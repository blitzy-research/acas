"""`pl100` - Purchase cash posting [purchase/pl100.cbl].

The whole program: it posts purchase payments to the Purchase ledger and the
open-item file, and maintains the supplier payment statistics.

The payment-days average is the Purchase variant of the cycle's average idiom
[purchase/pl100.cbl:L498], [purchase/pl100.cbl:L502]. It computes the same
accumulator-over-activity quotient as the Sales variants
[sales/sl100.cbl:L511], [sales/sl060.cbl:L827]; the guards around it differ, and
that difference is what is reproduced.

Also here: a sign flip [purchase/pl100.cbl:L387]; one of the cycle's nine
period-total writes [purchase/pl100.cbl:L396]; and one of the migration's four
`PERFORM ... THRU` sites [purchase/pl100.cbl:L336].

The run confirmation [purchase/pl100.cbl:L302-L311] gates every database write
the program makes, so it is a parameter of `run` rather than a prompt.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field as dc_field
from decimal import Decimal
from typing import Final, Mapping

from acas_posting import dates
from acas_posting.cobol import arithmetic, condition_names, picture
from acas_posting.cobol import move as movelib
from acas_posting.cobol.field import FieldDescriptor

from acas_posting.dal import facade

# copy "wsfnctn.cob".
from acas_posting.dal.status import FsReply
from acas_posting.records.calling_data import WsCallingData
from acas_posting.records.file_access import FileAccess
from acas_posting.records.file_defs import FileDefs
from acas_posting.records.gl_batch import GlBatchRecord
from acas_posting.records.gl_posting import WsPostingRecord
from acas_posting.records.maps03 import Maps03Ws
# copy "plwsoi5C.cob". [purchase/pl100.cbl:L213] - note the 5C variant; `pl060` copies
# 5B. The record the program addresses is `OI-Header`, the REDEFINES view, not the raw
# `WS-OTM5-Record` buffer.
from acas_posting.records.otm5 import (
    Filler1,
    OiBatch,
    OiCustomer,
    OiHeader,
    OiKey,
    OiSupplier,
    descriptors_of,
)
from acas_posting.records.purchase_ledger import WsPurchRecord
from acas_posting.records.spl_irs_posting import (
    WsIrsPostingRecord,
)
from acas_posting.records.system_record import SystemRecord
from acas_posting.records.system_record_4 import SystemRecord4
from acas_posting.records.test_data_flags import (
    AcasDalCommonData,
)
from acas_posting.records.value_analysis import WsValueRecord

__all__: Final[tuple[str, ...]] = ("run",)

_LOG: Final = logging.getLogger(__name__)

#: The frozen COBOL specification this module reproduces. Every locator in this file is
#: relative to it unless another path is named explicitly.
_SRC: Final[str] = "purchase/pl100.cbl"

_PROG_NAME: Final[str] = "PL100 (3.3.01)"

_PL002: Final[str] = "PL002 Note error and hit return"
_PL132: Final[str] = "PL132 Err on Batch file write : "
_PL137: Final[str] = "PL137 Payments Not Proofed"


# WORKING-STORAGE FIELD DESCRIPTORS [purchase/pl100.cbl:L125-L176] Program-local items
# have no data-dictionary entry, because they never reach a table.


def _local(clauses: str, *, name: str, line: int, level: str = "03") -> FieldDescriptor:
    """Describe one program-local working-storage item of `pl100`."""
    return picture.descriptor_for(
        clauses,
        name=name,
        source_locator=f"{_SRC}:L{line}",
        level=level,
    )


_D_EXCEPTION_MSG: Final = _local("pic x(25)", name="exception-msg", line=126, level="77")
_D_WS_REPLY: Final = _local("pic x", name="ws-reply", line=156)
_D_WX_REPLY: Final = _local("pic xxx", name="wx-reply", line=157)
_D_XX: Final = _local("pic 99", name="xx", line=158)
# 03  i              pic 99     value zero.   - declared, never referenced [L159]
_D_I: Final = _local("pic 99", name="i", line=159)
_D_J: Final = _local("pic 99", name="j", line=160)
# 03  k              pic 999    value zero.   - declared, never referenced [L161]
_D_K: Final = _local("pic 999", name="k", line=161)
_D_M: Final = _local("pic z(7)9", name="m", line=162)
_D_B: Final = _local("binary-char", name="b", line=163)
_D_C: Final = _local("binary-char", name="c", line=164)
_D_SAVE_LEVEL_1: Final = _local("pic 9", name="save-level-1", line=165)
_D_LINE_CNT: Final = _local("binary-char", name="line-cnt", line=166)
_D_N_DEDUCT: Final = _local("binary-long", name="n-deduct", line=167)
_D_T_PAID: Final = _local("pic s9(7)v99 comp-3", name="t-paid", line=168)
_D_T_APPROP: Final = _local("pic s9(7)v99 comp-3", name="t-approp", line=169)
_D_T_DEDUCT: Final = _local("pic s9(7)v99 comp-3", name="t-deduct", line=170)
_D_J_PAID: Final = _local("pic s9(7)v99 comp-3", name="j-paid", line=171)
_D_J_APPROP: Final = _local("pic s9(7)v99 comp-3", name="j-approp", line=172)
_D_J_DEDUCT: Final = _local("pic s9(7)v99 comp-3", name="j-deduct", line=173)
_D_WORK_1: Final = _local("pic s9(7)v99 comp-3", name="work-1", line=174)
_D_WORK_A: Final = _local("binary-long", name="work-a", line=175)
_D_WORK_B: Final = _local("binary-long", name="work-b", line=176)


_K = FieldDescriptor.from_dictionary_key

_D_PURCH_KEY: Final = _K("PULEDGER-REC.PURCH-KEY")
_D_PURCH_NAME: Final = _K("PULEDGER-REC.PURCH-NAME")
_D_PURCH_CURRENT: Final = _K("PULEDGER-REC.PURCH-CURRENT")
_D_PURCH_UNAPPLIED: Final = _K("PULEDGER-REC.PURCH-UNAPPLIED")
_D_PURCH_LAST_PAY: Final = _K("PULEDGER-REC.PURCH-LAST-PAY")
# The three payment-statistics fields are all `binary-long` - integers. That is
# precisely why the A-10 variant (d) divide at [L502] truncates.
_D_PURCH_PAY_ACTIVETY: Final = _K("PULEDGER-REC.PURCH-PAY-ACTIVETY")
_D_PURCH_PAY_AVERAGE: Final = _K("PULEDGER-REC.PURCH-PAY-AVERAGE")
_D_PURCH_PAY_WORST: Final = _K("PULEDGER-REC.PURCH-PAY-WORST")

# `OI-Header` is declared by BOTH `copybooks/plwsoi.cob` (purchase) and
# `copybooks/slwsoi.cob` (sales), so a bare dictionary lookup on the record name is
# ambiguous.
_OI_HEADER_D: Final = descriptors_of(OiHeader)
_OI_KEY_D: Final = descriptors_of(OiKey)
_OI_SUPPLIER_D: Final = descriptors_of(OiSupplier)
_OI_BATCH_D: Final = descriptors_of(OiBatch)
_OI_MONEY_D: Final = descriptors_of(Filler1)

_D_OI_NOS: Final = _OI_SUPPLIER_D["oi_nos"]
_D_OI_CHECK: Final = _OI_SUPPLIER_D["oi_check"]
_D_OI_INVOICE: Final = _OI_KEY_D["oi_invoice"]
_D_OI_DATE: Final = _OI_HEADER_D["oi_date"]
_D_OI_TYPE: Final = _OI_HEADER_D["oi_type"]
_D_OI_STATUS: Final = _OI_HEADER_D["oi_status"]
_D_OI_B_NOS: Final = _OI_BATCH_D["oi_b_nos"]
_D_OI_B_ITEM: Final = _OI_BATCH_D["oi_b_item"]
_D_OI_CR: Final = _OI_HEADER_D["oi_cr"]
_D_OI_DEDUCT_AMT: Final = _OI_HEADER_D["oi_deduct_amt"]
_D_OI_DATE_CLEARED: Final = _OI_HEADER_D["oi_date_cleared"]
_D_OI_APPROP: Final = _OI_MONEY_D["oi_approp"]
_D_OI_PAID: Final = _OI_MONEY_D["oi_paid"]

_D_VA_CODE: Final = _K("VALUEANAL-REC.VA-CODE")
_D_VA_SYSTEM: Final = _K("WS-Value-Record.va-system")
_D_VA_FIRST: Final = _K("WS-Value-Record.va-first")
_D_VA_SECOND: Final = _K("WS-Value-Record.va-second")
_D_VA_T_THIS: Final = _K("VALUEANAL-REC.VA-T-THIS")
_D_VA_T_YEAR: Final = _K("VALUEANAL-REC.VA-T-YEAR")
_D_VA_V_THIS: Final = _K("VALUEANAL-REC.VA-V-THIS")
_D_VA_V_YEAR: Final = _K("VALUEANAL-REC.VA-V-YEAR")

_D_WS_LEDGER: Final = _K("WS-Batch-Record.WS-Ledger")
_D_WS_BATCH_NOS: Final = _K("WS-Batch-Record.WS-Batch-Nos")
_D_ITEMS: Final = _K("GLBATCH-REC.ITEMS")
_D_BATCH_STATUS: Final = _K("GLBATCH-REC.BATCH-STATUS")
_D_CLEARED_STATUS: Final = _K("GLBATCH-REC.CLEARED-STATUS")
_D_BCYCLE: Final = _K("GLBATCH-REC.BCYCLE")
_D_ENTERED: Final = _K("GLBATCH-REC.ENTERED")
_D_INPUT_GROSS: Final = _K("GLBATCH-REC.INPUT-GROSS")
_D_INPUT_VAT: Final = _K("GLBATCH-REC.INPUT-VAT")
_D_ACTUAL_GROSS: Final = _K("GLBATCH-REC.ACTUAL-GROSS")
_D_ACTUAL_VAT: Final = _K("GLBATCH-REC.ACTUAL-VAT")
_D_DESCRIPTION: Final = _K("GLBATCH-REC.DESCRIPTION")
_D_BDEFAULT: Final = _K("GLBATCH-REC.BDEFAULT")
_D_CONVENTION: Final = _K("GLBATCH-REC.CONVENTION")
_D_BATCH_DEF_AC: Final = _K("GLBATCH-REC.BATCH-DEF-AC")
_D_BATCH_DEF_PC: Final = _K("GLBATCH-REC.BATCH-DEF-PC")
_D_BATCH_DEF_CODE: Final = _K("GLBATCH-REC.BATCH-DEF-CODE")
_D_BATCH_DEF_VAT: Final = _K("GLBATCH-REC.BATCH-DEF-VAT")
_D_BATCH_START: Final = _K("GLBATCH-REC.BATCH-START")

_D_WS_POST_RRN: Final = _K("GLPOSTING-REC.POST-RRN")
_D_POST_BATCH: Final = _K("WS-Posting-Record.Batch")
_D_POST_NUMBER: Final = _K("WS-Posting-Record.Post-Number")
_D_POST_CODE: Final = _K("GLPOSTING-REC.POST-CODE")
_D_POST_DATE: Final = _K("GLPOSTING-REC.POST-DAT")
_D_POST_DR: Final = _K("GLPOSTING-REC.POST-DR")
_D_DR_PC: Final = _K("GLPOSTING-REC.DR-PC")
_D_POST_CR: Final = _K("GLPOSTING-REC.POST-CR")
_D_CR_PC: Final = _K("GLPOSTING-REC.CR-PC")
_D_POST_AMOUNT: Final = _K("GLPOSTING-REC.POST-AMOUNT")
_D_POST_LEGEND: Final = _K("GLPOSTING-REC.POST-LEGEND")
_D_VAT_AC: Final = _K("GLPOSTING-REC.VAT-AC")
_D_VAT_PC: Final = _K("GLPOSTING-REC.VAT-PC")
_D_POST_VAT_SIDE: Final = _K("GLPOSTING-REC.POST-VAT-SIDE")
_D_VAT_AMOUNT: Final = _K("GLPOSTING-REC.VAT-AMOUNT")

# --- WS-IRS-Posting-Record  copy "wspost-irs.cob"  [purchase/pl100.cbl:L218] -
# The DR and CR account numbers NARROW from `9(6)` on the GL side to `9(5)`
# here, so the fan-out moves at [L634]/[L636] are truncating stores.  The two
# amount fields are `SIGN LEADING` display, not COMP-3.
_D_IRS_BATCH: Final = _K("WS-IRS-Posting-Record.WS-IRS-Batch")
_D_IRS_POST_NUMBER: Final = _K("WS-IRS-Posting-Record.WS-IRS-Post-Number")
_D_IRS_POST_CODE: Final = _K("PSIRSPOST-REC.IRS-POST-CODE")
_D_IRS_POST_DATE: Final = _K("PSIRSPOST-REC.IRS-POST-DAT")
_D_IRS_POST_DR: Final = _K("PSIRSPOST-REC.IRS-POST-DR")
_D_IRS_POST_CR: Final = _K("PSIRSPOST-REC.IRS-POST-CR")
_D_IRS_POST_AMOUNT: Final = _K("PSIRSPOST-REC.IRS-POST-AMOUNT")
_D_IRS_POST_LEGEND: Final = _K("PSIRSPOST-REC.IRS-POST-LEGEND")
_D_IRS_VAT_AC_DEF: Final = _K("PSIRSPOST-REC.IRS-VAT-AC-DEF")
_D_IRS_POST_VAT_SIDE: Final = _K("PSIRSPOST-REC.IRS-POST-VAT-SIDE")
_D_IRS_VAT_AMOUNT: Final = _K("PSIRSPOST-REC.IRS-VAT-AMOUNT")

_D_SCYCLE: Final = _K("System-Record.Scycle")
_D_RUN_DATE: Final = _K("SYSTEM-REC.RUN-DAT")
_D_POSTINGS: Final = _K("SYSTEM-REC.POSTINGS")
_D_BL_NEXT_BATCH: Final = _K("SYSTEM-REC.BL-NEXT-BATCH")
_D_BL_PAY_AC: Final = _K("SYSTEM-REC.BL-PAY-AC")
_D_P_CREDITORS: Final = _K("SYSTEM-REC.P-CREDITORS")
_D_P_FLAG_P: Final = _K("SYSTEM-REC.P-FLAG-P")
_D_OI_5_FLAG: Final = _K("SYSTEM-REC.OI-5-FLAG")

_D_PL_PAYMENTS: Final = _K("SYSTOT-REC.PL-PAYMENTS")

_D_RRN: Final = _K("File-Access.Rrn")
_D_FILE_KEY_NO: Final = _K("File-Access.File-Key-No")

# --- WS-Calling-Data  copy "wscall.cob"  [purchase/pl100.cbl:L258] --------
# `WS-Caller pic x(8)` [copybooks/wscall.cob:L8].  DECLARED AND DELIBERATELY
# UNUSED: `pl100` - unlike [purchase/pl060.cbl:L1022-L1025] - never tests it for
# the unattended `"xl150"` caller, and the entry log record that once rendered it
# was removed because a caller name is not inside the safe-event schema and its
# eager `move` made a diagnostic into a failure path.  The descriptor stays so the
# field keeps its dictionary citation, which is what rule R-5 asks of the group.
_D_WS_CALLER: Final = _K("WS-Calling-Data.WS-Caller")

_D_U_DATE: Final = _K("maps03-ws.u-date")
_D_U_BIN: Final = _K("maps03-ws.u-bin")


def _alpha_eq(value: str, literal: str, descriptor: FieldDescriptor) -> bool:
    """A COBOL alphanumeric relation condition, as a boolean.

    COBOL pads the shorter operand of an alphanumeric comparison with spaces to the
    length of the longer and then compares byte by byte, which is why ``if wx-reply =
    "NO"`` `[L308]` is true for the three-byte field content ``"NO "``.
    """
    return movelib.move(value, descriptor) == movelib.move(literal, descriptor)


def _initial(descriptor: FieldDescriptor) -> Decimal | int | str:
    """The figurative initial content of one elementary item.

    `ZERO` for a numeric item and `SPACE` for an alphanumeric one, produced by
    `cobol.move` so that neither the value nor its width is written by hand.
    """
    figurative = movelib.ZERO if descriptor.is_numeric else movelib.SPACE
    return movelib.move_figurative(figurative, descriptor)


def _fresh_oi_header() -> OiHeader:
    """A zero/space-filled ``OI-Header``, matching program start.

    ``01 OI-Header`` [copybooks/plwsoi.cob:L12] carries NO `VALUE` clause, and the
    buffer it redefines is ``01 WS-OTM5-Record pic x(113)``
    [copybooks/plwsoi5C.cob:L10], which GnuCOBOL space-fills.
    """
    money = Filler1(**{name: _initial(d) for name, d in _OI_MONEY_D.items()})
    supplier = OiSupplier(**{name: _initial(d) for name, d in _OI_SUPPLIER_D.items()})
    oi_key = OiKey(
        oi_customer=OiCustomer(oi_supplier=supplier),
        oi_invoice=_initial(_D_OI_INVOICE),
    )
    oi_batch = OiBatch(**{name: _initial(d) for name, d in _OI_BATCH_D.items()})
    _GROUPS: Final[frozenset[str]] = frozenset({"oi_key", "oi_batch", "filler_1"})
    elementary = {
        name: _initial(d) for name, d in _OI_HEADER_D.items() if name not in _GROUPS
    }
    return OiHeader(
        oi_key=oi_key, oi_batch=oi_batch, filler_1=money, **elementary
    )


@dataclass(slots=True)
class _Pl100State:
    """The whole of `pl100`'s addressable storage, in one mutable object.

    COBOL working storage is program-global: every paragraph of `pl100` reads and writes
    the same items, and control transfers between paragraphs carry no arguments.
    """

    ws_calling_data: WsCallingData
    system_record: SystemRecord
    system_record_4: SystemRecord4
    to_day: str
    file_defs: FileDefs

    ok_to_post: bool

    # ---- NOT A COBOL FIELD: the caller's keyword-only handler declarations --
    # Chiefly the transport-security policy, forwarded to every facade
    # `PERFORM` this program issues.  No COBOL counterpart: the frozen bridge's
    # connect passes six values and no transport policy at all
    # [copybooks/mysql-procedures.cpy:L72-L77] - transport is compiled into
    # `cobmysqlapi.c`.  An empty mapping is a STATEMENT, not an omission: every
    # handler declares `transport: TransportSecurity | None = None` and
    # `connection._require_permitted_connection` resolves `None` against the
    # INSTALLED PROCESS POLICY, which under the exact-parity default reports an
    # unencrypted non-local hop at WARNING and connects, as the compiled open does
    # (rule R-3).  Carried opaquely; `dal/facade.py` projects it onto whatever extras
    # each handler declares.
    dal_options: Mapping[str, object] = dc_field(default_factory=dict)

    # ---- records the facade reads into and writes from -------------------
    purch: WsPurchRecord = dc_field(default_factory=WsPurchRecord)
    otm5: OiHeader = dc_field(default_factory=_fresh_oi_header)
    batch: GlBatchRecord = dc_field(default_factory=GlBatchRecord)
    value: WsValueRecord = dc_field(default_factory=WsValueRecord)
    posting: WsPostingRecord = dc_field(default_factory=WsPostingRecord)
    irs_posting: WsIrsPostingRecord = dc_field(default_factory=WsIrsPostingRecord)

    file_access: FileAccess = dc_field(default_factory=FileAccess)
    dal_common: AcasDalCommonData = dc_field(default_factory=AcasDalCommonData)

    maps03_ws: Maps03Ws = dc_field(default_factory=Maps03Ws)
    date_formats: dates.WsDateFormats = dc_field(default_factory=dates.WsDateFormats)

    ws_reply: str = " "
    wx_reply: str = "   "
    xx: int = 0
    i: int = 0
    j: int = 0
    k: int = 0
    m: str = " " * 8
    b: int = 0
    c: int = 0
    save_level_1: int = 0
    line_cnt: int = 0
    n_deduct: int = 0
    t_paid: Decimal = Decimal("0.00")
    t_approp: Decimal = Decimal("0.00")
    t_deduct: Decimal = Decimal("0.00")
    j_paid: Decimal = Decimal("0.00")
    j_approp: Decimal = Decimal("0.00")
    j_deduct: Decimal = Decimal("0.00")
    work_1: Decimal = Decimal("0.00")
    work_a: int = 0
    work_b: int = 0
    exception_msg: str = " " * 25

    # The print file itself is omitted (see OMISSIONS), but `l5-name` is read back into
    # `post-legend`'s neighbour at [L434]/[L440] and `line-cnt`/`j` are load-bearing
    # because [L422] tests one and [L471] increments the other.
    l5_name: str = " " * 25

    # Facade contexts - one per entity, because `FacadeContext` binds the record it
    # operates on.
    def ctx(self, record: object) -> facade.FacadeContext:
        """Build the facade context for one entity's record.

        Mirrors the handler `CALL` argument list of `
        [copybooks/Proc-ACAS-FH-Calls.cob:L51-L57]` - ``call "acas0NN" using System-Record
        <entity-record> File- Access File-Defs ACAS-DAL-Common-Data`` - with the parameter order
        preserved. """
        return facade.FacadeContext(
            system=self.system_record,
            record=record,
            file_access=self.file_access,
            file_defs=self.file_defs,
            dal_common=self.dal_common,
            # Sixth operand, no COBOL counterpart and no accounting value: the
            # caller's keyword-only declarations, transport policy among them.
            # Attached to EVERY context so the policy does not depend on which
            # entity a verb happens to touch.
            options=self.dal_options,
        )

    # Named accessors for the linkage fields the program touches.
    @property
    def _sys(self) -> object:
        return self.system_record.system_data_block

    @property
    def _gl(self) -> object:
        return self.system_record.general_ledger_block

    @property
    def _pl(self) -> object:
        return self.system_record.purchase_ledger_block


def _is_g_l(state: _Pl100State) -> bool:
    """``88 G-L value 1.`` on ``07 Level-1 pic 9`` [copybooks/wssystem.cob:L85].

    `cobol.condition_names` publishes no `is_g_l` shorthand and `'G-L'` is absent from
    its `PREDICATES` mapping, so the registry is consulted by COBOL name. `'G-L'` is not
    in `DUPLICATED_COBOL_NAMES`, so the lookup is unambiguous.
    """
    return condition_names.evaluate("G-L", state._sys.level.level_1)


def _is_irs_used(state: _Pl100State) -> bool:
    """``88 IRS-Used value "Y".`` [copybooks/wssystem.cob:L180]."""
    return condition_names.is_irs_used(state._gl.irs_instead)


def _is_irs_both_used(state: _Pl100State) -> bool:
    """``88 IRS-Both-Used value "B".`` [copybooks/wssystem.cob:L181]."""
    return condition_names.is_irs_both_used(state._gl.irs_instead)


def _oi_supplier_image(state: _Pl100State) -> str:
    """The seven-byte image of ``03 OI-Supplier`` - a GROUP item.

    A COBOL group MOVE copies a byte image, and a group's image is the concatenation of
    its subordinates' images.
    """
    supplier = state.otm5.oi_key.oi_customer.oi_supplier
    image, _pointer = movelib.string_into(
        " " * (_D_OI_NOS.byte_length + _D_OI_CHECK.byte_length),
        [
            (supplier.oi_nos, movelib.Delimiter.SIZE, _D_OI_NOS),
            (supplier.oi_check, movelib.Delimiter.SIZE, _D_OI_CHECK),
        ],
        pointer=1,
        delimited_by=movelib.Delimiter.SIZE,
    )
    return image


# init01 SECTION [purchase/pl100.cbl:L272-L508] One very large section carrying TEN
# labels, three of which - `headings`, `compute-purch-pay` and `csp-exit` - are reached
# only by `PERFORM`.


def _init01(state: _Pl100State) -> None:
    """``init01 section.`` [purchase/pl100.cbl:L272-L294] - entry and the latch gate.

    The one-shot proof latch is the whole of the business content here.
    `P-Flag-P` is a `SYSTEM-REC` column, so the refusal survives across runs::

        289      if       p-flag-p not = 2
        290               display PL137   at 2301
        291               display PL002   at 2401
        292               accept ws-reply at 2433
        293               go to menu-exit
        294      end-if.

    and `[L465]` clears it back to zero at the end of a successful run, so a
    second immediate run is refused too.  `sl100` has the same latch on
    `S-Flag-P` [sales/sl100.cbl:L296-L301] and [sales/sl100.cbl:L474], but
    `pl100`'s DISPLAYS AND ACCEPTS BEFORE RETURNING where `sl100`'s does not.
    The latch and its clearing are reproduced.  `PL137` [L290] becomes a log
    record because it is the diagnostic; `PL002` [L291] and the acknowledgement
    `accept` [L292] are dropped together, the literal being nothing but the
    instruction to press that key; and the `go to menu-exit` control transfer at
    [L293] is preserved.
    """
    # [L273-L274] move prog-name to l1-name. move Print-Spool-Name to PSN. OMITTED -
    # both receivers are print-file layout items.

    _zz070_convert_date(state)

    if arithmetic.compare(state._pl.p_flag_p, 2) != 0:
        # [L290]  display PL137 at 2301.  A DIAGNOSTIC with no database effect
        # becomes a log record (plan section 0.3.4).  THE RECORD IS THE LITERAL
        # AND NOTHING ELSE:
        #  * [L291] `display PL002` and [L292] `accept ws-reply` are DROPPED
        #  together.  "PL002 Note error and hit return" is nothing but the
        #  instruction to press the key the `accept` reads, so there is no
        #  substantive half to keep and a headless run has no operator to
        #  instruct.
        #  * `P-Flag-P` ITSELF IS NOT LOGGED.  The frozen display shows the
        #  literal alone; the flag's value is a SYSTEM-REC host-variable
        #  value, which the safe-event schema in `acas_posting/dal/status.py`
        #  excludes from a record (CWE-532), and narrating it would also state
        #  more than the compiled program does.
        # The TRANSFER below is not dropped.
        _LOG.warning("%s: %s", _PROG_NAME, _PL137)
        # [L293]  go to menu-exit.        # GO TO class 3 -> menu-exit [L467]
        _init01__menu_exit(state)
        return
    _init01__menu_return(state)


def _init01__menu_return(state: _Pl100State) -> None:
    """``menu-return.`` [purchase/pl100.cbl:L296-L301] - the screen banner.

    Reached ONLY by fall-through from `[L294]`; nothing transfers to it. Every statement
    in it is a `DISPLAY` except the date conversion at `[L300]`, which recomputes `ws-
    date` from `to-day` and is therefore kept.
    """
    _LOG.info("%s: Purchase Cash Posting", _PROG_NAME)
    _zz070_convert_date(state)
    # [L301]  display ws-date at 0171.
    # NO LOG COUNTERPART.  `ws-date` is the posting date this run stamps into the
    # records it writes - a date with business meaning, which the safe-event
    # schema in `acas_posting/dal/status.py` excludes (CWE-532).  It is an INPUT
    # the caller supplied through `to-day`, already known wherever the run was
    # started and pinned by `clock.py`.  The conversion above still runs: it is a
    # redundant recomputation that is reproduced, and it can default `Date-Form`
    # in the system record, which IS a table effect.
    # FALL-THROUGH [L301] -> acpt-xrply. [L302]
    _init01__acpt_xrply(state)


def _init01__acpt_xrply(state: _Pl100State) -> None:
    """``acpt-xrply.`` [purchase/pl100.cbl:L302-L321] - the run confirmation and the opens.
    """
    while True:
        # [L303-L304]  display "OK to post payment transactions (YES/NO) ?".
        # NOT LOGGED.  It is the screen text for the `accept wx-reply` at [L306],
        # and plan section 0.3.4 resolves an `accept` that gates a database write
        # into "an explicit CLI parameter with the COBOL default preserved" -
        # which `ok_to_post` is.  The prompt is the dialogue around that
        # parameter, so emitting it as an operator diagnostic would log a question
        # no one can answer, and echoing the answer back would only restate a
        # command-line argument the caller already holds.
        # [L305]  move spaces to wx-reply.
        state.wx_reply = movelib.move_figurative(movelib.SPACE, _D_WX_REPLY)
        # [L306] accept wx-reply at 1256 with foreground-color 6 update. The accept
        # becomes the `ok_to_post` parameter.
        state.wx_reply = movelib.move("YES" if state.ok_to_post else "NO", _D_WX_REPLY)
        # [L307] move function upper-case (wx-reply) to wx-reply.
        state.wx_reply = movelib.move(state.wx_reply.upper(), _D_WX_REPLY)

        if _alpha_eq(state.wx_reply, "NO", _D_WX_REPLY):
            _init01__menu_exit(state)
            return
        if not _alpha_eq(state.wx_reply, "YES", _D_WX_REPLY):
            continue
        break

    facade.purch_open(state.ctx(state.purch))
    facade.otm5_open(state.ctx(state.otm5))

    if _is_g_l(state):
        _bl_open(state)
    # NOTE (FINDING F-PL100-17), and it is the outer frame A-PL100-A sits inside: `bl-open` runs
    # ONLY under `G-L`, and so do `bl-write` [L409-L410] and `bl-close` [L454-L455].

    state.j = movelib.move_figurative(movelib.ZERO, _D_J)
    _init01__headings(state)

    _init01__loop(state)


def _init01__loop(state: _Pl100State) -> None:
    """``loop.`` [purchase/pl100.cbl:L323-L347] - the OTM5 walk and its filter cascade.

    expands to a CONJUNCTION OF NEGATIONS - `oi-type not= 2` AND `oi-type not= 5` AND
    `oi-type not= 6` - and is written below in that shape, the shape COBOL evaluates,
    rather than as the logically equivalent negated disjunction. And.
    """
    while True:
        facade.otm5_read_next(state.ctx(state.otm5))
        if state.file_access.fs_reply == FsReply.END_OF_FILE:
            break

        # [L328] *> move open-item-record-5 to oi-header. Commented out in the frozen
        # source because `OI-Header` REDEFINES the same bytes.

        if (
            arithmetic.compare(state.otm5.oi_type, 2) != 0
            and arithmetic.compare(state.otm5.oi_type, 5) != 0
            and arithmetic.compare(state.otm5.oi_type, 6) != 0
        ):
            continue

        if (
            arithmetic.compare(state.otm5.oi_type, 2) == 0
            and arithmetic.compare(state.otm5.oi_batch.oi_b_nos, 0) != 0
            and arithmetic.compare(state.otm5.oi_batch.oi_b_item, 0) != 0
        ):
            # [L336] perform compute-purch-pay thru csp-exit. PERFORM ... THRU - one of
            # only FOUR in-scope sites in the whole migration ([general/gl072.cbl:L300],
            # [general/gl072.cbl:L304], [sales/sl100.cbl:L344] and this one).
            _init01__compute_purch_pay(state)
            _init01__csp_exit(state)
            (
                state.otm5.oi_batch.oi_b_nos,
                state.otm5.oi_batch.oi_b_item,
                state.otm5.oi_cr,
            ) = movelib.move_to_all(
                movelib.ZEROS, [_D_OI_B_NOS, _D_OI_B_ITEM, _D_OI_CR]
            )
            facade.otm5_rewrite(state.ctx(state.otm5))
            continue

        if (
            condition_names.is_s_closed_plwsoi(state.otm5.oi_status)
            or arithmetic.compare(state.otm5.oi_type, 2) == 0
        ):
            continue

        if (
            arithmetic.compare(0, state.otm5.oi_batch.oi_b_nos) == 0
            and arithmetic.compare(0, state.otm5.oi_batch.oi_b_item) == 0
        ):
            continue

        _init01__cust_update(state)
        # [L425] go to loop.
        continue

    # THE CLASS 2 TARGET. Plan section 0.6.3: the transformation is "`break` PLUS
    # faithful placement of that work after the loop, not `break` alone.
    _init01__main_end(state)


def _init01__cust_update(state: _Pl100State) -> None:
    """``cust-update.`` [purchase/pl100.cbl:L349-L425] - the purchase-ledger update."""
    (state.purch.ws_purch_key,) = movelib.move_to_all(
        _oi_supplier_image(state), [_D_PURCH_KEY]
    )

    state.ws_reply = movelib.move_figurative(movelib.SPACE, _D_WS_REPLY)
    facade.purch_read_indexed(state.ctx(state.purch))
    if state.file_access.fs_reply == FsReply.INVALID_KEY_ON_START:
        state.ws_reply = movelib.move("X", _D_WS_REPLY)

    # ANOMALY A-PL100-B [purchase/pl100.cbl:L356-L361] and [purchase/pl100.cbl:L405] - an
    # unknown supplier is NEVER CREATED.
    if _alpha_eq(state.ws_reply, "X", _D_WS_REPLY):
        state.l5_name = movelib.move("Supplier Unknown", _D_PURCH_NAME)
    else:
        state.l5_name = movelib.move(
            state.purch.purch_name, _D_PURCH_NAME, sending_field=_D_PURCH_NAME
        )


    state.maps03_ws.u_bin = movelib.move(
        state.otm5.oi_date, _D_U_BIN, sending_field=_D_OI_DATE
    )
    _zz060_convert_date(state)
    # [L369] move u-date to l5-date. OMITTED - print item. NOTE the source field:
    # `u-date`, where the sibling uses `ws-date` [purchase/pl060.cbl:L448].


    if arithmetic.compare(state.otm5.oi_deduct_amt, 0) != 0:
        state.n_deduct = arithmetic.add_to(
            1, receiver_value=state.n_deduct, receiving=_D_N_DEDUCT
        )

    # [L378] subtract purch-unapplied from purch-current giving l5-old-bal.

    state.purch.purch_current = arithmetic.subtract_from(
        state.otm5.filler_1.oi_approp,
        receiver_value=state.purch.purch_current,
        receiving=_D_PURCH_CURRENT,
    )
    state.purch.purch_current = arithmetic.subtract_from(
        state.otm5.oi_deduct_amt,
        receiver_value=state.purch.purch_current,
        receiving=_D_PURCH_CURRENT,
    )

    if arithmetic.compare(state.otm5.filler_1.oi_paid, state.otm5.filler_1.oi_approp) != 0:
        state.work_1 = arithmetic.subtract_giving(
            state.otm5.filler_1.oi_approp,
            minuend=state.otm5.filler_1.oi_paid,
            receiving=_D_WORK_1,
        )
        state.purch.purch_unapplied = arithmetic.add_to(
            state.work_1,
            receiver_value=state.purch.purch_unapplied,
            receiving=_D_PURCH_UNAPPLIED,
        )

    if arithmetic.compare(state.purch.purch_current, 0) < 0:
        state.work_1 = arithmetic.multiply_by_giving(-1, state.purch.purch_current, _D_WORK_1)
        state.purch.purch_unapplied = arithmetic.add_to(
            state.work_1,
            receiver_value=state.purch.purch_unapplied,
            receiving=_D_PURCH_UNAPPLIED,
        )
        state.purch.purch_current = movelib.move_figurative(
            movelib.ZERO, _D_PURCH_CURRENT
        )


    state.purch.purch_last_pay = movelib.move(
        state.otm5.oi_date, _D_PURCH_LAST_PAY, sending_field=_D_OI_DATE
    )

    if arithmetic.compare(state.otm5.oi_type, 5) == 0:
        state.t_approp = arithmetic.add_to(
            state.otm5.filler_1.oi_approp,
            receiver_value=state.t_approp,
            receiving=_D_T_APPROP,
        )
        # [L396] add oi-paid to t-paid pl-payments. PERIOD TOTAL 9 OF 9, and a TWO-
        # RECEIVER `ADD ... TO`. `t-paid` is a local print total.
        _oi_paid_at_l396 = state.otm5.filler_1.oi_paid
        state.t_paid = arithmetic.add_to(
            _oi_paid_at_l396, receiver_value=state.t_paid, receiving=_D_T_PAID
        )
        state.system_record_4.purchase_ledger_data.pl_payments = arithmetic.add_to(
            _oi_paid_at_l396,
            receiver_value=state.system_record_4.purchase_ledger_data.pl_payments,
            receiving=_D_PL_PAYMENTS,
        )
        state.t_deduct = arithmetic.add_to(
            state.otm5.oi_deduct_amt,
            receiver_value=state.t_deduct,
            receiving=_D_T_DEDUCT,
        )
    else:
        if arithmetic.compare(state.otm5.oi_type, 6) == 0:
            state.j_approp = arithmetic.add_to(
                state.otm5.filler_1.oi_approp,
                receiver_value=state.j_approp,
                receiving=_D_J_APPROP,
            )
            state.j_paid = arithmetic.add_to(
                state.otm5.filler_1.oi_paid,
                receiver_value=state.j_paid,
                receiving=_D_J_PAID,
            )
            state.j_deduct = arithmetic.add_to(
                state.otm5.oi_deduct_amt,
                receiver_value=state.j_deduct,
                receiving=_D_J_DEDUCT,
            )

    # [L404] move oi-approp to oi-paid. THE ORDERING TRAP.
    state.otm5.filler_1.oi_paid = movelib.move(
        state.otm5.filler_1.oi_approp, _D_OI_PAID, sending_field=_D_OI_APPROP
    )
    # [L405] perform Purch-Rewrite. *> rewrite purch-record. UNCONDITIONAL - see ANOMALY
    # A-PL100-B above.
    facade.purch_rewrite(state.ctx(state.purch))

    if _is_g_l(state):
        _bl_write(state)
    state.otm5.oi_status = movelib.move(1, _D_OI_STATUS)

    facade.otm5_rewrite(state.ctx(state.otm5))


    # [L421]  add 1 to line-cnt.  RETAINED because [L422] tests it.
    state.line_cnt = arithmetic.add_to(
        1, receiver_value=state.line_cnt, receiving=_D_LINE_CNT
    )
    if arithmetic.compare(state.line_cnt, state._sys.page_lines) > 0:
        _init01__headings(state)

    return


def _init01__main_end(state: _Pl100State) -> None:
    """``main-end.`` [purchase/pl100.cbl:L427-L465] - closes, the reversal, two SYSTEM-REC
    writes.
    """
    facade.otm5_close(state.ctx(state.otm5))
    facade.purch_close(state.ctx(state.purch))

    # [L433-L444]  the two total print blocks.  OMITTED AND NOT LOGGED.  Every
    # statement in both is a `move` into the print line followed by `write
    # print-record`; the frozen program DISPLAYS none of it.  Report formatting
    # beyond database effects is out of scope (plan section 0.2.2), and section
    # 0.3.4 converts a DISPLAY, not a report line.  The six operands are
    # MONETARY TOTALS besides, which the safe-event schema in
    # `acas_posting/dal/status.py` excludes from a record at any level (CWE-532).
    # The accumulators themselves are untouched: they are real, and the ones that
    # matter reach SYSTOT-REC, which is where the audit trail lives.
    # [L445]  close print-file.  OMITTED - the print file.
    # [L446]  call "SYSTEM" using Print-Report.  OMITTED - plan section 0.1.1
    # excludes "the `call "SYSTEM" using Print-Report` spool-out path" by name.
    # It is the only non-migratable call in the whole program (R-1).

    # [L448] add j-deduct to t-deduct. THE MERGE, and it is LOAD-BEARING.
    state.t_deduct = arithmetic.add_to(
        state.j_deduct, receiver_value=state.t_deduct, receiving=_D_T_DEDUCT
    )
    # [L449] if t-deduct not = zero ANOMALY A-PL100-C [purchase/pl100.cbl:L449] - the
    # ENTIRE value-analysis reversal is gated on `t-deduct` ALONE.
    if arithmetic.compare(state.t_deduct, 0) != 0:
        facade.value_open(state.ctx(state.value))
        _analise_deductions(state)
        facade.value_close(state.ctx(state.value))

    if _is_g_l(state):
        _bl_close(state)

    # [L460] *> move save-level-1 to level-1. The commented-out restore of the
    # commented-out GL bypass at [L282-L283]; neither is reproduced, because neither
    # executes.

    state.system_record.sales_ledger_block.oi_5_flag = movelib.move(
        "Y", _D_OI_5_FLAG
    )
    # [L465] move zero to P-Flag-P. A REAL `SYSTEM-REC` write - it clears the one-shot
    # latch that [L289] tests, so a second immediate run is refused.
    state.system_record.purchase_ledger_block.p_flag_p = movelib.move_figurative(
        movelib.ZERO, _D_P_FLAG_P
    )

    _init01__menu_exit(state)


def _init01__menu_exit(state: _Pl100State) -> None:
    """``menu-exit.`` [purchase/pl100.cbl:L467-L468].

    `exit program.` and NOT `goback.` - a FINDING, since `gl071` and others in the
    family end with `goback`.
    """
    # NO LOG RECORD.  `menu-exit.` [L467-L468] displays NOTHING - `exit program.`
    # is its only statement - so an "exit program" event would be output the
    # compiled program never produced, which R-4 forbids inventing, and
    # `WS-Term-Code` is a linkage field the caller reads directly.  `state` stays
    # in the signature so every paragraph function in this module has the same
    # shape (R-5) and the three transfer sites pass it as written.
    del state
    return


def _init01__headings(state: _Pl100State) -> None:
    """``headings.`` [purchase/pl100.cbl:L470-L486] - PERFORM-only, and still load-bearing.

    Every `WRITE` in it is omitted with the print file, but the paragraph MUST exist
    (R-5) and TWO of its statements must execute: `[L471]` advances the page counter and
    `[L486]` resets the line counter that `[L422]` tests.
    """
    state.j = arithmetic.add_to(1, receiver_value=state.j, receiving=_D_J)
    # [L472]  move j to l1-page.       OMITTED - print layout item.
    # [L473]  move usera to l2-user.   OMITTED - print layout item.
    # [L475-L485]  the six `write print-record` statements and the page/before
    # /after phrases.  OMITTED - the print file (see OMISSIONS) - AND NOT LOGGED:
    # a page number and a column ruler are report formatting, out of scope per
    # plan section 0.2.2, and this paragraph contains no `display` at all.  The
    # counter statements above and below stay, because [L422] tests the line
    # budget this paragraph resets.
    # [L486]  move 5 to line-cnt.
    state.line_cnt = movelib.move(5, _D_LINE_CNT)


def _init01__compute_purch_pay(state: _Pl100State) -> None:
    """``compute-purch-pay.`` [purchase/pl100.cbl:L488-L505] - A-10 VARIANT (d) OF FOUR.

    ANOMALY A-10 [purchase/pl100.cbl:L495], [purchase/pl100.cbl:L497],
    [purchase/pl100.cbl:L500-L502] - the fourth mutually inconsistent spelling of one
    moving-average idiom. `move zero to work-b` is UNCONDITIONAL and PRECEDES the guard,
    so there is no `ELSE`.
    """
    if arithmetic.compare(state.otm5.oi_date_cleared, 0) == 0:
        return

    state.work_a = arithmetic.subtract_giving(
        state.otm5.oi_date,
        minuend=state.otm5.oi_date_cleared,
        receiving=_D_WORK_A,
    )
    # ANOMALY A-10 [purchase/pl100.cbl:L495], [purchase/pl100.cbl:L497],
    # [purchase/pl100.cbl:L500-L502] - VARIANT (d) of four mutually inconsistent moving-
    # average idioms, differing from [purchase/pl060.cbl:L743-L751] (a) and
    # [purchase/pl060.cbl:L758-L766] (b) in FIVE ways and from
    # [sales/sl100.cbl:L497-L516] (c) in the guard.
    state.work_b = movelib.move_figurative(movelib.ZERO, _D_WORK_B)

    if arithmetic.compare(state.purch.purch_pay_activety, 0) != 0:
        state.work_b = arithmetic.multiply_by_giving(
            state.purch.purch_pay_activety,
            state.purch.purch_pay_average,
            _D_WORK_B,
        )

    state.work_b = arithmetic.add_to(
        state.work_a, receiver_value=state.work_b, receiving=_D_WORK_B
    )
    state.purch.purch_pay_activety = arithmetic.add_to(
        1,
        receiver_value=state.purch.purch_pay_activety,
        receiving=_D_PURCH_PAY_ACTIVETY,
    )
    # [L502] divide work-b by purch-pay-activety giving purch-pay-average. THE `BY`
    # FORM: average = work-b / activety.
    state.purch.purch_pay_average = arithmetic.divide_by_giving(
        state.work_b, state.purch.purch_pay_activety, _D_PURCH_PAY_AVERAGE
    )
    # AMBIGUITY Q-5: `Purch-Pay-Average` is declared SIGNED `binary-long`
    # [copybooks/wspl.cob:L41] while the bridge and the column narrow the statistics
    # family to unsigned (cf.

    if arithmetic.compare(state.work_a, state.purch.purch_pay_worst) > 0:
        state.purch.purch_pay_worst = movelib.move(
            state.work_a, _D_PURCH_PAY_WORST, sending_field=_D_WORK_A
        )


def _init01__csp_exit(state: _Pl100State) -> None:
    """``csp-exit.`` [purchase/pl100.cbl:L507-L508] - the second half of the THRU span.

    A PLAIN `EXIT`, not `exit section.` and not `exit program.` A bare `EXIT` is a
    documented NO-OP that exists only to give a paragraph a body, so this function has
    no statements - and it must still exist, both because R-5 requires a function per
    paragraph and because it is the second label of the `PERFORM compute-purch-pay THRU
    csp-exit` span at `[L336]`, which really does execute it.
    """
    return


def _analise_deductions(state: _Pl100State) -> None:
    """``analise-deductions section.`` [purchase/pl100.cbl:L510-L537] - the "Pzb" reversal.

    TWO DIFFERENT ACCUMULATORS, FOUR SUBTRACTS, TWICE OVER. `n-deduct` is a COUNT and
    reduces the `va-t-*` count fields; `t-deduct` is a VALUE and reduces the `va-v-*`
    value fields.
    """
    # [L513] move "Pzb" to va-code. A group MOVE distributes the literal across the
    # group's subordinates.
    _code = movelib.move_group("Pzb", _D_VA_CODE, length=3)
    state.value.va_code.va_system = movelib.move(
        movelib.ref_mod(_code, 1, 1), _D_VA_SYSTEM
    )
    state.value.va_code.va_group.va_first = movelib.move(
        movelib.ref_mod(_code, 2, 1), _D_VA_FIRST
    )
    state.value.va_code.va_group.va_second = movelib.move(
        movelib.ref_mod(_code, 3, 1), _D_VA_SECOND
    )

    # [L514] move 1 to File-Key-No.
    state.file_access.logging_data.file_key_no = movelib.move(1, _D_FILE_KEY_NO)
    facade.value_read_indexed(state.ctx(state.value))
    if state.file_access.fs_reply == FsReply.INVALID_KEY_ON_START:
        _analise_deductions__main_exit(state)
        return

    state.value.va_t_this = arithmetic.subtract_from(
        state.n_deduct, receiver_value=state.value.va_t_this, receiving=_D_VA_T_THIS
    )
    state.value.va_t_year = arithmetic.subtract_from(
        state.n_deduct, receiver_value=state.value.va_t_year, receiving=_D_VA_T_YEAR
    )
    state.value.va_v_this = arithmetic.subtract_from(
        state.t_deduct, receiver_value=state.value.va_v_this, receiving=_D_VA_V_THIS
    )
    state.value.va_v_year = arithmetic.subtract_from(
        state.t_deduct, receiver_value=state.value.va_v_year, receiving=_D_VA_V_YEAR
    )

    state.file_access.logging_data.file_key_no = movelib.move(1, _D_FILE_KEY_NO)
    facade.value_rewrite(state.ctx(state.value))

    state.value.va_code.va_group.va_second = movelib.move_figurative(
        movelib.SPACE, _D_VA_SECOND
    )
    state.file_access.logging_data.file_key_no = movelib.move(1, _D_FILE_KEY_NO)
    facade.value_read_indexed(state.ctx(state.value))
    if state.file_access.fs_reply == FsReply.INVALID_KEY_ON_START:
        _analise_deductions__main_exit(state)
        return

    state.value.va_t_this = arithmetic.subtract_from(
        state.n_deduct, receiver_value=state.value.va_t_this, receiving=_D_VA_T_THIS
    )
    state.value.va_t_year = arithmetic.subtract_from(
        state.n_deduct, receiver_value=state.value.va_t_year, receiving=_D_VA_T_YEAR
    )
    state.value.va_v_this = arithmetic.subtract_from(
        state.t_deduct, receiver_value=state.value.va_v_this, receiving=_D_VA_V_THIS
    )
    state.value.va_v_year = arithmetic.subtract_from(
        state.t_deduct, receiver_value=state.value.va_v_year, receiving=_D_VA_V_YEAR
    )
    # [L537] perform Value-Rewrite. *> rewrite value-record FINDING - THE ASYMMETRY:
    # there is NO `move 1 to File-Key-No` before this second rewrite, where [L524]
    # precedes the first.
    facade.value_rewrite(state.ctx(state.value))

    _analise_deductions__main_exit(state)


def _analise_deductions__main_exit(state: _Pl100State) -> None:
    """``main-exit. exit section.`` [purchase/pl100.cbl:L539].

    The FIRST of FIVE paragraphs in this program named `main-exit` - the others are at
    L574, L657, L679 and L687. Paragraph names are not globally unique in this codebase,
    which is why every function name here is section-qualified.
    """
    return


_BATCH_NOS_SCALE: Final[int] = 10**5


def _restate_ws_batch_key9(batch: GlBatchRecord) -> None:
    """Keep ``WS-Batch-Key9`` in step with the two members it redefines.

    ONE STORAGE, TWO READINGS. ``03 WS-Batch-Key.`` holds ``05 WS-Ledger pic 9.`` and
    ``05 WS-Batch-Nos pic 9(5).``, and ``03 WS-Batch-Key9 redefines WS-Batch-Key pic
    9(6).`` [copybooks/wsbatch.cob:L14-L21] is those SAME six bytes read as one number.

    Args:
        batch: ``01 WS-Batch-Record.`` [copybooks/wsbatch.cob:L13], mutated in place so
            both readings of its key agree.
    """
    batch.ws_batch_key9.ws_batch_key9 = (
        int(batch.ws_batch_key.ws_ledger) * _BATCH_NOS_SCALE
        + int(batch.ws_batch_key.ws_batch_nos)
    )


def _bl_open(state: _Pl100State) -> None:
    """``bl-open section.`` [purchase/pl100.cbl:L541-L572] - batch allocation, AND A-PL100-A.

    Allocates the next purchase batch number, stamps the batch header from the
    controlled run date, seeds the posting relative-record number - and then opens the
    posting files through the mutually exclusive `IF ...
    """
    facade.gl_batch_open(state.ctx(state.batch))

    state.batch.ws_batch_key.ws_batch_nos = movelib.move(
        state._pl.bl_next_batch, _D_WS_BATCH_NOS, sending_field=_D_BL_NEXT_BATCH
    )
    state.batch.ws_batch_key.ws_ledger = movelib.move(2, _D_WS_LEDGER)
    _restate_ws_batch_key9(state.batch)
    state.system_record.purchase_ledger_block.bl_next_batch = arithmetic.add_to(
        1, receiver_value=state._pl.bl_next_batch, receiving=_D_BL_NEXT_BATCH
    )
    (state.batch.batch_status, state.batch.cleared_status) = movelib.move_to_all(
        movelib.ZERO, [_D_BATCH_STATUS, _D_CLEARED_STATUS]
    )
    state.batch.bcycle = movelib.move(
        state._sys.scycle, _D_BCYCLE, sending_field=_D_SCYCLE
    )
    # [L551] move run-date to entered. THE CONTROLLED-CLOCK OBSERVABLE. `Run-Date
    # binary-long` [copybooks/wssystem.cob:L67] arrives on the linkage system record,
    # pinned by the CLI.
    state.batch.dates.entered = movelib.move(
        state._sys.run_date, _D_ENTERED, sending_field=_D_RUN_DATE
    )

    state.batch.description = movelib.move("Purchase Ledger Payments", _D_DESCRIPTION)
    (
        state.batch.posting_data.b_default,
        state.batch.posting_data.batch_def_ac,
        state.batch.posting_data.batch_def_pc,
        state.batch.items,
        state.batch.amounts.input_gross,
        state.batch.amounts.input_vat,
        state.batch.amounts.actual_gross,
        state.batch.amounts.actual_vat,
    ) = movelib.move_to_all(
        movelib.ZERO,
        [
            _D_BDEFAULT,
            _D_BATCH_DEF_AC,
            _D_BATCH_DEF_PC,
            _D_ITEMS,
            _D_INPUT_GROSS,
            _D_INPUT_VAT,
            _D_ACTUAL_GROSS,
            _D_ACTUAL_VAT,
        ],
    )

    state.batch.posting_data.convention = movelib.move("DR", _D_CONVENTION)
    state.batch.posting_data.batch_def_code = movelib.move("PL", _D_BATCH_DEF_CODE)
    state.batch.posting_data.batch_def_vat = movelib.move("I", _D_BATCH_DEF_VAT)
    # [L564] add postings 1 giving batch-start. THE A-17 CONSUMER.
    state.batch.batch_start = arithmetic.add_giving(
        state._gl.postings, 1, receiving=_D_BATCH_START
    )

    # ANOMALY A-PL100-A [purchase/pl100.cbl:L566-L570] - a mutually exclusive IF/ELSE
    # where every sibling program uses two independent IFs, and `if irs-used` omits IRS-
    # Both-Used.
    if _is_irs_used(state):
        facade.spl_posting_open_extend(state.ctx(state.irs_posting))
    else:
        facade.gl_posting_open(state.ctx(state.posting))

    state.file_access.rrn = movelib.move(
        state.batch.batch_start, _D_RRN, sending_field=_D_BATCH_START
    )

    _bl_open__main_exit(state)


def _bl_open__main_exit(state: _Pl100State) -> None:
    """``main-exit. exit section.`` [purchase/pl100.cbl:L574] - the SECOND of five."""
    return


def _bl_write(state: _Pl100State) -> None:
    """``bl-write section.`` [purchase/pl100.cbl:L577-L655] - the GL/IRS posting write.

    A PAYMENT POSTING CARRIES NO VAT, and the absence is reproduced rather than filled
    in.
    """
    # [L591-L592] move u-date (1:6) to post-date (1:6). *> using UK format move u-date
    # (9:2) to post-date (7:2).
    _post_date = movelib.move(state.posting.post_date, _D_POST_DATE)
    _post_date = movelib.ref_mod_into(
        _post_date, 1, 6, movelib.ref_mod(state.maps03_ws.u_date, 1, 6)
    )
    _post_date = movelib.ref_mod_into(
        _post_date, 7, 2, movelib.ref_mod(state.maps03_ws.u_date, 9, 2)
    )
    state.posting.post_date = _post_date

    state.batch.items = arithmetic.add_to(
        1, receiver_value=state.batch.items, receiving=_D_ITEMS
    )
    state.posting.ws_post_key.post_number = movelib.move(
        state.batch.items, _D_POST_NUMBER, sending_field=_D_ITEMS
    )
    state.posting.post_amount = movelib.move(
        state.otm5.filler_1.oi_paid, _D_POST_AMOUNT, sending_field=_D_OI_PAID
    )

    state.posting.ws_post_key.batch = movelib.move(
        state.batch.ws_batch_key.ws_batch_nos, _D_POST_BATCH,
        sending_field=_D_WS_BATCH_NOS,
    )

    # [L597-L610] the post-legend, built from folio/invoice number plus ".
    state.m = movelib.move_to_edited(state.otm5.oi_key.oi_invoice, _D_M)
    state.b = movelib.move(movelib.ZERO, _D_B)
    state.b = movelib.inspect_tallying_leading(state.m, movelib.SPACE, state.b)
    state.c = arithmetic.subtract_giving(state.b, minuend=8, receiving=_D_C)
    state.b = arithmetic.add_to(1, receiver_value=state.b, receiving=_D_B)
    state.xx = movelib.move(1, _D_XX)
    _legend, _pointer = movelib.string_into(
        movelib.move(state.posting.post_legend, _D_POST_LEGEND),
        [
            movelib.ref_mod(state.m, int(state.b), int(state.c)),
            " : ",
            movelib.move(state.purch.purch_name, _D_PURCH_NAME),
        ],
        pointer=int(state.xx),
        delimited_by=movelib.Delimiter.SIZE,
    )
    state.posting.post_legend = _legend
    # `STRING ... POINTER` updates the pointer in place.
    state.xx = movelib.move(_pointer, _D_XX)

    # [L612-L613] THE DR/CR SIDES ARE SWAPPED RELATIVE TO `pl060`. pl100 : p-creditors
    # -> post-dr bl-pay-ac -> post-cr pl060.
    state.posting.post_dr = movelib.move(
        state._pl.p_creditors, _D_POST_DR, sending_field=_D_P_CREDITORS
    )
    state.posting.post_cr = movelib.move(
        state._pl.bl_pay_ac, _D_POST_CR, sending_field=_D_BL_PAY_AC
    )

    # ANOMALY A-18 [purchase/pl100.cbl:L615-L616], [purchase/pl100.cbl:L640-L641] - `dr-
    # pc` and `cr-pc` are zeroed here and are never carried into the IRS posting record,
    # the maintainer flagging the concern himself in adjacent comments.
    (
        state.posting.dr_pc,
        state.posting.cr_pc,
        state.posting.vat_ac,
        state.posting.vat_pc,
        state.posting.vat_amount,
    ) = movelib.move_to_all(
        movelib.ZERO, [_D_DR_PC, _D_CR_PC, _D_VAT_AC, _D_VAT_PC, _D_VAT_AMOUNT]
    )

    # [L621] move spaces to post-vat-side. FINDING - AN INERT STORE: [L627] overwrites
    # it with "DR" before any write occurs, so this store is dead.
    state.posting.post_vat_side = movelib.move_figurative(
        movelib.SPACES, _D_POST_VAT_SIDE
    )

    state.batch.amounts.input_gross = arithmetic.add_to(
        state.posting.post_amount,
        receiver_value=state.batch.amounts.input_gross,
        receiving=_D_INPUT_GROSS,
    )
    state.batch.amounts.actual_gross = arithmetic.add_to(
        state.posting.post_amount,
        receiver_value=state.batch.amounts.actual_gross,
        receiving=_D_ACTUAL_GROSS,
    )

    state.posting.post_code = movelib.move("PL", _D_POST_CODE)
    state.posting.post_vat_side = movelib.move("DR", _D_POST_VAT_SIDE)

    # [L629-L645] the IRS fan-out write. Predicate `irs-used or IRS-Both-Used` -
    # INCONSISTENT with [L566], which tests `irs-used` ALONE, which is defect (a) of
    # A-PL100-A.
    if _is_irs_used(state) or _is_irs_both_used(state):
        _key_image, _ = movelib.string_into(
            " " * (_D_POST_BATCH.byte_length + _D_POST_NUMBER.byte_length),
            [
                (state.posting.ws_post_key.batch, movelib.Delimiter.SIZE, _D_POST_BATCH),
                (
                    state.posting.ws_post_key.post_number,
                    movelib.Delimiter.SIZE,
                    _D_POST_NUMBER,
                ),
            ],
            pointer=1,
            delimited_by=movelib.Delimiter.SIZE,
        )
        state.irs_posting.ws_irs_post_key.ws_irs_batch = movelib.move(
            movelib.ref_mod(_key_image, 1, _D_IRS_BATCH.byte_length), _D_IRS_BATCH
        )
        state.irs_posting.ws_irs_post_key.ws_irs_post_number = movelib.move(
            movelib.ref_mod(
                _key_image,
                _D_IRS_BATCH.byte_length + 1,
                _D_IRS_POST_NUMBER.byte_length,
            ),
            _D_IRS_POST_NUMBER,
        )
        state.irs_posting.ws_irs_post_code = movelib.move(
            state.posting.post_code, _D_IRS_POST_CODE, sending_field=_D_POST_CODE
        )
        state.irs_posting.ws_irs_post_date = movelib.move(
            state.posting.post_date, _D_IRS_POST_DATE, sending_field=_D_POST_DATE
        )
        # [L634] move Post-DR to WS-IRS-Post-DR.
        state.irs_posting.ws_irs_post_dr = movelib.move(
            state.posting.post_dr, _D_IRS_POST_DR, sending_field=_D_POST_DR
        )
        state.irs_posting.ws_irs_post_cr = movelib.move(
            state.posting.post_cr, _D_IRS_POST_CR, sending_field=_D_POST_CR
        )
        state.irs_posting.ws_irs_post_amount = movelib.move(
            state.posting.post_amount,
            _D_IRS_POST_AMOUNT,
            sending_field=_D_POST_AMOUNT,
        )
        state.irs_posting.ws_irs_post_legend = movelib.move(
            state.posting.post_legend,
            _D_IRS_POST_LEGEND,
            sending_field=_D_POST_LEGEND,
        )
        (
            state.irs_posting.ws_irs_vat_ac_def,
            state.posting.vat_pc,
        ) = movelib.move_to_all(31, [_D_IRS_VAT_AC_DEF, _D_VAT_PC])
        state.irs_posting.ws_irs_post_vat_side = movelib.move(
            state.posting.post_vat_side,
            _D_IRS_POST_VAT_SIDE,
            sending_field=_D_POST_VAT_SIDE,
        )
        state.irs_posting.ws_irs_vat_amount = movelib.move(
            state.posting.vat_amount,
            _D_IRS_VAT_AMOUNT,
            sending_field=_D_VAT_AMOUNT,
        )
        # [L644] perform SPL-Posting-Write. *> write irs-posting-record In "B" mode the
        # table was never opened - A-PL100-A defect (a), AMBIGUITY Q-1.
        facade.spl_posting_write(state.ctx(state.irs_posting))

    # [L646-L647] if IRS-Both-Used or G-L *> (As set in params) Predicate INCONSISTENT
    # with [L566]'s `else` branch, which reaches `GL-Posting-Open` only when `irs-used`
    # is FALSE - so in "Y" mode with `G-L` also set this writes to a table that was
    # never opened.
    if _is_irs_both_used(state) or _is_g_l(state):
        state.posting.ws_post_rrn = movelib.move(
            state.file_access.rrn, _D_WS_POST_RRN, sending_field=_D_RRN
        )
        facade.gl_posting_write(state.ctx(state.posting))
        state.file_access.rrn = arithmetic.add_to(
            1, receiver_value=state.file_access.rrn, receiving=_D_RRN
        )

    if arithmetic.compare(state.batch.items, 99) == 0:
        _bl_close(state)
        _bl_open(state)

    _bl_write__main_exit(state)


def _bl_write__main_exit(state: _Pl100State) -> None:
    """``main-exit. exit section.`` [purchase/pl100.cbl:L657] - the THIRD of five."""
    return


def _bl_close(state: _Pl100State) -> None:
    """``bl-close section.`` [purchase/pl100.cbl:L660-L677] - A-17 and the A-1 CONTROL
    CASE.

    Writes the batch header, then closes the batch file and BOTH posting files - under
    the `pl060`-style predicates, so it can close a file that `bl-open`'s mutually
    exclusive `IF ... ELSE` never opened.
    """
    facade.gl_batch_write(state.ctx(state.batch))
    # [L664-L670] if fs-reply not = zero -> DIAGNOSTICS WITH NO CONTROL TRANSFER. Every
    # close below still runs; nothing is retried and nothing is rolled back.
    if state.file_access.fs_reply != FsReply.SUCCESS:
        _eval_status(state)
        _LOG.error(
            "%s [%s:L665-L668] %s fs-reply=%s we-error=%s %s",
            _PROG_NAME,
            _SRC,
            _PL132,
            state.file_access.fs_reply,
            state.file_access.we_error,
            state.exception_msg,
        )

    # ANOMALY A-17 [purchase/pl100.cbl:L672] - `move RRN to postings.` carries the
    # maintainer's own "*> Why ?". Plan section 0.6.8.
    if _is_irs_both_used(state) or _is_g_l(state):
        # [L672]  move RRN to postings.    *> Why ?
        state.system_record.general_ledger_block.postings = movelib.move(
            state.file_access.rrn, _D_POSTINGS, sending_field=_D_RRN
        )

    facade.gl_batch_close(state.ctx(state.batch))

    # ANOMALY A-1, CONTROL CASE [purchase/pl100.cbl:L675] - THE PERIOD IS PRESENT, AND
    # IT MUST STAY PRESENT.
    if _is_irs_used(state) or _is_irs_both_used(state):
        # [L675] perform SPL-Posting-Close. *> close irs-post-file May close a file `bl-
        # open` never opened - see A-PL100-A.
        facade.spl_posting_close(state.ctx(state.irs_posting))
    if _is_irs_both_used(state) or _is_g_l(state):
        # [L677] perform GL-Posting-Close. *> close posting-file Likewise may close a
        # file `bl-open` never opened - see A-PL100-A.
        facade.gl_posting_close(state.ctx(state.posting))

    _bl_close__main_exit(state)


def _bl_close__main_exit(state: _Pl100State) -> None:
    """``main-exit. exit section.`` [purchase/pl100.cbl:L679] - the FOURTH of five."""
    return


def _eval_status(state: _Pl100State) -> None:
    """``Eval-Status section.`` [purchase/pl100.cbl:L681-L685] - the file-status message.

    DIAGNOSTIC ONLY - it renders a message and MUST NOT alter control flow. Its only
    caller is [L666], inside `bl-close`'s batch-write failure path, which itself
    performs no control transfer.
    """
    try:
        _text = FsReply(int(state.file_access.fs_reply)).name.replace("_", " ")
    except ValueError:
        _text = f"UNMAPPED FILE STATUS {int(state.file_access.fs_reply):02d}"
    state.exception_msg = movelib.move(_text, _D_EXCEPTION_MSG)

    _eval_status__main_exit(state)


def _eval_status__main_exit(state: _Pl100State) -> None:
    """``main-exit. exit section.`` [purchase/pl100.cbl:L687] - the FIFTH and last.

    Note the name: this section's exit is `main-exit`, NOT the `Eval-Msg-Exit` that
    [purchase/pl060.cbl] section 1043 uses. Preserved as written.
    """
    return


# zz050-Validate-Date SECTION [purchase/pl100.cbl:L689-L722] FINDING - DEAD CODE THAT
# MUST STILL EXIST. `grep -c "perform *zz050"` over purchase/pl100.cbl returns ZERO.


def _zz050_validate_date(state: _Pl100State) -> None:
    """``zz050-Validate-Date section.`` [purchase/pl100.cbl:L689-L714].

    The consolidated implementation reproduces, in order: `move ws-test-date to ws-date`
    [L698]; the `if Date-Form = zero move 1 to Date-Form` default [L699-L700]; the UK
    short-circuit [L701-L702]; the USA day/month swap through `ws-swap` [L703-L707].
    """
    # THE TWO TRANSFER SITES INSIDE THIS SECTION, each classified by shape.
    state.system_record.system_data_block.date_form = dates.zz050_validate_date(
        state.date_formats,
        state.maps03_ws,
        int(state._sys.date_form),
        wrapper=_maps04_wrapper(state),
    )
    _zz050_exit(state)


def _zz050_test_date(state: _Pl100State) -> None:
    """``zz050-test-date.`` [purchase/pl100.cbl:L716-L719] - the shared validation tail.
    """
    dates.zz050_test_date(
        state.date_formats, state.maps03_ws, wrapper=_maps04_wrapper(state)
    )
    _zz050_exit(state)


def _zz050_exit(state: _Pl100State) -> None:
    """``zz050-exit. exit section.`` [purchase/pl100.cbl:L721-L722]."""
    return


def _zz060_convert_date(state: _Pl100State) -> None:
    """``zz060-Convert-Date section.`` [purchase/pl100.cbl:L724-L754] - binary -> text.

    Reproduces in order: `perform maps04` [L733]; the space guard `if u-date = spaces
    move spaces to ws-Date go to zz060-Exit` [L734-L736]; `move u-date to ws-date`
    [L737]; the `Date-Form` default [L739-L740]; the UK short-circuit [L741-L742]; the
    USA swap [L743-L747].
    """
    # THE THREE TRANSFER SITES INSIDE THIS SECTION.
    state.system_record.system_data_block.date_form = dates.zz060_convert_date(
        state.date_formats,
        state.maps03_ws,
        int(state._sys.date_form),
        wrapper=_maps04_wrapper(state),
    )
    _zz060_exit(state)


def _zz060_exit(state: _Pl100State) -> None:
    """``zz060-Exit. exit section.`` [purchase/pl100.cbl:L756-L757]."""
    return


def _zz070_convert_date(state: _Pl100State) -> None:
    """``zz070-Convert-Date section.`` [purchase/pl100.cbl:L759-L784] - the run date.

    `zz070` is BYTE-IDENTICAL in all ten carrying programs, so the consolidated
    implementation is called directly. It reproduces `move to-day to ws-date` [L767];
    the `Date-Form` default [L769-L770]; the UK short-circuit [L771-L772]; the USA swap
    [L773-L777].
    """
    # THE TWO TRANSFER SITES INSIDE THIS SECTION. Both target the section's own trailing
    # exit label, so both are Class 3.
    state.system_record.system_data_block.date_form = dates.zz070_convert_date(
        state.date_formats, state.to_day, int(state._sys.date_form)
    )
    _zz070_exit(state)


def _zz070_exit(state: _Pl100State) -> None:
    """``zz070-Exit. exit section.`` [purchase/pl100.cbl:L786-L787]."""
    return


def _maps04(state: _Pl100State) -> None:
    """``maps04 section.`` [purchase/pl100.cbl:L789-L792] - the date-module wrapper.

    R-1 forbids COBOL at runtime, so the called program is reimplemented in
    `acas_posting.dates` rather than invoked.
    """
    dates.maps04(state.maps03_ws)
    _maps04_exit(state)


def _maps04_exit(state: _Pl100State) -> None:
    """``maps04-exit. exit section.`` [purchase/pl100.cbl:L794-L795]."""
    return


def _maps04_wrapper(state: _Pl100State) -> Callable[[Maps03Ws], None]:
    """Bind this program's own `maps04` section as the wrapper the date helpers perform.

    The consolidated `zz050`/`zz060` implementations take the wrapper as a parameter
    precisely because the carrying programs differ in which one they perform.
    """

    def _perform(ws: Maps03Ws) -> None:
        if ws is not state.maps03_ws:  # pragma: no cover - contract guard
            raise AssertionError(
                "maps04 wrapper invoked with a foreign maps03-ws instance"
            )
        _maps04(state)

    return _perform


def run(
    ws_calling_data: WsCallingData,
    system_record: SystemRecord,
    system_record_4: SystemRecord4,
    to_day: str,
    file_defs: FileDefs,
    *,
    ok_to_post: bool,
    dal_options: Mapping[str, object] | None = None,
) -> None:
    """Run `pl100` - Purchase Ledger Cash/Payment Posting.

    Both linkage records are MUTATED IN PLACE, and that is the whole point.

    Args:
        ws_calling_data: `WS-Calling-Data` [copybooks/wscall.cob:L7-L14].
        system_record: `System-Record` [copybooks/wssystem.cob]. Supplies the pinned
            `Run-Date` [copybooks/wssystem.cob:L67], the `P-Flag-P` one-shot latch, the
            IRS three-state switch and the GL/PL control accounts; receives the four
            writes listed above.
        system_record_4: `System-Record-4` [copybooks/wssys4.cob]. Receives period total
            9 of 9, `PL-Payments`, at [L396].
        to_day: `to-day pic x(10)` [purchase/pl100.cbl:L263] - the pinned run date in
            the presentation the `Date-Form` selects. The first of the two controlled-
            clock observables.
        file_defs: `File-Defs` [copybooks/wsnames.cob].
        dal_options: keyword-only, and NOT one of the five linkage operands. Forwarded
            to every facade `PERFORM` this program issues, carrying the caller's
            transport-security declaration. The frozen program has no counterpart
            because its bridge has none. `None` - the default - declares nothing,
            which every handler resolves FAIL-CLOSED. It changes no status, no
            statement, no arithmetic and no write order.
        ok_to_post: The `[L302-L311]` run-confirm, "OK to post payment
            transactions (YES/NO) ?".  Plan section 0.3.4 requires that
            "accept prompts that gate a database write become explicit CLI
            parameters with the COBOL default preserved", and this one gates
            EVERY write the program makes: answering NO transfers to
            `menu-exit` [L309] having opened nothing and written nothing at
            all.  `True` corresponds to the COBOL's `"YES"`, the only reply
            that proceeds.  REQUIRED, WITH NO DEFAULT: there is no COBOL
            default for section 0.3.4 to preserve, because `wx-reply` is
            `pic xxx value spaces` [L157], [L305] moves spaces into it again
            immediately before the accept so that [L306]'s `update` pre-fills
            blanks, and [L310-L311] re-asks on a blank.  A keyword default
            would invent an answer the frozen program has not got, and the
            affirmative one writes to the database.  The COBOL upper-cases the reply
            (`function upper-case`, [L307]) and re-asks on anything other than
            `"YES"` or `"NO"` [L310-L311]; with a boolean the re-ask collapses,
            which is a consequence of removing the presentation layer and NOT
            a behaviour change - see the Class 4 proof on
            `_init01__acpt_xrply`.

            REQUIRED, WITH NO DEFAULT (CWE-636).  `"YES"` is indeed the only
            reply that proceeds, but that does not yield a default of `True`:
            a default is what the program does when the operator supplies
            NOTHING, and this program then does neither.
            `wx-reply` is `pic xxx value spaces` [purchase/pl100.cbl:L157] and
            [L305] re-fills it with spaces immediately before the accept, so
            pressing return leaves it blank, [L310-L311] fires and control
            returns to `acpt-xrply.` [L302] - for ever.  [L313] is
            UNREACHABLE on a blank answer, so inferring `"YES"` from silence
            authorised every `OTM5-Rewrite`, every `Purch-Rewrite`, the GL
            batch family and the `PL-Payments` period total on an answer the
            compiled program never accepts.  Requiring the keyword removes the
            inference rather than replacing it with the opposite one: the
            caller must state the answer, as the operator must type it.  The
            same change is made to the Sales twin `sl100`, whose paragraph is
            character-for-character the same decision.

    Returns:
        None. `pl100` is a COBOL sub-program; it communicates only through the mutated
            linkage records and the database.
    """
    state = _Pl100State(
        ws_calling_data=ws_calling_data,
        system_record=system_record,
        system_record_4=system_record_4,
        to_day=to_day,
        file_defs=file_defs,
        ok_to_post=ok_to_post,
        # `None` and `{}` are the same thing - no declaration - and both leave
        # every handler under the installed process policy.
        dal_options=dict(dal_options) if dal_options else {},
    )
    # NO ENTRY OR EXIT RECORD.  `pl100` is a `CALL`ed sub-program: the COBOL
    # displays nothing on entry and nothing at [L467-L468] on the way out, so
    # both events would be output the compiled program never produced (R-4).
    # Each also carried data the safe-event schema in `acas_posting/dal/status.py`
    # excludes (CWE-532) - the caller name and the run date on the way in, the
    # batch item count and two accumulated deduction amounts on the way out.
    #
    # AND THE ENTRY RECORD WAS A FAILURE PATH THAT LOGGING MUST NOT ADD.  Its
    # `movelib.move(...)` argument was evaluated BEFORE the logging module
    # decided whether the record was wanted, so a value the receiving picture
    # could not hold would have raised from inside a disabled diagnostic.
    # Removing the operand removes the risk outright, which no `isEnabledFor`
    # guard can do.
    #
    # `init01 section.` [L272] is the program's first executable section, so
    # control enters there and reaches every other section by PERFORM or by
    # fall-through.
    _init01(state)


# ==========================================================================
# --- traceability ---
# ==========================================================================
# Required by R-5 (plan section 0.7.2): every program maps to a module, every
# paragraph to a function, every field to a data-dictionary entry.  Plan
# section 0.7.4 C-4 additionally requires that "every paragraph retains a
# named function even where its `GO TO` becomes a `continue`, a `break` or a
# `return`", and that deliberate omissions be "recorded as omissions ... so
# that a reader comparing the two files does not conclude something was lost".
#
# PROGRAM -> MODULE, LABEL -> FUNCTION, FALL-THROUGHS
# ===================================================
# Both tables live in docs/migration/traceability.md. Locally: 29 labels, 29
# functions, and because `main-exit.` occurs FIVE times every function name is
# SECTION-QUALIFIED. Two fall-throughs are reproduced as explicit calls and
# recorded at their sites, because COBOL fall-through is invisible in the source.
# Public API is `run` alone.
#

# ANOMALIES REPRODUCED (R-4: "a defect reproduced is correct; a defect fixed
# is a failure").  EIGHT sites, each carrying a locator and `DO NOT FIX`.
# --------------------------------------------------------------------------
#  A-PL100-A  [L566-L570]  in _bl_open - a MUTUALLY EXCLUSIVE `IF ... ELSE`
#  where every sibling uses two independent `IF`s, `irs-used` tested
#  WITHOUT `IRS-Both-Used`, and NO open-output fallback.  Writes to
#  unopened tables in BOTH IRS modes.  Control:
#  [purchase/pl060.cbl:L907-L920].  Discovered here and now REGISTERED
#  under this name in docs/migration/anomaly-log.md section 15.
#  A-PL100-B  [L356-L361], [L405]  in _init01__cust_update - no supplier is
#  ever created (no `Purch-Write` exists in the program), yet
#  `Purch-Rewrite` is issued unconditionally.  Control:
#  [purchase/pl060.cbl:L436-L440], [purchase/pl060.cbl:L515-L519].
#  REGISTERED under this name.
#  A-PL100-C  [L449]  in _init01__main_end - the whole deduction reversal is
#  gated on `t-deduct` ALONE, so `n-deduct` can drift permanently.
#  REGISTERED under this name.
#
#  THE ALIAS MAP, STATED HERE SO A GREP FOR A BARE `A-NEW-<n>` LANDS SOMEWHERE. The
#  three candidates above are the ones a reader may meet as bare `A-NEW-5`, `A-NEW-6`
#  and `A-NEW-7`, numbers meaningful in this file alone.  The project register in
#  docs/migration/anomaly-log.md had independently allocated those same three
#  numbers to unrelated defects - A-NEW-5 to "Purchase has no abort gate at all",
#  A-NEW-6 to the reachable gl080 divide-by-zero and A-NEW-7 to a comment naming a
#  field that does not exist - so one token meant two things depending on which file
#  a reader was in.  The register keeps its numbers, these three take globally unique
#  names, and the old-to-new map is published in that register:
#  A-NEW-5 -> A-PL100-A, A-NEW-6 -> A-PL100-B, A-NEW-7 -> A-PL100-C.
#  A-1      [L675]  in _bl_close - THE CONTROL CASE: the period IS present,
#  so [L676] is a SIBLING `if` and `GL-Posting-Close` IS reached in
#  pure-GL mode.  The defective sibling is [sales/sl060.cbl:L1176].
#  A-10     [L495], [L497], [L500-L502]  in _init01__compute_purch_pay -
#  VARIANT (d) of four mutually inconsistent moving-average idioms.
#  Peers: [purchase/pl060.cbl:L743] (a), [purchase/pl060.cbl:L758]
#  (b), [sales/sl100.cbl:L506] (c).  A-8 DOES NOT APPLY HERE.
#  A-17     [L672]  in _bl_close - `move RRN to postings.  *> Why ?`, the
#  maintainer's own question mark.  Occurrence 4 of 4, and
#  LOAD-BEARING via [L564] -> [L572].
#  A-18     [L615-L616], [L640-L641]  in _bl_write - `dr-pc`/`cr-pc` dropped
#  from the IRS record; `31` moved with `*> IS IT ???`.
#  A-21     [L617], [L626], [L631]  in _bl_write - qualified references
#  forced by copybook field-name collisions.
#  NOT PRESENT IN THIS FILE, recorded so a reader does not hunt for them:
#  A-8  (double truncation) - both accumulators here are integer
#  `binary-long` day counts, so there is only ONE truncation.
#  A-22 (wrapper/exit name disagreement) - `maps04` L789 and `maps04-exit`
#  L794 AGREE.  A-22 is at [general/gl070.cbl:L603-L609] and
#  [general/gl051.cbl:L1273]/[general/gl051.cbl:L1278].
#  A-6  (the always-refused rewrite verb, [common/acas008.cbl:L299-L307])
#  is never triggered: `SPL-Posting-Rewrite` is not called here.
#
# --------------------------------------------------------------------------
# FINDINGS - named `F-PL100-<n>` rather than bare `F-<n>`, so a file-local
# candidate cannot be read as an entry of a shared register, and so it cannot be
# confused with the REGISTERED anomalies `A-PL100-A`, `A-PL100-B` and
# `A-PL100-C`. The rule is docs/migration/anomaly-log.md section 15.1.
# Divergences and oddities recorded but not classified as
# registered anomalies.
# --------------------------------------------------------------------------
#  F-PL100-1  [L621]  an INERT store: `move spaces to post-vat-side` is overwritten
#  by `"DR"` at [L627] before any write.  Same pattern at
#  [sales/sl100.cbl:L639]/[L645].  Reproduced, not optimised away.
#  F-PL100-2  [L537]  ASYMMETRY: no `move 1 to File-Key-No` precedes the second
#  `Value-Rewrite`, where [L524] precedes the first.
#  F-PL100-3  [L612-L613]  the DR/CR sides are SWAPPED relative to
#  [purchase/pl060.cbl:L958-L959], and the account is `bl-pay-ac`, not
#  `bl-purch-ac`.
#  F-PL100-4  [L617], [L623-L624]  `vat-ac` is ZEROED where
#  [purchase/pl060.cbl:L966-L967] copies it, and only TWO control totals
#  are accumulated where [purchase/pl060.cbl:L973-L976] accumulates
#  FOUR.  A payment posting carries no VAT.
#  F-PL100-5  [L546], [L548]  the field is `bl-next-batch`, a DIFFERENT
#  `SYSTEM-REC` column from the `next-batch` that
#  [purchase/pl060.cbl:L885-L887] uses.
#  F-PL100-6  §541/§577/§660  the sections are declared LOWER CASE (`bl-open`,
#  `bl-write`, `bl-close`) yet performed as `BL-Open` [L317], `BL-Write`
#  [L410], `bl-close` [L455] and `bl-close`/`bl-open` [L654-L655].
#  COBOL is case-insensitive; the inconsistency is recorded.
#  F-PL100-7  [L670]  the `accept` is NOT wrapped in `if WS-Caller not = "xl150"`,
#  unlike [purchase/pl060.cbl:L1022-L1025] - the unattended-mode branch
#  is simply absent.
#  F-PL100-8  [L671]  the comment reads `*> THIS IS IN PURCHASE PL060` - inside
#  pl100.  A copy-paste artefact present in four files:
#  [sales/sl060.cbl:L1172], [purchase/pl060.cbl:L1027],
#  [sales/sl100.cbl:L690], [purchase/pl100.cbl:L671].
#  F-PL100-9  [L468]  the program ends with `exit program.`, not `goback`.
#  F-PL100-10 [L689-L722]  `zz050-Validate-Date` is DECLARED but NEVER PERFORMED -
#  `grep -c "perform *zz050"` returns 0.  Dead code that R-5 still
#  requires a named function for.
#  F-PL100-11 [L369]  `move u-date to l5-date` uses `u-date`, where
#  [purchase/pl060.cbl:L448] uses `ws-date`.  Presentation only, but the
#  field choice is reproduced.
#  F-PL100-12 [L356]  the unknown-supplier test is `fs-reply = 21`, where
#  [purchase/pl060.cbl:L433] tests `not = zero`.
#  F-PL100-13 [L386-L389]  the sign flip uses the `GIVING` form, so `purch-current`
#  is NOT mutated by the multiply and is zeroed separately at [L389];
#  [purchase/pl060.cbl:L507] uses the no-`GIVING` form, which DOES
#  mutate it.  Net effect equal, intermediate not.
#  F-PL100-14 [L634], [L636], [L638]  the IRS receivers are one digit NARROWER than
#  the GL senders (`9(6)`->`9(5)`, `s9(8)v99`->`s9(7)v99`), so a
#  six-digit account or a nine-digit amount loses its high-order digit.
#  F-PL100-15 [L640-L641]  the second receiver of the `move 31` is `Vat-PC` on the
#  GL POSTING record, written from inside the IRS block, over the zero
#  [L618] had just stored.  So `GLPOSTING-REC.VAT-PC` is 0 in pure-GL
#  mode and 31 in either IRS mode - the IRS switch changes a GL column.
#  F-PL100-19 [L591-L592]  `post-date` is built from `u-date`, which holds the
#  OPEN-ITEM date [L367-L368] unpacked from `oi-date` - NOT the run date.
#  `to-day` never reaches the posting record at all.  Verified at run
#  time: oi-date 155000 -> post-date "17/05/25" for a run of 31/12/2025.
#  F-PL100-16 [L653-L655]  the 99-item cap re-performs `bl-open`, so every reopen
#  repeats A-PL100-A in full.
#  F-PL100-17 [L316-L317], [L409-L410], [L454-L455]  ALL THREE `bl-*` sections are
#  gated on `G-L` ALONE, consistently, so with `G-L` unset none of them
#  runs and the IRS fan-out inside `bl-write` NEVER EXECUTES - the IRS
#  switch is inert unless the General Ledger is also enabled.  Verified
#  by driving the "B"-mode-with-`G-L`-unset case: zero batch and zero
#  posting verbs are reached.  This is NOT a pl100 divergence:
#  [purchase/pl060.cbl:L405-L406], [purchase/pl060.cbl:L474-L475] and
#  [purchase/pl060.cbl:L573-L574] gate identically, so it is a
#  codebase-wide property of the purchase posting family.  Recorded
#  because the coupling is invisible from `bl-write`'s own predicates,
#  which name `irs-used`/`IRS-Both-Used` as though they were sufficient.
#  F-PL100-18 [L671]/[L674]/[L676]  SIX IRS fan-out sites where `sl060`, `sl100`
#  and `pl060` each have SEVEN, and [L566]'s predicate disagrees with
#  [L629]'s.  Not harmonised across programs.
#
# --------------------------------------------------------------------------
# AMBIGUITIES referred to the compiled oracle (R-6).  Five sites, each marked
# `# AMBIGUITY Q-n` at its location.
# --------------------------------------------------------------------------
#  Q-1  _bl_open  - the status pair and row state produced by A-PL100-A's write
#  to an unopened table, in "Y" mode, in "B" mode, and with `G-L` unset.
#  Q-2  _init01__cust_update - the `PULEDGER-REC` state produced by
#  A-PL100-B's rewrite of a record that was never successfully read.
#  Q-3  _init01__main_end - the `VALUEANAL-REC` count drift from A-PL100-C, and
#  whether the unsigned count columns underflow or clamp.
#  Q-4  _bl_write - the exact `post-date` text the century-dropping
#  reference modification at [L591-L592] yields per `Date-Form`.
#  Q-5  _init01__compute_purch_pay - the stored value of `purch-pay-average`
#  if the bridge narrows a signed `binary-long` to an unsigned column.
#
# --------------------------------------------------------------------------
# OMISSIONS - deliberate, and recorded so nothing looks lost.
# --------------------------------------------------------------------------
#  O-1  [L446]  `call "SYSTEM" using Print-Report` - the spool-out path,
#  which plan section 0.1.1 EXPLICITLY excludes.  Omitted entirely.
#  This is the ONLY non-migratable `call` in the program: pl100 has
#  NO `call "CBL_*"` library calls and NO `FS-Cobol-Files-Used`-gated
#  library block at all, unlike pl055 (`call "sl070"`), pl060 (four
#  `CBL_*` calls) and sl060.  Do not go looking for one.
#  O-2  The ENTIRE PRINT FILE: `open output print-file` [L319], `close
#  print-file` [L445], every `write print-record` ([L420], [L438],
#  [L444], [L484-L485]), the `line-1`..`line-5` layouts [L221-L256],
#  `j`, `l1-name`, `l1-page`, `l2-date`, `l2-user`, `Print-Spool-Name`,
#  `PSN`, and `copy "selprint"` [L115] / `"fdprint"` [L122] /
#  `"print-spool-command"` [L127].  `headings` [L470] SURVIVES as a
#  named log-only function because R-5 requires it, and `line-cnt` is
#  still maintained because [L422] tests it.
#  O-3  `display ... at` -> A LOG RECORD, BUT NOT ALL OF IT.  Plan section 0.3.4
#  converts a DIAGNOSTIC display, and such records "must not alter control
#  flow and must not appear in any table dump" - none of these does.
#  CONVERTED: [L290] (`PL137`), [L298-L299] (the banner) and [L665-L668]
#  (the batch-write failure with its file status, we-error and the decoded
#  status name).  NOT CONVERTED, each for a stated reason:
#  - [L291] and [L669] - `PL002`.  PURE ACKNOWLEDGEMENT PROMPTS standing
#  immediately before the `accept ws-reply`s of O-4; the whole of the
#  literal is the key-press instruction, so nothing substantive is lost.
#  `P-Flag-P`, which the [L290] record once narrated, is a SYSTEM-REC
#  host-variable value and is excluded by the safe-event schema in
#  `acas_posting/dal/status.py` (CWE-532) - and the frozen display shows
#  the literal alone in any case.
#  - [L301] - `display ws-date`.  THE POSTING DATE IS BUSINESS DATA,
#  excluded by the same schema; it is a command-line INPUT that
#  `clock.py` pins.
#  - [L303-L304] - the run-confirm PROMPT.  It is the screen text for the
#  `accept wx-reply` that O-4 resolves into the `ok_to_post` parameter,
#  so reproducing it would log a question no one can answer, and echoing
#  the answer would restate a command-line argument.
#  Nothing from `01 line-1`..`line-5` is logged either: [L433-L444] (the two
#  total blocks) and [L472-L473] (the page number and the operator identity)
#  are report content, out of scope per plan section 0.2.2, and the amounts
#  and user identity they carry are excluded by the safe-event schema.
#  `run()` emits NO entry or exit record: the COBOL displays nothing on
#  either boundary, so both would be invented output (R-4).
#  O-4  `accept wx-reply` [L306] -> the explicit `ok_to_post` parameter of
#  `run()`, because it GATES A DATABASE WRITE.  That parameter carries NO
#  default: [L157], [L305] and [L310-L311] leave the frozen prompt with
#  none, so section 0.3.4's "with the COBOL default preserved" has nothing
#  to preserve and the answer is required of the caller.  `accept ws-reply` [L292]
#  and [L670] -> DROPPED as acknowledgement pauses; but [L293]'s
#  `go to menu-exit` control transfer IS PRESERVED.
#  O-5  `set ENVIRONMENT` [L276-L277] and `copy "envdiv.cob"` [L108] -
#  representation only.
#  O-6  `01 Dummies-4-Unused-ACAS-FH-Calls.` [L133] - pl100 declares the
#  group but NO facade stub block of the kind [general/gl072.cbl:L135]
#  and [general/gl080.cbl:L194] carry; Python needs no linker
#  satisfaction either way.  Maps to nothing.
#  O-7  The message literals.  `PL132` [L207] and `PL137` [L208] survive as log
#  text.  `PL002` [L204] is DECLARED AND DELIBERATELY NEVER REFERENCED - it
#  is the acknowledgement prompt of O-3 - and stays declared because rule
#  R-5 maps the whole `01 Error-Messages.` group.
#  O-8  The local print totals `t-approp`, `j-approp`, `j-paid` and
#  `j-deduct` are still COMPUTED - [L396] and [L448] consume them - but
#  their print lines are omitted.  `t-paid`, `t-deduct` and `n-deduct`
#  are LOAD-BEARING: `t-paid` receives period total 9 alongside
#  `pl-payments`, and `t-deduct`/`n-deduct` drive [L449] and the whole
#  of `analise-deductions`.
#  O-9  Absent facade verbs, stated so a reader does not expect them: NO
#  `GL-Posting-Open-Output`, NO `SPL-Posting-Open-Output` (that absence
#  IS A-PL100-A defect (c)), NO `Purch-Write` (that absence IS A-PL100-B),
#  NO `OTM5-Start` and NO `set fn-*` anywhere - the OTM5 walk is purely
#  sequential from the top, with no cursor positioning at all.
#  O-10 NO WORK FILE.  pl100 declares no `seloi4`/`fdoi4` and no
#  `plwsoi`/`plwssoi`, unlike pl055/pl060 which share OTM4.  Nothing
#  imports `acas_posting.workfiles`.
#  O-11 ZERO `ROUNDED` sites.  Every store in this program truncates toward
#  zero.  The migration's five `ROUNDED` sites are
#  [general/gl051.cbl:L791], [general/gl051.cbl:L796],
#  [general/gl080.cbl:L328], [irs/irs030.cbl:L1551] and
#  [irs/irs030.cbl:L1562].
#  O-12 `copy "FileStat-Msgs.cpy"` [L684-L685] - the message text is taken
#  from `dal.status.FsReply` rather than duplicating the copybook's
#  literal table; the rendering is diagnostic and reaches no table.
#
# --------------------------------------------------------------------------
# FIELD -> DICTIONARY ENTRY.  Every `FieldDescriptor` above is built either
# by `FieldDescriptor.from_dictionary_key(...)` - so it carries a
# `dictionary_key` resolved from `data_dictionary/acas_posting_dictionary.json`
# - or by `_local(...)`, which stamps a `source_locator` of the form
# `purchase/pl100.cbl:L<n>` naming the working-storage line it was read from.
# `_OI_*_D` descriptors come from `records.otm5.descriptors_of`, which carries
# the copybook's own dictionary keys.  No descriptor is hand-built.
# --------------------------------------------------------------------------
# --- end traceability ---
