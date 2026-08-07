"""THE EMPTY BATCH - the degenerate case, and the one scenario whose central
question is settled ONLY by running the compiled oracle.

Scenario `empty_batch`, subsystem `general`, operation `gl_post_cycle`, declared
terminal status `expected_status: [0]`. It drives the ten-stage parity protocol
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
`system.period: 1` is inert here, because only `gl_end_of_cycle` reads it and
this route never reaches gl080. The `end_of_cycle_gl` scenario is where it acts.

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
docs/migration/ambiguity-resolutions.md, section 13, where it is now `RESOLVED BY
ORACLE` (2026-08-07): NEITHER at-end paragraph leaves any observable effect, which
is the FIRST of the three readings below. That answer is a reason to expect these
assertions to hold and deliberately not a value any of them hard-codes - each still
asserts only that the two sides agree, because a parity test that encoded the
measured value would stop being a parity test. The identifier was coined
here, in the descriptive form that document already uses for `Q-SORT-TIE-ORDER`
and `Q-A17-POSTINGS-EFFECT`, and the register carries the entry it names:
three readings of what the two at-end rewrites do to a zero key, the observable
that separates them, and the note that this scenario's declared
`expected_table_effect: unchanged` is the FIRST reading stated as an expectation
rather than a resolution.

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
bytes on paper -- and it HAS been settled: `RESOLVED BY ORACLE` (2026-08-07), the
answer being NEITHER, because both record copies measure 96 and the 98 in the
maintainer's note is false under GnuCOBOL 3.2.0. The trailing-field alignment this
scenario depends on therefore does not shift. docs/migration/anomaly-log.md carries
A-15 as `REPRODUCED -- VALUE MEASURED` against that identifier, not as pending; the
contradictory note itself is untouched (R-4).

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
THE TEN-STAGE PROTOCOL, DRIVEN THROUGH THE ONE HELPER
-------------------------------------------------------------------------------

    1  reset_db.sh + seed.sh    6  run_python_scenario.sh
    2  run_cobol_scenario.sh    7  dump --side python
    3  dump --side cobol        8  normalize.py
    4  normalize.py             9  verify both captures published
    5  reset_db.sh + seed.sh   10  diff_states.py

EIGHT LOGICAL STAGES, TEN NUMBERED ONES. Agent Action Plan section 0.3.2 fixes the
order as "seed, run, dump, normalize, reset, run, dump, diff" - eight. The driver
`harness/run_parity.sh` numbers ten, reading the list from
`harness/parity_stages.sh`, because it makes BOTH normalisations and the publication
check explicit rather than implied. Nothing was added to the protocol; where older
prose says "stage 8" it means today's stage 10, the diff. The runners' own
`Check n/8' headings are their internal preflight checks and are not protocol
stages.

Neither runner performs stage 7, and neither runs `normalize.py` or
`diff_states.py`. Capture ownership is single and it is the protocol's: stage 7 is
invoked AFTER the runner has exited, which is the only moment at which the run
status the capture's attestation carries is final. Agent Action Plan section 0.4.3
requires that "no test reimplements the comparison protocol", so every stage above
is composed exactly once, in tests/conftest.py, and reached here through the
`protocol` fixture. NOTHING BELOW WRITES ITS OWN COMPARISON.

THE THREE-WAY EXIT CONTRACT OF STAGE 10, and the one conflation that must never
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

THE COMPARISON IS BOUNDED BY ALL 22 IN-SCOPE TABLES, WHICH IS THE PROTOCOL. The
scenario's own `affected_tables` list is its DECLARED EFFECT, asserted against
separately; it is not the bound, because a bound drawn from what a scenario
expects to move cannot reveal a difference in anything it did not. There is no
ignore-list, no tolerance-list and no "known difference" allowance anywhere in
the diff path, and none is added here.

The five DECLARED tables, alphabetically, in the order the seed fingerprint is
written in:

    GLBATCH-REC     carries the ANSWER to the central open question above
    GLLEDGER-REC    proves no balance moved - or records whatever
                    `end-account`'s `GL-Nominal-Rewrite` [general/gl072.cbl:L382]
                    actually did
    GLPOSTING-REC   the UNCHANGED WITNESS, additionally empty in the seed
    SYSDEFLT-REC    written by the menu exit path under key 2, and empty in this seed
    SYSTEM-REC      written by the menu exit path under key 1, on both sides

Why the last two are on the DECLARED EFFECT list at all - they are written by the
menu shell's exit path rather than by any of the twelve in-scope programs, and a
table a run writes belongs in its declared effect whichever layer writes it
[general/general.cbl:L656-L672]:

    656  overrewrite.
    657       if       File-System-Used NOT = zero
    664                move     2 to File-Key-No       <- KEY 2, SYSDEFLT-REC
    667                move     4 to File-Key-No       <- KEY 4, SYSTOT-REC

with key 1 at L659-L663, and BOTH SIDES REACH IT: `acas_posting/cli/args.py`'s
`overrewrite` is called by every one of the seven routes, so key 1 is written on
both sides of every scenario and these rows are comparable rather than excluded.
Sales and Purchase persist keys 1 and 4 only, never
key 2, on every `load000` call [sales/sales.cbl:L628-L657] with
[sales/sales.cbl:L659-L660] and [purchase/purchase.cbl:L621-L650] with
[purchase/purchase.cbl:L652-L653]. A census over all twelve in-scope PROGRAMS
finds ZERO `System-*` facade verbs, so no migrated program persists a system
record - only the menu-exit path does. `SYSFINAL-REC` appears on
no scenario list because nothing on either side writes it; `SYSTOT-REC`
remains genuinely in scope for `period_end_totals`, which is why nothing is ever
blanket-excluded; and `SYSTEM-REC` is DUMPED WITH EXACTLY TWO CELLS WITHHELD -
`RDBMS-PASSWD char(12)` [copybooks/wssystem.cob:L139] and the frozen schema's
shorter `PASS-WORD`, replaced on BOTH sides by `harness/dump_tables.py`'s
`REDACTED_COLUMNS` because a dump is `SELECT *` and a capture is committed
evidence. Every other column is compared byte for byte, so this is not an
ignore-list. THE OBVIOUS OBJECTION WAS TESTED AND DOES NOT HOLD: the row's
content depends on what the route did - including `Date-Form`, which the frozen
date sections write back [copybooks/wssystem.cob:L127] - so it is reasonable to
fear that comparing it would tie THIS scenario's
`expected_table_effect: unchanged` to fields it does not reason about. Measured,
the digest is UNCHANGED here and on every other scenario declaring `unchanged`,
because the exit rewrite writes back the value it loaded. Both runners digest the
row before and after every run besides, and
`protocol.assert_system_record_parity` compares the two sides' post-run digests
over all 169 columns - the credential included, with nothing to leak.

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

# The TIER mark, applied to the whole module because every test in it belongs to the
# tier. THE INFRASTRUCTURE MARKS ARE NOT HERE: `database` and `oracle` are declared per
# test, on exactly the tests whose fixture closure reaches the harness stack, because
# several tests in this file read only files on disk and pass on a bare host. A module
# mark would claim they need a MariaDB and a built oracle, and `-m database` would then
# select tests that require neither.
pytestmark = pytest.mark.scenario

SCENARIO = "empty_batch"

# THE TWO TABLES THE SEED FILLS: ledger.dat -> GLLEDGER-REC and batch.dat ->
# GLBATCH-REC. They must come back WITH ROWS on both sides, because THIS scenario is the
# one where "both dumps are empty" and "no dump was produced" look identical from the
# verdict alone - and where an unseeded database would make every claim below true for
# the wrong reason.
#
# `GLPOSTING-REC` IS NOT HERE, AND ITS EMPTINESS IS NOT ASSERTED HERE EITHER. The seed
# carries no posting.dat at all - see
# `test_seed_has_exactly_three_files_and_no_posting_dat` -
# so the table starts empty and an empty batch must leave it that way. Whether it DID is
# a behavioural claim owned by `test_glposting_rec_is_empty_on_both_sides`, where a
# Python side that wrote a row is a FAILURE; asserting it in this fixture would report
# that regression as an ERROR.
SEEDED_TABLES = (
    "GLBATCH-REC",
    "GLLEDGER-REC",
)

# THE RUNNER'S OWN WORDING for a cross-check it could not make, quoted from
# [harness/run_python_scenario.sh acas_py_seed_fingerprint]. Matched as a SUBSTRING of the stage-6
# transcript, so the note's surrounding path and punctuation are free to change; what
# must not change silently is that an absent oracle-side fingerprint is DECLARED.
UNVERIFIED_NOTE = "no oracle-side seed fingerprint at"


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
#  capture, either normalisation - and a stage-10 status of 2 raise
#  `HarnessFaultError` inside tests/conftest.py; raised from a fixture, pytest
#  reports that as an ERROR. A real behavioural difference reaches the test body
#  and fails an `assert`, so it is a FAILURE. That is the three-way contract of
#  the module docstring, realised structurally rather than by convention.
#
#  Function-scoped, deliberately, and that is NOT the same as re-running the
#  protocol per test. A module-scoped fixture cannot request the function-scoped
#  `protocol`, and `protocol` must stay function-scoped so that a bare host gets a
#  precise SKIP rather than a collection error - so this fixture is function-scoped
#  and the RUN behind it is shared.
#
#  ⭐ THE SHARING LIVES IN `run_scenario_parity` ITSELF, AND THE COMMENT THAT USED TO
#  BE HERE HAD THE ARGUMENT BACKWARDS. It said that memoising "would let two tests in
#  one session mean different things by the diff", and the truth is the reverse:
#  memoising is what makes every test in this file mean the SAME thing by it. Nine
#  tests each running their own protocol were nine separate runs, and every assertion
#  here is a claim about ONE of them - "the diff is empty", "the term code was zero in
#  that run", "the report the verdict came from says so". If two of those nine runs had
#  ever disagreed, this file would still have been green, because no assertion compared
#  a run to another run. That is a quiet incoherence, not nine independent
#  confirmations; independence of runs is the determinism tier's claim to make, and it
#  makes it explicitly, twice, in tests/determinism/.
#
#  So the protocol now runs ONCE per distinct request for the whole session, cached in
#  `tests/conftest.py`'s `_PARITY_RUN_CACHE`. The seven sibling scenario modules had
#  each already reached for module-level state to get this; putting it in the helper
#  means this file gets it without its own cache and no future module has to remember.
#  Agent Action Plan section 0.8.4 sets no performance target and forbids optimising
#  for one - and this is not that: it is what makes the file's own narrative true, with
#  the run time falling out as a side effect. Runs are strictly sequential (R-3);
#  nothing here is parallel.
#
#  The injected objects are annotated `object` because their precise
#  tests/conftest.py types cannot be named without a module-level import of that
#  module. Each parameter's real type is documented in the docstring that uses it.
# ---------------------------------------------------------------------------


@pytest.fixture
def empty_batch_parity(protocol: object) -> object:
    """Run all ten protocol stages for `empty_batch` and return the verdict.

    Args:
        protocol: tests/conftest.py's `Protocol` stage bundle. It applies the
            stack skip, so an unusable harness is a SKIP and never an error.

    Returns:
        The `ParityRun`: every stage result in execution order, both run stages,
        the stage-10 `DiffOutcome` and the artifact paths. `is_empty` is the pass
        condition and `tree` names what differed.

    Raises:
        HarnessFaultError: A stage whose failure destroys the evidence failed, or
            the comparison could not be performed at all. Reported as a test
            ERROR, never as a pass - in this scenario above all others, because
            "both dumps are empty" and "no dump was produced" look identical from
            the verdict alone.
    """
    run = protocol.run_scenario_parity(SCENARIO)

    # THE BOUND. The declared tables, in the declared ORDER - the order the report and
    # the seed fingerprint are both written in.
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

    # THE ORACLE'S DISPOSITION, plus a harness-fault refusal on BOTH sides. A runner
    # that exited in its own documented band never ran the cycle, and on THIS scenario
    # that is indistinguishable from success in the verdict alone. `reference_only`
    # leaves the Python side's status to `test_run_completes_with_term_code_zero`.
    #  BOTH SIDES DROVE THE SAME ORDERED OPERATION LIST (finding F-12). The
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

    # THE STARTING STATE WAS RECORDED. `test_seed_fingerprints_agree` reads the same
    # two files again and asserts the CROSS-CHECK disposition explicitly; this is the
    # setup-level claim that a fingerprint exists at all and describes the bounded
    # tables in the bounded order.
    protocol.assert_seed_fingerprints_agree(run)

    # SOMETHING WAS THERE TO COMPARE. The single most important guard in this file: an
    # empty batch over an EMPTY DATABASE agrees with itself perfectly.
    protocol.assert_non_vacuous(run, tables_requiring_rows=SEEDED_TABLES)

    return run


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

    # Inert on this route: only `gl_end_of_cycle` consumes the period and this route
    # never reaches gl080. Asserted so the pin stays visible.
    assert system["period"] == 1, (
        f"system.period is {system['period']!r}. It is inert here - only "
        f"gl_end_of_cycle consumes it, and this route never reaches it - "
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

    assert tables == [
        "GLBATCH-REC",
        "GLLEDGER-REC",
        "GLPOSTING-REC",
        "SYSDEFLT-REC",
        "SYSTEM-REC",
    ], (
        f"the affected-table list is {tables!r}. Three tables the General Ledger "
        f"posting cycle can touch - gl072's eight facade verbs reach the batch and "
        f"the nominal ledger [general/gl072.cbl:L276-L277, L377, L382, L408, "
        f"L441-L442, L454] and gl070 reads the posting file "
        f"[general/gl070.cbl:L481, L486, L466] - plus two menu-persisted ones.\n"
        f"SYSDEFLT-REC and SYSTEM-REC are the two menu-persisted tables MEASURED "
        f"comparable - the General menu exit rewrites keys 1, 2 and 4 "
        f"[general/general.cbl:L656-L692] and keys 1 and 2 come back byte-identical "
        f"on both sides. Key 4, SYSTOT-REC, is the one that cannot be compared: the "
        f"menu sources it from the COBOL flat file alone "
        f"[general/general.cbl:L402-L404], the RDB read being commented out at "
        f"L434-L436, so its exit returns sys4LD's four-spare sentinel "
        f"[common/sys4LD.cbl:L368-L390] from 1.00 to 0.00."
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


@pytest.mark.database
@pytest.mark.oracle
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
        f"{run.diagnose()}\n"
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

    #  AND THE PASS IS WHAT A PASS LOOKS LIKE, on THIS run's real trees. The exit
    #  contract itself is exercised on synthetic trees by
    #  `test_diff_exit_contract_is_honoured`, which needs no stack; these assertions are
    #  about the run that just happened, and they belong here because this is the test
    #  that owns it. On this scenario in particular an absent report and a zero-byte one
    #  are the difference that matters: the expected outcome is that nothing changed, so
    #  "compared, and identical" and "never compared" produce the same findings and only
    #  the artifacts distinguish them.
    diff_states = harness.diff_states
    result = run.outcome.result
    assert result.returncode == diff_states.EX_IDENTICAL, (
        f"stage 10 returned {result.returncode} while its own TreeDiff reports "
        f"is_empty={run.tree.is_empty} with {run.tree.total_differences} finding(s). "
        f"Both come from the same comparison over the same two trees, so a "
        f"disagreement means the trees changed between the two reads.\n"
        f"{result.describe()}"
    )
    assert result.stdout == "", (
        f"a passing comparison wrote {len(result.stdout)} byte(s) to stdout: "
        f"{result.stdout!r}. Status 0 means identical AND SILENT - zero bytes, not a "
        f"banner - so that an operator can test for emptiness rather than parse a "
        f"message."
    )
    assert run.diagnose() == "", (
        f"the report renders as {run.diagnose()!r} on an empty "
        f"comparison. Agent Action Plan section 0.8.5 makes the empty string the "
        f"rendering of two identical trees."
    )
    assert run.outcome.report.is_file(), (
        f"no report was written at {run.outcome.report}. A PASSING run writes a "
        f"ZERO-BYTE file deliberately: an existing empty file says 'compared, and "
        f"identical', while an absent file says nothing at all - which in this "
        f"scenario is the difference that matters."
    )
    assert run.outcome.report.stat().st_size == 0, (
        f"the report at {run.outcome.report} is "
        f"{run.outcome.report.stat().st_size} byte(s) although the comparison found "
        f"nothing. A pass writes zero bytes."
    )


@pytest.mark.database
@pytest.mark.oracle
def test_affected_tables_are_byte_identical_to_the_seed(
    empty_batch_parity: object,
    harness: object,
    protocol: object,
    scenario_loader: object,
) -> None:
    """BYTE-IDENTICAL TO THE SEED - compared against the seed, not against the other run.

    ⭐ WHAT THIS TEST USED TO COMPARE, AND WHY THAT WAS NOT ITS OWN TITLE. Its name
    claims the affected tables came back byte-identical TO THE SEED; every assertion it
    made compared the two POST-RUN trees to each other. Those are different claims, and
    the weaker one is satisfied by outcomes the stronger one rejects: two cycles that
    both stamped the empty batch agree perfectly, and two cycles that both inserted the
    same spurious row agree perfectly. Neither is byte-identical to anything.

    SO THE SEED COMPARISON IS MADE FIRST, AND IT IS A REAL ONE. Both runners record a
    canonical primary-key-ordered digest of every bounded table immediately BEFORE their
    dispatch and again immediately AFTER it. `assert_tables_unchanged_by_run` compares a
    side's own two records, per table, so the question it answers is "did THIS cycle
    change this table" - which no side-to-side diff can answer at all. Both sides are
    asserted, and separately, because "unchanged by the run" is a property of a CYCLE and
    there are two cycles.

    THE ONE CAVEAT THE FOLDER REQUIREMENT CARRIES IS STILL HONOURED, and it is the whole
    subtlety of this scenario: whatever `gl072`'s at-end branch legitimately performed -
    `end-account` then `end-batch` [general/gl072.cbl:L286-L289] - would not be a
    spurious change but the specification. The scenario declares
    `expected_table_effect: unchanged`, which is the reading that those two rewrites
    target a ZERO KEY and match no row; that reading is an EXPECTATION and is filed as
    ambiguity `Q-EMPTY-BATCH-AT-END` in docs/migration/ambiguity-resolutions.md, with the
    three readings and the observable set out in full. If the oracle takes a different
    one, THIS ASSERTION IS WHERE IT SURFACES - and the resolution is to record the
    measurement and reproduce it, never to weaken this back to a side-to-side comparison.
    Nothing here predicts `CLEARED-STATUS` or `POSTED`.

    THE SEED COMPARISON IS BOUNDED BY THE DECLARED EFFECT and the side-to-side
    comparison by all 22 in-scope tables, and the difference is not an oversight. Both
    runners fingerprint the scenario's own `affected_tables` plus the menu-persisted
    parameter row; those are the tables about which a pre/post record exists, so they
    are the tables about which "unchanged by THIS run" can be asserted at all. The
    22-table bound is what the diff below uses, because a bound drawn from what a
    scenario expects to move cannot reveal a difference in anything it did not.

    THE SIDE-TO-SIDE STRUCTURAL CLAIMS FOLLOW, per table: no spurious row, no dropped
    row, matching row counts and column lists, no differing value. And the corroboration
    that the verdict is not vacuous - the tables the seed filled came back WITH ROWS,
    because a run that never connected would leave every table at zero and still diff
    clean.

    Args:
        empty_batch_parity: The completed `ParityRun`.
        harness: The three harness modules (R-1).
        protocol: The protocol bundle, for the per-side seed comparison. It is the ONE
            implementation of that comparison; nothing here reads a digest file itself.
        scenario_loader: tests/conftest.py's `scenario_definition`, read for the
            declared `affected_tables` - the set the runners fingerprint.
    """
    run = empty_batch_parity

    # ---- THE CLAIM IN THE TEST'S NAME, ASSERTED FIRST -------------------------
    # Every bounded table, on each side, must carry the same row count and the same
    # digest after the run as before it. This is the seed comparison; everything below
    # it is the side-to-side structural detail.
    #  THE SEED COMPARISON IS OVER THE DECLARED EFFECT, WHICH IS WHAT THE RECORD
    #  COVERS. Both runners fingerprint the scenario's own `affected_tables' plus the
    #  menu-persisted parameter row, and nothing else, so this is exactly the set on
    #  which "unchanged by the run" can be established. It is deliberately NOT
    #  `run.tables': that is the 22-table COMPARISON bound, asserted side-to-side
    #  below, and asking the pre/post record about a table it never fingerprinted
    #  reports a missing record rather than an unchanged table.
    declared = tuple(scenario_loader(SCENARIO)["affected_tables"])
    protocol.assert_tables_unchanged_by_run(run, unchanged=declared)

    by_table = {entry.table: entry for entry in run.tree.tables}

    assert sorted(by_table) == sorted(run.tables), (
        f"the comparison covered {sorted(by_table)!r} but it is bounded by "
        f"{sorted(run.tables)!r} - all 22 in-scope tables. There is no ignore-list "
        f"anywhere in the diff path, so a table missing from the verdict was never "
        f"compared."
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


@pytest.mark.database
@pytest.mark.oracle
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


@pytest.mark.database
@pytest.mark.oracle
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


@pytest.mark.database
@pytest.mark.oracle
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
    emit would itself be an added behaviour, and therefore a defect.

    ⚠️ WHAT THIS TEST CAN AND CANNOT SEE, corrected (finding MJ-14). An earlier
    revision claimed a guard on the Python side "is observable precisely because it
    would SKIP the at-end work, so it shows up as a `GLBATCH-REC` or `GLLEDGER-REC`
    difference". THAT IS FALSE, and `Q-EMPTY-BATCH-AT-END` says why: it is
    `RESOLVED BY ORACLE` (2026-08-07) with the answer that NEITHER at-end paragraph
    leaves any observable effect. `end-account` and `end-batch` rewrite the BLANK
    records the program is holding, so both statements are an `UPDATE` on key zero,
    no row carries key zero, and the two rewrites match nothing. A guard that
    skipped them therefore produces the IDENTICAL empty diff and passes this test.
    Measured, not reasoned: adding `if save-batch not = zero` to the at-end clause
    was tried, and this file stayed green while the call-sequence lock failed.

    SO THIS TEST IS A WITNESS, and the LOCK lives in
    `tests/arithmetic/test_gl072_shipped_silent_skips.py` §4, which drives the
    shipped `gl072` over an empty work file with a recording facade double and
    asserts that `end-account` then `end-batch` both run, on zero keys, in that
    order. What THIS test contributes is different and still worth having: that the
    two independent implementations agree across all bounded tables on a run that
    posts nothing. A counter or summary row WOULD show up here, as an extra row or a
    changed column, because those add state rather than skip a no-op.

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
            f"  AN ADDED EMPTY-CASE GUARD IS *NOT* THE HYPOTHESIS THIS "
            f"DIFFERENCE SUPPORTS, and saying otherwise would send a reader the "
            f"wrong way (MJ-14). A short circuit over the empty work file omits "
            f"the at-end work [general/gl072.cbl:L287-L288], and that work is a "
            f"rewrite on key ZERO which matches no row - so a guard shows up "
            f"NOWHERE in this comparison. Q-EMPTY-BATCH-AT-END is `RESOLVED BY "
            f"ORACLE` (2026-08-07) with exactly that answer, and the guard is "
            f"caught instead by "
            f"tests/arithmetic/test_gl072_shipped_silent_skips.py section 4. R-3 "
            f"forbids adding one regardless of table state, because a guard that "
            f"agrees with a measured no-op is still added behaviour and would "
            f"diverge the moment the frozen path changed. A difference HERE is "
            f"something else: added state - an extra row, a counter, a summary - "
            f"or a genuine divergence in the phases that do write."
        )
        assert entry.rows_compared, (
            f"{entry.table}: the rows were not compared at all, so the absence "
            f"of a finding says nothing. That is a comparison that could not be "
            f"performed, never a pass (R-6)."
        )


@pytest.mark.database
@pytest.mark.oracle
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

    ⭐ DRIVEN THROUGH THE SHIPPED COMPARISON, AND THROUGH ONE IMPLEMENTATION.
    `tests/conftest.py`'s `assert_diff_exit_contract` publishes two synthetic sides with
    `harness/dump_tables.py`'s own writer, canonicalises them with `harness/normalize.py`
    and compares them with `harness/diff_states.py` - once for each of the four cases.
    THIS FILE USED TO ASSERT THE CONTRACT AGAINST MODULE CONSTANTS AND HAND-BUILT
    `TreeDiff` DATACLASSES, which passes whatever the comparison actually does: three
    integers being distinct says nothing about what the tool exits with, and a dataclass
    built in the test reports whatever the test put in it. The constants are still
    checked here, but only as a cheap corroboration of a contract the helper has just
    exercised end to end, over THIS scenario's own bound. It matters
    particularly here, because an empty batch's expected outcome is an empty diff -
    exactly what a comparison that never happened also produces. Only the exit status
    tells them apart, which is why it is exercised rather than assumed.

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
    empty_batch_parity: object, harness: object, frozen_schema: object,
    withheld: object,
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
            #  THE KEY'S DECLARED TYPE DECIDES WHAT TO ASSERT, because the
            #  comparison is bounded by all 22 in-scope tables and they do NOT all key
            #  on an integer: `ANALYSIS-REC.PA-CODE` is `char(3)`
            #  [mysql/ACASDB.sql:L32]. This scenario's three DECLARED tables happen to
            #  key on integers, which is why an earlier form of this assertion demanded
            #  it of everything. What matters to a dump's wellformedness is that the
            #  serialised key MATCHES ITS DECLARED COLUMN TYPE - `1` is not `"1"` and a
            #  drift either way silently un-aligns every row - so that is what is
            #  asserted, for every table, against the schema rather than against a
            #  scenario-specific expectation.
            if key_type.kind == normalize.KIND_INTEGER:
                for key in keys:
                    assert isinstance(key, int) and not isinstance(key, bool), (
                        f"{where}: the primary-key value {key!r} serialised as "
                        f"{type(key).__name__} although the column is "
                        f"{key_type.sql_type!r}. Rows are aligned on this value and "
                        f"`1` is not `\"1\"`, so a type drift silently un-aligns "
                        f"every row."
                    )
            else:
                for key in keys:
                    assert isinstance(key, str), (
                        f"{where}: the primary-key value {key!r} serialised as "
                        f"{type(key).__name__} although the column is "
                        f"{key_type.sql_type!r} at "
                        f"[mysql/ACASDB.sql:L{key_type.line}]. Rows are aligned on "
                        f"this value, so a type drift silently un-aligns every row."
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
                        f"{type(value).__name__} ({withheld(value)}). A dumped value is "
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
                                f"{where}: {column} rendered {withheld(value)}, which "
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


@pytest.mark.database
@pytest.mark.oracle
def test_seed_fingerprints_agree(
    empty_batch_parity: object, protocol: object
) -> None:
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

    Each fingerprint line carries a table name, a ROW COUNT and a SHA-256 of that
    table's canonical primary-key-ordered dump - integers and hex text only, so
    they introduce no decimal of their own (R-2) - and both files live under
    `run-logs/`, OUTSIDE every compared tree, so neither can leak into a capture
    (R-6). The digest is what makes the record decisive: EQUAL COUNTS WITH
    DIFFERENT VALUES is precisely the disagreement a count-only record cannot see.
    They are compared AS BYTES and never parsed: interpreting them here would be
    the added validation R-3 forbids, and the corroboration that the seeded tables
    actually hold rows is taken from the dumps instead, in
    `test_affected_tables_are_byte_identical_to_the_seed`.

    THE ORACLE-SIDE FINGERPRINT MAY LEGITIMATELY BE ABSENT, AND THAT IS ASSERTED
    RATHER THAN ASSUMED. `harness/run_cobol_scenario.sh` writes no pre-run
    fingerprint - its own SHA-256 transcript fingerprints come at the END of the
    run [harness/run_cobol_scenario.sh acas_run_fingerprint_transcript] - so the Python runner treats a
    missing counterpart as a WEAKER GUARANTEE rather than a fault: it emits the
    note at [harness/run_python_scenario.sh acas_py_seed_fingerprint] and records
    `seed cross-check = unverified` in its summary, then continues.

    So BOTH dispositions are asserted, and neither is silent:

      * PRESENT - the two files must be byte-identical, AND the runner must NOT
        have reported the weaker guarantee. A cross-check that happened and a
        cross-check that was skipped must never look the same.
      * ABSENT - the runner must have SAID SO on its own transcript. A tolerance
        nobody declared is indistinguishable from a fingerprint that was silently
        lost, and it is exactly the second case this test exists to catch.

    An earlier form of this test simply skipped the comparison when the oracle-side
    file was missing, which meant a lost fingerprint and a deliberately-absent one
    produced the same green result. Requiring the file instead would assert a
    contract the harness does not offer, so the disposition is what is asserted.

    ⭐ THE RECORD CARRIES ONE MORE LINE THAN THE SCENARIO BOUNDS, and that is the
    contract rather than a discrepancy. Both runners append the PARAMETER ROW,
    `SYSTEM-REC`, to the bounded tables - it is the one in-scope table BOTH cycles
    write on EVERY route (ambiguity `Q-7`), so leaving it wholly unobserved would be
    a real coverage hole, while adding it to `affected_tables` is impossible: a dump
    is `SELECT *` and `RDBMS-PASSWD char(12)` [copybooks/wssystem.cob:L139] is one of
    its 169 columns. The expected order is therefore taken from
    `protocol.fingerprinted_tables`, which is the same order
    `acas_py_resolve_fingerprint_tables` builds, rather than restated here - a second
    copy of that rule is how the two silently drift apart (R-4).

    Args:
        empty_batch_parity: The completed `ParityRun`, whose `paths.run_logs` is
            the transcript directory both fingerprints live in, and whose
            `python_run` carries the runner's own transcript.
        protocol: The stage bundle, read only for `fingerprinted_tables` - the
            scenario's DECLARED EFFECT in declared order, plus the parameter row. The
            fingerprint carries one line per declared table, not one per COMPARED
            table: the comparison is bounded by all 22 in-scope tables, while this
            record holds the seeded state of the tables the scenario declares.
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
    #  PER DECLARED EFFECT, NOT PER COMPARISON BOUND. The runner fingerprints the
    #  scenario's own `affected_tables` in declared order, plus the parameter row when
    #  the scenario has not already declared it; `run.tables` is the 22-table bound the
    #  capture and the diff cover, so comparing against THAT would demand a line for
    #  every in-scope table. `protocol.fingerprinted_tables` is the protocol's own
    #  authority for the order, so this test cannot drift away from what the runners
    #  actually write.
    expected_tables = protocol.fingerprinted_tables(run)
    assert len(lines) == len(expected_tables), (
        f"the seed fingerprint at {python_fingerprint} carries {len(lines)} "
        f"line(s) where the contract is {len(expected_tables)} - this scenario's "
        f"DECLARED tables, plus the parameter row when it is not already among them, "
        f"and NOT the {len(run.tables)} tables the comparison is bounded by:\n"
        f"{recorded.decode('utf-8')}"
        f"  One line per declared table is the contract, and the count is what the "
        f"two sides compare. The comparison itself covers all "
        f"{len(run.tables)} in-scope tables."
    )
    for line, table in zip(lines, expected_tables):
        # One line per table, the table name first, tab-separated from its count.
        # Only the NAME and its position are read; the counts are never
        # interpreted here (R-3) - the corroboration that the seeded tables hold
        # rows is taken from the dumps in the byte-identity test instead.
        recorded_table = line.split("\t")[0]
        assert recorded_table == table, (
            f"the seed fingerprint at {python_fingerprint} names "
            f"{recorded_table!r} where the record order names {table!r}:\n"
            f"{recorded.decode('utf-8')}"
            f"  THE DECLARED ORDER IS PART OF THE CONTRACT. The two sides compare "
            f"these files byte for byte, so a reordering on one side alone would "
            f"be reported as a starting-state disagreement."
        )

    # THE RUNNER'S OWN WORD ON THE CROSS-CHECK, read from the stage-6 transcript.
    # `acas_py_note` writes to the runner's output, so the note is evidence rather
    # than inference.
    transcript = (
        f"{empty_batch_parity.python_run.stdout}\n"
        f"{empty_batch_parity.python_run.stderr}"
    )
    declared_unverified = UNVERIFIED_NOTE in transcript

    if not cobol_fingerprint.is_file():
        # ABSENT. Admissible ONLY because the runner declared it. Without this
        # assertion a fingerprint that was written and then lost would produce
        # exactly the same green result as one that was never written at all.
        assert declared_unverified, (
            f"there is no oracle-side seed fingerprint at {cobol_fingerprint}, and "
            f"the Python runner DID NOT SAY SO on its transcript.\n"
            f"  Absence is admissible only as the WEAKER GUARANTEE the runner "
            f"declares at [harness/run_python_scenario.sh acas_py_seed_fingerprint], which writes "
            f"{UNVERIFIED_NOTE!r} and records `seed cross-check = unverified`. An "
            f"undeclared absence is indistinguishable from a fingerprint that was "
            f"written and then lost, and in THIS scenario - where both dumps are "
            f"legitimately near-empty - that is the difference between a "
            f"comparison and no comparison at all.\n"
            f"  stage 6 transcript:\n{empty_batch_parity.python_run.describe()}"
        )
        return

    # PRESENT. The runner must have performed the cross-check rather than reported
    # it skipped: `matched` and `unverified` must never be confusable.
    assert not declared_unverified, (
        f"the oracle-side seed fingerprint EXISTS at {cobol_fingerprint}, yet the "
        f"Python runner reported the weaker guarantee "
        f"{UNVERIFIED_NOTE!r} on its transcript. The cross-check at "
        f"[harness/run_python_scenario.sh acas_py_seed_fingerprint] therefore looked somewhere "
        f"else, and nothing has actually been cross-checked.\n"
        f"  stage 6 transcript:\n{empty_batch_parity.python_run.describe()}"
    )
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


@pytest.mark.database
@pytest.mark.oracle
def test_system_record_parity_by_digest_as_well_as_by_dump(empty_batch_parity: object, protocol: object) -> None:
    """THE PARAMETER ROW IS BOUNDED TWICE - by the dump, and by a digest of it.

    WHAT THIS CLOSES. An earlier draft kept `SYSTEM-REC` off every scenario's
    `affected_tables` and justified that by claiming no side writes it. That claim is
    FALSE:
    `acas_posting/cli/args.py`'s `overrewrite` reproduces
    [general/general.cbl:L656-L672] and every one of the seven routes calls it, so the
    parameter row is written on BOTH sides of every scenario. Until this assertion
    existed, a regression in that persistence produced an EMPTY DIFF and a green run.

    WHICH KEYS THIS ROUTE WRITES, ON A RUN THAT POSTS NOTHING. `gl_post_cycle` binds
    `general_menu_state`, so `overrewrite` rewrites KEY 1, KEY 2 and KEY 4 even though
    the cycle found no eligible batch and wrote no posting. THAT IS THE POINT: a run
    that is a no-op over the three tables this scenario reasons about is NOT necessarily a
    no-op over the parameter row, so this scenario's `expected_table_effect: unchanged`
    is a claim about the row too. It was MEASURED rather than assumed: the frozen
    `Date-Form` write-back [copybooks/wssystem.cob:L127] does not move the row's digest on
    any of the four scenarios that declare `unchanged`, so the row is declared, dumped and
    compared like any other, and the digest this test reads is a second, independent bound
    on the same persistence.

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
    over the eight scenarios that existed when the measurement was taken, which is all
    four `unchanged` ones; the ninth, `end_of_cycle_gl`, declares `changed` and moves the
    row by construction, Phase 5 advancing the cycle and rotating the quarter counter.
    So declaring the row falsifies no effect claim; the digest is the belt to the dump's
    braces.

    Args:
        empty_batch_parity: The completed, guarded run. The assertion needs its
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
    cobol_record, python_record = protocol.assert_system_record_parity(empty_batch_parity)

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
