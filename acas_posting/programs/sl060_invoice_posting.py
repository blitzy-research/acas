"""`sl060` - Sales invoice posting and report [sales/sl060.cbl].

The whole program: it posts sales invoices to the Sales ledger, the open-item
file and - depending on the IRS fan-out switch
[copybooks/wssystem.cob:L179-L181] - the General Ledger posting file, the IRS
transfer file, or both.

Four defects here are reproduced, not repaired, and each one changes stored
values:

  * The moving average truncates TWICE. The accumulator `work-2` is declared with
    zero decimal places [sales/sl060.cbl:L206] while the value added into it
    carries two [sales/sl060.cbl:L218], so pence are discarded on every
    accumulation [sales/sl060.cbl:L826]; the divide that follows
    [sales/sl060.cbl:L827] then discards the remainder as well, because the
    average field is an integer [copybooks/wssl.cob:L49]. Both field widths are
    modelled exactly - carrying two decimals through would diverge on almost
    every invoice.
  * The invoice path and the credit-note path do the same job differently. The
    invoice path increments the activity counter before dividing
    [sales/sl060.cbl:L825]; the credit-note path NEVER increments it and also
    guards the whole computation on the accumulator being non-zero
    [sales/sl060.cbl:L841-L843], which silently drops a customer's first credit
    note. The divide is the same way round in both - accumulator over activity -
    so only the guard and the counter differ.
  * A missing terminating period nests the second conditional inside the first
    [sales/sl060.cbl:L1175-L1178], so in pure-General-Ledger mode the posting
    file is never closed. The three sibling programs all have the period
    [purchase/pl060.cbl:L1031], [sales/sl100.cbl:L694],
    [purchase/pl100.cbl:L675], which is what proves this one is an accident - and
    it is still reproduced.
  * An unexplained move carries the maintainer's own inline question mark
    [sales/sl060.cbl:L1173] and is reproduced with its observable effect
    unchanged.

Locators inside a :class:`~acas_posting.cobol.field.FieldDescriptor` are never
abbreviated: ``source_locator`` always carries the full path, because the
dictionary loader and the R-5 audit both match it against a pattern.

WHAT THE PROGRAM DOES, in its own on-screen words. Two phases, both named by
the program itself:

* "Phase 1 - Building OTM3 from OTM2" [sales/sl060.cbl:L472] walks the OTM2
  header extract that ``sl055`` produced, reads and updates each customer's
  sales-ledger row, writes the OTM3 open-item row, and emits GL and/or IRS
  posting records through a batch.
* "2 - Applying Cr. Notes to OTM3" [:L659] re-walks OTM3 and swaps any
  still-unapplied credit note, accumulating the carried-forward total.

The maintainer's own remarks [:L24-L44] describe it as step two of two, taking
input from OTM2, updating OTM3 from every OTM2 record and updating the analysis
value file with deduction totals so that a business can see who takes prompt-
payment discounts and who pays late.

THE LINKAGE - the SL/PL five-parameter shape, [sales/sl060.cbl:L395-L399]
VERBATIM::

     procedure division using ws-calling-data
                              system-record
                              system-record-4
                              to-day
                              file-defs.

Five parameters, and the third is spelled literally ``system-record-4``, from
``copy "wssys4.cob"`` [:L393]. :func:`run` mirrors that list exactly and is the
module's ONLY public name: AAP section 0.3.3, verbatim - "Each ``programs/*.py``
module exposes a single ``run(...)`` entry mirroring its COBOL ``PROCEDURE
DIVISION USING`` list, with the paragraph functions private to the module.
Callers cannot reach into a program's internals, exactly as a COBOL ``CALL``
cannot."

The caller is ``acas_posting.cli.sl_invoice_post``, which reproduces the menu's
``load07`` [sales/sales.cbl:L756-L768]: dispatch ``sl830``, gate on
``if ws-term-code not = zero``, dispatch ``sl055``, gate again, dispatch
``sl060``. That gate differs from the General Ledger's ``= 5`` test and from
Purchase, which has no gate at all. This module never sequences itself.

THIS IS THE MOST ANOMALY-DENSE MODULE OF THE TWELVE. It carries SIX of the
twenty-two register entries - more than any other program - plus five findings
that are not yet in the register. Every one is REPRODUCED, never fixed. AAP
section 0.8.2, verbatim: "There is no test suite: compiled COBOL execution is
the behavioral specification, defects included. A defect reproduced is correct;
a defect fixed is a failure."

* ANOMALY A-1  - the missing terminating period at [:L1176] nests the [:L1177]
  condition inside the [:L1175] condition, so ``GL-Posting-Close`` NEVER
  executes in pure-GL mode. Reproduced in :func:`_ca000_bl_close`.
* ANOMALY A-8  - double truncation of the moving average: pence discarded into
  a zero-scale accumulator [:L206, :L826], then the remainder discarded by an
  integer divide [copybooks/wssl.cob:L49, sales/sl060.cbl:L827]. Reproduced in
  :func:`_ba000_sales_comp` purely through the field descriptors.
* ANOMALY A-9  - the credit-note path never increments its activity counter and
  its extra guard [:L841] silently drops a customer's first credit note.
  Reproduced in :func:`_ba000_credit_comp`.
* ANOMALY A-10 - three mutually inconsistent guards on one idiom: [:L819],
  [:L835], [:L841] here and [sales/sl100.cbl:L506] there. The two local
  variants are TWO SEPARATE FUNCTIONS with deliberately duplicated-looking
  bodies. AAP section 0.6.1, verbatim: "Normalising them into one helper would
  be the single easiest way to fail this migration."
* ANOMALY A-17 - ``move RRN to postings`` [:L1173], carrying the maintainer's
  own ``*> Why ?``. It is NOT inert: [:L1037] reads ``postings`` back to
  allocate the next batch's starting RRN, so it is the posting-RRN high-water
  mark and has a diff-visible database effect.
* ANOMALY A-18 - ``dr-pc`` and ``cr-pc`` are never carried into the IRS posting
  record [:L1126-L1143]. The maintainer flagged it FIVE times: [:L1123-L1124],
  [:L1133], [:L1135], [:L1139] and in the 3.3.01 changelog entry [:L131].

* FINDING 7  - this program ends with ``exit program.`` [:L723], not ``goback``
  like every sibling in the folder.
* FINDING 8  - two unbounded table subscripts, the same shape as A-2 in
  ``gl080``: ``a`` from ``oi-type`` over an ``occurs 3`` table [:L509, :L526,
  :L527] and ``current-quarter`` over an ``occurs 4`` table [:L545, :L551,
  :L558].
* FINDING 9  - a missing ``write`` in the ``sales-missing`` diagnostic
  [:L702-L707]: the period on L707 binds the ``write`` to the ``else`` branch
  only, so in file mode the message is moved into the record and never written.
* FINDING 10 - an asymmetric three-way apportionment [:L935-L955]: the three
  arms disagree on which status fields they set and on whether they clear the
  invoice deduction.
* FINDING 11 - qualified references, the A-21 field-name-collision pattern the
  register records only for ``gl070``: [:L1111-L1112], [:L1116], [:L1129-L1130].

Two further structural facts, recorded because a reader will look for them:
``zz050-Validate-Date`` [:L1192] is DECLARED BUT NEVER PERFORMED anywhere in
this program - dead code retained as a named function for traceability; and
anomaly A-22 does NOT occur here, because the wrapper section ``maps04``
[:L1292] and its exit label ``maps04-exit`` [:L1297] agree. A-22 occurs only in
``gl070`` and ``gl051``.

THE FACADE CONVENTION. This program copies ``Proc-ACAS-FH-Calls.cob`` [:L1300],
so it uses the ENTITY-NAMED verb vocabulary and TESTS THE REPLY INLINE. It has
no per-handler error-check paragraph, because that convention belongs to
``Proc-ZZ100-ACAS-IRS-Calls.cob`` and this program does not copy it. Twenty-
seven distinct verbs are performed, across six entities: Sales (``acas012``),
OTM3 (``acas019``), Value (``acas013``), GL-Batch (``acas007``), GL-Posting
(``acas006``) and SPL-Posting (``acas008``).

Every facade paragraph in the copybook is two to four statements - it sets the
access type, sets the function code, sometimes forces ``File-Key-No``, then
performs the handler dispatch paragraph, which itself does ``move 1 to
File-Key-No`` and issues a five-argument ``CALL`` naming the PROGRAM's own
record areas [copybooks/Proc-ACAS-FH-Calls.cob:L20-L186]. The paragraphs take
no parameters because they operate on the program's storage. AAP section 0.4.3
renders that as a single-argument call, verbatim::

    FROM:  perform GL-Batch-Read-Next
    TO:    facade.gl_batch_read_next(ctx)

(that particular verb is the AAP's illustration and is NOT one sl060 performs;
the twenty-seven it does perform are listed in the traceability footer). So
every verb here is called as ``facade.<verb>(state)`` with ONE argument -
:class:`_Sl060State`, whose attribute names are the COBOL identifiers of the
dispatch paragraphs in snake case: ``system_record``, ``ws_sales_record``,
``ws_value_record``, ``ws_batch_record``, ``ws_posting_record``,
``ws_irs_posting_record``, ``ws_otm3_record``, ``file_access``, ``file_defs``
and ``acas_dal_common_data``. A successful read MUTATES the record area IN
PLACE, which is what ``acas019``'s own contract says
[acas_posting/dal/acas019_otm3.py], and what the COBOL ``CALL`` does.

HOW THE FACADE IS REACHED, since this module is the first program to need it -
its sibling ``gl071`` is a pure sort and its own docstring forbids importing
anything from ``acas_posting.dal`` at all:

* The import form is the one AAP section 0.4.3 mandates verbatim - ``copy
  "Proc-ACAS-FH-Calls.cob".`` becomes ``from acas_posting.dal import facade``.
  It is written plainly, at module scope, with no ``try``/``except``, no lazy
  ``__getattr__`` and no local shim. Any of those would hide a genuinely absent
  dependency and would leave a stub in the shipped package, which the zero-
  placeholder policy forbids outright.
* The twenty-seven verbs this module performs are enumerated in the traceability
  footer with the locator of every call site, so the surface this module requires
  of ``acas_posting.dal.facade`` is fully specified from here.
* Behaviour was verified against an in-memory double implementing all twenty-
  seven verbs, exercising each of the six anomalies, both period totals, the
  99-item batch cap, the two-pass credit-note walk, the OTM2 truncation and an
  end-to-end ``run``. The double remains the way to exercise the arithmetic
  without a database; the module itself binds the real facade.

WHICH TABLES A RUN TOUCHES, and why the gating must be traced before reading
any of the code below. Seven IRS fan-out sites test a three-state switch,
``05 IRS-Instead pic x.`` with ``88 IRS-Used value "Y"`` and
``88 IRS-Both-Used value "B"`` [copybooks/wssystem.cob:L179-L181], and the
General Ledger switch is ``88 G-L value 1.``
[copybooks/wssystem.cob:L85]. The sites are [:L1039],
[:L1046], [:L1126], [:L1144-L1145], [:L1172], [:L1175] and [:L1177], in three
distinct predicate shapes. THE GATING IS LAYERED: ``ca000-BL-Open`` is reached
only ``if G-L`` [:L466-L467] and ``ca000-BL-Write`` only ``if G-L`` [:L535-L536],
and each then tests the IRS flags again internally - so IN IRS-ONLY MODE THE BL
SECTIONS NEVER RUN AT ALL and no posting record of either kind is written. AAP
section 0.6.4 notes that the switch's state "changes which tables a run
touches", which is why a scenario must pin it.

With the gates open, the writers are ``SALEDGER-REC`` (``Sales-Write`` /
``Sales-Rewrite``), ``SAITM3-REC`` (``OTM3-Write`` / ``OTM3-Rewrite``),
``VALUEANAL-REC`` (``Value-Rewrite``), ``GLBATCH-REC`` (``GL-Batch-Write``),
``GLPOSTING-REC`` (``GL-Posting-Write``), ``PSIRSPOST-REC``
(``SPL-Posting-Write``), ``SYSTOT-REC`` (the two period-total adds) and - by way
of A-17 - ``SYSTEM-REC.POSTINGS``. The OTM2 work sequence reaches no table and
is TRUNCATED at [:L677-L678] once the transfer to OTM3 is complete.

PERIOD TOTALS - sites 3 and 4 of the nine. ``add total-deduct to
sl-credit-deductions`` [:L641] and ``add work-b to
sl-cn-unappl-this-month`` [:L700], both into ``system_record_4``. AAP
section 0.6.4 calls the nine sites "the sole writers" of ``SYSTOT-REC``. The
second is OUTSIDE the ``if`` at [:L695]: the print line is conditional, the add
is UNCONDITIONAL. Getting that wrong would drop a ``SYSTOT-REC`` write in file
mode and add one in RDBMS mode.

CONTROL TOTALS BALANCE BY CONSTRUCTION. [:L1118-L1121] accumulate
``Post-Amount`` into both ``input-gross`` and ``actual-gross`` and
``vat-amount`` into both ``input-vat`` and ``actual-vat`` - identically. That is
why AAP section 0.6.4 records that Sales and Purchase batches balance by
construction and the control-total-mismatch scenario is General-Ledger-specific.

THE RULES THIS FILE IS HELD TO - the AAP's six, section 0.7.2, restated only
where they bite on this file.

* R-1 NO COBOL AT RUNTIME. No ``subprocess``, no ``os.system``, no ``ctypes``,
  no ``cffi``, no ``cobc``, no reference to the comparison oracle. The four
  ``if FS-Cobol-Files-Used`` blocks that call ``CBL_CHECK_FILE_EXIST`` and
  ``CBL_DELETE_FILE`` [:L437-L444, :L448-L456, :L681-L689, :L711-L713] keep
  their gates - reproduced through the condition-name vocabulary so the
  decision stays data-driven exactly as the COBOL's is - and raise
  :exc:`_CobolLibraryRoutineUnavailable` inside, naming the routine. The branch
  is unreachable in the RDBMS configuration this migration targets, because
  ``88 FS-Cobol-Files-Used value zero`` [copybooks/wssystem.cob:L113] against
  ``88 FS-RDBMS-Used value 1``
  [copybooks/wssystem.cob:L116]. The spool-out path ``call "SYSTEM"
  using Print-Report`` [:L710] is omitted outright, out of scope by AAP
  section 0.1.1.
* R-2 ZERO BINARY FLOATING POINT. No ``float``, no ``complex``, no ``round()``,
  no bare ``/``, no hand-written ``quantize``, no hand-written scale alignment,
  ``MOVE`` truncation, ``INITIALIZE``, ``INSPECT``, ``STRING`` or reference
  modification. AAP section 0.3.1, verbatim: "``cobol/`` contains no business
  logic and ``programs/`` contains no numeric primitives." THIS PROGRAM HAS
  ZERO ``ROUNDED`` SITES - the five in the whole migration are in ``gl051``,
  ``gl080`` and ``irs030`` - so every store here truncates toward zero, which
  is :func:`arithmetic.store`'s default and is never overridden below.
* R-3 NO NEW VALIDATIONS, FIELDS OR SCHEMA CHANGES; NO CONCURRENCY. Not one
  ``if`` is added. No bounds check on either unbounded subscript, no period at
  [:L1176], no counter increment in :func:`_ba000_credit_comp`, no guard
  unification, no ``write`` at [:L704], no symmetry imposed on the three
  apportionment arms, no ``dr-pc``/``cr-pc`` in the IRS block, no retry or
  abort after a failed ``OTM3-Write`` or ``GL-Batch-Write``. No threads, no
  ``asyncio``, no ``multiprocessing``, no pooling. The repeated
  ``Value-Read-Indexed`` pairs, the twice-over subtract blocks and the
  redundant ``move 1 to File-Key-No`` are exactly what an optimiser would
  remove; AAP section 0.8.4, verbatim: "Any performance work is therefore out
  of scope by construction, not merely unrequested."
* R-4 LEGACY ANOMALIES REPRODUCED, NEVER FIXED. Every reproduction site carries
  an ``# ANOMALY A-<nn>`` comment citing its COBOL locator, which AAP
  section 0.7.4 C-4 prescribes as how engineering quality is expressed here.
* R-5 FULL TRACEABILITY. A named function per section AND per paragraph - all
  FORTY-FIVE labels, being seventeen sections and twenty-eight paragraphs,
  counted by matching label declarations across [:L395-L1301] rather than taken
  from the AAP's inventory, which lists the section heads only - with
  section-qualified names, because ``main-exit.``
  occurs SIX times [:L763, :L789, :L813, :L829, :L845, :L973]. Every transfer
  site is annotated with its ``GO TO`` class, every ``EXIT SECTION`` and the one
  ``EXIT PROGRAM`` are annotated as what they are, and the footer carries the
  full mapping.
* R-6 COMPILED BEHAVIOR IS THE TIE-BREAKER; DETERMINISM. No ambient clock: no
  ``datetime.now``, ``date.today``, ``time.time``, ``random``, ``uuid`` or
  ``os.urandom``, and ``acas_posting.clock`` is not imported. ``sales/sl060.cbl``
  contains ZERO clock reads; the two date observables arrive as ``to_day`` and
  ``Run-Date`` [copybooks/wssystem.cob:L67] through ``system_record``, and
  [:L1022] is where the binary run date is consumed. ``accept ws-env-lines from
  lines`` [:L403] is a terminal-geometry read, not a clock read, and is omitted.
  Open questions are marked ``# AMBIGUITY Q-<n>`` for the oracle to settle.

The section-by-section notes, the structural decisions, the omissions and the
complete traceability mapping are in the footer at the end of this module.
"""

from __future__ import annotations

import dataclasses
import logging
import typing
from decimal import Decimal
from typing import Callable, Final, Mapping, cast

from acas_posting import dates
from acas_posting.cobol import arithmetic, condition_names, move
from acas_posting.cobol.field import FieldDescriptor
from acas_posting.cobol.picture import descriptor_for
from acas_posting.dal import facade
from acas_posting.dal.status import AccessType, FsReply
from acas_posting.records import otm3, sales_ledger
from acas_posting.records.calling_data import WsCallingData
from acas_posting.records.file_access import FileAccess
from acas_posting.records.file_defs import FileDefs
from acas_posting.records.gl_batch import GlBatchRecord
from acas_posting.records.gl_posting import WsPostingRecord
from acas_posting.records.maps03 import Maps03Ws
from acas_posting.records.otm3 import OiHeader
from acas_posting.records.sales_ledger import WsSalesRecord
from acas_posting.records.spl_irs_posting import WsIrsPostingRecord
from acas_posting.records.system_record import SystemRecord
from acas_posting.records.system_record_4 import SystemRecord4
from acas_posting.records.test_data_flags import AcasDalCommonData
from acas_posting.records.value_analysis import WsValueRecord
from acas_posting.workfiles import (
    OPEN_ITEM_2_NAME,
    OpenItemWorkFile,
    open_item_work_file,
)

__all__: Final[tuple[str, ...]] = ("run",)


#: The frozen specification this module reproduces. Every locator below is relative to
#: it unless another path is named.
_PROGRAM: Final[str] = "sales/sl060.cbl"

_PROG_NAME: Final[str] = "SL060 (3.3.01)"

#: Diagnostics go here. AAP section 0.3.4: display output with no database effect "must
#: not alter control flow and must not appear in any table dump".
_LOG: Final[logging.Logger] = logging.getLogger("acas_posting.programs.sl060")


# R-1 - the boundary where a GnuCOBOL library routine would have been called.


class _CobolLibraryRoutineUnavailable(RuntimeError):
    """A ``call "CBL_..."`` site was reached, and R-1 forbids honouring it.

    Four blocks of this program call GnuCOBOL library routines behind an ``if FS-Cobol-
    Files-Used`` gate: ``CBL_CHECK_FILE_EXIST`` at [sales/sl060.cbl:L438] and [:L449]
    and [:L682], and ``CBL_DELETE_FILE`` at [:L713].
    """

    def __init__(self, routine: str, locator: str, argument: str) -> None:
        super().__init__(
            f'call "{routine}" using {argument} at [{locator}] was reached. '
            f"R-1 forbids invoking COBOL at runtime, so this CALL is not "
            f"honoured and is deliberately not emulated. The branch is gated "
            f"on FS-Cobol-Files-Used [copybooks/wssystem.cob:L113], which is "
            f"false in the RDBMS configuration this migration targets."
        )
        self.routine: Final[str] = routine
        self.locator: Final[str] = locator
        self.argument: Final[str] = argument


# Descriptor provenance R-2 and AAP section 0.3.1.


def _index_descriptors(record_class: type) -> dict[str, FieldDescriptor]:
    """Index every ``FieldDescriptor`` of a record layout by its COBOL name.

    The record modules publish their descriptors as a ``FIELDS`` tuple on each dataclass
    in the layout tree, so a group's children live on the group's own class. This walks
    that tree and returns a flat, CASE-INSENSITIVE index.
    """
    index: dict[str, FieldDescriptor] = {}
    seen: set[type] = set()

    def walk(cls: type) -> None:
        if cls in seen:
            return
        seen.add(cls)
        for descriptor in getattr(cls, "FIELDS", ()):
            index.setdefault(descriptor.name.casefold(), descriptor)
        hints = typing.get_type_hints(cls)
        for member in dataclasses.fields(cls):
            annotated = hints.get(member.name)
            if isinstance(annotated, type) and dataclasses.is_dataclass(annotated):
                walk(annotated)

    walk(record_class)
    return index


_SYSTEM: Final[dict[str, FieldDescriptor]] = _index_descriptors(SystemRecord)

_SYSTOT: Final[dict[str, FieldDescriptor]] = _index_descriptors(SystemRecord4)

#: ``copy "wssl.cob"`` [:L275] - SALEDGER-REC.
def _index_published_descriptors(
    published: typing.Mapping[str, FieldDescriptor],
) -> dict[str, FieldDescriptor]:
    """Re-key a module-level descriptor mapping on the COBOL name."""
    index: dict[str, FieldDescriptor] = {}
    for descriptor in published.values():
        index.setdefault(descriptor.name.casefold(), descriptor)
    return index


_SALES: Final[dict[str, FieldDescriptor]] = _index_published_descriptors(
    sales_ledger.FIELD_DESCRIPTORS
)

_BATCH: Final[dict[str, FieldDescriptor]] = _index_descriptors(GlBatchRecord)

_POST: Final[dict[str, FieldDescriptor]] = _index_descriptors(WsPostingRecord)

_IRSPOST: Final[dict[str, FieldDescriptor]] = _index_descriptors(WsIrsPostingRecord)

_VALUE: Final[dict[str, FieldDescriptor]] = _index_descriptors(WsValueRecord)

_ACCESS: Final[dict[str, FieldDescriptor]] = _index_descriptors(FileAccess)

_MAPS03: Final[dict[str, FieldDescriptor]] = _index_descriptors(Maps03Ws)


# WORKING-STORAGE, field for field from [sales/sl060.cbl:L196-L268] Declared here rather
# than in records/ because these are the PROGRAM's own storage, not a copybook layout.

_WS_REPLY: Final[FieldDescriptor] = descriptor_for(
    "pic x", name="ws-reply", source_locator=f"{_PROGRAM}:L197", parent_group="ws-data"
)
_WS_ERROR: Final[FieldDescriptor] = descriptor_for(
    "pic 9 value zero", name="ws-error",
    source_locator=f"{_PROGRAM}:L198", parent_group="ws-data",
)
_WX_REPLY: Final[FieldDescriptor] = descriptor_for(
    "pic xxx", name="wx-reply", source_locator=f"{_PROGRAM}:L200", parent_group="ws-data"
)
_XX: Final[FieldDescriptor] = descriptor_for(
    "pic 99", name="xx", source_locator=f"{_PROGRAM}:L201", parent_group="ws-data"
)
#: ``03 c-check pic 9.`` [:L202] with ``88 c-exists value 1`` [:L203].
_C_CHECK: Final[FieldDescriptor] = descriptor_for(
    "pic 9", name="c-check", source_locator=f"{_PROGRAM}:L202", parent_group="ws-data"
)
_WS_EVAL_MSG: Final[FieldDescriptor] = descriptor_for(
    "pic x(25) value spaces",
    name="ws-eval-msg",
    source_locator=f"{_PROGRAM}:L204",
    parent_group="ws-data",
)
_WORK_1: Final[FieldDescriptor] = descriptor_for(
    "pic s9(7)v99 comp-3 value zero",
    name="work-1",
    source_locator=f"{_PROGRAM}:L205",
    parent_group="ws-data",
)
#: ``03 work-2 pic s9(14) comp-3.`` [:L206] ANOMALY A-8 [sales/sl060.cbl:L206] -
#: FOURTEEN DIGITS, ZERO DECIMAL PLACES. This is one half of the double truncation.
_WORK_2: Final[FieldDescriptor] = descriptor_for(
    "pic s9(14) comp-3", name="work-2",
    source_locator=f"{_PROGRAM}:L206", parent_group="ws-data",
)
_WORK_A: Final[FieldDescriptor] = descriptor_for(
    "pic s9(7)v99 comp-3 value zero",
    name="work-a",
    source_locator=f"{_PROGRAM}:L207",
    parent_group="ws-data",
)
_WORK_B: Final[FieldDescriptor] = descriptor_for(
    "pic s9(7)v99 comp-3 value zero",
    name="work-b",
    source_locator=f"{_PROGRAM}:L208",
    parent_group="ws-data",
)
_FIRST_PASS: Final[FieldDescriptor] = descriptor_for(
    "pic x", name="first-pass", source_locator=f"{_PROGRAM}:L209", parent_group="ws-data"
)
_I: Final[FieldDescriptor] = descriptor_for(
    "pic 999", name="i", source_locator=f"{_PROGRAM}:L210", parent_group="ws-data"
)
_J: Final[FieldDescriptor] = descriptor_for(
    "pic 999", name="j", source_locator=f"{_PROGRAM}:L211", parent_group="ws-data"
)
_K: Final[FieldDescriptor] = descriptor_for(
    "pic 9(5)", name="k", source_locator=f"{_PROGRAM}:L212", parent_group="ws-data"
)
_M: Final[FieldDescriptor] = descriptor_for(
    "pic z(7)9", name="m", source_locator=f"{_PROGRAM}:L213", parent_group="ws-data"
)
_B: Final[FieldDescriptor] = descriptor_for(
    "binary-char value zero", name="b",
    source_locator=f"{_PROGRAM}:L214", parent_group="ws-data",
)
_C: Final[FieldDescriptor] = descriptor_for(
    "binary-char value zero", name="c",
    source_locator=f"{_PROGRAM}:L215", parent_group="ws-data",
)
_WORK_NET: Final[FieldDescriptor] = descriptor_for(
    "pic s9(7)v99 comp-3",
    name="work-net",
    source_locator=f"{_PROGRAM}:L216",
    parent_group="ws-data",
)
_WORK_VAT: Final[FieldDescriptor] = descriptor_for(
    "pic s9(7)v99 comp-3",
    name="work-vat",
    source_locator=f"{_PROGRAM}:L217",
    parent_group="ws-data",
)
#: ``03 work-goods pic s9(7)v99 comp-3.`` [:L218] ANOMALY A-8 [sales/sl060.cbl:L218] -
#: TWO DECIMAL PLACES, against work-2's zero [:L206]. The mismatch IS the first
#: truncation.
_WORK_GOODS: Final[FieldDescriptor] = descriptor_for(
    "pic s9(7)v99 comp-3",
    name="work-goods",
    source_locator=f"{_PROGRAM}:L218",
    parent_group="ws-data",
)
#: ``03 total-group occurs 3 comp-3.`` [:L219] - the OCCURS and the USAGE are both on
#: the GROUP, so the two children inherit COMP-3 from here.
_TOTAL_GROUP: Final[FieldDescriptor] = descriptor_for(
    "occurs 3 comp-3",
    name="total-group",
    source_locator=f"{_PROGRAM}:L219",
    parent_group="ws-data",
)
_TOTAL_NET: Final[FieldDescriptor] = descriptor_for(
    "pic s9(7)v99",
    name="total-net",
    source_locator=f"{_PROGRAM}:L220",
    level="05",
    inherited_usage=_TOTAL_GROUP.usage,
    inherited_usage_from="total-group",
    inherited_usage_source=f"{_PROGRAM}:L219",
    parent_group="total-group",
)
_TOTAL_VAT: Final[FieldDescriptor] = descriptor_for(
    "pic s9(7)v99",
    name="total-vat",
    source_locator=f"{_PROGRAM}:L221",
    level="05",
    inherited_usage=_TOTAL_GROUP.usage,
    inherited_usage_from="total-group",
    inherited_usage_source=f"{_PROGRAM}:L219",
    parent_group="total-group",
)
#: ``03 a pic 9 value zero.`` [:L222]
#:
#: FINDING 8(a) [sales/sl060.cbl:L222] - a SINGLE-DIGIT subscript over an
#: ``occurs 3`` table [:L219], loaded straight from ``oi-type`` [:L509] and used
#: unchecked at [:L526-L527]. ``oi-type`` 4 is a proforma and 5, 6, 7 and 9 are
#: all declared values [copybooks/slwsoi.cob:L20-L30], so the only thing keeping
#: the subscript in range is an UPSTREAM, IMPLICIT filter: ``sl055`` skips
#: proformas at [sales/sl055.cbl:L430-L431]. R-3 forbids adding the bounds
#: check the COBOL does not have, and R-4 forbids raising in its place - see
#: ``_add_to_total_group``, which stores through ``move.subscripted_store`` over
#: ``_WS_DATA_TOTALS_GROUP`` and so resolves an out-of-range subscript by byte
#: address exactly as the compiled program resolves it.
_A: Final[FieldDescriptor] = descriptor_for(
    "pic 9 value zero", name="a", source_locator=f"{_PROGRAM}:L222", parent_group="ws-data"
)
#: ``03 line-cnt pic 99 comp value zero.`` [:L223] - the page-break counter.
_LINE_CNT: Final[FieldDescriptor] = descriptor_for(
    "pic 99 comp value zero",
    name="line-cnt",
    source_locator=f"{_PROGRAM}:L223",
    parent_group="ws-data",
)
_WS_DEDUCTION: Final[FieldDescriptor] = descriptor_for(
    "pic s9(7)v99 comp-3 value zero",
    name="ws-deduction",
    source_locator=f"{_PROGRAM}:L224",
    parent_group="ws-data",
)
_TOTAL_DEDUCT: Final[FieldDescriptor] = descriptor_for(
    "pic s9(7)v99 comp-3 value zero",
    name="total-deduct",
    source_locator=f"{_PROGRAM}:L225",
    parent_group="ws-data",
)
_TOTAL_MOV_DED: Final[FieldDescriptor] = descriptor_for(
    "pic s9(5) comp value zero",
    name="total-mov-ded",
    source_locator=f"{_PROGRAM}:L226",
    parent_group="ws-data",
)
_SAVE_LEVEL_1: Final[FieldDescriptor] = descriptor_for(
    "pic 9 value zero",
    name="save-level-1",
    source_locator=f"{_PROGRAM}:L227",
    parent_group="ws-data",
)
_FILE_18_STATUS: Final[FieldDescriptor] = descriptor_for(
    "pic 9 value zero",
    name="File-18-status",
    source_locator=f"{_PROGRAM}:L231",
    parent_group="ws-data",
)

#: ``01 error-code pic 999.`` [:L272] - declared between two copybooks and never
#: referenced; retained for declaration fidelity.
_ERROR_CODE: Final[FieldDescriptor] = descriptor_for(
    "pic 999", name="error-code", source_locator=f"{_PROGRAM}:L272", level="01"
)

# ``01 ws-Test-Date pic x(10).`` [:L235] and ``01 ws-date-formats.`` [:L236-L257] are
# the group that acas_posting.dates.WsDateFormats publishes - the same four items and
# the same three REDEFINES views - so they are taken from there rather than redeclared.

# ---------------------------------------------------------------------------
# ``01 Error-Messages.`` [sales/sl060.cbl:L259-L268]
#
# Message text only, and NOT all of it reaches a log record. Section 0.3.4
# splits this group three ways:
#
#  * A DIAGNOSTIC display with no database effect becomes a log record at a
#  matching severity - `SL130` [:L591] and `SL132` [:L1163].
#  * A PROMPT whose only effect is to block a terminal is DROPPED, and with it
#  the `accept` it introduces - `SL002` [:L599, L1168] and `SL003` [:L734].
#  Both literals are nothing but the instruction to press a key, so there is
#  no substantive half to keep.
#  * REPORT CONTENT is out of scope entirely (section 0.2.2) - `SL133` and
#  `SL133T` are never displayed at all: they are `move`d into `print-record`
#  at [:L704, L706] and belong to the spool file.
#
# `SL131` is the one MIXED literal and is split below. Every member of the group
# stays DECLARED even where nothing references it, because rule R-5 maps the
# whole `01 Error-Messages.` group and a shorter group would misreport the
# frozen source. The widths are the declared ones.
# ---------------------------------------------------------------------------

_SL002: Final[str] = "SL002 Note error and hit return"
_SL003: Final[str] = "SL003 Hit Return To Continue"
_SL130: Final[str] = "SL130 Error writing Open Item 3 Record"
_SL131: Final[str] = "SL131 PE - CR SWOP: Return to continue"
_SL132: Final[str] = "SL132 Err on Batch file write : "
_SL133: Final[str] = "SL133 Warning Record/s missing in Sales File"
_SL133T: Final[str] = "SL133 Warning Record/s missing in Sales Table"

#: THE SUBSTANTIVE HALF OF `SL131`. The frozen literal carries two things in one
#: string: the diagnostic "PE - CR SWOP" - the payment/credit-swap notice raised
#: when a credit note nets to zero [:L732] - and, after the colon, the
#: instruction to press the key that [:L734-L735]'s `accept ws-reply` reads.
#: Section 0.3.4 keeps the first and drops the second, so the record below
#: carries this prefix. Taken by slicing the declared literal rather than
#: retyped, so the two can never drift apart.
_SL131_NOTICE: Final[str] = _SL131.split(":", 1)[0]

# ---------------------------------------------------------------------------
# ``copy "FileStat-Msgs.cpy"`` [sales/sl060.cbl:L1186]
#
# The copybook is TEXTUALLY INCLUDED into zz040-Evaluate-Message with
# ``replacing MSG by ws-Eval-Msg STATUS by fs-reply``, so its EVALUATE is part
# of this program and is transcribed here. No records/ or dal/ module publishes
# it: dal.status models the FS-Reply value set and the SQLSTATE mapping, not
# this presentation table. Every literal is 25 characters, the width of the
# receiver [:L204]; the MOVE below re-imposes that width from the descriptor
# rather than trusting the transcription.
# ---------------------------------------------------------------------------

_FILE_STATUS_MESSAGES: Final[dict[int, str]] = {
    0: "Success                  ",
    2: "Success Duplicate        ",
    4: "Success Incomplete       ",
    5: "Success Optional, Missing",
    6: "Multiple Records LS      ",
    7: "Success No Unit          ",
    9: "Success LS Bad Data      ",
    10: "End Of File              ",
    14: "Out Of Key Range         ",
    21: "Key Invalid              ",
    22: "Key Exists               ",
    23: "Key Not Exists           ",
    24: "Key Boundary violation   ",
    30: "Permanent Error          ",
    31: "Inconsistent Filename    ",
    34: "Boundary Violation       ",
    35: "File Not Found           ",
    37: "Permission Denied        ",
    38: "Closed With Lock         ",
    39: "Conflict Attribute       ",
    41: "Already Open             ",
    42: "Not Open                 ",
    43: "Read Not Done            ",
    44: "Record Overflow          ",
    46: "Read Error               ",
    47: "Input Denied             ",
    48: "Output Denied            ",
    49: "I/O Denied               ",
    51: "Record Locked            ",
    52: "End-Of-Page              ",
    57: "I/O Linage               ",
    61: "File Sharing Failure     ",
    71: "Bad Character LS         ",
    91: "Feature Not Available    ",
}

_FILE_STATUS_UNKNOWN: Final[str] = "Unknown File Status      "

# Condition names - every 88-level this program tests R-2 and the agent brief both
# forbid a bare "Y", "B", 1 or 0 standing in for a condition name.

_IS_G_L: Final[Callable[[int | str | Decimal], bool]] = condition_names.predicate_for("G-L")

_IS_IRS_USED: Final[Callable[[int | str | Decimal], bool]] = condition_names.predicate_for(
    "IRS-Used"
)

_IS_IRS_BOTH_USED: Final[Callable[[int | str | Decimal], bool]] = condition_names.predicate_for(
    "IRS-Both-Used"
)

_IS_FS_COBOL_FILES_USED: Final[Callable[[int | str | Decimal], bool]] = (
    condition_names.predicate_for("FS-Cobol-Files-Used")
)

_IS_CUSTOMER_DEAD: Final[Callable[[int | str | Decimal], bool]] = condition_names.predicate_for(
    "Customer-Dead"
)

_IS_S_CLOSED: Final[Callable[[int | str | Decimal], bool]] = condition_names.predicate_for(
    "S-Closed", copybook="copybooks/slwsoi.cob"
)

_SALES_MISSING: Final[condition_names.ConditionNameSpec] = condition_names.ConditionNameSpec(
    cobol_name="Sales-Missing",
    python_name="is_sales_missing",
    values=("1",),
    kind=condition_names.ConditionKind.SINGLE,
    conditional_variable="WS-Error",
    copybook=_PROGRAM,
    locator=f"{_PROGRAM}:L199",
    declaration_index=0,
    notes=(
        "Program-local 88 on ws-error [sales/sl060.cbl:L198]. Set to 1 when a "
        "customer's sales-ledger row is missing [:L496] and reported once at "
        "end of run [:L702] - where FINDING 9 loses the file-mode write."
    ),
)

#: ``88 c-exists value 1.`` [sales/sl060.cbl:L203] on ``c-check`` [:L202]. DECLARED AND
#: NEVER TESTED anywhere in the program; retained because R-5 traces declarations.
_C_EXISTS: Final[condition_names.ConditionNameSpec] = condition_names.ConditionNameSpec(
    cobol_name="C-Exists",
    python_name="is_c_exists",
    values=("1",),
    kind=condition_names.ConditionKind.SINGLE,
    conditional_variable="C-Check",
    copybook=_PROGRAM,
    locator=f"{_PROGRAM}:L203",
    declaration_index=1,
    notes="Program-local 88 on c-check; declared at [:L203] and never tested.",
)

_FILE_18_EXISTS: Final[condition_names.ConditionNameSpec] = condition_names.ConditionNameSpec(
    cobol_name="File-18-Exists",
    python_name="is_file_18_exists",
    values=("0",),
    kind=condition_names.ConditionKind.SINGLE,
    conditional_variable="File-18-Status",
    copybook=_PROGRAM,
    locator=f"{_PROGRAM}:L232",
    declaration_index=2,
    notes=(
        "Program-local 88 on File-18-status [:L231]. Note the VALUE IS ZERO, "
        "which is also the field's initial value, so the OTM2 file counts as "
        "existing until a library call says otherwise - and those calls are "
        "gated on FS-Cobol-Files-Used and refused under R-1."
    ),
)

_FILE_18_NOT_EXISTS: Final[condition_names.ConditionNameSpec] = (
    condition_names.ConditionNameSpec(
        cobol_name="File-18-Not-Exists",
        python_name="is_file_18_not_exists",
        values=("1",),
        kind=condition_names.ConditionKind.SINGLE,
        conditional_variable="File-18-Status",
        copybook=_PROGRAM,
        locator=f"{_PROGRAM}:L233",
        declaration_index=3,
        notes="Program-local 88 on File-18-status [:L231]; tested at [:L740].",
    )
)

#: ``88 si-s-open value zero.`` [copybooks/slwssoi.cob:L49] - on the SAVED header.
#: Declared and never tested.
_SI_S_OPEN: Final[condition_names.ConditionNameSpec] = condition_names.ConditionNameSpec(
    cobol_name="Si-S-Open",
    python_name="is_si_s_open",
    values=("zero",),
    kind=condition_names.ConditionKind.FIGURATIVE,
    conditional_variable="Si-Status",
    copybook="copybooks/slwssoi.cob",
    locator="copybooks/slwssoi.cob:L49",
    declaration_index=0,
    notes="On the saved open-item header; declared at [copybooks/slwssoi.cob:L49].",
)

_SI_S_CLOSED: Final[condition_names.ConditionNameSpec] = condition_names.ConditionNameSpec(
    cobol_name="Si-S-Closed",
    python_name="is_si_s_closed",
    values=("1",),
    kind=condition_names.ConditionKind.SINGLE,
    conditional_variable="Si-Status",
    copybook="copybooks/slwssoi.cob",
    locator="copybooks/slwssoi.cob:L50",
    declaration_index=1,
    notes="On the saved open-item header; the value ba000-Apportion stores.",
)


# The open-item header - one layout, three names, two storages STRUCTURAL NOTE 1.


def _dataclass_leaves(
    record_class: type, prefix: tuple[str, ...] = ()
) -> tuple[tuple[tuple[str, ...], type, str], ...]:
    """Every elementary item of a layout, as ``(path, owner class, name)``."""
    leaves: list[tuple[tuple[str, ...], type, str]] = []
    hints = typing.get_type_hints(record_class)
    for member in dataclasses.fields(record_class):
        annotated = hints.get(member.name)
        if isinstance(annotated, type) and dataclasses.is_dataclass(annotated):
            leaves.extend(_dataclass_leaves(annotated, prefix + (member.name,)))
        else:
            leaves.append((prefix + (member.name,), record_class, member.name))
    return tuple(leaves)


_OI_HEADER_LEAVES: Final[tuple[tuple[tuple[str, ...], type, str], ...]] = _dataclass_leaves(
    OiHeader
)


def _initial_oi_header() -> OiHeader:
    """A header at its figurative initial value: spaces for text, zero for numbers."""

    def build(record_class: type) -> object:
        arguments: dict[str, object] = {}
        hints = typing.get_type_hints(record_class)
        for member in dataclasses.fields(record_class):
            annotated = hints.get(member.name)
            if isinstance(annotated, type) and dataclasses.is_dataclass(annotated):
                arguments[member.name] = build(annotated)
                continue
            descriptor = otm3.descriptor_for(record_class, member.name)
            figurative = move.ZERO if descriptor.is_numeric else move.SPACE
            arguments[member.name] = move.move_figurative(figurative, descriptor)
        return record_class(**arguments)

    return typing.cast(OiHeader, build(OiHeader))


def _group_move_oi_header(source: OiHeader, target: OiHeader) -> None:
    """``move oi-header to si-header`` [:L851] / ``move si-header to oi-header`` [:L913].

    A group ``MOVE`` between two identically described 118-byte areas copies the bytes
    and converts nothing, so every elementary item is carried across unchanged.
    """
    for path, _owner, name in _OI_HEADER_LEAVES:
        from_group: object = source
        into_group: object = target
        for step in path[:-1]:
            from_group = getattr(from_group, step)
            into_group = getattr(into_group, step)
        setattr(into_group, name, getattr(from_group, name))


# The program's storage, as one object The facade's dispatch paragraphs name the
# program's own record areas - for example ``call "acas019" using System-Record WS-
# OTM3-Record File-Access File-Defs ACAS-DAL-Common-Data``
# [copybooks/Proc-ACAS-FH-Calls.cob:L132-L138] - and take no parameters, because a COBOL
# sub-program sees the caller's storage.


@dataclasses.dataclass(slots=True)
class _Sl060State:
    """Everything ``sl060`` can see: its linkage, its record areas, its storage."""

    ws_calling_data: WsCallingData
    system_record: SystemRecord
    system_record_4: SystemRecord4
    to_day: str
    file_defs: FileDefs

    ws_sales_record: WsSalesRecord
    ws_value_record: WsValueRecord
    ws_batch_record: GlBatchRecord
    ws_posting_record: WsPostingRecord
    ws_irs_posting_record: WsIrsPostingRecord
    ws_otm3_record: OiHeader
    file_access: FileAccess
    acas_dal_common_data: AcasDalCommonData

    maps03_ws: Maps03Ws
    ws_date_formats: dates.WsDateFormats

    # --- the OTM2 work sequence and the saved header ------------------------
    #: ``select open-item-file-2 assign file-18 ... organization sequential``
    #: [copybooks/seloi2.cob], record ``open-item-record-2 pic x(118)``
    #: [copybooks/fdoi2.cob]. It reaches NO schema table; see STRUCTURAL NOTE 4.
    open_item_file_2: OpenItemWorkFile[OiHeader]
    #: ``01 si-header.`` [copybooks/slwssoi.cob:L9]; see STRUCTURAL NOTE 2.
    si_header: OiHeader

    ws_reply: str = " "
    ws_error: int = 0
    wx_reply: str = "   "
    xx: int = 0
    c_check: int = 0  # [:L202] - never referenced
    ws_eval_msg: str = " " * 25
    work_1: Decimal = Decimal("0.00")
    work_2: int = 0  # [:L206] - SCALE 0; see ANOMALY A-8
    work_a: Decimal = Decimal("0.00")
    work_b: Decimal = Decimal("0.00")
    first_pass: str = " "
    i: int = 0
    j: int = 0
    k: int = 0
    m: str = " " * 8
    b: int = 0
    c: int = 0
    work_net: Decimal = Decimal("0.00")
    work_vat: Decimal = Decimal("0.00")
    work_goods: Decimal = Decimal("0.00")  # [:L218] - SCALE 2; see ANOMALY A-8
    #: ``03 total-group occurs 3`` [:L219] with ``05 total-net`` [:L220] and ``05 total-
    #: vat`` [:L221].
    total_net: list[Decimal] = dataclasses.field(
        default_factory=lambda: [Decimal("0.00")] * 3
    )
    total_vat: list[Decimal] = dataclasses.field(
        default_factory=lambda: [Decimal("0.00")] * 3
    )
    a: int = 0
    line_cnt: int = 0
    ws_deduction: Decimal = Decimal("0.00")
    total_deduct: Decimal = Decimal("0.00")
    total_mov_ded: int = 0
    save_level_1: int = 0
    file_18_status: int = 0
    error_code: int = 0  # [:L272] - never referenced

    #: NOT A COBOL FIELD. The keyword-only extras every facade ``PERFORM`` in this
    #: program forwards to its handler, chief among them the caller's
    #: transport-security policy. It has no COBOL counterpart because the frozen
    #: bridge has none: ``call "MySQL_real_connect"`` [common/otm3MT.cbl:L459]
    #: passes host, user, password, schema, port and socket and nothing else, so
    #: transport is compiled into ``cobmysqlapi.c`` rather than declared by the
    #: program.
    #:
    #: IT IS THE ONLY WAY A POLICY REACHES A HANDLER FROM HERE, and its default
    #: is an empty mapping, which every handler resolves against the INSTALLED
    #: PROCESS POLICY: under the exact-parity default
    #: ``connection._require_permitted_connection`` reports an unencrypted
    #: non-local hop at WARNING and connects, as the compiled open does (rule
    #: R-3), and only an explicitly hardened policy refuses it. This program
    #: reaches ``acas019`` for the OTM3 open-item file [:L1039-L1178], so a run
    #: against a non-local server must be given the declaration by its caller
    #: rather than assuming one - see ``run``'s ``dal_options``. Carried opaquely:
    #: nothing in this program reads a key of it, and ``dal/facade.py`` projects
    #: it onto whatever extras each handler declares.
    dal_options: Mapping[str, object] = dataclasses.field(default_factory=dict)

    @property
    def oi_header(self) -> OiHeader:
        """``oi-header`` - the SAME storage as ``ws_otm3_record``."""
        return self.ws_otm3_record

    def ctx(self, record: object) -> facade.FacadeContext:
        """The five operands one facade ``PERFORM`` passes, for ``record``'s entity.

        so the record area is named at the CALL SITE, one per verb, exactly as the
        copybook names it.
        """
        return facade.FacadeContext(
            self.system_record,
            record,
            self.file_access,
            self.file_defs,
            self.acas_dal_common_data,
            # The sixth operand has no COBOL counterpart and carries no accounting
            # value: it is the caller's keyword-only declarations, transport policy
            # among them, and it is attached to EVERY context this program builds so
            # that the policy does not depend on which entity a verb happens to
            # touch. `dal/facade.py` projects it onto the extras each handler
            # actually declares, so a handler that takes none is called exactly as
            # before. Empty by default, which every handler resolves against the
            # installed process policy.
            self.dal_options,
        )


#  THE ``sl055`` -> ``sl060`` HANDOFF IS ONE OBJECT, SUPPLIED BY THE CALLER.
#  ``select open-item-file-2 assign file-18`` [copybooks/seloi2.cob:L2] names a
#  FILE, and a file OUTLIVES the program that opened it: ``sl055`` writes the
#  extract - ``open extend`` [sales/sl055.cbl:L359], ``write oi-header``
#  [sales/sl055.cbl:L681], ``close`` [sales/sl055.cbl:L501] - and this program
#  then opens THE SAME FILE for input [:L480] and reads those records back
#  [:L484]. In COBOL the two programs name the same ``assign`` and the operating
#  system supplies the identity; here the identity is the
#  ``acas_posting.workfiles.OpenItemWorkFile`` the ROUTE threads from one
#  dispatch to the next, exactly as it threads the General Ledger work files from
#  ``gl070`` to ``gl071`` to ``gl072``.
#
#  THIS WAS ONCE A MODULE-LEVEL REGISTRY keyed by the assigned name. That did
#  make ``sl055``'s extract reachable, but it shared the sequence across every run
#  in one interpreter, and rule R-6 requires two runs of the same scenario under
#  the same pinned clock to be byte-identical - a sequence still holding the
#  previous run's invoices breaks that with nothing failing. ``run`` now takes the
#  carrier as a keyword-only parameter and declares a fresh one only when the
#  caller passes none, which is the same contract every other work file in the
#  migration has.


def _new_state(
    ws_calling_data: WsCallingData,
    system_record: SystemRecord,
    system_record_4: SystemRecord4,
    to_day: str,
    file_defs: FileDefs,
    open_item_file_2: OpenItemWorkFile[OiHeader],
) -> _Sl060State:
    """Bind the linkage and give every record area its declared initial value."""
    return _Sl060State(
        ws_calling_data=ws_calling_data,
        system_record=system_record,
        system_record_4=system_record_4,
        to_day=to_day,
        file_defs=file_defs,
        # `dal_options` is NOT bound here and NOT a parameter of `run`. The
        # transport policy reaches every handler through the one process-level
        # policy the CLI boundary installs, so the field keeps its declared `{}` -
        # which every handler resolves against that installed policy - rather than being threaded
        # call by call. See `_Sl060State.dal_options` and
        # `acas_posting.cli.args.install_connection_policy`.
        ws_sales_record=WsSalesRecord(),
        ws_value_record=WsValueRecord(),
        ws_batch_record=GlBatchRecord(),
        ws_posting_record=WsPostingRecord(),
        ws_irs_posting_record=WsIrsPostingRecord(),
        ws_otm3_record=_initial_oi_header(),
        file_access=FileAccess(),
        acas_dal_common_data=AcasDalCommonData(),
        maps03_ws=Maps03Ws(),
        ws_date_formats=dates.WsDateFormats(),
        # STRUCTURAL NOTE 4. ``assign file-18`` [copybooks/seloi2.cob] resolves
        # through ``File-Defs`` [copybooks/wsnames.cob], whose ``file18`` is
        # "openitm2". The sequence is the OTM2 extract ``sl055`` wrote; it
        # reaches no schema table and appears in no table dump, and [:L677-L678]
        # TRUNCATES it once the transfer to OTM3 is complete.
        # SUPPLIED BY THE CALLER, NOT CONSTRUCTED HERE. A file outlives the
        # program that opens it, so declaring a fresh empty sequence per call
        # would make ``sl055``'s extract unreachable - see the note above
        # ``_new_state``.
        open_item_file_2=open_item_file_2,
        si_header=_initial_oi_header(),
    )


#: ``03 total-group occurs 3`` [sales/sl060.cbl:L219] - the occurrence count, named once
#: so the boundary is stated rather than spelled as a literal at the use site.
_TOTAL_GROUP_OCCURS: Final[int] = 3


#: The tail of ``01 ws-data`` [sales/sl060.cbl:L216-L227], as the BYTES the
#: compiled program addresses. It exists for exactly two statements -
#: ``add work-vat to total-vat (a).`` [sales/sl060.cbl:L526] and ``add work-net to
#: total-net (a).`` [:L527] - because their subscript is unbounded and an
#: unbounded subscript lands on bytes, not on a list element.
#:
#: THE WINDOW STARTS AT ``work-net`` AND ENDS AT ``save-level-1``, which is what
#: the two statements can reach: occurrence 0 is the ten bytes immediately BEFORE
#: the table and occurrence 4 the ten immediately after, so the two neighbours on
#: each side plus the table itself are the whole of the addressable
#: neighbourhood. ``03 total-group occurs 3 comp-3.`` [:L219] is spelled as its
#: three occurrences, each ``total-net`` then ``total-vat`` [:L220-L221].
#:
#: THE LENGTH IS VERIFIED AGAINST THE COMPILED ORACLE, not asserted: GnuCOBOL
#: 3.2.0 reported ``function length`` = 62 for this window, which pins the widths
#: it chose - ``pic 99 comp`` is ONE byte and ``pic s9(5) comp`` is FOUR.
_WS_DATA_TOTALS_GROUP: Final[move.StorageGroup] = move.StorageGroup(
    (
        move.GroupItem("work-net", _WORK_NET),
        move.GroupItem("work-vat", _WORK_VAT),
        move.GroupItem("work-goods", _WORK_GOODS),
        #  The occurrences are laid out from the declared count rather than
        #  written out three times, so the table's extent has exactly one
        #  statement of truth - `_TOTAL_GROUP_OCCURS`, taken from [:L219].
        *(
            item
            for occurrence in range(1, _TOTAL_GROUP_OCCURS + 1)
            for item in (
                move.GroupItem(f"total-net ({occurrence})", _TOTAL_NET),
                move.GroupItem(f"total-vat ({occurrence})", _TOTAL_VAT),
            )
        ),
        move.GroupItem("a", _A),
        move.GroupItem("line-cnt", _LINE_CNT),
        move.GroupItem("ws-deduction", _WS_DEDUCTION),
        move.GroupItem("total-deduct", _TOTAL_DEDUCT),
        move.GroupItem("total-mov-ded", _TOTAL_MOV_DED),
        move.GroupItem("save-level-1", _SAVE_LEVEL_1),
    ),
    source_locator="sales/sl060.cbl:L216-L227",
)

#: Bytes per occurrence of ``total-group``: one ``total-net`` plus one
#: ``total-vat`` [sales/sl060.cbl:L220-L221]. Read from the descriptors rather
#: than written as a literal 10.
_TOTAL_GROUP_ELEMENT_BYTES: Final[int] = (
    _TOTAL_NET.byte_length + _TOTAL_VAT.byte_length
)

def _ws_data_totals_values(state: _Sl060State) -> dict[str, object]:
    """The window's current contents, keyed the way the byte layout names them.

    THE SUBSCRIPT IS UNCHECKED IN THE FROZEN SOURCE, AND THAT IS WHY A BYTE
    MODEL IS NEEDED. ``add work-vat to total-vat (a).`` [sales/sl060.cbl:L526] and
    ``add work-net to total-net (a).`` [:L527] index ``03 total-group occurs 3``
    [:L219] with ``03 a pic 9`` [:L222], loaded by ``move oi-type to a.`` [:L509].
    Nothing between the load and the use tests ``a``: the three-way
    ``if oi-type = 2 / = 3 / = 1`` [:L511-L517] chooses a PRINT literal and has no
    ``else``, so an ``oi-type`` of 0 - or of 4 through 9, which ``pic 9`` admits -
    flows straight through to the subscript. ANOMALY A-2's sibling; reproduced,
    never fixed (rule R-4).

    WHAT THE COMPILED PROGRAM DOES, measured on GnuCOBOL 3.2.0 against this exact
    declaration with a variable subscript and the source's own statement order:

        a = 0  ->  ``total-vat (0)`` IS ``work-goods`` and ``total-net (0)`` IS
                   ``work-vat``. With work-net 11.11, work-vat 22.22 and
                   work-goods 33.33 the oracle left work-vat 33.33 and
                   work-goods 55.55 - the first statement having read work-vat
                   BEFORE the second overwrote it.
        a = 4  ->  ``total-net (4)`` spans ``a``, ``line-cnt`` and the first three
                   bytes of ``ws-deduction``; ``total-vat (4)`` spans the last two
                   bytes of ``ws-deduction`` and the first three of
                   ``total-deduct``. Both emerged as packed values carrying
                   invalid nibbles, which the compiled program decodes tolerantly
                   rather than rejecting.

    NO CLAMP, NO MODULO, NO DEFAULT OCCURRENCE, NO SKIP AND NO EXCEPTION, and
    in particular NOT a bare Python ``[a - 1]``: that turns ``a = 0`` into a
    silent write to the THIRD occurrence, which corresponds to nothing the
    compiled program does. ``move.subscripted_store`` performs the addressing and
    its own header records the measurements.

    WHY ``work-goods`` MATTERS HERE. It is not one of the print-only totals: the
    accumulate at [:L545, :L551, :L558] adds it to ``STurnover-Q``, which the
    ``acas012`` handler persists. So an ``oi-type`` of 0 corrupting it has a real,
    diff-visible effect on ``SALEDGER-REC``, which is precisely why it is
    reproduced rather than approximated.
    """
    return {
        "work-net": state.work_net,
        "work-vat": state.work_vat,
        "work-goods": state.work_goods,
        "total-net (1)": state.total_net[0],
        "total-vat (1)": state.total_vat[0],
        "total-net (2)": state.total_net[1],
        "total-vat (2)": state.total_vat[1],
        "total-net (3)": state.total_net[2],
        "total-vat (3)": state.total_vat[2],
        "a": state.a,
        "line-cnt": state.line_cnt,
        "ws-deduction": state.ws_deduction,
        "total-deduct": state.total_deduct,
        "total-mov-ded": state.total_mov_ded,
        "save-level-1": state.save_level_1,
    }


def _restore_ws_data_totals(
    state: _Sl060State, after: typing.Mapping[str, object]
) -> None:
    """Write the window's decoded bytes back onto the program's storage.

    EVERY item is written back, not only the two the statement names, because an
    out-of-range subscript changes fields the statement does NOT name - that is
    the whole of the anomaly. Assigning only the totals would silently discard
    the reproduced effect.
    """
    state.work_net = cast(Decimal, after["work-net"])
    state.work_vat = cast(Decimal, after["work-vat"])
    state.work_goods = cast(Decimal, after["work-goods"])
    state.total_net = [
        cast(Decimal, after["total-net (1)"]),
        cast(Decimal, after["total-net (2)"]),
        cast(Decimal, after["total-net (3)"]),
    ]
    state.total_vat = [
        cast(Decimal, after["total-vat (1)"]),
        cast(Decimal, after["total-vat (2)"]),
        cast(Decimal, after["total-vat (3)"]),
    ]
    state.a = cast(int, after["a"])
    state.line_cnt = cast(int, after["line-cnt"])
    state.ws_deduction = cast(Decimal, after["ws-deduction"])
    state.total_deduct = cast(Decimal, after["total-deduct"])
    state.total_mov_ded = cast(int, after["total-mov-ded"])
    state.save_level_1 = cast(int, after["save-level-1"])


def _add_to_total_group(state: _Sl060State, member: str, addend: Decimal) -> None:
    """``add <addend> to <member> (a).`` - one unchecked subscripted accumulate.

    Args:
        state: The program's storage. ``state.a`` is the subscript, unvalidated.
        member: ``"total-net"`` or ``"total-vat"`` - the member of the occurrence
            the statement names.
        addend: The sending field's value, read before the store as COBOL reads
            it.
    """
    values = _ws_data_totals_values(state)
    statement = (
        "sales/sl060.cbl:L526" if member == "total-vat" else "sales/sl060.cbl:L527"
    )
    receiving = _TOTAL_VAT if member == "total-vat" else _TOTAL_NET
    #  The receiver is READ through the same addressing as the store, so an
    #  out-of-range occurrence contributes its ALIASED value to the sum.
    receiver_value = move.subscripted_value(
        _WS_DATA_TOTALS_GROUP,
        values,
        member=f"{member} (1)",
        element_length=_TOTAL_GROUP_ELEMENT_BYTES,
        subscript=state.a,
        statement=statement,
    )
    total = arithmetic.add_to(
        addend,
        receiver_value=cast(Decimal, receiver_value),
        receiving=receiving,
    )
    _restore_ws_data_totals(
        state,
        move.subscripted_store(
            _WS_DATA_TOTALS_GROUP,
            values,
            member=f"{member} (1)",
            element_length=_TOTAL_GROUP_ELEMENT_BYTES,
            subscript=state.a,
            value=total,
            statement=statement,
        ),
    )


_TURNOVER_QUARTER_FIELDS: Final[tuple[str, str, str, str]] = (
    "turnover_q1",
    "turnover_q2",
    "turnover_q3",
    "turnover_q4",
)

#: The ``Quarters`` window of ``01 WS-Sales-Record`` [copybooks/wssl.cob:L54-L68],
#: as the BYTES the compiled program addresses. It exists for the three
#: subscripted accumulates at [sales/sl060.cbl:L545, :L551, :L558], whose
#: subscript is ``05 Current-Quarter pic 9`` and is never tested.
#:
#: The window runs from ``Sales-Last`` - the field a subscript of 0 reaches - to
#: the trailing filler, which is as far as a single-digit subscript can carry:
#: quarter 9 addresses bytes 48 to 53 of a 52-byte window, so the window covers
#: every reachable in-group byte and the two beyond it are reported rather than
#: invented. ``Sales-Current`` is included because it precedes ``Sales-Last`` and
#: makes the window's own start unambiguous. ``03 filler redefines Quarters.``
#: [copybooks/wssl.cob:L60-L61] is the SAME bytes as ``Turnover-Q1`` through
#: ``Turnover-Q4``, so the four occurrences are listed once.
#:
#: THE LENGTH IS VERIFIED AGAINST THE COMPILED ORACLE: GnuCOBOL 3.2.0 reported
#: ``function length`` = 52 for exactly this window.
#: The two ``filler`` items of ``01 WS-Sales-Record`` share one COBOL name, so
#: ``_SALES`` - which is keyed on the COBOL name - cannot tell them apart. The
#: trailing one [copybooks/wssl.cob:L68] is therefore taken by its dictionary key
#: instead, which is unique per item.
_SALES_TRAILING_FILLER: Final[FieldDescriptor] = sales_ledger.FIELD_DESCRIPTORS[
    "filler_l68"
]

_SALES_QUARTERS_GROUP: Final[move.StorageGroup] = move.StorageGroup(
    (
        move.GroupItem("Sales-Current", _SALES["sales-current"]),
        move.GroupItem("Sales-Last", _SALES["sales-last"]),
        move.GroupItem("STurnover-Q (1)", _SALES["sturnover-q"]),
        move.GroupItem("STurnover-Q (2)", _SALES["sturnover-q"]),
        move.GroupItem("STurnover-Q (3)", _SALES["sturnover-q"]),
        move.GroupItem("STurnover-Q (4)", _SALES["sturnover-q"]),
        move.GroupItem("Sales-Unapplied", _SALES["sales-unapplied"]),
        move.GroupItem("Sales-Stats-Date", _SALES["sales-stats-date"]),
        move.GroupItem(
            "Sales-Partial-Ship-Flag", _SALES["sales-partial-ship-flag"]
        ),
        move.GroupItem("filler-68", _SALES_TRAILING_FILLER),
    ),
    source_locator="copybooks/wssl.cob:L54-L68",
)

#: Bytes per occurrence of ``STurnover-Q`` [copybooks/wssl.cob:L61]. Read from
#: the descriptor rather than written as a literal 6.
_STURNOVER_Q_ELEMENT_BYTES: Final[int] = _SALES["sturnover-q"].byte_length


def _sales_quarters_values(state: _Sl060State) -> dict[str, object]:
    """The quarters window's current contents, keyed as the byte layout names it."""
    sales = state.ws_sales_record
    quarters = sales.quarters
    return {
        "Sales-Current": sales.sales_current,
        "Sales-Last": sales.sales_last,
        "STurnover-Q (1)": quarters.turnover_q1,
        "STurnover-Q (2)": quarters.turnover_q2,
        "STurnover-Q (3)": quarters.turnover_q3,
        "STurnover-Q (4)": quarters.turnover_q4,
        "Sales-Unapplied": sales.sales_unapplied,
        "Sales-Stats-Date": sales.sales_stats_date,
        "Sales-Partial-Ship-Flag": sales.sales_partial_ship_flag,
        "filler-68": sales.filler_l68,
    }


def _add_to_turnover_quarter(state: _Sl060State, addend: Decimal) -> None:
    """``add work-goods to STurnover-Q (current-quarter)`` [:L545, :L551, :L558].

    STRUCTURAL NOTE 5 - THE REDEFINES THE RECORDS LAYER LEAVES OPEN.
    ``STurnover-Q`` is an ``occurs 4`` view over the same 24 bytes as
    ``Turnover-Q1`` through ``Turnover-Q4``; the sales-ledger layout publishes
    both and, in its own words about that pair, "nothing here designates one of
    them or keeps the two in step". The data-access layer persists ONLY the four
    named fields - it lists the view among its omitted copybook fields, as "the
    same storage as TURNOVER-Q1 through Q4 under a second name". Writing the
    view alone would therefore lose the update silently at the next
    ``Sales-Rewrite``. This function is the ONLY writer of either declaration in
    this module, and it writes BOTH, which is the caller-side aliasing the
    records layer deliberately left to the caller.

    FINDING 8(b) [sales/sl060.cbl:L545, :L551, :L558] - the subscript is
    ``05 Current-Quarter pic 9.`` [copybooks/wssystem.cob:L110], a single digit
    used with NO BOUNDS CHECK against an ``occurs 4`` table. It is the same
    field anomaly A-2 concerns in ``gl080``. R-3 forbids adding the check the
    COBOL does not have, so none is added - and R-6 forbids guessing what happens
    instead, so it was MEASURED.

    WHAT THE COMPILED PROGRAM DOES, on GnuCOBOL 3.2.0 against
    [copybooks/wssl.cob:L54-L68] transcribed verbatim, adding 77.77 with
    ``Sales-Last`` 200.02, the four quarters 1.01/2.02/3.03/4.04,
    ``Sales-Unapplied`` 500.05 and ``Sales-Stats-Date`` 2024:

        quarter = 0  ->  ``Sales-Last`` became 277.79. IT IS A TABLE COLUMN
                         [copybooks/wssl.cob:L55], so this has a real,
                         diff-visible effect on ``SALEDGER-REC``.
        quarter = 5  ->  ``Sales-Unapplied`` became 577.82. ALSO A COLUMN
                         [copybooks/wssl.cob:L63].
        quarter = 6  ->  ``Sales-Stats-Date`` and ``Sales-Partial-Ship-Flag``
                         received the packed image. BOTH COLUMNS.

    So unlike the print-only ``total-group`` case above, every out-of-range
    quarter here writes a persisted column, which is exactly why it is
    reproduced byte for byte through ``move.subscripted_store`` instead of being
    approximated, clamped or refused. A bare Python ``[quarter - 1]`` is NOT
    used: it would send quarter 0 into ``Turnover-Q4``, which the oracle shows is
    not what happens.
    """
    quarter = state.system_record.system_data_block.current_quarter
    sales = state.ws_sales_record
    after = move.subscripted_store(
        _SALES_QUARTERS_GROUP,
        _sales_quarters_values(state),
        member="STurnover-Q (1)",
        element_length=_STURNOVER_Q_ELEMENT_BYTES,
        subscript=quarter,
        value=arithmetic.add_to(
            addend,
            receiver_value=cast(
                Decimal,
                move.subscripted_value(
                    _SALES_QUARTERS_GROUP,
                    _sales_quarters_values(state),
                    member="STurnover-Q (1)",
                    element_length=_STURNOVER_Q_ELEMENT_BYTES,
                    subscript=quarter,
                    statement="sales/sl060.cbl:L545",
                ),
            ),
            receiving=_SALES["sturnover-q"],
        ),
        statement="sales/sl060.cbl:L545",
    )

    #  Every field of the window is written back, not only the quarters: an
    #  out-of-range subscript lands on ``Sales-Last``, ``Sales-Unapplied``,
    #  ``Sales-Stats-Date`` or ``Sales-Partial-Ship-Flag``, and all four are
    #  columns. Writing back only the quarters would discard the effect being
    #  reproduced.
    sales.sales_last = cast(Decimal, after["Sales-Last"])
    sales.sales_unapplied = cast(Decimal, after["Sales-Unapplied"])
    sales.sales_stats_date = cast(int, after["Sales-Stats-Date"])
    sales.sales_partial_ship_flag = cast(str, after["Sales-Partial-Ship-Flag"])

    quarter_values = tuple(
        cast(Decimal, after[f"STurnover-Q ({occurrence})"])
        for occurrence in range(1, len(_TURNOVER_QUARTER_FIELDS) + 1)
    )
    #  BOTH readings of the same bytes, as this function's structural note
    #  requires: the ``occurs`` view the COBOL statement names, and the four
    #  named fields the data-access layer persists.
    state.ws_sales_record.quarters_view.sturnover_q = quarter_values
    for attribute, stored in zip(
        _TURNOVER_QUARTER_FIELDS, quarter_values, strict=True
    ):
        setattr(state.ws_sales_record.quarters, attribute, stored)


_SALES_LEAVES: Final[tuple[tuple[tuple[str, ...], FieldDescriptor], ...]] = tuple(
    (path, sales_ledger.FIELD_DESCRIPTORS[".".join(path)])
    for path, _owner, _name in _dataclass_leaves(WsSalesRecord)
)


def _initialize_ws_sales_record(state: _Sl060State) -> None:
    """``initialize WS-Sales-Record with filler`` [sales/sl060.cbl:L497].

    ``INITIALIZE`` with no ``REPLACING`` phrase sets every elementary item to its
    category's figurative value - numeric items to ZERO, alphanumeric items to SPACES -
    and ``WITH FILLER`` extends that to the ``FILLER`` items an ordinary ``INITIALIZE``
    would leave alone.
    """
    numeric_paths: list[tuple[str, ...]] = []
    numeric_fields: list[FieldDescriptor] = []
    text_paths: list[tuple[str, ...]] = []
    text_fields: list[FieldDescriptor] = []
    for path, descriptor in _SALES_LEAVES:
        if descriptor.is_numeric:
            numeric_paths.append(path)
            numeric_fields.append(descriptor)
        else:
            text_paths.append(path)
            text_fields.append(descriptor)

    for paths, fields, figurative in (
        (numeric_paths, numeric_fields, move.ZERO),
        (text_paths, text_fields, move.SPACE),
    ):
        values = move.move_to_all(figurative, fields)
        for path, descriptor, value in zip(paths, fields, values, strict=True):
            owner: object = state.ws_sales_record
            for step in path[:-1]:
                owner = getattr(owner, step)
            if descriptor.occurs is None:
                setattr(owner, path[-1], value)
            else:
                setattr(owner, path[-1], tuple([value] * descriptor.occurs))

    for quarter_field in _TURNOVER_QUARTER_FIELDS:
        setattr(
            state.ws_sales_record.quarters,
            quarter_field,
            move.move_figurative(move.ZERO, _SALES[quarter_field.replace("_", "-")]),
        )


def _oi_customer_image(header: OiHeader) -> str:
    """The seven-byte sending image of the ``oi-customer`` GROUP.

    ``03 oi-customer.`` is ``05 oi-nos pic x(6)`` plus ``05 oi-check pic 9``
    [copybooks/slwsoi.cob:L11-L13], so a group MOVE or a group comparison sees six
    characters followed by one zoned digit.
    """
    check_digit = move.move_alphanumeric(
        header.oi_key.oi_customer.oi_check,
        _OI_CHECK_AS_TEXT,
        sending_field=otm3.descriptor_for(type(header.oi_key.oi_customer), "oi_check"),
    )
    return f"{header.oi_key.oi_customer.oi_nos}{check_digit}"


_OI_CHECK_AS_TEXT: Final[FieldDescriptor] = descriptor_for(
    "pic x",
    name="oi-check-as-text",
    source_locator="copybooks/slwsoi.cob:L13",
    level="05",
)


def _write_oi3_customer(state: _Sl060State, image: str) -> None:
    """Store seven bytes into ``oi3-customer`` [copybooks/slwsoi3.cob:L13].

    ``oi3-customer pic x(7)`` occupies the same seven bytes as the ``oi-customer``
    group, so a move into it lands in ``oi-nos`` and ``oi-check``; see STRUCTURAL NOTE
    1.
    """
    customer = state.oi_header.oi_key.oi_customer
    customer.oi_nos = move.move_alphanumeric(
        move.ref_mod(image, 1, 6), otm3.descriptor_for(type(customer), "oi_nos")
    )
    customer.oi_check = move.move_numeric(
        move.ref_mod(image, 7, 1), otm3.descriptor_for(type(customer), "oi_check")
    )


def _file_status_message(state: _Sl060State) -> str:
    """``copy "FileStat-Msgs.cpy"`` - map ``fs-reply`` to ``ws-Eval-Msg``."""
    text = _FILE_STATUS_MESSAGES.get(state.file_access.fs_reply, _FILE_STATUS_UNKNOWN)
    return move.move_alphanumeric(text, _WS_EVAL_MSG)


def run(
    ws_calling_data: WsCallingData,
    system_record: SystemRecord,
    system_record_4: SystemRecord4,
    to_day: str,
    file_defs: FileDefs,
    *,
    open_item_file_2: OpenItemWorkFile[OiHeader] | None = None,
) -> None:
    """Post the sales invoice extract: ``sl060``'s two phases, in order.

    Args:
        ws_calling_data: ``WS-Calling-Data`` [copybooks/wscall.cob:L7-L14]. The
            caller's identity matters: three acknowledgement prompts are skipped
            when ``WS-Caller`` is the unattended driver [:L600, :L734, :L1167],
            and that test is PRESERVED even though the prompts themselves are
            dropped, because it is the codebase's own unattended-mode check.
        system_record: ``SYSTEM-REC`` [copybooks/wssystem.cob]. Carries the
            General Ledger and IRS switches that decide which tables the run
            touches, the accounting cycle, the current quarter, the page depth,
            the two VAT and control account numbers, and ``Run-Date``
            [copybooks/wssystem.cob:L67] -
            the binary run date that becomes the batch's entered date [:L1022].
            It is MUTATED: ``S-Flag-I``, ``S-Flag-A`` and ``oi-3-flag`` are set
            at [:L434-L436], ``Next-Batch`` is advanced at [:L1018], and
            ``Postings`` is stamped at [:L1173] - see ANOMALY A-17.
        system_record_4: ``SYSTOT-REC`` [copybooks/wssys4.cob]. MUTATED at the
            two period-total sites [:L641] and [:L700].
        to_day: ``to-day pic x(10)``, the run date as ``DD/MM/CCYY``. One of the
            two observables the controlled clock pins; this program reads no
            clock of its own.
        file_defs: ``File-Defs`` [copybooks/wsnames.cob]. Supplies the OTM2 work
            file's name through ``file18``.
        open_item_file_2: The OTM2 work file ``sl055`` wrote - the SHARED
            ``acas_posting.workfiles.OpenItemWorkFile``, keyword-only because the
            frozen ``PROCEDURE DIVISION USING`` has exactly five entries
            [:L395-L399] and a sixth would misrepresent the linkage. It is what
            ``select open-item-file-2 assign file-18`` [copybooks/seloi2.cob:L2]
            resolves to for BOTH programs: the route passes the very object
            ``sl055`` returned, which is how [:L484] reads what
            [sales/sl055.cbl:L681] wrote. A None declares an empty file, in which
            case [:L484] takes its ``at end`` branch at once - exactly as it would
            against an empty file.

    Returns:
        None. ``sl060`` reports nothing back through its linkage.

    Raises:
        _CobolLibraryRoutineUnavailable: if a ``CBL_...`` gate is entered, which
            requires ``FS-Cobol-Files-Used`` to be true. See R-1.
    """
    #  THE OTM2 CHANNEL. ``sl055`` returns the carrier it wrote and the route
    #  passes it here, which is how [:L484] reads what [sales/sl055.cbl:L681]
    #  wrote. A None means the caller ran this program alone, in which case the
    #  file is declared empty - and [:L484] then takes its ``at end`` branch
    #  immediately, exactly as it would against an empty file.
    state = _new_state(
        ws_calling_data,
        system_record,
        system_record_4,
        to_day,
        file_defs,
        open_item_work_file(OPEN_ITEM_2_NAME, OiHeader)
        if open_item_file_2 is None
        else open_item_file_2,
    )
    _aa000_main_process(state)


def _aa000_main_process(state: _Sl060State) -> None:
    """``aa000-Main-Process section.`` [sales/sl060.cbl:L402] - open and set up.

    Ends by FALLING THROUGH into ``aa020-Read-Loop`` [:L483], which is the next label in
    the section, so the chain of paragraph functions below runs exactly as the straight-
    line COBOL does.
    """
    system = state.system_record

    # [:L403-L409] accept ws-env-lines from lines / geometry arithmetic. OMITTED:
    # terminal geometry, and NOT a clock read (R-6).

    _zz070_convert_date(state)


    _LOG.info("%s Invoice Posting & Report", _PROG_NAME)
    # [:L420] perform zz070-Convert-Date. The SECOND call, four lines after the first;
    # both are reproduced because both are written.
    _zz070_convert_date(state)
    # [:L421] display ws-date.
    #
    #  THE RUN DATE IS NOT IN A RECORD, so this display has no log counterpart.
    #  `ws-date` is the posting date this run stamps into every record it writes -
    #  a date with business meaning, which the safe-event schema in
    #  `acas_posting/dal/status.py` excludes (CWE-532). It is an INPUT the caller
    #  supplied through the `to-day` operand, already known wherever the run was
    #  started and pinned by `clock.py`, so no record is needed to reconstruct it.
    #  `zz070-Convert-Date` above still runs: it stores `ws-date` and may default
    #  `Date-Form` in the system record, which IS a table effect.

    # [:L422] move 1 to File-Key-No. Redundant against the facade's own dispatch
    # paragraphs, every one of which sets it [copybooks/Proc-ACAS-FH-Calls.cob:L44],
    # but written here and therefore reproduced (R-3, R-4).
    state.file_access.logging_data.file_key_no = move.move_numeric(
        1, _ACCESS["file-key-no"]
    )

    # [:L424-L431] aa010-Acpt-Xrply - the whole confirmation dialogue is COMMENTED OUT
    # in the frozen source, with the maintainer's reason.


    system.sales_ledger_block.s_flag_i = move.move_numeric(2, _SYSTEM["s-flag-i"])
    system.sales_ledger_block.s_flag_a = move.move_numeric(1, _SYSTEM["s-flag-a"])
    system.sales_ledger_block.oi_3_flag = move.move_alphanumeric(
        "Y", _SYSTEM["oi-3-flag"]
    )

    # [:L437-L444] R-1 GATE 1 of 4.
    if _IS_FS_COBOL_FILES_USED(system.system_data_block.rdbms_flat_statuses.file_system_used):
        # [:L438-L439] call "CBL_CHECK_FILE_EXIST" using File-19 File-Info.
        raise _CobolLibraryRoutineUnavailable(
            "CBL_CHECK_FILE_EXIST", f"{_PROGRAM}:L438", "File-19 File-Info"
        )

    # [:L446] The maintainer's own note.
    if _IS_FS_COBOL_FILES_USED(system.system_data_block.rdbms_flat_statuses.file_system_used):
        raise _CobolLibraryRoutineUnavailable(
            "CBL_CHECK_FILE_EXIST", f"{_PROGRAM}:L449", "File-18 File-Info"
        )

    # [:L458-L464] A COMMENTED-OUT bypass that would save Level-1 and set it to zero,
    # suppressing the General Ledger for this run.

    # [:L466-L467] if G-L perform ca000-BL-Open. THE GATING IS LAYERED. Only the General
    # Ledger switch opens the batch here.
    if _IS_G_L(system.system_data_block.level.level_1):
        _ca000_bl_open(state)

    facade.sales_open(state.ctx(state.ws_sales_record))

    _LOG.info("Posting......Please Wait")
    _LOG.info("Phase 1 - Building OTM3 from OTM2")

    state.j = move.move_figurative(move.ZERO, _J)
    _ba000_headings(state)

    # [:L477] move zeros to total-net (1) total-net (2) total-net (3). [:L478] move
    # zeros to total-vat (1) total-vat (2) total-vat (3).
    state.total_net = list(
        move.move_to_all(move.ZERO, (_TOTAL_NET, _TOTAL_NET, _TOTAL_NET))
    )
    state.total_vat = list(
        move.move_to_all(move.ZERO, (_TOTAL_VAT, _TOTAL_VAT, _TOTAL_VAT))
    )

    # [:L480] open input open-item-file-2. A DIRECT file verb, not a facade
    # verb: the OTM2 sequence is a work file and has no handler.
    state.open_item_file_2.open_input(state.file_access)
    # [:L481] perform OTM3-Open.
    facade.otm3_open(state.ctx(state.ws_otm3_record))

    _aa020_read_loop(state)


def _aa020_read_loop(state: _Sl060State) -> None:
    """``aa020-Read-Loop.`` [sales/sl060.cbl:L483] - phase 1, the posting loop."""
    system = state.system_record

    while True:
        # [:L484] read open-item-file-2 at end
        header = state.open_item_file_2.read_next(state.file_access)
        if header is None:
            break

        # [:L487] move open-item-record-2 to oi-header. A GROUP MOVE of the whole
        # 118-byte record.
        _group_move_oi_header(header, state.oi_header)

        oi = state.oi_header
        body = oi.filler_1
        money = body.filler_2
        sales = state.ws_sales_record
        # `oi.oi_key` IS DELIBERATELY NOT ALIASED HERE. This paragraph reaches no
        # field of the key group: `oi-customer` goes through
        # `_oi_customer_image(oi)` and `oi-invoice` was read only by the write-
        # failure diagnostic at [:L592-L594], whose two data operands are dropped
        # because they are business keys (see the note there).

        sales.ws_sales_key = move.move_alphanumeric(
            _oi_customer_image(oi), _SALES["ws-sales-key"]
        )
        state.ws_reply = move.move_figurative(move.SPACE, _WS_REPLY)
        facade.sales_read_indexed(state.ctx(state.ws_sales_record))
        if state.file_access.fs_reply == FsReply.INVALID_KEY_ON_START:
            state.ws_reply = move.move_alphanumeric("X", _WS_REPLY)

        if state.ws_reply == "X":
            state.ws_error = move.move_numeric(1, _WS_ERROR)
            _initialize_ws_sales_record(state)
            # [:L498] move "*** Customer Unknown ***" to l5-name sales-name. The print
            # receiver is omitted.
            sales.sales_name = move.move_alphanumeric(
                "*** Customer Unknown ***", _SALES["sales-name"]
            )
            sales.ws_sales_key = move.move_alphanumeric(
                _oi_customer_image(oi), _SALES["ws-sales-key"]
            )
        else:
            pass


        state.maps03_ws.u_bin = move.move_numeric(body.oi_date, _MAPS03["u-bin"])
        _zz060_convert_date(state)

        # [:L509] move oi-type to a.
        # FINDING 8(a) [sales/sl060.cbl:L509] - this is where the unchecked
        # subscript is loaded. oi-type carries nine declared values
        # [copybooks/slwsoi.cob:L20-L30] and the table has three occurrences
        # [:L219]; nothing here or downstream checks. R-3 forbids adding the
        # check.
        # AMBIGUITY Q-1 [sales/sl060.cbl:L509, :L526-L527] - WHICH oi-type
        # VALUES ACTUALLY REACH HERE must be measured against the compiled
        # oracle. The guard is upstream and implicit: sl055 filters proformas
        # (type 4) out of the OTM2 extract [sales/sl055.cbl:L430-L431], and the
        # three branches at [:L544], [:L550] and [:L557] only handle 1, 2 and 3.
        # But types 5, 6, 7 and 9 are declared, and a type 0 or a type above 3
        # would index `total-vat (a)` / `total-net (a)` outside the three
        # occurrences at [:L526-L527]. COBOL reads and writes the adjacent
        # storage silently, AND `_total_group_target` REPRODUCES THAT rather than
        # guarding it, because guarding is the fix rule R-4 forbids. It resolves
        # the subscript by BYTE ADDRESS over the work area's own declared widths:
        #  a = 1..3 -> the three declared occurrences. Print-only accumulators
        #  [:L616-L636], so no table column depends on them.
        #  a  = 0   -> EXACT, and NOT print-only. The ten bytes before the table
        #  are `work-vat` and `work-goods` [:L217-L218], so [:L526]
        #  becomes `work-goods += work-vat` and [:L527] becomes
        #  `work-vat += work-net`, IN THAT ORDER. Both receivers are
        #  read immediately afterwards by statements that write
        #  PERSISTED columns - `work-goods` at [:L545], [:L551],
        #  [:L558] into SALEDGER-REC's turnover quarters and at
        #  [:L826], [:L842] into the moving average that decides
        #  SALES-AVERAGE; `work-vat` at [:L530] and at [:L552],
        #  [:L559] into SALES-CURRENT. So a type-0 header corrupts
        #  four persisted columns, silently. Reproduced.
        #  a >= 4   -> NOT FIELD-ALIGNED. Subscript 4 spans `a`, `line-cnt` and
        #  part of `ws-deduction` [:L222-L224], so no declared field
        #  wholly receives either five-byte store. Nothing is changed
        #  and nothing is invented; AMBIGUITY Q-SL060-SUBSCRIPT is
        #  narrowed to exactly this band and logged when reached.
        # NEITHER a Python `[a - 1]` NOR AN EXCEPTION was acceptable: the first
        # silently writes the THIRD occurrence when `a` is zero, and the second
        # refuses a store the compiled program performs.
        state.a = move.move_numeric(body.oi_type, _A)


        state.work_vat = arithmetic.add_giving(
            money.oi_vat,
            money.oi_c_vat,
            money.oi_e_vat,
            body.oi_deduct_vat,
            receiving=_WORK_VAT,
        )
        state.work_goods = arithmetic.add_giving(
            money.oi_net, money.oi_extra, receiving=_WORK_GOODS
        )
        state.work_net = arithmetic.add_giving(
            money.oi_net,
            money.oi_extra,
            money.oi_carriage,
            money.oi_discount,
            body.oi_deduct_amt,
            receiving=_WORK_NET,
        )

        # [:L526] add work-vat to total-vat (a).
        # [:L527] add work-net to total-net (a).
        # FINDING 8(a) again: both subscripted by `a`, unchecked, and IN THIS
        # ORDER - `total-vat` first. The order is load-bearing when `a` is out of
        # range, because the two windows then overlap fields the other statement
        # reads: at `a = 0` the first statement's receiver IS `work-goods` and the
        # second's IS `work-vat`, so the second reads a `work-vat` the first had
        # not yet touched and the compiled oracle's readings depend on exactly
        # that sequence. Each statement therefore performs its own read and its
        # own store through `_add_to_total_group`; nothing is hoisted, batched or
        # resolved once for both.
        _add_to_total_group(state, "total-vat", state.work_vat)
        _add_to_total_group(state, "total-net", state.work_net)

        state.work_1 = move.move_numeric(state.work_net, _WORK_1)
        state.work_1 = arithmetic.add_to(
            state.work_vat, receiver_value=state.work_1, receiving=_WORK_1
        )

        state.ws_deduction = move.move_figurative(move.ZERO, _WS_DEDUCTION)

        if _IS_G_L(system.system_data_block.level.level_1):
            _ca000_bl_write(state)


        if body.oi_type == 1 or body.oi_type == 2:
            _ba000_sales_comp(state)

        # [:L544-L562] THREE INDEPENDENT `if`s on oi-type, mutually exclusive by value
        # but written separately and differing in more than the test.

        if body.oi_type == 1:
            _add_to_turnover_quarter(state, state.work_goods)
            (sales.sales_last_inv, sales.sales_last_pay) = move.move_to_all(
                body.oi_date,
                (_SALES["sales-last-inv"], _SALES["sales-last-pay"]),
                sending_field=otm3.descriptor_for(type(body), "oi_date"),
            )

        if body.oi_type == 2:
            _add_to_turnover_quarter(state, state.work_goods)
            sales.sales_current = arithmetic.add_to(
                state.work_vat,
                state.work_net,
                receiver_value=sales.sales_current,
                receiving=_SALES["sales-current"],
            )
            sales.sales_last_inv = move.move_numeric(
                body.oi_date, _SALES["sales-last-inv"]
            )

        if body.oi_type == 3:
            _add_to_turnover_quarter(state, state.work_goods)
            sales.sales_current = arithmetic.add_to(
                state.work_vat,
                state.work_net,
                receiver_value=sales.sales_current,
                receiving=_SALES["sales-current"],
            )
            sales.sales_last_pay = move.move_numeric(
                body.oi_date, _SALES["sales-last-pay"]
            )
            _ba000_cr_notes(state)
            _ba000_credit_comp(state)

        state.total_deduct = arithmetic.add_to(
            state.ws_deduction, receiver_value=state.total_deduct, receiving=_TOTAL_DEDUCT
        )

        # [:L567-L568] if customer-dead move 1 to sales-status.
        if _IS_CUSTOMER_DEAD(sales.sales_status):
            sales.sales_status = move.move_numeric(1, _SALES["sales-status"])

        if arithmetic.compare(sales.sales_current, 0) < 0:
            sales.sales_current = arithmetic.multiply_by(
                -1, sales.sales_current, _SALES["sales-current"]
            )
            sales.sales_unapplied = arithmetic.add_to(
                sales.sales_current,
                receiver_value=sales.sales_unapplied,
                receiving=_SALES["sales-unapplied"],
            )
            sales.sales_current = move.move_figurative(
                move.ZERO, _SALES["sales-current"]
            )


        if state.ws_reply == "X":
            sales.sales_status = move.move_numeric(1, _SALES["sales-status"])
            facade.sales_write(state.ctx(state.ws_sales_record))
        else:
            facade.sales_rewrite(state.ctx(state.ws_sales_record))

        # [:L585] move OI-Header to WS-OTM3-Record. COMMENTED OUT in the frozen source,
        # with the maintainer's reason "*> is redefines" - they are the same storage.
        facade.otm3_write(state.ctx(state.ws_otm3_record))

        # [:L590-L601] The write-failure diagnostic. It TRANSFERS NO CONTROL.
        if state.file_access.fs_reply != FsReply.SUCCESS:
            _zz040_evaluate_message(state)
            # [:L591-L599] Four of the six displays become ONE record, and the
            # other two are DROPPED - deliberately, and they are the two that
            # carry data:
            #
            #  * [:L592] `display oi3-customer` and [:L594] `display l5-nos`
            #  (the invoice number moved in at [:L593]) are the CUSTOMER CODE
            #  and the INVOICE NUMBER - business keys for the very row that
            #  failed. The safe-event schema in `acas_posting/dal/status.py`
            #  excludes record keys and identifiers from every record at every
            #  level (CWE-532), and DEBUG is not an exemption.
            #  * Dropping them also removes a FAILURE PATH that logging must not
            #  add: `_oi_customer_image` and the `move` behind `l5-nos` are
            #  `cobol.move` calls, evaluated as arguments BEFORE the logging
            #  module decides whether the record is wanted, so a value the
            #  receiving picture cannot hold would raise from inside a
            #  diagnostic. Removing the operands removes the risk outright,
            #  which no `isEnabledFor` guard can do.
            #
            # What remains is the message literal, the file status and the status
            # NAME. `ws-Eval-Msg` is `pic x(25)` filled ONLY by
            # `zz040-Evaluate-Message` from the static table
            # `copybooks/FileStat-Msgs.cpy` keyed on `fs-reply`, so it is a fixed
            # status name - never driver text, never a business value.
            _LOG.error(
                "%s fs-reply = %02d %s",
                _SL130,
                state.file_access.fs_reply,
                state.ws_eval_msg,
            )
            if state.ws_calling_data.ws_caller.strip() != "xl150":
                # [:L599] display SL002. DROPPED WITH THE `accept` IT
                # INTRODUCES: "Note error and hit return" is the instruction to
                # press the key, and a headless run has no operator to instruct.
                # The substantive diagnostic is the record above.
                pass

        # [:L606] write print-record from line-5 after 1. OMITTED with the print file;
        # the counter it feeds is not, because [:L608] branches on it.
        state.line_cnt = arithmetic.add_to(
            1, receiver_value=state.line_cnt, receiving=_LINE_CNT
        )
        if (
            arithmetic.compare(state.line_cnt, system.system_data_block.page_lines)
            > 0
        ):
            _ba000_headings(state)

        continue

    # The post-loop block for the class-2 transfer at [:L485].
    _aa030_main_end(state)


def _aa030_main_end(state: _Sl060State) -> None:
    """``aa030-Main-End.`` [sales/sl060.cbl:L612] - close phase 1, open phase 2."""
    system = state.system_record

    # [:L613] close open-item-file-2.
    state.open_item_file_2.close(state.file_access)
    # [:L614] perform OTM3-Close.
    facade.otm3_close(state.ctx(state.ws_otm3_record))
    facade.sales_close(state.ctx(state.ws_sales_record))

    # [:L616-L636] Three report blocks, one per occurrence of the total table.
    if (
        arithmetic.compare(
            state.line_cnt,
            arithmetic.intermediate(system.system_data_block.page_lines - 7),
        )
        > 0
    ):
        _ba000_headings(state)

    # [:L638-L640] The "Total Amount Late Deductions" line.

    state.system_record_4.sales_ledger_data.sl_credit_deductions = arithmetic.add_to(
        state.total_deduct,
        receiver_value=state.system_record_4.sales_ledger_data.sl_credit_deductions,
        receiving=_SYSTOT["sl-credit-deductions"],
    )

    if arithmetic.compare(state.total_deduct, 0) != 0:
        facade.value_open(state.ctx(state.ws_value_record))
        _ba000_analise_deductions(state)
        facade.value_close(state.ctx(state.ws_value_record))

    if _IS_G_L(system.system_data_block.level.level_1):
        _ca000_bl_close(state)

    # [:L656] perform OTM3-Open. Re-opened for the second phase, which walks it
    # sequentially rather than by key.
    facade.otm3_open(state.ctx(state.ws_otm3_record))
    state.work_b = move.move_figurative(move.ZERO, _WORK_B)
    _LOG.info("2 - Applying Cr. Notes to OTM3")

    _aa040_end_loop(state)


def _aa040_end_loop(state: _Sl060State) -> None:
    """``aa040-End-Loop.`` [sales/sl060.cbl:L661] - phase 2, the credit swap walk."""
    while True:
        facade.otm3_read_next(state.ctx(state.ws_otm3_record))
        if state.file_access.fs_reply == FsReply.END_OF_FILE:
            break


        body = state.oi_header.filler_1

        if _IS_S_CLOSED(body.oi_status):
            continue

        if body.oi_type == 3:
            _ba000_cr_swop(state)

        # GO TO class 1 [sales/sl060.cbl:L674] -> aa040-End-Loop. Unconditional, so the
        # read at the head of the loop is the only place control leaves.
        continue

    _aa050_end_loop_end(state)


def _aa050_end_loop_end(state: _Sl060State) -> None:
    """``aa050-End-Loop-End.`` [sales/sl060.cbl:L676] - close down, and site 4 of 9."""
    system = state.system_record

    # [:L677] open output open-item-file-2.  *> Clear down IO2 file data now
    #  *> transferred to IO3
    # [:L678] close open-item-file-2.
    # OPEN OUTPUT ON A SEQUENTIAL FILE DISCARDS WHAT WAS THERE, so this pair
    # TRUNCATES the OTM2 extract - the transfer to OTM3 is complete and sl055's
    # output is deliberately destroyed. Reproduced: the work sequence's
    # open_output does the same, "because organization line sequential is why
    # open_output discards what was there before".
    state.open_item_file_2.open_output(state.file_access)
    state.open_item_file_2.close(state.file_access)
    # [:L679] perform OTM3-Close.
    facade.otm3_close(state.ctx(state.ws_otm3_record))

    # [:L681-L689] R-1 GATE 3 of 4.
    if _IS_FS_COBOL_FILES_USED(system.system_data_block.rdbms_flat_statuses.file_system_used):
        # [:L682-L683] call "CBL_CHECK_FILE_EXIST" using File-18 File-Info, then [:L685]
        # set File-18-Not-Exists / [:L687] set File-18-Exists.
        raise _CobolLibraryRoutineUnavailable(
            "CBL_CHECK_FILE_EXIST", f"{_PROGRAM}:L682", "File-18 File-Info"
        )

    # [:L691-L693] if line-cnt > Page-Lines - 6 and FS-Cobol-Files-Used and
    # File-18-Exists perform ba000-New-Heading. A THREE-CONDITION AND that also carries
    # relation-condition arithmetic.
    if (
        arithmetic.compare(
            state.line_cnt,
            arithmetic.intermediate(system.system_data_block.page_lines - 6),
        )
        > 0
        and _IS_FS_COBOL_FILES_USED(
            system.system_data_block.rdbms_flat_statuses.file_system_used
        )
        and condition_names.evaluate(_FILE_18_EXISTS, state.file_18_status)
    ):
        _ba000_new_heading(state)

    if _IS_FS_COBOL_FILES_USED(
        system.system_data_block.rdbms_flat_statuses.file_system_used
    ) and condition_names.evaluate(_FILE_18_EXISTS, state.file_18_status):
        # NO RECORD. [:L695-L698] is `move ... to print-record` / `write
        # print-record`: a REPORT LINE, not a display. Section 0.2.2 puts
        # "report formatting beyond database effects" out of scope, so the line
        # is not reproduced anywhere - and its operand `work-b` is an accumulated
        # MONETARY VALUE, which the safe-event schema excludes from logs in any
        # case (CWE-532). The `if` survives because the split between this
        # conditional print and the UNCONDITIONAL period-total add below it is
        # load-bearing, as the note on that add explains.
        pass

    # [:L700] add work-b to sl-cn-unappl-this-month. [copybooks/wssys4.cob:L16]. IT IS
    # OUTSIDE THE `if` AT [:L695]. The print line above is conditional; this add is
    # UNCONDITIONAL.
    state.system_record_4.sales_ledger_data.sl_cn_unappl_this_month = arithmetic.add_to(
        state.work_b,
        receiver_value=state.system_record_4.sales_ledger_data.sl_cn_unappl_this_month,
        receiving=_SYSTOT["sl-cn-unappl-this-month"],
    )

    # FINDING 9 [sales/sl060.cbl:L702-L707] - A MISSING `write`. The source is.
    if condition_names.evaluate(_SALES_MISSING, state.ws_error):
        if _IS_FS_COBOL_FILES_USED(
            system.system_data_block.rdbms_flat_statuses.file_system_used
        ):
            pass
        else:
            # [:L706-L707] move SL133T to print-record / write print-record.
            #
            # NO RECORD, on either arm. Neither `SL133` nor `SL133T` is ever
            # DISPLAYED: both are moved into `print-record` and belong to the
            # spool file, which section 0.2.2 puts out of scope. Section 0.3.4
            # converts a DISPLAY into a log record; it does not convert a report
            # line, and turning one into an operator diagnostic would invent
            # output the compiled program never produced.
            #
            # THE `if`/`else` SHAPE IS STILL LOAD-BEARING and is why both arms
            # survive as written: the asymmetry above - a `write` on this arm and
            # none on the other - is anomaly A-1's sibling, and the structure is
            # the evidence for it.
            pass

    # [:L709] close print-file. OMITTED with the print file. [:L710] call "SYSTEM" using
    # Print-Report. OMITTED.

    # [:L711-L713] R-1 GATE 4 of 4.
    if _IS_FS_COBOL_FILES_USED(
        system.system_data_block.rdbms_flat_statuses.file_system_used
    ) and condition_names.evaluate(_FILE_18_EXISTS, state.file_18_status):
        # [:L713] call "CBL_DELETE_FILE" using File-18.
        raise _CobolLibraryRoutineUnavailable(
            "CBL_DELETE_FILE", f"{_PROGRAM}:L713", "File-18"
        )

    # [:L715-L720] A COMMENTED-OUT restore of Level-1, the other half of the bypass at
    # [:L458-L464]. Not compiled, not reproduced.

    _aa999_exit_prog(state)


def _aa999_exit_prog(state: _Sl060State) -> None:
    """``aa999-Exit-Prog.`` [sales/sl060.cbl:L722] - return to the caller.

    FINDING 7 [sales/sl060.cbl:L723] - THE STATEMENT IS ``exit program.``, NOT
    ``goback.``. Every other module in this folder ends with ``goback``, and the two
    differ.
    """
    # FINDING 7 [sales/sl060.cbl:L723] - the terminator is `exit program.`, not the
    # `goback.` every sibling uses. Recorded, not normalised.
    del state


def _ba000_cr_swop(state: _Sl060State) -> None:
    """``ba000-Cr-Swop section.`` [sales/sl060.cbl:L725] - carry an unapplied note."""
    system = state.system_record
    oi = state.oi_header
    body = oi.filler_1
    money = body.filler_2

    state.work_1 = arithmetic.add_giving(
        money.oi_net,
        money.oi_extra,
        money.oi_carriage,
        money.oi_vat,
        money.oi_discount,
        money.oi_e_vat,
        money.oi_c_vat,
        body.oi_deduct_amt,
        body.oi_deduct_vat,
        receiving=_WORK_1,
    )
    state.work_1 = arithmetic.add_to(
        money.oi_paid, receiver_value=state.work_1, receiving=_WORK_1
    )

    if arithmetic.compare(state.work_1, 0) == 0:
        # [:L733] display SL131. A MIXED LITERAL: the diagnostic half is kept and
        # the trailing ": Return to continue" - the instruction to press the key
        # that the `accept` below reads - is dropped with the pause itself.
        _LOG.warning("%s", _SL131_NOTICE)
        if state.ws_calling_data.ws_caller.strip() != "xl150":
            # [:L734-L735] display SL003 / accept ws-reply.
            #
            # BOTH DROPPED. "SL003 Hit Return To Continue" [:L262] is a PURE
            # prompt - the whole literal is the key-press instruction, with no
            # diagnostic half to keep - and the `accept` is the key press.
            # Section 0.3.4 drops a prompt whose only effect is to block a
            # terminal. The unattended-mode BRANCH survives: it is the codebase's
            # own headless-operation test.
            pass

    if _IS_FS_COBOL_FILES_USED(
        system.system_data_block.rdbms_flat_statuses.file_system_used
    ) and condition_names.evaluate(_FILE_18_NOT_EXISTS, state.file_18_status):
        _ba000_new_heading(state)

    body.oi_status = move.move_numeric(1, otm3.descriptor_for(type(body), "oi_status"))

    state.line_cnt = arithmetic.add_to(
        1, receiver_value=state.line_cnt, receiving=_LINE_CNT
    )
    if arithmetic.compare(state.line_cnt, system.system_data_block.page_lines) > 0:
        _ba000_new_heading(state)

    state.work_b = arithmetic.add_to(
        state.work_1, receiver_value=state.work_b, receiving=_WORK_B
    )
    state.work_1 = arithmetic.multiply_by(-1, state.work_1, _WORK_1)
    money.oi_paid = arithmetic.add_to(
        state.work_1,
        receiver_value=money.oi_paid,
        receiving=otm3.descriptor_for(type(money), "oi_paid"),
    )

    facade.otm3_rewrite(state.ctx(state.ws_otm3_record))

    _ba000_cr_swop__main_exit(state)


def _ba000_cr_swop__main_exit(state: _Sl060State) -> None:
    """``main-exit.`` [sales/sl060.cbl:L763] - of ``ba000-Cr-Swop``.

    The name is section-qualified because ``main-exit.`` is declared SIX times in this
    program - [:L763], [:L789], [:L813], [:L829], [:L845] and [:L973] - and paragraph
    names are not globally unique in this codebase.
    """
    del state


# ba000-New-Heading section. [sales/sl060.cbl:L766] ba000-Headings section.


def _ba000_new_heading(state: _Sl060State) -> None:
    """``ba000-New-Heading section.`` [sales/sl060.cbl:L766] - the phase-2 heading.

    Differs from :func:`_ba000_headings` in three ways, all preserved: it emits an extra
    ``line-1a`` [:L776, :L782], it uses ``line-4a`` rather than ``line-4`` [:L784], and
    it leaves ``line-cnt`` at SIX rather than five.
    """
    state.j = arithmetic.add_to(1, receiver_value=state.j, receiving=_J)
    state.line_cnt = move.move_numeric(6, _LINE_CNT)

    _ba000_new_heading__main_exit(state)


def _ba000_new_heading__main_exit(state: _Sl060State) -> None:
    """``main-exit.`` [sales/sl060.cbl:L789] - of ``ba000-New-Heading``."""
    del state


def _ba000_headings(state: _Sl060State) -> None:
    """``ba000-Headings section.`` [sales/sl060.cbl:L792] - the phase-1 heading."""
    state.j = arithmetic.add_to(1, receiver_value=state.j, receiving=_J)
    state.line_cnt = move.move_numeric(5, _LINE_CNT)

    _ba000_headings__main_exit(state)


def _ba000_headings__main_exit(state: _Sl060State) -> None:
    """``main-exit.`` [sales/sl060.cbl:L813] - of ``ba000-Headings``."""
    del state


def _ba000_sales_comp(state: _Sl060State) -> None:
    """``ba000-Sales-Comp section.`` [sales/sl060.cbl:L816] - the invoice average.

    ANOMALY A-8 [sales/sl060.cbl:L826-L827] - DOUBLE TRUNCATION, and it is a FIELD-WIDTH
    defect rather than an arithmetic one.
    """
    sales = state.ws_sales_record

    if sales.sales_activety != 0 and sales.sales_average != 0:
        state.work_2 = arithmetic.multiply_by_giving(
            sales.sales_activety, sales.sales_average, _WORK_2
        )
    else:
        state.work_2 = move.move_figurative(move.ZERO, _WORK_2)

    # [:L825] add 1 to sales-activety. UNCONDITIONAL, and BEFORE the divide - which is
    # one of the two things ba000-Credit-Comp does differently. See ANOMALY A-9.
    sales.sales_activety = arithmetic.add_to(
        1, receiver_value=sales.sales_activety, receiving=_SALES["sales-activety"]
    )
    # [:L826] add work-goods to work-2. ANOMALY A-8 [sales/sl060.cbl:L826] - TRUNCATION
    # ONE: two decimal places into a zero-scale receiver [:L206] discards the pence.
    # Reproduced deliberately per R-4.
    state.work_2 = arithmetic.add_to(
        state.work_goods, receiver_value=state.work_2, receiving=_WORK_2
    )
    # [:L827] divide sales-activety into work-2 giving sales-average. ANOMALY A-8
    # [sales/sl060.cbl:L827] - TRUNCATION TWO: an integer receiver
    # [copybooks/wssl.cob:L49] discards the remainder, toward zero. Reproduced
    # deliberately per R-4.
    sales.sales_average = arithmetic.divide_into_giving(
        sales.sales_activety, state.work_2, _SALES["sales-average"]
    )

    _ba000_sales_comp__main_exit(state)


def _ba000_sales_comp__main_exit(state: _Sl060State) -> None:
    """``main-exit.`` [sales/sl060.cbl:L829] - of ``ba000-Sales-Comp``."""
    del state


def _ba000_credit_comp(state: _Sl060State) -> None:
    """``ba000-Credit-Comp section.`` [sales/sl060.cbl:L832] - the credit-note average.

    The credit-note counterpart of :func:`_ba000_sales_comp`, performed for ``oi-type``
    3 [:L562]. IT IS NOT THE SAME, AND MUST NOT BE MADE THE SAME.
    """
    sales = state.ws_sales_record

    # [:L835-L840] The inner guard - textually identical to [:L819-L824].
    if sales.sales_activety != 0 and sales.sales_average != 0:
        state.work_2 = arithmetic.multiply_by_giving(
            sales.sales_activety, sales.sales_average, _WORK_2
        )
    else:
        state.work_2 = move.move_figurative(move.ZERO, _WORK_2)

    # NOTE THE ABSENCE. ba000-Sales-Comp has `add 1 to sales-activety` at [:L825]
    # between the guard and the accumulate. This section has NOTHING here.

    # [:L841] if work-2 not = zero ANOMALY A-9 [sales/sl060.cbl:L841] - the extra outer
    # guard that swallows a customer's first credit note. Reproduced deliberately per
    # R-4.
    if state.work_2 != 0:
        # [:L842] add work-goods to work-2. ANOMALY A-8 [sales/sl060.cbl:L842] -
        # truncation one again.
        state.work_2 = arithmetic.add_to(
            state.work_goods, receiver_value=state.work_2, receiving=_WORK_2
        )
        # [:L843] divide sales-activety into work-2 giving sales-average. ANOMALY A-8
        # [sales/sl060.cbl:L843] - truncation two again. Note that the divisor is the
        # UNINCREMENTED counter.
        sales.sales_average = arithmetic.divide_into_giving(
            sales.sales_activety, state.work_2, _SALES["sales-average"]
        )

    _ba000_credit_comp__main_exit(state)


def _ba000_credit_comp__main_exit(state: _Sl060State) -> None:
    """``main-exit.`` [sales/sl060.cbl:L845] - of ``ba000-Credit-Comp``."""
    del state


# ba000-CR-Notes section. [sales/sl060.cbl:L848] The two-pass OTM3 walk that applies a
# credit note to a customer's invoices.

#: The three labels of ba000-CR-Notes' internal graph, named so that the dispatcher
#: below reads as the transfers it realises.
_LABEL_BA010_READ_LOOP: Final[str] = "ba010-read-loop"
_LABEL_BA020_END_LOOP: Final[str] = "ba020-end-loop"
_LABEL_BA030_MAIN_END: Final[str] = "ba030-main-end"


def _ba000_cr_notes(state: _Sl060State) -> None:
    """``ba000-CR-Notes section.`` [sales/sl060.cbl:L848] - apply a credit note.

    GO TO CLASS 4, PROOF FOR [sales/sl060.cbl:L908]. ``ba020-end-loop`` is BOTH a loop
    terminator and a re-dispatcher.
    """
    oi = state.oi_header
    key = oi.oi_key
    body = oi.filler_1

    _group_move_oi_header(oi, state.si_header)
    state.first_pass = move.move_alphanumeric("Y", _FIRST_PASS)
    # [:L853] move oi-customer to oi3-customer. A NO-OP BY CONSTRUCTION.
    _write_oi3_customer(state, _oi_customer_image(oi))
    # [:L854] move oi-cr to oi3-invoice. NOT a no-op: oi3-invoice IS oi-invoice, so this
    # OVERWRITES the header's own invoice number with the credit-note number.
    key.oi_invoice = move.move_numeric(
        body.oi_cr, otm3.descriptor_for(type(key), "oi_invoice")
    )
    # [:L855] set fn-not-less-than to true. The ISAM START relation, through the access-
    # type vocabulary [copybooks/wsfnctn.cob:L115] - never a raw integer.
    state.file_access.access_type = AccessType.NOT_LESS_THAN
    facade.otm3_start(state.ctx(state.ws_otm3_record))

    label = _LABEL_BA020_END_LOOP
    if state.file_access.fs_reply == FsReply.SUCCESS:
        state.work_b = move.move_figurative(move.ZERO, _WORK_B)
        if arithmetic.compare(state.work_1, 0) < 0:
            state.work_1 = arithmetic.multiply_by(-1, state.work_1, _WORK_1)
        state.work_1 = arithmetic.subtract_from(
            state.si_header.filler_1.filler_2.oi_paid,
            receiver_value=state.work_1,
            receiving=_WORK_1,
        )
        label = _LABEL_BA010_READ_LOOP

    while label != _LABEL_BA030_MAIN_END:
        if label == _LABEL_BA010_READ_LOOP:
            label = _ba010_read_loop(state)
        else:
            label = _ba020_end_loop(state)

    _ba030_main_end(state)
    _ba040_main_exit(state)


def _ba010_read_loop(state: _Sl060State) -> str:
    """``ba010-read-loop.`` [sales/sl060.cbl:L864] - walk the customer's invoices.

    Returns:
        The label this paragraph transfers to. Every exit goes to ``ba020-end-loop``.
    """
    si = state.si_header
    si_body = si.filler_1
    si_image = _oi_customer_image(si)

    while True:
        facade.otm3_read_next(state.ctx(state.ws_otm3_record))
        if state.file_access.fs_reply == FsReply.END_OF_FILE:
            return _LABEL_BA020_END_LOOP


        oi = state.oi_header
        key = oi.oi_key
        body = oi.filler_1
        money = body.filler_2

        if body.oi_type != 2:
            continue
        # [:L875-L876] if oi-customer not = si-customer go to ba020-end-loop.
        if _oi_customer_image(oi) != si_image:
            return _LABEL_BA020_END_LOOP
        if _IS_S_CLOSED(body.oi_status):
            continue

        state.work_b = arithmetic.add_giving(
            body.oi_deduct_amt, body.oi_deduct_vat, receiving=_WORK_B
        )
        state.maps03_ws.u_bin = move.move_numeric(body.oi_date, _MAPS03["u-bin"])
        state.maps03_ws.u_bin = arithmetic.add_to(
            1,
            body.oi_deduct_days,
            receiver_value=state.maps03_ws.u_bin,
            receiving=_MAPS03["u-bin"],
        )
        if arithmetic.compare(state.maps03_ws.u_bin, si_body.oi_date) <= 0:
            state.work_b = move.move_figurative(move.ZERO, _WORK_B)

        if si_body.oi_cr == key.oi_invoice or state.first_pass == "N":
            _ba000_apportion(state)

        if arithmetic.compare(state.work_1, 0) != 0:
            continue

        # FALL-THROUGH past [:L893] into ba020-end-loop [:L895]: the credit note is
        # fully applied, so the walk stops.
        return _LABEL_BA020_END_LOOP


def _ba020_end_loop(state: _Sl060State) -> str:
    """``ba020-end-loop.`` [sales/sl060.cbl:L895] - end the pass, or start the second.

    Returns:
        ``ba010-read-loop`` for the class-4 backward transfer at [:L908], or
            ``ba030-main-end`` for the class-2 transfers at [:L900] and [:L907].
    """
    si = state.si_header

    if arithmetic.compare(state.work_1, 0) == 0 or state.first_pass != "Y":
        return _LABEL_BA030_MAIN_END

    state.first_pass = move.move_alphanumeric("N", _FIRST_PASS)
    # [:L902] move si-customer to oi3-customer. From the SAVED header, because the walk
    # has left the current header on some other customer's row.
    _write_oi3_customer(state, _oi_customer_image(si))
    # [:L903] move zero to oi3-invoice. Position at the customer's FIRST invoice rather
    # than at the credit note's own.
    state.oi_header.oi_key.oi_invoice = move.move_figurative(
        move.ZERO, otm3.descriptor_for(type(state.oi_header.oi_key), "oi_invoice")
    )
    state.file_access.access_type = AccessType.NOT_LESS_THAN
    facade.otm3_start(state.ctx(state.ws_otm3_record))
    if state.file_access.fs_reply != FsReply.SUCCESS:
        return _LABEL_BA030_MAIN_END

    return _LABEL_BA010_READ_LOOP


def _ba030_main_end(state: _Sl060State) -> None:
    """``ba030-main-end.`` [sales/sl060.cbl:L910] - restore the header."""
    _group_move_oi_header(state.si_header, state.oi_header)


def _ba040_main_exit(state: _Sl060State) -> None:
    """``ba040-main-exit.`` [sales/sl060.cbl:L915] - of ``ba000-CR-Notes``."""
    del state


def _ba000_apportion(state: _Sl060State) -> None:
    """``ba000-Apportion section.`` [sales/sl060.cbl:L918] - apply value to one invoice.

    All three are reproduced exactly as written. R-3 forbids imposing the symmetry that
    would make them one arm with flags.
    """
    oi = state.oi_header
    body = oi.filler_1
    money = body.filler_2
    si_body = state.si_header.filler_1
    si_money = si_body.filler_2

    state.work_a = arithmetic.add_giving(
        money.oi_net,
        money.oi_extra,
        money.oi_carriage,
        money.oi_vat,
        money.oi_discount,
        money.oi_e_vat,
        money.oi_c_vat,
        body.oi_deduct_amt,
        body.oi_deduct_vat,
        receiving=_WORK_A,
    )
    state.work_a = arithmetic.subtract_from(
        money.oi_paid, receiver_value=state.work_a, receiving=_WORK_A
    )

    if arithmetic.compare(state.work_a, 0) == 0:
        body.oi_status = move.move_numeric(
            1, otm3.descriptor_for(type(body), "oi_status")
        )
        # GO TO class 4 [sales/sl060.cbl:L928] -> ba000-Main-Rewrite. PROOF.
        _ba000_main_rewrite(state)
        return

    if arithmetic.compare(state.work_a, 0) <= 0:
        return

    state.work_a = arithmetic.subtract_from(
        state.work_b, receiver_value=state.work_a, receiving=_WORK_A
    )

    oi_paid = otm3.descriptor_for(type(money), "oi_paid")
    oi_p_c = otm3.descriptor_for(type(money), "oi_p_c")
    oi_status = otm3.descriptor_for(type(body), "oi_status")
    si_paid = otm3.descriptor_for(type(si_money), "oi_paid")
    si_status = otm3.descriptor_for(type(si_body), "oi_status")

    if arithmetic.compare(state.work_a, state.work_1) == 0:
        money.oi_paid = arithmetic.add_to(
            state.work_1, receiver_value=money.oi_paid, receiving=oi_paid
        )
        si_money.oi_paid = arithmetic.add_to(
            state.work_1, receiver_value=si_money.oi_paid, receiving=si_paid
        )
        money.oi_p_c = arithmetic.add_to(
            state.work_1, receiver_value=money.oi_p_c, receiving=oi_p_c
        )
        state.work_1 = move.move_figurative(move.ZERO, _WORK_1)
        _ba000_clear_invoice_deduct(state)
        (body.oi_status, si_body.oi_status) = move.move_to_all(
            1, (oi_status, si_status)
        )
    elif arithmetic.compare(state.work_a, state.work_1) > 0:
        money.oi_paid = arithmetic.add_to(
            state.work_1, receiver_value=money.oi_paid, receiving=oi_paid
        )
        si_money.oi_paid = arithmetic.add_to(
            state.work_1, receiver_value=si_money.oi_paid, receiving=si_paid
        )
        money.oi_p_c = arithmetic.add_to(
            state.work_1, receiver_value=money.oi_p_c, receiving=oi_p_c
        )
        state.work_1 = move.move_figurative(move.ZERO, _WORK_1)
        # [:L948] move 1 to si-status. FINDING 10: ONLY si-status here, and NO perform
        # of ba000-Clear-Invoice-Deduct - the only one of the three arms that omits it.
        si_body.oi_status = move.move_numeric(1, si_status)
    else:
        # [:L950-L952] The same three adds, but of work-a rather than work-1.
        money.oi_paid = arithmetic.add_to(
            state.work_a, receiver_value=money.oi_paid, receiving=oi_paid
        )
        si_money.oi_paid = arithmetic.add_to(
            state.work_a, receiver_value=si_money.oi_paid, receiving=si_paid
        )
        money.oi_p_c = arithmetic.add_to(
            state.work_a, receiver_value=money.oi_p_c, receiving=oi_p_c
        )
        state.work_1 = arithmetic.subtract_from(
            state.work_a, receiver_value=state.work_1, receiving=_WORK_1
        )
        _ba000_clear_invoice_deduct(state)
        body.oi_status = move.move_numeric(1, oi_status)

    if arithmetic.compare(state.work_1, 0) == 0:
        si_body.oi_status = move.move_numeric(1, si_status)

    _ba000_main_rewrite(state)


def _ba000_main_rewrite(state: _Sl060State) -> None:
    """``ba000-Main-Rewrite.`` [sales/sl060.cbl:L960] - store the apportioned item.

    # EXIT SECTION [sales/sl060.cbl:L963] - which is why ba000-Clear-Invoice- # Deduct
    [:L965] is never reached by fall-through from here, only by the two # PERFORMs at
    [:L940] and [:L954].
    """
    facade.otm3_rewrite(state.ctx(state.ws_otm3_record))


def _ba000_clear_invoice_deduct(state: _Sl060State) -> None:
    """``ba000-Clear-Invoice-Deduct.`` [sales/sl060.cbl:L965] - take the deduction."""
    body = state.oi_header.filler_1
    sales = state.ws_sales_record

    if arithmetic.compare(state.work_b, 0) > 0:
        sales.sales_current = arithmetic.subtract_from(
            state.work_b,
            receiver_value=sales.sales_current,
            receiving=_SALES["sales-current"],
        )
        state.ws_deduction = arithmetic.add_to(
            state.work_b, receiver_value=state.ws_deduction, receiving=_WS_DEDUCTION
        )
        state.total_mov_ded = arithmetic.add_to(
            1, receiver_value=state.total_mov_ded, receiving=_TOTAL_MOV_DED
        )
        (body.oi_deduct_amt, body.oi_deduct_vat) = move.move_to_all(
            move.ZERO,
            (
                otm3.descriptor_for(type(body), "oi_deduct_amt"),
                otm3.descriptor_for(type(body), "oi_deduct_vat"),
            ),
        )


def _ba000_cid_exit(state: _Sl060State) -> None:
    """``ba000-cid-exit.`` [sales/sl060.cbl:L971] - AN EMPTY PARAGRAPH.

    The label carries NO STATEMENTS: [:L972] is a comment and [:L973] is the next label.
    """
    # FALL-THROUGH into main-exit [:L973] - the shape of the source, though the note
    # above explains why control never takes it.
    _ba000_apportion__main_exit(state)


def _ba000_apportion__main_exit(state: _Sl060State) -> None:
    """``main-exit.`` [sales/sl060.cbl:L973] - of ``ba000-Apportion``."""
    del state


def _ba000_analise_deductions(state: _Sl060State) -> None:
    """``ba000-Analise-Deductions section.`` [:L976] - reverse the discount totals.

    THE TWO BLOCKS ARE DELIBERATELY NOT FACTORED. They differ in the key they read
    [:L979] against [:L992], and ``sl055``'s own ``dc000-Store-Specials`` carries the
    same twice-over shape.
    """
    value = state.ws_value_record

    group_image = move.move_group("Szd", _VALUE["va-code"], length=3)
    value.va_code.va_system = move.move_alphanumeric(
        move.ref_mod(group_image, 1, 1), _VALUE["va-system"]
    )
    value.va_code.va_group.va_first = move.move_alphanumeric(
        move.ref_mod(group_image, 2, 1), _VALUE["va-first"]
    )
    value.va_code.va_group.va_second = move.move_alphanumeric(
        move.ref_mod(group_image, 3, 1), _VALUE["va-second"]
    )
    state.file_access.logging_data.file_key_no = move.move_numeric(
        1, _ACCESS["file-key-no"]
    )
    facade.value_read_indexed(state.ctx(state.ws_value_record))
    if state.file_access.fs_reply == FsReply.INVALID_KEY_ON_START:
        return

    value.va_t_this = arithmetic.subtract_from(
        state.total_mov_ded, receiver_value=value.va_t_this, receiving=_VALUE["va-t-this"]
    )
    value.va_t_year = arithmetic.subtract_from(
        state.total_mov_ded, receiver_value=value.va_t_year, receiving=_VALUE["va-t-year"]
    )
    value.va_v_this = arithmetic.subtract_from(
        state.total_deduct, receiver_value=value.va_v_this, receiving=_VALUE["va-v-this"]
    )
    value.va_v_year = arithmetic.subtract_from(
        state.total_deduct, receiver_value=value.va_v_year, receiving=_VALUE["va-v-year"]
    )

    facade.value_rewrite(state.ctx(state.ws_value_record))

    # [:L992] move space to va-second. The key becomes "Sz " - the group total rather
    # than the specific code.
    value.va_code.va_group.va_second = move.move_figurative(
        move.SPACE, _VALUE["va-second"]
    )
    state.file_access.logging_data.file_key_no = move.move_numeric(
        1, _ACCESS["file-key-no"]
    )
    facade.value_read_indexed(state.ctx(state.ws_value_record))
    if state.file_access.fs_reply == FsReply.INVALID_KEY_ON_START:
        return

    value.va_t_this = arithmetic.subtract_from(
        state.total_mov_ded, receiver_value=value.va_t_this, receiving=_VALUE["va-t-this"]
    )
    value.va_t_year = arithmetic.subtract_from(
        state.total_mov_ded, receiver_value=value.va_t_year, receiving=_VALUE["va-t-year"]
    )
    value.va_v_this = arithmetic.subtract_from(
        state.total_deduct, receiver_value=value.va_v_this, receiving=_VALUE["va-v-this"]
    )
    value.va_v_year = arithmetic.subtract_from(
        state.total_deduct, receiver_value=value.va_v_year, receiving=_VALUE["va-v-year"]
    )
    facade.value_rewrite(state.ctx(state.ws_value_record))

    _ba999_main_exit(state)


def _ba999_main_exit(state: _Sl060State) -> None:
    """``ba999-main-exit.`` [sales/sl060.cbl:L1004] - of ``ba000-Analise-Deductions``.
    """
    del state


# ca000-BL-Open section. [sales/sl060.cbl:L1007] THE GATING, STATED ONCE FOR ALL THREE
# ca000 SECTIONS.


_BATCH_NOS_SCALE: Final[int] = 10**5


def _restate_ws_batch_key9(batch: GlBatchRecord) -> None:
    """Keep ``WS-Batch-Key9`` in step with the two members it redefines.

    ONE STORAGE, TWO READINGS. ``03 WS-Batch-Key.`` holds ``05 WS-Ledger pic 9.`` and
    ``05 WS-Batch-Nos pic 9(5).``, and ``03 WS-Batch-Key9 redefines WS-Batch-Key pic
    9(6).`` [copybooks/wsbatch.cob:L14-L21] is those SAME six bytes read as a single
    number.

    Args:
        batch: ``01 WS-Batch-Record.`` [copybooks/wsbatch.cob:L13], mutated in place so
            both readings of its key agree.
    """
    batch.ws_batch_key9.ws_batch_key9 = (
        int(batch.ws_batch_key.ws_ledger) * _BATCH_NOS_SCALE
        + int(batch.ws_batch_key.ws_batch_nos)
    )


def _ca000_bl_open(state: _Sl060State) -> None:
    """``ca000-BL-Open section.`` [sales/sl060.cbl:L1007] - start a GL batch.

    perform ca000-BL-Close / perform ca000-BL-Open.`` [:L1150-L1152] closes the full
    batch and opens the next one, so a run that posts a hundredth item comes back
    through here with a batch key already in working storage.
    """
    system = state.system_record
    gl_block = system.general_ledger_block
    batch = state.ws_batch_record

    facade.gl_batch_open(state.ctx(state.ws_batch_record))
    # [:L1011-L1014] The open-then-fallback pair that the other two opens in this
    # section still have is COMMENTED OUT for the batch file.

    batch.ws_batch_key.ws_batch_nos = move.move_numeric(
        gl_block.next_batch,
        _BATCH["ws-batch-nos"],
        sending_field=_SYSTEM["next-batch"],
    )
    batch.ws_batch_key.ws_ledger = move.move_numeric(3, _BATCH["ws-ledger"])
    # THE REDEFINED READING IS RESTATED HERE, because the two preceding moves have
    # just changed the bytes it shares. See `_restate_ws_batch_key9`.
    _restate_ws_batch_key9(batch)
    # [:L1018] add 1 to next-Batch. The system record is mutated here but only persisted
    # by whatever later writes SYSTEM-REC.
    gl_block.next_batch = arithmetic.add_to(
        1, receiver_value=gl_block.next_batch, receiving=_SYSTEM["next-batch"]
    )
    (batch.batch_status, batch.cleared_status) = move.move_to_all(
        move.ZERO, (_BATCH["batch-status"], _BATCH["cleared-status"])
    )
    batch.bcycle = move.move_numeric(
        system.system_data_block.scycle,
        _BATCH["bcycle"],
        sending_field=_SYSTEM["scycle"],
    )
    # [:L1022] move run-date to entered. THE CONTROLLED-CLOCK OBSERVABLE. Run-Date
    # [copybooks/wssystem.cob:L67] is the binary run date, pinned by the caller and
    # arriving through linkage.
    batch.dates.entered = move.move_numeric(
        system.system_data_block.run_date,
        _BATCH["entered"],
        sending_field=_SYSTEM["run-date"],
    )

    batch.description = move.move_alphanumeric(
        "Sales Ledger Invoices", _BATCH["description"]
    )
    (
        batch.posting_data.b_default,
        batch.posting_data.batch_def_ac,
        batch.posting_data.batch_def_pc,
        batch.items,
        batch.amounts.input_gross,
        batch.amounts.input_vat,
        batch.amounts.actual_gross,
        batch.amounts.actual_vat,
    ) = move.move_to_all(
        move.ZERO,
        (
            _BATCH["bdefault"],
            _BATCH["batch-def-ac"],
            _BATCH["batch-def-pc"],
            _BATCH["items"],
            _BATCH["input-gross"],
            _BATCH["input-vat"],
            _BATCH["actual-gross"],
            _BATCH["actual-vat"],
        ),
    )

    batch.posting_data.convention = move.move_alphanumeric(
        "CR", _BATCH["convention"]
    )
    batch.posting_data.batch_def_code = move.move_alphanumeric(
        "SL", _BATCH["batch-def-code"]
    )
    batch.posting_data.batch_def_vat = move.move_alphanumeric(
        "O", _BATCH["batch-def-vat"]
    )
    # [:L1037] add postings 1 giving Batch-start. ANOMALY A-17 [sales/sl060.cbl:L1037] -
    # THE READ-BACK END of the unexplained move at [:L1173]. `Postings` is the SYSTEM-
    # REC posting-RRN high-water mark.
    batch.batch_start = arithmetic.add_giving(
        gl_block.postings, 1, receiving=_BATCH["batch-start"]
    )

    if _IS_IRS_USED(gl_block.irs_instead) or _IS_IRS_BOTH_USED(gl_block.irs_instead):
        facade.spl_posting_open_extend(state.ctx(state.ws_irs_posting_record))
        # [:L1041-L1044] if fs-reply not = zero -> close and re-create. The maintainer's
        # comment says "wont happen in FH".
        if state.file_access.fs_reply != FsReply.SUCCESS:
            facade.spl_posting_close(state.ctx(state.ws_irs_posting_record))
            facade.spl_posting_open_output(state.ctx(state.ws_irs_posting_record))
    if _IS_IRS_BOTH_USED(gl_block.irs_instead) or _IS_G_L(
        system.system_data_block.level.level_1
    ):
        facade.gl_posting_open(state.ctx(state.ws_posting_record))
        if state.file_access.fs_reply != FsReply.SUCCESS:
            facade.gl_posting_close(state.ctx(state.ws_posting_record))
            facade.gl_posting_open_output(state.ctx(state.ws_posting_record))
    state.file_access.rrn = move.move_numeric(
        batch.batch_start, _ACCESS["rrn"], sending_field=_BATCH["batch-start"]
    )

    _ca997_main_exit(state)


def _ca997_main_exit(state: _Sl060State) -> None:
    """``ca997-main-exit.`` [sales/sl060.cbl:L1055] - of ``ca000-BL-Open``.

    Uniquely prefixed in the source, unlike the six ``main-exit`` labels, so the Python
    name needs no section qualification.
    """
    del state


def _ca000_bl_write(state: _Sl060State) -> None:
    """``ca000-BL-Write section.`` [sales/sl060.cbl:L1058] - one posting per invoice.

    Reached only from [:L535-L536] ``if G-L perform ca000-BL-Write``, once per OTM2
    record, i.e. once per invoice rather than once per line item despite the
    maintainer's comment at [:L1062].
    """
    system = state.system_record
    gl_block = system.general_ledger_block
    batch = state.ws_batch_record
    post = state.ws_posting_record
    irs_post = state.ws_irs_posting_record
    oi = state.oi_header
    body = oi.filler_1
    money = body.filler_2

    # [:L1071] move u-date (1:6) to post-date (1:6). [:L1072] move u-date (9:2) to post-
    # date (7:2). REFERENCE MODIFICATION ON BOTH SIDES, 1-BASED.
    post.post_date = move.ref_mod_into(
        post.post_date, 1, 6, move.ref_mod(state.maps03_ws.u_date, 1, 6)
    )
    post.post_date = move.ref_mod_into(
        post.post_date, 7, 2, move.ref_mod(state.maps03_ws.u_date, 9, 2)
    )
    post.ws_post_key.batch = move.move_numeric(
        batch.ws_batch_key.ws_batch_nos,
        _POST["batch"],
        sending_field=_BATCH["ws-batch-nos"],
    )
    # [:L1074] add 1 to items.
    batch.items = arithmetic.add_to(
        1, receiver_value=batch.items, receiving=_BATCH["items"]
    )
    post.ws_post_key.post_number = move.move_numeric(
        batch.items, _POST["post-number"], sending_field=_BATCH["items"]
    )
    post.post_amount = move.move_numeric(
        state.work_net, _POST["post-amount"], sending_field=_WORK_NET
    )

    # [:L1078] move 1 to xx. The STRING pointer, pre-set before the STRING at
    # [:L1091-L1094] rather than inside it.
    state.xx = move.move_numeric(1, _XX)
    state.k = move.move_numeric(
        body.oi_batch.oi_b_nos,
        _K,
        sending_field=otm3.descriptor_for(type(body.oi_batch), "oi_b_nos"),
    )
    state.i = move.move_numeric(
        body.oi_batch.oi_b_item,
        _I,
        sending_field=otm3.descriptor_for(type(body.oi_batch), "oi_b_item"),
    )

    # [:L1085] move oi-invoice to m. `m` is `pic z(7)9` [:L213] - an EDITED picture that
    # suppresses leading zeros to spaces but always shows the final digit.
    state.m = move.move_to_edited(oi.oi_key.oi_invoice, _M)
    state.b = move.move_figurative(move.ZERO, _B)
    state.b = move.inspect_tallying_leading(state.m, move.SPACE, state.b)
    state.c = arithmetic.subtract_giving(
        state.b, minuend=8, receiving=_C
    )
    state.b = arithmetic.add_to(1, receiver_value=state.b, receiving=_B)

    # [:L1091-L1094] string m (b:c) delimited by size " : " delimited by size sales-name
    # delimited by size into Post-Legend pointer xx.
    (post.post_legend, pointer) = move.string_into(
        post.post_legend,
        (
            move.ref_mod(state.m, state.b, state.c),
            " : ",
            state.ws_sales_record.sales_name,
        ),
        pointer=state.xx,
        delimited_by=move.Delimiter.SIZE,
    )
    state.xx = move.move_numeric(pointer, _XX)

    post.post_dr = move.move_numeric(
        system.sales_ledger_block.s_debtors,
        _POST["post-dr"],
        sending_field=_SYSTEM["s-debtors"],
    )
    post.post_cr = move.move_numeric(
        system.sales_ledger_block.sl_sales_ac,
        _POST["post-cr"],
        sending_field=_SYSTEM["sl-sales-ac"],
    )

    # [:L1106-L1109] move zero to dr-pc cr-pc vat-pc vat-amount. Four receivers.
    (post.dr_pc, post.cr_pc, post.vat_pc, post.vat_amount) = move.move_to_all(
        move.ZERO,
        (_POST["dr-pc"], _POST["cr-pc"], _POST["vat-pc"], _POST["vat-amount"]),
    )

    # [:L1111-L1112] move VAT-AC of system-record to VAT-AC of WS-Posting-Record FINDING
    # 11 [sales/sl060.cbl:L1111-L1112] - A QUALIFIED REFERENCE, the field-name-collision
    # pattern the AAP records only for gl070 (anomaly A-21).
    post.vat_ac = move.move_numeric(
        gl_block.vat_ac,
        _POST["vat-ac"],
        sending_field=_SYSTEM["vat-ac"],
    )

    post.vat_amount = arithmetic.add_to(
        money.oi_vat,
        money.oi_e_vat,
        money.oi_c_vat,
        receiver_value=post.vat_amount,
        receiving=_POST["vat-amount"],
    )
    post.post_vat_side = move.move_alphanumeric("CR", _POST["post-vat-side"])
    # [:L1116] move "SL" to Post-Code in WS-Posting-Record.
    post.post_code = move.move_alphanumeric("SL", _POST["post-code"])

    # [:L1118-L1121] The four control-total accumulations, as four separate statements.
    batch.amounts.input_gross = arithmetic.add_to(
        post.post_amount,
        receiver_value=batch.amounts.input_gross,
        receiving=_BATCH["input-gross"],
    )
    batch.amounts.actual_gross = arithmetic.add_to(
        post.post_amount,
        receiver_value=batch.amounts.actual_gross,
        receiving=_BATCH["actual-gross"],
    )
    batch.amounts.input_vat = arithmetic.add_to(
        post.vat_amount,
        receiver_value=batch.amounts.input_vat,
        receiving=_BATCH["input-vat"],
    )
    batch.amounts.actual_vat = arithmetic.add_to(
        post.vat_amount,
        receiver_value=batch.amounts.actual_vat,
        receiving=_BATCH["actual-vat"],
    )

    if _IS_IRS_USED(gl_block.irs_instead) or _IS_IRS_BOTH_USED(gl_block.irs_instead):
        # ELEVEN MOVES build the IRS posting record from the GL one. Counted and listed
        # so that A-18's omission is provably an omission.
        irs_post.ws_irs_post_key.ws_irs_batch = move.move_numeric(
            post.ws_post_key.batch,
            _IRSPOST["ws-irs-batch"],
            sending_field=_POST["batch"],
        )
        irs_post.ws_irs_post_key.ws_irs_post_number = move.move_numeric(
            post.ws_post_key.post_number,
            _IRSPOST["ws-irs-post-number"],
            sending_field=_POST["post-number"],
        )
        irs_post.ws_irs_post_code = move.move_alphanumeric(
            post.post_code,
            _IRSPOST["ws-irs-post-code"],
        )
        irs_post.ws_irs_post_date = move.move_alphanumeric(
            post.post_date, _IRSPOST["ws-irs-post-date"]
        )
        # [:L1132] move Post-DR to WS-IRS-Post-DR. FINDING 12 [sales/sl060.cbl:L1132] -
        # A NARROWING MOVE NOBODY FLAGGED.
        irs_post.ws_irs_post_dr = move.move_numeric(
            post.post_dr, _IRSPOST["ws-irs-post-dr"], sending_field=_POST["post-dr"]
        )
        irs_post.ws_irs_post_cr = move.move_numeric(
            post.post_cr, _IRSPOST["ws-irs-post-cr"], sending_field=_POST["post-cr"]
        )
        irs_post.ws_irs_post_amount = move.move_numeric(
            post.post_amount,
            _IRSPOST["ws-irs-post-amount"],
            sending_field=_POST["post-amount"],
        )
        irs_post.ws_irs_post_legend = move.move_alphanumeric(
            post.post_legend, _IRSPOST["ws-irs-post-legend"]
        )
        # [:L1138-L1139] move 32 to WS-IRS-vat-ac-def Vat-PC *> IS IT ??? ONE MOVE, TWO
        # RECEIVERS IN DIFFERENT RECORDS.
        (irs_post.ws_irs_vat_ac_def, post.vat_pc) = move.move_to_all(
            32, (_IRSPOST["ws-irs-vat-ac-def"], _POST["vat-pc"])
        )
        irs_post.ws_irs_post_vat_side = move.move_alphanumeric(
            post.post_vat_side, _IRSPOST["ws-irs-post-vat-side"]
        )
        irs_post.ws_irs_vat_amount = move.move_numeric(
            post.vat_amount,
            _IRSPOST["ws-irs-vat-amount"],
            sending_field=_POST["vat-amount"],
        )
        facade.spl_posting_write(state.ctx(state.ws_irs_posting_record))

    if _IS_IRS_BOTH_USED(gl_block.irs_instead) or _IS_G_L(
        system.system_data_block.level.level_1
    ):
        post.ws_post_rrn = move.move_numeric(
            state.file_access.rrn,
            _POST["ws-post-rrn"],
            sending_field=_ACCESS["rrn"],
        )
        facade.gl_posting_write(state.ctx(state.ws_posting_record))
        state.file_access.rrn = arithmetic.add_to(
            1, receiver_value=state.file_access.rrn, receiving=_ACCESS["rrn"]
        )

    # [:L1151-L1153] if items = 99 perform ca000-BL-Close / perform ca000-BL-Open. THE
    # 99-ITEM BATCH CAP, and a real control structure with real table effects.
    if arithmetic.compare(batch.items, 99) == 0:
        _ca000_bl_close(state)
        _ca000_bl_open(state)

    _ca998_main_exit(state)


def _ca998_main_exit(state: _Sl060State) -> None:
    """``ca998-main-exit.`` [sales/sl060.cbl:L1155] - of ``ca000-BL-Write``."""
    del state


def _ca000_bl_close(state: _Sl060State) -> None:
    """``ca000-BL-Close section.`` [sales/sl060.cbl:L1158] - write and close the batch.

    Two anomalies live in these twenty lines: A-17's write end at [:L1173] and A-1's
    missing period at [:L1176].
    """
    system = state.system_record
    gl_block = system.general_ledger_block

    facade.gl_batch_write(state.ctx(state.ws_batch_record))
    # [:L1162-L1171] if fs-reply not = zero -> report and, unless unattended, pause. A
    # DIAGNOSTIC WITH NO CONTROL TRANSFER.
    if state.file_access.fs_reply != FsReply.SUCCESS:
        # [:L1163-L1166] The displays become one log record; zz040 supplies the message
        # text and must not alter control flow.
        _zz040_evaluate_message(state)
        # The literal, the file status and the status NAME - `ws-Eval-Msg` is the
        # static `copybooks/FileStat-Msgs.cpy` text keyed on `fs-reply`, so it is
        # a fixed status name and not driver text. No key, no amount.
        _LOG.error(
            "%s%02d %s", _SL132, state.file_access.fs_reply, state.ws_eval_msg
        )
        if state.ws_calling_data.ws_caller.strip() != "xl150":
            # [:L1168] display SL002 / [:L1169] accept ws-reply. BOTH DROPPED -
            # the key-press instruction and the key press. The substantive
            # diagnostic is the record above.
            pass

    # ANOMALY A-17 [sales/sl060.cbl:L1172-L1173] - THE UNEXPLAINED MOVE. if IRS-Both-
    # Used OR G-L *> THIS IS IN PURCHASE PL060 move RRN to postings. *> Why ?
    if _IS_IRS_BOTH_USED(gl_block.irs_instead) or _IS_G_L(
        system.system_data_block.level.level_1
    ):
        gl_block.postings = move.move_numeric(
            state.file_access.rrn,
            _SYSTEM["postings"],
            sending_field=_ACCESS["rrn"],
        )

    facade.gl_batch_close(state.ctx(state.ws_batch_record))

    # ANOMALY A-1 [sales/sl060.cbl:L1172-L1178] - THE MISSING TERMINATING PERIOD. The
    # source reads.
    if _IS_IRS_USED(gl_block.irs_instead) or _IS_IRS_BOTH_USED(gl_block.irs_instead):
        facade.spl_posting_close(state.ctx(state.ws_irs_posting_record))
        # IRS FAN-OUT SITE 7 of 7 - predicate shape `IRS-Both-Used or G-L`, and NESTED
        # here rather than sibling, which is the whole of A-1.
        if _IS_IRS_BOTH_USED(gl_block.irs_instead) or _IS_G_L(
            system.system_data_block.level.level_1
        ):
            facade.gl_posting_close(state.ctx(state.ws_posting_record))

    _ca999_main_exit(state)


def _ca999_main_exit(state: _Sl060State) -> None:
    """``ca999-main-exit.`` [sales/sl060.cbl:L1180] - of ``ca000-BL-Close``."""
    del state


def _zz040_evaluate_message(state: _Sl060State) -> None:
    """``zz040-Evaluate-Message Section.`` [:L1183] - name the file-status code.

    DIAGNOSTIC ONLY: it sets ``ws-Eval-Msg`` and alters no control flow and no table, so
    its output reaches a log record and never a dump.
    """
    state.ws_eval_msg = _file_status_message(state)

    _eval_msg_exit(state)


def _eval_msg_exit(state: _Sl060State) -> None:
    """``Eval-Msg-Exit.`` [sales/sl060.cbl:L1189] - of ``zz040-Evaluate-Message``."""
    del state


# The four date sections. [sales/sl060.cbl:L1192-L1298] All four bodies live in
# `acas_posting/dates.py`, which is the ONE place in this migration where consolidation
# is unambiguously safe.


def _zz050_validate_date(state: _Sl060State) -> None:
    """``zz050-Validate-Date section.`` [:L1192] - operator input to UK order.

    DEAD CODE in this program - see the block comment above - but reproduced in full
    because the declaration exists.
    """
    block = state.system_record.system_data_block
    block.date_form = dates.zz050_validate_date(
        state.ws_date_formats,
        state.maps03_ws,
        block.date_form,
        wrapper=_maps04,
    )

    _zz050_exit(state)


def _zz050_test_date(state: _Sl060State) -> None:
    """``zz050-test-date.`` [sales/sl060.cbl:L1219] - the shared tail of zz050.

    The target of both class-3 transfers in ``zz050-Validate-Date`` and also reached by
    fall-through from [:L1217].
    """
    dates.zz050_test_date(
        state.ws_date_formats, state.maps03_ws, wrapper=_maps04
    )


def _zz050_exit(state: _Sl060State) -> None:
    """``zz050-exit.`` [sales/sl060.cbl:L1224] - of ``zz050-Validate-Date``."""
    del state


def _zz060_convert_date(state: _Sl060State) -> None:
    """``zz060-Convert-Date section.`` [:L1227] - binary day number to text.

    Called from the posting loop at [:L506] with the invoice date already moved into
    ``u-bin`` [:L505], and produces ``ws-date`` in the configured presentation format.
    """
    block = state.system_record.system_data_block
    block.date_form = dates.zz060_convert_date(
        state.ws_date_formats,
        state.maps03_ws,
        block.date_form,
        wrapper=_maps04,
    )

    _zz060_exit(state)


def _zz060_exit(state: _Sl060State) -> None:
    """``zz060-Exit.`` [sales/sl060.cbl:L1259] - of ``zz060-Convert-Date``."""
    del state


def _zz070_convert_date(state: _Sl060State) -> None:
    """``zz070-Convert-Date section.`` [:L1262] - the run date to text.

    Reformats the ``to-day`` linkage parameter - the FIRST of the two observables the
    controlled clock pins - into the configured presentation format. It calls no date
    module at all, so it cannot fail.
    """
    block = state.system_record.system_data_block
    block.date_form = dates.zz070_convert_date(
        state.ws_date_formats, state.to_day, block.date_form
    )

    _zz070_exit(state)


def _zz070_exit(state: _Sl060State) -> None:
    """``zz070-Exit.`` [sales/sl060.cbl:L1289] - of ``zz070-Convert-Date``."""
    del state


def _maps04(maps03_ws: Maps03Ws) -> None:
    """``maps04 section.`` [sales/sl060.cbl:L1292] - the date-module wrapper.

    R-1 forbids invoking the COBOL program, so the call is satisfied by
    ``dates.maps04``, which is the full reimplementation of ``common/maps04.cbl``
    including its 1600-12-31 ordinal epoch, its six-part reject test and - critically -
    its behaviour of LEAVING THE OUTPUT FIELD UNTOUCHED on rejection.
    """
    dates.maps04(maps03_ws)

    _maps04_exit(maps03_ws)


def _maps04_exit(maps03_ws: Maps03Ws) -> None:
    """``maps04-exit.`` [sales/sl060.cbl:L1297] - of the ``maps04`` section."""
    del maps03_ws


# ---------------------------------------------------------------------------
# copy "Proc-ACAS-FH-Calls.cob".                    [sales/sl060.cbl:L1300]
#
# The last line of the program is the ENTITY-NAMED facade copybook, which is
# what settles the calling convention for every one of the twenty-seven verbs
# above: sl060 uses the entity vocabulary (`Sales-Read-Indexed`, `OTM3-Write`,
# `GL-Batch-Close`, ...) and TESTS `fs-reply` INLINE at each call site. It does
# NOT use the handler-named vocabulary of
# `copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob`, and it therefore does NOT get that
# convention's per-handler error-check paragraph or its hard return on an
# unrecoverable open failure. `acas_posting.dal.facade` publishes both alias
# sets over one implementation; this module imports only the entity-named half.
#
# sl060 has NO FACADE STUB BLOCK. gl072 [general/gl072.cbl:L134-L153] and gl080
# declare unused facade paragraphs purely so the linker resolves the copybook's
# full verb set; sl060 declares none, so there is no representation-only
# omission to record for it.
# ---------------------------------------------------------------------------



# ===========================================================================
# --- traceability ---
#
# Required by R-5 and by AAP section 0.4.3, which directs that deliberate
# omissions be "recorded as omissions so that a reader comparing the two files
# does not conclude something was lost". The full label -> function table, the
# GO TO classification and the program -> module row live in
# docs/migration/traceability.md; the anomaly text in
# docs/migration/anomaly-log.md; the questions in
# docs/migration/ambiguity-resolutions.md. What is kept here is what is local to
# this file and stated nowhere else.
#
# CENSUS, measured across [sales/sl060.cbl:L395-L1301]. 1301 source lines, whole
# program in scope. 45 labels -> 45 functions (17 sections, 28 paragraphs), plus
# 11 support functions and `run`. 22 `GO TO` sites, all annotated at the site
# with their class. `main-exit.` is declared SIX times, so every function name is
# section-qualified. Public API is `run` only; `__all__ == ("run",)` and every
# other module-level name is underscore-private, per AAP section 0.3.3.
#
# LINKAGE -> SIGNATURE                          [sales/sl060.cbl:L395-L399]
#  using ws-calling-data system-record system-record-4 to-day file-defs
#  -> run(ws_calling_data, system_record, system_record_4, to_day, file_defs)
# The SL/PL FIVE-parameter shape - not the GL four-parameter shape and not the
# IRS three-parameter shape. `system-record-4` comes from `copy "wssys4.cob"`
# [:L393].
#
# ANOMALIES, FINDINGS AND AMBIGUITIES. Six register entries (A-1, A-8, A-9,
# A-10, A-17, A-18), six findings numbered 7 to 12, and nine questions Q-1 to
# Q-9. Each is annotated at its own reproduction site with its COBOL locator,
# and the module docstring above indexes all three sets. The register text lives
# in docs/migration/anomaly-log.md and docs/migration/ambiguity-resolutions.md.
# A-22 DOES NOT OCCUR HERE: the wrapper is `maps04` [:L1292] and its exit is
# `maps04-exit` [:L1297], so the names AGREE. Two further facts are recorded at
# their sites and nowhere else: `zz050-Validate-Date` [:L1192] is DEAD CODE in
# this program, and the MOVE at [:L1111-L1112] has no terminating period, which
# unlike A-1 is HARMLESS because neither statement is conditional.
#

# STRUCTURAL NOTES - the declaration decisions, recorded in full at their own
# marked block earlier in this file.
#  1 `OI-Header`, `Open-Item-Record-3` and `WS-OTM3-Record` are ONE STORAGE
#  AREA [copybooks/slwsoi3.cob:L9-L19], which is why five moves between them
#  are commented out with `*> is redefines` [:L585], [:L666], [:L760],
#  [:L871], [:L961] and why building the START key at [:L853-L854] and
#  [:L902-L903] DESTROYS the header's own `oi-invoice`. One object, reached
#  through `_Sl060State.oi_header`, which IS `ws_otm3_record`.
#  2 `si-header` [copybooks/slwssoi.cob:L9] is a SECOND, INDEPENDENT 118 bytes
#  of the same layout used as a save area - saved [:L851], restored [:L913] -
#  so it is a separate instance, never an alias.
#  3 `si-approp redefines si-net` [copybooks/slwssoi.cob:L39-L40] is never
#  referenced by this program.
#  4 THE OTM2 WORK SEQUENCE is the one sl055 wrote, navigated with DIRECT
#  COBOL VERBS rather than facade verbs - `open input` [:L480], `read`
#  [:L484], `close` [:L613], `open output` then immediate `close`
#  [:L677-L678] - and it reaches NO SCHEMA TABLE. It lives in
#  `acas_posting.workfiles` and not here because BOTH ends need it and
#  section 0.4.3 forbids one `programs/` module importing another; a carrier
#  declared in either program would leave the other opening an EMPTY file.
#  Its layout is reached through `records.otm3.OiHeader`, the same copybook
#  included under a different name [copybooks/slwsoi3.cob:L18-L19].
#  5 `Sales-Turnover` is published twice by `records.sales_ledger` - four
#  named fields and an immutable OCCURS-4 view. Only the named fields are
#  persisted, so the subscripted add writes BOTH to keep them in step.
#
# OMISSIONS - deliberate.
#  (a) [:L710] `call "SYSTEM" using Print-Report.` The spool-out path, out of
#  scope per AAP section 0.1.1; `copy "print-spool-command.cob"` [:L192]
#  and [:L413] go with it.
#  (b) The four `FS-Cobol-Files-Used`-gated library-call blocks [:L437-L444],
#  [:L448-L456], [:L681-L689], [:L711-L713]. The GATES are reproduced
#  through `condition_names` so the decision stays data-driven; the CALL
#  BODIES are not, because `CBL_CHECK_FILE_EXIST` and `CBL_DELETE_FILE`
#  are GnuCOBOL library routines and R-1 forbids invoking COBOL at
#  runtime. Each gate raises `_CobolLibraryRoutineUnavailable` naming the
#  routine, its locator and its arguments - not skipped, not stubbed, not
#  emulated. All four are unreachable in the RDBMS configuration. Note
#  that [:L441-L442] performs the FACADE verbs `OTM3-Open-Output` and
#  `OTM3-Close` inside gate 1, so they sit behind the same gate. Distinct
#  from these, [:L692], [:L695], [:L703] and [:L711] merely TEST the same
#  condition to choose print behaviour and are reproduced normally.
#  (c) The print file and its line layouts - `selprint` [:L179], `fdprint`
#  [:L187], the open/close pair [:L470], [:L709], every `write
#  print-record` and the whole `l1-*`..`l8-*` families. BUT
#  `ba000-Headings` [:L792] and `ba000-New-Heading` [:L766] still exist as
#  named functions (R-5), and `line-cnt` and `j` are still maintained,
#  because [:L608], [:L621], [:L691] and [:L754] branch on them.
#  (d) `display ... at` becomes log records, but NOT all of it. Converted:
#  [:L418-L419], [:L471-L472], [:L591], [:L595-L598], [:L659], the
#  substantive half of `SL131` [:L733], and [:L1163-L1166]. Not converted,
#  each for a reason: [:L599], [:L734], [:L1168] are pure acknowledgement
#  prompts standing before the `accept`s of (e); [:L421] displays the
#  POSTING DATE, business data the safe-event schema in
#  `acas_posting/dal/status.py` excludes (CWE-532); [:L592-L594] display
#  RECORD KEYS, excluded at any level, and their renderers were eager log
#  arguments, so removing them also removes a failure path a diagnostic
#  must not add; [:L433] displays a SPACE. `ws-Eval-Msg` IS carried,
#  because `zz040-Evaluate-Message` fills it only from the static table
#  `copybooks/FileStat-Msgs.cpy` keyed on `fs-reply`.
#  (e) `accept ws-reply` [:L601], [:L735], [:L1169] - acknowledgement pauses -
#  are dropped, but the `WS-Caller not = "xl150"` tests around them
#  [:L600], [:L734], [:L1167] ARE preserved: that is the codebase's own
#  unattended-mode check.
#  (f) `accept ws-env-lines from lines` [:L403] and the geometry arithmetic
#  [:L404-L409]; `set ENVIRONMENT` [:L415-L416]; `copy "envdiv.cob"`
#  [:L171]. [:L403] is a TERMINAL-GEOMETRY read, NOT a clock read, so this
#  does not touch R-6: sl060 contains ZERO clock reads and both date
#  observables arrive through linkage - `to-day` as a parameter and
#  `Run-Date` [copybooks/wssystem.cob:L67] in `system-record`, used at
#  [:L1022].
#  (g) The message literals [:L261-L268]. `SL130`, `SL132` and the diagnostic
#  half of `SL131` survive as log text. `SL002` and `SL003` are declared
#  and deliberately never referenced. `SL133` and `SL133T` are never
#  DISPLAYED at all - [:L704], [:L706] move them into `print-record`,
#  which is report content. Every member stays declared because R-5 maps
#  the whole `01 Error-Messages.` group.
#  (h) [:L1079-L1080] `move oi-b-nos to k` and `move oi-b-item to i` are
#  REPRODUCED although they are DEAD STORES - their only readers are the
#  commented-out STRING at [:L1096-L1101] - because the moves execute.
#  (i) [:L1011-L1014] the commented-out open-then-fallback pair is reproduced
#  as the ABSENCE it is: a failed `GL-Batch-Open` is not recovered from.
#  (j) sl060 has NO facade stub block, unlike [general/gl072.cbl:L134-L153],
#  so there is no representation-only declaration to omit.
#
# FACADE VERBS - 27 DISTINCT, all entity-named, because the program's last line
# is `copy "Proc-ACAS-FH-Calls.cob"` [:L1300] and it tests `fs-reply` INLINE
# rather than through a per-handler error-check paragraph: Sales (acas012) 5,
# OTM3 (acas019) 7, Value (acas013) 4, GL-Batch (acas007) 3, GL-Posting
# (acas006) 4, SPL-Posting (acas008) 4. `SPL-Posting-Open-Output` MEANS DELETE
# EVERY ROW of PSIRSPOST-REC [common/acas008.cbl:L313-L319],
# [common/acas008.cbl:L571-L574]; `acas008` also rejects read-indexed, rewrite,
# start and delete UNCONDITIONALLY at entry [common/acas008.cbl:L299-L307],
# which is anomaly A-6, and sl060 calls none of those four. Both `OTM3-Start`
# calls are preceded by `set fn-not-less-than to true` [:L855], [:L904],
# expressed as `AccessType.NOT_LESS_THAN` and never as a raw integer.
#
# TABLES THIS PROGRAM WRITES, and the gate that decides each.
#  SALEDGER-REC   Write [:L581] / Rewrite [:L583]; also mutated by
#  `ba000-Clear-Invoice-Deduct` [:L967].  UNGATED.
#  SAITM3-REC     Write [:L586], Rewrite [:L761], [:L962].  UNGATED.
#  VALUEANAL-REC  Rewrite [:L990], [:L1002]. Gated `total-deduct not = zero`
#  [:L643].
#  SYSTOT-REC     PERIOD TOTAL 3 OF 9 at [:L641] and 4 OF 9 at [:L700].
#  [:L700] IS UNCONDITIONAL - it sits OUTSIDE the `if` at
#  [:L695], which guards only the print line - and getting
#  that wrong would drop a write in file mode and add one in
#  RDBMS mode. The nine sites are the SOLE WRITERS of
#  SYSTOT-REC in the whole migration (AAP section 0.6.4).
#  GLBATCH-REC    Write [:L1161], reached only `if G-L` [:L649] or from the
#  99-item cap [:L1152].
#  GLPOSTING-REC  Write [:L1147], gated `if G-L` [:L535] then
#  `IRS-Both-Used or G-L` [:L1144-L1145].
#  PSIRSPOST-REC  Write [:L1142], gated `if G-L` [:L535] then `irs-used or
#  IRS-Both-Used` [:L1126].
#  SYSTEM-REC     via A-17 [:L1173] and [:L1018] - mutated in storage with no
#  rewrite here; see Q-6.
# Plus the OTM2 work sequence, which reaches no table and is TRUNCATED at
# [:L677-L678].
#
# THE SEVEN IRS FAN-OUT SITES, three distinct predicate shapes, all evaluated
# through `condition_names` and never against a raw "Y"/"B"/1: [:L1039],
# [:L1046], [:L1126], [:L1144], [:L1172], [:L1175], [:L1177] - the last nested
# inside [:L1175] by A-1. Condition names `88 IRS-Used value "Y"` and
# `88 IRS-Both-Used value "B"` on `05 IRS-Instead pic x`
# [copybooks/wssystem.cob:L179-L181], and `88 G-L value 1`
# [copybooks/wssystem.cob:L85]. THE GATING IS LAYERED: `ca000-BL-Open`,
# `ca000-BL-Write` and `ca000-BL-Close` are each reached ONLY `if G-L` [:L466],
# [:L535], [:L649] and only then test the IRS flags, SO IN IRS-ONLY MODE NONE OF
# THE THREE RUNS AT ALL and no batch, GL posting or IRS posting row is written.
# AAP section 0.6.4 records that this switch "changes which tables a run
# touches", so a scenario must pin it explicitly.
#
# ARITHMETIC - ZERO `ROUNDED` SITES IN THIS PROGRAM; the five in the whole
# migration are [general/gl051.cbl:L791], [general/gl051.cbl:L796],
# [general/gl080.cbl:L328], [irs/irs030.cbl:L1551] and [irs/irs030.cbl:L1562].
# EVERY STORE HERE TRUNCATES TOWARD ZERO, the default path of
# `acas_posting.cobol.arithmetic`; the `rounded` flag is never set in any of the
# 93 arithmetic calls, which an AST audit over the executable code confirms
# rather than a text search, since the token would otherwise match this
# sentence. Zero `ON SIZE ERROR` clauses and zero `REMAINDER` phrases. Verb
# shapes map to `multiply_by` (the three sign flips [:L571], [:L758], [:L861]),
# `multiply_by_giving` [:L821], [:L837], `divide_into_giving` [:L827], [:L843],
# `subtract_from`, `subtract_giving` [:L409], [:L538], [:L578], [:L1088],
# `add_giving` (variadic, summed at intermediate precision and quantized ONCE -
# notably the two NINE-ADDEND statements [:L728-L730], [:L921-L923]) and
# `add_to` [:L552], [:L559], [:L884], [:L1114]. Relation-condition arithmetic
# with NO receiver at [:L621] and [:L691] goes through
# `arithmetic.intermediate`, so no temporary field can quantize differently.
# Reference modification is 1-BASED through `move.ref_mod` /
# `move.ref_mod_into`, never Python slicing - [:L1071-L1072] builds the
# 8-character `Post-Date` from the 10-character `u-date` on BOTH sides.
# `INITIALIZE ... WITH FILLER` [:L497], `INSPECT ... TALLYING FOR LEADING`
# [:L1087], the edited MOVE into `pic z(7)9` [:L1085] and `STRING ... INTO ...
# POINTER` [:L1091-L1094] all use the published `cobol.move` primitives.
#
# DATE SECTIONS - which consolidated body each call selects.
#  `zz050-Validate-Date` [:L1192] -> `dates.zz050_validate_date`, the
#  NON-gl051 variant, because gl051 carries three extra
#  `inspect ... replacing` statements [general/gl051.cbl:L1178-L1180].
#  `zz060-Convert-Date` [:L1227] -> `dates.zz060_convert_date` with
#  `wrapper=_maps04`, because sl060 performs `maps04` [:L1236] where
#  gl051 and gl070 perform `maps03` - the ONE TOKEN that differs.
#  `zz070-Convert-Date` [:L1262] -> `dates.zz070_convert_date`, byte-identical
#  in all ten carriers.
#  `maps04` [:L1292] -> `dates.maps04`, the full reimplementation of
#  `common/maps04.cbl` (R-1 forbids the `call "maps04"` at [:L1295]),
#  including its 1600-12-31 epoch, its six-part reject test
#  [common/maps04.cbl:L140-L146] and its LEAVING THE OUTPUT FIELD
#  UNTOUCHED on rejection [common/maps04.cbl:L146], [common/maps04.cbl:L154]
#  - which is why `move zero to u-bin` [:L1221] is load-bearing.
#
# LAYERING (AAP section 0.4.3). Imports only `records.*`, `dal.facade`,
# `dal.status`, `cobol.arithmetic`, `cobol.move`, `cobol.condition_names`,
# `cobol.field`, `cobol.picture`, `dates`, `workfiles` and the standard library.
# NO `cli`, NO `dal.acas*`, NO `dal.connection`, NO `dal.cursor_state`, NO
# `clock`, NO `harness`, NO `dictionary.generate` and NO other `programs.*` -
# including NOT `programs.sl055_invoice_extract_analysis`, even though sl055
# produces the OTM2 sequence this program consumes. The handoff is through the
# work sequence, exactly as in COBOL, and the CLI sequences the two calls:
# `acas_posting/cli/sl_invoice_post.py` dispatches sl055 then sl060, gating on
# `if ws-term-code not = zero` [sales/sales.cbl:L759-L768] - the SALES gate,
# different from the GL's `= 5` test and from Purchase, which has no gate.
# ===========================================================================
