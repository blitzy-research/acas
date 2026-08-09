"""THE SALES CLEAN-BATCH STATE-PARITY TEST, AND ANOMALY A-1'S STATE WITNESS.

 THIS FILE IS A-1's WITNESS, NOT ITS LOCK, and the header below says so wherever it
matters. `GL-Posting-Close` writes nothing, so adding the missing period
at [sales/sl060.cbl:L1176] leaves an IDENTICAL `GLPOSTING-REC` and every assertion here
still passes. The LOCK is
`tests/arithmetic/test_double_entry_explosion.py`, which drives the shipped
`ca000-BL-Close` over the whole `IRS-Instead` × `Level-1` truth table with a recording
facade stand-in and fails on exactly the row the two readings disagree about. What THIS
file establishes is different and still worth having: that two independent
implementations agree on `GLPOSTING-REC` on the one route where A-1 is reachable at all.

Scenario `clean_batch_sl`, subsystem `sales`, operation `sl_invoice_post` - the two
in-scope programs `sl055` then `sl060`. It drives the ten-stage parity protocol and
asserts an EMPTY ORDERING-NORMALISED DIFF between the compiled COBOL oracle and the
migrated Python cycle, which Agent Action Plan section 0.8.5 makes the only pass
condition.

THE SIX BINDING RULES R-1 to R-6 live in Agent Action Plan section 0.7.2, and their
exact wording is retrievable from the requirements via `review_prompt`. Where they are
silent, enterprise-standard best practice applies. Each rule is named below at the site
that honours it.

THE INVERTED PREMISE, WHICH GOVERNS THIS FILE ABOVE ALL OTHERS. Agent Action Plan
section 0.8.2, verbatim: "There is no test suite: compiled COBOL execution is the
behavioral specification, defects included. A defect reproduced is correct; a defect
fixed is a failure." The corollary is the whole design of this file: A TEST THAT
ASSERTS CORRECT ACCOUNTING RATHER THAN OBSERVED BEHAVIOUR IS ITSELF A DEFECT. Every
assertion below is framed as "the two sides agree", never as "the figure is right".
No test here recomputes a monetary value, and none asserts that a ledger balances.

WHY THE EMPTY-DIFF ASSERTION IS TRUSTWORTHY. Agent Action Plan section 0.6.6: "a
non-empty diff is always a real behavioral difference and never an artefact of the
comparison." That is earned rather than assumed - every in-scope table has a
SINGLE-COLUMN primary key, zero secondary indexes, no `TIMESTAMP` column and no
`AUTO_INCREMENT`, so the dump is `SELECT * FROM <table> ORDER BY <primary key>` with no
tie-breaking, no timestamp masking and no surrogate-key remapping.

-------------------------------------------------------------------------------
THE ROUTE, AND ITS FOUR STRUCTURAL PECULIARITIES
-------------------------------------------------------------------------------

`sl_invoice_post` IS `load07`, AND IS NOT THE EIGHTH MENU PARAGRAPH.
[sales/sales.cbl:L756-L768] verbatim:

    L756  load07.             *> Sales trans posting
    L759       move     "sl830" to WS-Called.   *> In case autogen is use
    L760       perform  load00.
    L761       if       ws-term-code not = zero
    L762                go to display-menu.
    L763       move     "sl055" to ws-called.
    L764       perform  load000.
    L765       if       ws-term-code not = zero
    L766                go to display-menu.
    L767       move     "sl060" to ws-called.
    L768       go       to load000.

THE EIGHTH PARAGRAPH, at [sales/sales.cbl:L770-L774], dispatches the OUT-OF-SCOPE
`sl080` (Payment Input) instead. The menu-letter proof is direct:
[sales/sales.cbl:L545] displays "(G)  Sales Transactions Post", the SEVENTH letter,
hence the seventh paragraph; and [sales/sales.cbl:L546] displays "(H)  Payment
Input", the eighth, hence the eighth. Citing that eighth paragraph name against Sales
anywhere is an error, so this file does not write it at all - not even to deny it.

ONE. `sl830` IS A GUARDED NO-OP ON THE COBOL SIDE AND ABSENT FROM THE PYTHON SIDE.
[sales/sales.cbl:L759] dispatches it before `sl055`, but the `sl800` to `sl830`
automatic-generation series is explicitly out of scope (Agent Action Plan section 0.2.2)
and `acas_posting/cli/sl_invoice_post.py` dispatches only `sl055` then `sl060`. It is
harmless in practice - [sales/sl830.cbl:L269-L270] verbatim:

    L269       if       SL-Autogen not = "Y"    *> SL Autogen not in use
    L270                goback.

and the scenario pins `sl_autogen` to a space, so the program returns immediately. The
resolution is structural rather than tolerated: the four automatic-generation tables are
NEVER SEEDED and appear on NO affected-table list, and both runners assert after their
run that `SAAUTOGEN-REC`, `SAAUTOGEN-LINES-REC`, `PUAUTOGEN-REC` and
`PUAUTOGEN-LINES-REC` are still empty. `test_autogen_tables_untouched` below asserts the
list-level half of that. Purchase's `pl830` is COMMENTED OUT
[purchase/purchase.cbl:L755-L758] - another divergence PRESERVED AND NOT HARMONISED
(R-4).

TWO. THE SALES ABORT GATE FIRES TWICE, and the four ledgers disagree about the gate in
four different ways. Sales tests `if ws-term-code not = zero` at BOTH
[sales/sales.cbl:L761-L762] and [sales/sales.cbl:L765-L766]; General tests
`if ws-term-code = 5` [general/general.cbl:L810-L811]; Purchase has NO gate at all, its
copy being commented out [purchase/purchase.cbl:L755-L758]; and IRS has neither a gate
nor a dispatch wrapper. DO NOT HARMONISE THEM.

    A verified subtlety worth stating, because it is what makes this scenario's
    `expected_status` provable rather than hopeful. `WS-Term-Code` is `pic 99`
    [copybooks/wscall.cob:L10], so `load000`'s two bands - `if ws-term-code < 8`
    [sales/sales.cbl:L708-L709] and `if ws-term-code > 7`
    [sales/sales.cbl:L710-L712] - are EXHAUSTIVE AND MUTUALLY EXCLUSIVE over the
    whole domain. Term code 8 never reaches `load07`'s own gate, because the `> 7`
    band terminates the run first. And 8 is itself unreachable on this route,
    because both of its raise sites sit inside `if FS-Cobol-Files-Used`
    ([sales/sl055.cbl:L326] wrapping [sales/sl055.cbl:L344];
    [purchase/pl055.cbl:L266] wrapping [purchase/pl055.cbl:L286]) while the
    scenario pins `file_system_used` to 1. So a declared expected status of zero
    is provable, not assumed.

THREE. THE MENU SHELL'S EXIT PATH IS ASYMMETRIC BETWEEN LEDGERS, and the asymmetry
decides which system tables can appear on any affected-table list.
[sales/sales.cbl:L628-L641] `overrewrite` persists KEY 1 AND KEY 4 ONLY - `move 1 to
File-Key-No` at L631 and `move 4 to File-Key-No` at L636 - AND NEVER KEY 2, whereas
[general/general.cbl:L656-L691] persists keys 1, 2 and 4. That is why `SYSDEFLT-REC`
appears on NO scenario's list. `load000` performs `overrewrite` effectively
unconditionally, from both of its exhaustive bands, AND SO DOES THE MIGRATED SIDE:
`acas_posting/cli/args.py`'s `overrewrite` is called by every one of the seven routes,
and `slpl_menu_state` carries the totals record, so keys 1 and 4 are written on BOTH
sides here. A census across all twelve in-scope PROGRAMS finds ZERO `System-*` facade
verbs, so no migrated program persists a system record - only the menu-exit path does.
`SYSDEFLT-REC` and `SYSFINAL-REC` are on no list at all because nothing on either side
writes them; `SYSTOT-REC` IS listed here, and the ambiguity that governs it is recorded
under THE TWO ORACLE-ARBITRATED QUESTIONS below; and `SYSTEM-REC` is bounded BY
FINGERPRINT rather than by dump, because `RDBMS-PASSWD char(12)`
[copybooks/wssystem.cob:L139] is one of its columns and a dump is `SELECT *`. Both
runners digest it before and after every run and `protocol.assert_system_record_parity`
compares the two sides' post-run digests over all 169 columns.

FOUR. BOUNDING IS DONE BY ALL 22 IN-SCOPE TABLES, WHICH IS THE PROTOCOL, and the
affected-table list is the scenario's DECLARED EFFECT rather than the bound. There is
no ignore-list, no tolerance-list and no "known difference" allowance anywhere in this
file or in the diff path it drives. Every in-scope table is compared, and each is
compared exactly.

-------------------------------------------------------------------------------
A-1 - THE MISSING TERMINATING PERIOD.  THE HEADLINE, AND WHY THIS FILE EXISTS
-------------------------------------------------------------------------------

[sales/sl060.cbl] `ca000-BL-Close section.` opens at L1158. Verbatim:

    L1161       perform  GL-Batch-Write                     *>   write Batch-record.
    L1162-L1171 <the fs-reply error block, ending `end-if`>
    L1172       if       IRS-Both-Used OR G-L    *> THIS IS IN PURCHASE PL060
    L1173                move     RRN  to  postings.     *> Why ?   <- PERIOD ends IF#1
    L1174       perform  GL-Batch-Close.                            <- unconditional
    L1175       if       IRS-Used OR IRS-Both-Used                  <- IF#2 opens
    L1176                perform SPL-Posting-Close                  <- ** NO PERIOD **
    L1177       if       IRS-Both-Used or G-L                       <- IF#3 NESTED in #2
    L1178                perform GL-Posting-Close.                 <- closes BOTH ifs
    L1180  ca999-main-exit.

Because L1176 carries NO terminating period, IF#3 is nested INSIDE IF#2. So
`GL-Posting-Close` executes only when

    (`IRS-Used` OR `IRS-Both-Used`)  AND  (`IRS-Both-Used` OR `G-L`)

and IN PURE GENERAL LEDGER MODE IF#2 IS FALSE, SO IT NEVER EXECUTES AT ALL.

THE THREE CONTROLS, EACH WITH THE PERIOD PRESENT, verified verbatim in this checkout -
which is what proves A-1 is an accident of transcription and not a house idiom:

    [purchase/pl060.cbl:L1030-L1031]   `perform SPL-Posting-Close.`   period present
    [sales/sl100.cbl:L693-L694]        `perform SPL-Posting-Close.`   period present
    [purchase/pl100.cbl:L674-L675]     `perform SPL-Posting-Close.`   period present

All four sites carry the identical maintainer comment `*> THIS IS IN PURCHASE PL060`
([sales/sl060.cbl:L1172], [purchase/pl060.cbl:L1027], [sales/sl100.cbl:L690],
[purchase/pl100.cbl:L671]) and the identical `*> Why ?` of A-17
([sales/sl060.cbl:L1173], [purchase/pl060.cbl:L1028], [sales/sl100.cbl:L691],
[purchase/pl100.cbl:L672]). One of the four differs by a single character, and that
character changes which statements run.

A-1 IS OBSERVABLE ONLY IN PURE GENERAL LEDGER MODE, which is exactly why this scenario
pins `irs_instead` to a space and why `GLPOSTING-REC` is on its affected-table list.
`tests/scenarios/test_clean_batch_post_pl.py` is A-1's control: the same statement with
the period present. THE DEFECTIVE OUTCOME IS ASSERTED. PRESERVED, NOT NORMALISED (R-4).
DO NOT ADD THE MISSING PERIOD TO `sl060`;
`test_a1_missing_period_gl_posting_close_not_executed` below exists so that a
well-meaning correction turns this suite RED instead of passing unnoticed. Recorded as
A-1 in `docs/migration/anomaly-log.md`.

-------------------------------------------------------------------------------
A-8, A-9 AND A-10 - THE THREE DIVERGENT MOVING-AVERAGE BLOCKS
-------------------------------------------------------------------------------

The highest-value arithmetic finding in the whole migration, and the one most likely to
be "tidied" into a single helper. THEY MUST NOT BE NORMALISED INTO ONE (R-4).

A-8, DOUBLE TRUNCATION. [sales/sl060.cbl] `ba000-Sales-Comp section.` opens at L816:
its guard is L819-L824, `add 1 to sales-activety.` is L825, the first truncation is
L826 and the second is L827. The accumulator is declared with ZERO DECIMAL PLACES -
[sales/sl060.cbl:L206] `03  work-2  pic s9(14)  comp-3.` - while the value added into it
carries TWO - [sales/sl060.cbl:L218] `03  work-goods  pic s9(7)v99  comp-3.` - so PENCE
ARE DISCARDED ON EVERY ACCUMULATION at L826. The divide at L827 then discards the
remainder as well, because the receiving average field is `binary-long`
[copybooks/wssl.cob:L49], one of SEVEN `binary-long` statistics fields at
[copybooks/wssl.cob:L46-L52] - hence Python `int`, NEVER `Decimal` - while the two money
fields at [copybooks/wssl.cob:L54-L55] are `pic s9(8)v99 comp-3` and hence `Decimal`.
A seed of round pounds would hide A-8 completely.

A-9, THE COUNTER THAT IS NEVER INCREMENTED. [sales/sl060.cbl] `ba000-Credit-Comp
section.` opens at L832: guard L835-L840, then an EXTRA guard
`if work-2 not = zero` at L841, the add at L842 and the divide at L843. There is NO
`add 1 to sales-activety` ANYWHERE IN THAT SECTION, so the FIRST CREDIT NOTE FOR A
CUSTOMER IS SILENTLY DROPPED from the average.

A-10, THREE MUTUALLY INCONSISTENT GUARDS ON ONE IDIOM. [sales/sl060.cbl:L819] tests two
conditions with an explicit `else move zero` and increments the counter BEFORE dividing
at L825; [sales/sl060.cbl:L835] tests the same two, adds a THIRD guard at L841 and never
increments at all; and [sales/sl100.cbl:L506] tests ONE condition, expresses its else as
a preceding `move zero to work-b` at L504, increments at L510 and returns early on a zero
cleared date at L500-L501 - `compute-sales-pay` opens at [sales/sl100.cbl:L497] with its
arithmetic at L507 and L511 and `csp-exit` at L516.

THE DIVIDE SPELLINGS DIFFER AND THE ARITHMETIC DOES NOT, and the distinction is worth
stating exactly because calling L511 an INVERTED divide leaves a reader expecting a
reciprocal, which is wrong. `divide work-b by sales-pay-activety giving
sales-pay-average` [sales/sl100.cbl:L511] and `divide sales-activety into work-2 giving
sales-average` [sales/sl060.cbl:L827] both compute ACCUMULATOR / COUNTER: `DIVIDE X INTO
Y GIVING Z` is Z = Y / X and `DIVIDE Y BY X GIVING Z` is Z = Y / X, so the two forms name
their operands in opposite orders and produce the same quotient. THE DIVERGENCE IS
ENTIRELY IN THE GUARDS AND THE COUNTER HANDLING, which is where the three variants really
do disagree, and it is what must stay unnormalised (R-4).

Consequently THE SEED MUST CARRY TWO INVOICES AND ONE CREDIT NOTE FOR THE SAME CUSTOMER,
so that both `ba000-Sales-Comp` and `ba000-Credit-Comp` fire and their divergence is
observable in `SALEDGER-REC`. The scenario's own seed contract requires exactly that of
`salesled.dat`, `invoice.dat` and `openitm3.dat`. Recorded as A-8, A-9 and A-10 in
`docs/migration/anomaly-log.md`; `test_moving_average_fields_agree` asserts them at
state level and NEVER recomputes an average - that is arithmetic-tier work and belongs
to `tests/arithmetic/`.

-------------------------------------------------------------------------------
A-11 - A SIGNED VALUE NARROWED AT THE BRIDGE, BEFORE ANY SQL EXECUTES
-------------------------------------------------------------------------------

    Layer            Declaration                                      Range
    ---------------  -----------------------------------------------  --------
    Copybook         `Sales-Average binary-long`                      SIGNED
                     [copybooks/wssl.cob:L49]
    Bridge host var  `HV-SALES-AVERAGE PIC 9(10) COMP`                UNSIGNED
                     [common/salesMT.cbl:L308]
    Column           `SALES-AVERAGE int(8) unsigned NOT NULL`         UNSIGNED
                     [mysql/ACASDB.sql:L969]

The same narrowing applies across the whole statistics and date block at
[common/salesMT.cbl:L305-L312], while the two money fields stay signed at all three
layers - [common/salesMT.cbl:L313-L314] declares them `PIC S9(08)V9(02) COMP` - so THE
DRIFT IS SPECIFIC, NOT SYSTEMIC, and is handled field by field from the generated
dictionary. THE SIGN IS LOST AT THE BRIDGE, not at the database, so the Python
data-access layer reproduces the bridge's conversion rather than writing the computed
value and letting the server object. Recorded as A-11 in
`docs/migration/anomaly-log.md`, whose status entry is `REPRODUCED`: the narrowed value is
MEASURED as the ABSOLUTE VALUE - magnitude first, then high-order truncation - under
question `Q-3`. Measuring it does not repair it, and R-4 forbids repairing it, so A-11
stands.

-------------------------------------------------------------------------------
A-17 AND A-18 - RECORDED HERE BECAUSE A READER WILL LOOK FOR THEM
-------------------------------------------------------------------------------

A-17, THE UNEXPLAINED MOVE. [sales/sl060.cbl:L1173] `move RRN to postings.  *> Why ?` is
read back at [sales/sl060.cbl:L1037] as `add postings 1 giving Batch-start.`, and
`postings` is [copybooks/wssystem.cob:L184] `05  Postings  binary-short.`. Its
observable effect is therefore confined to `GLBATCH-REC.BATCH-START` ON THE NEXT RUN
against the same seeded system record. Because the maintainer himself does not know why
the statement is there, ITS EFFECT IS MEASURED AND REPRODUCED, NOT REASONED ABOUT (Agent
Action Plan section 0.6.8); the open question is `Q-A17-POSTINGS-EFFECT`.

A-18, TWO PERCENTAGE FIELDS NOT CARRIED INTO THE IRS POSTING RECORD - LATENT ON THIS
ROUTE. The maintainer flags the concern in comments at [sales/sl060.cbl:L1123-L1124];
the fan-out gate is `if irs-used or IRS-Both-Used` at [sales/sl060.cbl:L1126]; the
missing-usage notes are at [sales/sl060.cbl:L1133] and [sales/sl060.cbl:L1135];
[sales/sl060.cbl:L1138] moves 32 to `WS-IRS-vat-ac-def` and CONTINUES onto
[sales/sl060.cbl:L1139] `Vat-PC  *> IS IT ???`; and the block ends in
`SPL-Posting-Write` at [sales/sl060.cbl:L1142]. IN PURE GENERAL LEDGER MODE NONE OF THAT
EXECUTES, so A-18 is LATENT here and this capture cannot show it - stated explicitly so
that no reader expects it in this scenario's diff. `PSIRSPOST-REC` is nevertheless on
the affected-table list, as the UNCHANGED-WITNESS half of A-18's evidence; the positive
half needs a scenario pinning the switch to "Y" or "B".

-------------------------------------------------------------------------------
WHAT `sl055` FILTERS, AND WHAT THE ROUTE WRITES
-------------------------------------------------------------------------------

`sl055`'s four filters all live in `da020-Header-Analysis.` [sales/sl055.cbl:L426]: the
already-analysed-and-applied skip at L427-L428; the PROFORMA filter at L430-L431 (`if
ih-type = 4`); the PENDING filter at L433-L436, which also sets `ws-p-flag`; and then
`perform dd000-Extract.` at L438, with `move "Z" to ih-status.` at L679 and the invoice
rewrite that follows. The document types are 1 = Receipt, 2 = Invoice, 3 = Credit Note,
4 = Proforma. The credit-note sign flips are at [sales/sl055.cbl:L446],
[sales/sl055.cbl:L457] and [sales/sl055.cbl:L463], the NINE-FIELD NEGATION BLOCK is
[sales/sl055.cbl:L658-L666] under `if ih-type = 3` at L657, and the three-line addend
build is [sales/sl055.cbl:L671-L673].

THE ROUTE'S VERB CENSUS, which is what justifies the affected-table list:

    `sl830`  NO VERBS AT ALL - the guarded no-op above.
    `sl055`  `Analysis-Write`, `Invoice-Rewrite`, `Value-Write`, `Value-Rewrite`,
             `Value-Open-Output` (a recovery), `Invoice-Start` / `Invoice-Read-Next`,
             `Analysis-Read-Indexed`, `Value-Open-Input`
             => mutates ANALYSIS-REC, SAINVOICE-REC + SAINV-LINES-REC, VALUEANAL-REC.
    `sl060`  `GL-Batch-Write`, `GL-Posting-Write`, `OTM3-Write`, `OTM3-Rewrite` x3,
             `SPL-Posting-Write`, `Sales-Write`, `Sales-Rewrite`, `Value-Rewrite` x2,
             four `*-Open-Output` recoveries, `SPL-Posting-Open-Extend`
             => mutates GLBATCH-REC, GLPOSTING-REC, SAITM3-REC, SALEDGER-REC,
             VALUEANAL-REC.

`GLLEDGER-REC` IS DELIBERATELY ABSENT: `sl060` issues no `GL-Nominal-*` verb of any
kind, so the nominal ledger is not reached on this route and comparing it would compare
state the route does not produce.

FOUR OF THE NINE PERIOD-TOTAL WRITE SITES ARE ON THIS ROUTE, which is why `SYSTOT-REC`
is listed: [sales/sl055.cbl:L675] `add ws-inv-amt to sl-invoices-this-month.` under
`if ih-type = 2` at L674; [sales/sl055.cbl:L677] under `if ih-type = 3` at L676;
[sales/sl060.cbl:L641] `add total-deduct to sl-credit-deductions.`; and
[sales/sl060.cbl:L700] `add work-b to sl-cn-unappl-this-month.`, which is
UNCONDITIONAL - it sits OUTSIDE the `if FS-Cobol-Files-Used and File-18-Exists` print
guard at [sales/sl060.cbl:L695].

OTHER DETAILS PRESERVED AS WRITTEN, listed so that a reader tracing the route finds them
named: the further sign flips at [sales/sl060.cbl:L571], [sales/sl060.cbl:L758] and
[sales/sl060.cbl:L861]; the deduction apportionment at [sales/sl060.cbl:L643-L647],
which opens the value file, performs `ba000-Analise-Deductions` and closes it; `if G-L
perform ca000-BL-Close.` at [sales/sl060.cbl:L649-L650]; the ninety-nine-item batch cap
at [sales/sl060.cbl:L1151-L1153], which the seed stays under so that a second batch
header does not enter the capture; `aa040-End-Loop.` at [sales/sl060.cbl:L661] with its
`OTM3-Read-Next` at L662; `if s-closed go to aa040-End-Loop.` at
[sales/sl060.cbl:L668-L669]; `if oi-type = 3 perform ba000-Cr-Swop.` at
[sales/sl060.cbl:L671-L672]; and `aa050-End-Loop-End.` at [sales/sl060.cbl:L676].

WHY A SALES BATCH CANNOT MISMATCH ITS CONTROL TOTALS, stated because it is the reason
the control-total-mismatch scenario is GENERAL-LEDGER-ONLY: `sl060` writes the entered
and the actual totals from the SAME values, four adds in a row at
[sales/sl060.cbl:L1118-L1121]. A Sales batch balances BY CONSTRUCTION (Agent Action Plan
section 0.6.4), so there is no meaningful way to build an unbalanced one and this
scenario does not try.

-------------------------------------------------------------------------------
THE TEN-STAGE PROTOCOL, AND THE THREE-WAY EXIT CONTRACT
-------------------------------------------------------------------------------

    1  harness/reset_db.sh              6  harness/run_python_scenario.sh
    2  harness/run_cobol_scenario.sh    7  dump --side python
    3  dump --side cobol                8  normalize.py --side python
    4  normalize.py --side cobol        9  verify both captures published
    5  harness/reset_db.sh             10  diff_states.py

EIGHT LOGICAL STAGES, TEN NUMBERED ONES. Agent Action Plan section 0.3.2 fixes the
order as "seed, run, dump, normalize, reset, run, dump, diff" - eight. The driver
The PROTOCOL numbers ten, reading the list from
`harness/normalize.py`, because it makes BOTH normalisations and the publication
check explicit rather than implied. Nothing was added to the protocol; where older
prose says "stage 8" it means today's stage 10, the diff. The runners' own
`Check n/8' headings are their internal preflight checks and are not protocol
stages.

Driven through ONE helper, `protocol.run_scenario_parity`, which is what Agent Action
Plan section 0.4.3 built `tests/conftest.py` for: "so that no test reimplements the
comparison protocol". NO COMPARISON IS WRITTEN HERE. `TreeDiff.is_empty` is the pass
condition and `harness/diff_states.py`'s own `render` supplies the failure detail.

THE THREE-WAY EXIT CONTRACT, and the one conflation that must never happen:

    0  the two trees are identical, and stdout is EMPTY - ZERO BYTES, not a banner
    1  a real behavioural difference             -> a pytest FAILURE
    2  THE COMPARISON COULD NOT BE PERFORMED     -> a pytest ERROR, NEVER a pass
       (a missing tree or table file, a malformed dump, a shape mismatch, a `float`,
       a duplicate primary key, a wrong key order, `row_count != len(rows)`, a ragged
       row, a `null`)

"A test that treats 'could not compare' as 'no differences' is the single worst bug
available in this tree." Exit 2 is mapped to a harness fault by `tests/conftest.py` and
surfaces as an ERROR. THE COMPARISON IS EXACT: no tolerance, no epsilon, no case- or
whitespace-insensitivity and no numeric coercion - `1` against `"1"` IS a difference.
Rows align by PRIMARY-KEY VALUE, never by position, and the two labels are `cobol` and
`python`.

ALWAYS DUMP, THEN DECIDE THE STATUS. Agent Action Plan section 0.6.5, of a run-aborting
rejection: "The database effect is therefore THE ABSENCE of everything the later phases
would have written." ABSENCE IS EVIDENCE, so no dump is ever short-circuited on a
non-zero runner status - `run_scenario_parity` records the two run stages' statuses and
dumps regardless. The three exit categories are kept DISTINCT: success (including a
reproduced abort the scenario declared), a behavioural difference (whose dump is still
taken), and a harness fault (`argparse` exit 2 meaning the runner built a bad command
line, a missing promoted flag, an unreachable database, malformed YAML, or disagreeing
seed fingerprints). They are never conflated.

NO COMMAND LINE IS CONSTRUCTED HERE, EVER. The promoted-flag spellings belong to
`acas_posting/cli/*` and are discovered from them; `harness/run_python_scenario.sh` owns
the flag probe and fails as a HARNESS FAULT if a required flag is absent. This file
never imports `acas_posting.cli.sl_invoice_post`, never invokes it as a module, never
builds an `argv` list and never spells a `--flag`. The scenario declares no interactive
answer at all, because neither `sl055` nor `sl060` has a prompt that gates a database
write: their prompts are diagnostic acknowledgements guarded by
`if WS-Caller not = "xl150"`, and answering one changes no table.

-------------------------------------------------------------------------------
NORMALISATION DOES EXACTLY THREE THINGS, AND THERE IS NO FOURTH
-------------------------------------------------------------------------------

Delegated ENTIRELY to `harness/normalize.py`; nothing here reimplements or extends it.

ONE. TRAILING SPACES IN FIXED-CHARACTER COLUMNS - `rstrip(" ")`, TRAILING ONLY, because
a COBOL alphanumeric `MOVE` is left-justified with right padding, so LEADING SPACES ARE
CONTENT. ASCII U+0020 only, applied by declared type including `char(1)`. Motivated by
A-12: `pic x(24)` [copybooks/wsledger.cob:L27] becomes `PIC X(32)`
[common/nominalMT.cbl:L299] becomes `char(32)` [mysql/ACASDB.sql:L127]. The schema
carries 238 `char(` columns and zero `varchar(`.

TWO. DECIMAL SCALE RENDERING AT THE DECLARED SCALE - NOT uniformly two places. The
census is 68 columns at `(9,2)`, 57 at `(10,2)`, 17 at `(4,2)`, 12 at `(5,2)`, 4 at
`(14,2)`, 2 at `(2,0)`, 2 at `(14,4)` and a tail of singletons, and a value implying
more places RAISES rather than rounds, because rounding there would hide a real finding.
`SALEDGER-REC` has 37 columns mixing `Decimal` money fields
[copybooks/wssl.cob:L54-L55] with `int` statistics fields [copybooks/wssl.cob:L46-L52] -
THAT SPLIT IS EXACTLY WHAT MAKES A-8's INTEGER TRUNCATION REPRODUCIBLE and must not be
blurred.

THREE. TWO- VERSUS FOUR-DIGIT DATE TEXT FORMS, UNDER AN EXPLICIT COLUMN ALLOW-LIST ONLY:
`GLPOSTING-REC.POST-DAT`, `IRSPOSTING-REC.POST4-DAT`, `PSIRSPOST-REC.IRS-POST-DAT`,
`SYSTEM-REC.STATS-DATE-PERIOD` and `SALEDGER-REC.SALES-STATS-DATE`. `char(8)` DOES NOT
IMPLY DATE - `SAITM3-REC.OI3-BATCH` is a batch reference and is excluded by name - and
most in-scope "dates" are BINARY DAY-NUMBER INTEGERS that job 3 must not touch.

-------------------------------------------------------------------------------
THE TWO ORACLE-ARBITRATED QUESTIONS THIS FILE CARRIES  (R-6)
-------------------------------------------------------------------------------

Referenced BY IDENTIFIER into `docs/migration/ambiguity-resolutions.md`. These are
TEXTUAL REFERENCES ONLY: nothing here imports that document, stats its path or skips on
its absence.

`Q-3`  THE VALUE A NARROWED NEGATIVE PRODUCES. A-11 settles the SHAPE - the sign is lost
       at the bridge - and the value stored is MEASURED through the compiled
       handler, bridge and C interface: it is the ABSOLUTE VALUE, magnitude taken first
       and high-order digits truncated after. The generated dictionary therefore emits
       `A-11` ALONE on its 91 field entries across eleven tables, eleven of them in
       `SALEDGER-REC`, having dropped the `Q-3` tag when the question closed; the
       dictionary's remaining `ambiguity_refs` are `Q-4` on 28 entries and `Q-6` on 1.
       The narrowing test below still asserts ONLY that the two sides agree and PREDICTS
       NO VALUE, because the measurement settled the RULE and not what each seeded figure
       becomes after this route's sign flips - the arithmetic tier owns the vectors.

`Q-CLI-SYSREC-PINS`  WHAT `SYSTOT-REC`'s PERSISTENCE DEPENDS ON. The broader question,
       `Q-CLI-OVERREWRITE`, is SETTLED AND SETTLED BY REPRODUCTION:
       `acas_posting/cli/sl_invoice_post.py` performs the `overrewrite` paragraph from
       both arms of `load000` and loads `SYSTEM-REC` and `SYSTOT-REC` before the first
       dispatch, exactly as [sales/sales.cbl:L628-L641] does. What remains, recorded in
       `acas_posting/cli/args.py`, is narrower: three columns - `Run-Date`, `Date-Form`
       and `IRS-Instead` - are re-pinned from the command line over the loaded row, so
       the scenario must SEED them to agree with the options it passes, which
       the preconditions test below asserts. IF `SYSTOT-REC` DIVERGES THAT IS A REAL
       SIGNAL AND NEVER SOMETHING TO SUPPRESS: no ignore-list resolves it, and the
       failure message names the identifier instead.

       A third question on this route, `Q-CLI-TERMCODE-1-7`, is SETTLED BY CENSUS and is
       recorded for completeness: only 0, 4, 5, 8 and 9 are ever stored into
       `WS-Term-Code` in the frozen tree, so the 1..7 band has no producer and the gate
       is reproduced over the whole `pic 99` domain rather than over reachable values.

The declination of `gl_end_of_cycle` is likewise oracle-reversible and is recorded in
`harness/scenarios/period_end_totals.yaml`, on six grounds. Its consequence reaches this
file: `gl_end_of_cycle` appears in NO scenario's operation list, so `system.period` is
an INERT value on this route - carried because it is part of the seeded system
record and because the key set is uniform, not because any listed operation divides by
it.

-------------------------------------------------------------------------------
THE FIVE REJECTION CLASSES - THIS SCENARIO EXERCISES NONE OF THEM
-------------------------------------------------------------------------------

Agent Action Plan section 0.8.1: "a single generic rejection path would fail this
directive." They are named here so that this file's silence about them is deliberate
rather than an omission, and so that a reader does not look for one in this capture.

    ONE    CLEAN REJECTION, NO DATABASE EFFECT - the two entirely silent skips at
           [general/gl072.cbl:L291-L292] and [general/gl072.cbl:L306-L307] (A-13).
    TWO    RUN-ABORTING - the control-total mismatch, whose database effect is THE
           ABSENCE of everything the later phases would have written.
    THREE  PARTIAL DATABASE EFFECT - the half-posted double entry at
           [irs/irs030.cbl:L1635-L1652] (A-4), and the lost update from the pre-loop
           snapshots at [irs/irs030.cbl:L1602] and [irs/irs030.cbl:L1612] rewritten at
           [irs/irs030.cbl:L1704-L1708] (A-5).
    FOUR   FILE-ABANDONING - [irs/irs030.cbl:L1673-L1678], whose partial state is
           COMMITTED, NOT ROLLED BACK.
    FIVE   A PERMANENTLY FAILING FACADE VERB - four verbs refused unconditionally at
           handler entry, [common/acas008.cbl:L299-L307] (A-6).

This is the reference happy path: `expected_status` is zero for its single operation,
and that zero is provable rather than hoped for, as shown under peculiarity TWO above.

-------------------------------------------------------------------------------
SEEDING AND SCHEMA CONSTRAINTS THIS FILE RELIES ON  (R-3)
-------------------------------------------------------------------------------

Documented, never implemented here - `harness/seed.sh` and `harness/reset_db.sh` own
every one of them.

NO DDL OF ANY KIND. `mysql/ACASDB.sql` is applied VERBATIM; it already contains all 33
`DROP TABLE IF EXISTS` statements, so re-applying it IS the drop-and-recreate, and the
database name must be on the client command line because the file carries no `USE`.

AUTOCOMMIT MUST BE OFF WHILE SEEDING, asserted rather than set. The batch loader says so
itself, [common/glbatchLD.cbl:L9-L12] verbatim: "This modules uses commit and rollback
so you MUST ensure that autocommit is OFF in the rdb settings. It is as default set ON."

`common/masterLD.sh` IS NEVER INVOKED. Its own header says "THIS SCRIPT HAS NOT YET BEEN
TESTED" [common/masterLD.sh:L4]; all 24 of its loader lines
[common/masterLD.sh:L93-L116] omit the `;` before `fi`, so `bash -n` rejects a 123-line
file at line 124; and it ends by paging a log through `less`, which would block a
non-interactive run forever. IT IS FROZEN AND IS NOT FIXED. `harness/seed.sh` reproduces
its documented per-file contract [common/masterLD.sh:L44-L115] instead, and tests the
loaders' exit codes rather than assuming success - values above 63 abort the load, with
128 meaning the parameters were not set up, 64 the relational database was not, and 16 a
write error. The `dfltLD` strict-versus-lenient exit asymmetry
([common/masterLD.sh:L83] tests `!= 0` where its three siblings test `-gt 63`) is
PRESERVED, NOT HARMONISED (R-4), as are the charset caveat and the `tinyint(1) unsigned`
display-width quirk.

EXECUTION IS STRICTLY SEQUENTIAL. There is no parallel test-execution plugin, no `-n`
flag and no randomised ordering anywhere in this project's configuration - `addopts`
carries none, and `pyproject.toml` says so in its own comment: parallel scenario runs
against one shared MariaDB would break the seed / run / dump / reset / run / dump / diff
protocol outright. There is likewise no timing assertion and no performance measurement
in this file - Agent Action Plan section 0.8.4 puts performance out of scope by
construction.

-------------------------------------------------------------------------------
HOW THE SIX RULES ARE HONOURED HERE
-------------------------------------------------------------------------------

R-1  NO COBOL AT RUNTIME, satisfied STRUCTURALLY. This module imports `pytest` and the
     standard library and nothing else. IT NEVER IMPORTS A HARNESS MODULE IN ANY FORM,
     and there is none to import: `harness/` has no `__init__.py` and
     `pyproject.toml` excludes `harness*` from packaging, which is the structural
     enforcement. Nor does it reach one by file path, by dynamic loading or by
     `sys.path` manipulation. The three harness
     Python modules arrive ONLY through `tests/conftest.py`'s `harness` fixture, and the
     compiled oracle is reached only out of process, by the harness shell scripts that
     `run_scenario_parity` drives. Nothing here invokes `cobc` or `cobcrun`, and there
     is no foreign-function interface of any kind. `tests/conftest.py` itself is
     reached through FIXTURES AND NEVER IMPORTED, which is the house convention
     across the test tree.
R-2  ZERO BINARY FLOATING POINT. There is no binary-radix numeric literal in this file,
     no conversion to one and no annotation naming one; there is no epsilon, no
     tolerance, no closeness helper from the standard library and no
     approximate-equality helper from the test runner. Dumped values are JSON integers
     or canonical JSON strings, and the type assertions below REFUSE a binary-radix
     value outright. No `pandas` and no `numpy`.
R-3  NO NEW VALIDATIONS, FIELDS OR SCHEMA CHANGES; NO CONCURRENCY. This file emits no
     DDL, opens no connection of its own, adds no check the COBOL lacks and interprets
     no scenario value beyond asserting the pins the protocol depends on. It creates
     no `__init__.py`, no nested `conftest.py` and no helper module: everything shared
     comes from `tests/conftest.py`. It registers no marker - `pyproject.toml`
     declares all five under `--strict-markers` - and defines no `pytest_configure`,
     `pytest_collection_modifyitems` or `pytest_plugins`.
R-4  ANOMALIES REPRODUCED, NEVER FIXED. A-1 is asserted in its DEFECTIVE form; A-8, A-9
     and A-10 are asserted as three separate observations rather than one; A-11's sign
     loss is asserted as loss. There is NO ignore-list, NO tolerance-list and NO "known
     difference" allowance in this file, and no assertion here can be made to pass by
     normalising, sorting, coalescing or trimming anything.
R-5  FULL TRACEABILITY. Every anomaly this file touches is named by its register
     identifier - A-1, A-8, A-9, A-10, A-11, A-12, A-17, A-18 - and every claim carries
     its `[path:Lnnn]` locator, both in this docstring and at each assertion site. The
     register is `docs/migration/anomaly-log.md`. `pytest-cov` is EVIDENCE, NOT A GATE:
     there is no `--cov-fail-under` anywhere.
R-6  COMPILED BEHAVIOUR IS THE TIE-BREAKER. The empty normalised diff is the arbiter,
     the two open questions above are referenced by identifier and never guessed, and
     the pinned clock is asserted so that two runs of this scenario are
     byte-identical. The
     per-scenario evidence is recorded in `docs/migration/scenario-diff-evidence.md`.
"""

from __future__ import annotations

# The standard library only, and only what the annotations and the path arithmetic need.
# NOTHING ELSE IS IMPORTED AT ALL (R-1): no harness module in any form, no
# `acas_posting.cli` entry point, no child-process primitive, no dynamic loader and no
# YAML parser - the scenario definition arrives ALREADY PARSED, through the
# `scenario_loader` fixture, which reads it with `yaml.safe_load` and never with the
# loader that can construct arbitrary Python objects.
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Final

import pytest

# The tier label. ALREADY REGISTERED, in `pyproject.toml`'s `[tool.pytest.ini_options]
# markers` under `--strict-markers` and `--strict-config`, where its description records
# that it requires the Compose stack. Nothing here re-registers it and this file adds no
# `pytest.ini`, no `markers =` and no `pytest_configure`. Selectable as
# `pytest -m scenario` and `pytest -m "scenario or determinism"`.
# The TIER mark, applied to the whole module because every test in it belongs to the
# tier. THE INFRASTRUCTURE MARKS ARE NOT HERE: `database` and `oracle` are declared per
# test, on exactly the tests whose fixture closure reaches the harness stack, because
# several tests in this file read only files on disk and pass on a bare host. A module
# mark would claim they need a MariaDB and a built oracle, and `-m database` would then
# select tests that require neither.
pytestmark = pytest.mark.scenario

# THE SCENARIO THIS FILE IS. One per `tests/scenarios/test_*.py`, defined at
# `harness/scenarios/clean_batch_sl.yaml`, which is the single authority for every value
# below that is not a frozen-source locator.
SCENARIO: Final[str] = "clean_batch_sl"


# ---------------------------------------------------------------------------
#  THE SCENARIO'S OWN KEYS, AND THE PINS THE PROTOCOL DEPENDS ON
#
#  KEY NAMES ONLY - not values. The scenario file is read through the fixture and its
#  declared contents are never second-guessed: interpreting them and judging them would
#  be the added validation R-3 forbids. What IS asserted is the handful of pins WITHOUT
#  WHICH THE COMPARISON WOULD BE MEANINGLESS RATHER THAN MERELY DIFFERENT - the
#  false-pass trap of section 3.1 and the fan-out switch that makes A-1 observable at
#  all.
#
#  The scenario publishes a few values under BOTH a grouped and a flat key, because its
#  two consumers read it differently: the COBOL-side runner accepts TOP-LEVEL keys only,
#  so a value nested under `clock`, `system` or `seed` is invisible to it. The pairs are
#  aadjacent in the file so that drift is visible, and the assertions below check the
#  apair
#  members against EACH OTHER as well as against the pin, which is what makes the
#  duplication safe.
# ---------------------------------------------------------------------------

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
KEY_SEED_DATA_DIR: Final[str] = "data_dir"
KEY_SEED_FILES_NESTED: Final[str] = "files"
KEY_SEED_DIR: Final[str] = "seed_dir"
KEY_SEED_FILES: Final[str] = "seed_files"
KEY_AFFECTED_TABLES: Final[str] = "affected_tables"

# The `system:` block's own keys. Every one of them is an assertion about the SEEDED
# RRECORD rather than a command-line input, which is why the Python entry point exposes
# Rno
# option for most of them.
SYS_FILE_SYSTEM_USED: Final[str] = "file_system_used"
SYS_CYCLEA: Final[str] = "cyclea"
SYS_PERIOD: Final[str] = "period"
SYS_SL_AUTOGEN: Final[str] = "sl_autogen"
SYS_PL_AUTOGEN: Final[str] = "pl_autogen"

# THE ROUTE. `sl_invoice_post` is `load07` [sales/sales.cbl:L756-L768] and dispatches
# `sl055` then `sl060`; the eighth menu paragraph belongs to the out-of-scope payment
# route and is named nowhere in this file.
OPERATION: Final[str] = "sl_invoice_post"
SUBSYSTEM: Final[str] = "sales"

# THE FALSE-PASS TRAP, section 3.1, and the single most important pin in the file.
# [copybooks/wssystem.cob:L112-L114] declares `07  File-System-Used  pic 9.` with
# `88  FS-Cobol-Files-Used  value zero.` and `88  FS-MySql-Used  value 1.`, inside
# `RDBMS-Flat-Statuses` [copybooks/wssystem.cob:L111]. Every handler gates on it -
# [common/acas007.cbl:L316-L320] verbatim:
#  L316       if       not FS-Cobol-Files-Used
#  L317                move RDBMS-Flat-Statuses to FA-RDBMS-Flat-Statuses
#  L318                perform  ba-Process-RDBMS
#  L319                go to AA-Main-Exit
#  L320       end-if.
# WWith zero the handler NEVER TOUCHES MySQL, both dumps come back empty, the diff exits
# W0
# and the run is a SILENT FALSE PASS. Hence the pin, and hence the assertion.
FILE_SYSTEM_USED_MYSQL: Final[int] = 1

# THE FAN-OUT SWITCH, [copybooks/wssystem.cob:L179-L181] verbatim:
#  L179         05  IRS-Instead     pic x.
#  L180             88  IRS-Used                   value "Y".
#  L181             88  IRS-Both-Used              value "B".   *> 26/11/16
# THREE states, and THE THIRD HAS NO CONDITION NAME AT ALL - for a space both predicates
# are simply False, which is pure General Ledger mode. Tested at three sites in each of
# the four Sales and Purchase posting programs, on this route at
# [sales/sl060.cbl:L1039], [sales/sl060.cbl:L1126] and [sales/sl060.cbl:L1175]. Agent
# Action Plan section 0.6.4: "leaving it at a default would make the affected-table list
# ambiguous", so every scenario pins it explicitly. A space or empty value reaches the
# command line as the LITERAL SPACE `--irs-instead ' '`; the option takes one character
# and publishes no `N`, so the space is what is passed and what the column stores, and
# normalisation job 1 trims that identically on BOTH sides.
#
# IF THIS EVER DRIFTS TO "Y" OR "B", IF#2 AT [sales/sl060.cbl:L1175] BECOMES TRUE, A-1
# VVANISHES FROM THE DIFF AND THIS FILE SILENTLY STOPS LOCKING ANYTHING. That is the
# Vwhole
# reason it is asserted rather than assumed.
IRS_INSTEAD_GL_ONLY: Final[str] = " "

# `G-L` is a condition name on the INSTALLED-LEDGER level byte, `88  G-L  value 1.` at
# [copybooks/wssystem.cob:L85] over `07  Level-1  pic 9.` at
# [copybooks/wssystem.cob:L84] - NOT on the fan-out switch. Pure General Ledger mode is
# therefore the TWO-FIELD statement `Level-1 = 1` AND `IRS-Instead = space`, which is
# what makes IF#2 false while IF#1 and IF#3 are true.
LEVEL_1_GENERAL_LEDGER: Final[int] = 1

# The automatic-generation switches, [copybooks/wssystem.cob:L274]
# `05  SL-Autogen  pic x  value space.  *> added 14/04/23` and
# [copybooks/wssystem.cob:L209] `05  PL-Autogen  pic x  value space.
# *> added 14/04/23 NOT USED YET`. A space makes `sl830` return at
# [sales/sl830.cbl:L269-L270] before it issues a single verb.
AUTOGEN_OFF: Final[str] = " "

# THE PROJECT-WIDE PINNED RUN DATE, restated as the two literals so that a drift between
# THIS file, `tests/conftest.py` and the scenario YAML fails loudly rather than
# iinvisibly. They are not a competing authority:
# i`test_scenario_definition_preconditions`
# cross-checks all three sources against each other, and `tests/conftest.py` asserts the
# pair against `acas_posting/clock.py` inside the `pinned_clock` fixture, so any two of
# the three disagreeing is a failure. The house convention is that conftest is reached
# through FIXTURES and never imported, which is why the literals appear here at all.
#
# `to-day pic x(10)` is DD/MM/CCYY; the binary observable is
# [copybooks/wssystem.cob:L67] `05  Run-Date        binary-long.`, counted from the
# 1600-12-31 epoch the maintainer flags at [common/maps04.cbl:L39-L41].
PINNED_TO_DAY: Final[str] = "21/09/2025"
PINNED_RUN_DATE: Final[int] = 155127

# `SYSTEM-REC.DATE-FORM`, `88 Date-UK value 1` [copybooks/wssystem.cob:L129-L131]. It
# selects the DIGIT ORDER THE COBOL RUNNER TYPES at the Date Entry screen; the Python
# side fixes DD/MM/CCYY unconditionally. That lexical asymmetry is documented and
# deliberate: the two sides agree on the DATE and differ only in how it is spelled at an
# input surface the Python side does not have.
DATE_FORM_UK: Final[int] = 1

# The single operation's declared whole-process status. `expected_status` is a flat
# sequence matching `operations` POSITIONALLY. Zero here is PROVABLE - see peculiarity
# TWO in the module docstring - because the only term code either program on this route
# can raise is 8, both of whose raise sites are unreachable while `file_system_used` is
# pinned to 1.
EXPECTED_STATUS_SUCCESS: Final[int] = 0


# ---------------------------------------------------------------------------
#  THE SEED CONTRACT, AND THE BOUNDED TABLE SET
# ---------------------------------------------------------------------------

# THE SIX FLAT FILES, each one a name the frozen loader script recognises, with its
# loader traced to [common/masterLD.sh]:
#  system.dat    -> the four-loader system block [common/masterLD.sh:L51-L87]:
#  `systemLD` L52, then `sys4LD` L61, then `finalLD` L70, then
#  `dfltLD` L79, in that fixed order. SYS4LD IS WHAT LOADS
#  SYSTOT-REC. Effectively mandatory: without the system record the
#  menu calls its interactive setup program and the runner blocks on
#  aa terminal, and the seeder refuses a scenario that omits it. It
#  ais
#  also what carries `Run-Date` [copybooks/wssystem.cob:L67] and the
#  fan-out switch [copybooks/wssystem.cob:L179-L181].
#  analysis.dat  -> `analLD`      [common/masterLD.sh:L93]  -> ANALYSIS-REC
#  invoice.dat   -> `slinvoiceLD` [common/masterLD.sh:L98]  -> SAINVOICE-REC AND
#  SAINV-LINES-REC, both from the one loader
#  openitm3.dat  -> `otm3LD`      [common/masterLD.sh:L104] -> SAITM3-REC
#  salesled.dat  -> `salesLD`     [common/masterLD.sh:L112] -> SALEDGER-REC
#  value.dat     -> `valueLD`     [common/masterLD.sh:L116] -> VALUEANAL-REC
#
# The DECLARED ORDER is membership only: the seeder applies the frozen loader order
# regardless, and the system block always runs first. Held here as a frozenset for that
# reason, so the assertion cannot accidentally become an order assertion.
EXPECTED_SEED_FILES: Final[frozenset[str]] = frozenset(
    {
        "system.dat",
        "analysis.dat",
        "invoice.dat",
        "openitm3.dat",
        "salesled.dat",
        "value.dat",
    }
)

# TTHE ONE SEED FILE WHOSE PRESENCE WOULD DESTROY THIS SCENARIO'S PURPOSE.
# T`slautogen.dat`
# is one of the eight out-of-scope names the frozen loader script recognises
# [common/masterLD.sh:L113]; seeding it would populate the very tables this scenario
# aasserts empty and would make the `sl830` no-op UNPROVABLE. Its omission is LOAD-
# aBEARING
# rather than an oversight, so it is asserted rather than left to inspection.
FORBIDDEN_SEED_FILE: Final[str] = "slautogen.dat"

# TThe system flat file the seeder refuses a scenario without, named separately because
# Tit
# is the one whose ABSENCE is a hang rather than a difference.
MANDATORY_SEED_FILE: Final[str] = "system.dat"

# How many tables this scenario bounds its comparison to. THE LIST ITSELF IS NEVER
# RESTATED HERE (R-4): `harness/scenarios/clean_batch_sl.yaml` is its single definition
# and `harness/dump_tables.py`'s `IN_SCOPE` is the single definition of what is in scope
# at all. What is asserted is the list's PROPERTIES - the count, strict alphabetical
# order, in-scope membership - plus the four individual memberships the anomaly evidence
# below would be VACUOUS without, each named at its own assertion with its reason.
#: Ten justified by the route's verb census, plus SYSTEM-REC. The eleventh joined
#: after MEASUREMENT (rule R-6): this route mutates the system record - the
#: allocator increment at [sales/sl060.cbl:L1018] and anomaly A-17's move at
#: [sales/sl060.cbl:L1173] - and the Sales menu exit persists it
#: [sales/sales.cbl:L628-L657], which the headless route reproduces as
#: args.overrewrite. Both sides end byte-identical, so bounding it in is what makes
#: those two mutations observable at all.
EXPECTED_AFFECTED_TABLE_COUNT: Final[int] = 11

# A-1's WITNESS TABLE. `GLPOSTING-REC` is on the list BECAUSE OF A-1: it is where the
# effect - or the non-effect - of the posting file that is never closed becomes visible.
GL_POSTING_TABLE: Final[str] = "GLPOSTING-REC"

# A-8, A-9, A-10 and A-11's witness table, 37 columns [mysql/ACASDB.sql:L945].
SALES_LEDGER_TABLE: Final[str] = "SALEDGER-REC"

# A-18's UNCHANGED witness. Latent in pure General Ledger mode, so the evidence this
# capture carries is negative: the transfer table is compared and expected to agree,
# which is the only half of A-18 a pure-GL run can show.
IRS_TRANSFER_TABLE: Final[str] = "PSIRSPOST-REC"

# The period-total table, written by four of the nine sites on this route
# ([sales/sl055.cbl:L675], [sales/sl055.cbl:L677], [sales/sl060.cbl:L641],
# [sales/sl060.cbl:L700]). It carries the recorded `Q-CLI-SYSREC-PINS` caveat set out in
# the module docstring; a divergence here is A REAL SIGNAL and is never suppressed.
PERIOD_TOTALS_TABLE: Final[str] = "SYSTOT-REC"

# THE SEVEN TABLES THE SEED ITSELF FILLS, each named by the `seed_files:` entry that
# fills it: analysis.dat -> ANALYSIS-REC, value.dat -> VALUEANAL-REC, salesled.dat ->
# SALEDGER-REC, invoice.dat -> SAINVOICE-REC and SAINV-LINES-REC, openitm3.dat ->
# SAITM3-REC, and system.dat -> SYSTOT-REC through the four-loader system block
# [common/masterLD.sh:L51-L87]. These must come back WITH ROWS or the empty diff this
# file's headline test celebrates is two empty databases agreeing.
#
# THE OTHER THREE AFFECTED TABLES ARE DELIBERATELY ABSENT from this tuple. GLBATCH-REC,
# GLPOSTING-REC and PSIRSPOST-REC are WRITTEN BY THE RUN rather than seeded, and A-1 is
# precisely the claim that `GLPOSTING-REC` may legitimately stay empty here - requiring
# rows in it would assert the opposite of what [sales/sl060.cbl:L1172-L1178] does.
SEEDED_TABLES: Final[tuple[str, ...]] = (
    "ANALYSIS-REC",
    "SAINV-LINES-REC",
    "SAINVOICE-REC",
    "SAITM3-REC",
    "SALEDGER-REC",
    "SYSTOT-REC",
    "VALUEANAL-REC",
)

# THE FOUR AUTOMATIC-GENERATION TABLES. Named so the assertion can be made, and each one
# cross-checked against `harness/dump_tables.py`'s own `OUT_OF_SCOPE` set so that THE
# HARNESS REMAINS THE AUTHORITY on what is out of scope and this tuple cannot drift into
# a second definition of it.
AUTOGEN_TABLES: Final[tuple[str, ...]] = (
    "PUAUTOGEN-LINES-REC",
    "PUAUTOGEN-REC",
    "SAAUTOGEN-LINES-REC",
    "SAAUTOGEN-REC",
)

# A-8 AND A-9's TWO COLUMNS, and the only two `SALEDGER-REC` columns this route's
# moving-average blocks reach. Both are `int(8) unsigned` in the frozen schema
# ([mysql/ACASDB.sql:L966] and [mysql/ACASDB.sql:L969]) over `binary-long` copybook
# fields ([copybooks/wssl.cob:L46] and [copybooks/wssl.cob:L49]).
SALES_ACTIVETY_COLUMN: Final[str] = "SALES-ACTIVETY"
SALES_AVERAGE_COLUMN: Final[str] = "SALES-AVERAGE"

# A-10's THIRD-VARIANT COLUMNS, written by `sl100` on the sibling cash route and NOT by
# this one - [sales/sl100.cbl:L510-L511] against [sales/sl060.cbl:L825-L827]. Compared
# here as UNCHANGED WITNESSES, which is what makes the divergence between the two routes
# attributable rather than merely present.
SALES_PAY_ACTIVETY_COLUMN: Final[str] = "SALES-PAY-ACTIVETY"
SALES_PAY_AVERAGE_COLUMN: Final[str] = "SALES-PAY-AVERAGE"

# THE SEVEN SIGNED-TO-UNSIGNED NARROWED STATISTICS COLUMNS OF A-11, in the order
# [copybooks/wssl.cob:L46-L52] declares them, each `binary-long` there and each
# `PIC 9(10) COMP` in the bridge at [common/salesMT.cbl:L305-L312].
NARROWED_STATISTICS_COLUMNS: Final[tuple[str, ...]] = (
    "SALES-ACTIVETY",
    "SALES-LAST-INV",
    "SALES-LAST-PAY",
    "SALES-AVERAGE",
    "SALES-PAY-ACTIVETY",
    "SALES-PAY-AVERAGE",
    "SALES-PAY-WORST",
)

# TTHE TWO MONEY COLUMNS THAT PASS THROUGH SIGNED AT ALL THREE LAYERS, which is what
# Tmakes
# A-11 "specific, not systemic": `pic s9(8)v99 comp-3`
# [copybooks/wssl.cob:L54-L55], `PIC S9(08)V9(02) COMP`
# [common/salesMT.cbl:L313-L314], `decimal(10,2)` [mysql/ACASDB.sql:L974-L975]. Asserted
# alongside the narrowed set so the contrast is measured rather than asserted in prose.
SIGNED_MONEY_COLUMNS: Final[tuple[str, ...]] = ("SALES-CURRENT", "SALES-LAST")

# TThe frozen schema's three type kinds, as `harness/normalize.py` names them. Restated
# Tas
# strings only because this file must not import that module directly (R-1); every use
# bbelow reads the kind off the parsed schema the `frozen_schema` fixture supplies, so
# bthe
# schema stays the authority.
KIND_DECIMAL: Final[str] = "decimal"
KIND_INTEGER: Final[str] = "integer"

# The two sides of the comparison, as the canonical output layout records them. The side
# lives in the PATH and never inside a dump.
SIDE_COBOL: Final[str] = "cobol"
SIDE_PYTHON: Final[str] = "python"

# The suffix `harness/dump_tables.py` gives a dump file, `<TABLE>.json` for the table it
# holds, hyphens included.
DUMP_SUFFIX: Final[str] = ".json"


# ---------------------------------------------------------------------------
#  THE SHARED PARITY RUN
#
#  ONE TEN-STAGE RUN PER MODULE, SHARED AS FROZEN EVIDENCE. The five stack-backed
#  assertions below all interrogate the SAME pair of normalised trees, which is the
#  point: A-1, the moving averages, the sign narrowing and the dump shape are four
#  readings of one comparison, not four comparisons.
#
#  WHY THE MEMOISATION IS DONE HERE RATHER THAN WITH A MODULE-SCOPED FIXTURE. The
#  ``protocol` fixture `tests/conftest.py` publishes is FUNCTION-SCOPED by its own
#  `design,
#  because it applies the stack skip guard per test; pytest refuses to let a
#  module-scoped fixture depend on a function-scoped one, and importing
#  `tests/conftest.py` to reach `run_scenario_parity` directly would break the house
#  convention that conftest is reached through fixtures. So the run is memoised on the
#  scenario name in this private mapping, which leaves every test below INDEPENDENT OF
#  OORDERING - whichever executes first performs the ten stages - while still
#  Operforming
#  the destructive seed / reset / reseed sequence exactly once.
#
#  A `ParityRun` is a FROZEN dataclass whose every collection is a tuple, so sharing it
#  is safe: evidence that could be edited after the fact would not be evidence.
#
#  STRICTLY SEQUENTIAL (R-3). There is no thread, no `asyncio`, no `multiprocessing` and
#  no parallel test-execution plugin in this project, so a plain dict needs no lock and
#  there is no race to guard.
# ---------------------------------------------------------------------------

_PARITY_RUNS: dict[str, Any] = {}


@pytest.fixture
def parity(protocol: Any) -> Any:
    """The completed ten-stage parity run for `clean_batch_sl`.

    Every stage happens HERE rather than in a test body, so that a HARNESS FAULT is a
    pytest ERROR while the verdict is left for the test to assert and a genuine
    behavioural difference is a pytest FAILURE. The two can then never be confused,
    which is the whole point of the split and the reason exit 2 must never read as
    "no differences".

    `protocol` applies the stack skip guard before any stage can run, so on a host with
    no Docker, no MariaDB and no built oracle every stack-backed test below SKIPS with a
    precise, multi-line reason naming every missing precondition - it never errors at
    collection.

    FOUR GUARDS RUN HERE, and each closes a way AN EMPTY DIFF CAN MEAN NOTHING:

      1. THE BOUND - the comparison covered the declared tables in the declared order.
      2. THE ORACLE'S DISPOSITION - its ACTUAL exit status, plus a harness-fault
         classification on BOTH sides. A runner that exited in its own documented band
         or on `argparse` usage exit 2 never ran the cycle, and that must read as an
         ERROR here rather than as a behavioural FAILURE downstream.
      3. THE SEED FINGERPRINTS - both sides started from the same recorded row counts.
      4. NON-VACUITY - the seven tables the seed fills came back WITH ROWS. Every
         assertion in this file holds vacuously against 33 empty tables without it.

    Args:
        protocol: Every protocol stage and both compositions, from `tests/conftest.py`.
            `protocol.run_scenario_parity` is what Agent Action Plan section 0.4.3 built
            that module for, "so that no test reimplements the comparison protocol".

    Returns:
        The `ParityRun`: the affected-table list the comparison was bounded by, every
        stage result in execution order, both run stages, the stage-10 verdict and the
        paths of every artifact. Frozen, and memoised for the module.

    Raises:
        HarnessFaultError: A stage whose failure destroys the evidence failed - the
            seed, the reset, either dump, either normalisation, or the comparison itself
            with exit 2. Reported as a pytest ERROR, never as a pass.
    """
    cached = _PARITY_RUNS.get(SCENARIO)
    if cached is None:
        cached = protocol.run_scenario_parity(SCENARIO)
        _PARITY_RUNS[SCENARIO] = cached
    run = cached

    # GUARD 1. The comparison was bounded by the tables the scenario declares, in the
    # declared ORDER - the report is written in it and so is the seed fingerprint.
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

    # GUARD 2. THE ORACLE REACHED THE DECLARED DISPOSITION, and NEITHER side is a
    # harness fault. The harness-fault refusal is why this belongs in a fixture: a
    # runner that exits in its own documented band, or on `argparse` usage exit 2,
    # never asked the question at all, and the headline test below would otherwise
    # report that as a behavioural FAILURE. `reference_only` leaves the Python side's
    # status to that test, which owns it and says so under its own name.
    #  BOTH SIDES DROVE THE SAME ORDERED OPERATION LIST. The
    #  comparison below is between one COBOL run and one Python run, and it means
    #  nothing unless the two drove the same work in the same order - an empty diff
    #  between a short run and a full one being the most dangerous false pass this tier
    #  can produce. Both runners resolve the list from the scenario itself and publish
    #  one status row per operation, so it is checked rather than assumed.
    protocol.assert_operations_driven(run, operations=(OPERATION,))

    protocol.assert_declared_statuses(
        run,
        operations=(OPERATION,),
        declared=list(protocol.definition(SCENARIO)[KEY_EXPECTED_STATUS]),
        reference_only=True,
    )

    # GUARD 3. Both sides started from the same recorded seeded state - row counts, one
    # line per affected table in the declared order, compared as bytes.
    protocol.assert_seed_fingerprints_agree(run)

    # GUARD 4. SOMETHING WAS THERE TO COMPARE. Without this, every assertion below
    # holds just as well against 33 empty tables.
    protocol.assert_non_vacuous(run, tables_requiring_rows=SEEDED_TABLES)

    return run


@pytest.fixture
def definition(scenario_loader: Any) -> Mapping[str, Any]:
    """This scenario's parsed definition. NEEDS NO STACK.

    A scenario definition is a file on disk, so the four stack-free assertions below run
    on a bare host. Parsed with `yaml.safe_load` by `tests/conftest.py` and never with
    the loader that can construct arbitrary Python objects, because a data file must not
    be able to do that. Nothing here opens the file itself and nothing imports a YAML
    parser (R-1, R-3).

    Args:
        scenario_loader: The loader, from `tests/conftest.py`.

    Returns:
        The mapping exactly as `harness/scenarios/clean_batch_sl.yaml` declares it.

    Raises:
        FileNotFoundError: The definition is absent; the message names the path and the
            eight expected definitions.
        ValueError: It is not a YAML mapping, or declares neither spelling of the
            affected-table key, or both.
    """
    return scenario_loader(SCENARIO)


def _system_block(definition: Mapping[str, Any]) -> Mapping[str, Any]:
    """The scenario's `system:` block, which describes the SEEDED RECORD.

    Args:
        definition: The parsed definition.

    Returns:
        The block.

    Raises:
        AssertionError: It is absent or is not a mapping. Its absence is fatal rather
            than defaultable: `file_system_used` lives in it, and a missing pin is the
            false-pass trap of section 3.1 rather than a tidy zero.
    """
    block = definition.get(KEY_SYSTEM)
    assert isinstance(block, Mapping), (
        f"{SCENARIO}: the `{KEY_SYSTEM}:` block is {type(block).__name__} and must be "
        f"a "
        f""
        f"mapping. It carries the pins that describe the SEEDED SYSTEM RECORD - "
        f"`{SYS_FILE_SYSTEM_USED}`, `{SYS_CYCLEA}`, `{SYS_PERIOD}`, `{KEY_DATE_FORM}`, "
        f"`{KEY_IRS_INSTEAD}`, `{SYS_SL_AUTOGEN}` and `{SYS_PL_AUTOGEN}` - none of "
        f"which "
        f"may be defaulted. `{SYS_FILE_SYSTEM_USED}` in particular decides whether the "
        f"frozen handlers touch MySQL at all [common/acas007.cbl:L316-L320], so a "
        f"missing block would let both dumps come back empty and the diff exit zero."
    )
    return block


def _affected_tables(definition: Mapping[str, Any]) -> tuple[str, ...]:
    """The affected-table list, in the order the scenario declares it.

    THE DECLARED ORDER IS LOAD-BEARING and is therefore read rather than sorted: the
    pre-run seed fingerprint is written in declared order, and a disagreement between
    the two runs' fingerprints is a HARNESS FAULT rather than a difference.

    Args:
        definition: The parsed definition.

    Returns:
        The table names, in declared order.

    Raises:
        AssertionError: The key is absent or is not a sequence of names.
    """
    declared = definition.get(KEY_AFFECTED_TABLES)
    assert isinstance(declared, Sequence) and not isinstance(declared, str), (
        f"{SCENARIO}: `{KEY_AFFECTED_TABLES}` is {type(declared).__name__} and must be "
        f"a "
        f"list of table names. IT IS HOW THE COMPARISON IS BOUNDED, and bounding is "
        f"done "
        f"by all 22 in-scope tables, of which this list is the declared subset - "
        f"there is no ignore-list, no "
        f"tolerance-list "
        f""
        f"and no known-difference allowance anywhere in the diff path."
    )
    for position, name in enumerate(declared):
        assert isinstance(name, str), (
            f"{SCENARIO}: `{KEY_AFFECTED_TABLES}` position {position} is "
            f"{type(name).__name__} ({name!r}); every entry must be a table name "
            f"spelled "
            f"exactly as mysql/ACASDB.sql spells it, hyphens included."
        )
    return tuple(declared)


def _seed_files(definition: Mapping[str, Any]) -> tuple[str, ...]:
    """The flat files the seeder stages, from the flat mirror key.

    Args:
        definition: The parsed definition.

    Returns:
        The file names, in declared order.

    Raises:
        AssertionError: The key is absent or is not a sequence of names.
    """
    declared = definition.get(KEY_SEED_FILES)
    assert isinstance(declared, Sequence) and not isinstance(declared, str), (
        f"{SCENARIO}: `{KEY_SEED_FILES}` is {type(declared).__name__} and must be a "
        f"list "
        f"of flat-file names. `harness/seed.sh` stages exactly these into a fresh "
        f"scenario-owned fixture and seeds from them alone, so the resulting state is "
        f"provably attributable to the scenario it is credited to."
    )
    for position, name in enumerate(declared):
        assert isinstance(name, str), (
            f"{SCENARIO}: `{KEY_SEED_FILES}` position {position} is "
            f"{type(name).__name__} ({name!r}); every entry must be one of the "
            f"flat-file "
            f"names the frozen loader script recognises [common/masterLD.sh:L93-L116]."
        )
    return tuple(declared)


def _dump_for(paths: Any, side: str, table: str, harness: Any) -> Mapping[str, Any]:
    """Read one side's NORMALISED dump for one table, asserting it is well formed.

    Delegated to `harness/diff_states.py`'s own `load_dump`, which is the SINGLE
    DEFINITION of the structural contract (R-4) and whose every failure is an exit-2
    condition: the five keys in fixed order and no others, the table in the twenty-two
    name allow-list, the primary key present among the columns,
    `row_count == len(rows)`, no ragged row, NO value a `float` (R-2), no value `null`,
    no primary-key value twice, and the file name agreeing with the table it declares.
    Nothing is reimplemented here and nothing in the returned object is altered.

    THE NORMALISED TREE IS READ, NOT THE RAW ONE. A raw dump still carries the
    representation artefacts normalisation removes, so a verdict taken from one would
    not be evidence.

    Args:
        paths: The run's `ScenarioPaths`.
        side: `cobol` or `python`. Recorded in the PATH, never inside a dump.
        table: The table name, hyphens included.
        harness: The three harness modules, from the `harness` fixture.

    Returns:
        The parsed, asserted dump object.

    Raises:
        Exception: `harness/diff_states.py`'s own errors, every one of which means the
            comparison could not be performed and is therefore a pytest ERROR.
    """
    directory: Path = paths.normalized_dir(side)
    return harness.diff_states.load_dump(directory / f"{table}{DUMP_SUFFIX}")


def _rows_by_key(dump: Mapping[str, Any]) -> dict[Any, Sequence[Any]]:
    """Index one dump's rows by primary-key VALUE.

    ROWS ALIGN BY KEY VALUE, NEVER BY POSITION, which is the same rule
    `harness/diff_states.py` applies - and the reason `1` and `"1"` are different keys
    rather than the same one.

    Args:
        dump: A well-formed dump object.

    Returns:
        The rows, keyed by their primary-key value.
    """
    columns = list(dump["columns"])
    key_index = columns.index(str(dump["primary_key"]))
    return {row[key_index]: row for row in dump["rows"]}


def _column_values(dump: Mapping[str, Any], column: str) -> dict[Any, Any]:
    """One column's values, keyed by primary-key value.

    Args:
        dump: A well-formed dump object.
        column: The column to read.

    Returns:
        The values, keyed by primary key.

    Raises:
        AssertionError: The dump does not carry the column. The schema is frozen, so a
            missing column means either the dump or the checkout is wrong rather than
            that the column is optional.
    """
    columns = list(dump["columns"])
    assert column in columns, (
        f"`{dump['table']}` does not carry a column named {column!r}; it lists "
        f"{columns}. mysql/ACASDB.sql is FROZEN (Agent Action Plan section 0.8.1), so "
        f"this means either the dump or the checkout is wrong."
    )
    index = columns.index(column)
    return {key: row[index] for key, row in _rows_by_key(dump).items()}


def _table_diff(tree: Any, table: str) -> Any:
    """The per-table finding set for one table, out of a completed comparison.

    Args:
        tree: The `TreeDiff`.
        table: The table to look up.

    Returns:
        Its `TableDiff`.

    Raises:
        AssertionError: The table was not compared at all. That is never treated as
            agreement: a table absent from the comparison is a table about which nothing
            was measured, and nothing is exactly what a false pass looks like.
    """
    for candidate in tree.tables:
        if candidate.table == table:
            return candidate
    raise AssertionError(
        f"`{table}` was not compared: the completed comparison covers "
        f"{[entry.table for entry in tree.tables]}. A table absent from the comparison "
        f"has had NOTHING measured about it, which must never be read as agreement "
        f"(R-6)."
    )


# ---------------------------------------------------------------------------
#  THE STACK-FREE ASSERTIONS
#
#  Four of them, and they run on a bare host: a scenario definition, the frozen schema
#  and the three harness Python modules are all files on disk, and loading a harness
#  mmodule needs no Docker, no MariaDB and no GnuCOBOL - two of the three are pure and
#  mthe
#  third opens a connection only when asked to.
#
#  TTHEY ARE NOT DECORATION. Each one guards a way in which the expensive comparison
#  Tcould
#  come back EMPTY FOR THE WRONG REASON, which no amount of running the protocol would
#  reveal.
# ---------------------------------------------------------------------------


def test_scenario_definition_preconditions(
    definition: Mapping[str, Any],
    pinned_clock: Any,
) -> None:
    """Every pin without which this scenario's empty diff would prove nothing.

    THE FALSE-PASS TRAP FIRST. `file_system_used` must be 1.
    [copybooks/wssystem.cob:L112-L114] declares `07  File-System-Used  pic 9.` with
    `88  FS-Cobol-Files-Used  value zero.` and `88  FS-MySql-Used  value 1.`, and every
    frozen handler gates on it - [common/acas007.cbl:L316-L320] verbatim:

        L316       if       not FS-Cobol-Files-Used
        L317                move RDBMS-Flat-Statuses to FA-RDBMS-Flat-Statuses
        L318                perform  ba-Process-RDBMS
        L319                go to AA-Main-Exit
        L320       end-if.

    With zero the handler NEVER TOUCHES MySQL. Both dumps then come back empty, the two
    empty trees are identical, the comparison exits 0 - AND THE RUN IS A SILENT FALSE
    PASS. No stage would report anything wrong.

    THEN THE FAN-OUT SWITCH. `irs_instead` must be a space.
    [copybooks/wssystem.cob:L179-L181] gives it three states and THE THIRD HAS NO
    CONDITION NAME AT ALL, so a space makes both `IRS-Used` and `IRS-Both-Used` False -
    pure General Ledger mode. A-1 IS OBSERVABLE ONLY IN THAT MODE: if this drifts to "Y"
    or "B" then IF#2 at [sales/sl060.cbl:L1175] becomes true, `GL-Posting-Close` starts
    running, and this file SILENTLY STOPS LOCKING ANYTHING. Agent Action Plan section
    0.6.4 is the reason it is pinned at all: "leaving it at a default would make the
    affected-table list ambiguous."

    THEN THE PINNED CLOCK, in both observables and across all three sources - this
    file's literals, the scenario's own two key pairs, and `acas_posting/clock.py`
    through the `pinned_clock` fixture. The binary observable is
    [copybooks/wssystem.cob:L67] `05  Run-Date        binary-long.`, a real `SYSTEM-REC`
    column whose value the cycle stamps into date columns of the tables that ARE dumped,
    so an epoch regression would surface as a table difference rather than as an error;
    catching it here means it is diagnosed at the pin instead of three tables into a
    diff.

    THEN THE AUTOGEN SWITCHES, both of them, so that [sales/sales.cbl:L759]'s dispatch
    of `sl830` returns at [sales/sl830.cbl:L269-L270] before issuing a single verb.

    AND `cyclea` NON-ZERO [copybooks/wssystem.cob:L62]. `period` is asserted PRESENT and
    NOT interpreted: it is an INERT value on this route, because
    `gl_end_of_cycle` appears in no scenario's operation list - a declination recorded
    on six grounds in `harness/scenarios/period_end_totals.yaml` and reversible only by
    measured compiled behaviour (R-6).

    FINALLY THE SEED AND OPERATION CONTRACT: the six flat files, `slautogen.dat` absent,
    the single operation, and the declared status of zero - which peculiarity TWO of the
    module docstring shows to be PROVABLE, since the only term code either program on
    this route raises is 8 and both of its raise sites sit inside `if
    FS-Cobol-Files-Used` ([sales/sl055.cbl:L326] wrapping L344,
    [purchase/pl055.cbl:L266] wrapping L286).

    Needs no stack.

    Args:
        definition: The parsed scenario definition.
        pinned_clock: The project-wide pinned run date, both observables, already
            cross-checked against `acas_posting/clock.py` by the fixture itself.
    """
    system = _system_block(definition)

    # --- IDENTITY -----------------------------------------------------------
    assert definition.get(KEY_NAME) == SCENARIO, (
        f"the definition names itself {definition.get(KEY_NAME)!r} but this file "
        f"drives "
        f""
        f"{SCENARIO!r}. The name is published once and the COBOL-side runner falls "
        f"back "
        f""
        f"to the file's own basename, so the two agree by construction; a disagreement "
        f"means this file and that file are about different runs."
    )
    assert definition.get(KEY_SUBSYSTEM) == SUBSYSTEM, (
        f"{SCENARIO}: `{KEY_SUBSYSTEM}` is {definition.get(KEY_SUBSYSTEM)!r}, expected "
        f"{SUBSYSTEM!r}. The subsystem selects which frozen menu the oracle drives."
    )
    assert definition.get(KEY_OPERATION) == OPERATION, (
        f"{SCENARIO}: `{KEY_OPERATION}` is {definition.get(KEY_OPERATION)!r}, expected "
        f"{OPERATION!r} - the route [sales/sales.cbl:L756-L768] dispatches, `sl055` "
        f"then "
        f"`sl060`. That paragraph is the SEVENTH, proved by [sales/sales.cbl:L545] "
        f'displaying "(G)  Sales Transactions Post"; the eighth belongs to the '
        f"out-of-scope payment route at [sales/sales.cbl:L770-L774]."
    )

    # --- THE FALSE-PASS TRAP  (section 3.1) ---------------------------------
    assert system.get(SYS_FILE_SYSTEM_USED) == FILE_SYSTEM_USED_MYSQL, (
        f"{SCENARIO}: `{KEY_SYSTEM}.{SYS_FILE_SYSTEM_USED}` is "
        f"{system.get(SYS_FILE_SYSTEM_USED)!r} and MUST be "
        f"{FILE_SYSTEM_USED_MYSQL} (`88 FS-MySql-Used value 1.` "
        f"[copybooks/wssystem.cob:L114]).\n"
        f"  THIS IS THE FALSE-PASS TRAP. With zero - `88 FS-Cobol-Files-Used value "
        f"zero.` [copybooks/wssystem.cob:L113] - every frozen handler takes the branch "
        f"at [common/acas007.cbl:L316-L320] and NEVER TOUCHES MySQL. Both dumps would "
        f"come back empty, the two empty trees would be identical, the comparison "
        f"would "
        f""
        f"exit 0 and the scenario would PASS WHILE PROVING NOTHING. The seeded "
        f"`system.dat` must carry the same value, because the twelve posting programs "
        f"read this column off the loaded row."
    )

    # --- THE FAN-OUT SWITCH, WITHOUT WHICH A-1 IS INVISIBLE  (section 3.2) --
    assert system.get(KEY_IRS_INSTEAD) == IRS_INSTEAD_GL_ONLY, (
        f"{SCENARIO}: `{KEY_SYSTEM}.{KEY_IRS_INSTEAD}` is "
        f"{system.get(KEY_IRS_INSTEAD)!r} and MUST be {IRS_INSTEAD_GL_ONLY!r} - PURE "
        f"GENERAL LEDGER MODE.\n"
        f"  [copybooks/wssystem.cob:L179-L181] gives `IRS-Instead pic x` three states, "
        f'and the third - a space - HAS NO CONDITION NAME AT ALL: both `88 IRS-Used '
        f'value "Y".` and `88 IRS-Both-Used value "B".` are simply False.\n'
        f"  A-1 IS OBSERVABLE ONLY IN THIS MODE. [sales/sl060.cbl:L1176] `perform "
        f"SPL-Posting-Close` carries NO TERMINATING PERIOD, so [sales/sl060.cbl:L1177] "
        f"nests inside [sales/sl060.cbl:L1175] and `GL-Posting-Close` runs only when "
        f"(IRS-Used OR IRS-Both-Used) AND (IRS-Both-Used OR G-L). Pin this to \"Y\" or "
        f"\"B\" and IF#2 becomes true, the anomaly vanishes from the diff, and this "
        f"file "
        f"stops locking anything at all (R-4)."
    )
    assert definition.get(KEY_IRS_INSTEAD) == system.get(KEY_IRS_INSTEAD), (
        f"{SCENARIO}: the flat `{KEY_IRS_INSTEAD}` is "
        f"{definition.get(KEY_IRS_INSTEAD)!r} while `{KEY_SYSTEM}.{KEY_IRS_INSTEAD}` "
        f"is "
        f""
        f"{system.get(KEY_IRS_INSTEAD)!r}. The pair exists because the COBOL-side "
        f"runner "
        f"reads TOP-LEVEL KEYS ONLY and cannot see the nested block; the two are "
        f"written "
        f"adjacently precisely so that drift is visible, and drift here would point "
        f"the "
        f""
        f"two sides at different fan-out states."
    )

    # --- THE PINNED CLOCK, ACROSS ALL THREE SOURCES  (section 3.3) ----------
    clock = definition.get(KEY_CLOCK)
    assert isinstance(clock, Mapping), (
        f"{SCENARIO}: the `{KEY_CLOCK}:` block is {type(clock).__name__} and must be a "
        f"mapping carrying `{KEY_CLOCK_TO_DAY}` and `{KEY_CLOCK_RUN_DATE}`."
    )
    assert clock.get(KEY_CLOCK_TO_DAY) == PINNED_TO_DAY, (
        f"{SCENARIO}: `{KEY_CLOCK}.{KEY_CLOCK_TO_DAY}` is "
        f"{clock.get(KEY_CLOCK_TO_DAY)!r}, expected {PINNED_TO_DAY!r}. That is "
        f"`to-day pic x(10)` in DD/MM/CCYY form, the text observable the controlled "
        f"clock "
        f"pins at the command-line boundary."
    )
    assert clock.get(KEY_CLOCK_RUN_DATE) == PINNED_RUN_DATE, (
        f"{SCENARIO}: `{KEY_CLOCK}.{KEY_CLOCK_RUN_DATE}` is "
        f"{clock.get(KEY_CLOCK_RUN_DATE)!r}, expected {PINNED_RUN_DATE}. That is "
        f"`05  Run-Date        binary-long.` [copybooks/wssystem.cob:L67], counted "
        f"from "
        f""
        f"the 1600-12-31 epoch [common/maps04.cbl:L39-L41]."
    )
    assert definition.get(KEY_RUN_DATE_TEXT) == clock.get(KEY_CLOCK_TO_DAY), (
        f"{SCENARIO}: the flat `{KEY_RUN_DATE_TEXT}` is "
        f"{definition.get(KEY_RUN_DATE_TEXT)!r} while `{KEY_CLOCK}.{KEY_CLOCK_TO_DAY}` "
        f"is {clock.get(KEY_CLOCK_TO_DAY)!r}. The COBOL-side runner reads the flat key "
        f"and the Python side the grouped one, so drift would type one date at the "
        f"Date "
        f""
        f"Entry screen and pass another on the command line."
    )
    assert definition.get(KEY_RUN_DATE_BINARY) == clock.get(KEY_CLOCK_RUN_DATE), (
        f"{SCENARIO}: the flat `{KEY_RUN_DATE_BINARY}` is "
        f"{definition.get(KEY_RUN_DATE_BINARY)!r} while "
        f"`{KEY_CLOCK}.{KEY_CLOCK_RUN_DATE}` is {clock.get(KEY_CLOCK_RUN_DATE)!r}."
    )
    assert pinned_clock.to_day == PINNED_TO_DAY, (
        f"the pinned clock's text date is {pinned_clock.to_day!r} while this file and "
        f"{SCENARIO} both declare {PINNED_TO_DAY!r}. `tests/conftest.py` and "
        f"`acas_posting/clock.py` are the other two of the three sources; any two "
        f"disagreeing is a failure, which is why all three are checked here."
    )
    assert pinned_clock.run_date == PINNED_RUN_DATE, (
        f"the pinned clock's binary Run-Date is {pinned_clock.run_date} while this "
        f"file "
        f""
        f"and {SCENARIO} both declare {PINNED_RUN_DATE}. A mismatch is an EPOCH "
        f"REGRESSION in acas_posting/dates.py, and because `Run-Date` is stamped into "
        f"the date columns of the tables this scenario DOES dump, it would otherwise "
        f"surface as a posting difference rather than as an error."
    )

    # `Date-Form` selects only WHICH DIGIT ORDER THE ORACLE TYPES at the Date Entry
    # screen, [copybooks/wssystem.cob:L129-L131]; the Python side fixes DD/MM/CCYY
    # uunconditionally. The asymmetry is documented and deliberate - the two sides agree
    # uon
    # the DATE and differ only in how it is spelled at an input surface the Python side
    # does not have - so the pin is asserted, not the symmetry.
    assert system.get(KEY_DATE_FORM) == DATE_FORM_UK, (
        f"{SCENARIO}: `{KEY_SYSTEM}.{KEY_DATE_FORM}` is "
        f"{system.get(KEY_DATE_FORM)!r}, expected {DATE_FORM_UK} (`88 Date-UK value 1` "
        f"[copybooks/wssystem.cob:L129-L131]), which is the digit order "
        f"{PINNED_TO_DAY!r} is written in."
    )
    assert definition.get(KEY_DATE_FORM) == system.get(KEY_DATE_FORM), (
        f"{SCENARIO}: the flat `{KEY_DATE_FORM}` is {definition.get(KEY_DATE_FORM)!r} "
        f"while `{KEY_SYSTEM}.{KEY_DATE_FORM}` is {system.get(KEY_DATE_FORM)!r}."
    )

    # --- THE AUTOGEN SWITCHES  (section 3.4) --------------------------------
    for key in (SYS_SL_AUTOGEN, SYS_PL_AUTOGEN):
        assert system.get(key) == AUTOGEN_OFF, (
            f"{SCENARIO}: `{KEY_SYSTEM}.{key}` is {system.get(key)!r} and must be "
            f"{AUTOGEN_OFF!r}.\n"
            f"  [sales/sales.cbl:L759] dispatches the OUT-OF-SCOPE `sl830` before "
            f"`sl055` on the COBOL side while acas_posting/cli/sl_invoice_post.py "
            f"dispatches only `sl055` then `sl060`. That asymmetry is harmless ONLY "
            f"because [sales/sl830.cbl:L269-L270] reads `if SL-Autogen not = \"Y\" / "
            f"goback.` and returns before issuing a verb. Set it to \"Y\" and the "
            f"COBOL "
            f""
            f"side would populate the four automatic-generation tables the Python side "
            f"cannot, and no diff over the affected tables could be trusted. The "
            f"fields "
            f""
            f"are [copybooks/wssystem.cob:L274] and [copybooks/wssystem.cob:L209]."
        )

    # --- THE ACCOUNTING CYCLE, AND THE INERT PERIOD  (section 3.5) ----------
    cyclea = system.get(SYS_CYCLEA)
    assert isinstance(cyclea, int) and not isinstance(cyclea, bool) and cyclea != 0, (
        f"{SCENARIO}: `{KEY_SYSTEM}.{SYS_CYCLEA}` is {cyclea!r} and must be a non-zero "
        f"integer. `05  Cyclea          binary-char.` [copybooks/wssystem.cob:L62] is "
        f"the "
        f"accounting cycle the batch filters compare against, so a zero would leave "
        f"the "
        f""
        f"seeded batches unmatched and the capture empty for a reason that is not a "
        f"behavioural difference."
    )
    assert SYS_PERIOD in system, (
        f"{SCENARIO}: `{KEY_SYSTEM}.{SYS_PERIOD}` is absent. It is asserted PRESENT "
        f"and "
        f""
        f"deliberately NOT interpreted: it is an INERT value on this route "
        f"because `gl_end_of_cycle` appears in NO scenario's operation list - a "
        f"declination recorded on six grounds in "
        f"harness/scenarios/period_end_totals.yaml and reversible only by measured "
        f"compiled behaviour (R-6). It is carried because it is part of the seeded "
        f"system "
        f"record and because the key set is uniform, not because any listed operation "
        f"divides by it."
    )

    # --- THE SEED CONTRACT  (section 3.7) -----------------------------------
    seed_files = _seed_files(definition)
    assert set(seed_files) == EXPECTED_SEED_FILES, (
        f"{SCENARIO}: `{KEY_SEED_FILES}` declares {sorted(seed_files)}, expected "
        f"exactly "
        f"{sorted(EXPECTED_SEED_FILES)}. Each name maps to one frozen loader: "
        f"`system.dat` to the four-loader block [common/masterLD.sh:L51-L87] "
        f"(`systemLD`, "
        f"`sys4LD` - WHICH IS WHAT LOADS SYSTOT-REC - `finalLD`, `dfltLD`, in that "
        f"fixed "
        f"order); `analysis.dat` to `analLD` [common/masterLD.sh:L93]; `invoice.dat` "
        f"to "
        f""
        f"`slinvoiceLD` [common/masterLD.sh:L98], which loads SAINVOICE-REC AND "
        f"SAINV-LINES-REC from the one file; `openitm3.dat` to `otm3LD` "
        f"[common/masterLD.sh:L104]; `salesled.dat` to `salesLD` "
        f"[common/masterLD.sh:L112]; and `value.dat` to `valueLD` "
        f"[common/masterLD.sh:L116]."
    )
    assert len(seed_files) == len(set(seed_files)), (
        f"{SCENARIO}: `{KEY_SEED_FILES}` names a file more than once: "
        f"{list(seed_files)}."
    )
    assert MANDATORY_SEED_FILE in seed_files, (
        f"{SCENARIO}: `{MANDATORY_SEED_FILE}` is not among {list(seed_files)}. The "
        f"frozen "
        f"order seeds the system block FIRST and unconditionally "
        f"[common/masterLD.sh:L51-L87], the seeder refuses a scenario that omits it, "
        f"and "
        f"it is what carries `Run-Date` [copybooks/wssystem.cob:L67], the fan-out "
        f"switch "
        f"[copybooks/wssystem.cob:L179-L181] and `File-System-Used` "
        f"[copybooks/wssystem.cob:L112-L114] - without it the menu reaches its "
        f"interactive setup program and the runner blocks on a terminal."
    )
    assert FORBIDDEN_SEED_FILE not in seed_files, (
        f"{SCENARIO}: `{FORBIDDEN_SEED_FILE}` IS SEEDED, and must not be. It is one of "
        f"the eight out-of-scope flat-file names the frozen loader script recognises "
        f"[common/masterLD.sh:L113]; seeding it would populate the very tables this "
        f"scenario asserts empty - `SAAUTOGEN-REC` and `SAAUTOGEN-LINES-REC` - and "
        f"would "
        f"make the `sl830` no-op of [sales/sl830.cbl:L269-L270] UNPROVABLE. Its "
        f"omission "
        f"is load-bearing, not an oversight."
    )

    seed = definition.get(KEY_SEED)
    assert isinstance(seed, Mapping), (
        f"{SCENARIO}: the `{KEY_SEED}:` block is {type(seed).__name__} and must be a "
        f"mapping carrying `{KEY_SEED_DATA_DIR}` and `{KEY_SEED_FILES_NESTED}`."
    )
    assert list(seed.get(KEY_SEED_FILES_NESTED) or ()) == list(seed_files), (
        f"{SCENARIO}: `{KEY_SEED}.{KEY_SEED_FILES_NESTED}` is "
        f"{list(seed.get(KEY_SEED_FILES_NESTED) or ())} while the flat "
        f"`{KEY_SEED_FILES}` "
        f"is {list(seed_files)}. The pair is written adjacently so that drift is "
        f"visible; "
        f"drift would seed one side from a different fixture than the other."
    )
    data_dir = seed.get(KEY_SEED_DATA_DIR)
    assert isinstance(data_dir, str) and data_dir, (
        f"{SCENARIO}: `{KEY_SEED}.{KEY_SEED_DATA_DIR}` is {data_dir!r} and must be a "
        f"non-empty relative directory name."
    )
    assert not Path(data_dir).is_absolute() and ".." not in Path(data_dir).parts, (
        f"{SCENARIO}: `{KEY_SEED}.{KEY_SEED_DATA_DIR}` is {data_dir!r}. It must be a "
        f"RELATIVE name with no upward traversal: its two consumers resolve it against "
        f"different bases, and an absolute path would additionally carry a host "
        f"identity "
        f"into a committed scenario file (R-6)."
    )
    assert definition.get(KEY_SEED_DIR) == data_dir, (
        f"{SCENARIO}: the flat `{KEY_SEED_DIR}` is {definition.get(KEY_SEED_DIR)!r} "
        f"while "
        f"`{KEY_SEED}.{KEY_SEED_DATA_DIR}` is {data_dir!r}."
    )

    # TTHE SEED MUST EXERCISE BOTH MOVING-AVERAGE BLOCKS  (section 3.8). The YAML
    # Texpresses
    # tthis in its own seed contract rather than structurally, because the requirement
    # tis a
    # pproperty of the FLAT FILES - `salesled.dat` must hold at least one customer with
    # ptwo
    # iinvoices and one credit note, `invoice.dat` at least one document of type 2 and
    # ione
    # of type 3, and `openitm3.dat` at least one open credit note of type 3 so that
    # [sales/sl060.cbl:L671-L672] performs `ba000-Cr-Swop`. What IS assertable here is
    # that the three files carrying that fixture are declared, which is the structural
    # half of the requirement; the content half is asserted by the state comparison in
    # `test_moving_average_fields_agree`, which is where a seed of round pounds or a
    # single-document customer shows up as an unexercised column.
    for required in ("salesled.dat", "invoice.dat", "openitm3.dat"):
        assert required in seed_files, (
            f"{SCENARIO}: `{required}` is not seeded, so A-8, A-9 and A-10 cannot be "
            f"observed. `ba000-Sales-Comp` [sales/sl060.cbl:L816] and "
            f"`ba000-Credit-Comp` [sales/sl060.cbl:L832] must BOTH fire for their "
            f"divergence to reach `{SALES_LEDGER_TABLE}`, which needs two invoices and "
            f"one credit note for the SAME customer; and the credit note must be open "
            f"and "
            f"of type 3 for [sales/sl060.cbl:L671-L672] to reach `ba000-Cr-Swop`."
        )

    # --- THE OPERATION AND ANSWER CONTRACT  (section 1.5) -------------------
    operations = definition.get(KEY_OPERATIONS)
    assert list(operations or ()) == [OPERATION], (
        f"{SCENARIO}: `{KEY_OPERATIONS}` is {operations!r}, expected exactly "
        f"[{OPERATION!r}]. It is A FLAT SEQUENCE OF OPERATION NAMES and holds nothing "
        f"else."
    )
    assert definition.get(KEY_OPERATION) in list(operations or ()), (
        f"{SCENARIO}: the singular `{KEY_OPERATION}` is "
        f"{definition.get(KEY_OPERATION)!r} and is not among `{KEY_OPERATIONS}` "
        f"{list(operations or ())}. The singular key names the same operation for the "
        f"oracle-side reader, which sees top-level keys only."
    )
    assert "answers" not in definition, (
        f"{SCENARIO} declares an `answers` mapping. IT MUST NOT: this route promotes "
        f"NO "
        f""
        f"interactive answer at all, because neither `sl055` nor `sl060` has a prompt "
        f"that gates a database write - their prompts are diagnostic acknowledgements "
        f"guarded by `if WS-Caller not = \"xl150\"`, and answering one changes no "
        f"table. "
        f"An answer key here would name a semantic input that does not exist, and the "
        f"option spellings belong to acas_posting/cli/* and are discovered from them."
    )
    statuses = definition.get(KEY_EXPECTED_STATUS)
    assert list(statuses or ()) == [EXPECTED_STATUS_SUCCESS], (
        f"{SCENARIO}: `{KEY_EXPECTED_STATUS}` is {statuses!r}, expected "
        f"[{EXPECTED_STATUS_SUCCESS}] - a flat sequence matching `{KEY_OPERATIONS}` "
        f"POSITIONALLY.\n"
        f"  Zero is PROVABLE here rather than hoped for. Only three in-scope programs "
        f"set "
        f"`WS-Term-Code` at all, and on this route the single raise is 8 at "
        f"[sales/sl055.cbl:L344] - which sits inside `if FS-Cobol-Files-Used` "
        f"[sales/sl055.cbl:L326] while `{SYS_FILE_SYSTEM_USED}` is pinned to "
        f"{FILE_SYSTEM_USED_MYSQL}, so it is unreachable. `WS-Term-Code` is `pic 99` "
        f"[copybooks/wscall.cob:L10], so `load000`'s `< 8` [sales/sales.cbl:L708-L709] "
        f"and `> 7` [sales/sales.cbl:L710-L712] bands are exhaustive and mutually "
        f"exclusive over the whole domain. This is the reference happy path and "
        f"exercises "
        f"none of the five rejection classes."
    )


def test_affected_tables_are_in_scope_and_alphabetical(
    definition: Mapping[str, Any],
    harness: Any,
) -> None:
    """The ten-table DECLARED EFFECT of this scenario, and its four key members.

    THIS LIST IS THE DECLARED EFFECT, NOT THE COMPARISON BOUND - the comparison covers
    all 22 in-scope tables. There is no ignore-list, no tolerance-list and no
    known-difference allowance anywhere in the diff path, which is what makes Agent
    Action Plan section 0.6.6's guarantee - "a non-empty diff is always a real
    behavioral difference" - hold. Of the two structural asymmetries between the sides,
    the menu shell's `overrewrite` exit path [sales/sales.cbl:L628-L641] is CLOSED BY
    REPRODUCTION: it persists key 1 and key 4 ONLY and never key 2 - against
    [general/general.cbl:L656-L672] which persists all three - and
    `acas_posting/cli/args.py::overrewrite` inherits that divergence by writing key 2
    only when the route loaded the defaults record. The other remains: `sl830` runs only
    on the COBOL side, and the scenario pins its inputs so it cannot fire.

    THE LIST ITSELF IS NOT RESTATED HERE (R-4). `harness/scenarios/clean_batch_sl.yaml`
    is its single definition and `harness/dump_tables.py`'s `IN_SCOPE` is the single
    definition of the twenty-two in-scope tables, their single-column primary keys and
    their declared column counts. What is asserted is the list's PROPERTIES, plus the
    four individual memberships without which a specific assertion elsewhere in this
    file would be VACUOUS - and each of those four is named with the reason it is
    needed, so a silent removal fails here with a diagnosis rather than turning a test
    into a no-op.

    THE DECLARED ORDER IS LOAD-BEARING, which is why it is asserted alphabetical rather
    than sorted before use: `harness/run_python_scenario.sh` writes the pre-run seed
    fingerprint in DECLARED ORDER, and two fingerprints that disagree are a HARNESS
    FAULT rather than a behavioural difference. Sorting the list here would make that
    diagnosis impossible.

    THE ELEVEN OUT-OF-SCOPE TABLES ARE NEVER DUMPED. Dumping one would compare state the
    migration does not produce, so `harness/dump_tables.py` refuses an out-of-scope name
    outright; this asserts the scenario never asks.

    Needs no stack: a scenario definition is a file on disk, and loading a harness
    module needs no Docker, no MariaDB and no GnuCOBOL.

    Args:
        definition: The parsed scenario definition.
        harness: The three harness modules, loaded by explicit file path by
            `tests/conftest.py` (R-1) - `harness/` is not a package and must never
            become one.
    """
    tables = _affected_tables(definition)
    in_scope: Mapping[str, Any] = harness.dump_tables.IN_SCOPE
    out_of_scope = harness.dump_tables.OUT_OF_SCOPE

    assert len(tables) == EXPECTED_AFFECTED_TABLE_COUNT, (
        f"{SCENARIO}: `{KEY_AFFECTED_TABLES}` names {len(tables)} table(s), expected "
        f"{EXPECTED_AFFECTED_TABLE_COUNT}: {list(tables)}. The route's verb census "
        f"fixes "
        f"the set - `sl055` reaches `ANALYSIS-REC`, `SAINVOICE-REC` with "
        f"`SAINV-LINES-REC`, and `VALUEANAL-REC`; `sl060` reaches `GLBATCH-REC`, "
        f"`GLPOSTING-REC`, `SAITM3-REC`, `SALEDGER-REC` and `VALUEANAL-REC` again; "
        f"`PSIRSPOST-REC` is the unchanged witness for A-18; and `SYSTOT-REC` carries "
        f"the "
        f"four period-total writes. `GLLEDGER-REC` is DELIBERATELY ABSENT because "
        f"`sl060` "
        f"issues no `GL-Nominal-*` verb of any kind."
    )
    assert list(tables) == sorted(tables), (
        f"{SCENARIO}: `{KEY_AFFECTED_TABLES}` is not in ascending order: "
        f"{list(tables)} "
        f""
        f"against {sorted(tables)}. THE DECLARED ORDER IS LOAD-BEARING - "
        f"harness/run_python_scenario.sh writes the pre-run seed fingerprint in "
        f"declared "
        f"order and a disagreement between the two runs' fingerprints is a HARNESS "
        f"FAULT, "
        f"not a difference - so the order is asserted here rather than normalised at "
        f"the "
        f"point of use."
    )
    assert len(tables) == len(set(tables)), (
        f"{SCENARIO}: `{KEY_AFFECTED_TABLES}` names a table more than once: "
        f"{list(tables)}. A repeated entry would be dumped twice and reported twice."
    )

    for table in tables:
        assert table in in_scope, (
            f"{SCENARIO}: `{KEY_AFFECTED_TABLES}` names {table!r}, which is not one of "
            f"the {len(in_scope)} in-scope tables harness/dump_tables.py declares. The "
            f"inventory has exactly one definition in this repository (R-4) and every "
            f"entry is re-checked against a live information_schema on every dump, so "
            f"a "
            f""
            f"name absent from it is either a typo or an out-of-scope table."
        )
        assert table not in out_of_scope, (
            f"{SCENARIO}: `{KEY_AFFECTED_TABLES}` names the OUT-OF-SCOPE table "
            f"{table!r}. "
            f"The eleven out-of-scope tables are present in the frozen schema but "
            f"never "
            f""
            f"touched by the posting cycle (Agent Action Plan section 0.2.2), so "
            f"dumping "
            f"one would compare state the migration does not produce."
        )
        specification = in_scope[table]
        assert not set(specification.primary_key) & set(", "), (
            f"`{table}`'s primary key is declared {specification.primary_key!r}, which "
            f"is "
            f"not a single column name. A dump orders by ONE column with no tie-break "
            f"[mysql/ACASDB.sql:L{specification.schema_line}], so a composite key "
            f"would "
            f""
            f"leave the row order undetermined - and Agent Action Plan section 0.6.6's "
            f"guarantee rests on all twenty-two having a single-column key."
        )

    # THE FOUR MEMBERSHIPS THE EVIDENCE BELOW WOULD BE VACUOUS WITHOUT.
    assert GL_POSTING_TABLE in tables, (
        f"{SCENARIO}: `{GL_POSTING_TABLE}` is not on the affected-table list, so A-1 "
        f"CANNOT BE OBSERVED AT ALL. It is on the list BECAUSE OF A-1: it is where the "
        f"effect - or, in pure General Ledger mode, the NON-effect - of the posting "
        f"file "
        f"that [sales/sl060.cbl:L1176-L1178] never closes becomes visible. Removing it "
        f"would turn `test_a1_missing_period_gl_posting_close_not_executed` into a "
        f"no-op "
        f"while leaving the suite green."
    )
    assert SALES_LEDGER_TABLE in tables, (
        f"{SCENARIO}: `{SALES_LEDGER_TABLE}` is not on the affected-table list, so "
        f"A-8, "
        f""
        f"A-9, A-10 and A-11 cannot be observed. It is the table the moving-average "
        f"columns [copybooks/wssl.cob:L46-L52] and the two signed money columns "
        f"[copybooks/wssl.cob:L54-L55] land in, 37 columns at [mysql/ACASDB.sql:L945]."
    )
    assert IRS_TRANSFER_TABLE in tables, (
        f"{SCENARIO}: `{IRS_TRANSFER_TABLE}` is not on the affected-table list. It is "
        f"the "
        f"UNCHANGED WITNESS for A-18: the transfer-file block at "
        f"[sales/sl060.cbl:L1126-L1142] is gated by the fan-out switch and does not "
        f"execute in pure General Ledger mode, so comparing the table and finding the "
        f"two "
        f"sides agree is the NEGATIVE HALF of A-18's evidence. The positive half needs "
        f"a "
        f"scenario pinning the switch to \"Y\" or \"B\"."
    )
    assert PERIOD_TOTALS_TABLE in tables, (
        f"{SCENARIO}: `{PERIOD_TOTALS_TABLE}` is not on the affected-table list. Four "
        f"of "
        f"the nine period-total write sites are on this route - [sales/sl055.cbl:L675] "
        f"under `if ih-type = 2` at L674, [sales/sl055.cbl:L677] under `if ih-type = "
        f"3` "
        f"at "
        f"L676, [sales/sl060.cbl:L641], and [sales/sl060.cbl:L700], the last being "
        f"UNCONDITIONAL and outside the print guard at [sales/sl060.cbl:L695] - and "
        f"those "
        f"nine sites are the SOLE writers of the totals record.\n"
        f"  It carries a recorded caveat, `Q-CLI-SYSREC-PINS` in "
        f"docs/migration/ambiguity-resolutions.md: its persistence depends on the "
        f"Python "
        f"entry point reproducing the menu's key-4 `overrewrite` "
        f"[sales/sales.cbl:L636-L638], which acas_posting/cli/sl_invoice_post.py does, "
        f"leaving only the three command-line-pinned columns open. IF IT DIVERGES THAT "
        f"IS "
        f"A REAL SIGNAL: it is never resolved with an ignore-list."
    )


def test_autogen_tables_untouched(
    definition: Mapping[str, Any],
    harness: Any,
) -> None:
    """The four automatic-generation tables are neither seeded nor compared.

    THE ONE ASYMMETRY THAT COULD NOT BE BOUNDED AWAY IF IT MATTERED.
    [sales/sales.cbl:L759] dispatches `sl830` before `sl055` on the COBOL side, while
    `acas_posting/cli/sl_invoice_post.py` dispatches only `sl055` then `sl060` - the
    `sl800` to `sl830` series is explicitly out of scope (Agent Action Plan section
    0.2.2). It is harmless only because [sales/sl830.cbl:L269-L270] reads

        L269       if       SL-Autogen not = "Y"    *> SL Autogen not in use
        L270                goback.

    and this scenario pins `sl_autogen` to a space, so the program returns before
    issuing a single verb. Purchase's `pl830` is COMMENTED OUT entirely
    [purchase/purchase.cbl:L755-L758] - a fourth divergence between the two menus,
    PRESERVED AND NOT HARMONISED (R-4).

    THE RESOLUTION IS STRUCTURAL AND HAS THREE PARTS, of which this asserts the two that
    need no stack: the four tables are never seeded, and they appear on no
    affected-table list. THE THIRD PART BELONGS TO THE RUNNERS - both assert after their
    run that all four are still EMPTY, which is the authoritative check, because rows in
    them would mean the two sides were not doing comparable work and no diff over the
    affected tables could be trusted.

    Needs no stack.

    Args:
        definition: The parsed scenario definition.
        harness: The three harness modules; its `OUT_OF_SCOPE` set is the authority on
            what is out of scope, and each of the four names is cross-checked against it
            so that this file's tuple cannot drift into a second definition.
    """
    tables = _affected_tables(definition)
    seed_files = _seed_files(definition)
    out_of_scope = harness.dump_tables.OUT_OF_SCOPE

    for table in AUTOGEN_TABLES:
        assert table in out_of_scope, (
            f"{table!r} is not in harness/dump_tables.py's OUT_OF_SCOPE set, which is "
            f"the "
            f"authority on scope. Either the inventory changed or this file's tuple is "
            f"wrong; it is cross-checked here precisely so that the two cannot diverge "
            f"silently (R-4)."
        )
        assert table not in tables, (
            f"{SCENARIO}: `{KEY_AFFECTED_TABLES}` names the automatic-generation table "
            f"{table!r}. The four are NEVER on any affected-table list: "
            f"[sales/sales.cbl:L759] dispatches `sl830` on the COBOL side only, so "
            f"comparing them would report a FALSE FAILURE if `sl830` ever wrote, and "
            f"would conceal the fact that it did not if it silently agreed. The "
            f"runners' "
            f"still-empty database assertion is the check that matters, and it needs "
            f"these "
            f"tables OFF the list to stay meaningful."
        )

    assert FORBIDDEN_SEED_FILE not in seed_files, (
        f"{SCENARIO}: `{FORBIDDEN_SEED_FILE}` is seeded. Seeding the Sales "
        f"automatic-generation loader [common/masterLD.sh:L113] would populate the "
        f"very "
        f""
        f"tables the runners assert empty and would make the `sl830` no-op UNPROVABLE."
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

    DRIVEN THROUGH THE SHIPPED COMPARISON, AND THROUGH ONE IMPLEMENTATION.
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


# ---------------------------------------------------------------------------
#  THE STACK-BACKED ASSERTIONS
#
#  Five readings of ONE comparison. The `parity` fixture performs the ten stages and
#  applies the stack skip guard, so on a host without the Compose stack and the built
#  oracle each of these SKIPS with a precise, multi-line reason naming every missing
#  precondition - collection always succeeds.
#
#  EVERY ONE IS FRAMED AS "THE TWO SIDES AGREE", NEVER AS "THE FIGURE IS RIGHT". A test
#  that asserted correct accounting rather than observed behaviour would itself be a
#  defect under the inverted premise of Agent Action Plan section 0.8.2. Nothing below
#  recomputes a monetary value, and nothing asserts that a ledger balances.
# ---------------------------------------------------------------------------


@pytest.mark.database
@pytest.mark.oracle
def test_clean_batch_post_sl_state_parity(
    parity: Any,
    definition: Mapping[str, Any],
    harness: Any,
) -> None:
    """THE HEADLINE: the migrated Sales cycle reproduces the compiled oracle EXACTLY.

    Agent Action Plan section 0.8.5, criterion 1: "seed identically through the
    maintainer's load programs, run the compiled cycle, dump the affected tables
    ordering-normalised, reset, run the Python cycle, dump again - and the diff MUST BE
    EMPTY."

    The ten stages ran in the fixture, so every stage whose failure destroys the
    evidence - the seed, the reset, either dump, either normalisation, and the
    comparison itself with exit 2 - is already a pytest ERROR by the time this body
    runs. What is left here is the VERDICT, so that a genuine behavioural difference is
    a pytest FAILURE. The two can never be confused, which is the entire reason for the
    split.

    THE VERDICT IS TRUSTWORTHY BY CONSTRUCTION. Agent Action Plan section 0.6.6: the
    dump is `SELECT * FROM <table> ORDER BY <primary key>` with no tie-breaking, no
    timestamp masking and no surrogate-key remapping, because every in-scope table has a
    single-column primary key, zero secondary indexes, no `TIMESTAMP` column and no
    `AUTO_INCREMENT`. So "a non-empty diff is always a real behavioral difference and
    never an artefact of the comparison."

    THE TWO RUN STATUSES ARE ALSO ASSERTED, and asserted against the scenario's OWN
    declaration rather than against a literal expectation of success: this is the
    reference happy path and declares zero, and that zero is provable rather than hoped
    for - see `test_scenario_definition_preconditions`. The two sides' dispositions are
    additionally required to AGREE, which catches the case where one side succeeded and
    the other aborted into a state that happened to look the same.

    NO COMPARISON IS WRITTEN HERE. `TreeDiff.is_empty` is the pass condition and
    `harness/diff_states.py`'s own `render` supplies the detail, which keeps the report
    a test reads byte-identical to the one an operator reads out of `diff.txt`.

    Args:
        parity: The completed ten-stage run, memoised for the module.
        definition: The parsed scenario definition, for its declared expected status.
        harness: The three harness modules, for `render`.
    """
    declared_status = list(definition.get(KEY_EXPECTED_STATUS) or ())[0]

    # THE TWO RUN STAGES FIRST, because a run that did not do what the scenario declared
    # makes the verdict unattributable even when it is empty. The statuses were RECORDED
    # and never allowed to skip the dumps that followed them: Agent Action Plan section
    # 00.6.5 makes ABSENCE EVIDENCE, so short-circuiting a dump on a non-zero status
    # 0would
    # destroy exactly the evidence a rejection scenario depends on.
    assert parity.cobol_run.returncode == declared_status, (
        f"{SCENARIO}: THE COMPILED ORACLE exited {parity.cobol_run.returncode} while "
        f"the "
        f"scenario declares {declared_status}.\n"
        f"{parity.cobol_run.describe()}\n"
        f"  Only three in-scope programs set `WS-Term-Code` at all, and the single "
        f"raise "
        f"on this route is 8 at [sales/sl055.cbl:L344], inside `if "
        f"FS-Cobol-Files-Used` "
        f""
        f"[sales/sl055.cbl:L326] - unreachable while `{SYS_FILE_SYSTEM_USED}` is "
        f"pinned "
        f""
        f"to {FILE_SYSTEM_USED_MYSQL}. So a non-zero status here is either a term code "
        f"that should not be reachable or a harness fault, and the two are "
        f"distinguished "
        f"by the runner's own documented exit bands."
    )
    assert parity.python_run.returncode == declared_status, (
        f"{SCENARIO}: THE MIGRATED CYCLE exited {parity.python_run.returncode} while "
        f"the "
        f"scenario declares {declared_status} and the oracle exited "
        f"{parity.cobol_run.returncode}.\n"
        f"{parity.python_run.describe()}\n"
        f"  An `argparse` usage exit of 2 means the RUNNER BUILT A BAD COMMAND LINE - "
        f"a "
        f""
        f"harness fault, never a behavioural difference. The promoted-flag spellings "
        f"belong to acas_posting/cli/* and harness/run_python_scenario.sh probes for "
        f"them; this file constructs no command line at all."
    )

    # THE HEADLINE.
    assert parity.is_empty, (
        f"{SCENARIO}: THE MIGRATED SALES CYCLE DID NOT REPRODUCE THE COMPILED ORACLE. "
        f"{parity.tree.total_differences} finding(s) across "
        f"{len(parity.tree.differing)} of {len(parity.tables)} bounded table(s) "
        f"{list(parity.tables)}.\n"
        f"\n"
        f"  THE LABELS ARE `{SIDE_COBOL}` AND `{SIDE_PYTHON}`: `{SIDE_COBOL}` is the "
        f"compiled COBOL, which IS the specification (Agent Action Plan section "
        f"0.8.2), "
        f""
        f"and `{SIDE_PYTHON}` is the migrated cycle. Where they differ, THE COBOL IS "
        f"RIGHT BY DEFINITION - including where it is wrong, because a defect "
        f"reproduced "
        f"is correct and a defect fixed is a failure (R-4).\n"
        f"\n"
        f"{parity.diagnose()}"
        f"\n"
        f"  Full report at {parity.outcome.report}; every stage's outcome follows.\n"
        f"{parity.describe()}\n"
        f"\n"
        f"  WHAT TO SUSPECT, in order. A monetary figure differing by pence: the "
        f"truncation direction, which is ROUND_DOWN everywhere on this route because "
        f"there is no `ROUNDED` site in either program. An integer statistics column "
        f"differing: A-8's double truncation, whose accumulator has ZERO decimal "
        f"places "
        f""
        f"[sales/sl060.cbl:L206] against a two-place addend [sales/sl060.cbl:L218], or "
        f"A-9's missing counter increment, or A-11's sign narrowing at the bridge. "
        f"`{GL_POSTING_TABLE}` differing: A-1, [sales/sl060.cbl:L1172-L1178]. "
        f"`{PERIOD_TOTALS_TABLE}` differing: the four period-total sites, and the "
        f"`Q-CLI-SYSREC-PINS` question recorded in "
        f"docs/migration/ambiguity-resolutions.md. A character column differing only "
        f"in "
        f""
        f"padding: A-12, and normalisation job 1 - but job 1 strips TRAILING spaces "
        f"only, "
        f"because a COBOL alphanumeric `MOVE` is left-justified so LEADING SPACES ARE "
        f"CONTENT.\n"
        f"\n"
        f"  DO NOT MAKE THIS PASS BY NORMALISING IT. There is no ignore-list, no "
        f"tolerance-list and no known-difference allowance in this file or in the diff "
        f"path, and adding one would destroy the only property this migration has: "
        f"that "
        f""
        f"the Python cycle can replace the COBOL cycle without changing a single "
        f"posted "
        f""
        f"figure. Fix the cycle, or - if the oracle turns out to do something "
        f"surprising - reproduce the surprise, because the surprise is the "
        f"specification "
        f"(R-6)."
    )


@pytest.mark.database
@pytest.mark.oracle
def test_a1_missing_period_gl_posting_close_not_executed(
    parity: Any,
    harness: Any,
) -> None:
    """A-1, THE ANOMALY LOCK. DO NOT ADD THE MISSING PERIOD TO `sl060`.

    [sales/sl060.cbl] `ca000-BL-Close section.` opens at L1158. Verbatim:

        L1161       perform  GL-Batch-Write                     *>   write Batch-record.
        L1162-L1171 <the fs-reply error block, ending `end-if`>
        L1172       if       IRS-Both-Used OR G-L    *> THIS IS IN PURCHASE PL060
        L1173                move     RRN  to  postings.     *> Why ?
        L1174       perform  GL-Batch-Close.                   *>    close Batch-file.
        L1175       if       IRS-Used OR IRS-Both-Used
        L1176                perform SPL-Posting-Close      *>  close irs-post-file
        L1177       if       IRS-Both-Used or G-L
        L1178                perform GL-Posting-Close.       *>    close posting-file.
        L1180  ca999-main-exit.

    L1173 ends IF#1 with a period. L1174 is therefore UNCONDITIONAL. L1175 opens IF#2.
    L1176 CARRIES NO TERMINATING PERIOD, so L1177's IF#3 is NESTED INSIDE IF#2, and the
    single period at the end of L1178 closes BOTH. `GL-Posting-Close` therefore executes
    only when

        (`IRS-Used` OR `IRS-Both-Used`)  AND  (`IRS-Both-Used` OR `G-L`)

    and IN PURE GENERAL LEDGER MODE IF#2 IS FALSE, SO IT NEVER EXECUTES AT ALL. `G-L` is
    `88  G-L  value 1.` on the installed-ledger level byte
    [copybooks/wssystem.cob:L84-L85] and NOT on the fan-out switch, so pure General
    Ledger mode is the two-field statement `Level-1 = 1` AND `IRS-Instead = space` -
    which makes IF#1 and IF#3 true while IF#2 is false.

    THE THREE CONTROLS, EACH WITH THE PERIOD PRESENT, verified verbatim in this
    checkout:

        [purchase/pl060.cbl:L1031]   `perform SPL-Posting-Close.`   period PRESENT
        [sales/sl100.cbl:L694]       `perform SPL-Posting-Close.`   period PRESENT
        [purchase/pl100.cbl:L675]    `perform SPL-Posting-Close.`   period PRESENT

    All four sites carry the identical maintainer comment `*> THIS IS IN PURCHASE PL060`
    and the identical `*> Why ?` of A-17 on the line below it. THREE OF THE FOUR HAVE
    THE PERIOD AND ONE DOES NOT, which is what proves A-1 is an accident of
    transcription rather than a house idiom - and
    `tests/scenarios/test_clean_batch_post_pl.py` is its control.

    THIS TEST ASSERTS THAT THE TWO SIDES AGREE, AND NOTHING ELSE. It does not assert
    that the posting file is closed, nor that closing it would be better, nor that any
    figure
    in the table is correct. The claim is exactly: WHATEVER THE COMPILED PROGRAM LEFT IN
    `GLPOSTING-REC` IN PURE GENERAL LEDGER MODE, THE MIGRATED CYCLE LEFT THE SAME THING.
    That is the only claim the inverted premise of Agent Action Plan section 0.8.2
    permits:
    "A defect reproduced is correct; a defect fixed is a failure."

    SO DO NOT ADD THE MISSING PERIOD - and note WHICH test catches you if you do
. NOT THIS ONE. A well-meaning correction to
    [sales/sl060.cbl:L1176], or a translation of `ca000-BL-Close` that "obviously"
    closes the posting file, changes which VERBS are performed and changes NO ROW,
    because a close writes nothing. This test would stay green. The lock is
    `tests/arithmetic/test_double_entry_explosion.py::test_a1_the_posting_close_follows_the_nested_predicate`,
    which drives the shipped paragraph and asserts the verb sequence over the full
    two-field truth table; it was verified to fail on exactly the pure-GL row when the
    period was added. Recorded as A-1 in `docs/migration/anomaly-log.md`, where its
    status is REPRODUCED, its dagger marks it test-locked, and this assertion is listed
    as a state WITNESS rather than the lock.

    THE COMPARISON IS MADE TWICE, deliberately. The `TableDiff` LOCALISES a difference
    to a primary key and a column, which is what makes a failure actionable; the direct
    row-by-row comparison of the two normalised dumps is the check that the localisation
    was performed at all, so that a `TableDiff` which reported nothing because the table
    was never read cannot read as agreement.

    Args:
        parity: The completed ten-stage run.
        harness: The three harness modules, for `load_dump` and `render`.
    """
    assert GL_POSTING_TABLE in parity.tables, (
        f"{SCENARIO}: `{GL_POSTING_TABLE}` was not among the bounded tables "
        f"{list(parity.tables)}, so A-1 WAS NOT MEASURED. That is never agreement: "
        f"this "
        f""
        f"table is on the affected-table list precisely because it is where the effect "
        f"- "
        f"or in pure General Ledger mode the NON-effect - of the posting close at "
        f"[sales/sl060.cbl:L1176-L1178] becomes visible."
    )

    finding = _table_diff(parity.tree, GL_POSTING_TABLE)

    assert finding.is_empty, (
        f"{SCENARIO}: A-1's WITNESS TABLE `{GL_POSTING_TABLE}` DIFFERS between the two "
        f"sides - {finding.total_differences} finding(s).\n"
        f"\n"
        f"{harness.diff_states.summarise(
            harness.diff_states.TreeDiff(tables=(finding,)), report_path=None
        )}"
        f"\n"
        f"  READ THE `{SIDE_COBOL}` COLUMN AS THE SPECIFICATION. In pure General "
        f"Ledger "
        f""
        f"mode - which this scenario pins with `{KEY_IRS_INSTEAD}: "
        f"{IRS_INSTEAD_GL_ONLY!r}` - `GL-Posting-Close` NEVER EXECUTES, because "
        f"[sales/sl060.cbl:L1176] `perform SPL-Posting-Close` carries NO TERMINATING "
        f"PERIOD and so nests [sales/sl060.cbl:L1177]'s condition inside "
        f"[sales/sl060.cbl:L1175]'s. `GL-Posting-Write` still runs; only the CLOSE is "
        f"unreachable.\n"
        f"\n"
        f"  IF YOU HAVE JUST 'FIXED' THAT MISSING PERIOD, OR TRANSLATED "
        f"`ca000-BL-Close` SO THAT IT CLOSES THE POSTING FILE, REVERT IT. Three "
        f"sibling "
        f""
        f"programs have the period - [purchase/pl060.cbl:L1031], "
        f"[sales/sl100.cbl:L694] "
        f""
        f"and [purchase/pl100.cbl:L675] - and `sl060` does not; that asymmetry IS THE "
        f"SPECIFICATION, not a bug to be normalised (R-4). A defect reproduced is "
        f"correct; a defect fixed is a failure (Agent Action Plan section 0.8.2). The "
        f"register entry is A-1 in docs/migration/anomaly-log.md and this test is its "
        f"lock.\n"
        f"\n"
        f"  IF YOU HAVE NOT TOUCHED THAT SITE, suspect instead the posting-record "
        f"fields "
        f"`GL-Posting-Write` writes on this route, or the batch-number and posting-key "
        f"derivation - not the close, which does nothing observable to a table in "
        f"either "
        f"language."
    )

    # THE SECOND, INDEPENDENT READING. Both normalised dumps are read directly and
    # ccompared row by row, so that a `TableDiff` which found nothing because the table
    # cwas
    # nnever read cannot be mistaken for agreement. `load_dump` is the single definition
    # nof
    # tthe structural contract and every one of its failures is an exit-2 condition,
    # thence
    # a pytest ERROR rather than a pass.
    cobol_dump = _dump_for(parity.paths, SIDE_COBOL, GL_POSTING_TABLE, harness)
    python_dump = _dump_for(parity.paths, SIDE_PYTHON, GL_POSTING_TABLE, harness)

    assert list(cobol_dump["columns"]) == list(python_dump["columns"]), (
        f"`{GL_POSTING_TABLE}`'s column lists disagree between the two sides: "
        f"{list(cobol_dump['columns'])} against {list(python_dump['columns'])}. Rows "
        f"are "
        f"POSITIONAL, so two different column orders have no meaningful alignment and "
        f"the "
        f"row comparison below would be nonsense - which is why this is asserted first."
    )
    assert cobol_dump["row_count"] == python_dump["row_count"], (
        f"`{GL_POSTING_TABLE}` holds {cobol_dump['row_count']} row(s) on the "
        f"{SIDE_COBOL} side and {python_dump['row_count']} on the {SIDE_PYTHON} side. "
        f"A-1 concerns the CLOSE and not the WRITE, so a row-count difference is a "
        f"posting difference rather than an A-1 regression - but it is reported here "
        f"because this is where the two sides' posting output is compared."
    )

    cobol_rows = _rows_by_key(cobol_dump)
    python_rows = _rows_by_key(python_dump)
    assert set(cobol_rows) == set(python_rows), (
        f"`{GL_POSTING_TABLE}`'s primary keys disagree. Present only on the "
        f"{SIDE_COBOL} side: {sorted(set(cobol_rows) - set(python_rows), key=repr)}; "
        f"present only on the {SIDE_PYTHON} side: "
        f"{sorted(set(python_rows) - set(cobol_rows), key=repr)}. Rows align by "
        f"primary-key VALUE and never by position, so `1` and `\"1\"` are different "
        f"keys "
        f"rather than the same one."
    )
    for key in cobol_rows:
        assert list(cobol_rows[key]) == list(python_rows[key]), (
            f"`{GL_POSTING_TABLE}` row {key!r} differs between the two sides:\n"
            f"  {SIDE_COBOL}:  {list(cobol_rows[key])}\n"
            f"  {SIDE_PYTHON}: {list(python_rows[key])}\n"
            f"  The comparison is EXACT - no tolerance, no epsilon, no numeric "
            f"coercion "
            f"- "
            f"so a `str` against an `int` IS a difference. The `{SIDE_COBOL}` values "
            f"are "
            f"the specification."
        )

    # AAND THE STATEMENT THIS TEST IS REALLY ABOUT: whatever the compiled program
    # Aproduced
    # was reproduced. Stated as its own assertion so that the test cannot pass by
    # comparing an empty pair of dumps that neither side ever wrote to - that would be
    # agreement about nothing, which is the false-pass shape section 3.1 guards against
    # at the other end of the protocol.
    assert cobol_dump["row_count"] > 0, (
        f"`{GL_POSTING_TABLE}` is EMPTY ON BOTH SIDES, so this test agrees about "
        f"nothing "
        f"and A-1 is not locked by it.\n"
        f"  `sl060` writes the posting record through `GL-Posting-Write` on this "
        f"route, "
        f"so "
        f"an empty table means the run posted nothing at all. Suspect, in order: a "
        f"seed "
        f""
        f"whose invoice headers do not pass `sl055`'s four filters "
        f"[sales/sl055.cbl:L426-L438] - the already-analysed skip at L427-L428, the "
        f"PROFORMA filter at L430-L431, or the PENDING and status-byte filter at "
        f"L433-L436; `{KEY_SYSTEM}.{SYS_CYCLEA}` not matching the seeded batches; or "
        f"`{SYS_FILE_SYSTEM_USED}` reaching the handlers as zero, which is the "
        f"false-pass "
        f"trap of [common/acas007.cbl:L316-L320]."
    )


@pytest.mark.database
@pytest.mark.oracle
def test_moving_average_fields_agree(
    parity: Any,
    harness: Any,
    frozen_schema: Mapping[str, Mapping[str, Any]],
) -> None:
    """A-8, A-9 AND A-10 at state level: both sides agree on the average AND its
    counter.

    THE THREE ANOMALIES, each verified verbatim in this checkout.

    A-8, DOUBLE TRUNCATION. `ba000-Sales-Comp section.` opens at
    [sales/sl060.cbl:L816]; its guard is L819-L824, `add 1 to sales-activety.` is L825,
    and the two truncations are L826 and L827:

        L825      add      1 to sales-activety.
        L826      add      work-goods to work-2.
        L827      divide   sales-activety into work-2 giving sales-average.

    The accumulator has ZERO DECIMAL PLACES - [sales/sl060.cbl:L206]
    `03  work-2  pic s9(14)  comp-3.` - while the addend has TWO -
    [sales/sl060.cbl:L218] `03  work-goods  pic s9(7)v99  comp-3.` - so PENCE ARE
    DISCARDED AT L826. The divide at L827 then discards the remainder as well, because
    `Sales-Average` is `binary-long` [copybooks/wssl.cob:L49] - an INTEGER - and integer
    truncation is what makes A-8 reproducible at all.

    A-9, THE COUNTER THAT IS NEVER INCREMENTED. `ba000-Credit-Comp section.` opens at
    [sales/sl060.cbl:L832]: guard L835-L840, an EXTRA guard `if work-2 not = zero` at
    L841, the add at L842 and the divide at L843. THERE IS NO `add 1 to sales-activety`
    ANYWHERE IN THAT SECTION, so the FIRST credit note for a customer is silently
    dropped from the average - the divisor is whatever the invoice path last left.

    A-10, THREE MUTUALLY INCONSISTENT GUARDS ON ONE IDIOM: [sales/sl060.cbl:L819] tests
    two conditions and increments before dividing; [sales/sl060.cbl:L835] tests the same
    two, adds a third at L841 and never increments; and [sales/sl100.cbl:L506] tests ONE,
    increments at L510 and returns early on a zero cleared date at L500-L501. Its L511
    reads `divide work-b by sales-pay-activety giving sales-pay-average` where L827 reads
    `divide sales-activety into work-2 giving sales-average` - two SPELLINGS of the same
    quotient, accumulator over counter, and NOT an inverted computation. The divergence is
    in the guards and the counter handling.

    WHAT THIS TEST ASSERTS, AND WHAT IT REFUSES TO ASSERT. It asserts that the two sides
    produced THE SAME values in the average column and in its activity counter. IT DOES
    NOT RECOMPUTE THE AVERAGE - that is arithmetic-tier work and belongs to
    `tests/arithmetic/`, which owns the per-field truncation parity against values
    captured from the compiled oracle. Recomputing it here would substitute this file's
    arithmetic for the oracle's, which is the one thing rule R-6 forbids.

    THE TYPE SPLIT IS ASSERTED TOO, because A-8 depends on it. The seven statistics
    fields are `binary-long` [copybooks/wssl.cob:L46-L52] and reach the dump as JSON
    INTEGERS, while the two money fields are `pic s9(8)v99 comp-3`
    [copybooks/wssl.cob:L54-L55] and reach it as canonical JSON DECIMAL STRINGS. Blur
    that split - carry two decimal places through the accumulator, or make the average a
    `Decimal` - and A-8's integer truncation disappears. Neither side may hold a `float`
    (R-2), which `load_dump` refuses outright.

    A-10's THIRD-VARIANT COLUMNS ARE COMPARED AS UNCHANGED WITNESSES. `sl100` owns them
    and does not run on this route, so they are expected to agree at their seeded
    values; comparing them is what makes the divergence between the two routes
    attributable rather than merely present.

    Args:
        parity: The completed ten-stage run.
        harness: The three harness modules.
        frozen_schema: `mysql/ACASDB.sql` parsed to `{table: {column: type}}`. READ,
            never written - Agent Action Plan section 0.8.1 makes any diff against it
            a defect.
    """
    assert SALES_LEDGER_TABLE in parity.tables, (
        f"{SCENARIO}: `{SALES_LEDGER_TABLE}` was not among the bounded tables "
        f"{list(parity.tables)}, so A-8, A-9, A-10 and A-11 WERE NOT MEASURED."
    )

    cobol_dump = _dump_for(parity.paths, SIDE_COBOL, SALES_LEDGER_TABLE, harness)
    python_dump = _dump_for(parity.paths, SIDE_PYTHON, SALES_LEDGER_TABLE, harness)

    assert cobol_dump["row_count"] > 0, (
        f"`{SALES_LEDGER_TABLE}` is EMPTY on the {SIDE_COBOL} side, so the "
        f"moving-average "
        f"blocks were never reached and this test agrees about nothing. The seed must "
        f"carry at least one customer with TWO INVOICES AND ONE CREDIT NOTE, so that "
        f"`ba000-Sales-Comp` [sales/sl060.cbl:L816] and `ba000-Credit-Comp` "
        f"[sales/sl060.cbl:L832] both fire; `salesled.dat` is what carries it."
    )

    columns = list(cobol_dump["columns"])
    assert columns == list(python_dump["columns"]), (
        f"`{SALES_LEDGER_TABLE}`'s column lists disagree: {columns} against "
        f"{list(python_dump['columns'])}. Rows are POSITIONAL, so nothing below would "
        f"align."
    )

    # A-8 AND A-9: THE AVERAGE AND ITS COUNTER, WHICH MUST BE READ TOGETHER. The average
    # aalone would not distinguish A-9 from correct behaviour, because a wrong divisor
    # aand a
    # wrong dividend can produce the same quotient; the counter is the field A-9 leaves
    # un-incremented, so the pair is what carries the evidence.
    for column in (SALES_ACTIVETY_COLUMN, SALES_AVERAGE_COLUMN):
        declared = frozen_schema[SALES_LEDGER_TABLE][column]
        assert declared.kind == KIND_INTEGER, (
            f"the frozen schema declares `{SALES_LEDGER_TABLE}`.`{column}` as "
            f"{declared.sql_type!r} of kind {declared.kind!r}, expected "
            f"{KIND_INTEGER!r} [mysql/ACASDB.sql:L{declared.line}]. It is "
            f"`binary-long` "
            f""
            f"in the copybook [copybooks/wssl.cob:L46-L52], and A-8's SECOND "
            f"truncation "
            f"- "
            f"the remainder discarded by the divide at [sales/sl060.cbl:L827] - "
            f"happens "
            f""
            f"only because the receiving field is an integer. A decimal declaration "
            f"here "
            f"would mean the anomaly could not be reproduced at all."
        )

        cobol_values = _column_values(cobol_dump, column)
        python_values = _column_values(python_dump, column)

        assert set(cobol_values) == set(python_values), (
            f"`{SALES_LEDGER_TABLE}`'s primary keys disagree while comparing "
            f"{column!r}: "
            f"only on {SIDE_COBOL}: "
            f"{sorted(set(cobol_values) - set(python_values), key=repr)}; only on "
            f"{SIDE_PYTHON}: "
            f"{sorted(set(python_values) - set(cobol_values), key=repr)}."
        )

        for key, expected in cobol_values.items():
            produced = python_values[key]
            assert isinstance(expected, int) and not isinstance(expected, bool), (
                f"`{SALES_LEDGER_TABLE}`.`{column}` row {key!r} arrived from the "
                f"{SIDE_COBOL} side as {type(expected).__name__} ({expected!r}); a "
                f"`binary-long` column [copybooks/wssl.cob:L49] must reach the dump as "
                f"a "
                f"JSON INTEGER. A `Decimal` or a decimal string here would mean the "
                f"integer truncation A-8 depends on had been carried at two decimal "
                f"places instead, and pence that the COBOL discards would survive."
            )
            assert type(produced) is type(expected), (
                f"`{SALES_LEDGER_TABLE}`.`{column}` row {key!r} is "
                f"{type(expected).__name__} on the {SIDE_COBOL} side and "
                f"{type(produced).__name__} on the {SIDE_PYTHON} side. A TYPE MISMATCH "
                f"IS "
                f"A DIFFERENCE IN ITS OWN RIGHT - `1` is not `\"1\"` - because it "
                f"means "
                f""
                f"the two dumps were produced by inconsistent serialisation."
            )
            assert produced == expected, (
                f"A-8 / A-9 / A-10 REGRESSION: `{SALES_LEDGER_TABLE}`.`{column}` row "
                f"{key!r} is {expected!r} on the {SIDE_COBOL} side and {produced!r} on "
                f"the {SIDE_PYTHON} side.\n"
                f"  The two sides must AGREE; neither value is asserted to be the "
                f"arithmetically correct average, and this test does not compute one.\n"
                f"  SUSPECT, in order. A-8: has the accumulator been given decimal "
                f"places? [sales/sl060.cbl:L206] declares `work-2` as `pic s9(14) "
                f"comp-3` - ZERO places - against `work-goods` at two "
                f"[sales/sl060.cbl:L218], so [sales/sl060.cbl:L826] MUST discard "
                f"pence, "
                f""
                f"and [sales/sl060.cbl:L827] MUST discard the remainder because the "
                f"receiving field is `binary-long` [copybooks/wssl.cob:L49]. A-9: has "
                f"an "
                f"`add 1 to sales-activety` been introduced into `ba000-Credit-Comp` "
                f"[sales/sl060.cbl:L832-L843]? THERE IS NONE IN THE COBOL, and adding "
                f"one "
                f"would stop the first credit note being dropped - which is a FIX, and "
                f"therefore a failure (R-4). A-10: have the three guards been unified "
                f"into one helper? [sales/sl060.cbl:L819], [sales/sl060.cbl:L835] with "
                f"its extra [sales/sl060.cbl:L841], and [sales/sl100.cbl:L506] with "
                f"its "
                f""
                f"differently-spelled divide at L511 are THREE DIFFERENT "
                f"COMPUTATIONS and must stay three - different GUARDS and different "
                f"COUNTER handling, not different arithmetic: `divide X into Y giving Z` "
                f"and `divide Y by X giving Z` are the same quotient.\n"
                f"  The register entries are A-8, A-9 and A-10 in "
                f"docs/migration/anomaly-log.md, all three test-locked."
            )

    # A-10's THIRD VARIANT, COMPARED AS AN UNCHANGED WITNESS. `sl100` owns
    # ``compute-sales-pay` [sales/sl100.cbl:L497-L516] and is NOT dispatched on this
    # `route,
    # so these two columns should still hold their seeded values on both sides. If they
    # mmove here, something on this route reached the payment average - which would be a
    # mnew
    # behaviour rather than a reproduced one.
    for column in (SALES_PAY_ACTIVETY_COLUMN, SALES_PAY_AVERAGE_COLUMN):
        cobol_values = _column_values(cobol_dump, column)
        python_values = _column_values(python_dump, column)
        assert cobol_values == python_values, (
            f"`{SALES_LEDGER_TABLE}`.`{column}` differs between the two sides:\n"
            f"  {SIDE_COBOL}:  {cobol_values}\n"
            f"  {SIDE_PYTHON}: {python_values}\n"
            f"  This column belongs to A-10's THIRD variant, `compute-sales-pay` "
            f"[sales/sl100.cbl:L497-L516], which `sl100` owns and which is NOT on this "
            f"route - `{OPERATION}` dispatches `sl055` then `sl060` only. It is "
            f"compared "
            f"as an UNCHANGED WITNESS, so a difference here means one side reached the "
            f"payment average and the other did not."
        )

    # THE OTHER HALF OF THE TYPE SPLIT. The two money fields are signed at all three
    # layers and must arrive as canonical JSON DECIMAL STRINGS at the declared scale -
    # never as JSON numbers, never in exponent notation, and never as a `float` (R-2).
    for column in SIGNED_MONEY_COLUMNS:
        declared = frozen_schema[SALES_LEDGER_TABLE][column]
        assert declared.kind == KIND_DECIMAL, (
            f"the frozen schema declares `{SALES_LEDGER_TABLE}`.`{column}` as "
            f"{declared.sql_type!r} of kind {declared.kind!r}, expected "
            f"{KIND_DECIMAL!r} [mysql/ACASDB.sql:L{declared.line}]. It is "
            f"`pic s9(8)v99 comp-3` in the copybook [copybooks/wssl.cob:L54-L55] and "
            f"`PIC S9(08)V9(02) COMP` in the bridge [common/salesMT.cbl:L313-L314] - "
            f"SIGNED at all three layers, which is what makes A-11's narrowing "
            f"specific "
            f""
            f"rather than systemic."
        )
        cobol_values = _column_values(cobol_dump, column)
        python_values = _column_values(python_dump, column)
        for key, expected in cobol_values.items():
            assert isinstance(expected, str), (
                f"`{SALES_LEDGER_TABLE}`.`{column}` row {key!r} arrived from the "
                f"{SIDE_COBOL} side as {type(expected).__name__} ({expected!r}); a "
                f"DECIMAL column must reach the dump as a canonical JSON STRING at its "
                f"declared scale of {declared.scale}, so that no accounting value ever "
                f"passes through a binary floating-point type (R-2)."
            )
        assert cobol_values == python_values, (
            f"`{SALES_LEDGER_TABLE}`.`{column}` differs between the two sides:\n"
            f"  {SIDE_COBOL}:  {cobol_values}\n"
            f"  {SIDE_PYTHON}: {python_values}\n"
            f"  Rendered at the DECLARED scale of {declared.scale} on both sides by "
            f"normalisation job 2, which RAISES rather than rounds when a value "
            f"implies "
            f""
            f"more places - so a difference here is a difference in the stored value "
            f"and "
            f"never a rendering artefact."
        )


@pytest.mark.database
@pytest.mark.oracle
def test_sign_narrowing_at_the_bridge_agrees(
    parity: Any,
    harness: Any,
    frozen_schema: Mapping[str, Mapping[str, Any]],
    withheld: object,
) -> None:
    """A-11: the sign is lost AT THE BRIDGE, and both sides lose it identically.

    THE THREE LAYERS, verified in this checkout:

        Copybook         `Sales-Average binary-long`               SIGNED
                         [copybooks/wssl.cob:L49]
        Bridge host var  `HV-SALES-AVERAGE PIC 9(10) COMP`         UNSIGNED
                         [common/salesMT.cbl:L308]
        Column           `SALES-AVERAGE int(8) unsigned NOT NULL`  UNSIGNED
                         [mysql/ACASDB.sql:L969]

    The same narrowing applies across the whole statistics and date block at
    [common/salesMT.cbl:L305-L312], seven fields declared `binary-long` at
    [copybooks/wssl.cob:L46-L52]. THE SIGN IS THEREFORE LOST BEFORE ANY STATEMENT
    EXECUTES - at the bridge, not at the database - so the Python data-access layer
    reproduces the bridge's conversion rather than writing the computed value and
    letting the server object. The two money fields stay signed at all three layers
    ([copybooks/wssl.cob:L54-L55], [common/salesMT.cbl:L313-L314], `decimal(10,2)`),
    which is what makes the drift SPECIFIC, NOT SYSTEMIC and why it is handled field by
    field from the generated dictionary rather than by a blanket rule.

    WHAT THIS TEST ASSERTS, AND WHAT IT DELIBERATELY DOES NOT. It asserts that the shape
    holds - the columns really are unsigned, and no value on either side is negative -
    and that the TWO SIDES AGREE ON THE VALUE, whatever it is. IT PREDICTS NO VALUE.
    Agent Action Plan section 0.6.8 lists this as one of the five questions the compiled
    program must arbitrate: the SHAPE was settled by reading, and WHAT A NEGATIVE INPUT
    BECOMES depended on the conversion the bridge's C interface object performs. That has
    since been MEASURED - a negative written through the COMPILED handler and the COMPILED
    bridge arrives as its ABSOLUTE VALUE, magnitude taken first and high-order digits
    truncated after - and `Q-3` in `docs/migration/ambiguity-resolutions.md` records the
    operands. A-11's status is accordingly `REPRODUCED`, and the dictionary now emits
    `A-11` ALONE on its ninety-one field entries across eleven tables, eleven of them in
    this table, having dropped the `Q-3` tag when the question closed.

    THIS TEST STILL PREDICTS NO VALUE, and that is deliberate rather than left over. The
    measurement settled the RULE; it did not enumerate what every seeded figure becomes
    once the route's sign flips and truncations have run. Asserting the two sides agree
    keeps this tier measuring the migration instead of re-deriving the bridge, which is
    the arithmetic tier's job and is where the vectors live.

    A NON-NEGATIVE VALUE IS THEREFORE EVIDENCE OF THE ANOMALY AND NOT OF ITS ABSENCE.
    The computed value can legitimately be negative - the credit-note path negates nine
    fields at [sales/sl055.cbl:L658-L666] and three further sign flips are on this route
    at [sales/sl060.cbl:L571], [sales/sl060.cbl:L758] and [sales/sl060.cbl:L861] - and
    what the column holds afterwards is whatever the narrowing made of it. That is the
    defect, REPRODUCED AND NOT FIXED (R-4).

    Args:
        parity: The completed ten-stage run.
        harness: The three harness modules.
        frozen_schema: The parsed frozen schema. READ, never written.
        withheld: The value-free stand-in for a dumped cell, so a failure message can
            name a column without reproducing an accounting figure.
    """
    cobol_dump = _dump_for(parity.paths, SIDE_COBOL, SALES_LEDGER_TABLE, harness)
    python_dump = _dump_for(parity.paths, SIDE_PYTHON, SALES_LEDGER_TABLE, harness)

    assert cobol_dump["row_count"] > 0, (
        f"`{SALES_LEDGER_TABLE}` is EMPTY on the {SIDE_COBOL} side, so no customer row "
        f"was "
        f"written and the narrowing was never exercised. See "
        f"`test_moving_average_fields_agree` for what the seed must carry."
    )

    for column in NARROWED_STATISTICS_COLUMNS:
        # THE SHAPE, READ OFF THE FROZEN SCHEMA rather than asserted from prose. The
        # schema is the third of A-11's three layers and the only one this process can
        # inspect directly.
        declared = frozen_schema[SALES_LEDGER_TABLE][column]
        assert declared.kind == KIND_INTEGER and declared.unsigned, (
            f"the frozen schema declares `{SALES_LEDGER_TABLE}`.`{column}` as "
            f"{declared.sql_type!r} (kind {declared.kind!r}, unsigned="
            f"{declared.unsigned}) at [mysql/ACASDB.sql:L{declared.line}]; A-11 "
            f"requires "
            f"an UNSIGNED INTEGER column over a SIGNED `binary-long` copybook field "
            f"[copybooks/wssl.cob:L46-L52] and an UNSIGNED host variable "
            f"[common/salesMT.cbl:L305-L312]. If this column is no longer unsigned "
            f"then "
            f""
            f"either the frozen schema was modified - which Agent Action Plan section "
            f"0.8.1 makes a defect in the migration - or the field is not one of the "
            f"narrowed set after all."
        )

        cobol_values = _column_values(cobol_dump, column)
        python_values = _column_values(python_dump, column)

        assert set(cobol_values) == set(python_values), (
            f"`{SALES_LEDGER_TABLE}`'s primary keys disagree while comparing "
            f"{column!r}."
        )

        for key, expected in cobol_values.items():
            produced = python_values[key]

            # THE SIGN IS GONE ON BOTH SIDES. Asserted as LOSS, which is the reproduced
            # behaviour - not as correctness.
            for side, value in ((SIDE_COBOL, expected), (SIDE_PYTHON, produced)):
                assert isinstance(value, int) and not isinstance(value, bool), (
                    f"`{SALES_LEDGER_TABLE}`.`{column}` row {key!r} arrived from the "
                    f"{side} side as {type(value).__name__} ({withheld(value)}); the column is "
                    f"{declared.sql_type!r} and must reach the dump as a JSON integer."
                )
                assert value >= 0, (
                    f"`{SALES_LEDGER_TABLE}`.`{column}` row {key!r} is {withheld(value)} on the "
                    f"{side} side - NEGATIVE, in a column the frozen schema declares "
                    f"{declared.sql_type!r} at [mysql/ACASDB.sql:L{declared.line}].\n"
                    f"  A-11 is that the sign is lost AT THE BRIDGE: the copybook "
                    f"field "
                    f""
                    f"is signed [copybooks/wssl.cob:L46-L52] and the host variable is "
                    f"`PIC 9(10) COMP` [common/salesMT.cbl:L305-L312], so a negative "
                    f"value cannot survive into the column. A negative here means the "
                    f"bridge's conversion was NOT reproduced - the computed value was "
                    f"written and the server was left to object - which is a FIX of "
                    f"the "
                    f""
                    f"anomaly and therefore a failure (R-4)."
                )

            assert type(produced) is type(expected) and produced == expected, (
                f"A-11 REGRESSION: `{SALES_LEDGER_TABLE}`.`{column}` row {key!r} is "
                f"{expected!r} ({type(expected).__name__}) on the {SIDE_COBOL} side "
                f"and "
                f""
                f"{produced!r} ({type(produced).__name__}) on the {SIDE_PYTHON} side.\n"
                f"  THE TWO SIDES MUST AGREE, and NO VALUE IS PREDICTED HERE. What a "
                f"narrowed negative BECOMES has been MEASURED through the compiled "
                f"bridge: it arrives as its ABSOLUTE VALUE, magnitude first and "
                f"high-order truncation after. That is question "
                f"`Q-3` in docs/migration/ambiguity-resolutions.md. What the "
                f"measurement did NOT do is enumerate what each seeded figure "
                f"becomes after this route's sign flips, which is why this tier "
                f"compares the two sides rather than predicting one. A-11 stays in "
                f"docs/migration/anomaly-log.md as `REPRODUCED` - the content is "
                f"known and holding it is still wrong (R-4). "
                f"The Purchase-side variant is carried as "
                f"`Q-PURCH-AVERAGE-SIGN`.\n"
                f"  So do not derive an expected value from the copybook and assert it "
                f"- "
                f"measure the oracle and reproduce what it did. The `{SIDE_COBOL}` "
                f"value "
                f"above IS that measurement."
            )


@pytest.mark.database
@pytest.mark.oracle
def test_dump_is_wellformed_on_both_sides(
    parity: Any,
    harness: Any,
    frozen_schema: Mapping[str, Mapping[str, Any]],
    definition: Mapping[str, Any],
    withheld: object,
) -> None:
    """Both normalised trees carry the shape the protocol guarantees, for all ten
    tables.

    THIS IS THE TEST THAT MAKES THE EMPTY DIFF MEAN SOMETHING. Agent Action Plan section
    0.6.6's guarantee - "a non-empty diff is always a real behavioral difference and
    never an artefact of the comparison" - has a converse the comparison cannot check
    for itself: AN EMPTY DIFF IS ONLY EVIDENCE IF BOTH TREES WERE REALLY THERE AND
    REALLY WELL FORMED. Every failure below is an exit-2 condition, "the comparison
    could not be performed", and is therefore a pytest ERROR rather than a pass.

    THE SHAPE, from `harness/dump_tables.py`'s `DUMP_KEYS`: exactly five keys in fixed
    insertion order - `table`, `primary_key`, `columns`, `row_count`, `rows` - AND NO
    OTHERS. No timestamp, no server version, no scenario name and no side; THE SIDE IS
    RECORDED IN THE PATH, which is what lets the two trees be compared at all.

    Delegated to `harness/diff_states.py`'s own `load_dump`, the single definition of
    the contract (R-4): the five keys in order, the table in the twenty-two-name
    allow-list, the primary key present among the columns, `row_count == len(rows)`, no
    ragged row, NO value a `float` (R-2), no value `null`, no primary-key value twice,
    and the file name agreeing with the table it declares. Nothing is reimplemented
    here.

    THREE PROPERTIES ARE ADDED, none of which duplicates a harness responsibility:

      1. `columns` IN SCHEMA ORDINAL ORDER, checked against `mysql/ACASDB.sql` itself
         and against the declared column count. Rows are POSITIONAL, so a column list
         in any other order has no meaningful alignment - and a width disagreement
         means the two sides of the comparison are aligning DIFFERENT COLUMNS.
      2. `rows` PRIMARY-KEY ASCENDING. `load_dump` does not check this, because the diff
         aligns by key VALUE and does not need it. The BYTE-IDENTICAL claim of
         `tests/determinism/` does need it, and it is what makes the dump's order total
         and stable with a single `ORDER BY` and no tie-break. Checked as
         `keys == sorted(keys)` over a HOMOGENEOUS key type, which for integers is
         numeric order and for strings is code-point order - exactly the total order the
         comparison itself uses, so no second definition of it is introduced.
      3. EVERY DECIMAL VALUE IS A CANONICAL JSON STRING and every integer a JSON
         integer, asserted per column against the frozen schema's declared kind. This
         is R-2 at
         the widest point in the protocol: no accounting value may pass through a binary
         floating-point type in computation, storage or transport.

    Args:
        parity: The completed ten-stage run.
        harness: The three harness modules.
        frozen_schema: The parsed frozen schema. READ, never written.
        definition: The parsed scenario, for its DECLARED EFFECT. The comparison is
            bounded by all 22 in-scope tables; `EXPECTED_AFFECTED_TABLE_COUNT` is a
            fact about what this scenario declares it changes.
        withheld: The value-free stand-in for a dumped cell, so a failure message can
            name a column without reproducing an accounting figure.
    """
    in_scope: Mapping[str, Any] = harness.dump_tables.IN_SCOPE

    #  THE DECLARED EFFECT's size, not the bound's. The comparison is bounded by all
    #  22 in-scope tables; `EXPECTED_AFFECTED_TABLE_COUNT` is a fact about what THIS
    #  scenario declares it changes.
    declared = _affected_tables(definition)
    assert len(declared) == EXPECTED_AFFECTED_TABLE_COUNT, (
        f"{SCENARIO}: declares {len(declared)} table(s) {list(declared)}, expected "
        f"{EXPECTED_AFFECTED_TABLE_COUNT}."
    )

    for table in parity.tables:
        specification = in_scope[table]
        expected_columns = harness.normalize.schema_columns(frozen_schema, table)

        for side in (SIDE_COBOL, SIDE_PYTHON):
            dump = _dump_for(parity.paths, side, table, harness)

            # 1. THE COLUMN LIST, AGAINST THE FROZEN SCHEMA.
            columns = tuple(str(name) for name in dump["columns"])
            assert columns == expected_columns, (
                f"{side} `{table}`: the dump's column list disagrees with the frozen "
                f"schema.\n"
                f"  dump:   {list(columns)}\n"
                f"  schema: {list(expected_columns)}\n"
                f"  Rows are POSITIONAL, so a column list in any other order has no "
                f"meaningful alignment and every reported difference would be about "
                f"the "
                f""
                f"wrong column. mysql/ACASDB.sql is FROZEN (Agent Action Plan section "
                f"0.8.1), so a disagreement means either the dump or the checkout is "
                f"wrong - never that the schema should change."
            )
            assert len(columns) == specification.column_count, (
                f"{side} `{table}`: the dump lists {len(columns)} column(s) but the "
                f"inventory declares {specification.column_count} "
                f"[mysql/ACASDB.sql:L{specification.schema_line}]. A width "
                f"disagreement "
                f""
                f"means the two sides of the comparison are aligning different columns."
            )
            assert str(dump["primary_key"]) == specification.primary_key, (
                f"{side} `{table}`: the dump orders by {dump['primary_key']!r} but the "
                f"inventory declares `{specification.primary_key}` as the primary key "
                f"[mysql/ACASDB.sql:L{specification.schema_line}]. Rows align on that "
                f"column's VALUE, so ordering by another column would leave the two "
                f"sides "
                f"with no common alignment."
            )
            assert int(dump["row_count"]) == len(dump["rows"]), (
                f"{side} `{table}`: `row_count` is {dump['row_count']} but the dump "
                f"carries {len(dump['rows'])} row(s), so the file cannot be trusted to "
                f"be "
                f"complete."
            )

            # 2. PRIMARY-KEY ASCENDING ORDER.
            keys = list(_rows_by_key(dump))
            key_types = {type(key).__name__ for key in keys}
            assert len(key_types) <= 1, (
                f"{side} `{table}`: its primary-key values are of mixed types "
                f"{sorted(key_types)}. Rows are aligned on that column's VALUE, and "
                f"`1` "
                f"is "
                f"not `\"1\"`, so a mixed key type means the two sides could not be "
                f"aligned at all - and no total order over the mixture would be the "
                f"one "
                f""
                f"the comparison uses."
            )
            assert keys == sorted(keys), (
                f"{side} `{table}`: its rows are not in ascending primary-key order.\n"
                f"  first ten as dumped: {keys[:10]}\n"
                f"  first ten sorted:    {sorted(keys)[:10]}\n"
                f"  A dump is `SELECT * FROM <table> ORDER BY "
                f"`{specification.primary_key}`` with NO tie-break, which is total and "
                f"stable only because the ordering column is a single-column PRIMARY "
                f"KEY "
                f"[mysql/ACASDB.sql:L{specification.schema_line}]. Out-of-order rows "
                f"would "
                f"break the byte-identical claim of tests/determinism/ for a reason "
                f"that "
                f"is not a defect in the posting cycle."
            )

            # 3. THE VALUE TYPES, PER COLUMN, AGAINST THE DECLARED KIND  (R-2).
            for position, column in enumerate(columns):
                declared = frozen_schema[table][column]
                for row_index, row in enumerate(dump["rows"]):
                    value = row[position]
                    assert not isinstance(value, float), (
                        f"{side} `{table}`.`{column}` row {row_index} is a `float` "
                        f"({withheld(value)}). NO ACCOUNTING VALUE MAY PASS THROUGH A BINARY "
                        f"FLOATING-POINT TYPE at any point - not in computation, not "
                        f"in "
                        f""
                        f"storage, not in transport (R-2). The frozen schema contains "
                        f"zero "
                        f"`FLOAT`, `DOUBLE` and `REAL` columns, so a float here came "
                        f"from "
                        f"the driver or from the dump writer."
                    )
                    assert value is not None, (
                        f"{side} `{table}`.`{column}` row {row_index} is null. Every "
                        f"column of the frozen schema is `NOT NULL`, because each "
                        f"bridge's "
                        f"load paragraph initialises its host-variable group so an "
                        f"unset "
                        f"field becomes zero or space rather than SQL NULL - so the "
                        f"Python "
                        f"layer must DEFAULT rather than omit, and a null means it did "
                        f"neither."
                    )
                    if declared.kind == KIND_DECIMAL:
                        assert isinstance(value, str), (
                            f"{side} `{table}`.`{column}` row {row_index} is "
                            f"{type(value).__name__} ({withheld(value)}); the schema declares "
                            f"it "
                            f"{declared.sql_type!r} "
                            f"[mysql/ACASDB.sql:L{declared.line}], and a DECIMAL value "
                            f"must reach the dump as a canonical JSON STRING at its "
                            f"declared scale of {declared.scale} - never a JSON number "
                            f"and never exponent notation. Normalisation job 2 renders "
                            f"at "
                            f"the DECLARED scale, which is not uniformly two places, "
                            f"and "
                            f"RAISES rather than rounds when a value implies more."
                        )
                    elif declared.kind == KIND_INTEGER:
                        assert isinstance(value, int) and not isinstance(value, bool), (
                            f"{side} `{table}`.`{column}` row {row_index} is "
                            f"{type(value).__name__} ({withheld(value)}); the schema declares "
                            f"it "
                            f"{declared.sql_type!r} "
                            f"[mysql/ACASDB.sql:L{declared.line}], so it must reach "
                            f"the "
                            f""
                            f"dump as a JSON integer. The `binary-long` statistics "
                            f"fields "
                            f"[copybooks/wssl.cob:L46-L52] depend on this: their "
                            f"truncation on divide is INTEGER truncation, which is "
                            f"what "
                            f""
                            f"makes A-8 reproducible."
                        )
                    else:
                        assert isinstance(value, str), (
                            f"{side} `{table}`.`{column}` row {row_index} is "
                            f"{type(value).__name__} ({withheld(value)}); the schema declares "
                            f"it "
                            f"{declared.sql_type!r} "
                            f"[mysql/ACASDB.sql:L{declared.line}], a fixed-character "
                            f"column, so it must reach the dump as a string. "
                            f"Normalisation job 1 strips TRAILING spaces only - a "
                            f"COBOL "
                            f""
                            f"alphanumeric `MOVE` is left-justified with right "
                            f"padding, "
                            f"so "
                            f"LEADING SPACES ARE CONTENT - which is what A-12's width "
                            f"drift makes necessary [copybooks/wsledger.cob:L27] to "
                            f"[common/nominalMT.cbl:L299] to [mysql/ACASDB.sql:L127]."
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

    WHICH KEYS THIS ROUTE WRITES. `sl_invoice_post` binds `slpl_menu_state`, which
    carries the totals record but NOT the defaults record, so `overrewrite` rewrites KEY
    1 (`SYSTEM-REC`) and KEY 4 (`SYSTOT-REC`) and never KEY 2 - matching
    [sales/sales.cbl:L631, L636], which is why `SYSDEFLT-REC` is on no SALES or PURCHASE
    scenario's declared-effect list, and on all five General ones. It is dumped and
    compared on every scenario either way: the 22-table bound does not vary.

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
