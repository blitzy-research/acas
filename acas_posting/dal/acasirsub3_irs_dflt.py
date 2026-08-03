"""IRS defaults data access - handler ``acasirsub3`` over bridge ``irsdfltMT``.

THE ONE FACT THAT SHAPES EVERY LINE BELOW
=========================================
This handler does not move rows, it moves a TABLE. One COBOL record is a
33-element ``OCCURS`` group [copybooks/irswsdflt.cob:L9], so a single logical
operation is **thirty-two SQL statements** wrapped in a synthesised connect and
disconnect - thirty-four bridge-level operations for a read, a write or a
rewrite, and **sixty-eight** for a write that fails. Every other handler in this
package is row-per-call; this one is not, and a module written by analogy with
``acas005`` or ``acas029`` would be structurally wrong before it was wrong in
any detail. The ``OCCURS`` is therefore the first thing declared here and the
thing every verb is organised around.

The array holds 33 entries. The bridge only ever handles 32. Both facts are
declared separately, as :data:`OCCURS` and :data:`BRIDGE_LIMIT`, so that the gap
cannot be closed by accident - see anomaly **A2**.

WHAT THIS MODULE OWNS
=====================
The Python reimplementation of two frozen COBOL programs, as one module,
because Agent Action Plan section 0.3.1 fixes the boundary at the handler:

    "One data-access module per handler, not per table. ... Mirroring the
    handler boundary rather than the table boundary keeps the Python module set
    in exact correspondence with the COBOL programs that the traceability
    document must map, and preserves the dispatch semantics rather than
    flattening them."

* ``common/acasirsub3.cbl`` (543 lines) - the handler. Linkage
  [common/acasirsub3.cbl:L151-L157]; flat-path dispatch [:L199-L218]; the
  commented-out flat open and close [:L220-L256]; the record-size gate
  [:L366-L415]; the RDB orchestration [:L426-L526].
* ``common/irsdfltMT.cbl`` (916 lines) - the generated bridge. Host-variable
  group [common/irsdfltMT.cbl:L323-L327]; key metadata [:L266-L275]; cursor
  state [:L282-L286]; ``PROCEDURE DIVISION USING`` [:L360-L362]; bridge open
  [:L407-L453]; bridge close [:L455-L468]; read [:L470-L615]; write
  [:L617-L671]; rewrite [:L673-L739]; bad function [:L741-L747]; free
  [:L753-L763]; ``bb200-Insert`` [:L774-L837]; ``bb300-Update`` [:L839-L906].
* Target: ``IRSDFLT-REC``, four columns, frozen [mysql/ACASDB.sql:L189-L195].
  The table carries a deliberate table-level comment,
  ``COMMENT='Defaults table for IRS'`` [mysql/ACASDB.sql:L195], which most
  in-scope tables do not - evidence it was authored rather than generated
  blindly. Nothing is preserved from it here; the schema is frozen and comments
  are schema metadata.
* Pre-translation source ``common/irsdfltMT.scb`` (764 lines) is cited wherever
  it settles whether something was authored or produced by the JC preSQL
  translator. That distinction matters twice below (A21 and the ``UPDATE``
  column list).

HOW TO READ A LOCATOR IN THIS FILE
==================================
Two forms appear, and the rule relating them is exact so that the record is
machine-checkable as rule R-5 requires:

* ``[<path>:L<n>]`` or ``[<path>:L<n>-L<m>]`` names the file outright.
* ``[:L<n>]`` continues **the file named by the nearest preceding locator of the
  first form**, reading the file top to bottom. Nothing else resolves it - not
  the enclosing function, not the section heading.

Every one of the 579 locators here was verified against that single rule: each
resolves to a real file and to a line inside it, and no locator token is ever
split across two lines, so a reader and a script arrive at the same answer.
Where an incidental citation of some other file would have hijacked the
continuation, the following locator is written out in full instead.

PROVENANCE, AND CORRECTIONS TO THE CITED SPANS
==============================================
Every locator in this file was read from this checkout rather than copied
forward, because rule R-5 makes a wrong locator a traceability defect. Three
classes of correction resulted, recorded here so a reader comparing this module
against second-hand notes is not misled:

1. **The handler's RDB orchestration is at L426-L526, not L505-L609.** The
   working notes this module was specified from carried a span shifted by
   roughly 79 lines. The verified spans are: ``fn-open`` intercept L429-L432;
   ``fn-close`` intercept L433-L438; read block L440-L467; write block
   L468-L492; the silent retry L484-L492; rewrite block L494-L513; the second
   bad-function site L517-L519; ``ba020-Call-DAL`` L521-L526.
2. **The bridge's read-loop spans shift by a few lines**: the EOF guard is
   L564-L573, the key-above-32 guard L575-L583, the count-rows probe
   L585-L602, and the squashing loop L663-L670.
3. **Two claimed anomalies do not survive reading the source**, and are
   documented as measured rather than as received. See "TWO CORRECTED
   ANOMALIES" below.

FIELD-TO-DICTIONARY MAPPING (RULE R-5)
======================================
Agent Action Plan section 0.8.1 makes the ordering a directive: "Data
dictionary first. ... every Python field definition cites its entry. This
ordering is a directive, not a preference - it is what prevents fields being
transcribed by eye." Every field here is therefore resolved through
:mod:`acas_posting.dictionary.loader` at import time, never transcribed.

The mapping is one-to-many in one direction and zero-to-one in the other:

===================  ==========================  ==================  =========
Dictionary key       Copybook field              Host variable       Column
===================  ==========================  ==================  =========
``...DEF-REC-KEY``   **NONE - bridge only**      ``9(03)`` COMP      tinyint(2)
``...DEF-ACS``       ``Def-Acs pic 9(5)``        ``9(05)`` COMP      decimal(5,0)
``...DEF-CODES``     ``Def-Codes pic xx``        ``X(2)``            char(2)
``...DEF-VAT``       ``Def-Vat pic x``           ``X(1)``            char(1)
===================  ==========================  ==================  =========

* Three copybook fields each map to one column but are **subscripted 1..33**
  [copybooks/irswsdflt.cob:L10-L12], which is what makes one record 32 rows.
* ``DEF-REC-KEY`` maps to **no copybook field whatsoever**. It is the
  ``OCCURS`` subscript materialised as a column, derived by the bridge at
  [common/irsdfltMT.cbl:L637-L639] on write and [:L689-L691] on rewrite. This
  is the **second** instance in this package of the bridge-only-column finding
  that Agent Action Plan section 0.1.1 raises; the plan names only the first
  (``POST4-DAY`` / ``POST4-MONTH`` / ``POST4-YEAR`` in ``irspostingMT``). It is
  also the single strongest local argument for the plan's rule, quoted in
  section 0.8.2: "The maintainer's one-way COBOL-to-MySQL bridge defines the
  authoritative record-layout <-> table mapping - it is the data dictionary for
  this migration." A migration driven from the copybook alone would omit this
  table's primary key.
* ``records/irs_dflt.py`` states the division of labour explicitly and defers
  to this module: "the ``acasirsub3`` handler module owns the subscript-to-key
  mapping in both directions". :func:`_load_host_variables` and
  :func:`_unload_row_into` are the two directions.
* This table has **no monetary column and no signed field at all**, so none of
  the signedness drift catalogued in Agent Action Plan section 0.6.2 applies
  here. The one drift present is a USAGE change: the copybook declares
  ``DISPLAY``, the host variable ``COMP``, the column ``DECIMAL``. It is read
  from ``loader.drift_for`` rather than asserted, and it is the reason
  ``DEF-ACS`` has **two** correct Python types rather than one, each on its own
  side of a boundary. Rule R-2 fixes the transport type from the column, so the
  value bound into a statement and read back out of one is a scale-zero
  :class:`~decimal.Decimal` - ``decimal(5,0) unsigned``
  [mysql/ACASDB.sql:L191] is a ``decimal`` column, not an integer type, despite
  holding an account number. The generated dictionary gives the *copybook field*
  the INT storage class, because ``pic 9(5)`` is unsigned with no ``V``, and
  ``records/irs_dflt.py`` declares ``def_acs`` an ``int`` accordingly. This
  module converts at the boundary in both directions rather than overruling
  either: :func:`_load_host_variables` widens the truncated integer to
  ``Decimal`` and :func:`_unload_row_into` narrows the fetched ``Decimal`` back.
  Both routes are exact, because every layer agrees on scale zero - so the
  stored row is identical either way and nothing passes through a binary float.

THE THIRTY-FOUR ANOMALIES
=========================
Rule R-4 is unconditional: "A defect reproduced is correct; a defect fixed is a
failure." Section 0.7.4 C-4 adds the mechanism - "a comment at each
reproduction site citing the COBOL locator". Anomalies **A1-A34** are each
reproduced below with such a comment. The four that dominate the module's
shape:

* **A1 - a failed write always reports success.** The handler clears the
  write's status and retries it as a rewrite [common/acasirsub3.cbl:L484-L492];
  the rewrite then unconditionally clears its error fields after its loop
  [common/irsdfltMT.cbl:L736-L738]. Neither layer alone would fully hide the
  error; together they do. This is the module's headline defect and it spans
  two files, which is why error handling here must be traced across the
  handler/bridge boundary before concluding what the caller sees.
* **A2 - 33 declared, 32 handled.** The copybook was widened from 32 to 33
  *specifically* for the in-scope IRS posting program - "to support temp.
  default 33 in postings (irs030)" [copybooks/irswsdflt.cob:L7] - and the
  record length comments corroborate it independently (256 bytes = 32 x 8 at
  [:L6], 264 = 33 x 8 at [:L7]). Yet both write loops stop at 32
  [common/irsdfltMT.cbl:L626] [:L678] and the read *rejects* a key above 32
  [:L575-L583]. Entry 33 can never reach the database and, if present, stops
  the read. ``irs030``'s 33rd default lives only in memory.
* **A3 - a fetched key above 32 moves the key VALUE into ``WE-Error``** and
  does not set ``FS-Reply`` [common/irsdfltMT.cbl:L575-L583], so a row 33
  reports ``WE-Error = 33`` - a row number masquerading as an error code.
* **A7 - the post-read status reset is commented out**
  [common/irsdfltMT.cbl:L613-L614], so a table holding fewer than 32 rows
  returns end-of-file ``(10, 10)`` even though every available row was loaded
  correctly.

TWO CORRECTED ANOMALIES - MEASURED, NOT RECEIVED
================================================
Rule R-6 makes compiled behaviour the arbiter and section 0.6.8 requires the
bridge's conversions be "measured rather than assumed". Applying that to the
anomaly list itself falsified two of its claims. Both corrections matter,
because acting on either claim as received would have *introduced* a defect
into a module whose entire purpose is to introduce none.

* **A20 as stated is wrong.** The claim was that this bridge's three-way
  duplicate test (``1062``, ``1022``, SQLSTATE ``23000``
  [common/irsdfltMT.cbl:L651-L653]) is richer than ``glpostingMT``'s
  single ``23000`` test. ``glpostingMT.cbl:L818-L820`` in fact carries the
  identical three-way rule, and a census of all twenty in-scope bridges shows
  **sixteen of twenty** test all three; only ``dfltMT``, ``finalMT``,
  ``sys4MT`` and ``slpostingMT`` omit the SQLSTATE test. So this bridge uses
  the MAJORITY form, not a divergent one. The surviving true statement - that
  duplicate-detection practice varies by bridge and must be resolved per
  bridge - is honoured by resolving it here from this bridge's own source. The
  shared helper :func:`~acas_posting.dal.status.is_duplicate_key_bridge_level`
  implements exactly this rule, so reusing it introduces no behavioural change;
  it is used, and the equivalence is asserted at the call site.
* **A21 has no behavioural effect at all.** The two error-number comparisons
  really are padded differently - three spaces at [common/irsdfltMT.cbl:L647]
  and four at [:L723] - and the divergence is *authored* rather than a
  translator artifact, appearing identically pre-translation at
  [common/irsdfltMT.scb:L612] and [:L688]. But ``Ws-Mysql-Error-Number`` is
  ``pic x(5)`` [copybooks/mysql-variables.cpy:L84], so COBOL space-pads both
  literals to the same five characters and the two tests are the same test.
  There are also FOUR such sites, not two: [common/irsdfltMT.cbl:L526],
  [:L589] and [:L647] use three spaces and only [:L723] uses four.
  Reproducing them as two different
  predicates would have created a difference the compiled program does not
  have. One predicate is used, and both source literals are recorded at it.

A third received claim - that the ``Testing-2`` display gate is unique to the
rewrite - is also false: it gates the read as well, at
[common/irsdfltMT.cbl:L516-L518] and pre-translation at
[common/irsdfltMT.scb:L491-L493]. Both are presentation and both are dropped.

HOW THIS HANDLER IS REACHED, AND WHY IT NEVER RECOVERS
======================================================
Through the IRS facade convention in
``copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob``, which names its paragraphs after
the HANDLER rather than the entity and adds a per-handler error check the
General/Sales/Purchase convention has no equivalent for. Agent Action Plan
section 0.6.5 states the consequence verbatim: "The Python facade must
therefore behave differently depending on which alias set the caller used,
which is a behavioral difference and not merely a naming one."

That difference belongs to ``dal/facade.py``, not here. What belongs here is
the corollary, stated by the handler itself at [common/acasirsub3.cbl:L528] -
"Any errors leave it to caller to recover from". :func:`dispatch` therefore
returns the status pair cleanly and performs **no** recovery, and this module
raises no ACAS handler exception: that is reserved for the facade's
``goback`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L364].

Three facts about that convention were verified here and are load-bearing:

* **It publishes only SIX verbs for this handler**
  [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L223-L253] - ``Open``,
  ``Open-Input``, ``Close``, ``Read-Next``, ``Write`` and ``ReWrite`` (with the
  copybook's own capital W). There is no ``Open-Output``, ``Open-Extend``,
  ``Start``, ``Read-Indexed``, ``Delete`` or ``Delete-All``. Combined with the
  bridge having no ``DELETE`` section at all (A24) and ``fn-Delete-All`` being
  dispatched by no handler in the package, that is three independent
  confirmations that those verbs are unreachable here. They are still
  implemented, and they route to bad function.
* **Only ``Open`` and ``Open-Input`` get the error check** [:L227] [:L233].
  ``Read-Next``, ``Write`` and ``ReWrite`` return the raw status pair with no
  check whatsoever, which is the mechanism behind "no recovery" above.
* **``Access-Type`` is set to ZERO for Read-Next, Write and ReWrite**
  [:L241] [:L246] [:L251]. Zero is not a legal access type - the vocabulary
  runs 1..9 [copybooks/wsfnctn.cob:L107-L116]. This is decisive corroboration
  of A16: the read's relation *cannot* be derived from ``Access-Type``, because
  the facade never supplies a valid one. Hard-coding ``" > "`` is not a
  shortcut the author took but the only thing that could have worked, and it is
  why this module builds its own ``SELECT`` instead of calling
  ``cursor_state.start``, which would reject an access type of zero.

The facade also allocates this handler a message, ``IR913``
[copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L343], entirely disjoint from the
handler's own ``IR917``/``IR918``/``IR919`` - two independent
``IR9xx`` allocations for one handler (A34). And its recovery path performs
``acasirsub3-Close`` [:L344] before bailing out, which per A10 is a no-op that
touches nothing: the facade's cleanup cleans up nothing for this handler.

CONVENTION DRIFT RECORDED FOR TRACEABILITY (A25, A28, A29, A33, A34)
====================================================================
Five of the thirty-four anomalies have no executable reproduction site: they are
facts about how the frozen source is *written*, not about what it *does*. Rule
R-4 still requires each to be recorded with its locator, and rule R-5 requires
the record to be a document rather than something left implicit, so they are
inventoried here and repeated in the traceability footer.

* **A25 - the FD record is a flat, unstructured byte blob.** ``01 Record-3 pic
  x(264)`` [common/acasirsub3.cbl:L113], with no copybook and no fields at all,
  where every other handler in the package declares a structured FD. All
  structure lives in the linkage record instead; 264 bytes matches 33 x 8
  exactly [copybooks/irswsdflt.cob:L7]. Nothing here structures it, because the
  flat path is omitted entire.
* **A28 - ``ba020-Call-DAL`` is the fourth DAL-call naming variant in the
  package** [common/acasirsub3.cbl:L521-L526]. The others are
  ``ba020-Process-DAL`` (``acas005``, ``acas006``, ``acas007``, ``acas012``,
  ``acasirsub1``), ``ba020-Call`` (``acas013``), and no paragraph at all - an
  inline ``call`` - in eight handlers. Only three of the handler's five linkage
  parameters cross to the bridge [common/acasirsub3.cbl:L522-L525], with the
  family's habitual blank line inside the argument list.
* **A29 - the handler and the bridge disagree on the record's name.** The
  handler copies the layout ``replacing Default-Record by
  WS-IRS-Default-Record`` [common/acasirsub3.cbl:L141] and passes it under that
  name [:L525]; the bridge copies the same copybook **without any ``replacing``
  clause** [common/irsdfltMT.cbl:L340], confirmed pre-translation at
  [common/irsdfltMT.scb:L330], and receives it as ``Default-Record``
  [common/irsdfltMT.cbl:L362]. One storage layout, two names across a ``CALL``
  boundary - the third such instance in the package, after ``plinvoiceMT`` and
  ``irsnominalMT``. Python has one object and one name, so the divergence
  survives only as this note.
* **A33 - the logging comments contradict themselves.**
  ``Ca-Process-Logs`` is annotated "Not called on DAL access as it does it
  already" [common/acasirsub3.cbl:L534] yet is performed explicitly FIVE times
  inside ``ba015`` [:L436] [:L454] [:L465] [:L487] [:L511], each marked "temp
  only during testing". Alongside it: a ``Testing-2`` gate
  [common/irsdfltMT.cbl:L715-L717] where every other hook in both files uses
  ``Testing-1``; "should test if select worked first??????" with six question
  marks [common/irsdfltMT.cbl:L536], marking that the cursor is flagged active
  without verifying the ``SELECT``; and "COULD LET caller module deal with these
  errors !!!!!!!" with seven exclamation marks [common/acasirsub3.cbl:L383],
  beside the record-size abort that does exactly the opposite.
* **A34 - the ``IR9xx`` space has gaps in at least three places.** This handler
  owns ``IR917``-``IR919`` only [common/acasirsub3.cbl:L135-L137]; ``IR901`` and
  ``IR902`` are duplicated verbatim from ``acasirsub1``
  [common/acasirsub3.cbl:L133-L134]; ``IR903``-``IR916`` are absent here, and
  ``IR903``-``IR905`` are absent from ``acasirsub1`` too; and ``IR914`` is
  missing from the IRS facade copybook's own header list
  [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L11]. With it: the doubly-commented
  line ``*>*> 27/07/16 16:30`` [common/acasirsub3.cbl:L251]; **both spellings of
  the translator's name three lines apart in this one file** - ``JCs`` at
  [common/acasirsub3.cbl:L420] and ``JC`` at [:L423], where
  ``acasirsub1.cbl:L748`` writes only ``JCs``; and ``function Length`` then
  ``function length`` on adjacent lines [common/acasirsub3.cbl:L377] [:L380], a
  copy-paste this handler shares with ``common/acas029.cbl``.

DELIBERATE OMISSIONS - RECORDED AS OMISSIONS (RULE R-5, SECTION 0.5.3)
=====================================================================
* **The whole flat-file record path.** ``Default-File`` is a line-sequential
  file [common/acasirsub3.cbl:L103-L106] over ``irsdflt.dat``
  (``File-Defs.file_defs_a.file_35``). This package's data-access layer is SQL
  against the frozen schema and the target tree has no flat-file module, so the
  flat ``READ``/``WRITE`` verbs themselves are not reimplemented. What IS
  reproduced is the flat *dispatch shape*, published as
  :data:`FLAT_PATH_DISPATCH`, because that is where anomaly A11 lives.
* **The commented-out flat open and close** [common/acasirsub3.cbl:L220-L256]
  - roughly 38 lines of fully formed dead code, and with them the error codes
  ``997`` [:L232] and ``1`` [:L226] and the trace numbers ``201`` [:L222] and
  ``202`` [:L248], all unreachable in this handler. Declared as dead constants
  so the omission is visible, never executed. Includes the doubly-commented
  line ``*>*> 27/07/16 16:30`` [:L251] - a comment that was itself commented
  out.
* **The flat read's create-if-missing fallback** [:L266-L273] - on a failed
  open it closes, opens output, initialises, writes and closes. Part of the
  flat record path, and omitted with it.
* **All presentation.** The ``display``/``accept`` pairs behind ``IR901``,
  ``IR902``, ``IR917``, ``IR918``, ``IR919`` [:L130-L137] and the bridge's
  ``SM901`` [common/irsdfltMT.cbl:L313]; the two ``Testing-2`` screen displays
  [:L516-L518] [:L715-L717]; ``accept ws-env-lines from lines`` [:L365], which
  reads the terminal height; and the screen section [:L342-L357]. Agent Action
  Plan section 0.3.4 gives the rule: a diagnostic display with no database
  effect becomes a log record, an accept that merely pauses for
  acknowledgement is dropped, and **the control transfer around it is
  preserved**. The record-size gate's abort is preserved exactly for that
  reason.
* **``Ca-Process-Logs``** [common/acasirsub3.cbl:L534-L538] and
  [common/irsdfltMT.cbl:L908-L912], both of which ``call "fhlogger"``.
  ``common/fhlogger.cbl`` is explicitly out of scope (section 0.2.2) and rule
  R-1 forbids calling any COBOL program, so the hook becomes a Python log
  record at the sites the frozen source reaches it and nothing at the sites it
  does not - which is itself observable behaviour, see A30.
* **``Def-Group``** [copybooks/irswsdflt.cob:L9], the ``OCCURS`` group name,
  and **``Record-3 pic x(264)``** [common/acasirsub3.cbl:L113], the flat FD
  record. Neither has a column or a host variable. The FD record being a flat,
  unstructured byte blob rather than a structured copybook is unique to this
  handler in the package (A25).
* **The lock-retry ladder** reached through ``COPY "mysql-procedures.cpy"``
  [common/irsdfltMT.cbl:L751]. Its only ``perform`` is commented out at
  [copybooks/mysql-procedures.cpy:L167], so ``WE-Error 910`` is unreachable
  and a lock surfaces as ``(99, 911)``. The ladder is reproduced as dead by
  not reaching it, exactly as the frozen source does not reach it.

WHAT IS DELIBERATELY *NOT* OPTIMISED
====================================
The thirty-two statements are issued one at a time, in the loop's order, and
are never batched into a multi-row ``INSERT``, a single ``UPDATE`` or an
``executemany``. Section 0.3.3 objects to an ORM on exactly this ground, that
it "would obscure the exact statement ordering that the state diff is
sensitive to", and section 0.8.4 settles the wider question: "Any performance
work is therefore out of scope by construction, not merely unrequested." No
transaction is opened either - the frozen source has none, and
``dal/connection.py`` owns the autocommit policy.

Identifiers are quoted through
:func:`~acas_posting.dal.connection.quote_identifier` without exception,
because every table and column name in this schema contains a hyphen and is a
syntax error unquoted. Values travel as bound ``%s`` parameters, which is the
package's transport rule and yields the identical logical statement and stored
value while removing an injection route the frozen source left open; the
COBOL's own double-quoted literal text is recorded alongside each statement so
the two can be compared.

DETERMINISM (RULE R-6)
======================
No clock, no randomness, no identifier generation. The single ``ORDER BY`` in
the frozen source is preserved verbatim (A17) and none is added anywhere else.
Two questions this module could not settle from the source alone are now RESOLVED
BY MEASUREMENT against MariaDB 10.11.7 - the server version the frozen schema
records as its producer [mysql/ACASDB.sql:L1] - rather than guessed; each is
recorded at its site and in ``docs/migration/ambiguity-resolutions.md``.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Final

# The pinned driver, imported ONLY for its exception type.
#
# A NOTED DEVIATION FROM THIS MODULE'S IMPORT WHITELIST, MADE VISIBLE RATHER
# THAN QUIET. The whitelist governs `acas_posting` layering (Agent Action Plan
# section 0.4.3) and lists the standard library alongside it; it did not
# anticipate that reproducing the bridge's `call "MySQL_errno"` /
# `"MySQL_sqlstate"` / `"MySQL_error"` probes [common/irsdfltMT.cbl:L644-L649]
# requires catching a driver error, and `dal/connection.py` does not re-export
# the type. `mysql-connector-python` 26.7.0 is the driver the Agent Action Plan
# names in section 0.5.1, `dal/connection.py` imports the same symbol for the
# same purpose, and the alternative - a bare `except Exception` - would swallow
# programming errors and fail the enterprise-quality bar this file is held to.
# Nothing else from the driver is used, and no connection is created here.
from mysql.connector import Error as DriverError

from acas_posting.dal import connection as _connection
from acas_posting.dal import cursor_state as _cursor_state
from acas_posting.dal import status as _status
from acas_posting.dictionary import loader as _loader
from acas_posting.records.file_access import FileAccess
from acas_posting.records.file_defs import FileDefs
from acas_posting.records.irs_dflt import WsIrsDefaultRecord
from acas_posting.records.system_record import SystemRecord
from acas_posting.records.test_data_flags import AcasDalCommonData

__all__: Final[tuple[str, ...]] = (
    # Identity and shape
    "TABLE",
    "PRIMARY_KEY",
    "COLUMNS",
    "OCCURS",
    "BRIDGE_LIMIT",
    "HANDLER",
    "BRIDGE",
    "ENTITY_FACADE",
    "DICTIONARY_KEYS",
    "FACADE_VERBS",
    "FLAT_PATH_DISPATCH",
    "RDB_PATH_DISPATCH",
    # The read's frozen predicate
    "READ_RELATION",
    "READ_KEY_LITERAL",
    "ORDER_BY_CLAUSE",
    "KEY_OFFSET",
    "KEY_LENGTH",
    "KEY_METADATA_TYPE",
    # Status codes this module can produce
    "HANDLER_BAD_FUNCTION",
    "BRIDGE_BAD_FUNCTION",
    "RECORD_SIZE_MISMATCH_WE_ERROR",
    "REWRITE_UNOBSERVABLE_WE_ERROR",
    # Logging identity and trace numbers
    "WS_LOG_SYSTEM",
    "WS_LOG_FILE_NO_FLAT",
    "WS_LOG_FILE_NO_RDB",
    # The verbs
    "close",
    "delete",
    "delete_all",
    "dispatch",
    "open_",
    "open_extend",
    "open_input",
    "open_output",
    "read_indexed",
    "read_next",
    "reset_record_size_gate",
    "rewrite",
    "start",
    "write",
)

_LOG = logging.getLogger(__name__)

#: The status pair every verb returns and writes back into ``File-Access``.
#: COBOL returns through the linkage record; these functions do both, so a
#: caller may read the pair directly or inspect ``file_access`` as the frozen
#: callers do.
StatusPair = tuple[int, int]


# ---------------------------------------------------------------------------
#  IDENTITY AND SHAPE
# ---------------------------------------------------------------------------

#: The frozen table this handler owns [mysql/ACASDB.sql:L189].
TABLE: Final[str] = "IRSDFLT-REC"

#: The COBOL handler program reimplemented here [common/acasirsub3.cbl:L118].
HANDLER: Final[str] = "acasirsub3"

#: The generated bridge program reimplemented here [common/irsdfltMT.scb:L247].
BRIDGE: Final[str] = "irsdfltMT"

#: The entity facade name from the Agent Action Plan's entity-to-table spine.
ENTITY_FACADE: Final[str] = "IRS defaults"

#: Sole primary key, single column, zero secondary indexes
#: [mysql/ACASDB.sql:L194]. Also ``KeyName (1)`` in the bridge's key metadata
#: [common/irsdfltMT.cbl:L267].
PRIMARY_KEY: Final[str] = "DEF-REC-KEY"

#: The four columns in schema ordinal order [mysql/ACASDB.sql:L190-L193],
#: which is also host-variable declaration order
#: [common/irsdfltMT.cbl:L324-L327]. The two orders agreeing is what makes the
#: bridge's positional ``MySQL_fetch_record`` [:L552-L560] and this module's
#: fetch-by-column-name equivalent under ``SELECT *``.
COLUMNS: Final[tuple[str, ...]] = (
    "DEF-REC-KEY",
    "DEF-ACS",
    "DEF-CODES",
    "DEF-VAT",
)

# A2. THE TWO BOUNDS ARE SEPARATE CONSTANTS, ON PURPOSE.
#
# They disagree, and the disagreement is the defect. Declaring one constant and
# reusing it - or "tidying" the loops to OCCURS - would silently fix a defect
# rule R-4 requires be preserved. Nothing in this module iterates to OCCURS.

#: Declared array length: 33 [copybooks/irswsdflt.cob:L9]. Widened from 32
#: "to support temp. default 33 in postings (irs030)" [:L7], corroborated
#: independently by the record-length comments - 256 bytes = 32 x 8 [:L6] and
#: 264 bytes = 33 x 8 [:L7].
OCCURS: Final[int] = 33

#: What the bridge actually handles: 32. Both write loops are bounded
#: ``until A > 32`` [common/irsdfltMT.cbl:L626] [:L678], the read loop likewise
#: [:L544-L545], and the read *rejects* a fetched key above 32 [:L575-L583].
#: Entry 33 can therefore never reach the database.
BRIDGE_LIMIT: Final[int] = 32

#: Record length in bytes, both sides of the record-size gate: the linkage
#: record is 33 x 8 [copybooks/irswsdflt.cob:L9-L12] and the flat FD record is
#: declared ``pic x(264)`` [common/acasirsub3.cbl:L113]. Equal, so the gate
#: passes; it is still evaluated, because a mismatch aborts before the bridge.
RECORD_LENGTH_BYTES: Final[int] = 264

#: The dictionary key for each column, in schema order. Rule R-5: every field
#: is resolved through the dictionary rather than transcribed.
DICTIONARY_KEYS: Final[tuple[str, ...]] = tuple(
    f"{TABLE}.{column}" for column in COLUMNS
)

# ---------------------------------------------------------------------------
#  THE READ'S FROZEN PREDICATE
# ---------------------------------------------------------------------------

# A16. The relation is HARD-CODED and the key value is a QUOTED STRING LITERAL.
# Neither is derived from `Access-Type`, and `MOST-Relation` - declared at
# [common/irsdfltMT.cbl:L283] - is never read by this bridge's read path.
# Corroborated decisively by the facade, which sets `Access-Type` to zero for
# Read-Next [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L241]; zero is not a legal
# access type [copybooks/wsfnctn.cob:L107-L116], so no relation could have been
# derived from it. This is also why `cursor_state.start` is not used here: it
# validates the access type and would reject zero.

#: The read's relation token, hard-coded ``" > "`` [common/irsdfltMT.cbl:L486].
#: Cross-checked against the package's own registration for this table,
#: :data:`~acas_posting.dal.cursor_state.SEQUENTIAL_READ_START`, at import.
READ_RELATION: Final[str] = ">"

#: The read's low-key literal, ``'"000"'`` - three characters, quoted, compared
#: against a one-byte ``tinyint`` column [common/irsdfltMT.cbl:L487]. The
#: trailing comment there, ``*> changed from '000'``, records that only the
#: quoting style was altered.
READ_KEY_LITERAL: Final[str] = "000"

# A15. DEAD KEY METADATA - COMPUTED BY THE BRIDGE AND NEVER USED.
#
# The metadata declares offset 1, length 1 [common/irsdfltMT.cbl:L268] for a
# key that IS NOT IN THE RECORD. The record's first byte is the first digit of
# `Def-Acs (1)` [copybooks/irswsdflt.cob:L10], so the canonical
# `<record-buffer>(K:L)` substring would yield one character of the first
# account number. The maintainer discovered this and worked around it rather
# than fixing it: the canonical construction sits commented out at
# [common/irsdfltMT.cbl:L705], the host variable at [:L706], and the loop
# subscript is used instead at [:L707]. `K` and `L` are still computed at
# [:L478-L479] and [:L695-L697] and then never read. Preserved commented-out
# code is evidence, not noise - it records which approach was tried and
# rejected, which is what the ambiguity-resolutions document exists to capture.

#: ``KOR-Offset (1)``, computed and unused [common/irsdfltMT.cbl:L268].
KEY_OFFSET: Final[int] = 1

#: ``KOR-Length (1)``, computed and unused [common/irsdfltMT.cbl:L268].
KEY_LENGTH: Final[int] = 1

#: ``KOR-Type (1)``, annotated "Not used currently" in the source itself
#: [common/irsdfltMT.cbl:L275].
KEY_METADATA_TYPE: Final[str] = "STR"

# A17. THE ONLY EXPLICIT `ORDER BY` IN ANY IN-SCOPE BRIDGE.
# Built through the package's own `OrderTerm` so the quoting is the shared
# implementation rather than a local f-string, and asserted below against the
# echo the bridge itself leaves at [common/irsdfltMT.cbl:L499].
_ORDER_TERM: Final[_cursor_state.OrderTerm] = _cursor_state.OrderTerm(
    column_name=PRIMARY_KEY,
    direction="ASC",
    quoting=_cursor_state.OrderQuoting.IDENTIFIER,
    source_locator="[common/irsdfltMT.cbl:L488-L492]",
)

#: ``ORDER BY `DEF-REC-KEY` ASC`` [common/irsdfltMT.cbl:L488-L492]. Preserved
#: verbatim: it is in the frozen source, so it is not an optimisation that may
#: be dropped - and, being unique to this bridge, not one that may be added
#: anywhere else. It is on the primary key, so Agent Action Plan section 0.6.6
#: still holds that there is "no ordering nondeterminism from a secondary
#: index".
ORDER_BY_CLAUSE: Final[str] = f"ORDER BY {_ORDER_TERM.to_sql()}"

# ---------------------------------------------------------------------------
#  STATUS CODES THIS MODULE CAN PRODUCE
# ---------------------------------------------------------------------------

# A26. THE HANDLER AND THE BRIDGE DISAGREE ON THE BAD-FUNCTION CODE, AND THE
# DISAGREEMENT IS NOT RECONCILED. `aa100-Bad-Function` moves 999
# [common/acasirsub3.cbl:L340-L345]; `ba100-Bad-Function` moves 990
# [common/irsdfltMT.cbl:L741-L747]. The same handler/bridge split holds for
# `acas029`/`otm5MT`, so it is a package-wide pattern rather than a one-off.
# The handler is the module boundary, so 999 is what a caller of `dispatch`
# sees; 990 is declared because the bridge-level paragraph is reproduced too.

#: ``aa100-Bad-Function`` and the second, RDB-section bad-function site
#: [common/acasirsub3.cbl:L344] [:L517]. What :func:`dispatch` returns.
HANDLER_BAD_FUNCTION: Final[int] = int(_status.WeError.NOT_USED)

#: ``ba100-Bad-Function`` [common/irsdfltMT.cbl:L743]. Never surfaced to a
#: caller, because the handler filters the function code first.
BRIDGE_BAD_FUNCTION: Final[int] = int(_status.WeError.UNKNOWN_UNEXPECTED)

#: The record-size gate's abort code [common/acasirsub3.cbl:L384].
RECORD_SIZE_MISMATCH_WE_ERROR: Final[int] = int(
    _status.WeError.RECORD_SIZE_MISMATCH
)

# A18. `WE-Error 994` IS PERMANENTLY UNOBSERVABLE. Set inside the rewrite's
# error branch [common/irsdfltMT.cbl:L728], then cleared unconditionally after
# the loop [:L736]. It is set here anyway, and then cleared, because the
# clearing is the defect and a value that is never set cannot be cleared.
REWRITE_UNOBSERVABLE_WE_ERROR: Final[int] = int(
    _status.WeError.REWRITE_SQLSTATE_NOT_00000
)

# A10 / DELIBERATE OMISSION. Codes reachable only from the commented-out flat
# open, declared so the omission is visible and never executed:
# `move 997 to WE-Error` for an `open i-o`/`extend` attempt
# [common/acasirsub3.cbl:L233] and `move 1 to we-error` for a failed open
# [:L226].
_DEAD_FLAT_ACCESS_TYPE_WRONG: Final[int] = int(_status.WeError.ACCESS_TYPE_WRONG)
_DEAD_FLAT_OPEN_FAILED: Final[int] = 1

# A20 - CORRECTED. The duplicate test consults BOTH the error number and the
# SQLSTATE [common/irsdfltMT.cbl:L651-L653]. Contrary to the received note this
# is the MAJORITY form across the twenty in-scope bridges (sixteen of twenty),
# and `glpostingMT.cbl:L818-L820` carries the identical rule rather than a
# SQLSTATE-only one. The four that differ are `dfltMT`, `finalMT`, `sys4MT` and
# `slpostingMT`, which omit the SQLSTATE test. The shared helper therefore
# matches this bridge exactly and is used; these constants exist to document
# the rule at its own locator and to let the equivalence be asserted.
_DUPLICATE_KEY_ERRNOS: Final[tuple[str, ...]] = ("1062", "1022")
_DUPLICATE_KEY_SQLSTATE: Final[str] = "23000"

#: The width the bridge compares an error number at, ``SQL-Err (1:4)``
#: [common/irsdfltMT.cbl:L651].
_SQL_ERR_COMPARE_WIDTH: Final[int] = 4

# ---------------------------------------------------------------------------
#  LOGGING IDENTITY AND PARAGRAPH TRACE NUMBERS
# ---------------------------------------------------------------------------

#: ``move 1 to WS-Log-System`` [common/acasirsub3.cbl:L166] - 1 is IRS. The
#: legend on that line reads "1 = IRS, 2=GL, 3=SL, 4=PL, 5=Stock", which
#: CONTRADICTS the "5 = Invoice" legend carried by ``acas016``, ``acas019``,
#: ``acas026`` and ``acas029``: two mutually inconsistent legends coexist in
#: the codebase. Only the value matters, and the value is 1.
WS_LOG_SYSTEM: Final[int] = int(_status.LogSystem.IRS)

#: ``move 12 to WS-Log-File-No`` [common/acasirsub3.cbl:L167], the value on the
#: flat path.
WS_LOG_FILE_NO_FLAT: Final[int] = 12

#: ``move 22 to WS-Log-File-no`` [common/acasirsub3.cbl:L372], the effective
#: value on the RDB path. The 12-to-22 bump lives in ``ba010-Test-WS-Rec-Size``
#: [:L366-L372], which contains ONLY the bump and is reached by fall-through,
#: so it happens on the RDB path alone - the flat path performs ``ba012``
#: directly [:L188]. The pair ``(1, 22)`` is what disambiguates this handler:
#: file number 22 collides three ways across the package, with ``acas015``
#: (system 6) and ``acas016`` (system 3).
WS_LOG_FILE_NO_RDB: Final[int] = 22

#: ``ws-No-Paragraph`` values, the bridge's own paragraph trace numbers. Live:
#: open 1 [common/irsdfltMT.cbl:L440], close 2 [:L459], read-select 3 [:L498],
#: read-fetch 4 [:L542], write 10 [:L624], rewrite 17 [:L677], free 20
#: [common/irsdfltMT.cbl:L755]. The handler adds flat-path values 203
#: [common/acasirsub3.cbl:L263] and 206 [:L316], and the dead flat open/close
#: carry 201 [:L222] and 202 [:L248], unreachable in this handler (A10).
_PARA_BRIDGE_OPEN: Final[int] = 1
_PARA_BRIDGE_CLOSE: Final[int] = 2
_PARA_READ_SELECT: Final[int] = 3
_PARA_READ_FETCH: Final[int] = 4
_PARA_WRITE: Final[int] = 10
_PARA_REWRITE: Final[int] = 17
_PARA_FREE: Final[int] = 20
_DEAD_PARA_FLAT_OPEN: Final[int] = 201
_DEAD_PARA_FLAT_CLOSE: Final[int] = 202
_PARA_FLAT_READ: Final[int] = 203
_PARA_FLAT_WRITE: Final[int] = 206

# ---------------------------------------------------------------------------
#  DIAGNOSTIC KEY STRINGS  -  `WS-File-Key`, VERBATIM
# ---------------------------------------------------------------------------
# Four distinct end-of-data markers, not three: the received note listed "EOF",
# "EOF2" and "EOF3", but the empty-table probe inside the cursor-activation
# block contributes "No Data" as well [common/irsdfltMT.cbl:L533].
_KEY_EOF: Final[str] = "EOF"
_KEY_EOF2: Final[str] = "EOF2"
_KEY_EOF3: Final[str] = "EOF3"
_KEY_NO_DATA: Final[str] = "No Data"
_KEY_SELECT_ISSUED: Final[str] = "> 0"
_KEY_OPEN: Final[str] = "OPEN IRS DEFAULT"
_KEY_CLOSE: Final[str] = "CLOSE IRS DEFAULT"
_KEY_OPEN_READ_CLOSE: Final[str] = "Open, Read, Close"
_KEY_OPEN_WRITE_FAILED_CLOSE: Final[str] = "Open, Write failed, Close"
_KEY_OPEN_REWRITE_CLOSE: Final[str] = "Open, Rewrite, Close"

# ---------------------------------------------------------------------------
#  THE TWO DISPATCH TABLES  -  A11, PUBLISHED AS DATA
# ---------------------------------------------------------------------------
# A11. VERB IDENTITY IS PATH-DEPENDENT, WHICH NO SHARED MAPPING COULD EXPRESS.
#
# On the FLAT path `when 5` falls through to `when 7`, both reaching
# `aa070-Process-Write` [common/acasirsub3.cbl:L210-L212], justified in the
# source as "write/rewrite can do the same ... as file is opened as output."
# So on that path REWRITE *IS* WRITE.
#
# On the RDB path they are DISTINCT: the handler runs separate `fn-Write`
# [:L468] and `fn-Re-write` [:L494] blocks, and the bridge's own dispatch sends
# 5 to `ba070-Process-Write` and 7 to `ba090-Process-Rewrite`
# [common/irsdfltMT.cbl:L397-L401].
#
# Both tables are published so the divergence is inspectable rather than buried
# in a branch, and so a traceability reader can see that this handler dispatches
# only FIVE codes - 1, 2, 3, 5, 7 [common/acasirsub3.cbl:L199-L215]. It is one
# of only two five-code handlers in the package (the other is `acasirsub5`).
# `fn-Delete-All` (6) is dispatched by NO handler at all and is not in either
# table.

#: The flat-path ``evaluate`` [common/acasirsub3.cbl:L199-L215], as frozen
#: data. ``FileFunction.WRITE`` and ``FileFunction.RE_WRITE`` both name
#: ``"write"`` - that identity is anomaly A11.
FLAT_PATH_DISPATCH: Final[Mapping[int, str]] = {
    int(_status.FileFunction.OPEN): "open",
    int(_status.FileFunction.CLOSE): "close",
    int(_status.FileFunction.READ_NEXT): "read_next",
    int(_status.FileFunction.WRITE): "write",
    int(_status.FileFunction.RE_WRITE): "write",
}

#: The RDB-path orchestration [common/acasirsub3.cbl:L429-L513], as frozen
#: data. Here ``RE_WRITE`` maps to its own verb.
RDB_PATH_DISPATCH: Final[Mapping[int, str]] = {
    int(_status.FileFunction.OPEN): "open",
    int(_status.FileFunction.CLOSE): "close",
    int(_status.FileFunction.READ_NEXT): "read_next",
    int(_status.FileFunction.WRITE): "write",
    int(_status.FileFunction.RE_WRITE): "rewrite",
}

#: The six verbs the IRS facade convention publishes for this handler
#: [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L223-L253], with the function and
#: access codes each sets and whether it is followed by
#: ``irsub3-Check-4-Errors``. Note the copybook's own capital W in ``ReWrite``,
#: and that ``Access-Type`` is ZERO - an illegal value - for the last four.
FACADE_VERBS: Final[Mapping[str, tuple[int, int, bool]]] = {
    "acasirsub3-Open": (
        int(_status.FileFunction.OPEN),
        int(_status.AccessType.I_O),
        True,
    ),
    "acasirsub3-Open-Input": (
        int(_status.FileFunction.OPEN),
        int(_status.AccessType.INPUT),
        True,
    ),
    "acasirsub3-Close": (int(_status.FileFunction.CLOSE), 0, False),
    "acasirsub3-Read-Next": (int(_status.FileFunction.READ_NEXT), 0, False),
    "acasirsub3-Write": (int(_status.FileFunction.WRITE), 0, False),
    "acasirsub3-ReWrite": (int(_status.FileFunction.RE_WRITE), 0, False),
}

# ---------------------------------------------------------------------------
#  PRE-QUOTED SQL FRAGMENTS
# ---------------------------------------------------------------------------
# Every identifier passes through `quote_identifier` because every table and
# column name in this schema is hyphenated and a syntax error unquoted. The
# bridge backtick-quotes for the same reason at [common/irsdfltMT.cbl:L483-L485]
# and [:L701-L703].
_QUOTED_TABLE: Final[str] = _connection.quote_identifier(TABLE)
_QUOTED_KEY: Final[str] = _connection.quote_identifier(PRIMARY_KEY)
_QUOTED_COLUMNS: Final[tuple[str, ...]] = tuple(
    _connection.quote_identifier(column) for column in COLUMNS
)

#: ``SELECT * FROM `IRSDFLT-REC` WHERE `DEF-REC-KEY` > %s ORDER BY
#: `DEF-REC-KEY` ASC``.
#:
#: The frozen statement is assembled in two halves: the ``WHERE`` text is built
#: into ``ws-Where`` with a pointer [common/irsdfltMT.cbl:L481-L495] and then
#: interpolated into ``SELECT * FROM `IRSDFLT-REC` WHERE ...;``
#: [:L505-L510]. The bridge leaves its own echo of the result one line below
#: the build - ``*> DEF-REC-KEY > "000" ORDER BY DEF-REC-KEY ASC`` [:L499] -
#: which is asserted against below.
#:
#: ``SELECT *`` is preserved rather than being narrowed to the four named
#: columns: the frozen source selects all columns and the bridge fetches
#: positionally into its host-variable group [:L552-L560], so a column list
#: would be a change, however invisible.
_SELECT_STATEMENT: Final[str] = (
    f"SELECT * FROM {_QUOTED_TABLE} "
    f"WHERE {_QUOTED_KEY} {READ_RELATION} %s {ORDER_BY_CLAUSE}"
)

#: The frozen predicate text, for comparison against the bridge's echo at
#: [common/irsdfltMT.cbl:L499]. Retained as documentation of what the compiled
#: program emits; this module binds the value instead of interpolating it.
_FROZEN_SELECT_ECHO: Final[str] = (
    f'{PRIMARY_KEY} {READ_RELATION} "{READ_KEY_LITERAL}" '
    f"ORDER BY {PRIMARY_KEY} ASC"
)

# A24. NO `bb000-HV-Load`, NO `bb100-UnloadHVs`, AND NO `DELETE` ANYWHERE.
#
# This bridge has only TWO `bb` sections - `bb200-Insert`
# [common/irsdfltMT.cbl:L774] and `bb300-Update` [:L839] - and handles its host
# variables inline in the read and write loops instead of in the dedicated
# load/unload paragraphs every other bridge uses. There is no delete statement
# of any kind, which is the second of three independent reasons the delete verbs
# below are unreachable.

#: ``INSERT INTO `IRSDFLT-REC` SET ...`` [common/irsdfltMT.cbl:L784-L831].
#:
#: The ``SET`` form rather than ``VALUES`` is what the JC preSQL translator
#: emitted: the directive names only the table [common/irsdfltMT.scb:L736-L738]
#: and the translator supplied the column list from the host-variable group. All
#: four columns are named and bound on every statement, never omitted and never
#: ``None`` - Agent Action Plan section 0.6.2 requires it: "This is why every
#: column in the schema can be declared ``NOT NULL`` and why the Python layer
#: must default rather than omit."
_INSERT_STATEMENT: Final[str] = "INSERT INTO {table} SET {assignments}".format(
    table=_QUOTED_TABLE,
    assignments=", ".join(f"{column} = %s" for column in _QUOTED_COLUMNS),
)

#: ``UPDATE `IRSDFLT-REC` SET ... WHERE `DEF-REC-KEY` = %s``
#: [common/irsdfltMT.cbl:L849-L899].
#:
#: THE PRIMARY KEY APPEARS IN BOTH THE `SET` LIST AND THE `WHERE`, and the
#: ``.scb`` settles whose choice that was: the directive carries only
#: ``TABLE=`` and ``WHERE=`` [common/irsdfltMT.scb:L747-L750], so the
#: translator generated all four assignments including the key. It is an
#: artifact of the translator rather than something the maintainer wrote - and
#: it is preserved, because what the compiled program emits is the
#: specification.
_UPDATE_STATEMENT: Final[str] = (
    "UPDATE {table} SET {assignments} WHERE {key} = %s".format(
        table=_QUOTED_TABLE,
        assignments=", ".join(f"{column} = %s" for column in _QUOTED_COLUMNS),
        key=_QUOTED_KEY,
    )
)



# ---------------------------------------------------------------------------
#  FIELD METADATA, RESOLVED FROM THE DICTIONARY  -  RULE R-5
# ---------------------------------------------------------------------------
# "Data dictionary first. ... every Python field definition cites its entry.
# This ordering is a directive, not a preference - it is what prevents fields
# being transcribed by eye." (Agent Action Plan section 0.8.1.)
#
# `records/irs_dflt.py` resolves the same fields through `cobol.field`, which
# `dal/*` may not import (section 0.4.3), so the resolution is repeated here
# against the dictionary directly rather than borrowed across a layer boundary.
# Nothing about a field is written as a literal below: widths, storage classes
# and the bridge-only status of the key all come from the generated artifact.


def _character_width(dictionary_key: str) -> int:
    """Return the host variable's character width for a text column.

    The host variable, not the column, is the width that matters: a value read
    back from a ``CHAR`` column arrives with its trailing spaces already
    stripped by the server, and the frozen program's first act is to land it in
    a fixed-width ``PIC X(n)`` host variable [common/irsdfltMT.cbl:L326-L327],
    which re-pads it. That padding is what the copybook field then receives.

    Args:
        dictionary_key: A key from :data:`DICTIONARY_KEYS`.

    Returns:
        The declared character length of the host variable.

    Raises:
        ValueError: If the dictionary has no host variable for the key, or
            declares no character length for it. Either would mean the
            generated artifact and this module have drifted apart, which rule
            R-5 makes a defect rather than something to work around.
    """
    host_variable = _loader.host_variable_for(dictionary_key)
    if host_variable is None or not host_variable.character_length:
        raise ValueError(
            f"{dictionary_key}: the data dictionary declares no host-variable "
            f"character length, so {TABLE} cannot be loaded field-by-field "
            f"as {BRIDGE} does - see {_loader.cite(dictionary_key)}"
        )
    return host_variable.character_length


def _numeric_digits(dictionary_key: str) -> int:
    """Return the host variable's digit count for a numeric column.

    Used for the receiving-field truncation a COBOL ``MOVE`` performs when it
    stores into a shorter numeric picture.

    Args:
        dictionary_key: A key from :data:`DICTIONARY_KEYS`.

    Returns:
        The declared digit count of the host variable.

    Raises:
        ValueError: If the dictionary declares no host variable or no digit
            count for the key.
    """
    host_variable = _loader.host_variable_for(dictionary_key)
    if host_variable is None or not host_variable.digits:
        raise ValueError(
            f"{dictionary_key}: the data dictionary declares no host-variable "
            f"digit count - see {_loader.cite(dictionary_key)}"
        )
    return host_variable.digits


# A4. THE PRIMARY KEY HAS NO COPYBOOK FIELD, AND THE DICTIONARY SAYS SO.
#
# Asserted from the artifact rather than asserted in prose: `presence` reports
# the column absent from every copybook and present in the bridge and the
# schema, and `derivation_for` names the move that invents it,
# `move WS-Key to HV-DEF-REC-KEY` [common/irsdfltMT.cbl:L639]. This is the
# second bridge-only-column instance in the package; section 0.1.1 names only
# the first, in `irspostingMT`.
_KEY_ENTRY: Final = _loader.get_entry(f"{TABLE}.{PRIMARY_KEY}")
_KEY_DERIVATION: Final = _loader.derivation_for(f"{TABLE}.{PRIMARY_KEY}")

if _loader.copybook_field_for(f"{TABLE}.{PRIMARY_KEY}") is not None:
    raise ValueError(
        f"{TABLE}.{PRIMARY_KEY} is declared by a copybook in the generated "
        "data dictionary, contradicting [copybooks/irswsdflt.cob:L8-L12] and "
        "the bridge-only derivation this module reproduces "
        "[common/irsdfltMT.cbl:L637-L639]"
    )

# A2, read side. The dictionary's own record of where the key is unloaded from
# is the guard, not the fetch - `unload_source` points at
# [common/irsdfltMT.cbl:L577], the line that moves the key value into
# `WE-Error`. The artifact therefore corroborates that the key's only read-path
# use is the rejection test.
_KEY_HOST_VARIABLE: Final = _loader.host_variable_for(f"{TABLE}.{PRIMARY_KEY}")

#: ``HV-DEF-ACS`` digit count, from the dictionary
#: [common/irsdfltMT.cbl:L325].
_DEF_ACS_DIGITS: Final[int] = _numeric_digits(f"{TABLE}.DEF-ACS")

#: ``HV-DEF-CODES`` and ``HV-DEF-VAT`` widths, from the dictionary
#: [common/irsdfltMT.cbl:L326-L327].
_DEF_CODES_WIDTH: Final[int] = _character_width(f"{TABLE}.DEF-CODES")
_DEF_VAT_WIDTH: Final[int] = _character_width(f"{TABLE}.DEF-VAT")

#: The modulus the ``MOVE`` into ``HV-DEF-ACS`` truncates by. A COBOL ``MOVE``
#: into a shorter numeric picture discards high-order digits; the copybook and
#: host variable are both five digits [copybooks/irswsdflt.cob:L10]
#: [common/irsdfltMT.cbl:L325], so this never fires for a value the copybook
#: could hold - but the record is mutable working storage that ``irs030``
#: amends, so the receiving-field rule is applied rather than assumed away.
_DEF_ACS_MODULUS: Final[int] = 10**_DEF_ACS_DIGITS

# The USAGE drift, read from the artifact rather than restated. The copybook
# declares DISPLAY, the host variable COMP, the column DECIMAL - the one drift
# this table has. There is no signedness drift and no monetary column here, so
# none of section 0.6.2's sign-loss findings apply; that is confirmed per field
# rather than extrapolated from a sibling handler.
_DEF_ACS_DRIFT: Final = _loader.drift_for(f"{TABLE}.DEF-ACS")

# AMBIGUITY Q-IRSDFLT-NUMERIC - RESOLVED BY MEASUREMENT against MariaDB 10.11.7,
# the server version the frozen schema records as its producer
# [mysql/ACASDB.sql:L1, :L5], with the frozen `ENGINE=InnoDB` and the server's
# DEFAULT `sql_mode`, which carries `STRICT_TRANS_TABLES`. That default is what the
# bridge's C interface gets: the dump's own `SQL_MODE='NO_AUTO_VALUE_ON_ZERO'`
# [mysql/ACASDB.sql:L21] is SESSION-scoped, leaves `@@global.sql_mode` untouched
# (measured) and is restored at [:L1451], so it governs only the schema load - and
# is inert even there, the schema's only `AUTO_INCREMENT` column belonging to the
# out-of-scope `STOCKAUDIT-REC` [mysql/ACASDB.sql:L1107]. Agent
# Action Plan section 0.6.8 requires the bridge's numeric conversions "be measured
# rather than assumed"; both were, and NEITHER RESULT CHANGES A LINE OF CODE below,
# which is the point of measuring rather than guessing.
#
#   * `Def-Acs pic 9(5)` DISPLAY [copybooks/irswsdflt.cob:L10] -> `HV-DEF-ACS
#     PIC 9(05) COMP` [common/irsdfltMT.cbl:L325] -> rendered through
#     `WS-MYSQL-EDIT PIC -Z(18)9.9(9)` [:L257] sliced at `(16:05)` and trimmed ->
#     `decimal(5,0) unsigned` [mysql/ACASDB.sql:L191].
#     MEASURED: the zero-suppressed text round-trips EXACTLY. `'00001'` stored 1
#     and `'99999'` stored 99999, so the edited-picture slice boundary holds and
#     the plain decimal digits an `int` bind produces are the same value. Out of
#     range the server REFUSES rather than clamps: `100000` and `-1` each raise
#     ERROR 1264, SQLSTATE 22003, "Out of range value", and the row is NOT
#     written; the empty string raises ERROR 1366, SQLSTATE 22007, "Incorrect
#     decimal value". So a negative or oversized `Def-Acs` fails at the server,
#     exactly where the frozen bridge meets it, and no Python check is added
#     (rule R-3) - one would move the refusal to a layer the source has nothing at
#     and would hide the error the frozen bridge receives.
#   * `HV-DEF-REC-KEY PIC 9(03) COMP` [common/irsdfltMT.cbl:L324] -> `tinyint(2)
#     unsigned` [mysql/ACASDB.sql:L190].
#     MEASURED, AND THE PREMISE WAS WRONG: `(2)` IS A DISPLAY WIDTH, NOT A
#     CONSTRAINT. `tinyint unsigned` holds 0..255, so it accepted 255, and the
#     three-digit host variable is NOT wider than the column over 0..255 - it is
#     wider only over 256..999, where the server raises ERROR 1264 / 22003 and
#     writes nothing. The write path still cannot reach even that: `A` runs 1..32
#     and is itself `pic 99` [common/irsdfltMT.cbl:L310]. What a fetched
#     out-of-range value does to the read's guard was already settled by A3.
# Both are left exactly as the frozen source expresses them and nothing is
# normalised - now on evidence rather than pending it.


def _truncate_trailing(value: str) -> str:
    """Apply ``FUNCTION TRIM(<hv>, TRAILING)`` to a character host variable.

    The bridge trims trailing spaces off both character host variables as it
    builds the statement text - ``INSERT`` at [common/irsdfltMT.cbl:L810-L825]
    and ``UPDATE`` at [:L875-L890] - so an all-blank ``DEF-VAT`` reaches the
    server as the EMPTY STRING rather than as a space. That is observable in a
    table dump, which is why it is reproduced here rather than left to the
    driver.

    Args:
        value: The host variable's contents.

    Returns:
        ``value`` with trailing spaces removed.
    """
    return value.rstrip(" ")


def _pad_to(value: str, width: int) -> str:
    """Land a fetched character value in a fixed-width ``PIC X(n)``.

    The reverse of :func:`_truncate_trailing`. A ``CHAR`` column returns its
    value with trailing spaces already stripped, and the frozen program moves
    that into a fixed-width host variable, which space-pads it; the copybook
    field then receives the padded form. Over-long values are truncated on the
    right, which is what a COBOL ``MOVE`` into a shorter alphanumeric field
    does.

    Args:
        value: The fetched value.
        width: The host variable's declared width.

    Returns:
        ``value`` padded or truncated to exactly ``width`` characters.
    """
    return value[:width].ljust(width)


def _is_numeric_class(value: object) -> bool:
    """Reproduce the COBOL ``numeric`` class test on ``Def-Acs``.

    The frozen guard is ``if Def-Acs (A) numeric`` [common/irsdfltMT.cbl:L632]
    on the write and [:L684] on the rewrite, with ``move zeros to HV-DEF-ACS``
    as the else [:L635] [:L687]. The field is an unsigned ``DISPLAY`` picture
    [copybooks/irswsdflt.cob:L10], so the class test asks whether its bytes are
    all digits - which for a Python ``int`` means an integer that is not a
    ``bool`` and is not negative, since an unsigned zoned field cannot carry a
    sign.

    THIS VALIDATION IS COPIED, NOT EXTENDED. Rule R-3: "Validation is copied,
    never extended." No range check, no upper bound, and no rejection of the
    row - a non-numeric value becomes zero and the rest of the row is still
    written, exactly as the dictionary's own record of this guard states:
    "When the condition does not hold the move is not made, so the host
    variable keeps the value left by the INITIALIZE of its group - zero for a
    numeric, space for a character - while the rest of the row is still
    written."

    Args:
        value: Whatever ``Def-Acs (A)`` currently holds.

    Returns:
        ``True`` if the field would pass COBOL's ``numeric`` class test.
    """
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _load_host_variables(
    dflt: WsIrsDefaultRecord, index: int
) -> tuple[int, Decimal, str, str]:
    """Load ``TD-IRSDFLT-REC`` from one array slot, for one SQL statement.

    The Python analogue of the write loop's inline host-variable handling
    [common/irsdfltMT.cbl:L632-L641] and the rewrite's near-identical copy
    [:L684-L693]. This bridge has no ``bb000-HV-Load`` paragraph to correspond
    to - see A24 - so the loading is inline there and factored to one function
    here, called once per statement from both loops.

    RULE R-2, AND WHY THE FOUR TYPES ARE WHAT THEY ARE. Rule R-2 fixes the
    transport type of each column from the column itself: ``DEF-REC-KEY
    tinyint(2) unsigned`` [mysql/ACASDB.sql:L190] is an ``int``, ``DEF-ACS
    decimal(5,0) unsigned`` [:L191] is a :class:`~decimal.Decimal` - it is a
    ``decimal`` column, not an integer type, despite holding an account number -
    and ``DEF-CODES char(2)`` [:L192] and ``DEF-VAT char(1)`` [:L193] are
    ``str``. Nothing here is ever a binary float.

    The ``Decimal`` carries scale zero because all three layers agree on scale
    zero: the copybook field is ``pic 9(5)`` with no ``V``
    [copybooks/irswsdflt.cob:L10], the host variable is ``PIC 9(05) COMP``
    [common/irsdfltMT.cbl:L325] - a binary integer - and the column is
    ``decimal(5,0)``. Because the value is integral, an ``int`` and a scale-zero
    ``Decimal`` store the identical row, so following the column costs nothing
    behaviourally and keeps the transport type honest about what the column is.
    The record layer keeps its own declared type: ``records/irs_dflt.py``
    declares ``def_acs`` an ``int`` because the generated dictionary gives that
    field the INT storage class, and this module does not overrule a dependency's
    contract - it converts at the boundary, in both directions.

    Args:
        dflt: The 33-element linkage record.
        index: The one-based ``OCCURS`` subscript, ``A`` in the frozen loops.

    Returns:
        The four host-variable values in :data:`COLUMNS` order, ready to bind.
    """
    group = dflt.def_group[index - 1]

    # A4. `DEF-REC-KEY` COMES FROM THE SUBSCRIPT, NOT FROM THE RECORD.
    # `move A to WS-Key` then `move WS-Key to HV-DEF-REC-KEY`
    # [common/irsdfltMT.cbl:L637] [:L639]. The rewrite reaches the same place
    # with a single two-receiver move instead [:L689-L691] - a cosmetic
    # divergence between two otherwise identical loops, noted and not
    # normalised. There is no copybook field to read this from; the bridge
    # invents the value, which is why it is the authoritative mapping.
    hv_def_rec_key = index

    # The `numeric` class test, and the receiving-field truncation of the
    # `MOVE` into `HV-DEF-ACS PIC 9(05) COMP` [common/irsdfltMT.cbl:L632-L636].
    # The truncation is done in exact integer arithmetic and only then widened
    # to the column's `Decimal`, so no step of it can round: `%` on a Python
    # `int` keeps the low-order digits, which is what a `MOVE` into a
    # five-digit unsigned receiving field does.
    if _is_numeric_class(group.def_acs):
        hv_def_acs = Decimal(int(group.def_acs) % _DEF_ACS_MODULUS)
    else:
        # `move zeros to HV-DEF-ACS` [common/irsdfltMT.cbl:L635] [:L687].
        hv_def_acs = Decimal(0)

    # `move Def-Vat (A) to HV-DEF-VAT` [common/irsdfltMT.cbl:L640] and
    # `move Def-Codes (A) to HV-DEF-CODES` [:L641] - declared in that order in
    # the source, VAT before CODES, though the statement binds them in schema
    # order. Trailing spaces are trimmed as the bridge trims them when building
    # the statement text, so a blank slot is written as the empty string.
    hv_def_codes = _truncate_trailing(_pad_to(group.def_codes, _DEF_CODES_WIDTH))
    hv_def_vat = _truncate_trailing(_pad_to(group.def_vat, _DEF_VAT_WIDTH))

    return hv_def_rec_key, hv_def_acs, hv_def_codes, hv_def_vat


def _unload_row_into(dflt: WsIrsDefaultRecord, row: Mapping[str, object]) -> int:
    """Unload one fetched row into the array slot its own key selects.

    The Python analogue of [common/irsdfltMT.cbl:L603-L605], the three moves
    that scatter a fetched row into the ``OCCURS`` table.

    A6. THE SUBSCRIPT IS THE DATABASE VALUE, AND IT IS NOT BOUNDS-CHECKED.
    The frozen moves index a 33-element array with ``HV-DEF-REC-KEY`` - a value
    read from the database - under the comment "KEY = table position"
    [common/irsdfltMT.cbl:L603]. The host variable is ``PIC 9(03)`` [:L324] so
    it can carry up to 999, and the guard that precedes these moves
    ``exit perform``s rather than skipping the row [:L575-L583], so no
    per-iteration bound is ever applied. This is the same class of defect as
    Agent Action Plan anomaly 2, ``gl080``'s unbounded quarter subscript.

    NO BOUNDS CHECK IS ADDED HERE. Rule R-3 forbids new validation and rule R-4
    forbids the fix. The guard at [:L575-L583] - reproduced faithfully in
    :func:`read_next` - admits only 1..32 before these moves are reached, so
    the raw subscript is in range in practice; a Python negative index, which
    would wrap to the end of the tuple rather than run off the front as COBOL
    would, is therefore unreachable. Reaching for a check to make that
    unreachability explicit would be exactly the prohibited fix.

    Args:
        dflt: The 33-element linkage record.
        row: One fetched row, keyed by column name.

    Returns:
        The key the row was filed under - ``WS-Key`` at
        [common/irsdfltMT.cbl:L606].
    """
    # `MySQL_fetch_record` binds positionally into the host-variable group
    # [common/irsdfltMT.cbl:L552-L560]. Fetching by column name is equivalent
    # here and only here, because the group's declaration order [:L324-L327] is
    # the schema's ordinal order [mysql/ACASDB.sql:L190-L193] and the statement
    # is `SELECT *`.
    hv_def_rec_key = int(row[PRIMARY_KEY])

    # The column is `decimal(5,0)` [mysql/ACASDB.sql:L191] so the pinned
    # converter yields a `Decimal`; the copybook field is an unsigned,
    # scale-zero DISPLAY picture [copybooks/irswsdflt.cob:L10] whose dictionary
    # storage class is INT, so it lands as an `int` in the record. Rule R-2: the
    # value passes through `Decimal` and `int` and never through a binary float.
    # `Decimal(str(...))` is the exact route for whatever the driver hands back -
    # a `Decimal` passes through unchanged and a string of digits converts
    # exactly - and `int()` on a scale-zero `Decimal` cannot lose a digit.
    hv_def_acs = int(Decimal(str(row["DEF-ACS"])))
    hv_def_codes = _pad_to(str(row["DEF-CODES"]), _DEF_CODES_WIDTH)
    hv_def_vat = _pad_to(str(row["DEF-VAT"]), _DEF_VAT_WIDTH)

    # A6. The raw database value is the subscript. The frozen order is
    # ACS, VAT, CODES [common/irsdfltMT.cbl:L603-L605] - not schema order -
    # and is kept, because a partial failure part-way through would otherwise
    # leave a different slot populated.
    group = dflt.def_group[hv_def_rec_key - 1]
    group.def_acs = hv_def_acs
    group.def_vat = hv_def_vat
    group.def_codes = hv_def_codes

    return hv_def_rec_key


def _clear_all_slots(dflt: WsIrsDefaultRecord) -> None:
    """Reproduce ``initialize Default-Record with filler``.

    [common/irsdfltMT.cbl:L543], immediately before the read's fetch loop. All
    THIRTY-THREE groups are zeroed and blanked, not just the thirty-two the
    loop can fill, because the verb names the whole record.

    The consequence is the read's half of A2 and A8 together: any key absent
    from the table leaves its slot at zero and spaces, and slot 33 is left that
    way unconditionally because nothing can ever fill it.

    Args:
        dflt: The 33-element linkage record.
    """
    # OCCURS, not BRIDGE_LIMIT. This is the one place the full array length is
    # correct, because `initialize` names the record rather than a loop bound.
    for index in range(OCCURS):
        group = dflt.def_group[index]
        group.def_acs = 0
        group.def_codes = " " * _DEF_CODES_WIDTH
        group.def_vat = " " * _DEF_VAT_WIDTH



# ---------------------------------------------------------------------------
#  STATUS PLUMBING
# ---------------------------------------------------------------------------
# COBOL returns through the linkage record, so every status change is written
# into `File-Access` as well as returned. A caller may therefore read the pair
# or inspect the record, exactly as the frozen callers do.

#: ``Ws-Mysql-Error-Number`` is ``pic x(5)`` [copybooks/mysql-variables.cpy:L84]
#: - "changed to 5 char 18/09/16", per the comment there. THE WIDTH IS WHY A21
#: HAS NO EFFECT: both of the source's zero literals pad to the same five
#: characters.
_ERRNO_FIELD_WIDTH: Final[int] = 5


def _set_status(file_access: FileAccess, fs_reply: int, we_error: int) -> StatusPair:
    """Write a status pair into ``File-Access`` and return it.

    Args:
        file_access: The linkage record that carries the reply.
        fs_reply: The ``Fs-Reply`` value [copybooks/wsfnctn.cob:L25].
        we_error: The ``We-Error`` value [copybooks/wsfnctn.cob:L23].

    Returns:
        The pair, for a caller that prefers the return value.
    """
    file_access.fs_reply = fs_reply
    file_access.we_error = we_error
    return fs_reply, we_error


def _errno_is_zero(errno_text: str) -> bool:
    """Reproduce ``if WS-MYSQL-Error-Number not = "0..."`` as ONE predicate.

    A21 - MEASURED, AND CORRECTED. The frozen source compares this field
    against a zero literal at four sites, and the padding is not uniform: three
    spaces at [common/irsdfltMT.cbl:L526], [:L589] and [:L647], four spaces at
    [:L723]. The divergence is authored rather than introduced by the
    translator, appearing identically pre-translation at
    [common/irsdfltMT.scb:L501], [:L554], [:L612] and [:L688].

    IT HAS NO BEHAVIOURAL EFFECT, so it is reproduced as one predicate rather
    than two. ``Ws-Mysql-Error-Number`` is ``pic x(5)``
    [copybooks/mysql-variables.cpy:L84], so COBOL space-pads ``"0  "`` and
    ``"0   "`` alike to ``"0    "`` and both comparisons are the same
    comparison. Writing two predicates to honour the source text would have
    manufactured a difference the compiled program does not have - which rule
    R-4 forbids as surely as it forbids removing a real one. The received note
    also counted two sites; there are four, and only one uses four spaces.

    Args:
        errno_text: The driver's error number as text.

    Returns:
        ``True`` if the field would compare equal to the source's zero literal.
    """
    zero_literal = "0".ljust(_ERRNO_FIELD_WIDTH)
    return errno_text.ljust(_ERRNO_FIELD_WIDTH)[:_ERRNO_FIELD_WIDTH] == zero_literal


def _probe_driver_error(
    error: DriverError | None, file_access: FileAccess
) -> tuple[str, str, str]:
    """Reproduce the bridge's three-call error probe.

    The frozen sequence, identical at all four probe sites - the read's
    empty-table test [common/irsdfltMT.cbl:L523-L525], the fetch loop
    [:L586-L588], the write [:L644-L646] and the rewrite [:L720-L722] - is:
    ``call "MySQL_errno"``, ``call "MySQL_sqlstate"``, then
    ``move WS-MYSQL-SqlState to SQL-State``. SQLSTATE is stored
    UNCONDITIONALLY; the error number and message are stored only if the number
    is non-zero, and ``call "MySQL_error"`` is only made in that branch.

    Args:
        error: The driver error, or ``None`` if the statement itself succeeded
            and only the affected-row count was unexpected - which is the case
            the frozen source's ``count-rows not = 1`` test also admits.
        file_access: Receives ``SQL-State`` now and ``SQL-Err``/``SQL-Msg`` if
            the number is non-zero.

    Returns:
        The triple ``(errno_text, message, sql_state)``.
    """
    logging_data = file_access.logging_data

    # `call "MySQL_errno"` / `call "MySQL_sqlstate"`. Text, not an integer,
    # because `Ws-Mysql-Error-Number` is `pic x(5)` and the duplicate test
    # compares it as characters [common/irsdfltMT.cbl:L651].
    if error is None:
        errno_text = "0"
        message = ""
        sql_state = ""
    else:
        errno = getattr(error, "errno", None)
        errno_text = str(errno) if errno else "0"
        message = str(getattr(error, "msg", None) or error)
        sql_state = str(getattr(error, "sqlstate", None) or "")

    # `move WS-MYSQL-SqlState to SQL-State` - outside the `if`, so always.
    logging_data.sql_state = sql_state[: _status.SQL_STATE_WIDTH]

    if not _errno_is_zero(errno_text):
        # `call "MySQL_error" using WS-MYSQL-Error-Message`, then the two moves
        # [common/irsdfltMT.cbl:L648-L649] [:L724-L726].
        logging_data.sql_err = errno_text[: _status.SQL_ERR_WIDTH]
        logging_data.sql_msg = message[: _status.SQL_MSG_WIDTH]

    return errno_text, message, sql_state


def _is_duplicate_key(errno_text: str, sql_state: str) -> bool:
    """Reproduce this bridge's duplicate-key test.

    ``if SQL-Err (1:4) = "1062" or = "1022" or Sql-State = "23000"``
    [common/irsdfltMT.cbl:L651-L653] - three checks, evaluated against the
    four-character prefix of the error number and the full SQLSTATE.

    A20 - MEASURED, AND CORRECTED. The received note held this three-way form
    to be richer than ``glpostingMT``'s, which it described as SQLSTATE-only.
    ``glpostingMT.cbl:L818-L820`` carries the identical three-way rule, and a
    census of the twenty in-scope bridges puts this form in the majority at
    sixteen of twenty; the four exceptions - ``dfltMT``, ``finalMT``,
    ``sys4MT`` and ``slpostingMT`` - omit the SQLSTATE test. The surviving true
    statement is that practice varies by bridge and must be resolved per
    bridge, which is done here from this bridge's own source.

    Because the rule matches, the package's shared helper is used rather than a
    local reimplementation, and the equivalence against this bridge's own
    literals is checked below rather than asserted in prose.

    Args:
        errno_text: The driver's error number as text.
        sql_state: The driver's SQLSTATE.

    Returns:
        ``True`` if the frozen test would treat this as a duplicate key.
    """
    shared_verdict = _status.is_duplicate_key_bridge_level(errno_text, sql_state)

    # This bridge's own literals, evaluated directly. Not a second opinion -
    # a check that the shared helper still encodes THIS bridge's rule, so that
    # a future change to another bridge's rule cannot silently change this one.
    local_verdict = (
        errno_text[:_SQL_ERR_COMPARE_WIDTH] in _DUPLICATE_KEY_ERRNOS
        or sql_state == _DUPLICATE_KEY_SQLSTATE
    )
    if shared_verdict != local_verdict:  # pragma: no cover - drift guard
        _LOG.error(
            "%s: the shared duplicate-key rule no longer matches "
            "[common/irsdfltMT.cbl:L651-L653]; using this bridge's own rule",
            BRIDGE,
        )
        return local_verdict
    return shared_verdict


def _execute_one(
    connection: object, statement: str, parameters: Sequence[object]
) -> tuple[int, DriverError | None]:
    """Issue exactly one statement and report affected rows.

    The Python analogue of ``PERFORM MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT``
    as reached from ``bb200-Insert`` [common/irsdfltMT.cbl:L832] and
    ``bb300-Update`` [:L901], followed by the caller's
    ``WS-MYSQL-COUNT-ROWS not = 1`` test.

    ONE STATEMENT PER CALL, NEVER BATCHED. The thirty-two statements of a write
    or a rewrite are issued individually and in the loop's order because the
    scenario state diff is sensitive to statement order (section 0.3.3), and no
    transaction is opened around them because the frozen source opens none.

    Args:
        connection: An open connection from :func:`_ba020_process_open`.
        statement: One statement, identifiers already quoted.
        parameters: The values to bind, in the statement's order.

    Returns:
        ``(affected_rows, error)``. A raised driver error is reported as zero
        affected rows, which is what the frozen source's count-rows test sees
        after a failed ``MySQL_query``.
    """
    try:
        with _connection.execute_statement(connection, statement, parameters) as cursor:
            affected = cursor.rowcount
    except DriverError as error:
        return 0, error
    # A negative row count is the driver's "not applicable"; the frozen field
    # `Ws-Mysql-Count-Rows` is unsigned [copybooks/mysql-variables.cpy:L73], so
    # it can only be zero or positive.
    return max(affected, 0), None


def _execute_select(
    connection: object, statement: str, parameters: Sequence[object]
) -> tuple[tuple[Mapping[str, object], ...], DriverError | None]:
    """Issue the read's ``SELECT`` and materialise its result.

    The Python analogue of [common/irsdfltMT.cbl:L505-L513]: build the command,
    ``PERFORM MYSQL-1210-COMMAND``, ``PERFORM MYSQL-1220-STORE-RESULT``, then
    ``MOVE WS-MYSQL-RESULT TO TP-IRSDFLT-REC``. ``store-result`` materialises
    the whole result server-side-to-client before the fetch loop walks it,
    which is why the rows are collected here rather than streamed: the frozen
    program's row count is known before its first fetch, and the empty-table
    probe [:L522-L535] depends on that.

    Args:
        connection: An open connection.
        statement: The ``SELECT``, identifiers already quoted.
        parameters: The bound low-key value.

    Returns:
        ``(rows, error)`` with rows keyed by column name.
    """
    try:
        with _connection.execute_statement(connection, statement, parameters) as cursor:
            description = cursor.description or ()
            names = tuple(str(column[0]) for column in description)
            rows = tuple(
                dict(zip(names, tuple(values), strict=True))
                for values in cursor.fetchall()
            )
    except DriverError as error:
        return (), error
    return rows, None


# ---------------------------------------------------------------------------
#  THE RECORD-SIZE GATE  -  `ba012-Test-WS-Rec-Size-2`
# ---------------------------------------------------------------------------
# The handler's `A` is `77 A pic 9(4)` [common/acasirsub3.cbl:L124], default
# zero, and the whole paragraph body is wrapped in `if A = zero`
# [:L376] ... `end-if` [:L414]. Working storage survives across `CALL`s because
# the program is not `INITIAL`, so the body runs ONCE per process and every
# later call skips it. That latch is reproduced with a module-level flag.

_GATE_HAS_RUN: bool = False


def reset_record_size_gate() -> None:
    """Re-arm the once-only record-size gate.

    The frozen latch is process-lifetime working storage
    [common/acasirsub3.cbl:L376], so nothing in the COBOL re-arms it. This
    exists for tests, which need to exercise the first-call path more than once
    in a process, and mirrors
    :func:`~acas_posting.dal.connection.reset_rdb_data_cache`, which exists for
    the same reason.
    """
    global _GATE_HAS_RUN
    _GATE_HAS_RUN = False


def _ba012_test_ws_rec_size_2(
    system: SystemRecord, file_access: FileAccess
) -> StatusPair | None:
    """Compare the linkage record against the file record, once per process.

    ``ba012-Test-WS-Rec-Size-2`` [common/acasirsub3.cbl:L374-L414]. On the
    first call it measures both records and, if the linkage record is SHORTER
    than the file record, sets ``(99, 901)``, shows ``IR902``/``IR901``, waits
    for a keypress and transfers to ``ba-rdbms-exit`` WITHOUT CALLING THE
    BRIDGE [:L383-L402]. Otherwise it loads the connection parameters [:L408-
    L413] and falls through.

    The presentation is dropped and THE CONTROL TRANSFER IS PRESERVED, which is
    the rule section 0.3.4 lays down for an accept that only pauses for
    acknowledgement. The maintainer's own note on the abort - "COULD LET caller
    module deal with these errors !!!!!!!" [:L383], seven exclamation marks -
    is recorded and not acted on.

    Both records are 264 bytes here - 33 x 8 from the copybook
    [copybooks/irswsdflt.cob:L9-L12] and ``pic x(264)`` for the flat FD record
    [common/acasirsub3.cbl:L113] - so the comparison passes. It is still
    evaluated, because a mismatch aborts before any statement is issued.

    The connection parameters are loaded in the frozen source's order -
    Schema, UName, UPass, PORT, Host, Socket [:L408-L413], with port before
    host, which is NOT the declaration order of ``RDB-Data``
    [copybooks/wsfnctn.cob:L57-L64] - and loaded ONCE, never refreshed.
    :func:`~acas_posting.dal.connection.load_rdb_data_once` already reproduces
    exactly that latch and that order, so it is reused rather than restated.

    Args:
        system: The system record carrying the RDBMS credentials.
        file_access: Receives the status on failure.

    Returns:
        ``(99, 901)`` if the gate rejects the record, otherwise ``None`` to mean
        "fall through and carry on".
    """
    global _GATE_HAS_RUN

    if _GATE_HAS_RUN:
        # `if A = zero` is false on every later call, so the whole body -
        # including the credential load - is skipped
        # [common/acasirsub3.cbl:L376] [:L414].
        return None

    # `move function Length ( WS-IRS-Default-Record ) to A` [:L377-L379] and
    # `move function length ( Record-3 ) to B` [:L380-L382]. The source spells
    # the same intrinsic with a capital L then a lower-case l on adjacent
    # lines - identical to `common/acas029.cbl`, a package-wide copy-paste
    # (A34). Both lengths are the same 264 bytes.
    linkage_record_length = OCCURS * (
        _DEF_ACS_DIGITS + _DEF_CODES_WIDTH + _DEF_VAT_WIDTH
    )
    file_record_length = RECORD_LENGTH_BYTES

    _GATE_HAS_RUN = True

    if linkage_record_length < file_record_length:
        # `move 901 to WE-Error` / `move 99 to fs-reply` [:L384-L385], then
        # IR902 with the record number, IR901, an `accept`, and
        # `go to ba-rdbms-exit` [:L387-L402] - the bridge is never called.
        # Presentation dropped, control transfer kept.
        _LOG.error(
            "%s: IR902 Program Error: Temp rec = %d against a file record of "
            "%d [common/acasirsub3.cbl:L383-L385]",
            HANDLER,
            linkage_record_length,
            file_record_length,
        )
        return _set_status(
            file_access,
            int(_status.FsReply.ERROR),
            RECORD_SIZE_MISMATCH_WE_ERROR,
        )

    # `move RDBMS-DB-Name to DB-Schema` and its five siblings [:L408-L413].
    rdb_data = _connection.load_rdb_data_once(system)
    file_access.rdb_data = rdb_data
    return None


# ---------------------------------------------------------------------------
#  BRIDGE PARAGRAPHS  -  CONNECT, DISCONNECT, FREE, BAD FUNCTION
# ---------------------------------------------------------------------------
# These correspond to `irsdfltMT`'s OWN open and close, which the handler
# synthesises around every read, write and rewrite (A5). They are NOT the
# caller-facing `open_*`/`close` verbs below: those are the handler's codes 1
# and 2, which never reach the bridge at all (A10).

#: Cursor state for this table, at module scope so that the read's skipped
#: close (A12) leaks a cursor across calls exactly as the frozen bridge's
#: working storage does.
_CURSOR_STATES: Final[_cursor_state.CursorStateTable] = (
    _cursor_state.CursorStateTable()
)


def _cursor() -> _cursor_state.CursorState:
    """Return this table's single cursor slot.

    The bridge declares one cursor - ``Most-Cursor-Set`` with its two condition
    names [common/irsdfltMT.cbl:L282-L286] - and one key of reference
    [:L271], so there is exactly one slot.

    Returns:
        The primary cursor state for :data:`TABLE`.
    """
    return _CURSOR_STATES.state_for(TABLE, _cursor_state.CursorSlot.PRIMARY)


def _ba998_free(file_access: FileAccess) -> None:
    """Free the stored result and mark the cursor inactive.

    ``ba998-Free`` [common/irsdfltMT.cbl:L753-L763]: trace number 20,
    ``MySQL_free_result``, then ``move zero to Most-Cursor-Set``.

    Args:
        file_access: Receives the paragraph trace number.
    """
    file_access.logging_data.ws_no_paragraph = _PARA_FREE
    _cursor().free()


def _ba020_process_open(
    system: SystemRecord,
    file_access: FileAccess,
    *,
    transport: _connection.TransportSecurity | None,
) -> tuple[object | None, StatusPair]:
    """Connect, as ``ba020-Process-Open`` does.

    [common/irsdfltMT.cbl:L407-L453]: build the six connection strings from
    ``RDB-Data`` [:L416-L439], trace number 1 [:L440], ``PERFORM
    MYSQL-1000-OPEN THRU MYSQL-1090-EXIT`` [:L441], bail out on a non-zero
    reply [:L442-L443], set ``WS-File-Key`` to "OPEN IRS DEFAULT" [:L451] and
    then ``move zero to Most-Cursor-Set`` [:L452].

    THE CURSOR RESET AT [:L452] HAS A CONSEQUENCE WORTH STATING. Because the
    handler synthesises an open before every read (A5), ``Cursor-Not-Active`` is
    ALWAYS true when the read begins, so the ``SELECT`` is re-issued on every
    single ``read_next`` and the bridge's "cursor already active" path is
    unreachable through this handler. It is still reproduced, because the
    bridge contains it.

    Args:
        system: Supplies the credentials.
        file_access: Receives the trace number, key text and status.
        transport: TLS material for the connection, or ``None``. Needed as a
            parameter because a host-side caller reaching an isolated oracle
            must declare that explicitly rather than have it assumed.

    Returns:
        ``(connection_or_None, status_pair)``.
    """
    file_access.logging_data.ws_no_paragraph = _PARA_BRIDGE_OPEN

    outcome = _connection.mysql_1000_open(
        system,
        ws_no_paragraph=_PARA_BRIDGE_OPEN,
        we_error=int(file_access.we_error),
        transport=transport,
    )
    outcome.apply_to_logging_data(file_access.logging_data)

    if outcome.fs_reply != int(_status.FsReply.SUCCESS) or outcome.connection is None:
        # `if fs-reply not = zero go to ba999-end`
        # [common/irsdfltMT.cbl:L442-L443] - the open's own failure is
        # reported as-is.
        return None, _set_status(
            file_access, int(outcome.fs_reply), int(outcome.we_error)
        )

    file_access.logging_data.ws_file_key = _KEY_OPEN
    # `move zero to Most-Cursor-Set` [:L452].
    _cursor().set_cursor_not_active()
    return outcome.connection, _set_status(
        file_access, int(_status.FsReply.SUCCESS), int(_status.WeError.SUCCESS)
    )


def _ba030_process_close(connection: object | None, file_access: FileAccess) -> None:
    """Disconnect, as ``ba030-Process-Close`` does.

    [common/irsdfltMT.cbl:L455-L468]: free the result first if the cursor is
    active [:L456-L457], trace number 2 [:L459], ``WS-File-Key`` to
    "CLOSE IRS DEFAULT" [:L460], then ``PERFORM MYSQL-1980-CLOSE THRU
    MYSQL-1999-EXIT`` [:L465].

    A13. THIS PARAGRAPH'S STATUS IS ALWAYS DISCARDED, so it returns nothing.
    The handler saves the operation's status before calling close and restores
    it afterwards [common/acasirsub3.cbl:L452-L453] [:L462-L463] on the read
    and [:L478-L479] [:L482-L483] on the write, so a failing close is
    invisible to the caller. That is reproduced by not reporting it, which is
    also why this function's signature has no status in it.

    Args:
        connection: The connection to close, or ``None`` if the open failed.
        file_access: Receives the trace number and key text.
    """
    # `if Cursor-Active perform ba998-Free` [common/irsdfltMT.cbl:L456-L457].
    if _cursor().cursor_active():
        _ba998_free(file_access)

    file_access.logging_data.ws_no_paragraph = _PARA_BRIDGE_CLOSE
    file_access.logging_data.ws_file_key = _KEY_CLOSE
    _connection.mysql_1980_close(connection)


def _ba100_bad_function(file_access: FileAccess) -> StatusPair:
    """The bridge's bad-function paragraph.

    ``ba100-Bad-Function`` [common/irsdfltMT.cbl:L741-L747], which the source
    heads with "Houston; We have a problem" - a comment that appears in BOTH
    files' bad-function paragraphs. Sets ``990``/``99``.

    A26. The handler's own bad-function paragraph sets 999 rather than 990
    [common/acasirsub3.cbl:L344], and the two are NOT reconciled. This
    paragraph is unreachable through :func:`dispatch`, which filters the
    function code before the bridge would see it; it exists so the bridge's
    behaviour is represented and so the disagreement is visible in one place.

    Args:
        file_access: Receives the status.

    Returns:
        ``(99, 990)``.
    """
    return _set_status(file_access, int(_status.FsReply.ERROR), BRIDGE_BAD_FUNCTION)


def _aa100_bad_function(file_access: FileAccess) -> StatusPair:
    """The handler's bad-function paragraph.

    ``aa100-Bad-Function`` [common/acasirsub3.cbl:L340-L345], sets ``999``/
    ``99``. The RDB section carries a SECOND, textually distinct site with the
    same codes [:L517-L519] (A27); both are routed here because the codes
    agree, and both locators are recorded at their call sites so the two remain
    countable.

    Args:
        file_access: Receives the status.

    Returns:
        ``(99, 999)``.
    """
    return _set_status(file_access, int(_status.FsReply.ERROR), HANDLER_BAD_FUNCTION)



# ---------------------------------------------------------------------------
#  CLEARING VALUES  -  `move zero` AND `move spaces` ARE NOT THE SAME THING
# ---------------------------------------------------------------------------
# The figurative constant ZERO moved into an alphanumeric receiver fills it with
# the CHARACTER '0' repeated to the receiver's length, which is not what
# `move spaces` does. It matters here because the two layers clear the same
# fields differently, and A1's observability depends on what the rewrite leaves
# behind:
#   * the handler clears with spaces - `move spaces to SQL-Err SQL-Msg
#     SQL-State` [common/acasirsub3.cbl:L197], all three fields;
#   * the bridge clears `SQL-Err` with ZERO - [common/irsdfltMT.cbl:L623] on
#     entry to the write and [:L737] on exit from the rewrite - and `SQL-Msg`
#     with spaces [:L622] [:L738].
# One more asymmetry between handler and bridge, reproduced rather than
# harmonised.
_SQL_ERR_ZEROED: Final[str] = "0" * _status.SQL_ERR_WIDTH
_SQL_ERR_SPACES: Final[str] = " " * _status.SQL_ERR_WIDTH
_SQL_MSG_SPACES: Final[str] = " " * _status.SQL_MSG_WIDTH
_SQL_STATE_SPACES: Final[str] = " " * _status.SQL_STATE_WIDTH


def _ba040_process_read_next(
    connection: object, dflt: WsIrsDefaultRecord, file_access: FileAccess
) -> StatusPair:
    """Load the whole table into the 33-element record.

    ``ba040-Process-Read-Next`` [common/irsdfltMT.cbl:L470-L615], whose own
    opening comment reads "Getting the 32 rows for loading into one cobol rec" -
    the paragraph says 32, not 33 (A2).

    One ``SELECT`` positions a cursor, then a thirty-two iteration fetch loop
    scatters each row into the array slot ITS OWN KEY selects. Four separate
    end-of-data paths exist, each leaving a different diagnostic marker.

    Args:
        connection: An open connection.
        dflt: The 33-element linkage record, filled in place.
        file_access: Receives the status, trace numbers and diagnostics.

    Returns:
        The status pair as the loop left it - see A7, which is why that phrasing
        is exact.
    """
    cursor = _cursor()
    logging_data = file_access.logging_data

    if cursor.cursor_not_active():
        # `if Cursor-Not-Active` [common/irsdfltMT.cbl:L476]. Always true when
        # reached through this handler, because the synthesised open resets the
        # cursor [:L452].

        # A15. `set KOR-x1 to 1` [:L477] then `move KOR-offset (KOR-x1) to K`
        # [:L478] and `move KOR-length (KOR-x1) to L` [:L479]. BOTH ARE THEN
        # NEVER USED. They are computed here because the frozen source computes
        # them, and the offset/length pair describes a field that is not in the
        # record at all - offset 1, length 1 lands on the first digit of
        # `Def-Acs (1)` [copybooks/irswsdflt.cob:L10]. The comment on
        # [common/irsdfltMT.cbl:L476] reads "1 = Primary, 2 = Abrev, 3 = Desc"
        # on a table with ONE key -
        # copy-paste from a multi-key bridge.
        key_of_reference = _cursor_state.key_of_reference(TABLE, 1)
        dead_k = key_of_reference.kor_offset
        dead_l = key_of_reference.kor_length
        if (dead_k, dead_l) != (KEY_OFFSET, KEY_LENGTH):  # pragma: no cover
            _LOG.error(
                "%s: key metadata drifted from '00010001' "
                "[common/irsdfltMT.cbl:L268]",
                BRIDGE,
            )

        # A16 / A17. The predicate is built from a hard-coded relation and a
        # quoted string literal, with the only explicit `ORDER BY` in any
        # in-scope bridge appended [:L481-L495]. `Access-Type` is not consulted
        # - the facade sets it to zero for this verb
        # [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L241] - and `MOST-Relation`
        # [common/irsdfltMT.cbl:L283] is never read.
        logging_data.ws_log_where = _FROZEN_SELECT_ECHO  # [common/irsdfltMT.cbl:L497]
        logging_data.ws_no_paragraph = _PARA_READ_SELECT  # [common/irsdfltMT.cbl:L498]

        # [:L505-L513]. The bound value is the literal `"000"` the frozen source
        # interpolates [:L487]; binding it yields the identical predicate.
        #
        # AMBIGUITY Q-IRSDFLT-PREDICATE - RESOLVED BY MEASUREMENT against
        # MariaDB 10.11.7 [mysql/ACASDB.sql:L1]. The frozen predicate compares a
        # QUOTED THREE-CHARACTER STRING against a `tinyint(2) unsigned` column
        # [mysql/ACASDB.sql:L190], and which way the coercion goes decides which
        # rows come back: numeric would make it `> 0` and admit every legal key
        # 1..32, while a lexical comparison would order by characters.
        #
        # IT COERCES TO A NUMBER. Proved with a probe whose two readings disagree,
        # because `> "000"` on its own does not discriminate - every positive
        # integer's text also sorts above "000". Against a `tinyint(2) unsigned`
        # column holding 9 and 10: `k > "10"` returned NO rows and `k < "10"`
        # returned 9, which is the exact opposite of the lexical answer; and
        # `9 > "10"` evaluates 0 while `"9" > "10"` evaluates 1, so it is the
        # numeric operand that decides. Then measured directly on this shape: with
        # rows {1,2,9,10,31,32} present, `DEF-REC-KEY > "000"` matched ALL SIX,
        # identically to `> 0`.
        #
        # So the frozen predicate does admit every legal key, and the literal and
        # its type stay exactly as the source expresses them - now on evidence.
        rows, select_error = _execute_select(
            connection, _SELECT_STATEMENT, (READ_KEY_LITERAL,)
        )
        # `MYSQL-1220-STORE-RESULT` [common/irsdfltMT.cbl:L512].
        row_count = cursor.store_result(rows)
        logging_data.ws_count_rows = row_count
        logging_data.ws_file_key = _KEY_SELECT_ISSUED  # `move "> 0"` [:L515]

        # [:L516-L518] `if Testing-2 display Display-Message-1 with erase eos`.
        # Presentation, dropped. NOTE: the received working note held the
        # `Testing-2` gate to be unique to the rewrite; it is here as well, and
        # pre-translation at [common/irsdfltMT.scb:L491-L493].

        if row_count == 0:
            # THE EMPTY-TABLE PROBE [common/irsdfltMT.cbl:L522-L535], which the
            # source introduces with "It could be an empty table so test for
            # it". This is the
            # FOURTH end-of-data marker, and the one the received note omitted:
            # "No Data" [common/irsdfltMT.cbl:L533], alongside EOF, EOF2 and EOF3.
            _probe_driver_error(select_error, file_access)
            logging_data.ws_file_key = _KEY_NO_DATA
            # `move 10 to fs-reply` / `move 10 to WE-Error` [:L531-L532].
            status = _set_status(
                file_access,
                int(_status.FsReply.END_OF_FILE),
                int(_status.FsReply.END_OF_FILE),
            )
            # `go to ba998-Free` [:L534] - Class 4 sibling re-dispatch: the
            # target frees the cursor and then falls into `ba999-end`, so the
            # Python equivalent is the call followed by an explicit return.
            _ba998_free(file_access)
            return status

        # `move 1 to Most-Cursor-Set` [:L536], whose trailing comment is
        # "should test if select worked first??????" - six question marks. The
        # cursor is marked active WITHOUT verifying the select, and that is
        # preserved: `store_result` above reports the row count but its outcome
        # gates nothing beyond the zero test just made.
        cursor.set_cursor_active()

    # [common/irsdfltMT.cbl:L541-L543].
    logging_data.ws_log_where = " " * len(logging_data.ws_log_where)
    logging_data.ws_no_paragraph = _PARA_READ_FETCH
    # `initialize Default-Record with filler` [:L543] - all THIRTY-THREE slots.
    _clear_all_slots(dflt)

    # `perform varying A from 1 by 1 until A > 32` [:L544-L545]. The bound is
    # BRIDGE_LIMIT, never OCCURS (A2). The source also carries a commented-out
    # second bound, `*> or return-code not = zero` [common/irsdfltMT.cbl:L546].
    for a in range(1, BRIDGE_LIMIT + 1):
        # `MySQL_fetch_record` into the four host variables [:L552-L560].
        row = cursor.fetch_record()

        # A31. `if return-code = -1 or A > 32 or = zero` [:L564-L565]. The third
        # term is an abbreviated combined relation meaning `A = zero`, WHICH CAN
        # NEVER BE TRUE because `A` starts at 1 and only increases - a dead
        # condition. It is written out rather than dropped so the reader can see
        # what the source tests; `a == 0` is unreachable inside `range(1, ...)`.
        if row is None or a > BRIDGE_LIMIT or a == 0:
            # `move 10 to fs-Reply WE-Error` [:L566], `move "EOF"` [:L567],
            # `move zero to Most-Cursor-Set` [common/irsdfltMT.cbl:L568].
            #
            # A7's CONSEQUENCE LIVES HERE. A table holding fewer than 32 rows
            # exhausts the cursor and lands in this branch, so the caller is
            # told END-OF-FILE even though every available row was loaded
            # correctly - because the post-loop status reset is commented out
            # [:L613-L614]. The handler then treats a non-zero status as
            # failure and SKIPS ITS CLOSE [common/acasirsub3.cbl:L455-L458], so
            # a short table both misreports and leaks the cursor (A12).
            _set_status(
                file_access,
                int(_status.FsReply.END_OF_FILE),
                int(_status.FsReply.END_OF_FILE),
            )
            logging_data.ws_file_key = _KEY_EOF
            cursor.set_cursor_not_active()
            # Class 2 forward terminator: `exit perform`
            # [common/irsdfltMT.cbl:L571] plus the
            # post-loop work, which for this paragraph is nothing but the
            # commented-out reset.
            break

        key_value = int(row[PRIMARY_KEY])

        # A3. THE OFF-BY-ONE GUARD [common/irsdfltMT.cbl:L575-L583].
        # `if HV-DEF-REC-KEY = zero or > 32` terminates the read, writes "EOF3"
        # and MOVES THE KEY VALUE ITSELF INTO `WE-Error` [:L577], so a row 33
        # reports `WE-Error = 33` - a row number masquerading as an error code.
        # `FS-Reply` IS NOT SET IN THIS BRANCH, so the caller sees whatever
        # reply the previous iteration left alongside that number.
        #
        # This is the read-side face of A2: the copybook was widened to 33 "to
        # support temp. default 33 in postings (irs030)"
        # [copybooks/irswsdflt.cob:L7] and the read REJECTS such a row rather
        # than loading it. The error code is not normalised and the branch is
        # not turned into a skip: it terminates the loop, exactly as written.
        if key_value == 0 or key_value > BRIDGE_LIMIT:
            logging_data.ws_file_key = _KEY_EOF3
            # `move HV-DEF-REC-KEY to WE-Error` - the VALUE, not a code. Set
            # directly rather than through `_set_status`, because FS-Reply must
            # be left alone.
            file_access.we_error = key_value
            cursor.set_cursor_not_active()
            break  # Class 2 forward terminator [common/irsdfltMT.cbl:L582].

        if cursor.count_rows == 0:
            # [:L585-L601]. Unreachable in practice - the empty-table probe
            # above already returned for a zero row count, and the count does
            # not change as the loop fetches - but reproduced because the source
            # carries it, and because A32 lives in it.
            errno_text, _message, _sql_state = _probe_driver_error(
                None, file_access
            )
            if not _errno_is_zero(errno_text):
                # A32. `move 10 to fs-reply *> EOF equivilent !!` [:L593] -
                # a GENUINE SQL ERROR REPORTED AS END-OF-FILE. The mapping is
                # reproduced; a caller cannot distinguish the two, and that is
                # the defect.
                _set_status(
                    file_access,
                    int(_status.FsReply.END_OF_FILE),
                    int(_status.FsReply.END_OF_FILE),
                )
                logging_data.ws_file_key = _KEY_EOF2
            cursor.set_cursor_not_active()
            break  # Class 2 forward terminator [common/irsdfltMT.cbl:L601].

        # A6. The unload, indexing the array with the database value [:L603-
        # L605].
        stored_key = _unload_row_into(dflt, row)

        # `move HV-DEF-REC-KEY to WS-Key` then `move WS-Key to WS-File-Key`
        # [:L606-L607] - a two-step move through a `pic 99` intermediate
        # [common/irsdfltMT.cbl:L258], which cannot hold a value above 99.
        logging_data.ws_file_key = str(stored_key % 100)

        # [:L608-L610] `if Testing-1 perform Ca-Process-Logs` - "do for each row",
        # so the frozen hook fires ONCE PER ROW rather than once per call.
        #  NOTHING IS EMITTED HERE, for two reasons. The record named
        #  `stored_key`, which is `DEF-REC-KEY` - a business key (CWE-532) - and it
        #  was a per-row record, the highest volume in the module.
        # THE OTHER `perform Ca-Process-Logs` SITES ARE A RECORDED OMISSION. The
        # frozen paragraph is `call "fhlogger" using File-Access ACAS-DAL-Common-data`
        # [common/acasirsub3.cbl:L534-L538], and this verb does not receive
        # `ACAS-DAL-Common-data` - inventing a route for it would change the module's
        # linkage, which R-3 forbids. :func:`ca_process_logs` is the ONE faithful
        # reproduction of the paragraph and is performed where the linkage allows it,
        # at the common exit in :func:`dispatch` [:L347-L350]. A hand-rolled record
        # here stood for the paragraph without its field set, without its level and
        # without advancing `Log-File-Rec-Written`, which is the incoherence OBS-010
        # names; the omission is listed in `docs/migration/traceability.md`.


    # A7. THE POST-LOOP STATUS RESET IS COMMENTED OUT.
    # `*> move HV-DEF-REC-KEY to WS-File-Key.` [:L613] and
    # `*> move zero to fs-reply WE-Error.` [:L614]. So the status returned is
    # whatever the last iteration left - success only if all thirty-two rows
    # were fetched, end-of-file otherwise. NOTHING IS RESET HERE.
    return int(file_access.fs_reply), int(file_access.we_error)


def _ba070_process_write(
    connection: object, dflt: WsIrsDefaultRecord, file_access: FileAccess
) -> StatusPair:
    """Insert all thirty-two rows, blanks included, squashing failures.

    ``ba070-Process-Write`` [common/irsdfltMT.cbl:L617-L671]. Thirty-two
    ``INSERT`` statements, one per array slot, issued individually and in
    order.

    Args:
        connection: An open connection.
        dflt: The 33-element linkage record to write out.
        file_access: Receives the status and diagnostics.

    Returns:
        The status pair, which reports only the LAST failing row - see A9.
    """
    logging_data = file_access.logging_data

    # [:L618-L619] `move zero to WS-Mysql-Time-Step WS-SQL-Retry`. These arm the
    # lock-retry ladder in `COPY "mysql-procedures.cpy"` [:L751], whose only
    # `perform` is commented out at [copybooks/mysql-procedures.cpy:L167]. THE
    # LADDER IS DEAD, so `WE-Error 910` is unreachable and a lock surfaces as
    # `(99, 911)`. Reproduced as dead by not reaching it.

    # [common/irsdfltMT.cbl:L621-L623]. Note `move zero to SQL-Err` fills with
    # the CHARACTER '0', unlike the handler's `move spaces`
    # [common/acasirsub3.cbl:L197].
    _set_status(file_access, int(_status.FsReply.SUCCESS), int(_status.WeError.SUCCESS))
    logging_data.sql_msg = _SQL_MSG_SPACES
    logging_data.sql_err = _SQL_ERR_ZEROED
    logging_data.ws_no_paragraph = _PARA_WRITE  # [common/irsdfltMT.cbl:L624]

    # A23. `initialise TD-IRSDFLT-REC.` [:L625] - British spelling, executed
    # ONCE BEFORE THE LOOP rather than per statement as every `bb000-HV-Load`
    # in the other bridges does, and ABSENT ENTIRELY from the rewrite. All four
    # host variables are assigned on every iteration by
    # `_load_host_variables`, so the NOT-NULL invariant of section 0.6.2 holds
    # by a different mechanism here: nothing can leak between iterations
    # because nothing is left unassigned.

    # A9's accumulator: `ws-saved-fs-reply pic 99` [:L299].
    saved_fs_reply = 0

    # `perform varying A from 1 by 1 until A > 32` [:L626]. A2: never OCCURS.
    for a in range(1, BRIDGE_LIMIT + 1):
        # A8. THE EMPTY-SLOT SKIP IS COMMENTED OUT [:L627-L631]. The dead code
        # tests `Def-Acs (A) = zero and Def-Codes (A) = spaces and Def-Vat (A) =
        # space` and would `exit perform cycle`. Because it is commented out,
        # ALL THIRTY-TWO ROWS ARE ALWAYS INSERTED, including entirely blank
        # ones, and the table therefore always holds exactly 32 rows after a
        # write. No skip is added.

        # [:L632-L641], including the `numeric` class test and the key derived
        # from the subscript.
        parameters = _load_host_variables(dflt, a)

        # A22. `move WS-Key to WS-File-Key` [:L638], commented "will contain
        # the record with problems" - BUT IT IS OVERWRITTEN EVERY ITERATION, so
        # it ends holding 32 regardless of which row failed. A diagnostic that
        # cannot work, preserved as it is.
        logging_data.ws_file_key = str(a)

        # `perform bb200-Insert` [:L642] - one statement, never batched (A5).
        affected_rows, error = _execute_one(connection, _INSERT_STATEMENT, parameters)
        logging_data.ws_count_rows = affected_rows

        if affected_rows != 1:
            # [common/irsdfltMT.cbl:L643-L661].
            errno_text, _message, sql_state = _probe_driver_error(error, file_access)
            # [:L647] - three-space zero literal; see A21 for why one predicate
            # serves all four sites.
            if not _errno_is_zero(errno_text):
                if _is_duplicate_key(errno_text, sql_state):
                    # `move 22 to fs-reply` [common/irsdfltMT.cbl:L654].
                    file_access.fs_reply = int(_status.FsReply.DUPLICATE_KEY)
                else:
                    # `move 99 to fs-reply` [:L656], whose trailing comment is
                    # "this may need changing for val in WE-Error!!" - the
                    # maintainer's own note that this mapping is provisional.
                    file_access.fs_reply = int(_status.FsReply.ERROR)

            # A19. THE WRITE SETS `FS-Reply` ONLY, NEVER `WE-Error`. The rewrite
            # sets both and then discards both [:L727-L728]. The asymmetry is
            # reproduced: `we_error` is not touched anywhere in this loop.

        # [:L660-L662] `if Testing-1 perform Ca-Process-Logs`.
        # THE OTHER `perform Ca-Process-Logs` SITES ARE A RECORDED OMISSION. The
        # frozen paragraph is `call "fhlogger" using File-Access ACAS-DAL-Common-data`
        # [common/acasirsub3.cbl:L534-L538], and this verb does not receive
        # `ACAS-DAL-Common-data` - inventing a route for it would change the module's
        # linkage, which R-3 forbids. :func:`ca_process_logs` is the ONE faithful
        # reproduction of the paragraph and is performed where the linkage allows it,
        # at the common exit in :func:`dispatch` [:L347-L350]. A hand-rolled record
        # here stood for the paragraph without its field set, without its level and
        # without advancing `Log-File-Rec-Written`, which is the incoherence OBS-010
        # names; the omission is listed in `docs/migration/traceability.md`.

        # A9. THE SQUASHING LOOP [:L663-L666].
        # Each failing row's status is stashed and `fs-reply` is CLEARED "for
        # next loop iteration". So the loop NEVER STOPS on failure and only one
        # row's status can survive. Not fail-fast, and not aggregated either -
        # both would be fixes.
        if file_access.fs_reply != int(_status.FsReply.SUCCESS):
            saved_fs_reply = int(file_access.fs_reply)
            file_access.fs_reply = int(_status.FsReply.SUCCESS)

    # [:L668-L670] `if ws-saved-fs-reply not = zero` / "restore last error".
    # THE LAST failing row's status, not the first and not a count.
    if saved_fs_reply != int(_status.FsReply.SUCCESS):
        file_access.fs_reply = saved_fs_reply

    return int(file_access.fs_reply), int(file_access.we_error)


def _ba090_process_rewrite(
    connection: object, dflt: WsIrsDefaultRecord, file_access: FileAccess
) -> StatusPair:
    """Update all thirty-two rows, then discard every error.

    ``ba090-Process-Rewrite`` [common/irsdfltMT.cbl:L673-L739]. Thirty-two
    ``UPDATE`` statements, then an UNCONDITIONAL reset of the error fields -
    the second half of A1, and the reason a failed write reports success.

    Args:
        connection: An open connection.
        dflt: The 33-element linkage record to write out.
        file_access: Receives the status and diagnostics.

    Returns:
        Always ``(0, 0)``. That is the defect, not a simplification.
    """
    logging_data = file_access.logging_data

    # [:L675-L676] `move zero to WS-Mysql-Time-Step WS-SQL-Retry` - the dead
    # ladder again. NOTE WHAT IS MISSING: unlike the write [:L621-L623], this
    # paragraph does NOT clear `FS-Reply`, `WE-Error`, `SQL-Msg` or `SQL-Err` on
    # entry, so it begins with whatever the failed write left behind. A further
    # asymmetry between two otherwise parallel paragraphs, reproduced.
    logging_data.ws_no_paragraph = _PARA_REWRITE  # [:L677]

    # A23. THERE IS NO `initialise TD-IRSDFLT-REC` HERE, where the write has one
    # at [:L625]. Absence reproduced by absence.

    # `perform varying A from 1 by 1 until A > 32` [:L678]. A2 again.
    for a in range(1, BRIDGE_LIMIT + 1):
        # A8. The same commented-out empty-slot skip [:L679-L683]. All
        # thirty-two rows are updated, blanks included.

        # [:L684-L693]. The rewrite reaches the same host-variable state as the
        # write but spells one move differently: `move WS-Key to WS-File-Key /
        # HV-DEF-REC-KEY` is a single TWO-RECEIVER move [:L689-L691] where the
        # write uses two separate moves [:L637] [:L639]. Cosmetic, and noted
        # rather than normalised.
        parameters = _load_host_variables(dflt, a)
        logging_data.ws_file_key = str(a)  # A22, again [:L690].

        # A15. `set KOR-x1 to 1` / `move KOR-offset to K` / `move KOR-length to
        # L` [:L695-L697] - computed, never used, for the second time.
        key_of_reference = _cursor_state.key_of_reference(TABLE, 1)
        dead_k = key_of_reference.kor_offset
        dead_l = key_of_reference.kor_length
        if (dead_k, dead_l) != (KEY_OFFSET, KEY_LENGTH):  # pragma: no cover
            _LOG.error(
                "%s: key metadata drifted from '00010001' "
                "[common/irsdfltMT.cbl:L268]",
                BRIDGE,
            )

        # A15, continued. THE WHERE IS REBUILT PER ITERATION from the LOOP
        # SUBSCRIPT [:L699-L711], and the two alternatives the maintainer tried
        # first are preserved commented out immediately above it: the canonical
        # `Default-Record (K:L)` record-buffer substring [:L705] and the host
        # variable [:L706]. The live line is `WS-KEY delimited by size` [:L707]
        # with the comment "use the real key for row". The canonical
        # construction was tried, found to index a field that is not in the
        # record, and abandoned.
        logging_data.ws_log_where = f'{PRIMARY_KEY}="{a}"'  # [:L712]

        # `perform bb300-Update` [:L713]. The statement re-assigns the primary
        # key in its own SET list as well as matching on it in the WHERE - a
        # translator artifact, see `_UPDATE_STATEMENT`. Bound order is the four
        # SET values then the WHERE value.
        affected_rows, error = _execute_one(
            connection, _UPDATE_STATEMENT, (*parameters, a)
        )
        logging_data.ws_count_rows = affected_rows

        # [:L715-L717] `if Testing-2 display Display-Message-1 with erase eos`.
        # Presentation, dropped. The second of the two `Testing-2` gates.

        if affected_rows != 1:
            # [:L719-L731]. Note that MySQL reports zero affected rows for an
            # UPDATE that matched but changed nothing, so this branch is entered
            # on a perfectly successful no-op update; the errno is then zero and
            # nothing is set. Faithful either way, because of the reset below.
            errno_text, _message, _sql_state = _probe_driver_error(error, file_access)
            # [:L723] - the FOUR-space zero literal, the only one of the four
            # sites that uses four. Same predicate; see A21.
            if not _errno_is_zero(errno_text):
                # `move 99 to fs-reply` [:L727] carrying the same provisional
                # note as the write, and `move 994 to WE-Error` [:L728].
                file_access.fs_reply = int(_status.FsReply.ERROR)
                # A18. `WE-Error 994` IS SET HERE AND CLEARED BELOW, so it is
                # permanently unobservable - a dead error code. It is still set,
                # because a value that is never set cannot be cleared, and the
                # clearing is the defect.
                file_access.we_error = REWRITE_UNOBSERVABLE_WE_ERROR

        # [:L731-L733] `if Testing-1 perform Ca-Process-Logs`. The status this
        # loop is about to destroy [:L736-L738] is anomaly A19's own content, and it
        # is documented in `docs/migration/anomaly-log.md` rather than narrated once
        # per row.
        # THE OTHER `perform Ca-Process-Logs` SITES ARE A RECORDED OMISSION. The
        # frozen paragraph is `call "fhlogger" using File-Access ACAS-DAL-Common-data`
        # [common/acasirsub3.cbl:L534-L538], and this verb does not receive
        # `ACAS-DAL-Common-data` - inventing a route for it would change the module's
        # linkage, which R-3 forbids. :func:`ca_process_logs` is the ONE faithful
        # reproduction of the paragraph and is performed where the linkage allows it,
        # at the common exit in :func:`dispatch` [:L347-L350]. A hand-rolled record
        # here stood for the paragraph without its field set, without its level and
        # without advancing `Log-File-Rec-Written`, which is the incoherence OBS-010
        # names; the omission is listed in `docs/migration/traceability.md`.


    # A1 / A18. THE UNCONDITIONAL RESET [:L736-L738].
    #
    # `move zero to FS-Reply WE-Error.` / `move zero to SQL-Err.` /
    # `move spaces to SQL-Msg.` - outside the loop, outside any `if`. A rewrite
    # that failed on all thirty-two rows returns (0, 0) with no error text.
    #
    # Combined with the handler's silent retry [common/acasirsub3.cbl:L484-L492]
    # this is why A FAILED WRITE ALWAYS REPORTS SUCCESS: the handler clears the
    # write's status and sets rewrite, the rewrite runs its thirty-two updates,
    # and then this clears everything again. Neither layer alone would fully
    # hide the error.
    #
    # NOTE PRECISELY WHAT IS CLEARED: FS-Reply, WE-Error, SQL-Err and SQL-Msg.
    # `SQL-State` IS NOT among them and survives, so a caller that inspects
    # SQLSTATE can still see evidence a statement failed even though the status
    # pair says otherwise. The received note said "all four status fields";
    # there are four fields cleared, but SQL-State is not one of them.
    _set_status(file_access, int(_status.FsReply.SUCCESS), int(_status.WeError.SUCCESS))
    logging_data.sql_err = _SQL_ERR_ZEROED
    logging_data.sql_msg = _SQL_MSG_SPACES

    return int(_status.FsReply.SUCCESS), int(_status.WeError.SUCCESS)



# ---------------------------------------------------------------------------
#  THE CALLER-FACING VERBS
# ---------------------------------------------------------------------------
# A10. OPEN AND CLOSE ARE NO-OPS ON BOTH PATHS, AND NEITHER REACHES THE BRIDGE.
#
# The maintainer explains the shape himself [common/acasirsub3.cbl:L169-L176]:
#
#     WARNING The modules acasirsub5 for Final as well as acasirsub3 for
#      defaults has to be modified as IRS only does a read or write
#       and not a direct open or close so
#       it has to be done here when processing RDB.
#       For Cobol files these have been changed to do the same so direct
#        calls to open and close are not needed or wanted.
#         so return with fs-reply & we-error = zero.
#
# So on the FLAT path codes 1 and 2 return (0, 0) and jump to `aa-Exit`
# [:L200-L207], their real bodies commented out [:L220-L256]; and on the RDB
# path they are intercepted before `ba020-Call-DAL` [:L429-L438]. The bridge DOES
# implement open and close [common/irsdfltMT.cbl:L407] [:L455] - that is how the
# handler's own synthesised calls are serviced - but a CALLER's code 1 or 2
# never gets there.


def _no_op_open_or_close(file_access: FileAccess, *, is_close: bool) -> StatusPair:
    """Return ``(0, 0)`` without touching the database.

    A10 for both paths, and A30 for the flat one.

    A30. CODES 1 AND 2 JUMP TO `aa-Exit`, BYPASSING `aa999-main-exit`
    [common/acasirsub3.cbl:L203] [:L207], and `aa999-main-exit` is where the
    logging hook lives [:L347-L350]. So these two verbs are the only ones that
    produce no log record at all, and that bypass is reproduced by emitting
    none here.

    The close additionally zeroes ``File-Function`` and ``Access-Type`` to close
    the logger - live at [:L433-L438] on the RDB path, and present in the dead
    flat body too [:L254-L255].

    Args:
        file_access: Receives ``(0, 0)`` and, for a close, the zeroed function
            and access codes.
        is_close: ``True`` for code 2, ``False`` for code 1.

    Returns:
        ``(0, 0)``, always.
    """
    status = _set_status(
        file_access, int(_status.FsReply.SUCCESS), int(_status.WeError.SUCCESS)
    )
    if is_close:
        # `move zero to File-Function Access-Type` [:L434-L435], commented
        # "Close ignore & close logger".
        file_access.file_function = 0
        file_access.access_type = 0
    return status


def open_(file_access: FileAccess) -> StatusPair:
    """``fn-open`` with ``fn-i-o``. A no-op returning ``(0, 0)``.

    Reached from ``acasirsub3-Open``
    [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L223-L227], the only verb besides
    ``Open-Input`` whose reply the IRS facade checks - and, on a non-zero reply,
    the only kind of failure that makes the facade return from the program
    outright [:L364]. Since this can only reply ``(0, 0)``, that check can never
    fire through this handler, and the facade's ``perform acasirsub3-Close``
    [:L344] would close nothing either.

    Args:
        file_access: Receives ``(0, 0)``.

    Returns:
        ``(0, 0)``.
    """
    return _no_op_open_or_close(file_access, is_close=False)


def open_input(file_access: FileAccess) -> StatusPair:
    """``fn-open`` with ``fn-input``. A no-op returning ``(0, 0)``.

    Reached from ``acasirsub3-Open-Input``
    [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L229-L233].

    Args:
        file_access: Receives ``(0, 0)``.

    Returns:
        ``(0, 0)``.
    """
    return _no_op_open_or_close(file_access, is_close=False)


def open_output(file_access: FileAccess) -> StatusPair:
    """``fn-open`` with ``fn-output``. A no-op returning ``(0, 0)``.

    NOT PUBLISHED BY THE IRS FACADE for this handler - the six verbs it does
    publish are listed in :data:`FACADE_VERBS` - and this handler has NO
    Open-Output coercion block, unlike ``acas008`` where an open-output means
    "delete every row". The handler filters on ``fn-open`` alone
    [common/acasirsub3.cbl:L429] without inspecting the access type, so an
    output open is intercepted as a no-op like any other, and NOTHING IS
    DELETED. That difference from ``acas008`` is behaviour, not an oversight to
    correct.

    Args:
        file_access: Receives ``(0, 0)``.

    Returns:
        ``(0, 0)``.
    """
    return _no_op_open_or_close(file_access, is_close=False)


def open_extend(file_access: FileAccess) -> StatusPair:
    """``fn-open`` with ``fn-extend``. A no-op returning ``(0, 0)``.

    On the RDB path the access type is not inspected
    [common/acasirsub3.cbl:L429], so this is a no-op like any other open. The
    DEAD flat body would have
    rejected it with ``(99, 997)`` [:L232-L234]; that code is declared as
    ``_DEAD_FLAT_ACCESS_TYPE_WRONG`` and never returned, because the path that
    returns it is commented out (A10).

    Args:
        file_access: Receives ``(0, 0)``.

    Returns:
        ``(0, 0)``.
    """
    return _no_op_open_or_close(file_access, is_close=False)


def close(file_access: FileAccess) -> StatusPair:
    """``fn-close``. A no-op returning ``(0, 0)``, plus zeroing the log codes.

    Reached from ``acasirsub3-Close``
    [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L235-L238].

    Args:
        file_access: Receives ``(0, 0)`` and zeroed function/access codes.

    Returns:
        ``(0, 0)``.
    """
    return _no_op_open_or_close(file_access, is_close=True)


def _unsupported_verb(file_access: FileAccess, verb: str) -> StatusPair:
    """Route a verb this handler does not dispatch to bad function.

    THREE INDEPENDENT REASONS these verbs are unreachable, which is why they are
    grouped rather than each argued separately:

    1. **The handler dispatches only five codes** - 1, 2, 3, 5 and 7
       [common/acasirsub3.cbl:L199-L215]. It is one of only two five-code
       handlers in the package, with ``acasirsub5``; every other handler
       dispatches at least eight. Anything else falls to ``when other``
       [:L213-L214].
    2. **The bridge has no ``DELETE`` section at all** (A24). Its only ``bb``
       sections are ``bb200-Insert`` [common/irsdfltMT.cbl:L774] and
       ``bb300-Update`` [:L839]; there is no delete statement anywhere in the
       916 lines.
    3. **The IRS facade never publishes them** for this handler
       [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L223-L253] - see
       :data:`FACADE_VERBS`.

    And ``fn-Delete-All`` (6) is dispatched by NO handler in the package at all:
    it is reachable only by coercion inside an Open-Output block, and this
    handler has no such block. So an explicit 6 lands here too.

    Args:
        file_access: Receives ``(99, 999)``.
        verb: The verb name, for the log record only.

    Returns:
        ``(99, 999)`` - the HANDLER's code. A26: the bridge's own bad-function
        paragraph would say 990 [common/irsdfltMT.cbl:L743], and the two are not
        reconciled; the handler is the module boundary, so 999 is what a caller
        sees.
    """
    # ONE ERROR, through the shared reporter. The refusal returns (99, 999) to the
    # caller, so it is a failure and DEBUG put it below the level an operator
    # watches - the same reasoning that took every other handler's verb refusal off
    # DEBUG.
    _status.log_handler_failure(
        _LOG,
        program=HANDLER,
        paragraph="aa100-Bad-Function",
        locator="[common/acasirsub3.cbl:L199-L215]",
        fs_reply=int(_status.FsReply.ERROR),
        we_error=int(_status.WeError.NOT_USED),
        detail="verb %s is not dispatched by this handler; the bridge's own "
        "bad-function paragraph would report 990 instead (anomaly A26)" % verb,
    )
    return _aa100_bad_function(file_access)


def read_indexed(file_access: FileAccess) -> StatusPair:
    """``fn-read-indexed``. Not dispatched; returns ``(99, 999)``.

    Args:
        file_access: Receives ``(99, 999)``.

    Returns:
        ``(99, 999)``.
    """
    return _unsupported_verb(file_access, "fn-read-indexed")


def start(file_access: FileAccess) -> StatusPair:
    """``fn-start``. Not dispatched; returns ``(99, 999)``.

    Args:
        file_access: Receives ``(99, 999)``.

    Returns:
        ``(99, 999)``.
    """
    return _unsupported_verb(file_access, "fn-start")


def delete(file_access: FileAccess) -> StatusPair:
    """``fn-delete``. Not dispatched; returns ``(99, 999)``.

    Args:
        file_access: Receives ``(99, 999)``.

    Returns:
        ``(99, 999)``.
    """
    return _unsupported_verb(file_access, "fn-delete")


def delete_all(file_access: FileAccess) -> StatusPair:
    """``fn-Delete-All``. Not dispatched by ANY handler; returns ``(99, 999)``.

    Args:
        file_access: Receives ``(99, 999)``.

    Returns:
        ``(99, 999)``.
    """
    return _unsupported_verb(file_access, "fn-Delete-All")


# ---------------------------------------------------------------------------
#  THE THREE REAL OPERATIONS  -  THREE BRIDGE CALLS EACH  (A5)
# ---------------------------------------------------------------------------


def read_next(
    system: SystemRecord,
    dflt: WsIrsDefaultRecord,
    file_access: FileAccess,
    *,
    transport: _connection.TransportSecurity | None = None,
) -> StatusPair:
    """``fn-read-next``: synthesised open, read, then close - unless it failed.

    The handler's read block [common/acasirsub3.cbl:L440-L467]. THREE bridge
    calls with the function code mutated between them (A5), with the operation's
    status saved around the close (A13) and the close SKIPPED on failure (A12).

    Args:
        system: Supplies the credentials for the synthesised open.
        dflt: The 33-element linkage record, filled in place.
        file_access: Carries the reply.
        transport: TLS material for the connection, or ``None``.

    Returns:
        The read's status pair, never the close's.
    """
    # `move zero to FS-Reply WE-Error` [:L441].
    _set_status(file_access, int(_status.FsReply.SUCCESS), int(_status.WeError.SUCCESS))

    # `set fn-Open to true` / `set fn-Input to true` [:L442-L443], then
    # `perform ba020-Call-DAL` [:L444] - the synthesised OPEN, with access type
    # INPUT for a read (the write and rewrite use I-O instead).
    file_access.file_function = int(_status.FileFunction.OPEN)
    file_access.access_type = int(_status.AccessType.INPUT)
    connection, (fs_reply, we_error) = _ba020_process_open(
        system, file_access, transport=transport
    )
    if (
        fs_reply != int(_status.FsReply.SUCCESS)
        or we_error != int(_status.WeError.SUCCESS)
        or connection is None
    ):
        # `go to ba-rdbms-Exit` [:L446-L449]. Class 3 section exit -> return.
        return fs_reply, we_error

    # `set fn-Read-Next to true` / `perform ba020-Call-DAL` [:L450-L451].
    file_access.file_function = int(_status.FileFunction.READ_NEXT)
    fs_reply, we_error = _ba040_process_read_next(connection, dflt, file_access)

    # A13. `move FS-Reply to WS-Save-FS-Reply` / `move WE-Error to
    # WS-Save-WE-Error` [:L452-L453] - THE OPERATION'S STATUS IS CAPTURED
    # BEFORE THE CLOSE, so the close can never report anything.
    saved_fs_reply, saved_we_error = fs_reply, we_error

    # `perform Ca-Process-Logs` [:L454] - UNGATED here, unlike the bridge's hooks
    # which test `Testing-1`, and marked "temp only during testing".
    # THE OTHER `perform Ca-Process-Logs` SITES ARE A RECORDED OMISSION. The
    # frozen paragraph is `call "fhlogger" using File-Access ACAS-DAL-Common-data`
    # [common/acasirsub3.cbl:L534-L538], and this verb does not receive
    # `ACAS-DAL-Common-data` - inventing a route for it would change the module's
    # linkage, which R-3 forbids. :func:`ca_process_logs` is the ONE faithful
    # reproduction of the paragraph and is performed where the linkage allows it,
    # at the common exit in :func:`dispatch` [:L347-L350]. A hand-rolled record
    # here stood for the paragraph without its field set, without its level and
    # without advancing `Log-File-Rec-Written`, which is the incoherence OBS-010
    # names; the omission is listed in `docs/migration/traceability.md`.


    if saved_fs_reply != int(_status.FsReply.SUCCESS) or saved_we_error != int(
        _status.WeError.SUCCESS
    ):
        # A12. THE READ SKIPS ITS CLOSE ON FAILURE [:L455-L458], leaving an
        # unbalanced open. THE WRITE DOES NOT [:L480-L481] - a real asymmetry
        # between two adjacent blocks, and it is not levelled here.
        #
        # Because A7 makes ANY table of fewer than 32 rows report end-of-file,
        # this path is the normal one for a short table, not an edge case.
        #
        # What is observable, and therefore what is reproduced, is that NO
        # CLOSE IS ISSUED: the stored result is not freed and the connection is
        # not disconnected, exactly as the frozen source leaves them. The
        # connection object is not retained either, so Python's driver will
        # release the socket when it is collected - which differs from COBOL's
        # process-lifetime leak only in a way no table dump can see, while
        # retaining a reference would make the leak strictly worse than the
        # original. Adding the missing close would be the prohibited fix.
        #  NO RECORD HERE. The frozen source SKIPS the close - it executes
        #  nothing on this path and displays nothing - so a record announcing the
        #  absence was invented (R-4). The leak is the anomaly, and it is recorded in
        #  the comment above and in `docs/migration/anomaly-log.md`.
        return saved_fs_reply, saved_we_error

    # `set fn-Close to true` / `perform ba020-Call-DAL` [:L459-L460].
    file_access.file_function = int(_status.FileFunction.CLOSE)
    _ba030_process_close(connection, file_access)

    # A13. `move WS-Save-FS-Reply to FS-Reply` / `move WS-Save-WE-Error to
    # WE-Error` [:L462-L463] - the close's own status is discarded by being
    # overwritten.
    _set_status(file_access, saved_fs_reply, saved_we_error)
    file_access.logging_data.ws_file_key = _KEY_OPEN_READ_CLOSE  # [:L464]
    return saved_fs_reply, saved_we_error


def write(
    system: SystemRecord,
    dflt: WsIrsDefaultRecord,
    file_access: FileAccess,
    *,
    transport: _connection.TransportSecurity | None = None,
) -> StatusPair:
    """``fn-write``: open, 32 inserts, close - then silently retry as a rewrite.

    The handler's write block [common/acasirsub3.cbl:L468-L492].

    A1, FIRST HALF. On failure this DOES NOT REPORT THE FAILURE. It writes a
    diagnostic key, sets ``fn-Re-write``, CLEARS ``fs-reply`` and ``we-error``
    [:L488-L489], and falls through into the rewrite block - which then clears
    its own errors unconditionally [common/irsdfltMT.cbl:L736-L738]. So a write
    that failed on all thirty-two rows returns ``(0, 0)``.

    A14 MAKES THAT FALL-THROUGH REACHABLE, and the proof is worth stating
    because it is the only Class 4 transfer in this module. The block ends with a
    SINGLE ``end-if.`` at [:L492] while TWO ``if``s are open - ``if fn-Write``
    [:L468] and ``if (fs-Reply not = zero or WE-Error not = zero)`` [:L484]. The
    period terminates the sentence and so implicitly closes the outer one, which
    means the ``else go to ba-RDBMS-Exit`` [:L490-L491] binds to the INNER
    condition. Therefore: the write succeeded -> ``else`` -> return; the write
    failed -> the ``if`` body runs, sets ``fn-Re-write``, and control reaches
    [:L494] where ``if fn-Re-write`` is now true. The sibling rewrite block
    [:L494-L513] is properly matched with its own ``end-if.`` at [:L513], so
    this block is short exactly one ``end-if`` relative to its twin - the same
    class of construct as Agent Action Plan anomaly 1, ``sl060``'s missing
    terminating period. The fall-through is reproduced, not the tidied version.

    Args:
        system: Supplies the credentials for the synthesised opens.
        dflt: The 33-element linkage record to write out.
        file_access: Carries the reply.
        transport: TLS material for the connections, or ``None``.

    Returns:
        The status pair - which on any failure is the rewrite's ``(0, 0)``.
    """
    # `set fn-Open to true` / `set fn-I-O to true` [:L469-L470] - I-O here,
    # where the read used INPUT.
    file_access.file_function = int(_status.FileFunction.OPEN)
    file_access.access_type = int(_status.AccessType.I_O)
    connection, (fs_reply, we_error) = _ba020_process_open(
        system, file_access, transport=transport
    )
    if (
        fs_reply != int(_status.FsReply.SUCCESS)
        or we_error != int(_status.WeError.SUCCESS)
        or connection is None
    ):
        # `go to ba-rdbms-Exit` [:L472-L475]. Class 3 -> return.
        return fs_reply, we_error

    # `set fn-Write to true` / `perform ba020-Call-DAL` [:L476-L477].
    file_access.file_function = int(_status.FileFunction.WRITE)
    fs_reply, we_error = _ba070_process_write(connection, dflt, file_access)

    # A13. Save before the close [:L478-L479].
    saved_fs_reply, saved_we_error = fs_reply, we_error

    # `set fn-Close to true` / `perform ba020-Call-DAL` [:L480-L481].
    # UNCONDITIONAL - contrast the read, which skips this on failure (A12).
    file_access.file_function = int(_status.FileFunction.CLOSE)
    _ba030_process_close(connection, file_access)

    # A13. Restore both [:L482-L483].
    _set_status(file_access, saved_fs_reply, saved_we_error)

    if saved_fs_reply == int(_status.FsReply.SUCCESS) and saved_we_error == int(
        _status.WeError.SUCCESS
    ):
        # `else go to ba-RDBMS-Exit` [:L490-L491], bound to the INNER condition
        # by A14. Class 3 -> return.
        return saved_fs_reply, saved_we_error

    # A1 / A14. The failure path: diagnose, log, set the rewrite function, and
    # DESTROY THE STATUS [:L486-L489].
    file_access.logging_data.ws_file_key = _KEY_OPEN_WRITE_FAILED_CLOSE  # [:L486]

    # `perform Ca-Process-Logs` [:L487]. Anomalies A1 and A14 - a failed write is
    # retried as a rewrite that reports success, destroying the status - are recorded
    # in `docs/migration/anomaly-log.md`, which is where a reader finds them.
    # THE OTHER `perform Ca-Process-Logs` SITES ARE A RECORDED OMISSION. The
    # frozen paragraph is `call "fhlogger" using File-Access ACAS-DAL-Common-data`
    # [common/acasirsub3.cbl:L534-L538], and this verb does not receive
    # `ACAS-DAL-Common-data` - inventing a route for it would change the module's
    # linkage, which R-3 forbids. :func:`ca_process_logs` is the ONE faithful
    # reproduction of the paragraph and is performed where the linkage allows it,
    # at the common exit in :func:`dispatch` [:L347-L350]. A hand-rolled record
    # here stood for the paragraph without its field set, without its level and
    # without advancing `Log-File-Rec-Written`, which is the incoherence OBS-010
    # names; the omission is listed in `docs/migration/traceability.md`.


    # `set fn-Re-write to true` [:L488] and `move zero to fs-reply we-error`
    # [:L489], commented "clear if used in write".
    file_access.file_function = int(_status.FileFunction.RE_WRITE)
    _set_status(file_access, int(_status.FsReply.SUCCESS), int(_status.WeError.SUCCESS))

    # Class 4 sibling re-dispatch: fall through to `if fn-Re-write` [:L494].
    # The named call plus an explicit return is the transformation, and the
    # equivalence is proved in this function's docstring rather than assumed.
    return rewrite(system, dflt, file_access, transport=transport)


def rewrite(
    system: SystemRecord,
    dflt: WsIrsDefaultRecord,
    file_access: FileAccess,
    *,
    transport: _connection.TransportSecurity | None = None,
) -> StatusPair:
    """``fn-re-write``: open, 32 updates, close. Always reports success.

    The handler's rewrite block [common/acasirsub3.cbl:L494-L513] - the same
    three-call shape as the write, with its ``end-if.`` correctly matched at
    [:L513].

    A1, SECOND HALF: whatever the thirty-two updates did,
    ``ba090-Process-Rewrite`` clears ``FS-Reply``, ``WE-Error``, ``SQL-Err`` and
    ``SQL-Msg`` after its loop [common/irsdfltMT.cbl:L736-L738], so this returns
    ``(0, 0)`` unless the synthesised OPEN itself failed - the one failure this
    verb can still report, because it happens before the loop.

    A11. ON THE FLAT PATH THIS VERB DOES NOT EXIST as a distinct operation:
    ``when 5`` falls through to ``when 7`` and both reach
    ``aa070-Process-Write`` [:L210-L212], justified there as "write/rewrite can
    do the same ... as file is opened as output." On the RDB path they are
    distinct, both in the handler [:L468] [:L494] and in the bridge's own
    dispatch [common/irsdfltMT.cbl:L397-L401]. Verb identity is therefore
    PATH-DEPENDENT, and both behaviours are published as data in
    :data:`FLAT_PATH_DISPATCH` and :data:`RDB_PATH_DISPATCH`.

    Args:
        system: Supplies the credentials for the synthesised open.
        dflt: The 33-element linkage record to write out.
        file_access: Carries the reply.
        transport: TLS material for the connection, or ``None``.

    Returns:
        ``(0, 0)`` unless the synthesised open failed.
    """
    # `set fn-Open to true` / `set fn-I-O to true` [:L495-L496].
    file_access.file_function = int(_status.FileFunction.OPEN)
    file_access.access_type = int(_status.AccessType.I_O)
    connection, (fs_reply, we_error) = _ba020_process_open(
        system, file_access, transport=transport
    )
    if (
        fs_reply != int(_status.FsReply.SUCCESS)
        or we_error != int(_status.WeError.SUCCESS)
        or connection is None
    ):
        # `go to ba-rdbms-Exit` [:L498-L501]. Class 3 -> return.
        return fs_reply, we_error

    # `set fn-Re-write to true` / `perform ba020-Call-DAL` [:L502-L503], whose
    # trailing comment still reads "write" - copied from the block above.
    file_access.file_function = int(_status.FileFunction.RE_WRITE)
    fs_reply, we_error = _ba090_process_rewrite(connection, dflt, file_access)

    # A13. Save [:L504-L505], close unconditionally [:L506-L507], restore
    # [:L508-L509].
    saved_fs_reply, saved_we_error = fs_reply, we_error
    file_access.file_function = int(_status.FileFunction.CLOSE)
    _ba030_process_close(connection, file_access)
    _set_status(file_access, saved_fs_reply, saved_we_error)

    file_access.logging_data.ws_file_key = _KEY_OPEN_REWRITE_CLOSE  # [:L510]
    # THE OTHER `perform Ca-Process-Logs` SITES ARE A RECORDED OMISSION. The
    # frozen paragraph is `call "fhlogger" using File-Access ACAS-DAL-Common-data`
    # [common/acasirsub3.cbl:L534-L538], and this verb does not receive
    # `ACAS-DAL-Common-data` - inventing a route for it would change the module's
    # linkage, which R-3 forbids. :func:`ca_process_logs` is the ONE faithful
    # reproduction of the paragraph and is performed where the linkage allows it,
    # at the common exit in :func:`dispatch` [:L347-L350]. A hand-rolled record
    # here stood for the paragraph without its field set, without its level and
    # without advancing `Log-File-Rec-Written`, which is the incoherence OBS-010
    # names; the omission is listed in `docs/migration/traceability.md`.
    # `go to ba-RDBMS-Exit` [:L512]. Class 3 -> return.
    return saved_fs_reply, saved_we_error


# ---------------------------------------------------------------------------
#  THE ENTRY POINT
# ---------------------------------------------------------------------------


def dispatch(
    system: SystemRecord,
    dflt: WsIrsDefaultRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    *,
    transport: _connection.TransportSecurity | None = None,
) -> StatusPair:
    """Enter the handler, exactly as ``CALL "acasirsub3"`` does.

    THE PARAMETER ORDER IS THE LINKAGE ORDER and is not negotiable
    [common/acasirsub3.cbl:L151-L157]::

        Procedure Division Using System-Record
                                 WS-IRS-Default-Record
                                 File-Access
                                 File-Defs
                                 ACAS-DAL-Common-data.

    which Agent Action Plan section 0.4.3 fixes as the transformation contract::

        FROM:  call "acas007" using System-Record WS-Batch-Record File-Access
                                    File-Defs ACAS-DAL-Common-Data
        TO:    acas007_gl_batch.dispatch(system, batch, file_access, file_defs,
                                         dal_common)

    The IRS facade issues exactly this call, having first set ``File-Key-No`` to
    1 [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L59-L65].

    NO RECOVERY IS PERFORMED HERE. [common/acasirsub3.cbl:L528]: "Any errors
    leave it to caller to recover from". The status pair is returned as it
    stands, and no exception is raised - the hard return on an unrecoverable
    open belongs to the facade's ``goback``
    [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L364], reached through
    ``irsub3-Check-4-Errors`` [:L341-L346], which is the facade's
    responsibility and not this module's.

    Args:
        system: ``System-Record``. Selects the path and supplies credentials.
        dflt: ``WS-IRS-Default-Record`` - the 33-element array.
        file_access: ``File-Access``. Carries the function code in and the
            status out.
        file_defs: ``File-Defs``. Its only relevance to this handler is
            ``file_35``, the flat file name ``irsdflt.dat``
            [common/acasirsub3.cbl:L103-L106], and the flat record path is a
            documented omission - so the parameter is present to preserve the
            linkage order and is deliberately not otherwise consulted.
        dal_common: ``ACAS-DAL-Common-data``. ``sw_testing`` is the frozen
            ``Testing-1`` switch that gates the logging hooks
            [copybooks/Test-Data-Flags.cob], honoured below.
        transport: TLS material for the synthesised connections. Keyword-only
            and placed after the five positional parameters so the linkage order
            is untouched. It exists because a caller reaching an isolated oracle
            must say so explicitly rather than have it assumed.

    Returns:
        ``(fs_reply, we_error)``, also written into ``file_access``.
    """
    logging_data = file_access.logging_data

    # `move 1 to WS-Log-System` [:L166] and `move 12 to WS-Log-File-No` [:L167].
    logging_data.ws_log_system = WS_LOG_SYSTEM
    logging_data.ws_log_file_no = WS_LOG_FILE_NO_FLAT

    # `if not FS-Cobol-Files-Used` [:L180] selects the RDB path. The 88-level
    # predicates live in `cobol/condition_names.py`, which `dal/*` may not import
    # (section 0.4.3), so the condition is evaluated locally against its own
    # locator: `FS-Cobol-Files-Used value zero`
    # [copybooks/wssystem.cob:L112-L113]. `status.py` localises `_pic_x` for the
    # same layering reason.
    file_system_used = int(
        system.system_data_block.rdbms_flat_statuses.file_system_used
    )
    rdb_path = file_system_used != 0

    if rdb_path:
        # `move RDBMS-Flat-Statuses to FA-RDBMS-Flat-Statuses`
        # [common/acasirsub3.cbl:L181], noted
        # "needed for DAL? not JC/dbpre versions", then
        # `perform ba-Process-RDBMS` [:L182] and `go to AA-Main-Exit` [:L183].
        file_access.fa_rdbms_flat_statuses.fa_file_system_used = file_system_used
        file_access.fa_rdbms_flat_statuses.fa_file_duplicates_in_use = int(
            system.system_data_block.rdbms_flat_statuses.file_duplicates_in_use
        )
        # `move 22 to WS-Log-File-no` [common/acasirsub3.cbl:L372]. The bump lives in
        # `ba010-Test-WS-Rec-Size`, which holds ONLY the bump and is reached by
        # fall-through, so it happens on THIS PATH ALONE - the flat path
        # performs `ba012` directly [common/acasirsub3.cbl:L188] and keeps 12.
        logging_data.ws_log_file_no = WS_LOG_FILE_NO_RDB

    # `move zero to WE-Error` [:L196], whose comment reads "as in irsub3" - the
    # program referring to ITSELF by a shortened name, exactly as `acasirsub1`
    # calls itself `irsub1`. Then `move spaces to SQL-Err SQL-Msg SQL-State`
    # [:L197] - THREE fields, cleared with SPACES, where the bridge clears
    # `SQL-Err` with the character zero [common/irsdfltMT.cbl:L623] [:L737].
    file_access.we_error = int(_status.WeError.SUCCESS)
    logging_data.sql_err = _SQL_ERR_SPACES
    logging_data.sql_msg = _SQL_MSG_SPACES
    logging_data.sql_state = _SQL_STATE_SPACES

    # `perform ba012-Test-WS-Rec-Size-2` - [:L188] on the flat path and by
    # fall-through from `ba010` [:L366-L374] on the RDB path.
    gate_status = _ba012_test_ws_rec_size_2(system, file_access)
    if gate_status is not None:
        # `go to ba-rdbms-exit` [:L402] - THE BRIDGE IS NEVER CALLED. Class 3
        # section exit -> return.
        return gate_status

    function_code = int(file_access.file_function)

    # A11. The two dispatch tables differ on code 7, so the path is chosen
    # before the verb is.
    dispatch_table = RDB_PATH_DISPATCH if rdb_path else FLAT_PATH_DISPATCH
    verb = dispatch_table.get(function_code)

    if verb is None:
        # `when other` -> `aa100-Bad-Function` [:L213-L214] on the flat path,
        # and the second, textually distinct site [:L517-L519] on the RDB path
        # (A27). Both set the same codes, so both route here; the two locators
        # are recorded so they stay countable. `go to aa100-Bad-Function` at
        # [:L218] is a third textual route to the first site, guarded by
        # "Should never get here but Just in case :(".
        return _aa100_bad_function(file_access)

    if verb == "open":
        # A10 / A30. Codes 1 and 2 never reach the bridge on either path, and
        # bypass the logging hook. Flat: [:L200-L203]. RDB: [:L429-L432].
        return _no_op_open_or_close(file_access, is_close=False)
    if verb == "close":
        # Flat: [:L204-L207]. RDB: [:L433-L438].
        return _no_op_open_or_close(file_access, is_close=True)

    if not rdb_path:
        # DOCUMENTED OMISSION, STATED AT THE POINT IT BITES. On the flat path
        # the frozen handler reads and writes `irsdflt.dat` through
        # `Default-File` [:L103-L113] - `aa040-Process-Read-Next` [:L258-L310]
        # with its create-if-missing fallback [:L266-L273], and
        # `aa070-Process-Write` [:L312-L338]. This package's data-access layer
        # is SQL against the frozen schema and the target tree has no
        # flat-file module, so those record verbs are not reimplemented; what
        # IS reproduced is the dispatch shape, in `FLAT_PATH_DISPATCH`, because
        # that is where A11 lives. The migrated store is reached instead, which
        # is why the verb still runs below.
        logging_data.ws_no_paragraph = (
            _PARA_FLAT_READ if verb == "read_next" else _PARA_FLAT_WRITE
        )
        #  NO RECORD HERE. The frozen flat-path dispatch displays nothing, so a
        #  record was invented (R-4) - and it named `File-35`, an absolute filesystem
        #  path from the deployment's own configuration (CWE-532). The omission of the
        #  line-sequential path is documented in the comment above and in
        #  `docs/migration/traceability.md`.

    if verb == "read_next":
        status = read_next(system, dflt, file_access, transport=transport)
    elif verb == "write":
        status = write(system, dflt, file_access, transport=transport)
    else:
        # A11. Reached only on the RDB path: the flat table maps code 7 to
        # "write", so `rewrite` is unreachable through `FLAT_PATH_DISPATCH`.
        status = rewrite(system, dflt, file_access, transport=transport)

    # `aa999-main-exit. if Testing-1 perform Ca-Process-Logs` [:L347-L350].
    # `Testing-1` is `SW-Testing` in `copybooks/Test-Data-Flags.cob`, whose own
    # comment reads "set sw-testing to zero to stop logging" [:L149]. The hook
    # itself calls `fhlogger`, which is out of scope (R-1, section 0.2.2), so it
    # becomes a log record - and the switch is honoured so that the gating
    # structure survives even though the logger does not.
    if int(dal_common.sw_testing) != 0:
        ca_process_logs(file_access, dal_common)

    return status


def ca_process_logs(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``Ca-Process-Logs`` [common/acasirsub3.cbl:L534-L538].

    Two statements, ``call "fhlogger" using File-Access ACAS-DAL-Common-data``,
    followed by ``ca-Exit.     exit.``, under a label whose own comment reads
    ``*> Not called on DAL access as it does it already``.

    ``common/fhlogger.cbl`` is out of scope per Agent Action Plan section 0.2.2 and
    rule R-1 forbids calling a COBOL program, so the record it would have appended to
    its flat log is emitted through
    :func:`acas_posting.dal.status.log_file_handler_record` - THE ONE ADAPTER every
    handler in this package shares, at one level, with one field set. Before it, this
    module stood the paragraph up nine different times as nine hand-rolled records,
    each with its own fields and its own level and none of them advancing the
    counter, which is the incoherence OBS-010 names.

    ``WS-File-Key`` is WITHHELD: on this table it is ``DEF-REC-KEY``, and the
    safe-event schema admits no record key (CWE-532). So are ``WS-Log-Where`` and
    ``SQL-Msg``. ``Log-File-Rec-Written`` is advanced by one modulo a million - the
    range of the frozen ``pic 9(6)`` [copybooks/Test-Data-Flags.cob:L20] - once per
    record, by the adapter.

    Args:
        file_access: The block the record is built from.
        dal_common: The block carrying ``SW-Testing`` and the counter.
    """
    logging_data = file_access.logging_data
    _status.log_file_handler_record(
        _LOG,
        program=HANDLER,
        paragraph="Ca-Process-Logs",
        log_system=logging_data.ws_log_system,
        log_file_no=logging_data.ws_log_file_no,
        no_paragraph=logging_data.ws_no_paragraph,
        file_function=int(file_access.file_function),
        access_type=int(file_access.access_type),
        fs_reply=int(file_access.fs_reply),
        we_error=int(file_access.we_error),
        sql_err=logging_data.sql_err,
        sql_state=logging_data.sql_state,
        dal_common=dal_common,
    )



# ---------------------------------------------------------------------------
#  --- traceability ---
# ---------------------------------------------------------------------------
# Rule R-5: "Every program must map to a module, every paragraph to a function,
# and every field to a data-dictionary entry." The field mapping is in the module
# docstring and is resolved from the generated artifact at import; the paragraph
# mapping is below. Every line number was read from this checkout - see
# "PROVENANCE, AND CORRECTIONS TO THE CITED SPANS" for the three classes of
# correction that produced.
#
# HANDLER  -  common/acasirsub3.cbl (543 lines)
# ==============================================
#   L97-L98    environment division, copy "envdiv.cob"      omitted (no FD)
#   L103-L106  select Default-File ... line sequential      omitted: flat path
#   L111-L113  fd Default-File / 01 Record-3 pic x(264)     omitted (A25)
#   L118       77 prog-name "acasirsub3 (3.3.00)"           HANDLER
#   L121-L122  WS-Save-FS-Reply / WS-Save-WE-Error          locals in read_next,
#                                                           write, rewrite (A13)
#   L124-L125  77 A / 77 B                                  _ba012_test_ws_rec_size_2
#   L130-L137  IR901 IR902 IR917 IR918 IR919                omitted: presentation
#   L141-L149  copy ... replacing Default-Record            the imports (A29)
#   L151-L157  Procedure Division Using (5 params)          dispatch()
#   L166-L167  WS-Log-System 1 / WS-Log-File-No 12          dispatch()
#   L169-L176  the WARNING comment block                    quoted at the verbs
#   L180-L184  if not FS-Cobol-Files-Used                   dispatch()
#   L188       perform ba012 (flat path)                    dispatch()
#   L196-L197  clear WE-Error, SQL-Err/Msg/State            dispatch()
#   L199-L218  evaluate File-Function (5 codes)             FLAT_PATH_DISPATCH
#                                                           (A11, A30)
#   L220-L256  aa020-Process-Open / aa030-Process-Close     omitted: dead (A10)
#   L258-L310  aa040-Process-Read-Next (flat)               omitted: flat path
#   L312-L338  aa070-Process-Write (flat)                   omitted: flat path
#   L340-L345  aa100-Bad-Function (999/99)                  _aa100_bad_function
#   L347-L350  aa999-main-exit + Testing-1 hook             dispatch() tail
#   L352-L356  aa-main-exit / aa-Exit (exit program)        dispatch() return
#   L358       ba-Process-RDBMS section                     dispatch() RDB branch
#   L366-L372  ba010-Test-WS-Rec-Size (the 12->22 bump)     dispatch()
#   L374-L414  ba012-Test-WS-Rec-Size-2                     _ba012_test_ws_rec_size_2
#   L416       ba015-Test-Ends                              dispatch() + the verbs
#   L429-L432  if fn-open -> ignore                         _no_op_open_or_close
#   L433-L438  if fn-close -> ignore + close logger         _no_op_open_or_close
#   L440-L467  if fn-read-next (3 calls)                    read_next (A12, A13)
#   L468-L492  if fn-Write (3 calls + silent retry)         write (A1, A13, A14)
#   L494-L513  if fn-Re-write (3 calls)                     rewrite (A1, A13)
#   L517-L519  second bad-function site (999/99)            dispatch() (A27)
#   L521-L526  ba020-Call-DAL (4th naming variant, A28)     the _ba0* calls
#   L530-L531  ba-rdbms-exit / exit section                 the returns
#   L534-L538  Ca-Process-Logs -> call "fhlogger"           omitted: R-1 (A33)
#   L540       ca-Exit / exit                               n/a
#
# BRIDGE  -  common/irsdfltMT.cbl (916 lines)
# ============================================
#   L257-L258  WS-MYSQL-EDIT / WS-Key pic 99                _load_host_variables,
#                                                           read_next
#   L266-L275  Table-Of-Keynames + keyOfReference           KEY_OFFSET/LENGTH,
#                                                           dead (A15)
#   L282-L286  DAL-Data / Most-Cursor-Set + 88s             _cursor()
#   L291-L294  subscripts J K L                             dead K/L (A15)
#   L298-L310  work-fields / ws-saved-fs-reply / A          _ba070_process_write
#   L313       SM901                                        omitted: presentation
#   L315-L328  /MYSQL VAR\ + TD-IRSDFLT-REC (4 HVs)         COLUMNS,
#                                                           _load_host_variables
#   L340       copy "irswsdflt.cob" (no replacing)          the import (A29)
#   L342-L357  screen section                               omitted: presentation
#   L360-L362  PROCEDURE DIVISION using (3 params)          the _ba0* signatures
#   L364-L365  section head + accept ws-env-lines           omitted: presentation
#   L375-L383  ba010-Initialise                             _ba020_process_open,
#                                                           dispatch()
#   L392-L405  evaluate (5 codes, 5 and 7 DISTINCT)         RDB_PATH_DISPATCH (A11)
#   L407-L453  ba020-Process-Open (connect, cursor reset)   _ba020_process_open
#   L455-L468  ba030-Process-Close (free + disconnect)      _ba030_process_close
#   L470-L615  ba040-Process-Read-Next                      _ba040_process_read_next
#   L617-L671  ba070-Process-Write (32 inserts)             _ba070_process_write
#   L673-L739  ba090-Process-Rewrite (32 updates + reset)   _ba090_process_rewrite
#   L741-L747  ba100-Bad-Function (990/99)                  _ba100_bad_function (A26)
#   L751       COPY "mysql-procedures.cpy" (dead ladder)    omitted: unreachable
#   L753-L763  ba998-Free                                   _ba998_free
#   L765-L769  ba999-end + Testing-1 hook                   the returns
#   L771-L772  ba999-exit / exit program                    the returns
#   L774-L837  bb200-Insert Section (SET form)              _INSERT_STATEMENT,
#                                                           _execute_one
#   L839-L906  bb300-Update Section (PK re-SET)             _UPDATE_STATEMENT,
#                                                           _execute_one
#   L908-L912  Ca-Process-Logs -> call "fhlogger"           omitted: R-1
#
# `GO TO` CLASSES  -  the four-class taxonomy of section 0.4.2, per site
# ======================================================================
# CLASS 1, loop-back -> `continue`:
#   NONE. Neither program contains a loop-back `GO TO`; both loops are
#   `perform varying ... until`, and the only in-loop transfers are
#   `exit perform`. This module therefore has no `continue`, which is itself
#   worth recording: the absence is a fact about the source, not an omission.
#
# CLASS 2, forward terminator -> `break` PLUS the post-loop work. Four sites,
# all in the read loop, and THE POST-LOOP WORK DIFFERS AT EACH, which is why
# they are transformed individually rather than by pattern:
#   * [common/irsdfltMT.cbl:L571]  `exit perform` after the EOF branch. Post-loop
#     work: none but the commented-out reset [:L613-L614] - so the (10, 10) it
#     just set is what the caller receives (A7).
#   * [:L582]  `exit perform` after the key-above-32 guard. Post-loop work: none;
#     `WE-Error` carries the KEY VALUE and `FS-Reply` was never set (A3).
#   * [:L601]  `exit perform` after the count-rows probe. Post-loop work: none;
#     a real SQL error leaves (10, 10) (A32).
#   * [:L611]  the loop's own normal exit at `end-perform`. Post-loop work: none;
#     the status is whatever the last iteration left, which for a full
#     thirty-two rows is the (0, 0) the handler set at
#     [common/acasirsub3.cbl:L441].
#   Also CLASS 2 in the write loop: `exit perform cycle`
#   [common/irsdfltMT.cbl:L630], inside the
#   COMMENTED-OUT empty-slot skip - a Class 2 transfer that cannot execute (A8).
#
# CLASS 3, section or paragraph exit -> `return`. Every `go to ba999-exit`
#   [:L615] [:L671] [:L739], `go to ba999-end` [:L443] [:L453] [:L468] [:L747],
#   `go to ba-rdbms-Exit` [common/acasirsub3.cbl:L431] [:L437] [:L449] [:L458]
#   [:L466] [:L474] [:L491] [:L500] [:L512] [:L519], `go to aa-Exit` [:L203]
#   [:L207], `go to AA-Main-Exit` [:L183] and `go to ba-rdbms-exit` [:L402].
#   All unconditionally safe: a forward transfer to a trailing exit label skips
#   no code that would otherwise run.
#
# CLASS 4, sibling re-dispatch -> named call PLUS an explicit control statement.
# TWO sites, each proved individually as the class requires:
#   * [common/acasirsub3.cbl:L488-L492]  `set fn-Re-write to true` followed by
#     fall-through into `if fn-Re-write` [:L494]. THE ONLY TRUE SIBLING
#     RE-DISPATCH IN EITHER FILE, and reachable only because of A14's single
#     `end-if.`. Transformed as `return rewrite(...)` at the end of `write`, and
#     the equivalence is proved in `write`'s docstring: the period closes the
#     outer `if fn-Write`, so the `else go to ba-RDBMS-Exit` [:L490-L491] binds
#     to the inner status test, making success return and failure fall through.
#   * [common/irsdfltMT.cbl:L534]  `go to ba998-Free` from the empty-table probe.
#     The target frees the cursor [:L753-L763] and falls into `ba999-end`
#     [:L765], so the equivalent is `_ba998_free(...)` followed by an explicit
#     `return` - which is what `_ba040_process_read_next` does. Proof that no
#     code is skipped: between the `go to` and `ba998-Free` lie only
#     `move 1 to Most-Cursor-Set` [:L536] and the fetch loop, both of which the
#     transfer is precisely intended to bypass, and `ba999-end`'s own body is
#     the `Testing-1` logging hook [:L766-L768], which is a documented omission.
#
# THE THIRTY-FOUR ANOMALIES, AND WHERE EACH IS REPRODUCED
# =======================================================
#   A1  write failure always reports success   write, _ba090_process_rewrite
#   A2  33 declared, 32 handled                OCCURS vs BRIDGE_LIMIT
#   A3  key > 32 puts the VALUE in WE-Error    _ba040_process_read_next
#   A4  DEF-REC-KEY has no copybook field      _load_host_variables, _KEY_ENTRY
#   A5  32 statements + synthesised open/close read_next, write, rewrite
#   A6  unbounded array subscript              _unload_row_into
#   A7  post-read status reset commented out   _ba040_process_read_next tail
#   A8  empty-slot skip commented out          _ba070_process_write,
#                                              _ba090_process_rewrite
#   A9  write failures squashed                _ba070_process_write
#   A10 open and close are no-ops              _no_op_open_or_close, open_*, close
#   A11 verb identity is path-dependent        FLAT_/RDB_PATH_DISPATCH, rewrite
#   A12 read skips its close, write does not   read_next
#   A13 the close's status is discarded        _ba030_process_close and callers
#   A14 one end-if. closes two nested ifs      write (the Class 4 proof)
#   A15 key metadata indexes a missing field   KEY_OFFSET/LENGTH and both loops
#   A16 relation hard-coded, literal "000"     READ_RELATION, READ_KEY_LITERAL
#   A17 the only explicit ORDER BY             ORDER_BY_CLAUSE
#   A18 WE-Error 994 unobservable              _ba090_process_rewrite
#   A19 write sets FS-Reply only               _ba070_process_write
#   A20 duplicate test - CORRECTED             _is_duplicate_key
#   A21 errno padding - CORRECTED, no effect   _errno_is_zero
#   A22 WS-File-Key cannot hold the bad row    both write loops
#   A23 initialise once, and absent in rewrite _ba070_process_write vs rewrite
#   A24 no HV-Load, no Unload, no DELETE       _unsupported_verb, the inline loads
#   A25 the FD record is a flat byte blob      docstring: CONVENTION DRIFT
#   A26 handler 999 vs bridge 990              HANDLER_/BRIDGE_BAD_FUNCTION
#   A27 a second bad-function site             dispatch()
#   A28 ba020-Call-DAL, 4th naming variant     docstring: CONVENTION DRIFT
#   A29 handler/bridge record-name mismatch    docstring: CONVENTION DRIFT
#   A30 codes 1 and 2 bypass the log hook      _no_op_open_or_close
#   A31 `or A > 32 or = zero` is dead          _ba040_process_read_next
#   A32 a real SQL error reported as EOF       _ba040_process_read_next
#   A33 self-contradicting log comments        docstring: CONVENTION DRIFT
#   A34 IR9xx gaps and spelling drift          docstring: CONVENTION DRIFT,
#                                              _ba012_test_ws_rec_size_2
#
# The last five carry no executable site because they are facts about how the
# frozen source is written rather than about what it does; each is inventoried
# with its locator in the docstring section named above, which is where rule R-5
# requires such a record to live.
