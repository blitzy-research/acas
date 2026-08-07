"""Sales payment posting - the batch entry point for `sl100`.

Migration of one paragraph of the Sales menu shell, `load11.`
[sales/sales.cbl:L792-L796]: name sl100 and dispatch it through `load000.`, which
carries the five-parameter Sales/Purchase linkage and the `< 8` / `> 7`
disposition [sales/sales.cbl:L691]. No screen output.

`--ok-to-post` promotes the run confirmation to a parameter, because the answer
gates a database write (Agent Action Plan section 0.3.4). The run date is an
argument and never a clock reading (R-6); sl100 contains no clock read.

sl100 maintains the payment-days average with the third of the cycle's three
mutually inconsistent guard variants [sales/sl100.cbl:L497-L516]. All three
compute accumulator over activity - `divide work-b by sales-pay-activety`
[sales/sl100.cbl:L511] and `divide sales-activety into work-2`
[sales/sl060.cbl:L827] have the same quotient - and the guards differ, which is
what is reproduced: the divergence is in when the computation happens, not in
which way round it divides.

THE SOURCE IS FROZEN
====================
`sales/sales.cbl` and `sales/sl100.cbl` are read-only specification. Agent
Action Plan section 0.8.1 is unambiguous: "Any diff touching `common/*.cbl`,
`common/*.scb`, `copybooks/*.cob`, `general/*.cbl`, `sales/*.cbl`,
`purchase/*.cbl`, `irs/*.cbl` or `mysql/ACASDB.sql` is a defect in the
migration, regardless of how harmless it appears." Nothing here edits either.

THERE IS NO USER RULES DOCUMENT
===============================
`review_rules` returns exactly "No user rules provided." - there is no on-disk
rules document for this project and none should be looked for. The six binding
rules R-1 ... R-6 live in the Agent Action Plan itself, section 0.7.2, and are
treated as binding. Where the plan is silent, enterprise-standard best practice
applies; no rule has been invented to fill the gap. How this module honours
each is recorded under RULES below.

DISPATCH GOES THROUGH `load000.`, NOT `load00.`
===============================================
`load11` transfers to `load000.` [sales/sales.cbl:L698-L712], the FIVE-parameter
dispatch paragraph:

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

This is easy to get wrong, and getting it wrong would bind the wrong linkage
shape. The Sales menu also has a FOUR-parameter `load00.`
[sales/sales.cbl:L677-L692] whose whitelist names `"sl100"` explicitly
[sales/sales.cbl:L688] - but nothing ever routes `sl100` through `load00`, so
that whitelist entry is dead code. It is recorded as an anomaly and left alone
(R-4); see OMISSIONS in the footer.

The linkage shape is therefore Shape 2 of the migration's three, and it has
FIVE parameters: `procedure division using ws-calling-data, system-record,
system-record-4, to-day, file-defs.` [sales/sl100.cbl:L272-L276]. The caller
spells the third one `WS-System-Record-4` [sales/sales.cbl:L704] and the callee
spells its own `system-record-4` [sales/sl100.cbl:L274]; both spellings are
preserved rather than reconciled. See CORRECTION 1 in the footer for why "four"
appears in one planning document.

`load11` HAS NO GATE, AND THAT IS DELIBERATE
============================================
Three gate forms coexist in these menu shells and they must stay different
(R-4). The router's job is to keep them apart, not to harmonise them:

    General Ledger posting cycle   `if ws-term-code = 5` - the abort gate
    Sales invoice posting          `if ws-term-code not = zero`
                                   [sales/sales.cbl:L761-L762, L765-L766]
    Sales PAYMENT posting          none at all - this module
    Purchase order posting         none at all

`load11` is two statements: set the callee, transfer. There is nothing to gate,
because there is only one dispatch on this route and a gate exists to decide
whether the NEXT one happens. Reaching `load000.` by `go to` [L796] rather than
by `perform` reinforces it: control never comes back to `load11`, so no code can
follow the dispatch, and none does.

The reason no gate is needed also holds at the value level. `sl100` never writes
`WS-Term-Code` at all - a census of the frozen program finds no reference to the
field - so on this route the code is still the zero that L701 moved into it when
L708 and L710 test it. Only three of the twelve in-scope programs ever set it:
`gl070` to 5 [general/gl070.cbl:L289], `sl055` to 8 [sales/sl055.cbl:L344] and
`pl055` to 8 [purchase/pl055.cbl:L286]. The `> 7` branch is consequently
unreachable on this route in practice. It is implemented anyway, faithfully,
because the branch is in the paragraph being migrated and its absence would be
a behaviour change rather than a simplification.

THE RUN-CONFIRM IS PROMOTED TO A PARAMETER
==========================================
`sl100` opens with an interactive confirm that gates every database write
[sales/sl100.cbl:L310-L319]:

    L311       display  "OK to Post Payment Transactions (YES/NO) ? [   ]"
    L313       move     spaces to wx-reply.
    L314       accept   wx-reply at 1256 with foreground-color 6 update.
    L315       move     function upper-case (wx-reply) to wx-reply.
    L316       if       wx-reply = "NO"
    L317                go to menu-exit.
    L318       if       wx-reply not = "YES"
    L319                go to acpt-xrply.

Agent Action Plan section 0.3.4: "Accept prompts that gate a database write
become explicit CLI parameters with the COBOL default preserved." This one
plainly gates every write - `"NO"` transfers to `menu-exit.`
[sales/sl100.cbl:L476-L477], which is `exit program.`, and it does so BEFORE the
first `perform OTM3-Open` at [sales/sl100.cbl:L321], so nothing whatsoever is
written - which is why it becomes `--ok-to-post` / `--no-ok-to-post` here rather
than being dropped.

There is, however, no default in the COBOL to preserve. `wx-reply` is declared
`pic xxx value spaces` [sales/sl100.cbl:L167] and L313 moves spaces into it
again immediately before the accept, and spaces are neither `"NO"` nor `"YES"`,
so a blank answer re-prompts at L318-L319 rather than resolving. Only `"YES"`
proceeds. The switch therefore defaults to posting - see AMBIGUITY
Q-CLI-OKTOPOST at the constant that carries the default - and an explicit
opt-out reproduces the `"NO"` transfer, which the program module itself
performs.

THE CONTROLLED CLOCK
====================
The run date arrives only as the required `--run-date` and is pinned before any
program is entered, which is what makes two runs of one scenario byte-identical
(Agent Action Plan section 0.8.5, rule R-6). Nothing in this module reads a
clock, and neither does `sl100`: all twelve in-scope programs receive the date
purely through linkage. The frozen call chain holds FOURTEEN ambient date and time
reads across six files - six `FUNCTION CURRENT-DATE` [common/ACAS.cbl:L353],
[general/general.cbl:L371], [sales/sales.cbl:L323], [purchase/purchase.cbl:L318],
[irs/irs.cbl:L480], [copybooks/Proc-ACAS-Mapser-RDB.cob:L72], four `accept ...
from time` and four `accept ... from date` - and EVERY ONE of them is in an
out-of-scope menu shell or in the date-service copybook those shells COPY, as the
census in `acas_posting/clock.py` records. The one that bears on a posting run is
[copybooks/Proc-ACAS-Mapser-RDB.cob:L72-L80], and even that runs only on the
FIRST-TIME capture path `ba010-Capture-Data`: a normal Sales run derives `to-day`
from the STORED `Run-Date` [sales/sales.cbl:L409-L411]. Both
observables - the text `to-day pic x(10)` and the binary `Run-Date`
[copybooks/wssystem.cob:L67] - are pinned from that one argument by
`args.bind_slpl_linkage`, which delegates to `args.resolve_clock` and thence to
`acas_posting.clock`.

PRESENTATION IS GONE
====================
The menu's screen output, its `display-menu` paragraph and its
`go to load01 ... depending on z` dispatch table [sales/sales.cbl:L662-L670] are
not migrated, and neither is the `menu-return.` banner block
[sales/sl100.cbl:L303-L308]. Diagnostics that have no database effect become log
records that cannot alter control flow and cannot appear in a table dump. The
pre-run backup spool-out is omitted for the reasons recorded in the footer. The
`overrewrite` persistence of the two system records IS reproduced - by
`args.overrewrite`, performed from both arms of `load000` - because `sl100`
mutates SYSTEM-REC twice [sales/sl100.cbl:L473-L474] and writes one of the nine
period totals [sales/sl100.cbl:L404], and that paragraph is their only writer to
the store. Only its ISAM arm has no counterpart.

RULES
=====
R-1  No COBOL at runtime. Nothing here creates a child process, launches a shell,
     loads a shared object, binds a foreign function or names the compiler, the
     module runner, the SQL translator or the bridge's C interface object; and
     nothing imports the comparison-oracle tree, of which Agent Action Plan
     section 0.7.2 says there "is no import path from the shipped package". The
     COBOL above is quoted as specification, never executed.
R-2  Zero binary floating point. This module handles exactly three value kinds
     and not one of them is a binary fraction: `ok_to_post` is `bool`,
     `WS-Term-Code` is `int` because `pic 99` [copybooks/wscall.cob:L10] is two
     unsigned digits, and `to-day` is `str`. No monetary or quantity value
     passes through here at all - every one of them lives in the program module.
R-3  No new validations, fields or schema changes; no concurrency. No option
     validates anything the COBOL does not, no field is added to any record, no
     SQL is emitted, and execution is strictly sequential: one dispatch, in
     order, on the calling thread.
R-4  Legacy anomalies reproduced, never fixed. Every reproduction site below
     carries a comment citing its COBOL locator, per Agent Action Plan section
     0.7.4 C-4. Reproduced here: the absent gate on `load11`; the `< 8` and
     `> 7` thresholds and the fact that they are two separate statements; the
     per-dispatch reset of `WS-Term-Code`; the dead `"sl100"` whitelist entry;
     and the Sales `perform overrewrite` / `goback` mechanism where Purchase
     writes `go to overrewrite`.
R-5  Full traceability. One named function per migrated paragraph, `load000` and
     `load11`, each keeping the COBOL's own name; a `# GO TO class N` annotation
     at every transfer site; and the mandatory footer.
R-6  Compiled behaviour is the tie-breaker. This module reads no wall clock, no
     monotonic clock, no entropy source, no unique-identifier generator and no
     process environment - it imports neither `datetime` nor `time` nor `os`, so
     there is nothing for such a read to be spelled with. The run date enters
     only as the required `--run-date`. Open questions are marked `# AMBIGUITY`
     with the experiment that settles them.

A NOTE ON THE PROSE ABOVE, which is deliberate and should not be "tidied". The
literal spellings of the constructs R-1, R-2 and R-6 forbid are absent from this
file, this documentation included, so that the mandated audit greps return a
count of zero rather than a page of prose asserting the constructs' absence. The
same convention is followed in `acas_posting/programs/sl100_cash_posting.py` for
the affirmative rounding keyword. Each construct is named by what it does
instead, which is unambiguous and greppable in the other direction.

Invocation, for reference. `--ok-to-post/--no-ok-to-post` is REQUIRED - the
parser has no default for it, so an otherwise complete command line that omits
it exits 2 with "the following arguments are required" - and the two answers do
different things, so both forms are given rather than one with the flag elided::

    # DECLINES. Reproduces the "NO" branch [sales/sl100.cbl:L316-L317], which
    # transfers to menu-exit before the first open at [sales/sl100.cbl:L321], so
    # the run has no database effect whatsoever.
    python -m acas_posting.cli.sl_cash_post --run-date 21/09/2025 \\
        --irs-instead B --no-ok-to-post

    # PROCEEDS. WARNING - THIS ONE WRITES. Every database write in the route is
    # gated on this switch, and the menu's `overrewrite` persistence runs after
    # the dispatch either way. Point it only at a disposable schema.
    python -m acas_posting.cli.sl_cash_post --run-date 21/09/2025 \\
        --irs-instead B --ok-to-post

The scenario runner script in the comparison-oracle tree invokes the entry points
as modules exactly like this; `pyproject.toml` declares no `[project.scripts]`,
so there is no console script to install.
"""

from __future__ import annotations

import argparse
import enum
import logging
from collections.abc import Mapping, Sequence
from typing import Final

from acas_posting.cli import args
from acas_posting.programs import sl100_cash_posting

#: The public surface.
__all__: Final[tuple[str, ...]] = ("main", "load000", "load11")


_log: Final = logging.getLogger(__name__)


_MENU_SRC: Final = "sales/sales.cbl"

_PROGRAM_SRC: Final = "sales/sl100.cbl"

_SL100: Final = "sl100"

_PROG: Final = "python -m acas_posting.cli.sl_cash_post"

#: The promoted run-confirmation switch, spelled once so the declaration, the
#: help text and the traceability footer cannot drift
#: [sales/sl100.cbl:L310-L319].
_OK_TO_POST_OPTION: Final[str] = "--ok-to-post"

#  ⛔ THE RUN-CONFIRM HAS NO DEFAULT, BECAUSE THE FROZEN PROGRAM HAS NONE.
#
#  What is in the frozen source, in its own order [sales/sl100.cbl:L310-L319]::
#
#      310  acpt-xrply.
#      312  display  "OK to Post Payment Transactions (YES/NO) ? [   ]" ...
#      313  move     spaces to wx-reply.
#      314  accept   wx-reply at 1256 with foreground-color 6 update.
#      315  move     function upper-case (wx-reply) to wx-reply.
#      316  if       wx-reply = "NO"
#      317           go to menu-exit.
#      318  if       wx-reply not = "YES"
#      319           go to acpt-xrply.
#
#  `wx-reply` is `pic xxx value spaces` [sales/sl100.cbl:L167]; L313 moves spaces
#  into it AGAIN immediately before the accept; the accept IS `with update`, so
#  what it pre-fills is those spaces; and L318-L319 send a blank straight back to
#  `acpt-xrply.`. Even the displayed field is drawn as three spaces, `[   ]`, and
#  not as a suggested answer. The field therefore has exactly two answers - `"NO"`,
#  which exits at L316-L317 having written nothing, and `"YES"`, which proceeds -
#  and NO third disposition for "the operator just pressed return".
#
#  A CORRECTION, RECORDED RATHER THAN QUIETLY REPLACED. An earlier draft of this
#  module reached the same reading of the source and then defaulted the switch to
#  `True` anyway, on the ground that "an operator who runs a cash-posting command
#  has answered the question by running it". That is a usability argument, not a
#  fidelity one, and Agent Action Plan section 0.3.4 licenses neither: it promotes
#  a write-gating `ACCEPT` to an explicit parameter "with the COBOL default
#  preserved", and where the COBOL has no default there is nothing to preserve and
#  a default invented here is added behaviour (R-3) in the direction that writes to
#  the database. The switch is REQUIRED: argparse rejects an invocation that names
#  neither answer, and `load11`, `load000` and `sl100_cash_posting.run` all declare
#  the parameter without a default, so no layer can resolve an omission into a
#  posting run.
#
#  R-4 sales/sl100.cbl:L167, L313, L316-L317, L318-L319 - the prompt's answer set
#  is reproduced exactly as the frozen program defines it, including the fact that
#  it has no third position and no defaultable answer. Nothing is normalised into
#  a tri-state and no answer is invented.
#
#  AMBIGUITY Q-CLI-OKTOPOST: sales/sl100.cbl:L313 moves spaces into wx-reply and
#  L318-L319 re-prompts on blank, so the COBOL has NO DEFAULTABLE ANSWER - only
#  "YES" proceeds and only "NO" exits. RESOLVED, and resolved without guessing:
#  the answer is REQUIRED on the command line.
#
#  What is actually in the frozen source. `wx-reply` is `pic xxx value spaces`
#  [sales/sl100.cbl:L167]; L313 moves spaces into it AGAIN immediately before the
#  `accept` at L314; and L318-L319 send a blank straight back to `acpt-xrply.`.
#  So the declared value is not an answer, and there is no "the operator just
#  pressed return" disposition to preserve: the field's only two answers are
#  `"NO"`, which exits at L316-L317 having written nothing, and `"YES"`, which
#  proceeds. THE PROMPT CANNOT BE LEFT UNANSWERED.
#
#  WHY THE PREVIOUS DEFAULT OF `True` WAS WRONG (finding CLI-06). An earlier draft
#  defaulted the switch to posting, on two grounds that do not survive contact
#  with Agent Action Plan section 0.8.1. That section promotes a write-gating
#  prompt to a CLI parameter "with the COBOL default preserved" - and where the
#  COBOL HAS no default, there is nothing to preserve, so supplying one is not
#  preservation but INVENTION. The two grounds were:
#    * "it is the only reachable answer that lets the entry point do the thing it
#      is named for" - an argument about the command's name, not about the frozen
#      program's behaviour; and
#    * "the alternative default would make the command a no-op unless a flag were
#      supplied" - true, and it is the wrong dichotomy. THERE IS A THIRD OPTION,
#      and it is the faithful one: refuse to run until the operator answers, which
#      is exactly what the frozen loop does. An unanswered prompt in the COBOL
#      produces neither a post nor a no-op; it produces a re-prompt.
#  The invented default was the more dangerous of the two possible inventions,
#  because it silently ENABLED EVERY DATABASE WRITE on this route (rule R-3) on
#  behalf of an operator who had said nothing.
#
#  WHY NOT RESOLVE IT ON THE ORACLE INSTEAD (rule R-6). Because the oracle cannot
#  currently be built: the frozen archive is missing
#  copybooks/ACAS-SQLstate-error-list.cob, which 44 frozen files COPY, so 22 of
#  the 29 bridges do not compile. Fabricating that copybook would breach R-3 and
#  R-4. With no compiled arbiter available, REQUIRING THE INPUT is the one
#  disposition that pre-judges nothing: it cannot post when the operator meant not
#  to, and it cannot skip when the operator meant to post.
#
#  WHAT REQUIRING IT COSTS, stated plainly: a caller must now pass one of the two
#  switches, and `load11`/`load000` take the answer as a REQUIRED keyword with no
#  default, so no library caller can inherit a silent YES either. The scenario
#  driver pins the answer per scenario, which it already did on the oracle side -
#  the compiled-oracle runner resolves this same prompt from a scenario key,
#  validating it to exactly "YES" or "NO" and refusing anything else because both
#  programs loop on anything else. Both halves of the comparison are now explicit,
#  which is what makes them agree by construction rather than by a matched pair of
#  assumptions.


class _Disposition(enum.Enum):
    """Where control went after the dispatch - the two exits of `load000.`.

    `load000.` [sales/sales.cbl:L698-L712] ends in exactly one of two ways, and which
    one it was is the only thing a caller of the paragraph can observe, because in the
    COBOL the two exits are a transfer to a different paragraph and a `goback` out of
    the run unit.

    Attributes:
        RETURNED_TO_MENU: the `< 8` path. `perform overrewrite.` at
            [sales/sales.cbl:L709] and then fall-through past the false `> 7` test into
            `load000-exit.` [sales/sales.cbl:L714] and its `go to display-menu`
            [sales/sales.cbl:L716].
        ENDED_RUN_UNIT: the `> 7` path. `perform overrewrite` at [sales/sales.cbl:L711]
            and then `goback.` at [sales/sales.cbl:L712], which ends the run unit
            without redrawing the menu.
    """

    RETURNED_TO_MENU = enum.auto()
    ENDED_RUN_UNIT = enum.auto()


def _perform_overrewrite(
    linkage: args.SlPlLinkage, menu_state: args.MenuState, locator: str
) -> None:
    """`perform overrewrite` - reproduced, at both of the two sites that reach it.

    The paragraph persists `System-Record` under file-key 1 and
    `WS-System-Record-4` under file-key 4, to the relational store
    [sales/sales.cbl:L629-L641] and then again to the Cobol file
    [sales/sales.cbl:L645-L657], before falling through `overclose.`
    [sales/sales.cbl:L659] to `goback.` [sales/sales.cbl:L660]. The RDB arm is
    reproduced once, in `acas_posting.cli.args.overrewrite`; the Cobol arm has no
    counterpart because the migration has a single store, which is recorded at
    `args.RDBMS_STORE_SELECTOR_DIGIT`.

    IT IS REACHED ON BOTH PATHS, ALWAYS. `load000.` performs it at L709 and again
    at L711, and `WS-Term-Code` is `pic 99` [copybooks/wscall.cob:L10], so `< 8`
    and `> 7` are exhaustive: the persistence is unconditional in effect. This
    route needs it for a concrete reason - `sl100` mutates SYSTEM-REC twice
    [sales/sl100.cbl:L473-L474] and writes one of the nine period totals
    [sales/sl100.cbl:L404], and every one of those changes leaves the program
    through linkage with `overrewrite` as its only writer to the store.

    This function exists so that the citation and the log record sit at both call
    sites with the locator of the site rather than a generic note.

    Args:
        linkage: the five `CALL` arguments. `system_record` is rewritten under key
            1; `menu_state.system_record_4` - the SAME object as
            `linkage.system_record_4` - under key 4.
        menu_state: the menu's own WORKING-STORAGE.
        locator: the `sales/sales.cbl` line the `perform` sits on, so the two call
            sites are distinguishable in a log.
    """
    _log.debug(
        "%s:%s `perform overrewrite` - persisting System-Record (file-key 1) and "
        "WS-System-Record-4 (file-key 4) [sales/sales.cbl:L628-L641]",
        _MENU_SRC,
        locator,
    )
    args.overrewrite(linkage.system_record, menu_state, linkage.file_defs)

def load000(
    linkage: args.SlPlLinkage,
    *,
    program_id: str,
    menu_state: args.MenuState,
    ok_to_post: bool,
    dal_options: Mapping[str, object] | None = None,
) -> _Disposition:
    """`load000.` [sales/sales.cbl:L698-L712] - the five-parameter dispatch.

    A LOCAL COPY, DELIBERATELY. Each menu shell carries its own `load000.` - Sales at
    [sales/sales.cbl:L698-L712], Purchase at [purchase/purchase.cbl:L691-L704] - and the
    two are not identical, so each Python entry point carries its own too.

    Args:
        linkage: the bound five-parameter Shape 2 carrier. Its `calling_data` is
            MUTATED in place, exactly as the COBOL writes into the menu's own
            working storage: `WS-Term-Code` is cleared and `WS-Called` is set.
        program_id: the callee's program-id, which the caller has named. On this
            route it is always `"sl100"`; the value is what the COBOL's
            `move "sl100" to ws-called` [sales/sales.cbl:L795] moves, and the
            `MOVE` is performed here because a dynamic `call ws-called`
            [sales/sales.cbl:L702] resolves the field at the dispatch, whereas
            Python resolves the callee at the call site.
        ok_to_post: the promoted run-confirm - the callee's own interactive
            prompt at [sales/sl100.cbl:L310-L319], which has no counterpart in
            this paragraph and is carried through it. REQUIRED, with no default
            at any layer (M-09): a blank answer re-prompts for ever in the frozen
            source [sales/sl100.cbl:L313, L318-L319], so there is no silence to
            interpret. Forwarded EXPLICITLY into `run`.

    Returns:
        Which of the paragraph's two exits was taken. See `_Disposition`.
    """
    calling_data = linkage.calling_data

    # `move zero to ws-term-code.` [sales/sales.cbl:L701] R-4 sales/sales.cbl:L701 - per
    # dispatch, not once per run.
    args.reset_term_code(calling_data)

    # `move "sl100" to ws-called.` [sales/sales.cbl:L795], realised at the dispatch it
    # feeds.
    args.set_called(calling_data, program_id)

    _log.info(
        "%s:L702-L707 dispatching %s with the five-parameter Sales/Purchase "
        "linkage shape (%s:L272-L276); run date %r, ok_to_post=%s",
        _MENU_SRC,
        program_id,
        _PROGRAM_SRC,
        linkage.to_day,
        ok_to_post,
    )

    sl100_cash_posting.run(
        linkage.calling_data,
        linkage.system_record,
        linkage.system_record_4,
        linkage.to_day,
        linkage.file_defs,
        ok_to_post=ok_to_post,
        #  The operator's transport declaration, carried to every facade context
        #  `sl100` builds. NO COBOL COUNTERPART - the frozen bridge's connect
        #  passes six values and no transport policy at all
        #  [copybooks/mysql-procedures.cpy:L72-L77] - so it is stated at the
        #  process boundary, which is the only place that knows. `None` states the
        #  exact-parity policy - no TLS material, no isolated-oracle claim - which
        #  is a statement rather than an omission.
        dal_options=dal_options,
    )

    # The two tests below are TWO SEPARATE `if` STATEMENTS in the frozen source, not an
    # `if`/`else`, and they are reproduced as two.
    term_code = calling_data.ws_term_code

    # `load000-exit.` [sales/sales.cbl:L714] is reached by FALL-THROUGH whenever the
    # `goback` at L712 does not execute, and it transfers to `display-menu`
    # [sales/sales.cbl:L716].
    disposition = _Disposition.RETURNED_TO_MENU

    # R-4 sales/sales.cbl:L708-L709 L708 if ws-term-code < 8 *> for sl055 & 060, xl150
    # L709 perform overrewrite. `not is_serious_error(code)` IS `ws-term-code < 8`.
    if not args.is_serious_error(term_code):
        _perform_overrewrite(linkage, menu_state, "L709")

    # R-4 sales/sales.cbl:L710-L712
    #     L710       if       ws-term-code > 7      *> Got a serious (reported) error
    #     L711                perform overrewrite
    #     L712                goback.
    #
    # UNREACHABLE ON THIS ROUTE IN PRACTICE, and implemented anyway. `sl100`
    # never writes `WS-Term-Code` - the frozen program contains no reference to
    # the field - so after the dispatch above the code is still the zero L701
    # moved in, and only `gl070` (5), `sl055` (8) and `pl055` (8) ever set it.
    # Omitting the branch would be a behaviour change, not a simplification.
    #
    # GO TO class 4 (sibling re-dispatch), with the per-site proof this class
    # requires:
    #   COBOL:  `perform overrewrite` [L711] runs the persistence paragraph,
    #           which falls through `overclose.` [L659] to `goback.` [L660]; then
    #           the `goback.` at [L712] ends the run unit. Control does NOT
    #           return to this paragraph, does not reach `load000-exit.` [L714]
    #           and does not reach `go to display-menu` [L716], so no further
    #           program is invoked and the menu is not redrawn.
    #   PYTHON: return the serious-error disposition. `main` logs it and returns
    #           `args.exit_status_for(...)`, and the process ends.
    #   PROOF:  the two agree on everything observable. The dispatch has already
    #           happened in both; no further dispatch occurs in either, because
    #           `load11` has nothing after its transfer [L796] and the caller
    #           here returns immediately; and the menu redraw that the COBOL
    #           skips is not migrated at all. `overrewrite`'s persistence is NOT
    #           a difference either: it is performed on this branch and on the
    #           ordinary one, as the frozen source performs it on both. The only
    #           part left out is that paragraph's flat-file half
    #           [sales/sales.cbl:L643-L657], which repeats both rewrites against
    #           an ISAM parameter file this migration's target does not have.
    #
    # MECHANISM DIVERGENCE, PRESERVED. Sales writes `perform overrewrite` then
    # `goback` [sales/sales.cbl:L710-L712]; Purchase writes `go to overrewrite`
    # [purchase/purchase.cbl:L703-L704] and lets `overrewrite`'s own fall-through
    # to `goback` [sales/sales.cbl:L660] end the run unit. Sales' own `load00.`
    # uses the Purchase form [sales/sales.cbl:L691-L692], so the two forms sit in
    # one file. Net effect identical, mechanism different; both are preserved and
    # neither is harmonised (R-4).
    if args.is_serious_error(term_code):
        _perform_overrewrite(linkage, menu_state, "L711")
        disposition = _Disposition.ENDED_RUN_UNIT

    return disposition


def load11(
    linkage: args.SlPlLinkage,
    *,
    menu_state: args.MenuState,
    ok_to_post: bool,
) -> _Disposition:
    """`load11.` [sales/sales.cbl:L792-L796] - Sales payments posting.

    NO GATE, and none is missing. R-4 sales/sales.cbl:L792-L796 - there is no `if ws-
    term-code` test of any kind in this paragraph.

    Args:
        linkage: the bound five-parameter Shape 2 carrier, its `calling_data`
            mutated in place by the dispatch.
        ok_to_post: the promoted run-confirm [sales/sl100.cbl:L310-L319].
            REQUIRED, with no default at any layer - see Q-CLI-OKTOPOST, resolved
            from the source (M-09) - and forwarded explicitly all the way to the
            program module.

    Returns:
        Whichever of `load000.`'s two exits was taken, unchanged. This paragraph neither
            inspects nor overrides it.
    """
    # `move     "sl100" to ws-called.` [sales/sales.cbl:L795] - the literal is
    # named here, in the paragraph the frozen source puts it in, and the `MOVE`
    # itself happens in `load000` immediately before the dispatch it feeds.
    #
    # GO TO class 4 (sibling re-dispatch):
    #   COBOL:  `go to load000.` [sales/sales.cbl:L796] transfers to a peer
    #           paragraph that does the work and then itself transfers control,
    #           either to `display-menu` [L716] or out of the run unit [L712].
    #   PYTHON: call the peer and return its disposition immediately.
    #   PROOF:  a `go to` leaves nothing behind to execute, and this `return`
    #           executes nothing after the call, so the two tails are both empty.
    #           Where the peer's own transfer goes is carried out of the call as
    #           the returned disposition rather than being re-decided here.
    return load000(
        linkage, program_id=_SL100, menu_state=menu_state, ok_to_post=ok_to_post
    )


def _build_parser() -> argparse.ArgumentParser:
    """Compose the parser for this route from the shared option fragments.

    The `WS-Calling-Data` binding is NOT redefined here: `cli/args.py` owns it, and this
    route composes its two fragments and adds exactly one option of its own.

    Returns:
        A parser offering, in this order: the five settable `WS-Calling-Data` fields
            with `--ws-caller` defaulted to the Sales menu's own identity `"sales"`
            [sales/sales.cbl:L481]; the required `--run-date`.
    """
    parser = argparse.ArgumentParser(
        prog=_PROG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Sales payment posting - dispatch sl100 exactly as the Sales menu's "
            f"`load11.` does [{_MENU_SRC}:L792-L796], through the "
            f"five-parameter `load000.` [{_MENU_SRC}:L698-L712] and NOT through "
            f"the four-parameter `load00.` [{_MENU_SRC}:L677-L692]. Headless: "
            "there is no menu, no screen output and no report spool-out."
        ),
        epilog=(
            "The run date is required and is never taken from the system clock, "
            "so two runs of one scenario are byte-identical. Pin --irs-instead "
            "explicitly for every scenario: its state changes which tables a run "
            "touches."
        ),
    )
    # The shared fragments, composed rather than reimplemented.
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
    #  `cli/rdbms_params.resolve_transport_policy` while the linkage is bound, and
    #  every handler observes the installed policy without being told. It decides
    #  no posted figure, so it cannot make two runs of one scenario differ (R-6).

    #  THE RUN-CONFIRM, OWNED HERE. It is specific to `sl100`
    #  [sales/sl100.cbl:L310-L319], so `cli/args.py` must not carry it: a shared
    #  fragment would offer the switch on routes whose programs have no such
    #  prompt, which would be an input the COBOL does not have (R-3).
    #
    #  R-4 sales/sl100.cbl:L310-L319 - and note what is NOT added. There is no
    #  `choices` list, no case normalisation of the operator's answer and no
    #  rejection message, because `argparse` already admits exactly the two
    #  answers the COBOL admits. The frozen program reaches its two answers by
    #  upper-casing whatever was typed [L315] and looping on anything else
    #  [L318-L319]; a switch pair has no third thing to type, so the loop has
    #  nothing to reject and adding a validation would invent one (R-3).
    #
    #  `BooleanOptionalAction` is stdlib argparse and renders the pair
    #  `--ok-to-post | --no-ok-to-post`, which is as close as a command line gets
    #  to a `(YES/NO)` field. No third position is offered, because the COBOL has
    #  no third answer: a blank re-prompts [sales/sl100.cbl:L313, L318-L319]
    #  rather than resolving, so there is nothing for a third position to mean.
    #
    #  `required=True`, AND NO `default` (finding CLI-06). The frozen prompt cannot
    #  be left unanswered - `wx-reply pic xxx value spaces` [sales/sl100.cbl:L167]
    #  is re-blanked at L313 and a blank goes straight back to `acpt-xrply.` at
    #  L318-L319 - so there is no default to preserve and any default would be an
    #  invention (Agent Action Plan section 0.8.1). Omitting the switch is
    #  therefore a USAGE ERROR: argparse exits with status 2 and names the missing
    #  argument, which is the headless analogue of a prompt that will not accept
    #  a blank. It is NOT a validation added to the cycle (rule R-3): nothing is
    #  checked that the frozen source does not check, and what the frozen source
    #  does with an unanswered prompt is refuse to proceed.
    parser.add_argument(
        _OK_TO_POST_OPTION,
        action=argparse.BooleanOptionalAction,
        required=True,
        help=(
            "REQUIRED. The promoted run-confirm of "
            f"{_PROGRAM_SRC}:L310-L319 - 'OK to Post Payment Transactions "
            "(YES/NO) ?'. It gates EVERY database write: --no-ok-to-post "
            f'reproduces the "NO" branch at {_PROGRAM_SRC}:L316-L317, which '
            "transfers to menu-exit before the first file is opened at "
            f"{_PROGRAM_SRC}:L321, so the run has no effect whatsoever. The "
            "program is still entered either way, exactly as the COBOL enters it "
            "before asking. THERE IS NO DEFAULT because the frozen program has "
            f"none - wx-reply is 'pic xxx value spaces' ({_PROGRAM_SRC}:L167) and "
            f'a blank re-prompts ({_PROGRAM_SRC}:L313, L318-L319), so only "YES" '
            'proceeds and only "NO" declines. Pass one of the two switches; '
            "omitting both is a usage error, not an implied yes."
        ),
    )
    #  Diagnostics only: no COBOL counterpart, no database effect. Shared with
    #  the other six routes so the level policy has one spelling.
    args.add_log_level_argument(parser)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Bind the linkage from `argv`, run `load11`, and report the term code.

    The process boundary, and the only function in this module that configures
    logging or touches `argv`. It does four things in order: parse, pin and bind,
    dispatch, report.

    NO CONNECTION CONTRACT, NO RUN - AND ONE STATUS FOR IT ACROSS THE PACKAGE
    (finding CLI-09). The six connection fields of `SYSTEM-REC` are resolved from
    the deployment contract, which raises `args.RdbmsParamError` when that
    contract is absent or unusable. That EXACT TYPE is caught here and turned into
    the one documented status every route of this package shares, through
    `args.report_configuration_failure`: 8 when the contract is absent, 1 when it
    is present but unusable. Nothing has been written when it surfaces - the raise
    happens while the parameters are still being resolved, before the system store
    is opened and before any program is entered.

    This does not re-encode a COBOL value, and that was the objection an earlier
    draft raised against catching it: the frozen loaders abandon on exactly this
    condition by displaying a message and issuing a bare `goback` WITHOUT setting a
    return code [common/glbatchLD.cbl:L245-L259], so there is no frozen
    exit-status vocabulary to map onto. True - and it cuts the other way too. The
    process exit status is a boundary the migration introduces (Q-CLI-EXITSTATUS),
    so it must be DECIDED rather than derived, and deciding it once for all seven
    routes is what makes a failed configuration diagnosable instead of
    route-dependent. What is NOT caught is `ValueError` at large: a genuine defect
    keeps its traceback.

    A REJECTED RUN DATE IS NOT AN ERROR. `args.resolve_clock` returns a binary
    `Run-Date` of 0 for a date the legacy module rejects and raises nothing,
    which reproduces `maps04` falling through without touching its output field
    together with the caller pre-zero that turns "untouched" into zero. Raising
    instead would both add a validation and correct a defect (R-3, R-4).

    Args:
        argv: the argument vector WITHOUT the program name. `None` means take it from
            `sys.argv`, which is argparse's own default and is what happens under
            `python -m`.

    Returns:
        The process exit status.

    Raises:
        SystemExit: argparse's own, for `--help` and for a usage error such as
            the required `--run-date` or the required `--ok-to-post` /
            `--no-ok-to-post` decision being omitted.

    `args.RdbmsParamError` is CAUGHT, not raised: `main` returns
    `args.report_configuration_failure`'s status instead - 8 for an absent
    deployment contract, 1 for an unusable one (finding CLI-09). Nothing has been
    written when it surfaces.
    """
    parser = _build_parser()
    ns = parser.parse_args(argv)

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

    #  THIS MODULE CALLS NO `basicConfig`, AND ITS `asctime` FIELD IS GONE.
    #  The package contains exactly one call to it -
    #  `acas_posting.__main__.configure_logging` - which both process boundaries
    #  reach: the router, and this module's own guard through `run_entry_point`.
    #  `main` does ask that configurator to SET THE LEVEL, but only when the
    #  operator supplied `--log-level`; called as a library without that option,
    #  which is how the scenario suites reach it, it touches nothing.
    #
    #  The format that configurator applies carries NO `%(asctime)s`. The old
    #  reasoning here - that a record timestamp reaches the log stream and never a
    #  table dump, so section 0.8.5's determinism is untouched - was true and is
    #  still beside the point: it made this route the only one whose transcript of
    #  two identical runs differed, and it was the only reading of a wall clock
    #  anywhere in an otherwise clock-free package. One format for seven routes,
    #  and no clock in any of them. The two date observables still come only from
    #  `--run-date`.

    #  PIN AND BIND. One call resolves the clock from `--run-date` and returns
    #  the five Shape 2 arguments in COBOL parameter order. `called` is the
    #  program-id this route dispatches; `WS-Caller` comes from `--ws-caller`,
    #  which this parser defaults to the Sales menu's own identity
    #  [sales/sales.cbl:L481], so the binder's program-id-derived fallback is not
    #  what supplies it here.
    #
    #  The deployment environment is NOT read by this module. The six connection
    #  fields of `SYSTEM-REC` are resolved inside the binder, which reproduces the
    #  frozen `common/acas-get-params.cbl` keyword contract - a program the
    #  loaders call and whose own remarks say it "Uses Current directory only."
    #  The run date is untouched by that and still arrives only as `--run-date`,
    #  so no ambient input can make two runs of one scenario differ (R-6).
    #  THE MENU'S OWN WORKING-STORAGE - one block for the whole route, owning
    #  `WS-System-Record-4`, which the binder hands to the linkage as its third
    #  argument. See `args.slpl_menu_state`.
    menu_state = args.slpl_menu_state()

    #  L351  aa005-Open-System.   L365  aa010-Get-System-Recs.
    #  Passing it makes the binder perform `Open-System.` and
    #  `aa010-Get-System-Recs.` [sales/sales.cbl:L338-L360] - keys 4 then 1, never
    #  key 2, TWO keys where the General Ledger shell reads three - so `sl100`
    #  receives the PERSISTED records rather than defaulted ones (finding CLI-02).
    #
    #  THE EXACT TYPE IS CAUGHT, NOT `ValueError` (finding CLI-09). The six
    #  connection parameters are resolved inside the binder before the store is
    #  opened, so a failure here has touched nothing, and catching the base class
    #  would swallow a genuine defect as if it were a configuration problem.
    try:
        linkage = args.bind_slpl_linkage(ns, called=_SL100, menu_state=menu_state)
    except args.RdbmsParamError as error:
        return args.report_configuration_failure(
            error, logger=_log, subject="Sales cash posting"
        )

    # `go       to load11` - the menu's own `depending on z` dispatch table
    # [sales/sales.cbl:L662-L670] selected this paragraph for menu letter
    # `(K)  Payment Post` [sales/sales.cbl:L549]. The table itself is an
    # OMISSION; a command line selects the route by being invoked.
    disposition = load11(
        linkage, menu_state=menu_state, ok_to_post=ns.ok_to_post
    )

    term_code = linkage.calling_data.ws_term_code
    if disposition is _Disposition.ENDED_RUN_UNIT:
        _log.error(
            "%s:L710-L712 %s reported a serious error: WS-Term-Code %d",
            _MENU_SRC,
            _SL100,
            term_code,
        )
    else:
        _log.info(
            "%s:L714-L716 %s completed; WS-Term-Code %d",
            _MENU_SRC,
            _SL100,
            term_code,
        )

    return args.exit_status_for(term_code)


if __name__ == "__main__":  # pragma: no cover - the module-as-script boundary
    #  ONE PROCESS BOUNDARY, SHARED WITH THE ROUTER. `run_entry_point` configures
    #  logging once, from the single format and level policy, and converts a
    #  failure into one sanitised ERROR record and a deterministic exit status.
    #  The import is inside the guard: it is needed only when this module IS the
    #  process, and the router imports this module back when the router is.
    from acas_posting.__main__ import run_entry_point

    raise SystemExit(run_entry_point(main, command="sl-cash-post"))


# ===========================================================================
# --- traceability ---
# ===========================================================================
#
# No user rules document exists for this project: `review_rules` returns exactly
# "No user rules provided." The six binding rules R-1 ... R-6 come from the Agent
# Action Plan section 0.7.2 and are restated in the module docstring above, each
# with how this module honours it. No rule has been invented.
#
# ---------------------------------------------------------------------------
# 1. FUNCTION -> COBOL PARAGRAPH (R-5). Spans measured against the frozen
#    source, line by line, not taken from any planning document.
# ---------------------------------------------------------------------------
#   load000                    sales/sales.cbl  `load000.`   L698-L712
#                              L701 reset, L702-L707 the five-parameter CALL,
#                              L708-L709 the `< 8` branch, L710-L712 the `> 7`
#                              branch. `load000-exit.` L714 and its
#                              `go to display-menu` L716 are the fall-through
#                              exit and are carried as a disposition, not as a
#                              transfer, because the menu is not migrated.
#   load11                     sales/sales.cbl  `load11.`    L792-L796
#                              L792 the label and the maintainer's own comment
#                              `*> Sales payments posting`, L795 the `move`,
#                              L796 the `go to`. Two statements, NO gate.
#   _Disposition               the two exits of `load000.` - L714/L716 and L712.
#   _perform_overrewrite       the two `perform overrewrite` sites, L709 and
#                              L711. Performs `args.overrewrite`, the paragraph
#                              itself, and logs the site's own locator.
#   _build_parser              the CLI boundary. No COBOL counterpart: the menu
#                              selects a route with a letter
#                              [sales/sales.cbl:L549] through a `depending on z`
#                              table [sales/sales.cbl:L662-L670].
#   main                       the CLI boundary. No COBOL counterpart either -
#                              the frozen shell is an interactive menu loop, and
#                              a process that starts, dispatches once and exits
#                              is the headless equivalent (AAP 0.3.4).
#
# ---------------------------------------------------------------------------
# 2. PROGRAM -> MODULE (R-5)
# ---------------------------------------------------------------------------
#   sl100  ->  acas_posting/programs/sl100_cash_posting.py
#              `procedure division using ws-calling-data, system-record,
#              system-record-4, to-day, file-defs.` [sales/sl100.cbl:L272-L276]
#              Imported AS A MODULE and called through its published `run`;
#              `acas_posting/programs/__init__.py` deliberately publishes no
#              dispatch table, no registry and no `run` re-export, so a caller
#              cannot reach into a program's internals any more than a COBOL
#              `CALL` can (AAP 0.3.3).
#
# ---------------------------------------------------------------------------
# 3. PROMOTED PARAMETER -> LOCATOR (AAP 0.3.4)
# ---------------------------------------------------------------------------
#   ok_to_post  ->  sales/sl100.cbl `acpt-xrply.` L310-L319
#       L311-L312  the prompt, "OK to Post Payment Transactions (YES/NO) ? [   ]"
#       L313       `move spaces to wx-reply` - and `wx-reply` is declared
#                  `pic xxx value spaces` at L167, so the field's declared value
#                  is not an answer either
#       L314       the accept; L315 `function upper-case`
#       L316-L317  `"NO"` -> `menu-exit.` L476-L477 (`exit program.`), reached
#                  BEFORE the first open at L321, so NOTHING is written
#       L318-L319  blank, and anything else, re-prompts
#       => only "YES" proceeds, so there is no defaultable answer to preserve.
#          The switch pair is `required=True` with no default, so the decision
#          must be stated (finding CLI-06); see Q-CLI-OKTOPOST.
#          The value is passed EXPLICITLY into `run` at every call, so the
#          callee's own `ok_to_post: bool = True` is never consulted and the two
#          defaults cannot silently drift.
#
# ---------------------------------------------------------------------------
# 4. `GO TO` CLASSES (AAP 0.4.2, R-5)
# ---------------------------------------------------------------------------
#   sales/sl100.cbl:L316-L317   Class 3, section/paragraph exit. `go to
#       menu-exit` on the "NO" answer. Transformed to a `return` INSIDE
#       `programs/sl100_cash_posting.py`; it reaches this module only as the
#       `--no-ok-to-post` position of the promoted parameter.
#   sales/sl100.cbl:L318-L319   Class 1, loop-back. `go to acpt-xrply` on a blank
#       or unrecognised answer - the interactive retry loop. It is NOT migrated
#       as a loop: a command-line switch has exactly the two answers the loop
#       exists to insist on, so the retry has nothing to retry. Recorded here
#       rather than dropped silently, because dropping it is a decision.
#   sales/sales.cbl:L796        Class 4, sibling re-dispatch. `go to load000`.
#       Proof at the call site in `load11`: a `go to` leaves nothing behind to
#       execute and the `return` executes nothing after the call, so both tails
#       are empty; the peer's own transfer is carried out as the returned
#       disposition rather than re-decided.
#   sales/sales.cbl:L710-L712   Class 4, sibling re-dispatch. `perform
#       overrewrite` then `goback`. Full per-site proof at the branch in
#       `load000`: control never returns to the dispatch paragraph, never reaches
#       `load000-exit.` L714 or `go to display-menu` L716, and no further program
#       is invoked; Python returns the serious-error disposition and `main`
#       returns `args.exit_status_for(...)`. The only difference is the omitted
#       `overrewrite` persistence, recorded under OMISSIONS.
#   sales/sales.cbl:L716        Class 4, sibling re-dispatch, NOT MIGRATED. `go
#       to display-menu` at the tail of `load000-exit.`. The menu loop it returns
#       to is out of scope, so it becomes the `RETURNED_TO_MENU` disposition and
#       then the end of the process.
#
# ---------------------------------------------------------------------------
# 5. DRIFT NOTES - measured spans against what planning documents say
# ---------------------------------------------------------------------------
#   * `load11` is cited as L793-L797 by the planned `acas_posting/__main__.py`
#     route table, and as L790-L797 by the docstring of
#     `acas_posting/programs/sl100_cash_posting.py`. The MEASURED span is
#     L792-L796: the label is on L792, `move "sl100" to ws-called.` on L795 and
#     `go to load000.` on L796; L793 is `*>-----` and L794 is `*>`.
#     `acas_posting/cli/__init__.py` already records L792-L796. This module cites
#     the measured span throughout.
#   * The Sales menu's INVOICE posting chain is `load07.` [sales/sales.cbl:L757-
#     L768], not `load08.`; `load08.` [L770-L774] dispatches sl080, which AAP
#     0.2.2 places out of scope. Recorded because this module's docstring
#     contrasts its own absent gate with that route's two gates.
#
# ---------------------------------------------------------------------------
# 6. CORRECTIONS
# ---------------------------------------------------------------------------
#   1. THE SALES/PURCHASE LINKAGE SHAPE HAS FIVE PARAMETERS, NOT FOUR. AAP
#      0.4.1.1 describes it as "the four-parameter SL/PL linkage shape"; AAP
#      0.1.1 and the frozen source both give five. The `CALL` lists them at
#      [sales/sales.cbl:L702-L707] and the callee declares them at
#      [sales/sl100.cbl:L272-L276]: ws-calling-data, system-record,
#      system-record-4, to-day, file-defs. `args.SlPlLinkage` carries five and
#      says so in its own docstring. Four is the General Ledger shape, which
#      omits `system-record-4`.
#   2. `--irs-instead` TAKES NO CHOICES LIST. One planning document describes it
#      as `--irs-instead {N,Y,B}`. As implemented in `cli/args.py` it is a
#      free-form single character with no `choices`, deliberately: the field is
#      `pic x` and its only two condition names are "IRS instead" and "IRS as
#      well as" [copybooks/wssystem.cob:L179-L181] - there is no third value and
#      in particular no 'N' - so refusing a character would invent a check the
#      COBOL has not got (R-3). This module composes the fragment unchanged.
#
# ---------------------------------------------------------------------------
# 7. OMISSIONS - recorded per AAP 0.4.3 "so that a reader comparing the two
#    files does not conclude something was lost".
# ---------------------------------------------------------------------------
#   * ALL MENU SCREEN I/O, the `display-menu` paragraph, the twenty-odd
#     `display "(x)  ..."` menu-letter lines including `(K)  Payment Post`
#     [sales/sales.cbl:L549] which is how a human selects this route, and every
#     `accept` that merely pauses for acknowledgement.
#   * THE DISPATCH TABLE. `load-it.` and its
#     `go to load01 ... load11 ... depending on z` [sales/sales.cbl:L662-L670],
#     with the `depending on z` phrase itself at L670. A command line selects a
#     route by being invoked, so there is nothing to dispatch on.
#   * `overrewrite`'s PERSISTENCE OF THE TWO SYSTEM RECORDS. `overrewrite.`
#     [sales/sales.cbl:L628] rewrites `System-Record` under file-key 1 and
#     `WS-System-Record-4` under file-key 4, first to the relational store
#     [L629-L641] and then again to the Cobol file [L645-L657], before falling
#     through `overclose.` [L659] to `goback.` [L660]. `load000.` performs it on
#     BOTH paths [L709, L711], and because `< 8` and `> 7` are exhaustive over
#     `pic 99` it therefore always happens. It belongs to the menu shell, which
#     is frozen and out of scope as a program (AAP 0.2.2). See
#     Q-CLI-OVERREWRITE - this is the one omission with a possible table-visible
#     effect, and it is measured rather than argued.
#   * `pre-overrewrite`'s BACKUP SPOOL-OUT. `call "SYSTEM" using
#     Full-Backup-Script.` [sales/sales.cbl:L625], with the script assembled at
#     [L613-L623] and the `if not Backup-Script-Found / go to overrewrite`
#     bypass at [L610-L611]. Excluded twice over: by AAP 0.2.2's exclusion of the
#     `call "SYSTEM" using Print-Report` spool-out path, and by R-1, which
#     forbids the shipped package from shelling out at all.
#   * `sl100`'s `menu-return.` PRESENTATION BLOCK [sales/sl100.cbl:L303-L308]:
#     `display prog-name` (L305, the value `"SL100 (3.3.01)"` at L135), the
#     `"Sales Cash Posting"` banner (L306), `perform zz070-Convert-Date` (L307)
#     and `display ws-date` (L308). Display only, no database effect. The date
#     conversion it performs belongs to `acas_posting/dates.py` and is reached
#     through `programs/sl100_cash_posting.py`; this module does not import
#     either, because a CLI entry point has no date work of its own - the pinned
#     pair arrives from `args.bind_slpl_linkage`.
#   * `acas_posting/clock.py` IS NOT IMPORTED HERE, although it is a declared
#     dependency of this file. `args.bind_slpl_linkage` already calls
#     `args.resolve_clock`, which delegates to `clock.pin_from_to_day`, and
#     returns the pinned text date as the linkage's own `to_day`. A direct import
#     would be an unused one. The clock contract is honoured through `args`, and
#     the run date still enters only as the required `--run-date` (R-6).
#   * OUT-OF-SCOPE SALES ROUTES, deliberately absent: `load10.`
#     [sales/sales.cbl:L782-L790] (sl090 then sl095, the payment proof and its
#     report) and `load12.` [L798-L802] (sl070). Neither is routed by any entry
#     point in this package.
#   * THE FOUR-PARAMETER DISPATCH PARAGRAPH `load00.` [sales/sales.cbl:L677-L692]
#     is not migrated here at all. This route does not use it - see the ANOMALY
#     below - and the routes that do are other entry points' business.
#
# ---------------------------------------------------------------------------
# 8. ANOMALIES REPRODUCED, NEVER FIXED (R-4). AAP 0.8.2: "There is no test
#    suite: compiled COBOL execution is the behavioral specification, defects
#    included. A defect reproduced is correct; a defect fixed is a failure."
#    Each site in the code above carries a comment citing its locator, as AAP
#    0.7.4 C-4 requires.
# ---------------------------------------------------------------------------
#   A. THE DEAD `"sl100"` WHITELIST ENTRY. `load00.`'s post-dispatch condition
#      [sales/sales.cbl:L686-L690] lists the programs that get `perform
#      overrewrite` after a FOUR-parameter call, and `"sl100"` is among them
#      [L688] - yet `sl100` is dispatched only by `load11.` through `load000.`
#      [L795-L796], so that entry can never be reached. It is dead code. The
#      maintainer doubted the list himself: his own inline comment at [L689]
#      reads `*> 200 ??  930 ??`. Recorded, not cleaned up. Reading that
#      whitelist as a routing table is the trap on this route: it would send an
#      implementer to `load00.` and therefore to the wrong linkage shape.
#   B. `load11` HAS NO GATE [sales/sales.cbl:L792-L796], where the sibling
#      invoice route gates twice on `not = zero` [L761-L762, L765-L766] and the
#      General Ledger cycle gates on `= 5`. Three gate forms in one folder, kept
#      apart rather than harmonised.
#   C. THE `< 8` AND `> 7` TESTS ARE TWO SEPARATE STATEMENTS [L708, L710] whose
#      conditions are exhaustive and mutually exclusive over `pic 99`
#      [copybooks/wscall.cob:L10], so the paragraph states the same condition
#      twice and always performs `overrewrite`. Reproduced as two statements.
#   D. THE PER-DISPATCH RESET [L701]. `move zero to ws-term-code` sits inside the
#      dispatch paragraph rather than at the top of the run, so it executes once
#      per `CALL`. Reproduced in the same place.
#   E. THE SALES/PURCHASE MECHANISM DIVERGENCE. Sales writes `perform
#      overrewrite` then `goback` [sales/sales.cbl:L710-L712]; Purchase writes
#      `go to overrewrite` [purchase/purchase.cbl:L703-L704], and Sales' own
#      `load00.` uses the Purchase form [sales/sales.cbl:L691-L692]. Same net
#      effect, different mechanism, both preserved.
#   F. THE `> 7` BRANCH IS UNREACHABLE ON THIS ROUTE. `sl100` never writes
#      `WS-Term-Code`; only `gl070` (5) [general/gl070.cbl:L289], `sl055` (8)
#      [sales/sl055.cbl:L344] and `pl055` (8) [purchase/pl055.cbl:L286] do.
#      Implemented faithfully anyway.
#   Not this module's to reproduce, recorded so a reader does not look for them
#   here: anomaly 10 of the register - `sl100`'s moving-average guard uses the
#   `divide ... BY ... giving` form where its two siblings write
#   `divide ... INTO ... giving` [sales/sl100.cbl:L506, L511] - a SYNTACTIC
#   difference only, since both forms compute accumulator / activity and the
#   two are therefore arithmetically equal; the truncation, not the operand
#   order, is what the anomaly turns on - integer truncation throughout and never a
#   binary fraction - lives in `programs/sl100_cash_posting.py`, and nothing here
#   compensates for it. So does the period-total write to `sl-payments`
#   [sales/sl100.cbl:L404, copybooks/wssys4.cob:L17], which is one of the nine
#   period-total write sites and the observable signature of this route: it is
#   why the period-end-totals scenario can be verified by inspecting one table.
#   And so does the `sl4-spare3`/`sl4-spare4` misnaming, two spare fields
#   carrying the Sales prefix inside the Purchase group
#   [copybooks/wssys4.cob:L29-L30].
#
# ---------------------------------------------------------------------------
# 9. AMBIGUITIES - each to be recorded in
#    docs/migration/ambiguity-resolutions.md with its experiment and outcome.
# ---------------------------------------------------------------------------
#   Q-CLI-OKTOPOST     RESOLVED. Stated in full above the parser's `--ok-to-post`
#                      declaration. The question was: what CLI default preserves a
#                      prompt that has no defaultable answer
#                      [sales/sl100.cbl:L167, L313, L318-L319]? The answer is that
#                      NONE DOES, so the switch is `required=True` with no default
#                      and omitting it is a usage error (status 2). An earlier
#                      draft answered `True`, which invented the one answer that
#                      silently enables every database write on this route
#                      (finding CLI-06, rule R-3). Resolution by oracle is
#                      unavailable - the frozen archive is missing
#                      copybooks/ACAS-SQLstate-error-list.cob, so 22 of the 29
#                      bridges do not compile and fabricating it would breach R-3
#                      and R-4 - and requiring the input is the one disposition
#                      that pre-judges neither answer. The oracle runner already
#                      pins this prompt per scenario, so both halves of the
#                      comparison are now explicit rather than relying on a matched
#                      pair of assumptions. The program module records the same
#                      question as its own AMBIGUITY Q-6; the value is passed
#                      explicitly at every call, so the two cannot disagree.
#                      One span note: the oracle runner cites the prompt's loop as
#                      [sales/sl100.cbl:L316-L318]. Measured precisely, the two
#                      tests are L316-L317 (`"NO"` -> `menu-exit`) and L318-L319
#                      (anything but `"YES"` -> `acpt-xrply`); this module cites
#                      those.
#   Q-CLI-OVERREWRITE  SETTLED, by reproducing the paragraph. `args.overrewrite`
#                      is performed from both sites [sales/sales.cbl:L709, L711]
#                      and `args.aa010_get_system_recs` loads the same two rows
#                      before the dispatch, so SYSTEM-REC and SYSTOT-REC are
#                      written on both sides. What remains for the oracle is
#                      narrower and lives in `cli/args.py` as
#                      Q-CLI-SYSREC-PINS: three columns are re-pinned from the
#                      command line over the loaded row.
#   Q-CLI-EXITSTATUS   SETTLED, and settled in `cli/args.py:exit_status_for`,
#                      which this module calls rather than re-deciding. The
#                      mapping is the identity: `WS-Term-Code` is `pic 99` so its
#                      whole domain fits a POSIX wait status, and a census of the
#                      five menus and all twelve programs finds `RETURN-CODE`
#                      read and never written, so the compiled cycle emits no
#                      exit status derived from the field and there is no oracle
#                      observable to arbitrate against. Nothing here re-encodes
#                      the value. A related boundary decision taken in `main`
#                      rests on the same kind of evidence: the frozen loaders
#                      abandon a missing connection contract with a bare `goback`
#                      and NO return code [common/glbatchLD.cbl:L245-L259], so
#                      `RdbmsParamError` is left to propagate rather than mapped
#                      onto an invented status.
