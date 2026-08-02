"""``sl060`` - Sales Invoice Posting & Report, migrated from ``sales/sl060.cbl``.

THE MIGRATION BOUNDARY IS THE WHOLE PROGRAM. All 1,301 lines of
``sales/sl060.cbl`` are in scope, unlike its two partially-migrated siblings
``gl051`` (control-total gate only) and ``irs030`` (``Ledger-Postings-Add``
only). The COBOL itself is FROZEN SPECIFICATION - read exhaustively, never
modified. The AAP section 0.8.1 is explicit, verbatim: "Any diff touching
``common/*.cbl``, ``common/*.scb``, ``copybooks/*.cob``, ``general/*.cbl``,
``sales/*.cbl``, ``purchase/*.cbl``, ``irs/*.cbl`` or ``mysql/ACASDB.sql`` is a
defect in the migration, regardless of how harmless it appears."

HOW TO READ THE LOCATORS. Every claim in this module cites the line it came
from, because R-5 makes the mapping between the two files a deliverable rather
than a courtesy. Two forms appear, and they mean the same thing:

* ``[sales/sl060.cbl:L472]`` - the full form, used on first reference in a
  docstring or comment block and always for a file other than this one.
* ``[:L659]`` - the file-local shorthand for the SAME file, ``sales/sl060.cbl``.
  A locator with an empty path is ALWAYS this program's COBOL source. Ranges are
  written ``[:L1096-L1133]``.

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

THE ONE OPEN INTEGRATION SEAM, stated plainly so nobody mistakes it for a
defect in this module. ``acas_posting/dal/facade.py`` DOES NOT EXIST YET. The
AAP lists it as a file to be CREATED and ``acas_posting/dal/__init__`` says so
itself - "Target inventory, not yet present: `facade`". This module is the first
program to need it: its sibling ``gl071`` is a pure sort and its own docstring
forbids importing anything from ``acas_posting.dal`` at all. So until that file
lands, ``import acas_posting.programs.sl060_invoice_posting`` raises
``ImportError: cannot import name 'facade' from 'acas_posting.dal'``.

That is the correct state of affairs, not a bug to work around:

* The import form is the one AAP section 0.4.3 mandates verbatim - ``copy
  "Proc-ACAS-FH-Calls.cob".`` becomes ``from acas_posting.dal import facade``.
  It is written plainly, at module scope, with no ``try``/``except``, no lazy
  ``__getattr__`` and no local shim. Any of those would hide a genuinely absent
  dependency and would leave a stub in the shipped package, which the zero-
  placeholder policy forbids outright.
* The twenty-seven verbs this module performs are enumerated in the traceability
  footer with the locator of every call site, so the facade's required surface
  is fully specified from here.
* Behaviour was verified against an in-memory double implementing all twenty-
  seven verbs, exercising each of the six anomalies, both period totals, the
  99-item batch cap, the two-pass credit-note walk, the OTM2 truncation and an
  end-to-end ``run``. The module is complete and correct; it is waiting on one
  sibling file, and nothing in it needs to change when that file arrives.

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

THE RULES THIS FILE IS HELD TO. There is no user rules document for this
project: ``review_rules`` returns "No user rules provided." The six binding
rules live in the AAP section 0.7.2 and are restated where they bite.

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
from typing import Callable, Final

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
from acas_posting.workfiles import LineSequentialWorkFile

__all__: Final[tuple[str, ...]] = ("run",)


#: The frozen specification this module reproduces. Every locator below is
#: relative to it unless another path is named.
_PROGRAM: Final[str] = "sales/sl060.cbl"

#: ``77 prog-name pic x(15) value "SL060 (3.3.01)".`` [sales/sl060.cbl:L191].
#: The version is the maintainer's; the 3.3.01 changelog entry [:L129-L136] is
#: itself an A-1 and A-18 flag.
_PROG_NAME: Final[str] = "SL060 (3.3.01)"

#: Diagnostics go here. AAP section 0.3.4: display output with no database
#: effect "must not alter control flow and must not appear in any table dump".
_LOG: Final[logging.Logger] = logging.getLogger("acas_posting.programs.sl060")


# ---------------------------------------------------------------------------
# R-1 - the boundary where a GnuCOBOL library routine would have been called
# ---------------------------------------------------------------------------


class _CobolLibraryRoutineUnavailable(RuntimeError):
    """A ``call "CBL_..."`` site was reached, and R-1 forbids honouring it.

    Four blocks of this program call GnuCOBOL library routines behind an
    ``if FS-Cobol-Files-Used`` gate: ``CBL_CHECK_FILE_EXIST`` at
    [sales/sl060.cbl:L438] and [:L449] and [:L682], and ``CBL_DELETE_FILE`` at
    [:L713]. R-1 forbids invoking COBOL at runtime, so the CALL cannot be
    honoured, and R-3 forbids inventing a replacement, so it cannot be
    emulated either.

    The GATES are reproduced faithfully through the condition-name vocabulary
    (see :data:`_IS_FS_COBOL_FILES_USED`), which keeps the decision data-driven
    at runtime exactly as the COBOL's is. Only the CALL bodies are refused, and
    they are refused LOUDLY rather than silently skipped or stubbed as a no-op,
    because a silent skip would make an unreachable branch look like a
    reproduced one.

    The branch is unreachable in the configuration this migration targets:
    ``88 FS-Cobol-Files-Used value zero`` [copybooks/wssystem.cob:L113] against
    ``88 FS-RDBMS-Used value 1``
    [copybooks/wssystem.cob:L116], and the whole data-access layer is
    SQL against the frozen schema. Whether any scenario nonetheless sets the
    flat-file mode is AMBIGUITY Q-2, for the oracle to settle.
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


# ---------------------------------------------------------------------------
# Descriptor provenance
#
# R-2 and AAP section 0.3.1: "cobol/ contains no business logic and programs/
# contains no numeric primitives." Every store below names the receiving field's
# descriptor, so truncation, scale, sign and width come from the DECLARATION and
# never from hand-written arithmetic. That is also what makes A-8 fall out for
# free: the double truncation happens because work-2 has scale 0 and
# Sales-Average is an integer, not because this module rounds anything.
# ---------------------------------------------------------------------------


def _index_descriptors(record_class: type) -> dict[str, FieldDescriptor]:
    """Index every ``FieldDescriptor`` of a record layout by its COBOL name.

    The record modules publish their descriptors as a ``FIELDS`` tuple on each
    dataclass in the layout tree, so a group's children live on the group's own
    class. This walks that tree and returns a flat, CASE-INSENSITIVE index.

    Case-insensitivity is not cosmetic. The generated layouts spell some names
    differently from the copybook - ``SL-Sales-Ac`` for ``SL-Sales-AC``,
    ``Oi-3-Flag`` for ``oi-3-flag`` - and a lookup that failed on case would
    send an author hand-coding a descriptor, which is precisely how a wrong
    picture clause enters a posting.

    The modules use ``from __future__ import annotations``, so a dataclass
    field's ``.type`` is a STRING; :func:`typing.get_type_hints` is what turns
    it back into the nested class. The first declaration of a repeated name
    wins, which matters only for ``filler`` - never for a field this module
    reads or writes.
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


#: ``copy "wssystem.cob"`` [sales/sl060.cbl:L392] - 169 columns of SYSTEM-REC.
_SYSTEM: Final[dict[str, FieldDescriptor]] = _index_descriptors(SystemRecord)

#: ``copy "wssys4.cob"`` [:L393] - SYSTOT-REC, the period totals.
_SYSTOT: Final[dict[str, FieldDescriptor]] = _index_descriptors(SystemRecord4)

#: ``copy "wssl.cob"`` [:L275] - SALEDGER-REC.
#:
#: This layout publishes its descriptors as a module-level mapping keyed by the
#: PYTHON attribute path rather than as a per-class ``FIELDS`` tuple, so it is
#: re-keyed here on the COBOL name to give every lookup in this file one shape.
#: The first declaration of a name wins, as it does in :func:`_index_descriptors`.
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

#: ``copy "wsbatch.cob"`` [:L276] - GLBATCH-REC.
_BATCH: Final[dict[str, FieldDescriptor]] = _index_descriptors(GlBatchRecord)

#: ``copy "wspost.cob"`` [:L277] - GLPOSTING-REC.
_POST: Final[dict[str, FieldDescriptor]] = _index_descriptors(WsPostingRecord)

#: ``copy "wspost-irs.cob"`` [:L278] - PSIRSPOST-REC, the SIGN LEADING record.
_IRSPOST: Final[dict[str, FieldDescriptor]] = _index_descriptors(WsIrsPostingRecord)

#: ``copy "wsval.cob"`` [:L274] - VALUEANAL-REC.
_VALUE: Final[dict[str, FieldDescriptor]] = _index_descriptors(WsValueRecord)

#: ``copy "wsfnctn.cob"`` [:L194] - File-Access, Logging-Data, RDB-Data.
_ACCESS: Final[dict[str, FieldDescriptor]] = _index_descriptors(FileAccess)

#: ``copy "wsmaps03.cob"`` [:L193] - the date-conversion linkage block.
_MAPS03: Final[dict[str, FieldDescriptor]] = _index_descriptors(Maps03Ws)


# ---------------------------------------------------------------------------
# WORKING-STORAGE, field for field from [sales/sl060.cbl:L196-L268]
#
# Declared here rather than in records/ because these are the PROGRAM's own
# storage, not a copybook layout: nothing else in the migration may see them.
# Every descriptor carries the source locator of its declaration, so a reader
# can check the picture against the frozen source without leaving this file.
# ---------------------------------------------------------------------------

#: ``03 ws-reply pic x.`` [:L197]
_WS_REPLY: Final[FieldDescriptor] = descriptor_for(
    "pic x", name="ws-reply", source_locator=f"{_PROGRAM}:L197", parent_group="ws-data"
)
#: ``03 ws-error pic 9 value zero.`` [:L198] - conditional variable of
#: ``88 sales-missing`` [:L199].
_WS_ERROR: Final[FieldDescriptor] = descriptor_for(
    "pic 9 value zero", name="ws-error",
    source_locator=f"{_PROGRAM}:L198", parent_group="ws-data",
)
#: ``03 wx-reply pic xxx.`` [:L200] - referenced ONLY by the commented-out
#: confirmation dialogue [:L426-L430], retained for declaration fidelity.
_WX_REPLY: Final[FieldDescriptor] = descriptor_for(
    "pic xxx", name="wx-reply", source_locator=f"{_PROGRAM}:L200", parent_group="ws-data"
)
#: ``03 xx pic 99.`` [:L201] - the STRING pointer, 1-based [:L1078].
_XX: Final[FieldDescriptor] = descriptor_for(
    "pic 99", name="xx", source_locator=f"{_PROGRAM}:L201", parent_group="ws-data"
)
#: ``03 c-check pic 9.`` [:L202] with ``88 c-exists value 1`` [:L203].
#: DECLARED AND NEVER REFERENCED anywhere in the program - retained because R-5
#: traces declarations, not just uses.
_C_CHECK: Final[FieldDescriptor] = descriptor_for(
    "pic 9", name="c-check", source_locator=f"{_PROGRAM}:L202", parent_group="ws-data"
)
#: ``03 ws-eval-msg pic x(25) value spaces.`` [:L204] - the receiver of the
#: FileStat message table [:L1186].
_WS_EVAL_MSG: Final[FieldDescriptor] = descriptor_for(
    "pic x(25) value spaces",
    name="ws-eval-msg",
    source_locator=f"{_PROGRAM}:L204",
    parent_group="ws-data",
)
#: ``03 work-1 pic s9(7)v99 comp-3 value zero.`` [:L205]
_WORK_1: Final[FieldDescriptor] = descriptor_for(
    "pic s9(7)v99 comp-3 value zero",
    name="work-1",
    source_locator=f"{_PROGRAM}:L205",
    parent_group="ws-data",
)
#: ``03 work-2 pic s9(14) comp-3.`` [:L206]
#:
#: ANOMALY A-8 [sales/sl060.cbl:L206] - FOURTEEN DIGITS, ZERO DECIMAL PLACES.
#: This is one half of the double truncation: ``add work-goods to work-2``
#: [:L826] moves a two-decimal value into a zero-scale receiver, so the pence
#: are discarded on every accumulation. Reproduced deliberately per R-4; DO NOT
#: FIX - widening the scale here would diverge from the oracle on almost every
#: invoice.
_WORK_2: Final[FieldDescriptor] = descriptor_for(
    "pic s9(14) comp-3", name="work-2",
    source_locator=f"{_PROGRAM}:L206", parent_group="ws-data",
)
#: ``03 work-a pic s9(7)v99 comp-3 value zero.`` [:L207]
_WORK_A: Final[FieldDescriptor] = descriptor_for(
    "pic s9(7)v99 comp-3 value zero",
    name="work-a",
    source_locator=f"{_PROGRAM}:L207",
    parent_group="ws-data",
)
#: ``03 work-b pic s9(7)v99 comp-3 value zero.`` [:L208] - the un-applied
#: credit accumulator that period-total site 4 writes [:L700].
_WORK_B: Final[FieldDescriptor] = descriptor_for(
    "pic s9(7)v99 comp-3 value zero",
    name="work-b",
    source_locator=f"{_PROGRAM}:L208",
    parent_group="ws-data",
)
#: ``03 first-pass pic x.`` [:L209] - the two-pass state of ba000-CR-Notes.
_FIRST_PASS: Final[FieldDescriptor] = descriptor_for(
    "pic x", name="first-pass", source_locator=f"{_PROGRAM}:L209", parent_group="ws-data"
)
#: ``03 i pic 999.`` [:L210] - the batch item, [:L1080].
_I: Final[FieldDescriptor] = descriptor_for(
    "pic 999", name="i", source_locator=f"{_PROGRAM}:L210", parent_group="ws-data"
)
#: ``03 j pic 999.`` [:L211] - the page counter of the two heading sections.
_J: Final[FieldDescriptor] = descriptor_for(
    "pic 999", name="j", source_locator=f"{_PROGRAM}:L211", parent_group="ws-data"
)
#: ``03 k pic 9(5).`` [:L212] - the batch number, [:L1079].
_K: Final[FieldDescriptor] = descriptor_for(
    "pic 9(5)", name="k", source_locator=f"{_PROGRAM}:L212", parent_group="ws-data"
)
#: ``03 m pic z(7)9.`` [:L213] - the SPACE-SUPPRESSED EDITED field the
#: Post-Legend chain tallies over [:L1085-L1091].
_M: Final[FieldDescriptor] = descriptor_for(
    "pic z(7)9", name="m", source_locator=f"{_PROGRAM}:L213", parent_group="ws-data"
)
#: ``03 b binary-char value zero.`` [:L214] - the leading-space tally [:L1087].
_B: Final[FieldDescriptor] = descriptor_for(
    "binary-char value zero", name="b",
    source_locator=f"{_PROGRAM}:L214", parent_group="ws-data",
)
#: ``03 c binary-char value zero.`` [:L215] - the extracted length [:L1088].
_C: Final[FieldDescriptor] = descriptor_for(
    "binary-char value zero", name="c",
    source_locator=f"{_PROGRAM}:L215", parent_group="ws-data",
)
#: ``03 work-net pic s9(7)v99 comp-3.`` [:L216] - the five-addend gross-goods
#: figure [:L523] that becomes Post-Amount [:L1076].
_WORK_NET: Final[FieldDescriptor] = descriptor_for(
    "pic s9(7)v99 comp-3",
    name="work-net",
    source_locator=f"{_PROGRAM}:L216",
    parent_group="ws-data",
)
#: ``03 work-vat pic s9(7)v99 comp-3.`` [:L217] - the four-addend VAT figure
#: [:L520].
_WORK_VAT: Final[FieldDescriptor] = descriptor_for(
    "pic s9(7)v99 comp-3",
    name="work-vat",
    source_locator=f"{_PROGRAM}:L217",
    parent_group="ws-data",
)
#: ``03 work-goods pic s9(7)v99 comp-3.`` [:L218]
#:
#: ANOMALY A-8 [sales/sl060.cbl:L218] - TWO DECIMAL PLACES, against work-2's
#: zero [:L206]. The mismatch IS the first truncation. Reproduced deliberately
#: per R-4; DO NOT FIX.
_WORK_GOODS: Final[FieldDescriptor] = descriptor_for(
    "pic s9(7)v99 comp-3",
    name="work-goods",
    source_locator=f"{_PROGRAM}:L218",
    parent_group="ws-data",
)
#: ``03 total-group occurs 3 comp-3.`` [:L219] - the OCCURS and the USAGE are
#: both on the GROUP, so the two children inherit COMP-3 from here.
_TOTAL_GROUP: Final[FieldDescriptor] = descriptor_for(
    "occurs 3 comp-3",
    name="total-group",
    source_locator=f"{_PROGRAM}:L219",
    parent_group="ws-data",
)
#: ``05 total-net pic s9(7)v99.`` [:L220] - one per occurrence.
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
#: ``05 total-vat pic s9(7)v99.`` [:L221] - one per occurrence.
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
#: check the COBOL does not have.
_A: Final[FieldDescriptor] = descriptor_for(
    "pic 9 value zero", name="a", source_locator=f"{_PROGRAM}:L222", parent_group="ws-data"
)
#: ``03 line-cnt pic 99 comp value zero.`` [:L223] - the page-break counter.
#: Retained although the print file is omitted, because [:L608], [:L621],
#: [:L691] and [:L754] all BRANCH on it.
_LINE_CNT: Final[FieldDescriptor] = descriptor_for(
    "pic 99 comp value zero",
    name="line-cnt",
    source_locator=f"{_PROGRAM}:L223",
    parent_group="ws-data",
)
#: ``03 ws-deduction pic s9(7)v99 comp-3 value zero.`` [:L224]
_WS_DEDUCTION: Final[FieldDescriptor] = descriptor_for(
    "pic s9(7)v99 comp-3 value zero",
    name="ws-deduction",
    source_locator=f"{_PROGRAM}:L224",
    parent_group="ws-data",
)
#: ``03 total-deduct pic s9(7)v99 comp-3 value zero.`` [:L225] - what period
#: total site 3 writes [:L641] and what ba000-Analise-Deductions subtracts.
_TOTAL_DEDUCT: Final[FieldDescriptor] = descriptor_for(
    "pic s9(7)v99 comp-3 value zero",
    name="total-deduct",
    source_locator=f"{_PROGRAM}:L225",
    parent_group="ws-data",
)
#: ``03 total-mov-ded pic s9(5) comp value zero.`` [:L226] - a COUNT, not money.
_TOTAL_MOV_DED: Final[FieldDescriptor] = descriptor_for(
    "pic s9(5) comp value zero",
    name="total-mov-ded",
    source_locator=f"{_PROGRAM}:L226",
    parent_group="ws-data",
)
#: ``03 save-level-1 pic 9 value zero.`` [:L227] - referenced ONLY by the
#: commented-out GL bypass [:L461] and [:L718]; retained for fidelity.
_SAVE_LEVEL_1: Final[FieldDescriptor] = descriptor_for(
    "pic 9 value zero",
    name="save-level-1",
    source_locator=f"{_PROGRAM}:L227",
    parent_group="ws-data",
)
#: ``03 File-18-status pic 9 value zero.`` [:L231] - the conditional variable
#: of ``88 File-18-Exists`` [:L232] and ``88 File-18-Not-Exists`` [:L233].
_FILE_18_STATUS: Final[FieldDescriptor] = descriptor_for(
    "pic 9 value zero",
    name="File-18-status",
    source_locator=f"{_PROGRAM}:L231",
    parent_group="ws-data",
)

#: ``01 error-code pic 999.`` [:L272] - declared between two copybooks and
#: never referenced; retained for declaration fidelity.
_ERROR_CODE: Final[FieldDescriptor] = descriptor_for(
    "pic 999", name="error-code", source_locator=f"{_PROGRAM}:L272", level="01"
)

# ``01 ws-Test-Date pic x(10).`` [:L235] and ``01 ws-date-formats.``
# [:L236-L257] are the group that acas_posting.dates.WsDateFormats publishes -
# the same four items and the same three REDEFINES views - so they are taken
# from there rather than redeclared. ws-env-lines [:L228], ws-lines [:L229] and
# ws-23-lines [:L230] are terminal geometry, omitted with the ACCEPT that fills
# them (see OMISSIONS).

# ---------------------------------------------------------------------------
# ``01 Error-Messages.`` [sales/sl060.cbl:L259-L268]
#
# Message text only. Every use is a DISPLAY, so under AAP section 0.3.4 these
# become log records: they must not alter control flow and must not appear in
# any table dump. The widths are the declared ones so the log reads exactly as
# the screen did.
# ---------------------------------------------------------------------------

_SL002: Final[str] = "SL002 Note error and hit return"  # pic x(31) [:L261]
_SL003: Final[str] = "SL003 Hit Return To Continue"  # pic x(28) [:L262]
_SL130: Final[str] = "SL130 Error writing Open Item 3 Record"  # pic x(38) [:L264]
_SL131: Final[str] = "SL131 PE - CR SWOP: Return to continue"  # pic x(38) [:L265]
_SL132: Final[str] = "SL132 Err on Batch file write : "  # pic x(32) [:L266]
_SL133: Final[str] = "SL133 Warning Record/s missing in Sales File"  # pic x(44) [:L267]
_SL133T: Final[str] = "SL133 Warning Record/s missing in Sales Table"  # pic x(45) [:L268]

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
    0: "Success                  ",  # [copybooks/FileStat-Msgs.cpy:L24]
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

#: The ``when other`` arm [copybooks/FileStat-Msgs.cpy:L58].
_FILE_STATUS_UNKNOWN: Final[str] = "Unknown File Status      "

# ---------------------------------------------------------------------------
# Condition names - every 88-level this program tests
#
# R-2 and the agent brief both forbid a bare "Y", "B", 1 or 0 standing in for a
# condition name. The catalogued ones are manufactured by the published
# vocabulary; the four PROGRAM-LOCAL ones and the two on the saved header are
# declared here as specs over their own conditional variables, because they are
# declared in this program (or in a copybook only this program copies) and no
# catalogue can know them.
# ---------------------------------------------------------------------------

#: ``88 G-L value 1.`` [copybooks/wssystem.cob:L85]. Gates ca000-BL-Open
#: [:L466] and ca000-BL-Write [:L535], and appears in four of the seven fan-out
#: predicates.
_IS_G_L: Final[Callable[[int | str | Decimal], bool]] = condition_names.predicate_for("G-L")

#: ``88 IRS-Used value "Y".`` [copybooks/wssystem.cob:L180]
_IS_IRS_USED: Final[Callable[[int | str | Decimal], bool]] = condition_names.predicate_for(
    "IRS-Used"
)

#: ``88 IRS-Both-Used value "B".`` [copybooks/wssystem.cob:L181]
_IS_IRS_BOTH_USED: Final[Callable[[int | str | Decimal], bool]] = condition_names.predicate_for(
    "IRS-Both-Used"
)

#: ``88 FS-Cobol-Files-Used value zero.`` [copybooks/wssystem.cob:L113]. Gates
#: the four library-call blocks and four presentation tests.
_IS_FS_COBOL_FILES_USED: Final[Callable[[int | str | Decimal], bool]] = (
    condition_names.predicate_for("FS-Cobol-Files-Used")
)

#: ``88 Customer-Dead value zero.`` on the sales-ledger status
#: [copybooks/wssl.cob]. Tested at [:L567].
_IS_CUSTOMER_DEAD: Final[Callable[[int | str | Decimal], bool]] = condition_names.predicate_for(
    "Customer-Dead"
)

#: ``88 S-Closed value 1.`` [copybooks/slwsoi.cob:L49]. The copybook must be
#: named: S-Closed is declared in both the sales and the purchase open-item
#: layouts, and only the copybook distinguishes them.
_IS_S_CLOSED: Final[Callable[[int | str | Decimal], bool]] = condition_names.predicate_for(
    "S-Closed", copybook="copybooks/slwsoi.cob"
)

#: ``88 sales-missing value 1.`` [sales/sl060.cbl:L199] on ``ws-error``
#: [:L198]. Set at [:L496], tested at [:L702].
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

#: ``88 c-exists value 1.`` [sales/sl060.cbl:L203] on ``c-check`` [:L202].
#: DECLARED AND NEVER TESTED anywhere in the program; retained because R-5
#: traces declarations.
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

#: ``88 File-18-Exists value 0.`` [sales/sl060.cbl:L232]
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

#: ``88 File-18-Not-Exists value 1.`` [sales/sl060.cbl:L233]
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

#: ``88 si-s-open value zero.`` [copybooks/slwssoi.cob:L49] - on the SAVED
#: header. Declared and never tested; its sibling below is likewise untested,
#: because ba000-Apportion writes si-status rather than reading it.
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

#: ``88 si-s-closed value 1.`` [copybooks/slwssoi.cob:L50] - "Paid".
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



# ---------------------------------------------------------------------------
# The open-item header - one layout, three names, two storages
#
# STRUCTURAL NOTE 1. ``copy "slwsoi3.cob"`` [sales/sl060.cbl:L279] declares
# ``01 WS-OTM3-Record pic x(118).`` [copybooks/slwsoi3.cob:L9], then
# ``01 Open-Item-Record-3 redefines WS-OTM3-Record.``
# [copybooks/slwsoi3.cob:L11], and then copies the body layout with
# ``replacing ==OI-Header== by ==OI-Header redefines WS-OTM3-Record==``
# [copybooks/slwsoi3.cob:L18-L19]. So OI-HEADER, OPEN-ITEM-RECORD-3 AND
# WS-OTM3-RECORD ARE ALL THE SAME 118 BYTES. That is why five moves in this
# program are commented out with the maintainer's own ``*> is redefines``
# annotation - [:L585], [:L666], [:L760], [:L871] and [:L961] - and it is
# recorded in the 3.2.14 changelog entry [:L120].
#
# The consequences are load-bearing, not cosmetic:
#
#   * ``perform OTM3-Write`` [:L586] writes whatever ``oi-header`` holds; no
#     move precedes it.
#   * ``perform OTM3-Read-Next`` [:L662, :L867] fills ``oi-header``.
#   * ``move oi-cr to oi3-invoice`` [:L854] and ``move zero to oi3-invoice``
#     [:L903] OVERWRITE ``oi-invoice``, because ``oi3-invoice`` is the same
#     eight digits. Building the START key therefore DESTROYS the header's own
#     invoice number - which is safe only because [:L851] saved the whole header
#     first and [:L913] restores it.
#
# This module realises the redefines as ONE object: :attr:`_Sl060State.oi_header`
# is the facade's ``ws_otm3_record``, and the ``oi3-*`` names are reached through
# the same fields (``oi3-customer`` is ``oi_key.oi_customer``, ``oi3-invoice`` is
# ``oi_key.oi_invoice``, ``oi3-date`` is ``oi_date``). The records layer also
# publishes ``OpenItemRecord3`` and ``Oi3Key`` as separate declarations and - as
# its ``QuartersView`` docstring says of the same situation - keeps neither in
# step with the other. Using one object is what keeps them in step here.
#
# STRUCTURAL NOTE 2. ``copy "slwssoi.cob"`` [:L280] declares ``01 si-header.``
# - a SECOND, INDEPENDENT 118 bytes with the same layout under ``si-*`` names
# [copybooks/slwssoi.cob:L9-L57]. It is a save area: [:L851] saves and [:L913]
# restores, bracketing ba000-CR-Notes. No records/ module publishes it, and the
# migration's file inventory does not admit a new one, so it is realised as a
# second :class:`OiHeader` instance and the group moves are reproduced by
# :func:`_group_move_oi_header`. The ``si-*`` name of each field is given at
# every use site.
#
# STRUCTURAL NOTE 3. ``05 si-approp redefines si-net`` [copybooks/slwssoi.cob:
# L39-L40], and likewise ``oi-approp`` in the sales layout, is a second name for
# the net amount. This program never references either, so the two names cannot
# drift observably; the leaf walk below carries both.
# ---------------------------------------------------------------------------


def _dataclass_leaves(
    record_class: type, prefix: tuple[str, ...] = ()
) -> tuple[tuple[tuple[str, ...], type, str], ...]:
    """Every elementary item of a layout, as ``(path, owner class, name)``.

    Groups are walked, not returned: a COBOL group item has no value of its own.
    :func:`typing.get_type_hints` is what resolves the string annotations the
    record modules produce under ``from __future__ import annotations``.
    """
    leaves: list[tuple[tuple[str, ...], type, str]] = []
    hints = typing.get_type_hints(record_class)
    for member in dataclasses.fields(record_class):
        annotated = hints.get(member.name)
        if isinstance(annotated, type) and dataclasses.is_dataclass(annotated):
            leaves.extend(_dataclass_leaves(annotated, prefix + (member.name,)))
        else:
            leaves.append((prefix + (member.name,), record_class, member.name))
    return tuple(leaves)


#: The 28 elementary items of the open-item header [copybooks/slwsoi.cob:L9-L56].
_OI_HEADER_LEAVES: Final[tuple[tuple[tuple[str, ...], type, str], ...]] = _dataclass_leaves(
    OiHeader
)


def _initial_oi_header() -> OiHeader:
    """A header at its figurative initial value: spaces for text, zero for numbers.

    ``01 WS-OTM3-Record pic x(118).`` [copybooks/slwsoi3.cob:L9] carries no
    ``VALUE`` clause, so what the storage holds before its first use is the
    compiler's working-storage fill and NOT something the program relies on:
    every path either group-moves 118 bytes into it [sales/sl060.cbl:L487] or
    has the file handler fill it [:L662, :L867] before any field is read. The
    figuratives come from :mod:`acas_posting.cobol.move` against each field's
    own descriptor, so no width or scale is decided here.
    """

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

    A group ``MOVE`` between two identically described 118-byte areas copies
    the bytes and converts nothing, so every elementary item is carried across
    unchanged. The target is updated IN PLACE, because the COBOL storage's
    identity is stable and the file handler holds the same area across calls.
    """
    for path, _owner, name in _OI_HEADER_LEAVES:
        from_group: object = source
        into_group: object = target
        for step in path[:-1]:
            from_group = getattr(from_group, step)
            into_group = getattr(into_group, step)
        setattr(into_group, name, getattr(from_group, name))


# ---------------------------------------------------------------------------
# The program's storage, as one object
#
# The facade's dispatch paragraphs name the program's own record areas - for
# example ``call "acas019" using System-Record WS-OTM3-Record File-Access
# File-Defs ACAS-DAL-Common-Data`` [copybooks/Proc-ACAS-FH-Calls.cob:L132-L138]
# - and take no parameters, because a COBOL sub-program sees the caller's
# storage. AAP section 0.4.3 renders ``perform GL-Batch-Read-Next`` as
# ``facade.gl_batch_read_next(ctx)``, so this class IS that ctx: one object whose
# attribute names are those COBOL identifiers in snake case.
# ---------------------------------------------------------------------------


@dataclasses.dataclass(slots=True)
class _Sl060State:
    """Everything ``sl060`` can see: its linkage, its record areas, its storage."""

    # --- PROCEDURE DIVISION USING, [sales/sl060.cbl:L395-L399] ---------------
    ws_calling_data: WsCallingData
    system_record: SystemRecord
    system_record_4: SystemRecord4
    to_day: str
    file_defs: FileDefs

    # --- the record areas the facade dispatch paragraphs name ---------------
    #: ``copy "wssl.cob"`` [:L275] - acas012 [copybooks/Proc-ACAS-FH-Calls.cob:L82-L88].
    ws_sales_record: WsSalesRecord
    #: ``copy "wsval.cob"`` [:L274] - acas013
    #: [copybooks/Proc-ACAS-FH-Calls.cob:L90-L96].
    ws_value_record: WsValueRecord
    #: ``copy "wsbatch.cob"`` [:L276] - acas007
    #: [copybooks/Proc-ACAS-FH-Calls.cob:L51-L57].
    ws_batch_record: GlBatchRecord
    #: ``copy "wspost.cob"`` [:L277] - acas006
    #: [copybooks/Proc-ACAS-FH-Calls.cob:L43-L49].
    ws_posting_record: WsPostingRecord
    #: ``copy "wspost-irs.cob"`` [:L278] - acas008
    #: [copybooks/Proc-ACAS-FH-Calls.cob:L59-L65].
    ws_irs_posting_record: WsIrsPostingRecord
    #: ``copy "slwsoi3.cob"`` [:L279] - acas019
    #: [copybooks/Proc-ACAS-FH-Calls.cob:L132-L138]. THIS IS ALSO
    #: ``oi-header`` and ``open-item-record-3``; see STRUCTURAL NOTE 1.
    ws_otm3_record: OiHeader
    #: ``copy "wsfnctn.cob"`` [:L194].
    file_access: FileAccess
    #: ``copy "Test-Data-Flags.cob"`` [:L270].
    acas_dal_common_data: AcasDalCommonData

    # --- date storage -------------------------------------------------------
    #: ``copy "wsmaps03.cob"`` [:L193] - the linkage block ``maps04`` converts.
    maps03_ws: Maps03Ws
    #: ``01 ws-Test-Date`` [:L235] and ``01 ws-date-formats`` [:L236-L257].
    ws_date_formats: dates.WsDateFormats

    # --- the OTM2 work sequence and the saved header ------------------------
    #: ``select open-item-file-2 assign file-18 ... organization sequential``
    #: [copybooks/seloi2.cob], record ``open-item-record-2 pic x(118)``
    #: [copybooks/fdoi2.cob]. It reaches NO schema table; see STRUCTURAL NOTE 4.
    open_item_file_2: LineSequentialWorkFile[OiHeader]
    #: ``01 si-header.`` [copybooks/slwssoi.cob:L9]; see STRUCTURAL NOTE 2.
    si_header: OiHeader

    # --- WORKING-STORAGE, [:L196-L233] --------------------------------------
    ws_reply: str = " "  # [:L197]
    ws_error: int = 0  # [:L198]
    wx_reply: str = "   "  # [:L200] - commented-out dialogue only
    xx: int = 0  # [:L201]
    c_check: int = 0  # [:L202] - never referenced
    ws_eval_msg: str = " " * 25  # [:L204]
    work_1: Decimal = Decimal("0.00")  # [:L205]
    work_2: int = 0  # [:L206] - SCALE 0; see ANOMALY A-8
    work_a: Decimal = Decimal("0.00")  # [:L207]
    work_b: Decimal = Decimal("0.00")  # [:L208]
    first_pass: str = " "  # [:L209]
    i: int = 0  # [:L210]
    j: int = 0  # [:L211]
    k: int = 0  # [:L212]
    m: str = " " * 8  # [:L213] - pic z(7)9, edited
    b: int = 0  # [:L214]
    c: int = 0  # [:L215]
    work_net: Decimal = Decimal("0.00")  # [:L216]
    work_vat: Decimal = Decimal("0.00")  # [:L217]
    work_goods: Decimal = Decimal("0.00")  # [:L218] - SCALE 2; see ANOMALY A-8
    #: ``03 total-group occurs 3`` [:L219] with ``05 total-net`` [:L220] and
    #: ``05 total-vat`` [:L221]. Three occurrences, one list each, 1-based in
    #: the COBOL and therefore offset by one here - left in the open on purpose,
    #: because a hidden offset is how an off-by-one enters a posting.
    total_net: list[Decimal] = dataclasses.field(
        default_factory=lambda: [Decimal("0.00")] * 3
    )
    total_vat: list[Decimal] = dataclasses.field(
        default_factory=lambda: [Decimal("0.00")] * 3
    )
    a: int = 0  # [:L222] - FINDING 8(a), the unchecked subscript
    line_cnt: int = 0  # [:L223]
    ws_deduction: Decimal = Decimal("0.00")  # [:L224]
    total_deduct: Decimal = Decimal("0.00")  # [:L225]
    total_mov_ded: int = 0  # [:L226]
    save_level_1: int = 0  # [:L227] - commented-out bypass only
    file_18_status: int = 0  # [:L231]
    error_code: int = 0  # [:L272] - never referenced

    @property
    def oi_header(self) -> OiHeader:
        """``oi-header`` - the SAME storage as ``ws_otm3_record``.

        ``OI-Header redefines WS-OTM3-Record`` [copybooks/slwsoi3.cob:L18-L19].
        One object, two COBOL names; see STRUCTURAL NOTE 1.
        """
        return self.ws_otm3_record

    def ctx(self, record: object) -> facade.FacadeContext:
        """The five operands one facade ``PERFORM`` passes, for ``record``'s entity.

        Every dispatch paragraph in ``Proc-ACAS-FH-Calls.cob`` passes the same
        five things and varies only the second - the entity work area - e.g.::

            acas012.  move 1 to File-Key-No.
                      call "acas012" using System-Record WS-Sales-Record
                           File-Access File-Defs ACAS-DAL-Common-Data.
                                    [copybooks/Proc-ACAS-FH-Calls.cob:L82-L88]

        so the record area is named at the CALL SITE, one per verb, exactly as
        the copybook names it. The six this program performs against are
        ``WS-Sales-Record`` (acas012, L82-L88), ``WS-Value-Record`` (acas013,
        L90-L96), ``WS-Batch-Record`` (acas007, L51-L57), ``WS-Posting-Record``
        (acas006, L43-L49), ``WS-IRS-Posting-Record`` (acas008, L59-L65) and
        ``WS-OTM3-Record`` (acas019, L132-L138).

        ``file_access`` is passed by reference, so the verb writes ``Fs-Reply``
        and ``We-Error`` into the block this state already holds - the status
        protocol of [copybooks/wsfnctn.cob:L23-L38] - and every inline reply test
        after a ``PERFORM`` reads the block, never a return value.
        """
        return facade.FacadeContext(
            self.system_record,
            record,
            self.file_access,
            self.file_defs,
            self.acas_dal_common_data,
        )


def _new_state(
    ws_calling_data: WsCallingData,
    system_record: SystemRecord,
    system_record_4: SystemRecord4,
    to_day: str,
    file_defs: FileDefs,
) -> _Sl060State:
    """Bind the linkage and give every record area its declared initial value."""
    return _Sl060State(
        ws_calling_data=ws_calling_data,
        system_record=system_record,
        system_record_4=system_record_4,
        to_day=to_day,
        file_defs=file_defs,
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
        open_item_file_2=LineSequentialWorkFile(
            file_defs.file_defs_a.file_18, OiHeader
        ),
        si_header=_initial_oi_header(),
    )


# ---------------------------------------------------------------------------
# The one place the two turnover declarations are reconciled
# ---------------------------------------------------------------------------

#: ``05 Turnover-Q1`` through ``Turnover-Q4`` [copybooks/wssl.cob], the
#: declaration the data-access layer persists as four columns.
_TURNOVER_QUARTER_FIELDS: Final[tuple[str, str, str, str]] = (
    "turnover_q1",
    "turnover_q2",
    "turnover_q3",
    "turnover_q4",
)


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
    field anomaly A-3 concerns in ``gl080``. R-3 forbids adding the check the
    COBOL does not have, so none is added; AMBIGUITY Q-4 records that the
    reachable range must be established against the oracle, because a quarter
    of zero or five does not fail here the way it does not fail there - it
    simply does something else.
    """
    quarter = state.system_record.system_data_block.current_quarter
    occurrence = quarter - 1  # COBOL subscripts are 1-based
    receiving = _SALES["sturnover-q"]
    view = state.ws_sales_record.quarters_view
    updated = arithmetic.add_to(
        addend, receiver_value=view.sturnover_q[occurrence], receiving=receiving
    )
    quarters = list(view.sturnover_q)
    quarters[occurrence] = updated
    view.sturnover_q = tuple(quarters)
    setattr(state.ws_sales_record.quarters, _TURNOVER_QUARTER_FIELDS[occurrence], updated)



#: Every elementary item of the sales-ledger record, with its descriptor - the
#: operand list of ``initialize WS-Sales-Record with filler`` [:L497].
_SALES_LEAVES: Final[tuple[tuple[tuple[str, ...], FieldDescriptor], ...]] = tuple(
    (path, sales_ledger.FIELD_DESCRIPTORS[".".join(path)])
    for path, _owner, _name in _dataclass_leaves(WsSalesRecord)
)


def _initialize_ws_sales_record(state: _Sl060State) -> None:
    """``initialize WS-Sales-Record with filler`` [sales/sl060.cbl:L497].

    ``INITIALIZE`` with no ``REPLACING`` phrase sets every elementary item to
    its category's figurative value - numeric items to ZERO, alphanumeric items
    to SPACES - and ``WITH FILLER`` extends that to the ``FILLER`` items an
    ordinary ``INITIALIZE`` would leave alone. This record has two of them,
    ``filler`` at [copybooks/wssl.cob:L40] and [copybooks/wssl.cob:L68], so the phrase is not
    decoration.

    Both figuratives go through the published multi-receiver primitive, which
    converts once PER RECEIVER rather than reusing one converted value - so a
    ``pic 9(8) comp-3`` and a ``pic x(30)`` in the same statement each get what
    their own description demands. The subscripted turnover view is set through
    :func:`_add_to_turnover_quarter`'s sibling declaration as well, for the
    reason given in STRUCTURAL NOTE 5.
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

    # STRUCTURAL NOTE 5 again: the four named quarters and the OCCURS 4 view
    # describe the same 24 bytes, and clearing one must clear the other.
    for quarter_field in _TURNOVER_QUARTER_FIELDS:
        setattr(
            state.ws_sales_record.quarters,
            quarter_field,
            move.move_figurative(move.ZERO, _SALES[quarter_field.replace("_", "-")]),
        )


def _oi_customer_image(header: OiHeader) -> str:
    """The seven-byte sending image of the ``oi-customer`` GROUP.

    ``03 oi-customer.`` is ``05 oi-nos pic x(6)`` plus ``05 oi-check pic 9``
    [copybooks/slwsoi.cob:L11-L13], so a group MOVE or a group comparison sees
    six characters followed by one zoned digit. The digit's byte image comes
    from an alphanumeric move that names the sending numeric field, so the
    zoning is the published primitive's business and not this module's.
    """
    check_digit = move.move_alphanumeric(
        header.oi_key.oi_customer.oi_check,
        _OI_CHECK_AS_TEXT,
        sending_field=otm3.descriptor_for(type(header.oi_key.oi_customer), "oi_check"),
    )
    return f"{header.oi_key.oi_customer.oi_nos}{check_digit}"


#: A one-character alphanumeric receiver, used only to take the zoned image of
#: ``oi-check pic 9`` [copybooks/slwsoi.cob:L13] when the enclosing GROUP is
#: moved or compared as seven bytes.
_OI_CHECK_AS_TEXT: Final[FieldDescriptor] = descriptor_for(
    "pic x",
    name="oi-check-as-text",
    source_locator="copybooks/slwsoi.cob:L13",
    level="05",
)


def _write_oi3_customer(state: _Sl060State, image: str) -> None:
    """Store seven bytes into ``oi3-customer`` [copybooks/slwsoi3.cob:L13].

    ``oi3-customer pic x(7)`` occupies the same seven bytes as the
    ``oi-customer`` group, so a move into it lands in ``oi-nos`` and
    ``oi-check``; see STRUCTURAL NOTE 1. The split is by reference modification,
    1-based, through the published primitive - never by Python slicing.
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


# ===========================================================================
# PROCEDURE DIVISION
# ===========================================================================


def run(
    ws_calling_data: WsCallingData,
    system_record: SystemRecord,
    system_record_4: SystemRecord4,
    to_day: str,
    file_defs: FileDefs,
) -> None:
    """Post the sales invoice extract: ``sl060``'s two phases, in order.

    The parameter list is [sales/sl060.cbl:L395-L399] exactly - five parameters,
    the third being ``system-record-4`` from ``copy "wssys4.cob"`` [:L393].

    Args:
        ws_calling_data: ``WS-Calling-Data`` [copybooks/wscall.cob:L6-L13]. The
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

    Returns:
        None. ``sl060`` reports nothing back through its linkage: it has no
        ``WS-Term-Code`` store of its own, so the caller's gate
        [sales/sales.cbl:L759-L768] sees whatever the previous program left.

    Raises:
        _CobolLibraryRoutineUnavailable: if a ``CBL_...`` gate is entered, which
            requires ``FS-Cobol-Files-Used`` to be true. See R-1.
    """
    state = _new_state(ws_calling_data, system_record, system_record_4, to_day, file_defs)
    _aa000_main_process(state)


# ---------------------------------------------------------------------------
# aa000-Main-Process section.                        [sales/sl060.cbl:L402]
# ---------------------------------------------------------------------------


def _aa000_main_process(state: _Sl060State) -> None:
    """``aa000-Main-Process section.`` [sales/sl060.cbl:L402] - open and set up.

    Ends by FALLING THROUGH into ``aa020-Read-Loop`` [:L483], which is the next
    label in the section, so the chain of paragraph functions below runs exactly
    as the straight-line COBOL does.
    """
    system = state.system_record

    # [:L403-L409] accept ws-env-lines from lines / geometry arithmetic.
    # OMITTED: terminal geometry, and NOT a clock read (R-6). ws-env-lines
    # [:L228], ws-lines [:L229] and ws-23-lines [:L230] are consumed only by the
    # screen section, which is out of scope.

    # [:L410] move prog-name to l1-name. OMITTED - print heading field.
    # [:L411] perform zz070-Convert-Date. KEPT: it stores ws-date and may
    # default Date-Form in the system record.
    _zz070_convert_date(state)
    # [:L412] move ws-date to l1-date. OMITTED - print heading field.
    # [:L413] move Print-Spool-Name to PSN. OMITTED with the spool-out path.

    # [:L415-L416] set ENVIRONMENT "COB_SCREEN_EXCEPTIONS"/"COB_SCREEN_ESC".
    # OMITTED: curses configuration for a screen section that is out of scope.

    # [:L418-L419] display prog-name / "Invoice Posting & Report".
    _LOG.info("%s Invoice Posting & Report", _PROG_NAME)
    # [:L420] perform zz070-Convert-Date. The SECOND call, four lines after the
    # first; both are reproduced because both are written.
    _zz070_convert_date(state)
    # [:L421] display ws-date.
    _LOG.info("%s", state.ws_date_formats.ws_date)

    # [:L422] move 1 to File-Key-No. Redundant against the facade's own dispatch
    # paragraphs, every one of which sets it [copybooks/Proc-ACAS-FH-Calls.cob:
    # L44], but written here and therefore reproduced (R-3, R-4).
    state.file_access.logging_data.file_key_no = move.move_numeric(
        1, _ACCESS["file-key-no"]
    )

    # [:L424-L431] aa010-Acpt-Xrply - the whole confirmation dialogue is
    # COMMENTED OUT in the frozen source, with the maintainer's reason: "All
    # omitted 18/01/25 as pointless and possibly dangerous" [:L125-L127],
    # because sl055 has already run. Nothing to reproduce; wx-reply [:L200] is
    # its only storage and stays unreferenced.

    # [:L433] display space at 0801 with erase eol. Screen clear only.

    # [:L434] move 2 to S-Flag-I.  *> invoice lines
    system.sales_ledger_block.s_flag_i = move.move_numeric(2, _SYSTEM["s-flag-i"])
    # [:L435] move 1 to S-Flag-A.  *> Applied recs
    system.sales_ledger_block.s_flag_a = move.move_numeric(1, _SYSTEM["s-flag-a"])
    # [:L436] move "Y" to oi-3-flag.  *> sets changes to file so sl115 sort needed.
    system.sales_ledger_block.oi_3_flag = move.move_alphanumeric(
        "Y", _SYSTEM["oi-3-flag"]
    )

    # [:L437-L444] R-1 GATE 1 of 4.
    if _IS_FS_COBOL_FILES_USED(system.system_data_block.rdbms_flat_statuses.file_system_used):
        # [:L438-L439] call "CBL_CHECK_FILE_EXIST" using File-19 File-Info.
        # The two facade verbs at [:L441-L442] - OTM3-Open-Output and
        # OTM3-Close, which would CREATE the OTM3 file when the check says it is
        # absent - are legitimate Python calls, but they are reached only when
        # this gate is true, so the whole block is unreachable in the RDBMS
        # configuration and the CALL that decides it cannot be honoured.
        raise _CobolLibraryRoutineUnavailable(
            "CBL_CHECK_FILE_EXIST", f"{_PROGRAM}:L438", "File-19 File-Info"
        )

    # [:L446] The maintainer's own note: "File-18 settings used elsewhere in
    # program but file IS created in sl055 so a bit pointless .."
    # [:L448-L456] R-1 GATE 2 of 4.
    if _IS_FS_COBOL_FILES_USED(system.system_data_block.rdbms_flat_statuses.file_system_used):
        # [:L449-L450] call "CBL_CHECK_FILE_EXIST" using File-18 File-Info,
        # then [:L452] set File-18-Not-Exists / [:L454] set File-18-Exists.
        raise _CobolLibraryRoutineUnavailable(
            "CBL_CHECK_FILE_EXIST", f"{_PROGRAM}:L449", "File-18 File-Info"
        )

    # [:L458-L464] A COMMENTED-OUT bypass that would save Level-1 and set it to
    # zero, suppressing the General Ledger for this run. Not reproduced because
    # it is not compiled; save-level-1 [:L227] is its only storage.

    # [:L466-L467] if G-L perform ca000-BL-Open.
    # THE GATING IS LAYERED. Only the General Ledger switch opens the batch
    # here; ca000-BL-Open then tests the IRS flags again internally [:L1039,
    # :L1046]. In IRS-only mode this section is never entered, so no batch and
    # no posting file of either kind is opened - and ca000-BL-Write, gated the
    # same way at [:L535], never runs either.
    if _IS_G_L(system.system_data_block.level.level_1):
        _ca000_bl_open(state)

    # [:L469] perform Sales-Open.
    facade.sales_open(state.ctx(state.ws_sales_record))
    # [:L470] open output print-file. OMITTED with the print file.

    # [:L471-L472] display "Posting......Please Wait" / the phase-1 banner.
    _LOG.info("Posting......Please Wait")
    _LOG.info("Phase 1 - Building OTM3 from OTM2")

    # [:L474] move zero to j.
    state.j = move.move_figurative(move.ZERO, _J)
    # [:L475] perform ba000-Headings.
    _ba000_headings(state)

    # [:L477] move zeros to total-net (1) total-net (2) total-net (3).
    # [:L478] move zeros to total-vat (1) total-vat (2) total-vat (3).
    # Written with EXPLICIT SUBSCRIPTS, one receiver per occurrence, rather than
    # as a group move over the table; reproduced the same way.
    state.total_net = list(
        move.move_to_all(move.ZERO, (_TOTAL_NET, _TOTAL_NET, _TOTAL_NET))
    )
    state.total_vat = list(
        move.move_to_all(move.ZERO, (_TOTAL_VAT, _TOTAL_VAT, _TOTAL_VAT))
    )

    # [:L480] open input open-item-file-2. A DIRECT file verb, not a facade
    # verb: the OTM2 sequence is a work file and has no handler.
    state.open_item_file_2.open_input()
    # [:L481] perform OTM3-Open.
    facade.otm3_open(state.ctx(state.ws_otm3_record))

    # FALL-THROUGH into aa020-Read-Loop. [:L483] is the next label in the
    # section and no transfer precedes it.
    _aa020_read_loop(state)


# ---------------------------------------------------------------------------
# aa020-Read-Loop.                                   [sales/sl060.cbl:L483]
# ---------------------------------------------------------------------------


def _aa020_read_loop(state: _Sl060State) -> None:
    """``aa020-Read-Loop.`` [sales/sl060.cbl:L483] - phase 1, the posting loop.

    One iteration per OTM2 header: read it, find the customer, accumulate the
    report totals, post to the General Ledger if it is in use, update the
    sales-ledger row, write the OTM3 open item.

    The loop's two transfers are [:L485] to ``aa030-Main-End`` (class 2, the
    only way out) and [:L610] back to here (class 1, the unconditional
    tail).
    """
    system = state.system_record

    while True:
        # [:L484] read open-item-file-2 at end
        header = state.open_item_file_2.read_next()
        if header is None:
            # GO TO class 2 [sales/sl060.cbl:L485] -> aa030-Main-End. The only
            # exit; the post-loop block follows the loop, below.
            break

        # [:L487] move open-item-record-2 to oi-header. A GROUP MOVE of the
        # whole 118-byte record; see STRUCTURAL NOTE 1 for why it lands in the
        # same storage the file handler uses.
        _group_move_oi_header(header, state.oi_header)

        oi = state.oi_header
        key = oi.oi_key
        body = oi.filler_1
        money = body.filler_2
        sales = state.ws_sales_record

        # [:L489] move oi-customer to WS-Sales-Key l5-cust. TWO receivers; the
        # second is a print field and is omitted.
        sales.ws_sales_key = move.move_alphanumeric(
            _oi_customer_image(oi), _SALES["ws-sales-key"]
        )
        # [:L490] move space to ws-reply.
        state.ws_reply = move.move_figurative(move.SPACE, _WS_REPLY)
        # [:L491] perform Sales-Read-Indexed
        facade.sales_read_indexed(state.ctx(state.ws_sales_record))
        # [:L492-L493] if fs-reply = 21 move "X" to ws-reply.
        # 21 is what the handlers return for "no such record" after an indexed
        # read; the published vocabulary spells that value INVALID_KEY_ON_START
        # after the other verb that produces it. The VALUE is what the COBOL
        # tests, and naming it is what keeps a bare 21 out of this file.
        if state.file_access.fs_reply == FsReply.INVALID_KEY_ON_START:
            state.ws_reply = move.move_alphanumeric("X", _WS_REPLY)

        # [:L495-L501]
        if state.ws_reply == "X":
            # [:L496] move 1 to ws-error. Sets 88 sales-missing [:L199].
            state.ws_error = move.move_numeric(1, _WS_ERROR)
            # [:L497] initialize WS-Sales-Record with filler.
            _initialize_ws_sales_record(state)
            # [:L498] move "*** Customer Unknown ***" to l5-name sales-name.
            # The print receiver is omitted; SALES-NAME IS A TABLE COLUMN and
            # this text is what a rewrite would store - except that [:L579-L581]
            # writes rather than rewrites in exactly this case.
            sales.sales_name = move.move_alphanumeric(
                "*** Customer Unknown ***", _SALES["sales-name"]
            )
            # [:L499] move oi-customer to WS-Sales-Key. The SECOND time, after
            # the INITIALIZE cleared what [:L489] put there.
            sales.ws_sales_key = move.move_alphanumeric(
                _oi_customer_image(oi), _SALES["ws-sales-key"]
            )
        else:
            # [:L501] move sales-name to l5-name. Print only.
            pass

        # [:L503] move oi-invoice to l5-nos. Print only.

        # [:L505] move oi-date to u-bin.
        state.maps03_ws.u_bin = move.move_numeric(body.oi_date, _MAPS03["u-bin"])
        # [:L506] perform zz060-Convert-Date.
        _zz060_convert_date(state)
        # [:L507] move ws-date to l5-date. Print only.

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
        # storage silently; the two Python artefacts of the same unchecked
        # subscript are stated here rather than guarded, because R-3 forbids the
        # check and the checklist forbids it AT THESE EXACT SITES:
        #   a >= 4  -> `IndexError` from the list subscript. This is Python's
        #              own consequence of an out-of-range index, not a check
        #              this module added.
        #   a  = 0  -> index -1, which Python resolves to the LAST occurrence.
        #              The add lands on `total-*(3)` instead of on the storage
        #              before the table. That is a migration artefact, and it is
        #              the one case where the unchecked subscript is silently
        #              WRONG rather than loudly so.
        # Neither artefact matches COBOL, because COBOL's behaviour here is
        # undefined; what the compiled program stores is the specification, and
        # Q-1 is open until the oracle establishes the reachable range. Both
        # totals are print-only accumulators [:L616-L636], so no table column
        # depends on this - which is why the divergence is recorded rather than
        # resolved by inventing a semantic.
        state.a = move.move_numeric(body.oi_type, _A)

        # [:L511-L518] A three-deep nested if selecting the report's type text.
        # OMITTED: every receiver is a print field and no branch has another
        # effect.

        # [:L520] add oi-vat oi-c-vat oi-e-vat oi-deduct-vat giving work-vat.
        # FOUR addends, summed at intermediate precision and quantized ONCE.
        state.work_vat = arithmetic.add_giving(
            money.oi_vat,
            money.oi_c_vat,
            money.oi_e_vat,
            body.oi_deduct_vat,
            receiving=_WORK_VAT,
        )
        # [:L521] add oi-net oi-extra giving work-goods.
        state.work_goods = arithmetic.add_giving(
            money.oi_net, money.oi_extra, receiving=_WORK_GOODS
        )
        # [:L522] move work-vat to l5-vat. Print only.
        # [:L523] add oi-net oi-extra oi-carriage oi-discount oi-deduct-amt
        #         giving work-net. FIVE addends.
        state.work_net = arithmetic.add_giving(
            money.oi_net,
            money.oi_extra,
            money.oi_carriage,
            money.oi_discount,
            body.oi_deduct_amt,
            receiving=_WORK_NET,
        )
        # [:L524] move work-net to l5-net. Print only.

        # [:L526] add work-vat to total-vat (a).
        # [:L527] add work-net to total-net (a).
        # FINDING 8(a) again: both subscripted by `a`, unchecked.
        state.total_vat[state.a - 1] = arithmetic.add_to(
            state.work_vat,
            receiver_value=state.total_vat[state.a - 1],
            receiving=_TOTAL_VAT,
        )
        state.total_net[state.a - 1] = arithmetic.add_to(
            state.work_net,
            receiver_value=state.total_net[state.a - 1],
            receiving=_TOTAL_NET,
        )

        # [:L529] move work-net to work-1.
        state.work_1 = move.move_numeric(state.work_net, _WORK_1)
        # [:L530] add work-vat to work-1.
        state.work_1 = arithmetic.add_to(
            state.work_vat, receiver_value=state.work_1, receiving=_WORK_1
        )
        # [:L531] move work-1 to l5-gross. Print only.

        # [:L533] move zero to l5-deduction ws-deduction. Two receivers; the
        # first is a print field.
        state.ws_deduction = move.move_figurative(move.ZERO, _WS_DEDUCTION)

        # [:L535-L536] if G-L perform ca000-BL-Write.
        if _IS_G_L(system.system_data_block.level.level_1):
            _ca000_bl_write(state)

        # [:L538] subtract sales-unapplied from sales-current giving l5-old-bal.
        # OMITTED: the receiver is a print field and neither operand changes.

        # [:L539-L540] if oi-type = 1 or 2 perform ba000-Sales-Comp.
        # An ABBREVIATED RELATION: oi-type = 1 OR oi-type = 2.
        if body.oi_type == 1 or body.oi_type == 2:
            _ba000_sales_comp(state)

        # [:L544-L562] THREE INDEPENDENT `if`s on oi-type, mutually exclusive by
        # value but written separately and differing in more than the test:
        # type 1 sets BOTH date fields and does not touch sales-current; type 2
        # sets one date and adds to sales-current; type 3 sets the other date,
        # adds to sales-current, and performs two further sections. Not merged,
        # not reordered (R-3, R-4).

        # [:L544-L546]
        if body.oi_type == 1:
            # [:L545] add work-goods to STurnover-Q (current-quarter).
            _add_to_turnover_quarter(state, state.work_goods)
            # [:L546] move oi-date to sales-last-inv sales-last-pay. BOTH.
            (sales.sales_last_inv, sales.sales_last_pay) = move.move_to_all(
                body.oi_date,
                (_SALES["sales-last-inv"], _SALES["sales-last-pay"]),
                sending_field=otm3.descriptor_for(type(body), "oi_date"),
            )

        # [:L550-L553]
        if body.oi_type == 2:
            # [:L551] add work-goods to STurnover-Q (current-quarter).
            _add_to_turnover_quarter(state, state.work_goods)
            # [:L552] add work-vat work-net to sales-current. TWO SOURCES, ONE
            # RECEIVER - not two statements.
            sales.sales_current = arithmetic.add_to(
                state.work_vat,
                state.work_net,
                receiver_value=sales.sales_current,
                receiving=_SALES["sales-current"],
            )
            # [:L553] move oi-date to sales-last-inv.
            sales.sales_last_inv = move.move_numeric(
                body.oi_date, _SALES["sales-last-inv"]
            )

        # [:L557-L562]
        if body.oi_type == 3:
            # [:L558] add work-goods to STurnover-Q (current-quarter).
            _add_to_turnover_quarter(state, state.work_goods)
            # [:L559] add work-vat work-net to sales-current.
            sales.sales_current = arithmetic.add_to(
                state.work_vat,
                state.work_net,
                receiver_value=sales.sales_current,
                receiving=_SALES["sales-current"],
            )
            # [:L560] move oi-date to sales-last-pay.
            sales.sales_last_pay = move.move_numeric(
                body.oi_date, _SALES["sales-last-pay"]
            )
            # [:L561] perform ba000-CR-Notes.
            _ba000_cr_notes(state)
            # [:L562] perform ba000-Credit-Comp.
            _ba000_credit_comp(state)

        # [:L564] move ws-deduction to l5-deduction. Print only.
        # [:L565] add ws-deduction to total-deduct.
        state.total_deduct = arithmetic.add_to(
            state.ws_deduction, receiver_value=state.total_deduct, receiving=_TOTAL_DEDUCT
        )

        # [:L567-L568] if customer-dead move 1 to sales-status.
        # `88 Customer-Dead value zero` on Sales-Status [copybooks/wssl.cob:L27],
        # so a dead customer is REVIVED to status 1 by being posted to.
        if _IS_CUSTOMER_DEAD(sales.sales_status):
            sales.sales_status = move.move_numeric(1, _SALES["sales-status"])

        # [:L570-L573] The sign flip, and all three statements are ONE `if` body
        # (the period is at L573).
        if arithmetic.compare(sales.sales_current, 0) < 0:
            # [:L571] multiply -1 by sales-current.
            # The NO-GIVING form: the RECEIVER IS SECOND, so this is
            # sales-current = -1 * sales-current, leaving it POSITIVE.
            sales.sales_current = arithmetic.multiply_by(
                -1, sales.sales_current, _SALES["sales-current"]
            )
            # [:L572] add sales-current to sales-unapplied. The now-POSITIVE
            # value; the order of these three statements is load-bearing.
            sales.sales_unapplied = arithmetic.add_to(
                sales.sales_current,
                receiver_value=sales.sales_unapplied,
                receiving=_SALES["sales-unapplied"],
            )
            # [:L573] move zero to sales-current.
            sales.sales_current = move.move_figurative(
                move.ZERO, _SALES["sales-current"]
            )

        # [:L578] subtract sales-unapplied from sales-current giving l5-new-bal.
        # OMITTED: print receiver.

        # [:L579-L583] The maintainer's own comment on L579 reads "shouldnt
        # happen (No sales rec found) but JIC".
        if state.ws_reply == "X":
            # [:L580] move 1 to sales-status.
            sales.sales_status = move.move_numeric(1, _SALES["sales-status"])
            # [:L581] perform Sales-Write. A NEW ledger row, from the record
            # that [:L497] initialized and [:L498] named "Customer Unknown".
            facade.sales_write(state.ctx(state.ws_sales_record))
        else:
            # [:L583] perform Sales-Rewrite.
            facade.sales_rewrite(state.ctx(state.ws_sales_record))

        # [:L585] move OI-Header to WS-OTM3-Record. COMMENTED OUT in the frozen
        # source, with the maintainer's reason "*> is redefines" - they are the
        # same storage. Nothing to reproduce; see STRUCTURAL NOTE 1.
        # [:L586] perform OTM3-Write.
        facade.otm3_write(state.ctx(state.ws_otm3_record))

        # [:L590-L601] The write-failure diagnostic. It TRANSFERS NO CONTROL:
        # there is no retry, no abort and no counter, so a failed OTM3 write
        # leaves the sales-ledger row already written and the open item not
        # written, and the loop simply continues. The commented-out [:L603-L604]
        # shows the maintainer once had `perform OTM3-Rewrite` and `stop run`
        # here. R-3 forbids restoring either.
        # AMBIGUITY Q-3 [sales/sl060.cbl:L590] - THE DISPOSITION OF A FAILED
        # OTM3-Write. This is a rejection class with a PARTIAL DATABASE EFFECT:
        # SALEDGER-REC has already been written or rewritten at [:L581]/[:L583]
        # and, if `G-L`, a GLPOSTING-REC row and possibly a PSIRSPOST-REC row
        # were written at [:L536], while SAITM3-REC gets nothing. Exactly which
        # rows survive, and whether the batch's control totals still include the
        # invoice, must be measured against the compiled oracle. Paired with
        # AMBIGUITY Q-8 for the GL-Batch-Write failure at [:L1162].
        if state.file_access.fs_reply != FsReply.SUCCESS:
            # [:L593] move oi3-invoice to l5-nos. Print-only; omitted with the
            # print line it feeds.
            # [:L597] perform zz040-Evaluate-Message.
            _zz040_evaluate_message(state)
            _LOG.error(
                "%s customer=%s invoice=%s fs-reply = %02d %s",  # [:L591-L599]
                _SL130,
                _oi_customer_image(oi),
                key.oi_invoice,
                state.file_access.fs_reply,
                state.ws_eval_msg,
            )
            # [:L600-L601] if WS-Caller not = "xl150" accept ws-reply at 2455.
            # The PROMPT is dropped - it only blocks a terminal - but the
            # unattended-mode test around it is the codebase's own and is kept.
            if state.ws_calling_data.ws_caller.strip() != "xl150":
                _LOG.error("%s", _SL002)

        # [:L606] write print-record from line-5 after 1. OMITTED with the print
        # file; the counter it feeds is not, because [:L608] branches on it.
        # [:L607] add 1 to line-cnt.
        state.line_cnt = arithmetic.add_to(
            1, receiver_value=state.line_cnt, receiving=_LINE_CNT
        )
        # [:L608-L609] if line-cnt > Page-Lines perform ba000-Headings.
        if (
            arithmetic.compare(state.line_cnt, system.system_data_block.page_lines)
            > 0
        ):
            _ba000_headings(state)

        # GO TO class 1 [sales/sl060.cbl:L610] -> aa020-Read-Loop.
        continue

    # The post-loop block for the class-2 transfer at [:L485]. Placing it here
    # rather than treating the break as the end of the work is what AAP
    # section 0.6.3 requires: "the transformation is `break` PLUS faithful
    # placement of that work after the loop, not `break` alone. Mis-splitting
    # here would silently drop end-of-run processing." Here that work includes
    # BOTH remaining period-total writes.
    _aa030_main_end(state)



# ---------------------------------------------------------------------------
# aa030-Main-End.                                    [sales/sl060.cbl:L612]
# ---------------------------------------------------------------------------


def _aa030_main_end(state: _Sl060State) -> None:
    """``aa030-Main-End.`` [sales/sl060.cbl:L612] - close phase 1, open phase 2.

    THE PERIOD-TOTAL WRITE AT [:L641] IS HERE, site 3 of the nine that are the
    sole writers of ``SYSTOT-REC``. So is the deductions analysis, the batch
    close, and the re-open of OTM3 for phase 2.

    Ends by FALLING THROUGH into ``aa040-End-Loop`` [:L661]: [:L659] is a
    display and the next line is the label.
    """
    system = state.system_record

    # [:L613] close open-item-file-2.
    state.open_item_file_2.close()
    # [:L614] perform OTM3-Close.
    facade.otm3_close(state.ctx(state.ws_otm3_record))
    # [:L615] perform Sales-Close.
    facade.sales_close(state.ctx(state.ws_sales_record))

    # [:L616-L636] Three report blocks, one per occurrence of the total table:
    # move total-net (n) to l6-net, move total-vat (n) to l6-vat,
    # add total-net (n) total-vat (n) giving l6-gross, move ws-lits (n) to
    # l6-lit, then write. Every receiver is a print field, so the arithmetic at
    # [:L618], [:L628] and [:L634] has no other effect and is omitted with them.
    # The PAGE TEST inside the first block is not omitted, because it calls a
    # section that resets a counter this program branches on:
    #
    # [:L621-L622] if line-cnt > Page-Lines - 7 perform ba000-Headings.
    # RELATION-CONDITION ARITHMETIC WITH NO RECEIVER - one of only six such
    # sites in the whole migration. Evaluated at intermediate precision; no
    # temporary field is introduced, because a temporary would have a picture
    # and a picture could round.
    if (
        arithmetic.compare(
            state.line_cnt,
            arithmetic.intermediate(system.system_data_block.page_lines - 7),
        )
        > 0
    ):
        _ba000_headings(state)

    # [:L638-L640] The "Total Amount Late Deductions" line. Print only - and
    # note that [:L638] moves the caption OVER line-6 as a group, which is why
    # the caption and l6-net share the record.

    # [:L641] add total-deduct to sl-credit-deductions.
    # ****** PERIOD TOTAL, SITE 3 OF 9 ****** SYSTOT-REC.SL-CREDIT-DEDUCTIONS
    # [copybooks/wssys4.cob:L15]. AAP section 0.6.4 records that the nine sites
    # across sl055, sl060, sl100, pl055, pl060 and pl100 are "the sole writers"
    # of this table, which is what makes the period-end-totals scenario
    # verifiable by inspecting one table. UNCONDITIONAL here.
    state.system_record_4.sales_ledger_data.sl_credit_deductions = arithmetic.add_to(
        state.total_deduct,
        receiver_value=state.system_record_4.sales_ledger_data.sl_credit_deductions,
        receiving=_SYSTOT["sl-credit-deductions"],
    )

    # [:L643-L647] if total-deduct not = zero -> open, analyse, close.
    if arithmetic.compare(state.total_deduct, 0) != 0:
        # [:L644] perform Value-Open.
        facade.value_open(state.ctx(state.ws_value_record))
        # [:L645] perform ba000-Analise-Deductions.
        _ba000_analise_deductions(state)
        # [:L646] perform Value-Close.
        facade.value_close(state.ctx(state.ws_value_record))

    # [:L649-L650] if G-L perform ca000-BL-Close.
    if _IS_G_L(system.system_data_block.level.level_1):
        _ca000_bl_close(state)

    # [:L656] perform OTM3-Open. Re-opened for the second phase, which walks it
    # sequentially rather than by key.
    facade.otm3_open(state.ctx(state.ws_otm3_record))
    # [:L658] move zero to work-b. The accumulator period-total site 4 writes.
    state.work_b = move.move_figurative(move.ZERO, _WORK_B)
    # [:L659] display "2 - Applying Cr. Notes to OTM3".
    _LOG.info("2 - Applying Cr. Notes to OTM3")

    # FALL-THROUGH into aa040-End-Loop. [:L661] is the next label.
    _aa040_end_loop(state)


# ---------------------------------------------------------------------------
# aa040-End-Loop.                                    [sales/sl060.cbl:L661]
# ---------------------------------------------------------------------------


def _aa040_end_loop(state: _Sl060State) -> None:
    """``aa040-End-Loop.`` [sales/sl060.cbl:L661] - phase 2, the credit swap walk.

    A sequential walk of OTM3 that hands every still-open credit note to
    ``ba000-Cr-Swop``. Three transfers: [:L664] out (class 2), and [:L669] and
    [:L674] back (class 1) - so end of file is the only exit.
    """
    while True:
        # [:L662] perform OTM3-Read-Next.
        facade.otm3_read_next(state.ctx(state.ws_otm3_record))
        # [:L663-L664] if fs-reply = 10 go to aa050-End-Loop-End.
        if state.file_access.fs_reply == FsReply.END_OF_FILE:
            # GO TO class 2 [sales/sl060.cbl:L664] -> aa050-End-Loop-End.
            break

        # [:L666] move open-item-record-3 to oi-header. COMMENTED OUT, "*> is
        # redefines" - the read already filled this storage. STRUCTURAL NOTE 1.

        body = state.oi_header.filler_1

        # [:L668-L669] if s-closed go to aa040-End-Loop.
        # `88 S-Closed value 1` [copybooks/slwsoi.cob:L49] - "Paid".
        if _IS_S_CLOSED(body.oi_status):
            # GO TO class 1 [sales/sl060.cbl:L669] -> aa040-End-Loop.
            continue

        # [:L671-L672] if oi-type = 3 perform ba000-Cr-Swop.
        if body.oi_type == 3:
            _ba000_cr_swop(state)

        # GO TO class 1 [sales/sl060.cbl:L674] -> aa040-End-Loop. Unconditional,
        # so the read at the head of the loop is the only place control leaves.
        continue

    # The post-loop block for the class-2 transfer at [:L664].
    _aa050_end_loop_end(state)


# ---------------------------------------------------------------------------
# aa050-End-Loop-End.                                [sales/sl060.cbl:L676]
# ---------------------------------------------------------------------------


def _aa050_end_loop_end(state: _Sl060State) -> None:
    """``aa050-End-Loop-End.`` [sales/sl060.cbl:L676] - close down, and site 4 of 9.

    Truncates the OTM2 sequence, writes the second period total, reports the
    missing-record warning, and hands the report to the operating system - the
    last of which is out of scope.

    Ends by FALLING THROUGH into ``aa999-Exit-Prog`` [:L722]: [:L713] is the
    last statement of the paragraph and the next line is the label.
    """
    system = state.system_record

    # [:L677] open output open-item-file-2.  *> Clear down IO2 file data now
    #                                        *> transferred to IO3
    # [:L678] close open-item-file-2.
    # OPEN OUTPUT ON A SEQUENTIAL FILE DISCARDS WHAT WAS THERE, so this pair
    # TRUNCATES the OTM2 extract - the transfer to OTM3 is complete and sl055's
    # output is deliberately destroyed. Reproduced: the work sequence's
    # open_output does the same, "because organization line sequential is why
    # open_output discards what was there before".
    state.open_item_file_2.open_output()
    state.open_item_file_2.close()
    # [:L679] perform OTM3-Close.
    facade.otm3_close(state.ctx(state.ws_otm3_record))

    # [:L681-L689] R-1 GATE 3 of 4.
    if _IS_FS_COBOL_FILES_USED(system.system_data_block.rdbms_flat_statuses.file_system_used):
        # [:L682-L683] call "CBL_CHECK_FILE_EXIST" using File-18 File-Info, then
        # [:L685] set File-18-Not-Exists / [:L687] set File-18-Exists. This is
        # the SECOND time the same question is asked about the same file - the
        # first was at [:L449] - and the answer can have changed, because
        # [:L677] has just rewritten it.
        raise _CobolLibraryRoutineUnavailable(
            "CBL_CHECK_FILE_EXIST", f"{_PROGRAM}:L682", "File-18 File-Info"
        )

    # [:L691-L693] if line-cnt > Page-Lines - 6 and FS-Cobol-Files-Used and
    #              File-18-Exists perform ba000-New-Heading.
    # A THREE-CONDITION AND that also carries relation-condition arithmetic.
    # The two flag tests here are ORDINARY TESTS, not the call-bearing gates
    # above: they choose presentation, they call nothing, and R-1 does not touch
    # them.
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

    # [:L695-L698] if FS-Cobol-Files-Used and File-18-Exists -> the
    # "Un-Applied Credits C/F" line. PRINT ONLY, and CONDITIONAL.
    if _IS_FS_COBOL_FILES_USED(
        system.system_data_block.rdbms_flat_statuses.file_system_used
    ) and condition_names.evaluate(_FILE_18_EXISTS, state.file_18_status):
        _LOG.info("Un-Applied Credits C/F  %s", state.work_b)

    # [:L700] add work-b to sl-cn-unappl-this-month.
    # ****** PERIOD TOTAL, SITE 4 OF 9 ****** SYSTOT-REC.SL-CN-UNAPPL-THIS-MONTH
    # [copybooks/wssys4.cob:L16].
    # IT IS OUTSIDE THE `if` AT [:L695]. The print line above is conditional;
    # this add is UNCONDITIONAL. Putting it inside would drop a SYSTOT-REC write
    # in flat-file mode and putting the print outside would add one in RDBMS
    # mode - so the split between the two statements is load-bearing and is
    # reproduced exactly as written.
    state.system_record_4.sales_ledger_data.sl_cn_unappl_this_month = arithmetic.add_to(
        state.work_b,
        receiver_value=state.system_record_4.sales_ledger_data.sl_cn_unappl_this_month,
        receiving=_SYSTOT["sl-cn-unappl-this-month"],
    )

    # [:L702-L707]
    # FINDING 9 [sales/sl060.cbl:L702-L707] - A MISSING `write`. The source is:
    #
    #     702      if       sales-missing
    #     703          if   FS-Cobol-Files-Used
    #     704               move SL133 to print-record
    #     705          else
    #     706               move SL133T to print-record
    #     707               write print-record after 3.
    #
    # The period on L707 closes BOTH `if`s, so the `write` belongs to the ELSE
    # branch ALONE: in flat-file mode the SL133 message is moved into the print
    # record and NEVER WRITTEN. Print-only, so no table effect - but it is
    # structurally the same class of defect as A-1 and is recorded rather than
    # repaired. Reproduced deliberately per R-4; DO NOT FIX. The log line below
    # therefore sits in the else arm only, exactly as the write does.
    if condition_names.evaluate(_SALES_MISSING, state.ws_error):
        if _IS_FS_COBOL_FILES_USED(
            system.system_data_block.rdbms_flat_statuses.file_system_used
        ):
            # [:L704] move SL133 to print-record - and no write follows it.
            pass
        else:
            # [:L706-L707] move SL133T to print-record / write print-record.
            _LOG.warning("%s", _SL133T)

    # [:L709] close print-file. OMITTED with the print file.
    # [:L710] call "SYSTEM" using Print-Report.
    # OMITTED: AAP section 0.1.1 excludes "the call "SYSTEM" using Print-Report
    # spool-out path that hands a report file to the operating system", and R-1
    # forbids shelling out in any case. Recorded in OMISSIONS.

    # [:L711-L713] R-1 GATE 4 of 4.
    if _IS_FS_COBOL_FILES_USED(
        system.system_data_block.rdbms_flat_statuses.file_system_used
    ) and condition_names.evaluate(_FILE_18_EXISTS, state.file_18_status):
        # [:L713] call "CBL_DELETE_FILE" using File-18. This one DESTROYS the
        # OTM2 file rather than truncating it, which is why the gate's two
        # conditions are spread over [:L711] and [:L712] as a continuation.
        raise _CobolLibraryRoutineUnavailable(
            "CBL_DELETE_FILE", f"{_PROGRAM}:L713", "File-18"
        )

    # [:L715-L720] A COMMENTED-OUT restore of Level-1, the other half of the
    # bypass at [:L458-L464]. Not compiled, not reproduced.

    # FALL-THROUGH into aa999-Exit-Prog. [:L722] is the next label.
    _aa999_exit_prog(state)


# ---------------------------------------------------------------------------
# aa999-Exit-Prog.                                   [sales/sl060.cbl:L722]
# ---------------------------------------------------------------------------


def _aa999_exit_prog(state: _Sl060State) -> None:
    """``aa999-Exit-Prog.`` [sales/sl060.cbl:L722] - return to the caller.

    FINDING 7 [sales/sl060.cbl:L723] - THE STATEMENT IS ``exit program.``, NOT
    ``goback.``. Every other module in this folder ends with ``goback``, and the
    two differ: ``GOBACK`` returns from a program OR terminates a main program,
    while ``EXIT PROGRAM`` in a program that was CALLed returns to the caller and
    in a main program does nothing at all. ``sl060`` is only ever CALLed - by
    the menu's ``load000`` [sales/sales.cbl:L765-L768] - so the two behave
    alike here, and the distinction is preserved as a finding rather than
    normalised away.
    """
    # FINDING 7 [sales/sl060.cbl:L723] - the terminator is `exit program.`, not
    # the `goback.` every sibling uses. Recorded, not normalised; see the
    # docstring above for why the two coincide for a CALLed program.
    # EXIT PROGRAM [sales/sl060.cbl:L723] - not a GO TO; the section's end.
    del state  # the return carries nothing back; see run()'s Returns note


# ---------------------------------------------------------------------------
# ba000-Cr-Swop section.                             [sales/sl060.cbl:L725]
# ---------------------------------------------------------------------------


def _ba000_cr_swop(state: _Sl060State) -> None:
    """``ba000-Cr-Swop section.`` [sales/sl060.cbl:L725] - carry an unapplied note.

    Marks a credit note closed, accumulates its outstanding value into the
    carried-forward total, and flips the sign before applying it to the note's
    own paid amount. THE ORDER OF THE LAST THREE STATEMENTS IS LOAD-BEARING:
    [:L757] accumulates the POSITIVE value into ``work-b`` - which period-total
    site 4 later writes [:L700] - and only then does [:L758] negate it for
    [:L759].
    """
    system = state.system_record
    oi = state.oi_header
    body = oi.filler_1
    money = body.filler_2

    # [:L728-L730] add oi-net oi-extra oi-carriage oi-vat oi-discount oi-e-vat
    #              oi-c-vat oi-deduct-amt oi-deduct-vat giving work-1.
    # NINE ADDENDS in one statement: summed at intermediate precision and
    # quantized ONCE into work-1, not nine times.
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
    # [:L731] add oi-paid to work-1.
    state.work_1 = arithmetic.add_to(
        money.oi_paid, receiver_value=state.work_1, receiving=_WORK_1
    )

    # [:L732-L735] if work-1 = zero -> display SL131 and, unless the caller is
    # the unattended driver, pause. The pause is dropped; the caller test is the
    # codebase's own and is kept.
    if arithmetic.compare(state.work_1, 0) == 0:
        _LOG.warning("%s", _SL131)
        if state.ws_calling_data.ws_caller.strip() != "xl150":
            _LOG.warning("%s", _SL003)

    # [:L740-L741] if FS-Cobol-Files-Used and File-18-Not-Exists perform
    #              ba000-New-Heading.
    # An ORDINARY test pair, not a call-bearing gate. Note the condition: the
    # heading is emitted when the OTM2 file does NOT exist, the opposite of the
    # test at [:L691].
    if _IS_FS_COBOL_FILES_USED(
        system.system_data_block.rdbms_flat_statuses.file_system_used
    ) and condition_names.evaluate(_FILE_18_NOT_EXISTS, state.file_18_status):
        _ba000_new_heading(state)

    # [:L743] move 1 to oi-status. `88 S-Closed value 1` - the note is now paid.
    body.oi_status = move.move_numeric(1, otm3.descriptor_for(type(body), "oi_status"))

    # [:L745-L751] Build and write line-7. Print only.
    # [:L753] add 1 to line-cnt.
    state.line_cnt = arithmetic.add_to(
        1, receiver_value=state.line_cnt, receiving=_LINE_CNT
    )
    # [:L754-L755] if line-cnt > Page-Lines perform ba000-New-Heading.
    if arithmetic.compare(state.line_cnt, system.system_data_block.page_lines) > 0:
        _ba000_new_heading(state)

    # [:L757] add work-1 to work-b. BEFORE the flip, so work-b takes the
    # positive outstanding value.
    state.work_b = arithmetic.add_to(
        state.work_1, receiver_value=state.work_b, receiving=_WORK_B
    )
    # [:L758] multiply -1 by work-1.
    # The NO-GIVING form again: receiver second, work-1 = -1 * work-1.
    state.work_1 = arithmetic.multiply_by(-1, state.work_1, _WORK_1)
    # [:L759] add work-1 to oi-paid. The NEGATED value.
    money.oi_paid = arithmetic.add_to(
        state.work_1,
        receiver_value=money.oi_paid,
        receiving=otm3.descriptor_for(type(money), "oi_paid"),
    )

    # [:L760] move OI-Header to WS-OTM3-Record. COMMENTED OUT, "*> is redefines".
    # [:L761] perform OTM3-Rewrite.
    facade.otm3_rewrite(state.ctx(state.ws_otm3_record))

    # FALL-THROUGH into this section's own main-exit.
    _ba000_cr_swop__main_exit(state)


def _ba000_cr_swop__main_exit(state: _Sl060State) -> None:
    """``main-exit.`` [sales/sl060.cbl:L763] - of ``ba000-Cr-Swop``.

    The name is section-qualified because ``main-exit.`` is declared SIX times
    in this program - [:L763], [:L789], [:L813], [:L829], [:L845] and [:L973] -
    and paragraph names are not globally unique in this codebase.

    # EXIT SECTION [sales/sl060.cbl:L764]
    """
    del state


# ---------------------------------------------------------------------------
# ba000-New-Heading section.                         [sales/sl060.cbl:L766]
# ba000-Headings section.                            [sales/sl060.cbl:L792]
#
# Both are report headings, so every write in them is omitted - but both remain
# named functions (R-5) and both still maintain `j` and `line-cnt`, because four
# sites branch on line-cnt [:L608, :L621, :L691, :L754] and the page number is
# what distinguishes the two sections' first-page behaviour.
# ---------------------------------------------------------------------------


def _ba000_new_heading(state: _Sl060State) -> None:
    """``ba000-New-Heading section.`` [sales/sl060.cbl:L766] - the phase-2 heading.

    Differs from :func:`_ba000_headings` in three ways, all preserved: it emits
    an extra ``line-1a`` [:L776, :L782], it uses ``line-4a`` rather than
    ``line-4`` [:L784], and it leaves ``line-cnt`` at SIX rather than five
    [:L787].
    """
    # [:L769] add 1 to j.
    state.j = arithmetic.add_to(1, receiver_value=state.j, receiving=_J)
    # [:L770] move j to l3-page. Print only.
    # [:L771] move usera to l3-user. Print only.
    # [:L773-L783] The page-throw block: after the first page it throws a page
    # and writes three heading lines plus a blank; on the first page it writes
    # the same three before the line. Print only.
    # [:L784-L786] line-4a and a blank line. Print only.
    # [:L787] move 6 to line-cnt.
    state.line_cnt = move.move_numeric(6, _LINE_CNT)

    # FALL-THROUGH into this section's own main-exit.
    _ba000_new_heading__main_exit(state)


def _ba000_new_heading__main_exit(state: _Sl060State) -> None:
    """``main-exit.`` [sales/sl060.cbl:L789] - of ``ba000-New-Heading``.

    # EXIT SECTION [sales/sl060.cbl:L790]
    """
    del state


def _ba000_headings(state: _Sl060State) -> None:
    """``ba000-Headings section.`` [sales/sl060.cbl:L792] - the phase-1 heading."""
    # [:L795] add 1 to j.
    state.j = arithmetic.add_to(1, receiver_value=state.j, receiving=_J)
    # [:L796] move j to l3-page. Print only.
    # [:L797] move usera to l3-user. Print only.
    # [:L799-L807] The page-throw block - two heading lines here, not three.
    # [:L808-L810] line-4 and a blank line. Print only.
    # [:L811] move 5 to line-cnt. FIVE, against the other section's six.
    state.line_cnt = move.move_numeric(5, _LINE_CNT)

    # FALL-THROUGH into this section's own main-exit.
    _ba000_headings__main_exit(state)


def _ba000_headings__main_exit(state: _Sl060State) -> None:
    """``main-exit.`` [sales/sl060.cbl:L813] - of ``ba000-Headings``.

    # EXIT SECTION [sales/sl060.cbl:L814]
    """
    del state



# ===========================================================================
# THE TWO MOVING-AVERAGE SECTIONS - ANOMALIES A-8, A-9 AND A-10
#
# ba000-Sales-Comp section.                          [sales/sl060.cbl:L816]
# ba000-Credit-Comp section.                         [sales/sl060.cbl:L832]
#
# ANOMALY A-10 [sales/sl060.cbl:L819, :L835, :L841] - THREE MUTUALLY
# INCONSISTENT GUARDS ON ONE IDIOM. Variants (a) and (b) are the two functions
# below; variant (c) is `compute-sales-pay` [sales/sl100.cbl:L497-L517], which
# uses a SINGLE-condition guard with no ELSE [:L506], increments its counter
# AFTER the accumulate [:L510], and writes the divide as `divide work-b by
# sales-pay-activety giving sales-pay-average` [:L511] rather than as an INTO.
#
# AAP section 0.6.1, verbatim: "Normalising them into one helper would be the
# single easiest way to fail this migration."
#
# So THE TWO FUNCTIONS BELOW ARE INDEPENDENT. Their bodies look almost
# duplicated and that is the point: there is no shared helper, no parameterised
# variant, no `if variant == ...`, and neither calls the other. Reproduced
# deliberately per R-4; DO NOT FACTOR.
#
# A TECHNICAL NOTE, so that the operand order is not mistaken for a defect and
# "corrected": `divide X into Y giving Z` and `divide Y by X giving Z` are
# ARITHMETICALLY EQUIVALENT - both are Z = Y / X. The difference between
# [sales/sl060.cbl:L827] and [sales/sl100.cbl:L511] is SYNTACTIC. The real
# divergences between the three variants are the guard structure and the counter
# increment, which are reproduced exactly. The INTO spelling is mirrored here by
# calling the INTO primitive.
# ===========================================================================


def _ba000_sales_comp(state: _Sl060State) -> None:
    """``ba000-Sales-Comp section.`` [sales/sl060.cbl:L816] - the invoice average.

    Maintains the customer's mean invoice value: rebuild the running total from
    the stored count and mean, count this invoice, add its goods value, divide
    back down. Performed for ``oi-type`` 1 and 2 [:L539-L540].

    ANOMALY A-8 [sales/sl060.cbl:L826-L827] - DOUBLE TRUNCATION, and it is a
    FIELD-WIDTH defect rather than an arithmetic one:

    * ``work-2`` is ``pic s9(14) comp-3`` [:L206] - fourteen digits, ZERO
      DECIMAL PLACES - while ``work-goods`` is ``pic s9(7)v99 comp-3`` [:L218].
      So [:L826] moves a two-decimal value into a zero-scale receiver and THE
      PENCE ARE DISCARDED ON EVERY ACCUMULATION. That is truncation one.
    * ``Sales-Average`` is ``binary-long`` [copybooks/wssl.cob:L49] - an
      INTEGER - so [:L827] discards the remainder as well. That is truncation
      two.

    Both happen because of the DECLARATIONS: the values below come from
    :mod:`acas_posting.cobol.arithmetic` against ``_WORK_2`` and the ledger's own
    ``sales-average`` descriptor, and nothing here rounds, quantizes or floors
    anything. If this module ever needs an explicit truncation to make A-8
    appear, the descriptors are wrong. Reproduced deliberately per R-4; DO NOT
    FIX - carrying two decimals through would diverge from the oracle on almost
    every invoice.

    ANOMALY A-10 variant (a) [sales/sl060.cbl:L819-L820] - the guard is a
    TWO-CONDITION test with an explicit ``ELSE`` and an ``END-IF``.
    """
    sales = state.ws_sales_record

    # [:L819-L824]
    if sales.sales_activety != 0 and sales.sales_average != 0:
        # [:L821] multiply sales-activety by sales-average giving work-2.
        state.work_2 = arithmetic.multiply_by_giving(
            sales.sales_activety, sales.sales_average, _WORK_2
        )
    else:
        # [:L823] move zero to work-2.
        state.work_2 = move.move_figurative(move.ZERO, _WORK_2)
    # [:L824] end-if

    # [:L825] add 1 to sales-activety.
    # UNCONDITIONAL, and BEFORE the divide - which is one of the two things
    # ba000-Credit-Comp does differently. See ANOMALY A-9.
    sales.sales_activety = arithmetic.add_to(
        1, receiver_value=sales.sales_activety, receiving=_SALES["sales-activety"]
    )
    # [:L826] add work-goods to work-2.
    # ANOMALY A-8 [sales/sl060.cbl:L826] - TRUNCATION ONE: two decimal places
    # into a zero-scale receiver [:L206] discards the pence.
    # Reproduced deliberately per R-4; DO NOT FIX.
    state.work_2 = arithmetic.add_to(
        state.work_goods, receiver_value=state.work_2, receiving=_WORK_2
    )
    # [:L827] divide sales-activety into work-2 giving sales-average.
    # ANOMALY A-8 [sales/sl060.cbl:L827] - TRUNCATION TWO: an integer receiver
    # [copybooks/wssl.cob:L49] discards the remainder, toward zero.
    # Reproduced deliberately per R-4; DO NOT FIX.
    sales.sales_average = arithmetic.divide_into_giving(
        sales.sales_activety, state.work_2, _SALES["sales-average"]
    )

    # FALL-THROUGH into this section's own main-exit.
    _ba000_sales_comp__main_exit(state)


def _ba000_sales_comp__main_exit(state: _Sl060State) -> None:
    """``main-exit.`` [sales/sl060.cbl:L829] - of ``ba000-Sales-Comp``.

    # EXIT SECTION [sales/sl060.cbl:L830]
    """
    del state


def _ba000_credit_comp(state: _Sl060State) -> None:
    """``ba000-Credit-Comp section.`` [sales/sl060.cbl:L832] - the credit-note average.

    The credit-note counterpart of :func:`_ba000_sales_comp`, performed for
    ``oi-type`` 3 [:L562]. IT IS NOT THE SAME, AND MUST NOT BE MADE THE SAME.

    ANOMALY A-9 [sales/sl060.cbl:L835-L843] - TWO INDEPENDENT DIVERGENCES from
    its sibling, both reproduced:

    1. THERE IS NO ``add 1 to sales-activety`` ANYWHERE IN THIS SECTION. Its
       sibling has one at [:L825]. So a credit note never counts toward the
       activity total that the average divides by.
    2. AN EXTRA OUTER GUARD, ``if work-2 not = zero`` [:L841], wraps BOTH the
       accumulate [:L842] AND the divide [:L843] - the period is at the end of
       L843, so both statements are inside it.

    The consequence of the two together: on a customer's FIRST credit note,
    ``sales-activety`` or ``sales-average`` is zero, so the inner guard
    [:L835-L836] fails, ``work-2`` becomes zero at [:L839], the [:L841] guard is
    therefore FALSE, and ``sales-average`` IS NOT UPDATED AT ALL. THE FIRST
    CREDIT NOTE FOR A CUSTOMER IS SILENTLY DROPPED. Reproduced deliberately per
    R-4; DO NOT FIX - neither by adding the counter increment nor by relaxing the
    guard.

    ANOMALY A-10 variant (b) [sales/sl060.cbl:L835, :L841] - the second and
    third of the three inconsistent guards, in one section.

    ANOMALY A-8 applies here too [sales/sl060.cbl:L842-L843]: the same
    zero-scale accumulator and the same integer quotient.
    """
    sales = state.ws_sales_record

    # [:L835-L840] The inner guard - textually identical to [:L819-L824].
    if sales.sales_activety != 0 and sales.sales_average != 0:
        # [:L837] multiply sales-activety by sales-average giving work-2.
        state.work_2 = arithmetic.multiply_by_giving(
            sales.sales_activety, sales.sales_average, _WORK_2
        )
    else:
        # [:L839] move zero to work-2.
        state.work_2 = move.move_figurative(move.ZERO, _WORK_2)
    # [:L840] end-if

    # NOTE THE ABSENCE. ba000-Sales-Comp has `add 1 to sales-activety` at
    # [:L825] between the guard and the accumulate. This section has NOTHING
    # here. See ANOMALY A-9 divergence 1.

    # [:L841] if work-2 not = zero
    # ANOMALY A-9 [sales/sl060.cbl:L841] - the extra outer guard that swallows a
    # customer's first credit note. Reproduced deliberately per R-4; DO NOT FIX.
    if state.work_2 != 0:
        # [:L842] add work-goods to work-2.
        # ANOMALY A-8 [sales/sl060.cbl:L842] - truncation one again.
        state.work_2 = arithmetic.add_to(
            state.work_goods, receiver_value=state.work_2, receiving=_WORK_2
        )
        # [:L843] divide sales-activety into work-2 giving sales-average.
        # ANOMALY A-8 [sales/sl060.cbl:L843] - truncation two again. Note that
        # the divisor is the UNINCREMENTED counter.
        sales.sales_average = arithmetic.divide_into_giving(
            sales.sales_activety, state.work_2, _SALES["sales-average"]
        )

    # FALL-THROUGH into this section's own main-exit.
    _ba000_credit_comp__main_exit(state)


def _ba000_credit_comp__main_exit(state: _Sl060State) -> None:
    """``main-exit.`` [sales/sl060.cbl:L845] - of ``ba000-Credit-Comp``.

    # EXIT SECTION [sales/sl060.cbl:L846]
    """
    del state


# ---------------------------------------------------------------------------
# ba000-CR-Notes section.                            [sales/sl060.cbl:L848]
#
# The two-pass OTM3 walk that applies a credit note to a customer's invoices.
# Its label graph is the only irreducible one in the program, because [:L908]
# transfers BACKWARD from the terminator paragraph into the loop.
# ---------------------------------------------------------------------------

#: The three labels of ba000-CR-Notes' internal graph, named so that the
#: dispatcher below reads as the transfers it realises.
_LABEL_BA010_READ_LOOP: Final[str] = "ba010-read-loop"
_LABEL_BA020_END_LOOP: Final[str] = "ba020-end-loop"
_LABEL_BA030_MAIN_END: Final[str] = "ba030-main-end"


def _ba000_cr_notes(state: _Sl060State) -> None:
    """``ba000-CR-Notes section.`` [sales/sl060.cbl:L848] - apply a credit note.

    Saves the header, positions OTM3 at the note's own invoice, and walks
    forward applying the note to matching invoices. If value remains after the
    first pass, it repositions to the START of the customer and walks again -
    this time applying to ANY invoice, not just the named one.

    GO TO CLASS 4, PROOF FOR [sales/sl060.cbl:L908]. ``ba020-end-loop`` is BOTH
    a loop terminator and a re-dispatcher: reached by three class-2 transfers
    [:L858, :L869, :L876] and by fall-through from [:L892], it may reset
    ``first-pass``, reposition the cursor and transfer BACKWARD to
    ``ba010-read-loop``. That makes the graph irreducible - two entries into the
    read loop, one from the preamble and one from the terminator - so it cannot
    be expressed as a single ``while`` with ``continue``/``break`` alone.

    The equivalence-preserving transformation is the label graph itself: each
    paragraph is a function that RETURNS THE LABEL IT TRANSFERS TO, and this
    dispatcher performs them in that order until ``ba030-main-end`` is reached.
    Every class-1 and class-2 transfer INSIDE ``ba010-read-loop`` stays a
    ``continue`` or a ``break`` there, so only the one genuinely irreducible
    edge is handled here. Nothing is collapsed and the two passes remain two.
    """
    oi = state.oi_header
    key = oi.oi_key
    body = oi.filler_1

    # [:L851] move oi-header to si-header. A GROUP MOVE - the save half of the
    # pair that brackets this section; STRUCTURAL NOTE 2.
    _group_move_oi_header(oi, state.si_header)
    # [:L852] move "Y" to first-pass.
    state.first_pass = move.move_alphanumeric("Y", _FIRST_PASS)
    # [:L853] move oi-customer to oi3-customer.
    # A NO-OP BY CONSTRUCTION: oi3-customer occupies the same seven bytes as the
    # oi-customer group it is being given (STRUCTURAL NOTE 1), so the bytes are
    # rewritten with themselves. Reproduced rather than dropped, because the
    # statement is written and because the next line proves the author was
    # building a key in this storage on purpose.
    _write_oi3_customer(state, _oi_customer_image(oi))
    # [:L854] move oi-cr to oi3-invoice.
    # NOT a no-op: oi3-invoice IS oi-invoice, so this OVERWRITES the header's own
    # invoice number with the credit-note number. Safe only because [:L851]
    # saved the header and [:L913] restores it.
    key.oi_invoice = move.move_numeric(
        body.oi_cr, otm3.descriptor_for(type(key), "oi_invoice")
    )
    # [:L855] set fn-not-less-than to true.
    # The ISAM START relation, through the access-type vocabulary
    # [copybooks/wsfnctn.cob:L115] - never a raw integer. Note that OTM3-Start
    # is the one facade verb that does NOT clear Access-Type first
    # [copybooks/Proc-ACAS-FH-Calls.cob:L1036], by the deliberate change its
    # changelog records at
    # [copybooks/Proc-ACAS-FH-Calls.cob:L18]: "Remove 'move zero to access-type for Start,
    # it is set !!!".
    state.file_access.access_type = AccessType.NOT_LESS_THAN
    # [:L856] perform OTM3-Start.
    facade.otm3_start(state.ctx(state.ws_otm3_record))

    # [:L857-L858] if fs-reply not = zero go to ba020-end-loop.
    # GO TO class 2 [sales/sl060.cbl:L858] -> ba020-end-loop. It skips
    # [:L859-L862], so on this path work-b is NOT zeroed and work-1 is NOT
    # reduced by the amount already paid - and ba020-end-loop then decides on a
    # work-1 that still holds the whole invoice gross from [:L529-L530].
    label = _LABEL_BA020_END_LOOP
    if state.file_access.fs_reply == FsReply.SUCCESS:
        # [:L859] move zero to work-b.
        state.work_b = move.move_figurative(move.ZERO, _WORK_B)
        # [:L860-L861] if work-1 < zero multiply -1 by work-1.
        # The NO-GIVING form once more: receiver second.
        if arithmetic.compare(state.work_1, 0) < 0:
            state.work_1 = arithmetic.multiply_by(-1, state.work_1, _WORK_1)
        # [:L862] subtract si-paid from work-1. si-paid is the SAVED paid
        # amount, from the header that [:L851] copied.
        state.work_1 = arithmetic.subtract_from(
            state.si_header.filler_1.filler_2.oi_paid,
            receiver_value=state.work_1,
            receiving=_WORK_1,
        )
        label = _LABEL_BA010_READ_LOOP

    # The label graph. Two entries into ba010-read-loop: here, and the class-4
    # edge at [:L908] that ba020-end-loop returns.
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
        The label this paragraph transfers to. Every exit goes to
        ``ba020-end-loop``: by the class-2 transfers at [:L869] and [:L876], and
        by FALL-THROUGH past [:L892] when the credit note is exhausted.
    """
    si = state.si_header
    si_body = si.filler_1
    si_image = _oi_customer_image(si)

    while True:
        # [:L867] perform OTM3-Read-Next.
        facade.otm3_read_next(state.ctx(state.ws_otm3_record))
        # [:L868-L869] if fs-reply = 10 go to ba020-end-loop.
        if state.file_access.fs_reply == FsReply.END_OF_FILE:
            # GO TO class 2 [sales/sl060.cbl:L869] -> ba020-end-loop.
            return _LABEL_BA020_END_LOOP

        # [:L871] move open-item-record-3 to oi-header. COMMENTED OUT,
        # "*> is redefines"; the read filled this storage. STRUCTURAL NOTE 1.

        oi = state.oi_header
        key = oi.oi_key
        body = oi.filler_1
        money = body.filler_2

        # [:L872-L873] if oi-type not = 2 go to ba010-read-loop.
        if body.oi_type != 2:
            # GO TO class 1 [sales/sl060.cbl:L873] -> ba010-read-loop.
            continue
        # [:L875-L876] if oi-customer not = si-customer go to ba020-end-loop.
        # A GROUP comparison of two seven-byte areas of identical description,
        # so the byte images compare directly with no padding to decide.
        if _oi_customer_image(oi) != si_image:
            # GO TO class 2 [sales/sl060.cbl:L876] -> ba020-end-loop. The walk
            # stops at the first row of the next customer, which is what makes
            # the START relation and the key order load-bearing.
            return _LABEL_BA020_END_LOOP
        # [:L877-L878] if s-closed go to ba010-read-loop.
        if _IS_S_CLOSED(body.oi_status):
            # GO TO class 1 [sales/sl060.cbl:L878] -> ba010-read-loop.
            continue

        # [:L882] add oi-deduct-amt oi-deduct-vat giving work-b.
        state.work_b = arithmetic.add_giving(
            body.oi_deduct_amt, body.oi_deduct_vat, receiving=_WORK_B
        )
        # [:L883] move oi-date to u-bin.
        # u-bin is the maps04 linkage field [copybooks/wsmaps03.cob:L29] used
        # here as a PLAIN ARITHMETIC REGISTER over the binary day number - no
        # conversion is performed, so no date section is called.
        state.maps03_ws.u_bin = move.move_numeric(body.oi_date, _MAPS03["u-bin"])
        # [:L884] add 1 oi-deduct-days to u-bin.
        # TWO SOURCES INTO ONE RECEIVER: both the literal 1 and the deduction
        # days are added to u-bin - not one statement per source.
        state.maps03_ws.u_bin = arithmetic.add_to(
            1,
            body.oi_deduct_days,
            receiver_value=state.maps03_ws.u_bin,
            receiving=_MAPS03["u-bin"],
        )
        # [:L885-L886] if u-bin not > si-date move zero to work-b.
        # The settlement-discount eligibility test: unless the invoice's
        # deduction window closes AFTER the credit note's date, the deduction is
        # not available and work-b is cleared.
        if arithmetic.compare(state.maps03_ws.u_bin, si_body.oi_date) <= 0:
            state.work_b = move.move_figurative(move.ZERO, _WORK_B)

        # [:L888-L890] if si-cr = oi-invoice or first-pass = "N"
        #              perform ba000-Apportion.
        # First pass applies the note only to the invoice it names; the second
        # pass, with first-pass "N", applies it to any of the customer's
        # invoices.
        if si_body.oi_cr == key.oi_invoice or state.first_pass == "N":
            _ba000_apportion(state)

        # [:L892-L893] if work-1 not = zero go to ba010-read-loop.
        if arithmetic.compare(state.work_1, 0) != 0:
            # GO TO class 1 [sales/sl060.cbl:L893] -> ba010-read-loop.
            continue

        # FALL-THROUGH past [:L893] into ba020-end-loop [:L895]: the credit note
        # is fully applied, so the walk stops.
        return _LABEL_BA020_END_LOOP


def _ba020_end_loop(state: _Sl060State) -> str:
    """``ba020-end-loop.`` [sales/sl060.cbl:L895] - end the pass, or start the second.

    Returns:
        ``ba010-read-loop`` for the class-4 backward transfer at [:L908], or
        ``ba030-main-end`` for the class-2 transfers at [:L900] and [:L907].
    """
    si = state.si_header

    # [:L898-L900] if work-1 = zero or first-pass not = "Y" go to ba030-main-end.
    # Nothing left to apply, or the second pass has already been made.
    if arithmetic.compare(state.work_1, 0) == 0 or state.first_pass != "Y":
        # GO TO class 2 [sales/sl060.cbl:L900] -> ba030-main-end.
        return _LABEL_BA030_MAIN_END

    # [:L901] move "N" to first-pass.
    state.first_pass = move.move_alphanumeric("N", _FIRST_PASS)
    # [:L902] move si-customer to oi3-customer. From the SAVED header, because
    # the walk has left the current header on some other customer's row.
    _write_oi3_customer(state, _oi_customer_image(si))
    # [:L903] move zero to oi3-invoice. Position at the customer's FIRST invoice
    # rather than at the credit note's own.
    state.oi_header.oi_key.oi_invoice = move.move_figurative(
        move.ZERO, otm3.descriptor_for(type(state.oi_header.oi_key), "oi_invoice")
    )
    # [:L904] set fn-not-less-than to true. Set again - the previous START
    # consumed it, and OTM3-Start does not default it.
    state.file_access.access_type = AccessType.NOT_LESS_THAN
    # [:L905] perform OTM3-Start.
    facade.otm3_start(state.ctx(state.ws_otm3_record))
    # [:L906-L907] if fs-reply not = zero go to ba030-main-end.
    if state.file_access.fs_reply != FsReply.SUCCESS:
        # GO TO class 2 [sales/sl060.cbl:L907] -> ba030-main-end.
        return _LABEL_BA030_MAIN_END

    # GO TO class 4 [sales/sl060.cbl:L908] -> ba010-read-loop. The BACKWARD
    # transfer that makes this graph irreducible; see the proof in
    # :func:`_ba000_cr_notes`.
    return _LABEL_BA010_READ_LOOP


def _ba030_main_end(state: _Sl060State) -> None:
    """``ba030-main-end.`` [sales/sl060.cbl:L910] - restore the header."""
    # [:L913] move si-header to oi-header. The RESTORE half of the pair; the
    # walk has left the current header on whatever row it stopped at, and
    # aa020-Read-Loop expects its own record back - it goes on to read
    # sales-current and write the open item from this storage.
    _group_move_oi_header(state.si_header, state.oi_header)


def _ba040_main_exit(state: _Sl060State) -> None:
    """``ba040-main-exit.`` [sales/sl060.cbl:L915] - of ``ba000-CR-Notes``.

    Uniquely among this program's six section exits, this one is PREFIXED rather
    than plain ``main-exit`` - the section numbers its four paragraphs ba000,
    ba010, ba020, ba030 and then names the exit ba040.

    # EXIT SECTION [sales/sl060.cbl:L916]
    """
    del state



# ---------------------------------------------------------------------------
# ba000-Apportion section.                           [sales/sl060.cbl:L918]
# ---------------------------------------------------------------------------


def _ba000_apportion(state: _Sl060State) -> None:
    """``ba000-Apportion section.`` [sales/sl060.cbl:L918] - apply value to one invoice.

    Works out what the invoice still owes, then applies as much of the credit
    note as fits: all of the note if the invoice owes exactly that or more, or
    only what the invoice owes if it owes less.

    FINDING 10 [sales/sl060.cbl:L935-L955] - THE THREE ARMS ARE ASYMMETRIC, and
    the asymmetry is not in the arithmetic but in the bookkeeping:

    * ``= work-1`` [:L935-L941] sets BOTH ``oi-status`` and ``si-status``, and
      DOES perform ``ba000-Clear-Invoice-Deduct``.
    * ``> work-1`` [:L943-L948] sets ONLY ``si-status``, and does NOT perform
      ``ba000-Clear-Invoice-Deduct`` - so an invoice that is only partly settled
      keeps its deduction fields, and neither ``sales-current`` nor
      ``ws-deduction`` nor ``total-mov-ded`` moves on this path.
    * the ``else`` [:L950-L955] sets ONLY ``oi-status``, and DOES perform it.

    All three are reproduced exactly as written. R-3 forbids imposing the
    symmetry that would make them one arm with flags.
    """
    oi = state.oi_header
    body = oi.filler_1
    money = body.filler_2
    si_body = state.si_header.filler_1
    si_money = si_body.filler_2

    # [:L921-L923] add oi-net oi-extra oi-carriage oi-vat oi-discount oi-e-vat
    #              oi-c-vat oi-deduct-amt oi-deduct-vat giving work-a.
    # The SECOND nine-addend statement in the program; the other is [:L728-L730].
    # Summed at intermediate precision and quantized ONCE.
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
    # [:L924] subtract oi-paid from work-a. What the invoice still owes.
    state.work_a = arithmetic.subtract_from(
        money.oi_paid, receiver_value=state.work_a, receiving=_WORK_A
    )

    # [:L926-L928] if work-a = zero -> already settled.
    if arithmetic.compare(state.work_a, 0) == 0:
        # [:L927] move 1 to oi-status.
        body.oi_status = move.move_numeric(
            1, otm3.descriptor_for(type(body), "oi_status")
        )
        # GO TO class 4 [sales/sl060.cbl:L928] -> ba000-Main-Rewrite.
        # PROOF: the target is a SIBLING PARAGRAPH of this section that performs
        # work - it rewrites the open item [:L962] - and then itself transfers
        # control with `exit section` [:L963]. So the equivalent is a CALL to the
        # named paragraph followed by a RETURN, and neither [:L930] onwards nor
        # ba000-Clear-Invoice-Deduct can be reached afterwards. It is not a plain
        # `return`, because the rewrite must happen; and not a fall-through,
        # because the intervening statements must not.
        _ba000_main_rewrite(state)
        return

    # [:L930-L931] if work-a not > zero exit section.
    # EXIT SECTION [sales/sl060.cbl:L931] - a STATEMENT, not a GO TO: the
    # invoice is overpaid, so there is nothing to apply and NO REWRITE HAPPENS.
    if arithmetic.compare(state.work_a, 0) <= 0:
        return

    # [:L933] subtract work-b from work-a. Take off any settlement deduction the
    # eligibility test at [:L885] left standing.
    state.work_a = arithmetic.subtract_from(
        state.work_b, receiver_value=state.work_a, receiving=_WORK_A
    )

    oi_paid = otm3.descriptor_for(type(money), "oi_paid")
    oi_p_c = otm3.descriptor_for(type(money), "oi_p_c")
    oi_status = otm3.descriptor_for(type(body), "oi_status")
    si_paid = otm3.descriptor_for(type(si_money), "oi_paid")
    si_status = otm3.descriptor_for(type(si_body), "oi_status")

    # [:L935] if work-a = work-1  - the invoice owes exactly the note's value.
    if arithmetic.compare(state.work_a, state.work_1) == 0:
        # [:L936] add work-1 to oi-paid.  [:L937] add work-1 to si-paid.
        # [:L938] add work-1 to oi-p-c.   THREE SEPARATE statements.
        money.oi_paid = arithmetic.add_to(
            state.work_1, receiver_value=money.oi_paid, receiving=oi_paid
        )
        si_money.oi_paid = arithmetic.add_to(
            state.work_1, receiver_value=si_money.oi_paid, receiving=si_paid
        )
        money.oi_p_c = arithmetic.add_to(
            state.work_1, receiver_value=money.oi_p_c, receiving=oi_p_c
        )
        # [:L939] move zero to work-1. The note is exhausted.
        state.work_1 = move.move_figurative(move.ZERO, _WORK_1)
        # [:L940] perform ba000-Clear-Invoice-Deduct.
        _ba000_clear_invoice_deduct(state)
        # [:L941] move 1 to oi-status si-status. BOTH, in one two-receiver MOVE.
        (body.oi_status, si_body.oi_status) = move.move_to_all(
            1, (oi_status, si_status)
        )
    # [:L943] else if work-a > work-1  - the invoice owes more than the note.
    elif arithmetic.compare(state.work_a, state.work_1) > 0:
        # [:L944-L946] The same three adds.
        money.oi_paid = arithmetic.add_to(
            state.work_1, receiver_value=money.oi_paid, receiving=oi_paid
        )
        si_money.oi_paid = arithmetic.add_to(
            state.work_1, receiver_value=si_money.oi_paid, receiving=si_paid
        )
        money.oi_p_c = arithmetic.add_to(
            state.work_1, receiver_value=money.oi_p_c, receiving=oi_p_c
        )
        # [:L947] move zero to work-1.
        state.work_1 = move.move_figurative(move.ZERO, _WORK_1)
        # [:L948] move 1 to si-status.
        # FINDING 10: ONLY si-status here, and NO perform of
        # ba000-Clear-Invoice-Deduct - the only one of the three arms that omits
        # it. Reproduced deliberately per R-4; DO NOT FIX.
        si_body.oi_status = move.move_numeric(1, si_status)
    # [:L949] else  - the invoice owes less than the note.
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
        # [:L953] subtract work-a from work-1. What remains of the note.
        state.work_1 = arithmetic.subtract_from(
            state.work_a, receiver_value=state.work_1, receiving=_WORK_1
        )
        # [:L954] perform ba000-Clear-Invoice-Deduct.
        _ba000_clear_invoice_deduct(state)
        # [:L955] move 1 to oi-status.
        # FINDING 10: ONLY oi-status here.
        body.oi_status = move.move_numeric(1, oi_status)

    # [:L957-L958] if work-1 = zero move 1 to si-status.
    # OUTSIDE the three arms, so it can set si-status a second time on the first
    # arm and can set it on the third arm - which is the only way the third
    # arm's saved header is ever closed.
    if arithmetic.compare(state.work_1, 0) == 0:
        si_body.oi_status = move.move_numeric(1, si_status)

    # FALL-THROUGH into ba000-Main-Rewrite [:L960]: [:L958] is the last statement
    # before the label and no transfer intervenes.
    _ba000_main_rewrite(state)


def _ba000_main_rewrite(state: _Sl060State) -> None:
    """``ba000-Main-Rewrite.`` [sales/sl060.cbl:L960] - store the apportioned item.

    Reached two ways: by the class-4 transfer at [:L928] and by fall-through
    from [:L958].

    # EXIT SECTION [sales/sl060.cbl:L963] - which is why ba000-Clear-Invoice-
    # Deduct [:L965] is never reached by fall-through from here, only by the two
    # PERFORMs at [:L940] and [:L954].
    """
    # [:L961] move oi-header to open-item-record-3. COMMENTED OUT, "*> is
    # redefines"; STRUCTURAL NOTE 1.
    # [:L962] perform OTM3-Rewrite.
    facade.otm3_rewrite(state.ctx(state.ws_otm3_record))


def _ba000_clear_invoice_deduct(state: _Sl060State) -> None:
    """``ba000-Clear-Invoice-Deduct.`` [sales/sl060.cbl:L965] - take the deduction.

    A REAL DATABASE EFFECT: [:L967] reduces the customer's balance by the
    settlement deduction, which is a ``SALEDGER-REC`` column, and [:L970] clears
    the invoice's own deduction fields, which are ``SAITM3-REC`` columns. It also
    feeds two report accumulators - ``ws-deduction`` reaches [:L565] and
    ``total-mov-ded`` reaches ``ba000-Analise-Deductions`` [:L985], which
    SUBTRACTS it from the analysis totals.

    ``PERFORM`` executes THIS PARAGRAPH ONLY, up to the next label, so control
    returns to the caller at the end of [:L970] and does not run
    ``ba000-cid-exit`` or ``main-exit``.
    """
    body = state.oi_header.filler_1
    sales = state.ws_sales_record

    # [:L966] if work-b > zero
    if arithmetic.compare(state.work_b, 0) > 0:
        # [:L967] subtract work-b from sales-current.
        sales.sales_current = arithmetic.subtract_from(
            state.work_b,
            receiver_value=sales.sales_current,
            receiving=_SALES["sales-current"],
        )
        # [:L968] add work-b to ws-deduction.
        state.ws_deduction = arithmetic.add_to(
            state.work_b, receiver_value=state.ws_deduction, receiving=_WS_DEDUCTION
        )
        # [:L969] add 1 to total-mov-ded.
        state.total_mov_ded = arithmetic.add_to(
            1, receiver_value=state.total_mov_ded, receiving=_TOTAL_MOV_DED
        )
        # [:L970] move zero to oi-deduct-amt oi-deduct-vat. Two receivers.
        (body.oi_deduct_amt, body.oi_deduct_vat) = move.move_to_all(
            move.ZERO,
            (
                otm3.descriptor_for(type(body), "oi_deduct_amt"),
                otm3.descriptor_for(type(body), "oi_deduct_vat"),
            ),
        )


def _ba000_cid_exit(state: _Sl060State) -> None:
    """``ba000-cid-exit.`` [sales/sl060.cbl:L971] - AN EMPTY PARAGRAPH.

    The label carries NO STATEMENTS: [:L972] is a comment and [:L973] is the
    next label. Retained as a named function because R-5 traces declarations,
    and AAP section 0.7.4 C-4 requires that "every paragraph retains a named
    function even where its GO TO becomes a continue, a break or a return".

    Two facts about its reachability, both verifiable:

    * By STRAIGHT-LINE execution it would be entered by fall-through from
      [:L970] and would itself fall through into ``main-exit`` [:L973].
    * In practice NEITHER IS EVER ENTERED. ``ba000-Clear-Invoice-Deduct`` is
      only ever ``PERFORM``ed [:L940, :L954], and a ``PERFORM`` of a paragraph
      returns at the paragraph's end rather than falling into the next label;
      and straight-line execution cannot arrive here at all, because
      ``ba000-Main-Rewrite`` ends with ``exit section`` [:L963]. So this
      paragraph and the ``main-exit`` below it are DEAD LABELS.
    """
    # FALL-THROUGH into main-exit [:L973] - the shape of the source, though the
    # note above explains why control never takes it.
    _ba000_apportion__main_exit(state)


def _ba000_apportion__main_exit(state: _Sl060State) -> None:
    """``main-exit.`` [sales/sl060.cbl:L973] - of ``ba000-Apportion``.

    The sixth and last declaration of this paragraph name in the program, hence
    the section-qualified Python name. Dead, for the reason given in
    :func:`_ba000_cid_exit`.

    # EXIT SECTION [sales/sl060.cbl:L974]
    """
    del state


# ---------------------------------------------------------------------------
# ba000-Analise-Deductions section.                  [sales/sl060.cbl:L976]
# ---------------------------------------------------------------------------


def _ba000_analise_deductions(state: _Sl060State) -> None:
    """``ba000-Analise-Deductions section.`` [:L976] - reverse the discount totals.

    Reads the analysis row for the settlement-discount group and SUBTRACTS this
    run's deduction count and value from both the this-period and the year
    totals - reversing what ``sl055`` accumulated into the same ``"zd"`` group -
    then does the whole thing a SECOND time against the group with a blanked
    second character.

    THE TWO BLOCKS ARE DELIBERATELY NOT FACTORED. They differ in the key they
    read [:L979] against [:L992], and ``sl055``'s own ``dc000-Store-Specials``
    carries the same twice-over shape. Collapsing them into a loop would be the
    kind of tidying R-3 forbids, and it would also hide that the second read can
    fail independently of the first [:L995].

    Called only when ``total-deduct`` is non-zero [:L643-L646], between an
    explicit ``Value-Open`` and ``Value-Close``.
    """
    value = state.ws_value_record

    # [:L979] move "Szd" to va-code.
    # A GROUP MOVE of three characters into va-code, which is va-system plus
    # va-group's two characters [copybooks/wsval.cob:L11-L15]: "S" for the sales
    # ledger, "zd" for the settlement-discount group sl055 created. Split by
    # reference modification, 1-based, through the published primitive.
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
    # [:L980] move 1 to File-Key-No. Redundant twice over - the dispatch
    # paragraph sets it [copybooks/Proc-ACAS-FH-Calls.cob:L98] and so does the
    # Value-Read-Indexed verb itself [:L753] - and written anyway.
    state.file_access.logging_data.file_key_no = move.move_numeric(
        1, _ACCESS["file-key-no"]
    )
    # [:L981] perform Value-Read-Indexed
    facade.value_read_indexed(state.ctx(state.ws_value_record))
    # [:L982-L983] if FS-Reply = 21 exit section.
    # EXIT SECTION [sales/sl060.cbl:L983] - no analysis row, so no reversal, and
    # the second block does not run either.
    if state.file_access.fs_reply == FsReply.INVALID_KEY_ON_START:
        return

    # [:L985-L988] Four SUBTRACT ... FROM statements, no GIVING: each receiver
    # is reduced in place. The counts come from total-mov-ded and the values
    # from total-deduct.
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

    # [:L990] perform Value-Rewrite.
    facade.value_rewrite(state.ctx(state.ws_value_record))

    # [:L992] move space to va-second. The key becomes "Sz " - the group total
    # rather than the specific code.
    value.va_code.va_group.va_second = move.move_figurative(
        move.SPACE, _VALUE["va-second"]
    )
    # [:L993] move 1 to File-Key-No. Written a second time.
    state.file_access.logging_data.file_key_no = move.move_numeric(
        1, _ACCESS["file-key-no"]
    )
    # [:L994] perform Value-Read-Indexed.
    facade.value_read_indexed(state.ctx(state.ws_value_record))
    # [:L995-L996] if FS-Reply = 21 exit section.
    # EXIT SECTION [sales/sl060.cbl:L996] - and note that the FIRST block's
    # rewrite has already happened, so this is a partial effect, not a no-op.
    if state.file_access.fs_reply == FsReply.INVALID_KEY_ON_START:
        return

    # [:L998-L1001] The same four subtracts against the group row.
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
    # [:L1002] perform Value-Rewrite.
    facade.value_rewrite(state.ctx(state.ws_value_record))

    # FALL-THROUGH into this section's own exit.
    _ba999_main_exit(state)


def _ba999_main_exit(state: _Sl060State) -> None:
    """``ba999-main-exit.`` [sales/sl060.cbl:L1004] - of ``ba000-Analise-Deductions``.

    # EXIT SECTION [sales/sl060.cbl:L1005]
    """
    del state



# ---------------------------------------------------------------------------
# ca000-BL-Open section.                            [sales/sl060.cbl:L1007]
#
# THE GATING, STATED ONCE FOR ALL THREE ca000 SECTIONS.  This section is
# reached ONLY from [:L466-L467] `if G-L perform ca000-BL-Open.`, and
# ca000-BL-Write only from [:L535-L536] `if G-L perform ca000-BL-Write.`, and
# ca000-BL-Close from [:L649-L650] `if G-L perform ca000-BL-Close.` plus the
# 99-item cap [:L1152].  So in IRS-ONLY mode (`IRS-Instead = "Y"`, `Level-1`
# not 1) NONE of the three ever runs and NO batch, GL posting or IRS posting
# row is written at all - even though the sections themselves contain three
# `irs-used OR IRS-Both-Used` tests that would write IRS rows if reached.
# That is the single biggest determinant of which tables a run touches.
# ---------------------------------------------------------------------------


def _ca000_bl_open(state: _Sl060State) -> None:
    """``ca000-BL-Open section.`` [sales/sl060.cbl:L1007] - start a GL batch.

    Claims the next batch number from the system record, builds the batch header
    in working storage, and opens the posting file or files that the IRS fan-out
    switch selects.

    A-17's OTHER END lives here, at [:L1037].
    """
    system = state.system_record
    gl_block = system.general_ledger_block
    batch = state.ws_batch_record

    # [:L1010] perform GL-Batch-Open.
    facade.gl_batch_open(state.ctx(state.ws_batch_record))
    # [:L1011-L1014] The open-then-fallback pair that the other two opens in this
    # section still have is COMMENTED OUT for the batch file. Reproduced as the
    # absence it is: a failed GL-Batch-Open is NOT recovered from, and the batch
    # header is built and written regardless.

    # [:L1016] move next-Batch to WS-Batch-nos.
    # Next-Batch is `binary-short` [copybooks/wssystem.cob] and WS-Batch-Nos is
    # `pic 9(5)` DISPLAY UNSIGNED [copybooks/wsbatch.cob:L19], so this is a
    # narrowing, sign-dropping MOVE handled by the published primitive.
    batch.ws_batch_key.ws_batch_nos = move.move_numeric(
        gl_block.next_batch,
        _BATCH["ws-batch-nos"],
        sending_field=_SYSTEM["next-batch"],
    )
    # [:L1017] move 3 to WS-ledger.  3 = Sales Ledger.
    batch.ws_batch_key.ws_ledger = move.move_numeric(3, _BATCH["ws-ledger"])
    # [:L1018] add 1 to next-Batch.  The system record is mutated here but only
    # persisted by whatever later writes SYSTEM-REC; sl060 never writes it
    # itself, which is why A-17's `postings` update [:L1173] shares its fate.
    # AMBIGUITY Q-6 [sales/sl060.cbl:L1018] - sl060 increments Next-Batch and
    # (via A-17) sets Postings, but performs NO System-Rewrite anywhere. Whether
    # the run's caller writes SYSTEM-REC back, and therefore whether either
    # update survives the run, must be measured against the compiled oracle.
    gl_block.next_batch = arithmetic.add_to(
        1, receiver_value=gl_block.next_batch, receiving=_SYSTEM["next-batch"]
    )
    # [:L1019-L1020] move zero to Batch-status cleared-status.  Two receivers.
    (batch.batch_status, batch.cleared_status) = move.move_to_all(
        move.ZERO, (_BATCH["batch-status"], _BATCH["cleared-status"])
    )
    # [:L1021] move scycle to bcycle.  Scycle is `binary-char`, Bcycle `pic 99`.
    batch.bcycle = move.move_numeric(
        system.system_data_block.scycle,
        _BATCH["bcycle"],
        sending_field=_SYSTEM["scycle"],
    )
    # [:L1022] move run-date to entered.
    # THE CONTROLLED-CLOCK OBSERVABLE. Run-Date [copybooks/wssystem.cob:L67] is
    # the binary run date, pinned by the caller and arriving through linkage; R-6
    # forbids reading any clock here, and sl060 reads none.
    batch.dates.entered = move.move_numeric(
        system.system_data_block.run_date,
        _BATCH["entered"],
        sending_field=_SYSTEM["run-date"],
    )

    # [:L1024] move "Sales Ledger Invoices" to description.
    # 21 characters into `pic x(24)`, so space-padded by the receiving field.
    batch.description = move.move_alphanumeric(
        "Sales Ledger Invoices", _BATCH["description"]
    )
    # [:L1025-L1032] move zero to bdefault Batch-def-ac Batch-def-pc items
    #               input-gross input-vat actual-gross actual-vat.
    # EIGHT receivers in one MOVE; the figurative is converted once per receiver.
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

    # [:L1034] move "CR" to convention.
    batch.posting_data.convention = move.move_alphanumeric(
        "CR", _BATCH["convention"]
    )
    # [:L1035] move "SL" to Batch-def-code.
    batch.posting_data.batch_def_code = move.move_alphanumeric(
        "SL", _BATCH["batch-def-code"]
    )
    # [:L1036] move "O" to Batch-def-vat.  "O" for output tax.
    batch.posting_data.batch_def_vat = move.move_alphanumeric(
        "O", _BATCH["batch-def-vat"]
    )
    # [:L1037] add postings 1 giving Batch-start.
    # ANOMALY A-17 [sales/sl060.cbl:L1037] - THE READ-BACK END of the unexplained
    # move at [:L1173]. `Postings` is the SYSTEM-REC posting-RRN high-water mark:
    # this batch's first posting RRN is one past it, and [:L1173] pushes the mark
    # forward to whatever RRN the batch reached. The AAP frames [:L1173] as a
    # curiosity carrying the maintainer's own `*> Why ?`; it is not, because THIS
    # statement reads the field back, so the pair is load-bearing and
    # diff-visible in GLPOSTING-REC.POST-RRN.
    # Reproduced deliberately per R-4; DO NOT FIX.
    batch.batch_start = arithmetic.add_giving(
        gl_block.postings, 1, receiving=_BATCH["batch-start"]
    )

    # [:L1039] if irs-used OR IRS-Both-Used  - IRS FAN-OUT SITE 1 of 7.
    if _IS_IRS_USED(gl_block.irs_instead) or _IS_IRS_BOTH_USED(gl_block.irs_instead):
        # [:L1040] perform SPL-Posting-Open-Extend.  The maintainer's comment
        # calls the extend "needed: - bug/feature in OC".
        facade.spl_posting_open_extend(state.ctx(state.ws_irs_posting_record))
        # [:L1041-L1044] if fs-reply not = zero -> close and re-create.
        # The maintainer's comment says "wont happen in FH"; the branch is
        # reproduced anyway because it is written.
        if state.file_access.fs_reply != FsReply.SUCCESS:
            # [:L1042] perform SPL-Posting-Close.
            facade.spl_posting_close(state.ctx(state.ws_irs_posting_record))
            # [:L1043] perform SPL-Posting-Open-Output.
            # THIS DELETES EVERY ROW of PSIRSPOST-REC: acas008 implements
            # open-output as a full table delete [common/acas008.cbl:L313-L319,
            # :L571-L574]. The fallback is therefore destructive, not merely a
            # re-open.
            facade.spl_posting_open_output(state.ctx(state.ws_irs_posting_record))
    # [:L1046] if IRS-Both-Used or G-L  - IRS FAN-OUT SITE 2 of 7.
    # NOTE the different predicate shape: `IRS-Both-Used or G-L`, not
    # `irs-used or IRS-Both-Used`.
    if _IS_IRS_BOTH_USED(gl_block.irs_instead) or _IS_G_L(
        system.system_data_block.level.level_1
    ):
        # [:L1047] perform GL-Posting-Open.
        facade.gl_posting_open(state.ctx(state.ws_posting_record))
        # [:L1048-L1051] The same close-and-re-create fallback.
        if state.file_access.fs_reply != FsReply.SUCCESS:
            # [:L1049] perform GL-Posting-Close.
            facade.gl_posting_close(state.ctx(state.ws_posting_record))
            # [:L1050] perform GL-Posting-Open-Output.
            facade.gl_posting_open_output(state.ctx(state.ws_posting_record))
    # [:L1053] move Batch-start to RRN.
    # Rrn is `pic 9(5) comp` [copybooks/wsfnctn.cob:L24]; it is the posting
    # record's relative number and is incremented per posting at [:L1148].
    state.file_access.rrn = move.move_numeric(
        batch.batch_start, _ACCESS["rrn"], sending_field=_BATCH["batch-start"]
    )

    # FALL-THROUGH into this section's own exit.
    _ca997_main_exit(state)


def _ca997_main_exit(state: _Sl060State) -> None:
    """``ca997-main-exit.`` [sales/sl060.cbl:L1055] - of ``ca000-BL-Open``.

    Uniquely prefixed in the source, unlike the six ``main-exit`` labels, so the
    Python name needs no section qualification.

    # EXIT SECTION [sales/sl060.cbl:L1056]
    """
    del state


# ---------------------------------------------------------------------------
# ca000-BL-Write section.                           [sales/sl060.cbl:L1058]
#
# The maintainer's own boxed warning [:L1060-L1069] is worth carrying across
# verbatim in substance: this section writes ONE posting record per invoice to
# GL and/or IRS, so every analysis code must already carry a GL account number
# set up through sl070, and it ASSUMES the IRS/GL convention that default
# account 31 is VAT input (purchases) and 32 is VAT output (sales) - which is
# where the literal 32 at [:L1138] comes from.
# ---------------------------------------------------------------------------


def _ca000_bl_write(state: _Sl060State) -> None:
    """``ca000-BL-Write section.`` [sales/sl060.cbl:L1058] - one posting per invoice.

    Reached only from [:L535-L536] ``if G-L perform ca000-BL-Write``, once per
    OTM2 record, i.e. once per invoice rather than once per line item despite the
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

    # [:L1071] move u-date (1:6) to post-date (1:6).
    # [:L1072] move u-date (9:2) to post-date (7:2).
    # REFERENCE MODIFICATION ON BOTH SIDES, 1-BASED: an 8-character
    # `Post-Date` (DD/MM/YY) is built from the 10-character `u-date`
    # (DD/MM/CCYY) by taking "DD/MM/" and then the last two year digits. This
    # writes a GLPOSTING-REC column, so an off-by-one is diff-visible; both
    # sides go through the published primitive rather than Python slicing.
    post.post_date = move.ref_mod_into(
        post.post_date, 1, 6, move.ref_mod(state.maps03_ws.u_date, 1, 6)
    )
    post.post_date = move.ref_mod_into(
        post.post_date, 7, 2, move.ref_mod(state.maps03_ws.u_date, 9, 2)
    )
    # [:L1073] move WS-Batch-nos to Batch.
    post.ws_post_key.batch = move.move_numeric(
        batch.ws_batch_key.ws_batch_nos,
        _POST["batch"],
        sending_field=_BATCH["ws-batch-nos"],
    )
    # [:L1074] add 1 to items.  Items is `pic 99`, which is why [:L1151] can cap
    # the batch at 99 - a hundredth item would wrap the field.
    batch.items = arithmetic.add_to(
        1, receiver_value=batch.items, receiving=_BATCH["items"]
    )
    # [:L1075] move items to Post-Number.
    post.ws_post_key.post_number = move.move_numeric(
        batch.items, _POST["post-number"], sending_field=_BATCH["items"]
    )
    # [:L1076] move work-net to Post-Amount.  work-net is the five-addend total
    # built at [:L523].
    post.post_amount = move.move_numeric(
        state.work_net, _POST["post-amount"], sending_field=_WORK_NET
    )

    # [:L1078] move 1 to xx.  The STRING pointer, pre-set before the STRING at
    # [:L1091-L1094] rather than inside it.
    state.xx = move.move_numeric(1, _XX)
    # [:L1079] move oi-b-nos to k.
    # [:L1080] move oi-b-item to i.
    # BOTH ARE DEAD STORES: k and i are referenced only by the COMMENTED-OUT
    # STRING at [:L1096-L1101], which built the legend from batch/item instead of
    # folio/invoice. The moves are still executed, so they are still written.
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

    # [:L1085] move oi-invoice to m.
    # `m` is `pic z(7)9` [:L213] - an EDITED picture that suppresses leading
    # zeros to spaces but always shows the final digit. Through move_to_edited,
    # never through string formatting.
    state.m = move.move_to_edited(oi.oi_key.oi_invoice, _M)
    # [:L1086] move zero to b.
    state.b = move.move_figurative(move.ZERO, _B)
    # [:L1087] inspect m tallying b for leading space.
    state.b = move.inspect_tallying_leading(state.m, move.SPACE, state.b)
    # [:L1088] subtract b from 8 giving c.  c = 8 - b, the significant length.
    state.c = arithmetic.subtract_giving(
        state.b, minuend=8, receiving=_C
    )
    # [:L1089] add 1 to b.  b becomes the 1-based offset of the first digit.
    state.b = arithmetic.add_to(1, receiver_value=state.b, receiving=_B)

    # [:L1091-L1094] string m (b:c) delimited by size
    #                       " : "   delimited by size
    #                       sales-name delimited by size
    #                          into Post-Legend pointer xx.
    # THE EDITED-MOVE + INSPECT + STRING CHAIN. The three sources can total 41
    # characters (8 + 3 + 30) into a 32-character receiver, so the tail is lost
    # without an ON OVERFLOW clause to notice.
    # NOTE ALSO that STRING OVERLAYS FROM THE POINTER and does NOT clear the
    # receiver: whatever a previous invoice left in Post-Legend beyond the
    # characters written this time SURVIVES into this posting row. Reproduced by
    # threading the receiver's current text through the primitive rather than
    # starting from spaces.
    # AMBIGUITY Q-7 [sales/sl060.cbl:L1091-L1094] - the exact Post-Legend bytes,
    # including any residue from a longer preceding legend and the truncation
    # point when name plus invoice exceeds 32 characters, must be measured
    # against the compiled oracle.
    # DO NOT UNIFY with sl100, which builds the SAME Post-Legend field with FIVE
    # separate STRING statements sharing one pointer
    # [sales/sl100.cbl:L622, :L624, :L626, :L627, :L628].
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

    # [:L1103] move S-Debtors to Post-DR.
    post.post_dr = move.move_numeric(
        system.sales_ledger_block.s_debtors,
        _POST["post-dr"],
        sending_field=_SYSTEM["s-debtors"],
    )
    # [:L1104] move SL-Sales-AC to Post-CR.
    post.post_cr = move.move_numeric(
        system.sales_ledger_block.sl_sales_ac,
        _POST["post-cr"],
        sending_field=_SYSTEM["sl-sales-ac"],
    )

    # [:L1106-L1109] move zero to dr-pc cr-pc vat-pc vat-amount.  Four receivers.
    # ANOMALY A-18 [sales/sl060.cbl:L1106-L1109] - DR-PC and CR-PC ARE SET TO
    # ZERO HERE AND NEVER GIVEN A VALUE ANYWHERE ELSE, and they are not carried
    # into the IRS posting record at [:L1126-L1143] either. The maintainer flags
    # the concern five times: at [:L1123-L1124] "The postings for GL NEEDS TO BE
    # CHECKED if it is used etc . 05/10/25 and usage of DR-PC and CR-PC", at
    # [:L1133] "Missing usage of DR-PC for GL MUST be checked in GL ????", at
    # [:L1135] the same for CR-PC, and at [:L1139] "*> IS IT ???" against the
    # two-receiver `move 32`. The AAP cites [:L1122-L1126] for this; the flags
    # measured in the source are at the lines just named.
    # Reproduced deliberately per R-4; DO NOT FIX - the two columns stay zero in
    # GLPOSTING-REC and have no IRS counterpart at all.
    (post.dr_pc, post.cr_pc, post.vat_pc, post.vat_amount) = move.move_to_all(
        move.ZERO,
        (_POST["dr-pc"], _POST["cr-pc"], _POST["vat-pc"], _POST["vat-amount"]),
    )

    # [:L1111-L1112] move VAT-AC of system-record to VAT-AC of WS-Posting-Record
    # FINDING 11 [sales/sl060.cbl:L1111-L1112] - A QUALIFIED REFERENCE, the
    # field-name-collision pattern the AAP records only for gl070 (anomaly A-21).
    # `VAT-AC` is declared in BOTH the system record and the posting record, so
    # the program must say which it means. The qualification is kept visible in
    # the Python by naming both owners in the expression.
    # NOTE ALSO that this MOVE has NO TERMINATING PERIOD ([:L1113] is a comment
    # and [:L1114] is the next statement, which does carry one). Unlike A-1 at
    # [:L1176] this is HARMLESS - neither statement is conditional, so the two
    # simply form one sentence - and it is recorded here only so that a reader
    # auditing missing periods can see that this one was checked and dismissed.
    post.vat_ac = move.move_numeric(
        gl_block.vat_ac,  # VAT-AC OF SYSTEM-RECORD
        _POST["vat-ac"],  # VAT-AC OF WS-POSTING-RECORD
        sending_field=_SYSTEM["vat-ac"],
    )

    # [:L1114] add oi-vat oi-e-vat oi-c-vat to vat-amount.
    # THREE SOURCES into ONE receiver, which already holds zero from [:L1109].
    post.vat_amount = arithmetic.add_to(
        money.oi_vat,
        money.oi_e_vat,
        money.oi_c_vat,
        receiver_value=post.vat_amount,
        receiving=_POST["vat-amount"],
    )
    # [:L1115] move "CR" to Post-Vat-Side.
    post.post_vat_side = move.move_alphanumeric("CR", _POST["post-vat-side"])
    # [:L1116] move "SL" to Post-Code in WS-Posting-Record.
    # FINDING 11 again - `Post-Code` is declared in both posting records, so the
    # source qualifies it and so does this comment.
    post.post_code = move.move_alphanumeric("SL", _POST["post-code"])

    # [:L1118-L1121] The four control-total accumulations, as four separate
    # statements. sl060 writes the INPUT pair and the ACTUAL pair IDENTICALLY,
    # which is why AAP section 0.6.4 records that Sales and Purchase batches
    # balance by construction and the control-total-mismatch scenario is
    # General-Ledger-specific. All four fields are UNSIGNED `pic 9(9)v99 comp-3`
    # [copybooks/wsbatch.cob:L41-L44], the same fields gl051's gate later
    # compares.
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

    # [:L1126] if irs-used or IRS-Both-Used  - IRS FAN-OUT SITE 3 of 7.
    if _IS_IRS_USED(gl_block.irs_instead) or _IS_IRS_BOTH_USED(gl_block.irs_instead):
        # ELEVEN MOVES build the IRS posting record from the GL one. Counted and
        # listed so that A-18's omission is provably an omission: batch,
        # post-number, post-code, post-date, post-DR, post-CR, post-amount,
        # post-legend, vat-ac-def/Vat-PC, post-vat-side, vat-amount. NEITHER
        # dr-pc NOR cr-pc appears.
        # [:L1127] move Batch to WS-IRS-Batch.
        irs_post.ws_irs_post_key.ws_irs_batch = move.move_numeric(
            post.ws_post_key.batch,
            _IRSPOST["ws-irs-batch"],
            sending_field=_POST["batch"],
        )
        # [:L1128] move Post-Number to WS-IRS-Post-Number.
        irs_post.ws_irs_post_key.ws_irs_post_number = move.move_numeric(
            post.ws_post_key.post_number,
            _IRSPOST["ws-irs-post-number"],
            sending_field=_POST["post-number"],
        )
        # [:L1129-L1130] move Post-Code in WS-Posting-Record to WS-IRS-Post-Code.
        # FINDING 11 - the third qualified reference in this section.
        irs_post.ws_irs_post_code = move.move_alphanumeric(
            post.post_code,  # POST-CODE IN WS-POSTING-RECORD
            _IRSPOST["ws-irs-post-code"],
        )
        # [:L1131] move post-date to WS-IRS-post-date.
        irs_post.ws_irs_post_date = move.move_alphanumeric(
            post.post_date, _IRSPOST["ws-irs-post-date"]
        )
        # [:L1132] move Post-DR to WS-IRS-Post-DR.
        # FINDING 12 [sales/sl060.cbl:L1132] - A NARROWING MOVE NOBODY FLAGGED.
        # Post-DR is `pic 9(6)` [copybooks/wspost.cob:L19] but WS-IRS-Post-DR is
        # `pic 9(5)` [copybooks/wspost-irs.cob:L19], so a six-digit GL account
        # number LOSES ITS HIGH-ORDER DIGIT on the way to the IRS posting row.
        # The same applies to Post-CR at [:L1134] and, with ten digits into nine,
        # to Post-Amount at [:L1136] and Vat-Amount at [:L1141]. Left as written
        # (R-3); the truncation comes from the receiving descriptor.
        # AMBIGUITY Q-5 [sales/sl060.cbl:L1132, :L1134, :L1136, :L1141] - WHAT
        # THE NARROWING MOVES ACTUALLY STORE. High-order truncation on a MOVE is
        # well defined, but three details are not settled by reading: whether
        # six-digit control accounts occur in practice, what the bridge does with
        # the SIGN LEADING form of WS-IRS-Post-Amount
        # [copybooks/wspost-irs.cob:L21] when the value came from a
        # TRAILING-signed field, and therefore what PSIRSPOST-REC holds. Measure
        # against the compiled oracle.
        irs_post.ws_irs_post_dr = move.move_numeric(
            post.post_dr, _IRSPOST["ws-irs-post-dr"], sending_field=_POST["post-dr"]
        )
        # [:L1133] "*> Missing usage of DR-PC for GL MUST be checked in GL ????"
        # - the maintainer's flag, and half of A-18.
        # [:L1134] move Post-CR to WS-IRS-Post-CR.
        irs_post.ws_irs_post_cr = move.move_numeric(
            post.post_cr, _IRSPOST["ws-irs-post-cr"], sending_field=_POST["post-cr"]
        )
        # [:L1135] "*> Missing usage of CR-PC ..." - the other half of A-18.
        # [:L1136] move Post-Amount to WS-IRS-Post-Amount.  s9(8)v99 -> s9(7)v99,
        # and the IRS field's sign is LEADING [copybooks/wspost-irs.cob:L21].
        irs_post.ws_irs_post_amount = move.move_numeric(
            post.post_amount,
            _IRSPOST["ws-irs-post-amount"],
            sending_field=_POST["post-amount"],
        )
        # [:L1137] move Post-Legend to WS-IRS-Post-Legend.
        irs_post.ws_irs_post_legend = move.move_alphanumeric(
            post.post_legend, _IRSPOST["ws-irs-post-legend"]
        )
        # [:L1138-L1139] move 32 to WS-IRS-vat-ac-def
        #                          Vat-PC         *> IS IT ???
        # ONE MOVE, TWO RECEIVERS IN DIFFERENT RECORDS: the literal 32 - the
        # convention's VAT output-tax default account - lands in the IRS record's
        # account-default field AND in the GL posting record's VAT PERCENTAGE
        # field. An account number in a percentage field is what the maintainer's
        # "*> IS IT ???" is asking about, and it is the only value Vat-PC ever
        # receives other than the zero at [:L1108]. Part of A-18.
        # Reproduced deliberately per R-4; DO NOT FIX.
        (irs_post.ws_irs_vat_ac_def, post.vat_pc) = move.move_to_all(
            32, (_IRSPOST["ws-irs-vat-ac-def"], _POST["vat-pc"])
        )
        # [:L1140] move Post-Vat-Side to WS-IRS-Post-Vat-Side.
        irs_post.ws_irs_post_vat_side = move.move_alphanumeric(
            post.post_vat_side, _IRSPOST["ws-irs-post-vat-side"]
        )
        # [:L1141] move Vat-Amount to WS-IRS-vat-amount.
        irs_post.ws_irs_vat_amount = move.move_numeric(
            post.vat_amount,
            _IRSPOST["ws-irs-vat-amount"],
            sending_field=_POST["vat-amount"],
        )
        # [:L1142] perform SPL-Posting-Write.
        facade.spl_posting_write(state.ctx(state.ws_irs_posting_record))

    # [:L1144-L1145] if IRS-Both-Used or G-L  - IRS FAN-OUT SITE 4 of 7.
    if _IS_IRS_BOTH_USED(gl_block.irs_instead) or _IS_G_L(
        system.system_data_block.level.level_1
    ):
        # [:L1146] move RRN to WS-Post-RRN.  Both `pic 9(5)`.
        post.ws_post_rrn = move.move_numeric(
            state.file_access.rrn,
            _POST["ws-post-rrn"],
            sending_field=_ACCESS["rrn"],
        )
        # [:L1147] perform GL-Posting-Write.
        facade.gl_posting_write(state.ctx(state.ws_posting_record))
        # [:L1148] add 1 to RRN.  Only advanced when a GL posting was written, so
        # in IRS-only-through-both mode the mark still moves, and in pure IRS
        # mode this section is unreachable anyway.
        state.file_access.rrn = arithmetic.add_to(
            1, receiver_value=state.file_access.rrn, receiving=_ACCESS["rrn"]
        )

    # [:L1151-L1153] if items = 99 perform ca000-BL-Close / perform ca000-BL-Open.
    # THE 99-ITEM BATCH CAP, and a real control structure with real table
    # effects: closing writes the batch header (an extra GLBATCH-REC row) and
    # opening claims the next batch number, so a run of 250 invoices produces
    # three batches rather than one. This is NOT recursion into BL-Write - the
    # two sections it performs never call back into this one.
    if arithmetic.compare(batch.items, 99) == 0:
        _ca000_bl_close(state)
        _ca000_bl_open(state)

    # FALL-THROUGH into this section's own exit.
    _ca998_main_exit(state)


def _ca998_main_exit(state: _Sl060State) -> None:
    """``ca998-main-exit.`` [sales/sl060.cbl:L1155] - of ``ca000-BL-Write``.

    # EXIT SECTION [sales/sl060.cbl:L1156]
    """
    del state


# ---------------------------------------------------------------------------
# ca000-BL-Close section.                           [sales/sl060.cbl:L1158]
# ---------------------------------------------------------------------------


def _ca000_bl_close(state: _Sl060State) -> None:
    """``ca000-BL-Close section.`` [sales/sl060.cbl:L1158] - write and close the batch.

    Two anomalies live in these twenty lines: A-17's write end at [:L1173] and
    A-1's missing period at [:L1176].
    """
    system = state.system_record
    gl_block = system.general_ledger_block

    # [:L1161] perform GL-Batch-Write.
    facade.gl_batch_write(state.ctx(state.ws_batch_record))
    # [:L1162-L1171] if fs-reply not = zero -> report and, unless unattended,
    # pause. A DIAGNOSTIC WITH NO CONTROL TRANSFER: the batch header failed to
    # write, and the program neither retries it nor abandons the run, so the
    # posting rows this batch wrote stay in GLPOSTING-REC with no batch header to
    # match. That is a rejection class with a PARTIAL DATABASE EFFECT and it is
    # preserved exactly (R-3 forbids adding the retry or the abort).
    # AMBIGUITY Q-8 [sales/sl060.cbl:L1162] - the disposition of a failed
    # GL-Batch-Write, and of the failed OTM3-Write at [:L590], must be measured
    # against the compiled oracle: both leave the database partly written.
    if state.file_access.fs_reply != FsReply.SUCCESS:
        # [:L1163-L1166] The displays become one log record; zz040 supplies the
        # message text and must not alter control flow.
        _zz040_evaluate_message(state)
        _LOG.error(
            "%s%02d %s", _SL132, state.file_access.fs_reply, state.ws_eval_msg
        )
        # [:L1167-L1170] The unattended-mode test is kept; the pause is dropped.
        if state.ws_calling_data.ws_caller.strip() != "xl150":
            _LOG.error("%s", _SL002)

    # ANOMALY A-17 [sales/sl060.cbl:L1172-L1173] - THE UNEXPLAINED MOVE.
    #     if       IRS-Both-Used OR G-L    *> THIS IS IN PURCHASE PL060
    #              move     RRN  to  postings.     *> Why ?
    # The maintainer's own `*> Why ?` is on the move and his `*> THIS IS IN
    # PURCHASE PL060` is on the condition. It is NOT inert: `postings` is the
    # SYSTEM-REC posting-RRN high-water mark that [:L1037] reads back to
    # allocate the next batch's Batch-Start, so this statement is what makes GL
    # posting RRNs continue across runs instead of restarting.
    # Reproduced deliberately per R-4; DO NOT FIX.
    # AMBIGUITY Q-9 [sales/sl060.cbl:L1173] - `Rrn` is `pic 9(5) comp`, range 0
    # to 99999, while `Postings` is `binary-short`, range -32768 to 32767. An
    # RRN above 32767 therefore WRAPS NEGATIVE on this move (99999 stores as
    # -31073 through the published primitive). AAP section 0.6.8 already makes
    # this move's observable effect an oracle question; the wrap is the specific
    # value that must be measured.
    # IRS FAN-OUT SITE 5 of 7 - predicate shape `IRS-Both-Used OR G-L`.
    if _IS_IRS_BOTH_USED(gl_block.irs_instead) or _IS_G_L(
        system.system_data_block.level.level_1
    ):
        gl_block.postings = move.move_numeric(
            state.file_access.rrn,
            _SYSTEM["postings"],
            sending_field=_ACCESS["rrn"],
        )

    # [:L1174] perform GL-Batch-Close.
    # UNCONDITIONAL: the period on [:L1173] closed the `if` above it.
    facade.gl_batch_close(state.ctx(state.ws_batch_record))

    # ANOMALY A-1 [sales/sl060.cbl:L1172-L1178] - THE MISSING TERMINATING PERIOD.
    # The source reads:
    #     1175      if       IRS-Used OR IRS-Both-Used
    #     1176               perform SPL-Posting-Close      *>  close irs-post-file
    #     1177      if       IRS-Both-Used or G-L
    #     1178               perform GL-Posting-Close.       *>    close posting-file.
    # THE DEFECT IS THE ABSENCE OF A PERIOD AFTER `perform SPL-Posting-Close` ON
    # LINE 1176 - not a missing END-IF and not a wrong condition. Because [:L1176]
    # is unterminated, the `if` on [:L1177] is a NESTED conditional inside the
    # `if` on [:L1175], and the single period on [:L1178] closes both. The
    # effective structure is exactly the nesting written below.
    # CONSEQUENCE: in PURE-GL MODE (`G-L` true, `IRS-Used` false,
    # `IRS-Both-Used` false) the OUTER condition is FALSE, so GL-Posting-Close IS
    # NEVER EXECUTED and the GL posting file is left open by this section.
    # The three sibling programs ALL HAVE THE PERIOD - [purchase/pl060.cbl:L1031],
    # [sales/sl100.cbl:L694], [purchase/pl100.cbl:L675] - which proves this is an
    # accident rather than an idiom.
    # Reproduced deliberately per R-4; DO NOT FIX. DO NOT ADD THE PERIOD, i.e. do
    # not lift the inner `if` out to this function's top level.
    # IRS FAN-OUT SITE 6 of 7 - predicate shape `IRS-Used OR IRS-Both-Used`.
    if _IS_IRS_USED(gl_block.irs_instead) or _IS_IRS_BOTH_USED(gl_block.irs_instead):
        # [:L1176] perform SPL-Posting-Close.
        facade.spl_posting_close(state.ctx(state.ws_irs_posting_record))
        # IRS FAN-OUT SITE 7 of 7 - predicate shape `IRS-Both-Used or G-L`, and
        # NESTED here rather than sibling, which is the whole of A-1.
        # [:L1177] if IRS-Both-Used or G-L
        if _IS_IRS_BOTH_USED(gl_block.irs_instead) or _IS_G_L(
            system.system_data_block.level.level_1
        ):
            # [:L1178] perform GL-Posting-Close.
            facade.gl_posting_close(state.ctx(state.ws_posting_record))

    # FALL-THROUGH into this section's own exit.
    _ca999_main_exit(state)


def _ca999_main_exit(state: _Sl060State) -> None:
    """``ca999-main-exit.`` [sales/sl060.cbl:L1180] - of ``ca000-BL-Close``.

    # EXIT SECTION [sales/sl060.cbl:L1181]
    """
    del state



# ---------------------------------------------------------------------------
# zz040-Evaluate-Message Section.                   [sales/sl060.cbl:L1183]
# ---------------------------------------------------------------------------


def _zz040_evaluate_message(state: _Sl060State) -> None:
    """``zz040-Evaluate-Message Section.`` [:L1183] - name the file-status code.

    The section's whole body is a ``COPY`` of the shared status table with the
    two placeholders bound to this program's own field names [:L1186-L1187]::

        copy "FileStat-Msgs.cpy" replacing MSG by ws-Eval-Msg
                                           STATUS by fs-reply.

    DIAGNOSTIC ONLY: it sets ``ws-Eval-Msg`` and alters no control flow and no
    table, so its output reaches a log record and never a dump.

    NOTE THE NAME. This program calls the section ``zz040-Evaluate-Message``;
    ``pl060`` and ``gl080`` call theirs plain ``Evaluate-Message`` and
    ``sl100``/``pl100`` call theirs ``Eval-Status``. Each program keeps its own
    spelling so that traceability reads the same in both directions.
    """
    # [:L1186-L1187] The 35-arm EVALUATE, held as a mapping keyed on fs-reply.
    state.ws_eval_msg = _file_status_message(state)

    # FALL-THROUGH into this section's own exit.
    _eval_msg_exit(state)


def _eval_msg_exit(state: _Sl060State) -> None:
    """``Eval-Msg-Exit.`` [sales/sl060.cbl:L1189] - of ``zz040-Evaluate-Message``.

    Written on ONE LINE with its statement in the source - ``Eval-Msg-Exit.
    exit section.`` - unlike every other exit label in the program.

    # EXIT SECTION [sales/sl060.cbl:L1189]
    """
    del state


# ---------------------------------------------------------------------------
# The four date sections.                    [sales/sl060.cbl:L1192-L1298]
#
# All four bodies live in `acas_posting/dates.py`, which is the ONE place in
# this migration where consolidation is unambiguously safe: the bodies are
# textually equivalent across their carriers, so a single implementation is a
# faithful rendering rather than a normalisation. The program keeps a named
# function per section (R-5) that binds the program's own working storage to
# the consolidated body and stores the possibly-defaulted `Date-Form` back.
#
# THREE CARRIER-SPECIFIC FACTS, each verified rather than assumed:
#
#  1. `zz050-Validate-Date` is NOT one body across the repository. gl051's
#     copy carries three extra `inspect ... replacing` statements
#     [general/gl051.cbl:L1178-L1180] that sl060 omits entirely, so
#     `dates` publishes two variants and this program must call
#     `zz050_validate_date` - NOT `zz050_validate_date_gl051`.
#  2. `zz060-Convert-Date` is identical in all six carriers EXCEPT ONE TOKEN:
#     sl060 performs `maps04` [:L1236] where gl051 and gl070 perform `maps03`.
#     The consolidated body takes the wrapper as a parameter, so passing
#     `_maps04` selects this program's spelling.
#  3. ANOMALY A-22 DOES NOT OCCUR IN THIS PROGRAM. A-22 is the wrapper section
#     whose name and exit label disagree, and it is confined to gl070
#     (`maps03` section at :L603 with `maps04-exit` at :L608) and gl051
#     (`maps03` at :L1273 with `maps04-exit` at :L1278). Here the section is
#     `maps04` [:L1292] and its exit is `maps04-exit` [:L1297] - THE NAMES
#     AGREE - so there is nothing to reproduce and nothing to log.
#
# `zz050-Validate-Date` IS DEAD CODE in sl060: no statement anywhere in the
# program performs it, because sl060 accepts no date from an operator - the
# run date arrives through linkage. It is retained because R-5 traces
# declarations, and because removing it would make the program's section
# inventory disagree with its three sibling carriers.
# ---------------------------------------------------------------------------


def _zz050_validate_date(state: _Sl060State) -> None:
    """``zz050-Validate-Date section.`` [:L1192] - operator input to UK order.

    Reads ``ws-test-date``, reorders it out of USA or International
    presentation into UK order, and validates it through the date module, which
    leaves ``u-bin`` non-zero only if the date is valid.

    DEAD CODE in this program - see the block comment above - but reproduced in
    full because the declaration exists.

    # GO TO class 3 [sales/sl060.cbl:L1205] - `if Date-UK go to zz050-test-date`.
    # GO TO class 3 [sales/sl060.cbl:L1210] - the same after the USA day/month
    # swap. Both transfer to the section's shared tail rather than to its exit,
    # and both are realised inside ``dates.zz050_validate_date``, which owns the
    # body; classified 3 because each ends this section's own straight-line work.
    """
    block = state.system_record.system_data_block
    # [:L1201-L1222] The consolidated body: ws-test-date to ws-date, the
    # Date-Form default at [:L1202-L1203], the UK short-circuit, the USA
    # day/month swap, the International rebuild by reference modification, and
    # then zz050-test-date's move to u-date, zeroing of u-bin and perform of the
    # wrapper.
    # THE NON-gl051 VARIANT: no separator normalisation here.
    block.date_form = dates.zz050_validate_date(
        state.ws_date_formats,
        state.maps03_ws,
        block.date_form,
        wrapper=_maps04,
    )

    # FALL-THROUGH into this section's own exit.
    _zz050_exit(state)


def _zz050_test_date(state: _Sl060State) -> None:
    """``zz050-test-date.`` [sales/sl060.cbl:L1219] - the shared tail of zz050.

    The target of both class-3 transfers in ``zz050-Validate-Date`` and also
    reached by fall-through from [:L1217]. Its three statements - ``move ws-date
    to u-date`` [:L1220], ``move zero to u-bin`` [:L1221] and ``perform maps04``
    [:L1222] - are executed inside ``dates.zz050_validate_date``, which is why
    this function exists as a traceable declaration rather than as a second
    implementation of them.

    THE ZEROING AT [:L1221] IS LOAD-BEARING: the date module leaves its output
    field UNTOUCHED when it rejects a date [common/maps04.cbl:L146, :L154], so
    the documented "errors return zero" contract holds only because callers
    pre-zero, exactly as this paragraph does.
    """
    dates.zz050_test_date(
        state.ws_date_formats, state.maps03_ws, wrapper=_maps04
    )


def _zz050_exit(state: _Sl060State) -> None:
    """``zz050-exit.`` [sales/sl060.cbl:L1224] - of ``zz050-Validate-Date``.

    # EXIT SECTION [sales/sl060.cbl:L1225]
    """
    del state


def _zz060_convert_date(state: _Sl060State) -> None:
    """``zz060-Convert-Date section.`` [:L1227] - binary day number to text.

    Called from the posting loop at [:L506] with the invoice date already moved
    into ``u-bin`` [:L505], and produces ``ws-date`` in the configured
    presentation format. When the day number is invalid the date module returns
    spaces and this section propagates spaces [:L1237-L1239] rather than
    failing.

    # GO TO class 3 [sales/sl060.cbl:L1239] - the invalid-date escape.
    # GO TO class 3 [sales/sl060.cbl:L1245] - the UK short-circuit.
    # GO TO class 3 [sales/sl060.cbl:L1250] - after the USA day/month swap.
    # All three transfer to ``zz060-Exit`` and all three are realised inside
    # ``dates.zz060_convert_date``.
    """
    block = state.system_record.system_data_block
    # [:L1236] perform maps04 - THE ONE TOKEN THAT DIFFERS from gl051's and
    # gl070's copies of this section, which perform maps03. Selected by the
    # wrapper argument.
    block.date_form = dates.zz060_convert_date(
        state.ws_date_formats,
        state.maps03_ws,
        block.date_form,
        wrapper=_maps04,
    )

    # FALL-THROUGH into this section's own exit.
    _zz060_exit(state)


def _zz060_exit(state: _Sl060State) -> None:
    """``zz060-Exit.`` [sales/sl060.cbl:L1259] - of ``zz060-Convert-Date``.

    # EXIT SECTION [sales/sl060.cbl:L1260]
    """
    del state


def _zz070_convert_date(state: _Sl060State) -> None:
    """``zz070-Convert-Date section.`` [:L1262] - the run date to text.

    Reformats the ``to-day`` linkage parameter - the FIRST of the two observables
    the controlled clock pins - into the configured presentation format. It calls
    no date module at all, so it cannot fail.

    BYTE-IDENTICAL IN ALL TEN CARRIERS, which is why ``dates`` publishes one body
    that takes ``to_day`` directly rather than through ``maps03-ws``.

    # GO TO class 3 [sales/sl060.cbl:L1275] - the UK short-circuit.
    # GO TO class 3 [sales/sl060.cbl:L1280] - after the USA day/month swap.
    # Both transfer to ``zz070-Exit`` and both are realised inside
    # ``dates.zz070_convert_date``.
    """
    block = state.system_record.system_data_block
    # [:L1270-L1287] to-day to ws-date, the Date-Form default, the UK
    # short-circuit, the USA day/month swap and the International rebuild.
    block.date_form = dates.zz070_convert_date(
        state.ws_date_formats, state.to_day, block.date_form
    )

    # FALL-THROUGH into this section's own exit.
    _zz070_exit(state)


def _zz070_exit(state: _Sl060State) -> None:
    """``zz070-Exit.`` [sales/sl060.cbl:L1289] - of ``zz070-Convert-Date``.

    # EXIT SECTION [sales/sl060.cbl:L1290]
    """
    del state


def _maps04(maps03_ws: Maps03Ws) -> None:
    """``maps04 section.`` [sales/sl060.cbl:L1292] - the date-module wrapper.

    Its entire body is one statement [:L1295]::

        call     "maps04"  using  maps03-ws.

    R-1 forbids invoking the COBOL program, so the call is satisfied by
    ``dates.maps04``, which is the full reimplementation of
    ``common/maps04.cbl`` including its 1600-12-31 ordinal epoch, its six-part
    reject test and - critically - its behaviour of LEAVING THE OUTPUT FIELD
    UNTOUCHED on rejection.

    Takes the interface block rather than the program state because that is
    exactly what the COBOL statement passes, and because it lets this function
    be handed straight to the consolidated date bodies as their wrapper.

    A-22 DOES NOT OCCUR HERE: this section is named ``maps04`` and its exit
    label is ``maps04-exit`` [:L1297], so the two AGREE. The anomaly is confined
    to gl070 and gl051.
    """
    dates.maps04(maps03_ws)

    # FALL-THROUGH into this section's own exit.
    _maps04_exit(maps03_ws)


def _maps04_exit(maps03_ws: Maps03Ws) -> None:
    """``maps04-exit.`` [sales/sl060.cbl:L1297] - of the ``maps04`` section.

    # EXIT SECTION [sales/sl060.cbl:L1298]
    """
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
# Required by R-5 (full traceability) and by AAP section 0.4.3, which directs
# that deliberate omissions be "recorded as omissions so that a reader
# comparing the two files does not conclude something was lost". Everything
# below is measured against the frozen source, not inferred: the label census
# was taken by matching COBOL label lines across [sales/sl060.cbl:L395-L1301],
# and the transfer census by matching every `go to`, `exit section` and
# `exit program` in the same range.
#
# 1. PROGRAM -> MODULE
#    sales/sl060.cbl (1301 lines, whole program in scope)
#        -> acas_posting/programs/sl060_invoice_posting.py
#    Public API: `run` only. `__all__ == ("run",)`; every other module-level
#    name is underscore-private, because AAP section 0.3.3 requires that
#    "callers cannot reach into a program's internals, exactly as a COBOL CALL
#    cannot".
#
# 2. LINKAGE -> SIGNATURE                       [sales/sl060.cbl:L395-L399]
#        procedure division using ws-calling-data
#                                 system-record
#                                 system-record-4
#                                 to-day
#                                 file-defs.
#    -> run(ws_calling_data, system_record, system_record_4, to_day, file_defs)
#    The SL/PL five-parameter shape. The third parameter is spelled
#    `system-record-4` in the source and comes from `copy "wssys4.cob"` [:L393].
#    Not the GL four-parameter shape, and not the IRS three-parameter shape.
#
# 3. LABEL -> FUNCTION.  45 LABELS, 45 FUNCTIONS: 17 sections and 28
#    paragraphs. AAP section 0.4.2's inventory for sl060 is accurate for the
#    section heads but omits the three `ca99x-main-exit` labels, `Eval-Msg-Exit`
#    and several paragraph exits; the census below is the measured one.
#
#      L  402  aa000-Main-Process section.       _aa000_main_process
#      L  483  aa020-Read-Loop.                  _aa020_read_loop
#      L  612  aa030-Main-End.                   _aa030_main_end
#      L  661  aa040-End-Loop.                   _aa040_end_loop
#      L  676  aa050-End-Loop-End.               _aa050_end_loop_end
#      L  722  aa999-Exit-Prog.                  _aa999_exit_prog
#      L  725  ba000-Cr-Swop section.            _ba000_cr_swop
#      L  763  main-exit.                        _ba000_cr_swop__main_exit
#      L  766  ba000-New-Heading section.        _ba000_new_heading
#      L  789  main-exit.                        _ba000_new_heading__main_exit
#      L  792  ba000-Headings section.           _ba000_headings
#      L  813  main-exit.                        _ba000_headings__main_exit
#      L  816  ba000-Sales-Comp section.         _ba000_sales_comp
#      L  829  main-exit.                        _ba000_sales_comp__main_exit
#      L  832  ba000-Credit-Comp section.        _ba000_credit_comp
#      L  845  main-exit.                        _ba000_credit_comp__main_exit
#      L  848  ba000-CR-Notes section.           _ba000_cr_notes
#      L  864  ba010-read-loop.                  _ba010_read_loop
#      L  895  ba020-end-loop.                   _ba020_end_loop
#      L  910  ba030-main-end.                   _ba030_main_end
#      L  915  ba040-main-exit.                  _ba040_main_exit
#      L  918  ba000-Apportion section.          _ba000_apportion
#      L  960  ba000-Main-Rewrite.               _ba000_main_rewrite
#      L  965  ba000-Clear-Invoice-Deduct.       _ba000_clear_invoice_deduct
#      L  971  ba000-cid-exit.                   _ba000_cid_exit
#      L  973  main-exit.                        _ba000_apportion__main_exit
#      L  976  ba000-Analise-Deductions section. _ba000_analise_deductions
#      L 1004  ba999-main-exit.                  _ba999_main_exit
#      L 1007  ca000-BL-Open section.            _ca000_bl_open
#      L 1055  ca997-main-exit.                  _ca997_main_exit
#      L 1058  ca000-BL-Write section.           _ca000_bl_write
#      L 1155  ca998-main-exit.                  _ca998_main_exit
#      L 1158  ca000-BL-Close section.           _ca000_bl_close
#      L 1180  ca999-main-exit.                  _ca999_main_exit
#      L 1183  zz040-Evaluate-Message Section.   _zz040_evaluate_message
#      L 1189  Eval-Msg-Exit.                    _eval_msg_exit
#      L 1192  zz050-Validate-Date section.      _zz050_validate_date
#      L 1219  zz050-test-date.                  _zz050_test_date
#      L 1224  zz050-exit.                       _zz050_exit
#      L 1227  zz060-Convert-Date section.       _zz060_convert_date
#      L 1259  zz060-Exit.                       _zz060_exit
#      L 1262  zz070-Convert-Date section.       _zz070_convert_date
#      L 1289  zz070-Exit.                       _zz070_exit
#      L 1292  maps04 section.                   _maps04
#      L 1297  maps04-exit.                      _maps04_exit
#
#    SECTION-QUALIFIED NAMES ARE MANDATORY, NOT STYLISTIC. `main-exit.` is
#    declared SIX times - L763, L789, L813, L829, L845, L973 - so paragraph
#    names are not globally unique in this program and a bare `_main_exit`
#    would silently collapse six declarations into one. The `ba000-` prefix is
#    likewise shared by seven distinct sections.
#
# 4. SUPPORT FUNCTIONS (not COBOL labels; 11 plus `run`)
#    _index_descriptors            - re-key a record layout's FIELDS tree on the
#                                    COBOL name, so descriptors are LOOKED UP
#                                    from the published record modules rather
#                                    than restated here.
#    _index_published_descriptors  - the same for `sales_ledger`, which publishes
#                                    a module-level mapping instead of per-class
#                                    FIELDS tuples.
#    _dataclass_leaves             - the elementary items of a layout, used to
#                                    build and group-move OTM2 headers.
#    _initial_oi_header            - a header at its figurative initial value.
#    _group_move_oi_header         - `move oi-header to si-header` [:L851] and
#                                    `move si-header to oi-header` [:L913].
#    _new_state                    - bind linkage, build the record areas.
#    _add_to_turnover_quarter      - the OCCURS-4 subscripted add at [:L545,
#                                    :L551, :L558]; see STRUCTURAL NOTE 5.
#    _initialize_ws_sales_record   - `initialize WS-Sales-Record with filler`
#                                    [:L497], through the published primitive.
#    _oi_customer_image            - the seven-byte `oi-customer` group image.
#    _write_oi3_customer           - the reverse, for the two START keys.
#    _file_status_message          - the `FileStat-Msgs.cpy` table [:L1186].
#
# 5. GO TO CENSUS - 22 SITES, ALL ANNOTATED AT THE SITE.  Classified BY SHAPE,
#    not by matching the AAP's label list, which is explicitly not exhaustive.
#    15 sites are realised in this module; the 7 class-3 sites are realised
#    inside `acas_posting/dates.py`, which owns the consolidated date bodies,
#    and are annotated in the docstrings of the sections that declare them.
#
#    CLASS 1 - loop-back, becomes `continue` inside `while True:`  (6 sites)
#      L 610 -> aa020-Read-Loop      the Phase-1 posting loop
#      L 669 -> aa040-End-Loop       skip a closed item
#      L 674 -> aa040-End-Loop       the Phase-2 loop tail
#      L 873 -> ba010-read-loop      skip a non-type-2 item
#      L 878 -> ba010-read-loop      skip a closed item
#      L 893 -> ba010-read-loop      the credit note still has value
#
#    CLASS 2 - forward terminator, becomes `break` PLUS the post-loop block
#              faithfully placed  (7 sites)
#      L 485 -> aa030-Main-End       OTM2 at end
#      L 664 -> aa050-End-Loop-End   OTM3 at end
#      L 858 -> ba020-end-loop       the first START failed
#      L 869 -> ba020-end-loop       OTM3 at end
#      L 876 -> ba020-end-loop       a different customer
#      L 900 -> ba030-main-end       nothing left to apply, or pass two done
#      L 907 -> ba030-main-end       the second START failed
#    AAP section 0.6.3, verbatim, on this class: "the target label is followed
#    by real work - closing files, printing totals, rewriting a control record -
#    so the transformation is `break` PLUS faithful placement of that work after
#    the loop, not `break` alone. Mis-splitting here would silently drop
#    end-of-run processing." HERE THAT WORK IS: the three closes [:L613-L615],
#    the three total-group blocks, PERIOD TOTAL 3 [:L641], the deductions
#    analysis [:L643-L647], `ca000-BL-Close` [:L649-L650], the OTM2 truncation
#    [:L677-L678], PERIOD TOTAL 4 [:L700] and the remaining closes. Mis-splitting
#    would drop TWO OF THE NINE SYSTOT-REC writes in the whole migration.
#
#    CLASS 3 - section exit, becomes `return`  (7 sites, all inside `dates`)
#      L1205, L1210 -> zz050-test-date  (the shared tail of zz050)
#      L1239, L1245, L1250 -> zz060-Exit
#      L1275, L1280 -> zz070-Exit
#
#    CLASS 4 - sibling re-dispatch, becomes a named call plus an explicit
#              transfer; per-site proof required  (2 sites)
#
#      L 908 -> ba010-read-loop, FROM INSIDE ba020-end-loop.
#        PROOF. `ba020-end-loop` is reached as a class-2 terminator from three
#        sites, and its own last statement transfers BACKWARD into the loop it
#        terminates. So it is simultaneously a terminator and a re-dispatcher:
#        having set `first-pass` to "N" [:L901], rebuilt the key from the SAVED
#        header [:L902-L903] and repositioned the cursor [:L904-L905], it runs
#        the read loop A SECOND TIME over the same customer's open items - the
#        first pass applying only to the invoice the credit note names
#        [:L888], the second to any invoice [:L889]. The equivalent shape is an
#        OUTER loop whose body dispatches on a label value: `_ba010_read_loop`
#        and `_ba020_end_loop` each RETURN the label they transfer to, and
#        `_ba000_cr_notes` loops until that label is `ba030-main-end`.
#        Equivalence holds because (a) the only backward edge is this one, (b)
#        `first-pass` is monotone "Y"->"N" so the outer loop runs at most twice,
#        and (c) the guard at [:L898-L900] is exactly the condition under which
#        no further pass is taken. NOT collapsed into one pass: the two passes
#        apply DIFFERENT matching rules and both mutate OTM3.
#
#      L 928 -> ba000-Main-Rewrite, FROM INSIDE ba000-Apportion.
#        PROOF. The target is a sibling PARAGRAPH of the same section that
#        performs work - `perform OTM3-Rewrite` [:L962] - and then itself
#        transfers control with `exit section` [:L963]. The equivalent is
#        therefore a CALL to the named paragraph followed by a RETURN. It is not
#        a bare `return`, because the rewrite must happen; and not a
#        fall-through, because [:L930] onward must NOT run - in particular
#        `ba000-Clear-Invoice-Deduct` must not, so an already-settled invoice
#        does not take a second settlement deduction off `sales-current`.
#
# 6. EXIT SECTION / EXIT PROGRAM CENSUS - NOT `GO TO`s, annotated separately.
#    21 sites. Four are called out by name because they are behavioural rather
#    than merely terminal:
#      L 723  `exit program.`  FINDING 7 - see below.
#      L 931  mid-flow `exit section` in ba000-Apportion: an OVERPAID invoice
#             leaves with NO REWRITE at all.
#      L 983  mid-flow `exit section` in ba000-Analise-Deductions: no analysis
#             row for the specific code, so neither block runs.
#      L 996  mid-flow `exit section` in the same section: the SECOND read
#             failed, so the FIRST block's rewrite has ALREADY happened - a
#             partial effect, not a no-op.
#    Also mid-flow: L 963 in ba000-Main-Rewrite, which is what makes
#    ba000-cid-exit and its following main-exit dead labels.
#    Terminal: L 764, 790, 814, 830, 846, 916, 974, 1005, 1056, 1156, 1181,
#    1189, 1225, 1260, 1290, 1298.
#
# 7. PERFORM ... THRU
#    DOES NOT OCCUR IN sl060. The four in-scope sites repository-wide are
#    [general/gl072.cbl:L300], [general/gl072.cbl:L304], [sales/sl100.cbl:L344]
#    and [purchase/pl100.cbl:L336]. Nothing to transform here.
#
# 8. FALL-THROUGH CENSUS.  The two the brief names, plus the section-into-exit
#    fall-throughs which are recorded at each site.
#      L 659 -> L 661   aa030-Main-End falls through into aa040-End-Loop. There
#                       is no transfer at the end of aa030, so Phase 2 begins by
#                       fall-through and NOT by a PERFORM. Reproduced as a
#                       direct call at the end of `_aa030_main_end`.
#      L 970 -> L 971 -> L 973
#                       ba000-Clear-Invoice-Deduct falls through into the EMPTY
#                       ba000-cid-exit, which falls through into main-exit. BOTH
#                       ARE DEAD IN PRACTICE: the paragraph is only ever
#                       PERFORMed [:L940, :L954] and a PERFORM of a paragraph
#                       returns at the paragraph's end, while straight-line
#                       arrival is impossible because ba000-Main-Rewrite ends
#                       with `exit section` [:L963]. Both functions are retained
#                       (R-5) with the fall-through wired and the reachability
#                       argument recorded in `_ba000_cid_exit`'s docstring.
#
# 9. ANOMALIES REPRODUCED - SIX REGISTER ENTRIES, more than any other program in
#    the migration. Every one carries an `# ANOMALY A-nn` comment at its
#    reproduction site citing the COBOL locator, which AAP section 0.7.4 C-4
#    prescribes as the way engineering quality is expressed here "rather than
#    through correction".
#
#    A-1  [:L1172-L1178] in `_ca000_bl_close`. THE MISSING TERMINATING PERIOD,
#         and the missing period is specifically THE ONE AFTER
#         `perform SPL-Posting-Close` ON LINE 1176 - not a missing END-IF and
#         not a wrong condition. It makes the `if` on [:L1177] a NESTED
#         conditional inside the `if` on [:L1175], so in PURE-GL MODE the outer
#         condition is false and `GL-Posting-Close` NEVER EXECUTES. The three
#         siblings all have the period: [purchase/pl060.cbl:L1031],
#         [sales/sl100.cbl:L694], [purchase/pl100.cbl:L675].
#    A-8  [:L826, :L827] in `_ba000_sales_comp`. DOUBLE TRUNCATION of the moving
#         average, caused by FIELD WIDTHS, not by arithmetic: `work-2` is
#         `pic s9(14) comp-3` with ZERO decimal places [:L206] while
#         `work-goods` carries two [:L218], so pence are discarded on every
#         accumulation; then `Sales-Average` is `binary-long`
#         [copybooks/wssl.cob:L49], an INTEGER, so the divide discards the
#         remainder. Both truncations arise from the descriptors.
#    A-9  [:L835-L843] in `_ba000_credit_comp`. The credit-note path has NO
#         `add 1 to sales-activety` ANYWHERE, and wraps BOTH the accumulate and
#         the divide in an extra outer guard `if work-2 not = zero` [:L841], so
#         on the FIRST credit note for a customer the average is not updated at
#         all and the note is silently dropped.
#    A-10 [:L819, :L835, :L841] across both functions above. THREE MUTUALLY
#         INCONSISTENT GUARDS on one idiom; variant (c) is
#         [sales/sl100.cbl:L497-L516], whose guard is single-condition, whose
#         counter is incremented AFTER the accumulate [:L510] and which uses a
#         `BY` divide [:L511] rather than an `INTO`. AAP section 0.6.1, verbatim:
#         "Normalising them into one helper would be the single easiest way to
#         fail this migration." `_ba000_sales_comp` and `_ba000_credit_comp` are
#         therefore two independent functions with NO shared helper, NO
#         parameterised variant and NO call from one to the other.
#         TECHNICAL NOTE, to prevent a future false "fix": `divide X into Y
#         giving Z` and `divide Y by X giving Z` are ARITHMETICALLY EQUIVALENT,
#         so sl100's operand order is a SYNTACTIC difference. The real
#         divergences are the guard structure and the counter.
#    A-17 [:L1173] written in `_ca000_bl_close`, [:L1037] read back in
#         `_ca000_bl_open`. THE UNEXPLAINED MOVE, carrying the maintainer's own
#         `*> Why ?`. It is NOT inert: `postings` is the SYSTEM-REC posting-RRN
#         high-water mark that `add postings 1 giving Batch-start` reads to
#         allocate the next batch's first RRN, so the pair is load-bearing and
#         diff-visible in GLPOSTING-REC. See AMBIGUITY Q-6 and Q-9.
#    A-18 [:L1106-L1109, :L1126-L1143] in `_ca000_bl_write`. `dr-pc` and
#         `cr-pc` are zeroed and NEVER given a value, and are NOT carried into
#         the IRS posting record; the IRS layout has no counterpart columns at
#         all. The maintainer flags it five times - [:L1123-L1124], [:L1133],
#         [:L1135] and the `*> IS IT ???` at [:L1139] against the two-receiver
#         `move 32`, which puts an ACCOUNT NUMBER into a PERCENTAGE field.
#         AAP CITATION CORRECTION: the AAP cites [:L1122-L1126]; the flags
#         measured in the frozen source are at the lines just named.
#
#    Anomalies of OTHER programs referenced here for context only, never
#    reproduced here: A-2 and A-3 (gl080's quarter subscript and its second
#    rotating counter), A-6 (acas008's always-failing verbs - sl060 calls none
#    of them), A-21 (gl070's field-name collisions, whose pattern recurs here as
#    FINDING 11), A-22 (the wrapper/exit name disagreement, WHICH DOES NOT OCCUR
#    HERE because `maps04` [:L1292] and `maps04-exit` [:L1297] AGREE).
#
# 10. FINDINGS - candidate anomaly-log additions, each with a `# FINDING`
#     comment at its site. 7 to 11 are the five the brief names; 12 is an
#     additional one found while transcribing.
#     FINDING 7  [:L722-L723] `aa999-Exit-Prog.` ends with `exit program.`, NOT
#                `goback.` - the only module in this folder to do so.
#     FINDING 8  TWO UNBOUNDED TABLE SUBSCRIPTS, the shape of A-2 in gl080.
#                (a) [:L509, :L526-L527] `a` is loaded from `oi-type` and used
#                    to index a table of THREE occurrences [:L219] with no
#                    check; the guard is UPSTREAM AND IMPLICIT, because sl055
#                    filters proformas out [sales/sl055.cbl:L430-L431].
#                (b) [:L545, :L551, :L558] `STurnover-Q (current-quarter)` is
#                    subscripted by the field A-3 concerns
#                    [copybooks/wssystem.cob:L110], also unchecked.
#                Both left unbounded (R-3). See AMBIGUITY Q-1 and Q-4.
#     FINDING 9  [:L702-L707] A MISSING `write` IN THE `sales-missing`
#                DIAGNOSTIC: the period on [:L707] closes both `if`s, so the
#                `write` belongs to the ELSE branch only and in COBOL-file mode
#                the message is moved into the print record and never written.
#                Print-only, so no table effect, but structurally the same class
#                of defect as A-1.
#     FINDING 10 [:L935-L955] THE ASYMMETRIC THREE-WAY APPORTIONMENT: the
#                `= work-1` arm sets BOTH statuses and DOES clear the deduction;
#                the `> work-1` arm sets ONLY `si-status` and does NOT clear;
#                the `else` arm sets ONLY `oi-status` and DOES clear.
#     FINDING 11 [:L1111-L1112, :L1116, :L1129-L1130] QUALIFIED REFERENCES, the
#                field-name-collision pattern the AAP records only for gl070.
#                `VAT-AC` and `Post-Code` are each declared in two of the
#                records in scope, so the source qualifies them; the Python
#                names both owners at each site so a reader sees which is meant.
#     FINDING 12 [:L1132, :L1134, :L1136, :L1141] NARROWING MOVES INTO THE IRS
#                POSTING RECORD that nobody flagged: `Post-DR`/`Post-CR` are
#                `pic 9(6)` [copybooks/wspost.cob:L19, :L21] but their IRS
#                counterparts are `pic 9(5)` [copybooks/wspost-irs.cob:L19,
#                :L20], and `Post-Amount`/`Vat-Amount` go from ten digits to
#                nine. High-order truncation is therefore possible on four
#                fields of every IRS posting row. Left as written; see
#                AMBIGUITY Q-5.
#     Also recorded at its site, though not numbered: `zz050-Validate-Date`
#     [:L1192] is DEAD CODE in sl060 - no statement performs it - and the MOVE
#     at [:L1111-L1112] has NO TERMINATING PERIOD, which unlike A-1 is HARMLESS
#     because neither statement is conditional.
#
# 11. AMBIGUITIES FOR THE COMPILED ORACLE (R-6).  Nine, each marked
#     `# AMBIGUITY Q-n` at its site, and each destined for
#     docs/migration/ambiguity-resolutions.md.
#     Q-1 [:L509, :L526-L527] which `oi-type` values actually reach the loop,
#         and what the compiled program stores when `a` is 0 or above 3.
#     Q-2 [:L437-L444, :L448-L456, :L681-L689, :L711-L713] is
#         `FS-Cobol-Files-Used` ever true in a scenario? If it is, the four
#         library-call gates become reachable and R-1 forbids honouring them.
#     Q-3 [:L590] the disposition of a failed OTM3-Write, which leaves
#         SALEDGER-REC written and SAITM3-REC not.
#     Q-4 [:L545, :L551, :L558] the reachable range of `Current-Quarter`, and
#         what an out-of-range value writes.
#     Q-5 [:L1132, :L1134, :L1136, :L1141] what the narrowing moves of FINDING
#         12 actually store, including the SIGN LEADING conversion.
#     Q-6 [:L1018, :L1173] sl060 increments `Next-Batch` and sets `Postings` but
#         performs NO System-Rewrite; does either update survive the run?
#     Q-7 [:L1091-L1094] the exact `Post-Legend` bytes from the edited-move,
#         INSPECT and STRING chain, including residue from a longer preceding
#         legend and the truncation point past 32 characters.
#     Q-8 [:L1162] the disposition of a failed GL-Batch-Write, which leaves
#         posting rows with no batch header.
#     Q-9 [:L1173] `Rrn` is `pic 9(5) comp` (0..99999) but `Postings` is
#         `binary-short` (-32768..32767), so an RRN above 32767 WRAPS NEGATIVE.
#
# 12. STRUCTURAL NOTES - the declaration decisions, recorded in full at their
#     own marked block earlier in this file and summarised here.
#     NOTE 1  The three-name redefines: `OI-Header`, `Open-Item-Record-3` and
#             `WS-OTM3-Record` are ONE STORAGE AREA
#             [copybooks/slwsoi3.cob:L9-L19], which is why five moves between
#             them are commented out in the source with the maintainer's reason
#             "*> is redefines" [:L585, :L666, :L760, :L871, :L961] and why
#             building the START key at [:L853-L854] and [:L902-L903] DESTROYS
#             the header's own `oi-invoice`. Modelled as one object reached
#             through `_Sl060State.oi_header`, which IS `ws_otm3_record`.
#     NOTE 2  `si-header` [copybooks/slwssoi.cob:L9] is a SECOND, INDEPENDENT
#             118 bytes of the same layout, used as a save area: saved at
#             [:L851] and restored at [:L913], bracketing `ba000-CR-Notes`.
#             Modelled as a separate instance, never an alias.
#     NOTE 3  `si-approp redefines si-net` [copybooks/slwssoi.cob:L39-L40] is
#             never referenced by this program.
#     NOTE 4  THE OTM2 WORK SEQUENCE. `open-item-file-2` is the sequence sl055
#             wrote (`seloi2` [:L178], `fdoi2` [:L186], `slwssoi` [:L280]). It
#             is navigated with DIRECT COBOL VERBS, not facade verbs -
#             `open input` [:L480], `read ... at end` [:L484], `close` [:L613],
#             `open output` then immediate `close` [:L677-L678] - and it reaches
#             NO SCHEMA TABLE, so it appears in no table dump. Modelled with
#             `acas_posting.workfiles.LineSequentialWorkFile`, whose
#             `open_output` discards prior content, which is exactly the
#             TRUNCATION at [:L677-L678] that marks the transfer to OTM3 as
#             complete. `copybooks/slwssoi.cob` has NO counterpart in AAP
#             section 0.3.1's `records/` list, and `acas_posting/programs/` is
#             closed at thirteen files, so no new file was created: the layout
#             is reached through `records.otm3.OiHeader`, which is the SAME
#             copybook included under a different name
#             [copybooks/slwsoi3.cob:L18-L19], and its descriptors carry
#             `copybooks/slwsoi.cob` locators.
#     NOTE 5  `Sales-Turnover` is published twice by `records.sales_ledger` -
#             as four named fields `quarters.turnover_q1..q4` and as an
#             OCCURS-4 view `quarters_view.sturnover_q`, which is an IMMUTABLE
#             tuple. Only the named fields are persisted, so the subscripted add
#             writes BOTH representations to keep them in step.
#
# 13. OMISSIONS - deliberate, and recorded so that a reader comparing the two
#     files does not conclude something was lost.
#     (a) [:L710] `call "SYSTEM" using Print-Report.` THE SPOOL-OUT PATH, out of
#         scope by AAP section 0.1.1, which excludes "the `call "SYSTEM" using
#         Print-Report` spool-out path that hands a report file to the operating
#         system". `copy "print-spool-command.cob"` [:L192] and
#         `move Print-Spool-Name to PSN` [:L413] go with it.
#     (b) THE FOUR `FS-Cobol-Files-Used`-GATED LIBRARY-CALL BLOCKS -
#         [:L437-L444], [:L448-L456], [:L681-L689], [:L711-L713]. The GATES are
#         reproduced faithfully through `condition_names`, so the decision stays
#         data-driven exactly as the COBOL's is; the CALL BODIES are not, because
#         `CBL_CHECK_FILE_EXIST` and `CBL_DELETE_FILE` are GnuCOBOL library
#         routines and R-1 forbids invoking COBOL at runtime. Each gate raises
#         `_CobolLibraryRoutineUnavailable`, naming the routine, its locator and
#         its arguments - NOT silently skipped, NOT stubbed as a no-op, NOT
#         emulated. All four are unreachable in the RDBMS configuration this
#         migration targets, because `88 FS-Cobol-Files-Used value zero`
#         [copybooks/wssystem.cob:L113] is false when
#         `88 FS-RDBMS-Used value 1` [copybooks/wssystem.cob:L116] is true. See
#         AMBIGUITY Q-2. NOTE that [:L441-L442] performs the FACADE verbs
#         `OTM3-Open-Output` and `OTM3-Close` inside gate 1: those would be
#         legitimate Python calls, but they sit behind the same gate, so the
#         whole block is unreachable together.
#         DISTINCT FROM THESE, and reproduced normally because they are ordinary
#         tests rather than calls: [:L692], [:L695], [:L703] and [:L711] also
#         TEST `FS-Cobol-Files-Used` to choose print behaviour.
#     (c) THE ENTIRE PRINT FILE AND ITS LINE LAYOUTS - `selprint` [:L179],
#         `fdprint` [:L187], `open output print-file` [:L470],
#         `close print-file` [:L709], every `write print-record` ([:L606],
#         [:L624], [:L630], [:L636], [:L640], [:L698], [:L707], [:L751],
#         [:L774-L786], [:L800-L810]) and the whole `l1-*` to `l8-*` field
#         families. BUT `ba000-Headings` [:L792] and `ba000-New-Heading`
#         [:L766] STILL EXIST as named functions (R-5), and `line-cnt` and `j`
#         are STILL MAINTAINED, because [:L608], [:L621], [:L691] and [:L754]
#         branch on them.
#     (d) ALL `display ... at` OUTPUT becomes log records - [:L418-L421],
#         [:L433], [:L471-L472], [:L591-L599], [:L659], [:L733],
#         [:L1163-L1168]. Per AAP section 0.3.4 they "must not alter control
#         flow and must not appear in any table dump".
#     (e) `accept ws-reply` [:L601], [:L735], [:L1169] - acknowledgement pauses
#         whose only effect is to block a terminal - are DROPPED, but the
#         `WS-Caller not = "xl150"` tests around them [:L600], [:L734],
#         [:L1167] ARE PRESERVED, because that is the codebase's own
#         unattended-mode check.
#     (f) `accept ws-env-lines from lines` [:L403] and the geometry arithmetic
#         [:L404-L409]; `set ENVIRONMENT` [:L415-L416]; `copy "envdiv.cob"`
#         [:L171]. [:L403] IS A TERMINAL-GEOMETRY READ, NOT A CLOCK READ, so
#         omitting it does not touch R-6: sl060 contains ZERO clock reads and
#         both date observables arrive through linkage - `to-day` as a parameter
#         and `Run-Date` [copybooks/wssystem.cob:L67] inside `system-record`,
#         used at [:L1022].
#     (g) The message literals `SL002`, `SL003`, `SL130`, `SL131`, `SL132`,
#         `SL133`, `SL133T` [:L261-L268] survive only as log text.
#     (h) `[:L1079-L1080]` `move oi-b-nos to k` and `move oi-b-item to i` are
#         REPRODUCED even though they are DEAD STORES - their only readers are
#         the commented-out STRING at [:L1096-L1101] - because the moves execute.
#     (i) `[:L1011-L1014]` the commented-out open-then-fallback pair for the
#         batch file is reproduced as the ABSENCE it is: a failed
#         `GL-Batch-Open` is not recovered from.
#     (j) sl060 has NO FACADE STUB BLOCK, unlike [general/gl072.cbl:L134-L153]
#         and gl080, so there is no representation-only declaration to omit.
#
# 14. FACADE VERBS - 27 DISTINCT, all entity-named, because the program's last
#     line is `copy "Proc-ACAS-FH-Calls.cob"` [:L1300] and it tests `fs-reply`
#     INLINE rather than through a per-handler error-check paragraph.
#       Sales       (acas012): Open [:L469], Read-Indexed [:L491], Write
#                              [:L581], Rewrite [:L583], Close [:L615]
#       OTM3        (acas019): Open [:L481, :L656], Open-Output [:L441],
#                              Write [:L586], Read-Next [:L662, :L867],
#                              Start [:L856, :L905], Rewrite [:L761, :L962],
#                              Close [:L442, :L614, :L679]
#       Value       (acas013): Open [:L644], Read-Indexed [:L981, :L994],
#                              Rewrite [:L990, :L1002], Close [:L646]
#       GL-Batch    (acas007): Open [:L1010], Write [:L1161], Close [:L1174]
#       GL-Posting  (acas006): Open [:L1047], Open-Output [:L1050],
#                              Write [:L1147], Close [:L1049, :L1178]
#       SPL-Posting (acas008): Open-Extend [:L1040], Open-Output [:L1043],
#                              Write [:L1142], Close [:L1042, :L1176]
#     `OTM3-Open-Output` is called only inside R-1 gate 1, so it appears in the
#     source and in the gate's comment but not as an executed call.
#     `SPL-Posting-Open-Output` MEANS DELETE EVERY ROW of PSIRSPOST-REC
#     [common/acas008.cbl:L313-L319, :L571-L574]. `acas008` also rejects
#     read-indexed, rewrite, start and delete UNCONDITIONALLY at entry
#     [common/acas008.cbl:L299-L307] - anomaly A-6 - and sl060 calls none of
#     those four.
#     Both `OTM3-Start` calls are preceded by `set fn-not-less-than to true`
#     [:L855, :L904], expressed as `AccessType.NOT_LESS_THAN`, never as a raw
#     integer. `move 1 to File-Key-No` appears at [:L422], [:L980] and [:L993].
#
# 15. TABLES THIS PROGRAM WRITES, and the gate that decides each.
#       SALEDGER-REC   Sales-Write [:L581] / Sales-Rewrite [:L583]; also
#                      mutated by `ba000-Clear-Invoice-Deduct` [:L967].
#                      UNGATED.
#       SAITM3-REC     OTM3-Write [:L586], OTM3-Rewrite [:L761, :L962].
#                      UNGATED.
#       VALUEANAL-REC  Value-Rewrite [:L990, :L1002]. Gated on
#                      `total-deduct not = zero` [:L643].
#       SYSTOT-REC     the two period-total adds - PERIOD TOTAL 3 OF 9 at
#                      [:L641] into `sl-credit-deductions`, and PERIOD TOTAL 4
#                      OF 9 at [:L700] into `sl-cn-unappl-this-month`. [:L700]
#                      IS UNCONDITIONAL - it sits OUTSIDE the `if` at [:L695]
#                      that guards only the print line - and getting that wrong
#                      would drop a SYSTOT-REC write in file mode and add one in
#                      RDBMS mode. These nine sites are the SOLE WRITERS of
#                      SYSTOT-REC in the whole migration (AAP section 0.6.4).
#       GLBATCH-REC    GL-Batch-Write [:L1161], reached only `if G-L` [:L649]
#                      or from the 99-item cap [:L1152].
#       GLPOSTING-REC  GL-Posting-Write [:L1147], gated `if G-L` [:L535] and
#                      then `IRS-Both-Used or G-L` [:L1144-L1145].
#       PSIRSPOST-REC  SPL-Posting-Write [:L1142], gated `if G-L` [:L535] and
#                      then `irs-used or IRS-Both-Used` [:L1126].
#       SYSTEM-REC     via A-17 [:L1173] `postings` and [:L1018] `Next-Batch` -
#                      mutated in storage, with no rewrite performed here; see
#                      AMBIGUITY Q-6.
#     Plus the OTM2 WORK SEQUENCE, which reaches no table and is TRUNCATED at
#     [:L677-L678].
#
#     THE SEVEN IRS FAN-OUT SITES, with their three distinct predicate shapes,
#     all evaluated through `condition_names` and never against a raw "Y"/"B"/1:
#       1 [:L1039] irs-used OR IRS-Both-Used     6 [:L1175] IRS-Used OR IRS-Both-Used
#       2 [:L1046] IRS-Both-Used or G-L          7 [:L1177] IRS-Both-Used or G-L
#       3 [:L1126] irs-used or IRS-Both-Used         (nested inside 6 - A-1)
#       4 [:L1144] IRS-Both-Used or G-L
#       5 [:L1172] IRS-Both-Used OR G-L
#     Condition names: `88 IRS-Used value "Y"` and `88 IRS-Both-Used value "B"`
#     on `05 IRS-Instead pic x` [copybooks/wssystem.cob:L179-L181]; `88 G-L
#     value 1` [copybooks/wssystem.cob:L85]. AAP section 0.6.4 records that this
#     switch's state "changes which tables a run touches", so a scenario must
#     pin it explicitly.
#     THE GATING IS LAYERED: `ca000-BL-Open`, `ca000-BL-Write` and
#     `ca000-BL-Close` are each reached ONLY `if G-L` [:L466, :L535, :L649], and
#     only then test the IRS flags internally. SO IN IRS-ONLY MODE NONE OF THE
#     THREE RUNS AT ALL and no batch, GL posting or IRS posting row is written.
#
# 16. ARITHMETIC - ZERO `ROUNDED` SITES IN THIS PROGRAM. The five in the whole
#     migration are [general/gl051.cbl:L791], [general/gl051.cbl:L796],
#     [general/gl080.cbl:L328], [irs/irs030.cbl:L1551] and
#     [irs/irs030.cbl:L1562]. EVERY STORE HERE TRUNCATES TOWARD ZERO, which is
#     the default path of `acas_posting.cobol.arithmetic`. The `rounded` flag of
#     every primitive is left at its default and is NEVER SET ANYWHERE in this
#     file - not once, in any of the 93 arithmetic calls - which an AST audit
#     over the executable code confirms rather than a text search, since the
#     token would otherwise match this very sentence. There are also ZERO
#     `ON SIZE ERROR` clauses and ZERO `REMAINDER` phrases.
#     Verb shapes, each mapped to the primitive that reproduces it:
#       `MULTIPLY a BY b` no GIVING, receiver SECOND -> `multiply_by`
#           the three sign flips at [:L571], [:L758], [:L861]
#       `MULTIPLY a BY b GIVING c`                   -> `multiply_by_giving`
#           [:L821], [:L837]
#       `DIVIDE a INTO b GIVING c`, i.e. c = b / a   -> `divide_into_giving`
#           [:L827], [:L843]
#       `SUBTRACT a FROM b` no GIVING                -> `subtract_from`
#       `SUBTRACT a FROM b GIVING c`                 -> `subtract_giving`
#           [:L409], [:L538], [:L578], [:L1088]
#       `ADD ... GIVING x`, variadic, summed at intermediate precision and
#           quantized ONCE                           -> `add_giving`
#           notably the TWO NINE-ADDEND statements at [:L728-L730] and
#           [:L921-L923], and the four/two/five-addend statements at [:L520],
#           [:L521], [:L523]
#       `ADD a b TO c`, multi-source into one receiver -> `add_to`
#           [:L552], [:L559], [:L884], and the three-source [:L1114]
#     RELATION-CONDITION ARITHMETIC WITH NO RECEIVER at [:L621] and [:L691]
#     (`line-cnt > Page-Lines - 7` and `... - 6`) is evaluated at intermediate
#     precision through `arithmetic.intermediate`, with no temporary field that
#     could quantize differently.
#     REFERENCE MODIFICATION is 1-BASED and goes through `move.ref_mod` /
#     `move.ref_mod_into`, never Python slicing - [:L1071-L1072] builds the
#     8-character `Post-Date` from the 10-character `u-date` on BOTH sides.
#     `INITIALIZE ... WITH FILLER` [:L497], `INSPECT ... TALLYING FOR LEADING`
#     [:L1087], the edited MOVE into `pic z(7)9` [:L1085] and `STRING ... INTO
#     ... POINTER` [:L1091-L1094] all use the published `cobol.move` primitives,
#     per AAP section 0.3.1: "`cobol/` contains no business logic and
#     `programs/` contains no numeric primitives."
#
# 17. DATE SECTIONS - which consolidated body each call selects.
#     `zz050-Validate-Date` [:L1192] -> `dates.zz050_validate_date`, THE
#         NON-gl051 VARIANT, because gl051 carries three extra
#         `inspect ... replacing` statements [general/gl051.cbl:L1178-L1180]
#         that sl060 omits entirely. (Dead code in sl060; retained per R-5.)
#     `zz060-Convert-Date` [:L1227] -> `dates.zz060_convert_date` with
#         `wrapper=_maps04`, because sl060 performs `maps04` [:L1236] where
#         gl051 and gl070 perform `maps03` - the ONE TOKEN that differs across
#         the six carriers.
#     `zz070-Convert-Date` [:L1262] -> `dates.zz070_convert_date`, the
#         consolidated form, BYTE-IDENTICAL in all ten carriers.
#     `maps04` [:L1292] -> `dates.maps04`, the full reimplementation of
#         `common/maps04.cbl` (R-1 forbids the `call "maps04"` at [:L1295]),
#         including its 1600-12-31 epoch, its six-part reject test
#         [common/maps04.cbl:L140-L146] and its behaviour of LEAVING THE OUTPUT
#         FIELD UNTOUCHED on rejection [common/maps04.cbl:L146, :L154] - which
#         is why `move zero to u-bin` [:L1221] is load-bearing.
#     A-22 DOES NOT OCCUR HERE: the wrapper section is `maps04` and its exit is
#     `maps04-exit`, so THE NAMES AGREE. A-22 is confined to
#     [general/gl070.cbl:L603-L609] and [general/gl051.cbl:L1273-L1278].
#
# 18. LAYERING (AAP section 0.4.3). This module imports only `acas_posting`'s
#     `records.*`, `dal.facade`, `dal.status`, `cobol.arithmetic`, `cobol.move`,
#     `cobol.condition_names`, `cobol.field`, `cobol.picture`, `dates`,
#     `workfiles` and the standard library. It imports NO `cli`, NO
#     `dal.acas*`, NO `dal.connection`, NO `dal.cursor_state`, NO `clock`, NO
#     `harness`, NO `dictionary.generate` and NO OTHER `programs.*` module -
#     including NOT `programs.sl055_invoice_extract_analysis`, even though sl055
#     produces the OTM2 sequence this program consumes. The handoff is through
#     the work sequence, exactly as in COBOL, and the CLI sequences the two
#     calls: `acas_posting/cli/sl_invoice_post.py` dispatches sl055 then sl060,
#     gating on `if ws-term-code not = zero` [sales/sales.cbl:L759-L768] - which
#     is the SALES gate, different from the GL's `= 5` test and from Purchase,
#     which has no gate at all.
# ===========================================================================
