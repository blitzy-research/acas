"""THE EMPTY BATCH - the degenerate case, and the one scenario whose central
question is settled ONLY by running the compiled oracle.

Scenario `empty_batch`, subsystem `general`, operation `gl_post_cycle`, declared
terminal status `expected_status: [0]`. It drives the eight-stage parity protocol
and asserts an EMPTY ordering-normalised diff across three bounded tables.

THERE IS NO USER RULES DOCUMENT FOR THIS PROJECT. `review_rules` reports that none
was provided, so there is no on-disk rules file and no reader should look for one.
The six binding rules R-1 to R-6 live in the Agent Action Plan itself, section
0.7.2, and their exact wording is retrievable from the requirements via
`review_prompt`. Summarised in this file's own words, and each named at the site
that honours it:

    R-1  No COBOL at runtime. This file NEVER imports `harness`; harness/ has no
         `__init__.py` and pyproject.toml's packaging allow-list excludes it, which
         is the structural enforcement. The three harness Python modules and the
         four shell runners are reached only through tests/conftest.py's fixtures.
    R-2  Zero binary floating point. No float, no tolerance, no epsilon, no
         approximate comparison, no numpy, no pandas. Every dumped value is a
         `str` or an `int` and the comparison is `==` after a type check.
    R-3  No new validations, fields or schema changes; no concurrency. NOTHING HERE
         ASSERTS THAT AN EMPTY-CASE GUARD EXISTS, and none may be added - see
         "NO GUARD MAY BE ADDED" below. Strictly sequential: no distributed test
         runner, no parallel execution, no randomised ordering.
    R-4  Legacy anomalies are reproduced, never fixed. A-12, A-13, A-14 and A-15
         are named at their sites with the anomaly log's VERIFIED locators, and the
         `acas007`-versus-`acas008` `Open-Output` divergence is recorded rather
         than harmonised.
    R-5  Full traceability. Every claim carries an inline `[<path>:L<n>]` citation
         into the frozen source, and every anomaly and ambiguity carries its
         identifier. `pytest-cov` is evidence, never a gate.
    R-6  Compiled behaviour is the tie-breaker. An empty normalised diff is the
         pass condition; a diff status of 2 means the comparison could not be
         performed and is an ERROR, never a pass. THIS FILE LEANS ON R-6 HARDER
         THAN ANY OTHER IN THE TREE - see the central open question below.

Where the Agent Action Plan is silent, enterprise-standard best practice applies.
Nothing has been invented to fill the gap.

-------------------------------------------------------------------------------
THE INVERTED PREMISE, AND WHAT IT FORBIDS THIS FILE FROM DOING
-------------------------------------------------------------------------------

Agent Action Plan section 0.8.2, verbatim:

    "There is no test suite: compiled COBOL execution is the behavioral
    specification, defects included. A defect reproduced is correct; a defect
    fixed is a failure."

The corollary governs every assertion below: A TEST THAT ASSERTS CORRECT
ACCOUNTING RATHER THAN OBSERVED BEHAVIOUR IS ITSELF A DEFECT. So no test here
recomputes a balance, none asserts that debits equal credits, and none predicts
a stored value. The empty diff is the arbiter; the oracle records the answer.

-------------------------------------------------------------------------------
THE COBOL ROUTE, AND WHY ZERO IS PROVABLE RATHER THAN HOPED FOR
-------------------------------------------------------------------------------

`load08.` [general/general.cbl:L805-L815] dispatches the three phases in order,
with a HARD gate between the first and the second:

    805  load08.
    808       move     "gl070" to ws-called.
    809       perform  load00.
    810       if       ws-term-code = 5
    811                go to display-menu.
    812       move     "gl071" to ws-called.
    813       perform  load00.
    814       move     "gl072" to ws-called.
    815       go       to load00.

THE GATE MUST NOT FIRE HERE. The seeded batch is CLOSED, so `gl070`'s phase-1
detector never trips:

    312       if       bcycle not = scycle          <- the phase-1 cycle filter
    313                go to  loop.
    314       if       status-open                  <- NEVER TRUE for this batch
    315                move  1  to  a.

and therefore the raise block never runs:

    287       if       a = 1
    288                perform gl060a
    289                move 5 to ws-term-code       <- the ONLY raise on this route
    290                go to  main-exit.

`expected_status: [0]` follows from that, and the other candidate is unreachable
by construction: term code 8 is set only by `[sales/sl055.cbl:L344]` and
`[purchase/pl055.cbl:L286]`, both of which sit inside `if FS-Cobol-Files-Used`
([sales/sl055.cbl:L326], [purchase/pl055.cbl:L266]) while the scenario pins
`system.file_system_used: 1` - and neither program is dispatched by this
operation in any case.

LOCATOR CORRECTIONS CARRIED FORWARD (R-5). The Agent Action Plan cites the
open-batch detection at `L288` and the raise at `L312-L313`. Measured against
this checkout, L288 is `perform gl060a`, L289 is the raise, L312-L313 is the
phase-1 CYCLE filter and L314-L315 is the detector. docs/migration/anomaly-log.md
section 8 records the same class of correction; the verified values are used
throughout this file, because a citation that does not resolve defeats the
convention.

THE ABORT GATES DIVERGE BY LEDGER AND ARE NOT HARMONISED. General is
`if ws-term-code = 5` once [general/general.cbl:L810-L811]; Sales is
`if ws-term-code not = zero` TWICE [sales/sales.cbl:L761-L762, L765-L766];
Purchase has NONE, commented out [purchase/purchase.cbl:L755-L758]; IRS has none
and no dispatch wrapper at all [irs/irs.cbl:L666-L672]. Only the General form is
relevant here; the others are recorded so the divergence stays visible (R-4).

-------------------------------------------------------------------------------
THE SEED - EXACTLY THREE FILES, AND THE ABSENCE OF THE FOURTH IS THE SCENARIO
-------------------------------------------------------------------------------

`system.dat`, `ledger.dat`, `batch.dat`. THERE IS NO `posting.dat`. That absence
is what makes the batch empty: no transaction rows exist for `gl070`'s phase 2 to
explode, so its posting read hits end-of-file on its first attempt
[general/gl070.cbl:L487-L488], `gl071` sorts nothing
[general/gl071.cbl:L172-L178], and `gl072` reads a work file that is
immediately at end [general/gl072.cbl:L286]. This is the ONLY scenario in the set
seeded with three files; every other General Ledger scenario has four.

The loader mapping, from the frozen script this contract is reproduced from:
`system.dat` drives the four-loader system block `systemLD` then `sys4LD` then
`finalLD` then `dfltLD` [common/masterLD.sh:L51-L87]; `ledger.dat` drives
`nominalLD` [common/masterLD.sh:L103]; `batch.dat` drives `glbatchLD`
[common/masterLD.sh:L94]. `posting.dat` would drive `glpostingLD`
[common/masterLD.sh:L109] - the mapping exists and is deliberately not named.

EIGHT FLAT-FILE NAMES ARE FORBIDDEN IN ANY SEED LIST because their loaders target
out-of-scope tables: `delfolio.dat` L95, `delinvno.dat` L96, `delivery.dat` L97,
`pay.dat` L106, `plautogen.dat` L108, `slautogen.dat` L113, `staudit.dat` L114
and `stockctl.dat` L115, all in [common/masterLD.sh]. Their loaders -
`delfolioLD`, `sldelinvnosLD`, `deliveryLD`, `paymentsLD`, `plautogenLD`,
`slautogenLD`, `auditLD`, `stockLD` - are never invoked, and
test_seed_has_exactly_three_files_and_no_posting_dat asserts their absence.

THE BATCH IS WELL FORMED BUT EMPTY. From [copybooks/wsbatch.cob]:

    WS-Ledger      = 1   `88 GL-Batch value 1`        L15-L16
    Batch-Status   = 1   `88 Status-Closed value 1`   L25-L27  <- CLOSED
    Cleared-Status = 0   `88 Waiting value 0`         L29-L32  <- WAITING
    Bcycle         = system.cyclea                    L34
    Items          = 0   `03 Items pic 99.`           L23
    Input-Gross, Input-Vat, Actual-Gross, Actual-Vat all zero, each
    `pic 9(9)v99` under `03 Amounts comp-3` and UNSIGNED    L40-L44

CLOSED keeps the abort gate shut; WAITING is what lets the phase-2 filter admit
the batch. An alternative reading of "empty batch" is permitted - no batch at all
in the pinned cycle - but THE ZERO-ITEM BATCH IS PREFERRED, because it exercises
`gl070`'s two filters and `gl072`'s at-end path instead of trivially skipping
everything. The batch's PRESENCE WITH ZERO ITEMS is the input under test and must
not be tidied out of the seed to make the run pass more easily (R-4).

THE PHASE-2 FILTER MUST ADMIT IT [general/gl070.cbl:L460-L463]:

    460       if       status-open
    461             or not waiting
    462             or not gl-batch
    463                go to  loop.

so the batch must be closed AND waiting AND a General Ledger batch. Note that the
cycle filter appears TWICE WITH DIFFERENT COMPANIONS - L312-L313 in phase 1 and
L457-L458 in phase 2 - and only the second pass adds L460-L463. Agent Action Plan
section 0.6.4: "Collapsing the two passes into one would change which batches are
pre-processed."

`Bcycle` MUST EQUAL `system.cyclea`, or both filters skip the batch and the run
touches nothing at all - which in THIS scenario is nearly indistinguishable from
the intended outcome, making it a peculiarly silent trap. The pin is asserted;
`system.period: 1` is inert here, because no scenario drives `gl_end_of_cycle`.

-------------------------------------------------------------------------------
THE CENTRAL OPEN QUESTION - RESOLVED BY THE ORACLE, NEVER BY READING
-------------------------------------------------------------------------------

`gl072`'s mainline begins [general/gl072.cbl:L283-L289]:

    283  loop.
    286       read     post-trans  at end
    287                perform  end-account
    288                perform  end-batch
    289                go to    end-run.

and `end-batch` is [general/gl072.cbl:L372-L377]:

    372  end-batch.
    375       move     1  to  cleared-status.
    376       move     run-date  to  posted.
    377       perform  GL-Batch-Rewrite.

WITH ZERO RECORDS IN THE SORTED WORK FILE THE VERY FIRST READ HITS AT END, so
`end-account` and `end-batch` are performed with `save-batch` still zero
[general/gl072.cbl:L281]. Does `end-batch` then stamp the empty batch cleared and
posted, or does it rewrite nothing meaningful, or rewrite a zero-key record? THAT
QUESTION IS NOT ANSWERED HERE. No test below hard-codes an expectation for
`CLEARED-STATUS` or `POSTED`; each asserts only that THE TWO SIDES AGREE. The
question is carried as ambiguity `Q-EMPTY-BATCH-AT-END` in
docs/migration/ambiguity-resolutions.md - the identifier is coined here, in the
descriptive form that document already uses for `Q-SORT-TIE-ORDER` and
`Q-A17-POSTINGS-EFFECT`, so that the resolution has a name to be filed under.

The same question extends to `GLLEDGER-REC`, because `end-account`
[general/gl072.cbl:L379-L382] performs `GL-Nominal-Rewrite` at L382 - and
`new-account`, which issues the only `GL-Nominal-Read-Next`
[general/gl072.cbl:L408] under its guard at L407, is NEVER REACHED on an
immediately-at-end read, so there may be no positioned record to rewrite. Again:
the oracle decides.

`run_date` is pinned to the project value precisely so that this is answerable.
IF L376 fires, the stamped value is deterministic and the two sides compare
byte-for-byte; if it does not, `POSTED` stays as seeded. Either way the diff is
decisive. The binary observable is `05  Run-Date        binary-long.`
[copybooks/wssystem.cob:L67] and `GLBATCH-REC.POSTED` is `int(8) unsigned`
[mysql/ACASDB.sql:L88], so whatever L376 writes is compared as an INTEGER.

ANOMALY A-15 LANDS HERE HARDER THAN ANYWHERE ELSE, and is not resolved here.
[copybooks/wsbatch.cob:L7-L9] verbatim in shape:

    L7  *> 96 bytes 26/03/09
    L8  *> 98 bytes 20/12/11 (no, dont understand as I count 96)
    L9  *>   but function length (Batch-record) says 98?

The field that carries "zero transactions" is `Items pic 99`
[copybooks/wsbatch.cob:L23], near the FRONT of the record with every status
field, date and money amount behind it. If the declared length rather than the
sum of the fields governs the record actually read, trailing-field alignment
shifts and the very fields this scenario depends on - `Batch-Status`,
`Cleared-Status`, `Bcycle` - could be read from the wrong offsets. Which reading
governs is the R-6 arbitration filed as `Q-4` in
docs/migration/ambiguity-resolutions.md, settled by execution and not by counting
bytes on paper. docs/migration/anomaly-log.md records A-15's status as PENDING
against exactly that identifier.

-------------------------------------------------------------------------------
THE TRAP THAT MAKES THIS THE MOST DANGEROUS SCENARIO IN THE SET
-------------------------------------------------------------------------------

AN EMPTY DIFF HERE IS ALSO EXACTLY WHAT A COMPLETELY BROKEN HARNESS PRODUCES:
nothing seeded, nothing run, nothing written, nothing differing. Two defences,
both mandatory, and both asserted below:

  1. `system.file_system_used: 1`. `File-System-Used pic 9` with
     `88 FS-Cobol-Files-Used value zero` and `88 FS-MySql-Used value 1`
     [copybooks/wssystem.cob:L112-L114]; every handler gates its database path on
     it, for the batch handler at [common/acas007.cbl:L316-L320]:

         316       if       not FS-Cobol-Files-Used
         317                move RDBMS-Flat-Statuses to FA-RDBMS-Flat-Statuses
         318                perform  ba-Process-RDBMS
         319                go to AA-Main-Exit
         320       end-if.

     With `0` the handler never touches MySQL, both dumps come back empty and the
     diff exits 0 - A SILENT FALSE PASS. This scenario legitimately expects very
     little change, so that false pass is nearly invisible. The pin is asserted
     with `== 1`.

  2. THE SEED FINGERPRINT. `harness/run_python_scenario.sh` records one
     tab-separated `<TABLE>` and `<COUNT>` line per affected table, IN THE
     LIST'S DECLARED ORDER,
     immediately before the run, and refuses to proceed when the oracle side
     recorded something different - reported as a HARNESS FAULT and never as a
     behavioural difference, because a stage that cannot establish its own
     starting state has not measured behaviour at all. It converts a whole class
     of silent false failures into a correctly attributed error. THIS IS WHY THE
     ORDER OF `affected_tables` IS PART OF THE CONTRACT and not a matter of
     taste. Both fingerprints live under `run-logs/`, outside every compared
     tree, so neither can leak into a capture (R-6).

Two further structural facts corroborate that an empty result here is real rather
than vacuous, and both are asserted from the dumps rather than from prose: the
seeded tables come back with rows on BOTH sides, and `GLPOSTING-REC` comes back
EMPTY on both sides.

`empty_batch` IS NOT THE MISSING-EXTRACT-FILE PATH. [sales/sl055.cbl:L344] and
[purchase/pl055.cbl:L286] raise term code 8 for a MISSING FILE, not for an EMPTY
BATCH; they belong to no mandated scenario and are unreachable under
`file_system_used: 1` in any case. Conflating the two would mis-describe both.

-------------------------------------------------------------------------------
WHAT THE CYCLE CAN TOUCH AT ALL, AND WHY GLPOSTING-REC IS AN UNCHANGED WITNESS
-------------------------------------------------------------------------------

`gl072` issues EIGHT facade verbs in total and NOT ONE of them is a
`GL-Posting-*` verb: `GL-Batch-Open` L276, `GL-Nominal-Open` L277,
`GL-Batch-Rewrite` L377, `GL-Nominal-Rewrite` L382, `GL-Nominal-Read-Next` L408,
`GL-Batch-Close` L441, `GL-Nominal-Close` L442 and `GL-Batch-Read-Next` L454, all
in [general/gl072.cbl]. `gl070` is READ-ONLY throughout - `GL-Batch-Open-Input`
at L303, L342, L448; `GL-Batch-Read-Next` at L308, L347, L453; `GL-Batch-Close`
at L321, L440, L473; plus `GL-Posting-Open-Input` L481, `GL-Posting-Read-Next`
L486 and `GL-Posting-Close` L466, all in [general/gl070.cbl]. `gl071` performs no
facade verb at all: it is a pure sort [general/gl071.cbl:L172-L178].

So `GLPOSTING-REC` IS AN UNCHANGED WITNESS on every General Ledger scenario, and
in THIS one it is additionally EMPTY IN THE SEED, since no `posting.dat` was
loaded. Corroborated by the one-byte dummy stub `gl072` declares purely so the
linker resolves the copybook's full verb set [general/gl072.cbl:L135-L155], whose
`03  WS-Posting-Record      pic x.` sits at L140. Agent Action Plan section 0.4.3
records that the whole block maps to nothing in Python, as a
representation-only omission rather than a loss.

`common/acas007.cbl`'s `Open-Output` DOES NOT TRUNCATE `GLBATCH-REC`, and the
divergence from its sibling is preserved rather than harmonised (R-4):

    305       if       fn-Open and
    306                fn-output
    307           and  not FS-Cobol-Files-Used  *> RDB processing
    308  *>             set fn-delete-all to true      <- COMMENTED OUT
    309  *>             move zero to access-type       <- COMMENTED OUT
    310                perform ba-Process-RDBMS
    311                go to AA-Main-Exit
    312       end-if.

whereas the equivalent line IS ACTIVE at [common/acas008.cbl:L316] inside
[common/acas008.cbl:L313-L319], where `set fn-delete-all to true` makes an
open-for-output delete every row. Directly relevant here: the seeded batch row
cannot be silently wiped by an open.

[general/gl072.cbl:L443] `call "SYSTEM" using Print-Report.` is a spool-out,
excluded by Agent Action Plan section 0.2.2. It has no database effect and must
appear in no dump.

-------------------------------------------------------------------------------
NO GUARD MAY BE ADDED FOR THE EMPTY CASE (R-3)
-------------------------------------------------------------------------------

This scenario invites exactly the wrong instinct, so it is ruled out in writing.
The Python side must NOT gain an empty-batch short circuit, an early return when
the work file is empty, a "nothing to post" warning, a counter, a summary line, a
skipped phase or any new validation of the item count. Whatever the compiled
cycle does with zero transactions - including opening every file, running all
three phases, taking the at-end branch that performs `end-account` and `end-batch`
[general/gl072.cbl:L286-L289], and closing everything normally
[general/gl072.cbl:L440-L442] - is what must be reproduced, statement for
statement.

AND NO TEST HERE MAY ASSERT THAT SUCH A MESSAGE EXISTS. Asserting a diagnostic
the COBOL does not emit would itself be an added behaviour, and therefore a
defect. `test_no_empty_batch_special_case_was_added` is consequently a
BEHAVIOURAL assertion over the dumps and not a source scan.

-------------------------------------------------------------------------------
THE EIGHT-STAGE PROTOCOL, DRIVEN THROUGH THE ONE HELPER
-------------------------------------------------------------------------------

    1  seed.sh                     5  reset_db.sh
    2  run_cobol_scenario.sh       6  run_python_scenario.sh
    3  dump --side cobol           7  dump --side python
    4  normalize.py                8  diff_states.py

`harness/run_python_scenario.sh` performs stage 7 itself unless `--no-dump` is
given, and never runs `normalize.py` or `diff_states.py`. Agent Action Plan
section 0.4.3 requires that "no test reimplements the comparison protocol", so
every stage above is composed exactly once, in tests/conftest.py, and reached
here through the `protocol` fixture. NOTHING BELOW WRITES ITS OWN COMPARISON.

THE THREE-WAY EXIT CONTRACT OF STAGE 8, and the one conflation that must never
happen:

    0  the trees are identical, and stdout is EMPTY - zero bytes, not a banner
    1  a real behavioural difference, with a deterministic report
    2  THE COMPARISON COULD NOT BE PERFORMED - a missing tree, a missing table
       file, a malformed dump, a shape mismatch, a float, a duplicate primary
       key, a wrong key order, `row_count != len(rows)`, a ragged row, a null

Status 2 must surface as an ERROR and never as a pass: "a test that treats 'could
not compare' as 'no differences' is the single worst bug available in this tree."
IN THIS SCENARIO THE DISTINCTION IS EXISTENTIAL, because "both dumps are empty"
and "no dump was produced" look identical from the verdict alone. The mapping is
delivered structurally: tests/conftest.py raises `HarnessFaultError` for status 2
and for every stage whose failure destroys the evidence, and because that raise
happens inside the fixture below, pytest reports it as an ERROR. A real
difference reaches the test body and fails an `assert`, so it is a FAILURE. That
is why `test_dump_is_wellformed_on_both_sides` is NOT OPTIONAL here: it is the
test that distinguishes "correctly empty" from "never dumped".

The comparison is EXACT - no tolerance, no epsilon, no case- or
whitespace-insensitivity, no numeric coercion; `1` against `"1"` IS a difference.
Rows align by PRIMARY-KEY VALUE, never by position. The two labels are `cobol`
and `python`, never left and right. `--max-differences` truncates the report only:
it always prints the true total and never changes the exit status.

ALWAYS DUMP, THEN DECIDE THE STATUS. Agent Action Plan section 0.6.5, of a
run-aborting rejection: "The database effect is therefore the absence of
everything the later phases would have written." ABSENCE IS EVIDENCE, so the two
run stages' statuses are recorded and never allowed to skip the dump that follows
them. Every OTHER stage's failure does destroy the evidence, and those raise.

THREE EXIT CATEGORIES, KEPT DISTINCT: success, including a reproduced abort the
scenario declared; a behavioural difference, with the dump still taken; and a
harness fault - `argparse` status 2 meaning the runner built a bad command line,
a missing promoted flag, an unreachable database, malformed YAML, or DISAGREEING
SEED FINGERPRINTS. For this scenario `expected_status: [0]` means any non-zero
status is one of the last two, and the fingerprint cross-check is what tells them
apart.

THE HARD PROHIBITION ON COMMAND LINES. The promoted-flag spellings are
deliberately unfixed in the `acas_posting/cli/*` specifications, so this file
NEVER composes a command line, an argument vector or a spawned child process,
NEVER hard-codes an option name, and NEVER runs a `cli` route as a module itself.
`harness/run_python_scenario.sh` owns the option probe and fails harness-fault
when a required option is absent from the module it is about to drive.
`gl_post_cycle` promotes nothing, so the scenario declares NO answer key at all -
not
`irs_clear_postings`, not `payment_post_confirm`, not `gl080_proceed`, not
`disk_change_option` - and their absence is asserted.

-------------------------------------------------------------------------------
BOUNDING, NEVER IGNORING
-------------------------------------------------------------------------------

THE COMPARISON IS BOUNDED BY THE SCENARIO'S OWN `affected_tables` LIST AND BY
NOTHING ELSE. There is no ignore-list, no tolerance-list and no "known
difference" allowance anywhere in the diff path, and none is added here.

Three tables, alphabetically, and the order is part of the contract because the
seed fingerprint is written in it:

    GLBATCH-REC     carries the ANSWER to the central open question above
    GLLEDGER-REC    proves no balance moved - or records whatever
                    `end-account`'s `GL-Nominal-Rewrite` [general/gl072.cbl:L382]
                    actually did
    GLPOSTING-REC   the UNCHANGED WITNESS, additionally empty in the seed

Why the system tables are absent is bounding and not ignoring. The menu shell's
exit path persists three of them on the way out [general/general.cbl:L656-L691]:

    656  overrewrite.
    657       if       File-System-Used NOT = zero
    664                move     2 to File-Key-No       <- KEY 2, SYSDEFLT-REC
    667                move     4 to File-Key-No       <- KEY 4, SYSTOT-REC

with key 1 at L659-L663. The Python command line has no menu and never does this.
Sales and Purchase persist keys 1 and 4 only, never key 2, on every `load000`
call [sales/sales.cbl:L628-L657] with [sales/sales.cbl:L659-L660] and
[purchase/purchase.cbl:L621-L650] with [purchase/purchase.cbl:L652-L653]. A
census over all twelve in-scope programs finds ZERO `System-*` facade verbs, so
`SYSTEM-REC`, `SYSDEFLT-REC`, `SYSFINAL-REC` and `SYSTOT-REC` appear on no
scenario list - while `SYSTOT-REC` remains genuinely in scope for
`period_end_totals`, which is why nothing is ever blanket-excluded.

The four autogen tables - `SAAUTOGEN-REC`, `SAAUTOGEN-LINES-REC`,
`PUAUTOGEN-REC`, `PUAUTOGEN-LINES-REC` - are never seeded and never listed; both
runners assert after the run that all four are still empty. `sl830` runs only on
the COBOL side [sales/sales.cbl:L759] and Purchase's `pl830` is commented out
[purchase/purchase.cbl:L755-L758]. Irrelevant to a General Ledger scenario and
recorded only for consistency; those assertions live in the runners, not here.

-------------------------------------------------------------------------------
NORMALISATION DOES EXACTLY THREE THINGS, AND THERE IS NO FOURTH
-------------------------------------------------------------------------------

Delegated ENTIRELY to `harness/normalize.py`; nothing here reimplements or
extends it. The three jobs, and what each means for these three tables:

  1. TRAILING spaces in fixed-character columns, `rstrip(" ")`, trailing only -
     a COBOL alphanumeric `MOVE` is left-justified with right padding, so LEADING
     spaces are content - ASCII U+0020 only, by declared type including
     `char(1)`. Motivated by ANOMALY A-12, the width drift `pic x(24)`
     [copybooks/wsledger.cob:L27] to `PIC X(32)` [common/nominalMT.cbl:L299] to
     `` `LEDGER-NAME` char(32) `` [mysql/ACASDB.sql:L127]. The frozen schema has
     238 `char(` columns and zero `varchar(`. Here it touches
     `GLBATCH-REC.DESCRIPTION` `char(24)` [mysql/ACASDB.sql:L94] from
     [copybooks/wsbatch.cob:L45], `CONVENTION` and `BATCH-DEF-CODE` `char(2)`
     [mysql/ACASDB.sql:L96, L99], `BATCH-DEF-VAT` `char(1)`
     [mysql/ACASDB.sql:L100], and `GLLEDGER-REC.LEDGER-PLACE` `char(1)`.
  2. DECIMAL scale rendering AT THE DECLARED SCALE, which is NOT uniformly 2:
     68 columns at `(9,2)`, 57 at `(10,2)`, 17 at `(4,2)`, 12 at `(5,2)`, 4 at
     `(14,2)`, 2 at `(2,0)`, 2 at `(14,4)`, plus singletons.
     `GLBATCH-REC`'s four money columns are `decimal(14,2) unsigned`
     [mysql/ACASDB.sql:L90-L93], matching the UNSIGNED `pic 9(9)v99 comp-3` at
     [copybooks/wsbatch.cob:L41-L44]; `GLLEDGER-REC.LEDGER-BALANCE` is
     `decimal(10,2)` [mysql/ACASDB.sql:L128] from `pic s9(8)v99 comp-3`
     [copybooks/wsledger.cob:L28]. A ZERO MUST RENDER AT THE DECLARED SCALE ON
     BOTH SIDES, which is exactly the difference this scenario would otherwise
     expose spuriously. A value implying more places RAISES rather than rounds,
     because rounding there would hide a real finding.
  3. Two- versus four-digit date TEXT forms, under an EXPLICIT COLUMN ALLOW-LIST
     only: `GLPOSTING-REC.POST-DAT`, `IRSPOSTING-REC.POST4-DAT`,
     `PSIRSPOST-REC.IRS-POST-DAT`, `SYSTEM-REC.STATS-DATE-PERIOD` and
     `SALEDGER-REC.SALES-STATS-DATE`. `char(8)` DOES NOT IMPLY DATE -
     `PUITM5-REC.OI5-BATCH` and `SAITM3-REC.OI3-BATCH` are batch references and
     are excluded. AND `GLBATCH-REC.ENTERED`, `PROOFED`, `POSTED` and `STORED`
     ARE `int(8) unsigned` BINARY DAY NUMBERS [mysql/ACASDB.sql:L86-L89], from
     four `binary-long` fields [copybooks/wsbatch.cob:L36-L39], so JOB 3 MUST NOT
     TOUCH THEM. That matters directly to the central open question: whatever
     L376 writes to `POSTED` is an integer and is compared as an integer.

ANOMALY A-7 is dumped AS STORED and never repaired: the three independent guards
at [common/irspostingMT.cbl:L982-L987] make a partially-derived row reachable.
Not exercised by a General Ledger scenario; recorded for completeness.

-------------------------------------------------------------------------------
THE FIVE REJECTION CLASSES, AND WHY THIS SCENARIO EXERCISES NONE OF THEM
-------------------------------------------------------------------------------

Agent Action Plan section 0.8.1: "a single generic rejection path would fail this
directive." The five are distinct in their DATABASE EFFECT, not merely in their
disposition:

  1. CLEAN REJECTION, NO DATABASE EFFECT - `gl072` skips a posting whose batch
     number is non-numeric [general/gl072.cbl:L291-L292] and a record whose
     handler returned 999 [general/gl072.cbl:L306-L307], both entirely silent,
     with no message, counter or trace. ANOMALY A-13, whose verified locators are
     these rather than the Agent Action Plan's L289-L290 and L303-L304. Owned by
     tests/scenarios/test_mixed_accepted_rejected_batch.py.
  2. RUN-ABORTING REJECTION - the control-total mismatch; the effect is THE
     ABSENCE of everything the later phases would have written. Owned by
     tests/scenarios/test_control_total_mismatch_rejection.py.
  3. PARTIAL DATABASE EFFECT - the half-posted double entry
     [irs/irs030.cbl:L1635-L1652] (A-4) and the lost update on the two VAT
     control accounts [irs/irs030.cbl:L1602], [irs/irs030.cbl:L1612],
     [irs/irs030.cbl:L1704-L1708] (A-5). Owned by
     tests/scenarios/test_clean_batch_post_irs.py.
  4. FILE-ABANDONING REJECTION - a failure writing the posting record jumps
     straight to end of job [irs/irs030.cbl:L1673-L1678], and the partial state
     is COMMITTED, not rolled back.
  5. PERMANENTLY FAILING FACADE VERB - the transfer-file handler rejects
     read-indexed, rewrite, start and delete UNCONDITIONALLY at entry, each with
     `WE-Error 988` and `FS-Reply 99` [common/acas008.cbl:L299-L307] (A-6), so
     the published Rewrite verb can never succeed.

THE BOUNDARY, STATED EXPLICITLY: an empty batch RUNS TO COMPLETION with status 0.
It is not class 1, because no posting was skipped - there was none. It is not
class 2, because nothing aborted. It is none of classes 3 to 5, because no IRS
path and no failing verb is on this route. ANY TEST HERE THAT REPORTED A
"REJECTION" WOULD HAVE MIS-CLASSIFIED THE SCENARIO, and conflating "nothing to
do" with "rejected" is precisely the collapse the directive forbids.

-------------------------------------------------------------------------------
THE SEEDING AND SCHEMA CONSTRAINTS THIS FILE RELIES ON (R-3, R-4)
-------------------------------------------------------------------------------

Documented, never implemented here - every one belongs to a harness script.

NO DDL. `mysql/ACASDB.sql` is applied VERBATIM; it already carries all 33
`DROP TABLE IF EXISTS` beside its 33 `CREATE TABLE`, so re-applying the frozen
file IS the drop-and-recreate. It contains neither `CREATE DATABASE` nor `USE`,
so the database name must be supplied on the client command line.

AUTOCOMMIT MUST BE OFF DURING SEEDING, asserted rather than set.
[common/glbatchLD.cbl:L9-L13] verbatim: "This modules uses commit and rollback so
you MUST ensure that autocommit is OFF in the rdb settings. It is as default set
ON." Directly relevant here, because `batch.dat` is loaded by exactly that
loader.

`common/masterLD.sh` IS NEVER INVOKED. Its own header says "THIS SCRIPT HAS NOT
YET BEEN TESTED" [common/masterLD.sh:L4-L5]; all 24 loader lines
[common/masterLD.sh:L93-L116] omit the `;` before `fi`, so `bash -n` rejects the
file; and it ends by paging a log through `less`, which would block an unattended
run forever. It is FROZEN AND NOT FIXED. `harness/seed.sh` reproduces its
documented per-file contract [common/masterLD.sh:L44-L115] and checks loader exit
codes explicitly - 128 params unset, 64 RDB unset, 16 write error
[common/masterLD.sh:L37-L39] - with anything above 63 aborting the load.

R-4 ITEMS PRESERVED RATHER THAN FIXED: the `dfltLD` strict-versus-lenient exit
asymmetry, `if [ $rc != 0 ]` at [common/masterLD.sh:L83] against the `-gt 63`
tolerance the other three system-block loaders get; the charset caveat, `SET NAMES
utf8mb4` [mysql/ACASDB.sql:L16] against 33 tables declared
`DEFAULT CHARSET=utf8mb3 COLLATE=utf8mb3_general_ci`, with the maintainer's own
note at [mysql/ACASDB.sql:L9-L11]; the `tinyint(1) unsigned` display-width quirk
on `GLBATCH-REC.BATCH-STATUS` [mysql/ACASDB.sql:L83] and `CLEARED-STATUS`
[mysql/ACASDB.sql:L84]; and the `acas007`-versus-`acas008` `Open-Output`
divergence above.

THE CREDENTIAL PRECONDITION, stated because it decides whether the run happens at
all and fixable only outside this folder. The connection is carried INSIDE the
system record - `RDBMS-DB-Name` through `RDBMS-Socket`
[copybooks/wssystem.cob:L137-L144] - and each handler copies it into the
`RDB-Data` group before connecting, whose fields are `DB-Schema x(12)`,
`DB-UName x(12)`, `DB-UPass x(12)`, `DB-Host x(32)`, `DB-Socket x(64)` and
`DB-Port x(5)` [copybooks/wsfnctn.cob:L56-L62]. So THE USER AND PASSWORD ARE
LIMITED TO TWELVE CHARACTERS - a longer value is silently shortened by the MOVE,
and the two sides would then connect as different accounts - and the `ACAS_DB_*`
environment must EQUAL the `RDBMS-*` fields inside the seeded `system.dat`. No
credential value appears in this file. Note also that `general/general.cbl` never
reads the system record from the database: [general/general.cbl:L421] says the
code below it is bypassed "AS THE FILE WILL ALWAYS BE CURRENT" and that whole
block is commented out, and the menu reads its keys from the COBOL indexed file
only, after forcing `File-System-Used` to zero locally
[general/general.cbl:L386] and again at [general/general.cbl:L399] in case the
setup program has just run. So the staged `system.dat` must be a REAL COBOL
INDEXED FILE. (The scenario definition cites the banner at L422; measured, L422
is a blank comment line and L421 carries the text - the verified value is used
here, as docs/migration/anomaly-log.md section 8 does for the same class of
correction.)

STRICTLY SEQUENTIAL (R-3). No distributed test runner, no parallel runner and no
plugin that reorders execution - pyproject.toml's dependency manifest excludes
every one of them by name. Parallel scenario runs against one shared MariaDB
would break the seed, run, dump, reset, run, dump, diff protocol outright, and
posting order is load-bearing in this cycle.

-------------------------------------------------------------------------------
TRACEABILITY AND ARBITRATION (R-5, R-6)
-------------------------------------------------------------------------------

Anomalies named at their sites, with the anomaly log's VERIFIED locators: A-7,
A-12, A-13, A-14 - the nominal account is located by a SEQUENTIAL read
[general/gl072.cbl:L408], guarded at L407, so correctness depends entirely on
`gl071`'s output order - and A-15. Ambiguities referenced BY IDENTIFIER only:
`Q-EMPTY-BATCH-AT-END` for the empty-work-file `end-batch` and `end-account`
disposition, `Q-4` for the batch-record declared-length contradiction, and the
deliberate omission of `gl_end_of_cycle` from every scenario. Evidence per
scenario belongs in docs/migration/scenario-diff-evidence.md and the register in
docs/migration/anomaly-log.md.

THE REFERENCES ABOVE ARE TEXTUAL ONLY. Nothing here imports a migration document,
checks that one exists, or skips when one is absent: they are prose deliverables
and this file neither creates nor reads them.

THE GENERAL LEDGER CAVEAT. The maintainer records that he has not worked with
General since it was migrated to the current compiler [README.TXT:L50-L53], while
reporting the other ledgers as tested, and General contributes the majority of
the in-scope programs. So no expected value for this scenario may be derived from
documentation or from reasoning about intended behaviour: IF THE COMPILED CYCLE
BEHAVES SURPRISINGLY, THE SURPRISE IS THE SPECIFICATION (R-6). That applies with
unusual force here, because the behaviour of the compiled cycle on a
zero-transaction batch is genuinely unknown until it is run.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.scenario

SCENARIO = "empty_batch"


# ---------------------------------------------------------------------------
#  THE ONE FIXTURE
#
#  Everything the protocol needs is composed exactly once, in tests/conftest.py,
#  and reached through the `protocol` fixture - which applies the stack skip
#  BEFORE any stage can run, so COLLECTION SUCCEEDS ON A BARE HOST and each test
#  reports a precise SKIP rather than an error.
#
#  THE ERROR-VERSUS-FAILURE MAPPING IS DELIVERED BY DOING THE WORK HERE. Every
#  stage whose failure destroys the evidence - the seed, the reset, either
#  capture, either normalisation - and a stage-8 status of 2 raise
#  `HarnessFaultError` inside tests/conftest.py; raised from a fixture, pytest
#  reports that as an ERROR. A real behavioural difference reaches the test body
#  and fails an `assert`, so it is a FAILURE. That is the three-way contract of
#  the module docstring, realised structurally rather than by convention.
#
#  Function-scoped, deliberately. A module-scoped fixture cannot request the
#  function-scoped `protocol`, and the two alternatives are both worse: importing
#  tests/conftest.py directly would break the house convention that conftest is
#  reached through FIXTURES and never imported - which is what keeps R-1's
#  structural boundary structural - and memoising the run in module-level state
#  would let two tests in one session mean different things by "the diff". Agent
#  Action Plan section 0.8.4 sets no performance target and forbids optimising
#  for one, so each test is given its own complete, self-consistent run. Runs are
#  strictly sequential (R-3); nothing here is parallel.
#
#  The injected objects are annotated `object` because their precise
#  tests/conftest.py types cannot be named without a module-level import of that
#  module. Each parameter's real type is documented in the docstring that uses it.
# ---------------------------------------------------------------------------


@pytest.fixture
def empty_batch_parity(protocol: object) -> object:
    """Run all eight protocol stages for `empty_batch` and return the verdict.

    Args:
        protocol: tests/conftest.py's `Protocol` stage bundle. It applies the
            stack skip, so an unusable harness is a SKIP and never an error.

    Returns:
        The `ParityRun`: every stage result in execution order, both run stages,
        the stage-8 `DiffOutcome` and the artifact paths. `is_empty` is the pass
        condition and `tree` names what differed.

    Raises:
        HarnessFaultError: A stage whose failure destroys the evidence failed, or
            the comparison could not be performed at all. Reported as a test
            ERROR, never as a pass - in this scenario above all others, because
            "both dumps are empty" and "no dump was produced" look identical from
            the verdict alone.
    """
    return protocol.run_scenario_parity(SCENARIO)


# ---------------------------------------------------------------------------
#  THE PRECONDITIONS. No stack required: a scenario definition is a file on disk,
#  so these three collect and RUN on a bare host and fail loudly if the scenario
#  is ever edited into something other than an empty batch.
# ---------------------------------------------------------------------------


def test_scenario_definition_preconditions(
    scenario_loader: object, pinned_clock: object
) -> None:
    """Every pin this scenario's result depends on, asserted explicitly.

    THE FALSE-PASS TRAP IS THE REASON THIS TEST EXISTS. `file_system_used` is the
    one pin whose loss cannot be seen in the verdict:
    `88 FS-Cobol-Files-Used value zero` [copybooks/wssystem.cob:L112-L114] makes
    every handler bypass MySQL entirely [common/acas007.cbl:L316-L320], both
    dumps come back empty and the diff exits 0. This scenario legitimately
    expects very little change, so that false pass is nearly invisible.

    `cyclea` must be non-zero for a second, independent reason as well: the menu
    diverts into interactive setup on a zero cycle, which on an unattended runner
    is an indefinite hang rather than an error.

    Args:
        scenario_loader: tests/conftest.py's `scenario_definition`, which parses
            with `yaml.safe_load` so a data file cannot construct Python objects.
        pinned_clock: The project-wide `PinnedRunDate`, carrying both observables
            - the text `to-day pic x(10)` and the binary `Run-Date binary-long`
            [copybooks/wssystem.cob:L67].
    """
    definition = scenario_loader(SCENARIO)

    assert definition["name"] == SCENARIO, (
        f"the definition at harness/scenarios/{SCENARIO}.yaml names itself "
        f"{definition['name']!r}. The name composes every evidence path, so a "
        f"disagreement would file this run's dumps under another scenario."
    )

    # ONE operation, and it is the General Ledger posting cycle - the migration of
    # `load08.` [general/general.cbl:L805-L815], which dispatches gl070, then the
    # `ws-term-code = 5` gate at L810-L811, then gl071, then gl072.
    assert definition["subsystem"] == "general", (
        f"the subsystem is {definition['subsystem']!r}; the empty-batch case is a "
        f"GENERAL LEDGER scenario, and the oracle-side runner refuses a run whose "
        f"subsystem and operation disagree."
    )
    assert definition["operation"] == "gl_post_cycle", (
        f"the operation is {definition['operation']!r}, not gl_post_cycle. Only "
        f"that operation walks batch check and pre-process, the sort, and the "
        f"transaction update [general/general.cbl:L805-L815]."
    )
    assert list(definition["operations"]) == ["gl_post_cycle"], (
        f"the operation sequence is {list(definition['operations'])!r}. Exactly "
        f"one operation runs here: the singular `operation` key and this "
        f"sequence must resolve to the same single operation, because the two "
        f"runners read different keys."
    )

    # `expect.term_code: 0` in the folder brief is spelt `expected_status` in the
    # file, positionally against `operations`. Zero is PROVABLE: the batch is
    # seeded CLOSED, so [general/gl070.cbl:L314-L315] never trips and the raise at
    # [general/gl070.cbl:L289] inside L287-L290 never runs; term code 8 belongs to
    # sl055 and pl055, which this operation never dispatches and which are
    # unreachable under file_system_used 1 anyway.
    assert list(definition["expected_status"]) == [0], (
        f"the declared terminal status is {list(definition['expected_status'])!r} "
        f"and must be [0]. Five is the only code any program on this route can "
        f"raise [general/gl070.cbl:L289], and a closed batch cannot raise it."
    )

    # `gl_post_cycle` PROMOTES NOTHING, so no answer key may be declared. Each of
    # these belongs to a route this scenario never takes.
    for answer_key in (
        "answers",
        "irs_clear_postings",
        "payment_post_confirm",
        "gl080_proceed",
        "disk_change_option",
    ):
        assert answer_key not in definition, (
            f"the definition declares {answer_key!r}, but the General Ledger "
            f"posting cycle asks nothing interactively. Every answer key belongs "
            f"to the IRS, payment or end-of-cycle routes; declaring one here "
            f"would feed the run an input the frozen cycle does not take."
        )

    system = definition["system"]

    # DEFENCE 1 OF TWO against an empty diff that means nothing. See the docstring.
    assert system["file_system_used"] == 1, (
        f"system.file_system_used is {system['file_system_used']!r} and must be "
        f"1. `88 FS-Cobol-Files-Used value zero` "
        f"[copybooks/wssystem.cob:L112-L114] makes every handler skip MySQL "
        f"altogether [common/acas007.cbl:L316-L320], so BOTH dumps come back "
        f"empty and the comparison exits 0 - a SILENT FALSE PASS, and in this "
        f"scenario an almost invisible one."
    )
    assert isinstance(system["file_system_used"], int) and not isinstance(
        system["file_system_used"], bool
    ), (
        f"system.file_system_used parsed as "
        f"{type(system['file_system_used']).__name__}. It mirrors "
        f"`File-System-Used pic 9` [copybooks/wssystem.cob:L112], a one-digit "
        f"numeric field, and must stay an integer (R-2)."
    )

    # THE IRS FAN-OUT SWITCH, pinned explicitly rather than defaulted.
    # [copybooks/wssystem.cob:L179-L181] declares `05 IRS-Instead pic x.` with
    # `88 IRS-Used value "Y"` and `88 IRS-Both-Used value "B"`. THE THIRD STATE -
    # a space - HAS NO CONDITION NAME AT ALL: both predicates are simply False,
    # which is General Ledger only. Agent Action Plan section 0.6.4: leaving it at
    # a default "would make the affected-table list ambiguous".
    assert system["irs_instead"] == " ", (
        f"system.irs_instead is {system['irs_instead']!r} and must be a single "
        f"space - the third, unnamed state of "
        f"[copybooks/wssystem.cob:L179-L181], for which both `IRS-Used` and "
        f"`IRS-Both-Used` are False. Any other value would fan postings out to "
        f"the IRS tables and widen the affected-table list."
    )
    assert definition["irs_instead"] == system["irs_instead"], (
        f"the flat mirror `irs_instead` is {definition['irs_instead']!r} while "
        f"`system.irs_instead` is {system['irs_instead']!r}. The oracle-side "
        f"runner reads the flat key, so the two halves of one fact must agree."
    )

    # `Bcycle` must equal this, or both cycle filters skip the batch and the run
    # touches nothing - which for THIS scenario is nearly indistinguishable from
    # the intended outcome. [general/gl070.cbl:L312-L313] and L457-L458.
    assert system["cyclea"] != 0, (
        f"system.cyclea is {system['cyclea']!r}. A zero cycle makes the menu "
        f"divert into interactive setup, which on an unattended runner hangs "
        f"indefinitely, and it would leave the seeded batch's `Bcycle` "
        f"[copybooks/wsbatch.cob:L34] matching nothing."
    )

    # Inert on this route: no scenario drives `gl_end_of_cycle`, which is the only
    # operation that consumes the period. Asserted so the pin stays visible.
    assert system["period"] == 1, (
        f"system.period is {system['period']!r}. It is inert here - only "
        f"gl_end_of_cycle consumes it, and no scenario drives that operation - "
        f"but it is pinned so two runs cannot differ in it."
    )

    # THE PINNED CLOCK, both observables, and the flat mirrors the oracle-side
    # runner reads. This is the pin that makes the central open question
    # answerable: if [general/gl072.cbl:L376] `move run-date to posted` fires on
    # the empty batch, the stamped value is deterministic.
    clock = definition["clock"]
    assert clock["to_day"] == pinned_clock.to_day, (
        f"the scenario pins to-day {clock['to_day']!r} while the project pin is "
        f"{pinned_clock.to_day!r}. `to-day pic x(10)` is a linkage parameter in "
        f"DD/MM/CCYY form and the two must be one fact."
    )
    assert clock["run_date"] == pinned_clock.run_date, (
        f"the scenario pins Run-Date {clock['run_date']!r} while the project pin "
        f"is {pinned_clock.run_date!r}. `05  Run-Date        binary-long.` "
        f"[copybooks/wssystem.cob:L67] is a REAL column and is therefore visible "
        f"in a dump, so a one-day shift would read as a posting difference."
    )
    assert definition["run_date_text"] == pinned_clock.to_day, (
        f"the flat mirror run_date_text is {definition['run_date_text']!r}, not "
        f"{pinned_clock.to_day!r}. The oracle-side runner reads the flat keys."
    )
    assert definition["run_date_binary"] == pinned_clock.run_date, (
        f"the flat mirror run_date_binary is "
        f"{definition['run_date_binary']!r}, not {pinned_clock.run_date}."
    )
    assert isinstance(definition["run_date_binary"], int) and not isinstance(
        definition["run_date_binary"], bool
    ), (
        f"run_date_binary parsed as "
        f"{type(definition['run_date_binary']).__name__}. The binary run date is "
        f"a whole day count from a 1600-12-31 epoch and must be an integer: no "
        f"accounting or date value in this tree passes through a real number "
        f"(R-2)."
    )
    assert isinstance(definition["run_date_text"], str), (
        f"run_date_text parsed as {type(definition['run_date_text']).__name__}. "
        f"It must stay a ten-character string, the width of `to-day pic x(10)`, "
        f"rather than being parsed as some other scalar."
    )

    # UK dd/mm/yyyy, the form `to-day` is written in.
    assert system["date_form"] == 1, (
        f"system.date_form is {system['date_form']!r} and must be 1, the UK "
        f"dd/mm/yyyy form the pinned text {pinned_clock.to_day!r} is written in."
    )
    assert definition["date_form"] == system["date_form"], (
        f"the flat mirror date_form is {definition['date_form']!r} while "
        f"system.date_form is {system['date_form']!r}; the two must agree."
    )


def test_seed_has_exactly_three_files_and_no_posting_dat(
    scenario_loader: object,
) -> None:
    """`empty_batch` IS DEFINED BY THE ABSENCE OF `posting.dat`.

    Isolated from the other preconditions so that its failure message can say
    only that. Three files are seeded - `system.dat` driving the four-loader
    system block [common/masterLD.sh:L51-L87], `ledger.dat` driving `nominalLD`
    [common/masterLD.sh:L103] and `batch.dat` driving `glbatchLD`
    [common/masterLD.sh:L94]. A fourth would drive `glpostingLD`
    [common/masterLD.sh:L109] and would destroy the scenario: `GLPOSTING-REC`
    would no longer start empty, `gl070`'s posting read would no longer hit
    end-of-file on its first attempt [general/gl070.cbl:L487-L488], `gl071` would
    have something to sort and `gl072` would not take its at-end branch.

    This is the ONLY scenario in the set with three seed files.

    Args:
        scenario_loader: tests/conftest.py's `scenario_definition`.
    """
    definition = scenario_loader(SCENARIO)
    seed = definition["seed"]
    files = list(seed["files"])

    assert files == ["system.dat", "ledger.dat", "batch.dat"], (
        f"the seed list is {files!r} and must be exactly "
        f"['system.dat', 'ledger.dat', 'batch.dat'], in that order. The frozen "
        f"script seeds the system block first and unconditionally "
        f"[common/masterLD.sh:L50-L88], and it is `system.dat` that carries "
        f"`Run-Date` [copybooks/wssystem.cob:L67] and the fan-out switch "
        f"[copybooks/wssystem.cob:L179-L181]."
    )

    # STATED SEPARATELY AND DELIBERATELY: this one assertion encodes "empty".
    assert "posting.dat" not in files, (
        f"posting.dat is declared in the seed list {files!r}. `empty_batch` IS "
        f"DEFINED BY THE ABSENCE OF posting.dat - that absence is what leaves the "
        f"batch with no transactions for gl070's phase 2 to explode, nothing for "
        f"gl071 to sort [general/gl071.cbl:L172-L178] and an immediately-at-end "
        f"work file for gl072 [general/gl072.cbl:L286]. Seeding it would turn "
        f"this scenario into a clean-batch post and silence the one question it "
        f"exists to ask."
    )

    assert list(definition["seed_files"]) == files, (
        f"the flat mirror seed_files is {list(definition['seed_files'])!r} while "
        f"seed.files is {files!r}. harness/seed.sh reads the flat key, so a "
        f"divergence would seed something other than what this scenario claims."
    )
    assert definition["seed_dir"] == seed["data_dir"], (
        f"the flat mirror seed_dir is {definition['seed_dir']!r} while "
        f"seed.data_dir is {seed['data_dir']!r}. The fixture directory is what "
        f"makes the seeded state provably attributable to this scenario."
    )

    # THE EIGHT FORBIDDEN FLAT FILES. Every one is a name the frozen loader script
    # recognises, and every one targets an OUT-OF-SCOPE table, so loading it would
    # widen the comparison past the cycle under test.
    forbidden = {
        "delfolio.dat": "delfolioLD [common/masterLD.sh:L95]",
        "delinvno.dat": "sldelinvnosLD [common/masterLD.sh:L96]",
        "delivery.dat": "deliveryLD [common/masterLD.sh:L97]",
        "pay.dat": "paymentsLD [common/masterLD.sh:L106]",
        "plautogen.dat": "plautogenLD [common/masterLD.sh:L108]",
        "slautogen.dat": "slautogenLD [common/masterLD.sh:L113]",
        "staudit.dat": "auditLD [common/masterLD.sh:L114]",
        "stockctl.dat": "stockLD [common/masterLD.sh:L115]",
    }
    for name, loader in sorted(forbidden.items()):
        assert name not in files, (
            f"{name} is declared in the seed list. Its loader is {loader}, whose "
            f"table is one of the eleven the posting cycle never touches, so the "
            f"differ would be handed rows no in-scope program can account for."
        )


def test_affected_tables_are_in_scope_and_alphabetical(
    scenario_loader: object, in_scope_table_names: object
) -> None:
    """The three tables that BOUND the comparison, and their declared order.

    `GLBATCH-REC` carries the answer to the central open question - whatever
    `end-batch` [general/gl072.cbl:L372-L377] did on an immediately-at-end read.
    `GLLEDGER-REC` proves no balance moved, or records whatever `end-account`'s
    `GL-Nominal-Rewrite` [general/gl072.cbl:L382] actually did. `GLPOSTING-REC` is
    the UNCHANGED WITNESS: `gl072` issues zero `GL-Posting-*` verbs and `gl070` is
    read-only, and here it is additionally empty in the seed.

    THE ORDER IS LOAD-BEARING, not a matter of taste: each side writes its seed
    fingerprint as one line per table IN THIS ORDER, and a disagreement between
    the two is a HARNESS FAULT that outranks any behavioural finding.

    Args:
        scenario_loader: tests/conftest.py's `scenario_definition`.
        in_scope_table_names: The 22 in-scope names, read from
            `harness/dump_tables.py`'s own inventory - the single definition of it
            in this repository (R-4). Never restated here.
    """
    definition = scenario_loader(SCENARIO)
    tables = list(definition["affected_tables"])

    assert tables == ["GLBATCH-REC", "GLLEDGER-REC", "GLPOSTING-REC"], (
        f"the affected-table list is {tables!r}. The General Ledger posting "
        f"cycle can touch exactly these three: gl072's eight facade verbs reach "
        f"the batch and the nominal ledger [general/gl072.cbl:L276-L277, L377, "
        f"L382, L408, L441-L442, L454] and gl070 reads the posting file "
        f"[general/gl070.cbl:L481, L486, L466]."
    )
    assert tables == sorted(tables), (
        f"the affected-table list {tables!r} is not alphabetical. The order is "
        f"part of the contract: the seed fingerprint is written in it on both "
        f"sides and a mismatch is reported as a harness fault."
    )
    assert len(tables) == len(set(tables)), (
        f"the affected-table list {tables!r} names a table twice, which would "
        f"dump and compare it twice and double-count any finding."
    )

    known = set(in_scope_table_names)
    for table in tables:
        assert table in known, (
            f"{table!r} is not one of the 22 in-scope tables. The eleven "
            f"out-of-scope tables are never dumped: no in-scope program writes "
            f"them, so any row there is unattributable."
        )



# ---------------------------------------------------------------------------
#  THE STATE-PARITY TESTS. Each requires the harness/ Compose stack, which the
#  `protocol` fixture behind `empty_batch_parity` skips on when it is unusable.
# ---------------------------------------------------------------------------


def test_empty_batch_state_parity(
    empty_batch_parity: object, harness: object
) -> None:
    """THE HEADLINE: the two cycles left the three bounded tables identical.

    Agent Action Plan section 0.8.5: "the diff must be empty". Section 0.6.6
    earns the right to trust that verdict - "a non-empty diff is always a real
    behavioral difference and never an artefact of the comparison" - because
    every in-scope table has a single-column primary key, zero secondary indexes,
    no TIMESTAMP column and no AUTO_INCREMENT, so the capture is
    `SELECT * FROM <table> ORDER BY <primary key>` with no tie-breaking, no
    timestamp masking and no surrogate-key remapping.

    THE VERDICT IS ASKED, NEVER RECOMPUTED. `TreeDiff.is_empty` is the one cheap
    question, and `render` is the same deterministic report the evidence document
    cites.

    Args:
        empty_batch_parity: The completed `ParityRun`.
        harness: The three harness modules, loaded by explicit file path (R-1).
    """
    run = empty_batch_parity

    assert run.is_empty, (
        f"THE MIGRATED CYCLE DIVERGED FROM THE COMPILED ORACLE on the empty "
        f"batch: {run.tree.total_differences} finding(s) across "
        f"{len(run.tables)} bounded table(s).\n"
        f"{harness.diff_states.render(run.tree)}\n"
        f"  Each line is `<TABLE>  <finding>  cobol=... python=...`; rows are "
        f"aligned by primary-key VALUE and the comparison is exact, so `1` "
        f"against `\"1\"` is a difference. The report is also at "
        f"{run.outcome.report}.\n"
        f"  WHATEVER THE ORACLE DID IS CORRECT (R-6). If the oracle stamped the "
        f"empty batch cleared and posted [general/gl072.cbl:L372-L377] and the "
        f"Python cycle did not, the defect is on the Python side - a guard, a "
        f"short circuit or an early return over the empty work file, which R-3 "
        f"forbids outright. See ambiguity Q-EMPTY-BATCH-AT-END.\n"
        f"{run.describe()}"
    )


def test_affected_tables_are_byte_identical_to_the_seed(
    empty_batch_parity: object, harness: object
) -> None:
    """NO SPURIOUS ROW, NO DROPPED ROW - and the seed demonstrably landed.

    The folder requirement asks that the affected tables come back "byte-identical
    to the seed - no spurious row, no counter bump, no status change". IT CARRIES
    ONE EXPLICIT CAVEAT, and the caveat is the whole subtlety of this scenario:
    whatever `gl072`'s at-end branch legitimately performed - `end-account` then
    `end-batch` [general/gl072.cbl:L286-L289] - IS NOT A SPURIOUS CHANGE. It is
    the specification. So this test asserts "no change beyond whatever the
    compiled cycle itself performed, and the two sides agree exactly", and NEVER
    a predicted value.

    What it adds beyond the headline is the structural half of that claim, stated
    per table: the two sides agree on the row count, and the tables the seed
    filled came back WITH ROWS. The second half is the corroboration that an
    empty verdict here is real rather than vacuous - a run that never connected
    would leave every table at zero and still diff clean.

    Args:
        empty_batch_parity: The completed `ParityRun`.
        harness: The three harness modules (R-1).
    """
    run = empty_batch_parity
    by_table = {entry.table: entry for entry in run.tree.tables}

    assert sorted(by_table) == sorted(run.tables), (
        f"the comparison covered {sorted(by_table)!r} but the scenario bounds it "
        f"to {sorted(run.tables)!r}. Bounding is done by the affected-table list "
        f"and by nothing else - there is no ignore-list anywhere in the diff "
        f"path - so a table missing from the verdict was never compared."
    )

    for table in run.tables:
        entry = by_table[table]

        assert entry.in_cobol and entry.in_python, (
            f"{table} was dumped on only one side (cobol={entry.in_cobol}, "
            f"python={entry.in_python}). A MISSING DUMP IS NOT AN EMPTY DIFF; it "
            f"means the capture could not be taken for that side."
        )
        assert not entry.missing_in_cobol, (
            f"{table}: the Python cycle produced {len(entry.missing_in_cobol)} "
            f"row(s) the oracle did not - keys {list(entry.missing_in_cobol)!r}. "
            f"A SPURIOUS ROW on an empty batch means the Python side wrote "
            f"something the compiled cycle never wrote."
        )
        assert not entry.missing_in_python, (
            f"{table}: the oracle produced {len(entry.missing_in_python)} row(s) "
            f"the Python cycle did not - keys {list(entry.missing_in_python)!r}."
        )
        assert not entry.row_count_differs, (
            f"{table}: row counts disagree - cobol={entry.cobol_row_count}, "
            f"python={entry.python_row_count}. Nothing on this route inserts or "
            f"deletes a row: gl070 is read-only throughout "
            f"[general/gl070.cbl:L303, L308, L321, L342, L347, L440, L448, L453, "
            f"L466, L473, L481, L486] and gl072 only rewrites "
            f"[general/gl072.cbl:L377, L382]. Note that "
            f"`common/acas007.cbl`'s open-for-output CANNOT wipe the batch table: "
            f"its delete-all lines are commented out at "
            f"[common/acas007.cbl:L308-L309], unlike the active "
            f"[common/acas008.cbl:L316]."
        )
        assert not entry.columns_differ, (
            f"{table}: the two column lists disagree. Rows are POSITIONAL within "
            f"a dump, so a column list in another order has no meaningful "
            f"alignment and the values compared would not be the same fields."
        )
        assert not entry.value_differences, (
            f"{table}: {entry.value_difference_count} column value(s) differ "
            f"across {len(entry.value_differences)} row(s).\n"
            f"{harness.diff_states.render_table(entry)}\n"
            f"  NO VALUE IS PREDICTED BY THIS TEST. The two sides must agree; "
            f"which value they agree ON is the oracle's to decide (R-6)."
        )

    # THE CORROBORATION. `batch.dat` [common/masterLD.sh:L94] and `ledger.dat`
    # [common/masterLD.sh:L103] were both seeded, so both tables must hold rows on
    # both sides. Zero everywhere is the signature of a run that never reached
    # MySQL - the `file_system_used` trap - or of a seed that never landed.
    for table in ("GLBATCH-REC", "GLLEDGER-REC"):
        entry = by_table[table]
        assert entry.cobol_row_count > 0 and entry.python_row_count > 0, (
            f"{table} came back EMPTY on at least one side "
            f"(cobol={entry.cobol_row_count}, python={entry.python_row_count}), "
            f"yet this scenario seeds it. AN EMPTY DIFF OVER EMPTY TABLES PROVES "
            f"NOTHING: it is exactly what a run that never connected, a seed that "
            f"never landed or `system.file_system_used: 0` "
            f"[copybooks/wssystem.cob:L112-L114] would produce. Check the seed "
            f"fingerprints under {run.paths.run_logs} before reading any verdict "
            f"in this file."
        )


def test_glposting_rec_is_empty_on_both_sides(
    empty_batch_parity: object, harness: object
) -> None:
    """`GLPOSTING-REC` is the UNCHANGED WITNESS, and here it is empty as well.

    Two independent reasons, and the table must satisfy both. First, no
    `posting.dat` was seeded, so the table starts as the freshly applied schema
    created it. Second, NOTHING ON THIS ROUTE CAN WRITE IT: `gl072` issues eight
    facade verbs and not one is a `GL-Posting-*` verb - `GL-Batch-Open` L276,
    `GL-Nominal-Open` L277, `GL-Batch-Rewrite` L377, `GL-Nominal-Rewrite` L382,
    `GL-Nominal-Read-Next` L408, `GL-Batch-Close` L441, `GL-Nominal-Close` L442,
    `GL-Batch-Read-Next` L454, all in [general/gl072.cbl] - and `gl070` only ever
    opens the posting file for INPUT [general/gl070.cbl:L481], reads it
    [general/gl070.cbl:L486] and closes it [general/gl070.cbl:L466].

    Corroborated by the program's own declaration: `gl072` carries a block of
    one-byte dummies purely so the linker resolves the copybook's full verb set
    [general/gl072.cbl:L135-L155], and the posting record is one of them -
    `03  WS-Posting-Record      pic x.` at [general/gl072.cbl:L140]. Agent Action
    Plan section 0.4.3 records that the whole block maps to nothing in Python.

    Args:
        empty_batch_parity: The completed `ParityRun`.
        harness: The three harness modules (R-1).
    """
    run = empty_batch_parity
    diff_states = harness.diff_states
    table = "GLPOSTING-REC"

    for side in diff_states.SIDES:
        path = run.paths.normalized_dir(side) / diff_states.dump_filename(table)
        dump = diff_states.load_dump(path)

        assert dump["row_count"] == 0, (
            f"{side}: {table} holds {dump['row_count']} row(s) at {path}. It is "
            f"seeded EMPTY - no posting.dat is declared - and no program on this "
            f"route can write it: gl072 issues zero `GL-Posting-*` verbs and "
            f"gl070 opens the posting file for input only "
            f"[general/gl070.cbl:L481]. A row here means either the seed loaded "
            f"posting.dat after all or something wrote through a verb the cycle "
            f"does not use."
        )
        assert dump["rows"] == [], (
            f"{side}: {table} declares row_count 0 but carries "
            f"{len(dump['rows'])} row(s) at {path}. `row_count == len(rows)` is "
            f"part of the dump contract, and a dump that contradicts itself "
            f"cannot produce a verdict."
        )


def test_batch_disposition_is_whatever_the_oracle_produced(
    empty_batch_parity: object, harness: object
) -> None:
    """THE CENTRAL OPEN QUESTION - asserted as AGREEMENT, never as a value.

    `gl072`'s first read of the sorted work file hits at end
    [general/gl072.cbl:L283-L289]:

        286       read     post-trans  at end
        287                perform  end-account
        288                perform  end-batch
        289                go to    end-run.

    and `end-batch` stamps and rewrites [general/gl072.cbl:L372-L377]:

        372  end-batch.
        375       move     1  to  cleared-status.
        376       move     run-date  to  posted.
        377       perform  GL-Batch-Rewrite.

    with `save-batch` still zero [general/gl072.cbl:L281]. WHETHER
    `CLEARED-STATUS` BECOMES 1 AND WHETHER `POSTED` RECEIVES THE RUN DATE IS
    DETERMINED BY THE ORACLE AND NOT BY THIS TEST. Nothing here predicts either;
    the assertion is that the two sides produced the SAME `GLBATCH-REC`, whatever
    it is. The question is filed as ambiguity `Q-EMPTY-BATCH-AT-END`, and anomaly
    A-15's competing record lengths [copybooks/wsbatch.cob:L7-L9] are filed as
    `Q-4`, because whether the declared length or the field sum governs decides
    the alignment of exactly the trailing fields at issue - `Batch-Status`
    [copybooks/wsbatch.cob:L25-L27], `Cleared-Status`
    [copybooks/wsbatch.cob:L29-L32] and the four `binary-long` dates
    [copybooks/wsbatch.cob:L36-L39].

    Comparing the two dump objects WHOLE is what makes the assertion complete
    without predicting anything: the five keys, the column list, the row count and
    every row must match.

    Args:
        empty_batch_parity: The completed `ParityRun`.
        harness: The three harness modules (R-1).
    """
    run = empty_batch_parity
    diff_states = harness.diff_states
    table = "GLBATCH-REC"

    dumps = {}
    for side in diff_states.SIDES:
        path = run.paths.normalized_dir(side) / diff_states.dump_filename(table)
        dumps[side] = diff_states.load_dump(path)

    cobol_side, python_side = diff_states.SIDES
    assert dumps[cobol_side] == dumps[python_side], (
        f"{table} DIFFERS BETWEEN THE TWO SIDES, so the two cycles reached "
        f"different conclusions about the empty batch.\n"
        f"  cobol : {dumps[cobol_side]}\n"
        f"  python: {dumps[python_side]}\n"
        f"  THE ORACLE'S ANSWER IS THE SPECIFICATION (R-6). Do not 'fix' the "
        f"Python side toward whichever disposition looks more correct: reproduce "
        f"[general/gl072.cbl:L286-L289] and [general/gl072.cbl:L372-L377] "
        f"statement for statement and record the outcome under ambiguity "
        f"Q-EMPTY-BATCH-AT-END. `POSTED` is `int(8) unsigned` "
        f"[mysql/ACASDB.sql:L88] from `binary-long` "
        f"[copybooks/wsbatch.cob:L38], so it is compared as an integer, and the "
        f"pinned run date is what makes it deterministic if L376 fires at all."
    )

    entry = {item.table: item for item in run.tree.tables}[table]
    assert entry.is_empty, (
        f"{table}: {entry.total_differences} finding(s) from the comparison "
        f"itself, although the two dump objects compared equal above - which "
        f"means the trees changed between the two reads and neither view can be "
        f"trusted.\n{harness.diff_states.render_table(entry)}"
    )


def test_no_empty_batch_special_case_was_added(
    empty_batch_parity: object, harness: object
) -> None:
    """NO EMPTY-CASE GUARD, SHORT CIRCUIT, EARLY RETURN OR WARNING MAY EXIST.

    R-3 forbids added validation, and this is the file most tempted to add it. The
    Python side must NOT gain an empty-batch short circuit, an early return when
    the work file is empty, a "nothing to post" warning, a counter or a skipped
    phase. If the compiled cycle opens every file, walks all three phases, takes
    the at-end branch that performs `end-account` and `end-batch`
    [general/gl072.cbl:L286-L289] and closes everything normally
    [general/gl072.cbl:L440-L442], SO MUST THE PYTHON CYCLE.

    THIS IS A BEHAVIOURAL ASSERTION, NOT A SOURCE SCAN, and it deliberately does
    NOT assert that any diagnostic exists: asserting a message the COBOL does not
    emit would itself be an added behaviour, and therefore a defect. A guard on
    the Python side is observable precisely because it would SKIP the at-end work
    the oracle performed, so it shows up as a `GLBATCH-REC` or `GLLEDGER-REC`
    difference; a counter or summary row would show up as an extra row or a
    changed column. Both are checked here, per table, with the guard hypothesis
    named in the message.

    [general/gl072.cbl:L443] `call "SYSTEM" using Print-Report.` is the one thing
    the cycle does that must NOT appear in a dump: it is a spool-out with no
    database effect, excluded by Agent Action Plan section 0.2.2.

    Args:
        empty_batch_parity: The completed `ParityRun`.
        harness: The three harness modules (R-1).
    """
    run = empty_batch_parity

    for entry in run.tree.tables:
        assert entry.is_empty, (
            f"{entry.table}: {entry.total_differences} finding(s) on a run that "
            f"posts nothing.\n"
            f"{harness.diff_states.render_table(entry)}\n"
            f"  THE FIRST HYPOTHESIS TO TEST IS AN ADDED EMPTY-CASE GUARD. A "
            f"short circuit, an early return over the empty work file or a "
            f"skipped phase on the Python side would omit exactly the at-end "
            f"work [general/gl072.cbl:L287-L288] that the oracle performed, and "
            f"would show up here. R-3 forbids adding one even if it produced the "
            f"same table state today, because it would produce a DIFFERENT state "
            f"the moment the Q-EMPTY-BATCH-AT-END arbitration comes back as 'the "
            f"batch is stamped'."
        )
        assert entry.rows_compared, (
            f"{entry.table}: the rows were not compared at all, so the absence "
            f"of a finding says nothing. That is a comparison that could not be "
            f"performed, never a pass (R-6)."
        )


def test_run_completes_with_term_code_zero(
    empty_batch_parity: object, protocol: object, scenario_loader: object
) -> None:
    """Both cycles reached the SAME terminal disposition, and it is the declared 0.

    Zero is provable rather than merely expected. Five is the only code any
    program on this route can raise - `move 5 to ws-term-code`
    [general/gl070.cbl:L289], inside the block at L287-L290 - and it is reached
    only when phase 1 meets a batch left OPEN in the current cycle
    [general/gl070.cbl:L314-L315]. This scenario seeds the batch CLOSED
    (`88 Status-Closed value 1` [copybooks/wsbatch.cob:L25-L27]), so the detector
    never trips and the gate at [general/general.cbl:L810-L811] never fires -
    which is what lets `gl071` and `gl072` run at all.

    Term code 8 is unreachable twice over: it is set only by
    [sales/sl055.cbl:L344] and [purchase/pl055.cbl:L286], both inside
    `if FS-Cobol-Files-Used` ([sales/sl055.cbl:L326],
    [purchase/pl055.cbl:L266]) while the scenario pins `file_system_used: 1`, and
    neither program is dispatched by `gl_post_cycle`.

    A STATUS OF 2 IS A HARNESS FAULT AND NEVER A DIFFERENCE: `argparse` exits 2 on
    a usage error, which in this family means the runner built a bad command line.
    The three dispositions are kept distinct because conflating them is the worst
    bug available here - a run that aborted behaviourally still left evidence to
    compare, whereas a runner handed a bad command line left none. The
    evidence-destroying stages are mapped to ERRORs by the fixture; a run stage's
    own fault status is surfaced here as a clearly labelled failure, because the
    protocol deliberately keeps the capture in that case (absence is evidence).

    Args:
        empty_batch_parity: The completed `ParityRun`.
        protocol: tests/conftest.py's stage bundle, for `classify_run`.
        scenario_loader: tests/conftest.py's `scenario_definition`.
    """
    run = empty_batch_parity
    definition = scenario_loader(SCENARIO)
    operation = definition["operation"]
    expected = list(definition["expected_status"])[0]

    cobol_disposition = protocol.classify_run(run.cobol_run, operation=operation)
    python_disposition = protocol.classify_run(run.python_run, operation=operation)

    assert run.cobol_run.returncode == expected, (
        f"THE ORACLE ended with status {run.cobol_run.returncode}, not the "
        f"declared {expected}; its disposition is {cobol_disposition!r}. A "
        f"status of 5 would mean gl070 found a batch left open "
        f"[general/gl070.cbl:L289] - which cannot happen with a batch seeded "
        f"closed - and any other non-zero status is a HARNESS FAULT rather than a "
        f"behavioural finding: the question was never asked.\n"
        f"{run.cobol_run.describe()}"
    )
    assert run.python_run.returncode == expected, (
        f"THE MIGRATED CYCLE ended with status {run.python_run.returncode}, not "
        f"the declared {expected}; its disposition is {python_disposition!r}, "
        f"while the oracle ended {run.cobol_run.returncode}. "
        f"`acas_posting/cli/args.py`'s `exit_status_for` returns the term code "
        f"itself, so 5 would be the open-batch abort and anything else is a "
        f"harness fault.\n{run.python_run.describe()}"
    )
    assert cobol_disposition == python_disposition, (
        f"the two sides ended in different dispositions - oracle "
        f"{cobol_disposition!r} against python {python_disposition!r} - even "
        f"though their statuses were {run.cobol_run.returncode} and "
        f"{run.python_run.returncode}. Preserving rejection behaviour means the "
        f"same disposition AND the same effect on the database (Agent Action Plan "
        f"section 0.8.1), and an empty batch is not a rejection of any of the "
        f"five classes: it runs to completion."
    )


def test_diff_exit_contract_is_honoured(
    empty_batch_parity: object, harness: object
) -> None:
    """The three-way exit contract of stage 8, asserted rather than assumed.

        0  identical, and stdout is EMPTY - zero bytes, not a banner
        1  a real behavioural difference, with a deterministic report
        2  THE COMPARISON COULD NOT BE PERFORMED - an ERROR, never a pass

    IN THIS SCENARIO THE 0-VERSUS-2 DISTINCTION IS EXISTENTIAL. "Both dumps are
    empty" and "no dump was produced" look identical from the verdict alone, so a
    status of 2 read as a pass would turn a broken harness into a green run.
    Status 2 cannot reach this test body at all: tests/conftest.py raises
    `HarnessFaultError` for it, and because that happens inside the fixture pytest
    reports an ERROR. This test asserts the remaining half of the contract - that
    the status the comparison returned and the verdict it computed agree, and that
    a pass really does write zero bytes.

    The zero-byte report is deliberate rather than incidental: an existing empty
    `diff.txt` says "compared, and identical", while an absent file says nothing
    at all, and the per-scenario evidence in
    docs/migration/scenario-diff-evidence.md cites the file.

    Args:
        empty_batch_parity: The completed `ParityRun`.
        harness: The three harness modules (R-1).
    """
    run = empty_batch_parity
    diff_states = harness.diff_states
    result = run.outcome.result

    assert result.returncode != diff_states.EX_ERROR, (
        f"stage 8 returned {diff_states.EX_ERROR}, meaning THE COMPARISON COULD "
        f"NOT BE PERFORMED, and it reached the test body instead of being raised "
        f"as a harness fault. That is the one conflation this tree forbids "
        f"outright.\n{result.describe()}"
    )
    assert result.returncode in (
        diff_states.EX_IDENTICAL,
        diff_states.EX_DIFFERENT,
    ), (
        f"stage 8 returned {result.returncode}, which is none of the three "
        f"documented statuses {diff_states.EX_IDENTICAL}, "
        f"{diff_states.EX_DIFFERENT} or {diff_states.EX_ERROR}. An unclassified "
        f"status is a status nobody should draw a conclusion from.\n"
        f"{result.describe()}"
    )

    expected_status = (
        diff_states.EX_IDENTICAL
        if run.tree.is_empty
        else diff_states.EX_DIFFERENT
    )
    assert result.returncode == expected_status, (
        f"stage 8 returned {result.returncode} while its own TreeDiff reports "
        f"is_empty={run.tree.is_empty} with {run.tree.total_differences} "
        f"finding(s). Both come from the same comparison over the same two trees, "
        f"so a disagreement means the trees changed between the two reads."
    )

    rendered = diff_states.render(run.tree)
    if run.tree.is_empty:
        assert result.stdout == "", (
            f"a passing comparison wrote {len(result.stdout)} byte(s) to stdout: "
            f"{result.stdout!r}. Status 0 means identical AND SILENT - zero "
            f"bytes, not a banner - so that an operator can test for emptiness "
            f"rather than parse a message."
        )
        assert rendered == "", (
            f"the report renders as {rendered!r} on an empty comparison. Agent "
            f"Action Plan section 0.8.5 makes the empty string the rendering of "
            f"two identical trees."
        )
        assert run.outcome.report.is_file(), (
            f"no report was written at {run.outcome.report}. A PASSING run "
            f"writes a ZERO-BYTE file deliberately: an existing empty file says "
            f"'compared, and identical', while an absent file says nothing at "
            f"all - which in this scenario is the difference that matters."
        )
        assert run.outcome.report.stat().st_size == 0, (
            f"the report at {run.outcome.report} is "
            f"{run.outcome.report.stat().st_size} byte(s) although the "
            f"comparison found nothing. A pass writes zero bytes."
        )
    else:
        assert rendered != "", (
            f"stage 8 reported {run.tree.total_differences} finding(s) but "
            f"rendered nothing. A difference with no report cannot be acted on."
        )


def test_dump_is_wellformed_on_both_sides(
    empty_batch_parity: object, harness: object, frozen_schema: object
) -> None:
    """THE DEFENCE AGAINST "NEVER DUMPED" MASQUERADING AS "CORRECTLY EMPTY".

    NOT OPTIONAL IN THIS SCENARIO. Everywhere else a malformed or absent capture
    shows up as a difference; here, where almost nothing is expected to change, it
    shows up as success. So the shape of every capture on both sides is asserted
    for all three tables.

    THE SHAPE, from `harness/dump_tables.py`'s `DUMP_KEYS`: exactly five keys in
    fixed insertion order - `table`, `primary_key`, `columns`, `row_count`,
    `rows` - AND NO OTHERS. No timestamp, no server version, no scenario name and
    no side; the side is recorded in the PATH. `columns` is in schema ordinal
    order and is never sorted. `rows` is a list of lists in primary-key-ascending
    order, positionally aligned. DECIMAL values are canonical JSON STRINGS at the
    DECLARED scale - never JSON numbers, never exponent notation - and integers
    are JSON integers. No value is null and NO VALUE IS A REAL NUMBER (R-2).

    The structural half is delegated to `harness/diff_states.py`'s own dump
    assertion, which is the single definition of it (R-4) and which also refuses a
    duplicate primary key and a file whose name disagrees with the table it
    declares. This test then adds the schema-ordinal check against the frozen
    `mysql/ACASDB.sql`, the declared column count, and the scale rendering that
    matters most here: A ZERO MUST RENDER AT THE DECLARED SCALE ON BOTH SIDES, or
    `GLBATCH-REC`'s four `decimal(14,2) unsigned` columns
    [mysql/ACASDB.sql:L90-L93] and `GLLEDGER-REC.LEDGER-BALANCE` `decimal(10,2)`
    [mysql/ACASDB.sql:L128] would report a spurious difference.

    Args:
        empty_batch_parity: The completed `ParityRun`.
        harness: The three harness modules (R-1).
        frozen_schema: The parsed `mysql/ACASDB.sql`, read and never written
            (Agent Action Plan section 0.8.1).
    """
    run = empty_batch_parity
    diff_states = harness.diff_states
    normalize = harness.normalize

    for side in diff_states.SIDES:
        for table in run.tables:
            where = f"{side}:{table}"
            path = run.paths.normalized_dir(side) / diff_states.dump_filename(
                table
            )

            # The single definition of the structural contract, including the
            # float gate, the null gate and the duplicate-key gate.
            dump = diff_states.load_dump(path)

            assert tuple(dump) == tuple(diff_states.DUMP_KEYS), (
                f"{where}: the dump at {path} carries keys {tuple(dump)!r} and "
                f"must carry exactly {tuple(diff_states.DUMP_KEYS)!r}, in that "
                f"insertion order and with no others. An extra key - a "
                f"timestamp, a server version, a side - would make two captures "
                f"of one state compare unequal."
            )

            spec = diff_states.IN_SCOPE[table]
            assert dump["table"] == table, (
                f"{where}: the dump declares table {dump['table']!r}."
            )
            assert dump["primary_key"] == spec.primary_key, (
                f"{where}: the dump aligns on {dump['primary_key']!r} but "
                f"mysql/ACASDB.sql declares the primary key "
                f"{spec.primary_key!r} at [mysql/ACASDB.sql:L{spec.schema_line}]."
            )

            columns = tuple(str(name) for name in dump["columns"])
            expected_columns = normalize.schema_columns(frozen_schema, table)
            assert columns == expected_columns, (
                f"{where}: the column list disagrees with the frozen schema.\n"
                f"  dump  : {columns!r}\n"
                f"  schema: {expected_columns!r}\n"
                f"  Rows are POSITIONAL, so a column list in any other order has "
                f"no meaningful alignment."
            )
            assert len(columns) == spec.column_count, (
                f"{where}: {len(columns)} column(s) against the "
                f"{spec.column_count} mysql/ACASDB.sql declares at "
                f"[mysql/ACASDB.sql:L{spec.schema_line}]. The schema is frozen, "
                f"so a disagreement means either the dump or the checkout is "
                f"wrong."
            )
            assert dump["row_count"] == len(dump["rows"]), (
                f"{where}: row_count is {dump['row_count']} but {len(dump['rows'])} "
                f"row(s) are present. A dump that contradicts itself cannot "
                f"produce a verdict."
            )

            key_index = columns.index(dump["primary_key"])
            keys = [row[key_index] for row in dump["rows"]]
            key_type = normalize.column_type(
                frozen_schema, table, dump["primary_key"]
            )
            assert key_type.kind == normalize.KIND_INTEGER, (
                f"{where}: the primary key {dump['primary_key']!r} is declared "
                f"{key_type.sql_type!r} at [mysql/ACASDB.sql:L{key_type.line}]. "
                f"All three tables this scenario bounds key on an integer "
                f"column, so an ordering check on their keys is total."
            )
            for key in keys:
                assert isinstance(key, int) and not isinstance(key, bool), (
                    f"{where}: the primary-key value {key!r} serialised as "
                    f"{type(key).__name__} although the column is "
                    f"{key_type.sql_type!r}. Rows are aligned on this value and "
                    f"`1` is not `\"1\"`, so a type drift silently un-aligns "
                    f"every row."
                )
            assert keys == sorted(keys), (
                f"{where}: the rows are not in primary-key-ascending order - "
                f"{keys!r}. The capture is `SELECT * FROM <table> ORDER BY "
                f"<primary key>` with no tie-breaking, which is what makes it "
                f"deterministic by construction."
            )
            assert len(keys) == len(set(keys)), (
                f"{where}: a primary-key value appears twice in {keys!r}, so at "
                f"least one row could not be aligned unambiguously."
            )

            for row in dump["rows"]:
                assert len(row) == len(columns), (
                    f"{where}: a row carries {len(row)} value(s) against "
                    f"{len(columns)} column(s). A ragged row has no alignment."
                )
                for column, value in zip(columns, row):
                    declared = normalize.column_type(
                        frozen_schema, table, column
                    )
                    assert value is not None, (
                        f"{where}: {column} is null. Every column of the frozen "
                        f"schema is `NOT NULL`, because each bridge initialises "
                        f"its host-variable group before a write so an unset "
                        f"field becomes zero or space rather than SQL NULL."
                    )
                    assert isinstance(value, (str, int)) and not isinstance(
                        value, bool
                    ), (
                        f"{where}: {column} serialised as "
                        f"{type(value).__name__} ({value!r}). A dumped value is "
                        f"a JSON string or a JSON integer and NEVER a real "
                        f"number: no accounting value in this migration passes "
                        f"through binary floating point (R-2)."
                    )
                    if declared.kind == normalize.KIND_DECIMAL:
                        assert isinstance(value, str), (
                            f"{where}: {column} is declared "
                            f"{declared.sql_type!r} at "
                            f"[mysql/ACASDB.sql:L{declared.line}] but "
                            f"serialised as {type(value).__name__}. An "
                            f"exact-decimal column is carried as a canonical "
                            f"JSON STRING, because a JSON number is a real "
                            f"number (R-2)."
                        )
                        if declared.scale:
                            fraction = value.partition(".")[2]
                            assert len(fraction) == declared.scale, (
                                f"{where}: {column} rendered {value!r}, which "
                                f"carries {len(fraction)} decimal place(s) "
                                f"against the {declared.scale} declared by "
                                f"{declared.sql_type!r} at "
                                f"[mysql/ACASDB.sql:L{declared.line}]. Scale is "
                                f"rendered at the DECLARED scale and is NOT "
                                f"uniformly 2 across the schema; a zero that "
                                f"rendered differently on the two sides would "
                                f"be reported as a posting difference."
                            )
                    elif declared.kind == normalize.KIND_CHAR:
                        assert isinstance(value, str), (
                            f"{where}: {column} is declared "
                            f"{declared.sql_type!r} but serialised as "
                            f"{type(value).__name__}."
                        )
                    else:
                        assert isinstance(value, int), (
                            f"{where}: {column} is declared "
                            f"{declared.sql_type!r} at "
                            f"[mysql/ACASDB.sql:L{declared.line}] but "
                            f"serialised as {type(value).__name__}. "
                            f"`GLBATCH-REC.ENTERED`, `PROOFED`, `POSTED` and "
                            f"`STORED` in particular are `int(8) unsigned` "
                            f"binary day numbers [mysql/ACASDB.sql:L86-L89] from "
                            f"four `binary-long` fields "
                            f"[copybooks/wsbatch.cob:L36-L39], NOT date text, so "
                            f"normalisation's third job must never touch them."
                        )


def test_seed_fingerprints_agree(empty_batch_parity: object) -> None:
    """BOTH CYCLES STARTED FROM THE SAME ROW COUNTS - or the run is unattributable.

    THE SECOND OF THE TWO DEFENCES against an empty diff that means nothing.
    Nothing else in the protocol proves that the two sides began from the same
    state: without this check, a re-seed that quietly loaded a different fixture
    produces differences with no indication that the seed rather than the cycle
    caused them. So each side records the row count of every table this scenario
    names, IN THE ORDER IT NAMES THEM, immediately before its run, and the Python
    runner refuses to proceed when the oracle side recorded something different.

    A MISMATCH IS A HARNESS FAULT AND OUTRANKS ANY BEHAVIOURAL FINDING, because a
    stage that cannot establish its own starting state has not measured behaviour
    at all. It converts a whole class of silent false failures into a correctly
    attributed error.

    The fingerprints are row counts only, all integers, so they introduce no
    decimal of their own (R-2), and both live under `run-logs/` - OUTSIDE every
    compared tree - so neither can leak into a capture (R-6). They are compared
    AS BYTES and never parsed: interpreting the counts here would be the added
    validation R-3 forbids, and the corroboration that the seeded tables actually
    hold rows is taken from the dumps instead, in
    `test_affected_tables_are_byte_identical_to_the_seed`.

    THE ORACLE-SIDE FINGERPRINT MAY LEGITIMATELY BE ABSENT. The Python runner
    treats that as a WEAKER GUARANTEE rather than a fault - it says so plainly and
    continues - so this test asserts everything that can be asserted and invents
    no failure the harness itself does not raise.

    Args:
        empty_batch_parity: The completed `ParityRun`, whose `paths.run_logs` is
            the transcript directory both fingerprints live in.
    """
    run = empty_batch_parity
    run_logs = run.paths.run_logs
    python_fingerprint = run_logs / "python.seed-fingerprint"
    cobol_fingerprint = run_logs / "cobol.seed-fingerprint"

    assert python_fingerprint.is_file(), (
        f"no seed fingerprint at {python_fingerprint}. The Python runner records "
        f"it before the run and exits with a precondition status if it cannot, so "
        f"a completed run without one means the starting state of the comparison "
        f"was never established."
    )

    recorded = python_fingerprint.read_bytes()
    assert recorded, (
        f"the seed fingerprint at {python_fingerprint} is empty. It carries one "
        f"line per affected table, so an empty file means no table was counted."
    )

    lines = [
        line for line in recorded.decode("utf-8").splitlines() if line.strip()
    ]
    assert len(lines) == len(run.tables), (
        f"the seed fingerprint at {python_fingerprint} carries {len(lines)} "
        f"line(s) for {len(run.tables)} affected table(s):\n"
        f"{recorded.decode('utf-8')}"
        f"  One line per table is the contract, and the count is what the two "
        f"sides compare."
    )
    for line, table in zip(lines, run.tables):
        # One line per table, the table name first, tab-separated from its count.
        # Only the NAME and its position are read; the counts are never
        # interpreted here (R-3) - the corroboration that the seeded tables hold
        # rows is taken from the dumps in the byte-identity test instead.
        recorded_table = line.split("\t")[0]
        assert recorded_table == table, (
            f"the seed fingerprint at {python_fingerprint} names "
            f"{recorded_table!r} where the scenario names {table!r}:\n"
            f"{recorded.decode('utf-8')}"
            f"  THE DECLARED ORDER IS PART OF THE CONTRACT. The two sides compare "
            f"these files byte for byte, so a reordering on one side alone would "
            f"be reported as a starting-state disagreement."
        )

    if cobol_fingerprint.is_file():
        assert recorded == cobol_fingerprint.read_bytes(), (
            f"THE TWO SIDES DID NOT START FROM THE SAME SEEDED STATE - a HARNESS "
            f"FAULT, not a behavioural difference, and the distinction matters "
            f"because the two look identical in a table diff.\n"
            f"  python ({python_fingerprint}):\n"
            f"{recorded.decode('utf-8')}"
            f"  cobol  ({cobol_fingerprint}):\n"
            f"{cobol_fingerprint.read_text(encoding='utf-8')}"
            f"  Nothing about either cycle's behaviour has been measured: they "
            f"were never given the same starting state. Re-run the reset and "
            f"seed stages and then both run stages, in the protocol order. "
            f"Autocommit must be OFF while seeding - "
            f"[common/glbatchLD.cbl:L9-L13] - and `batch.dat` is loaded by "
            f"exactly that loader [common/masterLD.sh:L94]."
        )
