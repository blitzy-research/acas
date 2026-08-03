"""`acasirsub3` and its bridge `irsdfltMT` - the `IRSDFLT-REC` IRS defaults table.

The data-access module for the IRS defaults entity, reached through the
handler-named facade aliases the IRS convention uses.

The array holds 33 entries. The bridge only ever handles 32. Both facts are
declared separately, as :data:`OCCURS` and :data:`BRIDGE_LIMIT`, so that the gap
cannot be closed by accident - see anomaly **A2**.

WHAT THIS MODULE OWNS
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
Two questions this module cannot settle from the source are marked
``TODO(oracle)`` against section 0.6.8 rather than guessed.
=======
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

# The pinned driver, imported ONLY for its exception type. THAN QUIET.
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
    "READ_RELATION",
    "READ_KEY_LITERAL",
    "ORDER_BY_CLAUSE",
    "KEY_OFFSET",
    "KEY_LENGTH",
    "KEY_METADATA_TYPE",
    "HANDLER_BAD_FUNCTION",
    "BRIDGE_BAD_FUNCTION",
    "RECORD_SIZE_MISMATCH_WE_ERROR",
    "REWRITE_UNOBSERVABLE_WE_ERROR",
    "WS_LOG_SYSTEM",
    "WS_LOG_FILE_NO_FLAT",
    "WS_LOG_FILE_NO_RDB",
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

#: The status pair every verb returns and writes back into ``File-Access``. COBOL
#: returns through the linkage record.
StatusPair = tuple[int, int]


TABLE: Final[str] = "IRSDFLT-REC"

HANDLER: Final[str] = "acasirsub3"

BRIDGE: Final[str] = "irsdfltMT"

ENTITY_FACADE: Final[str] = "IRS defaults"

PRIMARY_KEY: Final[str] = "DEF-REC-KEY"

COLUMNS: Final[tuple[str, ...]] = (
    "DEF-REC-KEY",
    "DEF-ACS",
    "DEF-CODES",
    "DEF-VAT",
)

# They disagree, and the disagreement is the defect.

OCCURS: Final[int] = 33

#: What the bridge actually handles: 32.
BRIDGE_LIMIT: Final[int] = 32

#: Record length in bytes, both sides of the record-size gate.
RECORD_LENGTH_BYTES: Final[int] = 264

#: The dictionary key for each column, in schema order. Rule R-5: every field is
#: resolved through the dictionary rather than transcribed.
DICTIONARY_KEYS: Final[tuple[str, ...]] = tuple(
    f"{TABLE}.{column}" for column in COLUMNS
)


# A16. The relation is HARD-CODED and the key value is a QUOTED STRING LITERAL.

READ_RELATION: Final[str] = ">"

READ_KEY_LITERAL: Final[str] = "000"

# A15. DEAD KEY METADATA - COMPUTED BY THE BRIDGE AND NEVER USED.

KEY_OFFSET: Final[int] = 1

KEY_LENGTH: Final[int] = 1

KEY_METADATA_TYPE: Final[str] = "STR"

# Built through the package's own `OrderTerm` so the quoting is the shared
# implementation rather than a local f-string, and asserted below against the echo the
# bridge itself leaves at [common/irsdfltMT.cbl:L499].
_ORDER_TERM: Final[_cursor_state.OrderTerm] = _cursor_state.OrderTerm(
    column_name=PRIMARY_KEY,
    direction="ASC",
    quoting=_cursor_state.OrderQuoting.IDENTIFIER,
    source_locator="[common/irsdfltMT.cbl:L488-L492]",
)

#: ``ORDER BY `DEF-REC-KEY` ASC`` [common/irsdfltMT.cbl:L488-L492]. Preserved verbatim.
ORDER_BY_CLAUSE: Final[str] = f"ORDER BY {_ORDER_TERM.to_sql()}"


# DISAGREEMENT IS NOT RECONCILED. `aa100-Bad-Function` moves 999
# [common/acasirsub3.cbl:L340-L345]; `ba100-Bad-Function` moves 990
# [common/irsdfltMT.cbl:L741-L747].

HANDLER_BAD_FUNCTION: Final[int] = int(_status.WeError.NOT_USED)

#: ``ba100-Bad-Function`` [common/irsdfltMT.cbl:L743]. Never surfaced to a caller,
#: because the handler filters the function code first.
BRIDGE_BAD_FUNCTION: Final[int] = int(_status.WeError.UNKNOWN_UNEXPECTED)

RECORD_SIZE_MISMATCH_WE_ERROR: Final[int] = int(
    _status.WeError.RECORD_SIZE_MISMATCH
)

# A18. `WE-Error 994` IS PERMANENTLY UNOBSERVABLE. Set inside the rewrite's error branch
# [common/irsdfltMT.cbl:L728], then cleared unconditionally after the loop [:L736].
REWRITE_UNOBSERVABLE_WE_ERROR: Final[int] = int(
    _status.WeError.REWRITE_SQLSTATE_NOT_00000
)

# A10 / DELIBERATE OMISSION. Codes reachable only from the commented-out flat open,
# declared so the omission is visible and never executed.
_DEAD_FLAT_ACCESS_TYPE_WRONG: Final[int] = int(_status.WeError.ACCESS_TYPE_WRONG)
_DEAD_FLAT_OPEN_FAILED: Final[int] = 1

# A20 - CORRECTED. The duplicate test consults BOTH the error number and the SQLSTATE
# [common/irsdfltMT.cbl:L651-L653].
_DUPLICATE_KEY_ERRNOS: Final[tuple[str, ...]] = ("1062", "1022")
_DUPLICATE_KEY_SQLSTATE: Final[str] = "23000"

_SQL_ERR_COMPARE_WIDTH: Final[int] = 4


WS_LOG_SYSTEM: Final[int] = int(_status.LogSystem.IRS)

WS_LOG_FILE_NO_FLAT: Final[int] = 12

WS_LOG_FILE_NO_RDB: Final[int] = 22

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

# A11. VERB IDENTITY IS PATH-DEPENDENT, WHICH NO SHARED MAPPING COULD EXPRESS.

#: The flat-path ``evaluate`` [common/acasirsub3.cbl:L199-L215], as frozen data.
#: ``FileFunction.WRITE`` and ``FileFunction.RE_WRITE`` both name ``"write"`` - that
#: identity is anomaly A11.
FLAT_PATH_DISPATCH: Final[Mapping[int, str]] = {
    int(_status.FileFunction.OPEN): "open",
    int(_status.FileFunction.CLOSE): "close",
    int(_status.FileFunction.READ_NEXT): "read_next",
    int(_status.FileFunction.WRITE): "write",
    int(_status.FileFunction.RE_WRITE): "write",
}

RDB_PATH_DISPATCH: Final[Mapping[int, str]] = {
    int(_status.FileFunction.OPEN): "open",
    int(_status.FileFunction.CLOSE): "close",
    int(_status.FileFunction.READ_NEXT): "read_next",
    int(_status.FileFunction.WRITE): "write",
    int(_status.FileFunction.RE_WRITE): "rewrite",
}

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

# Every identifier passes through `quote_identifier` because every table and column name
# in this schema is hyphenated and a syntax error unquoted.
_QUOTED_TABLE: Final[str] = _connection.quote_identifier(TABLE)
_QUOTED_KEY: Final[str] = _connection.quote_identifier(PRIMARY_KEY)
_QUOTED_COLUMNS: Final[tuple[str, ...]] = tuple(
    _connection.quote_identifier(column) for column in COLUMNS
)

#: The frozen statement is assembled in two halves.
_SELECT_STATEMENT: Final[str] = (
    f"SELECT * FROM {_QUOTED_TABLE} "
    f"WHERE {_QUOTED_KEY} {READ_RELATION} %s {ORDER_BY_CLAUSE}"
)

_FROZEN_SELECT_ECHO: Final[str] = (
    f'{PRIMARY_KEY} {READ_RELATION} "{READ_KEY_LITERAL}" '
    f"ORDER BY {PRIMARY_KEY} ASC"
)


#: ``INSERT INTO `IRSDFLT-REC` SET ...`` [common/irsdfltMT.cbl:L784-L831]. The ``SET``
#: form rather than ``VALUES`` is what the JC preSQL translator emitted.
_INSERT_STATEMENT: Final[str] = "INSERT INTO {table} SET {assignments}".format(
    table=_QUOTED_TABLE,
    assignments=", ".join(f"{column} = %s" for column in _QUOTED_COLUMNS),
)

#: [common/irsdfltMT.cbl:L849-L899]. ``.scb`` settles whose choice that was: the
#: directive carries only ``TABLE=`` and ``WHERE=`` [common/irsdfltMT.scb:L747-L750], so
#: the translator generated all four assignments including the key.
_UPDATE_STATEMENT: Final[str] = (
    "UPDATE {table} SET {assignments} WHERE {key} = %s".format(
        table=_QUOTED_TABLE,
        assignments=", ".join(f"{column} = %s" for column in _QUOTED_COLUMNS),
        key=_QUOTED_KEY,
    )
)


# "Data dictionary first. ... every Python field definition cites its entry.


def _character_width(dictionary_key: str) -> int:
    """Return the host variable's character width for a text column.

    Args:
        dictionary_key: A key from :data:`DICTIONARY_KEYS`.

    Returns:
        The declared character length of the host variable.

    Raises:
        ValueError: If the dictionary has no host variable for the key, or declares no
            character length for it.
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

    Args:
        dictionary_key: A key from :data:`DICTIONARY_KEYS`.

    Returns:
        The declared digit count of the host variable.

    Raises:
        ValueError: If the dictionary declares no host variable or no digit count for
            the key.
    """
    host_variable = _loader.host_variable_for(dictionary_key)
    if host_variable is None or not host_variable.digits:
        raise ValueError(
            f"{dictionary_key}: the data dictionary declares no host-variable "
            f"digit count - see {_loader.cite(dictionary_key)}"
        )
    return host_variable.digits


# A4. THE PRIMARY KEY HAS NO COPYBOOK FIELD, AND THE DICTIONARY SAYS SO. Asserted from
# the artifact rather than asserted in prose.
_KEY_ENTRY: Final = _loader.get_entry(f"{TABLE}.{PRIMARY_KEY}")
_KEY_DERIVATION: Final = _loader.derivation_for(f"{TABLE}.{PRIMARY_KEY}")

if _loader.copybook_field_for(f"{TABLE}.{PRIMARY_KEY}") is not None:
    raise ValueError(
        f"{TABLE}.{PRIMARY_KEY} is declared by a copybook in the generated "
        "data dictionary, contradicting [copybooks/irswsdflt.cob:L8-L12] and "
        "the bridge-only derivation this module reproduces "
        "[common/irsdfltMT.cbl:L637-L639]"
    )

_KEY_HOST_VARIABLE: Final = _loader.host_variable_for(f"{TABLE}.{PRIMARY_KEY}")

_DEF_ACS_DIGITS: Final[int] = _numeric_digits(f"{TABLE}.DEF-ACS")

_DEF_CODES_WIDTH: Final[int] = _character_width(f"{TABLE}.DEF-CODES")
_DEF_VAT_WIDTH: Final[int] = _character_width(f"{TABLE}.DEF-VAT")

#: The modulus the ``MOVE`` into ``HV-DEF-ACS`` truncates by. A COBOL ``MOVE`` into a
#: shorter numeric picture discards high-order digits.
_DEF_ACS_MODULUS: Final[int] = 10**_DEF_ACS_DIGITS

# The USAGE drift, read from the artifact rather than restated.
_DEF_ACS_DRIFT: Final = _loader.drift_for(f"{TABLE}.DEF-ACS")


def _truncate_trailing(value: str) -> str:
    """Apply ``FUNCTION TRIM(<hv>, TRAILING)`` to a character host variable.

    The bridge trims trailing spaces off both character host variables as it builds the
    statement text - ``INSERT`` at [common/irsdfltMT.cbl:L810-L825] and ``UPDATE`` at
    [:L875-L890] - so an all-blank ``DEF-VAT`` reaches the server as the EMPTY STRING
    rather than as a space.

    Args:
        value: The host variable's contents.

    Returns:
        ``value`` with trailing spaces removed.
    """
    return value.rstrip(" ")


def _pad_to(value: str, width: int) -> str:
    """Land a fetched character value in a fixed-width ``PIC X(n)``.

    Args:
        value: The fetched value.
        width: The host variable's declared width.

    Returns:
        ``value`` padded or truncated to exactly ``width`` characters.
    """
    return value[:width].ljust(width)


def _is_numeric_class(value: object) -> bool:
    """Reproduce the COBOL ``numeric`` class test on ``Def-Acs``.

    The frozen guard is ``if Def-Acs (A) numeric`` [common/irsdfltMT.cbl:L632] on the
    write and [:L684] on the rewrite, with ``move zeros to HV-DEF-ACS`` as the else
    [:L635] [:L687].

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
    [common/irsdfltMT.cbl:L632-L641] and the rewrite's near-identical copy [:L684-L693].

    Args:
        dflt: The 33-element linkage record.
        index: The one-based ``OCCURS`` subscript, ``A`` in the frozen loops.

    Returns:
        The four host-variable values in :data:`COLUMNS` order, ready to bind.
    """
    group = dflt.def_group[index - 1]

    # A4. `DEF-REC-KEY` COMES FROM THE SUBSCRIPT, NOT FROM THE RECORD. `move A to WS-
    # Key` then `move WS-Key to HV-DEF-REC-KEY` [common/irsdfltMT.cbl:L637] [:L639].
    hv_def_rec_key = index

    if _is_numeric_class(group.def_acs):
        hv_def_acs = Decimal(int(group.def_acs) % _DEF_ACS_MODULUS)
    else:
        hv_def_acs = Decimal(0)

    # `move Def-Vat (A) to HV-DEF-VAT` [common/irsdfltMT.cbl:L640] and `move Def-Codes
    # (A) to HV-DEF-CODES` [:L641] - declared in that order in the source, VAT before
    # CODES, though the statement binds them in schema order.
    hv_def_codes = _truncate_trailing(_pad_to(group.def_codes, _DEF_CODES_WIDTH))
    hv_def_vat = _truncate_trailing(_pad_to(group.def_vat, _DEF_VAT_WIDTH))

    return hv_def_rec_key, hv_def_acs, hv_def_codes, hv_def_vat


def _unload_row_into(dflt: WsIrsDefaultRecord, row: Mapping[str, object]) -> int:
    """Unload one fetched row into the array slot its own key selects.

    A6. THE SUBSCRIPT IS THE DATABASE VALUE, AND IT IS NOT BOUNDS-CHECKED. The frozen
    moves index a 33-element array with ``HV-DEF-REC-KEY`` - a value read from the
    database - under the comment "KEY = table position" [common/irsdfltMT.cbl:L603].

    Args:
        dflt: The 33-element linkage record.
        row: One fetched row, keyed by column name.

    Returns:
        The key the row was filed under - ``WS-Key`` at [common/irsdfltMT.cbl:L606].
    """
    # `MySQL_fetch_record` binds positionally into the host-variable group
    # [common/irsdfltMT.cbl:L552-L560].
    hv_def_rec_key = int(row[PRIMARY_KEY])

    # The column is `decimal(5,0)` [mysql/ACASDB.sql:L191] so the pinned converter
    # yields a `Decimal`.
    hv_def_acs = int(Decimal(str(row["DEF-ACS"])))
    hv_def_codes = _pad_to(str(row["DEF-CODES"]), _DEF_CODES_WIDTH)
    hv_def_vat = _pad_to(str(row["DEF-VAT"]), _DEF_VAT_WIDTH)

    # A6. The raw database value is the subscript.
    group = dflt.def_group[hv_def_rec_key - 1]
    group.def_acs = hv_def_acs
    group.def_vat = hv_def_vat
    group.def_codes = hv_def_codes

    return hv_def_rec_key


def _clear_all_slots(dflt: WsIrsDefaultRecord) -> None:
    """Reproduce ``initialize Default-Record with filler``.

    [common/irsdfltMT.cbl:L543], immediately before the read's fetch loop. All THIRTY-
    THREE groups are zeroed and blanked, not just the thirty-two the loop can fill,
    because the verb names the whole record.

    Args:
        dflt: The 33-element linkage record.
    """
    # OCCURS, not BRIDGE_LIMIT. This is the one place the full array length is correct,
    # because `initialize` names the record rather than a loop bound.
    for index in range(OCCURS):
        group = dflt.def_group[index]
        group.def_acs = 0
        group.def_codes = " " * _DEF_CODES_WIDTH
        group.def_vat = " " * _DEF_VAT_WIDTH


#: ``Ws-Mysql-Error-Number`` is ``pic x(5)`` [copybooks/mysql-variables.cpy:L84] -
#: "changed to 5 char 18/09/16", per the comment there. THE WIDTH IS WHY A21 HAS NO
#: EFFECT.
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

    A21 - MEASURED, AND CORRECTED. The frozen source compares this field against a zero
    literal at four sites, and the padding is not uniform: three spaces at
    [common/irsdfltMT.cbl:L526], [:L589] and [:L647], four spaces at [:L723].

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

    Args:
        error: The driver error, or ``None`` if the statement itself succeeded and only
            the affected-row count was unexpected - which is the case the frozen
            source's ``count-rows not = 1`` test also admits.
        file_access: Receives ``SQL-State`` now and ``SQL-Err``/``SQL-Msg`` if the
            number is non-zero.

    Returns:
        The triple ``(errno_text, message, sql_state)``.
    """
    logging_data = file_access.logging_data

    # `call "MySQL_errno"` / `call "MySQL_sqlstate"`. Text, not an integer, because `Ws-
    # Mysql-Error-Number` is `pic x(5)` and the duplicate test compares it as characters
    # [common/irsdfltMT.cbl:L651].
    if error is None:
        errno_text = "0"
        message = ""
        sql_state = ""
    else:
        errno = getattr(error, "errno", None)
        errno_text = str(errno) if errno else "0"
        message = str(getattr(error, "msg", None) or error)
        sql_state = str(getattr(error, "sqlstate", None) or "")

    logging_data.sql_state = sql_state[: _status.SQL_STATE_WIDTH]

    if not _errno_is_zero(errno_text):
        logging_data.sql_err = errno_text[: _status.SQL_ERR_WIDTH]
        logging_data.sql_msg = message[: _status.SQL_MSG_WIDTH]

    return errno_text, message, sql_state


def _is_duplicate_key(errno_text: str, sql_state: str) -> bool:
    """Reproduce this bridge's duplicate-key test.

    Because the rule matches, the package's shared helper is used rather than a local
    reimplementation, and the equivalence against this bridge's own literals is checked
    below rather than asserted in prose.

    Args:
        errno_text: The driver's error number as text.
        sql_state: The driver's SQLSTATE.

    Returns:
        ``True`` if the frozen test would treat this as a duplicate key.
    """
    shared_verdict = _status.is_duplicate_key_bridge_level(errno_text, sql_state)

    # This bridge's own literals, evaluated directly.
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

    Args:
        connection: An open connection from :func:`_ba020_process_open`.
        statement: One statement, identifiers already quoted.
        parameters: The values to bind, in the statement's order.

    Returns:
        ``(affected_rows, error)``. A raised driver error is reported as zero affected
            rows, which is what the frozen source's count-rows test sees after a failed
            ``MySQL_query``.
    """
    try:
        with _connection.execute_statement(connection, statement, parameters) as cursor:
            affected = cursor.rowcount
    except DriverError as error:
        return 0, error
    return max(affected, 0), None


def _execute_select(
    connection: object, statement: str, parameters: Sequence[object]
) -> tuple[tuple[Mapping[str, object], ...], DriverError | None]:
    """Issue the read's ``SELECT`` and materialise its result.

    The Python analogue of [common/irsdfltMT.cbl:L505-L513]: build the command, ``MOVE
    WS-MYSQL-RESULT TO TP-IRSDFLT-REC``. ``store-result`` materialises the whole result
    server-side-to-client before the fetch loop walks it, which is why the rows are
    collected here rather than streamed.

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


# THE RECORD-SIZE GATE - `ba012-Test-WS-Rec-Size-2` The handler's `A` is `77 A pic 9(4)`
# [common/acasirsub3.cbl:L124], default zero, and the whole paragraph body is wrapped in
# `if A = zero` [:L376] ...

_GATE_HAS_RUN: bool = False


def reset_record_size_gate() -> None:
    """Re-arm the once-only record-size gate."""
    global _GATE_HAS_RUN
    _GATE_HAS_RUN = False


def _ba012_test_ws_rec_size_2(
    system: SystemRecord, file_access: FileAccess
) -> StatusPair | None:
    """Compare the linkage record against the file record, once per process.

    ``ba012-Test-WS-Rec-Size-2`` [common/acasirsub3.cbl:L374-L414]. On the first call it
    measures both records and, if the linkage record is SHORTER than the file record,
    sets ``(99, 901)``, shows ``IR902``/``IR901``, waits for a keypress and transfers to
    ``ba-rdbms-exit`` WITHOUT CALLING THE BRIDGE [:L383-L402].

    Args:
        system: The system record carrying the RDBMS credentials.
        file_access: Receives the status on failure.

    Returns:
        ``(99, 901)`` if the gate rejects the record, otherwise ``None`` to mean "fall
            through and carry on".
    """
    global _GATE_HAS_RUN

    if _GATE_HAS_RUN:
        # `if A = zero` is false on every later call, so the whole body - including the
        # credential load - is skipped [common/acasirsub3.cbl:L376] [:L414].
        return None

    linkage_record_length = OCCURS * (
        _DEF_ACS_DIGITS + _DEF_CODES_WIDTH + _DEF_VAT_WIDTH
    )
    file_record_length = RECORD_LENGTH_BYTES

    _GATE_HAS_RUN = True

    if linkage_record_length < file_record_length:
        # `move 901 to WE-Error` / `move 99 to fs-reply` [:L384-L385], then IR902 with
        # the record number, IR901, an `accept`, and `go to ba-rdbms-exit` [:L387-L402]
        # - the bridge is never called.
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

    rdb_data = _connection.load_rdb_data_once(system)
    file_access.rdb_data = rdb_data
    return None


# These correspond to `irsdfltMT`'s OWN open and close, which the handler synthesises
# around every read, write and rewrite (A5).

#: Cursor state for this table, at module scope so that the read's skipped close (A12)
#: leaks a cursor across calls exactly as the frozen bridge's working storage does.
_CURSOR_STATES: Final[_cursor_state.CursorStateTable] = (
    _cursor_state.CursorStateTable()
)


def _cursor() -> _cursor_state.CursorState:
    """Return this table's single cursor slot.

    Returns:
        The primary cursor state for :data:`TABLE`.
    """
    return _CURSOR_STATES.state_for(TABLE, _cursor_state.CursorSlot.PRIMARY)


def _ba998_free(file_access: FileAccess) -> None:
    """Free the stored result and mark the cursor inactive.

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

    Args:
        system: Supplies the credentials.
        file_access: Receives the trace number, key text and status.
        transport: TLS material for the connection, or ``None``.

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
        return None, _set_status(
            file_access, int(outcome.fs_reply), int(outcome.we_error)
        )

    file_access.logging_data.ws_file_key = _KEY_OPEN
    _cursor().set_cursor_not_active()
    return outcome.connection, _set_status(
        file_access, int(_status.FsReply.SUCCESS), int(_status.WeError.SUCCESS)
    )


def _ba030_process_close(connection: object | None, file_access: FileAccess) -> None:
    """Disconnect, as ``ba030-Process-Close`` does.

    A13. THIS PARAGRAPH'S STATUS IS ALWAYS DISCARDED, so it returns nothing.

    Args:
        connection: The connection to close, or ``None`` if the open failed.
        file_access: Receives the trace number and key text.
    """
    if _cursor().cursor_active():
        _ba998_free(file_access)

    file_access.logging_data.ws_no_paragraph = _PARA_BRIDGE_CLOSE
    file_access.logging_data.ws_file_key = _KEY_CLOSE
    _connection.mysql_1980_close(connection)


def _ba100_bad_function(file_access: FileAccess) -> StatusPair:
    """The bridge's bad-function paragraph.

    A26. The handler's own bad-function paragraph sets 999 rather than 990
    [common/acasirsub3.cbl:L344], and the two are NOT reconciled. This paragraph is
    unreachable through :func:`dispatch`, which filters the function code before the
    bridge would see it.

    Args:
        file_access: Receives the status.

    Returns:
        ``(99, 990)``.
    """
    return _set_status(file_access, int(_status.FsReply.ERROR), BRIDGE_BAD_FUNCTION)


def _aa100_bad_function(file_access: FileAccess) -> StatusPair:
    """The handler's bad-function paragraph.

    ``aa100-Bad-Function`` [common/acasirsub3.cbl:L340-L345], sets ``999``/ ``99``. The
    RDB section carries a SECOND, textually distinct site with the same codes
    [:L517-L519] (A27).

    Args:
        file_access: Receives the status.

    Returns:
        ``(99, 999)``.
    """
    return _set_status(file_access, int(_status.FsReply.ERROR), HANDLER_BAD_FUNCTION)


# CLEARING VALUES - `move zero` AND `move spaces` ARE NOT THE SAME THING The figurative
# constant ZERO moved into an alphanumeric receiver fills it with the CHARACTER '0'
# repeated to the receiver's length, which is not what `move spaces` does.
_SQL_ERR_ZEROED: Final[str] = "0" * _status.SQL_ERR_WIDTH
_SQL_ERR_SPACES: Final[str] = " " * _status.SQL_ERR_WIDTH
_SQL_MSG_SPACES: Final[str] = " " * _status.SQL_MSG_WIDTH
_SQL_STATE_SPACES: Final[str] = " " * _status.SQL_STATE_WIDTH


def _ba040_process_read_next(
    connection: object, dflt: WsIrsDefaultRecord, file_access: FileAccess
) -> StatusPair:
    """Load the whole table into the 33-element record.

    Args:
        connection: An open connection.
        dflt: The 33-element linkage record, filled in place.
        file_access: Receives the status, trace numbers and diagnostics.

    Returns:
        The status pair as the loop left it - see A7, which is why that phrasing is
            exact.
    """
    cursor = _cursor()
    logging_data = file_access.logging_data

    if cursor.cursor_not_active():
        # `if Cursor-Not-Active` [common/irsdfltMT.cbl:L476]. Always true when reached
        # through this handler, because the synthesised open resets the cursor [:L452].

        # A15. `set KOR-x1 to 1` [:L477] then `move KOR-offset (KOR-x1) to K` [:L478]
        # and `move KOR-length (KOR-x1) to L` [:L479]. BOTH ARE THEN NEVER USED.
        key_of_reference = _cursor_state.key_of_reference(TABLE, 1)
        dead_k = key_of_reference.kor_offset
        dead_l = key_of_reference.kor_length
        if (dead_k, dead_l) != (KEY_OFFSET, KEY_LENGTH):  # pragma: no cover
            _LOG.error(
                "%s: key metadata drifted from '00010001' "
                "[common/irsdfltMT.cbl:L268]",
                BRIDGE,
            )

        logging_data.ws_log_where = _FROZEN_SELECT_ECHO
        logging_data.ws_no_paragraph = _PARA_READ_SELECT

        rows, select_error = _execute_select(
            connection, _SELECT_STATEMENT, (READ_KEY_LITERAL,)
        )
        row_count = cursor.store_result(rows)
        logging_data.ws_count_rows = row_count
        logging_data.ws_file_key = _KEY_SELECT_ISSUED


        if row_count == 0:
            _probe_driver_error(select_error, file_access)
            logging_data.ws_file_key = _KEY_NO_DATA
            status = _set_status(
                file_access,
                int(_status.FsReply.END_OF_FILE),
                int(_status.FsReply.END_OF_FILE),
            )
            # `go to ba998-Free` [:L534] - Class 4 sibling re-dispatch.
            _ba998_free(file_access)
            return status

        # `move 1 to Most-Cursor-Set` [:L536], whose trailing comment is "should test if
        # select worked first??????" - six question marks.
        cursor.set_cursor_active()

    logging_data.ws_log_where = " " * len(logging_data.ws_log_where)
    logging_data.ws_no_paragraph = _PARA_READ_FETCH
    _clear_all_slots(dflt)

    # `perform varying A from 1 by 1 until A > 32` [:L544-L545]. The bound is
    # BRIDGE_LIMIT, never OCCURS (A2).
    for a in range(1, BRIDGE_LIMIT + 1):
        row = cursor.fetch_record()

        # A31. `if return-code = -1 or A > 32 or = zero` [:L564-L565].
        if row is None or a > BRIDGE_LIMIT or a == 0:
            # `move 10 to fs-Reply WE-Error` [:L566], `move "EOF"` [:L567], `move zero
            # to Most-Cursor-Set` [common/irsdfltMT.cbl:L568]. A7's CONSEQUENCE LIVES
            # HERE.
            _set_status(
                file_access,
                int(_status.FsReply.END_OF_FILE),
                int(_status.FsReply.END_OF_FILE),
            )
            logging_data.ws_file_key = _KEY_EOF
            cursor.set_cursor_not_active()
            break

        key_value = int(row[PRIMARY_KEY])

        # A3. THE OFF-BY-ONE GUARD [common/irsdfltMT.cbl:L575-L583].
        if key_value == 0 or key_value > BRIDGE_LIMIT:
            logging_data.ws_file_key = _KEY_EOF3
            # `move HV-DEF-REC-KEY to WE-Error` - the VALUE, not a code. Set directly
            # rather than through `_set_status`, because FS-Reply must be left alone.
            file_access.we_error = key_value
            cursor.set_cursor_not_active()
            break

        if cursor.count_rows == 0:
            errno_text, _message, _sql_state = _probe_driver_error(
                None, file_access
            )
            if not _errno_is_zero(errno_text):
                # A32. `move 10 to fs-reply *> EOF equivilent !!` [:L593] - a GENUINE
                # SQL ERROR REPORTED AS END-OF-FILE. The mapping is reproduced.
                _set_status(
                    file_access,
                    int(_status.FsReply.END_OF_FILE),
                    int(_status.FsReply.END_OF_FILE),
                )
                logging_data.ws_file_key = _KEY_EOF2
            cursor.set_cursor_not_active()
            break

        stored_key = _unload_row_into(dflt, row)

        # `move HV-DEF-REC-KEY to WS-Key` then `move WS-Key to WS-File-Key` [:L606-L607]
        # - a two-step move through a `pic 99` intermediate [common/irsdfltMT.cbl:L258],
        # which cannot hold a value above 99.
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


    # `*> move HV-DEF-REC-KEY to WS-File-Key.` [:L613] and `*> move zero to fs-reply WE-
    # Error.` [:L614].
    return int(file_access.fs_reply), int(file_access.we_error)


def _ba070_process_write(
    connection: object, dflt: WsIrsDefaultRecord, file_access: FileAccess
) -> StatusPair:
    """Insert all thirty-two rows, blanks included, squashing failures.

    Args:
        connection: An open connection.
        dflt: The 33-element linkage record to write out.
        file_access: Receives the status and diagnostics.

    Returns:
        The status pair, which reports only the LAST failing row - see A9.
    """
    logging_data = file_access.logging_data

    # [:L618-L619] `move zero to WS-Mysql-Time-Step WS-SQL-Retry`. These arm the lock-
    # retry ladder in `COPY "mysql-procedures.cpy"` [:L751], whose only `perform` is
    # commented out at [copybooks/mysql-procedures.cpy:L167].

    _set_status(file_access, int(_status.FsReply.SUCCESS), int(_status.WeError.SUCCESS))
    logging_data.sql_msg = _SQL_MSG_SPACES
    logging_data.sql_err = _SQL_ERR_ZEROED
    logging_data.ws_no_paragraph = _PARA_WRITE


    saved_fs_reply = 0

    # `perform varying A from 1 by 1 until A > 32` [:L626]. A2: never OCCURS.
    for a in range(1, BRIDGE_LIMIT + 1):
        # A8. THE EMPTY-SLOT SKIP IS COMMENTED OUT [:L627-L631].

        parameters = _load_host_variables(dflt, a)

        logging_data.ws_file_key = str(a)

        # `perform bb200-Insert` [:L642] - one statement, never batched (A5).
        affected_rows, error = _execute_one(connection, _INSERT_STATEMENT, parameters)
        logging_data.ws_count_rows = affected_rows

        if affected_rows != 1:
            errno_text, _message, sql_state = _probe_driver_error(error, file_access)
            # [:L647] - three-space zero literal; see A21 for why one predicate serves
            # all four sites.
            if not _errno_is_zero(errno_text):
                if _is_duplicate_key(errno_text, sql_state):
                    file_access.fs_reply = int(_status.FsReply.DUPLICATE_KEY)
                else:
                    file_access.fs_reply = int(_status.FsReply.ERROR)

            # A19. THE WRITE SETS `FS-Reply` ONLY, NEVER `WE-Error`. The rewrite sets
            # both and then discards both [:L727-L728]. The asymmetry is reproduced.

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

        # Each failing row's status is stashed and `fs-reply` is CLEARED "for next loop
        # iteration".
        if file_access.fs_reply != int(_status.FsReply.SUCCESS):
            saved_fs_reply = int(file_access.fs_reply)
            file_access.fs_reply = int(_status.FsReply.SUCCESS)

    if saved_fs_reply != int(_status.FsReply.SUCCESS):
        file_access.fs_reply = saved_fs_reply

    return int(file_access.fs_reply), int(file_access.we_error)


def _ba090_process_rewrite(
    connection: object, dflt: WsIrsDefaultRecord, file_access: FileAccess
) -> StatusPair:
    """Update all thirty-two rows, then discard every error.

    Args:
        connection: An open connection.
        dflt: The 33-element linkage record to write out.
        file_access: Receives the status and diagnostics.

    Returns:
        Always ``(0, 0)``. That is the defect, not a simplification.
    """
    logging_data = file_access.logging_data

    # [:L675-L676] `move zero to WS-Mysql-Time-Step WS-SQL-Retry` - the dead ladder
    # again. NOTE WHAT IS MISSING.
    logging_data.ws_no_paragraph = _PARA_REWRITE

    # A23. THERE IS NO `initialise TD-IRSDFLT-REC` HERE, where the write has one at
    # [:L625]. Absence reproduced by absence.

    for a in range(1, BRIDGE_LIMIT + 1):

        # [:L684-L693]. The rewrite reaches the same host-variable state as the write
        # but spells one move differently.
        parameters = _load_host_variables(dflt, a)
        logging_data.ws_file_key = str(a)

        # A15. `set KOR-x1 to 1` / `move KOR-offset to K` / `move KOR-length to L`
        # [:L695-L697] - computed, never used, for the second time.
        key_of_reference = _cursor_state.key_of_reference(TABLE, 1)
        dead_k = key_of_reference.kor_offset
        dead_l = key_of_reference.kor_length
        if (dead_k, dead_l) != (KEY_OFFSET, KEY_LENGTH):  # pragma: no cover
            _LOG.error(
                "%s: key metadata drifted from '00010001' "
                "[common/irsdfltMT.cbl:L268]",
                BRIDGE,
            )

        # A15, continued.
        logging_data.ws_log_where = f'{PRIMARY_KEY}="{a}"'

        affected_rows, error = _execute_one(
            connection, _UPDATE_STATEMENT, (*parameters, a)
        )
        logging_data.ws_count_rows = affected_rows


        if affected_rows != 1:
            errno_text, _message, _sql_state = _probe_driver_error(error, file_access)
            if not _errno_is_zero(errno_text):
                file_access.fs_reply = int(_status.FsReply.ERROR)
                # A18. `WE-Error 994` IS SET HERE AND CLEARED BELOW, so it is
                # permanently unobservable - a dead error code.
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


    # `move zero to FS-Reply WE-Error.` / `move zero to SQL-Err.` / `move spaces to SQL-
    # Msg.` - outside the loop, outside any `if`.
    _set_status(file_access, int(_status.FsReply.SUCCESS), int(_status.WeError.SUCCESS))
    logging_data.sql_err = _SQL_ERR_ZEROED
    logging_data.sql_msg = _SQL_MSG_SPACES

    return int(_status.FsReply.SUCCESS), int(_status.WeError.SUCCESS)


# A10. OPEN AND CLOSE ARE NO-OPS ON BOTH PATHS, AND NEITHER REACHES THE BRIDGE. The
# maintainer explains the shape himself [common/acasirsub3.cbl:L169-L176].


def _no_op_open_or_close(file_access: FileAccess, *, is_close: bool) -> StatusPair:
    """Return ``(0, 0)`` without touching the database.

    A30. CODES 1 AND 2 JUMP TO `aa-Exit`, BYPASSING `aa999-main-exit`
    [common/acasirsub3.cbl:L203] [:L207], and `aa999-main-exit` is where the logging
    hook lives [:L347-L350].

    Args:
        file_access: Receives ``(0, 0)`` and, for a close, the zeroed function and
            access codes.
        is_close: ``True`` for code 2, ``False`` for code 1.

    Returns:
        ``(0, 0)``, always.
    """
    status = _set_status(
        file_access, int(_status.FsReply.SUCCESS), int(_status.WeError.SUCCESS)
    )
    if is_close:
        file_access.file_function = 0
        file_access.access_type = 0
    return status


def open_(file_access: FileAccess) -> StatusPair:
    """``fn-open`` with ``fn-i-o``. A no-op returning ``(0, 0)``.

    Reached from ``acasirsub3-Open`` [copybooks/Proc-ZZ100-ACAS-IRS-
    Calls.cob:L223-L227], the only verb besides ``Open-Input`` whose reply the IRS
    facade checks - and, on a non-zero reply, the only kind of failure that makes the
    facade return from the program outright [:L364].

    Args:
        file_access: Receives ``(0, 0)``.

    Returns:
        ``(0, 0)``.
    """
    return _no_op_open_or_close(file_access, is_close=False)


def open_input(file_access: FileAccess) -> StatusPair:
    """``fn-open`` with ``fn-input``. A no-op returning ``(0, 0)``.

    Args:
        file_access: Receives ``(0, 0)``.

    Returns:
        ``(0, 0)``.
    """
    return _no_op_open_or_close(file_access, is_close=False)


def open_output(file_access: FileAccess) -> StatusPair:
    """``fn-open`` with ``fn-output``. A no-op returning ``(0, 0)``.

    Args:
        file_access: Receives ``(0, 0)``.

    Returns:
        ``(0, 0)``.
    """
    return _no_op_open_or_close(file_access, is_close=False)


def open_extend(file_access: FileAccess) -> StatusPair:
    """``fn-open`` with ``fn-extend``. A no-op returning ``(0, 0)``.

    On the RDB path the access type is not inspected [common/acasirsub3.cbl:L429], so
    this is a no-op like any other open. The DEAD flat body would have rejected it with
    ``(99, 997)`` [:L232-L234].

    Args:
        file_access: Receives ``(0, 0)``.

    Returns:
        ``(0, 0)``.
    """
    return _no_op_open_or_close(file_access, is_close=False)


def close(file_access: FileAccess) -> StatusPair:
    """``fn-close``. A no-op returning ``(0, 0)``, plus zeroing the log codes.

    Args:
        file_access: Receives ``(0, 0)`` and zeroed function/access codes.

    Returns:
        ``(0, 0)``.
    """
    return _no_op_open_or_close(file_access, is_close=True)


def _unsupported_verb(file_access: FileAccess, verb: str) -> StatusPair:
    """Route a verb this handler does not dispatch to bad function.

    THREE INDEPENDENT REASONS these verbs are unreachable, which is why they are grouped
    rather than each argued separately.

    Args:
        file_access: Receives ``(99, 999)``.
        verb: The verb name, for the log record only.

    Returns:
        ``(99, 999)`` - the HANDLER's code. A26: the bridge's own bad-function paragraph
            would say 990 [common/irsdfltMT.cbl:L743], and the two are not reconciled.
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


def read_next(
    system: SystemRecord,
    dflt: WsIrsDefaultRecord,
    file_access: FileAccess,
    *,
    transport: _connection.TransportSecurity | None = None,
) -> StatusPair:
    """``fn-read-next``: synthesised open, read, then close - unless it failed.

    Args:
        system: Supplies the credentials for the synthesised open.
        dflt: The 33-element linkage record, filled in place.
        file_access: Carries the reply.
        transport: TLS material for the connection, or ``None``.

    Returns:
        The read's status pair, never the close's.
    """
    _set_status(file_access, int(_status.FsReply.SUCCESS), int(_status.WeError.SUCCESS))

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
        return fs_reply, we_error

    file_access.file_function = int(_status.FileFunction.READ_NEXT)
    fs_reply, we_error = _ba040_process_read_next(connection, dflt, file_access)

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

    file_access.file_function = int(_status.FileFunction.CLOSE)
    _ba030_process_close(connection, file_access)

    _set_status(file_access, saved_fs_reply, saved_we_error)
    file_access.logging_data.ws_file_key = _KEY_OPEN_READ_CLOSE
    return saved_fs_reply, saved_we_error


def write(
    system: SystemRecord,
    dflt: WsIrsDefaultRecord,
    file_access: FileAccess,
    *,
    transport: _connection.TransportSecurity | None = None,
) -> StatusPair:
    """``fn-write``: open, 32 inserts, close - then silently retry as a rewrite.

    A1, FIRST HALF. On failure this DOES NOT REPORT THE FAILURE. It writes a diagnostic
    key, sets ``fn-Re-write``, CLEARS ``fs-reply`` and ``we-error`` [:L488-L489], and
    falls through into the rewrite block - which then clears its own errors
    unconditionally [common/irsdfltMT.cbl:L736-L738].

    Args:
        system: Supplies the credentials for the synthesised opens.
        dflt: The 33-element linkage record to write out.
        file_access: Carries the reply.
        transport: TLS material for the connections, or ``None``.

    Returns:
        The status pair - which on any failure is the rewrite's ``(0, 0)``.
    """
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
        return fs_reply, we_error

    file_access.file_function = int(_status.FileFunction.WRITE)
    fs_reply, we_error = _ba070_process_write(connection, dflt, file_access)

    saved_fs_reply, saved_we_error = fs_reply, we_error

    file_access.file_function = int(_status.FileFunction.CLOSE)
    _ba030_process_close(connection, file_access)

    _set_status(file_access, saved_fs_reply, saved_we_error)

    if saved_fs_reply == int(_status.FsReply.SUCCESS) and saved_we_error == int(
        _status.WeError.SUCCESS
    ):
        return saved_fs_reply, saved_we_error

    file_access.logging_data.ws_file_key = _KEY_OPEN_WRITE_FAILED_CLOSE

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


    file_access.file_function = int(_status.FileFunction.RE_WRITE)
    _set_status(file_access, int(_status.FsReply.SUCCESS), int(_status.WeError.SUCCESS))

    # Class 4 sibling re-dispatch: fall through to `if fn-Re-write` [:L494].
    return rewrite(system, dflt, file_access, transport=transport)


def rewrite(
    system: SystemRecord,
    dflt: WsIrsDefaultRecord,
    file_access: FileAccess,
    *,
    transport: _connection.TransportSecurity | None = None,
) -> StatusPair:
    """``fn-re-write``: open, 32 updates, close. Always reports success.

    Args:
        system: Supplies the credentials for the synthesised open.
        dflt: The 33-element linkage record to write out.
        file_access: Carries the reply.
        transport: TLS material for the connection, or ``None``.

    Returns:
        ``(0, 0)`` unless the synthesised open failed.
    """
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
        return fs_reply, we_error

    file_access.file_function = int(_status.FileFunction.RE_WRITE)
    fs_reply, we_error = _ba090_process_rewrite(connection, dflt, file_access)

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

    Args:
        system: ``System-Record``. Selects the path and supplies credentials.
        dflt: ``WS-IRS-Default-Record`` - the 33-element array.
        file_access: ``File-Access``. Carries the function code in and the status out.
        file_defs: ``File-Defs``.
        dal_common: ``ACAS-DAL-Common-data``. ``sw_testing`` is the frozen ``Testing-1``
            switch that gates the logging hooks [copybooks/Test-Data-Flags.cob],
            honoured below.
        transport: TLS material for the synthesised connections. Keyword-only and placed
            after the five positional parameters so the linkage order is untouched.

    Returns:
        ``(fs_reply, we_error)``, also written into ``file_access``.
    """
    logging_data = file_access.logging_data

    logging_data.ws_log_system = WS_LOG_SYSTEM
    logging_data.ws_log_file_no = WS_LOG_FILE_NO_FLAT

    # `if not FS-Cobol-Files-Used` [:L180] selects the RDB path.
    file_system_used = int(
        system.system_data_block.rdbms_flat_statuses.file_system_used
    )
    rdb_path = file_system_used != 0

    if rdb_path:
        file_access.fa_rdbms_flat_statuses.fa_file_system_used = file_system_used
        file_access.fa_rdbms_flat_statuses.fa_file_duplicates_in_use = int(
            system.system_data_block.rdbms_flat_statuses.file_duplicates_in_use
        )
        logging_data.ws_log_file_no = WS_LOG_FILE_NO_RDB

    file_access.we_error = int(_status.WeError.SUCCESS)
    logging_data.sql_err = _SQL_ERR_SPACES
    logging_data.sql_msg = _SQL_MSG_SPACES
    logging_data.sql_state = _SQL_STATE_SPACES

    gate_status = _ba012_test_ws_rec_size_2(system, file_access)
    if gate_status is not None:
        # `go to ba-rdbms-exit` [:L402] - THE BRIDGE IS NEVER CALLED. Class 3 section
        # exit -> return.
        return gate_status

    function_code = int(file_access.file_function)

    # A11. The two dispatch tables differ on code 7, so the path is chosen before the
    # verb is.
    dispatch_table = RDB_PATH_DISPATCH if rdb_path else FLAT_PATH_DISPATCH
    verb = dispatch_table.get(function_code)

    if verb is None:
        # `when other` -> `aa100-Bad-Function` [:L213-L214] on the flat path, and the
        # second, textually distinct site [:L517-L519] on the RDB path (A27).
        return _aa100_bad_function(file_access)

    if verb == "open":
        # A10 / A30. Codes 1 and 2 never reach the bridge on either path, and bypass the
        # logging hook. Flat: [:L200-L203]. RDB: [:L429-L432].
        return _no_op_open_or_close(file_access, is_close=False)
    if verb == "close":
        return _no_op_open_or_close(file_access, is_close=True)

    if not rdb_path:
        # DOCUMENTED OMISSION, STATED AT THE POINT IT BITES.
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
        status = rewrite(system, dflt, file_access, transport=transport)

    # `aa999-main-exit. if Testing-1 perform Ca-Process-Logs` [:L347-L350]. `Testing-1`
    # is `SW-Testing` in `copybooks/Test-Data-Flags.cob`, whose own comment reads "set
    # sw-testing to zero to stop logging" [:L149].
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
