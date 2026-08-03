"""IRS nominal-ledger posting - the THIRD linkage shape, three parameters.

`python -m acas_posting.cli.irs_post` reproduces the option `"4"` branch of
irs/irs.cbl `Main-Loop.` [irs/irs.cbl:L637], whose whole body is one `CALL`
[irs/irs.cbl:L666-L672]::

    L666       if       Menu-Reply = "4"
    L667             or Cob-Crt-Status = Cob-Scr-F4
    L668                call   "irs030" using IRS-System-Params
    L669                                      WS-System-Record   *> ACAS system rec.
    L670                                      file-defs
    L671                end-call
    L672                go to main-loop.

THREE PARAMETERS. NO `WS-CALLING-DATA`. NO `to-day`.
The callee's own header agrees, and it is the whole of its
`PROCEDURE DIVISION USING` list [irs/irs030.cbl:L552-L554]::

    L552  procedure division using IRS-System-Params
    L553                           WS-System-Record
    L554                           File-Defs.

`irs030` contains ZERO occurrences of `ws-calling-data`, of `wscall` and of
`to-day`, so the absence is measured rather than assumed. This entry point
therefore publishes no `--ws-caller`, `--ws-called`, `--ws-del-link`,
`--ws-process-func`, `--ws-sub-function`, `--ws-cd-args` and no `--term-code`
option: there is no such field on this route to bind them to.

THE THREE LINKAGE SHAPES, SIDE BY SIDE
Agent Action Plan section 0.1.1: the CLI contract "is already written, in the
LINKAGE SECTIONs", and there are exactly three shapes - "three argument shapes,
not one".

    Shape 1  General Ledger    FOUR parameters
             ws-calling-data, system-record, to-day, file-defs
             [general/gl070.cbl:L245-L248]
    Shape 2  Sales / Purchase  FIVE parameters
             ws-calling-data, system-record, system-record-4, to-day, file-defs
             [sales/sl060.cbl:L395-L399]
    Shape 3  IRS               THREE parameters      <- THIS MODULE
             IRS-System-Params, WS-System-Record, File-Defs
             [irs/irs030.cbl:L552-L554]

`acas_posting.cli.args.IrsLinkage` is the carrier for Shape 3 and holds the
three members in that exact COBOL order, so a reviewer can diff the argument
list of `main_loop_option_4` against L668-L670 line for line.

THERE IS NO TERM-CODE GATE ON THIS ROUTE - AND THAT IS REPRODUCED, NOT LOST
The IRS menu has none of the General, Sales and Purchase dispatch machinery: no
`load00`-style wrapper paragraph, no `move zero to ws-term-code` before the
call, no test of a code after it, and no `overrewrite` persistence of the system
records afterwards. L672 is a bare `go to main-loop.` - the menu simply loops.
Across the four ledgers there are FOUR DIFFERENT gate behaviours, and Agent
Action Plan section 0.7.4 C-3 makes harmonising them a failure rather than a
tidy-up:

    General Ledger   `if ws-term-code = 5` / `go to display-menu.` - so gl071
                     and gl072 NEVER RUN         [general/general.cbl:L810-L811]
    Sales            `if ws-term-code not = zero` / `go to display-menu.`,
                     TWICE on the invoice chain      [sales/sales.cbl:L761-L762]
                     and [sales/sales.cbl:L765-L766], inside `load07.` L756
    Purchase         NO gate. `load08.` L752 has the same two lines the Sales
                     chain has, but COMMENTED OUT by the maintainer
                                              [purchase/purchase.cbl:L757-L758]
    IRS              no gate, and no dispatch wrapper either
                                                      [irs/irs.cbl:L666-L672]

So `main_loop_option_4` contains no comparison, no abort and no early return.
Anyone comparing this module with `gl_post_cycle.py` and finding no gate here
is looking at a faithful reproduction (rule R-4), not at an omission.

THE MIGRATION BOUNDARY - 165 LINES OF A 1,733-LINE FILE
Agent Action Plan section 0.2.1.1 marks `irs/irs030.cbl` PARTIAL: only
`Ledger-Postings-Add` [irs/irs030.cbl:L1569-L1733] is migrated, plus the two
`ROUNDED` VAT computes of `Net` [irs/irs030.cbl:L1544] and `Gross`
[irs/irs030.cbl:L1556] that the posting path consumes. Everything else in that
file - the screen sections, `Init-Main` at L557, `Input-Headings` at L1239,
`Date-Validate` at L1285, `Initialise-Main` at L1402, `Show-Default` at L1504,
`file-init` at L1518 and every amendment dialog - is out of scope. Section
0.8.7 warns why the boundary is stated rather than inferred: "an agent working
from the file rather than from the stated boundary would migrate several
hundred lines that must not be migrated." That boundary belongs to
`acas_posting.programs.irs030_posting`; this module's whole job is to bind
three records and one boolean and to make one call.

*** THE DEFAULT ANSWER TRUNCATES A TABLE - READ THIS BEFORE RUNNING ***
`--clear-posting-file` DEFAULTS TO ON, and on means DELETE EVERY ROW of the IRS
transfer table `PSIRSPOST-REC`. The default is not a choice made here; it is
the COBOL's own. `EOJ-q1.` displays the question with `[Y]` pre-filled
[irs/irs030.cbl:L1716] and re-prompts on any reply that is neither `Y` nor `N`
[irs/irs030.cbl:L1718-L1719], so a bare Enter answers `Y`, and `Y` performs
`acas008-Open-Output` [irs/irs030.cbl:L1723] followed by `acas008-Close`
[irs/irs030.cbl:L1724]. For that handler an open-for-output is not a file
operation at all - it is a mass delete: `if fn-Open and fn-output and not
FS-Cobol-Files-Used / set fn-delete-all to true / perform ba-Process-RDBMS`
[common/acas008.cbl:L313-L319], reinforced at [common/acas008.cbl:L571-L574].
The handler's own inline comment at [irs/irs030.cbl:L1723] says so: "performs a
acas008-Delete-All". Agent Action Plan section 0.3.4 is explicit that this makes
the answer a genuine input rather than decoration, because "the answer changes
table state". Pass `--no-clear-posting-file` to answer `N` and leave the
transfer table populated.

    Entity   SPL-Posting        Handler  acas008
    Bridge   slpostingMT        Table    PSIRSPOST-REC
    Record   copybooks/wspost-irs.cob

THE TWO RUN-DATE OBSERVABLES, AND WHY `--run-date` IS STILL REQUIRED
"Shape 3 takes no run date" is true of the PARAMETER LIST and false of the
DATA. Two run-date fields reach `irs030`, in two formats, inside two different
records:

    WS-System-Record.Run-Date   `binary-long`   [copybooks/wssystem.cob:L67]
        The binary day count, inside linkage parameter 2 - the ordinary ACAS
        system record, as the maintainer's own comment at the call site says:
        `*> ACAS system rec.` [irs/irs.cbl:L669]. Unambiguously present, and it
        is a column of a compared table, so pinning it is NOT optional: Agent
        Action Plan section 0.8.5 requires that "two runs of the same scenario
        under the same pinned clock produce byte-identical dumps."
    IRS-System-Params.run-date  `pic x(8)`      [copybooks/irswssystem.cob:L14]
        The eight-character `dd/mm/yy` text, inside linkage parameter 1 - a
        DIFFERENT and much smaller record, `copybooks/irswssystem.cob`'s own
        `01 system-record.` [copybooks/irswssystem.cob:L13] renamed by the
        `COPY ... REPLACING` at [irs/irs.cbl:L392]. See Q-CLI-IRS-RUNDATE.

`--run-date` is therefore required, exactly as on the other two shapes, and it
is not "an argument the COBOL never passes": the COBOL passes it inside
parameters 1 and 2. It is consumed for one purpose only - pinning the clock -
and `acas_posting.cli.args` is the single authority that turns it into both
fields. This module derives nothing from it and overrides nothing in it.

A third date exists and is NOT this one. The date written into each posting row
comes from the transfer data, not from the linkage: `move WS-IRS-Post-Date to
post-date` [irs/irs030.cbl:L1662]. No CLI option injects a posting date.

WHAT THIS MODULE DELIBERATELY DOES NOT DO
It reads no clock, no environment variable, no file and no database. It performs
no validation of any kind - a run date the legacy `maps04` rejects yields
`Run-Date` 0 and no exception [common/maps04.cbl:L146], [common/maps04.cbl:L154]
with the caller pre-zero at [copybooks/Proc-ACAS-Mapser-RDB.cob:L78], which is
anomaly 16 of the register, reproduced rather than corrected. It contains no
error handling: the per-handler error checks of
[copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob], including the hard return on an
unrecoverable open failure at [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:
L355-L364], belong to the data-access facade. And it prints nothing - the two
screen statements this route would otherwise carry, the count display at
[irs/irs030.cbl:L1714] and the acknowledgement pause at
[irs/irs030.cbl:L1725-L1727], are presentation with no database effect and are
dropped under Agent Action Plan section 0.3.4.

IMPORTS, AND WHY THE LIST IS THIS SHORT
Agent Action Plan section 0.4.3's per-directory import table allows `cli/*.py`
to reach `programs`, `clock` and `cli.args`, and bars it from `dal.acas*`. This
module reaches `cli.args` and `programs.irs030_posting` and nothing else in the
package: the record dataclasses are `args`' business, the clock is reached
through `args.bind_irs_linkage`, and the three linkage records travel as one
`args.IrsLinkage` so that no record module has to be named here. There is no
COBOL at runtime and no path from here to `harness/` (rule R-1); the harness
drives this module from the outside, and the dependency runs one way only.

Importing this module does no work: it builds no parser, configures no logging,
opens no connection and touches no filesystem.
"""

from __future__ import annotations

import argparse
import logging
from collections.abc import Sequence
from typing import Final

#  The permitted internal edges, and both are used.
#
#  `args`                  Agent Action Plan section 0.4.1.1 gives it the whole
#                          binding mandate; it is the SINGLE authority for the
#                          three linkage records and for the pinned clock.
#  `irs030_posting`        imported AS A MODULE, never `from ... import run`.
#                          Agent Action Plan section 0.3.3: "Callers cannot
#                          reach into a program's internals, exactly as a COBOL
#                          `CALL` cannot." `programs/__init__.py` publishes no
#                          dispatch table and no re-export, so the module IS
#                          the call target - `irs030_posting.run(...)` reads as
#                          `call "irs030"` does.
from acas_posting.cli import args
from acas_posting.programs import irs030_posting

__all__: Final[tuple[str, ...]] = ("main", "main_loop_option_4")

_LOG: Final[logging.Logger] = logging.getLogger(__name__)

#  The `CALL` literal at [irs/irs.cbl:L668]. Recorded as a constant because it
#  is the program-id the traceability document maps to this route, and because
#  it is what the diagnostic records name. It is NOT moved into a `WS-Called`
#  field: Shape 3 has no calling-data block to hold one, and irs/irs.cbl names
#  its callee as a `CALL` literal rather than through the field.
_PROGRAM_ID: Final[str] = "irs030"

#  R-4 REPRODUCTION - THE DESTRUCTIVE DEFAULT, and the ONE place this module
#  states it. `EOJ-q1.` [irs/irs030.cbl:L1715] displays the question with `[Y]`
#  pre-filled [irs/irs030.cbl:L1716] into an `UPPER` update field
#  [irs/irs030.cbl:L1717] and loops back on any reply that is neither `Y` nor
#  `N` [irs/irs030.cbl:L1718-L1719], so a bare Enter answers `Y` and the COBOL
#  default is TO CLEAR. `Y` reaches `acas008-Open-Output`
#  [irs/irs030.cbl:L1723], which for this handler deletes every row of
#  `PSIRSPOST-REC` [common/acas008.cbl:L313-L319], [common/acas008.cbl:
#  L571-L574]. Preserved as `True` because the migration reproduces the
#  original's default rather than the safer one (rule R-4).
#
#  AMBIGUITY Q-CLI-CLEARFILE: irs/irs030.cbl:L1716 displays "[Y]" and
#  L1718-L1719 re-prompts on any reply other than Y or N, so the accept's update
#  pre-fill is what makes Y the effective default; confirm against the compiled
#  oracle that a bare Enter clears PSIRSPOST-REC; record in
#  docs/migration/ambiguity-resolutions.md.
_CLEAR_POSTING_FILE_DEFAULT: Final[bool] = True

#  The switch pair, spelled once. `argparse.BooleanOptionalAction` publishes
#  BOTH `--clear-posting-file` and `--no-clear-posting-file` from this single
#  declaration, so the operator can pin either answer for a scenario and
#  neither spelling can drift from the other.
_CLEAR_POSTING_FILE_OPTION: Final[str] = "--clear-posting-file"

#  The diagnostic format, and it carries NO TIMESTAMP on purpose. A log line is
#  presentation - Agent Action Plan section 0.3.4 requires that it "must not
#  alter control flow and must not appear in any table dump" - and omitting the
#  clock-derived field keeps even the transcript of two identical runs identical,
#  which is the cheapest possible reinforcement of rule R-6. Nothing in this
#  module reads a clock; this format could not, either.
_LOG_FORMAT: Final[str] = "%(levelname)s %(name)s %(message)s"

#  The `--help` prose, pre-wrapped so that no COBOL locator is split across
#  lines by a re-flow. See `_build_parser` for why the raw formatter is used.
_DESCRIPTION: Final[str] = (
    "Post the SL/PL transfer file to the IRS nominal ledger.\n"
    "\n"
    "Reproduces irs030's Ledger-Postings-Add section\n"
    "[irs/irs030.cbl:L1569-L1733], reached in the frozen system through the\n"
    'option "4" branch of irs/irs.cbl Main-Loop. [irs/irs.cbl:L666-L672].\n'
    "\n"
    "This is the THIRD of the migration's three linkage shapes: three\n"
    "parameters - IRS-System-Params, WS-System-Record, File-Defs\n"
    "[irs/irs030.cbl:L552-L554] - with no WS-Calling-Data and no to-day. So\n"
    "this route offers no calling-data options and has no term-code gate,\n"
    "unlike the General Ledger route's hard `ws-term-code = 5` gate\n"
    "[general/general.cbl:L810-L811]. That difference is reproduced, not\n"
    "harmonised."
)

_EPILOG: Final[str] = (
    "*** WARNING - THE DEFAULT DELETES DATA. ***\n"
    "\n"
    "Clearing the transfer file is ON by default because that is the COBOL\n"
    "default: the end-of-job question is displayed with [Y] pre-filled\n"
    "[irs/irs030.cbl:L1716], and answering Y deletes EVERY ROW of\n"
    "PSIRSPOST-REC [irs/irs030.cbl:L1720-L1724] through\n"
    "[common/acas008.cbl:L313-L319]. Pass --no-clear-posting-file to answer N\n"
    "instead.\n"
    "\n"
    "The database connection is NOT configured here. It comes from the six\n"
    "ACAS_DB_* variables of the deployment contract, which are the\n"
    "container-native transport of the six acas.param keywords the frozen\n"
    "common/acas-get-params.cbl reads; harness/docker-compose.yml sets all six\n"
    "for the gnucobol service. No password is ever taken from a command line."
)


def _build_parser() -> argparse.ArgumentParser:
    """Build the parser for Shape 3: `--run-date`, and the one promoted answer.

    Two contributions and no third. `args.add_irs_linkage_arguments` supplies
    everything the LINKAGE SECTION implies, which on this shape is the single
    required `--run-date`; this function then adds the one `ACCEPT` that gates a
    database write. Deliberately NOT composed:

      * `args.add_calling_data_arguments` - Shape 3 has no calling-data block
        [irs/irs030.cbl:L552-L554], so there is no `WS-Caller`, no
        `WS-Del-Link`, no `WS-Process-Func`, no `WS-Sub-Function`, no
        `WS-CD-Args` and no `WS-Term-Code` to bind;
      * `args.add_gl_linkage_arguments` and `args.add_slpl_linkage_arguments` -
        those build Shapes 1 and 2, which this route is not;
      * `--irs-instead`, the fan-out switch [copybooks/wssystem.cob:L179-L181].
        It selects whether the SALES and PURCHASE programs also post to IRS and
        is read at three sites in each of those four programs; `irs030` never
        reads it, because `irs030` IS the IRS posting program. Offering it here
        would imply a control this route does not have.

    WHY THE CLEAR-TRANSFER-FILE SWITCH IS DECLARED HERE AND NOT IN `args`.
    `acas_posting/cli/args.py` records the division in its own footer: the five
    promoted callee parameters - gl080's run-confirm, disk-change and
    archive-path, gl051's control-total inputs, sl100's post-confirm, pl100's
    run-confirm and irs030's clear-transfer-file decision - are each "an
    `ACCEPT` that gates a database write" and each "becomes an option on its OWN
    entry point, because each belongs to one route only. None is a linkage
    parameter and none is bound here." This is that option, declared exactly
    once, on the only route that has it.

    Returns:
        The parser. Built fresh per call, so nothing is constructed at import
        time and two callers cannot share mutable parser state.
    """
    parser = argparse.ArgumentParser(
        prog="python -m acas_posting.cli.irs_post",
        description=_DESCRIPTION,
        epilog=_EPILOG,
        #  The description and the epilog are PRE-WRAPPED above, with their line
        #  breaks chosen so that the destructive-default warning reads as a block
        #  and each COBOL locator stays on one line. argparse's default formatter
        #  would re-flow both and scatter the locators; this one does not, and it
        #  still wraps each option's own help text normally.
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    #  Shape 3's linkage options: the required `--run-date`, and nothing else.
    #  `args` owns the option's spelling, its `required=True` and its help text,
    #  so the three routes cannot disagree about what a run date is.
    args.add_irs_linkage_arguments(parser)

    #  The one promoted `ACCEPT` [irs/irs030.cbl:L1715-L1724].
    parser.add_argument(
        _CLEAR_POSTING_FILE_OPTION,
        action=argparse.BooleanOptionalAction,
        default=_CLEAR_POSTING_FILE_DEFAULT,
        help=(
            "Answer irs030's end-of-job question 'Can I clear the Ledgers "
            "Posting file? [Y]' (irs/irs030.cbl:L1716). *** DESTRUCTIVE, AND ON "
            "BY DEFAULT. *** Answering yes performs acas008-Open-Output "
            "(irs/irs030.cbl:L1723), which for this handler is not a file open "
            "but a mass delete - it sets fn-delete-all and calls the DAL "
            "(common/acas008.cbl:L313-L319, reinforced at L571-L574) - so EVERY "
            "ROW of the IRS transfer table PSIRSPOST-REC (entity SPL-Posting, "
            "bridge slpostingMT, record copybooks/wspost-irs.cob) is deleted. "
            "The default is the COBOL's own, not a choice made by the "
            "migration: the prompt pre-fills [Y] and re-prompts on any reply "
            "that is neither Y nor N (irs/irs030.cbl:L1718-L1719), so a bare "
            "Enter clears the file. Use --no-clear-posting-file to answer N and "
            "leave the transfer table populated. Pin this explicitly in every "
            "scenario: it decides whether one of the compared tables ends the "
            "run empty. (default: clear)"
        ),
    )

    return parser


def main_loop_option_4(
    linkage: args.IrsLinkage, *, clear_posting_file: bool
) -> None:
    """`Main-Loop.` option `"4"` - the whole dispatch, reproduced.

    Named after the paragraph it reproduces, as rule R-5 requires: irs/irs.cbl
    `Main-Loop.` [irs/irs.cbl:L637], option `"4"` branch
    [irs/irs.cbl:L666-L672]. That branch is four statements long and this
    function is its Python counterpart statement for statement.

    L666-L667 - THE MENU TEST, NOT REPRODUCED. `if Menu-Reply = "4" or
    Cob-Crt-Status = Cob-Scr-F4` selects the option from a keystroke or a
    function key. It is screen input with no database effect, dropped under
    Agent Action Plan section 0.3.4; invoking this entry point IS the selection.

    L668-L671 - THE `CALL`, REPRODUCED EXACTLY. Three positional arguments in
    the frozen parameter order, and nothing else positional. `args.IrsLinkage`
    holds them in that order, and they are spelled out by name here rather than
    unpacked with a star, so the argument list diffs against L668-L670 term for
    term.

    L672 - `go to main-loop.` The menu loops back to redraw and accept again.

    Args:
        linkage: the three bound linkage records, in COBOL parameter order
            [irs/irs.cbl:L668-L671] - `IRS-System-Params`
            [copybooks/irswssystem.cob:L13], `WS-System-Record`
            [copybooks/wssystem.cob], `File-Defs` [copybooks/wsnames.cob:L13].
            Build it with `args.bind_irs_linkage`; nothing here constructs or
            modifies a record. Note that the callee MUTATES the first of the
            three - the posting-key allocator `next-post` advances once per
            posting written [irs/irs030.cbl:L1670-L1671] - exactly as COBOL
            writes into the caller's own storage.
        clear_posting_file: the answer to the end-of-job question
            [irs/irs030.cbl:L1715-L1724]. KEYWORD-ONLY and REQUIRED, with no
            default of its own on purpose: the COBOL default lives at exactly
            one place in this module, `_CLEAR_POSTING_FILE_DEFAULT`, which is
            the argparse default, and a second default here could drift from it
            silently. `True` DELETES EVERY ROW of `PSIRSPOST-REC`
            [common/acas008.cbl:L313-L319].

    Returns:
        Nothing. `irs030` communicates entirely through the database, through
        its `File-Access` status block and through the advanced key allocator on
        `IRS-System-Params`; every disposition it has - clean skip,
        commit-and-stop, abort-with-nothing - is a normal return in the frozen
        program too, which raises no condition and signals no failure to the
        menu.
    """
    #  R-4 REPRODUCTION - NO GATE, AND NO DISPATCH WRAPPER
    #  [irs/irs.cbl:L666-L672]. The IRS route has neither of the two things the
    #  other ledgers' routes have around this call. There is no
    #  `move zero to ws-term-code` before it and no `if ws-term-code ...` after
    #  it, because Shape 3 carries no `WS-Term-Code` at all
    #  [irs/irs030.cbl:L552-L554]; and there is no `load00`-style paragraph that
    #  centralises the CALL, because irs/irs.cbl writes the CALL inline in the
    #  menu branch. Compare `gl_post_cycle`, where `if ws-term-code = 5` /
    #  `go to display-menu.` [general/general.cbl:L810-L811] is a HARD gate that
    #  stops gl071 and gl072 from running at all. Four ledgers, four gate
    #  behaviours - General `= 5` [general/general.cbl:L810-L811], Sales
    #  `not = zero` twice [sales/sales.cbl:L761-L762],
    #  [sales/sales.cbl:L765-L766], Purchase none because the maintainer
    #  commented its pair out [purchase/purchase.cbl:L757-L758], and IRS
    #  none-and-no-wrapper - and Agent Action Plan section 0.7.4 C-3 makes
    #  harmonising them a behaviour change and therefore a failure. Nothing is
    #  missing here.
    #
    #  There is likewise no `overrewrite` of the system records after the call.
    #  irs/irs.cbl does not perform one on this branch, and the persistence the
    #  other menus do perform is out of scope (Agent Action Plan section 0.2.2).
    _LOG.info(
        "call %s using IRS-System-Params, WS-System-Record, File-Defs "
        "[irs/irs.cbl:L668-L671]; clear_posting_file=%s",
        _PROGRAM_ID,
        clear_posting_file,
    )

    #  [irs/irs.cbl:L668-L670]  call "irs030" using IRS-System-Params
    #                                              WS-System-Record
    #                                              file-defs
    #  THREE positional arguments, in that order, and no fourth. In particular
    #  no `to_day`: `irs030` has no such parameter, and adding one "for
    #  consistency" with Shapes 1 and 2 would misstate its contract.
    #
    #  `clear_posting_file` is passed EXPLICITLY and always, never left to the
    #  callee's own default, so the two defaults cannot silently diverge.
    #
    #  The callee's remaining keyword-only parameters, `file_access` and
    #  `dal_common`, are deliberately not passed - see OMISSIONS in the footer.
    irs030_posting.run(
        linkage.irs_system_params,
        linkage.ws_system_record,
        linkage.file_defs,
        clear_posting_file=clear_posting_file,
    )

    #  GO TO class 1 (loop-back): irs/irs.cbl:L672 "go to main-loop" - the menu
    #  loops; a single CLI invocation is one iteration.
    return


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point: bind Shape 3, dispatch `irs030`, report a status.

    Four steps and no fifth: configure diagnostics, parse, bind, dispatch.

    Args:
        argv: the argument vector WITHOUT the program name, as
            `argparse.ArgumentParser.parse_args` takes it. `None` - the normal
            case - reads `sys.argv[1:]` inside argparse, so this module never
            touches `sys.argv` itself.

    Returns:
        `0`. See the Q-CLI-EXITSTATUS note at the return statement.

    Raises:
        SystemExit: from argparse, for `--help` (status 0) and for a usage error
            such as an omitted `--run-date` (status 2). Not caught: a required
            argument that has no defensible default must fail loudly rather than
            be invented, which is what keeps an ambient run date out of the
            cycle (rule R-6).
        acas_posting.cli.rdbms_params.RdbmsParamError: the deployment contract
            for the database connection is absent or unusable. Propagated
            deliberately, on the binder's own documented terms - a run that
            cannot connect to the provisioned database must stop before it
            writes anything, because the alternative is a silent connection to
            the placeholder endpoint [copybooks/wssystem.cob:L137-L144]. No
            handler is added here: this module contains no error handling at
            all, by design.
    """
    #  Diagnostics only, and configured here rather than at import so that
    #  importing this module has no side effect whatsoever - `tests/scenarios/*`
    #  import the package. `basicConfig` is a no-op when the root logger already
    #  has handlers, so a host application's own configuration wins.
    logging.basicConfig(level=logging.INFO, format=_LOG_FORMAT)

    parser = _build_parser()
    namespace = parser.parse_args(argv)

    #  THE ONE AND ONLY BINDING, AND THE ONE AND ONLY CLOCK INJECTION.
    #  `bind_irs_linkage` resolves the pinned pair from `--run-date` through
    #  `acas_posting.clock`, writes the binary `Run-Date`
    #  [copybooks/wssystem.cob:L67] into `WS-System-Record` and the
    #  eight-character `dd/mm/yy` form [copybooks/irswssystem.cob:L14] into
    #  `IRS-System-Params`, and fills the six RDBMS connection fields that are
    #  `SYSTEM-REC`'s only carrier to the data-access layer
    #  [common/acas008.cbl:L558-L563].
    #
    #  IT IS THE SINGLE AUTHORITY FOR BOTH DATE FIELDS. This module does not
    #  re-derive, override or second-guess either one: it does not call
    #  `args.resolve_clock`, `args.irs_run_date_x8` or `acas_posting.clock`, and
    #  it assigns nothing to a record. Every other `cli/*` entry point reuses
    #  `args.py` the same way, and none redefines the binding.
    #
    #  AMBIGUITY Q-CLI-IRS-RUNDATE: irs/irs.cbl:L972-L978 derives
    #  IRS-System-Params.run-date pic x(8) from the binary run date, but zz090 is
    #  performed only on the option "1" branch (L651), and L636 comments "menu
    #  uses the irs param file dates"; on the option "4" route the value
    #  therefore comes from the seeded IRS parameter record.
    #  WS-System-Record.Run-Date (copybooks/wssystem.cob:L67) is pinned
    #  unambiguously. Arbitrate the x(8) field against the compiled oracle;
    #  record in docs/migration/ambiguity-resolutions.md.
    linkage = args.bind_irs_linkage(namespace)

    #  Determinism evidence, read back off the bound records rather than
    #  re-derived, so the transcript reports what was actually bound. Both
    #  values come from `--run-date` alone; nothing ambient can move them.
    _LOG.info(
        "pinned run date: WS-System-Record.Run-Date=%d "
        "[copybooks/wssystem.cob:L67], IRS-System-Params.run-date=%r "
        "[copybooks/irswssystem.cob:L14]",
        linkage.ws_system_record.system_data_block.run_date,
        linkage.irs_system_params.run_date,
    )

    main_loop_option_4(
        linkage, clear_posting_file=namespace.clear_posting_file
    )

    #  AMBIGUITY Q-CLI-EXITSTATUS: the IRS linkage shape carries no WS-Term-Code
    #  (irs/irs030.cbl:L552-L554), so the process exit status has no COBOL
    #  counterpart on this route; 0 on completion is a migration convention, not
    #  reproduced behaviour. Arbitrate against the compiled oracle; record in
    #  docs/migration/ambiguity-resolutions.md.
    #
    #  For the record, and so that this marker is not read as contradicting its
    #  sibling in `args.py`: `args.exit_status_for` settles the GENERAL question
    #  by establishing that there is no oracle observable to arbitrate against -
    #  `RETURN-CODE`, the one register GnuCOBOL surfaces as a process status, is
    #  READ and never WRITTEN in any of the five menus or the twelve posting
    #  programs, and each menu ends with a bare `goback`. On THIS route the
    #  question is narrower still, because there is no `WS-Term-Code` to map: the
    #  identity mapping has no input, so `exit_status_for` is deliberately NOT
    #  called and there is nothing to encode but completion.
    return 0


if __name__ == "__main__":
    #  `harness/run_python_scenario.sh` invokes these modules directly, as
    #  `python -m acas_posting.cli.irs_post`, and `pyproject.toml` declares no
    #  `[project.scripts]`. `raise SystemExit(...)` rather than `sys.exit(...)`
    #  keeps `sys` out of the import list.
    raise SystemExit(main())



# --- traceability ------------------------------------------------------------
#
# FUNCTION -> PARAGRAPH  (rule R-5)
#   main_loop_option_4  <-  irs/irs.cbl  `Main-Loop.`  L637, option "4" branch
#                           L666-L672. The branch in full: the menu test at
#                           L666-L667 (dropped, screen input), the three-operand
#                           `CALL` at L668-L670 with `end-call` at L671
#                           (reproduced exactly), and `go to main-loop.` at L672.
#   main                <-  no paragraph. The CLI boundary itself: argparse
#                           replaces the menu's screen paint and `ACCEPT`
#                           (irs/irs.cbl L638-L644), which have no database
#                           effect and are excluded by Agent Action Plan
#                           section 0.3.4.
#   _build_parser       <-  no paragraph. Composes `args.add_irs_linkage_
#                           arguments` (Shape 3's linkage options) and declares
#                           the one promoted `ACCEPT` of
#                           irs/irs030.cbl `EOJ-q1.` L1715-L1724.
#
# PROGRAM -> MODULE  (rule R-5)
#   irs030  ->  acas_posting/programs/irs030_posting.py
#               linkage       irs/irs030.cbl:L552-L554
#                             (IRS-System-Params, WS-System-Record, File-Defs)
#               in scope      `Ledger-Postings-Add section.`
#                             irs/irs030.cbl:L1569-L1733, plus the two ROUNDED
#                             VAT computes of `Net section.` L1544 (compute at
#                             L1551) and `Gross section.` L1556 (compute at
#                             L1562) that the posting path consumes
#               out of scope  everything else in the 1,733-line file
#                             (Agent Action Plan section 0.2.1.1)
#
# PROMOTED PARAMETER -> LOCATOR  (Agent Action Plan section 0.3.4)
#   clear_posting_file  <-  irs/irs030.cbl `EOJ-q1.` L1715-L1727
#     L1716  the question, displayed with the literal `[Y]`   <- THE DEFAULT
#     L1717  `accept WS-Reply at 1440 ... UPPER`              <- the update field
#     L1718-L1719  re-prompt unless the reply is Y or N       <- GO TO class 1
#     L1720  `if WS-Reply = "Y"`
#     L1723  `perform acas008-Open-Output`  *> the comment on this very line
#            reads "performs a acas008-Delete-All"
#     L1724  `perform acas008-Close.`
#     L1725-L1727  the acknowledgement pause                  <- DROPPED
#     effect via common/acas008.cbl:L313-L319 (fn-Open + fn-output + not
#     FS-Cobol-Files-Used -> set fn-delete-all -> perform ba-Process-RDBMS) and
#     common/acas008.cbl:L571-L574 (`ba015-Test-Ends.` forcing the same),
#     so the answer DELETES EVERY ROW of PSIRSPOST-REC.
#     Default `True` [_CLEAR_POSTING_FILE_DEFAULT], preserving the COBOL's own.
#
# RECORD IDENTITIES  -  the three linkage parameters, in COBOL order
#   1  IRS-System-Params  =  copybooks/irswssystem.cob `01 system-record.` L13,
#      renamed by `copy "irswssystem.cob" replacing system-record by
#      IRS-System-Params.` at irs/irs.cbl:L391-L392. `03 run-date pic x(8).` at
#      copybooks/irswssystem.cob:L14 - TEXT, dd/mm/yy, NOT the binary field.
#      NOT copybooks/wssystem.cob: a different and much smaller record (256
#      bytes per its own header note at copybooks/irswssystem.cob:L10), so
#      binding the ACAS system record into parameter 1 would be wrong in both
#      layout and width. Modelled by acas_posting/records/irs_system.py.
#      Its `03 system-ops pic x.` at copybooks/irswssystem.cob:L23 carries one
#      extra space of indentation relative to its siblings - a cosmetic
#      irregularity of the frozen source, noted and not corrected.
#   2  WS-System-Record   =  copybooks/wssystem.cob, the 169-column ACAS system
#      record, as the maintainer's own comment `*> ACAS system rec.` at the call
#      site says (irs/irs.cbl:L669). `05 Run-Date binary-long.` at
#      copybooks/wssystem.cob:L67 - the binary day count, and a column of a
#      compared table. Also the sole carrier of the six RDBMS connection fields
#      (copybooks/wssystem.cob:L137-L144) to the data-access layer
#      (common/acas008.cbl:L558-L563).
#   3  File-Defs         =  copybooks/wsnames.cob `01 File-Defs.` L13. Entirely
#      `VALUE`-initialised in the copybook, so its declared defaults already are
#      the COBOL state and it needs no CLI option.
#
# `GO TO` CLASSES  (Agent Action Plan section 0.4.2 taxonomy)
#   irs/irs.cbl:L672        `go to main-loop.`  -  Class 1 (loop-back).
#     Annotated at the end of `main_loop_option_4`. One CLI invocation is one
#     iteration of the menu loop; the loop itself is screen-driven and dropped.
#   irs/irs030.cbl:L1718-L1719  `go to EOJ-q1.`  -  Class 1 (loop-back),
#     DROPPED. It re-prompts after an unrecognised reply, so its only effect is
#     to block a terminal; it has no database effect and no control transfer to
#     preserve (Agent Action Plan section 0.3.4). The DECISION it guards is
#     preserved, as `clear_posting_file`.
#   No Class 2, 3 or 4 site exists on this route.
#
# CORRECTIONS  -  each verified against the frozen source with a line read. DO
# NOT "fix" these back to the values the planning documents carry.
#
#   1. irs/irs.cbl's dispatching paragraph is `Main-Loop.` at L637, with the
#      option "4" `CALL` inline at L666-L672. There is NO `load00` / `load000`
#      equivalent anywhere on the IRS side: irs/irs.cbl has no dispatch wrapper
#      paragraph at all, and `procedure division.` at L470 takes no `USING`, so
#      irs/irs.cbl is a MAIN program while all twelve migrated programs are
#      `CALL`ed sub-programs.
#
#   2. The Sales / Purchase linkage shape has FIVE parameters, not the four Agent
#      Action Plan section 0.4.1.1's phrasing implies. Section 0.1.1 and the
#      source agree on five: sales/sl060.cbl:L395-L399. `args.SlPlLinkage` has
#      five members.
#
#   3. `WS-CD-Args` is at copybooks/wscall.cob:L14, not the L13 Agent Action Plan
#      section 0.4.1.1 cites (L13 is `WS-Sub-Function`, and L11 is a comment line
#      between L10 and L12). Recorded for the folder's record only - Shape 3 has
#      no calling-data block, so the field is not used on this route at all.
#
#   4. Agent Action Plan section 0.1.1 calls
#      copybooks/Proc-ACAS-Mapser-RDB.cob:L72-L80 "the single read in the whole
#      call chain". A grep census finds THIRTEEN clock reads across six files -
#      common/ACAS.cbl L353, L470, L478; general/general.cbl L371, L551, L559;
#      sales/sales.cbl L323, L520, L528; purchase/purchase.cbl L318, L514, L522;
#      irs/irs.cbl L480 (this route's one, `move function current-date to
#      wse-date-block.`); and the copybook's own at L72. BUT every one of the
#      thirteen is in an out-of-scope MENU SHELL, and all twelve in-scope posting
#      programs contain zero, so the plan's CONCLUSION holds exactly: pinning the
#      two observables at the CLI boundary is sufficient.
#
#   5. The `acas008-Open-Output` perform is at irs/irs030.cbl:L1723, not the
#      L1722 the file brief cites: L1721-L1722 are the maintainer's commented-out
#      `open output irs-post-file` / `close irs-post-file` pair, kept above the
#      live `perform`. Every citation in this module uses L1723.
#
#   6. `acas_posting.programs.irs030_posting.run` takes TWO keyword-only
#      parameters beyond the three positional ones and `clear_posting_file`:
#      `file_access` and `dal_common`, both defaulting to `None`. The file brief
#      quotes the signature without them. The MODULE is followed, not the brief;
#      `clear_posting_file` does default to `True` there, as the brief says, and
#      this module passes it explicitly anyway. See OMISSIONS.
#
# OMISSIONS  -  recorded as omissions so that a reader comparing the two trees
# does not conclude something was lost (Agent Action Plan section 0.4.3).
#
#   * irs/irs.cbl'S ENTIRE MENU. The screen section and its paint (L638-L642),
#     the `accept Menu-Screen-1` (L643), the `Param-Restrict` erase (L641-L642),
#     and every option other than "4": "1" -> irs000 (L645-L652), "2" -> irs010
#     (L653-L658), "3" -> irs020 (L659-L665), "5" -> irs040 (L673-L679) and each
#     later option. NOT ROUTED. Agent Action Plan section 0.2.2 places irs000,
#     irs010, irs020 and irs070 out of scope as interactive programs and irs040,
#     irs050, irs060 and irs090 out of scope as report programs; only option "4"
#     reaches an in-scope program. `irs-main section.` L473 onwards - the
#     environment set-up at L478-L479, the terminal-size checks at L483-L486 and
#     the program-argument scan `zz020-Get-Program-Args` at L481 - is likewise
#     not reproduced.
#   * irs/irs.cbl `zz090-Proc-Run-Date.` L972-L978. The `dd/mm/yy` derivation is
#     reproduced ONCE, by `args.irs_run_date_x8`, and called ONCE, by
#     `args.bind_irs_linkage`. Never here: this module holds no date logic at
#     all. See Q-CLI-IRS-RUNDATE. Its siblings `zz090-Proc-Start-Date.` L980 and
#     the end-date paragraph that follows are equally not this module's business.
#   * irs/irs.cbl:L480, THE MENU'S SINGLE CLOCK READ
#     (`move function current-date to wse-date-block.`) and the binary-to-text
#     conversion it feeds at L632-L634. Replaced by the REQUIRED `--run-date`
#     argument, which is what makes two runs byte-identical (rule R-6, Agent
#     Action Plan section 0.8.5). This module reads no clock by any route.
#   * irs/irs030.cbl:L1713-L1714, the `display space` and the
#     `display "Processing Complete on " Post-Record-Cnt " records"` count
#     report; and irs/irs030.cbl:L1725-L1727, the "Note counts and any messages"
#     acknowledgement pause. Both are presentation with no database effect: the
#     count display is a diagnostic at most and the pause exists only to block a
#     terminal, so it is dropped entirely (Agent Action Plan section 0.3.4).
#     Neither may alter control flow and neither appears in any table dump.
#   * EVERYTHING IN irs/irs030.cbl OUTSIDE `Ledger-Postings-Add` L1569-L1733,
#     except the `Net` L1544 and `Gross` L1556 VAT computes the posting path
#     consumes. `Init-Main` L557, `Main-Loop.` L571, `Input-Headings` L1239,
#     `Date-Validate` L1285, `Initialise-Main` L1402, `Show-Default` L1504 and
#     `file-init` L1518 are all out of scope, and none of them is reachable from
#     this module.
#   * THE PER-HANDLER ERROR CHECKS OF copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob,
#     copied by irs030 at irs/irs030.cbl:L1732, including the hard return on an
#     unrecoverable open failure at
#     copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L355-L364. They belong to
#     `acas_posting/dal/facade.py`, which publishes both the entity-named and the
#     handler-named vocabularies over one implementation. This module adds NO
#     error handling of its own - not a try, not an except, not a retry.
#   * THE CALLEE'S `file_access` AND `dal_common` PARAMETERS. Both are `irs030`'s
#     own WORKING-STORAGE rather than linkage - `File-Access` at
#     irs/irs030.cbl:L285 and `ACAS-DAL-Common-data` at irs/irs030.cbl:L298 - and
#     the frozen program populates them in `Init-Main` / `file-init`, which are
#     out of scope. They are left at their `None` defaults, so the callee builds
#     fresh blocks. Two reasons, and either alone is sufficient: they are not
#     among the three parameters irs/irs.cbl:L668-L670 passes, so supplying them
#     from a CLI would invent an input (rule R-3); and constructing one would
#     require importing `acas_posting.records.*`, which Agent Action Plan section
#     0.4.3's import table bars `cli/*.py` from doing. The connection parameters
#     the handlers need do NOT travel that way in any case - they travel in
#     `WS-System-Record`, which this module does pass
#     (common/acas008.cbl:L558-L563).
#   * `args.reset_term_code`, `args.set_called`, `args.is_serious_error` and
#     `args.exit_status_for`. All four are helpers for the term-code protocol,
#     and Shape 3 has no `WS-Term-Code` (irs/irs030.cbl:L552-L554). Not called,
#     and calling any of them would imply a field this route has not got.
#   * THE MENUS' `overrewrite` PERSISTENCE of the system records. irs/irs.cbl
#     performs none on this branch - L672 is a bare `go to main-loop.` - and the
#     persistence the General, Sales and Purchase menus do perform is out of
#     scope (Agent Action Plan section 0.2.2). See Q-CLI-SYSREC-LOAD in
#     `args.py`, where the question is settled.
#
# ANOMALIES REPRODUCED DOWNSTREAM  -  listed for the reader, and compensated for
# by NOTHING here (rule R-4: "A defect reproduced is correct; a defect fixed is a
# failure"). This module adds no retry, no rollback, no validation and no warning
# for any of them, and passes no flag that would suppress one.
#   * THE HALF-POSTED DOUBLE ENTRY. The debit is rewritten before the credit
#     account is even looked up, so a missing credit account leaves a posted
#     debit with no balancing credit and no posting record
#     [irs/irs030.cbl:L1635-L1652]. Reproduced in
#     `programs/irs030_posting.py`. Anomaly 4 of the register.
#   * THE LOST UPDATE ON THE TWO VAT CONTROL ACCOUNTS. They are read into
#     pre-loop snapshots [irs/irs030.cbl:L1602], [irs/irs030.cbl:L1612] and
#     rewritten from those snapshots at end of job
#     [irs/irs030.cbl:L1704-L1708], so any in-loop rewrite of the same accounts
#     is silently discarded. Anomaly 5.
#   * THE WRITE-FAILURE JUMP TO END OF JOB. A failure writing the posting record
#     jumps straight to `EOJ` [irs/irs030.cbl:L1673-L1678], which still performs
#     the two snapshot rewrites and the closes - so the partial state is
#     committed, not rolled back. NOTE that this path still reaches `EOJ-q1.`,
#     which means `clear_posting_file` still applies after a write failure. That
#     is the frozen behaviour and it is preserved.
#   * THE ALWAYS-FAILING REWRITE VERB. The transfer-file handler rejects
#     read-indexed, rewrite, start and delete UNCONDITIONALLY at entry, with
#     WE-Error 988 and fs-reply 99 [common/acas008.cbl:L299-L307], because the
#     underlying file is sequential - yet the facade still publishes Rewrite, so
#     a caller invoking it always fails. Reproduced in
#     `dal/acas008_spl_posting.py`. Anomaly 6.
#   * THE BRIDGE-ONLY DERIVED DATE COLUMNS. `POST4-DAY`, `POST4-MONTH` and
#     `POST4-YEAR` exist in no copybook; the bridge derives them from a date
#     string under a guard, and when the guard fails they stay zero while the raw
#     date text is still stored [common/irspostingMT.cbl:L982-L987]. Reproduced
#     in `dal/acasirsub4_irs_posting.py`. Anomaly 7.
#   * ANOMALY 16, WHICH THIS MODULE IS ON THE PATH OF. `maps04` leaves its output
#     field untouched on a rejected date [common/maps04.cbl:L146],
#     [common/maps04.cbl:L154] and the documented "errors return zero" contract
#     holds only because callers pre-zero it
#     [copybooks/Proc-ACAS-Mapser-RDB.cob:L78]. So a `--run-date` the legacy
#     module rejects yields `Run-Date` 0 and NO exception. This module adds no
#     check and no message: validating would add a validation the COBOL has not
#     got (R-3) and correcting a defect is a failure (R-4).
#
# OUT-OF-SCOPE FINDING, RECORDED AND NOT ACTED ON  -  `File-System-Used`
# [copybooks/wssystem.cob:L112-L113]. Observed while validating this route with a
# real invocation: the record `args.bind_irs_linkage` hands over carries the
# copybook's own declared default of ZERO, which is the `88 FS-Cobol-Files-Used`
# condition, so a live run reaches the data-access layer's Cobol flat-file leg
# rather than its RDB leg. That layer's own docstring states the model it was
# written to - "unreachable in normal operation, because `FS-Cobol-Files-Used` is
# false for every migrated run" - so three AAP-created files hold three
# consistent-in-isolation positions and the boundary between them is not settled
# by any of them:
#     records/system_record.py  reproduces the copybook default 0 faithfully, and
#                               must: SYSTEM-REC is one of the 22 compared tables,
#                               so its declared default is diff-visible (R-4);
#     cli/args.py               builds the record at its declared defaults plus a
#                               list of nine fields it declares CLOSED, and
#                               settles Q-CLI-SYSREC-LOAD by recording that the
#                               seeded state and the scenario driver own the rest;
#     dal/*                     branches on the field and expects the RDB leg.
# NOT FIXED HERE, and every available fix inside this file's boundary would break
# a rule: this module may not import `acas_posting.records.*` (Agent Action Plan
# section 0.4.3's import table) nor construct or mutate a linkage record; adding a
# `--file-system-used` option would add a CLI input the frozen menus do not offer
# (R-3), which is the same ground on which args.py closed its own option list; and
# forcing the value silently would overwrite a declared default that is a column
# of a compared table (R-4). The field's value comes from the SYSTEM-REC row in
# the COBOL, so its owner is the seeded state and `harness/run_python_scenario.sh`
# - an Agent Action Plan file not yet written. The finding is package-wide, not
# specific to this route: all seven entry points bind through the same binder.
# Recorded here so that whoever writes the scenario driver meets it.
#
# AMBIGUITIES RAISED BY THIS MODULE  (rule R-6)  -  three, each marked in place
# at the code it governs, and each to be recorded in
# docs/migration/ambiguity-resolutions.md.
#   Q-CLI-IRS-RUNDATE  in `main`, at the `bind_irs_linkage` call. Whether irs030
#     observes `IRS-System-Params.run-date pic x(8)` at all, and if so what value
#     the option "4" route presents it with, given that
#     `zz090-Proc-Run-Date.` [irs/irs.cbl:L972-L978] is performed on the option
#     "1" branch [irs/irs.cbl:L651] and that [irs/irs.cbl:L636] comments "menu
#     uses the irs param file dates". STILL OPEN, and marked in `args.py` too,
#     where the single derivation lives. Nothing provisional executes: the
#     binder reproduces the frozen `STRING` either way.
#   Q-CLI-EXITSTATUS  in `main`, at the `return 0`. Shape 3 carries no
#     `WS-Term-Code`, so the process exit status has no COBOL counterpart on this
#     route at all. `args.exit_status_for` settles the general question by
#     establishing that there is no oracle observable - `RETURN-CODE` is read and
#     never written in the five menus and the twelve programs - and on this route
#     there is not even a code to map, so completion is all there is to report.
#   Q-CLI-CLEARFILE  at `_CLEAR_POSTING_FILE_DEFAULT`. That a bare Enter answers
#     `Y` follows from the `[Y]` literal [irs/irs030.cbl:L1716] together with the
#     re-prompt on any other reply [irs/irs030.cbl:L1718-L1719], which together
#     mean the accept's update pre-fill is the effective default. To be confirmed
#     against the compiled oracle by observing whether a bare Enter empties
#     PSIRSPOST-REC.
#
# RULES  -  there is NO user rules document for this project: `review_rules`
# returns "No user rules provided.", and a full paging read returns the same one
# line. These six are the Agent Action Plan's own, section 0.7.2, and enterprise-
# standard best practice applies wherever they are silent.
#   R-1  NO COBOL AT RUNTIME. Satisfied structurally. The whole import list is
#        `argparse`, `logging`, `collections.abc.Sequence`, `typing.Final`,
#        `acas_posting.cli.args` and `acas_posting.programs.irs030_posting`. No
#        `subprocess`, no `os.system` / `popen` / `exec*` / `spawn*`, no
#        `ctypes`, no `cffi`, no `shutil.which`, no `cobc` / `cobcrun` /
#        `presql2` / `cobmysqlapi`, and no import of `harness` - so there is no
#        import path from the shipped package to the comparison oracle. No
#        `--use-oracle`, `--compare`, `--cobol` or `--oracle` option exists. The
#        harness drives THIS module from the outside; the dependency runs one
#        way.
#   R-2  ZERO BINARY FLOATING POINT. Satisfied by type. The only values this
#        module handles are `bool` (`clear_posting_file`), `str` (`--run-date`
#        text and the program id) and `int` (the exit status and the binary
#        `Run-Date` it logs). No `float` appears in any signature, any
#        annotation, any option `type=` or any expression; there is no float
#        literal anywhere; and NO ARITHMETIC IS PERFORMED AT ALL. Checked
#        mechanically over the syntax tree, which contains exactly one `BinOp`
#        and zero `AugAssign`: that `BinOp` is `Sequence[str] | None`, the
#        `main` signature's PEP 604 type union, whose operator is `BitOr` on two
#        types rather than on two numbers. The two `ROUNDED` VAT computes of
#        [irs/irs030.cbl:L1551] and [irs/irs030.cbl:L1562], two of only five
#        `ROUNDED` sites in the whole in-scope cycle, live in
#        `programs/irs030_posting.py`.
#   R-3  NO NEW VALIDATIONS, FIELDS OR SCHEMA; NO CONCURRENCY. Satisfied by
#        omission. No validation of `--run-date` (see anomaly 16 above), no
#        validation of the linkage records, no field added to any record, no SQL
#        and no DDL. The option set is closed at two - the required `--run-date`
#        that `args` owns, and the one promoted `ACCEPT` of
#        [irs/irs030.cbl:L1715-L1724] - and no third option is offered, in
#        particular no `--irs-instead`, which `irs030` never reads. No
#        `threading`, `asyncio`, `multiprocessing` or `concurrent.futures`, and
#        no `--parallel` / `--jobs` / `--workers` / `--threads`: execution is
#        strictly sequential, matching the single-threaded COBOL. No web tier, no
#        API, no GUI, no ORM entity layer, no queue and no cache.
#   R-4  ANOMALIES REPRODUCED, NEVER FIXED. Three reproductions in this module,
#        each carrying its locator at the site, per Agent Action Plan section
#        0.7.4 C-4: the THREE-PARAMETER SHAPE with no calling-data block and no
#        `to-day` [irs/irs.cbl:L666-L672], [irs/irs030.cbl:L552-L554]; the
#        ABSENCE OF ANY TERM-CODE GATE OR DISPATCH WRAPPER on this route, left
#        absent rather than harmonised with the other three ledgers
#        [irs/irs.cbl:L672]; and the DESTRUCTIVE `[Y]` DEFAULT
#        [irs/irs030.cbl:L1716] whose effect is a mass delete
#        [irs/irs030.cbl:L1720-L1724], [common/acas008.cbl:L313-L319] - kept as
#        the default because the migration reproduces the original's default and
#        not the safer one. The five downstream anomalies above are listed and
#        compensated for by nothing.
#   R-5  FULL TRACEABILITY. This footer, the paragraph-named dispatch function
#        `main_loop_option_4`, a `# GO TO class N` annotation at every transfer
#        site, and a `[path:Lnnn]` locator on every claim about the frozen
#        source. Deliberate omissions are recorded as omissions above rather than
#        left silent.
#   R-6  COMPILED BEHAVIOUR IS THE TIE-BREAKER. The clock is pinned at this
#        boundary and nowhere else: `--run-date` is REQUIRED, has no default and
#        no fallback, and this module reads no clock, no environment variable, no
#        random source and no host identity - even the log format carries no
#        timestamp. Two runs of one scenario under the same `--run-date` bind
#        byte-identical records (Agent Action Plan section 0.8.5). The three open
#        questions above are marked for oracle arbitration, not guessed.
#
# MODULE -> COBOL SOURCE  (rule R-5)
#   acas_posting/cli/irs_post.py  <-  irs/irs.cbl (the option "4" dispatch),
#   irs/irs030.cbl (the callee's linkage and its one promoted `ACCEPT`),
#   common/acas008.cbl (what "clear" means), copybooks/irswssystem.cob,
#   copybooks/wssystem.cob and copybooks/wsnames.cob (the three record
#   identities). ALL SIX ARE REFERENCE ONLY - frozen, read as specification,
#   never modified. Agent Action Plan section 0.8.1: any diff touching
#   `common/*.cbl`, `common/*.scb`, `copybooks/*.cob`, `general/*.cbl`,
#   `sales/*.cbl`, `purchase/*.cbl`, `irs/*.cbl` or `mysql/ACASDB.sql` "is a
#   defect in the migration, regardless of how harmless it appears."
# -----------------------------------------------------------------------------
