"""PURCHASE CLEAN-BATCH STATE PARITY - and ANOMALY A-1's CONTROL.

THE HEADLINE OBLIGATION. This file drives the `clean_batch_pl` scenario through the
eight-stage parity protocol and asserts an EMPTY ordering-normalised diff between the
compiled COBOL oracle and the migrated Python cycle. Agent Action Plan section 0.8.5,
acceptance criterion 1: "the diff **must be empty**".

Scenario `clean_batch_pl`; subsystem `purchase`; operation `pl_order_post`, which is
`pl055` (order proof extract) followed by `pl060` (order posting). One menu selection
drives both programs, and unlike `gl051` and `irs030` NEITHER is migrated in part -
the whole of `pl055` and the whole of `pl060` are in scope.

THE SECOND, EQUALLY IMPORTANT OBLIGATION. Where `tests/scenarios/
test_clean_batch_post_sl.py` LOCKS anomaly A-1, this file locks the CORRECT sibling
behaviour, and the two together are what prove A-1 is an accident rather than an
idiom. Neither half may be normalised toward the other.

-------------------------------------------------------------------------------
THE INVERTED PREMISE, WHICH GOVERNS EVERY ASSERTION BELOW
-------------------------------------------------------------------------------

Agent Action Plan section 0.8.2, verbatim:

    "There is no test suite: compiled COBOL execution is the behavioral
    specification, defects included. A defect reproduced is correct; a defect fixed
    is a failure."

The corollary is that a test asserting CORRECT ACCOUNTING rather than OBSERVED
BEHAVIOUR is itself a defect. Nothing here recomputes a monetary figure, and nothing
here asserts that a ledger balances.

A WARNING SPECIFIC TO THIS FILE. Purchase happens to be the "correct" side of several
divergences, so there is a standing temptation to write assertions that read as
"Purchase does it properly". Every assertion below instead reads "THE COBOL AND
PYTHON SIDES AGREE". Agent Action Plan section 0.4.1.2 on `pl060` is explicit: "the
divergence from `sl060` is preserved, not normalised".

WHY THE EMPTY-DIFF ASSERTION IS TRUSTWORTHY. Agent Action Plan section 0.6.6: "a
non-empty diff is always a real behavioral difference and never an artefact of the
comparison." That is earned by the frozen schema rather than asserted - every one of
the twenty-two in-scope tables has a SINGLE-COLUMN primary key and ZERO secondary
indexes, and none carries a `TIMESTAMP`, an `AUTO_INCREMENT` or a column-level
`DEFAULT`. So the dump is `SELECT * FROM <table> ORDER BY <primary key>` with no
tie-breaking, no masking and no surrogate-key remapping.

-------------------------------------------------------------------------------
1. THE COBOL ROUTE, AND IT HAS NO ABORT GATE
-------------------------------------------------------------------------------

`[purchase/purchase.cbl:L752-L762]`, verbatim from the frozen source:

    L752  load08.
    L755  *>    move     "pl830" to WS-Called.   *> In case autogen is use
    L756  *>    perform  load000.
    L757  *>    if       ws-term-code not = zero
    L758  *>             go to display-menu.
    L759       move     "pl055" to ws-called.
    L760       perform  load000.
    L761       move     "pl060" to ws-called.       <- NO GATE BETWEEN THEM
    L762       go       to load000.

THREE DIVERGENCES FROM SALES IN FIVE LINES, ALL PRESERVED (rule R-4):

  (a) `pl830` IS COMMENTED OUT ENTIRELY, where Sales dispatches `sl830` live at
      `[sales/sales.cbl:L759]`. The maintainer's own changelog says why, at
      `[purchase/purchase.cbl:L112-L114]`: the four lines are remarked out "until
      the programs have been written". So on the Purchase route NO out-of-scope
      program runs on either side, and there is nothing to mitigate - which is
      itself the finding, because the Sales scenario must mitigate exactly that.
  (b) EVEN THE DEAD CODE DIVERGES: the commented-out Sales-equivalent line uses
      `perform load000` at `[purchase/purchase.cbl:L756]` where Sales uses
      `perform load00` at `[sales/sales.cbl:L760]`.
  (c) THERE IS NO `ws-term-code` GATE AT ALL between `pl055` and `pl060`. Sales has
      one at `[sales/sales.cbl:L765-L766]` and General has `if ws-term-code = 5` at
      `[general/general.cbl:L810-L811]`. Three programs, three different gate
      shapes - recorded as A-NEW-5, "Purchase has no abort gate at all", the
      sharpest R-4 obligation in the menu family. NONE OF THE THREE IS HARMONISED.

MENU-LETTER PROOF that this is `load08` and not some other paragraph:
`[purchase/purchase.cbl:L540]` displays `"(H)  Purchase Transactions Post"`, and H is
the eighth letter, so the computed `go to` selects `load08`.

-------------------------------------------------------------------------------
2. A-1's CONTROL - `pl060`'s TERMINATING PERIOD IS PRESENT
-------------------------------------------------------------------------------

`[purchase/pl060.cbl:L1027-L1033]`, verbatim, verified in this checkout:

    L1027       if       IRS-Both-Used OR G-L    *> THIS IS IN PURCHASE PL060
    L1028                move     RRN  to  postings.     *> Why ?
    L1029       perform  GL-Batch-Close.
    L1030       if       IRS-Used OR IRS-Both-Used
    L1031                perform SPL-Posting-Close.      *> ** THE PERIOD IS PRESENT **
    L1032       if       IRS-Both-Used or G-L
    L1033                perform GL-Posting-Close.
    L1035  main-exit.   exit section.

`[sales/sl060.cbl:L1172-L1178]`, verbatim, for contrast:

    L1172       if       IRS-Both-Used OR G-L    *> THIS IS IN PURCHASE PL060
    L1173                move     RRN  to  postings.     *> Why ?
    L1174       perform  GL-Batch-Close.
    L1175       if       IRS-Used OR IRS-Both-Used
    L1176                perform SPL-Posting-Close      *> ** NO PERIOD **
    L1177       if       IRS-Both-Used or G-L
    L1178                perform GL-Posting-Close.

Because `[sales/sl060.cbl:L1176]` carries no terminating period, the `if` at L1177
becomes NESTED INSIDE the preceding IRS test instead of being a sibling sentence. In
pure-GL mode - `G-L` true, `IRS-Used` and `IRS-Both-Used` both false - the outer
condition is false, the nested condition is never evaluated, and `GL-Posting-Close`
NEVER EXECUTES. The General Ledger posting file is left unclosed on the one
configuration where it is the only posting file in play.

IN `pl060` THE SAME STATEMENT IS A SIBLING, so `GL-Posting-Close` executes whenever
`IRS-Both-Used OR G-L` - INCLUDING pure-GL mode.

THE OTHER TWO SIBLINGS ALSO HAVE THE PERIOD: `[sales/sl100.cbl:L694]` and
`[purchase/pl100.cbl:L675]`. THREE OF FOUR HAVE IT; ONE DOES NOT. That
three-to-one split is the whole proof that A-1 is accidental, and this file is what
makes the proof reviewable: it captures the control half as compiled behaviour rather
than as an argument. All four sites carry the identical maintainer comment
`*> THIS IS IN PURCHASE PL060` - `[purchase/pl060.cbl:L1027]`,
`[sales/sl060.cbl:L1172]`, `[sales/sl100.cbl:L690]`, `[purchase/pl100.cbl:L671]` -
which is the copy-paste artefact recorded as A-NEW-10 and the most plausible
mechanism by which the period was lost.

NEITHER PROGRAM MAY BE NORMALISED TOWARD THE OTHER. Harmonising them would delete the
evidence, and under rule R-4 that is a failure and not an improvement.

-------------------------------------------------------------------------------
3. A-NEW-1 - THE LOST `invalid key` CLAUSE, WHICH KILLS THE SECOND PASS
-------------------------------------------------------------------------------

`[purchase/pl060.cbl:L809-L823]`, verbatim:

    L809  end-loop.
    L812       if       work-1 = zero
    L813          or    first-pass not = "Y"
    L814                go to  main-end.
    L815       move     "N"  to  first-pass.
    L818       set      fn-not-less-than to true.
    L819       perform  OTM5-Start.    *> start open-item-file-5 key not < oi5-key
    L820       go       to main-end.        <- UNCONDITIONAL
    L821       go       to  read-loop.      <- DEAD CODE, unreachable
    L823  main-end.

The `perform OTM5-Start` at L819 repositions the open-item cursor for a SECOND
apportionment pass over the credit notes, and the transfer back to `read-loop` that
would begin that pass sits at L821 - AFTER an unconditional `go to main-end` at L820.
So the second pass NEVER RUNS. Reproduced, not fixed (rule R-4). The end state the
dead pass would have left is unmeasured and is carried as `Q-CR-NOTES-SECOND-PASS`.

-------------------------------------------------------------------------------
4. `pl055` IS NOT A MIRROR OF `sl055` - FIVE MEASURED DIVERGENCES
-------------------------------------------------------------------------------

A reader arriving from the Sales scenario must not conclude that `pl055` is a
defective copy of `sl055`. It is a different program with the same job, and all five
differences are preserved.

  1. FOUR NEGATED FIELDS, NOT NINE. On a credit note `pl055` flips `oi-net`,
     `oi-carriage`, `oi-vat` and `oi-c-vat` and stops -
     `[purchase/pl055.cbl:L572-L575]`, under `if ih-type = 3` at L571. `sl055` flips
     NINE at `[sales/sl055.cbl:L658-L666]`, adding the two deduction fields,
     `oi-extra`, `oi-e-vat` and `oi-discount`.
  2. FOUR ADDENDS ON ONE LINE, NOT NINE OVER THREE.
     `[purchase/pl055.cbl:L580]` is `add ih-net ih-carriage ih-vat ih-c-vat giving
     ws-inv-amt.`, guarded by `if ih-type not = 1` at L579. `sl055`'s equivalent
     spans `[sales/sl055.cbl:L671-L673]` with nine terms. The two programs therefore
     compute DIFFERENT period totals from the same conceptual invoice, and that is
     correct.
  3. NO PROFORMA FILTER AND NO PENDING FILTER. `sl055` skips proformas with
     `if ih-type = 4` at `[sales/sl055.cbl:L430-L431]` and skips pending or non-"L"
     headers at `[sales/sl055.cbl:L433-L436]`. `pl055`'s header paragraph at
     `[purchase/pl055.cbl:L362]` has NEITHER, so a seeded `ih-type = 4` row would be
     EXTRACTED rather than ignored - which is why this scenario's fixture seeds none.
  4. ONE STATUS FIELD WRITTEN, NOT TWO. `[purchase/pl055.cbl:L586]` is
     `move "Z"  to  ih-status.   *> 07/01/18 was "z"` followed by
     `write open-item-record-4.` at `[purchase/pl055.cbl:L587]` - and OTM4 is a FLAT
     WORK FILE, not one of the twenty-two tables. `sl055` writes both `ih-status`
     AND `ih-status-A` at `[sales/sl055.cbl:L679-L680]`.
  5. `[purchase/pl055.cbl:L308]` tests `if FS-Reply not = zero` and L309 leaves the
     read loop for ANY non-zero reply - not only for end-of-file.

Also on this route: the two value-analysis sign flips at `[purchase/pl055.cbl:L376]`
(VAT total) and `[purchase/pl055.cbl:L387]` (carriage total);
`[purchase/pl055.cbl:L250-L254]` tolerating `ws-env-lines < 24`;
`perform Value-Open.` at `[purchase/pl055.cbl:L261]`; `move 1 to File-Key-No.` at
`[purchase/pl055.cbl:L291]`; `initialise OI-Header` at `[purchase/pl055.cbl:L547]`
with NO `WITH FILLER`; and `va-system = "P"` at `[purchase/pl055.cbl:L403]`.

-------------------------------------------------------------------------------
5. THE ROUTE'S VERB CENSUS, WHICH IS WHAT JUSTIFIES THE TABLE LIST
-------------------------------------------------------------------------------

`pl055` issues `Analysis-Write`, `PInvoice-Rewrite`, `Value-Write` and
`Value-Rewrite` - and NO `Value-Open-Output`, where `sl055` has one as a recovery.

`pl060` issues `GL-Batch-Write`, `GL-Posting-Write`, `OTM5-Write`, `OTM5-Rewrite`
twice, `SPL-Posting-Write`, `Purch-Write`, `Purch-Rewrite`, three `*-Open-Output`
recoveries and `SPL-Posting-Open-Extend` - and ZERO `Value-*` verbs of any kind.

FOUR CONSEQUENCES, EACH OF WHICH A WELL-MEANING TIDY-UP WOULD DESTROY:

  * `VALUEANAL-REC` IS WRITTEN ON THE PURCHASE SIDE BY `pl055` ONLY. `pl060` issues
    not an open, not a read, not a rewrite. Its Sales counterpart `sl060` issues
    `Value-Read-Indexed` and `Value-Rewrite` twice each.
  * `PSIRSPOST-REC` IS AN UNCHANGED WITNESS HERE. Its only writer on this route is
    `SPL-Posting-Write` at `[purchase/pl060.cbl:L997]`, inside the fan-out
    conditional opening at `[purchase/pl060.cbl:L982]`. With the fan-out switch
    pinned to a space that guard is false and no row is written. It is listed anyway,
    because PROVING it unchanged is the point - A-1's evidence depends on the IRS
    branches being off, and a table left out of the comparison cannot prove anything
    about itself.
  * `GLLEDGER-REC` IS ABSENT, and its absence is measured rather than assumed:
    neither program issues a single `GL-Nominal-*` verb, so the nominal ledger is
    never read or written on this route. Only the General Ledger scenarios reach it.
  * THERE IS NO `GL-Batch-Open-Output`. The batch-file recovery open that would have
    provided one is COMMENTED OUT at `[purchase/pl060.cbl:L881-L883]`, so a failed
    batch open is not recovered from here at all.

-------------------------------------------------------------------------------
6. THE PURCHASE MOVING-AVERAGE MIRRORS - A-8, A-9 and A-10's PURCHASE HALF
-------------------------------------------------------------------------------

`[purchase/pl060.cbl:L740-L751]`, `purch-comp section.`:

    L743       if       purch-activety not = zero
    L744          and   purch-average not = zero
    L745                multiply purch-activety by purch-average giving work-2
    L746       else
    L747                move zero to work-2
    L748       end-if
    L749       add      1 to purch-activety.        <- THE COUNTER IS INCREMENTED
    L750       add      work-goods to work-2.
    L751       divide   purch-activety into work-2 giving purch-average.

`[purchase/pl060.cbl:L755-L766]`, `credit-comp section.`:

    L758       if       purch-activety not = zero
    L759         and    purch-average not = zero
    L760                multiply purch-activety by purch-average giving work-2
    L761       else
    L762                move zero to work-2
    L763       end-if
    L764       if       work-2 not = zero            <- AN EXTRA GUARD (A-10)
    L765                add work-goods to work-2
    L766                divide purch-activety into work-2 giving purch-average.
                                        <- AND NO `add 1 to purch-activety` ANYWHERE

`credit-comp` NEVER INCREMENTS ITS ACTIVITY COUNTER - that is the A-9 mirror, and it
silently drops the first credit note for a supplier. Its extra guard at L764 is the
A-10 mirror: three instances of one idiom, three different guards, and the Sales cash
path at `[sales/sl100.cbl:L506]` additionally INVERTS the divide operand order.
`cr-notes section.` is at `[purchase/pl060.cbl:L770]`.

A-8's DOUBLE TRUNCATION IS WHY THE FIELD TYPES MATTER. `Purch-Activety` and
`Purch-Average` are declared `binary-long` at `[copybooks/wspl.cob:L35]` and
`[copybooks/wspl.cob:L38]`, and land as `PURCH-ACTIVETY int(8) unsigned` and
`PURCH-AVERAGE int(8) unsigned`. They are INTEGERS, so the divide at L751 and L766
truncates twice - once into the accumulator and once on the store. `PULEDGER-REC`
therefore mixes `Decimal` money columns with `int` statistics columns, and the split
must not be blurred. Nothing in this file recomputes either value: the arithmetic tier
owns that, and here the only question is whether the two SIDES agree.

CONSEQUENCE FOR THE SEED: the fixture must hold TWO INVOICES PLUS ONE CREDIT NOTE FOR
THE SAME SUPPLIER, so `purch-comp` fires twice from a non-zero accumulator and
`credit-comp` fires once with a counter that was never incremented for it.

`pl060`'s section inventory, for the paragraph-to-function mapping (rule R-5):
`init01` 347, `cr-swop` 653, `new-heading` 691, `headings` 717, `purch-comp` 740,
`credit-comp` 755, `cr-notes` 770, `apportion` 831, `BL-Open` 877, `BL-Write` 926,
`BL-Close` 1013, `Evaluate-Message` 1037, `zz050` 1046, `zz060` 1081, `zz070` 1116 and
the date-module wrapper 1146. Its three sign flips are at
`[purchase/pl060.cbl:L507]`, `[purchase/pl060.cbl:L683]` and
`[purchase/pl060.cbl:L783]`. `pl055`'s inventory: `mainline` 246, `create` 441,
`store-specials` 503, `extract` 538, `zz070-Convert-Date` 599, `a01-Eval-Status` 629.

-------------------------------------------------------------------------------
7. THE THREE PERIOD-TOTAL WRITES ON THIS ROUTE
-------------------------------------------------------------------------------

Agent Action Plan section 0.6.4 names NINE period-total write sites across the Sales
and Purchase programs and calls them "the sole writers of the totals record". THREE
of the nine are on this route, which is why `SYSTOT-REC` is compared here:

    `[purchase/pl055.cbl:L582]`  add ws-inv-amt to pl-invoices-this-month.
                                 under `if ih-type = 2` at L581
    `[purchase/pl055.cbl:L584]`  add ws-inv-amt to pl-credit-notes-this-month.
                                 under `if ih-type = 3` at L583
    `[purchase/pl060.cbl:L628]`  add work-b to pl-cn-unappl-this-month.

THE THIRD ONE IS UNCONDITIONAL. It sits OUTSIDE the print guard
`if FS-Cobol-Files-Used and File-28-Exists` that opens at `[purchase/pl060.cbl:L623]`
and closes with the `write print-record` at `[purchase/pl060.cbl:L626]`. A reader who
assumed the add was part of the print block would predict a zero here and be wrong.

THE THREE RECEIVING FIELDS, and A-20 sitting two lines below them. All three live in
the `Purchase-Ledger-Data` group at `[copybooks/wssys4.cob:L20]` -
`pl-invoices-this-month` at `[copybooks/wssys4.cob:L23]`,
`pl-credit-notes-this-month` at `[copybooks/wssys4.cob:L24]` and
`pl-cn-unappl-this-month` at `[copybooks/wssys4.cob:L27]`, each
`pic s9(8)v99` under a group-level `comp-3`, landing as `decimal(10,2)`. IMMEDIATELY
AFTER THEM, STILL INSIDE THE PURCHASE GROUP, ARE `sl4-spare3` AND `sl4-spare4` AT
`[copybooks/wssys4.cob:L29-L30]` - two spare fields carrying the SALES prefix inside
the PURCHASE group, which is anomaly A-20, and it is visible in this very capture as
`SYSTOT-REC.SL4-SPARE3` and `SYSTOT-REC.SL4-SPARE4`. The misnaming is REPRODUCED, not
corrected: renaming them would change a column name, which the frozen schema forbids
outright.

-------------------------------------------------------------------------------
8. A-17's MIRROR, AND WHY ITS EFFECT IS DEFERRED
-------------------------------------------------------------------------------

`[purchase/pl060.cbl:L1028]` is `move RRN to postings.  *> Why ?` - the maintainer's
own question mark, in all four Sales and Purchase posting programs, each carrying it on
the line after the identical wrong-program comment: `[purchase/pl060.cbl:L1028]`,
`[sales/sl060.cbl:L1173]`, `[sales/sl100.cbl:L691]` and `[purchase/pl100.cbl:L672]`.
`postings` is declared `05  Postings   binary-short.` at
`[copybooks/wssystem.cob:L184]`.

THE WRITE IS IN `BL-Close` AND EVERY READ IS IN A `BL-Open`, WHICH IS WHY THE EFFECT
IS DEFERRED. `pl060` reads it at `[purchase/pl060.cbl:L905]` as
`add postings 1 giving batch-start.`, and `pl100` reads it the same way at
`[purchase/pl100.cbl:L564]`. Both reads happen when a batch is OPENED and the single
write happens when one is CLOSED, so within this run the value read is the seeded one
and the value written is observable only in `GLBATCH-REC.BATCH-START` ON A LATER RUN.
The statement is reproduced; its stored effect once the source counter has passed the
receiving field's picture is unmeasured and is carried as `Q-A17-POSTINGS-EFFECT`.

-------------------------------------------------------------------------------
9. TWO LEXICAL DIVERGENCES IN `purchase.cbl`, RECORDED UNDER RULE R-4
-------------------------------------------------------------------------------

  * `[purchase/purchase.cbl:L681]` lists `"pl090"` TWICE, both on the one line, in
    `load00`'s whitelist - alongside a `"pl100"` entry that can never be reached,
    because `pl100` is dispatched through `load000` from `load12.` at
    `[purchase/purchase.cbl:L789-L790]`. Wrong in two ways at once, and neither is
    cleaned up.
  * `[purchase/purchase.cbl:L644]` and `[purchase/purchase.cbl:L649]` are MISSING
    their terminating periods, where the Sales equivalents at
    `[sales/sales.cbl:L651]` and `[sales/sales.cbl:L656]` have them. Harmless here,
    because both are simple statements in sequence rather than conditionals - which
    is precisely what makes A-1 different, and worth stating so the two are not
    conflated.

-------------------------------------------------------------------------------
10. PURE GENERAL LEDGER MODE IS TWO SEEDED FIELDS, NOT ONE
-------------------------------------------------------------------------------

THIS IS THE MOST EXPENSIVE THING TO GET WRONG IN THIS SCENARIO, so it is stated
separately from the preconditions it drives.

THE FIRST FIELD is the fan-out switch, `[copybooks/wssystem.cob:L179-L181]` verbatim:

    L179         05  IRS-Instead     pic x.
    L180             88  IRS-Used                   value "Y".
    L181             88  IRS-Both-Used              value "B".   *> 26/11/16

THREE states, and THE THIRD - a space - HAS NO CONDITION NAME AT ALL: both predicates
are simply false for it, which is General Ledger only. There is no `N`. `pl060` tests
the switch at `[purchase/pl060.cbl:L907]`, `[purchase/pl060.cbl:L982]`,
`[purchase/pl060.cbl:L1027]`, `[purchase/pl060.cbl:L1030]` and
`[purchase/pl060.cbl:L1032]`; `pl055` does not test it at all.

THE SECOND FIELD IS NOT ON THAT SWITCH, and reading only the fan-out tests would miss
it. `G-L` is a condition name on the INSTALLED-LEDGER LEVEL BYTE -
`88  G-L  value 1.` at `[copybooks/wssystem.cob:L85]`, over
`07  Level-1  pic 9.` at `[copybooks/wssystem.cob:L84]`, inside the `Level` group at
`[copybooks/wssystem.cob:L83-L96]`. Pure General Ledger mode is therefore
`IRS-Instead` equal to a space AND `Level-1` equal to one.

ON THIS ROUTE THE SECOND FIELD IS THE MORE LOAD-BEARING OF THE TWO, because `pl060`
gates its ENTIRE General Ledger side on `G-L` alone, at three unconditional-looking
sites:

    `[purchase/pl060.cbl:L405-L406]`   if G-L / perform BL-Open.
    `[purchase/pl060.cbl:L474-L475]`   if G-L / perform BL-Write.
    `[purchase/pl060.cbl:L573-L574]`   if G-L / perform BL-Close.

With `Level-1` anything other than one, `G-L` is FALSE, none of those three sections
is entered, and `BL-Close` - the section that CONTAINS A-1, at
`[purchase/pl060.cbl:L1013]` - is never reached. `GLBATCH-REC` and `GLPOSTING-REC`
would then be empty on BOTH sides, the diff would be empty FOR THE WRONG REASON, and
A-1 would be UNOBSERVABLE. That is a silent false pass of exactly the same class as
the `file_system_used` trap, and NEITHER RUNNER ASSERTS IT. It is closed by the seed
contract and by the precondition test below, and nowhere else. The maintainer plainly
found the gate awkward: a bypass for it survives, commented out, at
`[purchase/pl060.cbl:L644-L646]` - and being commented out it is not code, so nothing
reproduces it.

-------------------------------------------------------------------------------
11. THE EIGHT-STAGE PROTOCOL, AND THE THREE-WAY EXIT CONTRACT
-------------------------------------------------------------------------------

    1  seed.sh                 5  reset_db.sh
    2  run_cobol_scenario.sh   6  run_python_scenario.sh
    3  dump --side cobol       7  dump --side python
    4  normalize.py            8  diff_states.py

Driven through ONE helper, `protocol.run_scenario_parity`, which is what Agent Action
Plan section 0.4.3 exposed it for: "no test reimplements the comparison protocol".
Nothing below writes its own comparison.

THE THREE-WAY EXIT CONTRACT:

    0  the two trees are IDENTICAL, and stdout is EMPTY - zero bytes, not a banner
    1  a REAL BEHAVIOURAL DIFFERENCE, with a deterministic report      -> FAILURE
    2  THE COMPARISON COULD NOT BE PERFORMED - a missing tree, a missing table file,
       a malformed dump, a shape mismatch, a `float`, a duplicate primary key, a wrong
       key order, `row_count != len(rows)`, a ragged row or a `null`   -> ERROR

Exit 2 is NEVER a pass. `tests/conftest.py`'s `diff` maps it to `HarnessFaultError`,
which surfaces as a test ERROR rather than a failure, because "a test that treats
'could not compare' as 'no differences' is the single worst bug available in this
tree" - and rule R-6 makes an empty diff the pass condition ONLY WHEN A COMPARISON
ACTUALLY HAPPENED.

THE COMPARISON IS EXACT. No tolerance, no epsilon, no closeness helper, no
approximate-equality helper, no case- or whitespace-insensitive comparison and no
numeric coercion: `1` against `"1"` IS a difference. Rows align by PRIMARY-KEY VALUE
and never by position, and the two labels are `cobol` and `python`, never left and
right.

ALWAYS DUMP, THEN DECIDE THE STATUS. Agent Action Plan section 0.6.5: "The database
effect is therefore *the absence* of everything the later phases would have written."
ABSENCE IS EVIDENCE, so stages 3 and 4 are taken WHATEVER stage 2 returned and stages
7 and 7b whatever stage 6 returned. The dump is never short-circuited on a non-zero
runner status.

THREE EXIT CATEGORIES ARE KEPT DISTINCT and are never conflated: SUCCESS; a
BEHAVIOURAL DIFFERENCE, for which the dump is still taken because the state is exactly
the state the specification says it should be in; and a HARNESS FAULT - `argparse`
exit 2, a missing promoted flag, an unreachable database, malformed YAML, or two
disagreeing seed fingerprints - for which there is no evidence at all.

A NOTE PECULIAR TO THIS ROUTE. Because `load08` has NO GATE, an abort in `pl055` would
NOT stop `pl060` from running. Combined with the proof that term code 8 is unreachable
under `file_system_used: 1` - the raise at `[purchase/pl055.cbl:L286]` sits inside a
block whose outermost guard is `if FS-Cobol-Files-Used` at
`[purchase/pl055.cbl:L266]`, closed by the two `end-if`s at
`[purchase/pl055.cbl:L289]` and `[purchase/pl055.cbl:L290]` - the scenario's declared
status of zero is PROVABLE rather than optimistic. The genuine Sales-versus-Purchase
divergence lives in the 1..7 BAND: Sales returns to the menu for any non-zero code up
to seven, whereas Purchase would PROCEED TO `pl060`. That band is currently
unobservable, because the census finds no in-scope program that sets a code in it -
`[general/gl070.cbl:L289]` sets 5, `[sales/sl055.cbl:L344]` sets 8 and
`[purchase/pl055.cbl:L286]` sets 8, and `pl060` sets nothing - but it must still be
reproduced exactly, and it is carried as `Q-CLI-TERMCODE-1-7`.

-------------------------------------------------------------------------------
12. BOUNDING, NEVER IGNORING
-------------------------------------------------------------------------------

THERE IS NO IGNORE-LIST, NO TOLERANCE-LIST AND NO "KNOWN DIFFERENCE" ALLOWANCE
anywhere in this file or in the diff path it drives. Bounding is done by the
scenario's own `affected_tables` list, and by nothing else.

TWO STRUCTURAL ASYMMETRIES exist between the two sides, and neither is a migration
defect:

  1. THE MENU SHELL'S EXIT PATH. `[purchase/purchase.cbl:L621-L650]` is `overrewrite`,
     and it persists KEYS 1 AND 4 ONLY - NEVER KEY 2:

         L621  overrewrite.                              *> save to RDB or file.
         L622       if       File-System-Used NOT = zero  *> Force RDB processing
         L624                move     1 to File-Key-No
         L629                move     4 to File-Key-No    <- KEY 4 ONLY, NO KEY 2

     Contrast `[general/general.cbl:L656-L691]`, which writes keys 1, 2 AND 4; Sales
     behaves like Purchase here, at `[sales/sales.cbl:L636]`. THAT is why
     `SYSDEFLT-REC` appears on NO scenario's affected-table list. A further
     Purchase-only divergence: `[purchase/purchase.cbl:L703-L704]` uses
     `go to overrewrite` where `[sales/sales.cbl:L710-L712]` uses
     `perform overrewrite` followed by `goback`. Preserved.
     `load000` performs `overrewrite` effectively unconditionally, because `< 8` at
     `[purchase/purchase.cbl:L701-L702]` and `> 7` at
     `[purchase/purchase.cbl:L703-L704]` are exhaustive over `WS-Term-Code pic 99`
     `[copybooks/wscall.cob:L10]`. The Python command line has no menu. A census
     across all twelve in-scope programs finds ZERO `System-*` facade verbs, so
     `SYSTEM-REC`, `SYSDEFLT-REC` and `SYSFINAL-REC` are on no list at all, while
     `SYSTOT-REC` earns its place because three statements on this route do change it.
     The residual question is `Q-CLI-OVERREWRITE`, and it is settled in
     `acas_posting/cli/pl_order_post.py` by REPRODUCING the paragraph - never by an
     ignore-list, which would convert a real behavioural difference into a silent
     pass.
  2. THE AUTOGEN ASYMMETRY. On the Sales side `sl830` runs only on the COBOL side; on
     the Purchase side `pl830` is commented out entirely. Either way the four autogen
     tables - `SAAUTOGEN-REC`, `SAAUTOGEN-LINES-REC`, `PUAUTOGEN-REC` and
     `PUAUTOGEN-LINES-REC` - are NEVER SEEDED AND NEVER LISTED, and BOTH RUNNERS
     assert after the run that all four are still empty. That assertion lives in the
     runners; this file asserts only the list-level fact.

-------------------------------------------------------------------------------
13. NORMALISATION DOES EXACTLY THREE THINGS, AND THERE IS NO FOURTH
-------------------------------------------------------------------------------

Delegated ENTIRELY to `harness/normalize.py`. Nothing here reimplements or extends it.

  1. TRAILING SPACES IN FIXED-CHARACTER COLUMNS - `rstrip(" ")`, TRAILING ONLY,
     because a COBOL alphanumeric `MOVE` is left-justified with right padding, so
     LEADING SPACES ARE CONTENT. ASCII `U+0020` only, applied by declared type
     including `char(1)`. Motivated by A-12, the width drift `pic x(24)` at
     `[copybooks/wsledger.cob:L27]` to `PIC X(32)` at `[common/nominalMT.cbl:L299]` to
     `char(32)` at `[mysql/ACASDB.sql:L127]`. The schema has 238 `char(` columns and
     ZERO `varchar(`.
  2. DECIMAL SCALE RENDERING AT THE DECLARED SCALE - and it is NOT uniformly 2. The
     census is 68 x `(9,2)`, 57 x `(10,2)`, 17 x `(4,2)`, 12 x `(5,2)`, 4 x `(14,2)`,
     2 x `(2,0)`, 2 x `(14,4)` plus singletons. A value implying more places RAISES
     rather than rounds, because rounding there would hide a real finding.
  3. TWO- VERSUS FOUR-DIGIT DATE TEXT FORMS, under an EXPLICIT FIVE-COLUMN ALLOW-LIST
     only: `GLPOSTING-REC.POST-DAT`, `IRSPOSTING-REC.POST4-DAT`,
     `PSIRSPOST-REC.IRS-POST-DAT`, `SYSTEM-REC.STATS-DATE-PERIOD` and
     `SALEDGER-REC.SALES-STATS-DATE`.
     `char(8)` DOES NOT IMPLY DATE. `PUITM5-REC.OI5-BATCH` is a BATCH REFERENCE and is
     EXCLUDED - `[copybooks/slwsoi.cob:L16-L18]` declares `03 OI-Batch comp.` over
     `05 OI-B-Nos pic 9(5).` and `05 OI-B-Item pic 999.`, and the schema labels its two
     component columns `COMMENT 'Batch content'`. `PULEDGER-REC.PURCH-EXT` is
     similarly excluded as the supplier-key extension `[copybooks/wspl.cob:L27]`. BOTH
     OF THOSE TABLES ARE DUMPED BY THIS SCENARIO, so the exclusions matter here
     concretely. Most in-scope "dates" are BINARY DAY-NUMBER INTEGERS and job 3 must
     not touch them at all.

`PULEDGER-REC` has 29 columns, `PUITM5-REC` 29, `PUINVOICE-REC` 30 and
`PUINV-LINES-REC` 14. Like the Sales ledger, `PULEDGER-REC` mixes `Decimal` money
columns with `int` statistics columns; that split is what makes the integer truncation
in `purch-comp` and `credit-comp` reproducible, and it is not blurred.

-------------------------------------------------------------------------------
14. THE FIVE REJECTION CLASSES - THIS SCENARIO EXERCISES NONE OF THEM
-------------------------------------------------------------------------------

Agent Action Plan section 0.8.1: "a single generic rejection path would fail this
directive." The five classes differ precisely in their DATABASE EFFECT, so they are
recorded here rather than collapsed, and this scenario - the clean happy path -
deliberately triggers none:

  1. CLEAN REJECTION, NO DATABASE EFFECT - `gl072` skips a posting whose batch number
     is non-numeric `[general/gl072.cbl:L291-L292]` and a record whose handler
     returned a specific error `[general/gl072.cbl:L306-L307]`, both entirely silently.
  2. RUN-ABORTING - a control-total mismatch leaves the batch open; the database
     effect is THE ABSENCE of everything the later phases would have written. A
     Purchase batch cannot reach this class: `pl060` accumulates the input and the
     actual figures from the SAME posting amounts, two statements apart at
     `[purchase/pl060.cbl:L973-L976]`, so the pair cannot disagree by construction.
     The control-total gate is a General Ledger matter, tested against the entered
     gross at `[general/gl051.cbl:L1109-L1118]`.
  3. PARTIAL DATABASE EFFECT - the half-posted double entry at
     `[irs/irs030.cbl:L1635-L1652]`, and the lost update from pre-loop snapshots at
     `[irs/irs030.cbl:L1602]` and `[irs/irs030.cbl:L1612]` rewritten at end of job at
     `[irs/irs030.cbl:L1704-L1708]`.
  4. FILE-ABANDONING - a posting-record write failure jumps straight to end of job at
     `[irs/irs030.cbl:L1673-L1678]`, so the partial state is COMMITTED, NOT ROLLED
     BACK.
  5. PERMANENTLY FAILING FACADE VERB - the transfer-file handler rejects four of its
     published verbs unconditionally at entry `[common/acas008.cbl:L299-L307]`.

-------------------------------------------------------------------------------
15. SEEDING AND SCHEMA CONSTRAINTS (rule R-3) - DOCUMENTED, NOT IMPLEMENTED
-------------------------------------------------------------------------------

NO DDL OF ANY KIND. `mysql/ACASDB.sql` is applied VERBATIM; the frozen file already
carries all 33 `DROP TABLE IF EXISTS`, so re-applying it IS the drop-and-recreate, and
the database name must be given on the client command line because the file has no
`USE`.

AUTOCOMMIT IS OFF DURING SEEDING, asserted globally and per session, because all 28
frozen loaders carry the banner at `[common/glbatchLD.cbl:L9-L12]` requiring it. The
seeded state depends on the loaders' commit boundaries.

`common/masterLD.sh` IS NEVER INVOKED, for three independent reasons: its own header
at `[common/masterLD.sh:L4]` reads "THIS SCRIPT HAS NOT YET BEEN TESTED"; all 24
loader lines at `[common/masterLD.sh:L93-L116]` omit the `;` before `fi`, so `bash -n`
rejects a 123-line file at line 124; and it ends by paging `SYS-DISPLAY.log` through
`less`, which would block a non-interactive run forever. It is FROZEN AND NOT FIXED.
`harness/seed.sh` reproduces its documented per-file contract instead
`[common/masterLD.sh:L44-L115]`.

R-4 ITEMS IN THE SEEDING PATH, PRESERVED RATHER THAN FIXED: the `dfltLD`
strict-versus-lenient exit asymmetry, where `[common/masterLD.sh:L83]` tests
`if [ $rc != 0 ]` against the `-gt 63` tolerance at `[common/masterLD.sh:L37-L39]`
(128 means the RDBMS parameters are unset, 64 the database flag is unset, 16 a write
error); the charset caveat, where `[mysql/ACASDB.sql:L16]` sets `NAMES utf8mb4` while
all 33 tables declare `DEFAULT CHARSET=utf8mb3`; and the `tinyint(1) unsigned`
display-width quirk.

STRICTLY SEQUENTIAL (rule R-3). No parallel test-distribution plugin is used, no
process is forked and no ordering is randomised: parallel scenario runs against one
shared MariaDB would break the seed / run / dump / reset / run / dump / diff protocol
outright, and the COBOL being reproduced is single-threaded.

-------------------------------------------------------------------------------
16. THE RULES THIS FILE IS HELD TO
-------------------------------------------------------------------------------

THERE IS NO USER RULES DOCUMENT FOR THIS PROJECT. `review_rules` reports, exactly,
"No user rules provided." There is no on-disk rules file to consult and no reader
should look for one. The six binding rules R-1 to R-6 live in the Agent Action Plan
itself, section 0.7.2, and their exact wording is retrievable from the requirements
via `review_prompt` - never via `review_rules`. Where they are silent,
enterprise-standard best practice applies, and NONE HAS BEEN INVENTED TO FILL A GAP.

  R-1  NO COBOL AT RUNTIME. This file imports `pytest` AND NOTHING ELSE. It never
       imports `harness` in any form - `harness/` has no `__init__.py` and
       `pyproject.toml`'s package allow-list excludes it, which is where R-1 stops
       being a promise and becomes a fact - and it never loads a harness path itself:
       the three harness modules arrive through `tests/conftest.py`'s explicit-path
       loaders, exposed as the `harness` fixture. It never invokes `cobc` or
       `cobcrun`, spawns no child process of its own and uses no foreign-function
       interface. The compiled oracle is reached only out of process, by the harness
       shell scripts that `tests/conftest.py` drives - which Agent Action Plan section
       0.7.2 licenses precisely: the oracle "is consumed only by `tests/scenarios/*`
       and `tests/determinism/*` as an out-of-process comparison".
       It also never imports `acas_posting.cli.pl_order_post`, never executes an
       entry point as a script, never constructs a command line or an `argv` list,
       and never hard-codes an option spelling. The promoted-option spellings are
       deliberately left unfixed in the entry-point specifications, and
       `harness/run_python_scenario.sh` owns the flag probe and fails HARNESS-FAULT if
       a required flag is absent. On this route the prohibition is easy to honour
       because `pl_order_post` PROMOTES NOTHING - `pl060`'s `acpt-xrply.` at
       `[purchase/pl060.cbl:L362]` is commented out line by line at
       `[purchase/pl060.cbl:L363-L370]`, so there is no prompt to promote and no
       default to preserve. What survives it is unconditional, at
       `[purchase/pl060.cbl:L373-L375]`.
  R-2  ZERO BINARY FLOATING POINT. There is no binary-radix numeric literal, no
       approximate-equality helper from the test runner, no closeness helper from the
       standard library, no tolerance, no epsilon, and no dataframe or array library
       anywhere below. Every value this file handles is a `str`, an `int` or a
       `bool`, and the comparison it drives refuses a `float` in a dump outright with
       exit 2.
  R-3  NO NEW VALIDATIONS, FIELDS OR SCHEMA CHANGES, AND NO CONCURRENCY. This file
       emits no DDL, adds no check the COBOL lacks, judges nothing the scenario
       declares, and is strictly sequential. It also creates no `__init__.py`, no
       nested `conftest.py` and no helper module: everything shared comes from
       `tests/conftest.py`, through fixtures.
  R-4  LEGACY ANOMALIES REPRODUCED, NEVER FIXED. Every anomaly named above is
       asserted as "THE TWO SIDES AGREE" and never as "Purchase is correct". No
       assertion recomputes a figure, tidies a value, coalesces a null or normalises
       one program toward its sibling.
  R-5  FULL TRACEABILITY. Every anomaly carries its identifier - A-1 as the control,
       A-NEW-1, the A-8, A-9 and A-10 mirrors, A-12, A-17, A-20, A-NEW-5 and A-NEW-10
       - and every claim carries its `[path:Lnnn]` locator, both in this docstring and
       at each assertion site. The register is `docs/migration/anomaly-log.md`, whose
       identifiers are externally imposed and are never renumbered. `pytest-cov` is
       TRACEABILITY EVIDENCE AND NOT A QUALITY GATE: no coverage failure threshold is
       configured here or in `pyproject.toml`, because a coverage number never
       decides whether this migration is correct - only an empty diff against the
       compiled oracle does.
  R-6  COMPILED BEHAVIOUR IS THE TIE-BREAKER, and the empty diff is the arbiter. The
       open questions this scenario touches are referenced BY IDENTIFIER -
       `Q-CLI-OVERREWRITE` for the `SYSTOT-REC` persistence question,
       `Q-CLI-TERMCODE-1-7` for the unobservable 1..7 band,
       `Q-CR-NOTES-SECOND-PASS` for A-NEW-1's suppressed pass,
       `Q-A17-POSTINGS-EFFECT` for A-17's stored effect and `Q-PURCH-AVERAGE-SIGN` for
       the average's sign - and each is recorded in
       `docs/migration/ambiguity-resolutions.md`, with the per-scenario empty-diff
       evidence in `docs/migration/scenario-diff-evidence.md`. THOSE REFERENCES ARE
       TEXTUAL ONLY: nothing below imports a document, checks that a path exists or
       skips because one is absent.
       Determinism is what makes the arbitration meaningful, and it is proven
       elsewhere, by `tests/determinism/test_two_runs_byte_identical.py`. `period: 1`
       is INERT in all eight scenarios, because `gl_end_of_cycle` - the only consumer
       of the cycles-per-quarter divisor `[copybooks/wssystem.cob:L64]` - appears in no
       scenario file; that omission is deliberate and is recorded in
       `docs/migration/ambiguity-resolutions.md` rather than silently assumed.

-------------------------------------------------------------------------------
17. HOW THIS FILE REACHES ITS HELPERS
-------------------------------------------------------------------------------

THROUGH FIXTURES, AND NEVER BY IMPORTING `tests/conftest.py`. That is the house
convention already established across `tests/arithmetic/` and stated verbatim in
`tests/determinism/test_two_runs_byte_identical.py`: "the house convention across
`tests/arithmetic/` is that conftest is reached through FIXTURES and never imported."
`Protocol`'s own docstring gives the reason - a test handed the object "needs no
import of this module and cannot accidentally reach a private helper".

The fixtures used below, and what each supplies:

    `scenario_loader`   the parsed scenario YAML, read with the SAFE loader and never
                        with the one that can construct arbitrary Python objects from
                        a data file. NEEDS NO STACK. This file never opens the YAML
                        itself and never imports a YAML parser.
    `harness`           the three harness modules, loaded by explicit file path.
                        Loading needs no Docker, no MariaDB and no GnuCOBOL, so the
                        list-level assertions below run on a bare host.
    `frozen_schema`     `mysql/ACASDB.sql` parsed into `{table: {column: ColumnType}}`.
                        READ, NEVER WRITTEN.
    `in_scope_table_names`  the twenty-two in-scope names. The inventory, the
                        single-column primary keys and the declared column counts have
                        EXACTLY ONE definition in this repository, so neither the
                        table list nor any primary key is restated here.
    `pinned_clock`      the two pinned observables, `to_day` and `run_date`.
    `protocol`          every protocol stage plus `run_scenario_parity`. It applies the
                        stack skip itself, so COLLECTION ALWAYS SUCCEEDS ON A BARE HOST
                        and a missing stack is a SKIP with a precise reason listing
                        every unmet precondition - never an error and never a false
                        pass.

`pytestmark` applies the `scenario` marker, which `pyproject.toml` registers under
`--strict-markers`. IT IS NOT RE-REGISTERED HERE: this file defines no
`pytest_configure`, no `pytest_plugins` and no `pytest_collection_modifyitems`, and a
second definition of one vocabulary is exactly the divergence R-4 forbids.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.scenario

SCENARIO = "clean_batch_pl"


# NOTE ON THE ANNOTATIONS BELOW. The module-level block above is fixed by this file's
# own specification to exactly four statements - the `__future__` import, `pytest`,
# `pytestmark` and `SCENARIO` - so no `typing` or `collections.abc` import is
# introduced and every fixture parameter is annotated with the builtin `object`. The
# concrete types are `tests/conftest.py`'s `Protocol`, `HarnessModules`,
# `acas_posting.clock.PinnedRunDate`, the `Callable[[str], Mapping[str, Any]]` scenario
# loader, the parsed schema mapping and the 22-name tuple; each parameter's docstring
# names what it actually is. Nothing here imports `tests/conftest.py`: the house
# convention across this tree is that conftest is reached through FIXTURES ONLY.
#
# EVERY EXPECTED VALUE IS A LOCAL, for the same reason. The affected-table list and the
# seed-file list are declared inside the one test that checks them, so this module
# publishes no second authority that could drift out of step with the scenario YAML.


def test_scenario_definition_preconditions(
    scenario_loader: object, pinned_clock: object
) -> None:
    """Every precondition `clean_batch_pl` must declare, asserted before any run.

    NEEDS NO STACK. A scenario definition is a file on disk, so this runs on a bare
    host and fails loudly there rather than being skipped into silence.

    THE FALSE-PASS TRAP, AND WHY IT IS CHECKED FIRST. `file_system_used` selects which
    store the frozen file handlers actually touch. `[copybooks/wssystem.cob:L112-L114]`
    declares it verbatim:

        L112                07  File-System-Used  pic 9.
        L113                    88  FS-Cobol-Files-Used    value zero.
        L114                    88  FS-MySql-Used          value 1.

    and `[common/acas007.cbl:L316-L320]` is what consumes it:

        L316       if       not FS-Cobol-Files-Used
        L317                move RDBMS-Flat-Statuses to FA-RDBMS-Flat-Statuses
        L318                perform  ba-Process-RDBMS
        L319                go to AA-Main-Exit
        L320       end-if.

    With the flag at ZERO that test is false, control falls through to the COBOL
    indexed-file path at `[common/acas007.cbl:L324]`, MySQL IS NEVER TOUCHED AT ALL,
    both dumps come back empty, the diff exits 0 and the run is a SILENT FALSE PASS.
    `[copybooks/wssystem.cob:L122]` bounds the field with
    `88 FS-Valid-Options values 0 thru 1.`

    On this route the flag has two further effects. `pl055` wraps its whole
    file-existence probe AND its terminate-code-8 raise inside
    `if FS-Cobol-Files-Used` at `[purchase/pl055.cbl:L266]`, so with the flag at one
    that branch is unreachable and the declared status of zero is provable. `pl060`
    guards its own open-item probe the same way at `[purchase/pl060.cbl:L376]`, so the
    OTM5 open-output recovery at `[purchase/pl060.cbl:L380]` does NOT fire and
    `PUITM5-REC` is not cleared at start-up.

    THE FAN-OUT SWITCH IS PINNED, AND HERE IT IS THE CONTROL CONDITION. Pure-GL mode -
    `IRS-Instead` a space `[copybooks/wssystem.cob:L179-L181]` - is precisely the
    configuration in which `sl060` FAILS to close the General Ledger posting file and
    `pl060` SUCCEEDS. Pinning the identical value in both scenarios is what makes them
    a matched pair, and Agent Action Plan section 0.6.4 is explicit that "leaving it at
    a default would make the affected-table list ambiguous". A YAML space or empty
    value maps to the command-line token `N` while the column still stores a space, and
    `harness/normalize.py`'s job 1 trims that identically on BOTH sides.

    THE SECOND PURE-GL FIELD IS NOT A YAML KEY, AND THAT IS RECORDED RATHER THAN
    ASSERTED. `G-L` is `88 G-L value 1.` on `Level-1`
    `[copybooks/wssystem.cob:L84-L85]`, and `pl060` gates its entire General Ledger
    side on it alone at `[purchase/pl060.cbl:L405-L406]`,
    `[purchase/pl060.cbl:L474-L475]` and `[purchase/pl060.cbl:L573-L574]`. It is
    carried by the seeded `system.dat` and by nothing in this file, because inventing a
    YAML key for it would be the added validation rule R-3 forbids. Its OBSERVABLE
    consequence is asserted instead, and in the right place: `GLBATCH-REC` and
    `GLPOSTING-REC` are on the affected-table list, and they can only be non-empty when
    `G-L` is true.

    Args:
        scenario_loader: `tests/conftest.py`'s loader, which parses the definition with
            the SAFE loader, never the one that can construct arbitrary Python
            objects from a data file. This file never opens the YAML itself and
            never imports a YAML parser.
        pinned_clock: The project-wide pinned pair, `to_day` and `run_date`, already
            asserted by `tests/conftest.py` to be the text `21/09/2025` and the binary
            155127.
    """
    definition = scenario_loader(SCENARIO)

    # Identity. `operations` is the sequence the Python runner reads and it PREFERS it
    # over the singular key; the oracle-side runner reads the singular key. Both must
    # name the same single operation, or the two sides would run different work.
    assert definition["name"] == SCENARIO
    assert definition["subsystem"] == "purchase"
    assert definition["operation"] == "pl_order_post"
    assert list(definition["operations"]) == ["pl_order_post"], (
        "clean_batch_pl runs exactly one operation, once, sequentially (rule R-3). "
        "load08 dispatches both pl055 and pl060 from a single menu selection "
        "[purchase/purchase.cbl:L752-L762], so one operation covers both programs."
    )

    system = definition["system"]

    # 1. THE FALSE-PASS TRAP. See the docstring - this is the assertion that keeps a
    #    run that never touched MySQL from reading as agreement.
    assert system["file_system_used"] == 1, (
        "system.file_system_used MUST be 1. At zero, "
        "[common/acas007.cbl:L316-L320]'s `if not FS-Cobol-Files-Used` is false, the "
        "handler never reaches the MySQL bridge, BOTH dumps come back empty and the "
        "diff exits 0 - a SILENT FALSE PASS. The condition names are "
        "[copybooks/wssystem.cob:L112-L114] and the valid range is "
        "[copybooks/wssystem.cob:L122]."
    )

    # 2. THE FAN-OUT SWITCH, pinned to a space in BOTH halves of the A-1 pair. The
    #    third state has no condition name at all [copybooks/wssystem.cob:L179-L181],
    #    and a `pic x` cannot hold an empty string, so a SPACE is the faithful
    #    spelling. The flat mirror exists because the oracle-side runner reads
    #    top-level keys only, and the two must agree.
    assert system["irs_instead"] == " ", (
        "system.irs_instead MUST be a single space - pure General Ledger mode. That "
        "is the ONLY configuration in which A-1 is observable: sl060 leaves the "
        "posting file unclosed [sales/sl060.cbl:L1176] and pl060 closes it "
        "[purchase/pl060.cbl:L1031]. Agent Action Plan section 0.6.4: leaving it at a "
        "default would make the affected-table list ambiguous."
    )
    assert definition["irs_instead"] == system["irs_instead"], (
        "the top-level irs_instead mirror and the system block must agree; the "
        "oracle-side runner reads the flat key and the seeder reads the block."
    )

    # 3. THE PINNED CLOCK, both observables. The binary one is a real column -
    #    `05  Run-Date  binary-long.` [copybooks/wssystem.cob:L67] - and
    #    `move run-date to entered` [purchase/pl060.cbl:L892] carries it into
    #    GLBATCH-REC.ENTERED, so a drifting clock cannot hide (rule R-6).
    clock = definition["clock"]
    assert clock["to_day"] == pinned_clock.to_day
    assert clock["run_date"] == pinned_clock.run_date
    assert definition["run_date_text"] == clock["to_day"], (
        "the flat run_date_text mirror must equal the clock block's to_day; "
        "harness/run_cobol_scenario.sh reads top-level keys only."
    )
    assert definition["run_date_binary"] == clock["run_date"]
    # An `int`, never a binary float (rule R-2), and never a `bool` - which would pass
    # an `isinstance(..., int)` check because `bool` subclasses `int`.
    assert isinstance(clock["run_date"], int)
    assert not isinstance(clock["run_date"], bool)

    # 4. THE AUTOGEN LATCHES. `05  PL-Autogen  pic x  value space.` at
    #    [copybooks/wssystem.cob:L209], which the maintainer marks NOT USED YET. On the
    #    Purchase side it is DOUBLY inert, because the autogen dispatch is commented
    #    out anyway at [purchase/purchase.cbl:L755-L758] - a divergence from Sales,
    #    where [sales/sales.cbl:L759] dispatches sl830 live. Pinned regardless, so all
    #    eight scenarios share one system block and so the asymmetry is recorded from
    #    the Purchase side too.
    assert system["pl_autogen"] == " "
    assert system["sl_autogen"] == " "

    # 5. THE CYCLE MUST BE NON-ZERO, and a zero does not fail a run - it HANGS one.
    #    `if scycle = zero / go to call-system-setup` [general/general.cbl:L462-L463]
    #    diverts the menu into interactive setup and waits on a terminal. The field and
    #    its redefinition are [copybooks/wssystem.cob:L62-L63], and the same value
    #    reaches the batch header through `move scycle to bcycle`
    #    [purchase/pl060.cbl:L891], so it is diff-visible as GLBATCH-REC.BCYCLE.
    assert system["cyclea"] != 0, (
        "system.cyclea must be non-zero. At zero the menu diverts to "
        "call-system-setup [general/general.cbl:L462-L463] and waits on an operator, "
        "which looks exactly like a hung harness rather than a failure."
    )

    # `period` is INERT on this route and in all eight scenarios: its only consumer is
    # the cycles-per-quarter divisor of gl080 [copybooks/wssystem.cob:L64], and
    # `gl_end_of_cycle` appears in no scenario file. That omission is deliberate and is
    # recorded in docs/migration/ambiguity-resolutions.md, not assumed away here. It is
    # still DECLARED, because the seeded system record must be fully determined.
    assert "period" in system

    # `date_form` selects the DIGIT ORDER the oracle types at the Date Entry screen -
    # `88 Date-UK value 1` [copybooks/wssystem.cob:L129-L131] - whereas the Python side
    # fixes DD/MM/CCYY unconditionally. That lexical asymmetry is documented and
    # deliberate: the two sides agree on the DATE, and differ only in how it is spelled
    # at an input surface the Python side does not have.
    assert system["date_form"] == 1
    assert definition["date_form"] == system["date_form"]

    # The cash and payment latches, inert here because sl100 and pl100 are not on this
    # route. Declared so the seeded record is fully determined
    # [copybooks/wssystem.cob:L226] and [copybooks/wssystem.cob:L206].
    assert system["s_flag_p"] == 2
    assert system["p_flag_p"] == 2

    # 6. THE SEED CONTRACT - EXACTLY SIX FILES, and the loader each one runs, from the
    #    frozen driver's per-file contract [common/masterLD.sh:L44-L115]:
    #      system.dat   -> the four-loader block [common/masterLD.sh:L51-L87]:
    #                      systemLD then sys4LD then finalLD then dfltLD, in that fixed
    #                      order. sys4LD IS WHAT LOADS SYSTOT-REC.
    #      analysis.dat -> analLD      [common/masterLD.sh:L93]  -> ANALYSIS-REC
    #      value.dat    -> valueLD     [common/masterLD.sh:L116] -> VALUEANAL-REC
    #      purchled.dat -> purchLD     [common/masterLD.sh:L111] -> PULEDGER-REC
    #      pinvoice.dat -> plinvoiceLD [common/masterLD.sh:L107]
    #                      -> PUINVOICE-REC and PUINV-LINES-REC
    #      openitm5.dat -> otm5LD      [common/masterLD.sh:L105] -> PUITM5-REC
    expected_seed_files = (
        "system.dat",
        "analysis.dat",
        "value.dat",
        "purchled.dat",
        "pinvoice.dat",
        "openitm5.dat",
    )
    seed = definition["seed"]
    assert tuple(seed["files"]) == expected_seed_files
    assert seed["data_dir"] == "pl_clean"
    # The flat mirrors the seeder itself reads. It resolves a relative directory
    # against the directory holding the definition.
    assert tuple(definition["seed_files"]) == expected_seed_files
    assert definition["seed_dir"] == seed["data_dir"]

    # system.dat is MANDATORY and the seeder refuses a scenario that omits it: the
    # frozen order seeds the system block first and unconditionally
    # [common/masterLD.sh:L51], and a missing system record makes the menu call sys002
    # and wait for an operator [general/general.cbl:L385-L396]. It is also the file
    # that carries Run-Date [copybooks/wssystem.cob:L67], the fan-out switch
    # [copybooks/wssystem.cob:L179-L181] and Level-1 [copybooks/wssystem.cob:L84-L85].
    assert "system.dat" in expected_seed_files

    # THE PURCHASE AUTOGEN SEED FILE IS FORBIDDEN. Its loader is at
    # [common/masterLD.sh:L108] and it lands in two tables this scenario does not
    # compare at all, so seeding it would put rows in the database that no declared
    # table covers.
    assert "plautogen.dat" not in expected_seed_files
    assert "plautogen.dat" not in tuple(seed["files"])
    assert "plautogen.dat" not in tuple(definition["seed_files"])

    # 7. THE DECLARED STATUS. Positional, one entry per operation. Zero here is
    #    PROVABLE rather than optimistic: the only terminate code either program can
    #    raise is eight, at [purchase/pl055.cbl:L286], inside a block whose outermost
    #    guard is `if FS-Cobol-Files-Used` at [purchase/pl055.cbl:L266] and which is
    #    closed by the two end-ifs at [purchase/pl055.cbl:L289] and
    #    [purchase/pl055.cbl:L290]. With the flag at one that raise cannot be taken.
    #    The other code the harness can ever see is five, raised on finding an open
    #    batch at [general/gl070.cbl:L289], and that belongs to the control-total
    #    scenario.
    #    NOTE that because load08 has NO GATE, an abort in pl055 would NOT stop pl060.
    #    The genuine Sales-versus-Purchase divergence therefore lives in the 1..7 band
    #    - Sales returns to the menu for any non-zero code up to seven, Purchase would
    #    PROCEED - and it is currently unobservable but must still be reproduced
    #    exactly. Carried as Q-CLI-TERMCODE-1-7.
    assert list(definition["expected_status"]) == [0]
    assert len(list(definition["expected_status"])) == len(
        list(definition["operations"])
    ), "expected_status is positional, so it must have one entry per operation."

    # 8. THIS ROUTE PROMOTES NOTHING, so no answer key is declared. pl060's
    #    confirmation paragraph `acpt-xrply.` [purchase/pl060.cbl:L362] is commented
    #    out line by line at [purchase/pl060.cbl:L363-L370], so there is no prompt to
    #    answer and no default to preserve. The four keys the runners DO recognise
    #    belong to the IRS, payment and end-of-cycle routes.
    for answer_key in (
        "answers",
        "irs_clear_postings",
        "payment_post_confirm",
        "gl080_proceed",
        "disk_change_option",
    ):
        assert not definition.get(answer_key), (
            f"clean_batch_pl must declare no {answer_key!r}: pl_order_post promotes "
            f"nothing, because pl060's acpt-xrply is commented out in the frozen "
            f"source [purchase/pl060.cbl:L362-L370]. Leaving every answer key "
            f"unstated is what keeps this scenario's inputs exactly the inputs the "
            f"frozen cycle takes."
        )

    # 9. RULE R-2, OVER THE WHOLE DEFINITION. YAML parses a bare decimal literal as a
    #    binary float, so no accounting value may appear as a YAML scalar anywhere -
    #    every money and quantity figure lives in the seeded flat files as decimal text
    #    in the frozen record layout. This walks the parsed object iteratively rather
    #    than recursively, so a deeply nested document cannot exhaust the stack.
    pending = [definition]
    while pending:
        node = pending.pop()
        if isinstance(node, dict):
            pending.extend(node.keys())
            pending.extend(node.values())
        elif isinstance(node, (list, tuple)):
            pending.extend(node)
        else:
            assert not isinstance(node, float), (
                f"the scenario definition carries the binary floating-point value "
                f"{node!r}. No accounting value may pass through binary floating "
                f"point at any point (rule R-2), and YAML parses a bare decimal "
                f"literal as a float - so every figure belongs in the seeded flat "
                f"files, never here."
            )


def test_affected_tables_are_in_scope_and_alphabetical(
    scenario_loader: object,
    harness: object,
    in_scope_table_names: object,
) -> None:
    """The ten declared tables, and the boundary they draw. NEEDS NO STACK.

    BOUNDING IS DONE BY THIS LIST AND BY NOTHING ELSE. There is no ignore-list, no
    tolerance-list and no "known difference" allowance anywhere in the diff path, so
    the list is the entire mechanism by which the two structural asymmetries between
    the sides - the menu shell's `overrewrite` and the autogen dispatch - are kept from
    reporting false failures.

    THE ORDER IS LOAD-BEARING, not cosmetic. The seed fingerprint is written in the
    DECLARED order, and two fingerprints that disagree are a HARNESS FAULT rather than
    a behavioural difference. The list is also the report's table order.

    TWO ENTRIES DESERVE COMMENT.

    `GLPOSTING-REC` IS THE A-1 CONTROL WITNESS. Here the General Ledger posting file
    DOES get closed, because `[purchase/pl060.cbl:L1031]` carries its terminating
    period; in the Sales half it does not, because `[sales/sl060.cbl:L1176]` does not.
    That contrast is the entire evidential value of the pair, and it is invisible in
    any other table and in any other mode.

    `SYSTOT-REC` IS LISTED BECAUSE THREE STATEMENTS ON THIS ROUTE WRITE IT -
    `[purchase/pl055.cbl:L582]`, `[purchase/pl055.cbl:L584]` and
    `[purchase/pl060.cbl:L628]` - AND IT CARRIES A RECORDED R-6 CAVEAT. A census across
    all twelve in-scope programs finds ZERO `System-*` facade verbs, so no in-scope
    program persists the system records; the OUT-OF-SCOPE menu shell does it, and the
    key-four write is the one that carries `SYSTOT-REC`
    `[purchase/purchase.cbl:L645-L650]`. The Python command line has no menu, so this
    table matches only if `acas_posting/cli/pl_order_post.py` reproduces that
    key-four `overrewrite` itself. The question is `Q-CLI-OVERREWRITE` and it is
    arbitrated against the oracle. IT IS NOT AND MUST NOT BE RESOLVED BY AN
    IGNORE-LIST: a divergence here is a REAL SIGNAL, and adding an allowance would
    convert it into a silent pass, which rule R-4 forbids outright.

    Args:
        scenario_loader: The scenario definition loader.
        harness: `tests/conftest.py`'s `HarnessModules`. Its `dump_tables.IN_SCOPE` is
            the single definition of the inventory, the single-column primary keys and
            the declared column counts, and `dump_tables.OUT_OF_SCOPE` the eleven
            tables the cycle never touches. The harness tree is NEVER imported as a
            package - it has no `__init__.py` and `pyproject.toml` excludes it.
        in_scope_table_names: The same twenty-two names, ascending, for a second
            independent membership check.
    """
    definition = scenario_loader(SCENARIO)
    dump_tables = harness.dump_tables

    # The ten, in the order the scenario declares them. Declared as a LOCAL so this
    # module publishes no second authority.
    expected = (
        "ANALYSIS-REC",
        "GLBATCH-REC",
        "GLPOSTING-REC",
        "PSIRSPOST-REC",
        "PUINV-LINES-REC",
        "PUINVOICE-REC",
        "PUITM5-REC",
        "PULEDGER-REC",
        "SYSTOT-REC",
        "VALUEANAL-REC",
    )
    declared = tuple(definition["affected_tables"])

    assert declared == expected, (
        "clean_batch_pl declares exactly these ten tables, in this order. The list "
        "BOUNDS the comparison and is the only bounding mechanism there is."
    )
    assert len(declared) == 10
    assert list(declared) == sorted(declared), (
        "the affected-table list must be alphabetical. The order is load-bearing: the "
        "seed fingerprint is written in declared order and a disagreement between the "
        "two sides' fingerprints is a HARNESS FAULT, not a behavioural difference."
    )
    assert len(set(declared)) == len(declared), "no table may be declared twice."

    # Every entry must be one of the twenty-two, checked against BOTH published views
    # of the one inventory. Neither the list nor any primary key is restated here.
    for table in declared:
        assert table in dump_tables.IN_SCOPE, (
            f"{table!r} is not one of the twenty-two in-scope tables. Dumping an "
            f"out-of-scope table would compare state the migration does not produce."
        )
        assert table in in_scope_table_names
        # The inventory's own metadata, read rather than retyped, so a drift in
        # mysql/ACASDB.sql surfaces here instead of three tables into a diff.
        specification = dump_tables.IN_SCOPE[table]
        assert specification.primary_key
        assert specification.column_count > 0

    # The eleven out-of-scope tables are never dumped.
    for table in declared:
        assert table not in dump_tables.OUT_OF_SCOPE

    # GLLEDGER-REC IS ABSENT, and its absence is MEASURED rather than assumed: neither
    # pl055 nor pl060 issues a single GL-Nominal-* verb, so the nominal ledger is never
    # read or written on this route. Only the General Ledger scenarios reach it.
    assert "GLLEDGER-REC" not in declared, (
        "GLLEDGER-REC must not be compared here: the Purchase route issues no "
        "GL-Nominal-* verb at all, so listing it would add a table that neither side "
        "touches."
    )

    # The three system records are absent because NO statement on this route changes
    # their content, so listing them would add a caveat without adding evidence.
    # SYSTOT-REC differs precisely in that three statements DO change it.
    for table in ("SYSTEM-REC", "SYSDEFLT-REC", "SYSFINAL-REC"):
        assert table not in declared
    assert "SYSTOT-REC" in declared

    # The A-1 control witness, and the batch record BL-Close also closes.
    assert "GLPOSTING-REC" in declared
    assert "GLBATCH-REC" in declared

    # PSIRSPOST-REC is an UNCHANGED WITNESS in pure-GL mode - its only writer here is
    # SPL-Posting-Write [purchase/pl060.cbl:L997] inside the fan-out conditional at
    # [purchase/pl060.cbl:L982], which is false for a space. It is listed anyway,
    # because a table left out of the comparison cannot prove anything about itself.
    assert "PSIRSPOST-REC" in declared

    # VALUEANAL-REC is written on this side by pl055 ONLY - pl060 issues zero Value-*
    # verbs - and ANALYSIS-REC by pl055's Analysis-Write.
    assert "VALUEANAL-REC" in declared
    assert "ANALYSIS-REC" in declared


def test_clean_batch_post_pl_state_parity(protocol: object, harness: object) -> None:
    """THE HEADLINE. Eight stages, and the diff MUST BE EMPTY.

    Agent Action Plan section 0.8.5, acceptance criterion 1: seed identically, run the
    compiled cycle, dump the affected tables ordering-normalised, reset, run the Python
    cycle, dump again - "and the diff **must be empty**".

    THE PROTOCOL IS NOT REIMPLEMENTED HERE. `protocol.run_scenario_parity` runs all
    eight stages in order, strictly sequentially, on one database, which is exactly
    what Agent Action Plan section 0.4.3 exposed it for. The stages whose failure
    DESTROYS the evidence - seed, reset, either dump, either normalisation - raise, so
    they surface as a pytest ERROR. The two RUN stages do not: a run that aborted
    behaviourally still leaves the database in the state the specification says it
    should be in, and that state is still dumped, because Agent Action Plan section
    0.6.5 makes ABSENCE EVIDENCE.

    WHAT A FAILURE HERE MEANS. Exactly one thing: the migrated Purchase cycle diverges
    from the compiled COBOL. It does NOT mean the comparison was inconclusive - that is
    exit 2, which `tests/conftest.py` maps to `HarnessFaultError` and therefore to an
    ERROR, never to a pass. The two can never be confused.

    THE EVIDENCE THIS RUN PRODUCES is `$ACAS_OUT/clean_batch_pl/diff.txt`, cited by
    `docs/migration/scenario-diff-evidence.md`. ON A PASS IT IS ZERO BYTES, and that is
    deliberate rather than an omission: an existing empty file says "compared, and
    identical" while an absent file says nothing at all, and the evidence document must
    be able to tell those apart.

    Args:
        protocol: `tests/conftest.py`'s protocol object. It applies the stack skip
            itself, so collection always succeeds on a bare host and an unusable stack
            is a SKIP naming every unmet precondition.
        harness: The three harness modules, for the report renderer. The harness
            tree is NEVER imported as a package; it arrives only through the fixture.

    Raises:
        Skipped: The Compose stack is unusable.
        Exception: A stage fault, or the comparison's exit 2. A HARNESS FAULT, and
            never a pass.
    """
    diff_states = harness.diff_states

    parity = protocol.run_scenario_parity(SCENARIO)

    # The comparison was bounded by the scenario's own list, in the scenario's own
    # order. Asserted because an unbounded or re-ordered comparison would be a
    # different experiment from the one this file documents.
    assert parity.tables == protocol.affected_tables(SCENARIO)
    assert len(parity.tables) == 10

    # THE PASS CONDITION. `render` returns THE EMPTY STRING when the two trees are
    # identical, so it is safe to build the message unconditionally - and when they are
    # not, it names every finding, table by table and key by key.
    assert parity.is_empty, (
        f"clean_batch_pl DIVERGED: the migrated Purchase cycle did not reproduce the "
        f"compiled COBOL. {parity.tree.total_differences} finding(s) across "
        f"{len(parity.tables)} bounded table(s).\n"
        f"\nA non-empty diff here is ALWAYS a real behavioural difference and never "
        f"an artefact of the comparison (Agent Action Plan section 0.6.6): every "
        f"in-scope table has a single-column primary key, zero secondary indexes, no "
        f"TIMESTAMP and no AUTO_INCREMENT, so the dump is deterministic by "
        f"construction.\n"
        f"\nDO NOT resolve this with an ignore-list, a tolerance or a 'known "
        f"difference' allowance - there is none anywhere in the diff path and adding "
        f"one would convert a real signal into a silent pass (rule R-4). If the "
        f"divergence is in SYSTOT-REC, it is the recorded persistence question "
        f"Q-CLI-OVERREWRITE - the menu's key-four overrewrite "
        f"[purchase/purchase.cbl:L645-L650] against a Python entry point that has no "
        f"menu - and it is settled by REPRODUCING the paragraph, in "
        f"docs/migration/ambiguity-resolutions.md.\n"
        f"\n{diff_states.render(parity.tree)}"
        f"\n{parity.describe()}"
    )

    # 0 MEANS ZERO BYTES ON STDOUT, not a banner. Asserted on the real artifact of a
    # real run, because this is the only test that produces one.
    assert parity.outcome.result.returncode == diff_states.EX_IDENTICAL
    assert parity.outcome.result.stdout == "", (
        "an identical comparison writes NOTHING to stdout. A banner would make an "
        "empty diff indistinguishable from a summarised one in a captured log."
    )
    if parity.outcome.report.exists():
        assert parity.outcome.report.stat().st_size == 0, (
            "a passing comparison writes a ZERO-BYTE diff.txt. An existing empty file "
            "says 'compared, and identical'; an absent file says nothing at all, and "
            "docs/migration/scenario-diff-evidence.md must be able to tell those "
            "apart."
        )


def test_a1_control_pl060_terminating_period_is_present(
    protocol: object, harness: object
) -> None:
    """A-1's CONTROL. `pl060` HAS the period, so the posting file IS closed.

    THE TWO SOURCES, SIDE BY SIDE. `[purchase/pl060.cbl:L1027-L1033]`, verbatim:

        L1027       if       IRS-Both-Used OR G-L    *> THIS IS IN PURCHASE PL060
        L1028                move     RRN  to  postings.     *> Why ?
        L1029       perform  GL-Batch-Close.
        L1030       if       IRS-Used OR IRS-Both-Used
        L1031                perform SPL-Posting-Close.   *> ** THE PERIOD IS PRESENT **
        L1032       if       IRS-Both-Used or G-L
        L1033                perform GL-Posting-Close.
        L1035  main-exit.   exit section.

    `[sales/sl060.cbl:L1172-L1178]`, verbatim:

        L1172       if       IRS-Both-Used OR G-L    *> THIS IS IN PURCHASE PL060
        L1173                move     RRN  to  postings.     *> Why ?
        L1174       perform  GL-Batch-Close.
        L1175       if       IRS-Used OR IRS-Both-Used
        L1176                perform SPL-Posting-Close      *> ** NO PERIOD **
        L1177       if       IRS-Both-Used or G-L
        L1178                perform GL-Posting-Close.

    In `sl060` the absent period at L1176 makes the `if` at L1177 a NESTED conditional
    instead of a sibling sentence, so in pure-GL mode the outer test is false, the inner
    test is never evaluated, and `GL-Posting-Close` never runs. In `pl060` the same
    statement is a sibling, so `GL-Posting-Close` runs whenever `IRS-Both-Used OR G-L`,
    INCLUDING pure-GL mode.

    THE OTHER TWO SIBLINGS ALSO HAVE THE PERIOD - `[sales/sl100.cbl:L694]` and
    `[purchase/pl100.cbl:L675]`. THREE OF FOUR HAVE IT; ONE DOES NOT. That
    three-to-one split is the proof that A-1 is an ACCIDENT AND NOT AN IDIOM, and it is
    the reason the anomaly is worded as a defect at all. This test and
    `tests/scenarios/test_clean_batch_post_sl.py` together make the proof reviewable:
    one captures the defect, the other captures the control, and both capture COMPILED
    BEHAVIOUR rather than an argument about it. NEITHER MAY BE NORMALISED TOWARD THE
    OTHER - harmonising the two programs would delete the evidence, and under rule R-4
    that is a failure, not an improvement. The reproducing modules are
    `acas_posting/programs/sl060_invoice_posting.py`, where the second conditional is
    written as a NESTED conditional deliberately, and
    `acas_posting/programs/pl060_order_posting.py`, where it is not.

    WHAT IS ASSERTED, AND HOW IT IS FRAMED. That the two SIDES AGREE on
    `GLPOSTING-REC` and `GLBATCH-REC` - never that "Purchase is correct". Correctness
    here is defined solely as reproducing what the compiled program did; the accounting
    merit of closing a file is not this file's business, and asserting it would be the
    inverted-premise error Agent Action Plan section 0.8.2 warns against.

    WHY `GLPOSTING-REC` IS THE RIGHT WITNESS. `BL-Close` at
    `[purchase/pl060.cbl:L1013]` is reached only through `if G-L / perform BL-Close` at
    `[purchase/pl060.cbl:L573-L574]`, and it is `BL-Close` that contains all three
    closes. So a non-empty `GLPOSTING-REC` on either side is proof the section ran, and
    agreement between the sides is proof the migrated cycle took the same branch.

    Args:
        protocol: The protocol object; it applies the stack skip.
        harness: The three harness modules, for the report renderer.

    Raises:
        Skipped: The Compose stack is unusable.
        Exception: A stage fault or the comparison's exit 2 - a harness fault.
    """
    diff_states = harness.diff_states

    parity = protocol.run_scenario_parity(SCENARIO)

    # The two tables BL-Close touches, located by name in the comparison's own report
    # order rather than by position.
    by_table = {table.table: table for table in parity.tree.tables}
    for witness in ("GLPOSTING-REC", "GLBATCH-REC"):
        assert witness in by_table, (
            f"{witness} was not compared. It is on clean_batch_pl's affected-table "
            f"list precisely so that A-1's control side is witnessed, and a table left "
            f"out of the comparison cannot prove anything about itself."
        )
        table_diff = by_table[witness]
        assert table_diff.is_empty, (
            f"A-1's CONTROL FAILED on {witness}: the two sides disagree, with "
            f"{table_diff.total_differences} finding(s).\n"
            f"\nIn pure-GL mode pl060 CLOSES the General Ledger posting file, because "
            f"[purchase/pl060.cbl:L1031] carries its terminating period, so "
            f"[purchase/pl060.cbl:L1032-L1033] is a SIBLING sentence and "
            f"GL-Posting-Close runs. sl060's equivalent at [sales/sl060.cbl:L1176] has "
            f"NO period, so [sales/sl060.cbl:L1177-L1178] is NESTED and never runs. "
            f"The other two siblings - [sales/sl100.cbl:L694] and "
            f"[purchase/pl100.cbl:L675] - have the period, so three of four do.\n"
            f"\nThis assertion says only that the COBOL AND PYTHON SIDES AGREE. It "
            f"does NOT say Purchase is correct, and the fix is NEVER to normalise "
            f"pl060 toward sl060 or sl060 toward pl060: that three-to-one split is the "
            f"whole evidence that A-1 is an accident rather than an idiom, and "
            f"deleting it would be a failure under rule R-4. See A-1 and A-NEW-10 in "
            f"docs/migration/anomaly-log.md.\n"
            f"\n{diff_states.render(parity.tree)}"
        )

    # The whole comparison, so a divergence elsewhere is not mistaken for A-1's control
    # holding. The two facts are reported separately on purpose.
    assert parity.is_empty, (
        f"the A-1 control witnesses agree, but clean_batch_pl diverged elsewhere: "
        f"{parity.tree.total_differences} finding(s).\n"
        f"{diff_states.render(parity.tree)}"
    )


def test_a_new_1_second_apportionment_pass_never_runs(
    protocol: object, harness: object
) -> None:
    """A-NEW-1. The credit-note SECOND apportionment pass is unreachable.

    `[purchase/pl060.cbl:L809-L823]`, verbatim:

        L809  end-loop.
        L812       if       work-1 = zero
        L813          or    first-pass not = "Y"
        L814                go to  main-end.
        L815       move     "N"  to  first-pass.
        L818       set      fn-not-less-than to true.
        L819       perform  OTM5-Start.  *> start open-item-file-5 key not < oi5-key
        L820       go       to main-end.        <- UNCONDITIONAL
        L821       go       to  read-loop.      <- DEAD CODE, unreachable
        L823  main-end.

    The shape is unmistakable and the maintainer's own trailing comment on L819 records
    the `invalid key` clause the `perform` replaced. L815 flips `first-pass` to `"N"`
    and L818-L819 reposition the open-item cursor - both of which are preparation for a
    SECOND pass over the credit notes. The transfer that would begin that pass is L821.
    IT SITS AFTER AN UNCONDITIONAL `go to main-end` AT L820, so control leaves the
    paragraph first and L821 can never execute. The second pass NEVER RUNS.

    REPRODUCED, NOT FIXED (rule R-4). `acas_posting/programs/pl060_order_posting.py`
    carries the dead transfer forward as dead. The end state the suppressed pass would
    have left is UNMEASURED and is carried as `Q-CR-NOTES-SECOND-PASS` in
    `docs/migration/ambiguity-resolutions.md`; nothing here guesses at it.

    WHY `PUITM5-REC` IS THE WITNESS. The suppressed pass is the one that would have
    re-walked the open-item file, so a single-pass outcome and a two-pass outcome would
    differ in the open-item table and nowhere else. `pl060` reaches it through
    `OTM5-Write` and two `OTM5-Rewrite` verbs. Note that the table is NOT cleared at
    start-up either: `pl060`'s open-item probe is guarded by `if FS-Cobol-Files-Used` at
    `[purchase/pl060.cbl:L376]`, so with the flag at one the open-output recovery at
    `[purchase/pl060.cbl:L380]` does not fire. So the seeded rows survive into the
    capture, which is what makes a single-pass outcome visible at all.

    THE FIXTURE IS BUILT TO APPROACH THE ANOMALY GENUINELY. The seed carries at least
    one OPEN CREDIT NOTE with an unapplied balance against the same supplier as the
    invoices, so `work-1` is non-zero at L812 and `first-pass` is still `"Y"` - which
    means the guard at L812-L814 does NOT take the early exit, and control really does
    reach L819 and then L820. A fixture that failed that guard would make the anomaly
    LATENT rather than reproduced, and the test would pass for the wrong reason.

    AS ALWAYS, WHAT IS ASSERTED IS THAT THE TWO SIDES AGREE. This test does not compute
    what a second pass would have produced, and it does not assert that the open items
    are correctly apportioned.

    Args:
        protocol: The protocol object; it applies the stack skip.
        harness: The three harness modules, for the report renderer.

    Raises:
        Skipped: The Compose stack is unusable.
        Exception: A stage fault or the comparison's exit 2 - a harness fault.
    """
    diff_states = harness.diff_states

    parity = protocol.run_scenario_parity(SCENARIO)

    by_table = {table.table: table for table in parity.tree.tables}
    assert "PUITM5-REC" in by_table, (
        "PUITM5-REC was not compared, so A-NEW-1's single-pass outcome is unwitnessed."
    )
    open_items = by_table["PUITM5-REC"]

    assert open_items.is_empty, (
        f"PUITM5-REC diverged, with {open_items.total_differences} finding(s), so the "
        f"two sides do not agree on the SINGLE-PASS outcome A-NEW-1 produces.\n"
        f"\nA-NEW-1: in [purchase/pl060.cbl:L809-L823] the `go to main-end.` at L820 "
        f"is UNCONDITIONAL, so the `go to read-loop.` at L821 - the transfer that "
        f"would begin the second apportionment pass prepared by L815 and L818-L819 - "
        f"is DEAD CODE and the second pass never runs.\n"
        f"\nIF THE PYTHON SIDE HAS MORE APPORTIONMENT THAN THE COBOL SIDE, THE SECOND "
        f"PASS HAS BEEN 'FIXED' AND THAT IS A FAILURE, not an improvement (rule R-4). "
        f"The dead transfer must stay dead. The unmeasured end state the pass would "
        f"have left is Q-CR-NOTES-SECOND-PASS; see A-NEW-1 in "
        f"docs/migration/anomaly-log.md.\n"
        f"\n{diff_states.render(parity.tree)}"
    )

    assert parity.is_empty, (
        f"PUITM5-REC agrees, but clean_batch_pl diverged elsewhere: "
        f"{parity.tree.total_differences} finding(s).\n"
        f"{diff_states.render(parity.tree)}"
    )


def test_moving_average_fields_agree(
    protocol: object, harness: object, frozen_schema: object
) -> None:
    """A-8, A-9 and A-10's PURCHASE HALF, witnessed in `PULEDGER-REC`.

    THE TWO SECTIONS, verbatim. `[purchase/pl060.cbl:L740-L751]`, `purch-comp`:

        L743       if       purch-activety not = zero
        L744          and   purch-average not = zero
        L745                multiply purch-activety by purch-average giving work-2
        L746       else
        L747                move zero to work-2
        L748       end-if
        L749       add      1 to purch-activety.
        L750       add      work-goods to work-2.
        L751       divide   purch-activety into work-2 giving purch-average.

    `[purchase/pl060.cbl:L755-L766]`, `credit-comp`:

        L758       if       purch-activety not = zero
        L759         and    purch-average not = zero
        L760                multiply purch-activety by purch-average giving work-2
        L761       else
        L762                move zero to work-2
        L763       end-if
        L764       if       work-2 not = zero
        L765                add work-goods to work-2
        L766                divide purch-activety into work-2 giving purch-average.

    THREE ANOMALIES MEET IN THOSE TWENTY-TWO LINES.

    A-9 - `credit-comp` NEVER INCREMENTS THE ACTIVITY COUNTER. `purch-comp` does, at
    `[purchase/pl060.cbl:L749]`; there is no `add 1 to purch-activety` anywhere in
    `credit-comp`. So a supplier's first credit note is silently dropped from the
    average, because the divisor never learns about it.

    A-10 - THE GUARDS DISAGREE WITH ONE ANOTHER. `credit-comp` carries an EXTRA guard
    at `[purchase/pl060.cbl:L764]` that `purch-comp` does not, and the Sales cash path
    at `[sales/sl100.cbl:L506]` uses a third variant that additionally INVERTS the
    divide operand order. Three instances of one idiom, three different guards.
    NORMALISING THEM INTO ONE HELPER WOULD BE THE SINGLE EASIEST WAY TO FAIL THIS
    MIGRATION.

    A-8 - THE PRECISION IS LOST TWICE, AND THE FIELD TYPES ARE WHY.
    `03  Purch-Activety   binary-long.` `[copybooks/wspl.cob:L35]` and
    `03  Purch-Average    binary-long.` `[copybooks/wspl.cob:L38]` land as
    `PURCH-ACTIVETY int(8) unsigned` and `PURCH-AVERAGE int(8) unsigned`. They are
    INTEGERS, so the `divide` at L751 and at L766 truncates - and the accumulator has
    already truncated once. `PULEDGER-REC` mixes `Decimal` money columns with `int`
    statistics columns, and that split is exactly what makes the defect reproducible;
    blurring it would silently produce the "improved" answer.

    THE SIGN QUESTION IS OPEN AND IS NOT PRE-EMPTED HERE. The COBOL field is SIGNED
    `binary-long` while the column is UNSIGNED, which is the A-11 pattern, and what a
    negative average actually stores is carried as `Q-PURCH-AVERAGE-SIGN`. This test
    asserts only that BOTH SIDES STORE THE SAME THING.

    NOTHING IS RECOMPUTED. The arithmetic tier owns per-field exactness, with expected
    values captured from the compiled oracle rather than derived by reading the COBOL.
    Here the only question is agreement, and computing an expected average in Python
    would substitute this file's reading of the source for the oracle's behaviour -
    precisely the inversion rule R-6 forbids.

    THE FIXTURE MAKES BOTH SECTIONS FIRE: two invoices plus one credit note for the
    SAME supplier, so `purch-comp` runs twice from a non-zero accumulator and
    `credit-comp` runs once with a counter that was never incremented for it.

    Args:
        protocol: The protocol object; it applies the stack skip.
        harness: The three harness modules, for the renderer and the schema reader.
        frozen_schema: `mysql/ACASDB.sql` parsed into `{table: {column: ColumnType}}`.
            READ, NEVER WRITTEN - Agent Action Plan section 0.8.1 makes any diff against
            it a defect in the migration.

    Raises:
        Skipped: The Compose stack is unusable.
        Exception: A stage fault or the comparison's exit 2 - a harness fault.
    """
    diff_states = harness.diff_states
    normalize = harness.normalize

    # THE STORAGE CLASS IS PART OF THE ANOMALY, so it is asserted from the frozen schema
    # before anything is run. If either column were ever a DECIMAL the double
    # truncation would not occur and A-8 would be silently "fixed" by the schema.
    for column_name in ("PURCH-ACTIVETY", "PURCH-AVERAGE"):
        column = normalize.column_type(frozen_schema, "PULEDGER-REC", column_name)
        assert column.kind == normalize.KIND_INTEGER, (
            f"PULEDGER-REC.{column_name} must be an INTEGER column - it is declared "
            f"`{column.sql_type}` at [mysql/ACASDB.sql:L{column.line}], from "
            f"`binary-long` at [copybooks/wspl.cob:L35] and "
            f"[copybooks/wspl.cob:L38]. Integer storage is what makes the divide at "
            f"[purchase/pl060.cbl:L751] and [purchase/pl060.cbl:L766] truncate, which "
            f"is anomaly A-8. A decimal column here would silently repair the defect."
        )
        assert column.scale is None, (
            f"PULEDGER-REC.{column_name} must carry no decimal scale: pence are "
            f"discarded by construction, which is the first of A-8's two truncations."
        )

    parity = protocol.run_scenario_parity(SCENARIO)

    by_table = {table.table: table for table in parity.tree.tables}
    assert "PULEDGER-REC" in by_table, (
        "PULEDGER-REC was not compared, so the Purchase moving average is unwitnessed."
    )
    ledger = by_table["PULEDGER-REC"]

    # Name the average columns explicitly when they are among the differences, so the
    # failure message points at A-8, A-9 and A-10 rather than at "a ledger difference".
    # `TableDiff.value_differences` is a tuple of `RowDifference`, each of whose
    # `values` is a tuple of `ValueDifference` carrying the `column` name.
    average_columns = ("PURCH-ACTIVETY", "PURCH-AVERAGE")
    implicated = sorted(
        {
            difference.column
            for row in ledger.value_differences
            for difference in row.values
            if difference.column in average_columns
        }
    )

    assert ledger.is_empty, (
        f"PULEDGER-REC diverged, with {ledger.total_differences} finding(s)"
        + (
            f", INCLUDING the moving-average columns {', '.join(implicated)}"
            if implicated
            else ""
        )
        + ".\n"
        f"\nThe Purchase half of A-8, A-9 and A-10 lives in two sections:\n"
        f"  purch-comp  [purchase/pl060.cbl:L740] - guard L743-L748, counter L749, "
        f"add L750, divide L751\n"
        f"  credit-comp [purchase/pl060.cbl:L755] - guard L758-L763, EXTRA guard L764, "
        f"add L765, divide L766, AND NO COUNTER INCREMENT ANYWHERE (A-9)\n"
        f"\nIf the two sides differ in PURCH-AVERAGE or PURCH-ACTIVETY, the most "
        f"likely cause is a repair rather than a bug: a counter increment added to "
        f"credit-comp, the extra guard at L764 dropped, the three guards unified into "
        f"one helper, or the integer divide carried at two decimal places. EVERY ONE "
        f"OF THOSE IS A FAILURE (rule R-4) - the defects are the specification. The "
        f"sign "
        f"question is separately open as Q-PURCH-AVERAGE-SIGN; see A-8, A-9, A-10 and "
        f"A-11 in docs/migration/anomaly-log.md.\n"
        f"\n{diff_states.render(parity.tree)}"
    )

    assert parity.is_empty, (
        f"PULEDGER-REC agrees, but clean_batch_pl diverged elsewhere: "
        f"{parity.tree.total_differences} finding(s).\n"
        f"{diff_states.render(parity.tree)}"
    )


def test_valueanal_written_by_pl055_only(protocol: object, harness: object) -> None:
    """`VALUEANAL-REC` has ONE writer on this route, and it is `pl055`.

    THE VERB CENSUS, which is what makes the claim measured rather than assumed.
    `pl055` issues `Analysis-Write`, `PInvoice-Rewrite`, `Value-Write` and
    `Value-Rewrite` - and NO `Value-Open-Output`, where `sl055` carries one as a
    recovery. `pl060` issues `GL-Batch-Write`, `GL-Posting-Write`, `OTM5-Write`,
    `OTM5-Rewrite` twice, `SPL-Posting-Write`, `Purch-Write`, `Purch-Rewrite`, three
    `*-Open-Output` recoveries and `SPL-Posting-Open-Extend` - and ZERO `Value-*` VERBS
    OF ANY KIND: not an open, not a read, not a rewrite. Its Sales counterpart `sl060`
    issues `Value-Read-Indexed` and `Value-Rewrite` twice each, so this is a genuine
    Sales-versus-Purchase divergence and not an oversight in the census.

    THEREFORE EVERY `VALUEANAL-REC` CHANGE IN THIS CAPTURE TRACES TO `pl055`, and the
    same is true of `ANALYSIS-REC`, whose only writer here is `pl055`'s
    `Analysis-Write`. That narrows a divergence in either table to one program, which is
    the whole reason to assert them separately from the headline diff.

    TWO `pl055` BEHAVIOURS THE FIXTURE IS BUILT AROUND. `pl055` opens the value file
    with `perform Value-Open.` at `[purchase/pl055.cbl:L261]` and accumulates into it
    with two sign flips - on the VAT total at `[purchase/pl055.cbl:L376]` and on the
    carriage total at `[purchase/pl055.cbl:L387]` - under `va-system = "P"` at
    `[purchase/pl055.cbl:L403]`. And a MISSING analysis or value code does not fail a
    run: it makes `pl055` CREATE the entry, at `[purchase/pl055.cbl:L323-L325]`. That is
    a different capture from the one this scenario describes, which is why the fixture
    seeds codes covering every group the invoice lines reference, INCLUDING the four
    `va-system "P"` specials `pl055` stores for itself at
    `[purchase/pl055.cbl:L403-L419]`.

    AS EVERYWHERE, THE ASSERTION IS AGREEMENT. Nothing here recomputes a value-analysis
    total or checks that the analysis codes balance.

    Args:
        protocol: The protocol object; it applies the stack skip.
        harness: The three harness modules, for the report renderer.

    Raises:
        Skipped: The Compose stack is unusable.
        Exception: A stage fault or the comparison's exit 2 - a harness fault.
    """
    diff_states = harness.diff_states

    parity = protocol.run_scenario_parity(SCENARIO)

    by_table = {table.table: table for table in parity.tree.tables}
    for table_name, attribution in (
        ("VALUEANAL-REC", "pl055's Value-Write and Value-Rewrite"),
        ("ANALYSIS-REC", "pl055's Analysis-Write"),
    ):
        assert table_name in by_table, f"{table_name} was not compared."
        table_diff = by_table[table_name]
        assert table_diff.is_empty, (
            f"{table_name} diverged, with {table_diff.total_differences} finding(s). "
            f"Its ONLY writer on this route is {attribution}: pl060 issues ZERO "
            f"Value-* verbs of any kind, so the divergence is attributable to pl055 "
            f"alone.\n"
            f"\nCheck first whether the seeded analysis and value codes cover every "
            f"group the invoice lines reference - a MISSING code does not fail the "
            f"run, it makes pl055 CREATE the entry at "
            f"[purchase/pl055.cbl:L323-L325], which is a different capture from the "
            f"one this scenario describes. Then check the two sign flips at "
            f"[purchase/pl055.cbl:L376] and [purchase/pl055.cbl:L387].\n"
            f"\n{diff_states.render(parity.tree)}"
        )

    assert parity.is_empty, (
        f"the value-analysis tables agree, but clean_batch_pl diverged elsewhere: "
        f"{parity.tree.total_differences} finding(s).\n"
        f"{diff_states.render(parity.tree)}"
    )


def test_autogen_tables_untouched(scenario_loader: object, harness: object) -> None:
    """The four autogen tables are neither seeded nor compared. NEEDS NO STACK.

    THE ASYMMETRY THIS GUARDS. On the SALES side `[sales/sales.cbl:L759]` dispatches
    `sl830` LIVE, before `sl055`, and `acas_posting/cli/sl_invoice_post.py` dispatches
    only `sl055` then `sl060` - so an out-of-scope program runs on the oracle side and
    not on the Python side, and the Sales scenario has to mitigate that. On the PURCHASE
    side there is NOTHING TO MITIGATE, because the autogen dispatch is COMMENTED OUT
    ENTIRELY at `[purchase/purchase.cbl:L755-L758]`, and the maintainer's own changelog
    entry at `[purchase/purchase.cbl:L112-L114]` says why: the four lines are remarked
    out "until the programs have been written". No autogen program runs on EITHER side
    here, which is exactly why `pl_autogen` is inert on this route.

    EITHER WAY THE FOUR TABLES ARE NEVER SEEDED AND NEVER LISTED. The `sl800` to `sl830`
    autogen series and the `pl800` series are explicitly out of scope (Agent Action Plan
    section 0.2.2), and their two loaders are among the eight forbidden seed files -
    `[common/masterLD.sh:L108]` for the Purchase pair and `[common/masterLD.sh:L113]`
    for the Sales pair.

    THE AUTHORITATIVE POST-RUN ASSERTION LIVES IN THE RUNNERS, NOT HERE. Both
    `harness/run_cobol_scenario.sh` and `harness/run_python_scenario.sh` check after
    their run that all four tables are still EMPTY, because if a run left rows in them
    the two sides were not doing comparable work and no diff over the affected tables
    could be trusted. This test makes only the LIST-LEVEL assertion, which is what can
    be checked without a stack - and it is worth checking, because a table absent from
    the list is also absent from the runners' comparison, so the two facts have to hold
    together.

    Args:
        scenario_loader: The scenario definition loader.
        harness: The three harness modules. `dump_tables.OUT_OF_SCOPE` is the single
            definition of the eleven tables the cycle never touches.
    """
    definition = scenario_loader(SCENARIO)
    dump_tables = harness.dump_tables

    autogen_tables = (
        "SAAUTOGEN-REC",
        "SAAUTOGEN-LINES-REC",
        "PUAUTOGEN-REC",
        "PUAUTOGEN-LINES-REC",
    )
    declared = tuple(definition["affected_tables"])
    seeded = tuple(definition["seed_files"])

    for table in autogen_tables:
        # Out of scope by definition, checked against the harness's own inventory rather
        # than asserted from this file's own list.
        assert table in dump_tables.OUT_OF_SCOPE, (
            f"{table!r} must be one of the eleven out-of-scope tables. The autogen "
            f"series is explicitly out of scope (Agent Action Plan section 0.2.2)."
        )
        assert table not in dump_tables.IN_SCOPE
        assert table not in declared, (
            f"{table!r} must not appear on clean_batch_pl's affected-table list. "
            f"Dumping it would compare state neither side produces: the Purchase "
            f"autogen dispatch is commented out at "
            f"[purchase/purchase.cbl:L755-L758], where the Sales equivalent at "
            f"[sales/sales.cbl:L759] is live."
        )

    # Neither autogen loader may be seeded. Named by locator in the frozen driver so the
    # token cannot be copied into a seed list by accident:
    # [common/masterLD.sh:L108] is the Purchase pair, [common/masterLD.sh:L113] the
    # Sales pair. Seeding the Purchase one in particular would populate two tables this
    # scenario does not compare at all.
    for forbidden in ("plautogen.dat", "slautogen.dat"):
        assert forbidden not in seeded, (
            f"{forbidden!r} must not be seeded: its loader lands in tables this cycle "
            f"never touches, so loading it would put rows in the database that no "
            f"declared table covers."
        )


def test_diff_exit_contract_is_honoured(harness: object) -> None:
    """THE THREE-WAY EXIT CONTRACT, asserted directly. NEEDS NO STACK.

        0  the trees are IDENTICAL, and stdout is EMPTY - zero bytes, not a banner
        1  a REAL BEHAVIOURAL DIFFERENCE, with a deterministic report   -> FAILURE
        2  THE COMPARISON COULD NOT BE PERFORMED                        -> ERROR

    EXIT 2 IS NEVER A PASS. It covers a missing tree, a missing table file, a malformed
    dump, a shape mismatch, a `float` in the input, a duplicate primary key, a wrong key
    order, `row_count != len(rows)`, a ragged row and a `null`. `tests/conftest.py`'s
    stage 8 maps it to `HarnessFaultError`, which surfaces as a pytest ERROR rather than
    a failure, because rule R-6 makes an empty diff the pass condition ONLY WHEN A
    COMPARISON ACTUALLY HAPPENED. A test that treated "could not compare" as "no
    differences" is the single worst bug available in this tree, and this test is the
    standing check that the three codes remain three distinct things.

    WHY THE RENDERER IS EXERCISED HERE. The "zero bytes" half of the contract is a
    property of `render`, not of a run: it must return THE EMPTY STRING for an identical
    comparison, so that a passing stage can write a zero-byte `diff.txt` and an operator
    sees nothing at all. That is asserted on constructed `TreeDiff` values, which are
    pure data - no database, no Docker and no compiled oracle - so the contract is
    checked on every host rather than only where the stack is up. The complementary
    assertions on a REAL run's artifact are in
    `test_clean_batch_post_pl_state_parity`.

    THE TWO LABELS ARE FIXED AND ARE NOT CONFIGURABLE: `cobol` and `python`, never left
    and right, and the side is recorded in the PATH and never inside a dump.

    Args:
        harness: The three harness modules. Constructing a `TreeDiff` and a `TableDiff`
            performs no I/O of any kind.
    """
    diff_states = harness.diff_states

    # The three codes, and that they are three DISTINCT things. THE LITERALS ARE THE
    # POINT HERE and are deliberately not replaced by the very constants under test:
    # `EX_ERROR == diff_states.EX_ERROR` would be a tautology, whereas
    # `EX_ERROR == 2` pins the published constant to the documented status an operator
    # and every harness script agree on.
    assert diff_states.EX_IDENTICAL == 0
    assert diff_states.EX_DIFFERENT == 1
    assert diff_states.EX_ERROR == 2
    assert (
        len({diff_states.EX_IDENTICAL, diff_states.EX_DIFFERENT, diff_states.EX_ERROR})
        == 3
    ), (
        "the three exit statuses must remain distinct. Collapsing 2 into 0 would turn "
        "'the comparison could not be performed' into 'no differences found'."
    )

    # 0 MEANS ZERO BYTES. An identical comparison renders to the empty string, which is
    # what lets a passing stage write a zero-byte report.
    identical = diff_states.TreeDiff(tables=())
    assert identical.is_empty
    assert identical.total_differences == 0
    assert not identical
    assert diff_states.render(identical) == "", (
        "an identical comparison must render to the EMPTY STRING - Agent Action Plan "
        "section 0.8.5. A banner would make 'compared, and identical' "
        "indistinguishable from 'summarised' in a captured log."
    )

    # 1 MEANS A REAL DIFFERENCE, and it must render something an operator can act on.
    # One table present on the oracle side and absent on the migrated side is the
    # simplest structural finding there is; `PULEDGER-REC` is used because it is on this
    # scenario's list, and its primary key is read from the single inventory rather than
    # restated here.
    specification = harness.dump_tables.IN_SCOPE["PULEDGER-REC"]
    different = diff_states.TreeDiff(
        tables=(
            diff_states.TableDiff(
                table="PULEDGER-REC",
                primary_key=specification.primary_key,
                in_python=False,
            ),
        )
    )
    assert not different.is_empty
    assert different.total_differences == 1
    assert bool(different)
    assert different.differing == different.tables
    assert diff_states.render(different) != "", (
        "a real behavioural difference must render a report. Exit 1 is a FAILURE with "
        "evidence, and the evidence is what a reader diagnoses from."
    )

    # The two labels, fixed and not configurable.
    assert diff_states.LABEL_COBOL == "cobol"
    assert diff_states.LABEL_PYTHON == "python"
    assert tuple(harness.dump_tables.SIDES) == (
        diff_states.LABEL_COBOL,
        diff_states.LABEL_PYTHON,
    )

    # A tree must PROVE it was normalised before it can produce a verdict; the raw
    # escape hatch is a debugging aid whose result is not evidence.
    assert diff_states.NORMALIZED_SUFFIX in tuple(diff_states.NORMALIZED_SUFFIXES)


def test_dump_is_wellformed_on_both_sides(
    protocol: object, harness: object, frozen_schema: object
) -> None:
    """Both captures have the shape the protocol guarantees, for all ten tables.

    THE SHAPE, from `harness/dump_tables.py`'s `DUMP_KEYS`: EXACTLY FIVE KEYS IN FIXED
    INSERTION ORDER - `table`, `primary_key`, `columns`, `row_count`, `rows` - AND NO
    OTHERS. No timestamp, no server version, no scenario name and no side; THE SIDE IS
    RECORDED IN THE PATH. `columns` is in schema ordinal order and is never sorted;
    `rows` is a list of lists, positionally aligned to `columns`, in primary-key order.
    DECIMAL values are canonical JSON STRINGS at the declared scale - `format(value,
    "f")`, never `str`, so `Decimal("1E+2")` cannot reach a report as exponent notation
    - integers are JSON integers, and `bool` is refused outright because it would pass
    an integer check.

    WHY THIS TEST EXISTS AT ALL. Every one of those properties is an EXIT-2 CONDITION,
    and exit 2 is an ERROR rather than a failure. Asserting them explicitly, per table
    and per side, turns "the comparison could not be performed" into a diagnosis that
    names the offending table and side instead of a single opaque fault at stage 8.

    THE STRUCTURAL CONTRACT IS NOT REIMPLEMENTED. `harness/diff_states.py`'s public
    `load_dump` is the single definition of it - the five keys in order, the table in
    the 22-name allow-list, `primary_key` present in `columns`,
    `row_count == len(rows)`, every row of `len(columns)` values, no `float` (rule R-2),
    no `null`, no primary-key value twice, and the file name agreeing with the declared
    table. It is called first, per file, so a malformed capture fails naming its own
    path. What follows are the checks `load_dump` does NOT make: agreement with the
    frozen schema's ordinal order, and the per-kind value typing.

    ON KEY ORDER, STATED PRECISELY RATHER THAN OVERCLAIMED. The dump is
    `SELECT * FROM <table> ORDER BY <primary key>`, so MySQL's collation decides the
    order of a `char` key and Python's codepoint ordering need not agree with it -
    `utf8mb3_general_ci` is case-insensitive. Ascending order is therefore asserted only
    for INTEGER keys, where the two provably agree. For every key the strictly stronger
    and always-true property is asserted instead: THE TWO SIDES PRESENT THE IDENTICAL
    KEY SEQUENCE. That is what makes the captures byte-comparable, and it is what a
    scenario diff actually depends on - `diff_trees` aligns rows by primary-key VALUE
    and never by position, so a false assertion about collation here would fail a
    perfectly good capture.

    Args:
        protocol: The protocol object; it applies the stack skip.
        harness: The three harness modules.
        frozen_schema: `mysql/ACASDB.sql` parsed into `{table: {column: ColumnType}}`.
            READ, NEVER WRITTEN.

    Raises:
        Skipped: The Compose stack is unusable.
        Exception: A stage fault, or one of `harness/diff_states.py`'s own dump errors -
            every one of which is exit 2, a harness fault, and never a pass.
    """
    diff_states = harness.diff_states
    dump_tables = harness.dump_tables
    normalize = harness.normalize

    parity = protocol.run_scenario_parity(SCENARIO)
    paths = parity.paths

    for table in parity.tables:
        expected_columns = normalize.schema_columns(frozen_schema, table)
        specification = dump_tables.IN_SCOPE[table]
        key_sequences: dict[str, tuple[object, ...]] = {}

        for side in (diff_states.LABEL_COBOL, diff_states.LABEL_PYTHON):
            path = paths.normalized_dir(side) / diff_states.dump_filename(table)
            where = f"{side}/{table}"

            # The single definition of the structural contract. Raises on any exit-2
            # condition, naming the offending file.
            dump = diff_states.load_dump(path)

            # EXACTLY FIVE KEYS, IN FIXED ORDER, AND NO OTHERS.
            assert tuple(dump) == tuple(dump_tables.DUMP_KEYS), (
                f"{where}: a dump carries exactly {tuple(dump_tables.DUMP_KEYS)} in "
                f"that order and nothing else - no timestamp, no server version, no "
                f"scenario name and no side. The side is recorded in the PATH. Got "
                f"{tuple(dump)}."
            )
            assert dump["table"] == table
            assert dump["primary_key"] == specification.primary_key

            # `columns` MUST match the frozen schema's ordinal order EXACTLY, because
            # rows are POSITIONAL and a column list in any other order has no
            # meaningful alignment.
            columns = tuple(dump["columns"])
            assert columns == expected_columns, (
                f"{where}: the column list disagrees with the frozen schema. Rows are "
                f"positional, so any other order has no meaningful alignment. The "
                f"schema is frozen (Agent Action Plan section 0.8.1), so a "
                f"disagreement means the dump or the checkout is wrong, never the "
                f"schema."
            )
            assert len(columns) == specification.column_count, (
                f"{where}: {len(columns)} column(s) against the "
                f"{specification.column_count} mysql/ACASDB.sql declares at "
                f"[mysql/ACASDB.sql:L{specification.schema_line}]."
            )

            rows = dump["rows"]
            assert dump["row_count"] == len(rows), (
                f"{where}: row_count {dump['row_count']} against {len(rows)} row(s). "
                f"A dump whose count contradicts its content cannot produce a verdict."
            )

            # PER-KIND VALUE TYPING. This is what keeps rule R-2 enforceable at the
            # boundary: a DECIMAL that arrived as a JSON number would already have been
            # through binary floating point by the time anything compared it.
            for row_index, row in enumerate(rows):
                for column_name, value in zip(columns, row, strict=True):
                    declared = normalize.column_type(frozen_schema, table, column_name)
                    site = f"{where}[{row_index}].{column_name}"
                    assert value is not None, f"{site}: a null reached the protocol."
                    assert not isinstance(value, bool), (
                        f"{site}: a dump holds JSON integers and JSON strings only, "
                        f"and `bool` would pass an integer check because it subclasses "
                        f"`int`."
                    )
                    assert not isinstance(value, float), (
                        f"{site}: the binary floating-point value {value!r}. No "
                        f"accounting value may pass through binary floating point at "
                        f"any point (rule R-2)."
                    )
                    if declared.kind == normalize.KIND_INTEGER:
                        assert isinstance(value, int), (
                            f"{site}: `{declared.sql_type}` must arrive as a JSON "
                            f"integer, so that the integer truncation the COBOL relies "
                            f"on - anomaly A-8 in PULEDGER-REC - is reproducible."
                        )
                    else:
                        assert isinstance(value, str), (
                            f"{site}: `{declared.sql_type}` must arrive as a JSON "
                            f'STRING. DECIMAL is rendered with format(value, "f") at '
                            f"the DECLARED scale - which is not uniformly 2 - so a "
                            f"number here would mean the driver had already converted "
                            f"it."
                        )
                    if declared.kind == normalize.KIND_CHAR:
                        # Job 1 is `rstrip(" ")`, TRAILING ONLY, because a COBOL
                        # alphanumeric MOVE is left-justified with right padding, so
                        # LEADING SPACES ARE CONTENT. A normalised capture therefore has
                        # no trailing space left - which is what makes anomaly A-12's
                        # width drift invisible in a diff without hiding anything else.
                        assert value == value.rstrip(" "), (
                            f"{site}: a normalised char value carries no trailing "
                            f"space. Job 1 strips them on BOTH sides identically; a "
                            f"survivor means normalisation did not run."
                        )
                        assert len(value) <= (declared.width or len(value)), (
                            f"{site}: {len(value)} character(s) in a "
                            f"`{declared.sql_type}` column."
                        )

            key_index = columns.index(str(dump["primary_key"]))
            keys = tuple(row[key_index] for row in rows)
            assert len(set(keys)) == len(keys), (
                f"{where}: a primary-key value appears twice, so rows cannot be "
                f"aligned."
            )
            if keys and all(isinstance(key, int) for key in keys):
                # Only for integer keys, where MySQL's ORDER BY and Python's ordering
                # provably agree. See the docstring on why char keys are not claimed.
                assert list(keys) == sorted(keys), (
                    f"{where}: an integer primary key must be dumped ascending - the "
                    f"capture is `SELECT * FROM {table} ORDER BY "
                    f"{specification.primary_key}`."
                )
            key_sequences[side] = keys

        assert (
            key_sequences[diff_states.LABEL_COBOL]
            == key_sequences[diff_states.LABEL_PYTHON]
        ), (
            f"{table}: the two sides present DIFFERENT primary-key sequences, so the "
            f"captures are not byte-comparable. That is a behavioural difference in "
            f"which rows exist, and the bounded diff reports it in full - "
            f"{diff_states.render(parity.tree)}"
        )

    assert parity.is_empty, (
        f"both captures are well formed, but clean_batch_pl diverged: "
        f"{parity.tree.total_differences} finding(s).\n"
        f"{diff_states.render(parity.tree)}"
    )
