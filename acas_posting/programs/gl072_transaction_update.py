"""`gl072` - General Ledger Phase 4, Transaction Update  [general/gl072.cbl].

The migration of `general/gl072.cbl` in its entirety - 498 lines, thirteen
procedure-division labels, boundary THE WHOLE PROGRAM. This is the program that
actually posts money into the nominal ledger, and it is simultaneously the
smallest database footprint in the General Ledger family and the highest
consequence one.

    display  "Phase - 4.  Transaction Update" at 0801
                                              [general/gl072.cbl:L274]

FOUR STATEMENTS ARE THE WHOLE DATABASE EFFECT
=============================================
Everything else in the file - and it is the large majority of it - is print-file
construction. The four that reach a table are:

    331      add      post-amount  to  ledger-balance.      the accumulation
    375      move     1  to  cleared-status.                 the batch stamp
    376      move     run-date  to  posted.                  the batch stamp
    377      perform  GL-Batch-Rewrite.                      the batch UPDATE
    382      perform  GL-Nominal-Rewrite.                    the ledger UPDATE

Get those four right and the scenario state diff is empty even if every print
line is wrong; get one of them wrong and nothing else can save the run. They are
marked `THE POSTING` and `DATABASE EFFECT` at their sites below, and every other
statement in the module is scaffolding around them.

`gl072` mutates exactly TWO tables, `GLLEDGER-REC` and `GLBATCH-REC`, and only by
`REWRITE`. It inserts nothing and deletes nothing: there is no `Write` verb, no
`Delete` verb and no `Delete-All` verb anywhere in it, and - unlike `gl070`,
which writes the posting stream - it does not touch the posting table at all. It
copies no posting-record layout, because it reads the `post-trans` WORK SEQUENCE
rather than a table.

THE PHASE NUMBERS ARE NOT AN EXECUTION ORDER
============================================
The programs label their own phases on screen, and the labels do not run in
numeric order:

    "Phase - 1.  Batch Check"               [general/gl070.cbl:L284]
    "Phase - 2.  Transaction Pre-process"   [general/gl070.cbl:L292]
    (the sort, unlabelled)                  [general/gl071.cbl:L172-L178]
    "Phase - 4.  Transaction Update"        [general/gl072.cbl:L274]  <- HERE
    "Phase - 3.  Transaction Deletion"      [general/gl080.cbl:L319]
    "Phase - 5.  End of Period Processing"  [general/gl080.cbl:L336]

Phase 3 runs AFTER phase 4. Agent Action Plan section 0.6.4 asks that the labels
be preserved "so a maintainer is not misled", which is why the ordering is stated
here rather than left to be inferred from the numbering.

THE PRODUCER / CONSUMER CHAIN, AND WHY ORDER IS CORRECTNESS
===========================================================
    `gl070` phase 2 writes `pre-trans`     [general/gl070.cbl:L495-L533]
    `gl071` sorts it into `post-trans` on `(batch, ac, pc, post)` ascending
                                           [general/gl071.cbl:L172-L178]
    `gl072` reads `post-trans` SEQUENTIALLY and posts
                                           [general/gl072.cbl:L286], [:L408]

This module is the third link and it has NO error handling for a mis-ordered
stream. Agent Action Plan section 0.6.4, ordering dependency 1, verbatim:

    "Any change in sort stability or key composition produces silent
    misposting - no error, no diagnostic, wrong balances."

That is anomaly A-14, reproduced in `_new_account` below.

IT MAY NEVER RUN AT ALL
=======================
The General Ledger menu dispatches the cycle from one paragraph,
`load08.` [general/general.cbl:L805-L815]:

    move     "gl070" to ws-called.
    perform  load00.
    if       ws-term-code = 5
             go to display-menu.
    move     "gl071" to ws-called.
    perform  load00.
    move     "gl072" to ws-called.
    go       to load00.

`gl070` sets `move 5 to ws-term-code` [general/gl070.cbl:L289] on finding a
batch left open, and the test at [general/general.cbl:L810-L811] then returns to
the menu - so `gl071` AND `gl072` are skipped entirely. AN UNTOUCHED LEDGER
AFTER AN ABORTED RUN IS CORRECT. Nothing below checks for that case, and nothing
below checks for an empty `post-trans` either: the very first `read` reports at
end, `_end_account` and `_end_batch` run against their initial state, and the run
closes. That is the `test_empty_batch` scenario.

THE `999` SENTINEL IS THE SUBTLEST THING IN THE PROGRAM
=======================================================
`999` is NOT an error code. It is `WeError.NOT_USED`, the handler vocabulary's
"not used" sentinel [copybooks/wsfnctn.cob:L23], and `get-batch` borrows it as a
private flag meaning "this batch is not `Waiting`, so skip its transactions". It
is set in one place, survives across loop iterations in a working-storage field,
and is tested in three places with three different effects:

    get-batch  L458  if not waiting  ->  L459  move 999 to we-error
                                        L460  move 0   to save-batch
                     |
                     | called from headings L346
                     v
    headings   L348  if we-error equal 999 -> L349 go to headings-end
                     (so the page never prints, and `line-cnt` is NOT reset
                      to 5 at L367)
                     |
                     | headings returns into loop
                     v
    loop       L296  and we-error not = 999
                     (suppresses the batch-break close, third of three ANDs)
    loop       L306  if we-error equal 999 -> L307 go to loop
                     (SILENT SKIP #2 - anomaly A-13, site b)

Note the ORDER at L294-L307: the batch-break block at L297-L300 closes the
PREVIOUS account and the PREVIOUS batch and then calls `headings`, which is what
SETS the sentinel; only then does L306 test it. So a batch that `get-batch` has
just marked 999 still closes its predecessor first. Reversing those two blocks
would leave the previous batch unstamped.

`get-batch` also zeroes `save-batch` at L460, which means the next record
re-enters the L302 branch and calls `headings` again - so `get-batch` runs once
per record for as long as the batch stays un-`Waiting`.

TWO ENTIRELY SILENT SKIPS  (anomaly A-13)
=========================================
    291      if       post-batch  not numeric
    292               go to  loop.                      site (a)

    306      if       we-error  equal  999
    307               go to  loop.                      site (b)

No message, no counter, no trace. Agent Action Plan section 0.6.5, verbatim:
"Both are silent - no message, no counter, no trace. The Python equivalent must
be equally silent; adding a warning would be an added behavior." There is
therefore NO `logger` call of any kind on either path, and this module contains
no warning-level or error-level logging at all - its single log record is the
phase banner. The code COMMENT citing the locator is required by rule R-4; a
RUNTIME trace is forbidden by rule R-3.

THE `read-ledger` FLAG SUPPRESSES THREE THINGS, NOT ONE
=======================================================
`read-ledger pic x value space` [general/gl072.cbl:L162] is set to `"R"` in
exactly one place, the page-overflow path [general/gl072.cbl:L338], and reset to
space at the end of `new-account` [general/gl072.cbl:L431]. While set it
suppresses THREE separate things inside `new-account`, under three SEPARATE `if`
statements that must not be merged:

    407  if read-ledger not = "R"   ->  408  perform GL-Nominal-Read-Next
    410  if read-ledger not = "R"   ->  411  move zero to tot-dr tot-cr
    (413-419 run UNCONDITIONALLY, including `perform zz070-convert-date` L418)
    421  if read-ledger not = "R"   ->  422-427 the brought-forward split

So a page break re-prints the account's heading line WITHOUT advancing the
sequential read and WITHOUT resetting the running totals - which is the whole
point: the account has not changed, only the paper has.

A PAGE BREAK REWRITES THE SAME ACCOUNT AGAIN
============================================
    335      if       line-cnt > Page-Lines
    336               perform  end-account          <- GL-Nominal-Rewrite
    337               perform  headings
    338               move     "R"  to  read-ledger
    339               perform  new-account.

`end-account` begins with `perform GL-Nominal-Rewrite` [general/gl072.cbl:L382],
so a page break issues an EXTRA `UPDATE` of the account it is in the middle of,
with content identical to what is already there. It is invisible in a
final-state diff and visible in statement order. Reproduced exactly; the
"redundant" rewrite is NOT suppressed. See AMBIGUITY Q-20.

`end-account` IS CALLED BEFORE `end-batch` AND DECLARED AFTER IT
===============================================================
    call sites   L287-L288  perform end-account / perform end-batch  (at end)
                 L297-L298  perform end-account / perform end-batch  (break)
    declarations L372       end-batch.
                 L379       end-account.

The declaration order is the reverse of the call order. Agent Action Plan
section 0.6.4: "Inverting them would produce a batch marked posted with an
unclosed final account." The functions below are declared in SOURCE order, so
`_end_batch` precedes `_end_account` in this file exactly as the paragraphs do,
and both call sites invoke them account-first.

`perform headings` APPEARS IN THREE DIFFERENT FORMS
==================================================
    300      perform  headings  through  headings-end.     `PERFORM ... THRU`
    304      perform  headings  through  headings-end.     `PERFORM ... THRU`
    337      perform  headings                             BARE, no range

`headings-end.` [general/gl072.cbl:L369] has an EMPTY BODY, so the bare form and
the range form are behaviourally identical here - but rule R-5 requires the
distinction be recorded, and the two range sites are two of only FOUR
`PERFORM ... THRU` sites inside the whole in-scope migration surface. Each is
hand-verified at its site below, with no pattern-matching shortcut.

`headings` IS NOT PURELY PRESENTATIONAL
=======================================
Every line of it except two is print construction, and the two are load-bearing:
`perform get-batch` [general/gl072.cbl:L346] issues a database read and sets the
sentinel, `save-batch` and the batch record that `end-batch` later stamps and
rewrites; and `move 5 to line-cnt` [general/gl072.cbl:L367] resets the paging
counter that gates L335, which has the database effect described above. Both are
preserved. So is `add 1 to y` [general/gl072.cbl:L353], which is in the
arithmetic census.

`tot-dr` AND `tot-cr` ARE DECLARED UNSIGNED, WHICH EXPLAINS EVERYTHING
======================================================================
    165      03  tot-dr          pic 9(8)v99     value zero.
    166      03  tot-cr          pic 9(8)v99     value zero.

No `S`. Both receivers are UNSIGNED, and that single fact resolves what looks
like an internal inconsistency between the two `tot-cr` accumulation sites:

    327      subtract  post-amount  from  tot-cr      (tot-cr = tot-cr - a)
    427      add       ledger-balance  to  tot-cr     (tot-cr = tot-cr + a)

At L327 `post-amount` is `not > zero`, so subtracting it ADDS its magnitude. At
L427 `ledger-balance` is `not > zero`, so adding it would make the result
negative - and the unsigned receiver DROPS THE SIGN on store, leaving the
magnitude. The two sites disagree in form and agree in outcome. Both feed only
the print fields `l6-debit` and `l6-credit` [general/gl072.cbl:L389-L390], so
neither has any database effect. Recorded as AMBIGUITY Q-19 and offered to the
anomaly-log author as a candidate not in the plan's twenty-two-entry register.

THE `COPY` LIST, TRANSLATED  (Agent Action Plan section 0.4.3)
=============================================================
Thirteen `copy` statements, measured. Each is either an import below or a
recorded omission:

    envdiv.cob                 L88   omission, representation only
    selprint.cob               L101  omission, the print file
    fdprint.cob                L123  omission, the print file, copied
                                     `replacing ==x(132)== by ==x(120)==`
    print-spool-command.cob    L128  omission, the spool-out path
    wsfnctn.cob                L129  records.file_access + dal.status
    wsledger.cob               L130  records.gl_ledger
    wsbatch.cob                L131  records.gl_batch
    Test-Data-Flags.cob        L157  records.test_data_flags
    screenio.cpy               L177  omission, representation only
    wscall.cob                 L256  records.calling_data
    wssystem.cob               L257  records.system_record
    wsnames.cob                L258  records.file_defs
    Proc-ACAS-FH-Calls.cob     L497  dal.facade

THERE IS NO `copy "wspost.cob"`. `01 WS-Posting-Record pic x.`
[general/gl072.cbl:L140] is a ONE-BYTE DUMMY inside the unused-stub block, not a
record layout, so no posting-record module is imported.

BECAUSE THE FACADE COPYBOOK IS `Proc-ACAS-FH-Calls.cob`, THIS MODULE USES THE
ENTITY-NAMED VOCABULARY AND TESTS THE REPLY INLINE. That copybook contains no
error-check paragraph at all - the IRS convention's per-handler check
[copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L355-L364] belongs to the other
vocabulary - so no facade call here raises on a file error, and the handler-named
aliases are not used.

RULES THIS MODULE IS HELD TO
============================
There is NO user rules document for this project: `review_rules` reports that no
user rules were provided. The six binding rules R-1 to R-6 are the Agent Action
Plan's own, section 0.7.2, and where the plan is silent this module holds to
enterprise-standard best practice rather than inventing a rule.

R-1, no COBOL at runtime. Nothing here starts a process, loads a foreign
library, or reaches the compiled-oracle tree. In particular
`call "SYSTEM" using Print-Report.` [general/gl072.cbl:L443] is OMITTED, not
translated: Agent Action Plan section 0.2.2 excludes the report spool-out path
"wherever it appears", and R-1 independently forbids handing a file to the
operating system. It is recorded in the traceability footer.

R-2, zero binary floating-point arithmetic. Every value is `decimal.Decimal`,
`int` or `str`; nothing is inexact anywhere. And per Agent Action Plan section
0.3.1 - "`cobol/` contains no business logic and `programs/` contains no numeric
primitives" - there is no scale arithmetic, no truncation helper, no picture
parsing, no packed or zoned encoding, no `MOVE` truncation and no comparator in
this module. Every one of the twelve arithmetic statements delegates to
`acas_posting.cobol.arithmetic`, every `MOVE` to `acas_posting.cobol.move`, and
every `88`-level test to `acas_posting.cobol.condition_names`.

    THE COMPLETE ARITHMETIC CENSUS - TWELVE STATEMENTS, ONE OF THEM A POSTING

    323  add       post-amount     to    tot-dr          print total
    327  subtract  post-amount     from  tot-cr          print total
    331  add       post-amount     to    ledger-balance  <- THE POSTING
    334  add       1               to    line-cnt        paging, gates L335
    353  add       1               to    y               page number
    385  add       1               to    line-cnt        paging
    386  divide    WS-Ledger-Nos   by 100 giving l6-account   presentation
    400  add       3               to    line-cnt        paging
    413  divide    WS-Ledger-Nos   by 100 giving l6-account   presentation
    424  add       ledger-balance  to    tot-dr          print total
    427  add       ledger-balance  to    tot-cr          print total
    434  add       2               to    line-cnt        paging

ZERO `ROUNDED` SITES. The five in the whole in-scope cycle are
[general/gl051.cbl:L791], [general/gl051.cbl:L796], [general/gl080.cbl:L328],
[irs/irs030.cbl:L1551] and [irs/irs030.cbl:L1562] - none in this program - so
every store here truncates toward zero and every call below passes
`rounded=False` explicitly rather than relying on the default. Agent Action Plan
section 0.1.1: "Getting this backwards would corrupt essentially every posted
figure." There is also ZERO `ON SIZE ERROR` and ZERO `REMAINDER` in this
program, so no overflow handler and no remainder capture is invented (R-3).

Two operand directions are easy to invert and are stated once here:
`DIVIDE a BY b GIVING c` means `c = a / b`, and `SUBTRACT a FROM b` with no
`GIVING` means `b = b - a`.

R-3, nothing added. Every conditional below is one the frozen source has -
L291, L294-L296, L302, L306, L309-L310, L314, L321, L335, L348, L407, L410, L421,
L422, L458, L477, L479, L481 - and nothing else. No transaction wrapper, no
rollback, no save-point around the paired rewrites: the COBOL commits per
statement, and making the pair atomic would change which rows survive a mid-run
failure, which is a behaviour change. No DDL, no ORM entity layer, no migration
tool. No concurrency of any kind; Agent Action Plan section 0.8.4 puts
performance work "out of scope by construction, not merely unrequested", which
is also why the sequential read at L408 stays sequential.

R-4, anomalies reproduced, never fixed. Agent Action Plan section 0.8.2:
"A defect reproduced is correct; a defect fixed is a failure." This module owns
A-13 (both silent-skip sites) and A-14 (the sequential nominal read), each with a
locator-citing comment at its reproduction site, and it offers Q-19 as a
candidate anomaly the register does not carry.

R-5, full traceability. A named function for every one of the thirteen
procedure-division labels, the two `main-exit.` paragraphs section-qualified
because the name repeats, `_headings_end` present with an empty body because the
paragraph has one, a `# GO TO class N` annotation at all seven transfer sites,
both `PERFORM ... THRU` sites hand-verified, and a footer that records every
deliberate omission as an omission.

R-6, compiled behaviour is the tie-breaker, and determinism. `gl072` contains
ZERO clock reads - verified over the whole file - so no ambient clock is read
here and the controlled-clock module is not imported. The run date arrives
through `system_record`, and `move run-date to posted.`
[general/gl072.cbl:L376] writes it straight into `GLBATCH-REC.POSTED`, making it
one of the two observables the byte-identical-reruns guarantee depends on being
pinned at the command-line boundary. The text date arrives through the `to_day`
linkage parameter, used at [general/gl072.cbl:L391] and
[general/gl072.cbl:L475].

WHAT THIS MODULE MAY IMPORT
===========================
`records.*`, `dal.facade`, `dal.status`, `cobol.arithmetic`, `cobol.move`,
`cobol.condition_names`, `cobol.field`, `cobol.picture`, `dates`, `workfiles`,
and the standard library. It must NOT import a command-line module, a handler
module directly, the connection or cursor-state modules, the controlled clock,
the dictionary generator, the oracle harness, or a sibling program module. The
dependency direction is `programs -> {dal.facade, cobol, records, dates,
workfiles}` and never the reverse.

AMBIGUITIES, ARBITRATED AGAINST COMPILED BEHAVIOUR  (rule R-6)
==============================================================
Rule R-6 makes the compiled program's observed behaviour the tie-breaker for an
ambiguous semantic question and requires each resolution to be recorded rather
than settled silently. Six bear on this module, and each is marked in the code
below with a literal `AMBIGUITY Q-<n>` comment at the statement it concerns, so
the sites are greppable and not only narrated here. AMBIGUITY Q-14 is INHERITED from
`acas_posting.cobol.move`, which owns both the number and the answer. Q-18 to
Q-22 are new and take the next free numbers in the migration's shared, sequential
register, whose last-used entry was Q-17 in
`acas_posting.dal.acasirsub5_irs_final`; the next free number after this module
is therefore Q-23.

Two of the six - Q-21 and Q-22 - are findings this migration's own plan does not
carry. They were reached by reading the frozen source rather than by working the
plan's list, and both are offered to the anomaly-log author as candidate register
entries. Neither changes what this module does: in each case the faithful
translation is the same whichever way the question resolves, which is exactly why
recording them is the whole of the obligation.

    Q-14  WHAT AN EDITED RECEIVER OF THE FORM `9999.99` ACTUALLY STORES.
          INHERITED from `acas_posting.cobol.move`, which owns the number and
          the answer. `l6-account pic 9999.99 blank when zero`
          [general/gl072.cbl:L233] is the receiver of both divides, L386 and
          L413. Its picture is all-`9` with an inserted point and a
          `blank when zero` clause, which is NOT the leading-`Z` suppression
          shape `move_to_edited` implements - that function raises
          `UnobservableEditedPicture` for this picture by design, because the
          character image it would have to produce is unobservable once the
          print file is omitted. `divide_by_giving` accepts the descriptor and
          answers with the stored VALUE, which is all this module needs, so the
          two divides go through `divide_by_giving` ALONE and no edited-move is
          attempted. The value is print-only either way; see the OMISSIONS list.
    Q-18  WHETHER `move 1 to File-Key-No.` [general/gl072.cbl:L272] HAS ANY
          EFFECT. ALMOST CERTAINLY INERT, AND REPRODUCED ANYWAY. `File-Key-No`
          sits inside `Logging-Data` [copybooks/wsfnctn.cob:L44-L46], and both
          dispatch paragraphs this program reaches re-pin it to the primary key
          themselves before the `CALL` - `acas005`
          [copybooks/Proc-ACAS-FH-Calls.cob:L35-L40] and `acas007`
          [copybooks/Proc-ACAS-FH-Calls.cob:L51-L56] both issue
          `move 1 to File-Key-No` - so the program's own move is overwritten
          with the same value before it can matter. The only reading that would
          make it observable is a handler that logs the key number BEFORE the
          dispatch paragraph runs, which is why the statement is reproduced
          rather than dropped: the cost is one assignment and the alternative is
          an unrecorded behaviour change. Compare `acas000`, whose entity-named
          dispatch paragraph deliberately does NOT pin the key
          [copybooks/Proc-ACAS-FH-Calls.cob:L20-L24] - proof that the pinning is
          a per-paragraph decision and not a blanket one.
    Q-19  WHETHER THE TWO `tot-cr` ACCUMULATION SITES ARE A DEFECT. NO
          DATABASE EFFECT EITHER WAY, AND THE MECHANISM IS THE UNSIGNED
          RECEIVER. Set out in full under `tot-dr` AND `tot-cr` above. What an
          oracle run would settle is the exact stored magnitude when
          `ledger-balance` is negative at L427 - an unsigned `pic 9(8)v99`
          receiving a negative value stores the absolute value under standard
          COBOL store rules, and that is what
          `acas_posting.cobol.arithmetic.add_to` does with this descriptor - and
          whether the print line the plan's register does not mention was ever
          noticed. Offered to the anomaly-log author as a candidate entry.
    Q-20  WHETHER THE EXTRA `GL-Nominal-Rewrite` A PAGE BREAK CAUSES IS
          OBSERVABLE. NOT IN A FINAL-STATE DIFF; POSSIBLY IN STATEMENT ORDER.
          `line-cnt > Page-Lines` [general/gl072.cbl:L335] performs
          `end-account` mid-account, and `end-account` rewrites the nominal row
          before doing anything else [general/gl072.cbl:L382]. The row's content
          at that moment is exactly what it already holds, so the `UPDATE` is a
          no-op in content and a real statement in sequence. It is reproduced
          because Agent Action Plan section 0.4.1.5 requires statement ordering
          to match - "per-statement autocommit as the COBOL does" - and because
          `Page-Lines` [copybooks/wssystem.cob:L65] is operator-configurable, so
          how often it fires is a property of the seed rather than of the code.
    Q-21  WHETHER THE BARE `perform headings` [general/gl072.cbl:L337] AND THE
          TWO RANGE FORMS [general/gl072.cbl:L300], [general/gl072.cbl:L304] ARE
          EQUIVALENT ON THE `999` PATH. NOT PROVEN EQUIVALENT, AND THE PLAN'S
          CLASSIFICATION IS FOLLOWED PENDING AN ORACLE RUN. They are certainly
          equivalent on the FALL-THROUGH path, because `headings-end.`
          [general/gl072.cbl:L369] has an empty body. The `go to headings-end` at
          [general/gl072.cbl:L349] is the open question. Inside
          `perform headings through headings-end` the jump lands INSIDE the
          performed range and the range's exit is taken normally. Inside the BARE
          `perform headings` the range is one paragraph, so its exit sits at the
          end of `headings.` and the jump goes PAST it; `headings-end.` is empty
          and its own exit tests for a different range, so on the usual
          implementation of `PERFORM` control would continue LINEARLY into the
          paragraphs that follow - `end-batch.` [general/gl072.cbl:L372],
          `end-account.` [general/gl072.cbl:L379], `new-account.`
          [general/gl072.cbl:L402], `end-run.` [general/gl072.cbl:L437] and
          `goback.` [general/gl072.cbl:L446] - abandoning the remainder of
          `post-trans` mid-run. Nothing stops that fall-through structurally:
          all five are paragraphs of `gl072-Main section` and no section
          boundary intervenes. The combination that would reach it is a page
          overflow AND a batch that `get-batch` finds not `Waiting`, which is
          reachable rather than impossible.
          WHAT IS IMPLEMENTED: the Agent Action Plan's own taxonomy classifies
          [general/gl072.cbl:L349] as a class-3 paragraph exit, so `_headings`
          returns and its caller continues - the two forms are treated as
          equivalent. That choice is recorded rather than assumed, because the
          alternative is a drastic control-flow difference that must be MEASURED
          before it is implemented, and no oracle run can arbitrate it in this
          environment: `copybooks/ACAS-SQLstate-error-list.cob` is absent from
          the frozen archive, which blocks most of the compiled bridges and with
          them every database-backed scenario. If a later oracle run shows the
          fall-through, the fix is confined to `_headings`'s return and to the
          bare call site at L337; nothing else in this module changes.
    Q-22  WHICH BATCH ROW `get-batch` ACTUALLY READS. THE SAME
          KEY-THEN-SEQUENTIAL-READ SHAPE AS ANOMALY A-14, ON THE BATCH FILE, AND
          IT MATTERS MORE. `get-batch` sets the whole composite batch key -
          `move 1 to WS-Ledger` [general/gl072.cbl:L451] and
          `move post-batch to save-batch WS-Batch-Nos`
          [general/gl072.cbl:L452] - and then performs `GL-Batch-Read-Next`
          [general/gl072.cbl:L454], which is SEQUENTIAL. `gl072` never performs
          `GL-Batch-Start` and never performs `GL-Batch-Read-Indexed`, so the two
          key moves position nothing, exactly as at [general/gl072.cbl:L405].
          The consequence is larger than A-14's: `end-batch` stamps
          `cleared-status` and `posted` into WHATEVER row is in the record area
          and rewrites it [general/gl072.cbl:L375-L377], so a read that lands on
          a different row stamps a different batch. The two sequences are not
          guaranteed to align, because `gl070`'s cycle filter
          [general/gl070.cbl:L309-L310] keeps other cycles' batches OUT of
          `post-trans` while they remain present in `GLBATCH-REC`. Nothing is
          decided here and nothing needs to be: this module performs the same
          verb after the same two moves, so it is faithful whatever the answer
          turns out to be. Offered to the anomaly-log author as a candidate
          register entry alongside Q-19.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Final

# copy "Proc-ACAS-FH-Calls.cob".  [general/gl072.cbl:L497]
# The ENTITY-named facade vocabulary - `GL-Nominal-*` and `GL-Batch-*` here -
# and its `FacadeContext`, which carries exactly the five items every dispatch
# paragraph passes [copybooks/Proc-ACAS-FH-Calls.cob:L51-L57]. This copybook has
# NO error-check paragraph, so every verb below returns and the reply is tested
# inline, which is what the frozen source does.
from acas_posting.dal import facade

# copy "wsfnctn.cob".  [general/gl072.cbl:L129] - the operation vocabulary half.
# `We-Error` is `pic 999` [copybooks/wsfnctn.cob:L23]; `WeError.NOT_USED` is its
# `999`, the sentinel `get-batch` borrows. Named rather than written as a literal
# because 999 does not mean "error" and the literal invites reading it that way.
from acas_posting.dal.status import WeError

# The COBOL-language semantics layer. `programs/` holds no numeric primitive of
# its own (Agent Action Plan section 0.3.1), so all twelve arithmetic
# statements, every `MOVE`, every numeric relation and every `88`-level test
# resolve here.
from acas_posting.cobol import arithmetic, condition_names, move, picture
from acas_posting.cobol.field import FieldDescriptor
from acas_posting.cobol.move import Figurative

# The date sections consolidated. `zz070-Convert-Date` [general/gl072.cbl:L467]
# is byte-identical across its ten carriers, so it lives once in
# `acas_posting.dates`; `WsDateFormats` is `01 ws-date-formats.`
# [general/gl072.cbl:L180-L201] with its three `REDEFINES` views.
from acas_posting.dates import WsDateFormats, zz070_convert_date

# copy "wscall.cob".  [general/gl072.cbl:L256]
# `01 WS-Calling-Data` [copybooks/wscall.cob:L6-L14], the first linkage
# parameter. Accepted and unread here; see the traceability footer.
from acas_posting.records.calling_data import WsCallingData

# copy "wsfnctn.cob".  [general/gl072.cbl:L129] - the data-layout half.
# `01 File-Access` [copybooks/wsfnctn.cob:L23-L38] carries `We-Error`,
# `Fs-Reply` and, inside `Logging-Data` [copybooks/wsfnctn.cob:L44-L46],
# `File-Key-No`. WORKING-STORAGE, not linkage, so every status this program sees
# is program-local.
from acas_posting.records.file_access import FileAccess

# copy "wsnames.cob".  [general/gl072.cbl:L258]
# `01 File-Defs.` [copybooks/wsnames.cob:L13], the file-name buffers. Supplies
# `post-trans-name` [copybooks/wsnames.cob:L16], which this program's sole
# FILE-CONTROL entry assigns [general/gl072.cbl:L95].
from acas_posting.records.file_defs import FileDefs

# copy "wsbatch.cob".  [general/gl072.cbl:L131]
# `GLBATCH-REC` - the batch header `end-batch` stamps and rewrites, and the one
# `get-batch` reads.
from acas_posting.records.gl_batch import GlBatchRecord

# copy "wsledger.cob".  [general/gl072.cbl:L130]
# `GLLEDGER-REC` - the nominal account whose `Ledger-Balance` L331 accumulates
# into and `end-account` rewrites.
from acas_posting.records.gl_ledger import WsLedgerRecord

# copy "wssystem.cob".  [general/gl072.cbl:L257]
# `SYSTEM-REC`, the 169-column system record. Read for `Run-Date`
# [copybooks/wssystem.cob:L67], `Page-Lines` [copybooks/wssystem.cob:L65],
# `Date-Form` [copybooks/wssystem.cob:L128] and `Scycle`
# [copybooks/wssystem.cob:L63]; `Date-Form` is also WRITTEN, at
# [general/gl072.cbl:L478].
from acas_posting.records.system_record import SystemRecord

# copy "Test-Data-Flags.cob".  [general/gl072.cbl:L157]
# `ACAS-DAL-Common-Data` - the fifth argument of every handler `CALL`
# [copybooks/Proc-ACAS-FH-Calls.cob:L51-L57]. The maintainer's own inline
# comment on the `copy` reads "set sw-testing to zero to stop logging."
from acas_posting.records.test_data_flags import AcasDalCommonData

# fd post-trans / 01 post-trans-record.  [general/gl072.cbl:L108-L119]
# The work-sequence record this program reads. NOT a table row: `post-trans` is
# a transient scratch file [copybooks/wsnames.cob:L16], so nothing about it
# reaches the database and nothing about it appears in a table dump.
from acas_posting.records.work_records import PostTransRecord

# The work-file layer. `post-trans` is the output of `gl071`
# [general/gl071.cbl:L178], modelled as an ordered in-process sequence; the
# container is handed in rather than made module-global so that one run's
# records cannot leak into the next (rule R-6).
from acas_posting.workfiles import (
    GeneralLedgerWorkFiles,
    general_ledger_work_files,
)

logger: Final[logging.Logger] = logging.getLogger(__name__)

#: The whole public surface: the program's single entry point, mirroring its
#: `PROCEDURE DIVISION USING` list [general/gl072.cbl:L262-L265]. Agent Action
#: Plan section 0.3.3, verbatim: "Each `programs/*.py` module exposes a single
#: `run(...)` entry mirroring its COBOL `PROCEDURE DIVISION USING` list, with
#: the paragraph functions private to the module. Callers cannot reach into a
#: program's internals, exactly as a COBOL `CALL` cannot." Every one of the
#: thirteen paragraph functions below is therefore private, and a tuple is used
#: rather than a list so the surface cannot be extended in place at run time.
__all__: Final[tuple[str, ...]] = ("run",)


# ---------------------------------------------------------------------------
# Literals the frozen source writes, named once
# ---------------------------------------------------------------------------

#: `display "Phase - 4.  Transaction Update" at 0801 with foreground-color 2.`
#: [general/gl072.cbl:L274]. A progress notice with no database effect, so per
#: Agent Action Plan section 0.3.4 it becomes a log record "at a severity
#: matching the original's intent" - INFO. It must not alter control flow and
#: must never appear in a table dump, and it does neither. The screen position,
#: the colour and the literal's internal double space are presentation; the
#: text itself is kept verbatim so a reader can match it to the source.
_PHASE_4_DIAGNOSTIC: Final[str] = "Phase - 4.  Transaction Update"

#: The one-character flag value the page-overflow path stores
#: [general/gl072.cbl:L338] and the three guards test
#: [general/gl072.cbl:L407], [general/gl072.cbl:L410],
#: [general/gl072.cbl:L421]. Named because the same literal appears at four
#: sites and a typo at any one of them would silently change which of the three
#: suppressions fires.
_READ_LEDGER_SUPPRESSED: Final[str] = "R"

#: The divisor of `divide WS-Ledger-Nos by 100 giving l6-account`
#: [general/gl072.cbl:L386], [general/gl072.cbl:L413]. The nominal account
#: number is held scaled by 100 - `WS-Ledger-Nos pic 9(6)`
#: [copybooks/wsledger.cob:L14] against a printed `9999.99` - so the divide is
#: the account-number presentation scaling, not an accounting computation.
_ACCOUNT_NUMBER_DIVISOR: Final[int] = 100

#: The two character positions of `WS-Ledger-Key`'s children inside the eight-byte
#: group image, ONE-BASED as COBOL reference modification is:
#: `03 WS-Ledger-Nos pic 9(6).` [copybooks/wsledger.cob:L14] occupies 1:6 and
#: `03 Ledger-PC pic 9(2).` [copybooks/wsledger.cob:L20] occupies 7:2. Named so
#: the group split at [general/gl072.cbl:L405] carries no bare offsets, and taken
#: from the two picture clauses rather than counted by eye.
_WS_LEDGER_NOS_POSITION: Final[tuple[int, int]] = (1, 6)
_LEDGER_PC_POSITION: Final[tuple[int, int]] = (7, 2)

#: `move 5 to line-cnt.` [general/gl072.cbl:L367] - the paging counter's value
#: after a fresh page of headings has been laid down. Not presentation-only in
#: effect: `line-cnt` gates [general/gl072.cbl:L335], which performs
#: `end-account` and therefore issues an `UPDATE`.
_LINE_CNT_AFTER_HEADINGS: Final[int] = 5

#: The scale-2 zero the two `value zero` clauses on the unsigned money
#: accumulators declare [general/gl072.cbl:L165-L166]. A `VALUE` clause is a
#: DECLARATION rather than a `MOVE` - it is applied by the compiler at program
#: load, not by an executed statement - so it is expressed as a literal here
#: rather than routed through `acas_posting.cobol.move`, which publishes no
#: `VALUE`-clause primitive. The scale is two because the picture says `v99`.
_MONEY_ZERO: Final[Decimal] = Decimal("0.00")


# ---------------------------------------------------------------------------
# Field descriptors  (rule R-5: every field cites its dictionary entry)
# ---------------------------------------------------------------------------
# Two provenances, and the choice between them is not a preference. A field the
# data dictionary catalogues is looked up by its dictionary key, so its digits,
# scale, sign and usage are DERIVED from the authoritative
# copybook/host-variable/column triple rather than transcribed here - which is
# exactly the transcription error rule R-5 exists to prevent. A field the
# dictionary does not catalogue - this program's own WORKING-STORAGE and its
# print lines, none of which reach a table - is built from its picture clause
# with the frozen line as its provenance, which
# `FieldDescriptor.__post_init__` requires.

#  fd post-trans / 01 post-trans-record.  [general/gl072.cbl:L110-L119]
_POST_BATCH: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "post-trans-record.post-batch#111"
)
_POST_LEDGER: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "post-trans-record.post-ledger"
)
_POST_AC: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "post-trans-record.post-ac#116"
)
_POST_PC: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "post-trans-record.post-pc#117"
)
#  `03 post-amount pic s9(8)v99.` [general/gl072.cbl:L118] is NOT modelled as a
#  descriptor here, and its absence is deliberate rather than an oversight. It is
#  the SENDING field of the three statements that consume it -
#  [general/gl072.cbl:L323], [general/gl072.cbl:L327] and THE POSTING at
#  [general/gl072.cbl:L331] - and COBOL's `ADD ... TO` and `SUBTRACT ... FROM`
#  store under the RECEIVING field's picture, so `arithmetic.add_to` and
#  `arithmetic.subtract_from` take a receiving descriptor and no sending one. A
#  descriptor built but never passed would be dead metadata inviting the reader to
#  think the sending picture governs something here. Its declaration is cited at
#  each of the three sites instead, and the value itself is carried as a scale-2
#  `decimal.Decimal` by `records.work_records`, which does cite the dictionary
#  entry `post-trans-record.post-amount#118`.

#  copy "wsledger.cob".  [general/gl072.cbl:L130]
_WS_LEDGER_KEY: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "WS-Ledger-Record.WS-Ledger-Key"
)
_WS_LEDGER_NOS: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "WS-Ledger-Record.WS-Ledger-Nos"
)
_LEDGER_PC: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "WS-Ledger-Record.Ledger-PC"
)
#: `03 Ledger-Balance pic s9(8)v99 comp-3.` [copybooks/wsledger.cob:L28] -
#: SIGNED, scale 2, packed. The receiving field of THE POSTING
#: [general/gl072.cbl:L331] and the only field in this program whose value
#: reaches a monetary column.
_LEDGER_BALANCE: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLLEDGER-REC.LEDGER-BALANCE"
)

#  copy "wsbatch.cob".  [general/gl072.cbl:L131]
_WS_LEDGER: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "WS-Batch-Record.WS-Ledger"
)
_WS_BATCH_NOS: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "WS-Batch-Record.WS-Batch-Nos"
)
_CLEARED_STATUS: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLBATCH-REC.CLEARED-STATUS"
)
#: `03 Posted binary-long.` [copybooks/wsbatch.cob:L38] - the column
#: [general/gl072.cbl:L376] stamps with the controlled clock's run date.
_POSTED: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLBATCH-REC.POSTED"
)

#  copy "wssystem.cob".  [general/gl072.cbl:L257]
#: `03 Run-Date binary-long.` [copybooks/wssystem.cob:L67] - one of exactly two
#: observables the controlled clock pins, the other being the `to-day pic x(10)`
#: text date. Read here, never derived.
_RUN_DATE: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "SYSTEM-REC.RUN-DAT"
)
#: `03 Date-Form pic 9.` [copybooks/wssystem.cob:L128], with `88 Date-UK value 1.`
#: `88 Date-USA value 2.` and `88 Date-Intl value 3.` following it. READ AND
#: WRITTEN: [general/gl072.cbl:L477-L478] defaults a zero to 1, and this is a
#: `SYSTEM-REC` column, so the write is visible in a table dump.
_DATE_FORM: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "SYSTEM-REC.DATE-FORM"
)

#  copy "wsfnctn.cob".  [general/gl072.cbl:L129]
#: `03 We-Error pic 999.` [copybooks/wsfnctn.cob:L23] - the field `get-batch`
#: borrows as its private "skip this batch" flag by storing `999` into it, and
#: the only status this program ever tests.
_WE_ERROR: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "File-Access.We-Error"
)
_FILE_KEY_NO: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "File-Access.File-Key-No"
)
#: `03 Fs-Reply pic 99.` [copybooks/wsfnctn.cob:L25]. Named because this
#: program's FILE-CONTROL entry declares it as the FILE STATUS of the work
#: sequence - `status fs-reply` [general/gl072.cbl:L97] - so every
#: `open`/`read`/`close` of `post-trans` stores into the very same field the
#: facade verbs report through. See `_gl072_main` for why that is reproduced.
_FS_REPLY: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "File-Access.Fs-Reply"
)

#  01 filler.  [general/gl072.cbl:L159-L166] - this program's own state.
#  Not in the data dictionary: none of it reaches a table.
_SAVE_BATCH: Final[FieldDescriptor] = picture.descriptor_for(
    "pic 9(5) value zero",
    name="save-batch",
    source_locator="general/gl072.cbl:L160",
)
_SAVE_LEDGER: Final[FieldDescriptor] = picture.descriptor_for(
    "pic 9(8) value zero",
    name="save-ledger",
    source_locator="general/gl072.cbl:L161",
)
_READ_LEDGER: Final[FieldDescriptor] = picture.descriptor_for(
    "pic x value space",
    name="read-ledger",
    source_locator="general/gl072.cbl:L162",
)
#: `03 line-cnt binary-char value zero.` [general/gl072.cbl:L163] - SIGNED,
#: because no `unsigned` follows `binary-char`, unlike the six page-geometry
#: fields immediately below it [general/gl072.cbl:L169-L174] which all carry it.
#: The divergence is the source's, and it is preserved.
_LINE_CNT: Final[FieldDescriptor] = picture.descriptor_for(
    "binary-char value zero",
    name="line-cnt",
    source_locator="general/gl072.cbl:L163",
)
_Y: Final[FieldDescriptor] = picture.descriptor_for(
    "pic 99 value zero",
    name="y",
    source_locator="general/gl072.cbl:L164",
)
#: `03 tot-dr pic 9(8)v99 value zero.` [general/gl072.cbl:L165] - UNSIGNED.
_TOT_DR: Final[FieldDescriptor] = picture.descriptor_for(
    "pic 9(8)v99 value zero",
    name="tot-dr",
    source_locator="general/gl072.cbl:L165",
)
#: `03 tot-cr pic 9(8)v99 value zero.` [general/gl072.cbl:L166] - UNSIGNED, and
#: that is the whole mechanism of AMBIGUITY Q-19.
_TOT_CR: Final[FieldDescriptor] = picture.descriptor_for(
    "pic 9(8)v99 value zero",
    name="tot-cr",
    source_locator="general/gl072.cbl:L166",
)

#  01 line-6.  [general/gl072.cbl:L232-L245] - the detail print line. Only the
#  one field an arithmetic statement receives into is modelled; the other
#  eleven are pure print receivers and are recorded in the OMISSIONS list.
_L6_ACCOUNT: Final[FieldDescriptor] = picture.descriptor_for(
    "pic 9999.99 blank when zero",
    name="l6-account",
    source_locator="general/gl072.cbl:L233",
)


# ---------------------------------------------------------------------------
# The program's storage, as one object
# ---------------------------------------------------------------------------
@dataclass(slots=True)
class _ProgramStorage:
    """`gl072`'s LINKAGE and WORKING-STORAGE sections, in one place.

    COBOL paragraphs do not take arguments: every paragraph of a program sees
    the whole of its working-storage and the whole of its linkage. The thirteen
    paragraph functions below therefore take ONE argument, this object, which is
    the Python analogue of that shared visibility - and NOT a context object in
    the design-pattern sense. Nothing is encapsulated, nothing is validated on
    the way in or out, and no field is private, precisely because none of that
    is true of a COBOL working-storage item.

    Handing storage around explicitly rather than holding it in module globals
    is what makes two runs of the same scenario byte-identical (rule R-6): a
    module-level `save-batch` would carry the previous run's batch number into
    the next one, and the difference would surface as a missing `end-batch`
    rather than as an obvious error.

    THE LINKAGE SECTION  [general/gl072.cbl:L253-L260]
    Four items, in the order `procedure division using` names them
    [general/gl072.cbl:L262-L265].

    THE WORKING-STORAGE SECTION  [general/gl072.cbl:L124-L245]
    `File-Access` [copybooks/wsfnctn.cob:L23-L38], `WS-Ledger-Record`
    [copybooks/wsledger.cob], `WS-Batch-Record` [copybooks/wsbatch.cob] and
    `ACAS-DAL-Common-Data` [copybooks/Test-Data-Flags.cob] are copied into
    WORKING-STORAGE, so they belong to this program alone and are constructed by
    `run` rather than passed in. `01 ws-date-formats.`
    [general/gl072.cbl:L180-L201] likewise.

    THE FILE SECTION  [general/gl072.cbl:L108-L119]
    `post` is the `01 post-trans-record.` buffer. A COBOL record area PERSISTS
    after the `at end` branch is taken - the last record read stays in it - so it
    is a field here and not a local of `_loop`. Nothing below reads it after the
    at-end, but the persistence is the source's and is not designed away.
    """

    #  procedure division using ws-calling-data ...  [general/gl072.cbl:L262]
    ws_calling_data: WsCallingData
    system_record: SystemRecord
    to_day: str
    file_defs: FileDefs

    #  working-storage section.  [general/gl072.cbl:L124]
    file_access: FileAccess
    ledger: WsLedgerRecord
    batch: GlBatchRecord
    dal_common: AcasDalCommonData
    date_formats: WsDateFormats

    #  The `post-trans` sequence, and the two facade linkages over it.
    work_files: GeneralLedgerWorkFiles
    ledger_ctx: facade.FacadeContext
    batch_ctx: facade.FacadeContext

    #  01 filler.  [general/gl072.cbl:L159-L166], with their `value` clauses.
    #: `03 save-batch pic 9(5) value zero.` [general/gl072.cbl:L160] - the
    #: batch-break detector, and `get-batch` zeroes it to force a re-read
    #: [general/gl072.cbl:L460].
    save_batch: int = 0
    #: `03 save-ledger pic 9(8) value zero.` [general/gl072.cbl:L161] - the
    #: account-break detector, holding the composite `(account, profit centre)`
    #: key as one eight-digit number.
    save_ledger: int = 0
    #: `03 read-ledger pic x value space.` [general/gl072.cbl:L162] - the
    #: three-way suppression flag; see the module docstring.
    read_ledger: str = " "
    #: `03 line-cnt binary-char value zero.` [general/gl072.cbl:L163] - the
    #: paging counter, which gates the extra rewrite at
    #: [general/gl072.cbl:L335].
    line_cnt: int = 0
    #: `03 y pic 99 value zero.` [general/gl072.cbl:L164] - the page number.
    y: int = 0
    #: `03 tot-dr pic 9(8)v99 value zero.` [general/gl072.cbl:L165] - print
    #: total only; its sole consumer is [general/gl072.cbl:L389].
    tot_dr: Decimal = _MONEY_ZERO
    #: `03 tot-cr pic 9(8)v99 value zero.` [general/gl072.cbl:L166] - print
    #: total only; its sole consumer is [general/gl072.cbl:L390]. Question Q-19.
    tot_cr: Decimal = _MONEY_ZERO

    #: `03 l6-account pic 9999.99 blank when zero.` [general/gl072.cbl:L233] -
    #: the receiver of both divides, [general/gl072.cbl:L386] and
    #: [general/gl072.cbl:L413]. Print-only; modelled because the two divides
    #: are arithmetic statements and rule R-2 requires them to go through a
    #: receiving descriptor rather than a bare division.
    l6_account: Decimal = _MONEY_ZERO

    #: `01 post-trans-record.` [general/gl072.cbl:L110] - the record area.
    post: PostTransRecord = field(default_factory=PostTransRecord)


def _post_ledger_group_image(post: PostTransRecord) -> str:
    """The eight-character byte image of `03 post-ledger.`.

    `post-ledger` [general/gl072.cbl:L115-L117] is a GROUP item over
    `post-ac pic 9(6)` and `post-pc pic 99`, and COBOL lets a group be used as
    an alphanumeric item of the concatenated width of its children - which is
    what makes `move post-ledger to WS-Ledger-Key` [general/gl072.cbl:L405] and
    `move post-ledger to save-ledger` [general/gl072.cbl:L317] legal, and what
    makes `if post-ledger not = save-ledger` [general/gl072.cbl:L309] a
    comparison rather than a type error. Python has no such view of a dataclass,
    so the image is materialised here.

    THIS FUNCTION OWNS NO SEMANTICS. It renders nothing itself: each child's
    character image comes from `acas_posting.cobol.move.move_group` applied with
    that child's own descriptor, so the digit count, the zero padding and the
    absence of a sign are all decided by the picture clause one layer down
    (Agent Action Plan section 0.3.1, and rule R-2). It exists because three
    statements need the same image and building it three times would be three
    chances to build it differently.

    It is NOT a COBOL paragraph and is deliberately not named as one; the
    traceability footer lists it as a rendering helper.

    Args:
        post: The `01 post-trans-record.` area whose `post-ledger` group is
            wanted. Both children are read; nothing is written.

    Returns:
        Exactly eight characters - six digits of account number followed by two
        of profit centre.
    """
    #      03  post-ledger.
    #          05  post-ac     pic 9(6).
    #          05  post-pc     pic 99.
    return move.move_group(
        post.post_ledger.post_ac, _POST_LEDGER, sending_field=_POST_AC
    ) + move.move_group(
        post.post_ledger.post_pc, _POST_LEDGER, sending_field=_POST_PC
    )


#  gl072-Main section.  [general/gl072.cbl:L268]


def _gl072_main(st: _ProgramStorage) -> None:
    """`gl072-Main section.` - the opens and the break-detector reset.

    [general/gl072.cbl:L268-L281]

        271      move     Print-Spool-Name to PSN.
        272      move     1  to File-Key-No.
        274      display  "Phase - 4.  Transaction Update" at 0801 with
                          foreground-color 2.
        275      move     prog-name to l1-prog.
        276      perform  GL-Batch-Open.
        277      perform  GL-Nominal-Open.
        278      open     input  post-trans.
        279      open     output print-file.
        281      move     zero  to  save-batch save-ledger.

    Control FALLS THROUGH from here into `loop.` [general/gl072.cbl:L283]; the
    section header carries no `exit section.` and there is no transfer at the end
    of L281. `run` therefore calls `_loop` immediately after this, so the
    fall-through is visible rather than implied.

    THE TWO OPENS ARE I-O OPENS, NOT INPUT OPENS. `GL-Batch-Open`
    [copybooks/Proc-ACAS-FH-Calls.cob:L419-L422] and `GL-Nominal-Open`
    [copybooks/Proc-ACAS-FH-Calls.cob:L299-L302] both set the access type to
    I-O, which is what the maintainer's own inline comment on L276 says -
    "open i-o batch-file ledger-file" - and what the two `REWRITE`s later
    require. The `-Open-Input` verbs exist in the same copybook and are NOT the
    ones performed here.

    NEITHER OPEN'S REPLY IS TESTED. `Proc-ACAS-FH-Calls.cob` publishes no
    error-check paragraph, and this program does not test `Fs-Reply` or
    `We-Error` after either open - it proceeds straight to the read loop. No
    check is invented (rule R-3): a failed open would surface as whatever the
    first read or rewrite then does, which is the frozen behaviour.

    Args:
        st: The program's storage. `file_access.logging_data.file_key_no`,
            `save_batch` and `save_ledger` are written; the two facade contexts
            and the work-file container are used.
    """
    # 271  move     Print-Spool-Name to PSN.
    # OMITTED - the report spool-out path. `PSN` is the shell command buffer of
    # [copybooks/print-spool-command.cob], consumed only by
    # `call "SYSTEM" using Print-Report.` [general/gl072.cbl:L443], which Agent
    # Action Plan section 0.2.2 excludes and rule R-1 independently forbids.
    # Recorded in the traceability footer.

    # 272  move     1  to File-Key-No.
    # AMBIGUITY Q-18. Reproduced although it is almost certainly inert: both
    # dispatch paragraphs this program reaches re-pin `File-Key-No` to the same
    # value before the `CALL` [copybooks/Proc-ACAS-FH-Calls.cob:L35-L40],
    # [copybooks/Proc-ACAS-FH-Calls.cob:L51-L56]. Dropping it would be an
    # unrecorded behaviour change for the cost of one assignment saved. The
    # value goes through the move layer with `File-Key-No`'s own descriptor
    # [copybooks/wsfnctn.cob:L46] rather than being assigned raw, so the field's
    # picture governs the store here exactly as it does everywhere else.
    st.file_access.logging_data.file_key_no = move.move(1, _FILE_KEY_NO)

    # 274  display  "Phase - 4.  Transaction Update" at 0801 with
    #               foreground-color 2.
    # A progress notice with no database effect, so it becomes ONE log record at
    # INFO (Agent Action Plan section 0.3.4). It alters no control flow and
    # reaches no table.
    logger.info(_PHASE_4_DIAGNOSTIC)

    # 275  move     prog-name to l1-prog.
    # OMITTED - presentation. `77 prog-name pic x(15) value "gl072 (3.3.00)".`
    # [general/gl072.cbl:L127] is the version banner and `l1-prog`
    # [general/gl072.cbl:L207] is a print-line field.

    # 276  perform  GL-Batch-Open.       *> open i-o batch-file ledger-file.
    # The status arrives IN THE LINKAGE, not in the return value: every handler
    # mutates `File-Access` in place exactly as a COBOL `CALL` does through its
    # parameter list, and `_perform` reads it back afterwards. The returned pair
    # is therefore a convenience this program has no use for, and the frozen
    # source tests nothing here, so nothing is bound.
    facade.gl_batch_open(st.batch_ctx)

    # 277  perform  GL-Nominal-Open.
    facade.gl_nominal_open(st.ledger_ctx)

    # 278  open     input  post-trans.
    # The work sequence `gl071` wrote [general/gl071.cbl:L178]. Opened INPUT:
    # this program only reads it, and it is the one file `gl072` opens itself
    # rather than through a facade verb.
    st.work_files.post_trans.open_input()
    # `select post-trans ... status fs-reply` [general/gl072.cbl:L95-L98]
    # declares the FILE STATUS of this sequence to be the very `Fs-Reply` field
    # the facade verbs report through [copybooks/wsfnctn.cob:L25], because
    # `wsfnctn.cob` is copied into this program's WORKING-STORAGE at
    # [general/gl072.cbl:L129]. So each `open`, `read` and `close` of the
    # sequence OVERWRITES the reply left by the last facade call. Reproduced -
    # it is a store the frozen source performs - and recorded: `gl072` never
    # inspects `Fs-Reply`, only `We-Error`, so the clobber changes nothing
    # observable, which is exactly why it must not be relied upon either.
    st.file_access.fs_reply = move.move(
        st.work_files.post_trans.fs_reply, _FS_REPLY
    )

    # 279  open     output print-file.
    # OMITTED with the print file.

    # 281  move     zero  to  save-batch save-ledger.
    # A TWO-RECEIVER `MOVE` of the figurative constant. Each receiver is
    # converted independently under its own picture - `pic 9(5)` and `pic 9(8)` -
    # rather than one value being assigned twice.
    st.save_batch, st.save_ledger = move.move_to_all(
        Figurative.ZERO, [_SAVE_BATCH, _SAVE_LEDGER]
    )


#  loop.  [general/gl072.cbl:L283]


def _loop(st: _ProgramStorage) -> None:
    """`loop.` - the main read loop, and the one statement that posts.

    [general/gl072.cbl:L283-L341]

    Every exit from this paragraph is a `GO TO`: three of them return to `loop.`
    itself [general/gl072.cbl:L292], [general/gl072.cbl:L307],
    [general/gl072.cbl:L341] and one leaves for `end-run.`
    [general/gl072.cbl:L289]. Control therefore NEVER falls through from here
    into `headings.` [general/gl072.cbl:L343], and this function's `while True`
    has no exit other than the one `break`.

    THE POST-LOOP WORK IS `end-run`'s, AND IT IS NOT INSIDE THIS FUNCTION.
    `go to end-run` is a class-2 forward terminator: its target does real work -
    three closes [general/gl072.cbl:L440-L442] - so the transformation is the
    `break` PLUS faithful placement of that work after the loop. Agent Action
    Plan section 0.6.3, verbatim: "the transformation is `break` plus faithful
    placement of that work after the loop, not `break` alone. Mis-splitting here
    would silently drop end-of-run processing." `run` calls `_end_run`
    immediately after this function returns, which is where the split lands.

    Args:
        st: The program's storage. `post`, `save_batch`, `save_ledger`,
            `read_ledger`, `line_cnt`, `tot_dr`, `tot_cr` and - through
            `_end_account`, `_end_batch`, `_headings` and `_new_account` - the
            ledger and batch record areas are all written.
    """
    while True:
        # 286  read     post-trans  at end
        # 287           perform  end-account
        # 288           perform  end-batch
        # 289           go to    end-run.
        record = st.work_files.post_trans.read_next()
        # `status fs-reply` [general/gl072.cbl:L97] again; see `_gl072_main`.
        st.file_access.fs_reply = move.move(
            st.work_files.post_trans.fs_reply, _FS_REPLY
        )
        if record is None:
            # AT END. The record area is NOT refreshed - `st.post` still holds
            # the last record actually read, which is the COBOL behaviour and
            # why the buffer is a field of the storage rather than a local.
            #
            # ACCOUNT FIRST, THEN BATCH. The declarations are the other way
            # round [general/gl072.cbl:L372] then [general/gl072.cbl:L379];
            # Agent Action Plan section 0.6.4: "Inverting them would produce a
            # batch marked posted with an unclosed final account."
            _end_account(st)  # 287
            _end_batch(st)  # 288
            # GO TO class 2 - forward terminator. `end-run.`
            # [general/gl072.cbl:L437] runs after the loop, in `run`.
            break  # 289
        st.post = record

        # 291  if       post-batch  not numeric
        # 292           go to  loop.
        #
        # ANOMALY A-13 [general/gl072.cbl:L291-L292] - site (a). A record whose
        # batch number is not numeric is skipped ENTIRELY SILENTLY: no message,
        # no counter, no trace, and the record is not written anywhere. Nothing
        # downstream can tell it existed.
        # Reproduced deliberately per R-4; DO NOT FIX. No logging on this path
        # (rule R-3: "adding a warning would be an added behavior").
        #
        # The class test itself is `acas_posting.cobol.move.is_numeric_class`,
        # which implements COBOL's `NOT NUMERIC` class condition and never
        # raises. It is NOT a digit-string test and not an integer conversion
        # wrapped in a handler: rule R-2 and Agent Action Plan section 0.3.1 keep
        # every such rule one layer down.
        #
        # WHY THIS GUARD CANNOT FIRE HERE, AND WHY IT IS STILL WRITTEN.
        # `post_batch` is carried as `int` [general/gl072.cbl:L111 is `pic 9(5)`,
        # unsigned DISPLAY], so no value the work sequence can hold makes the
        # class condition false. In the compiled program it CAN fire: the record
        # area is raw bytes and an unwritten or partially written `pretrans.tmp`
        # leaves spaces or nulls in those five positions. The guard is therefore
        # a real defence in COBOL and a provably dead one in Python - and it is
        # reproduced regardless, because deleting it would erase a register
        # anomaly and because a future change to the carrier type would silently
        # remove a check the source has.
        if not move.is_numeric_class(st.post.post_batch, _POST_BATCH):
            continue  # 292  GO TO class 1 - loop-back

        # 294  if       post-batch not = save-batch
        # 295    and    save-batch not = zero
        # 296    and    we-error   not = 999
        # 297           perform  end-account
        # 298           perform  end-batch
        # 299           move  zero  to  save-ledger
        # 300           perform  headings  through  headings-end.
        #
        # A THREE-CONDITION `AND`: a batch break, on a batch that is not the
        # initial zero, whose predecessor was not flagged. All three must hold.
        # The third is the `999` sentinel - `WeError.NOT_USED`, never the
        # literal - which suppresses the close for a batch `get-batch` has
        # already rejected.
        if (
            arithmetic.compare(st.post.post_batch, st.save_batch) != 0
            and arithmetic.compare(st.save_batch, 0) != 0
            and arithmetic.compare(st.file_access.we_error, WeError.NOT_USED)
            != 0
        ):
            _end_account(st)  # 297  account first
            _end_batch(st)  # 298  then batch
            # 299  move  zero  to  save-ledger
            st.save_ledger = move.move(Figurative.ZERO, _SAVE_LEDGER)
            # PERFORM THRU [general/gl072.cbl:L300] - hand-verified: spans
            # headings (L343) through headings-end (L369), which has an empty
            # body. Transformed into an explicit two-call sequence rather than
            # by pattern, per Agent Action Plan section 0.4.2 - "each is
            # transformed by hand into an explicit sequence of calls and
            # verified individually, with no pattern-matching shortcut". One of
            # only four such sites in the whole in-scope surface, two of which
            # are in this program.
            _headings(st)  # 300  range start
            _headings_end()  # 300  range end

        # 302  if       save-batch  equal  zero
        # 303           move  post-batch  to  save-batch
        # 304           perform  headings  through  headings-end.
        #
        # First record of a run, and also every record after `get-batch` has
        # zeroed `save-batch` at [general/gl072.cbl:L460] - which is how a
        # rejected batch re-enters `headings` on every one of its records.
        if arithmetic.compare(st.save_batch, 0) == 0:
            # 303  move  post-batch  to  save-batch
            st.save_batch = move.move(
                st.post.post_batch, _SAVE_BATCH, sending_field=_POST_BATCH
            )
            # PERFORM THRU [general/gl072.cbl:L304] - hand-verified: spans
            # headings (L343) through headings-end (L369), which has an empty
            # body. The second of the two range sites in this program, and
            # verified separately from L300 rather than assumed to match it.
            _headings(st)  # 304  range start
            _headings_end()  # 304  range end

        # 306  if       we-error  equal  999
        # 307           go to  loop.
        #
        # ANOMALY A-13 [general/gl072.cbl:L306-L307] - site (b). A record
        # belonging to a batch that `get-batch` found not `Waiting` is skipped
        # ENTIRELY SILENTLY: no message, no counter, no trace, nothing written.
        # Reproduced deliberately per R-4; DO NOT FIX. No logging on this path.
        #
        # `999` IS `WeError.NOT_USED`, NOT AN ERROR CODE
        # [copybooks/wsfnctn.cob:L23]. The chain that sets it is
        # `get-batch` L458-L460 -> `headings` L348-L349 -> here; it is drawn in
        # full in the module docstring.
        #
        # NOTE THE ORDER. The batch-break block above has ALREADY closed the
        # previous account and batch and called `headings` - which is what set
        # the sentinel - before this test runs. Moving this test earlier would
        # leave the previous batch unstamped.
        if arithmetic.compare(st.file_access.we_error, WeError.NOT_USED) == 0:
            continue  # 307  GO TO class 1 - loop-back

        # 309  if       post-ledger not = save-ledger
        # 310    and    save-ledger not = zero
        # 311           perform  end-account
        # 312           perform  new-account.
        #
        # THE COMPOSITE LEDGER KEY, ONCE. `post-ledger`
        # [general/gl072.cbl:L115-L117] is a group of `post-ac pic 9(6)` and
        # `post-pc pic 99`; `save-ledger` is `pic 9(8)`
        # [general/gl072.cbl:L161]. COBOL compares the group as eight
        # characters and stores it at L317 as eight digits.
        #
        # WHY ONE CONVERSION SERVES BOTH L309 AND L317. The conversion is a pure
        # function of `post-ledger`, and nothing between L309 and L317 writes
        # `post-ledger`: `new-account` READS it [general/gl072.cbl:L405] and
        # writes `WS-Ledger-Key`, never the record area. So the value the COBOL
        # would compute twice is computed once here.
        #
        # WHY COMPARING VALUES IS THE SAME AS COMPARING BYTES. The relation is
        # `not =` only - no ordering is taken - and both operands are exactly
        # eight unsigned digit characters, so two images are equal if and only if
        # the numbers they denote are equal. The comparison itself is
        # `acas_posting.cobol.arithmetic.compare`, COBOL's algebraic relation;
        # no text comparator is written here.
        post_ledger_value = move.move(
            _post_ledger_group_image(st.post),
            _SAVE_LEDGER,
            sending_field=_POST_LEDGER,
        )
        if (
            arithmetic.compare(post_ledger_value, st.save_ledger) != 0
            and arithmetic.compare(st.save_ledger, 0) != 0
        ):
            _end_account(st)  # 311
            _new_account(st)  # 312

        # 314  if       save-ledger  equal  zero
        # 315           perform  new-account.
        #
        # A SEPARATE `if`, not an `else` of the one above. Both can run for the
        # same record only if `save-ledger` were both non-zero and zero, so in
        # practice they are exclusive - but the source states them as two
        # statements and they are reproduced as two.
        if arithmetic.compare(st.save_ledger, 0) == 0:
            _new_account(st)  # 315

        # 317  move     post-ledger  to  save-ledger.
        st.save_ledger = post_ledger_value

        # 319  move     post-post  to  l6-tran.
        # 320  move     post-date  to  l6-date.
        # OMITTED - print-line receivers [general/gl072.cbl:L238],
        # [general/gl072.cbl:L240].

        # 321  if       post-amount  >  zero
        # 322           move  post-amount  to  l6-debit
        # 323           add   post-amount  to  tot-dr
        # 324           move  zero         to  l6-credit
        # 325  else
        # 326           move      post-amount  to    l6-credit
        # 327           subtract  post-amount  from  tot-cr
        # 328           move      zero         to    l6-debit.
        #
        # The sign split. Its three `move`s per branch are print-line receivers
        # and are omitted; the two accumulations are arithmetic-census statements
        # and are kept. Both receivers are UNSIGNED `pic 9(8)v99`
        # [general/gl072.cbl:L165-L166] and both totals feed only the print
        # fields at [general/gl072.cbl:L389-L390], so nothing here reaches a
        # table.
        #
        # AMBIGUITY Q-19, first of its two sites. `subtract post-amount from
        # tot-cr` [general/gl072.cbl:L327] removes a NON-POSITIVE value from an
        # unsigned receiver and so accumulates a magnitude; the other site,
        # `add ledger-balance to tot-cr` [general/gl072.cbl:L427], ADDS a
        # negative value into the same receiver and arrives at the same
        # magnitude by the opposite form. Two disagreeing forms for one
        # accumulator, with no database effect either way. Offered to the
        # anomaly-log author as a candidate register entry.
        if arithmetic.compare(st.post.post_amount, 0) > 0:
            # 323  add   post-amount  to  tot-dr
            # No `ROUNDED`, so the store truncates toward zero. Same scale on
            # both sides, so nothing is actually lost - stated because
            # `rounded=False` is written at every one of the twelve sites rather
            # than left to the default.
            st.tot_dr = arithmetic.add_to(
                st.post.post_amount,
                receiver_value=st.tot_dr,
                receiving=_TOT_DR,
                rounded=False,
            )
        else:
            # 327  subtract  post-amount  from  tot-cr
            # `SUBTRACT a FROM b` with no `GIVING` means `b = b - a`. This
            # branch runs when `post-amount` is NOT greater than zero, so
            # subtracting it accumulates its magnitude - the opposite form to
            # [general/gl072.cbl:L427], which adds a negative value into the
            # same unsigned receiver and arrives at the same magnitude by a
            # different route. Question Q-19.
            st.tot_cr = arithmetic.subtract_from(
                st.post.post_amount,
                receiver_value=st.tot_cr,
                receiving=_TOT_CR,
                rounded=False,
            )

        # 330  move     post-legend  to  l6-legend.
        # OMITTED - print-line receiver [general/gl072.cbl:L245].

        # 331  add      post-amount  to  ledger-balance.
        #
        # ==================== THE POSTING - DATABASE EFFECT ====================
        # THE ONE STATEMENT IN THIS PROGRAM THAT MOVES MONEY. Every posting in
        # the sorted stream is accumulated into the nominal account's balance
        # here, and `end-account` [general/gl072.cbl:L382] is what writes the
        # accumulated figure back to `GLLEDGER-REC`.
        #
        # THE FIELDS, AND WHY BOTH DESCRIPTORS MATTER.
        #   sending   `post-amount pic s9(8)v99` [general/gl072.cbl:L118] -
        #             signed, scale 2, DISPLAY zoned, sign trailing included.
        #   receiving `Ledger-Balance pic s9(8)v99 comp-3`
        #             [copybooks/wsledger.cob:L28] - signed, scale 2, PACKED,
        #             mapping to `decimal(10,2)`.
        # Same scale, different storage class. The store is governed by the
        # RECEIVING descriptor, which is why it is named explicitly.
        #
        # NO `ROUNDED` - there is none anywhere in `gl072`, so this is a
        # TRUNCATING store toward zero, and `rounded=False` says so at the call
        # site rather than by omission. Agent Action Plan section 0.1.1:
        # "Getting this backwards would corrupt essentially every posted
        # figure."
        #
        # SIGN IS CARRIED, NOT DROPPED. `gl070`'s double-entry explosion negates
        # the credit leg with `multiply pre-amount by -1`
        # [general/gl070.cbl:L517], so negative values are routine in this
        # stream and both operands are signed at every layer - unlike the two
        # print totals above.
        #
        # This statement is what `tests/arithmetic/test_ledger_balance_
        # accumulation.py` exists to pin.
        # =======================================================================
        st.ledger.ledger_balance = arithmetic.add_to(
            st.post.post_amount,
            receiver_value=st.ledger.ledger_balance,
            receiving=_LEDGER_BALANCE,
            rounded=False,
        )

        # 333  write    print-record  from  line-6 after 1.
        # OMITTED with the print file.

        # 334  add      1 to line-cnt.
        # KEPT, and not as bookkeeping: `line-cnt` gates L335, which issues an
        # extra `UPDATE`. The receiver is `binary-char` SIGNED
        # [general/gl072.cbl:L163], so this is integer arithmetic.
        st.line_cnt = arithmetic.add_to(
            1, receiver_value=st.line_cnt, receiving=_LINE_CNT, rounded=False
        )

        # 335  if       line-cnt > Page-Lines
        # 336           perform  end-account
        # 337           perform  headings
        # 338           move     "R"  to  read-ledger
        # 339           perform  new-account.
        #
        # THE PAGE-OVERFLOW PATH, AND IT HAS A DATABASE EFFECT. `end-account`
        # begins with `perform GL-Nominal-Rewrite` [general/gl072.cbl:L382], so
        # a page break issues an EXTRA `UPDATE` of the account being posted,
        # with content identical to what the row already holds. Invisible in a
        # final-state diff, visible in statement order, and NOT suppressed here.
        #
        # AMBIGUITY Q-20 - whether that extra `UPDATE` is observable in the
        # oracle's statement order. It is reproduced either way, because Agent
        # Action Plan section 0.4.1.5 requires statement ordering to match.
        #
        # `Page-Lines` is `binary-char unsigned` [copybooks/wssystem.cob:L65], an
        # operator-configurable page depth, so how often this fires is a
        # property of the seed.
        if arithmetic.compare(
            st.line_cnt, st.system_record.system_data_block.page_lines
        ) > 0:
            _end_account(st)  # 336
            # 337  perform  headings
            # THE BARE FORM - `perform headings`, with NO `through
            # headings-end`. Distinct from the two range sites at L300 and L304
            # and recorded as distinct (rule R-5). `headings-end.`
            # [general/gl072.cbl:L369] has an empty body, so on the
            # fall-through path the two forms coincide; on the
            # `go to headings-end` path [general/gl072.cbl:L349] they may not.
            #
            # AMBIGUITY Q-21 - a finding this migration's plan does not carry.
            # The plan's class-3 reading of L349 is what is implemented, so this
            # call behaves like the two range calls. If an oracle run shows the
            # fall-through instead, the fix is confined to `_headings`'s return
            # and to this one call site.
            _headings(st)
            # 338  move     "R"  to  read-ledger
            # Arms the three suppressions inside `new-account`; reset to space
            # at [general/gl072.cbl:L431].
            st.read_ledger = move.move(_READ_LEDGER_SUPPRESSED, _READ_LEDGER)
            _new_account(st)  # 339

        # 341  go       to loop.
        # GO TO class 1 - loop-back to [general/gl072.cbl:L283]. Written
        # explicitly even though it is the last statement of the loop body,
        # because rule R-5 requires the transfer to be visible at its site.
        continue


#  headings.  [general/gl072.cbl:L343]


def _headings(st: _ProgramStorage) -> None:
    """`headings.` - a page of headings, and the batch read that gates the run.

    [general/gl072.cbl:L343-L367]

    NOT PURELY PRESENTATIONAL, WHICH IS THE POINT. Fifteen of its seventeen
    statements build print lines and are omitted; the other two carry the whole
    reason this paragraph is in the migration:

        346      perform  get-batch.
        367      move     5 to line-cnt.

    `perform get-batch` issues a `GL-Batch-Read-Next` and, through it, sets
    `We-Error`, `save-batch` and the batch record area that `end-batch` later
    stamps and rewrites. `move 5 to line-cnt` resets the paging counter that
    gates [general/gl072.cbl:L335], which performs `end-account` and therefore
    issues an `UPDATE`. Both are preserved. `add 1 to y`
    [general/gl072.cbl:L353] is preserved too, as an arithmetic-census
    statement.

        348      if       we-error  equal  999
        349               go to  headings-end.

    THE `999` BAIL-OUT SUPPRESSES `move 5 to line-cnt` AS WELL AS THE PRINTING,
    because L367 sits after the jump. So a rejected batch leaves `line-cnt`
    wherever the detail lines left it, and the next page break falls due at a
    different record than it otherwise would. That is a real consequence of the
    jump, not a print detail.

    Args:
        st: The program's storage. `y` and `line_cnt` are written here;
            `file_access`, `save_batch`, the batch record area and
            `date_formats` are written by the two paragraphs performed.
    """
    # 346  perform  get-batch.
    # THE DATABASE READ. Preserved even though every other line of this
    # paragraph is print construction.
    _get_batch(st)

    # 348  if       we-error  equal  999
    # 349           go to  headings-end.
    #
    # GO TO class 3 - paragraph exit. CLASSIFIED BY SHAPE, NOT BY NAME: the
    # target `headings-end.` [general/gl072.cbl:L369] is an EMPTY paragraph
    # immediately following this one, whose only role is to terminate the
    # `PERFORM ... THRU` range at [general/gl072.cbl:L300] and
    # [general/gl072.cbl:L304]. Jumping to the end of a range and falling off it
    # is a paragraph exit, so the transformation is `return`.
    #
    # The reservation on that reading, for the BARE `perform headings` at
    # [general/gl072.cbl:L337], is AMBIGUITY Q-21 in the module docstring. The
    # Agent Action Plan's taxonomy is followed here.
    #
    # `999` is `WeError.NOT_USED` [copybooks/wsfnctn.cob:L23], set by
    # `get-batch` at [general/gl072.cbl:L459] - never the bare literal.
    if arithmetic.compare(st.file_access.we_error, WeError.NOT_USED) == 0:
        return  # 349

    # 351  perform  zz070-convert-date.
    _zz070_convert_date(st)

    # 352  move     ws-date  to  l3-date.
    # OMITTED - print-line receiver [general/gl072.cbl:L221].

    # 353  add      1  to  y.
    # The page number. Print-only in consumption - `move y to l1-page` L354 and
    # `if y not = 1` L357 are its only readers, both presentation - but an
    # arithmetic statement, so it goes through the arithmetic layer with `y`'s
    # own `pic 99` descriptor [general/gl072.cbl:L164].
    st.y = arithmetic.add_to(
        1, receiver_value=st.y, receiving=_Y, rounded=False
    )

    # 354  move     y  to  l1-page.
    # 355  move     scycle  to  l3-cycle.
    # 356  move     post-batch  to  l3-batch.
    # OMITTED - print-line receivers [general/gl072.cbl:L210],
    # [general/gl072.cbl:L214], [general/gl072.cbl:L216]. L355 is the only read
    # of `Scycle` [copybooks/wssystem.cob:L63] in the whole program and it goes
    # nowhere but the page heading.

    # 357  if       y not = 1
    # 358           write print-record from line-1 after page
    # 359           write print-record from line-3 after 1
    # 360           move spaces to print-record
    # 361           write print-record after 1
    # 362  else
    # 363           write print-record from line-1 before 1
    # 364           write print-record from line-3 before 1.
    # 365  write    print-record  from  line-4 after 1.
    # 366  write    print-record  from  line-5 after 1.
    # OMITTED with the print file. BOTH BRANCHES OF L357 CONSIST SOLELY OF
    # `write print-record` STATEMENTS - the first page is written `before 1` and
    # every later page `after page`, a carriage-control difference and nothing
    # else - so once the print file is omitted the conditional has no body left
    # on either side. It is therefore recorded as an omission rather than
    # reproduced as an `if` with two empty branches, which would be dead code
    # masquerading as fidelity. `y` is kept and accumulated because L353 is an
    # arithmetic statement; it becomes write-only, and that is stated rather
    # than hidden.

    # 367  move     5 to line-cnt.
    # KEPT. Reached only when the `999` bail-out did NOT fire, and it is what
    # makes the page-break test at [general/gl072.cbl:L335] count from the
    # bottom of a fresh heading block.
    st.line_cnt = move.move(_LINE_CNT_AFTER_HEADINGS, _LINE_CNT)


#  headings-end.  [general/gl072.cbl:L369]


def _headings_end() -> None:
    """`headings-end.` - the `PERFORM ... THRU` range terminator; EMPTY.

    [general/gl072.cbl:L369-L370]

        369  headings-end.
        370 *>***********

    THE PARAGRAPH HAS NO STATEMENTS AT ALL. Its two source lines are the label
    and the maintainer's underline comment; the next line of executable source is
    `end-batch.` [general/gl072.cbl:L372]. It exists solely to give the two
    `PERFORM ... THRU` statements at [general/gl072.cbl:L300] and
    [general/gl072.cbl:L304] a range end, and to give the `go to headings-end` at
    [general/gl072.cbl:L349] somewhere to land.

    THIS IS NOT A STUB, AND ITS EMPTY BODY IS NOT A PLACEHOLDER. There is nothing
    deferred, nothing unimplemented and nothing to add: an empty COBOL paragraph
    reproduced faithfully is an empty function. The function exists because rule
    R-5 requires a named function for every paragraph, and Agent Action Plan
    section 0.7.4 C-4 says so verbatim - "every paragraph retains a named
    function even where its `GO TO` becomes a `continue`, a `break` or a
    `return`". It takes no argument because the paragraph reads and writes
    nothing.

    Both range call sites call it explicitly after `_headings`, so the range's
    two members are visible as two calls rather than collapsed into one.
    """
    # The paragraph's body, in full: nothing. Its docstring is its
    # implementation, because there is no statement between
    # [general/gl072.cbl:L369] and [general/gl072.cbl:L372] to reproduce.


#  end-batch.  [general/gl072.cbl:L372]


def _end_batch(st: _ProgramStorage) -> None:
    """`end-batch.` - stamp the batch cleared and posted, and rewrite it.

    [general/gl072.cbl:L372-L377]

        375      move     1  to  cleared-status.
        376      move     run-date  to  posted.
        377      perform  GL-Batch-Rewrite.

    THREE STATEMENTS, ALL THREE A DATABASE EFFECT, AND THE WHOLE PARAGRAPH.
    There is no print work here at all - unique among the three paragraphs that
    touch a table.

    DECLARED BEFORE `end-account.` [general/gl072.cbl:L379] AND CALLED AFTER IT.
    Both call sites - the at-end clause [general/gl072.cbl:L287-L288] and the
    batch break [general/gl072.cbl:L297-L298] - perform `end-account` first. The
    functions in this file are declared in SOURCE order, so this one precedes
    `_end_account` here exactly as the paragraphs do, and the reversal is
    recorded in the traceability footer so a reader diffing the two files is not
    misled. Agent Action Plan section 0.6.4: "Inverting them would produce a
    batch marked posted with an unclosed final account."

    IT RUNS EVEN WHEN NOTHING WAS POSTED. On an empty `post-trans` the very first
    read reports at end and this paragraph rewrites whatever the batch record
    area holds - which, no `GL-Batch-Read-Next` having run, is an all-default
    record. Reproduced; no guard is invented (rule R-3).

    THE PARALLEL IN `gl080`, FOR CONTRAST. The end-of-cycle program stamps the
    same two fields with different values - `cleared-status` becomes `2`, the
    `Archived` condition name, and the date goes to `stored` rather than `posted`
    [general/gl080.cbl:L585-L586]. Same shape, different meaning, different
    program; noted because the similarity invites copying one into the other.

    Args:
        st: The program's storage. `batch.cleared_status` and
            `batch.dates.posted` are written, then the row is rewritten through
            the batch facade context. `system_record` is read for the run date.
    """
    # 375  move     1  to  cleared-status.
    #
    # DATABASE EFFECT. `1` is the `88 Processed` condition name on
    # `03 Cleared-Status pic 9.` [copybooks/wsbatch.cob:L29-L31]; the sibling
    # values are `88 Waiting value 0.` and `88 Archived value 2.`. The value is
    # taken FROM THE CONDITION-NAME VOCABULARY rather than written as a bare
    # integer, so the meaning and the number cannot drift apart, and it is stored
    # through the field's own descriptor.
    st.batch.cleared_status = move.move(
        condition_names.values_for("Processed")[0], _CLEARED_STATUS
    )

    # 376  move     run-date  to  posted.
    #
    # DATABASE EFFECT, AND A CONTROLLED-CLOCK OBSERVABLE. `Run-Date` is
    # `binary-long` on the system record [copybooks/wssystem.cob:L67] and
    # `Posted` is `binary-long` on the batch record
    # [copybooks/wsbatch.cob:L38] - one of exactly two date observables the
    # controlled clock pins, the other being the `to-day pic x(10)` text date.
    #
    # IT IS READ FROM THE LINKAGE, NEVER FROM A CLOCK (rule R-6). `gl072`
    # contains zero clock reads; the single read in the whole call chain is in
    # the menu shell's date-service copybook
    # [copybooks/Proc-ACAS-Mapser-RDB.cob:L72-L80], and injection belongs at the
    # command-line boundary. This module imports no clock module at all.
    #
    # This is one of the two values
    # `tests/determinism/test_two_runs_byte_identical.py` depends on being
    # pinned: it lands in a column, so an unpinned run would differ in a state
    # diff by a date and nothing else.
    st.batch.dates.posted = move.move(
        st.system_record.system_data_block.run_date,
        _POSTED,
        sending_field=_RUN_DATE,
    )

    # 377  perform  GL-Batch-Rewrite.        *> rewrite  batch-record.
    #
    # DATABASE EFFECT - the `UPDATE` of `GLBATCH-REC`
    # [copybooks/Proc-ACAS-FH-Calls.cob:L475-L478]. Its reply is NOT tested: the
    # frozen source performs the verb and moves on, and
    # `Proc-ACAS-FH-Calls.cob` publishes no error-check paragraph, so no check is
    # invented (rule R-3). A failed rewrite therefore leaves the batch unstamped
    # and the run continues - which is the frozen rejection behaviour, not an
    # oversight to correct.
    facade.gl_batch_rewrite(st.batch_ctx)


#  end-account.  [general/gl072.cbl:L379]


def _end_account(st: _ProgramStorage) -> None:
    """`end-account.` - rewrite the nominal account, then print its totals.

    [general/gl072.cbl:L379-L400]

        382      perform  GL-Nominal-Rewrite.
        384      write    print-record  from  line-7 after 1.
        385      add      1 to line-cnt.
        386      divide   WS-Ledger-Nos  by  100  giving  l6-account.
        387-393  ... seven moves into print-line fields ...
        395-396  write    print-record  ... twice ...
        398-399  move     spaces to print-record / write print-record after 1.
        400      add      3 to line-cnt.

    THE REWRITE COMES FIRST, BEFORE ANY PRINT WORK, and that ordering is
    preserved: it is the statement that persists the balance
    [general/gl072.cbl:L331] accumulated into.

    CALLED FROM FOUR SITES, one of which is not an account break at all:
    the at-end clause [general/gl072.cbl:L287], the batch break
    [general/gl072.cbl:L297], the account break [general/gl072.cbl:L311] and the
    PAGE BREAK [general/gl072.cbl:L336]. The last of those is why a page overflow
    issues an extra `UPDATE` of a row whose content has not changed - question
    Q-20.

    IT RUNS BEFORE ANY ACCOUNT HAS BEEN READ, on an empty `post-trans` and on the
    first batch break of a run that produced no records, and rewrites the default
    ledger record area. Reproduced; no guard is invented.

    Args:
        st: The program's storage. The nominal row is rewritten through the
            ledger facade context; `line_cnt` and `l6_account` are written.
    """
    # 382  perform  GL-Nominal-Rewrite.      *> rewrite  ledger-record.
    #
    # ==================== DATABASE EFFECT - THE LEDGER UPDATE ==================
    # The `UPDATE` of `GLLEDGER-REC` [copybooks/Proc-ACAS-FH-Calls.cob:L349-L352]
    # that persists the balance accumulated by [general/gl072.cbl:L331]. FIRST
    # STATEMENT OF THE PARAGRAPH, before any print work, exactly as written.
    #
    # Its reply is NOT tested, for the same reason as the batch rewrite: the
    # source performs the verb and continues, and this facade vocabulary has no
    # error-check paragraph. No check is invented (rule R-3).
    # ==========================================================================
    facade.gl_nominal_rewrite(st.ledger_ctx)

    # 384  write    print-record  from  line-7 after 1.
    # OMITTED with the print file. `line-7` [general/gl072.cbl:L247-L251] is the
    # rule of `=` characters that underlines the totals.

    # 385  add      1 to line-cnt.
    # KEPT - paging state that gates [general/gl072.cbl:L335].
    st.line_cnt = arithmetic.add_to(
        1, receiver_value=st.line_cnt, receiving=_LINE_CNT, rounded=False
    )

    # 386  divide   WS-Ledger-Nos  by  100  giving  l6-account.
    #
    # PRESENTATION ONLY, AND STILL AN ARITHMETIC STATEMENT. `DIVIDE a BY b
    # GIVING c` means `c = a / b`, so this is `WS-Ledger-Nos / 100` - the account
    # number [copybooks/wsledger.cob:L14] is held scaled by 100 and printed as
    # `9999.99`. The receiver `l6-account` [general/gl072.cbl:L233] is an EDITED
    # print field, so the result reaches no table.
    #
    # It goes through `divide_by_giving` and never a bare division (rule R-2),
    # with the receiving descriptor supplied so the store obeys the picture. No
    # edited MOVE is attempted: this picture is all-`9` with an inserted point
    # and `blank when zero`, not the leading-`Z` suppression shape, so the
    # character image is unobservable once the print file is gone - AMBIGUITY
    # Q-14, inherited from `acas_posting.cobol.move`, which owns the answer. The
    # stored VALUE is what `divide_by_giving` answers with, and that is all that
    # is kept.
    #
    # NO `ROUNDED` and NO `REMAINDER` - the remainder is discarded, which for a
    # six-digit account number over 100 into a four-and-two receiver is exact
    # anyway.
    st.l6_account = arithmetic.divide_by_giving(
        st.ledger.ws_ledger_key.ws_ledger_nos,
        _ACCOUNT_NUMBER_DIVISOR,
        _L6_ACCOUNT,
        rounded=False,
    )

    # 387  move     ledger-pc       to  l6-pc.
    # 388  move     ledger-balance  to  l6-balance.
    # 389  move     tot-dr          to  l6-debit.
    # 390  move     tot-cr          to  l6-credit.
    # 391  move     to-day          to  l6-date.
    # 392  move     ledger-name     to  l6-legend.
    # 393  move     zero            to  l6-tran.
    # OMITTED - seven print-line receivers [general/gl072.cbl:L235],
    # [general/gl072.cbl:L237], [general/gl072.cbl:L241],
    # [general/gl072.cbl:L243], [general/gl072.cbl:L240],
    # [general/gl072.cbl:L245], [general/gl072.cbl:L238]. L389 and L390 ARE THE
    # ONLY CONSUMERS OF `tot-dr` AND `tot-cr` in the program, which is what makes
    # both totals presentation-only and AMBIGUITY Q-19 harmless. L391 is one of
    # only two reads of the `to-day` linkage parameter, the other being
    # [general/gl072.cbl:L475].

    # 395  write    print-record  from  line-6 after 1.
    # 396  write    print-record  from  line-7 after 1.
    # 398  move     spaces  to  print-record.
    # 399  write    print-record after 1.
    # OMITTED with the print file.

    # 400  add      3 to line-cnt.
    # KEPT - the three lines just written, charged to the page. Gates
    # [general/gl072.cbl:L335].
    st.line_cnt = arithmetic.add_to(
        3, receiver_value=st.line_cnt, receiving=_LINE_CNT, rounded=False
    )


#  new-account.  [general/gl072.cbl:L402]


def _new_account(st: _ProgramStorage) -> None:
    """`new-account.` - position on the next account, print its brought forward.

    [general/gl072.cbl:L402-L435]

        405      move     post-ledger  to  WS-Ledger-Key.
        407      if       read-ledger not = "R"
        408               perform  GL-Nominal-Read-Next.
        410      if       read-ledger not = "R"
        411               move  zero   to  tot-dr  tot-cr.
        413      divide   WS-Ledger-Nos  by  100  giving  l6-account.
        414-419  ... print moves, and `perform zz070-convert-date.` at L418 ...
        421      if       read-ledger not = "R"
        422               if    ledger-balance  >  zero
        423                     move  ledger-balance  to  l6-debit
        424                     add   ledger-balance  to  tot-dr
        425               else
        426                     move  ledger-balance  to  l6-credit
        427                     add   ledger-balance  to  tot-cr.
        429      move     "Brought Forward"  to  l6-legend.
        430      move     zero            to  l6-tran.
        431      move     space  to  read-ledger.
        433-435  ... print write, `add 2 to line-cnt`, `move zero to l6-balance` ...

    WHERE ANOMALY A-14 LIVES. See the comment at L405-L408 below.

    THE THREE `read-ledger` GUARDS ARE THREE SEPARATE `if` STATEMENTS AND ARE NOT
    MERGED. Between the first and the second nothing intervenes, which is what
    makes merging look free; between the second and the third the print work at
    L413-L419 runs UNCONDITIONALLY, including `perform zz070-convert-date` at
    L418 - which writes `Date-Form` on the system record when it is zero
    [general/gl072.cbl:L477-L478] and is therefore not print-only in effect. So
    the second and third cannot be merged at all, and merging the first two would
    leave one guard where the source has three, breaking paragraph-level
    traceability for no gain (rule R-3, rule R-5).

    WHAT THE FLAG SUPPRESSES, AND WHY. `read-ledger` is `"R"` only on the
    page-overflow path [general/gl072.cbl:L338]. On that path the ACCOUNT HAS NOT
    CHANGED - only the paper has - so the sequential read must not advance, the
    running totals must not reset, and the brought-forward figures must not be
    re-accumulated. All three are suppressed; the heading line is still printed.

    Args:
        st: The program's storage. `ledger.ws_ledger_key`, `tot_dr`, `tot_cr`,
            `l6_account`, `line_cnt`, `read_ledger`, `date_formats` and - through
            the read - the whole ledger record area are written.
    """
    # 405  move     post-ledger  to  WS-Ledger-Key.
    #
    # ANOMALY A-14 [general/gl072.cbl:L405-L408] - the nominal-ledger account for
    # a posting is located by a SEQUENTIAL read-next, not an indexed read, even
    # though L405 has just set WS-Ledger-Key. Correctness depends entirely on
    # gl071 having emitted post-trans in (batch, ac, pc, post) ascending order
    # [general/gl071.cbl:L173-L176]. A wrong sort produces silent misposting - no
    # error, no diagnostic, wrong balances (AAP section 0.6.4 ordering dep. 1).
    # Reproduced deliberately per R-4; DO NOT FIX. Converting to an indexed read
    # is forbidden by AAP section 0.8.4.
    #
    # THE KEY MOVE IS PART OF THE ANOMALY, NOT A LEFTOVER. It is reproduced in
    # full - a group-to-group `MOVE` of eight characters, split back into the
    # receiving group's two children under their own pictures - because it is
    # what makes the missing indexed read look deliberate to a reader, and
    # because `GL-Nominal-Read-Indexed` and `GL-Nominal-Start` both exist in the
    # same facade copybook [copybooks/Proc-ACAS-FH-Calls.cob:L339-L342],
    # [copybooks/Proc-ACAS-FH-Calls.cob:L324-L327] and are NOT performed here.
    # Deleting the move would hide the anomaly rather than reproduce it.
    #
    # Every conversion is delegated: the sending image comes from
    # `_post_ledger_group_image`, the group-to-group carry from `move_group`, and
    # each child's store from `move_numeric` under its own descriptor. No digit
    # formatting, no padding rule and no slicing arithmetic is written here
    # (rule R-2, Agent Action Plan section 0.3.1).
    ws_ledger_key_image = move.move_group(
        _post_ledger_group_image(st.post),
        _WS_LEDGER_KEY,
        sending_field=_POST_LEDGER,
    )
    st.ledger.ws_ledger_key.ws_ledger_nos = move.move_numeric(
        move.ref_mod(ws_ledger_key_image, *_WS_LEDGER_NOS_POSITION),
        _WS_LEDGER_NOS,
    )
    st.ledger.ws_ledger_key.ledger_pc = move.move_numeric(
        move.ref_mod(ws_ledger_key_image, *_LEDGER_PC_POSITION),
        _LEDGER_PC,
    )

    # 407  if       read-ledger not = "R"
    # 408           perform  GL-Nominal-Read-Next.   *> read ledger-file record.
    #
    # GUARD ONE OF THREE. THE SEQUENTIAL READ - see the A-14 comment above. Its
    # reply is NOT tested: the source performs the verb and continues, so a read
    # that fails or hits end-of-file leaves the previous account in the record
    # area and the next posting accumulates into it. That is the frozen
    # behaviour and no check is invented (rule R-3).
    #
    # The comparison is a direct one-character test, and it is the ONLY direct
    # comparison in this module. `acas_posting.cobol.arithmetic.compare` is the
    # algebraic numeric relation and rejects a non-numeric operand by design;
    # `read-ledger` is `pic x` [general/gl072.cbl:L162] holding `"R"` or a space,
    # and the semantics layer publishes no alphanumeric comparator, so there is
    # nothing to delegate to. Both operands are single characters produced by
    # `move` under that same descriptor, so the test is exact.
    if st.read_ledger != _READ_LEDGER_SUPPRESSED:
        facade.gl_nominal_read_next(st.ledger_ctx)  # 408

    # 410  if       read-ledger not = "R"
    # 411           move  zero   to  tot-dr  tot-cr.
    #
    # GUARD TWO OF THREE, a SEPARATE `if` with the same condition. A TWO-RECEIVER
    # `MOVE` of the figurative constant; each receiver is converted under its own
    # `pic 9(8)v99` and both land at scale 2.
    if st.read_ledger != _READ_LEDGER_SUPPRESSED:
        st.tot_dr, st.tot_cr = move.move_to_all(
            Figurative.ZERO, [_TOT_DR, _TOT_CR]
        )  # 411

    # 413  divide   WS-Ledger-Nos  by  100  giving  l6-account.
    #
    # UNCONDITIONAL - it sits between guard two and guard three. Presentation
    # only, exactly as at [general/gl072.cbl:L386]; see that site for why the
    # edited receiver is not moved into. Note that on the page-overflow path the
    # sequential read above did NOT run, so this divides the SAME account number
    # again and reprints it, which is the intent.
    st.l6_account = arithmetic.divide_by_giving(
        st.ledger.ws_ledger_key.ws_ledger_nos,
        _ACCOUNT_NUMBER_DIVISOR,
        _L6_ACCOUNT,
        rounded=False,
    )

    # 414  move     ledger-pc       to  l6-pc.
    # 415  move     ledger-balance  to  l6-balance.
    # 416  move     zero            to  l6-debit.
    # 417  move     zero            to  l6-credit.
    # OMITTED - print-line receivers [general/gl072.cbl:L235],
    # [general/gl072.cbl:L237], [general/gl072.cbl:L241],
    # [general/gl072.cbl:L243].

    # 418  perform  zz070-convert-date.
    # UNCONDITIONAL, AND NOT PRINT-ONLY IN EFFECT. It writes `Date-Form` on the
    # system record when that field is zero [general/gl072.cbl:L477-L478], and
    # `Date-Form` is a `SYSTEM-REC` column, so the write is diff-visible. It is
    # therefore preserved here even though its other product, `ws-date`, feeds
    # only the print line at L419.
    _zz070_convert_date(st)

    # 419  move     ws-date         to  l6-date.
    # OMITTED - print-line receiver [general/gl072.cbl:L240].

    # 421  if       read-ledger not = "R"
    # 422           if    ledger-balance  >  zero
    # 423                 move  ledger-balance  to  l6-debit
    # 424                 add   ledger-balance  to  tot-dr
    # 425           else
    # 426                 move  ledger-balance  to  l6-credit
    # 427                 add   ledger-balance  to  tot-cr.
    #
    # GUARD THREE OF THREE, wrapping a NESTED `if` - the brought-forward split.
    # The two `move`s are print-line receivers and are omitted; the two
    # accumulations are arithmetic-census statements and are kept. Both totals
    # are consumed only by [general/gl072.cbl:L389-L390], so nothing here reaches
    # a table.
    if st.read_ledger != _READ_LEDGER_SUPPRESSED:
        if arithmetic.compare(st.ledger.ledger_balance, 0) > 0:
            # 424  add   ledger-balance  to  tot-dr
            st.tot_dr = arithmetic.add_to(
                st.ledger.ledger_balance,
                receiver_value=st.tot_dr,
                receiving=_TOT_DR,
                rounded=False,
            )
        else:
            # 427  add   ledger-balance  to  tot-cr
            # AMBIGUITY Q-19, second of its two sites. This branch runs when the
            # balance is NOT greater than zero, so a NEGATIVE value is ADDED into
            # an UNSIGNED `pic 9(8)v99` receiver [general/gl072.cbl:L166] and the
            # sign is dropped on store, leaving the magnitude. The other site,
            # [general/gl072.cbl:L327], SUBTRACTS a non-positive value from the
            # same receiver and arrives at the same magnitude by the opposite
            # form. The store rule belongs to the semantics layer, which is why
            # nothing is done about the sign here.
            st.tot_cr = arithmetic.add_to(
                st.ledger.ledger_balance,
                receiver_value=st.tot_cr,
                receiving=_TOT_CR,
                rounded=False,
            )

    # 429  move     "Brought Forward"  to  l6-legend.
    # 430  move     zero            to  l6-tran.
    # OMITTED - print-line receivers [general/gl072.cbl:L245],
    # [general/gl072.cbl:L238].

    # 431  move     space  to  read-ledger.
    # THE RESET, and it is unconditional. Without it every account after the
    # first page break would skip its own sequential read and its own totals
    # reset - so this single statement is what confines the three suppressions to
    # exactly one invocation.
    st.read_ledger = move.move(Figurative.SPACE, _READ_LEDGER)

    # 433  write    print-record  from  line-6 after 2.
    # OMITTED with the print file.

    # 434  add      2 to line-cnt.
    # KEPT - paging state that gates [general/gl072.cbl:L335].
    st.line_cnt = arithmetic.add_to(
        2, receiver_value=st.line_cnt, receiving=_LINE_CNT, rounded=False
    )

    # 435  move     zero  to  l6-balance.
    # OMITTED - print-line receiver [general/gl072.cbl:L237].


#  end-run.  [general/gl072.cbl:L437]


def _end_run(st: _ProgramStorage) -> None:
    """`end-run.` - the closes. The class-2 post-loop block.

    [general/gl072.cbl:L437-L443]

        440      close    post-trans print-file.
        441      perform  GL-Batch-Close.
        442      perform  GL-Nominal-Close.
        443      call     "SYSTEM" using Print-Report.

    REACHED ONLY BY `go to end-run` FROM THE AT-END CLAUSE
    [general/gl072.cbl:L289] - there is no other path to it and no fall-through
    into it, because `loop.` always transfers. It is the target of the module's
    single class-2 `GO TO`, and it does REAL WORK, which is why the
    transformation is `break` plus this block placed after the loop rather than
    `break` alone. Agent Action Plan section 0.6.3: "Mis-splitting here would
    silently drop end-of-run processing."

    Control falls through from here into `main-exit.` [general/gl072.cbl:L445].

    Args:
        st: The program's storage. The work sequence is closed and both facade
            files are closed; `file_access.fs_reply` is written by the close.
    """
    # 440  close    post-trans print-file.
    # The work sequence's close. `print-file` is closed by the same statement and
    # is omitted with the print file - the ONE statement in this program that
    # mixes a kept operand with an omitted one, which is why it is called out
    # rather than left to be noticed.
    st.work_files.post_trans.close()
    # `status fs-reply` [general/gl072.cbl:L97] once more; see `_gl072_main`.
    st.file_access.fs_reply = move.move(
        st.work_files.post_trans.fs_reply, _FS_REPLY
    )

    # 441  perform  GL-Batch-Close.
    # [copybooks/Proc-ACAS-FH-Calls.cob:L439-L442]. Reply not tested.
    facade.gl_batch_close(st.batch_ctx)

    # 442  perform  GL-Nominal-Close.
    # [copybooks/Proc-ACAS-FH-Calls.cob:L319-L322]. Reply not tested.
    facade.gl_nominal_close(st.ledger_ctx)

    # 443  call     "SYSTEM" using Print-Report.
    #
    # OMITTED, DELIBERATELY, AND FOR TWO INDEPENDENT REASONS. Agent Action Plan
    # section 0.2.2 excludes "the `call "SYSTEM" using Print-Report` spool-out
    # path wherever it appears", and rule R-1 forbids handing anything to the
    # operating system from the migrated cycle. It hands the finished print file
    # to a shell command and has NO database effect whatsoever, so omitting it
    # cannot change a table. Nothing here starts a process, and nothing in this
    # module imports a process-spawning facility. Recorded in the traceability
    # footer as an omission so that a reader comparing the two files does not
    # conclude something was lost.


#  main-exit.  [general/gl072.cbl:L445]  (in gl072-Main section)


def _gl072_main_main_exit() -> None:
    """`main-exit.` of `gl072-Main section.` - the `goback`.

    [general/gl072.cbl:L445-L446]

        445  main-exit.
        446      goback.

    SECTION-QUALIFIED, BECAUSE THE PARAGRAPH NAME REPEATS. `gl072` declares
    `main-exit.` TWICE - here in `gl072-Main section.` [general/gl072.cbl:L268]
    and again in `get-batch section.` [general/gl072.cbl:L464] - so neither
    Python function can be called `_main_exit` without ambiguity, and rule R-5's
    paragraph-to-function mapping would stop being one-to-one. The two are
    `_gl072_main_main_exit` and `_get_batch_main_exit`, and they are NOT
    interchangeable: this one ends the program, the other is a no-operation.

    Reached by FALLING THROUGH from `end-run.` [general/gl072.cbl:L437], not by a
    transfer - `end-run` ends on the omitted spool-out call with no `GO TO` - so
    `run` calls this immediately after `_end_run` to make the fall-through
    visible.

    `goback` in a called program returns control to its caller, leaving the
    linkage block as it stands. `gl072` never writes `WS-Term-Code`, so the value
    the menu reads back is the zero `load00.` moved in before the `CALL`
    [general/general.cbl:L714]: this program cannot abort the cycle the way
    `gl070` can.
    """
    # 446  goback.
    # Return to the caller - `general/general.cbl` `load00.`
    # [general/general.cbl:L711-L722] in a real run - with the linkage untouched.
    return


#  get-batch section.  [general/gl072.cbl:L448]


def _get_batch(st: _ProgramStorage) -> None:
    """`get-batch section.` - read the batch header and set or clear the sentinel.

    [general/gl072.cbl:L448-L464]

        451      move     1           to  WS-Ledger.
        452      move     post-batch  to  save-batch  WS-Batch-Nos.
        454      perform  GL-Batch-Read-Next.
        456      move     description of WS-Batch-Record to  l3-desc.
        458      if       not waiting
        459               move  999  to  we-error
        460               move  0    to  save-batch
        461      else
        462               move  0    to  we-error.

    THE ONLY SETTER OF THE `999` SENTINEL, AND THE ONLY READER OF THE BATCH FILE.
    Performed from exactly one place, `headings.` [general/gl072.cbl:L346].
    Everything the rest of the program does with `We-Error` follows from the four
    lines at L458-L462: the batch-break suppression [general/gl072.cbl:L296], the
    heading bail-out [general/gl072.cbl:L348] and silent skip (b)
    [general/gl072.cbl:L306]. The chain is drawn in the module docstring.

    IT ALSO ZEROES `save-batch` ON REJECTION [general/gl072.cbl:L460], which is
    subtler than it looks: a zero `save-batch` re-satisfies
    [general/gl072.cbl:L302] on the very next record, so `headings` - and
    therefore this section - runs AGAIN for every remaining record of a rejected
    batch. The sentinel is re-derived per record rather than latched.

    THE READ IS SEQUENTIAL, WHICH IS QUESTION Q-22. Both key moves happen first
    and then a `Read-Next` is performed; `gl072` never performs `GL-Batch-Start`
    and never performs `GL-Batch-Read-Indexed`. Same shape as anomaly A-14, on a
    different file, and with a larger consequence because `end-batch` stamps
    whatever row this leaves in the record area.

    Args:
        st: The program's storage. `batch.ws_batch_key`, `save_batch` and
            `file_access.we_error` are written; the whole batch record area is
            replaced by the read.
    """
    # 451  move     1           to  WS-Ledger.
    # `1` is the `88 GL-Batch` condition name on `03 WS-Ledger pic 9.`
    # [copybooks/wsbatch.cob:L15-L16] - the ledger selector inside the composite
    # batch key. Taken from the condition-name vocabulary rather than written as
    # a bare integer.
    st.batch.ws_batch_key.ws_ledger = move.move(
        condition_names.values_for("GL-Batch")[0], _WS_LEDGER
    )

    # 452  move     post-batch  to  save-batch  WS-Batch-Nos.
    # A TWO-RECEIVER `MOVE` ACROSS DIFFERENT PICTURES - `save-batch pic 9(5)`
    # [general/gl072.cbl:L160] and `WS-Batch-Nos pic 9(5)`
    # [copybooks/wsbatch.cob:L19]. Each receiver is converted INDEPENDENTLY under
    # its own picture; one conversion assigned twice would be wrong in general
    # even where it happens to agree here.
    st.save_batch, st.batch.ws_batch_key.ws_batch_nos = move.move_to_all(
        st.post.post_batch,
        [_SAVE_BATCH, _WS_BATCH_NOS],
        sending_field=_POST_BATCH,
    )

    # 454  perform  GL-Batch-Read-Next.      *> read     batch-file  record.
    # [copybooks/Proc-ACAS-FH-Calls.cob:L460-L463]. SEQUENTIAL.
    #
    # AMBIGUITY Q-22 - a finding this migration's plan does not carry, and the
    # same key-then-sequential-read shape as anomaly A-14, here on the batch
    # file. The two key moves at [general/gl072.cbl:L451-L452] position nothing,
    # because this program never performs `GL-Batch-Start` and never performs
    # `GL-Batch-Read-Indexed`. It matters MORE than A-14 does: `end-batch`
    # stamps whatever row is in the record area and rewrites it
    # [general/gl072.cbl:L375-L377], so a read landing elsewhere stamps a
    # different batch. Faithful either way - the same verb after the same two
    # moves. Offered to the anomaly-log author as a candidate register entry.
    # The reply is NOT tested: on end-of-file the record area keeps the previous
    # batch, and the `not waiting` test below then judges THAT row. Frozen
    # behaviour; no check is invented (rule R-3).
    facade.gl_batch_read_next(st.batch_ctx)

    # 456  move     description of WS-Batch-Record to  l3-desc.
    # OMITTED - print-line receiver [general/gl072.cbl:L219]. The QUALIFIED
    # reference `description of WS-Batch-Record` is worth recording even though
    # the statement is dropped: `Description` collides across posting copybooks,
    # which is why the source has to qualify it at all - the same collision the
    # anomaly register notes at [general/gl070.cbl:L510].

    # 458  if       not waiting
    # 459           move  999  to  we-error
    # 460           move  0    to  save-batch
    # 461  else
    # 462           move  0    to  we-error.
    #
    # `88 Waiting value 0.` on `03 Cleared-Status pic 9.`
    # [copybooks/wsbatch.cob:L29-L30]. The test goes through the condition-name
    # vocabulary, so the `88`-level's values come from the copybook and not from a
    # literal written here.
    if not condition_names.is_waiting(st.batch.cleared_status):
        # 459  move  999  to  we-error
        # `999` IS `WeError.NOT_USED` [copybooks/wsfnctn.cob:L23] - the handler
        # vocabulary's "not used" sentinel, borrowed here as a private flag. It
        # does NOT mean an error occurred, and the enum member is used precisely
        # so nobody reads it as one. THIS IS WHERE THE CHAIN THAT PRODUCES SILENT
        # SKIP (b) [general/gl072.cbl:L306-L307] BEGINS.
        st.file_access.we_error = move.move(WeError.NOT_USED, _WE_ERROR)
        # 460  move  0    to  save-batch
        # Forces `headings` to run again for the next record; see the docstring.
        st.save_batch = move.move(0, _SAVE_BATCH)
    else:
        # 462  move  0    to  we-error
        # Clears the sentinel for an accepted batch. Note that a literal `0` is
        # written here and at L460, not the figurative `zero` used at
        # [general/gl072.cbl:L281] and [general/gl072.cbl:L411]; the distinction
        # is preserved because the source draws it.
        st.file_access.we_error = move.move(0, _WE_ERROR)

    # 464  main-exit.   exit.
    # Fall-through into the section's exit paragraph, called explicitly.
    _get_batch_main_exit()


#  main-exit.  [general/gl072.cbl:L464]  (in get-batch section)


def _get_batch_main_exit() -> None:
    """`main-exit.` of `get-batch section.` - a plain `EXIT`, a no-operation.

    [general/gl072.cbl:L464-L465]

        464  main-exit.   exit.
        465 *>********    ****

    A PLAIN `EXIT`, NOT `exit section.` COBOL's `EXIT` statement is a
    NO-OPERATION whose only purpose is to give a series of procedures a common
    end point; it transfers nothing. Contrast `zz070-Exit.`
    [general/gl072.cbl:L494-L495], which really does write `exit section.` and
    really does transfer. The two spellings sit thirty lines apart in the same
    file and mean different things, which is exactly the kind of small
    inconsistency rule R-5 exists to surface rather than smooth away.

    So control returns to `headings.` [general/gl072.cbl:L346] not because of
    this statement but because this is the LAST PARAGRAPH of the performed
    section and the section's implicit end is the `PERFORM`'s return point. The
    `return` below is that no-operation completing, after which `_get_batch`
    itself returns - which is where the section exit actually happens.

    SECTION-QUALIFIED because `main-exit.` also names a paragraph of
    `gl072-Main section.` [general/gl072.cbl:L445]; see `_gl072_main_main_exit`.
    """
    # 464  exit.
    # The no-operation. Nothing is transferred and nothing is computed.
    return


#  zz070-Convert-Date section.  [general/gl072.cbl:L467]


def _zz070_convert_date(st: _ProgramStorage) -> None:
    """`zz070-Convert-Date section.` - reformat `to-day` into the configured form.

    [general/gl072.cbl:L467-L492]

        475      move     to-day to ws-date.
        477      if       Date-Form = zero
        478               move 1 to Date-Form.
        479      if       Date-UK
        480               go to zz070-Exit.
        481      if       Date-USA                *> swap month and days
        482               move ws-days to ws-swap
        483               move ws-month to ws-days
        484               move ws-swap to ws-month
        485               go to zz070-Exit.
        489      move     "ccyy/mm/dd" to ws-date.  *> swap Intl to UK form
        490      move     to-day (7:4) to ws-Intl-Year.
        491      move     to-day (4:2) to ws-Intl-Month.
        492      move     to-day (1:2) to ws-Intl-Days.

    CONSOLIDATED, AND THAT IS SAFE HERE. This section is BYTE-IDENTICAL across
    its ten carriers, so it lives once in `acas_posting.dates` and is called
    rather than re-implemented - the one place in this migration where
    consolidation is unambiguously safe because the bodies are textually equal.
    The two class-3 `GO TO`s at L480 and L485, the `REDEFINES` views
    [general/gl072.cbl:L184-L201] and the three ONE-BASED reference
    modifications at L490-L492 all belong to that shared implementation, which is
    also where the reference-modification rule lives (rule R-2: no index
    arithmetic is written in a program module).

    IT WRITES THE SYSTEM RECORD. `if Date-Form = zero / move 1 to Date-Form`
    [general/gl072.cbl:L477-L478] defaults an unset format to UK, and `Date-Form`
    [copybooks/wssystem.cob:L128] is a `SYSTEM-REC` column - so the write is
    DIFF-VISIBLE and must land back in the record. The shared implementation
    returns the effective value for exactly that reason and its own contract says
    a caller "MUST store this return value back into `System-Record.Date-Form`
    for the migration to stay faithful"; the store below is that.

    NO CLOCK IS READ (rule R-6). The date arrives as the `to-day` linkage
    parameter - this is one of only two statements in `gl072` that read it, the
    other being [general/gl072.cbl:L391] - so two runs under the same pinned date
    produce the same result.

    `gl072` HAS NO OTHER DATE SECTION. There is no `zz050-Validate-Date`, no
    `zz060-Convert-Date` and no wrapper section around the shared date program -
    the wrapper that `gl070` names after its date-interface copybook while naming
    that section's exit after the called program, which is anomaly A-22. A-22
    THEREFORE DOES NOT OCCUR IN THIS MODULE, and no date-validation or
    day-number conversion is reachable from here at all.

    Args:
        st: The program's storage. `date_formats.ws_date` and
            `system_record`'s `Date-Form` are written; `to_day` is read.
    """
    # 475  move     to-day to ws-date.        ... through ...
    # 492  move     to-day (1:2) to ws-Intl-Days.
    #
    # The whole section body, delegated. `Date-UK` and `Date-USA`
    # [copybooks/wssystem.cob:L129-L130] are evaluated inside the shared
    # implementation, and so are the module's two remaining transfer sites:
    #
    #   479      if       Date-UK
    #   480               go to zz070-Exit.     # GO TO class 3 - section exit.
    #   481      if       Date-USA
    #   485               go to zz070-Exit.     # GO TO class 3 - section exit.
    #
    # Both target `zz070-Exit.` [general/gl072.cbl:L494], the section's trailing
    # exit label, so both are class-3 `return`s under the Agent Action Plan's
    # taxonomy. They are annotated here rather than implemented here because the
    # section is byte-identical across its ten carriers and therefore lives once
    # in `acas_posting.dates`; the classification is recorded at this call site so
    # this module's `GO TO` census is complete at seven (rule R-5).
    effective_date_form = zz070_convert_date(
        st.date_formats,
        st.to_day,
        st.system_record.system_data_block.date_form,
    )

    # 478  move 1 to Date-Form.
    # The defaulted value stored back into the system record, which is where the
    # COBOL puts it. Unconditional here because the shared implementation has
    # already applied L477's test and returns the value the field should hold -
    # storing an unchanged value back is not observable, whereas failing to store
    # a defaulted one would lose a column write.
    st.system_record.system_data_block.date_form = move.move(
        effective_date_form, _DATE_FORM
    )

    # 494  zz070-Exit.  ->  495  exit section.
    # Fall-through into the section's exit paragraph, called explicitly.
    _zz070_exit()


#  zz070-Exit.  [general/gl072.cbl:L494]


def _zz070_exit() -> None:
    """`zz070-Exit.` - `exit section.`, the real one.

    [general/gl072.cbl:L494-L495]

        494  zz070-Exit.
        495      exit     section.

    A GENUINE `exit section.`, unlike the plain `EXIT` at
    [general/gl072.cbl:L464]: it transfers control to the end of the section it
    is written in, which for a performed section is the `PERFORM`'s return point.
    It is also the target of the module's two remaining class-3 `GO TO`s,
    [general/gl072.cbl:L480] and [general/gl072.cbl:L485], both of which are
    evaluated inside the shared implementation in `acas_posting.dates` and are
    annotated there.

    The function is present because rule R-5 requires a named function for every
    paragraph, and because the contrast with the plain `EXIT` thirty lines
    earlier is worth being able to point at.
    """
    # 495  exit     section.
    # Return to the caller of the section - `headings.`
    # [general/gl072.cbl:L351] or `new-account.` [general/gl072.cbl:L418].
    return


#  procedure division using ...  [general/gl072.cbl:L262-L265]


def run(
    ws_calling_data: WsCallingData,
    system_record: SystemRecord,
    to_day: str,
    file_defs: FileDefs,
    *,
    work_files: GeneralLedgerWorkFiles | None = None,
    dal_common: AcasDalCommonData | None = None,
) -> None:
    """Run `gl072` - post the sorted transaction stream to the nominal ledger.

    The program's single entry point. Phase 4 of the General Ledger posting
    cycle: walk `post-trans` in the order `gl071` left it, accumulate each
    posting into its nominal account's balance, rewrite the account at every
    account break, and stamp each batch cleared with the run date.

    THE LINKAGE, VERBATIM  [general/gl072.cbl:L262-L265]

        procedure division using ws-calling-data
                                 system-record
                                 to-day
                                 file-defs.

    The four positional parameters below are that list, in that order, under
    those names - the four-parameter General Ledger call shape, shared
    character-for-character by `gl051` [general/gl051.cbl:L353-L356], `gl070`
    [general/gl070.cbl:L245-L248], `gl071` [general/gl071.cbl:L161-L164], this
    program and `gl080` [general/gl080.cbl:L269-L272], because all five are
    dispatched through the SAME menu paragraph `load00.`
    [general/general.cbl:L711-L722] with one `CALL` parameter list
    [general/general.cbl:L715-L718]. It is NOT the five-parameter Sales and
    Purchase shape and NOT the three-parameter IRS shape.

    `to-day` is `01 to-day pic x(10).` [general/gl072.cbl:L260], a DD/MM/CCYY
    text date and a LINKAGE PARAMETER rather than a column - which is what makes
    the whole program clock-free. It is read at exactly two sites,
    [general/gl072.cbl:L391] and [general/gl072.cbl:L475].

    THE PROCEDURE DIVISION'S TOP-LEVEL FLOW, WHICH IS FOUR CALLS
    `gl072-Main section.` [general/gl072.cbl:L268] falls through into `loop.`
    [general/gl072.cbl:L283]; `loop.` ALWAYS transfers - three times to itself and
    once to `end-run.` [general/gl072.cbl:L437] - so it never falls through into
    `headings.` [general/gl072.cbl:L343]; `end-run.` falls through into
    `main-exit.` [general/gl072.cbl:L445]; and `main-exit.` ends the program. The
    other nine paragraphs are reached only by `PERFORM`. So the body below is
    `_gl072_main`, `_loop`, `_end_run`, `_gl072_main_main_exit`, called in that
    order, and the two fall-throughs are explicit calls rather than implied
    adjacency.

    WHAT THIS PROGRAM WRITES, IN FULL
    `GLLEDGER-REC` - one `UPDATE` per account break and one more per page break
    (AMBIGUITY Q-20) - and `GLBATCH-REC` - one `UPDATE` per batch. Nothing else.
    Plus one field of the SYSTEM record: `Date-Form`, defaulted to UK when it
    arrives as zero [general/gl072.cbl:L477-L478].

    IT MAY LEGITIMATELY DO NOTHING. On an empty `post-trans` - which is what an
    empty batch, or a run aborted by `gl070`'s `ws-term-code = 5`
    [general/gl070.cbl:L289], leaves behind - the first read reports at end,
    `_end_account` and `_end_batch` rewrite default record areas, and the run
    closes. That is correct, not a failure.

    Args:
        ws_calling_data: `01 WS-Calling-Data` [copybooks/wscall.cob:L6-L14].
            ACCEPTED AND UNREAD, and not written back either: `gl072` contains no
            `move` to any field of it, so `WS-Term-Code` keeps the zero
            `load00.` set before the `CALL` [general/general.cbl:L714]. Unlike
            `gl070`, this program cannot abort the cycle. Kept in the signature
            because the caller's contract is the four-parameter shape.
        system_record: `SYSTEM-REC`, the 169-column system record. READ for
            `Run-Date` [copybooks/wssystem.cob:L67], `Page-Lines`
            [copybooks/wssystem.cob:L65], `Date-Form`
            [copybooks/wssystem.cob:L128] and `Scycle`
            [copybooks/wssystem.cob:L63]; WRITTEN at `Date-Form`. Passed on to
            both handlers as the first argument of every `CALL`
            [copybooks/Proc-ACAS-FH-Calls.cob:L51-L57].
        to_day: `to-day pic x(10)` in DD/MM/CCYY form. The controlled clock's
            text observable; no clock is read here or downstream of here.
        file_defs: `01 File-Defs.` [copybooks/wsnames.cob:L13], the file-name
            buffers. Supplies `post-trans-name` [copybooks/wsnames.cob:L16] to
            the FILE-CONTROL entry [general/gl072.cbl:L95], and is the fourth
            argument of every handler `CALL`.
        work_files: The General Ledger cycle's work-file sequences. NOT A LINKAGE
            PARAMETER - keyword-only, and it stands in for what the compiled
            program uses instead: its own FILE SECTION over files that persist on
            the filesystem between phases. `gl071` must have written `post_trans`
            into the same container [general/gl071.cbl:L178] for this program to
            have anything to post, so the General Ledger cycle passes ONE
            container through all three phases. Omitting it declares a fresh,
            empty set, and posting nothing then posts nothing - the empty-batch
            outcome. It is not a module-level default, because one run's records
            leaking into the next would break rule R-6's byte-identical-reruns
            guarantee silently.
        dal_common: `ACAS-DAL-Common-Data` [copybooks/Test-Data-Flags.cob], the
            fifth argument of every handler `CALL`. KEYWORD-ONLY AND NOT A
            LINKAGE PARAMETER: in COBOL it is WORKING-STORAGE whose values come
            from the copybook's own `VALUE` clauses, and the maintainer's inline
            comment on the `copy` [general/gl072.cbl:L157] reads "set sw-testing
            to zero to stop logging." That switch is configuration, so it is
            exposed as configuration; omitting it takes the copybook's declared
            values unchanged, which is what the compiled program does.

    Raises:
        acas_posting.workfiles.WorkFileError: The work sequence was handed a
            record description it cannot carry, or was read in a mode that does
            not permit it. A PROGRAMMER error; no value in a record can cause it.
        acas_posting.dal.facade.FacadeError: A facade verb reached a boundary the
            migration states rather than crosses. Not raised by any of the eight
            verbs this program performs.
    """
    # NOT VALIDATION - two default resolutions Python signatures cannot express
    # (rule R-3). Neither tests a value that reaches an accounting decision:
    # a mutable default argument is evaluated once at definition time and would
    # then be SHARED between calls, which is exactly the cross-run leakage rule
    # R-6 forbids. `gl072`'s own conditionals are the nineteen listed in the
    # module docstring and none of them is here.
    files = general_ledger_work_files() if work_files is None else work_files
    common = AcasDalCommonData() if dal_common is None else dal_common

    #  working-storage section.  [general/gl072.cbl:L124-L245]
    #  Constructed HERE, not passed in, because in COBOL these are copied into
    #  this program's own working storage - `wsfnctn.cob` at
    #  [general/gl072.cbl:L129], `wsledger.cob` at [general/gl072.cbl:L130],
    #  `wsbatch.cob` at [general/gl072.cbl:L131] - so each `CALL` of `gl072` gets
    #  a fresh set, initialised from their `VALUE` clauses.
    file_access = FileAccess()
    ledger = WsLedgerRecord()
    batch = GlBatchRecord()
    date_formats = WsDateFormats()

    #  TWO FACADE LINKAGES OVER ONE STATUS FIELD. Each dispatch paragraph names
    #  the entity record it passes - `acas005` passes `WS-Ledger-Record`
    #  [copybooks/Proc-ACAS-FH-Calls.cob:L35-L40] and `acas007` passes
    #  `WS-Batch-Record` [copybooks/Proc-ACAS-FH-Calls.cob:L51-L56] - while
    #  `System-Record`, `File-Access`, `File-Defs` and `ACAS-DAL-Common-Data` are
    #  THE SAME four items in both. So there are two contexts and they share
    #  everything except `record`, which is what makes `We-Error` a single
    #  program-wide status exactly as the COBOL has it: a batch read overwrites
    #  the reply a ledger read left, and the program depends on that.
    #
    #  No `options` mapping is passed. Neither handler's dispatch takes a
    #  keyword-only extra, and inventing one would put a parameter in the call
    #  path that no COBOL statement corresponds to.
    ledger_ctx = facade.FacadeContext(
        system=system_record,
        record=ledger,
        file_access=file_access,
        file_defs=file_defs,
        dal_common=common,
    )
    batch_ctx = facade.FacadeContext(
        system=system_record,
        record=batch,
        file_access=file_access,
        file_defs=file_defs,
        dal_common=common,
    )

    st = _ProgramStorage(
        ws_calling_data=ws_calling_data,
        system_record=system_record,
        to_day=to_day,
        file_defs=file_defs,
        file_access=file_access,
        ledger=ledger,
        batch=batch,
        dal_common=common,
        date_formats=date_formats,
        work_files=files,
        ledger_ctx=ledger_ctx,
        batch_ctx=batch_ctx,
    )

    # 268  gl072-Main section.   ->  the opens and the break-detector reset
    _gl072_main(st)

    # 283  loop.                 ->  reached by FALL-THROUGH from L281
    _loop(st)

    # 437  end-run.              ->  reached by `go to end-run` L289, class 2.
    #      The class-2 split: the `break` is inside `_loop`, this block is after
    #      it. Agent Action Plan section 0.6.3 - "not `break` alone".
    _end_run(st)

    # 445  main-exit.  ->  446  goback.   reached by FALL-THROUGH from L443
    _gl072_main_main_exit()


# --- traceability ---------------------------------------------------------
#
# Rule R-5. Every construct of general/gl072.cbl mapped to what reproduces it
# here, and every deliberate omission recorded AS an omission - Agent Action Plan
# section 0.4.3, verbatim, on why: "so that a reader comparing the two files does
# not conclude something was lost."
#
# PROGRAM  ->  MODULE
#   general/gl072.cbl  ->  acas_posting/programs/gl072_transaction_update.py
#   program-id gl072 [general/gl072.cbl:L12]; version banner "gl072 (3.3.00)"
#   [general/gl072.cbl:L127]; boundary THE WHOLE PROGRAM, 498 lines.
#
# SECTION / PARAGRAPH  ->  FUNCTION   (thirteen labels, in source order)
#   gl072-Main section.          [general/gl072.cbl:L268]  ->  _gl072_main
#   loop.                        [general/gl072.cbl:L283]  ->  _loop
#   headings.                    [general/gl072.cbl:L343]  ->  _headings
#   headings-end.                [general/gl072.cbl:L369]  ->  _headings_end
#   end-batch.                   [general/gl072.cbl:L372]  ->  _end_batch
#   end-account.                 [general/gl072.cbl:L379]  ->  _end_account
#   new-account.                 [general/gl072.cbl:L402]  ->  _new_account
#   end-run.                     [general/gl072.cbl:L437]  ->  _end_run
#   main-exit.                   [general/gl072.cbl:L445]  ->
#                                              _gl072_main_main_exit
#   get-batch section.           [general/gl072.cbl:L448]  ->  _get_batch
#   main-exit.                   [general/gl072.cbl:L464]  ->
#                                              _get_batch_main_exit
#   zz070-Convert-Date section.  [general/gl072.cbl:L467]  ->
#                                              _zz070_convert_date
#   zz070-Exit.                  [general/gl072.cbl:L494]  ->  _zz070_exit
#   procedure division using ws-calling-data, system-record, to-day, file-defs
#                                [general/gl072.cbl:L262-L265]  ->  run
#
#   THREE SECTIONS, TEN PARAGRAPHS. The sections are `gl072-Main`
#   [general/gl072.cbl:L268], `get-batch` [general/gl072.cbl:L448] and
#   `zz070-Convert-Date` [general/gl072.cbl:L467]; the remaining ten labels are
#   paragraphs, eight of them inside `gl072-Main`.
#
#   `main-exit.` OCCURS TWICE and both Python functions are SECTION-QUALIFIED, so
#   the paragraph-to-function mapping stays one-to-one. They are not
#   interchangeable: [general/gl072.cbl:L445] is `goback.` and ends the program;
#   [general/gl072.cbl:L464] is a plain `exit.`, a no-operation.
#
#   `headings-end.` [general/gl072.cbl:L369] HAS AN EMPTY BODY in the source, so
#   `_headings_end` has an empty body here. Present because Agent Action Plan
#   section 0.7.4 C-4 requires it - "every paragraph retains a named function even
#   where its `GO TO` becomes a `continue`, a `break` or a `return`" - and it is
#   not a stub.
#
#   DECLARATION ORDER IS REVERSED AGAINST CALL ORDER. `end-batch.` is DECLARED at
#   [general/gl072.cbl:L372] and `end-account.` at [general/gl072.cbl:L379], but
#   both call sites perform `end-account` FIRST - the at-end clause
#   [general/gl072.cbl:L287-L288] and the batch break
#   [general/gl072.cbl:L297-L298]. The functions above are declared in SOURCE
#   order and called in CALL order, and the discrepancy is recorded here so a
#   reader diffing the two files is not confused by it. Agent Action Plan section
#   0.6.4: "Inverting them would produce a batch marked posted with an unclosed
#   final account."
#
#   ONE FUNCTION IS NOT A PARAGRAPH. `_post_ledger_group_image` is a RENDERING
#   HELPER, not a label: it materialises the eight-character group view of
#   `03 post-ledger.` [general/gl072.cbl:L115-L117] that COBOL gets for free and
#   Python does not, and it owns no semantics - every character comes from
#   `acas_posting.cobol.move` under the children's own descriptors. It is listed
#   here so the function count is not read as fourteen paragraphs.
#
# STATEMENT  ->  CALL SITE   (the four that reach a table, plus the system write)
#   add post-amount to ledger-balance   [general/gl072.cbl:L331]
#       ->  `arithmetic.add_to(..., receiving=_LEDGER_BALANCE, rounded=False)` in
#           `_loop`. THE POSTING. The only statement in the program that moves
#           money, and the only writer of a monetary column.
#   move 1 to cleared-status            [general/gl072.cbl:L375]
#       ->  `move.move(condition_names.values_for("Processed")[0], ...)` in
#           `_end_batch`.
#   move run-date to posted             [general/gl072.cbl:L376]
#       ->  `move.move(system_record ... run_date, _POSTED, ...)` in
#           `_end_batch`. A controlled-clock observable.
#   perform GL-Batch-Rewrite            [general/gl072.cbl:L377]
#       ->  `facade.gl_batch_rewrite(st.batch_ctx)` in `_end_batch`.
#           `GLBATCH-REC` UPDATE.
#   perform GL-Nominal-Rewrite          [general/gl072.cbl:L382]
#       ->  `facade.gl_nominal_rewrite(st.ledger_ctx)` in `_end_account`.
#           `GLLEDGER-REC` UPDATE - the first statement of the paragraph.
#   move 1 to Date-Form                 [general/gl072.cbl:L478]
#       ->  the store-back in `_zz070_convert_date`. A `SYSTEM-REC` column, so
#           diff-visible; the only field of the system record this program writes.
#
# FACADE VERBS PERFORMED - EXACTLY EIGHT, AND ALL EIGHT ARE HERE
#   GL-Batch-Open        [general/gl072.cbl:L276]  ->  facade.gl_batch_open
#       [copybooks/Proc-ACAS-FH-Calls.cob:L419-L422] - the I-O open, NOT
#       `-Open-Input`, per the maintainer's inline comment on L276.
#   GL-Nominal-Open      [general/gl072.cbl:L277]  ->  facade.gl_nominal_open
#       [copybooks/Proc-ACAS-FH-Calls.cob:L299-L302] - likewise I-O.
#   GL-Batch-Rewrite     [general/gl072.cbl:L377]  ->  facade.gl_batch_rewrite
#       [copybooks/Proc-ACAS-FH-Calls.cob:L475-L478]
#   GL-Nominal-Rewrite   [general/gl072.cbl:L382]  ->  facade.gl_nominal_rewrite
#       [copybooks/Proc-ACAS-FH-Calls.cob:L349-L352]
#   GL-Nominal-Read-Next [general/gl072.cbl:L408]  ->
#       facade.gl_nominal_read_next
#       [copybooks/Proc-ACAS-FH-Calls.cob:L334-L337] - ANOMALY A-14.
#   GL-Batch-Read-Next   [general/gl072.cbl:L454]  ->  facade.gl_batch_read_next
#       [copybooks/Proc-ACAS-FH-Calls.cob:L460-L463] - AMBIGUITY Q-22.
#   GL-Batch-Close       [general/gl072.cbl:L441]  ->  facade.gl_batch_close
#       [copybooks/Proc-ACAS-FH-Calls.cob:L439-L442]
#   GL-Nominal-Close     [general/gl072.cbl:L442]  ->  facade.gl_nominal_close
#       [copybooks/Proc-ACAS-FH-Calls.cob:L319-L322]
#
#   NO `Write`, NO `Delete`, NO `Delete-All`, NO `Start` and NO `Read-Indexed`
#   verb is performed anywhere in `gl072`, and no verb of any entity other than
#   GL-Nominal and GL-Batch. It INSERTS nothing and DELETES nothing: its whole
#   effect on the database is five statements' worth of `UPDATE` plus the
#   `Date-Form` default. In particular no verb of the posting entity is
#   performed - `gl072` does not copy `wspost.cob` and reads the `post-trans`
#   work sequence instead - so no posting-record module is imported.
#
#   NO REPLY IS TESTED AFTER ANY OF THE EIGHT. `Proc-ACAS-FH-Calls.cob`
#   [general/gl072.cbl:L497] publishes no error-check paragraph, unlike the
#   handler-named IRS convention [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob], whose
#   per-handler check returns from the program outright on an unrecoverable open
#   failure [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L355-L364]. This program
#   tests only `We-Error`, and only the `999` the sentinel puts there - never a
#   file status. No check is invented (rule R-3).
#
# `GO TO`  -  SEVEN SITES, MEASURED, EACH CLASSIFIED BY SHAPE
#   [general/gl072.cbl:L289]  ->  end-run.       CLASS 2  forward terminator
#       `break` in `_loop` PLUS `_end_run` called after the loop, from `run`. The
#       at-end clause still performs `end-account` then `end-batch` BEFORE the
#       break, inside the clause, exactly as L287-L288 do.
#   [general/gl072.cbl:L292]  ->  loop.          CLASS 1  loop-back
#       `continue`. ANOMALY A-13 site (a).
#   [general/gl072.cbl:L307]  ->  loop.          CLASS 1  loop-back
#       `continue`. ANOMALY A-13 site (b).
#   [general/gl072.cbl:L341]  ->  loop.          CLASS 1  loop-back
#       `continue`, written explicitly at the end of the loop body.
#   [general/gl072.cbl:L349]  ->  headings-end.  CLASS 3  paragraph exit
#       `return` from `_headings`. Classified by SHAPE: the target is an empty
#       paragraph immediately following, serving as a `PERFORM ... THRU` range
#       terminator. The reservation on that reading is AMBIGUITY Q-21.
#   [general/gl072.cbl:L480]  ->  zz070-Exit.    CLASS 3  section exit
#   [general/gl072.cbl:L485]  ->  zz070-Exit.    CLASS 3  section exit
#       Both are inside the consolidated `zz070` body and are annotated in
#       `acas_posting.dates`, which owns that section for all ten carriers.
#
#   NO CLASS 4 SITE. `gl072` has no sibling re-dispatch: every one of its seven
#   targets is a loop head, a forward terminator or an exit label, so the class
#   that needs per-site proof of equivalence does not arise here.
#
# `PERFORM ... THRU`  -  TWO SITES, HAND-VERIFIED INDIVIDUALLY
#   [general/gl072.cbl:L300]  perform headings through headings-end
#       ->  `_headings(st)` then `_headings_end()` in `_loop`, on the batch break.
#           Verified: the range spans `headings.` [general/gl072.cbl:L343] to
#           `headings-end.` [general/gl072.cbl:L369], and the terminator's body is
#           empty, so the range's only member with statements is `headings.`
#   [general/gl072.cbl:L304]  perform headings through headings-end
#       ->  `_headings(st)` then `_headings_end()` in `_loop`, on the first
#           record of a batch. Verified SEPARATELY rather than assumed to match
#           L300, per Agent Action Plan section 0.4.2 - "with no pattern-matching
#           shortcut".
#   AND ONE BARE FORM, WHICH IS NOT A RANGE
#   [general/gl072.cbl:L337]  perform headings
#       ->  `_headings(st)` alone in `_loop`, on the page-overflow path. Recorded
#           as DISTINCT from the two above. Equivalent on the fall-through path
#           because the terminator is empty; AMBIGUITY Q-21 records why that
#           equivalence is not proven for the `go to headings-end` path and what
#           was implemented instead.
#   These two range sites are two of only FOUR inside the whole in-scope
#   migration surface; see CITATION CORRECTIONS.
#
# ANOMALY REGISTER  (rule R-4 - reproduced, never fixed)
#   A-13  TWO ENTIRELY SILENT SKIPS.
#         site (a) [general/gl072.cbl:L291-L292] - a non-numeric batch number.
#         site (b) [general/gl072.cbl:L306-L307] - a `we-error = 999` record.
#         Reproduced in `_loop` with a locator-citing comment at each site. NO
#         runtime trace of any kind: no message, no counter, no metric, no log
#         record. This module contains no warning-level or error-level logging
#         at all, and its single log record is the phase banner in `_gl072_main`.
#         Note that site (a) is provably unreachable in Python, because
#         `post_batch` is carried as `int`; it is reproduced regardless, and
#         `_loop` says why.
#   A-14  THE SEQUENTIAL NOMINAL READ. [general/gl072.cbl:L405-L408] - the key
#         move at L405, the guard at L407, the `Read-Next` at L408. Reproduced in
#         `_new_account`, key move INCLUDED, with the full comment Agent Action
#         Plan section 0.8.4's prohibition requires. The correctness of the whole
#         phase rests on `gl071`'s sort [general/gl071.cbl:L173-L176].
#   A-21  FIELD-NAME COLLISIONS FORCING QUALIFIED REFERENCES. Present in this
#         program at `move description of WS-Batch-Record to l3-desc`
#         [general/gl072.cbl:L456]. The statement is omitted with the print file,
#         so the collision is recorded rather than reproduced - see `_get_batch`.
#   A-22  DOES NOT OCCUR HERE. The mis-named wrapper section and exit label are
#         `gl070`'s [general/gl070.cbl:L603-L609]. `gl072` declares no
#         `zz050-Validate-Date`, no `zz060-Convert-Date` and no wrapper section
#         around the shared date program at all; its only date section is
#         `zz070-Convert-Date` [general/gl072.cbl:L467] whose exit is correctly
#         named `zz070-Exit.` [general/gl072.cbl:L494]. Stated affirmatively
#         because the absence is a fact about the frozen source.
#   CANDIDATES THE REGISTER DOES NOT CARRY, offered to the anomaly-log author:
#         AMBIGUITY Q-19, the two disagreeing `tot-cr` accumulation forms
#         [general/gl072.cbl:L327] against [general/gl072.cbl:L427], resolved by
#         the receivers being declared UNSIGNED [general/gl072.cbl:L165-L166] -
#         no database effect; and AMBIGUITY Q-22, `get-batch`'s key-then-sequential
#         batch read [general/gl072.cbl:L451-L454], which HAS a database effect
#         because `end-batch` stamps whatever row it leaves behind.
#
# OMISSIONS - deliberate, and each one recorded rather than silent
#   1. THE UNUSED FACADE STUB BLOCK.
#      `01 Dummies-4-Unused-ACAS-FH-Calls.` [general/gl072.cbl:L135] through
#      `03 WS-OTM5-Record pic x.` [general/gl072.cbl:L155] - nineteen one-byte
#      dummies declared so the linker resolves the facade copybook's full verb
#      set. MAPS TO NOTHING, and NO Python stand-in for it exists anywhere in this
#      module. Agent Action Plan section 0.4.3, verbatim: "Python has no
#      equivalent need, so the block maps to nothing - recorded in the
#      traceability document as a representation-only omission so that a reader
#      comparing the two files does not conclude something was lost."
#      THE DETAIL THAT REVEALS ITS PURPOSE: the maintainer's own instruction sits
#      above it - `*> REMARK OUT ANY IN USE` [general/gl072.cbl:L133] - and
#      EXACTLY THREE entries are commented out, because `gl072` really does use
#      those three records: `Default-Record` [general/gl072.cbl:L136],
#      `WS-Ledger-Record` [general/gl072.cbl:L139] and `WS-Batch-Record`
#      [general/gl072.cbl:L141]. So the block is a linker artefact that doubles as
#      a statement of which entities the program touches, and the two it names
#      live are precisely the two tables it updates.
#      Note in particular that `03 WS-Posting-Record pic x.`
#      [general/gl072.cbl:L140] is one of the NINETEEN - a one-byte dummy, not a
#      record layout - which is why no posting-record module is imported.
#   2. THE REPORT SPOOL-OUT PATH.
#      `call "SYSTEM" using Print-Report.` [general/gl072.cbl:L443], together with
#      `copy "print-spool-command.cob".` [general/gl072.cbl:L128] and
#      `move Print-Spool-Name to PSN.` [general/gl072.cbl:L271] which prepare it.
#      Excluded by Agent Action Plan section 0.2.2 "wherever it appears" and
#      independently forbidden by rule R-1. NO database effect. Nothing in this
#      module starts a process or loads a foreign library.
#   3. THE ENTIRE PRINT FILE.
#      `copy "selprint.cob".` [general/gl072.cbl:L101]; `copy "fdprint.cob"
#      replacing ==x(132)== by ==x(120)==.` [general/gl072.cbl:L123] - the
#      replacement narrows the print record from 132 to 120 characters, which is
#      why every print line in this program is declared 120 wide;
#      `open output print-file` [general/gl072.cbl:L279]; `close ... print-file`
#      as the second operand of [general/gl072.cbl:L440]; and every
#      `write print-record` - [general/gl072.cbl:L333], [general/gl072.cbl:L358],
#      [general/gl072.cbl:L359], [general/gl072.cbl:L361],
#      [general/gl072.cbl:L363], [general/gl072.cbl:L364],
#      [general/gl072.cbl:L365], [general/gl072.cbl:L366],
#      [general/gl072.cbl:L384], [general/gl072.cbl:L395],
#      [general/gl072.cbl:L396], [general/gl072.cbl:L399],
#      [general/gl072.cbl:L433] - thirteen sites.
#      Also the seven print-line record areas themselves: `line-1`
#      [general/gl072.cbl:L206], `line-3` [general/gl072.cbl:L212], `line-4`
#      [general/gl072.cbl:L223], `line-5` [general/gl072.cbl:L228], `line-6`
#      [general/gl072.cbl:L232], `line-7` [general/gl072.cbl:L247]. Every `move`
#      into an `l1-*`, `l3-*`, `l6-*` or `l7-*` field is presentation and is
#      omitted at its site, EXCEPT `l6-account` [general/gl072.cbl:L233], which is
#      modelled because two arithmetic statements name it as their receiver.
#   4. THE `if y not = 1` PRINT-FORM SELECTION.
#      [general/gl072.cbl:L357-L364]. BOTH BRANCHES CONSIST SOLELY OF
#      `write print-record` STATEMENTS - the first page is written `before 1`, a
#      later page `after page` - so once the print file is omitted the conditional
#      has no body on either side. Recorded here rather than reproduced as an `if`
#      with two empty branches, which would be dead code dressed as fidelity.
#      `y` [general/gl072.cbl:L164] is KEPT and still accumulated, because
#      `add 1 to y` [general/gl072.cbl:L353] is an arithmetic-census statement; it
#      becomes a write-only counter, and that is stated rather than hidden.
#   5. `move prog-name to l1-prog.` [general/gl072.cbl:L275] and
#      `77 prog-name pic x(15) value "gl072 (3.3.00)".`
#      [general/gl072.cbl:L127] - the version banner. Presentation only.
#   6. `display "Phase - 4.  Transaction Update" at 0801 with
#      foreground-color 2.` [general/gl072.cbl:L274] - reproduced as ONE INFO log
#      record rather than omitted, per Agent Action Plan section 0.3.4. It alters
#      no control flow and appears in no table dump. The screen position and the
#      colour are dropped.
#   7. `copy "envdiv.cob".` [general/gl072.cbl:L88] and `copy "screenio.cpy".`
#      [general/gl072.cbl:L177] - environment-division and screen-section
#      boilerplate, representation only, no Python counterpart. `01
#      All-My-Constants pic 9(4).` [general/gl072.cbl:L176], the group the screen
#      copybook is nested under, goes with them.
#   8. THE SEVEN PAGE-GEOMETRY FIELDS `ws-env-lines`, `ws-lines`, `ws-23-lines`,
#      `ws-22-lines`, `ws-21-lines`, `ws-20-lines` and `Body-lines`
#      [general/gl072.cbl:L168-L174] - declared and NEVER REFERENCED anywhere in
#      the procedure division. Unlike `line-cnt` immediately above them they are
#      all `binary-char unsigned`; `gl072` uses `Page-Lines`
#      [copybooks/wssystem.cob:L65] directly instead. Omitted as dead
#      declarations, and recorded so their absence is not read as a lost page
#      calculation.
#   9. `01 ws-Test-Date pic x(10).` [general/gl072.cbl:L179] - declared and never
#      referenced; `gl072` has no date-validation section to use it.
#  10. KEPT DESPITE BEING PRESENTATION, and listed here so the choice is visible:
#      `line-cnt` [general/gl072.cbl:L163] and `Page-Lines`, because `line-cnt`
#      gates [general/gl072.cbl:L335] which issues an extra `UPDATE`; `tot-dr`
#      and `tot-cr` [general/gl072.cbl:L165-L166], because four arithmetic-census
#      statements name them, though their only consumers are
#      [general/gl072.cbl:L389-L390]; `l6-account` [general/gl072.cbl:L233], for
#      the two divides; and `y` [general/gl072.cbl:L164], for `add 1 to y`.
#  11. `Fs-Reply` IS WRITTEN BUT NEVER READ, AND THE WRITES ARE KEPT.
#      `select post-trans ... status fs-reply` [general/gl072.cbl:L95-L98] makes
#      the work sequence's file status the same `Fs-Reply`
#      [copybooks/wsfnctn.cob:L25] the facade verbs report through, so each
#      `open`, `read` and `close` of the sequence overwrites the last facade
#      reply. Reproduced at all three sites because they are stores the source
#      performs; recorded because `gl072` inspects only `We-Error`, so nothing
#      observable depends on them.
#  12. STATED AFFIRMATIVELY, because each absence is a fact about the frozen
#      source rather than a decision taken here. There is NO `accept` statement
#      anywhere in `gl072` - so no interactive prompt is dropped and none becomes
#      a command-line parameter, and Agent Action Plan section 0.3.4's second and
#      third cases do not arise. There is NO `ROUNDED`, NO `ON SIZE ERROR` and NO
#      `REMAINDER`. There is NO `zz050`, NO `zz060` and NO date-module wrapper
#      section, so anomaly A-22 does not occur. There is NO `SORT`, NO `SEARCH`,
#      NO `STRING`/`UNSTRING`, NO `CALL` other than the omitted spool-out, and NO
#      class-4 `GO TO`. And there is NO clock read of any kind.
#
# CITATION CORRECTIONS - the frozen file is the authority
#   Every locator in this module was re-read from `general/gl072.cbl` rather than
#   copied from the Agent Action Plan, and the plan's spans for this program
#   diverge in five places. Recorded so the wrong spans are not propagated.
#     * ANOMALY A-13's TWO SITES. The plan cites [general/gl072.cbl:L289-L290]
#       and [general/gl072.cbl:L303-L304]; the frozen statements are
#       L291-L292 and L306-L307. L289 is in fact the class-2
#       `go to end-run` and L303 is `move post-batch to save-batch`.
#     * ANOMALY A-14. The plan cites [general/gl072.cbl:L410-L412]; the frozen
#       key move is at L405, its guard at L407 and the `Read-Next` at L408.
#       L410-L411 is the SECOND guard and its `move zero to tot-dr tot-cr`, a
#       different statement entirely.
#     * THE BATCH STAMPING. The plan cites [general/gl072.cbl:L373-L377]; the
#       frozen statements are L375-L377, L373-L374 being the paragraph's underline
#       comment and a blank comment line.
#     * THE UNUSED STUB BLOCK. The plan cites [general/gl072.cbl:L134-L153]; the
#       frozen block is L135-L155, with the maintainer's `REMARK OUT ANY IN USE`
#       instruction at L133.
#     * THE PHASE-4 SCREEN LABEL. The plan cites [general/gl072.cbl:L277]; the
#       frozen `display` is at L274. L277 is `perform GL-Nominal-Open`.
#     * THE `end-account`/`end-batch` ORDERING. The plan cites
#       [general/gl072.cbl:L285-L296]; the frozen call sites are L287-L288 and
#       L297-L298, and the declarations are L372 and L379.
#     * THE `PERFORM ... THRU` CENSUS. The plan counts seven in-scope
#       occurrences. Measured, four fall inside the stated migration boundaries -
#       [general/gl072.cbl:L300] and [general/gl072.cbl:L304] here, plus
#       [sales/sl100.cbl:L344] and [purchase/pl100.cbl:L336]; the `irs030` and
#       `gl051` sites lie outside those programs' boundaries
#       ([irs/irs030.cbl:L1569-L1733] and [general/gl051.cbl:L1096-L1133]). This
#       program owns TWO of the four either way, which is what the count is
#       quoted for.
#   The plan's other citations for this program were checked and are exact:
#   [general/gl072.cbl:L386] and [general/gl072.cbl:L413] for the account-scaling
#   divides, and [general/gl072.cbl:L497] for the facade copybook.
#
# --- end traceability -----------------------------------------------------
