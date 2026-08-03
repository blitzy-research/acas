"""General Ledger end of cycle - `gl080`, dispatched by `load09.` with no gate.

The batch entry point for `general/general.cbl` `load09.` L817-L821, which is two
statements: name gl080 and dispatch it. There is no term-code test on this route,
and the absence is reproduced - the aborts live in the callee, which is where the
frozen source puts them.

gl080 carries phases 3 and 5, transaction deletion and end-of-period processing
[general/gl080.cbl:L319], [general/gl080.cbl:L330]; the phase numbers are the
program's own and are not the execution order.

Three interactive answers that gate a database write are promoted to parameters
with the COBOL default preserved, per Agent Action Plan section 0.3.4:
`--run-confirmed`, `--disk-change-option` and `--archive-path-override`. Prompts
that only pause for acknowledgement are dropped, keeping any control transfer
they sat in front of.

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
    contain zero clock reads. The frozen call chain holds FOURTEEN ambient date and
    time reads across six files - the census is in `acas_posting/clock.py` and in
    `cli/args.py` - but every one of them is in an out-of-scope menu shell or in
    the date-service copybook those shells COPY
    [copybooks/Proc-ACAS-Mapser-RDB.cob:L72-L80], so pinning at this boundary
    controls both posting observables. Two runs of one scenario are therefore
    byte-identical (section 0.8.5), and the two genuinely open questions are
    marked in place rather than guessed.

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
=======
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
Default-Record and WS-System-Record-4 [general/general.cbl:L656] IS reproduced -
by `args.overrewrite`, performed from the `> 7` arm of `load00`, with the matching
`aa010-Get-System-Recs.` load performed by the binder before the dispatch. Its
COBOL-FILE arm [general/general.cbl:L674-L691] is not, because the migration has
one store. The backup spool-out `call "SYSTEM" using Full-Backup-Script`
[general/general.cbl:L650] remains excluded by Agent Action Plan section 0.2.2 and
by rule R-1. The footer lists every omission.

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
#  is {0, 9} and nothing else - which is what `choices` on the option enforces
#  (finding CLI-07).
_DISK_CHANGE_OPTION_PROCEED: Final[int] = 0
_DISK_CHANGE_OPTION_ABORT: Final[int] = 9

#  ZERO, NOT NINE (rule R-4). The single value that lets control leave the
#  paragraph and the run proceed is 0; getting this backwards would silently
#  disable the archiving walk and the whole of end-of-period processing.
_DISK_CHANGE_OPTION_DEFAULT: Final[int] = _DISK_CHANGE_OPTION_PROCEED

_ARCHIVE_PATH_OVERRIDE_DEFAULT: Final[str | None] = None


#  DIAGNOSTIC VERBOSITY IS NO LONGER DECLARED HERE
#  `--log-level` used to be this module's private option, built from a pair of
#  constants at this point in the file - and so it existed on exactly ONE of the
#  seven entry points. The flag worked for this route and was a usage error for
#  the other six, which matters because `harness/run_python_scenario.sh` invokes
#  the entry points directly rather than through the router. The option is now
#  `args.add_log_level_argument`, composed by all seven, taking its choices and
#  its default from `acas_posting.__main__` - the module that owns the single
#  `basicConfig` that consumes them. Nothing about this route's behaviour changed:
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
    #  THE TRANSPORT DECLARATION - one contract, published on every route
    #  (`args.add_transport_security_arguments`). No COBOL counterpart: the frozen
    #  bridge's connect passes six values and no transport policy at all
    #  [copybooks/mysql-procedures.cpy:L72-L77], transport being compiled into
    #  `cobmysqlapi.c`, so the migration must decide it and the operator is the
    #  only party that knows. Stating NOTHING is the fail-closed policy - loopback
    #  and Unix sockets only - not an absent one. It decides no posted figure, so
    #  it cannot make two runs of one scenario differ (R-6).
    args.add_transport_security_arguments(parser)


    #  [general/gl080.cbl:L295-L302]  THE BACKUP PRE-FLIGHT.
    #  ANOMALY REPRODUCED (rule R-4): the frozen test is
    #      if cob-crt-status = cob-scr-esc or keyed-reply = "A" or "a"
    #  so ONLY Escape and the two spellings of A abort. Every other reply - the
    #  space moved in at L298 included - proceeds, and there is no retry loop.
    #  The flag therefore defaults to PROCEED and the opt-out is the explicit
    #  form; it is not turned into a required confirmation, which would invert
    #  the legacy default.
    #  ⭐ `args.ExplicitBooleanOptionalAction`, NOT `argparse.BooleanOptionalAction`.
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
    #  `choices=(0, 9)` - AND THAT IS NOT AN ADDED VALIDATION (finding CLI-07).
    #  An earlier draft of this file argued the opposite: that because the frozen
    #  program RE-PROMPTS rather than rejects, restricting the option would add a
    #  check the COBOL has not got. The argument inverts the facts. `accept-option.`
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
    #  ⭐ M-04.  A LEADING SPACE DOES NOT MEAN "KEEP THE COMPUTED PATH". The
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
            and every handler resolves that fail-closed.

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
        #  fail-closed policy, which is a statement and not an omission.
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
    deployment contract that is absent or unusable (`rdbms_params.RdbmsParamError`,
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
    #  ⭐ THE SEEDED ROWS ARE LOADED BEFORE THE DISPATCH, and passing `menu_state`
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
    #  zeroes (finding CLI-02).
    #
    #  A FAILING READ IS NOT REFUSED HERE. The frozen paragraph answers `if
    #  fs-reply not = zero` by running the out-of-scope parameter-file set-up
    #  program and looping back [general/general.cbl:L412-L417]; that recovery is
    #  not reproduced, so the reply is left in `File-Access` exactly as it is for
    #  every other handler failure in the migrated cycle, and refusing the run
    #  instead would be a new validation (rule R-3). Recorded at
    #  `args.aa010_get_system_recs`.
    #
    #  THE EXACT TYPE IS CAUGHT, NOT `ValueError` (finding CLI-09).
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
    #  ⭐ THE MENU-QUIT PERSISTENCE, PERFORMED ONCE HERE BECAUSE PROCESS COMPLETION
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
#         ON 0; 9 DECLINES ARCHIVING; anything else re-prompts, i.e. never reaches
#         the paragraph's exit, so the callee ENDS THE RUN UNIT there (M-04) and
#         nothing after L406 executes. Corroborated by the program's own GL084
#         literal at L252. Read back at L408-L409 (skips the archiving walk, and
#         with it the batch stamping at L430-L433) and at L324-L326 (skips all of
#         end-of-period processing). DEFAULT: 0, NOT 9. Callee parameter
#         `disk_change_option`. Receiving field `77 a pic 99 value zero.` L183.
#     --archive-path-override
#         general/gl080.cbl:L553-L557. The path display L553-L554, the
#         `accept file-2 ... with update` L555 - pre-filled with the path built at
#         L530-L537 - and the leading-space guard L556-L557. DEFAULT: no override
#         (None), which the `with update` phrase makes the proceed answer. A
#         leading space transfers to the OPTION prompt L542, not to the exit, so it
#         ends the run unit exactly as a third option value does (M-04) rather than
#         falling back to the computed path. Callee parameter
#         `archive_path_override`. The PATH has no table effect - the archive is a
#         flat file, not a schema table - but the TRANSFER does, because it
#         suppresses every write below L406.
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
#         either. The ONLY difference is the persistence of keys 1, 2 and 4 that
#         the General Ledger form performs [general/general.cbl:L657-L672], which
#         is listed under OMISSIONS: `args.overrewrite` implements the paragraph
#         and the Sales and Purchase routes call it, but Shape 1 carries neither
#         the totals record nor the defaults record, so two of its three rows have
#         no linkage destination here. Unreachable on this route in practice -
#         L714 clears the field and `gl080` never assigns it, ending at a bare
#         `goback` [general/gl080.cbl:L366] - and implemented regardless.
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
#     * ONLY THE COBOL-FILE ARM of `overrewrite` [general/general.cbl:L674-L691]:
#       the RDB arm IS reproduced by `args.overrewrite`, performed from the `> 7`
#       arm of `load00`, and `overclose.` [general/general.cbl:L693] with its
#       `goback` [general/general.cbl:L694] is the return from `main`. The
#       migration has no ISAM store - see `args.RDBMS_STORE_SELECTOR_DIGIT`;
#     * ONLY THE BACKUP HALF of `pre-overrewrite.`
#       [general/general.cbl:L634-L651]: the `string "nohup " ... Run-Backup`
#       assembly [general/general.cbl:L637-L648] and `call "SYSTEM" using
#       Full-Backup-Script` [general/general.cbl:L650], excluded by Agent Action
#       Plan section 0.2.2 and by rule R-1. It has no database effect.
#       ITS PERSISTENCE HALF IS NOW REPRODUCED, and the earlier reading here was
#       wrong - stated so it is not restored. `go to overrewrite`
#       [general/general.cbl:L636] when no backup script is installed and `perform
#       overrewrite` [general/general.cbl:L649] when one is: EITHER WAY the
#       paragraph reached from the quit key [general/general.cbl:L595-L596]
#       persists, and the quit key is the ONLY exit `display-menu.` has. So a
#       frozen operator who runs End Of Cycle and then leaves the menu ALWAYS
#       persists the records `gl080` mutated - `Scycle` [general/gl080.cbl:L334],
#       the rotated quarter [general/gl080.cbl:L355-L357], the rolled-over year
#       [general/gl080.cbl:L360-L363] - and `harness/run_cobol_scenario.sh` leaves
#       the oracle's menu with "X", so the COBOL side of the period-end scenario
#       carries them. A one-shot process runs ONE operation per session, so its
#       ordinary completion IS that session end: `main` performs the paragraph once
#       there, guarded by `args.is_serious_error` so the `> 7` arm inside `load00`
#       cannot persist twice. Without it a successful period end would update
#       GLLEDGER-REC, GLBATCH-REC and GLPOSTING-REC and leave SYSTEM-REC at the
#       prior cycle and quarter, and Agent Action Plan section 0.8.5's empty
#       ordering-normalised diff would be unreachable;
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
#     Q-CLI-OVERREWRITE-QUIT   [general/general.cbl:L595-L596],
#         [general/general.cbl:L634-L649], [general/general.cbl:L656-L672]. NOW
#         SETTLED, BY REPRODUCING THE PARAGRAPH RATHER THAN BY DEFERRING IT. The
#         question was whether a single-operation process has any counterpart to
#         the menu's quit-time rewrite. It does: the quit key is the ONLY exit
#         `display-menu.` has, so a frozen session that ran End Of Cycle always
#         persists on the way out - both arms of `pre-overrewrite.` reach
#         `overrewrite.` - and the oracle harness leaves the menu with "X"
#         accordingly. One operation per process therefore means one persist per
#         process, performed at the end of `main` and guarded by
#         `args.is_serious_error` so the `> 7` arm cannot persist twice. What
#         remains for the oracle is the ordinary table comparison, not this
#         question. Recorded in docs/migration/ambiguity-resolutions.md as settled;
#         the same resolution is stated in `acas_posting/cli/gl_post_cycle.py`.
#     Q-CLI-GL080-DEFAULTS     [general/gl080.cbl:L298-L302],
#         [general/gl080.cbl:L546-L549], [general/gl080.cbl:L555-L557]. OPEN: the
#         prompts have no textual defaults beyond their pre-filled accept values,
#         so the observed DATABASE EFFECT of each promoted parameter is to be
#         confirmed against the compiled oracle - in particular that
#         `--disk-change-option 9` leaves GLPOSTING-REC, GLBATCH-REC and
#         GLLEDGER-REC exactly as the seed left them.
