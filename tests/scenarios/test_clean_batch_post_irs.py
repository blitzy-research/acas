"""IRS CLEAN-BATCH STATE PARITY — THE ONLY SCENARIO THAT TRUNCATES A TABLE.

Scenario `clean_batch_irs`, subsystem `irs`, operation `irs_post`. It drives the
ten-stage parity protocol and asserts an EMPTY ordering-normalised table diff
between the compiled COBOL oracle and the migrated Python cycle, bounded by the four
tables the scenario declares.

It is the most dangerous of the scenario files, for three reasons that all
belong to the same route:

  1. Its end-of-job answer DELETES EVERY ROW of the Sales-and-Purchase-to-IRS
     transfer table. No other scenario destroys seeded state.
  2. It deliberately produces an UNBALANCED double entry (A-4) and a LOST UPDATE
     (A-5). The resulting nominal ledger is wrong, and reproducing that wrongness
     exactly is the entire point.
  3. It exercises the THIRD linkage shape, which takes neither the calling-data block
     nor the text run date.

-------------------------------------------------------------------------------
THE INVERTED PREMISE, AND WHY IT BITES HARDEST HERE
-------------------------------------------------------------------------------

Agent Action Plan section 0.8.2, verbatim:

    "There is no test suite: compiled COBOL execution is the behavioral
    specification, defects included. A defect reproduced is correct; a defect fixed
    is a failure."

COROLLARY, AND IT GOVERNS EVERY ASSERTION BELOW: a test that asserts CORRECT
ACCOUNTING rather than OBSERVED BEHAVIOUR is itself a defect. There is therefore no
assertion anywhere in this file of the form "debits equal credits", and none of the
form "the derived date components match the date text". Every assertion says exactly
one thing:

    THE COBOL SIDE AND THE PYTHON SIDE AGREE.

A future contributor who "fixes" the half-posted double entry, the lost update, the
always-failing facade verb or the partial date derivation will make one of these
tests fail. That is the mechanism by which rule R-4 is enforced rather than merely
documented.

-------------------------------------------------------------------------------
WHY THE EMPTY-DIFF ASSERTION IS TRUSTWORTHY
-------------------------------------------------------------------------------

Agent Action Plan section 0.6.6: "a non-empty diff is always a real behavioral
difference and never an artefact of the comparison." That is earned by the frozen
schema rather than assumed: every in-scope table has a SINGLE-COLUMN primary key, no
secondary index, no `TIMESTAMP` column, no `AUTO_INCREMENT` column and no
column-level `DEFAULT`, so `SELECT * FROM <table> ORDER BY <primary key>` is a total
and stable order with no tie-breaking, no timestamp masking and no surrogate-key
remapping. The five tables here:

    IRSDFLT-REC      4 columns, primary key DEF-REC-KEY
    IRSNL-REC       15 columns, primary key KEY-1
    IRSPOSTING-REC  13 columns, primary key KEY-4
    PSIRSPOST-REC   10 columns, primary key IRS-POST-KEY
    SYSTEM-REC     169 columns, primary key SYSTEM-REC-KEY

-------------------------------------------------------------------------------
THE MIGRATION BOUNDARY, WHICH IS NARROW AND MUST BE STATED
-------------------------------------------------------------------------------

`irs/irs030.cbl` is migrated ONLY IN PART. In scope is
`Ledger-Postings-Add section.` at [irs/irs030.cbl:L1569] through
[irs/irs030.cbl:L1733], which is the LITERAL END OF FILE — the file is exactly 1733
lines — plus `Net section.` at [irs/irs030.cbl:L1544] and `Gross section.` at
[irs/irs030.cbl:L1556], whose VAT computes the posting path consumes.

Everything else in the file is OUT of scope: `Init-Main` [irs/irs030.cbl:L557],
`Input-Headings` [irs/irs030.cbl:L1239], `Date-Validate` [irs/irs030.cbl:L1285],
`Initialise-Main` [irs/irs030.cbl:L1402], `Show-Default` [irs/irs030.cbl:L1504] and
`file-init` [irs/irs030.cbl:L1518]. Agent Action Plan section 0.8.7 says why this
matters: "an agent working from the file rather than from the stated boundary would
migrate several hundred lines that must not be migrated."

-------------------------------------------------------------------------------
THE THIRD LINKAGE SHAPE
-------------------------------------------------------------------------------

[irs/irs030.cbl:L552-L554], verbatim:

    552  procedure division using IRS-System-Params
    553                           WS-System-Record
    554                           File-Defs.

THREE parameters. No calling-data block, no term code, no text `to-day`. Searching
`irs030.cbl` for `ws-calling-data`, `wscall` or `to-day` returns zero hits. The same
three-parameter shape is used by `irs010`, `irs020` and `irs030` alike, so it is an
IRS-wide idiom rather than a peculiarity of this program.

IT STILL REQUIRES A PINNED RUN DATE, and "no run date" never meant "no clock":
parameter 2 is the ordinary ACAS system record, which carries
`05  Run-Date        binary-long.` at [copybooks/wssystem.cob:L67] — a real
`SYSTEM-REC` column, read back by both runners after the run and carried into
`IRSPOSTING-REC`'s date columns, which ARE dumped. The entry point's run-date option is
consequently required on this route as well; its spelling belongs to the entry point and
is discovered from it by the runner, never written here.

`IRS-System-Params` IS A DIFFERENT, MUCH SMALLER RECORD from
`copybooks/wssystem.cob`. [irs/irs.cbl:L392] carries
`copy "irswssystem.cob" replacing system-record by IRS-System-Params`, and
`copybooks/irswssystem.cob` declares `01 system-record.` at L13,
`03 run-date pic x(8).` at L14 — TEXT `dd/mm/yy`, NOT the binary `Run-Date` —
`03 suser` L15, `03 client` L16, `03 address-1` to `address-4` L17-L20,
`03 start-date` L21, `03 end-date` L22, `03  system-ops pic x.` L23 (with a stray
extra space of indentation, preserved rather than tidied), `03 pass-word` L24 and
`03 next-post pic 9(5).  *> 178` L25.

-------------------------------------------------------------------------------
THE DISPATCH HAS NO WRAPPER AND NO GATE
-------------------------------------------------------------------------------

[irs/irs.cbl:L666-L672], verbatim:

    666       if       Menu-Reply = "4"
    667             or Cob-Crt-Status = Cob-Scr-F4
    668                call   "irs030" using IRS-System-Params
    669                                      WS-System-Record   *> ACAS system rec.
    670                                      file-defs
    671                end-call
    672                go to main-loop.

There is no `load00`-style helper and no term-code test, because `irs030` has no
`WS-Term-Code` and returns 0. Contrast General's `if ws-term-code = 5`
[general/general.cbl:L810-L811], Sales' two `not = zero` gates and Purchase's
commented-out gate. THE ASYMMETRY IS THE SPECIFICATION AND IS NOT HARMONISED.

`irs/irs.cbl` is itself a MAIN program — `procedure division.` at [irs/irs.cbl:L470]
with no `USING`. Its [irs/irs.cbl:L632-L634] is unconditional and sits immediately
before `Main-Loop.` [irs/irs.cbl:L637]: `move run-date to u-bin.` /
`perform maps04.` / `move u-date to to-day.` So the text date is derived once at menu
entry and is then NEVER PASSED to `irs030`. `zz090-Proc-Run-Date.`
[irs/irs.cbl:L972-L978] runs only on the option-"1" branch [irs/irs.cbl:L650], not on
option "4", and [irs/irs.cbl:L636] records the maintainer's own note that the menu
uses the IRS parameter file dates.

-------------------------------------------------------------------------------
A-4 — THE HALF-POSTED DOUBLE ENTRY
-------------------------------------------------------------------------------

    1619  Input-Loop.
    1620       perform  acas008-Read-Next.
    1621       if       FS-Reply = 10
    1622                go to EOJ.
    1623       add      1 to Post-Record-Cnt.
    ---- DR side ----
    1627       move     WS-IRS-Post-DR to  nl-owning.
    1629       perform  acasirsub1-Read-Indexed.
    1630       if       we-error = 2
    1631                display IR032 ...
    1634                go to Input-Loop.            <- CLEAN skip, no write yet
    1635       add      WS-IRS-Post-Amount  to  nl-dr.
    1636       if       ws-irs-post-vat-side = "CR"
    1637                add  WS-IRS-Vat-Amount  to  nl-dr.
    1641       perform  acasirsub1-Rewrite.          <- THE DEBIT IS COMMITTED HERE
    ---- CR side ----
    1645       move     WS-IRS-Post-CR  to  nl-owning.
    1647       perform  acasirsub1-Read-Indexed.
    1648       if       we-error = 2
    1649                display IR033 ...
    1652                go to Input-Loop.            <- DESTRUCTIVE skip
    1653       add      WS-IRS-Post-Amount  to  nl-cr.
    1654       if       WS-irs-post-vat-side = "DR"
    1655                add  WS-IRS-Vat-Amount  to  nl-cr.
    1657       perform  acasirsub1-Rewrite.

The debit is rewritten at [irs/irs030.cbl:L1641] BEFORE the credit account is even
looked up at [irs/irs030.cbl:L1645-L1647]. A missing credit account therefore takes
the [irs/irs030.cbl:L1648-L1652] skip, leaving A POSTED DEBIT WITH NO BALANCING
CREDIT AND NO `IRSPOSTING-REC` ROW. Both effects are ABSENCES, and an absence is
only ever recorded by a dump — which is why the protocol always dumps.

Note the ASYMMETRY at [irs/irs030.cbl:L1636-L1637] against
[irs/irs030.cbl:L1654-L1655]: the debit side adds VAT when the side is "CR" and the
credit side when it is "DR". That is deliberate and is reproduced as written.

Two dispositions, and only the second is destructive: a missing DEBIT account
[irs/irs030.cbl:L1627-L1634], message IR032, is a CLEAN no-op because nothing has
been written yet; a missing CREDIT account [irs/irs030.cbl:L1645-L1652], message
IR033, is a PARTIAL WRITE. The two paths are textually near-identical and differ only
in what has already happened by the time they are reached, which is exactly why the
defect survived.

-------------------------------------------------------------------------------
A-5 — THE LOST UPDATE ON THE TWO VAT CONTROL ACCOUNTS
-------------------------------------------------------------------------------

Snapshots taken BEFORE the loop:

    1594       move     def-acs (31) to nl-owning.
    1596       perform  acasirsub1-Read-Indexed.
    1602       move     WS-IRSNL-Record to nl31-record.      <- SNAPSHOT 1
    1604       move     def-acs (32) to nl-owning.
    1606       perform  acasirsub1-Read-Indexed.
    1612       move     WS-IRSNL-Record to nl32-record.      <- SNAPSHOT 2

and rewritten FROM THOSE SNAPSHOTS at end of job:

    1702  EOJ.
    1704       move     nl31-record to WS-IRSNL-Record.
    1705       perform  acasirsub1-Rewrite.
    1707       move     nl32-record to WS-IRSNL-Record.
    1708       perform  acasirsub1-Rewrite.

So ANY in-loop rewrite of accounts 31 or 32 — the rewrites at
[irs/irs030.cbl:L1641] and [irs/irs030.cbl:L1657] — IS OVERWRITTEN by the stale
snapshot plus its accumulated VAT. A textbook lost update, and silent.

The four-way VAT ladder that feeds the snapshots: the gate
`if WS-IRS-Vat-AC-Def = zero / go to Input-Loop.` at
[irs/irs030.cbl:L1682-L1683]; 31 with "CR" adds to `nl31-cr`
[irs/irs030.cbl:L1687]; 31 with "DR" to `nl31-dr` [irs/irs030.cbl:L1691]; 32 with
"CR" to `nl32-cr` [irs/irs030.cbl:L1695]; 32 with "DR" to `nl32-dr`
[irs/irs030.cbl:L1699] — WITH NO FINAL `else`, so any other combination silently
does nothing — then `go to Input-Loop.` [irs/irs030.cbl:L1700].

`docs/migration/anomaly-log.md` names THIS FILE as A-5's lock, because an end-state
assertion is the only observable that can see a lost update: no arithmetic-tier test
can, since the defect is in ORDERING ACROSS A LOOP BOUNDARY and not in a
computation. The default account codes come from
`copybooks/irswsdflt.cob`: `01 Default-Record.` L8, `03 Def-Group occurs 33.` L9,
`05 Def-Acs pic 9(5).` L10, `05 Def-Codes pic xx.` L11, `05 Def-Vat pic x.` L12,
with L6-L7 recording the 256-to-264-byte growth that added default 33 for `irs030`.

-------------------------------------------------------------------------------
THE FILE-ABANDONING REJECTION — REJECTION CLASS 4
-------------------------------------------------------------------------------

    1673       perform  acasirsub4-Write.
    1674       if       we-error not = zero
    1675                display IR914 ...
    1676                display WE-Error ...
    1677                accept WS-Reply ...
    1678                go to EOJ.

A failure writing the posting record jumps straight to `EOJ`, which STILL performs
both snapshot rewrites [irs/irs030.cbl:L1704-L1708] and both closes
[irs/irs030.cbl:L1711-L1712]. THE PARTIAL STATE IS COMMITTED, NOT ROLLED BACK.

The posting record is built immediately before, at
[irs/irs030.cbl:L1661-L1669], then `move next-post to post-key.`
[irs/irs030.cbl:L1670] and `add 1 to next-post.` [irs/irs030.cbl:L1671]. `next-post`
lives at [copybooks/irswssystem.cob:L25], inside `IRS-System-Params` — a FLAT
PARAMETER FILE WITH NO BRIDGE AND NO SCHEMA TABLE — so its increment is
STRUCTURALLY INVISIBLE to the diff. That is bounding by the absence of a table, not
an ignore-list. [irs/irs030.cbl:L437] carries the `Next-Post by IRS-Next-Post`
replacing clause, and [irs/irs030.cbl:L1662] shows the posted date coming FROM THE
DATA (`move WS-IRS-Post-Date to post-date`) rather than from the linkage.

-------------------------------------------------------------------------------
A-6 — THE PERMANENTLY FAILING FACADE VERBS
-------------------------------------------------------------------------------

[common/acas008.cbl], verbatim:

    287  aa-Process-Flat-File Section.
    289  aa010-main.
    293       move     1      to WS-Log-System.   *> 1 = IRS, 2=GL, 3=SL, 4=PL
    294       move     15     to WS-Log-File-No.
    299       evaluate File-Function
    300                when  4   *> fn-read-indexed
    301                when  7   *> fn-re-write
    302                when  9   *> fn-start
    303                when  8   *> fn-delete
    304                         move 988 to WE-Error
    305                         move 99 to fs-reply
    306                         go   to aa999-main-exit
    307       end-evaluate.

Read-indexed, re-write, start and delete all return failure UNCONDITIONALLY AT
ENTRY, before any access-type or file-mode logic runs, because the underlying file is
sequential. The IRS facade nevertheless publishes the re-write verb
[copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L163], so a caller invoking it ALWAYS fails
with `WE-Error 988` [common/acas008.cbl:L304] and `FS-Reply 99`
[common/acas008.cbl:L305]. `acas_posting/dal/acas008_spl_posting.py` reproduces the
guard and returns the same pair rather than performing an update. Note also that the
handler declares its own logging identity as the IRS sub system
[common/acas008.cbl:L293-L294] even though its callers are Sales and Purchase.

-------------------------------------------------------------------------------
A-7 — THE GUARDED DATE-COMPONENT DERIVATION, DUMPED AS STORED
-------------------------------------------------------------------------------

[common/irspostingMT.cbl], verbatim:

    982       if       Post-Date (1:2) numeric
    983                move     Post-Date (1:2) to HV-POST4-DAY.
    984       if       Post-Date (4:2) numeric
    985                move     Post-Date (4:2) to HV-POST4-MONTH.
    986       if       Post-Date (7:2) numeric
    987                move     Post-Date (7:2) to HV-POST4-YEAR.

THREE INDEPENDENT GUARDS, NOT ONE COMPOUND TEST, and none has an `else`. A PARTIAL
derivation is therefore reachable — day and year set while month stays at zero, for
instance — beside a fully intact raw date text in the neighbouring column. The row is
internally inconsistent and nothing detects it. `POST4-DAY`, `POST4-MONTH` and
`POST4-YEAR` have NO COUNTERPART IN ANY COPYBOOK; they exist only because the bridge
derives them, which is the entry that proves the Agent Action Plan's central sourcing
decision. The maintainer's own note sits at [common/irspostingMT.cbl:L978-L980]. A
failed guard yields ZERO and never SQL `NULL`, because the host-variable group is
initialised at [common/irspostingMT.cbl:L966] before the load; the unconditional
raw-text store that survives a failed guard is [common/irspostingMT.cbl:L969]. THIS
FILE NEVER REPAIRS A PARTIAL DERIVATION and never asserts that a component agrees
with the text.

-------------------------------------------------------------------------------
THE CLEAR-POSTING-FILE ANSWER — MANDATORY, BECAUSE NO COBOL DEFAULT EXISTS
-------------------------------------------------------------------------------

    1715  EOJ-q1.
    1716       display  "Can I clear the Ledgers Posting file? [Y]" at 1401 ...
    1717       accept   WS-Reply at 1440 with foreground-color 6 UPPER.
    1718       if       WS-Reply not = "Y" and not = "N"
    1719                go to EOJ-q1.               <- AN EMPTY REPLY LOOPS FOREVER
    1720       if       WS-Reply = "Y"
    1723                perform acas008-Open-Output  *> performs an acas008-Delete-All
    1724                perform acas008-Close.
    1725       display  "Note counts and any messages" at 1401 ...
    1726       accept   WS-Reply at 1430.           <- pure acknowledgement, DROPPED
    1727       display  space at 1401 with erase eol.
    1729  main99-exit.
    1730       exit     section.
    1732  copy "Proc-ZZ100-ACAS-IRS-Calls.cob".

DESPITE THE `[Y]` HINT THERE IS NO DEFAULT. [irs/irs030.cbl:L1716] is display text;
[irs/irs030.cbl:L1718-L1719] re-asks for ever on anything that is neither "Y" nor
"N". The scenario therefore pins the answer explicitly and this file asserts that it
did. Answering "Y" performs `acas008-Open-Output`, which this handler converts into a
DELETE-ALL against `PSIRSPOST-REC` — [common/acas008.cbl:L313-L319] sets
`fn-delete-all` (its third leg, [common/acas008.cbl:L315], being
`and not FS-Cobol-Files-Used`), and [common/acas008.cbl:L566] with
[common/acas008.cbl:L571-L574] does it again unguarded.

⚠️ ONE HOP FURTHER, AND IT IS NOT A MASS DELETE. This passage previously called the
result "a mass delete of every row", which is what the handler ASKS FOR but not what
the bridge ISSUES. The bridge moves 99999 into both halves of the posting key
[common/slpostingMT.cbl:L850-L851] and deletes STRICTLY BELOW that sentinel
[common/slpostingMT.cbl:L860-L868, L885-L891] — its own log text is "Deleting back
from" [common/slpostingMT.cbl:L870-L871]:
    DELETE FROM `PSIRSPOST-REC` WHERE `IRS-POST-KEY` < "9999999999"
A row AT the sentinel would survive the bound built from it. MEASURED on this seed:
all six rows carry keys 0000101000 to 0000106000, so all six go and ZERO are retained
— the table does end empty HERE, but as a property of the SEED, not of the handler.
The bound is described in full in [harness/scenarios/clean_batch_irs.yaml] and
reproduced at [acas_posting/dal/acas008_spl_posting.py ba085_process_delete_all]. That is why the transfer
table is on the affected-table list and why the protocol's reset-and-re-seed stage is
load-bearing rather than hygienic.

CONTRAST, PRESERVED AND NEVER HARMONISED (A-NEW-8): the sibling handler
[common/acas007.cbl:L305-L312] carries the same block with
`set fn-delete-all to true` COMMENTED OUT at [common/acas007.cbl:L308], so a
General-Ledger batch `Open-Output` does NOT truncate. The asymmetry is what decides
whether an `Open-Output` empties a table, and it is directly diff-visible.

The trailing accept at [irs/irs030.cbl:L1726] is a bare pause with no database
effect and is dropped on the Python side, per Agent Action Plan section 0.3.4. The
[irs/irs030.cbl:L1717] answer is PROMOTED to an input, because its answer changes
table state.

-------------------------------------------------------------------------------
ALL THREE ABORT PATHS BYPASS `EOJ` ENTIRELY
-------------------------------------------------------------------------------

Because `main99-exit.` [irs/irs030.cbl:L1729] sits AFTER `EOJ-q1.`
[irs/irs030.cbl:L1715], a `go to main99-exit` skips the end-of-job paragraph
altogether:

    abort 1  open-input failure   [irs/irs030.cbl:L1578-L1581]   message IR031
    abort 2  account 31 lookup    [irs/irs030.cbl:L1597-L1601]   message IR03A
    abort 3  account 32 lookup    [irs/irs030.cbl:L1607-L1611]   message IR03B

In all three cases NEITHER snapshot is rewritten and NEITHER file is closed by
`EOJ`. The six message identifiers this route can display are IR031, IR03A, IR03B,
IR032 (debit lookup), IR033 (credit lookup) and IR914 (posting write). Aborts 2 and 3
are why `def-acs (31)` and `def-acs (32)` MUST name accounts that exist in
`IRSNL-REC`: if they do not, the whole run leaves through a guard and the scenario
measures nothing.

-------------------------------------------------------------------------------
THE VERB CENSUS, WHICH IS WHAT JUSTIFIES EXACTLY FOUR TABLES
-------------------------------------------------------------------------------

    acas008      Open-Input x1 [L1578], Read-Next x1 [L1620],
                 OPEN-OUTPUT x1 = DELETE-ALL [L1723], Close x2 [L1712, L1724]
                 => PSIRSPOST-REC is READ then EMPTIED
    acasirsub1   Read-Indexed x11, REWRITE x7, Open x2, Open-Input x1,
                 Read-Next x1, Close x5   => IRSNL-REC is MUTATED
                 (`acasirsub1-Close` is COMMENTED OUT at [irs/irs030.cbl:L1710],
                  "Closed at EOJ")
    acasirsub4   Open x2 (including [L1617]), WRITE x1 [L1673], Close x2 [L1711]
                 => IRSPOSTING-REC is MUTATED
    acasirsub3   ZERO facade verbs; reached only by `move 3 to file-function.`
                 [irs/irs030.cbl:L1585] and `perform acasirsub3.`
                 [irs/irs030.cbl:L1586]   => IRSDFLT-REC is READ ONLY
    acasirsub5   ZERO verbs of any kind   => IRSFINAL-REC IS NOT TOUCHED

`IRSFINAL-REC` IS DELIBERATELY ABSENT from the affected-table list, and the frozen
source says so outright at [irs/irs030.cbl:L296]:
`03  Final-Record          pic x.    *> Table/File not used in this program.` Its
absence is asserted POSITIVELY below, so that nobody "helpfully" adds it.

`IRSDFLT-REC` is on the list as a READ-ONLY WITNESS. Nothing in the section can write
it, so it must be identical on both sides — and, the re-seed being provably from the
same fixture, identical to the seed as well.

-------------------------------------------------------------------------------
THE TWO `ROUNDED` VAT COMPUTES, AND A-19
-------------------------------------------------------------------------------

Two of only FIVE `ROUNDED` sites in the entire migration, the other three being
[general/gl080.cbl:L328], [general/gl051.cbl:L791] and [general/gl051.cbl:L796]:

    1544  Net section.
    1550  *>     compute  vat-amount rounded = post-amount * vat / 100.
    1551       compute  vat-amount rounded = post-amount * WS-Vat-Current / 100.
    1556  Gross section.
    1561  *>    compute vat-amount rounded = post-amount - (post-amount /
    1561         ( (vat + 100) / 100)).
    1562       compute  vat-amount rounded =
    1563                post-amount - (post-amount /
    1563                ( (WS-Vat-Current + 100) / 100)).
    1564       subtract vat-amount from post-amount.        <- UN-ROUNDED

A-19 is that pair of SUPERSEDED COMMENTED-OUT VARIANTS at
[irs/irs030.cbl:L1550] and [irs/irs030.cbl:L1561], which reference a differently
named rate field; the destructive un-rounded subtract they feed is
[irs/irs030.cbl:L1564]. They are preserved, not deleted.

THE ARITHMETIC IS NOT THIS FILE'S BUSINESS. It is locked by
`tests/arithmetic/test_irs_vat_from_net.py` and
`tests/arithmetic/test_irs_vat_from_gross.py`. NO VAT FIGURE IS RECOMPUTED HERE: this
file asserts STATE PARITY only.

-------------------------------------------------------------------------------
THE IRS FACADE CONVENTION DIFFERS BEHAVIOURALLY, NOT ONLY IN NAMING
-------------------------------------------------------------------------------

[irs/irs030.cbl:L1732] copies `Proc-ZZ100-ACAS-IRS-Calls.cob`, which adds a
PER-HANDLER ERROR-CHECK PARAGRAPH that the General, Sales and Purchase convention
lacks entirely, and which on an unrecoverable open failure RETURNS FROM THE PROGRAM
OUTRIGHT — `goback.` at [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L355-L364]. Agent
Action Plan section 0.6.5: "The Python facade must therefore behave differently
depending on which alias set the caller used, which is a behavioral difference and
not merely a naming one."

-------------------------------------------------------------------------------
THE TEN-STAGE PROTOCOL, AND WHY STAGE 5 MATTERS MORE HERE THAN ANYWHERE
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

STAGE 5 IS LOAD-BEARING ON THIS ROUTE IN A WAY IT IS NOT ELSEWHERE. The COBOL run at
stage 2 EMPTIES `PSIRSPOST-REC`. Without the drop, schema re-apply and re-seed at
stage 5, the Python run at stage 6 would start from an emptied transfer file, walk
nothing, and post nothing — and the two sides would then "agree" about a scenario
neither of them actually ran.

Not one of those stages is reimplemented here. `tests/conftest.py` composes all ten
in order and hands them over as the `protocol` fixture, which is the whole reason
that file exists (Agent Action Plan section 0.4.3: "so that no test reimplements the
comparison protocol"). Every assertion below reads finished evidence.

ALWAYS DUMP, THEN DECIDE THE STATUS. Agent Action Plan section 0.6.5 says of a
run-aborting rejection that "the database effect is therefore THE ABSENCE of
everything the later phases would have written". Absence is evidence, and here it is
doubly so: A-4's missing `IRSPOSTING-REC` row and the truncation of `PSIRSPOST-REC`
are BOTH absences, and only a dump records them. `run_scenario_parity` therefore
takes both dumps whatever the two run stages returned.

-------------------------------------------------------------------------------
THE THREE-WAY EXIT CONTRACT
-------------------------------------------------------------------------------

    0  the trees are identical, and stdout is EMPTY - zero bytes, not a banner  PASS
    1  a real behavioural difference, with a deterministic report            FAILURE
    2  THE COMPARISON COULD NOT BE PERFORMED - a missing tree, a missing table
       file, a malformed dump, a shape mismatch, a value that is not exact, a
       duplicate primary key, a wrong key order, `row_count` disagreeing with the
       row list, a ragged row, a null                                         ERROR

A test that treated "could not compare" as "no differences" would be the single worst
bug available in this tree, so exit 2 is mapped to a harness fault and surfaces as an
ERROR. The comparison itself is EXACT: no tolerance, no epsilon, no closeness
helper, no case- or whitespace-insensitive comparison and no numeric coercion — `1`
against `"1"` IS a difference. Rows align by PRIMARY-KEY VALUE, never by position,
and the report's two labels are `cobol` and `python`.

Three exit categories are kept distinct and are never collapsed: SUCCESS; a
BEHAVIOURAL DIFFERENCE, after which the dump is still taken; and a HARNESS FAULT — a
usage exit from the argument parser, an option the entry point does not publish, an
unreachable database, a malformed scenario file or disagreeing seed fingerprints.
Because `irs030` has no `WS-Term-Code` and returns 0, the scenario's declared
expected status of 0 is STRUCTURAL here rather than merely expected.

-------------------------------------------------------------------------------
BOUNDING, NEVER IGNORING
-------------------------------------------------------------------------------

THERE IS NO IGNORE-LIST, NO TOLERANCE-LIST AND NO "KNOWN DIFFERENCE" ALLOWANCE
anywhere in this file. The COMPARISON covers all 22 in-scope tables on every scenario;
the scenario's affected-table list is its DECLARED EFFECT, asserted per side, and is not
the bound.

  * A census across all twelve in-scope PROGRAMS found ZERO `System-*` facade verbs,
    so no migrated program persists a system record. `SYSDEFLT-REC`, `SYSFINAL-REC`
    and `SYSTOT-REC` are on no DECLARED-EFFECT list for THIS route because nothing on
    either side of it writes them: `irs/irs.cbl` has no `overrewrite` equivalent on the
    option-"4" branch, and `acas_posting/cli/args.py`'s `irs_menu_state` carries neither
    the defaults record nor the totals record, so the migrated IRS route persists KEY 1
    ALONE. They are still DUMPED and still COMPARED, as all 22 are - a table nobody
    writes is a table whose rows must not move, which is a claim worth making.
  * `SYSTEM-REC` IS DECLARED, AND THAT IS THE DECISION. Key 1 IS written on this route -
    `args.overrewrite` rewrites it unconditionally, and this scenario's own advanced
    allocator value is what it carries - so the row belongs on the declared-effect list
    and it is on it. The one problem a dump does have is solved where it arises:
    `RDBMS-PASSWD char(12)` [copybooks/wssystem.cob:L139] and `PASS-WORD` are two of its
    169 columns and a dump is `SELECT *`, so `harness/dump_tables.py`'s
    `REDACTED_COLUMNS` withholds exactly those two cells, identically on both sides, and
    the other 167 - including everything the frozen date sections write back
    [copybooks/wssystem.cob:L127] - are compared by value. Both runners FINGERPRINT the
    row before and after every run as well, and `protocol.assert_system_record_parity`
    compares the two sides' post-run digests over all 169 columns, so even the two
    withheld cells are bounded - without putting a credential in the evidence.
  * `next-post` [copybooks/irswssystem.cob:L25] lives in a flat parameter file with
    no bridge and no table, so its increment at [irs/irs030.cbl:L1671] is
    structurally invisible. Bounding by the absence of a table is not an ignore.
  * The four autogen tables are never seeded and never listed; the runners assert
    they are still empty.

-------------------------------------------------------------------------------
NORMALISATION DOES EXACTLY THREE THINGS, AND THERE IS NO FOURTH
-------------------------------------------------------------------------------

Delegated entirely to `harness/normalize.py`. Nothing is reimplemented or extended
here:

  1. TRAILING spaces in fixed-character columns, `rstrip(" ")`, TRAILING ONLY,
     because a COBOL alphanumeric `MOVE` is left-justified with right padding so
     LEADING spaces are content. ASCII U+0020 only, by declared type, `char(1)`
     included. Motivated by A-12, the width drift from `pic x(24)`
     [copybooks/wsledger.cob:L27] to `PIC X(32)` [common/nominalMT.cbl:L299] to
     `char(32)` [mysql/ACASDB.sql:L127]. The frozen schema has 238 `char(` columns
     and zero `varchar(`.
  2. DECIMAL scale rendering AT THE DECLARED SCALE, which is NOT uniformly 2.
     `PSIRSPOST-REC` carries `SIGN LEADING` display fields
     [copybooks/wspost-irs.cob:L21, L25] and `IRSPOSTING-REC` the `sign is leading`
     form [copybooks/irswspost.cob:L14, L19]; collapsing either into a plain numeric
     would change on-the-wire values. The semantics layer owns them and this file
     does not touch them.
  3. The two- versus four-digit date text forms, under an EXPLICIT FIVE-COLUMN
     ALLOW-LIST — and TWO of the five live in this scenario:
     `IRSPOSTING-REC.POST4-DAT` and `PSIRSPOST-REC.IRS-POST-DAT`. The other three are
     `GLPOSTING-REC.POST-DAT`, `SYSTEM-REC.STATS-DATE-PERIOD` and
     `SALEDGER-REC.SALES-STATS-DATE`. `char(8)` does NOT imply date — batch
     references of the same width are deliberately excluded — and most in-scope
     "dates" are binary day-number integers that job 3 must not touch.

A-7 IS DUMPED AS STORED AND NEVER REPAIRED: `POST4-DAY`, `POST4-MONTH` and
`POST4-YEAR` are ordinary integer columns, and normalisation must not complete a
partial derivation.

-------------------------------------------------------------------------------
THE FIVE REJECTION CLASSES — THIS FILE EXERCISES THREE
-------------------------------------------------------------------------------

Agent Action Plan section 0.8.1: "a single generic rejection path would fail this
directive." They are distinguished and never collapsed.

  1. CLEAN REJECTION, NO DATABASE EFFECT. Not exercised in its General-Ledger form
     [general/gl072.cbl:L291-L292, L306-L307], but the IRS debit-side skip at
     [irs/irs030.cbl:L1630-L1634] IS this class: nothing has been written yet, so it
     is a true no-op.
  2. RUN-ABORTING REJECTION. The control-total mismatch is not on this route; the
     three IRS aborts are structurally similar in leaving the database untouched AND
     bypassing `EOJ` entirely.
  3. PARTIAL DATABASE EFFECT. EXERCISED — A-4's committed debit
     [irs/irs030.cbl:L1635, L1641] with the [irs/irs030.cbl:L1648-L1652] skip, and
     A-5's snapshots [irs/irs030.cbl:L1602, L1612] overwritten at
     [irs/irs030.cbl:L1704-L1708].
  4. FILE-ABANDONING REJECTION. ⭐ NOT EXERCISED ON THIS FIXTURE, and the claim is
     withdrawn rather than qualified. [irs/irs030.cbl:L1673-L1678] jumps to `EOJ` on
     `we-error not = zero` after `perform acasirsub4-Write`, and `EOJ` still performs
     both snapshot rewrites and both closes — so IF it fired, the partial state would be
     COMMITTED, which is what makes the class distinct. It cannot fire here: the write
     is a plain `INSERT` into `IRSPOSTING-REC` and the only failure this fixture could
     produce is a DUPLICATE KEY, but the allocator starts at `Next-Post` 100
     [copybooks/irswssystem.cob:L25] and `irspost.dat` seeds exactly ONE internal
     posting, key 1, so the five keys this run allocates — 100 through 104 — cannot
     collide with anything. `test_scenario_definition_preconditions` asserts that
     arithmetic from the definition, so the withdrawal is a MEASURED fact about the
     fixture rather than a concession. Making the class reachable would mean seeding an
     internal posting whose key falls inside the allocator's band, which changes what
     `IRSPOSTING-REC` is bounded to prove and is not this scenario's job.
  5. PERMANENTLY FAILING FACADE VERB. EXERCISED — [common/acas008.cbl:L299-L307].

Every assertion establishes THE SAME DISPOSITION AND THE SAME DATABASE EFFECT on
both sides.

-------------------------------------------------------------------------------
SEEDING AND SCHEMA CONSTRAINTS — DOCUMENTED HERE, IMPLEMENTED BY THE HARNESS
-------------------------------------------------------------------------------

NO DDL (R-3). `mysql/ACASDB.sql` is applied VERBATIM; it already carries all 33
`DROP TABLE IF EXISTS` beside its 33 `CREATE TABLE`, so re-applying the frozen file
IS the drop-and-recreate. It contains no `USE`, so the database name is supplied on
the client command line. AUTOCOMMIT IS OFF during seeding, asserted rather than set,
per the banner every one of the 28 frozen loaders carries at
[common/glbatchLD.cbl:L9-L12].

`common/masterLD.sh` IS NEVER INVOKED. Its own header says
"THIS SCRIPT HAS NOT YET BEEN TESTED" [common/masterLD.sh:L4], all 24 loader lines
[common/masterLD.sh:L93-L116] omit the `;` before `fi` so a syntax check rejects it
at line 124 of a 123-line file, and it ends by paging a log through an interactive
pager that would block a run forever. It is FROZEN AND NOT FIXED; `harness/seed.sh`
reproduces its documented per-file contract [common/masterLD.sh:L44-L115] instead.

Six seed files, and the loader each is mapped to by the frozen contract:
`system.dat` to the four-loader block [common/masterLD.sh:L51-L87]; `irsacnts.dat`
to `irsnominalLD` [common/masterLD.sh:L99]; `irsdflt.dat` to `irsdfltLD`
[common/masterLD.sh:L100]; `irsfinal.dat` to `irsfinalLD`
[common/masterLD.sh:L101]; `irspost.dat` to `irspostingLD`
[common/masterLD.sh:L102]; and `postings2irs.dat` to `slpostingLD`
[common/masterLD.sh:L110], which is what loads `PSIRSPOST-REC`.

R-4 items preserved rather than fixed: the `dfltLD` strict-versus-lenient exit
asymmetry ([common/masterLD.sh:L83] tests `!= 0` where the others tolerate up to 63,
of which 128 means the parameters were unset, 64 that the relational database was
unset and 16 a write error); the charset caveat at [mysql/ACASDB.sql:L9-L11] and
[mysql/ACASDB.sql:L16], `SET NAMES utf8mb4` against 33 tables declared utf8mb3; and
the display-width quirk of `int(1) unsigned` beside `tinyint(1) unsigned`.

EXECUTION IS STRICTLY SEQUENTIAL (R-3). There is no test-distribution plugin, no
parallelism and no randomised ordering: parallel scenario runs against one shared
database would break the seed, run, dump, reset, run, dump, diff protocol outright —
and doubly so here, because this scenario DESTROYS seeded state, so a concurrent
scenario would observe an emptied transfer table.

WHAT THE SEED MUST CARRY FOR THE ANOMALIES TO BE OBSERVABLE. These are properties of
the flat files under the scenario's own seed directory, which this file does not read
and does not second-guess; they are recorded here because the assertions below are
only as sharp as the fixture makes them:

  1. At least one clean, fully balanced posting, so the happy path is exercised.
  2. Postings hitting BOTH VAT control accounts, plus at least one whose debit or
     credit account IS 31 or 32 — that is what makes A-5's lost update observable,
     because the in-loop rewrite of 31 or 32 is discarded at
     [irs/irs030.cbl:L1704-L1708].
  3. One posting whose CREDIT account is MISSING, which triggers A-4's half-posted
     double entry through the [irs/irs030.cbl:L1648-L1652] skip.
  4. One posting whose date text FAILS a bridge guard, so A-7's partial derivation is
     exercised and at least one of `POST4-DAY`, `POST4-MONTH` or `POST4-YEAR` stays
     zero beside intact date text.

CREDENTIALS. [copybooks/wssystem.cob:L137-L144] ships the defaults and the IRS
handlers copy them into `RDB-Data` at [common/acasirsub1.cbl:L726],
[common/acasirsub3.cbl:L409] and [common/acas008.cbl:L558-L563]; the target block is
[copybooks/wsfnctn.cob:L56-L62], whose user and password are `pic x(12)` and so are
limited to twelve characters. The `ACAS_DB_*` environment must EQUAL the `RDBMS-*`
fields in the seeded `system.dat`; that is verified by the harness and not here.

-------------------------------------------------------------------------------
TRACEABILITY (R-5) AND ARBITRATION (R-6)
-------------------------------------------------------------------------------

R-5. The anomalies this file names are A-4, A-5, A-6, A-7, A-12 and A-19, plus
A-NEW-8 for the `Open-Output` asymmetry, and every claim above and below carries its
`[path:Lnnn]` locator. The register is `docs/migration/anomaly-log.md`. Coverage
measurement is EVIDENCE, NOT A GATE: there is no minimum-coverage threshold anywhere
in this project's configuration, and a coverage number never decides whether this
migration is correct.

R-6. The empty diff is the arbiter. Three arbitrations bear on this file, referenced
BY IDENTIFIER and never by importing or probing for a document:

    Q-2  the default arithmetic precision that governs the two `ROUNDED` VAT
         computes. Agent Action Plan section 0.6.8 calls the compound VAT expression
         "the one place a precision difference could change a stored penny".
    Q-3  a negative binary value passing through an unsigned host variable into an
         unsigned column, where the sign is lost AT THE BRIDGE and the resulting
         stored value has to be measured rather than assumed.
    ---  the deliberate omission of the General-Ledger end-of-cycle operation from
         every scenario file, recorded as oracle-reversible.

Each is recorded in `docs/migration/ambiguity-resolutions.md`; the per-scenario
evidence goes to `docs/migration/scenario-diff-evidence.md`. THOSE ARE TEXTUAL
REFERENCES ONLY — nothing here imports them, checks that they exist or skips if they
are absent.

-------------------------------------------------------------------------------
HOW THIS FILE IS BUILT, AND WHY
-------------------------------------------------------------------------------

R-1 IS ENFORCED STRUCTURALLY, NOT BY DISCIPLINE. The compiled oracle is reached only
out of process, by the harness shell runners that `tests/conftest.py` drives. The
three harness Python modules are NOT a package — there is no `harness/__init__.py`
and `pyproject.toml` excludes `harness*` from packaging — so they arrive only through
the `harness` fixture, which loads them by explicit file path. This file never
imports them, never spawns a child process of its own, never invokes an entry point
as a module, never constructs a command line or an argument list, and never writes
the spelling of any command-line option. The scenario's own answer mapping is the
ONLY place an interactive answer is named, and `harness/run_python_scenario.sh`
translates answers into options, owning the probe that requires the option to be
published and failing as a harness fault when it is not.

R-2 IS ENFORCED BY CONSTRUCTION. No value here is a binary floating-point number, and
there is no tolerance, no epsilon, no closeness helper and no approximate-equality
helper. Dumped DECIMAL values arrive as canonical JSON STRINGS at the declared scale
and integers as JSON integers; where this file needs to add money it does so in
`decimal.Decimal`, imported inside the function that uses it.

EVERYTHING SHARED COMES FROM `tests/conftest.py`, AND ONLY THROUGH FIXTURES. That is
the house convention across the other two tiers, and it is what keeps the module
level of this file down to the four statements below: a docstring, the postponed
annotations import, the marker and the scenario name. One consequence is deliberate
and is stated so it does not read as carelessness: injected fixtures are annotated
`object`, because naming their real types would require module-level imports this
file is not permitted to make, and each parameter's true type is given in its
docstring instead.

There is no `__init__.py` in this directory, no nested `conftest.py` and no helper
module; the few private helpers below live in this file. Collection SUCCEEDS WITH NO
STACK: every test that needs the Compose stack reaches it through a fixture that
skips with a precise, multi-line reason naming every missing precondition.
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

SCENARIO = "clean_batch_irs"

# THE THREE TABLES THIS SCENARIO'S SEED FILLS AND THE RUN LEAVES POPULATED, each named
# by the `seed_files:` entry that fills it: irsdflt.dat -> IRSDFLT-REC, irsacnts.dat ->
# IRSNL-REC, irspost.dat -> IRSPOSTING-REC. They must come back WITH ROWS on both sides
# or every assertion in this file holds just as well against four empty tables.
#
# `PSIRSPOST-REC` IS DELIBERATELY NOT HERE even though postings2irs.dat seeds it. The
# end-of-job answer is pinned "Y", so the route DELETES EVERY ROW of it
# [irs/irs030.cbl:L1720-L1723] via [common/acas008.cbl:L313-L319, L571-L574]. Whether
# that truncation actually happened is a BEHAVIOURAL claim owned by
# `test_psirspost_rec_is_emptied_by_the_clear_answer`, where a Python side that failed
# to empty it is a FAILURE; asserting it here would report that regression as an ERROR.
SEEDED_TABLES = (
    "IRSDFLT-REC",
    "IRSNL-REC",
    "IRSPOSTING-REC",
)


# ---------------------------------------------------------------------------
#  PRIVATE READERS
#
#  Each one READS finished evidence and interprets nothing. None of them
#  normalises, coalesces, defaults, re-orders or trims anything: harness/normalize.py
#  owns the only three transformations that exist, and a helper here that tidied a
#  result would be a defect rather than a kindness (R-4).
# ---------------------------------------------------------------------------


def _declared_tables(definition: object) -> tuple:
    """The scenario's affected-table list, in the order it declares them.

    The list is READ, never restated: a second copy of a table list would drift
    (R-4), and it is the affected-table list that BOUNDS every comparison. Both
    spellings of the key are accepted, which is the same rule
    `harness/dump_tables.py` and `harness/diff_states.py` apply; `tests/conftest.py`
    has already established that exactly one of them is present by the time a
    definition reaches this function.

    Args:
        definition: One scenario's parsed mapping, from the `scenario_loader`
            fixture.

    Returns:
        The table names as declared.

    Raises:
        AssertionError: Neither spelling is present. A HARNESS FAULT: an unbounded
            comparison is not a comparison.
    """
    for key in ("affected_tables", "affected-tables"):
        declared = definition.get(key)
        if declared is not None:
            return tuple(str(name) for name in declared)
    raise AssertionError(
        f"HARNESS FAULT: {SCENARIO} declares neither 'affected_tables' nor "
        f"'affected-tables'. That list is the scenario's DECLARED EFFECT, which the "
        f"runners assert against; the comparison itself is bounded by all 22 "
        f"in-scope tables. Both are required, and neither is an ignore-list - there "
        f"is no ignore-list, no tolerance-list and no known-difference allowance "
        f"anywhere in the diff path."
    )


def _clear_postings_answer(definition: object) -> str:
    """The pinned end-of-job answer that decides whether the transfer file is cleared.

    THE ONE PROMOTED INTERACTIVE ANSWER ON THIS ROUTE, and the destructive one. It is
    a required top-level scalar because the frozen program has NO DEFAULT: the
    bracketed hint at [irs/irs030.cbl:L1716] is display text, and
    [irs/irs030.cbl:L1718-L1719] re-asks for ever on anything that is neither "Y" nor
    "N". Both runners refuse this operation without it.

    THE KEY IS SEMANTIC AND IS NEVER A COPY OF A COMMAND-LINE OPTION SPELLING. The
    spellings belong to the entry points and are discovered from them at run time;
    naming one here would break the moment an entry point chose a different one.

    Args:
        definition: One scenario's parsed mapping.

    Returns:
        The answer exactly as declared, upper-cased for the comparison the frozen
        accept performs at [irs/irs030.cbl:L1717] `with ... UPPER`.

    Raises:
        AssertionError: The key is absent. A HARNESS FAULT, because the oracle would
            sit at the prompt for ever.
    """
    for key in ("irs_clear_postings", "irs-clear-postings"):
        answer = definition.get(key)
        if answer is not None:
            return str(answer).strip().upper()
    answers = definition.get("answers")
    if isinstance(answers, dict):
        for key in ("irs_clear_postings", "clear_posting_file"):
            answer = answers.get(key)
            if answer is not None:
                return str(answer).strip().upper()
    raise AssertionError(
        f"HARNESS FAULT: {SCENARIO} does not pin the end-of-job "
        f"clear-the-posting-file answer. The frozen program has no default - "
        f"[irs/irs030.cbl:L1718-L1719] loops for ever on an empty reply - so an "
        f"unpinned answer hangs the compiled oracle at the prompt rather than "
        f"producing a comparison."
    )


def _normalised(harness: object, paths: object, side: str, table: str) -> dict:
    """One table's NORMALISED dump for one side, read and asserted well formed.

    `load_dump` is the harness's own public read-and-assert entry point, so the
    structural contract has exactly ONE definition in this repository (R-4): the five
    keys in fixed order, the table in the twenty-two-name allow-list, the primary key
    present among the columns, `row_count` equal to the length of the row list, every
    row of the declared width, no value a binary floating-point number (R-2), no
    value null, and no primary-key value twice. Every one of those failures is the
    comparison's exit 2 - a HARNESS FAULT, never a pass.

    THE NORMALISED TREE IS READ, NEVER THE RAW ONE. A raw dump still carries the
    representation artefacts - character padding, driver decimal rendering, the
    two-digit date text forms - so a verdict taken from it would not be evidence.

    Args:
        harness: The three harness modules, from the `harness` fixture.
        paths: The scenario's `ScenarioPaths`, from `protocol.paths`.
        side: `cobol` or `python`. The side is recorded in the PATH, never in a file.
        table: The in-scope table name, hyphens included.

    Returns:
        The parsed dump object: `table`, `primary_key`, `columns`, `row_count`,
        `rows`.
    """
    diff_states = harness.diff_states
    tree = paths.normalized_dir(side)
    return diff_states.load_dump(tree / diff_states.dump_filename(table))


def _rows_by_key(dump: dict) -> dict:
    """One dump's rows, indexed by primary-key VALUE.

    ROWS ALIGN BY PRIMARY-KEY VALUE AND NEVER BY POSITION, which is the same rule
    `harness/diff_states.py` applies, and the reason a type mismatch in the key
    column cannot be papered over: `1` is not `"1"`.

    Args:
        dump: A well-formed dump object.

    Returns:
        A mapping of primary-key value to the row, as a tuple so it cannot be edited
        after the fact.
    """
    index = dump["columns"].index(dump["primary_key"])
    return {row[index]: tuple(row) for row in dump["rows"]}


def _cell(dump: dict, row: tuple, column: str) -> object:
    """One value of one row, selected by COLUMN NAME.

    Args:
        dump: The dump the row came from, for its column list.
        row: The row.
        column: The column name, spelled as the frozen schema spells it.

    Returns:
        The value: an `int` for an integer column, a canonical decimal STRING for a
        DECIMAL column, the driver's string for a `char` column.

    Raises:
        AssertionError: The dump does not carry the column. A HARNESS FAULT - the
            frozen schema is the authority on what a table has.
    """
    columns = list(dump["columns"])
    if column not in columns:
        raise AssertionError(
            f"HARNESS FAULT: `{dump['table']}` carries no column `{column}`. The "
            f"frozen schema mysql/ACASDB.sql is the authority on the column set, "
            f"and it declares {columns}."
        )
    return row[columns.index(column)]


def _table_diff(parity: object, table: str) -> object:
    """The comparison's finding for ONE bounded table.

    Args:
        parity: The completed `ParityRun`.
        table: The table name, which must be one the scenario bounded the comparison
            by.

    Returns:
        The `TableDiff`. Its `is_empty` is that table's pass condition, and its
        `missing_in_python`, `missing_in_cobol` and `value_differences` localise a
        finding to a primary key and a column.

    Raises:
        AssertionError: The table was not compared. A HARNESS FAULT: a table that was
            never compared cannot support a conclusion either way.
    """
    for candidate in parity.tree.tables:
        if candidate.table == table:
            return candidate
    raise AssertionError(
        f"HARNESS FAULT: `{table}` was not compared, so nothing can be concluded "
        f"about it. The comparison covered "
        f"{[entry.table for entry in parity.tree.tables]}, bounded by "
        f"{list(parity.tables)}."
    )


# THE FAILURE-MESSAGE ROUTE IS `parity.diagnose()`, defined once in tests/conftest.py.
# This module used to wrap `harness.diff_states.render` in a local `_render` helper,
# which printed every differing value and every primary key into pytest output
# (finding SEC-05). The wrapper is gone rather than repointed, so there is no
# module-local name left that looks like the old route. The values are not lost: they
# are in the report `diagnose()` names, with its digest.


# ---------------------------------------------------------------------------
#  THE SHARED EVIDENCE
#
#  Ten stages, in order, ONCE. Every guard layer lives in the fixture, so a
#  HARNESS FAULT is reported as a pytest ERROR and what is left in each test body is
#  the VERDICT, so a genuine behavioural difference is reported as a pytest FAILURE.
#  The two can never be confused, which is the whole point of the split.
# ---------------------------------------------------------------------------


@pytest.fixture
def parity(
    request: pytest.FixtureRequest,
    protocol: object,
    scenario_loader: object,
    pinned_clock: object,
    harness: object,
) -> object:
    """The completed ten-stage parity run for this scenario, guarded.

    RUN ONCE PER SESSION, AND SHARED. Eleven assertions in this file interrogate one
    comparison from different angles, and re-driving the compiled oracle for each of
    them would multiply a seed, a menu-driven oracle run, a schema drop-and-re-apply
    and a re-seed by eleven for no additional evidence. The completed run is therefore
    memoised on the pytest session, keyed by scenario name. Two facts make that safe
    rather than clever: execution is STRICTLY SEQUENTIAL (R-3), so nothing can mutate
    the evidence concurrently; and the evidence is FILES under the scenario's own
    output directory, which only another run of this same scenario could overwrite,
    and there is exactly one scenario file per scenario. Re-running the protocol per
    test would be equally correct - the memo is an economy and nothing more.

    THE GUARDS BELOW ARE HARNESS-FAULT DETECTORS AND NOT BEHAVIOURAL ASSERTIONS. Each
    one catches a condition under which an EMPTY DIFF WOULD BE MEANINGLESS, so that a
    false pass is impossible rather than merely unlikely.

    Args:
        request: For the session the memo lives on.
        protocol: Every protocol stage, from `tests/conftest.py`. It applies the stack
            skip guard itself, so a host with no Compose stack SKIPS with a precise,
            multi-line reason naming every missing precondition, and never errors.
        scenario_loader: The scenario definition, parsed with the safe YAML loader.
        pinned_clock: The project-wide `PinnedRunDate`, already asserted by
            `tests/conftest.py` to be the text 21/09/2025 and the binary 155127.
        harness: The three harness Python modules, loaded by explicit file path. There
            is no `harness/__init__.py` and `pyproject.toml` excludes `harness*` from
            packaging, which is the structural enforcement of R-1.

    Returns:
        The `ParityRun`: every stage result in execution order, both run stages, the
        stage-10 outcome and the artifact paths. `is_empty` is the pass condition.

    Raises:
        Skipped: The Compose stack is unusable. A SKIP and never an error.
        AssertionError: A guard failed - a HARNESS FAULT.
        Exception: A stage whose failure destroys the evidence failed, or the
            comparison could not be performed at all (its exit 2). Also a harness
            fault, and never a pass.
    """
    memo_name = "_acas_scenario_parity_runs"
    session = request.session
    memo = getattr(session, memo_name, None)
    if memo is None:
        memo = {}
        setattr(session, memo_name, memo)

    definition = scenario_loader(SCENARIO)
    tables = _declared_tables(definition)
    system = definition.get("system") or {}

    # ------------------------------------------------------------------
    #  GUARD 1 - THE FALSE-PASS TRAP. `File-System-Used pic 9` is declared at
    #  [copybooks/wssystem.cob:L112] with `88 FS-Cobol-Files-Used value zero` L113 and
    #  `88 FS-MySql-Used value 1` L114, and [common/acas008.cbl:L323-L325] routes to
    #  the relational path only when the flag is NOT zero. Seeded zero sends the whole
    #  run to indexed files, both dumps come back empty and the comparison exits clean
    #  having compared nothing. On THIS route the flag is doubly load-bearing, because
    #  the destructive end-of-job answer reaches the database through the same gate -
    #  the third leg of [common/acas008.cbl:L313-L319] is `not FS-Cobol-Files-Used` at
    #  [common/acas008.cbl:L315] - so a seeded zero would also silently cancel the
    #  most distinctive effect of the scenario.
    # ------------------------------------------------------------------
    assert int(system.get("file_system_used", -1)) == 1, (
        f"HARNESS FAULT: {SCENARIO} must seed `File-System-Used` = 1 "
        f"(`88 FS-MySql-Used` [copybooks/wssystem.cob:L114]); it declares "
        f"{system.get('file_system_used')!r}. With zero, "
        f"[common/acas008.cbl:L323-L325] never reaches the relational path, BOTH "
        f"DUMPS COME BACK EMPTY and the comparison would exit clean having compared "
        f"nothing - a silent FALSE PASS. It would also cancel the transfer-table "
        f"truncation, whose guard's third leg is `not FS-Cobol-Files-Used` "
        f"[common/acas008.cbl:L315]."
    )

    # ------------------------------------------------------------------
    #  GUARD 2 - THE DESTRUCTIVE ANSWER IS PINNED, and the table it destroys is on
    #  the list. Answering "Y" [irs/irs030.cbl:L1720] performs `acas008-Open-Output`
    #  [irs/irs030.cbl:L1723], which this handler converts into a DELETE-ALL against
    #  the transfer table [common/acas008.cbl:L313-L319, L571-L574]. The bridge bounds
    #  it to keys strictly below "9999999999" [common/slpostingMT.cbl:L850-L851,
    #  L885-L891]; see the module docstring above for the measured effect on this seed.
    # ------------------------------------------------------------------
    answer = _clear_postings_answer(definition)
    assert answer in {"Y", "N"}, (
        f"HARNESS FAULT: the end-of-job answer is {answer!r}; the frozen accept at "
        f"[irs/irs030.cbl:L1717-L1719] admits only Y or N and RE-ASKS FOR EVER on "
        f"anything else, so any other value hangs the compiled oracle."
    )
    if answer == "Y":
        assert "PSIRSPOST-REC" in tables, (
            f"HARNESS FAULT: {SCENARIO} answers Y to "
            f"[irs/irs030.cbl:L1716], which DELETES EVERY ROW of PSIRSPOST-REC "
            f"[common/acas008.cbl:L313-L319], yet PSIRSPOST-REC is not among "
            f"{list(tables)}. The most distinctive effect of this scenario would go "
            f"unobserved."
        )

    # ------------------------------------------------------------------
    #  GUARD 3 - THE PIN. The scenario's own clock block must agree with the
    #  project-wide pin, because the run receives the date through linkage and a
    #  one-day shift in `Run-Date` [copybooks/wssystem.cob:L67] would look like a
    #  posting difference three tables into a diff.
    # ------------------------------------------------------------------
    clock = definition.get("clock") or {}
    assert str(clock.get("to_day")) == pinned_clock.to_day, (
        f"HARNESS FAULT: {SCENARIO} declares the text run date "
        f"{clock.get('to_day')!r} while the project pin is "
        f"{pinned_clock.to_day!r}. Two different pinned dates in one run would make "
        f"the comparison meaningless."
    )
    assert int(clock.get("run_date", -1)) == pinned_clock.run_date, (
        f"HARNESS FAULT: {SCENARIO} declares the binary run date "
        f"{clock.get('run_date')!r} while the project pin is "
        f"{pinned_clock.run_date}. `Run-Date` [copybooks/wssystem.cob:L67] is a real "
        f"SYSTEM-REC column and is therefore visible in a dump."
    )

    run = memo.get(SCENARIO)
    if run is None:
        # ------------------------------------------------------------------
        #  ALL TEN STAGES, IN ORDER, ONCE. Nothing about the protocol is
        #  reimplemented here. STAGE 5 IS LOAD-BEARING ON THIS ROUTE: the oracle run
        #  at stage 2 EMPTIES PSIRSPOST-REC, so without the drop, schema re-apply and
        #  re-seed the Python run at stage 6 would start from an emptied transfer
        #  file, walk nothing and post nothing.
        # ------------------------------------------------------------------
        run = protocol.run_scenario_parity(SCENARIO)
        memo[SCENARIO] = run

    # ------------------------------------------------------------------
    #  GUARD 4 - THE COMPARISON WAS ACTUALLY BOUNDED, and by ALL 22 IN-SCOPE TABLES,
    #  which is the protocol. A bound drawn from the scenario's declared effect cannot
    #  reveal a difference in anything the scenario did not expect to move - including
    #  the system rows `overrewrite` writes on BOTH sides
    #  [general/general.cbl:L656-L672]. The scenario's own declared list is checked
    #  separately, as a SUBSET, so nothing it claims to change goes uncompared.
    # ------------------------------------------------------------------
    assert tuple(run.tables) == tuple(protocol.in_scope_tables()), (
        f"HARNESS FAULT: the comparison was bounded by {list(run.tables)} while the "
        f"protocol bounds it by all 22 in-scope tables, "
        f"{list(protocol.in_scope_tables())}."
    )
    assert run.tables, (
        f"HARNESS FAULT: {SCENARIO} bounded the comparison by no tables at all. An "
        f"unbounded or empty comparison is not a comparison."
    )
    #  The scenario's declared effect must be a SUBSET of the bound, or something it
    #  claims to change was never compared.
    assert set(tables) <= set(run.tables), (
        f"HARNESS FAULT: {SCENARIO} declares an effect on "
        f"{sorted(set(tables) - set(run.tables))!r}, which the comparison never "
        f"covered."
    )

    # ------------------------------------------------------------------
    #  GUARD 5 - BOTH RUN STAGES ARE CLASSIFIED, and a harness fault is refused. The
    #  three dispositions are kept distinct: a run that aborted BEHAVIOURALLY still
    #  leaves evidence to compare, whereas a runner handed a bad command line leaves
    #  none. `irs030` has NO `WS-Term-Code` and returns 0, so on this operation the
    #  set of admissible term codes is EMPTY and any non-zero status is a fault by
    #  construction - which is why the scenario's declared expected status of 0 is
    #  structural here rather than merely expected.
    # ------------------------------------------------------------------
    operation = str(definition.get("operation") or "irs_post")
    for stage in (run.cobol_run, run.python_run):
        disposition = protocol.classify_run(stage, operation=operation)
        assert disposition != "harness-fault", (
            f"HARNESS FAULT rather than a behavioural difference:\n"
            f"{stage.describe()}\n"
            f"  Operation {operation!r} has NO admissible term code - `irs030` "
            f"carries no `WS-Term-Code` at all [irs/irs030.cbl:L552-L554] and "
            f"returns 0 - so a non-zero status here means the runner could not do "
            f"its job, not that the two implementations disagree. The dump was still "
            f"taken, because absence is evidence, but the run's own status cannot be "
            f"read as a verdict."
        )

    # ------------------------------------------------------------------
    #  GUARD 5b - THE OBSERVED DISPOSITION MATCHES THE ONE THE SCENARIO DECLARED
    #  (finding F-48).
    #
    #  Guard 5 above establishes that neither run stage was a HARNESS FAULT, which is
    #  a different and much weaker claim: it says the runner did its job, not that the
    #  cycle reached the disposition this scenario says it should reach. Every other
    #  scenario test carries this guard; this one was the only one of the eight that
    #  did not, so `clean_batch_irs` was the one route on which a cycle could have
    #  aborted with a status the scenario never declared and still been compared -
    #  and if the abort happened identically on both sides, the diff would have been
    #  EMPTY and the run reported as parity.
    #
    #  `reference_only=True` for the same reason the other tests use it: an ORACLE
    #  that did not reach its declared disposition means this scenario was never set
    #  up as declared, which is a setup error, while a PYTHON side that diverges from
    #  the oracle is a behavioural regression and is reported as a failure by the
    #  test that compares the two dispositions.
    # ------------------------------------------------------------------
    #  BOTH SIDES DROVE THE SAME ORDERED OPERATION LIST (finding F-12). The
    #  comparison below is between one COBOL run and one Python run, and it means
    #  nothing unless the two drove the same work in the same order - an empty diff
    #  between a short run and a full one being the most dangerous false pass this tier
    #  can produce. Both runners resolve the list from the scenario itself and publish
    #  one status row per operation, so it is checked rather than assumed.
    protocol.assert_operations_driven(run, operations=(operation,))

    protocol.assert_declared_statuses(
        run,
        operations=(operation,),
        declared=list(definition["expected_status"]),
        reference_only=True,
    )

    # ------------------------------------------------------------------
    #  GUARD 6 - BOTH SIDES STARTED FROM THE SAME RECORDED SEEDED STATE. Row counts
    #  only, one line per affected table in the declared order, compared as bytes.
    #  Stage 5 drops and re-applies all 33 tables and re-seeds between the two runs,
    #  so "the same state" is a claim about that reset having worked - and on THIS
    #  route it is load-bearing twice over, because the oracle run at stage 2 empties
    #  the transfer table and a failed reset would leave the Python run walking
    #  nothing.
    # ------------------------------------------------------------------
    protocol.assert_seed_fingerprints_agree(run)

    # ------------------------------------------------------------------
    #  GUARD 7 - SOMETHING WAS THERE TO COMPARE. Guard 1 rules out the flag that
    #  sends the whole run to indexed files, but a seed that never landed produces
    #  exactly the same empty-and-agreeing dumps with the flag set correctly. This
    #  counts rows and nothing else, so it can neither judge a value nor add
    #  validation the cycle does not have (R-3, R-6).
    # ------------------------------------------------------------------
    protocol.assert_non_vacuous(run, tables_requiring_rows=SEEDED_TABLES)

    return run


# ---------------------------------------------------------------------------
#  THE PRECONDITIONS - NO COMPOSE STACK REQUIRED
#
#  These read the scenario definition, the frozen schema and the pinned clock, all of
#  which are files on disk. They must therefore PASS on a bare host, and they are the
#  reason a mis-declared scenario is caught before an oracle run is spent on it.
# ---------------------------------------------------------------------------


def test_scenario_definition_preconditions(
    scenario_loader: object,
    pinned_clock: object,
    harness: object,
    repo_root: object,
) -> None:
    """The scenario declares every input this route takes, and pins each explicitly.

    NEEDS NO STACK. Every value checked here is declared in
    `harness/scenarios/clean_batch_irs.yaml` and read with the safe YAML loader; the
    file is never opened directly and no value is retyped from the Agent Action Plan.

    THE FALSE-PASS TRAP IS THE FIRST THING ASSERTED. `File-System-Used pic 9`
    [copybooks/wssystem.cob:L112] with `88 FS-Cobol-Files-Used value zero` L113 and
    `88 FS-MySql-Used value 1` L114 decides whether the handler reaches the relational
    database at all [common/acas008.cbl:L323-L325]. Seeded zero would leave BOTH
    dumps empty and the comparison would exit clean having compared nothing.

    THE FAN-OUT SWITCH IS AN ASSERTION ABOUT THE SEEDED ROW, NOT AN ARGUMENT. The IRS
    entry point publishes no fan-out option and no calling-data option, so on this
    route [copybooks/wssystem.cob:L179-L181] reaches the program only through the
    seeded system row. Agent Action Plan section 0.6.4: "leaving it at a default would
    make the affected-table list ambiguous."

    THE PINNED CLOCK IS REQUIRED EVEN THOUGH `irs030` TAKES NO TEXT DATE, because
    parameter 2 of [irs/irs030.cbl:L552-L554] is the ordinary ACAS system record,
    which carries `Run-Date binary-long` [copybooks/wssystem.cob:L67] - a real column,
    visible in a dump.

    THE SEED REQUIREMENTS THAT MAKE THE ANOMALIES OBSERVABLE are properties of the
    flat files under the scenario's own seed directory and are not expressible as YAML
    scalars, so they are recorded against `seed.data_dir` in the module docstring
    rather than asserted here: a clean balanced posting; postings hitting both VAT
    control accounts including at least one whose debit or credit account IS 31 or 32,
    which is what makes A-5 observable; one posting whose credit account is MISSING,
    which triggers A-4; and one posting whose date text fails a bridge guard, which
    exercises A-7. `def-acs (31)` and `def-acs (32)` must also name accounts that
    EXIST in `IRSNL-REC`, or aborts 2 and 3 [irs/irs030.cbl:L1597-L1601, L1607-L1611]
    fire and the run bypasses `EOJ` entirely.

    THE CREDENTIAL PRECONDITION IS THE HARNESS'S, NOT THIS FILE'S.
    [copybooks/wssystem.cob:L137-L144] ships the defaults, the IRS handlers copy them
    into `RDB-Data` [common/acasirsub1.cbl:L726], [common/acasirsub3.cbl:L409],
    [common/acas008.cbl:L558-L563], and the target block
    [copybooks/wsfnctn.cob:L56-L62] limits the user and password to twelve characters.
    The `ACAS_DB_*` environment must EQUAL the `RDBMS-*` fields in the seeded
    `system.dat`; the harness verifies that, and this file does not duplicate the
    check.

    Args:
        scenario_loader: Loads one scenario definition with the safe YAML loader.
        pinned_clock: The project-wide `PinnedRunDate`.
        harness: The three harness modules, for the harness's own validated
            scenario-table reader.
        repo_root: The repository root, resolved from `tests/conftest.py`'s own
            location, so a run from any working directory finds the same tree.
    """
    definition = scenario_loader(SCENARIO)

    # Identity. Both runners take the scenario name from the file's own basename when
    # no explicit key is present, so the two must agree by construction.
    assert (
        str(definition.get("name")),
        str(definition.get("subsystem")),
        str(definition.get("operation")),
    ) == (SCENARIO, "irs", "irs_post"), (
        f"the definition must identify itself as {SCENARIO} on the IRS subsystem "
        f"running `irs_post`; it declares name={definition.get('name')!r} "
        f"subsystem={definition.get('subsystem')!r} "
        f"operation={definition.get('operation')!r}. Both runners take the scenario "
        f"name from the file's own basename when no explicit key is present, so the "
        f"name and the file stem must agree by construction."
    )

    # The operation list the Python-side runner prefers, and the singular key the
    # oracle-side runner reads, must resolve to the SAME single operation.
    assert list(definition.get("operations") or []) == ["irs_post"], (
        f"{SCENARIO} must run exactly the one operation this route has; it declares "
        f"{definition.get('operations')!r}. [irs/irs.cbl:L666-L672] dispatches "
        f"`irs030` and nothing else on menu option four."
    )

    # 3.1 THE FALSE-PASS TRAP.
    system = definition.get("system") or {}
    assert int(system.get("file_system_used", -1)) == 1, (
        f"{SCENARIO} must seed `File-System-Used` = 1, the `88 FS-MySql-Used` "
        f"condition [copybooks/wssystem.cob:L114]; it declares "
        f"{system.get('file_system_used')!r}. Zero is `88 FS-Cobol-Files-Used` "
        f"[copybooks/wssystem.cob:L113], and [common/acas008.cbl:L323-L325] then "
        f"never performs `ba-Process-RDBMS`: the run would touch indexed files only, "
        f"BOTH DUMPS WOULD COME BACK EMPTY, and the comparison would exit 0 having "
        f"compared nothing. That is a silent FALSE PASS, and it is the single most "
        f"dangerous mis-declaration available to this scenario."
    )

    # 3.2 THE PROMOTED DESTRUCTIVE ANSWER. Asserted in full by
    # `test_clear_posting_file_answer_is_pinned`; asserted here because it is one of
    # the inputs this route takes and the definition would otherwise be incomplete.
    assert _clear_postings_answer(definition) == "Y", (
        f"{SCENARIO} must pin the end-of-job answer to Y. There is NO COBOL DEFAULT: "
        f"the `[Y]` in [irs/irs030.cbl:L1716] is display text and "
        f"[irs/irs030.cbl:L1718-L1719] re-asks for ever on anything that is neither "
        f"Y nor N."
    )

    # 3.3 THE THREE-STATE FAN-OUT SWITCH, pinned explicitly. The three states are the
    # frozen declaration's own: `IRS-Instead pic x` [copybooks/wssystem.cob:L179],
    # `88 IRS-Used value "Y"` L180, `88 IRS-Both-Used value "B"` L181. The THIRD state
    # has NO CONDITION NAME AT ALL - both predicates are simply false for a space,
    # which is General Ledger only.
    gl_only, irs_used, both_used = " ", "Y", "B"
    assert "irs_instead" in definition, (
        f"{SCENARIO} must pin the fan-out switch explicitly. Agent Action Plan "
        f"section 0.6.4: leaving it at a default would make the affected-table list "
        f"ambiguous. The oracle-side runner also requires the key to be PRESENT even "
        f"when its value is a space."
    )
    declared_switch = str(definition.get("irs_instead"))
    assert declared_switch in {gl_only, irs_used, both_used}, (
        f"{SCENARIO} declares the fan-out switch as {declared_switch!r}, which is "
        f"none of the three states `IRS-Instead pic x` can hold "
        f"[copybooks/wssystem.cob:L179-L181]."
    )
    assert str(system.get("irs_instead")) == declared_switch, (
        f"the grouped and flat spellings of the fan-out switch disagree: "
        f"{system.get('irs_instead')!r} against {declared_switch!r}. They are written "
        f"side by side precisely so that any drift is visible at a glance."
    )
    # WHAT THE AFFECTED-TABLE LIST IMPLIES. The switch governs whether the four Sales
    # and Purchase posting programs fan out into the transfer table; `irs030` itself
    # never tests it. This scenario runs `irs_post` alone, so no Sales or Purchase
    # program runs and none of their tables is on the list - which is exactly why the
    # General-Ledger-only space is the right pin: it guarantees the transfer file
    # holds what the seed put there and nothing a sibling program contributed.
    declared = _declared_tables(definition)
    trading = [
        name
        for name in declared
        if name.startswith(("SALEDGER", "SAINV", "SAITM", "PULEDGER", "PUINV",
                            "PUITM", "ANALYSIS", "VALUEANAL"))
    ]
    assert not trading, (
        f"{SCENARIO} lists Sales or Purchase tables {trading}, which this route "
        f"cannot write: [irs/irs.cbl:L666-L672] dispatches `irs030` alone."
    )
    assert declared_switch == gl_only, (
        f"{SCENARIO} pins the fan-out switch to {declared_switch!r}. With no Sales or "
        f"Purchase table on the affected-table list, no fan-out can occur, so the "
        f"General-Ledger-only space is what the list implies - and pinning it is what "
        f"guarantees the transfer table holds exactly the seeded rows."
    )

    # 3.4 THE PINNED CLOCK, in both observables, and its two flat mirrors.
    clock = definition.get("clock") or {}
    assert str(clock.get("to_day")) == pinned_clock.to_day, (
        f"{SCENARIO} declares the text run date {clock.get('to_day')!r} while the "
        f"project pin is {pinned_clock.to_day!r}. `to-day pic x(10)` in DD/MM/CCYY "
        f"form is a linkage parameter and never a column, but two different pinned "
        f"dates in one run would still make every comparison meaningless."
    )
    assert int(clock.get("run_date", -1)) == pinned_clock.run_date, (
        f"{SCENARIO} declares the binary run date {clock.get('run_date')!r} while the "
        f"project pin is {pinned_clock.run_date}. `Run-Date binary-long` "
        f"[copybooks/wssystem.cob:L67] IS a real SYSTEM-REC column, so a one-day shift "
        f"would surface three tables into a diff looking like a posting difference."
    )
    assert str(definition.get("run_date_text")) == pinned_clock.to_day, (
        f"the clock block and its flat mirror disagree on the text date: "
        f"{clock.get('to_day')!r} against {definition.get('run_date_text')!r}."
    )
    assert int(definition.get("run_date_binary", -1)) == pinned_clock.run_date, (
        f"the clock block and its flat mirror disagree on the binary date: "
        f"{clock.get('run_date')!r} against {definition.get('run_date_binary')!r}. "
        f"`Run-Date binary-long` [copybooks/wssystem.cob:L67] is a real column."
    )
    # On this route the text form is DERIVED by the menu from the binary value
    # [irs/irs.cbl:L632-L634] rather than passed in, so the pair must agree.
    assert int(system.get("date_form", -1)) == int(definition.get("date_form", -2)), (
        f"the grouped and flat spellings of `Date-Form` "
        f"[copybooks/wssystem.cob:L128] disagree: {system.get('date_form')!r} "
        f"against {definition.get('date_form')!r}."
    )

    # 3.5 A light check here; the full one is
    # `test_affected_tables_are_in_scope_and_alphabetical`.
    assert len(declared) == 5, (
        f"{SCENARIO} must bound the comparison by exactly five tables - the four the "
        f"verb census justifies plus SYSTEM-REC; it declares {list(declared)}."
    )

    # THE EXPECTED STATUS IS STRUCTURAL, NOT MERELY EXPECTED. `irs030` has no
    # `WS-Term-Code` [irs/irs030.cbl:L552-L554] and returns 0, and there is no
    # dispatch gate at all [irs/irs.cbl:L666-L672] - contrast General's
    # `if ws-term-code = 5` [general/general.cbl:L810-L811], Sales' two `not = zero`
    # gates and Purchase's commented-out gate. THE ASYMMETRY IS NOT HARMONISED.
    assert list(definition.get("expected_status") or []) == [0], (
        f"{SCENARIO} must expect status 0. `irs030` carries no term code at all, so "
        f"zero states that the section ran to completion - it opened the transfer "
        f"file, found both control accounts, walked the fixture and reached `EOJ` "
        f"[irs/irs030.cbl:L1702] rather than leaving through one of the three guards "
        f"at [irs/irs030.cbl:L1579-L1581], [irs/irs030.cbl:L1597-L1601] or "
        f"[irs/irs030.cbl:L1607-L1611], every one of which BYPASSES `EOJ` entirely "
        f"because `main99-exit.` [irs/irs030.cbl:L1729] sits after `EOJ-q1.` "
        f"[irs/irs030.cbl:L1715]. It declares "
        f"{definition.get('expected_status')!r}."
    )

    # ⭐ 3.5b THE ALLOCATOR CANNOT COLLIDE, WHICH IS WHY REJECTION CLASS 4 IS NOT
    # REACHED. `move next-post to post-key.` [irs/irs030.cbl:L1670] then `add 1 to
    # next-post.` [irs/irs030.cbl:L1671] allocate one internal posting key per transfer
    # row that reaches the write, and `perform acasirsub4-Write`
    # [irs/irs030.cbl:L1672-L1678] jumps to `EOJ` if the write reports any error. The
    # write is an INSERT, so the only failure this fixture could produce is a DUPLICATE
    # KEY - and the module docstring's rejection-class table says class 4 is NOT
    # exercised here. This is the assertion behind that statement: every key the
    # allocator can hand out lies strictly above every key the seed already occupies, so
    # no collision is possible and the claim is withdrawn on measured grounds rather than
    # asserted without support.
    # `seed_records["system.dat"]` is keyed by the four RELATIVE RECORD numbers the
    # frozen loader block writes - 1 for the system record, 2 for the defaults, 3 for
    # final and 4 for the totals [common/masterLD.sh:L51-L87] - and each value is a LIST
    # of records. `Next-Post` lives in relative record 1, so the search walks the blocks
    # rather than assuming a shape, and fails loudly if the field moves.
    system_blocks = definition["seed_records"]["system.dat"]
    next_post = None
    for block in system_blocks.values():
        for record in block if isinstance(block, list) else [block]:
            if isinstance(record, dict) and "Next-Post" in record:
                next_post = int(record["Next-Post"])
    assert next_post is not None, (
        "`system.dat` must declare `Next-Post`, the counter "
        "[copybooks/irswssystem.cob:L25] the section allocates internal posting keys "
        "from; without it the allocator's band is unknown and rejection class 4's "
        "reachability cannot be stated either way."
    )
    seeded_internal = [int(row["Post-Key"]) for row in
                       definition["seed_records"]["irspost.dat"]]
    transfer_rows = len(definition["seed_records"]["postings2irs.dat"])
    allocated = range(next_post, next_post + transfer_rows)
    assert not set(allocated) & set(seeded_internal), (
        f"the allocator would hand out keys {allocated.start}..{allocated.stop - 1} "
        f"(`Next-Post` {next_post}, and at most {transfer_rows} transfer rows reach the "
        f"write) and `irspost.dat` already occupies {sorted(seeded_internal)!r}. They "
        f"OVERLAP, so `perform acasirsub4-Write` [irs/irs030.cbl:L1672] could fail on a "
        f"duplicate key and jump to `EOJ` [irs/irs030.cbl:L1673-L1678] - which would "
        f"make rejection class 4 reachable. That is not a fault, but this file's "
        f"rejection-class table states the class is NOT exercised: update the table, and "
        f"add the assertions that observe the committed partial state, before changing "
        f"this fixture."
    )

    # 3.6 THE SIX SEED FILES, and the frozen loader each is mapped to.
    expected_seed_files = [
        "system.dat",        # the four-loader block  [common/masterLD.sh:L51-L87]
        "irsacnts.dat",      # irsnominalLD           [common/masterLD.sh:L99]
        "irsdflt.dat",       # irsdfltLD              [common/masterLD.sh:L100]
        "irsfinal.dat",      # irsfinalLD             [common/masterLD.sh:L101]
        "irspost.dat",       # irspostingLD           [common/masterLD.sh:L102]
        "postings2irs.dat",  # slpostingLD -> PSIRSPOST-REC  [common/masterLD.sh:L110]
    ]
    seed = definition.get("seed") or {}
    assert list(seed.get("files") or []) == expected_seed_files, (
        f"{SCENARIO} must seed exactly the six flat files this route reads; it "
        f"declares {seed.get('files')!r}. `system.dat` is not optional: the frozen "
        f"order seeds the system block first and unconditionally "
        f"[common/masterLD.sh:L50-L88], and it is what carries `Run-Date` "
        f"[copybooks/wssystem.cob:L67], the file-system flag "
        f"[copybooks/wssystem.cob:L112] and the fan-out switch "
        f"[copybooks/wssystem.cob:L179-L181]."
    )
    assert list(definition.get("seed_files") or []) == expected_seed_files, (
        f"the seed block and its flat mirror disagree: {seed.get('files')!r} against "
        f"{definition.get('seed_files')!r}. `harness/seed.sh` reads the flat list."
    )
    data_dir = str(seed.get("data_dir") or "")
    assert data_dir and not set(data_dir) & set("/\\"), (
        f"{SCENARIO} must name its seed fixture as a plain relative directory, "
        f"resolved against the directory holding the scenario file; it declares "
        f"{seed.get('data_dir')!r}. A path here would carry a host identity into a "
        f"file required to have none."
    )
    assert str(definition.get("seed_dir")) == data_dir, (
        f"the seed block and its flat mirror disagree on the fixture directory: "
        f"{seed.get('data_dir')!r} against {definition.get('seed_dir')!r}."
    )

    # THE HARNESS'S OWN VALIDATED READER MUST AGREE. `scenario_tables` is what the dump
    # and comparison stages resolve a scenario's table list with, and it validates each
    # name against the in-scope inventory itself, refusing an out-of-scope or unknown
    # table by name rather than with a not-found. Reading the list twice by two
    # independent routes is what makes a silent disagreement impossible.
    resolved = tuple(
        harness.dump_tables.scenario_tables(
            repo_root / "harness" / "scenarios" / f"{SCENARIO}.yaml"
        )
    )
    assert resolved == declared, (
        f"the harness resolves {SCENARIO}'s tables as {list(resolved)} while this "
        f"file reads {list(declared)}. The comparison is bounded by the harness's "
        f"reading, so a disagreement would mean this file is asserting about a "
        f"different set of tables from the one actually compared."
    )


def test_affected_tables_are_in_scope_and_alphabetical(
    scenario_loader: object,
    in_scope_table_names: object,
    harness: object,
) -> None:
    """Exactly five tables, alphabetical, all in scope - and `IRSFINAL-REC` ABSENT.

    NEEDS NO STACK.

    FOUR ARE JUSTIFIED BY A MEASURED VERB CENSUS, and the fifth, SYSTEM-REC, by
    measured comparability: the IRS menu exit rewrites key 1 after
    zz095-Restore-IRS-System-Data, so the Next-Post allocator is persisted there and
    nowhere else, and both sides end byte-identical (rule R-6).

    THE FOUR ARE JUSTIFIED BY A MEASURED VERB CENSUS over
    `Ledger-Postings-Add`, not by inference:

        acas008     Open-Input [irs/irs030.cbl:L1578], Read-Next
                    [irs/irs030.cbl:L1620], OPEN-OUTPUT = DELETE-ALL
                    [irs/irs030.cbl:L1723], Close [irs/irs030.cbl:L1712, L1724]
                    => PSIRSPOST-REC read then EMPTIED
        acasirsub1  Read-Indexed x11 and REWRITE x7    => IRSNL-REC MUTATED
        acasirsub4  Open, WRITE [irs/irs030.cbl:L1673] => IRSPOSTING-REC MUTATED
        acasirsub3  ZERO facade verbs, reached only by `move 3 to file-function.`
                    [irs/irs030.cbl:L1585] and `perform acasirsub3.`
                    [irs/irs030.cbl:L1586]             => IRSDFLT-REC READ ONLY
        acasirsub5  ZERO verbs of any kind              => IRSFINAL-REC UNTOUCHED

    `IRSFINAL-REC`'S ABSENCE IS ASSERTED POSITIVELY, because it is exactly the kind of
    thing a future contributor would "fix". The frozen source says so outright at
    [irs/irs030.cbl:L296]:
    `03  Final-Record          pic x.    *> Table/File not used in this program.`
    The table IS in scope for the migration as a whole, so its absence from THIS list
    is a measured choice and not an oversight - which is why both halves are asserted.

    THE DECLARED ORDER IS LOAD-BEARING, not cosmetic: the comparison reports in the
    scenario's declared order and the Python-side runner fingerprints the seeded row
    counts one table per line in that same order, so a disagreement between the two is
    a harness fault. Alphabetical is the convention every scenario file shares.

    THE ELEVEN OUT-OF-SCOPE TABLES ARE NEVER DUMPED, and the frozen column counts are
    checked against the schema as a cheap, strong tripwire on schema tampering - the
    schema is frozen (R-3), so any disagreement means either the inventory or the
    checkout is wrong.

    Args:
        scenario_loader: Loads the scenario definition.
        in_scope_table_names: The twenty-two in-scope names, ascending, read from the
            harness inventory and never restated.
        harness: The three harness modules, for the frozen per-table facts.
    """
    declared = _declared_tables(scenario_loader(SCENARIO))
    in_scope = tuple(in_scope_table_names)
    dump_tables = harness.dump_tables

    assert declared == (
        "IRSDFLT-REC",
        "IRSNL-REC",
        "IRSPOSTING-REC",
        "PSIRSPOST-REC",
        "SYSTEM-REC",
    ), (
        f"{SCENARIO} must bound the comparison by exactly these five, in alphabetical "
        f"order; it declares {list(declared)}. Four are justified by the verb census. "
        f"SYSTEM-REC is the fifth and it matters most HERE: the IRS menu exit rewrites "
        f"key 1 [irs/irs.cbl:L755-L775] AFTER performing zz095-Restore-IRS-System-Data, "
        f"so the Next-Post allocator this run advances is persisted through that path "
        f"and nowhere else. An allocator that drifted, or a key reused, would show in "
        f"this row and in no other. Measured byte-identical on both sides (rule R-6)."
    )
    assert list(declared) == sorted(declared), (
        f"the affected-table list must be alphabetical: {list(declared)}. The order "
        f"is load-bearing - the report and the seed fingerprint both follow it."
    )
    assert len(set(declared)) == len(declared), (
        f"the affected-table list repeats a table: {list(declared)}. A table compared "
        f"twice would double-count every finding in it."
    )

    for table in declared:
        assert table in in_scope, (
            f"`{table}` is not one of the twenty-two in-scope tables {list(in_scope)}. "
            f"The eleven the posting cycle never touches are refused by name rather "
            f"than by a not-found, and dumping one would compare state no in-scope "
            f"program can produce."
        )
        assert table not in dump_tables.OUT_OF_SCOPE, (
            f"`{table}` is one of the eleven out-of-scope tables and must never be "
            f"dumped."
        )

    # IRSFINAL-REC: in scope for the migration, DELIBERATELY off this list. BOTH halves
    # are asserted, because only together do they say "measured choice" rather than
    # "oversight".
    assert "IRSFINAL-REC" in in_scope, (
        f"IRSFINAL-REC must be one of the twenty-two in-scope tables, or its absence "
        f"from this scenario's list would be an accident of the inventory rather than "
        f"the measured decision [irs/irs030.cbl:L296] records. In scope: "
        f"{list(in_scope)}."
    )
    assert "IRSFINAL-REC" not in declared, (
        f"IRSFINAL-REC must NOT be on {SCENARIO}'s affected-table list. "
        f"`acasirsub5` is performed with ZERO verbs of any kind in "
        f"`Ledger-Postings-Add`, and [irs/irs030.cbl:L296] says so in the frozen "
        f"source itself: `03  Final-Record          pic x.    *> Table/File not used "
        f"in this program.` Adding it would compare a table nothing on this route can "
        f"write, and any difference found would be an artefact."
    )

    # The frozen per-table facts, as a tripwire. Each count and key is the frozen
    # schema's, cited to the `CREATE TABLE` that declares it.
    expected_facts = {
        "IRSDFLT-REC": ("DEF-REC-KEY", 4, 189),
        "IRSNL-REC": ("KEY-1", 15, 238),
        "IRSPOSTING-REC": ("KEY-4", 13, 274),
        "PSIRSPOST-REC": ("IRS-POST-KEY", 10, 366),
    }
    for table, (primary_key, column_count, schema_line) in expected_facts.items():
        specification = dump_tables.IN_SCOPE[table]
        assert specification.primary_key == primary_key, (
            f"`{table}` is ordered by `{specification.primary_key}` and this file "
            f"expects `{primary_key}` [mysql/ACASDB.sql:L{schema_line}]. Rows align "
            f"by primary-key VALUE, so the alignment column is not negotiable."
        )
        assert specification.column_count == column_count, (
            f"`{table}` declares {specification.column_count} columns and the frozen "
            f"schema declares {column_count} at "
            f"[mysql/ACASDB.sql:L{schema_line}]. The schema is FROZEN (R-3), so a "
            f"disagreement means either the inventory or the checkout is wrong."
        )
        assert specification.schema_line == schema_line, (
            f"`{table}` is recorded as declared at "
            f"[mysql/ACASDB.sql:L{specification.schema_line}] and this file cites "
            f"L{schema_line}. The schema is frozen, so the citation cannot drift."
        )


def test_clear_posting_file_answer_is_pinned(scenario_loader: object) -> None:
    """The one promoted interactive answer, and the only one that destroys a table.

    NEEDS NO STACK.

    [irs/irs030.cbl:L1715-L1727], verbatim:

        1715  EOJ-q1.
        1716       display  "Can I clear the Ledgers Posting file? [Y]" at 1401 ...
        1717       accept   WS-Reply at 1440 with foreground-color 6 UPPER.
        1718       if       WS-Reply not = "Y" and not = "N"
        1719                go to EOJ-q1.
        1720       if       WS-Reply = "Y"
        1723                perform acas008-Open-Output
        1724                perform acas008-Close.
        1725       display  "Note counts and any messages" at 1401 ...
        1726       accept   WS-Reply at 1430.
        1727       display  space at 1401 with erase eol.

    THERE IS NO COBOL DEFAULT DESPITE THE `[Y]`. The bracket at
    [irs/irs030.cbl:L1716] is DISPLAY TEXT; [irs/irs030.cbl:L1718-L1719] sends control
    back to the top of the paragraph on anything that is neither Y nor N, so AN EMPTY
    REPLY LOOPS FOR EVER. The answer is consequently a genuine INPUT that must be
    pinned, and both runners refuse this operation without it. The accept is
    `with ... UPPER`, so the comparison is against upper case.

    WHY IT IS PROMOTED RATHER THAN DROPPED, per Agent Action Plan section 0.3.4:
    answering Y performs `acas008-Open-Output` [irs/irs030.cbl:L1723], and for this
    handler `fn-Open` with `fn-output` and `not FS-Cobol-Files-Used` sets
    `fn-delete-all` [common/acas008.cbl:L313-L319], with a second unguarded
    substitution at [common/acas008.cbl:L566] and
    [common/acas008.cbl:L571-L574]. The answer therefore CHANGES TABLE STATE. The
    trailing accept at [irs/irs030.cbl:L1726] is a bare acknowledgement with no
    database effect and is dropped.

    THE CONTRAST IS PRESERVED AND NEVER HARMONISED (A-NEW-8): the sibling handler
    [common/acas007.cbl:L305-L312] carries the same block with
    `set fn-delete-all to true` COMMENTED OUT at [common/acas007.cbl:L308], so a
    General-Ledger batch `Open-Output` does NOT truncate. Both behaviours are
    reproduced (R-4).

    Args:
        scenario_loader: Loads the scenario definition.
    """
    definition = scenario_loader(SCENARIO)
    answer = _clear_postings_answer(definition)

    assert answer == "Y", (
        f"{SCENARIO} must pin the end-of-job answer to Y; it pins {answer!r}. The "
        f"frozen program has NO DEFAULT - [irs/irs030.cbl:L1718-L1719] re-asks for "
        f"ever - so the value is an input and not decoration, and Y is what makes the "
        f"scenario exercise the truncation at [irs/irs030.cbl:L1723]."
    )

    declared = _declared_tables(definition)
    assert "PSIRSPOST-REC" in declared, (
        f"answering Y DELETES EVERY ROW of PSIRSPOST-REC "
        f"[common/acas008.cbl:L313-L319], so it must be among the compared tables; "
        f"{SCENARIO} declares {list(declared)}. This is also why the protocol's "
        f"reset-and-re-seed stage is load-bearing rather than hygienic: the oracle run "
        f"empties the transfer file, and without the re-seed the Python run would "
        f"start from an emptied file, walk nothing and post nothing."
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
    exercised end to end, over THIS scenario's own bound. It matters
    particularly here, where BOTH of the route's most distinctive effects are
    ABSENCES - A-4's missing `IRSPOSTING-REC` row and the bounded transfer clear - so
    a one-sided table and a one-sided row must each be a FINDING and never a reason
    to drop the table from the comparison.

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
#  THE VERDICT - REQUIRES THE COMPOSE STACK
#
#  Everything below reads the finished evidence of ONE completed ten-stage run. The
#  `parity` fixture applies the stack skip guard, so a bare host SKIPS with a precise
#  reason and never errors.
# ---------------------------------------------------------------------------


@pytest.mark.database
@pytest.mark.oracle
def test_clean_batch_post_irs_state_parity(
    parity: object,
    harness: object,
) -> None:
    """THE HEADLINE. The migrated cycle reproduced the compiled COBOL EXACTLY.

    Agent Action Plan section 0.8.5, acceptance criterion 1: "seed identically through
    the maintainer's load programs, run the compiled cycle, dump the affected tables
    ordering-normalised, reset, run the Python cycle, dump again - and the diff MUST BE
    EMPTY."

    THIS BODY CONTAINS ONLY THE VERDICT, and that is deliberate. Every stage and every
    guard happened in the `parity` fixture, so a HARNESS FAULT is a pytest ERROR; what
    is left here is the answer the protocol exists to produce, so a real divergence is
    a pytest FAILURE. The two can never be confused.

    THE COMPARISON IS EXACT. No tolerance, no epsilon, no closeness helper, no case- or
    whitespace-insensitive comparison, no numeric coercion: `1` against `"1"` IS a
    difference (R-2). Rows align by primary-key VALUE, never by position, and bounding
    is the scenario's affected-table list and nothing else - there is no ignore-list,
    no tolerance-list and no known-difference allowance anywhere in this file.

    WHAT A FAILURE HERE MEANS. The Python cycle diverges from the compiled COBOL on
    this route. It does NOT mean the books are wrong: this scenario deliberately
    produces an unbalanced double entry (A-4) and a lost update (A-5), and reproducing
    those exactly is the requirement. Suspect, in order: the debit rewrite moving to
    after the credit lookup; the two VAT snapshots being refreshed inside the loop
    instead of rewritten stale at end of job; the truncation of the transfer table
    being skipped or made conditional; a date component being "completed" rather than
    left at zero; and the two `ROUNDED` VAT computes at [irs/irs030.cbl:L1551] and
    [irs/irs030.cbl:L1562-L1563] having become truncating stores or the un-rounded
    subtract at [irs/irs030.cbl:L1564] having become rounded.

    Args:
        parity: The completed, guarded ten-stage run.
        harness: The three harness modules, for the report renderer.
    """
    assert parity.is_empty, (
        f"STATE PARITY FAILED for {SCENARIO}: the migrated Python cycle and the "
        f"compiled COBOL oracle produced DIFFERENT database state.\n"
        f"\n"
        f"  THIS IS A REAL BEHAVIOURAL DIFFERENCE, not an artefact. Every in-scope "
        f"table has a single-column primary key, no secondary index, no TIMESTAMP "
        f"column and no AUTO_INCREMENT column, so the dump order is total and stable "
        f"and the comparison is exact (Agent Action Plan section 0.6.6).\n"
        f"\n"
        f"  DO NOT 'FIX' THE ACCOUNTING. This scenario deliberately produces an "
        f"unbalanced double entry (A-4, [irs/irs030.cbl:L1635] then "
        f"[irs/irs030.cbl:L1641] then [irs/irs030.cbl:L1648-L1652]) and a lost update "
        f"(A-5, [irs/irs030.cbl:L1602] and [irs/irs030.cbl:L1612] rewritten at "
        f"[irs/irs030.cbl:L1704-L1708]). A defect reproduced is correct; a defect "
        f"fixed is a failure (R-4).\n"
        f"\n"
        f"  {parity.tree.total_differences} finding(s) across "
        f"{len(parity.tree.differing)} of the {len(parity.tables)} bounded table(s) "
        f"{list(parity.tables)}. Report at {parity.outcome.report}.\n"
        f"{parity.diagnose()}\n"
        f"  Every stage of the run:\n"
        f"{parity.describe()}"
    )


@pytest.mark.database
@pytest.mark.oracle
def test_a4_half_posted_double_entry_reproduced(
    parity: object,
    harness: object,
) -> None:
    """A-4: the ONE-SIDED outcome is identical on both sides, imbalance included.

    THE DEFECT. The debit is accumulated at [irs/irs030.cbl:L1635] and REWRITTEN at
    [irs/irs030.cbl:L1641], BEFORE the credit account is even looked up at
    [irs/irs030.cbl:L1645-L1647]. A missing credit account takes the skip at
    [irs/irs030.cbl:L1648-L1652], leaving a POSTED DEBIT WITH NO BALANCING CREDIT and
    NO `IRSPOSTING-REC` ROW. The run continues.

    NEVER ASSERT THAT DEBITS EQUAL CREDITS. They do not, and they must not. What is
    asserted is that the two implementations produce THE SAME imbalance, in the same
    accounts, to the penny, and that the SAME posting rows are absent. The aggregate
    debit and credit totals are compared ACROSS SIDES and never against each other -
    the second form would be an assertion of correct accounting, which on this route is
    itself a defect (R-4).

    ABSENCE IS THE EVIDENCE, which is why the protocol dumps whatever the run stages
    returned: a missing `IRSPOSTING-REC` row cannot be observed any other way. It
    surfaces in the report as a one-sided key rather than as a value difference, and
    both directions are asserted separately because they are materially different
    findings.

    THE TWO DISPOSITIONS MUST NEVER BE COLLAPSED, AND ONLY ONE OF THEM IS SEEDED HERE
    (finding MJ-11). A missing DEBIT account [irs/irs030.cbl:L1627-L1634], message
    IR032, is rejection class 1 - a CLEAN no-op, because nothing has been written yet. A
    missing CREDIT account [irs/irs030.cbl:L1645-L1652], message IR033, is rejection
    class 3 - a PARTIAL WRITE. Agent Action Plan section 0.8.1: "a single generic
    rejection path would fail this directive."

    ⚠️ THIS FIXTURE SEEDS CLASS 3 ONLY. `clean_batch_irs.yaml` withholds exactly one
    account - the CREDIT one, for A-4 - and requires every DEBIT account the transfer
    records reference to be present, so the IR032 path is never taken on this route and
    the assertions below say nothing about it. Nor could a state comparison say much: a
    clean no-op's whole signature is an ABSENCE, and an implementation that ABORTED the
    run on a missing debit, or that committed the debit anyway, can leave the same rows.
    Class 1 is therefore locked directly, by call sequence, in
    `tests/arithmetic/test_shipped_close_and_rejection_paths.py` section 2 - which
    drives the shipped `Input-Loop` over two transfer records, the first with a missing
    debit, and requires the second to be posted in full so that the rejection is proved
    to be a loop-back rather than a terminator. What THIS test owns is class 3.

    THE VAT ASYMMETRY IS PART OF THE SPECIFICATION: the debit side adds VAT when the
    side is "CR" [irs/irs030.cbl:L1636-L1637] and the credit side when it is "DR"
    [irs/irs030.cbl:L1654-L1655].

    Args:
        parity: The completed, guarded ten-stage run.
        harness: The three harness modules, for reading the normalised dumps.
    """
    from decimal import Decimal  # noqa: PLC0415 - see the module docstring on R-2

    ledger = _table_diff(parity, "IRSNL-REC")
    posting = _table_diff(parity, "IRSPOSTING-REC")

    # THE NOMINAL LEDGER AGREES, ACCOUNT FOR ACCOUNT AND PENNY FOR PENNY - including
    # every account whose debit moved without a matching credit.
    assert ledger.is_empty, (
        f"A-4 IS NOT REPRODUCED: the two sides disagree about `IRSNL-REC` after the "
        f"posting walk. The debit is rewritten at [irs/irs030.cbl:L1641] BEFORE the "
        f"credit account is looked up at [irs/irs030.cbl:L1645-L1647], so a missing "
        f"credit leaves a posted debit with no balancing credit - and that imbalance "
        f"must be reproduced, not corrected.\n"
        f"  missing on the Python side: {list(ledger.missing_in_python)}\n"
        f"  missing on the COBOL side:  {list(ledger.missing_in_cobol)}\n"
        f"  rows differing in a value:  {ledger.value_difference_count}\n"
        f"{parity.diagnose()}"
    )

    # THE POSTING RECORDS AGREE, INCLUDING THE ONES THAT ARE ABSENT. A transaction that
    # took the [irs/irs030.cbl:L1648-L1652] skip never reaches `acasirsub4-Write`
    # [irs/irs030.cbl:L1673], so its row is missing on BOTH sides or on neither.
    assert posting.missing_in_python == (), (
        f"A-4 IS NOT REPRODUCED: the oracle wrote `IRSPOSTING-REC` rows "
        f"{list(posting.missing_in_python)} that the migrated cycle did not. A row is "
        f"written only after BOTH ledger sides succeed "
        f"[irs/irs030.cbl:L1661-L1673], so a row missing on one side alone means the "
        f"two implementations disagree about which transactions completed."
    )
    assert posting.missing_in_cobol == (), (
        f"A-4 IS NOT REPRODUCED - AND THIS IS THE DIRECTION THAT LOOKS LIKE A FIX: "
        f"the migrated cycle wrote `IRSPOSTING-REC` rows "
        f"{list(posting.missing_in_cobol)} that the oracle did NOT. The most likely "
        f"cause is that the credit lookup was moved BEFORE the debit rewrite, so a "
        f"transaction the frozen program abandons half-posted now completes. That is a "
        f"defect fixed, which R-4 makes a failure."
    )
    assert posting.is_empty, (
        f"A-4 IS NOT REPRODUCED: the two sides disagree about `IRSPOSTING-REC`.\n"
        f"{parity.diagnose()}"
    )

    # THE IMBALANCE ITSELF, COMPARED ACROSS SIDES AND NEVER AGAINST ITSELF. Summed in
    # `decimal.Decimal` from the canonical decimal STRINGS the dump carries; no binary
    # floating-point value is created at any point (R-2). `DR` and `CR` are
    # `decimal(10,2) unsigned` [mysql/ACASDB.sql:L240-L241] and correspond to
    # `NL-DR` and `NL-CR` [copybooks/irswsnl.cob:L17-L18].
    totals = {}
    for side in ("cobol", "python"):
        dump = _normalised(harness, parity.paths, side, "IRSNL-REC")
        debit = sum(
            (Decimal(str(_cell(dump, row, "DR"))) for row in dump["rows"]),
            Decimal("0.00"),
        )
        credit = sum(
            (Decimal(str(_cell(dump, row, "CR"))) for row in dump["rows"]),
            Decimal("0.00"),
        )
        totals[side] = (debit, credit)

    assert totals["cobol"] == totals["python"], (
        f"A-4 IS NOT REPRODUCED: the aggregate nominal-ledger totals differ between "
        f"the two sides. COBOL debit {totals['cobol'][0]} credit "
        f"{totals['cobol'][1]}; Python debit {totals['python'][0]} credit "
        f"{totals['python'][1]}.\n"
        f"  NOTE WHAT IS **NOT** ASSERTED HERE: that the debits equal the credits. On "
        f"this route they need not, because [irs/irs030.cbl:L1641] commits a debit "
        f"that [irs/irs030.cbl:L1648-L1652] may then leave unmatched, and A-5's lost "
        f"update discards in-loop rewrites of the two VAT control accounts. The books "
        f"are wrong, and reproducing that wrongness exactly IS the requirement."
    )


@pytest.mark.database
@pytest.mark.oracle
def test_a5_lost_update_on_vat_control_accounts_reproduced(
    parity: object,
    harness: object,
    withheld: object,
) -> None:
    """A-5: accounts 31 and 32 hold the SNAPSHOT outcome, identically on both sides.

    THE DEFECT. The two VAT control accounts are read into working snapshots BEFORE the
    loop begins - `move def-acs (31) to nl-owning.` [irs/irs030.cbl:L1594] then
    `move WS-IRSNL-Record to nl31-record.` [irs/irs030.cbl:L1602], and
    `move def-acs (32) to nl-owning.` [irs/irs030.cbl:L1604] then
    `move WS-IRSNL-Record to nl32-record.` [irs/irs030.cbl:L1612], each after
    `perform acasirsub1-Read-Indexed.` at [irs/irs030.cbl:L1596] and
    [irs/irs030.cbl:L1606]. VAT is accumulated into those snapshots inside the loop and
    they are rewritten AT END OF JOB from the snapshots:

        1702  EOJ.
        1704       move     nl31-record to WS-IRSNL-Record.
        1705       perform  acasirsub1-Rewrite.
        1707       move     nl32-record to WS-IRSNL-Record.
        1708       perform  acasirsub1-Rewrite.

    So ANY in-loop rewrite of those same two accounts - the debit rewrite at
    [irs/irs030.cbl:L1641] or the credit rewrite at [irs/irs030.cbl:L1657], whenever a
    posting's debit or credit account happens to BE 31 or 32 - is DISCARDED. A textbook
    lost update, and silent.

    THE FOUR-WAY VAT LADDER that feeds the snapshots is gated by
    `if WS-IRS-Vat-AC-Def = zero / go to Input-Loop.` [irs/irs030.cbl:L1682-L1683],
    then 31 with "CR" to `nl31-cr` [irs/irs030.cbl:L1687], 31 with "DR" to `nl31-dr`
    [irs/irs030.cbl:L1691], 32 with "CR" to `nl32-cr` [irs/irs030.cbl:L1695] and 32
    with "DR" to `nl32-dr` [irs/irs030.cbl:L1699] - WITH NO FINAL `else`, so any other
    combination silently does nothing - and then `go to Input-Loop.`
    [irs/irs030.cbl:L1700].

    WHY THIS FILE OWNS THE LOCK. `docs/migration/anomaly-log.md` records that no
    arithmetic-tier test can see A-5: the defect is in ORDERING ACROSS A LOOP BOUNDARY,
    not in a computation, so an END-STATE assertion is the only observable that can
    witness it.

    THE TWO ACCOUNTS ARE LOCATED FROM THE DATA, NOT FROM A GUESS. `IRSDFLT-REC` is on
    the affected-table list and is therefore dumped; entries 31 and 32 of
    `03 Def-Group occurs 33.` [copybooks/irswsdflt.cob:L9] carry the account codes in
    `05 Def-Acs pic 9(5).` [copybooks/irswsdflt.cob:L10]. The nominal key is
    `03 NL-Key.` over `05 NL-Owning pic 9(5).` and `05 NL-Sub-Nominal pic 9(5).`
    [copybooks/irswsnl.cob:L9-L11], materialised by the bridge as
    `03 NL-Key pic 9(10).` [common/irsnominalMT.cbl:L225] and moved whole into
    `HV-KEY-1` [common/irsnominalMT.cbl:L1198], so with `nl-sub-nominal` set to zero
    [irs/irs030.cbl:L1595, L1605] the key is the owning code followed by five zeros.

    NEVER ASSERT WHAT THE BALANCES OUGHT TO BE. What is asserted is that the two
    implementations left the same values in the same two accounts.

    Args:
        parity: The completed, guarded ten-stage run.
        harness: The three harness modules, for reading the normalised dumps.
    """
    ledger = _table_diff(parity, "IRSNL-REC")
    assert ledger.is_empty, (
        f"A-5 IS NOT REPRODUCED: the two sides disagree about `IRSNL-REC`.\n"
        f"  missing on the Python side: {list(ledger.missing_in_python)}\n"
        f"  missing on the COBOL side:  {list(ledger.missing_in_cobol)}\n"
        f"{parity.diagnose()}"
    )

    defaults = {
        side: _normalised(harness, parity.paths, side, "IRSDFLT-REC")
        for side in ("cobol", "python")
    }
    ledgers = {
        side: _normalised(harness, parity.paths, side, "IRSNL-REC")
        for side in ("cobol", "python")
    }

    # The defaults table is read-only on this route, so the two sides must agree about
    # WHICH accounts the snapshots were taken from before anything else is compared.
    control_codes = {}
    for side, dump in defaults.items():
        rows = _rows_by_key(dump)
        codes = []
        for entry in (31, 32):
            row = rows.get(entry) or rows.get(str(entry))
            assert row is not None, (
                f"HARNESS FAULT: the {side} dump of `IRSDFLT-REC` carries no entry "
                f"{entry}. [irs/irs030.cbl:L1594] and [irs/irs030.cbl:L1604] read "
                f"`def-acs (31)` and `def-acs (32)` from "
                f"`03 Def-Group occurs 33.` [copybooks/irswsdflt.cob:L9]; without "
                f"them the section leaves through abort 2 or abort 3 "
                f"([irs/irs030.cbl:L1597-L1601], [irs/irs030.cbl:L1607-L1611]) and "
                f"BYPASSES `EOJ` entirely, so the scenario would measure nothing. "
                f"The dump holds {withheld(rows, column='DEF-REC-KEY')}."
            )
            codes.append(int(str(_cell(dump, row, "DEF-ACS"))))
        control_codes[side] = tuple(codes)

    assert control_codes["cobol"] == control_codes["python"], (
        f"HARNESS FAULT: the two sides read the VAT control accounts from different "
        f"default codes - COBOL {withheld(control_codes['cobol'], column='DEF-ACS')}, "
        f"Python {withheld(control_codes['python'], column='DEF-ACS')}. "
        f"`IRSDFLT-REC` is READ ONLY on this route "
        f"(`acasirsub3` is performed with zero facade verbs, "
        f"[irs/irs030.cbl:L1585-L1586]), so a difference here means the two runs were "
        f"not seeded from the same fixture."
    )

    # THE SNAPSHOT OUTCOME, ACCOUNT BY ACCOUNT. Nothing is recomputed: the two sides'
    # stored values are compared to each other.
    money_columns = (
        "DR",
        "CR",
        "DR-LAST-01",
        "CR-LAST-01",
        "DR-LAST-02",
        "CR-LAST-02",
        "DR-LAST-03",
        "CR-LAST-03",
        "DR-LAST-04",
        "CR-LAST-04",
    )
    for entry, code in zip((31, 32), control_codes["cobol"]):
        key = code * 100000
        observed = {}
        for side, dump in ledgers.items():
            rows = _rows_by_key(dump)
            row = rows.get(key) or rows.get(str(key))
            assert row is not None, (
                f"HARNESS FAULT: the {side} dump of `IRSNL-REC` carries no account "
                f"for `def-acs ({entry})` = {code}, whose key is {key} - the owning "
                f"code [copybooks/irswsnl.cob:L10] followed by a zero sub-nominal "
                f"[irs/irs030.cbl:L1595, L1605], packed into "
                f"`03 NL-Key pic 9(10).` [common/irsnominalMT.cbl:L225]. The account "
                f"MUST exist or [irs/irs030.cbl:L1597-L1601] and "
                f"[irs/irs030.cbl:L1607-L1611] abort the section before the loop and "
                f"neither snapshot is ever rewritten. The dump holds "
                f"{withheld(rows, column='NL-KEY')}."
            )
            observed[side] = tuple(
                _cell(dump, row, column) for column in money_columns
            )

        assert observed["cobol"] == observed["python"], (
            f"A-5 IS NOT REPRODUCED for VAT control account `def-acs ({entry})` = "
            f"{code} (key {key}).\n"
            f"  columns {list(money_columns)}\n"
            f"  COBOL  {withheld(observed['cobol'])}\n"
            f"  Python {withheld(observed['python'])}\n"
            f"\n"
            f"  THE EXPECTED OUTCOME IS THE SNAPSHOT ONE, NOT THE ACCUMULATED ONE. "
            f"The record read at [irs/irs030.cbl:L1596] or [irs/irs030.cbl:L1606] and "
            f"held at [irs/irs030.cbl:L1602] or [irs/irs030.cbl:L1612] is rewritten "
            f"unconditionally at [irs/irs030.cbl:L1704-L1705] or "
            f"[irs/irs030.cbl:L1707-L1708], DISCARDING any in-loop rewrite of the "
            f"same account made at [irs/irs030.cbl:L1641] or "
            f"[irs/irs030.cbl:L1657]. If the migrated cycle now preserves those "
            f"in-loop rewrites, THE LOST UPDATE HAS BEEN FIXED - and a defect fixed "
            f"is a failure (R-4). Check also the four-way ladder at "
            f"[irs/irs030.cbl:L1685-L1699]: it has NO FINAL `else`, so a combination "
            f"outside 31/32 crossed with DR/CR must silently do NOTHING."
        )


@pytest.mark.database
@pytest.mark.oracle
def test_psirspost_rec_clear_reproduces_the_frozen_high_key_threshold(
    parity: object,
    harness: object,
    scenario_loader: object,
) -> None:
    """The clear answer reproduces the bridge's bounded predicate on both sides.

    Answering Y at [irs/irs030.cbl:L1720-L1724] still reaches the special
    open-output route in [common/acas008.cbl:L313-L319]. The bridge does NOT issue an
    unqualified DELETE, however. It moves 99999 into both five-digit key components
    [common/slpostingMT.cbl:L849-L851] and deletes only rows whose SQL key is below
    the resulting text bound, 9999999999 [common/slpostingMT.cbl:L857-L891].

    F-7 made the six fixture rows independently reachable by assigning distinct post
    numbers. The frozen group-to-binary move stores each resulting key near
    472328296244... - well ABOVE 9999999999. Consequently the operator's Y answer is
    a measured NO-OP for this reachable RDBMS fixture: all six rows remain on both
    sides. Treating the paragraph name "Delete-ALL" as proof of truncation would assert
    intended accounting rather than compiled behaviour, violating R-4 and R-6.

    The reset between the two runs remains load-bearing even though this table is
    retained: the other three affected tables are mutated, and both sides must still
    begin from the identical six-row transfer fixture.

    Args:
        parity: The completed, guarded ten-stage run.
        harness: The three harness modules, for reading the normalised dumps.
        scenario_loader: Loads the scenario definition, to confirm the pinned answer.
    """
    answer = _clear_postings_answer(scenario_loader(SCENARIO))
    assert answer == "Y", (
        f"this assertion is only meaningful when the scenario answers Y; it pins "
        f"{answer!r}. With N the table is left alone and would still have to agree on "
        f"both sides, but it would not be emptied."
    )

    transfer = _table_diff(parity, "PSIRSPOST-REC")
    assert transfer.is_empty, (
        f"the two sides disagree about `PSIRSPOST-REC` after the bounded clear.\n"
        f"  COBOL rows {transfer.cobol_row_count}, Python rows "
        f"{transfer.python_row_count}\n"
        f"  missing on the Python side: {list(transfer.missing_in_python)}\n"
        f"  missing on the COBOL side:  {list(transfer.missing_in_cobol)}\n"
        f"{parity.diagnose()}"
    )

    definition = scenario_loader(SCENARIO)
    seed_rows = definition["seed_records"]["postings2irs.dat"]
    expected_rows = len(seed_rows)
    delete_bound = 9_999_999_999
    assert expected_rows > 0, (
        "HARNESS FAULT: the transfer fixture is empty, so the frozen delete threshold "
        "cannot be observed."
    )

    for side in ("cobol", "python"):
        dump = _normalised(harness, parity.paths, side, "PSIRSPOST-REC")
        assert dump["row_count"] == expected_rows, (
            f"the {side} side retained {dump['row_count']} transfer row(s), expected "
            f"the fixture's {expected_rows}. The compiled bridge deletes only SQL keys "
            f"below {delete_bound} [common/slpostingMT.cbl:L849-L891]."
        )
        indexed = _rows_by_key(dump)
        assert len(indexed) == expected_rows, (
            f"the {side} dump reports {dump['row_count']} transfer rows but indexes "
            f"{len(indexed)} distinct primary keys."
        )
        low_keys = sorted(int(str(key)) for key in indexed if int(str(key)) < delete_bound)
        assert low_keys == [], (
            f"the {side} side retained transfer keys below the frozen clear bound "
            f"{delete_bound}: {low_keys}. Those rows should have matched "
            f"[common/slpostingMT.cbl:L857-L891]."
        )


@pytest.mark.database
@pytest.mark.oracle
def test_a6_rewrite_verb_can_never_succeed(
    parity: object,
    harness: object,
    protocol: object,
) -> None:
    """A-6: the state reflects the ENTRY GUARD, not an update - identically both sides.

    THE DEFECT. [common/acas008.cbl:L299-L307] is an `evaluate File-Function` whose
    `when 4` (read-indexed), `when 7` (re-write), `when 9` (start) and `when 8`
    (delete) all fall into one branch that sets `WE-Error = 988`
    [common/acas008.cbl:L304] - carrying the maintainer's own comment
    `*> Action type wrong for file type (seq)   988` - then `FS-Reply = 99`
    [common/acas008.cbl:L305], then `go to aa999-main-exit`
    [common/acas008.cbl:L306]. The rejection is UNCONDITIONAL AND AT ENTRY, before any
    access-type or file-mode logic runs, because the underlying file is sequential. The
    IRS facade nevertheless publishes the re-write verb
    [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L163], so a caller invoking it ALWAYS
    fails, every time, for every record.

    WHAT THIS TEST PROVES, STATED EXACTLY. It proves a STATE fact: the transfer table
    is byte-identical before and after each cycle's run, on each side independently, and
    the two sides agree about it. It does NOT prove that the verb was invoked and
    refused - a run that never reached the verb would leave exactly the same state, and
    so would a migrated handler that silently did nothing, or raised, or returned a
    DIFFERENT failure pair. The status pair is a value returned to a caller rather than
    a table state, so it cannot be seen from here.

    THE PAIR IS THEREFORE LOCKED WHERE IT LIVES, by
    `tests/arithmetic/test_shared_storage_and_dispatch_boundaries.py` section 20, which
    calls `acas_posting/dal/acas008_spl_posting.py`'s `aa010_main` once per refused verb
    and requires `WE-Error 988` with `FS-Reply 99`, drives the published verbs through
    BOTH vocabularies, and proves by sabotage that no connection is attempted.

    THOSE TWO NUMBERS WERE MEASURED, NOT READ. A COBOL driver compiled against the
    frozen copybooks called the COMPILED `acas008` with its own linkage in its own
    order [common/acas008.cbl:L278-L284], once for each of `read-indexed` (4),
    `re-write` (7), `delete` (8) and `start` (9); GnuCOBOL 3.2 answered `988` and `99`
    every time. It also answered the CONTRAST: `read-next` (2), which the `evaluate`
    does not name, passed the guard and went on into the handler's real work - so the
    pair belongs to THIS GUARD and is not what `acas008` says whenever anything goes
    wrong. No connection was needed for any of it, which is itself part of the finding:
    the guard returns before any code that would want one.

    WHERE THE VERB ITSELF IS LOCKED, so that the pair of claims is complete. The status
    pair is a value returned to a caller rather than a table state, so it belongs to the
    data-access layer's tests, and it IS locked there:
    `tests/arithmetic/test_shared_storage_and_dispatch_boundaries.py` INVOKES all four
    refused functions - read-indexed (4), re-write (7), start (9) and delete (8) -
    through BOTH published alias sets, asserts `WE-Error 988` with `FS-Reply 99` on each,
    asserts the record is unchanged, and sabotages the handler's connection opener to
    prove the guard returns BEFORE any database work. The register entry for A-6 names
    those locks. This file supplies the state half; that file supplies the mechanism
    half; neither claims the other's ground.

    WHAT THE STATE CAN SHOW, AND WHAT THE MEASURED CLEAR ACTUALLY DOES. The only outcome
    the always-failing verb can produce is NO CHANGE - and on this fixture the
    end-of-job clear is a measured NO-OP too, because the frozen group move stores each
    key near 3472328296244457776, far above the bridge's 9999999999 bound
    [common/slpostingMT.cbl:L849-L891]. So the transfer table survives the run intact on
    BOTH sides, which is what makes a before-and-after comparison possible at all: had
    the clear emptied it, "no evidence of an update" would have been true of any
    behaviour whatsoever and this test would have asserted nothing. It is compared
    against its OWN PRE-RUN state, per side, and not merely across the two sides.

    THE ONE VERB THAT DOES REACH THE DATABASE ON THIS HANDLER is the open-output
    special case, and only because [common/acas008.cbl:L313-L319] is tested BEFORE the
    guard block. That ordering is the whole reason the truncation works while the
    re-write cannot, and it is reproduced rather than tidied (R-4).

    Args:
        parity: The completed, guarded ten-stage run.
        harness: The three harness modules, for reading the normalised dumps.
        protocol: The protocol bundle, for the before-and-after state comparison that
            makes this assertion non-vacuous.
    """
    # ⭐ THE NON-VACUITY GUARD, AND THE STRONGEST CLAIM HERE. Each side's PRE-run digest
    # of the transfer table is compared against its OWN POST-run digest. A table diff
    # compares the two SIDES, and two cycles that both mutated the table identically
    # would agree perfectly; this comparison instead asks "did this cycle change the
    # table at all", separately for each cycle, and the answer must be no. That is the
    # only state signature an unconditionally refused re-write can leave.
    protocol.assert_tables_unchanged_by_run(parity, unchanged=("PSIRSPOST-REC",))

    transfer = _table_diff(parity, "PSIRSPOST-REC")

    assert transfer.is_empty, (
        f"the two sides disagree about `PSIRSPOST-REC`, the table whose handler "
        f"refuses read-indexed, re-write, start and delete unconditionally at entry "
        f"[common/acas008.cbl:L299-L307] with `WE-Error 988` and `FS-Reply 99`. The "
        f"only state that guard can produce is NO CHANGE.\n"
        f"  missing on the Python side: {list(transfer.missing_in_python)}\n"
        f"  missing on the COBOL side:  {list(transfer.missing_in_cobol)}\n"
        f"  rows differing in a value:  {transfer.value_difference_count}\n"
        f"{parity.diagnose()}"
    )
    assert transfer.value_differences == (), (
        f"`PSIRSPOST-REC` rows present on both sides differ in a value, which on this "
        f"handler is impossible by construction: the re-write verb is refused "
        f"unconditionally at [common/acas008.cbl:L299-L307], so no in-place update can "
        f"occur. If the migrated data-access layer now performs one, A-6 HAS BEEN "
        f"FIXED - and a defect fixed is a failure (R-4).\n"
        f"{parity.diagnose()}"
    )
    assert transfer.row_count_differs is False, (
        f"`PSIRSPOST-REC` holds {transfer.cobol_row_count} row(s) on the COBOL side "
        f"and {transfer.python_row_count} on the Python side. The only two things this "
        f"route does to the table are a sequential read [irs/irs030.cbl:L1620] and the "
        f"end-of-job bounded delete [irs/irs030.cbl:L1723], so the counts cannot legally "
        f"differ."
    )
    # And the fixture is genuinely there to be compared. A zero-row table would satisfy
    # every assertion above vacuously, and the pre/post comparison as well.
    assert transfer.cobol_row_count > 0, (
        f"`PSIRSPOST-REC` is EMPTY on both sides, so nothing above has been "
        f"established: an empty table is unchanged by any behaviour and identical to "
        f"any other empty table. The scenario seeds six transfer rows and the frozen "
        f"clear cannot reach them [common/slpostingMT.cbl:L849-L891], so an empty "
        f"table here is a seeding or clear-bound regression, not an A-6 result."
    )

    # The internal posting table is the one the transfer rows are copied INTO
    # [irs/irs030.cbl:L1661-L1673]. If a re-write of the transfer file had succeeded on
    # one side, the two sides would have walked different data and this table would
    # diverge too, so it is asserted as the corroborating observable.
    posting = _table_diff(parity, "IRSPOSTING-REC")
    assert posting.is_empty, (
        f"`IRSPOSTING-REC` differs between the two sides, which corroborates a "
        f"divergence in what the transfer walk saw.\n{parity.diagnose()}"
    )


@pytest.mark.database
@pytest.mark.oracle
def test_a7_partial_date_component_derivation_is_dumped_as_stored(
    parity: object,
    harness: object,
    scenario_loader: object,
    withheld: object,
) -> None:
    """A-7: the three bridge-derived date components agree, partial zeros included.

    THE DEFECT. [common/irspostingMT.cbl:L982-L987], verbatim:

        982       if       Post-Date (1:2) numeric
        983                move     Post-Date (1:2) to HV-POST4-DAY.
        984       if       Post-Date (4:2) numeric
        985                move     Post-Date (4:2) to HV-POST4-MONTH.
        986       if       Post-Date (7:2) numeric
        987                move     Post-Date (7:2) to HV-POST4-YEAR.

    THREE INDEPENDENT GUARDS, NOT ONE COMPOUND TEST, and not one of them has an `else`.
    A PARTIAL derivation is therefore reachable - day and year set while month stays at
    zero, for instance - beside a fully intact raw date text in `POST4-DAT`, which is
    stored unconditionally at [common/irspostingMT.cbl:L969]. The row is internally
    inconsistent and nothing detects it. A failed guard leaves ZERO and never SQL
    `NULL`, because the host-variable group is initialised at
    [common/irspostingMT.cbl:L966] before the load - which is also why every column in
    the frozen schema can be declared `NOT NULL`.

    `POST4-DAY`, `POST4-MONTH` AND `POST4-YEAR` HAVE NO COUNTERPART IN ANY COPYBOOK.
    They exist only because the bridge derives them, which is the single entry that
    proves the Agent Action Plan's central sourcing decision: the bridge, and not the
    copybook, is the authoritative data dictionary. A migration driven from the
    copybooks alone would have omitted three columns of a posting table outright. The
    maintainer's own note sits immediately above, at
    [common/irspostingMT.cbl:L978-L980].

    THE ROW IS DUMPED AS STORED AND NEVER REPAIRED. The three components are ordinary
    integer columns, so normalisation's job 3 - the two- versus four-digit date text
    allow-list, which does cover `IRSPOSTING-REC.POST4-DAT` - must not touch them and
    must not complete a partial derivation. THIS TEST NEVER ASSERTS THAT A COMPONENT
    AGREES WITH THE TEXT. It asserts only that the two implementations stored the same
    thing, including where one component is zero beside intact text.

    THE POSTED DATE COMES FROM THE DATA, NOT FROM THE LINKAGE:
    `move WS-IRS-Post-Date to post-date` [irs/irs030.cbl:L1662]. So a partially
    derivable date reaches the bridge only if the seed put one in the transfer file.

    THE FIXTURE CARRIES THE PARTIAL ROW DELIBERATELY, AND ITS ABSENCE IS A FAILURE.
    `postings2irs.dat` seeds post number 5000 with `WS-IRS-Post-Date` `"XX/09/25"`,
    legend "Day position is not numeric": the day guard at
    [common/irspostingMT.cbl:L982-L983] cannot fire while the month and year guards can,
    so exactly one component stays at zero beside intact text. That row is REACHABLE -
    the missing-credit-account path at [irs/irs030.cbl:L1647-L1652] ends in
    `go to Input-Loop`, so post 4000's absent account 9999 skips ONE record and does not
    end the walk. An earlier form of this test SKIPPED when no partial row was observed,
    which turned both a fixture regression and a fixed anomaly into a green run; it now
    fails, and its message distinguishes the two causes.

    Args:
        parity: The completed, guarded ten-stage run.
        harness: The three harness modules, for reading the normalised dumps.
        scenario_loader: Loads the scenario definition, so the seeded partial date is
            named from the fixture rather than assumed.
    """
    # THE FIXTURE PRECONDITION, READ FROM THE DEFINITION. Asserted before the dumps, so
    # a fixture that stopped carrying a non-numeric date component is reported as such
    # rather than as an anomaly that stopped reproducing.
    seed_rows = scenario_loader(SCENARIO)["seed_records"]["postings2irs.dat"]
    seeded_partials = tuple(
        row
        for row in seed_rows
        if not all(
            str(row["WS-IRS-Post-Date"])[offset : offset + 2].isdigit()
            for offset in (0, 3, 6)
        )
    )
    assert seeded_partials, (
        f"{SCENARIO}'s transfer fixture carries no posting whose date text fails one of "
        f"the three bridge guards [common/irspostingMT.cbl:L982-L987], so A-7's PARTIAL "
        f"derivation cannot be exercised by this scenario at all. The fixture is "
        f"supposed to carry post 5000 with `WS-IRS-Post-Date` 'XX/09/25'. Dates "
        f"seeded: "
        f"{[str(row['WS-IRS-Post-Date']) for row in seed_rows]!r}. This is a FIXTURE "
        f"REGRESSION, not an anomaly that stopped reproducing."
    )

    posting = _table_diff(parity, "IRSPOSTING-REC")
    assert posting.is_empty, (
        f"A-7 IS NOT REPRODUCED: the two sides disagree about `IRSPOSTING-REC`.\n"
        f"{parity.diagnose()}"
    )

    derived = ("POST4-DAY", "POST4-MONTH", "POST4-YEAR")
    dumps = {
        side: _normalised(harness, parity.paths, side, "IRSPOSTING-REC")
        for side in ("cobol", "python")
    }
    indexed = {side: _rows_by_key(dump) for side, dump in dumps.items()}

    assert set(indexed["cobol"]) == set(indexed["python"]), (
        f"the two sides wrote different `IRSPOSTING-REC` keys.\n"
        f"  only in the COBOL dump:  "
        f"{sorted(set(indexed['cobol']) - set(indexed['python']), key=str)}\n"
        f"  only in the Python dump: "
        f"{sorted(set(indexed['python']) - set(indexed['cobol']), key=str)}"
    )

    partial_rows = 0
    for key in sorted(indexed["cobol"], key=str):
        observed = {}
        for side in ("cobol", "python"):
            dump = dumps[side]
            row = indexed[side][key]
            observed[side] = (
                _cell(dump, row, "POST4-DAT"),
                tuple(_cell(dump, row, column) for column in derived),
            )

        assert observed["cobol"] == observed["python"], (
            f"A-7 IS NOT REPRODUCED for `IRSPOSTING-REC` key {key!r}.\n"
            f"  COBOL  POST4-DAT={withheld(observed['cobol'][0], column='POST4-DAT')} "
            f"{list(derived)}={withheld(observed['cobol'][1])}\n"
            f"  Python POST4-DAT={withheld(observed['python'][0], column='POST4-DAT')} "
            f"{list(derived)}={withheld(observed['python'][1])}\n"
            f"\n"
            f"  THE THREE COMPONENTS ARE DERIVED BY THE BRIDGE UNDER THREE "
            f"INDEPENDENT GUARDS [common/irspostingMT.cbl:L982-L987], none of which "
            f"has an `else`, so a component whose two characters are not numeric MUST "
            f"remain zero while the raw text stands. If the migrated bridge now "
            f"completes a partial derivation - or refuses the row, or stores a null - "
            f"A-7 HAS BEEN FIXED, and a defect fixed is a failure (R-4)."
        )

        components = observed["cobol"][1]
        text = str(observed["cobol"][0])
        if text.strip() and any(int(str(value)) == 0 for value in components):
            partial_rows += 1

    # ⭐ A MISSING PARTIAL ROW IS A FAILURE, NOT A SKIP. This was a `pytest.skip` and
    # that was wrong: a skip is for something the ENVIRONMENT cannot provide, and this
    # is something the FIXTURE is built to provide. The parity loop above holds
    # trivially for rows whose three components all derived cleanly, so without a
    # partially-derived row present this test has confirmed nothing about A-7. The
    # fixture precondition at the top of this function has already established that the
    # SEED carries such a row - posting 5000, declared with
    # `WS-IRS-Post-Date: "XX/09/25"` for exactly this purpose, a day whose two
    # characters are not numeric so the first of the three bridge guards
    # [common/irspostingMT.cbl:L982] cannot fire while the raw text is still stored -
    # and the branch IS reached today, measured by running this scenario in the harness
    # container and observing that this test passes rather than skips. So reaching here
    # with none observed means the row did not survive the run in that state, which is
    # precisely the disappearance a skip would hide.
    assert partial_rows > 0, (
        f"{SCENARIO} produced no `IRSPOSTING-REC` row with a zero derived component "
        f"beside non-blank `POST4-DAT`, so A-7's PARTIAL derivation was NOT exercised - "
        f"and the parity assertions above are therefore vacuous with respect to the "
        f"anomaly, however many rows they compared "
        f"({len(indexed['cobol'])} posting row(s)).\n"
        f"\n"
        f"  THE FIXTURE IS BUILT TO PRODUCE ONE. `harness/scenarios/{SCENARIO}.yaml` "
        f"declares a transfer record whose `WS-IRS-Post-Date` begins `XX`, so the "
        f"DAY guard [common/irspostingMT.cbl:L982] cannot fire and `POST4-DAY` must "
        f"stay zero while `POST4-DAT` still carries the text. The seed's own "
        f"partially-derivable dates are "
        f"{[str(row['WS-IRS-Post-Date']) for row in seeded_partials]!r}, each failing "
        f"at least one of the three guards at [common/irspostingMT.cbl:L982-L987], and "
        f"post 4000's missing credit account only skips ONE record "
        f"([irs/irs030.cbl:L1647-L1652] ends in `go to Input-Loop`), so the row is "
        f"reachable.\n"
        f"\n"
        f"  SO ONE OF THREE THINGS HAPPENED, AND ALL THREE ARE FAILURES: both sides "
        f"completed the partial derivation, which means A-7 HAS BEEN FIXED and a defect "
        f"fixed is a failure (rule R-4); or the row was refused rather than stored, "
        f"which the guards' absent `else` forbids; or the transfer walk ended before "
        f"reaching post 5000, which makes the whole scenario shorter than it claims. "
        f"Read the normalised `IRSPOSTING-REC` dumps under "
        f"{parity.paths.run_logs.parent} to see which. Re-measure against the compiled "
        f"oracle before adjusting this assertion, and do NOT weaken it back to a skip: "
        f"a branch the fixture is supposed to reach and does not is a REGRESSION in the "
        f"fixture, not a property of the host."
    )


@pytest.mark.database
@pytest.mark.oracle
def test_irsdflt_rec_is_a_readonly_witness(
    parity: object,
    harness: object,
) -> None:
    """`IRSDFLT-REC` is READ ONLY: identical on both sides, and therefore to the seed.

    THE VERB CENSUS IS THE WHOLE ARGUMENT. In `Ledger-Postings-Add` the defaults
    handler is reached ONLY by `move 3 to file-function.` [irs/irs030.cbl:L1585]
    followed by `perform acasirsub3.` [irs/irs030.cbl:L1586] - a read of the default
    record and nothing else. There is NO facade verb of any kind against it: no write,
    no re-write, no delete, no open-output. So no code path on this route can change
    the table.

    WHY THAT MAKES IT A WITNESS. The defaults are what the section reads its two VAT
    control account codes from, at [irs/irs030.cbl:L1594] and
    [irs/irs030.cbl:L1604]. If they differed between the two runs, the two sides would
    have snapshotted DIFFERENT accounts and every A-5 assertion would be comparing
    unlike things. A silent difference here would therefore corrupt the conclusion
    rather than merely add a finding, which is why the table is on the affected-table
    list at all despite never being written.

    AND WHY "IDENTICAL TO THE SEED" FOLLOWS WITHOUT A THIRD DUMP. Stage 5 of the
    protocol re-seeds from the SAME scenario-owned fixture stage 1 used, and the
    re-seed asserts the same seed identity marker, so both runs began from the same
    rows. Nothing on this route can then write the table. Therefore two sides that
    agree with each other also agree with the seed, and a pre-run snapshot would add
    an oracle-side reset, dump and normalisation without adding evidence.

    THE LAYOUT, for the record: `01 Default-Record.`
    [copybooks/irswsdflt.cob:L8] over `03 Def-Group occurs 33.`
    [copybooks/irswsdflt.cob:L9] with `05 Def-Acs pic 9(5).`
    [copybooks/irswsdflt.cob:L10], `05 Def-Codes pic xx.`
    [copybooks/irswsdflt.cob:L11] and `05 Def-Vat pic x.`
    [copybooks/irswsdflt.cob:L12]; [copybooks/irswsdflt.cob:L6-L7] record the growth
    from 256 to 264 bytes that added default 33 for `irs030` itself.

    Args:
        parity: The completed, guarded ten-stage run.
        harness: The three harness modules, for reading the normalised dumps.
    """
    defaults = _table_diff(parity, "IRSDFLT-REC")

    assert defaults.missing_in_python == (), (
        f"`IRSDFLT-REC` rows {list(defaults.missing_in_python)} vanished on the Python "
        f"side. Nothing on this route can delete from a table reached only by "
        f"[irs/irs030.cbl:L1585-L1586], which is a READ."
    )
    assert defaults.missing_in_cobol == (), (
        f"`IRSDFLT-REC` gained rows {list(defaults.missing_in_cobol)} on the Python "
        f"side. `acasirsub3` is performed with ZERO facade verbs in this section, so "
        f"no insert is possible."
    )
    assert defaults.value_differences == (), (
        f"`IRSDFLT-REC` values differ between the two sides, which is impossible if "
        f"the table is read-only: the only access is the read at "
        f"[irs/irs030.cbl:L1585-L1586].\n{parity.diagnose()}"
    )
    assert defaults.is_empty, (
        f"`IRSDFLT-REC` differs between the two sides.\n{parity.diagnose()}"
    )

    # The two sides' dumps are compared WHOLE, not only through the comparison's
    # findings, so that a column-order or row-count difference is caught here as well.
    cobol = _normalised(harness, parity.paths, "cobol", "IRSDFLT-REC")
    python = _normalised(harness, parity.paths, "python", "IRSDFLT-REC")
    assert cobol == python, (
        f"the two `IRSDFLT-REC` dumps are not identical objects, even though the "
        f"table is read-only on this route.\n  COBOL  {cobol}\n  Python {python}"
    )
    assert cobol["row_count"] > 0, (
        f"HARNESS FAULT: `IRSDFLT-REC` is empty, so `def-acs (31)` "
        f"[irs/irs030.cbl:L1594] and `def-acs (32)` [irs/irs030.cbl:L1604] cannot be "
        f"read and the section leaves through abort 2 or abort 3 without ever "
        f"reaching `EOJ`. `irsdflt.dat` is one of the six seed files, loaded by "
        f"`irsdfltLD` [common/masterLD.sh:L100]."
    )


@pytest.mark.database
@pytest.mark.oracle
def test_dump_is_wellformed_on_both_sides(
    parity: object,
    harness: object,
    frozen_schema: object,
) -> None:
    """Every dump on both sides has the shape the protocol guarantees.

    THE SHAPE: exactly five keys in fixed insertion order - `table`, `primary_key`,
    `columns`, `row_count`, `rows` - AND NO OTHERS. No timestamp, no server version, no
    scenario name and no side; THE SIDE IS RECORDED IN THE PATH. `columns` is in schema
    ordinal order and is never sorted; `rows` is a list of lists in
    primary-key-ascending order, positionally aligned with `columns`; `row_count`
    equals the number of rows; DECIMAL values are canonical JSON STRINGS at the
    DECLARED SCALE - which is not uniformly two - never JSON numbers and never exponent
    notation; integers are JSON integers.

    WHY IT IS ASSERTED AT ALL. Every one of those failures is the comparison's exit 2,
    and exit 2 means THE COMPARISON COULD NOT BE PERFORMED. Asserting the shape
    directly is what turns "the diff was empty" into "the diff was empty AND the two
    dumps were things a diff can be taken of". The structural contract is delegated to
    the harness's own read-and-assert entry point, so it has exactly one definition in
    this repository (R-4).

    THE TWO SIGN-LEADING FAMILIES LIVE HERE AND ARE NOT TOUCHED. `PSIRSPOST-REC`
    carries `SIGN LEADING` display fields [copybooks/wspost-irs.cob:L21, L25] and
    `IRSPOSTING-REC` the `sign is leading` form [copybooks/irswspost.cob:L14, L19].
    Collapsing either into a plain numeric would change the on-the-wire values; the
    semantics layer owns them and this file only checks that what arrived is exact.

    NO BINARY FLOATING-POINT VALUE MAY APPEAR ANYWHERE IN A DUMP (R-2), and no null may
    either - which is exactly why the bridge initialises its host-variable group before
    every load, and why every column of the frozen schema can be `NOT NULL`.

    Args:
        parity: The completed, guarded ten-stage run.
        harness: The three harness modules, for the reader and the column order.
        frozen_schema: The parsed frozen schema, `{table: {column: ColumnType}}`, read
            from `mysql/ACASDB.sql` - read, never written (Agent Action Plan section
            0.8.1).
    """
    normalize = harness.normalize
    dump_tables = harness.dump_tables
    expected_keys = tuple(dump_tables.DUMP_KEYS)

    for table in parity.tables:
        for side in ("cobol", "python"):
            # `load_dump` IS the structural gate: five keys in order, the table in the
            # twenty-two-name allow-list, the primary key among the columns,
            # `row_count` equal to the row count, every row of the declared width, no
            # float, no null, no duplicate primary key. It raises on any of them.
            dump = _normalised(harness, parity.paths, side, table)

            assert tuple(dump) == expected_keys, (
                f"the {side} dump of `{table}` carries keys {list(dump)}; the "
                f"protocol guarantees exactly {list(expected_keys)}, in that order "
                f"and with no others. The side belongs in the PATH, never in the file."
            )
            assert dump["table"] == table, (
                f"the {side} dump read from `{table}.json` declares itself to be "
                f"{dump['table']!r}. A report that named the wrong table would be "
                f"worthless as evidence."
            )
            assert dump["primary_key"] == dump_tables.IN_SCOPE[table].primary_key, (
                f"the {side} dump of `{table}` says it is ordered by "
                f"{dump['primary_key']!r}; the frozen schema's single-column primary "
                f"key is {dump_tables.IN_SCOPE[table].primary_key!r}. Rows align by "
                f"that column's VALUE, so the alignment column is not negotiable."
            )
            assert dump["row_count"] == len(dump["rows"]), (
                f"the {side} dump of `{table}` reports row_count "
                f"{dump['row_count']} but carries {len(dump['rows'])} row(s). A dump "
                f"whose count disagrees with its rows is the comparison's exit 2."
            )

            columns = tuple(str(name) for name in dump["columns"])
            assert columns == normalize.schema_columns(frozen_schema, table), (
                f"the {side} dump of `{table}` lists its columns in an order the "
                f"frozen schema does not declare. ROWS ARE POSITIONAL, so a column "
                f"list in any other order has no meaningful alignment."
            )
            assert len(columns) == dump_tables.IN_SCOPE[table].column_count, (
                f"the {side} dump of `{table}` lists {len(columns)} column(s) and the "
                f"frozen schema declares "
                f"{dump_tables.IN_SCOPE[table].column_count} at "
                f"[mysql/ACASDB.sql:L{dump_tables.IN_SCOPE[table].schema_line}]. The "
                f"schema is FROZEN (R-3), so a disagreement means either the dump or "
                f"the checkout is wrong."
            )

            keys = [
                row[columns.index(dump["primary_key"])] for row in dump["rows"]
            ]
            # A TOTAL, TYPE-AWARE ASCENDING ORDER, matching the one the comparison
            # aligns on: an INTEGER key ascends NUMERICALLY, so 2 precedes 10, and a
            # `char` key ascends by code point. A single lexicographic test would
            # reject a correctly ordered integer dump outright.
            ordering = [
                (0, value, "") if isinstance(value, int) else (1, 0, str(value))
                for value in keys
            ]
            assert ordering == sorted(ordering), (
                f"the {side} dump of `{table}` is not in primary-key-ascending order: "
                f"{keys}. The order is `SELECT * FROM <table> ORDER BY <primary key>` "
                f"with no tie-breaking, because every in-scope table has a "
                f"single-column primary key and no secondary index."
            )
            assert len(set(keys)) == len(keys), (
                f"the {side} dump of `{table}` repeats a primary-key value. Rows "
                f"align by key VALUE, so a duplicate makes the alignment ambiguous "
                f"and is the comparison's exit 2."
            )

            for row in dump["rows"]:
                assert len(row) == len(columns), (
                    f"the {side} dump of `{table}` carries a ragged row of "
                    f"{len(row)} value(s) against {len(columns)} column(s). Rows are "
                    f"POSITIONAL, so a ragged row has no alignment at all."
                )
                for column, value in zip(columns, row):
                    declared = normalize.column_type(frozen_schema, table, column)
                    assert value is not None, (
                        f"the {side} dump of `{table}`.`{column}` carries a null. "
                        f"Every column of the frozen schema is NOT NULL, because the "
                        f"bridge initialises its host-variable group before each load "
                        f"so an unset field becomes zero or space."
                    )
                    assert not isinstance(value, bool), (
                        f"the {side} dump of `{table}`.`{column}` carries a boolean. "
                        f"The frozen schema declares no boolean column."
                    )
                    if declared.kind == normalize.KIND_DECIMAL:
                        assert isinstance(value, str), (
                            f"the {side} dump of `{table}`.`{column}` is "
                            f"{type(value).__name__} and must be a canonical decimal "
                            f"STRING: `{declared.sql_type}` "
                            f"[mysql/ACASDB.sql:L{declared.line}]. A JSON number here "
                            f"would be a binary floating-point value, which R-2 "
                            f"forbids outright."
                        )
                    elif declared.kind == normalize.KIND_INTEGER:
                        assert isinstance(value, int), (
                            f"the {side} dump of `{table}`.`{column}` is "
                            f"{type(value).__name__} and must be a JSON integer: "
                            f"`{declared.sql_type}` "
                            f"[mysql/ACASDB.sql:L{declared.line}]."
                        )
                    else:
                        assert isinstance(value, str), (
                            f"the {side} dump of `{table}`.`{column}` is "
                            f"{type(value).__name__} and must be a string: "
                            f"`{declared.sql_type}` "
                            f"[mysql/ACASDB.sql:L{declared.line}]."
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

    WHICH KEYS THIS ROUTE WRITES, AND WHY THIS SCENARIO NEEDS IT MOST. `irs_post` binds
    `irs_menu_state`, which carries NEITHER the defaults record nor the totals record,
    so `overrewrite` rewrites KEY 1 ALONE - the narrowest of the three shapes. That one
    key is the whole of this route's system persistence, and it is where the ADVANCED
    POSTING ALLOCATOR lands: `next-post` [copybooks/irswssystem.cob:L25] is incremented
    at [irs/irs030.cbl:L1671] and the entry point persists the advanced value. Without
    this assertion the allocator's advance is observable NOWHERE - the transfer table is
    cleared, `next-post` has no column of its own, and the diff cannot reach the row it
    is written into.

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
