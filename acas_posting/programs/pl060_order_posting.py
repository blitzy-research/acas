"""``pl060`` - Purchase Orders Posting Report. Migration of ``purchase/pl060.cbl``.

THIS MODULE IS THE **A-1 CONTROL CASE** AND IT IS **NOT** A COPY OF ``sl060``.

Anomaly A-1 is a missing terminating period in the Sales twin. In this program the
period IS present::

    L1030      if       IRS-Used OR IRS-Both-Used
    L1031               perform SPL-Posting-Close.      <- PERIOD PRESENT
    L1032      if       IRS-Both-Used or G-L
    L1033               perform GL-Posting-Close.       <- therefore a SIBLING, and REACHED

Because ``[purchase/pl060.cbl:L1031]`` terminates its sentence, ``[L1032]``'s ``if``
is a sibling of ``[L1030]``'s and ``GL-Posting-Close`` DOES execute when only ``G-L``
is set. The Sales twin ``[sales/sl060.cbl:L1176]`` lacks the period, so its
``[L1177]`` nests inside ``[L1175]`` and ``GL-Posting-Close`` NEVER runs in pure-GL
mode. **The divergence between the two files IS the anomaly; preserving it is the
whole point.** The other two control cases are ``[sales/sl100.cbl:L694]`` and
``[purchase/pl100.cbl:L675]``.

Agent Action Plan section 0.6.1 states the governing prohibition verbatim, of the
moving-average idiom that ``sl060``, ``pl060``, ``sl100`` and ``pl100`` each spell
differently: *"Normalising them into one helper would be the single easiest way to
fail this migration."* Accordingly this module imports NOTHING from any sibling
program module - not ``sl060_invoice_posting``, not ``pl055_order_proof_extract`` -
and shares no helper with them.

WHAT THIS PROGRAM DOES
----------------------
It consumes the OTM4 extract that ``pl055`` built, posts each header to the purchase
ledger, maintains the moving average, writes the GL batch and posting records and the
IRS fan-out records, runs a credit-note apportionment pass over OTM5, then a second
pass to swap unapplied credits, and finally truncates OTM4. Its on-screen title is
``"Purchase Orders Posting Report"`` ``[purchase/pl060.cbl:L357]``.

Boundary: **the whole program.** ``purchase/pl060.cbl`` is 1155 lines and every one of
its forty procedure labels has a correspondingly named function here (rule R-5).

WHAT IT WRITES - five tables, two system records, one work sequence
-------------------------------------------------------------------
====================  ================================================================
``PULEDGER-REC``      ``Purch-Write`` ``[L517]`` / ``Purch-Rewrite`` ``[L519]``;
                      ``purch-status``, ``purch-current``, ``purch-unapplied``,
                      ``purch-average``, ``purch-activety``, ``pturnover-q``,
                      ``purch-last-inv``, ``purch-last-pay``
``PUITM5-REC``        ``OTM5-Write`` ``[L522]`` / ``OTM5-Rewrite`` ``[L686]``,
                      ``[L871]``; ``oi-status``, ``oi-paid``, ``oi-p-c``
``GLBATCH-REC``       ``GL-Batch-Write`` ``[L1016]``
``GLPOSTING-REC``     ``GL-Posting-Write`` ``[L1002]``
``PSIRSPOST-REC``     ``SPL-Posting-Write`` ``[L997]``
``SYSTEM-REC``        ``P-Flag-I`` ``[L373]``, ``P-Flag-A`` ``[L374]``,
                      ``Oi-5-Flag`` ``[L375]``, ``Next-Batch`` ``[L887]``,
                      ``postings`` ``[L1028]``
``SYSTOT-REC``        ``pl-cn-unappl-this-month`` ``[L628]`` - period total 8
OTM4 sequence         consumed ``[L421]``-``[L425]`` then TRUNCATED ``[L605]``-``[L606]``
====================  ================================================================

Agent Action Plan section 0.6.4 calls the nine period-total sites *"the sole writers"*
of ``SYSTOT-REC``. ``[L628]`` is site 8 of those nine, and it sits OUTSIDE the
``[L623]`` print guard - the print line is conditional, the database effect is not.

STRUCTURAL FACTS ABOUT THIS PROGRAM, EACH VERIFIED AGAINST THE SOURCE
--------------------------------------------------------------------
* **ZERO ``ROUNDED`` sites.** Every store in this program truncates toward zero. The
  five ``ROUNDED`` sites in the whole migration are ``[general/gl051.cbl:L791]``,
  ``[general/gl051.cbl:L796]``, ``[general/gl080.cbl:L328]``, ``[irs/irs030.cbl:L1551]``
  and ``[irs/irs030.cbl:L1562]`` - none of them here.
* **ZERO ``PERFORM ... THRU``.** The four in-scope sites are ``[general/gl072.cbl:L300]``,
  ``[general/gl072.cbl:L304]``, ``[sales/sl100.cbl:L344]`` and ``[purchase/pl100.cbl:L336]``.
* **NO anomaly A-22.** The wrapper section ``maps04`` ``[L1146]`` and its exit
  ``maps04-exit`` ``[L1151]`` AGREE. A-22's two occurrences are
  ``[general/gl070.cbl:L603-L609]`` and ``[general/gl051.cbl:L1273]``.
* **NO facade stub block.** Unlike ``[general/gl072.cbl:L135-L155]`` and
  ``[general/gl080.cbl:L194-L214]``, this program declares no unused facade stubs.
* **NO ``analise-deductions`` section** and no ``ws-deduction`` / ``total-deduct`` /
  ``total-mov-ded`` fields, unlike ``[sales/sl060.cbl:L224-L226]`` and its section at
  ``[sales/sl060.cbl:L976]``. That absence is precisely why ``pl060`` has ONE period
  total ``[L628]`` where ``sl060`` has TWO, ``[sales/sl060.cbl:L641]`` and
  ``[sales/sl060.cbl:L700]``.
* **NO run-confirm gate.** ``acpt-xrply`` ``[L362]`` has its entire body
  ``[L363]``-``[L371]`` commented out, unlike ``[sales/sl100.cbl:L310-L319]``. The
  paragraph is retained as an empty named function for rule R-5.
* **NO term-code gate upstream.** ``[purchase/purchase.cbl:L752-L762]`` has its
  ``if ws-term-code not = zero / go to display-menu`` lines commented out, so the
  Purchase CLI sequences ``pl055`` then ``pl060`` with no gate. General uses ``= 5``
  and Sales uses ``not = zero``; the three predicates are NOT unified anywhere.
* **``main-exit.`` occurs TEN times** (L688, L714, L738, L753, L768, L828, L875, L923,
  L1010, L1035), **``main-end.`` twice** (L545, L823) and **``end-loop.`` twice**
  (L585, L809). Every function name here is therefore SECTION-QUALIFIED.
* **23 live ``GO TO`` sites.** A twenty-fourth and twenty-fifth appear in the source
  only as commented-out text at ``[L368]`` and ``[L370]``. Each live site carries a
  ``# GO TO class N`` annotation; the full census is in the traceability footer.

RULES
-----
``review_rules`` reports, verbatim, ``"No user rules provided."`` There is no user
rules document for this project; the six binding rules are the Agent Action Plan's
R-1 through R-6 (section 0.7.2), and enterprise-standard best practice governs
wherever they are silent. Of them, this module is bound by:

R-1  No COBOL at runtime. Nothing here executes, embeds or shells out to COBOL. The
     four ``CBL_*`` library calls ``[L377]``, ``[L388]``, ``[L610]``, ``[L641]`` are
     all gated on ``FS-Cobol-Files-Used``, which is unreachable in the RDBMS
     configuration this migration targets; the gates are reproduced and the probes
     raise :class:`_Pl060CobolLibraryRoutineUnavailable`. The facade verbs inside the
     first gate ``[L380-L381]`` ARE reproduced. ``[L638]``'s spool-out is omitted.
R-2  Zero binary floating point. All arithmetic delegates to
     :mod:`acas_posting.cobol.arithmetic` and all data movement to
     :mod:`acas_posting.cobol.move`; per Agent Action Plan section 0.3.1,
     *"cobol/ contains no business logic and programs/ contains no numeric
     primitives."* No store in this module requests COBOL's ``ROUNDED`` phrase, because
     the program contains no ``ROUNDED`` site.
R-3  No new validations, fields, schema changes or concurrency. Execution is strictly
     sequential. Nothing is cached - not the three repeated ``File-28`` probes, not
     the double ``OTM5-Open``, not the near-duplicate heading sections, not the twice
     reset ``work-b``.
R-4  Legacy anomalies reproduced, never fixed. Eleven anomalies are reproduced here -
     A-1, A-8, A-9, A-10, A-17, A-18, A-21 and four measured but unregistered defects
     A-NEW-1 through A-NEW-4 - each annotated at its site with its locator.
R-5  Full traceability. One named function per section and per paragraph, a
     ``GO TO`` class at every transfer site, every fall-through recorded, and a
     ``# --- traceability ---`` footer.
R-6  Compiled behaviour is the tie-breaker; determinism. This program contains ZERO
     clock reads; the date arrives entirely through the ``to-day`` linkage item and
     ``Run-Date`` on the system record. Nothing here reads a clock.

Open questions that only the compiled oracle can settle are marked ``# AMBIGUITY Q-``.
"""

from __future__ import annotations

import inspect
import logging
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Callable, Final, Mapping, cast

from acas_posting.cobol import arithmetic as ar
from acas_posting.cobol import condition_names as cn
from acas_posting.cobol import move as mv
from acas_posting.cobol import picture as pic
from acas_posting.cobol.field import FieldDescriptor
from acas_posting.dal import facade
#: ``AccessType`` carries ``fn-not-less-than`` [copybooks/wsfnctn.cob:L88-L118], which
#: this program sets itself before both ``OTM5-Start`` calls
#: [purchase/pl060.cbl:L777], [purchase/pl060.cbl:L818] - the facade's ``Start`` verb
#: deliberately does NOT zero the access type
#: [copybooks/Proc-ACAS-FH-Calls.cob:L1284]. ``FsReply`` carries every status this
#: program tests. ``FileFunction`` and ``WeError`` are NOT imported: ``pl060`` sets no
#: function code of its own - the facade owns that - and contains no ``we-error``
#: reference at all, so importing either would be an unused import.
from acas_posting.dal.status import AccessType, FsReply
from acas_posting.dates import (
    WsDateFormats,
    maps04 as _dates_maps04,
    zz050_validate_date as _dates_zz050,
    zz060_convert_date as _dates_zz060,
    zz070_convert_date as _dates_zz070,
)
from acas_posting.records.calling_data import WsCallingData
from acas_posting.records.file_access import FileAccess
from acas_posting.records.file_defs import FileDefs
from acas_posting.records.gl_batch import (
    BatchAmounts,
    BatchDates,
    GlBatchRecord,
    PostingData,
    WsBatchKey,
)
from acas_posting.records.gl_posting import WsPostingRecord, WsPostKey
from acas_posting.records.otm5 import (
    Filler1,
    Oi5Key,
    OiBatch,
    OiCustomer,
    OiHeader,
    OiKey,
    OiSupplier,
    descriptors_of,
)
from acas_posting.records.maps03 import Maps03Ws
from acas_posting.records.purchase_ledger import Quarters, QuartersView, WsPurchRecord
from acas_posting.records.spl_irs_posting import WsIrsPostingRecord, WsIrsPostKey
from acas_posting.records.system_record import SystemRecord
from acas_posting.records.system_record_4 import SystemRecord4
from acas_posting.records.test_data_flags import AcasDalCommonData
from acas_posting.workfiles import (
    OPEN_ITEM_4_NAME,
    OpenItemWorkFile,
    open_item_work_file,
)

#: Agent Action Plan section 0.3.3, verbatim: *"Each ``programs/*.py`` module exposes
#: a single ``run(...)`` entry mirroring its COBOL ``PROCEDURE DIVISION USING`` list,
#: with the paragraph functions private to the module. Callers cannot reach into a
#: program's internals, exactly as a COBOL ``CALL`` cannot."*
__all__: Final[tuple[str, ...]] = ("run",)

_LOG: Final[logging.Logger] = logging.getLogger(__name__)

#: ``77  prog-name  pic x(15)  value "PL060 (3.3.01)".`` [purchase/pl060.cbl:L139]
_PROG_NAME: Final[str] = "PL060 (3.3.01)"

#: The program's own on-screen title [purchase/pl060.cbl:L357]. Presentation, so it
#: reaches a log record and never a table - Agent Action Plan section 0.3.4.
_TITLE: Final[str] = "Purchase Orders Posting Report"

#: ``01  open-item-file-4`` is assigned to ``file-28`` with ``ACCESS SEQUENTIAL``
#: [copybooks/seloi4.cob:L2-L4], and ``open-item-file-5`` to ``file-29``. The
#: ``File-28-status`` switch [purchase/pl060.cbl:L218-L220] records whether the flat
#: file exists; it is program-local, so its condition names are modelled here.
_FILE_28_EXISTS: Final[int] = 0
_FILE_28_NOT_EXISTS: Final[int] = 1

#: ``88  purchase-missing  value 1.`` on ``03 ws-error pic 9``
#: [purchase/pl060.cbl:L192-L193].
_WS_ERROR_PURCHASE_MISSING: Final[int] = 1

#: ``01 Error-Messages`` [purchase/pl060.cbl:L248-L257], transcribed from the frozen
#: ``VALUE`` clauses rather than paraphrased.  Presentation only, and never a stored
#: value - but they do NOT all survive as log text.  Agent Action Plan section 0.3.4
#: splits the group three ways, and every member stays DECLARED regardless, because rule
#: R-5 maps the whole ``01 Error-Messages`` group and a shorter group would misreport the
#: frozen source:
#:
#: * ``PL130`` [L527] and ``PL132`` [L1018] are DIAGNOSTICS and become log records.
#: * ``PL002`` is a PURE PROMPT.  Both of its displays - [L535] and [L1023] - stand
#:   immediately before an ``accept ws-reply``, and the literal is nothing but the
#:   instruction to press that key, so it is declared and deliberately never referenced.
#: * ``PL133`` and ``PL133T`` are REPORT CONTENT and are never displayed at all: they are
#:   ``move``d into ``print-record`` at [L632] and [L634], which section 0.2.2 puts out of
#:   scope.  Declared and deliberately never referenced.
#: * ``PL131`` is the one MIXED literal; it is split below.
_PL002: Final[str] = "PL002 Note error and hit return"
_PL130: Final[str] = "PL130 Error writing Open Item 5 Record"
_PL131: Final[str] = "PL131 PE - CR SWOP: Return to continue"
_PL132: Final[str] = "PL132 Err on Batch file write : "
_PL133: Final[str] = "PL133 Warning Record/s missing in Purchase File"
_PL133T: Final[str] = "PL133T Warning Record/s missing in Purchase Table"

#: THE SUBSTANTIVE HALF OF ``PL131``.  The frozen literal carries two things in one
#: string: the diagnostic "PE - CR SWOP" - the credit-swap notice raised when a credit
#: note nets to zero [L658-L659] - and, after the colon, the instruction to press the key
#: that [L661]'s ``accept ws-reply`` reads.  Section 0.3.4 keeps the first and drops the
#: second, so the record at [L659] carries this prefix.  Taken by slicing the declared
#: literal rather than retyped, so the two can never drift apart.  ``sl060`` splits its
#: own ``SL131`` the same way [sales/sl060.cbl:L265].
_PL131_NOTICE: Final[str] = _PL131.split(":", 1)[0]

#: ``01  total-lits`` with ``03 ws-lits pic x(17) occurs 3`` redefining it
#: [purchase/pl060.cbl:L261-L266]. Indexed by ``oi-type``, one-based, and read ONLY by the
#: printed totals block at [L551-L571], which is report content and out of scope per
#: section 0.2.2 - so the tuple is DECLARED AND DELIBERATELY UNREFERENCED.  It stays
#: because R-5 maps the group, and because the ``x(17)`` width is the evidence that the
#: captions never reach a stored value.
_WS_LITS: Final[tuple[str, str, str]] = ("Receipts", "Invoices", "Credit Notes")


# ---------------------------------------------------------------------------
# WORKING-STORAGE field descriptors.
#
# ``pl060``'s own WORKING-STORAGE is absent from the generated data dictionary -
# ``data_dictionary/acas_posting_dictionary.json`` carries 1061 entries and NONE of
# them names this program - because the dictionary is generated from the copybook /
# bridge / column triple and a program's private working storage has no column. Every
# descriptor below is therefore built by the picture parser, which
# ``acas_posting/cobol/field.py`` documents as the one factory permitted to construct a
# descriptor without a dictionary key, and each carries a ``source_locator`` so rule
# R-5's field-level traceability still holds.
# ---------------------------------------------------------------------------

_SRC: Final[str] = "purchase/pl060.cbl"


def _ws_descriptor(clauses: str, name: str, line: int) -> FieldDescriptor:
    """Parse one ``pl060`` WORKING-STORAGE entry into a descriptor.

    ``line`` is the declaration's line number in the frozen source, which becomes the
    descriptor's provenance. ``acas_posting/cobol/picture.py``'s ``descriptor_for`` is
    the published entry point for this; nothing about the picture clause is
    interpreted here (rule R-2, Agent Action Plan section 0.3.1).
    """
    return pic.descriptor_for(clauses, name=name, source_locator=f"{_SRC}:L{line}")


#: ``03  ws-reply  pic x.`` [purchase/pl060.cbl:L191]
_D_WS_REPLY: Final[FieldDescriptor] = _ws_descriptor("pic x", "ws-reply", 191)
#: ``03  ws-error  pic 9  value zero.`` [purchase/pl060.cbl:L192]
_D_WS_ERROR: Final[FieldDescriptor] = _ws_descriptor("pic 9", "ws-error", 192)
#: ``03  xx  pic 99.`` [purchase/pl060.cbl:L195] - the ``STRING`` pointer.
_D_XX: Final[FieldDescriptor] = _ws_descriptor("pic 99", "xx", 195)
#: ``03  ws-eval-msg  pic x(25)  value spaces.`` [purchase/pl060.cbl:L198]
_D_WS_EVAL_MSG: Final[FieldDescriptor] = _ws_descriptor("pic x(25)", "ws-eval-msg", 198)
#: ``03  work-1  pic s9(7)v99  comp-3  value zero.`` [purchase/pl060.cbl:L199]
_D_WORK_1: Final[FieldDescriptor] = _ws_descriptor("pic s9(7)v99 comp-3", "work-1", 199)
#: ``03  work-2  pic s9(14)  comp-3.`` [purchase/pl060.cbl:L200]
#:
#: ANOMALY A-8 - FOURTEEN digits and **ZERO decimal places**. This is the receiving
#: field of the first of the two truncations in the moving average; see
#: :func:`_purch_comp` and :func:`_credit_comp`.
_D_WORK_2: Final[FieldDescriptor] = _ws_descriptor("pic s9(14) comp-3", "work-2", 200)
#: ``03  work-a  pic s9(7)v99  comp-3  value zero.`` [purchase/pl060.cbl:L201]
_D_WORK_A: Final[FieldDescriptor] = _ws_descriptor("pic s9(7)v99 comp-3", "work-a", 201)
#: ``03  work-b  pic s9(7)v99  comp-3  value zero.`` [purchase/pl060.cbl:L202]
#: The accumulator that becomes period total 8 at ``[L628]``. It is reset twice, at
#: ``[L582]`` and at ``[L781]``, on two different accumulation phases.
_D_WORK_B: Final[FieldDescriptor] = _ws_descriptor("pic s9(7)v99 comp-3", "work-b", 202)
#: ``03  first-pass  pic x.`` [purchase/pl060.cbl:L203]
_D_FIRST_PASS: Final[FieldDescriptor] = _ws_descriptor("pic x", "first-pass", 203)
#: ``03  j  pic 999.`` [purchase/pl060.cbl:L205] - the printed page counter.
_D_J: Final[FieldDescriptor] = _ws_descriptor("pic 999", "j", 205)
#: ``03  m  pic z(7)9.`` [purchase/pl060.cbl:L207] - zero-suppressed EDITED field.
_D_M: Final[FieldDescriptor] = _ws_descriptor("pic z(7)9", "m", 207)
#: ``03  a  pic 9  value zero.`` [purchase/pl060.cbl:L208] - the ``total-group``
#: subscript, loaded from ``oi-type`` at ``[L450]`` with no bounds check (A-NEW-3).
_D_A: Final[FieldDescriptor] = _ws_descriptor("pic 9", "a", 208)
#: ``03  b  binary-char  value zero.`` [purchase/pl060.cbl:L209] - the ``INSPECT`` tally.
_D_B: Final[FieldDescriptor] = _ws_descriptor("binary-char", "b", 209)
#: ``03  c  binary-char  value zero.`` [purchase/pl060.cbl:L210]
_D_C: Final[FieldDescriptor] = _ws_descriptor("binary-char", "c", 210)
#: ``03  work-net  pic s9(7)v99  comp-3.`` [purchase/pl060.cbl:L211]
_D_WORK_NET: Final[FieldDescriptor] = _ws_descriptor("pic s9(7)v99 comp-3", "work-net", 211)
#: ``03  work-vat  pic s9(7)v99  comp-3.`` [purchase/pl060.cbl:L212]
_D_WORK_VAT: Final[FieldDescriptor] = _ws_descriptor("pic s9(7)v99 comp-3", "work-vat", 212)
#: ``03  work-goods  pic s9(7)v99  comp-3.`` [purchase/pl060.cbl:L213]
#:
#: ANOMALY A-8 - TWO decimal places. Adding this into the zero-scale ``work-2`` at
#: ``[L750]`` discards the pence on every accumulation.
_D_WORK_GOODS: Final[FieldDescriptor] = _ws_descriptor("pic s9(7)v99 comp-3", "work-goods", 213)
#: ``05  total-net  pic s9(7)v99.`` inside ``03 total-group occurs 3 comp-3``
#: [purchase/pl060.cbl:L214-L215].
_D_TOTAL_NET: Final[FieldDescriptor] = _ws_descriptor("pic s9(7)v99 comp-3", "total-net", 215)
#: ``05  total-vat  pic s9(7)v99.`` [purchase/pl060.cbl:L216]
_D_TOTAL_VAT: Final[FieldDescriptor] = _ws_descriptor("pic s9(7)v99 comp-3", "total-vat", 216)
#: ``03  line-cnt  binary-char  value zero.`` [purchase/pl060.cbl:L217]
_D_LINE_CNT: Final[FieldDescriptor] = _ws_descriptor("binary-char", "line-cnt", 217)
#: ``03  File-28-status  pic 9  value zero.`` [purchase/pl060.cbl:L218]
_D_FILE_28_STATUS: Final[FieldDescriptor] = _ws_descriptor("pic 9", "File-28-status", 218)

#: The three print-line balance fields whose arithmetic is reproduced even though the
#: print itself is omitted: ``l5-old-bal`` ``[L477]``, ``l5-new-bal`` ``[L514]`` and
#: ``l6-gross`` ``[L553]``, ``[L563]``, ``[L569]``. Their pictures come from the
#: report layouts in the frozen source; each is an eight-and-two signed edited money
#: field, so a truncating store into two decimals is the observable behaviour.
_D_PRINT_MONEY: Final[FieldDescriptor] = _ws_descriptor(
    "pic s9(8)v99 comp-3", "print-money-work", 214
)

# ---------------------------------------------------------------------------
# STRUCTURAL NOTES - the two record layouts with no ``records/`` module.
#
# 1. ``01 open-item-record-4 pic x(113)`` [copybooks/fdoi4.cob:L10], selected
#    ``assign file-28 access sequential status fs-reply`` [copybooks/seloi4.cob:L2-L4].
#    ``pl055`` writes ``OI-Header`` into it [purchase/pl055.cbl:L587] and ``pl060``
#    reads it back and group-moves it into ``oi-header`` [purchase/pl060.cbl:L428], so
#    the 113 bytes ARE an ``OI-Header``. It is a transient scratch file, not part of
#    the frozen schema, so it reaches no table and appears in no dump: Agent Action
#    Plan section 0.3.1 models exactly this as *"ordered sequences with the same record
#    layout and the same ordering guarantees"*.
#    ``acas_posting/workfiles.py`` publishes ``OpenItemWorkFile``, the SHARED carrier
#    for both open-item work files, whose semantics match the COBOL exactly:
#    ``open_extend`` appends, ``open_output`` TRUNCATES, ``open_input`` positions at the
#    first record, ``read_next`` returns ``None`` and sets end-of-file, ``close`` keeps
#    the records. ``pl055`` writes through the same object, which is what makes the
#    handoff a channel. No new file is added to ``records/`` - that folder is closed.
#
# 2. ``01 si-header`` [copybooks/plwssoi.cob:L11] is byte-identical to ``OI-Header``,
#    field for field, with an ``si-`` prefix. It has no ``records/`` module and no
#    dictionary entry. ``pl060`` uses it only to save the OTM4 header across the
#    ``cr-notes`` walk [purchase/pl060.cbl:L773] and restore it afterwards
#    [purchase/pl060.cbl:L826], reading ``si-supplier``, ``si-cr``, ``si-paid`` and
#    writing ``si-status`` in between. It is therefore modelled as a second
#    ``OiHeader`` buffer behind ``si-`` named accessors, and the two group moves are
#    genuine group moves over identical layouts.
# ---------------------------------------------------------------------------

#: ``fd  open-item-file-4.`` / ``01  open-item-record-4  pic x(113).``
#: [copybooks/fdoi4.cob:L8-L10]
_D_OPEN_ITEM_RECORD_4: Final[FieldDescriptor] = pic.descriptor_for(
    "pic x(113)", name="open-item-record-4", source_locator="copybooks/fdoi4.cob:L10"
)

# ---------------------------------------------------------------------------
# Descriptor lookup across the TWO conventions the ``records/`` layer uses.
#
# ``records/purchase_ledger.py`` and ``records/otm5.py`` attach each descriptor to its
# dataclass field as ``field(metadata={"descriptor": ...})``; ``records/gl_batch.py``,
# ``records/gl_posting.py``, ``records/spl_irs_posting.py``, ``records/file_access.py``,
# ``records/system_record.py`` and ``records/system_record_4.py`` publish a ``FIELDS``
# ClassVar TUPLE instead. Both carry the same ``FieldDescriptor`` objects with the same
# dictionary provenance, so one accessor over both is enough.
#
# The match is deliberately case-INSENSITIVE, and that is not tidiness: the very
# collision anomaly A-21 records shows up here as a spelling difference. The system
# record spells the field ``Vat-Ac`` while the posting record spells it ``Vat-AC``,
# which is exactly why ``[purchase/pl060.cbl:L966-L967]`` has to write
# ``vat-ac of system-record to vat-ac of WS-Posting-Record``.
# ---------------------------------------------------------------------------


def _desc(owner: Any, cobol_name: str) -> FieldDescriptor:
    """Return the ``FieldDescriptor`` a record class publishes for ``cobol_name``.

    ``owner`` is a record dataclass (or an instance of one). ``cobol_name`` is the
    COBOL field name as the copybook spells it. Raising rather than returning ``None``
    is deliberate: a descriptor that cannot be found is a broken traceability chain,
    and rule R-5 makes that a defect rather than something to work around.
    """
    cls = owner if isinstance(owner, type) else type(owner)
    wanted = cobol_name.casefold()

    for descriptor in getattr(cls, "FIELDS", ()):
        if descriptor.name.casefold() == wanted:
            return descriptor

    for member in getattr(cls, "__dataclass_fields__", {}).values():
        descriptor = member.metadata.get("descriptor")
        if descriptor is not None and descriptor.name.casefold() == wanted:
            return descriptor

    # ``records/otm5.py`` publishes neither convention directly; it publishes the
    # accessor ``descriptors_of``, which is its own documented way of reaching the same
    # ``FieldDescriptor`` objects. Asking it is therefore the third lookup rather than a
    # fallback, and it is what makes ``OI-Net``, ``OI-Type`` and their siblings reachable.
    if cls.__module__ == OiHeader.__module__:
        for descriptor in descriptors_of(cls).values():
            if descriptor.name.casefold() == wanted:
                return descriptor

    raise LookupError(
        f"{cls.__name__} publishes no descriptor named {cobol_name!r}; the "
        f"records layer is the authority for field metadata and this module must "
        f"not invent one"
    )


# ---------------------------------------------------------------------------
# The facade seam.
#
# ``copy "Proc-ACAS-FH-Calls.cob".`` [purchase/pl060.cbl:L1154] brings in the
# ENTITY-named vocabulary, whose callers test the reply INLINE - that copybook has no
# error-check paragraph in any of its 256 labels. The handler-named vocabulary of
# ``copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob``, which DOES wrap each call in a
# per-handler check, is the IRS convention and is not used by this program.
#
# Every facade paragraph has the same two-level shape. The verb paragraph sets the
# function code and the access type, for example ``GL-Batch-Read-Next``
# [copybooks/Proc-ACAS-FH-Calls.cob:L465-L469], and the dispatch paragraph sets the key
# number and issues the ``CALL``, for example ``acas007``
# [copybooks/Proc-ACAS-FH-Calls.cob:L51-L57]. ``dal/facade.py`` owns both levels; this
# module only names the verb.
#
# AMBIGUITY Q-FACADE-SHAPE - ``acas_posting/dal/facade.py`` is authored in parallel with
# this module and is not present to bind against. Two documented shapes exist for its
# verb functions and the compiled behaviour is identical under either, so the seam
# below accepts both rather than guessing one:
#   * Agent Action Plan section 0.4.3 and ``dal/facade.py``'s own specification give
#     ``facade.gl_batch_read_next(ctx)`` - a single context object which that
#     specification defines as *"the system record, the entity record, File-Access,
#     File-Defs and ACAS-DAL-Common-Data"*.
#   * The twenty handler modules each publish
#     ``dispatch(system, record, file_access, file_defs, dal_common)``, the five
#     parameters of the frozen ``PROCEDURE DIVISION USING`` in order, which is the
#     shape a thin facade would forward unchanged.
# :func:`_fh` binds by the target's OWN declared signature and raises
# :class:`_Pl060FacadeBindingError` if neither shape fits, so an integration mismatch
# fails loudly at the seam instead of silently mis-posting. The resolution belongs in
# ``docs/migration/ambiguity-resolutions.md``.
# ---------------------------------------------------------------------------


class _Pl060FacadeBindingError(RuntimeError):
    """The data-access facade does not expose a verb in a shape this module can call.

    Raised when ``acas_posting.dal.facade`` publishes a verb whose signature matches
    neither documented shape. It is deliberately fatal: a posting program that cannot
    reach the ledger must stop, not continue with unwritten rows.
    """


class _Pl060CobolLibraryRoutineUnavailable(RuntimeError):
    """A GnuCOBOL library routine was reached, which rule R-1 forbids invoking.

    ``purchase/pl060.cbl`` calls two library routines, both only inside
    ``if FS-Cobol-Files-Used`` guards. ``88 FS-Cobol-Files-Used value zero`` and
    ``88 FS-RDBMS-Used value 1`` [copybooks/wssystem.cob:L113], [copybooks/wssystem.cob:L116]
    are the two settings of one digit, so in the RDBMS configuration this migration
    targets every one of those branches is unreachable. The guards are reproduced
    faithfully so the decision stays data-driven, and reaching the body raises this
    rather than silently skipping, stubbing a no-op, or emulating a file system.
    """


@dataclass(frozen=True)
class _FacadeContext:
    """What one ``PERFORM`` of a facade verb needs, in ``CALL`` parameter order.

    The five items are those every dispatch paragraph passes -
    ``call "acas022" using System-Record WS-Purch-Record File-Access File-Defs
    ACAS-DAL-Common-Data`` [copybooks/Proc-ACAS-FH-Calls.cob:L142-L148]. It owns no
    connection and no cursor; those belong to the data-access layer.
    """

    system_record: SystemRecord
    record: Any
    file_access: FileAccess
    file_defs: FileDefs
    dal_common: AcasDalCommonData

    #: NOT ONE OF THE FIVE OPERANDS, and deliberately last so the five above stay
    #: diffable against [copybooks/Proc-ACAS-FH-Calls.cob:L142-L148]. It is the
    #: caller's keyword-only handler declarations - chiefly the transport-security
    #: policy - which have no COBOL counterpart because the frozen bridge has none:
    #: its connect passes six values and no transport policy at all
    #: [copybooks/mysql-procedures.cpy:L72-L77], transport being compiled into
    #: ``cobmysqlapi.c``. An empty mapping is the SAFE answer, not the absent one:
    #: every handler resolves an unstated policy fail-closed, permitting a Unix
    #: socket or a loopback address and refusing every other target.
    dal_options: Mapping[str, object] = field(default_factory=dict)


#: How many operands a dispatch paragraph's ``CALL`` carries
#: [copybooks/Proc-ACAS-FH-Calls.cob:L142-L148]. Named once so the count is
#: stated rather than spelled as a literal inside the binding resolver.
_FACADE_LINKAGE_OPERANDS: Final[int] = 5


#: ``verb`` -> the callable the facade publishes for it, paired with the calling
#: convention that callable declares. Populated on the FIRST ``PERFORM`` of each
#: verb and read on every later one.
#:
#: ⭐ WHY A BINDING CACHE AND NOT REFLECTION AT EACH CALL. ``_fh`` is performed
#: inside the OTM4 row loop [purchase/pl060.cbl:L424-L543], so a per-call
#: ``getattr`` plus ``inspect.signature`` would re-derive one unchanging fact -
#: which shape ``acas_posting.dal.facade`` publishes - once per posted row.
#: ``inspect.signature`` is the expensive half: it builds a ``Signature`` object
#: and its ``Parameter`` objects from the callable's ``__code__`` every time it is
#: asked. Resolving it ONCE per verb removes that work from the loop and changes
#: nothing else.
#:
#: ⛔ THIS IS NOT A CACHE OF ANY VALUE, STATUS OR RESULT (rules R-3, R-6). What is
#: memoised is the BINDING - a function object and a boolean describing its
#: parameter list - which is a property of the imported module and cannot vary
#: between two calls in one process. Every ``PERFORM`` still issues its own call,
#: in source order, with its own freshly built operand list, and still reads its
#: status back out of ``File-Access`` afterwards. Nothing is reordered, batched,
#: deferred, coalesced or skipped, and no row's outcome depends on whether it was
#: the first to reach its verb: the compiled program's dynamic ``CALL`` resolves a
#: program name to an entry point once per run unit too
#: [copybooks/Proc-ACAS-FH-Calls.cob:L51-L57].
_FACADE_BINDINGS: Final[dict[str, tuple[Callable[..., Any], bool]]] = {}


def _facade_binding(verb: str) -> tuple[Callable[..., Any], bool]:
    """Resolve ``verb`` to ``(callable, takes_five_positionals)``, once per verb.

    ``verb`` is the entity-named facade paragraph in lower snake case, exactly as
    Agent Action Plan section 0.4.3 specifies the translation:
    ``perform GL-Batch-Read-Next`` becomes ``facade.gl_batch_read_next``.

    The boolean is ``True`` when the target declares at least the five operands of
    the dispatch paragraph - or a ``*args`` - and ``False`` when it declares fewer
    and must therefore be handed the facade's own single-argument context. That
    question is answered from the callable's declared signature, which is fixed
    once the module is imported, so it is answered once.

    Raises:
        _Pl060FacadeBindingError: the facade publishes no such verb, or publishes
            one that accepts no positional argument at all - an integration
            mismatch that must fail loudly at the seam rather than mis-post.
    """
    binding = _FACADE_BINDINGS.get(verb)
    if binding is not None:
        return binding

    try:
        target: Callable[..., Any] = getattr(facade, verb)
    except AttributeError as exc:  # pragma: no cover - integration guard
        raise _Pl060FacadeBindingError(
            f"acas_posting.dal.facade publishes no verb {verb!r}; the facade owns the "
            f"vocabulary of copybooks/Proc-ACAS-FH-Calls.cob and this module must not "
            f"reach a handler module directly"
        ) from exc

    try:
        signature = inspect.signature(target)
    except (TypeError, ValueError):  # pragma: no cover - integration guard
        #  No introspectable signature: the facade's published shape is the
        #  single-argument context, so that is what is supplied.
        takes_five = False
    else:
        accepts = [
            parameter
            for parameter in signature.parameters.values()
            if parameter.kind
            in (parameter.POSITIONAL_ONLY, parameter.POSITIONAL_OR_KEYWORD)
        ]
        variadic = any(
            parameter.kind is parameter.VAR_POSITIONAL
            for parameter in signature.parameters.values()
        )
        if len(accepts) >= _FACADE_LINKAGE_OPERANDS or variadic:
            takes_five = True
        elif accepts:
            takes_five = False
        else:  # pragma: no cover - integration guard
            raise _Pl060FacadeBindingError(
                f"acas_posting.dal.facade.{verb} accepts no positional argument, so "
                f"neither the context shape nor the five-parameter linkage shape of "
                f"copybooks/Proc-ACAS-FH-Calls.cob can be supplied"
            )

    binding = (target, takes_five)
    _FACADE_BINDINGS[verb] = binding
    return binding


def _fh(verb: str, ctx: _FacadeContext) -> tuple[int, int]:
    """Perform one facade verb and return the ``(FS-Reply, WE-Error)`` pair.

    One ``PERFORM`` is one call, in source order. Nothing is reordered, batched,
    deferred, coalesced or cached (rules R-3 and R-6) - see
    :data:`_FACADE_BINDINGS` for what IS memoised and why that is not a value
    cache.
    """
    target, takes_five = _facade_binding(verb)

    linkage = (
        ctx.system_record,
        ctx.record,
        ctx.file_access,
        ctx.file_defs,
        ctx.dal_common,
    )

    # THE CONTEXT SHAPE THE FACADE PUBLISHES. `facade.FacadeContext` carries the
    # dispatch paragraph's five operands positionally, in the copybook's order -
    # `(system, record, file_access, file_defs, dal_common)` - which is exactly
    # the order `linkage` is built in above. Handing the facade its own context
    # type rather than this module's private one keeps the operand list diffable
    # against [copybooks/Proc-ACAS-FH-Calls.cob:L142-L148] while leaving the
    # facade free to name its fields as it likes; `_FacadeContext` stays as the
    # module's own record of that operand list. `file_access` is the SAME object
    # either way, so `_status_pair` still reads the block the verb wrote.
    # This resolves AMBIGUITY Q-FILE-DEFS-SHAPE's sibling question - the shape of
    # the single argument - against the facade as generated.
    if takes_five:
        reply = target(*linkage)
    else:
        reply = target(facade.FacadeContext(*linkage))

    return _status_pair(reply, ctx.file_access)


def _status_pair(reply: Any, file_access: FileAccess) -> tuple[int, int]:
    """Normalise a facade return into the ``File-Access`` status protocol.

    ``01 File-Access`` [copybooks/wsfnctn.cob:L22-L26] is the shared block a COBOL
    ``CALL`` writes its status into - ``We-Error pic 999`` at L23 and ``Fs-Reply pic 99``
    at L25 - so the block, not the return value, is the protocol. Handlers that publish
    a pair as well as writing the block are honoured by copying the pair in first, which
    keeps the two in step whichever way the facade reports.
    """
    if isinstance(reply, tuple) and len(reply) == 2:
        first, second = reply
        if isinstance(first, int) and isinstance(second, int):
            file_access.fs_reply = first
            file_access.we_error = second
    return int(file_access.fs_reply), int(file_access.we_error)




# ---------------------------------------------------------------------------
# ``OI-Header`` construction and group moves.
#
# ``01 OI-Header`` [copybooks/plwsoi.cob:L12] is the layout all three of this program's
# open-item buffers share: the OTM4 record it reads, the working ``oi-header`` it posts
# from, and ``si-header`` [copybooks/plwssoi.cob:L11] which saves and restores it. A
# COBOL group move between identical layouts copies every elementary item unchanged, so
# each leaf below goes through ``acas_posting.cobol.move`` with its own descriptor
# rather than being assigned (rule R-2, Agent Action Plan section 0.3.1).
# ---------------------------------------------------------------------------

#: The group classes of ``OI-Header``, keyed by the attribute path that reaches them.
_OI_GROUPS: Final[dict[tuple[str, ...], type[Any]]] = {
    (): OiHeader,
    ("oi_key",): OiKey,
    ("oi_key", "oi_customer"): OiCustomer,
    ("oi_key", "oi_customer", "oi_supplier"): OiSupplier,
    ("oi_batch",): OiBatch,
    ("filler_1",): Filler1,
}


def _oi_leaf(parent: tuple[str, ...], attr: str) -> tuple[tuple[str, ...], FieldDescriptor]:
    """Pair one elementary item of ``OI-Header`` with the descriptor ``records/`` publishes."""
    return parent + (attr,), descriptors_of(_OI_GROUPS[parent])[attr]


#: Every elementary item of ``OI-Header``, in declaration order
#: [copybooks/plwsoi.cob:L12-L62]. ``oi_approp`` is carried alongside ``oi_net``
#: because ``05 OI-Approp redefines OI-Net`` names the same storage
#: [copybooks/plwsoi.cob:L44]; a group move copies those bytes once, so copying both
#: views keeps them in step exactly as the redefinition does.
_OI_ELEMENTARY: Final[tuple[tuple[tuple[str, ...], FieldDescriptor], ...]] = (
    _oi_leaf(("oi_key", "oi_customer", "oi_supplier"), "oi_nos"),
    _oi_leaf(("oi_key", "oi_customer", "oi_supplier"), "oi_check"),
    _oi_leaf(("oi_key",), "oi_invoice"),
    _oi_leaf((), "oi_date"),
    _oi_leaf(("oi_batch",), "oi_b_nos"),
    _oi_leaf(("oi_batch",), "oi_b_item"),
    _oi_leaf((), "oi_type"),
    _oi_leaf((), "oi_ref"),
    _oi_leaf((), "oi_order"),
    _oi_leaf((), "oi_hold_flag"),
    _oi_leaf((), "oi_unapl"),
    _oi_leaf(("filler_1",), "oi_p_c"),
    _oi_leaf(("filler_1",), "oi_net"),
    _oi_leaf(("filler_1",), "oi_approp"),
    _oi_leaf(("filler_1",), "oi_extra"),
    _oi_leaf(("filler_1",), "oi_carriage"),
    _oi_leaf(("filler_1",), "oi_vat"),
    _oi_leaf(("filler_1",), "oi_discount"),
    _oi_leaf(("filler_1",), "oi_e_vat"),
    _oi_leaf(("filler_1",), "oi_c_vat"),
    _oi_leaf(("filler_1",), "oi_paid"),
    _oi_leaf((), "oi_status"),
    _oi_leaf((), "oi_deduct_days"),
    _oi_leaf((), "oi_deduct_amt"),
    _oi_leaf((), "oi_deduct_vat"),
    _oi_leaf((), "oi_days"),
    _oi_leaf((), "oi_cr"),
    _oi_leaf((), "oi_applied"),
    _oi_leaf((), "oi_date_cleared"),
)


def _oi_get(record: OiHeader, path: tuple[str, ...]) -> Any:
    """Read one elementary item of ``OI-Header`` by its attribute path."""
    value: Any = record
    for attr in path:
        value = getattr(value, attr)
    return value


def _oi_set(record: OiHeader, path: tuple[str, ...], value: Any) -> None:
    """Write one elementary item of ``OI-Header`` by its attribute path."""
    owner: Any = record
    for attr in path[:-1]:
        owner = getattr(owner, attr)
    setattr(owner, path[-1], value)


def _new_oi_header() -> OiHeader:
    """Build an ``OI-Header`` buffer in the state COBOL WORKING-STORAGE starts in.

    Numeric items read as zero and alphanumeric items as spaces, which is what every
    figurative store in ``acas_posting.cobol.move`` yields for the respective category.
    """

    def zero(path: tuple[str, ...], attr: str) -> Any:
        """The ZERO figurative constant as the named numeric item receives it."""
        return mv.move_figurative(mv.ZERO, descriptors_of(_OI_GROUPS[path])[attr])

    def space(path: tuple[str, ...], attr: str) -> Any:
        """The SPACES figurative constant as the named alphanumeric item receives it."""
        return mv.move_figurative(mv.SPACES, descriptors_of(_OI_GROUPS[path])[attr])

    supplier = ("oi_key", "oi_customer", "oi_supplier")
    return OiHeader(
        oi_key=OiKey(
            oi_customer=OiCustomer(
                oi_supplier=OiSupplier(
                    oi_nos=space(supplier, "oi_nos"),
                    oi_check=zero(supplier, "oi_check"),
                )
            ),
            oi_invoice=zero(("oi_key",), "oi_invoice"),
        ),
        oi_date=zero((), "oi_date"),
        oi_batch=OiBatch(
            oi_b_nos=zero(("oi_batch",), "oi_b_nos"),
            oi_b_item=zero(("oi_batch",), "oi_b_item"),
        ),
        oi_type=zero((), "oi_type"),
        oi_ref=space((), "oi_ref"),
        oi_order=space((), "oi_order"),
        oi_hold_flag=space((), "oi_hold_flag"),
        oi_unapl=space((), "oi_unapl"),
        filler_1=Filler1(
            oi_p_c=zero(("filler_1",), "oi_p_c"),
            oi_net=zero(("filler_1",), "oi_net"),
            oi_approp=zero(("filler_1",), "oi_approp"),
            oi_extra=zero(("filler_1",), "oi_extra"),
            oi_carriage=zero(("filler_1",), "oi_carriage"),
            oi_vat=zero(("filler_1",), "oi_vat"),
            oi_discount=zero(("filler_1",), "oi_discount"),
            oi_e_vat=zero(("filler_1",), "oi_e_vat"),
            oi_c_vat=zero(("filler_1",), "oi_c_vat"),
            oi_paid=zero(("filler_1",), "oi_paid"),
        ),
        oi_status=zero((), "oi_status"),
        oi_deduct_days=zero((), "oi_deduct_days"),
        oi_deduct_amt=zero((), "oi_deduct_amt"),
        oi_deduct_vat=zero((), "oi_deduct_vat"),
        oi_days=zero((), "oi_days"),
        oi_cr=zero((), "oi_cr"),
        oi_applied=space((), "oi_applied"),
        oi_date_cleared=zero((), "oi_date_cleared"),
    )


def _group_move_oi(source: OiHeader, target: OiHeader) -> None:
    """``MOVE <group> TO <group>`` between two ``OI-Header``-shaped buffers.

    Used at ``[purchase/pl060.cbl:L428]`` (OTM4 record into ``oi-header``),
    ``[purchase/pl060.cbl:L592]`` and ``[purchase/pl060.cbl:L793]`` (OTM5 record into
    ``oi-header``), ``[purchase/pl060.cbl:L521]``, ``[purchase/pl060.cbl:L685]`` and
    ``[purchase/pl060.cbl:L870]`` (``oi-header`` into ``WS-OTM5-Record``), and
    ``[purchase/pl060.cbl:L773]`` / ``[purchase/pl060.cbl:L826]`` (``si-header``
    save and restore).
    """
    for path, descriptor in _OI_ELEMENTARY:
        _oi_set(
            target,
            path,
            mv.move(_oi_get(source, path), descriptor, sending_field=descriptor),
        )


def _initialize_with_filler(record: Any) -> None:
    """``INITIALIZE <group> WITH FILLER`` [purchase/pl060.cbl:L438].

    COBOL's ``INITIALIZE`` sets every elementary item of the group to its category
    default - numeric to zero, alphanumeric to spaces - and ``WITH FILLER`` extends that
    to the ``FILLER`` items too. It does NOT apply ``VALUE`` clauses. Both behaviours
    are reproduced by composing the figurative store ``acas_posting.cobol.move``
    publishes over every leaf; nothing about category defaults is decided here.

    ``acas_posting/cobol/move.py`` publishes no ``INITIALIZE`` primitive, so this
    composition is the reproduction rather than a re-implementation.

    FINDING - ``WITH FILLER`` IS present here, where the ``pl055`` twin writes plain
    ``initialize WS-Purch-Record`` [purchase/pl055.cbl:L547]. The two programs
    initialise the same record differently and the divergence is preserved.
    """
    for member in getattr(type(record), "__dataclass_fields__", {}).values():
        value = getattr(record, member.name)
        descriptor = member.metadata.get("descriptor")

        if isinstance(value, tuple):
            # ``05 PTurnover-q ... occurs 4`` [copybooks/wspl.cob:L51] - an OCCURS view.
            setattr(
                record,
                member.name,
                tuple(mv.move_figurative(mv.ZERO, descriptor) for _ in value),
            )
            continue

        if hasattr(type(value), "__dataclass_fields__"):
            _initialize_with_filler(value)
            continue

        if descriptor is None:  # pragma: no cover - records layer always supplies one
            continue

        figurative = mv.SPACES if descriptor.is_str else mv.ZERO
        setattr(record, member.name, mv.move_figurative(figurative, descriptor))


# ---------------------------------------------------------------------------
# Condition names.
#
# Every ``88``-level test in this program routes through
# ``acas_posting.cobol.condition_names``; none is written as a bare comparison
# (rule R-2, Agent Action Plan section 0.1.1 construct 12).
#
# Two names have to be qualified by copybook or they resolve wrongly.
# ``FS-Cobol-Files-Used`` has a homonym in ``copybooks/wsfnctn.cob``, and ``S-Closed``
# has a Sales twin in ``copybooks/slwsoi3.cob``; the registry exposes the collisions
# rather than silently picking one, so the copybook is named at each lookup.
# ---------------------------------------------------------------------------

#: ``88  G-L  value 1.`` on ``07 Level-1 pic 9`` [copybooks/wssystem.cob:L85].
_IS_G_L: Final[Callable[[Any], bool]] = cn.predicate_for("G-L")
#: ``88  FS-Cobol-Files-Used  value zero.`` on ``07 File-System-Used pic 9``
#: [copybooks/wssystem.cob:L113]. Its counterpart ``88 FS-RDBMS-Used value 1``
#: [copybooks/wssystem.cob:L116] is the configuration this migration targets.
_IS_FS_COBOL_FILES_USED: Final[Callable[[Any], bool]] = cn.predicate_for(
    "FS-Cobol-Files-Used", copybook="copybooks/wssystem.cob"
)
#: ``88  IRS-Used  value "Y".`` [copybooks/wssystem.cob:L180]
_IS_IRS_USED: Final[Callable[[Any], bool]] = cn.predicate_for("IRS-Used")
#: ``88  IRS-Both-Used  value "B".`` [copybooks/wssystem.cob:L181]
_IS_IRS_BOTH_USED: Final[Callable[[Any], bool]] = cn.predicate_for("IRS-Both-Used")
#: ``88  Supplier-dead  value 0.`` on ``03 Purch-Status pic 9``
#: [copybooks/wspl.cob:L20]. LIVE at [purchase/pl060.cbl:L503].
_IS_SUPPLIER_DEAD: Final[Callable[[Any], bool]] = cn.predicate_for(
    "Supplier-dead", copybook="copybooks/wspl.cob"
)
#: ``88  S-Closed  value 1.`` on ``03 OI-Status pic 9`` [copybooks/plwsoi.cob:L55].
#: LIVE at [purchase/pl060.cbl:L594] and [purchase/pl060.cbl:L799].
_IS_S_CLOSED: Final[Callable[[Any], bool]] = cn.predicate_for(
    "S-Closed", copybook="copybooks/plwsoi.cob"
)



# ---------------------------------------------------------------------------
# The OTM5 record area and its two byte-aligned views.
#
# ``pl060`` copies BOTH ``plwsoi5B.cob`` [purchase/pl060.cbl:L147] and
# ``plwsoi.cob`` [purchase/pl060.cbl:L152], and the ``copy ... replacing`` that would
# have made ``OI-Header`` redefine ``WS-OTM5-Record`` is commented out
# [copybooks/plwsoi5B.cob:L19-L20]. So the two are SEPARATE storage in this program,
# which is why ``[purchase/pl060.cbl:L521]`` has to group-move one into the other at all.
#
# Inside ``WS-OTM5-Record pic x(113)`` [copybooks/plwsoi5B.cob:L10] the redefinition
# ``Open-Item-Record-5`` [copybooks/plwsoi5B.cob:L12-L17] exposes only the key and the
# date::
#
#     03  oi5-key.
#         05 oi5-supplier    pic x(7).      <- the same 7 bytes as OI-Supplier
#         05 oi5-invoice     PIC 9(8).      <- the same 8 bytes as OI-Invoice
#     03  oi5-date           binary-long.   <- the same 4 bytes as OI-Date
#
# The generated data dictionary states that alignment independently: the descriptor for
# ``OI-Supplier`` carries the dictionary key ``PUITM5-REC.OI5-SUPPLIER`` and the one for
# ``OI-Invoice`` carries ``PUITM5-REC.OI5-INVOICE``. Writing ``oi5-supplier`` and
# writing ``OI-Supplier`` therefore write the same bytes, and the data-access layer
# models ``WS-OTM5-Record`` as an ``OI-Header`` for exactly that reason. The OTM5 record
# area is consequently held here as one ``OiHeader`` buffer, and the four ``oi5-*``
# stores [purchase/pl060.cbl:L775-L776], [purchase/pl060.cbl:L816-L817] are performed
# through the ``OI-Header`` view of the same storage.
# ---------------------------------------------------------------------------

#: ``05 oi5-supplier pic x(7)`` [copybooks/plwsoi5B.cob:L14].  DECLARED AND
#: DELIBERATELY UNREFERENCED: the frozen program's only use of the field is
#: ``display oi5-supplier`` [L528], and that display is not converted because a supplier
#: code is a record key, which the safe-event schema in ``acas_posting/dal/status.py``
#: excludes from a log record (CWE-532).  The descriptor stays so the field keeps its
#: dictionary citation, which is what rule R-5 asks of the group.
_D_OI5_SUPPLIER: Final[FieldDescriptor] = descriptors_of(Oi5Key)["oi5_supplier"]
#: ``05 oi5-invoice PIC 9(8)`` [copybooks/plwsoi5B.cob:L15].
_D_OI5_INVOICE: Final[FieldDescriptor] = descriptors_of(Oi5Key)["oi5_invoice"]

#: ``07 OI-Supplier`` viewed as the seven contiguous bytes it occupies
#: [copybooks/plwsoi.cob:L15-L17]. The group itself has no elementary picture, so the
#: byte view is declared here to serve the three statements that move or compare the
#: whole group: ``[purchase/pl060.cbl:L430]``, ``[purchase/pl060.cbl:L440]`` and
#: ``[purchase/pl060.cbl:L797]``.
_D_OI_SUPPLIER_GROUP: Final[FieldDescriptor] = pic.descriptor_for(
    "pic x(7)", name="OI-Supplier", source_locator="copybooks/plwsoi.cob:L15-L17"
)
#: ``09 OI-Nos Pic X(6)`` [copybooks/plwsoi.cob:L16].
_D_OI_NOS: Final[FieldDescriptor] = descriptors_of(OiSupplier)["oi_nos"]
#: ``09 OI-Check Pic 9`` [copybooks/plwsoi.cob:L17] seen as its single DISPLAY byte.
#: A ``DISPLAY`` digit IS its character, which is what makes the group image a
#: concatenation rather than an encoding.
_D_OI_CHECK_BYTE: Final[FieldDescriptor] = pic.descriptor_for(
    "pic x", name="OI-Check", source_locator="copybooks/plwsoi.cob:L17"
)

#: The attribute path of ``OI-Supplier``'s two leaves inside an ``OI-Header`` buffer.
_OI_SUPPLIER_PATH: Final[tuple[str, ...]] = ("oi_key", "oi_customer", "oi_supplier")


def _oi_supplier_image(record: OiHeader) -> str:
    """The seven-byte image of ``OI-Supplier``, for a group move or a group compare.

    ``03 WS-Purch-Key pic x(7)`` [copybooks/wspl.cob:L14] is an elementary
    alphanumeric, so ``move oi-supplier to WS-Purch-key``
    [purchase/pl060.cbl:L430] moves the group's bytes into it. Those bytes are
    ``OI-Nos``' six characters followed by ``OI-Check``'s one DISPLAY digit, and both
    halves are rendered through ``acas_posting.cobol.move`` rather than formatted here.
    """
    nos = mv.move_alphanumeric(_oi_get(record, _OI_SUPPLIER_PATH + ("oi_nos",)), _D_OI_NOS)
    check = mv.move_alphanumeric(
        _oi_get(record, _OI_SUPPLIER_PATH + ("oi_check",)), _D_OI_CHECK_BYTE
    )
    return mv.move_group(nos + check, _D_OI_SUPPLIER_GROUP)


def _move_supplier_group(source: OiHeader, target: OiHeader) -> None:
    """``MOVE <supplier group> TO oi5-supplier`` through the redefinition boundary.

    ``[purchase/pl060.cbl:L775]`` (``oi-supplier``) and ``[purchase/pl060.cbl:L816]``
    (``si-supplier``) both write the OTM5 record area's key. Because ``oi5-supplier``
    and ``OI-Supplier`` name the same seven bytes, the store is performed leaf by leaf
    on the ``OI-Header`` view, which is byte-identical and needs no re-encoding.
    """
    for attr in ("oi_nos", "oi_check"):
        descriptor = descriptors_of(OiSupplier)[attr]
        _oi_set(
            target,
            _OI_SUPPLIER_PATH + (attr,),
            mv.move(
                _oi_get(source, _OI_SUPPLIER_PATH + (attr,)),
                descriptor,
                sending_field=descriptor,
            ),
        )


# ---------------------------------------------------------------------------
# WORKING-STORAGE.
#
# ``01 ws-data`` [purchase/pl060.cbl:L189-L220] plus the record areas the program
# copies in, gathered into one object so that every paragraph function receives the
# program's storage exactly as a COBOL paragraph sees it - one shared, mutable area
# rather than arguments threaded by hand. Nothing is added: a field appears here only
# because it is declared in the frozen source, and each carries its declaration's line.
#
# STRUCTURAL NOTE - ``03 total-group occurs 3 comp-3`` [purchase/pl060.cbl:L214-L216]
# is a table of PAIRS, ``total-net`` and ``total-vat`` per occurrence, so
# ``total-net (a)`` and ``total-vat (a)`` index the same occurrence. It is held as two
# three-element lists because each is a distinct elementary item; the subscript is
# COBOL's, one-based, and the offset is stated at each use rather than hidden.
#
# STRUCTURAL NOTE - ``ws-Test-Date`` is a separate ``01`` in this program
# [purchase/pl060.cbl:L222] while ``ws-swap``, ``ws-Conv-Date`` and ``ws-date`` live in
# ``01 ws-date-formats`` [purchase/pl060.cbl:L223-L226]. ``acas_posting.dates`` bundles
# all four into ``WsDateFormats`` because the consolidated date sections need them
# together; the split in the frozen declaration is recorded here and has no observable
# consequence, since no statement in ``pl060`` moves the group as a whole.
# ---------------------------------------------------------------------------


@dataclass
class _Ws:
    """``pl060``'s storage: the linkage records, the file record areas and ``ws-data``."""

    # --- PROCEDURE DIVISION USING [purchase/pl060.cbl:L340-L344] ---------------
    ws_calling_data: WsCallingData
    system_record: SystemRecord
    system_record_4: SystemRecord4
    to_day: str
    file_defs: FileDefs

    # --- the file-handler linkage the facade needs ----------------------------
    #: ``copy "wsfnctn.cob"`` [purchase/pl060.cbl:L142]. Also the FILE STATUS field of
    #: ``open-item-file-4``: ``status fs-reply`` [copybooks/seloi4.cob:L4] names this
    #: very field, so the OTM4 verbs and the facade verbs share one status.
    file_access: FileAccess
    #: ``copy "Test-Data-Flags.cob"`` [purchase/pl060.cbl:L246] - the fifth argument of
    #: every handler call [copybooks/Proc-ACAS-FH-Calls.cob:L164-L170].
    dal_common: AcasDalCommonData

    # --- record areas [purchase/pl060.cbl:L146-L153] --------------------------
    #: ``01 WS-Purch-Record`` [copybooks/wspl.cob:L13].
    purch: WsPurchRecord
    #: ``01 WS-OTM5-Record`` / ``Open-Item-Record-5`` [copybooks/plwsoi5B.cob:L10-L17].
    otm5: OiHeader
    #: ``01 OI-Header`` [copybooks/plwsoi.cob:L12].
    oi_header: OiHeader
    #: ``01 si-header`` [copybooks/plwssoi.cob:L9] - byte-for-byte ``OI-Header``'s
    #: layout with ``si-`` names, so one class serves both.
    si_header: OiHeader
    #: ``01 WS-Batch-Record`` [copybooks/wsbatch.cob:L13].
    batch: GlBatchRecord
    #: ``01 WS-Posting-Record`` [copybooks/wspost.cob:L11].
    posting: WsPostingRecord
    #: ``01 WS-IRS-Posting-Record`` [copybooks/wspost-irs.cob:L13].
    irs_posting: WsIrsPostingRecord

    # --- fd open-item-file-4 [copybooks/seloi4.cob], [copybooks/fdoi4.cob] ----
    #: The OTM4 extract ``pl055`` produced. See the STRUCTURAL NOTES above.
    otm4: OpenItemWorkFile[OiHeader]

    # --- the date sections' storage -------------------------------------------
    #: ``01 maps03-ws`` [copybooks/wsmaps03.cob:L6] - the ``maps04`` linkage record.
    maps03_ws: Maps03Ws
    #: ``ws-Test-Date`` and ``01 ws-date-formats`` [purchase/pl060.cbl:L222-L226].
    date_ws: WsDateFormats

    # --- 01 ws-data [purchase/pl060.cbl:L189-L220] ---------------------------
    #: ``03 save-level-1 pic 9 value zero.`` [purchase/pl060.cbl:L190]
    save_level_1: int = 0
    #: ``03 ws-reply pic x.`` [purchase/pl060.cbl:L191] - no VALUE clause.
    ws_reply: str = " "
    #: ``03 ws-error pic 9 value zero.`` [purchase/pl060.cbl:L192]
    ws_error: int = 0
    #: ``03 wx-reply pic xxx.`` [purchase/pl060.cbl:L194]
    wx_reply: str = "   "
    #: ``03 xx pic 99.`` [purchase/pl060.cbl:L195] - the ``STRING`` pointer.
    xx: int = 0
    #: ``03 c-check pic 9.`` [purchase/pl060.cbl:L196]
    c_check: int = 0
    #: ``03 ws-eval-msg pic x(25) value spaces.`` [purchase/pl060.cbl:L198]
    ws_eval_msg: str = " " * 25
    #: ``03 work-1 pic s9(7)v99 comp-3 value zero.`` [purchase/pl060.cbl:L199]
    work_1: Decimal = Decimal("0.00")
    #: ``03 work-2 pic s9(14) comp-3.`` [purchase/pl060.cbl:L200] - FOURTEEN digits and
    #: ZERO scale. Anomaly A-8's first truncation lives in that scale; see
    #: ``_purch_comp``.
    work_2: int = 0
    #: ``03 work-a pic s9(7)v99 comp-3 value zero.`` [purchase/pl060.cbl:L201]
    work_a: Decimal = Decimal("0.00")
    #: ``03 work-b pic s9(7)v99 comp-3 value zero.`` [purchase/pl060.cbl:L202] - the
    #: accumulator that becomes period total 8 at ``[purchase/pl060.cbl:L628]``.
    work_b: Decimal = Decimal("0.00")
    #: ``03 first-pass pic x.`` [purchase/pl060.cbl:L203] - no VALUE clause.
    first_pass: str = " "
    #: ``03 i pic 999.`` [purchase/pl060.cbl:L204]
    i: int = 0
    #: ``03 j pic 999.`` [purchase/pl060.cbl:L205] - the page counter.
    j: int = 0
    #: ``03 k pic 9(5).`` [purchase/pl060.cbl:L206]
    k: int = 0
    #: ``03 m pic z(7)9.`` [purchase/pl060.cbl:L207] - the zero-suppressed edited field
    #: the posting legend is built from.
    m: str = " " * 8
    #: ``03 a pic 9 value zero.`` [purchase/pl060.cbl:L208] - the ``total-group``
    #: subscript, taken straight from ``oi-type`` and never range-checked.
    a: int = 0
    #: ``03 b binary-char value zero.`` [purchase/pl060.cbl:L209]
    b: int = 0
    #: ``03 c binary-char value zero.`` [purchase/pl060.cbl:L210]
    c: int = 0
    #: ``03 work-net pic s9(7)v99 comp-3.`` [purchase/pl060.cbl:L211]
    work_net: Decimal = Decimal("0.00")
    #: ``03 work-vat pic s9(7)v99 comp-3.`` [purchase/pl060.cbl:L212]
    work_vat: Decimal = Decimal("0.00")
    #: ``03 work-goods pic s9(7)v99 comp-3.`` [purchase/pl060.cbl:L213] - TWO decimals,
    #: which is the other half of anomaly A-8.
    work_goods: Decimal = Decimal("0.00")
    #: ``05 total-net pic s9(7)v99`` of ``total-group occurs 3``
    #: [purchase/pl060.cbl:L215]. One-based subscript; index with ``subscript - 1``.
    total_net: list[Decimal] = field(
        default_factory=lambda: [Decimal("0.00"), Decimal("0.00"), Decimal("0.00")]
    )
    #: ``05 total-vat pic s9(7)v99`` of ``total-group occurs 3``
    #: [purchase/pl060.cbl:L216].
    total_vat: list[Decimal] = field(
        default_factory=lambda: [Decimal("0.00"), Decimal("0.00"), Decimal("0.00")]
    )
    #: ``03 line-cnt binary-char value zero.`` [purchase/pl060.cbl:L217]. Presentation
    #: drives it, but ``[purchase/pl060.cbl:L556]``, ``[purchase/pl060.cbl:L619]``,
    #: ``[purchase/pl060.cbl:L541]`` and ``[purchase/pl060.cbl:L679]`` all TEST it, so
    #: it is maintained here even though no line is printed - see the OMISSIONS list.
    line_cnt: int = 0
    #: ``03 File-28-status pic 9 value zero.`` [purchase/pl060.cbl:L218] with
    #: ``88 File-28-Exists value 0`` and ``88 File-28-Not-Exists value 1``
    #: [purchase/pl060.cbl:L219-L220]. Program-local, so its condition names are the
    #: two module constants rather than registry rows.
    file_28_status: int = _FILE_28_EXISTS
    #: ``01 error-code pic 999.`` [purchase/pl060.cbl:L259]
    error_code: int = 0

    #: NOT A COBOL FIELD. The caller's keyword-only handler declarations - chiefly
    #: the transport-security policy - carried onto every facade context this
    #: program builds. No COBOL counterpart: the frozen bridge's connect passes six
    #: values and no transport policy at all
    #: [copybooks/mysql-procedures.cpy:L72-L77]. An empty mapping is the SAFE
    #: answer, not the absent one - an unstated policy resolves fail-closed,
    #: permitting a Unix socket or a loopback address and refusing every other
    #: target. Carried opaquely; ``dal/facade.py`` projects it onto whatever extras
    #: each handler declares.
    dal_options: Mapping[str, object] = field(default_factory=dict)


def _is_purchase_missing(ws: _Ws) -> bool:
    """``88 purchase-missing value 1.`` on ``03 ws-error pic 9``
    [purchase/pl060.cbl:L192-L193].

    Program-local, so it is not a row of the condition-name registry; the comparison is
    against the declared ``VALUE`` and nothing else. Tested at
    ``[purchase/pl060.cbl:L630]``.
    """
    return ws.ws_error == _WS_ERROR_PURCHASE_MISSING


def _is_file_28_exists(ws: _Ws) -> bool:
    """``88 File-28-Exists value 0.`` [purchase/pl060.cbl:L219].

    Tested at ``[purchase/pl060.cbl:L620]``, ``[purchase/pl060.cbl:L623]`` and
    ``[purchase/pl060.cbl:L640]``.
    """
    return ws.file_28_status == _FILE_28_EXISTS


def _is_file_28_not_exists(ws: _Ws) -> bool:
    """``88 File-28-Not-Exists value 1.`` [purchase/pl060.cbl:L220].

    Tested at ``[purchase/pl060.cbl:L665]``.
    """
    return ws.file_28_status == _FILE_28_NOT_EXISTS


def _ctx(ws: _Ws, record: Any) -> _FacadeContext:
    """The five linkage items one facade ``PERFORM`` needs, for ``record``'s entity.

    ``[copybooks/Proc-ACAS-FH-Calls.cob:L138-L170]`` shows the shape being reproduced:
    every handler dispatch is ``call "acasNNN" using System-Record <entity record>
    File-Access File-Defs ACAS-DAL-Common-Data``, so the only thing that varies between
    entities is the second argument.

    AMBIGUITY Q-FILE-DEFS-SHAPE - the handler modules declare their fourth parameter as
    ``FileDefsA`` while ``PROCEDURE DIVISION USING`` hands this program ``File-Defs``,
    whose ``file_defs_a`` member is that group [copybooks/wsnames.cob]. ``File-Defs`` is
    passed through unchanged, because reaching inside it here would make this module
    depend on the handler's parameter shape, which the layering in Agent Action Plan
    section 0.4.3 forbids. Whether the facade unwraps it is the facade's business and is
    recorded rather than assumed.
    """
    return _FacadeContext(
        system_record=ws.system_record,
        record=record,
        file_access=ws.file_access,
        file_defs=ws.file_defs,
        dal_common=ws.dal_common,
        dal_options=ws.dal_options,
    )


def _otm4_status(ws: _Ws) -> None:
    """Publish the OTM4 work file's status into ``fs-reply``.

    ``select open-item-file-4 ... status fs-reply`` [copybooks/seloi4.cob:L2-L4] names
    the very field ``copy "wsfnctn.cob"`` declares [copybooks/wsfnctn.cob:L23-L38], so
    in the compiled program an OTM4 ``open``, ``read`` or ``close`` writes the SAME
    status the facade verbs write. Mirroring it keeps that sharing observable instead of
    quietly giving the work file a private status.
    """
    ws.file_access.fs_reply = ws.otm4.fs_reply


#  ⭐⭐ THE ``pl055`` -> ``pl060`` HANDOFF IS ONE OBJECT, SUPPLIED BY THE CALLER.
#  ``select open-item-file-4 assign file-28`` [copybooks/seloi4.cob:L1] names a FILE, and a
#  file outlives the program that opened it: ``pl055`` writes the extract
#  [purchase/pl055.cbl:L301, :L587, :L423], this program reads it at
#  [purchase/pl060.cbl:L421-L425] and then truncates it at [purchase/pl060.cbl:L605].
#  In COBOL the two programs name the same ``ASSIGN`` and the operating system supplies the
#  identity; here the identity is the ``acas_posting.workfiles.OpenItemWorkFile`` the ROUTE
#  threads from one dispatch to the next, exactly as it threads the General Ledger work
#  files from ``gl070`` to ``gl071`` to ``gl072``.
#
#  THE LINKAGE IS NOT WIDENED TO CARRY IT. ``PROCEDURE DIVISION USING`` has exactly five
#  entries [purchase/pl060.cbl:L340-L344] and a sixth would misrepresent it, so the carrier
#  is a KEYWORD-ONLY parameter of ``run`` - outside the positional linkage, which is the
#  same device ``gl070``, ``gl071`` and ``gl072`` use for their work files.
#
#  ⛔ THIS WAS ONCE A MODULE-LEVEL REGISTRY keyed by the assigned name, on the ground that a
#  single ``run`` call cannot own a file and that ``workfiles.py`` published no carrier for
#  it. The first half was right; the second was a gap to be closed rather than worked
#  around. A registry also shares the sequence across every run in one interpreter, and
#  rule R-6 requires two runs of the same scenario under the same pinned clock to be
#  byte-identical - a sequence still holding the previous run's orders breaks that with
#  nothing failing.


def run(
    ws_calling_data: WsCallingData,
    system_record: SystemRecord,
    system_record_4: SystemRecord4,
    to_day: str,
    file_defs: FileDefs,
    *,
    open_item_file_4: OpenItemWorkFile[OiHeader] | None = None,
) -> None:
    """``pl060`` - post the OTM4 purchase-order extract. The program's single entry.

    Mirrors ``procedure division using ws-calling-data system-record system-record-4
    to-day file-defs`` [purchase/pl060.cbl:L340-L344] - the five-parameter Sales and
    Purchase linkage shape, in that order. The General Ledger family takes four and the
    IRS program takes three; Agent Action Plan section 0.1.1 records all three shapes and
    they are NOT unified.

    Args:
        ws_calling_data: ``01 WS-Calling-Data`` [copybooks/wscall.cob:L6-L13].
            ``WS-Caller`` is read at ``[purchase/pl060.cbl:L536]``,
            ``[purchase/pl060.cbl:L660]`` and ``[purchase/pl060.cbl:L1022]``, where the
            value ``"xl150"`` suppresses an operator pause.
        system_record: ``01 System-Record`` [copybooks/wssystem.cob]. Read for the
            ledger switches and WRITTEN at ``[purchase/pl060.cbl:L373-L375]``,
            ``[purchase/pl060.cbl:L887]`` and ``[purchase/pl060.cbl:L1028]``.
        system_record_4: ``01 System-Record-4`` [copybooks/wssys4.cob]. Written once, at
            ``[purchase/pl060.cbl:L628]`` - period total 8.
        to_day: ``to-day pic x(10)``, the run date in ``DD/MM/CCYY``. It arrives through
            linkage and is never read from a clock (rule R-6).
        file_defs: ``01 File-Defs`` [copybooks/wsnames.cob]. ``File-28`` names the OTM4
            extract file and ``File-29`` the OTM5 file; both are read at
            ``[purchase/pl060.cbl:L377]``, ``[purchase/pl060.cbl:L388]``,
            ``[purchase/pl060.cbl:L610]`` and ``[purchase/pl060.cbl:L641]``.
        open_item_file_4: the OTM4 extract file. NOT part of the linkage - the frozen
            ``PROCEDURE DIVISION USING`` has exactly the five entries above
            [purchase/pl060.cbl:L340-L344] and the file arrives through ``File-Defs``
            exactly as it does in COBOL. Defaults to the file ``file-28`` names, resolved
            out of the SHARED registry by ``_otm4_file``, which is the very file ``pl055``
            appended to. This keyword exists so a test can supply an isolated file; a
            caller wanting the frozen handoff should leave it alone and pass matching
            ``File-Defs`` to both programs.

    Returns:
        None. ``exit-prog.`` performs ``exit program.`` [purchase/pl060.cbl:L650-L651],
        not ``goback``, and a sub-program's ``exit program`` yields no value.

    Note:
        Exactly five parameters, in the frozen source's order. Everything else this program
        needs it obtains by ``COPY`` rather than by linkage, so it is built here as
        WORKING-STORAGE is built at program entry: ``01 File-Access``
        [copybooks/wsfnctn.cob:L23-L38] copied at ``[purchase/pl060.cbl:L142]``,
        ``01 ACAS-DAL-Common-Data`` copied at ``[purchase/pl060.cbl:L246]``, and the six
        record areas copied at ``[purchase/pl060.cbl:L146-L153]``. The OTM4 sequence is a
        FILE and therefore outlives the call, so it arrives as the keyword-only
        ``open_item_file_4`` rather than being declared here; see the note above ``run``.
    """
    ws = _Ws(
        ws_calling_data=ws_calling_data,
        system_record=system_record,
        system_record_4=system_record_4,
        to_day=to_day,
        file_defs=file_defs,
        # ``copy "wsfnctn.cob"`` [purchase/pl060.cbl:L142] - WORKING-STORAGE, not linkage.
        file_access=FileAccess(),
        # ``copy "Test-Data-Flags.cob"`` [purchase/pl060.cbl:L246].
        dal_common=AcasDalCommonData(),
        purch=WsPurchRecord(),  # copy "wspl.cob"        [L146]
        otm5=_new_oi_header(),  # copy "plwsoi5B.cob"    [L147]
        oi_header=_new_oi_header(),  # copy "plwsoi.cob"      [L152]
        si_header=_new_oi_header(),  # copy "plwssoi.cob"     [L153]
        batch=GlBatchRecord(),  # copy "wsbatch.cob"     [L148]
        posting=WsPostingRecord(),  # copy "wspost.cob"      [L149]
        irs_posting=WsIrsPostingRecord(),  # copy "wspost-irs.cob"  [L150]
        # ⭐ SUPPLIED BY THE CALLER: the very carrier ``pl055`` wrote, which is how
        # [L425] reads what [purchase/pl055.cbl:L587] wrote. A None means this
        # program was run alone, in which case the file is declared empty and [L425]
        # takes its ``at end`` branch at once - as it would against an empty file.
        otm4=(
            open_item_work_file(OPEN_ITEM_4_NAME, OiHeader)
            if open_item_file_4 is None
            else open_item_file_4
        ),  # copy "seloi4"/"fdoi4"  [L125]/[L134]
        maps03_ws=Maps03Ws(),  # copy "wsmaps03.cob"    [L141]
        date_ws=WsDateFormats(),  # 01 ws-Test-Date [L222] + 01 ws-date-formats [L223]
        # NOT a linkage operand, NOT a parameter of `run`, and NOT bound here: the
        # transport policy reaches every handler through the one process-level
        # policy the CLI boundary installs, so this field keeps its declared `{}`,
        # which every handler resolves fail-closed. See
        # `acas_posting.cli.args.install_connection_policy`.
    )
    _init01(ws)



# ---------------------------------------------------------------------------
# The GnuCOBOL library routines (rule R-1).
# ---------------------------------------------------------------------------


def _cbl_check_file_exist(ws: _Ws, file_name: str, locator: str) -> int:
    """``call "CBL_CHECK_FILE_EXIST" using File-nn File-Info`` - NOT invoked (rule R-1).

    Three sites: ``[purchase/pl060.cbl:L377]`` (``File-29``),
    ``[purchase/pl060.cbl:L388]`` and ``[purchase/pl060.cbl:L610]`` (both ``File-28``).
    All three sit inside ``if FS-Cobol-Files-Used``, which is the flat-file setting of
    ``07 File-System-Used`` [copybooks/wssystem.cob:L112-L113]; the RDBMS setting
    ``88 FS-RDBMS-Used value 1`` [copybooks/wssystem.cob:L116] is what this migration
    targets, so no scenario reaches here.

    The GUARD is reproduced by the caller so the decision stays data-driven; the PROBE
    is not, because rule R-1 forbids executing a COBOL library routine and emulating a
    file system would invent behaviour the frozen program does not have.
    """
    raise _Pl060CobolLibraryRoutineUnavailable(
        f"CBL_CHECK_FILE_EXIST using {file_name} at [{locator}] was reached. Rule R-1 "
        f"forbids invoking a COBOL library routine, and this branch is unreachable "
        f"whenever FS-RDBMS-Used holds [copybooks/wssystem.cob:L116]. The configured "
        f"file system is File-System-Used="
        f"{ws.system_record.system_data_block.rdbms_flat_statuses.file_system_used}."
    )


def _cbl_delete_file(ws: _Ws, file_name: str, locator: str) -> None:
    """``call "CBL_DELETE_FILE" using File-28`` - NOT invoked (rule R-1).

    One site, ``[purchase/pl060.cbl:L641]``, behind the same guard as the probes above
    plus ``File-28-Exists``. See :func:`_cbl_check_file_exist`.
    """
    raise _Pl060CobolLibraryRoutineUnavailable(
        f"CBL_DELETE_FILE using {file_name} at [{locator}] was reached. Rule R-1 forbids "
        f"invoking a COBOL library routine, and this branch is unreachable whenever "
        f"FS-RDBMS-Used holds [copybooks/wssystem.cob:L116]. The configured file system "
        f"is File-System-Used="
        f"{ws.system_record.system_data_block.rdbms_flat_statuses.file_system_used}."
    )


# ===========================================================================
# init01  section.                                    [purchase/pl060.cbl:L347]
#
# The section runs from L347 to L651 and holds SEVEN paragraphs: its unnamed first
# paragraph, then ``acpt-xrply`` L362, ``loop`` L424, ``main-end`` L545, ``end-loop``
# L585, ``end-loop-end`` L602 and ``exit-prog`` L650. The next ``section.`` is
# ``cr-swop`` at L653, which is why ``go to main-end`` and ``go to loop`` are ordinary
# intra-section transfers. Each paragraph is its own function below, section-qualified
# because ``main-end`` and ``end-loop`` are each declared twice in this program.
# ===========================================================================


def _init01(ws: _Ws) -> None:
    """``init01 section.`` - set up, open the files, then run the section's paragraphs.

    Carries the section's unnamed first paragraph ``[purchase/pl060.cbl:L348-L360]`` and
    the statements from ``[purchase/pl060.cbl:L372]`` to ``[purchase/pl060.cbl:L422]``,
    then performs the remaining paragraphs in source order exactly as COBOL falls
    through them: ``acpt-xrply``, ``loop``, ``main-end``, ``end-loop``, ``end-loop-end``,
    ``exit-prog``.

    FINDING - the paragraph boundary and the brief's boundary differ by intent.
    ``acpt-xrply.`` at L362 opens a paragraph that formally extends to the next label,
    ``loop.`` at L424, so L372-L422 belong to it in COBOL's own terms. Because its own
    nine statements are commented out and L372 onward is plainly the section's setup,
    those statements are carried here and ``acpt-xrply`` is the empty named function rule
    R-5 requires. No statement moves, is duplicated or is skipped by that choice.
    """
    # [L348] move prog-name to l1-name.  [L349] move to-day to l1-date.
    # [L350] move Print-Spool-Name to PSN.
    # OMITTED - all three build print-page furniture. ``l1-name`` and ``l1-date`` are
    # items of ``01 line-1`` [purchase/pl060.cbl:L268-L270] and ``PSN`` belongs to
    # ``copy "print-spool-command.cob"`` [purchase/pl060.cbl:L140]. Presentation with no
    # database effect; see the OMISSIONS list.
    #
    # [L352] set ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".
    # [L353] set ENVIRONMENT "COB_SCREEN_ESC" to "Y".
    # OMITTED - they configure the curses screen handler for key detection. There is no
    # screen here, so there is nothing to configure; representation only.
    #
    # FINDING - [L400-L401] `move level-1 to save-level-1.` / `move 0 to level-1.` are
    # COMMENTED OUT under the maintainer's own banner "BYPASS CODE TO SEND TOTALS TO GL"
    # [purchase/pl060.cbl:L397-L403]. `03 save-level-1` [purchase/pl060.cbl:L190] is
    # therefore declared and never written anywhere in the program. Declared here for the
    # same reason - rule R-5 - and left unwritten.

    # [L355-L357] the banner displays. Agent Action Plan section 0.3.4: a diagnostic
    # display with no database effect becomes a log record, must not alter control flow,
    # and must not appear in any table dump.
    _LOG.info("%s - %s", _PROG_NAME, _TITLE)

    _zz070_convert_date(ws)  # [L358] perform zz070-Convert-Date.
    # [L359] display ws-date at 0171.  NO LOG COUNTERPART: ``ws-date`` is the posting
    # date this run stamps into the records it writes - a date with business meaning,
    # which the safe-event schema in ``acas_posting/dal/status.py`` excludes (CWE-532).
    # It is an INPUT the caller supplied through ``to-day``, already known wherever the
    # run was started and pinned by ``clock.py``.  The conversion above still runs: it
    # stores ``ws-date`` and may default ``Date-Form``, which IS a table effect.

    # [L360] move 1 to File-Key-No.
    # ``File-Key-No`` is an item of ``Logging-Data`` inside ``File-Access``
    # [copybooks/wsfnctn.cob:L44-L56], not of any entity record.
    ws.file_access.logging_data.file_key_no = mv.move(
        1, _desc(ws.file_access.logging_data, "File-Key-No")
    )

    _init01__acpt_xrply(ws)  # [L362] fall-through into the paragraph.

    # [L372] display space at 0801 with erase eol.  NOT A LOG RECORD.  Its whole
    # operand is a SPACE and its whole purpose is to blank the line the commented-out
    # confirmation prompt [L363-L365] would have occupied: there is no diagnostic
    # content to convert, and narrating the erase would emit an event the compiled
    # program never produced (R-4).  Screen geometry is out of scope besides.

    # [L373-L375] THREE SYSTEM-REC COLUMNS ARE WRITTEN HERE, and all three are
    # diff-visible. The maintainer's own comments give the reasons: ``P-Flag-I`` marks
    # invoice lines, ``P-Flag-A`` applied records, and ``Oi-5-Flag`` "sets changes to
    # file so pl115 sort needed" - a downstream sort requirement.
    ws.system_record.purchase_ledger_block.p_flag_i = mv.move(
        2, _desc(ws.system_record.purchase_ledger_block, "P-Flag-I")
    )
    ws.system_record.purchase_ledger_block.p_flag_a = mv.move(
        1, _desc(ws.system_record.purchase_ledger_block, "P-Flag-A")
    )
    # FINDING - ``Oi-5-Flag`` is declared in the SALES block
    # [copybooks/wssystem.cob], yet ``pl060`` writes it. A cross-ledger write, preserved.
    ws.system_record.sales_ledger_block.oi_5_flag = mv.move(
        "Y", _desc(ws.system_record.sales_ledger_block, "Oi-5-Flag")
    )

    # [L376-L383] THE FIRST LIBRARY GATE. Unlike the ``pl055`` twin's, this gate's body
    # performs FACADE VERBS as well as the probe, so the verbs are reproduced in full and
    # only the probe is omitted (rule R-1). They are unreachable in the RDBMS
    # configuration for the same reason the probe is: the guard is false there.
    if _IS_FS_COBOL_FILES_USED(
        ws.system_record.system_data_block.rdbms_flat_statuses.file_system_used
    ):
        return_code = _cbl_check_file_exist(  # [L377-L378] using File-29 File-Info
            ws, "File-29", "purchase/pl060.cbl:L377"
        )
        if return_code != 0:  # [L379] not = zero - No file found
            # ``OTM5-Open-Output`` [copybooks/Proc-ACAS-FH-Calls.cob:L1268] creates the
            # open-item file; the immediate close leaves it empty.
            _fh("otm5_open_output", _ctx(ws, ws.otm5))  # [L380]
            _fh("otm5_close", _ctx(ws, ws.otm5))  # [L381]

    # [L385] The maintainer's own note: "File-18 settings used elsewhere in program but
    # file IS created in sl055 so a bit pointless .."
    #
    # [L387-L395] THE SECOND LIBRARY GATE. Its body only SETS a condition-name flag, so
    # nothing but the flag survives; the flag itself is load-bearing and is tested at
    # [L620], [L623], [L640] and [L665].
    if _IS_FS_COBOL_FILES_USED(
        ws.system_record.system_data_block.rdbms_flat_statuses.file_system_used
    ):
        return_code = _cbl_check_file_exist(  # [L388-L389] using File-28 File-Info
            ws, "File-28", "purchase/pl060.cbl:L388"
        )
        if return_code != 0:  # [L390]
            ws.file_28_status = _FILE_28_NOT_EXISTS  # [L391] set File-28-Not-Exists
        else:
            ws.file_28_status = _FILE_28_EXISTS  # [L393] set File-28-Exists

    # [L405-L406] BL-Open runs ONLY under G-L. ``BL-Write`` [L474-L475] and ``BL-Close``
    # [L573-L574] carry the same guard, so the three are consistent within this program.
    # ``pl100`` diverges on exactly this point and is not harmonised with it.
    if _IS_G_L(ws.system_record.system_data_block.level.level_1):
        _bl_open(ws)

    _fh("purch_open", _ctx(ws, ws.purch))  # [L408] open i-o purchase-file.

    # [L410] open output print-file.  OMITTED - the whole print file; see OMISSIONS.
    # [L411-L413] displays, including the program's own phase label.
    _LOG.info("Posting......Please Wait - Phase 1")

    ws.j = mv.move(mv.ZERO, _D_J)  # [L415] move zero to j.
    _headings(ws)  # [L416] perform headings.

    # [L418-L419] Two three-receiver MOVEs with EXPLICIT LITERAL SUBSCRIPTS. COBOL
    # subscripts are one-based, so occurrence n is index n-1 here. Written as one
    # ``move_to_all`` per statement, never as a loop, because the frozen source names the
    # three receivers individually.
    ws.total_net[0], ws.total_net[1], ws.total_net[2] = mv.move_to_all(
        mv.ZEROS, (_D_TOTAL_NET, _D_TOTAL_NET, _D_TOTAL_NET)
    )
    ws.total_vat[0], ws.total_vat[1], ws.total_vat[2] = mv.move_to_all(
        mv.ZEROS, (_D_TOTAL_VAT, _D_TOTAL_VAT, _D_TOTAL_VAT)
    )

    ws.otm4.open_input(ws.file_access)  # [L421] open input open-item-file-4.
    _otm4_status(ws)
    _fh("otm5_open", _ctx(ws, ws.otm5))  # [L422] open i-o open-item-file-5.

    _init01__loop(ws)  # [L424] fall-through into the OTM4 walk.
    # GO TO class 2 - [L426] `go to main-end` leaves the loop, and the post-loop work is
    # placed here in full. Agent Action Plan section 0.6.3: "the transformation is
    # `break` PLUS faithful placement of that work after the loop, not `break` alone.
    # Mis-splitting here would silently drop end-of-run processing." That work is
    # enormous in this program - the closes and totals of [L548-L583], then the OTM5
    # second pass, then the OTM4 truncation and PERIOD TOTAL 8 of [L605-L641].
    _init01__main_end(ws)  # [L545]
    _init01__end_loop(ws)  # [L585] reached by fall-through from main-end.
    _init01__end_loop_end(ws)  # [L602] reached by GO TO class 2 from [L590].
    _init01__exit_prog(ws)  # [L650] reached by fall-through.


def _init01__acpt_xrply(ws: _Ws) -> None:
    """``acpt-xrply.`` [purchase/pl060.cbl:L362] - AN EMPTY PARAGRAPH.

    FINDING - the paragraph's entire body ``[purchase/pl060.cbl:L363-L371]`` is
    COMMENTED OUT: the "OK to post Purchase Transactions (YES/NO) ?" prompt, the accept,
    the upper-case fold, the ``go to exit-prog`` on "NO" and the ``go to acpt-xrply``
    retry on anything but "YES". **There is therefore NO run-confirm gate in ``pl060``**,
    where ``sl100`` still has a live one ``[sales/sl100.cbl:L310-L319]``. Two of the
    program's fields exist only for that dead prompt: ``03 wx-reply pic xxx``
    ``[purchase/pl060.cbl:L194]`` and the two commented-out transfers are why the ``go
    to`` census counts 25 grep hits but only 23 LIVE sites.

    The paragraph is kept as a named function because rule R-5 requires one per label and
    Agent Action Plan section 0.7.4 C-4 requires it "even where its ``GO TO`` becomes a
    ``continue``, a ``break`` or a ``return``". It does nothing, which is what the
    compiled program does here.
    """
    # [L363] display "OK to post Purchase Transactions (YES/NO) ?  [   ]" - commented out
    # [L364] move spaces to wx-reply.                                    - commented out
    # [L365] accept wx-reply at 0858 with foreground-color 6 update.     - commented out
    # [L366] move function upper-case (wx-reply) to wx-reply.            - commented out
    # [L367-L368] if wx-reply = "NO" go to exit-prog.                    - commented out
    # [L369-L370] if wx-reply not = "YES" go to acpt-xrply.              - commented out
    del ws


def _init01__exit_prog(ws: _Ws) -> None:
    """``exit-prog.`` [purchase/pl060.cbl:L650-L651].

    FINDING - the verb is ``exit program.``, not ``goback``. In a called sub-program the
    two are equivalent in effect, and the frozen spelling is recorded rather than
    modernised. ``run`` returns ``None`` here, which is the whole of it.
    """
    del ws



# ---------------------------------------------------------------------------
# Record-field descriptors, resolved once from the ``records/`` layer.
#
# Every one comes from ``_desc``, so every one carries the dictionary provenance the
# generated data dictionary gave it (rule R-5). Nothing here parses a picture clause or
# decides a scale - that is ``acas_posting/cobol/``'s job and this module has no numeric
# primitives of its own (Agent Action Plan section 0.3.1).
# ---------------------------------------------------------------------------

# ``01 WS-Purch-Record`` [copybooks/wspl.cob:L13-L54]
_D_WS_PURCH_KEY: Final[FieldDescriptor] = _desc(WsPurchRecord, "WS-Purch-Key")
_D_PURCH_STATUS: Final[FieldDescriptor] = _desc(WsPurchRecord, "Purch-Status")
_D_PURCH_NAME: Final[FieldDescriptor] = _desc(WsPurchRecord, "Purch-Name")
#: ``03 Purch-Activety binary-long`` [copybooks/wspl.cob:L35] - SIGNED, and an INTEGER.
_D_PURCH_ACTIVETY: Final[FieldDescriptor] = _desc(WsPurchRecord, "Purch-Activety")
#: ``03 Purch-Average binary-long`` [copybooks/wspl.cob:L38] - SIGNED, and an INTEGER.
#: The integer receiver is the second half of anomaly A-8's double truncation, and the
#: signed declaration is what anomaly A-11 narrows at the bridge boundary
#: [common/purchMT.cbl] exactly as it does for the Sales twin
#: [common/salesMT.cbl:L305-L312].
_D_PURCH_AVERAGE: Final[FieldDescriptor] = _desc(WsPurchRecord, "Purch-Average")
_D_PURCH_LAST_INV: Final[FieldDescriptor] = _desc(WsPurchRecord, "Purch-Last-inv")
_D_PURCH_LAST_PAY: Final[FieldDescriptor] = _desc(WsPurchRecord, "Purch-Last-pay")
_D_PURCH_CURRENT: Final[FieldDescriptor] = _desc(WsPurchRecord, "Purch-Current")
_D_PURCH_UNAPPLIED: Final[FieldDescriptor] = _desc(WsPurchRecord, "Purch-Unapplied")
#: ``05 PTurnover-q pic s9(8)v99 comp-3 occurs 4`` [copybooks/wspl.cob:L51], the OCCURS
#: view that ``03 filler redefines Quarters`` [copybooks/wspl.cob:L50] exposes.
_D_PTURNOVER_Q: Final[FieldDescriptor] = _desc(QuartersView, "PTurnover-q")
#: ``03 Quarters`` and its four named items [copybooks/wspl.cob:L45-L49]. Both views name
#: the same storage and ``records/purchase_ledger.py`` designates neither as primary, so
#: a store through one is mirrored into the other.
_D_TURNOVER_Q: Final[tuple[FieldDescriptor, ...]] = tuple(
    _desc(Quarters, f"Turnover-q{occurrence}") for occurrence in (1, 2, 3, 4)
)
#: The attribute names of ``Quarters``' four items, in occurrence order.
_QUARTER_ATTRS: Final[tuple[str, ...]] = (
    "turnover_q1",
    "turnover_q2",
    "turnover_q3",
    "turnover_q4",
)

# ``01 OI-Header`` [copybooks/plwsoi.cob:L12-L62]
_D_OI_TYPE: Final[FieldDescriptor] = _desc(OiHeader, "OI-Type")
_D_OI_DATE: Final[FieldDescriptor] = _desc(OiHeader, "OI-Date")
_D_OI_STATUS: Final[FieldDescriptor] = _desc(OiHeader, "OI-Status")
_D_OI_CR: Final[FieldDescriptor] = _desc(OiHeader, "OI-CR")
#: DECLARED AND DELIBERATELY UNREFERENCED.  ``oi-invoice`` reaches only print items in
#: this program - ``move oi-invoice to l5-nos`` [L444] and its companion at [L529] - and
#: report formatting is out of scope (section 0.2.2); the ``display l5-nos`` at [L530] is
#: not converted either, because an invoice number is a record key and the safe-event
#: schema in ``acas_posting/dal/status.py`` excludes it from a log record (CWE-532).  The
#: descriptor stays so the field keeps its dictionary citation, per rule R-5.
_D_OI_INVOICE: Final[FieldDescriptor] = _desc(OiKey, "OI-Invoice")
_D_OI_NET: Final[FieldDescriptor] = _desc(Filler1, "OI-Net")
_D_OI_CARRIAGE: Final[FieldDescriptor] = _desc(Filler1, "OI-Carriage")
_D_OI_VAT: Final[FieldDescriptor] = _desc(Filler1, "OI-Vat")
_D_OI_C_VAT: Final[FieldDescriptor] = _desc(Filler1, "OI-C-Vat")
_D_OI_PAID: Final[FieldDescriptor] = _desc(Filler1, "OI-Paid")
_D_OI_P_C: Final[FieldDescriptor] = _desc(Filler1, "OI-P-C")

# ``01 maps03-ws`` [copybooks/wsmaps03.cob:L6-L30]
_D_U_BIN: Final[FieldDescriptor] = _desc(Maps03Ws, "u-bin")
#: ``03 u-date pic x(10)`` [copybooks/wsmaps03.cob] - the ten-character UK text date.
#: Read by ``[purchase/pl060.cbl:L937-L938]``, whose reference modification takes six
#: characters and then two, dropping the century digits.
_D_U_DATE: Final[FieldDescriptor] = _desc(Maps03Ws, "u-date")

# ``01 System-Record`` [copybooks/wssystem.cob]
_D_CURRENT_QUARTER: Final[FieldDescriptor] = _desc(
    type(SystemRecord().system_data_block), "Current-Quarter"
)
_D_SCYCLE: Final[FieldDescriptor] = _desc(
    type(SystemRecord().system_data_block), "Scycle"
)
#: ``05 Run-Date binary-long`` [copybooks/wssystem.cob:L67] - one of the two observables
#: ``acas_posting/clock.py`` pins. It arrives on the system record and is never read from
#: a clock here (rule R-6).
_D_RUN_DATE: Final[FieldDescriptor] = _desc(
    type(SystemRecord().system_data_block), "Run-Date"
)
#: ``05 Next-Batch binary-short`` [copybooks/wssystem.cob] - incremented at
#: ``[purchase/pl060.cbl:L887]``, so batch numbering is diff-visible.
_D_NEXT_BATCH: Final[FieldDescriptor] = _desc(
    type(SystemRecord().general_ledger_block), "Next-Batch"
)
#: ``05 Postings binary-short`` - anomaly A-17's storage. Written at
#: ``[purchase/pl060.cbl:L1028]`` and read back at ``[purchase/pl060.cbl:L905]``.
_D_POSTINGS: Final[FieldDescriptor] = _desc(
    type(SystemRecord().general_ledger_block), "Postings"
)
#: ``05 Vat-Ac`` on the General Ledger block. NOTE THE SPELLING: the posting record
#: spells the same idea ``Vat-AC``, which is anomaly A-21 in miniature.
_D_SYS_VAT_AC: Final[FieldDescriptor] = _desc(
    type(SystemRecord().general_ledger_block), "Vat-Ac"
)
_D_P_CREDITORS: Final[FieldDescriptor] = _desc(
    type(SystemRecord().purchase_ledger_block), "P-Creditors"
)
_D_BL_PURCH_AC: Final[FieldDescriptor] = _desc(
    type(SystemRecord().purchase_ledger_block), "BL-Purch-Ac"
)

# ``01 System-Record-4`` [copybooks/wssys4.cob]
#: ``05 pl-cn-unappl-this-month pic s9(8)v99 comp-3`` [copybooks/wssys4.cob:L27] - PERIOD
#: TOTAL 8, and the only ``SYSTOT-REC`` column this program writes.
_D_PL_CN_UNAPPL: Final[FieldDescriptor] = _desc(
    type(SystemRecord4().purchase_ledger_data), "pl-cn-unappl-this-month"
)

# ``01 WS-Batch-Record`` [copybooks/wsbatch.cob:L13-L54]
_D_WS_LEDGER: Final[FieldDescriptor] = _desc(WsBatchKey, "WS-Ledger")
_D_WS_BATCH_NOS: Final[FieldDescriptor] = _desc(WsBatchKey, "WS-Batch-Nos")
_D_ITEMS: Final[FieldDescriptor] = _desc(GlBatchRecord, "Items")
_D_BATCH_STATUS: Final[FieldDescriptor] = _desc(GlBatchRecord, "Batch-Status")
_D_CLEARED_STATUS: Final[FieldDescriptor] = _desc(GlBatchRecord, "Cleared-Status")
_D_BCYCLE: Final[FieldDescriptor] = _desc(GlBatchRecord, "Bcycle")
_D_ENTERED: Final[FieldDescriptor] = _desc(BatchDates, "Entered")
#: ``03 Amounts comp-3`` with four ``pic 9(9)v99`` items [copybooks/wsbatch.cob:L40-L44].
#: UNSIGNED at all four, which the descriptors carry.
_D_INPUT_GROSS: Final[FieldDescriptor] = _desc(BatchAmounts, "Input-Gross")
_D_INPUT_VAT: Final[FieldDescriptor] = _desc(BatchAmounts, "Input-Vat")
_D_ACTUAL_GROSS: Final[FieldDescriptor] = _desc(BatchAmounts, "Actual-Gross")
_D_ACTUAL_VAT: Final[FieldDescriptor] = _desc(BatchAmounts, "Actual-Vat")
_D_DESCRIPTION: Final[FieldDescriptor] = _desc(GlBatchRecord, "Description")
_D_BDEFAULT: Final[FieldDescriptor] = _desc(PostingData, "bDefault")
_D_CONVENTION: Final[FieldDescriptor] = _desc(PostingData, "Convention")
_D_BATCH_DEF_AC: Final[FieldDescriptor] = _desc(PostingData, "Batch-Def-AC")
_D_BATCH_DEF_PC: Final[FieldDescriptor] = _desc(PostingData, "Batch-Def-PC")
_D_BATCH_DEF_CODE: Final[FieldDescriptor] = _desc(PostingData, "Batch-Def-Code")
_D_BATCH_DEF_VAT: Final[FieldDescriptor] = _desc(PostingData, "Batch-Def-Vat")
_D_BATCH_START: Final[FieldDescriptor] = _desc(GlBatchRecord, "Batch-Start")

# ``01 WS-Posting-Record`` [copybooks/wspost.cob:L11-L26]
_D_WS_POST_RRN: Final[FieldDescriptor] = _desc(WsPostingRecord, "WS-Post-RRN")
_D_POST_BATCH: Final[FieldDescriptor] = _desc(WsPostKey, "Batch")
_D_POST_NUMBER: Final[FieldDescriptor] = _desc(WsPostKey, "Post-Number")
_D_POST_CODE: Final[FieldDescriptor] = _desc(WsPostingRecord, "Post-Code")
_D_POST_DATE: Final[FieldDescriptor] = _desc(WsPostingRecord, "Post-Date")
_D_POST_DR: Final[FieldDescriptor] = _desc(WsPostingRecord, "Post-DR")
_D_DR_PC: Final[FieldDescriptor] = _desc(WsPostingRecord, "DR-PC")
_D_POST_CR: Final[FieldDescriptor] = _desc(WsPostingRecord, "Post-CR")
_D_CR_PC: Final[FieldDescriptor] = _desc(WsPostingRecord, "CR-PC")
_D_POST_AMOUNT: Final[FieldDescriptor] = _desc(WsPostingRecord, "Post-Amount")
_D_POST_LEGEND: Final[FieldDescriptor] = _desc(WsPostingRecord, "Post-Legend")
#: ``Vat-AC`` - the posting record's spelling. See ``_D_SYS_VAT_AC`` and anomaly A-21.
_D_POST_VAT_AC: Final[FieldDescriptor] = _desc(WsPostingRecord, "Vat-AC")
_D_VAT_PC: Final[FieldDescriptor] = _desc(WsPostingRecord, "Vat-PC")
_D_POST_VAT_SIDE: Final[FieldDescriptor] = _desc(WsPostingRecord, "Post-Vat-Side")
_D_VAT_AMOUNT: Final[FieldDescriptor] = _desc(WsPostingRecord, "Vat-Amount")

# ``01 WS-IRS-Posting-Record`` [copybooks/wspost-irs.cob:L13-L25]
_D_IRS_BATCH: Final[FieldDescriptor] = _desc(WsIrsPostKey, "WS-IRS-Batch")
_D_IRS_POST_NUMBER: Final[FieldDescriptor] = _desc(WsIrsPostKey, "WS-IRS-Post-Number")
_D_IRS_POST_CODE: Final[FieldDescriptor] = _desc(WsIrsPostingRecord, "WS-IRS-Post-Code")
_D_IRS_POST_DATE: Final[FieldDescriptor] = _desc(WsIrsPostingRecord, "WS-IRS-Post-Date")
#: ``03 WS-IRS-Post-DR pic 9(5)`` [copybooks/wspost-irs.cob:L19] - FIVE digits, where
#: ``Post-DR`` in ``copybooks/wspost.cob`` is ``9(6)``. FINDING: the fan-out therefore
#: truncates a six-digit account silently. Recorded, not corrected.
_D_IRS_POST_DR: Final[FieldDescriptor] = _desc(WsIrsPostingRecord, "WS-IRS-Post-DR")
_D_IRS_POST_CR: Final[FieldDescriptor] = _desc(WsIrsPostingRecord, "WS-IRS-Post-CR")
#: ``03 WS-IRS-Post-Amount pic s9(7)v99 sign leading``
#: [copybooks/wspost-irs.cob:L21] - one of the two SIGN LEADING DISPLAY fields whose
#: storage class Agent Action Plan section 0.6.1 counts among the six that must be
#: modelled. The descriptor carries the sign position; nothing is encoded here.
_D_IRS_POST_AMOUNT: Final[FieldDescriptor] = _desc(
    WsIrsPostingRecord, "WS-IRS-Post-Amount"
)
_D_IRS_POST_LEGEND: Final[FieldDescriptor] = _desc(
    WsIrsPostingRecord, "WS-IRS-Post-Legend"
)
#: ``03 WS-IRS-Vat-AC-Def pic 99`` [copybooks/wspost-irs.cob:L23] - TWO digits, which is
#: why ``move 31`` fits it at ``[purchase/pl060.cbl:L993]`` and a six-digit account code
#: could not.
_D_IRS_VAT_AC_DEF: Final[FieldDescriptor] = _desc(
    WsIrsPostingRecord, "WS-IRS-Vat-AC-Def"
)
_D_IRS_POST_VAT_SIDE: Final[FieldDescriptor] = _desc(
    WsIrsPostingRecord, "WS-IRS-Post-Vat-Side"
)
_D_IRS_VAT_AMOUNT: Final[FieldDescriptor] = _desc(
    WsIrsPostingRecord, "WS-IRS-Vat-Amount"
)

#: ``03 Rrn pic 9(5) comp`` of ``01 File-Access`` [copybooks/wsfnctn.cob:L24]. NOT a
#: field of the posting record: anomaly A-17's cycle runs through this one field.
_D_RRN: Final[FieldDescriptor] = _desc(FileAccess, "Rrn")


def _attr_descriptor(owner: Any, attribute: str) -> FieldDescriptor:
    """The descriptor a record dataclass attaches to one PYTHON attribute.

    :func:`_desc` looks a descriptor up by its COBOL name, which is the right key
    almost everywhere. It cannot separate the two items ``copybooks/wspl.cob``
    both spells ``filler`` - the ``redefines`` of ``Quarters``
    [copybooks/wspl.cob:L50] and the trailing ``x(12)``
    [copybooks/wspl.cob:L54] - so the trailing one is taken by its attribute
    name, which is unique. Raising keeps rule R-5's chain unbroken.
    """
    cls = owner if isinstance(owner, type) else type(owner)
    member = getattr(cls, "__dataclass_fields__", {}).get(attribute)
    descriptor = None if member is None else member.metadata.get("descriptor")
    if descriptor is None:
        raise LookupError(
            f"{cls.__name__} attaches no descriptor to attribute {attribute!r}"
        )
    return descriptor


#: ⭐⭐ ``01 ws-data``'s tail [purchase/pl060.cbl:L208-L220] as the BYTES the
#: compiled program addresses, which is what the two subscripted accumulates at
#: [purchase/pl060.cbl:L467-L468] need - their subscript is unbounded, and an
#: unbounded subscript lands on bytes rather than on a list element.
#:
#: THE WINDOW STARTS AT ``a`` AND ENDS AT ``File-28-status``, because
#: ``total-group`` sits near the END of this ``01`` rather than in the middle of
#: it as ``sl060``'s does. That asymmetry is the whole of finding F7: occurrence 4
#: does not land on a comfortable neighbour here, it runs off the end of the
#: group.
#:
#: THE LENGTH IS VERIFIED AGAINST THE COMPILED ORACLE, not asserted: GnuCOBOL
#: 3.2.0 reported ``function length`` = 50 for exactly this window, pinning
#: ``binary-char`` at ONE byte and ``pic s9(7)v99 comp-3`` at FIVE.
_WS_DATA_TOTALS_GROUP: Final[mv.StorageGroup] = mv.StorageGroup(
    (
        mv.GroupItem("a", _D_A),
        mv.GroupItem("b", _D_B),
        mv.GroupItem("c", _D_C),
        mv.GroupItem("work-net", _D_WORK_NET),
        mv.GroupItem("work-vat", _D_WORK_VAT),
        mv.GroupItem("work-goods", _D_WORK_GOODS),
        mv.GroupItem("total-net (1)", _D_TOTAL_NET),
        mv.GroupItem("total-vat (1)", _D_TOTAL_VAT),
        mv.GroupItem("total-net (2)", _D_TOTAL_NET),
        mv.GroupItem("total-vat (2)", _D_TOTAL_VAT),
        mv.GroupItem("total-net (3)", _D_TOTAL_NET),
        mv.GroupItem("total-vat (3)", _D_TOTAL_VAT),
        mv.GroupItem("line-cnt", _D_LINE_CNT),
        mv.GroupItem("File-28-status", _D_FILE_28_STATUS),
    ),
    source_locator="purchase/pl060.cbl:L208-L220",
)

#: Bytes per occurrence of ``total-group``: one ``total-net`` plus one
#: ``total-vat`` [purchase/pl060.cbl:L215-L216]. Read from the descriptors rather
#: than written as a literal 10.
_TOTAL_GROUP_ELEMENT_BYTES: Final[int] = (
    _D_TOTAL_NET.byte_length + _D_TOTAL_VAT.byte_length
)


def _ws_data_totals_values(ws: _Ws) -> dict[str, object]:
    """The window's current contents, keyed the way the byte layout names them.

    ⭐⭐ FINDING F7 LIVES HERE. ``add work-vat to total-vat (a).``
    [purchase/pl060.cbl:L467] and ``add work-net to total-net (a).`` [:L468] index
    ``03 total-group occurs 3`` [:L214] with ``03 a pic 9`` [:L208], which
    ``move oi-type to a.`` [:L459] loaded straight from the open-item header.
    ``OI-Type`` is documented as ``4 = Proforma`` on the PURCHASE side
    [copybooks/plwsoi.cob:L28] - used, not reserved - and
    ``purchase/pl055.cbl:L552`` propagates it verbatim from ``ih-type``. So a
    perfectly ordinary proforma drives the subscript one past the table, and
    nothing between the load and the use tests it: the three-way
    ``if oi-type = 2 / = 3 / = 1`` [:L461-L465] only chooses a print literal and
    has no ``else``.

    Note the contrast the migration must PRESERVE rather than smooth away: the
    SALES copybook documents its type 4 as ``Proforma (Not used)``
    [copybooks/slwsoi.cob:L24]. Same subscript, same unchecked table, different
    reachability - and ``pl055``'s producer behaviour is correct as it stands.

    WHAT THE COMPILED PROGRAM DOES, measured on GnuCOBOL 3.2.0 against this exact
    declaration with a variable subscript (a literal one is refused at compile
    time, which is why the frozen ``move oi-type to a`` form is what makes this
    reachable at all):

        a = 0  ->  ``total-vat (0)`` IS ``work-goods`` and ``total-net (0)`` IS
                   ``work-vat``, both whole fields, both reproduced exactly.
        a = 4  ->  ``total-net (4)`` covers ``line-cnt``, ``File-28-status`` and
                   then three bytes PAST the ``01`` group; ``total-vat (4)`` lies
                   ENTIRELY past it. The oracle ran to completion and returned
                   normally, having left ``line-cnt`` at 115 and
                   ``File-28-status`` blank, and having changed the process's own
                   exit status - it did NOT abort.

    ⛔ NO ``IndexError``, no clamp, no modulo, no skip and no bare Python
    ``[a - 1]``: a negative index would silently accumulate into the THIRD
    occurrence, which corresponds to nothing the compiled program does. Raising
    would replace a reproduced anomaly with an invented one (rules R-3, R-4).
    """
    return {
        "a": ws.a,
        "b": ws.b,
        "c": ws.c,
        "work-net": ws.work_net,
        "work-vat": ws.work_vat,
        "work-goods": ws.work_goods,
        "total-net (1)": ws.total_net[0],
        "total-vat (1)": ws.total_vat[0],
        "total-net (2)": ws.total_net[1],
        "total-vat (2)": ws.total_vat[1],
        "total-net (3)": ws.total_net[2],
        "total-vat (3)": ws.total_vat[2],
        "line-cnt": ws.line_cnt,
        "File-28-status": ws.file_28_status,
    }


def _restore_ws_data_totals(ws: _Ws, after: Mapping[str, object]) -> None:
    """Write the window's decoded bytes back onto the program's storage.

    EVERY item is written back, not only the two the statement names, because an
    out-of-range subscript changes fields the statement does NOT name - that is
    the whole of the anomaly. Assigning only the totals would silently discard
    the reproduced effect on ``line-cnt`` and ``File-28-status``.
    """
    ws.a = cast(int, after["a"])
    ws.b = cast(int, after["b"])
    ws.c = cast(int, after["c"])
    ws.work_net = cast(Decimal, after["work-net"])
    ws.work_vat = cast(Decimal, after["work-vat"])
    ws.work_goods = cast(Decimal, after["work-goods"])
    ws.total_net = [
        cast(Decimal, after["total-net (1)"]),
        cast(Decimal, after["total-net (2)"]),
        cast(Decimal, after["total-net (3)"]),
    ]
    ws.total_vat = [
        cast(Decimal, after["total-vat (1)"]),
        cast(Decimal, after["total-vat (2)"]),
        cast(Decimal, after["total-vat (3)"]),
    ]
    ws.line_cnt = cast(int, after["line-cnt"])
    ws.file_28_status = cast(int, after["File-28-status"])


def _add_to_total_group(ws: _Ws, member: str, addend: Decimal) -> None:
    """``add <addend> to <member> (a).`` - one unchecked subscripted accumulate.

    Args:
        ws: The program's storage. ``ws.a`` is the subscript, unvalidated.
        member: ``"total-net"`` or ``"total-vat"`` - the member of the occurrence
            the statement names.
        addend: The sending field's value, read before the store as COBOL reads
            it.
    """
    values = _ws_data_totals_values(ws)
    statement = (
        "purchase/pl060.cbl:L467"
        if member == "total-vat"
        else "purchase/pl060.cbl:L468"
    )
    receiving = _D_TOTAL_VAT if member == "total-vat" else _D_TOTAL_NET
    #  The receiver is READ through the same addressing as the store, so an
    #  out-of-range occurrence contributes its ALIASED value to the sum.
    receiver_value = mv.subscripted_value(
        _WS_DATA_TOTALS_GROUP,
        values,
        member=f"{member} (1)",
        element_length=_TOTAL_GROUP_ELEMENT_BYTES,
        subscript=ws.a,
        statement=statement,
    )
    total = ar.add_to(
        addend, receiver_value=cast(Decimal, receiver_value), receiving=receiving
    )
    _restore_ws_data_totals(
        ws,
        mv.subscripted_store(
            _WS_DATA_TOTALS_GROUP,
            values,
            member=f"{member} (1)",
            element_length=_TOTAL_GROUP_ELEMENT_BYTES,
            subscript=ws.a,
            value=total,
            statement=statement,
        ),
    )


#: ``03 filler pic x(12).`` [copybooks/wspl.cob:L54] - the trailing item of
#: ``01 WS-Purch-Record``, taken by attribute because it shares its COBOL name
#: with the ``redefines`` of ``Quarters``.
_D_PURCH_TRAILING_FILLER: Final[FieldDescriptor] = _attr_descriptor(
    WsPurchRecord, "filler_l54"
)

#: ⭐⭐ The ``Quarters`` neighbourhood of ``01 WS-Purch-Record``
#: [copybooks/wspl.cob:L43-L54] as the BYTES the compiled program addresses. It
#: exists for the three subscripted accumulates at [purchase/pl060.cbl:L484,
#: :L490, :L497], whose subscript is ``05 Current-Quarter pic 9``
#: [copybooks/wssystem.cob:L110] and is never tested.
#:
#: BOTH IMMEDIATE NEIGHBOURS ARE PERSISTED COLUMNS, which is why this cannot be
#: approximated: quarter 0 addresses ``Purch-Last`` and quarter 5
#: ``Purch-Unapplied``. Quarter 6 reaches ``Purch-Stats-Date``, a column as well.
#:
#: THE LENGTH IS VERIFIED AGAINST THE COMPILED ORACLE: GnuCOBOL 3.2.0 reported
#: ``function length`` = 58 for exactly this window - SIX more than the sales
#: record's 52, because the purchase record carries no partial-ship flag and its
#: trailing filler is ``x(12)`` rather than ``x(5)``.
_PURCH_QUARTERS_GROUP: Final[mv.StorageGroup] = mv.StorageGroup(
    (
        mv.GroupItem("Purch-Current", _desc(WsPurchRecord, "Purch-Current")),
        mv.GroupItem("Purch-Last", _desc(WsPurchRecord, "Purch-Last")),
        mv.GroupItem("PTurnover-q (1)", _D_PTURNOVER_Q),
        mv.GroupItem("PTurnover-q (2)", _D_PTURNOVER_Q),
        mv.GroupItem("PTurnover-q (3)", _D_PTURNOVER_Q),
        mv.GroupItem("PTurnover-q (4)", _D_PTURNOVER_Q),
        mv.GroupItem("Purch-Unapplied", _desc(WsPurchRecord, "Purch-Unapplied")),
        mv.GroupItem("Purch-Stats-Date", _desc(WsPurchRecord, "Purch-Stats-Date")),
        mv.GroupItem("filler-54", _D_PURCH_TRAILING_FILLER),
    ),
    source_locator="copybooks/wspl.cob:L43-L54",
)

#: Bytes per occurrence of ``PTurnover-q`` [copybooks/wspl.cob:L51]. Read from
#: the descriptor rather than written as a literal 6.
_PTURNOVER_Q_ELEMENT_BYTES: Final[int] = _D_PTURNOVER_Q.byte_length


def _purch_quarters_values(ws: _Ws) -> dict[str, object]:
    """The quarters window's current contents, keyed as the byte layout names it.

    ``03 Quarters`` names the four occurrences individually
    [copybooks/wspl.cob:L45-L49] and ``03 filler redefines Quarters`` exposes the
    same bytes as ``PTurnover-q`` [copybooks/wspl.cob:L50-L51]. They are ONE
    four-item area, so the subscripted view is read here and both views are
    written back together.
    """
    quarters = ws.purch.quarters_view.pturnover_q
    return {
        "Purch-Current": ws.purch.purch_current,
        "Purch-Last": ws.purch.purch_last,
        "PTurnover-q (1)": quarters[0],
        "PTurnover-q (2)": quarters[1],
        "PTurnover-q (3)": quarters[2],
        "PTurnover-q (4)": quarters[3],
        "Purch-Unapplied": ws.purch.purch_unapplied,
        "Purch-Stats-Date": ws.purch.purch_stats_date,
        "filler-54": ws.purch.filler_l54,
    }


def _add_to_pturnover_q(ws: _Ws, quarter: int, value: Decimal) -> None:
    """``add work-goods to pturnover-q (current-quarter)`` - one subscripted accumulate.

    Three sites, one per transaction type: ``[purchase/pl060.cbl:L484]`` (Receipts),
    ``[purchase/pl060.cbl:L490]`` (Accounts) and ``[purchase/pl060.cbl:L497]``
    (Cr. Notes).

    ANOMALY A-NEW-4 [purchase/pl060.cbl:L484], [purchase/pl060.cbl:L490],
    [purchase/pl060.cbl:L497] - ``current-quarter`` is used as a subscript into a table
    of ``occurs 4`` with NO bounds check whatsoever, exactly as the quarter subscript at
    [general/gl080.cbl:L345] is used unchecked (anomaly A-2). Nothing in this program
    constrains ``05 Current-Quarter pic 9`` to 1..4.
    Reproduced deliberately per R-4; DO NOT FIX.

    ⭐ WHAT THE COMPILED PROGRAM DOES - MEASURED, NOT INFERRED (rule R-6). The
    window above was transcribed verbatim into GnuCOBOL 3.2.0 and driven with a
    variable subscript. Seeded ``Purch-Last`` 200.02, quarters 1.01/2.02/3.03/4.04,
    ``Purch-Unapplied`` 500.05, ``Purch-Stats-Date`` 2024, adding 77.77:

        q = 1  ->  Turnover-q1 78.78          q = 4  ->  Turnover-q4 81.81
        q = 0  ->  Purch-Last  277.79   A PERSISTED COLUMN
        q = 5  ->  Purch-Unapplied 577.82   A PERSISTED COLUMN
        q = 6  ->  Purch-Stats-Date, ANOTHER COLUMN, plus the first two bytes of
                   the trailing filler - reproduced byte for byte, the six-byte
                   window ``32 30 32 34 20 20`` being one of the readings that
                   pinned the runtime's receiver read.

    Every reading returned normally with no diagnostic and no status change: the
    out-of-range quarters are all INSIDE ``01 WS-Purch-Record``, so unlike the
    ``total-group`` site there is no off-the-end case here at all.

    ⛔ The previous note recorded subscript 0 as addressing the LAST occurrence
    and subscript 5 as raising. Both were wrong, and both are now measured:
    subscript 0 addresses the field immediately BEFORE the table and subscript 5
    the one immediately after it. A Python ``[quarter - 1]`` produces the first of
    those errors silently, which is why the addressing is done in bytes.

    Both views of the storage are kept in step, and so is every neighbour the
    window can reach.
    """
    values = _purch_quarters_values(ws)
    statement = "purchase/pl060.cbl:L484"
    after = mv.subscripted_store(
        _PURCH_QUARTERS_GROUP,
        values,
        member="PTurnover-q (1)",
        element_length=_PTURNOVER_Q_ELEMENT_BYTES,
        subscript=quarter,
        value=ar.add_to(
            value,
            receiver_value=cast(
                Decimal,
                mv.subscripted_value(
                    _PURCH_QUARTERS_GROUP,
                    values,
                    member="PTurnover-q (1)",
                    element_length=_PTURNOVER_Q_ELEMENT_BYTES,
                    subscript=quarter,
                    statement=statement,
                ),
            ),
            receiving=_D_PTURNOVER_Q,
        ),
        statement=statement,
    )

    ws.purch.purch_current = cast(Decimal, after["Purch-Current"])
    ws.purch.purch_last = cast(Decimal, after["Purch-Last"])
    ws.purch.purch_unapplied = cast(Decimal, after["Purch-Unapplied"])
    ws.purch.purch_stats_date = cast(int, after["Purch-Stats-Date"])
    ws.purch.filler_l54 = cast(str, after["filler-54"])
    occurrences = tuple(
        cast(Decimal, after[f"PTurnover-q ({index})"]) for index in (1, 2, 3, 4)
    )
    ws.purch.quarters_view.pturnover_q = occurrences
    for attribute, occurrence in zip(_QUARTER_ATTRS, occurrences):
        setattr(ws.purch.quarters, attribute, occurrence)


def _init01__loop(ws: _Ws) -> None:
    """``loop.`` [purchase/pl060.cbl:L424-L543] - the OTM4 walk and the ledger update.

    One iteration per OTM4 header: read, find the supplier, accumulate the printed
    totals, write the General Ledger batch line, update the purchase ledger, then write
    the open-item record. The loop-back at ``[purchase/pl060.cbl:L543]`` is unconditional
    and the only way out is the at-end at ``[purchase/pl060.cbl:L425-L426]``.
    """
    while True:
        record = ws.otm4.read_next(ws.file_access)  # [L425] read open-item-file-4 at end
        _otm4_status(ws)
        if record is None:
            # GO TO class 2 - [L426] `go to main-end`. The post-loop work is placed in
            # ``_init01`` immediately after this call, in source order.
            break

        _group_move_oi(record, ws.oi_header)  # [L428] GROUP MOVE into oi-header

        # [L430] move oi-supplier to WS-Purch-key l5-cust.
        # Two receivers; ``l5-cust`` is an item of ``01 line-5`` and is OMITTED with the
        # rest of the print file. ``OI-Supplier`` is a GROUP of ``OI-Nos pic x(6)`` and
        # ``OI-Check pic 9`` [copybooks/plwsoi.cob:L15-L17], and ``WS-Purch-Key`` is an
        # elementary ``pic x(7)`` [copybooks/wspl.cob:L14], so the seven bytes move whole.
        ws.purch.ws_purch_key = mv.move_group(
            _oi_supplier_image(ws.oi_header),
            _D_WS_PURCH_KEY,
            sending_field=_D_OI_SUPPLIER_GROUP,
        )

        ws.ws_reply = mv.move_figurative(mv.SPACE, _D_WS_REPLY)  # [L431]
        _fh("purch_read_indexed", _ctx(ws, ws.purch))  # [L432] read purchase-file

        # [L433-L434] if FS-Reply not = zero move "X" to ws-reply.
        if ws.file_access.fs_reply != FsReply.SUCCESS:
            ws.ws_reply = mv.move("X", _D_WS_REPLY)

        if ws.ws_reply == "X":  # [L436]
            # A MISSING SUPPLIER IS CREATED, not rejected. Two table effects flow from
            # this one branch: the record is initialised and written here and at
            # [L515-L517], and ``purchase-missing`` latches for the [L630] report.
            ws.ws_error = mv.move(  # [L437] move 1 to ws-error -> 88 purchase-missing
                _WS_ERROR_PURCHASE_MISSING, _D_WS_ERROR
            )
            # [L438] initialize WS-Purch-Record with filler. ``WITH FILLER`` IS present
            # here where the ``pl055`` twin omits it [purchase/pl055.cbl:L547].
            _initialize_with_filler(ws.purch)
            # [L439] move "Supplier Unknown" to l5-name purch-name.
            # ``l5-name`` is a print item and is omitted; ``purch-name`` is a
            # ``PULEDGER-REC`` column and is written.
            ws.purch.purch_name = mv.move("Supplier Unknown", _D_PURCH_NAME)
            # [L440] move oi-supplier to WS-Purch-key. Re-stated because [L438] has just
            # cleared the key; the repetition is the frozen source's, not a mistake here.
            ws.purch.ws_purch_key = mv.move_group(
                _oi_supplier_image(ws.oi_header),
                _D_WS_PURCH_KEY,
                sending_field=_D_OI_SUPPLIER_GROUP,
            )
        else:
            # [L442] move purch-name to l5-name. OMITTED - print item only, AND NOT
            # LOGGED: report formatting is out of scope (Agent Action Plan section
            # 0.2.2), the frozen source does not ``display`` it, and ``purch-name`` is a
            # SUPPLIER NAME, which the safe-event schema in
            # ``acas_posting/dal/status.py`` excludes from a record at any level
            # (CWE-532).  The ELSE arm survives because the branch is real control flow:
            # the THEN arm above rebuilds the key after a failed read.
            pass

        # [L444] move oi-invoice to l5-nos. OMITTED - print item only.

        # [L446] move oi-date to u-bin. The binary day number crosses into the ``maps04``
        # linkage record, which is what makes ``zz060`` the unpack direction.
        ws.maps03_ws.u_bin = mv.move(
            ws.oi_header.oi_date, _D_U_BIN, sending_field=_D_OI_DATE
        )
        _zz060_convert_date(ws)  # [L447] perform zz060-Convert-Date.
        # [L448] move ws-date to l5-date. OMITTED - print item only.

        # [L450] move oi-type to a.
        # ANOMALY A-NEW-3 [purchase/pl060.cbl:L450], [purchase/pl060.cbl:L467-L468] -
        # ``a`` is taken straight from ``oi-type`` and used as the subscript of
        # ``total-group occurs 3`` [purchase/pl060.cbl:L214] with no range test. The type
        # codes the copybook documents run to 9 [copybooks/plwsoi.cob:L25-L34], so a
        # Proforma (4), a Payment (5), a Journal (6, 7) or an Old Payment (9) indexes
        # outside the table, and so does a zero.
        # Reproduced deliberately per R-4; DO NOT FIX.
        ws.a = mv.move(ws.oi_header.oi_type, _D_A, sending_field=_D_OI_TYPE)

        # [L452-L459] the nested type-literal moves. Presentation only - ``l5-type`` is a
        # print item - but the nesting is reproduced because its shape is the program's.
        # Note there is no ELSE arm for a type outside {1,2,3}: ``l5-type`` then keeps
        # whatever the previous iteration left in it.
        # NONE OF THE THREE IS LOGGED.  Each arm is ``move <literal> to l5-type``
        # [L453, L456, L459] - a store into ``01 line-5``, report content that section
        # 0.2.2 puts out of scope; the frozen program ``display``s none of it, and
        # section 0.3.4 converts a DISPLAY, not a report field.  ALL THREE ARMS AND THE
        # ABSENT ELSE SURVIVE, because that shape is the finding recorded just above:
        # a type outside {1,2,3} leaves the previous iteration's caption in place.
        if ws.oi_header.oi_type == 2:
            pass  # [L453]
        elif ws.oi_header.oi_type == 3:
            pass  # [L456]
        elif ws.oi_header.oi_type == 1:
            pass  # [L459]

        # [L461] add oi-vat oi-c-vat giving work-vat.  TWO addends, ONE quantize.
        ws.work_vat = ar.add_giving(
            ws.oi_header.filler_1.oi_vat,
            ws.oi_header.filler_1.oi_c_vat,
            receiving=_D_WORK_VAT,
        )
        # [L462] move oi-net to work-goods.
        # THE pl055 -> pl060 SIGN CONTRACT. For a credit note ``pl055`` has already
        # negated ``oi-net``, ``oi-carriage``, ``oi-vat`` and ``oi-c-vat``
        # [purchase/pl055.cbl:L572-L575], so ``work-goods`` carries a NEGATIVE here for
        # type 3 - which is exactly what makes anomalies A-8 and A-9 behave as they do in
        # ``credit-comp``. See the matching comment at [L498] below.
        ws.work_goods = mv.move(
            ws.oi_header.filler_1.oi_net, _D_WORK_GOODS, sending_field=_D_OI_NET
        )
        # [L463] move work-vat to l5-vat. OMITTED - print item only.
        # [L464] add oi-net oi-carriage giving work-net.
        ws.work_net = ar.add_giving(
            ws.oi_header.filler_1.oi_net,
            ws.oi_header.filler_1.oi_carriage,
            receiving=_D_WORK_NET,
        )
        # [L465] move work-net to l5-net. OMITTED - print item only.

        # [L467-L468] the two subscripted accumulates, in the source's own order.
        # THE ORDER IS LOAD-BEARING when ``a`` is out of range: at ``a = 0`` the
        # first statement's receiver IS ``work-goods`` and the second's IS
        # ``work-vat``, so the second reads a ``work-vat`` the first has already
        # changed. Each statement therefore takes its own trip through
        # ``_add_to_total_group``; nothing is hoisted, batched or reordered.
        # See A-NEW-3 and finding F7 - ``a`` comes from ``oi-type``, which is 4
        # for a purchase proforma [copybooks/plwsoi.cob:L28].
        _add_to_total_group(ws, "total-vat", ws.work_vat)
        _add_to_total_group(ws, "total-net", ws.work_net)

        # [L470-L471] work-1 = work-net + work-vat, in two statements and two stores.
        ws.work_1 = mv.move(ws.work_net, _D_WORK_1, sending_field=_D_WORK_NET)
        ws.work_1 = ar.add_to(
            ws.work_vat, receiver_value=ws.work_1, receiving=_D_WORK_1
        )
        # [L472] move work-1 to l5-gross. OMITTED - print item only.

        if _IS_G_L(ws.system_record.system_data_block.level.level_1):  # [L474]
            _bl_write(ws)  # [L475]

        # [L477] subtract purch-unapplied from purch-current giving l5-old-bal.
        # PRINT-ONLY: the receiver is an item of ``01 line-5``.  THE STATEMENT IS STILL
        # PERFORMED - unconditionally, exactly as the frozen program performs it - so the
        # arithmetic census stays complete and the receiving field's width is honoured.
        # ITS RESULT IS NOT BOUND AND NOT LOGGED, for three reasons that each suffice:
        # the receiver is report content, out of scope per section 0.2.2; the value is a
        # MONETARY BALANCE, which the safe-event schema in ``acas_posting/dal/status.py``
        # excludes from a record at any level (CWE-532); and as a log ARGUMENT it was
        # evaluated before the logging module decided whether the record was wanted, so a
        # value the receiving picture could not hold would have raised from inside a
        # disabled diagnostic.  Performing it as a plain statement removes that failure
        # path outright, which no ``isEnabledFor`` guard could do, while keeping the
        # frozen program's own unconditional evaluation.
        ar.subtract_giving(
            ws.purch.purch_unapplied,
            minuend=ws.purch.purch_current,
            receiving=_D_PRINT_MONEY,
        )

        # [L478] if oi-type = 1 or 2 - AN ABBREVIATED RELATION, i.e.
        # ``oi-type = 1 OR oi-type = 2``. So ``purch-comp`` runs for Receipts and
        # Accounts and NEVER for credit notes, which take ``credit-comp`` at [L501].
        if ws.oi_header.oi_type == 1 or ws.oi_header.oi_type == 2:
            _purch_comp(ws)  # [L479]

        if ws.oi_header.oi_type == 1:  # [L483] Receipts
            _add_to_pturnover_q(  # [L484]
                ws, ws.system_record.system_data_block.current_quarter, ws.work_goods
            )
            # [L485] move oi-date to purch-last-inv purch-last-pay. TWO receivers.
            (
                ws.purch.purch_last_inv,
                ws.purch.purch_last_pay,
            ) = mv.move_to_all(
                ws.oi_header.oi_date,
                (_D_PURCH_LAST_INV, _D_PURCH_LAST_PAY),
                sending_field=_D_OI_DATE,
            )

        if ws.oi_header.oi_type == 2:  # [L489] Accounts
            _add_to_pturnover_q(  # [L490]
                ws, ws.system_record.system_data_block.current_quarter, ws.work_goods
            )
            # [L491] add work-vat work-net to purch-current. TWO SOURCES, one receiver.
            ws.purch.purch_current = ar.add_to(
                ws.work_vat,
                ws.work_net,
                receiver_value=ws.purch.purch_current,
                receiving=_D_PURCH_CURRENT,
            )
            ws.purch.purch_last_inv = mv.move(  # [L492]
                ws.oi_header.oi_date, _D_PURCH_LAST_INV, sending_field=_D_OI_DATE
            )

        if ws.oi_header.oi_type == 3:  # [L496] CR. Notes
            _add_to_pturnover_q(  # [L497]
                ws, ws.system_record.system_data_block.current_quarter, ws.work_goods
            )
            # [L498] add work-vat work-net to purch-current.
            # IT ADDS, IT DOES NOT SUBTRACT, and that is correct only because of the
            # pl055 -> pl060 sign contract: ``pl055`` negated ``oi-net``, ``oi-carriage``,
            # ``oi-vat`` and ``oi-c-vat`` for ``ih-type = 3``
            # [purchase/pl055.cbl:L572-L575], so both sources are already negative here.
            # Break either half of the contract and every credit note posts with the
            # wrong sign.
            ws.purch.purch_current = ar.add_to(
                ws.work_vat,
                ws.work_net,
                receiver_value=ws.purch.purch_current,
                receiving=_D_PURCH_CURRENT,
            )
            ws.purch.purch_last_pay = mv.move(  # [L499]
                ws.oi_header.oi_date, _D_PURCH_LAST_PAY, sending_field=_D_OI_DATE
            )
            _cr_notes(ws)  # [L500]
            _credit_comp(ws)  # [L501]

        # [L503-L504] if supplier-dead move 1 to purch-status.
        # ``88 Supplier-dead value 0`` and ``88 Supplier-live value 1``
        # [copybooks/wspl.cob:L19-L20], so a freshly initialised record IS "dead" and
        # this promotes it to live.
        # FINDING - for a missing supplier this fires as well, because [L438] has just
        # zeroed the status; [L516] then stores 1 into the same field a second time. The
        # redundancy is the frozen source's and is left in place.
        if _IS_SUPPLIER_DEAD(ws.purch.purch_status):
            ws.purch.purch_status = mv.move(1, _D_PURCH_STATUS)

        if ws.purch.purch_current < 0:  # [L506] if purch-current is negative
            # [L507] multiply -1 by purch-current. NO ``GIVING``, so the RECEIVER IS
            # SECOND: ``purch-current = -1 * purch-current``.
            ws.purch.purch_current = ar.multiply_by(
                -1, ws.purch.purch_current, receiving=_D_PURCH_CURRENT
            )
            ws.purch.purch_unapplied = ar.add_to(  # [L508]
                ws.purch.purch_current,
                receiver_value=ws.purch.purch_unapplied,
                receiving=_D_PURCH_UNAPPLIED,
            )
            ws.purch.purch_current = mv.move_figurative(  # [L509]
                mv.ZERO, _D_PURCH_CURRENT
            )

        # [L511-L512] the maintainer's own invariant: "At this point only current OR
        # unapplied can be non zero and current will be = or > zero".
        # [L514] subtract purch-unapplied from purch-current giving l5-new-bal.
        # PRINT-ONLY, as [L477] is: performed unconditionally for the census, its result
        # neither bound nor logged, for the three reasons set out at [L477].
        ar.subtract_giving(
            ws.purch.purch_unapplied,
            minuend=ws.purch.purch_current,
            receiving=_D_PRINT_MONEY,
        )

        if ws.ws_reply == "X":  # [L515]
            ws.purch.purch_status = mv.move(1, _D_PURCH_STATUS)  # [L516]
            _fh("purch_write", _ctx(ws, ws.purch))  # [L517] write WS-Purch-Record
        else:
            _fh("purch_rewrite", _ctx(ws, ws.purch))  # [L519] rewrite WS-Purch-Record

        _group_move_oi(ws.oi_header, ws.otm5)  # [L521] GROUP MOVE into WS-OTM5-Record
        _fh("otm5_write", _ctx(ws, ws.otm5))  # [L522] write open-item-record-5

        # [L524-L525] the maintainer's own comment: "Should not happen."
        # [L526] if FS-Reply not = zero  *> 21
        # FINDING - the maintainer's inline ``*> 21`` names the status he expected; the
        # test is against zero, not against 21. Compare [L779]'s ``*> 21 ?``, where he
        # wrote the same guess with a question mark, and [L790], which tests ``= 10``.
        # THIS REJECTION TRANSFERS NO CONTROL. The loop continues, so the disposition is
        # "diagnose and carry on" - and it leaves a PARTIAL effect, because the purchase
        # ledger was already written or rewritten at [L517] / [L519].
        if ws.file_access.fs_reply != FsReply.SUCCESS:
            _LOG.error("%s", _PL130)  # [L527]
            # [L528] display oi5-supplier.  [L529-L530] move oi5-invoice to l5-nos and
            # display it.  NEITHER IS LOGGED, and the two renderer calls that built them
            # are gone with them.  They are the SUPPLIER CODE and the INVOICE NUMBER of
            # the very row that failed - record keys, which the safe-event schema in
            # ``acas_posting/dal/status.py`` excludes from a record at any level
            # (CWE-532), DEBUG included.  Their removal also deletes a failure path that
            # logging must not add: both were ``cobol.move`` calls evaluated as log
            # ARGUMENTS, before the logging module decided whether the record was wanted,
            # so a value the receiving picture could not hold would have raised from
            # inside a diagnostic.  ``l5-nos`` is a print item besides, omitted with the
            # rest of ``01 line-5``.
            _LOG.error("fs-reply = %s", ws.file_access.fs_reply)  # [L531-L532]
            _evaluate_message(ws)  # [L533]
            # ``ws-Eval-Msg`` is ``pic x(25)`` filled ONLY by ``Evaluate-Message`` from
            # the static table ``copybooks/FileStat-Msgs.cpy`` keyed on ``fs-reply``, so
            # it is a fixed status NAME - never driver text, never a business value.
            _LOG.error("%s", ws.ws_eval_msg)  # [L534]
            # [L535] display PL002 / [L537] accept ws-reply at 2450.  BOTH DROPPED: the
            # literal is nothing but the instruction to press the key the ``accept``
            # reads, so there is no substantive half to keep, and section 0.3.4 drops a
            # prompt whose only effect is to block a terminal.  The substantive
            # diagnostics are the three records above.
            if ws.ws_calling_data.ws_caller.strip() != "xl150":  # [L536]
                # THE BRANCH THAT DECIDES WHETHER TO PAUSE IS PRESERVED - it is the
                # codebase's own unattended-mode test - and it now decides nothing
                # observable, which is exactly what dropping the pause means.
                pass

        # [L539] write print-record from line-5 after 1. OMITTED - the print file.
        ws.line_cnt = ar.add_to(1, receiver_value=ws.line_cnt, receiving=_D_LINE_CNT)
        # [L541-L542] if line-cnt > Page-Lines perform headings.
        if (
            ar.compare(ws.line_cnt, ws.system_record.system_data_block.page_lines) > 0
        ):
            _headings(ws)

        # GO TO class 1 - [L543] `go to loop`, the unconditional loop-back.
        continue



def _init01__main_end(ws: _Ws) -> None:
    """``main-end.`` [purchase/pl060.cbl:L545-L583] - the closes, the totals, phase 2's setup.

    The post-loop block for the GO TO class 2 transfer at ``[purchase/pl060.cbl:L426]``.
    Agent Action Plan section 0.6.3 is emphatic that this work must be placed faithfully
    rather than dropped, and here it carries three real effects among the print lines: the
    file closes, the ``BL-Close`` that writes and closes the General Ledger batch, and the
    reset of ``work-b`` that period total 8 later depends on.

    Section-qualified because ``main-end.`` is declared twice in this program - here and
    in ``cr-notes`` at ``[purchase/pl060.cbl:L823]``.
    """
    ws.otm4.close(ws.file_access)  # [L548] close open-item-file-4.
    _otm4_status(ws)
    _fh("purch_close", _ctx(ws, ws.purch))  # [L549]
    _fh("otm5_close", _ctx(ws, ws.otm5))  # [L550]

    # [L551-L571] THREE TOTAL BLOCKS, one per ``total-group`` occurrence, each moving the
    # pair into ``01 line-6`` and adding them for the gross.  Every receiver is a print
    # item, so the three ``add ... giving`` statements ARE STILL PERFORMED -
    # unconditionally, as the frozen program performs them - and NOTHING IS LOGGED.
    #
    # Three independent reasons, each sufficient: the receivers are report content, which
    # section 0.2.2 puts out of scope and 0.3.4 does not convert; the operands are the
    # run's MONETARY TOTALS, which the safe-event schema in
    # ``acas_posting/dal/status.py`` excludes from a record at any level (CWE-532); and as
    # log ARGUMENTS the three ``add_giving`` calls were evaluated before the logging
    # module decided whether the record was wanted, so a value the receiving picture could
    # not hold would have raised from inside a disabled diagnostic.  Performing them as
    # plain statements removes that failure path outright.
    #
    # ``ws-lits (n)`` [purchase/pl060.cbl:L266] supplies the caption for the printed line
    # and is therefore no longer read here.  Subscripts are literal 1, 2 and 3 in the
    # frozen source - not a loop - and are kept literal.
    ar.add_giving(  # [L551-L554]
        ws.total_net[0], ws.total_vat[0], receiving=_D_PRINT_MONEY
    )
    # [L556] if line-cnt > Page-Lines - 7 perform headings.
    # A RELATION-CONDITION ARITHMETIC SITE: ``Page-Lines - 7`` has NO receiving field, so
    # it is evaluated at intermediate precision inside the comparison and never stored.
    # One of six such sites in the migration; the other in this program is [L619].
    if (
        ar.compare(
            ws.line_cnt,
            ar.intermediate(
                lambda: ar.intermediate(ws.system_record.system_data_block.page_lines)
                - ar.intermediate(7)
            ),
        )
        > 0
    ):
        _headings(ws)  # [L557]
    # [L559] write print-record from line-6 after 3. OMITTED - the print file.
    ar.add_giving(  # [L561-L565]
        ws.total_net[1], ws.total_vat[1], receiving=_D_PRINT_MONEY
    )
    ar.add_giving(  # [L567-L571]
        ws.total_net[2], ws.total_vat[2], receiving=_D_PRINT_MONEY
    )

    if _IS_G_L(ws.system_record.system_data_block.level.level_1):  # [L573]
        _bl_close(ws)  # [L574]

    # [L576-L578] the maintainer's own banner: "Routine To Close Un-Applied CR. Notes".
    _fh("otm5_open", _ctx(ws, ws.otm5))  # [L580] open i-o open-item-file-5.

    # [L582] move zero to work-b.
    # LOAD-BEARING PLACEMENT. This is the SECOND of two resets of the accumulator that
    # becomes period total 8: ``cr-notes`` resets it at [L781] once per credit note
    # inside the OTM4 loop, and this one resets it again before the OTM5 pass. The two
    # resets belong to different accumulation phases and neither may be hoisted or merged
    # (rule R-3, Agent Action Plan section 0.8.4).
    ws.work_b = mv.move_figurative(mv.ZERO, _D_WORK_B)

    _LOG.info("Phase 2")  # [L583] display "2" at 1407.


def _init01__end_loop(ws: _Ws) -> None:
    """``end-loop.`` [purchase/pl060.cbl:L585-L600] - the OTM5 pass that swaps credits.

    Walks the whole open-item file and hands every open credit note to ``cr-swop``.
    Reached by fall-through from ``main-end``; left by the GO TO class 2 transfer at
    ``[purchase/pl060.cbl:L590]``.

    Section-qualified because ``end-loop.`` is declared twice - here and in ``cr-notes``
    at ``[purchase/pl060.cbl:L809]``.
    """
    while True:
        _fh("otm5_read_next", _ctx(ws, ws.otm5))  # [L588] read next record at end

        # [L589] if FS-Reply not = zero go to end-loop-end.
        # FINDING - THIS PASS TESTS ``not = zero`` WHILE ``cr-notes``' PASS TESTS ``= 10``
        # [purchase/pl060.cbl:L790], on the same file in the same program. The two
        # end-of-file tests are not equivalent - ``not = zero`` also catches 21, 22, 23
        # and 99 - and both are reproduced exactly as written.
        if ws.file_access.fs_reply != FsReply.SUCCESS:
            # GO TO class 2 - [L590] `go to end-loop-end`, whose block ``_init01`` runs
            # immediately after this call.
            break

        _group_move_oi(ws.otm5, ws.oi_header)  # [L592] GROUP MOVE into oi-header

        if _IS_S_CLOSED(ws.oi_header.oi_status):  # [L594]
            # GO TO class 1 - [L595] `go to end-loop`.
            continue

        if ws.oi_header.oi_type == 3:  # [L597]
            _cr_swop(ws)  # [L598]

        # GO TO class 1 - [L600] `go to end-loop`, the unconditional loop-back.
        continue


def _init01__end_loop_end(ws: _Ws) -> None:
    """``end-loop-end.`` [purchase/pl060.cbl:L602-L648] - truncate OTM4, write period total 8.

    Four things happen here that reach storage: the OTM4 extract is TRUNCATED, the
    open-item file is closed, ``SYSTOT-REC``'s ``pl-cn-unappl-this-month`` is
    accumulated, and nothing else. Everything else in the paragraph is a print line, a
    library call or the spool-out.
    """
    # [L605-L606] open output open-item-file-4. / close open-item-file-4.
    # THE OPEN-OUTPUT-THEN-CLOSE TRUNCATES THE OTM4 SEQUENCE. This is how ``pl060``
    # clears the extract ``pl055`` produced, and it is the exact mirror of the Sales
    # twin's truncation of OTM2 [sales/sl060.cbl:L677-L678]. ``open_output`` on the work
    # sequence discards its records, which is COBOL's own semantics for the verb.
    ws.otm4.open_output(ws.file_access)
    _otm4_status(ws)
    ws.otm4.close(ws.file_access)
    _otm4_status(ws)
    _fh("otm5_close", _ctx(ws, ws.otm5))  # [L607]

    # [L609-L617] THE THIRD LIBRARY GATE, identical in shape to [L387-L395]. It resets
    # the same flag a third time. It looks cacheable and it is NOT cached: Agent Action
    # Plan section 0.8.4 - "Any performance work is therefore out of scope by
    # construction, not merely unrequested."
    if _IS_FS_COBOL_FILES_USED(
        ws.system_record.system_data_block.rdbms_flat_statuses.file_system_used
    ):
        return_code = _cbl_check_file_exist(  # [L610-L611] using File-28 File-Info
            ws, "File-28", "purchase/pl060.cbl:L610"
        )
        if return_code != 0:  # [L612]
            ws.file_28_status = _FILE_28_NOT_EXISTS  # [L613]
        else:
            ws.file_28_status = _FILE_28_EXISTS  # [L615]

    # [L619-L621] A THREE-CONDITION ``AND`` whose first term is another
    # relation-condition arithmetic site: ``Page-Lines - 6``, again with no receiver.
    if (
        ar.compare(
            ws.line_cnt,
            ar.intermediate(
                lambda: ar.intermediate(ws.system_record.system_data_block.page_lines)
                - ar.intermediate(6)
            ),
        )
        > 0
        and _IS_FS_COBOL_FILES_USED(
            ws.system_record.system_data_block.rdbms_flat_statuses.file_system_used
        )
        and _is_file_28_exists(ws)
    ):
        _new_heading(ws)  # [L621]

    # [L623-L626] the un-applied-credits carry-forward LINE, which IS conditional.
    if (
        _IS_FS_COBOL_FILES_USED(
            ws.system_record.system_data_block.rdbms_flat_statuses.file_system_used
        )
        and _is_file_28_exists(ws)
    ):
        # [L624] move "Un-Applied Credits C/F " to l8-desc.
        # [L625] move work-b to l8-tot.
        # [L626] write print-record from line-8 after 3.  All three OMITTED - print file -
        # AND NOT LOGGED: a report line is out of scope per section 0.2.2, and ``work-b``
        # is an accumulated MONETARY VALUE, which the safe-event schema excludes from a
        # record (CWE-532).  THE ``if`` SURVIVES, because the split between this
        # conditional line and the UNCONDITIONAL period-total add below it is load-bearing
        # - the banner on that add explains why.
        pass

    # [L628] add work-b to pl-cn-unappl-this-month.
    # ******************************************************************************
    # THIS IS OUTSIDE THE [L623] GUARD, AND DELIBERATELY SO. The period at [L626] closes
    # that ``if``, so the accumulate executes UNCONDITIONALLY: the printed line is
    # conditional, the database effect is not. The Sales twin has the identical structure,
    # its own period-total add at [sales/sl060.cbl:L700] sitting outside the guard at
    # [sales/sl060.cbl:L695].
    #
    # This is SITE 8 of the nine period-total writes that Agent Action Plan section 0.6.4
    # calls "the sole writers" of ``SYSTOT-REC``, and the only ``SYSTOT-REC`` column
    # ``pl060`` touches. Indenting it under the guard would silently drop a ledger's
    # monthly total.
    # ******************************************************************************
    ws.system_record_4.purchase_ledger_data.pl_cn_unappl_this_month = ar.add_to(
        ws.work_b,
        receiver_value=ws.system_record_4.purchase_ledger_data.pl_cn_unappl_this_month,
        receiving=_D_PL_CN_UNAPPL,
    )

    # [L630-L635] THE MISSING-WRITE DEFECT.
    # ANOMALY A-NEW-2 [purchase/pl060.cbl:L630-L635] - the period at [L635] closes BOTH
    # ``if``s, so ``write print-record after 3`` belongs to the ``else`` arm alone. In
    # ``FS-Cobol-Files-Used`` (flat-file) mode ``PL133`` is moved into ``print-record``
    # and NEVER WRITTEN; only the RDBMS-mode message ``PL133T`` is printed. The Sales twin
    # carries the same defect at [sales/sl060.cbl:L702-L707]. Print-only, so there is no
    # database effect - but the control flow is reproduced and the missing ``write`` is
    # NOT supplied.
    # Reproduced deliberately per R-4; DO NOT FIX.
    if _is_purchase_missing(ws):  # [L630]
        # NEITHER ARM IS LOGGED.  Neither ``PL133`` nor ``PL133T`` is ever DISPLAYED:
        # both are ``move``d into ``print-record``, which makes them report content, out
        # of scope per section 0.2.2 - and section 0.3.4 converts a DISPLAY, not a report
        # line.  Narrating the missing ``write`` would additionally invent an operator
        # diagnostic for a defect the compiled program reports in no way at all, which is
        # the opposite of reproducing it.  BOTH ARMS SURVIVE AS WRITTEN, because their
        # asymmetry IS anomaly A-NEW-2 and the structure is its evidence.
        if _IS_FS_COBOL_FILES_USED(  # [L631]
            ws.system_record.system_data_block.rdbms_flat_statuses.file_system_used
        ):
            # [L632] move PL133 to print-record.  ... and no write follows.
            pass
        else:
            # [L634] move PL133T to print-record.
            # [L635] write print-record after 3.
            pass

    # [L637] close print-file. OMITTED with the rest of the print file.
    # [L638] call "SYSTEM" using Print-Report.
    # OMITTED ENTIRELY. Agent Action Plan section 0.1.1 excludes "the
    # `call "SYSTEM" using Print-Report` spool-out path that hands a report file to the
    # operating system", and rule R-1 forbids handing anything to a COBOL runtime. See
    # the OMISSIONS list in the footer.

    # [L639-L641] the fourth library gate, guarding CBL_DELETE_FILE.
    if _IS_FS_COBOL_FILES_USED(
        ws.system_record.system_data_block.rdbms_flat_statuses.file_system_used
    ) and _is_file_28_exists(ws):
        _cbl_delete_file(ws, "File-28", "purchase/pl060.cbl:L641")  # [L641]

    # [L643-L648] `move save-level-1 to level-1.` is COMMENTED OUT under the banner
    # "BYPASS CODE FOR G-L" - the other half of the pair at [L397-L403]. Recorded as a
    # FINDING in ``_init01``; nothing is restored here.



# ===========================================================================
# cr-swop      section.                               [purchase/pl060.cbl:L653]
# ===========================================================================


def _cr_swop(ws: _Ws) -> None:
    """``cr-swop section.`` [purchase/pl060.cbl:L653-L686] - close one un-applied credit.

    Called from ``[purchase/pl060.cbl:L598]`` for every open credit note the OTM5 pass
    finds. Two effects reach storage: ``oi-status`` is set to closed and ``oi-paid`` is
    reduced by the note's outstanding balance, then the row is rewritten.
    """
    # [L656] add oi-net oi-carriage oi-vat oi-c-vat giving work-1.  FOUR addends, and one
    # quantize into ``work-1`` rather than four.
    ws.work_1 = ar.add_giving(
        ws.oi_header.filler_1.oi_net,
        ws.oi_header.filler_1.oi_carriage,
        ws.oi_header.filler_1.oi_vat,
        ws.oi_header.filler_1.oi_c_vat,
        receiving=_D_WORK_1,
    )
    ws.work_1 = ar.add_to(  # [L657] add oi-paid to work-1.
        ws.oi_header.filler_1.oi_paid, receiver_value=ws.work_1, receiving=_D_WORK_1
    )

    # [L658-L661] a diagnostic with NO control transfer; [L663] is the maintainer's own
    # "Above should NOT happen". The pause is dropped and the branch that decides on it
    # is preserved (Agent Action Plan section 0.3.4).
    if ws.work_1 == 0:
        # [L659] display PL131.  A MIXED LITERAL: the diagnostic half is kept and the
        # trailing ": Return to continue" - the instruction to press the key that [L661]'s
        # ``accept`` reads - is dropped with the pause itself.
        _LOG.warning("%s", _PL131_NOTICE)  # [L659]
        if ws.ws_calling_data.ws_caller.strip() != "xl150":  # [L660]
            # [L661] accept ws-reply at 2434.  THE PAUSE IS DROPPED and the branch that
            # decides whether to pause is PRESERVED - it is the codebase's own
            # unattended-mode test.  Narrating the suppression would emit an event the
            # compiled program never produced (R-4).
            pass

    if _IS_FS_COBOL_FILES_USED(  # [L665]
        ws.system_record.system_data_block.rdbms_flat_statuses.file_system_used
    ) and _is_file_28_not_exists(ws):
        _new_heading(ws)  # [L666]

    # [L668] move 1 to oi-status. A REAL ``PUITM5-REC`` EFFECT - ``88 S-Closed value 1``
    # [copybooks/plwsoi.cob:L55].
    ws.oi_header.oi_status = mv.move(1, _D_OI_STATUS)

    # [L670-L676] the printed line: ``l7-cust``, ``l7-trans``, ``l7-cr-note``, ``l7-type``,
    # ``l7-bal``, ``l7-appl`` and the ``write``. All OMITTED - ``01 line-7`` is print
    # furniture. ``l7-cust`` receives the ``oi-supplier`` group, which is the third of the
    # three whole-group uses of that field.
    # NOT LOGGED EITHER.  Every operand the record carried is excluded by the
    # safe-event schema in ``acas_posting/dal/status.py``: the supplier group and the
    # invoice and credit-note numbers are RECORD KEYS, and the balance and the applied
    # amount are MONETARY VALUES (CWE-532).  The frozen source ``display``s none of them -
    # they are ``move``s into ``01 line-7`` - so there is nothing here for section 0.3.4
    # to convert.  Removing the record also removes an eager ``_oi_supplier_image`` call
    # that ran before the logging module decided whether the record was wanted.

    ws.line_cnt = ar.add_to(  # [L678] add 1 to line-cnt.
        1, receiver_value=ws.line_cnt, receiving=_D_LINE_CNT
    )
    # [L679-L680] if line-cnt > Page-Lines perform new-heading.
    if ar.compare(ws.line_cnt, ws.system_record.system_data_block.page_lines) > 0:
        _new_heading(ws)

    # ******************************************************************************
    # [L682] -> [L683] -> [L684]: THE ORDER OF THESE THREE STATEMENTS IS LOAD-BEARING.
    #
    #     682      add      work-1   to  work-b.      <- accumulates the POSITIVE balance
    #     683      multiply -1 by work-1.             <- only NOW is work-1 negated
    #     684      add      work-1 to oi-paid.        <- therefore REDUCES oi-paid
    #
    # ``work-b`` feeds period total 8 at [L628], so it must take the balance before the
    # sign flip; ``oi-paid`` must take it after, because the ``ADD`` is how the frozen
    # source performs a subtraction. Swapping ANY two of the three changes both the period
    # total and the stored ``PUITM5-REC`` row (rule R-3).
    # ******************************************************************************
    ws.work_b = ar.add_to(  # [L682]
        ws.work_1, receiver_value=ws.work_b, receiving=_D_WORK_B
    )
    # [L683] multiply -1 by work-1. No ``GIVING``: the receiver is SECOND.
    ws.work_1 = ar.multiply_by(-1, ws.work_1, receiving=_D_WORK_1)
    ws.oi_header.filler_1.oi_paid = ar.add_to(  # [L684]
        ws.work_1,
        receiver_value=ws.oi_header.filler_1.oi_paid,
        receiving=_D_OI_PAID,
    )

    _group_move_oi(ws.oi_header, ws.otm5)  # [L685] GROUP MOVE into WS-OTM5-Record
    _fh("otm5_rewrite", _ctx(ws, ws.otm5))  # [L686] rewrite open-item-record-5

    _cr_swop__main_exit(ws)


def _cr_swop__main_exit(ws: _Ws) -> None:
    """``main-exit.   exit section.`` [purchase/pl060.cbl:L688].

    One of TEN paragraphs in this program spelled ``main-exit``, which is why every
    function here is section-qualified. Reached by fall-through from
    ``[purchase/pl060.cbl:L686]``.
    """
    del ws


# ===========================================================================
# new-heading  section.                               [purchase/pl060.cbl:L691]
# headings     section.                               [purchase/pl060.cbl:L717]
#
# FINDING - the two sections are NEAR-DUPLICATES. They differ in exactly two respects:
# ``new-heading`` also writes ``line-1a`` [purchase/pl060.cbl:L701],
# [purchase/pl060.cbl:L707] and sets ``line-cnt`` to 6
# [purchase/pl060.cbl:L712], while ``headings`` writes neither and sets it to 5
# [purchase/pl060.cbl:L736]. They are exactly what an optimiser would collapse into one
# parameterised routine, and they are left as two (Agent Action Plan section 0.8.4).
#
# Both are presentation, so no line is emitted here - but they are NOT no-ops: each
# increments the page counter ``j`` and RESETS ``line-cnt``, and ``line-cnt`` is tested at
# [purchase/pl060.cbl:L541], [purchase/pl060.cbl:L556], [purchase/pl060.cbl:L619] and
# [purchase/pl060.cbl:L679]. Dropping the reset would change how often they are called,
# which is observable in the call sequence even though no page is printed. Rule R-5
# requires them to exist as named functions in any case.
# ===========================================================================


def _new_heading(ws: _Ws) -> None:
    """``new-heading section.`` [purchase/pl060.cbl:L691-L712].

    Page furniture, which is presentation and therefore omitted - except ``line-cnt``,
    which is load-bearing because [L556], [L619] and [L679] all test it.
    """
    ws.j = ar.add_to(1, receiver_value=ws.j, receiving=_D_J)  # [L694]
    # [L695] move j to l3-page.  [L696] move usera to l3-user.  Both OMITTED - print
    # items of ``01 line-3`` - AND NOT LOGGED.  A page number is report formatting, out of
    # scope per section 0.2.2, and ``usera`` (``05 Suser`` of the system record) is the
    # OPERATOR IDENTITY, which the safe-event schema excludes from a record at any level
    # (CWE-532).  The counter above stays: [L556], [L619] and [L679] all test ``line-cnt``,
    # and ``j`` selects which heading form is written.
    if ws.j != 1:  # [L698]
        # [L699-L703] four writes: line-1 after page, line-2, line-1a, then a blank.
        pass
    else:
        # [L705-L707] three writes, all ``before 1``: line-1, line-2, line-1a.
        pass
    # [L709] write print-record from line-4a after 1.  [L710-L711] blank line.
    # All OMITTED with the rest of the print file.
    ws.line_cnt = mv.move(6, _D_LINE_CNT)  # [L712] move 6 to line-cnt.
    _new_heading__main_exit(ws)


def _new_heading__main_exit(ws: _Ws) -> None:
    """``main-exit.   exit section.`` [purchase/pl060.cbl:L714]."""
    del ws


def _headings(ws: _Ws) -> None:
    """``headings section.`` [purchase/pl060.cbl:L717-L736].

    A near-duplicate of ``new-heading``, differing only in the absent ``line-1a`` write
    and in seeding ``line-cnt`` with 5 rather than 6. The duplication is preserved.
    """
    ws.j = ar.add_to(1, receiver_value=ws.j, receiving=_D_J)  # [L720]
    # [L721-L722] move j to l3-page. / move usera to l3-user.  OMITTED - print items -
    # and NOT LOGGED, for the same two reasons as [L695-L696] in ``new-heading``: report
    # formatting is out of scope, and ``usera`` is the operator identity.
    if ws.j != 1:  # [L724]
        # [L725-L728] three writes and a blank - NO ``line-1a`` here, unlike [L701].
        pass
    else:
        # [L730-L731] two writes - again no ``line-1a``, unlike [L707].
        pass
    # [L733] write print-record from line-4 after 1 - ``line-4``, where ``new-heading``
    # writes ``line-4a``.  [L734-L735] blank line. OMITTED.
    ws.line_cnt = mv.move(5, _D_LINE_CNT)  # [L736] move 5 to line-cnt - 5, NOT 6.
    _headings__main_exit(ws)


def _headings__main_exit(ws: _Ws) -> None:
    """``main-exit.   exit section.`` [purchase/pl060.cbl:L738]."""
    del ws


# ===========================================================================
# purch-comp   section.                               [purchase/pl060.cbl:L740]
# credit-comp  section.                               [purchase/pl060.cbl:L755]
#
# ******************************************************************************
# THESE ARE TWO SEPARATE FUNCTIONS AND THEY SHARE NO HELPER. NOT ONE LINE.
#
# Agent Action Plan section 0.6.1, verbatim: *"Normalising them into one helper would be
# the single easiest way to fail this migration."* The moving-average idiom is spelled
# FOUR mutually inconsistent ways across the cycle - ``purch-comp`` here,
# ``credit-comp`` here, ``compute-purch-pay`` in ``pl100``
# [purchase/pl100.cbl:L488-L507], and the Sales twins at [sales/sl060.cbl:L819] and
# [sales/sl060.cbl:L835] - and each spelling produces different figures. There is no
# ``average()`` utility in ``acas_posting/cobol/``, no parameter that selects a variant,
# and nothing imported from a sibling program module.
# ******************************************************************************
# ===========================================================================


def _purch_comp(ws: _Ws) -> None:
    """``purch-comp section.`` [purchase/pl060.cbl:L740-L751] - the average for types 1 and 2.

    Called from ``[purchase/pl060.cbl:L479]`` for Receipts and Accounts only, because
    ``[purchase/pl060.cbl:L478]``'s abbreviated relation reads ``oi-type = 1 OR
    oi-type = 2``. Credit notes take ``credit-comp`` instead.

    ANOMALY A-8 [purchase/pl060.cbl:L200], [purchase/pl060.cbl:L213],
    [purchase/pl060.cbl:L750], [purchase/pl060.cbl:L751] - DOUBLE TRUNCATION.
    ``03 work-2 pic s9(14) comp-3`` has FOURTEEN digits and ZERO decimal places, while
    ``03 work-goods pic s9(7)v99 comp-3`` carries TWO. So ``add work-goods to work-2``
    at [L750] DISCARDS THE PENCE on every accumulation, and
    ``divide purch-activety into work-2 giving purch-average`` at [L751] then discards
    the remainder as well, because ``03 Purch-Average binary-long``
    [copybooks/wspl.cob:L38] is an INTEGER. Both field widths are modelled exactly; an
    implementation that carried two decimals through would diverge from the oracle on
    almost every invoice.
    Reproduced deliberately per R-4; DO NOT FIX.

    ANOMALY A-10 [purchase/pl060.cbl:L743] - this is one of the four mutually
    inconsistent guards on one idiom. THIS variant guards with a two-condition ``AND``
    that HAS an ``ELSE`` and then increments the counter UNCONDITIONALLY.
    ``credit-comp`` [purchase/pl060.cbl:L764] guards identically but adds a SECOND,
    nested guard and never increments; ``pl100``'s ``compute-purch-pay``
    [purchase/pl100.cbl:L497] is a third variant; the Sales twins
    [sales/sl060.cbl:L819], [sales/sl060.cbl:L835] are the others.
    Reproduced deliberately per R-4; DO NOT FIX.

    AMBIGUITY Q-PURCH-AVERAGE-SIGN - ``Purch-Average`` is a SIGNED ``binary-long`` here
    and its bridge host variable is unsigned, exactly as anomaly A-11 documents for the
    Sales twin [common/salesMT.cbl:L305-L312]. The conversion belongs to the data-access
    layer, but the SIGN it receives is decided here: for a credit note ``work-goods`` is
    negative because of the ``pl055`` sign contract, so a negative average is reachable.
    What the bridge then stores has to be measured rather than assumed.
    """
    # [L743-L748] if purch-activety not = zero AND purch-average not = zero ... else ...
    if ws.purch.purch_activety != 0 and ws.purch.purch_average != 0:
        # [L745] multiply purch-activety by purch-average giving work-2, i.e.
        # ``work-2 = purch-activety * purch-average``. The product is stored into a
        # ZERO-SCALE receiver, which is where the pence would go if there were any.
        ws.work_2 = ar.multiply_by_giving(
            ws.purch.purch_activety, ws.purch.purch_average, receiving=_D_WORK_2
        )
    else:
        ws.work_2 = mv.move_figurative(mv.ZERO, _D_WORK_2)  # [L747]

    # [L749] add 1 to purch-activety.  UNCONDITIONAL, and present ONLY in this variant.
    ws.purch.purch_activety = ar.add_to(
        1, receiver_value=ws.purch.purch_activety, receiving=_D_PURCH_ACTIVETY
    )
    # [L750] add work-goods to work-2.  TRUNCATION 1 of A-8: two decimals into s9(14).
    ws.work_2 = ar.add_to(
        ws.work_goods, receiver_value=ws.work_2, receiving=_D_WORK_2
    )
    # [L751] divide purch-activety into work-2 giving purch-average.
    # ``divide A into B giving C`` means ``C = B / A``, so this is
    # ``purch-average = work-2 / purch-activety``. TRUNCATION 2 of A-8: an integer
    # receiver. Note the ``INTO`` form; ``sl100`` and ``pl100`` use the ``BY`` form, which
    # is the opposite operand order AS WRITTEN. It computes the same quotient -
    # accumulator / activity - so the difference is syntactic; the two forms are
    # still not conflated, because each program's source form is mirrored.
    ws.purch.purch_average = ar.divide_into_giving(
        ws.purch.purch_activety, ws.work_2, receiving=_D_PURCH_AVERAGE
    )

    _purch_comp__main_exit(ws)


def _purch_comp__main_exit(ws: _Ws) -> None:
    """``main-exit.   exit section.`` [purchase/pl060.cbl:L753]."""
    del ws


def _credit_comp(ws: _Ws) -> None:
    """``credit-comp section.`` [purchase/pl060.cbl:L755-L766] - the average for credit notes.

    Called from ``[purchase/pl060.cbl:L501]``, and only for ``oi-type = 3``.

    ANOMALY A-9 [purchase/pl060.cbl:L755-L766] - THERE IS NO
    ``add 1 to purch-activety`` ANYWHERE IN THIS SECTION. The activity counter is never
    incremented on the credit-note path, and the extra guard at [L764] suppresses the
    whole computation while the accumulator is still zero, so THE FIRST PURCHASE CREDIT
    NOTE FOR A SUPPLIER IS SILENTLY DROPPED FROM THE AVERAGE. This mirrors the Sales twin
    exactly [sales/sl060.cbl:L835-L843].
    Reproduced deliberately per R-4; DO NOT FIX.

    ANOMALY A-10 [purchase/pl060.cbl:L764] - the second of this program's two
    inconsistent guards. ``purch-comp`` guards once with an ``ELSE`` and increments
    unconditionally; this one guards TWICE - the same two-condition ``AND`` with its
    ``ELSE``, and then ``if work-2 not = zero`` around the accumulate and the divide
    together - and increments never. See ``_purch_comp`` for the other two variants.
    Reproduced deliberately per R-4; DO NOT FIX.

    ANOMALY A-8 [purchase/pl060.cbl:L765], [purchase/pl060.cbl:L766] - the same double
    truncation as ``purch-comp``, and for a credit note ``work-goods`` is NEGATIVE because
    ``pl055`` negated the source fields [purchase/pl055.cbl:L572-L575]. COBOL truncation
    is toward zero, so a negative accumulation truncates upward - which is the opposite
    direction from a floor division and is exactly why ``acas_posting.cobol.arithmetic``
    owns the store rather than this module.
    Reproduced deliberately per R-4; DO NOT FIX.
    """
    # [L758-L763] the identical outer guard, spelled with the ``and`` on the second line
    # rather than the first - a layout difference only.
    if ws.purch.purch_activety != 0 and ws.purch.purch_average != 0:
        ws.work_2 = ar.multiply_by_giving(  # [L760]
            ws.purch.purch_activety, ws.purch.purch_average, receiving=_D_WORK_2
        )
    else:
        ws.work_2 = mv.move_figurative(mv.ZERO, _D_WORK_2)  # [L762]

    # [L764] if work-2 not = zero - THE EXTRA GUARD. It covers BOTH [L765] and [L766],
    # because the period at [L766] closes it, so on the first credit note for a supplier
    # neither the accumulate nor the divide happens and ``purch-average`` keeps its old
    # value. There is NO counter increment here at all.
    if ws.work_2 != 0:
        ws.work_2 = ar.add_to(  # [L765] add work-goods to work-2.
            ws.work_goods, receiver_value=ws.work_2, receiving=_D_WORK_2
        )
        # [L766] divide purch-activety into work-2 giving purch-average -> C = B / A.
        ws.purch.purch_average = ar.divide_into_giving(
            ws.purch.purch_activety, ws.work_2, receiving=_D_PURCH_AVERAGE
        )

    _credit_comp__main_exit(ws)


def _credit_comp__main_exit(ws: _Ws) -> None:
    """``main-exit.   exit section.`` [purchase/pl060.cbl:L768]."""
    del ws



# ===========================================================================
# cr-notes     section.                               [purchase/pl060.cbl:L770]
#
# Performed from ``[purchase/pl060.cbl:L500]``, inside the OTM4 walk, for every credit
# note. It saves the current header, positions OTM5 at the note's own invoice, and walks
# forward applying the note against the supplier's open invoices. A second pass - which
# would re-walk from the supplier's first row with ``first-pass`` set to ``"N"``, so that
# ``[purchase/pl060.cbl:L802-L803]``'s second condition lets ANY invoice be apportioned
# rather than only the matching one - is what the source intends and what anomaly
# A-NEW-1 prevents.
# ===========================================================================


def _cr_notes(ws: _Ws) -> None:
    """``cr-notes section.`` [purchase/pl060.cbl:L770-L784] - set up the apportionment walk."""
    # [L773] move oi-header to si-header. GROUP MOVE - the whole 113-byte header is saved
    # so that [L826] can restore it after the walk has overwritten ``oi-header`` with
    # other rows. ``01 si-header`` [copybooks/plwssoi.cob] is byte-for-byte the layout of
    # ``01 OI-Header`` [copybooks/plwsoi.cob] with ``si-`` prefixes, so one buffer type
    # serves both.
    _group_move_oi(ws.oi_header, ws.si_header)
    ws.first_pass = mv.move_alphanumeric("Y", _D_FIRST_PASS)  # [L774]

    # [L775] move oi-supplier to oi5-supplier.  [L776] move oi-cr to oi5-invoice.
    # Together these build the START key: the credit note's own supplier and the invoice
    # number the note refers to.
    _move_supplier_group(ws.oi_header, ws.otm5)
    ws.otm5.oi_key.oi_invoice = mv.move(
        ws.oi_header.oi_cr, _D_OI5_INVOICE, sending_field=_D_OI_CR
    )

    # [L777] set fn-not-less-than to true. The access-type vocabulary, never a literal;
    # ``88 fn-not-less-than`` is value 8 in ``copybooks/wsfnctn.cob``.
    ws.file_access.access_type = AccessType.NOT_LESS_THAN
    # [L778] perform OTM5-Start. The maintainer's own comment preserves the ISAM verb the
    # facade replaced: ``start open-item-file-5 key not < oi5-key invalid key``.
    _fh("otm5_start", _ctx(ws, ws.otm5))

    # [L779-L780] if FS-Reply not = zero go to end-loop.
    # FINDING - the maintainer's inline ``*> 21 ?`` records that he was unsure which
    # status a failed START returns; the test is written against zero regardless. Compare
    # [L526]'s ``*> 21`` without the question mark and [L790]'s ``= 10``.
    if ws.file_access.fs_reply != FsReply.SUCCESS:
        # [L780] GO TO class 2 - forward to ``end-loop`` [L809], skipping the read loop.
        # FINDING - this path also skips [L781] and [L784], so ``work-b`` is NOT reset and
        # ``work-1`` is NOT reduced by ``si-paid``; yet ``end-loop`` still issues the
        # second START at [L819] whenever ``work-1`` is non-zero. Both consequences are
        # part of the specification and neither is smoothed away.
        _cr_notes__end_loop(ws)
        return

    # [L781] move zero to work-b. THE FIRST OF THIS PROGRAM'S TWO RESETS of the
    # period-total accumulator; the second is at [L582], before the OTM5 pass. They sit on
    # different accumulation phases - this one runs once per credit note inside the OTM4
    # walk - and neither may be hoisted or merged (rule R-3,
    # Agent Action Plan section 0.8.4).
    ws.work_b = mv.move_figurative(mv.ZERO, _D_WORK_B)

    # [L782-L783] if work-1 < zero multiply -1 by work-1.
    # An ABSOLUTE-VALUE idiom, not an unconditional sign flip: the guard is what makes it
    # one, and it is preserved. ``work-1`` arrives holding the note's gross from
    # [L470-L471], which is negative for a credit note because ``pl055`` negated the
    # source amounts [purchase/pl055.cbl:L572-L575].
    if ar.compare(ws.work_1, 0) < 0:
        # No ``GIVING``: the receiver is SECOND.
        ws.work_1 = ar.multiply_by(-1, ws.work_1, receiving=_D_WORK_1)

    # [L784] subtract si-paid from work-1 -> ``work-1 = work-1 - si-paid``.
    ws.work_1 = ar.subtract_from(
        ws.si_header.filler_1.oi_paid, receiver_value=ws.work_1, receiving=_D_WORK_1
    )

    _cr_notes__read_loop(ws)


def _cr_notes__read_loop(ws: _Ws) -> None:
    """``read-loop.`` [purchase/pl060.cbl:L786-L807] - walk OTM5 applying the credit note.

    Every exit from this paragraph reaches ``end-loop`` [purchase/pl060.cbl:L809], either
    by an explicit ``GO TO`` or by falling out of the bottom, so ``end-loop`` is performed
    once after the loop - the ``break`` PLUS the post-loop work that
    Agent Action Plan section 0.6.3 requires, never the ``break`` alone.
    """
    while True:
        # [L789] perform OTM5-Read-Next. The maintainer's comment preserves
        # ``read open-item-file-5 next record at end``.
        _fh("otm5_read_next", _ctx(ws, ws.otm5))

        # [L790-L791] if FS-Reply = 10 go to end-loop.
        # FINDING - THIS pass tests ``= 10`` while the OTM5 pass at [L589] tests
        # ``not = zero`` on the SAME FILE IN THE SAME PROGRAM. The two are not equivalent:
        # any non-zero status other than 10 continues here and terminates there. Both
        # spellings are reproduced exactly as written.
        if ws.file_access.fs_reply == FsReply.END_OF_FILE:
            break  # [L791] GO TO class 2 -> end-loop [L809]

        # [L793] move open-item-record-5 to oi-header. The maintainer's own comment
        # ``*> WS-OTM5-Record.`` records that the two name the same storage.
        _group_move_oi(ws.otm5, ws.oi_header)

        if ws.oi_header.oi_type != 2:  # [L794] only Account Invoices are apportionable
            continue  # [L795] GO TO class 1 -> read-loop [L786]

        # [L797-L798] if oi-supplier not = si-supplier go to end-loop.
        # A GROUP COMPARE of the seven bytes, which is how the walk detects that it has
        # run past the credit note's own supplier - the file is in supplier order.
        if _oi_supplier_image(ws.oi_header) != _oi_supplier_image(ws.si_header):
            break  # [L798] GO TO class 2 -> end-loop [L809]

        if _IS_S_CLOSED(ws.oi_header.oi_status):  # [L799] already settled
            continue  # [L800] GO TO class 1 -> read-loop [L786]

        # [L802-L803] if si-cr = oi-invoice OR first-pass = "N" perform apportion.
        # On the FIRST pass only the invoice the note names is apportioned; on the second
        # pass ``first-pass`` is ``"N"`` so any remaining invoice qualifies. Anomaly
        # A-NEW-1 means the second pass never happens, so in practice only the named
        # invoice is ever apportioned.
        if (
            ar.compare(ws.si_header.oi_cr, ws.oi_header.oi_key.oi_invoice) == 0
            or ws.first_pass == "N"
        ):
            _apportion(ws)  # [L804]

        # [L806-L807] if work-1 not equal zero go to read-loop.
        # FINDING - spelled ``not equal`` in words here, where every sibling test in this
        # program uses ``not =``. A spelling variant only, reproduced as written.
        if ws.work_1 != 0:
            continue  # [L807] GO TO class 1 -> read-loop [L786]

        # FALL-THROUGH - ``work-1`` is exhausted, so control drops out of the paragraph
        # into ``end-loop`` [L809]. This is the loop's normal exit, not a ``GO TO``.
        break

    _cr_notes__end_loop(ws)


def _cr_notes__end_loop(ws: _Ws) -> None:
    """``end-loop.`` [purchase/pl060.cbl:L809-L821] - arm the second pass, then never run it."""
    # [L812-L814] if work-1 = zero OR first-pass not = "Y" go to main-end.
    if ws.work_1 == 0 or ws.first_pass != "Y":
        _cr_notes__main_end(ws)  # [L814] GO TO class 2 -> main-end [L823]
        return

    ws.first_pass = mv.move_alphanumeric("N", _D_FIRST_PASS)  # [L815]
    # [L816] move si-supplier to oi5-supplier.  [L817] move zero to oi5-invoice.
    # Re-position at the supplier's FIRST row so the second pass can apportion the
    # remainder against any open invoice rather than only the named one.
    _move_supplier_group(ws.si_header, ws.otm5)
    ws.otm5.oi_key.oi_invoice = mv.move_figurative(mv.ZERO, _D_OI5_INVOICE)
    ws.file_access.access_type = AccessType.NOT_LESS_THAN  # [L818]
    _fh("otm5_start", _ctx(ws, ws.otm5))  # [L819]

    # ******************************************************************************
    # ANOMALY A-NEW-1 [purchase/pl060.cbl:L819-L821] - a lost ``invalid key`` conditional
    # makes ``go to main-end`` unconditional and ``go to read-loop`` dead, so the
    # credit-note second apportionment pass never executes.
    #
    #     818      set      fn-not-less-than to true.
    #     819      perform  OTM5-Start.      *>   start ... invalid key
    #     820               go to main-end.          <- UNCONDITIONAL
    #     821      go       to  read-loop.           <- UNREACHABLE
    #
    # The original statement was ``start open-item-file-5 key not < oi5-key invalid key
    # go to main-end``, in which the transfer belonged to the ``invalid key`` branch and
    # [L821] was the success path back into the walk. When the I/O verb was replaced by
    # ``perform OTM5-Start.`` the PERIOD terminated the sentence, so [L820]'s transfer
    # became unconditional and [L821] became unreachable. The maintainer's own inline
    # comment at [L819] still carries the original ``invalid key`` wording, which is the
    # direct evidence of the conversion accident. The indentation of [L820] - eight
    # further columns, as a continuation would be - is the second piece of evidence.
    #
    # Observable effect: ``first-pass`` has just been set to ``"N"`` and the cursor has
    # just been repositioned, and then control leaves immediately, so no row is read and
    # nothing is apportioned. The remainder of the credit note stays unapplied and
    # ``PUITM5-REC`` keeps rows that the intended second pass would have settled. The
    # Sales twin's equivalent transfer [sales/sl060.cbl:L908] IS reachable, which is what
    # makes ``ba020-end-loop`` there both a terminator and a re-dispatcher.
    #
    # Reproduced deliberately per R-4; DO NOT FIX. Neither the dead statement at [L821]
    # nor the lost ``invalid key`` conditional at [L819-L820] may be restored (rule R-3).
    #
    # AMBIGUITY Q-CR-NOTES-SECOND-PASS - the resulting ``PUITM5-REC`` state therefore
    # differs from ``SAITM3-REC`` under the same seed: purchase credit notes retain an
    # unapplied remainder that sales credit notes do not. Which rows differ, and whether
    # ``oi-status`` or ``oi-paid`` or both diverge, has to be measured against the
    # compiled oracle rather than reasoned about.
    # ******************************************************************************
    _cr_notes__main_end(ws)  # [L820] GO TO class 2 (unconditional - A-NEW-1)
    # UNREACHABLE (A-NEW-1) - [L821] ``go       to  read-loop.`` Left as a comment rather
    # than as a statement because Python has no way to spell a statement that cannot be
    # reached; a reader diffing this function against [L809-L821] sees it here, in source
    # order, immediately after the transfer that orphaned it.
    return


def _cr_notes__main_end(ws: _Ws) -> None:
    """``main-end.`` [purchase/pl060.cbl:L823-L826] - restore the saved header.

    This is ``cr-notes``' post-loop work, and it is a real effect rather than
    housekeeping: the caller at [purchase/pl060.cbl:L500] resumes at
    [purchase/pl060.cbl:L501] with ``credit-comp``, which reads ``work-goods``, and then
    at [purchase/pl060.cbl:L521] group-moves ``oi-header`` into the OTM5 record area.
    Without the restore, the row written there would be whichever invoice the walk last
    read instead of the credit note itself. Losing it would silently corrupt
    ``PUITM5-REC`` (Agent Action Plan section 0.6.3).
    """
    _group_move_oi(ws.si_header, ws.oi_header)  # [L826]
    _cr_notes__main_exit(ws)


def _cr_notes__main_exit(ws: _Ws) -> None:
    """``main-exit.   exit section.`` [purchase/pl060.cbl:L828]."""
    del ws


# ===========================================================================
# apportion    section.                               [purchase/pl060.cbl:L831]
#
# The three-way split: a credit note is applied to one open invoice, and the amount
# applied is the smaller of the invoice's outstanding balance and the note's remaining
# value. Which of ``oi-status`` and ``si-status`` is closed depends on WHICH of the three
# cases held, and the three cases set DIFFERENT combinations. ``sl060`` expresses its
# asymmetry differently again, through an inline ``Clear-Invoice-Deduct`` perform in two
# of its three branches [sales/sl060.cbl:L935-L955]; this section's shape comes from this
# section's source and from nowhere else.
# ===========================================================================


def _apportion(ws: _Ws) -> None:
    """``apportion section.`` [purchase/pl060.cbl:L831-L865] - apply the note to one invoice."""
    # [L834] add oi-net oi-carriage oi-vat oi-c-vat giving work-a. FOUR addends, one store.
    ws.work_a = ar.add_giving(
        ws.oi_header.filler_1.oi_net,
        ws.oi_header.filler_1.oi_carriage,
        ws.oi_header.filler_1.oi_vat,
        ws.oi_header.filler_1.oi_c_vat,
        receiving=_D_WORK_A,
    )
    # [L835] subtract oi-paid from work-a -> ``work-a = work-a - oi-paid``, the invoice's
    # outstanding balance.
    ws.work_a = ar.subtract_from(
        ws.oi_header.filler_1.oi_paid, receiver_value=ws.work_a, receiving=_D_WORK_A
    )

    if ws.work_a == 0:  # [L837] nothing outstanding: just close the row
        ws.oi_header.oi_status = mv.move(1, _D_OI_STATUS)  # [L838]
        # [L839] GO TO class 4 - ``main-rewrite`` [L867] performs the rewrite and then falls
        # through into ``main-exit`` [L875], so the transfer is a call followed by a
        # return and there is no path back into the statements above.
        _apportion__main_rewrite(ws)
        return

    if not ar.compare(ws.work_a, 0) > 0:  # [L841] if work-a not > zero
        # [L842] GO TO class 3 - RETURN WITHOUT REWRITING. A negative outstanding balance leaves
        # ``PUITM5-REC`` untouched: a distinct rejection disposition with NO database
        # effect, and it is reached before any status is set.
        _apportion__main_exit(ws)
        return

    if ar.compare(ws.work_a, ws.work_1) == 0:  # [L844] exact match
        ws.oi_header.filler_1.oi_paid = ar.add_to(  # [L845]
            ws.work_1,
            receiver_value=ws.oi_header.filler_1.oi_paid,
            receiving=_D_OI_PAID,
        )
        ws.si_header.filler_1.oi_paid = ar.add_to(  # [L846]
            ws.work_1,
            receiver_value=ws.si_header.filler_1.oi_paid,
            receiving=_D_OI_PAID,
        )
        # [L847] add work-1 to oi-p-c. ``oi-p-c`` takes the apportioned amount in ALL
        # THREE branches - a real ``PUITM5-REC`` effect in each.
        ws.oi_header.filler_1.oi_p_c = ar.add_to(
            ws.work_1,
            receiver_value=ws.oi_header.filler_1.oi_p_c,
            receiving=_D_OI_P_C,
        )
        ws.work_1 = mv.move_figurative(mv.ZERO, _D_WORK_1)  # [L848]
        # [L849] move 1 to oi-status si-status. BOTH statuses - the note is exhausted and
        # the invoice is settled in the same step.
        ws.oi_header.oi_status, ws.si_header.oi_status = mv.move_to_all(
            1, (_D_OI_STATUS, _D_OI_STATUS)
        )
    elif ar.compare(ws.work_a, ws.work_1) > 0:  # [L851] invoice larger than the note
        ws.oi_header.filler_1.oi_paid = ar.add_to(  # [L852]
            ws.work_1,
            receiver_value=ws.oi_header.filler_1.oi_paid,
            receiving=_D_OI_PAID,
        )
        ws.si_header.filler_1.oi_paid = ar.add_to(  # [L853]
            ws.work_1,
            receiver_value=ws.si_header.filler_1.oi_paid,
            receiving=_D_OI_PAID,
        )
        ws.oi_header.filler_1.oi_p_c = ar.add_to(  # [L854]
            ws.work_1,
            receiver_value=ws.oi_header.filler_1.oi_p_c,
            receiving=_D_OI_P_C,
        )
        ws.work_1 = mv.move_figurative(mv.ZERO, _D_WORK_1)  # [L855]
        # [L856] move 1 to si-status. THE NOTE ONLY - the invoice keeps a balance and so
        # keeps its open status.
        ws.si_header.oi_status = mv.move(1, _D_OI_STATUS)
    else:  # [L857] the note is larger than the invoice
        ws.oi_header.filler_1.oi_paid = ar.add_to(  # [L858]
            ws.work_a,
            receiver_value=ws.oi_header.filler_1.oi_paid,
            receiving=_D_OI_PAID,
        )
        ws.si_header.filler_1.oi_paid = ar.add_to(  # [L859]
            ws.work_a,
            receiver_value=ws.si_header.filler_1.oi_paid,
            receiving=_D_OI_PAID,
        )
        ws.oi_header.filler_1.oi_p_c = ar.add_to(  # [L860]
            ws.work_a,
            receiver_value=ws.oi_header.filler_1.oi_p_c,
            receiving=_D_OI_P_C,
        )
        # [L861] subtract work-a from work-1 -> ``work-1 = work-1 - work-a``, the note's
        # remainder, which keeps the read loop at [L806] going.
        ws.work_1 = ar.subtract_from(
            ws.work_a, receiver_value=ws.work_1, receiving=_D_WORK_1
        )
        # [L862] move 1 to oi-status. THE INVOICE ONLY.
        ws.oi_header.oi_status = mv.move(1, _D_OI_STATUS)

    # [L864-L865] if work-1 = zero move 1 to si-status. A UNIFORM POST-CHECK applying to
    # all three branches, which ``sl060`` does not have at all. It is redundant after
    # [L849] and [L856], where ``work-1`` was just zeroed and ``si-status`` just set, and
    # it is what closes the note in the third branch when the remainder happens to land
    # exactly on zero. Left exactly where it is (rule R-3).
    if ws.work_1 == 0:
        ws.si_header.oi_status = mv.move(1, _D_OI_STATUS)

    # FALL-THROUGH into ``main-rewrite`` [L867].
    _apportion__main_rewrite(ws)


def _apportion__main_rewrite(ws: _Ws) -> None:
    """``main-rewrite.`` [purchase/pl060.cbl:L867-L871] - store the apportioned row.

    Also the target of ``[purchase/pl060.cbl:L839]``'s class 4 transfer. The maintainer's
    superseded ISAM form is preserved in comments at ``[purchase/pl060.cbl:L872-L873]``.
    """
    _group_move_oi(ws.oi_header, ws.otm5)  # [L870] GROUP MOVE into WS-OTM5-Record
    _fh("otm5_rewrite", _ctx(ws, ws.otm5))  # [L871] rewrite open-item-record-5
    # FALL-THROUGH into ``main-exit`` [L875].
    _apportion__main_exit(ws)


def _apportion__main_exit(ws: _Ws) -> None:
    """``main-exit.   exit section.`` [purchase/pl060.cbl:L875].

    Reached by fall-through from ``main-rewrite`` and by
    ``[purchase/pl060.cbl:L842]``'s class 3 transfer, which is the only way out of this
    section that leaves ``PUITM5-REC`` unwritten.
    """
    del ws



# ===========================================================================
# BL-Open      section.                               [purchase/pl060.cbl:L877]
#
# Performed once from ``[purchase/pl060.cbl:L406]`` under ``G-L``, and again from
# ``[purchase/pl060.cbl:L1008]`` whenever a batch fills up at 99 items. It allocates the
# next batch number, builds the batch header, and opens whichever posting files the IRS
# fan-out switch selects.
# ===========================================================================


#: ``05 WS-Batch-Nos pic 9(5)`` [copybooks/wsbatch.cob:L19] - the scale at which
#: ``WS-Ledger`` [:L15] contributes to the six digits ``WS-Batch-Key9`` reads.
_BATCH_NOS_SCALE: Final[int] = 10**5


def _restate_ws_batch_key9(batch: GlBatchRecord) -> None:
    """Keep ``WS-Batch-Key9`` in step with the two members it redefines.

    ⭐⭐ ONE STORAGE, TWO READINGS. ``03 WS-Batch-Key.`` holds ``05 WS-Ledger
    pic 9.`` and ``05 WS-Batch-Nos pic 9(5).``, and ``03 WS-Batch-Key9 redefines
    WS-Batch-Key pic 9(6).`` [copybooks/wsbatch.cob:L14-L21] is those SAME six
    bytes read as one number. ``move next-batch to WS-Batch-nos``
    [purchase/pl060.cbl:L885] and ``move 2 to WS-Ledger`` [:L886] therefore change
    what ``WS-Batch-Key9`` reads, instantly - in COBOL there is nothing to keep in
    step because there is only one storage. Python has no aliasing, so restating it
    is a MODELLING obligation, not a new rule.

    THE ROLLOVER IS WHY THIS IS REACHED TWICE. ``if items = 99 / perform BL-Close /
    perform BL-Open`` [purchase/pl060.cbl:L1006] closes the full batch and opens the
    next, so a hundredth item returns here with a key already in working storage.
    Without the restatement the grouped reading held the NEW batch while the
    redefined reading still held the PREVIOUS one, and ``acas007``'s
    ``synchronise_batch_key_views`` - which deliberately refuses to pick between two
    non-default disagreeing readings, because ``bb000-HV-Load`` reads
    ``WS-BATCH-KEY9`` [common/glbatchMT.cbl:L1069] while ``ba070`` logs
    ``ws-BATCH-KEY`` - raised ``BatchKeyViewsDisagreeError`` and aborted the run,
    turning a key rollover into a failure.

    ⛔ DO NOT relax the reconciler instead. Its refusal is the safeguard; the defect
    was here, at the writer. NOT a new validation (rule R-3) and NOT an anomaly
    repair (rule R-4) - nothing is tested, clamped or corrected, and the value
    computed is the one the COBOL's own bytes already carry after [:L885-L886].

    Args:
        batch: ``01 WS-Batch-Record.`` [copybooks/wsbatch.cob:L13], mutated in
            place so both readings of its key agree.
    """
    batch.ws_batch_key9.ws_batch_key9 = (
        int(batch.ws_batch_key.ws_ledger) * _BATCH_NOS_SCALE
        + int(batch.ws_batch_key.ws_batch_nos)
    )


def _bl_open(ws: _Ws) -> None:
    """``BL-Open section.`` [purchase/pl060.cbl:L877-L921] - allocate and build the batch."""
    _fh("gl_batch_open", _ctx(ws, ws.batch))  # [L880] open i-o batch-file
    # FINDING - [L881-L883] is a commented-out ``if fs-reply not = zero / close / open
    # output`` fallback of exactly the shape that [L909-L912] and [L916-L919] still use
    # live. The batch file therefore has NO create-on-absence recovery, where the two
    # posting files do. Left absent.

    # [L885] move next-batch to WS-Batch-nos.  [L886] move 2 to WS-Ledger.
    # Ledger 2 is Purchase; the General Ledger family writes 1 and Sales writes 3.
    ws.batch.ws_batch_key.ws_batch_nos = mv.move(
        ws.system_record.general_ledger_block.next_batch,
        _D_WS_BATCH_NOS,
        sending_field=_D_NEXT_BATCH,
    )
    ws.batch.ws_batch_key.ws_ledger = mv.move(2, _D_WS_LEDGER)
    # ⭐ The two moves above have just changed the bytes ``WS-Batch-Key9`` redefines,
    # so its reading is restated - see `_restate_ws_batch_key9`.
    _restate_ws_batch_key9(ws.batch)
    # [L887] add 1 to Next-Batch. A ``SYSTEM-REC`` MUTATION, diff-visible and load-bearing
    # for batch numbering: it is what makes the number allocated at [L885] unique.
    ws.system_record.general_ledger_block.next_batch = ar.add_to(
        1,
        receiver_value=ws.system_record.general_ledger_block.next_batch,
        receiving=_D_NEXT_BATCH,
    )

    # [L889-L890] move zero to batch-status cleared-status. TWO receivers, one statement.
    ws.batch.batch_status, ws.batch.cleared_status = mv.move_to_all(
        mv.ZERO, (_D_BATCH_STATUS, _D_CLEARED_STATUS)
    )
    ws.batch.bcycle = mv.move(  # [L891] move scycle to bcycle
        ws.system_record.system_data_block.scycle, _D_BCYCLE, sending_field=_D_SCYCLE
    )
    # ******************************************************************************
    # [L892] move run-date to entered.
    # THE CONTROLLED-CLOCK OBSERVABLE. ``Run-Date binary-long``
    # [copybooks/wssystem.cob:L67] is one of the two values ``acas_posting/clock.py``
    # pins, and it arrives here purely through the ``system-record`` linkage parameter.
    # This module reads no clock of any kind (rule R-6) and does not import the clock.
    # ******************************************************************************
    ws.batch.dates.entered = mv.move(
        ws.system_record.system_data_block.run_date,
        _D_ENTERED,
        sending_field=_D_RUN_DATE,
    )

    ws.batch.description = mv.move_alphanumeric(  # [L894]
        "Purchase Ledger Orders", _D_DESCRIPTION
    )
    # [L895-L900] move zero to bdefault batch-def-ac batch-def-pc items input-gross
    # input-vat actual-gross actual-vat. EIGHT receivers in one statement, spelled across
    # six source lines; not a loop.
    (
        ws.batch.posting_data.b_default,
        ws.batch.posting_data.batch_def_ac,
        ws.batch.posting_data.batch_def_pc,
        ws.batch.items,
        ws.batch.amounts.input_gross,
        ws.batch.amounts.input_vat,
        ws.batch.amounts.actual_gross,
        ws.batch.amounts.actual_vat,
    ) = mv.move_to_all(
        mv.ZERO,
        (
            _D_BDEFAULT,
            _D_BATCH_DEF_AC,
            _D_BATCH_DEF_PC,
            _D_ITEMS,
            _D_INPUT_GROSS,
            _D_INPUT_VAT,
            _D_ACTUAL_GROSS,
            _D_ACTUAL_VAT,
        ),
    )

    ws.batch.posting_data.convention = mv.move_alphanumeric("DR", _D_CONVENTION)  # [L902]
    ws.batch.posting_data.batch_def_code = mv.move_alphanumeric(  # [L903]
        "PL", _D_BATCH_DEF_CODE
    )
    ws.batch.posting_data.batch_def_vat = mv.move_alphanumeric(  # [L904]
        "I", _D_BATCH_DEF_VAT
    )

    # ******************************************************************************
    # ANOMALY A-17 [purchase/pl060.cbl:L905] - the CONSUMER half of the unexplained
    # ``move RRN to postings`` that the maintainer annotated ``*> Why ?`` at
    # [purchase/pl060.cbl:L1028]. It is NOT inert: ``postings`` is a ``SYSTEM-REC`` column
    # that [L1028] writes at batch close and this line reads at the next batch open, and
    # [L921] then seeds ``RRN`` from it. The producer/consumer cycle is
    # [L1028] -> [L905] -> [L921], and its effect is to allocate the next batch's starting
    # relative record number. Optimising the round trip away would renumber every
    # ``GLPOSTING-REC`` row.
    # Reproduced deliberately per R-4; DO NOT FIX.
    #
    # AMBIGUITY Q-A17-POSTINGS-EFFECT - Agent Action Plan section 0.6.8 requires the
    # observable effect of the [L1028] move to be measured against the compiled program
    # rather than reasoned about, precisely because the maintainer himself does not know
    # why it is there. What is reproduced here is the data flow; what the oracle has to
    # settle is the stored value when ``RRN`` has been advanced past ``postings``' picture.
    # ******************************************************************************
    # [L905] add postings 1 giving batch-start -> ``batch-start = postings + 1``.
    ws.batch.batch_start = ar.add_giving(
        ws.system_record.general_ledger_block.postings, 1, receiving=_D_BATCH_START
    )

    # [L907] if irs-used OR IRS-Both-Used. Fan-out site 1 of 7; each site's predicate is
    # spelled differently and none is harmonised with another (section 2.9 of the brief).
    if _IS_IRS_USED(
        ws.system_record.general_ledger_block.irs_instead
    ) or _IS_IRS_BOTH_USED(ws.system_record.general_ledger_block.irs_instead):
        # [L908] perform SPL-Posting-Open-Extend -> open extend irs-post-file.
        _fh("spl_posting_open_extend", _ctx(ws, ws.irs_posting))
        # [L909] if fs-reply not = zero - the maintainer's own comment reads "wont happen
        # in FH", and the fallback is kept anyway.
        if ws.file_access.fs_reply != FsReply.SUCCESS:
            _fh("spl_posting_close", _ctx(ws, ws.irs_posting))  # [L910]
            # [L911] perform SPL-Posting-Open-Output. THIS DELETES EVERY ROW of
            # ``PSIRSPOST-REC`` [common/acas008.cbl:L313-L319],
            # [common/acas008.cbl:L571-L574] - the handler implements open-output on a
            # sequential file as a full delete. It is reachable only from this fallback.
            _fh("spl_posting_open_output", _ctx(ws, ws.irs_posting))

    # [L914] if IRS-Both-Used or G-L. Fan-out site 2 of 7 - note the DIFFERENT predicate.
    if _IS_IRS_BOTH_USED(
        ws.system_record.general_ledger_block.irs_instead
    ) or _IS_G_L(ws.system_record.system_data_block.level.level_1):
        _fh("gl_posting_open", _ctx(ws, ws.posting))  # [L915] open i-o posting-file
        if ws.file_access.fs_reply != FsReply.SUCCESS:  # [L916]
            _fh("gl_posting_close", _ctx(ws, ws.posting))  # [L917]
            _fh("gl_posting_open_output", _ctx(ws, ws.posting))  # [L918]

    # [L921] move batch-start to RRN. ``RRN`` is ``03 Rrn pic 9(5) comp``
    # [copybooks/wsfnctn.cob:L24], carried on ``File-Access`` rather than on the posting
    # record; this is the third link of the A-17 cycle.
    ws.file_access.rrn = mv.move(
        ws.batch.batch_start, _D_RRN, sending_field=_D_BATCH_START
    )

    _bl_open__main_exit(ws)


def _bl_open__main_exit(ws: _Ws) -> None:
    """``main-exit.   exit section.`` [purchase/pl060.cbl:L923]."""
    del ws


# ===========================================================================
# BL-Write     section.                               [purchase/pl060.cbl:L926]
#
# The maintainer's own boxed warning at [purchase/pl060.cbl:L928-L935] states the two
# preconditions: a General Ledger account number must exist for EVERY analysis code, and
# the IRS convention that default account 31 is VAT input tax and 32 is VAT output tax
# must have been followed. That convention is why [purchase/pl060.cbl:L993] moves 31 in
# this Purchase program while [sales/sl060.cbl:L1139] moves 32 in the Sales one.
# ===========================================================================


def _bl_write(ws: _Ws) -> None:
    """``BL-Write section.`` [purchase/pl060.cbl:L926-L1008] - one posting per invoice."""
    # ******************************************************************************
    # [L937] move u-date (1:6) to post-date (1:6).
    # [L938] move u-date (9:2) to post-date (7:2).
    # ``u-date`` is ten characters, ``DD/MM/CCYY``; ``post-date`` is eight
    # [copybooks/wspost.cob:L18]. Taking (1:6) and then (9:2) copies ``DD/MM/`` and then
    # the last two year digits, so THE CENTURY DIGITS ARE DROPPED and the stored form is
    # ``DD/MM/YY``. This is the origin of the two-digit-versus-four-digit date text forms
    # the harness normaliser has to canonicalise. Reference modification is ONE-BASED on
    # both the sending and the receiving side and is performed by
    # ``acas_posting.cobol.move``, never by Python slicing.
    # ******************************************************************************
    post_date = mv.ref_mod_into(
        ws.posting.post_date, 1, 6, mv.ref_mod(ws.maps03_ws.u_date, 1, 6)
    )
    post_date = mv.ref_mod_into(
        post_date, 7, 2, mv.ref_mod(ws.maps03_ws.u_date, 9, 2)
    )
    ws.posting.post_date = mv.move_alphanumeric(
        post_date, _D_POST_DATE, sending_field=_D_POST_DATE
    )

    ws.posting.ws_post_key.batch = mv.move(  # [L939] move WS-Batch-nos to batch
        ws.batch.ws_batch_key.ws_batch_nos,
        _D_POST_BATCH,
        sending_field=_D_WS_BATCH_NOS,
    )
    ws.batch.items = ar.add_to(  # [L940] add 1 to items
        1, receiver_value=ws.batch.items, receiving=_D_ITEMS
    )
    ws.posting.ws_post_key.post_number = mv.move(  # [L941] move items to Post-number
        ws.batch.items, _D_POST_NUMBER, sending_field=_D_ITEMS
    )
    ws.posting.post_amount = mv.move(  # [L942] move work-net to Post-amount
        ws.work_net, _D_POST_AMOUNT, sending_field=_D_WORK_NET
    )

    # ******************************************************************************
    # [L947-L956] the legend. The maintainer's comment at [L944-L945] explains the intent:
    # "using folio/invoice no + ' : ' supplier name instead of batch/item on posting file
    # for both IRS & GL."
    #
    #     947      move     oi-invoice to m.               <- EDITED move, m is z(7)9
    #     948      move     zero to b.
    #     949      inspect  m tallying b for leading space.
    #     950      subtract b from 8 giving c.             <- c = 8 - b, the OLD b
    #     951      add      1 to b.                        <- b becomes the 1-based start
    #     953      move     1  to  xx.
    #     954-956  string   m (b:c) / " : " / purch-name into post-legend pointer xx.
    #
    # ONE ``STRING`` with three sources sharing one ``POINTER``, which is what makes the
    # receiver's tail keep whatever it held rather than being space-filled. ``sl100``
    # builds the same column with FIVE separate ``STRING`` statements
    # [sales/sl100.cbl:L620-L628] and the two are NOT unified.
    # ******************************************************************************
    ws.m = mv.move_to_edited(ws.oi_header.oi_key.oi_invoice, _D_M)  # [L947]
    ws.b = mv.move_figurative(mv.ZERO, _D_B)  # [L948]
    ws.b = mv.inspect_tallying_leading(ws.m, mv.SPACE, ws.b)  # [L949]
    # [L950] subtract b from 8 giving c -> ``c = 8 - b`` with the pre-increment ``b``.
    ws.c = ar.subtract_giving(ws.b, minuend=8, receiving=_D_C)
    ws.b = ar.add_to(1, receiver_value=ws.b, receiving=_D_B)  # [L951]
    ws.xx = mv.move(1, _D_XX)  # [L953]
    ws.posting.post_legend, ws.xx = mv.string_into(
        ws.posting.post_legend,
        (
            mv.ref_mod(ws.m, ws.b, ws.c),
            " : ",
            ws.purch.purch_name,
        ),
        pointer=ws.xx,
        delimited_by=mv.DELIMITED_BY_SIZE,
    )

    # [L958] move p-creditors to post-cr.  [L959] move bl-purch-ac to post-dr.
    # The credit side is the creditors control account and the debit side the purchases
    # account - the Purchase convention, and the mirror image of the Sales one.
    ws.posting.post_cr = mv.move(
        ws.system_record.purchase_ledger_block.p_creditors,
        _D_POST_CR,
        sending_field=_D_P_CREDITORS,
    )
    ws.posting.post_dr = mv.move(
        ws.system_record.purchase_ledger_block.bl_purch_ac,
        _D_POST_DR,
        sending_field=_D_BL_PURCH_AC,
    )

    # ******************************************************************************
    # ANOMALY A-18 [purchase/pl060.cbl:L961-L962] - ``dr-pc`` and ``cr-pc`` are zeroed
    # here and then NEVER copied into the IRS posting record by the fan-out block at
    # [L982-L998], even though the maintainer flagged the concern three times in comments:
    # [L979] "and usage of DR-PC and CR-PC", [L988] "Missing usage of DR-PC for GL MUST be
    # checked in GL ????" and [L990] the same for CR-PC. The two percentage fields are
    # therefore dropped on the IRS path. Nothing is added to carry them (rule R-3).
    # Reproduced deliberately per R-4; DO NOT FIX.
    # ******************************************************************************
    # [L961-L964] move zero to dr-pc cr-pc vat-pc vat-amount. FOUR receivers.
    (
        ws.posting.dr_pc,
        ws.posting.cr_pc,
        ws.posting.vat_pc,
        ws.posting.vat_amount,
    ) = mv.move_to_all(mv.ZERO, (_D_DR_PC, _D_CR_PC, _D_VAT_PC, _D_VAT_AMOUNT))

    # ******************************************************************************
    # ANOMALY A-21 [purchase/pl060.cbl:L966-L967] - ``move vat-ac OF system-record to
    # vat-ac OF WS-Posting-Record``. ``copybooks/wssystem.cob`` and
    # ``copybooks/wspost.cob`` both declare a field spelled ``Vat-Ac`` / ``Vat-AC``, so
    # the reference is AMBIGUOUS and COBOL requires qualification. In Python the
    # qualification IS the record instance the attribute is taken from, and both sides are
    # named explicitly here for exactly that reason. Note also that the two copybooks
    # differ in CASE - ``Vat-Ac`` in the system record, ``Vat-AC`` in the posting record -
    # which is why the descriptor lookup in this module folds case.
    # Reproduced deliberately per R-4; DO NOT FIX.
    #
    # FINDING - [L966-L967] has NO terminating period of its own; the sentence is closed
    # by [L969]'s ``add``. Harmless, because neither statement is inside a conditional -
    # unlike [L1031], where the same omission in ``sl060`` is anomaly A-1. It is the
    # second missing period in this program and it is left exactly as written.
    # ******************************************************************************
    ws.posting.vat_ac = mv.move(
        ws.system_record.general_ledger_block.vat_ac,
        _D_POST_VAT_AC,
        sending_field=_D_SYS_VAT_AC,
    )

    # [L969] add oi-vat oi-c-vat to vat-amount -> ``vat-amount += oi-vat + oi-c-vat``.
    # A TWO-SOURCE ``ADD ... TO``: the receiver participates and there is ONE store.
    ws.posting.vat_amount = ar.add_to(
        ws.oi_header.filler_1.oi_vat,
        ws.oi_header.filler_1.oi_c_vat,
        receiver_value=ws.posting.vat_amount,
        receiving=_D_VAT_AMOUNT,
    )
    ws.posting.post_vat_side = mv.move_alphanumeric(  # [L970]
        "DR", _D_POST_VAT_SIDE
    )
    # ANOMALY A-21 [purchase/pl060.cbl:L971] - ``move "PL" to post-code IN
    # WS-Posting-Record``, qualified with ``IN`` rather than ``OF`` for the same collision:
    # ``copybooks/wspost.cob`` and ``copybooks/wspost-irs.cob`` both carry a post code.
    # Reproduced deliberately per R-4; DO NOT FIX.
    ws.posting.post_code = mv.move_alphanumeric("PL", _D_POST_CODE)

    # ******************************************************************************
    # [L973-L976] the control totals. ``input-*`` and ``actual-*`` are accumulated
    # IDENTICALLY, from the same two sources in the same order, so A PURCHASE BATCH
    # BALANCES BY CONSTRUCTION. Agent Action Plan section 0.6.4: "Sales and Purchase
    # batches balance by construction, so the control-total mismatch scenario is
    # General-Ledger-specific." That is why no Purchase mismatch scenario exists, and why
    # the batch gate in ``gl051`` can never reject a batch this program wrote.
    # ******************************************************************************
    ws.batch.amounts.input_gross = ar.add_to(  # [L973]
        ws.posting.post_amount,
        receiver_value=ws.batch.amounts.input_gross,
        receiving=_D_INPUT_GROSS,
    )
    ws.batch.amounts.actual_gross = ar.add_to(  # [L974]
        ws.posting.post_amount,
        receiver_value=ws.batch.amounts.actual_gross,
        receiving=_D_ACTUAL_GROSS,
    )
    ws.batch.amounts.input_vat = ar.add_to(  # [L975]
        ws.posting.vat_amount,
        receiver_value=ws.batch.amounts.input_vat,
        receiving=_D_INPUT_VAT,
    )
    ws.batch.amounts.actual_vat = ar.add_to(  # [L976]
        ws.posting.vat_amount,
        receiver_value=ws.batch.amounts.actual_vat,
        receiving=_D_ACTUAL_VAT,
    )

    # [L982] if irs-used or IRS-Both-Used. Fan-out site 3 of 7.
    if _IS_IRS_USED(
        ws.system_record.general_ledger_block.irs_instead
    ) or _IS_IRS_BOTH_USED(ws.system_record.general_ledger_block.irs_instead):
        # [L983] move WS-Post-key to WS-IRS-Post-key. A GROUP MOVE, and the two groups
        # have identical layouts - ``9(5)`` then ``9(5)`` in both
        # [copybooks/wspost.cob:L14-L16], [copybooks/wspost-irs.cob:L14-L16] - so the byte
        # copy and the leaf-by-leaf copy performed here are the same thing.
        ws.irs_posting.ws_irs_post_key.ws_irs_batch = mv.move(
            ws.posting.ws_post_key.batch,
            _D_IRS_BATCH,
            sending_field=_D_POST_BATCH,
        )
        ws.irs_posting.ws_irs_post_key.ws_irs_post_number = mv.move(
            ws.posting.ws_post_key.post_number,
            _D_IRS_POST_NUMBER,
            sending_field=_D_POST_NUMBER,
        )
        # ANOMALY A-21 [purchase/pl060.cbl:L984-L985] - the third qualified reference,
        # ``move Post-Code IN WS-Posting-Record to WS-IRS-Post-Code``, forced by the same
        # collision as [L971].
        # Reproduced deliberately per R-4; DO NOT FIX.
        ws.irs_posting.ws_irs_post_code = mv.move_alphanumeric(
            ws.posting.post_code, _D_IRS_POST_CODE, sending_field=_D_POST_CODE
        )
        ws.irs_posting.ws_irs_post_date = mv.move_alphanumeric(  # [L986]
            ws.posting.post_date, _D_IRS_POST_DATE, sending_field=_D_POST_DATE
        )
        # [L987] move Post-DR to WS-IRS-Post-DR.
        # FINDING - ``Post-DR pic 9(6)`` [copybooks/wspost.cob:L19] narrows into
        # ``WS-IRS-Post-DR pic 9(5)`` [copybooks/wspost-irs.cob:L19], so a six-digit
        # account number SILENTLY LOSES its leading digit on the IRS path. The same
        # applies to ``Post-CR`` at [L989]. The narrowing belongs to the receiving field's
        # picture and is performed by ``acas_posting.cobol.move``.
        ws.irs_posting.ws_irs_post_dr = mv.move(
            ws.posting.post_dr, _D_IRS_POST_DR, sending_field=_D_POST_DR
        )
        ws.irs_posting.ws_irs_post_cr = mv.move(  # [L989]
            ws.posting.post_cr, _D_IRS_POST_CR, sending_field=_D_POST_CR
        )
        # [L991] move Post-Amount to WS-IRS-Post-Amount. ``s9(8)v99`` into
        # ``s9(7)v99 SIGN LEADING`` [copybooks/wspost-irs.cob:L21] - one integer digit
        # narrower, and a different sign representation.
        ws.irs_posting.ws_irs_post_amount = mv.move(
            ws.posting.post_amount, _D_IRS_POST_AMOUNT, sending_field=_D_POST_AMOUNT
        )
        ws.irs_posting.ws_irs_post_legend = mv.move_alphanumeric(  # [L992]
            ws.posting.post_legend, _D_IRS_POST_LEGEND, sending_field=_D_POST_LEGEND
        )
        # ******************************************************************************
        # ANOMALY A-18 [purchase/pl060.cbl:L993-L994] - ``move 31 to WS-IRS-vat-ac-def
        # Vat-PC``, and the maintainer's own ``*> IS IT ???`` sits on the second receiver.
        # THE LITERAL IS 31 HERE AND 32 IN THE SALES TWIN [sales/sl060.cbl:L1139]: 31 is
        # the IRS default account for VAT INPUT tax and 32 for VAT OUTPUT tax, per the
        # maintainer's boxed note at [L933-L934]. The divergence is deliberate on his part
        # and is NOT harmonised. ``WS-IRS-Vat-AC-Def pic 99``
        # [copybooks/wspost-irs.cob:L23] is two digits wide, which is why 31 fits, while
        # ``Vat-PC pic 99`` [copybooks/wspost.cob:L26] receives a percentage - hence the
        # question mark.
        # Reproduced deliberately per R-4; DO NOT FIX.
        #
        # AMBIGUITY Q-VAT-PC-31 - whether storing 31 into a percentage field is observable
        # downstream, and in which column, has to be measured against the compiled program.
        # ******************************************************************************
        ws.irs_posting.ws_irs_vat_ac_def, ws.posting.vat_pc = mv.move_to_all(
            31, (_D_IRS_VAT_AC_DEF, _D_VAT_PC)
        )
        ws.irs_posting.ws_irs_post_vat_side = mv.move_alphanumeric(  # [L995]
            ws.posting.post_vat_side,
            _D_IRS_POST_VAT_SIDE,
            sending_field=_D_POST_VAT_SIDE,
        )
        ws.irs_posting.ws_irs_vat_amount = mv.move(  # [L996]
            ws.posting.vat_amount, _D_IRS_VAT_AMOUNT, sending_field=_D_VAT_AMOUNT
        )
        # [L997] perform SPL-Posting-Write -> write irs-posting-record. Note that
        # ``SPL-Posting-Rewrite`` is never performed anywhere in this program, which is
        # fortunate: the handler rejects rewrite unconditionally at entry
        # [common/acas008.cbl:L299-L307], so the published verb can never succeed
        # (anomaly A-6).
        _fh("spl_posting_write", _ctx(ws, ws.irs_posting))

    # [L999-L1000] if IRS-Both-Used or G-L. Fan-out site 4 of 7; the maintainer's comment
    # ``*> (As set in params)`` sits on the continuation line.
    if _IS_IRS_BOTH_USED(
        ws.system_record.general_ledger_block.irs_instead
    ) or _IS_G_L(ws.system_record.system_data_block.level.level_1):
        ws.posting.ws_post_rrn = mv.move(  # [L1001] move RRN to WS-Post-RRN
            ws.file_access.rrn, _D_WS_POST_RRN, sending_field=_D_RRN
        )
        _fh("gl_posting_write", _ctx(ws, ws.posting))  # [L1002] write posting-record
        ws.file_access.rrn = ar.add_to(  # [L1003] add 1 to RRN
            1, receiver_value=ws.file_access.rrn, receiving=_D_RRN
        )

    # [L1006-L1008] if items = 99 perform BL-Close / perform BL-Open.
    # The batch cap: at 99 items the batch is closed and a fresh one opened mid-run, which
    # allocates a new number through [L885-L887] and a new starting RRN through
    # [L905]/[L921]. Same shape as [sales/sl060.cbl:L1151-L1153].
    if ws.batch.items == 99:
        _bl_close(ws)
        _bl_open(ws)

    _bl_write__main_exit(ws)


def _bl_write__main_exit(ws: _Ws) -> None:
    """``main-exit.   exit section.`` [purchase/pl060.cbl:L1010]."""
    del ws


# ===========================================================================
# BL-Close     section.                               [purchase/pl060.cbl:L1013]
#
# ******************************************************************************
# THIS SECTION IS ANOMALY A-1's CONTROL CASE. See ``_bl_close`` for the full argument.
# ******************************************************************************
# ===========================================================================


def _bl_close(ws: _Ws) -> None:
    """``BL-Close section.`` [purchase/pl060.cbl:L1013-L1033] - write and close the batch.

    ******************************************************************************
    ANOMALY A-1 [purchase/pl060.cbl:L1031] - THE PERIOD IS PRESENT HERE, AND THAT IS THE
    POINT. Measured verbatim::

        1027      if       IRS-Both-Used OR G-L    *> THIS IS IN PURCHASE PL060
        1028               move     RRN  to  postings.     *> Why ?      <- period PRESENT
        1029      perform  GL-Batch-Close.
        1030      if       IRS-Used OR IRS-Both-Used
        1031               perform SPL-Posting-Close.      <- period PRESENT
        1032      if       IRS-Both-Used or G-L
        1033               perform GL-Posting-Close.       <- therefore REACHED

    Because [L1031] terminates its sentence, [L1032]'s ``if`` is a SIBLING of [L1030]'s
    rather than nested inside it, and ``GL-Posting-Close`` DOES execute when only ``G-L``
    is set. The Sales twin's equivalent line [sales/sl060.cbl:L1176] LACKS the period, so
    there [L1177]'s ``if`` nests inside [L1175]'s and ``GL-Posting-Close`` NEVER RUNS in
    pure-GL mode. That difference IS anomaly A-1, and it is demonstrable only because this
    program is written the correct way. The three sibling control cases are this one,
    [sales/sl100.cbl:L694] and [purchase/pl100.cbl:L675].

    This file is therefore written the CORRECT way, and it is NOT aligned with ``sl060``
    (rule R-3, rule R-4). Nothing here is copied from, parameterised over, or imported
    from ``sl060_invoice_posting``.
    ******************************************************************************

    FINDING - the maintainer's comment ``*> THIS IS IN PURCHASE PL060`` at [L1027] sits
    INSIDE ``pl060`` itself, where it is self-referential and says nothing. In ``sl060``
    [sales/sl060.cbl:L1172] the same comment is a genuine cross-reference. It is a
    copy-paste artefact present in both files.
    """
    _fh("gl_batch_write", _ctx(ws, ws.batch))  # [L1016] write batch-record

    # [L1017-L1026] a write failure produces DIAGNOSTICS WITH NO CONTROL TRANSFER: the
    # closes below still run, so the partial state is committed rather than rolled back.
    if ws.file_access.fs_reply != FsReply.SUCCESS:
        _LOG.error("%s%s", _PL132, ws.file_access.fs_reply)  # [L1018-L1019]
        _evaluate_message(ws)  # [L1020]
        _LOG.error("%s", ws.ws_eval_msg)  # [L1021]
        if ws.ws_calling_data.ws_caller.strip() != "xl150":  # [L1022]
            # [L1023] display PL002 / [L1024] accept ws-reply at 2430.  BOTH DROPPED -
            # the key-press instruction and the key press - and the suppression is not
            # narrated either, because the compiled program produces no such output
            # (R-4).  The branch is kept: it is the codebase's own unattended-mode test,
            # and its ABSENCE in the ``pl100`` twin [purchase/pl100.cbl:L670] is a
            # recorded structural divergence.  The substantive diagnostics are the two
            # records above.
            pass

    # [L1027] if IRS-Both-Used OR G-L. Fan-out site 5 of 7.
    if _IS_IRS_BOTH_USED(
        ws.system_record.general_ledger_block.irs_instead
    ) or _IS_G_L(ws.system_record.system_data_block.level.level_1):
        # ******************************************************************************
        # ANOMALY A-17 [purchase/pl060.cbl:L1028] - ``move RRN to postings.`` carrying the
        # maintainer's own ``*> Why ?``. Occurrence 3 of 4; the others are
        # [sales/sl060.cbl:L1173], [sales/sl100.cbl:L691] and the ``pl100`` twin. It is
        # NOT inert: this is the PRODUCER half of the cycle whose consumer is
        # [purchase/pl060.cbl:L905], which reads ``postings`` back as
        # ``add postings 1 giving batch-start``, and [purchase/pl060.cbl:L921], which
        # seeds ``RRN`` from ``batch-start``. It therefore allocates the next batch's
        # starting relative record number. Agent Action Plan section 0.6.8 requires its
        # observable effect to be measured and reproduced "regardless of whether it makes
        # sense", so it is reproduced and not optimised away.
        # Reproduced deliberately per R-4; DO NOT FIX.
        # ******************************************************************************
        ws.system_record.general_ledger_block.postings = mv.move(
            ws.file_access.rrn, _D_POSTINGS, sending_field=_D_RRN
        )

    # [L1029] perform GL-Batch-Close. UNCONDITIONAL - the period at [L1028] closed
    # [L1027]'s ``if``, so this is not inside it.
    _fh("gl_batch_close", _ctx(ws, ws.batch))

    # [L1030] if IRS-Used OR IRS-Both-Used. Fan-out site 6 of 7.
    if _IS_IRS_USED(
        ws.system_record.general_ledger_block.irs_instead
    ) or _IS_IRS_BOTH_USED(ws.system_record.general_ledger_block.irs_instead):
        # A-1 CONTROL CASE [purchase/pl060.cbl:L1031] versus [sales/sl060.cbl:L1176] - the
        # period after this ``perform`` is what makes the next ``if`` a sibling. See this
        # function's docstring for the full comparison.
        _fh("spl_posting_close", _ctx(ws, ws.irs_posting))

    # [L1032] if IRS-Both-Used or G-L. Fan-out site 7 of 7. A SIBLING of [L1030], not a
    # nested conditional - and therefore REACHED in pure-GL mode, unlike the Sales twin.
    if _IS_IRS_BOTH_USED(
        ws.system_record.general_ledger_block.irs_instead
    ) or _IS_G_L(ws.system_record.system_data_block.level.level_1):
        _fh("gl_posting_close", _ctx(ws, ws.posting))  # [L1033]

    _bl_close__main_exit(ws)


def _bl_close__main_exit(ws: _Ws) -> None:
    """``main-exit.   exit section.`` [purchase/pl060.cbl:L1035]."""
    del ws


# ===========================================================================
# Evaluate-Message        Section.                    [purchase/pl060.cbl:L1037]
#
# FINDING - the section is named ``Evaluate-Message``, NOT ``zz040-Evaluate-Message`` as
# in the Sales twin [sales/sl060.cbl:L1183]; its exit label is ``Eval-Msg-Exit.``
# [purchase/pl060.cbl:L1043] rather than a ``zz`` name; and its
# ``copy "FileStat-Msgs.cpy" replacing`` names ``MSG`` in UPPER CASE and puts it BEFORE
# ``STATUS`` [purchase/pl060.cbl:L1040-L1041], which is the reverse of ``pl055``'s order.
# All three are naming variants with no behavioural content, and all three are recorded
# rather than normalised.
# ===========================================================================


def _evaluate_message(ws: _Ws) -> None:
    """``Evaluate-Message Section.`` [purchase/pl060.cbl:L1037-L1041] - status text.

    The body is a single ``COPY ... REPLACING`` of ``FileStat-Msgs.cpy``, which expands to
    an ``EVALUATE`` over the file status and moves a human-readable string into
    ``ws-Eval-Msg``. It is PURELY DIAGNOSTIC: it writes one working-storage field, reaches
    no table, and MUST NOT alter control flow. Its three callers - [L533], [L1020] and
    [L662] - all continue regardless of what it produced.

    ``copybooks/ACAS-SQLstate-error-list.cob``, which the expansion's own dependency chain
    reaches, is absent from the frozen archive, so the text is rendered from the status
    value itself rather than from a table this module would otherwise have to fabricate.
    """
    ws.ws_eval_msg = mv.move_alphanumeric(
        f"fs-reply {int(ws.file_access.fs_reply):02d}", _D_WS_EVAL_MSG
    )
    _evaluate_message__eval_msg_exit(ws)


def _evaluate_message__eval_msg_exit(ws: _Ws) -> None:
    """``Eval-Msg-Exit.  exit section.`` [purchase/pl060.cbl:L1043].

    Spelled on one line, and named after the section rather than ``main-exit`` - the only
    exit paragraph in this program that is not called ``main-exit``.
    """
    del ws



# ===========================================================================
# The four date sections.        [purchase/pl060.cbl:L1046], [L1081], [L1116], [L1146]
#
# These four sections are repeated near-identically in nine of the twelve in-scope
# programs, and Agent Action Plan section 0.6.3 identifies them as "the one place where
# consolidation is unambiguously safe because the bodies are textually equivalent". Their
# statements therefore live in ``acas_posting/dates.py`` and the sections here are the
# per-program bindings: they select the correct variant, supply this program's wrapper, and
# store the returned ``Date-Form`` back into the system record as that module's contract
# requires.
#
# Variant selection, verified against this program's own text rather than assumed:
#   * ``zz050-Validate-Date`` [L1046-L1071] is THE PLAIN VARIANT. It has no separator
#     normalisation of any kind, unlike ``gl051``'s, which carries three extra
#     ``inspect ... replacing`` statements at [general/gl051.cbl:L1178-L1180]. The plain
#     entry point is called and the two variants are NOT consolidated here.
#   * ``zz060-Convert-Date`` [L1081-L1111] performs ``maps04`` at [L1090], not ``maps03``,
#     so the ``maps04`` wrapper is the one supplied.
#   * ``zz070-Convert-Date`` [L1116-L1141] is byte-identical in all ten carriers.
#   * ``maps04`` [L1146-L1149] is the thin wrapper around ``call "maps04" using maps03-ws``.
#
# FINDING - ``maps04 section.`` [purchase/pl060.cbl:L1146] and ``maps04-exit.``
# [purchase/pl060.cbl:L1151] AGREE, so anomaly A-22 - a wrapper section named after the
# interface copybook while its exit is named after the called program - DOES NOT OCCUR in
# this program. Its two occurrences are [general/gl070.cbl:L603-L609] and
# [general/gl051.cbl:L1273], [general/gl051.cbl:L1278].
#
# FINDING - ``zz050-Validate-Date`` is DECLARED AND NEVER PERFORMED in this program:
# ``perform zz050`` appears nowhere, and ``01 ws-Test-Date`` [purchase/pl060.cbl:L222] is
# consequently never written, only read inside the unreachable section. It is retained
# because rule R-5 requires a named function per section and because removing it would be
# a change to the program's surface.
#
# STRUCTURAL NOTE - this program declares ``01 ws-Test-Date`` [purchase/pl060.cbl:L222] as
# a separate ``01`` while ``dates.WsDateFormats`` bundles it with ``ws-swap``,
# ``ws-Conv-Date`` and ``ws-date``. ``ws.date_ws.ws_test_date`` is therefore this
# program's ``01 ws-Test-Date``; the grouping differs, the storage does not.
#
# ``GO TO`` census for these four sections - eight of this program's twenty-three sites.
# All eight transfers are executed inside the consolidated implementation, and each is
# classified here so the traceability table is complete:
#   [L1059] -> ``zz050-test-date`` [L1073]  # GO TO class 4 (work then falls to the exit)
#   [L1064] -> ``zz050-test-date`` [L1073]  # GO TO class 4
#   [L1093] -> ``zz060-Exit``      [L1113]  # GO TO class 3
#   [L1099] -> ``zz060-Exit``      [L1113]  # GO TO class 3
#   [L1104] -> ``zz060-Exit``      [L1113]  # GO TO class 3
#   [L1129] -> ``zz070-Exit``      [L1143]  # GO TO class 3
#   [L1134] -> ``zz070-Exit``      [L1143]  # GO TO class 3
# and ``maps04`` [L1146-L1152] contains none.
# ===========================================================================


def _maps04(ws: _Ws) -> None:
    """``maps04 section.`` [purchase/pl060.cbl:L1146-L1149] - the date-module wrapper.

    ``[purchase/pl060.cbl:L1149] call "maps04" using maps03-ws`` becomes a call into
    ``acas_posting.dates``, which reimplements ``common/maps04.cbl`` natively - no COBOL is
    executed, embedded or shelled out to (rule R-1).

    Direction is selected by the linkage block itself, exactly as the COBOL program does:
    a non-zero ``u-bin`` unpacks a binary day number into ``u-date``, and a zero ``u-bin``
    packs the text date in ``u-date`` into ``u-bin``. Callers here rely on both directions -
    ``zz060`` on the unpack [purchase/pl060.cbl:L1090], ``zz050`` on the pack after zeroing
    ``u-bin`` at [purchase/pl060.cbl:L1075].

    The reject behaviour is the consolidated module's: on an invalid date ``maps04`` leaves
    its output field UNTOUCHED [common/maps04.cbl:L146], [common/maps04.cbl:L154] rather
    than zeroing it, which is anomaly A-16. Nothing here pre-zeroes or post-zeroes beyond
    what [purchase/pl060.cbl:L1075] itself does.
    """
    _dates_maps04(ws.maps03_ws)  # [L1149]
    _maps04__maps04_exit(ws)


def _maps04__maps04_exit(ws: _Ws) -> None:
    """``maps04-exit.`` / ``exit section.`` [purchase/pl060.cbl:L1151-L1152].

    Named after the section, which AGREES with the section's own name - see the A-22
    FINDING above.
    """
    del ws


def _zz050_validate_date(ws: _Ws) -> None:
    """``zz050-Validate-Date section.`` [purchase/pl060.cbl:L1046-L1071].

    The maintainer's own header states the contract: input ``ws-test-date``, output
    ``u-date`` / ``ws-date`` in UK form, and ``u-bin`` non-zero when the date is valid
    [purchase/pl060.cbl:L1049-L1053].

    THE PLAIN VARIANT is called - this program has no ``inspect ... replacing`` separator
    normalisation, unlike ``gl051``'s same-named section. Never performed in this program;
    see the FINDING above.
    """
    # [L1055-L1071] plus ``zz050-test-date`` [L1073-L1076] are performed by the
    # consolidated implementation, which owns the ``Date-UK`` / ``Date-USA`` /
    # International branching and the two class 4 transfers at [L1059] and [L1064].
    def _perform_maps04(_maps03_ws: Maps03Ws) -> None:
        """``perform maps04`` [purchase/pl060.cbl:L1076] - this program's own wrapper."""
        _maps04(ws)

    # [L1056-L1057] ``if Date-Form = zero move 1 to Date-Form`` happens inside, and the
    # effective value comes back to be stored into the system record - the consolidated
    # module's documented requirement, and a real ``SYSTEM-REC`` effect.
    ws.system_record.system_data_block.date_form = _dates_zz050(
        ws.date_ws,
        ws.maps03_ws,
        ws.system_record.system_data_block.date_form,
        wrapper=_perform_maps04,
    )
    _zz050_validate_date__zz050_test_date(ws)
    _zz050_validate_date__zz050_exit(ws)


def _zz050_validate_date__zz050_test_date(ws: _Ws) -> None:
    """``zz050-test-date.`` [purchase/pl060.cbl:L1073-L1076].

    The traceability anchor for the label. Its three statements - ``move ws-date to
    u-date``, ``move zero to u-bin`` and ``perform maps04`` - are executed inside the
    consolidated implementation invoked by ``_zz050_validate_date``, which is where the
    two class 4 transfers at [purchase/pl060.cbl:L1059] and [purchase/pl060.cbl:L1064]
    land. Reached here in the same position COBOL reaches it: after the International
    reformatting falls through, and before the section exit.
    """
    del ws


def _zz050_validate_date__zz050_exit(ws: _Ws) -> None:
    """``zz050-exit.`` / ``exit     section.`` [purchase/pl060.cbl:L1078-L1079]."""
    del ws


def _zz060_convert_date(ws: _Ws) -> None:
    """``zz060-Convert-Date section.`` [purchase/pl060.cbl:L1081-L1111].

    Input ``u-bin``, output ``ws-date`` in UK, USA or International form, and ``u-date``
    and ``ws-date`` both spaces when the date is invalid
    [purchase/pl060.cbl:L1086-L1088]. Performed from ``[purchase/pl060.cbl:L447]`` to turn
    each invoice's stored binary date into text.

    This is ``zz070`` with a conversion in front of it: the input is a binary day number
    rather than a text date, so the wrapper runs FIRST [purchase/pl060.cbl:L1090]. This
    program performs ``maps04`` there, not ``maps03``, so the ``maps04`` wrapper is the one
    supplied.
    """

    def _perform_maps04(_maps03_ws: Maps03Ws) -> None:
        """``perform maps04`` [purchase/pl060.cbl:L1090] - this program's own wrapper."""
        _maps04(ws)

    # The three class 3 transfers at [L1093], [L1099] and [L1104], the spaces-on-invalid
    # rule at [L1091-L1092], the ``Date-Form`` defaulting at [L1096-L1097] and the
    # International reformatting at [L1108-L1111] are all inside the consolidated
    # implementation.
    ws.system_record.system_data_block.date_form = _dates_zz060(
        ws.date_ws,
        ws.maps03_ws,
        ws.system_record.system_data_block.date_form,
        wrapper=_perform_maps04,
    )
    _zz060_convert_date__zz060_exit(ws)


def _zz060_convert_date__zz060_exit(ws: _Ws) -> None:
    """``zz060-Exit.`` / ``exit     section.`` [purchase/pl060.cbl:L1113-L1114].

    The target of three class 3 transfers - [purchase/pl060.cbl:L1093],
    [purchase/pl060.cbl:L1099] and [purchase/pl060.cbl:L1104] - and of the fall-through
    from [purchase/pl060.cbl:L1111].
    """
    del ws


def _zz070_convert_date(ws: _Ws) -> None:
    """``zz070-Convert-Date section.`` [purchase/pl060.cbl:L1116-L1141].

    Input ``to-day``, output ``ws-date`` in UK, USA or International form
    [purchase/pl060.cbl:L1121-L1122]. Performed once from ``[purchase/pl060.cbl:L358]``
    to render the run-date banner.

    ``to-day pic x(10)`` [purchase/pl060.cbl:L338] is the SECOND of the two observables
    ``acas_posting/clock.py`` pins, and it arrives purely through linkage. This section
    reads no clock (rule R-6), and neither does the consolidated implementation.

    Byte-identical in all ten carrying programs, so the consolidated entry point takes no
    variant selector - only the two class 3 transfers at [purchase/pl060.cbl:L1129] and
    [purchase/pl060.cbl:L1134] and the International reformatting at
    [purchase/pl060.cbl:L1138-L1141] live inside it.
    """
    ws.system_record.system_data_block.date_form = _dates_zz070(
        ws.date_ws, ws.to_day, ws.system_record.system_data_block.date_form
    )
    _zz070_convert_date__zz070_exit(ws)


def _zz070_convert_date__zz070_exit(ws: _Ws) -> None:
    """``zz070-Exit.`` / ``exit     section.`` [purchase/pl060.cbl:L1143-L1144].

    The target of two class 3 transfers - [purchase/pl060.cbl:L1129] and
    [purchase/pl060.cbl:L1134] - and of the fall-through from
    [purchase/pl060.cbl:L1141].
    """
    del ws


# ---------------------------------------------------------------------------
# ``copy "Proc-ACAS-FH-Calls.cob".`` [purchase/pl060.cbl:L1154]
#
# The copybook's 1449 lines expand HERE, at the very end of the procedure division, and
# supply the twenty-one entity facades whose verbs this program performs. In Python they
# are ``acas_posting.dal.facade``, imported at the top of this module and reached through
# ``_fh``. The ENTITY-named vocabulary is the one in force, and the reply is tested INLINE
# by each caller - this copybook has no per-handler error-check paragraph at all, unlike
# ``copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob``, whose handler-named aliases are therefore
# NOT used anywhere in this module.
#
# OMISSION - unlike ``gl072`` [general/gl072.cbl:L134-L153] and ``gl080``, this program
# declares NO block of unused facade stubs, so there is no representation-only omission to
# record on that account.
# ---------------------------------------------------------------------------



# ###########################################################################
# --- traceability ---
#
# Rule R-5 requires that every program map to a module, every paragraph to a function and
# every field to a data-dictionary entry, and that the mapping be RECORDED rather than left
# implicit. This footer is that record for ``purchase/pl060.cbl`` (1155 lines) ->
# ``acas_posting/programs/pl060_order_posting.py``. Agent Action Plan section 0.4.2 lists
# this program's SECTION heads only; every PARAGRAPH below is a measured addition taken
# from the frozen source.
#
# ===========================================================================
# 1. PROGRAM -> MODULE
# ===========================================================================
#
#   purchase/pl060.cbl                 -> acas_posting/programs/pl060_order_posting.py
#   procedure division using ...       -> run(ws_calling_data, system_record,
#     [purchase/pl060.cbl:L340-L344]        system_record_4, to_day, file_defs)
#   77 prog-name value "PL060 (3.3.01)"-> _PROG_NAME  [purchase/pl060.cbl:L139]
#   public API                         -> __all__ == ("run",); every other module-level
#                                         name is ``_``-prefixed, so callers cannot reach
#                                         into the program exactly as a COBOL ``CALL``
#                                         cannot (Agent Action Plan section 0.3.3)
#
# ===========================================================================
# 2. SECTION / PARAGRAPH -> FUNCTION  (42 labels, all present)
# ===========================================================================
#
# Names are SECTION-QUALIFIED because paragraph labels are not unique in this program:
# ``main-exit.`` occurs TEN times, ``main-end.`` twice and ``end-loop.`` twice.
#
#   L347   init01 section.                    _init01
#   L362   acpt-xrply.                        _init01__acpt_xrply        (body commented out)
#   L424   loop.                              _init01__loop
#   L545   main-end.                          _init01__main_end
#   L585   end-loop.                          _init01__end_loop
#   L602   end-loop-end.                      _init01__end_loop_end
#   L650   exit-prog.                         _init01__exit_prog
#   L653   cr-swop      section.              _cr_swop
#   L688   main-exit.   (1 of 10)             _cr_swop__main_exit
#   L691   new-heading  section.              _new_heading
#   L714   main-exit.   (2 of 10)             _new_heading__main_exit
#   L717   headings     section.              _headings
#   L738   main-exit.   (3 of 10)             _headings__main_exit
#   L740   purch-comp   section.              _purch_comp
#   L753   main-exit.   (4 of 10)             _purch_comp__main_exit
#   L755   credit-comp  section.              _credit_comp
#   L768   main-exit.   (5 of 10)             _credit_comp__main_exit
#   L770   cr-notes     section.              _cr_notes
#   L786   read-loop.                         _cr_notes__read_loop
#   L809   end-loop.                          _cr_notes__end_loop
#   L823   main-end.                          _cr_notes__main_end
#   L828   main-exit.   (6 of 10)             _cr_notes__main_exit
#   L831   apportion    section.              _apportion
#   L867   main-rewrite.                      _apportion__main_rewrite
#   L875   main-exit.   (7 of 10)             _apportion__main_exit
#   L877   BL-Open      section.              _bl_open
#   L923   main-exit.   (8 of 10)             _bl_open__main_exit
#   L926   BL-Write     section.              _bl_write
#   L1010  main-exit.   (9 of 10)             _bl_write__main_exit
#   L1013  BL-Close     section.              _bl_close
#   L1035  main-exit.   (10 of 10)            _bl_close__main_exit
#   L1037  Evaluate-Message        Section.   _evaluate_message
#   L1043  Eval-Msg-Exit.                     _evaluate_message__eval_msg_exit
#   L1046  zz050-Validate-Date     section.   _zz050_validate_date       (never performed)
#   L1073  zz050-test-date.                   _zz050_validate_date__zz050_test_date
#   L1078  zz050-exit.                        _zz050_validate_date__zz050_exit
#   L1081  zz060-Convert-Date      section.   _zz060_convert_date
#   L1113  zz060-Exit.                        _zz060_convert_date__zz060_exit
#   L1116  zz070-Convert-Date      section.   _zz070_convert_date
#   L1143  zz070-Exit.                        _zz070_convert_date__zz070_exit
#   L1146  maps04       section.              _maps04
#   L1151  maps04-exit.                       _maps04__maps04_exit
#
# Supporting functions, which correspond to no COBOL label and are named so that this is
# obvious: ``_ws_descriptor``, ``_desc``, ``_fh``, ``_status_pair``, ``_oi_leaf``,
# ``_oi_get``, ``_oi_set``, ``_new_oi_header``, ``_group_move_oi``,
# ``_initialize_with_filler``, ``_oi_supplier_image``, ``_move_supplier_group``,
# ``_is_purchase_missing``, ``_is_file_28_exists``, ``_is_file_28_not_exists``, ``_ctx``,
# ``_otm4_status``, ``_add_to_pturnover_q``, ``_cbl_check_file_exist``,
# ``_cbl_delete_file``.
#
# ``PERFORM ... THRU`` DOES NOT OCCUR in this program. The four in-scope sites repo-wide
# are [general/gl072.cbl:L300], [general/gl072.cbl:L304], [sales/sl100.cbl:L344] and
# [purchase/pl100.cbl:L336].
#
# ===========================================================================
# 3. ``GO TO`` CENSUS - 23 LIVE SITES, EACH CLASSIFIED
# ===========================================================================
#
# 25 textual ``go to`` occurrences; [L368] and [L370] are inside ``acpt-xrply``'s
# fully commented-out body, leaving 23 live. Classified BY SHAPE, not by matching a label
# list.
#
#   CLASS 1 - loop-back -> ``continue``                              (6 sites)
#     L543 -> loop      L424      | L595 -> end-loop  L585 | L600 -> end-loop  L585
#     L795 -> read-loop L786      | L800 -> read-loop L786 | L807 -> read-loop L786
#
#   CLASS 2 - forward terminator -> ``break`` PLUS the post-loop block (6 sites)
#     L426 -> main-end      L545  (post-loop block: _init01__main_end, L548-L583)
#     L590 -> end-loop-end  L602  (post-loop block: _init01__end_loop_end, L605-L641)
#     L780 -> end-loop      L809  (skips [L781-L784] entirely - see the FINDING)
#     L791 -> end-loop      L809
#     L798 -> end-loop      L809
#     L814 -> main-end      L823  (post-loop block: the [L826] header restore)
#     Agent Action Plan section 0.6.3: "the transformation is ``break`` PLUS faithful
#     placement of that work after the loop, not ``break`` alone. Mis-splitting here would
#     silently drop end-of-run processing." Here the post-loop work is enormous - the
#     closes, the three total blocks, ``BL-Close``, the OTM5 reopen and the ``work-b``
#     reset at [L548-L583]; the OTM4 TRUNCATION, PERIOD TOTAL 8 and the spool-out at
#     [L605-L641]; and ``cr-notes``' header restore at [L826]. Every one of those carries a
#     real database effect.
#
#   CLASS 3 - section / paragraph exit -> ``return``                 (6 sites)
#     L842  -> apportion's main-exit L875   (the ONLY exit that leaves PUITM5-REC unwritten)
#     L1093 -> zz060-Exit L1113 | L1099 -> zz060-Exit L1113 | L1104 -> zz060-Exit L1113
#     L1129 -> zz070-Exit L1143 | L1134 -> zz070-Exit L1143
#
#   CLASS 4 - sibling re-dispatch -> named call + explicit transfer  (3 sites)
#     L839  -> main-rewrite    L867  (performs the rewrite, then falls into main-exit L875)
#     L1059 -> zz050-test-date L1073 (performs three statements, then falls into the exit)
#     L1064 -> zz050-test-date L1073
#
#   THE TWO A-NEW-1 SITES                                             (2 sites)
#     L820 -> main-end  L823  # GO TO class 2 (UNCONDITIONAL - A-NEW-1)
#     L821 -> read-loop L786  # UNREACHABLE (A-NEW-1)
#
#   6 + 6 + 6 + 3 + 2 = 23.
#
# ===========================================================================
# 4. FALL-THROUGHS, RECORDED EXPLICITLY
# ===========================================================================
#
#   L543 area  loop -> (via [L426] only) main-end                  explicit break
#   L583 -> L585   main-end falls into end-loop                    _init01 calls both in order
#   L600 area  end-loop -> (via [L590] only) end-loop-end          explicit break
#   L641 -> L650   end-loop-end falls into exit-prog               _init01 calls both in order
#   L686 -> L688   cr-swop falls into main-exit
#   L712 -> L714   new-heading falls into main-exit
#   L736 -> L738   headings falls into main-exit
#   L751 -> L753   purch-comp falls into main-exit
#   L766 -> L768   credit-comp falls into main-exit
#   L784 -> L786   cr-notes falls into read-loop
#   L807 -> L809   read-loop falls out of the bottom into end-loop  (the loop's normal exit,
#                                                                    NOT a GO TO)
#   L826 -> L828   cr-notes' main-end falls into main-exit
#   L865 -> L867   apportion falls into main-rewrite
#   L871 -> L875   main-rewrite falls into main-exit
#   L921 -> L923   BL-Open falls into main-exit
#   L1008 -> L1010 BL-Write falls into main-exit
#   L1033 -> L1035 BL-Close falls into main-exit
#   L1071 -> L1073 zz050 falls into zz050-test-date
#   L1076 -> L1078 zz050-test-date falls into zz050-exit
#   L1111 -> L1113 zz060 falls into zz060-Exit
#   L1141 -> L1143 zz070 falls into zz070-Exit
#   L1149 -> L1151 maps04 falls into maps04-exit
#
# ===========================================================================
# 5. THE ELEVEN ANOMALY REPRODUCTIONS  (rule R-4: a defect reproduced is correct)
# ===========================================================================
#
#   A-1     [L1031]  CONTROL CASE. The period IS present, so [L1032]'s ``if`` is a SIBLING
#                    and ``GL-Posting-Close`` [L1033] IS reached in pure-GL mode. The
#                    defective sibling is [sales/sl060.cbl:L1176], which lacks it. The
#                    other two control cases are [sales/sl100.cbl:L694] and
#                    [purchase/pl100.cbl:L675].            -> _bl_close
#   A-8     [L200], [L213], [L750], [L751]  DOUBLE TRUNCATION: ``work-2`` is
#                    ``s9(14) comp-3`` with ZERO scale and ``work-goods`` is ``s9(7)v99``,
#                    so the pence go on accumulation and the remainder goes on the divide
#                    into the ``binary-long`` ``purch-average``
#                    [copybooks/wspl.cob:L38].             -> _purch_comp, _credit_comp
#   A-9     [L755-L766]  ``credit-comp`` has NO ``add 1 to purch-activety`` anywhere, and
#                    its extra guard suppresses the computation while the accumulator is
#                    zero, so THE FIRST PURCHASE CREDIT NOTE FOR A SUPPLIER IS DROPPED.
#                    Mirrors [sales/sl060.cbl:L835-L843].  -> _credit_comp
#   A-10    [L743], [L764]  two of the four mutually inconsistent guards on one idiom; the
#                    others are [sales/sl060.cbl:L819], [sales/sl060.cbl:L835] and
#                    [purchase/pl100.cbl:L497].            -> _purch_comp, _credit_comp
#   A-17    [L1028]  ``move RRN to postings.  *> Why ?`` - the producer of the cycle
#                    [L1028] -> [L905] -> [L921] that allocates the next batch's starting
#                    RRN. Occurrence 3 of 4.               -> _bl_close, _bl_open
#   A-18    [L961-L962], [L993-L994]  ``dr-pc`` and ``cr-pc`` are zeroed and never carried
#                    into the IRS posting record; and ``31`` is moved here where ``sl060``
#                    moves ``32`` [sales/sl060.cbl:L1139]. -> _bl_write
#   A-21    [L966-L967], [L971], [L984-L985]  three qualified references forced by
#                    field-name collisions across ``wspost.cob``, ``wspost-irs.cob`` and
#                    ``wssystem.cob``.                     -> _bl_write
#   A-NEW-1 [L819-L821]  UNREGISTERED, and the highest-value discovery in this file. A lost
#                    ``invalid key`` conditional makes [L820] unconditional and [L821]
#                    dead, so THE CREDIT-NOTE SECOND APPORTIONMENT PASS NEVER EXECUTES.
#                    ``sl060``'s equivalent [sales/sl060.cbl:L908] DOES execute.
#                                                          -> _cr_notes__end_loop
#   A-NEW-2 [L630-L635]  UNREGISTERED. The ``write`` sits in the ``else`` arm only, so
#                    ``PL133`` is moved into ``print-record`` and never written in
#                    ``FS-Cobol-Files-Used`` mode. Mirrors
#                    [sales/sl060.cbl:L702-L707].          -> _init01__end_loop_end
#   A-NEW-3 [L450], [L467-L468]  UNREGISTERED. ``a`` is set from ``oi-type`` with no range
#                    check and used to subscript ``total-group occurs 3``.
#                                                          -> _init01__loop
#   A-NEW-4 [L484], [L490], [L497]  UNREGISTERED. ``current-quarter`` subscripts
#                    ``pturnover-q occurs 4`` unchecked, exactly as
#                    [general/gl080.cbl:L345] (anomaly A-2) does.
#                                                          -> _add_to_pturnover_q
#
# ===========================================================================
# 6. FINDINGS - observations that are not registered anomalies
# ===========================================================================
#
#   * [L1027] the maintainer's ``*> THIS IS IN PURCHASE PL060`` sits INSIDE ``pl060``,
#     where it is self-referential and says nothing; in ``sl060`` [sales/sl060.cbl:L1172]
#     the same comment is a genuine cross-reference. A copy-paste artefact in both files.
#   * [L362-L371] ``acpt-xrply``'s body is ENTIRELY COMMENTED OUT, so this program has NO
#     run-confirm gate where ``sl100`` [sales/sl100.cbl:L310-L319] still has a live one.
#     The two commented ``go to`` statements at [L368] and [L370] are why the textual
#     census is 25 and the live census 23.
#   * [L589] tests ``FS-Reply not = zero`` while [L790] tests ``FS-Reply = 10`` - two
#     different end-of-file tests on the SAME FILE in the SAME PROGRAM, and not equivalent.
#   * [L526] carries the maintainer's ``*> 21`` and [L779] his ``*> 21 ?`` - both name a
#     status the test does not actually compare against.
#   * [L806] spells the relation ``not equal`` in words where every sibling uses ``not =``.
#   * [L691] and [L717] are NEAR-DUPLICATE sections differing only in the ``line-1a`` write
#     and in ``line-cnt`` 6 versus 5.
#   * this program has NO ``analise-deductions`` section and no ``ws-deduction`` /
#     ``total-deduct`` / ``total-mov-ded`` fields, unlike [sales/sl060.cbl:L224-L226] and
#     [sales/sl060.cbl:L976] - which is exactly WHY it writes ONE period total [L628] where
#     ``sl060`` writes two, [sales/sl060.cbl:L641] and [sales/sl060.cbl:L700].
#   * [L651] the verb is ``exit program.``, not ``goback``.
#   * [L966-L967] has no terminating period of its own; [L969]'s ``add`` closes the
#     sentence. The second missing period in this program, and harmless because neither
#     statement is inside a conditional - unlike [L1031], where the same omission in
#     ``sl060`` IS anomaly A-1.
#   * [L375] writes ``Oi-5-Flag``, which is declared in the SALES ledger block of
#     ``copybooks/wssystem.cob`` - a cross-ledger write from a Purchase program.
#   * [L987], [L989] ``Post-DR`` / ``Post-CR`` are ``pic 9(6)``
#     [copybooks/wspost.cob:L19], [copybooks/wspost.cob:L21] and narrow into ``pic 9(5)``
#     [copybooks/wspost-irs.cob:L19-L20], so a six-digit account number silently loses its
#     leading digit on the IRS path. [L991] and [L996] narrow ``s9(8)v99`` into
#     ``s9(7)v99 SIGN LEADING`` the same way.
#   * [L503-L504] and [L515-L516] both store 1 into ``purch-status`` for a missing
#     supplier, because [L438]'s ``INITIALIZE`` leaves the record ``Supplier-dead``
#     (``88 Supplier-dead value 0`` [copybooks/wspl.cob:L20]) and [L503] then promotes it.
#     A redundant double store, preserved.
#   * [L190] ``03 save-level-1`` is declared and NEVER written, because both halves of the
#     BYPASS block - [L400-L401] and [L646] - are commented out.
#   * [L881-L883] a commented-out ``close`` / ``open output`` fallback for the batch file,
#     of exactly the shape [L909-L912] and [L916-L919] still use live. The batch file has
#     no create-on-absence recovery; the two posting files do.
#   * [L1046] ``zz050-Validate-Date`` is DECLARED AND NEVER PERFORMED, so
#     ``01 ws-Test-Date`` [L222] is never written either.
#   * [L1146] / [L1151] ``maps04`` and ``maps04-exit`` AGREE, so anomaly A-22 does NOT
#     occur here. Its occurrences are [general/gl070.cbl:L603-L609] and
#     [general/gl051.cbl:L1273], [general/gl051.cbl:L1278].
#   * [L1037] the section is named ``Evaluate-Message``, not ``zz040-Evaluate-Message`` as
#     in [sales/sl060.cbl:L1183], and its ``COPY ... REPLACING`` names ``MSG`` in upper
#     case and before ``STATUS`` - the reverse of ``pl055``'s order.
#   * [L780] the failure path into ``end-loop`` skips [L781]'s ``work-b`` reset and
#     [L784]'s ``subtract si-paid from work-1``, yet ``end-loop`` still issues the second
#     START at [L819] whenever ``work-1`` is non-zero.
#   * [L864-L865] ``apportion`` carries a uniform post-check that ``sl060`` does not have
#     at all; ``sl060`` expresses its asymmetry through an inline ``Clear-Invoice-Deduct``
#     perform in two of three branches [sales/sl060.cbl:L935-L955].
#   * THERE ARE ZERO ``ROUNDED`` SITES in this program. The five in the whole migration are
#     [general/gl051.cbl:L791], [general/gl051.cbl:L796], [general/gl080.cbl:L328],
#     [irs/irs030.cbl:L1551] and [irs/irs030.cbl:L1562]. Every store here truncates toward
#     zero, which is COBOL's default, so no store here requests the ``ROUNDED`` phrase.
#   * THERE IS NO FACADE STUB BLOCK, unlike [general/gl072.cbl:L134-L153] and the
#     equivalent in ``gl080``.
#
# ===========================================================================
# 7. AMBIGUITIES REQUIRING ORACLE ARBITRATION (rule R-6)
# ===========================================================================
#
#   Q-FACADE-SHAPE            the exact parameter shape each facade verb declares
#   Q-FILE-DEFS-SHAPE         ``File-Defs`` versus ``File-Defs-A`` at the handler boundary
#   Q-QUARTER-SUBSCRIPT       the effect of a ``current-quarter`` outside 1..4 (A-NEW-4),
#                             and of an ``oi-type`` outside 1..3 on ``(a)`` (A-NEW-3)
#   Q-PURCH-AVERAGE-SIGN      the value stored when the bridge narrows a signed
#                             ``binary-long`` into an unsigned host variable and column,
#                             as anomaly A-11 documents for [common/salesMT.cbl:L305-L312]
#   Q-CR-NOTES-SECOND-PASS    the ``PUITM5-REC`` state A-NEW-1's dead second pass leaves,
#                             versus ``SAITM3-REC`` under the same seed
#   Q-A17-POSTINGS-EFFECT     the stored value of ``postings`` once ``RRN`` has advanced
#                             past its picture ([L1028] -> [L905] -> [L921])
#   Q-VAT-PC-31               whether storing 31 into a percentage field [L994] is
#                             observable downstream, and in which column
#   Q-OTM4-HANDOFF            RESOLVED, and recorded here rather than removed. The OTM4
#                             sequence ``pl055`` writes and this program reads lives in
#                             ``acas_posting/workfiles.py`` as the shared
#                             ``OpenItemWorkFile``, which publishes the ``EXTEND`` mode the
#                             producer needs and the ``read_next`` this program needs, and
#                             the ROUTE threads ONE instance from the ``pl055`` dispatch to
#                             the ``pl060`` dispatch - which is what the two programs naming
#                             the same ``assign file-28`` achieves in COBOL. It arrives as
#                             the keyword-only ``open_item_file_4``, leaving the frozen
#                             five-entry ``PROCEDURE DIVISION USING`` untouched.
#   and, from the body: the exact ``post-date`` text the century-dropping reference
#   modification at [L937-L938] produces; whether any scenario sets
#   ``FS-Cobol-Files-Used``; and the disposition of the OTM5 write failure at [L526].
#
# ===========================================================================
# 8. STRUCTURAL NOTES
# ===========================================================================
#
#   OTM4 - ``open-item-file-4``. ``copybooks/seloi4.cob`` declares it
#   ``assign file-28 / access sequential / status fs-reply`` with NO ``organization``
#   clause, and ``copybooks/fdoi4.cob`` gives it a single record
#   ``01 open-item-record-4 pic x(113)``. Because ``ASSIGN`` names a FILE and a file
#   outlives the program that opened it, the sequence is the SHARED
#   ``acas_posting.workfiles.OpenItemWorkFile`` that ``pl055`` wrote and the ROUTE hands on.
#   It arrives as the KEYWORD-ONLY ``open_item_file_4`` - NOT as a sixth positional
#   argument, because the frozen ``PROCEDURE DIVISION USING`` has exactly five entries -
#   which is the same device the three General Ledger phases use for their work files.
#   Neither ``copybooks/plwsoi.cob`` nor ``copybooks/plwssoi.cob`` has a module under
#   ``acas_posting/records/``, and none is added: no new file is created in either folder,
#   both of which the Agent Action Plan closes at a fixed file list
#   (sections 0.4.1.2, 0.4.4).
#   Semantics, matching the COBOL verbs exactly: ``open input`` [L421] positions at the
#   start; ``read ... at end`` [L425] yields the EOF branch; ``open output`` [L605]
#   TRUNCATES; ``close`` [L548], [L606] keeps the records. Because ``seloi4.cob`` names
#   ``fs-reply`` - the SAME field ``copybooks/wsfnctn.cob`` declares for the facade - every
#   OTM4 verb here is followed by ``_otm4_status``, which mirrors the work file's status
#   into ``File-Access``. The sequence is in-memory only and reaches NO table, so it appears
#   in no dump.
#
#   OI-Header versus WS-OTM5-Record. ``copybooks/plwsoi5B.cob:L19-L20`` COMMENTS OUT the
#   ``copy ... replacing`` that would have made ``OI-Header`` redefine ``WS-OTM5-Record``,
#   so in this program they are separate storage - which is why [L521], [L685] and [L870]
#   have to group-move at all. ``oi5-supplier`` / ``oi5-invoice`` and ``OI-Supplier`` /
#   ``OI-Invoice`` name the same bytes, as the generated dictionary states independently
#   (``PUITM5-REC.OI5-SUPPLIER``, ``PUITM5-REC.OI5-INVOICE``), so one ``OiHeader`` buffer
#   holds the record area and the four ``oi5-*`` stores [L775-L776], [L816-L817] go through
#   its ``OI-Header`` view.
#
#   si-header. ``copybooks/plwssoi.cob`` is byte-for-byte ``copybooks/plwsoi.cob`` with
#   ``si-`` prefixes and different level numbers, so it is a second ``OiHeader`` buffer.
#
#   total-group. ``03 total-group occurs 3 comp-3`` [L214-L216] is a table of PAIRS, held
#   as two three-element lists with the one-based subscript stated at each use.
#
#   ws-Test-Date. Declared as a separate ``01`` at [L222] while ``dates.WsDateFormats``
#   bundles it with ``ws-swap``, ``ws-Conv-Date`` and ``ws-date``. The grouping differs; the
#   storage does not.
#
#   WORKING-STORAGE and the dictionary. NONE of ``01 ws-data``'s fields [L189-L220] appear
#   in ``data_dictionary/acas_posting_dictionary.json`` - they are program-local and reach
#   no table - so each carries a ``source_locator`` pointing at its declaration line
#   instead of a ``dictionary_key``. Every field that DOES reach a table takes its
#   descriptor from the generated dictionary through ``_desc``.
#
# ===========================================================================
# 9. OMISSIONS - recorded so that a reader comparing the two files does not
#    conclude something was lost (Agent Action Plan section 0.4.3, rule R-5)
# ===========================================================================
#
#   * [L638] ``call "SYSTEM" using Print-Report`` - the spool-out path that hands a report
#     file to the operating system. Agent Action Plan section 0.1.1 excludes it explicitly.
#     OMITTED ENTIRELY.
#   * the FOUR non-migratable library calls, all gated on ``FS-Cobol-Files-Used``
#     (``88 FS-Cobol-Files-Used value zero`` [copybooks/wssystem.cob:L113], against
#     ``88 FS-RDBMS-Used value 1`` [copybooks/wssystem.cob:L116], so all four are
#     unreachable in the RDBMS configuration this migration targets):
#         [L377] CBL_CHECK_FILE_EXIST File-29 | [L388] CBL_CHECK_FILE_EXIST File-28
#         [L610] CBL_CHECK_FILE_EXIST File-28 | [L641] CBL_DELETE_FILE      File-28
#     For each, the ``if FS-Cobol-Files-Used`` test is reproduced through
#     ``condition_names`` so the decision stays data-driven, and the probe itself raises an
#     explicitly-typed error naming the routine and stating that rule R-1 forbids invoking
#     COBOL. Nothing is silently skipped, stubbed as a no-op, or emulated on the filesystem.
#     NOTE that the FIRST gate's body ALSO contains facade verbs -
#     ``OTM5-Open-Output`` and ``OTM5-Close`` at [L380-L381] - and THOSE ARE REPRODUCED;
#     only the existence probe is not.
#   * the ENTIRE print file: ``open output print-file`` [L410], ``close print-file``
#     [L637], and every ``write print-record`` - [L539], [L559], [L565], [L571], [L626],
#     [L635], [L676], [L699-L711], [L725-L735]; all of ``line-1`` .. ``line-8`` and
#     ``line-1a`` / ``line-4a``; ``l3-page``, ``usera`` as a print item,
#     ``Print-Spool-Name`` / ``PSN``; and ``copy "selprint"`` [L126], ``copy "fdprint"``
#     [L135] and ``copy "print-spool-command"`` [L140]. ``new-heading`` and ``headings``
#     REMAIN as named functions (rule R-5) and still maintain ``j`` and ``line-cnt``,
#     because ``line-cnt`` is tested at [L541], [L556], [L619] and [L679].
#   * ``copy "envdiv.cob"`` [L118] and ``set ENVIRONMENT`` [L352-L353] - representation
#     only.
#   * ``display ... at`` -> A LOG RECORD, BUT NOT ALL OF IT. Agent Action Plan section
#     0.3.4 converts a DIAGNOSTIC display, which "must not alter control flow and must not
#     appear in any table dump" - and no record this module emits does either.
#     CONVERTED: [L356-L357] the banner and title, [L412-L413] the wait and phase-1
#     labels, [L527, L531-L534] the OTM5 write-failure message with its file status and
#     the decoded status name, [L583] the phase-2 label, [L659] the substantive half of
#     ``PL131``, and [L1018-L1021] the batch-write failure with its status and name.
#     NOT CONVERTED, each for a stated reason:
#       - [L535] and [L1023] - ``PL002``, PURE ACKNOWLEDGEMENT PROMPTS standing
#         immediately before the ``accept``s below. The whole of the literal is the
#         key-press instruction, so no substantive half is lost. ``PL131`` [L659] is the
#         one MIXED literal and its diagnostic half IS kept, split at ``_PL131_NOTICE``.
#       - [L359] - ``display ws-date``. THE POSTING DATE IS BUSINESS DATA, which the
#         safe-event schema in ``acas_posting/dal/status.py`` excludes from a record
#         (CWE-532); it is a command-line INPUT that ``clock.py`` pins.
#       - [L528] and [L530] - ``oi5-supplier`` and ``l5-nos``. RECORD KEYS, excluded by
#         the same schema at any level, DEBUG included; their renderers were eager log
#         arguments besides, so removing them also removes a failure path a diagnostic
#         must not add.
#       - [L355], [L372] and [L411] - ``display " "`` / ``display space``. Screen erasure:
#         the operand is a space, so there is no diagnostic content to convert.
#     ``ws-Eval-Msg`` IS carried, because ``Evaluate-Message`` fills it only from the
#     static table ``copybooks/FileStat-Msgs.cpy`` keyed on ``fs-reply`` - a fixed status
#     NAME, not driver text and not a business value.
#   * ``accept ws-reply`` at [L537], [L661] and [L1024] - acknowledgement pauses, DROPPED;
#     the ``WS-Caller not = "xl150"`` branches around them are PRESERVED, because they are
#     branches and not pauses.
#   * the message literals [L250-L257]. ``PL130``, ``PL132`` and the diagnostic half of
#     ``PL131`` are kept as log text. ``PL002`` is DECLARED AND DELIBERATELY NEVER
#     REFERENCED - the acknowledgement prompt above - as are ``PL133`` and ``PL133T``,
#     which the frozen program never ``display``s at all: [L632] and [L634] ``move`` them
#     into ``print-record``, which is report content and out of scope. ``PL003`` is
#     declared and never referenced BY THE FROZEN PROGRAM ITSELF. Every member stays
#     declared because rule R-5 maps the whole ``01 Error-Messages`` group.
#   * [L134-L153]-style facade stub block: NONE EXISTS in this program, so there is nothing
#     to omit on that account - stated because ``gl072`` and ``gl080`` do have one.
#   * ``01 total-lits`` / ``ws-lits`` [L261-L265] and ``01 line-*`` [L268 onward] are print
#     furniture. The three captions are consequently DECLARED AND DELIBERATELY
#     UNREFERENCED: their only reader was the printed totals block [L551-L571], which is
#     report content. THE THREE ``add ... giving`` STATEMENTS IN THAT BLOCK ARE STILL
#     PERFORMED - unconditionally, as the frozen program performs them - so the arithmetic
#     census stays complete and the print field's width is still honoured; only their
#     results are neither bound nor logged.
#
# ===========================================================================
# 10. FIELD -> DICTIONARY  (rule R-5, third mapping)
# ===========================================================================
#
# Every ``FieldDescriptor`` in this module carries either a ``dictionary_key``, when the
# field reaches a table and the generated dictionary therefore owns its metadata, or a
# ``source_locator`` of the form ``<path>:L<n>`` when it is program-local. The record-layer
# descriptors are obtained through ``_desc``, which resolves against the three conventions
# the ``acas_posting/records/`` modules use, so no picture clause is transcribed by hand
# for any field that reaches storage. The tables and columns this program writes are listed
# in the module docstring.
# ###########################################################################
