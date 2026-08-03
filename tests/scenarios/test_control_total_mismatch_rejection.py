"""CONTROL-TOTAL MISMATCH REJECTION - THE SCENARIO WHOSE EXPECTED STATE IS AN ABSENCE.

Scenario `control_total_mismatch`, subsystem `general`, operation `gl_post_cycle`, and
THE ONLY NON-ZERO TERMINAL DISPOSITION IN THE ENTIRE SCENARIO SET: terminate code 5. It
drives the eight-stage parity protocol and asserts an EMPTY normalised diff, exactly as
the other seven do - but here the empty diff certifies that *nothing happened* on either
side, which is a materially different claim and needs a materially more careful test.
Every other scenario can fall back on "the diff was suspiciously empty" as a sanity
check; this one cannot, because unchanged tables ARE what success looks like.

-------------------------------------------------------------------------------
0. THE TWO STANDING FACTS
-------------------------------------------------------------------------------

THERE IS NO USER RULES DOCUMENT. `review_rules` returns exactly "No user rules
provided.", so no rules file exists to consult and none should be looked for. The
binding constraints are the Agent Action Plan's own numbered rules R-1 to R-6 (Plan
section 0.7.2), whose exact wording lives in the requirements themselves. Where the Plan
is silent, enterprise-standard best practice applies and nothing is invented.

THE PREMISE IS INVERTED. Plan section 0.8.2, verbatim:

    "There is no test suite: compiled COBOL execution is the behavioral specification,
    defects included. A defect reproduced is correct; a defect fixed is a failure."

Corollary, and the rule every assertion below obeys: A TEST THAT ASSERTS CORRECT
ACCOUNTING RATHER THAN OBSERVED BEHAVIOUR IS ITSELF A DEFECT. So no test here predicts a
figure. Each state test asserts AGREEMENT - between the compiled oracle and the migrated
cycle, and between both of them and the seed - and never a value of its own choosing.

Specific to this file: the control-total gate adds VAT into the actual gross BEFORE the
equality test, and TWO EARLIER EXITS bypass that mutation entirely, one of them leaving
`batch-status` unassigned. The ordering is not tidied, the unassigned status is not
initialised, and no third comparison is added (R-4).

WHY AN EMPTY DIFF CAN BE TRUSTED AT ALL. Plan section 0.6.6: "a non-empty diff is always
a real behavioral difference and never an artefact of the comparison." That is earned by
the frozen schema rather than asserted: every in-scope table has a single-column primary
key, zero secondary indexes, no `TIMESTAMP` column and no `AUTO_INCREMENT`, so the dump
is `SELECT * FROM <table> ORDER BY <primary key>` with no tie-breaking and no masking.

-------------------------------------------------------------------------------
1. GENERAL-LEDGER-SPECIFIC. THERE IS NO SALES OR PURCHASE VARIANT, AND CANNOT BE
-------------------------------------------------------------------------------

Plan section 0.6.4: Sales and Purchase batches "balance by construction, so the
control-total mismatch scenario is General-Ledger-specific - there is no meaningful way
to construct an unbalanced sales batch." That is not a judgement call; it is visible in
four adjacent statements. [sales/sl060.cbl:L1115-L1121], read from this checkout:

    1115|      move     "CR" to Post-Vat-Side.
    1116|      move     "SL" to Post-Code in WS-Posting-Record.
    1117| *>
    1118|      add      Post-Amount  to  input-gross.
    1119|      add      Post-Amount  to  actual-gross.
    1120|      add      vat-amount   to  input-vat.
    1121|      add      vat-amount   to  actual-vat.

and identically on the Purchase side, [purchase/pl060.cbl:L970-L976]:

     970|      move     "DR" to post-vat-side.
     971|      move     "PL" to post-code in WS-Posting-Record.
     972| *>
     973|      add      post-amount  to  input-gross.
     974|      add      post-amount  to  actual-gross.
     975|      add      vat-amount   to  input-vat.
     976|      add      vat-amount   to  actual-vat.

THE ENTERED AND THE ACTUAL TOTALS ARE INCREMENTED FROM THE SAME SOURCE IN ADJACENT
STATEMENTS. `input-gross` and `actual-gross` both receive `post-amount`; `input-vat` and
`actual-vat` both receive `vat-amount`. They cannot disagree, so a Sales or Purchase
batch cannot fail a control-total comparison however it is seeded. Consequently BOTH
harness runners refuse this scenario for a non-`general` subsystem with harness-fault
status, and `test_scenario_is_general_ledger_only` asserts the pin in isolation so that
the refusal can never be reached by accident.

-------------------------------------------------------------------------------
2. THE CONTROL-TOTAL GATE ITSELF - [general/gl051.cbl:L1096-L1134], VERBATIM
-------------------------------------------------------------------------------

    1096|  end-batch.
    1097| *>********
    1098| *>
    1099|      if       z = 99
    1100|               go to  main-exit.       <- EXIT #1: batch-status UNASSIGNED
    1101|      if       not truet
    1102|               move  0  to  batch-status
    1103|               go to  main-exit.       <- EXIT #2: rejects BEFORE L1109
    1104| *>
    1105|      subtract input-vat  from  input-gross  giving  l9-amount.
    1106|      move     input-vat    to  l9-vat.
    1107|      move     actual-gross to  l10-amount.
    1108|      move     actual-vat   to  l10-vat.
    1109|      add      actual-vat   to  actual-gross.  <- VAT ADDED BEFORE THE TEST
    1110| *>
    1111|      if       line-cnt > Page-Lines - 12
    1112|               perform headings.
    1113|      write    print-record  from  line-8 after 3.
    1114|      write    print-record  from  line-9 after 2.
    1115|      write    print-record  from  line-10 after 2.
    1116| *>
    1117|      if       input-gross = actual-gross
    1118|        and    input-vat   = actual-vat
    1119|               move  1  to  batch-status
    1120|      else
    1121|               move  0  to  batch-status.
    1122| *>
    1123|      move     "*********************"  to  l11-status.
    1124|      write    print-record  from  line-11 after 3.
    1125| *>
    1126|      if       batch-status = 1
    1127|               move  "* Batch Verified Ok *"  to  l11-status
    1128|      else
    1129|               move  "*  Batch In ERROR   *"  to  l11-status.
    1130| *>
    1131|      write    print-record  from  line-11 after 1.
    1132|      move     "*********************"  to  l11-status.
    1133|      write    print-record  from  line-11 after 1.
    1134|      go       to main-exit.

THREE FACTS ABOUT THAT PARAGRAPH, EACH LOAD-BEARING.

(a) `add actual-vat to actual-gross` at L1109 HAPPENS BEFORE the equality test at
    L1117-L1118, because the entered figure is VAT-inclusive. Reversing the two "would
    reject every batch that carries VAT" (Plan section 0.6.4). The ordering is
    preserved, and `test_vat_is_added_before_the_comparison_is_documented` locks the two
    locators against drift by reading the frozen source.

(b) THE FLAG TESTED AT L1101 IS SPELLED `truet`, AND BOTH SPELLINGS EXIST IN THE PROGRAM
    MEANING DIFFERENT THINGS - measured in this checkout, and recorded because the two
    differ by a single transposed letter and a well-meaning reader would repair one into
    the other. [general/gl051.cbl:L175-L177]:

         175      03  trutht              pic 9.
         176          88  falset                           value zero.
         177          88  truet                            value 1.

    `trutht` is the data item; `falset` and `truet` are its two condition names, so
    `if not truet` means `if trutht not = 1`. Neither spelling is corrected (R-4). L175
    carries NO `value` clause, and the ONLY paragraph that sets the item TRUE is
    `move 1 to trutht.` in the OUT-OF-SCOPE `gl050d` section [general/gl051.cbl:L967] -
    which is a second, independent demonstration of the point in section 3 below.

(c) TWO EARLIER EXITS the Plan's prose omits, and both are part of the specification.
    L1099-L1100 (`z = 99`) returns with `batch-status` NEVER ASSIGNED AT ALL - recorded
    as an open question in `docs/migration/ambiguity-resolutions.md`, because what the
    field then holds is whatever the record carried when it was read, and only execution
    settles it. L1101-L1103 (`not truet`) rejects BEFORE L1109, so on that path the VAT
    mutation never happens. Neither is initialised, guarded or merged.

The two accumulators that feed the comparison are [general/gl051.cbl:L1063-L1064]:

    1063|      add      post-amount  to  actual-gross.
    1064|      add      vat-amount   to  actual-vat.

THERE IS NO `actual-DR` AND NO `actual-CR` FIELD. [copybooks/wsbatch.cob:L40-L44] holds
exactly four money fields, all UNSIGNED packed decimal under one group usage clause:

      40|      03  Amounts                         comp-3.
      41|          05  Input-Gross     pic 9(9)v99.
      42|          05  Input-Vat       pic 9(9)v99.
      43|          05  Actual-Gross    pic 9(9)v99.
      44|          05  Actual-Vat      pic 9(9)v99.

and the frozen schema holds all four as `decimal(14,2) unsigned`
[mysql/ACASDB.sql:L90-L93]. No DR/CR pair is invented anywhere in this file.

-------------------------------------------------------------------------------
3. `gl051` HAS NO CLI ENTRY POINT, SO THIS SCENARIO REACHES THE GATE'S CONSEQUENCE
   AND NEVER THE GATE - THE SINGLE MOST MISUNDERSTANDABLE FACT IN THIS FILE
-------------------------------------------------------------------------------

NEITHER RUNNER MAY DRIVE `gl051`, and neither does. Only `batch-print` section 999 and
its `end-batch` paragraph [general/gl051.cbl:L1096-L1134] are in scope at all;
`gl051-Main` section 359, `proof-all` section 474, `gl050c` section 496,
`batch-amendment` section 825 and `gl050d` section 961 are out of scope, because Plan
section 0.2.2 excludes "the whole of `general/gl051.cbl` EXCEPT its control-total
block". `acas_posting/programs/ gl051_batch_control_check.py` is therefore a LIBRARY
FUNCTION with no command line, and it is exercised at the arithmetic tier by
`tests/arithmetic/test_control_total_comparison.py`.

CONSEQUENTLY: THE BATCH STATUS IS SEEDED, NOT COMPUTED. This scenario begins from a
batch that is ALREADY open - the state `gl051` would have left behind after its L1121
(or its L1102) - and asks one question of the posting cycle: what does the cycle do when
it finds one? No test in this file re-evaluates the comparison, and none asserts
`input_gross != actual_gross` arithmetically. The mismatch is a PREMISE of the seed and
the arithmetic belongs to the other tier.

For completeness, and because a reader chasing `gl051`'s arithmetic should not have to
find it twice: its two `ROUNDED` VAT computes are at [general/gl051.cbl:L791] and
[general/gl051.cbl:L796]; its account-scaling multiplies and divides at L604, L607,
L654, L657 and L803; its print-only divides at L1035, L1037 and L1044. None of them is
on this route.

-------------------------------------------------------------------------------
4. THE FOUR-LINK ABORT CHAIN, CROSSING THREE PROGRAMS
-------------------------------------------------------------------------------

LINK 1 - THE SEED. `Batch-Status = 0` makes `88 Status-Open` true
[copybooks/wsbatch.cob:L25-L27]:

      25|      03  Batch-Status        pic 9.
      26|          88  Status-Open                    value 0.
      27|          88  Status-Closed                  value 1.

LINK 2 - `gl070` PHASE 1 DETECTS IT. `gl071a section.` opens at
[general/gl070.cbl:L300]; the loop is L305-L318:

     305|  loop.
     308|      perform  GL-Batch-Read-Next.        *> read batch-file next ...
     309|      if       fs-reply = 10
     310|               go to  end-run.
     312|      if       bcycle not = scycle              <- CYCLE FILTER #1
     313|               go to  loop.
     314|      if       status-open                      <- THE OPEN-BATCH DETECTOR
     315|               move  1  to  a.
     316|      go       to loop.
     318|  end-run.

LINK 3 - THE MAINLINE RAISES TERMINATE CODE 5 [general/gl070.cbl:L281-L298]:

     281|  menu-input2.
     283|      move     zero  to  a.
     284|      display  "Phase - 1.  Batch Check" at 0801 ...
     285|      perform  gl071a.
     287|      if       a = 1
     288|               perform gl060a                   <- diagnostic display only
     289|               move 5 to ws-term-code           <- ** THE RAISE **
     290|               go to  main-exit.
     292|      display  "Phase - 2.  Transaction Pre-process" at 0801 ...
     293|      perform  gl071b.
     295|  main-exit.
     298|      goback.

    LOCATOR CORRECTION, recorded because the Plan misattributes all three. The Plan
    cites L283 for the Phase-1 label, L291 for the Phase-2 label and L288 for the raise.
    THE VERIFIED LINES IN THIS CHECKOUT ARE L284, L292 AND L289; L283 is `move zero to
    a.` and L288 is `perform gl060a`. The verified ones are cited throughout.

LINK 4 - THE MENU RETURNS [general/general.cbl:L805-L815]:

     805|  load08.
     808|      move     "gl070" to ws-called.
     809|      perform  load00.
     810|      if       ws-term-code = 5
     811|               go to display-menu.              <- ** THE HARD GATE **
     812|      move     "gl071" to ws-called.
     813|      perform  load00.
     814|      move     "gl072" to ws-called.
     815|      go       to load00.

SO `gl071` AND `gl072` NEVER RUN AT ALL, and neither does Phase 2 (`gl071b`), because
L290 leaves the mainline before L293 is reached. Three separate consequences follow:

  * The gate is a HARD stop between phases and never a warning. `acas_posting/cli/
    gl_post_cycle.py` reproduces it at its own L510-L511 against
    `args.GL_ABORT_TERM_CODE`.
  * `5` IS NOT `> 7`, so `load00`'s route to the system-record persistence path -
    `if ws-term-code > 7 / go to overrewrite.` [general/general.cbl:L720-L721] - is NOT
    taken. Even the COBOL side does not run `overrewrite` on this route.
  * `perform gl060a` at L288 is a DIAGNOSTIC DISPLAY WITH NO DATABASE EFFECT, so per
    Plan section 0.3.4 it becomes a log record on the Python side. It must not alter
    control flow and must never appear in a table dump;
    `test_diagnostic_display_has_no_database_effect` asserts precisely that.

THE ABORT GATES DIVERGE BY LEDGER AND ARE NOT HARMONISED (R-4). General: `if
ws-term-code = 5 / go to display-menu` [general/general.cbl:L810-L811]. Sales: `if
ws-term-code not = zero`, TWICE [sales/sales.cbl:L761-L762, L765-L766]. Purchase: NONE -
the gate is commented out [purchase/purchase.cbl:L755-L758]. IRS: none, and no dispatch
wrapper at all [irs/irs.cbl:L666-L672]. Only the General form is exercised here; the
other three are recorded so the asymmetry stays visible.

EXIT STATUSES ARE BEHAVIOURAL DATA. Only three in-scope programs set `WS-Term-Code` at
all: `gl070` to 5 [general/gl070.cbl:L289], `sl055` to 8 [sales/sl055.cbl:L344] and
`pl055` to 8 [purchase/pl055.cbl:L286]; and `acas_posting/cli/args.py`'s
`exit_status_for(term_code)` returns 0 for 0 and THE TERM CODE ITSELF otherwise, so a GL
open-batch abort surfaces as process exit 5. TERM CODE 8 IS UNREACHABLE IN THIS HARNESS
- both raise sites sit inside `if FS-Cobol-Files-Used` ([sales/sl055.cbl:L326] wrapping
L344, [purchase/pl055.cbl:L266] wrapping L286) and every scenario pins
`file_system_used: 1`. SO 5 IS THE ONLY OBSERVABLE NON-ZERO TERM CODE ANYWHERE IN THE
SUITE, AND THIS SCENARIO IS THE ONLY PLACE IT APPEARS.

THREE CATEGORIES, NEVER CONFLATED: success (INCLUDING a reproduced abort the scenario
definition predicted) - behavioural difference (the dump is still taken) - harness
fault. `argparse` exit 2 means the runner built a bad command line, which is a HARNESS
FAULT and never a difference. In this scenario THE ABORT IS THE EXPECTED SUCCESS: a run
that exits 5 exactly as the definition predicts is a PASS.

-------------------------------------------------------------------------------
5. THE EXPECTED DATABASE STATE IS AN ABSENCE
-------------------------------------------------------------------------------

Plan section 0.6.5, on a run-aborting rejection: "The database effect is therefore THE
ABSENCE of everything the later phases would have written." Named explicitly, every
mutation that MUST NOT HAVE HAPPENED is in [general/gl072.cbl]:

     331|      add      post-amount  to  ledger-balance.   <- MUST NOT HAPPEN
     372|  end-batch.
     375|      move     1  to  cleared-status.             <- MUST NOT HAPPEN
     376|      move     run-date  to  posted.              <- MUST NOT HAPPEN
     377|      perform  GL-Batch-Rewrite.   *> rewrite batch-record.  <- MUST NOT
     379|  end-account.
     382|      perform  GL-Nominal-Rewrite. *> rewrite ledger-record. <- MUST NOT

So `GLBATCH-REC` keeps its seeded `BATCH-STATUS`, its seeded `CLEARED-STATUS` and its
seeded `POSTED`; `GLLEDGER-REC` balances are unmoved; `GLPOSTING-REC` is untouched. ALL
THREE TABLES MUST BE IDENTICAL TO THE SEED, ON BOTH SIDES - which is a three-way
agreement and is what `test_gl071_and_gl072_never_ran` asserts.

-------------------------------------------------------------------------------
6. `Bcycle` MUST EQUAL `system.cyclea` - THE MOST DANGEROUS TRAP IN THIS FILE
-------------------------------------------------------------------------------

The seeded batch's `Bcycle` [copybooks/wsbatch.cob:L34] must equal the seeded system
record's `Cyclea` [copybooks/wssystem.cob:L62], which `Scycle` redefines
[copybooks/wssystem.cob:L63]. If they differ, Phase 1's CYCLE FILTER at
[general/gl070.cbl:L312-L313] skips the batch before the detector at L314-L315 is ever
reached; `a` stays zero; L287 is false; the cycle runs all three phases and ends with
`ws-term-code = 0` - AND THE DIFF IS STILL EMPTY. The scenario would pass while proving
nothing whatever. That is why `test_expected_term_code_is_five` exists as an assertion
in its own right: an exit of 0 on this route is a FAILURE OF THE SCENARIO'S PREMISE and
not a success. `system.period` is inert here - it is the cycles-per-quarter divisor used
only by `gl080`, which no scenario in this harness drives.

-------------------------------------------------------------------------------
7. WHAT THIS FILE DELEGATES, AND WHAT IT REFUSES TO DO
-------------------------------------------------------------------------------

EVERYTHING GOES THROUGH `tests/conftest.py`. This file NEVER imports `harness` in any
form, never reaches a harness path with `importlib`, never constructs a command line, an
`argv` list or a `subprocess` call, never hard-codes a CLI flag, and never invokes
`python -m acas_posting.cli.gl_post_cycle` (R-1). It does not import
`acas_posting.cli.gl_post_cycle` or `acas_posting.programs.gl051_batch_control_check`
either. `harness/` has no `__init__.py` and `pyproject.toml` packages only
`acas_posting*`, which is the structural enforcement of R-1; the three harness modules
arrive solely through conftest's explicit-path loaders, exposed as the `harness`
fixture. The protocol is driven by conftest's single composition helper, and the
scenario's promoted-answer map is empty because `gl_post_cycle` promotes no interactive
answer.

THE EIGHT STAGES, in the one order they may run (R-3, strictly sequential - parallel
runs against one shared MariaDB would break the protocol outright, which is why
`pyproject.toml` names the parallel-runner and execution-reordering plugins it excludes,
and depends on none of them):

    1 seed.sh   2 run_cobol_scenario.sh   3 dump --side cobol   4 normalize.py
    5 reset_db.sh   6 run_python_scenario.sh   7 dump --side python   8 diff_states.py

THE THREE-WAY EXIT CONTRACT OF STAGE 8:

    0  the two trees are identical, and stdout is EMPTY - zero bytes, not a banner  PASS
    1  a real behavioural difference                                             FAILURE
    2  THE COMPARISON COULD NOT BE PERFORMED                                       ERROR

"A test that treats 'could not compare' as 'no differences' is the single worst bug
available in this tree." THE 0-VERSUS-2 CONFUSION IS AT ITS MOST LETHAL HERE, because
the expected state is an absence: a missing dump tree and a correctly empty change set
can be made to look alike by careless code. Exit 2 is therefore mapped to an exception
and never to a pass, and `test_diff_exit_contract_is_honoured` proves the mapping by
provoking it. `test_dump_is_wellformed_on_both_sides` closes the same hole from the
other side - it is what distinguishes "compared, and identical" from "never dumped".

ALWAYS DUMP, THEN CLASSIFY. The COBOL runner exits 5 here BY DESIGN, and the dump is
taken regardless: conftest's composition applies `raise_for_status()` to seed, reset,
both dumps and both normalisations, and DELIBERATELY NOT to the two run stages. Absence
is evidence - and on this route it is the only evidence there is.

Comparison is EXACT: no tolerance, no epsilon, no case- or whitespace-insensitivity and
no numeric coercion; `1` against `"1"` IS a difference. Rows align by PRIMARY-KEY VALUE,
never by position. The report's two labels are `cobol` and `python` and are not
configurable. `--max-differences` truncates the report only; it always prints the true
total and never changes the exit code.

BOUNDING, NEVER IGNORING. There is no ignore-list, no tolerance-list and no "known
difference" allowance anywhere in this file or in the diff path. The comparison is
bounded by the scenario's own affected-table list and by nothing else. Two structural
asymmetries make that necessary and neither is a migration defect: the menu shell's exit
path runs `overrewrite`, persisting `SYSTEM-REC` (key 1), `SYSDEFLT-REC` (key 2) and
`SYSTOT-REC` (key 4) [general/general.cbl:L656-L670], which the Python command line has
no menu to do; and `sl830` runs only on the COBOL side [sales/sales.cbl:L759]. On THIS
route the first is doubly moot, since `load00` reaches `overrewrite` only `if
ws-term-code > 7` [general/general.cbl:L720-L721] and 5 is not greater than 7. A census
across all twelve in-scope programs finds ZERO `System-*` facade verbs, so the four
system tables appear on no scenario's list at all. Sales and Purchase persist keys 1 and
4 only, never key 2 ([sales/sales.cbl:L636], [purchase/purchase.cbl:L629]) - irrelevant
here, recorded for consistency. The four autogen tables are never seeded and never
listed, and both runners assert after the run that all four are still empty; that
assertion lives in the runners.

NORMALISATION DOES EXACTLY THREE THINGS AND THERE IS NO FOURTH. It is delegated entirely
to `harness/normalize.py` and nothing here reimplements or extends it:

  1. TRAILING spaces in fixed-character columns, `rstrip(" ")` only - a COBOL
     alphanumeric `MOVE` is left-justified with right padding, so LEADING SPACES ARE
     CONTENT. ASCII U+0020 only, by declared type, `char(1)` included. Motivated by
     ANOMALY A-12, the width drift `pic x(24)` [copybooks/wsledger.cob:L27] to `PIC
     X(32)` [common/nominalMT.cbl:L299] to `char(32)` [mysql/ACASDB.sql:L127]. On this
     route it touches `GLBATCH-REC.DESCRIPTION` `char(24)` [mysql/ACASDB.sql:L94] from
     [copybooks/wsbatch.cob:L45], `CONVENTION` and `BATCH-DEF-CODE` `char(2)` and
     `BATCH-DEF-VAT` `char(1)`, plus `GLLEDGER-REC.LEDGER-NAME` `char(32)` and
     `GLPOSTING-REC.POST-CODE`, `POST-LEGEND` and `POST-VAT-SIDE`.
  2. DECIMAL SCALE RENDERING AT THE DECLARED SCALE, which is NOT uniformly 2. Here the
     four `GLBATCH-REC` control totals are `decimal(14,2) unsigned`
     [mysql/ACASDB.sql:L90-L93] matching the unsigned `pic 9(9)v99 comp-3` of
     [copybooks/wsbatch.cob:L40-L44], while `GLLEDGER-REC.LEDGER-BALANCE` is
     `decimal(10,2)` [mysql/ACASDB.sql:L128] from a SIGNED `pic s9(8)v99 comp-3`.
  3. TWO- VERSUS FOUR-DIGIT DATE TEXT FORMS, under an EXPLICIT FIVE-COLUMN ALLOW-LIST
     and nothing wider: `GLPOSTING-REC.POST-DAT`, `IRSPOSTING-REC.POST4-DAT`,
     `PSIRSPOST-REC.IRS-POST-DAT`, `SYSTEM-REC.STATS-DATE-PERIOD` and
     `SALEDGER-REC.SALES-STATS-DATE`. `GLPOSTING-REC.POST-DAT` `char(8)`
     [mysql/ACASDB.sql:L158] is on this scenario's list, so job 3 is live here.
     `char(8)` DOES NOT IMPLY DATE: `GLBATCH-REC.ENTERED`, `PROOFED`, `POSTED` and
     `STORED` are `int(8) unsigned` [mysql/ACASDB.sql:L86-L89] binary day numbers from
     four `binary-long` fields [copybooks/wsbatch.cob:L36-L39], and job 3 must not touch
     them. That matters directly: `POSTED` is one of the columns whose NON-change proves
     the abort.

-------------------------------------------------------------------------------
8. THE SEED, AND WHY EACH PIECE OF IT IS THERE
-------------------------------------------------------------------------------

FOUR FLAT FILES, and exactly four: `system.dat`, `ledger.dat`, `batch.dat`,
`posting.dat`. The loader mapping is the frozen script's own per-file contract -
`system.dat` to the four-loader block `systemLD` then `sys4LD` then `finalLD` then
`dfltLD` [common/masterLD.sh:L51-L87]; `batch.dat` to `glbatchLD`
[common/masterLD.sh:L94]; `ledger.dat` to `nominalLD` [common/masterLD.sh:L103];
`posting.dat` to `glpostingLD` [common/masterLD.sh:L109].

THE SEED'S STRUCTURAL INTENT, documented because this file asserts the definition rather
than the fixture's contents:

  * THE BATCH MUST BE `Status-Open`, `Batch-Status = 0` [copybooks/wsbatch.cob:L25-L26].
    This is the SEEDED CONSEQUENCE of `gl051`'s rejection at L1121 (or its L1102) and is
    not a value this scenario computes.
  * `WS-Ledger = 1`, so `88 GL-Batch` is true [copybooks/wsbatch.cob:L15-L16].
  * `Cleared-Status = 0`, so `88 Waiting` is true [copybooks/wsbatch.cob:L29-L31].
  * `Bcycle` equal to `system.cyclea`, for the reason in section 6 above.
  * The four money fields seeded so that `Input-Gross`/`Input-Vat` DISAGREE with
    `Actual-Gross`/`Actual-Vat` in the way [general/gl051.cbl:L1117-L1118] would have
    detected, so a reader can see IN THE SEED why the batch is open. THIS IS
    DOCUMENTATION OF INTENT; the scenario does not re-evaluate the comparison, and
    making them balance would be a failure rather than an improvement (R-4).
  * `posting.dat` carrying postings that belong to the open batch, so that the ABSENCE
    of their effect is meaningful. A batch with no postings would make this route
    indistinguishable from `empty_batch`.

SEEDING CONSTRAINTS, DOCUMENTED AND NOT IMPLEMENTED HERE (R-3). No DDL of any kind:
`mysql/ACASDB.sql` is applied VERBATIM and already carries all 33 `DROP TABLE IF EXISTS`
beside its 33 `CREATE TABLE`, so re-applying the frozen file IS the drop-and-recreate;
it contains neither `CREATE DATABASE` nor `USE`, so the database name goes on the client
command line. AUTOCOMMIT MUST BE OFF DURING SEEDING - the batch loader says so in its
own header, it uses commit and rollback, and it warns that the default is on
[common/glbatchLD.cbl:L9-L13]. `common/masterLD.sh` IS NEVER INVOKED: its own author
marks it untested at [common/masterLD.sh:L4], all 24 of its loader lines
[common/masterLD.sh:L93-L116] omit the `;` before `fi` so `bash -n` rejects the file,
and it ends by paging a log through `less`, which would block a non-interactive run
forever. It is FROZEN and is NOT fixed; `harness/seed.sh` reproduces its documented
per-file contract [common/masterLD.sh:L44-L115] and checks loader exit codes explicitly
- 128 parameters unset, 64 RDBMS unset, 16 write error, anything above 63 aborting.
Further R-4 items preserved rather than fixed: the `dfltLD` strict-versus-lenient exit
asymmetry [common/masterLD.sh:L83]; the charset caveat, `SET NAMES utf8mb4`
[mysql/ACASDB.sql:L16] against 33 tables declared `DEFAULT CHARSET=utf8mb3`; the
`tinyint(1) unsigned` display- width quirk on `GLBATCH-REC.BATCH-STATUS`
[mysql/ACASDB.sql:L83] and `CLEARED-STATUS` [mysql/ACASDB.sql:L84]; and the
`acas007`-versus-`acas008` `Open-Output` divergence described in section 9. NO ADDED
VALIDATION anywhere: the `batch-status` that [general/gl051.cbl:L1099-L1100] leaves
unassigned is not initialised, no bounds check is introduced, no reconciliation is
performed and no error message is invented.

-------------------------------------------------------------------------------
9. THE AFFECTED-TABLE LIST - EXACTLY THREE, ALPHABETICAL, EACH PROVING AN ABSENCE
-------------------------------------------------------------------------------

`GLBATCH-REC`, `GLLEDGER-REC`, `GLPOSTING-REC`, and the ORDER IS LOAD-BEARING: the seed
fingerprint is written in the declared order and a disagreement between
`cobol.seed-fingerprint` and `python.seed-fingerprint` is a HARNESS FAULT rather than a
behavioural difference [harness/run_python_scenario.sh:L3176, L3206]. All three are on
the list PRECISELY TO PROVE ABSENCE - `GLBATCH-REC` proves the batch was not stamped,
`GLLEDGER-REC` proves no balance moved, `GLPOSTING-REC` proves nothing was consumed. The
eleven out-of-scope tables are never dumped, and the 22-name in-scope inventory and
every primary key are read from the harness rather than restated here (R-4).

CORROBORATING CENSUS, measured over this checkout. `gl072` issues exactly EIGHT facade
verbs - `GL-Batch-Open` L276, `GL-Nominal-Open` L277, `GL-Batch-Rewrite` L377,
`GL-Nominal-Rewrite` L382, `GL-Nominal-Read-Next` L408, `GL-Batch-Close` L441,
`GL-Nominal-Close` L442, `GL-Batch-Read-Next` L454 - and ZERO `GL-Posting-*` verbs; a
grep for `GL-Posting` over `general/gl072.cbl` returns nothing. `gl070` is read-only
throughout. `GLPOSTING-REC` is nevertheless listed, because `gl070` Phase 2 CONSUMES it
and its survival unchanged is exactly what proves Phase 2 never ran.

ALSO RELEVANT, AND PRESERVED RATHER THAN HARMONISED (R-4): GL-Batch `Open-Output` DOES
NOT TRUNCATE `GLBATCH-REC`, because the two lines that would arm the delete-all are
COMMENTED OUT [common/acas007.cbl:L305-L312]:

     305|      if       fn-Open and
     306|               fn-output
     307|          and  not FS-Cobol-Files-Used  *> RDB processing
     308|  *>             set fn-delete-all to true
     309|  *>             move zero to access-type
     310|               perform ba-Process-RDBMS
     311|               go to AA-Main-Exit
     312|      end-if.

whereas the equivalent line IS ACTIVE in the IRS transfer-file handler
[common/acas008.cbl:L313-L318], where `set fn-delete-all to true` at L316 deletes every
row of `PSIRSPOST-REC`. The divergence between the two handlers is the specification.

-------------------------------------------------------------------------------
10. THE FIVE REJECTION CLASSES - THIS FILE OWNS CLASS 2
-------------------------------------------------------------------------------

Plan section 0.8.1: "a single generic rejection path would fail this directive." They
differ precisely in their DATABASE EFFECT, and they are not collapsed:

  1. CLEAN REJECTION, NO DATABASE EFFECT - `gl072` skips a posting whose batch number is
     non-numeric [general/gl072.cbl:L291-L292] and a record whose handler returned a
     specific error [general/gl072.cbl:L306-L307], both silent and traceless, with no
     message, counter or trace. ANOMALY A-13. Owned by
     `tests/scenarios/test_mixed_accepted_rejected_batch.py`.
  2. RUN-ABORTING REJECTION - THIS FILE'S SUBJECT. The control-total mismatch leaves the
     batch open, which propagates through the four-link chain of section 4 and prevents
     the remaining phases from running at all. The database effect is THE ABSENCE of
     everything the later phases would have written.
  3. PARTIAL DATABASE EFFECT - the IRS half-posted double entry
     [irs/irs030.cbl:L1635-L1652] (A-4) and the lost update on the two VAT control
     accounts, snapshots taken at [irs/irs030.cbl:L1602] and L1612 and rewritten at
     L1704-L1708 (A-5). Owned by `tests/scenarios/test_clean_batch_post_irs.py`.
  4. FILE-ABANDONING REJECTION - a posting-record write failure jumps straight to
     end-of-job [irs/irs030.cbl:L1673-L1678] and the partial state is COMMITTED, not
     rolled back.
  5. PERMANENTLY FAILING FACADE VERB - the transfer-file handler refuses read-indexed,
     rewrite, start and delete UNCONDITIONALLY at entry, each answered `WE-Error 988`
     and `fs-reply 99` [common/acas008.cbl:L299-L307] (A-6), yet the facade still
     publishes the rewrite verb.

THE CLASS-1 VERSUS CLASS-2 BOUNDARY IS ONE SEEDED FIELD, and getting it backwards
silently converts each test into the other: `Batch-Status = 0` gives class 2 and this
file; `Batch-Status = 1` with the right posting mix gives class 1 and
`test_mixed_accepted_rejected_batch.py`. That is why the seeded status is asserted here
as an AGREEMENT between the two sides and the seed, and why nothing in this file
recomputes it.

-------------------------------------------------------------------------------
11. TRACEABILITY AND ARBITRATION (R-5, R-6)
-------------------------------------------------------------------------------

ANOMALIES TOUCHED BY THIS ROUTE, by register number in `docs/migration/anomaly-log.md`:
A-12 (the character-width drift that motivates normalisation job 1, REPRODUCED), A-13
(`gl072`'s two silent skips, cross-referenced - they belong to class 1 and to another
scenario), A-14 (the nominal account located by SEQUENTIAL read,
`general/gl072.cbl:L408` with its key move at L405 and its guard at L407, so correctness
depends entirely on `gl071`'s sort order - cross-referenced here because THIS route
proves the read never happens at all), and A-15 (the batch record's declared length
contradicting the sum of its fields, [copybooks/wsbatch.cob:L7-L9] - "98 bytes ... (no,
dont understand as I count 96) ... but function length (Batch-record) says 98?").

AMBIGUITIES ARBITRATED BY THE COMPILED ORACLE, referenced BY IDENTIFIER ONLY in
`docs/migration/ambiguity-resolutions.md` - textually, with no import, no path check and
no skip if absent:

  * `Q-4` - the batch-record declared-length contradiction behind A-15. Whether the
    declared length or the field sum governs the record actually read affects the
    alignment of the trailing fields, and only execution shows which. It matters
    directly to this scenario, because `Description`, `posting-data` and `Batch-Start`
    are the trailing fields of the very record whose non-change is the evidence.
  * The `batch-status`-unassigned path at [general/gl051.cbl:L1099-L1100], whose
    observable effect is measured rather than reasoned about.
  * The deliberate omission of `gl_end_of_cycle`: `gl080` is driven by NO scenario in
    this harness, which is why `system.period` is inert on every route.

Per-scenario evidence is recorded in `docs/migration/scenario-diff-evidence.md`.
`pytest-cov` is TRACEABILITY EVIDENCE AND NEVER A GATE - `pyproject.toml` sets no
`fail_under` and `addopts` carries no `--cov-fail-under`.

THE GENERAL LEDGER CAVEAT APPLIES HERE WITH MAXIMUM FORCE. The maintainer records that
he has not had time to work with General since it was migrated to the current compiler
[README.TXT:L50-L53], while testing is complete for the other ledgers. The General
Ledger is therefore the least-exercised ledger in the system and this scenario
deliberately drives a REJECTION path through it. Expected values come ONLY from the
oracle - never from the documentation and never from reasoning about intent. If the
compiled cycle behaves surprisingly, THE SURPRISE IS THE SPECIFICATION.

NO PERFORMANCE ASSERTION AND NO TIMING MEASUREMENT appears anywhere below (Plan section
0.8.4), and no floating-point value, tolerance, epsilon or approximate-equality helper
is used or imported (R-2).
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.scenario

SCENARIO = "control_total_mismatch"


# ---------------------------------------------------------------------------
#  THE EVIDENCE FIXTURES
#
#  MODULE-SCOPED, AND FOR A CORRECTNESS REASON RATHER THAN A SPEED ONE. Every state
#  assertion below - the parity verdict, the absence of the gl072 mutations, the
#  batch's unstamped columns, the dumps' well-formedness and the exit contract - must
#  describe ONE run of the eight-stage protocol. Re-running the protocol per test would
#  let two tests reason about two different runs and then report agreement between
#  them, which is exactly the kind of quiet incoherence this migration exists to rule
#  out. One run, one body of evidence, many questions asked of it.
#
#  They import from `tests/conftest.py` INSIDE the fixture body rather than requesting
#  the function-scoped `protocol` fixture, because a module-scoped fixture may not
#  depend on a function-scoped one. The import is function-local so that module scope
#  stays exactly as specified: the docstring, `__future__`, `pytest`, `pytestmark` and
#  `SCENARIO`. NOTHING here imports `harness` or reaches a harness path directly (R-1);
#  the harness modules are only ever the `harness` fixture's three explicitly-loaded
#  modules.
#
#  STRICTLY SEQUENTIAL (R-3). One database, one stage at a time, in the protocol's own
#  order. No thread, no asyncio, no connection pool, no parallel runner and no
#  execution-reordering plugin - `pyproject.toml` names every one it excludes.
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def parity_run():
    """All eight protocol stages for `control_total_mismatch`, run once.

    Skips - never fails - when the harness Compose stack is unusable, so that
    collection and the infrastructure-free tiers keep working on a bare host. The skip
    reason names every missing precondition.

    THE COBOL RUNNER IS EXPECTED TO EXIT 5 HERE, and that does not abort the protocol:
    conftest's composition applies `raise_for_status()` to seed, reset, both dumps and
    both normalisations and DELIBERATELY NOT to the two run stages, because "the
    database effect is therefore the absence of everything the later phases would have
    written" (Plan section 0.6.5) and a helper that short-circuited the dump would
    destroy the only evidence this scenario has.

    A stage whose failure destroys the evidence - or a stage-8 exit of 2, meaning the
    comparison could not be performed - raises `HarnessFaultError` from inside this
    fixture, which pytest reports as a genuine ERROR rather than a failure. That is the
    distinction the whole file rests on: "could not compare" must never read as "no
    differences".

    Returns:
        The `ParityRun`: every stage in order, both run results, the stage-8 verdict
        and the paths of every artifact.
    """
    from conftest import requires_stack, run_scenario_parity

    requires_stack()
    return run_scenario_parity(SCENARIO)


@pytest.fixture(scope="module")
def seed_baseline(parity_run):
    """The PRISTINE SEEDED STATE of this scenario's three tables, for the absence proof.

    Asserting that the two sides AGREE is necessary but not sufficient here: two sides
    that had both posted the batch would agree perfectly and the diff would still be
    empty. What makes the absence provable is a THIRD tree - the seed itself - so that
    `cobol == python` and `cobol == seed` and `python == seed` together say that nothing
    moved on either side.

    It is captured AFTER `parity_run` has finished, and depends on it for exactly that
    ordering: re-seeding replaces the migrated cycle's post-run state in the database,
    which is harmless only because every artifact of the parity run is already on disk.
    Stage 5's own script is reused verbatim - `harness/reset_db.sh` re-applies the
    frozen `mysql/ACASDB.sql` and re-seeds from the same scenario-owned fixture, so no
    DDL of this file's own is ever emitted (R-3) and the baseline is provably the same
    state both cycles started from.

    The capture is written under its own output root so that the canonical
    `<scenario>/cobol[.normalized]` and `<scenario>/python[.normalized]` trees the
    verdict was taken from are never overwritten. It occupies the `cobol` side of that
    private root only because a dump has exactly two side names; nothing about it came
    from the compiled oracle, and the failure messages below say so wherever the
    differ's two fixed labels would otherwise mislead.

    Args:
        parity_run: The completed protocol run, which this fixture must follow.

    Returns:
        The `ScenarioPaths` of the baseline capture; its `cobol_normalized` tree is the
        one to compare against.

    Raises:
        HarnessFaultError: The reset, the dump or the normalisation failed, so there is
            no baseline and therefore no absence proof.
    """
    from conftest import SIDE_COBOL, dump, normalize, reset, scenario_paths

    baseline_root = parity_run.paths.out_root / "seed-baseline"
    reset(SCENARIO).raise_for_status()
    dump(SCENARIO, SIDE_COBOL, out_dir=baseline_root).raise_for_status()
    normalize(SCENARIO, SIDE_COBOL, out_dir=baseline_root).raise_for_status()
    return scenario_paths(SCENARIO, out_root=baseline_root)


# ---------------------------------------------------------------------------
#  THE SCENARIO-DEFINITION TESTS.  NO STACK REQUIRED.
#
#  A scenario definition is a file on disk, so every assertion below runs on a bare
#  host with no Docker, no MariaDB and no GnuCOBOL. That is deliberate: these are the
#  preconditions that decide whether the protocol will PROVE anything, and a
#  precondition that could only be checked once the infrastructure was up would be
#  checked far too late.
#
#  The definition is read with conftest's loader, which uses `yaml.safe_load` and never
#  `yaml.load`, checks only the keys the helpers consume and interprets nothing -
#  judging a scenario's declared contents would be exactly the added validation R-3
#  forbids. This file never opens the YAML itself and never imports a YAML library.
# ---------------------------------------------------------------------------


def test_scenario_definition_preconditions(
    scenario_loader, in_scope_table_names, pinned_clock
) -> None:
    """Every precondition that decides whether an empty diff will MEAN anything.

    The definition's own key names are asserted as the file spells them. Note that the
    terminate-code expectation is NOT a nested `expect.term_code`: the runners read
    top-level keys only, so the contract is the flat pair `operations` and
    `expected_status`, matched POSITIONALLY. That pairing is asserted here and again, in
    isolation, in `test_expected_term_code_is_five`.

    Several values are published under both a grouped and a flat key because the COBOL
    runner reads this file with a plain top-level-only reader while the dumper uses a
    full YAML parser. THE PAIRS MUST HOLD THE SAME VALUE, and drift between them is
    asserted rather than assumed.

    Args:
        scenario_loader: Conftest's `yaml.safe_load` reader.
        in_scope_table_names: The 22 in-scope names, read from the harness (R-4).
        pinned_clock: The project-wide pinned run date, both observables.
    """
    from conftest import (
        IRS_INSTEAD_GL_ONLY,
        OPERATIONS,
        PINNED_RUN_DATE_BINARY,
        PINNED_RUN_DATE_TEXT,
        SCENARIO_KEY_AFFECTED_TABLES,
        scenario_affected_tables,
    )

    definition = scenario_loader(SCENARIO)

    # The scenario names itself, and the name is load-bearing rather than decorative:
    # the COBOL runner falls back to this file's basename when no name is present, and
    # it is the name that arms the General-Ledger-only refusal in BOTH runners.
    assert definition["name"] == SCENARIO, (
        f"the definition names itself {definition['name']!r} but this test drives "
        f"{SCENARIO!r}. The runners derive the General-Ledger-only refusal from the "
        f"name, so a mismatch disarms it."
    )

    # 3.1  The subsystem, from the top-level key AND from the operation map, because
    # a non-General subsystem cannot express this scenario at all - see section 1 of
    # the module docstring, [sales/sl060.cbl:L1118-L1121] and
    # [purchase/pl060.cbl:L973-L976].
    operation = definition["operation"]
    assert definition["subsystem"] == "general"
    assert OPERATIONS[operation][0] == "general", (
        f"operation {operation!r} belongs to subsystem "
        f"{OPERATIONS[operation][0]!r}, not to `general`."
    )
    assert operation == "gl_post_cycle", (
        f"this scenario drives the General Ledger posting cycle - gl070, then the "
        f"terminate-code gate, then gl071, then gl072 "
        f"[general/general.cbl:L805-L815] - and not {operation!r}."
    )

    # 3.2  The one non-zero terminal disposition in the whole scenario set, declared as
    # the flat positional pair the runners read.
    assert definition["operations"] == [operation], (
        f"`operations` is a FLAT SEQUENCE OF OPERATION NAMES and must agree with the "
        f"singular `operation` key; got {definition['operations']!r} against "
        f"{operation!r}."
    )
    assert definition["expected_status"] == [5], (
        f"`expected_status` matches `operations` positionally and must declare the "
        f"terminate code gl070 raises for an open batch "
        f"[general/gl070.cbl:L289]; got {definition['expected_status']!r}."
    )
    assert len(definition["operations"]) == len(definition["expected_status"]), (
        "`operations` and `expected_status` are matched by POSITION, so they must be "
        "the same length."
    )

    # 3.3  THE FALSE-PASS TRAP, and it is worse here than anywhere else in the suite.
    # [copybooks/wssystem.cob:L112-L114] declares `File-System-Used pic 9` with
    # `88 FS-Cobol-Files-Used value zero` and `88 FS-MySql-Used value 1`, and every
    # handler routes to the MySQL bridge only when the value is non-zero -
    # [common/acas007.cbl:L316-L320] is how the General Ledger batch handler decides:
    #     316       if       not FS-Cobol-Files-Used
    #     317                move RDBMS-Flat-Statuses to FA-RDBMS-Flat-Statuses
    #     318                perform  ba-Process-RDBMS
    #     319                go to AA-Main-Exit
    #     320       end-if.
    # Seed a zero and MySQL is never touched, both dumps come back empty and the differ
    # exits 0 having compared nothing against nothing. On EVERY OTHER ROUTE that shows
    # up as a suspiciously empty result; HERE unchanged tables are what success looks
    # like, so the two are indistinguishable in the dump. The seed fingerprint is the
    # second line of defence - a disagreement between `cobol.seed-fingerprint` and
    # `python.seed-fingerprint` is a HARNESS FAULT and not a behavioural difference
    # [harness/run_python_scenario.sh:L3176, L3206].
    system = definition["system"]
    assert system["file_system_used"] == 1, (
        f"`system.file_system_used` must be 1, so that `88 FS-MySql-Used` is true "
        f"[copybooks/wssystem.cob:L114] and every handler routes to the bridge "
        f"[common/acas007.cbl:L316-L320]; got "
        f"{system['file_system_used']!r}. With 0 the handlers never touch MySQL, both "
        f"dumps come back empty and the comparison passes having proved NOTHING - and "
        f"on this route that false pass is indistinguishable from the correct result, "
        f"because an unchanged table is what success looks like here."
    )

    # 3.4  The three-state fan-out switch, [copybooks/wssystem.cob:L179-L181]:
    #     179         05  IRS-Instead     pic x.
    #     180             88  IRS-Used                   value "Y".
    #     181             88  IRS-Both-Used              value "B".   *> 26/11/16
    # THE THIRD STATE HAS NO CONDITION NAME AT ALL - for a space both predicates are
    # simply False, which is General Ledger only. Plan section 0.6.4: "leaving it at a
    # default would make the affected-table list ambiguous", so it is pinned explicitly
    # even though its value is blank. The column stores a space and normalisation job 1
    # trims it identically on both sides, which is correct precisely because it is
    # applied to both.
    assert definition["irs_instead"] == IRS_INSTEAD_GL_ONLY
    assert system["irs_instead"] == IRS_INSTEAD_GL_ONLY, (
        f"`system.irs_instead` and the flat `irs_instead` are an adjacent pair and "
        f"must hold the same value; got {system['irs_instead']!r} against "
        f"{definition['irs_instead']!r}."
    )

    # 3.5  THE HEADLINE TRAP. `Cyclea` is `binary-char` [copybooks/wssystem.cob:L62],
    # redefined as `Scycle` at L63, and the menu diverts a zero cycle into interactive
    # setup. The seeded batch's `Bcycle` [copybooks/wsbatch.cob:L34] MUST equal it, or
    # Phase 1's cycle filter [general/gl070.cbl:L312-L313] skips the batch before the
    # open-batch detector at L314-L315 is reached, `a` stays zero, L287 is false, the
    # run ends with `ws-term-code = 0` AND THE DIFF IS STILL EMPTY - a scenario that
    # passes while proving nothing. The batch's own `Bcycle` lives in the seed fixture
    # and not in this file, so what is asserted here is the pin; the terminate code
    # asserted in `test_expected_term_code_is_five` is what catches the mismatch.
    assert system["cyclea"] != 0, (
        "`system.cyclea` must be non-zero: the menu traps a zero cycle and diverts "
        "into interactive setup [general/general.cbl:L462-L463], and the seeded "
        "batch's Bcycle [copybooks/wsbatch.cob:L34] must equal it or Phase 1's cycle "
        "filter [general/gl070.cbl:L312-L313] skips the batch and the abort never "
        "fires."
    )
    # `period` is the cycles-per-quarter divisor used only by gl080
    # [copybooks/wssystem.cob:L64], and NO scenario in this harness drives
    # `gl_end_of_cycle`, so it is inert on this route. It is asserted PRESENT, because
    # all eight definitions share one system block, and never interpreted.
    assert "period" in system

    # 3.6  The pinned clock, both observables. `to_day` is `pic x(10)` in DD/MM/CCYY
    # form and is a linkage parameter; `Run-Date` is `binary-long`
    # [copybooks/wssystem.cob:L67] and IS a real `SYSTEM-REC` column, hence visible in a
    # dump. It is ironically load-bearing here BY ITS ABSENCE: because gl072 never runs,
    # `move run-date to posted` [general/gl072.cbl:L376] never fires and
    # `GLBATCH-REC.POSTED` must remain exactly as seeded. Pinning the clock is what
    # makes a spurious stamp unambiguous rather than noise.
    assert definition["clock"]["to_day"] == pinned_clock.to_day
    assert definition["clock"]["run_date"] == pinned_clock.run_date
    assert definition["run_date_text"] == PINNED_RUN_DATE_TEXT
    assert definition["run_date_binary"] == PINNED_RUN_DATE_BINARY
    assert definition["run_date_text"] == definition["clock"]["to_day"], (
        "`run_date_text` and `clock.to_day` are an adjacent pair written side by side "
        "so that drift is visible at a glance."
    )
    assert definition["run_date_binary"] == definition["clock"]["run_date"]
    # Date form 1 selects UK day-month-year [copybooks/wssystem.cob:L128-L129], the
    # form the pinned date above is written in.
    assert definition["date_form"] == 1
    assert system["date_form"] == definition["date_form"]

    # 3.7  Exactly three affected tables, alphabetical, every one in scope. The list is
    # read through conftest, which delegates to the harness so the inventory and every
    # primary key have exactly one definition in this repository (R-4). Exactly one
    # spelling of the key may be present, and conftest enforces that.
    present = [key for key in SCENARIO_KEY_AFFECTED_TABLES if key in definition]
    assert len(present) == 1, (
        f"exactly one of {SCENARIO_KEY_AFFECTED_TABLES} may be declared - the list "
        f"that BOUNDS the comparison; found {present!r}."
    )
    tables = scenario_affected_tables(SCENARIO)
    assert tables == ("GLBATCH-REC", "GLLEDGER-REC", "GLPOSTING-REC"), (
        f"this scenario compares exactly three tables, each present to prove an "
        f"absence: GLBATCH-REC that the batch was not stamped "
        f"[general/gl072.cbl:L375-L377], GLLEDGER-REC that no balance moved "
        f"[general/gl072.cbl:L331, L382], GLPOSTING-REC that nothing was consumed. "
        f"Got {tables!r}."
    )
    assert set(tables) <= set(in_scope_table_names), (
        f"every affected table must be one of the 22 in-scope names; "
        f"{sorted(set(tables) - set(in_scope_table_names))!r} is not."
    )

    # 3.8  Exactly four seed files, and the frozen loader script's own per-file contract
    # decides which loader each one reaches: system.dat to the four-loader block
    # systemLD, sys4LD, finalLD, dfltLD [common/masterLD.sh:L51-L87]; batch.dat to
    # glbatchLD [common/masterLD.sh:L94]; ledger.dat to nominalLD
    # [common/masterLD.sh:L103]; posting.dat to glpostingLD [common/masterLD.sh:L109].
    # system.dat is effectively mandatory: without the system record the menu calls its
    # interactive setup program and the runner blocks on a terminal.
    assert definition["seed_files"] == [
        "system.dat",
        "ledger.dat",
        "batch.dat",
        "posting.dat",
    ], (
        f"the seed is exactly these four flat files, each a name the frozen loader "
        f"script recognises [common/masterLD.sh:L93-L116]; got "
        f"{definition['seed_files']!r}. Naming any other file would drag a table into "
        f"the fixture that the comparison must not see."
    )
    assert definition["seed"]["files"] == definition["seed_files"], (
        "`seed.files` and `seed_files` are an adjacent pair and must agree."
    )
    assert definition["seed_dir"] == definition["seed"]["data_dir"], (
        "`seed.data_dir` and `seed_dir` are an adjacent pair and must agree. Both are "
        "a RELATIVE directory name, never an absolute path."
    )

    # 3.9  The scenario promotes NO interactive answer, which is why no answer key is
    # declared. `gl_post_cycle` has no prompt whose reply gates a database write -
    # contrast the IRS route, whose clear-the-transfer-file reply performs an
    # open-output that deletes every row [common/acas008.cbl:L313-L318].
    assert "answers" not in definition


def test_scenario_is_general_ledger_only(scenario_loader) -> None:
    """The subsystem pin, asserted alone, because no other value is expressible.

    Sales and Purchase batches balance BY CONSTRUCTION: the entered and the actual
    control totals are incremented from the same source in adjacent statements, at
    [sales/sl060.cbl:L1118-L1121] and identically at [purchase/pl060.cbl:L973-L976]. So
    an unbalanced Sales or Purchase batch cannot be constructed at all, however it is
    seeded, and both harness runners refuse this scenario for a non-General subsystem
    with harness-fault status. This test exists as its own case so that the refusal can
    never be reached by accident, and so that its failure message carries the proof.

    Args:
        scenario_loader: Conftest's definition reader.
    """
    from conftest import OPERATIONS

    definition = scenario_loader(SCENARIO)
    subsystem = definition["subsystem"]
    operation_subsystem = OPERATIONS[definition["operation"]][0]

    assert subsystem == "general" and operation_subsystem == "general", (
        f"`{SCENARIO}` IS GENERAL-LEDGER-SPECIFIC and there is no Sales or Purchase "
        f"variant to write. Got subsystem {subsystem!r} and operation subsystem "
        f"{operation_subsystem!r}.\n"
        f"  Plan section 0.6.4: Sales and Purchase batches balance by construction, so "
        f"\"there is no meaningful way to construct an unbalanced sales batch\".\n"
        f"  The proof is four adjacent statements. [sales/sl060.cbl:L1118-L1121]:\n"
        f"      1118      add      Post-Amount  to  input-gross.\n"
        f"      1119      add      Post-Amount  to  actual-gross.\n"
        f"      1120      add      vat-amount   to  input-vat.\n"
        f"      1121      add      vat-amount   to  actual-vat.\n"
        f"  and [purchase/pl060.cbl:L973-L976]:\n"
        f"       973      add      post-amount  to  input-gross.\n"
        f"       974      add      post-amount  to  actual-gross.\n"
        f"       975      add      vat-amount   to  input-vat.\n"
        f"       976      add      vat-amount   to  actual-vat.\n"
        f"  input-gross and actual-gross both receive post-amount; input-vat and "
        f"actual-vat both receive vat-amount. They cannot disagree, so the "
        f"control-total gate can never reject such a batch.\n"
        f"  BOTH RUNNERS REJECT THIS SCENARIO FOR A NON-GENERAL SUBSYSTEM WITH "
        f"HARNESS-FAULT STATUS. Do not retarget it; write nothing in its place."
    )


def test_expected_term_code_is_five(scenario_loader) -> None:
    """Terminate code 5, asserted alone: the only non-zero expectation in the whole set.

    Raised at [general/gl070.cbl:L289] - `move 5 to ws-term-code` - when Phase 1 found a
    batch left open, and consumed by the hard gate at [general/general.cbl:L810-L811] -
    `if ws-term-code = 5 / go to display-menu.` `acas_posting/cli/args.py`'s
    `exit_status_for(term_code)` returns the term code itself for any non-zero value, so
    the abort surfaces as PROCESS EXIT 5 on both sides.

    A RUN THAT EXITS 0 HERE IS A FAILURE OF THE SCENARIO'S PREMISE AND NOT A SUCCESS.
    The two likely causes are both silent: the seeded batch's `Bcycle`
    [copybooks/wsbatch.cob:L34] not equalling `system.cyclea`
    [copybooks/wssystem.cob:L62], so Phase 1's cycle filter
    [general/gl070.cbl:L312-L313] skips it before the detector at L314-L315; or the
    seeded batch not being `Status-Open` [copybooks/wsbatch.cob:L25-L26] at all. In
    either case all three phases run, nothing aborts, and the diff can still come back
    empty - which is why this expectation is pinned in the definition and asserted here
    rather than merely observed at run time.

    Args:
        scenario_loader: Conftest's definition reader.
    """
    from conftest import TERM_CODES

    definition = scenario_loader(SCENARIO)
    operation = definition["operation"]

    assert definition["expected_status"] == [5], (
        f"`{SCENARIO}` must expect terminate code 5, the ONLY non-zero terminal "
        f"disposition in the entire scenario set. Got "
        f"{definition['expected_status']!r}.\n"
        f"  Raise site:  [general/gl070.cbl:L289]  move 5 to ws-term-code\n"
        f"  Abort gate:  [general/general.cbl:L810-L811]  if ws-term-code = 5 / "
        f"go to display-menu.\n"
        f"  An exit of 0 on this route means the abort never fired and the scenario "
        f"tested nothing."
    )
    # Cross-checked against conftest's admissible-term-code map, which is transcribed
    # from the three raise sites and is the single definition of them: gl070 to 5,
    # sl055 to 8 and pl055 to 8, the last two unreachable because both sit inside
    # `if FS-Cobol-Files-Used` and every definition pins `file_system_used: 1`.
    assert TERM_CODES[operation] == (5,), (
        f"5 must be the one admissible non-zero term code for {operation!r}; conftest "
        f"records {TERM_CODES[operation]!r}."
    )
    assert definition["expected_status"][0] in TERM_CODES[operation]


def test_affected_tables_are_in_scope_and_alphabetical(
    scenario_loader, in_scope_table_names, harness
) -> None:
    """Three tables, alphabetical, in scope, each with its single-column primary key.

    THE ORDER IS LOAD-BEARING and not cosmetic: the seed fingerprint is written in the
    declared order, and a disagreement between the two sides' fingerprints is a HARNESS
    FAULT rather than a behavioural difference
    [harness/run_python_scenario.sh:L3176, L3206]. The report's table order follows the
    same list.

    The 22-name inventory and every primary key are READ FROM THE HARNESS and never
    restated here, because they have exactly one definition in this repository (R-4).
    The eleven out-of-scope tables are never dumped.

    Args:
        scenario_loader: Conftest's definition reader.
        in_scope_table_names: The 22 in-scope names, ascending.
        harness: The three explicitly-loaded harness modules.
    """
    from conftest import scenario_affected_tables

    definition = scenario_loader(SCENARIO)
    tables = scenario_affected_tables(SCENARIO)

    assert tuple(definition["affected_tables"]) == tables, (
        "the declared list and the list conftest resolves must be the same, in the "
        "same order."
    )
    assert tables == tuple(sorted(tables)), (
        f"the affected-table list must be alphabetical, because the seed fingerprint "
        f"is written in the declared order and a disagreement between the two sides' "
        f"fingerprints is a harness fault; got {tables!r}."
    )
    assert len(tables) == len(set(tables)) == 3

    for table in tables:
        assert table in in_scope_table_names, (
            f"{table!r} is not one of the 22 in-scope tables. The eleven out-of-scope "
            f"tables are never dumped, and bounding is done by this list and by "
            f"nothing else - there is no ignore-list anywhere in the diff path."
        )
        # Every in-scope table has a SINGLE-COLUMN primary key and no secondary index,
        # which is what makes `SELECT * FROM <table> ORDER BY <primary key>` a total,
        # stable order with no tie-breaking (Plan section 0.6.6).
        specification = harness.dump_tables.table_spec(table)
        assert specification.primary_key
        assert specification.column_count > 0


def test_vat_is_added_before_the_comparison_is_documented(repo_root) -> None:
    """The gate's OPERATION ORDER, recorded for the reader and locked against drift.

    DOCUMENTATION, NOT EXECUTION. This test does not drive `gl051` and must not: the
    program has no CLI entry point on either side, only `batch-print` section 999 and
    its `end-batch` paragraph [general/gl051.cbl:L1096-L1134] are in scope, and
    `acas_posting/programs/gl051_batch_control_check.py` is a library function exercised
    by `tests/arithmetic/test_control_total_comparison.py`. THIS SCENARIO REACHES THE
    GATE'S CONSEQUENCE AND NEVER THE GATE - the batch status is SEEDED, not computed.

    What it does assert is that the frozen source still says what the module docstring
    quotes it as saying. The locators are cited at a dozen places in this file and in
    the anomaly register, so a silent drift would quietly invalidate all of them; and
    because the COBOL is FROZEN (Plan section 0.8.1 - any diff under `general/` is a
    defect in the migration however harmless it looks), a failure here means either the
    citation is wrong or the frozen tree has been edited. The file is read and never
    written.

    THE ORDER, and why reversing it would be catastrophic:

        1109      add      actual-vat   to  actual-gross.
        ...
        1117      if       input-gross = actual-gross
        1118        and    input-vat   = actual-vat

    VAT is folded into the actual gross BEFORE the equality test, because the entered
    figure is VAT-inclusive. Reversing the two "would reject every batch that carries
    VAT" (Plan section 0.6.4).

    THE TWO EARLIER EXITS, both part of the specification and neither tidied (R-4):

        1099      if       z = 99
        1100               go to  main-exit.        <- batch-status left UNASSIGNED
        1101      if       not truet
        1102               move  0  to  batch-status
        1103               go to  main-exit.        <- rejects BEFORE L1109 runs

    The first is an open question arbitrated by the compiled oracle and recorded in
    `docs/migration/ambiguity-resolutions.md`; the field is not initialised here or
    anywhere else. The flag tested at L1101 is spelled `truet`, and the data item behind
    it is spelled `trutht` [general/gl051.cbl:L175-L177] - two spellings one transposed
    letter apart, both of them the specification and neither corrected (R-4).

    Args:
        repo_root: The repository root, which holds the frozen COBOL beside the Python.
    """
    source = (repo_root / "general" / "gl051.cbl").read_text(encoding="utf-8")
    lines = source.splitlines()

    def at(number: int) -> str:
        """One frozen line, with runs of whitespace collapsed.

        The frozen source aligns its operands by column, so inner spacing is
        presentation and is not compared; nothing else about the text is altered, and
        no value of any kind is parsed out of it.

        Args:
            number: The 1-based line number, as every locator in this file cites it.

        Returns:
            The line's tokens, single-spaced and stripped.
        """
        return " ".join(lines[number - 1].split())

    # The paragraph, and the two accumulators that feed it.
    assert at(1096) == "end-batch."
    assert at(1063) == "add post-amount to actual-gross."
    assert at(1064) == "add vat-amount to actual-vat."

    # EARLIER EXIT #1 - returns with `batch-status` never assigned at all.
    assert at(1099) == "if z = 99"
    assert at(1100) == "go to main-exit."

    # EARLIER EXIT #2 - rejects BEFORE the VAT mutation, so on this path L1109 never
    # runs. THE SPELLING AT L1101 IS `truet`, and it is a CONDITION NAME rather than the
    # data item - see the declaration asserted immediately below.
    assert at(1101) == "if not truet", (
        f"the flag tested at [general/gl051.cbl:L1101] is spelled `truet` and is NOT "
        f"corrected (R-4); the frozen line reads {at(1101)!r}."
    )
    assert at(1102) == "move 0 to batch-status"
    assert at(1103) == "go to main-exit."

    # BOTH SPELLINGS EXIST AND MEAN DIFFERENT THINGS - measured in this checkout, and
    # recorded because the two differ by a single transposed letter and a well-meaning
    # reader would "fix" one into the other. [general/gl051.cbl:L175-L177]:
    #
    #      175      03  trutht              pic 9.
    #      176          88  falset                           value zero.
    #      177          88  truet                            value 1.
    #
    # `trutht` is the DATA ITEM; `falset` and `truet` are its two condition names. So
    # `if not truet` at L1101 means `if trutht not = 1`, and neither spelling is a typo
    # to be repaired (R-4). Note also that L175 carries NO `value` clause, so the item
    # is whatever the program last moved into it - and the ONLY paragraph that sets it
    # TRUE is `move 1 to trutht.` in the OUT-OF-SCOPE `gl050d` section
    # [general/gl051.cbl:L967]. That reinforces the point of section 3 of the module
    # docstring: this scenario reaches the gate's CONSEQUENCE and never the gate, so
    # the state of this flag is not something the route can influence.
    assert at(175) == "03 trutht pic 9."
    assert at(176) == "88 falset value zero."
    assert at(177) == "88 truet value 1."
    assert at(967) == "move 1 to trutht."

    # THE MUTATION, then THE TEST, in that order.
    assert at(1109) == "add actual-vat to actual-gross.", (
        f"[general/gl051.cbl:L1109] must fold actual VAT into the actual gross; the "
        f"frozen line reads {at(1109)!r}."
    )
    assert at(1117) == "if input-gross = actual-gross"
    assert at(1118) == "and input-vat = actual-vat"
    assert at(1119) == "move 1 to batch-status"
    assert at(1121) == "move 0 to batch-status."
    assert 1109 < 1117, (
        "the VAT addition at [general/gl051.cbl:L1109] precedes the equality test at "
        "[general/gl051.cbl:L1117-L1118]. Reversing the two would reject every batch "
        "that carries VAT."
    )

    # The verdict banner, whose L1121 branch is the state this scenario seeds.
    assert at(1126) == "if batch-status = 1"
    assert at(1134) == "go to main-exit."

    # THERE IS NO actual-DR AND NO actual-CR FIELD. The batch record carries exactly
    # four money fields [copybooks/wsbatch.cob:L40-L44], and no DR/CR pair is invented.
    batch_copybook = (repo_root / "copybooks" / "wsbatch.cob").read_text(
        encoding="utf-8"
    )
    lowered = batch_copybook.lower()
    assert "actual-dr" not in lowered and "actual-cr" not in lowered, (
        "copybooks/wsbatch.cob declares exactly four money fields - Input-Gross, "
        "Input-Vat, Actual-Gross and Actual-Vat [copybooks/wsbatch.cob:L40-L44] - and "
        "no actual-DR or actual-CR field. Do not invent one."
    )
    # A-15 / ambiguity `Q-4`: the declared length contradicts the field sum, in the
    # maintainer's own words. Recorded, never resolved from here.
    assert "dont understand as I count 96" in batch_copybook, (
        "anomaly A-15 lives in the frozen comment at [copybooks/wsbatch.cob:L7-L9] and "
        "is arbitrated by the compiled oracle under ambiguity `Q-4`; it is neither "
        "resolved nor removed here."
    )


# ---------------------------------------------------------------------------
#  THE STATE-PARITY TESTS.  THESE NEED THE HARNESS COMPOSE STACK.
#
#  All of them read the ONE `parity_run`, so they describe one run of the eight stages
#  rather than several. On a host without the stack the fixture SKIPS with a reason that
#  names every missing precondition, and collection still succeeds.
#
#  NOTHING BELOW PREDICTS A FIGURE. Each assertion is an AGREEMENT - between the
#  compiled oracle and the migrated cycle, and between both of them and the seed - which
#  is what R-6 requires: the compiled run is the arbiter, so a test that named the
#  expected value would be substituting its own judgement for the specification's.
# ---------------------------------------------------------------------------


def test_control_total_mismatch_state_parity(parity_run, harness) -> None:
    """THE HEADLINE. An empty ordering-normalised diff across the three bounded tables.

    Plan section 0.8.5, acceptance criterion 1: seed identically, run the compiled
    cycle, dump the affected tables ordering-normalised, reset, run the Python cycle,
    dump again - "and the diff MUST BE EMPTY". Plan section 0.6.6 is what makes that
    verdict trustworthy: "a non-empty diff is always a real behavioral difference and
    never an artefact of the comparison."

    ON THIS ROUTE THE EMPTY DIFF CERTIFIES A THREE-PART CLAIM, and it is worth stating
    because it is unusual: that both sides raised terminate code 5; that both left the
    batch in `GLBATCH-REC` still open, with no cleared status and no posted date stamped
    into it; and that `GLLEDGER-REC` and `GLPOSTING-REC` are untouched on both sides. In
    other words THAT THE ABSENCE IS SYMMETRICAL. The companion tests below take each of
    those apart; this one asks the single question the protocol exists to answer.

    Args:
        parity_run: The completed eight-stage run.
        harness: The three harness modules, for the report renderer.
    """
    assert parity_run.tables == ("GLBATCH-REC", "GLLEDGER-REC", "GLPOSTING-REC"), (
        f"the comparison must be bounded by this scenario's own three-table list and "
        f"by nothing else; it ran over {parity_run.tables!r}."
    )
    assert parity_run.is_empty, (
        f"`{SCENARIO}` DIFFERS between the compiled COBOL oracle and the migrated "
        f"Python cycle: {parity_run.tree.total_differences} finding(s) across "
        f"{len(parity_run.tables)} bounded table(s).\n"
        f"  The expected state on this route is an ABSENCE - Plan section 0.6.5: \"the "
        f"database effect is therefore the absence of everything the later phases "
        f"would have written\" - so ANY finding means one side did something the "
        f"other did not. Check first whether one side ran gl071 and gl072 at all: "
        f"the hard gate is [general/general.cbl:L810-L811] and the raise is "
        f"[general/gl070.cbl:L289].\n"
        f"  Rendered report (also written to {parity_run.outcome.report}):\n"
        f"{harness.diff_states.render(parity_run.tree)}\n"
        f"  Stages:\n{parity_run.describe()}"
    )


def test_abort_is_reproduced_as_term_code_five(parity_run) -> None:
    """BOTH sides must reach the same terminal disposition, and it must be the abort.

    THE FOUR-LINK CHAIN, each link verified in this checkout:

        1. the seed        `Batch-Status = 0`, so `88 Status-Open` is true
                           [copybooks/wsbatch.cob:L25-L26]
        2. gl070 Phase 1   `if status-open / move 1 to a.`
                           [general/gl070.cbl:L314-L315]
        3. the mainline    `if a = 1 / perform gl060a / move 5 to ws-term-code /
                           go to main-exit.`  [general/gl070.cbl:L287-L290]
        4. the menu        `if ws-term-code = 5 / go to display-menu.`
                           [general/general.cbl:L810-L811]

    so `gl071` and `gl072` never run, and neither does Phase 2 - L290 leaves the
    mainline before L293. `acas_posting/cli/args.py` surfaces the term code itself as
    the process exit status, so the abort is observable as exit 5 on both sides.

    THE ABORT IS THE EXPECTED SUCCESS HERE. A reproduced abort that the scenario
    definition predicted is a PASS, so this test does not demand `DISPOSITION_SUCCESS` -
    it demands the BEHAVIOURAL disposition, which is what conftest returns for a status
    inside the operation's admissible term-code set, and it demands that both sides
    produced the same one.

    AN `argparse` EXIT OF 2 IS A HARNESS FAULT AND NEVER A DIFFERENCE: it means the
    runner built a bad command line, so nothing was measured. It is RAISED as
    `HarnessFaultError` rather than asserted, so that the category is unmistakable in
    the traceback; when such a fault occurs inside a protocol stage the `parity_run`
    fixture raises it and pytest reports a genuine ERROR.

    Args:
        parity_run: The completed eight-stage run.
    """
    from conftest import (
        ARGPARSE_USAGE_EXIT,
        DISPOSITION_BEHAVIOURAL,
        DISPOSITION_HARNESS_FAULT,
        HarnessFaultError,
        classify_run,
        scenario_definition,
    )

    definition = scenario_definition(SCENARIO)
    operation = definition["operation"]
    expected = definition["expected_status"][0]

    for label, result in (
        ("the compiled COBOL oracle", parity_run.cobol_run),
        ("the migrated Python cycle", parity_run.python_run),
    ):
        if result.returncode == ARGPARSE_USAGE_EXIT:
            raise HarnessFaultError(
                f"{label} exited {ARGPARSE_USAGE_EXIT}, which in this family means "
                f"THE RUNNER BUILT A BAD COMMAND LINE. That is a HARNESS FAULT and "
                f"never a behavioural difference: no in-scope program sets terminate "
                f"code 2 and no harness script uses exit 2, so nothing about the "
                f"posting cycle was measured.\n{result.describe()}"
            )
        # THE STATUS IS CHECKED BEFORE ITS CLASSIFICATION, deliberately: an exit of 0 is
        # the failure an operator is most likely to hit here, and the diagnosis it needs
        # is the premise explanation below rather than the name of a disposition.
        assert result.returncode == expected, (
            f"{label} exited {result.returncode}; the scenario definition predicts "
            f"{expected}.\n"
            f"  Raise site  [general/gl070.cbl:L289]  move 5 to ws-term-code\n"
            f"  Abort gate  [general/general.cbl:L810-L811]  if ws-term-code = 5 / "
            f"go to display-menu.\n"
            f"  AN EXIT OF 0 IS A FAILURE OF THE SCENARIO'S PREMISE, not a success: it "
            f"means the abort never fired, all three phases ran, and the empty diff "
            f"this suite also asserts would be proving nothing. The two silent causes "
            f"are the seeded batch's Bcycle [copybooks/wsbatch.cob:L34] not equalling "
            f"system.cyclea [copybooks/wssystem.cob:L62], so Phase 1's cycle filter "
            f"[general/gl070.cbl:L312-L313] skipped it, or the seeded batch not being "
            f"Status-Open [copybooks/wsbatch.cob:L25-L26].\n"
            f"{result.describe()}"
        )
        # And the classification, which is what keeps the three categories distinct: a
        # status inside the operation's admissible term-code set is a BEHAVIOURAL result
        # whose database effect must still be judged, while a harness fault would mean
        # the question was never asked at all.
        disposition = classify_run(result, operation=operation)
        assert disposition == DISPOSITION_BEHAVIOURAL, (
            f"{label} exited {result.returncode}, which conftest classifies as "
            f"{disposition!r}. On this route the expected disposition is "
            f"{DISPOSITION_BEHAVIOURAL!r} - the reproduced abort, which IS the "
            f"expected success here - and {DISPOSITION_HARNESS_FAULT!r} would mean "
            f"the question was never asked.\n{result.describe()}"
        )

    assert parity_run.cobol_run.returncode == parity_run.python_run.returncode, (
        f"the two sides reached DIFFERENT terminal dispositions - the oracle exited "
        f"{parity_run.cobol_run.returncode} and the migrated cycle "
        f"{parity_run.python_run.returncode}. Plan section 0.8.1 requires a rejected "
        f"transaction to reach the same disposition AND leave the same effect on the "
        f"database; this is the first half of that, and the state tests are the second."
    )


def test_gl071_and_gl072_never_ran(parity_run, seed_baseline, harness) -> None:
    """THE ABSENCE ASSERTION, AND THE HEART OF THIS FILE.

    Plan section 0.6.5, on a run-aborting rejection: "The database effect is therefore
    THE ABSENCE of everything the later phases would have written."

    EVERY MUTATION THAT MUST NOT HAVE HAPPENED, all in [general/gl072.cbl]:

         331      add      post-amount  to  ledger-balance.   <- MUST NOT HAPPEN
         372  end-batch.
         375      move     1  to  cleared-status.             <- MUST NOT HAPPEN
         376      move     run-date  to  posted.              <- MUST NOT HAPPEN
         377      perform  GL-Batch-Rewrite.  *> rewrite batch-record.  <- MUST NOT
         379  end-account.
         382      perform  GL-Nominal-Rewrite. *> rewrite ledger-record. <- MUST NOT

    WHY TWO-WAY AGREEMENT IS NOT ENOUGH, and this is the point of the whole test: two
    sides that had BOTH posted the batch would agree with each other perfectly and the
    stage-8 diff would still be empty. So the seed is captured as a THIRD tree and each
    side is compared against it. `cobol == seed` and `python == seed` together say that
    neither cycle wrote anything to any of the three tables - which is the claim, and it
    cannot be made from the pairwise verdict alone.

    Each side is compared against the baseline separately rather than relying on
    transitivity through the stage-8 verdict, so that a failure names WHICH side moved.
    The comparison is the harness's own exact one - `==` after a type check, rows
    aligned by primary-key value and never by position, no tolerance and no ignore-list
    - reached through conftest and never by importing `harness` (R-1). The differ has
    exactly two fixed labels, so in these two reports `cobol` means the side under test
    and `python` means the seed baseline; that relabelling is spelt out in the messages
    rather than left to trip someone up.

    Args:
        parity_run: The completed eight-stage run.
        seed_baseline: The pristine seeded state, captured after it.
        harness: The three harness modules, for the report renderer.
    """
    from conftest import diff_trees_directly

    tables = parity_run.tables

    for label, tree, locator in (
        (
            "the compiled COBOL oracle",
            parity_run.paths.cobol_normalized,
            "[general/general.cbl:L810-L811] should have returned to the menu before "
            "gl071 and gl072 were called at all",
        ),
        (
            "the migrated Python cycle",
            parity_run.paths.python_normalized,
            "`acas_posting/cli/gl_post_cycle.py` should have stopped at its "
            "terminate-code gate before dispatching gl071",
        ),
    ):
        against_seed = diff_trees_directly(tree, seed_baseline.cobol_normalized, tables)
        assert against_seed.is_empty, (
            f"{label} CHANGED the database, and on this route nothing may change: "
            f"{against_seed.total_differences} finding(s) against the pristine seed "
            f"across {len(tables)} table(s).\n"
            f"  Plan section 0.6.5: the expected effect is \"the absence of everything "
            f"the later phases would have written\". {locator}.\n"
            f"  The mutations that must not have happened: "
            f"[general/gl072.cbl:L331] add post-amount to ledger-balance; "
            f"[general/gl072.cbl:L375] move 1 to cleared-status; "
            f"[general/gl072.cbl:L376] move run-date to posted; "
            f"[general/gl072.cbl:L377] GL-Batch-Rewrite; "
            f"[general/gl072.cbl:L382] GL-Nominal-Rewrite.\n"
            f"  IN THE REPORT BELOW `cobol` IS {label} AND `python` IS THE SEED "
            f"BASELINE - the differ has exactly two labels and they are not "
            f"configurable.\n"
            f"{harness.diff_states.render(against_seed)}"
        )

    # And the pairwise verdict, restated here so this test stands on its own rather than
    # inheriting a conclusion from the headline case.
    assert parity_run.is_empty, (
        f"both sides matched the seed individually, yet the stage-8 verdict reports "
        f"{parity_run.tree.total_differences} finding(s). That is contradictory and "
        f"means the trees changed between the reads, so neither view can be trusted; "
        f"re-run the protocol from stage 1 (R-6).\n{parity_run.describe()}"
    )


def test_batch_remains_open_and_unstamped(
    parity_run, seed_baseline, harness
) -> None:
    """`GLBATCH-REC`'s status and posted columns agree on both sides and with the seed.

    FRAMED AS AGREEMENT, NEVER AS A VALUE. R-6 makes the compiled run the arbiter, so
    this test does not assert that `BATCH-STATUS` is 0 - it asserts that whatever the
    seed put there is still there on both sides. If the oracle were to do something
    surprising, the surprise would be the specification and a test that had hard-coded
    the "right" answer would be asserting the wrong thing.

    THE THREE COLUMNS, and what each one's non-change proves:

      * `BATCH-STATUS` `tinyint(1) unsigned` [mysql/ACASDB.sql:L83] - from
        `Batch-Status pic 9` with `88 Status-Open value 0`
        [copybooks/wsbatch.cob:L25-L26]. Its seeded value is the CONSEQUENCE of gl051's
        rejection at [general/gl051.cbl:L1121] (or its L1102) and is the one field
        Phase 1 reads to decide [general/gl070.cbl:L314]. It is also the single field
        that separates this scenario from `mixed_accepted_rejected`.
      * `CLEARED-STATUS` `tinyint(1) unsigned` [mysql/ACASDB.sql:L84] - from
        `Cleared-Status pic 9` with `88 Waiting value 0`
        [copybooks/wsbatch.cob:L29-L30]. `gl072` would set it to 1
        [general/gl072.cbl:L375].
      * `POSTED` `int(8) unsigned` [mysql/ACASDB.sql:L88] - a BINARY DAY NUMBER from
        `Posted binary-long` [copybooks/wsbatch.cob:L38], NOT a date text, which is why
        normalisation job 3 must never touch it. `gl072` would stamp the run date into
        it [general/gl072.cbl:L376]. The clock is pinned precisely so that a spurious
        stamp would be unmistakable rather than noise.

    Rows are matched BY PRIMARY-KEY VALUE and never by position, which is the harness's
    own rule and matters as much here as in the differ.

    Args:
        parity_run: The completed eight-stage run.
        seed_baseline: The pristine seeded state.
        harness: The three harness modules, for `load_dump` and the table map.
    """
    from conftest import assert_dump_wellformed

    table = "GLBATCH-REC"
    specification = harness.dump_tables.table_spec(table)
    filename = harness.diff_states.dump_filename(table)

    def column_map(tree, side_label: str) -> dict[str, dict[object, object]]:
        """One tree's `GLBATCH-REC` values for the three columns, keyed by primary key.

        Args:
            tree: The normalised tree holding the dump.
            side_label: What this tree is, quoted in every message.

        Returns:
            `{column: {primary-key value: cell}}` for the three columns of interest.
        """
        dump = harness.diff_states.load_dump(tree / filename)
        assert_dump_wellformed(dump, where=f"{side_label} {table}")
        columns = list(dump["columns"])
        key_index = columns.index(specification.primary_key)
        wanted = ("BATCH-STATUS", "CLEARED-STATUS", "POSTED")
        return {
            name: {row[key_index]: row[columns.index(name)] for row in dump["rows"]}
            for name in wanted
        }

    oracle = column_map(parity_run.paths.cobol_normalized, "the compiled COBOL oracle")
    migrated = column_map(
        parity_run.paths.python_normalized, "the migrated Python cycle"
    )
    seeded = column_map(seed_baseline.cobol_normalized, "the pristine seed")

    assert oracle.keys() == migrated.keys() == seeded.keys()
    for name in oracle:
        assert oracle[name] == seeded[name], (
            f"the compiled COBOL oracle CHANGED `{table}`.`{name}`. Seeded "
            f"{seeded[name]!r}, found {oracle[name]!r}. On this route the batch must "
            f"come back exactly as seeded, because the abort at "
            f"[general/general.cbl:L810-L811] means gl072 never reached "
            f"[general/gl072.cbl:L375-L377]. Keys are primary-key values, never "
            f"positions."
        )
        assert migrated[name] == seeded[name], (
            f"the migrated Python cycle CHANGED `{table}`.`{name}`. Seeded "
            f"{seeded[name]!r}, found {migrated[name]!r}. The terminate-code gate in "
            f"`acas_posting/cli/gl_post_cycle.py` should have stopped the cycle before "
            f"gl072 was dispatched at all."
        )
        assert oracle[name] == migrated[name], (
            f"the two sides disagree on `{table}`.`{name}`: the oracle has "
            f"{oracle[name]!r} and the migrated cycle {migrated[name]!r}."
        )

    # The batch must actually BE there. An empty GLBATCH-REC would make every assertion
    # above vacuously true, and would silently turn this scenario into `empty_batch`.
    assert seeded["BATCH-STATUS"], (
        f"the seed left `{table}` EMPTY, so there was no open batch for Phase 1 to "
        f"find [general/gl070.cbl:L314-L315] and every comparison above is vacuous. "
        f"This scenario requires one General Ledger batch, deliberately left open and "
        f"deliberately unbalanced [copybooks/wsbatch.cob:L15-L16, L25-L27, L40-L44]."
    )


def test_diagnostic_display_has_no_database_effect(
    parity_run, seed_baseline, harness
) -> None:
    """`perform gl060a` is a LOG RECORD on the Python side, and invisible in every dump.

    [general/gl070.cbl:L288] performs a display paragraph immediately before the raise:

         287      if       a = 1
         288               perform gl060a
         289               move 5 to ws-term-code
         290               go to  main-exit.

    It has NO DATABASE EFFECT, so per Plan section 0.3.4 it becomes a log record at a
    severity matching the original's intent. Two obligations follow, and both are
    asserted here rather than assumed: IT MUST NOT ALTER CONTROL FLOW - the raise on the
    very next line still happens, which
    `test_abort_is_reproduced_as_term_code_five` establishes - and IT MUST NEVER APPEAR
    IN A TABLE DUMP.

    The second obligation is proved twice over, structurally and then by state.

    STRUCTURALLY: a dump object carries EXACTLY FIVE KEYS - `table`, `primary_key`,
    `columns`, `row_count`, `rows` - AND NO OTHERS. There is no `stdout` key, no `log`
    key, no `message` key and no place for one, so diagnostic output cannot reach a dump
    by construction. And the run transcripts live OUTSIDE the compared trees entirely,
    so they cannot leak in through the file system either.

    BY STATE: the compiled side's three tables are identical to the pristine seed, so
    whatever the display wrote, it wrote nothing to the database.

    Args:
        parity_run: The completed eight-stage run.
        seed_baseline: The pristine seeded state.
        harness: The three harness modules.
    """
    from conftest import diff_trees_directly

    # STRUCTURAL PROOF 1 - the transcripts are outside both compared trees.
    run_logs = parity_run.paths.run_logs
    for tree in (
        parity_run.paths.cobol_dump,
        parity_run.paths.python_dump,
        parity_run.paths.cobol_normalized,
        parity_run.paths.python_normalized,
    ):
        assert not run_logs.is_relative_to(tree), (
            f"the run transcript directory {run_logs} lies INSIDE the compared tree "
            f"{tree}. Diagnostic output - the display paragraph at "
            f"[general/gl070.cbl:L288] among it - would then become part of the state "
            f"under comparison, which it must never be."
        )

    # STRUCTURAL PROOF 2 - a dump has five keys, in fixed order, and no room for a log.
    expected_keys = tuple(harness.dump_tables.DUMP_KEYS)
    assert expected_keys == ("table", "primary_key", "columns", "row_count", "rows")
    for side_label, tree in (
        ("the compiled COBOL oracle", parity_run.paths.cobol_normalized),
        ("the migrated Python cycle", parity_run.paths.python_normalized),
    ):
        for table in parity_run.tables:
            dump = harness.diff_states.load_dump(
                tree / harness.diff_states.dump_filename(table)
            )
            assert tuple(dump) == expected_keys, (
                f"{side_label}'s `{table}` dump carries {tuple(dump)!r}. A dump has "
                f"exactly five keys in fixed insertion order and no others - no "
                f"timestamp, no server version, no scenario name, no side and NO LOG "
                f"OUTPUT. The side is recorded in the PATH."
            )

    # STATE PROOF - the oracle wrote nothing at all, display paragraph included.
    against_seed = diff_trees_directly(
        parity_run.paths.cobol_normalized,
        seed_baseline.cobol_normalized,
        parity_run.tables,
    )
    assert against_seed.is_empty, (
        f"the compiled side's tables differ from the pristine seed by "
        f"{against_seed.total_differences} finding(s), so SOMETHING on the abort path "
        f"wrote to the database. The display paragraph at [general/gl070.cbl:L288] "
        f"must have no database effect, and gl070 is read-only throughout.\n"
        f"  In the report below `cobol` is the oracle's post-run tree and `python` is "
        f"the seed baseline.\n"
        f"{harness.diff_states.render(against_seed)}"
    )


def test_diff_exit_contract_is_honoured(parity_run, harness, tmp_path) -> None:
    """THE THREE-WAY EXIT CONTRACT, and the one conflation that must never happen.

        0  the two trees are identical, and stdout is EMPTY - zero bytes    PASS
        1  a real behavioural difference, with a deterministic report    FAILURE
        2  THE COMPARISON COULD NOT BE PERFORMED                          ERROR

    "A test that treats 'could not compare' as 'no differences' is the single worst bug
    available in this tree."

    THE 0-VERSUS-2 DISTINCTION IS MOST LETHAL IN THIS SCENARIO, AND IT IS WORTH BEING
    EXPLICIT ABOUT WHY. Everywhere else in the suite the expected state is a set of
    CHANGES, so a comparison that silently failed to happen would show up as a missing
    change and the test would notice. Here the expected state is an ABSENCE: a missing
    dump tree, a missing table file and a correctly empty change set can all be made to
    look alike by careless code, because "nothing differs" is the right answer. Exit 2
    must therefore raise, and it does - conftest maps it to `HarnessFaultError`, which
    is an ERROR and never a pass. This test provokes the mapping rather than trusting
    it, by asking for a comparison of two trees that are not there.

    A ZERO-BYTE `diff.txt` IS DELIBERATE AND IS NOT AN ABSENT FILE. The evidence
    document must distinguish "compared, and identical" from "never compared": an
    existing empty report says the first, an absent report says nothing at all.

    Args:
        parity_run: The completed eight-stage run.
        harness: The three harness modules.
        tmp_path: An empty directory, standing in for an output root that holds no
            trees - the provocation for exit 2.
    """
    from conftest import (
        HarnessFaultError,
        diff,
    )

    diff_states = harness.diff_states
    assert (
        diff_states.EX_IDENTICAL,
        diff_states.EX_DIFFERENT,
        diff_states.EX_ERROR,
    ) == (0, 1, 2)

    result = parity_run.outcome.result
    assert result.returncode == diff_states.EX_IDENTICAL, (
        f"stage 8 exited {result.returncode}; only {diff_states.EX_IDENTICAL} is a "
        f"pass.\n{result.describe()}"
    )
    assert result.stdout == "", (
        f"a passing comparison writes ZERO BYTES to stdout - not a banner, not a "
        f"summary. Got {result.stdout!r}."
    )
    assert parity_run.outcome.is_empty is True
    report = parity_run.outcome.report
    assert report.is_file(), (
        f"{report} is absent. A pass writes an EMPTY report rather than none, because "
        f"an existing empty file says \"compared, and identical\" while a missing file "
        f"says nothing at all."
    )
    assert report.stat().st_size == 0, (
        f"{report} holds {report.stat().st_size} byte(s) while stage 8 reported an "
        f"empty diff. The renderer returns the empty string when the two trees are "
        f"identical, so the two views disagree and neither can be trusted."
    )
    assert harness.diff_states.render(parity_run.tree) == ""

    # EXIT 2 IS AN ERROR, PROVEN BY PROVOCATION. `tmp_path` holds no normalised
    # trees, so the comparison cannot be performed; conftest must raise rather than
    # report a pass.
    with pytest.raises(HarnessFaultError) as raised:
        diff(SCENARIO, out_dir=tmp_path)
    assert str(diff_states.EX_ERROR) in str(raised.value), (
        "the harness-fault diagnosis must name the exit status that produced it, so an "
        "operator can tell a failed comparison from a found difference."
    )


def test_dump_is_wellformed_on_both_sides(
    parity_run, harness, frozen_schema
) -> None:
    """Every dump on both sides has the shape the protocol guarantees.

    ESPECIALLY IMPORTANT ON THIS ROUTE: it is what distinguishes "correctly empty" from
    "never dumped". Since the expected state here is an absence, a truncated, malformed
    or absent dump would produce exactly the verdict a correct run produces, and nothing
    else in the protocol would notice.

    THE SHAPE: exactly five keys in fixed insertion order - `table`, `primary_key`,
    `columns`, `row_count`, `rows` - and no others; `columns` in the frozen schema's
    ordinal order and never sorted; `rows` a list of lists in primary-key-ascending
    order, positionally aligned; `row_count == len(rows)`; `DECIMAL` values as canonical
    JSON STRINGS at the declared scale, never JSON numbers and never exponent notation;
    integers as JSON integers; NO value a float (R-2) and NO value null.

    Every structural check is DELEGATED to conftest, which delegates in turn to the
    harness's own single definition of the contract (R-4). Nothing is reimplemented
    here, and the frozen schema is passed so that the column list is additionally
    required to match `mysql/ACASDB.sql`'s ordinal order EXACTLY - rows are positional,
    so a column list in any other order has no meaningful alignment.

    Args:
        parity_run: The completed eight-stage run.
        harness: The three harness modules.
        frozen_schema: `mysql/ACASDB.sql` parsed into the column-type map, read only.
    """
    from conftest import assert_dump_wellformed, read_dump

    for side_label, tree in (
        ("cobol", parity_run.paths.cobol_normalized),
        ("python", parity_run.paths.python_normalized),
    ):
        assert tree.is_dir(), (
            f"the {side_label} normalised tree is absent from {tree}. A MISSING "
            f"TREE IS NOT AN EMPTY DIFF: on this route the expected state is an "
            f"absence, so a "
            f"tree that was never written looks exactly like a correct result."
        )
        for table in parity_run.tables:
            path = tree / harness.diff_states.dump_filename(table)
            assert path.is_file(), (
                f"{path} is absent, so `{table}` was never dumped on the {side_label} "
                f"side. That is a harness fault and not an empty change set."
            )
            assert path.stat().st_size > 0, f"{path} is zero bytes."

            dump = read_dump(path)
            assert_dump_wellformed(
                dump, where=f"{side_label} {table}", schema=frozen_schema
            )
            # Restated explicitly, because these two are the ones that would let a
            # truncated dump masquerade as a correct absence.
            assert dump["table"] == table
            assert dump["row_count"] == len(dump["rows"])
            assert dump["primary_key"] in dump["columns"]
