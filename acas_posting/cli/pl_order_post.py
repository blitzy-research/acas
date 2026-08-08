"""Purchase transaction posting: `pl055` then `pl060`, with no gate at all.

The batch entry point for `purchase/purchase.cbl` `load08.` L752-L762, whose menu
letter is "(H) Purchase Transactions Post" [purchase/purchase.cbl:L540]. Both
legs are dispatched through `load000.`, with no screen output.

This route has no paragraph-level gate, and the absence is deliberate: the lines
that would gate it are commented out in the frozen source
[purchase/purchase.cbl:L755-L758], where the Sales twin tests `not = zero` after
each leg [sales/sales.cbl:L761-L766] and the General Ledger tests `= 5`
[general/general.cbl:L810-L811]. The route is still abortable, through
`load000.`'s own `> 7` disposition [purchase/purchase.cbl:L684], which is a
different mechanism reaching a different disposition - so pl060 runs after a
pl055 failure that only reported 1 through 7, exactly as it does in COBOL.

The linkage is five parameters - ws-calling-data, system-record,
system-record-4, to-day, file-defs - matching the Sales shape
[sales/sl060.cbl:L395-L399] and unlike the General Ledger's four
[general/gl070.cbl:L245-L248].

The run date is an argument and never a clock reading (R-6): neither pl055 nor
pl060 reads a clock, both receive the date through linkage.

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
pinned date are byte-identical (rule R-6). The frozen call chain holds FOURTEEN
ambient date and time reads across six files - six `FUNCTION CURRENT-DATE`
[common/ACAS.cbl:L353], [general/general.cbl:L371], [sales/sales.cbl:L323],
[purchase/purchase.cbl:L318], [irs/irs.cbl:L480],
[copybooks/Proc-ACAS-Mapser-RDB.cob:L72], four `accept ... from time` and four
`accept ... from date` - and EVERY ONE of them is in an out-of-scope menu shell or
in the date-service copybook those shells COPY, as the census in
`acas_posting/clock.py` records. The one that bears on a posting run is
[copybooks/Proc-ACAS-Mapser-RDB.cob:L72-L80], and even that runs only on the
FIRST-TIME capture path `ba010-Capture-Data`: a normal Purchase run derives
`to-day` from the STORED `Run-Date` - `move run-date to u-bin` / `call "maps04"` /
`move u-date to to-day` [purchase/purchase.cbl:L403-L405].

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


# THE TWO PROGRAM-IDS THIS ROUTE DISPATCHES, as the menu writes them. `move "pl055" to
# ws-called.` [purchase/purchase.cbl:L759] and `move "pl060" to ws-called.`
# [purchase/purchase.cbl:L761].
_PL055: Final[str] = "pl055"
_PL060: Final[str] = "pl060"

_MENU_OPTION: Final[str] = "(H)  Purchase Transactions Post"

# The invocation name argparse reports in usage and error messages. `pyproject` declares
# no console script, so a module invocation is the real entry form.
_PROG: Final[str] = "python -m acas_posting.cli.pl_order_post"

#  THIS MODULE DECLARES NO LOG FORMAT AND CALLS NO `basicConfig`. There is one
#  `logging.basicConfig` in the package - `acas_posting.__main__.configure_logging`
#  - which owns the single timestamp-free format and the single level policy, and
#  which only a process boundary reaches. Seven modules each declaring their own
#  format produced three different ones and a first-caller-wins race. `main` asks
#  that same configurator to set the LEVEL when `--log-level` was supplied, which
#  installs nothing and changes no format.


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
type _ProgramEntry = Callable[..., object | None]


class _ExtractChannel:
    """The ONE OTM4 work file `pl055` and `pl060` share.

    Not a linkage parameter and not a table. It stands in for what the compiled
    programs use instead: their own FILE SECTIONs over one transient work file
    that persists between the two `CALL`s, `file-28` alias `"openitm4"`
    [copybooks/wsnames.cob:L45]. `copy "seloi4.cob"` carries its author's own note
    on it - *"Temp file only for i/p to pl060."* [purchase/pl055.cbl:L109].
    Nothing about it reaches the database, so nothing about it appears in a table
    dump.

    WHY A HOLDER RATHER THAN A LOCAL. The file has to outlive the first dispatch
    and reach the second, because that is how the two programs communicate:
    `pl055` opens it for EXTEND [purchase/pl055.cbl:L301], appends one header per
    invoice [purchase/pl055.cbl:L587] and closes it [purchase/pl055.cbl:L423];
    `pl060` then opens THE SAME FILE for INPUT [purchase/pl060.cbl:L421], reads
    those headers back [purchase/pl060.cbl:L425] and finally truncates it once the
    transfer to OTM5 is complete [purchase/pl060.cbl:L605-L606]. Threading it
    through a holder keeps `load000` returning the term code that `load08.` reads,
    while still letting the file the FIRST dispatch produced reach the second.

    WHY NOT A MODULE-LEVEL DEFAULT. `acas_posting/workfiles.py` deliberately
    declares a fresh file on every request and caches nothing, so that one run's
    records cannot leak into the next; a shared carrier at module scope would
    break rule R-6's byte-identical-reruns guarantee silently. This holder is
    created per call to `load08`, which preserves that property.

    WHO CREATES THE FILE. Not this class. `pl055.run` declares one when it is
    passed None and RETURNS it, so the first dispatch both produces the file and
    fills it; `load000` captures the returned value here and the second dispatch
    receives it. That is why this holder starts empty and why the type is
    `object`: the concrete class lives in `acas_posting/workfiles.py`, which a
    `cli` module may not import (Agent Action Plan section 0.4.3), and it never
    needs to - the carrier is only ever carried, never inspected.

    Attributes:
        carrier: the OTM4 work file once a dispatch has produced it, and None
            before that. Passed to every dispatch as-is: a None means "you
            declare it", which is exactly what each program module's own
            `open_item_file_4=None` default means.
    """

    __slots__ = ("carrier",)

    def __init__(self) -> None:
        """Start with no file. The first dispatch produces one."""
        self.carrier: object | None = None


def _run_unit_ended(term_code: int) -> bool:
    """Did `load000` already end the run unit? `if ws-term-code > 7`.

    NAMED, rather than written inline at the one place it is asked, because what it asks
    is easy to mistake for a gate and it is not one.

    Args:
        term_code: `WS-Term-Code` as the callee left it, read back out of the shared
            calling-data record.

    Returns:
        True when the dispatch ended the run unit, so no further program runs.
    """
    return args.is_serious_error(term_code)


def load000(
    linkage: args.SlPlLinkage,
    program_id: str,
    program: _ProgramEntry,
    *,
    menu_state: args.MenuState,
    channel: _ExtractChannel | None = None,
) -> int:
    """`load000.` [purchase/purchase.cbl:L691-L708] - the one dispatch paragraph.

    Purchase's own copy of the paragraph, reproduced statement by statement: clear the
    code, name the callee, call it with the five operands, then make the two tests over
    the result.

    Args:
        linkage: the five linkage operands, in COBOL order.
        program_id: the callee's program-id, `"pl055"` or `"pl060"`, moved into `WS-
            Called` exactly as [purchase/purchase.cbl:L759] and
            [purchase/purchase.cbl:L761] move it.
        program: the migrated callee's published `run`. In the COBOL the target comes
            from the field itself - `call ws-called` is a dynamic call by name - so the
            two travel together here.

    Returns:
        `WS-Term-Code` as the callee left it. The caller decides what that means:
        `_run_unit_ended` distinguishes the two bands the COBOL distinguishes.

    Note:
        The callee communicates its RESULTS through the shared linkage records,
        exactly as a COBOL sub-program does, so nothing about the posting is read
        off the return value. The one thing the return value can carry is the OTM4
        work file `pl055` declared - the migration's stand-in for the operating
        system supplying the file identity to two programs naming the same
        `ASSIGN` - and it is captured into `channel` rather than used.
    """
    # L694 `move zero to ws-term-code.` - BEFORE EVERY CALL, not once per route. R-4
    # [purchase/purchase.cbl:L694].
    args.reset_term_code(linkage.calling_data)

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
    #  [purchase/purchase.cbl:L695-L699]. This route has no promoted prompt, so no
    #  keyword argument is passed for one.
    #
    #  THE ONE KEYWORD THAT IS PASSED IS THE OTM4 FILE, and it is not an operand of
    #  the `CALL` at all - it is the migration's stand-in for the two programs
    #  naming the same `assign file-28`. See `_ExtractChannel`.
    returned = (
        program(*linkage)
        if channel is None
        else program(*linkage, open_item_file_4=channel.carrier)
    )

    #  The one conditional that is a Python-language necessity rather than a test
    #  of any value the COBOL tests. `pl055.run` returns the OTM4 file - the
    #  migration's equivalent of naming the same file in the next program's
    #  `SELECT` - while `pl060.run` returns None because it has nothing new to hand
    #  on. Capturing the first is what lets [purchase/pl060.cbl:L425] read what
    #  [purchase/pl055.cbl:L587] wrote.
    if channel is not None and returned is not None:
        channel.carrier = returned

    term_code = linkage.calling_data.ws_term_code

    if not args.is_serious_error(term_code):
        _LOG.debug(
            "load000: %s left ws-term-code %d; `perform overrewrite` "
            "[purchase/purchase.cbl:L701-L702] - persisting SYSTEM-REC (key 1) "
            "and SYSTOT-REC (key 4)",
            program_id,
            term_code,
        )
        args.overrewrite(linkage.system_record, menu_state, linkage.file_defs)

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
    #  PROOF OF EQUIVALENCE: the two agree on everything observable. The
    #  persistence runs on both sides; no further program is invoked on either
    #  side; control never returns to the dispatch paragraph on either side; and
    #  the code survives on both.
    #
    #  R-4, MECHANISM DIVERGENCE PRESERVED: Purchase transfers here
    #  [purchase/purchase.cbl:L703-L704]; Sales instead performs and returns,
    #  `perform overrewrite / goback` [sales/sales.cbl:L710-L712]. Same net
    #  effect, different mechanism, and they are left different - the transfer
    #  reaches `overrewrite.` [purchase/purchase.cbl:L621] and falls through
    #  `overclose.` [:L652] into `goback` [:L653], so the persistence runs and
    #  THEN the run unit ends, in that order.
    if args.is_serious_error(term_code):
        _LOG.error(
            "load000: %s reported a serious error, ws-term-code %d - "
            "`go to overrewrite` [purchase/purchase.cbl:L703-L704] persists both "
            "system records and then ends the run unit at `goback` "
            "[purchase/purchase.cbl:L653]; no further program is dispatched",
            program_id,
            term_code,
        )
        #  L704  go to overrewrite.  ->  purchase/purchase.cbl:L621-L636
        args.overrewrite(linkage.system_record, menu_state, linkage.file_defs)

    return term_code


def load08(linkage: args.SlPlLinkage, *, menu_state: args.MenuState) -> int:
    """`load08.` [purchase/purchase.cbl:L752-L762] - `pl055`, then `pl060`.

    Args:
        linkage: the five linkage operands. ONE instance for the whole route.

    Returns:
        `WS-Term-Code` after the last dispatch that ran - `pl060`'s normally, or
            `pl055`'s when `pl055` ended the run unit.
    """
    #  L759-L760  `move "pl055" to ws-called.` / `perform load000.`
    #  Phase one - the Purchase Invoice Post Extract, which builds the OTM4
    #  extract `pl060` then posts and writes the two period totals
    #  [purchase/pl055.cbl:L582] and [purchase/pl055.cbl:L584].
    #  THE OTM4 CHANNEL, created per route invocation rather than per dispatch,
    #  because the file outlives the first `CALL` and is read by the second.
    channel = _ExtractChannel()

    term_code = load000(
        linkage,
        _PL055,
        pl055_order_proof_extract.run,
        menu_state=menu_state,
        channel=channel,
    )

    # R-4 [purchase/purchase.cbl:L755-L758] - the `pl830` dispatch AND its `if ws-term-
    # code not = zero / go to display-menu` gate are BOTH COMMENTED OUT in the frozen
    # source.

    # NOT the gate above, and not a substitute for it.
    if _run_unit_ended(term_code):
        return term_code

    #  L761-L762  `move "pl060" to ws-called.` / `go to load000.`
    #  Phase two - the Purchase Orders Posting Report, including the IRS fan-out.
    #
    #  NOTHING MAY FOLLOW THIS. L760 is a `perform`, which comes back; L762 is a
    #  `go to`, which does not - the paragraph ends at the transfer, so there is
    #  no third statement to reproduce and no post-dispatch work to place after
    #  it. The `return` carries the code out for the process status.
    return load000(
        linkage,
        _PL060,
        pl060_order_posting.run,
        menu_state=menu_state,
        channel=channel,
    )


def _build_parser() -> argparse.ArgumentParser:
    """Compose this route's parser from the shared option fragments.

    What the fragments bring, and why each matters on this route: `--run-date` REQUIRED,
    and the only way a date enters (rule R-6). `--ws-caller` defaulted to the menu's own
    literal, `move "purchase" to ws-caller` [purchase/purchase.cbl:L475].

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
    """Run the Purchase transaction-posting route from the command line.

    THE LINKAGE IS BOUND ONCE, NOT PER DISPATCH. In the COBOL these five records are the
    menu shell's own storage, established before the first `CALL` and handed unchanged
    to the second [purchase/purchase.cbl:L695-L699].

    Args:
        argv: the argument vector, without the program name. The real process arguments
            when omitted, which is the case in a real run.

    Returns:
        The process exit status, which IS `WS-Term-Code` - 0 when the route completed, 8
            when `pl055` found no extract file.

    Raises:
        SystemExit: raised by argparse for `--help` and for a malformed argument
            vector, including a missing `--run-date`, and left to propagate with
            argparse's own status and its own message.
    `args.RdbmsParamError` - the deployment contract for the six connection
    parameters being absent or unusable - is CAUGHT here, and only that exact type
    (finding CLI-09). `args.report_configuration_failure` returns the one status
    every route of this package shares: 8 when the contract is absent, 1 when it is
    unusable. The reason an earlier draft let it propagate still stands as far as
    it went - a run that cannot reach the provisioned database must stop before it
    writes anything, rather than connect silently to the placeholder endpoint the
    frozen copybook declares [copybooks/wssystem.cob:L137-L144] - and it still
    does stop, before the store is opened and before any program is entered. What
    changed is only that the stop is now DIAGNOSABLE and identical across the seven
    routes instead of route-dependent. The status is not a `WS-Term-Code` value and
    is not claimed to be one; it is the migration's own boundary
    (Q-CLI-EXITSTATUS). `ValueError` at large is NOT caught.

    Note:
        A malformed run date is NOT rejected - `args.resolve_clock` reproduces
        the frozen date module falling through without touching its output field
        [common/maps04.cbl:L146] together with the caller pre-zero that turns
        "untouched" into zero [copybooks/Proc-ACAS-Mapser-RDB.cob:L78], so a date
        the legacy module refuses pins `Run-Date` to 0 and the run proceeds.
        Raising instead would add a validation and correct a defect, and this
        migration does neither (rules R-3 and R-4).
    """
    #  NOT INSTALLED HERE. `basicConfig` mutates the root logger, so a module that
    #  called it would reconfigure logging for everything that imported it -
    #  including a test session and any other process that reaches `load08` as a
    #  library. Only a process boundary has the standing to install it, and there
    #  are exactly two: the router, and this module's own guard through
    #  `run_entry_point`. Both call the one configurator in
    #  `acas_posting.__main__`, so the format and the level are the same on either
    #  route and are already in effect before the binding below reports anything.
    #  What `main` may do is ask that same configurator to SET THE LEVEL, and only
    #  when the operator supplied `--log-level`; see the block after the parse.
    namespace = _build_parser().parse_args(argv)

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

    #  `bind_slpl_linkage` pins the clock from the required `--run-date` and
    #  returns the five operands in COBOL order. `called` seeds `WS-Called` with
    #  the FIRST callee, matching the state the menu is in when it enters
    #  `load08` [purchase/purchase.cbl:L759]; each dispatch then sets the field
    #  itself.
    #  THE MENU'S OWN WORKING-STORAGE - one block for the route, owning
    #  `WS-System-Record-4`, which the binder hands to the linkage as its third
    #  argument. See `args.slpl_menu_state`.
    menu_state = args.slpl_menu_state()

    #  L346  aa005-Open-System.   L360  aa010-Get-System-Recs.
    #  THE RECORDS THE CALLEES MUST SEE, READ BEFORE ANYTHING IS DISPATCHED.
    #  Passing `menu_state` makes the binder perform `Open-System.` and
    #  `aa010-Get-System-Recs.` [purchase/purchase.cbl:L346-L398] first - file-key
    #  4 into `WS-System-Record-4` and file-key 1 into `System-Record`, TWO keys
    #  where the General Ledger shell reads three - so both programs receive the
    #  PERSISTED records. `pl055` ACCUMULATES into the period totals
    #  [purchase/pl055.cbl:L582] and [:L584] rather than initialising them, so
    #  binding declared defaults discarded every prior period's figures
    #  (finding CLI-02).
    #
    #  THE EXACT TYPE IS CAUGHT, NOT `ValueError` (finding CLI-09). The six
    #  connection parameters are resolved inside the binder before the store is
    #  opened, so a failure here has touched nothing.
    try:
        linkage = args.bind_slpl_linkage(
            namespace, called=_PL055, menu_state=menu_state
        )
    except args.RdbmsParamError as error:
        return args.report_configuration_failure(
            error, logger=_LOG, subject="Purchase order posting"
        )

    _LOG.info(
        "%s: pl055 then pl060, no gate between them "
        "[purchase/purchase.cbl:L752-L762]",
        _MENU_OPTION,
    )

    term_code = load08(linkage, menu_state=menu_state)

    # `term_code` IS `linkage.calling_data.ws_term_code` - the shared field the menu
    # reads after its own dispatch [purchase/purchase.cbl:L701],
    # [purchase/purchase.cbl:L703] - carried out as a value rather than re-read so that
    # the route's result and the status cannot disagree.
    return args.exit_status_for(term_code)


if __name__ == "__main__":  # pragma: no cover - module entry point
    #  ONE PROCESS BOUNDARY, SHARED WITH THE ROUTER. `run_entry_point` configures
    #  logging once and converts a failure into one sanitised ERROR record and a
    #  deterministic exit status, so no traceback, absolute path or exception
    #  payload can reach a terminal. `harness/run_python_scenario.sh` drives this
    #  module directly, so the direct route must get the same treatment as the
    #  routed one. The import is inside the guard because the router imports this
    #  module back when the router is the process.
    from acas_posting.__main__ import run_entry_point

    raise SystemExit(run_entry_point(main, command="pl-order-post"))


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
#       observable, the persistence included: `args.overrewrite` runs on this
#       branch and on the `< 8` one, as the frozen paragraph does.
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
#   * ONLY THE COBOL-FILE ARM of `overrewrite` purchase/purchase.cbl:L637-L649.
#     Its RELATIONAL arm L621-L636 - the persistence of `System-Record`
#     (File-Key-No 1) and `WS-System-Record-4` (File-Key-No 4) - IS reproduced, by
#     `args.overrewrite`, performed from both branches of `load000`, and the
#     matching `aa010-Get-System-Recs.` load is performed by the binder before the
#     first dispatch. `overclose.` L652 and its `goback` L653 are the return from
#     `main`. The migration has no ISAM store - see
#     `args.RDBMS_STORE_SELECTOR_DIGIT`.
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
#   Q-CLI-OVERREWRITE   SETTLED at the `< 8` branch of `load000`, by reproducing
#     the paragraph rather than by measuring the gap. `overrewrite` is the sole
#     persistence of SYSTEM-REC and SYSTOT-REC and SYSTOT-REC is where this
#     route's three period totals accumulate, so leaving it out could not satisfy
#     Agent Action Plan section 0.8.5's empty diff. `args.overrewrite` now runs on
#     both branches. What remains for the oracle is narrower and lives in
#     `cli/args.py` as Q-CLI-SYSREC-PINS.
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
