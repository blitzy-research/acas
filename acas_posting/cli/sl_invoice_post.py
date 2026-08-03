"""Sales transaction posting: `sl055`, then the `not = zero` gate, then `sl060`.

The batch entry point for the Sales invoice posting route. It reproduces one
paragraph of the Sales menu shell - `load07.` [sales/sales.cbl:L756-L768] - and
its dispatch helper `load000.` [sales/sales.cbl:L698-L712], with no screen output
of any kind.

THE PARAGRAPH IS `load07`, AND IT IS NOT `load08`
=================================================
Two planning documents label this route `load08`, and both are wrong. The frozen
source settles it four times over, so this correction is stated here, at the top
of the file, rather than buried in the footer:

  1. THE MAINTAINER'S OWN INLINE COMMENT SITS ON THE LABEL LINE::

         L756  load07.             *> Sales trans posting

     Nothing else in sales/sales.cbl is annotated "Sales trans posting".
  2. `load08.` DISPATCHES A DIFFERENT AND OUT-OF-SCOPE PROGRAM::

         L770  load08.
         L773       move     "sl080" to ws-called.
         L774       go       to load00.

     `sl080` is Payment Input, which Agent Action Plan section 0.2.2 places
     explicitly out of scope.
  3. THE MENU-LETTER ORDINAL PROVES IT. Each menu accepts one character and
     resolves it to a paragraph by position - `go to load01 load02 ... depending
     on z` [sales/sales.cbl:L670] - so the Nth letter selects `loadNN`. The
     display block has `"(G)  Sales Transactions Post"` at
     [sales/sales.cbl:L545], and G is the SEVENTH letter, therefore `load07`.
     `"(H)  Payment Input"` at [sales/sales.cbl:L546] is the eighth, therefore
     `load08`, and `"(K)  Payment Post"` at [sales/sales.cbl:L549] is the
     eleventh, therefore `load11` - which is the sibling `sl_cash_post` route.
  4. TWO CHANGE-HISTORY ENTRIES NAME IT. ".32 Added execution of sl830 first when
     Invoice Post selected." [sales/sales.cbl:L121], matching the `sl830` head of
     `load07`; and, decisively, ".33 Call in load07 to 830 should have been using
     load00 not 000." [sales/sales.cbl:L124], in which the maintainer names
     `load07` AS the invoice-post paragraph and dates the very `perform load00`
     at L760 that stands there today.

Do not "correct" `load07` back to `load08`. The sibling package marker carries
the same note [acas_posting/cli/__init__.py], and so does the oracle driver
script - `'sl_invoice_post:sales:G:load07:sales/sales.cbl:L756-L768'`
[run_cobol_scenario.sh:L251].

THE ROUTE, VERBATIM FROM THE FROZEN SOURCE
==========================================
::

    L756  load07.             *> Sales trans posting
    L759       move     "sl830" to WS-Called.   *> In case autogen is use
    L760       perform  load00.
    L761       if       ws-term-code not = zero
    L762                go to display-menu.
    L763       move     "sl055" to ws-called.
    L764       perform  load000.
    L765       if       ws-term-code not = zero
    L766                go to display-menu.
    L767       move     "sl060" to ws-called.
    L768       go       to load000.

Three properties of that paragraph are load-bearing and are preserved exactly:

  * `perform load000` at L764 RETURNS, so the gate at L765-L766 is reachable;
    `go to load000` at L768 does NOT return, so NO CODE MAY FOLLOW the final
    dispatch. `load07` therefore ends with its second dispatch and nothing else.
  * the two dispatches share ONE `WS-Calling-Data` and ONE pair of system
    records - only `WS-Called` changes between them - because COBOL passes group
    items by reference. One `SlPlLinkage` instance serves both, which is what
    lets `sl055`'s period-total writes reach `sl060`.
  * `sl830` is out of scope, so this route dispatches `sl055` -> gate ->
    `sl060` and the `load00` head of the chain (L759-L762) is not migrated. It is
    recorded as an omission in the footer rather than silently dropped, and the
    oracle driver script documents the same asymmetry under "THE sl830
    ASYMMETRY" [run_cobol_scenario.sh:L332-L336].

THE DISPATCH HELPER, AND ITS FIVE PARAMETERS
============================================
Both in-scope dispatches go through `load000.`, the FIVE-parameter shape::

    L698  load000.
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

FIVE, not four. The callee declares the same five, in the same order:
`procedure division using ws-calling-data / system-record / system-record-4 /
to-day / file-defs` [sales/sl060.cbl:L395-L399] and identically at
[sales/sl055.cbl:L271-L275]. What Shape 2 adds to the General Ledger's Shape 1
is exactly `WS-System-Record-4` - `SYSTOT-REC` [copybooks/wssys4.cob], the
period-totals record that this route's two programs write. Agent Action Plan
section 0.4.1.1 calls this "the four-parameter SL/PL linkage shape"; that is a
slip, recorded as CORRECTION 2 in the footer, and section 0.1.1 has it right -
"The Sales and Purchase families add the fourth system record".

The maintainer's own comment at L708 names the beneficiaries of this paragraph:
`*> for sl055 & 060, xl150`.

`< 8` AND `> 7` ARE EXHAUSTIVE, so `load000` ALWAYS performs `overrewrite`:
`WS-Term-Code` is `pic 99` [copybooks/wscall.cob:L10], domain 0 through 99, over
which the two tests are complementary. The `> 7` case additionally `goback`s,
which ends the RUN UNIT - the menu program itself stops.

FOUR GATE FORMS, DELIBERATELY NOT HARMONISED  (rule R-4)
========================================================
The predicate here is `not = zero`, and it is not the predicate its siblings use.
The four forms the frozen source actually contains:

  Sales     `if ws-term-code not = zero / go to display-menu`
            [sales/sales.cbl:L765-L766] - ANY non-zero code stops the chain.
  General   `if ws-term-code = 5 / go to display-menu`
            [general/general.cbl:L810-L811] - an EQUALITY test against the one
            abort code `gl070` raises [general/gl070.cbl:L289].
  Purchase  NO PARAGRAPH-LEVEL GATE AT ALL. `load08.`
            [purchase/purchase.cbl:L752-L762] runs `pl055` through `load000` and
            falls straight into `pl060` with nothing tested in between.
  load000   `if ws-term-code > 7 / perform overrewrite / goback`
            [sales/sales.cbl:L710-L712] - a THRESHOLD test that ends the run unit
            instead of returning to the menu.

Harmonising any of them would be a behaviour change, and under rule R-4 a
behaviour change is a failure: "A defect reproduced is correct; a defect fixed is
a failure." Each form is reproduced where the source puts it.

THE FOURTH DIVERGENCE: THE GATE IS LIVE ONLY FOR CODES 1 THROUGH 7
==================================================================
`sl055` sets `WS-Term-Code` to EIGHT, and only ever to eight. Its one raise site
is the branch taken when the GnuCOBOL file-existence built-in it calls at
[sales/sl055.cbl:L336-L337] reports the analysis extract missing::

    sales/sl055.cbl
    L338       if    return-code not = zero
    L339             display  SL125  at 2301
    L340             display  SL002  at 2401
    L341             if     WS-Caller not = "xl150"
    L342                    accept WS-Reply at 2435
    L343             end-if
    L344             move 8 to WS-Term-Code
    L345             goback

Trace eight through `load000`: it is not `< 8`, and it IS `> 7`, so control takes
L710-L712 - `perform overrewrite`, then `goback` - and the menu PROGRAM ENDS.
The `not = zero` gate at L765-L766 is therefore NEVER REACHED for code eight. It
is reachable only for codes 1 through 7, which `sl055` never raises. A census of
every `move ... to ws-term-code` in the in-scope programs finds exactly three
raises: 5 at [general/gl070.cbl:L289], 8 at [sales/sl055.cbl:L344] and 8 at
[purchase/pl055.cbl:L286].

Three consequences, all encoded rather than reasoned away:

  * BOTH STOPS ARE IMPLEMENTED. The `> 7` stop belongs to `load000` and ends the
    run unit; the `not = zero` gate belongs to `load07` and returns to the menu.
    They are different dispositions in the source and both are written here.
  * THE GATE IS NOT SIMPLIFIED TO "if 8". The COBOL predicate is `not = zero`,
    so a code of 3 stops this chain exactly as a code of 8 does.
  * THE SALES-VERSUS-PURCHASE DIVERGENCE LIVES ENTIRELY IN THE 1..7 BAND. Sales
    returns to the menu for any non-zero code at or below seven; Purchase, having
    no gate, would proceed to `pl060`. Because `sl055` and `pl055` only ever raise
    eight the difference is currently unobservable - but it is reproduced anyway,
    because any other code in that band would diverge.

THE CLOCK CONTRACT  (rule R-6)
==============================
The run date enters this route ONCE, as the REQUIRED `--run-date` option, and
reaches the two programs only through the linkage. Nothing here reads a system
clock, an elapsed-time counter, an environment variable or an entropy source, and
neither do the twelve in-scope posting programs: the single clock read in the
whole call chain lives in the menu shells' date-service copybook
[copybooks/Proc-ACAS-Mapser-RDB.cob:L72-L80], which builds `to-day` at L77 and
stores the binary `run-date` at L80. Both observables are pinned by
`acas_posting.clock` through `acas_posting.cli.args.resolve_clock`, so two runs of
one scenario are byte-identical (Agent Action Plan section 0.8.5).

PIN `--irs-instead` EXPLICITLY ON THIS ROUTE
============================================
`SYSTEM-REC IRS-Instead pic x` [copybooks/wssystem.cob:L179] with its two
condition names, `88 IRS-Used value "Y"` at L180 and `88 IRS-Both-Used value "B"`
at L181, decides WHICH TABLES the run touches: `sl060` reads it at three sites -
[sales/sl060.cbl:L1039], [sales/sl060.cbl:L1126] and [sales/sl060.cbl:L1175] -
to choose between the General Ledger posting tables, the IRS posting table, or
both. Agent Action Plan section 0.6.4 therefore requires every scenario to pin it
explicitly, "since leaving it out makes the affected-table list ambiguous". The
option comes from `args.add_slpl_linkage_arguments` and is not redefined here.

WHAT THIS MODULE MAY AND MAY NOT IMPORT
=======================================
MAY, and does: `argparse`, `enum`, `logging`, `collections.abc`, `typing`;
`acas_posting.cli.args`; and the two program modules this route dispatches. The
per-directory import table of Agent Action Plan section 0.4.3 allows `cli/*.py`
exactly `programs`, `clock` and `cli.args`.

MAY NOT, and does not: the data-access layer including its facade, the record
layer, the COBOL-semantics package, the dictionary package, the work-file module,
and the compiled comparison oracle's own tree. (The forbidden names are given in
prose here on purpose: this module states its constraints without spelling any
banned import, so that the mechanical greps a reviewer runs over it come back
empty rather than needing to be read.) Two consequences are visible in the code
rather than merely promised:

  * `acas_posting.clock` is PERMITTED but NOT IMPORTED, because it is already
    reached through `args.bind_slpl_linkage` -> `args.resolve_clock`. An import
    this module did not use would be dead weight, and the clock contract is not
    weakened by routing through the one module whose job is binding.
  * the private dispatch protocol types its five record parameters as `Any`. The
    record classes would name those types exactly, but the record layer is
    outside this layer's whitelist, and `args` deliberately does not re-export
    them. The five parameter NAMES carry the shape instead, and the real types are
    enforced where they belong - in `args.SlPlLinkage`, whose members this module
    splats without touching.

NO IMPORT-TIME SIDE EFFECTS
===========================
Importing this module binds names and creates one logger. It builds no parser,
configures no logging, opens no file or connection, reads nothing from its
surroundings and cannot fail for an environmental reason. `logging.basicConfig`
is called only inside `main`, so importing the module never reconfigures a host
application's logging. That is a hard requirement: the scenario test suites
import this package.

NEITHER CALLEE'S FAILURE IS TRANSLATED
======================================
Two exceptions can leave this module, and both are allowed to propagate
deliberately:

  * `sl055` raises `CobolFileSystemPathUnavailable` when
    `FS-Cobol-Files-Used` is true, having first set `WS-Term-Code` to eight per
    [sales/sl055.cbl:L344]. It raises because the three sub-outcomes of the
    file-existence block [sales/sl055.cbl:L336-L346] cannot be told apart
    without running COBOL, which rule R-1 forbids. Catching it here and returning
    eight would PICK one of those three outcomes - a behaviour change dressed as
    a migration - so it is not caught.
  * `args.bind_slpl_linkage` raises `RdbmsParamError` when the deployment
    contract for the six connection parameters is absent or unusable. `args`
    states the contract: deliberately not caught, because a run that cannot reach
    the provisioned database must stop BEFORE it writes anything.

Neither is a COBOL disposition, so neither is mapped onto a `WS-Term-Code`. They
end the process loudly and before any posting, which is the only faithful
outcome available.

THE RULES THAT BIND THIS FILE
=============================
`review_rules` reports NO user rules document for this project, so the binding
constraints are the Agent Action Plan's own six (section 0.7.2), and enterprise
best practice applies wherever they are silent. The per-rule verdict is in the
footer; in outline:

R-1 No COBOL at run time. Nothing here spawns a child process, loads a foreign
    library or reaches the GnuCOBOL toolchain; there is no import path from this
    package to the compiled oracle's tree, and no option selects, invokes or
    diffs against that oracle - the oracle's own scripts drive this entry point
    from outside, never the reverse.
R-2 Zero binary floating point. `WS-Term-Code` is an `int` (`pic 99`), `to-day`
    is a `str`, and no binary-radix numeric type appears anywhere - in a
    signature, an option type or an expression. No arithmetic is performed here.
R-3 No added validation, no added field, no schema change, no concurrency. In
    particular there is NO "does the extract file exist?" pre-check here: that
    test lives inside `sl055` [sales/sl055.cbl:L336-L346] and duplicating it
    would be a validation this migration may not add. There is no worker, pool
    or event loop to configure and no option that would create one, so the two
    programs run one at a time with the gate between them.
R-4 Legacy behaviour is reproduced, never corrected - see the four gate forms
    above. Each reproduction below carries its COBOL locator in a comment, as
    section 0.7.4 C-4 requires.
R-5 Full traceability: paragraph-named functions, a `GO TO` class at every
    transfer site, and the mandatory footer.
R-6 Compiled behaviour is the tie-breaker, so the clock is injected, the run date
    is a required argument, and the three open questions are marked in place
    rather than guessed.
"""

from __future__ import annotations

import argparse
import enum
import logging
from collections.abc import Sequence
from typing import Any, Final, Protocol

from acas_posting.cli import args
from acas_posting.programs import sl055_invoice_extract_analysis, sl060_invoice_posting

__all__: Final[tuple[str, ...]] = ("main", "load000", "load07")

#  Diagnostics only. Agent Action Plan section 0.3.4 turns a display with no
#  database effect into "a log record at a severity matching the original's
#  intent" that "must not alter control flow and must not appear in any table
#  dump". Every call below obeys both halves of that: nothing branches on a log
#  record, and nothing logged reaches a column. `print` is never used.
_LOG: Final[logging.Logger] = logging.getLogger(__name__)


#  THE TWO PROGRAM-IDS THIS ROUTE MOVES INTO `WS-Called`
#  Named constants rather than inline literals so that the `move` each one
#  reproduces has one spelling and one locator. Both are five characters, which
#  `args.set_called` space-fills to the eight of `WS-Called pic x(8)`
#  [copybooks/wscall.cob:L7].
_PROGRAM_SL055: Final[str] = "sl055"  # sales/sales.cbl:L763
_PROGRAM_SL060: Final[str] = "sl060"  # sales/sales.cbl:L767

#  R-4 [sales/sales.cbl:L765] - the figurative constant ZERO of
#  `if ws-term-code not = zero`. Read out of the record layer's own declared
#  default through `args`, never typed as a literal, so the comparison value
#  cannot drift from `WS-Term-Code pic 99` [copybooks/wscall.cob:L10]. It is an
#  `int`, never a binary-radix numeric type (rule R-2).
_WS_TERM_CODE_ZERO: Final[int] = args.WS_TERM_CODE_DEFAULT


class _Stop(enum.Enum):
    """The two DIFFERENT dispositions that stop this route, named.

    The source contains both and they are not the same event, so each has a name
    here rather than living only in a comment (rule R-5). What they share is the
    observable outcome at a headless boundary - the operation ends, no further
    program is dispatched, and the process leaves with the term code - and what
    they do not share is where the stop is decided and what the COBOL then does
    with the terminal.

    Attributes:
        RUN_UNIT_ENDED: `if ws-term-code > 7 / perform overrewrite / goback`
            [sales/sales.cbl:L710-L712], decided INSIDE `load000`. `goback` from
            the menu's own paragraph ends the RUN UNIT: the menu program stops
            and no further selection is possible. This is the disposition
            `sl055`'s term code of eight actually takes.
        RETURNED_TO_MENU: `if ws-term-code not = zero / go to display-menu`
            [sales/sales.cbl:L765-L766], decided in `load07`. The menu is redrawn
            and awaits the next selection; the program does NOT end. Live only
            for codes 1 through 7 - see the module docstring.
    """

    RUN_UNIT_ENDED = "run unit ended (perform overrewrite / goback)"
    RETURNED_TO_MENU = "returned to the menu (go to display-menu)"


class _SlPlPostingProgram(Protocol):
    """What `call ws-called` dispatches: a program module exposing `run`.

    `call ws-called using ...` [sales/sales.cbl:L702-L707] is a DYNAMIC call by
    name - the callee is whatever program-id the field holds. The migrated
    equivalent passes the program MODULE itself, and `load000` reads `run` off it
    at dispatch time, which keeps two properties of the original:

      * the dispatch is late-bound, exactly as a dynamic `CALL` is; and
      * a caller cannot reach into a program's internals, because a program
        module publishes `run` and nothing else - `__all__ = ("run",)` in both
        [acas_posting/programs/sl055_invoice_extract_analysis.py] and
        [acas_posting/programs/sl060_invoice_posting.py]. Agent Action Plan
        section 0.3.3: "Callers cannot reach into a program's internals, exactly
        as a COBOL `CALL` cannot."

    The five record parameters are typed `Any` because the record layer is
    outside this layer's import whitelist (Agent Action Plan section 0.4.3) and
    `args` does not re-export the classes. Their NAMES carry the shape, and the
    real types are enforced by `args.SlPlLinkage`, whose five members this module
    splats without inspecting. `to_day` keeps its `str` type, which needs no
    record import and is the observable rule R-2 cares about.
    """

    def run(
        self,
        ws_calling_data: Any,
        system_record: Any,
        system_record_4: Any,
        to_day: str,
        file_defs: Any,
    ) -> None:
        """Run the program over the five-parameter Sales/Purchase linkage."""
        ...  # pragma: no cover - a Protocol member has no body to execute


def _overrewrite_omitted(*, program_id: str, term_code: int) -> None:
    """Record that `perform overrewrite` [sales/sales.cbl:L709, :L711] is omitted.

    THE STATEMENT IS REACHED; ITS EFFECT IS NOT REPRODUCED, and that is a
    recorded omission rather than an oversight. `overrewrite.`
    [sales/sales.cbl:L628-L658] opens the system parameter file, rewrites key 1
    (`SYSTEM-REC`) and key 4 (`SYSTOT-REC`) to the RDB and then again to the
    Cobol file, and closes - falling through `overclose.` [sales/sales.cbl:L659]
    to its `goback` at L660. Three provisions put that out of this module's
    reach, and they agree:

      * sales/sales.cbl is a menu program, and Agent Action Plan section 0.2.2
        places the menu programs explicitly out of scope;
      * the persistence needs the data-access layer, which section 0.4.3's import
        table bars `cli/*.py` from reaching; and
      * adding the write to the program layer instead is barred by rule R-3,
        because none of the twelve in-scope posting programs performs any
        system-record or totals-record I/O.

    So the two period-total writes `sl055` and `sl060` make - [sales/sl055.cbl:L675]
    and [sales/sl055.cbl:L677], [sales/sl060.cbl:L641] and [sales/sl060.cbl:L700] -
    land in the linkage record and are not persisted by this route. `SYSTEM-REC`
    and `SYSTOT-REC` therefore belong to each scenario's seeded state and to its
    declared affected-table list; the scenario driver owns that boundary. The
    sibling `args` module records the same decision as Q-CLI-SYSREC-LOAD, and the
    open question this raises is marked at the statement below.

    Args:
        program_id: the program-id just dispatched, for the log record only.
        term_code: `WS-Term-Code` as the callee left it, for the log record only.
    """
    # AMBIGUITY Q-CLI-OVERREWRITE: the Cobol run rewrites SYSTEM-REC and
    # SYSTOT-REC after every dispatch of this route - twice per dispatch when both
    # stores are in use - whereas the Python run leaves both rows as the seed left
    # them. Confirm against the compiled oracle which columns of those two rows a
    # Sales invoice post actually moves, so that each scenario can either declare
    # them out of its diff or seed them to the post-run state; record the
    # resolution in docs/migration/ambiguity-resolutions.md (rule R-6).
    #
    #  DEBUG, not INFO: this is the absence of an effect, and section 0.3.4
    #  forbids a diagnostic from altering control flow. It alters none - the
    #  caller ignores the return - and it reaches no column.
    _LOG.debug(
        "overrewrite omitted after %s (WS-Term-Code %d): SYSTEM-REC and SYSTOT-REC "
        "are not persisted by this route [sales/sales.cbl:L628-L660]",
        program_id.strip(),
        term_code,
    )


def _log_stop(stop: _Stop, *, program_id: str, term_code: int) -> None:
    """Report which of the two stops fired, at a severity matching its intent.

    `WARNING` rather than `ERROR`: neither stop is an error of this module's
    making, and the callee has already reported whatever went wrong - `sl055`
    logs its own `SL125` before raising, for instance. The record names the
    COBOL disposition so that a reader of the run log can tell the run-unit end
    from the menu return, which is the whole reason `_Stop` exists.

    Args:
        stop: which disposition the source takes at this site.
        program_id: the program-id whose term code caused the stop.
        term_code: the deciding `WS-Term-Code`.
    """
    #  "no further program is dispatched" rather than "sl060 is not dispatched":
    #  either stop can occur after EITHER dispatch, and naming the wrong callee
    #  would be a diagnostic that misreports the run.
    _LOG.warning(
        "%s left WS-Term-Code %d: %s; no further program is dispatched",
        program_id.strip(),
        term_code,
        stop.value,
    )


def load000(
    linkage: args.SlPlLinkage,
    program_id: str,
    program: _SlPlPostingProgram,
) -> int:
    """`load000.` [sales/sales.cbl:L698-L712] - the five-parameter dispatch.

    Reproduces the paragraph statement for statement::

        L698  load000.
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

    The `< 8` and `> 7` tests are written as the source writes them - two
    separate statements, not a two-armed conditional - because that is what they
    are, and because `WS-Term-Code pic 99` [copybooks/wscall.cob:L10] makes them
    exhaustive over 0..99: `overrewrite` is therefore performed on EVERY path
    through this paragraph, once for a clean run and once for a serious error.

    Args:
        linkage: the five arguments in COBOL parameter order
            [sales/sl060.cbl:L395-L399]. Mutated: `WS-Term-Code` is cleared and
            `WS-Called` is set before the dispatch, and the callee writes back
            into the same records, which is what COBOL linkage by reference does.
            ONE instance serves both dispatches of `load07`.
        program_id: the program-id to move into `WS-Called` - `"sl055"` or
            `"sl060"` here.
        program: the program module to dispatch. `run` is read off it at call
            time, so the dispatch is late-bound exactly as `call ws-called` is.

    Returns:
        `WS-Term-Code` as the callee left it, which is also readable from
        `linkage.calling_data.ws_term_code`. The caller MUST NOT dispatch
        anything further when `args.is_serious_error` is true of it: that is the
        `goback` of L712, whose only faithful expression across a function
        boundary is a return the caller honours.

    Raises:
        Nothing of its own. Whatever the callee raises propagates unchanged -
        `sl055` can raise `CobolFileSystemPathUnavailable` after setting
        `WS-Term-Code` to eight [sales/sl055.cbl:L344] - because mapping either
        exception onto a term code would invent a disposition the COBOL does not
        have. See the module docstring.
    """
    calling_data = linkage.calling_data

    #  R-4 [sales/sales.cbl:L701] `move zero to ws-term-code.`
    #  PER DISPATCH, not once per run. The placement is load-bearing rather than
    #  tidy: `WS-Term-Code` is shared linkage storage, so a code the previous
    #  callee left behind would still be there for the next test of it - and on
    #  this route that test decides whether `sl060` runs at all.
    args.reset_term_code(calling_data)

    #  R-4 [sales/sales.cbl:L763] and [sales/sales.cbl:L767]
    #  `move "sl055" to ws-called.` / `move "sl060" to ws-called.`
    #  HOISTED from the two call sites into this function, which is where the
    #  program-id arrives, because this function IS `call ws-called` - the
    #  dispatch takes the program-id as an argument where the COBOL reads it back
    #  out of the field. The order relative to the reset above is immaterial: the
    #  two statements write DIFFERENT fields of the group and nothing reads
    #  either between them.
    args.set_called(calling_data, program_id)

    _LOG.info(
        "dispatching %s over the five-parameter Sales/Purchase linkage "
        "[sales/sales.cbl:L702-L707]",
        program_id.strip(),
    )

    #  [sales/sales.cbl:L702-L707] `call ws-called using ws-calling-data /
    #  System-Record / WS-System-Record-4 / to-day / file-defs`.
    #  FIVE positional arguments in COBOL parameter order, and no others: the
    #  splat of a five-member NamedTuple makes an arity mistake a TypeError at
    #  this line rather than a silently mis-ordered posting. `sl055` also
    #  publishes two keyword-only test seams; the COBOL `CALL` passes neither, so
    #  neither is passed here.
    program.run(*linkage)

    term_code = calling_data.ws_term_code

    #  R-4 [sales/sales.cbl:L708-L709] `if ws-term-code < 8 / perform overrewrite.`
    #  `not is_serious_error(...)` IS `ws-term-code < 8` over the whole `pic 99`
    #  domain, which the sibling helper's own docstring states. The maintainer's
    #  comment at L708 names this route's programs: `*> for sl055 & 060, xl150`.
    #  The effect of `overrewrite` is a RECORDED OMISSION - see
    #  `_overrewrite_omitted` and Q-CLI-OVERREWRITE.
    if not args.is_serious_error(term_code):
        _overrewrite_omitted(program_id=program_id, term_code=term_code)

    #  R-4 [sales/sales.cbl:L710-L712] `if ws-term-code > 7 / perform overrewrite
    #  / goback.`  A SECOND, SEPARATE `if`, as the source has it.
    #
    #  GO TO class 4 (sibling re-dispatch), per-site proof:
    #    COBOL:  `perform overrewrite` returns, then `goback` ends the RUN UNIT -
    #            the menu program stops, so no further program is dispatched and
    #            no menu is redrawn.
    #    Python: the omitted-persistence record is emitted, the stop is logged,
    #            and the term code is returned for the caller to honour; `main`
    #            then leaves the process with `args.exit_status_for(...)`.
    #    Proof:  the set of programs invoked is identical and so is the database
    #            effect. Control never re-enters the dispatch paragraph in either
    #            version. The only difference is `overrewrite`'s persistence,
    #            which is recorded as an omission in the footer, and the process
    #            exit status, which the COBOL has no equivalent of at all
    #            (Q-CLI-EXITSTATUS, settled in `args.exit_status_for`).
    #
    #  DIVERGENCE FROM PURCHASE, PRESERVED. Sales writes `perform overrewrite`
    #  and then `goback` [sales/sales.cbl:L710-L712]; Purchase writes
    #  `go to overrewrite` [purchase/purchase.cbl:L703-L704], which reaches the
    #  same paragraph and falls through `overclose.` to the same `goback`. The
    #  net effect is identical - persist, then end the run unit - but the
    #  mechanism differs, and rule R-4 forbids harmonising the two.
    if args.is_serious_error(term_code):
        _overrewrite_omitted(program_id=program_id, term_code=term_code)
        _log_stop(_Stop.RUN_UNIT_ENDED, program_id=program_id, term_code=term_code)

    #  L714-L716 `load000-exit.` / `go to display-menu.` - the fall-through exit,
    #  reached whenever L712 did not `goback`. The menu redraw has no database
    #  effect and is omitted (Agent Action Plan section 0.3.4); returning to the
    #  caller is what remains of it.
    return term_code


def load07(linkage: args.SlPlLinkage) -> int:
    """`load07.` [sales/sales.cbl:L756-L768] - Sales transaction posting.

    The maintainer's own label comment is the evidence for that locator:
    `load07.             *> Sales trans posting` [sales/sales.cbl:L756]. See the
    module docstring for the three further confirmations and for why `load08` -
    which dispatches the out-of-scope `sl080` - is not this paragraph.

    Reproduces the paragraph in SOURCE ORDER, minus the omitted `sl830` head::

        L759       move     "sl830" to WS-Called.      <- OMITTED, out of scope
        L760       perform  load00.                    <- OMITTED with it
        L761       if       ws-term-code not = zero    <- OMITTED with it
        L762                go to display-menu.
        L763       move     "sl055" to ws-called.
        L764       perform  load000.
        L765       if       ws-term-code not = zero
        L766                go to display-menu.
        L767       move     "sl060" to ws-called.
        L768       go       to load000.

    Nothing follows the second dispatch, because L768 is `go to load000` rather
    than `perform load000`: control never comes back to this paragraph, so any
    statement written after it would be unreachable in the source and invented
    here.

    Args:
        linkage: the five arguments in COBOL parameter order, as
            `args.bind_slpl_linkage(ns, called="sl055")` builds them. ONE
            instance is passed to both dispatches, which is what makes the second
            program see the first program's writes - the two period-total
            accumulations of `sl055` [sales/sl055.cbl:L675, :L677] reach `sl060`
            in the same `SYSTOT-REC`.

    Returns:
        `WS-Term-Code` after the last dispatch that ran: `sl055`'s if the chain
        stopped there, otherwise `sl060`'s. Zero means the route completed.

    Raises:
        Nothing of its own - see `load000`.
    """
    #  OMITTED [sales/sales.cbl:L759-L762]: `move "sl830" to WS-Called` /
    #  `perform load00` and its own `not = zero` gate. The sales autogen series
    #  sl800..sl830 is excluded by Agent Action Plan section 0.2.2, and section
    #  0.4.1.1 has this entry point dispatch sl055 then sl060 only. `load00.`
    #  [sales/sales.cbl:L677-L692] - the FOUR-parameter shape - is therefore not
    #  implemented at all: this route has no caller for it. Recorded in the
    #  footer, where the oracle-side asymmetry is recorded too.

    #  [sales/sales.cbl:L763-L764] `move "sl055" to ws-called.` /
    #  `perform load000.`  A `perform` RETURNS, which is why the gate below is
    #  reachable at all.
    term_code = load000(linkage, _PROGRAM_SL055, sl055_invoice_extract_analysis)

    #  THE RETURN LEG OF L712, NOT A SECOND GATE. `load000` has already taken its
    #  own `> 7` disposition and logged it; in the COBOL that disposition was a
    #  `goback` out of the whole menu program, so control never arrived here. A
    #  Python function cannot end its caller, so the caller honours it instead.
    #  This is NOT a substitute for the gate below and does NOT narrow it: the
    #  gate keeps its own `not = zero` predicate, unaltered, and is what stops the
    #  chain for codes 1 through 7. The Purchase route needs the same return leg,
    #  because purchase/purchase.cbl `load000.` gobacks on `> 7` as well
    #  [purchase/purchase.cbl:L703-L704]; what Purchase does NOT have is the
    #  paragraph-level gate below.
    if args.is_serious_error(term_code):
        return term_code

    #  R-4 [sales/sales.cbl:L765-L766] `if ws-term-code not = zero /
    #  go to display-menu.`
    #
    #  THE PREDICATE IS `not = zero`. It is NOT the General Ledger's `= 5`
    #  [general/general.cbl:L810-L811] and it is NOT `= 8`; Purchase has no
    #  gate here at all [purchase/purchase.cbl:L752-L762]. Three ledgers, three
    #  forms, deliberately not harmonised: harmonising would be a behaviour
    #  change and therefore, under rule R-4, a failure.
    #
    #  GO TO class 4 (sibling re-dispatch), per-site proof:
    #    COBOL:  `go to display-menu` redraws the menu and awaits the next
    #            selection; `sl060` is never reached.
    #    Python: the operation ends immediately and `sl060` is never invoked.
    #    Proof:  identical set of invoked programs and identical database effect.
    #            The menu redraw is the only difference and it has no database
    #            effect (Agent Action Plan section 0.3.4), while the awaiting of a
    #            next selection has no headless equivalent - a command performs
    #            one operation and returns.
    #
    # AMBIGUITY Q-CLI-TERMCODE-1-7: the 1..7 band is unreachable from sl055
    # today - a census of the in-scope programs finds only 5 at
    # [general/gl070.cbl:L289], 8 at [sales/sl055.cbl:L344] and 8 at
    # [purchase/pl055.cbl:L286] - so this gate and Purchase's absence of one
    # cannot currently be told apart by any run. Confirm against the compiled
    # oracle that no other program on either route sets a code in that band, and
    # record the resolution in docs/migration/ambiguity-resolutions.md (rule R-6).
    if term_code != _WS_TERM_CODE_ZERO:
        _log_stop(
            _Stop.RETURNED_TO_MENU,
            program_id=_PROGRAM_SL055,
            term_code=term_code,
        )
        return term_code

    #  [sales/sales.cbl:L767-L768] `move "sl060" to ws-called.` /
    #  `go to load000.`  NO CODE MAY FOLLOW THIS LINE - see the docstring.
    return load000(linkage, _PROGRAM_SL060, sl060_invoice_posting)


def _build_parser() -> argparse.ArgumentParser:
    """Compose this route's parser from the shared option fragments.

    Composed, never re-declared: `acas_posting.cli.args` owns the binding of argv
    to `01 WS-Calling-Data` [copybooks/wscall.cob:L6-L14] and to the system
    records, and every entry point of this package imports those definitions
    rather than writing its own. Two fragments make Shape 2's option set:

      * `add_calling_data_arguments(..., default_caller=WS_CALLER_SALES)` - the
        five settable calling-data fields, defaulted to the literal this menu
        moves into `WS-Caller`, `move "sales" to ws-caller`
        [sales/sales.cbl:L481]. `WS-Called` gets no option because it is the
        dispatch vehicle, and `WS-Term-Code` gets none because it is an output.
      * `add_slpl_linkage_arguments(...)` - the REQUIRED `--run-date`, plus
        `--date-form` and the fan-out switch `--irs-instead`.

    No option of this module's own is added. In particular there is no option that
    would create a worker, a pool or an event loop (rule R-3: execution is
    strictly sequential), none that selects or diffs against the compiled oracle
    (rule R-1), and no control-total option - Agent Action Plan section 0.6.4
    records that Sales batches "balance by construction", so the control-total
    mismatch scenario is General-Ledger-specific.

    Returns:
        The parser. Built on call, never at import.
    """
    parser = argparse.ArgumentParser(
        prog="python -m acas_posting.cli.sl_invoice_post",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Sales transaction posting - sl055, then the `not = zero` gate, then "
            "sl060. Reproduces sales/sales.cbl `load07.` L756-L768, whose label "
            "carries the maintainer's own comment `*> Sales trans posting`, and "
            "its five-parameter dispatch helper `load000.` L698-L712."
        ),
        epilog=(
            "The two programs run one at a time with the gate between them. A "
            "non-zero WS-Term-Code from sl055 stops the chain and sl060 is not "
            "dispatched; the exit status IS the term code. sl830 is not "
            "dispatched: the sales autogen series is out of scope. Pin "
            "--irs-instead explicitly - it decides which tables the run touches."
        ),
    )
    args.add_calling_data_arguments(parser, default_caller=args.WS_CALLER_SALES)
    args.add_slpl_linkage_arguments(parser)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """The CLI boundary: bind argv to the linkage, run `load07`, report the code.

    Args:
        argv: the argument vector WITHOUT the program name. `None` means take it
            from the command line, which is argparse's own behaviour and the only
            way this module ever looks outside its arguments for one. Tests pass
            an explicit sequence.

    Returns:
        The process exit status, which is `WS-Term-Code` itself:
        `args.exit_status_for` is the identity, total and lossless over the
        `pic 99` domain 0..99 [copybooks/wscall.cob:L10]. Zero means the route
        completed; 8 is the code `sl055` raises when the analysis extract is
        missing [sales/sl055.cbl:L344]. Q-CLI-EXITSTATUS, settled in `args`: the
        COBOL menus never exit with the code at all, so the boundary is new in
        the migration and the identity is the mapping that discards nothing.

    Raises:
        SystemExit: from argparse, for `--help` or a usage error - including the
            omission of the REQUIRED `--run-date`, which is the mechanically
            checkable proof that no ambient date can enter (rule R-6).
        rdbms_params.RdbmsParamError: the deployment contract for the six
            connection parameters is absent or unusable. NOT caught, per the
            contract `args` states: a run that cannot reach the provisioned
            database must stop before it writes anything.
        CobolFileSystemPathUnavailable: from `sl055`, on the branch that needs
            GnuCOBOL built-ins rule R-1 forbids invoking. NOT caught - see the
            module docstring.
    """
    #  The ONLY `logging.basicConfig` in this module, and it is inside `main`.
    #  Importing the module must not reconfigure a host application's logging,
    #  and the scenario suites import this package. INFO carries the dispatch
    #  records and both stops; the omitted-persistence records are DEBUG.
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(name)s: %(message)s"
    )

    ns = _build_parser().parse_args(argv)

    #  Shape 2 bound in one call, with `called` set to the FIRST program of the
    #  chain - `move "sl055" to ws-called` [sales/sales.cbl:L763]. The same
    #  instance then serves the second dispatch, which only changes `WS-Called`.
    #  This call is also where the controlled clock is pinned, through
    #  `args.resolve_clock` -> `acas_posting.clock`: both observables, the text
    #  `to-day pic x(10)` and the binary `Run-Date`
    #  [copybooks/wssystem.cob:L67], from the one required `--run-date` (rule
    #  R-6). No date is read from anywhere else, here or downstream.
    linkage = args.bind_slpl_linkage(ns, called=_PROGRAM_SL055)

    _LOG.info(
        "sl_invoice_post: sales/sales.cbl load07. L756-L768; run date pinned to "
        "to-day %r; WS-Caller %r",
        linkage.to_day,
        linkage.calling_data.ws_caller.strip(),
    )

    term_code = load07(linkage)

    _LOG.info(
        "sl_invoice_post finished with WS-Term-Code %d [copybooks/wscall.cob:L10]",
        term_code,
    )
    return args.exit_status_for(term_code)


if __name__ == "__main__":
    raise SystemExit(main())


# --- traceability ------------------------------------------------------------
#
# MODULE -> COBOL SOURCE  (rule R-5)
#   acas_posting/cli/sl_invoice_post.py  <-  sales/sales.cbl `load07.` L756-L768
#   and its dispatch helper `load000.` L698-L712, plus the linkage declared by
#   copybooks/wscall.cob L6-L14, copybooks/wssystem.cob, copybooks/wssys4.cob and
#   copybooks/wsnames.cob. Every one of them is REFERENCE only - frozen, read as
#   specification. Any diff touching common/*.cbl, common/*.scb, copybooks/*.cob,
#   general/*.cbl, sales/*.cbl, purchase/*.cbl, irs/*.cbl or mysql/ACASDB.sql is
#   a defect in the migration, however harmless it looks (AAP 0.8.1).
#
# FUNCTION -> PARAGRAPH
#   load000               sales/sales.cbl:L698-L712  (exit L714-L716)
#   load07                sales/sales.cbl:L756-L768
#   main                  the CLI boundary - no COBOL paragraph. The menu shell
#                         has `display-menu.` L478 and its `accept` loop here;
#                         both are screen I/O with no database effect and are
#                         omitted (AAP 0.3.4).
#   _build_parser         the CLI boundary - no COBOL paragraph. Composes the
#                         shared fragments of acas_posting/cli/args.py.
#   _overrewrite_omitted  the RECORDED OMISSION of `overrewrite.`
#                         sales/sales.cbl:L628-L658, which falls through
#                         `overclose.` L659 to `goback` L660. Named for what it
#                         does - record the omission - not for the paragraph,
#                         because it deliberately does not perform it.
#   _log_stop, _Stop      the two dispositions, named: L710-L712 and L765-L766.
#   _SlPlPostingProgram   the shape of `call ws-called` L702, a dynamic call by
#                         name.
#
# PROGRAM -> MODULE
#   sl055  ->  acas_posting/programs/sl055_invoice_extract_analysis.py
#              linkage sales/sl055.cbl:L271-L275, dispatched at
#              sales/sales.cbl:L763-L764
#   sl060  ->  acas_posting/programs/sl060_invoice_posting.py
#              linkage sales/sl060.cbl:L395-L399, dispatched at
#              sales/sales.cbl:L767-L768
#   Both are imported AS MODULES and reached only through their published `run`;
#   `acas_posting/programs/__init__.py` provides no dispatch table, no registry
#   and no `run` re-export, and this module adds none (AAP 0.3.3).
#
# `GO TO` CLASSES  (AAP 0.4.2 taxonomy)  -  two transfer sites, both class 4
# (sibling re-dispatch), each with its per-site proof of equivalence:
#
#   L765-L766  `if ws-term-code not = zero / go to display-menu`   CLASS 4
#     COBOL   the menu is redrawn and awaits the next selection; sl060 is never
#             reached.
#     Python  the operation ends immediately; sl060 is never invoked.
#     Proof   identical set of invoked programs, identical database effect. The
#             menu redraw has no database effect (AAP 0.3.4) and "await the next
#             selection" has no headless equivalent - a command performs one
#             operation and returns.
#
#   L710-L712  `if ws-term-code > 7 / perform overrewrite / goback`   CLASS 4
#     COBOL   `perform overrewrite` returns, then `goback` ends the RUN UNIT: the
#             menu program stops, so nothing further is dispatched.
#     Python  load000 logs the stop and returns the term code; load07 honours it
#             by returning without dispatching sl060, and main leaves the process
#             with args.exit_status_for(...).
#     Proof   control never re-enters the dispatch paragraph in either version
#             and the same programs run. The only differences are overrewrite's
#             persistence (an omission below) and the process exit status, which
#             the COBOL has no equivalent of at all (Q-CLI-EXITSTATUS).
#
#   The `< 8` branch L708-L709 is NOT a transfer: `perform overrewrite` returns
#   to the next statement, so the flow is straight-line and only the effect is
#   omitted.
#
# CORRECTIONS  -  each verified against the frozen source with a line read. DO
# NOT "fix" any of these back to the value the planning documents carry.
#
#   1. THE PARAGRAPH IS `load07` (sales/sales.cbl:L756-L768), NOT `load08`.
#      The folder requirements table and the acas_posting/__main__.py route table
#      both say `load08`. `load08.` (L770-L774) dispatches "sl080" - Payment
#      Input - which AAP 0.2.2 places explicitly out of scope, so the wrong label
#      would point the traceability document at an out-of-scope program.
#      Evidence, four ways: the maintainer's inline comment
#      `load07.             *> Sales trans posting` on the label line itself
#      (L756); the menu-letter ordinal, `"(G)  Sales Transactions Post"` at L545
#      being the seventh letter under the `depending on z` dispatch at L670
#      (L546 `"(H)  Payment Input"` is the eighth, L549 `"(K)  Payment Post"` the
#      eleventh, which is load11 and the sibling sl_cash_post route); and TWO
#      change-history entries, ".32 Added execution of sl830 first when Invoice
#      Post selected." (L121) and - decisively - ".33 Call in load07 to 830
#      should have been using load00 not 000." (L124), in which the maintainer
#      names load07 as the invoice-post paragraph. Note that __main__.py's route
#      table cites the gate SPAN correctly, L759-L768, which lies inside load07;
#      only the label is wrong.
#
#   2. THE SALES/PURCHASE LINKAGE SHAPE HAS FIVE PARAMETERS, not the four AAP
#      0.4.1.1's phrasing implies. sales/sales.cbl:L702-L706 passes five
#      (ws-calling-data, System-Record, WS-System-Record-4, to-day, file-defs) and
#      both callees declare five, sales/sl055.cbl:L271-L275 and
#      sales/sl060.cbl:L395-L399. AAP 0.1.1 has it right - "The Sales and
#      Purchase families add the fourth system record" - and args.SlPlLinkage has
#      five members. The maintainer's own comment at L708 names the beneficiaries:
#      `*> for sl055 & 060, xl150`.
#
#   3. THE __main__.py ROUTE TABLE'S NEIGHBOURING SPANS DRIFT BY ONE LINE. It
#      cites `load11` as L793-L797; the label `load11.` is at L792 and the
#      paragraph runs to L796. Measured label lines in sales/sales.cbl:
#      load00. L677, load000. L698, load01. L718, load06. L750, load07. L756,
#      load08. L770, load09. L776, load10. L782, load11. L792, load12. L798.
#
#   A NOTE ON ONE FURTHER LOCATOR, already corrected by the sibling: AAP 0.4.1.1
#   cites `01 WS-Calling-Data` as copybooks/wscall.cob:L6-L13, but WS-CD-Args is
#   at L14 (L11 being a comment), so the block is L6-L14. This module cites
#   L6-L14 throughout, as acas_posting/cli/args.py already does in its own
#   CORRECTION 1.
#
# OMISSIONS - recorded as omissions so that a reader comparing the two trees does
# not conclude something was lost (AAP 0.4.3):
#
#   * `sl830` AND THE WHOLE `load00` HEAD OF THE CHAIN, sales/sales.cbl:L759-L762
#     - `move "sl830" to WS-Called`, `perform load00` and that leg's own
#     `not = zero` gate. AAP 0.2.2 excludes the sales autogen series sl800..sl830,
#     and AAP 0.4.1.1 has this entry point dispatch sl055 then sl060 only. The
#     maintainer added the leg at L121 (".32") and corrected which helper it uses
#     at L124 (".33"). Consequently `load00.` itself - sales/sales.cbl:L677-L692,
#     the FOUR-parameter shape - is NOT implemented in this module: with sl830
#     out of scope this route has no caller for it. The oracle driver script
#     records the same asymmetry, noting that the menu-driven Cobol side WILL run
#     sl830 and that the two autogen tables are asserted untouched
#     [run_cobol_scenario.sh:L332-L336].
#
#   * `display-menu.` (sales/sales.cbl:L478) AND ALL MENU SCREEN I/O, including
#     the `go to load01 load02 ... depending on z` dispatch table at
#     sales/sales.cbl:L670 and the banners the two programs display. No database
#     effect, excluded by AAP 0.2.2 and 0.3.4. Diagnostics become log records
#     that neither alter control flow nor reach a column.
#
#   * `overrewrite`'s PERSISTENCE of System-Record (key 1) and
#     WS-System-Record-4 (key 4) to both the RDB and the Cobol file -
#     sales/sales.cbl:L628 falling through `overclose.` L659 to `goback` L660 -
#     together with `pre-overrewrite`'s backup `call "SYSTEM" using
#     Full-Backup-Script` at sales/sales.cbl:L625. The first is out of this
#     layer's reach three times over (menu program: AAP 0.2.2; needs the
#     data-access layer, which AAP 0.4.3 bars cli/*.py from; and moving the write
#     into the program layer is barred by R-3, since no in-scope posting program
#     performs system-record I/O). The second is excluded twice, by AAP 0.2.2's
#     spool-out exclusion and by R-1. See `_overrewrite_omitted` and
#     Q-CLI-OVERREWRITE.
#
#   * THE PURE-ACKNOWLEDGEMENT `accept WS-Reply at 2435` at sales/sl055.cbl:L342.
#     Dropped under AAP 0.3.4 - its only effect is to block a terminal - while
#     THE SURROUNDING CONTROL TRANSFER IS PRESERVED: `move 8 to WS-Term-Code`
#     (L344) and `goback` (L345) both stand, in sl055's own module. Note that the
#     prompt is guarded by `if WS-Caller not = "xl150"` (L341), so `WS-Caller`
#     genuinely changes behaviour there; it remains bindable through
#     `args.add_calling_data_arguments` and is defaulted to "sales"
#     (sales/sales.cbl:L481).
#
#   * THE OTHER SALES MENU ROUTES, not dispatched by this entry point because
#     they are out of scope: `load08.` L770-L774 (sl080, Payment Input),
#     `load09.` L776-L780 (sl085), `load10.` L782-L790 (sl090 then sl095).
#     `load11.` L792-L796 (sl100) is in scope but belongs to the sibling
#     sl_cash_post route.
#
#   * NO "DOES THE EXTRACT FILE EXIST?" PRE-CHECK (rule R-3). That test is the
#     call to the GnuCOBOL file-existence built-in at sales/sl055.cbl:L336-L337,
#     inside sl055, and duplicating it in the entry point would add a validation
#     the COBOL does not have at this level. No path is inspected here at all.
#
# ANOMALY, REPRODUCED AS DATA (rule R-4)
#   `load00`'s whitelist, sales/sales.cbl:L686-L690, tests
#   `ws-called = "sl000" or "sl080" or "sl085" or "sl090" or "sl095" or "sl100"
#   or "sl115" or "sl200" or "sl910" or "sl920" or "sl930"` before performing
#   `overrewrite`. The `"sl100"` entry is DEAD: sl100 is dispatched through
#   `load000`, not `load00` - `load11.` is `move "sl100" to ws-called` then
#   `go to load000` (sales/sales.cbl:L795-L796) - so the test can never match it.
#   The maintainer's own inline `*> 200 ??  930 ??` at L689 shows he doubted two
#   further entries. Recorded, not cleaned up. It has no effect on THIS module,
#   which does not implement `load00` at all, and it is recorded here because the
#   paragraph is part of the route this module reproduces.
#
# AMBIGUITIES  (rule R-6)  -  three, each marked in place at the code it governs.
#   Q-CLI-OVERREWRITE   in _overrewrite_omitted - OPEN. The Cobol run rewrites
#     SYSTEM-REC and SYSTOT-REC after every dispatch of this route; the Python run
#     leaves both rows as the seed left them. Which columns a Sales invoice post
#     actually moves must be measured on the compiled oracle so that each
#     scenario can declare those two tables out of its diff or seed them to the
#     post-run state.
#     A MEASURED CONSEQUENCE OF THE SAME ROOT CAUSE, recorded here for whoever
#     wires the scenario driver: because nothing in the migrated cycle loads
#     SYSTEM-REC from the store (Q-CLI-SYSREC-LOAD in acas_posting/cli/args.py),
#     a run of this entry point built purely at the record layer's declared
#     defaults carries `File-System-Used` = 0, which is
#     `88 FS-Cobol-Files-Used value zero.` [copybooks/wssystem.cob:L113]. The
#     data-access layer then refuses the INDEXED path, correctly, because only the
#     relational path is migrated - the frozen handler makes the same distinction
#     with `if not FS-Cobol-Files-Used` [common/acas013.cbl:L321-L325], and the
#     relational side needs `88 FS-RDBMS-Used value 1.`
#     [copybooks/wssystem.cob:L116]. This entry point deliberately does NOT set
#     that field: the settable SYSTEM-REC list is closed at two options (rule
#     R-3), this layer may not reach the record layer to widen it, and the value
#     properly comes from the seeded row the COBOL menu would have read. So the
#     scenario seed must carry FS-RDBMS-Used - it is a property of the seeded
#     state, not of the command line - and this route needs no change when it
#     does. Verified by running the route with the real programs: the linkage
#     binds, the clock pins, load000 dispatches sl055, and control reaches the
#     data-access boundary before stopping there.
#   Q-CLI-TERMCODE-1-7  in load07, at the gate - OPEN. The 1..7 band is
#     unreachable from sl055 today (the census finds only 5 at
#     general/gl070.cbl:L289, 8 at sales/sl055.cbl:L344 and 8 at
#     purchase/pl055.cbl:L286), so the Sales gate and Purchase's absence of one
#     cannot currently be told apart. The oracle must confirm that no other
#     program on either route sets a code in that band.
#   Q-CLI-EXITSTATUS    in main - SETTLED in acas_posting/cli/args.py, and
#     settled by establishing that THERE IS NO ORACLE OBSERVABLE: RETURN-CODE, the
#     one register GnuCOBOL surfaces as a process status, is read and never
#     written anywhere in the five menus or the twelve posting programs, and each
#     menu ends with a bare `goback` (sales/sales.cbl:L660). The identity mapping
#     is therefore a boundary decision under AAP 0.3.4, taken because it is total
#     and lossless over the `pic 99` domain. This module re-encodes nothing.
#
# RULES  -  `review_rules` reports NO user rules document for this project, so
# these are the Agent Action Plan's own six (section 0.7.2); enterprise-standard
# best practice applies wherever they are silent, and no rule has been invented.
#   R-1  satisfied structurally. Imports: argparse, enum, logging,
#        collections.abc, typing, acas_posting.cli.args and the two program
#        modules - and nothing else. Nothing here spawns a child process, loads a
#        foreign library or reaches the GnuCOBOL toolchain; there is no import
#        path from this package to the compiled oracle's tree, and no option
#        selects, invokes or diffs against that oracle. The oracle's own scripts
#        drive THIS entry point from outside, never the reverse.
#   R-2  satisfied by type. WS-Term-Code is an `int` (`pic 99`,
#        copybooks/wscall.cob:L10), to-day is a `str`, and no binary-radix
#        numeric type appears in any signature, option type or expression - the
#        word does not occur in this file even as an argparse converter. No
#        arithmetic is performed here at all.
#   R-3  satisfied by omission. No added validation - notably no duplicated
#        extract-file check and no path inspection of any kind - no added field,
#        no SQL and no schema access; and no concurrency, there being no thread,
#        no pool, no event loop and no child-process primitive imported, and no
#        option that would create one. The two programs run ONE AT A TIME, in
#        this one process, with the gate
#        between them, matching the single-threaded COBOL. No control-total
#        option is offered, because Sales batches balance by construction
#        (AAP 0.6.4).
#   R-4  reproductions, each carrying its locator at the site: the `not = zero`
#        gate predicate (L765-L766), left different from the General Ledger's
#        `= 5` and from Purchase's absent gate; the `< 8` and `> 7` bands as two
#        separate statements (L708-L712); `move zero to ws-term-code` before
#        every dispatch (L701); Sales' `perform overrewrite` then `goback`
#        mechanism left distinct from Purchase's `go to overrewrite`
#        (purchase/purchase.cbl:L703-L704); the dead "sl100" whitelist entry
#        recorded above; and the deliberate non-normalisation of all four
#        divergent gate forms.
#   R-5  this footer, the paragraph-named public functions load000 and load07,
#        the `GO TO` class and proof at both transfer sites, and a locator on
#        every reproduced statement.
#   R-6  the clock is injected: --run-date is REQUIRED, with no default and no
#        fallback, and both observables are pinned through args.resolve_clock ->
#        acas_posting.clock. Nothing here reads a system clock, a calendar, an
#        elapsed-time counter, an environment variable, a host name or an entropy
#        source - none of the modules that offer one is imported. Two runs of one
#        scenario under the same pinned clock are therefore byte-identical
#        (AAP 0.8.5). The three questions above are marked, not guessed.
# -----------------------------------------------------------------------------

