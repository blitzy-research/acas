"""General Ledger end of cycle - `gl080`, dispatched by `load09.` with NO gate.

The batch entry point for `general/general.cbl` `load09.`, the menu route that
runs End Of Cycle Processing. In the frozen source that route is TWO STATEMENTS::

    L817  load09.
    L820       move     "gl080" to ws-called.
    L821       go       to load00.

and `load00.` is the shared four-parameter dispatch block it transfers to::

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

The callee is `acas_posting.programs.gl080_end_of_cycle`, whose own linkage list
is the same four parameters in the same order::

    269  procedure division using ws-calling-data
    270                           system-record
    271                           to-day
    272                           file-defs.

- the GENERAL LEDGER FOUR-PARAMETER SHAPE, one of the three linkage shapes in
this migration. The Sales and Purchase families add a fifth parameter, the
period-totals record; the IRS program takes neither the calling-data block nor
the run date at all. Shape 1 is built here by `acas_posting.cli.args`, which owns
the binding, so this module defines no linkage of its own.

`load09` HAS NO GATE, AND THAT IS DELIBERATE
============================================
Its sibling `load08.` [general/general.cbl:L805-L815] - the posting cycle - tests
the term code between phases::

    L808       move     "gl070" to ws-called.
    L809       perform  load00.
    L810       if       ws-term-code = 5
    L811                go to display-menu.

`load09` does no such thing. It does not test `ws-term-code`, it has no `= 5`
comparison, and it has no phase to gate: it dispatches one program and the route
is over. Adding a gate here "for symmetry" would be precisely the failure mode
rule R-4 exists to prevent - Agent Action Plan section 0.8.2, verbatim: "A defect
reproduced is correct; a defect fixed is a failure." There is nothing to gate
either, because `gl080` NEVER SETS A TERM CODE; it ends with a bare `goback`
[general/gl080.cbl:L366]. Only three of the twelve in-scope programs raise one at
all: `gl070` raises 5 [general/gl070.cbl:L289], and `sl055`
[sales/sl055.cbl:L344] and `pl055` [purchase/pl055.cbl:L286] each raise 8.

`go to load00`, NOT `perform load00` - SO NOTHING MAY FOLLOW THE DISPATCH
========================================================================
The distinction is load-bearing throughout this folder and it is not a stylistic
one. `perform load00` RETURNS to the statement after it, which is why `load08`
can put a gate on the line following its first two dispatches
[general/general.cbl:L809-L811]. `go to load00` [general/general.cbl:L821] does
NOT return: control falls out of `load00` through `load00-exit.`
[general/general.cbl:L723] and leaves for `display-menu`
[general/general.cbl:L725], never coming back to `load09`. So `load09` below
ends AT its dispatch, and no statement is placed after it.

`load09` REACHES `load00` ONLY - IT NEVER REACHES `load000`
There are two dispatch blocks in this menu, and they differ by one parameter:
`load000.` [general/general.cbl:L727-L737] passes `default-record` as its THIRD
argument, serving the out-of-scope `gl020` and `gl050` set-up programs. This
route uses `load00.` and the four-parameter shape.

THE PHASE NUMBERING IS NOT THE EXECUTION ORDER
==============================================
Agent Action Plan section 0.6.4 asks that this be preserved in the module
docstrings "so a maintainer is not misled", so it is recorded here rather than
left for a reader to trip over. `gl080` displays FIVE phase labels of its own, at
these MEASURED lines::

    L306   "Phase - 1.  Batch Check"
    L316   "Phase - 2.  Transaction Archiving"
    L319   "Phase - 3.  Transaction Deletion"
    L637   "Phase - 4.  Posting Contraction "
    L336   "Phase - 5.  End of Period Processing"

Read against the cycle as a whole, `gl072` - the LAST program of the posting
route this route follows - labels itself "Phase - 4.  Transaction Update"
[general/gl072.cbl:L274]. So the transaction DELETION this route performs is
labelled Phase 3 [general/gl080.cbl:L319] and yet executes AFTER that Phase 4,
and end-of-period processing is labelled Phase 5 [general/gl080.cbl:L336] while
the contraction inside this very program is labelled Phase 4
[general/gl080.cbl:L637]. Phase 1 and Phase 4 each occur twice across the family
under two different meanings. Nothing in this module infers an ordering from a
phase number; `acas_posting.programs.gl080_end_of_cycle` carries the full
five-label analysis.

THE THREE PROMOTED PARAMETERS, AND THEIR VERIFIED DEFAULTS
==========================================================
Agent Action Plan section 0.3.4, verbatim: "Accept prompts that gate a database
write become explicit CLI parameters with the COBOL default preserved." `gl080`
is the only in-scope program with three of them, because it is the only one with
an interactive pre-flight check AND an archive destination. Every default below
was read off the frozen source, not assumed, and every one is the answer that
lets the program PROCEED:

`--run-confirmed` / `--no-run-confirmed`   [general/gl080.cbl:L295-L302]
    The backup pre-flight. ONLY Escape or "A"/"a" aborts::

        L298       move     space to keyed-reply.
        L299       accept   keyed-reply at 1065 with update auto.
        L300       if       cob-crt-status = cob-scr-esc
        L301           or   keyed-reply = "A" or "a"
        L302                goback.

    Every other reply proceeds - INCLUDING the SPACE moved in at L298, which is
    what the operator gets by pressing Return. There is no retry loop. So the
    COBOL default is PROCEED, and `--no-run-confirmed` reproduces the `goback`:
    the program returns before a single write of any kind.

`--disk-change-option`   [general/gl080.cbl:L542-L557]
    The disk-change / archive option, and the clearest database-gating prompt in
    the General Ledger folder::

        L542  accept-option.
        L545       accept   a at 1369.
        L546       if       a = 9
        L547                go to  main-exit.
        L548       if       a  not = zero
        L549                go to  accept-option.

    THE ONLY VALUE THAT PROCEEDS IS 0. `9` aborts, and anything else re-prompts
    for ever. The program's own message says so: "GL084 Enter <0> to signify
    change made or <9> to abort this run" [general/gl080.cbl:L252]. So the
    default is 0 AND NOT 9 - which is the easy thing to get backwards. Answering
    9 is read twice afterwards, at [general/gl080.cbl:L408-L409] to skip the
    whole archiving walk and at [general/gl080.cbl:L324-L326] to skip the whole
    of end-of-period processing, so one keystroke suppresses every batch stamp,
    every posting delete, the ledger-quarter rollover and the cycle increment.

`--archive-path-override`   [general/gl080.cbl:L553-L557]
    The archive path edit. `accept file-2 ... with update` [general/gl080.cbl:
    L555] presents the field ALREADY HOLDING the path `disk-change` computed at
    [general/gl080.cbl:L537], so the COBOL default is NO OVERRIDE. Its only
    guard is that a first character of space re-prompts
    [general/gl080.cbl:L556-L557]; nothing else about the value is examined, and
    nothing else is examined here either (rule R-3). The archive is a flat file
    rather than a schema table, so this parameter has no table effect at all.

The maintainer's own note sits between the two `disk-change` prompts, at
[general/gl080.cbl:L551]: "Hopefully can remove these after testing", echoing the
program header's "NOTE TESTING Code in the disk-change section"
[general/gl080.cbl:L93]. The prompts are acknowledged legacy scaffolding, and
they are reproduced anyway, because their answers change table state.

THE DISPATCH IS UNCONDITIONAL - THE ABORTS LIVE IN THE CALLEE, NOT HERE
======================================================================
An answer that aborts does NOT stop this route from dispatching `gl080`. It is
passed to `gl080` as a parameter, and `gl080` acts on it exactly where the frozen
source acts on it. That is a correctness requirement rather than a layering
preference, and there are two independent proofs:

  * `perform zz070-convert-date` runs at [general/gl080.cbl:L285], BEFORE the
    backup pre-flight at L295-L302, and that section MUTATES the linkage system
    record - `if Date-Form = zero move 1 to Date-Form`
    [general/gl080.cbl:L729-L730]. A route that short-circuited on
    `--no-run-confirmed` would skip a mutation the compiled program performs, so
    the two runs would differ.
  * the disk-change option is read ONLY on the archiving path: `disk-change` is
    performed from `gl080b` [general/gl080.cbl:L406], and the deletion path
    `gl080c` [general/gl080.cbl:L562] never reaches it. So
    `--disk-change-option 9` must not suppress the run itself - in the
    non-archiving configuration it has no effect at all, and skipping the
    dispatch would wrongly cancel the whole of transaction deletion.

`load09` and `load00` below therefore contain no branch on any promoted
parameter. They pass all three through, every time.

WHAT IS NOT HERE
================
The acknowledgement pauses [general/gl080.cbl:L311-L312],
[general/gl080.cbl:L648] and [general/gl080.cbl:L696] are not parameters: their
only effect was to hold a terminal. The screen literals GL084 to GL087 are not
reproduced either - their EFFECT survives as the three parameters above, their
DISPLAY does not. The menu's own `overrewrite` persistence of System-Record,
Default-Record and WS-System-Record-4 [general/general.cbl:L656] and its backup
spool-out `call "SYSTEM" using Full-Backup-Script` [general/general.cbl:L650] are
excluded by Agent Action Plan section 0.2.2 and by rule R-1. The footer lists
every omission.

THE RULES THAT BIND THIS FILE
=============================
`review_rules` reports NO user rules document for this project - it returns the
single line "No user rules provided" - so there is no on-disk rules document to
consult and nothing here is held to an invented one. The binding constraints are
the Agent Action Plan's own six (section 0.7.2), and where they are silent this
file is held to enterprise-standard best practice:

R-1 No COBOL at run time. This module spawns no process, loads no foreign
    library, reaches no part of the GnuCOBOL toolchain and imports nothing from
    the comparison oracle under harness/. There is no option that selects,
    invokes or compares against that oracle; the oracle's own scripts drive this
    entry point from outside, never the reverse.
R-2 Zero binary floating point. `WS-Term-Code` is an `int` (`pic 99`
    [copybooks/wscall.cob:L10]), the disk-change option is an `int` (`77 a pic 99`
    [general/gl080.cbl:L183]), the archive path is a `str` and `to-day` is a
    `str`. No binary-radix numeric type appears in any signature, option type or
    expression.
R-3 No added validation, no added field, no schema change, no concurrency.
    The disk-change option is NOT restricted to 0 and 9, because the COBOL
    re-prompts on a third value rather than rejecting it; the archive path is NOT
    examined for existence, created, or resolved; execution is strictly
    sequential and there is no option that could make it otherwise.
R-4 Legacy behaviour is reproduced, never corrected. Each reproduction below
    carries its COBOL locator in a comment, as section 0.7.4 C-4 requires. The
    reproductions here are: `load09` having no gate, the disk-change option
    proceeding only on 0, the backup confirmation aborting only on Escape or
    "A"/"a", and the archive-path guard being the leading-space test alone.
R-5 Full traceability. The two functions are named after the two paragraphs they
    reproduce, every transfer site carries its `GO TO` class, and the footer
    records the mapping.
R-6 Compiled behaviour is the tie-breaker. The run date arrives ONLY as the
    required `--run-date`, pinned through `args.resolve_clock` into
    `acas_posting/clock.py`; nothing here reads a system clock, an environment
    variable, a host name or an entropy source. All twelve in-scope programs
    contain zero clock reads, and the one clock read in the whole call chain
    lives in the menu shells' date-service copybook
    [copybooks/Proc-ACAS-Mapser-RDB.cob:L72-L80]. Two runs of one scenario are
    therefore byte-identical (section 0.8.5), and the two genuinely open
    questions are marked in place rather than guessed.

NO IMPORT-TIME SIDE EFFECTS
Importing this module binds names and nothing else. It builds no parser,
configures no logging, opens no file or connection, reads nothing from its
surroundings and cannot fail for an environmental reason - a hard requirement
rather than a preference, because the scenario suites import this package.

INVOCATION
    python -m acas_posting.cli.gl_end_of_cycle --run-date DD/MM/CCYY [...]

No console script is declared for it: `pyproject.toml` deliberately has no
`[project.scripts]` table, so the module-execution form above is the documented
route and the one `harness/run_python_scenario.sh` uses.
"""

from __future__ import annotations

import argparse
import logging
from collections.abc import Sequence
from typing import Final

from acas_posting.cli import args
from acas_posting.programs import gl080_end_of_cycle as gl080

__all__: Final[tuple[str, ...]] = ("main", "load00", "load09")

#  Diagnostic displays with no database effect become log records at a severity
#  matching the original's intent (Agent Action Plan section 0.3.4). A log record
#  must not alter control flow and must not appear in any table dump, and none
#  below does. `logging.basicConfig` is called ONLY from `main`, never at import.
_LOG: Final[logging.Logger] = logging.getLogger(__name__)


#  THE PROGRAM-ID THIS ROUTE DISPATCHES
#  [general/general.cbl:L820]  move "gl080" to ws-called.
#  The literal is the whole of `load09`'s first statement. It reaches
#  `WS-Called pic x(8)` [copybooks/wscall.cob:L7] through `args.set_called`, so
#  the field holds "gl080" followed by three spaces rather than five characters -
#  receiving-field width is applied, not assignment.
_GL080_PROGRAM_ID: Final[str] = "gl080"


#  THE THREE PROMOTED-PARAMETER DEFAULTS, EACH READ OFF THE FROZEN SOURCE
#  Named here so that the argparse defaults, the log text and the traceability
#  footer all quote ONE value per parameter. The callee declares the same three
#  defaults [acas_posting/programs/gl080_end_of_cycle.py `run`]; they are not
#  imported from it, because a default that silently followed the callee's would
#  hide a divergence instead of failing on it. The ad-hoc verification asserts
#  the two sets are equal, which is where that check belongs.

#  [general/gl080.cbl:L298-L302]  ANOMALY-CLASS FIDELITY (rule R-4): the abort
#  needs Escape or "A"/"a" and NOTHING ELSE, so the SPACE moved in at L298 - what
#  an operator gets by pressing Return - proceeds. PROCEED is therefore the COBOL
#  default, and it is not softened into a confirmation prompt here.
_RUN_CONFIRMED_DEFAULT: Final[bool] = True

#  [general/gl080.cbl:L546-L549]  ZERO, NOT NINE (rule R-4). `if a = 9 go to
#  main-exit` aborts and `if a not = zero go to accept-option` re-prompts, so the
#  single value that lets control leave the paragraph and the run proceed is 0.
#  Getting this backwards would silently disable the archiving walk and the whole
#  of end-of-period processing.
_DISK_CHANGE_OPTION_DEFAULT: Final[int] = 0

#  [general/gl080.cbl:L553-L557]  NO OVERRIDE. `accept file-2 ... with update`
#  presents the field holding the path already computed at
#  [general/gl080.cbl:L537], so leaving the prompt alone keeps that path. None
#  means exactly that: do not override.
_ARCHIVE_PATH_OVERRIDE_DEFAULT: Final[str | None] = None


#  DIAGNOSTIC VERBOSITY - NOT A COBOL PARAMETER, AND NOT A GATE
#  The frozen program writes its diagnostics to a curses screen; section 0.3.4
#  turns those into log records "at a severity matching the original's intent".
#  A batch entry point therefore needs a severity threshold, and `--log-level`
#  is it. It has NO database effect, cannot alter control flow, is never read by
#  any migrated program and never reaches `gl080.run`. Where the six rules are
#  silent, enterprise-standard best practice applies, and a batch job whose
#  operator cannot choose between quiet and verbose is not production-ready.
_LOG_LEVEL_CHOICES: Final[tuple[str, ...]] = (
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
    "CRITICAL",
)
_LOG_LEVEL_DEFAULT: Final[str] = "INFO"

#  DETERMINISM EXTENDS TO THE LOG STREAM (rule R-6). The format carries no
#  timestamp, no process id and no thread name, so two runs of one scenario
#  produce byte-identical log text as well as byte-identical table dumps. That is
#  stricter than section 0.8.5 requires - it speaks of dumps - and it costs
#  nothing: it also means nothing in this module can reach a clock even
#  indirectly, through a formatter.
_LOG_FORMAT: Final[str] = "%(levelname)s %(name)s: %(message)s"


def _build_parser() -> argparse.ArgumentParser:
    """Build this route's parser: the shared Shape 1 options plus `gl080`'s three.

    The shared options are NOT redefined here. `acas_posting.cli.args` owns the
    binding of `01 WS-Calling-Data` [copybooks/wscall.cob:L6-L14], the required
    `--run-date` and the two settable `SYSTEM-REC` fields, and every entry point
    of this package composes those fragments rather than restating them, so the
    binding has one spelling. What this function adds is exactly the three
    options that are specific to `gl080` - a promoted prompt of another program
    has no business in a shared fragment - plus the diagnostic verbosity knob.

    Returns:
        A parser that has never been parsed. Built on demand and never at import,
        so importing this module does no work.
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

    #  Shape 1, composed from the shared fragments. `default_caller` is the
    #  dispatching menu's own literal, `move "general" to ws-caller`
    #  [general/general.cbl:L512] - this route is dispatched by the General
    #  Ledger menu and by no other.
    args.add_calling_data_arguments(
        parser, default_caller=args.WS_CALLER_GENERAL
    )
    args.add_gl_linkage_arguments(parser)

    #  ---- gl080's three promoted prompts  (Agent Action Plan section 0.3.4) ---

    #  [general/gl080.cbl:L295-L302]  THE BACKUP PRE-FLIGHT.
    #  ANOMALY REPRODUCED (rule R-4): the frozen test is
    #      if cob-crt-status = cob-scr-esc or keyed-reply = "A" or "a"
    #  so ONLY Escape and the two spellings of A abort. Every other reply - the
    #  space moved in at L298 included - proceeds, and there is no retry loop.
    #  The flag therefore defaults to PROCEED and the opt-out is the explicit
    #  form; it is not turned into a required confirmation, which would invert
    #  the legacy default.
    parser.add_argument(
        "--run-confirmed",
        action=argparse.BooleanOptionalAction,
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
    #  `if a not = zero go to accept-option` at L548-L549 is GO TO class 1, a
    #  loop-back to `accept-option.` at L542. So 0 is the ONLY value that
    #  proceeds and the default is 0, NOT 9.
    #
    #  NO `choices=` (rule R-3). The frozen program does not REJECT a third
    #  value, it RE-PROMPTS for ever - a behaviour with no database effect and no
    #  parameter equivalent - so restricting the option to 0 and 9 would add a
    #  validation the COBOL has not got. `type=int` is not such an addition: the
    #  receiving field is `77 a pic 99` [general/gl080.cbl:L183] and the screen
    #  field at L545 accepts digits, so a numeric argument is what the frozen
    #  source accepts. The callee stores the value through that field's own
    #  descriptor, which truncates exactly as the screen field would.
    parser.add_argument(
        "--disk-change-option",
        type=int,
        default=_DISK_CHANGE_OPTION_DEFAULT,
        metavar="N",
        help=(
            "The disk-change option gl080 accepts at general/gl080.cbl:L545, "
            "into `77 a pic 99`. 0 PROCEEDS and 9 ABORTS - the program's own "
            "message reads 'Enter <0> to signify change made or <9> to abort "
            "this run' (general/gl080.cbl:L252). 9 is read twice afterwards, at "
            "L408-L409 to skip the whole archiving walk and at L324-L326 to skip "
            "the whole of end-of-period processing, so it suppresses every batch "
            "stamp, every posting delete, the ledger-quarter rollover and the "
            "cycle increment. Any other value re-prompts in the frozen source "
            "and is carried forward unchanged here; it is deliberately not "
            f"rejected. Default {_DISK_CHANGE_OPTION_DEFAULT} - the value that "
            "proceeds."
        ),
    )

    #  [general/gl080.cbl:L553-L557]  THE ARCHIVE PATH EDIT.
    #  ANOMALY REPRODUCED (rule R-4): the ONLY guard in the frozen source is
    #  `if file-2 (1:1) = space go to accept-option` at L556-L557, GO TO class 1
    #  again. Nothing checks whether the path exists, whether its directory is
    #  writable, or whether it is absolute - and nothing here does either
    #  (rule R-3). The value is a plain string all the way to the callee, which
    #  applies the leading-space test and keeps the computed path when it fires.
    parser.add_argument(
        "--archive-path-override",
        default=_ARCHIVE_PATH_OVERRIDE_DEFAULT,
        metavar="PATH",
        help=(
            "Override the archive file path gl080 builds at "
            "general/gl080.cbl:L530-L537. The frozen prompt is "
            "`accept file-2 ... with update` (L555), which presents the field "
            "ALREADY HOLDING that computed path, so omitting this option is the "
            "COBOL default of no override. The archive is a flat file and not a "
            "schema table, so this has no effect on any table dump. A value "
            "whose first character is a space is declined and the computed path "
            "kept, reproducing L556-L557; nothing else about the path is checked."
        ),
    )

    #  ---- diagnostics only: no COBOL counterpart, no database effect ---------
    parser.add_argument(
        "--log-level",
        choices=_LOG_LEVEL_CHOICES,
        default=_LOG_LEVEL_DEFAULT,
        help=(
            "Severity threshold for the log records that replace gl080's screen "
            "output (Agent Action Plan section 0.3.4). Diagnostic only: it "
            "reaches no migrated program, alters no control flow and appears in "
            f"no table dump. Default {_LOG_LEVEL_DEFAULT}."
        ),
    )

    return parser


def load00(
    linkage: args.GlLinkage,
    *,
    called: str,
    run_confirmed: bool,
    disk_change_option: int,
    archive_path_override: str | None,
) -> int:
    """`load00.` - the shared four-parameter dispatch block.

    [general/general.cbl:L711-L721], reproduced statement by statement::

        L711  load00.
        L714       move     zero to ws-term-code.
        L715       call     ws-called using ws-calling-data
        L716                                system-record
        L717                                to-day
        L718                                file-defs
        L719       end-call
        L720       if       ws-term-code > 7
        L721                go to overrewrite.

    TWO MOVES PRECEDE THE CALL, AND BOTH ARE HERE. The term-code clear is
    `load00`'s own statement at L714. The program-id move is the CALLER's - `move
    "gl080" to ws-called` [general/general.cbl:L820] - and it is performed here
    rather than in `load09` because `ws-called` IS the call target
    (`call ws-called` at L715 is a dynamic call by name), so the value has to
    travel with the dispatch. `load09` supplies it; this function performs the
    `MOVE`. They are done in the frozen source's own order, the program-id first
    at L820 and the clear second at L714; the two write different fields, so the
    order between them cannot change an outcome either way.

    BOTH MOVES ARE PERFORMED PER DISPATCH, WHICH IS WHERE THE COBOL PUTS THEM.
    `args.bind_gl_linkage` already performed both while building the linkage, so
    on this single-dispatch route the pair is redundant - and it is executed
    anyway, because the frozen source executes it once per `CALL` and the
    placement is load-bearing on the multi-dispatch routes: `WS-Term-Code` is
    shared linkage storage, so a code a previous callee left behind would still be
    there for the next test of it.

    WHAT THE CALL BECOMES. `call ws-called` is a dynamic call by name in the
    COBOL; here the callee is imported and invoked directly (rule R-1 - no COBOL
    at run time, and nothing loads a compiled module). Its four arguments are
    passed POSITIONALLY, in the frozen parameter order
    [general/gl080.cbl:L269-L272], so a reviewer can diff the argument lists side
    by side. The three promoted parameters are passed as keywords and ALWAYS
    EXPLICITLY - see `main`.

    Args:
        linkage: Shape 1, built by `args.bind_gl_linkage`. Its `calling_data` is
            MUTATED here (the term-code clear and the program-id move) and is
            mutable by design, exactly as COBOL writes into the caller's own
            storage.
        called: the callee's program-id for `WS-Called`, as `load09` supplies it
            [general/general.cbl:L820].
        run_confirmed: the promoted backup pre-flight answer
            [general/gl080.cbl:L295-L302]. REQUIRED, with no default of its own.
        disk_change_option: the promoted disk-change option
            [general/gl080.cbl:L545-L549]. REQUIRED.
        archive_path_override: the promoted archive path
            [general/gl080.cbl:L553-L557]. REQUIRED, and None means no override.

    Returns:
        `WS-Term-Code` as the callee left it - `pic 99`
        [copybooks/wscall.cob:L10], so an `int` in 0..99 (rule R-2). Zero on this
        route in practice, because `gl080` never sets one.

    Raises:
        RuntimeError: the callee's reproduction of `stop run.`
            [general/gl080.cbl:L649] propagates. Deliberately not caught: the
            statement ends the run unit in the frozen source too, and swallowing
            it here would convert a documented abort into a silent one.
    """
    #  [general/general.cbl:L820]  move "gl080" to ws-called.
    #  The caller's statement, carried out here because `ws-called` is the call
    #  target. Receiving-field width is applied by `set_called`, so `PIC X(8)`
    #  ends up holding eight characters.
    args.set_called(linkage.calling_data, called)

    #  [general/general.cbl:L714]  move zero to ws-term-code.
    args.reset_term_code(linkage.calling_data)

    _LOG.info(
        "load00: dispatching %s with run-date %r",
        linkage.calling_data.ws_called.strip(),
        linkage.to_day,
    )

    #  L715-L719  call ws-called using ws-calling-data
    #                              system-record
    #                              to-day
    #                              file-defs
    #             end-call
    #
    #  FOUR POSITIONAL ARGUMENTS IN THE FROZEN ORDER. Nothing is added to,
    #  removed from or reordered within the list.
    #
    #  THE THREE PROMOTED PARAMETERS ARE PASSED EXPLICITLY, EVERY TIME. The
    #  callee declares defaults for all three and they agree with the frozen
    #  source, but passing them anyway is what makes a divergence between this
    #  route's defaults and the callee's IMPOSSIBLE TO HIDE: nothing here can
    #  fall back on the other side's opinion of what the COBOL default is. They
    #  are keyword-only and have no default in this function's own signature for
    #  the same reason - a caller must state all three.
    #
    #  The callee's THREE remaining keyword parameters - `file_access`,
    #  `dal_common` and `dal_options`, whose counterparts the frozen program
    #  declares in its own WORKING-STORAGE rather than receiving through linkage -
    #  are deliberately NOT passed and NOT exposed as options: they are not
    #  promoted prompts, and leaving them at their defaults gives the fresh
    #  records that `WORKING-STORAGE` provides. (`gl080.run` declares six
    #  keyword-only parameters in all: these three plus the three promoted ones.
    #  Its own docstring calls this group "the other four", which miscounts it;
    #  the signature is authoritative and it lists three.)
    gl080.run(
        linkage.calling_data,
        linkage.system_record,
        linkage.to_day,
        linkage.file_defs,
        run_confirmed=run_confirmed,
        disk_change_option=disk_change_option,
        archive_path_override=archive_path_override,
    )

    #  The callee wrote into the caller's storage, so the code is read back off
    #  the same record the COBOL reads it off.
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
    #    and the ONLY difference is the omitted persistence of the three system
    #    records - menu behaviour excluded by Agent Action Plan section 0.2.2,
    #    recorded as an omission in the footer rather than silently dropped.
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
        return term_code

    #  Fall-through is `load00-exit.` [general/general.cbl:L723], whose whole body
    #  is `go to display-menu` [general/general.cbl:L725] - screen handling, out
    #  of scope, so nothing stands in for it.
    _LOG.info(
        "load00: %s completed, ws-term-code %d",
        linkage.calling_data.ws_called.strip(),
        term_code,
    )
    return term_code


def load09(
    linkage: args.GlLinkage,
    *,
    run_confirmed: bool,
    disk_change_option: int,
    archive_path_override: str | None,
) -> int:
    """`load09.` - End Of Cycle Processing. Two statements, and NO GATE.

    [general/general.cbl:L817-L821], in its entirety::

        L817  load09.
        L820       move     "gl080" to ws-called.
        L821       go       to load00.

    NO GATE, BY THE SOURCE'S OWN CONSTRUCTION. This paragraph does not mention
    `ws-term-code`. Its sibling `load08.` [general/general.cbl:L805-L815] does -
    `if ws-term-code = 5 go to display-menu` at L810-L811, the hard abort gate
    that stops the posting cycle when a batch was left open - and the difference
    between the two paragraphs is not an oversight to be tidied away: `gl080`
    never sets a term code, so there is nothing here to gate. Rule R-4 is
    explicit that a defect fixed is a failure, and this is not even a defect;
    adding a gate "for symmetry" would invent behaviour outright.

    NOTHING FOLLOWS THE DISPATCH, BECAUSE L821 IS `go to` AND NOT `perform`. A
    `perform` returns to the following statement, which is exactly how `load08`
    is able to test the term code after its first dispatch
    [general/general.cbl:L809-L811]. A `go to` does not return: control leaves
    `load00` through `load00-exit.` [general/general.cbl:L723] for
    `display-menu` [general/general.cbl:L725] and never comes back here. So this
    function ends at its dispatch, and the returned value is `load00`'s own -
    passed straight out rather than acted on, because acting on it would be code
    after a transfer the COBOL cannot return from.

    Args:
        linkage: Shape 1, built by `args.bind_gl_linkage` with `called="gl080"`.
        run_confirmed: the promoted backup pre-flight answer
            [general/gl080.cbl:L295-L302]. REQUIRED - see `load00`.
        disk_change_option: the promoted disk-change option
            [general/gl080.cbl:L545-L549]. REQUIRED.
        archive_path_override: the promoted archive path
            [general/gl080.cbl:L553-L557]. REQUIRED.

    Returns:
        `WS-Term-Code` as `load00` observed it - `int`, and zero in practice on
        this route.

    Raises:
        RuntimeError: as `load00`.
    """
    #  L820  move "gl080" to ws-called.
    #  L821  go   to load00.
    #  ONE STATEMENT PAIR, ONE PYTHON STATEMENT: the program-id is handed to the
    #  dispatch block, which performs the `MOVE` and issues the call. GO TO
    #  class 4 (sibling re-dispatch) - the transfer enters a peer paragraph that
    #  itself transfers onward, and because that onward transfer never returns
    #  here, the equivalent is a call whose value is returned immediately with no
    #  statement between. See the per-site proof in `load00`.
    return load00(
        linkage,
        called=_GL080_PROGRAM_ID,
        run_confirmed=run_confirmed,
        disk_change_option=disk_change_option,
        archive_path_override=archive_path_override,
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

    ERRORS ARE NOT SWALLOWED. `args.bind_gl_linkage` raises when the deployment
    contract that carries the six connection parameters is absent or unusable,
    and that exception is deliberately allowed to propagate: a run that cannot
    reach the provisioned database must stop loudly BEFORE it writes anything,
    and returning a status for it would mean inventing an exit code the frozen
    system has no counterpart for. The callee's `stop run.` reproduction
    [general/gl080.cbl:L649] propagates for the same reason. An argparse usage
    error - a missing `--run-date`, say - raises `SystemExit` from `parse_args`
    with argparse's own status, which is the mechanically checkable proof that no
    ambient run date exists.

    Args:
        argv: the argument vector WITHOUT the program name. `None` means read
            `sys.argv[1:]`, which is argparse's own convention; a caller passes a
            sequence explicitly, and the scenario harness does.

    Returns:
        The process exit status: `args.exit_status_for` applied to the
        `WS-Term-Code` the dispatch produced. That mapping is the identity, so a
        caller sees the code the migrated cycle produced rather than a lossy
        re-encoding of it, and zero - the value this route yields in practice -
        is success in both vocabularies.

    Raises:
        SystemExit: from `parse_args`, for `--help` and for a usage error.
        RuntimeError: as `load09`.
    """
    parser = _build_parser()
    ns = parser.parse_args(argv)

    #  CONFIGURED HERE AND NOWHERE ELSE. `basicConfig` mutates global state, so
    #  it belongs to the process entry point rather than to import: a library
    #  import that configured logging would hijack its host application's
    #  handlers. Placed after `parse_args` so that `--log-level` is known, and
    #  before the binder so that everything the run reports is captured.
    logging.basicConfig(level=ns.log_level, format=_LOG_FORMAT)

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
    linkage = args.bind_gl_linkage(ns, called=_GL080_PROGRAM_ID)

    #  L817-L821, entered. Every promoted parameter is named at the call site.
    term_code = load09(
        linkage,
        run_confirmed=ns.run_confirmed,
        disk_change_option=ns.disk_change_option,
        archive_path_override=ns.archive_path_override,
    )

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
    raise SystemExit(main())


# --- traceability ------------------------------------------------------------
#
# Rule R-5 requires that every program map to a module, every paragraph to a
# function and every field to a data-dictionary entry, and that the mapping be
# RECORDED rather than left implicit. This footer is that record for the General
# Ledger end-of-cycle route. Every line span below was MEASURED against the
# frozen source, which is REFERENCE only: any diff touching general/general.cbl,
# general/gl080.cbl or copybooks/wscall.cob is a defect in the migration
# (Agent Action Plan section 0.8.1).
#
# FUNCTION -> PARAGRAPH
#     load00   <-  general/general.cbl  `load00.`   L711-L721
#                  The shared four-parameter dispatch block. L714 the term-code
#                  clear, L715-L718 the `CALL` parameter list, L719 `end-call`,
#                  L720-L721 the serious-error transfer. Fall-through reaches
#                  `load00-exit.` L723 and `go to display-menu` L725, both screen
#                  handling and both omitted.
#     load09   <-  general/general.cbl  `load09.`   L817-L821
#                  L817 the label, L820 `move "gl080" to ws-called`, L821
#                  `go to load00`. TWO STATEMENTS AND NO GATE - contrast
#                  `load08.` L805-L815, whose gate is at L810-L811.
#     main     <-  no COBOL counterpart. The CLI boundary: the frozen system
#                  reaches `load09` from a curses menu through the
#                  `go to load01 ... depending on z` table L696-L704, and a menu
#                  has no process boundary. Governed by Agent Action Plan
#                  section 0.3.4 rather than by a paragraph.
#     _build_parser  <-  no COBOL counterpart. Composes the shared Shape 1
#                  fragments from `acas_posting.cli.args` and adds gl080's three
#                  promoted prompts.
#
# PROGRAM -> MODULE
#     general/gl080.cbl  ->  acas_posting/programs/gl080_end_of_cycle.py
#     Linkage: `procedure division using ws-calling-data, system-record, to-day,
#     file-defs` [general/gl080.cbl:L269-L272] - the General Ledger
#     FOUR-PARAMETER shape, passed positionally in that order by `load00`.
#     Migration boundary: the whole program (Agent Action Plan section 0.2.1.1);
#     only `gl051` and `irs030` are partial.
#
# LINKAGE -> DICTIONARY / RECORD LAYER
#     `01 WS-Calling-Data`  copybooks/wscall.cob:L6-L14 - seven fields, 41 bytes.
#     Bound by `acas_posting.cli.args`, which is the ONE place this migration
#     binds it; this module redefines no part of it. The two fields this route
#     touches by name:
#         WS-Called     pic x(8)  copybooks/wscall.cob:L7  <- `args.set_called`
#         WS-Term-Code  pic 99    copybooks/wscall.cob:L10 <- `args.reset_term_code`,
#                       read back after the dispatch. `pic 99` is why the term
#                       code is an `int` in 0..99 and never a float (rule R-2).
#
# PROMOTED PARAMETER -> LOCATOR   (Agent Action Plan section 0.3.4)
#     --run-confirmed / --no-run-confirmed
#         general/gl080.cbl:L295-L302. Displays GL085-GL087 L295-L297, the field
#         pre-set to SPACE L298, the accept L299, and the abort test L300-L302.
#         ABORTS ONLY on Escape or "A"/"a"; every other reply proceeds, the blank
#         default included. DEFAULT: proceed (--run-confirmed). Callee parameter
#         `run_confirmed`.
#     --disk-change-option
#         general/gl080.cbl:L542-L557, inside `disk-change section.` L519. The
#         accept L545, `a = 9` L546-L547, `a not = zero` L548-L549. PROCEEDS ONLY
#         ON 0; 9 ABORTS; anything else re-prompts. Corroborated by the program's
#         own GL084 literal at L252. Read back at L408-L409 (skips the archiving
#         walk, and with it the batch stamping at L430-L433) and at L324-L326
#         (skips all of end-of-period processing). DEFAULT: 0, NOT 9. Callee
#         parameter `disk_change_option`. Receiving field `77 a pic 99 value zero.`
#         L183.
#     --archive-path-override
#         general/gl080.cbl:L553-L557. The path display L553-L554, the
#         `accept file-2 ... with update` L555 - pre-filled with the path built at
#         L530-L537 - and the leading-space guard L556-L557. DEFAULT: no override
#         (None). Callee parameter `archive_path_override`. No table effect: the
#         archive is a flat file, not a schema table.
#     --log-level
#         NOT a promoted prompt and NOT a COBOL parameter. Diagnostic verbosity
#         for the log records that stand in for gl080's screen output
#         (Agent Action Plan section 0.3.4). Reaches no migrated program, alters
#         no control flow, appears in no table dump.
#
#     NO PROMOTED PARAMETER IS BRANCHED ON HERE. An aborting answer is passed to
#     `gl080` and acted on inside it, at the line the frozen source acts on it.
#     Short-circuiting the dispatch instead would change behaviour twice over:
#     `perform zz070-convert-date` [general/gl080.cbl:L285] precedes the backup
#     pre-flight and MUTATES the linkage system record
#     [general/gl080.cbl:L729-L730], and the disk-change option is read only on
#     the archiving path [general/gl080.cbl:L406] so on the deletion path
#     [general/gl080.cbl:L562] the value 9 has no effect at all. See THE DISPATCH
#     IS UNCONDITIONAL in the module docstring.
#
# `GO TO` CLASSES  -  every transfer site this file reproduces or reasons about
#     general/general.cbl:L721   `go to overrewrite`   CLASS 4, sibling
#         re-dispatch. Reproduced in `load00`. PER-SITE PROOF: the COBOL target
#         [general/general.cbl:L656] persists System-Record, Default-Record and
#         WS-System-Record-4, falls through into `overclose.` L693 and ends at
#         `goback` L694, so the run unit ends and control never returns to the
#         dispatch block; in Python the serious-error disposition is returned and
#         `main` maps it through `args.exit_status_for`, and control never returns
#         either. The ONLY difference is the omitted persistence, listed under
#         OMISSIONS. Unreachable on this route in practice - L714 clears the field
#         and `gl080` never assigns it, ending at a bare `goback`
#         [general/gl080.cbl:L366] - and implemented regardless.
#     general/general.cbl:L821   `go to load00`        NOT a class-1/2/3 site: an
#         unconditional transfer to the shared dispatch block, which itself
#         transfers onward and never returns. That is why `load09` ends AT its
#         dispatch and why NO statement follows it. Had the source written
#         `perform load00`, a gate could have followed - which is exactly how
#         `load08` differs [general/general.cbl:L809-L811].
#     general/general.cbl:L725   `go to display-menu`  screen handling, out of
#         scope; nothing stands in for it.
#     general/gl080.cbl:L547     `go to main-exit`     CLASS 3, section exit to
#         `main-exit.  exit section.` L559. Carried out inside the callee; the
#         DECISION reaches it through `--disk-change-option`.
#     general/gl080.cbl:L549     `go to accept-option` CLASS 1, loop-back to
#         `accept-option.` L542. An interactive retry: the LOOP is dropped with
#         the prompt and the DECISION is preserved as the parameter, because a
#         parameter cannot be retried and the loop had no database effect.
#     general/gl080.cbl:L557     `go to accept-option` CLASS 1, loop-back to L542
#         again, for a path whose first character is a space. Same treatment: the
#         retry goes, the rejection stays - inside the callee.
#
# DRIFT NOTES  -  measured spans that differ from a planning document's citation.
# Recorded rather than silently corrected, so that a reader comparing the two
# lands on the measurement.
#     * `load09` is cited as L817-L820 by the `acas_posting/__main__.py` route
#       table. The MEASURED span is L817-L821: `go to load00.` is on L821.
#       `acas_posting/cli/__init__.py` already cites L817-L821.
#     * The "Phase - 5.  End of Period Processing" literal is cited at
#       general/gl080.cbl:L330 by Agent Action Plan sections 0.2.1.1 and 0.6.4.
#       The MEASURED line is L336. The Phase-3 citation L319 is correct.
#     * `01 WS-Calling-Data` is cited as copybooks/wscall.cob:L6-L13 by Agent
#       Action Plan section 0.4.1.3. The MEASURED span is L6-L14: `WS-CD-Args` is
#       on L14, after the comment on L11.
#
# OMISSIONS  -  recorded so that a reader comparing the two trees does not
# conclude something was lost (Agent Action Plan section 0.4.3):
#     * `display-menu` and ALL menu screen I/O, including `load00-exit.`'s
#       `go to display-menu` [general/general.cbl:L723-L725];
#     * the `go to load01 ... load09 ... depending on z` dispatch table
#       [general/general.cbl:L696-L704] and the `loader.` fall-back
#       [general/general.cbl:L706-L709];
#     * `overrewrite`'s persistence of System-Record, Default-Record and
#       WS-System-Record-4 [general/general.cbl:L656] through `overclose.`
#       [general/general.cbl:L693] to `goback` [general/general.cbl:L694], and
#       `pre-overrewrite`'s backup spool-out
#       `call "SYSTEM" using Full-Backup-Script` [general/general.cbl:L650] -
#       both excluded by Agent Action Plan section 0.2.2 and by rule R-1;
#     * the GL084-GL087 screen literals themselves
#       [general/gl080.cbl:L252-L255]: their EFFECT is preserved as the three
#       promoted parameters, their DISPLAY is not;
#     * the pure-acknowledgement pauses [general/gl080.cbl:L311-L312],
#       [general/gl080.cbl:L648] and [general/gl080.cbl:L696], whose only effect
#       was to hold a terminal. Where such a pause sits in a path that then
#       transfers control, the CONTROL TRANSFER is preserved by the callee and
#       only the pause is dropped;
#     * `load000.` [general/general.cbl:L727-L737], the FIVE-argument dispatch
#       block whose third argument is `default-record`. It serves the out-of-scope
#       set-up programs gl020 [general/general.cbl:L758] and gl050
#       [general/general.cbl:L784], and this route never reaches it;
#     * the callee's three non-promoted keyword parameters - `file_access`,
#       `dal_common` and `dal_options` - are neither passed nor exposed as
#       options: the frozen program declares their counterparts in its own
#       WORKING-STORAGE rather than receiving them, so the callee's fresh-record
#       defaults ARE the COBOL state. `gl080.run` declares six keyword-only
#       parameters: these three and the three promoted ones.
#
# AMBIGUITIES  -  each recorded in docs/migration/ambiguity-resolutions.md
#     Q-CLI-EXITSTATUS         [general/general.cbl:L720-L721]. SETTLED in
#         `acas_posting/cli/args.py` `exit_status_for`: `RETURN-CODE` is read and
#         never written anywhere in the five menus or the twelve in-scope
#         programs, so there is no oracle observable and the identity map is the
#         recorded decision. This route defers to it and re-encodes nothing.
#     Q-CLI-GL080-DEFAULTS     [general/gl080.cbl:L298-L302],
#         [general/gl080.cbl:L546-L549], [general/gl080.cbl:L555-L557]. OPEN: the
#         prompts have no textual defaults beyond their pre-filled accept values,
#         so the observed DATABASE EFFECT of each promoted parameter is to be
#         confirmed against the compiled oracle - in particular that
#         `--disk-change-option 9` leaves GLPOSTING-REC, GLBATCH-REC and
#         GLLEDGER-REC exactly as the seed left them.
