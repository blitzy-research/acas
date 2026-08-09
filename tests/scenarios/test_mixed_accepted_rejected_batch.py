"""THE MIXED ACCEPTED-AND-REJECTED BATCH -- state parity, and the file that LOCKS A-13.

Scenario `mixed_accepted_rejected`; subsystem `general`; operation `gl_post_cycle`; the
declared term code is zero. ONE closed, proofed General Ledger batch posts exactly as it
does on the reference happy path while OTHER transactions IN THE SAME RUN are abandoned
without a trace. The ten protocol stages are driven for it and an EMPTY
ordering-normalised diff is asserted -- Agent Action Plan section 0.8.5, criterion 1.

An empty diff proves three things here at once, and no single-transaction test can prove
any of them: that what posted, posted identically; that what was dropped was dropped
identically, which means it left NOTHING on either side; and that dropping it did not
shift the sequential nominal cursor, because if it had, the survivors' balances would
have landed in the wrong accounts.

RULES PROVENANCE, STATED PLAINLY
The six binding rules R-1 to R-6 live in the requirements themselves (Agent Action Plan
section 0.7.2) and their exact wording is retrievable there. Where they are silent,
enterprise-standard best practice applies.

THE INVERTED PREMISE, AND WHAT IT FORBIDS THIS FILE FROM ASSERTING
Agent Action Plan section 0.8.2, verbatim: "There is no test suite: compiled COBOL
execution is the behavioral specification, defects included. A defect reproduced is
correct; a defect fixed is a failure." So a test that asserted CORRECT ACCOUNTING rather
than OBSERVED BEHAVIOUR would itself be the defect. Every assertion below therefore
compares THE TWO SIDES TO EACH OTHER and never to a value a reader would expect. Where a
value is genuinely unsettled, that is recorded as an oracle question (R-6) rather than
guessed at.

The obligation bites this file a second, sharper way. Agent Action Plan section 0.6.5 on
the two skips, verbatim: "Both are silent - no message, no counter, no trace. The Python
equivalent must be equally silent; adding a warning would be an added behavior." So NO
test here asserts that a warning was emitted, that a rejection counter moved, or that a
summary line was written. Such an assertion would be demanding an added behaviour, which
R-3 forbids as surely as an added validation, and R-4 makes a failure.

WHY THE EMPTY-DIFF ASSERTION IS TRUSTWORTHY
Agent Action Plan section 0.6.6: "a non-empty diff is always a real behavioral
difference and never an artefact of the comparison." The schema earns that: every
in-scope table has a SINGLE-COLUMN primary key and ZERO secondary indexes, and none
carries a `TIMESTAMP`, an `AUTO_INCREMENT` column or a column-level `DEFAULT`. The three
tables this scenario bounds are `GLBATCH-REC` [mysql/ACASDB.sql:L80], `GLLEDGER-REC`
[mysql/ACASDB.sql:L122] and `GLPOSTING-REC` [mysql/ACASDB.sql:L154], whose keys are
`BATCH-KEY` [mysql/ACASDB.sql:L102], `LEDGER-KEY` [mysql/ACASDB.sql:L134] and `POST-RRN`
[mysql/ACASDB.sql:L169]. So `SELECT * FROM <table> ORDER BY <primary key>` is a total,
stable order with no tie-break, no timestamp masking and no surrogate-key remapping.

THE COBOL ROUTE
[general/general.cbl:L805-L815] is the whole dispatch, verbatim:

    L805  load08.
    L808       move     "gl070" to ws-called.
    L809       perform  load00.
    L810       if       ws-term-code = 5
    L811                go to display-menu.
    L812       move     "gl071" to ws-called.
    L813       perform  load00.
    L814       move     "gl072" to ws-called.
    L815       go       to load00.

gl070 runs, then the term-code gate, then gl071, then gl072. THE GATE MUST NOT FIRE IN
THIS SCENARIO -- see THE SEED USES A CLOSED BATCH below. Phase order is fixed and the
programs label themselves: "Phase - 1. Batch Check" [general/gl070.cbl:L284], "Phase -
2. Transaction Pre-process" [general/gl070.cbl:L292] and "Phase - 4. Transaction Update"
[general/gl072.cbl:L274]. gl071 shows only a wait message [general/gl071.cbl:L170] and
is unnumbered. Phase THREE is transaction deletion and lives in gl080, which executes
AFTER phase four and which this scenario does not drive; the numbering is preserved as
found and is not renumbered.

A-13 -- THE TWO ENTIRELY SILENT SKIPS. THE SUBJECT OF THIS FILE.
[general/gl072.cbl:L283-L307], verbatim:

    L283  loop.
    L286       read     post-trans  at end
    L287                perform  end-account
    L288                perform  end-batch
    L289                go to    end-run.
    L291       if       post-batch  not numeric       <- ** SILENT SKIP (a) **
    L292                go to  loop.
    L294       if       post-batch not = save-batch
    L295         and    save-batch not = zero
    L296         and    we-error   not = 999
    L297                perform  end-account
    L298                perform  end-batch
    L299                move  zero  to  save-ledger
    L300                perform  headings  through  headings-end.
    L302       if       save-batch  equal  zero
    L303                move  post-batch  to  save-batch
    L304                perform  headings  through  headings-end.
    L306       if       we-error  equal  999          <- ** SILENT SKIP (b) **
    L307                go to  loop.

SKIP (a): a posting whose batch number is not numeric is discarded at
[general/gl072.cbl:L291-L292]. SKIP (b): a record for which the handler returned
`we-error = 999` is discarded at [general/gl072.cbl:L306-L307]. Both are bare `go to
loop.` -- no message, no counter, no accumulator touched, no trace of any kind. Both `GO
TO`s are class 1, loop-back.

The Agent Action Plan's own locators for these two are OFF BY TWO: it cites
L289-L290 and L303-L304, which resolve to `go to end-run.` and `move post-batch to
save-batch` respectively. The verified sites are L291-L292 and L306-L307, and those are
the ones cited throughout this file. `docs/migration/anomaly-log.md` records the
correction under
A-13.

A THIRD SILENT PATH the Agent Action Plan omits entirely sits inside the headings
paragraph, [general/gl072.cbl:L346-L349]:

    L346       perform  get-batch.
    L348       if       we-error  equal  999
    L349                go to  headings-end.

Its disposition differs from the two loop sites -- it abandons the HEADINGS rather than
the RECORD -- so it is a third silent path and not a duplicate of skip (b). That `GO TO`
is class 3, a paragraph exit. It is named here because a reader chasing A-13 must find
all three.

HOW `we-error = 999` ACTUALLY GETS SET -- WHAT THE SEED ENGINEERS
`get-batch` is a SECTION at [general/gl072.cbl:L448], reached only by `perform
get-batch` from `headings` [general/gl072.cbl:L346] and lying beyond the mainline's own
`main-exit. goback.` at [general/gl072.cbl:L445-L446]. Verbatim:

    L448  get-batch               section.
    L451       move     1           to  WS-Ledger.
    L452       move     post-batch  to  save-batch  WS-Batch-Nos.
    L454       perform  GL-Batch-Read-Next.
    L456       move     description of WS-Batch-Record to  l3-desc.
    L458       if       not waiting
    L459                move  999  to  we-error       <- ** THE TRIGGER FOR SKIP (b) **
    L460                move  0    to  save-batch
    L461       else
    L462                move  0    to  we-error.
    L464  main-exit.   exit.

`88 Waiting value 0` is declared on `Cleared-Status` at [copybooks/wsbatch.cob:L29-L30],
with `88 Processed value 1` and `88 Archived value 2` beside it at
[copybooks/wsbatch.cob:L31-L32]. So A BATCH WHOSE `Cleared-Status` IS 1 OR 2 IS `not
waiting`, WHICH SETS `we-error = 999` AND MAKES EVERY POSTING FOR THAT BATCH VANISH
SILENTLY. One seeded field is the entire trigger.

THE A-13 / A-14 INTERACTION -- THE SUBTLEST PROPERTY THIS FILE PROVES
gl072 locates the nominal-ledger account for each posting with a SEQUENTIAL read,
[general/gl072.cbl:L405-L408]:

    L405       move     post-ledger  to  WS-Ledger-Key.
    L407       if       read-ledger not = "R"
    L408                perform  GL-Nominal-Read-Next.

It lands on the correct account ONLY because gl071 has already emitted the stream in
nominal-key order. A skipped posting is skipped AFTER the sort has placed it in that
stream, so it never reaches L408 and never advances the cursor. THEREFORE A SKIPPED
POSTING MUST NOT PERTURB THE ACCOUNT POSITIONS OF THE POSTINGS THAT FOLLOW IT -- and a
Python implementation that got this wrong would post into the WRONG ACCOUNT with no
error and no diagnostic, exactly as A-14 describes. That property is invisible in any
single-transaction test and is the reason this scenario exists.

Note that `if read-ledger not = "R"` appears AGAIN at [general/gl072.cbl:L410-L411],
AFTER the read, where it zeroes the running totals. It is a different test with a
different consequence and must not be mistaken for the read guard; the Agent Action
Plan's L410-L412 citation points at that post-read block rather than at the read.

NEVER "OPTIMISE" THE SEQUENTIAL READ INTO AN INDEXED ONE. Agent Action Plan section
0.8.4: "Any performance work is therefore out of scope by construction, not merely
unrequested." The indexed read would obviously be faster and would silently destroy the
property above.

THE gl071 SORT CONTRACT THE INTERACTION DEPENDS ON
[general/gl071.cbl:L172-L178], verbatim:

    L172       sort     sort-trans
    L173                on ascending key sort-batch
    L174                                 sort-ac
    L175                                 sort-pc
    L176                                 sort-post
    L177                using  pre-trans
    L178                giving post-trans.

The SD declaration order at [general/gl071.cbl:L137-L144] is `sort-batch, sort-post,
sort-code, sort-date, sort-ac, sort-pc, sort-amount, sort-legend` -- NOT the key order,
and confusing the two would reorder the stream. There is NO `with duplicates in order`
phrase, so the compiled tie order for two records carrying an identical `(sort-batch,
sort-ac, sort-pc, sort-post)` is whatever GnuCOBOL 3.2 chooses; the Python sort is
stable unconditionally. Under R-6 that was a question for the oracle, and the oracle
has ANSWERED it: `Q-SORT-TIE-ORDER` in `docs/migration/ambiguity-resolutions.md` is
`RESOLVED BY ORACLE` (2026-08-07) -- the compiled sort PRESERVES INPUT ORDER for equal
keys, which is exactly what an unconditionally stable sort produces, so no tie-driven
divergence is expected. The assertions below are unchanged and still assert only that
the two sides AGREE: a measured answer is a reason to expect agreement, never a
substitute for observing it. gl071 is a PURE SORT: zero facade verbs, zero arithmetic
statements.

THE ACCEPTED POSTINGS' ONLY MUTATIONS
The balance moves at [general/gl072.cbl:L331] `add post-amount to ledger-balance.`, is
persisted by `end-account`, and the batch is stamped by `end-batch`,
[general/gl072.cbl:L372-L382] verbatim:

    L372  end-batch.
    L375       move     1  to  cleared-status.
    L376       move     run-date  to  posted.
    L377       perform  GL-Batch-Rewrite.
    L379  end-account.
    L382       perform  GL-Nominal-Rewrite.

ACCOUNT-LEVEL TOTALS CLOSE BEFORE BATCH-LEVEL TOTALS -- `perform end-account` then
`perform end-batch`, at [general/gl072.cbl:L287-L288] on the at-end path and again at
[general/gl072.cbl:L297-L298] on the batch-change path. "Inverting them would produce a
batch marked posted with an unclosed final account."

THE THREE-LEG DOUBLE-ENTRY EXPLOSION THAT BUILT THE WORK FILE
[general/gl070.cbl:L495-L533]. The DR leg is written at L501-L508. The CR leg is written
at L510-L519 and carries the UNCONDITIONAL sign inversion `multiply pre-amount by -1
giving pre-amount.` at [general/gl070.cbl:L517]. The VAT leg is gated,
[general/gl070.cbl:L521-L523] verbatim:

    L521       if       vat-ac of WS-Posting-Record = zero
    L522             or vat-amount = zero
    L523                go to  loop.

so it is written at L525-L532 only when BOTH the VAT account and the VAT amount are
non-zero. The seed therefore carries at least one posting WITH VAT and at least one
WITHOUT, so both the three-leg and the two-leg shapes appear in the stream. A-21, the
field-name collisions across three posting copybooks that force qualified references, is
visible at [general/gl070.cbl:L497], [general/gl070.cbl:L521] and
[general/gl070.cbl:L525].

gl072 MUTATES EXACTLY TWO TABLES -- A MEASURED VERB CENSUS, NOT AN INFERENCE
gl072 issues exactly eight facade verbs: `GL-Batch-Open` [general/gl072.cbl:L276],
`GL-Nominal-Open` [general/gl072.cbl:L274], `GL-Batch-Rewrite` [general/gl072.cbl:L377],
`GL-Nominal-Rewrite` [general/gl072.cbl:L382], `GL-Nominal-Read-Next`
[general/gl072.cbl:L408], `GL-Batch-Close` [general/gl072.cbl:L441], `GL-Nominal-Close`
[general/gl072.cbl:L442] and `GL-Batch-Read-Next` [general/gl072.cbl:L454] -- and ZERO
`GL-Posting-*` VERBS OF ANY KIND. gl070 issues twelve and every one is read-only:
`GL-Batch-Open-Input` at L303,
L342
and L448; `GL-Batch-Read-Next` at L308, L347 and L453; `GL-Batch-Close` at L321, L440
and
L473; `GL-Posting-Open-Input` at L481; `GL-Posting-Read-Next` at L486;
`GL-Posting-Close` at L466. gl071 issues none.

So the only two mutating verbs on the whole route are the two Rewrites in gl072, and
`GLPOSTING-REC` IS AN UNCHANGED WITNESS. It is bounded into the comparison anyway, and
in this scenario that listing earns its place twice over: a skipped posting must leave
its source row exactly as seeded, and the dump is the only thing that can prove it.
gl072's own `WS-Posting-Record` is a ONE-BYTE DUMMY, `03 WS-Posting-Record pic x.` at
[general/gl072.cbl:L140] inside the stub block `01 Dummies-4-Unused-ACAS-FH-Calls.` at
[general/gl072.cbl:L135-L155], declared purely to satisfy the linker and mapping to
NOTHING AT ALL in Python (Agent Action Plan section 0.4.3).

WHAT IS EXCLUDED, AND WHY THAT IS BOUNDING RATHER THAN IGNORING
[general/gl072.cbl:L443] `call "SYSTEM" using Print-Report.` is the report spool-out,
excluded by Agent Action Plan section 0.2.2 as having no database effect; it must not
appear in any dump. The COBOL menu's exit path rewrites the system records on leaving,
[general/general.cbl:L656-L667]:

    L656  overrewrite.
    L657       if       File-System-Used NOT = zero
    L659                move     1 to File-Key-No       <- KEY 1, SYSTEM-REC
    L664                move     2 to File-Key-No       <- KEY 2, SYSDEFLT-REC
    L667                move     4 to File-Key-No       <- KEY 4, SYSTOT-REC

and BOTH SIDES REACH THAT PARAGRAPH: `acas_posting/cli/args.py`'s `overrewrite` is its
migrated counterpart and every one of the seven routes calls it, so KEY 1 IS WRITTEN ON
BOTH SIDES OF EVERY SCENARIO. Sales and Purchase persist keys 1 and 4 only, never key 2
[sales/sales.cbl:L636], [purchase/purchase.cbl:L629], and the reproduction inherits that
divergence by writing key 2 only when the route loaded the defaults record; the IRS route
persists key 1 alone. A census across all twelve in-scope PROGRAMS finds NO `System-*`
facade verb in any of them, so no migrated program persists these tables - only the
menu-exit path does, on both sides.

`SYSTEM-REC` AND `SYSDEFLT-REC` ARE ON THIS SCENARIO'S DECLARED EFFECT LIST, measured
byte-identical on the two sides rather than presumed to diverge. Two of `SYSTEM-REC`'s
169 columns are withheld from the capture and only two: `RDBMS-PASSWD char(12)`
[copybooks/wssystem.cob:L139] and the frozen schema's shorter `PASS-WORD` are replaced on
BOTH sides by `harness/dump_tables.py`'s `REDACTED_COLUMNS`, because a dump is `SELECT *`
and a capture is committed evidence. Every other column is compared byte for byte, so
that is redaction and not an ignore-list. THE COUPLING OBJECTION WAS MEASURED: the row's
content depends on what the route DID - the run-date stamp, the IRS allocator, the
latches, and `Date-Form`, which the frozen date sections write back
[copybooks/wssystem.cob:L127] - so counting it toward `expected_table_effect` could in
principle couple this scenario's effect claim to fields it does not reason about. Across
the committed scenarios the digest moves on exactly those declaring `changed` and holds
on those declaring `unchanged`, so it does not. The row is FINGERPRINTED besides, before
and after every run, and `protocol.assert_system_record_parity` compares the two sides'
post-run digests over all 169 columns - the credential included, with nothing to leak.

THE LIST IS NOT THE COMPARISON BOUND. The capture and the diff are bounded at ALL 22
IN-SCOPE TABLES (`--all-in-scope`), so a difference in any of these rows IS caught rather
than bounded away - which is the point, since a bound drawn from what a scenario expects
to move could report an empty diff while the run date, the allocators, the flags, the
defaults or the period totals differed. AND THERE IS STILL NO IGNORING: no ignore-list, no
tolerance-list and no "known difference" allowance exists anywhere in the diff path.

A-15 -- THE BATCH RECORD'S DECLARED LENGTH CONTRADICTION
[copybooks/wsbatch.cob:L7-L9] carries the maintainer's own three consecutive comments:

    L7  *> 96 bytes 26/03/09
    L8  *> 98 bytes 20/12/11 (no, dont understand as I count 96)
    L9  *>   but function length (Batch-record) says 98?

Whether the declared length or the field sum governs the record actually read affects
field alignment for the trailing fields, and only execution showed which. Execution has
now happened: `Q-4` in `docs/migration/ambiguity-resolutions.md` is `RESOLVED BY ORACLE`
(2026-08-07) and the answer is NEITHER -- both record copies measure 96, `FUNCTION
LENGTH` agrees with the field sum, and the 98 in the maintainer's note is false under
GnuCOBOL 3.2.0. `docs/migration/anomaly-log.md` correspondingly carries A-15 as
`REPRODUCED -- VALUE MEASURED`, not as pending. Measured is not fixed: the contradictory
note is still in the frozen copybook and nothing repairs it (R-4).

THE SEED USES A CLOSED BATCH -- NOT AN OPEN ONE. THE SINGLE EASIEST WAY TO GET THIS
SCENARIO WRONG.
AN OPEN BATCH WOULD COLLAPSE THIS SCENARIO INTO `control_total_mismatch`. gl070's
Phase-1 walk would fire, [general/gl070.cbl:L314-L315]:

    L314       if       status-open
    L315                move  1  to  a.

which raises the terminate code at [general/gl070.cbl:L287-L290]:

    L287       if       a = 1
    L288                perform gl060a
    L289                move 5 to ws-term-code
    L290                go to  main-exit.

which the menu tests at [general/general.cbl:L810-L811], returning to the menu -- so
gl071 AND gl072 WOULD NEVER RUN AT ALL and A-13 would never be reached. The difference
between this scenario and that one is A SINGLE SEEDED FIELD, `Batch-Status`, and getting
it wrong silently converts this file into a duplicate of
`tests/scenarios/test_control_total_mismatch_rejection.py`.

THE SEED THE SCENARIO ACTUALLY DECLARES, read out of `seed_records` rather than
described from intent, and asserted by `test_scenario_definition_preconditions` so that
this description cannot drift away from the fixture:

  `batch.dat`, TWO General Ledger batches, both with `Bcycle` equal to `system.cyclea`
    [copybooks/wsbatch.cob:L34]:
      BATCH 1, key 100001 -- `WS-Ledger = 1` so `88 GL-Batch`
        [copybooks/wsbatch.cob:L15-L16] is true; `Batch-Status = 1` so `88 Status-Closed`
        [copybooks/wsbatch.cob:L25-L27] is true; `Cleared-Status = 0` so `88 Waiting`
        [copybooks/wsbatch.cob:L29-L30] is true; `Items` 1; `Posted` 0. THIS IS THE
        BATCH THAT POSTS.
      BATCH 2, key 100002 -- General Ledger, closed, `Cleared-Status = 1` so `88
        Processed` [copybooks/wsbatch.cob:L31] is true and `88 Waiting` is false;
        `Items` 0. IT IS THE NOT-WAITING BATCH, and it has NO POSTINGS.
  `posting.dat`, ONE row -- batch 1, `Post-Amount` 1000.00 with `Vat-Amount` 200.00 on
    the CR side and `Vat-AC` 2200, which is the shape gl070's double-entry explosion
    would write all THREE legs from [general/gl070.cbl:L495-L533] with the VAT gate at
    [general/gl070.cbl:L521-L523] taken.
  `ledger.dat`, FIVE nominal accounts across four account numbers and two profit
    centres - 1000/0, 1000/1, 2000/0, 2200/0 and 3000/0.

WHAT THIS FIXTURE REACHES, AND WHAT IT DOES NOT - AND THE ANSWER IS SMALLER THAN THE
SEED SUGGESTS. Two frozen facts do it, and it is the second that fires the gate.
Compiled measurement recorded as `Q-9` in docs/migration/ambiguity-resolutions.md
established that the bridge's host-variable load NEVER LOADS `HV-POST-RRN`, THE TABLE'S
PRIMARY KEY [mysql/ACASDB.sql:L169], so that column is stored at zero. `A-NEW-18` in
docs/migration/anomaly-log.md then established that `move WS-Post-Key to HV-POST-KEY`
[common/glpostingMT.cbl:L1054] is a BYTE move from a group into `PIC 9(18) COMP`, so the
read-back at [common/glpostingMT.cbl:L1085] returns the bytes `06 8E 0C 15 3B 04 30 30`
and NOT the all-`0` image: the first disjunct `if WS-Post-Key = zero`
[general/gl070.cbl:L490-L491] is therefore FALSE, a group compared with `ZERO` being
byte-wise (`Q-NKEY-CMP` reading 7), and the gate that ACTUALLY skips the posting is
`if batch not = WS-Batch-Nos` [general/gl070.cbl:L492-L493], byte-wise too and matching
none of the 100,000 values a `pic 9(5)` batch number can hold (`Q-NKEY-CMP` reading 4).
Either way the posting is discarded before the explosion.
THE WORK FILE IS THEREFORE EMPTY: the three-leg explosion is not
reached, gl072 reads nothing, `end-batch`'s stamp is not reached for either batch, no
balance moves, and the run is a NO-OP over all three bounded tables. That is why the
scenario declares `expected_table_effect: unchanged` and why
docs/migration/scenario-diff-evidence.md section 10.5 records the observed journey as an
empty diff over an unchanged state. It is the SPECIFICATION and it is reproduced, not
corrected (R-4, R-6): a migrated cycle that loaded the RRN and posted the batch would be
a defect FIXED, which
`test_the_run_reproduced_the_measured_no_op_rather_than_posting` is written to catch.

WHAT THE SEED SHAPE IS STILL FOR, given that. It is what makes the no-op ATTRIBUTABLE
rather than accidental: the batch passes every filter phase two applies, the posting
carries VAT and two profit centres, and five nominal accounts stand ready - so when
nothing moves, the only remaining explanation is the zero key, and the assertions can say
so. A fixture that failed a filter would leave three candidate explanations and prove
none of them.

IT ALSO DOES NOT REACH EITHER SILENT SKIP. Skip (a) needs a non-numeric `post-batch`,
which cannot survive `POST-KEY bigint(10) unsigned` [mysql/ACASDB.sql:L156]; skip (b)
needs a POSTING that reaches gl072 at all, and none does. An earlier form of this
docstring described a three-batch, three-posting-kind fixture aimed squarely at both
skips. That fixture is not what `seed_records` declares - and it could not be, because
the store can address only ONE posting primary key while `HV-POST-RRN` goes unloaded, so
a fixture invented to exhibit a path the store cannot reach would be evidence of nothing
(section 10.5 of the evidence document says exactly that). Describing one that does not
exist made two tests in this file read as anomaly locks when they were end-state
agreement checks over a run in which neither skip occurred.

BOTH SKIPS ARE DRIVEN AT THE UNIT LEVEL INSTEAD, against the SHIPPED program:
`tests/arithmetic/test_ledger_balance_accumulation.py` drives
`acas_posting/programs/gl072_transaction_update.py` through each branch with a fake
facade and asserts a POSITIVE WITNESS for each - no batch lookup at all for skip (a), the
lookup pair `[7, 7]` with no nominal read for skip (b) - plus the absence of any effect
and of any counter. What this file adds is the end state, and it says so.

THE PHASE-2 EXTRA-STATUS FILTER MUST BE SATISFIED FOR BATCH A. Pass 2 filters again,
[general/gl070.cbl:L460-L463] verbatim:

    L460       if       status-open
    L461             or not waiting
    L462             or not gl-batch
    L463                go to  loop.

Batch 1 must be closed AND waiting AND a GL batch or it is never pre-processed at all.
Batch 2 fails this filter -- it is `not waiting` -- and it has no postings either way.
And `Bcycle` must equal `system.cyclea` or the cycle filters at
[general/gl070.cbl:L312-L313] and [general/gl070.cbl:L457-L458] skip the batch too. Both
conditions are asserted from the definition below, because they are what makes the
measured no-op attributable to the ZERO POSTING KEY rather than to a batch the filters
rejected -- two very different reasons for an unchanged table, and only one of them is
the anomaly this scenario reproduces.

WHY THE DECLARED TERM CODE OF ZERO IS PROVABLE RATHER THAN HOPEFUL
Only three in-scope programs set `WS-Term-Code` at all: gl070 sets 5
[general/gl070.cbl:L289], sl055 sets 8 [sales/sl055.cbl:L344] and pl055 sets 8
[purchase/pl055.cbl:L286]. Code 5 requires an OPEN batch, which this scenario
deliberately does not seed. Codes 8 are unreachable here because both raise sites sit
inside `if FS-Cobol-Files-Used` -- [sales/sl055.cbl:L326] wrapping L344 and
[purchase/pl055.cbl:L266] wrapping L286 -- and this scenario pins `file_system_used` to
1, so that condition name is false. Neither program is on the General Ledger route in
any case.

SKIP (a)'s REACHABILITY IS AN ARBITRATION, NOT AN ASSUMPTION (R-6)
Skip (a) tests a WORK-FILE field: `03 post-batch pic 9(5).` at [general/gl072.cbl:L111],
written by gl070 at [general/gl070.cbl:L495] from the posting row's own `Batch pic 9(5)`
inside the ten-character group `WS-Post-Key` [copybooks/wspost.cob:L14-L16]. THE HONEST
POSITION:
through the database path that group does not travel as text. The frozen schema holds
the whole of it as ONE NUMERIC COLUMN, `POST-KEY bigint(10) unsigned`
[mysql/ACASDB.sql:L156]; the bridge carries it in `HV-POST-KEY PIC 9(18) COMP`
[common/glpostingMT.cbl:L283], loading it with `move WS-Post-Key to HV-POST-KEY`
[common/glpostingMT.cbl:L1054] and unloading it with `move HV-POST-KEY to WS-Post-Key`
[common/glpostingMT.cbl:L1085]. A non-numeric batch number written into the seed is
therefore COERCED by that pair of group-to-binary moves, and whether any value can still
reach gl072 as non-numeric is a question about the compiled behaviour of those moves.

THAT IS WHY NO TEST BELOW ASSERTS THAT SKIP (a) FIRED. Each asserts only that BOTH SIDES
DID THE SAME THING, whatever that was -- which is the assertion R-6 licenses and the
only one the checkout supports. The seed DECLARES the row aimed at the guard and does
not tidy it away, because R-4 forbids removing the very data an anomaly needs. The
arbitration is recorded in `docs/migration/ambiguity-resolutions.md` under the scenario
file's own heading SKIP (a) AND ITS REACHABILITY.

THE FIVE REJECTION CLASSES -- THIS FILE OWNS CLASS 1
Agent Action Plan section 0.8.1: "a single generic rejection path would fail this
directive." The five differ precisely in their DATABASE EFFECT and must not be
collapsed:

  1. CLEAN REJECTION, NO DATABASE EFFECT -- THIS FILE'S SUBJECT.
     [general/gl072.cbl:L291-L292], [general/gl072.cbl:L306-L307] and the third path at
     [general/gl072.cbl:L348-L349]. Silent, traceless, a pure no-op.
  2. RUN-ABORTING REJECTION -- the control-total mismatch; the effect is THE ABSENCE of
     everything the later phases would have written. Owned by
     `tests/scenarios/test_control_total_mismatch_rejection.py`. THIS SCENARIO MUST NOT
     DRIFT INTO CLASS 2 -- see THE SEED USES A CLOSED BATCH above.
  3. PARTIAL DATABASE EFFECT -- the half-posted double entry at
     [irs/irs030.cbl:L1635-L1652], and the lost update on the two VAT control accounts
     at
     [irs/irs030.cbl:L1602], [irs/irs030.cbl:L1612] and [irs/irs030.cbl:L1704-L1708].
  4. FILE-ABANDONING REJECTION -- [irs/irs030.cbl:L1673-L1678]; the partial state is
     COMMITTED, not rolled back.
  5. PERMANENTLY FAILING FACADE VERB -- [common/acas008.cbl:L299-L307], four published
     verbs refused unconditionally at entry.

NORMALISATION DOES EXACTLY THREE THINGS AND THERE IS NO FOURTH
It is delegated ENTIRELY to `harness/normalize.py` and nothing here reimplements or
extends it:

  JOB 1, trailing spaces in fixed-character columns -- `rstrip(" ")`, TRAILING ONLY,
    because a COBOL alphanumeric `MOVE` is left-justified with right padding so LEADING
    SPACES ARE CONTENT; ASCII U+0020 only; by declared type, `char(1)` included. The
    schema has 238 `char(` columns and zero `varchar(`. It exists for A-12, the width
    drift: `Ledger-Name pic x(24)` [copybooks/wsledger.cob:L27] becomes `PIC X(32)`
    [common/nominalMT.cbl:L299] and `LEDGER-NAME char(32)` [mysql/ACASDB.sql:L127]. Here
    it also reaches `GLBATCH-REC.DESCRIPTION char(24)` [mysql/ACASDB.sql:L94], from `03
    Description pic x(24).` [copybooks/wsbatch.cob:L45].
  JOB 2, decimal scale rendering AT THE DECLARED SCALE -- NOT uniformly two. This
    scenario's money columns are `GLBATCH-REC`'s four `decimal(14,2) unsigned`
    [mysql/ACASDB.sql:L90-L93], matching the UNSIGNED `pic 9(9)v99 comp-3` group at
    [copybooks/wsbatch.cob:L40-L44]; `GLLEDGER-REC.LEDGER-BALANCE decimal(10,2)`
    [mysql/ACASDB.sql:L128] from `pic s9(8)v99 comp-3` [copybooks/wsledger.cob:L28]; and
    `GLPOSTING-REC.POST-AMOUNT` and `VAT-AMOUNT`, both `decimal(10,2)`
    [mysql/ACASDB.sql:L163], [mysql/ACASDB.sql:L168].
  JOB 3, the two- versus four-digit date text forms -- UNDER AN EXPLICIT COLUMN
    ALLOW-LIST ONLY: `GLPOSTING-REC.POST-DAT`, `IRSPOSTING-REC.POST4-DAT`,
    `PSIRSPOST-REC.IRS-POST-DAT`, `SYSTEM-REC.STATS-DATE-PERIOD` and
    `SALEDGER-REC.SALES-STATS-DATE`. `char(8)` DOES NOT IMPLY DATE, and MOST in-scope
    "dates" are BINARY DAY-NUMBER INTEGERS that job 3 must not touch:
    `GLBATCH-REC.ENTERED`, `PROOFED`, `POSTED` and `STORED` are all `int(8) unsigned`
    [mysql/ACASDB.sql:L86-L89], from the four `binary-long` fields at
    [copybooks/wsbatch.cob:L36-L39]. So [general/gl072.cbl:L376]'s stamp writes an
    INTEGER and job 3 leaves it alone.

THE THREE-WAY EXIT CONTRACT OF STAGE 10
  0  the trees are identical, and stdout is EMPTY -- zero bytes, not a banner  -> PASS
  1  a real behavioural difference, with a deterministic report                ->
  FAILURE
  2  THE COMPARISON COULD NOT BE PERFORMED -- a missing tree, a missing table file, a
     malformed dump, a shape mismatch, a `float`, a duplicate primary key, a wrong key
     order, `row_count != len(rows)`, a ragged row or a `null`                 -> ERROR

"A test that treats 'could not compare' as 'no differences' is the single worst bug
available in this tree." Exit 2 is mapped to a harness fault by `tests/conftest.py` and
surfaces as a pytest ERROR, never a pass. The comparison itself is EXACT: `==` after a
type check and nothing else -- no tolerance, no epsilon, no case- or
whitespace-insensitivity, no numeric coercion. `1` against `"1"` IS a difference. Rows
are aligned by PRIMARY-KEY VALUE, never by position, and the two labels are `cobol` and
`python`.

ALWAYS DUMP, THEN DECIDE THE EXIT STATUS. Agent Action Plan section 0.6.5: "The database
effect is therefore the absence of everything the later phases would have written."
ABSENCE IS EVIDENCE, AND FOR THIS SCENARIO IT IS THE ONLY EVIDENCE THE REJECTED
TRANSACTIONS HAVE. A skipped posting leaves nothing behind by construction, so a
short-circuited dump would destroy the only proof that the skip happened identically on
both sides. `run_scenario_parity` takes stages 3 and 4 whatever stage 2 returned, and
the three exit categories -- success, behavioural difference and harness fault -- are
kept distinct and never conflated.

WHAT THIS FILE DELIBERATELY DOES NOT DO -- AND THE PROHIBITIONS ARE GREPPABLE
THE ONLY IMPORT IN THIS FILE IS `pytest`. It never imports the harness package and never
loads a harness path by hand: `harness/` has no `__init__.py` and `pyproject.toml`
excludes `harness*` from packaging, which is the structural enforcement of R-1, and the
three harness modules arrive only through `tests/conftest.py`'s explicit-path loader
behind the `harness` fixture. It never imports the General Ledger command-line entry
point, never runs it as a script, never builds a command line or an argv list, never
spawns a child process and NEVER HARD-CODES ANY OPTION SPELLING -- the promoted-flag
spellings belong to the entry points, and `harness/run_python_scenario.sh` owns the
probe that fails as a harness fault when a required one is absent. `gl_post_cycle`
promotes nothing, so the scenario declares no answer key at all. It carries no binary
floating-point construction, no dataframe or array library, no approximate-equality
helper and no tolerance of any kind (R-2); no test-distribution plugin and no parallel
or randomised ordering, because parallel runs against one shared MariaDB would break the
seed / run / dump / reset / run / dump / diff protocol outright (R-3); and no timing or
performance assertion (Agent Action Plan section 0.8.4). It re-declares neither the
twenty-two-table inventory nor any primary key -- both are read from the harness, which
has the single definition. And it adds no validation, no counter, no warning and no
summary line for a skipped posting.

TRACEABILITY (R-5)
Anomalies named and cited here: A-12 the character-width drift; A-13 the two -- in fact
three -- entirely silent skips, the primary subject; A-14 the nominal account located by
sequential read; A-15 the batch record's declared-length contradiction; A-21 the
field-name collisions forcing qualified references. The register is
`docs/migration/anomaly-log.md`, which names
`acas_posting/programs/gl072_transaction_update.py` as A-13's and A-14's reproducing
module. Oracle questions are `docs/migration/ambiguity-resolutions.md`, cited by
identifier where one exists -- `Q-SORT-TIE-ORDER` for the compiled sort's tie order and
`Q-4` for A-15 -- and by the register's own heading where none does, rather than an
identifier being invented. The per-scenario verdict is recorded in
`docs/migration/scenario-diff-evidence.md`. Those references are TEXTUAL ONLY: nothing
below imports a document, checks that one exists, or skips because one is absent.
`pytest-cov` is evidence that a traced module was exercised and never a gate; there is
no `--cov-fail-under` anywhere.
"""

from __future__ import annotations

import pytest

# The TIER mark, applied to the whole module because every test in it belongs to the
# tier. THE INFRASTRUCTURE MARKS ARE NOT HERE: `database` and `oracle` are declared per
# test, on exactly the tests whose fixture closure reaches the harness stack, because
# several tests in this file read only files on disk and pass on a bare host. A module
# mark would claim they need a MariaDB and a built oracle, and `-m database` would then
# select tests that require neither.
pytestmark = pytest.mark.scenario

SCENARIO = "mixed_accepted_rejected"

# THE THREE TABLES THE SEED FILLS, each named by the `seed_files:` entry that fills it:
# ledger.dat -> GLLEDGER-REC, batch.dat -> GLBATCH-REC, posting.dat -> GLPOSTING-REC.
# All three of this scenario's affected tables are seeded, which is what makes the
# rejection evidence readable: A-13's two SILENT SKIPS are claims that specific rows
# were NOT posted, and "not posted" is indistinguishable from "never present" unless the
# tables came back with rows.
BATCH_TABLE = "GLBATCH-REC"
LEDGER_TABLE = "GLLEDGER-REC"
POSTING_TABLE = "GLPOSTING-REC"

SEEDED_TABLES = (
    BATCH_TABLE,
    LEDGER_TABLE,
    POSTING_TABLE,
)


# ---------------------------------------------------------------------------
#  THE MODULE PREAMBLE ABOVE IS THE WHOLE OF IT, AND THE ONLY IMPORT IS pytest.
#
#  `pytest.mark.scenario` is registered ONCE, in pyproject.toml's
#  [tool.pytest.ini_options] markers list, under --strict-markers. It is NOT
#  re-registered here and there is no pytest_configure, no pytest_plugins list and no
#  collection hook anywhere in this file.
#
#  EVERYTHING SHARED COMES FROM tests/conftest.py, AND IT IS REACHED THROUGH FIXTURES
#  AND NEVER IMPORTED. That is the house convention across tests/ and it is what keeps
#  R-1 structural rather than a matter of discipline: the three harness modules are
#  loaded by explicit file path inside conftest and handed over behind the `harness`
#  fixture, so no test file needs - or is able to reach - the harness package as an
#  importable name. There is no __init__.py in this directory, no nested conftest.py and
#  no helper module.
#
#  WHY INJECTED FIXTURES ARE ANNOTATED `object`. Their real types - Protocol,
#  HarnessModules, ParityRun, PinnedRunDate - are defined in tests/conftest.py, and
#  naming them here would require importing it. `object` is a builtin, needs no import,
#  and states the truth: an opaque value supplied by conftest whose contract is
#  documented there. Collections use builtin generics, which need no import either.
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def _parity_cache() -> dict[str, object]:
    """A module-lifetime holder for the one parity run this file's assertions read.

    WHY A CACHE AT ALL, AND WHY IT IS SHAPED LIKE THIS. The eleven assertions below are
    eleven statements about ONE ten-stage run's evidence, exactly as
    `tests/determinism/test_two_runs_byte_identical.py` makes two comparisons about one
    run pair. Running the protocol once per assertion would seed, drive the compiled
    oracle, dump, reset, drive the Python cycle, dump and compare nine separate times
    against ONE shared database, which is nine sequential rewrites of the same artifacts
    and would make the tests look independent when every one of them reads the same
    database.

    A module-scoped fixture cannot request the `protocol` fixture directly, because
    `protocol` is function-scoped by design - it applies the stack skip guard per test
    so a bare host gets a precise SKIP rather than a session-wide error. So the cache is
    module-scoped and the run that populates it is function-scoped.

    A plain dict is sufficient and correct: execution is strictly sequential (R-3), so
    there is no race to guard.

    Returns:
        An empty mapping on first use, then the same mapping for the rest of the module.
    """
    return {}


@pytest.fixture
def parity(protocol: object, _parity_cache: dict[str, object]) -> object:
    """Drive all ten protocol stages for this scenario ONCE, and return the verdict.

    THE STAGES ARE CALLED, NEVER REIMPLEMENTED. `protocol.run_scenario_parity` composes
    them in the mandated order and is the single definition of the protocol (Agent
    Action Plan section 0.4.3), so no test here reimplements the comparison:

        1  reset_db.sh + seed.sh    6  run_python_scenario.sh
        2  run_cobol_scenario.sh    7  dump --side python
        3  dump --side cobol        8  normalize.py
        4  normalize.py             9  verify both captures published
        5  reset_db.sh + seed.sh   10  diff_states.py

    EIGHT LOGICAL STAGES, TEN NUMBERED ONES. Agent Action Plan section 0.3.2 fixes the
    order as "seed, run, dump, normalize, reset, run, dump, diff" - eight. The driver
    The PROTOCOL numbers ten, reading the list from
    `harness/normalize.py`, because it makes BOTH normalisations and the publication
    check explicit rather than implied. Nothing was added to the protocol; where older
    prose says "stage 8" it means today's stage 10, the diff. The runners' own
    `Check n/8' headings are their internal preflight checks and are not protocol
    stages.

    STAGES 3 AND 4 ARE TAKEN WHATEVER STAGE 2 RETURNED, and 7 whatever 6 returned.
    Absence is evidence, and for this scenario it is the ONLY evidence the rejected
    transactions have, so the dump is never short-circuited.

    NOTHING HERE CONSTRUCTS A COMMAND LINE. No argv is built, no child process is
    spawned, no option spelling is written down and the General Ledger command-line
    entry point is never imported or run as a script. The two runner scripts own their
    own command lines and their own required-flag probe, and a missing flag is a HARNESS
    FAULT there rather than a silent difference here.

    Args:
        protocol: Every stage and both compositions, from `tests/conftest.py`. It
        applies
            the stack skip guard itself, so a host with no Docker, no MariaDB and no
            built GnuCOBOL oracle SKIPS with a precise reason and never errors.
        _parity_cache: The module-lifetime holder, so the ten stages run once.

    Returns:
        The `ParityRun`: every stage result in order, both run results, the stage-10
        verdict and the paths of every artifact.

    Raises:
        Skipped: The harness Compose stack is unusable - a SKIP and never an error.
        Exception: A stage whose failure destroys the evidence failed - the seed, the
            reset, either dump, either normalisation, or the comparison itself with exit
            2. Every one of those is a harness fault and a pytest ERROR, never a pass.
    """
    run = _parity_cache.get("run")
    if run is None:
        run = protocol.run_scenario_parity(SCENARIO)
        _parity_cache["run"] = run

    # THE COMPARISON WAS BOUNDED BY THE DECLARED TABLES, IN THE DECLARED ORDER. The
    # order is load-bearing: the report is written in it and so is the seed fingerprint.
    assert tuple(run.tables) == tuple(protocol.in_scope_tables()), (
        f"{SCENARIO}: the comparison was bounded by {list(run.tables)}, but the "
        f"protocol bounds it by ALL 22 IN-SCOPE TABLES, "
        f"{list(protocol.in_scope_tables())}. A narrower bound cannot reveal a "
        f"difference in anything the scenario did not expect to move - including the "
        f"system rows `overrewrite` writes on BOTH sides "
        f"[general/general.cbl:L656-L672]."
    )
    #  The scenario's `affected_tables` is its DECLARED EFFECT, not the bound. It must be
    #  a subset of the bound, or something the scenario claims to change went uncompared.
    assert set(protocol.affected_tables(SCENARIO)) <= set(run.tables), (
        f"{SCENARIO}: declares an effect on "
        f"{sorted(set(protocol.affected_tables(SCENARIO)) - set(run.tables))!r}, which the comparison never covered."
    )

    # THE ORACLE REACHED THE DECLARED DISPOSITION, and NEITHER side is a harness fault.
    # `reference_only` keeps the Python side's status a behavioural question owned by a
    # test body, while the fault refusal - a runner exiting in its own documented band,
    # or on `argparse` usage exit 2 - stays here where it reads as an ERROR.
    #  BOTH SIDES DROVE THE SAME ORDERED OPERATION LIST. The
    #  comparison below is between one COBOL run and one Python run, and it means
    #  nothing unless the two drove the same work in the same order - an empty diff
    #  between a short run and a full one being the most dangerous false pass this tier
    #  can produce. Both runners resolve the list from the scenario itself and publish
    #  one status row per operation, so it is checked rather than assumed.
    protocol.assert_operations_driven(run, operations=tuple(protocol.definition(SCENARIO)["operations"]))

    protocol.assert_declared_statuses(
        run,
        operations=tuple(protocol.definition(SCENARIO)["operations"]),
        declared=list(protocol.definition(SCENARIO)["expected_status"]),
        reference_only=True,
    )

    # BOTH SIDES STARTED FROM THE SAME RECORDED SEEDED STATE. One line per bounded
    # table in the declared order plus the parameter row, each line carrying the table
    # name, its ROW COUNT and a SHA-256 of its canonical primary-key-ordered dump -
    # produced for both sides by the one producer, harness/dump_tables.py --table-digest. The digest is
    # what makes the claim mean something: equal counts with different VALUES is exactly
    # the case a count-only record could not see, and it is the case a reset that
    # restored the wrong rows would produce. Stage 5 drops and re-applies all 33 tables
    # and re-seeds between the two runs, so this is the claim that the reset actually
    # restored the state the oracle had started from.
    protocol.assert_seed_fingerprints_agree(run)

    # SOMETHING WAS THERE TO COMPARE. Every assertion in this file - and especially the
    # two SILENT-SKIP claims, which are assertions about rows that must NOT have moved -
    # holds just as well against three empty tables without this.
    protocol.assert_non_vacuous(run, tables_requiring_rows=SEEDED_TABLES)

    return run


@pytest.fixture
def normalized_dumps(parity: object, harness: object) -> dict[str, dict[str, object]]:
    """Both sides' NORMALISED dumps for the three bounded tables, shape already
    asserted.

    THE SHAPE CONTRACT HAS EXACTLY ONE DEFINITION AND THIS READS IT THERE.
    `harness/diff_states.py`'s `load_dump` is the reader-and-asserter the comparison
    itself uses: five keys in fixed order, an in-scope table, a single-column primary
    key present in `columns`, `row_count == len(rows)`, every row of the declared width,
    no duplicate primary key, NO NULL VALUE and NO `float` (R-2). Re-deriving any of
    that here would be a second definition that could drift (R-4).

    THE NORMALISED trees are read and never the raw ones. `harness/diff_states.py`
    refuses to compare a tree that is not normalised, and a verdict taken over raw dumps
    would still carry the representation artefacts that the three normalisation jobs
    exist to remove - so a raw read here would be assertion-shaped but not evidence.

    Neither the side labels nor the table list is written down locally: the sides come
    from `harness/dump_tables.py`'s own `SIDES` and the tables from the scenario's
    declared affected-table list, which is how a comparison is BOUNDED.

    Args:
        parity: The completed run, for its artifact paths and its bounded table list.
        harness: The three harness modules, loaded by explicit file path through
            conftest. The harness package is NEVER imported by name.

    Returns:
        `{side: {table: dump}}`, keyed by the harness's own side labels.

    Raises:
        Exception: `harness/diff_states.py`'s own errors - a missing table file, an
            unreadable or malformed dump, a duplicate primary key, a null or a float.
            All are harness faults and pytest ERRORs, never passes.
    """
    diff_states = harness.diff_states
    dumps: dict[str, dict[str, object]] = {}
    for side in harness.dump_tables.SIDES:
        tree = parity.paths.normalized_dir(side)
        dumps[side] = {
            table: diff_states.load_dump(tree / diff_states.dump_filename(table))
            for table in parity.tables
        }
    return dumps


@pytest.fixture(scope="session")
def column_by_key() -> object:
    """A reader that projects one dump column into `{primary key: value}`.

    A LOCALISER, NOT A COMPARATOR. The authoritative comparison is stage 10 and there is
    exactly one of it; this exists so that a NAMED assertion can say which column
    carries the property it is about - `CLEARED-STATUS`, `POSTED`, `LEDGER-BALANCE` -
    instead of restating the verdict. It performs no comparison, applies no tolerance
    and alters no value: it reads the dump's own `columns` list to find the ordinal, and
    the dump's own `primary_key` to find the alignment column, so no column position and
    no key name is hard-coded anywhere in this file.

    ROWS ARE KEYED BY PRIMARY-KEY VALUE AND NEVER BY POSITION, which is the same rule
    the differ applies. `load_dump` has already refused any dump carrying a duplicate
    key, so the projection cannot silently lose a row.

    Returns:
        A callable taking a parsed dump and a column name and returning the mapping.
    """

    def _project(dump: object, column: str) -> dict[object, object]:
        """Project one column of one dump.

        Args:
            dump: A parsed, asserted dump object.
            column: The column to read, spelled as `mysql/ACASDB.sql` spells it.

        Returns:
            `{primary-key value: column value}` for every row.

        Raises:
            AssertionError: The dump does not declare that column. A wrong column name
                is a fault in this file, not a finding about the migration, so it says
                so.
        """
        columns = list(dump["columns"])
        assert column in columns, (
            f"this file asked for column {column!r} of {dump['table']!r}, which the "
            f"dump does not declare. Its columns are {columns}, in the schema ordinal "
            f"order mysql/ACASDB.sql fixes. A wrong column name here is a fault in "
            f"this test file and not a finding about the migration."
        )
        ordinal = columns.index(column)
        key_ordinal = columns.index(str(dump["primary_key"]))
        return {row[key_ordinal]: row[ordinal] for row in dump["rows"]}

    return _project



# ---------------------------------------------------------------------------
#  THE PRECONDITIONS  -  NEITHER OF THESE TWO NEEDS THE STACK
#
#  They read a file on disk, so they run on a bare host with no Docker, no MariaDB and
#  no built oracle. That matters: the preconditions are what stop a run that could only
#  ever have produced a FALSE PASS from being started at all, and a guard that is itself
#  skipped when the environment is thin would guard nothing.
# ---------------------------------------------------------------------------


def test_scenario_definition_preconditions(
    scenario_loader: object, pinned_clock: object
) -> None:
    """Assert every input this scenario's verdict depends on, before any stage runs.

    `file_system_used == 1` IS THE FALSE-PASS TRAP, AND IT IS WORSE HERE THAN IN ANY
    OTHER
    SCENARIO. `copybooks/wssystem.cob:L112-L114` declares `File-System-Used pic 9` with
    `88 FS-Cobol-Files-Used value zero` and `88 FS-MySql-Used value 1`, and the batch
    handler routes to the database only when the flag is non-zero -
    `[common/acas007.cbl:L316-L320]` verbatim:

        L316       if       not FS-Cobol-Files-Used
        L317                move RDBMS-Flat-Statuses to FA-RDBMS-Flat-Statuses
        L318                perform  ba-Process-RDBMS
        L319                go to AA-Main-Exit
        L320       end-if.

    With the flag at zero the handler never touches MySQL, BOTH dumps come back empty,
    the comparison finds nothing and exits 0 - a SILENT FALSE PASS. In this scenario
    that is the most dangerous configuration in the whole suite, because "the rejected
    rows left no trace" and "nothing happened at all" look IDENTICAL in an empty dump.
    The seeded system flat file must carry the same value, since the COBOL reads its
    flag from there and not from argv [general/general.cbl:L399-L419]; the runners' seed
    fingerprint is the second line of defence and lives with them.

    `irs_instead` IS PINNED EXPLICITLY. `copybooks/wssystem.cob:L179-L181` verbatim:

        L179         05  IRS-Instead     pic x.
        L180             88  IRS-Used                   value "Y".
        L181             88  IRS-Both-Used              value "B".   *> 26/11/16

    THREE states, and the third - a space - HAS NO CONDITION NAME AT ALL: both
    predicates are simply false, which is General Ledger only. Agent Action Plan section
    0.6.4:
    "leaving it at a default would make the affected-table list ambiguous", so it is
    declared rather than defaulted. A YAML space or empty value reaches the CLI as the
    LITERAL SPACE `--irs-instead ' '` - there is no `N` token and the option's own
    help says so - so the column stores a space, and normalisation job 1 trims that
    to the empty string on BOTH sides - correct, because it is applied identically.

    THE PINNED CLOCK MATTERS CONCRETELY HERE. The binary observable is `05 Run-Date
    binary-long.` [copybooks/wssystem.cob:L67], and [general/gl072.cbl:L376] `move
    run-date to posted` stamps the accepted batch with it, so a drifting clock would
    produce a differing `GLBATCH-REC.POSTED` and a difference that was about the clock
    rather than about the accounting.

    `cyclea` MUST BE NON-ZERO [copybooks/wssystem.cob:L62], and every seeded batch's
    `Bcycle` [copybooks/wsbatch.cob:L34] must equal it, or the cycle filters at
    [general/gl070.cbl:L312-L313] and [general/gl070.cbl:L457-L458] skip the batch and
    the run posts nothing at all. `period` is INERT on this route,
    because only `gl_end_of_cycle` consumes it. NO committed scenario drives that
    operation, so no table-state witness observes the period boundary or the quarter
    rollover; the Agent Action Plan's inventory names eight scenarios and none of them is
    an end-of-cycle definition. Appending the operation to THIS scenario was separately
    considered and DECLINED on six recorded grounds, and that decision is
    oracle-reversible in
    `docs/migration/ambiguity-resolutions.md` rather than re-litigated.

    NO MONETARY OR QUANTITY VALUE IS READ FROM THE YAML AND NONE COULD BE (R-2): YAML
    parses a bare decimal literal as a binary float, so every money figure lives in the
    seeded flat files as decimal text in the frozen record layout. The integers this
    test does read are checked with `type(...) is int` rather than `isinstance`, because
    `bool` is a subclass of `int` and `True` is not a COBOL `pic 9`.

    Args:
        scenario_loader: `scenario_definition`, which parses with `yaml.safe_load` and
            never the arbitrary-object loader. This file never reads the YAML itself and
            never imports a YAML library.
        pinned_clock: The project-wide pinned pair, already asserted by
            `tests/conftest.py` against `acas_posting/clock.py`.
    """
    definition = scenario_loader(SCENARIO)

    # THE IDENTITY. The COBOL runner falls back to this file's own basename when no
    # scenario key is present, so the two agree by construction and a disagreement would
    # mean the definition had been copied without being renamed.
    assert definition["name"] == SCENARIO, (
        f"the definition names itself {definition['name']!r} but lives in "
        f"{SCENARIO}.yaml. The COBOL runner takes the scenario name from the file stem "
        f"when no key is present, so a disagreement makes two stages disagree about "
        f"which scenario produced the evidence."
    )
    assert definition["subsystem"] == "general", (
        f"this scenario drives the General Ledger posting cycle, whose menu is "
        f"general/general.cbl; it declares subsystem {definition['subsystem']!r}."
    )

    # THE OPERATION, under both spellings. `operations` is a FLAT sequence of operation
    # names and never a sequence of blocks: a list whose items are themselves mappings
    # is recorded and not read by the Python runner, and a mapping under a key the
    # runner does read is refused outright.
    assert definition["operation"] == "gl_post_cycle", (
        f"the route under test is [general/general.cbl:L805-L815] load08, which is "
        f"gl_post_cycle; the definition declares {definition['operation']!r}."
    )
    assert list(definition["operations"]) == [definition["operation"]], (
        f"the grouped and flat spellings of the operation must hold the same value; "
        f"`operations` is {list(definition['operations'])!r} and `operation` is "
        f"{definition['operation']!r}. They are written side by side in the definition "
        f"precisely so that drift is visible at a glance."
    )

    # THE DECLARED TERM CODE, POSITIONALLY. Zero states that gl070 did NOT raise the
    # open-batch abort at [general/gl070.cbl:L289] and that the cycle therefore ran all
    # three phases - which is the whole premise of this scenario, since gl072 is where
    # A-13 lives and the menu's gate at [general/general.cbl:L810-L811] would have
    # prevented gl071 and gl072 from running at all.
    statuses = list(definition["expected_status"])
    assert statuses == [0], (
        f"this scenario must run to completion with term code zero; it declares "
        f"{statuses!r}. Code 5 is the open-batch abort and belongs to "
        f"control_total_mismatch, and codes 8 are unreachable on this route."
    )
    assert len(statuses) == len(list(definition["operations"])), (
        f"`expected_status` is positional against `operations`: {statuses!r} against "
        f"{list(definition['operations'])!r}."
    )
    assert type(statuses[0]) is int, (
        f"a term code is a whole number; the definition carries a "
        f"{type(statuses[0]).__name__}. A real number in a scenario file is refused by "
        f"the Python-side reader outright (R-2)."
    )

    system = definition["system"]

    # 3.1 THE FALSE-PASS TRAP.
    assert system["file_system_used"] == 1, (
        f"file_system_used is {system['file_system_used']!r} and must be 1. With zero, "
        f"[common/acas007.cbl:L316-L320] never routes to MySQL, both dumps come back "
        f"empty and the comparison exits 0 - a SILENT FALSE PASS. It is worse in this "
        f"scenario than in any other, because an empty dump cannot distinguish 'the "
        f"rejected rows left no trace' from 'nothing happened at all'."
    )
    assert type(system["file_system_used"]) is int, (
        f"`File-System-Used pic 9` [copybooks/wssystem.cob:L112] is a single digit; "
        f"the definition carries a {type(system['file_system_used']).__name__}."
    )

    # 3.2 THE FAN-OUT SWITCH, under both spellings.
    assert system["irs_instead"] == " ", (
        f"irs_instead is {system['irs_instead']!r} and must be a single space - the "
        f"third state of [copybooks/wssystem.cob:L179-L181], which has NO condition "
        f"name at all and means General Ledger only. 'Y' or 'B' would fan out to the "
        f"IRS tables and make the affected-table list wrong."
    )
    assert definition["irs_instead"] == system["irs_instead"], (
        f"the grouped and flat spellings of irs_instead must hold the same value; "
        f"{definition['irs_instead']!r} against {system['irs_instead']!r}."
    )

    # 3.3 THE PINNED CLOCK, both observables, both spellings.
    clock = definition["clock"]
    assert clock["to_day"] == pinned_clock.to_day, (
        f"the scenario pins the text date {clock['to_day']!r} while the project pins "
        f"{pinned_clock.to_day!r}. `to-day pic x(10)` is a linkage parameter of the "
        f"General Ledger shape, and two different dates would make the two sides post "
        f"under different ones."
    )
    assert clock["run_date"] == pinned_clock.run_date, (
        f"the scenario pins the binary run date {clock['run_date']!r} while the "
        f"project "
        f"pins {pinned_clock.run_date!r}. It is `05  Run-Date        binary-long.` "
        f"[copybooks/wssystem.cob:L67], and [general/gl072.cbl:L376] stamps "
        f"GLBATCH-REC.POSTED with it, so a drift is directly visible in the diff."
    )
    assert definition["run_date_text"] == clock["to_day"], (
        f"the flat and grouped spellings of the text date must agree; "
        f"{definition['run_date_text']!r} against {clock['to_day']!r}."
    )
    assert definition["run_date_binary"] == clock["run_date"], (
        f"the flat and grouped spellings of the binary run date must agree; "
        f"{definition['run_date_binary']!r} against {clock['run_date']!r}."
    )
    assert type(clock["run_date"]) is int, (
        f"`Run-Date binary-long` is a whole day number; the definition carries a "
        f"{type(clock['run_date']).__name__}."
    )

    # The date form governs the digit ORDER the COBOL runner types at the date prompt
    # [copybooks/wssystem.cob:L128-L132]; one is the UK form, matching the pinned
    # DD/MM/CCYY text above.
    assert system["date_form"] == definition["date_form"], (
        f"the grouped and flat spellings of date_form must agree; "
        f"{system['date_form']!r} against {definition['date_form']!r}."
    )
    assert type(system["date_form"]) is int, (
        f"date_form is a single digit; the definition carries a "
        f"{type(system['date_form']).__name__}."
    )

    # 3.4 THE ACCOUNTING CYCLE, and the inert period.
    assert type(system["cyclea"]) is int, (
        f"`cyclea` [copybooks/wssystem.cob:L62] is a whole number; the definition "
        f"carries a {type(system['cyclea']).__name__}."
    )
    assert system["cyclea"] != 0, (
        f"cyclea is {system['cyclea']!r}. Every seeded batch's Bcycle "
        f"[copybooks/wsbatch.cob:L34] must equal it, or [general/gl070.cbl:L312-L313] "
        f"and [general/gl070.cbl:L457-L458] skip the batch on both passes and the run "
        f"posts nothing - a silent failure of this scenario's premise rather than a "
        f"finding."
    )
    # DECLARED AND INERT: this route never reaches gl080, so nothing reads `period`
    # here, and no committed scenario drives that operation at all.
    # Its presence is asserted; its value is not interpreted, because
    # interpreting a declared value and judging it would be the added validation R-3
    # forbids.
    assert type(system["period"]) is int, (
        f"`period` is a whole number; the definition carries a "
        f"{type(system['period']).__name__}. It is INERT on this route - gl080 is the "
        f"only reader [copybooks/wssystem.cob:L64] and this route never reaches it."
    )

    # 3.6 THE SEED FILES - EXACTLY FOUR, in the loader order the frozen script fixes.
    #   system.dat  -> the four-loader block [common/masterLD.sh:L51-L88]: systemLD,
    #                  then sys4LD, then finalLD, then dfltLD. Effectively mandatory:
    #                  without the system record the menu calls its interactive setup
    #                  program [general/general.cbl:L385-L396] and the runner blocks.
    #   ledger.dat -> nominalLD [common/masterLD.sh:L103] -> GLLEDGER-REC batch.dat ->
    #   glbatchLD [common/masterLD.sh:L94] -> GLBATCH-REC posting.dat -> glpostingLD
    #   [common/masterLD.sh:L109] -> GLPOSTING-REC
    # `harness/seed.sh` reproduces that per-file contract and NEVER invokes
    # common/masterLD.sh, which its own author marks untested at [common/masterLD.sh:L4]
    # and which is not valid shell - all 24 loader lines omit the `;` before `fi`, so
    # `bash -n` rejects it, and it ends in an interactive pager that would block a run
    # forever. It is FROZEN and is not fixed (R-3, R-4).
    expected_files = ["system.dat", "ledger.dat", "batch.dat", "posting.dat"]
    seed = definition["seed"]
    assert list(seed["files"]) == expected_files, (
        f"the seed declares {list(seed['files'])!r}; this scenario is seeded from "
        f"exactly {expected_files!r}. Each maps to one loader of the frozen contract "
        f"[common/masterLD.sh:L44-L115], and the three ledger files map one-to-one "
        f"onto the three affected tables."
    )
    assert list(definition["seed_files"]) == list(seed["files"]), (
        f"the flat and grouped spellings of the seed file list must agree; "
        f"{list(definition['seed_files'])!r} against {list(seed['files'])!r}."
    )
    for name in seed["files"]:
        assert "/" not in name and "\\" not in name, (
            f"each declared seed file must be a BARE file name; got {name!r}. The "
            f"seeder resolves the directory itself and refuses a path."
        )
    assert definition["seed_dir"] == seed["data_dir"], (
        f"the flat and grouped spellings of the seed directory must agree; "
        f"{definition['seed_dir']!r} against {seed['data_dir']!r}."
    )
    assert isinstance(seed["data_dir"], str) and seed["data_dir"], (
        f"the seed directory must be a non-empty RELATIVE directory name; got "
        f"{seed['data_dir']!r}. An absolute path would carry a host identity into a "
        f"file required to have none (R-6)."
    )
    assert not seed["data_dir"].startswith("/"), (
        f"the seed directory is {seed['data_dir']!r} and must be relative: its two "
        f"consumers resolve it against different bases, which is a property of the "
        f"consumers and not of the definition."
    )

    # 3.7 THE SEED'S ACTUAL SHAPE, READ OUT OF `seed_records` AND ASSERTED. This module's
    # docstring describes the fixture in prose; these assertions are what stop the prose
    # from describing a fixture that is not there. Claiming three batches and three kinds
    # of posting row, which `seed_records` does NOT declare, is exactly the discrepancy
    # that lets a test in this file read as an anomaly lock while the branch it names is
    # never reached. Every number below is read from the
    # definition, so extending the fixture fails here first and the prose gets updated
    # with it.
    assert "batch.dat" in expected_files and "posting.dat" in expected_files, (
        "the batch and posting files are what carry the batches and the postings; "
        "without both there is nothing for gl070's two passes to select."
    )
    records = definition["seed_records"]
    batches = records["batch.dat"]
    postings = records["posting.dat"]
    accounts = records["ledger.dat"]

    waiting = [row for row in batches if int(row["Cleared-Status"]) == 0]
    unwaiting = [row for row in batches if int(row["Cleared-Status"]) != 0]
    assert len(waiting) == 1 and len(unwaiting) == 1, (
        f"this scenario is MIXED, so `batch.dat` must declare exactly one WAITING batch "
        f"and exactly one NOT-WAITING batch [copybooks/wsbatch.cob:L29-L32]; it declares "
        f"{len(waiting)} waiting and {len(unwaiting)} not waiting. Without both, the "
        f"file is a duplicate of the clean-batch scenario."
    )
    assert all(int(row["Batch-Status"]) == 1 for row in batches), (
        f"every declared batch must be CLOSED [copybooks/wsbatch.cob:L25-L27]: an OPEN "
        f"batch makes gl070 raise term code 5 [general/gl070.cbl:L287-L290] and the "
        f"whole cycle aborts, which is the control-total-mismatch scenario and not this "
        f"one. Statuses: {[row['Batch-Status'] for row in batches]!r}."
    )
    assert all(int(row["WS-Ledger"]) == 1 for row in batches), (
        f"every declared batch must be a GL batch [copybooks/wsbatch.cob:L15-L16] or "
        f"phase 2's filter [general/gl070.cbl:L460-L463] drops it. Ledgers: "
        f"{[row['WS-Ledger'] for row in batches]!r}."
    )

    # THE POSTINGS BELONG TO THE WAITING BATCH ONLY, and that is why neither silent skip
    # is reachable here - stated as an assertion so the docstring's claim is enforced
    # rather than trusted. A posting added for the not-waiting batch would make skip (b)
    # reachable, and this assertion is where that change announces itself.
    waiting_key = waiting[0]["WS-Batch-Nos"]
    unwaiting_key = unwaiting[0]["WS-Batch-Nos"]
    assert {str(row["Batch"]) for row in postings} == {str(waiting_key)}, (
        f"`posting.dat` declares postings for batch(es) "
        f"{sorted({str(row['Batch']) for row in postings})!r}; on this fixture they all "
        f"belong to the WAITING batch {str(waiting_key)!r}. If a posting is ever added "
        f"for the NOT-WAITING batch {str(unwaiting_key)!r}, skip (b) at "
        f"[general/gl072.cbl:L306-L307] becomes reachable end to end - update this "
        f"assertion, this module's docstring and the two A-13 tests together, because "
        f"all three describe what the fixture reaches."
    )
    assert all(str(row["Batch"]).isdigit() for row in postings), (
        f"every declared posting's batch number is numeric, which is why skip (a) at "
        f"[general/gl072.cbl:L291-L292] is not reachable here either: "
        f"{[str(row['Batch']) for row in postings]!r}. `POST-KEY` is "
        f"`bigint(10) unsigned` [mysql/ACASDB.sql:L156], so a non-numeric batch number "
        f"cannot reach gl072 through the database path at all."
    )
    assert any(
        row.get("Vat-AC") not in (None, "", "0")
        and str(row.get("Vat-Amount", "0")).strip("0.") != ""
        for row in postings
    ), (
        f"at least one posting must carry BOTH a non-zero VAT account and a non-zero "
        f"VAT amount - the shape the OR-gate at [general/gl070.cbl:L521-L523] would "
        f"take to write gl070's third leg. It is not reached on this fixture, because "
        f"the round trip corrupts `POST-KEY` and the posting is skipped at "
        f"[general/gl070.cbl:L492-L493] by `if batch not = WS-Batch-Nos` "
        f"(`A-NEW-18`, `Q-NKEY-CMP`); the shape is asserted so that the "
        f"measured no-op is attributable to THAT and not to a posting that would have "
        f"been uninteresting anyway. Declared: "
        f"{[(row.get('Vat-AC'), row.get('Vat-Amount')) for row in postings]!r}."
    )
    assert len({(row["WS-Ledger-Nos"], row["Ledger-PC"]) for row in accounts}) >= 3, (
        f"`ledger.dat` must declare at least three distinct nominal keys, so that the "
        f"balances the run leaves ALONE are several rather than one and an unchanged "
        f"`GLLEDGER-REC` is a substantive observation. Declared: "
        f"{sorted({(row['WS-Ledger-Nos'], row['Ledger-PC']) for row in accounts})!r}."
    )


def test_affected_tables_are_in_scope_and_alphabetical(
    scenario_loader: object, in_scope_table_names: object, vocabulary: object
) -> None:
    """The comparison is bounded by exactly three tables, alphabetical, all in scope.

    THE ORDER IS LOAD-BEARING, NOT COSMETIC. The Python-side runner records one row
    count per affected table IN THE ORDER DECLARED and refuses to proceed if the two
    sides disagree, so a reordered list is a HARNESS FAULT rather than a finding.
    Alphabetical is also the dumper's own iteration order, so the declared order and the
    produced order coincide.

    `GLPOSTING-REC` IS THE UNCHANGED WITNESS, and its presence on this list is what
    earns this scenario its name. The verb census in this module's docstring shows that
    gl072 issues ZERO `GL-Posting-*` verbs and that gl070 is read-only throughout, so
    nothing on the route writes it. It is bounded in anyway: a skipped posting must
    leave its source row exactly as seeded, and the dump is the only thing that can
    prove that on both sides. Without it, "the rejected rows left no trace" would be
    unfalsifiable.

    THE TWENTY-TWO-TABLE INVENTORY IS NOT RESTATED HERE. It is read from
    `harness/dump_tables.py`'s `IN_SCOPE_TABLES`, which has the single definition of the
    inventory, the single-column primary keys and the declared column counts (R-4). The
    eleven out-of-scope tables are never dumped and the dumper refuses them by name.

    Args:
        scenario_loader: `scenario_definition`. Read here rather than through
            `protocol.affected_tables` deliberately: this assertion must run on a bare
            host, and the protocol object applies the stack skip guard.
        in_scope_table_names: The twenty-two in-scope names, ascending, from the
        harness.
        vocabulary: The shared stack-free vocabulary bundle - the operation names both
            runners accept, the term codes, the scenario keys and the pinned clock pair
            - so this test reaches them without an `import conftest`.
    """
    declared = list(scenario_loader(SCENARIO)["affected_tables"])
    in_scope = tuple(in_scope_table_names)

    assert declared == [
        "GLBATCH-REC",
        "GLLEDGER-REC",
        "GLPOSTING-REC",
        "SYSDEFLT-REC",
        "SYSTEM-REC",
    ], (
        f"this scenario bounds the comparison to the two tables gl072's two Rewrites "
        f"mutate - GLBATCH-REC [general/gl072.cbl:L377] and GLLEDGER-REC "
        f"[general/gl072.cbl:L382] - plus GLPOSTING-REC as the unchanged witness and "
        f"the two menu-persisted tables; it declares {declared!r}.\n"
        f"SYSDEFLT-REC and SYSTEM-REC are the two menu-persisted tables MEASURED "
        f"comparable - the General menu exit rewrites keys 1, 2 and 4 "
        f"[general/general.cbl:L656-L692] and keys 1 and 2 come back byte-identical "
        f"on both sides. Key 4, SYSTOT-REC, is the one that cannot be compared: the "
        f"menu sources it from the COBOL flat file alone "
        f"[general/general.cbl:L402-L404], the RDB read being commented out at "
        f"L434-L436, so its exit returns sys4LD's four-spare sentinel "
        f"[common/sys4LD.cbl:L368-L390] from 1.00 to 0.00."
    )
    assert len(declared) == len(set(declared)) == 5, (
        f"the affected-table list must name three distinct tables; got {declared!r}. A "
        f"repeated name would be dumped and compared twice and would double-count "
        f"every finding for it."
    )
    assert declared == sorted(declared), (
        f"the affected-table list must be alphabetical, because the Python-side runner "
        f"writes its seed fingerprint in the DECLARED order and a disagreement between "
        f"the two sides is a harness fault; got {declared!r}, expected "
        f"{sorted(declared)!r}."
    )
    for table in declared:
        assert table in in_scope, (
            f"{table!r} is not one of the twenty-two in-scope tables of "
            f"harness/dump_tables.py's IN_SCOPE_TABLES. The eleven out-of-scope tables "
            f"of the frozen schema are never dumped and the dumper refuses them by "
            f"name."
        )

    # BOUNDING, NEVER IGNORING - AND WHICH SYSTEM TABLE FALLS WHERE WAS MEASURED
    # RATHER THAN REASONED (rule R-6). No migrated PROGRAM persists a system table - a
    # census across all twelve finds no `System-*` facade verb in any of them. The
    # MENU-EXIT path does [general/general.cbl:L656-L667], and BOTH SIDES REACH IT:
    # `acas_posting/cli/args.py`'s `overrewrite` is called by every one of the seven
    # routes, so key 1 is written on both sides of every scenario. That was ONCE taken
    # to mean every system table had to be excluded as a guaranteed false failure. It
    # was wrong for two of them: SYSTEM-REC and SYSDEFLT-REC come back byte-identical
    # on the two sides, so both are bounded IN above - which matters here, because a
    # mixed batch that silently advanced an allocator would otherwise leave no trace
    # anywhere. Two of SYSTEM-REC's 169 columns are withheld from the capture and only
    # two - `RDBMS-PASSWD char(12)` [copybooks/wssystem.cob:L139] and the frozen
    # schema's shorter `PASS-WORD`, replaced on BOTH sides by
    # `harness/dump_tables.py`'s `REDACTED_COLUMNS` because a dump is `SELECT *` - and
    # the row is fingerprinted before and after every run besides, which
    # `protocol.assert_system_record_parity` compares across the two sides over all
    # 169 columns including those two.
    for compared in ("SYSTEM-REC", "SYSDEFLT-REC"):
        assert compared in declared, (
            f"{compared!r} is menu-persisted AND measured comparable, so it must be "
            f"bounded rather than excluded: with it absent, a system-record change "
            f"this route did not intend could not be observed at all."
        )

    # THE TWO THAT REMAIN OUT, each for its own reason. SYSTOT-REC because the menu
    # sources System-Record-4 from the COBOL FLAT FILE alone
    # [general/general.cbl:L402-L404] - the RDB read is commented out at L434-L436 -
    # and rewrites it into the RDB on exit, so with only the RDB seeded that exit
    # returns sys4LD's four-spare sentinel [common/sys4LD.cbl:L368-L390] from 1.00 to
    # 0.00; measured, exactly SL4-SPARE1..4 differ. SYSFINAL-REC because nothing
    # writes it on this route at all. There is still no ignore-list, no
    # tolerance-list and no "known difference" allowance anywhere in the diff path.
    for excluded in ("SYSFINAL-REC", "SYSTOT-REC"):
        assert excluded not in declared, (
            f"{excluded!r} must not be bounded into this scenario: nothing on the "
            f"gl070 -> gl071 -> gl072 route issues a System facade verb, and the "
            f"menu-exit rewrite of keys 1, 2 and 4 happens on BOTH sides "
            f"[general/general.cbl:L656-L667], [acas_posting/cli/args.py overrewrite]. "
            f"For SYSTOT-REC the menu's flat-file-sourced key-4 rewrite would differ "
            f"for reasons the migration does not own. Its exclusion from the DECLARED "
            f"EFFECT is BOUNDING, not ignoring - every one of the 22 in-scope tables is "
            f"still compared, and the parameter row is fingerprinted besides."
        )
    # The parameter row's name reaches this stack-free test through the vocabulary, so
    # the claim cannot drift away from what the runners actually digest. It IS declared
    # here: this scenario's two silent skips leave no trace anywhere else, so every
    # bound that can be drawn is worth drawing, and the row is compared with exactly its
    # two credential cells redacted.
    assert vocabulary.parameter_table == "SYSTEM-REC"
    assert vocabulary.parameter_table in declared



# ---------------------------------------------------------------------------
#  THE PROOF OBLIGATION
#
#  Everything below needs the harness Compose stack, and reaches it through the `parity`
#  fixture, which reaches it through `protocol`, which applies the skip guard. So a host
#  with no Docker, no MariaDB or no built GnuCOBOL oracle SKIPS with a precise reason
#  naming every missing precondition, and COLLECTION SUCCEEDS EITHER WAY.
# ---------------------------------------------------------------------------


@pytest.mark.database
@pytest.mark.oracle
def test_mixed_accepted_rejected_state_parity(parity: object, harness: object) -> None:
    """THE HEADLINE - an EMPTY ordering-normalised diff for `mixed_accepted_rejected`.

    Agent Action Plan section 0.8.5, criterion 1: seed identically, run the compiled
    cycle, dump the affected tables ordering-normalised, reset, run the Python cycle,
    dump again - and the diff MUST BE EMPTY. This body contains only the verdict,
    deliberately:
    every stage and every guard happened in the fixture, so a harness fault is a pytest
    ERROR and what is left here is a genuine behavioural difference, which is a pytest
    FAILURE. The two can never be confused.

    FOR THIS SCENARIO AN EMPTY DIFF PROVES THREE THINGS AT ONCE, and the third is the
    one no other scenario can reach: that the postable transactions produced identical
    `GLLEDGER-REC` balances and identical `GLBATCH-REC` stamping; that the skipped
    transactions produced identically NOTHING - no ledger movement, no batch stamp, no
    row anywhere; and that the skipped transactions DID NOT SHIFT THE SEQUENTIAL NOMINAL
    CURSOR [general/gl072.cbl:L405-L408], because if they had, the survivors' balances
    would have landed in the wrong accounts and the first claim would have failed.

    THE REPORT IS SURFACED ON FAILURE, NOT SUMMARISED. `harness/diff_states.py`'s own
    `render` is the deterministic report and returns THE EMPTY STRING when the two trees
    are identical, so putting it in the message costs nothing on a pass and gives every
    finding on a failure. A non-empty diff is a real behavioural difference and never an
    artefact of the comparison (Agent Action Plan section 0.6.6), so it is interrogated
    against the compiled oracle and recorded in
    `docs/migration/ambiguity-resolutions.md`; the verdict itself belongs in
    `docs/migration/scenario-diff-evidence.md`.

    Args:
        parity: The completed ten-stage run.
        harness: The three harness modules, for `render`, reached through conftest.
    """
    assert parity.is_empty, (
        f"THE PYTHON CYCLE DID NOT REPRODUCE THE COMPILED COBOL for {SCENARIO}: "
        f"{parity.tree.total_differences} finding(s) across "
        f"{len(parity.tree.differing)} of {len(parity.tables)} bounded table(s). An "
        f"empty ordering-normalised diff is the only pass condition (Agent Action Plan "
        f"section 0.8.5), and a non-empty one is a real behavioural difference rather "
        f"than an artefact of the comparison (section 0.6.6): the schema's tables all "
        f"have a single-column primary key, no secondary index, no TIMESTAMP and no "
        f"AUTO_INCREMENT, so the dump order is total and stable.\n"
        f"{parity.diagnose()}\n"
        f"{parity.describe()}"
    )

    #  AND THE PASS IS WHAT A PASS LOOKS LIKE, on THIS run's real trees. The exit
    #  contract itself is exercised on synthetic trees by
    #  `test_diff_exit_contract_is_honoured`, which needs no stack; these assertions are
    #  about the run that just happened, and they belong here because this is the test
    #  that owns it.
    diff_states = harness.diff_states
    status = parity.outcome.result.returncode
    assert status in {diff_states.EX_IDENTICAL, diff_states.EX_DIFFERENT}, (
        f"stage 10 exited {status}, which is neither 0 nor 1. Exit "
        f"{diff_states.EX_ERROR} means THE COMPARISON COULD NOT BE PERFORMED and is "
        f"mapped to a harness fault - a pytest ERROR - before this test runs, so "
        f"seeing it here would mean the mapping had been bypassed and a non-comparison "
        f"was about to be read as a verdict."
    )
    assert (status == diff_states.EX_IDENTICAL) is parity.is_empty, (
        f"stage 10 exited {status} while its TreeDiff reports "
        f"is_empty={parity.is_empty} ({parity.tree.total_differences} finding(s)). "
        f"Both views come from the same diff_trees over the same two trees, so a "
        f"disagreement means the trees changed between two reads and NEITHER view can "
        f"be trusted."
    )
    rendered = parity.diagnose()
    assert (rendered == "") is parity.is_empty, (
        f"`render` must return the EMPTY STRING exactly when the trees are identical "
        f"(Agent Action Plan section 0.8.5); is_empty={parity.is_empty} and it "
        f"returned {len(rendered)} character(s)."
    )
    report = parity.outcome.report
    assert report.is_file(), (
        f"the report {report} was not written. It is written on EVERY path, and its "
        f"presence is what distinguishes 'compared, and identical' from 'never "
        f"compared' - an absent file says nothing at all, so the per-scenario evidence "
        f"in docs/migration/scenario-diff-evidence.md would have nothing to cite."
    )
    if parity.is_empty:
        assert report.stat().st_size == 0, (
            f"the trees are identical, so {report} must be ZERO BYTES; it holds "
            f"{report.stat().st_size} byte(s). A passing comparison writes no "
            f"findings, and a banner in the report file would make an empty diff "
            f"indistinguishable from a small one."
        )
        assert parity.outcome.result.stdout == "", (
            f"the trees are identical, so stage 10 must print NOT ONE BYTE on stdout; "
            f"it printed {parity.outcome.result.stdout!r}. The pass condition is an "
            f"empty diff, and an empty diff is announced by silence."
        )


@pytest.mark.database
@pytest.mark.oracle
def test_a13_non_numeric_batch_number_skipped_silently(
    parity: object, normalized_dumps: object, harness: object
) -> None:
    """A-13, SKIP (a) - `if post-batch not numeric / go to loop.` LOCKED.

    [general/gl072.cbl:L291-L292] verbatim:

        L291       if       post-batch  not numeric
        L292                go to  loop.

    Agent Action Plan section 0.6.5, verbatim: "Both are silent - no message, no
    counter, no trace. The Python equivalent must be equally silent; adding a warning
    would be an added behavior." SO THIS TEST ASSERTS NO WARNING, NO COUNTER AND NO LOG
    LINE. Demanding one would be demanding an added behaviour, which R-3 forbids and R-4
    makes a failure - and it would additionally be observable in a log a reader might
    diff.

    WHAT THIS TEST DOES NOT PROVE, STATED BEFORE WHAT IT DOES. IT DOES NOT PROVE THE
    BRANCH EXECUTED. `post-batch pic 9(5)` [general/gl072.cbl:L111] is filled by gl070 at
    [general/gl070.cbl:L495] from a group that the frozen schema holds as ONE NUMERIC
    column, `POST-KEY bigint(10) unsigned` [mysql/ACASDB.sql:L156], carried as
    `HV-POST-KEY PIC 9(18) COMP` [common/glpostingMT.cbl:L283] and moved in and out as a
    group [common/glpostingMT.cbl:L1054], [common/glpostingMT.cbl:L1085]. A non-numeric
    batch number therefore cannot reach the database at all through this path, and THIS
    SCENARIO'S FIXTURE DOES NOT CARRY ONE: `posting.dat` declares a single row, batch 1,
    with a numeric key. So the guard at L291-L292 is NOT TAKEN on this route, and a test
    asserting only that the two sides agree would read as a reproduction of the anomaly
    while proving nothing about it.

    WHERE THE BRANCH IS ACTUALLY DRIVEN, so that the pair of claims is complete.
    `tests/arithmetic/test_ledger_balance_accumulation.py` drives the SHIPPED
    `acas_posting/programs/gl072_transaction_update.py` with a work-file record whose
    `post-batch` is `'1234X'` - reachable because the shipped line-sequential work file
    is TEXT and `acas_posting.cobol.move.is_numeric_class` answers False for it - and
    asserts a POSITIVE WITNESS that the branch ran: the facade recorded NO batch lookup
    at all, which only the L291-L292 arm produces. It also asserts the skip left no
    effect, and that no counter was incremented. That file owns reachability; this one
    owns the end-state agreement.

    WHAT IS ASSERTED HERE, AND WHY IT IS PHRASED AS AGREEMENT. The bounded tables agree
    completely, no row exists on one side and not the other, and the source rows in
    `GLPOSTING-REC` are byte-identical across the two runs. Under R-6 that is the only
    honest end-state claim available for a guard whose taking is not observable in any
    table: it says the two cycles disposed of every record identically, whatever each
    did. THE DISCRIMINATION - that both cycles reproduced the MEASURED NO-OP rather than
    posting the batch a reader of the seed would expect them to post - is asserted by
    `test_the_run_reproduced_the_measured_no_op_rather_than_posting` below, because
    agreement alone is satisfied by two cycles that both posted.

    The arbitration is recorded in `docs/migration/ambiguity-resolutions.md` under the
    scenario file's own heading SKIP (a) AND ITS REACHABILITY, and the seed DECLARES the
    row aimed at the guard rather than tidying it away, because R-4 forbids removing the
    very data an anomaly needs.

    Args:
        parity: The completed run, for its per-table findings.
        normalized_dumps: Both sides' normalised dumps, shape already asserted.
        harness: The three harness modules, for `render`.
    """
    for table_diff in parity.tree.tables:
        assert table_diff.is_empty, (
            f"a rejected posting must leave the SAME (non-)effect on both sides, and "
            f"{table_diff.table} disagrees: {table_diff.total_differences} finding(s). "
            f"Skip (a) at [general/gl072.cbl:L291-L292] is a bare `go to loop.` - a "
            f"pure "
            f"no-op with no database effect at all - so ANY difference here means the "
            f"two "
            f"sides disposed of the same record differently, whether by skipping it on "
            f"one side and posting it on the other or the reverse.\n"
            f"{parity.diagnose()}"
        )
        # A one-sided row is the shape a rejection that left a TRACE would take, so it
        # is named separately from the value comparison rather than folded into it.
        assert not table_diff.missing_in_python and not table_diff.missing_in_cobol, (
            f"{table_diff.table} carries rows on one side only - "
            f"{len(table_diff.missing_in_python)} present for cobol and absent for "
            f"python, {len(table_diff.missing_in_cobol)} the other way. A clean "
            f"rejection creates nothing and destroys nothing, so a one-sided row means "
            f"one side recorded something about the rejection that the other did not."
        )
        assert table_diff.cobol_row_count == table_diff.python_row_count, (
            f"{table_diff.table} holds {table_diff.cobol_row_count} row(s) for cobol "
            f"and {table_diff.python_row_count} for python. A silent skip changes no "
            f"row count on either side."
        )

    # THE SOURCE ROWS SURVIVED IDENTICALLY. GLPOSTING-REC is read-only on this route -
    # the verb census in the module docstring - so the row aimed at skip (a) must come
    # back exactly as it went in, on BOTH sides. Compared side to side and never to a
    # predicted value.
    sides = tuple(harness.dump_tables.SIDES)
    postings = [normalized_dumps[side]["GLPOSTING-REC"] for side in sides]
    assert postings[0]["rows"] == postings[1]["rows"], (
        f"GLPOSTING-REC's rows differ between {sides[0]} and {sides[1]}. Nothing on "
        f"the gl070 -> gl071 -> gl072 route writes this table, so the rows aimed at "
        f"skip (a) must survive both runs untouched; a difference means one side "
        f"consumed, mutated or deleted a posting row that the other left alone."
    )
    assert postings[0]["rows"], (
        "GLPOSTING-REC came back EMPTY on both sides, so this assertion is vacuous: "
        "with no posting rows there is nothing for gl070 to explode into the work file "
        "and neither silent skip can be reached. That is a HARNESS FAULT in the seed - "
        "the scenario declares posting.dat with three kinds of row - and not a finding "
        "about the migration."
    )


@pytest.mark.database
@pytest.mark.oracle
def test_a13_we_error_999_record_skipped_silently(
    parity: object, normalized_dumps: object, column_by_key: object, harness: object
) -> None:
    """A-13, SKIP (b) - `if we-error equal 999 / go to loop.` LOCKED.

    [general/gl072.cbl:L306-L307] verbatim:

        L306       if       we-error  equal  999
        L307                go to  loop.

    and the trigger, [general/gl072.cbl:L458-L462] inside the `get-batch` SECTION at
    [general/gl072.cbl:L448], verbatim:

        L458       if       not waiting
        L459                move  999  to  we-error
        L460                move  0    to  save-batch
        L461       else
        L462                move  0    to  we-error.

    `88 Waiting value 0` sits on `Cleared-Status` [copybooks/wsbatch.cob:L29-L30], with
    `88 Processed value 1` and `88 Archived value 2` beside it
    [copybooks/wsbatch.cob:L31-L32]. BATCH B IS SEEDED WITH `Cleared-Status` = 1, so it
    is `not waiting`, so any posting referencing it would set `we-error` to 999 and
    vanish silently at L306-L307. One seeded field is the entire mechanism.

    AND ON THIS FIXTURE THE MECHANISM IS NOT FIRED, WHICH THIS TEST SAYS RATHER THAN
    IMPLIES. `get-batch` is performed only from `headings` [general/gl072.cbl:L346], and
    `headings` is reached only for a batch that has a record in the sorted work file.
    Batch B is seeded with `Items` 0 and `posting.dat` declares NO row for it, so gl072
    never performs `get-batch` for batch B, never sets the sentinel, and never reaches
    L306-L307 on this route. An earlier form of this test read as a reproduction of skip
    (b); it was an end-state agreement claim over a run in which the skip never occurred.

    WHERE THE BRANCH IS ACTUALLY DRIVEN. `tests/arithmetic/test_ledger_balance_accumulation.py`
    drives the SHIPPED `acas_posting/programs/gl072_transaction_update.py` against a
    not-waiting batch and asserts a POSITIVE WITNESS that the sentinel arm ran - the
    facade recorded the two batch lookups `[7, 7]` and NO `gl_nominal_read_next` at all,
    a signature only L306-L307 produces. It also records the measured consequence that
    the at-end `end-batch` still rewrites the held batch record, so a run that posted
    nothing still moves `GLBATCH-REC`. That file owns reachability; this one owns the
    end-state agreement, and neither claims the other's ground.

    A THIRD SILENT PATH shares the sentinel: [general/gl072.cbl:L348-L349] inside
    `headings` abandons the HEADINGS rather than the RECORD. Its disposition differs, so
    it is a third path and not a duplicate; it is named here because a reader chasing
    A-13 must find all three, and because the headings are print output with no database
    effect and therefore invisible in any dump.

    LIKE SKIP (a), NOTHING HERE ASSERTS A WARNING, A COUNTER OR A TRACE. And like skip
    (a), every claim is AGREEMENT between the two sides rather than a predicted value:
    batch B's postings must have moved no balance and left no stamp on EITHER side, and
    the way that is observed is that the `LEDGER-BALANCE` of every account and the
    `CLEARED-STATUS` and `POSTED` of every batch are identical across the two runs.

    Args:
        parity: The completed run.
        normalized_dumps: Both sides' normalised dumps.
        column_by_key: The projector, so the claim names its own columns.
        harness: The three harness modules, for `render` and for the side labels.
    """
    sides = tuple(harness.dump_tables.SIDES)

    # THE WHOLE BOUNDED STATE AGREES. This is the claim skip (b) reduces to: a record
    # abandoned at L307 touched nothing, so the end state is the end state the postable
    # records alone produce - identically on both sides.
    assert parity.is_empty, (
        f"the bounded state disagrees between the two sides, so it cannot be said that "
        f"batch B's postings were abandoned identically. {SCENARIO} exists to make "
        f"skip "
        f"(b) at [general/gl072.cbl:L306-L307] observable, and the only way a silent "
        f"skip "
        f"is observable is as an ABSENCE that matches.\n"
        f"{parity.diagnose()}"
    )

    # THE TWO STAMPED COLUMNS, PER BATCH KEY. [general/gl072.cbl:L375-L376] is the whole
    # of the batch mutation, so these two columns are where a wrongly-skipped or
    # wrongly-posted batch would show. Compared side to side; NO value is predicted,
    # because what the compiled cycle leaves on a `not waiting` batch is the
    # specification (R-6) and not something a reader may reason out.
    batch = {side: normalized_dumps[side]["GLBATCH-REC"] for side in sides}
    for column in ("CLEARED-STATUS", "POSTED"):
        left = column_by_key(batch[sides[0]], column)
        right = column_by_key(batch[sides[1]], column)
        assert left == right, (
            f"GLBATCH-REC.{column} disagrees between {sides[0]} and {sides[1]}: "
            f"{left!r} against {right!r}. [general/gl072.cbl:L375] sets CLEARED-STATUS "
            f"and [general/gl072.cbl:L376] moves run-date to POSTED, both inside "
            f"`end-batch`, so a difference here means one side stamped a batch the "
            f"other did not - which is precisely what skip (b) at "
            f"[general/gl072.cbl:L306-L307] and its trigger at "
            f"[general/gl072.cbl:L458-L459] decide."
        )

    # THE BALANCES, PER LEDGER KEY. A posting that survived on one side and was skipped
    # on the other moves a balance on one side only, so this is the second independent
    # view of the same claim.
    ledger = {side: normalized_dumps[side]["GLLEDGER-REC"] for side in sides}
    balances = [column_by_key(ledger[side], "LEDGER-BALANCE") for side in sides]
    assert balances[0] == balances[1], (
        f"GLLEDGER-REC.LEDGER-BALANCE disagrees between {sides[0]} and {sides[1]}. The "
        f"only balance mutation on this route is [general/gl072.cbl:L331] `add "
        f"post-amount to ledger-balance.`, persisted by `GL-Nominal-Rewrite` at "
        f"[general/gl072.cbl:L382], so a difference means one side accumulated a "
        f"posting the other abandoned at L307."
    )
    assert balances[0], (
        "GLLEDGER-REC came back EMPTY on both sides, so this assertion is vacuous: "
        "with no nominal accounts there is nothing for a posting to move and nothing "
        "for a skip to leave alone. That is a HARNESS FAULT in the seed - the scenario "
        "declares ledger.dat with three or more nominal accounts - and not a finding."
    )
    assert len(batch[sides[0]]["rows"]) >= 2, (
        f"GLBATCH-REC holds {len(batch[sides[0]]['rows'])} row(s). This scenario needs "
        f"at least a WAITING batch and a NOT-WAITING one in the same run, and "
        f"`batch.dat` declares exactly two - batch 1 closed and waiting with one "
        f"posting, batch 2 closed and NOT waiting with none "
        f"[copybooks/wsbatch.cob:L25-L32]. Fewer makes this file a duplicate of the "
        f"clean-batch scenario rather than a mixed one, which is a HARNESS FAULT in the "
        f"seed."
    )



@pytest.mark.database
@pytest.mark.oracle
def test_the_run_reproduced_the_measured_no_op_rather_than_posting(
    parity: object,
    normalized_dumps: object,
    protocol: object,
    scenario_loader: object,
    harness: object,
    withheld: object,
) -> None:
    """THE DISCRIMINATION, AND IT POINTS THE OPPOSITE WAY FROM INTUITION.

    WHY THIS TEST EXISTS. Every other assertion in this file is an AGREEMENT claim:
    the two sides' tables must match. Agreement is necessary and it is not sufficient,
    because TWO CYCLES THAT BOTH DID THE SAME THING AGREE PERFECTLY WHATEVER THAT THING
    WAS. This test is the one that says WHICH thing, and it names a value.

    AND THE VALUE IS "NOTHING CHANGED", WHICH IS NOT WHAT THE SEED PREDICTS. Batch 1
    is seeded `Cleared-Status` 0 - the condition name `Waiting`
    [copybooks/wsbatch.cob:L29-L30] - closed, a GL batch, with `Bcycle` equal to the
    pinned `Cyclea`, so phase two's filter [general/gl070.cbl:L460-L463] DOES select it,
    and a reader reasoning from the seed would expect `end-batch` to stamp it. THE
    COMPILED CYCLE DOES NOT. Compiled measurement recorded as `Q-9` in
    docs/migration/ambiguity-resolutions.md established that the bridge's host-variable
    never loads `HV-POST-RRN`, the table's primary key [mysql/ACASDB.sql:L169], so that
    column is stored at zero; and `A-NEW-18` records that the `POST-KEY` group move
    [common/glpostingMT.cbl:L1054] corrupts the key on the way back out
    [common/glpostingMT.cbl:L1085], leaving bytes that are not the all-`0` image. So
    `if WS-Post-Key = zero` [general/gl070.cbl:L490-L491] is FALSE and the posting is
    skipped by the SECOND disjunct, `if batch not = WS-Batch-Nos`
    [general/gl070.cbl:L492-L493] - both comparisons byte-wise, `Q-NKEY-CMP` readings 7
    and 4. The work file is empty, gl072 reads
    nothing, and the run is a no-op over all three bounded tables. The scenario declares
    `expected_table_effect: unchanged` for exactly that reason, and
    docs/migration/scenario-diff-evidence.md section 10.5 records the observed journey.

    SO THE DISCRIMINATION IS AGAINST A CYCLE THAT "FIXED" Q-9 OR `A-NEW-18`. A migrated
    cycle that loaded the RRN into the key, posted the batch and stamped it would produce a
    perfectly self-consistent database and would satisfy every agreement assertion in
    this file - and it would be a FAILURE, because a defect fixed is a failure (R-4).
    This test fails for it, and for nothing else fails. It is deliberately NOT written
    the other way round. Asserting `CLEARED-STATUS` 1 and `POSTED` = the pinned run date
    on the waiting batch - which is what the frozen statements
    [general/gl072.cbl:L375-L376] say unconditionally AND is unreachable on this fixture -
    would demand the repair rather than the reproduction, which is precisely inverted
    (R-6).

    IT ASSERTS TWO THINGS.

    ONE - NEITHER CYCLE CHANGED ANY BOUNDED TABLE, per side and independently. Both
    runners record a canonical per-table digest immediately BEFORE their dispatch and
    again immediately AFTER it, so `assert_tables_unchanged_by_run` can ask "did THIS
    cycle change this table" - a question no side-to-side diff can answer, and the
    question the scenario's declared effect is an answer to.

    TWO - BOTH BATCH ROWS ARE BYTE-IDENTICAL TO THEIR SEEDED VALUES, compared against
    `seed_records` rather than against the other side. The waiting batch's `POSTED` must
    still be 0 and its `CLEARED-STATUS` still 0; the not-waiting batch must be untouched
    too. Comparing against the SEED rather than across the sides is what makes this a
    statement about what the cycles did rather than about whether they agreed.

    WHAT IT STILL DOES NOT PROVE. It does not prove either silent skip executed; this
    fixture cannot reach them, for the reasons the module docstring gives, and
    `tests/arithmetic/test_ledger_balance_accumulation.py` drives both branches against
    the shipped program instead.

    Args:
        parity: The completed, guarded run. Its artifact layout carries the pre-run and
            post-run state records this test reads.
        normalized_dumps: Both sides' normalised dumps, shape already asserted.
        protocol: The protocol bundle, for the per-side pre/post comparison.
        scenario_loader: The definition, for the seeded values claim two compares to.
        harness: The three harness modules, for the side labels and for `render`.
        withheld: The value-free stand-in for a dumped cell, so a failure message can
            name a column without reproducing an accounting figure.

    Raises:
        Skipped: The Compose stack is unusable.
        AssertionError: A cycle changed a bounded table, or a batch row moved off its
            seeded value - either of which means the migrated cycle posted where the
            compiled one does not.
    """
    sides = tuple(harness.dump_tables.SIDES)

    # ---- ONE: neither cycle changed any DECLARED table --------------------------
    #  The pre/post record covers the scenario's own `affected_tables' plus the
    #  menu-persisted parameter row, and nothing else, so that is the set on which
    #  "unchanged by THIS run" can be established. `parity.tables' is the wider
    #  22-table COMPARISON bound, asserted side-to-side elsewhere in this file; asking
    #  the pre/post record about a table it never fingerprinted reports an absent
    #  record rather than an unchanged table.
    protocol.assert_tables_unchanged_by_run(
        parity, unchanged=tuple(scenario_loader(SCENARIO)["affected_tables"])
    )

    # ---- TWO: both batch rows still carry their seeded values --------------------
    records = scenario_loader(SCENARIO)["seed_records"]
    batches = records["batch.dat"]

    def batch_key(row: object) -> int:
        """Compose one seeded batch row's `BATCH-KEY`.

        `03 WS-Batch-Key` is `05 WS-Ledger pic 9` followed by `05 WS-Batch-Nos pic 9(5)`
        and is redefined as `WS-Batch-Key9 pic 9(6)` [copybooks/wsbatch.cob:L14-L21]; the
        bridge moves that redefinition, an ELEMENTARY numeric item, into
        `HV-BATCH-KEY PIC 9(08) COMP` [common/glbatchMT.cbl:L1069]. So the SQL key is the
        two components concatenated at their declared widths and read as a number - which
        is why this composition is safe here where `POST-KEY` is not (`Q-9`).

        Args:
            row: One `batch.dat` record from `seed_records`.

        Returns:
            The `BATCH-KEY` value the dump will carry for that row.
        """
        return int(f"{int(row['WS-Ledger']):01d}{int(row['WS-Batch-Nos']):05d}")

    integer_columns = (
        ("ITEMS", "Items"),
        ("BATCH-STATUS", "Batch-Status"),
        ("CLEARED-STATUS", "Cleared-Status"),
        ("BCYCLE", "Bcycle"),
        ("ENTERED", "Entered"),
        ("PROOFED", "Proofed"),
        ("POSTED", "Posted"),
        ("STORED", "Stored"),
    )

    for side in sides:
        dump = normalized_dumps[side][BATCH_TABLE]
        columns = list(dump["columns"])
        key_index = columns.index(dump["primary_key"])
        indexed = {int(row[key_index]): row for row in dump["rows"]}

        assert len(indexed) == len(batches), (
            f"the {side} dump of `{BATCH_TABLE}` carries {len(indexed)} row(s) and the "
            f"seed declares {len(batches)}. Nothing on the gl070 -> gl071 -> gl072 route "
            f"writes or deletes a batch - the four verbs are Open, Read-Next, Rewrite "
            f"and Close - so the count cannot legally move."
        )

        for seeded in batches:
            key = batch_key(seeded)
            assert key in indexed, (
                f"the {side} dump of `{BATCH_TABLE}` carries no row for BATCH-KEY "
                f"{key}. Keys present: {sorted(indexed)!r}."
            )
            observed = dict(zip(columns, indexed[key], strict=True))
            waiting = int(seeded["Cleared-Status"]) == 0
            role = "WAITING" if waiting else "NOT-WAITING"
            for column, field in integer_columns:
                assert int(observed[column]) == int(seeded[field]), (
                    f"the {side} cycle changed `{BATCH_TABLE}`.`{column}` on the {role} "
                    f"batch {key}: the seed declares {seeded[field]!r} and the dump "
                    f"carries {withheld(observed[column], column=column)}.\n"
                    f"  THE MEASURED BEHAVIOUR IS THAT NEITHER BATCH MOVES. The bridge "
                    f"never loads `HV-POST-RRN`, the table's primary key (ambiguity "
                    f"`Q-9`), and the `POST-KEY` group move corrupts the key on the way "
                    f"back out (anomaly `A-NEW-18`), so the read returns bytes that are "
                    f"NOT the all-`0` image: `if WS-Post-Key = zero` "
                    f"[general/gl070.cbl:L490-L491] is FALSE and the posting is skipped "
                    f"by `if batch not = WS-Batch-Nos` [general/gl070.cbl:L492-L493] "
                    f"instead (`Q-NKEY-CMP` readings 7 and 4). The work file is "
                    f"empty and gl072's `end-batch` [general/gl072.cbl:L372-L377] is "
                    f"never reached for either batch.\n"
                    f"  IF `CLEARED-STATUS` IS NOW 1 AND `POSTED` NOW HOLDS THE PINNED "
                    f"RUN DATE, THE MIGRATED CYCLE HAS FIXED `Q-9` OR `A-NEW-18` - it "
                    f"loaded the RRN, or rejoined the key without the byte move, "
                    f"found the posting and posted the batch. That is a defect FIXED, "
                    f"and a defect fixed is a failure (R-4). Reproduce the frozen "
                    f"host-variable load and the frozen round trip instead, and if the "
                    f"oracle's own behaviour has changed, re-measure it and update "
                    f"`Q-9`, `A-NEW-18`, `Q-NKEY-CMP`, this scenario's "
                    f"`expected_table_effect` and "
                    f"docs/migration/scenario-diff-evidence.md together.\n"
                    f"{parity.diagnose()}"
                )
            assert observed["DESCRIPTION"].rstrip() == seeded["Description"].rstrip(), (
                f"the {side} cycle changed `{BATCH_TABLE}`.`DESCRIPTION` on the {role} "
                f"batch {key}: the seed declares {seeded['Description']!r} and the dump "
                f"carries {withheld(observed['DESCRIPTION'], column='DESCRIPTION')}. "
                f"Nothing on this route writes that "
                f"column at all - `end-batch` touches `cleared-status` and `posted` "
                f"only [general/gl072.cbl:L375-L376]."
            )


@pytest.mark.database
@pytest.mark.oracle
def test_skipped_postings_do_not_perturb_sequential_nominal_cursor(
    parity: object, normalized_dumps: object, column_by_key: object, harness: object
) -> None:
    """THE A-13 / A-14 INTERACTION - the highest-value assertion in this file.

    gl072 does NOT locate the nominal-ledger account by an indexed read.
    [general/gl072.cbl:L405-L408] verbatim:

        L405       move     post-ledger  to  WS-Ledger-Key.
        L407       if       read-ledger not = "R"
        L408                perform  GL-Nominal-Read-Next.

    It lands on the correct account ONLY because gl071 has already emitted the stream in
    nominal-key order. [general/gl071.cbl:L172-L178] verbatim:

        L172       sort     sort-trans
        L173                on ascending key sort-batch
        L174                                 sort-ac
        L175                                 sort-pc
        L176                                 sort-post
        L177                using  pre-trans
        L178                giving post-trans.

    A SKIPPED POSTING IS SKIPPED AFTER THE SORT HAS PLACED IT IN THAT STREAM. Both skips
    are a bare `go to loop.` taken BEFORE `new-account` is ever performed, so neither
    reaches L408 and neither advances the cursor. THEREFORE A SKIPPED POSTING MUST NOT
    PERTURB THE ACCOUNT POSITIONS OF THE POSTINGS THAT FOLLOW IT - and the scenario
    seeds the skippable rows INTERLEAVED between postable rows that target DIFFERENT
    nominal accounts, precisely so that an implementation which advanced the cursor on a
    skip would post the survivors into the WRONG accounts.

    THAT IS THE PROPERTY THIS TEST OWNS, and it is invisible in any single-transaction
    test: with one account, or with the skips at the end of the stream, a perturbed
    cursor produces the same answer as a correct one. A-14 is exactly this dependency,
    and it is what turns a sorting detail into a correctness requirement: perturb the
    sort - its stability, its key composition, its tie-break - and the program SILENTLY
    POSTS TO
    THE
    WRONG ACCOUNT with no error and no diagnostic.

    THE SEQUENTIAL READ MUST NEVER BE "OPTIMISED" INTO AN INDEXED ONE. Agent Action Plan
    section 0.8.4: "Any performance work is therefore out of scope by construction, not
    merely unrequested." An indexed read by `WS-Ledger-Key` would obviously be faster,
    would look like an improvement, and would quietly delete the only reason this
    scenario has a third thing to prove.

    Note that `if read-ledger not = "R"` appears AGAIN at [general/gl072.cbl:L410-L411],
    AFTER the read, where it zeroes `tot-dr` and `tot-cr`. Different test, different
    consequence; the Agent Action Plan's L410-L412 citation points at that post-read
    block rather than at the read itself.

    WHAT READING DOES NOT SETTLE, AND WHAT THE ORACLE DID.
    [general/gl071.cbl:L172-L178] declares no `with duplicates in order` phrase, so the
    compiled tie order for two records carrying an identical `(sort-batch, sort-ac,
    sort-pc, sort-post)` is whatever GnuCOBOL 3.2 chooses, while the Python sort is
    stable unconditionally. Under R-6 that was a question for the oracle, and the
    oracle has ANSWERED it: `Q-SORT-TIE-ORDER` in
    `docs/migration/ambiguity-resolutions.md` is `RESOLVED BY ORACLE` (2026-08-07) - the
    compiled sort PRESERVES INPUT ORDER for equal keys, which is exactly what an
    unconditionally stable sort produces. This test still does not pre-judge the
    outcome: it asserts that the two sides AGREE, which is the observable that would
    catch a disagreement about ties as readily as one about skips. A measured answer is
    a reason to expect agreement, never a substitute for observing it.

    NOTHING IS RECOMPUTED HERE. No balance is recalculated in Python, no debit total is
    compared against a credit total, and no arithmetic is performed at all - that is
    arithmetic-tier work and belongs to `tests/arithmetic/`, where
    `test_ledger_balance_accumulation.py` owns A-14's computed side. What is compared is
    WHICH ACCOUNT ENDED UP WITH WHICH BALANCE, on both sides.

    Args:
        parity: The completed run.
        normalized_dumps: Both sides' normalised dumps.
        column_by_key: The projector, keyed on `LEDGER-KEY`.
        harness: The three harness modules, for the side labels and for `render`.
    """
    sides = tuple(harness.dump_tables.SIDES)
    ledger = {side: normalized_dumps[side]["GLLEDGER-REC"] for side in sides}

    # THE VACUITY GUARD, DEFENDED EXPLICITLY. With fewer than three nominal accounts the
    # interleaving cannot span "different accounts" and a perturbed cursor could land on
    # the right account by luck, so the assertion below would pass while proving
    # nothing. The scenario's seed contract declares THREE OR MORE for exactly this
    # reason.
    for side in sides:
        assert ledger[side]["row_count"] >= 3, (
            f"GLLEDGER-REC holds {ledger[side]['row_count']} row(s) on the {side} "
            f"side, and this assertion needs at least three. The whole claim is that a "
            f"skipped posting did not shift the cursor onto a NEIGHBOURING account, "
            f"and with one or two accounts a shifted cursor can produce the correct "
            f"answer by luck. That is a HARNESS FAULT in the seed - the scenario "
            f"declares ledger.dat with three or more nominal accounts - and not a "
            f"finding about the migration."
        )

    # THE KEY SETS MUST MATCH FIRST. Nothing on this route inserts or deletes a nominal
    # account - the only nominal verbs are Open, Read-Next, Rewrite and Close - so a
    # one-sided key would mean one side had walked the ledger file differently.
    keys = [tuple(column_by_key(ledger[side], "LEDGER-BALANCE")) for side in sides]
    assert keys[0] == keys[1], (
        f"GLLEDGER-REC's LEDGER-KEY set differs between {sides[0]} and {sides[1]}: "
        f"{keys[0]!r} against {keys[1]!r}. gl072 issues only GL-Nominal-Open, "
        f"GL-Nominal-Read-Next, GL-Nominal-Rewrite and GL-Nominal-Close "
        f"[general/gl072.cbl:L274], [general/gl072.cbl:L408], "
        f"[general/gl072.cbl:L382], [general/gl072.cbl:L442] - no write and no delete "
        f"- so neither side may add or lose an account."
    )
    assert keys[0] == tuple(sorted(keys[0])), (
        f"GLLEDGER-REC's rows are not in primary-key-ascending order: {keys[0]!r}. The "
        f"dump is `SELECT * ORDER BY LEDGER-KEY` [mysql/ACASDB.sql:L134] and the "
        f"cursor argument this test makes depends on that order being total and "
        f"stable."
    )

    # THE CLAIM ITSELF, PER ACCOUNT. If a skipped posting had advanced the cursor on one
    # side, at least two accounts would differ - the one that wrongly received a posting
    # and the one that wrongly did not - so the per-key comparison localises the fault
    # to the accounts involved instead of reporting one aggregate.
    balances = [column_by_key(ledger[side], "LEDGER-BALANCE") for side in sides]
    perturbed = sorted(
        key for key in balances[0] if balances[0][key] != balances[1][key]
    )
    assert not perturbed, (
        f"THE SEQUENTIAL NOMINAL CURSOR WAS PERTURBED. "
        f"GLLEDGER-REC.LEDGER-BALANCE differs on {len(perturbed)} account(s): "
        f"{perturbed!r}. gl072 finds each account with a SEQUENTIAL read "
        f"[general/gl072.cbl:L407-L408] and is correct only because gl071 sorted the "
        f"stream into nominal-key order [general/gl071.cbl:L172-L178]. A skip at "
        f"[general/gl072.cbl:L291-L292] or [general/gl072.cbl:L306-L307] happens "
        f"BEFORE "
        f"`new-account` runs, so it must not advance the cursor; a balance landing on "
        f"a "
        f"neighbouring account is anomaly A-14 realised, and the sequential read must "
        f"NEVER be replaced by an indexed one to make this pass. If the disagreement "
        f"is "
        f"about a SORT TIE rather than a skip, that is `Q-SORT-TIE-ORDER` in "
        f"docs/migration/ambiguity-resolutions.md, which the oracle ANSWERED: the "
        f"compiled sort preserves input order for equal keys, so a tie should NOT "
        f"produce a difference here, so one that appears is a real divergence and not an "
        f"open question.\n{parity.diagnose()}"
    )


@pytest.mark.database
@pytest.mark.oracle
def test_batch_stamp_columns_agree_on_both_sides(
    parity: object, normalized_dumps: object, column_by_key: object, harness: object
) -> None:
    """`end-batch`'s two stamp columns AGREE ON BOTH SIDES.

    RENAMED, BECAUSE THE OLD NAME ASSERTED SOMETHING MEASUREMENT REFUTED. This test
    was called `test_accepted_batch_is_stamped_cleared_and_posted` and opened by
    saying "`end-batch` stamps the accepted batch". NO BATCH IS STAMPED BY THIS RUN.
    The body was always framed as agreement and so always passed, which is exactly the
    trap: a reader took the name for a finding. What the run actually does, measured,
    is under ANOMALY N-KEY in `harness/scenarios/mixed_accepted_rejected.yaml`, and the
    unchanged-relative-to-the-seed facts are asserted by
    `test_every_bounded_row_is_unchanged_relative_to_the_declared_seed` below. This
    test makes its agreement claim, which is worth making, and claims no stamp.

    [general/gl072.cbl:L372-L377] verbatim:

        L372  end-batch.
        L375       move     1  to  cleared-status.
        L376       move     run-date  to  posted.
        L377       perform  GL-Batch-Rewrite.

    ACCOUNT-LEVEL TOTALS CLOSE BEFORE BATCH-LEVEL TOTALS - `perform end-account` then
    `perform end-batch`, at [general/gl072.cbl:L287-L288] on the at-end path and again
    at [general/gl072.cbl:L297-L298] on the batch-change path. "Inverting them would
    produce a batch marked posted with an unclosed final account", which is why the
    order is stated here even though the observable is the stamp rather than the order.

    FRAMED AS AGREEMENT, NOT AS A VALUE - and the measurement vindicates the framing
    rather than excusing it. This test does NOT assert that `CLEARED-STATUS` is 1 or
    that `POSTED` equals the pinned run date, and it is now known that neither is true:
    the run leaves both columns exactly as seeded. It asserts that whatever the
    compiled cycle wrote, the Python cycle wrote the same - which is the R-4 and R-6
    framing and the only one available: the maintainer records that he has not worked
    with General at all since it was migrated to the current compiler
    [README.TXT:L50-L53], while reporting the other ledgers as tested, so this is the
    least exercised ledger in the system and no expected value for it may be derived
    from documentation or from reasoning about intent. If a batch is stamped that a
    reader would not expect, THE SURPRISE IS THE
    SPECIFICATION.

    WHY THE STAMP IS COMPARABLE AT ALL. `POSTED` is `int(8) unsigned`
    [mysql/ACASDB.sql:L88] from `05 Posted binary-long.` [copybooks/wsbatch.cob:L38], so
    L376 writes an INTEGER day number and normalisation job 3 - the two- versus
    four-digit date text forms, under an explicit five-column allow-list that this
    column is not on - correctly leaves it alone. It is comparable because the clock is
    pinned to a single value at the boundary [copybooks/wssystem.cob:L67], and for no
    other reason.

    A-15 is in the background of every `GLBATCH-REC` assertion:
    [copybooks/wsbatch.cob:L7-L9] records the maintainer's own 96-versus-98
    contradiction, and whether the declared length or the field sum governs the record
    actually read affects the alignment of the trailing fields. `Q-4` in
    `docs/migration/ambiguity-resolutions.md` is `RESOLVED BY ORACLE` (2026-08-07) and
    the answer is NEITHER: both copies measure 96 and the 98 in the note is false under
    GnuCOBOL 3.2.0, so A-15 carries `REPRODUCED -- VALUE MEASURED` in
    `docs/migration/anomaly-log.md`. The measurement says the alignment does not shift;
    it does not repair the contradictory note, which stays as written (R-4). If it ever
    did bite it would bite the column values, and this comparison is where it would
    surface -- which is why the comparison is kept rather than dropped as settled.

    Args:
        parity: The completed run.
        normalized_dumps: Both sides' normalised dumps.
        column_by_key: The projector, keyed on `BATCH-KEY`.
        harness: The three harness modules, for the side labels and for `render`.
    """
    sides = tuple(harness.dump_tables.SIDES)
    batch = {side: normalized_dumps[side]["GLBATCH-REC"] for side in sides}

    for column in ("CLEARED-STATUS", "POSTED"):
        left = column_by_key(batch[sides[0]], column)
        right = column_by_key(batch[sides[1]], column)
        differing = sorted(key for key in left if left[key] != right[key])
        assert not differing, (
            f"GLBATCH-REC.{column} differs on {len(differing)} batch key(s): "
            f"{differing!r}. `end-batch` is the whole of the batch mutation - "
            f"[general/gl072.cbl:L375] sets CLEARED-STATUS, [general/gl072.cbl:L376] "
            f"moves run-date to POSTED and [general/gl072.cbl:L377] rewrites the row - "
            f"so the two sides stamped different batches, or stamped the same batch "
            f"differently. The claim is AGREEMENT and not a particular value: whatever "
            f"the compiled cycle left is the specification (R-6), including if it "
            f"surprises a reader.\n{parity.diagnose()}"
        )
        assert left, (
            f"GLBATCH-REC came back with no rows, so the {column} comparison is "
            f"vacuous. Without a seeded batch there is nothing for gl070's two passes "
            f"to select [general/gl070.cbl:L312-L313], [general/gl070.cbl:L460-L463] "
            f"and nothing for `end-batch` to stamp. That is a HARNESS FAULT in the "
            f"seed."
        )

    # The batch rows must be key-aligned before the per-column claims mean anything, and
    # nothing on this route writes or deletes a batch - GL-Batch-Open, -Read-Next,
    # -Rewrite and -Close are the only four verbs [general/gl072.cbl:L276],
    # [general/gl072.cbl:L454], [general/gl072.cbl:L377], [general/gl072.cbl:L441].
    key_sets = [tuple(column_by_key(batch[side], "CLEARED-STATUS")) for side in sides]
    assert key_sets[0] == key_sets[1], (
        f"GLBATCH-REC's BATCH-KEY set differs between {sides[0]} and {sides[1]}: "
        f"{key_sets[0]!r} against {key_sets[1]!r}. The route issues no batch write and "
        f"no batch delete, so neither side may add or lose a batch."
    )


@pytest.mark.database
@pytest.mark.oracle
def test_unwaiting_batch_is_not_stamped(
    parity: object, normalized_dumps: object, harness: object
) -> None:
    """The NOT-WAITING batch's row agrees on both sides - WHATEVER the oracle left on
    it.

    Batch B is seeded with `Cleared-Status` NOT zero, so `88 Waiting`
    [copybooks/wsbatch.cob:L29-L30] is false for it and `88 Processed value 1` or `88
    Archived value 2` [copybooks/wsbatch.cob:L31-L32] is true. `get-batch` then takes
    the sentinel branch, [general/gl072.cbl:L458-L460]:

        L458       if       not waiting
        L459                move  999  to  we-error
        L460                move  0    to  save-batch

    THE VALUE IS NOT PREDICTED, AND DELIBERATELY SO. L459 sets the sentinel that skips
    the record at [general/gl072.cbl:L306-L307], but L460 ALSO zeroes `save-batch`,
    which is the variable the batch-change test at [general/gl072.cbl:L294-L296] and the
    first-batch test at [general/gl072.cbl:L302-L304] both read - and `save-batch` zero
    makes L302's condition true again on the very next record, which performs `headings
    through headings-end` and therefore `get-batch` again [general/gl072.cbl:L346]. What
    that interaction leaves on batch B's row, and whether `end-batch` is ever reached
    for it at all, is a question only the compiled program answers. Under R-6 it is
    recorded in `docs/migration/ambiguity-resolutions.md` rather than settled by
    reading, and the General Ledger caveat [README.TXT:L50-L53] makes reasoning about
    intent inadmissible here in any case.

    SO THE ASSERTION IS AGREEMENT ON THE WHOLE ROW, EVERY COLUMN. That is strictly
    stronger than checking two stamped columns and strictly weaker than predicting a
    value, which is exactly the right strength: if the outcome is surprising, THAT IS
    THE SPECIFICATION and it is reproduced rather than corrected (R-4).

    A-15 applies with full force to this row too: the declared-length contradiction at
    [copybooks/wsbatch.cob:L7-L9], carried as `Q-4`, would show up as a trailing-field
    misalignment and a whole-row comparison is what would catch it.

    Args:
        parity: The completed run.
        normalized_dumps: Both sides' normalised dumps.
        harness: The three harness modules, for the side labels and for `render`.
    """
    sides = tuple(harness.dump_tables.SIDES)
    batch = [normalized_dumps[side]["GLBATCH-REC"] for side in sides]

    # THE COLUMN LISTS FIRST. Rows are lists of values in schema ordinal order, so a
    # column-list disagreement would make the row comparison below meaningless rather
    # than false.
    assert list(batch[0]["columns"]) == list(batch[1]["columns"]), (
        f"GLBATCH-REC's column list differs between {sides[0]} and {sides[1]}: "
        f"{list(batch[0]['columns'])!r} against {list(batch[1]['columns'])!r}. Rows "
        f"are POSITIONAL, so two different column lists have no meaningful alignment "
        f"at all."
    )
    assert batch[0]["primary_key"] == batch[1]["primary_key"], (
        f"GLBATCH-REC's declared primary key differs between the two sides: "
        f"{batch[0]['primary_key']!r} against {batch[1]['primary_key']!r}. Rows are "
        f"aligned by primary-key VALUE, so the two sides must agree on the column."
    )

    # EVERY ROW, EVERY COLUMN. The dumps are primary-key-ascending on both sides, so the
    # positional comparison is a key-aligned one; `load_dump` has already refused a
    # duplicate key, so no row can hide behind another.
    assert batch[0]["rows"] == batch[1]["rows"], (
        f"GLBATCH-REC's rows differ between {sides[0]} and {sides[1]}. The NOT-WAITING "
        f"batch is the one this assertion is about: [general/gl072.cbl:L458-L460] sets "
        f"the 999 sentinel AND zeroes save-batch, and what that leaves on its row is "
        f"an "
        f"ORACLE QUESTION recorded in docs/migration/ambiguity-resolutions.md - so the "
        f"claim is that the two sides agree, never that a particular value appears. A "
        f"surprising value is the specification (R-6) and is reproduced, not corrected "
        f"(R-4); a DISAGREEMENT is a real behavioural difference. Note A-15, the "
        f"declared-length contradiction at [copybooks/wsbatch.cob:L7-L9] carried as "
        f"Q-4, "
        f"which would surface here as a trailing-field "
        f"misalignment.\n{parity.diagnose()}"
    )
    assert batch[0]["row_count"] == len(batch[0]["rows"]), (
        f"GLBATCH-REC declares row_count {batch[0]['row_count']} and carries "
        f"{len(batch[0]['rows'])} row(s) on the {sides[0]} side."
    )


# ---------------------------------------------------------------------------
#  THE SEED-RELATIVE PROBE  -  what distinguishes a skip from a posting
#
#  EVERY OTHER ASSERTION IN THIS FILE COMPARES THE TWO SIDES TO EACH OTHER, AND
#  THAT IS NOT ENOUGH ON ITS OWN. Two implementations that both do nothing agree
#  perfectly, so side-to-side agreement cannot tell "correctly skipped" from "never
#  posted anything". The three tests below compare each side to THE DECLARED SEED
#  instead, read out of the scenario file itself, which is the only reference that
#  can make the distinction. They are the probe facts the run's absence needs.
#
#  WHY THE EXPECTED ANSWER IS "UNCHANGED", AND WHY THAT IS NOT A WEAK CLAIM. Under
#  ANOMALY N-KEY - derived and measured in the scenario file, and locked against the
#  migrated code by tests/arithmetic/test_comp_binary.py
#  section 19 - the POST-KEY a seeded posting row carries cannot be decoded back
#  into its batch number, so gl070 discards the row at
#  [general/gl070.cbl:L492-L493] and pretrans.tmp is left ZERO BYTES long. Nothing
#  reaches gl072, nothing posts, and every bounded row must therefore still hold its
#  seeded value. Asserting that EXACTLY is what turns an unexplained empty diff into
#  a measured statement about where the run stopped.
# ---------------------------------------------------------------------------


def _declared_batch_rows(definition: object) -> dict[int, dict[str, str]]:
    """Index the scenario's declared `batch.dat` records by their composed BATCH-KEY.

    `WS-Batch-Key` is `WS-Ledger pic 9` followed by `WS-Batch-Nos pic 9(5)`
    [copybooks/wsbatch.cob:L14-L19], redefined as `WS-Batch-Key9 pic 9(6)`
    [copybooks/wsbatch.cob:L20-L21], and that six-digit composition is what the schema
    holds as `BATCH-KEY`. Composed here rather than hard-coded so that changing a
    declared batch number cannot leave this file asserting against a stale key.

    Args:
        definition: The parsed scenario document.

    Returns:
        `{BATCH-KEY: declared field mapping}`.
    """
    rows = definition["seed_records"]["batch.dat"]
    return {
        int(f"{int(row['WS-Ledger'])}{int(row['WS-Batch-Nos']):05d}"): row
        for row in rows
    }


@pytest.mark.database
@pytest.mark.oracle
def test_no_work_record_is_emitted_so_nothing_can_post(
    parity: object, normalized_dumps: object, column_by_key: object, harness: object,
    scenario_loader: object,
    withheld: object,
) -> None:
    """ANOMALY N-KEY's consequence, asserted against the seed: NO BATCH IS STAMPED.

    THE DISTINGUISHING FACT. `end-batch` is the only writer of `CLEARED-STATUS` and
    `POSTED` [general/gl072.cbl:L375-L377], and it is reached only for a batch that a
    work record named. If a work record had been emitted for the waiting batch, that
    batch's `CLEARED-STATUS` would be 1 and its `POSTED` would be the pinned run date.
    Both columns are asserted here to hold THEIR SEEDED VALUES on both sides, which
    says the work file was empty far more precisely than an empty diff can.

    THE SEEDED VALUES ARE READ FROM THE SCENARIO FILE, not restated. So a future edit
    that changes a declared value cannot leave this test passing against the old one,
    and a future change that makes the cycle actually post will fail HERE - loudly,
    naming the column - instead of silently turning the file's narrative false again.

    Args:
        parity: The completed ten-stage run, for the failure report.
        normalized_dumps: Both sides' normalised dumps.
        column_by_key: The projector, keyed on `BATCH-KEY`.
        harness: The harness modules, for the side labels and `render`.
        scenario_loader: Loads the parsed scenario document, for the declared seed.
        withheld: The value-free stand-in for a dumped cell, so a failure message can
            name a column without reproducing an accounting figure.
    """
    declared = _declared_batch_rows(scenario_loader(SCENARIO))
    assert declared, "the scenario declares no batch.dat records - a HARNESS FAULT"

    for side in harness.dump_tables.SIDES:
        dump = normalized_dumps[side]["GLBATCH-REC"]
        for column, field_name in (
            ("CLEARED-STATUS", "Cleared-Status"),
            ("POSTED", "Posted"),
        ):
            observed = column_by_key(dump, column)
            assert set(observed) == set(declared), (
                f"GLBATCH-REC on the {side} side carries keys {sorted(observed)!r} "
                f"and the scenario declares {sorted(declared)!r}. The route issues no "
                f"batch write and no batch delete, so the key set must be the seed's."
            )
            for key, seeded_row in declared.items():
                expected = int(seeded_row[field_name])
                assert int(observed[key]) == expected, (
                    f"GLBATCH-REC.{column} for BATCH-KEY {key} is "
                    f"{withheld(observed[key], column=column)} on the {side} side and "
                    f"the scenario seeded "
                    f"{expected!r}. A CHANGED value means gl072 reached `end-batch` "
                    f"for a work record [general/gl072.cbl:L375-L377] - which ANOMALY "
                    f"N-KEY says it cannot, because gl070 discards every seeded "
                    f"posting row at [general/gl070.cbl:L492-L493] and leaves "
                    f"pretrans.tmp zero bytes long. Either the frozen bridge's "
                    f"POST-KEY handling has changed or this scenario's narrative is "
                    f"now wrong; re-measure before adjusting either.\n"
                    f"{parity.diagnose()}"
                )


@pytest.mark.database
@pytest.mark.oracle
def test_every_bounded_row_is_unchanged_relative_to_the_declared_seed(
    parity: object, normalized_dumps: object, column_by_key: object, harness: object,
    scenario_loader: object,
    withheld: object,
) -> None:
    """THE NOMINAL BALANCES ARE UNCHANGED RELATIVE TO THE SEED, on both sides.

    `LEDGER-BALANCE` is the one column the whole posting cycle exists to move -
    `add post-amount to ledger-balance` [general/gl072.cbl:L331] - so its seeded value
    surviving the run is the sharpest possible statement that no transaction posted.
    Asserted per account against the declared `ledger.dat` value, on each side
    separately, so neither side can be excused by the other's agreement.

    ONE SEEDED VALUE IS DELIBERATELY NEGATIVE AND ITS STORED FORM IS NOT. Account
    2000 is declared `-8765.43` and the column holds `8765.43`, which is ANOMALY
    N-EDIT and not a defect in this comparison: the bridge renders through
    `01 WS-MYSQL-EDIT PIC -Z(18)9.9(9)` whose sign occupies position 1, while every
    digit window it slices starts at position 3 or later, so the sign is
    STRUCTURALLY UNREACHABLE and never rendered. The comparison is therefore made on
    the ABSOLUTE value, and the sign loss is asserted as itself rather than tolerated
    silently - a future bridge that started rendering the sign would fail the second
    assertion below and force this note to be re-measured.

    Args:
        parity: The completed run, for the failure report.
        normalized_dumps: Both sides' normalised dumps.
        column_by_key: The projector, keyed on `LEDGER-KEY`.
        harness: The harness modules.
        scenario_loader: Loads the parsed scenario document.
        withheld: The value-free stand-in for a dumped cell, so a failure message can
            name a column without reproducing an accounting figure.
    """
    import decimal

    declared = {
        int(f"{int(row['WS-Ledger-Nos']):06d}{int(row['Ledger-PC']):02d}"): row
        for row in scenario_loader(SCENARIO)["seed_records"]["ledger.dat"]
    }
    assert declared, "the scenario declares no ledger.dat records - a HARNESS FAULT"
    signed_declarations = tuple(
        key
        for key, row in declared.items()
        if decimal.Decimal(row["Ledger-Balance"]) < 0
    )
    assert signed_declarations, (
        "at least one declared balance must be NEGATIVE, or the N-EDIT sign note "
        "below is untested and the fixture has lost a property it was built for"
    )

    for side in harness.dump_tables.SIDES:
        dump = normalized_dumps[side]["GLLEDGER-REC"]
        observed = column_by_key(dump, "LEDGER-BALANCE")
        assert set(observed) == set(declared), (
            f"GLLEDGER-REC on the {side} side carries keys {sorted(observed)!r} and "
            f"the scenario declares {sorted(declared)!r}. gl072 issues no nominal "
            f"write and no nominal delete, so the key set must be the seed's."
        )
        for key, seeded_row in declared.items():
            seeded = decimal.Decimal(seeded_row["Ledger-Balance"])
            got = decimal.Decimal(str(observed[key]))
            assert got == abs(seeded), (
                f"GLLEDGER-REC.LEDGER-BALANCE for LEDGER-KEY {key} is {got} on the "
                f"{side} side; the scenario seeded {seeded} and ANOMALY N-EDIT means "
                f"the bridge stores its ABSOLUTE value. A different figure means "
                f"`add post-amount to ledger-balance` [general/gl072.cbl:L331] ran, "
                f"which ANOMALY N-KEY says it cannot for a seeded posting row. "
                f"Re-measure before adjusting this test.\n"
                f"{parity.diagnose()}"
            )
        for key in signed_declarations:
            assert decimal.Decimal(str(observed[key])) >= 0, (
                f"LEDGER-KEY {key} was seeded negative and the column holds "
                f"{withheld(observed[key])}. ANOMALY N-EDIT says the bridge's edit "
                f"field can "
                f"never render the sign [common/nominalMT.cbl:L232]; a negative value "
                f"here means it now can, and every citation of N-EDIT in this "
                f"repository must be re-measured."
            )


@pytest.mark.database
@pytest.mark.oracle
def test_the_two_seeded_batches_are_rejected_for_two_different_reasons(
    parity: object, harness: object, scenario_loader: object
) -> None:
    """THE MIXTURE THIS SCENARIO ACTUALLY EXHIBITS, asserted on the seed itself.

    The file's name promises a mixture and its measured content delivers one - but a
    mixture of BATCH DISPOSITIONS rather than of posted and skipped transactions, for
    the frozen-code reason ANOMALY N-KEY records. This test pins the property that
    makes the two batches genuinely different inputs, so a future edit cannot quietly
    collapse them into two copies of the same case and leave the scenario's name
    unearned:

      - one batch is `88 Waiting` [copybooks/wsbatch.cob:L30], so gl070's phase-two
        filter ADMITS it [general/gl070.cbl:L457-L462] and it is discarded one layer
        lower, by the key guard;
      - the other is NOT waiting, so the same filter REJECTS it, and it never reaches
        the key guard at all.

    Both are `88 Status-Closed` [copybooks/wsbatch.cob:L27], which is what stops
    gl070's phase-one check raising the terminate code and aborting the run
    [general/gl070.cbl:L312-L313] - that path is `control_total_mismatch`'s subject,
    not this one.

    Args:
        parity: The completed run, so this test is part of the same evidence.
        harness: The harness modules, unused for comparison and taken for symmetry
            with the file's other tests.
        scenario_loader: Loads the parsed scenario document.
    """
    definition = scenario_loader(SCENARIO)
    declared = _declared_batch_rows(definition)
    cleared = {key: int(row["Cleared-Status"]) for key, row in declared.items()}

    waiting = sorted(key for key, value in cleared.items() if value == 0)
    not_waiting = sorted(key for key, value in cleared.items() if value != 0)

    assert waiting, (
        f"no declared batch is Waiting, so gl070's phase-two filter admits nothing "
        f"and the run is vacuous rather than mixed. Cleared-Status by key: {cleared!r}"
    )
    assert not_waiting, (
        f"no declared batch is other than Waiting, so every batch takes the same path "
        f"and the scenario's name is unearned. Cleared-Status by key: {cleared!r}"
    )
    assert all(int(row["Batch-Status"]) == 1 for row in declared.values()), (
        f"every declared batch must be Status-Closed, or gl070's phase-one check "
        f"raises the terminate code and aborts before phase two "
        f"[general/gl070.cbl:L312-L313] - which is a different scenario's subject. "
        f"Declared Batch-Status: "
        f"{ {k: v['Batch-Status'] for k, v in declared.items()} !r}"
    )
    assert all(
        int(row["Bcycle"]) == int(definition["seed_records"]["system.dat"]["1"][0]["Cyclea"])
        for row in declared.values()
    ), (
        "every declared batch must carry the system's own cycle, or gl070's cycle "
        "filter [general/gl070.cbl:L309-L310] rejects it before the disposition "
        "filter is reached and the mixture above is never evaluated"
    )
    assert parity.is_empty, (
        "this test is part of the parity evidence and must not render a verdict on a "
        "run that did not agree"
    )


@pytest.mark.database
@pytest.mark.oracle
def test_glposting_rec_is_an_unchanged_witness(
    parity: object, normalized_dumps: object, harness: object
) -> None:
    """`GLPOSTING-REC` is bounded in precisely so the diff can prove it was NOT touched.

    THE VERB CENSUS, MEASURED RATHER THAN INFERRED. gl072 issues exactly EIGHT facade
    verbs and not one of them is a `GL-Posting-*` verb: `GL-Batch-Open`
    [general/gl072.cbl:L276], `GL-Nominal-Open` [general/gl072.cbl:L274],
    `GL-Batch-Rewrite` [general/gl072.cbl:L377], `GL-Nominal-Rewrite`
    [general/gl072.cbl:L382], `GL-Nominal-Read-Next` [general/gl072.cbl:L408],
    `GL-Batch-Close` [general/gl072.cbl:L441], `GL-Nominal-Close`
    [general/gl072.cbl:L442] and `GL-Batch-Read-Next` [general/gl072.cbl:L454]. gl070
    issues twelve and every one is READ-ONLY - `GL-Batch-Open-Input` three times,
    `GL-Batch-Read-Next` three times, `GL-Batch-Close` three times, plus
    `GL-Posting-Open-Input` at [general/gl070.cbl:L481], `GL-Posting-Read-Next` at
    [general/gl070.cbl:L486] and `GL-Posting-Close` at [general/gl070.cbl:L466]. gl071
    issues none at all. So the ONLY two mutating verbs on the whole route are gl072's
    two Rewrites, and this table is written by nothing.

    CORROBORATED BY THE LINKER STUB. gl072's own `WS-Posting-Record` is a ONE-BYTE
    DUMMY:
    `03 WS-Posting-Record pic x.` at [general/gl072.cbl:L140], inside `01
    Dummies-4-Unused-ACAS-FH-Calls.` at [general/gl072.cbl:L135-L155], which the
    maintainer's own comment introduces as the call block for the unused facade verbs.
    It exists purely so the linker resolves the copybook's full verb set and it maps to
    NOTHING AT ALL in Python (Agent Action Plan section 0.4.3) - a representation-only
    omission recorded in `docs/migration/traceability.md` rather than left to look like
    a loss. A program that declares its posting record as a single byte cannot be
    writing posting rows.

    WHY THAT MATTERS HERE MORE THAN ANYWHERE ELSE. The rejected transactions leave
    NOTHING
    behind by construction, so their only trace is their SOURCE ROWS - and if those rows
    were consumed, mutated or deleted on one side and not the other, "the rejection left
    no trace" would be indistinguishable from "the rejection deleted its own evidence".
    This table is what makes the absence falsifiable.

    ON "IDENTICAL TO THE SEED". The protocol dumps AFTER each run and takes no pre-run
    dump, so the strongest assertion available in process is that the two post-run
    states agree. Identity to the SEEDED state rests on two things stated rather than
    re-derived here: that nothing on the route writes the table, which the census above
    establishes, and that both runs began from byte-for-byte the same seeded state,
    which the runners enforce with a per-table row-count fingerprint written in the
    declared order and compared across the two sides - a disagreement there is a HARNESS
    FAULT in the runner and never a silent pass. That argument is made explicitly rather
    than dressed up as an assertion this file cannot make.

    Args:
        parity: The completed run, for the per-table findings.
        normalized_dumps: Both sides' normalised dumps.
        harness: The three harness modules, for the side labels and for `render`.
    """
    sides = tuple(harness.dump_tables.SIDES)
    postings = [normalized_dumps[side]["GLPOSTING-REC"] for side in sides]

    witness = next(
        table for table in parity.tree.tables if table.table == "GLPOSTING-REC"
    )
    assert witness.is_empty, (
        f"GLPOSTING-REC differs between the two sides - {witness.total_differences} "
        f"finding(s) - and it is the UNCHANGED WITNESS: nothing on the "
        f"gl070 -> gl071 -> gl072 route writes it, because gl072 issues zero "
        f"GL-Posting-* verbs and gl070's three posting verbs are Open-Input, Read-Next "
        f"and Close. Any finding here means one side wrote, mutated or deleted a "
        f"posting "
        f"row, which would also destroy the only evidence the rejected transactions "
        f"have.\n{parity.diagnose()}"
    )
    assert not witness.missing_in_python and not witness.missing_in_cobol, (
        f"GLPOSTING-REC carries rows on one side only: "
        f"{len(witness.missing_in_python)} present for cobol and absent for python, "
        f"{len(witness.missing_in_cobol)} the other way. A read-only table cannot gain "
        f"or lose a row on either side."
    )
    assert witness.cobol_row_count == witness.python_row_count, (
        f"GLPOSTING-REC holds {witness.cobol_row_count} row(s) for cobol and "
        f"{witness.python_row_count} for python. Both runs seeded the same rows and "
        f"neither run writes this table, so the counts must be equal AND equal to the "
        f"seeded count."
    )
    assert not witness.columns_differ, (
        f"GLPOSTING-REC's column lists disagree: {witness.cobol_columns!r} against "
        f"{witness.python_columns!r}. The schema is frozen "
        f"[mysql/ACASDB.sql:L154-L169] and declares fourteen columns, so a "
        f"disagreement means one dump was produced against a different schema."
    )
    assert postings[0]["rows"] == postings[1]["rows"], (
        f"GLPOSTING-REC's rows are not byte-identical between {sides[0]} and "
        f"{sides[1]} after normalisation. This is the same claim the TreeDiff above "
        f"makes, asserted directly on the two dumps so that the failure names THIS "
        f"table rather than the tree."
    )


#  NO `database` OR `oracle` MARK, DELIBERATELY. This test used to consume the real
#  ten-stage run, which needed both; it now drives synthetic trees through the shipped
#  comparison in process, so it executes on a bare host. Leaving the marks on would SKIP
#  the contract in exactly the environments where nothing else checks it.
def test_diff_exit_contract_is_honoured(
    tmp_path, harness, frozen_schema, vocabulary, capsys
) -> None:
    """The THREE-WAY exit contract: 0 is a pass, 1 is a failure, 2 IS NEVER A PASS.

        0  the trees are identical, and stdout is EMPTY - zero bytes, not a banner
           and not "no differences found"                                 -> PASS
        1  a real behavioural difference, with a deterministic report   -> FAILURE
        2  THE COMPARISON COULD NOT BE PERFORMED - a missing tree, a capture that
           attests nothing, a capture taken after a failed run           -> ERROR

    A TEST THAT TREATED "COULD NOT COMPARE" AS "NO DIFFERENCES" IS THE SINGLE WORST BUG
    AVAILABLE IN THIS TREE, so the mapping is exercised rather than trusted. Rule R-6
    makes an empty diff the pass condition ONLY when a comparison actually happened.

    DRIVEN THROUGH THE SHIPPED COMPARISON, AND THROUGH ONE IMPLEMENTATION.
    `tests/conftest.py`'s `assert_diff_exit_contract` publishes two synthetic sides with
    `harness/dump_tables.py`'s own writer, canonicalises them with `harness/normalize.py`
    and compares them with `harness/diff_states.py` - once for each of the four cases.
    THIS FILE USED TO ASSERT THE CONTRACT AGAINST MODULE CONSTANTS AND HAND-BUILT
    `TreeDiff` DATACLASSES, which passes whatever the comparison actually does: three
    integers being distinct says nothing about what the tool exits with, and a dataclass
    built in the test reports whatever the test put in it. The constants are still
    checked here, but only as a cheap corroboration of a contract the helper has just
    exercised end to end, over THIS scenario's own three-table bound.
    It matters particularly here, where the two silent skips leave NO message, NO
    counter and no trace [general/gl072.cbl:L291-L292, L303-L304], so the diff is the
    only instrument that can see them and a comparison that refused to run must never
    read as agreement.

    IT ASSERTS NOTHING WHATEVER ABOUT THE MIGRATION. The trees are SYNTHETIC, built from
    the frozen schema's own column lists, so the machinery under test is the shipped
    machinery - but a verdict taken from a hand-built tree is not protocol evidence, and
    none is claimed. That is also why this test needs no Compose stack and no compiled
    oracle: it executes on a bare host.

    Args:
        tmp_path: A private output root, so `$ACAS_OUT` is neither read nor needed and
            nothing is written into a compared tree.
        harness: The three harness Python modules (R-1).
        frozen_schema: The parsed `mysql/ACASDB.sql`, READ AND NEVER WRITTEN. It supplies
            every column name and declared type, so nothing is invented.
        vocabulary: The STACK-FREE bundle. Stages 4 and 8 are file-to-file
            transformations driven in process, which is what lets the whole contract be
            exercised on a bare host; it also publishes the helper.
        capsys: The two refusals' streams, which the helper drives through
            `diff_states.main` directly - the `diff` helper maps exit 2 to a harness
            fault by design, and here a refusal is the expected outcome.

    Raises:
        AssertionError: An exit status, a stdout stream or a verdict did not match the
            contract.
    """
    vocabulary.assert_diff_exit_contract(
        SCENARIO,
        out_dir=tmp_path,
        harness=harness,
        schema=frozen_schema,
        vocabulary=vocabulary,
        readouterr=capsys.readouterr,
    )

    # THE THREE STATUSES REMAIN DISTINCT AND KEEP THEIR DOCUMENTED VALUES. Cheap, and
    # worth stating separately: the helper above proved what the tool DOES, and this
    # proves the numbers a reader of the evidence document will see are the numbers this
    # file names. Collapsing "could not compare" into either of the other two is how a
    # false pass is manufactured.
    diff_states = harness.diff_states
    observed = (
        diff_states.EX_IDENTICAL,
        diff_states.EX_DIFFERENT,
        diff_states.EX_ERROR,
    )
    assert observed == (0, 1, 2), (
        f"the exit contract's three statuses must be 0, 1 and 2 in that order; the "
        f"comparison declares {observed!r}."
    )


@pytest.mark.database
@pytest.mark.oracle
def test_dump_is_wellformed_on_both_sides(
    normalized_dumps: object, harness: object, frozen_schema: object,
    withheld: object,
) -> None:
    """Every dump on both sides has the shape the protocol guarantees, and no other.

    THE VACUITY ARGUMENT, DEFENDED EXPLICITLY. A comparison of two dumps is meaningful
    only because a dump carries NO timestamp, NO server version, NO connection info, NO
    scenario name and NO side - the side is recorded in the PATH. One such key and the
    two sides would differ for a reason that has nothing to do with the accounting, or,
    worse, an equality assertion would be quietly asserting nothing. So the five keys
    are checked in order, against `harness/dump_tables.py`'s own `DUMP_KEYS` rather than
    a local list.

    THE STRUCTURAL CONTRACT HAS ONE DEFINITION AND IT HAS ALREADY RUN. The
    `normalized_dumps` fixture reads every dump with `harness/diff_states.py`'s
    `load_dump`, which is the reader-and-asserter the comparison itself uses: the five
    keys in order, an in-scope table, a single-column primary key present in `columns`,
    `row_count == len(rows)`, every row of the declared width, no duplicate primary key,
    NO NULL and NO `float` (R-2). What is added here is what `load_dump` cannot know:
    that `columns` matches the FROZEN SCHEMA's ordinal order exactly, that the rows are
    primary-key ASCENDING, and that DECIMAL values arrive as canonical JSON STRINGS.

    WHY DECIMALS ARE STRINGS AND NOT NUMBERS. R-2 forbids binary floating point anywhere
    in an accounting value, and JSON has no exact decimal: a bare `123.45` in a dump
    would be parsed back as a float by any reader. So job 2 of the normaliser renders
    every
    DECIMAL
    at its DECLARED scale as a string - and the declared scale is NOT uniformly two,
    which is why the check reads the scale from `mysql/ACASDB.sql` rather than assuming.
    For this scenario the money columns are `GLBATCH-REC`'s four `decimal(14,2)
    unsigned` [mysql/ACASDB.sql:L90-L93], `GLLEDGER-REC.LEDGER-BALANCE decimal(10,2)`
    [mysql/ACASDB.sql:L128] and `GLPOSTING-REC`'s two `decimal(10,2)`
    [mysql/ACASDB.sql:L163], [mysql/ACASDB.sql:L168].

    WHY THE ROW ORDER IS ASSERTED. The dump is `SELECT * FROM <table> ORDER BY <primary
    key>` with no tie-break, and it needs none: every in-scope table has a SINGLE-COLUMN
    primary key and zero secondary indexes, so the order is total and stable. That is
    the whole basis of Agent Action Plan section 0.6.6's claim that a non-empty diff is
    always real, so it is checked rather than trusted.

    Args:
        normalized_dumps: Both sides' normalised dumps for the three bounded tables.
        harness: The three harness modules - `DUMP_KEYS`, `SIDES`, the in-scope table
            facts and the schema helpers all come from them, never from a local
            restatement.
        frozen_schema: `mysql/ACASDB.sql` parsed into `{table: {column: ColumnType}}`.
        The
            file is READ and never written; any diff against it is a defect in the
            migration (Agent Action Plan section 0.8.1).
        withheld: The value-free stand-in for a dumped cell, so a failure message can
            name a column without reproducing an accounting figure.
    """
    dump_keys = tuple(harness.dump_tables.DUMP_KEYS)
    diff_states = harness.diff_states
    normalize = harness.normalize

    for side in harness.dump_tables.SIDES:
        for table, dump in normalized_dumps[side].items():
            where = f"{side}/{table}"

            assert tuple(dump.keys()) == dump_keys, (
                f"{where} carries the keys {list(dump.keys())!r}; a dump must carry "
                f"exactly {list(dump_keys)!r} IN THAT ORDER and no others - no "
                f"timestamp, no server version, no connection info, no scenario name "
                f"and no side. THE ABSENCE OF ANY SUCH KEY IS WHAT MAKES THE "
                f"COMPARISON MEANINGFUL."
            )
            assert dump["table"] == table, (
                f"{where} declares table {dump['table']!r}; a report naming the wrong "
                f"table would be worthless as evidence."
            )

            spec = diff_states.IN_SCOPE[table]
            assert dump["primary_key"] == spec.primary_key, (
                f"{where} declares primary key {dump['primary_key']!r}; "
                f"mysql/ACASDB.sql declares {spec.primary_key!r} "
                f"[mysql/ACASDB.sql:L{spec.schema_line}]. Rows are aligned by that "
                f"column's VALUE, so the wrong column means no meaningful alignment."
            )

            columns = tuple(str(name) for name in dump["columns"])
            assert len(columns) == spec.column_count, (
                f"{where} lists {len(columns)} column(s); mysql/ACASDB.sql declares "
                f"{spec.column_count} [mysql/ACASDB.sql:L{spec.schema_line}]. The "
                f"schema is FROZEN, so a disagreement means either the dump or the "
                f"checkout is wrong."
            )
            expected_columns = normalize.schema_columns(frozen_schema, table)
            assert columns == expected_columns, (
                f"{where}'s column list disagrees with the frozen schema's ordinal "
                f"order: {columns!r} against {expected_columns!r}. Rows are "
                f"POSITIONAL, so a column list in any other order has no meaningful "
                f"alignment."
            )

            rows = list(dump["rows"])
            assert dump["row_count"] == len(rows), (
                f"{where} declares row_count {dump['row_count']!r} and carries "
                f"{len(rows)} row(s)."
            )
            for row in rows:
                assert len(row) == len(columns), (
                    f"{where} carries a ragged row of {len(row)} value(s) against "
                    f"{len(columns)} column(s). A ragged row cannot be aligned at all."
                )

            key_ordinal = columns.index(spec.primary_key)
            keys = [row[key_ordinal] for row in rows]
            assert keys == sorted(keys), (
                f"{where}'s rows are not primary-key ASCENDING: {keys!r}. The dump is "
                f"`SELECT * ORDER BY {spec.primary_key}` and every in-scope table has "
                f"a single-column primary key and zero secondary indexes, so the order "
                f"is total and stable and there is nothing to tie-break."
            )
            assert len(set(keys)) == len(keys), (
                f"{where} carries a primary-key value twice: {keys!r}. Rows are "
                f"aligned by that value, so a duplicate would silently hide a row."
            )

            # THE NUMERIC POLICY, PER COLUMN AND PER VALUE (R-2). A float anywhere in an
            # accounting dump is refused outright; DECIMAL arrives as a canonical string
            # at the DECLARED scale, and integer widths arrive as JSON integers.
            for ordinal, name in enumerate(columns):
                declared = normalize.column_type(frozen_schema, table, name)
                for row in rows:
                    value = row[ordinal]
                    assert value is not None, (
                        f"{where} carries a null in column {name!r}. Every column of "
                        f"the frozen schema is NOT NULL, and every bridge load "
                        f"paragraph initialises its host-variable group so an unset "
                        f"field becomes zero or space rather than SQL NULL."
                    )
                    assert not isinstance(value, float), (
                        f"{where} carries a binary floating-point value in column "
                        f"{name!r}: {withheld(value)}. R-2 forbids binary floating point in "
                        f"any accounting value, in computation, in storage and in "
                        f"transport."
                    )
                    if declared.kind == normalize.KIND_DECIMAL:
                        assert isinstance(value, str), (
                            f"{where} carries column {name!r} ({declared.sql_type}, "
                            f"declared at [mysql/ACASDB.sql:L{declared.line}]) as a "
                            f"{type(value).__name__}: {withheld(value, column=name)}. A DECIMAL is rendered "
                            f"as a canonical JSON STRING at its declared scale, "
                            f"because JSON has no exact decimal and a bare number "
                            f"would be read back as a float (R-2)."
                        )
                    elif declared.kind == normalize.KIND_INTEGER:
                        assert type(value) is int, (
                            f"{where} carries column {name!r} ({declared.sql_type}, "
                            f"declared at [mysql/ACASDB.sql:L{declared.line}]) as a "
                            f"{type(value).__name__}: {withheld(value, column=name)}. An integer width "
                            f"arrives "
                            f"as a JSON integer, and `1` against `\"1\"` IS a "
                            f"difference."
                        )


@pytest.mark.database
@pytest.mark.oracle
def test_system_record_parity_by_digest_as_well_as_by_dump(parity: object, protocol: object) -> None:
    """THE PARAMETER ROW IS BOUNDED TWICE - by the dump, and by a digest of it.

    WHAT THIS CLOSES. The tempting shortcut is to keep `SYSTEM-REC` off every scenario's
    `affected_tables` on the ground that no side writes it. THAT GROUND IS FALSE:
    `acas_posting/cli/args.py`'s `overrewrite` reproduces
    [general/general.cbl:L656-L672] and every one of the seven routes calls it, so the
    parameter row is written on BOTH sides of every scenario. Until this assertion
    existed, a regression in that persistence produced an EMPTY DIFF and a green run.

    WHICH KEYS THIS ROUTE WRITES. `gl_post_cycle` binds `general_menu_state`, which
    carries both the defaults record and the totals record, so `overrewrite` rewrites
    KEY 1, KEY 2 and KEY 4 - the same three the COBOL General menu writes
    [general/general.cbl:L659, L664, L667]. This scenario's two silent skips leave no
    trace anywhere else, so every bound that can be drawn is worth drawing.

    IT IS DUMPED, WITH EXACTLY TWO CELLS WITHHELD. `SYSTEM-REC` is one of the 22
    in-scope tables every capture covers, so 167 of its 169 columns are compared by value
    like any other table's. The two exceptions are credentials - `RDBMS-PASSWD char(12)`
    [copybooks/wssystem.cob:L139] and `PASS-WORD` - and a capture is evidence that gets
    committed, so `harness/dump_tables.py`'s `REDACTED_COLUMNS` replaces those two cells
    with a fixed marker inside `render_value`, the one funnel every captured cell passes
    through. That is keyed by `(table, column)` and applied identically on both sides, so
    it cannot itself produce a difference. Bounding the whole table out instead - the
    alternative that was considered and rejected - removes the leak and takes 167
    genuinely-written columns with it, and a bound drawn that way cannot reveal a
    difference in what it excludes.

    AND BOTH RUNNERS FINGERPRINT IT ANYWAY, before and after every run, which is what
    this test compares. A sha256 over the canonical primary-key-ordered dump covers all
    169 columns, credentials included, without being the dump - so the two withheld cells
    are still compared, inside a hash that leaks nothing. The credential columns come from
    the environment and are identical for both sides of one run, so they cannot
    manufacture a difference; anything that does differ is a difference in what the two
    cycles wrote. MEASURED, so the second-order worry is stated with its limit: the row's
    content depends on what the route DID - the run-date stamp, the IRS allocator, the
    one-shot latches, and `Date-Form`, which the frozen date sections write back
    [copybooks/wssystem.cob:L127] - and the digest HOLDS on all four scenarios that
    declare `unchanged` and MOVES on every one that declares `changed`. That was measured
    over the eight committed scenarios, which is all four `unchanged` ones. THE `changed`
    HALF IS NOT COVERED BY ANY COMMITTED SCENARIO: it was established on a definition that
    declared `changed` and moved the row by construction, its Phase 5 advancing the cycle
    and rotating the quarter counter, and no scenario in `harness/scenarios/` does that.
    So declaring the row falsifies no effect claim; the digest is the belt to the dump's
    braces.

    Args:
        parity: The completed, guarded run. The assertion needs its
            artifact layout, and taking the fixture is what orders this test after the
            two run stages rather than a comment claiming it.
        protocol: The protocol bundle. `assert_system_record_parity` is the ONE
            implementation of this comparison and lives in `tests/conftest.py`; nothing
            here reads a fingerprint file itself.

    Raises:
        Skipped: The harness Compose stack is not usable.
        AssertionError: A post-run record is missing or unreadable (a harness fault), or
            the two cycles left the parameter row in different states (a behavioural
            difference the table diff cannot see).
    """
    cobol_record, python_record = protocol.assert_system_record_parity(parity)

    # STATE WHAT WAS OBSERVED, so the test is not merely "the helper did not raise".
    # A zero-row parameter row would mean the seed never loaded system.dat, in which
    # case both sides agree on nothing at all and the digests would match vacuously.
    assert cobol_record.row_count == python_record.row_count == 1, (
        f"{SCENARIO}: the parameter row holds {cobol_record.row_count} row(s) on the "
        f"oracle side and {python_record.row_count} on the migrated side. system.dat "
        f"seeds EXACTLY ONE row for key 1, and two empty tables carry the same digest - "
        f"so without this check the parity claim above could pass on a database that "
        f"was never seeded."
    )
