"""`pl055` - Purchase order proof report extract [purchase/pl055.cbl].

The whole program, and the Purchase mirror of `sl055`: it walks the purchase
invoice file, extracts the postings the Purchase posting run needs and builds the
analysis totals.

Credit notes are carried by sign flips [purchase/pl055.cbl:L376],
[purchase/pl055.cbl:L387], [purchase/pl055.cbl:L572-L575], reproduced field by
field.

Two of the cycle's nine period-total writes are here - purchase invoices
[purchase/pl055.cbl:L582] and purchase credit notes
[purchase/pl055.cbl:L584].

A missing input file answers with terminate code 8 and returns
[purchase/pl055.cbl:L286-L287], which the menu treats as a serious error.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field as dataclass_field, fields as dataclasses_fields
from decimal import Decimal
from types import ModuleType
from typing import Any, Final

# `MULTIPLY -1 BY x`, `ADD ... GIVING`, `ADD ... TO` and `SUBTRACT ... FROM`. Every
# store in this module truncates toward zero.
from acas_posting.cobol import arithmetic

from acas_posting.cobol import condition_names

from acas_posting.cobol import move

from acas_posting.cobol import picture

from acas_posting.cobol.field import FieldDescriptor, descriptors_for_copybook_record

# copy "wsfnctn.cob". [purchase/pl055.cbl:L128] `Fs-Reply pic 99`
# [copybooks/wsfnctn.cob:L25] is tested at six sites in this program and never against a
# bare integer literal.
from acas_posting.dal.status import FsReply

# `zz070-Convert-Date` [purchase/pl055.cbl:L599-L627] is byte-identical in all ten
# carrying programs, so it is consolidated rather than re-implemented.
from acas_posting.dates import WsDateFormats, zz070_convert_date

from acas_posting.records.analysis import WsAnalysisRecord

from acas_posting.records.calling_data import (
    WsCallingData,
    descriptor_for as calling_data_descriptor_for,
)

from acas_posting.records.file_access import FileAccess

from acas_posting.records.file_defs import FileDefs

# copy "plwsoi.cob". [purchase/pl055.cbl:L121] The 113-byte purchase Open Item Header.
from acas_posting.records.otm5 import (
    Filler1,
    OiBatch,
    OiCustomer,
    OiHeader,
    OiKey,
    OiSupplier,
    descriptors_of as otm5_descriptors_of,
)

# copy "plwspinv2.cob". [purchase/pl055.cbl:L135] THE FLAT SHAPE, not the nested
# `plwspinv.cob` one.
from acas_posting.records.purchase_invoice import (
    IhFig2,
    IhInvoiceHeader,
    IhSupplier2,
    IlInvoiceLine,
    InvoiceKey,
    WsPInvoiceRecord,
    descriptor_for as pinvoice_descriptor_for,
)

from acas_posting.records.system_record import SystemRecord

from acas_posting.records.system_record_4 import SystemRecord4

from acas_posting.records.test_data_flags import AcasDalCommonData

from acas_posting.records.value_analysis import WsValueRecord

# `open extend`/`open output`/`write`/`close open-item-file-4`
# [purchase/pl055.cbl:L301-L304, L423, L587] act on a transient work file that
# reaches no schema table - and that `pl060` READS, so it is a channel and must be
# ONE object. `acas_posting.workfiles` publishes that object, `OpenItemWorkFile`,
# along with `OpenMode.EXTEND` and the raw file statuses it reports. The file was
# once declared module-privately here on the ground that `OpenMode` had no
# `EXTEND`; the ground was true and the conclusion was wrong - see STRUCTURAL
# NOTES.
from acas_posting.workfiles import (
    OPEN_ITEM_4_NAME,
    OpenItemWorkFile,
    open_item_work_file,
)

#: Agent Action Plan section 0.3.3, verbatim.
__all__: Final[tuple[str, ...]] = ("run",)


_LOG: Final[logging.Logger] = logging.getLogger(__name__)


# Field descriptors Three provenances, because the frozen sources have three. Record
# fields the bridge maps come from the generated data dictionary.


def _by_name(record: str) -> dict[str, FieldDescriptor]:
    """Descriptors of one dictionary-backed copybook record, keyed lower-case.

    `descriptors_for_copybook_record` returns them in copybook order with the copybook's
    own capitalisation - `va-t-this` in one record and `Pa-Gl` in another - so the key
    is folded to make a lookup independent of a transcription choice the copybook author
    made forty years ago.
    """
    return {d.name.lower(): d for d in descriptors_for_copybook_record(record)}


_VAL: Final[dict[str, FieldDescriptor]] = _by_name("WS-Value-Record")

_ANL: Final[dict[str, FieldDescriptor]] = _by_name("WS-Analysis-Record")

_S4: Final[dict[str, FieldDescriptor]] = _by_name("System-Record-4")

_VALUE_RECORD_BYTES: Final[int] = 66
_ANALYSIS_RECORD_BYTES: Final[int] = 36

#: The four alphanumeric/display fields the group move at [purchase/pl055.cbl:L452]
#: actually carries, as 1-based `(offset:length)` pairs into the 66-byte receiver.
_VALUE_HEAD_LAYOUT: Final[tuple[tuple[str, int, int], ...]] = (
    ("va-code", 1, 3),
    ("va-gl", 4, 6),
    ("va-desc", 10, 24),
    ("va-print", 34, 3),
)

#: copy "plwsoi.cob". [purchase/pl055.cbl:L121] The 113-byte OTM4 header.
_OI: Final[dict[str, FieldDescriptor]] = dict(otm5_descriptors_of(OiHeader))
_OI_MONEY: Final[dict[str, FieldDescriptor]] = dict(otm5_descriptors_of(Filler1))
_OI_KEY: Final[dict[str, FieldDescriptor]] = dict(otm5_descriptors_of(OiKey))
_OI_BATCH: Final[dict[str, FieldDescriptor]] = dict(otm5_descriptors_of(OiBatch))
_OI_CUSTOMER: Final[dict[str, FieldDescriptor]] = dict(otm5_descriptors_of(OiCustomer))
_OI_SUPPLIER: Final[dict[str, FieldDescriptor]] = dict(otm5_descriptors_of(OiSupplier))


def _ws(clauses: str, name: str, line: int) -> FieldDescriptor:
    """A descriptor for one of `01 ws-data.`'s own fields.

    `01 ws-data.` [purchase/pl055.cbl:L161-L179] is program-local working storage. It
    reaches no table, so the bridge never saw it and the generated dictionary has no
    entry for it.
    """
    return picture.descriptor_for(
        clauses, name=name, source_locator=f"purchase/pl055.cbl:L{line}"
    )


_D_ANAL_CREATED: Final[FieldDescriptor] = _ws("pic 9", "Anal-Created", 163)
_D_SAVE_CODE: Final[FieldDescriptor] = _ws("pic xxx", "save-code", 164)
_D_INV_AMT: Final[FieldDescriptor] = _ws("pic s9(7)v99 comp-3", "ws-inv-amt", 165)
_D_WORK_2: Final[FieldDescriptor] = _ws("pic s9(7)v99 comp-3", "work-2", 166)
_D_WORK_3: Final[FieldDescriptor] = _ws("pic s9(5) comp", "work-3", 167)
_D_VAT_TOTALV: Final[FieldDescriptor] = _ws("pic s9(7)v99 comp-3", "ws-vat-totalv", 168)
_D_VATR_TOTALV: Final[FieldDescriptor] = _ws("pic s9(7)v99 comp-3", "ws-vatr-totalv", 169)
_D_CARR_TOTALV: Final[FieldDescriptor] = _ws("pic s9(7)v99 comp-3", "ws-carr-totalv", 170)
_D_DISC_TOTALV: Final[FieldDescriptor] = _ws("pic s9(7)v99 comp-3", "ws-disc-totalv", 171)
#: The four counts, [purchase/pl055.cbl:L172-L175]. Signed `comp`, so the count
#: arithmetic is integer arithmetic and never touches `Decimal`.
_D_VAT_TOTALT: Final[FieldDescriptor] = _ws("pic s9(5) comp", "ws-vat-totalt", 172)
_D_VATR_TOTALT: Final[FieldDescriptor] = _ws("pic s9(5) comp", "ws-vatr-totalt", 173)
_D_CARR_TOTALT: Final[FieldDescriptor] = _ws("pic s9(5) comp", "ws-carr-totalt", 174)
_D_DISC_TOTALT: Final[FieldDescriptor] = _ws("pic s9(5) comp", "ws-disc-totalt", 175)
_D_V_EXISTS: Final[FieldDescriptor] = _ws("pic 9", "v-exists", 176)
#: `03 WS-Term-Code pic 99.` [copybooks/wscall.cob:L10], widened from `pic 9` on
#: 14/11/25 [copybooks/wscall.cob:L4], which is why 8 fits it comfortably.
_D_TERM_CODE: Final[FieldDescriptor] = calling_data_descriptor_for("ws_term_code")

_PROG_NAME: Final[str] = "PL055 (3.3.00)"

_PL003: Final[str] = "PL003 Hit Return To Continue"
_PL006: Final[str] = "PL006 Note Details & Hit Return to continue"
_PL201: Final[str] = "PL201 Analyst records with desc, 'Emergency Name' created"
_PL202: Final[str] = "PL202 You will need to update these"
_PL203: Final[str] = "PL203 P.A. File Does Not Exist"
_PL204: Final[str] = "PL204 Error writing to Open Item 4 File "

#: The character images of the only two literals `pl055` compares against an
#: ALPHANUMERIC field, resolved once through the receiving descriptor rather than
#: written as Python literals.
_IL_TYPE_3: Final[str] = move.move_alphanumeric(
    3, pinvoice_descriptor_for(IlInvoiceLine, "il_type")
)
_SPACE_1: Final[str] = move.move_figurative(move.SPACE, _VAL["va-second"])


class _CobolFilesModeUnsupportedError(RuntimeError):
    """`if FS-Cobol-Files-Used` was true, and that branch cannot be migrated.

    The block guarded by `if FS-Cobol-Files-Used` [purchase/pl055.cbl:L266-L290] does
    three things this migration cannot do.
    """


#: The only group items in the three `plwspinv2.cob` views, named explicitly
#: rather than discovered, so that a reader can check the list against the
#: copybook: `03 Invoice-Key.` [copybooks/plwspinv2.cob:L11], `03 ih-supplier.`
#: [copybooks/plwspinv2.cob:L24] and `03 ih-fig comp-3.`
#: [copybooks/plwspinv2.cob:L31]. `Invoice-Line` has none.
_PINVOICE_GROUPS: Final[dict[type, dict[str, type]]] = {
    WsPInvoiceRecord: {"invoice_key": InvoiceKey},
    IhInvoiceHeader: {"ih_supplier": IhSupplier2, "ih_fig": IhFig2},
    IlInvoiceLine: {},
    # The three subordinate groups themselves contain only elementary items - `05
    # Invoice-Nos` / `05 Item-Nos` [copybooks/plwspinv2.cob:L12-L13], `05 ih-nos` / `05
    # ih-check` [copybooks/plwspinv2.cob:L25-L26] and the eight `05 ih-...` money fields
    # [copybooks/plwspinv2.cob:L32-L39] - so the recursion terminates here.
    InvoiceKey: {},
    IhSupplier2: {},
    IhFig2: {},
}


def _initial_pinvoice_view(record_class: type) -> Any:
    """A `plwspinv2.cob` view with every field at its category's initial value.

    `copy "plwspinv2.cob"` [purchase/pl055.cbl:L135] declares one 100-byte working-
    storage area under three names - the base record and its two redefinitions - and
    NONE of its fields carries a `VALUE` clause.
    """
    values: dict[str, Any] = {}
    for attribute, nested_class in _PINVOICE_GROUPS[record_class].items():
        values[attribute] = _initial_pinvoice_view(nested_class)
    for attribute in _pinvoice_attributes(record_class):
        if attribute in values:
            continue
        descriptor = pinvoice_descriptor_for(record_class, attribute)
        figurative = move.ZERO if descriptor.is_numeric else move.SPACE
        values[attribute] = move.move_figurative(figurative, descriptor)
    return record_class(**values)


def _pinvoice_attributes(record_class: type) -> tuple[str, ...]:
    """The dataclass attribute names of one `plwspinv2.cob` view, in order."""
    return tuple(f.name for f in dataclasses_fields(record_class))


@dataclass
class _FacadeContext:
    """The operands the three handler dispatch paragraphs pass, in their order.

    One object rather than three parameter lists, because the Agent Action Plan fixes
    the facade call form as a single argument - section 0.4.3 gives `perform GL-Batch-
    Read-Next` becoming `facade.gl_batch_read_next(ctx)`.
    """

    system_record: SystemRecord
    ws_value_record: WsValueRecord
    ws_analysis_record: WsAnalysisRecord
    ws_pinvoice_record: WsPInvoiceRecord
    invoice_header: IhInvoiceHeader
    invoice_line: IlInvoiceLine
    file_access: FileAccess
    file_defs: FileDefs
    acas_dal_common_data: AcasDalCommonData

    #: The one `WS-PInvoice-Record` area the `acas026` `CALL` reaches, built on first
    #: use and then held.
    _pinvoice_record_area: _PInvoiceRecordArea | None = dataclass_field(
        default=None, init=False, repr=False, compare=False
    )

    def pinvoice_record_area(self) -> _PInvoiceRecordArea:
        """`WS-PInvoice-Record` as ONE area, stable for the life of the run.

        ⭐ THE SAME OBJECT ON EVERY VERB, deliberately. A COBOL record area is one
        storage for the life of the program, and the data-access layer relies on that.
        """
        area = self._pinvoice_record_area
        if area is None:
            area = _PInvoiceRecordArea(
                ws_pinvoice_record=self.ws_pinvoice_record,
                invoice_header=self.invoice_header,
                invoice_line=self.invoice_line,
            )
            self._pinvoice_record_area = area
        return area

    @property
    def invoice_fig(self) -> IhFig2:
        """`03 ih-fig comp-3.` [copybooks/plwspinv2.cob:L31]

        The eight money fields of the header live in a subordinate group, so they are
        reached through it rather than duplicated beside it - a second reference would
        be a second copy of one 113-byte record area, and keeping the views coherent is
        the whole point of a redefinition.
        """
        return self.invoice_header.ih_fig


_ENTITY_RECORD: Final[dict[str, str]] = {
    "value": "ws_value_record",
    "analysis": "ws_analysis_record",
    "pinvoice": "ws_pinvoice_record",
}


@dataclass(frozen=True, slots=True)
class _PInvoiceRecordArea:
    """`WS-PInvoice-Record` and its two `REDEFINES` views - ONE record area.

    THE OPERAND `acas026`'s DISPATCH PARAGRAPH NAMES is `WS-PInvoice-Record`
    [copybooks/Proc-ACAS-FH-Calls.cob:L156-L162], and in the compiled program that
    single name reaches the whole hundred bytes - so the callee sees the header view and
    the line view too, because `01 Invoice-Header redefines WS-PInvoice-Record.`
    [copybooks/plwspinv2.cob:L21] and `01 Invoice-Line redefines WS-PInvoice-Record.`
    [:L56] ARE those bytes.
    """

    ws_pinvoice_record: WsPInvoiceRecord
    invoice_header: IhInvoiceHeader
    invoice_line: IlInvoiceLine


class _BoundFacade:
    """`_FacadeContext` on this side, `facade.FacadeContext` on the other.

    So `_FacadeContext` stays exactly as it is - it is this module's record of the union
    of the three `using` lists, which is what makes them diffable against the copybook -
    and the pick happens here, at the boundary.
    """

    __slots__ = ("_facade",)

    def __init__(self, facade_module: ModuleType) -> None:
        self._facade = facade_module

    def __getattr__(self, verb: str) -> Any:
        """Bind one entity-named verb, resolving its record area by prefix."""
        entity = next(
            (name for name in _ENTITY_RECORD if verb.startswith(f"{name}_")), None
        )
        if entity is None:
            raise AttributeError(
                f"pl055 performs no facade verb {verb!r}; it copies "
                f'copy "Proc-ACAS-FH-Calls.cob". [purchase/pl055.cbl:L634] and '
                f"reaches only the Value, Analysis and PInvoice entities"
            )
        target = getattr(self._facade, verb)
        record_attribute = _ENTITY_RECORD[entity]

        def _operand(ctx: _FacadeContext) -> Any:
            """The second operand of the `CALL`, as the copybook names it.

            For Value and Analysis that is one record and one object. For PInvoice the
            COBOL name reaches the whole record AREA including its two redefinitions, so
            the trio goes over under the one name - see `_PInvoiceRecordArea` and
            `_FacadeContext.pinvoice_record_area`.
            """
            if entity == "pinvoice":
                return ctx.pinvoice_record_area()
            return getattr(ctx, record_attribute)

        def _perform(ctx: _FacadeContext, /) -> None:
            target(
                self._facade.FacadeContext(
                    ctx.system_record,
                    _operand(ctx),
                    ctx.file_access,
                    ctx.file_defs,
                    ctx.acas_dal_common_data,
                )
            )

        return _perform


@dataclass
class _Pl055State:
    """Everything `pl055` holds between statements."""

    ctx: _FacadeContext
    facade: ModuleType | _BoundFacade
    open_item_file_4: OpenItemWorkFile[OiHeader]
    ws_calling_data: WsCallingData
    system_record_4: SystemRecord4
    to_day: str
    ws_date_formats: WsDateFormats

    anal_created: int = 0
    save_code: str = ""
    ws_inv_amt: Decimal = Decimal("0.00")
    work_2: Decimal = Decimal("0.00")
    work_3: int = 0
    ws_vat_totalv: Decimal = Decimal("0.00")
    ws_vatr_totalv: Decimal = Decimal("0.00")
    ws_carr_totalv: Decimal = Decimal("0.00")
    ws_disc_totalv: Decimal = Decimal("0.00")
    ws_vat_totalt: int = 0
    ws_vatr_totalt: int = 0
    ws_carr_totalt: int = 0
    ws_disc_totalt: int = 0
    v_exists: int = 0
    exception_msg: str = " " * 25
    oi_header: OiHeader = dataclass_field(default_factory=lambda: _initialise_oi_header())


def _initialise_oi_header() -> OiHeader:
    """`initialise OI-Header.` [purchase/pl055.cbl:L547]

    ⭐ DIVERGENCE 5, THE BEHAVIOURAL ONE, PRESERVED AS WRITTEN. `pl055` spells the verb
    the British way and, critically, omits the `WITH FILLER` phrase that its sales
    counterpart carries.
    """
    zero_net = move.move_figurative(move.ZERO, _OI_MONEY["oi_net"])
    return OiHeader(
        oi_key=OiKey(
            oi_customer=OiCustomer(
                oi_supplier=OiSupplier(
                    oi_nos=move.move_figurative(move.SPACE, _OI_SUPPLIER["oi_nos"]),
                    oi_check=move.move_figurative(move.ZERO, _OI_SUPPLIER["oi_check"]),
                )
            ),
            oi_invoice=move.move_figurative(move.ZERO, _OI_KEY["oi_invoice"]),
        ),
        oi_date=move.move_figurative(move.ZERO, _OI["oi_date"]),
        oi_batch=OiBatch(
            oi_b_nos=move.move_figurative(move.ZERO, _OI_BATCH["oi_b_nos"]),
            oi_b_item=move.move_figurative(move.ZERO, _OI_BATCH["oi_b_item"]),
        ),
        oi_type=move.move_figurative(move.ZERO, _OI["oi_type"]),
        oi_ref=move.move_figurative(move.SPACE, _OI["oi_ref"]),
        oi_order=move.move_figurative(move.SPACE, _OI["oi_order"]),
        oi_hold_flag=move.move_figurative(move.SPACE, _OI["oi_hold_flag"]),
        oi_unapl=move.move_figurative(move.SPACE, _OI["oi_unapl"]),
        filler_1=Filler1(
            oi_p_c=move.move_figurative(move.ZERO, _OI_MONEY["oi_p_c"]),
            oi_net=zero_net,
            oi_approp=zero_net,
            oi_extra=move.move_figurative(move.ZERO, _OI_MONEY["oi_extra"]),
            oi_carriage=move.move_figurative(move.ZERO, _OI_MONEY["oi_carriage"]),
            oi_vat=move.move_figurative(move.ZERO, _OI_MONEY["oi_vat"]),
            oi_discount=move.move_figurative(move.ZERO, _OI_MONEY["oi_discount"]),
            oi_e_vat=move.move_figurative(move.ZERO, _OI_MONEY["oi_e_vat"]),
            oi_c_vat=move.move_figurative(move.ZERO, _OI_MONEY["oi_c_vat"]),
            oi_paid=move.move_figurative(move.ZERO, _OI_MONEY["oi_paid"]),
        ),
        oi_status=move.move_figurative(move.ZERO, _OI["oi_status"]),
        oi_deduct_days=move.move_figurative(move.ZERO, _OI["oi_deduct_days"]),
        oi_deduct_amt=move.move_figurative(move.ZERO, _OI["oi_deduct_amt"]),
        oi_deduct_vat=move.move_figurative(move.ZERO, _OI["oi_deduct_vat"]),
        oi_days=move.move_figurative(move.ZERO, _OI["oi_days"]),
        oi_cr=move.move_figurative(move.ZERO, _OI["oi_cr"]),
        oi_applied=move.move_figurative(move.SPACE, _OI["oi_applied"]),
        oi_date_cleared=move.move_figurative(move.ZERO, _OI["oi_date_cleared"]),
    )


def _mainline(st: _Pl055State) -> None:
    """`mainline section.` [purchase/pl055.cbl:L246-L304]

    Opens the four files and falls through into the read loop. Everything that survives
    migration is in the last fourteen lines; the first seventeen are terminal geometry,
    screen environment and a branch that cannot run.

    Args:
        st: The program's state, carrying the linkage records, the facade and the OTM4
            sequence.

    Raises:
        _CobolFilesModeUnsupportedError: If `FS-Cobol-Files-Used` is true. See that
            class for why the branch cannot be migrated and why it cannot arise in the
            configuration this migration targets.
    """
    # 261 perform Value-Open. FINDING / DIVERGENCE 11 [purchase/pl055.cbl:L261] vs
    # [sales/sl055.cbl:L319-L324] - the sales program probes for the file's existence
    # here and this one does not.
    st.facade.value_open(st.ctx)

    # 266 if FS-Cobol-Files-Used The gate is reproduced, and reproduced DATA-DRIVEN
    # through the condition name so the decision is made at run time from `07 File-
    # System-Used pic 9.` [copybooks/wssystem.cob:L112] exactly as the COBOL makes it -
    # not decided here by an assumption about how the run is configured.
    if condition_names.evaluate(
        "FS-Cobol-Files-Used",
        st.ctx.system_record.system_data_block.rdbms_flat_statuses.file_system_used,
    ):
        # 286 move 8 to WS-Term-Code Set BEFORE raising, so the observable consequence
        # the COBOL leaves on its abort path is present for any caller that catches the
        # error.
        st.ws_calling_data.ws_term_code = move.move(8, _D_TERM_CODE)
        # 287 goback FINDING [purchase/purchase.cbl:L704-L705] - term code 8 makes the
        # shared dispatch paragraph `go to overrewrite`, which abandons the `perform
        # load000.` return at [purchase/purchase.cbl:L760] and ends the menu program, so
        # `pl060` never runs.
        raise _CobolFilesModeUnsupportedError(
            "purchase/pl055.cbl:L266-L290 requires call "
            '"CBL_CHECK_FILE_EXIST" and call "sl070"; sl070 is out of scope '
            "per Agent Action Plan section 0.2.2 and rule R-1 forbids "
            "invoking COBOL at runtime. This branch is unreachable in the "
            "RDBMS configuration the migration targets, where "
            "File-System-Used is 1 (FS-RDBMS-Used) and not zero. "
            "WS-Term-Code has been set to 8 as the COBOL abort path does."
        )

    st.ctx.file_access.logging_data.file_key_no = 1

    # 293 display prog-name at 0101 ... 294 display "Invoice Post Extract" at 0133 ...
    _LOG.info("%s  Invoice Post Extract", _PROG_NAME)

    _zz070_convert_date(st)

    # 296  display  ws-date at 0171 ...
    #
    #  NO LOG COUNTERPART. `ws-date` is the posting date this run stamps into the
    #  records it writes - a date with business meaning, which the safe-event
    #  schema in `acas_posting/dal/status.py` excludes (CWE-532). It is an INPUT
    #  the caller supplied through the `to-day` operand, already known wherever
    #  the run was started and pinned by `clock.py`, so no record is needed to
    #  reconstruct it. The conversion above still runs: it stores `ws-date` and
    #  may default `Date-Form` in the system record, which IS a table effect.

    st.facade.pinvoice_open(st.ctx)
    st.facade.value_open(st.ctx)
    st.facade.analysis_open(st.ctx)

    # 301  open     extend  open-item-file-4.
    st.open_item_file_4.open_extend(st.ctx.file_access)
    # 302  if       fs-reply not = zero
    # The extend-then-fallback idiom: append if you can, otherwise create.
    if st.ctx.file_access.fs_reply != FsReply.SUCCESS:
        # 303           close open-item-file-4
        st.open_item_file_4.close(st.ctx.file_access)
        # 304           open output open-item-file-4.
        st.open_item_file_4.open_output(st.ctx.file_access)

    _read_loop(st)


def _read_loop(st: _Pl055State) -> None:
    """`read-loop.` [purchase/pl055.cbl:L306-L360]

    maintainer modernised the sales extract - `perform until FS-Reply = 10` with `exit
    perform` and `exit perform cycle`, carrying its own note *"changed 18/01/25 for
    clean up using inline perform"* [sales/sl055.cbl:L365] - and never came back to this
    one.

    Args:
        st: The program's state.
    """
    ctx = st.ctx
    line = ctx.invoice_line
    header = ctx.invoice_header
    value = ctx.ws_value_record

    while True:
        st.facade.pinvoice_read_next(ctx)

        # 308 if FS-Reply not = zero 309 go to close-files. GO TO class 2 - forward
        # terminator.
        if ctx.file_access.fs_reply != FsReply.SUCCESS:
            break

        if arithmetic.compare(header.ih_test, 0) == 0:
            _header_analysis(st)
            continue

        # 314 if il-analyised 315 go to read-loop. GO TO class 1 - loop-back.
        if condition_names.evaluate(
            "il-analyised", line.il_update, copybook="copybooks/plwspinv2.cob"
        ):
            continue


        value.va_code.va_system = move.move("P", _VAL["va-system"])
        # 318 move il-pa to va-group. `il-pa pic xx` [copybooks/plwspinv2.cob:L60] into
        # the two-character group `va-group` [copybooks/wsval.cob:L12], so a group move
        # of 2.
        _move_into_va_group(
            value,
            move.move_group(
                line.il_pa,
                _VAL["va-group"],
                sending_field=pinvoice_descriptor_for(IlInvoiceLine, "il_pa"),
                length=2,
            ),
        )
        st.v_exists = move.move(1, _D_V_EXISTS)

        st.ctx.file_access.logging_data.file_key_no = 1
        st.facade.value_read_indexed(ctx)
        # 323 if fs-reply = 21 FINDING [purchase/pl055.cbl:L323] - this site, and
        # [purchase/pl055.cbl:L346], [L510] and [L527], test 21 ALONE, while
        # [purchase/pl055.cbl:L449] tests `= 21 or = 23`.
        if ctx.file_access.fs_reply == FsReply.INVALID_KEY_ON_START:
            _create(st)
            st.v_exists = move.move_figurative(move.ZERO, _D_V_EXISTS)

        value.va_t_this = arithmetic.add_to(
            1, receiver_value=value.va_t_this, receiving=_VAL["va-t-this"]
        )
        value.va_t_year = arithmetic.add_to(
            1, receiver_value=value.va_t_year, receiving=_VAL["va-t-year"]
        )
        # 329 if il-type not = 3 `il-type pic x` [copybooks/plwspinv2.cob:L63] is
        # ALPHANUMERIC, so this compares one character against the image of the literal
        # 3.
        if line.il_type != _IL_TYPE_3:
            value.va_v_this, value.va_v_year = _add_to_pair(
                line.il_net,
                (value.va_v_this, _VAL["va-v-this"]),
                (value.va_v_year, _VAL["va-v-year"]),
            )
        else:
            value.va_v_this, value.va_v_year = _subtract_from_pair(
                line.il_net,
                (value.va_v_this, _VAL["va-v-this"]),
                (value.va_v_year, _VAL["va-v-year"]),
            )

        if arithmetic.compare(st.v_exists, 0) == 0:
            st.facade.value_write(ctx)
        else:
            st.facade.value_rewrite(ctx)

        # 340 if va-second = space 341 go to read-loop. FINDING
        # [purchase/pl055.cbl:L340-L341] cf. [purchase/pl055.cbl:L358-L359] IS RE-
        # ANALYSED - AND THEREFORE DOUBLE-COUNTED - ON EVERY SUBSEQUENT RUN.
        if value.va_code.va_group.va_second == _SPACE_1:
            continue

        value.va_code.va_group.va_second = move.move_figurative(
            move.SPACE, _VAL["va-second"]
        )
        st.ctx.file_access.logging_data.file_key_no = 1
        st.facade.value_read_indexed(ctx)
        if ctx.file_access.fs_reply == FsReply.INVALID_KEY_ON_START:
            continue

        value.va_t_this = arithmetic.add_to(
            1, receiver_value=value.va_t_this, receiving=_VAL["va-t-this"]
        )
        value.va_t_year = arithmetic.add_to(
            1, receiver_value=value.va_t_year, receiving=_VAL["va-t-year"]
        )
        if line.il_type != _IL_TYPE_3:
            value.va_v_this, value.va_v_year = _add_to_pair(
                line.il_net,
                (value.va_v_this, _VAL["va-v-this"]),
                (value.va_v_year, _VAL["va-v-year"]),
            )
        else:
            value.va_v_this, value.va_v_year = _subtract_from_pair(
                line.il_net,
                (value.va_v_this, _VAL["va-v-this"]),
                (value.va_v_year, _VAL["va-v-year"]),
            )
        # 355 move 1 to File-Key-No.
        st.ctx.file_access.logging_data.file_key_no = 1
        st.facade.value_rewrite(ctx)

        # 358 move "z" to il-update. ⭐⭐ DIVERGENCE 6 [purchase/pl055.cbl:L358] vs
        # [sales/sl055.cbl:L421]. LOWER-CASE "z" here.
        line.il_update = move.move(
            "z", pinvoice_descriptor_for(IlInvoiceLine, "il_update")
        )
        st.facade.pinvoice_rewrite(ctx)
        continue

    # The class-2 target of [purchase/pl055.cbl:L309]. Agent Action Plan section 0.6.3,
    # verbatim.
    _close_files(st)


def _move_into_va_group(value: WsValueRecord, image: str) -> None:
    """Scatter a two-character `va-group` image back into its two children.

    `03 va-group.` [copybooks/wsval.cob:L12] is a group over `va-first` and `va-second`
    [copybooks/wsval.cob:L13-L14].
    """
    value.va_code.va_group.va_first = move.move(
        move.ref_mod(image, 1, 1), _VAL["va-first"]
    )
    value.va_code.va_group.va_second = move.move(
        move.ref_mod(image, 2, 1), _VAL["va-second"]
    )


def _add_to_pair(
    source: Decimal | int,
    first: tuple[Decimal | int, FieldDescriptor],
    second: tuple[Decimal | int, FieldDescriptor],
) -> tuple[Any, Any]:
    """`ADD <source> TO <receiver-1> <receiver-2>` - two receivers, one verb.

    Each receiver is added into and stored under its OWN description, which is what a
    multi-receiver `ADD` does: the sender is not summed once and copied twice.
    """
    return (
        arithmetic.add_to(source, receiver_value=first[0], receiving=first[1]),
        arithmetic.add_to(source, receiver_value=second[0], receiving=second[1]),
    )


def _subtract_from_pair(
    source: Decimal | int,
    first: tuple[Decimal | int, FieldDescriptor],
    second: tuple[Decimal | int, FieldDescriptor],
) -> tuple[Any, Any]:
    """`SUBTRACT <source> FROM <receiver-1> <receiver-2>` - two receivers."""
    return (
        arithmetic.subtract_from(source, receiver_value=first[0], receiving=first[1]),
        arithmetic.subtract_from(source, receiver_value=second[0], receiving=second[1]),
    )


def _header_analysis(st: _Pl055State) -> None:
    """`header-analysis.` [purchase/pl055.cbl:L362-L398]

    ⭐ DIVERGENCE 8 - TWO SIGN FLIPS, NOT THREE. The sales program negates three work
    values for a credit note - VAT [sales/sl055.cbl:L446], carriage
    [sales/sl055.cbl:L457] and discount [sales/sl055.cbl:L461-L466].

    Args:
        st: The program's state.
    """
    ctx = st.ctx
    header = ctx.invoice_header
    fig = ctx.invoice_fig

    # ABSENCE IS THE SPECIFICATION. The sales program guards this same point with four
    # things `pl055` does not have.

    if condition_names.evaluate(
        "ih-analyised", header.ih_update, copybook="copybooks/plwspinv2.cob"
    ) and condition_names.evaluate(
        "applied", header.ih_status, copybook="copybooks/plwspinv2.cob"
    ):
        return

    _extract(st)

    if condition_names.evaluate(
        "ih-analyised", header.ih_update, copybook="copybooks/plwspinv2.cob"
    ):
        st.facade.pinvoice_rewrite(ctx)
        return

    st.work_2 = arithmetic.add_giving(fig.ih_c_vat, fig.ih_vat, receiving=_D_WORK_2)
    if arithmetic.compare(header.ih_type, 3) == 0:
        st.work_2 = arithmetic.multiply_by(-1, st.work_2, _D_WORK_2)
    if arithmetic.compare(st.work_2, 0) != 0 and arithmetic.compare(header.ih_type, 1) != 0:
        st.ws_vat_totalt = arithmetic.add_to(
            1, receiver_value=st.ws_vat_totalt, receiving=_D_VAT_TOTALT
        )
        st.ws_vat_totalv = arithmetic.add_to(
            st.work_2, receiver_value=st.ws_vat_totalv, receiving=_D_VAT_TOTALV
        )
    if arithmetic.compare(st.work_2, 0) != 0 and arithmetic.compare(header.ih_type, 1) == 0:
        st.ws_vatr_totalt = arithmetic.add_to(
            1, receiver_value=st.ws_vatr_totalt, receiving=_D_VATR_TOTALT
        )
        st.ws_vatr_totalv = arithmetic.add_to(
            st.work_2, receiver_value=st.ws_vatr_totalv, receiving=_D_VATR_TOTALV
        )
    st.work_2 = move.move(
        fig.ih_carriage,
        _D_WORK_2,
        sending_field=pinvoice_descriptor_for(IhFig2, "ih_carriage"),
    )
    if arithmetic.compare(header.ih_type, 3) == 0:
        st.work_2 = arithmetic.multiply_by(-1, st.work_2, _D_WORK_2)
    if arithmetic.compare(st.work_2, 0) != 0:
        st.ws_carr_totalt = arithmetic.add_to(
            1, receiver_value=st.ws_carr_totalt, receiving=_D_CARR_TOTALT
        )
        st.ws_carr_totalv = arithmetic.add_to(
            st.work_2, receiver_value=st.ws_carr_totalv, receiving=_D_CARR_TOTALV
        )
    st.work_2 = move.move(
        header.ih_deduct_amt,
        _D_WORK_2,
        sending_field=pinvoice_descriptor_for(IhInvoiceHeader, "ih_deduct_amt"),
    )
    if arithmetic.compare(st.work_2, 0) != 0:
        st.ws_disc_totalt = arithmetic.add_to(
            1, receiver_value=st.ws_disc_totalt, receiving=_D_DISC_TOTALT
        )
        st.ws_disc_totalv = arithmetic.add_to(
            st.work_2, receiver_value=st.ws_disc_totalv, receiving=_D_DISC_TOTALV
        )

    header.ih_update = move.move(
        "z", pinvoice_descriptor_for(IhInvoiceHeader, "ih_update")
    )
    st.facade.pinvoice_rewrite(ctx)
    return


def _close_files(st: _Pl055State) -> None:
    """`close-files.` [purchase/pl055.cbl:L400-L432]

    ⭐ ONE CONDITIONAL `goback`, NOT TWO. The sales program has two
    [sales/sl055.cbl:L509, L518] because it also carries a proforma flag; `pl055` has no
    `ws-p-flag` at all and so has one, at [purchase/pl055.cbl:L432], complete with the
    maintainer's shrug.

    Args:
        st: The program's state.
    """
    ctx = st.ctx
    value = ctx.ws_value_record

    value.va_code.va_system = move.move("P", _VAL["va-system"])

    _store_group(st, "vi", st.ws_vat_totalt, _D_VAT_TOTALT, st.ws_vat_totalv, _D_VAT_TOTALV)
    _store_group(
        st, "vj", st.ws_vatr_totalt, _D_VATR_TOTALT, st.ws_vatr_totalv, _D_VATR_TOTALV
    )
    _store_group(
        st, "za", st.ws_carr_totalt, _D_CARR_TOTALT, st.ws_carr_totalv, _D_CARR_TOTALV
    )
    _store_group(
        st, "zb", st.ws_disc_totalt, _D_DISC_TOTALT, st.ws_disc_totalv, _D_DISC_TOTALV
    )

    st.facade.pinvoice_close(ctx)
    st.facade.value_close(ctx)
    st.facade.analysis_close(ctx)
    # 423  close    open-item-file-4.
    st.open_item_file_4.close(st.ctx.file_access)

    if arithmetic.compare(st.anal_created, 0) != 0:
        _LOG.warning("%s", _PL201)
        _LOG.warning("%s", _PL202)
        # 428 if WS-Caller not = "xl150" The codebase's own unattended-mode check: when
        # the out-of-scope `xl150` driver is running the cycle there is nobody at the
        # terminal.
        if not _caller_is_xl150(st):
            # 429                  display PL006 at 1601 ...
            # 430                  accept ws-reply at 1645
            #
            # BOTH DROPPED. `PL006` is "PL006 Note Details & Hit Return to
            # continue" [purchase/pl055.cbl:L218] - the whole literal is the
            # instruction to press the key that the `accept` on the next line
            # reads, so there is no substantive half to keep and a headless run
            # has no operator to instruct. Agent Action Plan section 0.3.4 drops
            # a prompt whose only effect is to block a terminal. The substantive
            # diagnostics are the `PL201`/`PL202` records above, and the BRANCH
            # survives because it is the codebase's own unattended-mode test.
            pass
        # 432           goback.
        # *> Yep, I know but just in case extra code goes here!
        return

    _menu_exit()


def _store_group(
    st: _Pl055State,
    group: str,
    count: int,
    count_field: FieldDescriptor,
    money: Decimal,
    money_field: FieldDescriptor,
) -> None:
    """One `move va-group / move work-3 / move work-2 / perform store-specials`.

    The four blocks at [purchase/pl055.cbl:L404-L419] are textually identical but for
    the group literal and the pair of totals, so the repetition is carried by an
    argument list rather than by four transcriptions of the same four statements.
    """
    value = st.ctx.ws_value_record
    _move_into_va_group(
        value, move.move_group(group, _VAL["va-group"], length=2)
    )
    st.work_3 = move.move(count, _D_WORK_3, sending_field=count_field)
    st.work_2 = move.move(money, _D_WORK_2, sending_field=money_field)
    _store_specials(st)


def _caller_is_xl150(st: _Pl055State) -> bool:
    """`if WS-Caller not = "xl150"` [purchase/pl055.cbl:L283, L428]

    `03 WS-Caller pic x(8).` [copybooks/wscall.cob:L8] is eight characters, so the
    literal is compared space-padded to that width - the shorter operand is extended
    with spaces, which is what makes `"xl150"` match a field holding `"xl150 "`.
    """
    caller = move.move("xl150", calling_data_descriptor_for("ws_caller"))
    return st.ws_calling_data.ws_caller == caller


def _menu_exit() -> None:
    """`menu-exit.` / `goback.` [purchase/pl055.cbl:L434-L435]

    The normal end of the program. `GOBACK` from a called sub-program returns to its
    caller, which is a plain return here - `pl055` is never the main program, as its
    five-parameter `PROCEDURE DIVISION USING` [purchase/pl055.cbl:L239-L243] shows.
    """
    #  NO LOG RECORD. This paragraph displays NOTHING - [purchase/pl055.cbl:L434-L435] carries
    #  the `exit`/`goback` and no other statement - so an "entered/left the
    #  paragraph" event would be output the compiled program never produced.
    #  Rule R-4 forbids inventing observable output on a frozen silent path, and
    #  the function itself is what rule R-5 requires, not a trace of it.


def _create(st: _Pl055State) -> None:
    """`create section.` [purchase/pl055.cbl:L441]

    Kept as its own function rather than folded into `_create__create_main` because rule
    R-5 asks for a named function per SECTION as well as per paragraph, and because the
    two are genuinely different labels.

    Args:
        st: The program's state.
    """
    _create__create_main(st)


def _create__create_main(st: _Pl055State) -> None:
    """`Create-Main.` [purchase/pl055.cbl:L444-L486], of `create section.` L441

    PROGRAM. `Create-Anal` [purchase/pl055.cbl:L488] ends with `go to create-Main`
    [purchase/pl055.cbl:L499] - a BACKWARD transfer to this paragraph, the first of the
    section. So the pair is a retry loop: read the analysis record.

    Args:
        st: The program's state.
    """
    ctx = st.ctx
    value = ctx.ws_value_record
    analysis = ctx.ws_analysis_record

    while True:
        _move_into_pa_code(
            analysis,
            move.move_group(
                _va_code_image(value),
                _ANL["ws-pa-code"],
                sending_field=_VAL["va-code"],
                length=3,
            ),
        )

        ctx.file_access.logging_data.file_key_no = 1
        st.facade.analysis_read_indexed(ctx)
        if ctx.file_access.fs_reply in (
            FsReply.INVALID_KEY_ON_START,
            FsReply.KEY_NOT_FOUND,
        ):
            # 450 go to Create-Anal. GO TO class 4 - sibling re-dispatch.
            _create__create_anal(st)
            continue

        _group_move_analysis_into_value(analysis, value)
        _zero_the_six_value_totals(value)

        if value.va_code.va_group.va_second == _SPACE_1:
            return _create__main_exit()

        st.save_code = move.move(
            _va_code_image(value), _D_SAVE_CODE, sending_field=_VAL["va-code"]
        )

        value.va_code.va_group.va_second = move.move_figurative(
            move.SPACE, _VAL["va-second"]
        )
        _move_into_pa_code(
            analysis,
            move.move_group(
                _va_code_image(value),
                _ANL["ws-pa-code"],
                sending_field=_VAL["va-code"],
                length=3,
            ),
        )

        ctx.file_access.logging_data.file_key_no = 1
        st.facade.analysis_read_indexed(ctx)
        if ctx.file_access.fs_reply == FsReply.INVALID_KEY_ON_START:
            _move_into_pa_code(
                analysis,
                move.move_group(
                    st.save_code,
                    _ANL["ws-pa-code"],
                    sending_field=_D_SAVE_CODE,
                    length=3,
                ),
            )
            # 468 go to main-exit. GO TO class 3 - section exit. ⭐ FINDING
            # [purchase/pl055.cbl:L461, L467-L468] - THIS EXIT RESTORES `WS-Pa-Code` AND
            # LEAVES `va-code` BLANKED.
            return _create__main_exit()

        _group_move_analysis_into_value(analysis, value)
        _zero_the_six_value_totals(value)

        st.facade.value_write(ctx)

        _move_into_va_code(
            value,
            move.move_group(
                st.save_code, _VAL["va-code"], sending_field=_D_SAVE_CODE, length=3
            ),
        )
        _move_into_pa_code(
            analysis,
            move.move_group(
                st.save_code, _ANL["ws-pa-code"], sending_field=_D_SAVE_CODE, length=3
            ),
        )
        ctx.file_access.logging_data.file_key_no = 1
        st.facade.analysis_read_indexed(ctx)
        if ctx.file_access.fs_reply == FsReply.INVALID_KEY_ON_START:
            return _create__main_exit()

        _group_move_analysis_into_value(analysis, value)
        _zero_the_six_value_totals(value)

        return _create__main_exit()


def _create__create_anal(st: _Pl055State) -> None:
    """`Create-Anal.` [purchase/pl055.cbl:L488-L499], of `create section.` L441

    Invents an analysis record so the value record has something to be seeded from, and
    jumps back to `Create-Main` to read it.

    Args:
        st: The program's state.
    """
    ctx = st.ctx
    value = ctx.ws_value_record
    analysis = ctx.ws_analysis_record

    _move_into_pa_code(
        analysis,
        move.move_group(
            _va_code_image(value),
            _ANL["ws-pa-code"],
            sending_field=_VAL["va-code"],
            length=3,
        ),
    )
    analysis.pa_gl = move.move_figurative(move.ZERO, _ANL["pa-gl"])
    analysis.pa_print = move.move_figurative(move.SPACES, _ANL["pa-print"])
    analysis.pa_desc = move.move("Emergency Name - Missing", _ANL["pa-desc"])
    ctx.file_access.logging_data.file_key_no = 1
    st.facade.analysis_write(ctx)
    if analysis.ws_pa_code.pa_group.pa_second != _SPACE_1:
        analysis.ws_pa_code.pa_group.pa_second = move.move_figurative(
            move.SPACE, _ANL["pa-second"]
        )
        st.facade.analysis_write(ctx)
    st.anal_created = move.move(1, _D_ANAL_CREATED)
    return


def _create__main_exit() -> None:
    """`main-exit. exit section.` [purchase/pl055.cbl:L501]

    The `create` section's exit. Named with its section prefix because `main-exit.`
    occurs THREE times in this program - here, at [purchase/pl055.cbl:L536] and at
    [purchase/pl055.cbl:L597] - so paragraph names are not unique and a bare
    `_main_exit` would silently collide.
    """
    #  NO LOG RECORD. This paragraph displays NOTHING - [purchase/pl055.cbl:L501] carries
    #  the `exit`/`goback` and no other statement - so an "entered/left the
    #  paragraph" event would be output the compiled program never produced.
    #  Rule R-4 forbids inventing observable output on a frozen silent path, and
    #  the function itself is what rule R-5 requires, not a trace of it.


def _va_code_image(value: WsValueRecord) -> str:
    """The three-character byte image of `03 va-code.` [copybooks/wsval.cob:L10].

    A group has no value of its own, only the bytes of its children - `va-system`, `va-
    first`, `va-second` [copybooks/wsval.cob:L11-L14]. Assembled here so that a group
    move out of `va-code` has a sender to work from.
    """
    return "".join(
        (
            move.move(value.va_code.va_system, _VAL["va-system"]),
            move.move(value.va_code.va_group.va_first, _VAL["va-first"]),
            move.move(value.va_code.va_group.va_second, _VAL["va-second"]),
        )
    )


def _pa_code_image(analysis: WsAnalysisRecord) -> str:
    """The three-character byte image of `03 WS-Pa-Code.` [copybooks/wsanal.cob:L10]."""
    return "".join(
        (
            move.move(analysis.ws_pa_code.pa_system, _ANL["pa-system"]),
            move.move(analysis.ws_pa_code.pa_group.pa_first, _ANL["pa-first"]),
            move.move(analysis.ws_pa_code.pa_group.pa_second, _ANL["pa-second"]),
        )
    )


def _move_into_va_code(value: WsValueRecord, image: str) -> None:
    """Scatter a three-character `va-code` image into its three children."""
    value.va_code.va_system = move.move(move.ref_mod(image, 1, 1), _VAL["va-system"])
    value.va_code.va_group.va_first = move.move(
        move.ref_mod(image, 2, 1), _VAL["va-first"]
    )
    value.va_code.va_group.va_second = move.move(
        move.ref_mod(image, 3, 1), _VAL["va-second"]
    )


def _move_into_pa_code(analysis: WsAnalysisRecord, image: str) -> None:
    """Scatter a three-character `WS-Pa-Code` image into its three children."""
    analysis.ws_pa_code.pa_system = move.move(
        move.ref_mod(image, 1, 1), _ANL["pa-system"]
    )
    analysis.ws_pa_code.pa_group.pa_first = move.move(
        move.ref_mod(image, 2, 1), _ANL["pa-first"]
    )
    analysis.ws_pa_code.pa_group.pa_second = move.move(
        move.ref_mod(image, 3, 1), _ANL["pa-second"]
    )


def _group_move_analysis_into_value(
    analysis: WsAnalysisRecord, value: WsValueRecord
) -> None:
    """`move WS-Analysis-record to WS-Value-record.`

    child's picture is consulted on either side.
    """
    sender_image = move.move_group(
        _pa_code_image(analysis) + _analysis_tail_image(analysis),
        _ANL["ws-analysis-record"],
        length=_ANALYSIS_RECORD_BYTES,
    )
    image = move.move_group(
        sender_image,
        _VAL["ws-value-record"],
        sending_field=_ANL["ws-analysis-record"],
        length=_VALUE_RECORD_BYTES,
    )
    for name, offset, length in _VALUE_HEAD_LAYOUT:
        piece = move.ref_mod(image, offset, length)
        if name == "va-code":
            _move_into_va_code(value, piece)
        elif name == "va-gl":
            value.va_gl = move.move(piece, _VAL["va-gl"])
        elif name == "va-desc":
            value.va_desc = move.move(piece, _VAL["va-desc"])
        else:
            value.va_print = move.move(piece, _VAL["va-print"])


def _analysis_tail_image(analysis: WsAnalysisRecord) -> str:
    """Bytes 4 to 36 of `WS-Analysis-Record` - everything after the code."""
    return "".join(
        (
            move.move(analysis.pa_gl, _ANL["pa-gl"], sending_field=_ANL["pa-gl"]).rjust(
                6, "0"
            )
            if isinstance(analysis.pa_gl, str)
            else f"{int(analysis.pa_gl):06d}",
            move.move(analysis.pa_desc, _ANL["pa-desc"]),
            move.move(analysis.pa_print, _ANL["pa-print"]),
        )
    )


def _zero_the_six_value_totals(value: WsValueRecord) -> None:
    """`move zero to va-t-this va-t-last va-t-year va-v-this va-v-last va-v-year.`"""
    (
        value.va_t_this,
        value.va_t_last,
        value.va_t_year,
        value.va_v_this,
        value.va_v_last,
        value.va_v_year,
    ) = move.move_to_all(
        move.ZERO,
        (
            _VAL["va-t-this"],
            _VAL["va-t-last"],
            _VAL["va-t-year"],
            _VAL["va-v-this"],
            _VAL["va-v-last"],
            _VAL["va-v-year"],
        ),
    )


def _store_specials(st: _Pl055State) -> None:
    """`store-specials section.` [purchase/pl055.cbl:L503-L534]

    ⭐ IT ADDS. `pl060`'s deduction analysis later SUBTRACTS from these same groups,
    which is why the direction is worth stating rather than assuming.

    Args:
        st: The program's state.
    """
    ctx = st.ctx
    value = ctx.ws_value_record

    st.v_exists = move.move(1, _D_V_EXISTS)

    ctx.file_access.logging_data.file_key_no = 1
    st.facade.value_read_indexed(ctx)
    if ctx.file_access.fs_reply == FsReply.INVALID_KEY_ON_START:
        _create(st)
        st.v_exists = move.move_figurative(move.ZERO, _D_V_EXISTS)

    value.va_t_this = arithmetic.add_to(
        st.work_3, receiver_value=value.va_t_this, receiving=_VAL["va-t-this"]
    )
    value.va_t_year = arithmetic.add_to(
        st.work_3, receiver_value=value.va_t_year, receiving=_VAL["va-t-year"]
    )
    value.va_v_this = arithmetic.add_to(
        st.work_2, receiver_value=value.va_v_this, receiving=_VAL["va-v-this"]
    )
    value.va_v_year = arithmetic.add_to(
        st.work_2, receiver_value=value.va_v_year, receiving=_VAL["va-v-year"]
    )

    if arithmetic.compare(st.v_exists, 0) == 0:
        st.facade.value_write(ctx)
    else:
        st.facade.value_rewrite(ctx)

    value.va_code.va_group.va_second = move.move_figurative(
        move.SPACE, _VAL["va-second"]
    )
    ctx.file_access.logging_data.file_key_no = 1
    st.facade.value_read_indexed(ctx)
    if ctx.file_access.fs_reply == FsReply.INVALID_KEY_ON_START:
        return _store_specials__main_exit()

    value.va_t_this = arithmetic.add_to(
        st.work_3, receiver_value=value.va_t_this, receiving=_VAL["va-t-this"]
    )
    value.va_t_year = arithmetic.add_to(
        st.work_3, receiver_value=value.va_t_year, receiving=_VAL["va-t-year"]
    )
    value.va_v_this = arithmetic.add_to(
        st.work_2, receiver_value=value.va_v_this, receiving=_VAL["va-v-this"]
    )
    value.va_v_year = arithmetic.add_to(
        st.work_2, receiver_value=value.va_v_year, receiving=_VAL["va-v-year"]
    )
    st.facade.value_rewrite(ctx)

    return _store_specials__main_exit()


def _store_specials__main_exit() -> None:
    """`main-exit.   exit section.`   [purchase/pl055.cbl:L536]

    The `store-specials` section's exit - the second of the three paragraphs in
    this program named `main-exit`, hence the section-qualified name.
    """
    #  NO LOG RECORD. This paragraph displays NOTHING - [purchase/pl055.cbl:L536] carries
    #  the `exit`/`goback` and no other statement - so an "entered/left the
    #  paragraph" event would be output the compiled program never produced.
    #  Rule R-4 forbids inventing observable output on a frozen silent path, and
    #  the function itself is what rule R-5 requires, not a trace of it.


def _extract(st: _Pl055State) -> None:
    """`extract section.` [purchase/pl055.cbl:L538-L595]

    Only the second half is implemented, by `if applied` [purchase/pl055.cbl:L544].
    There is NO proforma test anywhere in `pl055` - the sales program has one, `if ih-
    type = 4` [sales/sl055.cbl:L430], routed through a skip paragraph this program does
    not have.

    Args:
        st: The program's state.
    """
    ctx = st.ctx
    header = ctx.invoice_header
    fig = ctx.invoice_fig
    s4 = st.system_record_4.purchase_ledger_data

    if condition_names.evaluate(
        "applied", header.ih_status, copybook="copybooks/plwspinv2.cob"
    ):
        return _extract__main_exit()

    st.oi_header = _initialise_oi_header()
    oi = st.oi_header

    _move_into_oi_supplier(
        oi,
        move.move_group(
            _ih_supplier_image(header),
            _OI_CUSTOMER["oi_supplier"],
            sending_field=pinvoice_descriptor_for(IhInvoiceHeader, "ih_supplier"),
            length=7,
        ),
    )
    oi.oi_key.oi_invoice = move.move(
        header.ih_invoice,
        _OI_KEY["oi_invoice"],
        sending_field=pinvoice_descriptor_for(IhInvoiceHeader, "ih_invoice"),
    )
    oi.oi_date = move.move(
        header.ih_date,
        _OI["oi_date"],
        sending_field=pinvoice_descriptor_for(IhInvoiceHeader, "ih_date"),
    )
    oi.oi_batch.oi_b_nos, oi.oi_batch.oi_b_item = move.move_to_all(
        move.ZERO, (_OI_BATCH["oi_b_nos"], _OI_BATCH["oi_b_item"])
    )
    oi.oi_type = move.move(
        header.ih_type,
        _OI["oi_type"],
        sending_field=pinvoice_descriptor_for(IhInvoiceHeader, "ih_type"),
    )
    oi.oi_ref = move.move(
        header.ih_ref,
        _OI["oi_ref"],
        sending_field=pinvoice_descriptor_for(IhInvoiceHeader, "ih_ref"),
    )
    oi.oi_order = move.move(
        header.ih_order,
        _OI["oi_order"],
        sending_field=pinvoice_descriptor_for(IhInvoiceHeader, "ih_order"),
    )
    oi.filler_1.oi_p_c = move.move_figurative(move.ZERO, _OI_MONEY["oi_p_c"])
    _set_oi_net(
        oi,
        move.move(
            fig.ih_net,
            _OI_MONEY["oi_net"],
            sending_field=pinvoice_descriptor_for(IhFig2, "ih_net"),
        ),
    )
    oi.filler_1.oi_extra = move.move_figurative(move.ZERO, _OI_MONEY["oi_extra"])
    oi.filler_1.oi_carriage = move.move(
        fig.ih_carriage,
        _OI_MONEY["oi_carriage"],
        sending_field=pinvoice_descriptor_for(IhFig2, "ih_carriage"),
    )
    oi.filler_1.oi_vat = move.move(
        fig.ih_vat,
        _OI_MONEY["oi_vat"],
        sending_field=pinvoice_descriptor_for(IhFig2, "ih_vat"),
    )
    oi.filler_1.oi_discount = move.move_figurative(move.ZERO, _OI_MONEY["oi_discount"])
    oi.filler_1.oi_c_vat = move.move(
        fig.ih_c_vat,
        _OI_MONEY["oi_c_vat"],
        sending_field=pinvoice_descriptor_for(IhFig2, "ih_c_vat"),
    )
    oi.filler_1.oi_e_vat = move.move_figurative(move.ZERO, _OI_MONEY["oi_e_vat"])
    oi.filler_1.oi_paid = move.move_figurative(move.ZERO, _OI_MONEY["oi_paid"])
    # 564 move ih-deduct-amt to oi-deduct-amt. FINDING - the sender is UNSIGNED, `pic
    # 999v99 comp` [copybooks/plwspinv2.cob:L46], and the receiver is SIGNED, `pic
    # s999v99 comp` [copybooks/plwsoi.cob:L57].
    oi.oi_deduct_amt = move.move(
        header.ih_deduct_amt,
        _OI["oi_deduct_amt"],
        sending_field=pinvoice_descriptor_for(IhInvoiceHeader, "ih_deduct_amt"),
    )
    oi.oi_deduct_vat = move.move_figurative(move.ZERO, _OI["oi_deduct_vat"])
    oi.oi_deduct_days = move.move(
        header.ih_deduct_days,
        _OI["oi_deduct_days"],
        sending_field=pinvoice_descriptor_for(IhInvoiceHeader, "ih_deduct_days"),
    )
    oi.oi_days = move.move(
        header.ih_days,
        _OI["oi_days"],
        sending_field=pinvoice_descriptor_for(IhInvoiceHeader, "ih_days"),
    )
    oi.oi_status, oi.oi_date_cleared = move.move_to_all(
        move.ZERO, (_OI["oi_status"], _OI["oi_date_cleared"])
    )
    oi.oi_applied, oi.oi_hold_flag = move.move_to_all(
        move.SPACE, (_OI["oi_applied"], _OI["oi_hold_flag"])
    )

    if arithmetic.compare(header.ih_type, 3) == 0:
        # ⭐⭐ DIVERGENCE 1 - FOUR fields, and `oi-deduct-amt` is deliberately not one of
        # them. [purchase/pl055.cbl:L571-L575] against the nine at
        # [sales/sl055.cbl:L658-L666].
        _set_oi_net(oi, arithmetic.multiply_by(-1, oi.filler_1.oi_net, _OI_MONEY["oi_net"]))
        oi.filler_1.oi_carriage = arithmetic.multiply_by(
            -1, oi.filler_1.oi_carriage, _OI_MONEY["oi_carriage"]
        )
        oi.filler_1.oi_vat = arithmetic.multiply_by(
            -1, oi.filler_1.oi_vat, _OI_MONEY["oi_vat"]
        )
        oi.filler_1.oi_c_vat = arithmetic.multiply_by(
            -1, oi.filler_1.oi_c_vat, _OI_MONEY["oi_c_vat"]
        )

    oi.oi_cr = move.move(
        header.ih_cr,
        _OI["oi_cr"],
        sending_field=pinvoice_descriptor_for(IhInvoiceHeader, "ih_cr"),
    )

    if arithmetic.compare(header.ih_type, 1) != 0:
        st.ws_inv_amt = arithmetic.add_giving(
            fig.ih_net,
            fig.ih_carriage,
            fig.ih_vat,
            fig.ih_c_vat,
            receiving=_D_INV_AMT,
        )
    if arithmetic.compare(header.ih_type, 2) == 0:
        s4.pl_invoices_this_month = arithmetic.add_to(
            st.ws_inv_amt,
            receiver_value=s4.pl_invoices_this_month,
            receiving=_S4["pl-invoices-this-month"],
        )
    if arithmetic.compare(header.ih_type, 3) == 0:
        # 584 add ws-inv-amt to pl-credit-notes-this-month. PERIOD TOTAL - site 7 of the
        # nine. `pl-credit-notes-this-month` [copybooks/wssys4.cob:L24].
        s4.pl_credit_notes_this_month = arithmetic.add_to(
            st.ws_inv_amt,
            receiver_value=s4.pl_credit_notes_this_month,
            receiving=_S4["pl-credit-notes-this-month"],
        )

    # 586 move "Z" to ih-status. *> 07/01/18 was "z" ⭐ DIVERGENCE 12 - UPPER case, and
    # `ih-status` alone.
    header.ih_status = move.move(
        "Z", pinvoice_descriptor_for(IhInvoiceHeader, "ih_status")
    )
    # 587  write    open-item-record-4.
    # DIVERGENCE 13 - the FD record name, where the sales program writes the
    # working-storage name [sales/sl055.cbl:L681]. Measured to be the SAME
    # 113-byte area in `pl055`, because `fdoi4.cob` and `plwsoi.cob` are both in
    # its FILE SECTION [purchase/pl055.cbl:L120-L121]; the divergence is which
    # of two names for one storage the programmer typed. See STRUCTURAL NOTES.
    st.open_item_file_4.write(oi, st.ctx.file_access)
    # 588  if       fs-reply not = zero
    if ctx.file_access.fs_reply != FsReply.SUCCESS:
        _a01_eval_status(st)
        _LOG.error(
            "%s fs-reply=%s %s",
            _PL204,
            ctx.file_access.fs_reply,
            st.exception_msg,
        )
        # 593           display  PL006 ...
        # 594           accept   ws-reply ...
        # BOTH DROPPED - the key-press instruction and the key press. The
        # substantive diagnostic is the record above.
        #
        # A REJECTION CLASS WITH A PARTIAL EFFECT, RECORDED. There is no retry,
        # no abort and no control transfer here: the invoice's header has
        # already been stamped `"Z"` at [L586] and will be rewritten by the
        # caller at [purchase/pl055.cbl:L397], but its OTM4 row is missing, so
        # `pl060` will never see it. The sequence is left short and the walk
        # continues. ⛔ Rule R-3 forbids adding either recovery.
        #
        # AMBIGUITY Q-PL055-4 - the disposition of a failed write at
        # [purchase/pl055.cbl:L588]. Whether the compiled program leaves the
        # header stamped as extracted while the extract row is absent is a
        # question for the oracle, not one to resolve by adding a rollback.
    # 595  end-if.

    return _extract__main_exit()


def _extract__main_exit() -> None:
    """`main-exit. exit.` [purchase/pl055.cbl:L597]

    ⭐ DIVERGENCE 18 - A PLAIN `EXIT`, NOT `EXIT SECTION`. The other two sections end
    `main-exit. exit section.` [purchase/pl055.cbl:L501, L536].
    """
    #  NO LOG RECORD. This paragraph displays NOTHING - [purchase/pl055.cbl:L597] carries
    #  the `exit`/`goback` and no other statement - so an "entered/left the
    #  paragraph" event would be output the compiled program never produced.
    #  Rule R-4 forbids inventing observable output on a frozen silent path, and
    #  the function itself is what rule R-5 requires, not a trace of it.


def _ih_supplier_image(header: IhInvoiceHeader) -> str:
    """The seven-character image of `03 ih-supplier.` [copybooks/plwspinv2.cob:L24]."""
    nos = move.move(header.ih_supplier.ih_nos, _OI_SUPPLIER["oi_nos"])
    check = f"{int(header.ih_supplier.ih_check):01d}"
    return nos + check


def _move_into_oi_supplier(oi: OiHeader, image: str) -> None:
    """Scatter a seven-character `oi-supplier` image into its two children."""
    supplier = oi.oi_key.oi_customer.oi_supplier
    supplier.oi_nos = move.move(move.ref_mod(image, 1, 6), _OI_SUPPLIER["oi_nos"])
    supplier.oi_check = move.move(move.ref_mod(image, 7, 1), _OI_SUPPLIER["oi_check"])


def _set_oi_net(oi: OiHeader, value: Decimal) -> None:
    """Store `oi-net` and carry `oi-approp` with it - they are one field.

    `05 OI-Approp redefines OI-Net pic s9(7)v99.` [copybooks/plwsoi.cob:L44] describes
    the SAME bytes as `05 OI-Net` [copybooks/plwsoi.cob:L43]. A COBOL store into one is
    visible through the other for free; two Python attributes are not, so the
    redefinition is honoured explicitly.
    """
    oi.filler_1.oi_net = value
    oi.filler_1.oi_approp = value


def _zz070_convert_date(st: _Pl055State) -> None:
    """`zz070-Convert-Date section.` [purchase/pl055.cbl:L599-L624]

    THE BODY IS DELEGATED, NOT RE-IMPLEMENTED. This section is byte-identical in all ten
    programs that carry it, which is the one place where consolidation is unambiguously
    safe because the bodies are textually equivalent.

    Args:
        st: The program's state.
    """
    system_data = st.ctx.system_record.system_data_block
    # 607-624, including the `Date-Form` default at L609-L610. GO TO class 3 - section
    # exit. `if Date-UK go to zz070-Exit.` [purchase/pl055.cbl:L611-L612] ->
    # `zz070-Exit.` [purchase/pl055.cbl:L626].
    system_data.date_form = zz070_convert_date(
        st.ws_date_formats, st.to_day, system_data.date_form
    )
    _zz070_exit()


def _zz070_exit() -> None:
    """`zz070-Exit.` / `exit section.` [purchase/pl055.cbl:L626-L627]

    The target of the two class-3 transfers at [purchase/pl055.cbl:L612] and
    [purchase/pl055.cbl:L617]. It carries nothing but the `exit section.` and is
    retained as a named function under rule R-5.
    """
    #  NO LOG RECORD. This paragraph displays NOTHING - [purchase/pl055.cbl:L626-L627] carries
    #  the `exit`/`goback` and no other statement - so an "entered/left the
    #  paragraph" event would be output the compiled program never produced.
    #  Rule R-4 forbids inventing observable output on a frozen silent path, and
    #  the function itself is what rule R-5 requires, not a trace of it.


def _a01_eval_status(st: _Pl055State) -> None:
    """`a01-Eval-Status section.` [purchase/pl055.cbl:L629-L632]

    Args:
        st: The program's state, whose `exception_msg` this fills.
    """
    st.exception_msg = move.move_figurative(
        move.SPACES, _ws("pic x(25)", "Exception-Msg", 126)
    )
    # 631-632 the FileStat-Msgs.cpy table, fs-reply -> exception-msg.
    st.exception_msg = move.move(
        _fs_reply_message(st.ctx.file_access.fs_reply),
        _ws("pic x(25)", "Exception-Msg", 126),
    )


def _fs_reply_message(fs_reply: int) -> str:
    """One `FileStat-Msgs.cpy` row - the text for a file status.

    `copybooks/FileStat-Msgs.cpy` is a flat `evaluate` over the status value. The
    statuses this program can actually see are the ones the data-access layer publishes,
    so the published enumeration names them rather than a transcription of the
    copybook's literals.
    """
    try:
        return FsReply(fs_reply).name.replace("_", " ").title()
    except ValueError:
        return f"Unmapped status {fs_reply}"


def run(
    ws_calling_data: WsCallingData,
    system_record: SystemRecord,
    system_record_4: SystemRecord4,
    to_day: str,
    file_defs: FileDefs,
    *,
    facade: ModuleType | None = None,
    file_access: FileAccess | None = None,
    acas_dal_common_data: AcasDalCommonData | None = None,
    ws_value_record: WsValueRecord | None = None,
    ws_analysis_record: WsAnalysisRecord | None = None,
    ws_pinvoice_record: WsPInvoiceRecord | None = None,
    invoice_header: IhInvoiceHeader | None = None,
    invoice_line: IlInvoiceLine | None = None,
    open_item_file_4: OpenItemWorkFile[OiHeader] | None = None,
) -> OpenItemWorkFile[OiHeader]:
    """Run `pl055`, the Purchase Invoice Post Extract.

    * `ws_calling_data` - read for `WS-Caller` at [purchase/pl055.cbl:L283] and
    [purchase/pl055.cbl:L428]; WRITTEN at [purchase/pl055.cbl:L286], which sets `WS-
    Term-Code` to 8 on the abort path. * `system_record` - read for `File-System-Used`
    at [purchase/pl055.cbl:L266]; WRITTEN at [purchase/pl055.cbl:L610], which defaults
    `Date-Form`.

    Args:
        ws_calling_data: `01 WS-Calling-Data.` [copybooks/wscall.cob:L6-L14].
        system_record: `01 System-Record.` [copybooks/wssystem.cob].
        system_record_4: `01 System-Record-4.` [copybooks/wssys4.cob:L8].
        to_day: `01 to-day pic x(10).` [purchase/pl055.cbl:L237], the run date as
            `DD/MM/CCYY`.
        file_defs: `01 File-Defs.` [copybooks/wsnames.cob:L13].
        facade: The entity-named data-access facade. `pl055` copies `Proc-ACAS-FH-
            Calls.cob` [purchase/pl055.cbl:L634], so it uses the ENTITY-named vocabulary
            and tests every reply inline.
        file_access: `01 File-Access.` [copybooks/wsfnctn.cob:L22]. Shared with the OTM4
            sequence, because `seloi4.cob:L4` declares `status fs-reply`.
        acas_dal_common_data: `01 ACAS-DAL-Common-data.` [copybooks/Test-Data-
            Flags.cob:L6].
        ws_value_record: `01 WS-Value-Record.` [copybooks/wsval.cob:L9].
        ws_analysis_record: `01 WS-Analysis-Record.` [copybooks/wsanal.cob:L9].
        ws_pinvoice_record: `01 WS-PInvoice-Record.` [copybooks/plwspinv2.cob:L10].
        invoice_header: `01 Invoice-Header redefines WS-PInvoice-Record.`
            [copybooks/plwspinv2.cob:L21].
        invoice_line: `01 Invoice-Line redefines WS-PInvoice-Record.`
            [copybooks/plwspinv2.cob:L56].
        open_item_file_4: The OTM4 extract sequence that `pl060` consumes - the
            SHARED `acas_posting.workfiles.OpenItemWorkFile`, not a private one.
            A caller sequencing the two programs passes ONE instance to both, and
            the route does exactly that. Defaults to a fresh, not-yet-existing
            file, which makes the `open extend` at [purchase/pl055.cbl:L301]
            report status 35 and the `open output` fallback at
            [purchase/pl055.cbl:L304] create it - the compiled program's own
            first-run path, and the one the maintainer describes at
            [purchase/pl055.cbl:L48].

    Returns:
        The OTM4 work file this program wrote - the one it was given, or the one
        it declared when given None. RETURNED because it IS the handoff: in COBOL
        the file survives the run unit and `pl060` reaches it by naming the same
        `assign file-28`, so the migrated equivalent has to hand the object back
        for the route to pass on. Nothing about the posting is communicated this
        way; the five linkage records carry that, by reference, as COBOL does.

    Raises:
        _CobolFilesModeUnsupportedError: If `FS-Cobol-Files-Used`
            [copybooks/wssystem.cob:L113] is true. Unreachable in the RDBMS
            configuration the migration targets.
    """
    if facade is None:
        # The Agent Action Plan's own import form, section 0.4.3. Resolved here rather
        # than at module scope because the module is generated later in this same batch.
        from acas_posting.dal import facade as imported_facade

        resolved_facade = _BoundFacade(imported_facade)
    else:
        resolved_facade = facade

    resolved_file_access = FileAccess() if file_access is None else file_access
    header = (
        _initial_pinvoice_view(IhInvoiceHeader)
        if invoice_header is None
        else invoice_header
    )

    ctx = _FacadeContext(
        system_record=system_record,
        ws_value_record=WsValueRecord() if ws_value_record is None else ws_value_record,
        ws_analysis_record=(
            WsAnalysisRecord() if ws_analysis_record is None else ws_analysis_record
        ),
        ws_pinvoice_record=(
            _initial_pinvoice_view(WsPInvoiceRecord)
            if ws_pinvoice_record is None
            else ws_pinvoice_record
        ),
        invoice_header=header,
        invoice_line=(
            _initial_pinvoice_view(IlInvoiceLine)
            if invoice_line is None
            else invoice_line
        ),
        file_access=resolved_file_access,
        file_defs=file_defs,
        acas_dal_common_data=(
            AcasDalCommonData()
            if acas_dal_common_data is None
            else acas_dal_common_data
        ),
    )

    st = _Pl055State(
        ctx=ctx,
        facade=resolved_facade,
        #  THE CHANNEL TO `pl060`. Declared here only when the caller passed
        #  none, and RETURNED either way, so the route can hand the very object
        #  this program wrote to the program that reads it - the same pattern
        #  `gl070.run` uses for the General Ledger work files.
        open_item_file_4=(
            open_item_work_file(OPEN_ITEM_4_NAME, OiHeader)
            if open_item_file_4 is None
            else open_item_file_4
        ),
        ws_calling_data=ws_calling_data,
        system_record_4=system_record_4,
        to_day=to_day,
        ws_date_formats=WsDateFormats(),
    )

    _mainline(st)

    #  THE CHANNEL IS RETURNED so that `pl060` reads what this program wrote. In
    #  COBOL the file survives the run unit and `pl060` names the same
    #  `assign file-28`; here the identity is this object.
    return st.open_item_file_4


# =============================================================================
# --- traceability ---
#
# Rule R-5 requires that every program map to a module, every paragraph to a
# function and every field to a data-dictionary entry, AND that the mapping be
# recorded rather than left implicit in the code. This footer is that record for
# `purchase/pl055.cbl`. It is deliberately exhaustive: the migration's only
# specification is a program nobody has re-tested since the compiler migration,
# so a reader who wants to know whether something was carried across must be
# able to find the answer here rather than by re-reading 635 lines of COBOL.
#
# PROGRAM -> MODULE
#   purchase/pl055.cbl  ->  acas_posting/programs/pl055_order_proof_extract.py
#   Boundary: THE WHOLE PROGRAM. Unlike `gl051` and `irs030`, which are migrated
#   in part, every section of `pl055` is in scope.
#
# -----------------------------------------------------------------------------
# 1.  SECTION AND PARAGRAPH -> FUNCTION
#
# Sixteen labels were measured in the procedure division. Agent Action Plan
# section 0.4.2 lists only the five section heads for this program and omits
# every paragraph, so the ten paragraphs plus `a01-Eval-Status` are a measured
# addition. Each label has its own function; the three `main-exit` labels are
# SECTION-QUALIFIED because paragraph names are not unique in this codebase.
#
#   COBOL label                    Line   Section            Python function
#   ---------------------------- ------ ------------------ ---------------------
#   mainline section.               246  mainline           _mainline
#   read-loop.                      306  mainline           _read_loop
#   header-analysis.                362  mainline           _header_analysis
#   close-files.                    400  mainline           _close_files
#   menu-exit.                      434  mainline           _menu_exit
#   create section.                 441  create             _create
#   Create-Main.                    444  create             _create__create_main
#   Create-Anal.                    488  create             _create__create_anal
#   main-exit.                      501  create             _create__main_exit
#   store-specials section.         503  store-specials     _store_specials
#   main-exit.                      536  store-specials     _store_specials__main_exit
#   extract section.                538  extract            _extract
#   main-exit.                      597  extract            _extract__main_exit
#   zz070-Convert-Date section.     599  zz070-Convert-Date _zz070_convert_date
#   zz070-Exit.                     626  zz070-Convert-Date _zz070_exit
#   a01-Eval-Status section.        629  a01-Eval-Status    _a01_eval_status
#
#   `create section.` [L441] and `Create-Main.` [L444] are two labels three
#   lines apart, and both are named by real transfers: `perform create` at
#   [L324] and [L511] names the SECTION, while the backward `go to create-Main`
#   at [L499] names the PARAGRAPH. They therefore get two functions, the first
#   of which carries no statements because the COBOL section head carries none.
#
#   Helper functions carry no COBOL label of their own. They exist because one
#   COBOL statement can need several Python ones - a two-receiver `MOVE`, a
#   group move into a nested dataclass, a byte image of a group item - and each
#   names in its docstring the statement it serves:
#     _by_name  _ws  _initialise_oi_header
#     _initial_pinvoice_view  _pinvoice_attributes  _move_into_va_group
#     _add_to_pair  _subtract_from_pair  _store_group  _caller_is_xl150
#     _va_code_image  _pa_code_image  _move_into_va_code  _move_into_pa_code
#     _group_move_analysis_into_value  _analysis_tail_image
#     _zero_the_six_value_totals  _ih_supplier_image  _move_into_oi_supplier
#     _set_oi_net  _fs_reply_message
#   Types: _CobolFilesModeUnsupportedError  _FacadeContext
#          _Pl055State.
#   Public API: `run` alone. `__all__ = ("run",)`, and every other module-level
#   name begins with an underscore, so a caller cannot reach into the program's
#   internals - exactly as a COBOL `CALL` cannot.
#
# -----------------------------------------------------------------------------
# 2.  `GO TO` CENSUS - NINETEEN SITES, CLASSIFIED BY SHAPE
#
# Classified by shape rather than by matching the Agent Action Plan's label
# list, which is not exhaustive for this program.
#
#   Class 1 - loop-back -> `continue` (7 sites)
#     L315  if il-analyised            go to read-loop     -> continue
#     L341  if va-second = space       go to read-loop     -> continue
#     L347  if FS-Reply = 21           go to read-loop     -> continue
#     L360  (unconditional, last stmt) go to read-loop     -> continue
#     L366  if ih-analyised and applied go to read-loop    -> return to caller
#     L372  after PInvoice-Rewrite     go to read-loop     -> return to caller
#     L398  (unconditional, last stmt) go to read-loop     -> return to caller
#     The last three are inside `header-analysis`, which the loop calls; a
#     `return` there lands on the `continue` at the class-4 site below, so the
#     effect is the same loop-back.
#
#   Class 2 - forward terminator -> `break` PLUS the post-loop block (1 site)
#     L309  if FS-Reply not = zero     go to close-files   -> break
#     Agent Action Plan section 0.6.3, verbatim: *"the target label is followed
#     by real work - closing files, printing totals, rewriting a control record
#     - so the transformation is `break` PLUS faithful placement of that work
#     after the loop, not `break` alone. Mis-splitting here would silently drop
#     end-of-run processing."* Here that work is the FOUR special-total stores
#     and the FOUR closes at [L403-L423]; dropping it would lose the entire
#     purchase value-analysis roll-up. And because [L308] leaves on ANY non-zero
#     status rather than only at end of file, this break is reached in more
#     circumstances than its sales counterpart - see divergence 4.
#
#   Class 3 - section or paragraph exit -> `return` (8 sites)
#     L457  if va-second = space       go to main-exit  [L501]
#     L468  after restoring WS-Pa-Code go to main-exit  [L501]
#     L480  if FS-Reply = 21           go to main-exit  [L501]
#     L486  (unconditional, last stmt) go to main-exit  [L501]
#     L528  if FS-Reply = 21           go to main-exit  [L536]
#     L545  if applied                 go to main-exit  [L597]
#     L612  if Date-UK                 go to zz070-Exit [L626]
#     L617  if Date-USA, after swap    go to zz070-Exit [L626]
#     The last two live in `dates.zz070_convert_date`, because that section is
#     textually identical in all ten carriers; they are annotated at the call
#     site so this census is complete for `pl055`.
#
#   Class 4 - sibling re-dispatch -> named call plus an explicit transfer
#             (3 sites, each with its own equivalence proof)
#     L312  if ih-test = zero  go to header-analysis  [L362]
#           PROOF: every path through `header-analysis` ends in `go to
#           read-loop` - at [L366], at [L372] and at [L398], the paragraph's
#           last statement - so the paragraph has no fall-through and no other
#           exit. A call followed by an unconditional `continue` visits the same
#           statements in the same order. Note the sales program reaches its
#           header block by `exit perform` and FALL-THROUGH
#           [sales/sl055.cbl:L371, L426]; this one names the target.
#     L450  if FS-Reply = 21 or = 23  go to Create-Anal  [L488]
#           PROOF: `Create-Anal` has exactly one exit, the unconditional `go to
#           create-Main` at its last line [L499], and contains no other
#           transfer. So the transfer pair is a retry loop and nothing else.
#     L499  (unconditional, last stmt) go to create-Main  [L444]
#           A BACKWARD transfer to the section's FIRST paragraph - the only
#           genuine cross-paragraph retry in the program. PROOF: combined with
#           the L450 proof above, the pair is exactly `while True:` around
#           `Create-Main`'s statements with a call to `Create-Anal` followed by
#           `continue`. Termination is NOT guaranteed by the COBOL and no guard
#           is added - see AMBIGUITY Q-PL055-2.
#
#   Plain `EXIT`, not `EXIT SECTION` (1 site, not a `GO TO`)
#     L597  main-exit.   exit.        -> `_extract__main_exit`
#     `EXIT` on its own is a no-op that documents an exit point; `create` [L501]
#     and `store-specials` [L536] both write `exit section.` instead. Divergence
#     18, preserved.
#
#   `PERFORM ... THRU` DOES NOT OCCUR IN `pl055`. The four in-scope sites
#   repository-wide are [general/gl072.cbl:L300], [general/gl072.cbl:L304],
#   [sales/sl100.cbl:L344] and [purchase/pl100.cbl:L336].
#
# -----------------------------------------------------------------------------
# 3.  FALL-THROUGH
#
#   `mainline` [L246-L304] has no terminating `exit section.`, so control
#   arrives at `read-loop.` [L306] by falling through. Represented by the call
#   to `_read_loop` at the end of `_mainline`.
#
#   `close-files` [L400-L432] falls through into `menu-exit.` [L434] whenever
#   `Anal-Created` is zero - the conditional `goback` at [L432] is taken only
#   when an emergency analysis record was written. Represented by the call to
#   `_menu_exit` after the conditional return in `_close_files`.
#
#   `create section.` [L441] falls through into `Create-Main.` [L444], the
#   section head carrying no statements. Represented by `_create` calling
#   `_create__create_main`.

#
# -----------------------------------------------------------------------------
# 4.  DIVERGENCES FROM `sales/sl055.cbl` - EIGHTEEN, ALL PRESERVED
#
# ⛔⛔ `pl055` IS NOT A MIRROR OF `sl055`. The Agent Action Plan describes it as
# the "Purchase mirror of `sl055`"; measured against the two sources that is
# WRONG. The two programs diverge in eighteen places, at least eight of them
# behaviourally significant and directly visible in a table dump. This module
# was transcribed from `purchase/pl055.cbl` alone. `sl055` is cited below and in
# the comments ONLY as the contrast that makes each divergence visible - there
# is no import of and no call into `sl055_invoice_extract_analysis`, which would
# be both a layering violation and the single most likely way to destroy these
# eighteen facts.
#
#   #   Subject                     sl055                     pl055
#  --- --------------------------- ------------------------- --------------------
#   1   negation-block width        NINE fields               ⭐ FOUR fields
#       [sales/sl055.cbl:L658-L666] vs [purchase/pl055.cbl:L571-L575]
#       `oi-net`, `oi-carriage`, `oi-vat`, `oi-c-vat` only. `oi-deduct-amt` IS
#       moved at [purchase/pl055.cbl:L564] and is NOT negated, where the sales
#       program negates it first [sales/sl055.cbl:L658]. Diff-visible in every
#       credit-note row of the OTM4 sequence that `pl060` then consumes.
#
#   2   invoice-total addends       NINE addends              ⭐ FOUR addends
#       [sales/sl055.cbl:L671-L673] vs [purchase/pl055.cbl:L580]
#       `ih-net ih-carriage ih-vat ih-c-vat` giving `ws-inv-amt`. Diff-visible
#       in `SYSTOT-REC` through the two period totals.
#
#   3   main-loop control structure inline PERFORM UNTIL      ⭐ a `GO TO` loop
#       [sales/sl055.cbl:L365-L424] vs [purchase/pl055.cbl:L306-L360]
#       The maintainer modernised the sales extract - its own note reads
#       *"changed 18/01/25 for clean up using inline perform"* - and never came
#       back to this one. Structural, not behavioural, but it is why the class-1
#       and class-2 census above has seven and one entries here and none there.
#
#   4   loop-exit condition         `if fs-reply = 10`        ⭐⭐ `not = zero`
#       [sales/sl055.cbl:L367] vs [purchase/pl055.cbl:L308]
#       BEHAVIOURAL. The sales program leaves the walk only at end of file;
#       `pl055` leaves it on ANY non-zero status. In a scenario where a read
#       fails mid-walk the two programs write different amounts of data.
#
#   5   `INITIALIZE`                `with filler`             ⭐⭐ no `with filler`
#       [sales/sl055.cbl:L635] vs [purchase/pl055.cbl:L547]
#       BEHAVIOURAL, and a British spelling into the bargain - `initialise`.
#       Without `WITH FILLER`, `FILLER` items are not reset and retain their
#       previous contents, which is directly visible in the written record. See
#       AMBIGUITY Q-PL055-1 and the note in `_initialise_oi_header`.
#
#   6   case of a STORED flag       upper `"Z"`               ⭐⭐ lower `"z"`
#       [sales/sl055.cbl:L421, L468] vs [purchase/pl055.cbl:L358, L396]
#       BEHAVIOURAL AND DIFF-VISIBLE: `il-update` in `PUINV-LINES-REC` and
#       `ih-update` in `PUINVOICE-REC` are stored columns, and the case differs.
#       The sales program even documents its own change - *"Analysied flag
#       changed from z (1/6/13)"* - and `pl055` was left behind. The `88`-level
#       [copybooks/plwspinv2.cob:L53, L72] accepts both cases, which is why the
#       program still recognises its own flag and the defect stays invisible at
#       run time.
#
#   7   skip-invoice path           a whole apparatus         ⭐⭐ NONE OF IT
#       [sales/sl055.cbl:L430, L433-L434, L472-L479] vs nothing in `pl055`
#       BEHAVIOURAL. No `da030-Skip-Invoice` paragraph, no `Invoice-Start`, no
#       `set fn-not-less-than`, no proforma filter, no pending/status filter and
#       no `ws-p-flag`. `header-analysis` [L362] goes straight from [L365-L366]
#       to `perform extract` [L368], so a purchase proforma IS extracted and IS
#       counted. See the note at the top of `_header_analysis`.
#
#   8   header-analysis sign flips  THREE                     ⭐ TWO
#       [sales/sl055.cbl:L446, L457, L463] vs [purchase/pl055.cbl:L376, L387]
#       BEHAVIOURAL for the discount total: the discount block
#       [purchase/pl055.cbl:L391-L394] has no `if ih-type = 3 multiply -1`.
#       Mechanically consistent with `03 ih-deduct-amt pic 999v99 comp.`
#       [copybooks/plwspinv2.cob:L46] being UNSIGNED, which cannot hold a
#       negative in the first place - recorded as evidence, not as a licence.
#
#   9   VAT total addends           THREE                     ⭐ TWO
#       [sales/sl055.cbl:L444] vs [purchase/pl055.cbl:L374]
#       BEHAVIOURAL. `ih-e-vat` [copybooks/plwspinv2.cob:L38] exists in the
#       purchase header and is simply not summed.
#
#  10   paragraph naming            `da`/`db`/`dc`/`dd`       ⭐ UNPREFIXED
#       [sales/sl055.cbl:L305, L364] vs [purchase/pl055.cbl:L306, L362, ...]
#       Structural. The Python functions carry the COBOL's own unprefixed names,
#       section-qualified only where a name is not unique.
#
#  11   the Value-file open         an existence probe        ⭐ just an open
#       [sales/sl055.cbl:L319-L324] vs [purchase/pl055.cbl:L261]
#       BEHAVIOURAL on a missing file: the sales program probes with
#       `Value-Open-Input`, conditionally closes and re-opens for output, then
#       unconditionally closes; `pl055` performs `Value-Open` with NO reply test
#       and does it a SECOND time at [purchase/pl055.cbl:L299]. A failed open is
#       therefore not noticed until the first read.
#
#  12   `ih-status-A`               set as well               ⭐ NOT set
#       [sales/sl055.cbl:L679-L680] vs [purchase/pl055.cbl:L586]
#       BEHAVIOURAL AND DIFF-VISIBLE: only `ih-status` is stamped. Corroborated
#       from the copybook side - `ih-status-A` DOES NOT EXIST in
#       `copybooks/plwspinv2.cob` at all, so there is no field to set. Note the
#       program's own internal inconsistency: `ih-status` takes UPPER-case `"Z"`
#       here while `ih-update` and `il-update` take LOWER-case `"z"` at [L396]
#       and [L358], and the maintainer's own comment at [L586] reads
#       *"07/01/18 was "z""*.
#
#  13   the write target            `oi-header` (WS)          ⭐ `open-item-record-4`
#       [sales/sl055.cbl:L681] vs [purchase/pl055.cbl:L587]
#       COSMETIC IN `pl055`, and the resolution is structural - see STRUCTURAL
#       NOTES below and AMBIGUITY Q-PL055-5.
#
#  14   `a01-Eval-Status` exit      `a01-exit.`               ⭐ NO exit paragraph
#       [sales/sl055.cbl:L729] vs [purchase/pl055.cbl:L629-L632]
#       Structural. The section ends at the `copy` and the following `copy
#       "Proc-ACAS-FH-Calls.cob"` [L634] terminates it.
#
#  15   accumulation verb count     four single-receiver      ⭐ two two-receiver
#       [sales/sl055.cbl:L391-L395] vs [purchase/pl055.cbl:L330, L332]
#       `add il-net to va-v-this va-v-year` and `subtract il-net from va-v-this
#       va-v-year`. Each receiver converts INDEPENDENTLY under its own
#       description, which is why `_add_to_pair` and `_subtract_from_pair` call
#       the primitive twice rather than computing once and assigning twice.
#
#  16   `il-product (1:1) = "/"`    present                   ⭐ absent
#       [sales/sl055.cbl:L376] vs nothing in `pl055`
#       BEHAVIOURAL. A purchase line whose product code opens with a comment
#       marker IS analysed and DOES contribute to `VALUEANAL-REC`.
#
#  17   value-analysis groups       `vo` `vp` `zc` `zd`       ⭐ `vi` `vj` `za` `zb`
#       [sales/sl055.cbl] vs [purchase/pl055.cbl:L404, L408, L412, L416]
#       and `va-system` set EXPLICITLY by `move "P" to va-system` at
#       [purchase/pl055.cbl:L403], where the sales program sets it implicitly by
#       moving a three-character literal such as `"Svo"` into `va-code`.
#       `pl060`'s deduction analysis later targets the `"zb"` group, the
#       purchase analogue of `sl060`'s `"Szd"`.
#
#  18   `extract` terminator        `exit section.`           ⭐ plain `exit.`
#       [sales/sl055.cbl] vs [purchase/pl055.cbl:L597]
#       Cosmetic, and inconsistent within `pl055` itself: `create` [L501] and
#       `store-specials` [L536] both write `exit section.`
#
# FURTHER DIVERGENCES AND INCONSISTENCIES RECORDED IN THE CODE, not numbered
# above because they are internal to `pl055` rather than contrasts with `sl055`:
#   * `= 21` alone at [L323], [L346], [L510] and [L527] against `= 21 or = 23`
#     at [L449] - the only site testing both. The data-access layer records that
#     `FS-Reply` 23 is documented but never actually returned, so the `or = 23`
#     arm is dead in practice; ⛔ it is not removed for that.
#   * The unguarded backward retry at [L499] - AMBIGUITY Q-PL055-2.
#   * `Create-Main.` declared mixed-case at [L444] and spelled `create-Main` at
#     the `GO TO` [L499]. COBOL is case-insensitive; `sl055` has the identical
#     quirk [sales/sl055.cbl:L530, L585].
#   * `end-if.` at [L338] - a period AFTER `end-if`, closing a construct whose
#     `if` at [L334] already ends at [L337]'s period. Harmless.
#   * The extra `move 1 to File-Key-No` at [L355], between the accumulation and
#     the `Value-Rewrite`, which the first accumulation block does not have at
#     the equivalent point.
#   * `call "sl070"` at [L273] - the SALES program called from a PURCHASE
#     module, not `pl070`. `sl070` creates the shared Analysis and Value files,
#     so it is probably deliberate; `sl055` makes the identical call
#     [sales/sl055.cbl:L332]. ⛔ Not "corrected" to `pl070`.
#   * The `va-code` left blanked by the [L467-L468] exit of `Create-Main` - a
#     latent defect recorded at that site, reproduced per R-4.
#   * Missing terminating periods at [L470] and [L482] where [L452] has one.
#   * [L547] carries one extra leading space relative to its neighbours.
#   * `01 ws-Test-Date pic x(10).` [L181], `01 error-code pic 999.` [L227] and
#     `03 ws-Conv-Date pic x(10).` [L184] are declared and NEVER referenced.
#
# SHARED LEGACY DEFECTS - PRESENT IDENTICALLY IN `sl055`, SO NOT DIVERGENCES.
# Both were found by RUNNING this module and tracing its verb order, then
# confirmed against the sales source line by line. Both are reproduced per R-4
# and both are locked in place by the ad-hoc walk, so that a later "tidy-up"
# fails rather than passing unnoticed.
#
#   FINDING A - THE ROLL-UP `Value-Write` AT [L474] IS UNCONDITIONAL AND
#   UNTESTED, SO IT ISSUES A DUPLICATE INSERT ON ESSENTIALLY EVERY RUN AND
#   SWALLOWS THE FAILURE.
#     `Create-Main` blanks the second character of the key [L461], group-moves
#     the analysis record over the value record [L470], zeroes all six totals
#     [L471-L472] and then writes UNCONDITIONALLY [L474] - with no `v-exists`
#     test, unlike the two structurally identical sites at [L334-L337] and
#     [L519-L522] - and never inspects the reply. When the roll-up row does not
#     yet exist this is the intended materialisation. When it does, the handler
#     `ba070_process_write` in `acas_posting.dal.acas013_value` issues
#     `INSERT INTO `VALUEANAL-REC` SET ...`, hits the duplicate key, sets
#     `FS-Reply` 22 and LEAVES THE STORED ROW UNTOUCHED - reproducing
#     [common/valueMT.cbl:L817-L831]. ⛔ The accumulated totals are therefore NOT
#     lost; this is not a lost update. The two real effects are a duplicate
#     INSERT - guaranteed by `close-files` [L403-L419], where `vi`/`vj` share the
#     roll-up `Pv ` and `za`/`zb` share `Pz ` - and a stale `FS-Reply` 22 on
#     return, inert only because the next read at [L345] or [L526] assigns over
#     it. Measured for one type-3 header against an empty table: duplicate writes
#     for `Pv ` and `Pz `, with `Pv ` holding (1, -11.00) and `Pz ` (2, -1.00).
#     `sl055` writes unconditionally at the same point,
#     `perform Value-Write.` [sales/sl055.cbl:L560], after the same blank-key
#     [sales/sl055.cbl:L547] and zeroing sequence, restoring `va-code` only
#     afterwards [sales/sl055.cbl:L562]. Recorded at its site in
#     `_create__create_main`. DO NOT FIX - guarding the write would remove a
#     statement the COBOL issues against the database, and testing the reply
#     would add a control transfer the COBOL does not have (R-3).
#
#   FINDING B - A SINGLE-CHARACTER ANALYSIS GROUP IS ACCUMULATED BUT NEVER
#   STAMPED, SO IT IS RE-ANALYSED AND DOUBLE-COUNTED ON EVERY LATER RUN.
#     `if va-second = space go to read-loop.` [L340-L341] correctly skips the
#     inapplicable second half of the twice-over accumulation, but because it
#     targets `read-loop` rather than the loop tail it ALSO skips
#     `move "z" to il-update` [L358] and `perform PInvoice-Rewrite` [L359]. The
#     line has already been committed into `VALUEANAL-REC` by [L327-L337], yet
#     `il-analyised` [copybooks/plwspinv2.cob:L69] still reads FALSE, so the
#     next run accumulates the same line again. Measured: for `il-pa = "v "` the
#     value rows are written and rewritten and `PInvoice-Rewrite` is never called
#     at all. `sl055` has the identical ordering -
#     `if va-second = space exit perform cycle` [sales/sl055.cbl:L402-L404]
#     before `move "Z" to il-update` [sales/sl055.cbl:L421] and
#     `perform Invoice-Rewrite` [sales/sl055.cbl:L422]. Only the STAMPED case
#     differs between the programs, and that is DIVERGENCE 6. Recorded at its
#     site in `_read_loop`. DO NOT FIX - issuing the stamp would set a stored
#     `PUINV-LINES-REC` column the COBOL leaves blank.
#
# THE TWICE-OVER BLOCKS ARE NOT FACTORED, DELIBERATELY. [L327-L337] against
# [L349-L356], and [L514-L522] against [L530-L534], each look like one helper
# called twice and are not: the first of each pair branches on `v-exists` to
# choose `Write` or `Rewrite` and the second always `Rewrite`s, and the first
# pair's second half carries the extra [L355]. Agent Action Plan section 0.6.1,
# verbatim: *"Normalising them into one helper would be the single easiest way
# to fail this migration."*

#
# -----------------------------------------------------------------------------
# 5.  STRUCTURAL NOTES
#
# 5.1  THE OTM4 WORK FILE, AND WHY IT LIVES IN `acas_posting.workfiles`
#
#   `open-item-file-4` is the purchase temp extract: `copy "seloi4.cob"` [L109]
#   carries its author's own note *"Temp file only for i/p to pl060"*, `copy
#   "fdoi4.cob"` [L120] gives it `01 open-item-record-4 pic x(113)`, and
#   `file-28` is `"openitm4.dat"` [copybooks/file28.cob:L1]. It reaches NO
#   schema table and appears in NO table dump; `pl060` consumes it
#   [purchase/pl060.cbl:L421-L425].
#
#   It is modelled the way the Agent Action Plan models the General Ledger work
#   files - an ordered in-process sequence with the same record layout and the
#   same ordering guarantee - by the SHARED `acas_posting.workfiles`
#   `OpenItemWorkFile`, which serves both open-item files and both sides of each:
#     `open extend`  [L301]  -> positions at the end, existing records survive
#     `open output`  [L304]  -> truncates, which is what makes the fallback a
#                               create
#     `write`        [L587]  -> appends, in insertion order, a SNAPSHOT
#     `close`        [L423]  -> a no-op on the records; they are the deliverable
#     `read_next`            -> what `pl060` uses [purchase/pl060.cbl:L425]
#   IT WAS ONCE DECLARED HERE, module-privately, because `OpenMode` had no
#   `EXTEND` member. The observation was true and the conclusion was wrong: a work
#   file the producer and the consumer declare separately is not a channel, so
#   `pl060` could never read what this program wrote. `OpenMode.EXTEND` is now
#   published and the file is declared ONCE. `run` returns the carrier so the
#   route can hand it to `pl060`, which is what naming the same `assign file-28`
#   does in COBOL.
#
#   WHY `OpenItemWorkFile` RATHER THAN `workfiles.LineSequentialWorkFile`. The
#   General Ledger class has no `open_extend`; its `OpenMode` vocabulary is
#   `CLOSED`/`INPUT`/`OUTPUT`, and its only route into a writable state is
#   `open_output`, which truncates. Its record list, open mode, read pointer and
#   status field are all private, so adding an extend by reaching into them would
#   be a layering violation dressed up as reuse. The answer was to publish a
#   SECOND carrier beside it, in the same module and over the same status
#   vocabulary - `OpenItemWorkFile`, whose `OpenMode.EXTEND` and raw file statuses
#   `FS_REPLY_OPEN_NOT_FOUND` and `FS_REPLY_WRITE_NOT_OPEN` are declared there
#   once. No parallel vocabulary is invented beside the published one.
#
#   AND NO NEW FILE WAS CREATED. `acas_posting/programs/` is closed at exactly
#   thirteen files - `__init__.py` plus the twelve program modules - per Agent
#   Action Plan sections 0.4.1.2 and 0.4.4, and `acas_posting/workfiles.py` is
#   an existing individually-named in-scope module (sections 0.3.1, 0.4.1.6).
#
#   The status field is shared with the data-access layer DELIBERATELY:
#   `seloi4.cob:L4` declares `status fs-reply`, and `Fs-Reply`
#   [copybooks/wsfnctn.cob:L25] is the very field every facade verb also writes.
#   That sharing is what lets [L302] and [L588] test `fs-reply` straight after a
#   native `OPEN` and `WRITE`.
#
# 5.2  `OI-Header` AGAINST `open-item-record-4` - DIVERGENCE 13, RESOLVED
#
#   [L547] initialises `OI-Header` and [L587] writes `open-item-record-4`, which
#   reads at first glance as a write of an area nothing filled. It is not. In
#   `pl055` BOTH `copy "fdoi4.cob"` [L120] and `copy "plwsoi.cob"` [L121] sit
#   inside the FILE SECTION under one FD, so `01 open-item-record-4 pic x(113)`
#   and `01 OI-Header` are two `01` DESCRIPTIONS OF THE SAME 113-BYTE RECORD
#   AREA - a second `01` under an FD is an alternative description, not a second
#   buffer - and `OI-Header`'s fields sum to exactly 113. The divergence is
#   therefore COSMETIC here, and `OpenItemWorkFile` models the one area.
#
#   `pl060` proves the contrast: it copies `plwsoi.cob` into WORKING-STORAGE
#   [purchase/pl060.cbl:L152] and consequently needs an explicit `move
#   open-item-record-4 to oi-header` [purchase/pl060.cbl:L428] that `pl055` has
#   no counterpart to. What remains for the oracle is recorded as AMBIGUITY
#   Q-PL055-5.
#
# 5.3  THE `OI-Header` LAYOUT IS PUBLISHED, NOT DECLARED HERE
#
#   `copybooks/plwsoi.cob` has no `records/` module of its own in Agent Action
#   Plan section 0.3.1's list, which suggested a module-private declaration would
#   be needed. It is not: `acas_posting/records/otm5.py` already publishes
#   `OiHeader` with its subordinate groups `OiKey`, `OiBatch`, `OiCustomer`,
#   `OiSupplier` and `Filler1`, and `otm5.descriptors_of()` supplies a descriptor
#   for every field WITH a dictionary key. So every field of the record this
#   module writes is traceable to a dictionary entry, and no layout was invented.
#   (`field.descriptors_for_copybook_record("OI-Header")` is NOT used: it is
#   ambiguous, returning 69 descriptors that mix the purchase `PUITM5-REC` and
#   the sales `SAITM3-REC` views of the same copybook name.)
#
# 5.4  `WITH FILLER` HAS NO ELEMENTARY TARGET IN THIS COPYBOOK
#
#   `copybooks/plwsoi.cob` contains exactly one `FILLER`, the GROUP item at
#   [copybooks/plwsoi.cob:L41] whose ten subordinates are ALL named. So the
#   omitted `WITH FILLER` at [L547] cannot be observed by watching a named field
#   - it can only be observed in bytes the group description does not name, and
#   whether any such bytes exist is the oracle question Q-PL055-1.
#   `_initialise_oi_header` therefore initialises the seventeen top-level fields
#   under their own descriptors and NOTHING ELSE, which is the closest faithful
#   reading of `initialise` without `WITH FILLER`.
#
# 5.5  FIELD DESCRIPTORS AND THEIR PROVENANCE
#
#   Every descriptor this module uses is either looked up from the generated
#   dictionary - `_VAL`, `_ANL`, `_S4`, the five `_OI*` dicts, and
#   `pinvoice_descriptor_for` - and therefore carries a `dictionary_key`, or is
#   built by `_ws()` from the program's OWN working storage and therefore carries
#   a `source_locator` of the form `purchase/pl055.cbl:L<n>`. FOURTEEN `_D_*`
#   descriptors are the second kind: `Anal-Created` [L163], `save-code` [L164],
#   `ws-inv-amt` [L165], `work-2` [L166], `work-3` [L167], the four money totals
#   [L168-L171], the four counts [L172-L175] and `v-exists` [L176]. A fifteenth
#   `_ws()` descriptor, `Exception-Msg` [L126], is built inline in
#   `_a01_eval_status` rather than at module scope because nothing else needs it.
#   `_D_TERM_CODE` is the FIRST kind - it comes from
#   `calling_data_descriptor_for("ws_term_code")`, so its provenance is the
#   dictionary entry for `WS-Term-Code` [copybooks/wscall.cob:L10] rather than a
#   locator written here.
#
#   VERIFIED BY INTROSPECTION, not by reading: 97 `FieldDescriptor` objects are
#   reachable from this module's namespace; 83 carry a `dictionary_key`, 14 carry
#   a `source_locator` matching `^[A-Za-z0-9_./-]+:L[0-9]+(-L[0-9]+)?$`, and NONE
#   carries neither. No descriptor is constructed without one or the other.
#
# 5.6  THE FACADE IS INJECTED, NOT IMPORTED AT MODULE SCOPE
#
#   `pl055` copies `Proc-ACAS-FH-Calls.cob` [L634], so it uses the ENTITY-named
#   verb vocabulary and TESTS THE REPLY INLINE - that copybook has no
#   per-handler error-check paragraph at all, unlike the IRS convention. The
#   thirteen distinct verbs this module calls are `PInvoice-Open` [L298],
#   `PInvoice-Read-Next` [L307], `PInvoice-Rewrite` [L359, L371, L397],
#   `PInvoice-Close` [L420], `Value-Open` [L261, L299], `Value-Read-Indexed`
#   [L322, L345, L509, L526], `Value-Write` [L335, L474, L520], `Value-Rewrite`
#   [L337, L356, L522, L534], `Value-Close` [L421], `Analysis-Open` [L300],
#   `Analysis-Read-Indexed` [L448, L465, L478], `Analysis-Write` [L494, L497]
#   and `Analysis-Close` [L422]. ⛔ No handler-named alias
#   (`acas013_*`/`acas015_*`/`acas026_*`) is called.
#
#   `acas_posting/dal/facade.py` is generated in this same batch and does not
#   exist while this module is written, so it is resolved lazily inside `run`
#   and can be substituted by a caller. See AMBIGUITY Q-PL055-7 and Q-PL055-8.
#
#   ALL TEN `move 1 to File-Key-No` STATEMENTS ARE PRESERVED IN PLACE - [L291],
#   [L321], [L344], [L355], [L447], [L464], [L477], [L493], [L508] and [L525] -
#   and so are BOTH `Value-Open` calls, neither with a reply test. They look
#   cacheable and are not cached: Agent Action Plan section 0.8.4, verbatim,
#   *"Any performance work is therefore out of scope by construction, not merely
#   unrequested."*
#
# -----------------------------------------------------------------------------
# 6.  CITATION CORRECTIONS - FOUR MEASURED FACTS THAT OVERTURN THE PLAN
#
# Recorded because a downstream reader working from the Agent Action Plan alone
# would otherwise be misled. Each was measured against the frozen source.
#
# 6.1  `pl055` DOES HAVE A FACADE STUB BLOCK.
#   The plan states this program has "NO facade stub block (unlike gl072
#   L135-L155 and gl080 L194-L214)". It does: `01
#   Dummies-4-Unused-ACAS-FH-Calls.` at [purchase/pl055.cbl:L139-L159], carrying
#   the comment *"Call blk at zz080-ACAS-Calls"*. What makes it look absent is
#   that FOUR of its members are COMMENTED OUT - `System-Record-4` [L142],
#   `WS-Value-Record` [L150], `WS-Analysis-Record` [L152] and
#   `WS-PInvoice-Record` [L158] - precisely because those four are real records
#   in this program rather than stubs. Like `gl072`'s block it maps to NOTHING
#   in Python, which has no linker to satisfy; recorded here as a
#   representation-only omission so that a reader diffing the two files does not
#   conclude something was lost.
#
# 6.2  THE `extract` SECTION COMMENT PROMISES A FILTER THAT DOES NOT EXIST.
#   [purchase/pl055.cbl:L541-L542] reads *"only Process header records, drop
#   pro-formas"* and *"ignore records which have already been copied"*. Only the
#   second is implemented, by `if applied` [L544]. There is NO `ih-type = 4`
#   proforma test anywhere in `pl055` - see divergence 7. The comment is the
#   maintainer's intent; the code is the specification.
#
# 6.3  ⛔ THE PURCHASE TERM-CODE GATE EXISTS, AND THE PLAN'S CONCLUSION IS WRONG.
#   The plan observes correctly that `load08.` [purchase/purchase.cbl:L752-L762]
#   has NO inline gate - its would-be gate lines are commented out at
#   [purchase/purchase.cbl:L755-L758] - and concludes that `move 8 to
#   WS-Term-Code` [purchase/pl055.cbl:L286] "has no gating effect on `pl060`".
#   MEASURED, IT DOES. The shared dispatch paragraph `load000.`
#   [purchase/purchase.cbl:L691] gates for every loader:
#       if       ws-term-code < 8   perform overrewrite.   [L702-L703]
#       if       ws-term-code > 7   go to overrewrite.     [L704-L705]
#   With term code 8, [L702] is false and [L704] is TRUE, so `go to overrewrite`
#   transfers OUT of the `perform load000.` range at
#   [purchase/purchase.cbl:L760]. A `GO TO` escaping a `PERFORM` range never
#   returns, so control reaches `overrewrite.` [purchase/purchase.cbl:L621],
#   falls through to `overclose.` [L652] and `goback.` [L653], and
#   `purchase.cbl` TERMINATES. `pl060` IS NEVER CALLED.
#   The three gate predicates must still NOT be unified - General tests `= 5`
#   [general/general.cbl:L810-L811], Sales `not = zero`
#   [sales/sales.cbl:L759-L768] and Purchase `> 7`
#   [purchase/purchase.cbl:L704].
#   SECOND-ORDER CONSEQUENCE, AND IT SHAPES THIS MODULE. `overrewrite.`
#   [purchase/purchase.cbl:L621-L651] is what PERSISTS the period totals: it
#   moves `WS-System-Record-4` into `System-Record` and rewrites under
#   `File-Key-No` 4, for both the RDB and the Cobol parameter file. So the two
#   period-total adds at [purchase/pl055.cbl:L582, L584] are written to
#   `SYSTOT-REC` BY THE MENU, not by `pl055`. This module therefore mutates
#   `system_record_4` in place and does NOT persist it - persisting it here
#   would double-write on the normal path and would write on the abort path,
#   where the COBOL does not.
#
# 6.4  `copybooks/wscall.cob`'s SEVEN-FIELD SPAN IS L6-L14, NOT L6-L13.
#   The plan cites [copybooks/wscall.cob:L6-L13]; measured, the seventh field
#   `WS-CD-Args pic x(13)` is at [copybooks/wscall.cob:L14]. The published
#   `records/calling_data.py` already records the correct span. Also note
#   [copybooks/wscall.cob:L4], *"14/11/25 vbc - 1.02 - Chg WS-Term-Code from 9
#   to 99"* - `WS-Term-Code` is `pic 99` [copybooks/wscall.cob:L10], which is
#   why the value 8 is stored through a descriptor rather than assigned raw.

#
# -----------------------------------------------------------------------------
# 7.  OMISSIONS - WHAT WAS DELIBERATELY NOT CARRIED ACROSS
#
# Agent Action Plan section 0.4.3 and rule R-5 require that deliberate omissions
# be recorded AS omissions, *"so that a reader comparing the two files does not
# conclude something was lost."* This is the complete list for `pl055`.
#
# 7.1  THE `if FS-Cobol-Files-Used` BLOCK BODY  [L266-L290]
#   The GATE is reproduced, data-driven through the condition name over `07
#   File-System-Used pic 9.` [copybooks/wssystem.cob:L112], so the decision is
#   made at run time exactly as the COBOL makes it. The BODY is not: it needs
#   `call "CBL_CHECK_FILE_EXIST"` [L267-L269, L278-L279] and `call "sl070"`
#   [L273-L277]. `sl070` is not one of the twelve in-scope programs - Agent
#   Action Plan section 0.2.2 - so there is no Python module to call, and rule
#   R-1 forbids invoking the COBOL. Inside the gate the module therefore RAISES
#   `_CobolFilesModeUnsupportedError`, an explicitly typed error whose message
#   states all four facts. ⛔ NOT silently skipped and NOT stubbed as a no-op: a
#   silent skip would make a genuinely divergent configuration look like a clean
#   run. The observable consequences of the COBOL's own abort path ARE preserved
#   - `move 8 to WS-Term-Code` [L286] happens BEFORE the raise, and the `goback`
#   [L287] is the raise itself. See AMBIGUITY Q-PL055-6.
#
# 7.2  `display ... at` OUTPUT -> LOG RECORDS, BUT NOT ALL OF IT
#   Agent Action Plan section 0.3.4 converts a DIAGNOSTIC display, and requires
#   that it *"must not alter control flow and must not appear in any table
#   dump."* Neither does any record this module emits. What is converted:
#   [L293-L294] the program banner and the "Invoice Post Extract" title;
#   [L426-L427] the two emergency-analysis warnings; [L590-L592] the OTM4
#   write-failure message, its file status and the decoded status name.
#
#   WHAT IS NOT CONVERTED, AND WHY:
#     * [L282], [L429], [L593] - `PL003`/`PL006`, pure acknowledgement prompts.
#       Dropped with the `accept` each introduces; see 7.3 and the note on the
#       `01 Error-Messages.` block.
#     * [L281] - `PL203`, inside the unreachable `sl070` block; see the same note.
#     * [L296] - `display ws-date`. The posting date is business data, which the
#       safe-event schema in `acas_posting/dal/status.py` excludes from a record
#       (CWE-532); it is a command-line INPUT and `clock.py` pins it.
#     * Every `move ... to print-record`/`l?-...` field. Report formatting is out
#       of scope per section 0.2.2, and section 0.3.4 converts a DISPLAY, not a
#       report line.
#     * The five paragraph exits [L434, L501, L536, L597, L626]. Each carries the
#       `exit`/`goback` and nothing else, so there is nothing to convert; an
#       "entered/left" trace would be output the compiled program never produced,
#       which R-4 forbids inventing.
#
# 7.3  `accept WS-Reply`  [L284], [L430], [L594]  -> DROPPED
#   Acknowledgement pauses whose only effect is to block a terminal. BUT the
#   `if WS-Caller not = "xl150"` branches around [L284] and [L430] ARE
#   PRESERVED - that test is the codebase's own unattended-mode check, and when
#   the out-of-scope `xl150` driver is the caller the COBOL skips the accept
#   itself. And both `goback`s ARE PRESERVED: [L287] and [L432].
#
# 7.4  TERMINAL GEOMETRY  [L249-L255]
#   `accept ws-env-lines from lines`, the companion `from columns`, and the
#   arithmetic `subtract 1 from ws-lines giving ws-23-lines`. A TERMINAL-SIZE
#   READ, NOT A CLOCK READ - it feeds only screen positioning, which is out of
#   scope. `ws-lines`, `ws-23-lines` and `ws-env-lines` are consequently not
#   modelled. Rule R-6 is unaffected: `purchase/pl055.cbl` contains ZERO clock
#   reads and the date arrives entirely through the `to-day` operand.
#
# 7.5  REPRESENTATION-ONLY DECLARATIONS
#   `set ENVIRONMENT` [L257-L258] and `copy "envdiv.cob"` [L102] - environment
#   configuration with no database effect. The facade stub block
#   [L139-L159] - see citation correction 6.1. `01 File-Info` [L205-L213] - eight
#   filesystem-metadata fields that only `CBL_CHECK_FILE_EXIST` populates and
#   that `pl055` never reads, testing `return-code` instead; NOT a clock read.
#   `01 ws-Test-Date pic x(10).` [L181], `01 error-code pic 999.` [L227] and
#   `03 ws-Conv-Date pic x(10).` [L184] - declared and never referenced anywhere
#   in the program. `03 ws-swap` [L183] IS modelled, inside
#   `dates.zz070_convert_date`, because [L614] and [L616] use it.
#
# 7.6  MESSAGE LITERALS
#   `prog-name` [L125] survives as the log prefix. `PL003` [L217], `PL006`
#   [L218], `PL201` [L220], `PL202` [L221], `PL203` [L222] and `PL204` [L223]
#   survive only insofar as they become log text; `PL204` is in fact never
#   referenced by any statement.
#
# 7.7  THE OTM4 SEQUENCE IS IN-MEMORY ONLY
#   It reaches no schema table and appears in no table dump - see STRUCTURAL
#   NOTES 5.1. Its `OI-Header` layout is the PUBLISHED `records/otm5.OiHeader`,
#   so nothing was declared privately after all; only the FILE was.
#
# 7.8  THINGS `pl055` SIMPLY DOES NOT HAVE, STATED EXPLICITLY
#   * NO print file and NO `call "SYSTEM" using Print-Report` - unlike `sl060`,
#     `sl100`, `pl060` and `pl100`. Nothing is spooled to the operating system.
#   * NO `PInvoice-Start` and NO `set fn-` of any kind - so no cursor
#     repositioning to emulate. `sl055` has `Invoice-Start`
#     [sales/sl055.cbl:L476] preceded by `set fn-not-less-than to true`
#     [sales/sl055.cbl:L475].
#   * NO skip-invoice paragraph, NO proforma filter, NO pending filter and NO
#     `ws-p-flag` - divergence 7. `pl055` has ONE conditional `goback` [L432]
#     where `sl055` has two [sales/sl055.cbl:L509, L518].
#   * ZERO IRS fan-out tests. It is an extract program, like `sl055`; the
#     `IRS-Used`/`IRS-Instead` switch [copybooks/wssystem.cob:L179-L181] is
#     tested by `sl060`/`pl060`, not here.
#   * ZERO `ROUNDED` stores and ZERO `DIVIDE` statements. Every store in this
#     program truncates toward zero. The five `ROUNDED` sites in the whole
#     migration are [general/gl051.cbl:L791], [general/gl051.cbl:L796],
#     [general/gl080.cbl:L328], [irs/irs030.cbl:L1551] and
#     [irs/irs030.cbl:L1562] - none of them here.
#   * ZERO `ON SIZE ERROR`, ZERO `REMAINDER`, ZERO relation-condition
#     arithmetic.
#   * NO `zz050`, NO `zz060` and NO `maps03`/`maps04` wrapper. `pl055` does not
#     `copy "wsmaps03.cob"` and never calls the date module, so anomaly A-22 -
#     the wrapper named after the copybook with its exit named after the called
#     program, [general/gl070.cbl:L603-L609] - CANNOT ARISE HERE. Only `zz070`
#     exists.
#   * NO `PERFORM ... THRU`.
#
# -----------------------------------------------------------------------------
# 8.  AMBIGUITY REGISTER - EIGHT QUESTIONS FOR THE ORACLE
#
# Rule R-6 makes compiled behaviour the tie-breaker and requires each resolution
# to be documented. These are the questions this module cannot settle by reading
# the source; each is marked `AMBIGUITY Q-PL055-<n>` at the site it affects and
# belongs in `docs/migration/ambiguity-resolutions.md`.
#
#   Q-PL055-1  The observable effect of the missing `WITH FILLER` at [L547].
#              Site: `_initialise_oi_header`.  Divergence 5.
#   Q-PL055-2  Whether the unguarded `Create-Anal` -> `Create-Main` retry
#              [L499] can fail to terminate, and what the compiled program does
#              when `Analysis-Write` [L494] fails.
#              Site: `_create__create_main`.
#   Q-PL055-3  The negated `oi-` extract row against the UNNEGATED `ih-` sum:
#              for a credit note the OTM4 row carries negatives [L571-L575]
#              while `ws-inv-amt` [L580] holds the positive sum that [L584]
#              adds into `pl-credit-notes-this-month`.
#              Site: `_extract`.  Divergences 1 and 2.
#   Q-PL055-4  The disposition of a failed `write open-item-record-4` [L588]:
#              the diagnostic transfers no control, so the sequence is left
#              short with no retry and no abort, and the partial state stands.
#              Site: `_extract`.
#   Q-PL055-5  The `OI-Header` / `open-item-record-4` storage relationship and
#              whether the object handoff to `pl060` can differ from the
#              113-byte handoff the COBOL performs.
#              Site: `acas_posting.workfiles.OpenItemWorkFile`.
#              Divergence 13.  See 5.2 above.
#   Q-PL055-6  Whether any mandated scenario seeds `File-System-Used` to zero
#              and therefore reaches the `FS-Cobol-Files-Used` branch at all.
#              Site: `_mainline`.  See 7.1 above.
#   Q-PL055-7  The exact shape of the single context argument the generated
#              facade verbs take.
#              Site: `_FacadeContext`.
#   Q-PL055-8  Which purchase-invoice record shape the `acas026` handler wants -
#              the flat `plwspinv2.cob` views this program copies, or the nested
#              `plwspinv.cob` `PInvoiceHeader` the published handler dispatches
#              on.
#              Site: `_FacadeContext`.
#
# TWO FURTHER QUESTIONS AROSE DURING VALIDATION AND ARE NOT IN THE REGISTER
# BECAUSE THEY WERE ANSWERED, NOT DEFERRED. Both concern what a COBOL `WRITE`
# against an existing key does, and both were settled by reading the handler
# rather than by reasoning about the COBOL:
#   * `Value-Write` [L474] against an existing roll-up key. `ba070_process_write`
#     in `acas_posting.dal.acas013_value` issues `INSERT INTO `VALUEANAL-REC`
#     SET ...`, and on `1062`/`1022`/SQLSTATE `23000` sets `FS-Reply` 22 and
#     LEAVES THE STORED ROW UNTOUCHED - reproducing
#     [common/valueMT.cbl:L817-L831]. So the roll-up totals survive; the defect
#     is an unchecked duplicate INSERT and a stale status, NOT a lost update.
#     Recorded as FINDING A in section 4.
#   * `Analysis-Write` [L494, L497] against an existing analysis key. Same shape
#     in `acas_posting.dal.acas015_analysis`; the reply is never tested at either
#     call site, so a duplicate is silently tolerated.
# They are minuted here because the FIRST reading of the source suggested a lost
# update, and the wrong reading is easy to arrive at independently. It is worth a
# reader's while to know it was checked against the handler and rejected.
#
# -----------------------------------------------------------------------------
# 9.  WHAT THIS PROGRAM WRITES - THREE TABLES AND ONE WORK SEQUENCE
#
#   VALUEANAL-REC     `Value-Write` [L335, L474, L520] and `Value-Rewrite`
#                     [L337, L356, L522, L534]
#   ANALYSIS-REC      `Analysis-Write` [L494, L497] - the emergency records
#   PUINVOICE-REC     `PInvoice-Rewrite` [L371, L397], stamping `ih-update` and
#                     `ih-status`
#   PUINV-LINES-REC   `PInvoice-Rewrite` [L359], stamping `il-update`
#   SYSTOT-REC        indirectly, through the two period-total adds at [L582]
#                     and [L584] - sites 6 and 7 of the nine period-total writes
#                     that Agent Action Plan section 0.6.4 calls *"the sole
#                     writers"* of that record. Persisted by the menu, not here;
#                     see citation correction 6.3.
#   SYSTEM-REC        indirectly, through the `Date-Form` default at [L610].
#   open-item-file-4  the OTM4 work sequence, which `pl060` consumes and which
#                     reaches no table.
#
# --- end traceability -------------------------------------------------------
