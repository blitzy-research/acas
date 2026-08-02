"""`gl080` - the General Ledger End Of Cycle Processing  [general/gl080.cbl].

The migration of `general/gl080.cbl` in its entirety. Boundary: THE WHOLE
PROGRAM. Agent Action Plan section 0.2.1.1 lists this file with migration
boundary "Whole program", and only two of the twelve in-scope programs are
partial - `gl051` and `irs030`. `gl080` is not one of them. So the archiving
path `gl080b`/`arc-process`, the interactive `disk-change`, and `compress-post`
are all migrated, not carved out. The plan's prose describes the file as
"Phase 3 transaction deletion and Phase 5 end-of-period processing", which is a
description of the emphasis and NOT a narrowing of the boundary.

Eight sections, THIRTY-EIGHT labels, THIRTY-SIX `GO TO` sites, six paragraphs
named `loop.`, seven named `main-exit.` and three named `end-run.` - the most
structurally complex program in the twelve, and the reason every function below
is section-qualified.

FIVE PHASE LABELS, TWO OF WHICH COLLIDE WITH OTHER PROGRAMS
===========================================================
`gl080` displays five phase labels of its own, MEASURED at these lines:

    L306   "Phase - 1.  Batch Check"
    L316   "Phase - 2.  Transaction Archiving"
    L319   "Phase - 3.  Transaction Deletion"
    L637   "Phase - 4.  Posting Contraction "
    L336   "Phase - 5.  End of Period Processing"

Two of them collide with a DIFFERENT program's phase of the same number:

    Phase 1  is "Batch Check" here [general/gl080.cbl:L306] AND "Batch Check"
             in `gl070` [general/gl070.cbl:L284] - same number, same name, two
             different programs and two different detector predicates. See
             THE DETECTOR IS NOT `gl070`'S below.
    Phase 2  is "Transaction Archiving" here [general/gl080.cbl:L316] but
             "Transaction Pre-process" in `gl070` [general/gl070.cbl:L292].
    Phase 4  is "Posting Contraction " here [general/gl080.cbl:L637] - note the
             literal's trailing space - but "Transaction Update" in `gl072`
             [general/gl072.cbl:L274].

AND THE NUMBERING IS NOT THE EXECUTION ORDER. Across the General Ledger family
the order in which the labelled phases actually run is:

    `gl070`  phase 1  batch check                 [general/gl070.cbl:L284]
    `gl070`  phase 2  transaction pre-process     [general/gl070.cbl:L292]
    `gl071`  unlabelled sort                      [general/gl071.cbl:L172-L178]
    `gl072`  phase 4  transaction update          [general/gl072.cbl:L274]
    `gl080`  phase 1  batch check       AGAIN     [general/gl080.cbl:L306]
    `gl080`  phase 2  archiving   OR   phase 3 deletion - never both
                                                  [general/gl080.cbl:L315-L320]
    `gl080`  phase 4  posting contraction AGAIN   [general/gl080.cbl:L637]
    `gl080`  phase 5  end of period               [general/gl080.cbl:L336]

So phase 3 is labelled before phase 4 and runs before it; phase 4 runs twice
across the family under two different names; phase 1 runs twice under the same
name. Agent Action Plan section 0.6.4 asks for the labels to be preserved
"so a maintainer is not misled", and this block is that preservation. Nothing
below infers an ordering from a phase number.

THE PHASE DRIVER, VERBATIM  [general/gl080.cbl:L306-L337]
=========================================================
    306      display  "Phase - 1.  Batch Check" ...
    307      perform  gl080a.
    308      if       a = 1
    313               go to  main-end.
    315      if       archiving
    316               display "Phase - 2.  Transaction Archiving" ...
    317               perform gl080b
    318      else
    319               display "Phase - 3.  Transaction Deletion" ...
    320               perform gl080c.
    322      perform  compress-post.
    324      if       a = 9
    325           or  scycle <  period
    326               go to  main-end.
    328      divide   scycle by period giving a rounded.
    329      multiply a  by  period  giving  y.
    331      if       scycle not = y
    332               go to  main-end.
    334      add      1  to scycle.
    336      display  "Phase - 5.  End of Period Processing" ...
    337      perform  GL-Nominal-Open.

`archiving` is the `88`-level over `Arch pic x` [copybooks/wssystem.cob:L164-
L165], so archiving and deletion are mutually exclusive - one `perform` or the
other, never both, and never neither.

`gl080b` AND `gl080c` HAVE IDENTICAL DATABASE EFFECTS
=====================================================
This is the key insight for reading a table dump of this program, and it is
easy to miss because the two sections look nothing alike. Both walk the batch
file filtered on the accounting cycle, delete EVERY posting belonging to the
batch, then stamp and rewrite the batch header with the SAME three moves:

    archiving  [general/gl080.cbl:L430-L433]    deletion  [general/gl080.cbl:L585-L589]
      move 2        to cleared-status               move 2        to cleared-status
      move run-date to stored                       move run-date to stored
      move zero     to batch-start                  move zero     to batch-start
      perform GL-Batch-Rewrite                      perform GL-Batch-Rewrite

Byte for byte the same stamping, and both inner sections delete through
`GL-Posting-Delete` - [general/gl080.cbl:L513] in `arc-process`,
[general/gl080.cbl:L622] in `del-process`. The ONLY difference is that
`arc-process` additionally writes three rows per posting to a FLAT ARCHIVE FILE
[general/gl080.cbl:L481], [general/gl080.cbl:L495], [general/gl080.cbl:L508],
and that file is not a schema table. IN AN ORDERING-NORMALIZED TABLE-STATE DIFF
THE TWO PATHS ARE INDISTINGUISHABLE. A scenario that means to exercise the
archiving path must therefore pin `Arch` explicitly and assert on something
other than the tables, or it is silently testing the deletion path.

Compare `gl072`'s parallel stamping [general/gl072.cbl:L375-L377]: same shape,
but it moves 1 (`Processed`) not 2 (`Archived`), writes `posted` not `stored`,
and does NOT zero `batch-start`. Three differences in three lines, all
preserved.

THE TABLE EFFECT IS NARROWER THAN THE PROGRAM IS LARGE
======================================================
Only three things in this whole program reach a table:

    1. `GL-Posting-Delete`, once per posting, in BOTH the archive path
       [general/gl080.cbl:L513] and the delete path [general/gl080.cbl:L622].
       `gl080` is the ONLY in-scope program that performs this verb.
    2. The batch stamping plus `GL-Batch-Rewrite`, once per batch in the cycle
       [general/gl080.cbl:L430-L433], [general/gl080.cbl:L585-L589].
    3. Phase 5's `GL-Nominal-Rewrite` [general/gl080.cbl:L348], performed for
       EVERY nominal account the sequential walk reaches - a full-table update
       of `GLLEDGER-REC`.

`compress-post` reaches a table only in the Cobol-files configuration, and see
below for why it never gets that far in the frozen source. Everything else -
five sections' worth of screen handling, path building and diagnostics - has no
database effect at all.

Q-23  `compress-post` CANNOT REACH ITS OWN LOOPS IN THE FROZEN SOURCE
=====================================================================
Two independent gates stand in front of `loop1` [general/gl080.cbl:L654], and
in the frozen source EVERY configuration is stopped by one of them.

THE FIRST GATE, the configuration test [general/gl080.cbl:L633-L635]:

    633      if       not FS-Cobol-Files-Used
    634               go to main-exit
    635      end-if.

`88 FS-Cobol-Files-Used value zero.` [copybooks/wssystem.cob:L113] and
`88 FS-RDBMS-Used value 1.` [copybooks/wssystem.cob:L116] are two condition
names over one `pic 9`. Running against MySQL the flag is 1, so
`not FS-Cobol-Files-Used` is TRUE and the section returns immediately. The body
below it is unreachable in that configuration - and IT IS NOT DELETED, because
the gate is a runtime test of a value that arrives in the system record, not a
compile-time constant. Rule R-3 forbids removing it and rule R-4 forbids
tidying it.

THE SECOND GATE, the record-size test [general/gl080.cbl:L643-L649]:

    643      if       function length (WS-Posting-Record) not =
    644               function length (work-file-record)
    645-647           display GL082 / GL083 / GL012
    648               accept Keyed-Reply at 1227
    649               stop run.

MEASURED, and the two lengths ARE NOT EQUAL:

    function length (WS-Posting-Record)  = 103   summed from the descriptors
    function length (work-file-record)   = 101   `pic x(101)` [general/gl080.cbl:L172]

`WS-Posting-Record` [copybooks/wspost.cob:L12-L28] sums to 103 bytes over its
fifteen elementary items, every one of them DISPLAY: 5 + 5 + 5 + 2 + 8 + 6 + 2
+ 6 + 2 + 10 + 32 + 6 + 2 + 2 + 10. Two independent parts of this package
already record the derivation and its provenance - `acas_posting/cobol/usage.py`
question Q-5.2 reports a compiled measurement under GnuCOBOL 3.2.0 establishing
that a zoned DISPLAY item is `digits` bytes wide, that the "96 bytes"
[copybooks/wspost.cob:L7] in that copybook's header is the maintainer's
arithmetic slip, and that the record corrects to 98 bytes without `WS-Post-rrn`;
and `acas_posting/records/gl_posting.py` records the three figures 96, 98 and
103 side by side. Adding `WS-Post-rrn pic 9(5)` [copybooks/wspost.cob:L13]
carries the layout to 103.

The maintainer's own note on the work record [general/gl080.cbl:L172] reads
"Was 96 added 5 for WS-Post-rrn (9(5)" - he took the slipped 96 from that
header and added 5 to reach 101. The record is 103, so the work file is TWO
BYTES SHORT and the test at L643 is TRUE.

CONSEQUENCE: in the Cobol-files configuration `compress-post` executes
`stop run` [general/gl080.cbl:L649] and terminates the run unit. In the RDBMS
configuration it returns at L634. `loop1`, `loop1-end`, `loop2`, `file-error`
and `loop2-end` are therefore unreachable in BOTH configurations of the frozen
source. Every one of them is nonetheless reproduced in full below, and the two
lengths are COMPUTED FROM THE DESCRIPTORS rather than written as literals, so
that if the compiled oracle reports something else the code follows the
dictionary and not this note. Logged as question Q-23.

THE FALL-THROUGH IN `compress-post`, AND WHY IT MATTERS
=======================================================
`file-error.` [general/gl080.cbl:L688] ends at [general/gl080.cbl:L697] with a
`display` and NO transfer of control, so it FALLS STRAIGHT THROUGH into
`loop2-end.` [general/gl080.cbl:L699]:

    688  file-error.
    691-695  display GL081 / fs-reply / perform evaluate-message / ... / GL012
    696      accept   Keyed-Reply at 1627.
    697      display  " " at 1601 with erase eol.
                                                     <-- no GO TO here
    699  loop2-end.
    702      close    work-file.
    703      perform  GL-Posting-Close.

Four `go to file-error` sites reach it - [general/gl080.cbl:L661] and
[general/gl080.cbl:L664] from `loop1`, [general/gl080.cbl:L681] and
[general/gl080.cbl:L685] from `loop2`. So a write or read failure inside
`loop1` prints, then closes through `loop2-end`, SKIPPING `loop1-end`'s own
closes at [general/gl080.cbl:L670-L671] entirely - it never reopens the work
file for input and never performs `GL-Posting-Open-Output`. The requirement
that "`PERFORM THRU` and fall-through becom[e] explicit function composition
that preserves execution order" makes each of the four sites an explicit
two-call sequence, and each carries its own equivalence proof below.

TWO INTERACTIVE PROMPTS GATE DATABASE WRITES
============================================
Agent Action Plan section 0.3.4, verbatim: "Accept prompts that gate a database
write become explicit CLI parameters with the COBOL default preserved." Two of
this program's five `accept` statements do exactly that.

    [general/gl080.cbl:L299-L302]  THE RUN CONFIRM.

        299      accept   keyed-reply at 1065 with update auto.
        300      if       cob-crt-status = cob-scr-esc
        301          or   keyed-reply = "A" or "a"
        302               goback.

    Answering A, a, or Escape returns from the program BEFORE ANY WRITE OF ANY
    KIND. Promoted to `run_confirmed`, defaulting to True - the COBOL's
    proceed answer, which is any reply that is not one of those three.

    [general/gl080.cbl:L545-L547]  THE `disk-change` OPTION.

        545      accept   a at 1369.
        546      if       a = 9
        547               go to  main-exit.

    This is the clearest database-gating prompt in the General Ledger folder.
    Answering 9 leaves `a = 9`, which [general/gl080.cbl:L408-L409] then tests
    to skip the whole of the archiving walk, AND which
    [general/gl080.cbl:L324-L326] tests to skip the whole of phase 5. One
    keystroke suppresses the batch stamping, every posting delete, the
    ledger-quarter rollover and the cycle increment. Promoted to
    `disk_change_option`, defaulting to 0 - the COBOL's proceed answer.

    [general/gl080.cbl:L555]  THE ARCHIVE PATH EDIT.

        555      accept   file-2  at 1501 with ... update.

    Gates WHERE THE FLAT ARCHIVE FILE IS WRITTEN, not what any table holds.
    Promoted to `archive_path_override`, defaulting to None, which keeps the
    value `disk-change` itself computes. It has NO table effect.

The other two - [general/gl080.cbl:L311-L312] and [general/gl080.cbl:L648] and
[general/gl080.cbl:L696] - are acknowledgement pauses whose only effect is to
block a terminal. They are DROPPED, and the control transfers around them are
PRESERVED: `go to main-end` [general/gl080.cbl:L313], `stop run`
[general/gl080.cbl:L649], and the fall-through at [general/gl080.cbl:L697].

ONE VARIABLE, THREE UNRELATED PURPOSES
======================================
`77 a pic 99 value zero.` [general/gl080.cbl:L183] is used for three things
that have nothing to do with each other, and the sharing is OBSERVABLE:

    1. THE BATCH-CHECK DETECTOR. Zeroed [general/gl080.cbl:L290], set to 1 by
       `gl080a` [general/gl080.cbl:L386], tested [general/gl080.cbl:L308].
    2. THE `disk-change` ABORT CODE. Accepted [general/gl080.cbl:L545], tested
       [general/gl080.cbl:L408] and again [general/gl080.cbl:L324].
    3. THE QUARTER SUBSCRIPT. Computed [general/gl080.cbl:L328], used as a
       table subscript [general/gl080.cbl:L345].

`divide scycle by period giving a rounded` [general/gl080.cbl:L328] OVERWRITES
whatever `a` held, including the 9 that [general/gl080.cbl:L324] has just
tested. Trace both values through: a `disk-change` abort of 9 reaches L324,
satisfies it and returns before L328 can clobber it; a detector value of 1
reaches L324, fails both of its conditions, and IS clobbered at L328. So the
sharing changes nothing in the first case and everything in the second, and it
is therefore modelled as ONE field rather than split into three well-named
locals. Splitting it would be a behaviour change disguised as a readability
improvement.

`77 y pic 99 value zero.` [general/gl080.cbl:L182] is the round-trip product,
used only at [general/gl080.cbl:L329] and [general/gl080.cbl:L331].

THE DETECTOR IS NOT `gl070`'S
=============================
    `gl070`  [general/gl070.cbl:L314-L315]   if status-open
                                                move 1 to a.
    `gl080a` [general/gl080.cbl:L384-L386]   if not status-closed
                                              and not processed
                                                move 1 to a.

Different predicate over different fields - `Batch-Status`
[copybooks/wsbatch.cob:L25-L27] versus `Cleared-Status`
[copybooks/wsbatch.cob:L29-L32] - and NOT interchangeable. `not status-closed`
is true for any `Batch-Status` other than 1, which includes but is not limited
to `status-open`; `not processed` is true for any `Cleared-Status` other than 1,
which includes `waiting` and `archived` alike. And unlike `gl070`, which raises
`move 5 to ws-term-code` [general/gl070.cbl:L289] so the menu skips the rest of
the cycle, `gl080` sets NO term code at all - it simply displays and returns
[general/gl080.cbl:L313], [general/gl080.cbl:L366].

THE ABORT CHAIN DOES NOT REACH THIS PROGRAM
===========================================
The menu dispatches `gl080` from `load09.` [general/general.cbl:L817-L820],
which moves the program name and then `go to load00.` - a transfer, not a
`perform`. `load00.` [general/general.cbl:L711-L722] zeroes `ws-term-code`
before the `CALL` [general/general.cbl:L714], issues the four-parameter call
[general/general.cbl:L715-L718], and tests `if ws-term-code > 7` afterwards
[general/general.cbl:L720-L721]. What `load08.` adds and `load09.` lacks is the
`gl070`-specific `if ws-term-code = 5` test [general/general.cbl:L810-L811],
and it is absent here because `gl080` never sets a term code. This program's
own aborts are all local: `goback` [general/gl080.cbl:L302], three `go to
main-end` transfers [general/gl080.cbl:L313], [general/gl080.cbl:L326],
[general/gl080.cbl:L332], and one `stop run` [general/gl080.cbl:L649].

TWO FLAT FILES THAT ARE NOT SCHEMA TABLES AND NOT THE CYCLE'S WORK FILES
========================================================================
    138  select  archive    assign  file-2   access sequential  status fs-reply
                            organization line sequential.
    143  select  work-file  assign  file-21  access sequential
                            organization sequential  status fs-reply.

Neither reaches the database, so neither appears in a table dump. See
STRUCTURAL NOTES in the traceability footer for why both are declared
module-privately here rather than added to the package's work-file layer, and
for the three facts that decision rests on: `arc-trans-record` is a TEN-field
78-byte layout whose field order differs from the cycle's work records,
`work-file-record` is one unstructured `pic x(101)`, and the package's
sequential work-file type cannot express `open extend`
[general/gl080.cbl:L411].

`work-file` is assigned `file-21`, which is `work.tmp` [copybooks/file21.cob:L1]
- THE SAME FILE NAME `gl071` ASSIGNS TO ITS SORT WORK FILE
[general/gl071.cbl:L102]. A genuine collision between two programs' scratch
files. It is harmless because the two never run at the same time, and rule R-3
forbids concurrency in any case, but it is exactly the kind of fact
traceability exists to surface.

BOTH FLAT FILES DECLARE `fs-reply` AS THEIR FILE STATUS, and `fs-reply` is
`Fs-Reply pic 99` [copybooks/wsfnctn.cob:L25] - the very field the facade and
its handlers write. So a flat-file open, read or write and a facade verb SHARE
ONE STATUS FIELD, and each overwrites the other's reply. `open extend archive`
[general/gl080.cbl:L411] sets it and `perform GL-Batch-Open`
[general/gl080.cbl:L415] immediately overwrites it; `write work-file-record`
[general/gl080.cbl:L662] sets it and [general/gl080.cbl:L663] tests it. The
sequences below therefore store their status INTO the shared `File-Access`
record, which is what a FILE STATUS clause does.

RULES THIS MODULE IS HELD TO
============================
There is NO user rules document for this project - `review_rules` reports "No
user rules provided", verified this session. The six binding rules live in the
Agent Action Plan section 0.7.2 and are answered here one by one; where the
plan is silent, enterprise-standard best practice applies and no rule has been
invented to fill a gap.

R-1, NO COBOL AT RUNTIME. Nothing here starts a process, loads a foreign
library, or reaches the compiled-oracle tree. There is NO
`call "SYSTEM" using Print-Report` anywhere in `general/gl080.cbl` - checked,
the string `SYSTEM` appears only as `system-record` and `Op-System` - and no
print file, so unlike `gl072` there is no report spool-out path to omit. The
`STRING` statement in `disk-change` [general/gl080.cbl:L531-L536] builds a FILE
PATH STRING and nothing else; it is not turned into a command line.

R-2, ZERO BINARY FLOATING POINT. Every value is `decimal.Decimal` or `int`,
carried under the field descriptor of the item that receives it. And per Agent
Action Plan section 0.3.1 - "`cobol/` contains no business logic and
`programs/` contains no numeric primitives" - there is no hand-written scale
alignment, truncation, packed or zoned encoding, picture parse, `MOVE`
truncation, `88`-level test, `STRING` implementation, reference-modification
implementation or comparator anywhere below. Every one of those delegates.

    `gl080` OWNS EXACTLY ONE OF THE FIVE `ROUNDED` SITES IN THE WHOLE
    MIGRATION - [general/gl080.cbl:L328] - and its un-`ROUNDED` companion sits
    on the very next line. The complete arithmetic census for this program:

        L328  divide   scycle by period giving a rounded    <-- THE ONLY ONE
        L329  multiply a by period giving y                     truncates
        L334  add      1 to scycle                              truncates
        L355  add      1 to current-quarter                     truncates
        L477  add      post-amount vat-amount giving arc-amount truncates
        L489  add      post-amount vat-amount giving arc-amount truncates
        L493  multiply arc-amount by -1 giving arc-amount        truncates
        L506  multiply arc-amount by -1 giving arc-amount        truncates
        L643  function length (...) twice, an integer count, no store

    Every store other than L328 TRUNCATES TOWARD ZERO, which is the COBOL
    default when `ROUNDED` is not written. Getting that backwards would
    corrupt essentially every posted figure. There is no `ON SIZE ERROR` and
    no `REMAINDER` phrase anywhere in this program.

R-3, NOTHING ADDED. No conditional statement below tests anything the frozen
source does not test. In particular: NO bounds check on the quarter subscript,
which IS anomaly A-2; NO guard on `GL-Posting-Open-Output`; NO check of the
archive write beyond the one test [general/gl080.cbl:L412] the source has; NO
check that `period` is non-zero before the L328 divide. No transaction
wrapper and no undo or partial-undo marker around the delete-then-stamp pairs -
the COBOL commits per statement, and adding atomicity would change what a
mid-run failure leaves behind. No DDL, no ORM entity layer, no migration tool.
No threads, no event loop, no process pool, no connection pool: execution is
strictly sequential, and Agent Action Plan section 0.8.4 puts performance work
"out of scope by construction, not merely unrequested". `compress-post` in
particular looks like a hand-rolled table rebuild begging to be replaced by one
SQL statement. It is not replaced.

R-4, ANOMALIES REPRODUCED. Five reproduction sites, each annotated inline with
its locator: A-2 the unbounded quarter subscript, A-3 the two disagreeing
notions of "current quarter", A-21 three qualified references, and the two
archive sign flips at [general/gl080.cbl:L493] and [general/gl080.cbl:L506].
The full treatment is at each site and in the footer.

R-5, FULL TRACEABILITY. A named function for every one of the 38 labels, a
`GO TO class` annotation at every one of the 36 transfer sites, per-site
equivalence proofs for the five class-4 sites, and a footer mapping every
construct and every deliberate omission to its frozen locator.

R-6, COMPILED BEHAVIOUR IS THE TIE-BREAKER. No clock is read. `general/gl080.cbl`
contains ZERO clock reads; the date arrives as the `to-day` linkage parameter
and as `Run-Date binary-long` [copybooks/wssystem.cob:L67] inside the system
record. `move run-date to stored` [general/gl080.cbl:L431] and
[general/gl080.cbl:L586] write that controlled-clock observable straight into
`GLBATCH-REC`, which is a value the migration's byte-identical-reruns test
depends on being pinned, so both read it from the system record and nothing
below reaches for an ambient time source. Six questions are logged for
arbitration against the compiled program; see AMBIGUITIES.

WHAT THIS MODULE MAY IMPORT
===========================
`gl080` carries TWELVE `COPY` statements. Their translation, in file order:

    envdiv.cob                 L131   omitted, representation only
    wsledger.cob               L188   records/gl_ledger
    wsbatch.cob                L189   records/gl_batch
    wspost.cob                 L190   records/gl_posting   <-- `gl072` does NOT
                                      copy this one; `gl080` does
    Test-Data-Flags.cob        L216   records/test_data_flags
    screenio.cpy               L219   omitted, presentation only
    wsfnctn.cob                L258   records/file_access AND dal/status
    wscall.cob                 L263   records/calling_data
    wssystem.cob               L264   records/system_record
    wsnames.cob                L265   records/file_defs
    FileStat-Msgs.cpy          L713   a message table, see `_evaluate_message`
    Proc-ACAS-FH-Calls.cob     L749   dal/facade

BECAUSE THE FILE COPIES `Proc-ACAS-FH-Calls.cob` AND NOT
`Proc-ZZ100-ACAS-IRS-Calls.cob`, THIS PROGRAM USES THE ENTITY-NAMED FACADE
VOCABULARY AND TESTS THE REPLY INLINE. That copybook has no error-check
paragraph of any kind, so every `fs-reply` test below is the caller's own, and
none of the handler-named aliases is called. Sixteen distinct verbs are
performed, the largest set of the twelve programs.

MUST NOT be imported, and none is: the CLI layer, any handler module directly,
the connection module, the cursor-state module, the controlled-clock module
`acas_posting/clock.py`, the dictionary generator, the compiled-oracle tree, or
any sibling program module. `acas_posting/workfiles.py` is NOT imported either -
`gl080` shares no work file with `gl070`, `gl071` or `gl072`, and its two flat
files cannot be expressed by that layer; see STRUCTURAL NOTES.

`gl080` has NO `zz050-Validate-Date` section, NO `zz060-Convert-Date` section
and NO wrapper section around the shared binary date program. Its only date
section is `zz070-Convert-Date` [general/gl080.cbl:L719]. Anomaly A-22 - a
wrapper section named after the interface copybook whose exit label is named
after the called program - therefore DOES NOT OCCUR in this module, and no date
validation or binary conversion is called from here.

AMBIGUITIES, FOR ARBITRATION AGAINST COMPILED BEHAVIOUR  (rule R-6)
===================================================================
Six questions cannot be settled by reading the source. Each is annotated
`AMBIGUITY Q-nn` at the site that raises it, and each takes the next free
number in the migration's shared register, which stood at Q-17.

    Q-18  WHETHER `move 1 to File-Key-No` [general/gl080.cbl:L288] HAS ANY
          OBSERVABLE EFFECT. The facade's own dispatch paragraphs move 1 into
          `File-Key-No` before every call - [copybooks/Proc-ACAS-FH-Calls.cob]
          `acas005.`, `acas006.` and `acas007.` each do so, and the Python
          facade pins the same value - so the program's own move is either
          redundant or it matters to a verb that does not re-pin it. Reproduced
          regardless.
    Q-19  WHAT THE COMPILED PROGRAM DOES WHEN THE QUARTER SUBSCRIPT IS OUT OF
          RANGE. See anomaly A-2 at `_gl080_main_loop`. COBOL indexes past a
          four-element table silently, overwriting adjacent storage; Python
          cannot do that. The divergence is declared rather than papered over,
          and no guard is added.
    Q-20  WHETHER `GL-Posting-Open-Output` [general/gl080.cbl:L673] TRUNCATES
          `GLPOSTING-REC`. `Open-Output` on the transfer-file handler means
          "delete every row" [common/acas008.cbl:L313-L319], and if `acas006`
          shares that reading then this statement empties the posting table
          before `loop2` rewrites it from the work file. Q-23 says the
          statement is unreachable in the frozen source; that does not settle
          what it would do. No guard is added.
    Q-21  WHETHER THIS PROGRAM'S FIVE SYSTEM-RECORD MUTATIONS ARE PERSISTED.
          `add 1 to scycle` [general/gl080.cbl:L334], `add 1 to
          current-quarter` [general/gl080.cbl:L355], `move 1 to current-quarter`
          [general/gl080.cbl:L357] and the two cycle wraps
          [general/gl080.cbl:L360], [general/gl080.cbl:L363] - plus `move 1 to
          Date-Form` [general/gl080.cbl:L730] - all write into the system
          record. `gl080` PERFORMS NO `System-*` FACADE VERB AT ALL, so whether
          any of them reaches `SYSTEM-REC` depends entirely on what the caller
          does with the by-reference linkage parameter afterwards. All six are
          reproduced in memory; none is written to a table from here.
    Q-22  WHAT PATH THE `disk-change` `STRING` ACTUALLY BUILDS. The maintainer
          flagged it himself, inline: `*> this lot looks wrong !!!!!`
          [general/gl080.cbl:L530]. Measured against the package's own record
          defaults the result is "archives archive.dat" - a SPACE where a
          directory separator belongs, because `file-24` defaults to 532 spaces
          so `DELIMITED BY SPACE` contributes nothing from it, and
          `File-Defs-os-Delimiter` defaults to a space. Reproduced exactly as
          written; see `_disk_change` for the measured widths, which also
          correct a claim that the following `MOVE` truncates.
    Q-23  WHETHER `compress-post` ABORTS THE RUN IN THE COBOL-FILES
          CONFIGURATION. See the section of that name above: the two record
          lengths measure 103 and 101, so `stop run` [general/gl080.cbl:L649]
          fires. The comparison is computed from the descriptors, never from a
          literal, so the code follows the dictionary.
"""

from __future__ import annotations

import dataclasses
import logging
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Final, Mapping

# copy "Proc-ACAS-FH-Calls.cob".  [general/gl080.cbl:L749]
# The 21-entity, 12-verb facade blueprint. `gl080` copies the ENTITY-named
# convention, which carries no error-check paragraph, so every `fs-reply` test
# in this module is the caller's own and no handler-named alias is used.
# Sixteen distinct verbs are performed from here.
from acas_posting.dal import facade

# copy "wsfnctn.cob".  [general/gl080.cbl:L258] - the operation half.
# `Fs-Reply pic 99` [copybooks/wsfnctn.cob:L25] is tested against zero and
# against 10 at fourteen sites below, and it is ALSO the FILE STATUS of both
# flat files [general/gl080.cbl:L140], [general/gl080.cbl:L146].
from acas_posting.dal.status import FsReply

# The COBOL-language semantics layer. Nothing in this module implements any of
# it; every arithmetic store, every `MOVE`, every `88`-level test, the `STRING`
# and the reference modifications delegate here (Agent Action Plan section
# 0.3.1).
from acas_posting.cobol import arithmetic, condition_names, move, picture

# `descriptors_for_copybook_record` is imported as a BARE NAME rather than
# through its module, because `dataclasses.field` is already bound above and the
# module `acas_posting.cobol.field` would shadow it - or be shadowed by it -
# depending on import order. The two are unrelated and both are needed here, so
# neither is allowed to own the name.
from acas_posting.cobol.field import FieldDescriptor, descriptors_for_copybook_record

# copy "wscall.cob".  [general/gl080.cbl:L263]
# `01 WS-Calling-Data` [copybooks/wscall.cob:L6-L13] - the first linkage
# parameter. `gl080` never reads or writes a field of it; see Q-21 and the
# OMISSIONS list.
from acas_posting.records.calling_data import WsCallingData

# copy "wsnames.cob".  [general/gl080.cbl:L265]
# `01 File-Defs.` [copybooks/wsnames.cob:L13]. Supplies `file-2`
# [copybooks/file02.cob:L1] and `file-21` [copybooks/file21.cob:L1] - the two
# `assign` clauses [general/gl080.cbl:L138], [general/gl080.cbl:L143] - plus
# `file-24` [copybooks/file24.cob:L1] and `File-Defs-os-Delimiter`, the two
# other sources of the `disk-change` `STRING`.
from acas_posting.records.file_defs import FileDefs

# copy "wsfnctn.cob".  [general/gl080.cbl:L258] - the data half.
# `01 File-Access` [copybooks/wsfnctn.cob:L22-L41] carries `Fs-Reply`,
# `We-Error`, the `Logging-Data` group holding `File-Key-No`
# [copybooks/wsfnctn.cob:L46], and `Lin2` [copybooks/wsfnctn.cob:L33], which is
# the display field [general/gl080.cbl:L291] moves the cycle into.
from acas_posting.records.file_access import FileAccess

# copy "wsbatch.cob".  [general/gl080.cbl:L189]
from acas_posting.records.gl_batch import GlBatchRecord

# copy "wsledger.cob".  [general/gl080.cbl:L188]
# `LedgerQuarters` is the four NAMED quarter fields and `LedgerQuartersTable`
# is the `occurs 4` view over the same bytes [copybooks/wsledger.cob:L31-L36].
# Both are imported because phase 5 must write through both; see
# `_gl080_main_loop`.
from acas_posting.records.gl_ledger import (
    LedgerQuarters,
    LedgerQuartersTable,
    WsLedgerRecord,
)

# copy "wspost.cob".  [general/gl080.cbl:L190]
# `gl080` DOES copy this, unlike `gl072`, because it reads the posting table
# through `acas006` rather than a work file.
from acas_posting.records.gl_posting import WsPostingRecord

# copy "wssystem.cob".  [general/gl080.cbl:L264]
from acas_posting.records.system_record import SystemRecord

# copy "Test-Data-Flags.cob".  [general/gl080.cbl:L216]
# `01 ACAS-DAL-Common-data.` - the logging switch, passed through to every
# handler as the fifth call argument.
from acas_posting.records.test_data_flags import AcasDalCommonData

# The house convention for attaching a `FieldDescriptor` to a dataclass
# attribute, borrowed from the package's work-record layouts so that the two
# module-private layouts below carry their provenance the same way every other
# record layout in the package does.
from acas_posting.records.work_records import COBOL_FIELD_METADATA_KEY

# The date-conversion interface copybook is NOT copied by this program, and no
# date validation or
# binary conversion is reached from here. The single date section is
# `zz070-Convert-Date` [general/gl080.cbl:L719-L747], which is byte-identical
# in all ten carriers and therefore consolidated.
from acas_posting.dates import WsDateFormats, zz070_convert_date

#: The whole public surface: the program's single entry point, mirroring its
#: `PROCEDURE DIVISION USING` list [general/gl080.cbl:L269-L272]. Agent Action
#: Plan section 0.3.3, verbatim: "Each `programs/*.py` module exposes a single
#: `run(...)` entry mirroring its COBOL `PROCEDURE DIVISION USING` list, with
#: the paragraph functions private to the module. Callers cannot reach into a
#: program's internals, exactly as a COBOL `CALL` cannot." All 38 paragraph and
#: section functions are therefore private, and a tuple is used so the surface
#: cannot be extended in place at run time.
__all__: Final[tuple[str, ...]] = ("run",)

_LOG: Final[logging.Logger] = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
#  WORKING-STORAGE FIELD DESCRIPTORS  [general/gl080.cbl:L182-L187]
# ---------------------------------------------------------------------------
#
# Four `77`/`01` items of this program's own working storage receive a value
# below, so each needs the descriptor of the field that receives it (rule R-2:
# the receiving field decides the truncation, not the value). The generated
# dictionary covers copybook and table fields, not a program's local working
# storage, so these four are built from their frozen declarations with an
# explicit `source_locator`. `FieldDescriptor.__post_init__` requires either a
# dictionary key or a locator, so provenance cannot be omitted by accident.

# 183  77  a                   pic 99          value zero.
# THE FIELD WITH THREE UNRELATED PURPOSES - see ONE VARIABLE, THREE UNRELATED
# PURPOSES in the module docstring. `pic 99` is two unsigned digits, so its
# value domain is 0 through 99 and a subscript computed into it can legally
# hold 0 or any value up to 99 against a four-element table (anomaly A-2).
_A: Final[FieldDescriptor] = picture.descriptor_for(
    "99 value zero", name="a", source_locator="general/gl080.cbl:L183", level="77"
)

# 182  77  y                   pic 99          value zero.
# The round-trip product of the period test, written only at
# [general/gl080.cbl:L329] and read only at [general/gl080.cbl:L331].
_Y: Final[FieldDescriptor] = picture.descriptor_for(
    "99 value zero", name="y", source_locator="general/gl080.cbl:L182", level="77"
)

# 185  77  ws-eval-msg         pic x(25)       value spaces.
# The receiving field of the file-status message lookup [general/gl080.cbl:L713].
# Diagnostic only.
_WS_EVAL_MSG: Final[FieldDescriptor] = picture.descriptor_for(
    "x(25) value spaces",
    name="ws-eval-msg",
    source_locator="general/gl080.cbl:L185",
    level="77",
)

# 187  01  Arg-Test            pic x(525)      value spaces.
# The receiver of the `disk-change` `STRING` [general/gl080.cbl:L531-L536].
# FIVE HUNDRED AND TWENTY-FIVE characters, which is SEVEN SHORT of the 532 of
# `file-2` [copybooks/file02.cob:L1] - so the `MOVE` at [general/gl080.cbl:L537]
# PADS rather than truncates. See `_disk_change`, question Q-22.
_ARG_TEST: Final[FieldDescriptor] = picture.descriptor_for(
    "x(525) value spaces",
    name="Arg-Test",
    source_locator="general/gl080.cbl:L187",
    level="01",
)

# 03  file-2  pic x(532).  [copybooks/file02.cob:L1]
# The receiving field of [general/gl080.cbl:L537] and the item whose first
# character [general/gl080.cbl:L556] inspects.
_FILE_2: Final[FieldDescriptor] = picture.descriptor_for(
    "x(532)", name="file-2", source_locator="copybooks/file02.cob:L1"
)


# ---------------------------------------------------------------------------
#  COPYBOOK AND TABLE FIELD DESCRIPTORS - looked up, never transcribed
# ---------------------------------------------------------------------------
#
# Every field below that belongs to a copybook record or a table column takes
# its descriptor from the generated data dictionary, so no picture, scale, sign
# or usage is retyped here (rule R-5: field-level traceability is mechanical).
# `FieldDescriptor.from_dictionary_key` is memoised upstream, so the repeated
# module-load lookups cost one parse each.

#: `05  Scycle  redefines cyclea  binary-char.`  [copybooks/wssystem.cob:L63]
#: Receives [general/gl080.cbl:L334], [general/gl080.cbl:L360] and
#: [general/gl080.cbl:L363]; read by the divide [general/gl080.cbl:L328] and by
#: three cycle filters.
_SCYCLE: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "System-Record.Scycle"
)

#: `05  Current-Quarter  pic 9.`  [copybooks/wssystem.cob:L110]
#: The SECOND, INDEPENDENT notion of "current quarter" - anomaly A-3. Receives
#: [general/gl080.cbl:L355] and [general/gl080.cbl:L357].
_CURRENT_QUARTER: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "SYSTEM-REC.CURRENT-QUARTER"
)

#: `05  Date-Form  pic 9.`  [copybooks/wssystem.cob]
#: THE FIFTH AND LAST SYSTEM-RECORD MUTATION THIS PROGRAM MAKES, and the only
#: one outside `gl080-Main`: `if Date-Form = zero / move 1 to Date-Form.`
#: [general/gl080.cbl:L729-L730] inside the date section. A `SYSTEM-REC` column,
#: so the store is diff-visible if the caller persists the record - AMBIGUITY
#: Q-21.
_DATE_FORM: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "SYSTEM-REC.DATE-FORM"
)

#: `03  Ledger-Balance  pic s9(8)v99  comp-3.`  [copybooks/wsledger.cob:L28]
#: The sending field of both phase-5 moves [general/gl080.cbl:L345],
#: [general/gl080.cbl:L347].
_LEDGER_BALANCE: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLLEDGER-REC.LEDGER-BALANCE"
)

#: `03  Ledger-Last  pic s9(8)v99  comp-3.`  [copybooks/wsledger.cob:L29]
_LEDGER_LAST: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLLEDGER-REC.LEDGER-LAST"
)

#: `05  Ledger-Q  pic s9(8)v99  comp-3  occurs 4.`
#: [copybooks/wsledger.cob:L36] - a REDEFINES over `Ledger-Q1` through
#: `Ledger-Q4` [copybooks/wsledger.cob:L31-L34]. The subscripted receiver of
#: [general/gl080.cbl:L345], and the table anomaly A-2 indexes without a bound.
#: `occurs` is read from this descriptor rather than written as a literal 4.
_LEDGER_Q: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "WS-Ledger-Record.Ledger-Q"
)

#: `03  Cleared-Status  pic 9.`  [copybooks/wsbatch.cob:L29]
#: Receives the value of `88 Archived value 2.` [copybooks/wsbatch.cob:L32] at
#: [general/gl080.cbl:L430] and [general/gl080.cbl:L585].
_CLEARED_STATUS: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLBATCH-REC.CLEARED-STATUS"
)

#: `05  Stored  binary-long.`  [copybooks/wsbatch.cob:L39]
#: Receives `Run-Date` [copybooks/wssystem.cob:L67] at
#: [general/gl080.cbl:L431] and [general/gl080.cbl:L586] - a controlled-clock
#: observable written into a table column (rule R-6).
_STORED: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLBATCH-REC.STORED"
)

#: `03  Batch-Start  pic 9(5).`  [copybooks/wsbatch.cob:L54]
#: Zeroed at [general/gl080.cbl:L432] and [general/gl080.cbl:L587]. `gl072`'s
#: parallel stamping does NOT include this move.
_BATCH_START: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLBATCH-REC.BATCH-START"
)

#: `03  WS-Batch-Nos  pic 9(5).`  [copybooks/wsbatch.cob:L19]
#: The sending field of [general/gl080.cbl:L449] and the right operand of the
#: batch filters [general/gl080.cbl:L460] and [general/gl080.cbl:L617].
_WS_BATCH_NOS: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "WS-Batch-Record.WS-Batch-Nos"
)

#: The fourteen `WS-Posting-Record` fields the archive explosion reads
#: [copybooks/wspost.cob:L14-L28]. Named individually so that each `MOVE`
#: below can cite the sending item as well as the receiver, which is what lets
#: `cobol.move` apply the correct unlike-picture rule.
_POST_CODE: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLPOSTING-REC.POST-CODE"
)
_POST_DATE: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLPOSTING-REC.POST-DAT"
)
_POST_LEGEND: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLPOSTING-REC.POST-LEGEND"
)
_POST_DR: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLPOSTING-REC.POST-DR"
)
_DR_PC: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLPOSTING-REC.DR-PC"
)
_POST_CR: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLPOSTING-REC.POST-CR"
)
_CR_PC: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLPOSTING-REC.CR-PC"
)
_POST_AMOUNT: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLPOSTING-REC.POST-AMOUNT"
)
_VAT_AC: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLPOSTING-REC.VAT-AC"
)
_VAT_PC: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLPOSTING-REC.VAT-PC"
)
_VAT_AMOUNT: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLPOSTING-REC.VAT-AMOUNT"
)
_POST_NUMBER: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "WS-Posting-Record.Post-Number"
)
_POST_BATCH: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "WS-Posting-Record.Batch"
)

#: `05  File-Key-No  pic 9.`  [copybooks/wsfnctn.cob:L46]
#: The receiver of [general/gl080.cbl:L288] - question Q-18.
_FILE_KEY_NO: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "File-Access.File-Key-No"
)

#: `05  Lin2  pic 99.`  [copybooks/wsfnctn.cob:L33], a redefines of
#: `Curs2 pic 9(4)` [copybooks/wsfnctn.cob:L31]. The receiver of
#: [general/gl080.cbl:L291]. Its three uses [general/gl080.cbl:L291],
#: [general/gl080.cbl:L402], [general/gl080.cbl:L566] are display only, but the
#: move itself DOES write into the shared `File-Access` block and is therefore
#: reproduced rather than dropped with the display.
_LIN2: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "File-Access.Lin2"
)


# ---------------------------------------------------------------------------
#  fd  archive.   [general/gl080.cbl:L156-L168]
# ---------------------------------------------------------------------------
#
# TEN fields, SEVENTY-EIGHT characters, and a field order that is NOT the order
# of the cycle's work records: `arc-amount` sits BEFORE `arc-legend`, and the
# two contra fields close the record after it. The cycle's `pre-trans` layout
# [general/gl070.cbl:L108-L116] has eight fields, carries no contra pair at all,
# and puts its amount before its legend as well but has nothing following. So
# this layout cannot be borrowed from the package's work-record module, and the
# generated dictionary carries no entry for any of these ten fields - checked,
# it holds no `arc-trans-record` key and no `general/gl080.cbl` program source.
# Each descriptor therefore carries an explicit `source_locator`.
#
#     158  01  arc-trans-record.
#     159      03  arc-batch   pic 9(5).     160  03  arc-post    pic 9(5).
#     161      03  arc-code    pic xx.       162  03  arc-date    pic x(8).
#     163      03  arc-ac      pic 9(6).     164  03  arc-pc      pic 99.
#     165      03  arc-amount  pic s9(8)v99. 166  03  arc-legend  pic x(32).
#     167      03  arc-c-ac    pic 9(6).     168  03  arc-c-pc    pic 99.

_ARC_BATCH: Final[FieldDescriptor] = picture.descriptor_for(
    "9(5)", name="arc-batch", source_locator="general/gl080.cbl:L159"
)
_ARC_POST: Final[FieldDescriptor] = picture.descriptor_for(
    "9(5)", name="arc-post", source_locator="general/gl080.cbl:L160"
)
_ARC_CODE: Final[FieldDescriptor] = picture.descriptor_for(
    "xx", name="arc-code", source_locator="general/gl080.cbl:L161"
)
_ARC_DATE: Final[FieldDescriptor] = picture.descriptor_for(
    "x(8)", name="arc-date", source_locator="general/gl080.cbl:L162"
)
_ARC_AC: Final[FieldDescriptor] = picture.descriptor_for(
    "9(6)", name="arc-ac", source_locator="general/gl080.cbl:L163"
)
_ARC_PC: Final[FieldDescriptor] = picture.descriptor_for(
    "99", name="arc-pc", source_locator="general/gl080.cbl:L164"
)
# Signed, scale 2, DISPLAY zoned with a trailing overpunched sign because the
# declaration carries no usage clause and no sign clause. Negated outright at
# [general/gl080.cbl:L493] and conditionally at [general/gl080.cbl:L506], so
# negative values are routine. `decimal.Decimal`, never a binary fraction (R-2).
_ARC_AMOUNT: Final[FieldDescriptor] = picture.descriptor_for(
    "s9(8)v99", name="arc-amount", source_locator="general/gl080.cbl:L165"
)
_ARC_LEGEND: Final[FieldDescriptor] = picture.descriptor_for(
    "x(32)", name="arc-legend", source_locator="general/gl080.cbl:L166"
)
_ARC_C_AC: Final[FieldDescriptor] = picture.descriptor_for(
    "9(6)", name="arc-c-ac", source_locator="general/gl080.cbl:L167"
)
_ARC_C_PC: Final[FieldDescriptor] = picture.descriptor_for(
    "99", name="arc-c-pc", source_locator="general/gl080.cbl:L168"
)

# 172  01  work-file-record  pic x(101).   *> Was 96 added 5 for WS-Post-rrn (9(5).
# ONE UNSTRUCTURED ALPHANUMERIC ITEM, not a record with fields. The maintainer's
# own comment records the width change, and question Q-23 in the module
# docstring shows the arithmetic behind it is two bytes short of the 103 the
# posting record actually occupies. The declared width is carried here and the
# comparison at [general/gl080.cbl:L643] reads it from this descriptor.
_WORK_FILE_RECORD: Final[FieldDescriptor] = picture.descriptor_for(
    "x(101)",
    name="work-file-record",
    source_locator="general/gl080.cbl:L172",
    level="01",
)


@dataclass(slots=True)
class _ArcTransRecord:
    """`01  arc-trans-record.` - the flat archive row  [general/gl080.cbl:L158].

    The record area of `fd archive.` [general/gl080.cbl:L156], written three
    times per posting by `arc-process` - a debit leg
    [general/gl080.cbl:L481], a credit leg negated outright
    [general/gl080.cbl:L493], [general/gl080.cbl:L495], and a value-added-tax
    leg written only when both the tax account and the tax amount are non-zero
    [general/gl080.cbl:L497-L508].

    MODULE-PRIVATE BY DESIGN, not by omission. See STRUCTURAL NOTES in the
    traceability footer. In short: the layout appears in no copybook, in no
    table and in no dictionary entry, it is not one of the cycle's work
    records, and nothing in it reaches the database - so it appears in no table
    dump and belongs to the one program that declares it.

    Attributes:
        arc_batch: `03  arc-batch   pic 9(5).` Set once before the posting walk
            [general/gl080.cbl:L449] and then again per posting
            [general/gl080.cbl:L465].
        arc_post: `03  arc-post    pic 9(5).` The posting number.
        arc_code: `03  arc-code    pic xx.` Filled by a QUALIFIED move,
            anomaly A-21 [general/gl080.cbl:L467].
        arc_date: `03  arc-date    pic x(8).` EIGHT characters, inherited from
            `Post-Date pic x(8)` [copybooks/wspost.cob:L18]. Not a truncation
            of the ten-character run date, and the century is not restored.
        arc_ac: `03  arc-ac      pic 9(6).` The account. SWAPPED with
            `arc_c_ac` between leg one and leg two.
        arc_pc: `03  arc-pc      pic 99.` The profit centre, swapped likewise.
        arc_amount: `03  arc-amount  pic s9(8)v99.` Signed, scale 2.
        arc_legend: `03  arc-legend  pic x(32).` The narrative. DECLARED AFTER
            the amount, which is where this layout parts company with the
            cycle's work records.
        arc_c_ac: `03  arc-c-ac    pic 9(6).` The contra account. No counterpart
            exists in `pre-trans-record`, so leg two's four-field swap has no
            analogue in `gl070`'s explosion.
        arc_c_pc: `03  arc-c-pc    pic 99.` The contra profit centre. NOT reset
            by leg three, which leaves leg two's values standing
            [general/gl080.cbl:L501-L503].
    """

    arc_batch: int = field(default=0, metadata={COBOL_FIELD_METADATA_KEY: _ARC_BATCH})
    arc_post: int = field(default=0, metadata={COBOL_FIELD_METADATA_KEY: _ARC_POST})
    arc_code: str = field(
        default="  ", metadata={COBOL_FIELD_METADATA_KEY: _ARC_CODE}
    )
    arc_date: str = field(
        default=" " * 8, metadata={COBOL_FIELD_METADATA_KEY: _ARC_DATE}
    )
    arc_ac: int = field(default=0, metadata={COBOL_FIELD_METADATA_KEY: _ARC_AC})
    arc_pc: int = field(default=0, metadata={COBOL_FIELD_METADATA_KEY: _ARC_PC})
    arc_amount: Decimal = field(
        default=Decimal("0.00"), metadata={COBOL_FIELD_METADATA_KEY: _ARC_AMOUNT}
    )
    arc_legend: str = field(
        default=" " * 32, metadata={COBOL_FIELD_METADATA_KEY: _ARC_LEGEND}
    )
    arc_c_ac: int = field(default=0, metadata={COBOL_FIELD_METADATA_KEY: _ARC_C_AC})
    arc_c_pc: int = field(default=0, metadata={COBOL_FIELD_METADATA_KEY: _ARC_C_PC})



# ---------------------------------------------------------------------------
#  THE TWO FLAT SEQUENCES  [general/gl080.cbl:L138-L146], [L156-L172]
# ---------------------------------------------------------------------------
#
# Neither file is a schema table and neither is one of the cycle's work files,
# so neither can be served by the package's work-file layer - which publishes
# only `pre_trans`, `post_trans` and `sort_trans`, and whose open modes are
# deliberately limited to input and output with NO extend, while
# [general/gl080.cbl:L411] needs `open extend`. Both are therefore modelled here
# as ordered in-memory sequences, insertion order absolute, and nothing about
# either reaches the database. See STRUCTURAL NOTES.
#
# BOTH DECLARE `fs-reply` AS THEIR FILE STATUS [general/gl080.cbl:L140],
# [general/gl080.cbl:L146], and that is `Fs-Reply pic 99`
# [copybooks/wsfnctn.cob:L25] - the same field the facade's handlers write. So
# every operation below stores its status into the SHARED `File-Access` record,
# which is exactly what a FILE STATUS clause does, and a facade verb performed
# straight afterwards overwrites it. That sharing is reproduced, not tidied.

#: File status "00" - successful completion. `Fs-Reply` is `pic 99`, so the
#: two-character status lands in it as a number and the test
#: `if fs-reply not = zero` [general/gl080.cbl:L412] reads it as one.
_FS_OK: Final[int] = int(FsReply.SUCCESS)

#: File status "10" - at end. The value every sequential read reports when the
#: sequence is exhausted, and the value fourteen tests below compare against.
_FS_AT_END: Final[int] = int(FsReply.END_OF_FILE)

#: File status "35" - an attempt to open a non-optional file that is not
#: present. What `open extend archive` [general/gl080.cbl:L411] reports the
#: first time a scenario runs, which is precisely the case the maintainer's own
#: comment anticipates: "just in case extend wont create a non-existent file"
#: [general/gl080.cbl:L412-L413]. Only the non-zero-ness of the reply reaches
#: the test, so the exact digits do not change the branch taken.
_FS_FILE_NOT_FOUND: Final[int] = 35


class _StopRun(RuntimeError):
    """Reproduces `stop run.`  [general/gl080.cbl:L649].

    THE ONE PLACE THIS PROGRAM TERMINATES THE RUN UNIT RATHER THAN RETURNING.
    `compress-post` compares the length of the posting record against the length
    of its own work record and, when they disagree, displays three messages,
    pauses, and executes `stop run` - Agent Action Plan section 0.6.5's
    run-aborting rejection class, whose database effect is THE ABSENCE of
    everything the statements below it would have written.

    WHY THIS IS A NEW EXCEPTION AND NOT A REUSED ONE. The package publishes one
    abort already, `FacadeGoback`, and its own documentation rules it out here:
    it "reproduces the `goback.` that ends the shared abort paragraph" and "is an
    exception and not a process exit on purpose", because `goback` returns to the
    calling program, which may still have end-of-job work to do. `stop run` is
    the opposite instruction - it ends the RUN UNIT, so the caller's remaining
    work does not happen either. The sibling handler module makes the same
    distinction in the other direction, noting that a called subprogram's
    `exit program` "is a return, not a `stop run`, and treating it as a process
    exit would be a behaviour change of the most drastic kind"
    [common/acas007.cbl:L561]. Conflating the two would lose exactly the
    difference the frozen source is drawing.

    WHY IT IS AN EXCEPTION AND NOT A PROCESS EXIT. Raising propagates out of
    `run()` to whoever invoked it, which is how a caller learns the run unit
    ended abnormally, and it lets the scenario comparison layer observe the
    abort
    instead of losing its own process. A process exit would also make the
    condition untestable, and the migration's tests are how a defect stays
    reproduced. It is deliberately NOT caught anywhere in this module: nothing
    below [general/gl080.cbl:L649] executes, and nothing here swallows it.

    Also NOT reused: the handler layer's error type, which belongs to the IRS
    calling convention's per-handler error checks
    [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob]. This program copies
    `Proc-ACAS-FH-Calls.cob` [general/gl080.cbl:L749], the convention with no
    error-check paragraph at all, and tests every reply inline.

    Recorded as a deviation in the traceability footer under STRUCTURAL NOTES.
    """


class _SequentialFile:
    """One flat sequential file: its record area, its rows and its status.

    The base of the two `fd` entries this program declares. It reproduces four
    things and no more - the record area a `WRITE` publishes and a `READ`
    fills, the ordered rows, the open mode, and the FILE STATUS clause that
    routes every reply into the shared `File-Access` record.

    NOT A WORK FILE OF THE CYCLE. Nothing here is shared with `gl070`, `gl071`
    or `gl072`, and nothing here reaches a table.

    Args:
        name: The `assign` clause's file name, carried for diagnostics only.
        file_access: The `01 File-Access` record whose `Fs-Reply`
            [copybooks/wsfnctn.cob:L25] is this file's FILE STATUS.
    """

    __slots__ = ("_file_access", "_name", "_open", "_position", "_present", "_rows")

    def __init__(self, name: str, file_access: FileAccess) -> None:
        self._name = name
        self._file_access = file_access
        self._rows: list[object] = []
        self._position = 0
        self._open = False
        # A sequence that has never been opened for output stands for a file
        # that is not yet on disk, which is the state the archive is in the
        # first time a scenario runs. A caller that pre-populates `rows` is
        # standing in for a file left behind by a previous cycle.
        self._present = False

    @property
    def name(self) -> str:
        """The `assign` clause's file name."""
        return self._name

    @property
    def rows(self) -> tuple[object, ...]:
        """Every row written so far, in the order it was written."""
        return tuple(self._rows)

    def _reply(self, status: int) -> None:
        """Store a file status into the shared `Fs-Reply`, as FILE STATUS does."""
        self._file_access.fs_reply = status

    def open_input(self) -> None:
        """`open input <file>` - position at the first row, status 00."""
        self._position = 0
        self._open = True
        self._present = True
        self._reply(_FS_OK)

    def open_output(self) -> None:
        """`open output <file>` - CREATE OR TRUNCATE, then status 00.

        Every existing row is discarded. This is what
        [general/gl080.cbl:L414] does to the archive when the extend fallback
        fires, and what [general/gl080.cbl:L652] does to the work file.
        """
        self._rows.clear()
        self._position = 0
        self._open = True
        self._present = True
        self._reply(_FS_OK)

    def open_extend(self) -> None:
        """`open extend <file>` - append, or report file-not-found.

        [general/gl080.cbl:L411]. Succeeds with status 00 when the file is
        present, and reports 35 when it is not - which is the case
        [general/gl080.cbl:L412-L414] exists to recover from. The package's own
        sequential work-file type has no extend mode at all, which is one of the
        three reasons this class exists; see STRUCTURAL NOTES.
        """
        if not self._present:
            # NOT AN ERROR PATH. The reply is the answer to a question the
            # source asks and handles two lines later.
            self._reply(_FS_FILE_NOT_FOUND)
            return
        self._position = len(self._rows)
        self._open = True
        self._reply(_FS_OK)

    def close(self) -> None:
        """`close <file>` - status 00. A closed file keeps its rows."""
        self._open = False
        self._reply(_FS_OK)


class _ArchiveFile(_SequentialFile):
    """`fd archive.` - the flat archive  [general/gl080.cbl:L156-L168].

    `organization line sequential`, `access sequential`, status in `fs-reply`
    [general/gl080.cbl:L138-L141], assigned `file-2`
    [copybooks/file02.cob:L1]. Written only; this program never reads it back.

    Args:
        file_access: The record carrying this file's FILE STATUS.
    """

    __slots__ = ("record",)

    def __init__(self, file_access: FileAccess) -> None:
        super().__init__("archive", file_access)
        #: The record area `01 arc-trans-record.` [general/gl080.cbl:L158].
        self.record = _ArcTransRecord()

    def write(self) -> None:
        """`write arc-trans-record.` - append a SNAPSHOT of the record area.

        Performed three times per posting [general/gl080.cbl:L481],
        [general/gl080.cbl:L495], [general/gl080.cbl:L508] against ONE record
        area, so each write must capture an INDEPENDENT COPY of the fields as
        they stand. Sharing one object between the three rows would make every
        row show the last leg's values - the same trap `gl070`'s three writes
        [general/gl070.cbl:L508], [general/gl070.cbl:L519],
        [general/gl070.cbl:L532] carry.
        """
        self._rows.append(dataclasses.replace(self.record))
        self._reply(_FS_OK)


class _WorkFile(_SequentialFile):
    """`fd work-file.` - the contraction scratch file  [general/gl080.cbl:L170].

    `organization sequential`, `access sequential`, status in `fs-reply`
    [general/gl080.cbl:L143-L146], assigned `file-21`, which is `work.tmp`
    [copybooks/file21.cob:L1] - THE SAME NAME `gl071` gives its sort work file
    [general/gl071.cbl:L102].

    Its record `01 work-file-record pic x(101).` [general/gl080.cbl:L172] is
    ONE UNSTRUCTURED ALPHANUMERIC ITEM, so the record area is a string of
    exactly 101 characters and both the write and the read below are GROUP
    MOVES of raw characters rather than field-by-field transfers.

    Args:
        file_access: The record carrying this file's FILE STATUS.
    """

    __slots__ = ("posting_image", "record")

    def __init__(self, file_access: FileAccess) -> None:
        super().__init__("work-file", file_access)
        #: The record area, `pic x(101)` wide.
        self.record: str = move.move_figurative(move.SPACE, _WORK_FILE_RECORD)
        #: The posting whose image the last row read carries; see the class
        #: docstring's note on how a group's byte image is modelled here.
        self.posting_image: WsPostingRecord | None = None

    def write_from(
        self,
        posting: WsPostingRecord,
        *,
        image: str,
        group: FieldDescriptor,
    ) -> None:
        """`write work-file-record from WS-Posting-Record.`

        [general/gl080.cbl:L662]. The FROM phrase performs
        `MOVE WS-Posting-Record TO work-file-record` and then writes, so the
        move happens first. Its receiver is the ELEMENTARY `pic x(101)` item and
        its sender is a GROUP, which makes it an alphanumeric move of the
        sender's byte image into the receiver's width - laid in from the left,
        truncated or space-padded on the right. The width work is `cobol.move`'s
        and none of it is done here.

        HOW A GROUP'S BYTE IMAGE IS MODELLED, AND WHY. Rendering the fifteen
        elementary items of `WS-Posting-Record` into their zoned bytes needs the
        byte-layout module, which is deliberately outside what a program module
        may import (Agent Action Plan section 0.4.3), and reimplementing zoned or
        packed layout here is forbidden outright - "`cobol/` contains no business
        logic and `programs/` contains no numeric primitives" (section 0.3.1). So
        the image carries the WIDTH, applied by `cobol.move` against the two
        descriptors, and the FIELD VALUES travel beside it as an independent
        snapshot. That is exact under the precondition the source itself
        establishes two paragraphs earlier: `Test-Work-File-Size-1`
        [general/gl080.cbl:L643-L644] refuses to proceed unless the two records
        are THE SAME WIDTH, and at equal widths the write-then-read round trip is
        the identity - which is what the snapshot is. See STRUCTURAL NOTES, and
        AMBIGUITY Q-23 for why no execution can observe the difference.

        Args:
            posting: The sending group's current field values.
            image: The sending group's byte image, `group`'s width wide.
            group: The sending group's descriptor, so the unlike-picture rule is
                applied rather than guessed.
        """
        self.record = move.move(image, _WORK_FILE_RECORD, sending_field=group)
        self._rows.append((self.record, _copy_posting_record(posting)))
        self._reply(_FS_OK)

    def read(self) -> bool:
        """`read work-file at end ...`  [general/gl080.cbl:L678].

        Returns:
            True when a row was read into the record area, False at end of
            file. The AT END phrase is a control transfer rather than a status
            test, so the caller branches on this answer; `fs-reply` is set
            either way because the FILE STATUS clause applies to every
            operation, and [general/gl080.cbl:L680] tests it on the path where
            a row WAS read.
        """
        if self._position >= len(self._rows):
            self._reply(_FS_AT_END)
            return False
        area, snapshot = self._rows[self._position]
        self.record = str(area)
        self.posting_image = snapshot
        self._position = self._position + 1
        self._reply(_FS_OK)
        return True


def _copy_posting_record(posting: WsPostingRecord) -> WsPostingRecord:
    """An independent copy of `01 WS-Posting-Record.` [copybooks/wspost.cob:L12].

    `WRITE` publishes the record area's CURRENT contents, so a row must not
    alias the live record that the next `READ` overwrites - the same trap the
    archive's three writes carry [general/gl080.cbl:L481],
    [general/gl080.cbl:L495], [general/gl080.cbl:L508]. The nested group
    `03 WS-Post-Key.` [copybooks/wspost.cob:L14] is copied too, because copying
    only the outer record would leave the key shared.

    Args:
        posting: The record area to snapshot.

    Returns:
        A copy that no later read can disturb.
    """
    return dataclasses.replace(
        posting, ws_post_key=dataclasses.replace(posting.ws_post_key)
    )


# ---------------------------------------------------------------------------
#  WORKING STORAGE AND LINKAGE, IN ONE PLACE
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class _Gl080Storage:
    """This program's linkage, working storage, records and facade contexts.

    COBOL working storage is visible to every paragraph of the program, and
    eight sections here read and write the same handful of fields - `a` alone is
    touched by five of them. So one object carries all of it and every paragraph
    function below takes it, which reproduces the sharing exactly and keeps each
    function a faithful one-to-one image of its paragraph rather than a
    signature-shaped approximation of it.

    Attributes:
        ws_calling_data: `01 WS-Calling-Data` [copybooks/wscall.cob:L6-L13].
            Accepted and never read - `gl080` sets no term code.
        system: `SYSTEM-REC`. Read for `Scycle`, `Period`, `Arch`,
            `Current-Quarter`, `Date-Form`, `Run-Date`, `Usera` and
            `File-System-Used`; MUTATED at six sites, question Q-21.
        to_day: `01 to-day pic x(10).` [general/gl080.cbl:L267], a DD/MM/CCYY
            text date and the only date input.
        file_defs: `01 File-Defs.` [copybooks/wsnames.cob:L13]. Supplies the two
            `assign` names and three of the four `STRING` sources.
        file_access: `01 File-Access` [copybooks/wsfnctn.cob:L22]. Carries
            `Fs-Reply`, which is BOTH the facade's status and both flat files'
            FILE STATUS.
        dal_common: `01 ACAS-DAL-Common-data.`
            [copybooks/Test-Data-Flags.cob], the logging switch every handler
            receives as its fifth argument.
        ledger: `WS-Ledger-Record` [copybooks/wsledger.cob], the record `acas005`
            reads and rewrites.
        batch: `WS-Batch-Record` [copybooks/wsbatch.cob], the record `acas007`
            reads and rewrites.
        posting: `WS-Posting-Record` [copybooks/wspost.cob], the record `acas006`
            reads, deletes, writes and rewrites.
        a: `77 a pic 99 value zero.` [general/gl080.cbl:L183]. ONE FIELD, THREE
            UNRELATED PURPOSES; see the module docstring. Modelled as one field
            because the sharing is observable.
        y: `77 y pic 99 value zero.` [general/gl080.cbl:L182].
        ws_eval_msg: `77 ws-eval-msg pic x(25).` [general/gl080.cbl:L185].
            Diagnostic only; never tested, never stored to a table.
        ws_date_formats: The `01 ws-date-formats` redefines block
            [general/gl080.cbl:L222-L243] that `zz070-Convert-Date` fills.
        archive: `fd archive.` [general/gl080.cbl:L156].
        work_file: `fd work-file.` [general/gl080.cbl:L170].
        run_confirmed: The promoted run-confirm answer
            [general/gl080.cbl:L299-L302].
        disk_change_option: The promoted `disk-change` option
            [general/gl080.cbl:L545-L547].
        archive_path_override: The promoted archive path edit
            [general/gl080.cbl:L555], or None to keep what `disk-change`
            computes.
        dal_options: Forwarded verbatim to every handler as
            `FacadeContext.options`. Python plumbing with no COBOL counterpart;
            see `run`.
    """

    ws_calling_data: WsCallingData
    system: SystemRecord
    to_day: str
    file_defs: FileDefs
    file_access: FileAccess
    dal_common: AcasDalCommonData
    ledger: WsLedgerRecord
    batch: GlBatchRecord
    posting: WsPostingRecord
    a: int
    y: int
    ws_eval_msg: str
    ws_date_formats: WsDateFormats
    archive: _ArchiveFile
    work_file: _WorkFile
    run_confirmed: bool
    disk_change_option: int
    archive_path_override: str | None
    dal_options: Mapping[str, object]

    def nominal_ctx(self) -> facade.FacadeContext:
        """The `acas005` call block: `WS-Ledger-Record` is the record argument.

        `perform acas005.` [copybooks/Proc-ACAS-FH-Calls.cob] issues
        `call "acas005" using System-Record WS-Ledger-Record File-Access
        File-Defs ACAS-DAL-Common-Data`, and this is that parameter list in that
        order. A fresh context per verb is deliberate: the record identity is
        what distinguishes the three handlers, and `FacadeContext` is frozen so
        it cannot be mutated between verbs by accident.
        """
        return facade.FacadeContext(
            system=self.system,
            record=self.ledger,
            file_access=self.file_access,
            file_defs=self.file_defs,
            dal_common=self.dal_common,
            options=self.dal_options,
        )

    def batch_ctx(self) -> facade.FacadeContext:
        """The `acas007` call block: `WS-Batch-Record` is the record argument."""
        return facade.FacadeContext(
            system=self.system,
            record=self.batch,
            file_access=self.file_access,
            file_defs=self.file_defs,
            dal_common=self.dal_common,
            options=self.dal_options,
        )

    def posting_ctx(self) -> facade.FacadeContext:
        """The `acas006` call block: `WS-Posting-Record` is the record argument."""
        return facade.FacadeContext(
            system=self.system,
            record=self.posting,
            file_access=self.file_access,
            file_defs=self.file_defs,
            dal_common=self.dal_common,
            options=self.dal_options,
        )



# ---------------------------------------------------------------------------
#  gl080-Main section.   [general/gl080.cbl:L275]
# ---------------------------------------------------------------------------


def _gl080_main(st: _Gl080Storage) -> None:
    """`gl080-Main section.` - setup, the confirm gate and the phase driver.

    [general/gl080.cbl:L275-L337]. The program's entry section. It sets up, asks
    whether a backup has been taken, runs phase 1, chooses between archiving and
    deletion, runs the posting contraction, decides whether this cycle ends a
    period, and only then opens the nominal ledger for phase 5.

    OMITTED FROM THIS FUNCTION, each recorded in the footer: the two
    `set ENVIRONMENT` statements [general/gl080.cbl:L280-L281], which force
    Escape and the paging keys to be detectable and are screen setup with no
    database effect; and the banner, date and user displays
    [general/gl080.cbl:L283-L284], [general/gl080.cbl:L286-L287], which become
    one log record each.

    Args:
        st: The program's storage. `st.a`, `st.y` and the system record are all
            mutated here.

    Raises:
        _StopRun: Only by way of `compress-post` [general/gl080.cbl:L649].
    """
    # 283  display  prog-name at 0101 ...
    # 284  display  "End Of Cycle Processing" at 0130 ...
    # Diagnostics with no database effect - Agent Action Plan section 0.3.4 puts
    # them in its first class: a log record at a severity matching the
    # original's intent, altering no control flow and appearing in no table
    # dump. `prog-name` is `77 prog-name pic x(15) value "gl080 (3.3.00)".`
    # [general/gl080.cbl:L181]; unlike `gl072`, this program never writes it to
    # a print line, so the literal survives only as log text.
    _LOG.info("gl080 (3.3.00) - End Of Cycle Processing")

    # 285  perform  zz070-convert-date.
    # PRESERVED, not dropped with the display that consumes it, because it
    # MUTATES `Date-Form` on the system record when that field is zero
    # [general/gl080.cbl:L729-L730].
    _zz070_convert_date(st)

    # 286  display  ws-date at 0171 ...
    # 287  display  usera at 0301 ...
    _LOG.info(
        "run date %s, user %s",
        st.ws_date_formats.ws_date,
        st.system.system_data_block.suser.usera,
    )

    # 288  move     1  to File-Key-No.
    # AMBIGUITY Q-18 - WHETHER THIS MOVE HAS ANY OBSERVABLE EFFECT. The facade's
    # own dispatch paragraphs move 1 into `File-Key-No` before every one of the
    # sixteen verbs this program performs, and the Python facade pins the same
    # value, so this statement is either redundant or it matters to something
    # that does not re-pin it. Reproduced either way: it is a `MOVE` into a
    # field of the shared `File-Access` block, and the compiled program executes
    # it.
    st.file_access.logging_data.file_key_no = move.move(1, _FILE_KEY_NO)

    # 290  move     zero  to  a.
    # `a` IN ITS FIRST ROLE: the batch-check detector flag. See ONE VARIABLE,
    # THREE UNRELATED PURPOSES in the module docstring.
    st.a = move.move_figurative(move.ZERO, _A)

    # 291  move     scycle to lin2.
    # Feeds the three "Cycle - " displays [general/gl080.cbl:L402],
    # [general/gl080.cbl:L566]. The DISPLAYS are dropped; THE MOVE IS NOT,
    # because it writes into the shared `File-Access` block
    # [copybooks/wsfnctn.cob:L33] which the handlers also read and write.
    st.file_access.curs2_parts.lin2 = move.move(
        st.system.system_data_block.scycle, _LIN2, sending_field=_SCYCLE
    )

    # 295  display  GL085  at 0801 ...    "Have you taken a backup?"
    # 296  display  GL086  at 0901 ...
    # 297  display  GL087  at 1001 ...
    # The three backup warnings [general/gl080.cbl:L253-L255]. Logged at WARNING
    # because that is the severity the original's `highlight` attribute and its
    # placement immediately before an abort gate convey.
    _LOG.warning(
        "end of cycle processing is about to run - a backup should have been "
        "taken first"
    )

    # 298  move     space to keyed-reply.
    # 299  accept   keyed-reply at 1065 with update auto.
    # 300  if       cob-crt-status = cob-scr-esc
    # 301      or   keyed-reply = "A" or "a"
    # 302           goback.
    #
    # THE FIRST OF THE TWO PROMPTS THAT GATE A DATABASE WRITE. Promoted to the
    # `run_confirmed` parameter per Agent Action Plan section 0.3.4, with the
    # COBOL's proceed answer as the default. The screen mechanism -
    # `77 keyed-reply pic x` [general/gl080.cbl:L184], `cob-crt-status` and
    # `cob-scr-esc` from `screenio.cpy` [general/gl080.cbl:L219] - is omitted;
    # THE DECISION IS NOT. Answering A, a or Escape returns before any write of
    # any kind, so a rejected run leaves the database completely untouched,
    # which is the first of the five rejection classes in Agent Action Plan
    # section 0.6.5.
    if not st.run_confirmed:
        # 302  goback.
        _LOG.info("run declined at the backup confirmation; nothing was posted")
        return

    # 306  display  "Phase - 1.  Batch Check" at 0801 ... erase eos.
    # THE SAME LABEL `gl070` USES [general/gl070.cbl:L284]. See FIVE PHASE
    # LABELS in the module docstring.
    _LOG.info("Phase - 1.  Batch Check")

    # 307  perform  gl080a.
    _gl080a(st)

    # 308  if       a = 1
    # `a` IN ITS FIRST ROLE, read back. Note that the value reaching here can
    # only be 0 or 1: `gl080a` writes nothing else, and the `disk-change` code
    # and the quarter subscript are both still in the future.
    if arithmetic.compare(st.a, 1) == 0:
        # 309  display GL088 at 1501 ...        "Batches outstanding"
        # 310  display GL012 at 1701 ...        "Press return"
        # 311  move     space to keyed-reply
        # 312  accept   keyed-reply at 1065 ...
        # The accept is an ACKNOWLEDGEMENT PAUSE whose only effect is to block a
        # terminal; it is dropped. The transfer that follows it is preserved.
        _LOG.warning(
            "batches are outstanding for this cycle - end of cycle processing "
            "cannot run"
        )
        # 313  go to  main-end.
        # GO TO class 3 - a transfer to the section's terminal paragraph, whose
        # only statement is `goback.` [general/gl080.cbl:L366]. Reproduced as a
        # call to that paragraph's function followed by a return, so the
        # paragraph keeps its name (rule R-5) and the transfer keeps its shape.
        # UNLIKE `gl070`, NO TERM CODE IS SET: `gl070` raises
        # `move 5 to ws-term-code` [general/gl070.cbl:L289] so the menu skips
        # the rest of the cycle, and `gl080` simply returns.
        _main_end(st)
        return

    # 315  if       archiving
    # `88 Archiving value "Y".` [copybooks/wssystem.cob:L165] over
    # `Arch pic x` [copybooks/wssystem.cob:L164]. Evaluated through the
    # condition-name vocabulary rather than compared against a bare "Y", so the
    # declared value set is the copybook's and not this module's.
    # MUTUALLY EXCLUSIVE with the else branch: one path or the other, never
    # both, never neither - and their TABLE EFFECTS ARE IDENTICAL, see the
    # module docstring.
    if condition_names.evaluate("Archiving", st.system.general_ledger_block.arch):
        # 316  display "Phase - 2.  Transaction Archiving" ...
        # `gl070`'S PHASE 2 IS "Transaction Pre-process" [general/gl070.cbl:L292].
        _LOG.info("Phase - 2.  Transaction Archiving")
        # 317  perform gl080b
        _gl080b(st)
    else:
        # 319  display "Phase - 3.  Transaction Deletion" ...
        _LOG.info("Phase - 3.  Transaction Deletion")
        # 320  perform gl080c.
        _gl080c(st)

    # 322  perform  compress-post.
    # Phase 4, and see question Q-23: in the frozen source this section either
    # returns immediately or aborts the run, and never reaches its own loops.
    _compress_post(st)

    # 324  if       a = 9
    # 325       or  scycle <  period
    # 326           go to  main-end.
    #
    # `a` IN ITS SECOND ROLE: the `disk-change` abort code
    # [general/gl080.cbl:L545]. THIS IS THE LAST MOMENT AT WHICH THAT VALUE IS
    # LEGIBLE - the divide two lines below overwrites it. A `disk-change` abort
    # of 9 satisfies this test and returns; a detector value of 1 fails both
    # conditions and is then clobbered. Note that the abort code can only be
    # here at all when the ARCHIVING path ran, because `disk-change` is
    # performed from `gl080b` [general/gl080.cbl:L406] and from nowhere else.
    if (
        arithmetic.compare(st.a, 9) == 0
        or arithmetic.compare(
            st.system.system_data_block.scycle, st.system.system_data_block.period
        )
        < 0
    ):
        # 326  go to  main-end.
        # GO TO class 3.
        _LOG.info(
            "end of period processing skipped: cycle %s, period %s, option %s",
            st.system.system_data_block.scycle,
            st.system.system_data_block.period,
            st.a,
        )
        _main_end(st)
        return

    # 328  divide   scycle by period giving a rounded.
    #
    # THE ONLY `ROUNDED` STORE IN THIS PROGRAM, and one of exactly FIVE in the
    # whole in-scope migration - the others being [general/gl051.cbl:L791],
    # [general/gl051.cbl:L796], [irs/irs030.cbl:L1551] and
    # [irs/irs030.cbl:L1562]. `DIVIDE a BY b GIVING c` means `c = a / b`, so
    # this is `a = scycle / period` rounded half away from zero and stored into
    # `pic 99`. This is the site `tests/arithmetic/test_gl080_cycle_divide_rounded.py`
    # pins, and the ONE AND ONLY call in this module that asks for rounding -
    # every other store below truncates toward zero.
    #
    # `a` IN ITS THIRD ROLE, and the store that destroys the second: whatever
    # the prompt left here is gone from this line onward.
    #
    # NO GUARD ON `period` (rule R-3). The frozen source tests nothing before
    # dividing, so nothing is tested here; a zero divisor is the compiled
    # program's behaviour to exhibit, not this module's to prevent.
    st.a = arithmetic.divide_by_giving(
        st.system.system_data_block.scycle,
        st.system.system_data_block.period,
        _A,
        rounded=True,
    )

    # 329  multiply a  by  period  giving  y.
    #
    # IMMEDIATELY UN-`ROUNDED`, and passed as `rounded=False` explicitly so the
    # adjacency is visible at the call site rather than implied by a default.
    # THIS ADJACENCY IS WHY ROUNDING MUST BE A PER-CALL ARGUMENT AND NEVER A
    # MODULE-LEVEL MODE: three of the migration's five `ROUNDED` sites are
    # followed directly by an un-`ROUNDED` store - [general/gl051.cbl:L797],
    # this line, and [irs/irs030.cbl:L1564].
    st.y = arithmetic.multiply_by_giving(
        st.a, st.system.system_data_block.period, _Y, rounded=False
    )

    # 331  if       scycle not = y
    # 332           go to  main-end.
    #
    # THE PERIOD-BOUNDARY TEST: round-trip the divide and compare. Only a cycle
    # that is an exact multiple of the period length reaches phase 5. Because
    # the divide rounds and the multiply truncates, a cycle just below a
    # boundary rounds UP and the product then overshoots, so the test fails -
    # which is the behaviour, not a defect to correct.
    if arithmetic.compare(st.system.system_data_block.scycle, st.y) != 0:
        # 332  go to  main-end.
        # GO TO class 3.
        _LOG.info(
            "cycle %s is not a period boundary (period %s, round trip %s)",
            st.system.system_data_block.scycle,
            st.system.system_data_block.period,
            st.y,
        )
        _main_end(st)
        return

    # 334  add      1  to scycle.
    # MUTATES THE SYSTEM RECORD - question Q-21. `gl080` performs no `System-*`
    # facade verb, so whether this increment reaches `SYSTEM-REC` depends
    # entirely on what the caller does with the by-reference linkage parameter.
    # Truncating store, as every store in this program other than L328 is.
    st.system.system_data_block.scycle = arithmetic.add_to(
        1, receiver_value=st.system.system_data_block.scycle, receiving=_SCYCLE
    )

    # 336  display  "Phase - 5.  End of Period Processing" ...
    # THE AGENT ACTION PLAN CITES [general/gl080.cbl:L330] FOR THIS LABEL; the
    # measured line is L336. L330 is a comment line.
    _LOG.info("Phase - 5.  End of Period Processing")

    # 337  perform  GL-Nominal-Open.        *> open  i-o  ledger-file.
    facade.gl_nominal_open(st.nominal_ctx())

    # Control now FALLS THROUGH into `loop.` [general/gl080.cbl:L339], which is
    # the next paragraph of this same section. The three functions below are
    # called in that order so the fall-through is explicit rather than implied.
    _gl080_main_loop(st)

    # 351  loop-end.
    # THE POST-LOOP BLOCK OF THE CLASS-2 TRANSFER AT [general/gl080.cbl:L344].
    # Agent Action Plan section 0.6.3, verbatim: "the transformation is `break`
    # PLUS faithful placement of that work after the loop, not `break` alone.
    # Mis-splitting here would silently drop end-of-run processing." This is the
    # site where that bites hardest in this program: the block below holds the
    # ledger close, the quarter increment and BOTH cycle wraps, so losing it
    # would lose the entire period rollover while leaving every posted balance
    # looking correct.
    _gl080_main_loop_end(st)

    # 365  main-end.  ->  366  goback.
    _main_end(st)


def _gl080_main_loop(st: _Gl080Storage) -> None:
    """`loop.` - phase 5's walk over every nominal account.

    [general/gl080.cbl:L339-L349]. Reads the nominal ledger sequentially, files
    the account's balance into the current quarter, copies it into the year-end
    field on the fourth quarter, and rewrites. EVERY ACCOUNT IS REWRITTEN, so
    phase 5's table effect is a full-table update of `GLLEDGER-REC`.

    THE PARAGRAPH VERBATIM

        339  loop.
        342      perform  GL-Nominal-Read-Next.
        343      if       fs-reply = 10
        344               go to  loop-end.
        345      move     ledger-balance  to  ledger-q (a).
        346      if       current-quarter = 4
        347               move  ledger-balance  to  ledger-last.
        348      perform  GL-Nominal-Rewrite.
        349      go       to loop.

    Args:
        st: The program's storage.

    Raises:
        ValueError: When the quarter subscript is outside 1 through 4. That is
            anomaly A-2 surfacing, NOT a check this module added; see the
            comment at the subscripted move and question Q-19.
    """
    while True:
        # 342  perform  GL-Nominal-Read-Next.
        facade.gl_nominal_read_next(st.nominal_ctx())

        # 343  if       fs-reply = 10
        if arithmetic.compare(st.file_access.fs_reply, _FS_AT_END) == 0:
            # 344  go to  loop-end.
            # GO TO class 2 - the forward terminator. `break` here, and the
            # post-loop block runs in `_gl080_main_loop_end`, called by
            # `_gl080_main` immediately after this function returns.
            break

        # 345  move     ledger-balance  to  ledger-q (a).
        #
        # ANOMALY A-2 [general/gl080.cbl:L328], [general/gl080.cbl:L345] - the
        # quarter subscript is computed by a `ROUNDED` divide and then used as a
        # table subscript with NO BOUNDS CHECK, against
        # `05 Ledger-Q pic s9(8)v99 comp-3 occurs 4.`
        # [copybooks/wsledger.cob:L36]. `a` is `pic 99`
        # [general/gl080.cbl:L183], so its declared domain is 0 through 99 and
        # only 1 through 4 are valid. An accounting cycle that is not a small
        # multiple of the period length silently indexes past a four-element
        # table. Reproduced deliberately per R-4; DO NOT FIX. No bounds test is
        # added, and none may be.
        #
        # AMBIGUITY Q-19 - WHAT THE COMPILED PROGRAM ACTUALLY DOES OUT OF RANGE.
        # COBOL writes past the table into whatever storage follows - which in
        # this record is `filler pic x(50)` [copybooks/wsledger.cob:L37] for
        # small overruns and then off the end of the record area - silently, with
        # no diagnostic. Python cannot reproduce that, and the three candidate
        # behaviours are not equivalent: `ledger_q[a - 1]` would write QUARTER
        # FOUR when `a` is zero, because Python indexes backwards from the end,
        # which is a third behaviour that is neither the COBOL's nor an honest
        # failure. So the subscript is resolved through the declared occurrence
        # range and an out-of-range value RAISES rather than writing somewhere
        # arbitrary. The divergence is declared, not papered over; what the
        # oracle does at `a = 0` and at `a > 4` is the open question.
        _move_ledger_balance_to_quarter(st)

        # 346  if       current-quarter = 4
        #
        # ANOMALY A-3 [general/gl080.cbl:L345-L357] - TWO DISAGREEING NOTIONS OF
        # "CURRENT QUARTER" in one paragraph pair. The subscript `a` selects
        # WHICH quarter field receives the balance; `Current-Quarter pic 9`
        # [copybooks/wssystem.cob:L110], an independent counter on the system
        # record rotated at [general/gl080.cbl:L355-L357], decides whether this
        # is the YEAR-END quarter. Nothing reconciles them, so the balance can
        # be filed into quarter 2 while the year-end copy is taken because the
        # rotating counter happens to read 4. Reproduced deliberately per R-4;
        # DO NOT FIX.
        if arithmetic.compare(st.system.system_data_block.current_quarter, 4) == 0:
            # 347  move  ledger-balance  to  ledger-last.
            st.ledger.ledger_last = move.move(
                st.ledger.ledger_balance,
                _LEDGER_LAST,
                sending_field=_LEDGER_BALANCE,
            )

        # 348  perform  GL-Nominal-Rewrite.
        facade.gl_nominal_rewrite(st.nominal_ctx())

        # 349  go       to loop.
        # GO TO class 1 - the loop-back. `continue` at the foot of the body.
        continue


def _move_ledger_balance_to_quarter(st: _Gl080Storage) -> None:
    """`move ledger-balance to ledger-q (a).`  [general/gl080.cbl:L345].

    One COBOL statement, and it needs its own function for a reason that has
    nothing to do with the statement and everything to do with the target: in
    COBOL `Ledger-Q (a)` and `Ledger-Q1` through `Ledger-Q4` ARE THE SAME BYTES
    [copybooks/wsledger.cob:L31-L36], and in Python they are two separate
    attributes that do not alias.

    WHY BOTH VIEWS MUST BE WRITTEN. `acas_posting/records/gl_ledger.py` declares
    the two views and deliberately declines to synchronise them, because keeping
    a redefines in step would be behaviour in a record layout (rule R-3), and it
    records that the unbounded subscript "is reproduced in the `gl080` program
    module, which is where it belongs". The consequence is concrete and silent:
    the `acas005` handler binds its columns from the FOUR NAMED FIELDS, and its
    own view-alignment step refreshes the `occurs` view FROM those names and only
    on the read path. So a value written into the `occurs` view alone would never
    reach `GLLEDGER-REC` - phase 5's entire table effect would vanish with no
    error and no diagnostic. The COBOL statement names the `occurs` view, so this
    function writes the `occurs` view AND the named field the same bytes carry.

    The occurrence count is read from the descriptor's own `occurs`
    [copybooks/wsledger.cob:L36] and the attribute names from the declaration
    order of the named-field group, so neither the bound nor the four names is
    typed as a literal here.

    Args:
        st: The program's storage. `st.a` is the subscript and
            `st.ledger.ledger_balance` the sending field.

    Raises:
        ValueError: The subscript is outside the declared occurrence range. See
            anomaly A-2 and question Q-19 at the call site: this is the
            divergence being declared, not a validation being added.
        IndexError: Never, because the range is resolved before it is used.
    """
    occurs = _LEDGER_Q.occurs
    quarter_names = tuple(f.name for f in dataclasses.fields(LedgerQuarters))
    if st.a not in range(1, occurs + 1):
        raise ValueError(
            "gl080 quarter subscript out of range: "
            f"a={st.a!r} against Ledger-Q occurs {occurs} "
            "[general/gl080.cbl:L345], [copybooks/wsledger.cob:L36]. "
            "ANOMALY A-2 reproduced: the frozen source computes this subscript "
            "at [general/gl080.cbl:L328] and applies no bound. AMBIGUITY Q-19 - "
            "what the compiled program does here is a question for the oracle; "
            "no guard is added and nothing is silently corrected."
        )
    index = range(1, occurs + 1).index(st.a)

    stored = move.move(
        st.ledger.ledger_balance, _LEDGER_Q, sending_field=_LEDGER_BALANCE
    )

    # The `occurs` view the COBOL statement names.
    quarters = list(st.ledger.quarters_table.ledger_q)
    quarters[index] = stored
    st.ledger.quarters_table = LedgerQuartersTable(ledger_q=tuple(quarters))

    # The named field those same bytes carry, which is what the handler reads.
    setattr(st.ledger.quarters, quarter_names[index], stored)


def _gl080_main_loop_end(st: _Gl080Storage) -> None:
    """`loop-end.` - close the ledger and roll the quarter and the cycle.

    [general/gl080.cbl:L351-L363]. The post-loop block of the class-2 transfer
    at [general/gl080.cbl:L344], and the whole of the period rollover.

        351  loop-end.
        354      perform  GL-Nominal-Close.
        355      add      1  to  current-quarter.
        356      if       current-quarter = 5
        357               move  1  to  current-quarter.
        358      if       period = 3
        359         and   scycle > 12
        360               move 1 to scycle.
        361      if       period = 13
        362         and   scycle > 52
        363               move 1 to scycle.

    THE TWO CYCLE WRAPS ARE ASYMMETRIC AND BOTH ARE PRESERVED AS WRITTEN.
    Period 3 wraps above 12 and period 13 wraps above 52 - monthly and weekly
    accounting respectively - and no other period value wraps at all. So a
    period of, say, 6 increments `scycle` forever. That is the frozen behaviour
    and no third branch is added (rule R-3).

    Note also that the two wraps test `scycle` AFTER
    [general/gl080.cbl:L334] has already incremented it, so the comparison is
    against the NEW cycle number.

    Args:
        st: The program's storage. Four system-record fields are mutated here;
            see question Q-21.
    """
    # 354  perform  GL-Nominal-Close.
    facade.gl_nominal_close(st.nominal_ctx())

    # 355  add      1  to  current-quarter.
    # ANOMALY A-3's second notion of "current quarter", rotated here
    # independently of the subscript `a` that actually selected a field
    # [general/gl080.cbl:L345]. Reproduced deliberately per R-4; DO NOT FIX.
    # MUTATES THE SYSTEM RECORD - question Q-21.
    st.system.system_data_block.current_quarter = arithmetic.add_to(
        1,
        receiver_value=st.system.system_data_block.current_quarter,
        receiving=_CURRENT_QUARTER,
    )

    # 356  if       current-quarter = 5
    # 357           move  1  to  current-quarter.
    if arithmetic.compare(st.system.system_data_block.current_quarter, 5) == 0:
        st.system.system_data_block.current_quarter = move.move(
            1, _CURRENT_QUARTER
        )

    # 358  if       period = 3
    # 359     and   scycle > 12
    # 360           move 1 to scycle.
    if (
        arithmetic.compare(st.system.system_data_block.period, 3) == 0
        and arithmetic.compare(st.system.system_data_block.scycle, 12) > 0
    ):
        st.system.system_data_block.scycle = move.move(1, _SCYCLE)

    # 361  if       period = 13
    # 362     and   scycle > 52
    # 363           move 1 to scycle.
    if (
        arithmetic.compare(st.system.system_data_block.period, 13) == 0
        and arithmetic.compare(st.system.system_data_block.scycle, 52) > 0
    ):
        st.system.system_data_block.scycle = move.move(1, _SCYCLE)

    # Control FALLS THROUGH into `main-end.` [general/gl080.cbl:L365], which
    # `_gl080_main` calls next.


def _main_end(st: _Gl080Storage) -> None:
    """`main-end.` - the `goback`  [general/gl080.cbl:L365-L366].

        365  main-end.
        366       goback.

    THE PARAGRAPH'S ENTIRE BODY IS `goback.`, so this function's entire body is
    a `return`. A faithful one-to-one mapping and NOT a stub: `goback` in a
    called program returns control to its caller - `general/general.cbl`
    `load00.` [general/general.cbl:L711-L722] in a real run - leaving the
    linkage block exactly as it stands. It is present because rule R-5 requires
    a named function for every paragraph, and Agent Action Plan section 0.7.4
    C-4 states the reason verbatim: "every paragraph retains a named function
    even where its `GO TO` becomes a `continue`, a `break` or a `return`."

    Reached FOUR ways: by fall-through from `loop-end.`
    [general/gl080.cbl:L363], and by the three class-3 transfers at
    [general/gl080.cbl:L313], [general/gl080.cbl:L326] and
    [general/gl080.cbl:L332].

    NOTHING IS WRITTEN BACK TO THE LINKAGE. `gl080` never moves to
    `WS-Term-Code`, so the value a caller reads is the zero `load00.` set before
    the `CALL` [general/general.cbl:L714] - which is why `load09.`
    [general/general.cbl:L817-L820] carries no `= 5` gate where `load08.` does
    [general/general.cbl:L810-L811]. The system-record mutations this program
    made ARE visible to the caller, because that parameter is by reference;
    question Q-21 asks whether the caller then persists them.

    Args:
        st: The program's storage, unchanged by this paragraph.
    """
    # 366  goback.
    _LOG.debug(
        "gl080 returning to its caller; cycle %s, quarter %s",
        st.system.system_data_block.scycle,
        st.system.system_data_block.current_quarter,
    )
    return



# ---------------------------------------------------------------------------
#  gl080a section.   [general/gl080.cbl:L368]   -   PHASE 1, THE BATCH CHECK
# ---------------------------------------------------------------------------


def _gl080a(st: _Gl080Storage) -> None:
    """`gl080a section.` - phase 1's detector  [general/gl080.cbl:L368-L372].

    Walks the batch file for the current accounting cycle and raises the
    detector flag if ANY batch is not both closed and processed. Reads only:
    this section performs no write, no rewrite and no delete, so it has no
    database effect whatsoever.

        368  gl080a section.
        371      display  "Checking Batches" AT 2301 ...
        372      perform  GL-Batch-Open-Input.

    NOTE THE OPEN MODE. `GL-Batch-Open-Input` opens for input only
    [copybooks/Proc-ACAS-FH-Calls.cob], where `gl080b`
    [general/gl080.cbl:L415] and `gl080c` [general/gl080.cbl:L570] both open the
    same file for update. The read-only intent is declared in the open.

    Args:
        st: The program's storage. Sets `st.a` when a batch is outstanding.
    """
    # 371  display  "Checking Batches" AT 2301 ...
    _LOG.info("checking batches")

    # 372  perform  GL-Batch-Open-Input.       *> open  input  batch-file.
    facade.gl_batch_open_input(st.batch_ctx())

    # Fall-through into `loop.` [general/gl080.cbl:L374].
    _gl080a_loop(st)

    # 390  end-run.
    # The post-loop block of the class-2 transfer at [general/gl080.cbl:L379].
    _gl080a_end_run(st)

    # 395  main-exit.   exit section.
    _gl080a_main_exit(st)


def _gl080a_loop(st: _Gl080Storage) -> None:
    """`loop.` - one pass over the batch file  [general/gl080.cbl:L374-L388].

        374  loop.
        377      perform  GL-Batch-Read-Next.
        378      if       fs-reply = 10
        379               go to  end-run.
        381      if       bcycle not = scycle
        382               go to  loop.
        384      if       not status-closed
        385        and    not processed
        386               move  1  to  a.
        388      go       to loop.

    THE DETECTOR PREDICATE IS NOT `gl070`'S, and the difference is not cosmetic.
    `gl070` tests `if status-open` [general/gl070.cbl:L314] - one condition name
    over `Batch-Status` [copybooks/wsbatch.cob:L25-L27]. This section tests
    `not status-closed and not processed` - one condition name over
    `Batch-Status` NEGATED, conjoined with one over `Cleared-Status`
    [copybooks/wsbatch.cob:L29-L32] negated. `not status-closed` is true for any
    batch status other than 1, which is a strictly larger set than
    `status-open`; `not processed` is true for `waiting` and for `archived`
    alike. Copying `gl070`'s predicate here would change which batches abort the
    run.

    NOTE ALSO THAT THE FLAG IS NEVER LOWERED. Once any batch in the cycle raises
    it, the walk continues to the end of the file and the value stands. There is
    no early exit and no counter (rule R-3: none is added).

    Args:
        st: The program's storage.
    """
    while True:
        # 377  perform  GL-Batch-Read-Next.    *> read  batch-file  next record.
        facade.gl_batch_read_next(st.batch_ctx())

        # 378  if       fs-reply = 10
        if arithmetic.compare(st.file_access.fs_reply, _FS_AT_END) == 0:
            # 379  go to  end-run.
            # GO TO class 2 - the forward terminator. The post-loop work is
            # `_gl080a_end_run`, called by `_gl080a` straight after this returns.
            break

        # 381  if       bcycle not = scycle
        # 382           go to  loop.
        # THE ACCOUNTING-CYCLE FILTER, the first of three in this program - the
        # others are [general/gl080.cbl:L424] and [general/gl080.cbl:L579]. All
        # three are the identical single condition; unlike `gl070`, whose second
        # pass adds status conditions the first does not
        # [general/gl070.cbl:L460-L463], none of `gl080`'s three filters carries
        # a companion.
        if (
            arithmetic.compare(
                st.batch.bcycle, st.system.system_data_block.scycle
            )
            != 0
        ):
            # 382  go to  loop.
            # GO TO class 1 - the loop-back.
            continue

        # 384  if       not status-closed
        # 385    and    not processed
        # Both through the condition-name vocabulary: `88 Status-Closed value 1.`
        # [copybooks/wsbatch.cob:L27] and `88 Processed value 1.`
        # [copybooks/wsbatch.cob:L31]. Never a bare integer comparison - the
        # declared value sets belong to the copybook.
        if not condition_names.is_status_closed(
            st.batch.batch_status
        ) and not condition_names.is_processed(st.batch.cleared_status):
            # 386  move  1  to  a.
            # `a` IN ITS FIRST ROLE. Read back at [general/gl080.cbl:L308], and
            # still legible at [general/gl080.cbl:L324] where it fails both
            # conditions before being overwritten at [general/gl080.cbl:L328].
            st.a = move.move(1, _A)

        # 388  go       to loop.
        # GO TO class 1 - unconditional loop-back at the foot of the paragraph.
        continue


def _gl080a_end_run(st: _Gl080Storage) -> None:
    """`end-run.` - close the batch file  [general/gl080.cbl:L390-L393].

        390  end-run.
        393      perform  GL-Batch-Close.

    The post-loop block of [general/gl080.cbl:L379]. One statement, and losing
    it would leave the batch file open across the archiving or deletion walk
    that follows, both of which reopen it for update.

    Args:
        st: The program's storage.
    """
    # 393  perform  GL-Batch-Close.        *> close  batch-file.
    facade.gl_batch_close(st.batch_ctx())

    # Control FALLS THROUGH into `main-exit.` [general/gl080.cbl:L395].


def _gl080a_main_exit(st: _Gl080Storage) -> None:
    """`main-exit.   exit section.`  [general/gl080.cbl:L395].

    ONE OF SEVEN paragraphs named `main-exit.` in this program - the others are
    at [general/gl080.cbl:L442], [general/gl080.cbl:L516],
    [general/gl080.cbl:L559], [general/gl080.cbl:L597],
    [general/gl080.cbl:L625] and [general/gl080.cbl:L705] - which is why every
    function in this module is section-qualified. `exit section.` returns to the
    `perform` that entered the section, at [general/gl080.cbl:L307].

    Reached only by fall-through from `end-run.` [general/gl080.cbl:L393]; this
    section has no class-3 transfer.

    Args:
        st: The program's storage, unchanged by this paragraph.
    """
    # 395  exit section.
    _LOG.debug("gl080a complete; detector flag a=%s", st.a)
    return



# ---------------------------------------------------------------------------
#  gl080b section.   [general/gl080.cbl:L398]   -   PHASE 2, ARCHIVING
# ---------------------------------------------------------------------------


def _gl080b(st: _Gl080Storage) -> None:
    """`gl080b section.` - the archiving walk  [general/gl080.cbl:L398-L415].

        398  gl080b section.
        401      display  "Archiving.      Cycle - " at 2301 ...
        402      display  lin2 at 2330 ...
        403      display  "/ Batch - " at 2334 ...
        404      display  "/ Item  - " at 2352 ...
        406      perform  disk-change.  *>   set up o/p path
        408      if       a = 9
        409               go to  main-exit.
        411      open     extend  archive.
        412      if       fs-reply not = zero   *> just in case extend wont create
        413               close archive         *>  a non-existent file
        414               open output archive.
        415      perform  GL-Batch-Open.        *> open  i-o  batch-file.

    IDENTICAL DATABASE EFFECT TO `gl080c`. See the module docstring: both
    sections delete every posting of every batch in the cycle and stamp the
    batch header with the same three moves. The only difference is the flat
    archive rows, which are not a table.

    THE EXTEND-THEN-FALLBACK IDIOM [general/gl080.cbl:L411-L414] is the
    maintainer's own, and his comment explains it: try to append, and if the
    status is non-zero close and open for output instead, which creates the file
    and truncates anything in it. Both branches are reproduced. Neither has any
    table effect, so which one a run takes cannot show up in a state diff.

    ASYMMETRIC OPEN AND CLOSE OF THE POSTING FILE, the same shape `gl070`
    carries [general/gl070.cbl:L481], [general/gl070.cbl:L466]:
    `GL-Posting-Open` is INSIDE `arc-process` [general/gl080.cbl:L450] and
    `GL-Posting-Close` is in THIS section [general/gl080.cbl:L428]. Neither is
    moved to sit beside the other.

    Args:
        st: The program's storage.
    """
    # 401  display  "Archiving.      Cycle - " ...
    # 402  display  lin2 at 2330 ...            `lin2` was set at L291
    # 403  display  "/ Batch - " ...
    # 404  display  "/ Item  - " ...
    # Four displays that together build one progress line. One log record.
    _LOG.info("archiving, cycle %s", st.file_access.curs2_parts.lin2)

    # 406  perform  disk-change.
    _disk_change(st)

    # 408  if       a = 9
    # `a` IN ITS SECOND ROLE, read for the first time. `disk-change` is the ONLY
    # writer of the value 9 and this is the first of its two readers; the other
    # is [general/gl080.cbl:L324].
    if arithmetic.compare(st.a, 9) == 0:
        # 409  go to  main-exit.
        # GO TO class 3 - a transfer to this section's exit paragraph. THE WHOLE
        # ARCHIVING WALK IS SKIPPED: no archive file is opened, no batch is read,
        # no posting is deleted and no batch header is stamped. Combined with
        # [general/gl080.cbl:L324-L326], which the same value satisfies, one
        # keystroke suppresses every database write the program would have made.
        _gl080b_main_exit(st)
        return

    # 411  open     extend  archive.
    st.archive.open_extend()

    # 412  if       fs-reply not = zero   *> just in case extend wont create
    # 413           close archive         *>  a non-existent file
    # 414           open output archive.
    # The fallback the maintainer's own comment describes. `open output` CREATES
    # OR TRUNCATES, so an archive that was already present would lose its
    # previous contents on this path - which is the frozen behaviour and not
    # corrected here (rule R-3). No test of the fallback's own status is added;
    # the source tests nothing after L414.
    if arithmetic.compare(st.file_access.fs_reply, _FS_OK) != 0:
        st.archive.close()
        st.archive.open_output()

    # 415  perform  GL-Batch-Open.        *> open  i-o  batch-file.
    # OPENED FOR UPDATE, not for input as `gl080a` did, because this walk
    # rewrites every batch header it reads.
    facade.gl_batch_open(st.batch_ctx())

    # Fall-through into `loop.` [general/gl080.cbl:L417].
    _gl080b_loop(st)

    # 436  end-run.
    _gl080b_end_run(st)

    # 442  main-exit.   exit section.
    _gl080b_main_exit(st)


def _gl080b_loop(st: _Gl080Storage) -> None:
    """`loop.` - one batch per pass  [general/gl080.cbl:L417-L434].

        417  loop.
        420      perform  GL-Batch-Read-Next.
        421      if       fs-reply = 10
        422               go to  end-run.
        424      if       bcycle not = scycle
        425               go to  loop.
        427      perform  arc-process.
        428      perform  GL-Posting-Close.
        430      move     2         to  cleared-status.
        431      move     run-date  to  stored.
        432      move     zero      to  batch-start.
        433      perform  GL-Batch-Rewrite.
        434      go       to loop.

    THE STAMPING AT L430-L433 IS BYTE FOR BYTE THE SAME AS `gl080c`'S AT
    [general/gl080.cbl:L585-L589], which is what makes the two paths
    indistinguishable in a table dump. It differs from `gl072`'s parallel
    stamping [general/gl072.cbl:L375-L377] in three ways at once: the value is 2
    rather than 1, the date column is `stored` rather than `posted`, and there
    is a third move zeroing `batch-start` that `gl072` does not make.

    Args:
        st: The program's storage.
    """
    while True:
        # 420  perform  GL-Batch-Read-Next.
        facade.gl_batch_read_next(st.batch_ctx())

        # 421  if       fs-reply = 10
        if arithmetic.compare(st.file_access.fs_reply, _FS_AT_END) == 0:
            # 422  go to  end-run.
            # GO TO class 2 - the forward terminator; `_gl080b_end_run` closes
            # the archive and the batch file after this loop.
            break

        # 424  if       bcycle not = scycle
        # 425           go to  loop.
        # The second of the three accounting-cycle filters.
        if (
            arithmetic.compare(
                st.batch.bcycle, st.system.system_data_block.scycle
            )
            != 0
        ):
            # 425  go to  loop.
            # GO TO class 1.
            continue

        # 427  perform  arc-process.
        # Opens the posting file, explodes and archives every posting of this
        # batch, and deletes each one.
        _arc_process(st)

        # 428  perform  GL-Posting-Close.     *> close  posting-file.
        # THE OUTER HALF OF THE ASYMMETRIC PAIR - the open is inside
        # `arc-process` [general/gl080.cbl:L450]. Not moved.
        facade.gl_posting_close(st.posting_ctx())

        # 430  move     2         to  cleared-status.
        # `88 Archived value 2.` [copybooks/wsbatch.cob:L32]. The value comes
        # from the condition-name vocabulary rather than being typed as a bare
        # 2, so the declared value belongs to the copybook.
        st.batch.cleared_status = _archived_status()

        # 431  move     run-date  to  stored.
        # A CONTROLLED-CLOCK OBSERVABLE WRITTEN STRAIGHT INTO A TABLE COLUMN
        # (rule R-6). `Run-Date binary-long` [copybooks/wssystem.cob:L67] is read
        # from the system record that arrived through linkage; no ambient clock
        # is consulted here or anywhere below. This is a value the migration's
        # byte-identical-reruns test depends on being pinned.
        st.batch.dates.stored = move.move(
            st.system.system_data_block.run_date, _STORED
        )

        # 432  move     zero      to  batch-start.
        # THE MOVE `gl072` DOES NOT MAKE.
        st.batch.batch_start = move.move_figurative(move.ZERO, _BATCH_START)

        # 433  perform  GL-Batch-Rewrite.     *> rewrite  batch-record.
        facade.gl_batch_rewrite(st.batch_ctx())

        # 434  go       to loop.
        # GO TO class 1.
        continue


def _gl080b_end_run(st: _Gl080Storage) -> None:
    """`end-run.` - close the archive and the batch file.

    [general/gl080.cbl:L436-L440].

        436  end-run.
        439      close    archive.                *> close batch-file
        440      perform  GL-Batch-Close.

    Note the maintainer's own comment on L439, which names the wrong file. The
    statement closes the archive; the batch file is closed by the next line.

    Args:
        st: The program's storage.
    """
    # 439  close    archive.
    st.archive.close()

    # 440  perform  GL-Batch-Close.
    facade.gl_batch_close(st.batch_ctx())

    # Control FALLS THROUGH into `main-exit.` [general/gl080.cbl:L442].


def _gl080b_main_exit(st: _Gl080Storage) -> None:
    """`main-exit.   exit section.`  [general/gl080.cbl:L442].

    The second of the seven `main-exit.` paragraphs. Reached two ways: by the
    class-3 transfer at [general/gl080.cbl:L409] when the promoted `disk-change`
    option is 9, and by fall-through from `end-run.` [general/gl080.cbl:L440]
    otherwise.

    Args:
        st: The program's storage, unchanged by this paragraph.
    """
    # 442  exit section.
    _LOG.debug("gl080b complete; %s archive rows written", len(st.archive.rows))
    return


def _archived_status() -> int:
    """The value of `88 Archived value 2.`  [copybooks/wsbatch.cob:L32].

    `move 2 to cleared-status` [general/gl080.cbl:L430] and
    [general/gl080.cbl:L585] both write the literal the `Archived` condition
    name declares. Reading it out of the condition-name registry rather than
    typing 2 twice keeps the declared value in the copybook where it belongs and
    makes the two stamping sites provably identical.

    Returns:
        The single declared value of the condition name, stored into
        `Cleared-Status pic 9` [copybooks/wsbatch.cob:L29].
    """
    declared = condition_names.values_for("Archived")
    return move.move(declared[0], _CLEARED_STATUS)


# ---------------------------------------------------------------------------
#  arc-process section.   [general/gl080.cbl:L445]   -   THE ARCHIVE EXPLOSION
# ---------------------------------------------------------------------------


def _arc_process(st: _Gl080Storage) -> None:
    """`arc-process section.` - explode, archive and delete one batch's postings.

    [general/gl080.cbl:L445-L450].

        445  arc-process        section.
        448      display  WS-Batch-Nos at 2345 ...
        449      move     WS-Batch-Nos  to  arc-batch.
        450      perform  GL-Posting-Open.       *> open  i-o  posting-file.

    THE OPEN HALF OF THE ASYMMETRIC PAIR; the close is in the caller
    [general/gl080.cbl:L428].

    Note that `arc-batch` is set here from `WS-Batch-Nos` AND AGAIN inside the
    loop from `batch` [general/gl080.cbl:L465] - the posting record's own batch
    number, which the filter at [general/gl080.cbl:L460] has just proved equal to
    `WS-Batch-Nos`. So the second move is redundant given the filter, and both
    are reproduced.

    THIS SECTION HAS EXACTLY ONE EXIT, the class-3 transfer at
    [general/gl080.cbl:L457], which is why `_arc_process_main_exit` is called
    from inside the loop function and not from here.

    Args:
        st: The program's storage.
    """
    # 448  display  WS-Batch-Nos at 2345 ...
    _LOG.info("archiving batch %s", st.batch.ws_batch_key.ws_batch_nos)

    # 449  move     WS-Batch-Nos  to  arc-batch.
    st.archive.record.arc_batch = move.move(
        st.batch.ws_batch_key.ws_batch_nos,
        _ARC_BATCH,
        sending_field=_WS_BATCH_NOS,
    )

    # 450  perform  GL-Posting-Open.        *> open  i-o  posting-file.
    facade.gl_posting_open(st.posting_ctx())

    # Fall-through into `loop.` [general/gl080.cbl:L452]. That paragraph returns
    # only through [general/gl080.cbl:L457], which performs this section's exit
    # paragraph itself, so there is nothing to call after it here.
    _arc_process_loop(st)


def _arc_process_loop(st: _Gl080Storage) -> None:
    """`loop.` - the three-leg archive explosion, once per posting.

    [general/gl080.cbl:L452-L514]. Reads the posting file sequentially, skips
    anything that is not a live posting of this batch, writes THREE archive rows
    per posting, and deletes the posting.

        452  loop.
        455      perform  GL-Posting-Read-Next.
        456      if       fs-reply = 10
        457               go to  main-exit.
        459      if       WS-Post-Key = zero
        460         or    batch  not = WS-Batch-Nos
        461               go to  loop.
        463      display  post-number at 2364 ...
        465-474  the common header and LEG ONE's four account fields
        476-479  leg one's amount, taking the tax in on the CR side
        481      write    arc-trans-record.
        483-486  LEG TWO swaps all four account fields
        488-491  leg two's amount, taking the tax in on the DR side
        493      multiply arc-amount  by  -1  giving  arc-amount.
        495      write    arc-trans-record.
        497      if       vat-ac of WS-Posting-Record equal  zero
        498            or vat-amount = zero
        499               go to  by-pass.
        501-503  LEG THREE's tax account, centre and amount
        505-506  negated only when the tax sits on the CR side
        508      write    arc-trans-record.

    HOW THIS DIFFERS FROM `gl070`'S EXPLOSION, WHICH IT OTHERWISE MIRRORS

    1.  THE TAX-SUPPRESSION TRANSFER GOES SOMEWHERE ELSE, AND IT MATTERS.
        `gl070` writes `go to loop` [general/gl070.cbl:L523], abandoning the
        record entirely. This section writes `go to by-pass`
        [general/gl080.cbl:L499], AND `by-pass` STILL PERFORMS
        `GL-Posting-Delete` [general/gl080.cbl:L513]. So a posting with no tax
        is archived in two legs AND STILL DELETED. Reusing `gl070`'s shape here
        would leave every tax-free posting undeleted.
    2.  LEG TWO SWAPS FOUR FIELDS, not two. `pre-trans-record`
        [general/gl070.cbl:L108-L116] carries no contra pair, so `gl070` has
        only `pre-ac` and `pre-pc` to overwrite. Here `arc-ac`/`arc-pc` and
        `arc-c-ac`/`arc-c-pc` exchange places [general/gl080.cbl:L483-L486].
    3.  THE TWO GUARDS ARE ONE STATEMENT, not two. `gl070` writes them as
        separate `if`s [general/gl070.cbl:L490-L493]; here they are one `if`
        with an `or` [general/gl080.cbl:L459-L461]. Same effect, and the frozen
        form is followed.

    WHAT IS THE SAME: leg one tests the CR side and leg two tests the DR side -
    the OPPOSITE side, deliberately; only leg two is negated unconditionally;
    leg three is negated only on the CR side; and the three writes share ONE
    record area, so each must capture an independent copy.

    Args:
        st: The program's storage.
    """
    while True:
        # 455  perform  GL-Posting-Read-Next.
        facade.gl_posting_read_next(st.posting_ctx())

        # 456  if       fs-reply = 10
        if arithmetic.compare(st.file_access.fs_reply, _FS_AT_END) == 0:
            # 457  go to  main-exit.
            # GO TO class 3 - a transfer to this section's exit paragraph, which
            # is `exit section.` [general/gl080.cbl:L516]. Reproduced as a call
            # to that paragraph followed by a return. THIS IS THE SECTION'S ONLY
            # EXIT, which is why `_arc_process` does not call the exit paragraph
            # again after this function returns.
            _arc_process_main_exit(st)
            return

        # 459  if       WS-Post-Key = zero
        # 460     or    batch  not = WS-Batch-Nos
        # 461           go to  loop.
        #
        # `WS-Post-Key` [copybooks/wspost.cob:L14] is a GROUP of two `pic 9(5)`
        # items, `Batch` and `Post-Number`, so `= zero` holds exactly when both
        # are zero. The one COBOL condition is therefore expressed over the
        # group's two declared members; this adds no test the source does not
        # make, it decomposes one test over the items it is written against.
        if (
            arithmetic.compare(st.posting.ws_post_key.batch, 0) == 0
            and arithmetic.compare(st.posting.ws_post_key.post_number, 0) == 0
        ) or arithmetic.compare(
            st.posting.ws_post_key.batch, st.batch.ws_batch_key.ws_batch_nos
        ) != 0:
            # 461  go to  loop.
            # GO TO class 1. Note that a posting skipped here is NOT deleted -
            # control never reaches `by-pass` - so a posting belonging to another
            # batch survives this walk untouched.
            continue

        # 463  display  post-number at 2364 ...
        _LOG.debug("archiving posting %s", st.posting.ws_post_key.post_number)

        # 465  move     batch        to  arc-batch.
        # 466  move     post-number  to  arc-post.
        # 467  move     post-code in WS-Posting-Record    to  arc-code.
        # 468  move     post-date    to  arc-date.
        # 469  move     post-legend  to  arc-legend.
        #
        # THE COMMON HEADER. These five fields are set ONCE per posting and
        # CARRY OVER into legs two and three unchanged - only the account fields
        # and the amount are rewritten below.
        record = st.archive.record
        record.arc_batch = move.move(
            st.posting.ws_post_key.batch, _ARC_BATCH, sending_field=_POST_BATCH
        )
        record.arc_post = move.move(
            st.posting.ws_post_key.post_number,
            _ARC_POST,
            sending_field=_POST_NUMBER,
        )
        # ANOMALY A-21 [general/gl080.cbl:L467] - a QUALIFIED reference forced by
        # a field-name collision across three posting copybooks. `Post-Code` is
        # declared in `copybooks/wspost.cob` and elsewhere, so the frozen source
        # must write `post-code in WS-Posting-Record` to say which one it means.
        # Note the spelling: `in` here, `of` at the other two sites. Reproduced
        # deliberately per R-4; DO NOT FIX. In Python the qualification is
        # inherent - the attribute is reached through the record object - so the
        # anomaly survives as this citation.
        record.arc_code = move.move(
            st.posting.post_code, _ARC_CODE, sending_field=_POST_CODE
        )
        record.arc_date = move.move(
            st.posting.post_date, _ARC_DATE, sending_field=_POST_DATE
        )
        record.arc_legend = move.move(
            st.posting.post_legend, _ARC_LEGEND, sending_field=_POST_LEGEND
        )

        # 471  move     post-dr      to  arc-ac.
        # 472  move     dr-pc        to  arc-pc.
        # 473  move     post-cr      to  arc-c-ac.
        # 474  move     cr-pc        to  arc-c-pc.
        # LEG ONE: the debit account leads, the credit account is the contra.
        record.arc_ac = move.move(
            st.posting.post_dr, _ARC_AC, sending_field=_POST_DR
        )
        record.arc_pc = move.move(
            st.posting.dr_pc, _ARC_PC, sending_field=_DR_PC
        )
        record.arc_c_ac = move.move(
            st.posting.post_cr, _ARC_C_AC, sending_field=_POST_CR
        )
        record.arc_c_pc = move.move(
            st.posting.cr_pc, _ARC_C_PC, sending_field=_CR_PC
        )

        # 476  if       post-vat-side = "CR"
        # 477           add  post-amount  vat-amount  giving  arc-amount
        # 478  else
        # 479           move post-amount  to  arc-amount.
        #
        # LEG ONE TESTS THE CR SIDE. `Post-Vat-Side pic xx`
        # [copybooks/wspost.cob:L27] is a two-character code compared against a
        # literal, not a condition name - the frozen source declares no
        # `88`-level over it, so none is invented here. The variadic
        # `ADD ... GIVING` sums at intermediate precision and stores ONCE, and
        # the store truncates.
        if st.posting.post_vat_side == "CR":
            record.arc_amount = arithmetic.add_giving(
                st.posting.post_amount,
                st.posting.vat_amount,
                receiving=_ARC_AMOUNT,
            )
        else:
            record.arc_amount = move.move(
                st.posting.post_amount, _ARC_AMOUNT, sending_field=_POST_AMOUNT
            )

        # 481  write    arc-trans-record.
        # THE FIRST OF THREE WRITES OF ONE RECORD AREA. Each appends an
        # independent copy; see `_ArchiveFile.write`.
        st.archive.write()

        # 483  move     post-cr      to  arc-ac.
        # 484  move     cr-pc        to  arc-pc.
        # 485  move     post-dr      to  arc-c-ac.
        # 486  move     dr-pc        to  arc-c-pc.
        # LEG TWO: ALL FOUR ACCOUNT FIELDS SWAP. The credit account now leads and
        # the debit account is the contra - the mirror image of leg one, which is
        # what makes the pair a double entry.
        record.arc_ac = move.move(
            st.posting.post_cr, _ARC_AC, sending_field=_POST_CR
        )
        record.arc_pc = move.move(
            st.posting.cr_pc, _ARC_PC, sending_field=_CR_PC
        )
        record.arc_c_ac = move.move(
            st.posting.post_dr, _ARC_C_AC, sending_field=_POST_DR
        )
        record.arc_c_pc = move.move(
            st.posting.dr_pc, _ARC_C_PC, sending_field=_DR_PC
        )

        # 488  if       post-vat-side = "DR"
        # 489           add  post-amount  vat-amount  giving  arc-amount
        # 490  else
        # 491           move post-amount  to  arc-amount.
        #
        # LEG TWO TESTS THE OPPOSITE SIDE TO LEG ONE - "DR" where leg one tested
        # "CR". So the tax is folded into whichever leg it belongs to and into
        # that leg only. The asymmetry is deliberate and matches
        # [general/gl070.cbl:L503] against [general/gl070.cbl:L512].
        if st.posting.post_vat_side == "DR":
            record.arc_amount = arithmetic.add_giving(
                st.posting.post_amount,
                st.posting.vat_amount,
                receiving=_ARC_AMOUNT,
            )
        else:
            record.arc_amount = move.move(
                st.posting.post_amount, _ARC_AMOUNT, sending_field=_POST_AMOUNT
            )

        # 493  multiply arc-amount  by  -1  giving  arc-amount.
        # THE FIRST ARCHIVE SIGN FLIP [general/gl080.cbl:L493], named explicitly
        # in Agent Action Plan sections 0.4.1.2 and 0.6.1 as behaviour to
        # preserve. UNCONDITIONAL: every leg-two row is negated, which is what
        # makes the debit and credit legs sum to zero. Truncating store, as every
        # store in this program other than [general/gl080.cbl:L328] is.
        record.arc_amount = arithmetic.multiply_by_giving(
            record.arc_amount, -1, _ARC_AMOUNT
        )

        # 495  write    arc-trans-record.
        st.archive.write()

        # 497  if       vat-ac of WS-Posting-Record equal  zero
        # 498        or vat-amount = zero
        # 499           go to  by-pass.
        #
        # ANOMALY A-21 [general/gl080.cbl:L497] - the second of three qualified
        # references, and note the spelling changes: `of` here where
        # [general/gl080.cbl:L467] used `in`. Note too that the frozen source
        # writes the relation as `equal zero` on this line and `= zero` on the
        # next, two spellings of one operator in one statement. Reproduced
        # deliberately per R-4; DO NOT FIX.
        if (
            arithmetic.compare(st.posting.vat_ac, 0) == 0
            or arithmetic.compare(st.posting.vat_amount, 0) == 0
        ):
            # 499  go to  by-pass.
            #
            # GO TO class 4 - SIBLING RE-DISPATCH, and the equivalence proof
            # matters here because the target is not an exit.
            #
            # PROOF. `by-pass.` [general/gl080.cbl:L510] holds exactly two
            # statements: `perform GL-Posting-Delete.`
            # [general/gl080.cbl:L513] and `go to loop.`
            # [general/gl080.cbl:L514]. So the transfer means "skip leg three,
            # then delete the posting, then read the next one". Calling
            # `_arc_process_by_pass` performs the delete and nothing else, and
            # the `continue` that follows reproduces its `go to loop`. The two
            # statements execute in that order and control arrives at exactly the
            # same place it would in the compiled program.
            #
            # AND THIS IS WHERE `gl070` DIVERGES. Its equivalent transfer is
            # `go to loop` [general/gl070.cbl:L523], which abandons the record
            # WITHOUT deleting it, because `gl070` deletes nothing at all. Here
            # the delete still happens, so a posting carrying no tax is archived
            # in two legs and removed from the table. Reusing `gl070`'s shape
            # would leave every tax-free posting behind.
            _arc_process_by_pass(st)
            continue

        # 501  move     vat-ac of WS-Posting-Record  to  arc-ac.
        # 502  move     vat-pc     to  arc-pc.
        # 503  move     vat-amount to  arc-amount.
        #
        # LEG THREE, the tax leg. ANOMALY A-21 [general/gl080.cbl:L501] - the
        # third qualified reference, spelled `of` again. Reproduced deliberately
        # per R-4; DO NOT FIX.
        #
        # NOTE WHAT IS *NOT* SET HERE: `arc-c-ac` and `arc-c-pc` keep LEG TWO's
        # values, which are the debit account and centre. The tax row therefore
        # carries the debit account as its contra whichever side the tax sits on.
        # Frozen behaviour; no fourth and fifth move is added.
        record.arc_ac = move.move(
            st.posting.vat_ac, _ARC_AC, sending_field=_VAT_AC
        )
        record.arc_pc = move.move(
            st.posting.vat_pc, _ARC_PC, sending_field=_VAT_PC
        )
        record.arc_amount = move.move(
            st.posting.vat_amount, _ARC_AMOUNT, sending_field=_VAT_AMOUNT
        )

        # 505  if       post-vat-side = "CR"
        # 506           multiply  arc-amount  by  -1 giving arc-amount.
        # THE SECOND ARCHIVE SIGN FLIP [general/gl080.cbl:L506], also named in
        # Agent Action Plan sections 0.4.1.2 and 0.6.1. CONDITIONAL, unlike
        # [general/gl080.cbl:L493]: the tax row is negated only when the tax sits
        # on the credit side.
        if st.posting.post_vat_side == "CR":
            record.arc_amount = arithmetic.multiply_by_giving(
                record.arc_amount, -1, _ARC_AMOUNT
            )

        # 508  write    arc-trans-record.
        st.archive.write()

        # Control FALLS THROUGH into `by-pass.` [general/gl080.cbl:L510] - the
        # same paragraph the class-4 transfer above jumps to. Called explicitly
        # so the fall-through is visible rather than implied.
        _arc_process_by_pass(st)

        # 514  go       to loop.
        # GO TO class 1 - `by-pass`'s own loop-back, reached here by
        # fall-through.
        continue


def _arc_process_by_pass(st: _Gl080Storage) -> None:
    """`by-pass.` - delete the posting  [general/gl080.cbl:L510-L513].

        510  by-pass.
        513      perform  GL-Posting-Delete.     *> delete  posting-file  record.

    THE ONE STATEMENT IN THIS SECTION THAT REACHES A TABLE, and `gl080` is the
    only in-scope program that performs this verb. It runs for EVERY posting of
    the batch that passed the filter at [general/gl080.cbl:L459-L461] -
    whether or not that posting carried tax, because the tax-suppression
    transfer at [general/gl080.cbl:L499] targets this paragraph rather than the
    loop head.

    The paragraph's second statement, `go to loop.` [general/gl080.cbl:L514], is
    reproduced by the `continue` at each of this function's two call sites
    rather than inside it, because a function cannot continue its caller's loop.

    NO STATUS TEST FOLLOWS THE DELETE. The frozen source tests nothing after
    [general/gl080.cbl:L513], so nothing is tested here (rule R-3) - a delete
    that failed would be silent and the batch would still be stamped as
    archived.

    Args:
        st: The program's storage.
    """
    # 513  perform  GL-Posting-Delete.
    facade.gl_posting_delete(st.posting_ctx())


def _arc_process_main_exit(st: _Gl080Storage) -> None:
    """`main-exit.   exit section.`  [general/gl080.cbl:L516].

    The third of the seven `main-exit.` paragraphs. Reached ONLY by the class-3
    transfer at [general/gl080.cbl:L457]; this section has no fall-through path
    to its exit, because `by-pass` always transfers back to the loop head.

    Args:
        st: The program's storage, unchanged by this paragraph.
    """
    # 516  exit section.
    _LOG.debug(
        "arc-process complete for batch %s", st.batch.ws_batch_key.ws_batch_nos
    )
    return



# ---------------------------------------------------------------------------
#  disk-change section.   [general/gl080.cbl:L519]   -   THE ARCHIVE PATH
# ---------------------------------------------------------------------------


def _disk_change(st: _Gl080Storage) -> None:
    """`disk-change section.` - build the archive path  [general/gl080.cbl:L519].

    Called from `gl080b` [general/gl080.cbl:L406] and from nowhere else, so
    everything below happens on the archiving path only.

        519  disk-change        section.
        530      move     space to Arg-Test.        *> this lot looks wrong !!!!!
        531      string   file-24        delimited by space   *> spaces
        532               "archives"     delimited by size
        533               file-defs-os-delimiter
        534                              delimited by size
        535                 file-2      delimited by space  *> archive.dat
        536                             into Arg-Test.
        537      move     Arg-Test to file-2.
        539      display  GL085 at 1201 ...
        540      display  Gl084 at 1301 ...

    AMBIGUITY Q-22 - THE MAINTAINER FLAGGED THIS HIMSELF, INLINE:
    `*> this lot looks wrong !!!!!` [general/gl080.cbl:L530]. The same
    CHARACTER of finding as anomaly A-17 [sales/sl060.cbl:L1173], where he
    marked an unexplained move with a question mark, though this is not one of
    the register's twenty-two entries. Reproduced exactly as written, and the
    reason it looks wrong was MEASURED against the package's own record
    defaults rather than reasoned about:

        `file-24`                  [copybooks/file24.cob:L1]  532 SPACES
        "archives"                 the literal                8 characters
        `File-Defs-os-Delimiter`   [copybooks/wsnames.cob]    ONE SPACE
        `file-2`                   [copybooks/file02.cob:L1]  "archive.dat"

    `DELIMITED BY SPACE` on an item that is ALL spaces contributes nothing, so
    the first source vanishes - which the maintainer's own `*> spaces` comment on
    L531 acknowledges. The operating-system delimiter then contributes a SPACE
    where a directory separator belongs. The result is "archives archive.dat":
    a single path segment with a space in the middle of it, not a directory and a
    file name. What the compiled program actually produces, and therefore where
    the archive rows land, is the open question.

    AND A CORRECTION TO A CLAIM MADE ABOUT [general/gl080.cbl:L537]. That `MOVE`
    is described elsewhere as "a truncating MOVE across very unequal widths".
    MEASURED, IT PADS: `Arg-Test` is `pic x(525)` [general/gl080.cbl:L187] and
    `file-2` is `pic x(532)` [copybooks/file02.cob:L1], so the receiver is SEVEN
    CHARACTERS WIDER than the sender and the move space-fills rather than
    truncating. Nothing is lost at that statement.

    NOTE ALSO that `file-2` is BOTH the fourth source of the `STRING` and the
    destination of the `MOVE` that follows it, so a second call would fold the
    previous result back into itself and grow the path. This section is called
    once per run.

    Args:
        st: The program's storage. `st.a`, `st.file_defs.file_defs_a.file_2` and
            the local `Arg-Test` are written here.
    """
    # 530  move     space to Arg-Test.
    # NOT a clear-to-nothing: it fills all 525 characters with spaces, which is
    # what makes the `STRING` below overwrite from position 1 rather than append.
    arg_test = move.move_figurative(move.SPACE, _ARG_TEST)

    # 531  string   file-24        delimited by space   *> spaces
    # 532           "archives"     delimited by size
    # 533           file-defs-os-delimiter
    # 534                          delimited by size
    # 535             file-2      delimited by space  *> archive.dat
    # 536                         into Arg-Test.
    #
    # FOUR SOURCES WITH MIXED DELIMITERS - SPACE, SIZE, SIZE, SPACE in that
    # order - so the delimiter is given per source rather than once for the
    # statement. NO `POINTER` PHRASE is written on L531, so the receiver is
    # filled from position 1, which is `string_into`'s default.
    #
    # Delegated whole (Agent Action Plan section 0.3.1): the truncation at the
    # receiver's edge, the delimiter scan and the pointer arithmetic are COBOL
    # language semantics. Nothing here concatenates, trims or slices.
    arg_test, _pointer = move.string_into(
        arg_test,
        (
            (st.file_defs.file_defs_a.file_24, move.DELIMITED_BY_SPACE),
            ("archives", move.DELIMITED_BY_SIZE),
            (st.file_defs.file_defs_os_delimiter, move.DELIMITED_BY_SIZE),
            (st.file_defs.file_defs_a.file_2, move.DELIMITED_BY_SPACE),
        ),
    )

    # 537  move     Arg-Test to file-2.
    # Pads to 532; see the correction in this function's docstring.
    st.file_defs.file_defs_a.file_2 = move.move(
        arg_test, _FILE_2, sending_field=_ARG_TEST
    )

    # 539  display  GL085 at 1201 ...
    # 540  display  Gl084 at 1301 ...
    # `GL084` [general/gl080.cbl:L252] and `GL085` [general/gl080.cbl:L253].
    _LOG.info("archive path built as %r", st.file_defs.file_defs_a.file_2)

    # Fall-through into `accept-option.` [general/gl080.cbl:L542].
    if _disk_change_accept_option(st):
        # 547  go to  main-exit.
        # GO TO class 3, raised inside `accept-option` and carried out here. The
        # option value 9 has already been stored into `a`, which
        # [general/gl080.cbl:L408] and [general/gl080.cbl:L324] both read.
        _disk_change_main_exit(st)
        return

    # 559  main-exit.   exit section.
    _disk_change_main_exit(st)


def _disk_change_accept_option(st: _Gl080Storage) -> bool:
    """`accept-option.` - the option and the path edit.

    [general/gl080.cbl:L542-L557].

        542  accept-option.
        545      accept   a at 1369.
        546      if       a = 9
        547               go to  main-exit.
        548      if       a  not = zero
        549               go to  accept-option.
        553      display  "Current path/name is :" at 1401 ...
        554      display  file-2             at 1501 ...
        555      accept   file-2             at 1501 with ... update.
        556      if       file-2 (1:1) = space
        557               go to accept-option.

    TWO PROMPTS, TWO DIFFERENT TREATMENTS, BOTH DECIDED BY WHETHER THEY GATE A
    DATABASE WRITE (Agent Action Plan section 0.3.4).

    [general/gl080.cbl:L545] GATES DATABASE WRITES, and it is the clearest such
    prompt in the General Ledger folder. The value it accepts lands in `a`, and
    the value 9 is then read TWICE - at [general/gl080.cbl:L408], which skips the
    entire archiving walk, and at [general/gl080.cbl:L324], which skips the
    entire end-of-period section. One keystroke therefore suppresses every batch
    stamp, every posting delete, the ledger-quarter rollover and the cycle
    increment. Promoted to the `disk_change_option` parameter with the COBOL's
    proceed answer, zero, as the default.

    [general/gl080.cbl:L555] gates only WHERE THE FLAT ARCHIVE FILE IS WRITTEN.
    That file is not a table, so this prompt has no table effect at all.
    Promoted to `archive_path_override`, defaulting to None, which keeps the
    path [general/gl080.cbl:L537] computed.

    THE TWO RETRY LOOPS ARE DROPPED AND THEIR TRANSFERS ARE NOT. Agent Action
    Plan section 0.4.2 puts interactive retry targets outside the migrated
    surface "except where one gates a database write, in which case it is treated
    as Class 4". `go to accept-option` at [general/gl080.cbl:L549] re-prompts
    when the option is neither 9 nor zero, and at [general/gl080.cbl:L557] when
    the edited path starts with a space; both exist only to make a terminal
    operator try again, and a parameter cannot be retried. So the LOOPS go and
    the DECISIONS stay: an option of 9 still transfers to the section exit, and a
    path whose first character is a space is still rejected - by declining the
    override and keeping the computed path, which is what the operator would
    have been left with.

    Args:
        st: The program's storage. Writes `st.a`, and `file-2` when the override
            is accepted.

    Returns:
        True when the class-3 transfer at [general/gl080.cbl:L547] was taken -
        that is, when the option is 9 - and False when control falls through to
        the section exit. A Python function cannot transfer into its caller, so
        the answer is returned and `_disk_change` carries out the transfer.
    """
    # 545  accept   a at 1369.
    # `a` IN ITS SECOND ROLE. The promoted value is stored through the field's
    # own descriptor, so a value outside `pic 99` is truncated exactly as the
    # screen field would truncate it.
    st.a = move.move(st.disk_change_option, _A)

    # 546  if       a = 9
    if arithmetic.compare(st.a, 9) == 0:
        # 547  go to  main-exit.
        # GO TO class 3, carried out by the caller.
        _LOG.info(
            "archiving declined at the disk-change option; no batch will be "
            "stamped and no posting deleted"
        )
        return True

    # 548  if       a  not = zero
    # 549           go to  accept-option.
    # GO TO class 1 over an INTERACTIVE RETRY. The loop is dropped with the
    # prompt; what it guaranteed - that control leaves this paragraph only when
    # the option is 9 or zero - is preserved by the promoted parameter, whose
    # only two meaningful values are those two. A third value would have
    # re-prompted forever with no database effect, so no branch is added for it
    # (rule R-3) and none can be reached.
    if arithmetic.compare(st.a, 0) != 0:
        _LOG.warning(
            "disk-change option %s is neither 0 nor 9; the frozen source "
            "re-prompts, so the value is carried forward unchanged",
            st.a,
        )

    # 553  display  "Current path/name is :" at 1401 ...
    # 554  display  file-2             at 1501 ...
    _LOG.info("current archive path is %r", st.file_defs.file_defs_a.file_2)

    # 555  accept   file-2             at 1501 with ... update.
    # 556  if       file-2 (1:1) = space
    # 557           go to accept-option.
    #
    # The `with update` phrase means the field is presented holding its current
    # value and the operator edits it, which is why declining the override keeps
    # the computed path rather than blanking it.
    if st.archive_path_override is not None:
        candidate = move.move(
            st.archive_path_override, _FILE_2, sending_field=_FILE_2
        )
        # 556  if       file-2 (1:1) = space
        # ONE-BASED reference modification, delegated. Never a Python slice.
        if move.ref_mod(candidate, 1, 1) == " ":
            # 557  go to accept-option.
            # GO TO class 1 over an interactive retry. The re-prompt is dropped;
            # the REJECTION is kept, and rejecting means the computed path
            # stands. No table is affected either way.
            _LOG.warning(
                "archive path override rejected: its first character is a "
                "space [general/gl080.cbl:L556]; keeping %r",
                st.file_defs.file_defs_a.file_2,
            )
        else:
            st.file_defs.file_defs_a.file_2 = candidate
            _LOG.info("archive path overridden to %r", candidate)

    # Control FALLS THROUGH into `main-exit.` [general/gl080.cbl:L559].
    return False


def _disk_change_main_exit(st: _Gl080Storage) -> None:
    """`main-exit.   exit section.`  [general/gl080.cbl:L559].

    The fourth of the seven `main-exit.` paragraphs. Reached two ways: by the
    class-3 transfer at [general/gl080.cbl:L547] when the option is 9, and by
    fall-through from [general/gl080.cbl:L557] otherwise.

    Args:
        st: The program's storage, unchanged by this paragraph.
    """
    # 559  exit section.
    _LOG.debug("disk-change complete; option a=%s", st.a)
    return



# ---------------------------------------------------------------------------
#  gl080c section.   [general/gl080.cbl:L562]   -   PHASE 3, TRANSACTION
#                                                   DELETION
# ---------------------------------------------------------------------------


def _gl080c(st: _Gl080Storage) -> None:
    """`gl080c section.` - Phase 3, delete without archiving.

    [general/gl080.cbl:L562-L597]. The `else` branch of the phase driver's
    `if archiving` [general/gl080.cbl:L315-L320]: performed when the system
    record's archive switch is not set, so the cycle's postings are discarded
    rather than written out first.

        562  gl080c section.
        565      display  "Deleting.       Cycle - " at 2301 ...
        566      display  lin2 at 2330 ...
        567      display  "/ Batch - " at 2334 ...
        568      display  "/ Item  - " at 2352 ...
        570      perform  GL-Batch-Open.        *> open  i-o  batch-file.

    THIS SECTION AND `gl080b` HAVE IDENTICAL DATABASE EFFECTS.

    Both walk the batch file filtering on the accounting cycle, delete every
    posting of each matching batch, stamp the batch `Archived` with the run date
    and a zeroed start, and rewrite it. The ONLY difference is that `arc-process`
    additionally appends rows to the flat archive sequence - and that sequence is
    not a schema table, so it appears in no table dump. IN AN ORDERING-NORMALISED
    STATE DIFF THE TWO PATHS ARE INDISTINGUISHABLE. That is the key fact for the
    period-end-totals scenario, and it is why the stamping below is performed by
    the SAME two helpers `gl080b` uses rather than by a second copy of the
    literals.

    IT IS ALSO SHORTER THAN `gl080b` BY EXACTLY THE ARCHIVE. There is no
    `disk-change` call, no promoted option, no `open extend` and no
    `close archive`; the batch walk is otherwise line-for-line the same.

    Args:
        st: The program's storage.
    """
    # 565  display  "Deleting.       Cycle - " at 2301 ...
    # 566  display  lin2 at 2330 ...            `lin2` was set at L291
    # 567  display  "/ Batch - " at 2334 ...
    # 568  display  "/ Item  - " at 2352 ...
    # Screen furniture with no database effect, so log records (Agent Action
    # Plan section 0.3.4). They must not alter control flow, and they do not.
    _LOG.info(
        "Phase - 3.  Transaction Deletion: deleting cycle %s",
        st.file_access.curs2_parts.lin2,
    )

    # 570  perform  GL-Batch-Open.        *> open  i-o  batch-file.
    # `GL-Batch-Open.` [copybooks/Proc-ACAS-FH-Calls.cob:L419] sets the function
    # to open and the access to i-o, then performs `acas007`. NOTE THAT `gl080b`
    # OPENS THE SAME FILE THE SAME WAY [general/gl080.cbl:L415] - the two paths
    # differ in what they do with the postings, not in how they reach the batch.
    facade.gl_batch_open(st.batch_ctx())

    # Fall-through into `loop.` [general/gl080.cbl:L572].
    _gl080c_loop(st)

    # 592  end-run.
    # Reached by the class-2 transfer at [general/gl080.cbl:L577].
    _gl080c_end_run(st)

    # 597  main-exit.   exit section.
    _gl080c_main_exit(st)


def _gl080c_loop(st: _Gl080Storage) -> None:
    """`loop.` - one batch per pass  [general/gl080.cbl:L572-L590].

        572  loop.
        575      perform  GL-Batch-Read-Next.
        576      if       fs-reply = 10
        577               go to  end-run.
        579      if       bcycle not = scycle
        580               go to  loop.
        582      perform  del-process.
        583      perform  GL-Posting-Close.
        585      move     2         to  cleared-status.
        586      move     run-date  to  stored.
        587      move     zero      to  batch-start.
        589      perform  GL-Batch-Rewrite.
        590      go       to loop.

    THE STAMPING AT L585-L589 IS THE SAME THREE MOVES AND THE SAME REWRITE AS
    [general/gl080.cbl:L430-L433], in the same order, against the same columns.
    The Agent Action Plan describes this stamping but supplies no locators for
    it; the measured lines are L585 through L589. Confirming the identity is the
    whole point of Headline Risk 6, so both sites go through `_archived_status()`
    and the same `run-date` read.

    Args:
        st: The program's storage.
    """
    while True:
        # 575  perform  GL-Batch-Read-Next.
        facade.gl_batch_read_next(st.batch_ctx())

        # 576  if       fs-reply = 10
        if arithmetic.compare(st.file_access.fs_reply, _FS_AT_END) == 0:
            # 577  go to  end-run.
            # GO TO class 2 - the forward terminator. `_gl080c_end_run` closes
            # the batch file AFTER this loop; placing that close inside the loop
            # would close on the first batch, and dropping it would leave the
            # file open. Agent Action Plan section 0.6.3 on class 2: the
            # transformation is `break` PLUS faithful placement of the work that
            # follows the label, not `break` alone.
            break

        # 579  if       bcycle not = scycle
        # 580           go to  loop.
        # THE THIRD OF THE THREE ACCOUNTING-CYCLE FILTERS in this program - the
        # first is `gl080a`'s [general/gl080.cbl:L381], the second `gl080b`'s
        # [general/gl080.cbl:L424]. All three compare the same two fields;
        # collapsing them into one walk would change which batches each phase
        # sees, so all three stay.
        if (
            arithmetic.compare(
                st.batch.bcycle, st.system.system_data_block.scycle
            )
            != 0
        ):
            # 580  go to  loop.
            # GO TO class 1.
            continue

        # 582  perform  del-process.
        # Opens the posting file and deletes every posting of this batch.
        _del_process(st)

        # 583  perform  GL-Posting-Close.     *> close  posting-file.
        # THE OUTER HALF OF THE ASYMMETRIC PAIR, exactly as in `gl080b`
        # [general/gl080.cbl:L428] - the matching open is inside `del-process`
        # [general/gl080.cbl:L607]. Not moved into the section that opens it.
        facade.gl_posting_close(st.posting_ctx())

        # 585  move     2         to  cleared-status.
        # `88 Archived value 2.` [copybooks/wsbatch.cob:L32], read through the
        # SAME helper `gl080b` uses at [general/gl080.cbl:L430].
        st.batch.cleared_status = _archived_status()

        # 586  move     run-date  to  stored.
        # A CONTROLLED-CLOCK OBSERVABLE WRITTEN INTO A TABLE COLUMN (rule R-6),
        # read from the system record that arrived through linkage.
        # `Run-Date binary-long` [copybooks/wssystem.cob:L67]. No ambient clock.
        st.batch.dates.stored = move.move(
            st.system.system_data_block.run_date, _STORED
        )

        # 587  move     zero      to  batch-start.
        # The move `gl072` does not make [general/gl072.cbl:L375-L377].
        st.batch.batch_start = move.move_figurative(move.ZERO, _BATCH_START)

        # 589  perform  GL-Batch-Rewrite.     *> rewrite  batch-record.
        facade.gl_batch_rewrite(st.batch_ctx())

        # 590  go       to loop.
        # GO TO class 1.
        continue


def _gl080c_end_run(st: _Gl080Storage) -> None:
    """`end-run.` - close the batch file  [general/gl080.cbl:L592-L595].

        592  end-run.
        595      perform  GL-Batch-Close.     *> close  batch-file.

    The third of the three `end-run.` paragraphs. Shorter than `gl080b`'s
    [general/gl080.cbl:L436-L440] by one statement: there is no archive sequence
    to close because this path never opened one.

    Args:
        st: The program's storage.
    """
    # 595  perform  GL-Batch-Close.
    facade.gl_batch_close(st.batch_ctx())

    # Control FALLS THROUGH into `main-exit.` [general/gl080.cbl:L597].


def _gl080c_main_exit(st: _Gl080Storage) -> None:
    """`main-exit.   exit section.`  [general/gl080.cbl:L597].

    The fifth of the seven `main-exit.` paragraphs. Reached only by
    fall-through from `end-run.`; no `GO TO` in this section targets it, because
    this path has no `disk-change` option to abort on.

    Args:
        st: The program's storage, unchanged by this paragraph.
    """
    # 597  exit section.
    _LOG.debug("gl080c complete")
    return


# ---------------------------------------------------------------------------
#  del-process section.   [general/gl080.cbl:L600]   -   DELETE ONE BATCH'S
#                                                        POSTINGS
# ---------------------------------------------------------------------------


def _del_process(st: _Gl080Storage) -> None:
    """`del-process section.` - delete every posting of one batch.

    [general/gl080.cbl:L600-L607].

        600  del-process        section.
        603  *> Using RDB this step can be done with one SQL process to delete all
        604  *>   specific batch no but using Cobol this is not possible.
        606      display  WS-Batch-Nos at 2345.
        607      perform  GL-Posting-Open.     *> open  i-o  posting-file.

    THE MAINTAINER'S COMMENT AT L603-L604 IS AN INVITATION THAT MUST BE
    DECLINED. He observes, correctly, that against a relational store the whole
    walk below could be one statement deleting every posting of a batch. Agent
    Action Plan section 0.8.4 forbids taking it up, verbatim: "Any performance
    work is therefore out of scope by construction, not merely unrequested." The
    row-at-a-time walk is preserved because the statement ordering it produces is
    what the state diff is compared against, and because the read filter at
    [general/gl080.cbl:L616-L618] skips rows a set-based delete would remove.
    THIS SECTION IS THE CLEAREST TEMPTATION IN THE PROGRAM; IT IS ALSO THE ONE
    THE SOURCE ITSELF WARNS ABOUT.

    `arc-process` is this section plus the archive: same open, same sequential
    walk, same filter, same delete. The two exist separately because one writes
    the flat archive rows first.

    Args:
        st: The program's storage.
    """
    # 606  display  WS-Batch-Nos at 2345.
    # Screen furniture. `arc-process` makes the same display at
    # [general/gl080.cbl:L448] and additionally moves the value into the archive
    # header at L449; there is no header here, so the display stands alone.
    _LOG.debug("deleting postings of batch %s", st.batch.ws_batch_key.ws_batch_nos)

    # 607  perform  GL-Posting-Open.      *> open  i-o  posting-file.
    # THE INNER HALF OF THE ASYMMETRIC PAIR - the close is in the caller at
    # [general/gl080.cbl:L583]. `GL-Posting-Open.`
    # [copybooks/Proc-ACAS-FH-Calls.cob:L356] sets the function to open and the
    # access to i-o, then performs `acas006`.
    facade.gl_posting_open(st.posting_ctx())

    # Fall-through into `loop.` [general/gl080.cbl:L609].
    _del_process_loop(st)


def _del_process_loop(st: _Gl080Storage) -> None:
    """`loop.` - one posting per pass  [general/gl080.cbl:L609-L623].

        609  loop.
        612      perform  GL-Posting-Read-Next.
        613      if       fs-reply = 10
        614               go to  main-exit.
        616      if       WS-Post-Key = zero
        617         or    batch  not = WS-Batch-Nos
        618               go to  loop.
        620      display  post-number at 2364 ...
        622      perform  GL-Posting-Delete.
        623      go       to loop.

    THE SAME FILTER AS `arc-process`'S [general/gl080.cbl:L459-L461], written the
    same way - one `if` with an `or` over the group key and the batch number.
    THE SAME DELETE, TOO [general/gl080.cbl:L513]. `gl080` is the only in-scope
    program that performs `GL-Posting-Delete`, and it performs it from these two
    places.

    A posting skipped by the filter is NOT deleted, in this path exactly as in
    the archive path, so postings belonging to other batches survive the walk.

    Args:
        st: The program's storage.
    """
    while True:
        # 612  perform  GL-Posting-Read-Next.
        facade.gl_posting_read_next(st.posting_ctx())

        # 613  if       fs-reply = 10
        if arithmetic.compare(st.file_access.fs_reply, _FS_AT_END) == 0:
            # 614  go to  main-exit.
            # GO TO class 3 - a transfer to this section's exit paragraph
            # [general/gl080.cbl:L625]. Reproduced as a call to that paragraph
            # followed by a return. THIS IS THE SECTION'S ONLY EXIT, which is
            # why `_del_process` does not call the exit paragraph again after
            # this function returns.
            _del_process_main_exit(st)
            return

        # 616  if       WS-Post-Key = zero
        # 617     or    batch  not = WS-Batch-Nos
        # 618           go to  loop.
        #
        # `WS-Post-Key` [copybooks/wspost.cob:L14] is a group of two `pic 9(5)`
        # items, so `= zero` holds exactly when both are zero; the single COBOL
        # condition is expressed over the two items the group declares. No test
        # is added (rule R-3) - one test is written against its own members.
        if (
            arithmetic.compare(st.posting.ws_post_key.batch, 0) == 0
            and arithmetic.compare(st.posting.ws_post_key.post_number, 0) == 0
        ) or arithmetic.compare(
            st.posting.ws_post_key.batch, st.batch.ws_batch_key.ws_batch_nos
        ) != 0:
            # 618  go to  loop.
            # GO TO class 1.
            continue

        # 620  display  post-number at 2364 ...
        _LOG.debug("deleting posting %s", st.posting.ws_post_key.post_number)

        # 622  perform  GL-Posting-Delete.   *> delete  posting-file  record.
        # THE TABLE EFFECT OF PHASE 3, one row per pass. `GL-Posting-Delete.`
        # [copybooks/Proc-ACAS-FH-Calls.cob:L403] pins the key number to 1, sets
        # the function to delete, and performs `acas006`.
        facade.gl_posting_delete(st.posting_ctx())

        # 623  go       to loop.
        # GO TO class 1.
        continue


def _del_process_main_exit(st: _Gl080Storage) -> None:
    """`main-exit.   exit section.`  [general/gl080.cbl:L625].

    The sixth of the seven `main-exit.` paragraphs. Reached only by the class-3
    transfer at [general/gl080.cbl:L614].

    Args:
        st: The program's storage, unchanged by this paragraph.
    """
    # 625  exit section.
    _LOG.debug("del-process complete for batch %s", st.batch.ws_batch_key.ws_batch_nos)
    return



# ---------------------------------------------------------------------------
#  compress-post section.   [general/gl080.cbl:L628]   -   PHASE 4, POSTING
#                                                          CONTRACTION
# ---------------------------------------------------------------------------


def _compress_post(st: _Gl080Storage) -> None:
    """`compress-post section.` - Phase 4, rebuild the posting file.

    [general/gl080.cbl:L628-L637]. Performed unconditionally by the phase driver
    at [general/gl080.cbl:L322], after whichever of `gl080b` or `gl080c` ran.

        628  compress-post  section.
        631  *>  First check if NOT running with Cobol files, if so skip section.
        633      if       not FS-Cobol-Files-Used  *> Will use fn-Read-Next-...
        634               go to main-exit
        635      end-if.
        637      display  "Phase - 4.  Posting Contraction " at 0801 ...

    THE BODY IS PRESENT IN FULL AND NOTHING WAS DELETED AS UNREACHABLE. The gate
    on L633 is a RUNTIME condition over a system-record field, so which way it
    goes is decided by the data and not by this migration. Reproducing the
    section whole is the only faithful answer; abbreviating it to the early return
    would delete seventy lines of the specification on the strength of an
    assumption about configuration.

    WHAT THE GATE ACTUALLY DECIDES. `88 FS-Cobol-Files-Used value zero.`
    [copybooks/wssystem.cob:L113] and `88 FS-RDBMS-Used value 1.`
    [copybooks/wssystem.cob:L116] are two condition names over one field. Against
    the relational store the field is 1, so `not FS-Cobol-Files-Used` is TRUE and
    the section returns at L634 having done nothing at all. Against indexed files
    it is zero and the walk below runs. The maintainer's own comment on L633 names
    the alternative he intended for the relational case - a sorted-by-batch read
    function - and it is not implemented here because it is not implemented there
    either.

    AMBIGUITY Q-23: IN THE FROZEN SOURCE NEITHER CONFIGURATION REACHES THE LOOPS.
    The relational one returns at L634. The indexed one falls into
    `Test-Work-File-Size-1`, whose length comparison the MEASURED widths fail -
    103 against 101 - so `stop run` [general/gl080.cbl:L649] fires. Both widths
    are computed from the dictionary's own descriptors below rather than typed in,
    so if the oracle disagrees with the measurement the test changes with it. The
    oracle question is whether GnuCOBOL 3.2 reports the same two lengths, and
    therefore whether any run of this program can execute L651 onwards.

    Args:
        st: The program's storage.

    Raises:
        _StopRun: From `Test-Work-File-Size-1` [general/gl080.cbl:L649] when the
            two record lengths disagree.
    """
    # 633  if       not FS-Cobol-Files-Used
    # 634           go to main-exit
    # 635  end-if.
    #
    # Through the condition-name vocabulary - `FS-Cobol-Files-Used` is declared
    # over `File-System-Used` in [copybooks/wssystem.cob:L113], and the value it
    # declares belongs to the copybook rather than to this module. Never a bare
    # comparison against zero.
    if not condition_names.evaluate(
        "FS-Cobol-Files-Used",
        st.system.system_data_block.rdbms_flat_statuses.file_system_used,
    ):
        # 634  go to main-exit.
        # GO TO class 3 - a transfer to this section's exit paragraph
        # [general/gl080.cbl:L705]. Reproduced as a call to that paragraph
        # followed by a return.
        _LOG.debug(
            "compress-post skipped: the file system in use is not Cobol files "
            "[general/gl080.cbl:L633]"
        )
        _compress_post_main_exit(st)
        return

    # 637  display  "Phase - 4.  Posting Contraction " at 0801 ...
    # THE FOURTH OF THE FIVE PHASE LABELS, and one of the two that COLLIDE with
    # another program's numbering: `gl072`'s Phase 4 is "Transaction Update"
    # [general/gl072.cbl:L274]. The trailing space inside the literal is the
    # maintainer's. Preserved as a log record with no control-flow effect.
    _LOG.info("Phase - 4.  Posting Contraction")

    # Fall-through into `Test-Work-File-Size-1.` [general/gl080.cbl:L639].
    _compress_post_test_work_file_size_1(st)

    # 705  main-exit.
    # Reached by fall-through from `loop2-end.` [general/gl080.cbl:L703], on
    # every path that did not transfer out above.
    _compress_post_main_exit(st)


def _compress_post_test_work_file_size_1(st: _Gl080Storage) -> None:
    """`Test-Work-File-Size-1.` - the length gate and the two loops.

    [general/gl080.cbl:L639-L652], then the paragraphs it falls through into.

        639  Test-Work-File-Size-1.
        641  *>  Check files are same size
        643      if       function length (WS-Posting-Record) not =
        644               function length (work-file-record)
        645               display GL082 at 1001 ...
        646               display GL083 at 1101 ...
        647               display GL012 at 1201 ...
        648               accept Keyed-Reply at 1227
        649               stop run.
        651      perform  GL-Posting-Open-Input.     *> open  input  posting-file.
        652      open     output work-file.

    BOTH LENGTHS ARE COMPUTED FROM DESCRIPTORS, NEVER TYPED IN. `FUNCTION LENGTH`
    of a group is the sum of its elementary items' storage widths, so the sending
    side is summed over the copybook's own declarations - which is also how the
    103 in AMBIGUITY Q-23 was measured - and the receiving side is the width its
    picture declares. Hard-coding either number would make this test agree with
    itself rather than with the records.

    THE MEASUREMENT, AND WHY IT MATTERS. `01 WS-Posting-Record.`
    [copybooks/wspost.cob:L12] sums to 103 characters: 98 for the posting proper
    plus the five of `WS-Post-rrn`, whose addition is what the maintainer's own
    comment on [general/gl080.cbl:L172] records - "Was 96 added 5 for WS-Post-rrn
    (9(5)". He widened `work-file-record` to 101 for it, which is 96 plus 5; the
    96 in that header is an arithmetic slip and the record is 98 without the
    reference number. So the two lengths differ by exactly the slip, the test at
    L643 is TRUE, and `stop run` fires. The defect is reproduced, not corrected
    (rule R-4): nothing here widens the work record, and nothing skips the test.

    THE ABORT IS A RUN-UNIT TERMINATION AND IS RAISED, NOT RETURNED. See
    `_StopRun`. Agent Action Plan section 0.6.5 classes this as a run-aborting
    rejection, whose database effect is the absence of everything the statements
    below would have written - so the posting file is neither emptied nor rebuilt,
    and Phase 5 never runs either.

    Args:
        st: The program's storage.

    Raises:
        _StopRun: When the two record lengths disagree
            [general/gl080.cbl:L649].
    """
    # 643  if       function length (WS-Posting-Record) not =
    # 644           function length (work-file-record)
    #
    # The sending group's own elementary declarations, summed. Group views carry
    # no width of their own, so they are excluded rather than counted as zero.
    posting_descriptors = descriptors_for_copybook_record("WS-Posting-Record")
    posting_length = sum(
        descriptor.byte_length
        for descriptor in posting_descriptors
        if not descriptor.is_group
    )
    work_length = _WORK_FILE_RECORD.byte_length

    if arithmetic.compare(posting_length, work_length) != 0:
        # 645  display GL082 at 1001 ...
        # 646  display GL083 at 1101 ...
        # 647  display GL012 at 1201 ...
        # `GL082` [general/gl080.cbl:L250] and `GL083` [general/gl080.cbl:L251]
        # report the mismatch; `GL012` [general/gl080.cbl:L246] is the
        # press-a-key prompt.
        _LOG.error(
            "posting record length %s does not match work file record length "
            "%s [general/gl080.cbl:L643-L644]",
            posting_length,
            work_length,
        )

        # 648  accept Keyed-Reply at 1227
        # An ACKNOWLEDGEMENT PAUSE whose only effect is to hold a terminal, so it
        # is dropped (Agent Action Plan section 0.3.4). THE STATEMENT AFTER IT IS
        # NOT.

        # 649  stop run.
        raise _StopRun(
            "compress-post: function length (WS-Posting-Record) = "
            f"{posting_length} does not equal function length "
            f"(work-file-record) = {work_length} "
            "[general/gl080.cbl:L643-L649]"
        )

    # 651  perform  GL-Posting-Open-Input.   *> open  input  posting-file.
    # `GL-Posting-Open-Input.` [copybooks/Proc-ACAS-FH-Calls.cob:L360]. `gl080`
    # is the only General Ledger program that opens the posting file for input
    # only; every other open in this program is i-o or output.
    facade.gl_posting_open_input(st.posting_ctx())

    # 652  open     output work-file.
    # CREATE OR TRUNCATE. The scratch sequence starts empty on every pass.
    st.work_file.open_output()

    # Fall-through into `loop1.` [general/gl080.cbl:L654].
    if _compress_post_loop1(st):
        # The class-4 transfer to `file-error.` was taken inside the loop, and
        # `file-error` has already fallen through into `loop2-end.`, so the whole
        # of `loop1-end.`, `loop2.` and the second half of the section is
        # skipped. Control resumes at `main-exit.` in the caller.
        return

    # 667  loop1-end.
    # Reached by the class-2 transfer at [general/gl080.cbl:L659].
    _compress_post_loop1_end(st)

    # Fall-through into `loop2.` [general/gl080.cbl:L675].
    if _compress_post_loop2(st):
        # As above: `file-error.` ran and fell through into `loop2-end.`.
        return

    # 699  loop2-end.
    # Reached by the class-2 transfer at [general/gl080.cbl:L679].
    _compress_post_loop2_end(st)


def _compress_post_loop1(st: _Gl080Storage) -> bool:
    """`loop1.` - copy every posting out to the scratch sequence.

    [general/gl080.cbl:L654-L665].

        654  loop1.
        657      perform  GL-Posting-Read-Next.
        658      if       fs-reply = 10
        659               go to loop1-end.
        660      if       fs-reply not = zero
        661               go to file-error.
        662      write    work-file-record from WS-Posting-Record.
        663      if       fs-reply not = zero
        664               go to file-error.
        665      go       to loop1.

    NOTE THE ORDER OF THE TWO STATUS TESTS AT L658 AND L660. End of file is
    tested FIRST, so status 10 leaves by the class-2 route and only a status that
    is neither 0 nor 10 reaches `file-error`. Reversing them would send every
    end-of-file through the error path.

    Args:
        st: The program's storage.

    Returns:
        True when one of the two class-4 transfers to `file-error.` was taken -
        in which case `file-error.` and the `loop2-end.` it falls into have
        ALREADY RUN and the caller must not continue. False when the class-2
        transfer at L659 was taken, in which case `loop1-end.` follows.
    """
    # The sending group and its width, needed by the FROM phrase at L662. Read
    # once; the copybook does not change between passes.
    posting_descriptors = descriptors_for_copybook_record("WS-Posting-Record")
    posting_group = next(
        descriptor
        for descriptor in posting_descriptors
        if descriptor.is_group and descriptor.name.lower() == "ws-posting-record"
    )
    posting_length = sum(
        descriptor.byte_length
        for descriptor in posting_descriptors
        if not descriptor.is_group
    )

    while True:
        # 657  perform  GL-Posting-Read-Next.
        facade.gl_posting_read_next(st.posting_ctx())

        # 658  if       fs-reply = 10
        if arithmetic.compare(st.file_access.fs_reply, _FS_AT_END) == 0:
            # 659  go to loop1-end.
            # GO TO class 2 - the forward terminator. The work that follows the
            # label - two closes, an open input and an open output
            # [general/gl080.cbl:L670-L673] - is placed AFTER this loop by the
            # caller, not inside it. Agent Action Plan section 0.6.3 warns that
            # mis-splitting a class 2 site "would silently drop end-of-run
            # processing"; here it would leave the posting file open and the
            # scratch sequence never re-read.
            return False

        # 660  if       fs-reply not = zero
        # 661           go to file-error.
        if arithmetic.compare(st.file_access.fs_reply, _FS_OK) != 0:
            # 661  go to file-error.
            #
            # GO TO CLASS 4, SITE ONE OF FOUR. EQUIVALENCE PROOF: `file-error.`
            # [general/gl080.cbl:L688] performs work - five displays, a pause and
            # an erase - and its LAST STATEMENT IS L697, with NO transfer of any
            # kind after it. Control therefore FALLS THROUGH into the next
            # paragraph in the source, `loop2-end.` [general/gl080.cbl:L699],
            # which closes the work file and the posting file. So the transfer is
            # equivalent to: run `file-error`, then run `loop2-end`, then leave
            # the section by fall-through into `main-exit.` The composition below
            # is exactly that, and the `return True` reports to the caller that
            # both paragraphs have run.
            #
            # THE CONSEQUENCE, WHICH IS THE POINT: A `loop1` ERROR NEVER RUNS
            # `loop1-end.` So the two closes at [general/gl080.cbl:L670-L671] are
            # SKIPPED, the `open input work-file` at L672 and the
            # `GL-Posting-Open-Output` at L673 never happen, and the file is
            # closed instead by L702-L703 - a different pair of closes reached by
            # a different route. Nothing rebuilds the posting file, which is what
            # keeps a mid-copy failure from emptying it.
            _compress_post_file_error(st)
            _compress_post_loop2_end(st)
            return True

        # 662  write    work-file-record from WS-Posting-Record.
        # The FROM phrase moves the sending group into the `pic x(101)` record
        # area and then writes. See `_WorkFile.write_from` for how the group's
        # byte image is modelled and why.
        st.work_file.write_from(
            st.posting,
            image=move.move_group(
                move.SPACE, posting_group, length=posting_length
            ),
            group=posting_group,
        )

        # 663  if       fs-reply not = zero
        # 664           go to file-error.
        if arithmetic.compare(st.file_access.fs_reply, _FS_OK) != 0:
            # 664  go to file-error.
            #
            # GO TO CLASS 4, SITE TWO OF FOUR. EQUIVALENCE PROOF: as at site one
            # - `file-error.` falls through into `loop2-end.` because L697 ends
            # the paragraph with no transfer. The composition runs both, and
            # `loop1-end.`'s own closes at [general/gl080.cbl:L670-L671] are
            # skipped. This site differs from site one only in WHICH statement
            # failed: a write rather than a read, so a row may be half-copied,
            # and the posting file is left exactly as it was because nothing has
            # emptied it yet.
            _compress_post_file_error(st)
            _compress_post_loop2_end(st)
            return True

        # 665  go       to loop1.
        # GO TO class 1.
        continue


def _compress_post_loop1_end(st: _Gl080Storage) -> None:
    """`loop1-end.` - turn both files around  [general/gl080.cbl:L667-L673].

        667  loop1-end.
        670      close    work-file.                 *> posting-file
        671      perform  GL-Posting-Close.
        672      open     input  work-file.
        673      perform  GL-Posting-Open-Output.     *> open output posting-file.

    FOUR STATEMENTS THAT SWAP THE DIRECTION OF BOTH FILES: the scratch sequence
    stops being written and starts being read, and the posting file stops being
    read and starts being written. The maintainer's comment on L670 names the
    wrong file; the statement closes the work file and the next line closes the
    posting file.

    AMBIGUITY Q-20 - THE DANGEROUS LINE IN THIS PROGRAM. L673 performs
    `GL-Posting-Open-Output` [copybooks/Proc-ACAS-FH-Calls.cob:L364], and on a
    relational store an open-for-output can mean DELETE EVERY ROW - which is
    exactly what the transfer-file handler does for the same verb
    [common/acas008.cbl:L313-L319]. If that is what `acas006` does then this
    statement empties the posting table, and the only thing standing between it
    and the data is the length test two paragraphs earlier. What `acas006`'s
    open-output actually does is an oracle question. NO GUARD IS ADDED (rule R-3):
    adding one would be a new validation, and the frozen source has none.

    Reached only by the class-2 transfer at [general/gl080.cbl:L659]. Both
    class-4 routes out of `loop1` skip it entirely.

    Args:
        st: The program's storage.
    """
    # 670  close    work-file.
    st.work_file.close()

    # 671  perform  GL-Posting-Close.
    facade.gl_posting_close(st.posting_ctx())

    # 672  open     input  work-file.
    # Rewinds to the first row, so `loop2` reads back what `loop1` wrote in the
    # order it wrote it.
    st.work_file.open_input()

    # 673  perform  GL-Posting-Open-Output.
    # See AMBIGUITY Q-20 above. Reproduced without a guard.
    facade.gl_posting_open_output(st.posting_ctx())

    # Control FALLS THROUGH into `loop2.` [general/gl080.cbl:L675].


def _compress_post_loop2(st: _Gl080Storage) -> bool:
    """`loop2.` - write every row back into the posting file.

    [general/gl080.cbl:L675-L686].

        675  loop2.
        678      read     work-file at end
        679               go to loop2-end.
        680      if       fs-reply not = zero
        681               go to file-error.
        682      move     work-file-record to WS-Posting-Record.
        683      perform  GL-Posting-Write.
        684      if       fs-reply not = zero
        685               go to file-error.
        686      go       to loop2.

    NOTE THE ASYMMETRY WITH `loop1`. There the end of file is a STATUS TEST
    [general/gl080.cbl:L658] because the read goes through a facade verb; here it
    is an AT END PHRASE [general/gl080.cbl:L678] because the read is a direct
    verb on a flat file. Same outcome, two different mechanisms, both preserved.

    `gl080` is the only General Ledger program that performs `GL-Posting-Write`,
    and this is the only place it does so.

    Args:
        st: The program's storage.

    Returns:
        True when one of the two class-4 transfers to `file-error.` was taken -
        in which case `file-error.` and `loop2-end.` have ALREADY RUN. False when
        the AT END route at L679 was taken, in which case `loop2-end.` follows.
    """
    # The receiving group and its width, for the group move at L682.
    posting_descriptors = descriptors_for_copybook_record("WS-Posting-Record")
    posting_group = next(
        descriptor
        for descriptor in posting_descriptors
        if descriptor.is_group and descriptor.name.lower() == "ws-posting-record"
    )
    posting_length = sum(
        descriptor.byte_length
        for descriptor in posting_descriptors
        if not descriptor.is_group
    )

    while True:
        # 678  read     work-file at end
        # 679           go to loop2-end.
        if not st.work_file.read():
            # 679  go to loop2-end.
            # GO TO class 2 - the forward terminator, reached through the AT END
            # phrase rather than a status test. The two closes that follow the
            # label are placed after this loop by the caller.
            return False

        # 680  if       fs-reply not = zero
        # 681           go to file-error.
        if arithmetic.compare(st.file_access.fs_reply, _FS_OK) != 0:
            # 681  go to file-error.
            #
            # GO TO CLASS 4, SITE THREE OF FOUR. EQUIVALENCE PROOF: `file-error.`
            # [general/gl080.cbl:L688] ends at L697 with no transfer, so control
            # falls through into `loop2-end.` [general/gl080.cbl:L699]. The
            # composition runs both and returns. UNLIKE THE TWO SITES IN `loop1`,
            # this one loses nothing by skipping ahead: `loop2-end.` is the very
            # paragraph this loop would have reached anyway, so the transfer's
            # only effect is to end the loop early after reporting. The database
            # is left with however many rows had been written back - the posting
            # file was emptied at L673 and is only partly rebuilt, and nothing
            # rolls that back (rule R-3: no transaction wrapper is added).
            _compress_post_file_error(st)
            _compress_post_loop2_end(st)
            return True

        # 682  move     work-file-record to WS-Posting-Record.
        # A GROUP MOVE of the 101 raw characters into a group receiver, so no
        # child picture is applied and no numeric conversion happens. Delegated
        # whole; see `_WorkFile.write_from` for how the field values travel.
        image = move.move_group(
            st.work_file.record, posting_group, length=posting_length
        )
        # The 101-character sender pads to the group's 103, which is the width
        # disagreement the length gate exists to prevent - and does. The field
        # values are taken from the snapshot the row carries, for the reason
        # `_WorkFile.write_from` documents. Rebinding the record area rather than
        # refilling it field by field is equivalent here because
        # `01 WS-Posting-Record.` is this program's own working storage
        # [general/gl080.cbl:L190] - nothing outside the program holds a
        # reference to it, and `posting_ctx()` reads the attribute afresh on
        # every facade call.
        if st.work_file.posting_image is not None:
            st.posting = st.work_file.posting_image
        _LOG.debug(
            "contraction restored a %s-character posting image from %s",
            len(image),
            st.work_file.name,
        )

        # 683  perform  GL-Posting-Write.   *> write posting-record from ...
        facade.gl_posting_write(st.posting_ctx())

        # 684  if       fs-reply not = zero
        # 685           go to file-error.
        if arithmetic.compare(st.file_access.fs_reply, _FS_OK) != 0:
            # 685  go to file-error.
            #
            # GO TO CLASS 4, SITE FOUR OF FOUR. EQUIVALENCE PROOF: as at site
            # three - `file-error.` falls through into `loop2-end.`, the
            # composition runs both, and this loop ends early. This site differs
            # in that the failure is a WRITE into the emptied posting file, so
            # the row that failed is missing from the rebuilt table and every row
            # after it is never attempted.
            _compress_post_file_error(st)
            _compress_post_loop2_end(st)
            return True

        # 686  go       to loop2.
        # GO TO class 1.
        continue


def _compress_post_file_error(st: _Gl080Storage) -> None:
    """`file-error.` - report, and FALL THROUGH  [general/gl080.cbl:L688-L697].

        688  file-error.
        691      display  GL081 at 1501 ...
        692      display  fs-reply at 1539 ...
        693      perform  evaluate-message.
        694      display  ws-Eval-Msg at 1542.
        695      display  GL012 at 1601 with erase eol ...
        696      accept   Keyed-Reply at 1627.
        697      display  " " at 1601 with erase eol.

    THE MAJOR FALL-THROUGH OF THIS PROGRAM. L697 is the paragraph's last
    statement and there is NO `GO TO`, no `PERFORM` return and no `EXIT` after
    it, so control runs straight on into `loop2-end.` [general/gl080.cbl:L699].
    Every one of the four `go to file-error` sites therefore ends up closing both
    files through L702-L703 - including the two in `loop1`, which never reach
    their own closes at L670-L671. The prompt's requirement that fall-through
    become explicit function composition preserving execution order is met by the
    four call pairs at those sites; this paragraph itself only reports.

    THIS PARAGRAPH HAS NO DATABASE EFFECT. Five displays become one log record;
    the pause at L696 is dropped as an acknowledgement pause, and the erase at
    L697 is screen furniture. What must not be dropped is the fall-through, and
    that is carried at the call sites rather than here, because a Python function
    cannot fall into its successor.

    Args:
        st: The program's storage. `st.ws_eval_msg` is written by the message
            lookup this paragraph performs.
    """
    # 691  display  GL081 at 1501 ...
    # `GL081` [general/gl080.cbl:L249].
    # 692  display  fs-reply at 1539 ...

    # 693  perform  evaluate-message.
    # The message-table lookup. Diagnostic only - it sets the text and must not
    # alter control flow, and it does not.
    _evaluate_message(st)

    # 694  display  ws-Eval-Msg at 1542.
    # 695  display  GL012 at 1601 with erase eol ...
    _LOG.error(
        "posting file error: fs-reply=%s %s [general/gl080.cbl:L691-L694]",
        st.file_access.fs_reply,
        st.ws_eval_msg,
    )

    # 696  accept   Keyed-Reply at 1627.
    # An acknowledgement pause. Dropped; nothing depended on it.

    # 697  display  " " at 1601 with erase eol.
    # Screen furniture, and THE LAST STATEMENT OF THE PARAGRAPH. Control now
    # FALLS THROUGH into `loop2-end.` [general/gl080.cbl:L699] - carried out by
    # the caller, which calls `_compress_post_loop2_end` immediately after this
    # function returns.


def _compress_post_loop2_end(st: _Gl080Storage) -> None:
    """`loop2-end.` - close both files  [general/gl080.cbl:L699-L703].

        699  loop2-end.
        702      close    work-file.        *>  posting-file.
        703      perform  GL-Posting-Close.

    REACHED FIVE WAYS: by the class-2 transfer at [general/gl080.cbl:L679], and
    by fall-through from `file-error.` on each of the four class-4 sites. That is
    why the two closes live here rather than being duplicated at the error sites,
    and why an error inside `loop1` closes through this paragraph instead of
    through `loop1-end.`

    The maintainer's comment on L702 again names the wrong file.

    Args:
        st: The program's storage.
    """
    # 702  close    work-file.
    st.work_file.close()

    # 703  perform  GL-Posting-Close.
    facade.gl_posting_close(st.posting_ctx())

    # Control FALLS THROUGH into `main-exit.` [general/gl080.cbl:L705].


def _compress_post_main_exit(st: _Gl080Storage) -> None:
    """`main-exit.` / `exit section.`  [general/gl080.cbl:L705-L708].

    The seventh and last of the seven `main-exit.` paragraphs, and the only one
    whose `exit section.` sits on a line of its own rather than sharing the
    label's line. Reached two ways: by the class-3 transfer at
    [general/gl080.cbl:L634] when the file system in use is not Cobol files, and
    by fall-through from `loop2-end.` otherwise.

    Args:
        st: The program's storage, unchanged by this paragraph.
    """
    # 708  exit     section.
    _LOG.debug("compress-post complete")
    return


# ---------------------------------------------------------------------------
#  Evaluate-Message Section.   [general/gl080.cbl:L710]
# ---------------------------------------------------------------------------

#: The `EVALUATE STATUS` table that `copy "FileStat-Msgs.cpy" replacing MSG by
#: ws-Eval-Msg STATUS by fs-reply.` [general/gl080.cbl:L713-L714] expands into.
#:
#: THIRTY-TWO `WHEN` CLAUSES AND A `WHEN OTHER`, transcribed from
#: [copybooks/FileStat-Msgs.cpy:L23-L60] in the copybook's own order. Every
#: literal there is written 25 characters wide to match
#: `ws-eval-msg pic x(25)` [general/gl080.cbl:L185], and the padding is left to
#: the store through that field's descriptor rather than typed in here.
#:
#: The copybook is part of this program's `COPY` closure and therefore in scope
#: as specification. Its two authors and its amendment history are recorded in
#: its own header; nothing here corrects or extends the table (rule R-3), which
#: is why the two statuses this program actually produces most often - 00 and 10
#: - sit alongside statuses no ACAS handler ever returns.
_FILE_STATUS_MESSAGES: Final[Mapping[int, str]] = {
    0: "Success",  # [copybooks/FileStat-Msgs.cpy:L24]
    2: "Success Duplicate",  # [copybooks/FileStat-Msgs.cpy:L25]
    4: "Success Incomplete",  # [copybooks/FileStat-Msgs.cpy:L26]
    5: "Success Optional, Missing",  # [copybooks/FileStat-Msgs.cpy:L27]
    6: "Multiple Records LS",  # [copybooks/FileStat-Msgs.cpy:L28]
    7: "Success No Unit",  # [copybooks/FileStat-Msgs.cpy:L29]
    9: "Success LS Bad Data",  # [copybooks/FileStat-Msgs.cpy:L30]
    10: "End Of File",  # [copybooks/FileStat-Msgs.cpy:L31]
    14: "Out Of Key Range",  # [copybooks/FileStat-Msgs.cpy:L32]
    21: "Key Invalid",  # [copybooks/FileStat-Msgs.cpy:L33]
    22: "Key Exists",  # [copybooks/FileStat-Msgs.cpy:L34]
    23: "Key Not Exists",  # [copybooks/FileStat-Msgs.cpy:L35]
    24: "Key Boundary violation",  # [copybooks/FileStat-Msgs.cpy:L36]
    30: "Permanent Error",  # [copybooks/FileStat-Msgs.cpy:L37]
    31: "Inconsistent Filename",  # [copybooks/FileStat-Msgs.cpy:L38]
    34: "Boundary Violation",  # [copybooks/FileStat-Msgs.cpy:L39]
    35: "File Not Found",  # [copybooks/FileStat-Msgs.cpy:L40]
    37: "Permission Denied",  # [copybooks/FileStat-Msgs.cpy:L41]
    38: "Closed With Lock",  # [copybooks/FileStat-Msgs.cpy:L42]
    39: "Conflict Attribute",  # [copybooks/FileStat-Msgs.cpy:L43]
    41: "Already Open",  # [copybooks/FileStat-Msgs.cpy:L44]
    42: "Not Open",  # [copybooks/FileStat-Msgs.cpy:L45]
    43: "Read Not Done",  # [copybooks/FileStat-Msgs.cpy:L46]
    44: "Record Overflow",  # [copybooks/FileStat-Msgs.cpy:L47]
    46: "Read Error",  # [copybooks/FileStat-Msgs.cpy:L48]
    47: "Input Denied",  # [copybooks/FileStat-Msgs.cpy:L49]
    48: "Output Denied",  # [copybooks/FileStat-Msgs.cpy:L50]
    49: "I/O Denied",  # [copybooks/FileStat-Msgs.cpy:L51]
    51: "Record Locked",  # [copybooks/FileStat-Msgs.cpy:L52]
    52: "End-Of-Page",  # [copybooks/FileStat-Msgs.cpy:L53]
    57: "I/O Linage",  # [copybooks/FileStat-Msgs.cpy:L54]
    61: "File Sharing Failure",  # [copybooks/FileStat-Msgs.cpy:L55]
    71: "Bad Character LS",  # [copybooks/FileStat-Msgs.cpy:L56]
    91: "Feature Not Available",  # [copybooks/FileStat-Msgs.cpy:L57]
}

#: `WHEN OTHER MOVE "Unknown File Status      " TO MSG`
#: [copybooks/FileStat-Msgs.cpy:L58-L59].
_FILE_STATUS_MESSAGE_OTHER: Final[str] = "Unknown File Status"


def _evaluate_message(st: _Gl080Storage) -> None:
    """`Evaluate-Message Section.` - status to text  [general/gl080.cbl:L710].

        710  Evaluate-Message       Section.
        713  copy "FileStat-Msgs.cpy" replacing MSG by ws-Eval-Msg
        714                                    STATUS by fs-reply.
        716  Eval-Msg-Exit.  exit section.

    THE SECTION IS A COPY STATEMENT AND NOTHING ELSE. The `replacing` phrase
    binds the copybook's two placeholders to this program's own names, so what
    the compiler sees is one `EVALUATE fs-reply` with thirty-three branches, each
    a `MOVE` of a literal into `ws-eval-msg`.

    THE SPELLING OF THE SECTION NAME IS LOCAL AND IS PRESERVED. `gl080` writes
    `Evaluate-Message`, which is what `pl060` writes too
    [purchase/pl060.cbl:L1037], while `sl060` writes `zz040-Evaluate-Message`
    [sales/sl060.cbl:L1183] for the same idea. Renaming either to match the other
    would break the paragraph-to-function traceability rule R-5 depends on.

    DIAGNOSTIC ONLY, AND IT MUST STAY THAT WAY. The one caller is `file-error.`
    [general/gl080.cbl:L693], which displays the text at L694 and does nothing
    else with it. No branch anywhere reads `ws-eval-msg`, so this function alters
    no control flow and reaches no table. It is kept as a named function because
    rule R-5 requires one per section, and because a reader following L693 must
    find it.

    Args:
        st: The program's storage. Reads `Fs-Reply` and writes `ws-eval-msg`.
    """
    # 713  EVALUATE fs-reply ... MOVE "<text>" TO ws-Eval-Msg
    #
    # `Fs-Reply pic 99` [copybooks/wsfnctn.cob:L25] holds the two-digit status as
    # a number, so the `WHEN 00` through `WHEN 91` branches are integer
    # selections. `WHEN OTHER` is the fall-back the copybook declares.
    status = int(st.file_access.fs_reply)
    text = _FILE_STATUS_MESSAGES.get(status, _FILE_STATUS_MESSAGE_OTHER)

    # The literal is stored through the receiving field's own descriptor, so the
    # 25-character width and its space padding come from
    # `ws-eval-msg pic x(25)` [general/gl080.cbl:L185] rather than from the
    # length the copybook happens to have typed.
    st.ws_eval_msg = move.move(text, _WS_EVAL_MSG)

    # 716  Eval-Msg-Exit.  exit section.
    _eval_msg_exit(st)


def _eval_msg_exit(st: _Gl080Storage) -> None:
    """`Eval-Msg-Exit.  exit section.`  [general/gl080.cbl:L716].

    Reached only by fall-through; no `GO TO` in the program targets it.

    Args:
        st: The program's storage, unchanged by this paragraph.
    """
    # 716  exit section.
    _LOG.debug("fs-reply %s reads %r", st.file_access.fs_reply, st.ws_eval_msg)
    return


# ---------------------------------------------------------------------------
#  zz070-Convert-Date section.   [general/gl080.cbl:L719]
# ---------------------------------------------------------------------------


def _zz070_convert_date(st: _Gl080Storage) -> None:
    """`zz070-Convert-Date section.` - present the run date.

    [general/gl080.cbl:L719-L744]. Performed once, from
    [general/gl080.cbl:L285], to fill `ws-date` for the banner display and for
    the three walk headings that echo the cycle.

        719  zz070-Convert-Date     section.
        722  *>  Converts date in to-day to UK/USA/Intl date format
        724  *> Input:   to-day
        725  *> output:  ws-date as uk/US/Intl date format
        727      move     to-day to ws-date.
        729      if       Date-Form = zero
        730               move 1 to Date-Form.
        731      if       Date-UK
        732               go to zz070-Exit.
        733      if       Date-USA                *> swap month and days
        734               move ws-days to ws-swap
        735               move ws-month to ws-days
        736               move ws-swap to ws-month
        737               go to zz070-Exit.
        741      move     "ccyy/mm/dd" to ws-date.  *> swap Intl to UK form
        742      move     to-day (7:4) to ws-Intl-Year.
        743      move     to-day (4:2) to ws-Intl-Month.
        744      move     to-day (1:2) to ws-Intl-Days.

    DELEGATED WHOLE, BECAUSE THE SECTION IS BYTE-IDENTICAL IN EVERY PROGRAM THAT
    CARRIES IT. Agent Action Plan section 0.6.3 identifies these repeated date
    sections as the one place consolidation is unambiguously safe, "because the
    bodies are textually equivalent". So the body lives in the shared date module
    and this function is the call site rule R-5 requires, not a second copy.

    THE LOCAL REDEFINES BLOCK [general/gl080.cbl:L222-L243] IS THE INTERFACE IT
    FILLS - `ws-date` viewed three ways at once, as UK days/month/year, as the
    USA order, and as the international `ccyy/mm/dd` form, plus the two-character
    `ws-swap` the USA branch borrows. That block is declaration rather than
    behaviour, so it is the shared module's `WsDateFormats` here.

    WHAT THIS PROGRAM DOES NOT HAVE. There is NO `zz050-Validate-Date`, NO
    `zz060-Convert-Date` and NO wrapper section around the shared binary date
    program - `zz070` is `gl080`'s only date section, and its exit is named
    `zz070-Exit` [general/gl080.cbl:L746] to match. So the naming inconsistency
    recorded as anomaly A-22, where a wrapper is named after the interface
    copybook while its exit is named after the called program
    [general/gl070.cbl:L603-L609], DOES NOT OCCUR HERE. There is nothing to
    reproduce and nothing to omit.

    L729-L730 MUTATES A SYSTEM RECORD COLUMN AND IS THEREFORE DIFF-VISIBLE.
    `Date-Form` [copybooks/wssystem.cob] is a `SYSTEM-REC` column, and a run that
    finds it zero leaves it as 1. The shared function returns the EFFECTIVE form
    precisely so that the caller can store it back, which is the only way the
    mutation survives; it is stored back below. Whether the caller of `gl080`
    then persists the system record is AMBIGUITY Q-21.

    Args:
        st: The program's storage. Reads `to-day`, reads and writes
            `Date-Form`, and fills `ws-date` and its three redefined views.
    """
    # 727-744, as one call. `zz070_convert_date` takes the date text and the
    # declared form, fills every view of `ws-date`, and returns the form it
    # actually used - 1 when it found zero, which is L729-L730.
    #
    # THE SECTION'S TWO TRANSFERS ARE INSIDE THAT CALL, and both are the same
    # shape:
    #
    #   731  if       Date-UK
    #   732           go to zz070-Exit.
    #   GO TO class 3 - the UK form needs no rearrangement, so the section ends
    #   at [general/gl080.cbl:L746] with `ws-date` holding `to-day` unchanged.
    #
    #   733  if       Date-USA                *> swap month and days
    #   737           go to zz070-Exit.
    #   GO TO class 3 - the USA form swaps days and month through `ws-swap` and
    #   then ends the section, which is what keeps the international block at
    #   L741-L744 from running on top of the swap.
    #
    # Both are reproduced inside the shared function rather than here, because
    # the section body is textually identical in every program that carries it
    # and consolidating it is the one safe consolidation in this migration
    # (Agent Action Plan section 0.6.3). The exit paragraph they target still has
    # its own function below, as rule R-5 requires.
    effective_form = zz070_convert_date(
        st.ws_date_formats,
        st.to_day,
        st.system.system_data_block.date_form,
    )

    # 729  if       Date-Form = zero
    # 730           move 1 to Date-Form.
    # Storing the returned form back is what reproduces the mutation. When the
    # form was already 1, 2 or 3 the store is a no-op, exactly as the `if` makes
    # it a no-op in the frozen source.
    st.system.system_data_block.date_form = move.move(effective_form, _DATE_FORM)

    # 746  zz070-Exit.
    # Reached three ways in the frozen source: the class-3 transfers at
    # [general/gl080.cbl:L732] and [general/gl080.cbl:L737], and fall-through
    # from L744. All three are inside the shared function; the exit paragraph is
    # named here because rule R-5 requires a function per paragraph.
    _zz070_exit(st)


def _zz070_exit(st: _Gl080Storage) -> None:
    """`zz070-Exit.` / `exit section.`  [general/gl080.cbl:L746-L747].

    The target of the two class-3 transfers at [general/gl080.cbl:L732] and
    [general/gl080.cbl:L737], and of the fall-through from
    [general/gl080.cbl:L744].

    Args:
        st: The program's storage, unchanged by this paragraph.
    """
    # 747  exit     section.
    _LOG.debug(
        "run date %r presented as %r under date form %s",
        st.to_day,
        st.ws_date_formats.ws_date,
        st.system.system_data_block.date_form,
    )
    return


# ---------------------------------------------------------------------------
#  THE ENTRY POINT   [general/gl080.cbl:L269-L272]
# ---------------------------------------------------------------------------


def run(
    ws_calling_data: WsCallingData,
    system_record: SystemRecord,
    to_day: str,
    file_defs: FileDefs,
    *,
    file_access: FileAccess | None = None,
    dal_common: AcasDalCommonData | None = None,
    run_confirmed: bool = True,
    disk_change_option: int = 0,
    archive_path_override: str | None = None,
    dal_options: Mapping[str, object] | None = None,
) -> None:
    """`gl080` - General Ledger End Of Cycle Processing  [general/gl080.cbl].

    The whole program, entered exactly where the COBOL is entered. Its four
    positional parameters are the `PROCEDURE DIVISION USING` list, verbatim and
    in order::

         269  procedure division using ws-calling-data
         270                           system-record
         271                           to-day
         272                           file-defs.

    THE GENERAL LEDGER FOUR-PARAMETER SHAPE, one of the three linkage shapes in
    the migration. The Sales and Purchase families add a fourth system record;
    the IRS program takes neither the calling-data block nor the run date. This
    is the plain General Ledger form and no parameter is added to, removed from or
    reordered within it.

    ITS CALLER, AND WHAT THAT CALLER DOES NOT DO. `general.cbl` dispatches this
    program from `load09.` [general/general.cbl:L817-L820], which moves the
    program name and transfers to the shared `load00.` block
    [general/general.cbl:L711-L722]. That block zeroes the term code, issues the
    `CALL` with these four arguments, and tests `if ws-term-code > 7`. UNLIKE
    `load08`, IT HAS NO `= 5` GATE - and it does not need one, because `gl080`
    NEVER SETS A TERM CODE. Where `gl070` raises 5 to stop the cycle
    [general/gl070.cbl:L289], `gl080` simply returns [general/gl080.cbl:L366].
    So `ws_calling_data` is accepted and never read, which is why it is a
    parameter rather than a return value.

    THE PROMOTED PARAMETERS. Three interactive statements in the frozen source
    decide something a later statement acts on, and Agent Action Plan section
    0.3.4 turns exactly those into parameters "with the COBOL default preserved".
    Every one defaults to the answer that lets the program proceed:

    `run_confirmed`  from [general/gl080.cbl:L299-L302]. The run-confirm prompt;
        Escape or "A" makes the program `goback` before a single write. Default
        True, meaning proceed.
    `disk_change_option`  from [general/gl080.cbl:L545-L547]. THE CLEAREST
        DATABASE-GATING PROMPT IN THE FOLDER: 9 suppresses the archiving walk
        [general/gl080.cbl:L408-L409] AND the whole of end-of-period processing
        [general/gl080.cbl:L324-L326], so it stops every batch stamp, every
        posting delete, the ledger-quarter rollover and the cycle increment.
        Default 0, meaning proceed.
    `archive_path_override`  from [general/gl080.cbl:L555]. Edits where the flat
        archive rows are written. NO TABLE EFFECT - the archive is not a schema
        table. Default None, meaning keep the path `disk-change` computes at
        [general/gl080.cbl:L537].

    The acknowledgement pauses at [general/gl080.cbl:L311-L312],
    [general/gl080.cbl:L648] and [general/gl080.cbl:L696] are NOT parameters,
    because their only effect was to hold a terminal. They are dropped and the
    control transfers around them are kept.

    THE OTHER FOUR KEYWORD PARAMETERS ARE NOT PROMOTED PROMPTS. `file_access` and
    `dal_common` are two of the five arguments every handler `CALL` carries
    [copybooks/Proc-ACAS-FH-Calls.cob:L51-L57]; the COBOL program declares them
    in its own working storage rather than receiving them, so they default to
    fresh records and a caller that wants to observe `Fs-Reply` afterwards may
    pass its own. `dal_options` is forwarded verbatim into every
    `FacadeContext.options` and has no COBOL counterpart at all - it is how a
    caller reaches the data-access layer's own knobs without this module knowing
    what they are.

    DETERMINISM (rule R-6). Every date this program uses arrives here: the text
    date in `to_day` and the binary run date in `system_record`. There is no
    ambient clock anywhere in the module and the controlled-clock module is not
    imported - the two batch stamps at [general/gl080.cbl:L431] and
    [general/gl080.cbl:L586] read `Run-Date` [copybooks/wssystem.cob:L67] out of
    the record they were handed. Two runs with the same arguments write the same
    rows.

    Args:
        ws_calling_data: `01 WS-Calling-Data` [copybooks/wscall.cob:L6-L13].
        system_record: `01 System-Record` [copybooks/wssystem.cob]. READ AND
            MUTATED - `Scycle` at [general/gl080.cbl:L334],
            [general/gl080.cbl:L360] and [general/gl080.cbl:L363],
            `Current-Quarter` at [general/gl080.cbl:L355] and
            [general/gl080.cbl:L357], and `Date-Form` at
            [general/gl080.cbl:L730]. It is a by-reference linkage parameter, so
            the mutations are visible to the caller; whether the caller persists
            them is AMBIGUITY Q-21.
        to_day: `01 to-day pic x(10).` [general/gl080.cbl:L267], DD/MM/CCYY.
        file_defs: `01 File-Defs.` [copybooks/wsnames.cob:L13].
        file_access: `01 File-Access` [copybooks/wsfnctn.cob:L22]. A fresh
            record when omitted.
        dal_common: `01 ACAS-DAL-Common-data.`
            [copybooks/Test-Data-Flags.cob]. A fresh record when omitted.
        run_confirmed: See above. False reproduces Escape or "A".
        disk_change_option: See above. 9 reproduces the abort.
        archive_path_override: See above.
        dal_options: Forwarded to every handler.

    Raises:
        _StopRun: `stop run.` [general/gl080.cbl:L649], when `compress-post`
            finds the posting record and its work record are different lengths.
            The run unit ends; see AMBIGUITY Q-23 for when this can happen.
    """
    # BOTH FLAT FILES DECLARE `fs-reply` AS THEIR FILE STATUS
    # [general/gl080.cbl:L140], [general/gl080.cbl:L146], and that is the SAME
    # `Fs-Reply pic 99` [copybooks/wsfnctn.cob:L25] the handlers write. So the
    # record is built first and the two sequences are given THAT record, not one
    # of their own - giving each its own status would break the very test at
    # [general/gl080.cbl:L412], which reads a flat-file reply through the shared
    # field.
    access = file_access if file_access is not None else FileAccess()

    st = _Gl080Storage(
        ws_calling_data=ws_calling_data,
        system=system_record,
        to_day=to_day,
        file_defs=file_defs,
        file_access=access,
        dal_common=(
            dal_common if dal_common is not None else AcasDalCommonData()
        ),
        # `copy "wsledger.cob".` [general/gl080.cbl:L188]
        ledger=WsLedgerRecord(),
        # `copy "wsbatch.cob".` [general/gl080.cbl:L189]
        batch=GlBatchRecord(),
        # `copy "wspost.cob".` [general/gl080.cbl:L190] - a copy `gl072` does
        # NOT make, which is why this program can write and rewrite postings.
        posting=WsPostingRecord(),
        # `77 a pic 99 value zero.` [general/gl080.cbl:L183] and
        # `77 y pic 99 value zero.` [general/gl080.cbl:L182] - both `value zero`,
        # so both start at zero on entry.
        a=0,
        y=0,
        # `77 ws-eval-msg pic x(25).` [general/gl080.cbl:L185] - no VALUE clause,
        # so it starts space-filled to its declared width.
        ws_eval_msg=move.move_figurative(move.SPACE, _WS_EVAL_MSG),
        # The redefines block [general/gl080.cbl:L222-L243].
        ws_date_formats=WsDateFormats(),
        # `fd archive.` [general/gl080.cbl:L156] and `fd work-file.`
        # [general/gl080.cbl:L170], both sharing `access` above.
        archive=_ArchiveFile(access),
        work_file=_WorkFile(access),
        run_confirmed=run_confirmed,
        disk_change_option=disk_change_option,
        archive_path_override=archive_path_override,
        dal_options=dal_options if dal_options is not None else {},
    )

    # 275  gl080-Main section.   -   the program's entry section.
    _gl080_main(st)


# --- traceability ----------------------------------------------------------
#
# Rule R-5 requires that every program map to a module, every paragraph to a
# function and every field to a data-dictionary entry, and that the mapping be
# RECORDED rather than left implicit. This footer is that record for `gl080`.
#
# PROGRAM -> MODULE
#     general/gl080.cbl                 acas_posting/programs/gl080_end_of_cycle
#     Migration boundary: THE WHOLE PROGRAM. The plan's prose calls it "Phase 3
#     transaction deletion and Phase 5 end-of-period processing", which is a
#     description of the emphasis and NOT a carve-out - section 0.2.1.1 lists the
#     boundary as "Whole program", and only `gl051` and `irs030` are partial. So
#     the archiving path, the interactive path builder and the contraction
#     section are all migrated, not just the two phases the prose names.
#     Public API: `run` only. `__all__ = ("run",)`, and every other module-level
#     name begins with an underscore, because a caller cannot reach into a
#     program's internals any more than a COBOL `CALL` can (section 0.3.3).
#
# PARAGRAPH -> FUNCTION      -   all 38 labels, in source order
#
#     Six paragraphs are named `loop.`, seven `main-exit.` and three `end-run.`,
#     so EVERY ONE is section-qualified. Nothing is folded away: a paragraph
#     whose `GO TO` became a `continue`, a `break` or a `return` still has its own
#     function, per section 0.7.4 C-4.
#
#     L275  gl080-Main section.            _gl080_main
#     L339    loop.                        _gl080_main_loop
#     L351    loop-end.                    _gl080_main_loop_end
#     L365    main-end.                    _main_end
#     L368  gl080a section.                _gl080a
#     L374    loop.                        _gl080a_loop
#     L390    end-run.                     _gl080a_end_run
#     L395    main-exit.                   _gl080a_main_exit
#     L398  gl080b section.                _gl080b
#     L417    loop.                        _gl080b_loop
#     L436    end-run.                     _gl080b_end_run
#     L442    main-exit.                   _gl080b_main_exit
#     L445  arc-process section.           _arc_process
#     L452    loop.                        _arc_process_loop
#     L510    by-pass.                     _arc_process_by_pass
#     L516    main-exit.                   _arc_process_main_exit
#     L519  disk-change section.           _disk_change
#     L542    accept-option.               _disk_change_accept_option
#     L559    main-exit.                   _disk_change_main_exit
#     L562  gl080c section.                _gl080c
#     L572    loop.                        _gl080c_loop
#     L592    end-run.                     _gl080c_end_run
#     L597    main-exit.                   _gl080c_main_exit
#     L600  del-process section.           _del_process
#     L609    loop.                        _del_process_loop
#     L625    main-exit.                   _del_process_main_exit
#     L628  compress-post section.         _compress_post
#     L639    Test-Work-File-Size-1.       _compress_post_test_work_file_size_1
#     L654    loop1.                       _compress_post_loop1
#     L667    loop1-end.                   _compress_post_loop1_end
#     L675    loop2.                       _compress_post_loop2
#     L688    file-error.                  _compress_post_file_error
#     L699    loop2-end.                   _compress_post_loop2_end
#     L705    main-exit.                   _compress_post_main_exit
#     L710  Evaluate-Message Section.      _evaluate_message
#     L716    Eval-Msg-Exit.               _eval_msg_exit
#     L719  zz070-Convert-Date section.    _zz070_convert_date
#     L746    zz070-Exit.                  _zz070_exit
#
#     THREE FUNCTIONS HAVE NO COBOL LABEL and are named so that no reader mistakes
#     them for paragraphs:
#       _move_ledger_balance_to_quarter   the dual-view write that one statement,
#                                         [general/gl080.cbl:L345], needs because
#                                         a COBOL REDEFINES aliases storage that
#                                         Python does not - see STRUCTURAL NOTES
#       _archived_status                  reads `88 Archived value 2.`
#                                         [copybooks/wsbatch.cob:L32] once so the
#                                         two stamping sites are provably equal
#       _copy_posting_record              the independent snapshot a `WRITE` of a
#                                         shared record area requires
#
# STATEMENT -> CALL SITE
#
#     SIXTEEN DISTINCT FACADE VERBS, the largest set of any program in the folder,
#     all through the ENTITY-NAMED vocabulary because `gl080` copies
#     `Proc-ACAS-FH-Calls.cob` [general/gl080.cbl:L749]. That copybook has NO
#     error-check paragraph, so every `fs-reply` test in this module is the
#     caller's own, tested inline. The handler-named aliases published for the IRS
#     convention are NOT used here.
#       GL-Nominal-Open        L337   facade.gl_nominal_open
#       GL-Nominal-Read-Next   L342   facade.gl_nominal_read_next
#       GL-Nominal-Rewrite     L348   facade.gl_nominal_rewrite
#       GL-Nominal-Close       L354   facade.gl_nominal_close
#       GL-Batch-Open-Input    L372   facade.gl_batch_open_input
#       GL-Batch-Read-Next     L377, L420, L575    facade.gl_batch_read_next
#       GL-Batch-Close         L393, L440, L595    facade.gl_batch_close
#       GL-Batch-Open          L415, L570          facade.gl_batch_open
#       GL-Batch-Rewrite       L433, L589          facade.gl_batch_rewrite
#       GL-Posting-Open        L450, L607          facade.gl_posting_open
#       GL-Posting-Read-Next   L455, L612, L657    facade.gl_posting_read_next
#       GL-Posting-Close       L428, L583, L671, L703   facade.gl_posting_close
#       GL-Posting-Delete      L513, L622          facade.gl_posting_delete
#       GL-Posting-Open-Input  L651   facade.gl_posting_open_input
#       GL-Posting-Open-Output L673   facade.gl_posting_open_output
#       GL-Posting-Write       L683   facade.gl_posting_write
#     `gl080` is the ONLY in-scope program that performs `GL-Posting-Delete`, and
#     the only General Ledger program that performs `GL-Posting-Write` or
#     `GL-Posting-Open-Output`.
#
#     ASYMMETRIC OPEN/CLOSE PAIRS, preserved and not tidied. `GL-Posting-Open` is
#     performed INSIDE `arc-process` [general/gl080.cbl:L450] and inside
#     `del-process` [general/gl080.cbl:L607], while the matching
#     `GL-Posting-Close` sits in the OUTER section at [general/gl080.cbl:L428] and
#     [general/gl080.cbl:L583]. Moving either into the other's section would
#     change how many times the file is opened per batch.
#
#     THE COMPLETE ARITHMETIC CENSUS - nine statements, ONE of them rounded.
#       L328  divide scycle by period giving a ROUNDED
#             arithmetic.divide_by_giving(..., asking for rounding)  <- THE ONLY
#             CALL IN THIS MODULE THAT DOES
#       L329  multiply a by period giving y
#             arithmetic.multiply_by_giving(..., rounded=False)
#       L334  add 1 to scycle              arithmetic.add_to
#       L355  add 1 to current-quarter     arithmetic.add_to
#       L477  add post-amount vat-amount giving arc-amount   arithmetic.add_giving
#       L489  add post-amount vat-amount giving arc-amount   arithmetic.add_giving
#       L493  multiply arc-amount by -1 giving arc-amount
#             arithmetic.multiply_by_giving   ARCHIVE SIGN FLIP ONE
#       L506  multiply arc-amount by -1 giving arc-amount
#             arithmetic.multiply_by_giving   ARCHIVE SIGN FLIP TWO, conditional
#       L643-L644  two `function length` comparisons, both summed from the
#             dictionary's descriptors and compared with arithmetic.compare
#     [general/gl080.cbl:L328] is one of exactly FIVE `ROUNDED` sites in the whole
#     migration; the other four are [general/gl051.cbl:L791],
#     [general/gl051.cbl:L796], [irs/irs030.cbl:L1551] and
#     [irs/irs030.cbl:L1562]. Counting the rounding argument across this file
#     yields exactly ONE occurrence, at [general/gl080.cbl:L328].
#     L329 is un-`ROUNDED` and IMMEDIATELY FOLLOWS the rounded divide, which is
#     why rounding is a per-call argument here and never a module-level mode.
#     There is ZERO `ON SIZE ERROR` and ZERO `REMAINDER` in this program.
#
#     EVERY `MOVE`, `STRING` AND REFERENCE MODIFICATION IS DELEGATED to
#     `cobol.move` - `move`, `move_group`, `move_figurative`, `string_into`,
#     `ref_mod`. Nothing here joins text with an operator, trims whitespace,
#     slices a string, or re-scales a Decimal in place. Section 0.3.1, verbatim:
#     "`cobol/` contains no business logic and `programs/` contains no numeric
#     primitives."
#
#     EVERY CONDITION IS A CONDITION NAME, never a bare literal:
#       `archiving`                L315   condition_names.evaluate("Archiving", ..)
#       `not status-closed`        L384   condition_names.is_status_closed
#       `not processed`            L385   condition_names.is_processed
#       `move 2 to cleared-status` L430, L585   values_for("Archived")
#       `not FS-Cobol-Files-Used`  L633   evaluate("FS-Cobol-Files-Used", ..)
#     and every file-status test reads `FsReply.SUCCESS` or `FsReply.END_OF_FILE`
#     rather than 0 or 10.
#
# `GO TO` CLASSIFICATION      -   36 transfer sites, every one annotated
#
#     Classified BY SHAPE rather than by matching the plan's label list, which is
#     not exhaustive for this program: `loop-end`, `by-pass`, `loop1`,
#     `loop1-end`, `loop2`, `loop2-end`, `file-error`, `accept-option` and
#     `main-end` are all targets here and none of them appears in it.
#
#     CLASS 1 - loop-back, `continue`                                   15 sites
#       L349, L382, L388, L425, L434, L461, L514, L549, L557, L580, L590, L618,
#       L623, L665, L686
#       L549 and L557 target `accept-option` and are INTERACTIVE RETRIES. The
#       re-prompt is dropped with the prompt (section 0.4.2) and the DECISION each
#       retry guarded is kept - see PROMOTED PARAMETERS.
#
#     CLASS 2 - forward terminator, `break` PLUS the post-loop block      6 sites
#       L344 -> loop-end  L351      L379 -> end-run  L390
#       L422 -> end-run   L436      L577 -> end-run  L592
#       L659 -> loop1-end L667      L679 -> loop2-end L699
#       Section 0.6.3 warns that mis-splitting a class 2 site "would silently drop
#       end-of-run processing". THE SITE WHERE THAT BITES HARDEST IS L344, whose
#       post-loop block [general/gl080.cbl:L354-L363] carries the nominal close,
#       the quarter increment, the quarter wrap and BOTH cycle wraps. Losing it
#       would lose the entire period rollover, silently. It is placed after the
#       loop in `_gl080_main`, not inside `_gl080_main_loop`.
#
#     CLASS 3 - section or paragraph exit, `return`                      10 sites
#       L313, L326, L332 -> main-end   L365
#       L409 -> gl080b main-exit       L442
#       L457 -> arc-process main-exit  L516
#       L547 -> disk-change main-exit  L559
#       L614 -> del-process main-exit  L625
#       L634 -> compress-post main-exit L705
#       L732, L737 -> zz070-Exit       L746   (inside the shared date function)
#
#     CLASS 4 - named call plus an explicit transfer                      5 sites
#       Each proved individually below, because this is the only class where the
#       target performs work and then transfers control itself.
#
#       PROOF 1 - L499 -> `by-pass.` L510
#         `by-pass` performs `GL-Posting-Delete` [general/gl080.cbl:L513] and then
#         `go to loop` [general/gl080.cbl:L514]. So the transfer is equivalent to:
#         run `by-pass`, then continue the loop. Reproduced as
#         `_arc_process_by_pass(st)` followed by `continue`.
#         WHY THIS MATTERS: `gl070`'s equivalent tax-suppression transfer is
#         `go to loop` [general/gl070.cbl:L523], which ABANDONS the record. Here
#         the delete still happens, so a posting with no tax is archived in two
#         legs and STILL DELETED. Reusing `gl070`'s shape would leave every
#         tax-free posting behind.
#
#       PROOF 2 - L661 -> `file-error.` L688,  inside `loop1`
#         `file-error`'s last statement is L697 and there is NO transfer after it,
#         so control FALLS THROUGH into `loop2-end.` [general/gl080.cbl:L699].
#         Equivalent to: run `file-error`, run `loop2-end`, leave the section.
#         Reproduced as `_compress_post_file_error(st)` then
#         `_compress_post_loop2_end(st)` then return.
#         CONSEQUENCE: `loop1-end.` NEVER RUNS, so the two closes at
#         [general/gl080.cbl:L670-L671], the `open input work-file` at L672 and
#         the `GL-Posting-Open-Output` at L673 are all skipped. The files close
#         through L702-L703 instead, and nothing empties the posting file.
#
#       PROOF 3 - L664 -> `file-error.` L688,  inside `loop1`
#         Identical composition and the same skipping of `loop1-end.`. Differs
#         only in which statement failed - a write rather than a read - so a row
#         may be half-copied to the scratch sequence while the posting file is
#         untouched.
#
#       PROOF 4 - L681 -> `file-error.` L688,  inside `loop2`
#         Same fall-through. Here the transfer skips nothing the loop would not
#         have reached anyway, because `loop2-end.` is this loop's own terminator.
#         Its effect is to end the rebuild early: the posting file was emptied at
#         L673 and is left partly rebuilt, and NO transaction wrapper rolls that
#         back (rule R-3).
#
#       PROOF 5 - L685 -> `file-error.` L688,  inside `loop2`
#         As proof 4, with the failure in the write back rather than the read. The
#         failed row is missing from the rebuilt table and every row after it is
#         never attempted.
#
#     `PERFORM ... THRU` DOES NOT OCCUR IN `gl080`. The in-scope sites are in
#     `gl072`, `sl100`, `pl100` and `irs030`; there is none here and none was
#     hunted for. The `file-error` -> `loop2-end` fall-through is the same class of
#     hazard, and it is handled with the same explicit composition and the same
#     per-site care.
#
# PROMOTED PARAMETERS      -   interactive prompts promoted per section 0.3.4
#
#     Three prompts in the frozen source decide something a later statement acts
#     on. Each becomes a keyword-only parameter of `run` defaulting to the COBOL's
#     proceed answer.
#
#     run_confirmed          [general/gl080.cbl:L299-L302]   default True
#         `accept keyed-reply at 1065` then `if cob-crt-status = cob-scr-esc or
#         keyed-reply = "A" or "a" goback.` Escape or "A" ends the program BEFORE
#         ANY WRITE AT ALL. Interactive prompt promoted to a parameter per
#         section 0.3.4.
#
#     disk_change_option     [general/gl080.cbl:L545-L547]   default 0
#         `accept a at 1369` then `if a = 9 go to main-exit.` THE CLEAREST
#         DATABASE-GATING PROMPT IN THE FOLDER. The value lands in `a`, and 9 is
#         then read twice: at [general/gl080.cbl:L408-L409] to skip the archiving
#         walk, and at [general/gl080.cbl:L324-L326] to skip the whole of
#         end-of-period processing. One keystroke therefore suppresses every batch
#         stamp, every posting delete, the ledger-quarter rollover and the cycle
#         increment. Interactive prompt promoted to a parameter per section 0.3.4.
#
#     archive_path_override  [general/gl080.cbl:L555]        default None
#         `accept file-2 at 1501 with update`. Gates WHERE the flat archive rows
#         are written, which is not a schema table, so it has NO TABLE EFFECT.
#         None keeps the path [general/gl080.cbl:L537] computes. Interactive
#         prompt promoted to a parameter per section 0.3.4.
#
#     NOT PROMOTED, because they gate nothing: the acknowledgement pauses at
#     [general/gl080.cbl:L311-L312], [general/gl080.cbl:L648] and
#     [general/gl080.cbl:L696]. All three are dropped and ALL THREE CONTROL
#     TRANSFERS AROUND THEM ARE KEPT - `go to main-end` at L313, `stop run` at
#     L649, and the fall-through after L697.
#
#     NOT PROMPTS AT ALL: `file_access`, `dal_common` and `dal_options`. The first
#     two are working-storage records every handler `CALL` carries as its third
#     and fifth arguments; the third is Python plumbing with no COBOL counterpart,
#     forwarded verbatim into `FacadeContext.options`.
#
# ANOMALY REGISTER      -   reproduced, never fixed (rule R-4)
#
#     Section 0.8.2, verbatim: "A defect reproduced is correct; a defect fixed is
#     a failure." Section 0.7.4 C-4 prescribes a comment at each reproduction site
#     citing the COBOL locator, and that is where engineering quality is expressed
#     here rather than through correction.
#
#     A-2  THE UNBOUNDED QUARTER SUBSCRIPT.
#          [general/gl080.cbl:L328] computes `a` with a `ROUNDED` divide and
#          [general/gl080.cbl:L345] uses it to subscript `05 Ledger-Q ... occurs
#          4.` [copybooks/wsledger.cob:L36] with NO bounds check anywhere. `a` is
#          `pic 99`, so its domain is 0..99 against a table of 4. Reproduced in
#          `_gl080_main_loop` / `_move_ledger_balance_to_quarter`; NO GUARD ADDED,
#          because the missing guard IS the anomaly. The subscript is resolved
#          through the declared occurrence range so that an out-of-range value
#          fails loudly rather than silently wrapping to the last quarter the way
#          a negative Python index would - the divergence from COBOL's silent
#          overwrite of adjacent storage is AMBIGUITY Q-19, and it is neither
#          pre-empted with a check nor swallowed.
#
#     A-3  TWO DISAGREEING NOTIONS OF "CURRENT QUARTER".
#          The computed subscript `a` [general/gl080.cbl:L328],
#          [general/gl080.cbl:L345] and the independent rotating counter
#          `Current-Quarter` [copybooks/wssystem.cob:L110] incremented and wrapped
#          at [general/gl080.cbl:L355-L357], and consulted on its own at
#          [general/gl080.cbl:L346]. They are never reconciled. Both are kept, and
#          the plan's own range for the entry, [general/gl080.cbl:L345-L357], is
#          cited at the site.
#
#     A-21 QUALIFIED REFERENCES FORCED BY FIELD-NAME COLLISIONS across three
#          posting copybooks. THREE SITES IN THIS PROGRAM, in both spellings:
#          [general/gl080.cbl:L467] writes `post-code in WS-Posting-Record` with
#          `in`, while [general/gl080.cbl:L497] and [general/gl080.cbl:L501] write
#          `vat-ac of WS-Posting-Record` with `of`. Each is commented at its site.
#
#     THE TWO ARCHIVE SIGN FLIPS, [general/gl080.cbl:L493] and
#          [general/gl080.cbl:L506], are named explicitly in sections 0.4.1.2 and
#          0.6.1 as behaviour to preserve. They are not registered anomalies, and
#          each carries its locator at its site. L493 is UNCONDITIONAL; L506 fires
#          only when the tax sits on the CR side.
#
#     THE LENGTH MISMATCH IN `compress-post` is reproduced rather than corrected.
#          `01 WS-Posting-Record.` measures 103 and `01 work-file-record pic
#          x(101).` measures 101, so [general/gl080.cbl:L643-L644] is true and
#          `stop run` fires. The maintainer's own comment on
#          [general/gl080.cbl:L172] shows the intent - "Was 96 added 5 for
#          WS-Post-rrn (9(5)" - and that 96 is an arithmetic slip for 98. NOTHING
#          HERE WIDENS THE WORK RECORD and nothing skips the test. See AMBIGUITY
#          Q-23.
#
# STRUCTURAL NOTES      -   decisions a reader should not have to infer
#
#     1.  THE TWO FLAT FILES ARE DECLARED MODULE-PRIVATELY, AND WHY.
#         `fd archive.` [general/gl080.cbl:L156-L168] and `fd work-file.`
#         [general/gl080.cbl:L170-L172] are neither schema tables nor cycle work
#         files. The package's work-file layer publishes only `pre_trans`,
#         `post_trans` and `sort_trans`, and its open modes deliberately exclude
#         extend - which [general/gl080.cbl:L411] requires - so it cannot serve
#         them, and that folder is closed to new files. RESOLUTION: both layouts
#         are declared here through `cobol.picture` with `source_locator`
#         "general/gl080.cbl:L158-L168" and "general/gl080.cbl:L172", and both
#         sequences are modelled as ordered in-memory lists with insertion order
#         absolute and `open output` truncating. NEITHER REACHES THE DATABASE, so
#         neither appears in any table dump.
#         `arc-trans-record` IS TEN FIELDS AND 78 CHARACTERS, and its field order
#         is NOT the cycle work record's: `arc-amount` sits BEFORE `arc-legend`,
#         and the contra pair `arc-c-ac`/`arc-c-pc` comes AFTER it.
#         BOTH FILES DECLARE `fs-reply` AS THEIR FILE STATUS
#         [general/gl080.cbl:L140], [general/gl080.cbl:L146], which is the same
#         `Fs-Reply pic 99` [copybooks/wsfnctn.cob:L25] the handlers write, so
#         both share the one `File-Access` record and a facade verb performed
#         straight after a flat-file operation overwrites its reply. That sharing
#         is reproduced, not tidied.
#
#     2.  `work-file` IS ASSIGNED `file-21`, THE SAME NAME `gl071` GIVES ITS SORT
#         WORK FILE [general/gl071.cbl:L102] - a genuine collision between two
#         programs' scratch files, both resolving to `work.tmp`. It has no effect
#         because the two never run at the same time, and rule R-3 forbids
#         concurrency in any case. Recorded because surfacing exactly this kind of
#         fact is what traceability is for.
#
#     3.  HOW A GROUP'S BYTE IMAGE IS MODELLED IN `compress-post`. Rendering the
#         fifteen elementary items of `WS-Posting-Record` into zoned bytes needs
#         the byte-layout module, which a program module may not import (section
#         0.4.3), and hand-rolling that layout is forbidden outright (section
#         0.3.1). So the two group moves at [general/gl080.cbl:L662] and
#         [general/gl080.cbl:L682] carry the WIDTH through `cobol.move` against
#         the two descriptors, and the field values travel beside the image as an
#         independent snapshot. That is exact under the precondition the source
#         itself establishes two paragraphs earlier: `Test-Work-File-Size-1`
#         refuses to proceed unless the records are the SAME WIDTH, and at equal
#         widths the write-then-read round trip is the identity. AMBIGUITY Q-23
#         records that no execution of the frozen source can observe the
#         difference in any case.
#
#     4.  `a` IS ONE FIELD WITH THREE UNRELATED PURPOSES, and it is modelled as
#         one field. `77 a pic 99 value zero.` [general/gl080.cbl:L183] is the
#         batch-check detector flag (L290, L386, L308), the `disk-change` abort
#         code (L545, L408, L324) AND the quarter subscript (L328, L345). The
#         `ROUNDED` divide at L328 OVERWRITES whatever it held, including the 9
#         that L324 has just tested. Splitting it into three well-named locals
#         would lose an observable behaviour, so it is not split; the triple use is
#         commented where it is set and where it is read.
#
#     5.  `ledger-q (a)` NEEDS A DUAL-VIEW WRITE, and this is a Python-versus-COBOL
#         storage fact rather than a behaviour change. `05 Ledger-Q ... occurs 4.`
#         [copybooks/wsledger.cob:L36] REDEFINES `Ledger-Q1` through `Ledger-Q4`
#         [copybooks/wsledger.cob:L31-L34], so in COBOL they are the SAME BYTES; in
#         Python they are separate attributes that do not alias. The nominal
#         handler's column bindings load from the NAMED fields, and its alignment
#         step refreshes the table FROM those names on the read path only. So a
#         write through the table alone would never reach the database.
#         `_move_ledger_balance_to_quarter` writes BOTH views from the one
#         statement, deriving the names from the dataclass and the count from the
#         descriptor's own `occurs` rather than hard-coding four.
#
#     6.  `stop run` IS A MODULE-PRIVATE EXCEPTION, `_StopRun`, AND NOT A REUSED
#         ONE. The package publishes `FacadeGoback`, whose own documentation rules
#         it out here: it reproduces `goback`, which returns to the CALLING program
#         and is "an exception and not a process exit on purpose". `stop run` ends
#         the RUN UNIT, so the caller's remaining work does not happen either -
#         the opposite instruction. The handler layer draws the same distinction
#         from the other side [common/acas007.cbl:L561]. It is RAISED, never
#         swallowed, and never turned into an interpreter exit: raising lets a
#         caller and a test observe
#         the abort, and a process exit would make the condition untestable.
#
#     7.  THE MESSAGE TABLE IS TRANSCRIBED, NOT EXTENDED. `Evaluate-Message`
#         [general/gl080.cbl:L710-L714] is one `copy ... replacing`, and its
#         thirty-two `WHEN` clauses plus `WHEN OTHER` are transcribed from
#         [copybooks/FileStat-Msgs.cpy:L23-L60] in the copybook's own order. The
#         copybook is inside this program's `COPY` closure and therefore in scope.
#         Diagnostic only: no branch reads the text, and it reaches no table.
#         The local spelling `Evaluate-Message` is kept - `pl060` spells it the
#         same [purchase/pl060.cbl:L1037] while `sl060` spells it
#         `zz040-Evaluate-Message` [sales/sl060.cbl:L1183].
#
# OMISSIONS      -   recorded as omissions so nothing looks lost
#
#     Section 0.4.3, verbatim, on the pattern the first entry belongs to: the
#     block "maps to nothing - recorded in the traceability document as a
#     representation-only omission so that a reader comparing the two files does
#     not conclude something was lost."
#
#     1.  THE UNUSED FACADE STUB BLOCK, `01 Dummies-4-Unused-ACAS-FH-Calls.`
#         [general/gl080.cbl:L194] through `03 WS-OTM5-Record pic x.`
#         [general/gl080.cbl:L214]. Declared purely so the linker resolves the
#         facade copybook's full verb set. Python has no equivalent need, so THERE
#         IS NO PYTHON STAND-IN FOR IT. Four entries inside the block are
#         COMMENTED OUT - `Default-Record` L195, `WS-Ledger-Record` L198,
#         `WS-Posting-Record` L199 and `WS-Batch-Record` L200 - which is the tell
#         that `gl080` really uses those four records.
#         A SECOND, INDEPENDENT OCCURRENCE OF A PATTERN THE PLAN RECORDS ONLY FOR
#         `gl072`. There the block is [general/gl072.cbl:L135-L155] and only THREE
#         entries are commented out, because `gl072` does not copy `wspost.cob`
#         and keeps `WS-Posting-Record` as a live stub. `gl080` DOES copy it
#         [general/gl080.cbl:L190], which is what lets it write and rewrite
#         postings.
#     2.  EVERY `display ... at` BECOMES A LOG RECORD. They must not alter control
#         flow and must not appear in any table dump (section 0.3.4). The sites:
#         L283-L287, L295-L297, L306, L309-L310, L316, L319, L336, L371,
#         L401-L404, L448, L463, L539-L540, L553-L554, L565-L568, L606, L620,
#         L637, L645-L647, L691-L695, L697.
#     3.  `set ENVIRONMENT ... to ...` L280-L281 - representation only.
#     4.  `copy "envdiv.cob".` L131 - the environment division.
#     5.  `copy "screenio.cpy".` L219 and `01 accept-terminator-array` L218 -
#         screen plumbing.
#     6.  `77 prog-name pic x(15) value "gl080 (3.3.00)".` L181 - a display
#         literal.
#     7.  `accept keyed-reply` at L311-L312, L648 and L696 - acknowledgement
#         pauses, DROPPED; the transfers around them are PRESERVED.
#     8.  `77 keyed-reply pic x.` L184 and the screen-status names
#         `cob-crt-status` / `cob-scr-esc` - the mechanism is omitted, the
#         Escape-or-"A" DECISION is promoted to `run_confirmed`.
#     9.  `lin2` at L291, L402 and L566 - display only; it is `Lin2`
#         [copybooks/wsfnctn.cob:L33] and reaches no table.
#     10. `01 Error-Messages.` L245-L256, i.e. `GL012` and `GL081` through
#         `GL088` - literals kept only insofar as they become log text.
#     11. `77 ws-eval-msg pic x(25).` L185 and the message table it receives -
#         diagnostic only, no control-flow effect.
#     12. The `archive` and `work-file` sequences and their `arc-trans-record` and
#         `work-file-record` layouts are IN-MEMORY ONLY and reach no table; see
#         STRUCTURAL NOTES 1 and 3.
#
#     STATED EXPLICITLY BECAUSE IT WAS CHECKED: there is NO
#     `call "SYSTEM" using Print-Report` anywhere in `general/gl080.cbl`, no print
#     file, no `zz050-Validate-Date`, no `zz060-Convert-Date` and no wrapper
#     section around the shared binary date program - so ANOMALY A-22, which is a
#     naming inconsistency between such a wrapper and its exit label
#     [general/gl070.cbl:L603-L609], DOES NOT OCCUR IN THIS MODULE. `gl080`'s only
#     date section is `zz070-Convert-Date` L719 with exit `zz070-Exit` L746, whose
#     names agree.
#
# AMBIGUITIES      -   settled by the compiled program, not by argument (rule R-6)
#
#     Each is raised with an `AMBIGUITY Q-nn` comment at the site that raises it.
#     Q-1 through Q-17 are already taken by sibling modules, so these begin at 18.
#
#     Q-18  `move 1 to File-Key-No.` [general/gl080.cbl:L288]. The facade's
#           dispatch pins the key number to the primary key on every verb, so
#           whether this move has any observable effect at all is open.
#     Q-19  What the compiled program does at `ledger-q (a)`
#           [general/gl080.cbl:L345] when `a` is 0 or greater than 4. COBOL
#           silently reads or writes adjacent storage; the migration must know
#           WHICH storage before it can claim to reproduce it.
#     Q-20  Whether `acas006`'s `Open-Output` [general/gl080.cbl:L673] TRUNCATES
#           `GLPOSTING-REC`, the way the transfer-file handler's does
#           [common/acas008.cbl:L313-L319]. If it does, that one statement empties
#           the posting table. NO GUARD IS ADDED (rule R-3).
#     Q-21  Whether the caller persists the system record this program mutates -
#           `Scycle` at L334, L360, L363, `Current-Quarter` at L355, L357 and
#           `Date-Form` at L730. `gl080` performs NO `System-*` facade verb, so the
#           six stores are in-memory unless the caller writes the record back.
#     Q-22  What path the `STRING` at [general/gl080.cbl:L531-L536] actually
#           produces, given the maintainer's own inline `*> this lot looks wrong
#           !!!!!` at L530. Measured against the package's record defaults it
#           yields a single segment with a space where a directory separator
#           belongs, because the first source is all spaces and the delimiter
#           defaults to a space.
#     Q-23  Whether ANY execution of the frozen source can reach
#           `compress-post`'s loops. The relational configuration returns at
#           [general/gl080.cbl:L634]; the indexed configuration reaches
#           [general/gl080.cbl:L643-L644], whose measured lengths - 103 against
#           101 - make the test true and fire `stop run` at L649. Both lengths are
#           computed from the dictionary's descriptors, so the test follows the
#           records rather than a typed-in number, and the oracle question is
#           whether GnuCOBOL 3.2 reports the same two values.
#
# CITATION CORRECTIONS      -   measured against the frozen source
#
#     Recorded so that no later reader rediscovers them as defects.
#     * THE PHASE 5 LABEL IS AT [general/gl080.cbl:L336], not L330. Section 0.6.4
#       cites L330; the `display` is at L336.
#     * THE PLAN NAMES ONLY TWO OF THIS PROGRAM'S FIVE PHASE LABELS. `gl080`
#       displays "Phase - 1.  Batch Check" at L306, "Phase - 2.  Transaction
#       Archiving" at L316, "Phase - 3.  Transaction Deletion" at L319,
#       "Phase - 5.  End of Period Processing" at L336 AND "Phase - 4.  Posting
#       Contraction " at L637. Two of them COLLIDE with other programs' numbering:
#       `gl070`'s Phase 1 is also "Batch Check" [general/gl070.cbl:L284] but its
#       Phase 2 is "Transaction Pre-process" [general/gl070.cbl:L292], and
#       `gl072`'s Phase 4 is "Transaction Update" [general/gl072.cbl:L274]. The
#       numbering is not an execution order and the module docstring says so.
#     * `gl080c`'S STAMPING IS AT [general/gl080.cbl:L585-L589]. Section 0.4.1.2
#       describes it and supplies no locators.
#     * THE STUB-BLOCK OMISSION OCCURS IN `gl080` TOO, at
#       [general/gl080.cbl:L194-L214]. Section 0.4.3 records the pattern only for
#       `gl072`.
#     * THE `MOVE` AT [general/gl080.cbl:L537] PADS; IT DOES NOT TRUNCATE. It is
#       described as "a truncating `MOVE` across very unequal widths", but
#       `Arg-Test` is `pic x(525)` [general/gl080.cbl:L187] and `file-2` is
#       `pic x(532)`, so the receiver is the WIDER of the two and the move
#       space-fills. Nothing is lost at that statement.
#     * `gl080` SETS NO TERM CODE, so the abort chain does not reach it. Its
#       caller `load09.` [general/general.cbl:L817-L820] transfers to the shared
#       `load00.` block [general/general.cbl:L711-L722], which tests only
#       `if ws-term-code > 7`; unlike `load08` it has no `= 5` gate, and needs
#       none. `gl080`'s own aborts are three local returns and one `stop run`.
#
# --- end traceability -----------------------------------------------------

