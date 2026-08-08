"""General Ledger end of cycle - `gl080`, dispatched by `load09.` with no gate.

The batch entry point for `general/general.cbl` `load09.` L817-L821, which is two
statements: name gl080 and dispatch it. There is no term-code test on this route,
and the absence is reproduced - the aborts live in the callee, which is where the
frozen source puts them.

gl080 carries phases 3 and 5, transaction deletion and end-of-period processing
[general/gl080.cbl:L319], [general/gl080.cbl:L336]. THE PHASE NUMBERING IS NOT
THE EXECUTION ORDER: this route's Phase-3 deletion runs AFTER `gl072`'s "Phase -
4.  Transaction Update" [general/gl072.cbl:L274], and Phase 1 and Phase 4 each
occur twice across the family under two different meanings.
`acas_posting.programs.gl080_end_of_cycle` carries the five-label analysis;
nothing here infers an ordering from a phase number (Agent Action Plan §0.6.4).

    L711  load00.
    L714       move     zero to ws-term-code.
    L715       call     ws-called using ws-calling-data
    L716                                system-record
    L717                                to-day
    L718                                file-defs
    L719       end-call
    L720       if       ws-term-code > 7
    L721                go to overrewrite.
    L723  load00-exit.
    L725       go       to display-menu.

The callee's own linkage list is the same four parameters in the same order
[general/gl080.cbl:L269-L272] - the GENERAL LEDGER FOUR-PARAMETER SHAPE, one of
the three in this migration. Shape 1 is built by `acas_posting.cli.args`, which
owns the binding, so this module defines no linkage of its own.

`load09` HAS NO GATE, AND THAT IS DELIBERATE
============================================
Its sibling `load08.` [general/general.cbl:L805-L815] tests the term code between
phases - `if ws-term-code = 5 / go to display-menu`
[general/general.cbl:L810-L811]. `load09` does not, and it has no phase to gate:
it dispatches one program and the route is over. There is nothing to gate either,
because `gl080` NEVER SETS A TERM CODE; it ends with a bare `goback`
[general/gl080.cbl:L366]. Only `gl070` [general/gl070.cbl:L289], `sl055`
[sales/sl055.cbl:L344] and `pl055` [purchase/pl055.cbl:L286] raise one at all.
Adding a gate "for symmetry" is the failure mode rule R-4 exists to prevent.

`go to load00`, NOT `perform load00` - SO NOTHING MAY FOLLOW THE DISPATCH
`perform load00` RETURNS, which is why `load08` can put a gate on the following
line. `go to load00` [general/general.cbl:L821] does not: control falls out
through `load00-exit.` [general/general.cbl:L723] to `display-menu`
[general/general.cbl:L725] and never comes back. So `load09` below ends AT its
dispatch and no statement is placed after it. This route reaches `load00.` only,
never the five-parameter `load000.` [general/general.cbl:L727-L737] that serves
the out-of-scope gl020 and gl050.

THE THREE PROMOTED PARAMETERS, AND THEIR VERIFIED DEFAULTS
==========================================================
Agent Action Plan §0.3.4: accept prompts that gate a database write become CLI
parameters with the COBOL default preserved. `gl080` is the only in-scope program
with three. Every default below was read off the frozen source, and every one is
the answer that lets the program PROCEED.

`--run-confirmed` / `--no-run-confirmed`   [general/gl080.cbl:L295-L302]
    The backup pre-flight. ONLY Escape or "A"/"a" aborts (L300-L302); every other
    reply proceeds, including the SPACE moved in at L298 that Return yields, and
    there is no retry loop. `--no-run-confirmed` reproduces the `goback`: the
    program returns before a single write of any kind.

`--disk-change-option`   [general/gl080.cbl:L542-L557]
    THE ONLY VALUE THAT PROCEEDS IS 0. `9` transfers to `main-exit` (L546-L547)
    and anything else re-prompts for ever (L548-L549) - the program's own GL084
    message says so at [general/gl080.cbl:L252]. So the default is 0 AND NOT 9,
    which is the easy thing to get backwards. A 9 is read twice afterwards, at
    [general/gl080.cbl:L408-L409] to skip the archiving walk and at
    [general/gl080.cbl:L324-L326] to skip end-of-period processing, so one
    keystroke suppresses every batch stamp, every posting delete, the ledger
    quarter rollover and the cycle increment.

`--archive-path-override`   [general/gl080.cbl:L553-L557]
    `accept file-2 ... with update` L555 presents the field ALREADY holding the
    path computed at L537, so the COBOL default is NO OVERRIDE. Its only guard is
    that a leading space re-prompts (L556-L557); nothing else is examined, here
    either (rule R-3). The archive is a flat file, so this has no table effect.

The maintainer's note between the two prompts [general/gl080.cbl:L551] -
"Hopefully can remove these after testing", echoing the header at
[general/gl080.cbl:L93] - marks them as acknowledged legacy scaffolding. They are
reproduced anyway, because their answers change table state.

THE DISPATCH IS UNCONDITIONAL - THE ABORTS LIVE IN THE CALLEE, NOT HERE
======================================================================
An aborting answer is PASSED to `gl080`, which acts on it where the frozen source
does. That is a correctness requirement, with two independent proofs:

  * `perform zz070-convert-date` runs at [general/gl080.cbl:L285] BEFORE the
    pre-flight, and MUTATES the linkage system record
    [general/gl080.cbl:L729-L730]. Short-circuiting would skip a mutation the
    compiled program performs.
  * the disk-change option is read ONLY on the archiving path, performed from
    `gl080b` [general/gl080.cbl:L406]; the deletion path `gl080c`
    [general/gl080.cbl:L562] never reaches it. So `--disk-change-option 9` must
    not suppress the run - in the non-archiving configuration it has no effect at
    all, and skipping the dispatch would wrongly cancel transaction deletion.

`load09` and `load00` below therefore branch on no promoted parameter.

WHAT IS NOT HERE
The acknowledgement pauses [general/gl080.cbl:L311-L312],
[general/gl080.cbl:L648], [general/gl080.cbl:L696] held a terminal and nothing
else. The GL084-GL087 literals [general/gl080.cbl:L252-L255] survive as the three
parameters above, not as displays. The menu's `overrewrite` persistence
[general/general.cbl:L656] IS reproduced, by `args.overrewrite`; its COBOL-file
arm [general/general.cbl:L674-L691] is not, because the migration has one store,
and the backup spool-out [general/general.cbl:L650] stays excluded by §0.2.2 and
rule R-1. The footer lists every omission.

RULE COMPLIANCE, FILE-SPECIFIC FACTS ONLY (the six rules are Agent Action Plan
§0.7.2; README-python-migration.md states them once)
R-1 No process is spawned, no foreign library loaded, nothing imported from
    harness/; no option selects or compares against the oracle.
R-2 `WS-Term-Code` is an `int` (`pic 99` [copybooks/wscall.cob:L10]), the
    disk-change option an `int` (`77 a pic 99` [general/gl080.cbl:L183]); the
    path and `to-day` are `str`. No binary-radix numeric anywhere.
R-3 The disk-change option is NOT restricted to 0 and 9, because the COBOL
    re-prompts on a third value rather than rejecting it; the archive path is not
    examined, created or resolved; execution is strictly sequential.
R-4 Reproduced here: `load09` having no gate, 0 as the only proceeding
    disk-change value, the pre-flight aborting only on Escape/"A"/"a", and the
    leading-space test as the archive path's sole guard.
R-5 The two functions are named after the two paragraphs; the footer records the
    mapping and the `GO TO` class of every transfer site.
R-6 The run date arrives only as `--run-date`, pinned through `args.resolve_clock`
    into `acas_posting/clock.py`. All twelve in-scope programs contain zero clock
    reads; the reads sit in the out-of-scope menu layer
    [copybooks/Proc-ACAS-Mapser-RDB.cob:L72-L80], [general/general.cbl:L371].

NO IMPORT-TIME SIDE EFFECTS
Importing this module binds names and nothing else - no parser, no logging
configuration, no file or connection, nothing read from its surroundings - a hard
requirement, because the scenario suites import this package.

INVOCATION
    Both confirmation options DEFAULT TO PROCEEDING, exactly as the frozen program
    does, so a command line that names neither is a DESTRUCTIVE one. The safe form
    is given first::

        # DECLINES. Reproduces Escape or A at the pre-flight
        # [general/gl080.cbl:L295-L302]: gl080 returns BEFORE ANY WRITE and the
        # database is left untouched.
        python -m acas_posting.cli.gl_end_of_cycle --run-date 21/09/2025 \
            --no-run-confirmed

        # PROCEEDS. WARNING - THIS ONE WRITES, AND MOST OF IT IS IRREVERSIBLE:
        # postings deleted or archived, batches stamped, and at a period boundary
        # the nominal-ledger quarters rolled and the cycle advanced. Point it only
        # at a disposable schema.
        python -m acas_posting.cli.gl_end_of_cycle --run-date 21/09/2025 \
            --run-confirmed --disk-change-option 0

No console script is declared: `pyproject.toml` has no `[project.scripts]` table,
so the module-execution form above is the documented route and the one
`harness/run_python_scenario.sh` uses.
"""

from __future__ import annotations

import argparse
import logging
from collections.abc import Mapping, Sequence
from typing import Final

from acas_posting.cli import args
from acas_posting.programs import gl080_end_of_cycle as gl080

__all__: Final[tuple[str, ...]] = ("main", "load00", "load09")

# Diagnostic displays with no database effect become log records at a severity matching
# the original's intent (Agent Action Plan section 0.3.4).
_LOG: Final[logging.Logger] = logging.getLogger(__name__)


# [general/general.cbl:L820] move "gl080" to ws-called. The literal is the whole of
# `load09`'s first statement.
_GL080_PROGRAM_ID: Final[str] = "gl080"


# Named here so that the argparse defaults, the log text and the traceability footer all
# quote ONE value per parameter.

# [general/gl080.cbl:L298-L302] ANOMALY-CLASS FIDELITY (rule R-4).
_RUN_CONFIRMED_DEFAULT: Final[bool] = True

#  [general/gl080.cbl:L542-L549]  THE TWO VALUES `accept-option.` CAN BE LEFT ON,
#  and there are exactly two. `if a = 9 go to main-exit` [:L546-L547] is a class-3
#  section exit that aborts the run; falling through on zero proceeds; and `if a
#  not = zero go to accept-option` [:L548-L549] is a class-1 loop-back that sends
#  EVERY OTHER VALUE to the prompt again. So the domain of the promoted parameter
#  is {0, 9} and nothing else - which is what `choices` on the option enforces.
_DISK_CHANGE_OPTION_PROCEED: Final[int] = 0
_DISK_CHANGE_OPTION_ABORT: Final[int] = 9

#  ZERO, NOT NINE (rule R-4). The single value that lets control leave the
#  paragraph and the run proceed is 0; getting this backwards would silently
#  disable the archiving walk and the whole of end-of-period processing.
_DISK_CHANGE_OPTION_DEFAULT: Final[int] = _DISK_CHANGE_OPTION_PROCEED

_ARCHIVE_PATH_OVERRIDE_DEFAULT: Final[str | None] = None


#  DIAGNOSTIC VERBOSITY IS NOT DECLARED HERE
#  `--log-level` is `args.add_log_level_argument`, composed by all seven entry
#  points and taking its choices and its default from `acas_posting.__main__` -
#  the module that owns the single `basicConfig` that consumes them. Declaring it
#  privately here would put it on exactly ONE of the seven, so the flag would work
#  for this route and be a usage error for the other six - which matters because
#  `harness/run_python_scenario.sh` invokes the entry points directly rather than
#  through the router. This route's behaviour is unaffected:
#  the same option, the same five choices, the same INFO default, applied through
#  the same one configurator at the same point in `main`.

#  DETERMINISM EXTENDS TO THE LOG STREAM (rule R-6), and the format that
#  delivers it is now declared ONCE, in `acas_posting.__main__.LOG_FORMAT`: no
#  timestamp, no process id, no thread name, so two runs of one scenario produce
#  byte-identical log text as well as byte-identical table dumps. That is
#  stricter than section 0.8.5 requires - it speaks of dumps - and it costs
#  nothing. Seven modules each declaring their own format produced three
#  different ones, one of which carried `asctime`; there is now one format, one
#  `basicConfig`, and one level policy, all owned by the router.


def _build_parser() -> argparse.ArgumentParser:
    """Build this route's parser: the shared Shape 1 options plus `gl080`'s three.

    The shared options are NOT redefined here. `acas_posting.cli.args` owns the
    binding of `01 WS-Calling-Data` [copybooks/wscall.cob:L6-L14], the required
    `--run-date` and the two settable `SYSTEM-REC` fields, and every entry point
    of this package composes those fragments rather than restating them, so the
    binding has one spelling. That is true of `--log-level` as well, which every
    route now composes from `args.add_log_level_argument`. What this function
    adds ITSELF is exactly the three options specific to `gl080` - a promoted
    prompt of one program has no business in a shared fragment.

    Returns:
        A parser that has never been parsed. Built on demand and never at import, so
            importing this module does no work.
    """
    parser = argparse.ArgumentParser(
        prog="python -m acas_posting.cli.gl_end_of_cycle",
        description=(
            "General Ledger End Of Cycle Processing - the migration of "
            "general/general.cbl `load09.` (L817-L821), which dispatches gl080 "
            "through the shared four-parameter block `load00.` (L711-L721). "
            "Unlike the posting-cycle route `load08.` this route has NO term-code "
            "gate, because gl080 never sets a term code. Deletes or archives the "
            "cycle's postings, stamps its batches, and at a period boundary rolls "
            "the nominal-ledger quarters and advances the cycle."
        ),
        epilog=(
            "The run date is REQUIRED and is never taken from the system clock, "
            "so that two runs of one scenario are byte-identical. Connection "
            "parameters are not command-line options: they reach SYSTEM-REC from "
            "the deployment contract, exactly as the frozen "
            "common/acas-get-params.cbl reads them."
        ),
    )

    args.add_calling_data_arguments(
        parser, default_caller=args.WS_CALLER_GENERAL
    )
    args.add_gl_linkage_arguments(parser)
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


    #  [general/gl080.cbl:L295-L302]  THE BACKUP PRE-FLIGHT.
    #  ANOMALY REPRODUCED (rule R-4): the frozen test is
    #      if cob-crt-status = cob-scr-esc or keyed-reply = "A" or "a"
    #  so ONLY Escape and the two spellings of A abort. Every other reply - the
    #  space moved in at L298 included - proceeds, and there is no retry loop.
    #  The flag therefore defaults to PROCEED and the opt-out is the explicit
    #  form; it is not turned into a required confirmation, which would invert
    #  the legacy default.
    #  `args.ExplicitBooleanOptionalAction`, NOT `argparse.BooleanOptionalAction`.
    #  Observationally identical - both publish `--run-confirmed` and
    #  `--no-run-confirmed` from this one declaration and store the same value, and
    #  the `default` below is untouched, so `--help` still shows the COBOL's own
    #  answer and `gl080.run` still declares it (rule R-4). The difference is that
    #  the explicit action records the FACT that the operator typed the option,
    #  which `main` then requires. The value cannot carry that fact: SPACE proceeds
    #  in the frozen source [general/gl080.cbl:L298-L302], so `run_confirmed=True`
    #  cannot be told apart from "nobody was asked" (CWE-284).
    parser.add_argument(
        "--run-confirmed",
        action=args.ExplicitBooleanOptionalAction,
        default=_RUN_CONFIRMED_DEFAULT,
        help=(
            "Whether the backup pre-flight was satisfied "
            "(general/gl080.cbl:L295-L302). --no-run-confirmed reproduces "
            "pressing Escape or A: gl080 returns BEFORE ANY WRITE OF ANY KIND, "
            "so the database is left completely untouched. In the frozen source "
            "only those three answers abort - every other reply, including the "
            "blank the field is pre-set to at L298, proceeds - so the default is "
            f"{'--run-confirmed' if _RUN_CONFIRMED_DEFAULT else '--no-run-confirmed'}."
        ),
    )

    #  [general/gl080.cbl:L542-L557]  THE DISK-CHANGE OPTION.
    #  ANOMALY REPRODUCED (rule R-4): `if a = 9 go to main-exit` at L546-L547 is
    #  GO TO class 3, a section exit to `main-exit.  exit section.` at L559;
    #  `if a not = zero go to accept-option` at L548-L549 transfers back to
    #  `accept-option.` at L542, whose own only exits are those same two. So 0 is
    #  the ONLY value that proceeds and the default is 0, NOT 9.
    #
    #  `choices=(0, 9)` - AND THAT IS NOT AN ADDED VALIDATION.
    #  THE TEMPTING OPPOSITE READING - that because the frozen program RE-PROMPTS
    #  rather than rejects, restricting the option would add a check the COBOL has
    #  not got - INVERTS THE FACTS. `accept-option.`
    #  [general/gl080.cbl:L542-L549] is a LOOP THAT CANNOT BE LEFT until the value
    #  is 9 (class 3, section exit) or zero (fall-through); every other value goes
    #  straight back to L542. So in the frozen system NO OTHER VALUE EVER REACHES
    #  THE CODE BELOW THE PROMPT - the set of values with which `gl080` can proceed
    #  is exactly {0, 9}. Accepting a third value at this boundary is therefore not
    #  permissiveness, it is a NEW INPUT DOMAIN, and it let database-changing
    #  end-of-period work run on a value legacy execution can never carry there.
    #  `choices` restores the frozen domain and makes a third value a deterministic
    #  argparse usage error (status 2) instead.
    #
    #  The retry ITSELF is still not reproduced, and cannot be: an interactive
    #  re-prompt has no parameter equivalent (Agent Action Plan section 0.4.2
    #  places interactive retry targets outside the migrated surface). What the
    #  loop GUARANTEED - that control leaves the paragraph only on 0 or 9 - is what
    #  is preserved here, which is the requirement.
    #
    #  `type=int` is likewise faithful rather than added: the receiving field is
    #  `77 a pic 99` [general/gl080.cbl:L183] and the screen field at L545 accepts
    #  digits, so a numeric argument is what the frozen source accepts. The callee
    #  stores the value through that field's own descriptor, which truncates
    #  exactly as the screen field would.
    parser.add_argument(
        "--disk-change-option",
        type=int,
        choices=(_DISK_CHANGE_OPTION_PROCEED, _DISK_CHANGE_OPTION_ABORT),
        default=_DISK_CHANGE_OPTION_DEFAULT,
        metavar="N",
        #  RECORDED AS STATED WHEN IT IS TYPED, which is what makes
        #  `args.require_stated` below able to tell an operator who chose 0 from
        #  one who said nothing at all. With argparse's own action the option
        #  would carry the frozen default and `stated_explicitly` would answer
        #  False for every invocation, so the route could never run - the answer
        #  has to be stated and there would be no way to state it.
        action=args.STATED_ACTION,
        help=(
            "The disk-change option gl080 accepts at general/gl080.cbl:L545, "
            "into `77 a pic 99`. 0 PROCEEDS and 9 ABORTS - the program's own "
            "message reads 'Enter <0> to signify change made or <9> to abort "
            "this run' (general/gl080.cbl:L252). 9 is read twice afterwards, at "
            "L408-L409 to skip the whole archiving walk and at L324-L326 to skip "
            "the whole of end-of-period processing, so it suppresses every batch "
            "stamp, every posting delete, the ledger-quarter rollover and the "
            "cycle increment. NO OTHER VALUE IS ACCEPTED, because no other value "
            "can leave the frozen program's input loop: general/gl080.cbl:L548-L549 "
            "sends anything that is neither 0 nor 9 straight back to the prompt, "
            "so 0 and 9 are the only two values the program can proceed on. "
            f"Default {_DISK_CHANGE_OPTION_DEFAULT} - the value that proceeds."
        ),
    )

    #  [general/gl080.cbl:L553-L557]  THE ARCHIVE PATH EDIT.
    #  ANOMALY REPRODUCED (rule R-4): the ONLY guard in the frozen source is
    #  `if file-2 (1:1) = space go to accept-option` at L556-L557. Nothing checks
    #  whether the path exists, whether its directory is writable, or whether it
    #  is absolute - and nothing here does either (rule R-3). The value is a plain
    #  string all the way to the callee, which applies the leading-space test.
    #
    #  A LEADING SPACE DOES NOT MEAN "KEEP THE COMPUTED PATH". The
    #  transfer at L557 goes back to the OPTION prompt at L542, not on to
    #  `main-exit`, so the answer leaves control inside `accept-option` exactly as
    #  a third option value does. The archive file is a flat file and not a schema
    #  table, so the PATH is not itself a table effect - but the TRANSFER is,
    #  because it makes everything after `perform disk-change.`
    #  [general/gl080.cbl:L406] unreachable. The callee therefore reports
    #  UNRESOLVED and ends the run unit rather than silently archiving to the
    #  computed path, which is a state the frozen program has no route to on this
    #  answer.
    parser.add_argument(
        "--archive-path-override",
        default=_ARCHIVE_PATH_OVERRIDE_DEFAULT,
        metavar="PATH",
        help=(
            "Override the archive file path gl080 builds at "
            "general/gl080.cbl:L530-L537. The frozen prompt is "
            "`accept file-2 ... with update` (L555), which presents the field "
            "ALREADY HOLDING that computed path, so omitting this option is the "
            "COBOL default of no override and proceeds. The archive is a flat "
            "file and not a schema table, so the path itself has no effect on any "
            "table dump. A value whose FIRST CHARACTER IS A SPACE returns the "
            "frozen paragraph to its option prompt (L556-L557), from which its "
            "exit is unreachable, so gl080 ends the run unit and performs no "
            "archive, no posting delete, no batch stamp and no period rollover "
            "rather than falling back to the computed path. Nothing else about "
            "the path is checked."
        ),
    )

    #  ---- diagnostics only: no COBOL counterpart, no database effect ---------
    args.add_log_level_argument(parser)

    return parser


def load00(
    linkage: args.GlLinkage,
    *,
    called: str,
    menu_state: args.MenuState,
    run_confirmed: bool,
    disk_change_option: int,
    archive_path_override: str | None,
    dal_options: Mapping[str, object] | None = None,
) -> int:
    """`load00.` - the shared four-parameter dispatch block.

    TWO MOVES PRECEDE THE CALL, AND BOTH ARE HERE. The term-code clear is `load00`'s own
    statement at L714.

    Args:
        linkage: Shape 1, built by `args.bind_gl_linkage`.
        called: the callee's program-id for `WS-Called`, as `load09` supplies it
            [general/general.cbl:L820].
        menu_state: the menu's own working storage, carrying the records
            `args.aa010_get_system_recs` loaded, so that the `> 7` arm can reach
            `overrewrite.` [general/general.cbl:L720-L721].
        run_confirmed: the promoted backup pre-flight answer
            [general/gl080.cbl:L295-L302]. REQUIRED, with no default of its own.
        disk_change_option: the promoted disk-change option
            [general/gl080.cbl:L545-L549]. REQUIRED.
        archive_path_override: the promoted archive path
            [general/gl080.cbl:L553-L557]. REQUIRED, and None means no override.
        dal_options: the caller's keyword-only declarations, transport policy
            among them, carried to every facade context `gl080` builds. NOT a
            COBOL operand - the frozen `CALL` [general/general.cbl:L715-L718]
            passes four things and no fifth. `None`, which `main` leaves it at,
            means "use the one policy `args.install_connection_policy` installed",
            and every handler resolves an unstated declaration against it.

    Returns:
        `WS-Term-Code` as the callee left it - `pic 99` [copybooks/wscall.cob:L10], so
            an `int` in 0..99 (rule R-2).

    Raises:
        RuntimeError: the callee's reproduction of `stop run.` [general/gl080.cbl:L649]
            propagates. Deliberately not caught.
    """
    # [general/general.cbl:L820] move "gl080" to ws-called. The caller's statement,
    # carried out here because `ws-called` is the call target.
    args.set_called(linkage.calling_data, called)

    args.reset_term_code(linkage.calling_data)

    _LOG.info(
        "load00: dispatching %s with run-date %r",
        linkage.calling_data.ws_called.strip(),
        linkage.to_day,
    )

    # L715-L719 call ws-called using ws-calling-data system-record to-day file-defs end-
    # call FOUR POSITIONAL ARGUMENTS IN THE FROZEN ORDER.
    gl080.run(
        linkage.calling_data,
        linkage.system_record,
        linkage.to_day,
        linkage.file_defs,
        run_confirmed=run_confirmed,
        disk_change_option=disk_change_option,
        archive_path_override=archive_path_override,
        #  The operator's transport declaration, carried to every facade context
        #  `gl080` builds. NOT a promoted prompt and NOT a COBOL operand - the
        #  frozen `CALL` at L715-L718 passes four things and no fifth, its bridge
        #  having no transport policy to pass
        #  [copybooks/mysql-procedures.cpy:L72-L77] - so it is stated at the
        #  process boundary, which is the only place that knows. `None` states the
        #  exact-parity policy, which is a statement and not an omission.
        dal_options=dal_options,
    )

    # The callee wrote into the caller's storage, so the code is read back off the same
    # record the COBOL reads it off.
    term_code = linkage.calling_data.ws_term_code

    #  L720  if       ws-term-code > 7
    #  L721           go to overrewrite.
    #
    #  GO TO class 4 (sibling re-dispatch). PER-SITE EQUIVALENCE PROOF:
    #    COBOL  - `go to overrewrite` enters a peer paragraph
    #             [general/general.cbl:L656] which persists System-Record,
    #             Default-Record and WS-System-Record-4, falls through into
    #             `overclose.` [general/general.cbl:L693] and ends at `goback`
    #             [general/general.cbl:L694]. The run unit ends there; control
    #             NEVER returns to this dispatch block.
    #    Python - the serious-error disposition is returned and `main` turns it
    #             into the process exit status through `args.exit_status_for`.
    #             Control never returns to this function either.
    #    Both sides therefore leave the dispatch block for good on this branch,
    #    and the persistence of the three system records happens on both:
    #    `args.overrewrite` is the same paragraph, reproduced once in
    #    `acas_posting.cli.args` and performed here before the return. The only
    #    remaining difference is that paragraph's COBOL-FILE arm
    #    [general/general.cbl:L674-L691], which has no counterpart because the
    #    migration has one store - recorded at `args.RDBMS_STORE_SELECTOR_DIGIT`.
    #
    #  UNREACHABLE ON THIS ROUTE IN PRACTICE, AND IMPLEMENTED ANYWAY. L714 clears
    #  the field immediately before the `CALL` and `gl080` never assigns it - it
    #  ends with a bare `goback` [general/gl080.cbl:L366] - so the value read back
    #  can only be the zero just written. The branch is reproduced because the
    #  frozen dispatch block contains it, not because this callee can trip it.
    if args.is_serious_error(term_code):
        _LOG.error(
            "load00: %s reported a serious error, ws-term-code %d (> %d) "
            "[general/general.cbl:L720-L721]",
            linkage.calling_data.ws_called.strip(),
            term_code,
            args.SERIOUS_ERROR_THRESHOLD,
        )
        #  L721  go to overrewrite.  ->  general/general.cbl:L656-L672
        args.overrewrite(linkage.system_record, menu_state, linkage.file_defs)
        return term_code

    _LOG.info(
        "load00: %s completed, ws-term-code %d",
        linkage.calling_data.ws_called.strip(),
        term_code,
    )
    return term_code


def load09(
    linkage: args.GlLinkage,
    *,
    menu_state: args.MenuState,
    run_confirmed: bool,
    disk_change_option: int,
    archive_path_override: str | None,
    dal_options: Mapping[str, object] | None = None,
) -> int:
    """`load09.` - End Of Cycle Processing. Two statements, and NO GATE.

    NO GATE, BY THE SOURCE'S OWN CONSTRUCTION. This paragraph does not mention `ws-term-
    code`.

    Args:
        linkage: Shape 1, built by `args.bind_gl_linkage` with `called="gl080"`.
        menu_state: the menu's own working storage, built by
            `args.general_menu_state` and already carrying the records
            `args.aa010_get_system_recs` loaded, threaded through so that the
            `> 7` arm of `load00.` can reach
            `overrewrite.` [general/general.cbl:L720-L721].
        run_confirmed: the promoted backup pre-flight answer
            [general/gl080.cbl:L295-L302]. REQUIRED - see `load00`.
        disk_change_option: the promoted disk-change option
            [general/gl080.cbl:L545-L549]. REQUIRED.
        archive_path_override: the promoted archive path [general/gl080.cbl:L553-L557].
            REQUIRED.
        dal_options: forwarded unchanged to `load00`, and from there to every facade
            context `gl080` builds. NOT a COBOL operand. `None` means "use the one
            policy `args.install_connection_policy` installed".

    Returns:
        `WS-Term-Code` as `load00` observed it - `int`, and zero in practice on this
            route.

    Raises:
        RuntimeError: as `load00`.
    """
    # L820 move "gl080" to ws-called. L821 go to load00. ONE STATEMENT PAIR, ONE PYTHON
    # STATEMENT.
    return load00(
        linkage,
        called=_GL080_PROGRAM_ID,
        menu_state=menu_state,
        run_confirmed=run_confirmed,
        disk_change_option=disk_change_option,
        archive_path_override=archive_path_override,
        dal_options=dal_options,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """The CLI boundary: bind argv to Shape 1, run `load09`, return a status.

    No COBOL counterpart - the frozen system reaches `load09` from a curses menu
    [general/general.cbl:L696-L704], and a menu has no process boundary. So this
    function is where the migration's headless equivalent lives, and it does the
    four things that boundary needs and nothing else: parse, configure logging,
    bind, dispatch.

    THE RUN DATE IS THE ONLY WAY A DATE ENTERS (rule R-6). `--run-date` is
    required by `args.add_gl_linkage_arguments`, and `args.bind_gl_linkage` pins
    both observables from it - the text `to-day pic x(10)` and the binary
    `Run-Date` [copybooks/wssystem.cob:L67] - through `acas_posting/clock.py`.
    Nothing here reads a system clock, an environment variable, a host name or an
    entropy source, so two runs of one scenario are byte-identical.

    ALL THREE PROMOTED PARAMETERS ARE PASSED EXPLICITLY. Their defaults live in
    exactly one place, the argparse options built by `_build_parser`, and they
    travel from there through `load09` and `load00` into `gl080.run` without any
    layer being allowed to substitute its own. That is what makes the CLI default
    and the callee default incapable of drifting apart silently.

    A DEFECT IS NOT SWALLOWED; AN EXPECTED CONFIGURATION FAILURE IS NOT RAISED.
    The two are different, and the distinction is what the boundary is for. A
    deployment contract that is absent or unusable (`args.RdbmsParamError`,
    a `ValueError`) and a transport declaration the data-access layer refuses
    (`ConnectionPolicyError`) are BOTH configuration failures at the process
    boundary; both stop the run before anything is connected, opened or written,
    and both are reported as one bounded, redacted line and become the parameter
    loader's own frozen return code through `args.boundary_exit_status`. Letting
    either escape would print a traceback carrying the installation's absolute
    paths, module layout and internal call chain - which tells the operator nothing
    they can act on and tells everyone else rather a lot (CWE-209) - and it is not
    an exit code invented by the migration: 8 and 1 are the codes the frozen
    parameter loader itself returns [common/acas-get-params.cbl:L37-L42].

    A failure INSIDE the cycle is the opposite case and propagates unchanged,
    including the callee's `stop run.` reproduction [general/gl080.cbl:L649],
    because there the traceback is the only diagnostic a genuine defect leaves
    behind. An argparse usage error - a missing `--run-date`, or a destructive
    answer left unstated - raises `SystemExit` from argparse with argparse's own
    status, which is the mechanically checkable proof that neither an ambient run
    date nor an unstated destructive intent can enter the cycle.

    Args:
        argv: the argument vector WITHOUT the program name. `None` means read
            `sys.argv[1:]`, which is argparse's own convention.

    Returns:
        The process exit status: `args.exit_status_for` applied to the `WS-Term-Code`
            the dispatch produced.

    Raises:
        SystemExit: from `parse_args`, for `--help` and for a usage error.
        RuntimeError: as `load09`. THE LIBRARY CONTRACT IS UNCHANGED - a caller
            that imports this function still receives the exception and its
            traceback. Only the PROCESS boundary differs:
            `acas_posting.__main__.run_entry_point` converts it into one
            sanitised ERROR record and a deterministic exit status, so no
            traceback, absolute path or exception payload reaches a terminal.
    """
    parser = _build_parser()
    ns = parser.parse_args(argv)

    #  `--log-level` IS APPLIED THROUGH THE ONE CONFIGURATOR, never by a second
    #  `basicConfig`, and ONLY WHEN THE OPERATOR SUPPLIED IT. The option defaults
    #  to `None` in the shared fragment, so `None` here means "not asked for" and
    #  the level the process boundary chose stands - on a routed run, the router's
    #  own `--log-level`. A supplied level is applied on either route: logging is
    #  configured once at the boundary, and `configure_logging` then sets the level
    #  because this package owns the handler, so the last explicit request wins. An
    #  embedding application's own configuration is never touched. The import is
    #  local to the call for the reason the guard at the foot of this module gives.
    if ns.log_level is not None:
        from acas_posting.__main__ import configure_logging

        configure_logging(ns.log_level)

    #  EXPLICIT DESTRUCTIVE INTENT, CHECKED BEFORE ANYTHING IS BOUND OR OPENED.
    #  `gl080` is the most destructive program of the migrated cycle: its Phase 3
    #  deletes posted transactions and its Phase 5 rolls the ledger quarters over
    #  and increments the accounting cycle [general/gl080.cbl:L319, L330]. Whether
    #  any of that happens is decided by exactly two answers, and IN THE FROZEN
    #  SOURCE BOTH DEFAULT TO PROCEEDING: the backup pre-flight aborts only on
    #  Escape or "A"/"a" and the field is pre-set to SPACE
    #  [general/gl080.cbl:L298-L302], and the disk-change option proceeds on 0 and
    #  aborts on 9 [general/gl080.cbl:L546-L549].
    #
    #  Those defaults are PRESERVED, exactly (rule R-4): they are what `--help`
    #  shows, what the parser stores, and what `gl080.run` declares. What is
    #  refused is the silence. In the frozen program a human read both questions
    #  off the screen - the first sitting under a highlighted warning
    #  [general/gl080.cbl:L295-L297] - and pressed a key; here nobody was asked, so
    #  treating omitted options as that operator's affirmative answers is the
    #  wrapper granting an authorization no one gave (CWE-284). Naming either
    #  spelling of each satisfies this, and the answers named are passed onward
    #  unaltered.
    #
    #  Placed before `bind_gl_linkage` so a refusal leaves the database wholly
    #  untouched - nothing is connected, opened or written at this point.
    args.require_stated(
        parser,
        ns,
        (
            "run_confirmed",
            "whether the backup pre-flight was satisfied "
            "(general/gl080.cbl:L295-L302). Pass --run-confirmed to PROCEED with "
            "end-of-cycle processing, which is the answer the frozen field's "
            "pre-set SPACE gives, or --no-run-confirmed to return before any "
            "write of any kind.",
        ),
        (
            "disk_change_option",
            "the disk-change option (general/gl080.cbl:L542-L549). Pass "
            "--disk-change-option 0 to PROCEED, which DELETES POSTED "
            "TRANSACTIONS, STAMPS EVERY BATCH, ROLLS THE LEDGER QUARTERS OVER AND "
            "INCREMENTS THE ACCOUNTING CYCLE, or --disk-change-option 9 to abort "
            "the run and leave GLPOSTING-REC, GLBATCH-REC and GLLEDGER-REC as the "
            "seed left them.",
        ),
    )

    #  AMBIGUITY Q-CLI-GL080-DEFAULTS: the COBOL prompts have no textual defaults
    #  beyond the pre-filled accept values; confirm the observed database effect
    #  for each promoted parameter - resolve against the compiled oracle; record
    #  in docs/migration/ambiguity-resolutions.md. Citing
    #  [general/gl080.cbl:L298-L302] for the backup pre-flight, whose field is
    #  pre-set to SPACE and where only Escape or "A"/"a" aborts;
    #  [general/gl080.cbl:L546-L549] for the disk-change option, where 0 proceeds
    #  and 9 aborts and every other value re-prompts, so a value the operator
    #  simply Returns past is NOT self-evidently zero on the screen; and
    #  [general/gl080.cbl:L555-L557] for the path edit, presented `with update`
    #  and therefore pre-filled with the path computed at L537. The defaults
    #  chosen here - proceed, 0 and no override - are the reading of the source
    #  set out in this module's docstring; what the ORACLE must confirm is the
    #  resulting table state for each, in particular that 9 leaves GLPOSTING-REC,
    #  GLBATCH-REC and GLLEDGER-REC exactly as the seed left them.
    #  THE MENU'S OWN WORKING-STORAGE. One block, shared by the load below and by
    #  the `overrewrite` inside `load00` - see `args.general_menu_state`, and see
    #  `args.MenuState` for why sharing it is what carries the open connection and
    #  the store selector from one to the other.
    menu_state = args.general_menu_state()

    #  385  aa005-Open-System.   399  aa010-Get-System-Recs.
    #  THE SEEDED ROWS ARE LOADED BEFORE THE DISPATCH, and passing `menu_state`
    #  is what makes that happen: the binder performs `Open-System.`
    #  [general/general.cbl:L385] then `aa010-Get-System-Recs.`
    #  [general/general.cbl:L398-L419] first - file-key 4, then 2, then 1, key 2
    #  being the General Ledger menu's alone [general/general.cbl:L406-L408] - so
    #  `gl080` receives the PERSISTED system record rather than a defaulted one.
    #  The linkage carries the very record the load filled, so what is read there
    #  is what `gl080` then sees. This route needs it more than any other:
    #  `gl080` READS `Period` and `Scycle` [copybooks/wssystem.cob:L63] to decide
    #  whether phase 5 runs at all [general/gl080.cbl:L324-L332] and which cycle to
    #  delete, and it MUTATES `Scycle`, `Current-Quarter` and `Date-Form`
    #  [general/gl080.cbl:L334, :L355-L357, :L360, :L363, :L730] - question Q-21 in
    #  that module's footer, which this load and the `> 7` rewrite in `load00`
    #  together settle. Bound at declared defaults the whole of phase 5 ran from
    #  zeroes.
    #
    #  A FAILING READ IS NOT REFUSED HERE. The frozen paragraph answers `if
    #  fs-reply not = zero` by running the out-of-scope parameter-file set-up
    #  program and looping back [general/general.cbl:L412-L417]; that recovery is
    #  not reproduced, so the reply is left in `File-Access` exactly as it is for
    #  every other handler failure in the migrated cycle, and refusing the run
    #  instead would be a new validation (rule R-3). Recorded at
    #  `args.aa010_get_system_recs`.
    #
    #  THE EXACT TYPE IS CAUGHT, NOT `ValueError`.
    try:
        linkage = args.bind_gl_linkage(
            ns, called=_GL080_PROGRAM_ID, menu_state=menu_state
        )
    except args.RdbmsParamError as error:
        return args.report_configuration_failure(
            error, logger=_LOG, subject="General Ledger end of cycle"
        )

    term_code = load09(
        linkage,
        menu_state=menu_state,
        run_confirmed=ns.run_confirmed,
        disk_change_option=ns.disk_change_option,
        archive_path_override=ns.archive_path_override,
    )

    #  NO `< 8` ARM IN THE DISPATCH BLOCK, AND THAT IS THE FROZEN SHAPE - MEASURED,
    #  NOT ASSUMED. `load09.` is two statements and reaches the dispatch block by
    #  `go to load00` [general/general.cbl:L820-L821]; `load00.` has exactly ONE
    #  transfer to `overrewrite`, guarded by `> 7`
    #  [general/general.cbl:L720-L721], and its ordinary exit falls through to
    #  `load00-exit.` and `go to display-menu` [general/general.cbl:L723-L725],
    #  which persists NOTHING. That transfer is reproduced inside `load00` above
    #  and nowhere else. The General menu DOES have paragraphs that persist on
    #  their ordinary exit - `load03.` through `load06.`, each a `perform
    #  load000`/`perform load00` followed by `perform overrewrite`
    #  [general/general.cbl:L765-L768], [general/general.cbl:L777-L780],
    #  [general/general.cbl:L785-L788], [general/general.cbl:L794-L797] - but
    #  every one of the four dispatches an out-of-scope program, and neither
    #  `load08.` nor `load09.` is among them. Sales and Purchase differ again,
    #  performing `overrewrite` on BOTH arms [sales/sales.cbl:L708-L712],
    #  [purchase/purchase.cbl:L701-L704], which is why the two SL and the two PL
    #  routes persist inside their dispatch wrappers and this one does not. No
    #  `< 8` arm is added to `load00` (rules R-3 and R-4).
    #
    #  595  if       menu-reply = "X"
    #  596           go to pre-overrewrite.
    #  634  pre-overrewrite.  ->  656  overrewrite.  ->  693 overclose. 694 goback.
    #  THE MENU-QUIT PERSISTENCE, PERFORMED ONCE HERE BECAUSE PROCESS COMPLETION
    #  IS THE MENU QUIT. What the frozen system does with the records `gl080`
    #  mutated is persist them when the operator leaves the menu, and this route
    #  needs that more than any other: `gl080` writes `Scycle`
    #  (`programs/gl080_end_of_cycle.py:L1797-L1799`, reproducing
    #  [general/gl080.cbl:L334]), `Current-Quarter` (L2244-L2254, reproducing
    #  [general/gl080.cbl:L355-L360]) and `Date-Form` (L4679) into the CALLER's
    #  `SYSTEM-REC` by reference. Without this statement a successful period end
    #  updates GLLEDGER-REC, GLBATCH-REC and GLPOSTING-REC and leaves SYSTEM-REC at
    #  the PRIOR cycle and quarter, so the next run would repeat the wrong period -
    #  and question Q-21 in that module's footer would stay unanswered.
    #
    #  WHY IT IS THE FROZEN SHAPE AND NOT AN ADDITION. A frozen SESSION has exactly
    #  one exit: `display-menu.` loops until the quit key
    #  [general/general.cbl:L595-L596], and that key reaches `overrewrite.` on
    #  either arm of `pre-overrewrite.` - `go to overrewrite`
    #  [general/general.cbl:L636] with no backup script installed, `perform
    #  overrewrite` [general/general.cbl:L649] with one. So an operator who runs
    #  End Of Cycle and then leaves persists the mutated records exactly once. A
    #  one-shot process runs ONE operation per session, so its ordinary completion
    #  IS that session end. `harness/run_cobol_scenario.sh` drives the oracle
    #  through the same menu and leaves it with "X", so the COBOL side of the
    #  period-end scenario carries these writes; a Python side that skipped them
    #  could not produce Agent Action Plan section 0.8.5's empty diff.
    #
    #  EXACTLY ONCE. `load00` above performs `args.overrewrite` on its `> 7` arm
    #  and returns that code, so a serious error has ALREADY persisted and the
    #  frozen `goback` [general/general.cbl:L694] has already ended the run unit;
    #  the guard therefore skips the second one. Every other code reaches it
    #  unpersisted. The predicate is `args.is_serious_error`, the same
    #  implementation the `> 7` arm uses.
    #
    #  NOT REPRODUCED: the backup spool-out half of `pre-overrewrite.`
    #  [general/general.cbl:L637-L650], which ends in `call "SYSTEM"` and is
    #  excluded by Agent Action Plan section 0.2.2 and by rule R-1. Recorded in the
    #  footer's OMISSIONS.
    if not args.is_serious_error(term_code):
        _LOG.info(
            "persisting the system records once, as the menu does at its quit key "
            "(general/general.cbl:L595-L596 -> L656-L672); ws-term-code %d",
            term_code,
        )
        args.overrewrite(linkage.system_record, menu_state, linkage.file_defs)
    #
    #  AMBIGUITY Q-CLI-EXITSTATUS: which process exit status each band of the
    #  `pic 99` term-code domain should produce - resolve against the compiled
    #  oracle; record in docs/migration/ambiguity-resolutions.md. Citing
    #  [general/general.cbl:L720-L721], the `if ws-term-code > 7 / go to
    #  overrewrite` this route's dispatch block ends on.
    #
    #  ALREADY SETTLED, AND THIS ROUTE DEFERS TO THAT RESOLUTION RATHER THAN
    #  REOPENING IT. `args.exit_status_for` records the finding: a census of the
    #  five menus and all twelve in-scope programs shows `RETURN-CODE` READ and
    #  never WRITTEN, so the compiled cycle emits no exit status derived from
    #  `WS-Term-Code` in any band and there is no oracle observable to measure.
    #  The identity map is the recorded decision, on the ground that it is total
    #  and lossless over 0..99 and that banding would discard distinctions the
    #  COBOL itself makes - 5 (a General Ledger abort) and 8 (a missing extract
    #  file) are different events. The marker is retained so the question remains
    #  greppable from every route it touches; nothing here re-encodes the value.
    return args.exit_status_for(term_code)


if __name__ == "__main__":  # pragma: no cover - module entry point
    #  `harness/run_python_scenario.sh` invokes these modules directly with
    #  `python -m`, and `pyproject.toml` declares no `[project.scripts]`, so this
    #  guard is the documented invocation route rather than a convenience.
    #
    #  ONE PROCESS BOUNDARY FOR BOTH ROUTES. `run_entry_point` configures logging
    #  and converts a failure into one sanitised ERROR and a deterministic exit
    #  status, so a direct invocation behaves exactly as a routed one. The import
    #  is inside the guard because it is needed only when this module IS the
    #  process, and because the router imports this module back when the router
    #  is the process.
    from acas_posting.__main__ import run_entry_point

    raise SystemExit(run_entry_point(main, command="gl-end-of-cycle"))


# --- traceability ------------------------------------------------------------
#
# Rule R-5's record for this route. Every span below was MEASURED against the
# frozen source, which is REFERENCE only: any diff touching general/general.cbl,
# general/gl080.cbl or copybooks/wscall.cob is a defect (Agent Action Plan
# §0.8.1). docs/migration/traceability.md §14.5 carries the route table and the
# §14.4 linkage table; this footer carries only what is local to this file.
#
# FUNCTION -> PARAGRAPH
#     load00   <-  general/general.cbl `load00.` L711-L721. L714 term-code clear,
#                  L715-L718 the `CALL` list, L719 `end-call`, L720-L721 the
#                  serious-error transfer. Fall-through reaches `load00-exit.`
#                  L723 and `go to display-menu` L725, both omitted as screen
#                  handling.
#     load09   <-  general/general.cbl `load09.` L817-L821. Two statements: L820
#                  names gl080, L821 `go to load00`. NO GATE.
#     main     <-  no COBOL counterpart. The CLI boundary; the frozen system
#                  reaches `load09` from the curses dispatch table
#                  [general/general.cbl:L696-L704]. Governed by §0.3.4.
#     _build_parser  <-  no COBOL counterpart. Composes the shared Shape 1
#                  fragments from `acas_posting.cli.args` and adds the three
#                  promoted prompts.
#     Callee: general/gl080.cbl -> acas_posting/programs/gl080_end_of_cycle.py,
#     whole program (§0.2.1.1); only gl051 and irs030 are partial.
#
# `GO TO` CLASSES  -  the sites this file reproduces or reasons about
#     general/general.cbl:L721 `go to overrewrite`  CLASS 4, sibling re-dispatch,
#         reproduced in `load00`. PER-SITE PROOF: the target
#         [general/general.cbl:L656] persists keys 1, 2 and 4, falls through into
#         `overclose.` L693 and ends at `goback` L694, so control never returns to
#         the dispatch block; in Python the serious-error disposition is returned
#         and `main` maps it through `args.exit_status_for`, and control does not
#         return either. Unreachable in practice on this route - L714 clears the
#         field and `gl080` never assigns it, ending at a bare `goback`
#         [general/gl080.cbl:L366] - and implemented regardless.
#     general/general.cbl:L821 `go to load00`  NOT a class-1/2/3 site: an
#         unconditional transfer to a block that transfers onward and never
#         returns. That is why `load09` ends AT its dispatch. Had the source
#         written `perform`, a gate could have followed - which is how `load08`
#         differs [general/general.cbl:L809-L811].
#     general/general.cbl:L725 `go to display-menu`  screen handling, out of scope.
#     general/gl080.cbl:L547 `go to main-exit`  CLASS 3, section exit to L559,
#         carried out inside the callee; the DECISION reaches it through
#         `--disk-change-option`.
#     general/gl080.cbl:L549 and L557 `go to accept-option`  CLASS 1, loop-back to
#         L542. Interactive retries: the LOOP is dropped with the prompt and the
#         DECISION survives as the parameter, because a parameter cannot be
#         retried and the loop had no database effect.
#
# PROMOTED PARAMETER -> LOCATOR   (Agent Action Plan §0.3.4; the semantics and
# defaults are in the module docstring, the callee parameter names here)
#     --run-confirmed / --no-run-confirmed   general/gl080.cbl:L295-L302
#         -> `run_confirmed`.
#     --disk-change-option   general/gl080.cbl:L542-L557, inside
#         `disk-change section.` L519, receiving field `77 a pic 99 value zero.`
#         L183 -> `disk_change_option`. Read back at L408-L409 and L324-L326.
#     --archive-path-override   general/gl080.cbl:L553-L557
#         -> `archive_path_override`. The PATH has no table effect; the TRANSFER
#         does, because it suppresses every write below L406.
#     --log-level   NOT a promoted prompt and NOT a COBOL parameter: diagnostic
#         verbosity for the log records standing in for gl080's screen output.
#         Reaches no program, alters no control flow, appears in no table dump.
#
# DRIFT NOTES  -  measured spans differing from a planning document's citation,
# recorded rather than silently corrected
#     * `load09` is cited L817-L820 by the planning material. MEASURED L817-L821:
#       the label is on L817 and `go to load00.` on L821. Both
#       `acas_posting/__main__.py`'s route table and
#       `programs/gl080_end_of_cycle.py` carry the measured span.
#     * "Phase - 5.  End of Period Processing" is cited at general/gl080.cbl:L330
#       by §0.2.1.1 and §0.6.4. MEASURED L336. The Phase-3 citation L319 is right.
#     * `01 WS-Calling-Data` is cited copybooks/wscall.cob:L6-L13 by §0.4.1.3.
#       MEASURED L6-L14: `WS-CD-Args` is on L14, after the comment on L11.
#
# OMISSIONS  -  recorded so a reader comparing the two trees does not conclude
# something was lost (Agent Action Plan §0.4.3)
#     * `display-menu` and all menu screen I/O, including `load00-exit.`'s
#       `go to display-menu` [general/general.cbl:L723-L725];
#     * the `go to load01 ... depending on z` dispatch table
#       [general/general.cbl:L696-L704] and `loader.` [general/general.cbl:L706-L709];
#     * ONLY THE COBOL-FILE ARM of `overrewrite` [general/general.cbl:L674-L691];
#       the RDB arm IS reproduced by `args.overrewrite`, performed from the `> 7`
#       arm of `load00`, and `overclose.` [general/general.cbl:L693-L694] is the
#       return from `main`. The migration has one store - see
#       `args.RDBMS_STORE_SELECTOR_DIGIT`;
#     * ONLY THE BACKUP HALF of `pre-overrewrite.`
#       [general/general.cbl:L634-L651] - the `nohup` assembly L637-L648 and
#       `call "SYSTEM" using Full-Backup-Script` L650 - excluded by §0.2.2 and
#       rule R-1, with no database effect. ITS PERSISTENCE HALF IS REPRODUCED:
#       both arms of the paragraph reach `overrewrite.`, the quit key is the only
#       exit `display-menu.` has [general/general.cbl:L595-L596], and
#       `harness/run_cobol_scenario.sh` leaves the oracle's menu with "X", so a
#       frozen End-Of-Cycle session always persists what `gl080` mutated. A
#       one-shot process runs one operation per session, so `main` performs it once
#       there, guarded by `args.is_serious_error` so the `> 7` arm cannot persist
#       twice. `acas_posting/cli/args.py` carries the full rationale;
#     * the GL084-GL087 literals [general/gl080.cbl:L252-L255]: their EFFECT is
#       the three promoted parameters, their DISPLAY is not;
#     * the acknowledgement pauses [general/gl080.cbl:L311-L312],
#       [general/gl080.cbl:L648], [general/gl080.cbl:L696]. Where such a pause sat
#       in a path that then transfers control, the TRANSFER is preserved by the
#       callee and only the pause is dropped;
#     * `load000.` [general/general.cbl:L727-L737], the five-argument block
#       serving the out-of-scope gl020 [general/general.cbl:L758] and gl050
#       [general/general.cbl:L784]; this route never reaches it;
#     * the callee's three non-promoted keyword parameters - `file_access`,
#       `dal_common`, `dal_options` - are neither passed nor exposed: the frozen
#       program declares their counterparts in its own WORKING-STORAGE rather than
#       receiving them, so the callee's fresh-record defaults ARE the COBOL state.
#
# AMBIGUITIES  -  each recorded in docs/migration/ambiguity-resolutions.md
#     Q-CLI-EXITSTATUS  [general/general.cbl:L720-L721]. SETTLED in
#         `args.exit_status_for`: `RETURN-CODE` is read and never written in any of
#         the five menus or the twelve programs, so there is no oracle observable
#         and the identity map is the recorded decision. This route re-encodes
#         nothing.
#     Q-CLI-OVERREWRITE-QUIT  [general/general.cbl:L595-L596], [L634-L649],
#         [L656-L672]. SETTLED BY REPRODUCING THE PARAGRAPH: one operation per
#         process means one persist per process, performed at the end of `main`.
#         See OMISSIONS above; `acas_posting/cli/gl_post_cycle.py` states the same
#         resolution.
#     Q-CLI-GL080-DEFAULTS  [general/gl080.cbl:L298-L302], [L546-L549],
#         [L555-L557]. OPEN: the prompts have no textual defaults beyond their
#         pre-filled accept values, so each promoted parameter's observed DATABASE
#         EFFECT is to be confirmed against the compiled oracle - in particular
#         that `--disk-change-option 9` leaves GLPOSTING-REC, GLBATCH-REC and
#         GLLEDGER-REC exactly as the seed left them.
