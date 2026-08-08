"""`python -m acas_posting` - the top-level router of the migrated posting cycle.

PROVENANCE. `common/ACAS.cbl`, 772 lines, `program-id. ACAS.`
[common/ACAS.cbl:L80] - the system-selection menu, the outermost program of the
frozen system. Agent Action Plan section 0.4.1.1 states this module's whole
mandate in one line:

    acas_posting/__main__.py | CREATE | common/ACAS.cbl | Top-level router
    mirroring the system-selection menu, MINUS ALL SCREEN I/O

`pyproject.toml` declares no `[project.scripts]`, so `python -m acas_posting` is
the single documented way into the package and this module is what makes it
work. Field-level traceability for every name below lives in
`docs/migration/traceability.md`.

WHAT IS ACTUALLY BEING MIGRATED. `ACAS.cbl` is a screen program wrapped around
one dispatch table. Section 0.3.4 of the plan gives a three-way rule for
removing the presentation layer, and almost every statement in the file falls
under its first or third branch: a diagnostic display with no database effect
becomes a log record, a prompt that gates a database write becomes an argument,
and a prompt that merely pauses for acknowledgement is dropped - keeping the
control transfer where one sits in an error path, and dropping only the pause.
Two things survive that filter, and they are the whole of this module:

  1. the dispatch table [common/ACAS.cbl:L558-L566], and
  2. the termination-code convention `load00` applies to what it called
     [common/ACAS.cbl:L573-L583].

THE DISPATCH TABLE, VERBATIM [common/ACAS.cbl:L558-L566]::

    go       to load08 load02 load03 load01
                load04
                loadsr2 loadsr2 loadsr2
                loaderror loaderror loaderror loaderror   *> x17 in total
                ...
                loaderror call-system-setup
             depending on z.

decoded by the maintainer's own comment immediately above it
[common/ACAS.cbl:L552-L556]::

    A=irs=08 , B=sales=02 , C=purchase=03 , D=General=01 ,
    E=stock=04 ,
    F=none, G=none, H=none= 5,6,7 Not avail for O/S versions.

so the live selections and the program name each `loadNN` moves into
`WS-Called` are:

    ==========  ==============  ==========  ==========================
    Selection   Paragraph       WS-Called   Disposition here
    ==========  ==============  ==========  ==========================
    A  IRS      load08 L627     "irs"       subsystem `irs`
    B  Sales    load02 L591     "sales"     subsystem `sales`
    C  Purchase load03 L597     "purchase"  subsystem `purchase`
    D  General  load01 L585     "general"   subsystem `general`
    E  Stock    load04 L603     "stock"     OMITTED - out of scope
    X  Exit     L512-L514       -           OMITTED - see `overclose`
    Z  Setup    L527-L539       "sys002"    OMITTED - out of scope
    ==========  ==============  ==========  ==========================

FOUR SUBSYSTEMS, NOT SEVEN. The letters are documented above and in each
subparser's help text rather than accepted as aliases, because an alias would
appear among argparse's own choice list and this router publishes exactly four
subsystem names and exactly seven operations - no eighth route exists.

THE TWO LEVELS. `ACAS.cbl` chooses a subsystem and calls its menu; that menu
then chooses an operation from its own `loadNN` table. A command line supplies
both selections at once, so this router is two levels deep and the seven
operations correspond one-for-one to the subsystem menus' own paragraphs::

    general  post-cycle    -> cli.gl_post_cycle
                              load08.    [general/general.cbl:L805-L815]
    general  end-of-cycle  -> cli.gl_end_of_cycle
                              load09.    [general/general.cbl:L817-L821]
    sales    invoice-post  -> cli.sl_invoice_post
                              load07.    [sales/sales.cbl:L756-L768]
    sales    cash-post     -> cli.sl_cash_post
                              load11.    [sales/sales.cbl:L792-L796]
    purchase order-post    -> cli.pl_order_post
                              load08.    [purchase/purchase.cbl:L752-L762]
    purchase payment-post  -> cli.pl_payment_post
                              load12.    [purchase/purchase.cbl:L786-L790]
    irs      post          -> cli.irs_post
                              Main-Loop. [irs/irs.cbl:L666-L672]

A LABEL CORRECTION, RECORDED SO IT IS NOT "CORRECTED" BACK. The Sales
invoice-posting chain is `load07.` [sales/sales.cbl:L756-L768], whose paragraph
label carries the maintainer's own inline `*> Sales trans posting`. Two planning
documents call it `load08`; `load08.` [sales/sales.cbl:L770-L774] actually
dispatches `sl080`, Payment Input, which plan section 0.2.2 places out of scope.
`acas_posting/cli/__init__.py` carries the same correction.

THIS ROUTER DELEGATES ITS ARGUMENTS AND OWNS NONE OF THEM, and that is a
reproduction rather than a convenience. `load00` calls the subsystem with no
parameters at all - its `USING` clause is commented out in the source
[common/ACAS.cbl:L577]::

    call     ws-called        *> using ws-calling-data system-record to-day.

The parameters appear one level down, in the subsystem menus. So this router
parses the subsystem and the operation and forwards every remaining argument
verbatim to the chosen entry point, which owns its own parser. Three
consequences follow, all of them wanted:

  * `01 WS-Calling-Data` [copybooks/wscall.cob:L6-L14] is bound in exactly one
    place, `acas_posting.cli.args`, and is not redefined here;
  * the three linkage shapes cannot be flattened, because no option declared
    here could be forced onto a route that does not take it - pass a
    calling-data option to the IRS route and the ROUTE refuses it, which is the
    shape asserting itself rather than this router policing it; and
  * `--help` after an operation reaches that route's own parser, so the help a
    reader sees is the route's real contract and never a second copy of it.

    One visible consequence of that last point: the delegated help names itself
    `python -m acas_posting.cli.<module>` rather than
    `python -m acas_posting <subsystem> <operation>`, because the parser
    answering is the route's. Both spellings are real invocations - every entry
    point carries its own `__main__` guard - and the route's `prog` is left
    alone rather than rewritten, because a second source for it is exactly the
    drift this delegation exists to prevent.

THREE LINKAGE SHAPES, NOT ONE (plan section 0.1.1)::

    General Ledger   4  ws-calling-data, system-record, to-day, file-defs
                        [general/general.cbl:L711-L721]
    Sales / Purchase 5  the same four plus WS-System-Record-4
                        [sales/sales.cbl:L698-L716]
                        [purchase/purchase.cbl:L691-L708]
    IRS              3  IRS-System-Params, WS-System-Record, file-defs -
                        no calling-data block and no `to-day`
                        [irs/irs.cbl:L666-L672], [irs/irs030.cbl:L552-L554]

On the third shape, note what "no run date" does and does not mean: it is true
of the PARAMETER LIST and false of the DATA, because two run-date fields still
reach `irs030` inside the two records it is passed. `cli.args` owns that
distinction; this router neither restates nor overrides it.

NO UNIFORM GATE IS IMPOSED HERE, AND THE THREE THAT EXIST DISAGREE. A later
reader must not "tidy" them into one:

    General Ledger  `if ws-term-code = 5 go to display-menu`
                    [general/general.cbl:L810-L811] - so `gl071` and `gl072`
                    never run at all; a hard gate between phases, not a warning
    Sales           `if ws-term-code not = zero go to display-menu`
                    [sales/sales.cbl:L761-L762], [sales/sales.cbl:L765-L766] -
                    a DIFFERENT predicate for the same idea
    Purchase        NO GATE - the equivalent lines are commented out in the
                    source [purchase/purchase.cbl:L755-L758]

Each gate belongs to its own entry point. This module holds only `load00`'s
`> 7` test, which is a different test again and is applied to every route
alike, exactly as `ACAS.cbl` applies it to every subsystem alike.

RECORDED OMISSIONS - listed so that a reader comparing the two trees does not
conclude something was lost (rule R-5 requires deliberate omissions be recorded
as omissions):

  * Stock Control, `load04.` [common/ACAS.cbl:L603-L607], `move "stock" to
    ws-called` - plan section 0.2.2 excludes `stock/**` in its entirety.
  * System Setup, `call-system-setup.` [common/ACAS.cbl:L527-L539], `move
    "sys002" to ws-called` at L534 - plan section 0.2.2 lists
    `common/sys002.cbl` under non-posting utilities. No route reaches it.
  * `(J) Project-Z` [common/ACAS.cbl:L496], `(F) Order Entry`
    [common/ACAS.cbl:L498], `(G) Payroll` [common/ACAS.cbl:L499] and
    `(H) Epos` [common/ACAS.cbl:L501] are COMMENTED OUT in the frozen source
    and are not live selections. Their paragraphs `load05`, `load06`, `load07`
    and `load09` [common/ACAS.cbl:L609-L636] survive but are unreachable: the
    dispatch table sends slots 6, 7 and 8 to `loadsr2` [common/ACAS.cbl:L560].
  * The `sl830` autogen leg, live at [sales/sales.cbl:L759] and already
    commented out on the Purchase side [purchase/purchase.cbl:L755-L758] -
    plan section 0.2.2 excludes the `sl800`..`sl830` series, so the Sales
    invoice route covers `sl055` then `sl060` only.
  * `load12.` [general/general.cbl:L835-L855], `gl100` then `gl105`, and the
    SECOND `if ws-term-code = 5` gate at [general/general.cbl:L844] - report
    programs, out of scope. Nothing here routes to it.
  * Every trace of the screen: `Display-Menu.` [common/ACAS.cbl:L427], the
    copyright and program banners [common/ACAS.cbl:L436-L440],
    [common/ACAS.cbl:L466-L467], the option displays
    [common/ACAS.cbl:L489-L504], `accept menu-reply ... auto UPPER`
    [common/ACAS.cbl:L510], the `loadsr`/`loadsr2` "Sorry" diagnostics
    [common/ACAS.cbl:L642-L652], `load23.` [common/ACAS.cbl:L637-L640] and
    `main-exit. stop run.` [common/ACAS.cbl:L654-L655].
  * BOTH CLOCK READS, deliberately and by rule. `accept wsb-time from time`
    [common/ACAS.cbl:L470] and `accept wsa-date from date`
    [common/ACAS.cbl:L478] feed the banner and nothing else - no database
    effect, no control flow - so under plan section 0.3.4 they are presentation
    and are dropped. This module therefore reads no clock at all, and neither
    supplies nor defaults a run date: rule R-6 requires two runs of one
    scenario to be byte-identical, and a router that defaulted the date would
    break that outright. Every route takes its run date as a required argument.
  * The presentation date conversion `Conv-date.` [common/ACAS.cbl:L441-L463]
    and `zz060-Convert-Date` [common/ACAS.cbl:L657-L680], which reformat
    between UK, USA and International forms for display only.
  * `gl051`'s control-total gate has NO entry point anywhere in `cli`, because
    plan section 0.4.1.1 lists none; it is reached as a library function,
    `acas_posting.programs.gl051_batch_control_check`. The frozen system
    reaches the whole interactive `gl051` through `load06.`
    [general/general.cbl:L790-L797], of which only the `end-batch` block
    [general/gl051.cbl:L1096-L1133] is in scope.
  * The version banner is not re-surfaced as an option. It is a display with no
    database effect, so plan section 0.3.4 makes it a diagnostic rather than an
    interface; `__version__` is reused from `acas_posting` in the help text
    below rather than re-declared or exposed as a second flag.

WHAT THIS MODULE MAY IMPORT (plan section 0.4.3). `acas_posting` itself, for
the version; `acas_posting.cli.*`; and the standard library. It must not, and
does not, import `programs`, `dal`, `records`, `cobol` or `dictionary` - it
sits above `cli` and reaches a program only through an entry point, exactly as
`ACAS.cbl` reaches `gl070` only through `general.cbl`.

NO COBOL RUNS HERE, AND NOTHING HERE CAN REACH ANY (rule R-1). There is no
process launch, no foreign-function binding, no compiler lookup and no import
of the sibling comparison tree - which is a sibling of this package precisely so
that no import path to it exists. In particular this router publishes NO switch
that would run the frozen programs, or run them alongside these and diff the
result: it is the one place such an option would look reasonable, and it would
violate R-1 outright. Comparison belongs entirely to that sibling tree, which
drives this package from outside and is never reached from within it.

Execution is strictly sequential and single-threaded, matching the original: one
selection, run once, and no option offering to run two of anything at a time.
"""

from __future__ import annotations

import argparse
import logging
from collections.abc import Callable, Mapping, Sequence
from typing import Final, NamedTuple, Protocol

from acas_posting import __version__

#  This module's own logger. Named for the module so that a caller can silence
#  or route the router's records independently of an entry point's.
_LOG: Final[logging.Logger] = logging.getLogger(__name__)

#  THE ONE RECORD FORMAT FOR THE WHOLE PACKAGE, declared here because this
#  module is the process boundary and the seven entry points read it from here
#  rather than each spelling their own. Level first so a record's severity is
#  greppable at the start of a line, then the logger name, which is the module
#  that emitted it and therefore the program-id or handler-id an operator is
#  looking for. NO TIMESTAMP: `asctime` reads the wall clock, and rule R-6 admits
#  exactly one time source - the pinned `--run-date` - so a timestamp would also
#  make two runs of one scenario differ textually.
LOG_FORMAT: Final[str] = "%(levelname)s %(name)s: %(message)s"

#: The level names `--log-level` accepts, in increasing severity.
LOG_LEVEL_NAMES: Final[tuple[str, ...]] = (
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
    "CRITICAL",
)

#  The level a run uses when `--log-level` is not given. INFO, so that the phase
#  announcements the frozen programs DISPLAY - "Phase - 1. Batch Check"
#  [general/gl070.cbl:L283] and its siblings - are visible and the file-handler
#  trace is not.
DEFAULT_LOG_LEVEL: Final[str] = "INFO"

#  Marks the root logger as configured BY THIS PACKAGE, so that a later explicit
#  `--log-level` may change the level while an embedding application's own setup
#  is never touched. It lives on the logger rather than in a module global so the
#  answer cannot depend on which copy of this module is asking.
_OWNED_MARKER: Final[str] = "_acas_posting_configured_logging"

#  `python -m acas_posting`, spelled once. argparse would otherwise derive
#  `prog` from `sys.argv[0]`, which for `-m` execution is the package
#  directory's path and therefore differs between checkouts - a usage or help
#  message must be identical on every host (rule R-6).
_PROG: Final[str] = "python -m acas_posting"


class _EntryPoint(Protocol):
    """What `call ws-called` [common/ACAS.cbl:L577] dispatches to.

    Every one of the seven modules of `acas_posting.cli` presents exactly this
    boundary, and presents nothing else that this router uses: `main` taking an
    argument vector without the program name and returning `WS-Term-Code` as a
    process exit status. A Protocol rather than an import of the seven concrete
    modules, so that the routing table can be typed without any of them being
    imported until the moment one is actually dispatched.
    """

    def main(self, argv: Sequence[str] | None = None) -> int:
        """Run the route and return `WS-Term-Code`.

        Args:
            argv: the argument vector for the route, without the program name.

        Returns:
            `WS-Term-Code` as the process exit status.
        """
        ...  # pragma: no cover - a Protocol body is never executed.


class _Subsystem(NamedTuple):
    """One live selection of the system-selection menu.

    Attributes:
        name: the subcommand this router publishes.
        letter: the key the frozen menu accepts for it, recorded for
            traceability only - it is documented, never accepted as an alias.
        ws_called: what the corresponding `loadNN` paragraph moves into
            `WS-Called`, verbatim from the frozen source.
        paragraph: the `ACAS.cbl` paragraph reproduced.
        locator: where that paragraph is.
        summary: the ledger name as the frozen menu displays it.
    """

    name: str
    letter: str
    ws_called: str
    paragraph: str
    locator: str
    summary: str


class _Route(NamedTuple):
    """One operation within a subsystem - a leaf of the two-level table.

    Attributes:
        subsystem: the owning `_Subsystem.name`.
        operation: the subcommand this router publishes for it.
        module: the `acas_posting.cli` module that owns the route, recorded so a
            diagnostic can name it without importing it.
        paragraph: the subsystem menu's own dispatch paragraph.
        locator: where that paragraph is.
        summary: help text - the programs run, and the gate between them.
    """

    subsystem: str
    operation: str
    module: str
    paragraph: str
    locator: str
    summary: str


class _Dispatch(NamedTuple):
    """The state a `loadNN` paragraph leaves behind for `load00` to act on.

    `load01.` [common/ACAS.cbl:L585-L589] is two statements - `move "general" to
    ws-called` and `go to load00` - so what one `loadNN` contributes is exactly
    the callee's identity. This carries that identity plus the resolved callee,
    because a command line names the operation as well as the subsystem and the
    module is what `load00` will call.

    Attributes:
        ws_called: the value moved into `WS-Called`, `pic x(8)`
            [copybooks/wscall.cob:L7].
        route: the resolved `acas_posting.cli` module.
        module_name: that module's name, for diagnostics.
    """

    ws_called: str
    route: _EntryPoint
    module_name: str


#  THE LIVE SELECTIONS  [common/ACAS.cbl:L558-L566], decoded at L552-L556.
#
#  Order is the frozen table's own - `load08 load02 load03 load01` - which is
#  the order the menu displays them in [common/ACAS.cbl:L489-L493]: A, then B,
#  then C, then D. Not alphabetical, and not the order of the paragraph numbers.
#  `load04` ("stock", L603-L607) is absent: plan section 0.2.2 excludes
#  `stock/**`. `call-system-setup` ("sys002", L527-L539) is absent: plan section
#  0.2.2 lists it under non-posting utilities. Slots 6, 7 and 8 - the
#  commented-out F, G and H options - resolve to `loadsr2` in the frozen table
#  [common/ACAS.cbl:L560] and are absent for that reason as well as by scope.
_SUBSYSTEMS: Final[tuple[_Subsystem, ...]] = (
    _Subsystem(
        name="irs",
        letter="A",
        ws_called="irs",
        paragraph="load08.",
        locator="common/ACAS.cbl:L627-L631",
        summary="Nominal Ledger (IRS)",
    ),
    _Subsystem(
        name="sales",
        letter="B",
        ws_called="sales",
        paragraph="load02.",
        locator="common/ACAS.cbl:L591-L595",
        summary="Sales Ledger",
    ),
    _Subsystem(
        name="purchase",
        letter="C",
        ws_called="purchase",
        paragraph="load03.",
        locator="common/ACAS.cbl:L597-L601",
        summary="Purchase Ledger",
    ),
    _Subsystem(
        name="general",
        letter="D",
        ws_called="general",
        paragraph="load01.",
        locator="common/ACAS.cbl:L585-L589",
        summary="General Ledger",
    ),
)

#  THE SEVEN OPERATIONS, one per subsystem-menu dispatch paragraph. Plan
#  sections 0.3.1 and 0.4.1.1 name the seven modules; these are the only routes
#  that exist, and there is no eighth. `acas_posting.cli.args` is the ninth
#  module of that package and is deliberately NOT a route: it is the library the
#  routes use, and its SECTION 0 carries the connection-parameter reader that
#  used to be a tenth module (finding M-01).
_ROUTES: Final[tuple[_Route, ...]] = (
    _Route(
        subsystem="general",
        operation="post-cycle",
        module="gl_post_cycle",
        paragraph="load08.",
        locator="general/general.cbl:L805-L815",
        summary=(
            "Post the General Ledger cycle: gl070, then the ws-term-code = 5 "
            "abort gate (general/general.cbl:L810-L811), then gl071, then "
            "gl072. The gate is hard: when it stops the cycle, gl071 and gl072 "
            "do not run at all."
        ),
    ),
    _Route(
        subsystem="general",
        operation="end-of-cycle",
        module="gl_end_of_cycle",
        paragraph="load09.",
        locator="general/general.cbl:L817-L821",
        summary=(
            "Run General Ledger end-of-cycle processing: gl080, transaction "
            "deletion and end-of-period. Two statements and NO gate."
        ),
    ),
    _Route(
        subsystem="sales",
        operation="invoice-post",
        module="sl_invoice_post",
        paragraph="load07.",
        locator="sales/sales.cbl:L756-L768",
        summary=(
            "Post Sales invoices: sl055, then the ws-term-code not = zero gate "
            "(sales/sales.cbl:L765-L766), then sl060. A DIFFERENT predicate "
            "from the General Ledger gate, reproduced and not harmonised. The "
            "sl830 autogen leg (sales/sales.cbl:L759) is out of scope."
        ),
    ),
    _Route(
        subsystem="sales",
        operation="cash-post",
        module="sl_cash_post",
        paragraph="load11.",
        locator="sales/sales.cbl:L792-L796",
        summary="Post Sales cash and receipts: sl100.",
    ),
    _Route(
        subsystem="purchase",
        operation="order-post",
        module="pl_order_post",
        paragraph="load08.",
        locator="purchase/purchase.cbl:L752-L762",
        summary=(
            "Post Purchase orders: pl055, then pl060, with NO GATE BETWEEN "
            "THEM - the equivalent lines are commented out in the frozen "
            "source (purchase/purchase.cbl:L755-L758). That divergence from "
            "the Sales route is preserved, not fixed."
        ),
    ),
    _Route(
        subsystem="purchase",
        operation="payment-post",
        module="pl_payment_post",
        paragraph="load12.",
        locator="purchase/purchase.cbl:L786-L790",
        summary="Post Purchase payments: pl100.",
    ),
    _Route(
        subsystem="irs",
        operation="post",
        module="irs_post",
        paragraph="Main-Loop. option 4",
        locator="irs/irs.cbl:L666-L672",
        summary=(
            "Post the transfer file to the IRS nominal ledger: irs030's "
            "Ledger-Postings-Add. The third linkage shape - three parameters, "
            "no calling-data block - so this route offers no calling-data "
            "options and has no term-code gate."
        ),
    ),
)


def loaderror(subsystem: str, operation: str) -> _Dispatch:
    """`loaderror.` [common/ACAS.cbl:L568-L571] - a selection outside the table.

    Two statements in the frozen source - the label and `go to display-menu` -
    which is to say: dispatch nothing and go back to the menu. Seventeen of the
    twenty-six slots of the dispatch table resolve here
    [common/ACAS.cbl:L561-L565], and so does any `z` the `search` did not set.

    UNREACHABLE HERE, BY CONSTRUCTION, AND THAT IS THE REPRODUCTION. The frozen
    menu refuses an unknown key silently - `if z = zero / go to accept-loop`
    [common/ACAS.cbl:L522-L523], no message of any kind - and argparse refuses an
    undeclared subcommand before this router dispatches anything, which is the
    same disposition: nothing runs. So this function can only be entered if the
    routing table and the parser ever disagreed about which operations exist,
    which is a defect in this module rather than a possible input. It therefore
    raises instead of returning, keeping the traceback that a genuine defect
    leaves behind, and invents no user-facing message for a case the frozen
    program has no message for.

    Args:
        subsystem: the subsystem that was selected.
        operation: the operation this router could not resolve within it.

    Raises:
        RuntimeError: always. The pair is named so the disagreement is obvious.
    """
    raise RuntimeError(
        f"no route for subsystem {subsystem!r} operation {operation!r}: the "
        "routing table and the argument parser disagree"
    )


def load01(operation: str) -> _Dispatch:
    """`load01.` [common/ACAS.cbl:L585-L589] - select the General Ledger.

    Two statements in the frozen source::

        L588      move     "general" to ws-called.
        L589      go       to load00.

    `general.cbl` then makes the second selection from its own dispatch table
    [general/general.cbl:L696-L704]. A command line supplies both at once, so the
    operation is resolved here and `load00` receives the callee itself.

    THE IMPORT IS DEFERRED AND THE DEFERRAL IS MEASURED, not stylistic. Importing
    one entry point costs roughly twice what importing `cli.args` alone costs,
    and importing all seven to answer `--help` would pay that for six routes that
    are not going to run. The import is still the FIRST thing the dispatch does,
    before any argument is bound, any connection opened or any program entered,
    so a broken import surfaces before any work rather than part-way through one.

    Args:
        operation: `post-cycle` or `end-of-cycle`.

    Returns:
        The callee's identity and the resolved module.
    """
    if operation == "post-cycle":
        #  general/general.cbl load08. L805-L815 - gl070, the `= 5` gate, gl071,
        #  gl072. The gate is the route's, not this router's.
        from acas_posting.cli import gl_post_cycle

        return _Dispatch("general", gl_post_cycle, "gl_post_cycle")
    if operation == "end-of-cycle":
        #  general/general.cbl load09. L817-L821 - gl080, and no gate.
        from acas_posting.cli import gl_end_of_cycle

        return _Dispatch("general", gl_end_of_cycle, "gl_end_of_cycle")
    return loaderror("general", operation)


def load02(operation: str) -> _Dispatch:
    """`load02.` [common/ACAS.cbl:L591-L595] - select the Sales Ledger.

    `move "sales" to ws-called` [common/ACAS.cbl:L594] then `go to load00`.
    `sales.cbl` makes the second selection from its own table.

    Note which paragraph each operation reproduces: `invoice-post` is `load07.`
    [sales/sales.cbl:L756-L768], NOT `load08.`, which dispatches the
    out-of-scope `sl080` [sales/sales.cbl:L770-L774]. See the module docstring.

    Args:
        operation: `invoice-post` or `cash-post`.

    Returns:
        The callee's identity and the resolved module.
    """
    if operation == "invoice-post":
        #  sales/sales.cbl load07. L756-L768 - sl055, the `not = zero` gate,
        #  sl060. A DIFFERENT gate predicate from the General Ledger's `= 5`
        #  [general/general.cbl:L810-L811]; both are reproduced as they are.
        from acas_posting.cli import sl_invoice_post

        return _Dispatch("sales", sl_invoice_post, "sl_invoice_post")
    if operation == "cash-post":
        #  sales/sales.cbl load11. L792-L796 - sl100.
        from acas_posting.cli import sl_cash_post

        return _Dispatch("sales", sl_cash_post, "sl_cash_post")
    return loaderror("sales", operation)


def load03(operation: str) -> _Dispatch:
    """`load03.` [common/ACAS.cbl:L597-L601] - select the Purchase Ledger.

    `move "purchase" to ws-called` [common/ACAS.cbl:L600] then `go to load00`.

    Args:
        operation: `order-post` or `payment-post`.

    Returns:
        The callee's identity and the resolved module.
    """
    if operation == "order-post":
        #  purchase/purchase.cbl load08. L752-L762 - pl055 then pl060 with NO
        #  gate between them: the equivalent lines are commented out at L755-L758.
        #  The divergence from the Sales route is preserved, not fixed (rule R-4).
        from acas_posting.cli import pl_order_post

        return _Dispatch("purchase", pl_order_post, "pl_order_post")
    if operation == "payment-post":
        #  purchase/purchase.cbl load12. L786-L790 - pl100.
        from acas_posting.cli import pl_payment_post

        return _Dispatch("purchase", pl_payment_post, "pl_payment_post")
    return loaderror("purchase", operation)


def load08(operation: str) -> _Dispatch:
    """`load08.` [common/ACAS.cbl:L627-L631] - select the IRS nominal ledger.

    `move "irs" to ws-called` [common/ACAS.cbl:L630] then `go to load00`. This is
    selection `A`, the FIRST slot of the dispatch table
    [common/ACAS.cbl:L558] - the paragraph numbering does not follow the menu
    order, which is why the maintainer wrote the decode comment at L552-L556.

    `irs.cbl` differs from the other three menus in shape as well as in name: it
    has no `loadNN` paragraphs at all and calls each program inline from
    `Main-Loop`, so this operation reproduces the option-4 branch
    [irs/irs.cbl:L666-L672] rather than a numbered paragraph. That branch passes
    THREE parameters and no run date [irs/irs030.cbl:L552-L554]; the route owns
    that shape and this router imposes nothing on it.

    Args:
        operation: `post`.

    Returns:
        The callee's identity and the resolved module.
    """
    if operation == "post":
        from acas_posting.cli import irs_post

        return _Dispatch("irs", irs_post, "irs_post")
    return loaderror("irs", operation)


#  `go to load08 load02 load03 load01 ... depending on z`
#  [common/ACAS.cbl:L558-L566], in the frozen table's own order. The computed
#  `go to` becomes a lookup because `z` is set by a `search` over the accepted
#  keys [common/ACAS.cbl:L519-L521]: the frozen program indexes a table of
#  selections, and so does this.
_LOAD_IT: Final[Mapping[str, Callable[[str], _Dispatch]]] = {
    "irs": load08,
    "sales": load02,
    "purchase": load03,
    "general": load01,
}


def load_it(subsystem: str, operation: str) -> _Dispatch:
    """`load-it.` [common/ACAS.cbl:L547-L566] - index the dispatch table.

    Two statements: `move space to menu-reply` [common/ACAS.cbl:L550], which
    clears the accepted key so a re-display does not show the last selection -
    presentation, and therefore dropped - and the computed `go to` itself.

    Args:
        subsystem: the selected subsystem name.
        operation: the selected operation within it.

    Returns:
        What the selected `loadNN` paragraph left for `load00`.

    Raises:
        RuntimeError: through `loaderror`, if the table and the parser disagree.
    """
    select = _LOAD_IT.get(subsystem)
    if select is None:
        #  568  loaderror.   571      go to display-menu.
        return loaderror(subsystem, operation)
    return select(operation)


def accept_loop(
    parser: argparse.ArgumentParser, argv: Sequence[str] | None
) -> tuple[str, str, list[str], str]:
    """`accept-loop.` [common/ACAS.cbl:L508-L525] - take one selection.

    The frozen paragraph, and what becomes of each statement::

        L510  accept   menu-reply at 0644 ... auto UPPER   -> the command line
        L512  if       menu-reply = "X"
        L514           go to pre-overrewrite.              -> see `overrewrite`
        L519  search   a-entry
        L520           when a-entry (q) = menu-reply
        L521           set z to q.                         -> argparse's choices
        L522  if       z = zero
        L523           go to accept-loop.                  -> CLASS 1 loop-back
        L525  go       to load-it.                         -> `load_it`

    CLASS 1, LOOP-BACK [common/ACAS.cbl:L522-L523]. Under the four-class
    taxonomy of plan section 0.4.2 a backward transfer to the head of an input
    loop becomes `continue` inside `while True:`. Here the loop has exactly one
    iteration and no `continue` appears, because the thing being iterated is a
    terminal read that this migration removes: a command line supplies its one
    selection once and cannot be re-prompted. WHAT IS PRESERVED IS THE CONTROL
    TRANSFER, WHICH IS WHAT PLAN SECTION 0.3.4 REQUIRES - on an unrecognised key
    the frozen menu dispatches NOTHING, and on an undeclared subcommand argparse
    exits before this router dispatches anything.

    AND THE SILENCE IS PRESERVED WITH IT. The frozen program prints no message
    whatever for a bad key - it re-draws and waits. So nothing here invents one:
    argparse's own "invalid choice" is left to do the refusing, no message of
    this module's own is added, and there is no fall-back to a default
    subsystem.

    `parse_known_args` rather than `parse_args`, because everything after the
    operation belongs to the route and must reach it untouched - including
    `--help`, which the leaf parsers decline to intercept so that the route's own
    parser answers it. That is `call ws-called` with no `USING` clause
    [common/ACAS.cbl:L577]: this level passes nothing of its own.

    Args:
        parser: the router's parser.
        argv: the argument vector without the program name; None reads
            `sys.argv[1:]`, which is what argparse does by default.

    Returns:
        The subsystem name, the operation name, every remaining argument in the
        order given - to be forwarded verbatim - and the diagnostic level, which
        is not part of the selection but is read from the same parse because it
        must be applied before anything is dispatched.

    Raises:
        SystemExit: raised by argparse for `--help` and for a usage error -
            an absent, unknown or ambiguous selection. Deliberately not caught:
            refusing to dispatch is the behaviour being reproduced.
    """
    namespace, route_argv = parser.parse_known_args(argv)
    #  Both attributes are guaranteed present: each `add_subparsers` call below
    #  sets `required=True`, so argparse has already exited if either selection
    #  is missing. Read positionally through `getattr` for nothing - they are
    #  plain attributes - so read them plainly.
    return (
        namespace.subsystem,
        namespace.operation,
        list(route_argv),
        namespace.log_level,
    )


def overrewrite(dispatch: _Dispatch, term_code: int) -> None:
    """`overrewrite.` [common/ACAS.cbl:L542] - the `> 7` disposition of `load00`.

    The frozen tail of this program is three consecutive labels and a `goback`,
    and ALL THREE LABELS ARE EMPTY [common/ACAS.cbl:L541-L545]::

        L541  pre-overrewrite.     *> Don't need to save system data as done by
                                   *> called menu program.
        L542  overrewrite.
        L544  overclose.
        L545      goback.

    The comment at L541 is the maintainer's own and gives the reason: the
    subsystem menu has already persisted the system records, so the outer program
    has nothing left to write. That is why this is ONE function with one real
    statement rather than three empty ones - three empty functions would be
    inventing structure, not reproducing it. `pre-overrewrite` and `overclose`
    contribute no statements, and `goback` is the return.

    CLASS 2, FORWARD TERMINATOR. Plan section 0.4.2 requires a forward transfer
    to a terminating label become `break` PLUS faithful placement of the work
    that follows the label. The work that follows this one is empty, as above, so
    there is nothing to place - and that is recorded here precisely so a reader
    does not go looking for it.

    THE SAME TAIL SERVES SELECTION `X`. `if menu-reply = "X" / go to
    pre-overrewrite` [common/ACAS.cbl:L512-L514] is the clean exit, and it
    reaches these same empty labels. There is consequently no `exit` subcommand
    to publish: a command that runs one operation and returns has no menu to
    leave, and publishing one would add surface the frozen program does not have.

    Args:
        dispatch: what was called, for the record.
        term_code: the reported `WS-Term-Code`, above the threshold.
    """
    #  A diagnostic with no database effect becomes a log record at a severity
    #  matching the original's intent (plan section 0.3.4) - and the intent is
    #  recorded in the frozen source in as many words: "Got a serious (reported)
    #  error" [sales/sales.cbl:L691]. It must not alter control flow, and does
    #  not: the caller returns the code either way.
    _LOG.error(
        "%s reported a serious error: WS-Term-Code=%d is above the threshold "
        "of 7 [common/ACAS.cbl:L578-L579]",
        dispatch.ws_called,
        term_code,
    )


def load00_exit(dispatch: _Dispatch, term_code: int) -> None:
    """`load00-exit.` [common/ACAS.cbl:L581-L583] - the `<= 7` disposition.

    One statement, `go to display-menu` [common/ACAS.cbl:L583]: the selection
    finished without a serious error, so the frozen program re-draws the menu and
    waits for the next one. A command line has no next selection, so the
    equivalent is to return - the run unit ends because there is nothing else to
    do, not because anything failed.

    Note that this is the branch a General Ledger abort arrives on. The abort
    code is 5 [general/general.cbl:L810-L811], which is `< 8`, so it is NOT a
    serious error by `load00`'s test and is surfaced as the exit status rather
    than as a failure here. The two tests are different tests and both are kept.

    Args:
        dispatch: what was called, for the record.
        term_code: the reported `WS-Term-Code`, at or below the threshold.
    """
    _LOG.debug(
        "%s returned WS-Term-Code=%d; the frozen menu would re-display "
        "[common/ACAS.cbl:L583] and there is no next selection",
        dispatch.ws_called,
        term_code,
    )


def load00(
    dispatch: _Dispatch,
    route_argv: Sequence[str],
    *,
    log_level: str = DEFAULT_LOG_LEVEL,
) -> int:
    """`load00.` [common/ACAS.cbl:L573-L583] - call the selection, test the code.

    The whole paragraph, verbatim from the frozen source::

        L573  load00.
        L576      move     zero to ws-term-code.
        L577      call     ws-called   *> using ws-calling-data system-record to-day.
        L578      if       ws-term-code > 7
        L579               go to overrewrite.
        L581  load00-exit.
        L583      go       to display-menu.

    THE `USING` CLAUSE IS COMMENTED OUT AT L577, AND THAT IS THE WHOLE REASON
    THIS ROUTER OWNS NO ARGUMENTS. The outer program hands its callee nothing;
    the parameters appear one level down, in the subsystem menus - four for the
    General Ledger [general/general.cbl:L711-L721], five for Sales and Purchase
    [sales/sales.cbl:L698-L716], three for IRS [irs/irs.cbl:L666-L672]. So the
    remaining argument vector is forwarded verbatim to the route, which owns its
    own parser, and no option declared here could be forced onto a shape that
    does not take one.

    ANOMALY, REPRODUCED AND NOT FIXED (rule R-4): IN THE FROZEN PROGRAM THIS
    TEST CAN NEVER BE TRUE. `WS-Calling-Data` reaches `ACAS.cbl` through
    `copy "wscall.cob"` in its WORKING-STORAGE [common/ACAS.cbl:L226],
    [common/ACAS.cbl:L268], and reaches `general.cbl` through the same copybook
    in ITS working storage [general/general.cbl:L285]; neither program declares a
    `PROCEDURE DIVISION USING` [common/ACAS.cbl:L343],
    [general/general.cbl:L361]. With the `USING` clause commented out at L577
    there is no linkage between the two copies, so `WS-Term-Code` here is set to
    zero at L576, the callee can only ever change its own copy, and the test at
    L578 reads the zero it just moved. `overrewrite` is therefore dead code
    reached from this paragraph, and every dispatch falls through to
    `load00-exit`.

    The same test IS live twice in the same program, and the difference is
    exactly the `USING` clause: `call ws-called using ws-calling-data file-defs`
    then `if ws-term-code > 7 / stop run` at [common/ACAS.cbl:L387-L392] and
    again at [common/ACAS.cbl:L535-L538]. So the dead one at L578 is an
    oversight, not a convention - and it is reproduced rather than removed.

    WHY REPRODUCING IT IS BEHAVIOUR-PRESERVING RATHER THAN A CHANGE. The
    migration boundary is different here: a COBOL `CALL` with no `USING` cannot
    return a code, whereas a Python entry point returns one, so the value that
    was unobservable in the frozen program is observable in this one. Making the
    test live changes nothing that can be observed in the database or in the
    dispatch, on three independent grounds:

      * both branches do the same thing - `overrewrite`, `overclose` and the `X`
        exit are all EMPTY [common/ACAS.cbl:L541-L545], for the reason the
        maintainer records at L541, so the `> 7` branch performs no work the
        other does not;
      * this router dispatches exactly one selection, so `go to display-menu`
        [common/ACAS.cbl:L583] and `goback` [common/ACAS.cbl:L545] both end the
        run unit; and
      * the code is returned unchanged on either branch, so the test decides
        only which record is logged, and plan section 0.3.4 requires a
        diagnostic never to alter control flow.

    Keeping the test therefore costs nothing and preserves the structure the
    specification has, including a place to report a serious error at a severity
    matching the original's intent. What is NOT done is to invent a disposition
    the frozen program has not got - the status is not banded, not re-encoded and
    not translated.

    THE EXIT STATUS IS `WS-Term-Code` ITSELF. `acas_posting.cli.args.exit_status_for`
    is the identity and its own documentation states that nothing downstream may
    re-encode the value, so the int an entry point returns IS `WS-Term-Code`.
    That is what makes `args.is_serious_error` applicable to it, and why this
    function returns it untouched rather than mapping it a second time. The
    domain is safe: `WS-Term-Code` is `pic 99` [copybooks/wscall.cob:L10], so
    0..99, entirely inside the 0..255 a process status carries.

    Args:
        dispatch: the callee's identity and module, from a `loadNN` paragraph.
        route_argv: every argument after the operation, forwarded verbatim.
        log_level: the diagnostic level `run_entry_point` configures before the
            route is entered. Records only; it reaches no program.

    Returns:
        `WS-Term-Code` as the process exit status - zero when the selection
        completed, 5 when the General Ledger abort gate stopped the cycle
        [general/general.cbl:L810-L811], and the reported code otherwise.

    Raises:
        SystemExit: raised by the route's own parser for `--help` and for a usage
            error, such as an omitted `--run-date`. Deliberately not caught: an
            omitted run date must fail, because the only alternative to a
            supplied date is an ambient one (rule R-6).
    """
    #  Imported here rather than at module scope so that `--help` does not pay
    #  for it: `cli.args` pulls the record layouts and the clock behind it. It is
    #  imported before the dispatch below, so a broken import cannot surface
    #  part-way through a run.
    from acas_posting.cli import args

    #  576  move     zero to ws-term-code.
    #  Reproduced as the local's only initial value. In COBOL the reset matters
    #  because `WS-Term-Code` is a field the callee might overwrite; here the
    #  callee RETURNS the code, so the reset and the call are the same statement
    #  and `args.WS_TERM_CODE_DEFAULT` - which is the value the record itself
    #  declares, not a typed-in zero - is what the local holds if the call
    #  returns nothing meaningful. Reading it from `args` rather than writing `0`
    #  keeps this module and the record's own declaration from disagreeing.
    term_code: int = args.WS_TERM_CODE_DEFAULT

    _LOG.debug(
        "load00: dispatching %s (%s) with %d forwarded argument(s) "
        "[common/ACAS.cbl:L577]",
        dispatch.ws_called,
        dispatch.module_name,
        len(route_argv),
    )

    #  577  call     ws-called   *> using ... - COMMENTED OUT in the frozen
    #  source, which is why nothing of this router's own is passed. `list(...)`
    #  because the route's `main` takes a sequence and argparse expects a list;
    #  copying also guarantees the route cannot mutate the caller's vector.
    #
    #  THROUGH THE ONE SANITISED BOUNDARY. `run_entry_point` configures logging
    #  and converts an escaping `Exception` into a deterministic status with one
    #  ERROR record and no traceback, path or payload - the same boundary a route
    #  invoked directly as `python -m acas_posting.cli.<name>` passes through, so
    #  the two invocation routes cannot behave differently.
    term_code = run_entry_point(
        dispatch.route.main,
        list(route_argv),
        command=dispatch.ws_called,
        log_level=log_level,
    )

    #  578-579  if ws-term-code > 7 / go to overrewrite.
    #  The threshold is `args.SERIOUS_ERROR_THRESHOLD`, read from the one module
    #  that owns it, so the router and the seven routes cannot disagree about
    #  where the boundary is. See the anomaly note above: this branch is dead in
    #  the frozen program and is kept anyway.
    if args.is_serious_error(term_code):
        overrewrite(dispatch, term_code)
    else:
        #  581  load00-exit.   583      go to display-menu.
        load00_exit(dispatch, term_code)

    return term_code


def configure_logging(level: str = DEFAULT_LOG_LEVEL) -> None:
    """Configure logging for this process. THE ONLY `basicConfig` IN THE PACKAGE.

    Called from the two places that are genuinely a process boundary - this
    module's `main`, and `run_entry_point` when one of the seven entry-point
    modules is executed directly as `python -m acas_posting.cli.<name>` - and,
    for the level alone, from each entry point's own `main` when the operator
    supplied `--log-level` there. No other module in `acas_posting` configures
    logging, so a library import cannot reconfigure its host application and the
    format cannot drift between routes.

    WHY A SECOND CALL MUST BE ABLE TO SET THE LEVEL. `basicConfig` alone made
    `--log-level` INERT on every route: a run enters through `run_entry_point`,
    which configures `DEFAULT_LOG_LEVEL` before the entry point has parsed
    anything, and the entry point's later call was then a no-op against a root
    logger that already had a handler. An operator could ask for DEBUG and
    silently get INFO. A diagnostic knob that does nothing is worse than no knob,
    because it invites the wrong conclusion from a quiet log.

    `force` is deliberately NOT passed, so the three arms below are: handler
    absent - install the format and the level and mark the root logger as ours;
    handler present and ours - set the level, an explicit request being more
    specific than the boundary default; handler present and NOT ours - change
    nothing, so the host wins.

    Args:
        level: one of `LOG_LEVEL_NAMES`. An unrecognised name falls back to
            `DEFAULT_LOG_LEVEL` rather than raising, because a diagnostic setting
            must not be able to stop a posting run (rule R-3).

    Returns:
        None.
    """
    chosen = level.upper() if level else DEFAULT_LOG_LEVEL
    if chosen not in LOG_LEVEL_NAMES:
        chosen = DEFAULT_LOG_LEVEL

    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(level=getattr(logging, chosen), format=LOG_FORMAT)
        setattr(root, _OWNED_MARKER, True)
        return
    if getattr(root, _OWNED_MARKER, False):
        root.setLevel(getattr(logging, chosen))


def _serious_error_threshold() -> int:
    """Return `load00`'s gate value, read from the one module that declares it.

    Imported inside the function rather than at module scope so that importing
    the router costs nothing: `cli.args` resolves its field metadata from the
    generated data dictionary while it is being imported, and the router must
    stay side-effect free on import.

    Returns:
        `cli.args.SERIOUS_ERROR_THRESHOLD`, which is 7 [common/ACAS.cbl:L578],
        or 7 when `cli.args` cannot be imported at all - which would itself
        already have failed the run.
    """
    try:
        from acas_posting.cli import args
    except Exception:  # noqa: BLE001 - a status must not depend on an import
        return 7
    return int(args.SERIOUS_ERROR_THRESHOLD)


def _failure_status(error: BaseException) -> int:
    """Return the deterministic exit status for a failure that reached the boundary.

    The `return_code` attribute is read reflectively rather than by importing the
    exception class, for the same reason `cli/gl_post_cycle.py` reads it that
    way: the per-directory import table of plan section 0.4.3 does not grant this
    module a path to `cli.args`, which is reached only through
    `cli.args`.

    Args:
        error: the failure. Only its `return_code` attribute is consulted;
            neither its type nor its message affects the result.

    Returns:
        The error's own frozen return code when it carries one - which
        `cli.args.RdbmsParamError` does, holding the parameter loader's 8
        for "contract absent" and 1 for "contract unusable"
        [common/acas-get-params.cbl:L37-L42] - otherwise the smallest status the
        frozen menu treats as a serious error, `ws-term-code > 7`
        [common/ACAS.cbl:L578].
    """
    return_code = getattr(error, "return_code", None)
    if isinstance(return_code, int):
        return return_code
    return _serious_error_threshold() + 1


def run_entry_point(
    entry: Callable[[Sequence[str] | None], int],
    argv: Sequence[str] | None = None,
    *,
    command: str,
    log_level: str = DEFAULT_LOG_LEVEL,
) -> int:
    """Run one entry point at the process boundary, converting failure to status.

    THE ONE SANITISED BOUNDARY. Called by `main` for a routed command and by each
    of the seven `cli` modules' `if __name__ == "__main__":` guards, so a route
    behaves identically whether it was reached through
    `python -m acas_posting general post-cycle` or through
    `python -m acas_posting.cli.gl_post_cycle`. The second is not a convenience:
    `pyproject.toml` declares no `[project.scripts]`.

    WHAT IT CATCHES, AND WHY THAT SET. `Exception` - broadly and on purpose. A
    process boundary is the one place where a broad catch is right, because the
    alternative is a traceback on stderr, and a traceback here would print
    absolute filesystem paths, the source lines of this migration and whatever
    text the exception carries, which for a driver error is the statement and its
    literal values (CWE-209, CWE-532). The record emitted instead names the
    command, the exception's TYPE and the two ACAS status fields when the
    exception carries them - all closed vocabularies of this migration - and NOT
    `str(error)`. `SystemExit` and `KeyboardInterrupt` derive from
    `BaseException` and are therefore not caught: the first is argparse's own
    path for `--help` and for a usage error such as an omitted `--run-date`, and
    the second is the operator ending the run.

    THE LIBRARY CONTRACT IS UNCHANGED. `entry` is the module's `main`, and `main`
    still raises when it is called as a library. Only this wrapper converts, and
    only this wrapper is on the process boundary.

    Args:
        entry: the module's `main`, taking an argument vector and returning
            `WS-Term-Code`.
        argv: the argument vector without the program name, or None to read
            `sys.argv[1:]`.
        command: the routed command name, for the log record. A constant.
        log_level: the level to configure before dispatching.

    Returns:
        `entry`'s own return value, unchanged, when it returns; otherwise the
        deterministic status of `_failure_status`.
    """
    configure_logging(log_level)
    try:
        return entry(argv)
    except Exception as error:  # noqa: BLE001 - see "WHAT IT CATCHES" above
        status = _failure_status(error)
        #  ONE record. No traceback (`exc_info` is deliberately absent), no
        #  `str(error)`, no path and no payload. `type(error).__name__` is a class
        #  name from this migration or from the driver, so it is a short
        #  identifier rather than data; `fs_reply` and `we_error` are read
        #  reflectively because only `dal.status.AcasFileHandlerError` carries
        #  them, and they are small closed integer vocabularies.
        _LOG.error(
            "%s: the run failed and was not completed - %s "
            "(fs-reply=%s we-error=%s); exiting %d. The exception detail is "
            "deliberately not reported here: it can carry a statement, a row "
            "key or an account name. Re-run the command as a library call to "
            "obtain the traceback.",
            command,
            type(error).__name__,
            getattr(error, "fs_reply", "-"),
            getattr(error, "we_error", "-"),
            status,
        )
        return status


def _build_parser() -> argparse.ArgumentParser:
    """Build the two-level router: four subsystems, seven operations.

    `Display-Menu.` [common/ACAS.cbl:L427-L440] and the option displays
    [common/ACAS.cbl:L489-L504] become this parser - the same set of selections,
    with none of the screen. The subsystems are added in the frozen table's own
    order [common/ACAS.cbl:L558], which is the order the menu lists them: A, B,
    C, D. `sorted()` is deliberately not applied; the order is the
    specification's.

    THE LEAVES DECLARE NO ARGUMENTS AND DECLINE `-h`. `add_help=False` is what
    lets `--help` after an operation fall through to the route's own parser, so
    the help a reader sees is that route's real contract rather than a second
    copy of it that could drift. It is also what keeps the three linkage shapes
    apart: with no option declared at this level, none can be forced onto a shape
    that does not accept it - notably the IRS shape, which takes no calling-data
    block at all [irs/irs030.cbl:L552-L554].

    NO ALIASES, so that the choice list is exactly the four subsystem names and
    the seven operation names. The frozen menu's letters are documented in each
    subsystem's help text instead of being accepted, because an alias would
    appear among argparse's own choices and this router publishes no route the
    plan does not name.

    Returns:
        The router's parser. Both subcommand levels are `required=True`, so
        argparse refuses an absent selection before anything is dispatched.
    """
    parser = argparse.ArgumentParser(
        prog=_PROG,
        description=(
            f"ACAS posting cycle {__version__} - batch entry points migrated "
            "from COBOL to Python.\n\n"
            "Mirrors the system-selection menu of common/ACAS.cbl "
            "(program-id ACAS) with no screen output of any kind. Pick a "
            "subsystem and an operation; every remaining argument is passed "
            "straight to that operation, which documents its own options:\n\n"
            f"    {_PROG} SUBSYSTEM OPERATION --help\n\n"
            "The frozen menu's own selection letters, for reference: "
            + ", ".join(
                f"({subsystem.letter}) {subsystem.name}"
                for subsystem in _SUBSYSTEMS
            )
            + ". They are documented, not accepted - use the names."
        ),
        epilog=(
            "EXIT STATUS is WS-Term-Code itself (copybooks/wscall.cob:L10, "
            "pic 99), surfaced unchanged and never re-encoded: 0 when the "
            "operation completed, 5 when the General Ledger abort gate stopped "
            "the cycle (general/general.cbl:L810-L811), above 7 when the "
            "operation reported a serious error (common/ACAS.cbl:L578-L579), "
            "and 2 when this router refused the selection.\n\n"
            "THREE LEDGERS, THREE DIFFERENT GATES, DELIBERATELY NOT "
            "HARMONISED: General Ledger tests ws-term-code = 5; Sales tests "
            "not = zero; Purchase has no gate at all, its equivalent lines "
            "being commented out in the frozen source. Each gate belongs to "
            "its own operation; this router imposes none.\n\n"
            "NO RUN DATE IS SUPPLIED OR DEFAULTED HERE. Every operation "
            "requires its run date as an argument so that two runs of one "
            "scenario are byte-identical; no clock is read anywhere in this "
            "router.\n\n"
            "Out of scope and therefore absent: Stock Control, System Setup "
            "(sys002), and the Order Entry, Payroll, Epos and Project-Z "
            "options that are commented out in common/ACAS.cbl. See "
            "docs/migration/traceability.md."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    #  DIAGNOSTIC VERBOSITY, AND NOTHING ELSE. It carries no COBOL counterpart
    #  and reaches no program: `configure_logging` applies it at the boundary
    #  before the operation is dispatched, and each operation declares the same
    #  option itself through `args.add_log_level_argument` so that a level given
    #  after the operation still wins. It is declared here rather than forwarded
    #  because a router that accepted it silently and ignored it would be a knob
    #  that does nothing.
    parser.add_argument(
        "--log-level",
        choices=LOG_LEVEL_NAMES,
        default=DEFAULT_LOG_LEVEL,
        help=(
            "Diagnostic verbosity for the whole run "
            f"(default: {DEFAULT_LOG_LEVEL}). Affects records only - never "
            "which programs run, which rows are written or the exit status."
        ),
    )

    #  `search a-entry / when a-entry (q) = menu-reply / set z to q`
    #  [common/ACAS.cbl:L519-L521] - the table of accepted selections. `required`
    #  reproduces the fact that the frozen menu will not proceed without one.
    subsystems = parser.add_subparsers(
        dest="subsystem",
        metavar="SUBSYSTEM",
        required=True,
    )

    for subsystem in _SUBSYSTEMS:
        subsystem_parser = subsystems.add_parser(
            subsystem.name,
            help=f"({subsystem.letter}) {subsystem.summary}",
            description=(
                f"{subsystem.summary} - selection ({subsystem.letter}) of the "
                f"frozen menu, dispatched by {subsystem.paragraph} "
                f"[{subsystem.locator}], which moves "
                f'"{subsystem.ws_called}" to WS-Called.'
            ),
            epilog=(
                "Every argument after the operation is forwarded to it "
                f"unchanged. Run `{_PROG} {subsystem.name} OPERATION --help` "
                "for that operation's own options."
            ),
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        operations = subsystem_parser.add_subparsers(
            dest="operation",
            metavar="OPERATION",
            required=True,
        )
        for route in _ROUTES:
            if route.subsystem != subsystem.name:
                continue
            #  `add_help=False` and NO arguments: this leaf exists only to name
            #  the selection. Everything else, `--help` included, belongs to
            #  `acas_posting.cli.{route.module}`.
            operations.add_parser(
                route.operation,
                help=f"{route.paragraph} [{route.locator}]",
                add_help=False,
            )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """The command-line boundary of the migrated posting cycle.

    What the frozen program has here is `procedure division.`
    [common/ACAS.cbl:L343] followed by a screen: it opens the system file,
    offers to run the parameter set-up program if that fails
    [common/ACAS.cbl:L387-L392], draws a menu, reads a key and dispatches. All of
    the screen is removed rather than reimplemented (plan section 0.3.4) and this
    function stands in its place: one selection, made on the command line, run
    once, non-interactively and sequentially.

    The four statements below are the four surviving paragraphs, in the frozen
    program's own order: take the selection [common/ACAS.cbl:L508-L525], index
    the dispatch table [common/ACAS.cbl:L547-L566], set the callee's identity
    [common/ACAS.cbl:L585-L631], and call it while testing the returned code
    [common/ACAS.cbl:L573-L583].

    NOT MIGRATED, and named here so the omission is visible: the pre-flight open
    of the system file and its fall-back call to `sys002`
    [common/ACAS.cbl:L387-L412] - `sys002` is out of scope by plan section 0.2.2,
    and its `Value`/`Anal` set-up sibling `sl070` [common/ACAS.cbl:L408-L410] is
    likewise outside the posting cycle. Each route resolves its own connection
    parameters through `acas_posting.cli.args`, so nothing here needs to.

    Args:
        argv: the argument vector WITHOUT the program name. None reads
            `sys.argv[1:]`, which is what argparse does by default and what a
            real invocation wants; a test passes a list.

    Returns:
        `WS-Term-Code` as the process exit status, unchanged. This function does
        not call `sys.exit`, so it is callable in process and its result can be
        asserted on.

    Raises:
        SystemExit: from argparse - status 0 for `--help` at any level, status 2
            for a selection this router refuses or for a usage error inside the
            chosen route. Not caught at either level: refusing to dispatch is the
            behaviour being reproduced [common/ACAS.cbl:L522-L523], and a route's
            required arguments must be able to fail.
        RuntimeError: from `loaderror`, if this module's routing table and its
            parser ever disagreed about which operations exist.
        Exception: propagated unchanged from the dispatched operation.
    """
    #  508  accept-loop.
    #  Parsed BEFORE logging is configured, so that `--log-level` can be honoured
    #  on the very first record. Configuring at import time would reconfigure
    #  logging for every importer, including the suites that import an entry
    #  point to drive its dispatch paragraph directly.
    parser = _build_parser()
    subsystem, operation, route_argv, log_level = accept_loop(parser, argv)

    #  THE ONLY SIDE EFFECT THIS MODULE PERFORMS, AND IT PERFORMS IT HERE, ONCE.
    #  `configure_logging` is the package's single `basicConfig`; a caller that
    #  configured logging itself keeps its own setup.
    configure_logging(log_level)

    #  547  load-it.   558  go to load08 load02 load03 load01 ... depending on z.
    #  585/591/597/627  loadNN.  -  move "<name>" to ws-called.
    dispatch = load_it(subsystem, operation)

    #  573  load00.  -  and the code it returns is the code this returns.
    return load00(dispatch, route_argv, log_level=log_level)


if __name__ == "__main__":
    #  `python -m acas_posting` runs this file as `__main__`, and `pyproject.toml`
    #  declares no `[project.scripts]`, so this guard is the packaged entry to the
    #  whole cycle. `sys.exit` raises `SystemExit`, so a status argparse already
    #  raised propagates unchanged and a status `main` returned becomes the
    #  process status - `WS-Term-Code` either way.
    import sys

    sys.exit(main())
