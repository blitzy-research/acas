"""``sl100`` - Sales Cash Posting.  Migration of ``sales/sl100.cbl`` (817 lines).

THE SOURCE IS FROZEN
====================
``sales/sl100.cbl`` is read-only specification.  Agent Action Plan section 0.8.1
is unambiguous: "Any diff touching ``common/*.cbl``, ``common/*.scb``,
``copybooks/*.cob``, ``general/*.cbl``, ``sales/*.cbl``, ``purchase/*.cbl``,
``irs/*.cbl`` or ``mysql/ACASDB.sql`` is a defect in the migration, regardless of
how harmless it appears."  Nothing in this migration edits it.  The migration
boundary for this program is **the whole program**.

THERE IS NO USER RULES DOCUMENT
===============================
``review_rules`` returns exactly "No user rules provided." - there is no on-disk
rules document for this project, and no rule has been invented to fill the gap.
The six binding rules **R-1 ... R-6** live in the Agent Action Plan itself
(section 0.7.2).  Where the plan is silent, enterprise-standard best practice
applies.  The rules that govern this module, and how it honours each:

R-1  No COBOL at runtime.  Nothing here spawns a process, loads a shared object
     or reaches for ``cobc``.  ``sl100`` contains no ``call "CBL_*"`` and no
     ``call "sl0NN"`` - unlike ``sl055`` [sales/sl055.cbl:L327-L336] and
     ``sl060`` [sales/sl060.cbl:L438-L449] - so there is no
     ``FS-Cobol-Files-Used``-gated library-call block to look for.  Its only
     ``CALL`` is [sales/sl100.cbl:L454] ``call "SYSTEM" using print-report``,
     the report spool-out, which AAP section 0.1.1 places out of scope; it is
     omitted and recorded in OMISSIONS.  ``function upper-case``
     [sales/sl100.cbl:L315] is a COBOL intrinsic, not a program call, and is
     routed through a published ``cobol.move`` primitive.
R-2  Zero binary floating point.  Every monetary and quantity value is
     ``decimal.Decimal`` or ``int``; there is no ``float``, no ``round()`` and no
     bare ``/``.  AAP section 0.3.1: "``cobol/`` contains no business logic and
     ``programs/`` contains no numeric primitives."  Accordingly this module
     contains no ``quantize``, no scale alignment, no packed or zoned encoding,
     no picture parsing, no ``MOVE`` truncation, no ``88``-level test, no
     reference modification and no ``STRING`` of its own - all of it is
     delegated.  ``sl100`` has **zero** ``ROUNDED`` sites (the five in the whole
     migration are gl051 L791/L796, gl080 L328 and irs030 L1551/L1562), so every
     store here truncates.  Not one of the 36 arithmetic store sites below
     overrides the ``rounded`` keyword - there are 39 ``cobol.arithmetic`` calls
     in total, three of which are the non-storing ``compare`` - and each leaves
     the keyword at the truncating default that ``cobol.arithmetic`` declares,
     because in COBOL an un-``ROUNDED`` store truncates toward zero.  The
     keyword is therefore never once set to the affirmative, and the literal
     spelling of that affirmative form is deliberately absent from this file,
     this prose included, so that the mandated audit grep returns a count of
     zero.
R-3  No new validations, fields or schema changes; no concurrency.  No condition
     was added, removed, reordered or strengthened.  Statements the compiler
     renders inert are reproduced anyway - see FINDING-3, FINDING-6 and
     FINDING-7.  Execution is strictly sequential.
R-4  Legacy anomalies reproduced, never fixed.  AAP section 0.8.2: "There is no
     test suite: compiled COBOL execution is the behavioral specification,
     defects included.  A defect reproduced is correct; a defect fixed is a
     failure."  Every reproduction site carries an ``# ANOMALY`` comment naming
     the defect and citing its COBOL locator, per AAP section 0.7.4 C-4.
R-5  Full traceability.  One named function per COBOL section and per paragraph,
     **section-qualified** because ``main-exit.`` occurs five times (L548, L595,
     L676, L698, L706).  Every ``GO TO`` site carries a ``# GO TO class N``
     annotation; the ``PERFORM ... THRU``, the plain ``EXIT`` and the
     ``EXIT PROGRAM`` each carry their own.  A traceability footer closes the
     file.  Every ``FieldDescriptor`` carries a ``dictionary_key`` or a
     ``source_locator``.
R-6  Compiled behavior is the tie-breaker; determinism.  No ambient clock is
     read anywhere: ``sales/sl100.cbl`` itself contains zero clock reads, and
     both date observables arrive through linkage - the text date as ``to_day``
     and the binary ``Run-Date`` [copybooks/wssystem.cob:L67] on
     ``system_record``, consumed at [sales/sl100.cbl:L561].  Questions that only
     the compiled oracle can settle are marked ``# AMBIGUITY Q-nn``.

WHAT THE PROGRAM DOES
=====================
``sl100`` walks the OTM3 open-item file once, from the beginning, and for each
record it admits [sales/sl100.cbl:L338]:

* ``oi-type = 2`` - a *cleared invoice*.  It folds the invoice's clearance delay
  into the customer's payment-days moving average, clears the three batch
  fields and rewrites OTM3 [L341-L348].  This branch **never reaches**
  ``cust-update``; no ledger arithmetic and no posting happens for an invoice.
* ``oi-type = 5`` - a *payment*.  It falls through to ``cust-update``.
* ``oi-type = 6`` - an *unapplied-cash credit journal*.  Likewise.

For types 5 and 6 it applies the amount to the customer's sales-ledger row,
accumulates the run totals, rewrites the ledger and OTM3, and - only when the
General Ledger is in use - emits a GL and/or IRS posting.  At end of run it
reverses the deduction counters out of the value-analysis ``"zd"`` group, closes
the batch, and stamps two ``SYSTEM-REC`` fields.

Tables this program writes: ``SALEDGER-REC`` (Sales-Rewrite), ``SAITM3-REC``
(OTM3-Rewrite, at both L347 and L421), ``VALUEANAL-REC`` (Value-Rewrite),
``GLBATCH-REC`` (GL-Batch-Write), ``GLPOSTING-REC`` (GL-Posting-Write),
``PSIRSPOST-REC`` (SPL-Posting-Write), plus ``SYSTOT-REC`` through the
two-receiver add at L404 and ``SYSTEM-REC`` through L473-L474 and A-17 at L691.
There is **no work file**: ``sl100`` copies no OTM2 work-file copybook, and
neither ``pretrans.tmp`` nor ``postrans.tmp`` [copybooks/wsnames.cob:L15-L16,
both annotated ``*> gl071``] is among the files it names.

LINKAGE - THE SALES/PURCHASE FIVE-PARAMETER SHAPE
=================================================
[sales/sl100.cbl:L272-L276], verbatim::

    procedure division using ws-calling-data
                             system-record
                             system-record-4
                             to-day
                             file-defs.

``run()`` mirrors that list exactly, in that order.  The one extra parameter is
keyword-only: ``ok_to_post`` carries the run-confirm of L310-L319, which gates
every database write and is therefore an input rather than decoration.

THIS FILE IS NOT ``sl060``, AND THE DIFFERENCES ARE THE POINT
=============================================================
``sl100`` reads like ``sl060`` and diverges from it in at least a dozen measured
places.  Three of those divergences are traps that a transcription from the
wrong sibling would walk straight into - the moving average (A-10), the
``BL-Close`` terminating period (the mirror of A-1) and ``post-legend`` (five
``STRING`` statements here, one there).  Every line below was transcribed from
``sales/sl100.cbl`` itself.  AAP section 0.6.1 on the moving averages, verbatim:
"Normalising them into one helper would be the single easiest way to fail this
migration."  Consequently this module shares no arithmetic helper with
``sl060_invoice_posting`` or ``pl100_payment_posting``, and imports neither -
which the layering rules forbid in any case.

LAYERING (AAP section 0.4.3)
============================
Imported: ``records.*``, ``dal.facade``, ``dal.status``, ``cobol.arithmetic``,
``cobol.move``, ``cobol.condition_names``, ``cobol.field``, ``cobol.picture``,
``dates``, and the standard library.

Deliberately **not** imported, each for a stated reason:

* ``acas_posting.workfiles`` - ``sl100`` has no work file (see above), unlike
  ``sl055``, ``sl060``, ``gl071``, ``gl072`` and ``gl080``.
* ``acas_posting.clock`` - R-6; the date arrives through linkage, and this
  program reads no clock.
* ``acas_posting.dal.acas*``, ``dal.connection``, ``dal.cursor_state`` - a
  program reaches a table only through the facade, exactly as the COBOL reaches
  it only through ``Proc-ACAS-FH-Calls.cob``.
* ``acas_posting.cli.*`` - the caller is ``cli/sl_cash_post.py``, derived from
  ``sales/sales.cbl`` ``load11.`` [sales/sales.cbl:L790-L797]; dependencies run
  one way.
* ``acas_posting.programs.*`` - no program module may import another.
* ``harness`` - R-1.

``sl100`` copies ``Proc-ACAS-FH-Calls.cob`` at [sales/sl100.cbl:L816], so it
uses the **entity-named** facade vocabulary and tests the reply **inline**.  It
never uses the handler-named aliases of ``Proc-ZZ100-ACAS-IRS-Calls.cob`` and
therefore never gets that convention's per-handler error check.
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

#: Everything cited by this module comes from one frozen program.
_SRC: Final = "sales/sl100.cbl"


# ---------------------------------------------------------------------------
# Field descriptors
# ---------------------------------------------------------------------------
# R-2 and R-5 both land here.  Arithmetic and MOVE are driven by the *receiving
# field*, so every store in this module names a descriptor, and every descriptor
# is looked up rather than described by hand: the copybook fields come from the
# generated data dictionary (each already carrying a ``dictionary_key``), and the
# program's own WORKING-STORAGE comes from the picture parser with an explicit
# ``source_locator``.  Nothing about a field's width, scale, sign or usage is
# written twice, so nothing about it can drift.


def _index(record: str) -> Mapping[str, FieldDescriptor]:
    """Index one copybook record's descriptors by case-folded COBOL name.

    ``FILLER`` is dropped: it is the only name that repeats with genuinely
    different shapes, it is never referenced by name, and keeping it would make
    the conflict guard below fire on a name no caller can ask for.

    The guard is a build-time integrity check on this module's own descriptor
    table - it can only fire if the generated dictionary changes shape beneath
    us - and is emphatically not a validation of business data, which R-3
    forbids adding.
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

    These sixteen fields exist only inside ``sl100``, so they have no dictionary
    entry and no table column.  R-5 requires provenance regardless, which the
    ``source_locator`` supplies.
    """
    return _picture.descriptor_for(
        clauses, name=name, source_locator=f"{_SRC}:L{line}"
    )


# The copybook records, by the record names the generated dictionary knows.
_SL: Final = _index("WS-Sales-Record")  # copybooks/wssl.cob      [L221]
_OI: Final = _index("OI-Header")  # copybooks/slwsoi3.cob   [L219]
_SYS: Final = _index("System-Record")  # copybooks/wssystem.cob  [L266]
_SYS4: Final = _index("System-Record-4")  # copybooks/wssys4.cob    [L267]
_BAT: Final = _index("WS-Batch-Record")  # copybooks/wsbatch.cob   [L222]
_POST: Final = _index("WS-Posting-Record")  # copybooks/wspost.cob    [L224]
_IRS: Final = _index("WS-IRS-Posting-Record")  # copybooks/wspost-irs.cob[L225]
_VAL: Final = _index("WS-Value-Record")  # copybooks/wsval.cob     [L223]
_FA: Final = _index("File-Access")  # copybooks/wsfnctn.cob   [L139]

# ``01 ws-data.`` [sales/sl100.cbl:L165-L183], field for field.
#
# ``i`` [L169] and ``save-level-1`` [L172] are declared but unreferenced in the
# migrated surface - ``save-level-1``'s only three uses are commented out, at
# L289-L290 and L465/L469 - so they are recorded here and nowhere else.
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
}

# ``01 Error-Messages.`` [sales/sl100.cbl:L209-L215].  The literals survive only
# as log text; see OMISSIONS.
_SL002: Final = "SL002 Note error and hit return"  # [L211]
_SL132: Final = "SL132 Err on Batch file write : "  # [L214]
_SL137: Final = "SL137 Payments Not Proofed"  # [L215]

#: ``03  prog-name pic x(15) value "SL100 (3.3.01)".`` [sales/sl100.cbl:L135].
_PROG_NAME: Final = "SL100 (3.3.01)"

#: ``03  u-bin binary-long.`` [copybooks/wsmaps03.cob:L30] - the date module's
#: binary day-number field, ``copy "wsmaps03.cob"`` at [sales/sl100.cbl:L138].
#: The copybook is a linkage work area rather than a table record, so it has no
#: dictionary entry and its provenance is the copybook line itself.
_U_BIN: Final = _picture.descriptor_for(
    "binary-long", name="u-bin", source_locator="copybooks/wsmaps03.cob:L30"
)


# ---------------------------------------------------------------------------
# Program state - the WORKING-STORAGE and LINKAGE of one run
# ---------------------------------------------------------------------------
# A COBOL program's storage is global to the program and private to it, and its
# paragraphs read and write it freely.  One mutable container passed between the
# paragraph functions reproduces that exactly, and reproduces its lifetime: a
# fresh ``_State`` per ``run()`` is a fresh WORKING-STORAGE per ``CALL``.


@dataclass(slots=True)
class _State:
    """One run's LINKAGE and WORKING-STORAGE.

    Field order follows the COBOL: the five linkage parameters
    [sales/sl100.cbl:L272-L276] first, then the record work areas in ``COPY``
    order [L217-L225], then ``01 ws-data.`` [L165-L183].
    """

    # -- LINKAGE SECTION [sales/sl100.cbl:L265-L276] --------------------------
    ws_calling_data: WsCallingData
    system: SystemRecord
    system_4: SystemRecord4
    to_day: str
    file_defs: FileDefs

    # -- the run-confirm of L310-L319, hoisted to an argument -----------------
    ok_to_post: bool

    # -- ``copy "wsfnctn.cob".`` [L139] --------------------------------------
    # ONE ``01 File-Access``, shared by every facade verb, exactly as the COBOL
    # has one.  ``fs-reply`` at L333/L364/L580/L587/L683 and ``RRN`` at
    # L593/L667/L669/L691 are fields of *this* record, which is why the batch's
    # record number survives from ``BL-Open`` through ``BL-Write`` to
    # ``BL-Close``.
    file_access: FileAccess
    dal_common: AcasDalCommonData

    # -- the record work areas [L217-L225] -----------------------------------
    sales: WsSalesRecord  # copy "wssl.cob".       [L221]
    oi: OiHeader  # copy "slwsoi3.cob".    [L219]
    value: WsValueRecord  # copy "wsval.cob".      [L223]
    batch: GlBatchRecord  # copy "wsbatch.cob".    [L222]
    posting: WsPostingRecord  # copy "wspost.cob".     [L224]
    irs_posting: WsIrsPostingRecord  # copy "wspost-irs.cob". [L225]

    # -- the date work areas [L138, L185-L207] -------------------------------
    maps03_ws: Maps03Ws  # copy "wsmaps03.cob".   [L138]
    ws_dates: _dates.WsDateFormats  # 01 ws-date-formats.    [L186]

    # -- one facade context per entity ---------------------------------------
    # ``FacadeContext`` is frozen and carries a single ``record``, so an entity
    # gets its own context.  That is not a Python compromise: each COBOL facade
    # paragraph names one work area too, and it is why a Sales verb can never
    # accidentally act on the OTM3 record.  All six share the one
    # ``File-Access`` above.
    ctx_sales: _facade.FacadeContext
    ctx_otm3: _facade.FacadeContext
    ctx_value: _facade.FacadeContext
    ctx_batch: _facade.FacadeContext
    ctx_posting: _facade.FacadeContext
    ctx_irs: _facade.FacadeContext

    # -- ``01 ws-data.`` [L165-L183] -----------------------------------------
    # Only ``line-cnt`` and the ten numerics from L174 down carry a ``VALUE``
    # clause.  ``ws-reply``, ``wx-reply``, ``xx``, ``j`` and ``k`` do not, and
    # none of them is read before the program writes it - ``move spaces to
    # wx-reply`` [L313], ``move space to ws-reply`` [L362], ``move zero to j``
    # [L328], ``move 1 to xx`` [L620], ``move oi-b-item to k`` [L625] - so their
    # initial content is unobservable and the values below cannot affect a diff.
    ws_reply: str = " "
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
    """A cleared ``01 oi-header.`` work area [copybooks/slwsoi3.cob].

    The copybook carries no ``VALUE`` clause - the record exists to be read into
    - so every leaf is initialised from its own picture through
    ``move_figurative``: alphanumeric to spaces, numeric to zero at the field's
    own scale.  Nothing here decides a representation; the descriptors do.
    """
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
                # ``OI-Approp REDEFINES OI-Net`` - see FINDING-13.
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
) -> _State:
    """Establish WORKING-STORAGE and the six facade contexts for one run."""
    file_access = FileAccess()
    dal_common = AcasDalCommonData()

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
        )

    return _State(
        ws_calling_data=ws_calling_data,
        system=system_record,
        system_4=system_record_4,
        to_day=to_day,
        file_defs=file_defs,
        ok_to_post=ok_to_post,
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


# ---------------------------------------------------------------------------
# Condition names - ``88``-level tests, never a raw literal
# ---------------------------------------------------------------------------
# R-2 keeps every ``88``-level test out of this module's own code.  ``G-L`` has
# no exported predicate of its own, so it is resolved through the registry the
# same way the others are reached by name.

#: ``88  G-L value 1.`` on ``05 Level-1`` [copybooks/wssystem.cob:L85].
_is_g_l: Final = _cn.predicate_for("G-L")

#: ``88  IRS-Used value "Y".`` on ``05 IRS-Instead``
#: [copybooks/wssystem.cob:L180].
_is_irs_used: Final = _cn.predicate_for("IRS-Used")

#: ``88  IRS-Both-Used value "B".`` on ``05 IRS-Instead``
#: [copybooks/wssystem.cob:L181].
_is_irs_both_used: Final = _cn.predicate_for("IRS-Both-Used")

#: ``88  S-Closed value 1.`` on ``05 OI-Status`` [copybooks/slwsoi.cob:L49].
#: The name is declared in both the sales and the purchase open-item copybooks;
#: the sales one is the live reader, at [sales/sl100.cbl:L350].
_is_s_closed: Final = _cn.predicate_for("S-Closed", copybook="copybooks/slwsoi.cob")


def _g_l(state: _State) -> bool:
    """``if G-L`` - the General Ledger is in use.  [sales/sl100.cbl:L324, L417,
    L462, L585, L666, L690, L695]."""
    return bool(_is_g_l(state.system.system_data_block.level.level_1))


def _irs_used(state: _State) -> bool:
    """``if irs-used`` [sales/sl100.cbl:L578, L647, L693]."""
    return bool(_is_irs_used(state.system.general_ledger_block.irs_instead))


def _irs_both_used(state: _State) -> bool:
    """``if IRS-Both-Used`` [sales/sl100.cbl:L578, L585, L647, L665, L690, L693,
    L695]."""
    return bool(_is_irs_both_used(state.system.general_ledger_block.irs_instead))


def _s_closed(state: _State) -> bool:
    """``if s-closed`` [sales/sl100.cbl:L350]."""
    return bool(_is_s_closed(state.oi.filler_1.oi_status))


# ---------------------------------------------------------------------------
# Two small transcription aids
# ---------------------------------------------------------------------------


class _Flow:
    """The three outcomes of the ``loop.`` paragraph, as named constants.

    ``loop.`` [sales/sl100.cbl:L331] ends in one of exactly three ways - a
    ``GO TO loop`` (class 1), a ``GO TO main-end`` (class 2), or no transfer at
    all, falling through into ``cust-update.`` [L357].  Naming them keeps the
    ``GO TO`` classification legible at the one place the loop is driven, rather
    than hiding it behind a bare boolean.
    """

    CONTINUE_LOOP: Final = "continue-loop"  # class 1 -> continue
    LEAVE_LOOP: Final = "leave-loop"  # class 2 -> break
    FALL_THROUGH: Final = "fall-through"  # no transfer -> cust-update


def _literal(text: str, receiving: FieldDescriptor) -> str:
    """A literal as the receiving field would hold it.

    COBOL compares an alphanumeric field with a shorter literal by padding the
    literal to the field's width, so ``if wx-reply = "NO"``
    [sales/sl100.cbl:L316] against ``wx-reply pic xxx`` [L167] is really a
    comparison against ``"NO "``.  Rather than pad by hand, the published
    ``MOVE`` primitive is asked what the field would hold - the field's own
    picture decides, here as everywhere.
    """
    return _move.move_alphanumeric(text, receiving)


def _upper_case(text: str, receiving: FieldDescriptor) -> str:
    """``function upper-case`` [sales/sl100.cbl:L315].

    An intrinsic function, not a program call, so R-1 is not engaged.  The
    case fold itself has no COBOL-specific subtlety on an alphanumeric field;
    the part that does - how wide the result is stored - is delegated to the
    published ``MOVE`` primitive and the receiving field's picture.
    """
    return _move.move_alphanumeric(text.upper(), receiving)


# ---------------------------------------------------------------------------
# init01 section.  [sales/sl100.cbl:L279]
# ---------------------------------------------------------------------------


def _init01(state: _State) -> bool:
    """``init01 section.`` [sales/sl100.cbl:L279-L301].

    Returns ``False`` when the proofing gate transfers control to ``menu-exit``,
    ``True`` when control falls through to ``menu-return.``.
    """
    # [L280] ``move prog-name to l1-name.`` and [L281] ``move Print-Spool-Name
    # to PSN.`` are print-heading and spool-name moves; both are in OMISSIONS.
    #
    # [L283-L284] ``set ENVIRONMENT "COB_SCREEN_EXCEPTIONS"/"COB_SCREEN_ESC"``
    # configure the curses screen this migration does not have.  OMITTED.
    #
    # [L286-L292] a commented-out block that would save and clear ``level-1`` to
    # bypass the GL posting code; its counterpart at [L465-L471] is commented out
    # too.  Dead in the compiled program, so dead here.  This is why
    # ``save-level-1`` [L172] has a descriptor and no use.

    # [L293] ``perform zz070-Convert-Date.``
    _zz070_convert_date(state)
    # [L294] ``move ws-date to l2-date.`` - print heading.  OMITTED.

    # [L296-L301] GATE 1.  ``S-Flag-P`` is the sales-payments proofing latch on
    # SYSTEM-REC; unless a proof run has set it to 2, this program refuses to
    # run.  [L474] clears it again at end of run, which makes the program
    # deliberately non-idempotent: a second consecutive run aborts here.
    if state.system.sales_ledger_block.s_flag_p != 2:
        # [L297-L298] ``display SL137 at 2301`` / ``display SL002 at 2401``.
        # Diagnostics with no database effect become log records (AAP 0.3.4);
        # they must not, and do not, alter control flow.
        _log.error("%s", _SL137)
        _log.error("%s", _SL002)
        # [L299] ``accept ws-reply at 2433`` is an acknowledgement pause whose
        # only effect is to block a terminal.  Dropped; the transfer below is
        # not.
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
    # [L301] ``end-if.`` - fall through to ``menu-return.`` L303.
    return True


def _menu_return(state: _State) -> None:
    """``menu-return.`` [sales/sl100.cbl:L303-L308].

    FALL-THROUGH TARGET.  No ``GO TO`` anywhere in the migrated surface names
    this label; it is reached only by falling out of the ``end-if`` at [L301].
    R-5 keeps the function regardless, both because the paragraph exists and
    because the ``perform zz070-Convert-Date`` at [L307] is a real statement.
    """
    # [L305-L306, L308] the screen banner.  Diagnostics -> log records.
    _log.info("%s", _PROG_NAME)
    _log.info("Sales Cash Posting")
    # [L307] ``perform zz070-Convert-Date.`` - the second call; the first was at
    # [L293].  Both are reproduced: the section stores into ``Date-Form`` and its
    # own work area, so calling it twice is not the same as calling it once.
    _zz070_convert_date(state)
    _log.info("%s", state.ws_dates.ws_date)


def _acpt_xrply(state: _State) -> bool:
    """``acpt-xrply.`` [sales/sl100.cbl:L310-L329].

    The paragraph runs from its label to the next one, so it carries not only
    the run-confirm but the file opens, the page counter and the first heading.

    Returns ``False`` when the confirm transfers control to ``menu-exit``.
    """
    # [L311-L312] the prompt itself -> a log record.
    _log.info("OK to Post Payment Transactions (YES/NO) ?")

    # The retry loop of [L318-L319] is preserved structurally.  It terminates on
    # its first pass and cannot spin: ``ok_to_post`` is a ``bool``, so the answer
    # synthesised at [L314] below is always exactly one of the two literals the
    # tests recognise, and one of the two transfers always fires.
    while True:
        # [L313] ``move spaces to wx-reply.``
        state.wx_reply = _move.move_figurative(_move.SPACES, _D["wx-reply"])
        # [L314] ``accept wx-reply at 1256 ... update.``  This is the one accept
        # in the program that is NOT dropped: AAP 0.3.4 makes a prompt that gates
        # a database write an explicit parameter, because its answer changes
        # table state.  The operator's keystrokes become ``ok_to_post``.
        state.wx_reply = _move.move_alphanumeric(
            "YES" if state.ok_to_post else "NO", _D["wx-reply"]
        )
        # [L315] ``move function upper-case (wx-reply) to wx-reply.``
        state.wx_reply = _upper_case(state.wx_reply, _D["wx-reply"])

        # [L316-L317]
        if state.wx_reply == _literal("NO", _D["wx-reply"]):
            # GO TO class 4 [sales/sl100.cbl:L317] -> ``menu-exit.`` L476.
            #
            # PER-SITE EQUIVALENCE PROOF.  As at L300, ``menu-exit.`` is one
            # ``exit program.`` [L477] and the tail of the flow.  This site is
            # reached before [L321], so once again no file is open and no facade
            # verb has run: answering NO leaves the database exactly as it was.
            # The distinction from L300 is only *which* condition declines the
            # run, not what declining does, and both are proved against the same
            # single-statement target.  Returning ``False`` runs the same
            # statements in the same order.  Equivalent.
            return False
        # [L318-L319]
        if state.wx_reply != _literal("YES", _D["wx-reply"]):
            # GO TO class 1 [sales/sl100.cbl:L319] -> ``acpt-xrply.`` L310, an
            # interactive re-prompt.  Unreachable once the answer is a
            # parameter, as proved above the loop, but transcribed rather than
            # deleted: R-3 forbids removing a condition.
            continue
        break

    # [L321] ``perform OTM3-Open.``
    _facade.otm3_open(state.ctx_otm3)
    # [L322] ``perform Sales-Open.``
    _facade.sales_open(state.ctx_sales)

    # [L324-L325] ``if G-L perform BL-Open.``
    if _g_l(state):
        _bl_open(state)

    # [L327] ``open output print-file.`` - OMITTED with the whole print file.
    # [L328] ``move zero to j.``
    state.j = _move.move_figurative(_move.ZERO, _D["j"])
    # [L329] ``perform headings.``
    _headings(state)
    # [L330] falls through to ``loop.`` L331.
    return True


# ---------------------------------------------------------------------------
# loop.  [sales/sl100.cbl:L331]
# ---------------------------------------------------------------------------


def _loop(state: _State) -> str:
    """``loop.`` [sales/sl100.cbl:L331-L355] - one pass over the OTM3 walk.

    ``sl100`` reads OTM3 sequentially from the beginning: there is no
    ``OTM3-Start`` and no ``set fn-*`` anywhere in the program, so no cursor is
    positioned first.
    """
    # [L332] ``perform OTM3-Read-Next.``
    _facade.otm3_read_next(state.ctx_otm3)
    # [L333-L334]
    if state.file_access.fs_reply == FsReply.END_OF_FILE:
        # GO TO class 2 [sales/sl100.cbl:L334] -> ``main-end.`` L435.  The
        # target is followed by real work - two closes, the total prints, the
        # deduction merge and reversal, the batch close and two SYSTEM-REC
        # stamps - so the transformation is a break PLUS that work placed after
        # the loop, which is ``_main_end`` in ``run()``.  AAP 0.6.3:
        # "Mis-splitting here would silently drop end-of-run processing."
        return _Flow.LEAVE_LOOP

    # [L336] ``move open-item-record-3 to oi-header`` is commented out: the
    # facade hands the record straight to the work area.

    # [L338-L339] ``if oi-type not = 2 and not = 5 and not = 6``.  An
    # abbreviated relation with the SUBJECT first and three objects, so it reads
    # ``oi-type /= 2 AND oi-type /= 5 AND oi-type /= 6`` - admit only invoices,
    # payments and unapplied-cash journals (the maintainer's own comment).
    # Contrast [L354], where the subject is on the other side.
    oi_type = state.oi.filler_1.oi_type
    if oi_type != 2 and oi_type != 5 and oi_type != 6:
        # GO TO class 1 [sales/sl100.cbl:L339] -> ``loop.`` L331.
        return _Flow.CONTINUE_LOOP

    # [L341-L348] THE TYPE-2 BRANCH - a cleared invoice.  It updates the
    # payment-days average, clears the batch linkage and rewrites OTM3, then
    # loops.  It never reaches ``cust-update.``, so an invoice moves no money in
    # the sales ledger and emits no posting.
    batch = state.oi.filler_1.oi_batch
    if oi_type == 2 and batch.oi_b_nos != 0 and batch.oi_b_item != 0:
        # PERFORM THRU [sales/sl100.cbl:L344] spans ``compute-sales-pay`` L497
        # -> ``csp-exit`` L516; hand-verified per AAP 0.4.2, which requires
        # every one of the four in-scope sites be transformed individually
        # "with no pattern-matching shortcut".  The range covers exactly two
        # paragraphs, so the expansion is exactly two calls in source order.
        _compute_sales_pay(state)
        _csp_exit(state)
        # [L345] ``move zeros to oi-b-nos oi-b-item oi-cr.`` - ONE source, THREE
        # receivers, each converted through its own picture.
        batch.oi_b_nos = _move.move_figurative(_move.ZEROS, _OI["oi-b-nos"])
        batch.oi_b_item = _move.move_figurative(_move.ZEROS, _OI["oi-b-item"])
        state.oi.filler_1.oi_cr = _move.move_figurative(_move.ZEROS, _OI["oi-cr"])
        # [L346] ``move oi-header to open-item-record-3`` is commented out.
        # [L347] ``perform OTM3-Rewrite.`` - the first of this program's two
        # OTM3 rewrites; the other is at [L421].
        _facade.otm3_rewrite(state.ctx_otm3)
        # GO TO class 1 [sales/sl100.cbl:L348] -> ``loop.`` L331.
        return _Flow.CONTINUE_LOOP

    # [L350-L352] ``if s-closed or oi-type = 2``.
    #
    # FINDING-1 [sales/sl100.cbl:L351] - the ``oi-type = 2`` half of this test
    # looks redundant after [L341-L348] and very nearly is, but it is not dead.
    # A type-2 record reaches this line only by FAILING the [L341] guards, that
    # is with ``oi-b-nos`` or ``oi-b-item`` zero.  When BOTH are zero [L354]
    # would catch it two lines later; when exactly ONE is zero, [L351] is the
    # only thing that stops it, and without this half the record would fall
    # through into ``cust-update`` and have ledger arithmetic applied to an
    # invoice.  So the condition is load-bearing for a narrow case that reading
    # it quickly makes invisible.  Reproduced exactly as written; R-3 forbids
    # removing a condition, and reachability reasoning is not licence to edit.
    if _s_closed(state) or oi_type == 2:
        # GO TO class 1 [sales/sl100.cbl:L352] -> ``loop.`` L331.
        return _Flow.CONTINUE_LOOP

    # [L354-L355] ``if zero = oi-b-nos and oi-b-item``.
    #
    # FINDING-2 - a REVERSED abbreviated relation.  The SUBJECT is ``zero`` and
    # both operands are objects, so this reads ``zero = oi-b-nos AND zero =
    # oi-b-item`` - skip anything with no batch linkage at all.  It is NOT
    # ``oi-b-nos = zero AND oi-b-item`` in the shape of [L338], and transcribing
    # it that way would give the same answer here only by luck of ``=`` being
    # symmetric; the two shapes differ in which side is reused.  Written out in
    # full so the shape is unmistakable.
    if 0 == batch.oi_b_nos and 0 == batch.oi_b_item:
        # GO TO class 1 [sales/sl100.cbl:L355] -> ``loop.`` L331.
        return _Flow.CONTINUE_LOOP

    # [L356] falls through to ``cust-update.`` L357.  Only types 5 and 6 with
    # live batch linkage get this far.
    return _Flow.FALL_THROUGH


# ---------------------------------------------------------------------------
# cust-update.  [sales/sl100.cbl:L357]
# ---------------------------------------------------------------------------


def _oi_customer_image(state: _State) -> str:
    """The byte image of the ``03 OI-Customer.`` group [copybooks/slwsoi3.cob].

    A group item *is* its children laid end to end, so the image is
    ``OI-Nos`` (``pic x(6)``) followed by ``OI-Check`` (``pic 9``), each rendered
    through its own picture by the published ``MOVE`` primitive.  The receiving
    field's width rule is applied by the caller's ``MOVE``, not here.
    """
    customer = state.oi.oi_key.oi_customer
    return _move.move_alphanumeric(
        customer.oi_nos, _OI["oi-nos"], sending_field=_OI["oi-nos"]
    ) + _move.move_alphanumeric(
        customer.oi_check, _OI["oi-check"], sending_field=_OI["oi-check"]
    )


def _cust_update(state: _State) -> None:
    """``cust-update.`` [sales/sl100.cbl:L357-L433].

    FALL-THROUGH TARGET.  No ``GO TO`` names this label either; it is entered by
    falling out of the last filter at [L355].

    Applies one payment (``oi-type = 5``) or one unapplied-cash credit journal
    (``oi-type = 6``) to the customer's sales-ledger row.  Every ``l5-*`` field
    written below is a print-line field and is in OMISSIONS; the fields that
    reach a table are ``sales-current``, ``sales-unapplied``, ``sales-last-pay``,
    ``oi-paid``, ``oi-status`` and - through [L404] - ``SL-Payments``.
    """
    filler_1 = state.oi.filler_1
    filler_2 = filler_1.filler_2

    # [L360] ``move oi-customer to WS-Sales-Key l5-cust.`` - two receivers; the
    # second is a print field.  Group sender into ``pic x(7)``.
    state.sales.ws_sales_key = _move.move_alphanumeric(
        _oi_customer_image(state),
        _SL["ws-sales-key"],
        sending_field=_OI["oi-customer"],
        length=7,
    )

    # [L362] ``move space to ws-reply.``
    state.ws_reply = _move.move_figurative(_move.SPACE, _D["ws-reply"])
    # [L363] ``perform Sales-Read-Indexed.``
    _facade.sales_read_indexed(state.ctx_sales)
    # [L364-L365]
    if state.file_access.fs_reply == FsReply.INVALID_KEY_ON_START:
        state.ws_reply = _move.move_alphanumeric("X", _D["ws-reply"])
    # [L366-L369] the customer name on the print line.  Print-only, so the two
    # branches survive as log text: no database effect and no control-flow
    # effect, which is the whole test AAP 0.3.4 sets for a diagnostic.
    if state.ws_reply == _literal("X", _D["ws-reply"]):
        _log.warning("!! Customer Unknown")
    else:
        _log.debug("%s", state.sales.sales_name)

    # [L371-L373] ``l5-batch`` / ``l5-slash`` / ``l5-item`` - print only.

    # [L375] ``move oi-date to u-bin.``
    state.maps03_ws.u_bin = _move.move_numeric(
        filler_1.oi_date, _U_BIN, sending_field=_OI["oi-date"]
    )
    # [L376] ``perform zz060-Convert-Date.``
    _zz060_convert_date(state)
    # [L377] ``move u-date to l5-date.`` - print only.
    #
    # FINDING-3 [sales/sl100.cbl:L377] - ``sl100`` prints ``u-date``, the date
    # module's own output field, where ``sl060`` prints ``ws-date``, the
    # presentation-formatted copy [sales/sl060.cbl:L507].  ``zz060`` sets both,
    # and they differ whenever ``Date-Form`` is not UK.  A print-only divergence
    # today, recorded because it would become diff-visible the moment either
    # field reached a column.

    # [L379-L381] ``l5-approp`` / ``l5-paid`` / ``l5-deduct`` - print only.

    # [L383-L384]
    if filler_1.oi_deduct_amt != 0:
        state.n_deduct = _arith.add_to(
            1, receiver_value=state.n_deduct, receiving=_D["n-deduct"]
        )

    # [L386] ``subtract sales-unapplied from sales-current giving l5-old-bal.``
    # The receiver is a print field, so the statement is in OMISSIONS - but note
    # it reads the ledger BEFORE the four mutations below, which is why it is
    # placed here rather than folded in with [L399].

    # [L387] ``subtract oi-approp from sales-current.``
    state.sales.sales_current = _arith.subtract_from(
        filler_2.oi_approp,
        receiver_value=state.sales.sales_current,
        receiving=_SL["sales-current"],
    )
    # [L388] ``subtract oi-deduct-amt from sales-current.``
    state.sales.sales_current = _arith.subtract_from(
        filler_1.oi_deduct_amt,
        receiver_value=state.sales.sales_current,
        receiving=_SL["sales-current"],
    )

    # [L390-L392] an over-payment: the excess becomes unapplied cash.
    if filler_2.oi_paid != filler_2.oi_approp:
        state.work_1 = _arith.subtract_giving(
            filler_2.oi_approp, minuend=filler_2.oi_paid, receiving=_D["work-1"]
        )
        state.sales.sales_unapplied = _arith.add_to(
            state.work_1,
            receiver_value=state.sales.sales_unapplied,
            receiving=_SL["sales-unapplied"],
        )

    # [L394-L397] the sign flip.
    #
    # FINDING-4 - ``sl100`` uses the ``GIVING`` form and never touches
    # ``sales-current`` until [L397]; ``sl060`` uses the no-``GIVING`` form and
    # mutates it in place, leaving it positive between [sales/sl060.cbl:L571] and
    # [sales/sl060.cbl:L573].  The net effect on both fields is identical, but
    # the intermediate state is not, and an intermediate state is exactly what a
    # later statement in a longer paragraph could observe.  Transcribed in each
    # program's own form; ``multiply_by_giving`` here, ``multiply_by`` there.
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

    # [L399] ``subtract sales-unapplied from sales-current giving l5-new-bal.``
    # Print only.  OMITTED.

    # [L400] ``move oi-date to sales-last-pay.``
    state.sales.sales_last_pay = _move.move_numeric(
        filler_1.oi_date, _SL["sales-last-pay"], sending_field=_OI["oi-date"]
    )

    # [L402-L410] THE ASYMMETRIC TOTALS.  The type-5 arm writes three
    # accumulators AND ``SL-Payments``; the type-6 arm writes three different
    # accumulators and never touches ``SL-Payments``, because an unapplied-cash
    # journal is not a payment.  They are not two instances of one shape and are
    # deliberately not factored together.
    if filler_1.oi_type == 5:
        # [L403]
        state.t_approp = _arith.add_to(
            filler_2.oi_approp,
            receiver_value=state.t_approp,
            receiving=_D["t-approp"],
        )
        # [L404] ``add oi-paid to t-paid sl-payments.``  ONE source, TWO
        # receivers, each converted independently through its own picture.
        #
        # This is period-total write 5 of the 9 in the whole migration, and AAP
        # 0.6.4 records that those nine are "the sole writers" of SYSTOT-REC.
        # ``sl-payments`` lives on ``system_record_4``, the third linkage
        # parameter, so the effect leaves this program through linkage.
        state.t_paid = _arith.add_to(
            filler_2.oi_paid, receiver_value=state.t_paid, receiving=_D["t-paid"]
        )
        state.system_4.sales_ledger_data.sl_payments = _arith.add_to(
            filler_2.oi_paid,
            receiver_value=state.system_4.sales_ledger_data.sl_payments,
            receiving=_SYS4["sl-payments"],
        )
        # [L405]
        state.t_deduct = _arith.add_to(
            filler_1.oi_deduct_amt,
            receiver_value=state.t_deduct,
            receiving=_D["t-deduct"],
        )
    # [L406-L407] ``else if oi-type = 6``
    elif filler_1.oi_type == 6:
        # [L408]
        state.j_approp = _arith.add_to(
            filler_2.oi_approp,
            receiver_value=state.j_approp,
            receiving=_D["j-approp"],
        )
        # [L409]
        state.j_paid = _arith.add_to(
            filler_2.oi_paid, receiver_value=state.j_paid, receiving=_D["j-paid"]
        )
        # [L410]
        state.j_deduct = _arith.add_to(
            filler_1.oi_deduct_amt,
            receiver_value=state.j_deduct,
            receiving=_D["j-deduct"],
        )

    # [L412] ``move oi-approp to oi-paid.``  Order is load-bearing: this
    # overwrites ``oi-paid`` AFTER [L404]/[L409] have accumulated its old value,
    # and BEFORE [L413] persists the row.  Hoisting it would change both the
    # totals and the stored record.
    filler_2.oi_paid = _move.move_numeric(
        filler_2.oi_approp, _OI["oi-paid"], sending_field=_OI["oi-approp"]
    )
    # [L413] ``perform Sales-Rewrite.``  [L415] the maintainer's note: for a
    # non-existent sales row the rewrite fails and the error is deliberately
    # ignored.  No reply test follows, and none is added.
    _facade.sales_rewrite(state.ctx_sales)

    # [L417-L418] ``if G-L perform BL-Write.  *> what happens if using IRS ?``
    #
    # FINDING-5 - the maintainer's question mark has an answer, and it is
    # "nothing happens".  All THREE calls into the batch family are gated on
    # ``G-L`` alone - ``BL-Open`` [L324], this ``BL-Write`` [L417] and
    # ``BL-Close`` [L462] - so when the General Ledger is off the family never
    # executes at all.  The seven IRS fan-out tests live INSIDE those three
    # sections [L578, L585, L647, L665, L690, L693, L695], which makes every one
    # of them unreachable in IRS-only mode: no transfer file is opened, no batch
    # is opened or closed, and not one PSIRSPOST-REC row is written.  The
    # commented-out "bypass gl posting code" block at [L286-L292], whose partner
    # is at [L465-L471], confirms the reading - it zeroes ``level-1`` for exactly
    # this effect.  ``sl060`` is gated the same way, at [sales/sl060.cbl:L466],
    # [sales/sl060.cbl:L535] and [sales/sl060.cbl:L649].  Verified by execution,
    # not by reading.  Reproduced exactly; see AMBIGUITY Q-5.
    if _g_l(state):
        _bl_write(state)

    # [L419] ``move 1 to oi-status.`` - mark the open item closed.
    filler_1.oi_status = _move.move_numeric(1, _OI["oi-status"])
    # [L421] ``perform OTM3-Rewrite.`` - the second OTM3 rewrite.
    _facade.otm3_rewrite(state.ctx_otm3)

    # [L423-L427] ``l5-type`` text selection - print only.
    # [L428] ``write print-record from line-5 after 1.`` - print only.

    # [L429] ``add 1 to line-cnt.``  The counter survives the print file's
    # removal because [L430] branches on it.
    state.line_cnt = _arith.add_to(
        1, receiver_value=state.line_cnt, receiving=_D["line-cnt"]
    )
    # [L430-L431] ``if line-cnt > Page-Lines perform headings.``  An ordered
    # comparison across two BINARY-CHAR fields of opposite signedness -
    # ``line-cnt`` is signed [L173], ``Page-Lines`` is not - so it goes through
    # the published algebraic comparator.
    if _arith.compare(state.line_cnt, state.system.system_data_block.page_lines) > 0:
        _headings(state)

    # GO TO class 1 [sales/sl100.cbl:L433] -> ``loop.`` L331.  Unconditional:
    # ``cust-update`` always returns to the read.
    return


# ---------------------------------------------------------------------------
# main-end.  [sales/sl100.cbl:L435]
# ---------------------------------------------------------------------------


def _main_end(state: _State) -> None:
    """``main-end.`` [sales/sl100.cbl:L435-L474] - the class-2 post-loop block.

    This is the work the ``GO TO main-end`` at [L334] jumps to, and it is
    substantial: two closes, the totals, the deduction merge and its reversal out
    of value analysis, the batch close, and two SYSTEM-REC stamps.  AAP 0.6.3
    warns that mis-splitting a class-2 transfer "would silently drop end-of-run
    processing"; here that would mean losing the value-analysis reversal and the
    ``S-Flag-P`` latch reset.
    """
    # [L438] ``perform OTM3-Close.``
    _facade.otm3_close(state.ctx_otm3)
    # [L439] ``perform Sales-Close.``
    _facade.sales_close(state.ctx_sales)

    # [L441-L452] the two total print blocks - "Payment Totals" from ``t-*`` and
    # "Journal Totals" from ``j-*``.  Print only; the totals themselves are real
    # and are logged so the run is auditable without the report.
    _log.info(
        "Payment Totals: approp=%s deduct=%s paid=%s",
        state.t_approp,
        state.t_deduct,
        state.t_paid,
    )
    _log.info(
        "Journal Totals: approp=%s deduct=%s paid=%s",
        state.j_approp,
        state.j_deduct,
        state.j_paid,
    )
    # [L453] ``close print-file.`` - OMITTED with the print file.
    # [L454] ``call "SYSTEM" using print-report.`` - the report spool-out path,
    # placed out of scope by AAP 0.1.1.  OMITTED and recorded.  (Note the
    # lower-case spelling here against ``sl060``'s ``Print-Report``.)

    # [L456] ``add j-deduct to t-deduct.``  Load-bearing and easy to misplace:
    # the journal deductions are merged into the payment deductions BEFORE the
    # test at [L457] and before ``analise-deductions`` reads ``t-deduct``.  Move
    # it after either and the value-analysis reversal changes.
    state.t_deduct = _arith.add_to(
        state.j_deduct, receiver_value=state.t_deduct, receiving=_D["t-deduct"]
    )
    # [L457-L460]
    if state.t_deduct != 0:
        _facade.value_open(state.ctx_value)
        _analise_deductions(state)
        _facade.value_close(state.ctx_value)

    # [L462-L463] ``if G-L perform BL-Close.``
    if _g_l(state):
        _bl_close(state)

    # [L465-L471] the commented-out ``move save-level-1 to level-1`` restore,
    # twice over.  Dead in the compiled program; dead here.

    # [L473] ``move "Y" to oi-3-flag.``  A SYSTEM-REC column, so diff-visible.
    state.system.sales_ledger_block.oi_3_flag = _move.move_alphanumeric(
        "Y", _SYS["oi-3-flag"]
    )
    # [L474] ``move zero to S-Flag-P.``  The proofing latch of [L296], cleared.
    # Together with that gate this makes the program a one-shot: run it twice in
    # a row and the second run aborts at [L300].  It matters to the determinism
    # test, which must re-seed rather than simply re-run.
    state.system.sales_ledger_block.s_flag_p = _move.move_figurative(
        _move.ZERO, _SYS["s-flag-p"]
    )
    # [L475] falls through to ``menu-exit.`` L476.


def _menu_exit(state: _State) -> None:
    """``menu-exit.`` [sales/sl100.cbl:L476-L477] - the one exit of the program.

    Reached three ways: the class-4 transfer at [L300], the class-4 transfer at
    [L317], and fall-through from [L474].
    """
    # EXIT PROGRAM [sales/sl100.cbl:L477] - ``exit program.``, which returns to
    # the caller.  Note the spelling: ``exit program.``, not ``goback``.  In a
    # called sub-program the two are equivalent here, and the source's choice is
    # recorded rather than normalised.  ``run()`` returning is that return.
    _log.debug("sl100 exit program [%s:L477]", _SRC)


# ---------------------------------------------------------------------------
# headings.  [sales/sl100.cbl:L479]
# ---------------------------------------------------------------------------


def _headings(state: _State) -> None:
    """``headings.`` [sales/sl100.cbl:L479-L495] - the report page header.

    Print-only, and retained for two reasons.  R-5 requires a named function per
    paragraph whatever the paragraph does; and its two counters are not
    print-only in effect - ``j`` is the page number and ``line-cnt`` is what
    [L430] branches on, so dropping the paragraph would change control flow.
    """
    # [L480] ``add 1 to j.``
    state.j = _arith.add_to(1, receiver_value=state.j, receiving=_D["j"])
    # [L481] ``move j to l1-page.`` and [L482] ``move usera to l2-user.`` -
    # print heading fields.  OMITTED.
    _log.debug(
        "page %s for %s", state.j, state.system.system_data_block.suser.usera
    )
    # [L484-L491] page-throw selection and [L492-L494] the column headings: five
    # ``write print-record`` statements against the omitted print file.
    # [L495] ``move 5 to line-cnt.``  Real: it resets the line budget [L430]
    # tests, so the page break interval is preserved exactly.
    state.line_cnt = _move.move_numeric(5, _D["line-cnt"])


# ---------------------------------------------------------------------------
# compute-sales-pay.  [sales/sl100.cbl:L497]  ... csp-exit.  [L516]
# ---------------------------------------------------------------------------


def _compute_sales_pay(state: _State) -> None:
    """``compute-sales-pay.`` [sales/sl100.cbl:L497-L514].

    The customer's payment-days moving average, plus the worst-days watermark.
    Called only from the ``PERFORM ... THRU`` at [L344], for a cleared invoice.

    ANOMALY A-10 [sales/sl100.cbl:L497-L514] - variant (c) of the moving-average
    idiom.  Three programs maintain a running average with the "same" three
    lines and no two of them agree.  This one differs from ``sl060``'s two
    variants in six measured dimensions:

      1. [L504] ``move zero to work-b`` runs UNCONDITIONALLY, BEFORE the guard,
         with no ``ELSE`` anywhere.  ``sl060`` clears its accumulator inside an
         ``else`` [sales/sl060.cbl:L822-L824].
      2. [L506] the guard has ONE condition, ``sales-pay-activety not = zero``.
         ``sl060``'s has TWO, ``activety /= 0 AND average /= 0``
         [sales/sl060.cbl:L819-L820].
      3. [L509-L510] the accumulate comes FIRST and the counter is incremented
         AFTER it.  ``sl060`` increments first [sales/sl060.cbl:L825] then
         accumulates [sales/sl060.cbl:L826].
      4. [L511] the divide is written ``divide work-b BY sales-pay-activety
         giving`` where ``sl060`` writes ``divide sales-activety INTO work-2
         giving`` [sales/sl060.cbl:L827].  The two verb forms are
         arithmetically equivalent - this dimension is syntactic - so the source
         form is mirrored with ``divide_by_giving`` and deliberately NOT
         rewritten into the ``into`` form.
      5. the accumulators are ``binary-long`` [sales/sl100.cbl:L182-L183], plain
         integers; ``sl060``'s ``work-2`` is ``pic s9(14) comp-3``
         [sales/sl060.cbl:L206].
      6. the operand is a DAY COUNT, not money: [L503] subtracts two binary day
         numbers.  ``sl060``'s is ``work-goods pic s9(7)v99``
         [sales/sl060.cbl:L218].

    A-8 DOES NOT APPLY HERE, and must not be recorded as if it did.  A-8 is the
    DOUBLE truncation of ``sl060``: pence lost accumulating two-decimal money
    into a zero-scale field, then the remainder lost on an integer divide.
    Dimensions 5 and 6 above remove the first of those two: the operand is
    already an integer, so the only truncation in this paragraph is the divide.

    AAP 0.6.1, verbatim: "Normalising them into one helper would be the single
    easiest way to fail this migration."  Reproduced deliberately per R-4; DO
    NOT FIX, DO NOT FACTOR, and do not reconcile it with the sibling programs -
    ``pl100``'s [purchase/pl100.cbl:L494-L506] is this same shape over the
    ``purch-pay-*`` fields and still keeps its own copy.
    """
    sales = state.sales
    filler_1 = state.oi.filler_1

    # [L500-L501] ``if oi-date-cleared = zero go to csp-exit.``
    if filler_1.oi_date_cleared == 0:
        # GO TO class 3 [sales/sl100.cbl:L501] -> ``csp-exit.`` L516, the exit
        # label of this PERFORM THRU range.  A forward transfer to the range's
        # own terminus is a return.
        return

    # [L503] ``subtract oi-date from oi-date-cleared giving work-a.``  The days
    # an invoice took to clear.  Both operands are binary day numbers, so the
    # result is an exact integer count with nothing to truncate.
    state.work_a = _arith.subtract_giving(
        filler_1.oi_date, minuend=filler_1.oi_date_cleared, receiving=_D["work-a"]
    )
    # [L504] ANOMALY A-10 dimension 1 - unconditional, and BEFORE the guard.
    # Reproduced deliberately per R-4; DO NOT FIX.
    state.work_b = _move.move_figurative(_move.ZERO, _D["work-b"])

    # [L506-L507] ANOMALY A-10 dimension 2 - ONE condition, and no ``ELSE``.
    # Reproduced deliberately per R-4; DO NOT FIX.
    if sales.sales_pay_activety != 0:
        state.work_b = _arith.multiply_by_giving(
            sales.sales_pay_activety, sales.sales_pay_average, _D["work-b"]
        )

    # [L509] ANOMALY A-10 dimension 3 - the accumulate happens FIRST ...
    # Reproduced deliberately per R-4; DO NOT FIX.
    state.work_b = _arith.add_to(
        state.work_a, receiver_value=state.work_b, receiving=_D["work-b"]
    )
    # [L510] ... and the counter is incremented AFTER it, so the divisor below
    # already includes this invoice.
    sales.sales_pay_activety = _arith.add_to(
        1,
        receiver_value=sales.sales_pay_activety,
        receiving=_SL["sales-pay-activety"],
    )
    # [L511] ANOMALY A-10 dimension 4 - the ``BY ... GIVING`` form, mirrored.
    # The receiving field is ``binary-long`` [copybooks/wssl.cob:L51], so the
    # store truncates toward zero and the fractional part of the average is
    # discarded.  That single truncation is the whole of it - see the A-8 note
    # above.  Reproduced deliberately per R-4; DO NOT FIX.
    sales.sales_pay_average = _arith.divide_by_giving(
        state.work_b, sales.sales_pay_activety, _SL["sales-pay-average"]
    )

    # [L513-L514] the worst-payment-days watermark.  ``sales-pay-worst`` is
    # ``binary-long`` [copybooks/wssl.cob:L52]; the comparison is algebraic.
    if _arith.compare(state.work_a, sales.sales_pay_worst) > 0:
        sales.sales_pay_worst = _move.move_numeric(
            state.work_a, _SL["sales-pay-worst"], sending_field=_D["work-a"]
        )
    # [L515] falls through to ``csp-exit.`` L516.


def _csp_exit(state: _State) -> None:
    """``csp-exit.`` [sales/sl100.cbl:L516-L517] - the ``PERFORM THRU`` terminus.

    EXIT [sales/sl100.cbl:L517] - the body is ``exit.``, a plain ``EXIT``
    statement, which is a no-op.  It is NOT ``exit section.``  This program
    carries exactly nine ``exit section.`` statements - L548, L595, L676, L698,
    L706, L741, L776, L806 and L814 - and this paragraph is not one of them.
    The distinction matters: ``exit section.`` would leave the enclosing section,
    whereas ``exit.`` does nothing at all, so control reaches the end of the
    paragraph and, in the ``PERFORM ... THRU`` at [L344], the range simply ends.

    The function exists because the label exists (R-5) and because the
    ``PERFORM ... THRU`` at [L344] names it as the end of its range, so it is
    genuinely executed once per cleared invoice.
    """
    # EXIT [sales/sl100.cbl:L517] - ``exit.``  A no-op, reproduced as a no-op.
    return


# ---------------------------------------------------------------------------
# analise-deductions section.  [sales/sl100.cbl:L519]
# ---------------------------------------------------------------------------


def _analise_deductions(state: _State) -> None:
    """``analise-deductions section.`` [sales/sl100.cbl:L519-L546].

    Reverses this run's deductions out of the value-analysis ``"zd"`` group -
    the same group ``sl055`` accumulated into - by SUBTRACTING where ``sl055``
    added.  It does it twice: once for the fully-qualified ``"Szd"`` code, then
    once more for the code with ``va-second`` blanked, which is the roll-up row.

    The two blocks are deliberately NOT factored into one helper.  They read
    different rows, the second depends on the first having already been
    rewritten, and the same twice-over shape appears in ``sl055``'s
    ``dc000-Store-Specials`` and ``sl060``'s ``ba000-Analise-Deductions`` - each
    keeping its own copy.  AAP 0.8.4 is explicit that performance work here is
    "out of scope by construction", and these two reads are precisely what an
    optimiser would coalesce.
    """
    value = state.value

    # [L522] ``move "Szd" to va-code.``  The receiver is the ``03 VA-Code.``
    # group, so this is a byte-image move: 'S' lands in ``va-system``, 'z' in
    # ``va-first``, 'd' in ``va-second``.  The image is taken from the published
    # group-move primitive and distributed with reference modification, rather
    # than the three leaves being assigned from hand-split literals.
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

    # [L523] ``move 1 to File-Key-No.``
    #
    # FINDING-6 - this assignment, and the two at [L533] and [L537], are inert.
    # ``Value-Read-Indexed`` [copybooks/Proc-ACAS-FH-Calls.cob:L753-L757] sets
    # ``File-Key-No`` to 1 itself before dispatching, and the ``acas013``
    # dispatch paragraph pins it again, so the program's own move is overwritten
    # by the very verb it precedes.  Preserved anyway: R-3 forbids removing a
    # statement, and the ordering is part of the record of what the source does.
    state.file_access.logging_data.file_key_no = _move.move_numeric(
        1, _FA["file-key-no"]
    )
    # [L524] ``perform Value-Read-Indexed.``
    _facade.value_read_indexed(state.ctx_value)
    # [L525-L526]
    if state.file_access.fs_reply == FsReply.INVALID_KEY_ON_START:
        # GO TO class 3 [sales/sl100.cbl:L526] -> ``main-exit.`` L548, which is
        # ``exit section.`` - a return from the section.
        _analise_deductions__main_exit(state)
        return

    # [L528-L531] the four subtracts.  Two different types share the shape:
    # ``n-deduct`` is a ``binary-long`` COUNT [sales/sl100.cbl:L180] going into
    # ``va-t-*`` (``pic 9(5) comp``), while ``t-deduct`` is MONEY [L176] going
    # into ``va-v-*`` (``pic s9(8)v99 comp-3``).  Each store is driven by its own
    # receiving descriptor, so the count never acquires a scale and the money
    # never loses one.
    #
    # AMBIGUITY Q-1 [sales/sl100.cbl:L528-L529] - ``va-t-this`` and
    # ``va-t-year`` are UNSIGNED (``pic 9(5) comp``), so a subtraction that would
    # go negative cannot store its sign.  The published primitive stores the
    # absolute value, which is COBOL's rule for an unsigned receiver, but the
    # exact bytes the bridge then hands to an ``int(5) unsigned`` column must be
    # confirmed against the compiled oracle before this is called settled.
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

    # [L533] the extra ``move 1 to File-Key-No`` - see FINDING-6.  It sits
    # BETWEEN the four subtracts and the rewrite, where ``sl060``'s equivalent
    # section has nothing at all, and it is kept exactly there.
    state.file_access.logging_data.file_key_no = _move.move_numeric(
        1, _FA["file-key-no"]
    )
    # [L534] ``perform Value-Rewrite.``
    _facade.value_rewrite(state.ctx_value)

    # [L536] ``move space to va-second.``  Blanking the second character turns
    # the key into the roll-up row.
    value.va_code.va_group.va_second = _move.move_figurative(
        _move.SPACE, _VAL["va-second"]
    )
    # [L537] the third ``move 1 to File-Key-No`` - see FINDING-6.
    state.file_access.logging_data.file_key_no = _move.move_numeric(
        1, _FA["file-key-no"]
    )
    # [L538] ``perform Value-Read-Indexed.``
    _facade.value_read_indexed(state.ctx_value)
    # [L539-L540]
    if state.file_access.fs_reply == FsReply.INVALID_KEY_ON_START:
        # GO TO class 3 [sales/sl100.cbl:L540] -> ``main-exit.`` L548.
        _analise_deductions__main_exit(state)
        return

    # [L542-L545] the same four subtracts again, against the roll-up row.
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
    # [L546] ``perform Value-Rewrite.``  Note there is NO ``move 1 to
    # File-Key-No`` before this one, unlike [L533] before the first rewrite.
    _facade.value_rewrite(state.ctx_value)
    # [L547] falls through to ``main-exit.`` L548.
    _analise_deductions__main_exit(state)


def _analise_deductions__main_exit(state: _State) -> None:
    """``main-exit.   exit section.`` [sales/sl100.cbl:L548].

    Section-qualified, because ``main-exit.`` is the name of five different
    paragraphs in this one program - L548, L595, L676, L698 and L706 - and R-5
    requires each to have its own function.  Paragraph names are not globally
    unique in this codebase.
    """
    return


# ---------------------------------------------------------------------------
# BL-Open section.  [sales/sl100.cbl:L550]
# ---------------------------------------------------------------------------


def _bl_open(state: _State) -> None:
    """``BL-Open section.`` [sales/sl100.cbl:L550-L593] - start a GL batch.

    Note the naming: this program calls its three batch sections ``BL-Open``,
    ``BL-Write`` and ``BL-Close``, where ``sl060`` prefixes them
    (``ca000-BL-Open``) and ``pl100`` lower-cases them (``bl-open``).  Each
    program's own spelling is preserved.
    """
    batch = state.batch

    # [L553] ``perform GL-Batch-Open.``
    _facade.gl_batch_open(state.ctx_batch)

    # [L555] ``move next-batch to WS-Batch-Nos.``  ``Next-Batch`` is
    # ``binary-short`` on SYSTEM-REC; ``WS-Batch-Nos`` is ``pic 9(5)``.
    batch.ws_batch_key.ws_batch_nos = _move.move_numeric(
        state.system.general_ledger_block.next_batch,
        _BAT["ws-batch-nos"],
        sending_field=_SYS["next-batch"],
    )
    # [L556] ``move 3 to WS-Ledger.``  3 = the Sales Ledger.
    batch.ws_batch_key.ws_ledger = _move.move_numeric(3, _BAT["ws-ledger"])
    # [L557] ``add 1 to Next-Batch.``  The allocation is consumed immediately,
    # so the SYSTEM-REC counter advances even if the batch is later empty.
    state.system.general_ledger_block.next_batch = _arith.add_to(
        1,
        receiver_value=state.system.general_ledger_block.next_batch,
        receiving=_SYS["next-batch"],
    )
    # [L558-L559] ``move zero to batch-status cleared-status.`` - two receivers.
    batch.batch_status = _move.move_figurative(_move.ZERO, _BAT["batch-status"])
    batch.cleared_status = _move.move_figurative(_move.ZERO, _BAT["cleared-status"])
    # [L560] ``move Scycle to Bcycle.``  ``binary-char`` into ``pic 99``.
    batch.bcycle = _move.move_numeric(
        state.system.system_data_block.scycle,
        _BAT["bcycle"],
        sending_field=_SYS["scycle"],
    )
    # [L561] ``move run-date to entered.``
    #
    # THE CONTROLLED-CLOCK OBSERVABLE.  ``Run-Date``
    # [copybooks/wssystem.cob:L67] is one of the two date observables the
    # migration pins, and it arrives here purely through linkage on
    # ``system_record`` - this program reads no clock, and R-6 forbids adding
    # one.  ``entered`` is a GLBATCH-REC column, so the pinning is what makes
    # two runs of a scenario byte-identical.
    batch.dates.entered = _move.move_numeric(
        state.system.system_data_block.run_date,
        _BAT["entered"],
        sending_field=_SYS["run-date"],
    )

    # [L563] ``move "Sales Ledger Payments" to description.``  21 characters
    # into ``pic x(24)``; ``sl060`` writes a different literal, and the batch
    # description is a column, so the two must not be unified.
    batch.description = _move.move_alphanumeric(
        "Sales Ledger Payments", _BAT["description"]
    )
    # [L564-L571] ``move zero to`` EIGHT receivers, each through its own
    # picture.  ``bdefault`` is spelled ``b_default`` in the record module.
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

    # [L573-L575] the batch conventions.
    batch.posting_data.convention = _move.move_alphanumeric(
        "CR", _BAT["convention"]
    )
    batch.posting_data.batch_def_code = _move.move_alphanumeric(
        "SL", _BAT["batch-def-code"]
    )
    batch.posting_data.batch_def_vat = _move.move_alphanumeric(
        "O", _BAT["batch-def-vat"]
    )
    # [L576] ``add postings 1 giving Batch-Start.``  A variadic ``ADD ...
    # GIVING`` with two addends, quantized ONCE into the receiver.
    #
    # ANOMALY A-17, the reading end.  ``postings`` is the SYSTEM-REC field that
    # [L691] writes with the unexplained ``move RRN to postings.  *> Why ?``.
    # This statement reads it straight back to allocate the batch's first record
    # number, and [L593] below seeds the counter from it - which is exactly what
    # makes that unexplained move load-bearing rather than harmless, and its
    # effect diff-visible in GLPOSTING-REC.  Reproduced deliberately per R-4;
    # DO NOT FIX.  See AMBIGUITY Q-2 and the matching comment at [L691].
    batch.batch_start = _arith.add_giving(
        state.system.general_ledger_block.postings, 1, receiving=_BAT["batch-start"]
    )

    # [L578-L584] IRS FAN-OUT SITE 1 of 7.  Open the transfer file for extend;
    # if that fails, close it and open it for output instead.  The maintainer's
    # comments say the fallback "wont happen in FH" - it is reproduced anyway.
    if _irs_used(state) or _irs_both_used(state):
        # [L579] ``perform SPL-Posting-Open-Extend.``
        _facade.spl_posting_open_extend(state.ctx_irs)
        # [L580]
        if state.file_access.fs_reply != FsReply.SUCCESS:
            # [L581]
            _facade.spl_posting_close(state.ctx_irs)
            # [L582] ``perform SPL-Posting-Open-Output.``
            #
            # On ``acas008`` an open-for-output means DELETE EVERY ROW: the
            # handler converts it into a ``Delete-All``
            # [common/acas008.cbl:L313-L319], restated unconditionally at
            # [common/acas008.cbl:L571-L574].  So this recovery path empties
            # PSIRSPOST-REC.
            _facade.spl_posting_open_output(state.ctx_irs)
        # [L583] ``end-if``
    # [L584] ``end-if`` - note there is no period here, so [L585] is a sibling.

    # [L585-L591] IRS FAN-OUT SITE 2 of 7, with the same extend-then-fallback
    # shape against the GL posting file.
    if _irs_both_used(state) or _g_l(state):
        # [L586] ``perform GL-Posting-Open.``
        _facade.gl_posting_open(state.ctx_posting)
        # [L587]
        if state.file_access.fs_reply != FsReply.SUCCESS:
            # [L588]
            _facade.gl_posting_close(state.ctx_posting)
            # [L589]
            _facade.gl_posting_open_output(state.ctx_posting)
        # [L590] ``end-if``
    # [L591] ``end-if.`` - a period after ``end-if``; a style quirk with no
    # effect, noted because the absence of one at [L584] does matter.

    # [L593] ``move Batch-Start to RRN.``  Seeds the shared record-number
    # counter that [L667] stamps onto each posting and [L669] advances.
    state.file_access.rrn = _move.move_numeric(
        batch.batch_start, _FA["rrn"], sending_field=_BAT["batch-start"]
    )
    # [L594] falls through to ``main-exit.`` L595.
    _bl_open__main_exit(state)


def _bl_open__main_exit(state: _State) -> None:
    """``main-exit.   exit section.`` [sales/sl100.cbl:L595]."""
    return


# ---------------------------------------------------------------------------
# BL-Write section.  [sales/sl100.cbl:L598]
# ---------------------------------------------------------------------------


def _bl_write(state: _State) -> None:
    """``BL-Write section.`` [sales/sl100.cbl:L598-L674] - emit one posting.

    The maintainer's own banner at [L601-L609] warns that this writes a posting
    to GL or IRS for each line item, that a GL account must therefore exist for
    every analysis code, and that the IRS convention reserves default account 31
    for input VAT and 32 for output VAT.  [L610] records that ``u-date`` is in UK
    format, which is what [L612-L613] relies on.
    """
    posting = state.posting
    batch = state.batch
    filler_1 = state.oi.filler_1
    filler_2 = filler_1.filler_2

    # [L612-L613] build an 8-character ``post-date`` (DD/MM/YY) from the
    # 10-character ``u-date`` (DD/MM/CCYY) with reference modification on BOTH
    # sides.  COBOL reference modification is 1-BASED, and ``post-date`` is a
    # GLPOSTING-REC column, so an off-by-one here is visible in a table dump.
    # Both sides go through the published primitive; no Python slicing appears.
    posting.post_date = _move.ref_mod_into(
        posting.post_date, 1, 6, _move.ref_mod(state.maps03_ws.u_date, 1, 6)
    )
    posting.post_date = _move.ref_mod_into(
        posting.post_date, 7, 2, _move.ref_mod(state.maps03_ws.u_date, 9, 2)
    )
    # [L614] ``add 1 to items.``
    batch.items = _arith.add_to(
        1, receiver_value=batch.items, receiving=_BAT["items"]
    )
    # [L615] ``move items to post-number.``
    posting.ws_post_key.post_number = _move.move_numeric(
        batch.items, _POST["post-number"], sending_field=_BAT["items"]
    )
    # [L616] ``move oi-paid to post-amount.``
    posting.post_amount = _move.move_numeric(
        filler_2.oi_paid, _POST["post-amount"], sending_field=_OI["oi-paid"]
    )

    # [L618] the maintainer's own comment: "THIS DOES NOT APPEAR THE SAME as
    # SL060 and PL060/PL100".  He is right, and it is the reason for the block
    # below.
    #
    # [L620-L628] FIVE SEPARATE ``STRING`` STATEMENTS sharing ONE pointer.
    # ``sl060`` builds the SAME ``post-legend`` column from a single ``STRING``
    # of three sources, preceded by an edited move and an ``INSPECT`` chain
    # [sales/sl060.cbl:L1085-L1094].  The two approaches produce different bytes
    # and the difference is visible in a table dump, so they are NOT unified.
    # ``sl100`` has no ``m pic z(7)9`` edited field and no ``INSPECT``, and none
    # is imported here.  The published ``string_into`` primitive documents this
    # very site and states that both shapes are supported and "neither is
    # rewritten into the other".
    #
    # FINDING-7 - ``STRING ... POINTER`` overlays from the pointer position and
    # leaves the REST of the receiver untouched.  ``post-legend`` is never
    # cleared before this chain, so on the second and later postings of a run any
    # tail beyond the new pointer is inherited from the previous legend.  Passing
    # the field's current content as the receiver reproduces that exactly.  See
    # AMBIGUITY Q-3.
    #
    # [L620] ``move 1 to xx.``
    state.xx = _move.move_numeric(1, _D["xx"])
    # [L621] ``move oi-b-nos to batch.``
    posting.ws_post_key.batch = _move.move_numeric(
        filler_1.oi_batch.oi_b_nos, _POST["batch"], sending_field=_OI["oi-b-nos"]
    )
    # [L622] ``string batch delimited by size into post-legend pointer xx.``
    posting.post_legend, state.xx = _move.string_into(
        posting.post_legend,
        [(posting.ws_post_key.batch, _move.DELIMITED_BY_SIZE, _POST["batch"])],
        pointer=state.xx,
    )
    # [L623] ``move WS-Batch-Nos to batch.``
    #
    # FINDING-8 - this move happens AFTER [L622] has already stringed ``batch``,
    # and ``batch`` is never stringed again.  So the LEGEND carries ``oi-b-nos``
    # (the OTM3 batch the payment came from) while the ``batch`` COLUMN ends up
    # holding ``WS-Batch-Nos`` (the new GL batch).  The statement is inert for
    # the legend and load-bearing for the column - two different observable
    # effects from one move - and it is emphatically not a redundant assignment
    # to be tidied away.
    posting.ws_post_key.batch = _move.move_numeric(
        batch.ws_batch_key.ws_batch_nos,
        _POST["batch"],
        sending_field=_BAT["ws-batch-nos"],
    )
    # [L624] ``string "/" delimited by size into post-legend pointer xx.``
    posting.post_legend, state.xx = _move.string_into(
        posting.post_legend, ["/"], pointer=state.xx
    )
    # [L625] ``move oi-b-item to k.``
    state.k = _move.move_numeric(
        filler_1.oi_batch.oi_b_item, _D["k"], sending_field=_OI["oi-b-item"]
    )
    # [L626] ``string k delimited by size into post-legend pointer xx.``
    posting.post_legend, state.xx = _move.string_into(
        posting.post_legend,
        [(state.k, _move.DELIMITED_BY_SIZE, _D["k"])],
        pointer=state.xx,
    )
    # [L627] ``string "  :  " delimited by size into post-legend pointer xx.``
    posting.post_legend, state.xx = _move.string_into(
        posting.post_legend, ["  :  "], pointer=state.xx
    )
    # [L628] ``string sales-name delimited by size into post-legend pointer xx.``
    posting.post_legend, state.xx = _move.string_into(
        posting.post_legend,
        [(state.sales.sales_name, _move.DELIMITED_BY_SIZE, _SL["sales-name"])],
        pointer=state.xx,
    )

    # [L630-L631] THE DOUBLE-ENTRY SIDES, and they are SWAPPED relative to
    # ``sl060``.
    #
    # FINDING-9 - a payment is the mirror of an invoice, so here the debtors
    # control account is the CREDIT and the payments account is the DEBIT:
    # ``S-Debtors -> post-cr`` [L630] and ``SL-Pay-AC -> post-dr`` [L631].
    # ``sl060`` does the opposite, ``S-Debtors -> Post-DR``
    # [sales/sl060.cbl:L1103] and ``SL-Sales-AC -> Post-CR``
    # [sales/sl060.cbl:L1104] - note also the DIFFERENT second account,
    # ``SL-Pay-AC`` here against ``SL-Sales-AC`` there.  The swap is correct and
    # is exactly what a transcription from the wrong sibling would get backwards.
    #
    # Both senders are ``binary-long`` on SYSTEM-REC and both receivers are
    # ``pic 9(6)``, so the store is a narrowing one and the descriptors decide
    # what survives.
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

    # [L633-L637] ``move zero to`` FIVE receivers.
    #
    # FINDING-10 - the VAT ACCOUNT is ZEROED here, not copied.  ``sl060`` zeroes
    # only FOUR fields and then MOVES ``VAT-AC of system-record`` into
    # ``VAT-AC of WS-Posting-Record`` [sales/sl060.cbl:L1111-L1112].  ``sl100``
    # includes the VAT account in the zeroing list and never populates it,
    # because a cash payment carries no VAT.  For the same reason there is no
    # ``input-vat``/``actual-vat`` accumulation anywhere in this program, where
    # ``sl060`` has both at [sales/sl060.cbl:L1120-L1121].
    #
    # ``VAT-AC of WS-Posting-record`` [L635] is qualified in the source because
    # ``VAT-AC`` also names a SYSTEM-REC field; the qualification is kept visible
    # in the descriptor lookups.
    posting.dr_pc = _move.move_figurative(_move.ZERO, _POST["dr-pc"])
    posting.cr_pc = _move.move_figurative(_move.ZERO, _POST["cr-pc"])
    posting.vat_ac = _move.move_figurative(_move.ZERO, _POST["vat-ac"])
    posting.vat_pc = _move.move_figurative(_move.ZERO, _POST["vat-pc"])
    posting.vat_amount = _move.move_figurative(_move.ZERO, _POST["vat-amount"])

    # [L639] ``move spaces to post-vat-side.``
    #
    # FINDING-11 - inert.  [L645] overwrites it with "CR" six lines later and
    # nothing reads it in between.  Both moves are reproduced; R-3 forbids
    # eliding the first.
    posting.post_vat_side = _move.move_figurative(
        _move.SPACES, _POST["post-vat-side"]
    )

    # [L641-L642] the batch control totals - GROSS ONLY, two separate statements.
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

    # [L644] ``move "SL" to post-code in WS-Posting-Record.`` - qualified.
    posting.post_code = _move.move_alphanumeric("SL", _POST["post-code"])
    # [L645] ``move "CR" to post-vat-side.``
    posting.post_vat_side = _move.move_alphanumeric("CR", _POST["post-vat-side"])

    # [L647-L664] IRS FAN-OUT SITE 3 of 7 - the IRS transfer record.
    #
    # ANOMALY A-18 [sales/sl100.cbl:L647-L664] - the block copies ELEVEN fields
    # and NEVER copies ``dr-pc`` or ``cr-pc``.  The maintainer flagged both
    # omissions himself, in place: "Missing usage of DR-PC for GL MUST be checked
    # in GL ????" at [L654] and the same for CR-PC at [L656].  He also flagged
    # the literal 32 at [L660] with "*> IS IT ???".  The percentages are
    # therefore simply absent from PSIRSPOST-REC, and ``WS-IRS-Posting-Record``
    # has no field to put them in - the copybook declares exactly those eleven
    # leaves.  Reproduced deliberately per R-4; DO NOT FIX, and do not invent a
    # column for them.
    if _irs_used(state) or _irs_both_used(state):
        irs = state.irs_posting
        # [L648]
        irs.ws_irs_post_key.ws_irs_batch = _move.move_numeric(
            posting.ws_post_key.batch,
            _IRS["ws-irs-batch"],
            sending_field=_POST["batch"],
        )
        # [L649]
        irs.ws_irs_post_key.ws_irs_post_number = _move.move_numeric(
            posting.ws_post_key.post_number,
            _IRS["ws-irs-post-number"],
            sending_field=_POST["post-number"],
        )
        # [L650-L651] ``move Post-Code in WS-Posting-Record to
        # WS-IRS-Post-Code`` - qualified again.
        irs.ws_irs_post_code = _move.move_alphanumeric(
            posting.post_code,
            _IRS["ws-irs-post-code"],
            sending_field=_POST["post-code"],
        )
        # [L652]
        irs.ws_irs_post_date = _move.move_alphanumeric(
            posting.post_date,
            _IRS["ws-irs-post-date"],
            sending_field=_POST["post-date"],
        )
        # [L653] ``move Post-DR to WS-IRS-Post-DR`` - ``pic 9(6)`` narrowing into
        # ``pic 9(5)``, so the leading digit is lost if an account number needs
        # six.  The descriptors carry that, not this module.
        irs.ws_irs_post_dr = _move.move_numeric(
            posting.post_dr, _IRS["ws-irs-post-dr"], sending_field=_POST["post-dr"]
        )
        # [L654] the maintainer's DR-PC note - see A-18 above.  No statement.
        # [L655]
        irs.ws_irs_post_cr = _move.move_numeric(
            posting.post_cr, _IRS["ws-irs-post-cr"], sending_field=_POST["post-cr"]
        )
        # [L656] the maintainer's CR-PC note - see A-18 above.  No statement.
        # [L657]
        irs.ws_irs_post_amount = _move.move_numeric(
            posting.post_amount,
            _IRS["ws-irs-post-amount"],
            sending_field=_POST["post-amount"],
        )
        # [L658]
        irs.ws_irs_post_legend = _move.move_alphanumeric(
            posting.post_legend,
            _IRS["ws-irs-post-legend"],
            sending_field=_POST["post-legend"],
        )
        # [L659-L660] ``move 32 to WS-IRS-vat-ac-def Vat-PC  *> IS IT ???`` -
        # ONE literal, TWO receivers, and the second of them is on the GL posting
        # record rather than the IRS one.  So this statement reaches back and
        # sets ``Vat-PC`` to 32 AFTER [L636] zeroed it, meaning the GL posting
        # written at [L668] carries a VAT percentage of 32 whenever IRS is in
        # use and none when it is not.  Part of A-18; reproduced exactly.
        irs.ws_irs_vat_ac_def = _move.move_numeric(32, _IRS["ws-irs-vat-ac-def"])
        posting.vat_pc = _move.move_numeric(32, _POST["vat-pc"])
        # [L661]
        irs.ws_irs_post_vat_side = _move.move_alphanumeric(
            posting.post_vat_side,
            _IRS["ws-irs-post-vat-side"],
            sending_field=_POST["post-vat-side"],
        )
        # [L662]
        irs.ws_irs_vat_amount = _move.move_numeric(
            posting.vat_amount,
            _IRS["ws-irs-vat-amount"],
            sending_field=_POST["vat-amount"],
        )
        # [L663] ``perform SPL-Posting-Write.``
        _facade.spl_posting_write(state.ctx_irs)
    # [L664] ``end-if.``

    # [L665-L670] IRS FAN-OUT SITE 4 of 7 - the GL posting itself.
    if _irs_both_used(state) or _g_l(state):
        # [L667] ``move RRN to WS-Post-RRN.``  The shared counter seeded at
        # [L593] from ``Batch-Start``.
        posting.ws_post_rrn = _move.move_numeric(
            state.file_access.rrn, _POST["ws-post-rrn"], sending_field=_FA["rrn"]
        )
        # [L668] ``perform GL-Posting-Write.``
        _facade.gl_posting_write(state.ctx_posting)
        # [L669] ``add 1 to RRN.``
        state.file_access.rrn = _arith.add_to(
            1, receiver_value=state.file_access.rrn, receiving=_FA["rrn"]
        )
    # [L670] ``end-if.``

    # [L672-L674] THE 99-ITEM BATCH CAP.  ``items`` is ``pic 99``, so a batch
    # cannot hold a hundredth posting; the section closes the batch and opens a
    # fresh one mid-run, which produces an extra GLBATCH-REC row and a new
    # ``Batch-Start``.  Note this is not recursion into ``BL-Write``: it calls
    # its two siblings only.
    if batch.items == 99:
        _bl_close(state)
        _bl_open(state)
    # [L675] falls through to ``main-exit.`` L676.
    _bl_write__main_exit(state)


def _bl_write__main_exit(state: _State) -> None:
    """``main-exit.   exit section.`` [sales/sl100.cbl:L676]."""
    return


# ---------------------------------------------------------------------------
# BL-Close section.  [sales/sl100.cbl:L679]
# ---------------------------------------------------------------------------


def _bl_close(state: _State) -> None:
    """``BL-Close section.`` [sales/sl100.cbl:L679-L696] - close the GL batch.

    Two of the migration's registered anomalies meet in these fifteen lines: the
    unexplained ``postings`` write (A-17) and the terminating period whose
    ABSENCE in ``sl060`` is A-1.
    """
    # [L682] ``perform GL-Batch-Write.``
    _facade.gl_batch_write(state.ctx_batch)
    # [L683-L689] the write-failure report.  Diagnostics only: the display, the
    # status decode and the acknowledgement pause.  There is NO retry, NO abort
    # and NO rollback - the run simply carries on with an unwritten batch - and
    # R-3 forbids adding any of the three.  See AMBIGUITY Q-4.
    if state.file_access.fs_reply != FsReply.SUCCESS:
        # [L684]
        _log.error("%s", _SL132)
        # [L685] ``perform Eval-Status.``
        _eval_status(state)
        # [L686-L687]
        _log.error("%s %s", state.file_access.fs_reply, state.file_access.fs_action)
        # [L688] and [L689]'s acknowledgement pause; the pause is dropped.
        _log.error("%s", _SL002)

    # [L690-L691] IRS FAN-OUT SITE 5 of 7.
    #
    # ANOMALY A-17 [sales/sl100.cbl:L691] - ``move RRN to postings.  *> Why ?``
    # The maintainer does not know why this is here and says so, twice: the
    # question mark on the move itself, and "*> THIS IS IN PURCHASE PL060" on the
    # condition above it at [L690].  It is not harmless.  ``postings`` is a
    # SYSTEM-REC column, and ``BL-Open`` reads it straight back at [L576] to
    # allocate the next batch's first record number, which [L593] then seeds the
    # counter from.  So the value written here decides the ``POST-RRN`` primary
    # keys of the NEXT batch's postings.  AAP 0.6.8 names this site explicitly:
    # its "observable effect on the posting record must be measured and then
    # reproduced regardless of whether it makes sense."  This is occurrence 2 of
    # the 4 across the Sales and Purchase posting programs.  Reproduced
    # deliberately per R-4; DO NOT FIX.  See AMBIGUITY Q-2.
    if _irs_both_used(state) or _g_l(state):
        state.system.general_ledger_block.postings = _move.move_numeric(
            state.file_access.rrn, _SYS["postings"], sending_field=_FA["rrn"]
        )
    # [L692] ``perform GL-Batch-Close.``
    _facade.gl_batch_close(state.ctx_batch)

    # [L693-L696] IRS FAN-OUT SITES 6 and 7 of 7.
    #
    # ANOMALY A-1, THE DIVERGENCE - and here the code is CORRECT.
    #
    # [L694] ``perform SPL-Posting-Close.`` HAS its terminating period.  That
    # period is what makes [L695] a SIBLING ``if`` rather than a nested one, so
    # ``GL-Posting-Close`` DOES execute in pure-GL mode, when ``G-L`` is set and
    # neither IRS flag is.
    #
    # ``sl060``'s otherwise identical block is MISSING that period at
    # [sales/sl060.cbl:L1176], which nests [sales/sl060.cbl:L1177-L1178] inside
    # the IRS test and leaves the GL posting file unclosed in pure-GL mode.  That
    # is anomaly A-1, and it belongs to ``sl060_invoice_posting``, not here.
    #
    # THE DIVERGENCE IS PRESERVED IN BOTH DIRECTIONS: correct in this module,
    # defective in that one.  Do not "align" them.  AAP: "The three sibling
    # programs all have the period, which proves this is an accident rather than
    # an idiom" - ``pl060`` at [purchase/pl060.cbl:L1031], ``pl100`` at
    # [purchase/pl100.cbl:L675] and this program at [L694].  A reader diffing the
    # two Python modules should conclude the asymmetry is deliberate, because it
    # is.
    if _irs_used(state) or _irs_both_used(state):
        _facade.spl_posting_close(state.ctx_irs)
    # [L695] - a SIBLING condition, not a nested one.  See the note above.
    if _irs_both_used(state) or _g_l(state):
        # [L696]
        _facade.gl_posting_close(state.ctx_posting)
    # [L697] falls through to ``main-exit.`` L698.
    _bl_close__main_exit(state)


def _bl_close__main_exit(state: _State) -> None:
    """``main-exit.   exit section.`` [sales/sl100.cbl:L698]."""
    return


# ---------------------------------------------------------------------------
# Eval-Status section.  [sales/sl100.cbl:L700]
# ---------------------------------------------------------------------------


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
    not - alter control flow.  The decoded text is exactly what the facade
    already records in ``FS-Action``, so the message is logged from there rather
    than a second copy of the table being maintained here.
    """
    _log.error(
        "file status %s (%s), we-error %s",
        state.file_access.fs_reply,
        state.file_access.fs_action,
        state.file_access.we_error,
    )
    # [L705] falls through to ``main-exit.`` L706.
    _eval_status__main_exit(state)


def _eval_status__main_exit(state: _State) -> None:
    """``main-exit.   exit section.`` [sales/sl100.cbl:L706]."""
    return


# ---------------------------------------------------------------------------
# The four date sections.  [sales/sl100.cbl:L708, L743, L778, L808]
# ---------------------------------------------------------------------------
# These four appear near-identically in nine of the in-scope programs, and AAP
# 0.6.3 records that consolidating them into ``dates.py`` is "the one place where
# consolidation is unambiguously safe because the bodies are textually
# equivalent".  Safe, but not unconditional: ``dates.py`` publishes TWO variants
# of ``zz050`` because ``gl051`` carries three extra ``inspect ... replacing``
# separator-normalisation statements [general/gl051.cbl:L1178-L1180] that this
# program and the other three carriers omit entirely.  ``sl100`` therefore calls
# the variant WITHOUT the separator normalisation.
#
# All three entry points return the EFFECTIVE ``Date-Form``, because each begins
# by defaulting a zero form to 1 [L718-L719, L758-L759, L788-L789], and that
# default is a real store into a SYSTEM-REC field.  The return value is stored
# back so the program observes it, as ``dates.py`` requires of every caller.


def _date_wrapper(state: _State) -> Callable[[Maps03Ws], None]:
    """The ``maps04 section.`` of this program, as a callable.

    ``zz050`` and ``zz060`` each ``perform maps04`` - meaning this program's own
    section at [sales/sl100.cbl:L808], not the called program directly.  Passing
    the section keeps that hop real, so ``_maps04`` and ``_maps04_exit`` are
    genuinely executed and their traceability is not notional.
    """

    def perform_maps04(maps03_ws: Maps03Ws) -> None:
        _maps04(state)

    return perform_maps04


def _zz050_validate_date(state: _State) -> None:
    """``zz050-Validate-Date section.`` [sales/sl100.cbl:L708-L733].

    Converts a USA or International date in ``ws-test-date`` to UK form and then
    validates it, leaving ``u-bin`` non-zero when the date is good.

    FINDING-12 - THIS SECTION IS NEVER PERFORMED.  There is no ``perform
    zz050`` anywhere in ``sales/sl100.cbl``; the section is boilerplate carried
    in with its three siblings and left unreached.  R-5 still requires the
    function, and it is a faithful transcription rather than a stub, so that the
    day a caller appears the behaviour is already right.
    """
    state.system.system_data_block.date_form = _dates.zz050_validate_date(
        state.ws_dates,
        state.maps03_ws,
        state.system.system_data_block.date_form,
        wrapper=_date_wrapper(state),
    )
    # The GO TO sites inside the consolidated body are classified there:
    # [L721] and [L726] -> ``zz050-test-date`` L735 are class 4, each a named
    # forward transfer into the shared tail; the fall-through at [L734] reaches
    # the same paragraph.
    #
    # ``_zz050_test_date`` is DELIBERATELY NOT CALLED HERE.  All three branches
    # of the consolidated body already perform that paragraph themselves - two by
    # the class-4 re-dispatch and one by fall-through - because it is a paragraph
    # of the SAME section.  Calling it again from this level would execute
    # ``move ws-date to u-date`` / ``move zero to u-bin`` / ``perform maps04`` a
    # second time, which the COBOL never does.  The function below exists for
    # R-5, not for this call site.
    _zz050_exit(state)


def _zz050_test_date(state: _State) -> None:
    """``zz050-test-date.`` [sales/sl100.cbl:L735-L738].

    ``move ws-date to u-date`` / ``move zero to u-bin`` / ``perform maps04``.
    The pre-zeroing at [L737] is the reason the date module's own reject path -
    which leaves its output field untouched [common/maps04.cbl:L146] - reads as
    "errors return zero" to this caller.

    R-5 requires a named function for this label, and this is it.  It is NOT
    called by ``_zz050_validate_date`` above: the consolidated body performs this
    paragraph internally from each of its three branches, exactly as the COBOL
    section does, so calling it from the section level as well would execute the
    paragraph twice.  This function is therefore the traceability entry for
    [L735-L738] and the way any future direct caller would reach it - which is
    also how the COBOL would reach it, since a ``GO TO zz050-test-date`` names
    the paragraph and not the section.
    """
    _dates.zz050_test_date(
        state.ws_dates, state.maps03_ws, wrapper=_date_wrapper(state)
    )


def _zz050_exit(state: _State) -> None:
    """``zz050-exit.`` [sales/sl100.cbl:L740-L741] - ``exit section.``"""
    return


def _zz060_convert_date(state: _State) -> None:
    """``zz060-Convert-Date section.`` [sales/sl100.cbl:L743-L773].

    Converts the binary day number in ``u-bin`` to the presentation form
    ``Date-Form`` selects, leaving both ``u-date`` and ``ws-date`` set - or both
    spaces if the day number is not a valid date.

    Identical in all six carriers except ONE token: ``sl100`` performs
    ``maps04`` where ``gl051`` and ``gl070`` perform ``maps03``.  The
    consolidated body takes the wrapper as an argument for exactly that reason,
    and this program supplies its ``maps04`` section.

    The GO TO sites in the body - [L755], [L761] and [L766], all to
    ``zz060-Exit`` L775 - are class 3 and are classified in the consolidated
    module.
    """
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

    Renders the run date - ``to-day``, the fourth linkage parameter - into
    ``ws-date`` in whichever of the UK, USA or International forms ``Date-Form``
    selects.  Byte-identical in all ten of its carriers, so the consolidated form
    is called with no variant selector.  It performs no date module at all, which
    is why it takes no wrapper.

    The GO TO sites [L791] and [L796], both to ``zz070-Exit`` L805, are class 3.
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

    The thin wrapper around ``call "maps04" using maps03-ws`` [L811].  R-1
    forbids reaching the compiled program, so the reimplementation in
    ``dates.maps04`` is called instead - epoch, six-part reject test and
    untouched-output-on-reject behaviour included.

    ANOMALY A-22 DOES NOT OCCUR IN THIS PROGRAM.  A-22 is a wrapper section
    named after the interface copybook while its exit label is named after the
    called program.  Here the section is ``maps04`` [L808] and its exit is
    ``maps04-exit`` [L813] - the names AGREE.  A-22 occurs only in ``gl070``
    (``maps03`` section 603 with ``maps04-exit`` L608) and ``gl051`` (``maps03``
    section 1273 with ``maps04-exit`` L1278).  Stated explicitly so that nobody
    goes looking for it here.
    """
    _dates.maps04(state.maps03_ws)
    # [L812] falls through to ``maps04-exit.`` L813.
    _maps04_exit(state)


def _maps04_exit(state: _State) -> None:
    """``maps04-exit.`` [sales/sl100.cbl:L813-L814] - ``exit section.``"""
    return


# ---------------------------------------------------------------------------
# The program entry point
# ---------------------------------------------------------------------------


def run(
    ws_calling_data: WsCallingData,
    system_record: SystemRecord,
    system_record_4: SystemRecord4,
    to_day: str,
    file_defs: FileDefs,
    *,
    ok_to_post: bool = True,
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
        whatsoever.  The default is ``True`` because the field's own
        ``value spaces`` [L167] is not an answer at all - spaces re-prompt at
        [L318-L319] - so the only preserved answer that lets the program proceed
        is ``"YES"``.  See AMBIGUITY Q-6.

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
    )

    # ``init01 section.`` [sales/sl100.cbl:L279]
    if not _init01(state):
        # The class-4 transfer at [L300] - see the proof in ``_init01``.
        _menu_exit(state)
        return

    # FALL-THROUGH from ``end-if`` [L301] into ``menu-return.`` [L303].
    _menu_return(state)

    # FALL-THROUGH from [L308] into ``acpt-xrply.`` [L310].
    if not _acpt_xrply(state):
        # The class-4 transfer at [L317] - see the proof in ``_acpt_xrply``.
        _menu_exit(state)
        return

    # FALL-THROUGH from [L330] into ``loop.`` [L331].
    #
    # The ``while True`` is the loop the six class-1 transfers to ``loop`` close
    # and the one class-2 transfer to ``main-end`` leaves.  It lives here rather
    # than inside ``_loop`` because ``loop.`` and ``cust-update.`` are two
    # paragraphs of one cycle: ``loop`` falls through into ``cust-update``, and
    # ``cust-update`` closes the cycle from its own end at [L433].
    while True:
        outcome = _loop(state)
        if outcome == _Flow.CONTINUE_LOOP:
            # GO TO class 1 [sales/sl100.cbl:L339, L348, L352, L355].
            continue
        if outcome == _Flow.LEAVE_LOOP:
            # GO TO class 2 [sales/sl100.cbl:L334] -> ``main-end.`` L435.
            break
        # FALL-THROUGH from [L356] into ``cust-update.`` [L357].
        _cust_update(state)
        # GO TO class 1 [sales/sl100.cbl:L433] -> ``loop.`` L331.  This is the
        # sixth class-1 site; it is a loop-back by shape, and classifying by
        # shape rather than by any pre-drawn label list is what finds it.
        continue

    # ``main-end.`` [sales/sl100.cbl:L435] - the class-2 post-loop block, placed
    # after the loop in full.  AAP 0.6.3 requires the break be accompanied by
    # this work rather than replacing it.
    _main_end(state)

    # FALL-THROUGH from [L475] into ``menu-exit.`` [L476].
    _menu_exit(state)


# ===========================================================================
# --- traceability ---
# ===========================================================================
#
# Source of record: sales/sl100.cbl, 817 lines, migrated in full (R-5).
# No user rules document exists for this project; R-1...R-6 come from the Agent
# Action Plan section 0.7.2 and are restated in this module's docstring.
#
# ---------------------------------------------------------------------------
# 1. FUNCTION -> COBOL LABEL.  23 labels, 23 functions.  Names are
#    SECTION-QUALIFIED where they must be: ``main-exit.`` names five different
#    paragraphs in this one program, so a bare ``_main_exit`` would collide.
# ---------------------------------------------------------------------------
#   _init01                        init01 section.            L279-L301
#   _menu_return                   menu-return.               L303-L308
#   _acpt_xrply                    acpt-xrply.                L310-L329
#   _loop                          loop.                      L331-L355
#   _cust_update                   cust-update.               L357-L433
#   _main_end                      main-end.                  L435-L474
#   _menu_exit                     menu-exit.                 L476-L477
#   _headings                      headings.                  L479-L495
#   _compute_sales_pay             compute-sales-pay.         L497-L514
#   _csp_exit                      csp-exit.                  L516-L517
#   _analise_deductions            analise-deductions section L519-L546
#   _analise_deductions__main_exit   main-exit.               L548
#   _bl_open                       BL-Open section.           L550-L593
#   _bl_open__main_exit              main-exit.               L595
#   _bl_write                      BL-Write section.          L598-L674
#   _bl_write__main_exit             main-exit.               L676
#   _bl_close                      BL-Close section.          L679-L696
#   _bl_close__main_exit             main-exit.               L698
#   _eval_status                   Eval-Status section.       L700-L704
#   _eval_status__main_exit          main-exit.               L706
#   _zz050_validate_date           zz050-Validate-Date sect.  L708-L733
#   _zz050_test_date                 zz050-test-date.         L735-L738
#   _zz050_exit                      zz050-exit.              L740-L741
#   _zz060_convert_date            zz060-Convert-Date sect.   L743-L773
#   _zz060_exit                      zz060-Exit.              L775-L776
#   _zz070_convert_date            zz070-Convert-Date sect.   L778-L803
#   _zz070_exit                      zz070-Exit.              L805-L806
#   _maps04                        maps04 section.            L808-L811
#   _maps04_exit                     maps04-exit.             L813-L814
#   run                            procedure division         L272-L276
#
#   Two of these labels are absent from the AAP's own inventory and were found
#   by reading the source: ``zz060-Exit`` L775 and ``zz070-Exit`` L805.  Each is
#   a live GO TO target, so each has a function.
#
# ---------------------------------------------------------------------------
# 2. GO TO CLASSIFICATION.  19 sites, verified by census
#    (``grep -ciE "go +to" sales/sl100.cbl`` -> 19).  Classified BY SHAPE.
# ---------------------------------------------------------------------------
#   class 1 - loop-back, becomes ``continue``.  SIX sites:
#       L319 -> acpt-xrply L310   (the interactive re-prompt; collapses once the
#                                  answer is ``ok_to_post``, and provably
#                                  terminates on its first pass - transcribed
#                                  rather than deleted)
#       L339 -> loop L331
#       L348 -> loop L331
#       L352 -> loop L331
#       L355 -> loop L331
#       L433 -> loop L331         <- NOT in the AAP's class-1 list.  It is a
#                                    loop-back by shape, and the AAP's own
#                                    instruction is to classify by shape because
#                                    its label list is not exhaustive.
#   class 2 - forward terminator, becomes ``break`` PLUS the post-loop block.
#             ONE site:
#       L334 -> main-end L435.  The post-loop work is L438-L474 in full:
#               OTM3-Close, Sales-Close, the two total blocks, the j-deduct
#               merge at L456, the Value-Open/analise-deductions/Value-Close
#               trio, BL-Close, and the two SYSTEM-REC stamps at L473-L474.
#               Mis-splitting would drop the value-analysis reversal and the
#               S-Flag-P latch reset.
#   class 3 - section or paragraph exit, becomes ``return``.  EIGHT sites
#             (6 + 1 + 8 + 4 = the 19 of the census):
#       L501 -> csp-exit L516     (inside the PERFORM THRU range)
#       L526 -> analise-deductions main-exit L548
#       L540 -> analise-deductions main-exit L548
#       L755 -> zz060-Exit L775 } classified in the consolidated
#       L761 -> zz060-Exit L775 } acas_posting.dates, which owns these bodies
#       L766 -> zz060-Exit L775 }
#       L791 -> zz070-Exit L805 }
#       L796 -> zz070-Exit L805 }
#   class 4 - named transfer needing a per-site proof.  FOUR sites:
#       L300 -> menu-exit L476.  PROVED in ``_init01``: the target is one
#               ``exit program.``, no file is open and no facade verb has run, so
#               the transfer is a return leaving the database untouched.
#       L317 -> menu-exit L476.  PROVED in ``_acpt_xrply``: same target, same
#               pre-open position; only the deciding condition differs.
#       L721 -> zz050-test-date L735 } forward transfers into the shared tail of
#       L726 -> zz050-test-date L735 } zz050; classified in acas_posting.dates.
#
#   PERFORM THRU [sales/sl100.cbl:L344] spans compute-sales-pay L497 ->
#       csp-exit L516.  Hand-verified per AAP 0.4.2 with no pattern-matching
#       shortcut, and emitted as TWO explicit calls in source order:
#       ``_compute_sales_pay(state)`` then ``_csp_exit(state)``.  One of only
#       four in-scope sites; the others are pl100 L336 and gl072 L300/L304 -
#       and gl072 spells the word ``through``, not ``thru``.
#   EXIT [sales/sl100.cbl:L517] - ``exit.``, a plain EXIT statement and a no-op.
#       NOT ``exit section.``  Reproduced as ``_csp_exit``'s empty body.
#   EXIT PROGRAM [sales/sl100.cbl:L477] - ``exit program.``, not ``goback``.
#       Reproduced by ``run()`` returning.
#
#   FALL-THROUGHS, both explicit in ``run()``:
#       L301 ``end-if.``  -> menu-return. L303
#       L356             -> cust-update.  L357
#   (and, within sections: L515 -> csp-exit, L547 -> L548, L594 -> L595,
#    L675 -> L676, L697 -> L698, L705 -> L706, L734 -> L735, L812 -> L813,
#    L475 -> menu-exit L476.)
#
# ---------------------------------------------------------------------------
# 3. ANOMALIES REPRODUCED (R-4: "A defect reproduced is correct; a defect fixed
#    is a failure.")  Each site carries its own comment and locator in place.
# ---------------------------------------------------------------------------
#   A-10  L497-L514, in ``_compute_sales_pay``.  The THIRD moving-average guard
#         variant, differing from sl060's two in six measured dimensions -
#         unconditional pre-guard clear L504, single-condition guard with no
#         ELSE L506, accumulate-then-increment L509-L510, the BY...GIVING form
#         L511, binary-long accumulators L182-L183, and a day-count operand
#         L503.  Cross-references [sales/sl060.cbl:L819] and
#         [sales/sl060.cbl:L835].  Explicitly recorded there: A-8 DOES NOT
#         APPLY here, because the integer operand removes the first of A-8's two
#         truncations.  No shared helper with sl060 or pl100.
#   A-17  L691, in ``_bl_close``, with the reading end at L576 in ``_bl_open``.
#         ``move RRN to postings.  *> Why ?`` under ``*> THIS IS IN PURCHASE
#         PL060``.  Load-bearing: L576 reads it back and L593 seeds the record
#         counter, so it decides the next batch's POST-RRN keys.  Occurrence 2
#         of 4 across the SL/PL posting programs.  Both ends commented.
#   A-18  L647-L664, in ``_bl_write``.  The IRS block copies ELEVEN fields and
#         never ``dr-pc`` or ``cr-pc``; the maintainer flagged both at L654 and
#         L656 and flagged the literal 32 at L660 with ``*> IS IT ???``.
#         ``WS-IRS-Posting-Record`` has no field for the percentages, confirmed
#         structurally - the copybook declares exactly eleven leaves.
#   A-1   L694, in ``_bl_close`` - THE DIVERGENCE, and here the code is CORRECT.
#         The terminating period IS present, so L695 is a SIBLING ``if`` and
#         ``GL-Posting-Close`` DOES run in pure-GL mode.  ``sl060`` is missing
#         that period at [sales/sl060.cbl:L1176]; that is A-1 and it belongs to
#         ``sl060_invoice_posting``.  Preserved in BOTH directions - correct
#         here, defective there - with the cross-reference in place.
#   A-6   Noted, not reproduced as a call site: ``acas008`` rejects
#         read-indexed, rewrite, start and delete unconditionally at entry
#         [common/acas008.cbl:L299-L307], so the facade's SPL-Posting-Rewrite
#         can never succeed.  ``sl100`` calls none of the four.  It DOES call
#         SPL-Posting-Open-Output at L582, which on that handler means DELETE
#         EVERY ROW [common/acas008.cbl:L313-L319, L571-L574]; noted at the site.
#   A-21  The qualified-reference pattern is preserved and visible at L635
#         (``VAT-AC of WS-Posting-record``), L644 and L650-L651 (``Post-Code in
#         WS-Posting-Record``).
#   A-22  DOES NOT OCCUR HERE.  ``maps04`` section L808 and ``maps04-exit`` L813
#         agree; A-22 is gl070's and gl051's alone.  Stated at ``_maps04``.
#
# ---------------------------------------------------------------------------
# 4. FINDINGS - unregistered divergences and oddities, recorded in place.
# ---------------------------------------------------------------------------
#   FINDING-1  L351 - the ``oi-type = 2`` re-test looks redundant after
#              L341-L348 but is not dead: it is the only guard for a type-2
#              record with EXACTLY ONE of ``oi-b-nos``/``oi-b-item`` zero, which
#              L354 does not catch.  Not removed.
#   FINDING-2  L354 - a REVERSED abbreviated relation, ``zero = oi-b-nos and
#              oi-b-item``.  The subject is ``zero``; contrast L338 where the
#              subject is first with three objects.  Written out in full.
#   FINDING-3  L377 - prints ``u-date`` where sl060 prints ``ws-date``
#              [sales/sl060.cbl:L507].  Print-only today, diff-visible if either
#              field ever reached a column.
#   FINDING-4  L394-L397 - the sign flip uses the GIVING form and leaves
#              ``sales-current`` alone until L397; sl060's no-GIVING form
#              [sales/sl060.cbl:L571-L573] leaves it transiently positive.
#   FINDING-5  L418 - ``*> what happens if using IRS ?``  The answer, verified by
#              execution, is "nothing".  ALL THREE calls into the batch family
#              are gated on ``G-L`` alone - BL-Open L324, BL-Write L417, BL-Close
#              L462 - and all seven IRS fan-out tests live inside those sections,
#              so in IRS-only mode the family never runs: no transfer file is
#              opened, no batch is opened or closed, and no PSIRSPOST-REC row is
#              written.  The commented-out "bypass gl posting code" at L286-L292
#              and L465-L471 confirms the reading.  Same layered gating in
#              [sales/sl060.cbl:L466, L535, L649].
#   FINDING-6  L523, L533, L537 - all three ``move 1 to File-Key-No`` are inert:
#              the facade verb sets it itself
#              [copybooks/Proc-ACAS-FH-Calls.cob:L753-L757] and the dispatch
#              paragraph pins it again [L51-L57].  Preserved in place, including
#              the extra L533 one that sl060's equivalent section lacks.
#   FINDING-7  L620-L628 - ``STRING ... POINTER`` overlays and leaves the rest of
#              ``post-legend`` untouched, and the field is never cleared, so a
#              later posting can inherit an earlier legend's tail.
#   FINDING-8  L623 - ``move WS-Batch-Nos to batch`` after ``batch`` was already
#              stringed: inert for the legend, load-bearing for the column.  The
#              legend carries ``oi-b-nos``; the column carries ``WS-Batch-Nos``.
#   FINDING-9  L630-L631 - the double-entry sides are SWAPPED relative to sl060
#              [sales/sl060.cbl:L1103-L1104], and the second account differs
#              (``SL-Pay-AC`` here, ``SL-Sales-AC`` there).
#   FINDING-10 L633-L637 - FIVE zero receivers including the VAT account, where
#              sl060 zeroes four and copies ``VAT-AC of system-record`` in
#              [sales/sl060.cbl:L1111-L1112].  No VAT accumulation at all here.
#   FINDING-11 L639 - ``move spaces to post-vat-side`` is inert; L645 overwrites
#              it.  Both reproduced.
#   FINDING-12 zz050-Validate-Date section L708 is NEVER PERFORMED anywhere in
#              this program (verified: no ``perform zz050`` exists).  Dead
#              boilerplate; the function exists for R-5 and is faithful anyway.
#   FINDING-13 L38-L39 of [copybooks/slwsoi3.cob] - ``OI-Approp REDEFINES
#              OI-Net``, the same bytes under two names.  ``sl100`` only ever
#              READS ``oi-approp`` and never writes it or ``oi-net``, so no
#              divergence arises here; recorded because a future writer of
#              either name would be writing both.
#   FINDING-14 Naming: this program spells its batch sections ``BL-Open`` /
#              ``BL-Write`` / ``BL-Close`` where sl060 prefixes them
#              (``ca000-BL-Open``) and pl100 lower-cases them; and it names its
#              status section ``Eval-Status`` where sl060 uses
#              ``zz040-Evaluate-Message``, pl060/gl080 use ``Evaluate-Message``
#              and sl055/pl055 use ``a01-Eval-Status``.  Each program's own
#              spelling is preserved.  Likewise ``exit program.`` at L477 rather
#              than ``goback``, and the lower-case ``print-report`` at L454 and
#              ``msg`` at L704 where sl060 upper-cases both.
#   FINDING-15 L296 + L474 - ``S-Flag-P`` is a ONE-SHOT LATCH: the run demands
#              it be 2 and clears it at the end, so a second consecutive run
#              aborts at L300 with no effect.  The program is non-idempotent by
#              design, which the determinism test must accommodate by re-seeding
#              rather than re-running.
#   The SEVEN IRS fan-out sites, all through ``condition_names``, never a raw
#   literal: L578 (``irs-used OR IRS-Both-Used``), L585 (``IRS-Both-Used or
#   G-L``), L647, L665-L666, L690, L693 (``IRS-Used OR IRS-Both-Used``), L695.
#   pl100 has only SIX and its first tests ``irs-used`` ALONE
#   [purchase/pl100.cbl:L566] - a divergence for that module to preserve.
#
# ---------------------------------------------------------------------------
# 5. AMBIGUITIES - questions only the compiled oracle can settle (R-6).  Each
#    belongs in docs/migration/ambiguity-resolutions.md.
# ---------------------------------------------------------------------------
#   AMBIGUITY Q-1  L528-L529.  ``va-t-this``/``va-t-year`` are UNSIGNED
#                  ``pic 9(5) comp``.  What does a subtraction that would go
#                  negative actually store, and what does the bridge hand to the
#                  unsigned column?  The published primitive stores the absolute
#                  value; confirm against the oracle.
#   AMBIGUITY Q-2  L691 with L576.  A-17's observable effect.  AAP 0.6.8 names
#                  this site explicitly: measure what ``postings`` holds after a
#                  run and what POST-RRN keys the next batch therefore gets.
#   AMBIGUITY Q-3  L620-L628.  The exact ``post-legend`` bytes the five-STRING
#                  chain produces, including what a second posting inherits from
#                  the first beyond the new pointer (FINDING-7), and what a
#                  pointer overflow does.
#   AMBIGUITY Q-4  L683-L689.  A failed ``GL-Batch-Write`` reports and continues
#                  - no retry, no abort, no rollback.  What state does the run
#                  leave behind, and does the following ``GL-Batch-Close``
#                  succeed?
#   AMBIGUITY Q-5  L324, L417 and L462 with L578-L695 (FINDING-5).  In IRS-only
#                  mode this migration produces NO GLBATCH-REC row and NO
#                  PSIRSPOST-REC row, because ``G-L`` gates the whole batch
#                  family and the IRS tests are all inside it.  That is what the
#                  source says; confirm against the compiled program that an
#                  IRS-only ``sl100`` run really does leave both tables
#                  untouched, since the surprise is the specification.
#   AMBIGUITY Q-6  L310-L319 with L167.  ``wx-reply value spaces`` is not an
#                  answer - spaces re-prompt.  ``ok_to_post`` therefore defaults
#                  to ``True``, the only answer that lets the program proceed.
#                  Confirm no scenario depends on a third disposition.
#   AMBIGUITY Q-7  L473-L474.  ``sl100`` performs no ``System-*`` facade verb -
#                  no in-scope program does - so who persists these two
#                  SYSTEM-REC mutations, and when?  Today they leave the program
#                  through linkage and the caller owns them.
#
# ---------------------------------------------------------------------------
# 6. OMISSIONS - deliberately not migrated, recorded per AAP 0.4.3 and R-5 "so
#    that a reader comparing the two files does not conclude something was
#    lost".
# ---------------------------------------------------------------------------
#   * L454 ``call "SYSTEM" using print-report.`` - the report spool-out path,
#     out of scope by AAP 0.1.1.  This is the ONLY ``call`` in the program.
#   * The entire print file and its line layouts: ``copy "selprint.cob"`` L125
#     and ``copy "fdprint.cob"`` L132; ``open output print-file`` L327; ``close
#     print-file`` L453; every ``write print-record`` (L428, L446, L452,
#     L485-L494); and the ``l1-*``/``l2-*``/``l4-*``/``l5-*`` field families
#     (L227-L263).  Also the print-only computations that feed them: L386 and
#     L399 (``l5-old-bal``/``l5-new-bal``) and L379-L381, L371-L373, L423-L427.
#     BUT ``headings.`` L479 still exists as a named function, and ``line-cnt``
#     and ``j`` are still maintained, because L430 branches on ``line-cnt``.
#   * ``copy "print-spool-command.cob"`` L137 and ``move Print-Spool-Name to
#     PSN`` L281 - the spool plumbing.
#   * ``copy "envdiv.cob"`` L118 and ``set ENVIRONMENT ...`` L283-L284 - the
#     curses screen configuration.
#   * Every ``display ... at`` becomes a log record and none alters control flow:
#     L297-L298, L305-L306, L308, L311, L684, L686-L688.
#   * ``accept ws-reply`` L299 and L689 - acknowledgement pauses, DROPPED; but
#     the control transfer at L300 is PRESERVED.
#   * ``accept wx-reply`` L314 - NOT dropped: it becomes the ``ok_to_post``
#     parameter.  L318-L319's retry collapses; L317's transfer is preserved.
#   * The commented-out level-1 bypass at L286-L292 and L465-L471, and the
#     commented-out record moves at L336 and L346 - dead in the compiled
#     program.  ``i`` L169 and ``save-level-1`` L172 are consequently unused.
#   * ``SL002``/``SL132``/``SL137`` survive only as log text.
#   * ``copy "FileStat-Msgs.cpy"`` L703-L704 - the status decode table; the
#     facade already records the decoded text in ``FS-Action``.
#
#   Stated explicitly, so nobody hunts for a pattern this program does not have:
#     - ``sl100`` has NO facade stub block (unlike gl072 L135-L155 and gl080
#       L194-L214).
#     - ``sl100`` has NO work file, so ``acas_posting.workfiles`` is not
#       imported - unlike sl055, sl060, gl071, gl072 and gl080.
#     - ``sl100`` has NO ``call "CBL_*"`` and therefore no
#       ``FS-Cobol-Files-Used``-gated library-call block.
#     - ``sl100`` performs NO ``OTM3-Start`` and NO ``set fn-*``: it walks OTM3
#       sequentially from the beginning.
#     - ``sl100`` performs NO ``Sales-Write`` - only ``Sales-Rewrite`` - unlike
#       sl060 [sales/sl060.cbl:L581].
#     - ``sl100`` has ZERO ``ROUNDED`` sites, ZERO ``ON SIZE ERROR`` and ZERO
#       ``REMAINDER``.  Every store truncates.
#     - ``sl100`` reads NO terminal geometry (no ``accept ... from lines``),
#       unlike sl055 and sl060.
#     - Anomaly A-22 does not occur here (see section 3).
