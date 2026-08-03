"""`load08.` - Purchase transaction posting: `pl055` then `pl060`, and NO gate.

The Purchase Ledger's transaction-posting route, reproduced from the frozen menu
shell. Its menu letter is `(H)  Purchase Transactions Post`
[purchase/purchase.cbl:L540] - the eighth letter, hence `load08.`, whose entire
body is these eleven lines [purchase/purchase.cbl:L752-L762]::

    L752  load08.
    L753  *>------
    L754  *>
    L755  *>    move     "pl830" to WS-Called.   *> In case autogen is use
    L756  *>    perform  load000.
    L757  *>    if       ws-term-code not = zero
    L758  *>             go to display-menu.
    L759       move     "pl055" to ws-called.
    L760       perform  load000.
    L761       move     "pl060" to ws-called.
    L762       go       to load000.

THERE IS NO PARAGRAPH-LEVEL GATE ON THIS ROUTE, AND THE ABSENCE IS THE
SPECIFICATION
Four of those eleven lines are commented out in the frozen source, and they are
exactly the ones that would have made a gate: the `pl830` autogen dispatch
(L755-L756) together with its `if ws-term-code not = zero / go to display-menu`
test (L757-L758). What remains is `pl055`, then `pl060`, with NOTHING between
them - `pl060` runs whatever `pl055` left in `WS-Term-Code`.

That is a genuine divergence from the Sales route, not an oversight in the
reading, and it is sharper than the commented-out block alone suggests. The
three gate forms in this package are:

    General Ledger    `if ws-term-code = 5`         general/general.cbl:L810-L811
    Sales invoice     `if ws-term-code not = zero`  sales/sales.cbl:L761-L762 and
                                                    L765-L766  -  TWO of them
    Purchase order    none                          purchase/purchase.cbl:
                                                    L755-L758, commented out

The Sales route tests the code after `sl830` AND again after `sl055`
[sales/sales.cbl:L765-L766]. Purchase has no live test at all, and the one
commented-out test it does carry guarded the `pl830` leg - it sat BEFORE the
`pl055` dispatch, never between `pl055` and `pl060`. So the position where a
well-meaning maintainer would insert a gate is a position the frozen source
never had a statement in, in any form, commented or otherwise.

It is PRESERVED, NOT FIXED (rule R-4: a defect reproduced is correct; a defect
fixed is a failure). Nothing here aligns Purchase with Sales, and nothing turns
the missing gate into a warning: a warning that changed what ran next would
change behaviour, and one that did not would be noise.

THE ROUTE IS STILL ABORTABLE, THROUGH THE DISPATCH PARAGRAPH ITSELF
The absence of a gate is not an absence of abort behaviour, and a caller must
not conclude that this route cannot stop. `load000.` carries its own
serious-error test [purchase/purchase.cbl:L691-L708]::

    L691  load000.
    L694       move     zero to ws-term-code.
    L695       call     ws-called using ws-calling-data
    L696                                system-record
    L697                                WS-system-record-4
    L698                                to-day
    L699                                file-defs
    L700       end-call
    L701       if       ws-term-code < 8  *> for pl055 & 060, xl150
    L702                perform  overrewrite.
    L703       if       ws-term-code > 7      *> Got a serious (reported) error
    L704                go to overrewrite.
    L706  load000-exit.
    L708       go       to display-menu.

`WS-Term-Code` is `pic 99` [copybooks/wscall.cob:L10], so its domain is 0
through 99 and the two tests `< 8` and `> 7` are exhaustive and mutually
exclusive - there is no third band. `pl055` raises 8, and only 8, on the one
path that raises anything at all: its extract file is missing, so it reports and
sets the code [purchase/pl055.cbl:L286] before `goback` [purchase/pl055.cbl:
L287]. Code 8 therefore takes L703-L704, `go to overrewrite`, which persists the
system records, falls through `overclose.` [purchase/purchase.cbl:L652] into
`goback` [purchase/purchase.cbl:L653] and ENDS THE RUN UNIT. `pl060` never runs.

AND THE ABORT MECHANISM ITSELF DIVERGES FROM SALES
Purchase transfers - `go to overrewrite` [purchase/purchase.cbl:L703-L704].
Sales performs and then returns - `perform overrewrite / goback`
[sales/sales.cbl:L710-L712]. The net effect is the same, persist then exit, but
the mechanism is not, and the two are left as they are rather than harmonised.

The consequence of having no gate is therefore confined to the 1..7 band, which
no in-scope program currently reaches: `gl070` raises 5
[general/gl070.cbl:L289], `sl055` raises 8 [sales/sl055.cbl:L344] and `pl055`
raises 8 [purchase/pl055.cbl:L286], and nothing else raises anything. Sales
would return to the menu for any non-zero code up to 7; Purchase proceeds to
`pl060`. Unobservable today, reproduced exactly regardless - see
Q-CLI-TERMCODE-1-7 in the footer.

THE LINKAGE SHAPE - FIVE PARAMETERS, NOT FOUR
Both callees take the Sales and Purchase shape, the second of the three shapes
this package binds::

    procedure division using ws-calling-data
                             system-record
                             system-record-4
                             to-day
                             file-defs.

`pl060` declares it at [purchase/pl060.cbl:L340-L344] and `pl055` at
[purchase/pl055.cbl:L239-L243]; the menu passes those same five operands at
[purchase/purchase.cbl:L695-L699]. FIVE - the General Ledger family omits
`system-record-4` and the IRS program takes neither the calling-data block nor
the run date. The three shapes are not unified. See CORRECTION 1 in the footer.

One record is spelled two ways and both spellings stay: the caller passes
`WS-system-record-4` [purchase/purchase.cbl:L697] and the callee declares
`system-record-4` [purchase/pl055.cbl:L241]. `args.SlPlLinkage` carries the five
in COBOL order, so splatting it into a callee's `run` reproduces the `CALL`
parameter list exactly.

THE CLOCK CONTRACT
The run date enters here and nowhere else, as the REQUIRED `--run-date`, and is
pinned by `args.resolve_clock` into both observables the cycle can see: the text
`to-day pic x(10)` in DD/MM/CCYY form, and the binary `Run-Date`
[copybooks/wssystem.cob:L67]. Neither `pl055` nor `pl060` reads a clock - the
date arrives purely through linkage - so two runs of one scenario under the same
pinned date are byte-identical (rule R-6). The single clock read in the whole
frozen call chain lives in the menu shell's date-service copybook
[copybooks/Proc-ACAS-Mapser-RDB.cob:L72-L80], which is out of scope.

WHAT THIS ROUTE DELIBERATELY DOES NOT HAVE
    * NO run-confirm option. `pl060`'s `acpt-xrply.` paragraph label survives at
      [purchase/pl060.cbl:L362] but its whole body, the "OK to post Purchase
      Transactions (YES/NO) ?" prompt and its two tests, is commented out at
      [purchase/pl060.cbl:L363-L370]. There is no question to promote. The
      sibling payment route DOES have one, because [purchase/pl100.cbl:L302-L311]
      is live - that belongs to `cli/pl_payment_post.py`, not here.
    * NO `pl830` dispatch. Already commented out in the frozen source
      [purchase/purchase.cbl:L755-L758], and the purchase `pl800` autogen series
      is out of scope in its own right.
    * NO file-existence pre-check. `pl055` makes that test itself
      [purchase/pl055.cbl:L278-L280] and duplicating it here would add a
      validation the migration may not add (rule R-3).
    * NO screen output of any kind, and no `ACCEPT`. Diagnostics that have no
      database effect are log records; a prompt that merely pauses for
      acknowledgement is dropped, keeping the control transfer around it - which
      is exactly what happens to [purchase/pl055.cbl:L284].

Sequential, single-threaded, one program at a time, matching the original
(rule R-3). Importing this module does no work: it builds no parser, opens no
connection and reads nothing.

Invoke it as `python -m acas_posting.cli.pl_order_post --run-date DD/MM/CCYY`,
or reach `load08` directly from the package router.
"""

from __future__ import annotations

import argparse
import logging
from collections.abc import Callable, Sequence
from typing import Final

from acas_posting.cli import args
from acas_posting.programs import pl055_order_proof_extract, pl060_order_posting

__all__: Final[tuple[str, ...]] = ("main", "load000", "load08")


_LOG: Final[logging.Logger] = logging.getLogger(__name__)


#  THE TWO PROGRAM-IDS THIS ROUTE DISPATCHES, as the menu writes them.
#  `move "pl055" to ws-called.` [purchase/purchase.cbl:L759] and
#  `move "pl060" to ws-called.` [purchase/purchase.cbl:L761]. Named constants
#  rather than inline literals so that the dispatch order below reads as the
#  paragraph does and so that `WS-Called` and the module actually invoked cannot
#  drift apart. `WS-Called` is `PIC X(8)` [copybooks/wscall.cob:L7]; the
#  space-filling to that width is applied by `args.set_called`, never here.
_PL055: Final[str] = "pl055"
_PL060: Final[str] = "pl060"

#  `display "(H)  Purchase Transactions Post"` [purchase/purchase.cbl:L540] -
#  the menu line that selects this route, carried for traceability and shown in
#  `--help`. The menu itself is out of scope, so nothing displays it.
_MENU_OPTION: Final[str] = "(H)  Purchase Transactions Post"

#  The invocation name argparse reports in usage and error messages. `pyproject`
#  declares no console script, so a module invocation is the real entry form.
_PROG: Final[str] = "python -m acas_posting.cli.pl_order_post"

#  The log format used when this module is the process entry point. Applied by
#  `main` only - see the note there on why no module may configure logging at
#  import time.
_LOG_FORMAT: Final[str] = "%(levelname)s %(name)s: %(message)s"


#  A migrated program's published entry, as `load000` invokes it.
#
#  `Callable[..., None]` rather than a five-parameter `Protocol`, and the reason
#  is a layering rule rather than laziness: naming the five parameter types would
#  mean importing the record classes, and this package's import table confines a
#  `cli` module to the program modules, the clock and `cli.args`. The arity and
#  the order are guaranteed STRUCTURALLY instead, and more strongly than an
#  annotation could: `load000` splats `args.SlPlLinkage`, a five-member
#  `NamedTuple` whose members ARE the COBOL parameter list in COBOL order
#  [purchase/pl060.cbl:L340-L344], so a callee declaring anything other than
#  those five in that order fails at the call.
type _ProgramEntry = Callable[..., None]


def _run_unit_ended(term_code: int) -> bool:
    """Did `load000` already end the run unit? `if ws-term-code > 7`.

    NAMED, rather than written inline at the one place it is asked, because what
    it asks is easy to mistake for a gate and it is not one. `load000`'s second
    test transfers control out of the dispatch paragraph -
    `go to overrewrite` [purchase/purchase.cbl:L703-L704] - and `overrewrite`
    falls through `overclose.` [purchase/purchase.cbl:L652] into `goback`
    [purchase/purchase.cbl:L653]. In COBOL that transfer simply never comes back;
    in Python a called function must return, so the caller has to honour the
    non-return itself. This predicate is that honouring, and nothing else.

    Why it cannot be a gate, provably: it is true only for codes ABOVE 7. A gate
    on this route would have to hold somewhere in 1..7, and this never does. The
    two bands are `args.is_serious_error`'s own, and its complement is exactly
    the `< 8` of [purchase/purchase.cbl:L701] over the `pic 99` domain
    [copybooks/wscall.cob:L10].

    Args:
        term_code: `WS-Term-Code` as the callee left it, read back out of the
            shared calling-data record.

    Returns:
        True when the dispatch ended the run unit, so no further program runs.
    """
    return args.is_serious_error(term_code)


def load000(
    linkage: args.SlPlLinkage,
    program_id: str,
    program: _ProgramEntry,
) -> int:
    """`load000.` [purchase/purchase.cbl:L691-L708] - the one dispatch paragraph.

    Purchase's own copy of the paragraph, reproduced statement by statement:
    clear the code, name the callee, call it with the five operands, then make
    the two tests over the result.

    DELIBERATELY NOT SHARED WITH THE SIBLING ROUTES. Each menu shell in the
    frozen tree carries its own `load000.`, and the copies are NOT identical -
    Purchase's serious-error branch is `go to overrewrite`
    [purchase/purchase.cbl:L703-L704] where Sales' is `perform overrewrite`
    followed by `goback` [sales/sales.cbl:L710-L712]. Importing one route's
    dispatcher into another would erase a divergence this migration is required
    to keep, so the duplication here mirrors the duplication there.

    Args:
        linkage: the five linkage operands, in COBOL order. The SAME instance is
            handed to every dispatch of a route, because these are the menu's own
            working-storage records and a callee writes back into them - which is
            how `WS-Term-Code` gets from `pl055` to the test below.
        program_id: the callee's program-id, `"pl055"` or `"pl060"`, moved into
            `WS-Called` exactly as [purchase/purchase.cbl:L759] and
            [purchase/purchase.cbl:L761] move it.
        program: the migrated callee's published `run`. In the COBOL the target
            comes from the field itself - `call ws-called` is a dynamic call by
            name - so the two travel together here and are resolved at the same
            moment: the caller looks the attribute up at the call site, which is
            also what keeps the field and the target in step.

    Returns:
        `WS-Term-Code` as the callee left it. The caller decides what that means:
        `_run_unit_ended` distinguishes the two bands the COBOL distinguishes.

    Note:
        The callee's own return value is discarded because there is none to keep:
        a COBOL sub-program communicates through the shared linkage records, and
        the migrated programs likewise return None and write into the records.
    """
    #  L694  `move zero to ws-term-code.`  -  BEFORE EVERY CALL, not once per
    #  route. R-4 [purchase/purchase.cbl:L694]: the field is shared linkage
    #  storage, so a code the previous callee left behind would still be sitting
    #  there for the tests below, and on this route those tests are the only
    #  thing that can stop the run. Clearing it per dispatch is what makes each
    #  phase's verdict its own.
    args.reset_term_code(linkage.calling_data)

    #  L759 / L761  `move "pl055" to ws-called.` / `move "pl060" to ws-called.`
    #  The MOVE is the dispatch vehicle, and its receiving-field width applies:
    #  `WS-Called` is `PIC X(8)` [copybooks/wscall.cob:L7].
    args.set_called(linkage.calling_data, program_id)

    _LOG.info(
        "load08: dispatching %s [purchase/purchase.cbl:L695-L700]", program_id
    )

    #  L695-L700  `call ws-called using ws-calling-data / system-record /
    #  WS-system-record-4 / to-day / file-defs / end-call`.
    #
    #  FIVE POSITIONAL ARGUMENTS IN COBOL ORDER, and the order is not retyped
    #  here: `args.SlPlLinkage` holds the five operands in the frozen source's
    #  own sequence, so the splat IS the parameter list
    #  [purchase/purchase.cbl:L695-L699]. No keyword argument is passed - this
    #  route has no promoted prompt to pass one for.
    program(*linkage)

    #  The callee wrote into the caller's storage, exactly as a COBOL `CALL BY
    #  REFERENCE` does: `move 8 to WS-Term-Code` [purchase/pl055.cbl:L286] lands
    #  in the very record handed over above. Read it back before testing it.
    term_code = linkage.calling_data.ws_term_code

    #  L701-L702  `if ws-term-code < 8 / perform overrewrite.`
    #
    #  R-4 [purchase/purchase.cbl:L701-L702]. Two facts about this branch, and
    #  both are recorded rather than tidied:
    #    * it is taken on EVERY dispatch that is not a serious error, including a
    #      wholly successful one - the maintainer's own comment on the line is
    #      "Update sys4 and system recs in case of changes"; and
    #    * its body is an OMISSION here. `overrewrite`
    #      [purchase/purchase.cbl:L621-L651] rewrites SYSTEM-REC (key 1) and
    #      SYSTOT-REC (key 4) to the relational store and then to the Cobol
    #      file, which needs the data-access layer that a `cli` module may not
    #      reach, and it lives in a menu program that is out of scope. So a
    #      Python run leaves those two rows as the seed left them where a COBOL
    #      run would rewrite them.
    #
    #  AMBIGUITY Q-CLI-OVERREWRITE: the two omitted rewrites are the sole
    #  persistence of the period totals that `pl055` accumulates
    #  [purchase/pl055.cbl:L582] and [purchase/pl055.cbl:L584] and that `pl060`
    #  adds to [purchase/pl060.cbl:L628], so SYSTEM-REC and SYSTOT-REC belong to
    #  the seeded state and to each scenario's declared affected-table list
    #  rather than to this layer. Resolve against the compiled oracle - run the
    #  route both ways and compare those two tables - and record the outcome in
    #  docs/migration/ambiguity-resolutions.md.
    #
    #  `not args.is_serious_error(...)` IS `< 8`: over the `pic 99` domain
    #  [copybooks/wscall.cob:L10] the frozen tests `< 8` and `> 7` are
    #  exhaustive and mutually exclusive, so the complement needs no second
    #  helper and no threshold is transcribed here.
    if not args.is_serious_error(term_code):
        _LOG.debug(
            "load000: %s left ws-term-code %d; the frozen `perform overrewrite` "
            "[purchase/purchase.cbl:L701-L702] is a recorded omission - "
            "SYSTEM-REC and SYSTOT-REC are not rewritten",
            program_id,
            term_code,
        )

    #  L703-L704  `if ws-term-code > 7 / go to overrewrite.`
    #
    #  GO TO class 4 (sibling re-dispatch), and this is its per-site proof.
    #
    #  COBOL: control leaves `load000.` for `overrewrite.`
    #  [purchase/purchase.cbl:L621], which persists the two system records and
    #  then FALLS THROUGH the `overclose.` label [purchase/purchase.cbl:L652]
    #  into `goback` [purchase/purchase.cbl:L653]. The run unit ends there. It
    #  does not reach `load000-exit.` [purchase/purchase.cbl:L706], so it never
    #  reaches the `go to display-menu` at [purchase/purchase.cbl:L708] either,
    #  and it never returns to whichever `perform`/`go to` arrived here.
    #
    #  PYTHON: report, then return the serious-error code. `load08` asks
    #  `_run_unit_ended` and dispatches nothing further; `main` turns the code
    #  into the process status through `args.exit_status_for`.
    #
    #  PROOF OF EQUIVALENCE: the two agree on everything observable. No further
    #  program is invoked on either side; control never returns to the dispatch
    #  paragraph on either side; and the code survives on both. The ONLY
    #  difference is the persistence `overrewrite` would have performed, which is
    #  the omission recorded above and in the footer - it is the same omission on
    #  the `< 8` path, so honouring this branch adds nothing new.
    #
    #  R-4, MECHANISM DIVERGENCE PRESERVED: Purchase transfers here
    #  [purchase/purchase.cbl:L703-L704]; Sales instead performs and returns,
    #  `perform overrewrite / goback` [sales/sales.cbl:L710-L712]. Same net
    #  effect, different mechanism, and they are left different.
    if args.is_serious_error(term_code):
        _LOG.error(
            "load000: %s reported a serious error, ws-term-code %d - "
            "`go to overrewrite` [purchase/purchase.cbl:L703-L704] ends the run "
            "unit at `goback` [purchase/purchase.cbl:L653]; no further program "
            "is dispatched",
            program_id,
            term_code,
        )

    return term_code


def load08(linkage: args.SlPlLinkage) -> int:
    """`load08.` [purchase/purchase.cbl:L752-L762] - `pl055`, then `pl060`.

    The Purchase transaction-posting route, in the frozen source's own order and
    with the frozen source's own absence of a gate between the two phases. Both
    dispatches go through `load000`, which is where this route's only stop lives.

    Args:
        linkage: the five linkage operands. ONE instance for the whole route:
            `pl060` must see the records `pl055` wrote, exactly as the COBOL
            hands both programs the same working storage and the same extract
            file.

    Returns:
        `WS-Term-Code` after the last dispatch that ran - `pl060`'s normally, or
        `pl055`'s when `pl055` ended the run unit.

    Note:
        Strictly sequential: one program at a time, never overlapped, matching
        the single-threaded original (rule R-3).
    """
    #  L759-L760  `move "pl055" to ws-called.` / `perform load000.`
    #  Phase one - the Purchase Invoice Post Extract, which builds the OTM4
    #  extract `pl060` then posts and writes the two period totals
    #  [purchase/pl055.cbl:L582] and [purchase/pl055.cbl:L584].
    term_code = load000(linkage, _PL055, pl055_order_proof_extract.run)

    #  ======================================================================
    #  THE GATE THAT IS NOT HERE
    #  ======================================================================
    #  R-4 [purchase/purchase.cbl:L755-L758] - the `pl830` dispatch AND its
    #  `if ws-term-code not = zero / go to display-menu` gate are BOTH COMMENTED
    #  OUT in the frozen source. Purchase has NO paragraph-level gate. Do NOT
    #  add one "for consistency with Sales".
    #
    #  And the frozen source is even emptier here than that block implies. The
    #  commented-out test at L757-L758 guarded the `pl830` leg and sat BEFORE the
    #  `pl055` dispatch at L759; between `pl055` (L760) and `pl060` (L761) the
    #  paragraph has NEVER carried a statement, commented or otherwise. The Sales
    #  route does carry one in that position - `if ws-term-code not = zero / go
    #  to display-menu` [sales/sales.cbl:L765-L766] - and the General Ledger
    #  route carries an equality test in its own equivalent position,
    #  `if ws-term-code = 5` [general/general.cbl:L810-L811]. Three routes, three
    #  different answers, and the divergence IS the specification: a defect
    #  reproduced is correct, a defect fixed is a failure.
    #
    #  Adding a gate here would be invisible in practice today, which is exactly
    #  what makes it dangerous. `pl055` raises 8 and only 8
    #  [purchase/pl055.cbl:L286], and `load000` already stops on 8, so a gate
    #  would change nothing that can currently be observed - and would still be a
    #  behaviour change, because any code in 1..7 would then skip `pl060` where
    #  the frozen program runs it. See Q-CLI-TERMCODE-1-7 in the footer.
    #  ======================================================================

    #  NOT the gate above, and not a substitute for it: this honours `load000`'s
    #  OWN serious-error branch [purchase/purchase.cbl:L703-L704], whose
    #  `go to overrewrite` ends the run unit at `goback`
    #  [purchase/purchase.cbl:L653] so that L761-L762 are never reached. It holds
    #  only ABOVE 7; for every code in 1..7 execution falls straight through to
    #  `pl060`, which is precisely the Purchase behaviour a gate would destroy.
    #  GO TO class 4 - the proof is at the branch itself, in `load000`.
    if _run_unit_ended(term_code):
        return term_code

    #  L761-L762  `move "pl060" to ws-called.` / `go to load000.`
    #  Phase two - the Purchase Orders Posting Report, including the IRS fan-out.
    #
    #  NOTHING MAY FOLLOW THIS. L760 is a `perform`, which comes back; L762 is a
    #  `go to`, which does not - the paragraph ends at the transfer, so there is
    #  no third statement to reproduce and no post-dispatch work to place after
    #  it. The `return` carries the code out for the process status.
    return load000(linkage, _PL060, pl060_order_posting.run)



def _build_parser() -> argparse.ArgumentParser:
    """Compose this route's parser from the shared option fragments.

    Two fragments and no local options: the calling-data group and the Sales and
    Purchase linkage group. The `WS-Calling-Data` binding is NOT redefined here -
    `cli/args.py` owns it, so it has one spelling across all seven routes.

    What the fragments bring, and why each matters on this route:
        `--run-date`      REQUIRED, and the only way a date enters (rule R-6).
        `--ws-caller`     defaulted to the menu's own literal, `move "purchase"
                          to ws-caller` [purchase/purchase.cbl:L475].
        `--ws-cd-args`    the maintainer's unattended-invocation slot
                          [copybooks/wscall.cob:L1-L3]; the shell reads its first
                          five characters at [purchase/purchase.cbl:L457].
        `--irs-instead`   the IRS fan-out switch [copybooks/wssystem.cob:
                          L179-L181]. PIN IT EXPLICITLY for every scenario: it
                          decides WHICH TABLES this route touches, because
                          `pl060` performs the fan-out, and leaving it out makes
                          the affected-table list ambiguous.
        `--date-form`     presentation only; affects no posted figure.

    Not composed, deliberately: `add_gl_linkage_arguments` (that is Shape 1) and
    `add_irs_linkage_arguments` (Shape 3), and NO run-confirm option of any kind,
    because `pl060`'s prompt is commented out at
    [purchase/pl060.cbl:L363-L370].

    Returns:
        The parser. Built on demand, never at import time.
    """
    parser = argparse.ArgumentParser(
        prog=_PROG,
        description=(
            f"{_MENU_OPTION} [purchase/purchase.cbl:L540] - the Purchase "
            "transaction-posting route, `load08.` "
            "[purchase/purchase.cbl:L752-L762]. Runs pl055, the Purchase "
            "Invoice Post Extract, and then pl060, the Purchase Orders Posting "
            "Report, in that order and one at a time."
        ),
        epilog=(
            "NO GATE BETWEEN THE TWO PHASES. The frozen menu has none: the "
            "pl830 leg and its `not = zero` test are commented out at "
            "purchase/purchase.cbl:L755-L758, and no test has ever stood "
            "between pl055 and pl060, so pl060 runs whatever ws-term-code "
            "pl055 leaves. The Sales route does stop there "
            "(sales/sales.cbl:L765-L766); this divergence is reproduced, not "
            "corrected. The route still aborts on a serious error - pl055 "
            "raises 8 when its extract file is missing "
            "(purchase/pl055.cbl:L286) and `if ws-term-code > 7 / go to "
            "overrewrite` (purchase/purchase.cbl:L703-L704) ends the run "
            "before pl060. The exit status IS ws-term-code, unmapped."
        ),
    )
    args.add_calling_data_arguments(parser, default_caller=args.WS_CALLER_PURCHASE)
    args.add_slpl_linkage_arguments(parser)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the Purchase transaction-posting route from the command line.

    The whole CLI boundary: configure logging, parse, bind the five linkage
    operands once, run `load08`, and surface `WS-Term-Code` as the process
    status.

    THE LINKAGE IS BOUND ONCE, NOT PER DISPATCH. In the COBOL these five records
    are the menu shell's own storage, established before the first `CALL` and
    handed unchanged to the second [purchase/purchase.cbl:L695-L699]. Binding
    twice would give `pl060` a fresh `SYSTOT-REC` and lose the period totals
    `pl055` accumulated into it [purchase/pl055.cbl:L582], so it is bound here
    and passed down. `WS-Called` is set per dispatch inside `load000`, which is
    where the frozen source sets it.

    Args:
        argv: the argument vector, without the program name. The real process
            arguments when omitted, which is the case in a real run; a caller
            driving one scenario passes an explicit sequence.

    Returns:
        The process exit status, which IS `WS-Term-Code` - 0 when the route
        completed, 8 when `pl055` found no extract file. `args.exit_status_for`
        is the identity over the `pic 99` domain [copybooks/wscall.cob:L10], so
        nothing here re-encodes or bands the value; see Q-CLI-EXITSTATUS.

    Raises:
        SystemExit: raised by argparse for `--help` and for a malformed argument
            vector, including a missing `--run-date`, and left to propagate with
            argparse's own status and its own message.
        rdbms_params.RdbmsParamError: the deployment contract that supplies the
            six connection parameters is absent or unusable. DELIBERATELY NOT
            CAUGHT, for the reason `cli/args.py` gives at the site that raises
            it: a run that cannot reach the provisioned database must stop before
            it writes anything, because the alternative is a silent connection to
            the placeholder endpoint the frozen copybook declares
            [copybooks/wssystem.cob:L137-L144]. Converting it to a status here
            would also invent an exit code that is not a `WS-Term-Code` value.

    Note:
        A malformed run date is NOT rejected - `args.resolve_clock` reproduces
        the frozen date module falling through without touching its output field
        [common/maps04.cbl:L146] together with the caller pre-zero that turns
        "untouched" into zero [copybooks/Proc-ACAS-Mapser-RDB.cob:L78], so a date
        the legacy module refuses pins `Run-Date` to 0 and the run proceeds.
        Raising instead would add a validation and correct a defect, and this
        migration does neither (rules R-3 and R-4).
    """
    #  CONFIGURED HERE AND ONLY HERE. `basicConfig` mutates the root logger, so a
    #  module that called it at import time would reconfigure logging for
    #  everything that imported it - including a test session and any other
    #  process that reaches `load08` as a library. A process entry point is the
    #  one place with the standing to decide, so this is that place. First
    #  statement, so that anything the binding below reports is already visible.
    logging.basicConfig(level=logging.INFO, format=_LOG_FORMAT)

    namespace = _build_parser().parse_args(argv)

    #  `bind_slpl_linkage` pins the clock from the required `--run-date` and
    #  returns the five operands in COBOL order. `called` seeds `WS-Called` with
    #  the FIRST callee, matching the state the menu is in when it enters
    #  `load08` [purchase/purchase.cbl:L759]; each dispatch then sets the field
    #  itself.
    linkage = args.bind_slpl_linkage(namespace, called=_PL055)

    _LOG.info(
        "%s: pl055 then pl060, no gate between them "
        "[purchase/purchase.cbl:L752-L762]",
        _MENU_OPTION,
    )

    term_code = load08(linkage)

    #  `term_code` IS `linkage.calling_data.ws_term_code` - the shared field the
    #  menu reads after its own dispatch [purchase/purchase.cbl:L701],
    #  [purchase/purchase.cbl:L703] - carried out as a value rather than re-read
    #  so that the route's result and the status cannot disagree.
    return args.exit_status_for(term_code)


if __name__ == "__main__":  # pragma: no cover - module entry point
    raise SystemExit(main())


# --- traceability ---------------------------------------------------------
#
# FUNCTION -> PARAGRAPH  (rule R-5; every span measured against the frozen
# source with a line read, never copied from a planning document)
#   load08           `load08.`     purchase/purchase.cbl:L752-L762
#                    the live statements are L759-L762; L755-L758 are commented
#                    out in the source and are an OMISSION, below
#   load000          `load000.`    purchase/purchase.cbl:L691-L708
#                    reset L694, CALL L695-L700, `< 8` L701-L702,
#                    `> 7` L703-L704, `load000-exit.` L706, `go to
#                    display-menu` L708
#   _run_unit_ended  the predicate of `load000`'s second test,
#                    purchase/purchase.cbl:L703
#   _build_parser    no paragraph - the CLI boundary. The menu's own equivalent
#                    is its screen: `display "(H)  Purchase Transactions Post"`
#                    purchase/purchase.cbl:L540, and the letter-to-paragraph
#                    dispatch table, both out of scope
#   main             no paragraph - the process boundary. The menu has none: it
#                    ends with a bare `goback` purchase/purchase.cbl:L653
#
# PROGRAM -> MODULE  (rule R-5)
#   pl055  ->  acas_posting/programs/pl055_order_proof_extract.py
#              linkage purchase/pl055.cbl:L239-L243, five parameters. The only
#              in-scope raiser on this route: `move 8 to WS-Term-Code`
#              purchase/pl055.cbl:L286, then `goback` L287
#   pl060  ->  acas_posting/programs/pl060_order_posting.py
#              linkage purchase/pl060.cbl:L340-L344, five parameters. Raises no
#              term code at all, and has no run-confirm - see the OMISSIONS
#   The record layouts and the data-access layer are reached only by those two
#   modules; this one imports neither, per the package's import table.
#
# `GO TO` CLASSES  (rule R-5 - one entry per transfer site, and the count is
# part of the record)
#   load000, purchase/purchase.cbl:L703-L704  `go to overrewrite`
#       CLASS 4, sibling re-dispatch. PER-SITE PROOF, in full at the branch:
#       the target persists the two system records and falls through
#       `overclose.` L652 into `goback` L653, so control never returns to the
#       dispatch paragraph, never reaches `load000-exit.` L706 and never
#       reaches the `go to display-menu` at L708. Python returns the code, the
#       caller asks `_run_unit_ended` and dispatches nothing further, and
#       `main` surfaces the code as the status. The two agree on every
#       observable; the sole difference is the persistence `overrewrite` would
#       have performed, recorded as an omission below and identical on the
#       `< 8` path.
#   load000, purchase/purchase.cbl:L708  `go to display-menu`
#       NOT REPRODUCED. `display-menu` purchase/purchase.cbl:L472 is the menu
#       redraw - screen work with no database effect, out of scope. A Python
#       return from `load000` is what "back to the menu" means here.
#   load08
#       NO TRANSFER SITE AT ALL. That is the point of this file: the only
#       transfer the paragraph could have had is the `go to display-menu` at
#       purchase/purchase.cbl:L758, and it is COMMENTED OUT. L762's `go to
#       load000` is the dispatch itself, reproduced as the final call, and
#       nothing follows it because in the COBOL nothing can.
#
# CORRECTIONS  -  each verified with a line read of the frozen source. DO NOT
# "fix" these back to the values the planning documents carry.
#   1. THE SALES AND PURCHASE LINKAGE SHAPE HAS FIVE PARAMETERS, NOT FOUR. One
#      planning section calls it "the four-parameter SL/PL linkage shape"; the
#      source gives five, twice over - the menu passes five at
#      purchase/purchase.cbl:L695-L699 and the callees declare five at
#      purchase/pl055.cbl:L239-L243 and purchase/pl060.cbl:L340-L344. The
#      fifth, relative to the General Ledger shape, is `system-record-4`.
#      `args.SlPlLinkage` has five members and `load000` splats all five.
#   2. THE COMMENTED-OUT GATE GUARDED `pl830`, NOT `pl055`. The test at
#      purchase/purchase.cbl:L757-L758 follows the `pl830` dispatch at L756 and
#      precedes the `pl055` dispatch at L759. Between `pl055` (L760) and
#      `pl060` (L761) the frozen paragraph has no statement at all, commented
#      or otherwise - so Purchase is not "a route whose gate was disabled" in
#      that position; it is a route that never had one there. Sales does, at
#      sales/sales.cbl:L765-L766.
#
# DRIFT NOTE  -  the sibling payment route `load12.` is at
#   purchase/purchase.cbl:L786-L790, measured. One planning document cites
#   L785-L789, which is one line early: L785 is a `*>` separator, L786 is the
#   `load12.` label, L789 is `move "pl100" to ws-called.` and L790 is `go to
#   load000.`. The correct span is already used by this package's own marker.
#   That route belongs to cli/pl_payment_post.py, not here.
#
# OMISSIONS  -  recorded as omissions so that a reader comparing the two trees
# does not conclude something was lost:
#   * `pl830` AND ITS GATE, purchase/purchase.cbl:L755-L758. Already commented
#     out in the frozen source, so there is nothing live to migrate, and the
#     purchase `pl800` autogen series is out of scope in its own right. TWO
#     DIVERGENCES LIVE INSIDE THAT DEAD BLOCK, and both are recorded rather
#     than smoothed: the Sales equivalent is LIVE, `move "sl830" to WS-Called /
#     perform load00` sales/sales.cbl:L759-L760; and it performs `load00`
#     whereas Purchase's dead copy performs `load000`
#     purchase/purchase.cbl:L756 - a different dispatch paragraph, in a block
#     that can no longer run.
#   * `display-menu` purchase/purchase.cbl:L472 and ALL MENU SCREEN I/O,
#     including the menu line this route is selected by, L540; and the
#     letter-to-paragraph dispatch that reaches `load08`. No database effect.
#   * `overrewrite` purchase/purchase.cbl:L621-L651 - the persistence of
#     `System-Record` (File-Key-No 1) and `WS-System-Record-4` (File-Key-No 4)
#     to the relational store and then again to the Cobol parameter file,
#     falling through `overclose.` L652 into `goback` L653. Needs the
#     data-access layer, which this layer may not reach, and lives in an
#     out-of-scope program. Its consequence is stated at the `< 8` branch and
#     carried by Q-CLI-OVERREWRITE below.
#   * `pre-overrewrite`'s backup spool-out `call "SYSTEM" using
#     Full-Backup-Script` purchase/purchase.cbl:L618 - excluded twice, by the
#     spool-out exclusion and by rule R-1.
#   * THE PURE-ACKNOWLEDGEMENT `accept` at purchase/pl055.cbl:L284, whose only
#     effect is to block a terminal. Dropped - but the CONTROL TRANSFER around
#     it is preserved by the callee: `move 8 to WS-Term-Code` L286 then
#     `goback` L287 still happen, which is what this route acts on. Note that
#     the prompt is itself conditional, `if WS-Caller not = "xl150"` L283-L285,
#     so `WS-Caller` changes behaviour there; it stays bindable through
#     `--ws-caller`.
#   * `pl060`'s COMMENTED-OUT `acpt-xrply.` - the label survives at
#     purchase/pl060.cbl:L362 but its whole body, the "OK to post Purchase
#     Transactions (YES/NO) ?" prompt and its `= "NO"` and `not = "YES"` tests,
#     is commented out at L363-L370. There is therefore NO run-confirm
#     parameter for `pl060`, and adding one would invent an input. The sibling
#     payment route has one because purchase/pl100.cbl:L302-L311 is live.
#   * THE OTHER PURCHASE ROUTES, not routed from here and out of scope:
#     `load09.` L764-L768 (pl080, Pay enter), `load10.` L770-L774 (pl085, pay
#     Amend), `load11.` L776-L784 (pl090 under `FS-Cobol-Files-Used`, then
#     pl095). `load12.` L786-L790 (pl100) is in scope but belongs to the
#     sibling payment entry point.
#   * THE PERIOD-TOTAL WRITES THEMSELVES. This route's observable signature is
#     three of the nine sites - purchase invoices purchase/pl055.cbl:L582,
#     purchase credit notes purchase/pl055.cbl:L584 and unapplied purchase
#     credit notes purchase/pl060.cbl:L628 - and every one of them lives in a
#     program module. Nothing is computed here.
#
# ANOMALIES, RECORDED AND NOT FIXED  (rule R-4; the reproductions in this file
# each carry their locator at the site)
#   * THE ABSENT GATE, purchase/purchase.cbl:L755-L758 - reproduced as an
#     ABSENCE, which is the one reproduction that looks like an oversight and
#     is not. `load08` runs `pl060` for every code in 1..7, where Sales would
#     stop.
#   * THE `< 8` / `> 7` THRESHOLDS, purchase/purchase.cbl:L701-L704 - left as
#     the two disjoint tests the menu makes over `pic 99`
#     copybooks/wscall.cob:L10, not collapsed into one comparison.
#   * `go to overrewrite` RATHER THAN `perform overrewrite / goback`,
#     purchase/purchase.cbl:L703-L704 against sales/sales.cbl:L710-L712.
#   * `move zero to ws-term-code` BEFORE EVERY CALL,
#     purchase/purchase.cbl:L694 - per dispatch, not once per route.
#   * `load00`'s WHITELIST, purchase/purchase.cbl:L679-L682, which this route
#     does not use but which is the paragraph next door and is recorded because
#     it is wrong in two ways at once: `"pl090"` appears TWICE, both on L681;
#     and `"pl100"` appears although `pl100` is dispatched through `load000`
#     from `load12.` at L789-L790, so that entry can never be reached. Neither
#     is cleaned up, here or anywhere.
#   * `pl060`'s TERMINATING PERIOD IS PRESENT, purchase/pl060.cbl:L1031, where
#     the Sales sibling's is missing at sales/sl060.cbl:L1172-L1178. Recorded
#     for awareness only and NOT compensated for here: the divergence belongs
#     to the two program modules and is preserved there, not normalised.
#
# AMBIGUITIES  (rule R-6 - compiled behaviour is the tie-breaker; each is
# marked in place at the code it governs and each is to be recorded in
# docs/migration/ambiguity-resolutions.md)
#   Q-CLI-OVERREWRITE   at the `< 8` branch of `load000`. The omitted
#     `overrewrite` is the sole persistence of SYSTEM-REC and SYSTOT-REC, and
#     SYSTOT-REC is where this route's three period totals accumulate. Run the
#     route both ways against one seed and diff those two tables to fix which
#     side of the seeded-state boundary they fall on. Nothing provisional
#     executes at the site: the branch's Python body is a log record either
#     way.
#   Q-CLI-TERMCODE-1-7  at the no-gate block of `load08`. The 1..7 band is
#     unreachable from `pl055` today, so the missing paragraph gate has no
#     observable effect. Confirm against the compiled oracle that no in-scope
#     program sets a code in that band - the census says none does:
#     general/gl070.cbl:L289 sets 5, sales/sl055.cbl:L344 sets 8 and
#     purchase/pl055.cbl:L286 sets 8, and `pl060` sets nothing.
#   Q-CLI-EXITSTATUS    at `main`'s return, and SETTLED in `cli/args.py`, where
#     `exit_status_for` records the evidence: `RETURN-CODE` is read and never
#     written anywhere in the menus or the twelve posting programs, and each
#     menu ends with a bare `goback` purchase/purchase.cbl:L653, so the
#     compiled cycle emits no status derived from `WS-Term-Code` and there is
#     no experiment to run. The identity is a boundary decision, total and
#     lossless over `pic 99`. Nothing here re-encodes it.
#
# RULES  -  NO USER RULES DOCUMENT EXISTS FOR THIS PROJECT: `review_rules`
# reports "No user rules provided." The six below are the Agent Action Plan's
# own, section 0.7.2, and enterprise-standard best practice applies wherever
# they are silent. None has been invented.
#   R-1  No COBOL at runtime - satisfied structurally. The imports of this
#        module are `argparse`, `logging`, `collections.abc`, `typing`,
#        `cli.args` and the two program modules. No child process, no shell
#        out, no foreign-function interface, no toolchain lookup, no import of
#        the comparison-oracle tree, and no option that reaches it. This module
#        runs on a host with no COBOL compiler and no COBOL runtime.
#   R-2  Zero binary floating point - satisfied by type. `WS-Term-Code` is
#        `pic 99` copybooks/wscall.cob:L10 and is an `int`; `to-day` is `str`;
#        the exit status is an `int`. No binary-radix numeric type appears in
#        any signature, option or expression, and this module performs no
#        arithmetic at all.
#   R-3  No new validations, fields or schema, and no concurrency - satisfied
#        by omission. No file-existence pre-check (`pl055` makes that test
#        itself, purchase/pl055.cbl:L278-L280); no gate added between the
#        phases; no run-date validation; no added option beyond the shared
#        fragments; no SQL and no schema access; and no thread, event loop,
#        subordinate process or pool of any kind - the two phases run one at a
#        time in one flow of control.
#   R-4  Anomalies reproduced, never fixed - the register above, each with its
#        locator at the reproduction site. The headline reproduction is an
#        ABSENCE, and the deliberate non-normalisation of the three divergent
#        gate forms is the whole substance of this file.
#   R-5  Full traceability - paragraph-named public functions, a `GO TO` class
#        with a per-site proof at the one transfer site, an explicit record
#        that `load08` has none, and this footer.
#   R-6  Compiled behaviour is the tie-breaker - the run date arrives only as
#        the required `--run-date` and is pinned through `args.resolve_clock`
#        into both observables, so nothing ambient can make two runs of one
#        scenario differ; the three questions above are marked, not guessed.
# -----------------------------------------------------------------------------
