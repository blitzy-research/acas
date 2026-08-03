r"""The single doorway between the posting programs and the file handlers.

This module is the twenty-second and last module of ``acas_posting.dal`` and the
only one permitted to know that all twenty handler modules exist. Every other
module in the package is forbidden from importing a sibling ``dal.acas*``, and
``programs/*`` may import this module but never a handler module directly. Agent
Action Plan section 0.4.3 fixes the layering::

    programs/*.py     may import  records, dal.facade, cobol.*, dates, workfiles
                      never       cli, dal.acas* directly, harness
    dal/acas*.py      may import  dal.connection, dal.status, dal.cursor_state,
                                  one records module
                      never       programs, cli, other dal.acas*, harness

So this file is the seam. Everything above it names business intent; everything
below it owns SQL. Nothing here owns a single statement.

Agent Action Plan section 0.1.2 states what collapses here, verbatim:

    "In Python this becomes **two layers rather than four**: a facade module
    publishing the verb vocabulary, and one module per handler that owns the SQL
    for its table."


THE HEADLINE: DUAL ALIASING IS A BEHAVIOURAL DIFFERENCE, NOT A NAMING ONE
=========================================================================
Two COBOL copybooks publish two vocabularies over the same handlers. Agent
Action Plan section 0.3.3, verbatim:

    "**Facade with dual aliasing.** One implementation, two published name sets:
    the entity-named vocabulary from [copybooks/Proc-ACAS-FH-Calls.cob] and the
    handler-named vocabulary from [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob].
    This resolves what would otherwise be a genuine tension - traceability
    demands that a reader following either COBOL convention find a
    correspondingly named Python function, while sane engineering demands the
    logic exist once."

Agent Action Plan section 0.6.5, verbatim - the sentence that defines this
module's hardest requirement:

    "The IRS facade convention wraps each handler call in a per-handler error
    check that displays a handler-specific message and, on an unrecoverable open
    failure, returns from the program outright
    [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L355-L364]. The General/Sales/
    Purchase convention has **no such paragraph at all** - its callers test the
    reply inline. The Python facade must therefore **behave differently
    depending on which alias set the caller used**, which is a behavioral
    difference and not merely a naming one."

An alias here is therefore NOT ``entity_verb = handler_verb``. The two
vocabularies are two thin wrappers over one core:

* the entity-named functions apply their paragraph's state moves, dispatch, and
  return the ``(FS-Reply, WE-Error)`` pair. They run no check, because
  [copybooks/Proc-ACAS-FH-Calls.cob] contains no error-check paragraph in any of
  its 256 labels - verified by exhaustive label scan, not by sampling.
* the handler-named functions do the same and then, for the open family only,
  run their handler's error check, which closes the file and raises
  :exc:`FacadeGoback` on a non-zero reply.

Both reach ``_perform``. There is exactly one dispatch path per handler verb, so
no verb can drift between the vocabularies.

The second consequence of publishing what exists rather than what the pattern
implies is recorded in the Agent Action Plan's own anomaly register. Section
0.6.7 entry 6, verbatim:

    "A published facade verb that can never succeed - the handler rejects
    rewrite unconditionally at entry"

That verb is ``acas008_rewrite`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L163],
refused at [common/acas008.cbl:L299-L307]. It is published here, it always
fails, and it returns the failure pair rather than raising - see its own
docstring.


A SECOND, QUIETER ASYMMETRY BETWEEN THE CONVENTIONS
===================================================
The error check is not the only place the two copybooks disagree about the same
handler. ``acas000`` is dispatched by both, and only one of them pins the key:

* [copybooks/Proc-ACAS-FH-Calls.cob:L20-L25] issues the ``CALL`` with **no**
  ``move ... to File-Key-No`` at all, so the caller's key survives into the
  handler. That is what makes the System entity a multi-key dispatcher: the
  caller selects the table by setting ``File-Key-No`` before the verb.
* [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L22-L30] does
  ``move 1 to File-Key-No`` with the comment "1 = Primary as only used", so the
  IRS convention can only ever reach the system-parameter table.

Reproduced by two distinct dispatch functions, ``_dispatch_acas000_entity`` and
``_dispatch_acas000_handler``. Every other handler dispatched by both copybooks
is textually identical in both and therefore shares one dispatch function.


THE SPINE - WHAT EACH ALIAS MUST REACH
======================================
Agent Action Plan section 0.2.1.1, one row per handler-and-bridge pair. The
entity column is the name [copybooks/Proc-ACAS-FH-Calls.cob] uses; the four IRS
rows have no entity-convention name at all and are reachable only through the
handler-named aliases::

    entity        handler      module                    table
    System        acas000 k1   acas000_system            SYSTEM-REC
    System        acas000 k2   acas000_system            SYSDEFLT-REC
    System        acas000 k3   acas000_system            SYSFINAL-REC
    System        acas000 k4   acas000_system            SYSTOT-REC
    GL-Nominal    acas005      acas005_gl_nominal        GLLEDGER-REC
    GL-Posting    acas006      acas006_gl_posting        GLPOSTING-REC
    GL-Batch      acas007      acas007_gl_batch          GLBATCH-REC
    SPL-Posting   acas008      acas008_spl_posting       PSIRSPOST-REC
    Sales         acas012      acas012_sales             SALEDGER-REC
    Value         acas013      acas013_value             VALUEANAL-REC
    Analysis      acas015      acas015_analysis          ANALYSIS-REC
    Invoice       acas016      acas016_invoice           SAINVOICE-REC + SAINV-LINES-REC
    OTM3          acas019      acas019_otm3              SAITM3-REC
    Purch         acas022      acas022_purch             PULEDGER-REC
    PInvoice      acas026      acas026_pinvoice          PUINVOICE-REC + PUINV-LINES-REC
    OTM5          acas029      acas029_otm5              PUITM5-REC
    (none)        acasirsub1   acasirsub1_irs_nominal    IRSNL-REC
    (none)        acasirsub3   acasirsub3_irs_dflt       IRSDFLT-REC
    (none)        acasirsub4   acasirsub4_irs_posting    IRSPOSTING-REC
    (none)        acasirsub5   acasirsub5_irs_final      IRSFINAL-REC

``acas000`` is a FIVE-way key dispatcher, not the four the Agent Action Plan
names in sections 0.3.1 and 0.4.1.5. [common/acas000.cbl:L574-L600] evaluates
``File-Key-No`` for values 1 through 5, and the guard at
[common/acas000.cbl:L335] admits ``1`` through ``5`` - widened on 14/10/25 to
pre-support Payroll, with key 5 aliasing the system-parameter table. Two
comments in that file were not updated and still say four
[common/acas000.cbl:L185], as does [copybooks/Proc-ACAS-FH-Calls.cob:L20]. The
code is authoritative; the comments are stale.


THE FUNCTION-CODE DISPATCH MATRIX
=================================
Censused from every ``when <n>`` in all seventeen handler programs, not from a
sample. ⭐ AND THE CENSUS IS OF THE HANDLERS' FLAT-FILE ``evaluate``, WHICH IS
NOT WHAT AN RDB VERB REACHES. Every handler branches to its RDB path first -
``if not FS-Cobol-Files-Used / perform ba-Process-RDBMS / go to AA-Main-Exit``,
for example [common/acas029.cbl:L257-L261] - and leaves BEFORE the ``evaluate``
below. So on the RDB path a handler's own dispatch decides nothing, the code
passes to the bridge, and the BRIDGE's ``evaluate`` is the one that matters.
Consequence 2 below is where that distinction bites::

    acas000      1 2 3 4 5 7            no 8, no 9 - six codes only
    acas005      1 2 3 4 5 7 8 9        the baseline eight
    acas006      1 2 3 4 5 7 8 9
    acas007      1 2 3 4 5 7 8 9
    acas008      1 2 3 4 5 7 8 9        but 4, 7, 8, 9 refused at entry
    acas012      1 2 3 4 5 7 8 9 31     [common/acas012.cbl:L342]
    acas013      1 2 3 4 5 7 8 9
    acas015      1 2 3 4 5 7 8 9
    acas016      1 2 3 4 5 7 8 9 34     [common/acas016.cbl:L297]
    acas019      1 2 3 4 5 7 8 9
    acas022      1 2 3 4 5 7 8 9 31     [common/acas022.cbl:L344]
    acas026      1 2 3 4 5 7 8 9 34     [common/acas026.cbl:L289] - 34, NOT 31
    acas029      1 2 3 4 5 7 8 9
    acasirsub1   1 2 3 4 5 7 8 9 13 15  the only handler with the raw verbs
    acasirsub3   1 2 3 5 7              no 4, no 8, no 9
    acasirsub4   1 2 3 4 5 7 8 9
    acasirsub5   1 2 3 5 7              no 4, no 8, no 9

Three consequences this module encodes rather than smooths over:

1. Function code 6, ``fn-Delete-All``, is dispatched by NO handler. Every one
   routes it to ``when other`` and a bad-function reply;
   [common/acasirsub4.cbl:L235] annotates it "6 is unused". A bridge does
   implement it - [common/irspostingMT.cbl:L271-L272] dispatches
   ``when 6 *> DELETE-ALL Special`` to a paragraph flagged
   "THIS IS NON STANDARD" - so the operation is real but reachable only through
   the open-output coercion below, never by direct dispatch. Twelve entity
   paragraphs nevertheless publish a ``-Delete-All`` verb, so those twelve are
   published and permanently unsatisfiable.
2. Codes 32 and 33 are declared for OTM3 and OTM5 at
   [copybooks/wsfnctn.cob:L103-L104] and appear in NEITHER handler's
   ``evaluate`` - but they ARE dispatched, by both BRIDGES:
   [common/otm3MT.cbl:L420-L427] and [common/otm5MT.cbl:L425-L428] each route
   them to ``ba140-Process-Read-Next`` and ``ba150-Process-Read-Next``. Since
   the RDB path never reaches a handler's ``evaluate``, the four entity
   paragraphs that publish these verbs are SATISFIABLE, and
   ``dal/acas019_otm3.py`` and ``dal/acas029_otm5.py`` implement all four
   paragraphs.

   They are nevertheless incapable of returning a row, for a reason that is a
   defect rather than a design: both bridges assemble
   ``SELECT * FROM <table> WHERE  ORDER BY '<column>' ...;`` - the ``WHERE``
   unconditional with no predicate to follow it, and every ordering term
   single-quoted into a string constant - and then mask the resulting syntax
   error as an empty table. The observable answer is ``(10, 10)``, not
   ``(99, 990)``. Anomaly N-sorted-order-is-a-syntax-error, reproduced under
   rule R-4 and recorded in both handler modules.
3. Code 31 is live in exactly two handlers, ``acas012`` and ``acas022``, and
   code 34 in exactly two, ``acas016`` and ``acas026``.


THE FOUR OPEN-OUTPUT BEHAVIOURS
===============================
An open for output is not a uniform operation across the handlers, and the
difference is a difference in rows written::

    acas005                              coercion block COMMENTED OUT,
                                         "NOT used with GL."
                                         [common/acas005.cbl:L307-L314]
    acas006 acas007 acasirsub1 acasirsub4
                                         TWO bridge calls - an open, then a
                                         delete-all by fall-through
                                         [common/acas006.cbl:L313-L318]
    acas008                              ONE coerced call, the function
                                         replaced at entry
                                         [common/acas008.cbl:L313-L319]
    acas015 acas016 acas019 acas022 acas026 acas029 acasirsub3 acasirsub5
                                         ABSENT ENTIRELY

For the transfer file an open for output means delete every row
[common/acas008.cbl:L313-L319] and [common/acas008.cbl:L571-L574]. That is how
the end-of-job clear in [irs/irs030.cbl:L1720-L1724] is implemented, so
:func:`spl_posting_open_output` and :func:`acas008_open_output` must reach the
handler's delete-all path and not a no-op. They do, and by the faithful route:
this module sets the open function and the output access type and dispatches,
exactly as the copybook does, and the handler performs its own coercion. This
module never sets the delete-all function itself, because neither copybook does.


WHAT THIS MODULE DELIBERATELY DOES NOT REPRODUCE
================================================
Recorded as omissions rather than left to be inferred, per Agent Action Plan
section 0.5.3 - "Deliberate omissions are recorded as omissions."

* **All presentation.** The five error checks each ``display`` a message
  identifier at a screen position [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L322]
  and the shared abort displays five fields and then waits
  [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L356-L363]. Agent Action Plan
  section 0.3.4 governs: diagnostic displays with no database effect become log
  records and must not alter control flow. So every ``display`` becomes a log
  record and the ``accept Accept-Reply`` at
  [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L363] is dropped, its only effect
  being to block a terminal. ``SY008`` is "Note message & Hit return"
  [common/ACAS.cbl:L334] - the prompt half of that pause, dropped with it.
  What is NOT dropped: the ``perform <handler>-Close``, which has a database
  effect, and the ``goback``, which alters control flow.
* **The FH log-writing program.** It is out of scope per Agent Action Plan
  section 0.2.2. Nothing is omitted at this layer, though: an exhaustive scan of
  both copybooks finds that neither performs or calls any logging routine - the
  only non-dispatch ``perform`` in either file is one of the five error checks.
  Logging belongs to the handler programs, and the handler modules own it.
* **The eight out-of-scope entities.** [copybooks/Proc-ACAS-FH-Calls.cob]
  publishes ``DelFolio``, ``DelInvNos``, ``Delivery``, ``PLautogen``,
  ``Payments``, ``SLautogen``, ``Stock`` and ``Stock-Audit`` - 89 of the 234
  entity paragraphs. Their bridges (``auditMT``, ``deliveryMT``, ``delfolioMT``,
  ``sldelinvnosMT``, ``stockMT``, ``paymentsMT``, ``plautogenMT``,
  ``slautogenMT``) and their eleven tables are out of scope per Agent Action
  Plan section 0.2.2, and their handlers ``acas004``, ``acas010``, ``acas011``,
  ``acas014``, ``acas017``, ``acas023``, ``acas030`` and ``acas032`` have no
  module. Every one of the 89 verb names is published for traceability and
  raises :exc:`UnsupportedEntityError` at the dispatch step. This is the one
  place in this module where raising is correct, because these are out of
  scope - not defective, not unimplemented.
* **The raw verbs, codes 15 and 13.** Declared at
  [copybooks/wsfnctn.cob:L99-L100] in that order - 15 before 13, out of numeric
  sequence - and dispatched only by ``acasirsub1``, the sole handler
  implementing them. NEITHER copybook publishes a verb for either, because
  [copybooks/wsfnctn.cob:L100] marks them "Special 4 LD", meaning the
  ``common/*LD.cbl`` loader programs reach them by direct ``CALL``. No alias is
  added here: implemented, and unpublished.
* **``fn-extend``, access type 4.** Declared "not valid for ISAM" at
  [copybooks/wsfnctn.cob:L111]. Five entity paragraphs publish an
  ``-Open-Extend`` verb and no handler dispatches an extend access type on the
  relational path, so all five are published and never satisfied.


WHY THE STATUS IS READ FROM THE LINKAGE AND NOT FROM A RETURN VALUE
==================================================================
COBOL hands status back by mutating ``File-Access``, which is a linkage
parameter shared with the handler [copybooks/wsfnctn.cob:L22-L41]. The Python
handler modules do the same, and their Python return annotations disagree with
each other - six different shapes across the seventeen modules, from ``None``
through ``tuple[int, int]`` to a handler-specific outcome type. Reading the
return value would therefore couple this module to seventeen unrelated
signatures and would break the moment one changed. ``_perform`` reads
``file_access.fs_reply`` and ``file_access.we_error`` after the call, which is
both the faithful reproduction and the stable contract.

Where handler and bridge disagree on a code, the handler's value is what crosses
the ``CALL`` boundary and therefore what this module surfaces: a bad function is
``999`` at the handler and ``990`` at the bridge, confirmed in four pairs -
``acas029``/``otm5MT``, ``acasirsub3``/``irsdfltMT``,
``acasirsub4``/``irspostingMT`` and ``acasirsub5``/``irsfinalMT``.


CONSTRAINTS
===========
* No COBOL at runtime. No process launch, no foreign-function interface, no
  path to a compiled program or to the harness. Rule R-1.
* No binary floating-point arithmetic, and no coercion at all: this module moves
  control codes and passes records through opaquely. It computes nothing and
  re-types nothing. Rule R-2.
* No SQL, no DDL, no schema change, no transaction control, no ORM construct, no
  added validation. In particular no check that a verb is supported: the
  copybooks publish verbs that always fail and omit verbs the handlers
  implement, and both facts are reproduced by publishing exactly the paragraphs
  that exist. Rule R-3.
* Strictly sequential. No threads, no event loop, no worker pool, no connection
  pool. Rule R-3.
* Anomalies reproduced, never repaired, each with the locator of the COBOL it
  comes from. Rule R-4.
* One ``perform`` is one call, in source order. Nothing is reordered, batched,
  deferred, cached or coalesced, and no clock or entropy source is read, because
  the scenario state diff is sensitive to statement order. Rule R-6.

There is no user rules document for this project - ``review_rules`` reports that
none was provided - so the six rules above are those of Agent Action Plan
section 0.7.2, and enterprise-standard best practice applies where they are
silent.
"""

from __future__ import annotations

import inspect
import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from functools import lru_cache
from types import MappingProxyType
from typing import Final, NamedTuple, NoReturn

from acas_posting.dal import acas000_system
from acas_posting.dal import acas005_gl_nominal
from acas_posting.dal import acas006_gl_posting
from acas_posting.dal import acas007_gl_batch
from acas_posting.dal import acas008_spl_posting
from acas_posting.dal import acas012_sales
from acas_posting.dal import acas013_value
from acas_posting.dal import acas015_analysis
from acas_posting.dal import acas016_invoice
from acas_posting.dal import acas019_otm3
from acas_posting.dal import acas022_purch
from acas_posting.dal import acas026_pinvoice
from acas_posting.dal import acas029_otm5
from acas_posting.dal import acasirsub1_irs_nominal
from acas_posting.dal import acasirsub3_irs_dflt
from acas_posting.dal import acasirsub4_irs_posting
from acas_posting.dal import acasirsub5_irs_final
from acas_posting.dal import connection as _connection
from acas_posting.dal import cursor_state as _cursor_state
from acas_posting.dal.status import AccessType, FileFunction, FsReply
# `redact_for_log` is deliberately NOT imported. It escapes control characters in a
# driver message rather than removing its content, so it cannot make `SQL-Msg` safe
# to log; `Open-Error-Continued` reports the typed fields instead. See the
# safe-event schema in `acas_posting/dal/status.py`.
from acas_posting.dal.status import log_handler_failure
from acas_posting.records.file_access import FileAccess
from acas_posting.records.file_defs import FileDefs

_LOG: Final[logging.Logger] = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# The vocabulary this module does NOT own
# ---------------------------------------------------------------------------
# The function codes and access types are declared once, at
# [copybooks/wsfnctn.cob:L88-L116], and ``dal.status`` owns their Python form.
# They are imported above and never redeclared here.
#
# ``Access-Type`` is a single digit, ``pic 9`` [copybooks/wsfnctn.cob:L107],
# carrying two disjoint meanings: 1 through 4 are open modes and 5 through 9 are
# START relations. One field, two vocabularies - which is why a START verb must
# not clear it (see ACCESS_TYPE_LOGGING_RESET below).

#: The value the non-open verbs move into ``Access-Type``. It is NOT one of the
#: nine declared condition names, so it cannot be spelled with
#: :class:`~acas_posting.dal.status.AccessType`. The copybook header records why
#: it exists [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L19-L20]: "Changed all
#: accessing other than open with 1st line of move zero to Access-Type to keep
#: logging clean."
ACCESS_TYPE_LOGGING_RESET: Final[int] = 0

#: The key number every dispatch paragraph but two pins before its ``CALL``,
#: e.g. [copybooks/Proc-ACAS-FH-Calls.cob:L52]. The two exceptions are
#: ``acas000`` [copybooks/Proc-ACAS-FH-Calls.cob:L20-L25] and ``acas011``
#: [copybooks/Proc-ACAS-FH-Calls.cob:L75-L80], which leave the caller's value
#: alone.
PRIMARY_FILE_KEY_NO: Final[int] = 1

# The three fields a verb paragraph moves into, named as the copybook names
# them so that a plan below reads as its COBOL source reads.
_FILE_FUNCTION: Final[str] = "File-Function"
_ACCESS_TYPE: Final[str] = "Access-Type"
_FILE_KEY_NO: Final[str] = "File-Key-No"

#: Published verbs whose handler refuses the function unconditionally at entry,
#: taken from the data ``dal.cursor_state`` already derives from the handlers.
#: For ``PSIRSPOST-REC`` this is [common/acas008.cbl:L299-L307] - read-indexed,
#: rewrite, START and delete, because the underlying file is sequential. Only
#: one of those four, rewrite, is published by either copybook, which is why
#: Agent Action Plan section 0.6.7 entry 6 singles it out. Exposed for the
#: traceability document; this module never consults it to decide anything,
#: because deciding would be an added validation.
ALWAYS_REFUSED_BY_HANDLER: Final[Mapping[str, object]] = (
    _cursor_state.HANDLER_REJECTED_FUNCTIONS
)


# ---------------------------------------------------------------------------
# What crosses the boundary
# ---------------------------------------------------------------------------
class StatusPair(NamedTuple):
    """The ``(FS-Reply, WE-Error)`` pair a facade verb yields.

    Both fields are read back out of ``File-Access`` after the handler has run,
    because that is where COBOL puts them [copybooks/wsfnctn.cob:L23-L25]. The
    pair is a convenience for the caller and never the authority: the authority
    is the ``File-Access`` record itself, which the handler mutated in place and
    which the caller still holds.
    """

    fs_reply: int
    we_error: int


class FacadeError(Exception):
    """Base for the two conditions this module raises."""


class FacadeGoback(FacadeError):
    """Reproduces the ``goback.`` that ends the shared abort paragraph.

    [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L364] is a ``goback``, which
    returns from the PROGRAM rather than from the section - Agent Action Plan
    section 0.6.5's "returns from the program outright". All five error checks
    ``go to Open-Error-Continued``, so one paragraph aborts the caller for any
    of them.

    It is an exception and not a process exit on purpose. ``goback`` returns to
    the COBOL program's *caller*, which in the migrated system is a
    ``programs/*`` module that may still have end-of-job work to do -
    [irs/irs030.cbl:L1673-L1678] jumps to end-of-job on a write failure and the
    partial state is committed, not rolled back. Terminating the process would
    skip that and change which rows survive.
    """


class UnsupportedEntityError(FacadeError):
    """Raised by the eight entities whose bridges and tables are out of scope.

    [copybooks/Proc-ACAS-FH-Calls.cob] publishes ``DelFolio``, ``DelInvNos``,
    ``Delivery``, ``PLautogen``, ``Payments``, ``SLautogen``, ``Stock`` and
    ``Stock-Audit``. Agent Action Plan section 0.2.2 places their bridges and
    their eleven tables out of scope, so no handler module exists for them. The
    verb names are published for traceability and reaching the dispatch step
    raises this.

    This is not a stub and not a defect: it is the boundary of the migration
    stated in the one place a caller can observe it.
    """


@dataclass(frozen=True, slots=True)
class FacadeContext:
    """The linkage a ``perform`` of a facade verb needs.

    Every dispatch paragraph in both copybooks passes the same five things, e.g.
    [copybooks/Proc-ACAS-FH-Calls.cob:L51-L57]::

        call "acas007" using System-Record
                             WS-Batch-Record
                             File-Access
                             File-Defs
                             ACAS-DAL-Common-Data

    so this carries exactly those five and nothing else. It owns no connection
    and no cursor - those belong to ``dal.connection`` and ``dal.cursor_state``.

    ``record`` is the entity work area, whichever one the paragraph names. It is
    passed through opaquely and never inspected here, which is why it is typed
    ``object``: the entity record classes belong to the handler modules, and the
    layering forbids this module from importing them.

    ``dal_common`` is ``ACAS-DAL-Common-Data``. It is likewise ``object``,
    because its class lives in a records module this layer may not import.

    ``options`` has no COBOL counterpart and exists only because several handler
    modules take keyword-only parameters that COBOL had no way to express - a
    transport-security policy, a cursor-state table, a per-handler context.
    Whatever a caller puts here is forwarded verbatim to that handler's
    ``dispatch``; an empty mapping forwards nothing. It carries no accounting
    value and nothing here reads it.

    ⭐ IT IS ALSO THE ONE CHANNEL BY WHICH A SECURITY POLICY REACHES A HANDLER,
    and that makes an empty mapping a decision rather than an absence. Every
    handler that opens a connection declares ``transport: TransportSecurity |
    None = None`` and forwards it to ``connection.mysql_1000_open``, whose
    ``_require_permitted_connection`` then FAILS CLOSED on ``None``: a Unix
    socket or a loopback address is permitted, and any other target is refused
    unless a certificate authority is supplied or ``isolated_oracle=True`` is
    declared. So a caller that leaves ``options`` empty gets the safe answer for
    every handler, and a caller that must reach a non-local server states it once
    - ``options={"transport": TransportSecurity(...)}`` - and this context carries
    it to whichever handler the verb dispatches to.

    That uniformity is the point. It was previously possible for ONE handler to
    default itself permissive while the other nineteen failed closed, which made
    the policy depend on which entity a program happened to touch rather than on
    what the operator had declared (CWE-319, CWE-295). Nothing here inspects or
    rewrites the mapping: the enforcement lives in ``dal/connection.py`` and the
    declaration lives with the caller, and this field is only the wire between
    them. Forwarding is by keyword, so a handler that does not accept a given key
    raises ``TypeError`` at the call rather than silently ignoring a policy the
    caller believed was in force.
    """

    system: object
    record: object
    file_access: FileAccess
    file_defs: FileDefs | None = None
    dal_common: object = None
    options: Mapping[str, object] = field(default_factory=dict)


class _Plan(NamedTuple):
    """One facade verb paragraph, transcribed as data.

    ``moves`` lists the paragraph's assignments in SOURCE ORDER, which differs
    between paragraphs and is therefore transcribed rather than normalised: an
    open sets the function then the access type, a non-open clears the access
    type then sets the function, and a START sets the key then the function and
    never touches the access type at all.
    """

    paragraph: str
    lines: str
    handler: str
    moves: tuple[tuple[str, int], ...]
    check: str | None = None
    check_first: bool = False


# ---------------------------------------------------------------------------
# The single implementation core
# ---------------------------------------------------------------------------
def _apply(file_access: FileAccess, target: str, value: int) -> None:
    """Perform one ``move``/``set`` of a verb paragraph.

    The values are :class:`int` subclasses - the condition names of
    [copybooks/wsfnctn.cob:L88-L116] arrive as ``IntEnum`` members - and are
    stored as they arrive. Nothing is coerced or re-typed, here or anywhere
    else in this module.
    """
    if target is _FILE_FUNCTION:
        file_access.file_function = value
    elif target is _ACCESS_TYPE:
        file_access.access_type = value
    else:
        # ``File-Key-No`` sits inside ``Logging-Data``, not beside the status
        # fields [copybooks/wsfnctn.cob:L44-L46].
        file_access.logging_data.file_key_no = value


def _perform(ctx: FacadeContext, plan: _Plan) -> StatusPair:
    """Run one facade verb paragraph, whichever vocabulary named it.

    This is the only path from either vocabulary to a handler, so no verb can
    behave differently depending on the name it was reached by - except in the
    one respect the source makes different, which ``plan.check`` carries.

    The steps are the copybook's steps, in the copybook's order: apply the
    paragraph's moves, perform the dispatch paragraph, and read the status back
    out of the linkage. Nothing is reordered, batched, deferred, cached or
    coalesced, because the scenario state diff is sensitive to statement order.
    """
    file_access = ctx.file_access
    for target, value in plan.moves:
        _apply(file_access, target, value)

    # [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L98-L102] - ``acas000-Open-Input``
    # performs its error check BEFORE the dispatch, alone among all 42 verb
    # paragraphs. The check therefore tests whatever reply the PREVIOUS
    # operation left behind and this open's own failure is never checked at all.
    # Reproduced, not straightened.
    if plan.check is not None and plan.check_first:
        _CHECKS[plan.check](ctx)

    _DISPATCH[plan.handler](ctx)

    # Every other check runs after its dispatch, e.g.
    # [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L133-L134].
    if plan.check is not None and not plan.check_first:
        _CHECKS[plan.check](ctx)

    return StatusPair(file_access.fs_reply, file_access.we_error)


@lru_cache(maxsize=None)
def _keyword_extras_accepted_by(target: Callable[..., object]) -> frozenset[str]:
    """The keyword-only parameter names ``target`` declares.

    Read from the signature rather than transcribed into a table, because the
    seventeen handler modules do NOT agree on their keyword-only extras - eight
    take ``transport``, two of those also take ``states``, three also take
    ``allow_frozen_placeholder_credentials``, ``acas022_purch`` takes
    ``purchase_file``, ``acas026_pinvoice`` takes ``context``, and nine take none
    at all. A transcribed table would be a second opinion that could drift from
    the first; a signature cannot.

    Cached because the answer is fixed for the life of the process and this is
    consulted once per facade verb.

    Args:
        target: the handler's ``dispatch`` function.

    Returns:
        Its keyword-only parameter names.
    """
    return frozenset(
        name
        for name, parameter in inspect.signature(target).parameters.items()
        if parameter.kind is inspect.Parameter.KEYWORD_ONLY
    )


def _forward(
    ctx: FacadeContext, target: Callable[..., object]
) -> Mapping[str, object]:
    """The keyword-only extras to forward to ``target``, projected from ``options``.

    ⭐ WHY THIS PROJECTS RATHER THAN FORWARDING WHOLESALE. ``options`` is the one
    channel by which a caller's transport-security policy reaches a handler, and
    a caller states that policy ONCE for a whole run - it cannot reasonably know
    which of the seventeen handlers a given verb dispatches to, nor which of them
    declares which keyword. Forwarding the mapping wholesale made a single
    uniform declaration impossible: ``options={"transport": ...}`` reached
    ``acas006`` happily and raised ``TypeError`` from ``acas000``, so the only
    way to avoid the error was to leave ``options`` empty everywhere and let each
    handler decide its own transport policy - which is exactly how one handler
    came to default itself permissive while the other nineteen failed closed
    (CWE-319, CWE-295).

    Projecting makes the uniform declaration work: the caller says it once, every
    handler that can honour it receives it, and a handler that cannot is called
    exactly as before. NOTHING IS SILENTLY DISCARDED - a key that no handler on
    this path accepts is reported at WARNING, so a caller who believed a policy
    was in force and was wrong finds out. That report is a log record with no
    database effect and no control-flow effect, which is the whole of the test
    AAP section 0.3.4 sets for a diagnostic.

    A handler that DOES declare ``transport`` and is not given one is unaffected:
    its own default is ``None``, and ``connection._require_permitted_connection``
    resolves ``None`` fail-closed. Omission is therefore never the permissive
    answer.

    Args:
        ctx: the linkage this verb was performed with.
        target: the handler ``dispatch`` about to be called.

    Returns:
        The subset of ``ctx.options`` that ``target`` accepts. An empty mapping
        when the caller supplied none, which is the ordinary case and forwards
        nothing at all.
    """
    options = ctx.options
    if not options:
        return {}

    accepted = _keyword_extras_accepted_by(target)
    unhonoured = [name for name in options if name not in accepted]
    if unhonoured:
        # `%r` on the sorted NAMES only. The values are policy objects and record
        # areas - a transport policy carries certificate paths - so the message
        # says which declarations could not be honoured and never what they held
        # (CWE-532).
        _LOG.warning(
            "facade: %s accepts no keyword extra named %r, so the caller's "
            "declaration(s) of that name are not in force for this verb; the "
            "handler's own default applies, which for a transport policy is "
            "fail-closed",
            getattr(target, "__module__", "the handler"),
            sorted(unhonoured),
        )

    return {name: value for name, value in options.items() if name in accepted}


# ---------------------------------------------------------------------------
# THE ONE SECURITY-POLICY CONTRACT
# ---------------------------------------------------------------------------
#
# `FacadeContext.options` carries a policy to the eight handlers that declare a
# keyword-only `transport` on their `dispatch`. Four more accept one ONLY through
# a module-level declaration function of their own - the equivalent of setting a
# sub-program's WORKING-STORAGE before the first `CALL`, which is exactly what
# their COBOL originals do with the six `RDBMS-*` values
# [common/acas008.cbl:L558-L563] - and four accept none at all and can therefore
# only ever fail closed.
#
# Three mechanisms is two too many for a caller to have to know about, and a
# caller who knows about none of them is the caller whose policy silently fails
# to apply. So this layer publishes ONE door. It is the right layer for it:
# `dal/facade.py` is already the only path from any caller to any handler, and
# the AAP's per-directory import table (section 0.4.3) names it as the DAL module
# the layer above may import.
#
# NOT GLOBAL MUTABLE STATE INVENTED BY THE MIGRATION. Each handler's declaration
# slot already exists, because each COBOL sub-program already has working storage
# that outlives one `CALL`; this function does not add a slot, it gives the four
# that can only be reached that way a single, greppable caller.


#: The handlers whose transport policy is settable ONLY through a module-level
#: declaration, each paired with the callable that sets it. Kept as data so the
#: set is greppable and so adding a handler is one line rather than a branch.
#:
#: The three spellings are the handler modules' own and are deliberately not
#: renamed: `acas000_system.configure_transport` takes the policy positionally,
#: `acas007_gl_batch.declare_connection_policy` takes it by keyword and also
#: takes the credential declaration, and
#: `acasirsub1_irs_nominal.reset_bridge_storage` takes only the transport and
#: additionally resets the rest of its working storage - which is why it is
#: called here rather than a narrower setter being invented for it.
#: `acas022_purch` publishes `reset_bridge_state()` with no policy parameter at
#: all, so it is absent from this table: it has no slot to set, and its
#: `dispatch` accepts `transport` instead, which the options channel reaches.
_MODULE_LEVEL_POLICY_SETTERS: Final[
    tuple[tuple[str, Callable[..., None]], ...]
] = (
    ("acas000_system", acas000_system.configure_transport),
    ("acas007_gl_batch", acas007_gl_batch.declare_connection_policy),
    ("acasirsub1_irs_nominal", acasirsub1_irs_nominal.reset_bridge_storage),
)


def declare_connection_policy(
    *,
    transport: _connection.TransportSecurity | None = None,
    allow_frozen_placeholder_credentials: bool = False,
) -> None:
    """Declare, once, how every handler may reach the database.

    THE COMPANION OF ``FacadeContext.options``, NOT A SUBSTITUTE FOR IT. Between
    them they cover every handler that can be told a policy at all:

    * eight handlers declare a keyword-only ``transport`` on their ``dispatch``
      and are reached by ``options={"transport": ...}`` on the context;
    * three are reached only through a module-level declaration and are reached
      by this function;
    * ``acas022_purch`` is in the first group;
    * ``acas005_gl_nominal``, ``acas012_sales``, ``acas016_invoice`` and
      ``acasirsub4_irs_posting`` publish neither, so they can only ever use the
      fail-closed default - a Unix socket or a loopback address. That is a
      LIMITATION AND IT IS RECORDED AS ONE: those four cannot be pointed at a
      non-local server, and the refusal surfaces as the same ``(99, 911)`` the
      frozen open produces on any connect failure, never as a silent plaintext
      connection.

    A process boundary should call this once and ALSO pass the same policy on
    every context it builds; the two together are the whole contract. Calling
    this with no arguments is meaningful and is the fail-closed declaration.

    Args:
        transport: the policy. ``None`` means the caller declares nothing, which
            ``connection._require_permitted_connection`` resolves fail-closed:
            loopback and Unix sockets are permitted and every other target is
            refused unless a certificate authority is supplied or
            ``isolated_oracle=True`` is declared.
        allow_frozen_placeholder_credentials: whether the shipped placeholders of
            [copybooks/wssystem.cob:L138-L139] may authenticate. ``False``, the
            default, refuses them.

    Returns:
        None. Every effect is on the named handlers' own declaration slots.
    """
    for module_name, setter in _MODULE_LEVEL_POLICY_SETTERS:
        parameters = inspect.signature(setter).parameters
        extras: dict[str, object] = {}
        if "allow_frozen_placeholder_credentials" in parameters:
            extras["allow_frozen_placeholder_credentials"] = (
                allow_frozen_placeholder_credentials
            )
        if parameters["transport"].kind is inspect.Parameter.KEYWORD_ONLY:
            setter(transport=transport, **extras)
        else:
            setter(transport, **extras)
        _LOG.debug(
            "facade: connection policy declared to %s (server verified=%s, "
            "isolated-oracle declared=%s)",
            module_name,
            bool(transport and transport.verifies_the_server()),
            bool(transport and transport.isolated_oracle),
        )


# ---------------------------------------------------------------------------
# The dispatch layer - one function per dispatch paragraph
# ---------------------------------------------------------------------------
# A verb paragraph sets state and then performs a dispatch paragraph; the
# dispatch paragraph pins the key number and issues the ``CALL``
# [copybooks/Proc-ACAS-FH-Calls.cob:L51-L57]. Both levels are kept, because
# collapsing them would lose the two paragraphs that decline to pin the key.
#
# The status is NOT taken from the return value. Every handler's ``dispatch``
# mutates ``File-Access`` in place, exactly as the COBOL ``CALL`` does through
# linkage, and the seventeen Python return annotations disagree with one
# another - six distinct shapes. ``_perform`` reads the linkage afterwards.


def _dispatch_acas000_entity(ctx: FacadeContext) -> None:
    """``acas000`` passing ``System-Record``.

    [copybooks/Proc-ACAS-FH-Calls.cob:L20-L24]

    This paragraph issues no ``move ... to File-Key-No``, so the caller's key
    survives into the handler. That is what makes the System entity a
    multi-key dispatcher, and it is the second way the two conventions
    disagree about ``acas000``: the handler-named side pins the key to 1.
    """
    acas000_system.dispatch(
        ctx.system,
        ctx.file_access,
        ctx.file_defs,
        ctx.dal_common,
        **_forward(ctx, acas000_system.dispatch),
    )


def _dispatch_acas000_handler(ctx: FacadeContext) -> None:
    """``acas000`` passing ``WS-System-Record``.

    [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L22-L29]

    The handler-named convention pins the key - ``move 1 to File-Key-No``,
    commented "1 = Primary as only used" - so this side can only ever
    reach the system-parameter table.
    """
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    acas000_system.dispatch(
        ctx.system,
        ctx.file_access,
        ctx.file_defs,
        ctx.dal_common,
        **_forward(ctx, acas000_system.dispatch),
    )


def _dispatch_acas004(ctx: FacadeContext) -> None:
    """``acas004`` passing ``WS-Invoice-Record``.

    [copybooks/Proc-ACAS-FH-Calls.cob:L27-L32]
    """
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    raise UnsupportedEntityError(
        "acas004 serves the out-of-scope entity SLautogen. Its bridge and its"
        " tables are out of scope per Agent Action Plan section"
        " 0.2.2, so no handler module exists. The verb names are"
        " published for traceability only."
    )


def _dispatch_acas005(ctx: FacadeContext) -> None:
    """``acas005`` passing ``WS-Ledger-Record``.

    [copybooks/Proc-ACAS-FH-Calls.cob:L35-L40]
    """
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    acas005_gl_nominal.dispatch(
        ctx.system,
        ctx.record,
        ctx.file_access,
        ctx.file_defs,
        ctx.dal_common,
        **_forward(ctx, acas005_gl_nominal.dispatch),
    )


def _dispatch_acas006(ctx: FacadeContext) -> None:
    """``acas006`` passing ``WS-Posting-Record``.

    [copybooks/Proc-ACAS-FH-Calls.cob:L43-L48]
    """
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    acas006_gl_posting.dispatch(
        ctx.system,
        ctx.record,
        ctx.file_access,
        ctx.file_defs,
        ctx.dal_common,
        **_forward(ctx, acas006_gl_posting.dispatch),
    )


def _dispatch_acas007(ctx: FacadeContext) -> None:
    """``acas007`` passing ``WS-Batch-Record``.

    [copybooks/Proc-ACAS-FH-Calls.cob:L51-L56]
    """
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    acas007_gl_batch.dispatch(
        ctx.system,
        ctx.record,
        ctx.file_access,
        ctx.file_defs,
        ctx.dal_common,
        **_forward(ctx, acas007_gl_batch.dispatch),
    )


def _dispatch_acas008(ctx: FacadeContext) -> None:
    """``acas008`` passing ``WS-IRS-Posting-Record``.

    [copybooks/Proc-ACAS-FH-Calls.cob:L59-L64]

    Dispatched by BOTH copybooks, [copybooks/Proc-ACAS-FH-Calls.cob:L59-L64]
    and [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L34-L40], with textually identical bodies, so one
    function serves both vocabularies.
    """
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    acas008_spl_posting.dispatch(
        ctx.system,
        ctx.record,
        ctx.file_access,
        ctx.file_defs,
        ctx.dal_common,
        **_forward(ctx, acas008_spl_posting.dispatch),
    )


def _dispatch_acas010(ctx: FacadeContext) -> None:
    """``acas010`` passing ``WS-Stock-Audit-Record``.

    [copybooks/Proc-ACAS-FH-Calls.cob:L67-L72]
    """
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    raise UnsupportedEntityError(
        "acas010 serves the out-of-scope entity Stock-Audit. Its bridge and its"
        " tables are out of scope per Agent Action Plan section"
        " 0.2.2, so no handler module exists. The verb names are"
        " published for traceability only."
    )


def _dispatch_acas011(ctx: FacadeContext) -> None:
    """``acas011`` passing ``WS-Stock-Record``.

    [copybooks/Proc-ACAS-FH-Calls.cob:L75-L79]

    This paragraph issues no ``move ... to File-Key-No`` either - its own
    comment reads "This one can use 3 File Key nos 1 - 3".
    """
    raise UnsupportedEntityError(
        "acas011 serves the out-of-scope entity Stock. Its bridge and its"
        " tables are out of scope per Agent Action Plan section"
        " 0.2.2, so no handler module exists. The verb names are"
        " published for traceability only."
    )


def _dispatch_acas012(ctx: FacadeContext) -> None:
    """``acas012`` passing ``WS-Sales-Record``.

    [copybooks/Proc-ACAS-FH-Calls.cob:L82-L87]
    """
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    acas012_sales.dispatch(
        ctx.system,
        ctx.record,
        ctx.file_access,
        ctx.file_defs,
        ctx.dal_common,
        **_forward(ctx, acas012_sales.dispatch),
    )


def _dispatch_acas013(ctx: FacadeContext) -> None:
    """``acas013`` passing ``WS-Value-Record``.

    [copybooks/Proc-ACAS-FH-Calls.cob:L90-L95]
    """
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    acas013_value.dispatch(
        ctx.system,
        ctx.record,
        ctx.file_access,
        ctx.file_defs,
        ctx.dal_common,
        **_forward(ctx, acas013_value.dispatch),
    )


def _dispatch_acas014(ctx: FacadeContext) -> None:
    """``acas014`` passing ``WS-Delivery-Record``.

    [copybooks/Proc-ACAS-FH-Calls.cob:L99-L104]
    """
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    raise UnsupportedEntityError(
        "acas014 serves the out-of-scope entity Delivery. Its bridge and its"
        " tables are out of scope per Agent Action Plan section"
        " 0.2.2, so no handler module exists. The verb names are"
        " published for traceability only."
    )


def _dispatch_acas015(ctx: FacadeContext) -> None:
    """``acas015`` passing ``WS-Analysis-Record``.

    [copybooks/Proc-ACAS-FH-Calls.cob:L108-L113]
    """
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    acas015_analysis.dispatch(
        ctx.system,
        ctx.record,
        ctx.file_access,
        ctx.file_defs,
        ctx.dal_common,
        **_forward(ctx, acas015_analysis.dispatch),
    )


def _dispatch_acas016(ctx: FacadeContext) -> None:
    """``acas016`` passing ``WS-Invoice-Record``.

    [copybooks/Proc-ACAS-FH-Calls.cob:L116-L121]

    ⭐ THE ONE DISPATCH PARAGRAPH THAT HANDS OVER A PROJECTED RECORD, and the
    reason is in the handler's own linkage. ``acas016`` copies its parameter with
    a renaming clause - ``copy "slwsinv2.cob" replacing Invoice-Record by
    WS-Invoice-Record`` [common/acas016.cbl:L218-L221] - while the bridge behind
    it copies ``slwsinv.cob``, the identical 137-byte layout under the ``sih-``
    and ``sil-`` names. In COBOL that costs nothing, because ``COPY ...
    REPLACING`` renames at compile time and a ``CALL`` passes the caller's bytes
    by reference either way. Python has no compile-time rename, so the two
    declarations are two classes and the handover has to be spelled out.

    It is spelled out in ``dal.acas016_invoice``, which owns both shapes, and
    called from here, which is where Agent Action Plan section 0.4.3 puts the
    business of handing a handler the parameter shape its ``PROCEDURE DIVISION
    USING`` declares - this module may not import a records module, so the
    conversion cannot live in it. A caller holding an ``InvoiceBuffer`` already
    passes straight through: ``linkage_buffer_for`` returns it unchanged and
    ``publish_linkage_buffer`` does nothing.

    ``publish_linkage_buffer`` runs AFTER the dispatch and not in a ``finally``,
    because the handler never raises [common/acas016.cbl:L627] - *"Any errors
    leave it to caller to recover from"* - so there is no failure path for which
    the COBOL would still have copied the record area back.
    """
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    invoice = acas016_invoice.linkage_buffer_for(ctx.record)
    acas016_invoice.dispatch(
        ctx.system,
        invoice,
        ctx.file_access,
        ctx.file_defs,
        ctx.dal_common,
        **_forward(ctx, acas016_invoice.dispatch),
    )
    acas016_invoice.publish_linkage_buffer(invoice, ctx.record)


def _dispatch_acas017(ctx: FacadeContext) -> None:
    """``acas017`` passing ``WS-Del-Inv-Nos-Record``.

    [copybooks/Proc-ACAS-FH-Calls.cob:L124-L129]
    """
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    raise UnsupportedEntityError(
        "acas017 serves the out-of-scope entity DelInvNos. Its bridge and its"
        " tables are out of scope per Agent Action Plan section"
        " 0.2.2, so no handler module exists. The verb names are"
        " published for traceability only."
    )


def _dispatch_acas019(ctx: FacadeContext) -> None:
    """``acas019`` passing ``WS-OTM3-Record``.

    [copybooks/Proc-ACAS-FH-Calls.cob:L132-L137]
    """
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    acas019_otm3.dispatch(
        ctx.system,
        ctx.record,
        ctx.file_access,
        ctx.file_defs,
        ctx.dal_common,
        **_forward(ctx, acas019_otm3.dispatch),
    )


def _dispatch_acas022(ctx: FacadeContext) -> None:
    """``acas022`` passing ``WS-Purch-Record``.

    [copybooks/Proc-ACAS-FH-Calls.cob:L140-L145]
    """
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    acas022_purch.dispatch(
        ctx.system,
        ctx.record,
        ctx.file_access,
        ctx.file_defs,
        ctx.dal_common,
        **_forward(ctx, acas022_purch.dispatch),
    )


def _dispatch_acas023(ctx: FacadeContext) -> None:
    """``acas023`` passing ``WS-Del-Inv-Nos-Record``.

    [copybooks/Proc-ACAS-FH-Calls.cob:L148-L153]
    """
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    raise UnsupportedEntityError(
        "acas023 serves the out-of-scope entity DelFolio. Its bridge and its"
        " tables are out of scope per Agent Action Plan section"
        " 0.2.2, so no handler module exists. The verb names are"
        " published for traceability only."
    )


def _dispatch_acas026(ctx: FacadeContext) -> None:
    """``acas026`` passing ``WS-PInvoice-Record``.

    [copybooks/Proc-ACAS-FH-Calls.cob:L156-L161]

    ⭐ THE SECOND DISPATCH PARAGRAPH THAT HANDS OVER A PROJECTED RECORD, for the
    same reason as ``acas016`` and with a different pair of descriptions. The
    purchase-invoice record is described TWICE in the frozen source -
    ``copybooks/plwspinv.cob`` nests it, ``copybooks/plwspinv2.cob`` lays it flat
    with two redefinitions over it - and each caller copies the one it wants, so
    ``acas026`` is handed whatever its caller's ``WS-PInvoice-Record`` happens to
    be. In COBOL that works because a ``CALL`` passes storage and the callee's
    ``LINKAGE SECTION`` decides how to read it; Python has no storage aliasing, so
    the swap is spelled out in ``dal.acas026_pinvoice``, which owns both
    descriptions, and called from here. That answers AMBIGUITY Q-PL055-8, which
    asked which description the handler wants and said the facade owns the
    translation.

    A caller holding a ``PInvoiceHeader`` passes straight through unchanged.

    The published-back copy runs AFTER the dispatch and not in a ``finally``,
    because the handler never raises [common/acas026.cbl:L617] - *"Any errors
    leave it to caller to recover from"*.
    """
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    options = _forward(ctx, acas026_pinvoice.dispatch)
    # The staged line lives in the working storage the call uses, so the same
    # `context` the caller forwarded - if any - is the one to project through, on
    # the way in AND on the way out.
    context = options.get("context")
    pinvoice = acas026_pinvoice.linkage_header_for(ctx.record, context)  # type: ignore[arg-type]
    acas026_pinvoice.dispatch(
        ctx.system,
        pinvoice,
        ctx.file_access,
        ctx.file_defs,
        ctx.dal_common,
        **options,
    )
    acas026_pinvoice.publish_linkage_header(pinvoice, ctx.record, context)  # type: ignore[arg-type]


def _dispatch_acas029(ctx: FacadeContext) -> None:
    """``acas029`` passing ``WS-OTM5-Record``.

    [copybooks/Proc-ACAS-FH-Calls.cob:L164-L169]
    """
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    acas029_otm5.dispatch(
        ctx.system,
        ctx.record,
        ctx.file_access,
        ctx.file_defs,
        ctx.dal_common,
        **_forward(ctx, acas029_otm5.dispatch),
    )


def _dispatch_acas030(ctx: FacadeContext) -> None:
    """``acas030`` passing ``WS-PInvoice-Record``.

    [copybooks/Proc-ACAS-FH-Calls.cob:L172-L177]
    """
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    raise UnsupportedEntityError(
        "acas030 serves the out-of-scope entity PLautogen. Its bridge and its"
        " tables are out of scope per Agent Action Plan section"
        " 0.2.2, so no handler module exists. The verb names are"
        " published for traceability only."
    )


def _dispatch_acas032(ctx: FacadeContext) -> None:
    """``acas032`` passing ``WS-Pay-Record``.

    [copybooks/Proc-ACAS-FH-Calls.cob:L180-L185]
    """
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    raise UnsupportedEntityError(
        "acas032 serves the out-of-scope entity Payments. Its bridge and its"
        " tables are out of scope per Agent Action Plan section"
        " 0.2.2, so no handler module exists. The verb names are"
        " published for traceability only."
    )


def _dispatch_acasirsub1(ctx: FacadeContext) -> None:
    """``acasirsub1`` passing ``WS-IRSNL-Record``.

    [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L45-L52]
    """
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    acasirsub1_irs_nominal.dispatch(
        ctx.system,
        ctx.record,
        ctx.file_access,
        ctx.file_defs,
        ctx.dal_common,
        **_forward(ctx, acasirsub1_irs_nominal.dispatch),
    )


def _dispatch_acasirsub3(ctx: FacadeContext) -> None:
    """``acasirsub3`` passing ``WS-IRS-Default-Record``.

    [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L57-L64]
    """
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    acasirsub3_irs_dflt.dispatch(
        ctx.system,
        ctx.record,
        ctx.file_access,
        ctx.file_defs,
        ctx.dal_common,
        **_forward(ctx, acasirsub3_irs_dflt.dispatch),
    )


def _dispatch_acasirsub4(ctx: FacadeContext) -> None:
    """``acasirsub4`` passing ``Posting-Record``.

    [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L69-L76]
    """
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    acasirsub4_irs_posting.dispatch(
        ctx.system,
        ctx.record,
        ctx.file_access,
        ctx.file_defs,
        ctx.dal_common,
        **_forward(ctx, acasirsub4_irs_posting.dispatch),
    )


def _dispatch_acasirsub5(ctx: FacadeContext) -> None:
    """``acasirsub5`` passing ``Final-Record``.

    [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L81-L88]
    """
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    acasirsub5_irs_final.dispatch(
        ctx.system,
        ctx.record,
        ctx.file_access,
        ctx.file_defs,
        ctx.dal_common,
        **_forward(ctx, acasirsub5_irs_final.dispatch),
    )



#: Dispatch paragraph to implementation. ``acas000`` has two entries because the
#: two copybooks dispatch it differently; every other handler both dispatch is
#: textually identical in both.
#: Read-only, so no caller can graft a handler on at run time.
_DISPATCH: Final[Mapping[str, Callable[[FacadeContext], None]]] = MappingProxyType({
    "acas000-entity": _dispatch_acas000_entity,
    "acas000-handler": _dispatch_acas000_handler,
    "acas004": _dispatch_acas004,
    "acas005": _dispatch_acas005,
    "acas006": _dispatch_acas006,
    "acas007": _dispatch_acas007,
    "acas008": _dispatch_acas008,
    "acas010": _dispatch_acas010,
    "acas011": _dispatch_acas011,
    "acas012": _dispatch_acas012,
    "acas013": _dispatch_acas013,
    "acas014": _dispatch_acas014,
    "acas015": _dispatch_acas015,
    "acas016": _dispatch_acas016,
    "acas017": _dispatch_acas017,
    "acas019": _dispatch_acas019,
    "acas022": _dispatch_acas022,
    "acas023": _dispatch_acas023,
    "acas026": _dispatch_acas026,
    "acas029": _dispatch_acas029,
    "acas030": _dispatch_acas030,
    "acas032": _dispatch_acas032,
    "acasirsub1": _dispatch_acasirsub1,
    "acasirsub3": _dispatch_acasirsub3,
    "acasirsub4": _dispatch_acasirsub4,
    "acasirsub5": _dispatch_acasirsub5,
})


# ---------------------------------------------------------------------------
# Vocabulary one: the entity-named verbs of [copybooks/Proc-ACAS-FH-Calls.cob]
# ---------------------------------------------------------------------------
# 234 paragraphs across 21 entities, published exactly as they exist. The grid
# is NOT complete and is not completed here: the 21 entities use 18 distinct
# verb suffixes between them, which would be 378 combinations, and 234 of those
# combinations are written. Synthesising the rest would invent behaviour.
#
# Per-entity paragraph counts, censused from the file: System 7, Analysis 10,
# Stock 10, GL-Nominal 11, Sales 11, Value 11, Purch 11, Payments 11,
# Delivery 11, DelInvNos 11, DelFolio 11, Stock-Audit 11, GL-Posting 12,
# GL-Batch 12, SPL-Posting 12, Invoice 12, PInvoice 12, OTM3 12, OTM5 12,
# SLautogen 12, PLautogen 12.
#
# NONE of these functions runs an error check, because
# [copybooks/Proc-ACAS-FH-Calls.cob] contains no error-check paragraph in any of
# its 256 labels. Its callers test ``FS-Reply`` and ``WE-Error`` inline, and so
# must the callers of these functions.


# --------------------------------------------------------------------------
# System -> acas000 -> SYSTEM-REC / SYSDEFLT-REC / SYSFINAL-REC / SYSTOT-REC (by File-Key-No)
# --------------------------------------------------------------------------


_E_SYSTEM_OPEN: Final[_Plan] = _Plan(
    "System-Open",
    "L190-L195",
    "acas000-entity",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
)


def system_open(ctx: FacadeContext) -> StatusPair:
    """``System-Open`` [copybooks/Proc-ACAS-FH-Calls.cob:L190-L195].

    Written with literal ``move n to File-Function`` and ``move n to
    Access-Type`` rather than ``set fn-... to true`` - the only entity that
    does. Same effect, transcribed as written.

    ``acas000`` is a FIVE-way key dispatcher
    [common/acas000.cbl:L574-L600] and its dispatch paragraph pins no key, so
    the caller selects the table through ``File-Key-No`` before calling.
    """
    return _perform(ctx, _E_SYSTEM_OPEN)


_E_SYSTEM_OPEN_INPUT: Final[_Plan] = _Plan(
    "System-Open-Input",
    "L197-L202",
    "acas000-entity",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
)


def system_open_input(ctx: FacadeContext) -> StatusPair:
    """``System-Open-Input`` [copybooks/Proc-ACAS-FH-Calls.cob:L197-L202].

    Written with literal ``move n to File-Function`` and ``move n to
    Access-Type`` rather than ``set fn-... to true`` - the only entity that
    does. Same effect, transcribed as written.

    ``acas000`` is a FIVE-way key dispatcher
    [common/acas000.cbl:L574-L600] and its dispatch paragraph pins no key, so
    the caller selects the table through ``File-Key-No`` before calling.
    """
    return _perform(ctx, _E_SYSTEM_OPEN_INPUT)


_E_SYSTEM_OPEN_OUTPUT: Final[_Plan] = _Plan(
    "System-Open-Output",
    "L204-L209",
    "acas000-entity",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.OUTPUT),
    ),
)


def system_open_output(ctx: FacadeContext) -> StatusPair:
    """``System-Open-Output`` [copybooks/Proc-ACAS-FH-Calls.cob:L204-L209].

    Written with literal ``move n to File-Function`` and ``move n to
    Access-Type`` rather than ``set fn-... to true`` - the only entity that
    does. Same effect, transcribed as written.

    ``acas000`` is a FIVE-way key dispatcher
    [common/acas000.cbl:L574-L600] and its dispatch paragraph pins no key, so
    the caller selects the table through ``File-Key-No`` before calling.
    """
    return _perform(ctx, _E_SYSTEM_OPEN_OUTPUT)


_E_SYSTEM_CLOSE: Final[_Plan] = _Plan(
    "System-Close",
    "L211-L215",
    "acas000-entity",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def system_close(ctx: FacadeContext) -> StatusPair:
    """``System-Close`` [copybooks/Proc-ACAS-FH-Calls.cob:L211-L215].

    Written with literal ``move n to File-Function`` and ``move n to
    Access-Type`` rather than ``set fn-... to true`` - the only entity that
    does. Same effect, transcribed as written.

    ``acas000`` is a FIVE-way key dispatcher
    [common/acas000.cbl:L574-L600] and its dispatch paragraph pins no key, so
    the caller selects the table through ``File-Key-No`` before calling.
    """
    return _perform(ctx, _E_SYSTEM_CLOSE)


_E_SYSTEM_READ_INDEXED: Final[_Plan] = _Plan(
    "System-Read-Indexed",
    "L217-L220",
    "acas000-entity",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_INDEXED),
    ),
)


def system_read_indexed(ctx: FacadeContext) -> StatusPair:
    """``System-Read-Indexed`` [copybooks/Proc-ACAS-FH-Calls.cob:L217-L220].

    ``acas000`` is a FIVE-way key dispatcher
    [common/acas000.cbl:L574-L600] and its dispatch paragraph pins no key, so
    the caller selects the table through ``File-Key-No`` before calling.
    """
    return _perform(ctx, _E_SYSTEM_READ_INDEXED)


_E_SYSTEM_WRITE: Final[_Plan] = _Plan(
    "System-Write",
    "L222-L225",
    "acas000-entity",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def system_write(ctx: FacadeContext) -> StatusPair:
    """``System-Write`` [copybooks/Proc-ACAS-FH-Calls.cob:L222-L225].

    ``acas000`` is a FIVE-way key dispatcher
    [common/acas000.cbl:L574-L600] and its dispatch paragraph pins no key, so
    the caller selects the table through ``File-Key-No`` before calling.
    """
    return _perform(ctx, _E_SYSTEM_WRITE)


_E_SYSTEM_REWRITE: Final[_Plan] = _Plan(
    "System-ReWrite",
    "L227-L230",
    "acas000-entity",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def system_rewrite(ctx: FacadeContext) -> StatusPair:
    """``System-ReWrite`` [copybooks/Proc-ACAS-FH-Calls.cob:L227-L230].

    Spelled ``ReWrite`` with a capital W in the source, where the other
    twenty entities spell it ``Rewrite``. Case folds in Python; the source
    spelling is recorded in the traceability footer.

    ``acas000`` is a FIVE-way key dispatcher
    [common/acas000.cbl:L574-L600] and its dispatch paragraph pins no key, so
    the caller selects the table through ``File-Key-No`` before calling.
    """
    return _perform(ctx, _E_SYSTEM_REWRITE)


# --------------------------------------------------------------------------
# SLautogen -> acas004 -> OUT OF SCOPE per Agent Action Plan section 0.2.2
# --------------------------------------------------------------------------


_E_SLAUTOGEN_OPEN: Final[_Plan] = _Plan(
    "SLautogen-Open",
    "L234-L237",
    "acas004",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
)


def slautogen_open(ctx: FacadeContext) -> StatusPair:
    """``SLautogen-Open`` [copybooks/Proc-ACAS-FH-Calls.cob:L234-L237].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas004``.
    """
    return _perform(ctx, _E_SLAUTOGEN_OPEN)


_E_SLAUTOGEN_OPEN_INPUT: Final[_Plan] = _Plan(
    "SLautogen-Open-Input",
    "L239-L242",
    "acas004",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
)


def slautogen_open_input(ctx: FacadeContext) -> StatusPair:
    """``SLautogen-Open-Input`` [copybooks/Proc-ACAS-FH-Calls.cob:L239-L242].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas004``.
    """
    return _perform(ctx, _E_SLAUTOGEN_OPEN_INPUT)


_E_SLAUTOGEN_OPEN_OUTPUT: Final[_Plan] = _Plan(
    "SLautogen-Open-Output",
    "L244-L247",
    "acas004",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.OUTPUT),
    ),
)


def slautogen_open_output(ctx: FacadeContext) -> StatusPair:
    """``SLautogen-Open-Output`` [copybooks/Proc-ACAS-FH-Calls.cob:L244-L247].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas004``.
    """
    return _perform(ctx, _E_SLAUTOGEN_OPEN_OUTPUT)


_E_SLAUTOGEN_CLOSE: Final[_Plan] = _Plan(
    "SLautogen-Close",
    "L249-L252",
    "acas004",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def slautogen_close(ctx: FacadeContext) -> StatusPair:
    """``SLautogen-Close`` [copybooks/Proc-ACAS-FH-Calls.cob:L249-L252].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas004``.
    """
    return _perform(ctx, _E_SLAUTOGEN_CLOSE)


_E_SLAUTOGEN_DELETE: Final[_Plan] = _Plan(
    "SLautogen-Delete",
    "L254-L258",
    "acas004",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def slautogen_delete(ctx: FacadeContext) -> StatusPair:
    """``SLautogen-Delete`` [copybooks/Proc-ACAS-FH-Calls.cob:L254-L258].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas004``.
    """
    return _perform(ctx, _E_SLAUTOGEN_DELETE)


_E_SLAUTOGEN_DELETE_ALL: Final[_Plan] = _Plan(
    "SLautogen-Delete-All",
    "L260-L264",
    "acas004",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE_ALL),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def slautogen_delete_all(ctx: FacadeContext) -> StatusPair:
    """``SLautogen-Delete-All`` [copybooks/Proc-ACAS-FH-Calls.cob:L260-L264].

    Sets function code 6, which NO handler dispatches - every one routes
    it to ``when other`` and a bad-function reply
    [common/acasirsub4.cbl:L235]. Published and permanently unsatisfiable.
    The operation is real but reachable only through the open-output
    coercion [common/irspostingMT.cbl:L271-L272].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas004``.
    """
    return _perform(ctx, _E_SLAUTOGEN_DELETE_ALL)


_E_SLAUTOGEN_START: Final[_Plan] = _Plan(
    "SLautogen-Start",
    "L266-L269",
    "acas004",
    (
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.START),
    ),
)


def slautogen_start(ctx: FacadeContext) -> StatusPair:
    """``SLautogen-Start`` [copybooks/Proc-ACAS-FH-Calls.cob:L266-L269].

    Deliberately does NOT clear ``Access-Type``: on a START that field
    carries the relation, 5 through 9 of [copybooks/wsfnctn.cob:L112-L116],
    and the caller sets it. Clearing it would change which row is found.

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas004``.
    """
    return _perform(ctx, _E_SLAUTOGEN_START)


_E_SLAUTOGEN_READ_NEXT: Final[_Plan] = _Plan(
    "SLautogen-Read-Next",
    "L271-L274",
    "acas004",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def slautogen_read_next(ctx: FacadeContext) -> StatusPair:
    """``SLautogen-Read-Next`` [copybooks/Proc-ACAS-FH-Calls.cob:L271-L274].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas004``.
    """
    return _perform(ctx, _E_SLAUTOGEN_READ_NEXT)


_E_SLAUTOGEN_READ_NEXT_HEADER: Final[_Plan] = _Plan(
    "SLautogen-Read-Next-Header",
    "L276-L279",
    "acas004",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT_HEADER),
    ),
)


def slautogen_read_next_header(ctx: FacadeContext) -> StatusPair:
    """``SLautogen-Read-Next-Header`` [copybooks/Proc-ACAS-FH-Calls.cob:L276-L279].

    Sets function code 34 [copybooks/wsfnctn.cob:L105].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas004``.
    """
    return _perform(ctx, _E_SLAUTOGEN_READ_NEXT_HEADER)


_E_SLAUTOGEN_READ_INDEXED: Final[_Plan] = _Plan(
    "SLautogen-Read-Indexed",
    "L281-L285",
    "acas004",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.READ_INDEXED),
    ),
)


def slautogen_read_indexed(ctx: FacadeContext) -> StatusPair:
    """``SLautogen-Read-Indexed`` [copybooks/Proc-ACAS-FH-Calls.cob:L281-L285].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas004``.
    """
    return _perform(ctx, _E_SLAUTOGEN_READ_INDEXED)


_E_SLAUTOGEN_WRITE: Final[_Plan] = _Plan(
    "SLautogen-Write",
    "L287-L290",
    "acas004",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def slautogen_write(ctx: FacadeContext) -> StatusPair:
    """``SLautogen-Write`` [copybooks/Proc-ACAS-FH-Calls.cob:L287-L290].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas004``.
    """
    return _perform(ctx, _E_SLAUTOGEN_WRITE)


_E_SLAUTOGEN_REWRITE: Final[_Plan] = _Plan(
    "SLautogen-Rewrite",
    "L292-L295",
    "acas004",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def slautogen_rewrite(ctx: FacadeContext) -> StatusPair:
    """``SLautogen-Rewrite`` [copybooks/Proc-ACAS-FH-Calls.cob:L292-L295].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas004``.
    """
    return _perform(ctx, _E_SLAUTOGEN_REWRITE)


# --------------------------------------------------------------------------
# GL-Nominal -> acas005 -> GLLEDGER-REC
# --------------------------------------------------------------------------


_E_GL_NOMINAL_OPEN: Final[_Plan] = _Plan(
    "GL-Nominal-Open",
    "L299-L302",
    "acas005",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
)


def gl_nominal_open(ctx: FacadeContext) -> StatusPair:
    """``GL-Nominal-Open`` [copybooks/Proc-ACAS-FH-Calls.cob:L299-L302]."""
    return _perform(ctx, _E_GL_NOMINAL_OPEN)


_E_GL_NOMINAL_OPEN_INPUT: Final[_Plan] = _Plan(
    "GL-Nominal-Open-Input",
    "L304-L307",
    "acas005",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
)


def gl_nominal_open_input(ctx: FacadeContext) -> StatusPair:
    """``GL-Nominal-Open-Input`` [copybooks/Proc-ACAS-FH-Calls.cob:L304-L307]."""
    return _perform(ctx, _E_GL_NOMINAL_OPEN_INPUT)


_E_GL_NOMINAL_OPEN_OUTPUT: Final[_Plan] = _Plan(
    "GL-Nominal-Open-Output",
    "L309-L312",
    "acas005",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.OUTPUT),
    ),
)


def gl_nominal_open_output(ctx: FacadeContext) -> StatusPair:
    """``GL-Nominal-Open-Output`` [copybooks/Proc-ACAS-FH-Calls.cob:L309-L312]."""
    return _perform(ctx, _E_GL_NOMINAL_OPEN_OUTPUT)


_E_GL_NOMINAL_OPEN_EXTEND: Final[_Plan] = _Plan(
    "GL-Nominal-Open-Extend",
    "L314-L317",
    "acas005",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.EXTEND),
    ),
)


def gl_nominal_open_extend(ctx: FacadeContext) -> StatusPair:
    """``GL-Nominal-Open-Extend`` [copybooks/Proc-ACAS-FH-Calls.cob:L314-L317].

    Sets access type 4, marked "not valid for ISAM"
    [copybooks/wsfnctn.cob:L111], and no handler dispatches an extend access
    type on the relational path. Published and never satisfied.
    """
    return _perform(ctx, _E_GL_NOMINAL_OPEN_EXTEND)


_E_GL_NOMINAL_CLOSE: Final[_Plan] = _Plan(
    "GL-Nominal-Close",
    "L319-L322",
    "acas005",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def gl_nominal_close(ctx: FacadeContext) -> StatusPair:
    """``GL-Nominal-Close`` [copybooks/Proc-ACAS-FH-Calls.cob:L319-L322]."""
    return _perform(ctx, _E_GL_NOMINAL_CLOSE)


_E_GL_NOMINAL_DELETE: Final[_Plan] = _Plan(
    "GL-Nominal-Delete",
    "L324-L328",
    "acas005",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def gl_nominal_delete(ctx: FacadeContext) -> StatusPair:
    """``GL-Nominal-Delete`` [copybooks/Proc-ACAS-FH-Calls.cob:L324-L328]."""
    return _perform(ctx, _E_GL_NOMINAL_DELETE)


_E_GL_NOMINAL_START: Final[_Plan] = _Plan(
    "GL-Nominal-Start",
    "L330-L332",
    "acas005",
    (
        (_FILE_FUNCTION, FileFunction.START),
    ),
)


def gl_nominal_start(ctx: FacadeContext) -> StatusPair:
    """``GL-Nominal-Start`` [copybooks/Proc-ACAS-FH-Calls.cob:L330-L332].

    Deliberately does NOT clear ``Access-Type``: on a START that field
    carries the relation, 5 through 9 of [copybooks/wsfnctn.cob:L112-L116],
    and the caller sets it. Clearing it would change which row is found.
    """
    return _perform(ctx, _E_GL_NOMINAL_START)


_E_GL_NOMINAL_READ_NEXT: Final[_Plan] = _Plan(
    "GL-Nominal-Read-Next",
    "L334-L337",
    "acas005",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def gl_nominal_read_next(ctx: FacadeContext) -> StatusPair:
    """``GL-Nominal-Read-Next`` [copybooks/Proc-ACAS-FH-Calls.cob:L334-L337]."""
    return _perform(ctx, _E_GL_NOMINAL_READ_NEXT)


_E_GL_NOMINAL_READ_INDEXED: Final[_Plan] = _Plan(
    "GL-Nominal-Read-Indexed",
    "L339-L342",
    "acas005",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_INDEXED),
    ),
)


def gl_nominal_read_indexed(ctx: FacadeContext) -> StatusPair:
    """``GL-Nominal-Read-Indexed`` [copybooks/Proc-ACAS-FH-Calls.cob:L339-L342]."""
    return _perform(ctx, _E_GL_NOMINAL_READ_INDEXED)


_E_GL_NOMINAL_WRITE: Final[_Plan] = _Plan(
    "GL-Nominal-Write",
    "L344-L347",
    "acas005",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def gl_nominal_write(ctx: FacadeContext) -> StatusPair:
    """``GL-Nominal-Write`` [copybooks/Proc-ACAS-FH-Calls.cob:L344-L347]."""
    return _perform(ctx, _E_GL_NOMINAL_WRITE)


_E_GL_NOMINAL_REWRITE: Final[_Plan] = _Plan(
    "GL-Nominal-Rewrite",
    "L349-L352",
    "acas005",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def gl_nominal_rewrite(ctx: FacadeContext) -> StatusPair:
    """``GL-Nominal-Rewrite`` [copybooks/Proc-ACAS-FH-Calls.cob:L349-L352]."""
    return _perform(ctx, _E_GL_NOMINAL_REWRITE)


# --------------------------------------------------------------------------
# GL-Posting -> acas006 -> GLPOSTING-REC
# --------------------------------------------------------------------------


_E_GL_POSTING_OPEN: Final[_Plan] = _Plan(
    "GL-Posting-Open",
    "L356-L359",
    "acas006",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
)


def gl_posting_open(ctx: FacadeContext) -> StatusPair:
    """``GL-Posting-Open`` [copybooks/Proc-ACAS-FH-Calls.cob:L356-L359]."""
    return _perform(ctx, _E_GL_POSTING_OPEN)


_E_GL_POSTING_OPEN_INPUT: Final[_Plan] = _Plan(
    "GL-Posting-Open-Input",
    "L361-L364",
    "acas006",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
)


def gl_posting_open_input(ctx: FacadeContext) -> StatusPair:
    """``GL-Posting-Open-Input`` [copybooks/Proc-ACAS-FH-Calls.cob:L361-L364]."""
    return _perform(ctx, _E_GL_POSTING_OPEN_INPUT)


_E_GL_POSTING_OPEN_OUTPUT: Final[_Plan] = _Plan(
    "GL-Posting-Open-Output",
    "L366-L369",
    "acas006",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.OUTPUT),
    ),
)


def gl_posting_open_output(ctx: FacadeContext) -> StatusPair:
    """``GL-Posting-Open-Output`` [copybooks/Proc-ACAS-FH-Calls.cob:L366-L369]."""
    return _perform(ctx, _E_GL_POSTING_OPEN_OUTPUT)


_E_GL_POSTING_OPEN_EXTEND: Final[_Plan] = _Plan(
    "GL-Posting-Open-Extend",
    "L371-L374",
    "acas006",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.EXTEND),
    ),
)


def gl_posting_open_extend(ctx: FacadeContext) -> StatusPair:
    """``GL-Posting-Open-Extend`` [copybooks/Proc-ACAS-FH-Calls.cob:L371-L374].

    Sets access type 4, marked "not valid for ISAM"
    [copybooks/wsfnctn.cob:L111], and no handler dispatches an extend access
    type on the relational path. Published and never satisfied.
    """
    return _perform(ctx, _E_GL_POSTING_OPEN_EXTEND)


_E_GL_POSTING_CLOSE: Final[_Plan] = _Plan(
    "GL-Posting-Close",
    "L376-L379",
    "acas006",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def gl_posting_close(ctx: FacadeContext) -> StatusPair:
    """``GL-Posting-Close`` [copybooks/Proc-ACAS-FH-Calls.cob:L376-L379]."""
    return _perform(ctx, _E_GL_POSTING_CLOSE)


_E_GL_POSTING_DELETE: Final[_Plan] = _Plan(
    "GL-Posting-Delete",
    "L381-L385",
    "acas006",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def gl_posting_delete(ctx: FacadeContext) -> StatusPair:
    """``GL-Posting-Delete`` [copybooks/Proc-ACAS-FH-Calls.cob:L381-L385]."""
    return _perform(ctx, _E_GL_POSTING_DELETE)


_E_GL_POSTING_DELETE_ALL: Final[_Plan] = _Plan(
    "GL-Posting-Delete-All",
    "L387-L391",
    "acas006",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE_ALL),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def gl_posting_delete_all(ctx: FacadeContext) -> StatusPair:
    """``GL-Posting-Delete-All`` [copybooks/Proc-ACAS-FH-Calls.cob:L387-L391].

    Sets function code 6, which NO handler dispatches - every one routes
    it to ``when other`` and a bad-function reply
    [common/acasirsub4.cbl:L235]. Published and permanently unsatisfiable.
    The operation is real but reachable only through the open-output
    coercion [common/irspostingMT.cbl:L271-L272].
    """
    return _perform(ctx, _E_GL_POSTING_DELETE_ALL)


_E_GL_POSTING_START: Final[_Plan] = _Plan(
    "GL-Posting-Start",
    "L393-L395",
    "acas006",
    (
        (_FILE_FUNCTION, FileFunction.START),
    ),
)


def gl_posting_start(ctx: FacadeContext) -> StatusPair:
    """``GL-Posting-Start`` [copybooks/Proc-ACAS-FH-Calls.cob:L393-L395].

    Deliberately does NOT clear ``Access-Type``: on a START that field
    carries the relation, 5 through 9 of [copybooks/wsfnctn.cob:L112-L116],
    and the caller sets it. Clearing it would change which row is found.
    """
    return _perform(ctx, _E_GL_POSTING_START)


_E_GL_POSTING_READ_NEXT: Final[_Plan] = _Plan(
    "GL-Posting-Read-Next",
    "L397-L400",
    "acas006",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def gl_posting_read_next(ctx: FacadeContext) -> StatusPair:
    """``GL-Posting-Read-Next`` [copybooks/Proc-ACAS-FH-Calls.cob:L397-L400]."""
    return _perform(ctx, _E_GL_POSTING_READ_NEXT)


_E_GL_POSTING_READ_INDEXED: Final[_Plan] = _Plan(
    "GL-Posting-Read-Indexed",
    "L402-L405",
    "acas006",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_INDEXED),
    ),
)


def gl_posting_read_indexed(ctx: FacadeContext) -> StatusPair:
    """``GL-Posting-Read-Indexed`` [copybooks/Proc-ACAS-FH-Calls.cob:L402-L405]."""
    return _perform(ctx, _E_GL_POSTING_READ_INDEXED)


_E_GL_POSTING_WRITE: Final[_Plan] = _Plan(
    "GL-Posting-Write",
    "L407-L410",
    "acas006",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def gl_posting_write(ctx: FacadeContext) -> StatusPair:
    """``GL-Posting-Write`` [copybooks/Proc-ACAS-FH-Calls.cob:L407-L410]."""
    return _perform(ctx, _E_GL_POSTING_WRITE)


_E_GL_POSTING_REWRITE: Final[_Plan] = _Plan(
    "GL-Posting-Rewrite",
    "L412-L415",
    "acas006",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def gl_posting_rewrite(ctx: FacadeContext) -> StatusPair:
    """``GL-Posting-Rewrite`` [copybooks/Proc-ACAS-FH-Calls.cob:L412-L415]."""
    return _perform(ctx, _E_GL_POSTING_REWRITE)


# --------------------------------------------------------------------------
# GL-Batch -> acas007 -> GLBATCH-REC
# --------------------------------------------------------------------------


_E_GL_BATCH_OPEN: Final[_Plan] = _Plan(
    "GL-Batch-Open",
    "L419-L422",
    "acas007",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
)


def gl_batch_open(ctx: FacadeContext) -> StatusPair:
    """``GL-Batch-Open`` [copybooks/Proc-ACAS-FH-Calls.cob:L419-L422]."""
    return _perform(ctx, _E_GL_BATCH_OPEN)


_E_GL_BATCH_OPEN_INPUT: Final[_Plan] = _Plan(
    "GL-Batch-Open-Input",
    "L424-L427",
    "acas007",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
)


def gl_batch_open_input(ctx: FacadeContext) -> StatusPair:
    """``GL-Batch-Open-Input`` [copybooks/Proc-ACAS-FH-Calls.cob:L424-L427]."""
    return _perform(ctx, _E_GL_BATCH_OPEN_INPUT)


_E_GL_BATCH_OPEN_OUTPUT: Final[_Plan] = _Plan(
    "GL-Batch-Open-Output",
    "L429-L432",
    "acas007",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.OUTPUT),
    ),
)


def gl_batch_open_output(ctx: FacadeContext) -> StatusPair:
    """``GL-Batch-Open-Output`` [copybooks/Proc-ACAS-FH-Calls.cob:L429-L432]."""
    return _perform(ctx, _E_GL_BATCH_OPEN_OUTPUT)


_E_GL_BATCH_OPEN_EXTEND: Final[_Plan] = _Plan(
    "GL-Batch-Open-Extend",
    "L434-L437",
    "acas007",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.EXTEND),
    ),
)


def gl_batch_open_extend(ctx: FacadeContext) -> StatusPair:
    """``GL-Batch-Open-Extend`` [copybooks/Proc-ACAS-FH-Calls.cob:L434-L437].

    Sets access type 4, marked "not valid for ISAM"
    [copybooks/wsfnctn.cob:L111], and no handler dispatches an extend access
    type on the relational path. Published and never satisfied.
    """
    return _perform(ctx, _E_GL_BATCH_OPEN_EXTEND)


_E_GL_BATCH_CLOSE: Final[_Plan] = _Plan(
    "GL-Batch-Close",
    "L439-L442",
    "acas007",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def gl_batch_close(ctx: FacadeContext) -> StatusPair:
    """``GL-Batch-Close`` [copybooks/Proc-ACAS-FH-Calls.cob:L439-L442]."""
    return _perform(ctx, _E_GL_BATCH_CLOSE)


_E_GL_BATCH_DELETE: Final[_Plan] = _Plan(
    "GL-Batch-Delete",
    "L444-L448",
    "acas007",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def gl_batch_delete(ctx: FacadeContext) -> StatusPair:
    """``GL-Batch-Delete`` [copybooks/Proc-ACAS-FH-Calls.cob:L444-L448]."""
    return _perform(ctx, _E_GL_BATCH_DELETE)


_E_GL_BATCH_DELETE_ALL: Final[_Plan] = _Plan(
    "GL-Batch-Delete-All",
    "L450-L454",
    "acas007",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE_ALL),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def gl_batch_delete_all(ctx: FacadeContext) -> StatusPair:
    """``GL-Batch-Delete-All`` [copybooks/Proc-ACAS-FH-Calls.cob:L450-L454].

    Sets function code 6, which NO handler dispatches - every one routes
    it to ``when other`` and a bad-function reply
    [common/acasirsub4.cbl:L235]. Published and permanently unsatisfiable.
    The operation is real but reachable only through the open-output
    coercion [common/irspostingMT.cbl:L271-L272].
    """
    return _perform(ctx, _E_GL_BATCH_DELETE_ALL)


_E_GL_BATCH_START: Final[_Plan] = _Plan(
    "GL-Batch-Start",
    "L456-L458",
    "acas007",
    (
        (_FILE_FUNCTION, FileFunction.START),
    ),
)


def gl_batch_start(ctx: FacadeContext) -> StatusPair:
    """``GL-Batch-Start`` [copybooks/Proc-ACAS-FH-Calls.cob:L456-L458].

    Deliberately does NOT clear ``Access-Type``: on a START that field
    carries the relation, 5 through 9 of [copybooks/wsfnctn.cob:L112-L116],
    and the caller sets it. Clearing it would change which row is found.
    """
    return _perform(ctx, _E_GL_BATCH_START)


_E_GL_BATCH_READ_NEXT: Final[_Plan] = _Plan(
    "GL-Batch-Read-Next",
    "L460-L463",
    "acas007",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def gl_batch_read_next(ctx: FacadeContext) -> StatusPair:
    """``GL-Batch-Read-Next`` [copybooks/Proc-ACAS-FH-Calls.cob:L460-L463]."""
    return _perform(ctx, _E_GL_BATCH_READ_NEXT)


_E_GL_BATCH_READ_INDEXED: Final[_Plan] = _Plan(
    "GL-Batch-Read-Indexed",
    "L465-L468",
    "acas007",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_INDEXED),
    ),
)


def gl_batch_read_indexed(ctx: FacadeContext) -> StatusPair:
    """``GL-Batch-Read-Indexed`` [copybooks/Proc-ACAS-FH-Calls.cob:L465-L468]."""
    return _perform(ctx, _E_GL_BATCH_READ_INDEXED)


_E_GL_BATCH_WRITE: Final[_Plan] = _Plan(
    "GL-Batch-Write",
    "L470-L473",
    "acas007",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def gl_batch_write(ctx: FacadeContext) -> StatusPair:
    """``GL-Batch-Write`` [copybooks/Proc-ACAS-FH-Calls.cob:L470-L473]."""
    return _perform(ctx, _E_GL_BATCH_WRITE)


_E_GL_BATCH_REWRITE: Final[_Plan] = _Plan(
    "GL-Batch-Rewrite",
    "L475-L478",
    "acas007",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def gl_batch_rewrite(ctx: FacadeContext) -> StatusPair:
    """``GL-Batch-Rewrite`` [copybooks/Proc-ACAS-FH-Calls.cob:L475-L478]."""
    return _perform(ctx, _E_GL_BATCH_REWRITE)


# --------------------------------------------------------------------------
# SPL-Posting -> acas008 -> PSIRSPOST-REC
# --------------------------------------------------------------------------


_E_SPL_POSTING_OPEN: Final[_Plan] = _Plan(
    "SPL-Posting-Open",
    "L482-L485",
    "acas008",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
)


def spl_posting_open(ctx: FacadeContext) -> StatusPair:
    """``SPL-Posting-Open`` [copybooks/Proc-ACAS-FH-Calls.cob:L482-L485]."""
    return _perform(ctx, _E_SPL_POSTING_OPEN)


_E_SPL_POSTING_OPEN_INPUT: Final[_Plan] = _Plan(
    "SPL-Posting-Open-Input",
    "L487-L490",
    "acas008",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
)


def spl_posting_open_input(ctx: FacadeContext) -> StatusPair:
    """``SPL-Posting-Open-Input`` [copybooks/Proc-ACAS-FH-Calls.cob:L487-L490]."""
    return _perform(ctx, _E_SPL_POSTING_OPEN_INPUT)


_E_SPL_POSTING_OPEN_OUTPUT: Final[_Plan] = _Plan(
    "SPL-Posting-Open-Output",
    "L492-L495",
    "acas008",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.OUTPUT),
    ),
)


def spl_posting_open_output(ctx: FacadeContext) -> StatusPair:
    """``SPL-Posting-Open-Output`` [copybooks/Proc-ACAS-FH-Calls.cob:L492-L495].

    On the transfer file an open for output means DELETE EVERY ROW: the
    handler replaces the function at entry [common/acas008.cbl:L313-L319]
    and [common/acas008.cbl:L571-L574]. This is how the end-of-job clear in
    [irs/irs030.cbl:L1720-L1724] is implemented. This function sets the open
    function and the output access type and dispatches, exactly as the
    copybook does; the handler performs the coercion.
    """
    return _perform(ctx, _E_SPL_POSTING_OPEN_OUTPUT)


_E_SPL_POSTING_OPEN_EXTEND: Final[_Plan] = _Plan(
    "SPL-Posting-Open-Extend",
    "L497-L500",
    "acas008",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.EXTEND),
    ),
)


def spl_posting_open_extend(ctx: FacadeContext) -> StatusPair:
    """``SPL-Posting-Open-Extend`` [copybooks/Proc-ACAS-FH-Calls.cob:L497-L500].

    Sets access type 4, marked "not valid for ISAM"
    [copybooks/wsfnctn.cob:L111], and no handler dispatches an extend access
    type on the relational path. Published and never satisfied.
    """
    return _perform(ctx, _E_SPL_POSTING_OPEN_EXTEND)


_E_SPL_POSTING_CLOSE: Final[_Plan] = _Plan(
    "SPL-Posting-Close",
    "L502-L505",
    "acas008",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def spl_posting_close(ctx: FacadeContext) -> StatusPair:
    """``SPL-Posting-Close`` [copybooks/Proc-ACAS-FH-Calls.cob:L502-L505]."""
    return _perform(ctx, _E_SPL_POSTING_CLOSE)


_E_SPL_POSTING_DELETE: Final[_Plan] = _Plan(
    "SPL-Posting-Delete",
    "L507-L511",
    "acas008",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def spl_posting_delete(ctx: FacadeContext) -> StatusPair:
    """``SPL-Posting-Delete`` [copybooks/Proc-ACAS-FH-Calls.cob:L507-L511].

    ``acas008`` refuses this function unconditionally at entry
    [common/acas008.cbl:L299-L307], because the transfer file is sequential,
    and answers ``FS-Reply`` 99 with ``WE-Error`` 988. Published and
    guaranteed to fail. The handler-named convention publishes only one of
    the four it refuses, which is why Agent Action Plan section 0.6.7 entry 6
    singles rewrite out.
    """
    return _perform(ctx, _E_SPL_POSTING_DELETE)


_E_SPL_POSTING_DELETE_ALL: Final[_Plan] = _Plan(
    "SPL-Posting-Delete-All",
    "L513-L517",
    "acas008",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE_ALL),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def spl_posting_delete_all(ctx: FacadeContext) -> StatusPair:
    """``SPL-Posting-Delete-All`` [copybooks/Proc-ACAS-FH-Calls.cob:L513-L517].

    Sets function code 6, which NO handler dispatches - every one routes
    it to ``when other`` and a bad-function reply
    [common/acasirsub4.cbl:L235]. Published and permanently unsatisfiable.
    The operation is real but reachable only through the open-output
    coercion [common/irspostingMT.cbl:L271-L272].
    """
    return _perform(ctx, _E_SPL_POSTING_DELETE_ALL)


_E_SPL_POSTING_START: Final[_Plan] = _Plan(
    "SPL-Posting-Start",
    "L519-L521",
    "acas008",
    (
        (_FILE_FUNCTION, FileFunction.START),
    ),
)


def spl_posting_start(ctx: FacadeContext) -> StatusPair:
    """``SPL-Posting-Start`` [copybooks/Proc-ACAS-FH-Calls.cob:L519-L521].

    Deliberately does NOT clear ``Access-Type``: on a START that field
    carries the relation, 5 through 9 of [copybooks/wsfnctn.cob:L112-L116],
    and the caller sets it. Clearing it would change which row is found.

    ``acas008`` refuses this function unconditionally at entry
    [common/acas008.cbl:L299-L307], because the transfer file is sequential,
    and answers ``FS-Reply`` 99 with ``WE-Error`` 988. Published and
    guaranteed to fail. The handler-named convention publishes only one of
    the four it refuses, which is why Agent Action Plan section 0.6.7 entry 6
    singles rewrite out.
    """
    return _perform(ctx, _E_SPL_POSTING_START)


_E_SPL_POSTING_READ_NEXT: Final[_Plan] = _Plan(
    "SPL-Posting-Read-Next",
    "L523-L526",
    "acas008",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def spl_posting_read_next(ctx: FacadeContext) -> StatusPair:
    """``SPL-Posting-Read-Next`` [copybooks/Proc-ACAS-FH-Calls.cob:L523-L526]."""
    return _perform(ctx, _E_SPL_POSTING_READ_NEXT)


_E_SPL_POSTING_READ_INDEXED: Final[_Plan] = _Plan(
    "SPL-Posting-Read-Indexed",
    "L528-L531",
    "acas008",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_INDEXED),
    ),
)


def spl_posting_read_indexed(ctx: FacadeContext) -> StatusPair:
    """``SPL-Posting-Read-Indexed`` [copybooks/Proc-ACAS-FH-Calls.cob:L528-L531].

    ``acas008`` refuses this function unconditionally at entry
    [common/acas008.cbl:L299-L307], because the transfer file is sequential,
    and answers ``FS-Reply`` 99 with ``WE-Error`` 988. Published and
    guaranteed to fail. The handler-named convention publishes only one of
    the four it refuses, which is why Agent Action Plan section 0.6.7 entry 6
    singles rewrite out.
    """
    return _perform(ctx, _E_SPL_POSTING_READ_INDEXED)


_E_SPL_POSTING_WRITE: Final[_Plan] = _Plan(
    "SPL-Posting-Write",
    "L533-L536",
    "acas008",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def spl_posting_write(ctx: FacadeContext) -> StatusPair:
    """``SPL-Posting-Write`` [copybooks/Proc-ACAS-FH-Calls.cob:L533-L536]."""
    return _perform(ctx, _E_SPL_POSTING_WRITE)


_E_SPL_POSTING_REWRITE: Final[_Plan] = _Plan(
    "SPL-Posting-Rewrite",
    "L538-L541",
    "acas008",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def spl_posting_rewrite(ctx: FacadeContext) -> StatusPair:
    """``SPL-Posting-Rewrite`` [copybooks/Proc-ACAS-FH-Calls.cob:L538-L541].

    ``acas008`` refuses this function unconditionally at entry
    [common/acas008.cbl:L299-L307], because the transfer file is sequential,
    and answers ``FS-Reply`` 99 with ``WE-Error`` 988. Published and
    guaranteed to fail. The handler-named convention publishes only one of
    the four it refuses, which is why Agent Action Plan section 0.6.7 entry 6
    singles rewrite out.
    """
    return _perform(ctx, _E_SPL_POSTING_REWRITE)


# --------------------------------------------------------------------------
# Stock-Audit -> acas010 -> OUT OF SCOPE per Agent Action Plan section 0.2.2
# --------------------------------------------------------------------------


_E_STOCK_AUDIT_OPEN: Final[_Plan] = _Plan(
    "Stock-Audit-Open",
    "L545-L548",
    "acas010",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
)


def stock_audit_open(ctx: FacadeContext) -> StatusPair:
    """``Stock-Audit-Open`` [copybooks/Proc-ACAS-FH-Calls.cob:L545-L548].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas010``.
    """
    return _perform(ctx, _E_STOCK_AUDIT_OPEN)


_E_STOCK_AUDIT_OPEN_INPUT: Final[_Plan] = _Plan(
    "Stock-Audit-Open-Input",
    "L550-L553",
    "acas010",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
)


def stock_audit_open_input(ctx: FacadeContext) -> StatusPair:
    """``Stock-Audit-Open-Input`` [copybooks/Proc-ACAS-FH-Calls.cob:L550-L553].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas010``.
    """
    return _perform(ctx, _E_STOCK_AUDIT_OPEN_INPUT)


_E_STOCK_AUDIT_OPEN_OUTPUT: Final[_Plan] = _Plan(
    "Stock-Audit-Open-Output",
    "L555-L558",
    "acas010",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.OUTPUT),
    ),
)


def stock_audit_open_output(ctx: FacadeContext) -> StatusPair:
    """``Stock-Audit-Open-Output`` [copybooks/Proc-ACAS-FH-Calls.cob:L555-L558].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas010``.
    """
    return _perform(ctx, _E_STOCK_AUDIT_OPEN_OUTPUT)


_E_STOCK_AUDIT_OPEN_EXTEND: Final[_Plan] = _Plan(
    "Stock-Audit-Open-Extend",
    "L560-L563",
    "acas010",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.EXTEND),
    ),
)


def stock_audit_open_extend(ctx: FacadeContext) -> StatusPair:
    """``Stock-Audit-Open-Extend`` [copybooks/Proc-ACAS-FH-Calls.cob:L560-L563].

    Sets access type 4, marked "not valid for ISAM"
    [copybooks/wsfnctn.cob:L111], and no handler dispatches an extend access
    type on the relational path. Published and never satisfied.

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas010``.
    """
    return _perform(ctx, _E_STOCK_AUDIT_OPEN_EXTEND)


_E_STOCK_AUDIT_CLOSE: Final[_Plan] = _Plan(
    "Stock-Audit-Close",
    "L565-L568",
    "acas010",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def stock_audit_close(ctx: FacadeContext) -> StatusPair:
    """``Stock-Audit-Close`` [copybooks/Proc-ACAS-FH-Calls.cob:L565-L568].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas010``.
    """
    return _perform(ctx, _E_STOCK_AUDIT_CLOSE)


_E_STOCK_AUDIT_DELETE: Final[_Plan] = _Plan(
    "Stock-Audit-Delete",
    "L570-L574",
    "acas010",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def stock_audit_delete(ctx: FacadeContext) -> StatusPair:
    """``Stock-Audit-Delete`` [copybooks/Proc-ACAS-FH-Calls.cob:L570-L574].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas010``.
    """
    return _perform(ctx, _E_STOCK_AUDIT_DELETE)


_E_STOCK_AUDIT_START: Final[_Plan] = _Plan(
    "Stock-Audit-Start",
    "L576-L578",
    "acas010",
    (
        (_FILE_FUNCTION, FileFunction.START),
    ),
)


def stock_audit_start(ctx: FacadeContext) -> StatusPair:
    """``Stock-Audit-Start`` [copybooks/Proc-ACAS-FH-Calls.cob:L576-L578].

    Deliberately does NOT clear ``Access-Type``: on a START that field
    carries the relation, 5 through 9 of [copybooks/wsfnctn.cob:L112-L116],
    and the caller sets it. Clearing it would change which row is found.

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas010``.
    """
    return _perform(ctx, _E_STOCK_AUDIT_START)


_E_STOCK_AUDIT_READ_NEXT: Final[_Plan] = _Plan(
    "Stock-Audit-Read-Next",
    "L580-L583",
    "acas010",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def stock_audit_read_next(ctx: FacadeContext) -> StatusPair:
    """``Stock-Audit-Read-Next`` [copybooks/Proc-ACAS-FH-Calls.cob:L580-L583].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas010``.
    """
    return _perform(ctx, _E_STOCK_AUDIT_READ_NEXT)


_E_STOCK_AUDIT_READ_INDEXED: Final[_Plan] = _Plan(
    "Stock-Audit-Read-Indexed",
    "L585-L588",
    "acas010",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_INDEXED),
    ),
)


def stock_audit_read_indexed(ctx: FacadeContext) -> StatusPair:
    """``Stock-Audit-Read-Indexed`` [copybooks/Proc-ACAS-FH-Calls.cob:L585-L588].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas010``.
    """
    return _perform(ctx, _E_STOCK_AUDIT_READ_INDEXED)


_E_STOCK_AUDIT_WRITE: Final[_Plan] = _Plan(
    "Stock-Audit-Write",
    "L590-L593",
    "acas010",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def stock_audit_write(ctx: FacadeContext) -> StatusPair:
    """``Stock-Audit-Write`` [copybooks/Proc-ACAS-FH-Calls.cob:L590-L593].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas010``.
    """
    return _perform(ctx, _E_STOCK_AUDIT_WRITE)


_E_STOCK_AUDIT_REWRITE: Final[_Plan] = _Plan(
    "Stock-Audit-Rewrite",
    "L595-L598",
    "acas010",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def stock_audit_rewrite(ctx: FacadeContext) -> StatusPair:
    """``Stock-Audit-Rewrite`` [copybooks/Proc-ACAS-FH-Calls.cob:L595-L598].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas010``.
    """
    return _perform(ctx, _E_STOCK_AUDIT_REWRITE)


# --------------------------------------------------------------------------
# Stock -> acas011 -> OUT OF SCOPE per Agent Action Plan section 0.2.2
# --------------------------------------------------------------------------


_E_STOCK_OPEN: Final[_Plan] = _Plan(
    "Stock-Open",
    "L602-L605",
    "acas011",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
)


def stock_open(ctx: FacadeContext) -> StatusPair:
    """``Stock-Open`` [copybooks/Proc-ACAS-FH-Calls.cob:L602-L605].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas011``.
    """
    return _perform(ctx, _E_STOCK_OPEN)


_E_STOCK_OPEN_INPUT: Final[_Plan] = _Plan(
    "Stock-Open-Input",
    "L607-L610",
    "acas011",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
)


def stock_open_input(ctx: FacadeContext) -> StatusPair:
    """``Stock-Open-Input`` [copybooks/Proc-ACAS-FH-Calls.cob:L607-L610].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas011``.
    """
    return _perform(ctx, _E_STOCK_OPEN_INPUT)


_E_STOCK_OPEN_OUTPUT: Final[_Plan] = _Plan(
    "Stock-Open-Output",
    "L612-L615",
    "acas011",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.OUTPUT),
    ),
)


def stock_open_output(ctx: FacadeContext) -> StatusPair:
    """``Stock-Open-Output`` [copybooks/Proc-ACAS-FH-Calls.cob:L612-L615].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas011``.
    """
    return _perform(ctx, _E_STOCK_OPEN_OUTPUT)


_E_STOCK_CLOSE: Final[_Plan] = _Plan(
    "Stock-Close",
    "L617-L620",
    "acas011",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def stock_close(ctx: FacadeContext) -> StatusPair:
    """``Stock-Close`` [copybooks/Proc-ACAS-FH-Calls.cob:L617-L620].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas011``.
    """
    return _perform(ctx, _E_STOCK_CLOSE)


_E_STOCK_DELETE: Final[_Plan] = _Plan(
    "Stock-Delete",
    "L622-L626",
    "acas011",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def stock_delete(ctx: FacadeContext) -> StatusPair:
    """``Stock-Delete`` [copybooks/Proc-ACAS-FH-Calls.cob:L622-L626].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas011``.
    """
    return _perform(ctx, _E_STOCK_DELETE)


_E_STOCK_START: Final[_Plan] = _Plan(
    "Stock-Start",
    "L628-L630",
    "acas011",
    (
        (_FILE_FUNCTION, FileFunction.START),
    ),
)


def stock_start(ctx: FacadeContext) -> StatusPair:
    """``Stock-Start`` [copybooks/Proc-ACAS-FH-Calls.cob:L628-L630].

    Deliberately does NOT clear ``Access-Type``: on a START that field
    carries the relation, 5 through 9 of [copybooks/wsfnctn.cob:L112-L116],
    and the caller sets it. Clearing it would change which row is found.

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas011``.
    """
    return _perform(ctx, _E_STOCK_START)


_E_STOCK_READ_NEXT: Final[_Plan] = _Plan(
    "Stock-Read-Next",
    "L632-L635",
    "acas011",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def stock_read_next(ctx: FacadeContext) -> StatusPair:
    """``Stock-Read-Next`` [copybooks/Proc-ACAS-FH-Calls.cob:L632-L635].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas011``.
    """
    return _perform(ctx, _E_STOCK_READ_NEXT)


_E_STOCK_READ_INDEXED: Final[_Plan] = _Plan(
    "Stock-Read-Indexed",
    "L637-L640",
    "acas011",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_INDEXED),
    ),
)


def stock_read_indexed(ctx: FacadeContext) -> StatusPair:
    """``Stock-Read-Indexed`` [copybooks/Proc-ACAS-FH-Calls.cob:L637-L640].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas011``.
    """
    return _perform(ctx, _E_STOCK_READ_INDEXED)


_E_STOCK_WRITE: Final[_Plan] = _Plan(
    "Stock-Write",
    "L642-L645",
    "acas011",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def stock_write(ctx: FacadeContext) -> StatusPair:
    """``Stock-Write`` [copybooks/Proc-ACAS-FH-Calls.cob:L642-L645].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas011``.
    """
    return _perform(ctx, _E_STOCK_WRITE)


_E_STOCK_REWRITE: Final[_Plan] = _Plan(
    "Stock-Rewrite",
    "L647-L650",
    "acas011",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def stock_rewrite(ctx: FacadeContext) -> StatusPair:
    """``Stock-Rewrite`` [copybooks/Proc-ACAS-FH-Calls.cob:L647-L650].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas011``.
    """
    return _perform(ctx, _E_STOCK_REWRITE)


# --------------------------------------------------------------------------
# Sales -> acas012 -> SALEDGER-REC
# --------------------------------------------------------------------------


_E_SALES_OPEN: Final[_Plan] = _Plan(
    "Sales-Open",
    "L654-L657",
    "acas012",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
)


def sales_open(ctx: FacadeContext) -> StatusPair:
    """``Sales-Open`` [copybooks/Proc-ACAS-FH-Calls.cob:L654-L657]."""
    return _perform(ctx, _E_SALES_OPEN)


_E_SALES_OPEN_INPUT: Final[_Plan] = _Plan(
    "Sales-Open-Input",
    "L659-L662",
    "acas012",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
)


def sales_open_input(ctx: FacadeContext) -> StatusPair:
    """``Sales-Open-Input`` [copybooks/Proc-ACAS-FH-Calls.cob:L659-L662]."""
    return _perform(ctx, _E_SALES_OPEN_INPUT)


_E_SALES_OPEN_OUTPUT: Final[_Plan] = _Plan(
    "Sales-Open-Output",
    "L664-L667",
    "acas012",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.OUTPUT),
    ),
)


def sales_open_output(ctx: FacadeContext) -> StatusPair:
    """``Sales-Open-Output`` [copybooks/Proc-ACAS-FH-Calls.cob:L664-L667]."""
    return _perform(ctx, _E_SALES_OPEN_OUTPUT)


_E_SALES_CLOSE: Final[_Plan] = _Plan(
    "Sales-Close",
    "L669-L672",
    "acas012",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def sales_close(ctx: FacadeContext) -> StatusPair:
    """``Sales-Close`` [copybooks/Proc-ACAS-FH-Calls.cob:L669-L672]."""
    return _perform(ctx, _E_SALES_CLOSE)


_E_SALES_DELETE: Final[_Plan] = _Plan(
    "Sales-Delete",
    "L674-L678",
    "acas012",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def sales_delete(ctx: FacadeContext) -> StatusPair:
    """``Sales-Delete`` [copybooks/Proc-ACAS-FH-Calls.cob:L674-L678]."""
    return _perform(ctx, _E_SALES_DELETE)


_E_SALES_START: Final[_Plan] = _Plan(
    "Sales-Start",
    "L680-L682",
    "acas012",
    (
        (_FILE_FUNCTION, FileFunction.START),
    ),
)


def sales_start(ctx: FacadeContext) -> StatusPair:
    """``Sales-Start`` [copybooks/Proc-ACAS-FH-Calls.cob:L680-L682].

    Deliberately does NOT clear ``Access-Type``: on a START that field
    carries the relation, 5 through 9 of [copybooks/wsfnctn.cob:L112-L116],
    and the caller sets it. Clearing it would change which row is found.
    """
    return _perform(ctx, _E_SALES_START)


_E_SALES_READ_NEXT: Final[_Plan] = _Plan(
    "Sales-Read-Next",
    "L684-L687",
    "acas012",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def sales_read_next(ctx: FacadeContext) -> StatusPair:
    """``Sales-Read-Next`` [copybooks/Proc-ACAS-FH-Calls.cob:L684-L687]."""
    return _perform(ctx, _E_SALES_READ_NEXT)


_E_SALES_READ_NEXT_SORTED_BY_NAME: Final[_Plan] = _Plan(
    "Sales-Read-Next-Sorted-By-Name",
    "L689-L692",
    "acas012",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_BY_NAME),
    ),
)


def sales_read_next_sorted_by_name(ctx: FacadeContext) -> StatusPair:
    """``Sales-Read-Next-Sorted-By-Name`` [copybooks/Proc-ACAS-FH-Calls.cob:L689-L692].

    Sets function code 31, which ``acas012`` does dispatch
    [common/acas012.cbl:L342]. Note the spelling: this one hyphenates
    ``By-Name`` where the Purch equivalent writes ``ByName``.
    """
    return _perform(ctx, _E_SALES_READ_NEXT_SORTED_BY_NAME)


_E_SALES_READ_INDEXED: Final[_Plan] = _Plan(
    "Sales-Read-Indexed",
    "L694-L697",
    "acas012",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_INDEXED),
    ),
)


def sales_read_indexed(ctx: FacadeContext) -> StatusPair:
    """``Sales-Read-Indexed`` [copybooks/Proc-ACAS-FH-Calls.cob:L694-L697]."""
    return _perform(ctx, _E_SALES_READ_INDEXED)


_E_SALES_WRITE: Final[_Plan] = _Plan(
    "Sales-Write",
    "L699-L702",
    "acas012",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def sales_write(ctx: FacadeContext) -> StatusPair:
    """``Sales-Write`` [copybooks/Proc-ACAS-FH-Calls.cob:L699-L702]."""
    return _perform(ctx, _E_SALES_WRITE)


_E_SALES_REWRITE: Final[_Plan] = _Plan(
    "Sales-Rewrite",
    "L704-L707",
    "acas012",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def sales_rewrite(ctx: FacadeContext) -> StatusPair:
    """``Sales-Rewrite`` [copybooks/Proc-ACAS-FH-Calls.cob:L704-L707]."""
    return _perform(ctx, _E_SALES_REWRITE)


# --------------------------------------------------------------------------
# Value -> acas013 -> VALUEANAL-REC
# --------------------------------------------------------------------------


_E_VALUE_OPEN: Final[_Plan] = _Plan(
    "Value-Open",
    "L711-L714",
    "acas013",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
)


def value_open(ctx: FacadeContext) -> StatusPair:
    """``Value-Open`` [copybooks/Proc-ACAS-FH-Calls.cob:L711-L714]."""
    return _perform(ctx, _E_VALUE_OPEN)


_E_VALUE_OPEN_INPUT: Final[_Plan] = _Plan(
    "Value-Open-Input",
    "L716-L719",
    "acas013",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
)


def value_open_input(ctx: FacadeContext) -> StatusPair:
    """``Value-Open-Input`` [copybooks/Proc-ACAS-FH-Calls.cob:L716-L719]."""
    return _perform(ctx, _E_VALUE_OPEN_INPUT)


_E_VALUE_OPEN_OUTPUT: Final[_Plan] = _Plan(
    "Value-Open-Output",
    "L721-L724",
    "acas013",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.OUTPUT),
    ),
)


def value_open_output(ctx: FacadeContext) -> StatusPair:
    """``Value-Open-Output`` [copybooks/Proc-ACAS-FH-Calls.cob:L721-L724]."""
    return _perform(ctx, _E_VALUE_OPEN_OUTPUT)


_E_VALUE_CLOSE: Final[_Plan] = _Plan(
    "Value-Close",
    "L726-L729",
    "acas013",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def value_close(ctx: FacadeContext) -> StatusPair:
    """``Value-Close`` [copybooks/Proc-ACAS-FH-Calls.cob:L726-L729]."""
    return _perform(ctx, _E_VALUE_CLOSE)


_E_VALUE_DELETE: Final[_Plan] = _Plan(
    "Value-Delete",
    "L731-L735",
    "acas013",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def value_delete(ctx: FacadeContext) -> StatusPair:
    """``Value-Delete`` [copybooks/Proc-ACAS-FH-Calls.cob:L731-L735]."""
    return _perform(ctx, _E_VALUE_DELETE)


_E_VALUE_DELETE_ALL: Final[_Plan] = _Plan(
    "Value-Delete-All",
    "L737-L741",
    "acas013",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE_ALL),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def value_delete_all(ctx: FacadeContext) -> StatusPair:
    """``Value-Delete-All`` [copybooks/Proc-ACAS-FH-Calls.cob:L737-L741].

    Sets function code 6, which NO handler dispatches - every one routes
    it to ``when other`` and a bad-function reply
    [common/acasirsub4.cbl:L235]. Published and permanently unsatisfiable.
    The operation is real but reachable only through the open-output
    coercion [common/irspostingMT.cbl:L271-L272].
    """
    return _perform(ctx, _E_VALUE_DELETE_ALL)


_E_VALUE_START: Final[_Plan] = _Plan(
    "Value-Start",
    "L743-L746",
    "acas013",
    (
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.START),
    ),
)


def value_start(ctx: FacadeContext) -> StatusPair:
    """``Value-Start`` [copybooks/Proc-ACAS-FH-Calls.cob:L743-L746].

    Deliberately does NOT clear ``Access-Type``: on a START that field
    carries the relation, 5 through 9 of [copybooks/wsfnctn.cob:L112-L116],
    and the caller sets it. Clearing it would change which row is found.
    """
    return _perform(ctx, _E_VALUE_START)


_E_VALUE_READ_NEXT: Final[_Plan] = _Plan(
    "Value-Read-Next",
    "L748-L751",
    "acas013",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def value_read_next(ctx: FacadeContext) -> StatusPair:
    """``Value-Read-Next`` [copybooks/Proc-ACAS-FH-Calls.cob:L748-L751]."""
    return _perform(ctx, _E_VALUE_READ_NEXT)


_E_VALUE_READ_INDEXED: Final[_Plan] = _Plan(
    "Value-Read-Indexed",
    "L753-L757",
    "acas013",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.READ_INDEXED),
    ),
)


def value_read_indexed(ctx: FacadeContext) -> StatusPair:
    """``Value-Read-Indexed`` [copybooks/Proc-ACAS-FH-Calls.cob:L753-L757]."""
    return _perform(ctx, _E_VALUE_READ_INDEXED)


_E_VALUE_WRITE: Final[_Plan] = _Plan(
    "Value-Write",
    "L759-L762",
    "acas013",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def value_write(ctx: FacadeContext) -> StatusPair:
    """``Value-Write`` [copybooks/Proc-ACAS-FH-Calls.cob:L759-L762]."""
    return _perform(ctx, _E_VALUE_WRITE)


_E_VALUE_REWRITE: Final[_Plan] = _Plan(
    "Value-Rewrite",
    "L764-L767",
    "acas013",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def value_rewrite(ctx: FacadeContext) -> StatusPair:
    """``Value-Rewrite`` [copybooks/Proc-ACAS-FH-Calls.cob:L764-L767]."""
    return _perform(ctx, _E_VALUE_REWRITE)


# --------------------------------------------------------------------------
# Delivery -> acas014 -> OUT OF SCOPE per Agent Action Plan section 0.2.2
# --------------------------------------------------------------------------


_E_DELIVERY_OPEN: Final[_Plan] = _Plan(
    "Delivery-Open",
    "L771-L774",
    "acas014",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
)


def delivery_open(ctx: FacadeContext) -> StatusPair:
    """``Delivery-Open`` [copybooks/Proc-ACAS-FH-Calls.cob:L771-L774].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas014``.
    """
    return _perform(ctx, _E_DELIVERY_OPEN)


_E_DELIVERY_OPEN_INPUT: Final[_Plan] = _Plan(
    "Delivery-Open-Input",
    "L776-L779",
    "acas014",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
)


def delivery_open_input(ctx: FacadeContext) -> StatusPair:
    """``Delivery-Open-Input`` [copybooks/Proc-ACAS-FH-Calls.cob:L776-L779].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas014``.
    """
    return _perform(ctx, _E_DELIVERY_OPEN_INPUT)


_E_DELIVERY_OPEN_OUTPUT: Final[_Plan] = _Plan(
    "Delivery-Open-Output",
    "L781-L784",
    "acas014",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.OUTPUT),
    ),
)


def delivery_open_output(ctx: FacadeContext) -> StatusPair:
    """``Delivery-Open-Output`` [copybooks/Proc-ACAS-FH-Calls.cob:L781-L784].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas014``.
    """
    return _perform(ctx, _E_DELIVERY_OPEN_OUTPUT)


_E_DELIVERY_CLOSE: Final[_Plan] = _Plan(
    "Delivery-Close",
    "L786-L789",
    "acas014",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def delivery_close(ctx: FacadeContext) -> StatusPair:
    """``Delivery-Close`` [copybooks/Proc-ACAS-FH-Calls.cob:L786-L789].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas014``.
    """
    return _perform(ctx, _E_DELIVERY_CLOSE)


_E_DELIVERY_DELETE: Final[_Plan] = _Plan(
    "Delivery-Delete",
    "L791-L795",
    "acas014",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def delivery_delete(ctx: FacadeContext) -> StatusPair:
    """``Delivery-Delete`` [copybooks/Proc-ACAS-FH-Calls.cob:L791-L795].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas014``.
    """
    return _perform(ctx, _E_DELIVERY_DELETE)


_E_DELIVERY_DELETE_ALL: Final[_Plan] = _Plan(
    "Delivery-Delete-All",
    "L797-L801",
    "acas014",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE_ALL),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def delivery_delete_all(ctx: FacadeContext) -> StatusPair:
    """``Delivery-Delete-All`` [copybooks/Proc-ACAS-FH-Calls.cob:L797-L801].

    Sets function code 6, which NO handler dispatches - every one routes
    it to ``when other`` and a bad-function reply
    [common/acasirsub4.cbl:L235]. Published and permanently unsatisfiable.
    The operation is real but reachable only through the open-output
    coercion [common/irspostingMT.cbl:L271-L272].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas014``.
    """
    return _perform(ctx, _E_DELIVERY_DELETE_ALL)


_E_DELIVERY_START: Final[_Plan] = _Plan(
    "Delivery-Start",
    "L803-L806",
    "acas014",
    (
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.START),
    ),
)


def delivery_start(ctx: FacadeContext) -> StatusPair:
    """``Delivery-Start`` [copybooks/Proc-ACAS-FH-Calls.cob:L803-L806].

    Deliberately does NOT clear ``Access-Type``: on a START that field
    carries the relation, 5 through 9 of [copybooks/wsfnctn.cob:L112-L116],
    and the caller sets it. Clearing it would change which row is found.

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas014``.
    """
    return _perform(ctx, _E_DELIVERY_START)


_E_DELIVERY_READ_NEXT: Final[_Plan] = _Plan(
    "Delivery-Read-Next",
    "L808-L811",
    "acas014",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def delivery_read_next(ctx: FacadeContext) -> StatusPair:
    """``Delivery-Read-Next`` [copybooks/Proc-ACAS-FH-Calls.cob:L808-L811].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas014``.
    """
    return _perform(ctx, _E_DELIVERY_READ_NEXT)


_E_DELIVERY_READ_INDEXED: Final[_Plan] = _Plan(
    "Delivery-Read-Indexed",
    "L813-L817",
    "acas014",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.READ_INDEXED),
    ),
)


def delivery_read_indexed(ctx: FacadeContext) -> StatusPair:
    """``Delivery-Read-Indexed`` [copybooks/Proc-ACAS-FH-Calls.cob:L813-L817].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas014``.
    """
    return _perform(ctx, _E_DELIVERY_READ_INDEXED)


_E_DELIVERY_WRITE: Final[_Plan] = _Plan(
    "Delivery-Write",
    "L819-L822",
    "acas014",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def delivery_write(ctx: FacadeContext) -> StatusPair:
    """``Delivery-Write`` [copybooks/Proc-ACAS-FH-Calls.cob:L819-L822].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas014``.
    """
    return _perform(ctx, _E_DELIVERY_WRITE)


_E_DELIVERY_REWRITE: Final[_Plan] = _Plan(
    "Delivery-Rewrite",
    "L824-L827",
    "acas014",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def delivery_rewrite(ctx: FacadeContext) -> StatusPair:
    """``Delivery-Rewrite`` [copybooks/Proc-ACAS-FH-Calls.cob:L824-L827].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas014``.
    """
    return _perform(ctx, _E_DELIVERY_REWRITE)


# --------------------------------------------------------------------------
# Analysis -> acas015 -> ANALYSIS-REC
# --------------------------------------------------------------------------


_E_ANALYSIS_OPEN: Final[_Plan] = _Plan(
    "Analysis-Open",
    "L831-L834",
    "acas015",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
)


def analysis_open(ctx: FacadeContext) -> StatusPair:
    """``Analysis-Open`` [copybooks/Proc-ACAS-FH-Calls.cob:L831-L834]."""
    return _perform(ctx, _E_ANALYSIS_OPEN)


_E_ANALYSIS_OPEN_INPUT: Final[_Plan] = _Plan(
    "Analysis-Open-Input",
    "L836-L839",
    "acas015",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
)


def analysis_open_input(ctx: FacadeContext) -> StatusPair:
    """``Analysis-Open-Input`` [copybooks/Proc-ACAS-FH-Calls.cob:L836-L839]."""
    return _perform(ctx, _E_ANALYSIS_OPEN_INPUT)


_E_ANALYSIS_OPEN_OUTPUT: Final[_Plan] = _Plan(
    "Analysis-Open-Output",
    "L841-L844",
    "acas015",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.OUTPUT),
    ),
)


def analysis_open_output(ctx: FacadeContext) -> StatusPair:
    """``Analysis-Open-Output`` [copybooks/Proc-ACAS-FH-Calls.cob:L841-L844]."""
    return _perform(ctx, _E_ANALYSIS_OPEN_OUTPUT)


_E_ANALYSIS_CLOSE: Final[_Plan] = _Plan(
    "Analysis-Close",
    "L846-L849",
    "acas015",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def analysis_close(ctx: FacadeContext) -> StatusPair:
    """``Analysis-Close`` [copybooks/Proc-ACAS-FH-Calls.cob:L846-L849]."""
    return _perform(ctx, _E_ANALYSIS_CLOSE)


_E_ANALYSIS_DELETE: Final[_Plan] = _Plan(
    "Analysis-Delete",
    "L851-L855",
    "acas015",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def analysis_delete(ctx: FacadeContext) -> StatusPair:
    """``Analysis-Delete`` [copybooks/Proc-ACAS-FH-Calls.cob:L851-L855]."""
    return _perform(ctx, _E_ANALYSIS_DELETE)


_E_ANALYSIS_START: Final[_Plan] = _Plan(
    "Analysis-Start",
    "L857-L860",
    "acas015",
    (
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.START),
    ),
)


def analysis_start(ctx: FacadeContext) -> StatusPair:
    """``Analysis-Start`` [copybooks/Proc-ACAS-FH-Calls.cob:L857-L860].

    Deliberately does NOT clear ``Access-Type``: on a START that field
    carries the relation, 5 through 9 of [copybooks/wsfnctn.cob:L112-L116],
    and the caller sets it. Clearing it would change which row is found.
    """
    return _perform(ctx, _E_ANALYSIS_START)


_E_ANALYSIS_READ_NEXT: Final[_Plan] = _Plan(
    "Analysis-Read-Next",
    "L862-L865",
    "acas015",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def analysis_read_next(ctx: FacadeContext) -> StatusPair:
    """``Analysis-Read-Next`` [copybooks/Proc-ACAS-FH-Calls.cob:L862-L865]."""
    return _perform(ctx, _E_ANALYSIS_READ_NEXT)


_E_ANALYSIS_READ_INDEXED: Final[_Plan] = _Plan(
    "Analysis-Read-Indexed",
    "L867-L871",
    "acas015",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.READ_INDEXED),
    ),
)


def analysis_read_indexed(ctx: FacadeContext) -> StatusPair:
    """``Analysis-Read-Indexed`` [copybooks/Proc-ACAS-FH-Calls.cob:L867-L871]."""
    return _perform(ctx, _E_ANALYSIS_READ_INDEXED)


_E_ANALYSIS_WRITE: Final[_Plan] = _Plan(
    "Analysis-Write",
    "L873-L876",
    "acas015",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def analysis_write(ctx: FacadeContext) -> StatusPair:
    """``Analysis-Write`` [copybooks/Proc-ACAS-FH-Calls.cob:L873-L876]."""
    return _perform(ctx, _E_ANALYSIS_WRITE)


_E_ANALYSIS_REWRITE: Final[_Plan] = _Plan(
    "Analysis-Rewrite",
    "L878-L881",
    "acas015",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def analysis_rewrite(ctx: FacadeContext) -> StatusPair:
    """``Analysis-Rewrite`` [copybooks/Proc-ACAS-FH-Calls.cob:L878-L881]."""
    return _perform(ctx, _E_ANALYSIS_REWRITE)


# --------------------------------------------------------------------------
# Invoice -> acas016 -> SAINVOICE-REC + SAINV-LINES-REC
# --------------------------------------------------------------------------


_E_INVOICE_OPEN: Final[_Plan] = _Plan(
    "Invoice-Open",
    "L885-L888",
    "acas016",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
)


def invoice_open(ctx: FacadeContext) -> StatusPair:
    """``Invoice-Open`` [copybooks/Proc-ACAS-FH-Calls.cob:L885-L888]."""
    return _perform(ctx, _E_INVOICE_OPEN)


_E_INVOICE_OPEN_INPUT: Final[_Plan] = _Plan(
    "Invoice-Open-Input",
    "L890-L893",
    "acas016",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
)


def invoice_open_input(ctx: FacadeContext) -> StatusPair:
    """``Invoice-Open-Input`` [copybooks/Proc-ACAS-FH-Calls.cob:L890-L893]."""
    return _perform(ctx, _E_INVOICE_OPEN_INPUT)


_E_INVOICE_OPEN_OUTPUT: Final[_Plan] = _Plan(
    "Invoice-Open-Output",
    "L895-L898",
    "acas016",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.OUTPUT),
    ),
)


def invoice_open_output(ctx: FacadeContext) -> StatusPair:
    """``Invoice-Open-Output`` [copybooks/Proc-ACAS-FH-Calls.cob:L895-L898]."""
    return _perform(ctx, _E_INVOICE_OPEN_OUTPUT)


_E_INVOICE_CLOSE: Final[_Plan] = _Plan(
    "Invoice-Close",
    "L900-L903",
    "acas016",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def invoice_close(ctx: FacadeContext) -> StatusPair:
    """``Invoice-Close`` [copybooks/Proc-ACAS-FH-Calls.cob:L900-L903]."""
    return _perform(ctx, _E_INVOICE_CLOSE)


_E_INVOICE_DELETE: Final[_Plan] = _Plan(
    "Invoice-Delete",
    "L905-L909",
    "acas016",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def invoice_delete(ctx: FacadeContext) -> StatusPair:
    """``Invoice-Delete`` [copybooks/Proc-ACAS-FH-Calls.cob:L905-L909]."""
    return _perform(ctx, _E_INVOICE_DELETE)


_E_INVOICE_DELETE_ALL: Final[_Plan] = _Plan(
    "Invoice-Delete-All",
    "L911-L915",
    "acas016",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE_ALL),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def invoice_delete_all(ctx: FacadeContext) -> StatusPair:
    """``Invoice-Delete-All`` [copybooks/Proc-ACAS-FH-Calls.cob:L911-L915].

    Sets function code 6, which NO handler dispatches - every one routes
    it to ``when other`` and a bad-function reply
    [common/acasirsub4.cbl:L235]. Published and permanently unsatisfiable.
    The operation is real but reachable only through the open-output
    coercion [common/irspostingMT.cbl:L271-L272].
    """
    return _perform(ctx, _E_INVOICE_DELETE_ALL)


_E_INVOICE_START: Final[_Plan] = _Plan(
    "Invoice-Start",
    "L917-L920",
    "acas016",
    (
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.START),
    ),
)


def invoice_start(ctx: FacadeContext) -> StatusPair:
    """``Invoice-Start`` [copybooks/Proc-ACAS-FH-Calls.cob:L917-L920].

    Deliberately does NOT clear ``Access-Type``: on a START that field
    carries the relation, 5 through 9 of [copybooks/wsfnctn.cob:L112-L116],
    and the caller sets it. Clearing it would change which row is found.
    """
    return _perform(ctx, _E_INVOICE_START)


_E_INVOICE_READ_NEXT: Final[_Plan] = _Plan(
    "Invoice-Read-Next",
    "L922-L925",
    "acas016",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def invoice_read_next(ctx: FacadeContext) -> StatusPair:
    """``Invoice-Read-Next`` [copybooks/Proc-ACAS-FH-Calls.cob:L922-L925]."""
    return _perform(ctx, _E_INVOICE_READ_NEXT)


_E_INVOICE_READ_NEXT_HEADER: Final[_Plan] = _Plan(
    "Invoice-Read-Next-Header",
    "L927-L930",
    "acas016",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT_HEADER),
    ),
)


def invoice_read_next_header(ctx: FacadeContext) -> StatusPair:
    """``Invoice-Read-Next-Header`` [copybooks/Proc-ACAS-FH-Calls.cob:L927-L930].

    Sets function code 34 [copybooks/wsfnctn.cob:L105].
    """
    return _perform(ctx, _E_INVOICE_READ_NEXT_HEADER)


_E_INVOICE_READ_INDEXED: Final[_Plan] = _Plan(
    "Invoice-Read-Indexed",
    "L932-L936",
    "acas016",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.READ_INDEXED),
    ),
)


def invoice_read_indexed(ctx: FacadeContext) -> StatusPair:
    """``Invoice-Read-Indexed`` [copybooks/Proc-ACAS-FH-Calls.cob:L932-L936]."""
    return _perform(ctx, _E_INVOICE_READ_INDEXED)


_E_INVOICE_WRITE: Final[_Plan] = _Plan(
    "Invoice-Write",
    "L938-L941",
    "acas016",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def invoice_write(ctx: FacadeContext) -> StatusPair:
    """``Invoice-Write`` [copybooks/Proc-ACAS-FH-Calls.cob:L938-L941]."""
    return _perform(ctx, _E_INVOICE_WRITE)


_E_INVOICE_REWRITE: Final[_Plan] = _Plan(
    "Invoice-Rewrite",
    "L943-L946",
    "acas016",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def invoice_rewrite(ctx: FacadeContext) -> StatusPair:
    """``Invoice-Rewrite`` [copybooks/Proc-ACAS-FH-Calls.cob:L943-L946]."""
    return _perform(ctx, _E_INVOICE_REWRITE)


# --------------------------------------------------------------------------
# DelInvNos -> acas017 -> OUT OF SCOPE per Agent Action Plan section 0.2.2
# --------------------------------------------------------------------------


_E_DELINVNOS_OPEN: Final[_Plan] = _Plan(
    "DelInvNos-Open",
    "L950-L953",
    "acas017",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
)


def delinvnos_open(ctx: FacadeContext) -> StatusPair:
    """``DelInvNos-Open`` [copybooks/Proc-ACAS-FH-Calls.cob:L950-L953].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas017``.
    """
    return _perform(ctx, _E_DELINVNOS_OPEN)


_E_DELINVNOS_OPEN_INPUT: Final[_Plan] = _Plan(
    "DelInvNos-Open-Input",
    "L955-L958",
    "acas017",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
)


def delinvnos_open_input(ctx: FacadeContext) -> StatusPair:
    """``DelInvNos-Open-Input`` [copybooks/Proc-ACAS-FH-Calls.cob:L955-L958].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas017``.
    """
    return _perform(ctx, _E_DELINVNOS_OPEN_INPUT)


_E_DELINVNOS_OPEN_OUTPUT: Final[_Plan] = _Plan(
    "DelInvNos-Open-Output",
    "L960-L963",
    "acas017",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.OUTPUT),
    ),
)


def delinvnos_open_output(ctx: FacadeContext) -> StatusPair:
    """``DelInvNos-Open-Output`` [copybooks/Proc-ACAS-FH-Calls.cob:L960-L963].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas017``.
    """
    return _perform(ctx, _E_DELINVNOS_OPEN_OUTPUT)


_E_DELINVNOS_CLOSE: Final[_Plan] = _Plan(
    "DelInvNos-Close",
    "L965-L968",
    "acas017",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def delinvnos_close(ctx: FacadeContext) -> StatusPair:
    """``DelInvNos-Close`` [copybooks/Proc-ACAS-FH-Calls.cob:L965-L968].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas017``.
    """
    return _perform(ctx, _E_DELINVNOS_CLOSE)


_E_DELINVNOS_DELETE: Final[_Plan] = _Plan(
    "DelInvNos-Delete",
    "L970-L974",
    "acas017",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def delinvnos_delete(ctx: FacadeContext) -> StatusPair:
    """``DelInvNos-Delete`` [copybooks/Proc-ACAS-FH-Calls.cob:L970-L974].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas017``.
    """
    return _perform(ctx, _E_DELINVNOS_DELETE)


_E_DELINVNOS_DELETE_ALL: Final[_Plan] = _Plan(
    "DelInvNos-Delete-All",
    "L976-L980",
    "acas017",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE_ALL),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def delinvnos_delete_all(ctx: FacadeContext) -> StatusPair:
    """``DelInvNos-Delete-All`` [copybooks/Proc-ACAS-FH-Calls.cob:L976-L980].

    Sets function code 6, which NO handler dispatches - every one routes
    it to ``when other`` and a bad-function reply
    [common/acasirsub4.cbl:L235]. Published and permanently unsatisfiable.
    The operation is real but reachable only through the open-output
    coercion [common/irspostingMT.cbl:L271-L272].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas017``.
    """
    return _perform(ctx, _E_DELINVNOS_DELETE_ALL)


_E_DELINVNOS_START: Final[_Plan] = _Plan(
    "DelInvNos-Start",
    "L982-L985",
    "acas017",
    (
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.START),
    ),
)


def delinvnos_start(ctx: FacadeContext) -> StatusPair:
    """``DelInvNos-Start`` [copybooks/Proc-ACAS-FH-Calls.cob:L982-L985].

    Deliberately does NOT clear ``Access-Type``: on a START that field
    carries the relation, 5 through 9 of [copybooks/wsfnctn.cob:L112-L116],
    and the caller sets it. Clearing it would change which row is found.

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas017``.
    """
    return _perform(ctx, _E_DELINVNOS_START)


_E_DELINVNOS_READ_NEXT: Final[_Plan] = _Plan(
    "DelInvNos-Read-Next",
    "L987-L990",
    "acas017",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def delinvnos_read_next(ctx: FacadeContext) -> StatusPair:
    """``DelInvNos-Read-Next`` [copybooks/Proc-ACAS-FH-Calls.cob:L987-L990].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas017``.
    """
    return _perform(ctx, _E_DELINVNOS_READ_NEXT)


_E_DELINVNOS_READ_INDEXED: Final[_Plan] = _Plan(
    "DelInvNos-Read-Indexed",
    "L992-L996",
    "acas017",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.READ_INDEXED),
    ),
)


def delinvnos_read_indexed(ctx: FacadeContext) -> StatusPair:
    """``DelInvNos-Read-Indexed`` [copybooks/Proc-ACAS-FH-Calls.cob:L992-L996].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas017``.
    """
    return _perform(ctx, _E_DELINVNOS_READ_INDEXED)


_E_DELINVNOS_WRITE: Final[_Plan] = _Plan(
    "DelInvNos-Write",
    "L998-L1001",
    "acas017",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def delinvnos_write(ctx: FacadeContext) -> StatusPair:
    """``DelInvNos-Write`` [copybooks/Proc-ACAS-FH-Calls.cob:L998-L1001].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas017``.
    """
    return _perform(ctx, _E_DELINVNOS_WRITE)


_E_DELINVNOS_REWRITE: Final[_Plan] = _Plan(
    "DelInvNos-Rewrite",
    "L1003-L1006",
    "acas017",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def delinvnos_rewrite(ctx: FacadeContext) -> StatusPair:
    """``DelInvNos-Rewrite`` [copybooks/Proc-ACAS-FH-Calls.cob:L1003-L1006].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas017``.
    """
    return _perform(ctx, _E_DELINVNOS_REWRITE)


# --------------------------------------------------------------------------
# OTM3 -> acas019 -> SAITM3-REC
# --------------------------------------------------------------------------


_E_OTM3_OPEN: Final[_Plan] = _Plan(
    "OTM3-Open",
    "L1010-L1013",
    "acas019",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
)


def otm3_open(ctx: FacadeContext) -> StatusPair:
    """``OTM3-Open`` [copybooks/Proc-ACAS-FH-Calls.cob:L1010-L1013]."""
    return _perform(ctx, _E_OTM3_OPEN)


_E_OTM3_OPEN_INPUT: Final[_Plan] = _Plan(
    "OTM3-Open-Input",
    "L1015-L1018",
    "acas019",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
)


def otm3_open_input(ctx: FacadeContext) -> StatusPair:
    """``OTM3-Open-Input`` [copybooks/Proc-ACAS-FH-Calls.cob:L1015-L1018]."""
    return _perform(ctx, _E_OTM3_OPEN_INPUT)


_E_OTM3_OPEN_OUTPUT: Final[_Plan] = _Plan(
    "OTM3-Open-Output",
    "L1020-L1023",
    "acas019",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.OUTPUT),
    ),
)


def otm3_open_output(ctx: FacadeContext) -> StatusPair:
    """``OTM3-Open-Output`` [copybooks/Proc-ACAS-FH-Calls.cob:L1020-L1023]."""
    return _perform(ctx, _E_OTM3_OPEN_OUTPUT)


_E_OTM3_CLOSE: Final[_Plan] = _Plan(
    "OTM3-Close",
    "L1025-L1028",
    "acas019",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def otm3_close(ctx: FacadeContext) -> StatusPair:
    """``OTM3-Close`` [copybooks/Proc-ACAS-FH-Calls.cob:L1025-L1028]."""
    return _perform(ctx, _E_OTM3_CLOSE)


_E_OTM3_DELETE: Final[_Plan] = _Plan(
    "OTM3-Delete",
    "L1030-L1034",
    "acas019",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def otm3_delete(ctx: FacadeContext) -> StatusPair:
    """``OTM3-Delete`` [copybooks/Proc-ACAS-FH-Calls.cob:L1030-L1034]."""
    return _perform(ctx, _E_OTM3_DELETE)


_E_OTM3_START: Final[_Plan] = _Plan(
    "OTM3-Start",
    "L1036-L1039",
    "acas019",
    (
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.START),
    ),
)


def otm3_start(ctx: FacadeContext) -> StatusPair:
    """``OTM3-Start`` [copybooks/Proc-ACAS-FH-Calls.cob:L1036-L1039].

    Deliberately does NOT clear ``Access-Type``: on a START that field
    carries the relation, 5 through 9 of [copybooks/wsfnctn.cob:L112-L116],
    and the caller sets it. Clearing it would change which row is found.
    """
    return _perform(ctx, _E_OTM3_START)


_E_OTM3_READ_NEXT: Final[_Plan] = _Plan(
    "OTM3-Read-Next",
    "L1041-L1044",
    "acas019",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def otm3_read_next(ctx: FacadeContext) -> StatusPair:
    """``OTM3-Read-Next`` [copybooks/Proc-ACAS-FH-Calls.cob:L1041-L1044]."""
    return _perform(ctx, _E_OTM3_READ_NEXT)


_E_OTM3_READ_INDEXED: Final[_Plan] = _Plan(
    "OTM3-Read-Indexed",
    "L1046-L1050",
    "acas019",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.READ_INDEXED),
    ),
)


def otm3_read_indexed(ctx: FacadeContext) -> StatusPair:
    """``OTM3-Read-Indexed`` [copybooks/Proc-ACAS-FH-Calls.cob:L1046-L1050]."""
    return _perform(ctx, _E_OTM3_READ_INDEXED)


_E_OTM3_READ_NEXT_SORTED_BY_BATCH: Final[_Plan] = _Plan(
    "OTM3-Read-Next-Sorted-By-Batch",
    "L1052-L1055",
    "acas019",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_BY_BATCH),
    ),
)


def otm3_read_next_sorted_by_batch(ctx: FacadeContext) -> StatusPair:
    """``OTM3-Read-Next-Sorted-By-Batch`` [copybooks/Proc-ACAS-FH-Calls.cob:L1052-L1055].

    Sets function code 32, declared for OTM3 and OTM5 at
    [copybooks/wsfnctn.cob:L103-L104] and dispatched by the BRIDGE of each of
    the two handlers it was declared for - ``otm3MT`` routes it to
    ``ba140-Process-Read-Next`` [common/otm3MT.cbl:L420-L423] and ``otm5MT``
    likewise [common/otm5MT.cbl:L425-L426]. Neither HANDLER carries a ``when
    32``, which is why an earlier reading of this verb called it
    unsatisfiable; on the RDB path the handler's flat-file ``evaluate`` is
    never reached [common/acas019.cbl:L257-L261,
    common/acas029.cbl:L257-L261], so the code passes through untouched.

    Satisfiable, therefore, but never SUCCESSFUL: the frozen ``SELECT`` both
    bridges assemble is a syntax error, and the zero-rows guard masks it as end
    of file, so the observable answer is ``(10, 10)``. See anomaly
    N-sorted-order-is-a-syntax-error in ``dal/acas019_otm3.py`` and
    ``dal/acas029_otm5.py``.
    """
    return _perform(ctx, _E_OTM3_READ_NEXT_SORTED_BY_BATCH)


_E_OTM3_READ_NEXT_SORTED_BY_CUST: Final[_Plan] = _Plan(
    "OTM3-Read-Next-Sorted-By-Cust",
    "L1057-L1060",
    "acas019",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_BY_CUST),
    ),
)


def otm3_read_next_sorted_by_cust(ctx: FacadeContext) -> StatusPair:
    """``OTM3-Read-Next-Sorted-By-Cust`` [copybooks/Proc-ACAS-FH-Calls.cob:L1057-L1060].

    Sets function code 33, whose declaration names OTM3 alone - "for OTM3
    (sl110, 120, 190)" [copybooks/wsfnctn.cob:L104] - even though this facade
    publishes the verb for OTM5 as well and both bridges dispatch it,
    ``otm3MT`` to ``ba150-Process-Read-Next`` [common/otm3MT.cbl:L424-L427] and
    ``otm5MT`` to its own [common/otm5MT.cbl:L427-L428]. Reached on the RDB
    path only, for the reason given on
    :func:`otm3_read_next_sorted_by_batch`.

    Satisfiable but never successful: the same three compounded defects yield
    ``(10, 10)``. See anomaly N-sorted-order-is-a-syntax-error.
    """
    return _perform(ctx, _E_OTM3_READ_NEXT_SORTED_BY_CUST)


_E_OTM3_WRITE: Final[_Plan] = _Plan(
    "OTM3-Write",
    "L1062-L1065",
    "acas019",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def otm3_write(ctx: FacadeContext) -> StatusPair:
    """``OTM3-Write`` [copybooks/Proc-ACAS-FH-Calls.cob:L1062-L1065]."""
    return _perform(ctx, _E_OTM3_WRITE)


_E_OTM3_REWRITE: Final[_Plan] = _Plan(
    "OTM3-Rewrite",
    "L1067-L1070",
    "acas019",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def otm3_rewrite(ctx: FacadeContext) -> StatusPair:
    """``OTM3-Rewrite`` [copybooks/Proc-ACAS-FH-Calls.cob:L1067-L1070]."""
    return _perform(ctx, _E_OTM3_REWRITE)


# --------------------------------------------------------------------------
# Purch -> acas022 -> PULEDGER-REC
# --------------------------------------------------------------------------


_E_PURCH_OPEN: Final[_Plan] = _Plan(
    "Purch-Open",
    "L1074-L1077",
    "acas022",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
)


def purch_open(ctx: FacadeContext) -> StatusPair:
    """``Purch-Open`` [copybooks/Proc-ACAS-FH-Calls.cob:L1074-L1077]."""
    return _perform(ctx, _E_PURCH_OPEN)


_E_PURCH_OPEN_INPUT: Final[_Plan] = _Plan(
    "Purch-Open-Input",
    "L1079-L1082",
    "acas022",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
)


def purch_open_input(ctx: FacadeContext) -> StatusPair:
    """``Purch-Open-Input`` [copybooks/Proc-ACAS-FH-Calls.cob:L1079-L1082]."""
    return _perform(ctx, _E_PURCH_OPEN_INPUT)


_E_PURCH_OPEN_OUTPUT: Final[_Plan] = _Plan(
    "Purch-Open-Output",
    "L1084-L1087",
    "acas022",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.OUTPUT),
    ),
)


def purch_open_output(ctx: FacadeContext) -> StatusPair:
    """``Purch-Open-Output`` [copybooks/Proc-ACAS-FH-Calls.cob:L1084-L1087]."""
    return _perform(ctx, _E_PURCH_OPEN_OUTPUT)


_E_PURCH_CLOSE: Final[_Plan] = _Plan(
    "Purch-Close",
    "L1089-L1092",
    "acas022",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def purch_close(ctx: FacadeContext) -> StatusPair:
    """``Purch-Close`` [copybooks/Proc-ACAS-FH-Calls.cob:L1089-L1092]."""
    return _perform(ctx, _E_PURCH_CLOSE)


_E_PURCH_DELETE: Final[_Plan] = _Plan(
    "Purch-Delete",
    "L1094-L1098",
    "acas022",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def purch_delete(ctx: FacadeContext) -> StatusPair:
    """``Purch-Delete`` [copybooks/Proc-ACAS-FH-Calls.cob:L1094-L1098]."""
    return _perform(ctx, _E_PURCH_DELETE)


_E_PURCH_START: Final[_Plan] = _Plan(
    "Purch-Start",
    "L1100-L1103",
    "acas022",
    (
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.START),
    ),
)


def purch_start(ctx: FacadeContext) -> StatusPair:
    """``Purch-Start`` [copybooks/Proc-ACAS-FH-Calls.cob:L1100-L1103].

    Deliberately does NOT clear ``Access-Type``: on a START that field
    carries the relation, 5 through 9 of [copybooks/wsfnctn.cob:L112-L116],
    and the caller sets it. Clearing it would change which row is found.
    """
    return _perform(ctx, _E_PURCH_START)


_E_PURCH_READ_NEXT: Final[_Plan] = _Plan(
    "Purch-Read-Next",
    "L1105-L1108",
    "acas022",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def purch_read_next(ctx: FacadeContext) -> StatusPair:
    """``Purch-Read-Next`` [copybooks/Proc-ACAS-FH-Calls.cob:L1105-L1108]."""
    return _perform(ctx, _E_PURCH_READ_NEXT)


_E_PURCH_READ_NEXT_SORTED_BYNAME: Final[_Plan] = _Plan(
    "Purch-Read-Next-Sorted-ByName",
    "L1110-L1113",
    "acas022",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_BY_NAME),
    ),
)


def purch_read_next_sorted_byname(ctx: FacadeContext) -> StatusPair:
    """``Purch-Read-Next-Sorted-ByName`` [copybooks/Proc-ACAS-FH-Calls.cob:L1110-L1113].

    Sets function code 31, which ``acas022`` does dispatch
    [common/acas022.cbl:L344]. Note the spelling: ``ByName`` unhyphenated,
    where the Sales equivalent writes ``By-Name``. Preserved, not tidied.
    """
    return _perform(ctx, _E_PURCH_READ_NEXT_SORTED_BYNAME)


_E_PURCH_READ_INDEXED: Final[_Plan] = _Plan(
    "Purch-Read-Indexed",
    "L1115-L1119",
    "acas022",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.READ_INDEXED),
    ),
)


def purch_read_indexed(ctx: FacadeContext) -> StatusPair:
    """``Purch-Read-Indexed`` [copybooks/Proc-ACAS-FH-Calls.cob:L1115-L1119]."""
    return _perform(ctx, _E_PURCH_READ_INDEXED)


_E_PURCH_WRITE: Final[_Plan] = _Plan(
    "Purch-Write",
    "L1121-L1124",
    "acas022",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def purch_write(ctx: FacadeContext) -> StatusPair:
    """``Purch-Write`` [copybooks/Proc-ACAS-FH-Calls.cob:L1121-L1124]."""
    return _perform(ctx, _E_PURCH_WRITE)


_E_PURCH_REWRITE: Final[_Plan] = _Plan(
    "Purch-Rewrite",
    "L1126-L1129",
    "acas022",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def purch_rewrite(ctx: FacadeContext) -> StatusPair:
    """``Purch-Rewrite`` [copybooks/Proc-ACAS-FH-Calls.cob:L1126-L1129]."""
    return _perform(ctx, _E_PURCH_REWRITE)


# --------------------------------------------------------------------------
# DelFolio -> acas023 -> OUT OF SCOPE per Agent Action Plan section 0.2.2
# --------------------------------------------------------------------------


_E_DELFOLIO_OPEN: Final[_Plan] = _Plan(
    "DelFolio-Open",
    "L1133-L1136",
    "acas023",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
)


def delfolio_open(ctx: FacadeContext) -> StatusPair:
    """``DelFolio-Open`` [copybooks/Proc-ACAS-FH-Calls.cob:L1133-L1136].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas023``.
    """
    return _perform(ctx, _E_DELFOLIO_OPEN)


_E_DELFOLIO_OPEN_INPUT: Final[_Plan] = _Plan(
    "DelFolio-Open-Input",
    "L1138-L1141",
    "acas023",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
)


def delfolio_open_input(ctx: FacadeContext) -> StatusPair:
    """``DelFolio-Open-Input`` [copybooks/Proc-ACAS-FH-Calls.cob:L1138-L1141].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas023``.
    """
    return _perform(ctx, _E_DELFOLIO_OPEN_INPUT)


_E_DELFOLIO_OPEN_OUTPUT: Final[_Plan] = _Plan(
    "DelFolio-Open-Output",
    "L1143-L1146",
    "acas023",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.OUTPUT),
    ),
)


def delfolio_open_output(ctx: FacadeContext) -> StatusPair:
    """``DelFolio-Open-Output`` [copybooks/Proc-ACAS-FH-Calls.cob:L1143-L1146].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas023``.
    """
    return _perform(ctx, _E_DELFOLIO_OPEN_OUTPUT)


_E_DELFOLIO_CLOSE: Final[_Plan] = _Plan(
    "DelFolio-Close",
    "L1148-L1151",
    "acas023",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def delfolio_close(ctx: FacadeContext) -> StatusPair:
    """``DelFolio-Close`` [copybooks/Proc-ACAS-FH-Calls.cob:L1148-L1151].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas023``.
    """
    return _perform(ctx, _E_DELFOLIO_CLOSE)


_E_DELFOLIO_DELETE: Final[_Plan] = _Plan(
    "DelFolio-Delete",
    "L1153-L1157",
    "acas023",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def delfolio_delete(ctx: FacadeContext) -> StatusPair:
    """``DelFolio-Delete`` [copybooks/Proc-ACAS-FH-Calls.cob:L1153-L1157].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas023``.
    """
    return _perform(ctx, _E_DELFOLIO_DELETE)


_E_DELFOLIO_DELETE_ALL: Final[_Plan] = _Plan(
    "DelFolio-Delete-All",
    "L1159-L1163",
    "acas023",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE_ALL),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def delfolio_delete_all(ctx: FacadeContext) -> StatusPair:
    """``DelFolio-Delete-All`` [copybooks/Proc-ACAS-FH-Calls.cob:L1159-L1163].

    Sets function code 6, which NO handler dispatches - every one routes
    it to ``when other`` and a bad-function reply
    [common/acasirsub4.cbl:L235]. Published and permanently unsatisfiable.
    The operation is real but reachable only through the open-output
    coercion [common/irspostingMT.cbl:L271-L272].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas023``.
    """
    return _perform(ctx, _E_DELFOLIO_DELETE_ALL)


_E_DELFOLIO_START: Final[_Plan] = _Plan(
    "DelFolio-Start",
    "L1165-L1168",
    "acas023",
    (
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.START),
    ),
)


def delfolio_start(ctx: FacadeContext) -> StatusPair:
    """``DelFolio-Start`` [copybooks/Proc-ACAS-FH-Calls.cob:L1165-L1168].

    Deliberately does NOT clear ``Access-Type``: on a START that field
    carries the relation, 5 through 9 of [copybooks/wsfnctn.cob:L112-L116],
    and the caller sets it. Clearing it would change which row is found.

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas023``.
    """
    return _perform(ctx, _E_DELFOLIO_START)


_E_DELFOLIO_READ_NEXT: Final[_Plan] = _Plan(
    "DelFolio-Read-Next",
    "L1170-L1173",
    "acas023",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def delfolio_read_next(ctx: FacadeContext) -> StatusPair:
    """``DelFolio-Read-Next`` [copybooks/Proc-ACAS-FH-Calls.cob:L1170-L1173].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas023``.
    """
    return _perform(ctx, _E_DELFOLIO_READ_NEXT)


_E_DELFOLIO_READ_INDEXED: Final[_Plan] = _Plan(
    "DelFolio-Read-Indexed",
    "L1175-L1179",
    "acas023",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.READ_INDEXED),
    ),
)


def delfolio_read_indexed(ctx: FacadeContext) -> StatusPair:
    """``DelFolio-Read-Indexed`` [copybooks/Proc-ACAS-FH-Calls.cob:L1175-L1179].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas023``.
    """
    return _perform(ctx, _E_DELFOLIO_READ_INDEXED)


_E_DELFOLIO_WRITE: Final[_Plan] = _Plan(
    "DelFolio-Write",
    "L1181-L1184",
    "acas023",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def delfolio_write(ctx: FacadeContext) -> StatusPair:
    """``DelFolio-Write`` [copybooks/Proc-ACAS-FH-Calls.cob:L1181-L1184].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas023``.
    """
    return _perform(ctx, _E_DELFOLIO_WRITE)


_E_DELFOLIO_REWRITE: Final[_Plan] = _Plan(
    "DelFolio-Rewrite",
    "L1186-L1189",
    "acas023",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def delfolio_rewrite(ctx: FacadeContext) -> StatusPair:
    """``DelFolio-Rewrite`` [copybooks/Proc-ACAS-FH-Calls.cob:L1186-L1189].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas023``.
    """
    return _perform(ctx, _E_DELFOLIO_REWRITE)


# --------------------------------------------------------------------------
# PInvoice -> acas026 -> PUINVOICE-REC + PUINV-LINES-REC
# --------------------------------------------------------------------------


_E_PINVOICE_OPEN: Final[_Plan] = _Plan(
    "PInvoice-Open",
    "L1193-L1196",
    "acas026",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
)


def pinvoice_open(ctx: FacadeContext) -> StatusPair:
    """``PInvoice-Open`` [copybooks/Proc-ACAS-FH-Calls.cob:L1193-L1196]."""
    return _perform(ctx, _E_PINVOICE_OPEN)


_E_PINVOICE_OPEN_INPUT: Final[_Plan] = _Plan(
    "PInvoice-Open-Input",
    "L1198-L1201",
    "acas026",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
)


def pinvoice_open_input(ctx: FacadeContext) -> StatusPair:
    """``PInvoice-Open-Input`` [copybooks/Proc-ACAS-FH-Calls.cob:L1198-L1201]."""
    return _perform(ctx, _E_PINVOICE_OPEN_INPUT)


_E_PINVOICE_OPEN_OUTPUT: Final[_Plan] = _Plan(
    "PInvoice-Open-Output",
    "L1203-L1206",
    "acas026",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.OUTPUT),
    ),
)


def pinvoice_open_output(ctx: FacadeContext) -> StatusPair:
    """``PInvoice-Open-Output`` [copybooks/Proc-ACAS-FH-Calls.cob:L1203-L1206]."""
    return _perform(ctx, _E_PINVOICE_OPEN_OUTPUT)


_E_PINVOICE_CLOSE: Final[_Plan] = _Plan(
    "PInvoice-Close",
    "L1208-L1211",
    "acas026",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def pinvoice_close(ctx: FacadeContext) -> StatusPair:
    """``PInvoice-Close`` [copybooks/Proc-ACAS-FH-Calls.cob:L1208-L1211]."""
    return _perform(ctx, _E_PINVOICE_CLOSE)


_E_PINVOICE_DELETE: Final[_Plan] = _Plan(
    "PInvoice-Delete",
    "L1213-L1217",
    "acas026",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def pinvoice_delete(ctx: FacadeContext) -> StatusPair:
    """``PInvoice-Delete`` [copybooks/Proc-ACAS-FH-Calls.cob:L1213-L1217]."""
    return _perform(ctx, _E_PINVOICE_DELETE)


_E_PINVOICE_DELETE_ALL: Final[_Plan] = _Plan(
    "PInvoice-Delete-All",
    "L1219-L1223",
    "acas026",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE_ALL),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def pinvoice_delete_all(ctx: FacadeContext) -> StatusPair:
    """``PInvoice-Delete-All`` [copybooks/Proc-ACAS-FH-Calls.cob:L1219-L1223].

    Sets function code 6, which NO handler dispatches - every one routes
    it to ``when other`` and a bad-function reply
    [common/acasirsub4.cbl:L235]. Published and permanently unsatisfiable.
    The operation is real but reachable only through the open-output
    coercion [common/irspostingMT.cbl:L271-L272].
    """
    return _perform(ctx, _E_PINVOICE_DELETE_ALL)


_E_PINVOICE_START: Final[_Plan] = _Plan(
    "PInvoice-Start",
    "L1225-L1228",
    "acas026",
    (
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.START),
    ),
)


def pinvoice_start(ctx: FacadeContext) -> StatusPair:
    """``PInvoice-Start`` [copybooks/Proc-ACAS-FH-Calls.cob:L1225-L1228].

    Deliberately does NOT clear ``Access-Type``: on a START that field
    carries the relation, 5 through 9 of [copybooks/wsfnctn.cob:L112-L116],
    and the caller sets it. Clearing it would change which row is found.
    """
    return _perform(ctx, _E_PINVOICE_START)


_E_PINVOICE_READ_NEXT: Final[_Plan] = _Plan(
    "PInvoice-Read-Next",
    "L1230-L1233",
    "acas026",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def pinvoice_read_next(ctx: FacadeContext) -> StatusPair:
    """``PInvoice-Read-Next`` [copybooks/Proc-ACAS-FH-Calls.cob:L1230-L1233]."""
    return _perform(ctx, _E_PINVOICE_READ_NEXT)


_E_PINVOICE_READ_NEXT_HEADER: Final[_Plan] = _Plan(
    "PInvoice-Read-Next-Header",
    "L1235-L1238",
    "acas026",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT_HEADER),
    ),
)


def pinvoice_read_next_header(ctx: FacadeContext) -> StatusPair:
    """``PInvoice-Read-Next-Header`` [copybooks/Proc-ACAS-FH-Calls.cob:L1235-L1238].

    Sets function code 34 [copybooks/wsfnctn.cob:L105].
    """
    return _perform(ctx, _E_PINVOICE_READ_NEXT_HEADER)


_E_PINVOICE_READ_INDEXED: Final[_Plan] = _Plan(
    "PInvoice-Read-Indexed",
    "L1240-L1244",
    "acas026",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.READ_INDEXED),
    ),
)


def pinvoice_read_indexed(ctx: FacadeContext) -> StatusPair:
    """``PInvoice-Read-Indexed`` [copybooks/Proc-ACAS-FH-Calls.cob:L1240-L1244]."""
    return _perform(ctx, _E_PINVOICE_READ_INDEXED)


_E_PINVOICE_WRITE: Final[_Plan] = _Plan(
    "PInvoice-Write",
    "L1246-L1249",
    "acas026",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def pinvoice_write(ctx: FacadeContext) -> StatusPair:
    """``PInvoice-Write`` [copybooks/Proc-ACAS-FH-Calls.cob:L1246-L1249]."""
    return _perform(ctx, _E_PINVOICE_WRITE)


_E_PINVOICE_REWRITE: Final[_Plan] = _Plan(
    "PInvoice-Rewrite",
    "L1251-L1254",
    "acas026",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def pinvoice_rewrite(ctx: FacadeContext) -> StatusPair:
    """``PInvoice-Rewrite`` [copybooks/Proc-ACAS-FH-Calls.cob:L1251-L1254]."""
    return _perform(ctx, _E_PINVOICE_REWRITE)


# --------------------------------------------------------------------------
# OTM5 -> acas029 -> PUITM5-REC
# --------------------------------------------------------------------------


_E_OTM5_OPEN: Final[_Plan] = _Plan(
    "OTM5-Open",
    "L1258-L1261",
    "acas029",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
)


def otm5_open(ctx: FacadeContext) -> StatusPair:
    """``OTM5-Open`` [copybooks/Proc-ACAS-FH-Calls.cob:L1258-L1261]."""
    return _perform(ctx, _E_OTM5_OPEN)


_E_OTM5_OPEN_INPUT: Final[_Plan] = _Plan(
    "OTM5-Open-Input",
    "L1263-L1266",
    "acas029",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
)


def otm5_open_input(ctx: FacadeContext) -> StatusPair:
    """``OTM5-Open-Input`` [copybooks/Proc-ACAS-FH-Calls.cob:L1263-L1266]."""
    return _perform(ctx, _E_OTM5_OPEN_INPUT)


_E_OTM5_OPEN_OUTPUT: Final[_Plan] = _Plan(
    "OTM5-Open-Output",
    "L1268-L1271",
    "acas029",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.OUTPUT),
    ),
)


def otm5_open_output(ctx: FacadeContext) -> StatusPair:
    """``OTM5-Open-Output`` [copybooks/Proc-ACAS-FH-Calls.cob:L1268-L1271]."""
    return _perform(ctx, _E_OTM5_OPEN_OUTPUT)


_E_OTM5_CLOSE: Final[_Plan] = _Plan(
    "OTM5-Close",
    "L1273-L1276",
    "acas029",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def otm5_close(ctx: FacadeContext) -> StatusPair:
    """``OTM5-Close`` [copybooks/Proc-ACAS-FH-Calls.cob:L1273-L1276]."""
    return _perform(ctx, _E_OTM5_CLOSE)


_E_OTM5_DELETE: Final[_Plan] = _Plan(
    "OTM5-Delete",
    "L1278-L1282",
    "acas029",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def otm5_delete(ctx: FacadeContext) -> StatusPair:
    """``OTM5-Delete`` [copybooks/Proc-ACAS-FH-Calls.cob:L1278-L1282]."""
    return _perform(ctx, _E_OTM5_DELETE)


_E_OTM5_START: Final[_Plan] = _Plan(
    "OTM5-Start",
    "L1284-L1287",
    "acas029",
    (
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.START),
    ),
)


def otm5_start(ctx: FacadeContext) -> StatusPair:
    """``OTM5-Start`` [copybooks/Proc-ACAS-FH-Calls.cob:L1284-L1287].

    Deliberately does NOT clear ``Access-Type``: on a START that field
    carries the relation, 5 through 9 of [copybooks/wsfnctn.cob:L112-L116],
    and the caller sets it. Clearing it would change which row is found.
    """
    return _perform(ctx, _E_OTM5_START)


_E_OTM5_READ_NEXT: Final[_Plan] = _Plan(
    "OTM5-Read-Next",
    "L1289-L1292",
    "acas029",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def otm5_read_next(ctx: FacadeContext) -> StatusPair:
    """``OTM5-Read-Next`` [copybooks/Proc-ACAS-FH-Calls.cob:L1289-L1292]."""
    return _perform(ctx, _E_OTM5_READ_NEXT)


_E_OTM5_READ_INDEXED: Final[_Plan] = _Plan(
    "OTM5-Read-Indexed",
    "L1294-L1298",
    "acas029",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.READ_INDEXED),
    ),
)


def otm5_read_indexed(ctx: FacadeContext) -> StatusPair:
    """``OTM5-Read-Indexed`` [copybooks/Proc-ACAS-FH-Calls.cob:L1294-L1298]."""
    return _perform(ctx, _E_OTM5_READ_INDEXED)


_E_OTM5_READ_NEXT_SORTED_BY_BATCH: Final[_Plan] = _Plan(
    "OTM5-Read-Next-Sorted-By-Batch",
    "L1300-L1303",
    "acas029",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_BY_BATCH),
    ),
)


def otm5_read_next_sorted_by_batch(ctx: FacadeContext) -> StatusPair:
    """``OTM5-Read-Next-Sorted-By-Batch`` [copybooks/Proc-ACAS-FH-Calls.cob:L1300-L1303].

    Sets function code 32 and performs ``acas029``, exactly as the frozen
    paragraph does::

        OTM5-Read-Next-Sorted-By-Batch.
            move     zero to Access-Type.
            set      fn-Read-By-Batch to true.
            perform  acas029.

    ``otm5MT`` routes the code to ``ba140-Process-Read-Next``
    [common/otm5MT.cbl:L425-L426], which ``dal/acas029_otm5.py`` publishes as
    ``read_next_sorted_by_batch``. The handler's own ``evaluate`` has no ``when
    32`` [common/acas029.cbl:L277-L296], but that evaluate is the FLAT-FILE one
    and the RDB branch leaves before it [common/acas029.cbl:L257-L261] - which
    is why an earlier reading of this verb called it unsatisfiable.

    Satisfiable, but it can never report success: the ``SELECT`` the bridge
    assembles emits ``WHERE`` with no predicate and orders by single-quoted
    string constants, and the zero-rows guard masks the resulting syntax error
    as end of file. The observable answer is ``(10, 10)`` - see anomaly
    N-sorted-order-is-a-syntax-error in ``dal/acas029_otm5.py``.
    """
    return _perform(ctx, _E_OTM5_READ_NEXT_SORTED_BY_BATCH)


_E_OTM5_READ_NEXT_SORTED_BY_CUST: Final[_Plan] = _Plan(
    "OTM5-Read-Next-Sorted-By-Cust",
    "L1305-L1308",
    "acas029",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_BY_CUST),
    ),
)


def otm5_read_next_sorted_by_cust(ctx: FacadeContext) -> StatusPair:
    """``OTM5-Read-Next-Sorted-By-Cust`` [copybooks/Proc-ACAS-FH-Calls.cob:L1305-L1308].

    Sets function code 33 and performs ``acas029``. ⭐ THE DECLARATION OF THE
    CODE NAMES OTM3 ALONE - "for OTM3 (sl110, 120, 190)"
    [copybooks/wsfnctn.cob:L104] - yet this facade publishes it for the PURCHASE
    open-item entity too, and ``otm5MT`` dispatches it to
    ``ba150-Process-Read-Next`` [common/otm5MT.cbl:L427-L428], whose own prose
    comment names sales columns [common/otm5MT.cbl:L1151-L1154]. The whole
    sorted-read pair is a sales template copied into a purchase bridge.

    ``dal/acas029_otm5.py`` publishes it as ``read_next_sorted_by_cust``.
    Reached on the RDB path only, for the reason given on
    :func:`otm5_read_next_sorted_by_batch`, and answering ``(10, 10)`` for the
    same reason - anomaly N-sorted-order-is-a-syntax-error.
    """
    return _perform(ctx, _E_OTM5_READ_NEXT_SORTED_BY_CUST)


_E_OTM5_WRITE: Final[_Plan] = _Plan(
    "OTM5-Write",
    "L1310-L1313",
    "acas029",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def otm5_write(ctx: FacadeContext) -> StatusPair:
    """``OTM5-Write`` [copybooks/Proc-ACAS-FH-Calls.cob:L1310-L1313]."""
    return _perform(ctx, _E_OTM5_WRITE)


_E_OTM5_REWRITE: Final[_Plan] = _Plan(
    "OTM5-Rewrite",
    "L1315-L1318",
    "acas029",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def otm5_rewrite(ctx: FacadeContext) -> StatusPair:
    """``OTM5-Rewrite`` [copybooks/Proc-ACAS-FH-Calls.cob:L1315-L1318]."""
    return _perform(ctx, _E_OTM5_REWRITE)


# --------------------------------------------------------------------------
# PLautogen -> acas030 -> OUT OF SCOPE per Agent Action Plan section 0.2.2
# --------------------------------------------------------------------------


_E_PLAUTOGEN_OPEN: Final[_Plan] = _Plan(
    "PLautogen-Open",
    "L1323-L1326",
    "acas030",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
)


def plautogen_open(ctx: FacadeContext) -> StatusPair:
    """``PLautogen-Open`` [copybooks/Proc-ACAS-FH-Calls.cob:L1323-L1326].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas030``.
    """
    return _perform(ctx, _E_PLAUTOGEN_OPEN)


_E_PLAUTOGEN_OPEN_INPUT: Final[_Plan] = _Plan(
    "PLautogen-Open-Input",
    "L1328-L1331",
    "acas030",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
)


def plautogen_open_input(ctx: FacadeContext) -> StatusPair:
    """``PLautogen-Open-Input`` [copybooks/Proc-ACAS-FH-Calls.cob:L1328-L1331].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas030``.
    """
    return _perform(ctx, _E_PLAUTOGEN_OPEN_INPUT)


_E_PLAUTOGEN_OPEN_OUTPUT: Final[_Plan] = _Plan(
    "PLautogen-Open-Output",
    "L1333-L1336",
    "acas030",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.OUTPUT),
    ),
)


def plautogen_open_output(ctx: FacadeContext) -> StatusPair:
    """``PLautogen-Open-Output`` [copybooks/Proc-ACAS-FH-Calls.cob:L1333-L1336].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas030``.
    """
    return _perform(ctx, _E_PLAUTOGEN_OPEN_OUTPUT)


_E_PLAUTOGEN_CLOSE: Final[_Plan] = _Plan(
    "PLautogen-Close",
    "L1338-L1341",
    "acas030",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def plautogen_close(ctx: FacadeContext) -> StatusPair:
    """``PLautogen-Close`` [copybooks/Proc-ACAS-FH-Calls.cob:L1338-L1341].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas030``.
    """
    return _perform(ctx, _E_PLAUTOGEN_CLOSE)


_E_PLAUTOGEN_DELETE: Final[_Plan] = _Plan(
    "PLautogen-Delete",
    "L1343-L1347",
    "acas030",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def plautogen_delete(ctx: FacadeContext) -> StatusPair:
    """``PLautogen-Delete`` [copybooks/Proc-ACAS-FH-Calls.cob:L1343-L1347].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas030``.
    """
    return _perform(ctx, _E_PLAUTOGEN_DELETE)


_E_PLAUTOGEN_DELETE_ALL: Final[_Plan] = _Plan(
    "PLautogen-Delete-All",
    "L1349-L1353",
    "acas030",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE_ALL),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def plautogen_delete_all(ctx: FacadeContext) -> StatusPair:
    """``PLautogen-Delete-All`` [copybooks/Proc-ACAS-FH-Calls.cob:L1349-L1353].

    Sets function code 6, which NO handler dispatches - every one routes
    it to ``when other`` and a bad-function reply
    [common/acasirsub4.cbl:L235]. Published and permanently unsatisfiable.
    The operation is real but reachable only through the open-output
    coercion [common/irspostingMT.cbl:L271-L272].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas030``.
    """
    return _perform(ctx, _E_PLAUTOGEN_DELETE_ALL)


_E_PLAUTOGEN_START: Final[_Plan] = _Plan(
    "PLautogen-Start",
    "L1355-L1358",
    "acas030",
    (
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.START),
    ),
)


def plautogen_start(ctx: FacadeContext) -> StatusPair:
    """``PLautogen-Start`` [copybooks/Proc-ACAS-FH-Calls.cob:L1355-L1358].

    Deliberately does NOT clear ``Access-Type``: on a START that field
    carries the relation, 5 through 9 of [copybooks/wsfnctn.cob:L112-L116],
    and the caller sets it. Clearing it would change which row is found.

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas030``.
    """
    return _perform(ctx, _E_PLAUTOGEN_START)


_E_PLAUTOGEN_READ_NEXT: Final[_Plan] = _Plan(
    "PLautogen-Read-Next",
    "L1360-L1363",
    "acas030",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def plautogen_read_next(ctx: FacadeContext) -> StatusPair:
    """``PLautogen-Read-Next`` [copybooks/Proc-ACAS-FH-Calls.cob:L1360-L1363].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas030``.
    """
    return _perform(ctx, _E_PLAUTOGEN_READ_NEXT)


_E_PLAUTOGEN_READ_NEXT_HEADER: Final[_Plan] = _Plan(
    "PLautogen-Read-Next-Header",
    "L1365-L1368",
    "acas030",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT_HEADER),
    ),
)


def plautogen_read_next_header(ctx: FacadeContext) -> StatusPair:
    """``PLautogen-Read-Next-Header`` [copybooks/Proc-ACAS-FH-Calls.cob:L1365-L1368].

    Sets function code 34 [copybooks/wsfnctn.cob:L105].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas030``.
    """
    return _perform(ctx, _E_PLAUTOGEN_READ_NEXT_HEADER)


_E_PLAUTOGEN_READ_INDEXED: Final[_Plan] = _Plan(
    "PLautogen-Read-Indexed",
    "L1370-L1374",
    "acas030",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.READ_INDEXED),
    ),
)


def plautogen_read_indexed(ctx: FacadeContext) -> StatusPair:
    """``PLautogen-Read-Indexed`` [copybooks/Proc-ACAS-FH-Calls.cob:L1370-L1374].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas030``.
    """
    return _perform(ctx, _E_PLAUTOGEN_READ_INDEXED)


_E_PLAUTOGEN_WRITE: Final[_Plan] = _Plan(
    "PLautogen-Write",
    "L1376-L1379",
    "acas030",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def plautogen_write(ctx: FacadeContext) -> StatusPair:
    """``PLautogen-Write`` [copybooks/Proc-ACAS-FH-Calls.cob:L1376-L1379].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas030``.
    """
    return _perform(ctx, _E_PLAUTOGEN_WRITE)


_E_PLAUTOGEN_REWRITE: Final[_Plan] = _Plan(
    "PLautogen-Rewrite",
    "L1381-L1384",
    "acas030",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def plautogen_rewrite(ctx: FacadeContext) -> StatusPair:
    """``PLautogen-Rewrite`` [copybooks/Proc-ACAS-FH-Calls.cob:L1381-L1384].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas030``.
    """
    return _perform(ctx, _E_PLAUTOGEN_REWRITE)


# --------------------------------------------------------------------------
# Payments -> acas032 -> OUT OF SCOPE per Agent Action Plan section 0.2.2
# --------------------------------------------------------------------------


_E_PAYMENTS_OPEN: Final[_Plan] = _Plan(
    "Payments-Open",
    "L1388-L1391",
    "acas032",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
)


def payments_open(ctx: FacadeContext) -> StatusPair:
    """``Payments-Open`` [copybooks/Proc-ACAS-FH-Calls.cob:L1388-L1391].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas032``.
    """
    return _perform(ctx, _E_PAYMENTS_OPEN)


_E_PAYMENTS_OPEN_INPUT: Final[_Plan] = _Plan(
    "Payments-Open-Input",
    "L1393-L1396",
    "acas032",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
)


def payments_open_input(ctx: FacadeContext) -> StatusPair:
    """``Payments-Open-Input`` [copybooks/Proc-ACAS-FH-Calls.cob:L1393-L1396].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas032``.
    """
    return _perform(ctx, _E_PAYMENTS_OPEN_INPUT)


_E_PAYMENTS_OPEN_OUTPUT: Final[_Plan] = _Plan(
    "Payments-Open-Output",
    "L1398-L1401",
    "acas032",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.OUTPUT),
    ),
)


def payments_open_output(ctx: FacadeContext) -> StatusPair:
    """``Payments-Open-Output`` [copybooks/Proc-ACAS-FH-Calls.cob:L1398-L1401].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas032``.
    """
    return _perform(ctx, _E_PAYMENTS_OPEN_OUTPUT)


_E_PAYMENTS_CLOSE: Final[_Plan] = _Plan(
    "Payments-Close",
    "L1403-L1406",
    "acas032",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def payments_close(ctx: FacadeContext) -> StatusPair:
    """``Payments-Close`` [copybooks/Proc-ACAS-FH-Calls.cob:L1403-L1406].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas032``.
    """
    return _perform(ctx, _E_PAYMENTS_CLOSE)


_E_PAYMENTS_DELETE: Final[_Plan] = _Plan(
    "Payments-Delete",
    "L1408-L1412",
    "acas032",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def payments_delete(ctx: FacadeContext) -> StatusPair:
    """``Payments-Delete`` [copybooks/Proc-ACAS-FH-Calls.cob:L1408-L1412].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas032``.
    """
    return _perform(ctx, _E_PAYMENTS_DELETE)


_E_PAYMENTS_DELETE_ALL: Final[_Plan] = _Plan(
    "Payments-Delete-All",
    "L1414-L1418",
    "acas032",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE_ALL),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def payments_delete_all(ctx: FacadeContext) -> StatusPair:
    """``Payments-Delete-All`` [copybooks/Proc-ACAS-FH-Calls.cob:L1414-L1418].

    Sets function code 6, which NO handler dispatches - every one routes
    it to ``when other`` and a bad-function reply
    [common/acasirsub4.cbl:L235]. Published and permanently unsatisfiable.
    The operation is real but reachable only through the open-output
    coercion [common/irspostingMT.cbl:L271-L272].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas032``.
    """
    return _perform(ctx, _E_PAYMENTS_DELETE_ALL)


_E_PAYMENTS_START: Final[_Plan] = _Plan(
    "Payments-Start",
    "L1420-L1423",
    "acas032",
    (
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.START),
    ),
)


def payments_start(ctx: FacadeContext) -> StatusPair:
    """``Payments-Start`` [copybooks/Proc-ACAS-FH-Calls.cob:L1420-L1423].

    Deliberately does NOT clear ``Access-Type``: on a START that field
    carries the relation, 5 through 9 of [copybooks/wsfnctn.cob:L112-L116],
    and the caller sets it. Clearing it would change which row is found.

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas032``.
    """
    return _perform(ctx, _E_PAYMENTS_START)


_E_PAYMENTS_READ_NEXT: Final[_Plan] = _Plan(
    "Payments-Read-Next",
    "L1425-L1428",
    "acas032",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def payments_read_next(ctx: FacadeContext) -> StatusPair:
    """``Payments-Read-Next`` [copybooks/Proc-ACAS-FH-Calls.cob:L1425-L1428].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas032``.
    """
    return _perform(ctx, _E_PAYMENTS_READ_NEXT)


_E_PAYMENTS_READ_INDEXED: Final[_Plan] = _Plan(
    "Payments-Read-Indexed",
    "L1430-L1434",
    "acas032",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.READ_INDEXED),
    ),
)


def payments_read_indexed(ctx: FacadeContext) -> StatusPair:
    """``Payments-Read-Indexed`` [copybooks/Proc-ACAS-FH-Calls.cob:L1430-L1434].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas032``.
    """
    return _perform(ctx, _E_PAYMENTS_READ_INDEXED)


_E_PAYMENTS_WRITE: Final[_Plan] = _Plan(
    "Payments-Write",
    "L1436-L1439",
    "acas032",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def payments_write(ctx: FacadeContext) -> StatusPair:
    """``Payments-Write`` [copybooks/Proc-ACAS-FH-Calls.cob:L1436-L1439].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas032``.
    """
    return _perform(ctx, _E_PAYMENTS_WRITE)


_E_PAYMENTS_REWRITE: Final[_Plan] = _Plan(
    "Payments-Rewrite",
    "L1441-L1444",
    "acas032",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def payments_rewrite(ctx: FacadeContext) -> StatusPair:
    """``Payments-Rewrite`` [copybooks/Proc-ACAS-FH-Calls.cob:L1441-L1444].

    Out of scope. Reaching the dispatch step raises
    :exc:`UnsupportedEntityError`; see ``_dispatch_acas032``.
    """
    return _perform(ctx, _E_PAYMENTS_REWRITE)


# ---------------------------------------------------------------------------
# Vocabulary two: the handler-named verbs of
# [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob]
# ---------------------------------------------------------------------------
# 42 paragraphs across six handlers [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:
# L92-L314]. No two handlers publish the same set, and the sets are NOT
# normalised here::
#
#     acas000     7   Open Open-Input Close Read-Next Read-Indexed Write Rewrite
#     acas008     7   Open Open-Input Open-Output Close Read-Next Write Rewrite
#     acasirsub1  10  Open Open-Input Open-Output Close Read-Next Read-Indexed
#                     Start Write Delete Rewrite
#     acasirsub3  6   Open Open-Input Close Read-Next Write ReWrite
#     acasirsub4  6   Open Open-Input Close Read-Next Write Rewrite
#     acasirsub5  6   Open Open-Input Close Read-Next Write ReWrite
#
# Three asymmetries worth stating rather than discovering later:
#
# * ``acas000`` publishes no Open-Output, no START and no Delete, matching its
#   six-code dispatch of 1 2 3 4 5 7.
# * ``acas008`` publishes a rewrite that can never succeed and omits the other
#   three functions its handler also refuses.
# * ``acasirsub4`` publishes no Read-Indexed, no START and no Delete even though
#   [common/acasirsub4.cbl:L218-L235] dispatches codes 4, 8 and 9. Implemented
#   and unpublished - the mirror image of the ``acas008`` rewrite.
#
# WHERE THE CHECK RUNS. Only the open family carries an error check, in all six
# handlers; close, read, write, rewrite, START and delete carry none. And
# ``acasirsub4`` carries none at all. This is what makes the two vocabularies
# behave differently, so it is carried in the plan rather than in the wrapper -
# both vocabularies reach the same ``_perform``.


# --------------------------------------------------------------------------
# acas000
# --------------------------------------------------------------------------


_H_ACAS000_OPEN: Final[_Plan] = _Plan(
    "acas000-Open",
    "L92-L96",
    "acas000-handler",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
    check="acas000",
)


def acas000_open(ctx: FacadeContext) -> StatusPair:
    """``acas000-Open`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L92-L96].

    Runs ``acas000-Check-4-Errors`` after the dispatch, which closes the file
    and raises :exc:`FacadeGoback` on any non-zero reply.
    """
    return _perform(ctx, _H_ACAS000_OPEN)


_H_ACAS000_OPEN_INPUT: Final[_Plan] = _Plan(
    "acas000-Open-Input",
    "L98-L102",
    "acas000-handler",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
    check="acas000",
    check_first=True,
)


def acas000_open_input(ctx: FacadeContext) -> StatusPair:
    """``acas000-Open-Input`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L98-L102].

    THE CHECK RUNS BEFORE THE DISPATCH. Alone among all 42 verb
    paragraphs, this one performs ``acas000-Check-4-Errors`` and only then
    performs ``acas000``. So the check tests whatever ``FS-Reply`` the
    PREVIOUS operation left behind, and this open's own failure is never
    checked at all. Reproduced by ``check_first``, not straightened.
    """
    return _perform(ctx, _H_ACAS000_OPEN_INPUT)


_H_ACAS000_CLOSE: Final[_Plan] = _Plan(
    "acas000-Close",
    "L104-L107",
    "acas000-handler",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def acas000_close(ctx: FacadeContext) -> StatusPair:
    """``acas000-Close`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L104-L107].

    No error check. Only the open family carries one, in all six handlers -
    close, read, write, rewrite, START and delete carry none. This close is
    also what the error check itself performs before aborting, so giving it a
    check would recurse.
    """
    return _perform(ctx, _H_ACAS000_CLOSE)


_H_ACAS000_READ_NEXT: Final[_Plan] = _Plan(
    "acas000-Read-Next",
    "L109-L112",
    "acas000-handler",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def acas000_read_next(ctx: FacadeContext) -> StatusPair:
    """``acas000-Read-Next`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L109-L112]."""
    return _perform(ctx, _H_ACAS000_READ_NEXT)


_H_ACAS000_READ_INDEXED: Final[_Plan] = _Plan(
    "acas000-Read-Indexed",
    "L114-L117",
    "acas000-handler",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_INDEXED),
    ),
)


def acas000_read_indexed(ctx: FacadeContext) -> StatusPair:
    """``acas000-Read-Indexed`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L114-L117]."""
    return _perform(ctx, _H_ACAS000_READ_INDEXED)


_H_ACAS000_WRITE: Final[_Plan] = _Plan(
    "acas000-Write",
    "L119-L122",
    "acas000-handler",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def acas000_write(ctx: FacadeContext) -> StatusPair:
    """``acas000-Write`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L119-L122]."""
    return _perform(ctx, _H_ACAS000_WRITE)


_H_ACAS000_REWRITE: Final[_Plan] = _Plan(
    "acas000-Rewrite",
    "L124-L127",
    "acas000-handler",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def acas000_rewrite(ctx: FacadeContext) -> StatusPair:
    """``acas000-Rewrite`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L124-L127]."""
    return _perform(ctx, _H_ACAS000_REWRITE)


# --------------------------------------------------------------------------
# acas008
# --------------------------------------------------------------------------


_H_ACAS008_OPEN: Final[_Plan] = _Plan(
    "acas008-Open",
    "L130-L134",
    "acas008",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
    check="acas008",
)


def acas008_open(ctx: FacadeContext) -> StatusPair:
    """``acas008-Open`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L130-L134].

    Runs ``acas008-Check-4-Errors`` after the dispatch, which closes the file
    and raises :exc:`FacadeGoback` on any non-zero reply.
    """
    return _perform(ctx, _H_ACAS008_OPEN)


_H_ACAS008_OPEN_INPUT: Final[_Plan] = _Plan(
    "acas008-Open-Input",
    "L136-L140",
    "acas008",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
    check="acas008",
)


def acas008_open_input(ctx: FacadeContext) -> StatusPair:
    """``acas008-Open-Input`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L136-L140]."""
    return _perform(ctx, _H_ACAS008_OPEN_INPUT)


_H_ACAS008_OPEN_OUTPUT: Final[_Plan] = _Plan(
    "acas008-Open-Output",
    "L142-L146",
    "acas008",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.OUTPUT),
    ),
    check="acas008",
)


def acas008_open_output(ctx: FacadeContext) -> StatusPair:
    """``acas008-Open-Output`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L142-L146].

    Reaches the delete-all path. ``acas008`` replaces the function at entry
    [common/acas008.cbl:L313-L319], so an open for output empties the
    transfer file - the mechanism behind the end-of-job clear at
    [irs/irs030.cbl:L1720-L1724].
    """
    return _perform(ctx, _H_ACAS008_OPEN_OUTPUT)


_H_ACAS008_CLOSE: Final[_Plan] = _Plan(
    "acas008-Close",
    "L148-L151",
    "acas008",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def acas008_close(ctx: FacadeContext) -> StatusPair:
    """``acas008-Close`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L148-L151]."""
    return _perform(ctx, _H_ACAS008_CLOSE)


_H_ACAS008_READ_NEXT: Final[_Plan] = _Plan(
    "acas008-Read-Next",
    "L153-L156",
    "acas008",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def acas008_read_next(ctx: FacadeContext) -> StatusPair:
    """``acas008-Read-Next`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L153-L156]."""
    return _perform(ctx, _H_ACAS008_READ_NEXT)


_H_ACAS008_WRITE: Final[_Plan] = _Plan(
    "acas008-Write",
    "L158-L161",
    "acas008",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def acas008_write(ctx: FacadeContext) -> StatusPair:
    """``acas008-Write`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L158-L161]."""
    return _perform(ctx, _H_ACAS008_WRITE)


_H_ACAS008_REWRITE: Final[_Plan] = _Plan(
    "acas008-Rewrite",
    "L163-L166",
    "acas008",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def acas008_rewrite(ctx: FacadeContext) -> StatusPair:
    """``acas008-Rewrite`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L163-L166].

    PUBLISHED AND GUARANTEED TO FAIL - Agent Action Plan section 0.6.7
    entry 6. ``acas008`` refuses rewrite unconditionally at entry
    [common/acas008.cbl:L299-L307] because the transfer file is sequential,
    answering ``FS-Reply`` 99 with ``WE-Error`` 988. It is nonetheless
    published here, so any caller invoking it always fails. Of the four
    functions that handler refuses - read-indexed, rewrite, START and
    delete - this convention publishes ONLY rewrite; the other three are
    absent from it entirely. Returns the failure pair. It does NOT raise:
    raising would be a new behaviour where the COBOL has a status.
    """
    return _perform(ctx, _H_ACAS008_REWRITE)


# --------------------------------------------------------------------------
# acasirsub1
# --------------------------------------------------------------------------


_H_ACASIRSUB1_OPEN: Final[_Plan] = _Plan(
    "acasirsub1-Open",
    "L169-L173",
    "acasirsub1",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
    check="irsub1",
)


def acasirsub1_open(ctx: FacadeContext) -> StatusPair:
    """``acasirsub1-Open`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L169-L173].

    Runs ``irsub1-Check-4-Errors`` after the dispatch, which closes the file
    and raises :exc:`FacadeGoback` on any non-zero reply.
    """
    return _perform(ctx, _H_ACASIRSUB1_OPEN)


_H_ACASIRSUB1_OPEN_INPUT: Final[_Plan] = _Plan(
    "acasirsub1-Open-Input",
    "L175-L179",
    "acasirsub1",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
    check="irsub1",
)


def acasirsub1_open_input(ctx: FacadeContext) -> StatusPair:
    """``acasirsub1-Open-Input`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L175-L179]."""
    return _perform(ctx, _H_ACASIRSUB1_OPEN_INPUT)


_H_ACASIRSUB1_OPEN_OUTPUT: Final[_Plan] = _Plan(
    "acasirsub1-Open-Output",
    "L181-L185",
    "acasirsub1",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.OUTPUT),
    ),
    check="irsub1",
)


def acasirsub1_open_output(ctx: FacadeContext) -> StatusPair:
    """``acasirsub1-Open-Output`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L181-L185]."""
    return _perform(ctx, _H_ACASIRSUB1_OPEN_OUTPUT)


_H_ACASIRSUB1_CLOSE: Final[_Plan] = _Plan(
    "acasirsub1-Close",
    "L187-L190",
    "acasirsub1",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def acasirsub1_close(ctx: FacadeContext) -> StatusPair:
    """``acasirsub1-Close`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L187-L190]."""
    return _perform(ctx, _H_ACASIRSUB1_CLOSE)


_H_ACASIRSUB1_READ_NEXT: Final[_Plan] = _Plan(
    "acasirsub1-Read-Next",
    "L192-L195",
    "acasirsub1",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def acasirsub1_read_next(ctx: FacadeContext) -> StatusPair:
    """``acasirsub1-Read-Next`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L192-L195]."""
    return _perform(ctx, _H_ACASIRSUB1_READ_NEXT)


_H_ACASIRSUB1_READ_INDEXED: Final[_Plan] = _Plan(
    "acasirsub1-Read-Indexed",
    "L197-L200",
    "acasirsub1",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_INDEXED),
    ),
)


def acasirsub1_read_indexed(ctx: FacadeContext) -> StatusPair:
    """``acasirsub1-Read-Indexed`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L197-L200]."""
    return _perform(ctx, _H_ACASIRSUB1_READ_INDEXED)


_H_ACASIRSUB1_START: Final[_Plan] = _Plan(
    "acasirsub1-Start",
    "L202-L205",
    "acasirsub1",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.START),
    ),
)


def acasirsub1_start(ctx: FacadeContext) -> StatusPair:
    """``acasirsub1-Start`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L202-L205].

    Clears ``Access-Type`` before setting the START function, and that
    destroys the relation. On a START that field carries 5 through 9 of
    [copybooks/wsfnctn.cob:L112-L116]; zero is none of them. Every one of the
    twenty entity-named START verbs deliberately leaves the field alone for
    exactly this reason, e.g. [copybooks/Proc-ACAS-FH-Calls.cob:L456-L458].
    This is the only START in the handler convention and it cannot position.
    A third way the two conventions differ in behaviour, after the error
    check and the ``acas000`` key. Reproduced as written.
    """
    return _perform(ctx, _H_ACASIRSUB1_START)


_H_ACASIRSUB1_WRITE: Final[_Plan] = _Plan(
    "acasirsub1-Write",
    "L207-L210",
    "acasirsub1",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def acasirsub1_write(ctx: FacadeContext) -> StatusPair:
    """``acasirsub1-Write`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L207-L210]."""
    return _perform(ctx, _H_ACASIRSUB1_WRITE)


_H_ACASIRSUB1_DELETE: Final[_Plan] = _Plan(
    "acasirsub1-Delete",
    "L212-L215",
    "acasirsub1",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE),
    ),
)


def acasirsub1_delete(ctx: FacadeContext) -> StatusPair:
    """``acasirsub1-Delete`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L212-L215]."""
    return _perform(ctx, _H_ACASIRSUB1_DELETE)


_H_ACASIRSUB1_REWRITE: Final[_Plan] = _Plan(
    "acasirsub1-Rewrite",
    "L217-L220",
    "acasirsub1",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def acasirsub1_rewrite(ctx: FacadeContext) -> StatusPair:
    """``acasirsub1-Rewrite`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L217-L220]."""
    return _perform(ctx, _H_ACASIRSUB1_REWRITE)


# --------------------------------------------------------------------------
# acasirsub3
# --------------------------------------------------------------------------


_H_ACASIRSUB3_OPEN: Final[_Plan] = _Plan(
    "acasirsub3-Open",
    "L223-L227",
    "acasirsub3",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
    check="irsub3",
)


def acasirsub3_open(ctx: FacadeContext) -> StatusPair:
    """``acasirsub3-Open`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L223-L227].

    Runs ``irsub3-Check-4-Errors`` after the dispatch, which closes the file
    and raises :exc:`FacadeGoback` on any non-zero reply.
    """
    return _perform(ctx, _H_ACASIRSUB3_OPEN)


_H_ACASIRSUB3_OPEN_INPUT: Final[_Plan] = _Plan(
    "acasirsub3-Open-Input",
    "L229-L233",
    "acasirsub3",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
    check="irsub3",
)


def acasirsub3_open_input(ctx: FacadeContext) -> StatusPair:
    """``acasirsub3-Open-Input`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L229-L233]."""
    return _perform(ctx, _H_ACASIRSUB3_OPEN_INPUT)


_H_ACASIRSUB3_CLOSE: Final[_Plan] = _Plan(
    "acasirsub3-Close",
    "L235-L238",
    "acasirsub3",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def acasirsub3_close(ctx: FacadeContext) -> StatusPair:
    """``acasirsub3-Close`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L235-L238]."""
    return _perform(ctx, _H_ACASIRSUB3_CLOSE)


_H_ACASIRSUB3_READ_NEXT: Final[_Plan] = _Plan(
    "acasirsub3-Read-Next",
    "L240-L243",
    "acasirsub3",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def acasirsub3_read_next(ctx: FacadeContext) -> StatusPair:
    """``acasirsub3-Read-Next`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L240-L243]."""
    return _perform(ctx, _H_ACASIRSUB3_READ_NEXT)


_H_ACASIRSUB3_WRITE: Final[_Plan] = _Plan(
    "acasirsub3-Write",
    "L245-L248",
    "acasirsub3",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def acasirsub3_write(ctx: FacadeContext) -> StatusPair:
    """``acasirsub3-Write`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L245-L248]."""
    return _perform(ctx, _H_ACASIRSUB3_WRITE)


_H_ACASIRSUB3_REWRITE: Final[_Plan] = _Plan(
    "acasirsub3-ReWrite",
    "L250-L253",
    "acasirsub3",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def acasirsub3_rewrite(ctx: FacadeContext) -> StatusPair:
    """``acasirsub3-ReWrite`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L250-L253].

    Spelled ``ReWrite`` with a capital W, as is ``acasirsub5-ReWrite`` - the
    same two-handler family that also shares the five-code dispatch, 1 2 3 5
    7 with no 4, 8 or 9. The other four handlers spell it ``Rewrite``. Case
    folds in Python; the source spelling is in the traceability footer.
    """
    return _perform(ctx, _H_ACASIRSUB3_REWRITE)


def acasirsub3(ctx: FacadeContext) -> StatusPair:
    """``acasirsub3`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L57-L64].

    THE BARE DISPATCH PARAGRAPH, published because a caller performs it
    directly. The six IRS dispatch paragraphs are otherwise an internal layer
    reached only through a verb paragraph, which is why the other five stay
    private; this one is public because ``irs/irs030.cbl:L1585-L1586`` sets the
    function code by hand and then performs the dispatch paragraph itself::

        move     3  to  file-function.
        perform  acasirsub3.    *> call-irsub3.

    and that site is inside ``Ledger-Postings-Add`` [irs/irs030.cbl:L1569-L1733],
    the one in-scope section of that program. It is the ONLY bare dispatch
    performed from in-scope code: the other four bare performs in the file
    [irs/irs030.cbl:L1147, :L1433, :L1537, :L1539] all sit outside that section.

    The bare form is NOT the same operation as ``acasirsub3-Read-Next``, and the
    difference is load-bearing rather than cosmetic. The verb paragraph moves
    ``zero to Access-Type`` before it dispatches
    [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L240-L243]; the bare paragraph
    performs no such move, so whatever ``Access-Type`` the previous operation
    left behind is carried into this call. Only the key number is pinned. That
    is exactly the two statements of L57-L64, in the source's order, and nothing
    else - so this is a strict alias of the dispatch paragraph and adds no
    behaviour of its own.
    """
    _dispatch_acasirsub3(ctx)
    return StatusPair(ctx.file_access.fs_reply, ctx.file_access.we_error)


# --------------------------------------------------------------------------
# acasirsub4
# --------------------------------------------------------------------------


_H_ACASIRSUB4_OPEN: Final[_Plan] = _Plan(
    "acasirsub4-Open",
    "L256-L259",
    "acasirsub4",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
)


def acasirsub4_open(ctx: FacadeContext) -> StatusPair:
    """``acasirsub4-Open`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L256-L259].

    NO ERROR CHECK, and not by omission. ``acasirsub4`` is dispatched
    [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L69-L77] and publishes six verbs,
    yet there is no ``acasirsub4-Check-4-Errors`` - five checks for six
    dispatched handlers. Three artifacts agree: the copybook has no such
    paragraph; its header lists the messages it uses as "IR911, IR912, IR913,
    IR915, IR916" [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L11], with IR914
    conspicuously absent from the run; and the handler declares no
    module-specific IR9xx message of its own
    [common/acasirsub4.cbl:L127-L131]. When three unrelated places agree on an
    absence, the absence is designed. No check is added.
    """
    return _perform(ctx, _H_ACASIRSUB4_OPEN)


_H_ACASIRSUB4_OPEN_INPUT: Final[_Plan] = _Plan(
    "acasirsub4-Open-Input",
    "L261-L264",
    "acasirsub4",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
)


def acasirsub4_open_input(ctx: FacadeContext) -> StatusPair:
    """``acasirsub4-Open-Input`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L261-L264].

    No error check - see ``acasirsub4_open``.
    """
    return _perform(ctx, _H_ACASIRSUB4_OPEN_INPUT)


_H_ACASIRSUB4_CLOSE: Final[_Plan] = _Plan(
    "acasirsub4-Close",
    "L266-L269",
    "acasirsub4",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def acasirsub4_close(ctx: FacadeContext) -> StatusPair:
    """``acasirsub4-Close`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L266-L269]."""
    return _perform(ctx, _H_ACASIRSUB4_CLOSE)


_H_ACASIRSUB4_READ_NEXT: Final[_Plan] = _Plan(
    "acasirsub4-Read-Next",
    "L271-L274",
    "acasirsub4",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def acasirsub4_read_next(ctx: FacadeContext) -> StatusPair:
    """``acasirsub4-Read-Next`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L271-L274]."""
    return _perform(ctx, _H_ACASIRSUB4_READ_NEXT)


_H_ACASIRSUB4_WRITE: Final[_Plan] = _Plan(
    "acasirsub4-Write",
    "L276-L279",
    "acasirsub4",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def acasirsub4_write(ctx: FacadeContext) -> StatusPair:
    """``acasirsub4-Write`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L276-L279]."""
    return _perform(ctx, _H_ACASIRSUB4_WRITE)


_H_ACASIRSUB4_REWRITE: Final[_Plan] = _Plan(
    "acasirsub4-Rewrite",
    "L281-L284",
    "acasirsub4",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def acasirsub4_rewrite(ctx: FacadeContext) -> StatusPair:
    """``acasirsub4-Rewrite`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L281-L284]."""
    return _perform(ctx, _H_ACASIRSUB4_REWRITE)


# --------------------------------------------------------------------------
# acasirsub5
# --------------------------------------------------------------------------


_H_ACASIRSUB5_OPEN: Final[_Plan] = _Plan(
    "acasirsub5-Open",
    "L287-L291",
    "acasirsub5",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
    check="irsub5",
)


def acasirsub5_open(ctx: FacadeContext) -> StatusPair:
    """``acasirsub5-Open`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L287-L291].

    Runs ``irsub5-Check-4-Errors`` after the dispatch, which closes the file
    and raises :exc:`FacadeGoback` on any non-zero reply.
    """
    return _perform(ctx, _H_ACASIRSUB5_OPEN)


_H_ACASIRSUB5_OPEN_INPUT: Final[_Plan] = _Plan(
    "acasirsub5-Open-Input",
    "L293-L297",
    "acasirsub5",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
    check="irsub5",
)


def acasirsub5_open_input(ctx: FacadeContext) -> StatusPair:
    """``acasirsub5-Open-Input`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L293-L297]."""
    return _perform(ctx, _H_ACASIRSUB5_OPEN_INPUT)


_H_ACASIRSUB5_CLOSE: Final[_Plan] = _Plan(
    "acasirsub5-Close",
    "L299-L302",
    "acasirsub5",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def acasirsub5_close(ctx: FacadeContext) -> StatusPair:
    """``acasirsub5-Close`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L299-L302]."""
    return _perform(ctx, _H_ACASIRSUB5_CLOSE)


_H_ACASIRSUB5_READ_NEXT: Final[_Plan] = _Plan(
    "acasirsub5-Read-Next",
    "L304-L307",
    "acasirsub5",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def acasirsub5_read_next(ctx: FacadeContext) -> StatusPair:
    """``acasirsub5-Read-Next`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L304-L307]."""
    return _perform(ctx, _H_ACASIRSUB5_READ_NEXT)


_H_ACASIRSUB5_WRITE: Final[_Plan] = _Plan(
    "acasirsub5-Write",
    "L309-L312",
    "acasirsub5",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def acasirsub5_write(ctx: FacadeContext) -> StatusPair:
    """``acasirsub5-Write`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L309-L312]."""
    return _perform(ctx, _H_ACASIRSUB5_WRITE)


_H_ACASIRSUB5_REWRITE: Final[_Plan] = _Plan(
    "acasirsub5-ReWrite",
    "L314-L317",
    "acasirsub5",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def acasirsub5_rewrite(ctx: FacadeContext) -> StatusPair:
    """``acasirsub5-ReWrite`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L314-L317].

    Spelled ``ReWrite`` with a capital W, matching ``acasirsub3-ReWrite``.
    """
    return _perform(ctx, _H_ACASIRSUB5_REWRITE)


# ---------------------------------------------------------------------------
# The five error-check paragraphs
# ---------------------------------------------------------------------------
# [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L320-L353]. FIVE checks for SIX
# dispatched handlers: there is no ``acasirsub4-Check-4-Errors``, and three
# unrelated places agree it was never meant to exist - the copybook has no such
# paragraph, its header's message list runs "IR911, IR912, IR913, IR915, IR916"
# [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L11] with IR914 missing from the run,
# and [common/acasirsub4.cbl:L127-L131] declares no module-specific IR9xx
# message under its own "Module Specific" heading. No sixth check is added.
#
# Two naming conventions inside five paragraphs: ``acas000-`` and ``acas008-``
# carry the full handler name while ``irsub1-``, ``irsub3-`` and ``irsub5-`` drop
# the ``acas`` prefix. Both spellings are published verbatim.
#
# Each check is three steps [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L321-L324]:
# test the reply, display a handler-specific message, perform that handler's
# close, and transfer to the shared abort. The display becomes a log record; the
# close and the transfer are preserved, because the close writes to the database
# and the transfer ends the program.


def acas000_check_4_errors(ctx: FacadeContext) -> None:
    """``acas000-Check-4-Errors`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L320-L325].

    Displays ``IR911`` for acas000/systemMT processing, closes, then aborts.
    """
    # [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L320]
    # ``if fs-reply not = zero`` - ANY non-zero reply, not an
    # open-specific test; the open family is simply the only caller.
    if ctx.file_access.fs_reply != FsReply.SUCCESS:
        # ``display IR911 at 0801`` becomes a log record: no database effect,
        # and per Agent Action Plan section 0.3.4 it must not alter control
        # flow. Screen position dropped.
        _LOG.error(
            "IR911 acas000/systemMT processing: FS-Reply=%s WE-Error=%s",
            ctx.file_access.fs_reply,
            ctx.file_access.we_error,
        )
        # ``perform acas000-Close`` - a real database effect inside an error
        # path, so it is preserved. That close carries no check of its own,
        # so this cannot recurse. It also overwrites ``FS-Reply`` and
        # ``WE-Error``, which is why the abort below reports the CLOSE's
        # status and not the failure that got us here - reproduced, not
        # worked around with a snapshot.
        acas000_close(ctx)
        # ``go to Open-Error-Continued``.
        open_error_continued(ctx)


def acas008_check_4_errors(ctx: FacadeContext) -> None:
    """``acas008-Check-4-Errors`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L327-L332].

    Displays ``IR916`` for acas008/slpostingMT processing, closes, then aborts.
    """
    # [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L327]
    # ``if fs-reply not = zero`` - ANY non-zero reply, not an
    # open-specific test; the open family is simply the only caller.
    if ctx.file_access.fs_reply != FsReply.SUCCESS:
        # ``display IR916 at 0801`` becomes a log record: no database effect,
        # and per Agent Action Plan section 0.3.4 it must not alter control
        # flow. Screen position dropped.
        _LOG.error(
            "IR916 acas008/slpostingMT processing: FS-Reply=%s WE-Error=%s",
            ctx.file_access.fs_reply,
            ctx.file_access.we_error,
        )
        # ``perform acas008-Close`` - a real database effect inside an error
        # path, so it is preserved. That close carries no check of its own,
        # so this cannot recurse. It also overwrites ``FS-Reply`` and
        # ``WE-Error``, which is why the abort below reports the CLOSE's
        # status and not the failure that got us here - reproduced, not
        # worked around with a snapshot.
        acas008_close(ctx)
        # ``go to Open-Error-Continued``.
        open_error_continued(ctx)


def irsub1_check_4_errors(ctx: FacadeContext) -> None:
    """``irsub1-Check-4-Errors`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L334-L339].

    Displays ``IR912`` for acasirsub1/irsnominalMT processing, closes, then aborts.
    """
    # [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L334]
    # ``if fs-reply not = zero`` - ANY non-zero reply, not an
    # open-specific test; the open family is simply the only caller.
    if ctx.file_access.fs_reply != FsReply.SUCCESS:
        # ``display IR912 at 0801`` becomes a log record: no database effect,
        # and per Agent Action Plan section 0.3.4 it must not alter control
        # flow. Screen position dropped.
        _LOG.error(
            "IR912 acasirsub1/irsnominalMT processing: FS-Reply=%s WE-Error=%s",
            ctx.file_access.fs_reply,
            ctx.file_access.we_error,
        )
        # ``perform acasirsub1-Close`` - a real database effect inside an error
        # path, so it is preserved. That close carries no check of its own,
        # so this cannot recurse. It also overwrites ``FS-Reply`` and
        # ``WE-Error``, which is why the abort below reports the CLOSE's
        # status and not the failure that got us here - reproduced, not
        # worked around with a snapshot.
        acasirsub1_close(ctx)
        # ``go to Open-Error-Continued``.
        open_error_continued(ctx)


def irsub3_check_4_errors(ctx: FacadeContext) -> None:
    """``irsub3-Check-4-Errors`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L341-L346].

    Displays ``IR913`` for acasirsub3/irsdfltMT processing, closes, then aborts.
    """
    # [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L341]
    # ``if fs-reply not = zero`` - ANY non-zero reply, not an
    # open-specific test; the open family is simply the only caller.
    if ctx.file_access.fs_reply != FsReply.SUCCESS:
        # ``display IR913 at 0801`` becomes a log record: no database effect,
        # and per Agent Action Plan section 0.3.4 it must not alter control
        # flow. Screen position dropped.
        _LOG.error(
            "IR913 acasirsub3/irsdfltMT processing: FS-Reply=%s WE-Error=%s",
            ctx.file_access.fs_reply,
            ctx.file_access.we_error,
        )
        # ``perform acasirsub3-Close`` - a real database effect inside an error
        # path, so it is preserved. That close carries no check of its own,
        # so this cannot recurse. It also overwrites ``FS-Reply`` and
        # ``WE-Error``, which is why the abort below reports the CLOSE's
        # status and not the failure that got us here - reproduced, not
        # worked around with a snapshot.
        acasirsub3_close(ctx)
        # ``go to Open-Error-Continued``.
        open_error_continued(ctx)


def irsub5_check_4_errors(ctx: FacadeContext) -> None:
    """``irsub5-Check-4-Errors`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L348-L353].

    Displays ``IR915`` for acasirsub5/irsfinalMT processing, closes, then aborts.
    """
    # [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L348]
    # ``if fs-reply not = zero`` - ANY non-zero reply, not an
    # open-specific test; the open family is simply the only caller.
    if ctx.file_access.fs_reply != FsReply.SUCCESS:
        # ``display IR915 at 0801`` becomes a log record: no database effect,
        # and per Agent Action Plan section 0.3.4 it must not alter control
        # flow. Screen position dropped.
        _LOG.error(
            "IR915 acasirsub5/irsfinalMT processing: FS-Reply=%s WE-Error=%s",
            ctx.file_access.fs_reply,
            ctx.file_access.we_error,
        )
        # ``perform acasirsub5-Close`` - a real database effect inside an error
        # path, so it is preserved. That close carries no check of its own,
        # so this cannot recurse. It also overwrites ``FS-Reply`` and
        # ``WE-Error``, which is why the abort below reports the CLOSE's
        # status and not the failure that got us here - reproduced, not
        # worked around with a snapshot.
        acasirsub5_close(ctx)
        # ``go to Open-Error-Continued``.
        open_error_continued(ctx)



#: Error-check paragraph to implementation, keyed as ``_Plan.check`` names them.
#: ``acasirsub4`` has NO entry, by design - five checks for six dispatched
#: handlers [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L320-L348]. The absence is
#: the data, which is why this is a table with a missing key rather than a
#: branch that skips one name. Read-only, so the missing key cannot be supplied
#: at run time and a well-meaning caller cannot "complete" the set.
_CHECKS: Final[Mapping[str, Callable[[FacadeContext], None]]] = MappingProxyType({
    "acas000": acas000_check_4_errors,
    "acas008": acas008_check_4_errors,
    "irsub1": irsub1_check_4_errors,
    "irsub3": irsub3_check_4_errors,
    "irsub5": irsub5_check_4_errors,
})


# ---------------------------------------------------------------------------
# The shared abort
# ---------------------------------------------------------------------------
def open_error_continued(ctx: FacadeContext) -> NoReturn:
    """``Open-Error-Continued`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L355-L364].

    The paragraph's own comment reads "If here we cannot continue as its a major
    failure". All five error checks ``go to`` here, so one paragraph aborts the
    caller for any of them.

    It displays five fields and waits for a keypress
    [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L356-L363] and then executes
    ``goback`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L364]. Reproduced as:
    the five displays become log records, the wait is dropped, and the
    ``goback`` becomes :exc:`FacadeGoback`.

    Omitted: the ``display SY008`` [:L362], the ``accept Accept-Reply at 1335``
    [:L363] and the screen positions. Agent Action Plan section 0.3.4 governs all
    three - a prompt whose only effect is to block a terminal is dropped, and
    "where such a prompt sits inside an error path that then transfers control, the
    control transfer is preserved and only the pause is removed". ``SY008`` is that
    prompt's text, "Note message & Hit return" [common/ACAS.cbl:L334], and quoting
    it in a log line, or logging a notice that it was not quoted, is still putting
    an unanswerable prompt in front of an operator. The transfer - the ``goback``
    at [:L364] - is preserved.

    THE FIVE DISPLAYS BECOME ONE RECORD, not four. [:L356-L361] are six
    ``display`` statements building one diagnostic out of four fields, and emitting
    a record per field made one failure look like four, none of which carried the
    identity of the handler that failed. ``SQL-Msg`` [:L361] is dropped from the
    record entirely: it is a ``pic x(512)`` of driver free text, which for these
    tables renders the statement and its bound values, and ``redact_for_log`` was
    escaping it rather than removing it (CWE-532).

    Never raises :exc:`SystemExit` and never terminates the process. ``goback``
    returns to the COBOL program's caller, which here is a ``programs/*`` module
    that may still have end-of-job work whose partial state must survive.
    """
    file_access = ctx.file_access
    logging_data = file_access.logging_data

    # L356-L361, the six displays, as ONE record through the shared reporter, so
    # that this failure reads like every other failure in the package: the status
    # pair from [:L356-L359] and the SQLSTATE from [:L360], with the stable error
    # category derived from them. `SQL-Err` is still read the way the bridges read
    # their fixed-width fields, up to the first space.
    log_handler_failure(
        _LOG,
        program="Proc-ZZ100-ACAS-IRS-Calls",
        paragraph="Open-Error-Continued",
        locator="[copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L355-L364]",
        fs_reply=int(file_access.fs_reply),
        we_error=int(file_access.we_error),
        sql_err=_connection.cobol_string_delimited_by_space(logging_data.sql_err),
        sql_state=_connection.cobol_string_delimited_by_space(
            logging_data.sql_state
        ),
        detail="unrecoverable file-handler failure; the IRS convention's error "
        "check has already named the handler, and this paragraph cannot continue",
    )
    # L362 `display SY008` and L363 `accept Accept-Reply` - the prompt and its wait
    # are one acknowledgement pause, dropped together and NOT announced. A record
    # saying a prompt was not reproduced is itself a presentation record, and it
    # quoted the prompt's own identifier at a destination where no operator can
    # answer it. The omission is documented in the docstring above and in
    # `docs/migration/traceability.md`, which is where a reader looks for it.
    # L364  goback.
    raise FacadeGoback(
        "Open-Error-Continued: unrecoverable file-handler failure; "
        "FS-Reply=%s WE-Error=%s. Reproduces the goback at "
        "[copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L364]."
        % (file_access.fs_reply, file_access.we_error)
    )


# ---------------------------------------------------------------------------
# The published surface
# ---------------------------------------------------------------------------
#: 234 entity-named verbs, 42 handler-named verbs, 5 error checks, the shared
#: abort, and the small amount of vocabulary a caller needs to drive them.
__all__ = (
    "ACCESS_TYPE_LOGGING_RESET",
    "ALWAYS_REFUSED_BY_HANDLER",
    #  The one security-policy door, for the handlers that publish no
    #  keyword-only `transport` on their `dispatch`. Its companion is
    #  `FacadeContext.options`; see THE ONE SECURITY-POLICY CONTRACT.
    "declare_connection_policy",
    "FacadeContext",
    "FacadeError",
    "FacadeGoback",
    "PRIMARY_FILE_KEY_NO",
    "StatusPair",
    "UnsupportedEntityError",
    "acas000_check_4_errors",
    "acas000_close",
    "acas000_open",
    "acas000_open_input",
    "acas000_read_indexed",
    "acas000_read_next",
    "acas000_rewrite",
    "acas000_write",
    "acas008_check_4_errors",
    "acas008_close",
    "acas008_open",
    "acas008_open_input",
    "acas008_open_output",
    "acas008_read_next",
    "acas008_rewrite",
    "acas008_write",
    "acasirsub1_close",
    "acasirsub1_delete",
    "acasirsub1_open",
    "acasirsub1_open_input",
    "acasirsub1_open_output",
    "acasirsub1_read_indexed",
    "acasirsub1_read_next",
    "acasirsub1_rewrite",
    "acasirsub1_start",
    "acasirsub1_write",
    "acasirsub3",
    "acasirsub3_close",
    "acasirsub3_open",
    "acasirsub3_open_input",
    "acasirsub3_read_next",
    "acasirsub3_rewrite",
    "acasirsub3_write",
    "acasirsub4_close",
    "acasirsub4_open",
    "acasirsub4_open_input",
    "acasirsub4_read_next",
    "acasirsub4_rewrite",
    "acasirsub4_write",
    "acasirsub5_close",
    "acasirsub5_open",
    "acasirsub5_open_input",
    "acasirsub5_read_next",
    "acasirsub5_rewrite",
    "acasirsub5_write",
    "analysis_close",
    "analysis_delete",
    "analysis_open",
    "analysis_open_input",
    "analysis_open_output",
    "analysis_read_indexed",
    "analysis_read_next",
    "analysis_rewrite",
    "analysis_start",
    "analysis_write",
    "delfolio_close",
    "delfolio_delete",
    "delfolio_delete_all",
    "delfolio_open",
    "delfolio_open_input",
    "delfolio_open_output",
    "delfolio_read_indexed",
    "delfolio_read_next",
    "delfolio_rewrite",
    "delfolio_start",
    "delfolio_write",
    "delinvnos_close",
    "delinvnos_delete",
    "delinvnos_delete_all",
    "delinvnos_open",
    "delinvnos_open_input",
    "delinvnos_open_output",
    "delinvnos_read_indexed",
    "delinvnos_read_next",
    "delinvnos_rewrite",
    "delinvnos_start",
    "delinvnos_write",
    "delivery_close",
    "delivery_delete",
    "delivery_delete_all",
    "delivery_open",
    "delivery_open_input",
    "delivery_open_output",
    "delivery_read_indexed",
    "delivery_read_next",
    "delivery_rewrite",
    "delivery_start",
    "delivery_write",
    "gl_batch_close",
    "gl_batch_delete",
    "gl_batch_delete_all",
    "gl_batch_open",
    "gl_batch_open_extend",
    "gl_batch_open_input",
    "gl_batch_open_output",
    "gl_batch_read_indexed",
    "gl_batch_read_next",
    "gl_batch_rewrite",
    "gl_batch_start",
    "gl_batch_write",
    "gl_nominal_close",
    "gl_nominal_delete",
    "gl_nominal_open",
    "gl_nominal_open_extend",
    "gl_nominal_open_input",
    "gl_nominal_open_output",
    "gl_nominal_read_indexed",
    "gl_nominal_read_next",
    "gl_nominal_rewrite",
    "gl_nominal_start",
    "gl_nominal_write",
    "gl_posting_close",
    "gl_posting_delete",
    "gl_posting_delete_all",
    "gl_posting_open",
    "gl_posting_open_extend",
    "gl_posting_open_input",
    "gl_posting_open_output",
    "gl_posting_read_indexed",
    "gl_posting_read_next",
    "gl_posting_rewrite",
    "gl_posting_start",
    "gl_posting_write",
    "invoice_close",
    "invoice_delete",
    "invoice_delete_all",
    "invoice_open",
    "invoice_open_input",
    "invoice_open_output",
    "invoice_read_indexed",
    "invoice_read_next",
    "invoice_read_next_header",
    "invoice_rewrite",
    "invoice_start",
    "invoice_write",
    "irsub1_check_4_errors",
    "irsub3_check_4_errors",
    "irsub5_check_4_errors",
    "open_error_continued",
    "otm3_close",
    "otm3_delete",
    "otm3_open",
    "otm3_open_input",
    "otm3_open_output",
    "otm3_read_indexed",
    "otm3_read_next",
    "otm3_read_next_sorted_by_batch",
    "otm3_read_next_sorted_by_cust",
    "otm3_rewrite",
    "otm3_start",
    "otm3_write",
    "otm5_close",
    "otm5_delete",
    "otm5_open",
    "otm5_open_input",
    "otm5_open_output",
    "otm5_read_indexed",
    "otm5_read_next",
    "otm5_read_next_sorted_by_batch",
    "otm5_read_next_sorted_by_cust",
    "otm5_rewrite",
    "otm5_start",
    "otm5_write",
    "payments_close",
    "payments_delete",
    "payments_delete_all",
    "payments_open",
    "payments_open_input",
    "payments_open_output",
    "payments_read_indexed",
    "payments_read_next",
    "payments_rewrite",
    "payments_start",
    "payments_write",
    "pinvoice_close",
    "pinvoice_delete",
    "pinvoice_delete_all",
    "pinvoice_open",
    "pinvoice_open_input",
    "pinvoice_open_output",
    "pinvoice_read_indexed",
    "pinvoice_read_next",
    "pinvoice_read_next_header",
    "pinvoice_rewrite",
    "pinvoice_start",
    "pinvoice_write",
    "plautogen_close",
    "plautogen_delete",
    "plautogen_delete_all",
    "plautogen_open",
    "plautogen_open_input",
    "plautogen_open_output",
    "plautogen_read_indexed",
    "plautogen_read_next",
    "plautogen_read_next_header",
    "plautogen_rewrite",
    "plautogen_start",
    "plautogen_write",
    "purch_close",
    "purch_delete",
    "purch_open",
    "purch_open_input",
    "purch_open_output",
    "purch_read_indexed",
    "purch_read_next",
    "purch_read_next_sorted_byname",
    "purch_rewrite",
    "purch_start",
    "purch_write",
    "sales_close",
    "sales_delete",
    "sales_open",
    "sales_open_input",
    "sales_open_output",
    "sales_read_indexed",
    "sales_read_next",
    "sales_read_next_sorted_by_name",
    "sales_rewrite",
    "sales_start",
    "sales_write",
    "slautogen_close",
    "slautogen_delete",
    "slautogen_delete_all",
    "slautogen_open",
    "slautogen_open_input",
    "slautogen_open_output",
    "slautogen_read_indexed",
    "slautogen_read_next",
    "slautogen_read_next_header",
    "slautogen_rewrite",
    "slautogen_start",
    "slautogen_write",
    "spl_posting_close",
    "spl_posting_delete",
    "spl_posting_delete_all",
    "spl_posting_open",
    "spl_posting_open_extend",
    "spl_posting_open_input",
    "spl_posting_open_output",
    "spl_posting_read_indexed",
    "spl_posting_read_next",
    "spl_posting_rewrite",
    "spl_posting_start",
    "spl_posting_write",
    "stock_audit_close",
    "stock_audit_delete",
    "stock_audit_open",
    "stock_audit_open_extend",
    "stock_audit_open_input",
    "stock_audit_open_output",
    "stock_audit_read_indexed",
    "stock_audit_read_next",
    "stock_audit_rewrite",
    "stock_audit_start",
    "stock_audit_write",
    "stock_close",
    "stock_delete",
    "stock_open",
    "stock_open_input",
    "stock_open_output",
    "stock_read_indexed",
    "stock_read_next",
    "stock_rewrite",
    "stock_start",
    "stock_write",
    "system_close",
    "system_open",
    "system_open_input",
    "system_open_output",
    "system_read_indexed",
    "system_rewrite",
    "system_write",
    "value_close",
    "value_delete",
    "value_delete_all",
    "value_open",
    "value_open_input",
    "value_open_output",
    "value_read_indexed",
    "value_read_next",
    "value_rewrite",
    "value_start",
    "value_write",
)


# --- traceability -----------------------------------------------------------
#
# Rule R-5 requires that every program map to a module, every paragraph to a
# function, and every field to a data-dictionary entry. This module owns the
# paragraph-to-function half for the two facade copybooks, and this footer is
# the mapping itself rather than a description of it -
# ``docs/migration/traceability.md`` is assembled from here.
#
# Reading the tables: the Python name is derived from the COBOL paragraph by one
# rule and one only - hyphens become underscores and case folds to lower.
# Nothing else changes, so the mapping is reversible by inspection. Agent Action
# Plan section 0.4.3 fixes it:
#
#     perform GL-Batch-Read-Next  ->  facade.gl_batch_read_next(ctx)
#     perform acas008-Read-Next   ->  facade.acas008_read_next(ctx)
#
# ===========================================================================
# TABLE 1 OF 7 - ENTITY-NAMED VERBS
#   copybooks/Proc-ACAS-FH-Calls.cob, 234 paragraphs, 21 entities
#   python name / COBOL paragraph / lines / dispatch paragraph
#   None of these runs an error check: that copybook has no such paragraph.
# ===========================================================================
#
# System -> acas000
#   system_open                     System-Open                     L190-L195  acas000
#   system_open_input               System-Open-Input               L197-L202  acas000
#   system_open_output              System-Open-Output              L204-L209  acas000
#   system_close                    System-Close                    L211-L215  acas000
#   system_read_indexed             System-Read-Indexed             L217-L220  acas000
#   system_write                    System-Write                    L222-L225  acas000
#   system_rewrite                  System-ReWrite                  L227-L230  acas000
#
# SLautogen -> acas004 (OUT OF SCOPE: raises UnsupportedEntityError)
#   slautogen_open                  SLautogen-Open                  L234-L237  acas004
#   slautogen_open_input            SLautogen-Open-Input            L239-L242  acas004
#   slautogen_open_output           SLautogen-Open-Output           L244-L247  acas004
#   slautogen_close                 SLautogen-Close                 L249-L252  acas004
#   slautogen_delete                SLautogen-Delete                L254-L258  acas004
#   slautogen_delete_all            SLautogen-Delete-All            L260-L264  acas004
#   slautogen_start                 SLautogen-Start                 L266-L269  acas004
#   slautogen_read_next             SLautogen-Read-Next             L271-L274  acas004
#   slautogen_read_next_header      SLautogen-Read-Next-Header      L276-L279  acas004
#   slautogen_read_indexed          SLautogen-Read-Indexed          L281-L285  acas004
#   slautogen_write                 SLautogen-Write                 L287-L290  acas004
#   slautogen_rewrite               SLautogen-Rewrite               L292-L295  acas004
#
# GL-Nominal -> acas005
#   gl_nominal_open                 GL-Nominal-Open                 L299-L302  acas005
#   gl_nominal_open_input           GL-Nominal-Open-Input           L304-L307  acas005
#   gl_nominal_open_output          GL-Nominal-Open-Output          L309-L312  acas005
#   gl_nominal_open_extend          GL-Nominal-Open-Extend          L314-L317  acas005
#   gl_nominal_close                GL-Nominal-Close                L319-L322  acas005
#   gl_nominal_delete               GL-Nominal-Delete               L324-L328  acas005
#   gl_nominal_start                GL-Nominal-Start                L330-L332  acas005
#   gl_nominal_read_next            GL-Nominal-Read-Next            L334-L337  acas005
#   gl_nominal_read_indexed         GL-Nominal-Read-Indexed         L339-L342  acas005
#   gl_nominal_write                GL-Nominal-Write                L344-L347  acas005
#   gl_nominal_rewrite              GL-Nominal-Rewrite              L349-L352  acas005
#
# GL-Posting -> acas006
#   gl_posting_open                 GL-Posting-Open                 L356-L359  acas006
#   gl_posting_open_input           GL-Posting-Open-Input           L361-L364  acas006
#   gl_posting_open_output          GL-Posting-Open-Output          L366-L369  acas006
#   gl_posting_open_extend          GL-Posting-Open-Extend          L371-L374  acas006
#   gl_posting_close                GL-Posting-Close                L376-L379  acas006
#   gl_posting_delete               GL-Posting-Delete               L381-L385  acas006
#   gl_posting_delete_all           GL-Posting-Delete-All           L387-L391  acas006
#   gl_posting_start                GL-Posting-Start                L393-L395  acas006
#   gl_posting_read_next            GL-Posting-Read-Next            L397-L400  acas006
#   gl_posting_read_indexed         GL-Posting-Read-Indexed         L402-L405  acas006
#   gl_posting_write                GL-Posting-Write                L407-L410  acas006
#   gl_posting_rewrite              GL-Posting-Rewrite              L412-L415  acas006
#
# GL-Batch -> acas007
#   gl_batch_open                   GL-Batch-Open                   L419-L422  acas007
#   gl_batch_open_input             GL-Batch-Open-Input             L424-L427  acas007
#   gl_batch_open_output            GL-Batch-Open-Output            L429-L432  acas007
#   gl_batch_open_extend            GL-Batch-Open-Extend            L434-L437  acas007
#   gl_batch_close                  GL-Batch-Close                  L439-L442  acas007
#   gl_batch_delete                 GL-Batch-Delete                 L444-L448  acas007
#   gl_batch_delete_all             GL-Batch-Delete-All             L450-L454  acas007
#   gl_batch_start                  GL-Batch-Start                  L456-L458  acas007
#   gl_batch_read_next              GL-Batch-Read-Next              L460-L463  acas007
#   gl_batch_read_indexed           GL-Batch-Read-Indexed           L465-L468  acas007
#   gl_batch_write                  GL-Batch-Write                  L470-L473  acas007
#   gl_batch_rewrite                GL-Batch-Rewrite                L475-L478  acas007
#
# SPL-Posting -> acas008
#   spl_posting_open                SPL-Posting-Open                L482-L485  acas008
#   spl_posting_open_input          SPL-Posting-Open-Input          L487-L490  acas008
#   spl_posting_open_output         SPL-Posting-Open-Output         L492-L495  acas008
#   spl_posting_open_extend         SPL-Posting-Open-Extend         L497-L500  acas008
#   spl_posting_close               SPL-Posting-Close               L502-L505  acas008
#   spl_posting_delete              SPL-Posting-Delete              L507-L511  acas008
#   spl_posting_delete_all          SPL-Posting-Delete-All          L513-L517  acas008
#   spl_posting_start               SPL-Posting-Start               L519-L521  acas008
#   spl_posting_read_next           SPL-Posting-Read-Next           L523-L526  acas008
#   spl_posting_read_indexed        SPL-Posting-Read-Indexed        L528-L531  acas008
#   spl_posting_write               SPL-Posting-Write               L533-L536  acas008
#   spl_posting_rewrite             SPL-Posting-Rewrite             L538-L541  acas008
#
# Stock-Audit -> acas010 (OUT OF SCOPE: raises UnsupportedEntityError)
#   stock_audit_open                Stock-Audit-Open                L545-L548  acas010
#   stock_audit_open_input          Stock-Audit-Open-Input          L550-L553  acas010
#   stock_audit_open_output         Stock-Audit-Open-Output         L555-L558  acas010
#   stock_audit_open_extend         Stock-Audit-Open-Extend         L560-L563  acas010
#   stock_audit_close               Stock-Audit-Close               L565-L568  acas010
#   stock_audit_delete              Stock-Audit-Delete              L570-L574  acas010
#   stock_audit_start               Stock-Audit-Start               L576-L578  acas010
#   stock_audit_read_next           Stock-Audit-Read-Next           L580-L583  acas010
#   stock_audit_read_indexed        Stock-Audit-Read-Indexed        L585-L588  acas010
#   stock_audit_write               Stock-Audit-Write               L590-L593  acas010
#   stock_audit_rewrite             Stock-Audit-Rewrite             L595-L598  acas010
#
# Stock -> acas011 (OUT OF SCOPE: raises UnsupportedEntityError)
#   stock_open                      Stock-Open                      L602-L605  acas011
#   stock_open_input                Stock-Open-Input                L607-L610  acas011
#   stock_open_output               Stock-Open-Output               L612-L615  acas011
#   stock_close                     Stock-Close                     L617-L620  acas011
#   stock_delete                    Stock-Delete                    L622-L626  acas011
#   stock_start                     Stock-Start                     L628-L630  acas011
#   stock_read_next                 Stock-Read-Next                 L632-L635  acas011
#   stock_read_indexed              Stock-Read-Indexed              L637-L640  acas011
#   stock_write                     Stock-Write                     L642-L645  acas011
#   stock_rewrite                   Stock-Rewrite                   L647-L650  acas011
#
# Sales -> acas012
#   sales_open                      Sales-Open                      L654-L657  acas012
#   sales_open_input                Sales-Open-Input                L659-L662  acas012
#   sales_open_output               Sales-Open-Output               L664-L667  acas012
#   sales_close                     Sales-Close                     L669-L672  acas012
#   sales_delete                    Sales-Delete                    L674-L678  acas012
#   sales_start                     Sales-Start                     L680-L682  acas012
#   sales_read_next                 Sales-Read-Next                 L684-L687  acas012
#   sales_read_next_sorted_by_name  Sales-Read-Next-Sorted-By-Name  L689-L692  acas012
#   sales_read_indexed              Sales-Read-Indexed              L694-L697  acas012
#   sales_write                     Sales-Write                     L699-L702  acas012
#   sales_rewrite                   Sales-Rewrite                   L704-L707  acas012
#
# Value -> acas013
#   value_open                      Value-Open                      L711-L714  acas013
#   value_open_input                Value-Open-Input                L716-L719  acas013
#   value_open_output               Value-Open-Output               L721-L724  acas013
#   value_close                     Value-Close                     L726-L729  acas013
#   value_delete                    Value-Delete                    L731-L735  acas013
#   value_delete_all                Value-Delete-All                L737-L741  acas013
#   value_start                     Value-Start                     L743-L746  acas013
#   value_read_next                 Value-Read-Next                 L748-L751  acas013
#   value_read_indexed              Value-Read-Indexed              L753-L757  acas013
#   value_write                     Value-Write                     L759-L762  acas013
#   value_rewrite                   Value-Rewrite                   L764-L767  acas013
#
# Delivery -> acas014 (OUT OF SCOPE: raises UnsupportedEntityError)
#   delivery_open                   Delivery-Open                   L771-L774  acas014
#   delivery_open_input             Delivery-Open-Input             L776-L779  acas014
#   delivery_open_output            Delivery-Open-Output            L781-L784  acas014
#   delivery_close                  Delivery-Close                  L786-L789  acas014
#   delivery_delete                 Delivery-Delete                 L791-L795  acas014
#   delivery_delete_all             Delivery-Delete-All             L797-L801  acas014
#   delivery_start                  Delivery-Start                  L803-L806  acas014
#   delivery_read_next              Delivery-Read-Next              L808-L811  acas014
#   delivery_read_indexed           Delivery-Read-Indexed           L813-L817  acas014
#   delivery_write                  Delivery-Write                  L819-L822  acas014
#   delivery_rewrite                Delivery-Rewrite                L824-L827  acas014
#
# Analysis -> acas015
#   analysis_open                   Analysis-Open                   L831-L834  acas015
#   analysis_open_input             Analysis-Open-Input             L836-L839  acas015
#   analysis_open_output            Analysis-Open-Output            L841-L844  acas015
#   analysis_close                  Analysis-Close                  L846-L849  acas015
#   analysis_delete                 Analysis-Delete                 L851-L855  acas015
#   analysis_start                  Analysis-Start                  L857-L860  acas015
#   analysis_read_next              Analysis-Read-Next              L862-L865  acas015
#   analysis_read_indexed           Analysis-Read-Indexed           L867-L871  acas015
#   analysis_write                  Analysis-Write                  L873-L876  acas015
#   analysis_rewrite                Analysis-Rewrite                L878-L881  acas015
#
# Invoice -> acas016
#   invoice_open                    Invoice-Open                    L885-L888  acas016
#   invoice_open_input              Invoice-Open-Input              L890-L893  acas016
#   invoice_open_output             Invoice-Open-Output             L895-L898  acas016
#   invoice_close                   Invoice-Close                   L900-L903  acas016
#   invoice_delete                  Invoice-Delete                  L905-L909  acas016
#   invoice_delete_all              Invoice-Delete-All              L911-L915  acas016
#   invoice_start                   Invoice-Start                   L917-L920  acas016
#   invoice_read_next               Invoice-Read-Next               L922-L925  acas016
#   invoice_read_next_header        Invoice-Read-Next-Header        L927-L930  acas016
#   invoice_read_indexed            Invoice-Read-Indexed            L932-L936  acas016
#   invoice_write                   Invoice-Write                   L938-L941  acas016
#   invoice_rewrite                 Invoice-Rewrite                 L943-L946  acas016
#
# DelInvNos -> acas017 (OUT OF SCOPE: raises UnsupportedEntityError)
#   delinvnos_open                  DelInvNos-Open                  L950-L953  acas017
#   delinvnos_open_input            DelInvNos-Open-Input            L955-L958  acas017
#   delinvnos_open_output           DelInvNos-Open-Output           L960-L963  acas017
#   delinvnos_close                 DelInvNos-Close                 L965-L968  acas017
#   delinvnos_delete                DelInvNos-Delete                L970-L974  acas017
#   delinvnos_delete_all            DelInvNos-Delete-All            L976-L980  acas017
#   delinvnos_start                 DelInvNos-Start                 L982-L985  acas017
#   delinvnos_read_next             DelInvNos-Read-Next             L987-L990  acas017
#   delinvnos_read_indexed          DelInvNos-Read-Indexed          L992-L996  acas017
#   delinvnos_write                 DelInvNos-Write                 L998-L1001  acas017
#   delinvnos_rewrite               DelInvNos-Rewrite               L1003-L1006  acas017
#
# OTM3 -> acas019
#   otm3_open                       OTM3-Open                       L1010-L1013  acas019
#   otm3_open_input                 OTM3-Open-Input                 L1015-L1018  acas019
#   otm3_open_output                OTM3-Open-Output                L1020-L1023  acas019
#   otm3_close                      OTM3-Close                      L1025-L1028  acas019
#   otm3_delete                     OTM3-Delete                     L1030-L1034  acas019
#   otm3_start                      OTM3-Start                      L1036-L1039  acas019
#   otm3_read_next                  OTM3-Read-Next                  L1041-L1044  acas019
#   otm3_read_indexed               OTM3-Read-Indexed               L1046-L1050  acas019
#   otm3_read_next_sorted_by_batch  OTM3-Read-Next-Sorted-By-Batch  L1052-L1055  acas019
#   otm3_read_next_sorted_by_cust   OTM3-Read-Next-Sorted-By-Cust   L1057-L1060  acas019
#   otm3_write                      OTM3-Write                      L1062-L1065  acas019
#   otm3_rewrite                    OTM3-Rewrite                    L1067-L1070  acas019
#
# Purch -> acas022
#   purch_open                      Purch-Open                      L1074-L1077  acas022
#   purch_open_input                Purch-Open-Input                L1079-L1082  acas022
#   purch_open_output               Purch-Open-Output               L1084-L1087  acas022
#   purch_close                     Purch-Close                     L1089-L1092  acas022
#   purch_delete                    Purch-Delete                    L1094-L1098  acas022
#   purch_start                     Purch-Start                     L1100-L1103  acas022
#   purch_read_next                 Purch-Read-Next                 L1105-L1108  acas022
#   purch_read_next_sorted_byname   Purch-Read-Next-Sorted-ByName   L1110-L1113  acas022
#   purch_read_indexed              Purch-Read-Indexed              L1115-L1119  acas022
#   purch_write                     Purch-Write                     L1121-L1124  acas022
#   purch_rewrite                   Purch-Rewrite                   L1126-L1129  acas022
#
# DelFolio -> acas023 (OUT OF SCOPE: raises UnsupportedEntityError)
#   delfolio_open                   DelFolio-Open                   L1133-L1136  acas023
#   delfolio_open_input             DelFolio-Open-Input             L1138-L1141  acas023
#   delfolio_open_output            DelFolio-Open-Output            L1143-L1146  acas023
#   delfolio_close                  DelFolio-Close                  L1148-L1151  acas023
#   delfolio_delete                 DelFolio-Delete                 L1153-L1157  acas023
#   delfolio_delete_all             DelFolio-Delete-All             L1159-L1163  acas023
#   delfolio_start                  DelFolio-Start                  L1165-L1168  acas023
#   delfolio_read_next              DelFolio-Read-Next              L1170-L1173  acas023
#   delfolio_read_indexed           DelFolio-Read-Indexed           L1175-L1179  acas023
#   delfolio_write                  DelFolio-Write                  L1181-L1184  acas023
#   delfolio_rewrite                DelFolio-Rewrite                L1186-L1189  acas023
#
# PInvoice -> acas026
#   pinvoice_open                   PInvoice-Open                   L1193-L1196  acas026
#   pinvoice_open_input             PInvoice-Open-Input             L1198-L1201  acas026
#   pinvoice_open_output            PInvoice-Open-Output            L1203-L1206  acas026
#   pinvoice_close                  PInvoice-Close                  L1208-L1211  acas026
#   pinvoice_delete                 PInvoice-Delete                 L1213-L1217  acas026
#   pinvoice_delete_all             PInvoice-Delete-All             L1219-L1223  acas026
#   pinvoice_start                  PInvoice-Start                  L1225-L1228  acas026
#   pinvoice_read_next              PInvoice-Read-Next              L1230-L1233  acas026
#   pinvoice_read_next_header       PInvoice-Read-Next-Header       L1235-L1238  acas026
#   pinvoice_read_indexed           PInvoice-Read-Indexed           L1240-L1244  acas026
#   pinvoice_write                  PInvoice-Write                  L1246-L1249  acas026
#   pinvoice_rewrite                PInvoice-Rewrite                L1251-L1254  acas026
#
# OTM5 -> acas029
#   otm5_open                       OTM5-Open                       L1258-L1261  acas029
#   otm5_open_input                 OTM5-Open-Input                 L1263-L1266  acas029
#   otm5_open_output                OTM5-Open-Output                L1268-L1271  acas029
#   otm5_close                      OTM5-Close                      L1273-L1276  acas029
#   otm5_delete                     OTM5-Delete                     L1278-L1282  acas029
#   otm5_start                      OTM5-Start                      L1284-L1287  acas029
#   otm5_read_next                  OTM5-Read-Next                  L1289-L1292  acas029
#   otm5_read_indexed               OTM5-Read-Indexed               L1294-L1298  acas029
#   otm5_read_next_sorted_by_batch  OTM5-Read-Next-Sorted-By-Batch  L1300-L1303  acas029
#   otm5_read_next_sorted_by_cust   OTM5-Read-Next-Sorted-By-Cust   L1305-L1308  acas029
#   otm5_write                      OTM5-Write                      L1310-L1313  acas029
#   otm5_rewrite                    OTM5-Rewrite                    L1315-L1318  acas029
#
# PLautogen -> acas030 (OUT OF SCOPE: raises UnsupportedEntityError)
#   plautogen_open                  PLautogen-Open                  L1323-L1326  acas030
#   plautogen_open_input            PLautogen-Open-Input            L1328-L1331  acas030
#   plautogen_open_output           PLautogen-Open-Output           L1333-L1336  acas030
#   plautogen_close                 PLautogen-Close                 L1338-L1341  acas030
#   plautogen_delete                PLautogen-Delete                L1343-L1347  acas030
#   plautogen_delete_all            PLautogen-Delete-All            L1349-L1353  acas030
#   plautogen_start                 PLautogen-Start                 L1355-L1358  acas030
#   plautogen_read_next             PLautogen-Read-Next             L1360-L1363  acas030
#   plautogen_read_next_header      PLautogen-Read-Next-Header      L1365-L1368  acas030
#   plautogen_read_indexed          PLautogen-Read-Indexed          L1370-L1374  acas030
#   plautogen_write                 PLautogen-Write                 L1376-L1379  acas030
#   plautogen_rewrite               PLautogen-Rewrite               L1381-L1384  acas030
#
# Payments -> acas032 (OUT OF SCOPE: raises UnsupportedEntityError)
#   payments_open                   Payments-Open                   L1388-L1391  acas032
#   payments_open_input             Payments-Open-Input             L1393-L1396  acas032
#   payments_open_output            Payments-Open-Output            L1398-L1401  acas032
#   payments_close                  Payments-Close                  L1403-L1406  acas032
#   payments_delete                 Payments-Delete                 L1408-L1412  acas032
#   payments_delete_all             Payments-Delete-All             L1414-L1418  acas032
#   payments_start                  Payments-Start                  L1420-L1423  acas032
#   payments_read_next              Payments-Read-Next              L1425-L1428  acas032
#   payments_read_indexed           Payments-Read-Indexed           L1430-L1434  acas032
#   payments_write                  Payments-Write                  L1436-L1439  acas032
#   payments_rewrite                Payments-Rewrite                L1441-L1444  acas032
#
# ===========================================================================
# TABLE 2 OF 7 - HANDLER-NAMED VERBS
#   copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob, 42 paragraphs, 6 handlers
#   python name / COBOL paragraph / lines / error check run
#   No two handlers publish the same set: 7, 7, 10, 6, 6, 6.
#   "check" names the paragraph performed; "-" means none is performed at all.
# ===========================================================================
#
# acas000 - no Open-Output, no Start, no Delete - matches its six-code dispatch
#   acas000_open             acas000-Open             L92-L96    acas000-Check-4-Errors
#   acas000_open_input       acas000-Open-Input       L98-L102   acas000-Check-4-Errors
#       ^ this one performs its check BEFORE the dispatch - see N1
#   acas000_close            acas000-Close            L104-L107  -
#   acas000_read_next        acas000-Read-Next        L109-L112  -
#   acas000_read_indexed     acas000-Read-Indexed     L114-L117  -
#   acas000_write            acas000-Write            L119-L122  -
#   acas000_rewrite          acas000-Rewrite          L124-L127  -
#
# acas008 - publishes a rewrite that can never succeed; omits the other 3 it refuses
#   acas008_open             acas008-Open             L130-L134  acas008-Check-4-Errors
#   acas008_open_input       acas008-Open-Input       L136-L140  acas008-Check-4-Errors
#   acas008_open_output      acas008-Open-Output      L142-L146  acas008-Check-4-Errors
#   acas008_close            acas008-Close            L148-L151  -
#   acas008_read_next        acas008-Read-Next        L153-L156  -
#   acas008_write            acas008-Write            L158-L161  -
#   acas008_rewrite          acas008-Rewrite          L163-L166  -
#
# acasirsub1 - the only 10-verb handler, and the only Start in this convention
#   acasirsub1_open          acasirsub1-Open          L169-L173  irsub1-Check-4-Errors
#   acasirsub1_open_input    acasirsub1-Open-Input    L175-L179  irsub1-Check-4-Errors
#   acasirsub1_open_output   acasirsub1-Open-Output   L181-L185  irsub1-Check-4-Errors
#   acasirsub1_close         acasirsub1-Close         L187-L190  -
#   acasirsub1_read_next     acasirsub1-Read-Next     L192-L195  -
#   acasirsub1_read_indexed  acasirsub1-Read-Indexed  L197-L200  -
#   acasirsub1_start         acasirsub1-Start         L202-L205  -
#   acasirsub1_write         acasirsub1-Write         L207-L210  -
#   acasirsub1_delete        acasirsub1-Delete        L212-L215  -
#   acasirsub1_rewrite       acasirsub1-Rewrite       L217-L220  -
#
# acasirsub3 - 6 verbs; ReWrite spelled with a capital W
#   acasirsub3_open          acasirsub3-Open          L223-L227  irsub3-Check-4-Errors
#   acasirsub3_open_input    acasirsub3-Open-Input    L229-L233  irsub3-Check-4-Errors
#   acasirsub3_close         acasirsub3-Close         L235-L238  -
#   acasirsub3_read_next     acasirsub3-Read-Next     L240-L243  -
#   acasirsub3_write         acasirsub3-Write         L245-L248  -
#   acasirsub3_rewrite       acasirsub3-ReWrite       L250-L253  -
#   acasirsub3               acasirsub3               L57-L64    -
#     ^ the DISPATCH paragraph, not a verb paragraph. Published because
#       [irs/irs030.cbl:L1585-L1586] sets file-function by hand and performs it
#       bare, inside the in-scope Ledger-Postings-Add section. The other five
#       dispatch paragraphs stay private: no in-scope caller performs them bare.
#
# acasirsub4 - 6 verbs; NO error check paragraph exists for it at all
#   acasirsub4_open          acasirsub4-Open          L256-L259  -
#   acasirsub4_open_input    acasirsub4-Open-Input    L261-L264  -
#   acasirsub4_close         acasirsub4-Close         L266-L269  -
#   acasirsub4_read_next     acasirsub4-Read-Next     L271-L274  -
#   acasirsub4_write         acasirsub4-Write         L276-L279  -
#   acasirsub4_rewrite       acasirsub4-Rewrite       L281-L284  -
#
# acasirsub5 - 6 verbs; ReWrite spelled with a capital W
#   acasirsub5_open          acasirsub5-Open          L287-L291  irsub5-Check-4-Errors
#   acasirsub5_open_input    acasirsub5-Open-Input    L293-L297  irsub5-Check-4-Errors
#   acasirsub5_close         acasirsub5-Close         L299-L302  -
#   acasirsub5_read_next     acasirsub5-Read-Next     L304-L307  -
#   acasirsub5_write         acasirsub5-Write         L309-L312  -
#   acasirsub5_rewrite       acasirsub5-ReWrite       L314-L317  -
#
# ===========================================================================
# TABLE 3 OF 7 - ERROR CHECKS AND THE SHARED ABORT
#   Five checks for six dispatched handlers. Both source naming conventions are
#   preserved: acas000-/acas008- full, irsub1-/irsub3-/irsub5- abbreviated.
# ===========================================================================
#   python name              COBOL paragraph          lines      message  closes
#   acas000_check_4_errors   acas000-Check-4-Errors   L320-L325  IR911    acas000-Close
#   acas008_check_4_errors   acas008-Check-4-Errors   L327-L332  IR916    acas008-Close
#   irsub1_check_4_errors    irsub1-Check-4-Errors    L334-L339  IR912    acasirsub1-Close
#   irsub3_check_4_errors    irsub3-Check-4-Errors    L341-L346  IR913    acasirsub3-Close
#   irsub5_check_4_errors    irsub5-Check-4-Errors    L348-L353  IR915    acasirsub5-Close
#   open_error_continued     Open-Error-Continued     L355-L364  SY008    (none) -> goback L364
#
#   There is deliberately NO acasirsub4 check. IR914 is absent from the whole
#   run, the copybook header's own list at L11 skips it, and
#   [common/acasirsub4.cbl:L127-L131] declares no module-specific message.
#
# ===========================================================================
# TABLE 4 OF 7 - FUNCTION-CODE DISPATCH MATRIX
#   Censused from every "when <n>" in all seventeen handler programs. Carries
#   two corrections against earlier working notes, marked (!).
# ===========================================================================
#   acas000      1 2 3 4 5 7            (!) six codes - no 8, no 9
#   acas005      1 2 3 4 5 7 8 9
#   acas006      1 2 3 4 5 7 8 9
#   acas007      1 2 3 4 5 7 8 9
#   acas008      1 2 3 4 5 7 8 9        4, 7, 8, 9 refused at entry L299-L307
#   acas012      1 2 3 4 5 7 8 9 31     [common/acas012.cbl:L342]
#   acas013      1 2 3 4 5 7 8 9
#   acas015      1 2 3 4 5 7 8 9
#   acas016      1 2 3 4 5 7 8 9 34     [common/acas016.cbl:L297]
#   acas019      1 2 3 4 5 7 8 9        does NOT dispatch 32 or 33
#   acas022      1 2 3 4 5 7 8 9 31     [common/acas022.cbl:L344]
#   acas026      1 2 3 4 5 7 8 9 34     (!) 34, NOT 31 [common/acas026.cbl:L289]
#   acas029      1 2 3 4 5 7 8 9        does NOT dispatch 32 or 33
#   acasirsub1   1 2 3 4 5 7 8 9 13 15  the only handler with the raw verbs
#   acasirsub3   1 2 3 5 7              no 4, no 8, no 9
#   acasirsub4   1 2 3 4 5 7 8 9        "when other *> 6 is unused"
#   acasirsub5   1 2 3 5 7              no 4, no 8, no 9
#
#   Code 6, fn-Delete-All: dispatched by NO handler, yet
#   [common/irspostingMT.cbl:L271-L272] implements it - "when 6 *> DELETE-ALL
#   Special" routed to a paragraph flagged "THIS IS NON STANDARD" at L790. So it
#   is not unreachable: it is reachable only through the open-output coercion
#   [common/acas008.cbl:L313-L319], never by direct dispatch. Twelve entity
#   paragraphs publish a -Delete-All verb regardless.
#   Codes 32 and 33: declared for OTM3/OTM5 [copybooks/wsfnctn.cob:L103-L104]
#   and dispatched by nobody, including the two handlers named. Four entity
#   paragraphs publish them regardless.
#   Codes 15 and 13: declared in that order - out of numeric sequence -
#   [copybooks/wsfnctn.cob:L99-L100], "Special 4 LD" for the common/*LD.cbl
#   loaders. Dispatched only by acasirsub1 and published by NEITHER copybook.
#   No facade alias exists for them: implemented, and unpublished.
#   Access type 4, fn-extend: "not valid for ISAM"
#   [copybooks/wsfnctn.cob:L111] and never dispatched on the relational path.
#   Five entity paragraphs publish an -Open-Extend verb regardless.
#
# ===========================================================================
# TABLE 5 OF 7 - THE FOUR OPEN-OUTPUT BEHAVIOURS
# ===========================================================================
#   acas005                   coercion block COMMENTED OUT, "NOT used with GL."
#                             [common/acas005.cbl:L307-L314] [:L649-L656]
#   acas006 acas007           TWO bridge calls - open, then delete-all by
#   acasirsub1 acasirsub4     fall-through. [common/acas006.cbl:L313-L318]
#                             [:L640-L644]; [common/acasirsub1.cbl:L738-L742]
#                             +L751; [common/acasirsub4.cbl:L518-L522]+L531.
#                             acasirsub4 is the origin -
#                             [common/acasirsub1.cbl:L247] records "TAKEN from
#                             acasirsub4 22/12/16".
#   acas008                   ONE coerced call, function replaced at entry.
#                             [common/acas008.cbl:L313-L319] [:L571-L574]
#   acas015 acas016 acas019   ABSENT ENTIRELY - no "fn-Open and" match.
#   acas022 acas026 acas029
#   acasirsub3 acasirsub5
#
# ===========================================================================
# TABLE 6 OF 7 - THE DAL-CALL PARAGRAPH, FOUR NAMING FORMS
#   Where to find the CALL site inside each handler program.
# ===========================================================================
#   ba020-Process-DAL   acas005 L662, acas006 L653, acas007 L640, acas012,
#                       acasirsub1 L751, acasirsub4 L531          - six
#   ba020-Call-DAL      acasirsub3 L521, acasirsub5 L512          - two
#   ba020-Call          acas013 L663                              - one
#   inline, no para     acas008, acas015, acas016, acas019, acas022,
#                       acas026, acas029                          - seven
#
# ===========================================================================
# TABLE 7 OF 7 - THE WS-LOG-FILE-NO CENSUS
#   Only the (WS-Log-System, WS-Log-File-No) pair identifies a handler.
#   Carries one correction against an earlier working note, marked (!).
# ===========================================================================
#   flat -> rdb   handlers (WS-Log-System in brackets)
#   11 -> 21      acas005 [2], acas012 [3], acas022 [4], acasirsub1 [1]
#   12 -> 22      acas015 [6], acas016 [3], acasirsub3 [1]
#   12 -> 12      acas026 [4]                    no increment, unique
#   13 -> 23      acas013 [6], acasirsub4 [1]
#   14 -> 24      acasirsub5 [1]             (!) 14 IS used - sole occupant
#   15 -> 25      acas008 [1], acas019 [3], acas029 [4]
#
#   WS-Log-System: acas000=0, acas005/006/007=2, acas008=1, acas012=3,
#   acas013=6, acas015=6, acas016=3, acas019=3, acas022=4, acas026=4,
#   acas029=4, acasirsub1/3/4/5=1. The legend contradicts itself across files -
#   [common/acas013.cbl:L298] against [common/acas016.cbl:L248] - and the value
#   6 is used by two handlers whose own legend does not define it.
#
# ===========================================================================
# DELIBERATE OMISSIONS - recorded as omissions per AAP section 0.5.3
# ===========================================================================
#   * Every "display" in the five checks and in Open-Error-Continued becomes a
#     log record; every screen position is dropped.
#     [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L322] [:L356-L362]
#   * "accept Accept-Reply at 1335" is dropped entirely - a pause with no
#     database effect. [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L363]
#   * The FH log-writing program: out of scope per AAP section 0.2.2. Nothing is
#     omitted at THIS layer - an exhaustive scan of both copybooks finds neither
#     performs nor calls any logging routine. The only non-dispatch "perform" in
#     either file is one of the five error checks. Logging belongs to the
#     handler programs and the handler modules own it.
#   * Eight out-of-scope entities, 89 of the 234 paragraphs: DelFolio,
#     DelInvNos, Delivery, PLautogen, Payments, SLautogen, Stock, Stock-Audit.
#     Names published; UnsupportedEntityError at the dispatch step; no SQL.
#   * Codes 32 and 33 - published by four entity paragraphs, dispatched by
#     nobody. Code 6 - published by twelve, dispatched by nobody. Access type 4
#     - published by five, dispatched by nobody. All published as they exist.
#   * Codes 13 and 15 - implemented by acasirsub1, published by neither
#     copybook. No alias added.
#
# ===========================================================================
# ANOMALY INDEX - reproduced, never repaired (Rule R-4)
# ===========================================================================
#   A1  the two conventions BEHAVE differently        _perform, _Plan.check
#   A2  a published verb that can never succeed       acas008_rewrite
#   A3  only rewrite of the four refused is published acas008_* set
#   A4  Open-Error-Continued ends in goback           FacadeGoback
#   A5  each check closes before aborting             the five checks
#   A6  five checks for six handlers                  _CHECKS has no irsub4 key
#   A7  no two handlers publish the same set          Table 2
#   A8  acasirsub4 omits 3 verbs it implements        Table 2, Table 4
#   A9  the raw verbs are published by neither        Table 4
#   A10 delete-all reachable only via open-output     *_open_output, Table 4
#   A11 codes 32/33 declared and dispatched by none   otm3_*/otm5_* sorted verbs
#   A12 ReWrite with a capital W                      acasirsub3/5, System
#   A13 two naming conventions in five checks         Table 3
#   A14 acas000 is a five-way key dispatcher          _dispatch_acas000_entity
#   A15 the entity grid is incomplete                 234 published, none added
#   A16 eight entities out of scope                   UnsupportedEntityError
#   A17 raw verbs declared 15 then 13                 Table 4
#   A18 Access-Type is one digit, two meanings        imported, not redeclared
#   A19 handler 999 against bridge 990                module docstring
#   A20 four DAL-call naming forms                    Table 6
#   A21 the WS-Log-System legend self-contradicts     Table 7
#   A22 fn-extend declared, never reached             *_open_extend, Table 4
#
#   Found while transcribing, and not in the register this module was given.
#   Each is reproduced and cited at its site:
#   N1  acas000-Open-Input checks BEFORE it dispatches, alone among 42
#       paragraphs, so it tests the previous operation's reply and never its
#       own. [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L98-L102]
#   N2  only the open family carries a check; close, read, write, rewrite,
#       START and delete carry none, in all six handlers.
#   N3  the check tests "fs-reply not = zero" - any non-zero reply, not an
#       open-specific condition. [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L321]
#   N4  a SECOND asymmetry between the conventions: the entity side dispatches
#       acas000 with NO File-Key-No move so the caller's key survives
#       [copybooks/Proc-ACAS-FH-Calls.cob:L20-L24], while the handler side pins
#       it to 1 [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L22-L29]. Two dispatch
#       functions, not one.
#   N5  18 distinct entity verb suffixes, not 12; and Purch spells it
#       "Sorted-ByName" [copybooks/Proc-ACAS-FH-Calls.cob:L1110] where Sales
#       spells it "Sorted-By-Name" [:L689].
#   N6  a THIRD asymmetry: acasirsub1-Start clears Access-Type
#       [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L202-L205] and so destroys the
#       START relation, where all twenty entity START verbs preserve it
#       [copybooks/Proc-ACAS-FH-Calls.cob:L456-L458]. Zero is not one of the
#       relations 5 through 9, so this verb cannot position.
#   N7  System-Open/-Open-Input/-Open-Output/-Close use literal "move n to
#       File-Function" rather than "set fn-... to true" - the only entity that
#       does. [copybooks/Proc-ACAS-FH-Calls.cob:L190-L215]
#   N8  the close performed inside a check overwrites FS-Reply and WE-Error, so
#       Open-Error-Continued reports the close's status and not the failure that
#       reached it. [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L323] then [:L357]
#   N9  58 entity verbs move 1 to File-Key-No and 19 of the 21 dispatch
#       paragraphs move 1 as well, so those verb-level stores are dead. The two
#       that matter are the two dispatch paragraphs that move nothing.
#   N10 the agent brief's own example cites "GL-Batch-Read-Next" at L465 with
#       "set fn-read-next" before "move zero to Access-Type". The source has
#       that paragraph at L460-L463 with the two statements the other way
#       round; L465 is GL-Batch-Read-Indexed. The plans follow the source,
#       because statement order is what the state diff is sensitive to.
#
# --- end traceability -------------------------------------------------------
