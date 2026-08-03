"""Purchase payment posting - the `pl100` batch entry point.

WHAT THIS MODULE IS
The headless equivalent of one menu letter. `purchase/purchase.cbl` draws
`"(L)  Payment Post"` at [purchase/purchase.cbl:L544] - the twelfth letter, so
the twelfth route - and its dispatch paragraph is `load12.`::

    L786  load12.
    L787 *>------
    L788 *>
    L789       move     "pl100" to ws-called.
    L790       go       to load000.

Two statements. That is the whole route, and the two facts about it that decide
this module's shape are both easy to get wrong:

  * `pl100` IS DISPATCHED THROUGH `load000.`, NOT `load00.` `load000.`
    [purchase/purchase.cbl:L691-L704] passes FIVE arguments; `load00.`
    [purchase/purchase.cbl:L670-L685] passes four, omitting the period-totals
    record. The trap is that `load00`'s own whitelist at
    [purchase/purchase.cbl:L679-L682] NAMES `"pl100"`, so reading that list as
    a routing table sends you to the wrong paragraph and the wrong linkage
    shape. That entry is dead code, and it is recorded as an anomaly in the
    footer rather than tidied away (rule R-4).
  * `load12` HAS NO GATE. It does not test `WS-Term-Code` before or after the
    dispatch, and it dispatches exactly one program. Sales `load11.`
    [sales/sales.cbl:L792-L796] (`sl100`) and General Ledger `load09.`
    [general/general.cbl:L817-L821] (`gl080`) are likewise ungated, whereas
    General Ledger `load08.` [general/general.cbl:L805-L815] tests
    `ws-term-code = 5` between phases and Sales `load07.`
    [sales/sales.cbl:L756-L768] tests `not = zero`. The difference is
    deliberate and is NOT harmonised (rule R-4).

THE LINKAGE SHAPE: FIVE PARAMETERS
`pl100` declares::

    L265  procedure division using ws-calling-data
    L266                           system-record
    L267                           system-record-4
    L268                           to-day
    L269                           file-defs.

[purchase/pl100.cbl:L265-L269] - the Sales/Purchase shape, and the `CALL` in
`load000.` [purchase/purchase.cbl:L695-L699] passes those five in that order.
What this shape adds over the General Ledger's four is exactly
`WS-System-Record-4`, the period-totals record: `pl100` writes period total 9
of 9, `PL-Payments`, at [purchase/pl100.cbl:L396], and that write is the
observable signature of this route. Note the two spellings of the same record -
the caller writes `WS-system-record-4` [purchase/purchase.cbl:L697] and the
callee `system-record-4` [purchase/pl100.cbl:L267]; both are preserved rather
than reconciled. See CORRECTION in the footer: the shape has five parameters,
not four.

THE RUN CONFIRMATION, PROMOTED TO A PARAMETER
`pl100` asks one question before it opens a single file::

    L302  acpt-xrply.
    L303      display "OK to post payment transactions (YES/NO) ? <   > enter {CR}"
    L305      move     spaces to wx-reply.
    L306      accept   wx-reply at 1256 ... update.
    L307      move     function upper-case (wx-reply) to wx-reply.
    L308      if       wx-reply = "NO"
    L309               go to menu-exit.
    L310      if       wx-reply not = "YES"
    L311               go to acpt-xrply.

[purchase/pl100.cbl:L302-L311]. The first file open is `perform Purch-Open.`
at [purchase/pl100.cbl:L313], AFTER both tests, so answering `"NO"` reaches
`menu-exit.` [purchase/pl100.cbl:L467] having opened nothing and written
nothing at all. Agent Action Plan section 0.3.4 is explicit about this class of
statement: "Accept prompts that gate a database write become explicit CLI
parameters with the COBOL default preserved." So the answer is the option pair
`--ok-to-post` / `--no-ok-to-post`, and it is passed to the program as its
`ok_to_post` keyword.

THERE IS NO DEFAULT TO PRESERVE, AND THAT IS THE INTERESTING PART.
[purchase/pl100.cbl:L305] moves SPACES into the reply field, and blank is
neither `"NO"` nor `"YES"`, so [purchase/pl100.cbl:L310-L311] sends control
back to the head of the paragraph and asks again. The `update` phrase on the
accept pre-fills the field with those same spaces, so pressing return alone
re-asks for ever. Only `"YES"` proceeds and only `"NO"` declines: the COBOL has
no defaultable answer at all. The default here is therefore a boundary decision
rather than a transcription - it is to post, that being the only reachable
posting path and what invoking a payment-post command means - and it is marked
`Q-CLI-OKTOPOST` for the compiled oracle to confirm.

The prompt TEXT differs from the Sales sibling's - [purchase/pl100.cbl:L303]
against [sales/sl100.cbl:L311] - in capitalisation, in bracket style and in
carrying an extra `enter {CR}`. The logic is identical. The divergence is
recorded in the footer and nothing else is required of it, the displays
themselves being removed under section 0.3.4.

WHAT THIS MODULE DELIBERATELY IS NOT
It is not a menu. `display-menu`, the `go to load01 ... depending on z` table
[purchase/purchase.cbl:L659-L663], the `overrewrite` persistence of the system
records [purchase/purchase.cbl:L621] and the pre-run backup spool-out
[purchase/purchase.cbl:L618] are all absent, and each absence is recorded in
the footer so that a reader comparing the two files does not conclude something
was lost (section 0.4.3). It is not a clock either: the run date arrives only as
the required `--run-date`, pinned through `args.resolve_clock` into
`acas_posting/clock.py`, which is what makes two runs of one scenario
byte-identical (section 0.8.5).

THE RULES THIS FILE IS HELD TO  (Agent Action Plan section 0.7.2)
R-1 No COBOL at runtime. This module starts no process, loads no shared library
    or foreign-function bridge, resolves no external executable and imports
    nothing from the compiled-oracle tree. `pl100` is reached by importing the
    migrated Python module, and by nothing else.
R-2 Zero binary floating point. This module handles three values and none is a
    float: the run confirmation is a `bool`, `WS-Term-Code` is an `int`
    (`pic 99`, [copybooks/wscall.cob:L10]) and `to-day` is `str`. No arithmetic
    is performed at all.
R-3 No new validations, no new fields, no schema change, no concurrency. The
    run-date text is not judged here, the option list is closed, no SQL is
    emitted and execution is strictly sequential - there is no worker, pool or
    event loop and no option that would create one.
R-4 Legacy behaviour is reproduced, never corrected, and each reproduction site
    below carries its COBOL locator as section 0.7.4 C-4 requires.
R-5 Full traceability - paragraph-named functions, a `GO TO` class at every
    transfer site, and the mandatory footer.
R-6 Compiled behaviour is the tie-breaker. No clock, environment, random or
    identity source is read here; the three open questions are marked in place
    rather than guessed.

Invocation, as `harness/run_python_scenario.sh` performs it::

    python -m acas_posting.cli.pl_payment_post --run-date 21/09/2025 \\
        --irs-instead ' ' [--no-ok-to-post]

`pyproject.toml` declares no `[project.scripts]`, so the module form is the
entry point.
"""

from __future__ import annotations

import argparse
import logging
from collections.abc import Sequence
from typing import Final

from acas_posting.cli import args
from acas_posting.programs import pl100_payment_posting

__all__: Final[tuple[str, ...]] = ("main", "load000", "load12")

#  Module-level logger only. `logging.basicConfig` is called inside `main()` and
#  nowhere else, so importing this module configures nothing, emits nothing and
#  touches no stream: `tests/scenarios/*` import the package, and an import that
#  reconfigured logging would change what an unrelated test observes.
_LOG: Final = logging.getLogger(__name__)

#  THE CALLEE'S PROGRAM-ID, and the literal the COBOL moves into `WS-Called`:
#  `move "pl100" to ws-called.` [purchase/purchase.cbl:L789]. Five characters
#  into a `PIC X(8)` field [copybooks/wscall.cob:L7], so `args.set_called`
#  space-fills it to eight - a receiving-field `MOVE`, not an assignment.
_PROGRAM_ID: Final[str] = "pl100"

#  The two frozen sources this module is derived from, quoted in log records so
#  that a run's output cites the specification it reproduces.
_MENU_SOURCE: Final[str] = "purchase/purchase.cbl"
_PROGRAM_SOURCE: Final[str] = "purchase/pl100.cbl"

#  `display "(L)  Payment Post" at 2104` [purchase/purchase.cbl:L544] - the
#  twelfth menu letter, which is why the dispatch paragraph is `load12`.
_MENU_LETTER: Final[str] = "L"

#  THE RUN-CONFIRMATION DEFAULT, and it is a boundary decision rather than a
#  transcription - see the module docstring and Q-CLI-OKTOPOST on
#  `_add_run_confirmation_argument`. `True` is the COBOL's `"YES"`, the only
#  reply that proceeds past [purchase/pl100.cbl:L310-L311].
_OK_TO_POST_DEFAULT: Final[bool] = True

#  NO TIMESTAMP, DELIBERATELY. `logging`'s default format carries `asctime`,
#  which reads the wall clock - and rule R-6 admits exactly one time source,
#  the pinned `--run-date`. A timestamp would also make two runs of one scenario
#  differ textually, which is the property section 0.8.5 exists to protect. The
#  records go to stderr, which is `basicConfig`'s own default, leaving stdout
#  free of anything but argparse's own usage text.
_LOG_FORMAT: Final[str] = "%(levelname)s %(name)s %(message)s"


def _add_run_confirmation_argument(parser: argparse.ArgumentParser) -> None:
    """Add the `pl100`-only run-confirmation switch pair.

    Defined HERE rather than in `acas_posting.cli.args`, and the placement is
    the point: this prompt belongs to ONE program. The Purchase order-posting
    route has no counterpart at all - `pl060`'s equivalent block
    [purchase/pl060.cbl:L362-L371] is commented out in the frozen source - so a
    shared option would offer an input three of the six Sales/Purchase programs
    have not got, which rule R-3 forbids.

    ONE `add_argument`, TWO SWITCHES. `argparse.BooleanOptionalAction` publishes
    `--ok-to-post` and `--no-ok-to-post` from a single declaration, so the pair
    cannot drift apart and `--help` lists both. The COBOL reply field is three
    characters, `wx-reply pic xxx` [purchase/pl100.cbl:L157], holding `"YES"` or
    `"NO"`; a boolean is the faithful headless form because the field's only two
    acted-upon values are exactly two.

    The `dest` is `ok_to_post`, matching the callee's keyword
    [purchase/pl100.cbl:L302-L311 promoted], so the value travels from argv to
    the program under one name.

    Args:
        parser: the parser to add the pair to. Mutated in place, which is the
            argparse idiom the sibling fragments in `args` also follow.
    """
    # AMBIGUITY Q-CLI-OKTOPOST: purchase/pl100.cbl:L305 moves spaces into
    # wx-reply and L310-L311 re-prompts on blank, so the COBOL has no
    # defaultable answer - only "YES" proceeds; confirm the chosen CLI default
    # against the compiled oracle; record in
    # docs/migration/ambiguity-resolutions.md — left for the compiled oracle to
    # settle (rule R-6).
    parser.add_argument(
        "--ok-to-post",
        action=argparse.BooleanOptionalAction,
        default=_OK_TO_POST_DEFAULT,
        help=(
            "The run confirmation 'OK to post payment transactions (YES/NO) ?' "
            "(purchase/pl100.cbl:L302-L311). This prompt GATES EVERY DATABASE "
            "WRITE the program makes: the first file open is at "
            "purchase/pl100.cbl:L313, after both tests, so --no-ok-to-post "
            "reaches menu-exit (purchase/pl100.cbl:L467) having opened nothing "
            "and written nothing. --ok-to-post is the COBOL's 'YES', the only "
            "reply that proceeds, and is the default: L305 moves spaces into "
            "the reply field and L310-L311 re-asks on anything that is neither "
            "literal, so the original has no defaultable answer to preserve. "
            "The program is invoked either way - declining is a path THROUGH "
            "pl100, not a decision taken before it."
        ),
    )


def _build_parser() -> argparse.ArgumentParser:
    """Compose this route's parser from the shared fragments plus one local pair.

    Three calls, no conditionals, and no option defined here that `args` already
    owns: the `WS-Calling-Data` binding is NOT redefined, so `--ws-caller`,
    `--ws-del-link`, `--ws-process-func`, `--ws-sub-function` and `--ws-cd-args`
    all come from one implementation shared by every entry point. Only the
    run-confirmation pair is local, and only because it is `pl100`'s alone.

    `--ws-caller` defaults to `args.WS_CALLER_PURCHASE`, the literal the frozen
    menu itself moves into the field [purchase/purchase.cbl:L475], because
    purchase/purchase.cbl is the shell that dispatches this route.

    `args.add_slpl_linkage_arguments` supplies the REQUIRED `--run-date` - the
    controlled clock's only input, with no default and no ambient fallback
    (rule R-6) - together with `--date-form` and the `--irs-instead` fan-out
    switch [copybooks/wssystem.cob:L179-L181]. Section 0.6.4 requires that
    switch be pinned explicitly for every scenario, since its state changes
    which tables a run touches and leaving it out makes the affected-table list
    ambiguous.

    Returns:
        A parser that has not parsed anything. Built on demand inside `main()`
        rather than at module scope, so importing this module does no work.
    """
    parser = argparse.ArgumentParser(
        prog="python -m acas_posting.cli.pl_payment_post",
        #  HAND-WRAPPED, because RawDescriptionHelpFormatter (chosen for the
        #  epilog's verbatim COBOL, below) leaves the description unwrapped too.
        description=(
            "Purchase payment posting - pl100.\n"
            "\n"
            f"The headless form of Purchase menu letter ({_MENU_LETTER}) "
            f"'Payment Post' ({_MENU_SOURCE}:L544), dispatched by\n"
            f"`load12.` ({_MENU_SOURCE}:L786-L790) through the "
            f"five-parameter `load000.` ({_MENU_SOURCE}:L691-L704).\n"
            "Posts Purchase cash/payment transactions to the Purchase ledger "
            "and the open-item file, and\n"
            f"writes period total PL-Payments ({_PROGRAM_SOURCE}:L396)."
        ),
        #  The COBOL is quoted verbatim in the epilog, so `--help` carries the
        #  specification it reproduces. RawDescriptionHelpFormatter keeps the
        #  quotation's own line breaks; argparse would otherwise reflow it.
        epilog=(
            "The dispatch route, verbatim from the frozen source:\n"
            "\n"
            f"  {_MENU_SOURCE}\n"
            "    L786  load12.\n"
            '    L789       move     "pl100" to ws-called.\n'
            "    L790       go       to load000.\n"
            "\n"
            "    L691  load000.\n"
            "    L694       move     zero to ws-term-code.\n"
            "    L695       call     ws-called using ws-calling-data\n"
            "    L696                                system-record\n"
            "    L697                                WS-system-record-4\n"
            "    L698                                to-day\n"
            "    L699                                file-defs\n"
            "    L700       end-call\n"
            "    L701       if       ws-term-code < 8\n"
            "    L702                perform overrewrite.\n"
            "    L703       if       ws-term-code > 7\n"
            "    L704                go to overrewrite.\n"
            "\n"
            "load12 has no term-code gate of its own, and that is deliberate:\n"
            "see the module docstring. The exit status is WS-Term-Code itself\n"
            "(pic 99, copybooks/wscall.cob:L10), unmapped.\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    args.add_calling_data_arguments(parser, default_caller=args.WS_CALLER_PURCHASE)
    args.add_slpl_linkage_arguments(parser)
    _add_run_confirmation_argument(parser)
    return parser


#  THE DISPATCH PARAGRAPHS
#  Two functions, two paragraphs, in the COBOL's own source order: the shared
#  dispatch helper `load000.` first, as purchase/purchase.cbl declares it
#  (L691), then the route paragraph `load12.` that transfers to it (L786). Both
#  are named after their paragraph, which is what rule R-5 requires and what
#  makes the traceability footer mechanical rather than editorial.


def load000(linkage: args.SlPlLinkage, *, ok_to_post: bool) -> int:
    """``load000.``  [purchase/purchase.cbl:L691-L704] - the five-parameter dispatch.

    The paragraph, verbatim from the frozen source::

        L691  load000.
        L692 *>------
        L693 *>
        L694       move     zero to ws-term-code.
        L695       call     ws-called using ws-calling-data
        L696                                system-record
        L697                                WS-system-record-4
        L698                                to-day
        L699                                file-defs
        L700       end-call
        L701       if       ws-term-code < 8  *> for pl055 & 060, xl150
        L702                perform overrewrite.
        L703       if       ws-term-code > 7      *> Got a serious (reported) error
        L704                go to overrewrite.

    THIS MODULE'S OWN COPY, ON PURPOSE. `acas_posting.cli.pl_order_post` carries
    a copy of the same paragraph for `pl055` and `pl060`, and the two are NOT
    shared. The duplication mirrors the COBOL, where every menu program carries
    its own `load000` - purchase/purchase.cbl at L691-L704, sales/sales.cbl at
    L698-L712 - and the two copies already differ in a way a shared helper would
    have to erase (see the mechanism note below). Each entry point therefore
    reimplements the paragraph against its own locators.

    Consequently this copy dispatches ONE callee, `pl100`. The COBOL's
    `call ws-called` [purchase/purchase.cbl:L695] is a dynamic call by name and
    so serves `pl055`, `pl060` and `pl100` from one paragraph; here the callee is
    named at the import, because `acas_posting.programs` publishes no dispatch
    table, no registry and no `run` re-export - a caller cannot reach into a
    program any more than a COBOL `CALL` can (section 0.3.3).

    `WS-Term-Code` IS THE RETURN VALUE, and it is read from the linkage record
    rather than tracked separately: `WS-Calling-Data` is passed BY REFERENCE, so
    a callee that sets the field writes into the caller's own storage, and the
    two tests at L701 and L703 read exactly what the callee left there.

    Args:
        linkage: the five bound arguments in COBOL parameter order
            [purchase/pl100.cbl:L265-L269]. MUTATED BY THE DISPATCH - both
            system records and the calling-data block are written through, which
            is how `pl100`'s four `SYSTEM-REC` writes and its `SYSTOT-REC`
            `PL-Payments` write [purchase/pl100.cbl:L396] survive the call.
        ok_to_post: the run confirmation, passed to the program as its
            `ok_to_post` keyword. ALWAYS passed explicitly, never defaulted -
            see `load12`.

    Returns:
        `WS-Term-Code` after the dispatch, as the callee left it. `pic 99`
        [copybooks/wscall.cob:L10], so 0 through 99.
    """
    calling_data = linkage.calling_data

    # [purchase/purchase.cbl:L694]  move zero to ws-term-code.
    # R-4, and the PLACEMENT is the reproduction: the clear happens once per
    # dispatch, immediately before the CALL, not once per run. `WS-Term-Code` is
    # shared linkage storage, so a code left behind by a previous callee would
    # still be there for the next test of it.
    args.reset_term_code(calling_data)

    # [purchase/purchase.cbl:L789]  move "pl100" to ws-called.
    # ISSUED BY `load12`, APPLIED HERE, and the two orderings are equivalent.
    # In the COBOL the MOVE runs in load12 (L789) and the clear above runs in
    # load000 (L694), so the frozen order is L789 then L694 while this function
    # writes the fields the other way round. Per-site proof: the two statements
    # write DISJOINT fields of `WS-Calling-Data` - `WS-Called`
    # [copybooks/wscall.cob:L7] and `WS-Term-Code` [copybooks/wscall.cob:L10] -
    # and no statement between them reads either, the next reader being the CALL
    # itself at L695. Neither field's value depends on the other, so their
    # relative order is unobservable. The MOVE is placed here so that the field
    # provably holds the callee's program-id at the dispatch, which is the
    # property L695 depends on.
    args.set_called(calling_data, _PROGRAM_ID)

    _LOG.info(
        "%s `load000.` [%s:L691-L704] dispatching %s [%s]: "
        "ws-called=%r ws-caller=%r to-day=%r ok-to-post=%s",
        _MENU_LETTER,
        _MENU_SOURCE,
        _PROGRAM_ID,
        _PROGRAM_SOURCE,
        calling_data.ws_called,
        calling_data.ws_caller,
        linkage.to_day,
        ok_to_post,
    )

    # [purchase/purchase.cbl:L695-L700]  call ws-called using ...  end-call.
    # FIVE arguments, positional, in the COBOL's own order - the Sales/Purchase
    # linkage shape [purchase/pl100.cbl:L265-L269]. The run confirmation follows
    # as a keyword because it is not a linkage parameter at all: it is the
    # promoted `acpt-xrply` accept [purchase/pl100.cbl:L302-L311].
    #
    # PASSED EXPLICITLY, ALWAYS. `pl100_payment_posting.run` declares its own
    # default for `ok_to_post`, and this call deliberately does not rely on it:
    # two defaults for one decision could silently drift apart, and the decision
    # is the one marked Q-CLI-OKTOPOST.
    #
    # The first argument is written `linkage.calling_data` rather than the local
    # alias bound above, so that all five read as one uniform list a reviewer can
    # diff straight against the `using` clause at L695-L699. It is the same
    # object either way.
    pl100_payment_posting.run(
        linkage.calling_data,
        linkage.system_record,
        linkage.system_record_4,
        linkage.to_day,
        linkage.file_defs,
        ok_to_post=ok_to_post,
    )

    term_code = calling_data.ws_term_code

    # [purchase/purchase.cbl:L701-L702]
    #     if ws-term-code < 8  *> for pl055 & 060, xl150
    #              perform overrewrite.
    # R-4 [purchase/purchase.cbl:L701-L702]. THE TWO TESTS ARE EXHAUSTIVE:
    # `WS-Term-Code` is `pic 99` [copybooks/wscall.cob:L10], domain 0 through 99,
    # over which `< 8` and `> 7` partition every possible value - so `load000`
    # ALWAYS reaches `overrewrite`, by one branch or the other. The maintainer's
    # own comment names pl055, pl060 and xl150, none of which is the callee on
    # this route; the test is reproduced as written regardless.
    #
    # AMBIGUITY Q-CLI-OVERREWRITE: `overrewrite.`
    # [purchase/purchase.cbl:L621-L650] persists the mutated `System-Record`
    # (File-Key-No 1) and `WS-System-Record-4` (File-Key-No 4) to the RDB and
    # then to the Cobol parameter file, and it is a MENU paragraph - out of scope
    # as a program (section 0.2.2), so this branch reproduces the TEST and not
    # its effect. Which of pl100's writes therefore never reach a table, and
    # whether a scenario diff shows it, must be measured against the compiled
    # oracle; recorded in docs/migration/ambiguity-resolutions.md — left for the
    # compiled oracle to settle (rule R-6).
    if not args.is_serious_error(term_code):
        _LOG.info(
            "%s returned ws-term-code=%d (< %d): `perform overrewrite.` "
            "[%s:L701-L702] - the menu would persist SYSTEM-REC key 1 and "
            "SYSTOT-REC key 4 here; that persistence is an OMISSION, see "
            "Q-CLI-OVERREWRITE",
            _PROGRAM_ID,
            term_code,
            args.SERIOUS_ERROR_THRESHOLD + 1,
            _MENU_SOURCE,
        )
        return term_code

    # [purchase/purchase.cbl:L703-L704]
    #     if ws-term-code > 7      *> Got a serious (reported) error
    #              go to overrewrite.
    # GO TO class 4 (sibling re-dispatch) -> `overrewrite.`
    # [purchase/purchase.cbl:L621].
    #
    # PER-SITE PROOF OF EQUIVALENCE, as class 4 requires.
    #   COBOL:  `go to overrewrite` enters a paragraph that does work (it
    #           persists both system records, L621-L650) and then TRANSFERS
    #           CONTROL ITSELF - it falls through into `overclose.` at L652,
    #           whose single statement is `goback.` at L653. The run unit ends
    #           there. Control never returns to L704, `load000-exit.` at L706 is
    #           never reached, and the `go to display-menu.` at L708 never runs,
    #           so no further program is invoked.
    #   Python: return the serious-error disposition to the caller, which
    #           returns it unchanged through `load12`; `main()` then ends the
    #           process with `args.exit_status_for(term_code)`. No further
    #           program is invoked on this path either, because `load12`
    #           dispatches exactly one.
    #   Proof:  both paths (a) invoke no further program and (b) end the run
    #           unit. They differ in exactly one respect - the COBOL persists
    #           the two system records on the way out and this does not - and
    #           that difference is the `overrewrite` OMISSION recorded in the
    #           footer, identical to the one the `< 8` branch above carries. It
    #           is a property of the menu boundary, not of the class 4 rewrite.
    #
    # R-4, MECHANISM DIVERGENCE FROM SALES - PRESERVED, NOT HARMONISED. Purchase
    # writes `go to overrewrite` [purchase/purchase.cbl:L703-L704]; Sales writes
    # `perform overrewrite` then `goback` [sales/sales.cbl:L710-L712]. The net
    # effect is the same - persist, then end the run unit - but the mechanism
    # genuinely differs, and it is one reason each entry point carries its own
    # copy of this paragraph rather than sharing one.
    #
    # UNREACHABLE IN PRACTICE ON THIS ROUTE, AND IMPLEMENTED ANYWAY. `pl100`
    # never assigns `WS-Term-Code`: only three of the twelve in-scope programs
    # do - `gl070` sets 5 [general/gl070.cbl:L289], `sl055` sets 8
    # [sales/sl055.cbl:L344] and `pl055` sets 8 [purchase/pl055.cbl:L286] - so
    # after this dispatch the field still holds the zero L694 put there. The
    # branch is written because the frozen paragraph writes it, and dropping a
    # statement on the grounds that the current callee cannot trigger it would
    # be an omission rather than a migration.
    _LOG.error(
        "%s returned ws-term-code=%d (> %d): serious error, `go to overrewrite.` "
        "[%s:L703-L704] -> `overclose.` [%s:L652] -> `goback.` [%s:L653]; the "
        "run unit ends and no further program is invoked",
        _PROGRAM_ID,
        term_code,
        args.SERIOUS_ERROR_THRESHOLD,
        _MENU_SOURCE,
        _MENU_SOURCE,
        _MENU_SOURCE,
    )
    return term_code


def load12(linkage: args.SlPlLinkage, *, ok_to_post: bool) -> int:
    """``load12.``  [purchase/purchase.cbl:L786-L790] - the Purchase payment-post route.

    The paragraph, verbatim from the frozen source::

        L786  load12.
        L787 *>------
        L788 *>
        L789       move     "pl100" to ws-called.
        L790       go       to load000.

    NO GATE, AND NOTHING AFTER THE DISPATCH. Two statements: name the callee,
    transfer to the shared dispatch paragraph. There is no test of
    `WS-Term-Code` before or after, and the transfer at L790 is a `go to` rather
    than a `perform`, so control never comes back - `load000` runs to its own
    exit and reaches `display-menu` (L708) or `overrewrite` (L704) on its own
    account. Nothing may follow the dispatch here, and nothing does.

    R-4: the absence of a gate is reproduced as an absence. Sales `load11.`
    [sales/sales.cbl:L792-L796] and General Ledger `load09.`
    [general/general.cbl:L817-L821] are equally ungated, while General Ledger
    `load08.` [general/general.cbl:L805-L815] tests `ws-term-code = 5` between
    its phases and Sales `load07.` [sales/sales.cbl:L756-L768] tests
    `not = zero` twice. Four sibling routes, three different gate policies; the
    difference is deliberate and is not smoothed away.

    Args:
        linkage: as `load000` - the five bound arguments, mutated by the
            dispatch.
        ok_to_post: the run confirmation, forwarded unchanged and explicitly.

    Returns:
        `WS-Term-Code` after the dispatch, unchanged from `load000`.
    """
    # [purchase/purchase.cbl:L789]  move "pl100" to ws-called.
    # The literal is `_PROGRAM_ID`; the `MOVE` itself is applied inside
    # `load000`, where the per-site ordering proof for it lives.
    #
    # [purchase/purchase.cbl:L790]  go to load000.
    # GO TO class 4 (sibling re-dispatch) -> `load000.`
    # [purchase/purchase.cbl:L691]. Per-site proof: the target paragraph does
    # work (it clears the term code, dispatches, and tests the result) and then
    # transfers control itself - to `overrewrite` at L704 or, by falling through
    # `load000-exit.` at L706, to `display-menu` at L708 - so control never
    # returns to L790. The Python form is a call whose value is returned
    # immediately, with no statement after it, which reproduces exactly that:
    # this function contributes nothing further to the run.
    return load000(linkage, ok_to_post=ok_to_post)


def main(argv: Sequence[str] | None = None) -> int:
    """The CLI boundary: bind `argv` to the linkage, run `load12`, report the code.

    Five steps, in this order, and the order is not arbitrary:

    1. PARSE. `_build_parser()` composes the shared fragments plus the local
       run-confirmation pair. A missing `--run-date` is an argparse usage error
       and exits non-zero, which is the mechanically checkable proof that no
       ambient date can enter (rule R-6).
    2. CONFIGURE LOGGING, and only here. The COBOL's diagnostics were screen
       writes with no database effect, so section 0.3.4 turns them into log
       records; `basicConfig` therefore belongs at the process boundary and
       nowhere else. It is a no-op if a host application has already configured
       the root logger, which is the behaviour a library caller wants.
    3. BIND. `args.bind_slpl_linkage` builds the five-parameter shape
       [purchase/pl100.cbl:L265-L269]: it pins BOTH clock observables through
       `args.resolve_clock`, starts each record from the copybook's own declared
       defaults, and resolves the six `SYSTEM-REC` connection fields from the
       deployment contract. Binding happens BEFORE the dispatch so that an
       absent or unusable contract stops the run before anything is written.
    4. DISPATCH. `load12` [purchase/purchase.cbl:L786-L790].
    5. REPORT. `args.exit_status_for` is the identity over `pic 99`
       [copybooks/wscall.cob:L10], so the caller sees the code the cycle
       produced rather than a re-encoding of it.

    NO EXCEPTION IS CAUGHT HERE, and that is deliberate rather than an omission.
    `args.bind_slpl_linkage` raises `rdbms_params.RdbmsParamError` when the
    deployment contract is absent or unusable, and letting it propagate is the
    documented contract of that binder: a run that cannot reach the provisioned
    database must stop before it writes, the alternative being a silent
    connection to the copybook's placeholder endpoint. Catching it to return a
    tidy status would invent an error-handling behaviour the frozen source has
    not got (rule R-3) and would hide a misconfiguration behind an exit code.

    Args:
        argv: the argument vector WITHOUT the program name. `None` - the normal
            case - lets argparse read `sys.argv[1:]` itself. A sequence is
            accepted so that a caller can drive this route in-process, which is
            how the scenario suites invoke it.

    Returns:
        The process exit status: `WS-Term-Code` after the dispatch, unmapped. 0
        when `pl100` reported nothing, which is every run of this route in
        practice - `pl100` never assigns the field.

    Raises:
        SystemExit: raised by argparse for a usage error or for `--help`. Not
            caught: it is argparse's own exit path.
        rdbms_params.RdbmsParamError: the deployment contract is absent or
            unusable. Propagated, per the note above.
    """
    parser = _build_parser()
    parsed = parser.parse_args(argv)

    #  Step 2. THE ONLY `basicConfig` IN THIS MODULE. Stream defaulted to stderr
    #  so that stdout carries nothing but argparse's own output; format carries
    #  no timestamp, so no wall clock is read (rule R-6).
    logging.basicConfig(level=logging.INFO, format=_LOG_FORMAT)

    #  Step 3. Bind the five-parameter shape. `called=` fills `WS-Called` from
    #  the callee's program-id and, through it, selects the Purchase menu as the
    #  caller; `--ws-caller` still overrides that. The run date is pinned here
    #  and nowhere else.
    linkage = args.bind_slpl_linkage(parsed, called=_PROGRAM_ID)

    _LOG.info(
        "Purchase menu letter (%s) 'Payment Post' [%s:L544] -> `load12.` "
        "[%s:L786-L790]: run-date=%r ok-to-post=%s",
        _MENU_LETTER,
        _MENU_SOURCE,
        _MENU_SOURCE,
        linkage.to_day,
        parsed.ok_to_post,
    )

    #  Step 4. The route. `ok_to_post` is read from the namespace and passed
    #  explicitly all the way down to `run()`, so the CLI default and the
    #  program's own default cannot drift apart.
    term_code = load12(linkage, ok_to_post=parsed.ok_to_post)

    #  Step 5. `Q-CLI-EXITSTATUS` was settled in `args.exit_status_for`, which
    #  establishes that the compiled cycle emits NO exit status derived from
    #  `WS-Term-Code` at all - every occurrence of `RETURN-CODE` in the five
    #  menus and all twelve posting programs is a READ of what a
    #  `call "SYSTEM"` left behind, e.g. [purchase/purchase.cbl:L434], and the
    #  menus end with a bare `goback` [purchase/purchase.cbl:L653]. The process
    #  boundary is therefore new in the migration and the identity is adopted
    #  because it loses nothing. This route re-uses that decision and does not
    #  re-encode the value.
    return args.exit_status_for(term_code)


if __name__ == "__main__":
    #  `harness/run_python_scenario.sh` invokes these modules directly -
    #  `python -m acas_posting.cli.pl_payment_post` - because pyproject.toml
    #  declares no `[project.scripts]` console entry point.
    raise SystemExit(main())


# =============================================================================
# --- traceability ---
# =============================================================================
# Required by R-5 (Agent Action Plan section 0.7.2): every program maps to a
# module, every paragraph to a function, every field to a data-dictionary entry.
# Section 0.7.4 C-4 adds that every paragraph keeps a named function even where
# its `GO TO` becomes a `continue`, a `break` or a `return`, and section 0.4.3
# that deliberate omissions are recorded as omissions "so that a reader
# comparing the two files does not conclude something was lost".
#
# -----------------------------------------------------------------------------
# FUNCTION -> PARAGRAPH.  Three functions; two are paragraphs, one is the
# boundary the migration adds.
# -----------------------------------------------------------------------------
#   load000                       -> purchase/purchase.cbl `load000.` L691-L704
#                                    (`move zero to ws-term-code.` L694; the
#                                    five-parameter `call` L695-L700; the `< 8`
#                                    test L701-L702; the `> 7` test L703-L704.
#                                    `load000-exit.` L706 and its
#                                    `go to display-menu.` L708 are menu
#                                    control flow - see OMISSIONS)
#   load12                        -> purchase/purchase.cbl `load12.` L786-L790
#                                    (`move "pl100" to ws-called.` L789;
#                                    `go to load000.` L790)
#   main                          -> NO PARAGRAPH. The CLI boundary, which is
#                                    new in the migration: the original had a
#                                    menu letter here, `(L)  Payment Post`
#                                    [purchase/purchase.cbl:L544], reached
#                                    through `display-menu` and the
#                                    `go to load01 ... depending on z` table
#                                    [purchase/purchase.cbl:L659-L663]. Both are
#                                    omitted; the letter survives only as the
#                                    documented origin of the route.
#   _add_run_confirmation_argument -> purchase/pl100.cbl `acpt-xrply.` L302-L311,
#                                    as an ARGUMENT DEFINITION rather than a
#                                    reproduction: the paragraph itself is
#                                    reproduced in the callee, by
#                                    `_init01__acpt_xrply`.
#   _build_parser                 -> NO PARAGRAPH. Argument composition.
#
# -----------------------------------------------------------------------------
# PROGRAM -> MODULE
# -----------------------------------------------------------------------------
#   pl100  ->  acas_posting/programs/pl100_payment_posting.py
#              `run(ws_calling_data, system_record, system_record_4, to_day,
#              file_defs, *, ok_to_post)`, whose five positional parameters are
#              the LINKAGE SECTION list `procedure division using
#              ws-calling-data / system-record / system-record-4 / to-day /
#              file-defs.` [purchase/pl100.cbl:L265-L269], in order.
#              Boundary: THE WHOLE PROGRAM. Migrated in full, unlike gl051 and
#              irs030 which are partial.
#              Route: purchase/purchase.cbl `load12.` -> `load000.` -> pl100.
#              Observable signature of this route: period total 9 of 9,
#              `PL-Payments`, written at [purchase/pl100.cbl:L396] into
#              `SYSTOT-REC` [copybooks/wssys4.cob:L28] - one of the nine
#              period-total write sites section 0.6.4 enumerates.
#
# -----------------------------------------------------------------------------
# PROMOTED PARAMETER -> LOCATOR
# -----------------------------------------------------------------------------
#   --ok-to-post / --no-ok-to-post   (dest `ok_to_post`, default True)
#       -> purchase/pl100.cbl `acpt-xrply.` L302-L311, promoted under section
#          0.3.4: "Accept prompts that gate a database write become explicit CLI
#          parameters with the COBOL default preserved."
#       *  L303-L304  the prompt "OK to post payment transactions (YES/NO) ?
#                     <   > enter {CR}" - display only, removed.
#       *  L305       `move spaces to wx-reply.` - the reply starts BLANK.
#       *  L306       `accept wx-reply ... update` - the accept this option
#                     replaces. `update` pre-fills the field with those spaces.
#       *  L307       `move function upper-case (wx-reply) to wx-reply.`
#       *  L308-L309  `if wx-reply = "NO" / go to menu-exit.` - declines, having
#                     opened nothing: the first open is `perform Purch-Open.` at
#                     L313, after both tests, so ZERO writes on this path.
#       *  L310-L311  `if wx-reply not = "YES" / go to acpt-xrply.` - blank
#                     RE-PROMPTS, so pressing return alone asks again for ever.
#       *  Consequence: only "YES" proceeds and only "NO" declines, so THE COBOL
#          HAS NO DEFAULTABLE ANSWER. The CLI default of True is a boundary
#          decision, marked Q-CLI-OKTOPOST below.
#       *  Passed EXPLICITLY at the dispatch, never left to the callee's own
#          default, so two defaults for one decision cannot drift apart.
#
# -----------------------------------------------------------------------------
# `GO TO` CLASSES.  Section 0.4.2's four-class taxonomy, per site.
# -----------------------------------------------------------------------------
#   purchase/purchase.cbl:L790  `go to load000.`
#       CLASS 4 (sibling re-dispatch). Reproduced in `load12` as a call whose
#       value is returned immediately with no statement after it. Per-site proof
#       at the site.
#   purchase/purchase.cbl:L704  `go to overrewrite.`   (the `> 7` branch)
#       CLASS 4 (sibling re-dispatch). Reproduced in `load000` as the return of
#       the serious-error disposition. Per-site proof at the site: `overrewrite`
#       persists both system records, falls through `overclose.` L652 to
#       `goback.` L653, and the run unit ends - control never returns to L704,
#       `load000-exit.` L706 is never reached and `display-menu` is never
#       entered, so no further program is invoked. The Python path invokes no
#       further program either and ends the process with the same code. The two
#       differ in exactly one respect, the omitted persistence, recorded under
#       OMISSIONS.
#   purchase/pl100.cbl:L309     `go to menu-exit.`     (the reply is "NO")
#       CLASS 3 (section exit). NOT reproduced here - this module promotes the
#       decision to an argument; the transfer itself is reproduced in the callee.
#   purchase/pl100.cbl:L311     `go to acpt-xrply.`    (the reply is neither)
#       CLASS 1 (loop-back): the target is the head of the very paragraph the
#       transfer is issued from [purchase/pl100.cbl:L302], and its purpose is to
#       iterate. NOT reproduced here, for the same reason as L309.
#       DIVERGENT CLASSIFICATION, RECORDED RATHER THAN RESOLVED: the reproducing
#       module `programs/pl100_payment_posting.py` classifies this same transfer
#       CLASS 4 and supplies a per-site proof for it, on the ground that
#       `acpt-xrply` performs work (a display and an accept) before transferring
#       control itself - and section 0.4.2 does direct that an interactive retry
#       loop "gates a database write, in which case it is treated as Class 4",
#       which this one does. Both readings describe the same transfer, both are
#       traceable, and the site is annotated in the file that reproduces it. No
#       behaviour depends on which label is preferred.
#   purchase/purchase.cbl:L708  `go to display-menu.`  (`load000-exit.`)
#       CLASS 4 in the original, and OUT OF SCOPE: the target is the menu draw.
#       See OMISSIONS.
#
# -----------------------------------------------------------------------------
# DRIFT NOTE - `load12`'s span
# -----------------------------------------------------------------------------
#   MEASURED: purchase/purchase.cbl L786-L790, verified statement by statement -
#   `load12.` at L786, the comment rules at L787-L788, `move "pl100" to
#   ws-called.` at L789 and `go to load000.` at L790.
#   Two planned artefacts cite L785-L789 instead, one line early:
#     * the `acas_posting/__main__.py` route table, and
#     * the callee's own docstring, `pl100_payment_posting.run`, which cites
#       "[purchase/purchase.cbl:L785-L789] (`load12`)".
#   `acas_posting/cli/__init__.py`'s footer already carries the measured span.
#   This module cites the measured span throughout. The drift is recorded, not
#   propagated, and neither cited file is edited from here.
#
# -----------------------------------------------------------------------------
# CORRECTION - the Sales/Purchase linkage shape has FIVE parameters
# -----------------------------------------------------------------------------
#   Section 0.4.1.1 describes this route as passing "the four-parameter SL/PL
#   linkage shape". It is FIVE. Section 0.1.1 says five, the callee declares five
#   [purchase/pl100.cbl:L265-L269] and the `CALL` passes five
#   [purchase/purchase.cbl:L695-L699]. The fifth - strictly, the third in order -
#   is `WS-System-Record-4`, the period-totals record, and it is exactly what
#   distinguishes `load000.` from `load00.` [purchase/purchase.cbl:L670-L685],
#   which passes four. Dispatching this route through the four-parameter
#   paragraph would drop the record that carries `PL-Payments`.
#
# -----------------------------------------------------------------------------
# PRESERVED COSMETIC DIVERGENCE - the prompt literal
# -----------------------------------------------------------------------------
#   purchase/pl100.cbl:L303  "OK to post payment transactions (YES/NO) ?
#                             <   > enter {CR}"
#   sales/sl100.cbl:L311     "OK to Post Payment Transactions (YES/NO) ?
#                             [   ]"
#   Three differences - capitalisation, `<   >` against `[   ]`, and the extra
#   `enter {CR}` - and the LOGIC IS IDENTICAL at both sites. Recorded because
#   R-4 makes divergence between siblings evidence rather than untidiness. The
#   displays themselves are removed under section 0.3.4, so the divergence needs
#   nothing else of this module; the two option pairs are named alike because
#   they promote the same decision, not because the literals were reconciled.
#
# -----------------------------------------------------------------------------
# OMISSIONS - present in the frozen menu, deliberately absent here
# -----------------------------------------------------------------------------
#   * `display-menu` and ALL menu screen I/O, including the menu letters
#     themselves [purchase/purchase.cbl:L544 among them] and every `ACCEPT` that
#     merely pauses for acknowledgement; and the dispatch table
#     `go to load01 load02 ... load12 ... depending on z`
#     [purchase/purchase.cbl:L659-L663] with its `loader.` fall-back L665-L668.
#     Section 0.3.4: presentation is removed rather than reimplemented.
#   * `overrewrite.` [purchase/purchase.cbl:L621] and its PERSISTENCE OF THE
#     SYSTEM RECORDS - `System-Record` under File-Key-No 1 and
#     `WS-System-Record-4` under File-Key-No 4, written first to the RDB
#     (L622-L634) and then to the Cobol parameter file (L638-L650) - falling
#     through `overclose.` L652 to `goback.` L653. BOTH branches of `load000`
#     reach it in the original and NEITHER reproduces its effect here: it is a
#     menu paragraph, and the menus are out of scope as programs (section 0.2.2).
#     Marked Q-CLI-OVERREWRITE, because which of `pl100`'s writes consequently
#     never reach a table is an oracle question.
#   * `pre-overrewrite.` [purchase/purchase.cbl:L602-L619] and its backup
#     spool-out `call "SYSTEM" using Full-Backup-Script`
#     [purchase/purchase.cbl:L618] - excluded twice over: by section 0.2.2's
#     spool-out exclusion, and by R-1, which forbids this package from starting a
#     process at all.
#   * The `menu-return.` presentation block [purchase/pl100.cbl:L296-L301] -
#     `display prog-name` L298, the `"Purchase Cash Posting"` banner L299,
#     `perform zz070-Convert-Date.` L300 and `display ws-date` L301. Display
#     only. The date conversion belongs to `acas_posting/dates.py` and is owned
#     by the callee; this module does not import it and performs no date work.
#   * The other Purchase routes, NOT ROUTED from this module and each dispatched
#     by its own paragraph: `load09.` L764-L768 (`pl080`, Payment Input),
#     `load10.` L770-L774 (`pl085`, Payment Amend), `load11.` L776-L784
#     (`pl090` under `FS-Cobol-Files-Used` then `pl095`, Payment Proof) and
#     `load13.` L792-L796 (`pl070`). All four are out of scope under section
#     0.2.2 - interactive entry, amendment and report programs. Note that all
#     four go through `load00.`, the FOUR-parameter paragraph, not `load000.`.
#   * `load08.` L752-L762 (`pl055` then `pl060`) is in scope but belongs to the
#     sibling entry point `acas_posting/cli/pl_order_post.py`, which carries its
#     own copy of `load000`. Not imported from here, and not imported into here.
#   * `acas_posting.clock` is NOT imported, though it is this file's dependency.
#     The clock contract is reached transitively and in exactly one place:
#     `args.bind_slpl_linkage` -> `args.resolve_clock` -> `clock.pin_from_to_day`,
#     which pins both observables - the text `to-day pic x(10)` and the binary
#     `Run-Date` [copybooks/wssystem.cob:L67]. A direct import here would be
#     unused, and a second pinning path would be a second place for the run date
#     to come from, which is precisely what R-6 forbids.
#
# -----------------------------------------------------------------------------
# ANOMALIES - reproduced or recorded, never fixed (R-4)
# -----------------------------------------------------------------------------
#   * `load00`'s whitelist [purchase/purchase.cbl:L679-L682] names `"pl090"`
#     TWICE, both occurrences on L681: `or "pl090" or "pl090" or "pl100" ...`.
#     The duplicate is redundant in an `or` chain and so has no effect. RECORDED,
#     NOT CLEANED UP.
#   * The same whitelist names `"pl100"`, also on L681 - and it is DEAD CODE.
#     `pl100` is dispatched by `load12.` L786-L790 through `load000.`
#     [purchase/purchase.cbl:L790], and `load000` performs `overrewrite`
#     unconditionally (its two tests being exhaustive), so `load00`'s conditional
#     `perform overrewrite` for `"pl100"` can never be reached on any route.
#     RECORDED, NOT CLEANED UP. Reading that whitelist as a routing table is the
#     trap this module's docstring warns about: it names the wrong dispatch
#     paragraph and so the wrong linkage shape.
#   * `load12` HAS NO TERM-CODE GATE [purchase/purchase.cbl:L786-L790], while
#     General Ledger `load08.` [general/general.cbl:L805-L815] tests
#     `ws-term-code = 5` and Sales `load07.` [sales/sales.cbl:L756-L768] tests
#     `not = zero` twice. Reproduced AS AN ABSENCE - `load12` performs no test.
#   * The `< 8` / `> 7` thresholds [purchase/purchase.cbl:L701-L704] are
#     exhaustive over `pic 99` [copybooks/wscall.cob:L10], so the "conditional"
#     persistence is unconditional. Reproduced as written, both branches present.
#   * Purchase's serious-error mechanism is `go to overrewrite`
#     [purchase/purchase.cbl:L703-L704] where Sales' is `perform overrewrite`
#     then `goback` [sales/sales.cbl:L710-L712]. Same net effect, different
#     mechanism. PRESERVED, not harmonised - and one reason each entry point
#     keeps its own copy of `load000`.
#   * `move zero to ws-term-code` [purchase/purchase.cbl:L694] runs once per
#     dispatch, immediately before the `CALL`. Reproduced at that placement.
#   * `pl100` NEVER ASSIGNS `WS-Term-Code`. Only three of the twelve in-scope
#     programs do: `gl070` sets 5 [general/gl070.cbl:L289], `sl055` sets 8
#     [sales/sl055.cbl:L344] and `pl055` sets 8 [purchase/pl055.cbl:L286]. The
#     `> 7` branch is therefore unreachable on this route in practice. Written
#     anyway, and annotated as unreachable at the site.
#   * Only `"YES"` proceeds and a blank reply re-prompts
#     [purchase/pl100.cbl:L305], [purchase/pl100.cbl:L310-L311]. Reproduced as
#     the absence of a preserved default, marked Q-CLI-OKTOPOST rather than
#     resolved by assumption.
#   * `wssys4.cob`'s two Purchase-group spares carry the SALES prefix -
#     `sl4-spare3` and `sl4-spare4` inside `Purchase-Ledger-Data`
#     [copybooks/wssys4.cob:L29-L30], anomaly 20 of the register. Nothing for
#     this module to do: the record is bound by `args` and written by the callee,
#     and the misnaming is preserved by the record layer.
#
# -----------------------------------------------------------------------------
# AMBIGUITIES - each recorded in docs/migration/ambiguity-resolutions.md
# -----------------------------------------------------------------------------
#   Q-CLI-OKTOPOST     OPEN. The run-confirmation default. L305 blanks the reply
#                      and L310-L311 re-prompts on blank, so the COBOL has no
#                      defaultable answer; True (post) is adopted as the only
#                      reachable posting path. Marked at
#                      `_add_run_confirmation_argument`.
#   Q-CLI-OVERREWRITE  OPEN. `overrewrite`'s persistence of SYSTEM-REC key 1 and
#                      SYSTOT-REC key 4 is omitted with the menus, so which of
#                      `pl100`'s writes never reach a table - and whether a
#                      scenario diff shows it - must be measured. Marked at the
#                      `< 8` branch in `load000`.
#   Q-CLI-EXITSTATUS   SETTLED UPSTREAM, in `args.exit_status_for`, which
#                      establishes that there is no oracle observable to consult:
#                      `RETURN-CODE` is READ and never WRITTEN anywhere in the
#                      five menus or the twelve posting programs - every
#                      occurrence tests what a `call "SYSTEM"` left behind, e.g.
#                      [purchase/purchase.cbl:L434] - and the menus end with a
#                      bare `goback` [purchase/purchase.cbl:L653]. The identity
#                      is adopted because it is total and lossless over `pic 99`.
#                      This route re-uses that decision unchanged.
#
# -----------------------------------------------------------------------------
# RULE COMPLIANCE, per rule (section 0.7.2). No user rules document exists -
# `review_rules` reports none - so these six, from the Agent Action Plan, are the
# binding set.
# -----------------------------------------------------------------------------
#   R-1  No COBOL at runtime. The import list is closed at six: argparse,
#        logging, collections.abc, typing, `acas_posting.cli.args` and
#        `acas_posting.programs.pl100_payment_posting`. This module starts no
#        process, loads no shared library and binds no foreign function; it
#        resolves no external executable; and it imports nothing from the
#        compiled-oracle tree, so there is NO import path from this module to
#        that tree. Its option list, printed in full by `--help`, offers nothing
#        that would select, drive or compare against a compiled program: the
#        only options are the five `WS-Calling-Data` fields, the run date, the
#        two `SYSTEM-REC` fields and the one run-confirmation pair.
#   R-2  Zero binary floating point. Three values pass through this module and
#        none is a float: `ok_to_post` is `bool`, `WS-Term-Code` is `int`
#        (`pic 99`, [copybooks/wscall.cob:L10]) and `to-day` is `str`. No
#        arithmetic is performed here at all - `pl100`'s payment-days average
#        [purchase/pl100.cbl:L498], [purchase/pl100.cbl:L502] is integer
#        truncation over `binary-long` and belongs to the callee; it is neither
#        reimplemented nor compensated for here.
#   R-3  No new validations, fields, schema or concurrency. The run-date text is
#        not judged (see `args.resolve_clock`); the option list is closed at the
#        shared fragments plus one local pair, and no `--rdbms-*` option is
#        added; no SQL is emitted; no field is added to any record; and execution
#        is strictly sequential - no threading, asyncio, multiprocessing or
#        concurrent.futures, and no `--parallel`, `--jobs`, `--workers` or
#        `--threads`.
#   R-4  Legacy behaviour reproduced, never corrected - see ANOMALIES above, each
#        with its locator at the reproduction site as section 0.7.4 C-4 requires.
#   R-5  Full traceability - this footer, the paragraph-named `load000` and
#        `load12`, and a `GO TO` class at every transfer site.
#   R-6  Compiled behaviour is the tie-breaker. No `datetime.now`, `date.today`,
#        `utcnow`, `time.time`, `time.monotonic`, `random`, `uuid`, `os.environ`
#        or `os.getenv` appears here; the run date arrives only as the REQUIRED
#        `--run-date` and is pinned once, through `args.resolve_clock` into
#        `acas_posting/clock.py`, reproducing the single clock read in the whole
#        call chain [copybooks/Proc-ACAS-Mapser-RDB.cob:L72-L80]. The log format
#        carries no timestamp for the same reason. Two runs of one scenario under
#        the same pinned clock are therefore byte-identical (section 0.8.5).
#
# THE FREEZE. Nothing under common/, copybooks/, general/, sales/, purchase/,
# irs/, stock/ or mysql/ is read as anything but specification here, and nothing
# is written to any of them. Every locator above was verified against the frozen
# source; any diff touching those paths is a defect in the migration.
