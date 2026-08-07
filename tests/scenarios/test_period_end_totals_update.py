"""Period-end totals state parity: `period_end_totals`, four operations, one diff.

THE ONE SENTENCE THIS FILE EXISTS TO ASSERT, from Agent Action Plan section 0.8.5:
"seed identically through the maintainer's load programs, run the compiled cycle,
dump the affected tables ordering-normalised, reset, run the Python cycle, dump
again - and the diff MUST BE EMPTY."

This is the ONLY scenario that drives FOUR operations in sequence, and therefore the
only one whose dump carries the CUMULATIVE effect of the period-total writes across
both ledgers. ⚠️ NARROWED: this previously also called it "the ONLY one for which
`SYSTOT-REC` is genuinely in scope", which is FALSE - measured over the nine scenario
files, three declare that table: `clean_batch_sl`, `clean_batch_pl` and this one. What
is unique here is REACH, not the table. Agent Action Plan section
0.6.4 is what makes it verifiable at all: the nine period-total write sites are "all
inside the Sales and Purchase programs, and all in scope ... the sole writers of the
totals record, which makes the period-end-totals scenario verifiable by inspecting
one table."

THE INVERTED PREMISE, Agent Action Plan section 0.8.2, verbatim:
"There is no test suite: compiled COBOL execution is the behavioral specification,
defects included. A defect reproduced is correct; a defect fixed is a failure."

Its corollary governs every assertion below: A TEST THAT ASSERTS CORRECT ACCOUNTING
RATHER THAN OBSERVED BEHAVIOUR IS ITSELF A DEFECT. So no test here predicts a total,
recomputes one, or checks that the nine totals "balance" against the invoice lines.
Every totals assertion is an assertion of AGREEMENT BETWEEN THE TWO SIDES, arbitrated
by the compiled run (R-6). Recomputation is arithmetic-tier work and lives in
`tests/arithmetic/`.

THERE IS NO USER RULES DOCUMENT FOR THIS PROJECT. `review_rules` reports that none
was provided, so there is no on-disk rules file and no reader should look for one.
The six binding rules R-1 to R-6 live in the Agent Action Plan itself, section 0.7.2,
and their exact wording is retrievable from the requirements via `review_prompt`. Each
is named below at the site that honours it, and where the plan is silent this file
holds to enterprise-standard best practice and invents nothing.

===========================================================================
THE SCENARIO
===========================================================================

`harness/scenarios/period_end_totals.yaml`, and its shape is read from the file
rather than assumed. Three of its keys differ in kind from every sibling scenario:

  `subsystem: ""`   THE EMPTY SCALAR, here and nowhere else. This run spans TWO
                    menus, and the oracle-side runner refuses a file whose declared
                    subsystem disagrees with the subsystem of the operation it was
                    asked to run [harness/run_cobol_scenario.sh acas_select_operation]. Its map
                    sends `sl_invoice_post` and `sl_cash_post` to the Sales menu and
                    `pl_order_post` and `pl_payment_post` to the Purchase menu, so no
                    single name is true for all four and naming either menu would
                    fail two invocations on a cross-check rather than on anything
                    behavioural. The empty scalar reads as "the file does not say",
                    and the subsystem then comes from the operation being run.

  `operations:`     A FLAT SEQUENCE OF OPERATION NAMES and nothing else - no
                    per-item subsystem, no per-item answer map, no per-item
                    expectation - because each runner owns the operation-to-subsystem
                    map itself and a nested block under this key is refused outright.
                    The per-operation subsystem therefore comes from the single
                    definition of that map, `tests/conftest.py`'s `OPERATIONS`, and
                    this file restates it only as the expectation it asserts against.

  `expected_status:` A flat sequence of whole process statuses matching `operations`
                    POSITIONALLY, one per operation. There is no `expect.term_code`
                    block; the status is the observable, and it is four zeros.

===========================================================================
THE FOUR OPERATIONS, IN THE ONLY ORDER THAT IS CORRECT
===========================================================================

  #  operation          subsystem  answer                     status  menu paragraph
  1  sl_invoice_post    sales      -                          0       sales/sales.cbl
                                                                      load07. L756-768
  2  sl_cash_post       sales      payment_post_confirm=YES   0       sales/sales.cbl
                                                                      load11. L792-796
  3  pl_order_post      purchase   -                          0       purchase/
                                                                      purchase.cbl
                                                                      load08. L752-762
  4  pl_payment_post    purchase   payment_post_confirm=YES   0       purchase/
                                                                      purchase.cbl
                                                                      load12. L786-790

`sl_invoice_post` IS load07, NOT load08. [sales/sales.cbl:L756] carries
`*> Sales trans posting`; `load08.` at [sales/sales.cbl:L770] dispatches the
OUT-OF-SCOPE sl080 (Payment Input). The menu letter is `(G) Sales Transactions Post`.
An occurrence of load08 against Sales anywhere is an error and is not propagated -
`tests/conftest.py`'s `OPERATIONS` already carries the correction, and this file
asserts against it.

THE ORDER IS PART OF THE SPECIFICATION, not a convenience. Operation 3 sets flags
operation 4 reads [purchase/pl060.cbl:L373-L375]; operations 1 and 3 create the
ledger rows operations 2 and 4 rewrite; and A-17's write [sales/sl060.cbl:L1173] is
read back by a LATER operation [purchase/pl100.cbl:L564]. All four run inside a
SINGLE stage 2 and a single stage 6, one at a time (R-3), with NO dump between them,
so the diff proves the CUMULATIVE effect of the sequence.

`gl_end_of_cycle` (gl080) IS DELIBERATELY NOT DRIVEN BY THIS SCENARIO. ⚠️ NARROWED:
this previously read "here or in any other scenario file", which is FALSE -
`harness/scenarios/end_of_cycle_gl.yaml` drives it, with its own affected-table list
and its own suite in `tests/scenarios/test_end_of_cycle_gl.py`. The scenario file this
paragraph cites had already been corrected to say so
[harness/scenarios/period_end_totals.yaml "It is not absent from the directory"]; this
restatement was the stale copy left behind. gl080 is Phase 3 (Transaction Deletion)
plus Phase 5 (End of Period
Processing), it promotes THREE interactive answers, and driving it would make the
totals attribution ambiguous - whereas section 0.6.4's nine write sites make the
totals attributable to one table without it. The decision is recorded at length in
the scenario file's own header [harness/scenarios/period_end_totals.yaml
"gl_end_of_cycle IS DELIBERATELY NOT APPENDED TO THIS SCENARIO"]
and belongs in `docs/migration/ambiguity-resolutions.md`; the register assigns it no
`Q-` identifier because it is a scoping decision rather than a question about
compiled behaviour. Because gl080 is not driven HERE, `system.period: 1` is INERT in
this file - it is carried because it is part of the seeded system
record and because the key set is uniform, not because any listed operation divides
by it. For completeness and never driven here, gl080's three promoted answers are
the backup confirmation [general/gl080.cbl:L295-L302], the disk-change reply
[general/gl080.cbl:L542-L557] and the archive path [general/gl080.cbl:L553-L557].

===========================================================================
THE NINE PERIOD-TOTAL WRITE SITES - every one read out of the frozen source
===========================================================================

  #  locator                     target field                  guard
  1  sales/sl055.cbl:L675        sl-invoices-this-month         if ih-type = 2  L674
  2  sales/sl055.cbl:L677        sl-credit-notes-this-month     if ih-type = 3  L676
  3  sales/sl060.cbl:L641        sl-credit-deductions           UNCONDITIONAL
  4  sales/sl060.cbl:L700        sl-cn-unappl-this-month        UNCONDITIONAL, and
                                                                OUTSIDE the L695
                                                                guard
  5  sales/sl100.cbl:L404        t-paid AND sl-payments -       if oi-type = 5  L402
                                TWO RECEIVERS IN ONE ADD       (else oi-type = 6
                                                                L407-L410)
  6  purchase/pl055.cbl:L582     pl-invoices-this-month         if ih-type = 2  L581
  7  purchase/pl055.cbl:L584     pl-credit-notes-this-month     if ih-type = 3  L583
  8  purchase/pl060.cbl:L628     pl-cn-unappl-this-month        UNCONDITIONAL, and
                                                                OUTSIDE the L623
                                                                guard
  9  purchase/pl100.cbl:L396     t-paid AND pl-payments -       if oi-type = 5  L394
                                TWO RECEIVERS IN ONE ADD       (else oi-type = 6
                                                                L399-L402)

`oi-type`: 3 is a Credit Note, 5 is a Payment, 6 is the else-branch case.
`ih-type`: 1 is Receipts and is EXCLUDED by [sales/sl055.cbl:L670] and
[purchase/pl055.cbl:L579]; 2 is an Invoice and 3 a Credit Note.

SITES 4 AND 8 VERBATIM. Both add unconditionally, immediately after a print block
that is guarded - which is almost certainly not what the author intended, and is the
specification:

    sales/sl060.cbl
    L695      if       FS-Cobol-Files-Used and File-18-Exists
    L696               move  "Un-Applied Credits C/F " to  l8-desc
    L697               move  work-b  to  l8-tot
    L698               write  print-record  from  line-8 after 3.
    L699 *>
    L700      add      work-b to sl-cn-unappl-this-month.   <- OUTSIDE the guard

    purchase/pl060.cbl
    L623      if       FS-Cobol-Files-Used and File-28-Exists
    L624               move  "Un-Applied Credits C/F " to  l8-desc
    L625               move  work-b  to  l8-tot
    L626               write  print-record  from  line-8 after 3.
    L627 *>
    L628      add      work-b to pl-cn-unappl-this-month.   <- OUTSIDE the guard

THESE TWO MATTER SPECIFICALLY BECAUSE `file_system_used: 1`. That pins
`File-System-Used` to 1 [copybooks/wssystem.cob:L112-L114], so the condition name
`FS-Cobol-Files-Used`, declared `value zero`, is FALSE - the two print blocks never
run, AND THE TWO TOTALS ACCUMULATIONS STILL HAPPEN. That is the whole reason
`SYSTOT-REC` changes in this scenario at all under relational mode. They are
reproduced, never "aligned" with their guards (R-4).

SITES 5 AND 9 VERBATIM. Each accumulates into TWO receivers in ONE `ADD`, and
neither is split, reordered or normalised (R-4):

    sales/sl100.cbl                        purchase/pl100.cbl
    L402  if oi-type = 5                   L394  if oi-type = 5
    L403       add oi-approp to t-approp    L395       add oi-approp to t-approp
    L404       add oi-paid to t-paid        L396       add oi-paid to t-paid
                   sl-payments                             pl-payments
    L405       add oi-deduct-amt to         L397       add oi-deduct-amt to
                   t-deduct                                t-deduct
    L406  else                              L398  else
    L407   if oi-type = 6                   L399   if oi-type = 6
    L408       add oi-approp to j-approp     L400       add oi-approp to j-approp
    L409       add oi-paid to j-paid         L401       add oi-paid to j-paid
    L410       add oi-deduct-amt to          L402       add oi-deduct-amt to
                   j-deduct.                                j-deduct.
    L412  move oi-approp to oi-paid.        L404  move oi-approp to oi-paid.
    L413  perform Sales-Rewrite.            L405  perform Purch-Rewrite.

===========================================================================
`SYSTOT-REC` - THE FOCAL TABLE, AND A-20
===========================================================================

21 columns, primary key `LEDGER-TOTALS-REC-KEY`, declared at
[mysql/ACASDB.sql:L1376-L1398], laid out by [copybooks/wssys4.cob] and loaded by
`sys4LD`, the second step of the system-file block [common/masterLD.sh:L51-L87].
The primary key is `tinyint(1) unsigned` [mysql/ACASDB.sql:L1377] and the other
TWENTY columns are every one of them `decimal(10,2)`
[mysql/ACASDB.sql:L1378-L1397], which is why normalisation's second job must render
each column at ITS OWN declared scale and never assume a uniform two places: the
twenty render at two, and the integer key renders as an integer.

A-20 LIVES IN THIS TABLE AND IS PRESERVED, NEVER RENAMED. Two spare fields carry
the SALES prefix inside the PURCHASE group: `sl4-spare3` and `sl4-spare4` at
[copybooks/wssys4.cob:L29-L30], inside `Purchase-Ledger-Data` which opens at
[copybooks/wssys4.cob:L20], surfacing as the columns `SL4-SPARE3` and `SL4-SPARE4`
at [mysql/ACASDB.sql:L1396-L1397]. It is a naming defect with no runtime effect,
which is why the anomaly register leaves it unlocked by an arithmetic test - but it
is visible in every dump this file compares.

===========================================================================
THE sl055 / pl055 DIVERGENCES THAT SHAPE WHAT IS ACCUMULATED
===========================================================================

Read out of the frozen source, both sides, and preserved rather than harmonised:

    sales/sl055.cbl                          purchase/pl055.cbl
    L670  if ih-type not = 1                 L579  if ih-type not = 1
    L671    add ih-net ih-extra ih-carriage   L580    add ih-net ih-carriage
    L672        ih-discount ih-vat ih-c-vat            ih-vat ih-c-vat
    L673        ih-e-vat ih-deduct-amt                 giving ws-inv-amt.
    L673        ih-deduct-vat
    L673          giving ws-inv-amt.
    L679  move "Z" to ih-status.             L586  move "Z" to ih-status.
    L680  move "A" to ih-status-A.                   *> 07/01/18 was "z"
    L681  write oi-header.  *> OTM2          L587  write open-item-record-4.

So Sales sums NINE addends across three continuation lines and writes TWO status
fields; Purchase sums FOUR addends on one line and writes ONE. Both are asserted only
as agreement between the two sides; neither is normalised into the other.

===========================================================================
THE ABORT GATES DIVERGE BY LEDGER - AND THAT IS THE SPECIFICATION
===========================================================================

Sales tests `if ws-term-code not = zero` TWICE, at [sales/sales.cbl:L761-L762] and
again at [sales/sales.cbl:L765-L766]. Purchase has NONE - its gate is commented out
at [purchase/purchase.cbl:L755-L758], which the anomaly register carries as A-NEW-5.
The same commented-out block removes Purchase's `pl830` call, while Sales still
dispatches `sl830` on the compiled side at [sales/sales.cbl:L759]. The
`sl800`...`sl830` autogen series is explicitly out of scope (Agent Action Plan
section 0.2.2) and `acas_posting/cli/sl_invoice_post.py` dispatches only sl055 then
sl060, so the four autogen tables are never seeded and appear on no affected-table
list; BOTH runners assert after the run that all four are still empty, and that
assertion lives in the runners rather than here.

A-1 IS CROSS-REFERENCED HERE, NOT OWNED HERE. The missing terminating period at
[sales/sl060.cbl:L1176] - `perform SPL-Posting-Close` with no period - nests
[sales/sl060.cbl:L1177-L1178] inside the L1175 conditional, so in pure General
Ledger mode `GL-Posting-Close` never executes. Its Purchase counterpart at
[purchase/pl060.cbl:L1031] HAS its period. That is why sl060 and pl060 behave
differently at close, and it is locked by `tests/scenarios/test_clean_batch_post_sl.py`
and `tests/scenarios/test_clean_batch_post_pl.py` respectively. Note that the
anomaly register's corrected-locator table names L1176 as the defect line where the
plan gave only the L1172-L1178 span.

===========================================================================
THE TWO `Flag-P` LATCHES ARE HARD PRECONDITIONS - AND THEY ARE ONE-SHOT
===========================================================================

Without `s_flag_p: 2` AND `p_flag_p: 2` in the seeded system record, operations 2 and
4 DO NOTHING AT ALL, and this scenario silently reaches only SEVEN of its nine write
sites - an empty diff that proves far less than it appears to. The count is derived
rather than asserted: operation 1 reaches sites 1, 2, 3 and 4; operation 3 reaches
sites 6, 7 and 8; and operations 2 and 4 reach sites 5 and 9 and nothing else. So the
two sites lost are exactly the two two-receiver payment adds.

    sales/sl100.cbl
    L296      if       S-Flag-P not = 2
    L297               display SL137   at 2301
    L298               display SL002   at 2401
    L299               accept ws-reply at 2433
    L300               go to menu-exit          <- NOTHING IS POSTED
    L301      end-if.
    L303  menu-return.
    ...
    L473      move     "Y"  to  oi-3-flag.
    L474      move     zero to S-Flag-P.        <- THE LATCH IS CLEARED HERE
    L476  menu-exit.
    L477      exit     program.

[purchase/pl100.cbl:L289-L294] has the identical structure, its `menu-return.` is at
[purchase/pl100.cbl:L296], and its latch is cleared at [purchase/pl100.cbl:L465]
beside the `oi-5-flag` set at L464. The two fields are `S-Flag-P`
[copybooks/wssystem.cob:L226] and `P-Flag-P` [copybooks/wssystem.cob:L206]; their
siblings are `S-Flag-A` L224, `S-Flag-I` L225, `P-Flag-A` L204 and `P-Flag-I` L205,
and the two open-item latches are `Oi-3-Flag` L219 and `Oi-5-Flag` L221.

BOTH LATCHES ARE CLEARED BY THE RUN, so a repeat of operation 2 or 4 within the same
seeded state is a no-op. That is precisely why stage 5 of the protocol re-seeds, and
why this scenario must never be re-run in place: without the reset, operations 2 and
4 would post nothing on the second leg and the diff would be empty FOR THE WRONG
REASON.

===========================================================================
THE ONE PROMOTED INTERACTIVE ANSWER
===========================================================================

    sales/sl100.cbl                          purchase/pl100.cbl
    L310  acpt-xrply.                        L302  acpt-xrply.
    L311   display "OK to Post Payment       L303   display "OK to post payment
           Transactions (YES/NO) ? [   ]"           transactions (YES/NO) ?
                                                    <   > enter {CR}"
    L313   move spaces to wx-reply.          L305   move spaces to wx-reply.
    L314   accept wx-reply at 1256 update    L306   accept wx-reply at 1256 update
    L315   move function upper-case          L307   move function upper-case
             (wx-reply) to wx-reply.                  (wx-reply) to wx-reply.
    L316   if wx-reply = "NO"                L308   if wx-reply = "NO"
    L317        go to menu-exit.             L309        go to menu-exit.
    L318   if wx-reply not = "YES"           L310   if wx-reply not = "YES"
    L319        go to acpt-xrply.            L311        go to acpt-xrply.
    L321   perform OTM3-Open.                L313   perform Purch-Open.
    L322   perform Sales-Open.               L314   perform OTM5-Open.

The prompt WORDING diverges - Sales uses `[   ]` and title-case "Post Payment
Transactions", Purchase uses `<   > enter {CR}` and lower-case "post payment
transactions" - and the divergence is preserved rather than harmonised (R-4). The
LOGIC is identical, and it has NO DEFAULT: each program blanks the reply immediately
before accepting it and re-asks for ever on a blank, so only the literal "YES"
proceeds and only "NO" exits, having written nothing. `"NO"` transfers to `menu-exit`
BEFORE the first file is opened, so declining posts nothing at all. That is ambiguity
Q-CLI-OKTOPOST, and it is RESOLVED rather than guessed: the answer is REQUIRED, on
both sides.

This is an accept prompt that GATES A DATABASE WRITE, so per Agent Action Plan
section 0.3.4 it becomes an explicit command-line parameter with the frozen
program's behaviour preserved. The scenario carries it as ONE key, whose value must
be the literal `"YES"`:

    payment_post_confirm: "YES"

ONE KEY COVERS BOTH CASH ROUTES, because the runners are invoked per operation, both
cash programs ask the same question, and both refuse to proceed without an answer.
THE KEY IS SEMANTIC AND IS NOT A COPY OF ANY COMMAND-LINE OPTION SPELLING:
`harness/run_python_scenario.sh` reads the key, validates it as YES or NO, and owns
the translation to whatever the entry points actually spell, probing each module's
`--help` once and failing as a HARNESS FAULT if a required option is absent. This
file therefore never constructs a command line, never builds an argument vector, never
starts a child process, never invokes an entry point as a module and never names an
option. Everything runs through the one protocol helper.

The three other answer keys are deliberately absent, because none of their routes is
on this path: the transfer-file clear belongs to the IRS route, and the two
end-of-cycle answers belong to the operation this scenario omits. The invoice and
order routes promote NOTHING - sl055 and sl060 have only diagnostic
acknowledgements, and pl060's own confirmation prompt is entirely commented out at
[purchase/pl060.cbl:L362-L370].

===========================================================================
THE TEN-STAGE PROTOCOL, AND THE THREE-WAY EXIT CONTRACT
===========================================================================

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

All four operations run inside a SINGLE stage 2 and a single stage 6, in the declared
order. There is exactly ONE dump per side and none between operations.

    exit 0  the two normalised trees are IDENTICAL, and stdout is EMPTY - zero
            bytes, not a banner.                                            PASS
    exit 1  a real behavioural difference, with a deterministic report.      FAILURE
    exit 2  THE COMPARISON COULD NOT BE PERFORMED - a missing tree, a missing table
            file, a malformed dump, a shape mismatch, a float in the input, a
            duplicate primary key, a wrong key order, `row_count != len(rows)`, a
            ragged row or a null.                                           ERROR

A test that treated "could not compare" as "no differences" would be the single worst
bug available in this tree, so exit 2 is surfaced as a pytest ERROR and never as a
pass. R-6 makes an empty diff the pass condition ONLY WHEN A COMPARISON ACTUALLY
HAPPENED.

The comparison is EXACT: no tolerance, no epsilon, no case or whitespace
insensitivity and no numeric coercion. `1` and `"1"` ARE a difference. Rows align by
PRIMARY-KEY VALUE, never by position. The two labels are `cobol` and `python`, and
`--max-differences` truncates the report only - it always prints the true total and
never changes the exit code.

ALWAYS DUMP, THEN DECIDE THE STATUS. Agent Action Plan section 0.6.5 says of a
run-aborting rejection that "the database effect is therefore THE ABSENCE of
everything the later phases would have written", so ABSENCE IS EVIDENCE and the two
run stages' statuses are recorded rather than allowed to skip the dump that follows
them. Concretely here: if operation 2 or 4 silently no-ops because a latch was not 2
or the answer was not "YES", the ABSENCE of the payment accumulations in
`SYSTOT-REC` is the diagnostic. Every OTHER stage's failure destroys the evidence, so
those raise.

Three exit categories are kept distinct: SUCCESS, including a reproduced abort the
scenario expected; BEHAVIOURAL DIFFERENCE, with the dump still taken; and HARNESS
FAULT, which is a runner that built a bad command line (`argparse` exit 2), a missing
option, an unreachable database, malformed YAML or disagreeing seed fingerprints.

EXIT STATUSES ARE BEHAVIOURAL DATA. Only three in-scope programs set `WS-Term-Code`:
gl070 raises 5 [general/gl070.cbl:L289], sl055 raises 8 [sales/sl055.cbl:L344] and
pl055 raises 8 [purchase/pl055.cbl:L286]. `acas_posting/cli/args.py`'s
`exit_status_for(term_code)` returns 0 for 0 and THE TERM CODE ITSELF otherwise -
ambiguity Q-CLI-EXITSTATUS, settled there and not re-decided here. TERM CODE 8 IS
UNREACHABLE IN THIS HARNESS, and provably rather than hopefully: both raise sites sit
inside `if FS-Cobol-Files-Used` [sales/sl055.cbl:L326], [purchase/pl055.cbl:L266] and
this scenario pins `file_system_used: 1`, which makes that condition name False. Code
5 comes from a program this scenario never runs. Hence four zeros.

===========================================================================
BOUNDING, NEVER IGNORING - AND THE ONE UNAVOIDABLE ASYMMETRY
===========================================================================

THERE IS NO IGNORE-LIST, NO TOLERANCE-LIST AND NO "KNOWN DIFFERENCE" ALLOWANCE
ANYWHERE IN THIS FILE OR IN THE DIFF PATH IT DRIVES. Bounding is done by the
scenario's own affected-table list, and only there. That list is FOURTEEN tables,
alphabetical, and the order is load-bearing because the seed fingerprint is written in
declared order and a disagreement is a harness fault:

    ANALYSIS-REC       GLBATCH-REC        GLPOSTING-REC      PSIRSPOST-REC
    PUINV-LINES-REC    PUINVOICE-REC      PUITM5-REC         PULEDGER-REC
    SAINV-LINES-REC    SAINVOICE-REC      SAITM3-REC         SALEDGER-REC
    SYSTOT-REC         VALUEANAL-REC

`SYSTOT-REC` IS GENUINELY IN SCOPE HERE, and it is never blanket-excluded. Its
inclusion is what makes the nine write sites verifiable "by inspecting one table".
⚠️ NARROWED: this previously read "AND ON NO OTHER SCENARIO'S LIST", which is false -
`clean_batch_sl` and `clean_batch_pl` declare it too. What is unique to this scenario
is REACH rather than the table: driving all four posting operations is what lets ONE
dump carry all nine write sites, where `clean_batch_sl` (sl055 then sl060) reaches four
of them and `clean_batch_pl` (pl055 then pl060) three.
Why each of the other thirteen is present:

  SAINVOICE-REC, SAINV-LINES-REC, PUINVOICE-REC, PUINV-LINES-REC - sl055 and pl055
    stamp the header status bytes [sales/sl055.cbl:L679-L681],
    [purchase/pl055.cbl:L586-L587].
  SALEDGER-REC, PULEDGER-REC - the posting programs rewrite the customer and supplier
    statistics, which is where the moving averages A-8, A-9 and A-10 land.
  SAITM3-REC, PUITM5-REC - sl100 and pl100 walk and rewrite the open-item files:
    `move oi-approp to oi-paid` then the rewrite [sales/sl100.cbl:L412-L413],
    [purchase/pl100.cbl:L404-L405].
  ANALYSIS-REC, VALUEANAL-REC - the deduction analysis. Site 3 adds unconditionally
    [sales/sl060.cbl:L641] and the value file is opened, analysed and closed only when
    `total-deduct` is non-zero [sales/sl060.cbl:L643-L647].
  GLBATCH-REC, GLPOSTING-REC - the Sales and Purchase posting programs write General
    Ledger batches and postings in pure General Ledger mode.
  PSIRSPOST-REC - the fan-out path opens and closes the transfer file even in pure
    General Ledger mode, and A-1 means sl060 does NOT close it.

THE `SYSTOT-REC` OVERLAP, AND WHY IT IS A SIGNAL RATHER THAN AN EXCEPTION.
`SYSTOT-REC` is written by the nine in-scope sites AND persisted by the menu shell's
exit path: `load000` in [sales/sales.cbl:L628-L657] persists keys 1 and 4 on EVERY
call [sales/sales.cbl:L659-L660], [purchase/purchase.cbl:L621-L650] does the same
[purchase/purchase.cbl:L652-L653], and the General menu's `overrewrite` persists keys
1, 2 and 4 [general/general.cbl:L656-L691]. THE MIGRATED CYCLE REPRODUCES THAT
PARAGRAPH - `acas_posting/cli/args.py`'s `overrewrite` is called by every one of the
seven routes - so `SYSTOT-REC`'s persistence is a shared behaviour rather than a
one-sided one, and the comparison is what proves it. That was the recorded R-6 caveat
Q-CLI-OVERREWRITE, now SETTLED by REPRODUCING the paragraph:
`acas_posting/cli/args.py`'s `slpl_menu_state` carries the totals record and
`args.overrewrite` is performed from both arms of `load000`, writing key 2 only when
the route loaded the defaults record so that the Sales and Purchase "keys 1 and 4
only" divergence is inherited rather than harmonised. Because both sides now write
these rows, they are COMPARABLE, and the comparison is bounded by all 22 in-scope
tables rather than by this scenario's declared effect.

A SECOND, RELATED QUESTION IS SPECIFIC TO THIS SCENARIO.
Q-CLI-OVERREWRITE-SECOND-LEG is still open: the omitted half of the COBOL paragraph
zeroes `File-System-Used` and never restores it, which under a literal reading would
put a SECOND dispatch in the same session on the indexed leg. This is the only
scenario that is two dispatches per menu - operations 1 and 2 on Sales, 3 and 4 on
Purchase - so it is the run that measures which leg the oracle's second dispatch
takes.

NEITHER QUESTION IS RESOLVED BY AN IGNORE-LIST, A TOLERANCE OR AN ALLOWANCE. A
divergence on `SYSTOT-REC` is a REAL SIGNAL: the test FAILS, and its message names the
ambiguity identifier so a reader knows which recorded question the finding bears on.

THE CENSUS THAT JUSTIFIES THE REST OF THE EXCLUSIONS, so that they are understood as
bounding rather than ignoring: all twelve in-scope programs contain zero
`perform System-Open`, `-Close`, `-Read`, `-Write`, `-Rewrite`, `-Start` or `-Delete`.
Only the out-of-scope menu shells do it - and their migrated counterpart,
`args.overrewrite`, which BOTH sides run. `SYSDEFLT-REC` appears on no SALES or PURCHASE
scenario's DECLARED-EFFECT list because those exit paths never write key 2 - it is on all
five General ones - and `SYSFINAL-REC` on none at all, because it has no writer anywhere
in the cycle. Every one of them is still DUMPED and COMPARED, because the bound is the 22
in-scope tables and not the declared effect: a table nobody writes is a table whose rows
must not move. `SYSTEM-REC` is bounded TWICE. It is declared and dumped like the rest, with
exactly two cells withheld - `RDBMS-PASSWD char(12)` [copybooks/wssystem.cob:L139] and
`PASS-WORD`, replaced on both sides by `harness/dump_tables.py`'s `REDACTED_COLUMNS`
because a dump is `SELECT *` and a capture is committed evidence - and both runners digest
the row before and after every run, so `protocol.assert_system_record_parity` compares the
two sides' post-run digests over all 169 columns including those two. The eleven
out-of-scope tables are never dumped at all.

===========================================================================
NORMALISATION DOES EXACTLY THREE THINGS, AND THEY ARE ALL DELEGATED
===========================================================================

`harness/normalize.py` owns all three. Nothing here reimplements or extends them, and
no fourth job is added. The obligation runs both ways: remove the representation
artefacts, and NEVER make two genuinely different stored values compare equal, so that
"a non-empty diff is always a real behavioral difference and never an artefact of the
comparison" (Agent Action Plan section 0.6.6) holds.

  1  TRAILING spaces in fixed-character columns, by declared type, `char(1)`
     included. `rstrip(" ")` and trailing only, because a COBOL alphanumeric `MOVE` is
     left-justified with right padding, so LEADING SPACES ARE CONTENT. ASCII U+0020
     only. Motivated by A-12, the width drift `pic x(24)`
     [copybooks/wsledger.cob:L27] to `PIC X(32)` [common/nominalMT.cbl:L299] to
     `char(32)` [mysql/ACASDB.sql:L127]; the schema has 238 `char(` columns and zero
     `varchar(`. DIRECTLY ACTIVE HERE, because the `ih-status` and `ih-status-A` stamps
     [sales/sl055.cbl:L679-L681], [purchase/pl055.cbl:L586] are single-character
     columns and `char(1)` is in this job's scope. A-12 also has a second instance in
     a table on this list, [copybooks/slwsoi.cob:L32] to [common/otm3MT.cbl:L310] to
     [mysql/ACASDB.sql:L905].
  2  DECIMAL scale rendering AT THE DECLARED SCALE, never a uniform two places. The
     schema declares many: 68 at `(9,2)`, 57 at `(10,2)`, 17 at `(4,2)`, 12 at
     `(5,2)`, 4 at `(14,2)`, 2 at `(2,0)`, 2 at `(14,4)` and singletons besides.
     `SYSTOT-REC` itself needs the distinction: its twenty money columns are
     `decimal(10,2)` and its key is an integer.
  3  Two- versus four-digit date text forms, from an EXPLICIT COLUMN ALLOW-LIST and
     nothing wider: `GLPOSTING-REC.POST-DAT`, `IRSPOSTING-REC.POST4-DAT`,
     `PSIRSPOST-REC.IRS-POST-DAT`, `SYSTEM-REC.STATS-DATE-PERIOD` and
     `SALEDGER-REC.SALES-STATS-DATE`. The last is on THIS scenario's affected list, so
     job 3 is genuinely active here. `char(8)` DOES NOT IMPLY DATE:
     `PUITM5-REC.OI5-BATCH` and `SAITM3-REC.OI3-BATCH` are batch references and are
     explicitly excluded even though both tables are on this list. Most in-scope
     "dates" are binary day-number integers and job 3 must not touch them.

===========================================================================
THE FIVE REJECTION CLASSES - NONE OF THEM EXERCISED HERE
===========================================================================

Agent Action Plan section 0.8.1 requires that rejection behaviour be preserved in BOTH
dimensions, disposition and database effect, because "a single generic rejection path
would fail this directive". All five are recorded so that the absence of any of them
from this scenario is a stated expectation rather than an omission - all four
operations expect status 0, and that absence is itself an assertion.

  1  CLEAN REJECTION, NO DATABASE EFFECT - gl072 skips a posting whose batch number is
     non-numeric [general/gl072.cbl:L291-L292] and a record whose handler returned a
     specific error [general/gl072.cbl:L306-L307], with a second site at
     [general/gl072.cbl:L348-L349]. Silent: no message, no counter, no trace. Owned by
     `tests/scenarios/test_mixed_accepted_rejected_batch.py`.
  2  RUN-ABORTING REJECTION - the control-total mismatch, whose database effect is THE
     ABSENCE of everything the later phases would have written. Owned by
     `tests/scenarios/test_control_total_mismatch_rejection.py`, and General-Ledger
     specific because Sales and Purchase batches balance by construction.
  3  PARTIAL DATABASE EFFECT - the half-posted double entry
     [irs/irs030.cbl:L1635-L1652], and the lost update whose pre-loop snapshots
     [irs/irs030.cbl:L1602], [irs/irs030.cbl:L1612] are rewritten at end of job
     [irs/irs030.cbl:L1704-L1708]. Owned by
     `tests/scenarios/test_clean_batch_post_irs.py`.
  4  FILE-ABANDONING REJECTION - a posting-write failure jumps straight to end of job
     [irs/irs030.cbl:L1673-L1678], which still performs the two snapshot rewrites and
     the closes, so the partial state is COMMITTED, not rolled back.
  5  PERMANENTLY FAILING FACADE VERB - the transfer-file handler rejects four of its
     published verbs unconditionally at entry, read-indexed, rewrite, start and
     delete, each answered `WE-Error 988` and `fs-reply 99`
     [common/acas008.cbl:L299-L307], because the underlying file is sequential. The
     published Rewrite verb can therefore never succeed.

A NEAR-MISS THAT MUST NOT BE MISTAKEN FOR ONE OF THE FIVE. A Sales or Purchase run in
which `S-Flag-P` or `P-Flag-P` is not 2, or in which the payment confirmation is not
the literal "YES", is NOT a rejection class - it is a PRECONDITION FAILURE THAT
SILENTLY REDUCES COVERAGE. That is exactly why the latch and answer preconditions are
asserted by their own named tests, separately from the parity assertion, and why each
of those tests says in its failure message what would have been lost.

===========================================================================
THE SEED, AND THE R-3 SEEDING CONSTRAINTS - DOCUMENTED, NEVER IMPLEMENTED
===========================================================================

NINE flat files, and no others:

    system.dat    analysis.dat   value.dat     salesled.dat   invoice.dat
    openitm3.dat  purchled.dat   pinvoice.dat  openitm5.dat

Their loaders, from the frozen contract: `system.dat` drives the four-loader block at
[common/masterLD.sh:L51-L87] - systemLD, then sys4LD, then finalLD, then dfltLD, in
that fixed order, and sys4LD is the step that loads this file's focal table;
`analysis.dat` drives analLD [common/masterLD.sh:L93]; `value.dat` valueLD
[common/masterLD.sh:L116]; `salesled.dat` salesLD [common/masterLD.sh:L112];
`invoice.dat` slinvoiceLD [common/masterLD.sh:L98]; `openitm3.dat` otm3LD
[common/masterLD.sh:L104]; `purchled.dat` purchLD [common/masterLD.sh:L111];
`pinvoice.dat` plinvoiceLD [common/masterLD.sh:L107]; `openitm5.dat` otm5LD
[common/masterLD.sh:L105].

THE EIGHT FORBIDDEN NAMES OF THE SAME CONTRACT ARE NAMED BY LOCATOR RATHER THAN BY
FILENAME, so that a search for a forbidden fixture name finds nothing in this file -
the same deliberate choice the scenario file makes. They are the two despatch-note
files [common/masterLD.sh:L95], [common/masterLD.sh:L96], the despatch file
[common/masterLD.sh:L97], the purchase-payments file [common/masterLD.sh:L106], the
two automatic-generation files [common/masterLD.sh:L108], [common/masterLD.sh:L113],
and the stock audit and stock control files [common/masterLD.sh:L114],
[common/masterLD.sh:L115]. Their loaders are never invoked. The seed list is asserted
by EXACT TUPLE EQUALITY, which proves the absence of all ten without naming any of
them.

THE SEED'S STRUCTURAL INTENT, so that a reader knows what makes all nine sites
reachable rather than assuming it: sales invoices of `ih-type = 2` AND `ih-type = 3`
for sites 1 and 2; purchase invoices of both types for sites 6 and 7; at least one
sales deduction so `total-deduct` is non-zero, for site 3 and for the value-file path
at [sales/sl060.cbl:L643-L647]; un-applied credit notes on both ledgers so `work-b` is
non-zero, for sites 4 and 8; and open items of `oi-type = 5` on both ledgers for sites
5 and 9, ideally with at least one `oi-type = 6` so the else-branches
[sales/sl100.cbl:L407-L410], [purchase/pl100.cbl:L399-L402] are exercised as well.
`ih-type = 1` is Receipts and is excluded by [sales/sl055.cbl:L670] and
[purchase/pl055.cbl:L579]. The seeded `SYSTOT-REC` row must start from a KNOWN
NON-ZERO state, or an accumulation would be indistinguishable from a fresh insert.

  NO DDL, EVER. `mysql/ACASDB.sql` is applied VERBATIM and never edited; it already
  contains all 33 `DROP TABLE IF EXISTS`, so re-applying it IS the drop-and-recreate,
  and the database name must be on the client command line because the file carries no
  `USE`.
  AUTOCOMMIT MUST BE OFF WHILE SEEDING, globally and per session.
  [common/glbatchLD.cbl:L9-L12] verbatim: "This modules uses commit and rollback so
  you MUST ensure that autocommit is OFF in the rdb settings. It is as default set
  ON." The seeded state depends on those commit boundaries.
  `common/masterLD.sh` IS NEVER INVOKED, for two independent reasons: its own header
  says "THIS SCRIPT HAS NOT YET BEEN TESTED" [common/masterLD.sh:L4], and it cannot
  execute at all - all 24 loader lines [common/masterLD.sh:L93-L116] omit the `;`
  before `fi`, so `bash -n` rejects it, and it ends by paging a log through an
  interactive pager that would block a headless run for ever. IT IS FROZEN AND IS NOT
  FIXED. `harness/seed.sh` reproduces its documented per-file contract
  [common/masterLD.sh:L44-L115] and checks loader exit codes explicitly - 128 params
  not set up, 64 relational database not set up, 16 write error
  [common/masterLD.sh:L37-L39], with anything above 63 aborting.
  R-4 ITEMS PRESERVED, NOT FIXED: the `dfltLD` strict-versus-lenient exit asymmetry,
  where [common/masterLD.sh:L83] aborts on ANY non-zero unlike the greater-than-63
  tolerance the same script documents at L37-L41; the charset caveat, where
  [mysql/ACASDB.sql:L16] sets one character set while all 33 tables declare another;
  and the `tinyint(1) unsigned` display-width quirk, of which this scenario's own
  `SYSTOT-REC` key [mysql/ACASDB.sql:L1377] is an instance alongside `IH-TYPE`
  [mysql/ACASDB.sql:L441] and the two `IL-VAT-CODE` columns [mysql/ACASDB.sql:L410],
  [mysql/ACASDB.sql:L523].
  NO ADDED VALIDATION, no new field, no schema change. The `SYSTOT-REC` layout keeps
  A-20's two Sales-prefixed spares inside the Purchase group.
  STRICTLY SEQUENTIAL. No distributed test runner, no parallel execution and no
  randomised ordering: parallel scenario runs against one shared MariaDB would break the
  seed-run-dump-reset-run-dump-diff protocol outright. Especially acute here, where
  four operations mutate fourteen tables against one database and the two `Flag-P`
  latches are cleared by the run, so any concurrency would corrupt the seeded state
  irrecoverably.
  THE CREDENTIAL PRECONDITION, documented only. The compiled side takes its connection
  details from the system record it was seeded with [copybooks/wssystem.cob:L137-L144],
  copied into the connection block [copybooks/wsfnctn.cob:L56-L62] whose user and
  password fields hold AT MOST TWELVE CHARACTERS [copybooks/wsfnctn.cob:L58],
  [copybooks/wsfnctn.cob:L59]. So the `ACAS_DB_*` environment the migrated side uses
  must EQUAL the credential fields inside the seeded `system.dat`, or the two legs
  connect as different accounts and their captures are not comparable at all. No
  credential of any kind appears in this file.

===========================================================================
RULE COMPLIANCE, PER RULE
===========================================================================

  R-1  NO COBOL AT RUNTIME. The import list is closed at four: `__future__`,
       `collections.abc`, `typing` and the test runner. IT NEVER IMPORTS THE ORACLE
       TREE - not as a package, not as a from-import of one of its modules, and not by
       loading one of its files dynamically. The oracle tree is not a Python package
       and `pyproject.toml` excludes it from packaging, which is the structural
       enforcement of the rule. The three harness
       Python modules are reached only through `tests/conftest.py`'s `harness` fixture,
       which loads them BY EXPLICIT FILE PATH, and the compiled oracle is reached only
       out of process, through the harness shell scripts the protocol helper drives.
       Nothing here starts a process, loads a shared library or binds a foreign
       function.
  R-2  ZERO BINARY FLOATING POINT. No binary-radix numeric type, no approximate
       equality helper from either the test runner or the standard library's maths
       module, no tolerance and no epsilon appears anywhere below, and no dataframe or
       array library is imported. No accounting value is computed here at all: the only
       numbers this file handles are a status code, a table count and a binary run
       date, each an `int`. The differ's own gate rejects a float in either input with
       exit 2, which this file surfaces as an ERROR.
  R-3  NO NEW VALIDATIONS, FIELDS OR SCHEMA CHANGES; NO CONCURRENCY. This file emits
       no DDL, opens no connection of its own, adds no check the COBOL lacks, and
       introduces no thread, no coroutine runtime, no process pool, no connection pool
       and no distributed test runner. It asserts what the scenario DECLARES and never
       judges the
       declaration.
  R-4  LEGACY ANOMALIES REPRODUCED, NEVER FIXED. Every totals assertion asserts
       AGREEMENT and never a predicted figure. The two unconditional adds at
       [sales/sl060.cbl:L700] and [purchase/pl060.cbl:L628] are asserted as they stand
       and are NOT aligned with their guards; the two two-receiver adds at
       [sales/sl100.cbl:L404] and [purchase/pl100.cbl:L396] are not split; the
       one-versus-two status-field divergence between sl055 and pl055 is not
       harmonised; the diverging abort gates are not harmonised; and A-20's misnamed
       spares are not renamed.
  R-5  FULL TRACEABILITY. Every anomaly this file touches is named by identifier -
       A-1 cross-referenced, A-2 and A-3 explicitly NOT exercised here, A-8, A-9, A-10,
       A-12, A-17 and A-20 - and every claim carries its `[path:Lnnn]` locator, in this
       docstring and again at each assertion site. Coverage is EVIDENCE AND NOT A GATE:
       there is no `--cov-fail-under` and this file adds none.
  R-6  COMPILED BEHAVIOUR IS THE TIE-BREAKER. The empty normalised diff is the
       arbiter. The ambiguity identifiers this file cites are drawn from the existing
       register and NONE of them is invented here: Q-CLI-OVERREWRITE and
       Q-CLI-OVERREWRITE-SECOND-LEG for the `SYSTOT-REC` overlap, Q-CLI-OKTOPOST for
       the promoted answer, Q-CLI-EXITSTATUS for the status mapping,
       Q-CLI-SYSREC-PINS for the re-pinned system columns, Q-A17-POSTINGS-EFFECT for
       A-17's stored value, and Q-19 with Q-QUARTER-SUBSCRIPT for A-2. The register
       lives in `docs/migration/ambiguity-resolutions.md`, the anomaly log in
       `docs/migration/anomaly-log.md`, and the per-scenario evidence in
       `docs/migration/scenario-diff-evidence.md`. THOSE ARE TEXTUAL REFERENCES ONLY:
       nothing here imports them, checks that they exist, or skips because they do not.

===========================================================================
WHAT THIS FILE DOES NOT DO
===========================================================================

It does not recompute a total, predict one, or check that the nine totals balance
against the invoice lines - that is arithmetic-tier work. It does not reimplement the
comparison, the dump, the normalisation or any stage of the protocol. It does not
re-register the `scenario` marker, which `pyproject.toml` already declares under
`--strict-markers`. It does not restate the 22-table in-scope inventory or any primary
key, both of which have exactly one definition in this repository. It adds no
`__init__.py`, no nested `conftest.py` and no helper module. It makes no timing
assertion and measures no performance, because Agent Action Plan section 0.8.4 pursues
none. And it COLLECTS ON A BARE HOST: five of its tests need no stack at all, and
every test that does begins with the precise skip the `protocol` fixture provides.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any, Final
import re

import pytest

# THE TIER LABEL. ALREADY REGISTERED, in `pyproject.toml`'s
# `[tool.pytest.ini_options] markers` under `--strict-markers --strict-config`, where
# its description records that it requires the Compose stack and a seeded database.
# Nothing here re-registers it, and this file adds no `pytest.ini`, no `markers =`, no
# `pytest_configure` and no `pytest_collection_modifyitems`. Selectable as
# `pytest -m scenario` and `pytest -m "scenario or determinism"`.
# The TIER mark, applied to the whole module because every test in it belongs to the
# tier. THE INFRASTRUCTURE MARKS ARE NOT HERE: `database` and `oracle` are declared per
# test, on exactly the tests whose fixture closure reaches the harness stack, because
# several tests in this file read only files on disk and pass on a bare host. A module
# mark would claim they need a MariaDB and a built oracle, and `-m database` would then
# select tests that require neither.
pytestmark = pytest.mark.scenario

# The scenario this file owns, and the stem of `harness/scenarios/<name>.yaml`.
SCENARIO: Final[str] = "period_end_totals"


# ---------------------------------------------------------------------------
#  SECTION 1  -  THE FOUR OPERATIONS
#
#  Restated here as the EXPECTATION this file asserts against, never as a second
#  authority. The scenario file declares the ordered names; the operation-to-subsystem
#  map has exactly one definition, in `tests/conftest.py`'s `OPERATIONS`, and that
#  definition is reached through the `protocol` fixture's own `definition` view of the
#  scenario plus the assertions below. A disagreement between this file, the scenario
#  file and that map fails loudly rather than drifting (R-4).
# ---------------------------------------------------------------------------

# The order is load-bearing - see the module docstring. Operation 1 is
# `sl_invoice_post`, whose COBOL counterpart is `load07` and NOT `load08`.
OPERATION_ORDER: Final[tuple[str, str, str, str]] = (
    "sl_invoice_post",
    "sl_cash_post",
    "pl_order_post",
    "pl_payment_post",
)

# The per-operation subsystem. THE SCENARIO FILE DOES NOT DECLARE THESE - its
# `operations:` key is a flat sequence of names and a nested block under it is refused
# outright - so they come from the runners' shared map and are asserted here because
# this run spans two menus and the file's own `subsystem` is therefore the empty
# scalar.
OPERATION_SUBSYSTEMS: Final[Mapping[str, str]] = {
    "sl_invoice_post": "sales",
    "sl_cash_post": "sales",
    "pl_order_post": "purchase",
    "pl_payment_post": "purchase",
}

# The same four subsystems as an ORDERED sequence, which is the fact that matters: two
# Sales dispatches then two Purchase dispatches. It is why the file's own `subsystem` is
# the empty scalar, and it is what makes Q-CLI-OVERREWRITE-SECOND-LEG live here - each
# menu is entered twice in one run.
EXPECTED_SUBSYSTEM_SEQUENCE: Final[tuple[str, str, str, str]] = (
    "sales",
    "sales",
    "purchase",
    "purchase",
)

# The COBOL menu paragraph each operation drives, for a failure message that places a
# finding in the frozen source. `sl_invoice_post` IS load07: [sales/sales.cbl:L756]
# carries `*> Sales trans posting`, while `load08.` at [sales/sales.cbl:L770]
# dispatches the OUT-OF-SCOPE sl080 (Payment Input).
OPERATION_MENU_PARAGRAPHS: Final[Mapping[str, str]] = {
    "sl_invoice_post": "sales/sales.cbl load07. L756-L768",
    "sl_cash_post": "sales/sales.cbl load11. L792-L796",
    "pl_order_post": "purchase/purchase.cbl load08. L752-L762",
    "pl_payment_post": "purchase/purchase.cbl load12. L786-L790",
}

# The process status each operation is declared to end with, POSITIONALLY. Four zeros,
# and provable rather than hopeful - see the docstring's term-code paragraph.
EXPECTED_STATUS: Final[tuple[int, int, int, int]] = (0, 0, 0, 0)

# The scenario keys this file reads. The clock and system values are published both
# grouped and flat, because the oracle-side runner reads TOP-LEVEL KEYS ONLY; the pairs
# must always agree and are asserted to.
KEY_NAME: Final[str] = "name"
KEY_SUBSYSTEM: Final[str] = "subsystem"
KEY_OPERATION: Final[str] = "operation"
KEY_OPERATIONS: Final[str] = "operations"
KEY_EXPECTED_STATUS: Final[str] = "expected_status"
KEY_CLOCK: Final[str] = "clock"
KEY_CLOCK_TO_DAY: Final[str] = "to_day"
KEY_CLOCK_RUN_DATE: Final[str] = "run_date"
KEY_RUN_DATE_TEXT: Final[str] = "run_date_text"
KEY_RUN_DATE_BINARY: Final[str] = "run_date_binary"
KEY_SYSTEM: Final[str] = "system"
KEY_DATE_FORM: Final[str] = "date_form"
KEY_IRS_INSTEAD: Final[str] = "irs_instead"
KEY_SEED: Final[str] = "seed"
KEY_SEED_FILES_NESTED: Final[str] = "files"
KEY_SEED_FILES: Final[str] = "seed_files"
KEY_AFFECTED_TABLES: Final[str] = "affected_tables"

# The system-record keys the scenario pins, inside its `system:` block.
SYS_FILE_SYSTEM_USED: Final[str] = "file_system_used"
SYS_CYCLEA: Final[str] = "cyclea"
SYS_PERIOD: Final[str] = "period"
SYS_DATE_FORM: Final[str] = "date_form"
SYS_IRS_INSTEAD: Final[str] = "irs_instead"
SYS_S_FLAG_P: Final[str] = "s_flag_p"
SYS_P_FLAG_P: Final[str] = "p_flag_p"


# ---------------------------------------------------------------------------
#  SECTION 2  -  THE PROMOTED ANSWER
# ---------------------------------------------------------------------------

# The ONE promoted interactive answer, covering BOTH cash routes. The key is SEMANTIC
# and is deliberately not a copy of any command-line option spelling:
# `harness/run_python_scenario.sh` owns the translation and probes each module's
# `--help` for the option it needs, failing as a harness fault if it is absent.
ANSWER_KEY_PAYMENT_CONFIRM: Final[str] = "payment_post_confirm"

# The literal, and it must be exactly this. [sales/sl100.cbl:L318-L319] and
# [purchase/pl100.cbl:L310-L311] send anything but "YES" back to `acpt-xrply.`, and
# [sales/sl100.cbl:L316-L317], [purchase/pl100.cbl:L308-L309] send "NO" to
# `menu-exit` before the first file is opened. There is NO third answer and no default:
# each program blanks the reply immediately before accepting it
# [sales/sl100.cbl:L313], [purchase/pl100.cbl:L305], so a blank loops for ever on a
# terminal. That is ambiguity Q-CLI-OKTOPOST, resolved by requiring the answer.
ANSWER_PAYMENT_CONFIRM: Final[str] = "YES"

# The two operations the answer gates, and the two it does not. The invoice and order
# routes promote NOTHING: sl055 and sl060 have only diagnostic acknowledgements, and
# pl060's own confirmation prompt is entirely commented out
# [purchase/pl060.cbl:L362-L370].
ANSWERED_OPERATIONS: Final[tuple[str, str]] = ("sl_cash_post", "pl_payment_post")
UNANSWERED_OPERATIONS: Final[tuple[str, str]] = ("sl_invoice_post", "pl_order_post")

# The answer keys of the OTHER routes, which must be absent because none of their
# routes is on this path: the transfer-file clear belongs to the IRS route, and the
# three end-of-cycle answers belong to the operation this scenario deliberately omits.
# Leaving them unstated is what keeps this scenario's inputs exactly the inputs the
# frozen cycle takes.
ABSENT_ANSWER_KEYS: Final[tuple[str, str, str, str]] = (
    "irs_clear_postings",
    "gl080_proceed",
    "disk_change_option",
    "archive_path_override",
)


# ---------------------------------------------------------------------------
#  SECTION 3  -  THE PINS
# ---------------------------------------------------------------------------

# THE PROJECT-WIDE PINNED RUN DATE, restated as the two literals the folder
# specification names so that the precondition tests can assert them without importing
# `tests/conftest.py` - the house convention across `tests/arithmetic/` and
# `tests/determinism/` is that conftest is reached through FIXTURES and never imported.
# These are not a second authority that could drift unnoticed: every use below
# cross-checks them against BOTH the `pinned_clock` fixture and the scenario's own
# declared pair, so a divergence between the three fails loudly (R-4). The binary
# observable is `Run-Date` [copybooks/wssystem.cob:L67] `05 Run-Date binary-long.`
PINNED_TO_DAY: Final[str] = "21/09/2025"
PINNED_RUN_DATE: Final[int] = 155127

# The date presentation form the scenario pins. 1 is UK dd/mm/yyyy, and the text above
# is passed through unchanged - its digits are never reordered to match the form.
DATE_FORM_UK: Final[int] = 1

# THE FALSE-PASS TRAP. `File-System-Used pic 9` with `88 FS-Cobol-Files-Used value
# zero` and `88 FS-MySql-Used value 1` [copybooks/wssystem.cob:L112-L114]. With ZERO
# the handlers never touch MySQL - the pattern is visible at
# [common/acas007.cbl:L316-L320] - so BOTH dumps come back empty, the trees agree and
# the diff exits 0: A SILENT FALSE PASS that proves nothing whatever. It must be 1.
# It has a second significance in this scenario: 1 also makes `FS-Cobol-Files-Used`
# False, which is exactly why the guarded print blocks at [sales/sl060.cbl:L695] and
# [purchase/pl060.cbl:L623] do not run while their unconditional totals adds at
# [sales/sl060.cbl:L700] and [purchase/pl060.cbl:L628] still do.
FILE_SYSTEM_USED_MYSQL: Final[int] = 1

# THE FAN-OUT SWITCH, [copybooks/wssystem.cob:L179-L181] verbatim:
#     179       05  IRS-Instead     pic x.
#     180           88  IRS-Used                   value "Y".
#     181           88  IRS-Both-Used              value "B".   *> 26/11/16
# THREE states, and the third has NO CONDITION NAME AT ALL - both predicates are simply
# False for a space, which is General Ledger only. Agent Action Plan section 0.6.4:
# "leaving it at a default would make the affected-table list ambiguous", so it is
# pinned explicitly. THE PIN IS LOAD-BEARING FOR THE AFFECTED-TABLE LIST: in pure
# General Ledger mode `GLBATCH-REC` and `GLPOSTING-REC` are written and
# `PSIRSPOST-REC` is only opened and closed, whereas under "Y" or "B" the fan-out
# would change which tables move. It is tested at three sites in each of the four
# Sales and Purchase posting programs - for example [sales/sl060.cbl:L1039],
# [sales/sl060.cbl:L1126] and [sales/sl060.cbl:L1175]. A YAML space reaches the CLI
# as the LITERAL SPACE `--irs-instead ' '` - no `N` token exists - so the column
# stores a space, and normalisation's first job trims it identically on both sides.
IRS_INSTEAD_GL_ONLY: Final[str] = " "

# The two one-shot posting latches, `S-Flag-P` [copybooks/wssystem.cob:L226] and
# `P-Flag-P` [copybooks/wssystem.cob:L206]. Both must be 2 in the seeded record or
# operations 2 and 4 post NOTHING [sales/sl100.cbl:L296-L301],
# [purchase/pl100.cbl:L289-L294], and both are CLEARED BY THE RUN
# [sales/sl100.cbl:L474], [purchase/pl100.cbl:L465].
FLAG_P_POSTING_READY: Final[int] = 2

# The accounting cycle. `Cyclea binary-char` [copybooks/wssystem.cob:L62], redefined as
# `Scycle` at L63. A zero cycle diverts the menu to system setup
# [general/general.cbl:L462-L463], which on a headless runner is a hang rather than an
# error, so it must be non-zero.
CYCLEA_MUST_BE_NON_ZERO: Final[int] = 0

# The accounting period, `Period binary-char` [copybooks/wssystem.cob:L64]. INERT in
# every scenario, because the only in-scope program that divides by it is gl080
# [general/gl080.cbl:L328] and `gl_end_of_cycle` is deliberately driven by none of the
# eight. Carried because it is part of the seeded system record and because the key set
# is uniform.
PERIOD_INERT_VALUE: Final[int] = 1


# ---------------------------------------------------------------------------
#  SECTION 4  -  THE BOUND, AND THE SEED
#
#  THE AFFECTED-TABLE LIST IS THE ONLY BOUNDING MECHANISM. There is no ignore-list, no
#  tolerance-list and no "known difference" allowance in this file or in the diff path
#  it drives. The 22-table in-scope inventory and every primary key are NOT restated
#  here - they have exactly one definition in this repository, in
#  `harness/dump_tables.py`, reached through the `in_scope_table_names` fixture.
# ---------------------------------------------------------------------------

# FIFTEEN tables, alphabetical, and the order is load-bearing: the seed fingerprint is
# written in declared order and a disagreement is a HARNESS FAULT.
#
# SYSTEM-REC IS THE FIFTEENTH, and in this scenario it earns its place more than
# anywhere else: FOUR operations run in sequence, each mutating the system record in
# memory - anomaly A-17's move [sales/sl060.cbl:L1173] among them - and each trading
# menu persists it on exit [sales/sales.cbl:L628-L657],
# [purchase/purchase.cbl:L621-L651], which the headless routes reproduce as
# args.overrewrite. Four sequential mutations are exactly the shape in which a lost or
# a doubled update hides, and it can only be observed if the table is compared.
# Measured byte-identical on both sides rather than presumed to diverge (rule R-6).
AFFECTED_TABLES: Final[tuple[str, ...]] = (
    "ANALYSIS-REC",
    "GLBATCH-REC",
    "GLPOSTING-REC",
    "PSIRSPOST-REC",
    "PUINV-LINES-REC",
    "PUINVOICE-REC",
    "PUITM5-REC",
    "PULEDGER-REC",
    "SAINV-LINES-REC",
    "SAINVOICE-REC",
    "SAITM3-REC",
    "SALEDGER-REC",
    "SYSTEM-REC",
    "SYSTOT-REC",
    "VALUEANAL-REC",
)

# The tables this scenario's `seed_files:` fill, and which must therefore come back
# WITH ROWS on both sides. Named here because the non-vacuity guard in the fixture and
# the three site tests below both depend on the same claim. GLBATCH-REC, GLPOSTING-REC
# and PSIRSPOST-REC are absent deliberately - see GUARD 5 in the fixture.
SEEDED_TABLES: Final[tuple[str, ...]] = (
    "ANALYSIS-REC",
    "PUINV-LINES-REC",
    "PUINVOICE-REC",
    "PUITM5-REC",
    "PULEDGER-REC",
    "SAINV-LINES-REC",
    "SAINVOICE-REC",
    "SAITM3-REC",
    "SALEDGER-REC",
    "SYSTOT-REC",
    "VALUEANAL-REC",
)

# THE FOCAL TABLE, in scope here and on no other scenario's list. 21 columns, primary
# key `LEDGER-TOTALS-REC-KEY`, declared at [mysql/ACASDB.sql:L1376-L1398], laid out by
# [copybooks/wssys4.cob] and loaded by `sys4LD` [common/masterLD.sh:L51-L87].
FOCAL_TABLE: Final[str] = "SYSTOT-REC"

# Why each table is on the list, quoted verbatim into the failure message so that a
# reader who has to remove or add one has the reason in front of them.
TABLE_REASONS: Final[Mapping[str, str]] = {
    "ANALYSIS-REC": (
        "the deduction analysis - site 3 adds unconditionally "
        "[sales/sl060.cbl:L641]"
    ),
    "GLBATCH-REC": (
        "the Sales and Purchase posting programs write General Ledger batches in "
        "pure General Ledger mode"
    ),
    "GLPOSTING-REC": (
        "the same programs write General Ledger postings in pure General Ledger mode"
    ),
    "PSIRSPOST-REC": (
        "the fan-out path opens and closes the transfer file even in pure General "
        "Ledger mode, and A-1 [sales/sl060.cbl:L1176] means sl060 does NOT close it"
    ),
    "PUINV-LINES-REC": "pl055 stamps the header status [purchase/pl055.cbl:L586-L587]",
    "PUINVOICE-REC": "pl055 stamps the header status [purchase/pl055.cbl:L586-L587]",
    "PUITM5-REC": (
        "pl100 walks and rewrites the open items [purchase/pl100.cbl:L404-L405]"
    ),
    "PULEDGER-REC": (
        "the posting programs rewrite supplier statistics, where A-8, A-9 and A-10 land"
    ),
    "SAINV-LINES-REC": "sl055 stamps the header status [sales/sl055.cbl:L679-L681]",
    "SAINVOICE-REC": (
        "sl055 stamps TWO status fields [sales/sl055.cbl:L679-L681], where pl055 "
        "stamps one"
    ),
    "SAITM3-REC": "sl100 walks and rewrites the open items [sales/sl100.cbl:L412-L413]",
    "SALEDGER-REC": (
        "the posting programs rewrite customer statistics, where A-8, A-9 and A-10 "
        "land, and it carries the one date-text column job 3 touches here"
    ),
    "SYSTOT-REC": (
        "THE FOCAL TABLE - the nine period-total write sites are its sole writers "
        "(Agent Action Plan section 0.6.4), which is what makes this scenario "
        "verifiable by inspecting one table"
    ),
    "VALUEANAL-REC": (
        "the value file is opened, analysed and closed when total-deduct is non-zero "
        "[sales/sl060.cbl:L643-L647]"
    ),
}

# NINE flat files, and no others. Asserted by EXACT TUPLE EQUALITY, which proves the
# absence of the eight forbidden names of the same frozen contract without naming any
# of them - see the docstring, which names them by locator as the scenario file does.
SEED_FILES: Final[tuple[str, ...]] = (
    "system.dat",
    "analysis.dat",
    "value.dat",
    "salesled.dat",
    "invoice.dat",
    "openitm3.dat",
    "purchled.dat",
    "pinvoice.dat",
    "openitm5.dat",
)

# `system.dat` is effectively mandatory rather than merely useful: without a system
# record the menu calls the parameter-setup program INTERACTIVELY
# [general/general.cbl:L385-L394], which on a headless runner is a hang rather than an
# error. It is also what carries `Run-Date` [copybooks/wssystem.cob:L67], the fan-out
# switch [copybooks/wssystem.cob:L179-L181] and both posting latches.
SEED_FILE_SYSTEM: Final[str] = "system.dat"


# ---------------------------------------------------------------------------
#  SECTION 5  -  THE NINE PERIOD-TOTAL WRITE SITES
#
#  Each entry is (site number, locator, target field, guard), and every locator was
#  read out of the frozen source in this checkout rather than copied from a plan (R-5).
#  The table is data for the failure messages: NOTHING HERE RECOMPUTES A TOTAL, and no
#  assertion below predicts a figure. The observable is agreement between the two
#  sides, and the compiled run is the arbiter (R-6).
# ---------------------------------------------------------------------------

PERIOD_TOTAL_WRITE_SITES: Final[tuple[tuple[int, str, str, str], ...]] = (
    (
        1,
        "sales/sl055.cbl:L675",
        "sl-invoices-this-month",
        "if ih-type = 2 [sales/sl055.cbl:L674]",
    ),
    (
        2,
        "sales/sl055.cbl:L677",
        "sl-credit-notes-this-month",
        "if ih-type = 3 [sales/sl055.cbl:L676]",
    ),
    (
        3,
        "sales/sl060.cbl:L641",
        "sl-credit-deductions",
        "UNCONDITIONAL",
    ),
    (
        4,
        "sales/sl060.cbl:L700",
        "sl-cn-unappl-this-month",
        "UNCONDITIONAL, and OUTSIDE the guard at [sales/sl060.cbl:L695]",
    ),
    (
        5,
        "sales/sl100.cbl:L404",
        "t-paid AND sl-payments - TWO RECEIVERS IN ONE ADD",
        "if oi-type = 5 [sales/sl100.cbl:L402], else oi-type = 6 at L407-L410",
    ),
    (
        6,
        "purchase/pl055.cbl:L582",
        "pl-invoices-this-month",
        "if ih-type = 2 [purchase/pl055.cbl:L581]",
    ),
    (
        7,
        "purchase/pl055.cbl:L584",
        "pl-credit-notes-this-month",
        "if ih-type = 3 [purchase/pl055.cbl:L583]",
    ),
    (
        8,
        "purchase/pl060.cbl:L628",
        "pl-cn-unappl-this-month",
        "UNCONDITIONAL, and OUTSIDE the guard at [purchase/pl060.cbl:L623]",
    ),
    (
        9,
        "purchase/pl100.cbl:L396",
        "t-paid AND pl-payments - TWO RECEIVERS IN ONE ADD",
        "if oi-type = 5 [purchase/pl100.cbl:L394], else oi-type = 6 at L399-L402",
    ),
)

# The two sites whose add sits OUTSIDE the guarded print block immediately above it -
# almost certainly not what the author intended, and the specification (R-4). They are
# reproduced and NEVER aligned with their guards.
UNCONDITIONAL_TOTAL_SITES: Final[tuple[int, int]] = (4, 8)

# The two sites that accumulate into TWO receivers in ONE `ADD`. Neither is split,
# reordered or normalised (R-4).
TWO_RECEIVER_TOTAL_SITES: Final[tuple[int, int]] = (5, 9)

# The sites each operation reaches, which is how the coverage claim in the latch
# precondition's failure message is DERIVED rather than asserted: without the two
# latches, operations 2 and 4 post nothing and exactly sites 5 and 9 are lost, leaving
# seven of nine.
SITES_BY_OPERATION: Final[Mapping[str, tuple[int, ...]]] = {
    "sl_invoice_post": (1, 2, 3, 4),
    "sl_cash_post": (5,),
    "pl_order_post": (6, 7, 8),
    "pl_payment_post": (9,),
}


# ---------------------------------------------------------------------------
#  SECTION 6  -  THE REGISTER IDENTIFIERS THIS FILE CITES  (rules R-5 and R-6)
#
#  NONE OF THEM IS INVENTED HERE. Each is drawn from the existing register, which the
#  numeric form spells `Q-<n>` (`acas_posting/dictionary/model.py`'s
#  `AMBIGUITY_REF_PATTERN`) and the descriptive form `Q-<SCOPE>-<NAME>`. They are
#  TEXTUAL REFERENCES ONLY: nothing below imports the documents, checks that they
#  exist, or skips because they do not.
# ---------------------------------------------------------------------------

# THE MOST IMPORTANT ONE IN THIS FILE. `SYSTOT-REC` is written by the nine in-scope
# sites AND persisted by the menu shell's exit path, which a bare command line has no
# equivalent of. SETTLED on the two Sales routes and on `pl_order_post`'s `< 8` branch
# by REPRODUCING the paragraph - `acas_posting/cli/args.py`'s `slpl_menu_state` carries
# the totals record and `args.overrewrite` is performed from both arms of `load000` -
# and still OPEN on `pl_payment_post` for which of pl100's writes reach a table.
AMBIGUITY_SYSTOT_OVERLAP: Final[str] = "Q-CLI-OVERREWRITE"

# STILL OPEN, and specific to this scenario: the omitted half of the COBOL paragraph
# zeroes `File-System-Used` and never restores it, so a SECOND dispatch in one session
# would take the indexed leg under a literal reading. This is the only scenario that is
# two dispatches per menu, so it is the run that measures which leg the oracle takes.
AMBIGUITY_SECOND_LEG: Final[str] = "Q-CLI-OVERREWRITE-SECOND-LEG"

# The promoted payment confirmation. RESOLVED: the answer is required, because the
# frozen programs have no defaultable reply.
AMBIGUITY_PAYMENT_CONFIRM: Final[str] = "Q-CLI-OKTOPOST"

# The term-code-to-process-status mapping, settled in `args.exit_status_for` as the
# identity and not re-decided here.
AMBIGUITY_EXIT_STATUS: Final[str] = "Q-CLI-EXITSTATUS"

# The three system columns re-pinned from the command line over the loaded row - what
# remains of the overlap question after the paragraph itself was reproduced.
AMBIGUITY_SYSREC_PINS: Final[str] = "Q-CLI-SYSREC-PINS"

# A-17's stored value. The unexplained `move RRN to postings. *> Why ?`
# [sales/sl060.cbl:L1173] is READ BACK by a later operation of this very sequence
# [purchase/pl100.cbl:L564], which is one of the reasons the operation order is part of
# the specification.
AMBIGUITY_A17_EFFECT: Final[str] = "Q-A17-POSTINGS-EFFECT"

# A-2's unbounded quarter subscript, locked in
# `tests/arithmetic/test_gl080_cycle_divide_rounded.py` and NOT exercised here.
# Both identifiers are SETTLED rather than open: the compiled oracle was measured and
# an out-of-record store writes past the record without touching any column of any
# compared table. They are still named, because a reader tracing A-2 through the
# register needs the identifiers that carry the measurement.
AMBIGUITY_QUARTER_SUBSCRIPT: Final[tuple[str, str]] = ("Q-19", "Q-QUARTER-SUBSCRIPT")

# The register and the evidence documents, by path, for a failure message that tells a
# reader where to record what they found. NEVER opened, never asserted to exist.
DOC_AMBIGUITIES: Final[str] = "docs/migration/ambiguity-resolutions.md"
DOC_ANOMALIES: Final[str] = "docs/migration/anomaly-log.md"
DOC_EVIDENCE: Final[str] = "docs/migration/scenario-diff-evidence.md"


# ---------------------------------------------------------------------------
#  SECTION 7  -  READING THE SCENARIO, AND READING A VERDICT
#
#  Small, pure helpers. None of them interprets a declaration or judges it - judging a
#  scenario's declared contents would be exactly the added validation R-3 forbids - and
#  none of them reimplements a protocol stage.
# ---------------------------------------------------------------------------


def _block(definition: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    """Return one grouped block of a scenario definition.

    Args:
        definition: The parsed scenario mapping.
        key: The block's key - `clock`, `system` or `seed`.

    Returns:
        The block.

    Raises:
        AssertionError: The key is absent or is not a mapping. The scenario files
            publish these blocks as the documented shape, so either is a malformed
            definition rather than a behavioural finding.
    """
    block = definition.get(key)
    assert isinstance(block, Mapping), (
        f"{SCENARIO}: the `{key}:` block is absent or is not a mapping "
        f"(got {type(block).__name__}). The nine scenario definitions publish "
        f"`clock:`, `system:` and `seed:` as mappings, with flat mirrors of the values "
        f"the oracle-side runner reads, because that runner accepts TOP-LEVEL KEYS "
        f"ONLY."
    )
    return block


def _sequence(definition: Mapping[str, Any], key: str) -> tuple[Any, ...]:
    """Return one sequence-valued key of a scenario definition, as a tuple.

    Args:
        definition: The parsed scenario mapping.
        key: The key - `operations`, `expected_status`, `seed_files` or
            `affected_tables`.

    Returns:
        The values, in the order the file declares them. DECLARED ORDER IS PRESERVED
        and never sorted: the affected-table order bounds the report and the seed
        fingerprint is written in it.

    Raises:
        AssertionError: The key is absent or is not a list.
    """
    value = definition.get(key)
    assert isinstance(value, list), (
        f"{SCENARIO}: `{key}:` is absent or is not a list "
        f"(got {type(value).__name__})."
    )
    return tuple(value)


def _table_diff(run: Any, table: str) -> Any:
    """Return one table's `TableDiff` out of a completed parity run.

    Args:
        run: The `ParityRun` the `parity` fixture produced.
        table: The table name, spelled as `mysql/ACASDB.sql` spells it.

    Returns:
        The `TableDiff` for that table, whose `is_empty` is the per-table verdict.

    Raises:
        AssertionError: The comparison holds no entry for the table. That is not a
            behavioural finding but a bounding fault: the comparison is bounded by the
            scenario's affected-table list, so every listed table is compared and a
            missing entry means the bound and the report disagree.
    """
    for candidate in run.tree.tables:
        if candidate.table == table:
            return candidate
    compared = ", ".join(candidate.table for candidate in run.tree.tables) or "none"
    raise AssertionError(
        f"{SCENARIO}: the comparison holds no entry for `{table}`, so the bound and "
        f"the report disagree. The comparison is bounded by the scenario's "
        f"`affected_tables:` list, inside a comparison bounded by all 22 in-scope "
        f"tables - there is no ignore-list and no "
        f"tolerance anywhere in the diff path - so every listed table is compared. "
        f"Compared: {compared}."
    )


#: The `SYSTOT-REC` column each of the nine write sites accumulates into, spelled as
#: [mysql/ACASDB.sql:L1378-L1397] spells it. THE OBSERVABLE PER SITE: the sites live in
#: the frozen COBOL and cannot be watched directly, but every one of them lands in
#: exactly one of these columns, so reading the column IS reading the site's effect.
SITE_COLUMNS: Final[Mapping[int, str]] = {
    1: "SL-INVOICES-THIS-MONTH",
    2: "SL-CREDIT-NOTES-THIS-MONTH",
    3: "SL-CREDIT-DEDUCTIONS",
    4: "SL-CN-UNAPPL-THIS-MONTH",
    5: "SL-PAYMENTS",
    6: "PL-INVOICES-THIS-MONTH",
    7: "PL-CREDIT-NOTES-THIS-MONTH",
    8: "PL-CN-UNAPPL-THIS-MONTH",
    9: "PL-PAYMENTS",
}

#: The two `SYSTEM-REC` columns the one-shot posting latches occupy, and the value a
#: cleared latch holds. [sales/sl100.cbl:L474] `move zero to S-Flag-P.` and
#: [purchase/pl100.cbl:L465] `move zero to P-Flag-P.`, reproduced in
#: acas_posting/programs/sl100_cash_posting.py and pl100_payment_posting.py, and
#: persisted by `overrewrite`'s key-1 `System-Rewrite`
#: [general/general.cbl:L656-L663].
LATCH_COLUMNS: Final[tuple[str, str]] = ("S-FLAG-P", "P-FLAG-P")
LATCH_CLEARED: Final[int] = 0
SYSTEM_TABLE: Final[str] = "SYSTEM-REC"
SYSTEM_RECORD_KEY: Final[int] = 1

#: The marker both runners print in their post-run assertion stage, one line per latch
#: column, read from the database in the seconds after the operation and printed into
#: THAT run's captured stream. See `_latches_from` for why the value is taken from the
#: capture rather than from a later query against the shared database - and for why the
#: ORACLE capture of this multi-operation scenario carries one pair PER OPERATION while
#: the Python capture carries exactly one, so the LAST pair is the final state.
LATCH_MARKER: Final[str] = "ONE-SHOT-LATCH"
LATCH_MARKER_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^\s*ONE-SHOT-LATCH\s+(?P<column>[A-Z0-9-]+)\s*=\s*(?P<value>\S*)\s*$",
    re.MULTILINE,
)


def _latches_from(
    side: str, captured: str, *, expected_emissions: int
) -> Mapping[str, str]:
    """Return one side's FINAL post-run latch values, read out of its OWN captured stream.

    WHY NOT A QUERY, AND WHY NOT THE DUMP. The dump of `SYSTEM-REC` is a comparison
    artifact written under the diff tree and consumed by the diff stage; a test that wants
    ONE latch value as a number, attributable to ONE side of ONE operation, is asking a
    different question. An earlier form of the latch assertion opened a connection and
    queried the live database when the TEST
    ran. Three things make that value untrustworthy as evidence about this run: the
    protocol's own stage 5 drops, re-applies the frozen schema and re-seeds between the
    two sides, so the oracle's latch values were already gone; the `parity` fixture is
    CACHED, so the query could execute an arbitrary time after the run it claims to
    describe; and every scenario in the suite shares one database, so another
    scenario's reset could have replaced the row entirely. The assertion could pass on
    a freshly seeded row - or fail on one - with no relation to what this scenario did.

    Both runners now read the two columns in their post-run assertion stage and print
    `ONE-SHOT-LATCH <column> = <value>`. A capture is frozen evidence attributable to
    exactly one side of exactly one run, which is what this test needs; and because a
    read failure there increments the runner's own failure counter and drives its exit
    status non-zero, an ABSENT marker is a harness fault the `parity` fixture has
    already raised on rather than a silent gap here.

    ⭐ THE TWO SIDES EMIT A DIFFERENT NUMBER OF MARKERS, AND THAT IS THE PROTOCOL.
    This is the one multi-operation scenario, and it spans TWO menu executables, so
    `tests/conftest.py` drives the oracle as a SEQUENCE of separate
    `run_cobol_scenario.sh` invocations over the declared list while driving Python as
    ONE invocation over the same list. Each oracle invocation runs its own post-run
    assertion stage, so the concatenated oracle capture carries one marker pair PER
    OPERATION and the Python capture carries exactly one pair.

    So the LAST pair on each side is the one that describes the final state, and that
    is what this returns. The intermediate oracle pairs are not noise - they are the
    per-operation history, and reading them as the answer would assert against the
    state after operation 1, where the latches are still SET: only operations 2 and 4
    clear them, at [sales/sl100.cbl:L474] and [purchase/pl100.cbl:L465]. An earlier
    form of this helper asserted that each column appeared exactly ONCE, which was
    true of the single-operation scenarios it was first written against and false here.

    THE COUNT IS ASSERTED RATHER THAN IGNORED, which turns the multiplicity from a
    thing to tolerate into positive evidence: the number of pairs must equal the number
    of operations that side actually REPORTED, so a sequence that stopped early, or a
    Python run that somehow re-entered its post-run stage, is caught here.

    Args:
        side: `cobol` or `python`, for the failure message.
        captured: That side's run-stage stdout, verbatim.
        expected_emissions: How many post-run assertion stages that side should have
            run - the number of operations it reported. One per oracle invocation, and
            one in total for the single Python invocation.

    Returns:
        Column name to the value the runner observed LAST, as text.

    Raises:
        AssertionError: A latch marker is missing, or the number of emissions does not
            match the number of operations the side reported.
    """
    history: dict[str, list[str]] = {}
    for match in LATCH_MARKER_PATTERN.finditer(captured):
        history.setdefault(match.group("column"), []).append(match.group("value"))

    for column in LATCH_COLUMNS:
        assert column in history, (
            f"the {side} capture carries no {LATCH_MARKER} line for {column!r}. Both "
            f"runners read `S-FLAG-P` and `P-FLAG-P` in their post-run assertion stage "
            f"and print one marker each; a missing marker means the read failed, which "
            f"also increments the runner's failure count, so this is a HARNESS FAULT "
            f"and not a latch that was left set."
        )
        assert len(history[column]) == expected_emissions, (
            f"the {side} capture prints {LATCH_MARKER} for {column!r} "
            f"{len(history[column])} time(s) but that side reported "
            f"{expected_emissions} operation(s): {history[column]!r}.\n"
            f"  Each post-run assertion stage emits exactly one marker per column, and "
            f"the oracle side of this scenario runs one such stage PER OPERATION "
            f"because it is driven as a sequence of invocations. A mismatch means the "
            f"sequence stopped early, or a stage ran twice, and it is then no longer "
            f"clear which operation each value follows."
        )

    return {column: history[column][-1] for column in LATCH_COLUMNS}


def _systot_projection(
    run: Any, protocol: Any, columns: Sequence[str]
) -> tuple[Mapping[str, Mapping[Any, Any]], Mapping[str, Mapping[Any, Any]]]:
    """Project named `SYSTOT-REC` columns from BOTH normalised captures.

    THIS IS WHAT GIVES EACH SITE TEST AN OBSERVABLE OF ITS OWN. A per-table `is_empty`
    restates the headline verdict; reading the column a site accumulates into is
    evidence about that site - and it cannot pass over an absent row, because the row
    count is asserted first.

    NO FIGURE IS PREDICTED (R-6). Which value the two sides agree on is the compiled
    oracle's to decide; this returns both projections so the caller can require only
    that they agree.

    Args:
        run: The completed `ParityRun`.
        protocol: The protocol bundle, for the dump reader and the side labels.
        columns: The columns to project.

    Returns:
        `(cobol, python)`, each `{column: {primary-key value: stored value}}`.

    Raises:
        AssertionError: The focal table is empty on either side, the column lists
            disagree, the primary keys disagree, or a column is absent from a capture.
    """
    cobol_side, python_side = protocol.vocabulary.sides
    dumps = {}
    for side in (cobol_side, python_side):
        path = run.paths.normalized_dir(side) / f"{FOCAL_TABLE}.json"
        dump = protocol.read_dump(path)
        assert int(dump["row_count"]) > 0, (
            f"{SCENARIO}: `{FOCAL_TABLE}` is EMPTY on the {side} side, so every "
            f"period-total claim in this file would agree about NOTHING. The totals "
            f"record is seeded by `sys4LD` from system.dat "
            f"[common/masterLD.sh:L51-L87] and only ever REWRITTEN by the nine sites, "
            f"so an absent row means the seed never landed or the run never reached "
            f"MySQL - `system.file_system_used` must be "
            f"{FILE_SYSTEM_USED_MYSQL} [copybooks/wssystem.cob:L112-L114]."
        )
        dumps[side] = dump

    assert list(dumps[cobol_side]["columns"]) == list(dumps[python_side]["columns"]), (
        f"{SCENARIO}: `{FOCAL_TABLE}`'s column lists disagree - "
        f"{list(dumps[cobol_side]['columns'])} against "
        f"{list(dumps[python_side]['columns'])}. Rows are POSITIONAL within a dump, so "
        f"nothing projected from them would align."
    )

    projections: list[dict[str, dict[Any, Any]]] = []
    for side in (cobol_side, python_side):
        dump = dumps[side]
        names = list(dump["columns"])
        key_index = names.index(str(dump["primary_key"]))
        projection: dict[str, dict[Any, Any]] = {}
        for column in columns:
            assert column in names, (
                f"{SCENARIO}: `{FOCAL_TABLE}` carries no column named {column!r} on "
                f"the {side} side; it lists {names}. mysql/ACASDB.sql is FROZEN, so "
                f"this means the dump or the checkout is wrong."
            )
            index = names.index(column)
            projection[column] = {
                row[key_index]: row[index] for row in dump["rows"]
            }
        projections.append(projection)

    assert projections[0].keys() == projections[1].keys()
    for column in columns:
        only_in_cobol = set(projections[0][column]) - set(projections[1][column])
        only_in_python = set(projections[1][column]) - set(projections[0][column])
        assert set(projections[0][column]) == set(projections[1][column]), (
            f"{SCENARIO}: `{FOCAL_TABLE}`'s primary keys disagree while projecting "
            f"{column!r}: only on {cobol_side} "
            f"{sorted(only_in_cobol, key=repr)}; "
            f"only on {python_side} "
            f"{sorted(only_in_python, key=repr)}."
        )
    return projections[0], projections[1]


def _assert_sites_agree(
    run: Any, protocol: Any, sites: Sequence[int]
) -> Mapping[str, Mapping[Any, Any]]:
    """Require the named sites' receiving columns to AGREE between the two sides.

    Args:
        run: The completed `ParityRun`.
        protocol: The protocol bundle.
        sites: The write-site numbers, keys of `SITE_COLUMNS`.

    Returns:
        The oracle-side projection, so a caller can report the values it agreed on.

    Raises:
        AssertionError: A projected column differs, or the row is absent.
    """
    columns = tuple(SITE_COLUMNS[site] for site in sites)
    cobol, python = _systot_projection(run, protocol, columns)
    for site, column in zip(sites, columns, strict=True):
        locator = next(
            entry[1] for entry in PERIOD_TOTAL_WRITE_SITES if entry[0] == site
        )
        assert cobol[column] == python[column], (
            f"{SCENARIO}: `{FOCAL_TABLE}`.`{column}` - the receiver of write site "
            f"{site} [{locator}] - disagrees between the two sides:\n"
            f"  cobol : {sorted(cobol[column].items(), key=repr)}\n"
            f"  python: {sorted(python[column].items(), key=repr)}\n"
            f"  NO FIGURE IS PREDICTED HERE. The two sides must agree; which value "
            f"they agree ON is the oracle's to decide (R-6). Do NOT 'correct' a total "
            f"and do NOT add an allowance - record the finding in {DOC_EVIDENCE} and "
            f"arbitrate it against the compiled run."
        )
    return cobol


def _verdict(run: Any, harness_modules: Any, *, bearing: str = "") -> str:
    """Render a completed parity run as a failure message.

    Args:
        run: The `ParityRun`.
        harness_modules: The `harness` fixture's three loaded modules. `render` is
            `harness/diff_states.py`'s own deterministic renderer, and it returns THE
            EMPTY STRING when the two trees are identical, which is the same zero-byte
            report a passing stage 10 writes.
        bearing: What the finding bears on - normally one or more register identifiers -
            appended so a reader knows which recorded question to consult.

    Returns:
        The report, the per-stage transcript and the bearing note, ready to hand to
        `assert`.
    """
    parts = [
        f"{SCENARIO}: the ordering-normalised diff is NOT EMPTY. Agent Action Plan "
        f"section 0.8.5 makes an empty diff the pass condition, and section 0.6.6 "
        f"establishes that the dump is deterministic by construction, so this is a "
        f"REAL BEHAVIOURAL DIFFERENCE and never an artefact of the comparison.",
        f"{run.tree.total_differences} finding(s) across "
        f"{len(run.tables)} bounded table(s).",
        harness_modules.diff_states.render(run.tree),
        run.describe(),
    ]
    if bearing:
        parts.append(bearing)
    parts.append(
        f"Record the finding in {DOC_EVIDENCE}; the anomaly register is "
        f"{DOC_ANOMALIES} and the ambiguity register is {DOC_AMBIGUITIES}. DO NOT "
        f"resolve it with an ignore-list, a tolerance or a 'known difference' "
        f"allowance: a difference here is a signal."
    )
    return "\n".join(part for part in parts if part)


# ---------------------------------------------------------------------------
#  SECTION 8  -  THE EVIDENCE FIXTURE
#
#  THE SPLIT THAT MAKES A FINDING LEGIBLE. Every stage runs in the fixture, so a
#  HARNESS FAULT - a failed seed, a failed reset, a failed dump or normalisation, or a
#  comparison that could not be performed at all - surfaces as a pytest ERROR. What is
#  left in each test body is the VERDICT, so a genuine behavioural difference surfaces
#  as a pytest FAILURE. The two can never be confused, which is the whole point.
#
#  THE TEN-STAGE PROTOCOL RUNS EXACTLY ONCE, and that is a correctness property
#  rather than an economy. Every test below is a view on ONE arbitration, so two of
#  them can never disagree about what the compiled run did - which is precisely what
#  R-6 asks of a tie-breaker. The result is memoised in a plain module-level dict, so
#  that the cache is inspectable and a partially completed run is never left in it;
#  execution is strictly sequential (R-3), so there is no race to guard. The fixture is
#  FUNCTION-SCOPED because `protocol` is, and `protocol` is function-scoped because it
#  applies the stack guard - which is what gives a bare host a precise SKIP instead of
#  an error.
# ---------------------------------------------------------------------------

# One entry, keyed by scenario name. The same pattern `tests/conftest.py` uses for its
# harness-module cache, and for the same reason: a plain dict rather than a decorator,
# so the cache can be read.
_PARITY_MEMO: dict[str, Any] = {}


@pytest.fixture
def parity(
    protocol: Any,
    harness: Any,
    scenario_loader: Callable[[str], Mapping[str, Any]],
    pinned_clock: Any,
) -> Any:
    """Run all ten protocol stages once and hand back the completed `ParityRun`.

    THE TWO GUARDS APPLIED BEFORE ANYTHING RUNS are the two whose violation would make
    the CAPTURE ITSELF untrustworthy rather than merely less informative:

      1. THE PINNED CLOCK. The scenario's declared pair must equal the project's pinned
         pair, in both observables. A one-day shift in the binary `Run-Date`
         [copybooks/wssystem.cob:L67] would surface three tables into a diff looking
         exactly like a posting difference, so it is caught here instead.
      2. THE BOUND. The comparison must be bounded by ALL 22 IN-SCOPE TABLES, which
         is the protocol. The scenario's own `affected_tables:` list is its DECLARED
         EFFECT and is checked separately, as a subset.

    THE COVERAGE-REDUCING PRECONDITIONS ARE DELIBERATELY NOT GUARDED HERE. The two
    `Flag-P` latches and the promoted answer are asserted by their own named tests, so
    that a wrong latch produces a FAILURE naming exactly what was lost rather than an
    ERROR that could mask a real parity difference. That separation is the reason those
    tests exist at all.

    Args:
        protocol: Every protocol stage and both compositions, as one object. Requesting
            it applies the stack guard, so a host without Docker, MariaDB or the built
            oracle gets a precise SKIP naming every missing precondition.
        harness: The three harness Python modules, loaded by explicit file path (R-1).
        scenario_loader: `yaml.safe_load` of one scenario definition. Nothing here opens
            the YAML itself and nothing imports `yaml`.
        pinned_clock: The project-wide pinned run date, as both observables.

    Returns:
        The completed `ParityRun`: every stage result in execution order, both run
        stages' statuses, the stage-10 verdict and the paths of every artifact.

    Raises:
        HarnessFaultError: A stage whose failure destroys the evidence failed - the
            seed, the reset, either dump, either normalisation, or the comparison itself
            with exit 2. The two RUN stages are exempt by design: their status is
            recorded and the dump is taken anyway, because absence is evidence (Agent
            Action Plan section 0.6.5).
        AssertionError: One of the two guards above failed.
    """
    definition = scenario_loader(SCENARIO)

    # GUARD 1 - the pinned clock, in both observables, against BOTH the fixture and this
    # file's restated literals, so that a divergence between the three is impossible to
    # miss (R-4).
    clock = _block(definition, KEY_CLOCK)
    assert (clock[KEY_CLOCK_TO_DAY], clock[KEY_CLOCK_RUN_DATE]) == (
        pinned_clock.to_day,
        pinned_clock.run_date,
    ), (
        f"{SCENARIO}: the declared clock "
        f"({clock[KEY_CLOCK_TO_DAY]!r}, {clock[KEY_CLOCK_RUN_DATE]!r}) does not equal "
        f"the project's pinned pair "
        f"({pinned_clock.to_day!r}, {pinned_clock.run_date!r}). Both observables are "
        f"pinned at the command-line boundary because the twelve in-scope programs "
        f"contain zero clock reads and take the date through linkage; a shift in the "
        f"binary `Run-Date` [copybooks/wssystem.cob:L67] would look like a posting "
        f"difference three tables into the diff."
    )
    assert (pinned_clock.to_day, pinned_clock.run_date) == (
        PINNED_TO_DAY,
        PINNED_RUN_DATE,
    ), (
        f"{SCENARIO}: the `pinned_clock` fixture supplies "
        f"({pinned_clock.to_day!r}, {pinned_clock.run_date!r}) where this file's "
        f"folder specification names ({PINNED_TO_DAY!r}, {PINNED_RUN_DATE!r}). One of "
        f"the two is wrong and neither is authoritative on its own."
    )

    # GUARD 2 - the DECLARED EFFECT. `protocol.affected_tables` delegates the reading
    # and the in-scope check to `harness/dump_tables.py`, so the list is validated
    # exactly once. It is what the runners assert changed or unchanged; it is NOT the
    # comparison bound, which is asserted below.
    declared = protocol.affected_tables(SCENARIO)
    assert declared == AFFECTED_TABLES, (
        f"{SCENARIO}: declares an effect on {declared!r}, where this file expects "
        f"{AFFECTED_TABLES!r}. The order is load-bearing - the seed fingerprint is "
        f"written in declared order and a disagreement is a harness fault. There is "
        f"no ignore-list, no tolerance-list and no 'known difference' allowance "
        f"anywhere in the diff path."
    )

    cached = _PARITY_MEMO.get(SCENARIO)
    if cached is None:
        # STAGES 1 to 8, in order, one at a time, on one database (R-3). The helper
        # raises on every stage whose failure destroys the evidence and records the two
        # run stages' statuses rather than enforcing them.
        cached = protocol.run_scenario_parity(SCENARIO)
        # Memoised only on success, so a half-completed run is never served to a later
        # test as though it were evidence.
        _PARITY_MEMO[SCENARIO] = cached
    run = cached

    #  THE BOUND, asserted on the completed run: ALL 22 IN-SCOPE TABLES, which is the
    #  protocol. This scenario needs it more than any other - `SYSTOT-REC` is its focal
    #  table AND one of the rows the menu's `overrewrite` persists
    #  [general/general.cbl:L656-L672], reproduced on both sides by
    #  `acas_posting/cli/args.py::overrewrite`, so bounding the system rows out would
    #  have hidden exactly the interaction this scenario exists to measure.
    assert tuple(run.tables) == tuple(protocol.in_scope_tables()), (
        f"{SCENARIO}: the comparison was bounded by {list(run.tables)}, but the "
        f"protocol bounds it by ALL 22 IN-SCOPE TABLES, "
        f"{list(protocol.in_scope_tables())}."
    )
    assert set(declared) <= set(run.tables), (
        f"{SCENARIO}: declares an effect on "
        f"{sorted(set(declared) - set(run.tables))!r}, which the comparison never "
        f"covered."
    )
    # GUARD 2b - BOTH SIDES DROVE THE SAME FOUR OPERATIONS, IN THE SAME ORDER
    # (finding F-12). This scenario is the reason the guard exists: it declares four
    # operations spanning TWO menu executables, and the oracle side was once driven one
    # operation at a time while the Python side ran all four - so the diff compared a
    # one-operation state against a four-operation state and its verdict meant nothing.
    # Both runners now resolve the ordered list from the scenario itself and publish one
    # status row per operation, so the claim is checkable, and it is checked HERE rather
    # than left to be implied by a status lookup raising further in.
    protocol.assert_operations_driven(run, operations=OPERATION_ORDER)

    # GUARD 3 - BOTH RUN STAGES' ACTUAL STATUSES, READ AND CLASSIFIED. This is the only
    # scenario with FOUR operations inside one run stage, and the runners stop at the
    # first operation whose status contradicts its declaration - so an abort or a
    # refused precondition in operation 2, 3 or 4 would leave the later legs unposted,
    # both sides equally unwritten, and the diff equally empty. The declared statuses
    # are read from the scenario file; nothing here restates them.
    # `reference_only` bounds this guard to the ORACLE side. An oracle that did not
    # complete all four operations means the scenario was never set up as declared - a
    # setup ERROR - whereas a Python side that diverges from it is a behavioural
    # regression, reported as a FAILURE by
    # `test_both_run_statuses_are_the_declared_ones` below.
    protocol.assert_declared_statuses(
        run,
        operations=OPERATION_ORDER,
        declared=list(_sequence(definition, KEY_EXPECTED_STATUS)),
        reference_only=True,
    )

    # GUARD 4 - THE TWO SIDES STARTED FROM THE SAME RECORDED STATE. One line per bounded
    # table in the declared order plus the parameter row, each carrying the table name,
    # its ROW COUNT and a SHA-256 of its canonical dump, compared as bytes. The digest is
    # what catches equal counts over different values.
    protocol.assert_seed_fingerprints_agree(run)

    # GUARD 5 - NON-VACUITY. Every table this scenario's `seed_files:` fill must come
    # back WITH ROWS on both sides, or an empty diff over empty tables proves nothing:
    # analysis.dat -> ANALYSIS-REC, value.dat -> VALUEANAL-REC, salesled.dat ->
    # SALEDGER-REC, invoice.dat -> SAINVOICE-REC and SAINV-LINES-REC, openitm3.dat ->
    # SAITM3-REC, purchled.dat -> PULEDGER-REC, pinvoice.dat -> PUINVOICE-REC and
    # PUINV-LINES-REC, openitm5.dat -> PUITM5-REC, and system.dat -> SYSTOT-REC through
    # the four-loader system block [common/masterLD.sh:L51-L87]. THE FOCAL TABLE IS
    # AMONG THEM, which is what stops the three site tests below asserting over an
    # absent row. GLBATCH-REC, GLPOSTING-REC and PSIRSPOST-REC are deliberately not
    # required: the first two are WRITTEN by the pure-General-Ledger fan-out rather than
    # seeded, and the third is only opened and closed on this route.
    protocol.assert_non_vacuous(run, tables_requiring_rows=SEEDED_TABLES)

    # The two views of one comparison must agree. `run_scenario_parity` already raises
    # if the stage's exit status and its `TreeDiff` disagree; this states the invariant
    # at the point the evidence is handed over, because everything below trusts it.
    assert run.is_empty == run.outcome.is_empty, (
        f"{SCENARIO}: the run's verdict and its outcome's verdict disagree "
        f"({run.is_empty} against {run.outcome.is_empty}). Both derive from one "
        f"`TreeDiff` over one pair of trees, so a disagreement means neither view can "
        f"be trusted. Reported through {harness.diff_states.LABEL_COBOL} against "
        f"{harness.diff_states.LABEL_PYTHON}."
    )
    return run


# ---------------------------------------------------------------------------
#  SECTION 9  -  THE PRECONDITIONS
#
#  Five tests, NONE of which needs the stack: a scenario definition is a file on disk,
#  and the harness Python modules load on a bare host because their database driver is
#  imported lazily. They run first because a precondition failure is a far cheaper and
#  far clearer finding than a two-hour parity run that proved less than it looked.
# ---------------------------------------------------------------------------


def test_scenario_definition_preconditions(
    scenario_loader: Callable[[str], Mapping[str, Any]],
    pinned_clock: Any,
) -> None:
    """Every pin this scenario's evidence depends on, asserted before anything runs.

    NEEDS NO STACK. Six pins, each with the reason it matters:

      `file_system_used == 1`  THE FALSE-PASS TRAP.
        [copybooks/wssystem.cob:L112-L114] declares `File-System-Used pic 9` with
        `88 FS-Cobol-Files-Used value zero` and `88 FS-MySql-Used value 1`. With ZERO
        the handlers never touch MySQL - the pattern is at
        [common/acas007.cbl:L316-L320] - so both dumps come back empty, the trees
        agree, and stage 10 exits 0. That is a silent false pass and it is the single
        most dangerous misconfiguration available to this tier.
      `irs_instead == " "`  PINNED EXPLICITLY, never defaulted, because Agent Action
        Plan section 0.6.4 records that "leaving it at a default would make the
        affected-table list ambiguous". The space is the third state of
        [copybooks/wssystem.cob:L179-L181] and it is the one with NO CONDITION NAME AT
        ALL - both `IRS-Used` and `IRS-Both-Used` are simply False.
      `cyclea != 0`  a zero accounting cycle diverts the menu to system setup
        [general/general.cbl:L462-L463], which on a headless runner is a hang.
      `period == 1`  INERT ON THIS SCENARIO, and asserted only so that its inertness
        is recorded rather than assumed: the sole in-scope divide by it is
        [general/gl080.cbl:L328], which belongs to `gl_end_of_cycle` - an operation
        none of THIS file's four routes dispatches. ⚠️ NARROWED: this previously said
        `gl_end_of_cycle` "is driven by no scenario at all", which is false.
        `end_of_cycle_gl` drives it, and the divide is emphatically NOT inert there -
        it is what selects the quarter.
      `date_form == 1`  UK dd/mm/yyyy, matching the pinned text, whose digits are never
        reordered to match the form.
      THE CLOCK  both observables, against the `pinned_clock` fixture and against this
        file's restated literals.

    Plus the shape facts that make the rest of this file's assertions meaningful: the
    scenario names itself, its `subsystem` is the empty scalar because it spans two
    menus, the grouped blocks and their flat mirrors agree, and the seed carries the
    nine flat files and no others.

    Args:
        scenario_loader: `yaml.safe_load` of one scenario definition.
        pinned_clock: The project-wide pinned run date, as both observables.
    """
    definition = scenario_loader(SCENARIO)

    assert definition.get(KEY_NAME) == SCENARIO, (
        f"the definition at harness/scenarios/{SCENARIO}.yaml names itself "
        f"{definition.get(KEY_NAME)!r}. The name is published once and the oracle-side "
        f"runner falls back to the file's own basename, so the two agree by "
        f"construction; a disagreement means the file was copied rather than written."
    )

    #  THE ONE KEY WHOSE VALUE DIFFERS IN KIND FROM ITS SEVEN SIBLINGS. The oracle-side
    #  runner refuses a file whose subsystem disagrees with the subsystem of the
    #  operation it was asked to run, and this run spans TWO menus, so naming either
    #  would fail two of the four invocations on a cross-check rather than on anything
    #  behavioural. The empty scalar reads as "the file does not say".
    assert definition.get(KEY_SUBSYSTEM) == "", (
        f"{SCENARIO}: `subsystem:` is {definition.get(KEY_SUBSYSTEM)!r} where it must "
        f"be the EMPTY SCALAR. This is the one scenario that spans two menus - "
        f"operations 1 and 2 are Sales and 3 and 4 are Purchase - so no single "
        f"subsystem name is true for all four, and naming one would fail two "
        f"invocations on the runner's own cross-check."
    )

    #  THE COMPATIBILITY KEY. Both runners resolve the ordered `operations:` list
    #  and drive every entry in ONE invocation, falling back to this singular key
    #  only when no list is present -- so for this file NEITHER runner reads it. It
    #  still has to name the first of the four, so that a reader who follows the
    #  fallback path arrives at a coherent single-operation run.
    assert definition.get(KEY_OPERATION) == OPERATION_ORDER[0], (
        f"{SCENARIO}: `operation:` is {definition.get(KEY_OPERATION)!r} where it must "
        f"name the first of the four, {OPERATION_ORDER[0]!r} "
        f"({OPERATION_MENU_PARAGRAPHS[OPERATION_ORDER[0]]}). Neither runner reads "
        f"this key while `operations:` is present; it is kept so the key set stays "
        f"identical across all nine scenario files, and it must stay consistent "
        f"with the list rather than name some other operation."
    )

    system = _block(definition, KEY_SYSTEM)

    assert system[SYS_FILE_SYSTEM_USED] == FILE_SYSTEM_USED_MYSQL, (
        f"{SCENARIO}: `system.file_system_used` is "
        f"{system[SYS_FILE_SYSTEM_USED]!r} and MUST be {FILE_SYSTEM_USED_MYSQL}. "
        f"[copybooks/wssystem.cob:L112-L114] gives `88 FS-Cobol-Files-Used value "
        f"zero` and `88 FS-MySql-Used value 1`; with zero the handlers never touch "
        f"MySQL [common/acas007.cbl:L316-L320], BOTH dumps come back empty, and the "
        f"diff exits 0 - A SILENT FALSE PASS. It is also what makes "
        f"`FS-Cobol-Files-Used` False, which is why the guarded print blocks at "
        f"[sales/sl060.cbl:L695] and [purchase/pl060.cbl:L623] do not run while their "
        f"unconditional totals adds at [sales/sl060.cbl:L700] and "
        f"[purchase/pl060.cbl:L628] still do."
    )

    assert system[SYS_IRS_INSTEAD] == IRS_INSTEAD_GL_ONLY, (
        f"{SCENARIO}: `system.irs_instead` is {system[SYS_IRS_INSTEAD]!r} and must be "
        f"{IRS_INSTEAD_GL_ONLY!r} - pure General Ledger. "
        f"[copybooks/wssystem.cob:L179-L181] declares `IRS-Instead pic x` with "
        f"`88 IRS-Used value \"Y\"` and `88 IRS-Both-Used value \"B\"`; the third "
        f"state has NO condition name at all. THE PIN IS LOAD-BEARING FOR THE BOUND: "
        f"in pure General Ledger mode GLBATCH-REC and GLPOSTING-REC are written and "
        f"PSIRSPOST-REC is only opened and closed, whereas under \"Y\" or \"B\" the "
        f"fan-out would change which tables move. Tested at three sites in each of "
        f"the four Sales and Purchase posting programs, for example "
        f"[sales/sl060.cbl:L1039], [sales/sl060.cbl:L1126], [sales/sl060.cbl:L1175]."
    )

    assert system[SYS_CYCLEA] != CYCLEA_MUST_BE_NON_ZERO, (
        f"{SCENARIO}: `system.cyclea` is {system[SYS_CYCLEA]!r}. `Cyclea binary-char` "
        f"[copybooks/wssystem.cob:L62] must be non-zero: a zero accounting cycle "
        f"diverts the menu to system setup [general/general.cbl:L462-L463], which on a "
        f"headless runner is a hang rather than an error."
    )

    assert system[SYS_PERIOD] == PERIOD_INERT_VALUE, (
        f"{SCENARIO}: `system.period` is {system[SYS_PERIOD]!r} where the uniform key "
        f"set carries {PERIOD_INERT_VALUE}. IT IS INERT - the only in-scope divide by "
        f"it is [general/gl080.cbl:L328] and `gl_end_of_cycle` is driven by no "
        f"scenario file at all - and it is asserted so that the inertness is recorded "
        f"rather than assumed."
    )

    assert system[SYS_DATE_FORM] == DATE_FORM_UK, (
        f"{SCENARIO}: `system.date_form` is {system[SYS_DATE_FORM]!r} and must be "
        f"{DATE_FORM_UK} (UK dd/mm/yyyy), matching the pinned text "
        f"{PINNED_TO_DAY!r}, whose digits are never reordered to match the form."
    )

    #  THE FLAT MIRRORS. The oracle-side runner reads TOP-LEVEL KEYS ONLY, so a value
    #  nested under `clock:`, `system:` or `seed:` is invisible to it. The pairs are
    #  written side by side precisely so that drift is visible, and they must agree.
    clock = _block(definition, KEY_CLOCK)
    assert clock[KEY_CLOCK_TO_DAY] == definition.get(KEY_RUN_DATE_TEXT), (
        f"{SCENARIO}: `clock.to_day` is {clock[KEY_CLOCK_TO_DAY]!r} and its flat "
        f"mirror `run_date_text` is {definition.get(KEY_RUN_DATE_TEXT)!r}. The pair "
        f"must always hold the same value: the oracle-side runner sees only the flat "
        f"key and every other consumer sees only the block."
    )
    assert clock[KEY_CLOCK_RUN_DATE] == definition.get(KEY_RUN_DATE_BINARY), (
        f"{SCENARIO}: `clock.run_date` is {clock[KEY_CLOCK_RUN_DATE]!r} and its flat "
        f"mirror `run_date_binary` is {definition.get(KEY_RUN_DATE_BINARY)!r}."
    )
    assert system[SYS_DATE_FORM] == definition.get(KEY_DATE_FORM), (
        f"{SCENARIO}: `system.date_form` and the flat `date_form` disagree "
        f"({system[SYS_DATE_FORM]!r} against {definition.get(KEY_DATE_FORM)!r})."
    )
    assert system[SYS_IRS_INSTEAD] == definition.get(KEY_IRS_INSTEAD), (
        f"{SCENARIO}: `system.irs_instead` and the flat `irs_instead` disagree "
        f"({system[SYS_IRS_INSTEAD]!r} against {definition.get(KEY_IRS_INSTEAD)!r}). "
        f"The switch must be PRESENT in both even though its value is a space."
    )

    #  THE PINNED CLOCK, in both observables, against the fixture and this file's
    #  literals. `Run-Date` is the binary observable [copybooks/wssystem.cob:L67].
    assert (clock[KEY_CLOCK_TO_DAY], clock[KEY_CLOCK_RUN_DATE]) == (
        PINNED_TO_DAY,
        PINNED_RUN_DATE,
    ), (
        f"{SCENARIO}: the declared clock is "
        f"({clock[KEY_CLOCK_TO_DAY]!r}, {clock[KEY_CLOCK_RUN_DATE]!r}) where the "
        f"folder specification names ({PINNED_TO_DAY!r}, {PINNED_RUN_DATE!r})."
    )
    assert (pinned_clock.to_day, pinned_clock.run_date) == (
        PINNED_TO_DAY,
        PINNED_RUN_DATE,
    ), (
        f"the `pinned_clock` fixture supplies "
        f"({pinned_clock.to_day!r}, {pinned_clock.run_date!r}) where the folder "
        f"specification names ({PINNED_TO_DAY!r}, {PINNED_RUN_DATE!r}). The Sales and "
        f"Purchase programs stamp dates through this same run-date path, and "
        f"`SALEDGER-REC.SALES-STATS-DATE` is the one column on this scenario's bound "
        f"that normalisation's third job touches."
    )

    #  THE SEED. Nine flat files and no others, asserted by exact tuple equality, which
    #  proves the absence of the eight forbidden names of the same frozen contract
    #  without naming any of them.
    seed = _block(definition, KEY_SEED)
    nested_files = tuple(seed[KEY_SEED_FILES_NESTED])
    flat_files = _sequence(definition, KEY_SEED_FILES)
    assert nested_files == SEED_FILES, (
        f"{SCENARIO}: `seed.files` is {nested_files!r} where it must be exactly "
        f"{SEED_FILES!r}. The frozen loader contract "
        f"[common/masterLD.sh:L93-L116] runs the system block first, and within it "
        f"`sys4LD` [common/masterLD.sh:L51-L87] is the step that loads this scenario's "
        f"focal table {FOCAL_TABLE}."
    )
    assert flat_files == nested_files, (
        f"{SCENARIO}: `seed_files` is {flat_files!r} and `seed.files` is "
        f"{nested_files!r}. The seeder reads the flat mirror; the pair must agree."
    )
    assert SEED_FILE_SYSTEM in flat_files, (
        f"{SCENARIO}: `{SEED_FILE_SYSTEM}` is absent from the seed list. It is "
        f"effectively mandatory: without a system record the menu calls the "
        f"parameter-setup program INTERACTIVELY [general/general.cbl:L385-L394], which "
        f"on a headless runner is a hang, and it is what carries `Run-Date` "
        f"[copybooks/wssystem.cob:L67], the fan-out switch "
        f"[copybooks/wssystem.cob:L179-L181] and both posting latches."
    )


def test_flag_p_latches_are_two(
    scenario_loader: Callable[[str], Mapping[str, Any]],
) -> None:
    """`s_flag_p` AND `p_flag_p` must both be 2, or two write sites are never reached.

    NEEDS NO STACK, and isolated into its own test so that its failure message is
    unmistakable. This is the single most valuable precondition in the file, because its
    violation does not fail anything - it QUIETLY REDUCES COVERAGE and still produces an
    empty diff.

    [sales/sl100.cbl:L296-L301] verbatim:

        L296      if       S-Flag-P not = 2
        L297               display SL137   at 2301
        L298               display SL002   at 2401
        L299               accept ws-reply at 2433
        L300               go to menu-exit          <- NOTHING IS POSTED
        L301      end-if.

    [purchase/pl100.cbl:L289-L294] has the identical structure. The two fields are
    `S-Flag-P` [copybooks/wssystem.cob:L226] and `P-Flag-P`
    [copybooks/wssystem.cob:L206].

    AND BOTH LATCHES ARE CLEARED BY THE RUN - [sales/sl100.cbl:L474] and
    [purchase/pl100.cbl:L465] each move zero into their own - so a repeat of operation 2
    or 4 within one seeded state is a no-op. That is why stage 5 of the protocol
    re-seeds, and why this scenario must never be re-run in place: without the reset,
    operations 2 and 4 would post nothing on the second leg and the diff would be empty
    FOR THE WRONG REASON.

    Args:
        scenario_loader: `yaml.safe_load` of one scenario definition.
    """
    system = _block(scenario_loader(SCENARIO), KEY_SYSTEM)

    #  The coverage claim is DERIVED from the per-operation site map rather than
    #  asserted, so the numbers in the message cannot drift from the write-site table.
    lost = tuple(
        site
        for operation in ANSWERED_OPERATIONS
        for site in SITES_BY_OPERATION[operation]
    )
    reached = len(PERIOD_TOTAL_WRITE_SITES) - len(lost)

    for key, field, gate, latch in (
        (SYS_S_FLAG_P, "S-Flag-P", "sales/sl100.cbl:L296-L301", "sales/sl100.cbl:L474"),
        (
            SYS_P_FLAG_P,
            "P-Flag-P",
            "purchase/pl100.cbl:L289-L294",
            "purchase/pl100.cbl:L465",
        ),
    ):
        assert system[key] == FLAG_P_POSTING_READY, (
            f"{SCENARIO}: `system.{key}` is {system[key]!r} and MUST be "
            f"{FLAG_P_POSTING_READY}. With any other value `{field}` fails its gate at "
            f"[{gate}] and control goes straight to `menu-exit`, so OPERATIONS 2 AND 4 "
            f"WOULD NO-OP and only {reached} of the "
            f"{len(PERIOD_TOTAL_WRITE_SITES)} period-total sites would be reached - "
            f"the two lost are sites {lost[0]} [sales/sl100.cbl:L404] and {lost[1]} "
            f"[purchase/pl100.cbl:L396], the two that accumulate into TWO RECEIVERS IN "
            f"ONE ADD. The diff would still be empty, and it would prove almost "
            f"nothing. Note also that the latch is CLEARED by the run at [{latch}], so "
            f"it is one-shot and the seeded value is the only one that counts."
        )


def test_four_operations_in_declared_order(
    scenario_loader: Callable[[str], Mapping[str, Any]],
) -> None:
    """Exactly four operations, in the only order that is correct, all expecting 0.

    NEEDS NO STACK. This is the only scenario in the set with more than one operation,
    and THE ORDER IS PART OF THE SPECIFICATION rather than a convenience: operation 3
    sets flags operation 4 reads [purchase/pl060.cbl:L373-L375]; operations 1 and 3
    create the ledger rows operations 2 and 4 rewrite; and A-17's unexplained write
    [sales/sl060.cbl:L1173] is read back by a LATER operation
    [purchase/pl100.cbl:L564], which is ambiguity Q-A17-POSTINGS-EFFECT. All four run
    inside a single stage 2 and a single stage 6, one at a time, with NO dump between
    them, so the diff proves the CUMULATIVE effect of the sequence.

    OPERATION 1 IS `sl_invoice_post`, WHOSE COBOL COUNTERPART IS `load07` AND NOT
    `load08`. [sales/sales.cbl:L756] carries `*> Sales trans posting` and dispatches
    sl055 then sl060; `load08.` at [sales/sales.cbl:L770] dispatches the OUT-OF-SCOPE
    sl080 (Payment Input). An occurrence of load08 against Sales anywhere is an error
    and is not propagated. Purchase's `load08` at [purchase/purchase.cbl:L752] is a
    different menu and a genuine one.

    `operations:` IS A FLAT SEQUENCE OF NAMES and carries no per-item subsystem, so the
    per-operation subsystem is asserted against this file's restatement of the runners'
    shared map: sales, sales, purchase, purchase. That is also why the file's own
    `subsystem` is the empty scalar.

    `expected_status:` IS POSITIONAL and is four zeros, provably rather than hopefully:
    the only code either extract program can raise is 8 [sales/sl055.cbl:L344],
    [purchase/pl055.cbl:L286], and both raise sites sit inside `if
    FS-Cobol-Files-Used` [sales/sl055.cbl:L326], [purchase/pl055.cbl:L266], which
    `file_system_used: 1` makes False. The only other code the harness can observe is 5
    [general/gl070.cbl:L289], from a program this scenario never runs. The mapping from
    a term code to a process status is the identity, settled as Q-CLI-EXITSTATUS in
    `acas_posting/cli/args.py` and not re-decided here.

    Args:
        scenario_loader: `yaml.safe_load` of one scenario definition.
    """
    definition = scenario_loader(SCENARIO)
    operations = _sequence(definition, KEY_OPERATIONS)

    assert operations == OPERATION_ORDER, (
        f"{SCENARIO}: `operations:` is {operations!r} where it must be exactly "
        f"{OPERATION_ORDER!r}. The order is load-bearing: operation 3 sets flags "
        f"operation 4 reads [purchase/pl060.cbl:L373-L375], operations 1 and 3 create "
        f"the rows operations 2 and 4 rewrite, and A-17's write "
        f"[sales/sl060.cbl:L1173] is read back by a later operation "
        f"[purchase/pl100.cbl:L564] ({AMBIGUITY_A17_EFFECT}). There is exactly one "
        f"dump per side and none between operations, so the diff proves the cumulative "
        f"effect of the whole sequence."
    )

    #  Operation 1 is called out separately so the load07 fact has a home of its own.
    assert operations[0] == "sl_invoice_post", (
        f"{SCENARIO}: the first operation is {operations[0]!r} and must be "
        f"'sl_invoice_post', whose COBOL counterpart is "
        f"{OPERATION_MENU_PARAGRAPHS['sl_invoice_post']} - LOAD07, NOT LOAD08. "
        f"[sales/sales.cbl:L756] carries `*> Sales trans posting`; `load08.` at "
        f"[sales/sales.cbl:L770] dispatches the out-of-scope sl080 (Payment Input)."
    )

    #  Every operation must be one this file knows the subsystem of, and no operation
    #  may repeat: a repeat would silently mean two dispatches where the scenario
    #  declares one, and both `Flag-P` latches are one-shot.
    assert len(set(operations)) == len(operations), (
        f"{SCENARIO}: `operations:` repeats an entry ({operations!r}). Both cash "
        f"latches are cleared by their own run [sales/sl100.cbl:L474], "
        f"[purchase/pl100.cbl:L465], so a repeated cash operation would post nothing "
        f"the second time."
    )
    for operation in operations:
        assert operation in OPERATION_SUBSYSTEMS, (
            f"{SCENARIO}: `{operation}` is not one of the four this scenario drives "
            f"({', '.join(OPERATION_ORDER)}). The seven-operation vocabulary is "
            f"identical in both runners so that they stay trivially comparable."
        )

    #  The per-operation subsystem, which the file deliberately does not declare. The
    #  ORDERED sequence is the fact that matters: two Sales dispatches, then two
    #  Purchase ones. That is why the file's own `subsystem` is the empty scalar, and it
    #  is what puts each menu's SECOND dispatch inside one run - the situation
    #  Q-CLI-OVERREWRITE-SECOND-LEG is about.
    sequence = tuple(OPERATION_SUBSYSTEMS[operation] for operation in operations)
    assert sequence == EXPECTED_SUBSYSTEM_SEQUENCE, (
        f"{SCENARIO}: the four operations run against {sequence!r} where they must run "
        f"against {EXPECTED_SUBSYSTEM_SEQUENCE!r} - "
        + ", ".join(
            f"{operation} on {OPERATION_SUBSYSTEMS[operation]} "
            f"({OPERATION_MENU_PARAGRAPHS[operation]})"
            for operation in OPERATION_ORDER
        )
        + f". Because each menu is entered TWICE in one run, this scenario is the one "
        f"that measures {AMBIGUITY_SECOND_LEG}."
    )

    statuses = _sequence(definition, KEY_EXPECTED_STATUS)
    assert statuses == EXPECTED_STATUS, (
        f"{SCENARIO}: `expected_status:` is {statuses!r} where it must be "
        f"{EXPECTED_STATUS!r} - one per operation, POSITIONALLY. Four zeros is "
        f"provable: term code 8 is unreachable because both raise sites sit inside `if "
        f"FS-Cobol-Files-Used` [sales/sl055.cbl:L326], [purchase/pl055.cbl:L266] and "
        f"this scenario pins file_system_used to {FILE_SYSTEM_USED_MYSQL}; term code 5 "
        f"[general/gl070.cbl:L289] comes from a program this scenario never runs. The "
        f"term-code-to-status mapping is the identity ({AMBIGUITY_EXIT_STATUS})."
    )
    assert len(statuses) == len(operations), (
        f"{SCENARIO}: `expected_status:` has {len(statuses)} entries against "
        f"{len(operations)} operations. The two sequences match POSITIONALLY, so a "
        f"length mismatch leaves an operation's expectation undefined."
    )


def test_ok_to_post_answers_are_pinned(
    scenario_loader: Callable[[str], Mapping[str, Any]],
) -> None:
    """The promoted payment confirmation is pinned to the literal "YES", and only it.

    NEEDS NO STACK. The two cash programs ask the same question and neither has a
    default:

        sales/sl100.cbl                        purchase/pl100.cbl
        L313  move spaces to wx-reply.         L305  move spaces to wx-reply.
        L314  accept wx-reply at 1256 update   L306  accept wx-reply at 1256 update
        L316  if wx-reply = "NO"               L308  if wx-reply = "NO"
        L317       go to menu-exit.            L309       go to menu-exit.
        L318  if wx-reply not = "YES"          L310  if wx-reply not = "YES"
        L319       go to acpt-xrply.           L311       go to acpt-xrply.

    So ONLY the literal "YES" proceeds; "NO" exits at [sales/sl100.cbl:L316-L317] and
    [purchase/pl100.cbl:L308-L309] BEFORE the first file is opened, having written
    nothing; and anything else, a blank included, loops back for ever. That is ambiguity
    Q-CLI-OKTOPOST, resolved by requiring the answer rather than inventing a default.

    ONE KEY COVERS BOTH ROUTES, because the runners are invoked per operation and both
    programs ask the same question. THE KEY IS SEMANTIC AND IS NOT AN OPTION SPELLING:
    `harness/run_python_scenario.sh` reads it, validates it as YES or NO, and owns the
    translation, probing each module's `--help` once and failing as a harness fault if
    the option is absent. This file therefore names no flag, builds no command line and
    starts no process.

    The prompt WORDING diverges between the two - Sales uses `[   ]` and title case at
    [sales/sl100.cbl:L311-L312], Purchase uses `<   > enter {CR}` and lower case at
    [purchase/pl100.cbl:L303-L304] - and that cosmetic divergence is preserved rather
    than harmonised (R-4). Only the wording differs; the logic is identical.

    THE OTHER ROUTES' ANSWER KEYS MUST BE ABSENT, because none of their routes is on
    this path: the transfer-file clear belongs to the IRS route, and the three
    end-of-cycle answers belong to the operation this scenario deliberately omits.
    Leaving them unstated is what keeps this scenario's inputs exactly the inputs the
    frozen cycle takes.

    Args:
        scenario_loader: `yaml.safe_load` of one scenario definition.
    """
    definition = scenario_loader(SCENARIO)

    assert definition.get(ANSWER_KEY_PAYMENT_CONFIRM) == ANSWER_PAYMENT_CONFIRM, (
        f"{SCENARIO}: `{ANSWER_KEY_PAYMENT_CONFIRM}:` is "
        f"{definition.get(ANSWER_KEY_PAYMENT_CONFIRM)!r} and must be the literal "
        f"{ANSWER_PAYMENT_CONFIRM!r}. It gates EVERY database write the two cash "
        f"programs make: \"NO\" transfers to `menu-exit` before the first file is "
        f"opened [sales/sl100.cbl:L316-L317], [purchase/pl100.cbl:L308-L309], and "
        f"anything else - a blank included - loops back to `acpt-xrply.` for ever "
        f"[sales/sl100.cbl:L318-L319], [purchase/pl100.cbl:L310-L311]. Without it, "
        f"period-total sites 5 [sales/sl100.cbl:L404] and 9 "
        f"[purchase/pl100.cbl:L396] are unreachable. Ambiguity "
        f"{AMBIGUITY_PAYMENT_CONFIRM}."
    )

    #  ONE key covers the two operations that ask - it is a scenario-level key rather
    #  than a per-operation answer map, because `operations:` is a flat sequence of
    #  names and a nested block under it is refused outright. The two partitions must be
    #  DISJOINT and must together be exactly the four, or some operation's answer state
    #  would be unstated: the two cash routes consume the key and the invoice and order
    #  routes promote nothing at all.
    answered = set(ANSWERED_OPERATIONS)
    unanswered = set(UNANSWERED_OPERATIONS)
    assert not answered & unanswered, (
        f"{SCENARIO}: {sorted(answered & unanswered)!r} is listed as both consuming "
        f"`{ANSWER_KEY_PAYMENT_CONFIRM}` and promoting nothing."
    )
    assert answered | unanswered == set(OPERATION_ORDER), (
        f"{SCENARIO}: the answered routes {sorted(answered)!r} and the unanswered ones "
        f"{sorted(unanswered)!r} do not together cover the four this scenario drives "
        f"({', '.join(OPERATION_ORDER)}), so some operation's answer state is "
        f"unstated. The two cash routes consume the key; the invoice and order routes "
        f"promote nothing - sl055 and sl060 have only diagnostic acknowledgements, and "
        f"pl060's own confirmation prompt is entirely commented out "
        f"[purchase/pl060.cbl:L362-L370]."
    )
    assert answered == {
        operation
        for operation in OPERATION_ORDER
        if OPERATION_MENU_PARAGRAPHS[operation].endswith(("L792-L796", "L786-L790"))
    }, (
        f"{SCENARIO}: the routes said to consume `{ANSWER_KEY_PAYMENT_CONFIRM}` are "
        f"{sorted(answered)!r}, which are not the two CASH routes - "
        f"`sl_cash_post` ({OPERATION_MENU_PARAGRAPHS['sl_cash_post']}) and "
        f"`pl_payment_post` ({OPERATION_MENU_PARAGRAPHS['pl_payment_post']}), the two "
        f"whose programs ask the question at [sales/sl100.cbl:L310-L319] and "
        f"[purchase/pl100.cbl:L302-L311]."
    )

    for key in ABSENT_ANSWER_KEYS:
        assert key not in definition, (
            f"{SCENARIO}: `{key}:` is declared and must not be. None of its routes is "
            f"on this path - the transfer-file clear belongs to the IRS route and the "
            f"three end-of-cycle answers to `gl_end_of_cycle`, which THIS scenario does "
            f"not drive (`end_of_cycle_gl` does). Leaving it unstated is what keeps "
            f"this scenario's inputs exactly "
            f"the inputs the frozen cycle takes (R-3)."
        )


def test_affected_tables_are_in_scope_and_alphabetical(
    scenario_loader: Callable[[str], Mapping[str, Any]],
    in_scope_table_names: tuple[str, ...],
) -> None:
    """Fourteen tables, alphabetical, every one in scope - and `SYSTOT-REC` among them.

    NEEDS NO STACK. THE AFFECTED-TABLE LIST IS THE ONLY BOUNDING MECHANISM in this
    tier. There is no ignore-list, no tolerance-list and no "known difference"
    allowance anywhere in the diff path, so what is on the list is compared exactly and
    what is off it is not compared at all - BOUNDING, NEVER IGNORING.

    `SYSTOT-REC` IS DELIBERATELY INCLUDED HERE, and it is never blanket-excluded.
    ⚠️ NARROWED: this previously added "AND ON NO OTHER SCENARIO'S LIST", which is
    false - `clean_batch_sl` and `clean_batch_pl` declare it too, reaching four and
    three of the nine write sites respectively. This scenario's claim rests on REACH,
    not exclusivity: all four operations, so all nine sites, in one dump.
    Agent Action Plan section 0.6.4 names the nine
    period-total write sites as "the sole writers of the totals record, which makes the
    period-end-totals scenario verifiable by inspecting one table", and that is exactly
    the claim this list makes possible.

    THE ORDER IS LOAD-BEARING, not cosmetic: the report's table order is the scenario's
    declared order, and the seed fingerprint is written in it, so a disagreement is a
    HARNESS FAULT rather than a behavioural finding.

    THE 22-TABLE IN-SCOPE INVENTORY AND EVERY PRIMARY KEY ARE NOT RESTATED HERE. They
    have exactly one definition in this repository, in `harness/dump_tables.py`, and
    they are reached through the `in_scope_table_names` fixture. The eleven out-of-scope
    tables are never dumped.

    Args:
        scenario_loader: `yaml.safe_load` of one scenario definition.
        in_scope_table_names: The 22 in-scope names, read from the single definition.
    """
    declared = _sequence(scenario_loader(SCENARIO), KEY_AFFECTED_TABLES)

    assert declared == AFFECTED_TABLES, (
        f"{SCENARIO}: `affected_tables:` is {declared!r} where it must be exactly "
        f"{AFFECTED_TABLES!r}. Each entry's reason: "
        + "; ".join(f"{table} - {TABLE_REASONS[table]}" for table in AFFECTED_TABLES)
    )

    assert list(declared) == sorted(declared), (
        f"{SCENARIO}: `affected_tables:` is not in ascending order ({declared!r}). "
        f"The order is load-bearing: the report's table order is this order and the "
        f"seed fingerprint is written in it, so a disagreement between the two sides' "
        f"declared order is a harness fault."
    )

    for table in declared:
        assert table in in_scope_table_names, (
            f"{SCENARIO}: `{table}` is not one of the 22 in-scope tables. The "
            f"inventory has exactly one definition, in `harness/dump_tables.py`, and "
            f"the eleven out-of-scope tables of Agent Action Plan section 0.2.2 are "
            f"never dumped."
        )

    #  THE FOCAL TABLE, called out separately so that a future reader tempted to
    #  blanket-exclude the system tables finds the reason here.
    assert FOCAL_TABLE in declared, (
        f"{SCENARIO}: `{FOCAL_TABLE}` is absent from the bound, and it is the one "
        f"table this scenario exists to compare. {TABLE_REASONS[FOCAL_TABLE]}. It is "
        f"also the one system table THIS route declares an effect on: `SYSDEFLT-REC` "
        f"and `SYSFINAL-REC` are on no Sales or Purchase scenario's declared-effect "
        f"list because all twelve in-scope programs contain zero `perform System-...` "
        f"verbs and only the out-of-scope menu shells touch them, and `SYSTEM-REC` is "
        f"declared on every scenario because `args.overrewrite` writes it on every "
        f"route. All 22 are dumped and compared regardless - bounding, not ignoring. "
        f"The "
        f"asymmetry that follows is recorded as {AMBIGUITY_SYSTOT_OVERLAP}."
    )


# ---------------------------------------------------------------------------
#  SECTION 10  -  THE PROOF OBLIGATION
#
#  Every test below requests `parity`, so every one of them is skipped with a precise
#  reason on a host without the Compose stack, the built oracle or a seeded database.
#  Each is a view on ONE arbitration - the ten-stage protocol ran once, in the fixture
#  - so two of them can never disagree about what the compiled run did.
# ---------------------------------------------------------------------------


@pytest.mark.database
@pytest.mark.oracle
def test_period_end_totals_state_parity(parity: Any, harness: Any) -> None:
    """THE HEADLINE. The ordering-normalised diff must be EMPTY.

    Agent Action Plan section 0.8.5, verbatim: "seed identically through the
    maintainer's load programs, run the compiled cycle, dump the affected tables
    ordering-normalised, reset, run the Python cycle, dump again - and the diff MUST BE
    EMPTY."

    WHAT AN EMPTY DIFF PROVES HERE, SPECIFICALLY: that all nine period-total
    accumulations landed on identical values in `SYSTOT-REC`, through A-8's double
    truncation, through A-9's missing increments on both credit-note paths, through
    A-10's three mutually inconsistent guards and their differing counter handling, and
    through
    the two write sites that add unconditionally where a reader would expect them to be
    guarded. It also proves that the two ledgers' own tables agree, that the transfer
    table came back exactly as seeded, and - asserted by the runners rather than here -
    that the four automatic-generation tables are still empty.

    THIS BODY HOLDS ONLY THE VERDICT. Every stage, both guards and the comparison's own
    construction happened in the fixture, so a harness fault is a pytest ERROR and what
    remains here is the arbitration, so a genuine behavioural difference is a pytest
    FAILURE. Agent Action Plan section 0.6.6 is what makes the verdict trustworthy: the
    dump is deterministic by construction, so "a non-empty diff is always a real
    behavioral difference and never an artefact of the comparison".

    A PASSING STAGE 10 WRITES A ZERO-BYTE REPORT, and that is deliberate rather than
    incidental: the evidence document must distinguish "compared, and identical" from
    "never compared", and an existing empty file says the first while an absent file
    says nothing at all. Both are asserted.

    Args:
        parity: The completed ten-stage run.
        harness: The three harness Python modules, for the deterministic renderer.
    """
    assert parity.is_empty, _verdict(
        parity,
        harness,
        bearing=(
            f"If the finding is on {FOCAL_TABLE}, it bears on "
            f"{AMBIGUITY_SYSTOT_OVERLAP} and, because this is the only scenario that "
            f"is two dispatches per menu, on {AMBIGUITY_SECOND_LEG}."
        ),
    )

    #  The renderer's own statement of the same verdict. It returns THE EMPTY STRING
    #  when the two trees are identical, which is the zero-byte stdout the contract
    #  promises for exit 0.
    assert harness.diff_states.render(parity.tree) == "", (
        f"{SCENARIO}: the comparison reports itself empty, yet the deterministic "
        f"renderer produced output. Exit 0 means the trees are identical AND that "
        f"stdout is EMPTY - zero bytes, not a banner - so the two disagree and neither "
        f"can be trusted."
    )

    #  The report file exists and is empty. `run_scenario_parity` already refused exit
    #  2 by raising, so reaching here means a comparison actually happened - which is
    #  what R-6 requires before an empty diff may be read as a pass.
    report = parity.outcome.report
    assert report.is_file(), (
        f"{SCENARIO}: stage 10 reported the trees identical but wrote no report at "
        f"{report}. A PASSING run writes a ZERO-BYTE file on purpose: the evidence "
        f"recorded in {DOC_EVIDENCE} must distinguish 'compared, and identical' from "
        f"'never compared', and an absent file says nothing at all."
    )
    assert report.stat().st_size == 0, (
        f"{SCENARIO}: stage 10 reported the trees identical but its report at {report} "
        f"is {report.stat().st_size} byte(s) rather than zero. The three-way contract "
        f"makes exit 0 mean identical trees and EMPTY output."
    )


@pytest.mark.database
@pytest.mark.oracle
def test_both_run_statuses_are_the_declared_ones(parity: Any, protocol: Any) -> None:
    """BOTH SIDES' ACTUAL EXIT STATUSES, read from the run rather than from the YAML.

    THE FOUR-OPERATION SCENARIO IS THE ONE WHERE THIS MATTERS MOST. All four operations
    run inside a single stage 2 and a single stage 6, with no dump between them, and the
    runners stop at the first operation whose status contradicts its declaration - so an
    abort, a refused `Flag-P` latch or a runner precondition in operation 2, 3 or 4
    leaves the later legs unposted, both sides equally unwritten and THE DIFF EQUALLY
    EMPTY. Comparing the scenario file's declaration with a constant of this file's own
    would not notice any of that; only the observed statuses do.

    BOTH SIDES ARE ALSO CLASSIFIED, so the three dispositions stay distinct: `argparse`
    exit 2 means the runner built a bad command line, a code in a runner's own band
    means the script diagnosed itself, and either way the question was never asked.
    Sales and Purchase have term code 8 available [sales/sl055.cbl:L344],
    [purchase/pl055.cbl:L286] - both inside `if FS-Cobol-Files-Used` blocks, so
    unreachable at `file_system_used: 1` - and the two cash routes have none at all,
    which is why 0 is provable here rather than merely expected.

    The fixture makes the same assertion as one of its guards, before any verdict is
    read; this test states it under its own name so that a status deviation is
    attributable at a glance rather than only inside a fixture error.

    Args:
        parity: The completed ten-stage run.
        protocol: The protocol bundle, for `assert_declared_statuses`.
    """
    declared = list(_sequence(protocol.definition(SCENARIO), KEY_EXPECTED_STATUS))
    assert declared == list(EXPECTED_STATUS), (
        f"{SCENARIO}: the scenario declares {declared!r} where this file's folder "
        f"specification names {list(EXPECTED_STATUS)!r}."
    )

    dispositions = protocol.assert_declared_statuses(
        parity, operations=OPERATION_ORDER, declared=declared
    )

    observed = (parity.cobol_run.returncode, parity.python_run.returncode)
    assert observed == (0, 0), (
        f"{SCENARIO}: the two run stages exited {observed}. Every one of the four "
        f"operations is declared to succeed, and `exit_status_for(term_code)` returns "
        f"the term code itself, so anything non-zero means an operation did not run to "
        f"completion and the later legs posted nothing.\n{parity.describe()}"
    )
    assert dispositions == (
        protocol.vocabulary.disposition_success,
        protocol.vocabulary.disposition_success,
    ), (
        f"{SCENARIO}: the two run stages classified as {dispositions!r}; both must be "
        f"{protocol.vocabulary.disposition_success!r} on this route."
    )


@pytest.mark.database
@pytest.mark.oracle
def test_both_flag_p_latches_are_cleared_by_the_run(parity: Any, protocol: Any) -> None:
    """THE TWO ONE-SHOT LATCHES ARE CLEARED ON BOTH SIDES - each read from its own run.

    `[sales/sl100.cbl:L474]` is `move zero to S-Flag-P.` and
    `[purchase/pl100.cbl:L465]` is `move zero to P-Flag-P.`; both are `SYSTEM-REC`
    columns [copybooks/wssystem.cob:L226] and [copybooks/wssystem.cob:L206], and the
    menu's `overrewrite` paragraph is their sole writer to the store - key 1,
    `System-Rewrite` [general/general.cbl:L656-L663] - which the migrated cycle
    reproduces through `acas_posting/cli/args.py`'s `overrewrite`. So a cleared latch is
    a REAL, STORED consequence of operations 2 and 4 having posted, and a latch still
    holding `1` means the posting section returned through its gate: payment sites 5
    [sales/sl100.cbl:L404] and 9 [purchase/pl100.cbl:L396] would then be lost while the
    diff stayed empty, because `SYSTEM-REC` is not one of the compared tables.

    WHY IT IS OBSERVED FROM THE CAPTURES RATHER THAN THROUGH THE DIFF. `SYSTEM-REC` IS
    inside the comparison - the diff is bounded by all 22 in-scope tables and both sides
    persist the row, so a divergence would be caught, with exactly two of its 169
    columns withheld: `RDBMS-PASSWD char(12)` [copybooks/wssystem.cob:L139] and the
    frozen schema's shorter `PASS-WORD`, replaced on both sides by
    `harness/dump_tables.py`'s `REDACTED_COLUMNS` because a dump is `SELECT *`. What
    neither the diff nor the fingerprint can do is say WHICH COLUMN carries the claim
    this test makes - that operations 2 and 4 cleared the two `Flag-P` latches - because
    an empty diff proves only that the two sides agree, and a digest cannot answer "what
    does this one column hold". So each side's own captured latch marker is read
    instead.

    WHY IT IS NOT OBSERVED WITH A QUERY EITHER, WHICH IS THE CORRECTION HERE. An
    earlier form opened a connection when the TEST ran and queried the live database.
    That value described whatever state the shared database happened to be in at that
    moment - after stage 5 had dropped, re-applied the frozen schema and re-seeded
    between the two sides, after an arbitrary delay because `parity` is cached, and
    after any other scenario in the suite had reset the same database. It could pass on
    a freshly seeded row that this scenario never touched. Both runners now read the two
    columns in their post-run assertion stage, seconds after their own operation, and
    print `ONE-SHOT-LATCH <column> = <value>` into their own captured stream. This test
    reads BOTH captures.

    ⭐ AND IT READS THE LAST PAIR ON EACH SIDE, NOT THE ONLY PAIR. This is the one
    multi-operation scenario and it spans two menu executables, so the oracle is driven
    as a SEQUENCE of invocations while Python is driven as one; each oracle invocation
    runs its own post-run stage, so the oracle capture carries FOUR pairs and the Python
    capture ONE. Reading the first pair would assert against the state after operation
    1, where both latches are still SET, because only operations 2 and 4 clear them.
    `_latches_from` therefore returns the final pair and separately asserts that the
    number of pairs equals the number of operations that side reported - which makes the
    differing counts evidence about the sequence rather than something to tolerate.

    AND THE ORACLE SIDE IS NOW RECOVERABLE, which it was not before. The previous form
    stated as a limitation that "the oracle's own latch values are not recoverable after
    the fact from this run" and left the oracle-side claim to the seeded precondition.
    They are recoverable now, because the oracle runner captures them at the same point
    in its own stage, so this test asserts the clearing on each side AND that the two
    sides agree - a parity fact about a column the diff cannot reach.

    Args:
        parity: The completed ten-stage run. Both run stages' captures are read, so
            the observation is bound to the runs themselves rather than to when pytest
            happened to execute this test.
        protocol: The protocol bundle, for the scenario's own seeded latch values.

    Raises:
        Skipped: The Compose stack is unusable.
        AssertionError: A latch was not cleared on one side, the two sides disagree, or
            a capture carries no latch marker (a harness fault).
    """
    seeded = _block(protocol.definition(SCENARIO), KEY_SYSTEM)
    assert (seeded[SYS_S_FLAG_P], seeded[SYS_P_FLAG_P]) == (
        FLAG_P_POSTING_READY,
        FLAG_P_POSTING_READY,
    ), (
        f"{SCENARIO}: the scenario seeds the latches as "
        f"{(seeded[SYS_S_FLAG_P], seeded[SYS_P_FLAG_P])!r}; both must be "
        f"{FLAG_P_POSTING_READY} or operations 2 and 4 post nothing and there is no "
        f"clearing to observe."
    )

    # The expected emission count comes from what each side actually REPORTED, never
    # from the scenario's declared list: a run that stopped early legitimately reports
    # fewer operations, and the `parity` fixture has already asserted that the two
    # sides drove the SAME ordered list, so this cannot silently compare unlike work.
    observed = {
        "cobol": _latches_from(
            "cobol",
            parity.cobol_run.stdout,
            expected_emissions=len(parity.cobol_run.operation_statuses),
        ),
        "python": _latches_from(
            "python", parity.python_run.stdout, expected_emissions=1
        ),
    }

    for column, locator in zip(
        LATCH_COLUMNS,
        ("sales/sl100.cbl:L474", "purchase/pl100.cbl:L465"),
        strict=True,
    ):
        for side, values in observed.items():
            text = values[column]
            assert text.strip("-").isdigit(), (
                f"{SCENARIO}: the {side} runner reported "
                f"`{SYSTEM_TABLE}`.`{column}` = {text!r} after its run. A dash means "
                f"the row was absent; system.dat seeds exactly one row for key "
                f"{SYSTEM_RECORD_KEY} and without it there is no latch to observe."
            )
            assert int(text) == LATCH_CLEARED, (
                f"{SCENARIO}: the {side} runner reported "
                f"`{SYSTEM_TABLE}`.`{column}` = {text!r} after its run; it must be "
                f"{LATCH_CLEARED}, because [{locator}] moves zero into it once the "
                f"posting completes and `overrewrite`'s key-1 `System-Rewrite` "
                f"[general/general.cbl:L656-L663] persists it. A latch still holding "
                f"{FLAG_P_POSTING_READY} means the posting section returned through "
                f"its gate without posting - the two payment sites 5 "
                f"[sales/sl100.cbl:L404] and 9 [purchase/pl100.cbl:L396] would then "
                f"be lost, and the diff would STILL BE EMPTY because "
                f"`{SYSTEM_TABLE}` is not one of the compared tables. "
                f"Observed: {observed!r}."
            )

        assert int(observed["cobol"][column]) == int(observed["python"][column]), (
            f"{SCENARIO}: the two sides left `{SYSTEM_TABLE}`.`{column}` in different "
            f"states - cobol {observed['cobol'][column]!r}, python "
            f"{observed['python'][column]!r}. This column is NOT in the compared "
            f"dump, so the diff cannot report it; this marker comparison is the only "
            f"thing standing between a one-sided latch clear and a green run."
        )


@pytest.mark.database
@pytest.mark.oracle
def test_systot_rec_reflects_the_nine_write_sites(
    parity: Any, protocol: Any, harness: Any
) -> None:
    """`SYSTOT-REC` must be IDENTICAL on both sides - the nine sites, one table.

    Agent Action Plan section 0.6.4 names the nine period-total write sites as "the sole
    writers of the totals record, which makes the period-end-totals scenario verifiable
    by inspecting one table". Those nine, every locator read out of the frozen source:

      1  [sales/sl055.cbl:L675]     sl-invoices-this-month        if ih-type = 2  L674
      2  [sales/sl055.cbl:L677]     sl-credit-notes-this-month    if ih-type = 3  L676
      3  [sales/sl060.cbl:L641]     sl-credit-deductions          UNCONDITIONAL
      4  [sales/sl060.cbl:L700]     sl-cn-unappl-this-month       UNCONDITIONAL, and
                                                                  outside the L695 guard
      5  [sales/sl100.cbl:L404]     t-paid AND sl-payments        if oi-type = 5  L402
      6  [purchase/pl055.cbl:L582]  pl-invoices-this-month        if ih-type = 2  L581
      7  [purchase/pl055.cbl:L584]  pl-credit-notes-this-month    if ih-type = 3  L583
      8  [purchase/pl060.cbl:L628]  pl-cn-unappl-this-month       UNCONDITIONAL, and
                                                                  outside the L623 guard
      9  [purchase/pl100.cbl:L396]  t-paid AND pl-payments        if oi-type = 5  L394

    AGREEMENT IS ASSERTED, NEVER A PREDICTED FIGURE. R-6 makes the compiled run the
    arbiter, so this test does not know - and must not claim to know - what any of the
    twenty money columns should hold. It asserts only that the two sides hold the same
    thing, that the same number of rows exist on both, and that the column lists agree.

    ITS 21 COLUMNS. Primary key `LEDGER-TOTALS-REC-KEY` `tinyint(1) unsigned`
    [mysql/ACASDB.sql:L1377] and twenty `decimal(10,2)` money columns
    [mysql/ACASDB.sql:L1378-L1397], laid out by [copybooks/wssys4.cob] and loaded by
    `sys4LD` [common/masterLD.sh:L51-L87]. Two of the twenty carry A-20, the SALES
    prefix inside the PURCHASE group - `sl4-spare3` and `sl4-spare4`
    [copybooks/wssys4.cob:L29-L30], group at L20, surfacing as `SL4-SPARE3` and
    `SL4-SPARE4` [mysql/ACASDB.sql:L1396-L1397]. Preserved, never renamed.

    A DIVERGENCE HERE IS A REAL SIGNAL AND THE TEST FAILS. It is NOT resolved with an
    ignore-list, a tolerance or a "known difference" allowance. The failure message
    names the ambiguity identifier the finding bears on, because the table is written
    both by the nine in-scope sites and by the menu shell's exit path
    [sales/sales.cbl:L659-L660], [purchase/purchase.cbl:L652-L653],
    [general/general.cbl:L656-L691], which the migrated cycle reproduces through
    `acas_posting/cli/args.py`'s `slpl_menu_state` and `args.overrewrite`.

    Args:
        parity: The completed ten-stage run.
        harness: The three harness Python modules, for the deterministic renderer.
    """
    #  THE NINE OBSERVABLES, READ BEFORE THE VERDICT IS ASKED FOR. Each site
    #  accumulates into exactly one `SYSTOT-REC` column, so reading all nine columns on
    #  both sides is how "all nine write paths are represented" becomes a measurement
    #  rather than a claim about this file's own constants. The helper refuses an absent
    #  row, so the nine cannot be asserted over a table that was never seeded.
    assert sorted(SITE_COLUMNS) == [
        entry[0] for entry in PERIOD_TOTAL_WRITE_SITES
    ], (
        f"{SCENARIO}: the site-to-column map and the write-site table name different "
        f"sites - {sorted(SITE_COLUMNS)} against "
        f"{[entry[0] for entry in PERIOD_TOTAL_WRITE_SITES]}. One of the two is wrong "
        f"and neither is authoritative alone."
    )
    agreed = _assert_sites_agree(parity, protocol, sorted(SITE_COLUMNS))
    assert len(agreed) == len(PERIOD_TOTAL_WRITE_SITES), (
        f"{SCENARIO}: {len(agreed)} of the {len(PERIOD_TOTAL_WRITE_SITES)} "
        f"period-total columns were read; all nine must be, or the claim that every "
        f"write path is represented is not measured."
    )

    diff = _table_diff(parity, FOCAL_TABLE)
    sites = "; ".join(
        f"site {number} [{locator}] -> {field} ({guard})"
        for number, locator, field, guard in PERIOD_TOTAL_WRITE_SITES
    )
    assert diff.is_empty, _verdict(
        parity,
        harness,
        bearing=(
            f"THE FINDING IS ON {FOCAL_TABLE}, this scenario's focal table and the one "
            f"Agent Action Plan section 0.6.4 calls the sole writee of the nine "
            f"period-total sites: {sites}. It bears on "
            f"{AMBIGUITY_SYSTOT_OVERLAP} - the table is written both by those nine "
            f"sites and by the menu shell's exit "
            f"path, which the migrated cycle reproduces through `slpl_menu_state` and "
            f"`args.overrewrite` - and on {AMBIGUITY_SYSREC_PINS} for the columns "
            f"re-pinned from the command line over the loaded row. Because this is the "
            f"only scenario that is two dispatches per menu it also bears on "
            f"{AMBIGUITY_SECOND_LEG}. NOTE WHAT THIS TEST DOES NOT SAY: it makes no "
            f"claim about what any total SHOULD be. Do not 'correct' a figure and do "
            f"not add an allowance; record the finding in {DOC_EVIDENCE} and arbitrate "
            f"it against the compiled run (R-6)."
        ),
    )

    #  Row count and column list, stated separately so that a structural finding is not
    #  reported as a value finding. Both are already inside `total_differences`; naming
    #  them makes the message say which kind of disagreement it is.
    assert not diff.row_count_differs, (
        f"{SCENARIO}: {FOCAL_TABLE} holds {diff.cobol_row_count} row(s) on the "
        f"{harness.diff_states.LABEL_COBOL} side and {diff.python_row_count} on the "
        f"{harness.diff_states.LABEL_PYTHON} side. The totals record is seeded by "
        f"`sys4LD` and only ever REWRITTEN by the nine sites, so the count must be "
        f"whatever the seed established, on both sides."
    )
    assert not diff.columns_differ, (
        f"{SCENARIO}: {FOCAL_TABLE}'s column lists disagree - "
        f"{diff.cobol_columns!r} against {diff.python_columns!r}. The schema is frozen "
        f"at [mysql/ACASDB.sql:L1376-L1398] with 21 columns, and rows are POSITIONAL, "
        f"so a list in any other order has no meaningful alignment."
    )


@pytest.mark.database
@pytest.mark.oracle
def test_unconditional_totals_adds_are_reproduced(
    parity: Any, protocol: Any, harness: Any
) -> None:
    """The two adds that sit OUTSIDE their guarded print blocks, reproduced not aligned.

    THE TWO SITES, verbatim from the frozen source:

        sales/sl060.cbl
        L695      if       FS-Cobol-Files-Used and File-18-Exists
        L696               move  "Un-Applied Credits C/F " to  l8-desc
        L697               move  work-b  to  l8-tot
        L698               write  print-record  from  line-8 after 3.
        L700      add      work-b to sl-cn-unappl-this-month.   <- OUTSIDE the guard

        purchase/pl060.cbl
        L623      if       FS-Cobol-Files-Used and File-28-Exists
        L624               move  "Un-Applied Credits C/F " to  l8-desc
        L625               move  work-b  to  l8-tot
        L626               write  print-record  from  line-8 after 3.
        L628      add      work-b to pl-cn-unappl-this-month.   <- OUTSIDE the guard

    That is almost certainly not what the author intended, AND IT IS THE SPECIFICATION.
    R-4: a defect reproduced is correct; a defect fixed is a failure. THEY ARE NOT
    ALIGNED WITH THEIR GUARDS.

    AND THEY MATTER SPECIFICALLY BECAUSE `file_system_used: 1`. That pins
    `File-System-Used` to 1 [copybooks/wssystem.cob:L112-L114], so the condition name
    `FS-Cobol-Files-Used`, declared `value zero`, is FALSE: the two print blocks NEVER
    RUN, and the two totals accumulations STILL HAPPEN. That is the whole reason
    `SYSTOT-REC` changes in this scenario at all under relational mode, and it is why
    these two sites deserve a test of their own rather than being folded into the
    headline.

    The observable is `SYSTOT-REC.SL-CN-UNAPPL-THIS-MONTH` and
    `SYSTOT-REC.PL-CN-UNAPPL-THIS-MONTH`, and the assertion is AGREEMENT between the two
    sides - never a predicted figure.

    Args:
        parity: The completed ten-stage run.
        protocol: The protocol bundle, for the dump reader and the side labels.
        harness: The three harness Python modules, for the deterministic renderer.
    """
    sites = tuple(
        entry
        for entry in PERIOD_TOTAL_WRITE_SITES
        if entry[0] in UNCONDITIONAL_TOTAL_SITES
    )
    assert len(sites) == len(UNCONDITIONAL_TOTAL_SITES), (
        f"{SCENARIO}: the write-site table no longer carries sites "
        f"{UNCONDITIONAL_TOTAL_SITES!r}. Those two are the ones whose `add` sits "
        f"outside the guarded print block immediately above it; losing them from the "
        f"table would lose the reason this test exists."
    )

    #  THE TWO OBSERVABLES THIS TEST OWNS, read from both captures before the verdict:
    #  `SL-CN-UNAPPL-THIS-MONTH` and `PL-CN-UNAPPL-THIS-MONTH`, the receivers of the two
    #  adds that sit outside their guarded print blocks. Under
    #  `file_system_used: 1` the print blocks never run WHILE THESE ADDS STILL DO, so
    #  these two columns are the whole reason the focal table changes at all on this
    #  route - and reading them is what makes this test evidence rather than a third
    #  restatement of the headline.
    _assert_sites_agree(parity, protocol, UNCONDITIONAL_TOTAL_SITES)

    diff = _table_diff(parity, FOCAL_TABLE)
    described = "; ".join(
        f"site {number} [{locator}] -> {field} ({guard})"
        for number, locator, field, guard in sites
    )
    assert diff.is_empty, _verdict(
        parity,
        harness,
        bearing=(
            f"{FOCAL_TABLE} differs, and the two sites this test guards are "
            f"{described}. Both add UNCONDITIONALLY, immediately after a print block "
            f"that is guarded, and under file_system_used = "
            f"{FILE_SYSTEM_USED_MYSQL} the print blocks do NOT run while the adds "
            f"still do. DO NOT 'ALIGN' EITHER ADD WITH ITS GUARD (R-4): a defect "
            f"reproduced is correct and a defect fixed is a failure. "
            f"Record the finding in {DOC_EVIDENCE} and see {DOC_ANOMALIES}."
        ),
    )


@pytest.mark.database
@pytest.mark.oracle
def test_two_receiver_payment_adds_are_reproduced(
    parity: Any, protocol: Any, harness: Any
) -> None:
    """The two `ADD` statements with TWO receivers each, reproduced and never split.

    THE TWO SITES, verbatim and side by side:

        sales/sl100.cbl                        purchase/pl100.cbl
        L402  if oi-type = 5                   L394  if oi-type = 5
        L403       add oi-approp to t-approp    L395       add oi-approp to t-approp
        L404       add oi-paid to t-paid        L396       add oi-paid to t-paid
                       sl-payments                             pl-payments
        L405       add oi-deduct-amt to         L397       add oi-deduct-amt to
                       t-deduct                                t-deduct
        L406  else                              L398  else
        L407   if oi-type = 6                   L399   if oi-type = 6
        L408       add oi-approp to j-approp     L400       add oi-approp to j-approp
        L409       add oi-paid to j-paid         L401       add oi-paid to j-paid
        L410       add oi-deduct-amt to          L402       add oi-deduct-amt to
                       j-deduct.                                j-deduct.

    One `ADD`, two receivers: a working accumulator and the period total. NEITHER IS
    SPLIT INTO TWO STATEMENTS, REORDERED, OR NORMALISED (R-4). `oi-type` 5 is a Payment
    and 6 selects the else-branch, whose three adds go to the `j-` accumulators instead;
    3 is a Credit Note.

    THESE ARE THE TWO SITES THE PROMOTED ANSWER AND THE TWO `Flag-P` LATCHES GATE. If
    either latch is not 2, or the confirmation is not the literal "YES", operations 2
    and 4 post nothing and these are exactly the sites lost - which is why they have
    their own precondition tests and their own test here.

    The observable is `SYSTOT-REC.SL-PAYMENTS` and `SYSTOT-REC.PL-PAYMENTS`, and the
    assertion is AGREEMENT - never a predicted figure.

    Args:
        parity: The completed ten-stage run.
        protocol: The protocol bundle, for the dump reader and the side labels.
        harness: The three harness Python modules, for the deterministic renderer.
    """
    sites = tuple(
        entry
        for entry in PERIOD_TOTAL_WRITE_SITES
        if entry[0] in TWO_RECEIVER_TOTAL_SITES
    )
    assert len(sites) == len(TWO_RECEIVER_TOTAL_SITES), (
        f"{SCENARIO}: the write-site table no longer carries sites "
        f"{TWO_RECEIVER_TOTAL_SITES!r}, the two that accumulate into two receivers in "
        f"one ADD."
    )

    #  THE TWO OBSERVABLES THIS TEST OWNS: `SL-PAYMENTS` and `PL-PAYMENTS`, the second
    #  receiver of each two-receiver `ADD`. They are also the two columns the promoted
    #  confirmation and the two `Flag-P` latches gate, so reading them is what turns
    #  "operations 2 and 4 posted" from a precondition about the YAML into an
    #  observation about the run.
    _assert_sites_agree(parity, protocol, TWO_RECEIVER_TOTAL_SITES)

    diff = _table_diff(parity, FOCAL_TABLE)
    described = "; ".join(
        f"site {number} [{locator}] -> {field} ({guard})"
        for number, locator, field, guard in sites
    )
    assert diff.is_empty, _verdict(
        parity,
        harness,
        bearing=(
            f"{FOCAL_TABLE} differs, and the two sites this test guards are "
            f"{described}. Each is ONE `ADD` with TWO receivers; DO NOT SPLIT EITHER "
            f"INTO TWO STATEMENTS and do not reorder them (R-4). They are also the "
            f"two sites the "
            f"promoted answer {ANSWER_KEY_PAYMENT_CONFIRM} = "
            f"{ANSWER_PAYMENT_CONFIRM!r} and the two `Flag-P` latches gate, so check "
            f"those preconditions before reading this as an arithmetic finding. "
            f"Ambiguity {AMBIGUITY_PAYMENT_CONFIRM}."
        ),
    )


@pytest.mark.database
@pytest.mark.oracle
def test_invoice_headers_are_stamped_on_both_ledgers(
    parity: Any, harness: Any
) -> None:
    """The invoice header stamps agree - and the one-versus-two divergence stands.

    THE DIVERGENCE, verbatim:

        sales/sl055.cbl                          purchase/pl055.cbl
        L679  move "Z" to ih-status.             L586  move "Z" to ih-status.
        L680  move "A" to ih-status-A.                   *> 07/01/18 was "z"
        L681  write oi-header.  *> OTM2          L587  write open-item-record-4.

    SALES WRITES TWO STATUS FIELDS AND PURCHASE WRITES ONE, and that is not harmonised
    (R-4). The same pair of programs also disagrees about how the invoice amount is
    built: Sales sums NINE addends across three continuation lines
    [sales/sl055.cbl:L671-L673] and Purchase sums FOUR on one line
    [purchase/pl055.cbl:L580], both under `if ih-type not = 1`
    [sales/sl055.cbl:L670], [purchase/pl055.cbl:L579], which excludes Receipts. Those
    sums are what sites 1, 2, 6 and 7 accumulate.

    THE FOUR TABLES ARE ON THE BOUND BECAUSE OF THESE STAMPS, and the stamps are why
    normalisation's FIRST job is genuinely active here: `ih-status` and `ih-status-A`
    surface as single-character columns, and `char(1)` IS in that job's scope - trailing
    spaces only, because a COBOL alphanumeric `MOVE` is left-justified with right
    padding, so leading spaces are content. The same job carries A-12, whose second
    instance is in a table on this bound: [copybooks/slwsoi.cob:L32] to
    [common/otm3MT.cbl:L310] to [mysql/ACASDB.sql:L905].

    Args:
        parity: The completed ten-stage run.
        harness: The three harness Python modules, for the deterministic renderer.
    """
    for table, stamp in (
        ("SAINVOICE-REC", "TWO status fields [sales/sl055.cbl:L679-L681]"),
        ("SAINV-LINES-REC", "the Sales lines written with the header"),
        ("PUINVOICE-REC", "ONE status field [purchase/pl055.cbl:L586-L587]"),
        ("PUINV-LINES-REC", "the Purchase lines written with the header"),
    ):
        diff = _table_diff(parity, table)
        assert diff.is_empty, _verdict(
            parity,
            harness,
            bearing=(
                f"THE FINDING IS ON {table}, which is on the bound because the extract "
                f"programs stamp the invoice header: {stamp}. DO NOT HARMONISE THE "
                f"ONE-VERSUS-TWO DIVERGENCE (R-4) - Sales writes `ih-status` AND "
                f"`ih-status-A`, Purchase writes `ih-status` alone - and do not "
                f"reconcile the nine-addend sum [sales/sl055.cbl:L671-L673] with the "
                f"four-addend one [purchase/pl055.cbl:L580]. If the difference is only "
                f"trailing space in a `char` column, that is normalisation's first job "
                f"and it is applied identically to both sides, so a surviving "
                f"difference is a real one."
            ),
        )


@pytest.mark.database
@pytest.mark.oracle
def test_open_items_are_rewritten_on_both_ledgers(parity: Any, harness: Any) -> None:
    """The open-item files agree after both cash programs walk and rewrite them.

    THE TWO SITES:

        sales/sl100.cbl                        purchase/pl100.cbl
        L412  move oi-approp to oi-paid.       L404  move oi-approp to oi-paid.
        L413  perform Sales-Rewrite.           L405  perform Purch-Rewrite.

    NOTE WHICH VERBS EACH PROGRAM ACTUALLY USES, because it bounds what can change:
    `pl100` performs `Purch-Rewrite` and NO `Purch-Write`, and `sl100` performs
    `Sales-Rewrite` and neither `Sales-Write` nor `OTM3-Write`. So the open-item and
    ledger rows these two programs touch are REWRITTEN IN PLACE and never inserted, and
    a row appearing on one side only is a structural finding rather than a value one.

    A REWRITE FAILURE IS DELIBERATELY IGNORED BY THE FROZEN PROGRAM. The maintainer's
    own comment at [sales/sl100.cbl:L415] records that for a non-existent Sales record
    the rewrite will fail and the error is ignored, so a missing customer produces no
    diagnostic and no database effect - reproduced, not improved on (R-4).

    ONE NORMALISATION SUBTLETY THAT APPLIES TO EXACTLY THESE TWO TABLES: `char(8)` DOES
    NOT IMPLY DATE. `SAITM3-REC.OI3-BATCH` and `PUITM5-REC.OI5-BATCH` are batch
    references and are explicitly EXCLUDED from the date-text allow-list even though
    both tables are on this bound, so job 3 leaves them alone and a difference in either
    is a real difference.

    Args:
        parity: The completed ten-stage run.
        harness: The three harness Python modules, for the deterministic renderer.
    """
    for table, locator, verb in (
        ("SAITM3-REC", "sales/sl100.cbl:L412-L413", "Sales-Rewrite, and no write verb"),
        (
            "PUITM5-REC",
            "purchase/pl100.cbl:L404-L405",
            "Purch-Rewrite, and no write verb",
        ),
    ):
        diff = _table_diff(parity, table)
        assert diff.is_empty, _verdict(
            parity,
            harness,
            bearing=(
                f"THE FINDING IS ON {table}. The cash program walks the open items and "
                f"rewrites them at [{locator}] using {verb}, so a row present on one "
                f"side only is a STRUCTURAL finding and not a value one. Its "
                f"`char(8)` batch-reference column is deliberately excluded from the "
                f"date-text allow-list, so job 3 did not touch it. Note that the "
                f"frozen program ignores a rewrite failure outright "
                f"[sales/sl100.cbl:L415], which is reproduced and not improved on "
                f"(R-4)."
            ),
        )

    #  The two ledger tables the same programs rewrite, and where the three
    #  moving-average anomalies land. Their arithmetic is locked in
    #  `tests/arithmetic/test_compute_truncate_unrounded.py`; what is asserted here is
    #  the end state those computations produce.
    for table, side in (("SALEDGER-REC", "customer"), ("PULEDGER-REC", "supplier")):
        diff = _table_diff(parity, table)
        assert diff.is_empty, _verdict(
            parity,
            harness,
            bearing=(
                f"THE FINDING IS ON {table}, where the posting programs rewrite the "
                f"{side} statistics. THREE ANOMALIES LAND HERE AND ALL THREE ARE "
                f"REPRODUCED, NEVER FIXED (R-4): A-8, the double truncation of the "
                f"moving average, where pence are lost into a zero-decimal accumulator "
                f"and the remainder is then lost by an integer divide; A-9, the "
                f"credit-note path that never increments its activity counter; and "
                f"A-10, the three mutually inconsistent guards on one idiom, which "
                f"also differ in whether and when they increment the counter - the "
                f"cash path's divide is merely SPELLED the other way round and "
                f"computes the same accumulator-over-counter quotient. Their "
                f"arithmetic is locked in "
                f"`tests/arithmetic/test_compute_truncate_unrounded.py` - if that "
                f"suite passes and this does not, the difference is in the end state "
                f"rather "
                f"than the computation. A-11 also bears on this table: a signed "
                f"`binary-long` narrows to an unsigned host variable and an unsigned "
                f"column, LOSING ITS SIGN AT THE BRIDGE and not at the database, and "
                f"that question is open as Q-3. On {table}, note that "
                f"`SALES-STATS-DATE` is the ONE column on this bound that "
                f"normalisation's third job touches."
            ),
        )


@pytest.mark.database
@pytest.mark.oracle
def test_deduction_analysis_tables_agree(parity: Any, harness: Any) -> None:
    """The deduction analysis agrees - site 3 and the value-file path it opens.

    SITE 3 IS UNCONDITIONAL:

        sales/sl060.cbl
        L638      move    "           Total  Amount Late Deductions" to line-6.
        L639      move     total-deduct to l6-net.
        L640      write    print-record from line-6 after 2.
        L641      add      total-deduct to sl-credit-deductions.   <- SITE 3

    AND THE VALUE FILE IS TOUCHED ONLY WHEN THERE IS SOMETHING TO ANALYSE:

        L643      if       total-deduct not = zero
        L644               perform Value-Open
        L645               perform ba000-Analise-Deductions
        L646               perform Value-Close
        L647      end-if

    So `VALUEANAL-REC` changes only when the seed carries at least one deduction, which
    the seed contract requires precisely so that site 3 is an add of something rather
    than an add of zero. `ANALYSIS-REC` must hold every analysis code the seeded
    invoices reference, on both sides, or the indexed reads do not find them and the run
    stops short of the sites that matter.

    THE ASSERTION IS AGREEMENT. Nothing here recomputes a deduction, apportions one, or
    checks that the analysis totals reconcile against the invoice lines.

    Args:
        parity: The completed ten-stage run.
        harness: The three harness Python modules, for the deterministic renderer.
    """
    for table in ("ANALYSIS-REC", "VALUEANAL-REC"):
        diff = _table_diff(parity, table)
        assert diff.is_empty, _verdict(
            parity,
            harness,
            bearing=(
                f"THE FINDING IS ON {table}: {TABLE_REASONS[table]}. Site 3 adds "
                f"unconditionally at [sales/sl060.cbl:L641] and the value file is "
                f"opened, analysed and closed only when `total-deduct` is non-zero "
                f"[sales/sl060.cbl:L643-L647]. If the table is EMPTY on both sides the "
                f"seed carries no deduction, which means site 3 added zero and this "
                f"scenario proved less than it should - check the seed contract before "
                f"reading the result as a pass."
            ),
        )


@pytest.mark.database
@pytest.mark.oracle
def test_general_ledger_fan_out_tables_agree(parity: Any, harness: Any) -> None:
    """The General Ledger batch, posting and transfer tables agree in pure-GL mode.

    THE FAN-OUT SWITCH IS PINNED TO A SPACE, so this run is pure General Ledger:
    `GLBATCH-REC` and `GLPOSTING-REC` are written by the Sales and Purchase posting
    programs, and `PSIRSPOST-REC` is only OPENED AND CLOSED - it must come back exactly
    as seeded. Under "Y" or "B" [copybooks/wssystem.cob:L179-L181] the fan-out would
    change which tables move, which is why the pin is load-bearing for the bound.

    A-1 IS WHY `PSIRSPOST-REC` IS NOT SYMMETRIC BETWEEN THE TWO LEDGERS, and it is
    cross-referenced here rather than owned here. The missing terminating period at
    [sales/sl060.cbl:L1176] nests [sales/sl060.cbl:L1177-L1178] inside the L1175
    conditional, so in pure General Ledger mode `sl060` closes neither the transfer file
    nor the posting file; `pl060`'s counterpart at [purchase/pl060.cbl:L1031] HAS its
    period. The two are locked by `tests/scenarios/test_clean_batch_post_sl.py` and
    `tests/scenarios/test_clean_batch_post_pl.py`; this test only requires that whatever
    the compiled cycle left behind, the migrated cycle left the same.

    A-17 ALSO WRITES HERE, AND ITS EFFECT CROSSES OPERATIONS. `move RRN to postings.
    *> Why ?` [sales/sl060.cbl:L1173] carries the maintainer's own question mark, and
    the value it stores is READ BACK by a later operation of this very sequence
    [purchase/pl100.cbl:L564]. That is ambiguity Q-A17-POSTINGS-EFFECT, and it is one of
    the reasons the four-operation order is part of the specification.

    Args:
        parity: The completed ten-stage run.
        harness: The three harness Python modules, for the deterministic renderer.
    """
    for table in ("GLBATCH-REC", "GLPOSTING-REC", "PSIRSPOST-REC"):
        diff = _table_diff(parity, table)
        assert diff.is_empty, _verdict(
            parity,
            harness,
            bearing=(
                f"THE FINDING IS ON {table}: {TABLE_REASONS[table]}. The fan-out "
                f"switch is pinned to {IRS_INSTEAD_GL_ONLY!r}, pure General Ledger, so "
                f"PSIRSPOST-REC should come back exactly as seeded while GLBATCH-REC "
                f"and GLPOSTING-REC are written. Two anomalies bear on this: A-1 at "
                f"[sales/sl060.cbl:L1176], whose missing period stops sl060 closing "
                f"either file in this mode, and A-17 at [sales/sl060.cbl:L1173], whose "
                f"stored value is read back by a LATER operation of this sequence "
                f"[purchase/pl100.cbl:L564] - ambiguity {AMBIGUITY_A17_EFFECT}. Both "
                f"are reproduced, never fixed. Note also that the transfer-file "
                f"handler rejects rewrite, read-indexed, start and delete "
                f"UNCONDITIONALLY at entry [common/acas008.cbl:L299-L307], so its "
                f"published Rewrite verb can never succeed on either side."
            ),
        )


@pytest.mark.database
@pytest.mark.oracle
def test_dump_is_wellformed_on_both_sides(
    parity: Any, harness: Any, frozen_schema: Mapping[str, Mapping[str, Any]]
) -> None:
    """Every dump on both sides has the shape the protocol guarantees.

    THE SHAPE, from `harness/dump_tables.py`'s `DUMP_KEYS`: exactly FIVE keys in fixed
    insertion order - `table`, `primary_key`, `columns`, `row_count`, `rows` - AND NO
    OTHERS. No timestamp, no server version, no scenario name and no side; THE SIDE IS
    RECORDED IN THE PATH, never in a file, because a side recorded in the data would
    make the two files differ by construction. `columns` is in schema ordinal order and
    is never sorted; `rows` is a list of lists in PRIMARY-KEY-ASCENDING order,
    positionally aligned with `columns`. DECIMAL values are canonical JSON STRINGS at
    the declared scale, never JSON numbers and never exponent notation (R-2); integers
    are JSON integers.

    THE STRUCTURAL CHECK IS DELEGATED, not reimplemented: `harness/diff_states.py`'s
    `load_dump` is the single definition of it and asserts the five keys in order, the
    table in the 22-name allow-list, `primary_key` present in `columns`,
    `row_count == len(rows)`, every row of `len(columns)` values, NO value a float
    (R-2), NO value null, and no primary-key value twice. Every one of those failures is
    exit 2 in the protocol - a comparison that could not be performed - which is an
    ERROR and never a pass.

    WHY IT IS WORTH ASSERTING SEPARATELY FROM THE DIFF. The comparison would report
    "identical" for two dumps that were both malformed in the same way, so the shape is
    checked against the FROZEN SCHEMA rather than against the other side: the column
    list must match `mysql/ACASDB.sql`'s ordinal order exactly, because rows are
    positional and a list in any other order has no meaningful alignment.

    Args:
        parity: The completed ten-stage run.
        harness: The three harness Python modules.
        frozen_schema: `mysql/ACASDB.sql` parsed into `{table: {column: ColumnType}}`.
            READ AND NEVER WRITTEN - Agent Action Plan section 0.8.1 makes any diff
            against that file a defect in the migration.
    """
    diff_states = harness.diff_states
    normalize = harness.normalize
    expected_keys = tuple(harness.dump_tables.DUMP_KEYS)

    for side in (diff_states.LABEL_COBOL, diff_states.LABEL_PYTHON):
        tree = parity.paths.normalized_dir(side)
        for table in parity.tables:
            where = f"{SCENARIO}/{side}/{table}"
            path = tree / diff_states.dump_filename(table)

            #  The single definition of the structural contract, and every failure it
            #  raises is a comparison that could not be performed.
            dump = diff_states.load_dump(path)

            assert tuple(dump) == expected_keys, (
                f"{where}: the dump's keys are {tuple(dump)!r} where the protocol "
                f"guarantees exactly {expected_keys!r}, in that order and no others. "
                f"The side is recorded in the PATH and never in the file."
            )

            columns = tuple(str(name) for name in dump["columns"])
            expected_columns = normalize.schema_columns(frozen_schema, table)
            assert columns == expected_columns, (
                f"{where}: the column list disagrees with the frozen schema. The dump "
                f"says {columns!r} and mysql/ACASDB.sql says {expected_columns!r}. "
                f"Rows are POSITIONAL, so a list in any other order has no meaningful "
                f"alignment."
            )

            assert dump["row_count"] == len(dump["rows"]), (
                f"{where}: `row_count` is {dump['row_count']!r} against "
                f"{len(dump['rows'])} row(s)."
            )

            #  PRIMARY-KEY-ASCENDING order. Compared only when every key is of one
            #  type, because a mixed-type key set is itself a finding the differ
            #  reports through its key-type comparison, and ordering two types has no
            #  defined meaning.
            key_index = columns.index(str(dump["primary_key"]))
            keys = [row[key_index] for row in dump["rows"]]
            if len({type(key).__name__ for key in keys}) <= 1:
                assert keys == sorted(keys), (
                    f"{where}: the rows are not in primary-key-ascending order on "
                    f"`{dump['primary_key']}`. The dump is "
                    f"`SELECT * FROM <table> ORDER BY <primary key>` with no "
                    f"tie-breaking, which is deterministic by construction because "
                    f"every in-scope table has a single-column primary key and zero "
                    f"secondary indexes."
                )

            #  DECIMAL values arrive as canonical JSON STRINGS at the declared scale.
            #  This is rule R-2 at the wire, and it is what lets the comparison be
            #  exact: `1` and `\"1\"` ARE a difference, and no numeric coercion is
            #  applied anywhere in the diff path.
            for column in columns:
                declared = normalize.column_type(frozen_schema, table, column)
                if declared.kind != normalize.KIND_DECIMAL:
                    continue
                ordinal = columns.index(column)
                for row_index, row in enumerate(dump["rows"]):
                    value = row[ordinal]
                    assert isinstance(value, str), (
                        f"{where}: row {row_index}, column `{column}` "
                        f"({declared.sql_type} at "
                        f"[mysql/ACASDB.sql:L{declared.line}]) is "
                        f"{type(value).__name__} where a DECIMAL must arrive as a "
                        f"canonical JSON STRING at scale {declared.scale}. A JSON "
                        f"number would invite a binary-radix round trip, which R-2 "
                        f"forbids outright."
                    )


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
    exercised end to end, over THIS scenario's own declared bound.

    IT ASSERTS NOTHING WHATEVER ABOUT THE MIGRATION. The trees are SYNTHETIC, built from
    the frozen schema's own column lists, so the machinery under test is the shipped
    machinery - but a verdict taken from a hand-built tree is not protocol evidence, and
    none is claimed. That is also why this test needs no Compose stack and no compiled
    oracle: it executes on a bare host.

    THE ZERO-BYTE GUARANTEE IS ASSERTED DIRECTLY as well: the deterministic renderer
    returns THE EMPTY STRING for a comparison with no findings, which is the same
    emptiness a passing stage 10 writes to `diff.txt`.

    THE COMPARISON IS EXACT. Two labels only, `cobol` and `python`, and they are not
    configurable; rows align by primary-key VALUE and never by position; and
    `--max-differences` truncates the report only, always printing the true total and
    never changing the exit code. There is no tolerance, no epsilon, no case or
    whitespace insensitivity and no numeric coercion anywhere in the path.

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
    assert len(set(observed)) == 3, (
        "two of the three exit statuses are equal, so 'could not compare' and one of "
        "the two verdicts would be indistinguishable. That conflation is the single "
        "worst bug available in this tree."
    )

    assert (diff_states.LABEL_COBOL, diff_states.LABEL_PYTHON) == (
        "cobol",
        "python",
    ), (
        f"the report labels are "
        f"({diff_states.LABEL_COBOL!r}, {diff_states.LABEL_PYTHON!r}) where they must "
        f"be ('cobol', 'python'). They are the specification side and the migrated "
        f"side respectively, and they are not configurable."
    )

    #  EXIT 0 MEANS ZERO BYTES. An empty comparison renders to the empty string, which
    #  is exactly what a passing stage 10 writes.
    empty = diff_states.TreeDiff(tables=())
    assert empty.is_empty, (
        "a comparison with no tables reports itself non-empty, so `is_empty` no longer "
        "means what the pass condition of Agent Action Plan section 0.8.5 needs it to."
    )
    assert empty.total_differences == 0, (
        f"an empty comparison reports {empty.total_differences} finding(s)."
    )
    assert diff_states.render(empty) == "", (
        f"the deterministic renderer produced {diff_states.render(empty)!r} for a "
        f"comparison with no findings, where exit 0 requires EMPTY output - zero "
        f"bytes, not a banner. The evidence in {DOC_EVIDENCE} distinguishes 'compared, "
        f"and "
        f"identical' from 'never compared' by exactly that emptiness."
    )


def test_a2_a3_quarter_handling_is_not_reconciled_here(
    scenario_loader: Callable[[str], Mapping[str, Any]],
) -> None:
    """A-2 and A-3 are NOT exercised by this scenario, and that is recorded not implied.

    DOCUMENTATION ONLY, AND IT NEEDS NO STACK. Both anomalies live in gl080, which
    THIS scenario does not drive, so neither can be observed HERE. ⚠️ NARROWED: this
    previously said `gl_end_of_cycle` "is driven by NO scenario file at all", which is
    false, and the correction changes where each anomaly is locked:
      A-2, the unbounded quarter subscript, IS owned by
        `tests/arithmetic/test_gl080_cycle_divide_rounded.py` and is deliberately never
        driven through the compiled oracle, because an out-of-range subscript is a write
        into adjacent storage whose effect is undefined.
      A-3, the second rotating quarter counter, is ALSO witnessed in TABLE STATE by
        `end_of_cycle_gl`, whose suite asserts it as a positive fact
        [tests/scenarios/test_end_of_cycle_gl.py "ANOMALY A-3, asserted as a positive
        fact about the state"] - seeding the counter and the subscript to disagree and
        observing that the subscript writes Q1 while the counter writes Ledger-Last.
    Both remain locked arithmetically in
    `tests/arithmetic/test_gl080_cycle_divide_rounded.py`.

        L328      divide   scycle by period giving a rounded.     <- A-2, the ROUNDED
                                                                    divide
        L329      multiply a  by  period  giving  y.
        L345      move     ledger-balance  to  ledger-q (a).      <- A-2, the UNBOUNDED
                                                                    subscript
        L346      if       current-quarter = 4
        L347               move  ledger-balance  to  ledger-last.
        L355      add      1  to  current-quarter.                <- A-3, the rotating
                                                                    counter
        L356      if       current-quarter = 5
        L357               move  1  to  current-quarter.

    A-2 is one of the five `ROUNDED` sites in the whole in-scope cycle, and the
    subscript it produces indexes an array with NO BOUNDS CHECK. A-3 is that the program
    carries a second and INDEPENDENT notion of "current quarter" beside the computed
    subscript; the anomaly register's corrected-locator table records that there are at
    least FOUR such notions rather than the two the plan named, the others being
    [general/gl080.cbl:L358-L360] and [general/gl080.cbl:L361-L363].

    DO NOT BOUNDS-CHECK THE SUBSCRIPT AND DO NOT RECONCILE THE COMPETING NOTIONS OF
    "CURRENT QUARTER" (R-4). What the compiled program writes when the subscript runs
    past the record's end was ambiguity Q-19, also carried as Q-QUARTER-SUBSCRIPT, and
    it is now MEASURED: `move 999.99 to ledger-q (13)' stores the six packed bytes
    `00 00 00 99 99 9C' at 1-based offsets 125-130 of the 126-byte GLLEDGER record --
    two of them inside the trailing `filler pic x(50)', FOUR of them past the end of
    the record -- leaves Q1..Q4 and Ledger-Last untouched, emits no diagnostic and
    exits 0. Occurrence 14 lands at 131-136, so the addressing is linear and does not
    wrap. The consequence for THIS scenario is unchanged and is what makes the
    measurement worth citing here: an overrunning store moves no column of any of the
    22 compared tables, so it could never appear in a state diff. The measurement is
    recorded in `acas_posting/cobol/move.py` as
    `UNCHECKED_SUBSCRIPT_ORACLE_EVIDENCE` and asserted in
    `tests/arithmetic/test_gl080_cycle_divide_rounded.py`.

    THE CONSEQUENCE THIS TEST ACTUALLY ASSERTS is the one fact that makes the omission
    verifiable from here: because gl080 is not driven here, `system.period` is INERT, and
    no operation of this scenario is `gl_end_of_cycle`.

    Args:
        scenario_loader: `yaml.safe_load` of one scenario definition.
    """
    definition = scenario_loader(SCENARIO)
    operations = _sequence(definition, KEY_OPERATIONS)

    assert "gl_end_of_cycle" not in operations, (
        f"{SCENARIO}: `gl_end_of_cycle` is among this scenario's operations "
        f"({operations!r}) and must not be. gl080 is Phase 3 (Transaction Deletion) "
        f"plus Phase 5 (End of Period Processing), it promotes THREE interactive "
        f"answers, and driving it would make the totals attribution ambiguous - "
        f"whereas the nine in-scope write sites make the totals attributable to one "
        f"table "
        f"without it (Agent Action Plan section 0.6.4). The decision is recorded at "
        f'[harness/scenarios/{SCENARIO}.yaml "gl_end_of_cycle IS DELIBERATELY NOT '
        f'APPENDED TO THIS SCENARIO"] and belongs in '
        f"{DOC_AMBIGUITIES}. A-2 and A-3 are locked in "
        f"`tests/arithmetic/test_gl080_cycle_divide_rounded.py`, not here; the "
        f"question that was {AMBIGUITY_QUARTER_SUBSCRIPT[0]}, also carried as "
        f"{AMBIGUITY_QUARTER_SUBSCRIPT[1]}, has since been measured against the "
        f"compiled oracle and is settled."
    )

    system = _block(definition, KEY_SYSTEM)
    assert system[SYS_PERIOD] == PERIOD_INERT_VALUE, (
        f"{SCENARIO}: `system.period` is {system[SYS_PERIOD]!r}. It is INERT precisely "
        f"because gl080 is not driven here - the only in-scope divide by it is "
        f"[general/gl080.cbl:L328], which is A-2's `ROUNDED` divide - so it is carried "
        f"at {PERIOD_INERT_VALUE} for key-set uniformity and for the seeded system "
        f"record, and nothing here reconciles it with the rotating counter at "
        f"[general/gl080.cbl:L355-L357]."
    )


@pytest.mark.database
@pytest.mark.oracle
def test_system_record_parity_by_digest_as_well_as_by_dump(parity: object, protocol: object) -> None:
    """THE PARAMETER ROW IS BOUNDED TWICE - by the dump, and by a digest of it.

    WHAT THIS CLOSES. An earlier draft kept `SYSTEM-REC` off every scenario's
    `affected_tables` and justified that by claiming no side writes it. That claim is
    FALSE:
    `acas_posting/cli/args.py`'s `overrewrite` reproduces
    [general/general.cbl:L656-L672] and every one of the seven routes calls it, so the
    parameter row is written on BOTH sides of every scenario. Until this assertion
    existed, a regression in that persistence produced an EMPTY DIFF and a green run.

    WHICH KEYS THIS ROUTE WRITES, AND HOW OFTEN. All four declared operations bind
    `slpl_menu_state`, so each one rewrites KEY 1 (`SYSTEM-REC`) and KEY 4
    (`SYSTOT-REC`) and never KEY 2 - four dispatches, four persistences, on each side.
    `SYSTOT-REC` is dumped and compared directly; KEY 1 is what this test bounds, and it
    is the row the two one-shot posting latches live in
    [copybooks/wssystem.cob:L206, L226].

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
