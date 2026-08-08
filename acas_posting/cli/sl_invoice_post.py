"""Sales transaction posting: `sl055`, then the `not = zero` gate, then `sl060`.

The batch entry point for `sales/sales.cbl` `load07.` L756-L768 and its dispatch
helper `load000.` L698-L712, with no screen output. The maintainer's own inline
comment on the label line reads "Sales trans posting"; `load08.` L770-L774 is a
different route (sl080, Payment Input) and is out of scope.

The gate here differs from the General Ledger's and both are preserved. Sales
tests `if ws-term-code not = zero go to display-menu` after each leg
[sales/sales.cbl:L761-L766], where General tests `= 5`
[general/general.cbl:L810-L811], and Purchase tests nothing at all - its
equivalent lines are commented out [purchase/purchase.cbl:L755-L758]. Unifying
the three would be a behaviour change.

The linkage is five parameters - ws-calling-data, system-record,
system-record-4, to-day, file-defs [sales/sl060.cbl:L395-L399] - passed through
`load000.`, which also carries the `< 8` / `> 7` disposition
[sales/sales.cbl:L691]. The IRS fan-out switch [copybooks/wssystem.cob:L179-L181]
decides which tables a run touches, so `--irs-instead` publishes it rather than
leaving it implicit.

The run date is an argument and never a clock reading (R-6): neither sl055 nor
sl060 reads a clock, both receive the date through linkage.

     Nothing else in sales/sales.cbl is annotated "Sales trans posting".
  2. `load08.` DISPATCHES A DIFFERENT AND OUT-OF-SCOPE PROGRAM::

         L770  load08.
         L773       move     "sl080" to ws-called.
         L774       go       to load00.

     `sl080` is Payment Input, which Agent Action Plan section 0.2.2 places
     explicitly out of scope.
  3. THE MENU-LETTER ORDINAL PROVES IT. Each menu accepts one character and
     resolves it to a paragraph by position - `go to load01 load02 ... depending
     on z` [sales/sales.cbl:L670] - so the Nth letter selects `loadNN`. The
     display block has `"(G)  Sales Transactions Post"` at
     [sales/sales.cbl:L545], and G is the SEVENTH letter, therefore `load07`.
     `"(H)  Payment Input"` at [sales/sales.cbl:L546] is the eighth, therefore
     `load08`, and `"(K)  Payment Post"` at [sales/sales.cbl:L549] is the
     eleventh, therefore `load11` - which is the sibling `sl_cash_post` route.
  4. TWO CHANGE-HISTORY ENTRIES NAME IT. ".32 Added execution of sl830 first when
     Invoice Post selected." [sales/sales.cbl:L121], matching the `sl830` head of
     `load07`; and, decisively, ".33 Call in load07 to 830 should have been using
     load00 not 000." [sales/sales.cbl:L124], in which the maintainer names
     `load07` AS the invoice-post paragraph and dates the very `perform load00`
     at L760 that stands there today.

Do not "correct" `load07` back to `load08`. The sibling package marker carries
the same note [acas_posting/cli/__init__.py], and so does the oracle driver
script - `'sl_invoice_post:sales:G:load07:sales/sales.cbl:L756-L768'`
[harness/run_cobol_scenario.sh ACAS_RUN_OPERATION_MAP].

THE ROUTE, VERBATIM FROM THE FROZEN SOURCE
::

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

Three properties of that paragraph are load-bearing and are preserved exactly:

  * `perform load000` at L764 RETURNS, so the gate at L765-L766 is reachable;
    `go to load000` at L768 does NOT return, so NO CODE MAY FOLLOW the final
    dispatch. `load07` therefore ends with its second dispatch and nothing else.
  * the two dispatches share ONE `WS-Calling-Data` and ONE pair of system
    records - only `WS-Called` changes between them - because COBOL passes group
    items by reference. One `SlPlLinkage` instance serves both, which is what
    lets `sl055`'s period-total writes reach `sl060`.
  * `sl830` is out of scope, so this route dispatches `sl055` -> gate ->
    `sl060` and the `load00` head of the chain (L759-L762) is not migrated. It is
    recorded as an omission in the footer rather than silently dropped, and the
    oracle driver script documents the same asymmetry under "THE sl830
    ASYMMETRY" [harness/run_cobol_scenario.sh acas_plan_sl_invoice_post].

THE DISPATCH HELPER, AND ITS FIVE PARAMETERS
Both in-scope dispatches go through `load000.`, the FIVE-parameter shape::

    L698  load000.
    L701       move     zero to ws-term-code.
    L702       call     ws-called using ws-calling-data
    L703                                System-Record
    L704                                WS-System-Record-4
    L705                                to-day
    L706                                file-defs
    L707       end-call
    L708       if       ws-term-code < 8  *> for sl055 & 060, xl150
    L709                perform overrewrite.
    L710       if       ws-term-code > 7      *> Got a serious (reported) error
    L711                perform overrewrite
    L712                goback.

FIVE, not four. The callee declares the same five, in the same order:
`procedure division using ws-calling-data / system-record / system-record-4 /
to-day / file-defs` [sales/sl060.cbl:L395-L399] and identically at
[sales/sl055.cbl:L271-L275]. What Shape 2 adds to the General Ledger's Shape 1
is exactly `WS-System-Record-4` - `SYSTOT-REC` [copybooks/wssys4.cob], the
period-totals record that this route's two programs write. Agent Action Plan
section 0.4.1.1 calls this "the four-parameter SL/PL linkage shape"; that is a
slip, recorded as CORRECTION 2 in the footer, and section 0.1.1 has it right -
"The Sales and Purchase families add the fourth system record".

The maintainer's own comment at L708 names the beneficiaries of this paragraph:
`*> for sl055 & 060, xl150`.

`< 8` AND `> 7` ARE EXHAUSTIVE, so `load000` ALWAYS performs `overrewrite`:
`WS-Term-Code` is `pic 99` [copybooks/wscall.cob:L10], domain 0 through 99, over
which the two tests are complementary. The `> 7` case additionally `goback`s,
which ends the RUN UNIT - the menu program itself stops.

FOUR GATE FORMS, DELIBERATELY NOT HARMONISED  (rule R-4)
The predicate here is `not = zero`, and it is not the predicate its siblings use.
The four forms the frozen source actually contains:

  Sales     `if ws-term-code not = zero / go to display-menu`
            [sales/sales.cbl:L765-L766] - ANY non-zero code stops the chain.
  General   `if ws-term-code = 5 / go to display-menu`
            [general/general.cbl:L810-L811] - an EQUALITY test against the one
            abort code `gl070` raises [general/gl070.cbl:L289].
  Purchase  NO PARAGRAPH-LEVEL GATE AT ALL. `load08.`
            [purchase/purchase.cbl:L752-L762] runs `pl055` through `load000` and
            falls straight into `pl060` with nothing tested in between.
  load000   `if ws-term-code > 7 / perform overrewrite / goback`
            [sales/sales.cbl:L710-L712] - a THRESHOLD test that ends the run unit
            instead of returning to the menu.

Harmonising any of them would be a behaviour change, and under rule R-4 a
behaviour change is a failure: "A defect reproduced is correct; a defect fixed is
a failure." Each form is reproduced where the source puts it.

THE FOURTH DIVERGENCE: THE GATE IS LIVE ONLY FOR CODES 1 THROUGH 7
`sl055` sets `WS-Term-Code` to EIGHT, and only ever to eight. Its one raise site
is the branch taken when the GnuCOBOL file-existence built-in it calls at
[sales/sl055.cbl:L336-L337] reports the analysis extract missing::

    sales/sl055.cbl
    L338       if    return-code not = zero
    L339             display  SL125  at 2301
    L340             display  SL002  at 2401
    L341             if     WS-Caller not = "xl150"
    L342                    accept WS-Reply at 2435
    L343             end-if
    L344             move 8 to WS-Term-Code
    L345             goback

Trace eight through `load000`: it is not `< 8`, and it IS `> 7`, so control takes
L710-L712 - `perform overrewrite`, then `goback` - and the menu PROGRAM ENDS.
The `not = zero` gate at L765-L766 is therefore NEVER REACHED for code eight. It
is reachable only for codes 1 through 7, which `sl055` never raises. A census of
every `move ... to ws-term-code` in the in-scope programs finds exactly three
raises: 5 at [general/gl070.cbl:L289], 8 at [sales/sl055.cbl:L344] and 8 at
[purchase/pl055.cbl:L286].

Three consequences, all encoded rather than reasoned away:

  * BOTH STOPS ARE IMPLEMENTED. The `> 7` stop belongs to `load000` and ends the
    run unit; the `not = zero` gate belongs to `load07` and returns to the menu.
    They are different dispositions in the source and both are written here.
  * THE GATE IS NOT SIMPLIFIED TO "if 8". The COBOL predicate is `not = zero`,
    so a code of 3 stops this chain exactly as a code of 8 does.
  * THE SALES-VERSUS-PURCHASE DIVERGENCE LIVES ENTIRELY IN THE 1..7 BAND. Sales
    returns to the menu for any non-zero code at or below seven; Purchase, having
    no gate, would proceed to `pl060`. Because `sl055` and `pl055` only ever raise
    eight the difference is currently unobservable - but it is reproduced anyway,
    because any other code in that band would diverge.

THE CLOCK CONTRACT  (rule R-6)
The run date enters this route ONCE, as the REQUIRED `--run-date` option, and
reaches the two programs only through the linkage. Nothing here reads a system
clock, an elapsed-time counter, an environment variable or an entropy source, and
neither do the twelve in-scope posting programs. The frozen call chain holds
FOURTEEN ambient date and time reads across six files - six `FUNCTION
CURRENT-DATE` [common/ACAS.cbl:L353], [general/general.cbl:L371],
[sales/sales.cbl:L323], [purchase/purchase.cbl:L318], [irs/irs.cbl:L480],
[copybooks/Proc-ACAS-Mapser-RDB.cob:L72], four `accept ... from time` and four
`accept ... from date` - and EVERY ONE of them is in an out-of-scope menu shell or
in the date-service copybook those shells COPY, as the census in
`acas_posting/clock.py` records. The one that matters to a posting run is
[copybooks/Proc-ACAS-Mapser-RDB.cob:L72-L80], which builds `to-day` at L77 and
stores the binary `run-date` at L80 - and even that runs only on the FIRST-TIME
capture path `ba010-Capture-Data`; a normal Sales run takes `to-day` from the
STORED `Run-Date` - `move run-date to u-bin` / `call "maps04"` / `move u-date to
to-day` [sales/sales.cbl:L409-L411]. Both observables are pinned by
`acas_posting.clock` through `acas_posting.cli.args.resolve_clock`, so two runs of
one scenario are byte-identical (Agent Action Plan section 0.8.5).

PIN `--irs-instead` EXPLICITLY ON THIS ROUTE
`SYSTEM-REC IRS-Instead pic x` [copybooks/wssystem.cob:L179] with its two
condition names, `88 IRS-Used value "Y"` at L180 and `88 IRS-Both-Used value "B"`
at L181, decides WHICH TABLES the run touches: `sl060` reads it at three sites -
[sales/sl060.cbl:L1039], [sales/sl060.cbl:L1126] and [sales/sl060.cbl:L1175] -
to choose between the General Ledger posting tables, the IRS posting table, or
both. Agent Action Plan section 0.6.4 therefore requires every scenario to pin it
explicitly, "since leaving it out makes the affected-table list ambiguous". The
option comes from `args.add_slpl_linkage_arguments` and is not redefined here.

WHAT THIS MODULE MAY AND MAY NOT IMPORT
MAY, and does: `argparse`, `enum`, `logging`, `collections.abc`, `typing`;
`acas_posting.cli.args`; and the two program modules this route dispatches. The
per-directory import table of Agent Action Plan section 0.4.3 allows `cli/*.py`
exactly `programs`, `clock` and `cli.args`.

MAY NOT, and does not: the data-access layer including its facade, the record
layer, the COBOL-semantics package, the dictionary package, the work-file module,
and the compiled comparison oracle's own tree. (The forbidden names are given in
prose here on purpose: this module states its constraints without spelling any
banned import, so that the mechanical greps a reviewer runs over it come back
empty rather than needing to be read.) Two consequences are visible in the code
rather than merely promised:

  * `acas_posting.clock` is PERMITTED but NOT IMPORTED, because it is already
    reached through `args.bind_slpl_linkage` -> `args.resolve_clock`. An import
    this module did not use would be dead weight, and the clock contract is not
    weakened by routing through the one module whose job is binding.
  * the private dispatch protocol types its five record parameters as `Any`. The
    record classes would name those types exactly, but the record layer is
    outside this layer's whitelist, and `args` deliberately does not re-export
    them. The five parameter NAMES carry the shape instead, and the real types are
    enforced where they belong - in `args.SlPlLinkage`, whose members this module
    splats without touching.

NO IMPORT-TIME SIDE EFFECTS
Importing this module binds names and creates one logger. It builds no parser,
configures no logging, opens no file or connection, reads nothing from its
surroundings and cannot fail for an environmental reason. `logging.basicConfig`
is not called here AT ALL - the whole package has one call to it, in
`acas_posting.__main__.configure_logging`, reached only from a process boundary -
so neither importing this module nor calling `main` as a library reconfigures a
host application's logging. That is a hard requirement: the scenario test suites
import this package.

NEITHER CALLEE'S FAILURE IS TRANSLATED
Two exceptions can leave this module, and both are allowed to propagate
deliberately:

  * `sl055` raises `CobolFileSystemPathUnavailable` when
    `FS-Cobol-Files-Used` is true, having first set `WS-Term-Code` to eight per
    [sales/sl055.cbl:L344]. It raises because the three sub-outcomes of the
    file-existence block [sales/sl055.cbl:L336-L346] cannot be told apart
    without running COBOL, which rule R-1 forbids. Catching it here and returning
    eight would PICK one of those three outcomes - a behaviour change dressed as
    a migration - so it is not caught.
  * `args.bind_slpl_linkage` raises `RdbmsParamError` when the deployment
    contract for the six connection parameters is absent or unusable. `args`
    states the contract: deliberately not caught, because a run that cannot reach
    the provisioned database must stop BEFORE it writes anything.

Neither is a COBOL disposition, so neither is mapped onto a `WS-Term-Code`. They
end the process loudly and before any posting, which is the only faithful
outcome available.

THE RULES THAT BIND THIS FILE
`review_rules` reports NO user rules document for this project, so the binding
constraints are the Agent Action Plan's own six (section 0.7.2), and enterprise
best practice applies wherever they are silent. The per-rule verdict is in the
footer; in outline:

R-1 No COBOL at run time. Nothing here spawns a child process, loads a foreign
    library or reaches the GnuCOBOL toolchain; there is no import path from this
    package to the compiled oracle's tree, and no option selects, invokes or
    diffs against that oracle - the oracle's own scripts drive this entry point
    from outside, never the reverse.
R-2 Zero binary floating point. `WS-Term-Code` is an `int` (`pic 99`), `to-day`
    is a `str`, and no binary-radix numeric type appears anywhere - in a
    signature, an option type or an expression. No arithmetic is performed here.
R-3 No added validation, no added field, no schema change, no concurrency. In
    particular there is NO "does the extract file exist?" pre-check here: that
    test lives inside `sl055` [sales/sl055.cbl:L336-L346] and duplicating it
    would be a validation this migration may not add. There is no worker, pool
    or event loop to configure and no option that would create one, so the two
    programs run one at a time with the gate between them.
R-4 Legacy behaviour is reproduced, never corrected - see the four gate forms
    above. Each reproduction below carries its COBOL locator in a comment, as
    section 0.7.4 C-4 requires.
R-5 Full traceability: paragraph-named functions, a `GO TO` class at every
    transfer site, and the mandatory footer.
R-6 Compiled behaviour is the tie-breaker, so the clock is injected, the run date
    is a required argument, and the three open questions are marked in place
    rather than guessed.
==========================================
::

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

Three properties of that paragraph are load-bearing and are preserved exactly:

  * `perform load000` at L764 RETURNS, so the gate at L765-L766 is reachable;
    `go to load000` at L768 does NOT return, so NO CODE MAY FOLLOW the final
    dispatch. `load07` therefore ends with its second dispatch and nothing else.
  * the two dispatches share ONE `WS-Calling-Data` and ONE pair of system
    records - only `WS-Called` changes between them - because COBOL passes group
    items by reference. One `SlPlLinkage` instance serves both, which is what
    lets `sl055`'s period-total writes reach `sl060`.
  * `sl830` is out of scope, so this route dispatches `sl055` -> gate ->
    `sl060` and the `load00` head of the chain (L759-L762) is not migrated. It is
    recorded as an omission in the footer rather than silently dropped, and the
    oracle driver script documents the same asymmetry under "THE sl830
    ASYMMETRY" [harness/run_cobol_scenario.sh:L332-L336].

THE DISPATCH HELPER, AND ITS FIVE PARAMETERS
============================================
Both in-scope dispatches go through `load000.`, the FIVE-parameter shape::

    L698  load000.
    L701       move     zero to ws-term-code.
    L702       call     ws-called using ws-calling-data
    L703                                System-Record
    L704                                WS-System-Record-4
    L705                                to-day
    L706                                file-defs
    L707       end-call
    L708       if       ws-term-code < 8  *> for sl055 & 060, xl150
    L709                perform overrewrite.
    L710       if       ws-term-code > 7      *> Got a serious (reported) error
    L711                perform overrewrite
    L712                goback.

FIVE, not four. The callee declares the same five, in the same order:
`procedure division using ws-calling-data / system-record / system-record-4 /
to-day / file-defs` [sales/sl060.cbl:L395-L399] and identically at
[sales/sl055.cbl:L271-L275]. What Shape 2 adds to the General Ledger's Shape 1
is exactly `WS-System-Record-4` - `SYSTOT-REC` [copybooks/wssys4.cob], the
period-totals record that this route's two programs write. Agent Action Plan
section 0.4.1.1 calls this "the four-parameter SL/PL linkage shape"; that is a
slip, recorded as CORRECTION 2 in the footer, and section 0.1.1 has it right -
"The Sales and Purchase families add the fourth system record".

The maintainer's own comment at L708 names the beneficiaries of this paragraph:
`*> for sl055 & 060, xl150`.

`< 8` AND `> 7` ARE EXHAUSTIVE, so `load000` ALWAYS performs `overrewrite`:
`WS-Term-Code` is `pic 99` [copybooks/wscall.cob:L10], domain 0 through 99, over
which the two tests are complementary. The `> 7` case additionally `goback`s,
which ends the RUN UNIT - the menu program itself stops.

FOUR GATE FORMS, DELIBERATELY NOT HARMONISED  (rule R-4)
========================================================
The predicate here is `not = zero`, and it is not the predicate its siblings use.
The four forms the frozen source actually contains:

  Sales     `if ws-term-code not = zero / go to display-menu`
            [sales/sales.cbl:L765-L766] - ANY non-zero code stops the chain.
  General   `if ws-term-code = 5 / go to display-menu`
            [general/general.cbl:L810-L811] - an EQUALITY test against the one
            abort code `gl070` raises [general/gl070.cbl:L289].
  Purchase  NO PARAGRAPH-LEVEL GATE AT ALL. `load08.`
            [purchase/purchase.cbl:L752-L762] runs `pl055` through `load000` and
            falls straight into `pl060` with nothing tested in between.
  load000   `if ws-term-code > 7 / perform overrewrite / goback`
            [sales/sales.cbl:L710-L712] - a THRESHOLD test that ends the run unit
            instead of returning to the menu.

Harmonising any of them would be a behaviour change, and under rule R-4 a
behaviour change is a failure: "A defect reproduced is correct; a defect fixed is
a failure." Each form is reproduced where the source puts it.

THE FOURTH DIVERGENCE: THE GATE IS LIVE ONLY FOR CODES 1 THROUGH 7
==================================================================
`sl055` sets `WS-Term-Code` to EIGHT, and only ever to eight. Its one raise site
is the branch taken when the GnuCOBOL file-existence built-in it calls at
[sales/sl055.cbl:L336-L337] reports the analysis extract missing::

    sales/sl055.cbl
    L338       if    return-code not = zero
    L339             display  SL125  at 2301
    L340             display  SL002  at 2401
    L341             if     WS-Caller not = "xl150"
    L342                    accept WS-Reply at 2435
    L343             end-if
    L344             move 8 to WS-Term-Code
    L345             goback

Trace eight through `load000`: it is not `< 8`, and it IS `> 7`, so control takes
L710-L712 - `perform overrewrite`, then `goback` - and the menu PROGRAM ENDS.
The `not = zero` gate at L765-L766 is therefore NEVER REACHED for code eight. It
is reachable only for codes 1 through 7, which `sl055` never raises. A census of
every `move ... to ws-term-code` in the in-scope programs finds exactly three
raises: 5 at [general/gl070.cbl:L289], 8 at [sales/sl055.cbl:L344] and 8 at
[purchase/pl055.cbl:L286].

Three consequences, all encoded rather than reasoned away:

  * BOTH STOPS ARE IMPLEMENTED. The `> 7` stop belongs to `load000` and ends the
    run unit; the `not = zero` gate belongs to `load07` and returns to the menu.
    They are different dispositions in the source and both are written here.
  * THE GATE IS NOT SIMPLIFIED TO "if 8". The COBOL predicate is `not = zero`,
    so a code of 3 stops this chain exactly as a code of 8 does.
  * THE SALES-VERSUS-PURCHASE DIVERGENCE LIVES ENTIRELY IN THE 1..7 BAND. Sales
    returns to the menu for any non-zero code at or below seven; Purchase, having
    no gate, would proceed to `pl060`. Because `sl055` and `pl055` only ever raise
    eight the difference is currently unobservable - but it is reproduced anyway,
    because any other code in that band would diverge.

THE CLOCK CONTRACT  (rule R-6)
==============================
The run date enters this route ONCE, as the REQUIRED `--run-date` option, and
reaches the two programs only through the linkage. Nothing here reads a system
clock, an elapsed-time counter, an environment variable or an entropy source, and
neither do the twelve in-scope posting programs. The frozen call chain holds
FOURTEEN ambient date and time reads across six files - six `FUNCTION
CURRENT-DATE` [common/ACAS.cbl:L353], [general/general.cbl:L371],
[sales/sales.cbl:L323], [purchase/purchase.cbl:L318], [irs/irs.cbl:L480],
[copybooks/Proc-ACAS-Mapser-RDB.cob:L72], four `accept ... from time` and four
`accept ... from date` - and EVERY ONE of them is in an out-of-scope menu shell or
in the date-service copybook those shells COPY, as the census in
`acas_posting/clock.py` records. The one that matters to a posting run is
[copybooks/Proc-ACAS-Mapser-RDB.cob:L72-L80], which builds `to-day` at L77 and
stores the binary `run-date` at L80 - and even that runs only on the FIRST-TIME
capture path `ba010-Capture-Data`; a normal Sales run takes `to-day` from the
STORED `Run-Date` - `move run-date to u-bin` / `call "maps04"` / `move u-date to
to-day` [sales/sales.cbl:L409-L411]. Both observables are pinned by
`acas_posting.clock` through `acas_posting.cli.args.resolve_clock`, so two runs of
one scenario are byte-identical (Agent Action Plan section 0.8.5).

PIN `--irs-instead` EXPLICITLY ON THIS ROUTE
============================================
`SYSTEM-REC IRS-Instead pic x` [copybooks/wssystem.cob:L179] with its two
condition names, `88 IRS-Used value "Y"` at L180 and `88 IRS-Both-Used value "B"`
at L181, decides WHICH TABLES the run touches: `sl060` reads it at three sites -
[sales/sl060.cbl:L1039], [sales/sl060.cbl:L1126] and [sales/sl060.cbl:L1175] -
to choose between the General Ledger posting tables, the IRS posting table, or
both. Agent Action Plan section 0.6.4 therefore requires every scenario to pin it
explicitly, "since leaving it out makes the affected-table list ambiguous". The
option comes from `args.add_slpl_linkage_arguments` and is not redefined here.

WHAT THIS MODULE MAY AND MAY NOT IMPORT
=======================================
MAY, and does: `argparse`, `enum`, `logging`, `collections.abc`, `typing`;
`acas_posting.cli.args`; and the two program modules this route dispatches. The
per-directory import table of Agent Action Plan section 0.4.3 allows `cli/*.py`
exactly `programs`, `clock` and `cli.args`.

MAY NOT, and does not: the data-access layer including its facade, the record
layer, the COBOL-semantics package, the dictionary package, the work-file module,
and the compiled comparison oracle's own tree. (The forbidden names are given in
prose here on purpose: this module states its constraints without spelling any
banned import, so that the mechanical greps a reviewer runs over it come back
empty rather than needing to be read.) Two consequences are visible in the code
rather than merely promised:

  * `acas_posting.clock` is PERMITTED but NOT IMPORTED, because it is already
    reached through `args.bind_slpl_linkage` -> `args.resolve_clock`. An import
    this module did not use would be dead weight, and the clock contract is not
    weakened by routing through the one module whose job is binding.
  * the private dispatch protocol types its five record parameters as `Any`. The
    record classes would name those types exactly, but the record layer is
    outside this layer's whitelist, and `args` deliberately does not re-export
    them. The five parameter NAMES carry the shape instead, and the real types are
    enforced where they belong - in `args.SlPlLinkage`, whose members this module
    splats without touching.

NO IMPORT-TIME SIDE EFFECTS
===========================
Importing this module binds names and creates one logger. It builds no parser,
configures no logging, opens no file or connection, reads nothing from its
surroundings and cannot fail for an environmental reason. `logging.basicConfig`
is not called here AT ALL - the whole package has one call to it, in
`acas_posting.__main__.configure_logging`, reached only from a process boundary -
so neither importing this module nor calling `main` as a library reconfigures a
host application's logging. That is a hard requirement: the scenario test suites
import this package.

CALLEE FAILURE IS NOT TRANSLATED; THE CONFIGURATION CONTRACT IS
===============================================================
  * `sl055` raises `CobolFileSystemPathUnavailable` when
    `FS-Cobol-Files-Used` is true, having first set `WS-Term-Code` to eight per
    [sales/sl055.cbl:L344]. It raises because the three sub-outcomes of the
    file-existence block [sales/sl055.cbl:L336-L346] cannot be told apart
    without running COBOL, which rule R-1 forbids. Catching it here and returning
    eight would PICK one of those three outcomes - a behaviour change dressed as
    a migration - so it is NOT caught. It is not a COBOL disposition, so it is not
    mapped onto a `WS-Term-Code` either; it ends the process loudly and before any
    posting, which is the only faithful outcome available.
  * `RdbmsParamError` - the deployment contract for the six connection parameters
    being absent or unusable - IS caught, in `main`, and only that exact type
    (finding CLI-09). `args.report_configuration_failure` turns it into the one
    documented status the whole package shares: 8 when the contract is absent, 1
    when it is present but unusable. This is not a softening of the previous
    "stop before it writes anything" contract, it is that contract made uniform
    and diagnosable - the failure is raised while the six parameters are being
    resolved, BEFORE the system store is opened, so nothing has been written when
    it surfaces. What is deliberately NOT caught is `ValueError` at large: a
    genuine defect must keep its traceback.

THE RULES THAT BIND THIS FILE
=============================
`review_rules` reports NO user rules document for this project, so the binding
constraints are the Agent Action Plan's own six (section 0.7.2), and enterprise
best practice applies wherever they are silent. The per-rule verdict is in the
footer; in outline:

R-1 No COBOL at run time. Nothing here spawns a child process, loads a foreign
    library or reaches the GnuCOBOL toolchain; there is no import path from this
    package to the compiled oracle's tree, and no option selects, invokes or
    diffs against that oracle - the oracle's own scripts drive this entry point
    from outside, never the reverse.
R-2 Zero binary floating point. `WS-Term-Code` is an `int` (`pic 99`), `to-day`
    is a `str`, and no binary-radix numeric type appears anywhere - in a
    signature, an option type or an expression. No arithmetic is performed here.
R-3 No added validation, no added field, no schema change, no concurrency. In
    particular there is NO "does the extract file exist?" pre-check here: that
    test lives inside `sl055` [sales/sl055.cbl:L336-L346] and duplicating it
    would be a validation this migration may not add. There is no worker, pool
    or event loop to configure and no option that would create one, so the two
    programs run one at a time with the gate between them.
R-4 Legacy behaviour is reproduced, never corrected - see the four gate forms
    above. Each reproduction below carries its COBOL locator in a comment, as
    section 0.7.4 C-4 requires.
R-5 Full traceability: paragraph-named functions, a `GO TO` class at every
    transfer site, and the mandatory footer.
R-6 Compiled behaviour is the tie-breaker, so the clock is injected, the run date
    is a required argument, and the three open questions are marked in place
    rather than guessed.
"""

from __future__ import annotations

import argparse
import enum
import logging
from collections.abc import Sequence
from typing import Any, Final, Protocol

from acas_posting.cli import args
from acas_posting.programs import sl055_invoice_extract_analysis, sl060_invoice_posting

__all__: Final[tuple[str, ...]] = ("main", "load000", "load07")

# Diagnostics only.
_LOG: Final[logging.Logger] = logging.getLogger(__name__)


# Named constants rather than inline literals so that the `move` each one reproduces has
# one spelling and one locator.
_PROGRAM_SL055: Final[str] = "sl055"
_PROGRAM_SL060: Final[str] = "sl060"

# R-4 [sales/sales.cbl:L765] - the figurative constant ZERO of `if ws-term-code not =
# zero`.
_WS_TERM_CODE_ZERO: Final[int] = args.WS_TERM_CODE_DEFAULT


class _Stop(enum.Enum):
    """The two DIFFERENT dispositions that stop this route, named.

    The source contains both and they are not the same event, so each has a name here
    rather than living only in a comment (rule R-5).

    Attributes:
        RUN_UNIT_ENDED: `if ws-term-code > 7 / perform overrewrite / goback`
            [sales/sales.cbl:L710-L712], decided INSIDE `load000`. `goback` from the
            menu's own paragraph ends the RUN UNIT.
        RETURNED_TO_MENU: `if ws-term-code not = zero / go to display-menu`
            [sales/sales.cbl:L765-L766], decided in `load07`. The menu is redrawn and
            awaits the next selection.
    """

    RUN_UNIT_ENDED = "run unit ended (perform overrewrite / goback)"
    RETURNED_TO_MENU = "returned to the menu (go to display-menu)"


class _SlPlPostingProgram(Protocol):
    """What `call ws-called` dispatches: a program module exposing `run`.

    * the dispatch is late-bound, exactly as a dynamic `CALL` is; and * a caller cannot
    reach into a program's internals, because a program module publishes `run` and
    nothing else - `__all__ = ("run",)` in both
    [acas_posting/programs/sl055_invoice_extract_analysis.py] and
    [acas_posting/programs/sl060_invoice_posting.py].
    """

    def run(
        self,
        ws_calling_data: Any,
        system_record: Any,
        system_record_4: Any,
        to_day: str,
        file_defs: Any,
        *,
        open_item_file_2: Any = None,
    ) -> Any:
        """Run the program over the five-parameter Sales/Purchase linkage.

        `open_item_file_2` is NOT a sixth linkage parameter. It is the OTM2 work
        file - `select open-item-file-2 assign file-18` [copybooks/seloi2.cob] -
        which `sl055` writes [sales/sl055.cbl:L681] and `sl060` reads
        [sales/sl060.cbl:L484]. In COBOL both programs name the same `ASSIGN` and
        the operating system supplies the identity; the frozen
        `PROCEDURE DIVISION USING` still has exactly five entries, so the carrier
        is keyword-only, outside the positional list - the same device the three
        General Ledger phases use for `pre-trans` and `post-trans`.

        The return value is that carrier when the program produced one, and None
        otherwise. `sl055` returns the file it wrote; `sl060` has nothing new to
        hand on and returns None.
        """
        ...  # pragma: no cover - a Protocol member has no body to execute


class _ExtractChannel:
    """The ONE OTM2 work file `sl055` and `sl060` share.

    Not a linkage parameter and not a table. It stands in for what the compiled
    programs use instead: their own FILE SECTIONs over one transient work file
    that persists between the two `CALL`s, `file-18` alias `"openitm2"`
    [copybooks/wsnames.cob:L35]. Nothing about it reaches the database, so nothing
    about it appears in a table dump.

    WHY A HOLDER RATHER THAN A LOCAL. The file has to outlive the first dispatch
    and reach the second, because that is how the two programs communicate:
    `sl055` opens it for EXTEND [sales/sl055.cbl:L359], appends one header per
    invoice [sales/sl055.cbl:L681] and closes it [sales/sl055.cbl:L501]; `sl060`
    then opens THE SAME FILE for INPUT [sales/sl060.cbl:L480] and reads those
    headers back [sales/sl060.cbl:L484]. Threading it through a holder keeps
    `load000` returning the term code that `load07.` reads, while still letting
    the file the FIRST dispatch produced reach the second.

    WHY NOT A MODULE-LEVEL DEFAULT. `acas_posting/workfiles.py` deliberately
    declares a fresh file on every request and caches nothing, so that one run's
    records cannot leak into the next; a shared carrier at module scope would
    break rule R-6's byte-identical-reruns guarantee silently. This holder is
    created per call to `load07`, which preserves that property.

    WHO CREATES THE FILE. Not this class. `sl055.run` declares one when it is
    passed None and RETURNS it, so the first dispatch both produces the file and
    fills it; `load000` captures the returned value here and the second dispatch
    receives it. That is why this holder starts empty and why the type is
    `object`: the concrete class lives in `acas_posting/workfiles.py`, which a
    `cli` module may not import (Agent Action Plan section 0.4.3), and it never
    needs to - the carrier is only ever carried, never inspected.

    Attributes:
        carrier: the OTM2 work file once a dispatch has produced it, and None
            before that. Passed to every dispatch as-is: a None means "you
            declare it", which is exactly what each program module's own
            `open_item_file_2=None` default means.
    """

    __slots__ = ("carrier",)

    def __init__(self) -> None:
        """Start with no file. The first dispatch produces one."""
        self.carrier: object | None = None


def _perform_overrewrite(
    linkage: args.SlPlLinkage,
    menu_state: args.MenuState,
    *,
    program_id: str,
    term_code: int,
) -> None:
    """`perform overrewrite` [sales/sales.cbl:L709, :L711] - reproduced.

    THE STATEMENT IS REACHED AND ITS EFFECT IS NOW REPRODUCED. `overrewrite.`
    [sales/sales.cbl:L628-L658] opens the system parameter file, rewrites key 1
    (`SYSTEM-REC`) and key 4 (`SYSTOT-REC`) to the RDB and then again to the Cobol
    file, and closes - falling through `overclose.` [sales/sales.cbl:L659] to its
    `goback` at L660. The paragraph itself lives ONCE, in
    `acas_posting.cli.args.overrewrite`, shared by all seven routes; this wrapper
    exists only to keep the log record and the citation next to the two call sites
    that reach it.

    IT MATTERS ON THIS ROUTE MORE THAN ON ANY OTHER. `sl055` and `sl060` make four
    of the nine period-total writes of the whole migration -
    [sales/sl055.cbl:L675] and [sales/sl055.cbl:L677], [sales/sl060.cbl:L641] and
    [sales/sl060.cbl:L700] - and every one of them lands in the linkage record
    `SYSTOT-REC` is read from and written to. `overrewrite` is their ONLY writer to
    the store, so without it a Python run leaves SYSTOT-REC exactly as the seed
    left it while a COBOL run advances it, and Agent Action Plan section 0.8.5's
    empty diff is unreachable. That is why the earlier reading of this site as an
    omission could not stand.

    WHAT IS STILL NOT REPRODUCED is that paragraph's COBOL-FILE arm
    [sales/sales.cbl:L644-L657]: the migration has one store, so only the RDB arm
    has a counterpart. Recorded at `args.RDBMS_STORE_SELECTOR_DIGIT`.

    Args:
        linkage: the five `CALL` arguments. `system_record` is rewritten under key
            1 and - through `menu_state` - `system_record_4` under key 4. The two
            are the SAME objects the dispatch just mutated, which is the whole
            point: `SlPlLinkage.system_record_4` IS `menu_state.system_record_4`,
            established by `args.bind_slpl_linkage`.
        menu_state: the menu's own WORKING-STORAGE, carrying the totals record and
            the `File-Access` block every verb writes its status into.
        program_id: the program-id just dispatched, for the log record only.
        term_code: `WS-Term-Code` as the callee left it, for the log record only.

    Raises:
        acas_posting.dal.facade.FacadeGoback: never from this entity - the
            entity-named `System-*` verbs carry no error check
            [copybooks/Proc-ACAS-FH-Calls.cob:L190-L230].
    """
    _LOG.debug(
        "overrewrite after %s (WS-Term-Code %d): persisting SYSTEM-REC and "
        "SYSTOT-REC [sales/sales.cbl:L628-L658]",
        program_id.strip(),
        term_code,
    )
    args.overrewrite(linkage.system_record, menu_state, linkage.file_defs)


def _log_stop(stop: _Stop, *, program_id: str, term_code: int) -> None:
    """Report which of the two stops fired, at a severity matching its intent.

    `WARNING` rather than `ERROR`: neither stop is an error of this module's making, and
    the callee has already reported whatever went wrong - `sl055` logs its own `SL125`
    before raising, for instance.

    Args:
        stop: which disposition the source takes at this site.
        program_id: the program-id whose term code caused the stop.
        term_code: the deciding `WS-Term-Code`.
    """
    # "no further program is dispatched" rather than "sl060 is not dispatched".
    _LOG.warning(
        "%s left WS-Term-Code %d: %s; no further program is dispatched",
        program_id.strip(),
        term_code,
        stop.value,
    )


def load000(
    linkage: args.SlPlLinkage,
    program_id: str,
    program: _SlPlPostingProgram,
    *,
    menu_state: args.MenuState,
    channel: _ExtractChannel | None = None,
) -> int:
    """`load000.` [sales/sales.cbl:L698-L712] - the five-parameter dispatch.

    The `< 8` and `> 7` tests are written as the source writes them - two separate
    statements, not a two-armed conditional - because that is what they are, and because
    `WS-Term-Code pic 99` [copybooks/wscall.cob:L10] makes them exhaustive over 0..99.

    Args:
        linkage: the five arguments in COBOL parameter order
            [sales/sl060.cbl:L395-L399]. Mutated: `WS-Term-Code` is cleared and
            `WS-Called` is set before the dispatch, and the callee writes back
            into the same records, which is what COBOL linkage by reference does.
            ONE instance serves both dispatches of `load07`.
        program_id: the program-id to move into `WS-Called` - `"sl055"` or
            `"sl060"` here.
        program: the program module to dispatch. `run` is read off it at call
            time, so the dispatch is late-bound exactly as `call ws-called` is.
        menu_state: the menu's own WORKING-STORAGE, which `overrewrite`
            persists on both arms below. Its
            `system_record` and `system_record_4` are the SAME instances the
            linkage carries, so no copy-back is needed - the callee wrote into
            them by reference, exactly as COBOL linkage does.

    Returns:
        `WS-Term-Code` as the callee left it, which is also readable from
            `linkage.calling_data.ws_term_code`. The caller MUST NOT dispatch anything
            further when `args.is_serious_error` is true of it.

    Raises:
        Nothing of its own.
    """
    calling_data = linkage.calling_data

    # R-4 [sales/sales.cbl:L701] `move zero to ws-term-code.` PER DISPATCH, not once per
    # run. The placement is load-bearing rather than tidy.
    args.reset_term_code(calling_data)

    # R-4 [sales/sales.cbl:L763] and [sales/sales.cbl:L767] `move "sl055" to ws-called.`
    # / `move "sl060" to ws-called.` HOISTED from the two call sites into this function,
    # which is where the program-id arrives, because this function IS `call ws-called` -
    # the dispatch takes the program-id as an argument where the COBOL reads it back out
    # of the field.
    args.set_called(calling_data, program_id)

    _LOG.info(
        "dispatching %s over the five-parameter Sales/Purchase linkage "
        "[sales/sales.cbl:L702-L707]",
        program_id.strip(),
    )

    #  [sales/sales.cbl:L702-L707] `call ws-called using ws-calling-data /
    #  System-Record / WS-System-Record-4 / to-day / file-defs`.
    #  FIVE positional arguments in COBOL parameter order, and no others: the
    #  splat of a five-member NamedTuple makes an arity mistake a TypeError at
    #  this line rather than a silently mis-ordered posting. `sl055` also
    #  publishes a keyword-only facade seam; the COBOL `CALL` passes none, so it
    #  is not passed here.
    #
    #  THE ONE KEYWORD THAT IS PASSED IS THE OTM2 FILE, and it is not a parameter
    #  of the `CALL` at all - it is the migration's stand-in for the two programs
    #  naming the same `assign file-18`. See `_ExtractChannel`.
    returned = (
        program.run(*linkage)
        if channel is None
        else program.run(*linkage, open_item_file_2=channel.carrier)
    )

    #  The one conditional that is a Python-language necessity rather than a test
    #  of any value the COBOL tests. `sl055.run` returns the OTM2 file - the
    #  migration's equivalent of naming the same file in the next program's
    #  `SELECT` - while `sl060.run` returns None because it has nothing new to
    #  hand on. Capturing the first is what lets [sales/sl060.cbl:L484] read what
    #  [sales/sl055.cbl:L681] wrote.
    if channel is not None and returned is not None:
        channel.carrier = returned

    term_code = calling_data.ws_term_code

    #  R-4 [sales/sales.cbl:L708-L709] `if ws-term-code < 8 / perform overrewrite.`
    #  `not is_serious_error(...)` IS `ws-term-code < 8` over the whole `pic 99`
    #  domain, which the sibling helper's own docstring states. The maintainer's
    #  comment at L708 names this route's programs: `*> for sl055 & 060, xl150`.
    #  The effect of `overrewrite` IS reproduced - see `_perform_overrewrite`.
    if not args.is_serious_error(term_code):
        _perform_overrewrite(
            linkage, menu_state, program_id=program_id, term_code=term_code
        )

    #  R-4 [sales/sales.cbl:L710-L712] `if ws-term-code > 7 / perform overrewrite
    #  / goback.`  A SECOND, SEPARATE `if`, as the source has it.
    #
    #  GO TO class 4 (sibling re-dispatch), per-site proof:
    #    COBOL:  `perform overrewrite` returns, then `goback` ends the RUN UNIT -
    #            the menu program stops, so no further program is dispatched and
    #            no menu is redrawn.
    #    Python: `overrewrite` runs, the stop is logged, and the term code is
    #            returned for the caller to honour; `main` then leaves the process
    #            with `args.exit_status_for(...)`.
    #    Proof:  the set of programs invoked is identical, the persistence happens
    #            on both sides, and control never re-enters the dispatch paragraph
    #            in either version. The only difference is the process exit
    #            status, which the COBOL has no equivalent of at all
    #            (Q-CLI-EXITSTATUS, settled in `args.exit_status_for`).
    #
    #  DIVERGENCE FROM PURCHASE, PRESERVED. Sales writes `perform overrewrite`
    #  and then `goback` [sales/sales.cbl:L710-L712]; Purchase writes
    #  `go to overrewrite` [purchase/purchase.cbl:L703-L704], which reaches the
    #  same paragraph and falls through `overclose.` to the same `goback`. The
    #  net effect is identical - persist, then end the run unit - but the
    #  mechanism differs, and rule R-4 forbids harmonising the two.
    if args.is_serious_error(term_code):
        _perform_overrewrite(
            linkage, menu_state, program_id=program_id, term_code=term_code
        )
        _log_stop(_Stop.RUN_UNIT_ENDED, program_id=program_id, term_code=term_code)

    return term_code


def load07(linkage: args.SlPlLinkage, *, menu_state: args.MenuState) -> int:
    """`load07.` [sales/sales.cbl:L756-L768] - Sales transaction posting.

    The maintainer's own label comment is the evidence for that locator: `load07. *>
    Sales trans posting` [sales/sales.cbl:L756].

    Args:
        linkage: the five arguments in COBOL parameter order, as
            `args.bind_slpl_linkage(ns, called="sl055")` builds them. ONE
            instance is passed to both dispatches, which is what makes the second
            program see the first program's writes - the two period-total
            accumulations of `sl055` [sales/sl055.cbl:L675, :L677] reach `sl060`
            in the same `SYSTOT-REC`.
        menu_state: the menu's own WORKING-STORAGE, passed straight through to
            both dispatches so each one's `overrewrite` persists what the callee
            just accumulated.

    Returns:
        `WS-Term-Code` after the last dispatch that ran: `sl055`'s if the chain stopped
            there, otherwise `sl060`'s. Zero means the route completed.

    Raises:
        Nothing of its own - see `load000`.
    """

    #  [sales/sales.cbl:L763-L764] `move "sl055" to ws-called.` /
    #  `perform load000.`  A `perform` RETURNS, which is why the gate below is
    #  reachable at all.
    #  THE OTM2 CHANNEL, created per route invocation rather than per dispatch,
    #  because the file outlives the first `CALL` and is read by the second.
    channel = _ExtractChannel()

    term_code = load000(
        linkage,
        _PROGRAM_SL055,
        sl055_invoice_extract_analysis,
        menu_state=menu_state,
        channel=channel,
    )

    # THE RETURN LEG OF L712, NOT A SECOND GATE. `load000` has already taken its own `>
    # 7` disposition and logged it.
    if args.is_serious_error(term_code):
        return term_code

    if term_code != _WS_TERM_CODE_ZERO:
        _log_stop(
            _Stop.RETURNED_TO_MENU,
            program_id=_PROGRAM_SL055,
            term_code=term_code,
        )
        return term_code

    #  [sales/sales.cbl:L767-L768] `move "sl060" to ws-called.` /
    #  `go to load000.`  NO CODE MAY FOLLOW THIS LINE - see the docstring.
    return load000(
        linkage,
        _PROGRAM_SL060,
        sl060_invoice_posting,
        menu_state=menu_state,
        channel=channel,
    )


def _build_parser() -> argparse.ArgumentParser:
    """Compose this route's parser from the shared option fragments.

    Composed, never re-declared: `acas_posting.cli.args` owns the binding of argv to `01
    WS-Calling-Data` [copybooks/wscall.cob:L6-L14] and to the system records, and every
    entry point of this package imports those definitions rather than writing its own.

    Returns:
        The parser. Built on call, never at import.
    """
    parser = argparse.ArgumentParser(
        prog="python -m acas_posting.cli.sl_invoice_post",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Sales transaction posting - sl055, then the `not = zero` gate, then "
            "sl060. Reproduces sales/sales.cbl `load07.` L756-L768, whose label "
            "carries the maintainer's own comment `*> Sales trans posting`, and "
            "its five-parameter dispatch helper `load000.` L698-L712."
        ),
        epilog=(
            "The two programs run one at a time with the gate between them. A "
            "non-zero WS-Term-Code from sl055 stops the chain and sl060 is not "
            "dispatched; the exit status IS the term code. sl830 is not "
            "dispatched: the sales autogen series is out of scope. Pin "
            "--irs-instead explicitly - it decides which tables the run touches."
        ),
    )
    args.add_calling_data_arguments(parser, default_caller=args.WS_CALLER_SALES)
    args.add_slpl_linkage_arguments(parser)
    #  THE TRANSPORT DECLARATION IS NOT AN OPTION ON THIS ROUTE, AND MUST NOT
    #  BECOME ONE. The frozen `CALL` publishes the linkage operands and the write
    #  gating answers, and nothing else; the frozen bridge's connect passes six
    #  values and no transport policy at all
    #  [copybooks/mysql-procedures.cpy:L72-L77], transport being compiled into
    #  `cobmysqlapi.c`. A `--db-tls-*` or `--db-allow-plaintext` option here would
    #  add a program input and two refusal outcomes the compiled program has not
    #  got, which rule R-3 forbids - and a certificate path on a command line is a
    #  process-listing leak besides. Deployment security is resolved ONCE, outside
    #  the accounting path, from the same contract the six connection parameters
    #  come from: `args.install_connection_policy` reads it through
    #  `cli/args.resolve_transport_policy` while the linkage is bound, and
    #  every handler observes the installed policy without being told. It decides
    #  no posted figure, so it cannot make two runs of one scenario differ (R-6).
    #  Diagnostics only: no COBOL counterpart, no database effect. Shared with
    #  the other six routes so the level policy has one spelling.
    args.add_log_level_argument(parser)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """The CLI boundary: bind argv to the linkage, run `load07`, report the code.

    Args:
        argv: the argument vector WITHOUT the program name.

    Returns:
        The process exit status, which is `WS-Term-Code` itself: `args.exit_status_for`
            is the identity, total and lossless over the `pic 99` domain 0..99
            [copybooks/wscall.cob:L10].

    Raises:
        SystemExit: from argparse, for `--help` or a usage error - including the
            omission of the REQUIRED `--run-date`, which is the mechanically
            checkable proof that no ambient date can enter (rule R-6).
        CobolFileSystemPathUnavailable: from `sl055`, on the branch that needs
            GnuCOBOL built-ins rule R-1 forbids invoking. NOT caught - see the
            module docstring.

            Both keep propagating out of THIS function, which is the library
            contract the scenario suites rely on. At the PROCESS boundary
            `acas_posting.__main__.run_entry_point` reports one sanitised ERROR
            and returns a deterministic exit status instead of letting a
            traceback - with its absolute paths, source lines and exception
            text - reach a terminal. The disposition is unchanged: the run still
            stops, still having written nothing.

    `args.RdbmsParamError` is CAUGHT here, not raised: `main` returns
    `args.report_configuration_failure`'s status instead - 8 for an absent
    deployment contract, 1 for an unusable one - which is the single contract every
    route of this package shares (finding CLI-09). `ValueError` at large is NOT
    caught, so a genuine defect keeps its traceback.
    """
    #  THIS MODULE CALLS NO `basicConfig`. There is exactly one in the package, in
    #  `acas_posting.__main__.configure_logging`, which owns the one timestamp-free
    #  format and the one level policy. Both process boundaries reach it - the
    #  router, and this module's own guard through `run_entry_point` - so the format
    #  and the handler are never installed from here. `main` does ask that
    #  configurator to SET THE LEVEL, but only when the operator supplied
    #  `--log-level`; a `main` called as a library without that option, which is how
    #  the scenario suites reach it, therefore still touches nothing.
    ns = _build_parser().parse_args(argv)

    #  `--log-level` APPLIED THROUGH THE ONE CONFIGURATOR, and only when the
    #  operator supplied it. The shared fragment defaults the option to `None`, so
    #  `None` means "not asked for" and whatever the process boundary configured
    #  stands - on a routed run, the router's own `--log-level`. A supplied level
    #  is applied on either route: logging is configured once at the boundary, and
    #  `configure_logging` then sets the level because this package owns the
    #  handler, so the last explicit request wins. An embedding application's own
    #  configuration is never touched. The import is local to the call for the same
    #  reason the guard at the foot of this module gives.
    if ns.log_level is not None:
        from acas_posting.__main__ import configure_logging

        configure_logging(ns.log_level)

    #  L351  aa005-Open-System.   L365  aa010-Get-System-Recs.
    #  THE RECORDS THE CALLEES MUST SEE, READ BEFORE ANYTHING IS DISPATCHED. The
    #  Sales shell reads file-key 4 into `WS-System-Record-4` and file-key 1 into
    #  `System-Record` [sales/sales.cbl:L351-L404] - TWO keys, where the General
    #  Ledger shell reads three - and hands the result to every `CALL`. So the
    #  route sees the STORED period, ledger levels, control accounts and the
    #  running period totals that `sl055` and `sl060` ACCUMULATE INTO rather than
    #  initialise: [sales/sl055.cbl:L675] and [:L677] add to the invoice and
    #  credit-note totals, so starting them at the declared zero silently
    #  discarded every prior period's figures (finding CLI-02).
    #
    #  Shape 2 bound in one call, with `called` set to the FIRST program of the
    #  chain - `move "sl055" to ws-called` [sales/sales.cbl:L763]. The same
    #  instance then serves the second dispatch, which only changes `WS-Called`.
    #  BOTH LOADED RECORDS ARE BOUND IN, so the linkage carries the stored rows
    #  and not declared defaults; `overrewrite` then rewrites those same
    #  instances, which is why nothing has to be copied back.
    #  This call is also where the controlled clock is pinned, through
    #  `args.resolve_clock` -> `acas_posting.clock`: both observables, the text
    #  `to-day pic x(10)` and the binary `Run-Date`
    #  [copybooks/wssystem.cob:L67], from the one required `--run-date` (rule
    #  R-6). No date is read from anywhere else, here or downstream.
    #  THE MENU'S OWN WORKING-STORAGE, created once for the whole route. It owns
    #  `WS-System-Record-4`, which the binder then hands to the linkage as its
    #  third argument - the SAME object, so the four period-total writes of this
    #  route reach the record `overrewrite` rewrites. See
    #  `args.slpl_menu_state` and `args.MenuState`.
    menu_state = args.slpl_menu_state()

    #  Passing `menu_state` makes the binder perform `Open-System.` and
    #  `aa010-Get-System-Recs.` [sales/sales.cbl:L338-L360] first - keys 4 then 1,
    #  never key 2 - so both programs receive the PERSISTED records.
    #
    #  THE EXACT TYPE IS CAUGHT, NOT `ValueError` (finding CLI-09). The six
    #  connection parameters are resolved inside the binder before the store is
    #  opened, so a failure here has touched nothing; anything else keeps its
    #  traceback.
    try:
        linkage = args.bind_slpl_linkage(
            ns, called=_PROGRAM_SL055, menu_state=menu_state
        )
    except args.RdbmsParamError as error:
        return args.report_configuration_failure(
            error, logger=_LOG, subject="Sales invoice posting"
        )

    _LOG.info(
        "sl_invoice_post: sales/sales.cbl load07. L756-L768; run date pinned to "
        "to-day %r; WS-Caller %r",
        linkage.to_day,
        linkage.calling_data.ws_caller.strip(),
    )

    term_code = load07(linkage, menu_state=menu_state)

    _LOG.info(
        "sl_invoice_post finished with WS-Term-Code %d [copybooks/wscall.cob:L10]",
        term_code,
    )
    return args.exit_status_for(term_code)


if __name__ == "__main__":
    #  `harness/run_python_scenario.sh` invokes this module directly, and
    #  `pyproject.toml` declares no `[project.scripts]`. `run_entry_point` is the
    #  ONE process boundary shared with the router: it configures logging once
    #  and converts a failure into one sanitised ERROR record and a deterministic
    #  exit status, so nothing here can print a traceback, an absolute path or an
    #  exception payload to a terminal. The library contract above is unaffected -
    #  a caller that imports `main` still receives the exception.
    from acas_posting.__main__ import run_entry_point

    raise SystemExit(run_entry_point(main, command="sl-invoice-post"))


# --- traceability ------------------------------------------------------------
#
# MODULE -> COBOL SOURCE  (rule R-5)
#   acas_posting/cli/sl_invoice_post.py  <-  sales/sales.cbl `load07.` L756-L768
#   and its dispatch helper `load000.` L698-L712, plus the linkage declared by
#   copybooks/wscall.cob L6-L14, copybooks/wssystem.cob, copybooks/wssys4.cob and
#   copybooks/wsnames.cob. Every one of them is REFERENCE only - frozen, read as
#   specification. Any diff touching common/*.cbl, common/*.scb, copybooks/*.cob,
#   general/*.cbl, sales/*.cbl, purchase/*.cbl, irs/*.cbl or mysql/ACASDB.sql is
#   a defect in the migration, however harmless it looks (AAP 0.8.1).
#
# FUNCTION -> PARAGRAPH
#   load000               sales/sales.cbl:L698-L712  (exit L714-L716)
#   load07                sales/sales.cbl:L756-L768
#   main                  the CLI boundary - no COBOL paragraph. The menu shell
#                         has `display-menu.` L478 and its `accept` loop here;
#                         both are screen I/O with no database effect and are
#                         omitted (AAP 0.3.4).
#   _build_parser         the CLI boundary - no COBOL paragraph. Composes the
#                         shared fragments of acas_posting/cli/args.py.
#   _perform_overrewrite  `perform overrewrite` L709 and L711, reaching
#                         `overrewrite.` sales/sales.cbl:L628-L658, which falls
#                         through `overclose.` L659 to `goback` L660. A thin
#                         wrapper: the paragraph itself is `args.overrewrite`,
#                         shared by all seven routes, and this keeps the log
#                         record and the citation beside the two call sites.
#   _log_stop, _Stop      the two dispositions, named: L710-L712 and L765-L766.
#   _SlPlPostingProgram   the shape of `call ws-called` L702, a dynamic call by
#                         name.
#
# PROGRAM -> MODULE
#   sl055  ->  acas_posting/programs/sl055_invoice_extract_analysis.py
#              linkage sales/sl055.cbl:L271-L275, dispatched at
#              sales/sales.cbl:L763-L764
#   sl060  ->  acas_posting/programs/sl060_invoice_posting.py
#              linkage sales/sl060.cbl:L395-L399, dispatched at
#              sales/sales.cbl:L767-L768
#   Both are imported AS MODULES and reached only through their published `run`;
#   `acas_posting/programs/__init__.py` provides no dispatch table, no registry
#   and no `run` re-export, and this module adds none (AAP 0.3.3).
#
# `GO TO` CLASSES  (AAP 0.4.2 taxonomy)  -  two transfer sites, both class 4
# (sibling re-dispatch), each with its per-site proof of equivalence:
#
#   L765-L766  `if ws-term-code not = zero / go to display-menu`   CLASS 4
#     COBOL   the menu is redrawn and awaits the next selection; sl060 is never
#             reached.
#     Python  the operation ends immediately; sl060 is never invoked.
#     Proof   identical set of invoked programs, identical database effect. The
#             menu redraw has no database effect (AAP 0.3.4) and "await the next
#             selection" has no headless equivalent - a command performs one
#             operation and returns.
#
#   L710-L712  `if ws-term-code > 7 / perform overrewrite / goback`   CLASS 4
#     COBOL   `perform overrewrite` returns, then `goback` ends the RUN UNIT: the
#             menu program stops, so nothing further is dispatched.
#     Python  load000 logs the stop and returns the term code; load07 honours it
#             by returning without dispatching sl060, and main leaves the process
#             with args.exit_status_for(...).
#     Proof   control never re-enters the dispatch paragraph in either version,
#             the same programs run, and overrewrite persists the same two rows
#             before control leaves - so the serious-error path's table state
#             matches too. The only remaining difference is the process exit
#             status, which the COBOL has no equivalent of at all
#             (Q-CLI-EXITSTATUS).
#
#   The `< 8` branch L708-L709 is NOT a transfer: `perform overrewrite` returns
#   to the next statement, so the flow is straight-line and the effect is
#   performed.
#
# CORRECTIONS  -  each verified against the frozen source with a line read. DO
# NOT "fix" any of these back to the value the planning documents carry.
#
#   1. THE PARAGRAPH IS `load07` (sales/sales.cbl:L756-L768), NOT `load08`.
#      The folder requirements table and the acas_posting/__main__.py route table
#      both say `load08`. `load08.` (L770-L774) dispatches "sl080" - Payment
#      Input - which AAP 0.2.2 places explicitly out of scope, so the wrong label
#      would point the traceability document at an out-of-scope program.
#      Evidence, four ways: the maintainer's inline comment
#      `load07.             *> Sales trans posting` on the label line itself
#      (L756); the menu-letter ordinal, `"(G)  Sales Transactions Post"` at L545
#      being the seventh letter under the `depending on z` dispatch at L670
#      (L546 `"(H)  Payment Input"` is the eighth, L549 `"(K)  Payment Post"` the
#      eleventh, which is load11 and the sibling sl_cash_post route); and TWO
#      change-history entries, ".32 Added execution of sl830 first when Invoice
#      Post selected." (L121) and - decisively - ".33 Call in load07 to 830
#      should have been using load00 not 000." (L124), in which the maintainer
#      names load07 as the invoice-post paragraph. Note that __main__.py's route
#      table cites the gate SPAN correctly, L759-L768, which lies inside load07;
#      only the label is wrong.
#
#   2. THE SALES/PURCHASE LINKAGE SHAPE HAS FIVE PARAMETERS, not the four AAP
#      0.4.1.1's phrasing implies. sales/sales.cbl:L702-L706 passes five
#      (ws-calling-data, System-Record, WS-System-Record-4, to-day, file-defs) and
#      both callees declare five, sales/sl055.cbl:L271-L275 and
#      sales/sl060.cbl:L395-L399. AAP 0.1.1 has it right - "The Sales and
#      Purchase families add the fourth system record" - and args.SlPlLinkage has
#      five members. The maintainer's own comment at L708 names the beneficiaries:
#      `*> for sl055 & 060, xl150`.
#
#   3. THE __main__.py ROUTE TABLE'S NEIGHBOURING SPANS DRIFT BY ONE LINE. It
#      cites `load11` as L793-L797; the label `load11.` is at L792 and the
#      paragraph runs to L796. Measured label lines in sales/sales.cbl:
#      load00. L677, load000. L698, load01. L718, load06. L750, load07. L756,
#      load08. L770, load09. L776, load10. L782, load11. L792, load12. L798.
#
#   A NOTE ON ONE FURTHER LOCATOR, already corrected by the sibling: AAP 0.4.1.1
#   cites `01 WS-Calling-Data` as copybooks/wscall.cob:L6-L13, but WS-CD-Args is
#   at L14 (L11 being a comment), so the block is L6-L14. This module cites
#   L6-L14 throughout, as acas_posting/cli/args.py already does in its own
#   CORRECTION 1.
#
# OMISSIONS - recorded as omissions so that a reader comparing the two trees does
# not conclude something was lost (AAP 0.4.3):
#
#   * `sl830` AND THE WHOLE `load00` HEAD OF THE CHAIN, sales/sales.cbl:L759-L762
#     - `move "sl830" to WS-Called`, `perform load00` and that leg's own
#     `not = zero` gate. AAP 0.2.2 excludes the sales autogen series sl800..sl830,
#     and AAP 0.4.1.1 has this entry point dispatch sl055 then sl060 only. The
#     maintainer added the leg at L121 (".32") and corrected which helper it uses
#     at L124 (".33"). Consequently `load00.` itself - sales/sales.cbl:L677-L692,
#     the FOUR-parameter shape - is NOT implemented in this module: with sl830
#     out of scope this route has no caller for it. The oracle driver script
#     records the same asymmetry, noting that the menu-driven Cobol side WILL run
#     sl830 and that the two autogen tables are asserted untouched
#     [harness/run_cobol_scenario.sh acas_plan_sl_invoice_post].
#
#   * `display-menu.` (sales/sales.cbl:L478) AND ALL MENU SCREEN I/O, including
#     the `go to load01 load02 ... depending on z` dispatch table at
#     sales/sales.cbl:L670 and the banners the two programs display. No database
#     effect, excluded by AAP 0.2.2 and 0.3.4. Diagnostics become log records
#     that neither alter control flow nor reach a column.
#
#   * `overrewrite`'s PERSISTENCE of System-Record (key 1) and
#     WS-System-Record-4 (key 4) to both the RDB and the Cobol file -
#     sales/sales.cbl:L628 falling through `overclose.` L659 to `goback` L660 -
#     together with `pre-overrewrite`'s backup `call "SYSTEM" using
#     Full-Backup-Script` at sales/sales.cbl:L625. THE FIRST IS NO LONGER
#     OMITTED: `args.overrewrite` reproduces its RDB arm and
#     `_perform_overrewrite` performs it from both arms of `load000`, which is
#     what makes this route's four period-total writes reach SYSTOT-REC. Only that
#     paragraph's COBOL-FILE arm sales/sales.cbl:L644-L657 has no counterpart, the
#     migration having one store - see args.RDBMS_STORE_SELECTOR_DIGIT. The second
#     remains excluded twice, by AAP 0.2.2's spool-out exclusion and by R-1.
#
#   * THE PURE-ACKNOWLEDGEMENT `accept WS-Reply at 2435` at sales/sl055.cbl:L342.
#     Dropped under AAP 0.3.4 - its only effect is to block a terminal - while
#     THE SURROUNDING CONTROL TRANSFER IS PRESERVED: `move 8 to WS-Term-Code`
#     (L344) and `goback` (L345) both stand, in sl055's own module. Note that the
#     prompt is guarded by `if WS-Caller not = "xl150"` (L341), so `WS-Caller`
#     genuinely changes behaviour there; it remains bindable through
#     `args.add_calling_data_arguments` and is defaulted to "sales"
#     (sales/sales.cbl:L481).
#
#   * THE OTHER SALES MENU ROUTES, not dispatched by this entry point because
#     they are out of scope: `load08.` L770-L774 (sl080, Payment Input),
#     `load09.` L776-L780 (sl085), `load10.` L782-L790 (sl090 then sl095).
#     `load11.` L792-L796 (sl100) is in scope but belongs to the sibling
#     sl_cash_post route.
#
#   * NO "DOES THE EXTRACT FILE EXIST?" PRE-CHECK (rule R-3). That test is the
#     call to the GnuCOBOL file-existence built-in at sales/sl055.cbl:L336-L337,
#     inside sl055, and duplicating it in the entry point would add a validation
#     the COBOL does not have at this level. No path is inspected here at all.
#
# ANOMALY, REPRODUCED AS DATA (rule R-4)
#   `load00`'s whitelist, sales/sales.cbl:L686-L690, tests
#   `ws-called = "sl000" or "sl080" or "sl085" or "sl090" or "sl095" or "sl100"
#   or "sl115" or "sl200" or "sl910" or "sl920" or "sl930"` before performing
#   `overrewrite`. The `"sl100"` entry is DEAD: sl100 is dispatched through
#   `load000`, not `load00` - `load11.` is `move "sl100" to ws-called` then
#   `go to load000` (sales/sales.cbl:L795-L796) - so the test can never match it.
#   The maintainer's own inline `*> 200 ??  930 ??` at L689 shows he doubted two
#   further entries. Recorded, not cleaned up. It has no effect on THIS module,
#   which does not implement `load00` at all, and it is recorded here because the
#   paragraph is part of the route this module reproduces.
#
# AMBIGUITIES  (rule R-6)  -  three, each marked in place at the code it governs.
#   One of the three is now SETTLED; the entry records how.
#   Q-CLI-OVERREWRITE   in _perform_overrewrite - SETTLED, AND SETTLED BY
#     REPRODUCING THE PARAGRAPH. The Cobol run rewrites SYSTEM-REC and SYSTOT-REC
#     after every dispatch of this route, and so does the Python run now:
#     `args.overrewrite` is performed from both arms of `load000`, and
#     `args.aa010_get_system_recs` loads the same two rows before the first
#     dispatch. What remains for the oracle is narrower and is recorded as
#     Q-CLI-SYSREC-PINS in acas_posting/cli/args.py: three columns - Run-Date,
#     Date-Form and IRS-Instead - are re-pinned from the command line over the
#     loaded row, so a scenario must seed them to agree with the options it passes.
#     A MEASURED CONSEQUENCE THAT IS NOW HANDLED, recorded because the earlier
#     reading of this site turned on it: `File-System-Used` is a SYSTEM-REC column
#     with `88 FS-Cobol-Files-Used value zero.` [copybooks/wssystem.cob:L113] and
#     `88 FS-RDBMS-Used value 1.` [copybooks/wssystem.cob:L116], and a record built
#     purely at the record layer's declared defaults carries zero - which is why a
#     run that never loaded the row could not reach the relational path. The load
#     now brings the seeded value in. The frozen menus do not test that column
#     before their own reads either: they force the store selector directly, `move
#     "00" to FA-RDBMS-Flat-Statuses` [sales/sales.cbl:L353], and the migration
#     forces `"66"` for the same reason and in the same place - see
#     args.RDBMS_STORE_SELECTOR_DIGIT. So the route no longer depends on the seed
#     for its own system-record traffic, while the twelve posting programs still
#     read `File-System-Used` from the loaded row exactly as the COBOL ones do.
#   Q-CLI-TERMCODE-1-7  in load07, at the gate - OPEN. The 1..7 band is
#     unreachable from sl055 today (the census finds only 5 at
#     general/gl070.cbl:L289, 8 at sales/sl055.cbl:L344 and 8 at
#     purchase/pl055.cbl:L286), so the Sales gate and Purchase's absence of one
#     cannot currently be told apart. The oracle must confirm that no other
#     program on either route sets a code in that band.
#   Q-CLI-EXITSTATUS    in main - SETTLED in acas_posting/cli/args.py, and
#     settled by establishing that THERE IS NO ORACLE OBSERVABLE: RETURN-CODE, the
#     one register GnuCOBOL surfaces as a process status, is read and never
#     written anywhere in the five menus or the twelve posting programs, and each
#     menu ends with a bare `goback` (sales/sales.cbl:L660). The identity mapping
#     is therefore a boundary decision under AAP 0.3.4, taken because it is total
#     and lossless over the `pic 99` domain. This module re-encodes nothing.
#
# RULES  -  `review_rules` reports NO user rules document for this project, so
# these are the Agent Action Plan's own six (section 0.7.2); enterprise-standard
# best practice applies wherever they are silent, and no rule has been invented.
#   R-1  satisfied structurally. Imports: argparse, enum, logging,
#        collections.abc, typing, acas_posting.cli.args and the two program
#        modules - and nothing else. Nothing here spawns a child process, loads a
#        foreign library or reaches the GnuCOBOL toolchain; there is no import
#        path from this package to the compiled oracle's tree, and no option
#        selects, invokes or diffs against that oracle. The oracle's own scripts
#        drive THIS entry point from outside, never the reverse.
#   R-2  satisfied by type. WS-Term-Code is an `int` (`pic 99`,
#        copybooks/wscall.cob:L10), to-day is a `str`, and no binary-radix
#        numeric type appears in any signature, option type or expression - the
#        word does not occur in this file even as an argparse converter. No
#        arithmetic is performed here at all.
#   R-3  satisfied by omission. No added validation - notably no duplicated
#        extract-file check and no path inspection of any kind - no added field,
#        no SQL and no schema access; and no concurrency, there being no thread,
#        no pool, no event loop and no child-process primitive imported, and no
#        option that would create one. The two programs run ONE AT A TIME, in
#        this one process, with the gate
#        between them, matching the single-threaded COBOL. No control-total
#        option is offered, because Sales batches balance by construction
#        (AAP 0.6.4).
#   R-4  reproductions, each carrying its locator at the site: the `not = zero`
#        gate predicate (L765-L766), left different from the General Ledger's
#        `= 5` and from Purchase's absent gate; the `< 8` and `> 7` bands as two
#        separate statements (L708-L712); `move zero to ws-term-code` before
#        every dispatch (L701); Sales' `perform overrewrite` then `goback`
#        mechanism left distinct from Purchase's `go to overrewrite`
#        (purchase/purchase.cbl:L703-L704); the dead "sl100" whitelist entry
#        recorded above; and the deliberate non-normalisation of all four
#        divergent gate forms.
#   R-5  this footer, the paragraph-named public functions load000 and load07,
#        the `GO TO` class and proof at both transfer sites, and a locator on
#        every reproduced statement.
#   R-6  the clock is injected: --run-date is REQUIRED, with no default and no
#        fallback, and both observables are pinned through args.resolve_clock ->
#        acas_posting.clock. Nothing here reads a system clock, a calendar, an
#        elapsed-time counter, an environment variable, a host name or an entropy
#        source - none of the modules that offer one is imported. Two runs of one
#        scenario under the same pinned clock are therefore byte-identical
#        (AAP 0.8.5). The three questions above are marked, not guessed.
# -----------------------------------------------------------------------------
