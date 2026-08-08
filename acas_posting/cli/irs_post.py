"""IRS nominal-ledger posting - the third linkage shape, three parameters.

Reproduces the option `"4"` branch of `irs/irs.cbl` `Main-Loop.`, whose whole
body is one `CALL` [irs/irs.cbl:L666-L672], and dispatches irs030's
`Ledger-Postings-Add` section [irs/irs030.cbl:L1569-L1730] - 165 lines of a
1,733-line file, the rest of which is interactive and out of scope.

The linkage is three parameters: `IRS-System-Params`, `WS-System-Record`,
`File-Defs` [irs/irs030.cbl:L552-L554]. There is no `ws-calling-data` block and
no `to-day`, unlike the General Ledger's four [general/gl070.cbl:L245-L248] and
the Sales/Purchase five [sales/sl060.cbl:L395-L399]. There is also no term-code
gate on this route, because the IRS menu tests none - that absence is reproduced
rather than filled in.

`--clear-posting-file` carries the end-of-job question
[irs/irs030.cbl:L1715-L1724], and its answer TRUNCATES A TABLE: answering yes
performs an open-output on the transfer file, which the handler implements as
deleting every row [common/acas008.cbl:L313-L319]. **The frozen prompt has no
default, so neither does this flag: the answer is REQUIRED in one spelling or the
other.** The `[Y]` at [irs/irs030.cbl:L1716] is prompt text and nothing more --
the accept on the next line carries no `WITH UPDATE`, `WS-Reply` is never set to
"Y" anywhere in the program, and L1718-L1719 send anything that is neither `Y`
nor `N` straight back to the prompt, so a bare Enter RE-PROMPTS rather than
clearing. Both spellings are published so that the answer, either answer, is
always something the caller said. Reading that `[Y]` as a pre-filled default was
a default the program has not got would be an invention, and the one it
invented was the destructive answer.

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
three members in that exact COBOL order, so the argument list of
`main_loop_option_4` lines up against L668-L670 member for member.

THERE IS NO TERM-CODE GATE ON THIS ROUTE - AND THAT IS REPRODUCED, NOT LOST
The IRS menu has none of the General, Sales and Purchase dispatch machinery: no
`load00`-style wrapper paragraph, no `move zero to ws-term-code` before the
call, no test of a code after it, and no `overrewrite` paragraph at all. L672 is
a bare `go to main-loop.` - the menu simply loops. Its persistence lives
elsewhere and on a different trigger: `EOJ.` [irs/irs.cbl:L755-L775], reached
when the operator leaves the menu, which re-reads key 1, lays the IRS deltas over
it with `zz095-Restore-IRS-System-Data` and writes it back. That IS reproduced,
in `main`, because it is what carries `irs030`'s advanced `next-post` allocator
[irs/irs030.cbl:L1670-L1671] into SYSTEM-REC.
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
`Ledger-Postings-Add` [irs/irs030.cbl:L1569-L1730] is migrated, plus the two
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

*** ONE ANSWER TRUNCATES A TABLE, AND THERE IS NO DEFAULT - READ THIS ***
`--clear-posting-file` / `--no-clear-posting-file` is REQUIRED, and the
affirmative means DELETE EVERY ROW of the IRS transfer table `PSIRSPOST-REC`.
There is no default because the frozen program has none, and the appearance that
it does is a trap worth spelling out: `EOJ-q1.` displays the question with a
`[Y]` in the prompt LITERAL [irs/irs030.cbl:L1716], but the `accept` on the next
line carries NO `WITH UPDATE` phrase [irs/irs030.cbl:L1717], so the literal never
reaches the field; `WS-Reply pic x` [irs/irs030.cbl:L230] is never given the value
"Y" anywhere in the program; and any reply that is neither `Y` nor `N` goes
straight back to the prompt [irs/irs030.cbl:L1718-L1719]. A bare Enter therefore
RE-PROMPTS - it does not clear. Reading the `[Y]` as a pre-filled default was
and it would invent the destructive answer. `Y` performs
`acas008-Open-Output` [irs/irs030.cbl:L1723] followed by `acas008-Close`
[irs/irs030.cbl:L1724]. For that handler an open-for-output is not a file
operation at all - it is a mass delete: `if fn-Open and fn-output and not
FS-Cobol-Files-Used / set fn-delete-all to true / perform ba-Process-RDBMS`
[common/acas008.cbl:L313-L319], reinforced at [common/acas008.cbl:L571-L574].
The handler's own inline comment at [irs/irs030.cbl:L1723] says so: "performs a
acas008-Delete-All". Agent Action Plan section 0.3.4 is explicit that this makes
the answer a genuine input rather than decoration, because "the answer changes
table state". Pass `--clear-posting-file` to answer `Y` or
`--no-clear-posting-file` to answer `N` and leave the transfer table populated;
omitting both is a usage error, not an implied yes.

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
anomaly A-16 of the register, reproduced rather than corrected. It contains no
error handling that has no frozen counterpart: the per-handler error checks of
[copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob] belong to the data-access facade, and
the ONE condition `main` absorbs is that copybook's own `goback`
[copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L364] - a disposition of THIS program,
because irs/irs.cbl copies the copybook itself [irs/irs.cbl:L1035] and drives
acas000 through it at [irs/irs.cbl:L494-L551] and [irs/irs.cbl:L755-L795]. No
retry, no fallback and no recovery is added anywhere. And it prints nothing - the two
screen statements this route would otherwise carry, the count display at
[irs/irs030.cbl:L1714] and the acknowledgement pause at
[irs/irs030.cbl:L1725-L1727], are presentation with no database effect and are
dropped under Agent Action Plan section 0.3.4.

IMPORTS, AND WHY THE LIST IS THIS SHORT
Agent Action Plan section 0.4.3's per-directory import table allows `cli/*.py`
to reach `programs`, `clock` and `cli.args`, and bars it from `dal.acas*`. This
module reaches `cli.args`, `programs.irs030_posting` and - for the single name
`FacadeGoback` - `dal.facade`, and nothing else in the package: the record
dataclasses are `args`' business, the clock is reached
through `args.bind_irs_route`, and the three linkage records travel as one
`args.IrsLinkage` - carried, with the pre-dispatch snapshot, on one
`args.IrsRouteBinding` - so that no record module has to be named here. `dal.facade` is
the layer's published seam and is what the bar on `dal.acas*` leaves open; no
handler module is named here and no SQL is reachable from here. There is no
COBOL at runtime and no path from here to `harness/` (rule R-1); the harness
drives this module from the outside, and the dependency runs one way only.

Importing this module does no work: it builds no parser, configures no logging,
opens no connection and touches no filesystem.
"""

from __future__ import annotations

import argparse
import logging
from collections.abc import Mapping, Sequence
from typing import Final

#  The permitted internal edges, and all three are used.
#
#  `args`                  Agent Action Plan section 0.4.1.1 gives it the whole
#                          binding mandate; it is the SINGLE authority for the
#                          three linkage records and for the pinned clock.
#  `facade`                for ONE name, `FacadeGoback`. This module reproduces
#                          the IRS MENU PROGRAM, and irs/irs.cbl copies the same
#                          facade copybook the posting programs do
#                          [irs/irs.cbl:L1035], so the copybook's `goback`
#                          [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L364] is a
#                          disposition of THIS program and has to be absorbed
#                          here. `dal.facade` is the permitted seam; `dal.acas*`
#                          is barred to `cli/*` and is not imported.
#  `irs030_posting`        imported AS A MODULE, never `from ... import run`.
#                          Agent Action Plan section 0.3.3: "Callers cannot
#                          reach into a program's internals, exactly as a COBOL
#                          `CALL` cannot." `programs/__init__.py` publishes no
#                          dispatch table and no re-export, so the module IS
#                          the call target - `irs030_posting.run(...)` reads as
#                          `call "irs030"` does.
from acas_posting.cli import args
from acas_posting.dal import facade
from acas_posting.programs import irs030_posting

__all__: Final[tuple[str, ...]] = ("main", "main_loop_option_4")

_LOG: Final[logging.Logger] = logging.getLogger(__name__)

# The `CALL` literal at [irs/irs.cbl:L668].
_PROGRAM_ID: Final[str] = "irs030"

#  THE END-OF-JOB QUESTION HAS NO DEFAULT, AND THE `[Y]` IS DISPLAY TEXT ONLY.
#  This is the one place this module states it, and it is stated from a reading of
#  the frozen source rather than from the prompt's appearance.
#
#  `EOJ-q1.` [irs/irs030.cbl:L1715-L1719] is four statements:
#      L1716  display "Can I clear the Ledgers Posting file? [Y]" at 1401 ...
#      L1717  accept  WS-Reply at 1440 with foreground-color 6 UPPER.
#      L1718  if      WS-Reply not = "Y" and not = "N"
#      L1719          go to EOJ-q1.
#  THE `accept` AT L1717 CARRIES NO `WITH UPDATE` PHRASE, so the `[Y]` inside the
#  DISPLAY literal at L1716 is part of the prompt's text and does not reach the
#  field. Nor is the field pre-set: `WS-Reply pic x` [irs/irs030.cbl:L230] is
#  never given the value "Y" anywhere in the program - the only moves into it are
#  `space` [irs/irs030.cbl:L1512] and `spaces` [irs/irs030.cbl:L1521], and the one
#  `move "Z" to WS-Reply` is COMMENTED OUT [irs/irs030.cbl:L1530]. So a reply that
#  is neither "Y" nor "N" - including a bare Enter - takes L1718-L1719 straight
#  back to the prompt. THE LOOP CANNOT BE LEFT WITHOUT AN EXPLICIT ANSWER.
#
#  That the omission of `WITH UPDATE` is deliberate rather than an oversight is
#  visible in the same file: it uses the phrase at six other accepts -
#  [irs/irs030.cbl:L582], [:L732], [:L829], [:L848], [:L883] and [:L1015] - so the
#  maintainer had the construct to hand and did not use it here.
#
#  WHY A DEFAULT OF `True` WOULD BE WRONG. Reading the `[Y]` as a pre-fill "into an
#  `UPPER` update field" and defaulting the switch to clearing would look like
#  reproducing the original's default under rule R-4. There is no such default to
#  reproduce: that reading invents one, and it invents THE DESTRUCTIVE ANSWER. `Y`
#  reaches `acas008-Open-Output`
#  [irs/irs030.cbl:L1723], which for this handler DELETES EVERY ROW of
#  `PSIRSPOST-REC` [common/acas008.cbl:L313-L319], [common/acas008.cbl:L571-L574].
#  So an operator who said nothing would have emptied a table (rule R-3).
#
#  THE RESOLUTION: the answer is REQUIRED on the command line - `required=True`
#  and no `default`. Agent Action Plan section 0.8.1 promotes a write-gating prompt
#  "with the COBOL default preserved"; where the COBOL has none there is nothing to
#  preserve, and a usage error is the only headless analogue of a prompt that will
#  not accept a blank. Resolution by oracle (rule R-6) is unavailable: the frozen
#  archive is missing copybooks/ACAS-SQLstate-error-list.cob, so 22 of the 28
#  generated bridges do not compile, and fabricating it would breach R-3 and R-4.
#  Requiring the input pre-judges neither answer.

#  The switch pair, spelled once. `argparse.BooleanOptionalAction` publishes
#  BOTH `--clear-posting-file` and `--no-clear-posting-file` from this single
#  declaration, so the operator states the answer in the affirmative or the
#  negative and neither spelling can drift from the other. `required=True` makes
#  the pair itself compulsory: argparse rejects an invocation that names neither.
_CLEAR_POSTING_FILE_OPTION: Final[str] = "--clear-posting-file"

#  THE DIAGNOSTIC FORMAT IS NOT DECLARED HERE. It is declared once for the whole
#  package as `acas_posting.__main__.LOG_FORMAT`, and it carries NO TIMESTAMP on
#  purpose. A log line is presentation - Agent Action Plan section 0.3.4 requires
#  that it "must not alter control flow and must not appear in any table dump" -
#  and omitting the clock-derived field keeps even the transcript of two identical
#  runs identical, which is the cheapest possible reinforcement of rule R-6.
#  Nothing in this module reads a clock; that format could not, either.

# The `--help` prose, pre-wrapped so that no COBOL locator is split across lines by a
# re-flow. See `_build_parser` for why the raw formatter is used.
_DESCRIPTION: Final[str] = (
    "Post the SL/PL transfer file to the IRS nominal ledger.\n"
    "\n"
    "Reproduces irs030's Ledger-Postings-Add section\n"
    "[irs/irs030.cbl:L1569-L1730], reached in the frozen system through the\n"
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
    "*** ONE ANSWER DELETES DATA, AND THERE IS NO DEFAULT. ***\n"
    "\n"
    "--clear-posting-file / --no-clear-posting-file is REQUIRED. Answering\n"
    "--clear-posting-file deletes EVERY ROW of PSIRSPOST-REC\n"
    "[irs/irs030.cbl:L1720-L1724] through [common/acas008.cbl:L313-L319].\n"
    "\n"
    "There is no default because the frozen program has none. The [Y] in the\n"
    "prompt at [irs/irs030.cbl:L1716] is DISPLAY TEXT: the accept at L1717\n"
    "carries no WITH UPDATE, WS-Reply is never set to Y anywhere in the\n"
    "program, and L1718-L1719 send any reply that is neither Y nor N back to\n"
    "the prompt - so the loop cannot be left without an explicit answer.\n"
    "\n"
    "The database connection is NOT configured here. It comes from the six\n"
    "ACAS_DB_* variables of the deployment contract, which are the\n"
    "container-native transport of the six acas.param keywords the frozen\n"
    "common/acas-get-params.cbl reads; harness/docker-compose.yml sets all six\n"
    "for the gnucobol service. No password is ever taken from a command line."
)


def _build_parser() -> argparse.ArgumentParser:
    """Build the parser for Shape 3: `--run-date`, and the one promoted answer.

    Two contributions and no third. `args.add_irs_linkage_arguments` supplies everything
    the LINKAGE SECTION implies, which on this shape is the single required `--run-
    date`; this function then adds the one `ACCEPT` that gates a database write.
    Deliberately NOT composed.

    Returns:
        The parser. Built fresh per call, so nothing is constructed at import time and
            two callers cannot share mutable parser state.
    """
    parser = argparse.ArgumentParser(
        prog="python -m acas_posting.cli.irs_post",
        description=_DESCRIPTION,
        epilog=_EPILOG,
        #  The description and the epilog are PRE-WRAPPED above, with their line
        #  breaks chosen so that the destructive-answer warning reads as a block
        #  and each COBOL locator stays on one line. argparse's default formatter
        #  would re-flow both and scatter the locators; this one does not, and it
        #  still wraps each option's own help text normally.
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Shape 3's linkage options: the required `--run-date`, and nothing else.
    args.add_irs_linkage_arguments(parser)
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

    parser.add_argument(
        _CLEAR_POSTING_FILE_OPTION,
        action=argparse.BooleanOptionalAction,
        required=True,
        help=(
            "REQUIRED. Answer irs030's end-of-job question 'Can I clear the "
            "Ledgers Posting file? [Y]' (irs/irs030.cbl:L1716). *** ONE ANSWER "
            "IS DESTRUCTIVE. *** --clear-posting-file performs "
            "acas008-Open-Output (irs/irs030.cbl:L1723), which for this handler "
            "is not a file open but a mass delete - it sets fn-delete-all and "
            "calls the DAL (common/acas008.cbl:L313-L319, reinforced at "
            "L571-L574) - so EVERY ROW of the IRS transfer table PSIRSPOST-REC "
            "(entity SPL-Posting, bridge slpostingMT, record "
            "copybooks/wspost-irs.cob) is deleted. --no-clear-posting-file "
            "answers N and leaves the transfer table populated. THERE IS NO "
            "DEFAULT, because the frozen program has none: the [Y] at L1716 is "
            "display text, the accept at L1717 carries no WITH UPDATE, WS-Reply "
            "is never set to Y anywhere in the program, and L1718-L1719 re-prompt "
            "on any reply that is neither Y nor N - so a bare Enter cannot leave "
            "the loop. Omitting both switches is a usage error, not an implied "
            "yes. The answer decides whether one of the compared tables ends the "
            "run empty, so it must be pinned in every scenario."
        ),
    )

    #  Diagnostics only: no COBOL counterpart, no database effect. Shared with
    #  the other six routes so the level policy has one spelling.
    args.add_log_level_argument(parser)

    return parser


def main_loop_option_4(
    linkage: args.IrsLinkage,
    *,
    clear_posting_file: bool,
    dal_options: Mapping[str, object] | None = None,
) -> None:
    """`Main-Loop.` option `"4"` - the whole dispatch, reproduced.

    Named after the paragraph it reproduces, as rule R-5 requires: irs/irs.cbl `Main-
    Loop.` [irs/irs.cbl:L637], option `"4"` branch [irs/irs.cbl:L666-L672]. That branch
    is four statements long and this function is its Python counterpart statement for
    statement.

    Args:
        linkage: the three bound linkage records, in COBOL parameter order
            [irs/irs.cbl:L668-L671] - `IRS-System-Params`
            [copybooks/irswssystem.cob:L13], `WS-System-Record`
            [copybooks/wssystem.cob], `File-Defs` [copybooks/wsnames.cob:L13]. Build it
            with `args.bind_irs_route`.
        clear_posting_file: the answer to the end-of-job question
            [irs/irs030.cbl:L1715-L1724]. KEYWORD-ONLY and REQUIRED, with no
            default anywhere on the path from argv to here - THE FROZEN PROMPT HAS
            NONE, so inventing one would invent the destructive answer. `True` DELETES EVERY ROW of `PSIRSPOST-REC`
            [common/acas008.cbl:L313-L319].
        dal_options: the caller's keyword-only declarations, transport policy among
            them, carried to every facade context `irs030` builds. NOT a COBOL
            operand - the frozen `CALL` [irs/irs.cbl:L668-L671] passes three things
            and no fourth. `None` means "use the one policy
            `args.install_connection_policy` installed".

    Returns:
        Nothing. `irs030` communicates entirely through the database, through its `File-
            Access` status block and through the advanced key allocator on `IRS-System-
            Params`.
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
    #  THE IRS SHELL HAS NO `overrewrite` PARAGRAPH AND NO PER-BRANCH REWRITE -
    #  it persists at `EOJ.` instead [irs/irs.cbl:L755-L775], once for the whole
    #  session, and this route reproduces that in `main` rather than here (findings
    #  The shape of the IRS persistence is materially different
    #  from the other three shells and the difference is preserved: it RE-READS
    #  file-key 1 before writing [irs/irs.cbl:L759-L762], so its rewrite discards
    #  every in-memory change OUTSIDE the IRS block, where General, Sales and
    #  Purchase all rewrite the in-memory record. `zz095-Restore-IRS-System-Data`
    #  [irs/irs.cbl:L1000-L1032] is what carries the IRS block's changes across
    #  that re-read, field by guarded field.
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
    #  `clear_posting_file` is passed EXPLICITLY and always, and the callee has
    #  NO default for it to fall back on - neither layer can resolve an omission
    #  into a table truncation.
    #
    #  The callee's remaining keyword-only parameters, `file_access` and
    #  `dal_common`, are deliberately not passed - see OMISSIONS in the footer.
    irs030_posting.run(
        linkage.irs_system_params,
        linkage.ws_system_record,
        linkage.file_defs,
        clear_posting_file=clear_posting_file,
        #  The operator's transport declaration, carried to every facade context
        #  `irs030` builds. NOT a COBOL operand - the frozen `CALL` at L668-L670
        #  passes three things and no fourth, its bridge having no transport policy
        #  to pass [copybooks/mysql-procedures.cpy:L72-L77] - so it is stated at
        #  the process boundary, which is the only place that knows. `None` states
        #  the exact-parity policy, which is a statement and not an omission.
        dal_options=dal_options,
    )

    return


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point: bind Shape 3, dispatch `irs030`, report a status.

    Args:
        argv: the argument vector WITHOUT the program name, as
            `argparse.ArgumentParser.parse_args` takes it.

    Returns:
        `0`, on both of its two paths - completion, and the facade copybook's
        `goback` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L364]. The two are
        indistinguishable in the only status observable the frozen system
        produces; see the Q-CLI-EXITSTATUS note at the completion return and the
        note on the `except` clause.

    Raises:
        SystemExit: from argparse, for `--help` (status 0) and for a usage error
            such as an omitted `--run-date` (status 2). Not caught: a required
            argument that has no defensible default must fail loudly rather than
            be invented, which is what keeps an ambient run date out of the
            cycle (rule R-6).
        acas_posting.cli.args.RdbmsParamError: the deployment contract
            for the database connection is absent or unusable. Propagated
            deliberately, on the binder's own documented terms - a run that
            cannot connect to the provisioned database must stop before it
            writes anything, because the alternative is a silent connection to
            the placeholder endpoint [copybooks/wssystem.cob:L137-L144]. No
            handler is added for it: it has no COBOL counterpart, so there is no
            frozen disposition to reproduce.

    The ONE condition this module does handle is
    `acas_posting.dal.facade.FacadeGoback`, and it is handled because it DOES
    have a frozen counterpart - the `goback` that ends the menu program - rather
    than as defensive programming. Nothing else is caught.
    """
    #  LOGGING IS NOT INSTALLED HERE, and not at import either, so importing this
    #  module has no side effect whatsoever - `tests/scenarios/*` import the
    #  package. The package's one `basicConfig` lives in
    #  `acas_posting.__main__.configure_logging` and is reached only from a
    #  process boundary: the router, or this module's own guard through
    #  `run_entry_point`. It installs nothing when the root logger already has
    #  handlers, and adjusts the level only for a handler this package installed
    #  itself, so a host application's own configuration still wins.
    parser = _build_parser()
    namespace = parser.parse_args(argv)

    #  `--log-level` APPLIED THROUGH THE ONE CONFIGURATOR, and only when the
    #  operator supplied it. The shared fragment defaults the option to `None`, so
    #  `None` means "not asked for" and whatever the process boundary configured
    #  stands - on a routed run, the router's own `--log-level`. A supplied level
    #  is applied on either route: logging is configured once at the boundary, and
    #  `configure_logging` then sets the level because this package owns the
    #  handler, so the last explicit request wins. An embedding application's own
    #  configuration is never touched. The import is local to the call for the same
    #  reason the guard at the foot of this module gives.
    if namespace.log_level is not None:
        from acas_posting.__main__ import configure_logging

        configure_logging(namespace.log_level)

    #  THE ONE AND ONLY BINDING, AND THE ONE AND ONLY CLOCK INJECTION.
    #  `bind_irs_route` resolves the pinned pair from `--run-date` through
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
    #  THE MENU PROGRAM'S `goback` BOUNDARY.
    #  irs/irs.cbl copies the facade copybook itself [irs/irs.cbl:L1035] and
    #  drives acas000 through it in its OWN code, both before `Main-Loop` -
    #  `aa005-Open-System.` [irs/irs.cbl:L494] and `aa010-Get-System-Recs.`
    #  [irs/irs.cbl:L507], whose traffic runs L499-L551 - and at end of job,
    #  `EOJ.` [irs/irs.cbl:L755]. Any of those verbs can reach
    #  `acas000-Check-4-Errors` and from there `Open-Error-Continued`, which ends
    #  in `goback.` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L364]. Because the
    #  copybook is textually included in irs/irs.cbl, that `goback` returns from
    #  THE MENU PROGRAM - it is this route's own termination, not a condition
    #  travelling up from `irs030`.
    #
    #  So it is absorbed at this boundary, and the handler covers the whole body
    #  rather than one call: every statement of the menu program that reaches a
    #  handler belongs inside it, including the load and the persist that
    #  reproduce L494-L551 and L755-L795.
    #
    #  `irs030`'s own `goback` sites do NOT surface here. `irs030_posting.run`
    #  absorbs them at its own program boundary, exactly as the frozen `goback`
    #  returns from `irs030` into `Main-Loop-Clear` [irs/irs030.cbl:L603] and the
    #  menu carries on to L604.
    #  THE MENU'S OWN WORKING-STORAGE - key 1 alone on this route, because
    #  irs/irs.cbl reads key 1 and nothing else [irs/irs.cbl:L511-L512]. See
    #  `args.irs_menu_state`.
    menu_state = args.irs_menu_state()

    try:
        #  ONE BIND, ONE KEY-1 LOAD, ONE `zz090`. The binder returns
        #  both halves of what the frozen menu holds at its `CALL`: the three
        #  operands and the snapshot its single `zz090-Set-Up-IRS-System-Data`
        #  [irs/irs.cbl:L556] captured. Re-taking the snapshot here meant a second
        #  remap over a second key-1 traversal, with its own store traffic, its own
        #  log records and its own failure path - none of which the frozen menu has.
        binding = args.bind_irs_route(namespace, menu_state=menu_state)
        linkage = binding.linkage

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

        #  [irs/irs.cbl:L556] `perform zz090-Set-Up-IRS-System-Data.` ran inside the
        #  binder, once, as the frozen menu performs it once - and the SNAPSHOT that
        #  one pass captured travels beside the linkage on `IrsRouteBinding`. It is
        #  the state BEFORE the dispatch, which is precisely what `zz095` must
        #  compare against; the maintainer's own reminder at [irs/irs.cbl:L556] is
        #  "dont forget to run zz095 after".
        #
        #  `menu_state` is always supplied above, so the binder always performed
        #  `zz090` and the snapshot is always present. The check is the one line that
        #  proves it rather than assuming it, because `eoj_persist_irs_system_data`
        #  cannot decide "only where changed" without it.
        snapshot = binding.pre_dispatch_snapshot
        if snapshot is None:  # pragma: no cover - menu_state is never None here
            raise AssertionError(
                "bind_irs_route returned no zz090 snapshot for a route that "
                "supplied menu_state; zz095 [irs/irs.cbl:L1011-L1029] compares "
                "against it and cannot run without it"
            )

        main_loop_option_4(
            linkage, clear_posting_file=namespace.clear_posting_file
        )

        #  [irs/irs.cbl:L755-L775] `EOJ.` - re-read key 1, lay the IRS deltas over
        #  it with `zz095`, write it back. THIS IS WHAT CARRIES `next-post`
        #  FORWARD: `irs030` advances the posting-key allocator once per posting
        #  written [irs/irs030.cbl:L1670-L1671], and without this the next run
        #  would restart at the same value. Its backup-script arm
        #  [irs/irs.cbl:L777-L791] is excluded by Agent Action Plan section 0.2.2.
        args.eoj_persist_irs_system_data(
            snapshot,
            linkage.irs_system_params,
            linkage.ws_system_record,
            menu_state,
            linkage.file_defs,
        )
    except facade.FacadeGoback:
        #  THE DISPOSITION IS THE MENU PROGRAM'S NORMAL END, AND THAT IS
        #  MEASURED, NOT CHOSEN. `EOJ-End.` [irs/irs.cbl:L795-L796] ends the menu
        #  with a bare `goback.`, and `RETURN-CODE` - the one register GnuCOBOL
        #  surfaces as a process status - is read and never written anywhere in
        #  the five menus or the twelve posting programs. The abort `goback` at
        #  [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L364] is also bare. The two
        #  paths are therefore indistinguishable in the only observable the
        #  frozen system produces, so this route reports the same `0`.
        #  Inventing a non-zero status would add an observable the compiled
        #  program does not have, which rules R-3 and R-4 forbid.
        #
        #  Nothing is closed and nothing is rolled back here. Each check
        #  paragraph has already closed its own handler
        #  [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L323, L330, L337], and the
        #  `goback` skips whatever the abandoned path had left to do - Agent
        #  Action Plan section 0.6.5: "the partial state is therefore committed,
        #  not rolled back."
        #
        #  Logged at debug, not error: `Open-Error-Continued` has already
        #  reported FS-Reply, WE-Error, SQL-Err and SQL-Msg at error level, and
        #  the `goback` itself displays nothing.
        _LOG.debug(
            "%s route: menu program returning via the goback at "
            "[copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L364]",
            _PROGRAM_ID,
        )
        return 0
    except args.RdbmsParamError as error:
        #  THE EXACT TYPE IS CAUGHT, NOT `ValueError`. The
        #  deployment contract for the six connection parameters is resolved
        #  inside `bind_irs_route`, before the store is opened, so a failure
        #  here has touched nothing: no database contacted, no file opened, no
        #  program entered. Catching the base class would also swallow a genuine
        #  defect - a bad namespace attribute, a malformed record - and report it
        #  as a configuration problem, so only the exact type is caught and
        #  everything else keeps its traceback. `RdbmsParamError` never carries a
        #  parameter value, so reporting it cannot leak a credential.
        return args.report_configuration_failure(
            error, logger=_LOG, subject="IRS posting"
        )

    #  755  EOJ.
    #  THE COPY-BACK AND THE PERSIST, in the frozen order,
    #  performed inside the block above rather than here - see the
    #  `args.eoj_persist_irs_system_data` call, which sits inside the `goback`
    #  boundary because every verb it issues can reach one.
    #  `irs.cbl` re-reads file-key 1 [irs/irs.cbl:L759-L762], performs
    #  `zz095-Restore-IRS-System-Data` [irs/irs.cbl:L764] to carry the IRS block's
    #  changes onto the freshly read row, and only then rewrites key 1 - to the
    #  Cobol file [irs/irs.cbl:L765-L769] and, when `File-System-Used NOT = zero`,
    #  to the RDB as well [irs/irs.cbl:L770-L775].
    #  `args.eoj_persist_irs_system_data` performs that sequence through the
    #  facade.
    #
    #  WITHOUT THIS THE ALLOCATOR NEVER ADVANCED IN THE STORE. `irs030` advances
    #  `Next-Post` in the linkage record it was handed, and nothing carried that
    #  back to `SYSTEM-REC` or wrote it out, so the next run started from the same
    #  key again. `zz095` is what carries it: seven guarded
    #  `if WS-<field> not = <field>` tests [irs/irs.cbl:L1000-L1032], which is why
    #  the pre-image taken at `zz090` had to be kept.
    #
    #  ONE CALL, NOT TWO. `args.eoj_persist_irs_system_data` performs the whole
    #  paragraph including its `perform zz095-Restore-IRS-System-Data` at
    #  [irs/irs.cbl:L764], and it performs it AFTER the re-read, which is the
    #  frozen order and the only order in which the copy-back means anything: the
    #  re-read replaces the record field by field, so a `zz095` applied before it
    #  would simply be overwritten. Calling `zz095` from here as well would add a
    #  statement the frozen paragraph does not have.

    #  `EOJ.` [irs/irs.cbl:L754-L775] - the menu's exit path, whose DATABASE
    #  EFFECT this route must reproduce because the in-scope section changed a
    #  field the store holds. Reproduced by the
    #  `args.eoj_persist_irs_system_data` call inside the boundary block above,
    #  which is where it has to sit: every verb the paragraph issues can reach a
    #  `goback`, so performing it outside the block would place the re-read, the
    #  copy-back and the rewrite beyond the reach of the handler that ends the
    #  run unit.

    return 0


if __name__ == "__main__":
    #  `harness/run_python_scenario.sh` invokes these modules directly, as
    #  `python -m acas_posting.cli.irs_post`, and `pyproject.toml` declares no
    #  `[project.scripts]`. `raise SystemExit(...)` rather than `sys.exit(...)`
    #  keeps `sys` out of the import list.
    #
    #  ONE PROCESS BOUNDARY, SHARED WITH THE ROUTER. `run_entry_point` configures
    #  logging once and converts a failure into one sanitised ERROR record and a
    #  deterministic exit status. The import is inside the guard because it is
    #  needed only when this module IS the process, and because the router imports
    #  this module back when the router is.
    from acas_posting.__main__ import run_entry_point

    raise SystemExit(run_entry_point(main, command="irs-post"))



# --- traceability ------------------------------------------------------------
#
# Rule R-5's record for this route. Every span was MEASURED against the frozen
# source, which is REFERENCE only (Agent Action Plan section 0.8.1).
#
# MODULE -> COBOL SOURCE
#   acas_posting/cli/irs_post.py  <-  irs/irs.cbl (the option "4" dispatch),
#   irs/irs030.cbl (the callee's linkage and its one promoted `ACCEPT`),
#   common/acas008.cbl (what "clear" means), copybooks/irswssystem.cob,
#   copybooks/wssystem.cob and copybooks/wsnames.cob (the record identities).
#
# FUNCTION -> PARAGRAPH
#   main_loop_option_4  <-  irs/irs.cbl `Main-Loop.` L637, option "4" branch
#                           L666-L672: the menu test L666-L667 (dropped, screen
#                           input), the three-operand `CALL` L668-L670 with
#                           `end-call` L671 (reproduced exactly), and
#                           `go to main-loop.` L672.
#   main                <-  no paragraph. The CLI boundary: argparse replaces the
#                           menu's paint and `ACCEPT` (irs/irs.cbl L638-L644),
#                           which have no database effect (AAP 0.3.4).
#   _build_parser       <-  no paragraph. Composes
#                           `args.add_irs_linkage_arguments` and declares the one
#                           promoted `ACCEPT` of irs/irs030.cbl `EOJ-q1.`
#                           L1715-L1724.
#
# PROGRAM -> MODULE
#   irs030  ->  acas_posting/programs/irs030_posting.py
#               linkage       irs/irs030.cbl:L552-L554 (IRS-System-Params,
#                             WS-System-Record, File-Defs)
#               in scope      `Ledger-Postings-Add section.` L1569-L1730, plus the
#                             two ROUNDED VAT computes of `Net section.` L1544
#                             (compute L1551) and `Gross section.` L1556 (compute
#                             L1562) that the posting path consumes
#               out of scope  everything else in the 1,733-line file (AAP 0.2.1.1)
#
# PROMOTED PARAMETER -> LOCATOR  (Agent Action Plan section 0.3.4)
#   clear_posting_file  <-  irs/irs030.cbl `EOJ-q1.` L1715-L1727
#     L1716  the question, displayed with the literal `[Y]`  <- AN OPERATOR HINT
#            INSIDE THE DISPLAY TEXT, not a value moved into the accept field
#     L1717  `accept WS-Reply at 1440 ... UPPER`  <- NO `with update` (which the
#            program does use, at L717 among others), and `03 WS-Reply pic x.`
#            L230 declares no VALUE
#     L1718-L1719  re-prompt unless the reply is Y or N  <- GO TO class 1, and the
#            reason there is NO DEFAULT: a space cannot get past it
#     L1720  `if WS-Reply = "Y"`;  L1723 `perform acas008-Open-Output` - the
#            comment on that very line reads "performs a acas008-Delete-All";
#            L1724 `perform acas008-Close.`;  L1725-L1727 the pause, DROPPED
#     Effect via common/acas008.cbl:L313-L319 and :L571-L574, so the answer
#     DELETES EVERY ROW of PSIRSPOST-REC. The switch pair is `required=True`:
#     the frozen prompt has no default, so there is nothing to preserve and a
#     default would be an invention.
#
# RECORD IDENTITIES  -  the three linkage parameters, in COBOL order
#   1  IRS-System-Params  =  copybooks/irswssystem.cob `01 system-record.` L13,
#      renamed by `copy "irswssystem.cob" replacing system-record by
#      IRS-System-Params.` at irs/irs.cbl:L391-L392. `03 run-date pic x(8).` at
#      copybooks/irswssystem.cob:L14 - TEXT, dd/mm/yy, NOT the binary field. NOT
#      copybooks/wssystem.cob: a different and much smaller record (256 bytes per
#      its own header note at copybooks/irswssystem.cob:L10), so binding the ACAS
#      system record into parameter 1 would be wrong in layout and width.
#      Modelled by acas_posting/records/irs_system.py. Its `03 system-ops pic x.`
#      L23 carries one extra space of indentation relative to its siblings - a
#      cosmetic irregularity of the frozen source, noted and not corrected.
#   2  WS-System-Record   =  copybooks/wssystem.cob, the 169-column ACAS system
#      record, as the maintainer's `*> ACAS system rec.` at the call site says
#      (irs/irs.cbl:L669). `05 Run-Date binary-long.` L67 - the binary day count,
#      and a column of a compared table. Also the sole carrier of the six RDBMS
#      connection fields (copybooks/wssystem.cob:L137-L144) to the data-access
#      layer (common/acas008.cbl:L558-L563).
#   3  File-Defs          =  copybooks/wsnames.cob `01 File-Defs.` L13. Entirely
#      `VALUE`-initialised in the copybook, so its declared defaults already are
#      the COBOL state and it needs no CLI option.
#
# `GO TO` CLASSES  (Agent Action Plan section 0.4.2)
#   irs/irs.cbl:L672  `go to main-loop.`  CLASS 1 (loop-back), annotated at the end
#     of `main_loop_option_4`. One CLI invocation is one iteration of the menu
#     loop; the loop itself is screen-driven and dropped.
#   irs/irs030.cbl:L1718-L1719  `go to EOJ-q1.`  CLASS 1, DROPPED. It re-prompts
#     after an unrecognised reply, so its only effect is to block a terminal - no
#     database effect and no control transfer to preserve (AAP 0.3.4). The
#     DECISION it guards survives as `clear_posting_file`.
#   No Class 2, 3 or 4 site exists on this route.
#
# CORRECTIONS  -  verified with a line read. DO NOT "fix" these back to the values
# the planning documents carry.
#   1. irs/irs.cbl's dispatching paragraph is `Main-Loop.` L637 with the option "4"
#      `CALL` inline at L666-L672. There is NO `load00` / `load000` equivalent on
#      the IRS side at all, and `procedure division.` L470 takes no `USING`, so
#      irs/irs.cbl is a MAIN program while all twelve migrated programs are
#      `CALL`ed sub-programs.
#   2. The Sales / Purchase shape has FIVE parameters, not the four AAP 0.4.1.1's
#      phrasing implies; section 0.1.1 and sales/sl060.cbl:L395-L399 agree on five.
#   3. `WS-CD-Args` is at copybooks/wscall.cob:L14, not the L13 AAP 0.4.1.1 cites
#      (L13 is `WS-Sub-Function`, L11 a comment). Recorded for the folder's record
#      only - Shape 3 has no calling-data block.
#   4. AAP 0.1.1 calls copybooks/Proc-ACAS-Mapser-RDB.cob:L72-L80 "the single read
#      in the whole call chain". A census finds FOURTEEN ambient date and time
#      reads across six files, this menu's own at irs/irs.cbl:L480 among them;
#      `acas_posting/clock.py` carries the site list. The plan's CONCLUSION
#      nonetheless holds exactly, because every one of the fourteen is in an
#      out-of-scope menu shell or the date-service copybook those shells COPY and
#      all twelve in-scope programs contain zero: pinning the two observables at
#      the CLI boundary is sufficient.
#   5. The `acas008-Open-Output` perform is at irs/irs030.cbl:L1723, not L1722:
#      L1721-L1722 are the maintainer's commented-out `open output` / `close` pair
#      kept above the live `perform`. Every citation here uses L1723.
#   6. `programs.irs030_posting.run` takes TWO keyword-only parameters beyond the
#      three positional ones and `clear_posting_file` - `file_access` and
#      `dal_common`, both defaulting to `None`. `clear_posting_file` itself is
#      keyword-only WITH NO DEFAULT, so neither layer can supply the destructive
#      answer on a caller's behalf. This module requires the switch, so it always
#      has an answer to pass.
#
# OMISSIONS  -  recorded so a reader comparing the two trees does not conclude
# something was lost (Agent Action Plan section 0.4.3)
#   * irs/irs.cbl'S ENTIRE MENU: the screen section and its paint (L638-L642), the
#     `accept Menu-Screen-1` (L643), the `Param-Restrict` erase (L641-L642), and
#     every option other than "4" - "1" irs000 (L645-L652), "2" irs010
#     (L653-L658), "3" irs020 (L659-L665), "5" irs040 (L673-L679) and later ones.
#     AAP 0.2.2 places irs000/irs010/irs020/irs070 out of scope as interactive and
#     irs040/irs050/irs060/irs090 as report programs; only option "4" reaches an
#     in-scope program. `irs-main section.` L473 onwards - the environment set-up
#     L478-L479, the terminal-size checks L483-L486 and the program-argument scan
#     L481 - is likewise not reproduced.
#   * irs/irs.cbl `zz090-Proc-Run-Date.` L972-L978 and its siblings
#     `zz090-Proc-Start-Date.` L980 and `zz090-Proc-End-Date.` L987, all three
#     reproduced ONCE inside `args.zz090_set_up_irs_system_data`, which shares one
#     `Maps03Ws` across them exactly as the frozen section shares one `maps03-ws`.
#     No date logic is held here. See Q-CLI-IRS-RUNDATE.
#   * irs/irs.cbl:L480, THIS MENU'S OWN CLOCK READ, and the binary-to-text
#     conversion it feeds at L632-L634. Replaced by the REQUIRED `--run-date`,
#     which is what makes two runs byte-identical (R-6, AAP 0.8.5).
#   * irs/irs030.cbl:L1713-L1714, the `display space` and the record-count report,
#     and :L1725-L1727, the acknowledgement pause. Presentation with no database
#     effect (AAP 0.3.4); neither may alter control flow or reach a table dump.
#   * EVERYTHING IN irs/irs030.cbl OUTSIDE `Ledger-Postings-Add` L1569-L1733
#     except the `Net` L1544 and `Gross` L1556 VAT computes: `Init-Main` L557,
#     `Main-Loop.` L571, `Input-Headings` L1239, `Date-Validate` L1285,
#     `Initialise-Main` L1402, `Show-Default` L1504 and `file-init` L1518 are all
#     out of scope and none is reachable from this module.
#   * THE PER-HANDLER ERROR CHECKS of copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob,
#     copied by irs030 at irs/irs030.cbl:L1732. They belong to `dal/facade.py`,
#     which publishes both vocabularies over one implementation. This module adds
#     no error handling beyond the ONE disposition the copybook gives it - the
#     `goback` at Proc-ZZ100-ACAS-IRS-Calls.cob:L364, absorbed in `main` because
#     irs/irs.cbl copies that copybook itself (irs/irs.cbl:L1035) and so owns that
#     termination. No retry and no fallback anywhere.
#   * THE CALLEE'S `file_access` AND `dal_common` PARAMETERS. Both are irs030's own
#     WORKING-STORAGE rather than linkage - irs/irs030.cbl:L285 and :L298 - and the
#     frozen program populates them in the out-of-scope `Init-Main` / `file-init`.
#     Left at `None`, so the callee builds fresh blocks. Two sufficient reasons:
#     they are not among the three parameters irs/irs.cbl:L668-L670 passes, so
#     supplying them would invent an input (R-3); and constructing one would
#     require importing `acas_posting.records.*`, which AAP 0.4.3's import table
#     bars `cli/*.py` from. The connection parameters travel in `WS-System-Record`
#     instead, which this module does pass (common/acas008.cbl:L558-L563).
#   * `args.reset_term_code`, `args.set_called`, `args.is_serious_error` and
#     `args.exit_status_for`: all four serve the term-code protocol, and Shape 3
#     has no `WS-Term-Code` (irs/irs030.cbl:L552-L554). Calling any would imply a
#     field this route has not got.
#   * THE OTHER MENUS' `overrewrite`. irs/irs.cbl has none: its persistence is
#     `EOJ.` L755-L775, firing when the operator leaves the menu rather than after
#     a dispatch. That paragraph IS reproduced, by
#     `args.eoj_persist_irs_system_data`, called from `main` after the dispatch -
#     where a single-operation CLI's "leaving the menu" falls. Only its
#     backup-script arm L777-L791 is omitted, by AAP 0.2.2's spool-out exclusion
#     and by R-1. See Q-CLI-SYSREC-LOAD in args.py.
#
# ANOMALIES REPRODUCED DOWNSTREAM  -  listed for the reader and compensated for by
# NOTHING here (R-4). This module adds no retry, rollback, validation or warning
# for any of them, and passes no flag that would suppress one.
#   * A-4  THE HALF-POSTED DOUBLE ENTRY: the debit is rewritten before the credit
#     account is looked up, so a missing credit leaves a posted debit with no
#     balancing credit and no posting record [irs/irs030.cbl:L1635-L1652].
#     Reproduced in programs/irs030_posting.py.
#   * A-5  THE LOST UPDATE ON THE TWO VAT CONTROL ACCOUNTS: read into pre-loop
#     snapshots [irs/irs030.cbl:L1602], [:L1612] and rewritten from those
#     snapshots at end of job [:L1704-L1708], so any in-loop rewrite of the same
#     accounts is silently discarded.
#   * THE WRITE-FAILURE JUMP TO END OF JOB [irs/irs030.cbl:L1673-L1678], which
#     still performs the two snapshot rewrites and the closes, so the partial
#     state is committed rather than rolled back. That path still reaches
#     `EOJ-q1.`, so `clear_posting_file` still applies after a write failure -
#     frozen behaviour, preserved.
#   * A-6  THE ALWAYS-FAILING REWRITE VERB: the transfer-file handler rejects
#     read-indexed, rewrite, start and delete UNCONDITIONALLY at entry with
#     WE-Error 988 and fs-reply 99 [common/acas008.cbl:L299-L307], because the
#     underlying file is sequential - yet the facade still publishes Rewrite.
#     Reproduced in dal/acas008_spl_posting.py.
#   * A-7  THE BRIDGE-ONLY DERIVED DATE COLUMNS `POST4-DAY`, `POST4-MONTH` and
#     `POST4-YEAR`, in no copybook, derived under a guard that leaves them zero
#     while the raw date text is still stored [common/irspostingMT.cbl:L982-L987].
#     Reproduced in dal/acasirsub4_irs_posting.py.
#   * A-16  ON WHOSE PATH THIS MODULE SITS: `maps04` leaves its output field
#     untouched on a rejected date [common/maps04.cbl:L146], [:L154] and the
#     documented "errors return zero" contract holds only because callers pre-zero
#     it [copybooks/Proc-ACAS-Mapser-RDB.cob:L78]. So a `--run-date` the legacy
#     module rejects yields `Run-Date` 0 and NO exception. No check and no message
#     is added: validating would add a validation the COBOL has not got (R-3) and
#     correcting a defect is a failure (R-4).
#
# OUT-OF-SCOPE FINDING, RECORDED AND NOT ACTED ON  -  `File-System-Used`
# [copybooks/wssystem.cob:L112-L113]. The record `args.bind_irs_route` builds at
# the copybook's declared defaults carries ZERO, which is the
# `88 FS-Cobol-Files-Used` condition, while `dal/*` branches on the field and
# expects the RDB leg. Three AAP-created files hold three consistent-in-isolation
# positions - records/system_record.py must reproduce the copybook default,
# SYSTEM-REC being one of the 22 compared tables (R-4); cli/args.py builds at the
# declared defaults and settles Q-CLI-SYSREC-LOAD by recording that the seeded
# state owns the rest; dal/* expects the RDB leg - and no fix available inside this
# file's boundary keeps every rule: this module may not import
# `acas_posting.records.*` (AAP 0.4.3) nor construct or mutate a linkage record,
# a `--file-system-used` option would add a CLI input the frozen menus do not
# offer (R-3), and forcing the value silently would overwrite a declared default
# that is a column of a compared table (R-4). The field's owner is therefore the
# seeded state, placed by `harness/seed.sh`. The finding is package-wide rather
# than specific to this route: all seven entry points bind through the same binder.
#
# AMBIGUITIES RAISED BY THIS MODULE  (rule R-6)  -  three, each marked in place at
# the code it governs and recorded in docs/migration/ambiguity-resolutions.md
#   Q-CLI-IRS-RUNDATE  in `main`, at the `bind_irs_route` call. Whether irs030
#     observes `IRS-System-Params.run-date pic x(8)` at all, and if so what value
#     the option "4" route presents it with, given that `zz090-Proc-Run-Date.`
#     [irs/irs.cbl:L972-L978] is performed on the option "1" branch
#     [irs/irs.cbl:L651] and that [irs/irs.cbl:L636] comments "menu uses the irs
#     param file dates". STILL OPEN, and marked in args.py too, where the single
#     derivation lives. Nothing provisional executes: the binder reproduces the
#     frozen `STRING` either way.
#   Q-CLI-EXITSTATUS  in `main`, at the `return 0`. Shape 3 carries no
#     `WS-Term-Code`, so the process exit status has no COBOL counterpart on this
#     route at all. `args.exit_status_for` settles the general question by
#     establishing there is no oracle observable - `RETURN-CODE` is read and never
#     written in the five menus and the twelve programs - and here there is not
#     even a code to map, so completion is all there is to report.
#   Q-CLI-CLEARFILE  RESOLVED by reading the frozen source rather than the
#     prompt's appearance. The `[Y]` literal [irs/irs030.cbl:L1716] does NOT
#     pre-fill an update field: the accept at L1717 carries no `WITH UPDATE`, so
#     the literal stays in the prompt text; `WS-Reply pic x` [:L230] is never given
#     "Y" anywhere in the program (the moves into it are `space` [:L1512] and
#     `spaces` [:L1521], and the `move "Z"` at [:L1530] is commented out); and
#     L1718-L1719 send anything that is neither "Y" nor "N" back to the prompt, so
#     a bare Enter re-prompts rather than clearing. That the missing `WITH UPDATE`
#     is deliberate shows in the same file, which uses the phrase at six other
#     accepts - [:L582], [:L732], [:L829], [:L848], [:L883], [:L1015]. THE ANSWER
#     IS THEREFORE REQUIRED on the command line, no default being available to
#     preserve (AAP 0.8.1). Arbitration against the FROZEN build is unavailable -
#     it does not compile, copybooks/ACAS-SQLstate-error-list.cob being absent
#     while 22 of the 28 generated bridges COPY it - and requiring the input
#     pre-judges neither answer.
#
# RULE COMPLIANCE, FILE-SPECIFIC FACTS ONLY (the six are Agent Action Plan 0.7.2;
# README-python-migration.md states them once)
#   R-1  The whole import list is `argparse`, `logging`,
#        `collections.abc.Sequence`, `typing.Final`, `acas_posting.cli.args` and
#        `acas_posting.programs.irs030_posting` - no process spawn, no foreign
#        library, no toolchain reference and no import of the oracle's tree, and no
#        option that selects, invokes or diffs against it. The harness drives THIS
#        module from outside; the dependency runs one way.
#   R-2  The only values handled are `bool` (`clear_posting_file`), `str`
#        (`--run-date` text and the program id) and `int` (the exit status and the
#        binary `Run-Date` it logs). No float in any signature, annotation, option
#        `type=` or expression, and NO ARITHMETIC AT ALL - the syntax tree contains
#        exactly one `BinOp`, `Sequence[str] | None`, whose operator is `BitOr` on
#        two types. The two `ROUNDED` VAT computes [irs/irs030.cbl:L1551], [:L1562]
#        live in programs/irs030_posting.py.
#   R-3  No validation of `--run-date` (see A-16 above) or of the linkage records,
#        no field added, no SQL, no DDL. The option set is CLOSED AT TWO - the
#        required `--run-date` that args owns, and the one promoted `ACCEPT` - and
#        in particular there is no `--irs-instead`, which irs030 never reads. No
#        concurrency primitive and no `--parallel` / `--jobs` / `--workers`.
#   R-4  Three reproductions here, each carrying its locator at the site (AAP
#        0.7.4 C-4): the THREE-PARAMETER SHAPE with no calling-data block and no
#        `to-day` [irs/irs.cbl:L666-L672], [irs/irs030.cbl:L552-L554]; the ABSENCE
#        OF ANY TERM-CODE GATE OR DISPATCH WRAPPER, left absent rather than
#        harmonised with the other three ledgers [irs/irs.cbl:L672]; and the
#        MASS-DELETE ANSWER [irs/irs030.cbl:L1716] whose effect is truncation of
#        the transfer table [:L1720-L1724], [common/acas008.cbl:L313-L319] -
#        reproduced in full and reachable by naming `--clear-posting-file`, exactly
#        as reachable as `Y` is in the frozen program. What is NOT reproduced is a
#        DEFAULT for that answer, because the frozen prompt has none; inventing one
#        in the destructive direction would have made an omitted argument delete
#        rows.
#   R-5  This footer, the paragraph-named `main_loop_option_4`, a `# GO TO class N`
#        annotation at every transfer site, and a `[path:Lnnn]` locator on every
#        claim about the frozen source.
#   R-6  `--run-date` is REQUIRED with no default and no fallback, and this module
#        reads no clock, environment variable, random source or host identity -
#        even the log format carries no timestamp. Two runs under the same
#        `--run-date` bind byte-identical records (AAP 0.8.5).
# -----------------------------------------------------------------------------
