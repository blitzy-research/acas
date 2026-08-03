r"""`acasirsub5` + `irsfinalMT` - the IRS Final-Accounts handler [`IRSFINAL-REC`].

The migration of the handler `common/acasirsub5.cbl` (534 lines) together with
its generated bridge `common/irsfinalMT.cbl` (727 lines), reimplemented as SQL
against the frozen three-column table `IRSFINAL-REC` [mysql/ACASDB.sql:L214].
Agent Action Plan section 0.4.1.5 names the pair and the target verbatim::

    | acas_posting/dal/acasirsub5_irs_final.py | CREATE |
    | common/acasirsub5.cbl + common/irsfinalMT.cbl | IRSFINAL-REC |

and section 0.2.1.1 gives the spine link: IRS final -> `acasirsub5` ->
`irsfinalMT` -> `IRSFINAL-REC` -> record copybook `copybooks/irswsfinal.cob`.
Section 0.3.1 states the boundary rule that puts a MODULE PER HANDLER rather
than per table here, verbatim: "Mirroring the handler boundary rather than the
table boundary keeps the Python module set in exact correspondence with the
COBOL programs that the traceability document must map, and preserves the
dispatch semantics rather than flattening them."

THREE THINGS TO KNOW BEFORE READING ANY CODE BELOW
==================================================

**1. THIS HANDLER IS NOT ROW-ORIENTED. ONE COBOL RECORD IS TWENTY-SIX ROWS.**
`copybooks/irswsfinal.cob` declares `01 Final-Record.` [:L7] as a 655-byte
structure holding TWO PARALLEL 26-ELEMENT ARRAYS - `05 ar1 pic x(24) occurs 26`
[:L36] redefining 26 enumerated fields [:L9-L34], and `05 ar2 pic x occurs 26`
[:L66] redefining another 26 [:L39-L64] - plus a trailing `03 ar3 pic x(5)`
[:L68]. The arithmetic is exact: 26 * 24 + 26 * 1 + 5 = 655, matching the
copybook's own `*> rec 655 bytes` [:L6]. The table has THREE columns. So one
logical `read` REASSEMBLES up to 26 rows into one record and one logical
`write` EMITS 26 `INSERT`s. The primary-key column `IRS-FINAL-ACC-REC-KEY`
EXISTS IN NO COPYBOOK: it is the array subscript, and the bridge says so in its
own comment `*> KEY = table position` [common/irsfinalMT.cbl:L455].

**2. `ar3 pic x(5)` IS SILENTLY DROPPED - VERIFIED BY EXHAUSTIVE SEARCH.**
A case-insensitive search for `ar3` returns ZERO hits in
`common/irsfinalMT.cbl`, ZERO in `common/irsfinalMT.scb`, ZERO in
`common/acasirsub5.cbl` and ZERO in `mysql/ACASDB.sql`; the ONE hit anywhere is
its declaration at [copybooks/irswsfinal.cob:L68]. There is no column, no host
variable, no load and no unload. FIVE BYTES OF EVERY RECORD ARE NEVER PERSISTED
AND NEVER READ BACK. The generated dictionary records the same finding
independently - `loader.cite("Final-Record.ar3")` renders
`copybook=copybooks/irswsfinal.cob:L68  bridge=absent  column=absent` - which
is exactly the cross-source check section 0.4.1.6 asks the generator to
automate, "flags any field present in one source and absent from another".
Rule R-4 makes reproducing this mandatory: the field stays in the record
dataclass and is ABSENT FROM EVERY SQL STATEMENT here. See anomaly A3.

**3. A FAILED WRITE REPORTS SUCCESS - AND IT TAKES TWO DEFECTS TO DO IT.**
Neither is visible from one file, which is why a reviewer who checked only one
would pass it:

    (a) THE HANDLER SILENTLY RETRIES A FAILED WRITE AS A REWRITE, HAVING FIRST
        ERASED THE FAILURE. A single `end-if.` [common/acasirsub5.cbl:L483]
        closes BOTH the outer `if fn-Write` [:L459] and the inner
        `if (fs-Reply not = zero or WE-Error not = zero)` [:L475], so the
        `else / go to ba-RDBMS-Exit` [:L481-L482] binds to the INNER
        conditional and the failure arm falls THROUGH into the rewrite block at
        [:L485]. Before falling through it executes
        `move zero to fs-reply we-error   *> clear if used in write` [:L480].

    (b) THE BRIDGE'S REWRITE UNCONDITIONALLY CLEARS EVERY ERROR FIELD AFTER ITS
        LOOP. `move zero to FS-Reply WE-Error.` / `move zero to SQL-Err.` /
        `move spaces to SQL-Msg.` [common/irsfinalMT.cbl:L571-L573], with NO
        guarding condition. The `move 994 to WE-Error` set at [:L563] is
        therefore PERMANENTLY UNOBSERVABLE.

    NET EFFECT: a write that fails on all 26 rows returns
    `(FS-Reply 0, WE-Error 0)` - indistinguishable from success.

This is the IDENTICAL CONSTRUCT CLASS as Agent Action Plan anomaly #1, "A
missing terminating period nests a second conditional inside the first"
[sales/sl060.cbl:L1172-L1178]. Here it is a missing `end-if` rather than a
missing period, but the mechanism and the consequence are the same. And it is
NOT UNIQUE TO `acasirsub5`: `common/acasirsub3.cbl` carries the same pair with
`common/irsdfltMT.cbl:L736-L738` as its unguarded reset, so TWO OF THE TWENTY
HANDLER MODULES SWALLOW WRITE FAILURES. Stated here so the anomaly log records
it once, correctly, for both. See anomalies A1 and A2.

THE MAINTAINER'S OWN EXPLANATION - WHY OPEN AND CLOSE ARE NO-OPS
================================================================
[common/acasirsub5.cbl:L161-L168], verbatim::

    *> WARNING The modules acasirsub5 for Final as well as acasirsub3
    *> for defaults has to be modified as IRS only does a read or write
    *>   and not a direct open or close so
    *>   it has to be done here when processing RDB.

    *>   For Cobol files these have been changed to do the same so direct
    *>    calls to open and close are not needed or wanted.
    *>     so return with fs-reply & we-error = zero.

That comment is the design rationale for this whole module. It is why
`open_`/`open_input`/`open_output`/`open_extend`/`close` published here are
NO-OPS, and why :func:`dispatch` SYNTHESISES its own open/verb/close triples
around every read, write and rewrite [common/acasirsub5.cbl:L432-L504]. The
maintainer labels his own arrangement non-standard at [:L418-L419]: "Here we do
non standard DAL things to handle open & close pre / post to calls for Read and
write."

A FIVE-CODE HANDLER, AND THE ONLY PAIR WHERE BOTH SIDES AGREE
=============================================================
A census of every `when <n>` across all seventeen in-scope handlers puts this
module in a class of two:

    acas000                                             1 2 3 4 5 7
    acas005 006 007 008 013 015 019 029 acasirsub4      1 2 3 4 5 7 8 9
    acas012 acas022                                     ... + 31
    acas016 acas026                                     ... + 34
    acasirsub1                                          ... + 13 15
    acasirsub3  acasirsub5                              1 2 3 5 7 ONLY

`common/acasirsub5.cbl:L191-L207` dispatches `when 1`, `when 2`, `when 3`,
`when 5`, `when 7`, `when other` - NO 4, NO 8, NO 9. Codes 1 and 2 are
DISPATCHED BUT ARE NO-OPS: they `move zero to FS-Reply WE-Error` and
`go to aa-Exit` [:L192-L199], with the real bodies commented out, and that jump
BYPASSES `aa999-main-exit` and its logging hook [:L334-L337]. `when 5` FALLS
THROUGH to `when 7` [:L202-L204] - "write/rewrite can do the same ... as file
is opened as output." And the bridge dispatches THE SAME FIVE
[common/irsfinalMT.cbl:L239-L252], which makes this handler/bridge pair the
ONLY one in the folder where both sides agree on a reduced code set.

The bridge does, however, SEPARATE 5 from 7 where the handler's flat path
merges them: `when 5 -> ba070-Process-Write` (an `INSERT`) and
`when 7 -> ba090-Process-Rewrite` (an `UPDATE`). On the RDB path the handler
therefore sends `fn-Write` (5) first and, on failure, `fn-Re-write` (7) - which
is the fall-through of anomaly A2.

THE FROZEN SCHEMA - THREE COLUMNS, THE NARROWEST IN-SCOPE TABLE
===============================================================
[mysql/ACASDB.sql:L214-L219], verbatim::

    CREATE TABLE `IRSFINAL-REC` (
      `IRS-FINAL-ACC-REC-KEY` tinyint(2) unsigned NOT NULL,
      `IRS-AR1` char(24) NOT NULL,
      `IRS-AR2` char(1) NOT NULL,
      PRIMARY KEY (`IRS-FINAL-ACC-REC-KEY`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci;

Three columns; next narrowest in scope are `SYSDEFLT-REC`, `IRSDFLT-REC` and
`ANALYSIS-REC` at four. Single-column primary key, ZERO secondary indexes,
ZERO `AUTO_INCREMENT`, ZERO `TIMESTAMP`, ZERO column `DEFAULT` and - unlike
`IRSDFLT-REC`, which carries `COMMENT='Defaults table for IRS'` - NO table
comment. Section 0.6.6 depends on exactly this shape: the harness dump is
`SELECT * FROM <table> ORDER BY <primary key>` with no tie-breaker.

NOT ONE NUMERIC DATA COLUMN, WHICH IS WHY NO `Decimal` APPEARS BELOW
====================================================================
`IRS-AR1` is `char(24)`, `IRS-AR2` is `char(1)`, and the only numeric column is
the bridge-derived key, `tinyint(2) unsigned` -> `int`. NO MONETARY VALUE PASSES
THROUGH THIS MODULE AT ALL. Rule R-2 is nonetheless binding and is honoured:
no `float`, no `complex`, no `math`, no builtin `round` or `abs`, and no
`numpy`/`pandas` - see the rule section below. Do NOT generalise the absence:
across this folder `valueMT` loses the sign on three MONETARY fields, `salesMT`
narrows eleven consecutive fields [common/salesMT.cbl:L302-L312] and `purchMT`
twelve [common/purchMT.cbl:L295-L306], while `irsnominalMT` and `irsdfltMT`
have no signed field at all. Every field here is resolved from
:mod:`acas_posting.dictionary.loader`, never inferred.

THE COLUMN NAMES CARRY AN `IRS-` PREFIX THE COPYBOOK FIELDS DO NOT
==================================================================
`ar1` -> `IRS-AR1`, `ar2` -> `IRS-AR2`, and the key is `IRS-FINAL-ACC-REC-KEY`
where `SYSFINAL-REC`'s equivalent is plain `FINAL-ACC-REC-KEY`. A PREFIX ADDED
AT THE BRIDGE [common/irsfinalMT.cbl:L172-L174], to disambiguate from the
non-IRS final-accounts table. Contrast `acas015`/`analMT`, where the bridge
STRIPS a `WS-` prefix. Prefix handling is PER-BRIDGE and must be read, never
inferred, so :data:`COLUMNS` is built from the dictionary rather than written
out by hand. See anomaly A28.

WHY THE COLUMN NAMES CANNOT COME FROM THE FD, EITHER
====================================================
The handler's file description is a FLAT, UNSTRUCTURED BYTE BLOB -
`01 Record-5 pic x(655).` [common/acasirsub5.cbl:L104] under
`fd Final-File.` [:L102] - and the handler moves the whole 655 bytes between
`Record-5` and `Final-Record` [:L293, :L318]. `acasirsub3` does the same with
`01 Record-3 pic x(264)`, and EXACTLY THE TWO HANDLERS THE MAINTAINER'S WARNING
NAMES have flat-blob FDs, for the same reason: they exchange whole arrays, not
rows, so there is nothing to structure. Every other handler in the folder
declares a structured FD. So where `IRSPOSTING-REC` takes its column names from
an inline `01 Record-4` and `IRSNL-REC` from `copybooks/irsfdwsnl.cob`, THIS
TABLE'S NAMES COME FROM THE BRIDGE'S HOST VARIABLES ALONE - which is precisely
section 0.8.2's point, quoted verbatim: "The maintainer's one-way
COBOL-to-MySQL bridge defines the authoritative record-layout <-> table mapping
- it is the data dictionary for this migration."

THE COMPLETE DRIFT TABLE
========================
    #  column (type)                          host variable          copybook
    -  ------------------------------------   --------------------   --------
    1  IRS-FINAL-ACC-REC-KEY                  HV-IRS-FINAL-ACC-      NONE -
       tinyint(2) unsigned  [ACASDB.sql:L215] REC-KEY 9(03) COMP     the array
                                              [irsfinalMT.cbl:L172]  subscript
       drift: bridge-only column; (none) -> 3 digits -> 2; `IRS-` prefix added;
              written from `move A to HV-...` [irsfinalMT.cbl:L481] and read
              back as the subscript at [:L455-L456]

    2  IRS-AR1 char(24)     [ACASDB.sql:L216] HV-IRS-AR1 X(24)       ar1-1 ...
                                              [irsfinalMT.cbl:L173]  ar1-26
                                                                     [:L9-L34]
                                                    redefined `ar1 occurs 26`
                                                    [irswsfinal.cob:L36]
       drift: 26 copybook fields -> 1 column x 26 rows; width EXACT (no
              24->32 drift as in `nominalMT`); `IRS-` prefix added

    3  IRS-AR2 char(1)      [ACASDB.sql:L217] HV-IRS-AR2 X(1)        ar2-1 ...
                                              [irsfinalMT.cbl:L174]  ar2-26
                                                                     [:L39-L64]
                                                    redefined `ar2 occurs 26`
                                                    [irswsfinal.cob:L66]
       drift: 26 copybook fields -> 1 column x 26 rows; width EXACT; `IRS-`
              prefix added

    -  NO COLUMN                              NO HOST VARIABLE       ar3 x(5)
                                                              [irswsfinal.cob:L68]
       drift: SILENTLY DROPPED - see headline 2 and anomaly A3

THE FIELD-TO-DICTIONARY MAPPING IS UNUSUAL THREE WAYS  (rule R-5)
=================================================================
Rule R-5 requires every field to map to a data-dictionary entry, and section
0.8.1 makes the ordering a directive rather than a preference: "Data dictionary
first. ... every Python field definition cites its entry. This ordering is a
directive, not a preference - it is what prevents fields being transcribed by
eye." All three peculiarities here are recorded in the generated artifact and
re-read at import time by :data:`COLUMNS`:

    `IRS-FINAL-ACC-REC-KEY`   HAS NO COPYBOOK FIELD. Its entry is one-sided,
                              `presence(in_copybook=False, in_bridge=True,
                              in_column=True)`, and carries a derivation note
                              naming the array subscript as its ONLY source -
                              `move A to HV-IRS-FINAL-ACC-REC-KEY`
                              [common/irsfinalMT.cbl:L481] on write, and
                              `AR1 (HV-IRS-FINAL-ACC-REC-KEY)`
                              [common/irsfinalMT.cbl:L455-L456] on read.
    `IRS-AR1` / `IRS-AR2`     EACH MAP TO 26 COPYBOOK FIELDS - `ar1-1` ...
                              `ar1-26` and `ar2-1` ... `ar2-26` - plus the
                              `occurs 26` redefines that overlay them.
    `ar3`                     MAPS TO NOTHING AT ALL. A deliberate omission
                              with no column, recorded as an omission per
                              section 0.5.3, "Deliberate omissions are recorded
                              as omissions."

THE `REDEFINES` PAIR - WHO KEEPS IT IN STEP
===========================================
`copybooks/irswsfinal.cob` declares each array TWICE: 26 enumerated fields and
an `occurs 26` view redefining them [:L8-L36, :L38-L66]. In COBOL those are ONE
STORAGE, so the question of keeping them in step cannot arise. In Python they
are two dataclasses, and `records/irs_final.py` deliberately declines to own
the aliasing - it states that both views are modelled with "no property that
switches between the two, and no designation of one as primary". So this module
owns it, and the rule is stated once here:

    * The BRIDGE'S OPERANDS ARE THE ARRAY VIEWS AND ONLY THE ARRAY VIEWS -
      `AR1 (HV-...)`/`AR2 (HV-...)` on read [common/irsfinalMT.cbl:L455-L456]
      and `AR1 (A)`/`AR2 (A)` on write [:L484-L485] and rewrite [:L528-L529].
      Verified: the 52 enumerated names appear NOWHERE in the bridge. So the
      SQL side reads the array view, exactly as the frozen source does.
    * `initialize Final-Record with filler.` [common/irsfinalMT.cbl:L395] names
      THE WHOLE `01` GROUP, so it blanks all five Python members - both array
      views, both enumerated groups, and `ar3`.
    * A `move` INTO one entry writes bytes that are addressable through both
      views, so :func:`read_next` writes the enumerated field as well as the
      array entry. That is reproducing `REDEFINES` storage aliasing, not adding
      behaviour: leaving the enumerated view stale would be a DIVERGENCE from
      compiled behaviour, which rule R-6 settles against.
    * THE RULE RUNS BOTH WAYS, AND THE WRITE DIRECTION IS THE ONE THAT MATTERS
      TO A CALLER. The bullet above covers the bridge writing INTO the record;
      the mirror case is a caller writing into it before a `write` or `rewrite`.
      In the compiled program `move "Sales" to ar1-7` has already written
      `AR1 (7)`, so the loads at [:L484-L485] and [:L528-L529] see it. Between
      two Python objects they do not, so the aliasing is re-established at the
      head of both loading verbs by `_alias_enumerated_into_array`. Which view
      leads is settled by the frozen source, not chosen: the enumerated names are
      what a caller writes - all 52 references outside the copybook are SCREEN
      `using` clauses [irs/irs020.cbl:L472-L593], and SCREEN `using` is
      bidirectional - while NOTHING in the frozen codebase writes an array name
      except the bridge's own read-unload [common/irsfinalMT.cbl:L455-L456]. Full
      evidence and the R-3 argument are under TRANSLATION CORRECTIONS as C1.
    * COBOL `OCCURS` subscripts are 1-BASED and Python indexing is 0-BASED.
      `records/irs_final.py` states that the offset "belongs to whichever layer
      turns a position into a key value" - that is this module, and the
      conversion is made explicit at every site.

THIS BRIDGE HAS NO DELETE OF ANY KIND
=====================================
No `ba080`, no `ba085`, no `DELETE FROM` anywhere. Verified: the ONLY occurrence
of the token `delete` in `common/irsfinalMT.cbl` is inside a comment at [:L531],
`*> 1 = Primary, 2 = Abrev, 3 = Desc (NOT Delete function as can be dups)`. So
NO `delete` and NO `delete_all` behaviour is published here, and none may be
added (rule R-3). `dal/status.py` corroborates the shape independently: its
`FsReply.KEY_NOT_FOUND` documentation records that six bridges have no keyed
read at all and names `irsfinalMT` among them.

THE PUBLISHED FACADE SURFACE - SIX VERBS, NOT TWELVE
====================================================
This handler is reached through the IRS convention,
`copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob`, whose paragraph `acasirsub5.` [:L81]
sets `move 1 to File-Key-No.` and then issues the `CALL` [:L84-L91] with the
parameter order this module's :func:`dispatch` preserves exactly. That copybook
publishes SIX verbs and no more::

    acasirsub5-Open        [:L287]  fn-open  + fn-i-o
    acasirsub5-Open-Input  [:L293]  fn-open  + fn-input
    acasirsub5-Close       [:L299]  Access-Type = 0, fn-Close
    acasirsub5-Read-Next   [:L304]
    acasirsub5-Write       [:L309]
    acasirsub5-ReWrite     [:L314]

No open-output, no open-extend, no start, no delete, no delete-all and no
read-indexed. The four `open_*` functions below therefore exceed what the
facade publishes, and that is deliberate and faithful rather than invention:
the handler's own test is `if fn-open` [common/acasirsub5.cbl:L421], on
`File-Function` ALONE, so it CANNOT TELL THE FOUR ACCESS TYPES APART and
ignores all four identically. In particular `open_output` here does NOT
truncate the table - contrast `acas008`, where `Open-Output` means delete every
row [common/acas008.cbl:L313-L319].

The convention also adds a per-handler error check the General/Sales/Purchase
convention has no equivalent for: `irsub5-Check-4-Errors` [:L348-L353] is
performed ONLY after Open [:L291] and Open-Input [:L297], displays `IR915`,
performs `acasirsub5-Close` and transfers to `Open-Error-Continued` [:L355],
which ends in `goback.` [:L364] - a RETURN FROM THE PROGRAM OUTRIGHT, as
section 0.6.5 records. THAT RECOVERY BELONGS TO THE FACADE, NOT HERE:
:func:`dispatch` performs NO recovery and simply hands back the status pair,
exactly as the handler does.

THE ERROR-MESSAGE NAMESPACE, AND WHAT IT CORROBORATES
=====================================================
[common/acasirsub5.cbl:L121-L129] declares six messages, `IR901` and `IR902`
system-wide plus four module-specific::

    IR921  pic x(39)  "IR921 Failure to read Final File rec. !"   [:L126]
    IR922  pic x(32)  "IR922 Failure to read Final File"          [:L127]
    IR923  pic x(36)  "IR923 Failure to open o/p Final File"      [:L128]
    IR924  pic x(33)  "IR924 Failure to write Final File"         [:L129]

The `IR9xx` namespace is partitioned by module WITH GAPS: `acasirsub1` owns
906-910, `acasirsub3` owns 917-919, `acasirsub5` owns 921-924, and `acasirsub4`
owns NONE AT ALL; 903-905, 911-916 and 920 are unassigned. That inventory
corroborates why `copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob` has no error-check
paragraph for `acasirsub4`. `IR921` ends in `. !` - a trailing
space-exclamation the other three lack. All four messages are DISPLAY-ONLY and
reach only the flat-file path, so all four are deliberate omissions here; the
handler's own save/restore pair carries the comment
`*> These 2 for acasirsub3 & 5`, naming the family once more.

LOG IDENTITY - THE ONLY UNCOLLIDED FILE NUMBER IN THE FOLDER
============================================================
`move 1 to WS-Log-System` [common/acasirsub5.cbl:L158] and
`move 14 to WS-Log-File-No` [:L159] on the flat path; the RDB path bumps it with
`move 24 to WS-Log-File-no` [:L364]. The corrected folder-wide census - flat ->
RDB, with the log system in brackets::

    11 -> 21   acas005 (2), acas012 (3), acas022 (4), acasirsub1 (1)  four-way
    12 -> 22   acas015 (6), acas016 (3), acasirsub3 (1)               three-way
    12 -> 12   acas026 (4)                     no increment, unique
    13 -> 23   acas013 (6), acasirsub4 (1)                            two-way
    14 -> 24   acasirsub5 (1)                  SOLE OCCUPANT
    15 -> 25   acas008 (1), acas019 (3), acas029 (4)                  three-way

So `acasirsub5` is the ONLY handler whose file number is unique - every other
number needs the `(system, file)` pair to disambiguate. The bump to 24 happens
ONLY on the RDB path, because `ba010-Test-WS-Rec-Size` [:L358] contains nothing
but that move and the flat path performs `ba012-Test-WS-Rec-Size-2` directly
[:L180].

ANOMALY REGISTER - REPRODUCED, NEVER FIXED  (rule R-4)
======================================================
Rule R-4, verbatim: "There is no test suite: compiled COBOL execution is the
behavioral specification, defects included. A defect reproduced is correct; a
defect fixed is a failure." Section 0.7.4 C-4 adds the mechanism: "a comment at
each reproduction site citing the COBOL locator." A1 to A31 are this module's
register as enumerated in the migration brief; A32 to A47 were found while
reading the frozen source for this module and are new. Every entry below either
has a `[<path>:L<n>]` comment at its reproduction site, or - where it is
flat-file-only and therefore outside the RDB surface - is named here as a
deliberate omission with its locator.

    A1   A FAILED WRITE REPORTS SUCCESS. Handler [acasirsub5.cbl:L470-L483];
         bridge [irsfinalMT.cbl:L563, :L571-L573]. Never surfaced.
    A2   ONE `end-if.` CLOSES TWO NESTED `if`s, which is what makes the
         fall-through reachable [acasirsub5.cbl:L483].
    A3   `ar3 pic x(5)` SILENTLY DROPPED [irswsfinal.cob:L68]; absent from
         `irsfinalMT.cbl`, `acasirsub5.cbl` and `ACASDB.sql`.
    A4   AN ARRAY SUBSCRIPT TAKEN DIRECTLY FROM A DATABASE VALUE -
         `AR1 (HV-IRS-FINAL-ACC-REC-KEY)` where the host variable is `9(03)`
         and the array is 26 [irsfinalMT.cbl:L455-L456].
    A5   THE OFFENDING KEY VALUE BECOMES THE ERROR CODE on an out-of-range key,
         and `FS-Reply` is NOT set [irsfinalMT.cbl:L426-L428].
    A6   THE STATUS-SQUASHING LOOP - each iteration's failure is stashed and
         cleared, so only the LAST survives and the loop never stops early
         [irsfinalMT.cbl:L509-L516]. `ba070` SETS NO `WE-Error` OF ITS OWN -
         every one of its own status statements writes `FS-Reply` alone - but
         that does NOT mean a caller sees zero there. `bb200-Insert` performs
         `MYSQL-1210-COMMAND` [irsfinalMT.cbl:L655], which on a query failure
         performs `Mysql-1100-Db-Error`
         [copybooks/mysql-procedures.cpy:L166-L177], and THAT paragraph does
         `move 99 to fs-Reply` / `move 911 to We-Error` unconditionally
         [copybooks/mysql-procedures.cpy:L127-L128]. `ba070` then overwrites the
         `FS-Reply` (to 22 or 99) and leaves the 911 standing, and the squash
         saves and clears `FS-Reply` only. So a failed write returns
         `(<last FS-Reply>, 911)` - the 911 belonging to the shared DB-error
         paragraph rather than to this one, which is why `WE-Error` carries no
         information about WHICH row failed. Verified by ad-hoc test rather
         than assumed.
    A7   THE BLANK-SLOT SKIP IS COMMENTED OUT, so all 26 rows are always
         written, blank ones included [irsfinalMT.cbl:L477-L480].
    A8   A READ VERB THAT CREATES THE FILE and writes one all-spaces record when
         the open fails [acasirsub5.cbl:L255-L263]. FLAT-FILE ONLY =>
         DELIBERATE OMISSION.
    A9   CONTRADICTORY ANNOTATIONS ON THE IDENTICAL STATEMENT 11 LINES APART -
         `move 3 to WE-Error  *> NOT as in irsub5` [acasirsub5.cbl:L268] then
         `move 3 to WE-Error  *> as in irsub5` [:L279]. Both quoted verbatim;
         an ambiguity-document entry.
    A10  ALL FOUR RDB BAIL-OUTS SKIP THE CLOSE, leaking the cursor and the
         connection - read [acasirsub5.cbl:L437-L440, :L446-L449], write
         [:L463-L466], rewrite [:L489-L492] - while the write's own close is
         UNCONDITIONAL [:L471-L472]. Reproduced, leak included.
    A11  DEAD STATUS ASSIGNMENTS - `move 10 to FS-Reply WE-Error` then
         `move 3 to WE-Error`, so the effective flat-file EOF pair is
         `(10, 3)` [acasirsub5.cbl:L266-L268, :L278-L279]. FLAT-FILE ONLY.
    A12  `move 1 to WS-File-Key` IMMEDIATELY OVERWRITTEN by the descriptive
         string [acasirsub5.cbl:L295, :L297]. FLAT-FILE ONLY.
    A13  THE FLAT READ CLEARS `WE-Error` ONLY, NOT `FS-Reply`
         [acasirsub5.cbl:L296] - and, unlike `acasirsub3`, does NOT clear
         `Cobol-File-Status`, leaving the EOF latch set. FLAT-FILE ONLY.
    A14  THE WRITE-FAILURE BRANCH NEITHER CLOSES NOR EXITS while the
         open-failure branch does both [acasirsub5.cbl:L312-L322]. FLAT-FILE
         ONLY.
    A15  CODES 1 AND 2 ARE DISPATCHED BUT ARE NO-OPS that jump to `aa-Exit`,
         bypassing the logging hook [acasirsub5.cbl:L192-L199, :L334-L337].
    A16  `when 5` FALLS THROUGH TO `when 7` - one paragraph serves both on the
         flat path [acasirsub5.cbl:L202-L204].
    A17  ~35 LINES OF FULLY-FORMED COMMENTED-OUT OPEN/CLOSE carrying trace
         numbers 201/202 and status codes 35, 997 and 1, including a
         DOUBLY-COMMENTED dated line `*>*> 27/07/16 16:30 move zeros to
         FS-Reply WE-Error.` - `acasirsub3` has the same line doubly-commented
         and `acasirsub4:L287` has it singly-commented and LIVE
         [acasirsub5.cbl:L212-L246]. DELIBERATE OMISSION, inventoried here.
    A18  A LIVE `stop "Cobol File EOF"` in a block whose own comment says
         "should NOT occur" [acasirsub5.cbl:L265, :L272]. FLAT-FILE ONLY;
         never translated to `sys.exit`, `exit()` or `os._exit`.
    A19  HANDLER BAD-FUNCTION 999 VS BRIDGE 990 [acasirsub5.cbl:L331-L332;
         irsfinalMT.cbl:L580-L581] - the FOURTH confirmed pair with this
         disagreement, after `acas029`/`otm5MT`, `acasirsub3`/`irsdfltMT` and
         `acasirsub4`/`irspostingMT`. A folder-wide pattern, not reconciled.
    A20  THE SAME LITERAL COMPARED AT TWO WIDTHS IN ONE FILE - `"0  "` in the
         write [irsfinalMT.cbl:L491] and `"0   "` in the rewrite [:L558].
         Compared trimmed here; the discrepancy is recorded.
    A21  `if Testing-2` WHERE EVERY OTHER TEST IN BOTH FILES USES `Testing-1`
         [irsfinalMT.cbl:L550] - the same anomaly `irsdfltMT` carries.
    A22  NO `initialize` OF THE HOST-VARIABLE GROUP BEFORE THE WRITE LOOP,
         diverging from the convention section 0.6.2 describes and from
         `irsdfltMT:L625` [irsfinalMT.cbl:L468-L476]. `NOT NULL` is honoured
         anyway because all three host variables are assigned every iteration.
    A23  `KOR-offset`/`KOR-length` MOVED TO `K`/`L` AND NEVER USED
         [irsfinalMT.cbl:L330-L331, :L532-L533]; the rewrite's commented-out
         `*> Final-Record (K:L)` [:L541] shows where they were meant to go.
    A24  THE RELATION IS HARD-CODED `" > "` while `MOST-Relation` is declared
         [irsfinalMT.cbl:L131] and unused on this path [:L338].
    A25  A QUOTED 3-DIGIT LITERAL `"000"` COMPARED AGAINST A `tinyint(2)`
         COLUMN [irsfinalMT.cbl:L339]. Quoted as written; ambiguity Q-16.
    A26  `Ca-Process-Logs` IS ANNOTATED "Not called on DAL access as it does it
         already" [acasirsub5.cbl:L525] YET IS PERFORMED SIX TIMES in `ba015` -
         four of them in the read path alone [:L428, :L436, :L445, :L452,
         :L456, :L478, :L502].
    A27  A COMMENTED-OUT DUAL-WRITE HOOK in `aa-main-exit`
         [acasirsub5.cbl:L344-L346]. DELIBERATE OMISSION, recorded.
    A28  THE `IRS-` PREFIX IS ADDED AT THE BRIDGE [irsfinalMT.cbl:L172-L174]
         where `analMT` STRIPS a `WS-` prefix. Resolved from the dictionary.
    A29  COSMETIC EVIDENCE OF COPY-PASTE, preserved as citations: `function
         Length` then `function length` on adjacent lines
         [acasirsub5.cbl:L369, :L372]; seven exclamation marks [:L375]; `JC`
         without the s [:L415]; six question marks on the cursor comment
         [irsfinalMT.cbl:L388].
    A30  `initialize ... with filler` IN THE READ [irsfinalMT.cbl:L395] VS NO
         `initialize` IN THE WRITE [:L468-L476] - the two-semantics
         inconsistency.
    A31  A COMMENTED-OUT STATUS CLEAR INSIDE THE WRITE LOOP'S `Testing-1` BLOCK
         that would have masked errors when logging was on
         [irsfinalMT.cbl:L506-L507].

    NEW - FOUND WHILE READING THE FROZEN SOURCE FOR THIS MODULE
    A32  THE READ HAS THE SAME UNCONDITIONAL RESET AS THE REWRITE.
         `move zero to fs-reply WE-Error.` [irsfinalMT.cbl:L465] sits AFTER the
         loop with no guard, so EVERY in-loop `exit perform` - end of data
         [:L423], out-of-range key [:L433] and the zero-count branch [:L453] -
         has its status ERASED. Only the PRE-LOOP empty-table path, which jumps
         to `ba998-Free` [:L386], keeps its `(10, 10)`. So A5's
         `WE-Error = <key>` and the in-loop EOF are set and then wiped: BOTH
         fan-out verbs of this bridge end in an unconditional reset. Reproduced
         in full - the in-loop stores happen, because they leave the `WS-File-Key`
         tags `EOF`/`EOF2`/`EOF3` behind, and then the reset happens.
    A33  THE SAME STATUS-CLEAR IDIOM IS LIVE IN ONE LOOP AND DEAD IN THE OTHER.
         `move zeros to FS-Reply SQL-Err` / `move spaces to SQL-Msg` are LIVE
         in the read loop [irsfinalMT.cbl:L459-L460] and COMMENTED OUT in the
         write loop [:L506-L507] - that second one being A31. One file, one
         idiom, two comment states.
    A34  THE BRIDGE'S OWN COMMENT SAYS 32 ROWS IN A 26-ROW TABLE - "As this is
         for only one set of 32 rows we will skip this" [irsfinalMT.cbl:L232],
         copy-pasted from `irsdfltMT`. Corroborates the family.
    A35  BOTH EOF PATHS SET THE PAIR `(10, 10)`, not `WE-Error` alone -
         pre-loop [irsfinalMT.cbl:L383-L384] and in-loop [:L417].
    A36  THE UPDATE RENDERS THE SAME KEY TWO WAYS IN ONE STATEMENT. Its `SET`
         term takes `TRIM(WS-MYSQL-EDIT(18:03))`, which is UNPADDED - `"1"` -
         while its own `WHERE` takes `WS-Key`, `pic 99`, which is ZERO-PADDED -
         `"01"` [irsfinalMT.cbl:L681, :L542]. And the `SET` clause INCLUDES THE
         PRIMARY KEY, updating it to itself [:L677-L687].
    A37  A SECOND READ ON AN ALREADY-ACTIVE CURSOR BLANKS THE CALLER'S RECORD
         AND REPORTS SUCCESS. `if Cursor-Not-Active` [irsfinalMT.cbl:L328]
         guards the SELECT, `initialize Final-Record with filler` [:L395] is
         OUTSIDE that guard, and nothing on the success path clears
         `Most-Cursor-Set` [:L462-L466]. So a repeat call skips the SELECT,
         finds the stored result exhausted, takes the in-loop EOF - and then
         A32's unconditional reset turns `(10, 10)` into `(0, 0)`. The caller
         gets an all-spaces record and a success status. Ambiguity Q-17.
    A38  THE THREE FAN-OUT VERBS SKIP THE BRIDGE'S OWN END-OF-CALL LOGGING.
         Read [irsfinalMT.cbl:L466], write [:L517] and rewrite [:L574] all
         `go to ba999-exit`, jumping past `ba999-end`'s
         `if Testing-1 / perform Ca-Process-Logs` [:L600-L604]; open, close and
         bad-function go through it.
    A39  THE LOCK-RETRY LADDER IS RESET BUT CAN NEVER RUN.
         `move zero to WS-Mysql-Time-Step WS-SQL-Retry` [irsfinalMT.cbl:L469-L470,
         :L521-L522] resets state that `Mysql-1210-Command` cannot reach: its
         whole retry arm, including `perform Mysql-1300-DB-Error` and the
         `go to Mysql-1210-Command` re-issue, IS COMMENTED OUT
         [copybooks/mysql-procedures.cpy:L169-L175]. So there is no retry and
         no sleep - which is also what rule R-6 requires.
    A40  `MySQL_affected_rows` IS CALLED EVEN AFTER A FAILED STATEMENT.
         `Mysql-1210-Command` performs the error paragraph and then falls into
         `call "MySQL_affected_rows"` unconditionally
         [copybooks/mysql-procedures.cpy:L178], so `WS-MYSQL-Count-Rows` is
         always written and the `not = 1` test below always has a value.
    A41  THE PREDICATE IS STORED "For test logging" AND THEN WIPED BEFORE ANY
         LOG CALL CAN READ IT. `move ws-Where (1:J) to WS-Log-Where` carries
         that very comment [irsfinalMT.cbl:L349], and `move spaces to
         WS-Log-Where.` [:L393] clears it before the loop - so all four of the
         read's `Ca-Process-Logs` sites [:L421, :L431, :L451, :L458] log an
         EMPTY predicate. It survives on exactly ONE path: the empty-table arm,
         which leaves by `go to ba998-Free` [:L386] and reaches `ba999-end`'s
         log [:L602-L604] with [:L393] never executed. The rewrite has the same
         `*> For test logging` move [:L547] and no such wipe, so there the
         predicate does reach the log.
    A42  TWO DEAD DISJUNCTS IN THE READ'S END-OF-DATA TEST.
         `if return-code = -1 or A > 26 or = zero` [irsfinalMT.cbl:L415-L416]
         sits inside `perform varying A from 1 by 1 until A > 26` [:L396-L397],
         so `A > 26` and `A = zero` cannot hold in the body. Only
         `return-code = -1` can fire. Same class as A23's dead `K`/`L`.
    A43  THE READ'S IN-LOOP COUNT GUARD CANNOT FIRE ON THE NORMAL PATH.
         `if WS-MYSQL-Count-Rows = zero` [irsfinalMT.cbl:L437] reads the
         store-result snapshot's size, which `Mysql-1220-Store-Result` set once
         [copybooks/mysql-procedures.cpy:L191-L192] and which nothing in the
         loop re-reads; the zero case already left at [:L386]. Reproduced
         because a caller arriving on a stale cursor (A37) is the one way in.
    A44  A STALE WRITE FAILURE IS RE-REPORTED BY EVERY LATER CLEAN WRITE.
         `03 ws-saved-fs-reply pic 99.` [irsfinalMT.cbl:L147] is written at
         [:L510] and read at [:L514-L515], and IS NEVER CLEARED - not by
         `ba010-Initialise` [:L222-L230], not by `ba070`'s own status resets
         [:L472-L474], and nowhere else in the program: those four lines are its
         only references. `Program-Id. irsfinalMT.` [:L13] carries no `IS
         INITIAL`, so working storage persists across `CALL`s, and a single
         failed row in one write makes every subsequent write return that row's
         `FS-Reply` for the life of the run. Combined with A1 the effect
         inverts: the failing write reports success and a later clean one
         reports the failure.
    A45  `01 Old-File-Function pic 9 value zero.` [irsfinalMT.cbl:L144] IS
         DECLARED AND NEVER REFERENCED - that line is its only occurrence.
         Shared with `irsdfltMT`, the other array-fan-out bridge, presumably to
         remember a caller's function across the synthesised open and close that
         these two alone need. Modelled as nothing, because it does nothing.
    A46  THE REWRITE TRIPLE'S BRIDGE CALL IS ANNOTATED `*> write`
         [common/acasirsub5.cbl:L494], copied verbatim from the write triple's
         own `*> write` [:L468] when the block was duplicated - so the only
         inline label on the rewrite path names the wrong verb. Comment-only,
         same cosmetic family as A29, and recorded because rule R-5 asks that
         every difference be visible rather than tidied away in translation.
    A47  A SUCCESSFUL WRITE IS THE ONLY ONE OF THE THREE TRIPLES THAT LEAVES NO
         WS-File-Key OF ITS OWN. The read ends `move "Open, Read, Close" to
         WS-File-key` [common/acasirsub5.cbl:L455] and the rewrite ends
         `move "Open, Rewrite, Close" to WS-File-key` [:L501], but the write sets
         `"Open, Write failed, Close"` [:L477] ONLY inside its failure branch and
         its `else` goes straight to `ba-RDBMS-Exit` [:L481-L482]. So a clean
         write returns with the key still reading `"CLOSE IRS FINAL"`, which
         `ba030-Process-Close` put there [common/irsfinalMT.cbl:L307] - the one
         disposition of the three whose log record does not name the operation
         that produced it. Reproduced as written; found by ad-hoc test, which
         asserted the symmetric value and was wrong to.

WHAT IS NOT REPRODUCED, AND WHY  (rule R-5: omissions recorded as omissions)
===========================================================================
    * THE ENTIRE FLAT-FILE PATH [common/acasirsub5.cbl:L180-L348]. Rule R-1
      makes this module SQL-only, and section 0.2.1.1 scopes the migration to
      the RDB path. With it go A8, A11, A12, A13, A14 and A18, plus the
      `fd Final-File.`/`01 Record-5 pic x(655)` blob [:L102-L104] and the whole
      of `aa040-Process-Read-Next` [:L248-L299] and `aa070-Process-Write`
      [:L301-L325].
    * THE ~35 DEAD LINES OF `aa020-Process-Open`/`aa030-Process-Close`
      [:L212-L246] - A17 - and the commented-out dual-write hook [:L344-L346] -
      A27. Representation-only; section 0.1.2 lists exactly this class.
    * ALL PRESENTATION. `display IR9xx ... with foreground-color 4`,
      `display Display-Blk at 2301`, `display IR901 at 2401` and
      `accept Accept-Reply at 2433` [:L380-L392] plus the bridge's
      `display Display-Message-1 with erase eos` [irsfinalMT.cbl:L369, :L551].
      Section 0.3.4's three-way rule applies: these are diagnostics with no
      database effect, so they become log records; the CONTROL TRANSFER that
      follows the record-size display IS preserved [:L393].
    * `Ca-Process-Logs` [:L525, irsfinalMT.cbl:L719-L723]. Both paragraphs do
      nothing but `call "fhlogger"`, and `common/fhlogger.cbl` is out of scope
      per section 0.2.2, so rule R-1 forbids the call. The ~six handler sites
      and the bridge's own become Python log records at debug level. A26
      records the self-contradiction in its comment.
    * THE `stop "Cobol File EOF"` [:L272]. Flat-file only; and a process
      terminator has no place in a library.

TRANSLATION CORRECTIONS - WHERE PYTHON NEEDS A STATEMENT COBOL DID NOT
======================================================================
A translation correction is the opposite of an anomaly. An anomaly is behaviour
the compiled program HAS and this module reproduces; a correction is behaviour
the compiled program has FOR FREE, from a language feature Python lacks, that
this module must therefore write out by hand. Correcting one is not "fixing a
defect" under rule R-4 - failing to write it is the defect, because the compiled
program's behaviour would not be reproduced. Each is numbered `Cn`, cited at its
site, and listed here. This module has ONE.

    C1  `REDEFINES` IS ONE BYTE AREA, AND PYTHON HAS TWO OBJECTS. The frozen
        record declares each array twice - the enumerated group `03 ar1-fields.`
        with `05 ar1-1 ... ar1-26 pic x(24)` [copybooks/irswsfinal.cob:L8-L34],
        then `03 filler redefines ar1-fields.` with `05 ar1 pic x(24) occurs 26`
        [:L35-L36]; and the same pair for `ar2` [:L38-L64, :L65-L66]. In the
        compiled program `ar1-7` and `AR1 (7)` ARE THE SAME TWENTY-FOUR BYTES, so
        a write through either name is instantly visible through the other and no
        statement anywhere synchronises them - there is nothing to synchronise.
        Section 0.3.1 requires each `REDEFINES` to be modelled as its own view
        class, so `records/irs_final.py` publishes `Ar1Fields`/`Ar1View` and
        `Ar2Fields`/`Ar2View` as four independent dataclasses. That is correct as
        a layout model and inert as a storage model: a caller writing
        `final.ar1_fields.ar1_7` leaves `final.ar1_view.ar1[6]` untouched.

        WHICH DIRECTION, AND WHY IT IS NOT A GUESS. The frozen codebase is
        unambiguous about who writes which name. Every reference to an enumerated
        name outside the copybook - all fifty-two of them - is a SCREEN SECTION
        `using` clause on the Finished Accounts Setup screen
        [irs/irs020.cbl:L472-L593], and SCREEN `using` is bidirectional, so those
        are the names the OPERATOR writes. The array names appear in exactly four
        places: this bridge's read-unload [common/irsfinalMT.cbl:L455-L456], its
        write-load [:L484-L485] and rewrite-load [:L528-L529], and two read-only
        consumers [irs/irs020.cbl:L1018-L1021, irs/irs060.cbl:L1184-L1187].
        NOTHING in the frozen codebase writes an array name except this bridge's
        own read-unload. So the enumerated view is the caller's write path and the
        array view is the bridge's, and the aliasing that has to be re-established
        runs enumerated -> array, at the two load boundaries.

        WHERE IT IS APPLIED. `_alias_enumerated_into_array` is called at the head
        of `write` and of `rewrite`, immediately before the loop that reproduces
        `perform varying A from 1 by 1` [:L476, :L524]. The READ direction needs
        nothing: `read` already writes both views, matching `initialize
        Final-Record with filler` [:L395] followed by `move HV-IRS-AR1 to
        AR1 (...)` [:L455] over shared bytes.

        WHY THIS IS NOT AN ADDED VALIDATION (rule R-3). It adds no bounds check,
        no field, no column and no width; it does not skip blank slots - A7 keeps
        all twenty-six rows written - and it does not touch `ar3`, which stays
        silently dropped per A3. It restores an aliasing property the compiled
        program already has, and nothing more. A per-slot guard makes a blank
        enumerated slot yield to whatever the array view already holds, so the
        array-only calling pattern the read path itself produces is unchanged;
        without the guard, reading a table and rewriting it would blank every row.

RULE COMPLIANCE  (Agent Action Plan section 0.7.2)
==================================================
There is NO user rules document for this project - `review_rules` reports "No
user rules provided." The six binding rules are the ones section 0.7.2
enumerates, and each is honoured here as follows.

R-1, NO COBOL AT RUNTIME. No `subprocess`, `os.system`, `os.popen`, `os.exec*`,
`ctypes` or `cffi`; no `cobc`, `cobcrun` or `cobmysqlapi.o`; no `import
harness`; and no `fhlogger`. Every construct is reimplemented natively: the
`SELECT`/`INSERT`/`UPDATE` the bridge assembles as literal text become bound
statements here, and the handler's synthesised open/verb/close triples become
Python calls.

R-2, ZERO BINARY FLOATING POINT. There is no numeric DATA column in this table,
so no `Decimal` is required and no monetary value passes through - but nothing
here touches `float`, `complex`, `math`, builtin `round`, builtin `abs`,
`numpy` or `pandas` either. The one numeric value, the subscript-derived key, is
an `int` and is rendered to text by the two functions that reproduce the
bridge's own two renderings.

R-3, NOTHING ADDED. Only `SELECT`, `INSERT` and `UPDATE` are issued - and no
`DELETE`, because the bridge has none. No DDL of any kind, no index, view or
trigger, no Alembic; no `sessionmaker`, `Session`, `declarative_base`,
`DeclarativeBase`, `relationship`, `Mapper`, `registry` or `MetaData`; no
`threading`, `asyncio`, `multiprocessing`, `concurrent.futures` or pooling; and
no `COMMIT`, `ROLLBACK` or `START TRANSACTION` - `dal/connection.py` owns the
autocommit policy. No validation is added: no bounds check the source lacks, no
skip of blank array slots, no `ar3` in any statement, and no check that the rows
returned are contiguous or complete. Correction C1 is not an exception to this:
it re-establishes the byte aliasing `redefines` already gives the compiled
program, and adds no field, width, column, check or skip.

R-4, ANOMALIES REPRODUCED. The forty entries above, each with a locator at its
reproduction site or a named omission here.

R-5, FULL TRACEABILITY. A named function per bridge and handler paragraph, the
`CALL` parameter order preserved exactly, :data:`COLUMNS` and every width read
from :mod:`acas_posting.dictionary.loader` rather than transcribed, and a footer
mapping every paragraph of both files to its Python function with the `GO TO`
class annotated at each transfer site. The one statement that has no COBOL
counterpart is numbered and indexed rather than left unexplained - see
TRANSLATION CORRECTIONS above and item 10 of the traceability footer.

R-6, COMPILED BEHAVIOUR IS THE TIE-BREAKER. No clock, no `random`, no `uuid`,
no `os.urandom` and no `time.sleep` - the frozen bridge cannot sleep either, per
A39. The bridge's explicit `ORDER BY` is reproduced because it is in the source;
it exists for REASSEMBLY rather than for determinism, and section 0.6.6's "no
ordering nondeterminism from a secondary index" still holds because the ordering
column is the primary key. Two questions are marked rather than guessed.

AMBIGUITIES, ARBITRATED AGAINST COMPILED BEHAVIOUR  (rule R-6)
==============================================================
Q-16 and Q-17 are the next free numbers in the migration's shared register -
`cobol/usage` claimed Q-5.1 to Q-5.3, `cobol/move` Q-9 to Q-14 and
`programs/gl071_batch_sort` Q-15. BOTH ARE NOW RESOLVED, and neither result
changes a line of code - which is what arbitrating rather than guessing was for.

    Q-16  WHAT THE `tinyint(2) unsigned` COLUMN ACTUALLY HOLDS, AND WHAT THE
          QUOTED PREDICATE ACTUALLY COMPARES.
          RESOLVED BY MEASUREMENT against MariaDB 10.11.7, the server version the
          frozen schema records as its producer [mysql/ACASDB.sql:L1, :L5], with
          the frozen `ENGINE=InnoDB` and the server's DEFAULT `sql_mode`, which
          carries `STRICT_TRANS_TABLES` and is what the bridge's C interface gets.
          The dump's own `SQL_MODE='NO_AUTO_VALUE_ON_ZERO'` [mysql/ACASDB.sql:L21]
          does not change it: session-scoped, measured to leave
          `@@global.sql_mode` untouched, restored at [:L1451], and inert anyway
          because the schema's only `AUTO_INCREMENT` column belongs to the
          out-of-scope `STOCKAUDIT-REC` [mysql/ACASDB.sql:L1107].
          THE STORE: the premise that a `9(03)` host variable is wider than a
          "two-digit" column is WRONG - `(2)` IS A DISPLAY WIDTH, NOT A
          CONSTRAINT. `tinyint unsigned` holds 0..255, measured, so every
          subscript 1..26 this table can index stores exactly, and the host
          variable is wider only over 256..999, where the server raises ERROR
          1264, SQLSTATE 22003, and writes nothing. The write path cannot reach
          even that, because the subscript is bounded by the `occurs 26`.
          THE PREDICATE: the coercion is NUMERIC, proved with a probe whose two
          readings disagree - against a `tinyint(2) unsigned` column holding 9 and
          10, `k > "10"` returned NO rows and `k < "10"` returned 9, the opposite
          of the lexical answer, and `9 > "10"` evaluates 0 while `"9" > "10"`
          evaluates 1. Measured on this shape, `> "000"` matched every one of
          {1,2,9,10,31,32}, identically to `> 0`. So `"000"` is the number 0 and
          the sequential predicate admits every legal key.
          Both renderings stay exactly as written; nothing is normalised - now on
          evidence rather than pending it.

    Q-17  WHAT THE TABLE HOLDS, AND WHAT A READ RETURNS, WHEN FEWER THAN 26 ROWS
          EXIST.
          RESOLVED FROM THE FROZEN SOURCE - no oracle run needed, because the
          question that remained was about INTENT and not behaviour, and R-4 makes
          intent irrelevant: a defect reproduced is correct. The note used to say
          "no reading of the source settles whether a caller was ever meant to be
          able to tell", which is true and is not a behavioural question. THE
          BEHAVIOUR IS FULLY DETERMINED: the bridge tolerates a short table by
          design - "having initialised record as some rows may not be present"
          [irsfinalMT.cbl:L320]; the exhaustion arm sets `(10, 10)` on its way out
          [:L417]; and `move zero to fs-reply WE-Error` [:L465] is UNCONDITIONAL
          (A32), so it erases that. The caller therefore observes `(0, 0)` -
          success - together with a record whose unfilled slots hold the spaces
          `initialize Final-Record with filler` [:L395] put there, and has NOTHING
          to distinguish it from a full read. A repeat read compounds it (A37).
          That is exactly what this module already does; nothing about it was
          waiting on a measurement.
          Note the state after ANY write is DENSE: A7 keeps the blank-slot skip
          commented out, so a written table always holds exactly 26 rows, blanks
          stored as spaces rather than absent - which matters to any scenario diff
          that expects "only the populated rows", and which means Q-17 bites only
          on tables seeded or loaded outside this handler.

WHAT THIS MODULE MAY IMPORT, AND WHAT IT MUST NOT  (section 0.4.3)
==================================================================
May: `dal.connection`, `dal.status`, `dal.cursor_state`, exactly ONE entity
record module - `records.irs_final` - plus the shared linkage records, and
`dictionary.loader`. Must not: `programs`, `cli`, ANY OTHER `dal.acas*` (only
`facade.py` may know every handler), `harness`, and - specifically -
`acas_posting.cobol.*`: character padding and `occurs` semantics belong to the
record layer, so the widths and occurrence counts used below are READ OFF the
descriptors `records.irs_final` already publishes - `Ar1View.FIELDS`,
`Ar2View.FIELDS` and `IrsFinalRecord.FIELDS` - and off the dictionary, never
written as a literal and never obtained by importing `cobol.field` or
`cobol.move`. The descriptor OBJECTS are used; the descriptor CLASS is not
imported, so the layering boundary holds while the metadata still comes from the
one place that owns it.

WHERE THE PLAN'S LINE NUMBERS DIFFER FROM THE FROZEN SOURCE
===========================================================
Every citation in this module was read from the frozen files rather than copied
from the brief, and several of the brief's numbers are off by a few lines. The
differences are recorded here so they are not rediscovered as defects:
the handler's messages are at [common/acasirsub5.cbl:L121-L129] and not
L118-L123; `copy "irswsfinal.cob"` is at [:L133] and not L129; the
`Procedure Division Using` list spans [:L143-L149] and not L147-L152; the log
identity is at [:L158-L159] and not L156-L157; the dead open/close block is
[:L212-L246]; the write paragraph is [:L301-L325]; the single `end-if.` of A2 is
at [:L483] and not L481; the second bad-function site is [:L506-L510]; and
`ba020-Call-DAL` is [:L512-L517]. On the bridge side the write's status-squash
is [common/irsfinalMT.cbl:L509-L516] and not L510-L517, and its unconditional
reset is [:L571-L573] as cited. The brief's own count of "thirty-one" anomalies
is likewise low by sixteen, per A32 to A47 above.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from acas_posting.dal.connection import (
    TransportSecurity,
    cobol_string_delimited_by_space,
    execute_statement,
    load_rdb_data_once,
    mysql_1000_open,
    mysql_1980_close,
    quote_identifier,
)
from acas_posting.dal.cursor_state import (
    SEQUENTIAL_READ_START,
    CursorSlot,
    CursorState,
    CursorStateTable,
    DatabaseCursor,
    KeyOfReference,
    key_of_reference,
)
from acas_posting.dal.status import (
    SQL_ERR_WIDTH,
    SQL_MSG_WIDTH,
    SQL_STATE_WIDTH,
    AccessType,
    DbErrorStatus,
    FileFunction,
    FsReply,
    LogSystem,
    WeError,
    end_of_file_status,
    is_duplicate_key_bridge_level,
    log_file_handler_record,
    mysql_1100_db_error,
)
from acas_posting.dictionary import loader
from acas_posting.records.file_access import FileAccess
from acas_posting.records.file_defs import FileDefs
from acas_posting.records.irs_final import Ar1View, Ar2View, IrsFinalRecord
from acas_posting.records.system_record import SystemRecord
from acas_posting.records.test_data_flags import AcasDalCommonData

if TYPE_CHECKING:  # pragma: no cover - typing only, never a runtime dependency
    from mysql.connector.abstracts import MySQLConnectionAbstract


__all__: Final[tuple[str, ...]] = (
    # Ordered isort-style to match `dal/status.py` and `dal/connection.py`: the
    # frozen tables and constants first, then the behaviour, each group sorted.
    # Neither this ordering nor theirs is observable.
    "ARRAY_LENGTH",
    "BRIDGE_BAD_FUNCTION",
    "BRIDGE_DISPATCHED_FUNCTIONS",
    "COLUMNS",
    "DUP_KEY_SQLSTATE",
    "DUP_KEY_SQL_ERRORS",
    "FD_RECORD_BYTES",
    "FS_REPLY_DUPLICATE",
    "FS_REPLY_GENERAL",
    "HANDLER_BAD_FUNCTION",
    "HANDLER_DISPATCHED_FUNCTIONS",
    "KEY_COUNT",
    "PRIMARY_KEY",
    "PUBLISHED_FACADE_VERBS",
    "RECORD_SIZE_ERROR",
    "TABLE",
    "TRACE_DEAD_CLOSE",
    "TRACE_DEAD_OPEN",
    "TRACE_READ_NEXT",
    "TRACE_WRITE",
    "WE_ERROR_UNOBSERVABLE_REWRITE",
    "WS_LOG_FILE_NO_FLAT",
    "WS_LOG_FILE_NO_RDB",
    "WS_LOG_SYSTEM",
    "WS_RECORD_BYTES",
    "acasirsub5_close",
    "acasirsub5_open",
    "acasirsub5_open_input",
    "acasirsub5_read_next",
    "acasirsub5_rewrite",
    "acasirsub5_write",
    "close",
    "dispatch",
    "insert_statement",
    "open_",
    "open_extend",
    "open_input",
    "open_output",
    "read_next",
    "reset",
    "rewrite",
    "select_statement",
    "select_where",
    "update_statement",
    "update_where",
    "write",
)

_LOG: Final[logging.Logger] = logging.getLogger(__name__)


#  THE FROZEN IDENTITY OF THIS HANDLER


#: `TABLE=IRSFINAL-REC` as the `.scb` declares it in its embedded directive
#: [common/irsfinalMT.scb:L163-L166] and the generated bridge repeats it in
#: every statement it assembles [common/irsfinalMT.cbl:L359, :L620, :L673].
TABLE: Final[str] = "IRSFINAL-REC"

#: `PRIMARY KEY (`IRS-FINAL-ACC-REC-KEY`)` [mysql/ACASDB.sql:L218]. THE COLUMN
#: EXISTS IN NO COPYBOOK - it is the `occurs` subscript, per the bridge's own
#: `*> KEY = table position` [common/irsfinalMT.cbl:L455]. Read from the
#: dictionary rather than written out, so the assertion is checkable.
PRIMARY_KEY: Final[str] = loader.table_for(TABLE).primary_key

#: `03 keyOfReference occurs 1 indexed by KOR-x1.`
#: [common/irsfinalMT.cbl:L119] - ONE key of reference, so `set KOR-x1 to 1`
#: [:L329, :L531] is the only positioning this bridge can do. There is no
#: alternate key and no keyed read at all.
KEY_COUNT: Final[int] = 1

#: The three columns in SCHEMA ORDINAL ORDER [mysql/ACASDB.sql:L215-L217],
#: taken from the generated dictionary rather than transcribed - which is what
#: section 0.8.1's "Data dictionary first" directive requires, and what catches
#: the `IRS-` prefix the bridge ADDS (anomaly A28) without anyone having to
#: remember it.
COLUMNS: Final[tuple[str, ...]] = tuple(
    entry.column.name
    for entry in sorted(
        loader.entries_for_table(TABLE), key=lambda entry: entry.column.ordinal
    )
)

#  THE RECORD LAYER'S OWN DESCRIPTORS - the ONLY source of widths and counts
#  used here. The descriptor OBJECTS are consumed; `cobol.field` is never
#  imported, so section 0.4.3's layering rule holds while the metadata still
#  comes from the module that owns it. Each descriptor's `dictionary_key` ties
#  it back to the generated artifact, satisfying rule R-5 mechanically.

#: `05 ar1 pic x(24) occurs 26.` [copybooks/irswsfinal.cob:L36] - the redefining
#: array view, which is the operand the bridge names. `dictionary_key` is
#: `IRSFINAL-REC.IRS-AR1`.
_AR1_DESCRIPTOR: Final = Ar1View.FIELDS[0]

#: `05 ar2 pic x occurs 26.` [copybooks/irswsfinal.cob:L66]. `dictionary_key` is
#: `IRSFINAL-REC.IRS-AR2`. Together with `IRS-AR2 char(1)` this is a 26-element
#: single-character flag array.
_AR2_DESCRIPTOR: Final = Ar2View.FIELDS[0]

#: `03 ar3 pic x(5).` [copybooks/irswsfinal.cob:L68]. Held ONLY so its five bytes
#: can be counted into the record length and so `initialize Final-Record with
#: filler` [common/irsfinalMT.cbl:L395] can blank it. IT REACHES NO STATEMENT -
#: anomaly A3 - and `loader.cite("Final-Record.ar3")` renders `bridge=absent
#: column=absent` to say so from the dictionary's side.
_AR3_DESCRIPTOR: Final = next(
    descriptor
    for descriptor in IrsFinalRecord.FIELDS
    if descriptor.name == "ar3"
)

#: `05 ar1 pic x(24) occurs 26.` [copybooks/irswsfinal.cob:L36] and
#: `05 ar2 pic x occurs 26.` [:L66]. ONE COBOL RECORD IS THIS MANY TABLE ROWS.
#:
#: THE BOUND IS CORRECT HERE, AND THAT IS THE POINT. The bridge guards the
#: subscript with `= zero or > 26` [common/irsfinalMT.cbl:L426] and loops
#: `until A > 26` [:L397, :L476, :L524], both matching `occurs 26` exactly. Its
#: sibling does not: `common/irsdfltMT.cbl:L575` guards `= zero or > 32` against
#: `03 Def-Group occurs 33.` [copybooks/irswsdflt.cob:L9], so entry 33 is never
#: written and is rejected on read - and the maintainer's own copybook comment
#: records that entry 33 was added specifically "to support temp. default 33 in
#: postings (irs030)" [copybooks/irswsdflt.cob:L7], so the off-by-one defeats the
#: very feature the array was widened for. `irsfinalMT` being right is what makes
#: that a defect rather than a convention, and it is why the bound below is NOT
#: to be "tidied" to `>= 26` or `> 25`.
#:
#: Read off the record layer's own descriptors, both of which must agree.
ARRAY_LENGTH: Final[int] = _AR1_DESCRIPTOR.occurs

#: `move function Length ( Final-Record ) to A` [common/acasirsub5.cbl:L369-L371]
#: - the `A` operand of the record-size gate, COMPUTED from the record layer's
#: descriptors. Each `redefines` pair contributes its bytes ONCE, giving
#: 24 * 26 + 1 * 26 + 5 = 624 + 26 + 5 = 655, which is exactly the copybook's own
#: `*> rec 655 bytes` [copybooks/irswsfinal.cob:L6].
WS_RECORD_BYTES: Final[int] = (
    _AR1_DESCRIPTOR.byte_length * _AR1_DESCRIPTOR.occurs
    + _AR2_DESCRIPTOR.byte_length * _AR2_DESCRIPTOR.occurs
    + _AR3_DESCRIPTOR.byte_length
)

#: `01 Record-5 pic x(655).` [common/acasirsub5.cbl:L104] - the flat, structureless
#: FD blob, and the `B` operand of the gate [:L372-L374]. Written out as the
#: literal the FD declares rather than derived, so that the gate compares two
#: INDEPENDENTLY SOURCED numbers exactly as the frozen `if A < B` [:L375] does;
#: deriving both from one expression would make the comparison vacuous. The guard
#: below then checks the two sources against each other at import time.
FD_RECORD_BYTES: Final[int] = 655

if WS_RECORD_BYTES != FD_RECORD_BYTES:  # pragma: no cover - frozen sources agree
    # A CROSS-SOURCE CONSISTENCY CHECK ON FROZEN DECLARATIONS, not a validation of
    # accounting data - rule R-3 forbids the latter and says nothing about the
    # former, and section 0.4.1.6 asks the dictionary generator to do exactly this
    # kind of "present in one source and absent from another" flagging. If it ever
    # fires, a copybook and an FD have drifted and the record-size gate below
    # would start rejecting every call, which is far harder to diagnose here.
    raise ValueError(
        f"{TABLE}: [copybooks/irswsfinal.cob] sums to {WS_RECORD_BYTES} bytes "
        f"but [common/acasirsub5.cbl:L104] declares {FD_RECORD_BYTES}"
    )

#: `move 1 to WS-Log-System` [common/acasirsub5.cbl:L158], with the frozen
#: comment `*> 1 = IRS, 2=GL, 3=SL, 4=PL, 5=Stock - used in FH logging`.
WS_LOG_SYSTEM: Final[LogSystem] = LogSystem.IRS

#: `move 14 to WS-Log-File-No` [common/acasirsub5.cbl:L159] - the flat-file
#: identity, and the ONLY UNCOLLIDED FILE NUMBER IN THE FOLDER. Kept even though
#: the flat path is not migrated, because the pair `(14, 24)` is what identifies
#: this handler in the file-handler log and the census in the module docstring
#: rests on it.
WS_LOG_FILE_NO_FLAT: Final[int] = 14

#: `move 24 to WS-Log-File-no.  *> for FHlogger` [common/acasirsub5.cbl:L364] -
#: the RDB identity, written on EVERY RDB call because `ba010-Test-WS-Rec-Size`
#: [:L358] contains nothing else and is reached by fall-through.
WS_LOG_FILE_NO_RDB: Final[int] = 24


#  TRACE NUMBERS - `WS-No-Paragraph`, THE SMALLEST SET IN THE FOLDER


#: `move 203 to WS-No-Paragraph` [common/acasirsub5.cbl:L253] - the flat read.
TRACE_READ_NEXT: Final[int] = 203

#: `move 206 to WS-No-Paragraph` [common/acasirsub5.cbl:L305] - the flat write.
TRACE_WRITE: Final[int] = 206

#: 201 and 202 survive ONLY inside the ~35 commented-out lines of
#: `aa020-Process-Open`/`aa030-Process-Close` [common/acasirsub5.cbl:L212-L246],
#: so this handler uses just TWO of the standard 201..208 band - the smallest set
#: in the folder, matching `acasirsub3`. Named so the gap is a recorded fact
#: rather than an apparent omission. Anomaly A17.
TRACE_DEAD_OPEN: Final[int] = 201
TRACE_DEAD_CLOSE: Final[int] = 202

#: `move <n> to ws-No-Paragraph` inside the BRIDGE, which keeps its own,
#: unrelated numbering: 1 open [common/irsfinalMT.cbl:L287], 2 close [:L306],
#: 3 the select [:L350], 4 the fetch loop [:L394], 10 the insert loop [:L475],
#: 17 the update loop [:L523] and 20 `ba998-Free` [:L589].
_BRIDGE_TRACE_OPEN: Final[int] = 1
_BRIDGE_TRACE_CLOSE: Final[int] = 2
_BRIDGE_TRACE_SELECT: Final[int] = 3
_BRIDGE_TRACE_FETCH: Final[int] = 4
_BRIDGE_TRACE_INSERT: Final[int] = 10
_BRIDGE_TRACE_UPDATE: Final[int] = 17
_BRIDGE_TRACE_FREE: Final[int] = 20


#  STATUS CODES


#: `if SQL-Err (1:4) = "1062" or = "1022"` [common/irsfinalMT.cbl:L495-L496],
#: both commented `*> Dup key (rec already present)`.
DUP_KEY_SQL_ERRORS: Final[tuple[str, ...]] = ("1062", "1022")

#: `or Sql-State = "23000"` [common/irsfinalMT.cbl:L497].
DUP_KEY_SQLSTATE: Final[str] = "23000"

#: `move 22 to fs-reply` [common/irsfinalMT.cbl:L498].
FS_REPLY_DUPLICATE: Final[FsReply] = FsReply.DUPLICATE_KEY

#: `move 99 to fs-reply` [common/irsfinalMT.cbl:L500, :L562], both carrying the
#: maintainer's `*> this may need changing for val in WE-Error!!`.
FS_REPLY_GENERAL: Final[FsReply] = FsReply.ERROR

#: `move 994 to WE-Error` [common/irsfinalMT.cbl:L563] - AND IT CAN NEVER BE
#: SEEN. The unconditional four-field reset eight lines later [:L571-L573]
#: erases it on every path out of `ba090-Process-Rewrite`. Named, set at its
#: site, and then erased at its site, because that is anomaly A1 and rule R-4
#: makes reproducing it mandatory.
WE_ERROR_UNOBSERVABLE_REWRITE: Final[int] = int(WeError.REWRITE_SQLSTATE_NOT_00000)

#: `move 999 to WE-Error.` / `move 99 to fs-reply.` - the HANDLER's bad-function
#: pair, at both of its sites [common/acasirsub5.cbl:L331-L332, :L508-L509].
HANDLER_BAD_FUNCTION: Final[int] = int(WeError.NOT_USED)

#: `move 990 to WE-Error.` / `move 99 to Fs-Reply.` - the BRIDGE's bad-function
#: pair [common/irsfinalMT.cbl:L580-L581]. THE TWO DISAGREE, and the
#: disagreement is not reconciled: anomaly A19 records it as the fourth
#: confirmed handler/bridge pair with exactly this mismatch. Only the handler's
#: pair can reach a caller, because the bridge is never asked for a code outside
#: the five it dispatches.
BRIDGE_BAD_FUNCTION: Final[int] = int(WeError.UNKNOWN_UNEXPECTED)

#: `move 901 to WE-Error` / `move 99 to fs-reply`
#: [common/acasirsub5.cbl:L376-L377], the record-size gate's pair. Its own
#: comment: `*> 901 Programming error; temp rec length is wrong caller must stop`.
RECORD_SIZE_ERROR: Final[int] = int(WeError.RECORD_SIZE_MISMATCH)

#: `evaluate File-Function` in the HANDLER [common/acasirsub5.cbl:L191-L207] -
#: five codes and no more. NO 4, NO 8, NO 9.
HANDLER_DISPATCHED_FUNCTIONS: Final[tuple[FileFunction, ...]] = (
    FileFunction.OPEN,
    FileFunction.CLOSE,
    FileFunction.READ_NEXT,
    FileFunction.WRITE,
    FileFunction.RE_WRITE,
)

#: `evaluate File-Function` in the BRIDGE [common/irsfinalMT.cbl:L239-L252] -
#: THE SAME FIVE, which makes this the only handler/bridge pair in the folder
#: where both sides agree on a reduced code set.
BRIDGE_DISPATCHED_FUNCTIONS: Final[tuple[FileFunction, ...]] = (
    HANDLER_DISPATCHED_FUNCTIONS
)

#: The verbs `copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob` actually publishes for
#: this handler - six, not twelve [:L287, :L293, :L299, :L304, :L309, :L314].
#: Published as data so `facade.py` can build the handler-named alias set from
#: the frozen list instead of guessing at the usual twelve.
PUBLISHED_FACADE_VERBS: Final[tuple[str, ...]] = (
    "acasirsub5-Open",
    "acasirsub5-Open-Input",
    "acasirsub5-Close",
    "acasirsub5-Read-Next",
    "acasirsub5-Write",
    "acasirsub5-ReWrite",
)



#  DERIVED WIDTHS AND THE FROZEN-SOURCE CROSS-CHECK


#: `pic x(24)` - the receiving width of one `ar1` entry, and the width of
#: `HV-IRS-AR1 PIC X(24)` [common/irsfinalMT.cbl:L173] and of
#: `IRS-AR1 char(24)` [mysql/ACASDB.sql:L216]. All three agree; there is NO
#: 24-to-32 width drift here of the kind `nominalMT` carries at
#: [common/nominalMT.cbl:L299].
_AR1_WIDTH: Final[int] = _AR1_DESCRIPTOR.byte_length

#: `pic x` - one character, matching `HV-IRS-AR2 PIC X(1)`
#: [common/irsfinalMT.cbl:L174] and `IRS-AR2 char(1)` [mysql/ACASDB.sql:L217].
_AR2_WIDTH: Final[int] = _AR2_DESCRIPTOR.byte_length

#: `pic x(5)` [copybooks/irswsfinal.cob:L68]. Used ONLY to blank the field.
_AR3_WIDTH: Final[int] = _AR3_DESCRIPTOR.byte_length

#: What `initialize Final-Record with filler.` [common/irsfinalMT.cbl:L395]
#: leaves in each member: `initialize` sets an alphanumeric item to SPACES, and
#: `with filler` extends that to the two unnamed `redefines` groups as well. Not
#: `None`, ever - section 0.6.2, verbatim: "unset fields become zero or space
#: rather than SQL `NULL` ... the Python layer must default rather than omit".
_AR1_BLANK: Final[str] = " " * _AR1_WIDTH
_AR2_BLANK: Final[str] = " " * _AR2_WIDTH
_AR3_BLANK: Final[str] = " " * _AR3_WIDTH

if _AR2_DESCRIPTOR.occurs != ARRAY_LENGTH:  # pragma: no cover - frozen metadata
    # A CROSS-SOURCE CONSISTENCY CHECK, NOT A DATA VALIDATION. Rule R-3 bars
    # added validations of accounting data; this compares two FROZEN
    # DECLARATIONS - `occurs 26` at [copybooks/irswsfinal.cob:L36] and at [:L66]
    # - against each other. The `irsdfltMT` off-by-one documented on
    # `ARRAY_LENGTH` is exactly what happens when a bound and its array are
    # allowed to disagree unnoticed, so the disagreement is made loud here
    # rather than left to be discovered as wrong data.
    raise ValueError(
        f"{TABLE}: the two occurs clauses of copybooks/irswsfinal.cob disagree "
        f"- ar1 declares {ARRAY_LENGTH} at L36 and ar2 declares "
        f"{_AR2_DESCRIPTOR.occurs} at L66; the bridge indexes both with one "
        f"subscript at [common/irsfinalMT.cbl:L455-L456]"
    )

if len(COLUMNS) != loader.table_for(TABLE).column_count:  # pragma: no cover
    # Same character of check, across the other two frozen sources: the
    # dictionary's own column count against the entries it published.
    raise ValueError(
        f"{TABLE}: the dictionary lists {len(COLUMNS)} column entries but "
        f"records a column count of {loader.table_for(TABLE).column_count} "
        f"from [mysql/ACASDB.sql:L214]"
    )


#  `01 DAL-Data.` - THIS BRIDGE'S OWN CURSOR, AND ONLY THIS BRIDGE'S


#: `01 DAL-Data.` with `05 MOST-Relation pic xxx.` and
#: `05 Most-Cursor-Set pic 9 value zero.` plus its two `88`-levels
#: [common/irsfinalMT.cbl:L130-L134]. ONE cursor, at level `05` like eighteen of
#: the twenty in-scope bridges - only `otm3MT` and `otm5MT` use `03`.
#:
#: A SEPARATE TABLE FROM `dal/cursor_state`'s, DELIBERATELY: every bridge holds
#: its `01 DAL-Data` in its OWN working storage, so in the compiled system
#: cursors are isolated by construction and `irsfinalMT`'s flag cannot be
#: disturbed by `glpostingMT`'s. Sharing one process is what makes the reset
#: below necessary at all, and rule R-6's byte-identical-runs requirement is why
#: it is part of the public surface.
_CURSOR_STATES: Final[CursorStateTable] = CursorStateTable()

#: `03 ws-saved-fs-reply pic 99.` [common/irsfinalMT.cbl:L147].
#:
#: ANOMALY A44 LIVES IN THIS VARIABLE. The write loop stashes each failing row's
#: `FS-Reply` here [:L510] and restores the last one after the loop
#: [:L514-L515], and NOTHING EVER CLEARS IT: those four lines are its only
#: occurrences in the whole 727-line program. `Program-Id. irsfinalMT.` [:L13]
#: carries no `IS INITIAL`, so working storage survives every `CALL`, and one
#: failed row therefore makes every later write in the run return that row's
#: status. It is module-level here for exactly that reason - a function-local
#: would silently fix the defect.
_WS_SAVED_FS_REPLY: int = 0

#: `77  A  pic 9(4).` and `77  B  pic 9(4).` [common/acasirsub5.cbl:L112-L115],
#: whose own comment reads `*> used in 1st test ONLY`, latched by
#: `if A = zero` [:L368]. Working storage of the HANDLER this time, not the
#: bridge, and equally never cleared - the same once-only-latch construct
#: `dal/connection.py` reproduces for `load_rdb_data_once`.
_RECORD_SIZE_A: int = 0
_RECORD_SIZE_B: int = 0


def reset(*, states: CursorStateTable | None = None) -> None:
    """Clear this module's persistent state, as a fresh run would find it.

    Three items survive between calls in the compiled system and therefore
    survive between calls here:

    * `05 Most-Cursor-Set pic 9 value zero.` [common/irsfinalMT.cbl:L132], which
      starts at zero in every fresh run;
    * `03 ws-saved-fs-reply pic 99.` [:L147], the A44 carrier; and
    * the handler's `A`/`B` record-size latch [common/acasirsub5.cbl:L368].

    Two runs of one scenario inside ONE Python process must be independent - rule
    R-6 requires them to be byte-identical - and any of the three surviving
    between them would let the second run inherit the first's state: a cursor
    that resumes a position (anomaly A37) or a stale failure that resurfaces
    (anomaly A44).

    THIS FUNCTION MODELS RELOADING THE PROGRAM, NOT ANY FROZEN STATEMENT. There
    is no `move zero to ws-saved-fs-reply` anywhere in `irsfinalMT`; the
    equivalent in the compiled system is `CANCEL "irsfinalMT"`, which discards
    working storage wholesale. Nothing inside a run may call this, or it would
    fix A44 by the back door.

    Args:
        states: The cursor set to clear. The module's own set by default, which
            is the one every function here uses unless a caller supplies another.
    """
    global _WS_SAVED_FS_REPLY, _RECORD_SIZE_A, _RECORD_SIZE_B  # noqa: PLW0603
    (states if states is not None else _CURSOR_STATES).reset(TABLE)
    _WS_SAVED_FS_REPLY = 0
    _RECORD_SIZE_A = 0
    _RECORD_SIZE_B = 0


def _cursor_state(states: CursorStateTable | None) -> CursorState:
    """Resolve the `01 DAL-Data` block these verbs are to work through.

    Args:
        states: A caller-supplied cursor set, or ``None`` for the module's own.

    Returns:
        The one :class:`~acas_posting.dal.cursor_state.CursorState` for this
        table's single key of reference.
    """
    table = states if states is not None else _CURSOR_STATES
    return table.state_for(TABLE, CursorSlot.PRIMARY)


#  THE SQL THE BRIDGE ASSEMBLES, REPRODUCED TEXT FOR TEXT


def select_where() -> str:
    """`ws-Where` for the sequential read [common/irsfinalMT.cbl:L335-L347].

    The bridge builds one predicate and appends its own ordering, in a single
    `string` statement::

        string   "`"              delimited by size
                 KeyName (KOR-x1) delimited by space
                 "`"              delimited by size
                 " > "            delimited by size
                 '"000"'          delimited by size
                 ' ORDER BY '     delimited by size
                 "`"              delimited by size
                 KeyName (KOR-x1) delimited by space
                 "`"              delimited by size
                   ' ASC'         delimited by size
                                  into ws-Where with pointer J

    and its own echo comment [:L351] shows the intended result - though WITHOUT
    the backticks the code actually emits, which is a documentation/code mismatch
    worth noting rather than acting on.

    Four fidelities, each of which is an anomaly reproduced rather than a choice:

    * THE RELATION IS HARD-CODED `" > "` [:L338]. `MOST-Relation` is declared at
      [:L131] with the comment `*> valid are >=, <=, <, >, =` and is NOT USED on
      this path - anomaly A24. The token is nonetheless taken from
      `SEQUENTIAL_READ_START`, which records the hard-coded literal AND its
      locator, so the value still comes from the frozen source.
    * THE LOW KEY IS THE QUOTED THREE-DIGIT STRING `"000"` [:L339], compared
      against a `tinyint(2) unsigned` column - anomaly A25, ambiguity Q-16. The
      double quotes are part of the emitted text and are reproduced. This is the
      ONE value here that is NOT bound as a parameter, and deliberately so: it is
      a fixed constant of the frozen source with no caller input reaching it, so
      there is no injection route to close, and binding it would change the
      statement text the scenario diff is compared against.
    * `KeyName` IS `delimited by space` [:L336, :L342], so the declared
      thirty-character key name is trimmed to its twenty-one significant
      characters before being quoted.
    * THE `ORDER BY` IS EXPLICIT AND ASCENDING [:L340-L344]. Exactly the two
      ARRAY-FAN-OUT bridges carry one - this and `irsdfltMT` - and the other
      eighteen carry none; for them the ordering is load-bearing, because the
      subscript order IS the reassembly order. Section 0.6.6's "no ordering
      nondeterminism from a secondary index" still holds, because the ordering
      column is the primary key.

    Returns:
        The predicate text, e.g.
        `` `IRS-FINAL-ACC-REC-KEY` > "000" ORDER BY `IRS-FINAL-ACC-REC-KEY` ASC ``.
    """
    key: KeyOfReference = key_of_reference(TABLE, 1)
    # `KeyName (KOR-x1) delimited by space` [common/irsfinalMT.cbl:L336], then
    # the surrounding backticks [:L335, :L337].
    column = quote_identifier(cobol_string_delimited_by_space(key.key_name))
    start = SEQUENTIAL_READ_START[TABLE]
    # `" > "` [:L338] via `MostRelation.token`, and `'"000"'` [:L339] with its
    # quotes restored - `SequentialReadStart` stores the three digits alone.
    relation = start.relation.token
    low_key = f'"{start.low_key}"'
    return f"{column} {relation} {low_key} ORDER BY {column} ASC"


def select_statement() -> str:
    """`SELECT * FROM ... WHERE ...` [common/irsfinalMT.cbl:L357-L362].

    The bridge assembles::

        STRING "SELECT * FROM " "`IRSFINAL-REC`" " WHERE "
               ws-Where (1:J) ";" X"00" INTO WS-MYSQL-COMMAND

    NO `LIMIT` AND NO SECOND PREDICATE, because there is neither in the frozen
    text: the whole point of this statement is to hand back EVERY qualifying row
    so the loop can reassemble the array in one pass - "get all the (up to 26)
    rows in one hit" [:L391].

    The trailing `";" X"00"` is a terminator and a C string end, not part of the
    predicate, and is omitted for the same reason the house sequential read omits
    it: `execute_statement` issues exactly one statement and
    `mysql_1000_open` has multi-statement execution DISABLED, so a semicolon
    could only ever be noise.

    Returns:
        The statement text, with no placeholder - the only value in it is the
        frozen low-key literal.
    """
    return f"SELECT * FROM {quote_identifier(TABLE)} WHERE {select_where()}"


def insert_statement() -> str:
    """`bb200-Insert` [common/irsfinalMT.cbl:L609-L657].

    The generated section assembles MySQL's `INSERT ... SET` form - not the
    `INSERT ... VALUES` form - with a comma-space separator between terms and
    each value wrapped in double quotes::

        'INSERT INTO ' '`IRSFINAL-REC` SET '
        '`IRS-FINAL-ACC-REC-KEY`="' TRIM(WS-MYSQL-EDIT(18:03)) '"'
        ', ' '`IRS-AR1`="' TRIM(HV-IRS-AR1,TRAILING) '"'
        ', ' '`IRS-AR2`="' TRIM(HV-IRS-AR2,TRAILING) '"' ';'

    ALL THREE COLUMNS ARE ALWAYS NAMED AND ALWAYS BOUND. None may be omitted and
    none may be `None`: every column is `NOT NULL` with no `DEFAULT`
    [mysql/ACASDB.sql:L215-L217], and section 0.6.2 makes the reason explicit -
    "This is why every column in the schema can be declared `NOT NULL` and why
    the Python layer must default rather than omit." A blank array slot therefore
    writes the EMPTY STRING the bridge's own `TRIM(..., TRAILING)` produces, not
    a null.

    THE PRIMARY KEY IS IN THE `SET` CLAUSE because the bridge puts it there; that
    is how a fan-out row gets its subscript. See :func:`update_statement` for the
    sibling that does the same thing in an `UPDATE`, which is odder.

    Values travel as `%s` placeholders rather than interpolated text. The frozen
    bridge interpolates, but interpolation is transport: a bound parameter yields
    the same logical row while removing an injection route the frozen source left
    open, which is the same trade `dal/cursor_state` documents for its own
    positioning statement.

    Returns:
        The statement text with three placeholders, in schema ordinal order.
    """
    columns = ", ".join(f"{quote_identifier(name)}=%s" for name in COLUMNS)
    return f"INSERT INTO {quote_identifier(TABLE)} SET {columns}"


def update_where(ws_key: str) -> str:
    """`WS-Where` for the rewrite [common/irsfinalMT.cbl:L535-L546].

    Rebuilt INSIDE the loop, once per row, from `WS-Key` rather than from the
    edited host variable::

        string   "`" KeyName (KOR-x1) "`" '="' WS-Key '"' into WS-Where

    `WS-Key` is `pic 99` [:L106], so `delimited by size` [:L542] emits it
    ZERO-PADDED - `"01"` through `"26"`. That is anomaly A36: the same key value
    reaches the `SET` clause UNPADDED, because there it comes through
    `TRIM(WS-MYSQL-EDIT(18:03))`. Two renderings of one number in one statement,
    both reproduced.

    The commented-out `*> Final-Record (K:L)` immediately above [:L541] shows
    where `K` and `L` were meant to be used and confirms anomaly A23: the offset
    and length are moved into them at [:L532-L533] and then never read.

    Args:
        ws_key: The `pic 99` rendering of the subscript, from :func:`_ws_key`.

    Returns:
        The predicate text, e.g. `` `IRS-FINAL-ACC-REC-KEY`="01" ``.
    """
    key: KeyOfReference = key_of_reference(TABLE, 1)
    column = quote_identifier(cobol_string_delimited_by_space(key.key_name))
    return f'{column}="{ws_key}"'


def update_statement() -> str:
    """`bb300-Update` [common/irsfinalMT.cbl:L662-L714].

    The same three `SET` terms as :func:`insert_statement`, followed by
    ` WHERE ` and the per-row predicate::

        'UPDATE ' '`IRSFINAL-REC` SET ' <the three terms>
        " WHERE " TRIM(WS-Where (1:J)) ";"

    TWO ODDITIES, BOTH REPRODUCED. The `SET` clause INCLUDES THE PRIMARY KEY, so
    every row's key is updated to itself [:L677-L687]; and the key is rendered
    UNPADDED there and ZERO-PADDED in the `WHERE` - anomaly A36.

    Returns:
        The statement text with four placeholders: the three `SET` values in
        schema ordinal order, then the `WHERE` key.
    """
    columns = ", ".join(f"{quote_identifier(name)}=%s" for name in COLUMNS)
    key: KeyOfReference = key_of_reference(TABLE, 1)
    predicate = quote_identifier(cobol_string_delimited_by_space(key.key_name))
    return (
        f"UPDATE {quote_identifier(TABLE)} SET {columns} WHERE {predicate}=%s"
    )



#  THE TWO KEY RENDERINGS, AND THE FIELD MOVES


def _ws_key(subscript: int) -> str:
    """`move A to WS-Key` where `WS-Key pic 99` [common/irsfinalMT.cbl:L106].

    A two-digit ZERO-PADDED rendering, which is what `delimited by size` puts
    into the rewrite's `WHERE` [:L542] and what both loops put into `WS-File-Key`
    [:L482-L483, :L525-L526] as the log tag whose own comment reads
    `*> will contain the record with problems`.

    Args:
        subscript: The 1-based `occurs` position, 1 through 26.

    Returns:
        The `pic 99` text, ``"01"`` through ``"26"``.
    """
    return f"{subscript:02d}"


def _insert_key_text(subscript: int) -> str:
    """`TRIM(WS-MYSQL-EDIT(18:03))` [common/irsfinalMT.cbl:L626-L628, :L679-L681].

    The generated sections render the key by moving the host variable into an
    EDITED field and then slicing three characters out of it::

        MOVE HV-IRS-FINAL-ACC-REC-KEY TO WS-MYSQL-EDIT
        STRING FUNCTION TRIM (WS-MYSQL-EDIT(18:03)) ...

    `WS-MYSQL-EDIT` is `PIC -Z(18)9.9(9)` [common/irsfinalMT.cbl:L105] - thirty
    characters: the sign
    at 1, eighteen zero-suppressed digit positions at 2 through 19, a mandatory
    digit at 20, the point at 21 and nine decimals at 22 through 30. The integer
    part is right-justified in 2..20, so positions 18, 19 and 20 hold the
    hundreds, tens and units. `FUNCTION TRIM` with no direction strips BOTH ends,
    so the Z-suppressed leading spaces vanish and the result is the plain,
    UNPADDED decimal of the subscript.

    Worked: 1 gives `"  1"` -> `"1"`; 10 gives `" 10"` -> `"10"`; 26 gives
    `" 26"` -> `"26"`. Three character positions is also the widest value this
    can carry, which matches `HV-IRS-FINAL-ACC-REC-KEY PIC 9(03) COMP` [:L172]
    and is far above the 26 the array can index.

    THE RESULT DIFFERS FROM :func:`_ws_key` FOR EVERY SUBSCRIPT BELOW TEN, and in
    the rewrite BOTH appear in the same statement - anomaly A36. The
    `tinyint(2) unsigned` column DOES hold what the `9(03)` host variable intended
    over the whole 1..26 domain - measured, ambiguity Q-16 resolved: `(2)` is a
    display width and the column holds 0..255.

    Args:
        subscript: The 1-based `occurs` position, 1 through 26.

    Returns:
        The trimmed edited text, ``"1"`` through ``"26"``.
    """
    # AMBIGUITY Q-16 - RESOLVED BY MEASUREMENT; see the module docstring for the
    # probes. `HV-IRS-FINAL-ACC-REC-KEY PIC 9(03) COMP`
    # [common/irsfinalMT.cbl:L172] is written into a `tinyint(2) unsigned` column
    # [mysql/ACASDB.sql:L215] through this three-character edited slice, and the
    # sequential predicate then compares that column against the QUOTED literal
    # `"000"` [common/irsfinalMT.cbl:L339]. Measured on MariaDB 10.11.7: `(2)` is a
    # DISPLAY WIDTH, so the column holds 0..255 and every subscript 1..26 stores
    # exactly; and the quoted literal coerces to a NUMBER, so `> "000"` is `> 0`
    # and admits every legal key. Both renderings are emitted exactly as the frozen
    # source emits them and NEITHER is normalised - on evidence, not pending it.
    return str(subscript)


def _trim_trailing(value: str) -> str:
    """`FUNCTION TRIM (<hv>, TRAILING)` [common/irsfinalMT.cbl:L638, :L647].

    TRAILING ONLY, so leading spaces are PRESERVED - a distinction that matters
    because `ar1` is a free-text 24-character slot and a caller may legitimately
    have indented its content.

    An ALL-SPACES slot trims to the EMPTY STRING, and that empty string is what
    reaches a `char(24) NOT NULL` column. It is not a null and it is not skipped:
    anomaly A7 keeps the blank-slot skip commented out, so all 26 rows are always
    written and the table is DENSE after any write.

    `records/irs_final.py` states that nothing is trimmed there and assigns this
    trim to the handler module, which is here.

    Args:
        value: The array entry, at its declared width.

    Returns:
        The entry with trailing spaces removed.
    """
    return value.rstrip(" ")


def _receive_alphanumeric(value: object, width: int) -> str:
    """Store a fetched column into a `pic x(n)` item, at that item's width.

    `move HV-IRS-AR1 to AR1 (HV-IRS-FINAL-ACC-REC-KEY)`
    [common/irsfinalMT.cbl:L455] is a same-width alphanumeric move in the frozen
    source, because the host variable and the array entry are both `x(24)`. Here
    the value arrives from a MySQL `CHAR` column, which the server returns with
    its trailing spaces already removed, so the receiving width has to be
    restored for the record to keep the fixed-width shape
    `records/irs_final.py` declares.

    That restoration is a COBOL `MOVE` semantic - pad short, truncate long, never
    raise - and NOT a validation: nothing here rejects a value or reports an
    error, which rule R-3 would forbid. `cobol.move` owns the general form of the
    rule but section 0.4.3 bars this layer from importing it, so the width is
    taken from the record layer's own descriptor and applied inline.

    A `bytes` reading is decoded rather than stringified. The pinned converter
    already decodes a `CHAR` column - `AcasConverter._string_to_python` does
    `value.decode(self.charset)` [acas_posting/dal/connection.py:L711-L713] - so
    this branch cannot fire on the normal path, but `dal/__init__.py:L55-L56`
    states that a value may arrive as `bytes`, and `str()` on a `bytes` object
    yields its Python repr. Storing `"b'ab'"` into a `pic x(24)` accounting field
    would be a translation defect, not a COBOL `MOVE`: the frozen `MOVE` copies
    BYTES into a fixed-width alphanumeric item and has no notion of encoding.
    Decoding here mirrors the sibling converter's own precedent. `errors=
    "replace"` keeps the promise that this helper never raises and never rejects
    - a decode failure reported as an error would be a new validation, which rule
    R-3 forbids - and it cannot lose data in practice because the frozen schema
    is `utf8mb3`, a strict subset of UTF-8 [mysql/ACASDB.sql:L219].

    Args:
        value: The column value as the pinned converter produced it.
        width: The receiving field's declared width, from its descriptor.

    Returns:
        Exactly ``width`` characters.
    """
    if value is None:
        text = ""
    elif isinstance(value, (bytes, bytearray)):
        text = bytes(value).decode("utf-8", errors="replace")
    else:
        text = str(value)
    return text[:width].ljust(width)


def _initialize_final_record(final: IrsFinalRecord) -> None:
    """`initialize Final-Record with filler.` [common/irsfinalMT.cbl:L395].

    The operand is THE WHOLE `01` GROUP, not one view, so every member is blanked:
    both `occurs` views, both enumerated groups, and `ar3`. `with filler` is what
    extends `initialize` to the two unnamed `redefines` groups
    [copybooks/irswsfinal.cob:L35, :L65]; anomaly A30 records that the write path
    has no `initialize` at all, so the two fan-out verbs disagree on this.

    THE READ THEREFORE DESTROYS THE CALLER'S `ar3`. That is the only thing that
    ever touches those five bytes - they are never written to the database and
    never read back from it (anomaly A3) - and it is reproduced rather than
    softened.

    The statement runs BEFORE the loop and OUTSIDE the `if Cursor-Not-Active`
    guard [:L328, :L389], which is half of what makes anomaly A37 possible: a
    second read on an active cursor blanks the record and then finds nothing to
    put back.

    Args:
        final: The caller's `Final-Record`, mutated in place exactly as the
            COBOL mutates the linkage record.
    """
    final.ar1_view.ar1 = tuple(_AR1_BLANK for _ in range(ARRAY_LENGTH))
    final.ar2_view.ar2 = tuple(_AR2_BLANK for _ in range(ARRAY_LENGTH))
    for subscript in range(1, ARRAY_LENGTH + 1):
        # The enumerated fields occupy the SAME BYTES as the array views
        # [copybooks/irswsfinal.cob:L35-L36, :L65-L66], so `initialize` of the
        # group blanks them too. See the REDEFINES section of the module
        # docstring for why this module owns keeping the pair in step.
        setattr(final.ar1_fields, f"ar1_{subscript}", _AR1_BLANK)
        setattr(final.ar2_fields, f"ar2_{subscript}", _AR2_BLANK)
    # `03 ar3 pic x(5).` [copybooks/irswsfinal.cob:L68] - blanked here and
    # referenced NOWHERE else in this module, because no column exists for it.
    final.ar3 = _AR3_BLANK


def _store_array_entry(final: IrsFinalRecord, key: int, ar1: str, ar2: str) -> None:
    """`move HV-IRS-AR1 to AR1 (key)` and its `ar2` twin [:L455-L456].

    ANOMALY A4 LIVES HERE: the subscript is THE DATABASE VALUE, not the loop
    counter. The bridge's inline comment on the first of the two lines is
    `*> KEY = table position`, and the host variable it indexes with is
    `PIC 9(03)`, so it could carry up to 999 against a 26-element array. The
    guard at [:L426] is the only protection and it is applied by the caller,
    exactly where the bridge applies it.

    Both `redefines` views are written, per the module docstring's REDEFINES
    section: in COBOL they are one storage, and leaving the enumerated view stale
    would diverge from compiled behaviour.

    Args:
        final: The caller's `Final-Record`.
        key: The 1-based key value the row carried - NOT the loop counter.
        ar1: The `IRS-AR1` value, already at its receiving width.
        ar2: The `IRS-AR2` value, already at its receiving width.
    """
    # COBOL `OCCURS` is 1-based and Python indexing is 0-based;
    # `records/irs_final.py` assigns the offset to "whichever layer turns a
    # position into a key value", which is this one.
    index = key - 1
    entries_1 = list(final.ar1_view.ar1)
    entries_2 = list(final.ar2_view.ar2)
    entries_1[index] = ar1
    entries_2[index] = ar2
    final.ar1_view.ar1 = tuple(entries_1)
    final.ar2_view.ar2 = tuple(entries_2)
    setattr(final.ar1_fields, f"ar1_{key}", ar1)
    setattr(final.ar2_fields, f"ar2_{key}", ar2)


def _alias_enumerated_into_array(final: IrsFinalRecord) -> None:
    """Re-establish the `redefines` byte sharing before a host-variable load.

    CORRECTION C1. `copybooks/irswsfinal.cob` declares each array TWICE over ONE
    byte area: the enumerated group `03 ar1-fields.` with `05 ar1-1 pic x(24).`
    through `ar1-26` [copybooks/irswsfinal.cob:L8-L34], then
    `03 filler redefines ar1-fields.` carrying `05 ar1 pic x(24) occurs 26.`
    [:L35-L36]; identically for `ar2-fields` and its `05 ar2 pic x occurs 26.`
    [:L38-L64, :L65-L66]. A COBOL `REDEFINES` is not a copy - `ar1-3` and
    `AR1 (3)` ARE THE SAME TWENTY-FOUR BYTES - so in the compiled program a write
    through either name is already a write through both, and no synchronising
    statement exists anywhere to be translated.

    THE TWO NAMES BELONG TO OPPOSITE SIDES OF THE INTERFACE, which is a fact of
    the frozen source and not a preference:

    * The ENUMERATED names are THE CALLER'S. Every one of the fifty-two
      references outside the copybook is a SCREEN SECTION `using` clause on the
      Finished Accounts Setup screen - `03 pic x(24) using ar1-1 line 6 col 10
      foreground-color 3.` [irs/irs020.cbl:L472-L593] - and SCREEN `using` is
      bidirectional, so the operator's keystrokes land in `ar1-1` .. `ar1-26` and
      `ar2-1` .. `ar2-26`.
    * The ARRAY names are THE BRIDGE'S. `common/irsfinalMT.cbl` never mentions an
      enumerated name; it reads `AR1 (A)` / `AR2 (A)` to load the host variables
      [common/irsfinalMT.cbl:L484-L485, :L528-L529] and writes them back on the
      read [:L455-L456]. Outside the two fan-out bridges the array form appears
      only in read-only consumers [irs/irs020.cbl:L1018-L1021,
      irs/irs060.cbl:L1184-L1187]. NOTHING in the frozen codebase writes the
      array form except that read.

    `records/irs_final.py` is required to publish the pair as two independent
    dataclasses - its contract fixes the `dataclasses.fields()` count of each
    view at one, requires a literal `tuple` of twenty-six, and forbids a property
    that switches between them - so the one byte area is two Python objects and
    the aliasing has to be re-established by whoever observes it. This bridge is
    the only thing that observes it, so this bridge owns it, at exactly the
    boundary the frozen bridge reads: immediately before each host-variable load.
    The READ direction is already in place and untouched -
    `_initialize_final_record` blanks BOTH views [common/irsfinalMT.cbl:L395] and
    `_store_array_entry` writes BOTH [:L455-L456].

    A slot is carried across only when its enumerated field is not the blank its
    descriptor declares. That guard is what keeps a caller who populated the
    array view directly working unchanged - not a frozen calling pattern, but one
    this module accepted before - and it makes the whole normal path a no-op,
    because a read has already put the same value in both. Every slot is then
    written back through both names, so a caller inspecting the record afterwards
    reads alike through either, as it would in the compiled program.

    THE ONE CASE THE TWO-OBJECT MODEL CANNOT RESOLVE is a caller that mutates the
    ARRAY view after a read while the enumerated view still holds that read's
    values: it resolves toward the enumerated view. It is unreachable from this
    package - only the read path and the initialise ever write the array view and
    both write both views - and it is recorded as an ambiguity in
    `docs/migration/ambiguity-resolutions.md` rather than settled silently.

    Args:
        final: The caller's `Final-Record`, whose two views of each array are
            brought into the agreement the compiled program never has to arrange.
    """
    # A short view is fitted rather than rejected, so this helper cannot raise on
    # a record the caller built by hand; the module contract is that a bridge
    # returns a status pair and never propagates an exception.
    current_1 = (list(final.ar1_view.ar1) + [_AR1_BLANK] * ARRAY_LENGTH)[:ARRAY_LENGTH]
    current_2 = (list(final.ar2_view.ar2) + [_AR2_BLANK] * ARRAY_LENGTH)[:ARRAY_LENGTH]
    resolved_1: list[str] = []
    resolved_2: list[str] = []
    for subscript in range(1, ARRAY_LENGTH + 1):
        index = subscript - 1
        # `_receive_alphanumeric` is the module's own fit to a declared width, so
        # a caller's `ar1_1 = "Sales"` becomes the twenty-four bytes a COBOL
        # `move` into `pic x(24)` would have stored.
        enumerated_1 = _receive_alphanumeric(
            getattr(final.ar1_fields, f"ar1_{subscript}"), _AR1_WIDTH
        )
        enumerated_2 = _receive_alphanumeric(
            getattr(final.ar2_fields, f"ar2_{subscript}"), _AR2_WIDTH
        )
        resolved_1.append(
            enumerated_1 if enumerated_1 != _AR1_BLANK else current_1[index]
        )
        resolved_2.append(
            enumerated_2 if enumerated_2 != _AR2_BLANK else current_2[index]
        )
    final.ar1_view.ar1 = tuple(resolved_1)
    final.ar2_view.ar2 = tuple(resolved_2)
    for subscript in range(1, ARRAY_LENGTH + 1):
        setattr(final.ar1_fields, f"ar1_{subscript}", resolved_1[subscript - 1])
        setattr(final.ar2_fields, f"ar2_{subscript}", resolved_2[subscript - 1])


def _array_entry(final: IrsFinalRecord, subscript: int) -> tuple[str, str]:
    """`move AR1 (A) to HV-IRS-AR1` and its twin [:L484-L485, :L528-L529].

    THE ARRAY VIEWS ARE THE OPERANDS, and only they: the 52 enumerated names
    appear NOWHERE in `common/irsfinalMT.cbl`. In the compiled program that costs
    nothing, because `AR1 (A)` and `ar1-A` are one byte area
    [copybooks/irswsfinal.cob:L35-L36, :L65-L66]; in Python the two views are two
    objects, so `_alias_enumerated_into_array` runs before the loop that calls
    this helper and leaves both views holding the same value. This function is
    therefore a pure read of the operand the bridge names, exactly as written.

    Args:
        final: The caller's `Final-Record`.
        subscript: The 1-based loop position, 1 through 26.

    Returns:
        The `(ar1, ar2)` pair at that position, untrimmed.
    """
    index = subscript - 1
    return final.ar1_view.ar1[index], final.ar2_view.ar2[index]


#  `ba010-Initialise` AND THE DRIVER PARAGRAPHS OF `mysql-procedures.cpy`


def _ba010_initialise(file_access: FileAccess) -> None:
    """`ba010-Initialise` [common/irsfinalMT.cbl:L222-L230].

    Every bridge call begins here::

        move     zero   to We-Error                        *> as in irsub5
        move     spaces to WS-MYSQL-Error-Message
                           WS-MYSQL-Error-Number
                           WS-Log-Where
                           WS-File-Key
                           SQL-Msg
                           SQL-Err
                           SQL-State.

    `We-Error` IS CLEARED AND `FS-Reply` IS NOT - so a caller's incoming
    `FS-Reply` survives into the verb, which is why the handler saves and restores
    the pair around its synthesised close rather than relying on the bridge.

    The `*> as in irsub5` comment is the bridge citing the handler that calls it;
    each module in this family names itself in that comment.

    Args:
        file_access: The caller's block, mutated in place.
    """
    file_access.we_error = int(WeError.SUCCESS)
    logging_data = file_access.logging_data
    logging_data.ws_log_where = ""
    logging_data.ws_file_key = ""
    logging_data.sql_msg = " " * SQL_MSG_WIDTH
    logging_data.sql_err = " " * SQL_ERR_WIDTH
    logging_data.sql_state = " " * SQL_STATE_WIDTH


def _process_logs(
    dal_common: AcasDalCommonData, file_access: FileAccess, site: str
) -> None:
    """`perform Ca-Process-Logs` - as a log record, never as a `CALL`.

    Both `Ca-Process-Logs` paragraphs contain nothing but
    `call "fhlogger" using File-Access ACAS-DAL-Common-data`
    [common/acasirsub5.cbl:L528-L529, common/irsfinalMT.cbl:L722-L723], and
    `common/fhlogger.cbl` is out of scope per section 0.2.2, so rule R-1 forbids
    the call outright. The site therefore emits the record through
    :func:`acas_posting.dal.status.log_file_handler_record` - THE ONE ADAPTER every
    handler in this package shares, at one level, with one field set - and it changes
    no status, no control flow and no table.

    `WS-File-Key` is WITHHELD: on this table it is `IRS-FINAL-ACC-REC-KEY`, a
    business key, and the safe-event schema admits no record key (CWE-532). So are
    `WS-Log-Where` and `SQL-Msg`. The two testing switches are withheld too - they
    are configuration, not an event, and a record naming them said nothing an
    operator acts on. `Log-File-Rec-Written` IS now advanced, by one modulo a
    million, once per record.

    THIS FUNCTION IS THE BARE `perform`, WITH NO GATE, because the gate is not
    always there in the frozen source. EVERY ONE of the bridge's seven sites is
    wrapped in `if Testing-1` [common/irsfinalMT.cbl:L420-L422, :L430-L432,
    :L450-L452, :L457-L458, :L504-L505, :L566-L568, :L602-L604], and NOT ONE of
    the handler's seven is [common/acasirsub5.cbl:L428, :L436, :L445, :L452,
    :L456, :L478, :L502]. Use :func:`_process_logs_if_testing` for the former and
    this for the latter, so each call site says which the source said.

    ANOMALY A26: the handler's own paragraph is annotated
    `*> Not called on DAL access as it does it already` [common/acasirsub5.cbl:
    L525] and yet `ba015-Test-Ends` performs it SEVEN times, four of them in the
    read path alone.

    Args:
        dal_common: `ACAS-DAL-Common-data`, which the logger takes as its second
            argument [common/acasirsub5.cbl:L529] and reads `Testing-1` from.
        file_access: The block the logger would have read.
        site: Which frozen `perform` this is, for the log line.
    """
    logging_data = file_access.logging_data
    log_file_handler_record(
        _LOG,
        program="irsfinalMT",
        paragraph=site,
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


def _process_logs_if_testing(
    dal_common: AcasDalCommonData, file_access: FileAccess, site: str
) -> None:
    """`if Testing-1 / perform Ca-Process-Logs / end-if` - the gated form.

    Every one of the BRIDGE's seven logging sites is written this way; none of
    the handler's is. Splitting the two forms keeps that asymmetry visible at
    each call site instead of hiding it inside one helper.

    `88 Testing-1 value 1` sits on `SW-Testing`, whose declaration carries the
    comment `*> set sw-testing to zero to stop logging.`
    [common/acasirsub5.cbl:L137].

    Args:
        dal_common: `ACAS-DAL-Common-data`; `sw_testing` is `Testing-1`.
        file_access: The block the logger would have read.
        site: Which frozen `perform` this is, for the log line.
    """
    if dal_common.sw_testing == 1:
        _process_logs(dal_common, file_access, site)


def _column_names(cursor: DatabaseCursor) -> tuple[str, ...]:
    """The result's column names, from the cursor's own metadata.

    Args:
        cursor: The cursor the statement was issued on.

    Returns:
        The names in result order, or an empty tuple when the driver published
        no description.
    """
    description = cursor.description
    if not description:
        return ()
    return tuple(str(column[0]) for column in description)


def _fetch_one_row(cursor: DatabaseCursor) -> Mapping[str, object] | None:
    """`CALL "MySQL_fetch_record"` [common/irsfinalMT.cbl:L404-L411].

    The frozen call hands the three host variables straight back from the result
    row. Here the row is returned keyed by column name so the caller can name
    `IRS-AR1` and `IRS-AR2` rather than count positions - which matters because
    the bridge's `SELECT *` takes its column order from the schema and the
    handler must not depend on that order.

    Both row shapes a driver may produce are accepted, because
    `dal/connection.py` owns that choice and this module must not constrain it.

    Args:
        cursor: The cursor the statement was issued on.

    Returns:
        The next row, or ``None`` at `return-code = -1` [:L415].
    """
    row = cursor.fetchone()
    if row is None:
        return None
    if isinstance(row, Mapping):
        return row
    names = _column_names(cursor)
    if not names:
        return MappingProxyType({str(index): value for index, value in enumerate(row)})
    return MappingProxyType(dict(zip(names, row, strict=False)))


def _store_result(cursor: DatabaseCursor) -> tuple[Mapping[str, object], ...]:
    """`PERFORM MYSQL-1220-STORE-RESULT` [common/irsfinalMT.cbl:L364].

    `mysql_store_result` materialises EVERY qualifying row on the client and
    `mysql_num_rows` then reports its size [copybooks/mysql-procedures.cpy:
    L187-L192]. The bridge relies on that snapshot: it stores once at [:L364] and
    then walks it up to 26 times [:L396-L462] without re-issuing anything.

    Args:
        cursor: The cursor the `SELECT` was issued on.

    Returns:
        Every row, keyed by column name, in the order the single `ORDER BY` term
        returned them.
    """
    rows: list[Mapping[str, object]] = []
    while True:
        row = _fetch_one_row(cursor)
        if row is None:
            return tuple(rows)
        rows.append(row)


@dataclass(frozen=True, slots=True)
class _CommandOutcome:
    """What one `Mysql-1210-Command` leaves behind for its caller to read.

    The frozen bridge keeps these in working storage - `WS-MYSQL-Count-Rows`,
    `WS-MYSQL-Error-Number`, `WS-MYSQL-Error-Message` and `WS-MYSQL-SQLstate` -
    and every verb reads them AFTER the command paragraph returns. Grouping them
    keeps that read-after-call ordering explicit instead of passing four separate
    return values through each call site.

    Attributes:
        count_rows: `WS-MYSQL-Count-Rows` - `MySQL_affected_rows` for the two
            command paragraphs [copybooks/mysql-procedures.cpy:L178], or
            `MySQL_num_rows` over the stored result for the select
            [copybooks/mysql-procedures.cpy:L191-L192].
        status: What `Mysql-1100-Db-Error` produced, or ``None`` when the
            statement carried no driver failure.
        errno: `WS-MYSQL-Error-Number`, as `call "MySQL_errno"` would return it.
        message: `WS-MYSQL-Error-Message`, as `call "MySQL_error"` would.
        sql_state: `WS-MYSQL-SQLstate`, as `call "MySQL_sqlstate"` would.
    """

    count_rows: int
    status: DbErrorStatus | None
    errno: str
    message: str
    sql_state: str


def _apply_driver_status(file_access: FileAccess, status: DbErrorStatus) -> None:
    """Store what `Mysql-1100-Db-Error Thru Mysql-1190-Exit` moved into place.

    The driver paragraph writes `fs-Reply`, `We-Error`, `SQL-Err`, `SQL-Msg` and
    `SQL-State` before returning to the verb that performed it, and the verb then
    OVERWRITES some of them from its own re-fetch. Both writes happen, in that
    order, and this is the first of the two.

    ON THE DUPLICATE-KEY ARM THE FROZEN PARAGRAPH EXITS EARLY. `move 22 to
    fs-Reply` then `go to Mysql-1190-Exit`
    [copybooks/mysql-procedures.cpy:L103-L104] jumps past `call "MySQL_error"`
    [:L107], past `call "MySQL_sqlstate"` and `move ... to SQL-State`
    [:L122-L123], and past `move 911 to We-Error` [:L128]. So that arm writes
    `fs-Reply` and NOTHING else, and `We-Error` keeps whatever it held - which is
    why every caller here passes its current `We-Error` in rather than letting it
    default (see :func:`_issue_command`).

    `dal/status.py` nonetheless returns the driver's message and SQLSTATE on that
    arm, and this function stores them. That is not a divergence in the observable
    state: both bridge loops re-fetch the SQLSTATE themselves, unconditionally,
    inside the `not = 1` arm [common/irsfinalMT.cbl:L489-L490, :L556-L557], and
    the message inside the errno arm [:L492-L494, :L559-L561], so the value a
    caller finally reads is the bridge's own store either way. Recorded because
    the two writes happen in an order the frozen program also has, and only the
    second is observable.

    Args:
        file_access: The caller's block, mutated in place.
        status: The paragraph's result.
    """
    file_access.fs_reply = int(status.fs_reply)
    file_access.we_error = int(status.we_error)
    logging_data = file_access.logging_data
    if status.sql_err:
        logging_data.sql_err = status.sql_err[:SQL_ERR_WIDTH].ljust(SQL_ERR_WIDTH)
    if status.sql_msg:
        logging_data.sql_msg = status.sql_msg[:SQL_MSG_WIDTH].ljust(SQL_MSG_WIDTH)
    if status.sql_state:
        logging_data.sql_state = status.sql_state[:SQL_STATE_WIDTH].ljust(
            SQL_STATE_WIDTH
        )


def _issue_command(
    connection: MySQLConnectionAbstract,
    statement: str,
    parameters: Sequence[object],
    *,
    we_error: int,
) -> _CommandOutcome:
    """`PERFORM MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT`.

    [copybooks/mysql-procedures.cpy:L164-L178], the paragraph both `bb200-Insert`
    [common/irsfinalMT.cbl:L655] and `bb300-Update` [:L712] end with::

        call     "MySQL_query" using WS-Mysql-Command.
        if       Return-Code not = zero
                  perform Mysql-1100-Db-Error Thru Mysql-1190-Exit
        end-if
        call     "MySQL_affected_rows" using WS-Mysql-Count-Rows.

    TWO FROZEN FACTS SHAPE THIS FUNCTION.

    ANOMALY A39 - THERE IS NO RETRY AND THERE CAN BE NONE. The whole retry arm of
    that `if`, including `perform Mysql-1300-DB-Error`, the `WE-Error = 910`
    test and the `go to Mysql-1210-Command` re-issue, IS COMMENTED OUT
    [copybooks/mysql-procedures.cpy:L167-L175]. So the lock-retry ladder
    `dal/status.py` models is unreachable
    from here, and the two `move zero to WS-Mysql-Time-Step WS-SQL-Retry` resets
    at [common/irsfinalMT.cbl:L469-L470, :L521-L522] reset state nothing reads.
    No retry is attempted here and nothing sleeps, which rule R-6 requires
    independently.

    ANOMALY A40 - `MySQL_affected_rows` IS CALLED EVEN AFTER A FAILURE, because
    the call sits AFTER the `end-if` [copybooks/mysql-procedures.cpy:L177-L178].
    So `WS-MYSQL-Count-Rows` always has
    a value and the `not = 1` test in both loops always has something to compare.
    A statement that never reached the server affected no rows, so zero is what
    that reading gives.

    THE CALLER'S CURRENT `We-Error` MUST BE PASSED IN. `Mysql-1100-Db-Error`'s
    duplicate-key arm does `move 22 to fs-Reply` and then
    `go to Mysql-1190-Exit` [copybooks/mysql-procedures.cpy:L99-L105], jumping
    PAST `move 911 to We-Error` [:L128] without writing `We-Error` at all - so on
    that arm the field keeps whatever it already held. `dal/status.py` models
    that by returning the `we_error` it was given rather than a value of its own,
    which means a caller that lets the parameter default to zero silently ERASES
    a 911 an earlier row in the same loop had set. The write loop is exactly that
    case: a non-duplicate failure on row 4 followed by a duplicate on row 26
    must leave `(22, 911)`, not `(22, 0)`. Found by ad-hoc test, not by reading.

    Args:
        connection: A connection from `mysql_1000_open`.
        statement: One statement, identifiers already quoted, values as `%s`.
        parameters: The values to bind, in the statement's own order.
        we_error: The caller's `We-Error` as it stands NOW, so the duplicate arm
            can pass it straight through instead of zeroing it.

    Returns:
        The `WS-MYSQL-Count-Rows` reading, the driver paragraph's status, and the
        raw three fields the bridge's own `MySQL_errno` / `MySQL_error` /
        `MySQL_sqlstate` calls would have fetched.
    """
    try:
        with execute_statement(connection, statement, parameters) as cursor:
            # `call "MySQL_affected_rows"` [copybooks/mysql-procedures.cpy:L178].
            affected = cursor.rowcount
    except Exception as error:  # noqa: BLE001 - any driver failure takes this arm
        # `if Return-Code not = zero / perform Mysql-1100-Db-Error`
        # [copybooks/mysql-procedures.cpy:L166, :L176]. `dal/status.py` owns that
        # paragraph, including the duplicate-key early exit that leaves
        # `We-Error` untouched.
        errno, message, sql_state = _driver_failure_fields(error)
        status = mysql_1100_db_error(
            errno=errno,
            message=message,
            sql_state=sql_state,
            command=statement,
            # The duplicate-key arm returns this untouched rather than 911
            # [copybooks/mysql-procedures.cpy:L99-L105 vs :L128].
            we_error=we_error,
        )
        #  NO SECOND RECORD HERE. `mysql_1100_db_error`, called on the line
        #  above, IS the one operator record for a database failure - it is the
        #  migration of `Mysql-1110-Report-Problem`
        #  [copybooks/mysql-procedures.cpy:L130-L137], which the frozen bridge reaches
        #  on every one - and it already carries the status pair, the SQLSTATE, the
        #  errno and the stable category. Repeating them made one failure two records,
        #  and this one also interpolated the driver's message, which for this table
        #  renders the statement and its bound key (CWE-532); `redact_for_log` escaped
        #  it and removed none of it. `message` is still RETURNED, because `SQL-Msg` is
        #  a status field the paragraphs read.
        # A40: affected rows is still read, and a failed statement affected none.
        return _CommandOutcome(
            count_rows=0,
            status=status,
            errno=errno,
            message=message,
            sql_state=sql_state,
        )
    return _CommandOutcome(
        count_rows=0 if affected is None or affected < 0 else int(affected),
        status=None,
        errno="",
        message="",
        sql_state="",
    )


def _driver_failure_fields(error: BaseException) -> tuple[str, str, str]:
    """Split a driver exception into the three values the frozen calls fetch.

    `call "MySQL_errno"`, `call "MySQL_error"` and `call "MySQL_sqlstate"` fetch
    a number, a message and a five-character SQLSTATE
    [common/irsfinalMT.cbl:L438-L448, :L488-L494, :L555-L561]. The pinned driver
    carries the same three on its exception, under names that are resolved
    defensively because the abstract base class does not declare them.

    Args:
        error: The exception the driver raised.

    Returns:
        `(errno, message, sqlstate)`, each already a string.
    """
    errno = getattr(error, "errno", None)
    sql_state = getattr(error, "sqlstate", None)
    message = getattr(error, "msg", None)
    return (
        "" if errno is None else str(errno),
        str(error) if message is None else str(message),
        "" if sql_state is None else str(sql_state),
    )



def _issue_select(
    connection: MySQLConnectionAbstract,
    statement: str,
    state: CursorState,
    *,
    we_error: int,
) -> _CommandOutcome:
    """The select pair: `MYSQL-1210-COMMAND` then `MYSQL-1220-STORE-RESULT`.

    [common/irsfinalMT.cbl:L363-L365]::

        PERFORM MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT
        PERFORM MYSQL-1220-STORE-RESULT THRU MYSQL-1239-EXIT
        MOVE WS-MYSQL-RESULT TO TP-IRSFINAL-REC

    THE COUNT COMES FROM `MySQL_num_rows`, NOT FROM AFFECTED ROWS.
    `Mysql-1220-Store-Result` materialises the whole result on the client and
    then overwrites `WS-MYSQL-Count-Rows` with its size
    [copybooks/mysql-procedures.cpy:L187-L192], so the affected-rows reading the
    command paragraph left there [:L178] is discarded. That is the number the
    empty-table test at [common/irsfinalMT.cbl:L374] reads, and the number the
    in-loop test at [:L437] reads on every iteration WITHOUT re-issuing anything -
    which is why that in-loop test can never fire on the normal path (anomaly
    A43).

    `MOVE WS-MYSQL-RESULT TO TP-IRSFINAL-REC` saves the result pointer into the
    table's own pointer item [:L170], which the loop then restores before each
    fetch [:L404]. `CursorState.stored_rows` is that pointer's Python analogue,
    and `count_rows` is `MySQL_num_rows` over it - a full count that does not
    shrink as records are fetched, exactly as `num_rows` does not.

    THE CALLER'S CURRENT `We-Error` IS PASSED IN for the same reason
    :func:`_issue_command` takes it: `Mysql-1100-Db-Error`'s duplicate arm leaves
    the field alone [copybooks/mysql-procedures.cpy:L99-L105]. A duplicate cannot
    arise on a `SELECT` - the arm additionally requires the command to begin
    `INSERT` [:L100-L102] - so the value is carried here for uniformity and
    because the frozen paragraph is one paragraph, not two.

    Args:
        connection: A connection from `mysql_1000_open`.
        statement: The select, with the frozen low-key literal already in it.
        state: The cursor state that will hold the materialised result.
        we_error: The caller's `We-Error` as it stands now.

    Returns:
        The stored-result count and, on a driver failure, everything the bridge's
        own re-fetch would have read.
    """
    try:
        with execute_statement(connection, statement, ()) as cursor:
            # `PERFORM MYSQL-1220-STORE-RESULT` [common/irsfinalMT.cbl:L364].
            rows = _store_result(cursor)
    except Exception as error:  # noqa: BLE001 - any driver failure takes this arm
        errno, message, sql_state = _driver_failure_fields(error)
        status = mysql_1100_db_error(
            errno=errno,
            message=message,
            sql_state=sql_state,
            command=statement,
            # The duplicate-key arm returns this untouched rather than 911
            # [copybooks/mysql-procedures.cpy:L99-L105 vs :L128].
            we_error=we_error,
        )
        # `Mysql-1220-Store-Result` still runs and still stores; with no result
        # there is nothing to store and `MySQL_num_rows` reads zero.
        state.store_result(())
        #  NO SECOND RECORD HERE, for the reason the command path gives above:
        #  `mysql_1100_db_error` has already emitted the one operator record, and the
        #  driver's message is not safe to log.
        return _CommandOutcome(
            count_rows=0,
            status=status,
            errno=errno,
            message=message,
            sql_state=sql_state,
        )
    # `MOVE WS-MYSQL-RESULT TO TP-IRSFINAL-REC` [:L365] then `MySQL_num_rows`.
    return _CommandOutcome(
        count_rows=state.store_result(rows),
        status=None,
        errno="",
        message="",
        sql_state="",
    )


#  `ba040-Process-Read-Next` - ONE COBOL RECORD REASSEMBLED FROM UP TO 26 ROWS


def read_next(
    connection: MySQLConnectionAbstract,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    final: IrsFinalRecord,
    *,
    states: CursorStateTable | None = None,
) -> tuple[FsReply, int]:
    """`ba040-Process-Read-Next` [common/irsfinalMT.cbl:L317-L466].

    ONE LOGICAL READ REASSEMBLES UP TO 26 ROWS INTO ONE `Final-Record`. The
    maintainer's own header says so [:L319-L326]::

        *> Getting the 26 rows for loading into one cobol rec
        *>  having initialised record as some rows may not be present
        *>   if Cobol record has no data for a heading.
        *>    Same applies to the write process.
        *>
        *>   Here a SELECT first then fetch if no cursor active using lowest
        *>    possible key of "000"
        *>           [ IRS-FINAL-ACC-REC-KEY ]

    A SHORT TABLE IS NORMAL AND IS NOT AN ERROR. "some rows may not be present"
    is the frozen contract, so nothing here requires 26 rows, requires them to be
    contiguous, or reports a gap - rule R-3 forbids adding the check and rule R-4
    forbids fixing what the absence of one causes.

    THE RETURNED STATUS IS ALMOST ALWAYS `(0, 0)`, AND THAT IS THE POINT.
    [:L465] is `move zero to fs-reply WE-Error.` with NO GUARD (anomaly A32), and
    it sits after the loop on the path every in-loop exit takes. So:

    * end of data part-way through the array sets `(10, 10)` at [:L417] and is
      then ERASED - the caller sees `(0, 0)`;
    * an out-of-range key puts THE KEY VALUE in `We-Error` at [:L428] (anomaly
      A5) and that too is ERASED;
    * only the EMPTY-TABLE path escapes, because it leaves by
      `go to ba998-Free` [:L386] and never reaches [:L465]. `(10, 10)` is
      therefore the ONE failure a caller can observe from this verb.

    Both erased values are still written at their sites, and both still reach the
    log record the bridge emits at that site [:L420-L422, :L430-L432], exactly as
    the compiled program logs them and then returns success. That is the same
    shape as the write's swallowed failure (anomaly A1) and is reproduced for the
    same reason.

    THREE MORE FROZEN ODDITIES ARE REPRODUCED HERE.

    * `initialize Final-Record with filler.` [:L395] SITS OUTSIDE the
      `if Cursor-Not-Active` guard [:L328, :L389] and nothing on the success path
      clears `Most-Cursor-Set`. A SECOND read on a still-active cursor therefore
      blanks the caller's record, issues no statement, finds the snapshot
      exhausted, and returns `(0, 0)` by way of [:L465] - anomaly A37. The
      handler's synthesised triple hides this because its open clears the cursor
      [:L299] and its close frees the result [:L303-L304], but the facade
      publishes `acasirsub5-Read-Next` as a verb in its own right
      [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L304], and a caller performing it
      twice hits it.
    * THE IN-LOOP EOF TEST CARRIES TWO DEAD DISJUNCTS. `A > 26 or = zero` [:L416]
      cannot be true inside a loop whose bound is `until A > 26` and whose start
      is 1 - anomaly A42. Written as the source writes it.
    * `move spaces to WS-Log-Where.` [:L393] WIPES THE PREDICATE that [:L349]
      stored `*> For test logging`, and it wipes it BEFORE any log call in this
      paragraph can read it. The predicate survives into a log record on exactly
      one path - the empty-table one, which reaches `ba999-end`'s log
      [:L602-L604] with [:L393] never executed - anomaly A41.

    Args:
        connection: A connection the caller has already opened, because the
            frozen bridge holds it in working storage across its three calls.
        file_access: `File-Access` [common/irsfinalMT.cbl:L207], mutated in place.
        dal_common: `ACAS-DAL-Common-data` [:L208]; `sw_testing` gates logging.
        final: `Final-Record` [:L209] - blanked, then filled by key.
        states: The cursor-state table to use. Defaults to this module's own,
            which keeps `read_next` deterministic across runs.

    Returns:
        The `(FS-Reply, We-Error)` pair as it stands at `ba999-exit`.
    """
    # `ba010-Initialise` runs on EVERY bridge call, before the dispatch
    # [common/irsfinalMT.cbl:L222-L230].
    _ba010_initialise(file_access)
    logging_data = file_access.logging_data
    state = _cursor_state(states)

    if state.cursor_not_active():  # [common/irsfinalMT.cbl:L328]
        # `set KOR-x1 to 1` [:L329] - one key of reference, `occurs 1` [:L119].
        key: KeyOfReference = key_of_reference(TABLE, 1)
        # `move KOR-offset (KOR-x1) to K` / `move KOR-length (KOR-x1) to L`
        # [:L330-L331] - ANOMALY A23: both are moved and then NEVER READ. The
        # commented-out `*> Final-Record (K:L)` in the rewrite [:L541] shows what
        # they were for. Named here so the dead move is visible and traceable,
        # and used for nothing, exactly as in the frozen source.
        _dead_kor_offset, _dead_kor_length = key.kor_offset, key.kor_length
        # `move ws-Where (1:J) to WS-Log-Where  *> For test logging` [:L349],
        # which [:L393] then wipes before any log call here reads it (A41).
        logging_data.ws_log_where = select_where()
        logging_data.ws_no_paragraph = _BRIDGE_TRACE_SELECT  # `move 3 to` [:L350]
        outcome = _issue_select(
            connection, select_statement(), state, we_error=file_access.we_error
        )
        if outcome.status is not None:
            # `Mysql-1100-Db-Error` wrote first [copybooks/mysql-procedures.cpy:
            # L176]; the block below then overwrites what it wrote.
            _apply_driver_status(file_access, outcome.status)
        logging_data.ws_file_key = "000"  # `move "000" to WS-File-Key` [:L367]
        # [:L368-L370] `if Testing-2 display Display-Message-1 with erase eos` -
        # screen output with no database effect, dropped per section 0.3.4.
        if outcome.count_rows == 0:  # `WS-MYSQL-Count-Rows = zero` [:L374]
            return _ba040_no_data(file_access, dal_common, state, outcome)
        # `move 1 to Most-Cursor-Set` [:L388]. The frozen comment on that line is
        # `*> should test if select worked first??????` - six question marks, and
        # no such test was ever added.
        state.set_cursor_active()

    # `move spaces to WS-Log-Where.` [:L393] - A41: the predicate is wiped here.
    logging_data.ws_log_where = ""
    logging_data.ws_no_paragraph = _BRIDGE_TRACE_FETCH  # `move 4 to` [:L394]
    # `initialize Final-Record with filler.` [:L395] - the WHOLE group, `ar3`
    # included, and outside the cursor guard (A37).
    _initialize_final_record(final)

    # `perform varying A from 1 by 1 until A > 26` [:L396-L397]. The commented-out
    # `*> or return-code not = zero` [:L398] is a third loop condition that was
    # never enabled; the fetch failure is tested inside the body instead.
    for subscript in range(1, ARRAY_LENGTH + 1):
        # `MOVE TP-IRSFINAL-REC TO WS-MYSQL-RESULT` then
        # `CALL "MySQL_fetch_record"` [:L404-L411]: the pointer is restored and
        # the three host variables are filled from the next row of the snapshot.
        row = state.fetch_record()

        # `if return-code = -1 or A > 26 or = zero` [:L415-L416]. ANOMALY A42:
        # inside a 1..26 loop the second and third disjuncts are unreachable.
        # Written as the source writes them.
        if row is None or subscript > ARRAY_LENGTH or subscript == 0:
            # `move 10 to fs-Reply WE-Error` [:L417] - one statement, both
            # fields, which is what `end_of_file_status` exists to reproduce.
            fs_reply, we_error = end_of_file_status()
            file_access.fs_reply = int(fs_reply)
            file_access.we_error = we_error
            logging_data.ws_file_key = "EOF"  # [:L418]
            # `move zero to Most-Cursor-Set` [:L419] - the flag is cleared and
            # the RESULT IS NOT FREED. That leak is the frozen behaviour.
            state.set_cursor_not_active()
            # [:L420-L422] `if Testing-1 perform Ca-Process-Logs` - "do for each
            # row". This log record is the only place the `(10, 10)` survives,
            # because [:L465] erases it.
            _process_logs_if_testing(dal_common, file_access, "ba040/EOF")
            break  # `exit perform` [:L423] - Class 2, post-loop work follows

        key_value = _read_key(row)

        # `if HV-IRS-FINAL-ACC-REC-KEY = zero or > 26` [:L426]. THE GUARD IS
        # CORRECT HERE - `> 26` against `occurs 26` - and its `irsdfltMT` twin
        # guards `> 32` against `occurs 33`, which is a genuine off-by-one in
        # that module. See the module docstring; do not "align" the two.
        if key_value == 0 or key_value > ARRAY_LENGTH:
            logging_data.ws_file_key = "EOF3"  # [:L427]
            # `move HV-IRS-FINAL-ACC-REC-KEY to WE-Error` [:L428] - ANOMALY A5:
            # THE OFFENDING KEY VALUE BECOMES THE ERROR CODE, and `FS-Reply` is
            # NOT set. [:L465] then erases both, so this reaches the log and
            # nothing else.
            file_access.we_error = key_value
            state.set_cursor_not_active()  # [:L429]
            _process_logs_if_testing(dal_common, file_access, "ba040/EOF3")
            break  # `exit perform` [:L433]

        # `move HV-IRS-FINAL-ACC-REC-KEY to WS-File-Key` [:L436].
        logging_data.ws_file_key = _insert_key_text(key_value)

        # `if WS-MYSQL-Count-Rows = zero` [:L437]. ANOMALY A43: the count is the
        # store-result snapshot's size and nothing re-reads it inside the loop,
        # so on the normal path the empty case already left at [:L386] and this
        # can never fire. Reproduced because the frozen source tests it, and
        # because a caller reaching here on a stale cursor (A37) could.
        if state.count_rows == 0:
            # [:L438-L446] The errno arm - and only this arm sets a status.
            if _errno_is_set(outcome_errno := _last_errno(file_access)):
                fs_reply, we_error = end_of_file_status()  # [:L441-L442]
                file_access.fs_reply = int(fs_reply)
                file_access.we_error = we_error
                logging_data.sql_err = outcome_errno[:SQL_ERR_WIDTH].ljust(
                    SQL_ERR_WIDTH
                )  # [:L443]
                logging_data.ws_file_key = "EOF2"  # [:L445]
            # `call "MySQL_sqlstate"` then `move ... to SQL-State` [:L447-L448] -
            # OUTSIDE the errno arm, so the SQLSTATE is stored either way.
            state.set_cursor_not_active()  # [:L449]
            _process_logs_if_testing(dal_common, file_access, "ba040/EOF2")
            break  # `exit perform` [:L453]

        # `move HV-IRS-AR1 to AR1 (HV-IRS-FINAL-ACC-REC-KEY)` and its `ar2` twin
        # [:L455-L456]. ANOMALY A4: THE SUBSCRIPT IS THE DATABASE VALUE, not the
        # loop counter - the bridge's own comment reads `*> KEY = table position`.
        _store_array_entry(
            final,
            key_value,
            _receive_alphanumeric(row.get(COLUMNS[1]), _AR1_WIDTH),
            _receive_alphanumeric(row.get(COLUMNS[2]), _AR2_WIDTH),
        )

        # [:L457-L461] `if Testing-1 / perform Ca-Process-Logs / move zeros to
        # FS-Reply SQL-Err / move spaces to SQL-Msg`. ANOMALY A33: this clear is
        # LIVE here and COMMENTED OUT in the write loop [:L506-L507] - the same
        # idiom, one enabled and one not.
        if dal_common.sw_testing == 1:
            _process_logs(dal_common, file_access, "ba040/row")
            file_access.fs_reply = int(FsReply.SUCCESS)
            # `move zeros to SQL-Err` where `SQL-Err pic x(5)`
            # [copybooks/wsfnctn.cob:L49]: a figurative-constant move to an
            # alphanumeric item fills it with the CHARACTER zero, so this is
            # "00000" and not spaces.
            logging_data.sql_err = "0" * SQL_ERR_WIDTH
            logging_data.sql_msg = " " * SQL_MSG_WIDTH  # [:L460]

    # `move HV-IRS-FINAL-ACC-REC-KEY to WS-File-Key.` [:L464]. The host variable
    # still holds whatever the LAST fetch left in it, so this restates the key
    # already in `WS-File-Key` on the success path and leaves the "EOF" tags in
    # place on the exit paths, because those set the tag after the last fetch.
    #
    # `move zero to fs-reply WE-Error.` [:L465] - ANOMALY A32, THE UNCONDITIONAL
    # RESET. Every status this paragraph set above is erased here, and there is
    # no guard to make it selective. `go to ba999-exit` [:L466] then skips
    # `ba999-end`'s own logging hook [:L602-L604] - anomaly A38.
    #
    # AMBIGUITY Q-17 - RESOLVED FROM THE FROZEN SOURCE. WHAT A CALLER OBSERVES FOR
    # A PARTIALLY POPULATED TABLE. Three findings meet here. The bridge tolerates a
    # short table by design - `*> having initialised record as some rows may not be
    # present` [:L320] - so a table holding, say, nine rows leaves array entries
    # 10..26 at the spaces `initialize Final-Record with filler` [:L395] put there;
    # the exhaustion arm set `(10, 10)` on the way out [:L417]; and THIS LINE then
    # erases it, so the caller is handed a half-blank record and a SUCCESS status
    # with nothing to distinguish it from a full read. A repeat read compounds it
    # (anomaly A37).
    #
    # WHY NO ORACLE RUN IS NEEDED, and the earlier note was asking the wrong
    # question. It said "no reading of the source settles whether a caller was ever
    # meant to be able to tell" - which is true, and is a question about INTENT.
    # Rule R-4 makes intent irrelevant: a defect reproduced is correct. The
    # BEHAVIOUR is fully determined by the statements above, because `move zero to
    # fs-reply WE-Error` [:L465] carries no guard, so the observable pair for a
    # short table is `(0, 0)` and a part-blank record, unconditionally. That is
    # what the two lines below produce. Nothing was waiting on a measurement.
    #
    # Note that after any WRITE the state is dense - anomaly A7 keeps the
    # blank-slot skip commented out [:L477-L480] - so this bites only on tables
    # seeded or loaded outside this handler.
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    return FsReply.SUCCESS, int(WeError.SUCCESS)


def _ba040_no_data(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    state: CursorState,
    outcome: _CommandOutcome,
) -> tuple[FsReply, int]:
    """The empty-table arm of the read [common/irsfinalMT.cbl:L374-L387].

    `*>  It could be an empty table so test for it` [:L372]::

        if       WS-MYSQL-Count-Rows = zero
                 call  "MySQL_errno" using WS-MYSQL-Error-Number
                 if    WS-MYSQL-Error-Number  not = "0  "
                       move WS-MYSQL-Error-Number to SQL-Err
                       call "MySQL_error" using WS-MYSQL-Error-Message
                       move WS-MYSQL-Error-Message to SQL-Msg
                 end-if
                 call  "MySQL_sqlstate" using WS-MYSQL-SQLstate
                 move  WS-MYSQL-SqlState   to SQL-State
                 move  10 to fs-reply
                 move  10 to WE-Error
                 move    "No Data" to WS-File-Key
                 go to ba998-Free
        end-if

    THIS IS THE ONLY FAILURE A CALLER OF THE READ CAN SEE. `go to ba998-Free`
    leaves by way of `ba998-Free` [:L588-L598] and `ba999-end` [:L600], so the
    unconditional reset at [:L465] is never executed and the `(10, 10)` survives.
    It is also the only path on which the predicate reaches a log record, because
    `ba999-end` performs `Ca-Process-Logs` [:L602-L604] while [:L393] - which
    wipes `WS-Log-Where` - has not run (anomaly A41).

    The frozen comment on the errno test, `*> set non '0' if no rows ?`, is the
    maintainer recording that he did not know whether an empty result sets errno.
    Whatever the driver does, the arm is taken or not on exactly that value.

    Args:
        file_access: The caller's block, mutated in place.
        dal_common: `ACAS-DAL-Common-data`; `sw_testing` gates the log.
        state: The cursor state, freed here.
        outcome: What the select left in the `WS-MYSQL-*` fields.

    Returns:
        `(10, 10)` - the end-of-file pair, unerased.
    """
    logging_data = file_access.logging_data
    # `call "MySQL_errno"` [:L375] then `if ... not = "0  "` [:L376]. ANOMALY A20:
    # the same literal is spelt with THREE trailing spaces here and in the write
    # [:L491] but FOUR in the rewrite [:L558], so the comparison is made on the
    # trimmed value and the discrepancy is recorded rather than resolved.
    if _errno_is_set(outcome.errno):
        logging_data.sql_err = outcome.errno[:SQL_ERR_WIDTH].ljust(SQL_ERR_WIDTH)
        # `call "MySQL_error"` then `move ... to SQL-Msg` [:L378-L379].
        logging_data.sql_msg = outcome.message[:SQL_MSG_WIDTH].ljust(SQL_MSG_WIDTH)
    # `call "MySQL_sqlstate"` / `move WS-MYSQL-SqlState to SQL-State`
    # [:L381-L382] - OUTSIDE the errno arm. The frozen comment on the `end-if`
    # above reads `*> do not really need to do this meaning the above CALL`.
    logging_data.sql_state = outcome.sql_state[:SQL_STATE_WIDTH].ljust(
        SQL_STATE_WIDTH
    )
    # `move 10 to fs-reply` [:L383] and `move 10 to WE-Error` [:L384] - TWO
    # separate statements here where [:L417] uses one. ANOMALY A35: both EOF
    # sites in this paragraph set `We-Error` to 10, so the "10" that
    # `dal/status.py` calls documentation-only is genuinely stored.
    fs_reply, we_error = end_of_file_status()
    file_access.fs_reply = int(fs_reply)
    file_access.we_error = we_error
    logging_data.ws_file_key = "No Data"  # [:L385]
    # `go to ba998-Free` [:L386] - Class 4, a named sibling that does work and
    # then falls through into `ba999-end`.
    _ba998_free(file_access, dal_common, state)
    return fs_reply, we_error


def _ba998_free(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    state: CursorState,
) -> None:
    """`ba998-Free` and the fall-through into `ba999-end` [:L588-L604].

    ::

        ba998-Free.
            move     20 to ws-No-Paragraph.
            ...  MySQL_free_result  ...
            move     zero to Most-Cursor-Set.
        ba999-end.
            if       Testing-1
                     perform Ca-Process-Logs
            end-if.

    The free and the flag clear TOGETHER, which is what distinguishes this from
    the in-loop end-of-file sites: those clear the flag and leave the result
    allocated [:L419, :L429, :L449].

    Reached only by `go to ba998-Free`, which in this bridge means only the
    empty-table arm of the read. The three fan-out verbs all leave by
    `go to ba999-exit` instead and so skip the log below - anomaly A38.

    Args:
        file_access: The caller's block; only `ws_no_paragraph` changes.
        dal_common: `ACAS-DAL-Common-data`; `sw_testing` gates the log.
        state: The cursor state to free.
    """
    file_access.logging_data.ws_no_paragraph = _BRIDGE_TRACE_FREE  # [:L589]
    state.free()  # `MySQL_free_result` [:L595-L596] + `move zero` [:L598]
    _process_logs_if_testing(dal_common, file_access, "ba999-end")  # [:L602-L604]


def _errno_is_set(errno: str) -> bool:
    """`if WS-MYSQL-Error-Number not = "0  "` - on the trimmed value.

    ANOMALY A20: the frozen source spells the literal with THREE trailing spaces
    at [common/irsfinalMT.cbl:L376] and [:L491] and with FOUR at [:L558]. In
    COBOL an alphanumeric comparison pads the shorter operand with spaces, so all
    three spellings mean the same test against a `pic x(4)` field; in Python the
    equivalent is to compare the significant characters, which is what this does.
    The discrepancy is recorded rather than reconciled.

    An empty string is treated as "not set", which is what a statement that
    raised nothing leaves in `WS-MYSQL-Error-Number` after `ba010-Initialise`
    moved spaces into it [:L224-L230].

    A RUN OF ASCII ZEROS IS ALSO "not set", and that case is not hypothetical.
    `WS-MYSQL-Error-Number` is `pic x(4)` [common/irsfinalMT.cbl:L198] and the
    frozen guard always re-fetches it from `MySQL_errno` [:L375, :L438, :L488,
    :L555], so the field it tests only ever holds a decimal rendering - `"0   "`
    for a healthy statement. `_last_errno` models that re-fetch by reading
    `SQL-Err pic x(5)` [copybooks/wsfnctn.cob:L49] back instead, and `SQL-Err`
    has a DIFFERENT fill convention: `move zero to SQL-Err` [:L474, :L572] is the
    figurative constant moved to an alphanumeric item, which fills all five
    characters with `'0'` and yields `"00000"`. Reporting that as an errno would
    invent a failure the frozen program does not have - rule R-3 bars new
    validations, and inventing an error is the worse half of that prohibition -
    so every all-zero reading takes the same arm the fresh fetch would take. No
    real reading is masked: MySQL error numbers start at 1000 and none renders as
    a run of zeros.

    Args:
        errno: The `MySQL_errno` reading.

    Returns:
        Whether the errno arm is taken.
    """
    trimmed = errno.strip()
    # `lstrip("0")` empties exactly the zero readings - "", "0", "0000", "00000"
    # - and leaves every genuine error number intact.
    return bool(trimmed.lstrip("0"))


def _last_errno(file_access: FileAccess) -> str:
    """`call "MySQL_errno" using WS-MYSQL-Error-Number` [:L438].

    The in-loop count-zero arm re-fetches the errno, and since no statement has
    been issued since the select, the value it gets is the select's. `SQL-Err`
    holds that value whenever the select's own arm stored it [:L377], so the
    working-storage field is where it is read back from.

    Args:
        file_access: The caller's block.

    Returns:
        The errno as `SQL-Err` currently holds it, trimmed of its padding.
    """
    return file_access.logging_data.sql_err.strip()


def _read_key(row: Mapping[str, object]) -> int:
    """The `HV-IRS-FINAL-ACC-REC-KEY` a fetched row carries [:L406].

    `HV-IRS-FINAL-ACC-REC-KEY PIC 9(03) COMP` [:L172] is an UNSIGNED THREE-DIGIT
    BINARY item, so it is a Python `int` and never a `Decimal` - there is no
    scale to preserve and rule R-2 forbids a float. The column it comes from is
    `tinyint(2) unsigned` [mysql/ACASDB.sql:L215], which the pinned converter
    materialises as `int`.

    A value the array cannot index is NOT rejected here: the guard the frozen
    bridge applies is applied at the frozen bridge's own site [:L426], and
    nothing else may be added (rule R-3).

    Args:
        row: One fetched row, keyed by column name.

    Returns:
        The key value as the host variable would hold it.
    """
    value = row.get(COLUMNS[0])
    if isinstance(value, int):
        return value
    if value is None:
        # `initialize`d host variables read zero; the guard at [:L426] then takes
        # the `= zero` arm, which is exactly what the frozen code would do.
        return 0
    return int(str(value).strip() or "0")



#  `ba070-Process-Write` - ONE COBOL RECORD OUT AS TWENTY-SIX `INSERT`s


def write(
    connection: MySQLConnectionAbstract,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    final: IrsFinalRecord,
) -> tuple[FsReply, int]:
    """`ba070-Process-Write` [common/irsfinalMT.cbl:L468-L517].

    TWENTY-SIX `INSERT`s PER LOGICAL WRITE, keyed by the loop subscript::

        perform  varying A from 1 by 1 until A > 26
                 move     A        to HV-IRS-FINAL-ACC-REC-KEY
                                      WS-Key
                 move     WS-Key   to WS-File-Key
                 move     AR1 (A)  to HV-IRS-AR1
                 move     AR2 (A)  to HV-IRS-AR2
                 perform  bb200-Insert
                 ...
        end-perform

    THE BLANK-SLOT SKIP IS COMMENTED OUT [:L477-L480]::

        *>             if       AR1 (A) = spaces              *> dont write out blank data
        *>                 and  AR2 (A) = spaces
        *>                      exit perform cycle
        *>             end-if

    so ALL 26 ROWS ARE ALWAYS WRITTEN, blank ones included, and this table is
    DENSE after any write - anomaly A7. A scenario diff that expects only the
    populated rows will fail, and correctly so. Re-enabling those four lines
    would be a rule R-4 failure.

    EVERY `INSERT` NAMES AND BINDS ALL THREE COLUMNS. All three are `NOT NULL`
    with no `DEFAULT` [mysql/ACASDB.sql:L215-L217], and section 0.6.2 is explicit
    that "the Python layer must default rather than omit". A blank slot writes the
    empty string the bridge's own `TRIM(..., TRAILING)` produces [:L638, :L647];
    `None` is never bound and no column is ever left out. Note that the bridge
    does NOT `initialize` its host-variable group before this loop - anomaly A22,
    a divergence from the convention section 0.6.2 describes and from
    `irsdfltMT`'s own `initialise TD-IRSDFLT-REC` - which is harmless only
    because all three are assigned on every iteration. The invariant is honoured
    regardless.

    THE STATUS-SQUASHING LOOP [:L509-L516] IS WHY ONLY THE LAST FAILURE SURVIVES::

        if       fs-reply not = zero
                 move fs-reply to ws-saved-fs-reply
                 move zero to fs-reply                   *> for next loop iteration
        end-if
        ...
        if       ws-saved-fs-reply not = zero             *> restore last error
                 move ws-saved-fs-reply to fs-reply
        end-if

    Anomaly A6: each row's failure is stashed and cleared, THE LOOP NEVER STOPS
    EARLY, and the pair a caller finally sees carries one row's status - the last
    that failed. `We-Error` is set by no statement in this paragraph at all; the
    only way it becomes non-zero here is `Mysql-1100-Db-Error`'s own 911.

    AND `ws-saved-fs-reply` IS NEVER CLEARED - anomaly A44. It is module state
    here for that reason. A single failed row in one write makes every subsequent
    write in the run return that row's status, which combined with anomaly A1
    inverts the reporting: the write that actually failed reports success, and a
    later clean one reports the failure.

    Args:
        connection: A connection the caller has already opened.
        file_access: `File-Access` [:L207], mutated in place.
        dal_common: `ACAS-DAL-Common-data` [:L208]; `sw_testing` gates logging.
        final: `Final-Record` [:L209] - read through its `occurs` views.

    Returns:
        The `(FS-Reply, We-Error)` pair as it stands at `ba999-Exit`.
    """
    global _WS_SAVED_FS_REPLY  # noqa: PLW0603 - A44: the frozen field is program state
    # `ba010-Initialise` [common/irsfinalMT.cbl:L222-L230], which clears
    # `We-Error` and NOT `FS-Reply`, and does not touch `ws-saved-fs-reply`.
    _ba010_initialise(file_access)
    logging_data = file_access.logging_data

    # `move zero to WS-Mysql-Time-Step WS-SQL-Retry.` [:L469-L470] - ANOMALY A39:
    # the ladder these two drive is commented out of `Mysql-1210-Command`
    # [copybooks/mysql-procedures.cpy:L167-L175], so this resets state nothing
    # can reach. Modelled as nothing, which is also what rule R-6 wants: no
    # retry, no sleep, no timing.

    # `move zero to FS-Reply WE-Error` [:L472].
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    logging_data.sql_msg = " " * SQL_MSG_WIDTH  # `move spaces to SQL-Msg` [:L473]
    # `move zero to SQL-Err` [:L474] where `SQL-Err pic x(5)`
    # [copybooks/wsfnctn.cob:L49]: a figurative-constant move to an alphanumeric
    # item stores the CHARACTER zero in every position, so this is "00000".
    logging_data.sql_err = "0" * SQL_ERR_WIDTH
    logging_data.ws_no_paragraph = _BRIDGE_TRACE_INSERT  # `move 10 to` [:L475]

    statement = insert_statement()
    # CORRECTION C1, before the load: `AR1 (A)` and `ar1-A` are ONE byte area
    # [copybooks/irswsfinal.cob:L35-L36, :L65-L66], so the compiled program needs
    # no statement here and none exists to translate. The two Python views are two
    # objects, so the aliasing is re-established at the boundary the frozen bridge
    # reads. See `_alias_enumerated_into_array`.
    _alias_enumerated_into_array(final)
    # `perform varying A from 1 by 1 until A > 26` [:L476] - 1 through 26
    # INCLUSIVE, matching `occurs 26` [copybooks/irswsfinal.cob:L36, :L66].
    for subscript in range(1, ARRAY_LENGTH + 1):
        # [:L477-L480] The blank-slot skip, COMMENTED OUT - anomaly A7. Nothing
        # is skipped and nothing may be.
        #
        # `move A to HV-IRS-FINAL-ACC-REC-KEY WS-Key` [:L481-L482] - ONE move
        # with TWO receivers, where `irsdfltMT` uses two moves. The two receivers
        # then render differently: the host variable through
        # `TRIM(WS-MYSQL-EDIT(18:03))` [:L626-L628] and `WS-Key` as `pic 99`.
        key_text = _insert_key_text(subscript)
        ws_key = _ws_key(subscript)
        # `move WS-Key to WS-File-Key` [:L483]. The frozen comment reads
        # `*> will contain the record with problems`.
        logging_data.ws_file_key = ws_key
        # `move AR1 (A) to HV-IRS-AR1` / `move AR2 (A) to HV-IRS-AR2`
        # [:L484-L485] - THE `occurs` VIEWS, indexed by the LOOP COUNTER here,
        # unlike the read which indexes by the returned key (anomaly A4).
        ar1, ar2 = _array_entry(final, subscript)
        # `perform bb200-Insert` [:L486].
        outcome = _issue_command(
            connection,
            statement,
            # `TRIM(HV-IRS-AR1,TRAILING)` and its twin [:L638, :L647]: trailing
            # only, so leading spaces survive and an all-spaces slot becomes the
            # empty string - never `None`.
            (key_text, _trim_trailing(ar1), _trim_trailing(ar2)),
            # Whatever an EARLIER row of this same loop left in `We-Error`, so
            # a duplicate on this row does not erase it
            # [copybooks/mysql-procedures.cpy:L99-L105].
            we_error=file_access.we_error,
        )
        if outcome.status is not None:
            # `Mysql-1100-Db-Error` wrote first [copybooks/mysql-procedures.cpy:
            # L176]; the block below then overwrites part of what it wrote.
            _apply_driver_status(file_access, outcome.status)

        # `if WS-MYSQL-COUNT-ROWS not = 1` [:L487].
        if outcome.count_rows != 1:
            # `call "MySQL_errno"` [:L488], then `call "MySQL_sqlstate"` and
            # `move WS-MYSQL-SqlState to SQL-State` [:L489-L490] - the SQLSTATE
            # store is UNCONDITIONAL inside this arm, BEFORE the errno test. So a
            # row that affected no rows WITHOUT a driver error stores a SQLSTATE
            # and sets no status at all: a SILENT non-write.
            logging_data.sql_state = outcome.sql_state[:SQL_STATE_WIDTH].ljust(
                SQL_STATE_WIDTH
            )
            # `if WS-MYSQL-Error-Number not = "0  "  *> 14/12/16` [:L491] -
            # THREE trailing spaces here, FOUR in the rewrite [:L558]. Anomaly
            # A20: compared on the trimmed value, discrepancy recorded.
            if _errno_is_set(outcome.errno):
                # `call "MySQL_error"` [:L492] then `move WS-MYSQL-Error-Number
                # to SQL-Err` [:L493] and `move WS-MYSQL-Error-Message to
                # SQL-Msg` [:L494].
                logging_data.sql_err = outcome.errno[:SQL_ERR_WIDTH].ljust(
                    SQL_ERR_WIDTH
                )
                logging_data.sql_msg = outcome.message[:SQL_MSG_WIDTH].ljust(
                    SQL_MSG_WIDTH
                )
                # `if SQL-Err (1:4) = "1062" or = "1022" or Sql-State = "23000"`
                # [:L495-L497] - the first FOUR characters of a five-character
                # field, plus SQLSTATE as an independent alternative.
                if is_duplicate_key_bridge_level(
                    logging_data.sql_err, logging_data.sql_state
                ):
                    file_access.fs_reply = int(FS_REPLY_DUPLICATE)  # [:L498]
                else:
                    # [:L500], whose frozen comment is
                    # `*> this may need changing for val in WE-Error!!`.
                    file_access.fs_reply = int(FS_REPLY_GENERAL)

        # `if Testing-1 / perform Ca-Process-Logs` [:L504-L505].
        if dal_common.sw_testing == 1:
            _process_logs(dal_common, file_access, "ba070/row")
            # [:L506-L507] `*> move zeros to FS-Reply SQL-Err` and
            # `*> move spaces to SQL-Msg` - ANOMALY A31: a status clear left
            # COMMENTED OUT inside the logging block, which would have masked
            # every error whenever logging was on. Its twin in the read loop
            # [:L459-L460] is LIVE (anomaly A33). Not re-enabled.

        # `if fs-reply not = zero` [:L509] - THE SQUASH, anomaly A6.
        if file_access.fs_reply != int(FsReply.SUCCESS):
            _WS_SAVED_FS_REPLY = file_access.fs_reply  # [:L510]
            # `move zero to fs-reply  *> for next loop iteration` [:L511].
            file_access.fs_reply = int(FsReply.SUCCESS)

    # `if ws-saved-fs-reply not = zero  *> restore last error` [:L514-L515]. A44:
    # the field was never cleared, so this can restore a failure from an EARLIER
    # write call that this one knows nothing about.
    if _WS_SAVED_FS_REPLY != int(FsReply.SUCCESS):
        file_access.fs_reply = _WS_SAVED_FS_REPLY

    # `go to ba999-Exit.` [:L517] - jumping past `ba999-end`'s own logging hook
    # [:L600-L604], anomaly A38.
    return FsReply(file_access.fs_reply), file_access.we_error


#  `ba090-Process-Rewrite` - TWENTY-SIX `UPDATE`s, THEN THE RESET THAT ERASES THEM


def rewrite(
    connection: MySQLConnectionAbstract,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    final: IrsFinalRecord,
) -> tuple[FsReply, int]:
    """`ba090-Process-Rewrite` [common/irsfinalMT.cbl:L519-L574].

    TWENTY-SIX `UPDATE`s PER LOGICAL REWRITE, one per array position, each with
    its own `WHERE` rebuilt inside the loop [:L535-L546].

    *** THIS VERB CANNOT REPORT A FAILURE. *** [:L571-L573], with NO GUARD OF ANY
    KIND, is the last thing it does before leaving::

        move     zero   to FS-Reply WE-Error.
        move     zero   to SQL-Err.
        move     spaces to SQL-Msg.
        go       to ba999-exit.

    So the `move 99 to fs-reply` at [:L562] and the `move 994 to WE-Error` at
    [:L563] are set and then ERASED, on every iteration and finally after the
    loop. A rewrite that failed on all twenty-six rows returns `(0, 0)`.
    `WeError.REWRITE_SQLSTATE_NOT_00000` - 994 - IS PERMANENTLY UNOBSERVABLE
    THROUGH THIS BRIDGE. That is anomaly A1's second half, and it is deliberate:
    guarding the reset, or returning 994, would be a rule R-4 failure.

    Its first half is in the handler: on a write failure `ba015-Test-Ends`
    [common/acasirsub5.cbl:L475-L483] clears the status and FALLS THROUGH into
    this rewrite, because ONE `end-if.` closes TWO nested `if`s (anomaly A2). Put
    together, A FAILED WRITE REPORTS SUCCESS. See :func:`dispatch`, which is where
    the fall-through is reproduced.

    Also here, and not fixed: `if Testing-2` at [:L550] where every other test in
    both files uses `Testing-1` (anomaly A21); the dead `KOR-offset`/`KOR-length`
    moves at [:L532-L533] with the commented-out `*> Final-Record (K:L)` at
    [:L541] showing what they were for (anomaly A23); the errno literal spelt with
    FOUR trailing spaces at [:L558] against THREE in the write (anomaly A20); and
    the same key rendered unpadded in the `SET` and zero-padded in the `WHERE`
    (anomaly A36). There is NO status-squashing loop in this paragraph, because
    the unconditional reset makes one pointless.

    Args:
        connection: A connection the caller has already opened.
        file_access: `File-Access` [:L207], mutated in place.
        dal_common: `ACAS-DAL-Common-data` [:L208]; `sw_testing` gates logging.
        final: `Final-Record` [:L209] - read through its `occurs` views.

    Returns:
        Always `(0, 0)`. See above; this is not an oversight in the translation.
    """
    _ba010_initialise(file_access)
    logging_data = file_access.logging_data

    # `move zero to WS-Mysql-Time-Step WS-SQL-Retry.` [:L521-L522] - anomaly A39
    # again; the ladder is unreachable, so this is modelled as nothing.
    logging_data.ws_no_paragraph = _BRIDGE_TRACE_UPDATE  # `move 17 to` [:L523]

    statement = update_statement()
    # CORRECTION C1, before the load, exactly as in `write`. The frozen loader
    # reads `AR1 (A)` / `AR2 (A)` [:L528-L529]; those are the same bytes as
    # `ar1-A` / `ar2-A` in the compiled program and two separate objects here.
    _alias_enumerated_into_array(final)
    # `perform varying A from 1 by 1 until A > 26` [:L524]. NO blank-slot skip
    # here, not even a commented-out one - all 26 rows are always attempted.
    for subscript in range(1, ARRAY_LENGTH + 1):
        ws_key = _ws_key(subscript)  # `move A to WS-Key` [:L525]
        # `move WS-Key to WS-File-Key HV-IRS-FINAL-ACC-REC-KEY` [:L526-L527] -
        # ONE move, TWO receivers, and the second of them is then rendered
        # UNPADDED by `bb300-Update`'s edited slice [:L679-L681] while the
        # `WHERE` below renders `WS-Key` ZERO-PADDED. Anomaly A36.
        logging_data.ws_file_key = ws_key
        key_text = _insert_key_text(subscript)
        # `move AR1 (A) to HV-IRS-AR1` / `move AR2 (A) to HV-IRS-AR2`
        # [:L528-L529].
        ar1, ar2 = _array_entry(final, subscript)

        # `set KOR-x1 to 1` [:L531], whose frozen comment reads
        # `*> 1 = Primary, 2 = Abrev, 3 = Desc (NOT Delete function as can be
        # dups)` - a note about a delete path THIS BRIDGE DOES NOT HAVE.
        key: KeyOfReference = key_of_reference(TABLE, 1)
        # `move KOR-offset (KOR-x1) to K` / `move KOR-length (KOR-x1) to L`
        # [:L532-L533] - ANOMALY A23, moved and never read. The commented-out
        # `*> Final-Record (K:L) delimited by size` at [:L541] is the use that
        # was replaced by `WS-Key delimited by size *> use the real key for row`.
        _dead_kor_offset, _dead_kor_length = key.kor_offset, key.kor_length
        # `move WS-Where (1:J) to WS-Log-Where  *>  For test logging` [:L547].
        # Unlike the read, NOTHING wipes it before the log call at [:L567], so
        # here the predicate genuinely reaches the log record (anomaly A41).
        logging_data.ws_log_where = update_where(ws_key)

        # `perform bb300-Update` [:L548].
        outcome = _issue_command(
            connection,
            statement,
            (key_text, _trim_trailing(ar1), _trim_trailing(ar2), ws_key),
            # As in the write loop. An `UPDATE` cannot take the duplicate arm at
            # all [copybooks/mysql-procedures.cpy:L100-L102], which is why a
            # duplicate on a rewrite is reported 99 and not 22.
            we_error=file_access.we_error,
        )
        if outcome.status is not None:
            _apply_driver_status(file_access, outcome.status)

        # [:L550-L552] `if Testing-2 / display Display-Message-1 with erase eos` -
        # ANOMALY A21: `Testing-2` where every other test in both files uses
        # `Testing-1`. Screen output with no database effect, so it is dropped
        # per section 0.3.4; the anomaly is recorded rather than reproduced.

        # `if WS-MYSQL-COUNT-ROWS not = 1` [:L554].
        if outcome.count_rows != 1:
            # `call "MySQL_errno"` [:L555], `call "MySQL_sqlstate"` and
            # `move WS-MYSQL-SqlState to SQL-State` [:L556-L557] - unconditional
            # inside this arm, as in the write.
            logging_data.sql_state = outcome.sql_state[:SQL_STATE_WIDTH].ljust(
                SQL_STATE_WIDTH
            )
            # `if WS-MYSQL-Error-Number not = "0   "` [:L558] - FOUR trailing
            # spaces, against THREE in the write [:L491]. Anomaly A20.
            if _errno_is_set(outcome.errno):
                # `call "MySQL_error"` [:L559], `move ... to SQL-Err` [:L560],
                # `move ... to SQL-Msg` [:L561]. NOTE: NO DUPLICATE-KEY TEST
                # HERE - the write has one [:L495-L497] and the rewrite does not,
                # so a duplicate on an update is reported as 99 and not 22.
                logging_data.sql_err = outcome.errno[:SQL_ERR_WIDTH].ljust(
                    SQL_ERR_WIDTH
                )
                logging_data.sql_msg = outcome.message[:SQL_MSG_WIDTH].ljust(
                    SQL_MSG_WIDTH
                )
                # `move 99 to fs-reply` [:L562] and `move 994 to WE-Error`
                # [:L563]. BOTH ARE ERASED BELOW. They are written anyway,
                # because the compiled program writes them and because the log
                # record at [:L567] is the one place they are ever visible.
                file_access.fs_reply = int(FS_REPLY_GENERAL)
                file_access.we_error = WE_ERROR_UNOBSERVABLE_REWRITE

        # `if Testing-1 / perform Ca-Process-Logs` [:L566-L568].
        if dal_common.sw_testing == 1:
            _process_logs(dal_common, file_access, "ba090/row")

    # *** THE UNCONDITIONAL RESET *** [:L571-L573]. There is no `if` above these
    # three statements and none may be added. `move zero to FS-Reply WE-Error.`
    # then `move zero to SQL-Err.` then `move spaces to SQL-Msg.` - and because
    # `SQL-Err pic x(5)` [copybooks/wsfnctn.cob:L49] is alphanumeric, its
    # figurative zero stores "00000" rather than spaces.
    #
    # THIS IS WHAT MAKES 994 UNREACHABLE AND WHAT LETS A WHOLLY FAILED REWRITE -
    # AND, THROUGH THE HANDLER'S FALL-THROUGH, A WHOLLY FAILED WRITE - RETURN
    # SUCCESS. Anomaly A1. Byte for byte the same defect as
    # [common/irsdfltMT.cbl:L736-L738], so the anomaly log records it once for
    # both `acasirsub3` and `acasirsub5`.
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    logging_data.sql_err = "0" * SQL_ERR_WIDTH
    logging_data.sql_msg = " " * SQL_MSG_WIDTH
    # `go to ba999-exit.` [:L574] - past `ba999-end`'s log, anomaly A38.
    return FsReply.SUCCESS, int(WeError.SUCCESS)



#  THE BRIDGE'S OWN OPEN, CLOSE AND BAD-FUNCTION - AND ITS CONNECTION HANDLE


#: The connection `ba020-Process-Open` establishes and `ba030-Process-Close`
#: releases. WORKING STORAGE OF THE BRIDGE, and module-level here for exactly
#: that reason: all four of the handler's bail-outs leave without performing the
#: close [common/acasirsub5.cbl:L437-L440, :L446-L449, :L463-L466, :L489-L492],
#: so the handle survives the call still open - anomaly A10. A function-local
#: would be released when the frame unwound and would therefore FIX A10.
#:
#: DEVIATION RECORDED (rule R-5): when a later open overwrites this name the
#: compiled program abandons a C handle that stays open until the process exits,
#: whereas CPython drops the last reference and the socket closes. The leak is
#: reproduced in the dimension the migration is judged on - the close is not
#: performed, the cursor and result are not released, and the statuses are not
#: those of a clean close - but not in process-lifetime resource terms, because
#: retaining unreachable connections deliberately would be an invented behaviour
#: of its own. Section 0.8.5 makes table state the observable.
_CONNECTION: MySQLConnectionAbstract | None = None


def _ba020_process_open(
    system: SystemRecord,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None,
    states: CursorStateTable | None = None,
) -> tuple[FsReply, int]:
    """`ba020-Process-Open` [common/irsfinalMT.cbl:L254-L300].

    ::

        string   DB-Schema      delimited by space X"00" into WS-MYSQL-BASE-NAME
        string   DB-Host        delimited by space X"00" into WS-MYSQL-HOST-NAME
        string   DB-UName       delimited by space X"00" into WS-MYSQL-IMPLEMENTATION
        string   DB-UPass       delimited by space X"00" into WS-MYSQL-PASSWORD
        string   DB-Port        delimited by space X"00" into WS-MYSQL-PORT-NUMBER
        string   DB-Socket      delimited by space X"00" into WS-MYSQL-SOCKET
        move     1 to ws-No-Paragraph.
        PERFORM  MYSQL-1000-OPEN  THRU MYSQL-1090-EXIT.
        if       fs-reply not = zero
                 go   to ba999-end.
        move    "OPEN IRS FINAL" to WS-File-Key
        move    zero   to Most-Cursor-Set
        go      to ba999-end.

    NOTE THE ORDER. The bridge stages the six credential fields as
    Schema, Host, UName, UPass, Port, Socket, while the handler's gate moves them
    into `RDB-Data` as Schema, UName, UPass, Port, Host, Socket
    [common/acasirsub5.cbl:L400-L405]. Two different orderings of the same six
    fields in the same call chain, neither observable, both recorded.

    `move zero to Most-Cursor-Set` [:L299] IS WHY THE HANDLER'S TRIPLE HIDES
    ANOMALY A37: every synthesised open resets the cursor, so the stale-cursor
    path is reachable only by calling the published read verb twice.

    `MYSQL-1000-OPEN` is `dal/connection.py`'s, which resolves the six fields
    through the same once-only latch the gate used, so the credentials this open
    sees are the ones the gate loaded and not a re-read.

    Args:
        system: `System-Record`, from which the credentials resolve.
        file_access: `File-Access`, mutated in place.
        dal_common: `ACAS-DAL-Common-data`, unused by the frozen paragraph and
            carried only so the caller's argument list stays uniform.
        transport: The transport policy `dal/connection.py` requires.
        states: The cursor set whose `Most-Cursor-Set` [:L299] this open clears.
            It MUST be the same set the read that follows will fetch from, or the
            reset lands on a different cursor and A37 leaks across calls that the
            frozen program starts clean.

    Returns:
        The `(FS-Reply, We-Error)` pair this paragraph leaves behind.
    """
    global _CONNECTION  # noqa: PLW0603 - the bridge holds this in working storage
    _ba010_initialise(file_access)
    logging_data = file_access.logging_data
    logging_data.ws_no_paragraph = _BRIDGE_TRACE_OPEN  # `move 1 to` [:L287]
    # `PERFORM MYSQL-1000-OPEN THRU MYSQL-1090-EXIT.` [:L288]. The six
    # `string ... delimited by space X"00"` stagings [:L263-L286] are what
    # `connection_parameters` does from the same `RDB-Data` fields.
    outcome = mysql_1000_open(
        system,
        ws_no_paragraph=_BRIDGE_TRACE_OPEN,
        we_error=file_access.we_error,
        transport=transport,
    )
    file_access.fs_reply = int(outcome.fs_reply)
    file_access.we_error = int(outcome.we_error)
    if outcome.sql_err:
        logging_data.sql_err = outcome.sql_err[:SQL_ERR_WIDTH].ljust(SQL_ERR_WIDTH)
    if outcome.sql_msg:
        logging_data.sql_msg = outcome.sql_msg[:SQL_MSG_WIDTH].ljust(SQL_MSG_WIDTH)
    if outcome.sql_state:
        logging_data.sql_state = outcome.sql_state[:SQL_STATE_WIDTH].ljust(
            SQL_STATE_WIDTH
        )
    # `if fs-reply not = zero / go to ba999-end.` [:L289-L290] - Class 4: the
    # target is a peer paragraph that does work (the gated log at [:L602-L604])
    # and then falls through to `ba999-exit`'s `exit program.` [:L606-L607], so
    # the translation is the named call followed by an explicit `return`. The
    # tail work below is skipped; `ba999-end`'s log still runs.
    if file_access.fs_reply != int(FsReply.SUCCESS):
        _CONNECTION = None
        _process_logs_if_testing(dal_common, file_access, "ba999-end/open-failed")
        return FsReply(file_access.fs_reply), file_access.we_error
    _CONNECTION = outcome.connection
    logging_data.ws_file_key = "OPEN IRS FINAL"  # [:L298]
    # `move zero to Most-Cursor-Set` [:L299] - on THE CALLER'S cursor set, not
    # unconditionally on this module's own, so a caller working through its own
    # set gets the reset the frozen program gives it.
    _cursor_state(states).set_cursor_not_active()
    # `go to ba999-end.` [:L300] - which logs [:L602-L604] and exits.
    _process_logs_if_testing(dal_common, file_access, "ba999-end/open")
    return FsReply.SUCCESS, int(WeError.SUCCESS)


def _ba030_process_close(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    *,
    states: CursorStateTable | None = None,
) -> tuple[FsReply, int]:
    """`ba030-Process-Close` [common/irsfinalMT.cbl:L302-L315].

    ::

        if      Cursor-Active         *> this will not occur for the system rows/records
                perform ba998-Free.
        move     2 to ws-No-Paragraph.
        move    "CLOSE IRS FINAL" to WS-File-Key.
              PERFORM MYSQL-1980-CLOSE THRU MYSQL-1999-EXIT
        go      to ba999-end.

    THIS IS THE ONLY PLACE THE RESULT IS FREED ON A SUCCESSFUL READ. A read that
    fetched all twenty-six rows leaves the loop by exhausting its bound rather
    than by an end-of-file exit, so `Most-Cursor-Set` is still 1 and the result
    is still allocated when it returns [:L462-L466]; the close then frees both.
    Skip the close - which all four of the handler's bail-outs do - and neither
    happens.

    NO COMMIT PRECEDES IT, and none is added: `dal/connection.py` records that a
    commit here would suppress the partial state section 0.6.5 requires.

    Args:
        file_access: `File-Access`, mutated in place.
        dal_common: `ACAS-DAL-Common-data`; `sw_testing` gates the log.
        states: The cursor set to free from.

    Returns:
        `(0, 0)` - this paragraph sets no status of its own.
    """
    global _CONNECTION  # noqa: PLW0603 - the bridge holds this in working storage
    _ba010_initialise(file_access)
    state = _cursor_state(states)
    # `if Cursor-Active perform ba998-Free.` [:L303-L304]. The frozen comment is
    # `*> this will not occur for the system rows/records`, which is wrong for
    # this table: a full twenty-six-row read leaves the cursor active.
    if state.cursor_active():
        _ba998_free(file_access, dal_common, state)
    file_access.logging_data.ws_no_paragraph = _BRIDGE_TRACE_CLOSE  # [:L306]
    file_access.logging_data.ws_file_key = "CLOSE IRS FINAL"  # [:L307]
    # `PERFORM MYSQL-1980-CLOSE THRU MYSQL-1999-EXIT` [:L312].
    mysql_1980_close(_CONNECTION)
    _CONNECTION = None
    # `go to ba999-end.` [:L315].
    _process_logs_if_testing(dal_common, file_access, "ba999-end/close")
    return FsReply(file_access.fs_reply), file_access.we_error


def _ba100_bad_function(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> tuple[FsReply, int]:
    """`ba100-Bad-Function` [common/irsfinalMT.cbl:L576-L582].

    ::

        *> Houston; We have a problem
        move     990 to WE-Error.
        move     99 to Fs-Reply.
        go       to ba999-end.

    ANOMALY A19: THE BRIDGE SAYS 990 AND ITS HANDLER SAYS 999
    [common/acasirsub5.cbl:L331-L332, :L508-L509]. Four handler/bridge pairs in
    this folder disagree the same way - `acas029`/`otm5MT`,
    `acasirsub3`/`irsdfltMT`, `acasirsub4`/`irspostingMT` and this one - so it is
    a folder-wide pattern rather than a local slip, and neither side is
    reconciled to the other. A caller of :func:`dispatch` sees 999, because the
    handler never reaches the bridge for a function the bridge would reject.

    Reachable through this module only if a caller drives a bridge verb directly
    with a function code the bridge does not dispatch [:L239-L252].

    Args:
        file_access: `File-Access`, mutated in place.
        dal_common: `ACAS-DAL-Common-data`; `sw_testing` gates the log.

    Returns:
        `(99, 990)`.
    """
    file_access.we_error = BRIDGE_BAD_FUNCTION  # `move 990 to WE-Error.` [:L580]
    file_access.fs_reply = int(FS_REPLY_GENERAL)  # `move 99 to Fs-Reply.` [:L581]
    # `go to ba999-end.` [:L582] - unlike the three fan-out verbs, this one DOES
    # reach the end-of-call log (anomaly A38 is about the verbs, not this).
    _process_logs_if_testing(dal_common, file_access, "ba999-end/bad-function")
    return FS_REPLY_GENERAL, BRIDGE_BAD_FUNCTION


def _ba020_call_dal(
    system: SystemRecord,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    final: IrsFinalRecord,
    *,
    transport: TransportSecurity | None,
    states: CursorStateTable | None,
) -> tuple[FsReply, int]:
    """`ba020-Call-DAL` [common/acasirsub5.cbl:L512-L517] and the bridge's
    dispatch [common/irsfinalMT.cbl:L239-L252].

    The handler's paragraph is four lines::

        ba020-Call-DAL.
            call     "irsfinalMT" using File-Access
                                       ACAS-DAL-Common-data

                                       Final-Record
            end-call.

    THREE OF THE HANDLER'S FIVE PARAMETERS CROSS, with a blank line before the
    third [:L515] - the family's layout habit. `System-Record` and `File-Defs` do
    NOT cross: the bridge gets its credentials from `RDB-Data`, which lives inside
    `File-Access` [copybooks/wsfnctn.cob:L56-L62] and which the handler's gate
    populated. Only two of the twenty handlers name this paragraph
    `ba020-Call-DAL` rather than `ba020-Process-DAL` - `acasirsub3` and this one.

    Rule R-1: THERE IS NO `CALL` HERE. The five arms below are the bridge's own
    `evaluate File-Function` [common/irsfinalMT.cbl:L239-L252] reimplemented in
    Python - the same five codes the handler dispatches, which makes this the one
    handler/bridge pair in the folder where both sides agree on a reduced set.

    Args:
        system: `System-Record` - not passed to the bridge, but needed by the
            open arm because that is where `dal/connection.py` reads the
            credentials the frozen bridge reads from `RDB-Data`.
        file_access: `File-Access` [common/irsfinalMT.cbl:L207].
        dal_common: `ACAS-DAL-Common-data` [:L208].
        final: `Final-Record` [:L209].
        transport: The transport policy for the open arm.
        states: The cursor set the read arm works through.

    Returns:
        The `(FS-Reply, We-Error)` pair the bridge leaves behind.
    """
    function = file_access.file_function
    if function == int(FileFunction.OPEN):  # `when 1` [:L240-L241]
        return _ba020_process_open(
            system, file_access, dal_common, transport=transport, states=states
        )
    if function == int(FileFunction.CLOSE):  # `when 2` [:L242-L243]
        return _ba030_process_close(file_access, dal_common, states=states)
    if function == int(FileFunction.READ_NEXT):  # `when 3` [:L244-L245]
        return _bridge_read_next(file_access, dal_common, final, states=states)
    if function == int(FileFunction.WRITE):  # `when 5` [:L246-L247]
        return _bridge_write(file_access, dal_common, final)
    if function == int(FileFunction.RE_WRITE):  # `when 7` [:L248-L249]
        return _bridge_rewrite(file_access, dal_common, final)
    # `when other / go to ba100-Bad-Function` [:L250-L251]. NOTE: the bridge, like
    # its handler, dispatches NO code 4, 8 or 9 - the only pair in the folder to
    # reduce the set on both sides.
    return _ba100_bad_function(file_access, dal_common)


def _require_connection(file_access: FileAccess) -> MySQLConnectionAbstract:
    """The connection the bridge's working storage is holding.

    `ba040`, `ba070` and `ba090` all issue statements on the handle
    `ba020-Process-Open` established, and the frozen program simply uses it: if no
    open preceded, `MySQL_query` is called on a null handle. There is no
    equivalent of that in Python, so the absence is reported as a programming
    error against this module's own API rather than modelled as a status - rule
    R-3 forbids inventing a validation of accounting data, and this is neither
    accounting data nor a value the frozen program could carry.

    Args:
        file_access: The caller's block, named in the message so the failing
            operation is identifiable.

    Returns:
        The open connection.

    Raises:
        RuntimeError: If no open preceded this verb.
    """
    if _CONNECTION is None:
        raise RuntimeError(
            f"{TABLE}: file-function {file_access.file_function} was reached with "
            "no connection open; ba020-Process-Open "
            "[common/irsfinalMT.cbl:L254-L300] must run first"
        )
    return _CONNECTION


def _bridge_read_next(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    final: IrsFinalRecord,
    *,
    states: CursorStateTable | None,
) -> tuple[FsReply, int]:
    """`when 3 / go to ba040-Process-Read-Next` [common/irsfinalMT.cbl:L244-L245].

    Args:
        file_access: `File-Access`.
        dal_common: `ACAS-DAL-Common-data`.
        final: `Final-Record`.
        states: The cursor set to work through.

    Returns:
        What :func:`read_next` returns.
    """
    return read_next(
        _require_connection(file_access), file_access, dal_common, final, states=states
    )


def _bridge_write(
    file_access: FileAccess, dal_common: AcasDalCommonData, final: IrsFinalRecord
) -> tuple[FsReply, int]:
    """`when 5 / go to ba070-Process-Write` [common/irsfinalMT.cbl:L246-L247].

    Args:
        file_access: `File-Access`.
        dal_common: `ACAS-DAL-Common-data`.
        final: `Final-Record`.

    Returns:
        What :func:`write` returns.
    """
    return write(_require_connection(file_access), file_access, dal_common, final)


def _bridge_rewrite(
    file_access: FileAccess, dal_common: AcasDalCommonData, final: IrsFinalRecord
) -> tuple[FsReply, int]:
    """`when 7 / go to ba090-Process-Rewrite` [common/irsfinalMT.cbl:L248-L249].

    Args:
        file_access: `File-Access`.
        dal_common: `ACAS-DAL-Common-data`.
        final: `Final-Record`.

    Returns:
        What :func:`rewrite` returns - always `(0, 0)`, per anomaly A1.
    """
    return rewrite(_require_connection(file_access), file_access, dal_common, final)



#  `ba010`/`ba012-Test-WS-Rec-Size-2` - THE ONCE-ONLY GATE BEFORE ANY BRIDGE CALL


def _record_size_gate(
    system: SystemRecord, file_access: FileAccess, dal_common: AcasDalCommonData
) -> tuple[FsReply, int] | None:
    """`ba012-Test-WS-Rec-Size-2` [common/acasirsub5.cbl:L366-L406].

    ::

        if       A = zero                      *> so it is being called first time
                 move function Length ( Final-Record ) to A
                 move function length ( Record-5 ) to B
                 if   A < B          *> COULD LET caller module deal with these errors !!!!!!!
                      move 901 to WE-Error
                      move 99 to fs-reply    *> allow for last field ( FILLER) not being present in layout.
                 end-if
                 if   WE-Error = 901
                      ... string IR902 ... display ... accept ...
                      go to ba-rdbms-exit
                 end-if
                 move RDBMS-DB-Name to DB-Schema
                 move RDBMS-User    to DB-UName
                 move RDBMS-Passwd  to DB-UPass
                 move RDBMS-Port    to DB-Port
                 move RDBMS-Host    to DB-Host
                 move RDBMS-Socket  to DB-Socket
        end-if.

    A ONCE-ONLY LATCH, and its own comment says so:
    `*> Test on very first call only (So do NOT use var A & B again)`
    [:L360], with `77 A pic 9(4) value zero.  *> A & B used in 1st test ONLY`
    [:L115-L116]. So THE CREDENTIALS ARE CAPTURED ONCE AND NEVER REFRESHED - the
    same construct `dal/connection.py` reproduces for `load_rdb_data_once`, whose
    docstring heads itself "ANOMALY A-1 - REPRODUCED, NOT FIXED". Both latches
    resolve through that one function here, so they cannot disagree.

    ON FAILURE THE BRIDGE IS NEVER CALLED. `go to ba-rdbms-exit` [:L393] leaves
    the section outright with `(99, 901)`, having displayed the two messages and
    waited on an `accept`. THE CONTROL TRANSFER IS PRESERVED AND THE PRESENTATION
    IS DROPPED: `display Display-Blk at 2301`, `display IR901 at 2401` and
    `accept Accept-Reply at 2433` [:L387-L392] are screen work with no database
    effect, and section 0.3.4 rules that an `accept` whose only effect is to block
    a terminal is dropped while the transfer that follows it is kept.

    The frozen source's own two remarks on this block are worth carrying, because
    they are what the anomaly log cites: `*> COULD LET caller module deal with
    these errors !!!!!!!` [:L375], seven exclamation marks and byte-identical to
    `acasirsub3`'s; and `*> allow for last field ( FILLER) not being present in
    layout.` [:L377], which explains why the test is `A < B` and not `A not = B`.

    Note also that `move function Length` and `move function length` differ in
    case on adjacent lines [:L369, :L372] - anomaly A29, now confirmed in four
    handlers - and that the message text embeds the literal `"IRS-Final-Rec = "`,
    which is table-specific.

    THE SIX CREDENTIAL MOVES ARE IN A DIFFERENT ORDER FROM THE BRIDGE'S SIX
    STAGINGS: Schema, UName, UPass, Port, Host, Socket here [:L400-L405] against
    Schema, Host, UName, UPass, Port, Socket there
    [common/irsfinalMT.cbl:L263-L286]. Neither is observable; both are recorded.

    Args:
        system: `System-Record`, the source of the six credential fields.
        file_access: `File-Access`; `RDB-Data` is populated here.
        dal_common: `ACAS-DAL-Common-data`; `sw_testing` gates the log at
            [common/acasirsub5.cbl:L389-L391].

    Returns:
        ``None`` when the gate passes - the caller continues to
        `ba015-Test-Ends`. `(99, 901)` when it does not, which the caller must
        return immediately without touching the bridge.
    """
    global _RECORD_SIZE_A, _RECORD_SIZE_B  # noqa: PLW0603 - frozen `77` latch
    # `if A = zero  *> so it is being called first time` [:L368]. Every later call
    # skips the whole block, credentials included.
    if _RECORD_SIZE_A != 0:
        return None

    # `move function Length ( Final-Record ) to A` [:L369-L371] and
    # `move function length ( Record-5 ) to B` [:L372-L374].
    _RECORD_SIZE_A = WS_RECORD_BYTES
    _RECORD_SIZE_B = FD_RECORD_BYTES

    # `if A < B` [:L375]. Both are 655 in the frozen sources, so this arm does not
    # fire - but it is computed and compared, not assumed.
    if _RECORD_SIZE_A < _RECORD_SIZE_B:
        file_access.we_error = RECORD_SIZE_ERROR  # `move 901 to WE-Error` [:L376]
        file_access.fs_reply = int(FS_REPLY_GENERAL)  # `move 99 to fs-reply` [:L377]

    # `if WE-Error = 901` [:L379] - a second test on the value the first arm just
    # set, rather than an `else`, so a caller arriving with 901 already in
    # `We-Error` would take this arm too. Reproduced as written.
    if file_access.we_error == RECORD_SIZE_ERROR:
        # `string IR902 ... A ... " < " ... "IRS-Final-Rec = " ... B into
        # Display-Blk` [:L381-L386] then two `display`s and an `accept`
        # [:L387-L392] - presentation, dropped. The message text itself is kept
        # as a log record so the diagnostic is not simply lost.
        _LOG.error(
            "acasirsub5: IR902 Program Error: Temp rec = %s < IRS-Final-Rec = %s",
            _RECORD_SIZE_A,
            _RECORD_SIZE_B,
        )
        # `if Testing-1 perform Ca-Process-Logs` [:L389-L391] - one of only two
        # GATED logging sites in the handler; the seven in `ba015` are not.
        _process_logs_if_testing(dal_common, file_access, "ba012/rec-size")
        # `go to ba-rdbms-exit` [:L393] - Class 3, and THE BRIDGE IS NEVER CALLED.
        return FS_REPLY_GENERAL, RECORD_SIZE_ERROR

    # [:L400-L405] The six credential moves, in the handler's own order. They
    # resolve through the same once-only latch `mysql_1000_open` uses, so the
    # values the bridge's open sees are these and not a re-read.
    rdb = load_rdb_data_once(system)
    rdb_data = file_access.rdb_data
    rdb_data.db_schema = rdb.db_schema  # `RDBMS-DB-Name to DB-Schema` [:L400]
    rdb_data.db_uname = rdb.db_uname  # `RDBMS-User to DB-UName` [:L401]
    rdb_data.db_upass = rdb.db_upass  # `RDBMS-Passwd to DB-UPass` [:L402]
    rdb_data.db_port = rdb.db_port  # `RDBMS-Port to DB-Port` [:L403]
    rdb_data.db_host = rdb.db_host  # `RDBMS-Host to DB-Host` [:L404]
    rdb_data.db_socket = rdb.db_socket  # `RDBMS-Socket to DB-Socket` [:L405]
    return None


#  `ba015-Test-Ends` - THE SYNTHESISED ORCHESTRATION, AND THE FALL-THROUGH


def _read_triple(
    system: SystemRecord,
    final: IrsFinalRecord,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None,
    states: CursorStateTable | None,
) -> tuple[FsReply, int]:
    """`if fn-read-next` inside `ba015-Test-Ends` [common/acasirsub5.cbl:L432-L458].

    ::

         if       fn-read-next
                  set     fn-Open  to true
                  set     fn-Input to true
                  perform ba020-Call-DAL                   *> open
                  perform Ca-Process-Logs
                  if      Fs-Reply not = zero
                       or WE-Error not = zero
                          go to ba-rdbms-Exit
                  end-if
                  set     fn-Read-Next to true
                  perform ba020-Call-DAL                   *> Read
                  move    FS-Reply to WS-Save-FS-Reply     *> save the statuses
                  move    WE-Error to WS-Save-WE-Error
                  perform Ca-Process-Logs                  *> temp only during testing
                  if      FS-Reply not = zero
                      or  WE-Error not = zero
                          go      to ba-RDBMS-Exit
                  end-if
                  set     fn-Close to true
                  perform ba020-Call-DAL
                  perform Ca-Process-Logs                  *> temp only during testing
                  move    WS-Save-FS-Reply to FS-Reply     *> restore them
                  move    WS-Save-WE-Error to WE-Error
                  move    "Open, Read, Close" to WS-File-key
                  perform Ca-Process-Logs                  *> temp only during testing
                  go      to ba-RDBMS-Exit
         end-if.

    THREE BRIDGE CALLS FOR ONE LOGICAL READ. The IRS callers issue neither an open
    nor a close [:L161-L168], so the handler synthesises both around every read -
    which is what the maintainer meant by `*> Here we do non standard DAL things`
    [:L418-L419].

    ANOMALY A10 - BOTH BAIL-OUTS SKIP THE CLOSE. The `go to ba-rdbms-Exit` at
    [:L439] and the `go to ba-RDBMS-Exit` at [:L448] leave `ba015-Test-Ends`
    without ever setting `fn-Close`, so on any failure of the open or of the read
    the connection that [:L435] established is never closed and the cursor
    `ba040` may have left active is never freed. The write triple, by contrast,
    closes UNCONDITIONALLY [:L471-L472] - an asymmetry between two paragraphs
    twenty lines apart. Both bail-outs are Class 3 transfers per section 0.4.2 -
    `ba-rdbms-exit.` is the section's trailing exit label and its whole body is
    `exit section.` [:L521-L522] - so each becomes a `return`. What makes them
    anomalous is not the class but WHERE they leave from: mid-way through the
    `if fn-read-next` block, with the block's own remaining statements - the
    close among them - never reached. Translating them as anything that still
    closed would be a fix, not a migration.

    THE CLOSE'S OWN STATUS IS DISCARDED. [:L443-L444] save the READ's pair before
    the close runs and [:L453-L454] put it back afterwards, so whatever
    `ba030-Process-Close` and `MYSQL-1980-CLOSE` leave in `FS-Reply`/`WE-Error` is
    overwritten and can never be observed. A close that failed reports the read's
    status.

    ANOMALY A26 - FOUR UNGATED LOG CALLS on this one path [:L436, :L445, :L452,
    :L456], where `acasirsub3`'s read has three and where the handler's own
    `Ca-Process-Logs` is annotated `*> Not called on DAL access as it does it
    already` [:L525]. None is wrapped in `if Testing-1`, unlike every one of the
    bridge's seven sites.

    `Access-Type` IS NEVER RESET. [:L434] sets it to `fn-Input` and nothing clears
    it before the close at [:L450-L451], so the block leaves this function with
    `File-Function` = 2 and `Access-Type` = 1 even though the caller asked for
    function 3. The bridge's close does not examine the access type, so this is
    observable only to a caller that inspects the block - but it is what the
    frozen program leaves, so it is what is left here.

    Args:
        system: `System-Record` - needed by the open arm alone.
        final: `Final-Record`, reassembled in place by the read arm.
        file_access: `File-Access`; `File-Function`, `Access-Type` and both status
            fields are mutated in place exactly as the `set`/`move` verbs do.
        dal_common: `ACAS-DAL-Common-data`.
        transport: The transport policy for the synthesised open.
        states: The cursor set to work through.

    Returns:
        The `(FS-Reply, We-Error)` pair. On either bail-out it is the failing
        call's own pair; otherwise it is the READ's pair, restored across the
        close.
    """
    # `set fn-Open to true` [:L433] and `set fn-Input to true` [:L434].
    file_access.file_function = int(FileFunction.OPEN)
    file_access.access_type = int(AccessType.INPUT)
    # `perform ba020-Call-DAL   *> open` [:L435].
    _ba020_call_dal(
        system, file_access, dal_common, final, transport=transport, states=states
    )
    # `perform Ca-Process-Logs` [:L436] - UNGATED. First of four.
    _process_logs(dal_common, file_access, "ba015/read-open")
    # `if Fs-Reply not = zero or WE-Error not = zero / go to ba-rdbms-Exit`
    # [:L437-L439]. ANOMALY A10: NO CLOSE. Class 3 transfer to `ba-rdbms-exit.`,
    # whose body is `exit section.` [:L521-L522]; the rest of this block,
    # including the close, is deliberately not performed.
    if file_access.fs_reply != 0 or file_access.we_error != 0:
        return FsReply(file_access.fs_reply), file_access.we_error

    # `set fn-Read-Next to true` [:L441] then
    # `perform ba020-Call-DAL   *> Read` [:L442].
    file_access.file_function = int(FileFunction.READ_NEXT)
    _ba020_call_dal(
        system, file_access, dal_common, final, transport=transport, states=states
    )
    # `move FS-Reply to WS-Save-FS-Reply  *> save the statuses` [:L443] and
    # `move WE-Error to WS-Save-WE-Error` [:L444]. These are the handler's own
    # `77 WS-Save-FS-Reply pic 99` / `77 WS-Save-WE-Error pic 999`, whose
    # declaration carries `*> These 2 for acasirsub3 & 5` [:L112-L113]. Unlike the
    # bridge's `ws-saved-fs-reply` (anomaly A44) they are written before every read
    # of them, so a call-local pair is faithful and a module-level one would add a
    # persistence the frozen handler does not have.
    ws_save_fs_reply = file_access.fs_reply
    ws_save_we_error = file_access.we_error
    # `perform Ca-Process-Logs  *> temp only during testing` [:L445] - second.
    _process_logs(dal_common, file_access, "ba015/read-verb")
    # `if FS-Reply not = zero or WE-Error not = zero / go to ba-RDBMS-Exit`
    # [:L446-L448]. ANOMALY A10 again: NO CLOSE, so a read that reported
    # `_ba040_no_data`'s unerased `(10, 10)` leaks the connection AND the result.
    if file_access.fs_reply != 0 or file_access.we_error != 0:
        return FsReply(file_access.fs_reply), file_access.we_error

    # `set fn-Close to true` [:L450] then `perform ba020-Call-DAL` [:L451]. NOTE
    # that `Access-Type` still holds `fn-Input` from [:L434]; nothing resets it.
    file_access.file_function = int(FileFunction.CLOSE)
    _ba020_call_dal(
        system, file_access, dal_common, final, transport=transport, states=states
    )
    # `perform Ca-Process-Logs  *> temp only during testing` [:L452] - third. It
    # runs BEFORE the restore below, so this one log record is the only place the
    # close's own status is ever visible, and only when logging is compiled in.
    _process_logs(dal_common, file_access, "ba015/read-close")
    # `move WS-Save-FS-Reply to FS-Reply  *> restore them` [:L453] and
    # `move WS-Save-WE-Error to WE-Error` [:L454]. THE CLOSE'S STATUS IS DISCARDED
    # HERE.
    file_access.fs_reply = ws_save_fs_reply
    file_access.we_error = ws_save_we_error
    # `move "Open, Read, Close" to WS-File-key` [:L455]. `WS-File-Key pic x(64)`
    # [copybooks/wsfnctn.cob:L52], so the literal is space-padded on the move; the
    # record layer owns that padding and the value is carried as written.
    file_access.logging_data.ws_file_key = "Open, Read, Close"
    # `perform Ca-Process-Logs  *> temp only during testing` [:L456] - fourth.
    _process_logs(dal_common, file_access, "ba015/read-done")
    # `go to ba-RDBMS-Exit` [:L457].
    return FsReply(file_access.fs_reply), file_access.we_error


def _write_triple(
    system: SystemRecord,
    final: IrsFinalRecord,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None,
    states: CursorStateTable | None,
) -> tuple[FsReply, int] | None:
    """`if fn-Write` inside `ba015-Test-Ends` [common/acasirsub5.cbl:L459-L483].

    ::

         if       fn-Write
                  set     fn-Open  to true
                  set     fn-I-O to true
                  perform ba020-Call-DAL                   *> Open
                  if      Fs-Reply not = zero
                       or WE-Error not = zero
                          go to ba-rdbms-Exit
                  end-if
                  set     fn-Write to true
                  perform ba020-Call-DAL                   *> write
                  move    FS-Reply to WS-Save-FS-Reply     *> save the statuses
                  move    WE-Error to WS-Save-WE-Error
                  set     fn-Close to true
                  perform ba020-Call-DAL
                  move    WS-Save-FS-Reply to FS-Reply     *> restore them
                  move    WS-Save-WE-Error to WE-Error
                  if      (fs-Reply not = zero or
                          WE-Error not = zero)
                          move    "Open, Write failed, Close" to WS-File-Key
                          perform Ca-Process-Logs            *> temp only during testing
                          set     fn-Re-write to true
                          move zero to fs-reply we-error   *> clear if used in write
                  else
                          go      to ba-RDBMS-Exit
         end-if.

    *** ANOMALIES A1 AND A2 LIVE IN THE LAST NINE LINES ABOVE. ***

    ANOMALY A2 - ONE `end-if.` CLOSES TWO NESTED `if`s [:L483]. The outer
    `if fn-Write` [:L459] has no terminator of its own; the period on the inner
    `end-if` ends the whole sentence and closes both. So:

    * the SUCCESS arm leaves by the `else / go to ba-RDBMS-Exit` [:L481-L482];
    * the FAILURE arm has NO terminator at all. It runs [:L477-L480] and control
      then reaches the NEXT SENTENCE, which is `if fn-Re-write` [:L485] - and
      [:L479] has just set that flag true.

    ANOMALY A1 - AND THE FAILURE IS ERASED ON THE WAY. [:L480] is
    `move zero to fs-reply we-error  *> clear if used in write`, so the rewrite
    that is about to run begins from a clean status, and the rewrite's own
    unguarded reset [common/irsfinalMT.cbl:L571-L573] guarantees `(0, 0)` when it
    finishes. A WRITE THAT FAILED ON ALL TWENTY-SIX ROWS RETURNS SUCCESS. This is
    the identical construct class as the plan's Anomaly #1
    [sales/sl060.cbl:L1172-L1178] - there a missing terminating period, here a
    missing `end-if`, same mechanism and same consequence. Rule R-4: reproduced,
    not fixed. `acasirsub3`/`irsdfltMT` carry the same pair, so two of the twenty
    data-access modules swallow write failures.

    THE FALL-THROUGH IS SIGNALLED BY RETURNING `None`, and `dispatch` continues
    into :func:`_rewrite_triple` when it sees that. It is expressed as a return
    value rather than as a call from inside this function because the frozen
    construct is not a transfer at all - nothing branches to the rewrite; control
    simply arrives at the next sentence. Section 0.4.2's Class 4 asks for a proof
    per site, and the proof here is that single `end-if.` at [:L483]: with it
    binding to the inner `if`, the outer `if`'s THEN branch has exactly one exit,
    fall-through, and the statement it falls into is [:L485].

    THE CLOSE IS UNCONDITIONAL [:L471-L472], unlike either of the read triple's
    two bail-outs (anomaly A10). Only the OPEN's failure [:L463-L465] skips it.
    ANOMALY A14 is the flat path's mirror of the same asymmetry [:L312-L322].

    THIS ARM HAS NO LOG CALL AROUND ITS OWN VERB. The read triple logs four times
    and the rewrite triple once; the write logs ONLY on the failure arm [:L478].
    So a successful write produces no log record from `ba015` at all.

    Args:
        system: `System-Record` - needed by the open arm alone.
        final: `Final-Record`, the source of the twenty-six rows.
        file_access: `File-Access`, mutated in place. On the fall-through path it
            is left with `File-Function` = `fn-Re-write` and a zeroed status pair,
            exactly as [:L479-L480] leaves it.
        dal_common: `ACAS-DAL-Common-data`.
        transport: The transport policy for the synthesised open.
        states: The cursor set to work through.

    Returns:
        The `(FS-Reply, We-Error)` pair when the open failed [:L465] or when the
        write succeeded [:L482]; `None` when the write failed, meaning the caller
        must fall through into the rewrite.
    """
    # `set fn-Open to true` [:L460] and `set fn-I-O to true` [:L461]. The write
    # path opens I-O where the read path opens INPUT [:L434].
    file_access.file_function = int(FileFunction.OPEN)
    file_access.access_type = int(AccessType.I_O)
    # `perform ba020-Call-DAL   *> Open` [:L462]. NOTE: no `Ca-Process-Logs` here,
    # where the read triple has one [:L436].
    _ba020_call_dal(
        system, file_access, dal_common, final, transport=transport, states=states
    )
    # `if Fs-Reply not = zero or WE-Error not = zero / go to ba-rdbms-Exit`
    # [:L463-L465] - the ONE path in this arm that skips the close (anomaly A10).
    if file_access.fs_reply != 0 or file_access.we_error != 0:
        return FsReply(file_access.fs_reply), file_access.we_error

    # `set fn-Write to true` [:L467] then
    # `perform ba020-Call-DAL   *> write` [:L468].
    file_access.file_function = int(FileFunction.WRITE)
    _ba020_call_dal(
        system, file_access, dal_common, final, transport=transport, states=states
    )
    # `move FS-Reply to WS-Save-FS-Reply  *> save the statuses` [:L469-L470].
    ws_save_fs_reply = file_access.fs_reply
    ws_save_we_error = file_access.we_error
    # `set fn-Close to true` [:L471] then `perform ba020-Call-DAL` [:L472] -
    # UNCONDITIONAL, and with `Access-Type` still holding `fn-I-O`.
    file_access.file_function = int(FileFunction.CLOSE)
    _ba020_call_dal(
        system, file_access, dal_common, final, transport=transport, states=states
    )
    # `move WS-Save-FS-Reply to FS-Reply  *> restore them` [:L473-L474]. The
    # close's own status is discarded here exactly as in the read triple.
    file_access.fs_reply = ws_save_fs_reply
    file_access.we_error = ws_save_we_error

    # `if (fs-Reply not = zero or WE-Error not = zero)` [:L475-L476].
    if file_access.fs_reply != 0 or file_access.we_error != 0:
        # `move "Open, Write failed, Close" to WS-File-Key` [:L477].
        file_access.logging_data.ws_file_key = "Open, Write failed, Close"
        # `perform Ca-Process-Logs  *> temp only during testing` [:L478] - UNGATED,
        # and the ONLY log record this arm ever emits. It runs BEFORE the erasure
        # below, so the failing status reaches the log even though it never reaches
        # the caller.
        _process_logs(dal_common, file_access, "ba015/write-failed")
        # `set fn-Re-write to true` [:L479].
        file_access.file_function = int(FileFunction.RE_WRITE)
        # *** ANOMALY A1 *** `move zero to fs-reply we-error
        # *> clear if used in write` [:L480]. THE FAILURE IS ERASED HERE.
        file_access.fs_reply = int(FsReply.SUCCESS)
        file_access.we_error = int(WeError.SUCCESS)
        # *** ANOMALY A2 *** No terminator: the single `end-if.` at [:L483] closes
        # both `if`s, so control falls through to `if fn-Re-write` [:L485].
        # `None` is that fall-through.
        return None

    # `else / go to ba-RDBMS-Exit` [:L481-L482] - the write succeeded.
    #
    # ANOMALY A47: AND THAT IS ALL THE `else` DOES. No `move ... to WS-File-Key`
    # and no `perform Ca-Process-Logs`, where the read ends with
    # `move "Open, Read, Close"` [:L455] and the rewrite with
    # `move "Open, Rewrite, Close"` [:L501], each followed by a log. So a clean
    # write returns with the key still reading `"CLOSE IRS FINAL"`, put there by
    # `ba030-Process-Close` [common/irsfinalMT.cbl:L307], and emits no record of
    # its own - the only one of the three dispositions whose trace does not name
    # the operation. Nothing is added here to make it symmetric.
    return FsReply(file_access.fs_reply), file_access.we_error


def _rewrite_triple(
    system: SystemRecord,
    final: IrsFinalRecord,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None,
    states: CursorStateTable | None,
) -> tuple[FsReply, int]:
    """`if fn-Re-write` inside `ba015-Test-Ends` [common/acasirsub5.cbl:L485-L504].

    ::

         if       fn-Re-write
                  set     fn-Open  to true
                  set     fn-I-O to true
                  perform ba020-Call-DAL                   *> Open
                  if      Fs-Reply not = zero
                       or WE-Error not = zero
                          go to ba-rdbms-Exit
                  end-if
                  set     fn-Re-write to true
                  perform ba020-Call-DAL                   *> write
                  move    FS-Reply to WS-Save-FS-Reply     *> save the statuses
                  move    WE-Error to WS-Save-WE-Error
                  set     fn-Close to true
                  perform ba020-Call-DAL
                  move    WS-Save-FS-Reply to FS-Reply     *> restore them
                  move    WS-Save-WE-Error to WE-Error
                  move    "Open, Rewrite, Close" to WS-File-key
                  perform Ca-Process-Logs                  *> temp only during testing
                  go      to ba-RDBMS-Exit
         end-if.

    REACHED TWO WAYS: from a caller that asked for function 7, and from the
    write arm's fall-through (anomalies A1 and A2, see :func:`_write_triple`).
    ANOMALY A16 is the same merging on the flat path, where `when 5` falls
    through to `when 7` in the `evaluate` [:L202-L204] with the frozen comment
    `*> write/rewrite can do the same ... as file is opened as output.`

    THE SAVE AND RESTORE ARE FUTILE HERE. [:L495-L496] and [:L499-L500] carry the
    rewrite's status across the close, but `ba090-Process-Rewrite` has already
    cleared `FS-Reply`, `WE-Error`, `SQL-Err` and `SQL-Msg` unconditionally at
    [common/irsfinalMT.cbl:L571-L573], so the pair being preserved is always
    `(0, 0)`. That is anomaly A1's second half, and it is why `move 994 to
    WE-Error` [common/irsfinalMT.cbl:L563] is permanently unobservable.

    ANOMALY A46: the bridge call on this arm is annotated `*> write` [:L494],
    copied verbatim from the write arm [:L468] - a comment-only divergence, in the
    same cosmetic family as anomaly A29's `function Length` / `function length`
    pair, and recorded because rule R-5 asks that every difference be visible.

    THE BAIL-OUT SKIPS THE CLOSE [:L489-L491] - anomaly A10 for the third and
    fourth time in this section, counting the read's two. Only the write arm
    closes unconditionally.

    ONE LOG CALL, and it is UNGATED [:L502], after the file-key move.

    Args:
        system: `System-Record` - needed by the open arm alone.
        final: `Final-Record`, the source of the twenty-six `UPDATE`s.
        file_access: `File-Access`, mutated in place.
        dal_common: `ACAS-DAL-Common-data`.
        transport: The transport policy for the synthesised open.
        states: The cursor set to work through.

    Returns:
        The `(FS-Reply, We-Error)` pair - `(0, 0)` on every path that reaches the
        rewrite verb, per anomaly A1, and the open's own pair on the bail-out.
    """
    # `set fn-Open to true` [:L486] and `set fn-I-O to true` [:L487].
    file_access.file_function = int(FileFunction.OPEN)
    file_access.access_type = int(AccessType.I_O)
    # `perform ba020-Call-DAL   *> Open` [:L488].
    _ba020_call_dal(
        system, file_access, dal_common, final, transport=transport, states=states
    )
    # `if Fs-Reply not = zero or WE-Error not = zero / go to ba-rdbms-Exit`
    # [:L489-L491] - ANOMALY A10: NO CLOSE.
    if file_access.fs_reply != 0 or file_access.we_error != 0:
        return FsReply(file_access.fs_reply), file_access.we_error

    # `set fn-Re-write to true` [:L493] then
    # `perform ba020-Call-DAL   *> write` [:L494] - ANOMALY A46, the comment says
    # write on the rewrite path.
    file_access.file_function = int(FileFunction.RE_WRITE)
    _ba020_call_dal(
        system, file_access, dal_common, final, transport=transport, states=states
    )
    # `move FS-Reply to WS-Save-FS-Reply  *> save the statuses` [:L495-L496].
    # Always `(0, 0)` by the time this runs - see the docstring.
    ws_save_fs_reply = file_access.fs_reply
    ws_save_we_error = file_access.we_error
    # `set fn-Close to true` [:L497] then `perform ba020-Call-DAL` [:L498].
    file_access.file_function = int(FileFunction.CLOSE)
    _ba020_call_dal(
        system, file_access, dal_common, final, transport=transport, states=states
    )
    # `move WS-Save-FS-Reply to FS-Reply  *> restore them` [:L499-L500]. This puts
    # the erased pair back over whatever the close reported, so a close that failed
    # after a rewrite is invisible too.
    file_access.fs_reply = ws_save_fs_reply
    file_access.we_error = ws_save_we_error
    # `move "Open, Rewrite, Close" to WS-File-key` [:L501].
    file_access.logging_data.ws_file_key = "Open, Rewrite, Close"
    # `perform Ca-Process-Logs  *> temp only during testing` [:L502] - UNGATED.
    _process_logs(dal_common, file_access, "ba015/rewrite-done")
    # `go to ba-RDBMS-Exit` [:L503].
    return FsReply(file_access.fs_reply), file_access.we_error



def dispatch(
    system: SystemRecord,
    final: IrsFinalRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None = None,
    states: CursorStateTable | None = None,
) -> tuple[FsReply, int]:
    """`call "acasirsub5"` - the handler entry [common/acasirsub5.cbl:L143-L149].

    ::

        Procedure Division Using System-Record

                                 Final-Record

                                 File-Access
                                 File-Defs
                                 ACAS-DAL-Common-data.

    PARAMETER ORDER PRESERVED EXACTLY, per the section 0.4.3 contract. The blank
    lines at [:L144] and [:L146] are the family's layout habit. The facade calls
    it as `call "acasirsub5" using WS-System-Record Final-Record File-Access
    File-Defs ACAS-DAL-Common-data` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:
    L84-L89] after `move 1 to File-Key-No  *> 1 = Primary` [:L83].

    WHY THIS FUNCTION SYNTHESISES OPENS AND CLOSES THE CALLER DID NOT ASK FOR -
    the maintainer's own warning [common/acasirsub5.cbl:L161-L168]::

        *> WARNING The modules acasirsub5 for Final as well as acasirsub3
        *> for defaults has to be modified as IRS only does a read or write
        *>   and not a direct open or close so
        *>   it has to be done here when processing RDB.
        *>
        *>   For Cobol files these have been changed to do the same so direct
        *>    calls to open and close are not needed or wanted.
        *>     so return with fs-reply & we-error = zero.

    and his own label for the result, at the head of `ba015-Test-Ends`
    [:L418-L419]: `*> Here we do non standard DAL things to handle open & close
    pre / post to calls for Read and write.`

    THE SIX ARMS, in the order `ba015-Test-Ends` tests them:

    * `if fn-open` [:L421-L424] - IGNORED. `move zero to FS-Reply WE-Error` and
      out. The access type is never examined, which is why all four published
      open forms are the same no-op.
    * `if fn-close` [:L425-L430] - IGNORED, after `move zero to File-Function
      Access-Type` [:L426-L427], so a close ZEROES THE FUNCTION CODE IT WAS
      DISPATCHED ON. Then an UNGATED `perform Ca-Process-Logs` [:L428], whose
      frozen comment is `*> Close ignore & close logger`.
    * `if fn-read-next` [:L432-L458] - open(input), read, close, with BOTH
      bail-outs skipping the close (anomaly A10) and the read's own statuses
      saved across the close so THE CLOSE'S STATUS IS DISCARDED [:L443-L444,
      :L453-L454]. FOUR ungated log calls [:L436, :L445, :L452, :L456] where
      `acasirsub3`'s read has three.
    * `if fn-Write` [:L459-L483] - open(i-o), write, then an UNCONDITIONAL close
      [:L471-L472] unlike the read's, then THE FALL-THROUGH described below.
    * `if fn-Re-write` [:L485-L504] - open(i-o), rewrite, close, restore, one log
      call, out.
    * anything else [:L506-L510] - `move 999 to WE-Error`, `move 99 to FS-Reply`.
      Anomaly A19: the bridge would have said 990 [common/irsfinalMT.cbl:L580].

    *** THE FALL-THROUGH - ANOMALIES A1 AND A2 *** [:L475-L483]::

        if      (fs-Reply not = zero or
                WE-Error not = zero)
                move    "Open, Write failed, Close" to WS-File-Key
                perform Ca-Process-Logs            *> temp only during testing
                set     fn-Re-write to true
                move zero to fs-reply we-error   *> clear if used in write
        else
                go      to ba-RDBMS-Exit
        end-if.

    ONE `end-if.` CLOSES BOTH THE INNER `if` AND, THROUGH ITS PERIOD, THE OUTER
    `if fn-Write`. So the success arm returns by its `else`, and THE FAILURE ARM
    HAS NO TERMINATOR OF ITS OWN: it sets `fn-Re-write`, erases the status, and
    control continues to the very next statement, which is `if fn-Re-write`
    [:L485] - now true. A FAILED WRITE IS SILENTLY RETRIED AS A REWRITE WITH THE
    FAILURE ALREADY ERASED, and the rewrite's own unconditional reset
    [common/irsfinalMT.cbl:L571-L573] then guarantees `(0, 0)`.

    THE CALLER CANNOT TELL A FAILED WRITE FROM A SUCCESSFUL ONE. That is the
    behaviour of the compiled program and rule R-4 makes reproducing it
    mandatory: "A defect reproduced is correct; a defect fixed is a failure."
    `acasirsub3`/`irsdfltMT` carry the identical pair, so TWO of the twenty
    data-access modules swallow write failures.

    NO RECOVERY IS ATTEMPTED HERE. `ba020-Call-DAL`'s own trailing comment is
    `*>   Any errors leave it to caller to recover from` [:L519]. The IRS facade
    convention supplies that recovery, and it is drastic: `irsub5-Check-4-Errors`
    displays `IR915`, performs `acasirsub5-Close` and transfers to
    `Open-Error-Continued`, which ends in `goback.`
    [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L348-L364] - a return from the
    PROGRAM, not from the paragraph. Only the two open verbs perform that check
    [:L291, :L297]; read, write, rewrite and close do not.

    Args:
        system: `System-Record` [:L143].
        final: `Final-Record` [:L145].
        file_access: `File-Access` [:L147] - carries the function code, the
            access type, `RDB-Data` and `Logging-Data`, all mutated in place.
        file_defs: `File-Defs` [:L148]. The frozen handler copies
            `wsnames.cob` for its flat-file paths [:L135] and the RDB path uses
            none of them; carried so the linkage matches and so a caller cannot
            call this without having one.
        dal_common: `ACAS-DAL-Common-data` [:L149].
        transport: The transport policy `dal/connection.py` requires of every
            open. Not a frozen parameter - the frozen bridge has no transport
            security at all - and keyword-only for that reason.
        states: The cursor set to work through. Keyword-only, and defaulted to
            this module's own so two runs are byte-identical (rule R-6).

    Returns:
        The `(FS-Reply, We-Error)` pair, with no recovery applied.
    """
    # `move 1 to WS-Log-System` [:L158] and `move 14 to WS-Log-File-No` [:L159],
    # in `aa010-main` before anything else.
    logging_data = file_access.logging_data
    logging_data.ws_log_system = int(WS_LOG_SYSTEM)
    logging_data.ws_log_file_no = WS_LOG_FILE_NO_FLAT
    # `move 1 to File-Key-No  *> 1 = Primary`
    # [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L83] - one key of reference
    # [common/irsfinalMT.cbl:L119], so this is always 1.
    logging_data.file_key_no = KEY_COUNT

    # `if not FS-Cobol-Files-Used / move RDBMS-Flat-Statuses to
    # FA-RDBMS-Flat-Statuses / perform ba-Process-RDBMS  *> Can't hurt /
    # go to AA-Main-Exit` [:L172-L176]. Rule R-1 makes this module the RDB path
    # only, so the flat branch at [:L180-L348] is a recorded omission and the
    # copy below is the one statement of that block which does reach here.
    file_access.fa_rdbms_flat_statuses.fa_file_system_used = (
        system.system_data_block.rdbms_flat_statuses.file_system_used
    )
    file_access.fa_rdbms_flat_statuses.fa_file_duplicates_in_use = (
        system.system_data_block.rdbms_flat_statuses.file_duplicates_in_use
    )

    # `ba010-Test-WS-Rec-Size.` [:L358] contains ONLY
    # `move 24 to WS-Log-File-no.  *> for FHlogger` [:L364] and is reached by
    # fall-through into `ba012`, so the 14 set above is replaced on EVERY RDB
    # call while the flat path keeps 14 - the pair that makes this the folder's
    # only uncollided file number.
    logging_data.ws_log_file_no = WS_LOG_FILE_NO_RDB

    # `perform ba012-Test-WS-Rec-Size-2` by fall-through [:L366].
    refused = _record_size_gate(system, file_access, dal_common)
    if refused is not None:
        return refused

    function = file_access.file_function

    # `if fn-open  *> Open ignore` [:L421-L424]. ANOMALY A15's RDB half: no
    # logging, no bridge call, no state change beyond the status pair.
    if function == int(FileFunction.OPEN):
        file_access.fs_reply = int(FsReply.SUCCESS)
        file_access.we_error = int(WeError.SUCCESS)
        return FsReply.SUCCESS, int(WeError.SUCCESS)

    # `if fn-close  *> Close ignore & close logger` [:L425-L430].
    if function == int(FileFunction.CLOSE):
        # `move zero to File-Function Access-Type` [:L426-L427] - the handler
        # ZEROES THE FUNCTION CODE IT WAS DISPATCHED ON, and `Access-Type` with
        # it, so a caller inspecting the block afterwards finds neither.
        file_access.file_function = 0
        file_access.access_type = 0
        # `perform Ca-Process-Logs` [:L428] - UNGATED, unlike every bridge site.
        _process_logs(dal_common, file_access, "ba015/close-ignored")
        # NOTE: no `move zero to FS-Reply WE-Error` on this arm, unlike the open
        # arm above. Whatever the caller arrived with survives.
        return FsReply(file_access.fs_reply), file_access.we_error

    # `if fn-read-next` [:L432-L458] - the three-call triple.
    if function == int(FileFunction.READ_NEXT):
        return _read_triple(
            system, final, file_access, dal_common, transport=transport, states=states
        )

    # `if fn-Write` [:L459-L483] - the three-call triple, then the fall-through.
    if function == int(FileFunction.WRITE):
        outcome = _write_triple(
            system, final, file_access, dal_common, transport=transport, states=states
        )
        if outcome is not None:
            # The `else / go to ba-RDBMS-Exit` arm [:L481-L482]: the write
            # succeeded and the section is left.
            return outcome
        # *** THE FALL-THROUGH *** [:L479-L480, :L483]. `set fn-Re-write to true`
        # and `move zero to fs-reply we-error  *> clear if used in write` have
        # already run inside `_write_triple`; control now reaches `if fn-Re-write`
        # [:L485] with that flag set. This is anomalies A1 and A2 together, and it
        # is the reason a failed write reports success.
        return _rewrite_triple(
            system, final, file_access, dal_common, transport=transport, states=states
        )

    # `if fn-Re-write` [:L485-L504] - reachable both from a caller asking for it
    # and from the fall-through above. ANOMALY A16's RDB half: the handler's flat
    # path merges codes 5 and 7 into one paragraph by `evaluate` fall-through
    # [:L202-L204]; the RDB path reaches the same place by the missing `end-if`.
    if function == int(FileFunction.RE_WRITE):
        return _rewrite_triple(
            system, final, file_access, dal_common, transport=transport, states=states
        )

    # `*> In case of bad call action that was missed.` [:L506], then
    # `move 999 to WE-Error.` [:L508] and `move 99 to FS-Reply.` [:L509].
    # ANOMALY A19: the bridge's own `ba100-Bad-Function` says 990
    # [common/irsfinalMT.cbl:L580], and the two are never reconciled. This is the
    # SECOND bad-function site in the handler; the flat path has its own at
    # [:L327-L332] with the same pair.
    file_access.we_error = HANDLER_BAD_FUNCTION
    file_access.fs_reply = int(FS_REPLY_GENERAL)
    return FS_REPLY_GENERAL, HANDLER_BAD_FUNCTION


#  THE PUBLISHED VERBS - THE HANDLER'S OWN VOCABULARY AND THE SIX FROZEN ALIASES


def open_(
    system: SystemRecord,
    final: IrsFinalRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None = None,
    states: CursorStateTable | None = None,
) -> tuple[FsReply, int]:
    """`acasirsub5-Open` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L287-L291].

    ::

         acasirsub5-Open.
             set      fn-open to true.
             set      fn-i-o  to true.
             perform  acasirsub5.
             perform  irsub5-Check-4-Errors.

    A NO-OP THAT ALWAYS SUCCEEDS. `ba015-Test-Ends` tests `if fn-open` first and
    answers `move zero to FS-Reply WE-Error / go to ba-RDBMS-Exit`
    [common/acasirsub5.cbl:L421-L424] without examining the access type, without
    calling the bridge and without touching the database. The maintainer says why
    in his own words [common/acasirsub5.cbl:L161-L168]: IRS "only does a read or
    write and not a direct open or close", so the open is absorbed here and
    re-synthesised inside the read and write triples instead.

    `perform irsub5-Check-4-Errors` IS DELIBERATELY NOT REPRODUCED HERE. That
    paragraph belongs to the facade, not to the handler
    [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L348-L353], and its behaviour is
    drastic - `display IR915`, `perform acasirsub5-Close`, then
    `Open-Error-Continued` ending in `goback.` [:L355-L364], a return from the
    PROGRAM. Section 0.4.1.5 assigns that behaviour to `dal/facade.py`, which is
    the only module permitted to know all twenty handlers, so publishing it here
    would put a program-level abort inside a per-table module. `dispatch` performs
    no recovery either, exactly as `ba020-Call-DAL`'s own comment says:
    `*>   Any errors leave it to caller to recover from`
    [common/acasirsub5.cbl:L519]. Since this arm cannot fail, the omission is
    unobservable in any case - `fs-reply` is zero on every path out of it.

    Args:
        system: `WS-System-Record` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L84].
        final: `Final-Record` [:L85].
        file_access: `File-Access` [:L86].
        file_defs: `File-Defs` [:L87].
        dal_common: `ACAS-DAL-Common-data` [:L88].
        transport: The transport policy, forwarded to :func:`dispatch`.
        states: The cursor set, forwarded to :func:`dispatch`.

    Returns:
        Always `(0, 0)` unless the record-size gate refuses first, which returns
        `(99, 901)` [common/acasirsub5.cbl:L376-L377].
    """
    # `set fn-open to true` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L288] and
    # `set fn-i-o to true` [:L289]. NOTE that this verb sets I-O where
    # `acasirsub5-Open-Input` sets INPUT, and that `ba015-Test-Ends` reads neither.
    file_access.file_function = int(FileFunction.OPEN)
    file_access.access_type = int(AccessType.I_O)
    # `perform acasirsub5` [:L290].
    return dispatch(
        system,
        final,
        file_access,
        file_defs,
        dal_common,
        transport=transport,
        states=states,
    )


def open_input(
    system: SystemRecord,
    final: IrsFinalRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None = None,
    states: CursorStateTable | None = None,
) -> tuple[FsReply, int]:
    """`acasirsub5-Open-Input`
    [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L293-L297].

    ::

         acasirsub5-Open-Input.
             set      fn-open  to true.
             set      fn-input to true.
             perform  acasirsub5.
             perform  irsub5-Check-4-Errors.

    The second and last of the two open forms the frozen IRS facade publishes for
    this handler, and the only difference from :func:`open_` is the access type -
    which `ba015-Test-Ends` never reads [common/acasirsub5.cbl:L421-L424]. Both
    are therefore the same no-op, and both leave the access type behind in the
    block for a caller to see. The error check is the facade's, as for
    :func:`open_`.

    Args:
        system: `WS-System-Record`.
        final: `Final-Record`.
        file_access: `File-Access`.
        file_defs: `File-Defs`.
        dal_common: `ACAS-DAL-Common-data`.
        transport: The transport policy, forwarded to :func:`dispatch`.
        states: The cursor set, forwarded to :func:`dispatch`.

    Returns:
        Always `(0, 0)`, or the record-size gate's `(99, 901)`.
    """
    # `set fn-open to true` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L294] and
    # `set fn-input to true` [:L295].
    file_access.file_function = int(FileFunction.OPEN)
    file_access.access_type = int(AccessType.INPUT)
    # `perform acasirsub5` [:L296].
    return dispatch(
        system,
        final,
        file_access,
        file_defs,
        dal_common,
        transport=transport,
        states=states,
    )


def open_output(
    system: SystemRecord,
    final: IrsFinalRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None = None,
    states: CursorStateTable | None = None,
) -> tuple[FsReply, int]:
    """The `-Open-Output` verb of the twelve-verb facade vocabulary.

    NO FROZEN PARAGRAPH PUBLISHES THIS FOR THIS HANDLER. The IRS convention
    publishes exactly six verbs for `acasirsub5` - Open, Open-Input, Close,
    Read-Next, Write and ReWrite [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L287,
    :L293, :L299, :L304, :L309, :L314], and :data:`PUBLISHED_FACADE_VERBS` is that
    list. This function exists so the vocabulary section 0.3.1 describes is
    complete and so a caller written against the entity-named convention resolves,
    and it is recorded as an addition of vocabulary rather than of behaviour.

    *** IT DOES NOT DELETE ANYTHING. *** In `acas008`, `Open-Output` means DELETE
    EVERY ROW [common/acas008.cbl:L313-L319, :L571-L574], and that is how the IRS
    transfer file is cleared at end of job [irs/irs030.cbl:L1720-L1724]. THERE IS
    NO SUCH COERCION IN `acasirsub5`: the handler has no Open-Output block at all,
    and its bridge has no `DELETE FROM`, no `ba080-Process-Delete` and no
    `ba085` of any kind. Rule R-3 forbids inventing one, so this verb is the same
    ignored no-op every other open form is, and this module publishes no `delete`
    and no `delete_all`.

    Args:
        system: `WS-System-Record`.
        final: `Final-Record`.
        file_access: `File-Access`.
        file_defs: `File-Defs`.
        dal_common: `ACAS-DAL-Common-data`.
        transport: The transport policy, forwarded to :func:`dispatch`.
        states: The cursor set, forwarded to :func:`dispatch`.

    Returns:
        Always `(0, 0)`, or the record-size gate's `(99, 901)`. Never a row count,
        because nothing is written and nothing is removed.
    """
    # `set fn-open to true` with `set fn-output to true`, the form the twelve-verb
    # vocabulary would use. `ba015-Test-Ends` ignores the access type
    # [common/acasirsub5.cbl:L421-L424], so this reaches the same no-op.
    file_access.file_function = int(FileFunction.OPEN)
    file_access.access_type = int(AccessType.OUTPUT)
    return dispatch(
        system,
        final,
        file_access,
        file_defs,
        dal_common,
        transport=transport,
        states=states,
    )


def open_extend(
    system: SystemRecord,
    final: IrsFinalRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None = None,
    states: CursorStateTable | None = None,
) -> tuple[FsReply, int]:
    """The `-Open-Extend` verb of the twelve-verb facade vocabulary.

    As with :func:`open_output`, NO FROZEN PARAGRAPH PUBLISHES THIS FOR THIS
    HANDLER; see :data:`PUBLISHED_FACADE_VERBS` for the six that are published.
    Vocabulary completeness only, and the same ignored no-op, because
    `ba015-Test-Ends` answers every `fn-open` identically without reading the
    access type [common/acasirsub5.cbl:L421-L424].

    Args:
        system: `WS-System-Record`.
        final: `Final-Record`.
        file_access: `File-Access`.
        file_defs: `File-Defs`.
        dal_common: `ACAS-DAL-Common-data`.
        transport: The transport policy, forwarded to :func:`dispatch`.
        states: The cursor set, forwarded to :func:`dispatch`.

    Returns:
        Always `(0, 0)`, or the record-size gate's `(99, 901)`.
    """
    file_access.file_function = int(FileFunction.OPEN)
    file_access.access_type = int(AccessType.EXTEND)
    return dispatch(
        system,
        final,
        file_access,
        file_defs,
        dal_common,
        transport=transport,
        states=states,
    )


def close(
    system: SystemRecord,
    final: IrsFinalRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None = None,
    states: CursorStateTable | None = None,
) -> tuple[FsReply, int]:
    """`acasirsub5-Close` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L299-L302].

    ::

         acasirsub5-Close.
             move     zero to Access-Type.
             set      fn-Close to true.
             perform  acasirsub5.

    NO ERROR CHECK ON THIS VERB. Only the two open forms perform
    `irsub5-Check-4-Errors` [:L291, :L297]; close, read, write and rewrite do not,
    which is itself worth stating because it means a failing close is silent at
    the facade as well as at the handler.

    ALSO A NO-OP, and one that erases evidence on its way out. `if fn-close`
    answers `move zero to File-Function Access-Type / perform Ca-Process-Logs /
    go to ba-RDBMS-Exit` [common/acasirsub5.cbl:L425-L430], so the handler ZEROES
    THE FUNCTION CODE IT WAS DISPATCHED ON. The frozen comment on the arm is
    `*> Close ignore & close logger`, and the log call is UNGATED where every one
    of the bridge's seven is wrapped in `if Testing-1`.

    NOTE what this arm does NOT do: there is no `move zero to FS-Reply WE-Error`
    on it, unlike the open arm four lines above. So a close inherits and returns
    whatever status the caller arrived with. That asymmetry is in the source and
    is reproduced.

    THE REAL CLOSE HAPPENS ELSEWHERE. `ba030-Process-Close`
    [common/irsfinalMT.cbl:L302-L315] is reached only from inside the read, write
    and rewrite triples, which synthesise it themselves - and two of those four
    paths skip it (anomaly A10).

    Args:
        system: `WS-System-Record`.
        final: `Final-Record`.
        file_access: `File-Access`; `File-Function` and `Access-Type` are both
            zeroed in it before this returns.
        file_defs: `File-Defs`.
        dal_common: `ACAS-DAL-Common-data`.
        transport: The transport policy, forwarded to :func:`dispatch`.
        states: The cursor set, forwarded to :func:`dispatch`.

    Returns:
        Whatever `(FS-Reply, We-Error)` the caller arrived with - NOT `(0, 0)`.
    """
    # `move zero to Access-Type` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L300].
    # The facade clears it here and the handler clears it again [:L427]; the
    # duplication is in the source.
    file_access.access_type = 0
    # `set fn-Close to true` [:L301].
    file_access.file_function = int(FileFunction.CLOSE)
    # `perform acasirsub5` [:L302].
    return dispatch(
        system,
        final,
        file_access,
        file_defs,
        dal_common,
        transport=transport,
        states=states,
    )


#: `acasirsub5-Open` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L287]. THE SAME
#: IMPLEMENTATION UNDER THE FROZEN PARAGRAPH NAME, per section 0.3.3's
#: "Facade with dual aliasing": one implementation, two published name sets, so a
#: reader following either COBOL convention finds a correspondingly named Python
#: function without the logic existing twice.
acasirsub5_open = open_

#: `acasirsub5-Open-Input` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L293].
acasirsub5_open_input = open_input

#: `acasirsub5-Close` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L299].
acasirsub5_close = close


def acasirsub5_read_next(
    system: SystemRecord,
    final: IrsFinalRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None = None,
    states: CursorStateTable | None = None,
) -> tuple[FsReply, int]:
    """`acasirsub5-Read-Next` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L304-L307].

    ::

         acasirsub5-Read-Next.
             move     zero to Access-Type.
             set      fn-Read-Next to true.
             perform  acasirsub5.

    THIS IS NOT :func:`read_next`. That function is the BRIDGE's
    `ba040-Process-Read-Next` [common/irsfinalMT.cbl:L317-L466] and takes an
    already-open connection; this one is the FACADE VERB, takes the handler's
    five-parameter linkage, and reaches `ba040` only through the synthesised
    open-read-close triple inside `ba015-Test-Ends`
    [common/acasirsub5.cbl:L432-L458]. The names are close because the frozen
    names are close; the distinction is the handler/bridge boundary that section
    0.3.1 requires this module to preserve rather than flatten.

    ONE CALL HERE IS THREE BRIDGE CALLS, and on any failure of the open or of the
    read the close is skipped (anomaly A10). No error check is performed - the
    facade supplies one only for the two open verbs [:L291, :L297].

    ONE LOGICAL READ REASSEMBLES UP TO TWENTY-SIX ROWS into the two `occurs 26`
    arrays, indexed by the KEY VALUE THE DATABASE RETURNED rather than by the loop
    counter [common/irsfinalMT.cbl:L455-L456]. Fewer than twenty-six rows is
    normal and tolerated: `*> having initialised record as some rows may not be
    present` [:L320].

    Args:
        system: `WS-System-Record`.
        final: `Final-Record`, reassembled in place.
        file_access: `File-Access`.
        file_defs: `File-Defs`.
        dal_common: `ACAS-DAL-Common-data`.
        transport: The transport policy, forwarded to :func:`dispatch`.
        states: The cursor set, forwarded to :func:`dispatch`.

    Returns:
        The read's own `(FS-Reply, We-Error)` pair, restored across the close.
    """
    # `move zero to Access-Type` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L305] -
    # and then `ba015-Test-Ends` immediately sets it to `fn-Input`
    # [common/acasirsub5.cbl:L434], so the clearing is undone at once.
    file_access.access_type = 0
    # `set fn-Read-Next to true` [:L306].
    file_access.file_function = int(FileFunction.READ_NEXT)
    # `perform acasirsub5` [:L307].
    return dispatch(
        system,
        final,
        file_access,
        file_defs,
        dal_common,
        transport=transport,
        states=states,
    )


def acasirsub5_write(
    system: SystemRecord,
    final: IrsFinalRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None = None,
    states: CursorStateTable | None = None,
) -> tuple[FsReply, int]:
    """`acasirsub5-Write` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L309-L312].

    ::

         acasirsub5-Write.
             move     zero to Access-Type.
             set      fn-Write to true.
             perform  acasirsub5.

    THIS IS NOT :func:`write`; that is the BRIDGE's `ba070-Process-Write`
    [common/irsfinalMT.cbl:L468-L517], reached from here through the synthesised
    open-write-close triple [common/acasirsub5.cbl:L459-L483].

    *** A FAILURE OF THIS VERB IS INDISTINGUISHABLE FROM SUCCESS. *** Anomalies A1
    and A2: the triple's single `end-if.` [common/acasirsub5.cbl:L483] lets a
    failed write fall through into the rewrite after `move zero to fs-reply
    we-error` [:L480] has erased the failure, and the rewrite's own unguarded
    four-field reset [common/irsfinalMT.cbl:L571-L573] then returns `(0, 0)`
    whatever happened. `acasirsub3` carries the same pair, so two of the twenty
    data-access modules behave this way. Rule R-4 makes reproducing it mandatory,
    and no error check runs here either - the facade checks only its two open
    verbs [:L291, :L297]. A CALLER THAT NEEDS TO KNOW A WRITE LANDED MUST READ THE
    TABLE BACK; the status pair cannot tell it.

    ONE LOGICAL WRITE IS TWENTY-SIX `INSERT`s, keyed by the `occurs` subscript
    [common/irsfinalMT.cbl:L481], with NO blank-slot skip - the skip is commented
    out [:L477-L480] - so the table holds exactly twenty-six rows afterwards, blank
    entries persisted as spaces. And `ar3 pic x(5)` [copybooks/irswsfinal.cob:L68]
    is in none of them, because it has no column.

    Args:
        system: `WS-System-Record`.
        final: `Final-Record`, the source of the twenty-six rows.
        file_access: `File-Access`.
        file_defs: `File-Defs`.
        dal_common: `ACAS-DAL-Common-data`.
        transport: The transport policy, forwarded to :func:`dispatch`.
        states: The cursor set, forwarded to :func:`dispatch`.

    Returns:
        `(0, 0)` on success AND on failure, per anomalies A1 and A2. The only
        failures a caller can see are the synthesised open's
        [common/acasirsub5.cbl:L463-L465] and the record-size gate's `(99, 901)`.
    """
    # `move zero to Access-Type` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L310] -
    # undone at once by `set fn-I-O to true` [common/acasirsub5.cbl:L461].
    file_access.access_type = 0
    # `set fn-Write to true` [:L311].
    file_access.file_function = int(FileFunction.WRITE)
    # `perform acasirsub5` [:L312].
    return dispatch(
        system,
        final,
        file_access,
        file_defs,
        dal_common,
        transport=transport,
        states=states,
    )


def acasirsub5_rewrite(
    system: SystemRecord,
    final: IrsFinalRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None = None,
    states: CursorStateTable | None = None,
) -> tuple[FsReply, int]:
    """`acasirsub5-ReWrite` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L314-L317].

    ::

         acasirsub5-ReWrite.
             move     zero to Access-Type.
             set      fn-re-write to true.
             perform  acasirsub5.

    NOTE THE FROZEN SPELLING: the paragraph is `acasirsub5-ReWrite` with an
    internal capital, where every other verb in the group is hyphen-separated
    lower case. :data:`PUBLISHED_FACADE_VERBS` carries it as written.

    THIS IS NOT :func:`rewrite`; that is the BRIDGE's `ba090-Process-Rewrite`
    [common/irsfinalMT.cbl:L519-L574], reached from here through the synthesised
    open-rewrite-close triple [common/acasirsub5.cbl:L485-L504].

    IT CANNOT REPORT A FAILURE EITHER, and for a different reason than the write:
    `ba090` sets `move 99 to fs-reply` and `move 994 to WE-Error` on a bad row
    [common/irsfinalMT.cbl:L562-L563] and then clears `FS-Reply`, `WE-Error`,
    `SQL-Err` and `SQL-Msg` UNCONDITIONALLY eight lines later [:L571-L573]. The
    `994` is permanently unobservable - see
    :data:`WE_ERROR_UNOBSERVABLE_REWRITE`.

    ANOMALY A16: on the flat-file path this verb and the write share one paragraph
    outright, because `when 5` falls through to `when 7` in the handler's
    `evaluate` [common/acasirsub5.cbl:L202-L204] under the comment
    `*> write/rewrite can do the same ... as file is opened as output.` On the RDB
    path they reach the same place by the missing `end-if` instead.

    Args:
        system: `WS-System-Record`.
        final: `Final-Record`, the source of the twenty-six `UPDATE`s.
        file_access: `File-Access`.
        file_defs: `File-Defs`.
        dal_common: `ACAS-DAL-Common-data`.
        transport: The transport policy, forwarded to :func:`dispatch`.
        states: The cursor set, forwarded to :func:`dispatch`.

    Returns:
        `(0, 0)` on every path that reaches the rewrite verb, per anomaly A1;
        otherwise the synthesised open's failure
        [common/acasirsub5.cbl:L489-L491] or the gate's `(99, 901)`.
    """
    # `move zero to Access-Type` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L315] -
    # undone at once by `set fn-I-O to true` [common/acasirsub5.cbl:L487].
    file_access.access_type = 0
    # `set fn-re-write to true` [:L316].
    file_access.file_function = int(FileFunction.RE_WRITE)
    # `perform acasirsub5` [:L317].
    return dispatch(
        system,
        final,
        file_access,
        file_defs,
        dal_common,
        transport=transport,
        states=states,
    )


# --- traceability -----------------------------------------------------------
#
# Rule R-5: "Every program must map to a module, every paragraph to a function,
# and every field to a data-dictionary entry, and the mapping must be recorded as
# a document rather than left implicit in the code." All three mappings are below,
# with the `GO TO` class annotated at every live transfer site per Agent Action
# Plan section 0.4.2, and every deliberate omission recorded AS an omission -
# section 0.4.3's reason, verbatim: "so that a reader comparing the two files does
# not conclude something was lost."
#
# PROGRAM  ->  MODULE
#   common/acasirsub5.cbl  (handler, 534 lines, `Program-Id. acasirsub5.` L12)
#   common/irsfinalMT.cbl  (bridge,  727 lines, `Program-Id. irsfinalMT.` L13)
#       ->  acas_posting/dal/acasirsub5_irs_final.py
#   BOTH programs map to ONE module, per section 0.3.1's boundary rule: "One data
#   access module per handler, not per table ... preserves the dispatch semantics
#   rather than flattening them." The handler is the bridge's only caller
#   [common/acasirsub5.cbl:L513], so folding the pair into one module keeps the
#   Python module set in exact correspondence with the COBOL programs while the
#   two layers stay separately named inside it: every `_ba0NN_*`, `read_next`,
#   `write` and `rewrite` is a BRIDGE paragraph, and `dispatch`, the three
#   `_*_triple` helpers and `_record_size_gate` are HANDLER paragraphs.
#   Boundary: THE WHOLE OF BOTH PROGRAMS' RDB PATHS. The handler's flat-file path
#   is out of scope - see OMISSIONS.
#
# PARAGRAPH  ->  FUNCTION   (handler, common/acasirsub5.cbl)
#   aa010-main.                [:L154]      ->  dispatch          (RDB gate only)
#   aa040-Process-Read-Next.   [:L248]      ->  OMITTED (flat) - A8, A11, A12, A13
#   aa070-Process-Write.       [:L301]      ->  OMITTED (flat) - A14
#   aa100-Bad-Function.        [:L327]      ->  OMITTED (flat); its RDB twin at
#                                                [:L506-L510] is `dispatch`'s tail
#   aa999-main-exit.           [:L334]      ->  OMITTED (flat)
#   aa-main-exit.              [:L339]      ->  OMITTED; carries only the
#                                                commented-out dual-write hook, A27
#   aa-Exit.                   [:L347]      ->  `dispatch`'s `return` on the
#                                                function-1 and function-2 arms
#   ba-Process-RDBMS section.  [:L350]      ->  everything below `dispatch`'s gate
#   ba010-Test-WS-Rec-Size.    [:L358]      ->  the `ws_log_file_no = 24` statement
#                                                in `dispatch`; the paragraph holds
#                                                nothing else [:L364]
#   ba012-Test-WS-Rec-Size-2.  [:L366]      ->  _record_size_gate
#   ba015-Test-Ends.           [:L408]      ->  dispatch's six arms, plus
#                                                _read_triple, _write_triple and
#                                                _rewrite_triple
#   ba020-Call-DAL.            [:L512]      ->  _ba020_call_dal
#   ba-rdbms-exit.             [:L521]      ->  every `return` in the above; its
#                                                body is `exit section.` [:L522]
#   Ca-Process-Logs.           [:L525]      ->  _process_logs  (as a log record,
#                                                never as the frozen `CALL`; R-1)
#   ca-Exit.  exit.            [:L531]      ->  `_process_logs` returning
#   Procedure Division Using System-Record / Final-Record / File-Access /
#   File-Defs / ACAS-DAL-Common-data       [:L143-L149]  ->  `dispatch`'s
#                                                parameter list, ORDER PRESERVED
#
# PARAGRAPH  ->  FUNCTION   (bridge, common/irsfinalMT.cbl)
#   ba-ACAS-DAL-Process section. [:L211]    ->  _ba020_call_dal
#   ba010-Initialise.            [:L222]    ->  _ba010_initialise
#   evaluate File-Function       [:L239-L252] -> _ba020_call_dal's five arms
#   ba020-Process-Open.          [:L254]    ->  _ba020_process_open
#   ba030-Process-Close.         [:L302]    ->  _ba030_process_close
#   ba040-Process-Read-Next.     [:L317]    ->  read_next, with _issue_select,
#                                                _initialize_final_record,
#                                                _store_array_entry, _read_key and
#                                                _ba040_no_data
#   ba070-Process-Write.         [:L468]    ->  write
#   ba090-Process-Rewrite.       [:L519]    ->  rewrite
#   ba100-Bad-Function.          [:L576]    ->  _ba100_bad_function
#   ba998-Free.                  [:L588]    ->  _ba998_free
#   ba999-end.                   [:L600]    ->  the `_process_logs_if_testing`
#                                                call that precedes each `return`
#                                                on the paths that reach it
#   ba999-exit.  exit program.   [:L606]    ->  those `return`s
#   bb200-Insert Section.        [:L609]    ->  insert_statement + _issue_command
#   bb200-Exit.                  [:L659]    ->  _issue_command returning
#   bb300-Update Section.        [:L662]    ->  update_statement + _issue_command
#   bb300-Exit.                  [:L716]    ->  _issue_command returning
#   Ca-Process-Logs.             [:L719]    ->  _process_logs_if_testing
#   ca-Exit.  exit.              [:L725]    ->  that function returning
#   PROCEDURE DIVISION using File-Access / ACAS-DAL-Common-data / Final-Record
#                                [:L207-L209] ->  _ba020_call_dal's first, third
#                                and fourth parameters; `system` and `states` are
#                                additions of plumbing, not of linkage, and the
#                                docstring says so
#   COPY "mysql-procedures.cpy". [:L585]    ->  _issue_command, _issue_select,
#                                                _store_result, _fetch_one_row and
#                                                _apply_driver_status, each citing
#                                                the copybook paragraph it models
#
# FACADE PARAGRAPH  ->  FUNCTION   (copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob)
#   acasirsub5.              [:L82-L89]  ->  dispatch (the `CALL` itself)
#   acasirsub5-Open.         [:L287]     ->  open_        == acasirsub5_open
#   acasirsub5-Open-Input.   [:L293]     ->  open_input   == acasirsub5_open_input
#   acasirsub5-Close.        [:L299]     ->  close        == acasirsub5_close
#   acasirsub5-Read-Next.    [:L304]     ->  acasirsub5_read_next
#   acasirsub5-Write.        [:L309]     ->  acasirsub5_write
#   acasirsub5-ReWrite.      [:L314]     ->  acasirsub5_rewrite
#   irsub5-Check-4-Errors.   [:L348]     ->  NOT REPRODUCED HERE - section 0.4.1.5
#                                            assigns the per-handler error check
#                                            and its `goback.` [:L364] to
#                                            `dal/facade.py`. See `open_`.
#   Section 0.3.3's dual aliasing gives the three open/close verbs ONE
#   implementation under TWO names. The three data verbs cannot be aliases: the
#   frozen facade verb is a HANDLER call taking the five-parameter linkage, while
#   `read_next`, `write` and `rewrite` are the BRIDGE paragraphs taking an open
#   connection. Each `acasirsub5_*` docstring says so explicitly, because the
#   names are close enough to mislead.
#   `open_output` and `open_extend` have NO frozen paragraph for this handler -
#   :data:`PUBLISHED_FACADE_VERBS` is the frozen six - and exist only so the
#   twelve-verb vocabulary of section 0.3.1 resolves. NO `delete` and NO
#   `delete_all` is published, because this bridge has neither.
#
# `GO TO`  ->  THE FOUR-CLASS TAXONOMY, at every LIVE site on the RDB path
#   Class 1 (loop-back -> `continue`):     ZERO SITES. Neither program contains a
#       backward `GO TO`; both loops are `perform varying ... until`, so iteration
#       never needs one.
#   Class 2 (forward terminator -> `break` + post-loop block):
#       * `exit perform` [common/irsfinalMT.cbl:L423] - the read's exhaustion arm
#         -> `break` in `read_next`, with [:L464-L465]'s post-loop work following.
#       * `exit perform` [:L453] - the read's in-loop failure arm -> the same.
#         Not a `GO TO` keyword, but the same shape, so the same class.
#   Class 3 (section/paragraph exit -> `return`):
#       * `go to AA-Main-Exit`   [common/acasirsub5.cbl:L175]  -> `dispatch` returns
#       * `go to ba-rdbms-exit`  [:L393]  -> `_record_size_gate` returns (99, 901)
#       * `go to ba-RDBMS-Exit`  [:L423]  -> `dispatch`'s function-1 arm
#       * `go to ba-RDBMS-Exit`  [:L429]  -> `dispatch`'s function-2 arm
#       * `go to ba-rdbms-Exit`  [:L439]  -> `_read_triple` open bail-out    (A10)
#       * `go to ba-RDBMS-Exit`  [:L448]  -> `_read_triple` read bail-out    (A10)
#       * `go to ba-RDBMS-Exit`  [:L457]  -> `_read_triple` normal exit
#       * `go to ba-rdbms-Exit`  [:L465]  -> `_write_triple` open bail-out   (A10)
#       * `go to ba-RDBMS-Exit`  [:L482]  -> `_write_triple` success `else`
#       * `go to ba-rdbms-Exit`  [:L491]  -> `_rewrite_triple` open bail-out (A10)
#       * `go to ba-RDBMS-Exit`  [:L503]  -> `_rewrite_triple` normal exit
#       * `go to ba-RDBMS-Exit.` [:L510]  -> `dispatch`'s bad-function tail   (A19)
#       * `go to ba999-exit`     [common/irsfinalMT.cbl:L466, :L517, :L574]
#         -> the `return` ending `read_next`, `write` and `rewrite`. All three SKIP
#            `ba999-end`'s logging hook [:L600-L604] - anomaly A38.
#       Every one targets a label whose body is the trailing exit: `ba-rdbms-exit.`
#       is `exit section.` [common/acasirsub5.cbl:L521-L522] and `ba999-exit.` is
#       `exit program.` [common/irsfinalMT.cbl:L606-L607].
#   Class 4 (sibling re-dispatch -> named call + explicit control statement):
#       * `go to aa040-Process-Read-Next` / `aa070-Process-Write` /
#         `aa100-Bad-Function` [common/acasirsub5.cbl:L201, :L204, :L206, :L210]
#         -> OMITTED with the flat path, and `when 5` falling through to `when 7`
#            [:L202-L204] is anomaly A16.
#       * `go to aa-Exit` [:L195, :L199] -> the flat twins of `dispatch`'s
#         function-1 and function-2 arms; A15's flat half. OMITTED.
#       * `go to ba020-Process-Open` / `ba030-Process-Close` /
#         `ba040-Process-Read-Next` / `ba070-Process-Write` /
#         `ba090-Process-Rewrite` / `ba100-Bad-Function`
#         [common/irsfinalMT.cbl:L241, :L243, :L245, :L247, :L249, :L251]
#         -> `_ba020_call_dal`'s five arms plus `_ba100_bad_function`, each a named
#            call followed by `return`.
#       * `go to ba998-Free` [:L386] -> `_ba998_free(...)` then `return`, inside
#         `_ba040_no_data`. The target does work (frees the result) and then falls
#         through to `ba999-end` and `ba999-exit`, so the explicit statement after
#         the call is a `return`.
#       * `go to ba999-end` [:L290, :L300, :L315, :L582] -> the
#         `_process_logs_if_testing(...)` call followed by `return` in
#         `_ba020_process_open`, `_ba030_process_close` and `_ba100_bad_function`.
#         Same shape as `ba998-Free`: work, then fall-through to the exit.
#   OMITTED-PATH SITES, listed so the census is complete rather than selective:
#       [common/acasirsub5.cbl:L262, :L274, :L284, :L291, :L299, :L316, :L325] -
#       all `go to aa999-main-exit` inside the flat read and write paragraphs.
#   `PERFORM ... THRU`: the handler has NONE. The bridge has the driver pairs
#   `PERFORM MYSQL-1000-OPEN THRU MYSQL-1090-EXIT` [common/irsfinalMT.cbl:L288],
#   `MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT` [:L657, :L714], `MYSQL-1220-STORE
#   RESULT THRU MYSQL-1239-EXIT` and `MYSQL-1980-CLOSE THRU MYSQL-1999-EXIT`
#   [:L313], every one of them spanning `copybooks/mysql-procedures.cpy` rather
#   than this program. Each is hand-verified in the function that models it -
#   `_ba020_process_open`, `_issue_command`, `_issue_select`,
#   `_ba030_process_close` - and none is pattern-matched.
#
# THE WRITE -> REWRITE FALL-THROUGH: AN INDIVIDUAL EQUIVALENCE PROOF
#   Section 0.4.2 requires Class 4 sites to be proved one at a time, and this site
#   needs the proof most because IT IS NOT A TRANSFER AT ALL. There is no `GO TO`
#   and no `PERFORM`; control reaches `if fn-Re-write` [common/acasirsub5.cbl:L485]
#   because the preceding sentence ENDED. The proof:
#     1. `if fn-Write` [:L459] opens a conditional with no `end-if` of its own.
#     2. The nested `if (fs-Reply not = zero or WE-Error not = zero)` [:L475-L476]
#        has a THEN branch [:L477-L480], an `else` [:L481] and a single terminator
#        `end-if.` [:L483].
#     3. A period ends the whole SENTENCE, so that one terminator closes the inner
#        `if` and, with it, the outer `if fn-Write`. There is no second `end-if`
#        anywhere between [:L459] and [:L485] - verified by reading every line of
#        the span.
#     4. Therefore the outer conditional's THEN branch has exactly one exit for the
#        failure case: fall-through past the end of the sentence.
#     5. The next sentence is `if fn-Re-write` [:L485], and [:L479] has just done
#        `set fn-Re-write to true`, so it is entered.
#     6. The success case cannot reach it, because its `else` [:L481-L482] performs
#        `go to ba-RDBMS-Exit` first.
#   The Python equivalent is exact: `_write_triple` returns `None` for case (4) and
#   the pair for cases (2)-`else` and the open bail-out, and `dispatch` calls
#   `_rewrite_triple` on `None` and returns otherwise. A boolean would have done,
#   but `None` versus a pair makes it impossible to fall through accidentally with
#   a status in hand - which is the one mistake that would hide the defect instead
#   of reproducing it. Anomalies A1 and A2.
#
# FIELD  ->  DICTIONARY ENTRY   (section 0.8.1's "data dictionary first")
#   Every column name, width and type used by this module is READ from
#   `data_dictionary/acas_posting_dictionary.json` through
#   `acas_posting.dictionary.loader`, never written as a literal:
#   `loader.table_for(TABLE).primary_key` supplies `PRIMARY_KEY`,
#   `loader.entries_for_table(TABLE)` sorted by `column.ordinal` supplies
#   `COLUMNS`, `loader.table_for(TABLE).column_count` is asserted against
#   `len(COLUMNS)` at import time, and the widths come off the descriptors
#   `records.irs_final` publishes. The three mappings are unusual in three
#   different ways and each is recorded:
#     1. `IRS-FINAL-ACC-REC-KEY` tinyint(2) unsigned [mysql/ACASDB.sql:L215] <-
#        `HV-IRS-FINAL-ACC-REC-KEY PIC 9(03) COMP` [common/irsfinalMT.cbl:L172] <-
#        NO COPYBOOK FIELD AT ALL. Its only source is the `occurs` subscript:
#        `move A to HV-IRS-FINAL-ACC-REC-KEY` on write [:L481] and
#        `AR1 (HV-IRS-FINAL-ACC-REC-KEY)` on read [:L455], whose own comment is
#        `*> KEY = table position`. The dictionary entry therefore carries a
#        derivation note rather than a copybook locator, which is exactly the case
#        section 0.4.1.6 asks the generator to flag: "flags any field present in
#        one source and absent from another".
#     2. `IRS-AR1` char(24) <- `HV-IRS-AR1 PIC X(24)` [:L173] <- TWENTY-SIX
#        copybook fields, `ar1-1` through `ar1-26`
#        [copybooks/irswsfinal.cob:L9-L34], plus the `occurs 26` redefine
#        `ar1` [:L35-L36]. One column, twenty-six rows. Same for `IRS-AR2`
#        char(1) <- `HV-IRS-AR2 PIC X(1)` [:L174] <- `ar2-1`..`ar2-26`
#        [copybooks/irswsfinal.cob:L39-L64] and the redefine [:L65-L66]. Both
#        names stay live in the record layer because the callers use the
#        enumerated names and the bridge uses the array.
#     3. `ar3 pic x(5)` [copybooks/irswsfinal.cob:L68] -> NOTHING. No column, no
#        host variable, no load, no unload: a case-insensitive search for `ar3`
#        across `common/irsfinalMT.cbl`, `common/acasirsub5.cbl` and
#        `mysql/ACASDB.sql` returns zero hits. Anomaly A3. The field exists in the
#        record dataclass and is blanked by `_initialize_final_record`, and it
#        appears in NO statement this module builds.
#   Widths reconcile: 26*24 + 26*1 + 5 = 655, matching both
#   `*> rec 655 bytes` [copybooks/irswsfinal.cob:L6] and
#   `01 Record-5 pic x(655).` [common/acasirsub5.cbl:L104]. Both numbers are
#   carried as :data:`WS_RECORD_BYTES` (derived) and :data:`FD_RECORD_BYTES`
#   (literal) and cross-checked at import, so the record-size gate compares two
#   independent sources as its COBOL original does.
#
# ANOMALY  ->  REPRODUCTION SITE   (rule R-4; register in the module docstring)
#   A1  `rewrite` (the unconditional reset) + `_write_triple` (the erasure)
#   A2  `_write_triple` (returns `None`) + `dispatch` (falls into `_rewrite_triple`)
#   A3  `_initialize_final_record`, and the absence of `ar3` from every builder
#   A4  `_store_array_entry`, called from `read_next` with the RETURNED key
#   A5  `read_next`'s `== 0 or > ARRAY_LENGTH` guard
#   A6  `write`'s squash into `_WS_SAVED_FS_REPLY`
#   A7  `write`'s loop, which has no blank-slot test
#   A8  OMITTED with the flat path; named in the docstring's omission list
#   A9  cited verbatim in the docstring; the statements are on the flat path
#   A10 the three bail-outs in `_read_triple` and `_write_triple`, and the fourth
#       in `_rewrite_triple`; the leaked handle is `_CONNECTION`
#   A11 A12 A13 A14  OMITTED with the flat path; named in the omission list
#   A15 `dispatch`'s function-1 and function-2 arms - no logging on either
#   A16 `dispatch`, where WRITE and RE_WRITE reach one `_rewrite_triple`
#   A17 docstring inventory only; the ~35 lines are commented out
#   A18 OMITTED with the flat path; NO `sys.exit`, `exit()` or `os._exit` anywhere
#   A19 `dispatch`'s tail (999) versus `_ba100_bad_function` (990); both named as
#       :data:`HANDLER_BAD_FUNCTION` and :data:`BRIDGE_BAD_FUNCTION`
#   A20 `_errno_is_set`, and the width note in `rewrite`
#   A21 `rewrite`'s `Testing-2` comment
#   A22 `write`, which initialises no host-variable group yet binds all three
#       columns every iteration
#   A23 `read_next`'s `_dead_kor_offset` / `_dead_kor_length` pair
#   A24 `select_where`, which hard-codes `" > "`
#   A25 `select_where`'s quoted `"000"`, with the Q-16 marker in `_insert_key_text`
#   A26 `_process_logs`'s docstring, and the four ungated calls in `_read_triple`
#   A27 OMITTED; named in the omission list
#   A28 the `IRS-` prefix, resolved from the dictionary rather than assumed
#   A29 docstring inventory only - comment-level cosmetics
#   A30 `read_next` initialises with filler semantics; `write` does not initialise
#   A31 the commented-out clear noted inside `write`'s loop
#   A32 `read_next`'s post-loop reset, with the Q-17 marker beside it
#   A33 the live clear in `read_next`'s loop and the dead one in `write`'s
#   A34 docstring note on the "32 rows" comment
#   A35 `_ba040_no_data` and `read_next`'s exhaustion arm, both via
#       `end_of_file_status()`
#   A36 `_insert_key_text` versus `_ws_key`, and `insert_statement` including the
#       primary key in its `SET` list
#   A37 `read_next`'s cursor-active branch
#   A38 the `return`s in `read_next`, `write` and `rewrite` that skip
#       `ba999-end`'s log
#   A39 the no-op note in `write` where the frozen lock-retry ladder is reset
#   A40 `_issue_command`, which reads the row count after a failure too
#   A41 `read_next`, which sets `ws_log_where` then blanks it before any log call
#   A42 `read_next`'s three-disjunct exhaustion test
#   A43 `read_next`'s in-loop count guard
#   A44 the module-level `_WS_SAVED_FS_REPLY`, never cleared within a run
#   A45 modelled as nothing, and recorded as nothing
#   A46 the comment on `_rewrite_triple`'s bridge call
#   A47 `_write_triple`'s SUCCESS return, which sets no `ws_file_key` - the
#       absence is the anomaly, so the site is the `return` at the end of the
#       success branch and the docstring paragraph above it
#
# OMISSIONS - deliberate, and each recorded rather than silent
#   1. THE ENTIRE FLAT-FILE PATH [common/acasirsub5.cbl:L180-L348], with
#      `fd Final-File.` / `01 Record-5 pic x(655).` [:L102-L104]. Rule R-1 makes
#      this module SQL-only. Carries away A8, A11, A12, A13, A14 and A18.
#   2. THE ~35 DEAD LINES of `aa020-Process-Open` / `aa030-Process-Close`
#      [:L212-L246] - A17 - and the commented-out dual-write hook in
#      `aa-main-exit` [:L344-L346] - A27. Representation only.
#   3. ALL PRESENTATION: every `display ... at <line><col> with foreground-color`,
#      the `accept Accept-Reply` pauses, `01 Error-Messages.` IR901/IR902/IR921/
#      IR922/IR923/IR924 [:L121-L129], the bridge's `screen section.`
#      [common/irsfinalMT.cbl:L189] and its `display Display-Message-1 with erase
#      eos` [:L369, :L551]. Section 0.3.4's three-way rule: diagnostics with no
#      database effect become log records, acknowledgement pauses are dropped, and
#      the CONTROL TRANSFER after an error display is preserved - which is why
#      `_record_size_gate` still returns (99, 901) and still skips the bridge.
#   4. `call "fhlogger"` [common/acasirsub5.cbl:L528-L529,
#      common/irsfinalMT.cbl:L722-L723]. `common/fhlogger.cbl` is out of scope
#      (section 0.2.2) and rule R-1 forbids the call, so all fourteen
#      `perform Ca-Process-Logs` sites emit Python log records instead. Gated and
#      ungated forms are kept apart, because the source keeps them apart.
#   5. `irsub5-Check-4-Errors` and `Open-Error-Continued`
#      [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L348-L364]. Facade behaviour,
#      assigned to `dal/facade.py` by section 0.4.1.5; a program-level `goback.`
#      does not belong in a per-table module. `dispatch` performs no recovery, as
#      `*>   Any errors leave it to caller to recover from`
#      [common/acasirsub5.cbl:L519] says it should not.
#   6. `01 Old-File-Function pic 9 value zero.` [common/irsfinalMT.cbl:L144] and
#      `MOST-Relation` [:L131] - both declared, neither used. A45 and A24.
#   7. THE `stop "Cobol File EOF"` [common/acasirsub5.cbl:L272]. Flat path, and
#      A18: nothing in this module terminates a process.
#   8. `copy "wsnames.cob"` [:L135] beyond the linkage itself. The RDB path uses
#      no file name; `file_defs` is carried so the parameter order matches.
#   9. NO DELETE OF ANY KIND. This bridge has no `ba080-Process-Delete`, no
#      `ba085`, no `DELETE FROM` and no `TRUNCATE`, so no `delete` or
#      `delete_all` verb is published and `open_output` clears nothing. Rule R-3
#      forbids inventing one, and `acas008`'s delete-all coercion is that
#      handler's behaviour, not this one's.
#
#  10. TRANSLATION CORRECTION C1 - THE ONE STATEMENT WITH NO COBOL COUNTERPART.
#      `_alias_enumerated_into_array` has no paragraph to map to, because the
#      compiled program needs none: `ar1-A` and `AR1 (A)` are one byte area
#      [copybooks/irswsfinal.cob:L8-L36, :L38-L66] and section 0.3.1 requires the
#      two `redefines` views be modelled as separate dataclasses, which makes them
#      two objects here. It is called at the head of `write` and `rewrite`,
#      immediately before the loops that reproduce `perform varying A from 1 by 1`
#      [common/irsfinalMT.cbl:L476, :L524], so the loads at [:L484-L485] and
#      [:L528-L529] read the same values the compiled loads would have. Direction
#      is settled by the frozen source, not chosen: the enumerated names are
#      written by the operator through SCREEN `using` [irs/irs020.cbl:L472-L593],
#      the array names are written by nothing but this bridge's own read-unload
#      [common/irsfinalMT.cbl:L455-L456]. The read direction needs no correction.
#      Rationale, evidence and the R-3 argument are in the module docstring under
#      TRANSLATION CORRECTIONS.
#
# CITATION CORRECTIONS
#   Every locator in this module was read from the frozen file rather than copied
#   from the brief. The divergences - and the fifteen anomalies beyond the brief's
#   thirty-one - are listed in the module docstring under WHERE THE PLAN'S LINE
#   NUMBERS DIFFER FROM THE FROZEN SOURCE, so they are recorded once and not
#   rediscovered as defects.
#
# --- end traceability -------------------------------------------------------
