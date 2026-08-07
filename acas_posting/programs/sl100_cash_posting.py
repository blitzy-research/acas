"""`sl100` - Sales cash posting [sales/sl100.cbl].

The whole program: it posts sales receipts to the Sales ledger and the open-item
file, and maintains the customer payment statistics.

The payment-days average is the third variant of the cycle's average idiom
[sales/sl100.cbl:L497-L516] and the three variants disagree with each other. This
one guards on the activity counter being non-zero
[sales/sl100.cbl:L506], increments it before dividing
[sales/sl100.cbl:L510] and divides accumulator by activity
[sales/sl100.cbl:L511]. `divide work-b by sales-pay-activety` here and `divide
sales-activety into work-2` at [sales/sl060.cbl:L827] compute the SAME quotient;
the spelling and the guards differ, and that difference is what is reproduced.

Also here: the worst-payment-days watermark, which only ever moves upward
[sales/sl100.cbl:L513-L514]; a sign flip [sales/sl100.cbl:L395]; one of the
cycle's nine period-total writes [sales/sl100.cbl:L404]; and one of the
migration's four `PERFORM ... THRU` sites [sales/sl100.cbl:L344].
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Final

from acas_posting import dates as _dates
from acas_posting.cobol import arithmetic as _arith
from acas_posting.cobol import condition_names as _cn
from acas_posting.cobol import move as _move
from acas_posting.cobol import picture as _picture
from acas_posting.cobol.field import FieldDescriptor, descriptors_for_copybook_record
from acas_posting.dal import facade as _facade
from acas_posting.dal.status import FsReply

#  The data-access layer's OWN log renderer, imported rather than
#  reimplemented so this program and the handlers cannot disagree about what a
#  safe diagnostic looks like. It escapes control characters and caps the
#  length; it decides nothing and is used only at log sites.
from acas_posting.records.calling_data import WsCallingData
from acas_posting.records.file_access import FileAccess
from acas_posting.records.file_defs import FileDefs
from acas_posting.records.gl_batch import GlBatchRecord
from acas_posting.records.gl_posting import WsPostingRecord
from acas_posting.records.maps03 import Maps03Ws
from acas_posting.records.otm3 import (
    Filler1,
    Filler2,
    OiBatch,
    OiCustomer,
    OiHeader,
    OiKey,
)
from acas_posting.records.sales_ledger import WsSalesRecord
from acas_posting.records.spl_irs_posting import WsIrsPostingRecord
from acas_posting.records.system_record import SystemRecord
from acas_posting.records.system_record_4 import SystemRecord4
from acas_posting.records.test_data_flags import AcasDalCommonData
from acas_posting.records.value_analysis import WsValueRecord

__all__ = ("run",)


_log: Final = logging.getLogger(__name__)

_SRC: Final = "sales/sl100.cbl"


# Field descriptors R-2 and R-5 both land here.


def _index(record: str) -> Mapping[str, FieldDescriptor]:
    """Index one copybook record's descriptors by case-folded COBOL name.

    ``FILLER`` is dropped: it is the only name that repeats with genuinely different
    shapes, it is never referenced by name, and keeping it would make the conflict guard
    below fire on a name no caller can ask for.
    """
    table: dict[str, FieldDescriptor] = {}
    for descriptor in descriptors_for_copybook_record(record):
        if descriptor.is_filler:
            continue
        key = descriptor.name.casefold()
        seen = table.get(key)
        if seen is not None and _shape(seen) != _shape(descriptor):
            raise ValueError(
                f"{record}.{descriptor.name} resolves to two different shapes "
                f"in the generated data dictionary: {_shape(seen)} vs "
                f"{_shape(descriptor)}"
            )
        table[key] = descriptor
    return table


def _shape(descriptor: FieldDescriptor) -> tuple[object, ...]:
    """The storage shape of a descriptor, for the duplicate guard in `_index`."""
    return (
        descriptor.usage,
        descriptor.digits,
        descriptor.scale,
        descriptor.signed,
        descriptor.character_length,
        descriptor.is_group,
    )


def _local(name: str, clauses: str, line: int) -> FieldDescriptor:
    """A descriptor for one of this program's own WORKING-STORAGE fields.

    These sixteen fields exist only inside ``sl100``, so they have no dictionary entry
    and no table column. R-5 requires provenance regardless, which the
    ``source_locator`` supplies.
    """
    return _picture.descriptor_for(
        clauses, name=name, source_locator=f"{_SRC}:L{line}"
    )


_SL: Final = _index("WS-Sales-Record")
_OI: Final = _index("OI-Header")
_SYS: Final = _index("System-Record")
_SYS4: Final = _index("System-Record-4")
_BAT: Final = _index("WS-Batch-Record")
_POST: Final = _index("WS-Posting-Record")
_IRS: Final = _index("WS-IRS-Posting-Record")
_VAL: Final = _index("WS-Value-Record")
_FA: Final = _index("File-Access")

_D: Final[Mapping[str, FieldDescriptor]] = {
    "ws-reply": _local("ws-reply", "pic x", 166),
    "wx-reply": _local("wx-reply", "pic xxx value spaces", 167),
    "xx": _local("xx", "pic 99", 168),
    "j": _local("j", "pic 99", 170),
    "k": _local("k", "pic 999", 171),
    "line-cnt": _local("line-cnt", "binary-char value zero", 173),
    "t-paid": _local("t-paid", "pic s9(7)v99 comp-3 value zero", 174),
    "t-approp": _local("t-approp", "pic s9(7)v99 comp-3 value zero", 175),
    "t-deduct": _local("t-deduct", "pic s9(7)v99 comp-3 value zero", 176),
    "j-paid": _local("j-paid", "pic s9(7)v99 comp-3 value zero", 177),
    "j-approp": _local("j-approp", "pic s9(7)v99 comp-3 value zero", 178),
    "j-deduct": _local("j-deduct", "pic s9(7)v99 comp-3 value zero", 179),
    "n-deduct": _local("n-deduct", "binary-long value zero", 180),
    "work-1": _local("work-1", "pic s9(7)v99 comp-3 value zero", 181),
    "work-a": _local("work-a", "binary-long value zero", 182),
    "work-b": _local("work-b", "binary-long value zero", 183),
    # ``77 exception-msg pic x(25) value spaces.`` [sales/sl100.cbl:L136] - declared
    # OUTSIDE ``01 ws-data``, hence the out-of-order line number.  It is the receiver
    # ``Eval-Status`` [L700-L704] fills and the field [L687] displays.
    "exception-msg": _local("exception-msg", "pic x(25) value spaces", 136),
}

# ``01 Error-Messages.`` [sales/sl100.cbl:L209-L215].  Two of the three survive
# as log text; see OMISSIONS.
#
# ``SL002`` IS DECLARED AND DELIBERATELY NEVER REFERENCED.  The frozen program
# displays it at [L298] and [L688], each time immediately before an ``accept
# ws-reply``, and the literal is nothing but the instruction to press that key.
# AAP 0.3.4 drops a prompt whose only effect is to block a terminal, so no log
# record carries it; the substantive diagnostic on each of those two paths is the
# ``SL137``/``SL132`` record beside it.  The DECLARATION stays because R-5 maps
# the whole ``01 Error-Messages.`` group and a shorter group would misreport the
# frozen source.
_SL002: Final = "SL002 Note error and hit return"  # [L211]
_SL132: Final = "SL132 Err on Batch file write : "  # [L214]
_SL137: Final = "SL137 Payments Not Proofed"  # [L215]

_PROG_NAME: Final = "SL100 (3.3.01)"

#: ``03 u-bin binary-long.`` [copybooks/wsmaps03.cob:L30] - the date module's binary
#: day-number field, ``copy "wsmaps03.cob"`` at [sales/sl100.cbl:L138].
_U_BIN: Final = _picture.descriptor_for(
    "binary-long", name="u-bin", source_locator="copybooks/wsmaps03.cob:L30"
)


# Program state - the WORKING-STORAGE and LINKAGE of one run A COBOL program's storage
# is global to the program and private to it, and its paragraphs read and write it
# freely.


@dataclass(slots=True)
class _State:
    """One run's LINKAGE and WORKING-STORAGE."""

    ws_calling_data: WsCallingData
    system: SystemRecord
    system_4: SystemRecord4
    to_day: str
    file_defs: FileDefs

    ok_to_post: bool

    # -- NOT A COBOL FIELD: the caller's keyword-only handler declarations -----
    # The extras every facade ``PERFORM`` in this program forwards to its
    # handler, the caller's transport-security policy chief among them. There is
    # no COBOL counterpart because the frozen bridge has none - transport is
    # compiled into ``cobmysqlapi.c``, and ``call "MySQL_real_connect"``
    # [common/otm3MT.cbl:L459] passes host, user, password, schema, port and
    # socket and nothing else.
    #
    # ⭐ THE DEFAULT IS AN EMPTY MAPPING, WHICH IS THE SAFE ANSWER, NOT THE ABSENT
    # ONE. Every handler declares ``transport: TransportSecurity | None = None``
    # and ``connection._require_permitted_connection`` resolves ``None`` against
    # the INSTALLED PROCESS POLICY: under the exact-parity default an unencrypted
    # non-local hop is reported at WARNING and connected to, as the compiled open
    # does (rule R-3), and only an explicitly hardened policy refuses it. This
    # program reaches ``acas019`` for the OTM3 open-item file, so a declaration
    # meant for it comes from its caller - see ``run``'s ``dal_options``. Carried
    # opaquely: nothing here reads a key of it.
    dal_options: Mapping[str, object]

    # -- ``copy "wsfnctn.cob".`` [L139] --------------------------------------
    # ONE ``01 File-Access``, shared by every facade verb, exactly as the COBOL
    # has one.  ``fs-reply`` at L333/L364/L580/L587/L683 and ``RRN`` at
    # L593/L667/L669/L691 are fields of *this* record, which is why the batch's
    # record number survives from ``BL-Open`` through ``BL-Write`` to
    # ``BL-Close``.
    file_access: FileAccess
    dal_common: AcasDalCommonData

    sales: WsSalesRecord
    oi: OiHeader
    value: WsValueRecord
    batch: GlBatchRecord
    posting: WsPostingRecord
    irs_posting: WsIrsPostingRecord

    maps03_ws: Maps03Ws
    ws_dates: _dates.WsDateFormats

    # ``FacadeContext`` is frozen and carries a single ``record``, so an entity gets its
    # own context. That is not a Python compromise.
    ctx_sales: _facade.FacadeContext
    ctx_otm3: _facade.FacadeContext
    ctx_value: _facade.FacadeContext
    ctx_batch: _facade.FacadeContext
    ctx_posting: _facade.FacadeContext
    ctx_irs: _facade.FacadeContext

    # Only ``line-cnt`` and the ten numerics from L174 down carry a ``VALUE`` clause.
    ws_reply: str = " "
    #: ``77 exception-msg pic x(25) value spaces.`` [sales/sl100.cbl:L136].  Written
    #: only by ``Eval-Status`` and read only by the display at [L687].
    exception_msg: str = " " * 25
    wx_reply: str = "   "
    xx: int = 0
    j: int = 0
    k: int = 0
    line_cnt: int = 0
    t_paid: Decimal = field(default_factory=lambda: Decimal("0.00"))
    t_approp: Decimal = field(default_factory=lambda: Decimal("0.00"))
    t_deduct: Decimal = field(default_factory=lambda: Decimal("0.00"))
    j_paid: Decimal = field(default_factory=lambda: Decimal("0.00"))
    j_approp: Decimal = field(default_factory=lambda: Decimal("0.00"))
    j_deduct: Decimal = field(default_factory=lambda: Decimal("0.00"))
    n_deduct: int = 0
    work_1: Decimal = field(default_factory=lambda: Decimal("0.00"))
    work_a: int = 0
    work_b: int = 0


def _new_oi_header() -> OiHeader:
    """A cleared ``01 oi-header.`` work area [copybooks/slwsoi3.cob]."""
    zero = _move.ZERO
    spaces = _move.SPACES
    return OiHeader(
        oi_key=OiKey(
            oi_customer=OiCustomer(
                oi_nos=_move.move_figurative(spaces, _OI["oi-nos"]),
                oi_check=_move.move_figurative(zero, _OI["oi-check"]),
            ),
            oi_invoice=_move.move_figurative(zero, _OI["oi-invoice"]),
        ),
        filler_1=Filler1(
            oi_date=_move.move_figurative(zero, _OI["oi-date"]),
            oi_batch=OiBatch(
                oi_b_nos=_move.move_figurative(zero, _OI["oi-b-nos"]),
                oi_b_item=_move.move_figurative(zero, _OI["oi-b-item"]),
            ),
            oi_type=_move.move_figurative(zero, _OI["oi-type"]),
            oi_description=_move.move_figurative(spaces, _OI["oi-description"]),
            oi_hold_flag=_move.move_figurative(spaces, _OI["oi-hold-flag"]),
            oi_unapl=_move.move_figurative(spaces, _OI["oi-unapl"]),
            filler_2=Filler2(
                oi_p_c=_move.move_figurative(zero, _OI["oi-p-c"]),
                oi_net=_move.move_figurative(zero, _OI["oi-net"]),
                oi_approp=_move.move_figurative(zero, _OI["oi-approp"]),
                oi_extra=_move.move_figurative(zero, _OI["oi-extra"]),
                oi_carriage=_move.move_figurative(zero, _OI["oi-carriage"]),
                oi_vat=_move.move_figurative(zero, _OI["oi-vat"]),
                oi_discount=_move.move_figurative(zero, _OI["oi-discount"]),
                oi_e_vat=_move.move_figurative(zero, _OI["oi-e-vat"]),
                oi_c_vat=_move.move_figurative(zero, _OI["oi-c-vat"]),
                oi_paid=_move.move_figurative(zero, _OI["oi-paid"]),
            ),
            oi_status=_move.move_figurative(zero, _OI["oi-status"]),
            oi_deduct_days=_move.move_figurative(zero, _OI["oi-deduct-days"]),
            oi_deduct_amt=_move.move_figurative(zero, _OI["oi-deduct-amt"]),
            oi_deduct_vat=_move.move_figurative(zero, _OI["oi-deduct-vat"]),
            oi_days=_move.move_figurative(zero, _OI["oi-days"]),
            oi_cr=_move.move_figurative(zero, _OI["oi-cr"]),
            oi_applied=_move.move_figurative(spaces, _OI["oi-applied"]),
            oi_date_cleared=_move.move_figurative(zero, _OI["oi-date-cleared"]),
        ),
    )


def _new_state(
    ws_calling_data: WsCallingData,
    system_record: SystemRecord,
    system_record_4: SystemRecord4,
    to_day: str,
    file_defs: FileDefs,
    *,
    ok_to_post: bool,
    dal_options: Mapping[str, object] | None = None,
) -> _State:
    """Establish WORKING-STORAGE and the six facade contexts for one run."""
    file_access = FileAccess()
    dal_common = AcasDalCommonData()
    # `None` and `{}` are the same thing here - no declaration - and both leave
    # every handler under the installed process policy. Copied rather than aliased so the
    # caller's mapping cannot change under a run in progress.
    handler_options: Mapping[str, object] = dict(dal_options) if dal_options else {}

    sales = WsSalesRecord()
    oi = _new_oi_header()
    value = WsValueRecord()
    batch = GlBatchRecord()
    posting = WsPostingRecord()
    irs_posting = WsIrsPostingRecord()

    def _ctx(record: object) -> _facade.FacadeContext:
        return _facade.FacadeContext(
            system=system_record,
            record=record,
            file_access=file_access,
            file_defs=file_defs,
            dal_common=dal_common,
            # No COBOL counterpart and no accounting value: the caller's
            # keyword-only declarations, transport policy among them. Attached to
            # EVERY context this program builds, so the policy does not depend on
            # which entity a verb happens to touch; `dal/facade.py` projects it
            # onto the extras each handler actually declares.
            options=handler_options,
        )

    return _State(
        ws_calling_data=ws_calling_data,
        system=system_record,
        system_4=system_record_4,
        to_day=to_day,
        file_defs=file_defs,
        ok_to_post=ok_to_post,
        dal_options=handler_options,
        file_access=file_access,
        dal_common=dal_common,
        sales=sales,
        oi=oi,
        value=value,
        batch=batch,
        posting=posting,
        irs_posting=irs_posting,
        maps03_ws=Maps03Ws(),
        ws_dates=_dates.WsDateFormats(),
        ctx_sales=_ctx(sales),
        ctx_otm3=_ctx(oi),
        ctx_value=_ctx(value),
        ctx_batch=_ctx(batch),
        ctx_posting=_ctx(posting),
        ctx_irs=_ctx(irs_posting),
    )


# Condition names - ``88``-level tests, never a raw literal R-2 keeps every ``88``-level
# test out of this module's own code.

_is_g_l: Final = _cn.predicate_for("G-L")

_is_irs_used: Final = _cn.predicate_for("IRS-Used")

_is_irs_both_used: Final = _cn.predicate_for("IRS-Both-Used")

_is_s_closed: Final = _cn.predicate_for("S-Closed", copybook="copybooks/slwsoi.cob")


def _g_l(state: _State) -> bool:
    """``if G-L`` - the General Ledger is in use. [sales/sl100.cbl:L324, L417, L462, L585,
    L666, L690, L695].
    """
    return bool(_is_g_l(state.system.system_data_block.level.level_1))


def _irs_used(state: _State) -> bool:
    """``if irs-used`` [sales/sl100.cbl:L578, L647, L693]."""
    return bool(_is_irs_used(state.system.general_ledger_block.irs_instead))


def _irs_both_used(state: _State) -> bool:
    """``if IRS-Both-Used`` [sales/sl100.cbl:L578, L585, L647, L665, L690, L693, L695].
    """
    return bool(_is_irs_both_used(state.system.general_ledger_block.irs_instead))


def _s_closed(state: _State) -> bool:
    """``if s-closed`` [sales/sl100.cbl:L350]."""
    return bool(_is_s_closed(state.oi.filler_1.oi_status))


class _Flow:
    """The three outcomes of the ``loop.`` paragraph, as named constants."""

    CONTINUE_LOOP: Final = "continue-loop"
    LEAVE_LOOP: Final = "leave-loop"
    FALL_THROUGH: Final = "fall-through"


def _literal(text: str, receiving: FieldDescriptor) -> str:
    """A literal as the receiving field would hold it.

    COBOL compares an alphanumeric field with a shorter literal by padding the literal
    to the field's width, so ``if wx-reply = "NO"`` [sales/sl100.cbl:L316] against ``wx-
    reply pic xxx`` [L167] is really a comparison against ``"NO "``.
    """
    return _move.move_alphanumeric(text, receiving)


def _upper_case(text: str, receiving: FieldDescriptor) -> str:
    """``function upper-case`` [sales/sl100.cbl:L315].

    An intrinsic function, not a program call, so R-1 is not engaged. The case fold
    itself has no COBOL-specific subtlety on an alphanumeric field.
    """
    return _move.move_alphanumeric(text.upper(), receiving)


def _init01(state: _State) -> bool:
    """``init01 section.`` [sales/sl100.cbl:L279-L301]."""
    # [L280] ``move prog-name to l1-name.`` and [L281] ``move Print-Spool-Name to PSN.``
    # are print-heading and spool-name moves; both are in OMISSIONS.

    _zz070_convert_date(state)

    # [L296-L301] GATE 1. ``S-Flag-P`` is the sales-payments proofing latch on SYSTEM-
    # REC; unless a proof run has set it to 2, this program refuses to run.
    if state.system.sales_ledger_block.s_flag_p != 2:
        # [L297] ``display SL137 at 2301``.  A DIAGNOSTIC with no database
        # effect becomes a log record (AAP 0.3.4); it must not, and does not,
        # alter control flow.
        _log.error("%s", _SL137)
        # [L298] ``display SL002 at 2401`` and [L299] ``accept ws-reply at
        # 2433``.  BOTH DROPPED.  The literal is "Note error and hit return" -
        # the whole of it is the instruction to press the key that the ``accept``
        # then reads - so there is no substantive half to keep, and a headless
        # run has no operator to instruct.  The TRANSFER below is not dropped.
        #
        # GO TO class 4 [sales/sl100.cbl:L300] -> ``menu-exit.`` L476.
        #
        # PER-SITE EQUIVALENCE PROOF.  ``menu-exit.`` L476 contains exactly one
        # statement, ``exit program.`` L477, and is the last paragraph of the
        # program's straight-line flow.  Reaching it therefore ends the run with
        # no further statement executed.  At this point no file has been opened
        # (the opens are at L321-L325, downstream) and no facade verb has been
        # called, so the transfer is observationally a return that leaves the
        # database untouched.  Returning ``False`` here, which makes ``run()``
        # call ``_menu_exit`` and return, executes precisely that same set of
        # statements in precisely that order.  Equivalent.
        return False
    return True


def _menu_return(state: _State) -> None:
    """``menu-return.`` [sales/sl100.cbl:L303-L308].

    FALL-THROUGH TARGET. No ``GO TO`` anywhere in the migrated surface names this label;
    it is reached only by falling out of the ``end-if`` at [L301].
    """
    _log.info("%s", _PROG_NAME)
    _log.info("Sales Cash Posting")
    # [L307] ``perform zz070-Convert-Date.`` - the second call; the first was at [L293].
    # Both are reproduced.
    _zz070_convert_date(state)
    # [L308] ``display ws-date at 0171``.  NO LOG COUNTERPART: ``ws-date`` is the
    # posting date this run stamps into every record it writes, a date with
    # business meaning that the safe-event schema in ``acas_posting/dal/status.py``
    # excludes (CWE-532).  It is an INPUT the caller supplied through ``to-day``,
    # already known wherever the run was started and pinned by ``clock.py``.  The
    # conversion above still runs - it defaults ``Date-Form`` in the system
    # record, which IS a table effect.


def _acpt_xrply(state: _State) -> bool:
    """``acpt-xrply.`` [sales/sl100.cbl:L310-L329].

    The paragraph runs from its label to the next one, so it carries not only
    the run-confirm but the file opens, the page counter and the first heading.

    Returns ``False`` when the confirm transfers control to ``menu-exit``.
    """
    # [L311-L312] THE PROMPT ITSELF IS DROPPED, not logged.  It is the screen
    # text for the ``accept wx-reply`` at [L314], and AAP 0.3.4 resolves an
    # ``accept`` that gates a database write into "an explicit CLI parameter with
    # the COBOL default preserved" - which ``ok_to_post`` is.  The prompt is the
    # dialogue around that parameter, so reproducing it as an operator diagnostic
    # would emit a question no one can answer.

    # The retry loop of [L318-L319] is preserved structurally. It terminates on its
    # first pass and cannot spin.
    while True:
        state.wx_reply = _move.move_figurative(_move.SPACES, _D["wx-reply"])
        # [L314] ``accept wx-reply at 1256 ... update.`` This is the one accept in the
        # program that is NOT dropped.
        state.wx_reply = _move.move_alphanumeric(
            "YES" if state.ok_to_post else "NO", _D["wx-reply"]
        )
        state.wx_reply = _upper_case(state.wx_reply, _D["wx-reply"])

        if state.wx_reply == _literal("NO", _D["wx-reply"]):
            return False
        if state.wx_reply != _literal("YES", _D["wx-reply"]):
            # GO TO class 1 [sales/sl100.cbl:L319] -> ``acpt-xrply.`` L310, an
            # interactive re-prompt.
            continue
        break

    _facade.otm3_open(state.ctx_otm3)
    _facade.sales_open(state.ctx_sales)

    if _g_l(state):
        _bl_open(state)

    state.j = _move.move_figurative(_move.ZERO, _D["j"])
    _headings(state)
    return True


def _loop(state: _State) -> str:
    """``loop.`` [sales/sl100.cbl:L331-L355] - one pass over the OTM3 walk."""
    _facade.otm3_read_next(state.ctx_otm3)
    if state.file_access.fs_reply == FsReply.END_OF_FILE:
        # GO TO class 2 [sales/sl100.cbl:L334] -> ``main-end.`` L435.
        return _Flow.LEAVE_LOOP


    oi_type = state.oi.filler_1.oi_type
    if oi_type != 2 and oi_type != 5 and oi_type != 6:
        return _Flow.CONTINUE_LOOP

    # [L341-L348] THE TYPE-2 BRANCH - a cleared invoice. It updates the payment-days
    # average, clears the batch linkage and rewrites OTM3, then loops.
    batch = state.oi.filler_1.oi_batch
    if oi_type == 2 and batch.oi_b_nos != 0 and batch.oi_b_item != 0:
        # PERFORM THRU [sales/sl100.cbl:L344] spans ``compute-sales-pay`` L497 -> ``csp-
        # exit`` L516.
        _compute_sales_pay(state)
        _csp_exit(state)
        batch.oi_b_nos = _move.move_figurative(_move.ZEROS, _OI["oi-b-nos"])
        batch.oi_b_item = _move.move_figurative(_move.ZEROS, _OI["oi-b-item"])
        state.oi.filler_1.oi_cr = _move.move_figurative(_move.ZEROS, _OI["oi-cr"])
        _facade.otm3_rewrite(state.ctx_otm3)
        return _Flow.CONTINUE_LOOP

    # [L350-L352] ``if s-closed or oi-type = 2``.
    if _s_closed(state) or oi_type == 2:
        return _Flow.CONTINUE_LOOP

    # [L354-L355] ``if zero = oi-b-nos and oi-b-item``. FINDING-2 - a REVERSED
    # abbreviated relation.
    if 0 == batch.oi_b_nos and 0 == batch.oi_b_item:
        return _Flow.CONTINUE_LOOP

    return _Flow.FALL_THROUGH


def _oi_customer_image(state: _State) -> str:
    """The byte image of the ``03 OI-Customer.`` group [copybooks/slwsoi3.cob].

    A group item *is* its children laid end to end, so the image is ``OI-Nos`` (``pic
    x(6)``) followed by ``OI-Check`` (``pic 9``), each rendered through its own picture
    by the published ``MOVE`` primitive.
    """
    customer = state.oi.oi_key.oi_customer
    return _move.move_alphanumeric(
        customer.oi_nos, _OI["oi-nos"], sending_field=_OI["oi-nos"]
    ) + _move.move_alphanumeric(
        customer.oi_check, _OI["oi-check"], sending_field=_OI["oi-check"]
    )


def _cust_update(state: _State) -> None:
    """``cust-update.`` [sales/sl100.cbl:L357-L433]."""
    filler_1 = state.oi.filler_1
    filler_2 = filler_1.filler_2

    state.sales.ws_sales_key = _move.move_alphanumeric(
        _oi_customer_image(state),
        _SL["ws-sales-key"],
        sending_field=_OI["oi-customer"],
        length=7,
    )

    state.ws_reply = _move.move_figurative(_move.SPACE, _D["ws-reply"])
    _facade.sales_read_indexed(state.ctx_sales)
    if state.file_access.fs_reply == FsReply.INVALID_KEY_ON_START:
        state.ws_reply = _move.move_alphanumeric("X", _D["ws-reply"])
    # [L366-L369] the customer name on the print line.  NEITHER ARM IS LOGGED.
    # Both are ``move ... to l5-name`` [L367, L369] - REPORT LINE CONTENT, never
    # a ``display``: the frozen program's only displays are at [L297-L298],
    # [L305-L308], [L311] and [L684-L688].  AAP 0.2.2 puts "report formatting
    # beyond database effects" out of scope, and 0.3.4 converts a DISPLAY, not a
    # report field.  The else arm's operand is additionally the CUSTOMER NAME,
    # which the safe-event schema excludes from a record at any level (CWE-532).
    # The BRANCH SURVIVES because ``ws-reply`` is set from the read status at
    # [L364-L365] and the two arms are the evidence of that split.
    if state.ws_reply == _literal("X", _D["ws-reply"]):
        pass
    else:
        pass


    state.maps03_ws.u_bin = _move.move_numeric(
        filler_1.oi_date, _U_BIN, sending_field=_OI["oi-date"]
    )
    _zz060_convert_date(state)
    # [L377] ``move u-date to l5-date.`` - print only.


    if filler_1.oi_deduct_amt != 0:
        state.n_deduct = _arith.add_to(
            1, receiver_value=state.n_deduct, receiving=_D["n-deduct"]
        )

    # [L386] ``subtract sales-unapplied from sales-current giving l5-old-bal.`` The
    # receiver is a print field, so the statement is in OMISSIONS - but note it reads
    # the ledger BEFORE the four mutations below, which is why it is placed here rather
    # than folded in with [L399].

    state.sales.sales_current = _arith.subtract_from(
        filler_2.oi_approp,
        receiver_value=state.sales.sales_current,
        receiving=_SL["sales-current"],
    )
    state.sales.sales_current = _arith.subtract_from(
        filler_1.oi_deduct_amt,
        receiver_value=state.sales.sales_current,
        receiving=_SL["sales-current"],
    )

    if filler_2.oi_paid != filler_2.oi_approp:
        state.work_1 = _arith.subtract_giving(
            filler_2.oi_approp, minuend=filler_2.oi_paid, receiving=_D["work-1"]
        )
        state.sales.sales_unapplied = _arith.add_to(
            state.work_1,
            receiver_value=state.sales.sales_unapplied,
            receiving=_SL["sales-unapplied"],
        )

    # [L394-L397] the sign flip. FINDING-4 - ``sl100`` uses the ``GIVING`` form and
    # never touches ``sales-current`` until [L397].
    if _arith.compare(state.sales.sales_current, 0) < 0:
        state.work_1 = _arith.multiply_by_giving(
            -1, state.sales.sales_current, _D["work-1"]
        )
        state.sales.sales_unapplied = _arith.add_to(
            state.work_1,
            receiver_value=state.sales.sales_unapplied,
            receiving=_SL["sales-unapplied"],
        )
        state.sales.sales_current = _move.move_figurative(
            _move.ZERO, _SL["sales-current"]
        )


    state.sales.sales_last_pay = _move.move_numeric(
        filler_1.oi_date, _SL["sales-last-pay"], sending_field=_OI["oi-date"]
    )

    # [L402-L410] THE ASYMMETRIC TOTALS. The type-5 arm writes three accumulators AND
    # ``SL-Payments``.
    if filler_1.oi_type == 5:
        state.t_approp = _arith.add_to(
            filler_2.oi_approp,
            receiver_value=state.t_approp,
            receiving=_D["t-approp"],
        )
        # [L404] ``add oi-paid to t-paid sl-payments.`` ONE source, TWO receivers, each
        # converted independently through its own picture.
        state.t_paid = _arith.add_to(
            filler_2.oi_paid, receiver_value=state.t_paid, receiving=_D["t-paid"]
        )
        state.system_4.sales_ledger_data.sl_payments = _arith.add_to(
            filler_2.oi_paid,
            receiver_value=state.system_4.sales_ledger_data.sl_payments,
            receiving=_SYS4["sl-payments"],
        )
        state.t_deduct = _arith.add_to(
            filler_1.oi_deduct_amt,
            receiver_value=state.t_deduct,
            receiving=_D["t-deduct"],
        )
    elif filler_1.oi_type == 6:
        state.j_approp = _arith.add_to(
            filler_2.oi_approp,
            receiver_value=state.j_approp,
            receiving=_D["j-approp"],
        )
        state.j_paid = _arith.add_to(
            filler_2.oi_paid, receiver_value=state.j_paid, receiving=_D["j-paid"]
        )
        state.j_deduct = _arith.add_to(
            filler_1.oi_deduct_amt,
            receiver_value=state.j_deduct,
            receiving=_D["j-deduct"],
        )

    # [L412] ``move oi-approp to oi-paid.`` Order is load-bearing: this overwrites ``oi-
    # paid`` AFTER [L404]/[L409] have accumulated its old value, and BEFORE [L413]
    # persists the row.
    filler_2.oi_paid = _move.move_numeric(
        filler_2.oi_approp, _OI["oi-paid"], sending_field=_OI["oi-approp"]
    )
    # [L413] ``perform Sales-Rewrite.`` [L415] the maintainer's note: for a non-existent
    # sales row the rewrite fails and the error is deliberately ignored.
    _facade.sales_rewrite(state.ctx_sales)

    # [L417-L418] ``if G-L perform BL-Write. *> what happens if using IRS ?`` FINDING-5
    # - the maintainer's question mark has an answer, and it is "nothing happens".
    if _g_l(state):
        _bl_write(state)

    filler_1.oi_status = _move.move_numeric(1, _OI["oi-status"])
    _facade.otm3_rewrite(state.ctx_otm3)


    # [L429] ``add 1 to line-cnt.`` The counter survives the print file's removal
    # because [L430] branches on it.
    state.line_cnt = _arith.add_to(
        1, receiver_value=state.line_cnt, receiving=_D["line-cnt"]
    )
    if _arith.compare(state.line_cnt, state.system.system_data_block.page_lines) > 0:
        _headings(state)

    return


def _main_end(state: _State) -> None:
    """``main-end.`` [sales/sl100.cbl:L435-L474] - the class-2 post-loop block.

    This is the work the ``GO TO main-end`` at [L334] jumps to, and it is substantial:
    two closes, the totals, the deduction merge and its reversal out of value analysis,
    the batch close, and two SYSTEM-REC stamps.
    """
    _facade.otm3_close(state.ctx_otm3)
    _facade.sales_close(state.ctx_sales)

    # [L441-L452] the two total print blocks - "Payment Totals" from ``t-*`` and
    # "Journal Totals" from ``j-*``.  NOT LOGGED.  Every statement in both blocks
    # is a ``move`` into ``line-5`` followed by ``write print-record``: report
    # content, which AAP 0.2.2 puts out of scope, and the frozen program displays
    # none of it.  The six operands are MONETARY TOTALS, which the safe-event
    # schema in ``acas_posting/dal/status.py`` excludes from a log record at any
    # level (CWE-532).  The accumulators themselves are untouched - they are real
    # and several of them feed SYSTOT-REC, which is where the audit trail lives.
    # [L453] ``close print-file.`` - OMITTED with the print file.
    # [L454] ``call "SYSTEM" using print-report.`` - the report spool-out path,
    # placed out of scope by AAP 0.1.1.  OMITTED and recorded.  (Note the
    # lower-case spelling here against ``sl060``'s ``Print-Report``.)

    state.t_deduct = _arith.add_to(
        state.j_deduct, receiver_value=state.t_deduct, receiving=_D["t-deduct"]
    )
    if state.t_deduct != 0:
        _facade.value_open(state.ctx_value)
        _analise_deductions(state)
        _facade.value_close(state.ctx_value)

    if _g_l(state):
        _bl_close(state)


    state.system.sales_ledger_block.oi_3_flag = _move.move_alphanumeric(
        "Y", _SYS["oi-3-flag"]
    )
    # [L474] ``move zero to S-Flag-P.`` The proofing latch of [L296], cleared. Together
    # with that gate this makes the program a one-shot.
    state.system.sales_ledger_block.s_flag_p = _move.move_figurative(
        _move.ZERO, _SYS["s-flag-p"]
    )


def _menu_exit(state: _State) -> None:
    """``menu-exit.`` [sales/sl100.cbl:L476-L477] - the one exit of the program.

    Reached three ways: the class-4 transfer at [L300], the class-4 transfer at
    [L317], and fall-through from [L474].
    """
    # EXIT PROGRAM [sales/sl100.cbl:L477] - ``exit program.``, which returns to
    # the caller.  Note the spelling: ``exit program.``, not ``goback``.  In a
    # called sub-program the two are equivalent here, and the source's choice is
    # recorded rather than normalised.  ``run()`` returning is that return.
    #
    # NO LOG RECORD.  ``menu-exit.`` displays NOTHING - the paragraph is one
    # statement long - so an "exit program" event would be output the compiled
    # program never produced, which R-4 forbids inventing.  The caller already
    # observes the return, and ``WS-Term-Code`` carries whatever the run set.
    #
    # ``state`` IS STILL THE PARAMETER even though the body no longer reads it:
    # R-5 keeps the paragraph's signature uniform with every other paragraph
    # function in this module, and the three call sites [L300, L317, L474] pass it
    # exactly as the frozen transfers reach the label.
    del state


def _headings(state: _State) -> None:
    """``headings.`` [sales/sl100.cbl:L479-L495] - the report page header.

    Print-only, and retained for two reasons. R-5 requires a named function per
    paragraph whatever the paragraph does.
    """
    state.j = _arith.add_to(1, receiver_value=state.j, receiving=_D["j"])
    # [L481] ``move j to l1-page.`` and [L482] ``move usera to l2-user.`` -
    # print heading fields.  OMITTED, AND NOT LOGGED EITHER.  A page number and a
    # column ruler are report formatting, out of scope per AAP 0.2.2, and
    # ``usera`` is the OPERATOR IDENTITY, which the safe-event schema excludes
    # from a record at any level (CWE-532).  The counter increment above is kept
    # because [L430] branches on the line budget this paragraph resets.
    # [L484-L491] page-throw selection and [L492-L494] the column headings: five
    # ``write print-record`` statements against the omitted print file.
    # [L495] ``move 5 to line-cnt.``  Real: it resets the line budget [L430]
    # tests, so the page break interval is preserved exactly.
    state.line_cnt = _move.move_numeric(5, _D["line-cnt"])


def _compute_sales_pay(state: _State) -> None:
    """``compute-sales-pay.`` [sales/sl100.cbl:L497-L514].

    ANOMALY A-10 [sales/sl100.cbl:L497-L514] - variant (c) of the moving-average idiom.
    Three programs maintain a running average with the "same" three lines and no two of
    them agree. This one differs from ``sl060``'s two variants in six measured
    dimensions.
    """
    sales = state.sales
    filler_1 = state.oi.filler_1

    if filler_1.oi_date_cleared == 0:
        return

    # [L503] ``subtract oi-date from oi-date-cleared giving work-a.`` The days an
    # invoice took to clear.
    state.work_a = _arith.subtract_giving(
        filler_1.oi_date, minuend=filler_1.oi_date_cleared, receiving=_D["work-a"]
    )
    # [L504] ANOMALY A-10 dimension 1 - unconditional, and BEFORE the guard. Reproduced
    # deliberately per R-4; DO NOT FIX.
    state.work_b = _move.move_figurative(_move.ZERO, _D["work-b"])

    # [L506-L507] ANOMALY A-10 dimension 2 - ONE condition, and no ``ELSE``. Reproduced
    # deliberately per R-4; DO NOT FIX.
    if sales.sales_pay_activety != 0:
        state.work_b = _arith.multiply_by_giving(
            sales.sales_pay_activety, sales.sales_pay_average, _D["work-b"]
        )

    # [L509] ANOMALY A-10 dimension 3 - the accumulate happens FIRST ... Reproduced
    # deliberately per R-4; DO NOT FIX.
    state.work_b = _arith.add_to(
        state.work_a, receiver_value=state.work_b, receiving=_D["work-b"]
    )
    # [L510] ... and the counter is incremented AFTER it, so the divisor below already
    # includes this invoice.
    sales.sales_pay_activety = _arith.add_to(
        1,
        receiver_value=sales.sales_pay_activety,
        receiving=_SL["sales-pay-activety"],
    )
    # [L511] ANOMALY A-10 dimension 4 - the ``BY ... GIVING`` form, mirrored.
    sales.sales_pay_average = _arith.divide_by_giving(
        state.work_b, sales.sales_pay_activety, _SL["sales-pay-average"]
    )

    if _arith.compare(state.work_a, sales.sales_pay_worst) > 0:
        sales.sales_pay_worst = _move.move_numeric(
            state.work_a, _SL["sales-pay-worst"], sending_field=_D["work-a"]
        )


def _csp_exit(state: _State) -> None:
    """``csp-exit.`` [sales/sl100.cbl:L516-L517] - the ``PERFORM THRU`` terminus.

    EXIT [sales/sl100.cbl:L517] - the body is ``exit.``, a plain ``EXIT`` statement,
    which is a no-op.
    """
    # EXIT [sales/sl100.cbl:L517] - ``exit.``  A no-op, reproduced as a no-op.
    return


def _analise_deductions(state: _State) -> None:
    """``analise-deductions section.`` [sales/sl100.cbl:L519-L546].

    The two blocks are deliberately NOT factored into one helper.
    """
    value = state.value

    code_image = _move.move_group("Szd", _VAL["va-code"], length=3)
    value.va_code.va_system = _move.move_alphanumeric(
        _move.ref_mod(code_image, 1, 1), _VAL["va-system"]
    )
    value.va_code.va_group.va_first = _move.move_alphanumeric(
        _move.ref_mod(code_image, 2, 1), _VAL["va-first"]
    )
    value.va_code.va_group.va_second = _move.move_alphanumeric(
        _move.ref_mod(code_image, 3, 1), _VAL["va-second"]
    )

    # [L523] ``move 1 to File-Key-No.`` FINDING-6 - this assignment, and the two at
    # [L533] and [L537], are inert.
    state.file_access.logging_data.file_key_no = _move.move_numeric(
        1, _FA["file-key-no"]
    )
    _facade.value_read_indexed(state.ctx_value)
    if state.file_access.fs_reply == FsReply.INVALID_KEY_ON_START:
        _analise_deductions__main_exit(state)
        return

    # [L528-L531] the four subtracts. Two different types share the shape.
    value.va_t_this = _arith.subtract_from(
        state.n_deduct, receiver_value=value.va_t_this, receiving=_VAL["va-t-this"]
    )
    value.va_t_year = _arith.subtract_from(
        state.n_deduct, receiver_value=value.va_t_year, receiving=_VAL["va-t-year"]
    )
    value.va_v_this = _arith.subtract_from(
        state.t_deduct, receiver_value=value.va_v_this, receiving=_VAL["va-v-this"]
    )
    value.va_v_year = _arith.subtract_from(
        state.t_deduct, receiver_value=value.va_v_year, receiving=_VAL["va-v-year"]
    )

    state.file_access.logging_data.file_key_no = _move.move_numeric(
        1, _FA["file-key-no"]
    )
    _facade.value_rewrite(state.ctx_value)

    value.va_code.va_group.va_second = _move.move_figurative(
        _move.SPACE, _VAL["va-second"]
    )
    state.file_access.logging_data.file_key_no = _move.move_numeric(
        1, _FA["file-key-no"]
    )
    _facade.value_read_indexed(state.ctx_value)
    if state.file_access.fs_reply == FsReply.INVALID_KEY_ON_START:
        _analise_deductions__main_exit(state)
        return

    value.va_t_this = _arith.subtract_from(
        state.n_deduct, receiver_value=value.va_t_this, receiving=_VAL["va-t-this"]
    )
    value.va_t_year = _arith.subtract_from(
        state.n_deduct, receiver_value=value.va_t_year, receiving=_VAL["va-t-year"]
    )
    value.va_v_this = _arith.subtract_from(
        state.t_deduct, receiver_value=value.va_v_this, receiving=_VAL["va-v-this"]
    )
    value.va_v_year = _arith.subtract_from(
        state.t_deduct, receiver_value=value.va_v_year, receiving=_VAL["va-v-year"]
    )
    _facade.value_rewrite(state.ctx_value)
    _analise_deductions__main_exit(state)


def _analise_deductions__main_exit(state: _State) -> None:
    """``main-exit. exit section.`` [sales/sl100.cbl:L548].

    Section-qualified, because ``main-exit.`` is the name of five different paragraphs
    in this one program - L548, L595, L676, L698 and L706 - and R-5 requires each to
    have its own function.
    """
    return


_BATCH_NOS_SCALE: Final[int] = 10**5


def _restate_ws_batch_key9(batch: GlBatchRecord) -> None:
    """Keep ``WS-Batch-Key9`` in step with the two members it redefines.

    ⭐⭐ ONE STORAGE, TWO READINGS. ``03 WS-Batch-Key.`` holds ``05 WS-Ledger pic 9.`` and
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


def _bl_open(state: _State) -> None:
    """``BL-Open section.`` [sales/sl100.cbl:L550-L593] - start a GL batch.

    Note the naming: this program calls its three batch sections ``BL-Open``, ``BL-
    Write`` and ``BL-Close``, where ``sl060`` prefixes them (``ca000-BL-Open``) and
    ``pl100`` lower-cases them (``bl-open``). Each program's own spelling is preserved.
    """
    batch = state.batch

    _facade.gl_batch_open(state.ctx_batch)

    batch.ws_batch_key.ws_batch_nos = _move.move_numeric(
        state.system.general_ledger_block.next_batch,
        _BAT["ws-batch-nos"],
        sending_field=_SYS["next-batch"],
    )
    batch.ws_batch_key.ws_ledger = _move.move_numeric(3, _BAT["ws-ledger"])
    _restate_ws_batch_key9(batch)
    # [L557] ``add 1 to Next-Batch.`` The allocation is consumed immediately, so the
    # SYSTEM-REC counter advances even if the batch is later empty.
    state.system.general_ledger_block.next_batch = _arith.add_to(
        1,
        receiver_value=state.system.general_ledger_block.next_batch,
        receiving=_SYS["next-batch"],
    )
    batch.batch_status = _move.move_figurative(_move.ZERO, _BAT["batch-status"])
    batch.cleared_status = _move.move_figurative(_move.ZERO, _BAT["cleared-status"])
    batch.bcycle = _move.move_numeric(
        state.system.system_data_block.scycle,
        _BAT["bcycle"],
        sending_field=_SYS["scycle"],
    )
    # [L561] ``move run-date to entered.`` [copybooks/wssystem.cob:L67] is one of the
    # two date observables the migration pins, and it arrives here purely through
    # linkage on ``system_record`` - this program reads no clock, and R-6 forbids adding
    # one.
    batch.dates.entered = _move.move_numeric(
        state.system.system_data_block.run_date,
        _BAT["entered"],
        sending_field=_SYS["run-date"],
    )

    # [L563] ``move "Sales Ledger Payments" to description.`` 21 characters into ``pic
    # x(24)``.
    batch.description = _move.move_alphanumeric(
        "Sales Ledger Payments", _BAT["description"]
    )
    batch.posting_data.b_default = _move.move_figurative(
        _move.ZERO, _BAT["bdefault"]
    )
    batch.posting_data.batch_def_ac = _move.move_figurative(
        _move.ZERO, _BAT["batch-def-ac"]
    )
    batch.posting_data.batch_def_pc = _move.move_figurative(
        _move.ZERO, _BAT["batch-def-pc"]
    )
    batch.items = _move.move_figurative(_move.ZERO, _BAT["items"])
    batch.amounts.input_gross = _move.move_figurative(
        _move.ZERO, _BAT["input-gross"]
    )
    batch.amounts.input_vat = _move.move_figurative(_move.ZERO, _BAT["input-vat"])
    batch.amounts.actual_gross = _move.move_figurative(
        _move.ZERO, _BAT["actual-gross"]
    )
    batch.amounts.actual_vat = _move.move_figurative(_move.ZERO, _BAT["actual-vat"])

    batch.posting_data.convention = _move.move_alphanumeric(
        "CR", _BAT["convention"]
    )
    batch.posting_data.batch_def_code = _move.move_alphanumeric(
        "SL", _BAT["batch-def-code"]
    )
    batch.posting_data.batch_def_vat = _move.move_alphanumeric(
        "O", _BAT["batch-def-vat"]
    )
    # [L576] ``add postings 1 giving Batch-Start.`` A variadic ``ADD ... GIVING`` with
    # two addends, quantized ONCE into the receiver. ANOMALY A-17, the reading end.
    batch.batch_start = _arith.add_giving(
        state.system.general_ledger_block.postings, 1, receiving=_BAT["batch-start"]
    )

    # [L578-L584] IRS FAN-OUT SITE 1 of 7. Open the transfer file for extend; if that
    # fails, close it and open it for output instead.
    if _irs_used(state) or _irs_both_used(state):
        _facade.spl_posting_open_extend(state.ctx_irs)
        if state.file_access.fs_reply != FsReply.SUCCESS:
            _facade.spl_posting_close(state.ctx_irs)
            _facade.spl_posting_open_output(state.ctx_irs)

    if _irs_both_used(state) or _g_l(state):
        _facade.gl_posting_open(state.ctx_posting)
        if state.file_access.fs_reply != FsReply.SUCCESS:
            _facade.gl_posting_close(state.ctx_posting)
            _facade.gl_posting_open_output(state.ctx_posting)
        # [L590] ``end-if`` [L591] ``end-if.`` - a period after ``end-if``; a style
        # quirk with no effect, noted because the absence of one at [L584] does matter.

    state.file_access.rrn = _move.move_numeric(
        batch.batch_start, _FA["rrn"], sending_field=_BAT["batch-start"]
    )
    _bl_open__main_exit(state)


def _bl_open__main_exit(state: _State) -> None:
    """``main-exit. exit section.`` [sales/sl100.cbl:L595]."""
    return


def _bl_write(state: _State) -> None:
    """``BL-Write section.`` [sales/sl100.cbl:L598-L674] - emit one posting."""
    posting = state.posting
    batch = state.batch
    filler_1 = state.oi.filler_1
    filler_2 = filler_1.filler_2

    posting.post_date = _move.ref_mod_into(
        posting.post_date, 1, 6, _move.ref_mod(state.maps03_ws.u_date, 1, 6)
    )
    posting.post_date = _move.ref_mod_into(
        posting.post_date, 7, 2, _move.ref_mod(state.maps03_ws.u_date, 9, 2)
    )
    batch.items = _arith.add_to(
        1, receiver_value=batch.items, receiving=_BAT["items"]
    )
    posting.ws_post_key.post_number = _move.move_numeric(
        batch.items, _POST["post-number"], sending_field=_BAT["items"]
    )
    posting.post_amount = _move.move_numeric(
        filler_2.oi_paid, _POST["post-amount"], sending_field=_OI["oi-paid"]
    )

    # [L618] the maintainer's own comment: "THIS DOES NOT APPEAR THE SAME as SL060 and
    # PL060/PL100".
    state.xx = _move.move_numeric(1, _D["xx"])
    posting.ws_post_key.batch = _move.move_numeric(
        filler_1.oi_batch.oi_b_nos, _POST["batch"], sending_field=_OI["oi-b-nos"]
    )
    posting.post_legend, state.xx = _move.string_into(
        posting.post_legend,
        [(posting.ws_post_key.batch, _move.DELIMITED_BY_SIZE, _POST["batch"])],
        pointer=state.xx,
    )
    # [L623] ``move WS-Batch-Nos to batch.`` FINDING-8 - this move happens AFTER [L622]
    # has already stringed ``batch``, and ``batch`` is never stringed again.
    posting.ws_post_key.batch = _move.move_numeric(
        batch.ws_batch_key.ws_batch_nos,
        _POST["batch"],
        sending_field=_BAT["ws-batch-nos"],
    )
    posting.post_legend, state.xx = _move.string_into(
        posting.post_legend, ["/"], pointer=state.xx
    )
    state.k = _move.move_numeric(
        filler_1.oi_batch.oi_b_item, _D["k"], sending_field=_OI["oi-b-item"]
    )
    posting.post_legend, state.xx = _move.string_into(
        posting.post_legend,
        [(state.k, _move.DELIMITED_BY_SIZE, _D["k"])],
        pointer=state.xx,
    )
    posting.post_legend, state.xx = _move.string_into(
        posting.post_legend, ["  :  "], pointer=state.xx
    )
    posting.post_legend, state.xx = _move.string_into(
        posting.post_legend,
        [(state.sales.sales_name, _move.DELIMITED_BY_SIZE, _SL["sales-name"])],
        pointer=state.xx,
    )

    # [L630-L631] THE DOUBLE-ENTRY SIDES, and they are SWAPPED relative to ``sl060``.
    posting.post_cr = _move.move_numeric(
        state.system.sales_ledger_block.s_debtors,
        _POST["post-cr"],
        sending_field=_SYS["s-debtors"],
    )
    posting.post_dr = _move.move_numeric(
        state.system.sales_ledger_block.sl_pay_ac,
        _POST["post-dr"],
        sending_field=_SYS["sl-pay-ac"],
    )

    # [L633-L637] ``move zero to`` FIVE receivers. FINDING-10 - the VAT ACCOUNT is
    # ZEROED here, not copied.
    posting.dr_pc = _move.move_figurative(_move.ZERO, _POST["dr-pc"])
    posting.cr_pc = _move.move_figurative(_move.ZERO, _POST["cr-pc"])
    posting.vat_ac = _move.move_figurative(_move.ZERO, _POST["vat-ac"])
    posting.vat_pc = _move.move_figurative(_move.ZERO, _POST["vat-pc"])
    posting.vat_amount = _move.move_figurative(_move.ZERO, _POST["vat-amount"])

    # [L639] ``move spaces to post-vat-side.`` FINDING-11 - inert. [L645] overwrites it
    # with "CR" six lines later and nothing reads it in between. Both moves are
    # reproduced.
    posting.post_vat_side = _move.move_figurative(
        _move.SPACES, _POST["post-vat-side"]
    )

    posting_amount = posting.post_amount
    batch.amounts.input_gross = _arith.add_to(
        posting_amount,
        receiver_value=batch.amounts.input_gross,
        receiving=_BAT["input-gross"],
    )
    batch.amounts.actual_gross = _arith.add_to(
        posting_amount,
        receiver_value=batch.amounts.actual_gross,
        receiving=_BAT["actual-gross"],
    )

    posting.post_code = _move.move_alphanumeric("SL", _POST["post-code"])
    posting.post_vat_side = _move.move_alphanumeric("CR", _POST["post-vat-side"])

    # [L647-L664] IRS FAN-OUT SITE 3 of 7 - the IRS transfer record.
    if _irs_used(state) or _irs_both_used(state):
        irs = state.irs_posting
        irs.ws_irs_post_key.ws_irs_batch = _move.move_numeric(
            posting.ws_post_key.batch,
            _IRS["ws-irs-batch"],
            sending_field=_POST["batch"],
        )
        irs.ws_irs_post_key.ws_irs_post_number = _move.move_numeric(
            posting.ws_post_key.post_number,
            _IRS["ws-irs-post-number"],
            sending_field=_POST["post-number"],
        )
        irs.ws_irs_post_code = _move.move_alphanumeric(
            posting.post_code,
            _IRS["ws-irs-post-code"],
            sending_field=_POST["post-code"],
        )
        irs.ws_irs_post_date = _move.move_alphanumeric(
            posting.post_date,
            _IRS["ws-irs-post-date"],
            sending_field=_POST["post-date"],
        )
        # [L653] ``move Post-DR to WS-IRS-Post-DR`` - ``pic 9(6)`` narrowing into ``pic
        # 9(5)``, so the leading digit is lost if an account number needs six.
        irs.ws_irs_post_dr = _move.move_numeric(
            posting.post_dr, _IRS["ws-irs-post-dr"], sending_field=_POST["post-dr"]
        )
        irs.ws_irs_post_cr = _move.move_numeric(
            posting.post_cr, _IRS["ws-irs-post-cr"], sending_field=_POST["post-cr"]
        )
        irs.ws_irs_post_amount = _move.move_numeric(
            posting.post_amount,
            _IRS["ws-irs-post-amount"],
            sending_field=_POST["post-amount"],
        )
        irs.ws_irs_post_legend = _move.move_alphanumeric(
            posting.post_legend,
            _IRS["ws-irs-post-legend"],
            sending_field=_POST["post-legend"],
        )
        # [L659-L660] ``move 32 to WS-IRS-vat-ac-def Vat-PC *> IS IT ???`` - ONE
        # literal, TWO receivers, and the second of them is on the GL posting record
        # rather than the IRS one.
        irs.ws_irs_vat_ac_def = _move.move_numeric(32, _IRS["ws-irs-vat-ac-def"])
        posting.vat_pc = _move.move_numeric(32, _POST["vat-pc"])
        irs.ws_irs_post_vat_side = _move.move_alphanumeric(
            posting.post_vat_side,
            _IRS["ws-irs-post-vat-side"],
            sending_field=_POST["post-vat-side"],
        )
        irs.ws_irs_vat_amount = _move.move_numeric(
            posting.vat_amount,
            _IRS["ws-irs-vat-amount"],
            sending_field=_POST["vat-amount"],
        )
        _facade.spl_posting_write(state.ctx_irs)

    if _irs_both_used(state) or _g_l(state):
        posting.ws_post_rrn = _move.move_numeric(
            state.file_access.rrn, _POST["ws-post-rrn"], sending_field=_FA["rrn"]
        )
        _facade.gl_posting_write(state.ctx_posting)
        state.file_access.rrn = _arith.add_to(
            1, receiver_value=state.file_access.rrn, receiving=_FA["rrn"]
        )

    # [L672-L674] THE 99-ITEM BATCH CAP. ``items`` is ``pic 99``, so a batch cannot hold
    # a hundredth posting.
    if batch.items == 99:
        _bl_close(state)
        _bl_open(state)
    _bl_write__main_exit(state)


def _bl_write__main_exit(state: _State) -> None:
    """``main-exit. exit section.`` [sales/sl100.cbl:L676]."""
    return


def _bl_close(state: _State) -> None:
    """``BL-Close section.`` [sales/sl100.cbl:L679-L696] - close the GL batch.

    Two of the migration's registered anomalies meet in these fifteen lines: the
    unexplained ``postings`` write (A-17) and the terminating period whose ABSENCE in
    ``sl060`` is A-1.
    """
    _facade.gl_batch_write(state.ctx_batch)
    # [L683-L689] the write-failure report. Diagnostics only: the display, the status
    # decode and the acknowledgement pause.
    if state.file_access.fs_reply != FsReply.SUCCESS:
        _log.error("%s", _SL132)
        _eval_status(state)
        # [L686-L687] ``display fs-reply`` / ``display exception-msg``.  The status
        # and the NAME ``Eval-Status`` just decoded for it - a fixed 25-character
        # string from a static table keyed on ``fs-reply``, so it is never driver text
        # and never a business value.
        _log.error("%s %s", state.file_access.fs_reply, state.exception_msg)
        # [L688] ``display SL002`` and [L689] ``accept ws-reply``.  BOTH
        # DROPPED - the key-press instruction and the key press.  The substantive
        # diagnostics are the two records above.

    # ANOMALY A-17 [sales/sl100.cbl:L691] - ``move RRN to postings. *> Why ?`` The
    # maintainer does not know why this is here and says so, twice.
    if _irs_both_used(state) or _g_l(state):
        state.system.general_ledger_block.postings = _move.move_numeric(
            state.file_access.rrn, _SYS["postings"], sending_field=_FA["rrn"]
        )
    _facade.gl_batch_close(state.ctx_batch)

    # [L693-L696] IRS FAN-OUT SITES 6 and 7 of 7. ANOMALY A-1, THE DIVERGENCE - and here
    # the code is CORRECT.
    if _irs_used(state) or _irs_both_used(state):
        _facade.spl_posting_close(state.ctx_irs)
    if _irs_both_used(state) or _g_l(state):
        _facade.gl_posting_close(state.ctx_posting)
    _bl_close__main_exit(state)


def _bl_close__main_exit(state: _State) -> None:
    """``main-exit. exit section.`` [sales/sl100.cbl:L698]."""
    return


def _eval_status(state: _State) -> None:
    """``Eval-Status section.`` [sales/sl100.cbl:L700-L704].

    The body is ``copy "FileStat-Msgs.cpy" replacing STATUS by fs-reply msg by
    exception-msg`` [L703-L704] - a decode table from a file status to a message.
    (Note the lower-case ``msg`` in this program's ``REPLACING`` clause where
    ``sl060`` writes ``MSG``; and note that ``sl100`` names the section
    ``Eval-Status`` where ``sl060`` uses ``zz040-Evaluate-Message``,
    ``pl060``/``gl080`` use ``Evaluate-Message`` and ``sl055``/``pl055`` use
    ``a01-Eval-Status``.  Each program's own spelling is preserved.)

    Purely diagnostic: it produces text for a display and must not - and does
    not - alter control flow.

    THE SECTION EMITS NO LOG RECORD OF ITS OWN, and that is deliberate.  It contains
    no ``display`` at all - its whole body is the ``COPY``, which only *stores* - so a
    record here would be output the compiled program never produced (R-4), and it
    would duplicate the one its single caller emits from [L686-L687] immediately
    afterwards.  What the section does instead is what the frozen section does: fill
    ``exception-msg``.
    """
    # [L703-L704] the expanded ``EVALUATE``.  ``FsReply`` is an enumeration whose
    # member NAME is the condition the copybook's text conveys, so the rendering is
    # taken from there rather than a second copy of the 35-arm table being maintained
    # here - exactly as the purchase twin does it
    # [acas_posting/programs/pl100_payment_posting.py, ``_eval_status``].  ``FS-Reply``
    # is ``pic 99``, so an unmapped value must still render.
    try:
        _text = FsReply(int(state.file_access.fs_reply)).name.replace("_", " ")
    except ValueError:
        _text = f"UNMAPPED FILE STATUS {int(state.file_access.fs_reply):02d}"
    state.exception_msg = _move.move_alphanumeric(_text, _D["exception-msg"])
    # [L705] falls through to ``main-exit.`` L706.
    _eval_status__main_exit(state)


def _eval_status__main_exit(state: _State) -> None:
    """``main-exit. exit section.`` [sales/sl100.cbl:L706]."""
    return


# The four date sections.


def _date_wrapper(state: _State) -> Callable[[Maps03Ws], None]:
    """The ``maps04 section.`` of this program, as a callable."""

    def perform_maps04(maps03_ws: Maps03Ws) -> None:
        _maps04(state)

    return perform_maps04


def _zz050_validate_date(state: _State) -> None:
    """``zz050-Validate-Date section.`` [sales/sl100.cbl:L708-L733].

    FINDING-12 - THIS SECTION IS NEVER PERFORMED. There is no ``perform zz050`` anywhere
    in ``sales/sl100.cbl``; the section is boilerplate carried in with its three
    siblings and left unreached.
    """
    state.system.system_data_block.date_form = _dates.zz050_validate_date(
        state.ws_dates,
        state.maps03_ws,
        state.system.system_data_block.date_form,
        wrapper=_date_wrapper(state),
    )
    # The GO TO sites inside the consolidated body are classified there.
    _zz050_exit(state)


def _zz050_test_date(state: _State) -> None:
    """``zz050-test-date.`` [sales/sl100.cbl:L735-L738].

    R-5 requires a named function for this label, and this is it. It is NOT called by
    ``_zz050_validate_date`` above.
    """
    _dates.zz050_test_date(
        state.ws_dates, state.maps03_ws, wrapper=_date_wrapper(state)
    )


def _zz050_exit(state: _State) -> None:
    """``zz050-exit.`` [sales/sl100.cbl:L740-L741] - ``exit section.``"""
    return


def _zz060_convert_date(state: _State) -> None:
    """``zz060-Convert-Date section.`` [sales/sl100.cbl:L743-L773]."""
    state.system.system_data_block.date_form = _dates.zz060_convert_date(
        state.ws_dates,
        state.maps03_ws,
        state.system.system_data_block.date_form,
        wrapper=_date_wrapper(state),
    )
    _zz060_exit(state)


def _zz060_exit(state: _State) -> None:
    """``zz060-Exit.`` [sales/sl100.cbl:L775-L776] - ``exit section.``"""
    return


def _zz070_convert_date(state: _State) -> None:
    """``zz070-Convert-Date section.`` [sales/sl100.cbl:L778-L803].

    Renders the run date - ``to-day``, the fourth linkage parameter - into ``ws-date``
    in whichever of the UK, USA or International forms ``Date-Form`` selects.
    """
    state.system.system_data_block.date_form = _dates.zz070_convert_date(
        state.ws_dates, state.to_day, state.system.system_data_block.date_form
    )
    _zz070_exit(state)


def _zz070_exit(state: _State) -> None:
    """``zz070-Exit.`` [sales/sl100.cbl:L805-L806] - ``exit section.``"""
    return


def _maps04(state: _State) -> None:
    """``maps04 section.`` [sales/sl100.cbl:L808-L811].

    The thin wrapper around ``call "maps04" using maps03-ws`` [L811]. R-1 forbids
    reaching the compiled program, so the reimplementation in ``dates.maps04`` is called
    instead - epoch, six-part reject test and untouched-output-on-reject behaviour
    included.
    """
    _dates.maps04(state.maps03_ws)
    _maps04_exit(state)


def _maps04_exit(state: _State) -> None:
    """``maps04-exit.`` [sales/sl100.cbl:L813-L814] - ``exit section.``"""
    return


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
    """Run ``sl100`` - Sales Cash Posting.

    The five positional parameters are the ``PROCEDURE DIVISION USING`` list of
    [sales/sl100.cbl:L272-L276], in that order and with the source's own
    spelling: ``ws-calling-data``, ``system-record``, ``system-record-4``,
    ``to-day``, ``file-defs``.  This is the Sales/Purchase five-parameter linkage
    shape, one of the migration's three; the General Ledger family omits
    ``system-record-4`` and the IRS program takes neither the calling-data block
    nor the run date.

    ``ws_calling_data`` is passed through untouched: ``sl100`` reads and writes
    none of its seven fields [copybooks/wscall.cob:L6-L14].  It is a parameter
    because the COBOL declares it, and it is declared because the caller -
    ``sales/sales.cbl`` ``load11.`` [sales/sales.cbl:L790-L797] - routes every
    dispatch through one common ``CALL``.

    ``to_day`` is the run date as ``pic x(10)`` text, DD/MM/CCYY; the binary
    ``Run-Date`` arrives on ``system_record``.  Those two are the only date
    observables, and pinning them is what makes two runs of a scenario
    byte-identical (R-6).  Nothing here reads a clock.

    :param ok_to_post: the run-confirm of [sales/sl100.cbl:L310-L319], which
        gates every database write in the program.  ``False`` reproduces the
        ``"NO"`` branch at [L316-L317] exactly: control transfers to
        ``menu-exit`` before a single file is opened, so the run has no effect
        whatsoever.  ⛔ REQUIRED, WITH NO DEFAULT.  The field's own ``value
        spaces`` [L167] is not an answer, [L313] moves spaces into it again
        immediately before the accept, and [L318-L319] re-prompts on a blank, so
        the frozen program HAS no default: only ``"YES"`` proceeds and only
        ``"NO"`` exits.  Agent Action Plan section 0.3.4 promotes a write-gating
        accept "with the COBOL default preserved", and where there is none to
        preserve a keyword default would invent one - in the direction that
        writes to the database.  An earlier draft defaulted this to ``True``.
        See AMBIGUITY Q-6.

    :param dal_options: keyword-only, and NOT one of the five linkage operands.
        Forwarded to every facade ``PERFORM`` this program issues, and the
        declaration it exists for is the caller's transport-security policy.  The
        frozen program has no counterpart because its bridge has none: transport
        is compiled into ``cobmysqlapi.c`` [common/otm3MT.cbl:L459] rather than
        declared by the COBOL.  ``None`` - the default - declares nothing, which
        every handler resolves FAIL-CLOSED: a Unix socket or a loopback address is
        permitted and any other target refused.  A run against the containerised
        parity harness must therefore say so explicitly,
        ``dal_options={"transport": TransportSecurity(isolated_oracle=True)}``,
        and a run against a real server should be given
        ``TransportSecurity(ca_file=...)``.  It changes no status, no statement,
        no arithmetic and no write order.

    :param dal_options: keyword-only, and NOT one of the five linkage operands.
        Forwarded to every facade ``PERFORM`` this program issues, and the
        declaration it exists for is the caller's transport-security policy.  The
        frozen program has no counterpart because its bridge has none: transport
        is compiled into ``cobmysqlapi.c`` [common/otm3MT.cbl:L459] rather than
        declared by the COBOL.  ``None`` - the default - declares nothing, which
        every handler resolves FAIL-CLOSED: a Unix socket or a loopback address is
        permitted and any other target refused.  A run against the containerised
        parity harness must therefore say so explicitly,
        ``dal_options={"transport": TransportSecurity(isolated_oracle=True)}``,
        and a run against a real server should be given
        ``TransportSecurity(ca_file=...)``.  It changes no status, no statement,
        no arithmetic and no write order.

    Nothing is returned.  Every effect is a mutation of the linkage records or a
    row written through the facade, exactly as in the COBOL.
    """
    state = _new_state(
        ws_calling_data,
        system_record,
        system_record_4,
        to_day,
        file_defs,
        ok_to_post=ok_to_post,
        dal_options=dal_options,
    )

    if not _init01(state):
        _menu_exit(state)
        return

    _menu_return(state)

    if not _acpt_xrply(state):
        _menu_exit(state)
        return

    # FALL-THROUGH from [L330] into ``loop.`` [L331].
    while True:
        outcome = _loop(state)
        if outcome == _Flow.CONTINUE_LOOP:
            continue
        if outcome == _Flow.LEAVE_LOOP:
            break
        _cust_update(state)
        # GO TO class 1 [sales/sl100.cbl:L433] -> ``loop.`` L331. This is the sixth
        # class-1 site.
        continue

    # ``main-end.`` [sales/sl100.cbl:L435] - the class-2 post-loop block, placed after
    # the loop in full.
    _main_end(state)

    _menu_exit(state)
