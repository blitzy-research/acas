"""The General Ledger posting cycle - `gl070`, the abort gate, `gl071`, `gl072`.

The migration of `general/general.cbl` `load08.` L805-L815 together with the
dispatch paragraph it performs three times, `load00.` L711-L721. Screen I/O is
removed; the dispatch, its order and its gate are not.

The abort gate is hard, not a warning. `if ws-term-code = 5 go to display-menu`
[general/general.cbl:L810-L811] means that when gl070 finds a batch left open
[general/gl070.cbl:L288] and raises 5 [general/gl070.cbl:L312-L313], gl071 and
gl072 NEVER RUN. The database effect of the rejection is therefore the absence of
everything the later phases would have written, and reporting a warning and
continuing would be a behaviour change.

Phase numbering is the programs' own and is not the execution order: batch check
and pre-process are phases 1 and 2 [general/gl070.cbl:L283], transaction update
is phase 4 [general/gl072.cbl:L277], and deletion is labelled phase 3 although it
runs afterwards, inside gl080 [general/gl080.cbl:L319].

The sort order between the phases is load-bearing. gl072 locates the
nominal-ledger account for each posting with a SEQUENTIAL read
[general/gl072.cbl:L408], guarded at L407, so it finds the right account only
because gl071 emitted the stream in nominal-key order. A perturbed order misposts
silently.

The run date is an argument, never a clock reading (R-6): `--run-date` is
required and pins both observables, and none of the three programs dispatched
here reads a clock. The exit status is `WS-Term-Code` itself, so a caller can
tell the abort code 5 from a serious error above 7.

identical in `gl071` [general/gl071.cbl:L161-L164] and `gl072`
[general/gl072.cbl:L262-L265], because all three are dispatched through the one
paragraph `load00.` whose single `CALL` parameter list is
[general/general.cbl:L715-L718]. `acas_posting.cli.args.GlLinkage` carries those
four arguments in that order, so `program.run(*linkage)` and the `CALL` above can
be diffed line for line. This is NOT the five-parameter Sales and Purchase shape
[sales/sl060.cbl:L395-L399] and NOT the three-parameter IRS shape
[irs/irs030.cbl:L552-L554]; neither applies here.

THE ABORT GATE IS HARD, NOT A WARNING
=====================================
Agent Action Plan section 0.6.4, verbatim: "The Python CLI must reproduce this as
a **hard gate between phases, not as a warning**."

The chain is four links long and crosses three programs:

    1. phase 1 of `gl070` raises a detector flag on meeting a batch left OPEN in
       the current accounting cycle          [general/gl070.cbl:L314-L315]
    2. `menu-input2.` tests the flag, runs the open-batch report and stores `5`
       into `WS-Term-Code`                   [general/gl070.cbl:L287-L290]
    3. `load00.` hands control back WITHOUT tripping its own gate, because that
       gate is `if ws-term-code > 7` and 5 is not greater than 7
                                             [general/general.cbl:L720-L721]
    4. `load08.` tests `if ws-term-code = 5 go to display-menu.`
                                             [general/general.cbl:L810-L811]

**The effect is that `gl071` and `gl072` never run at all.** Not "run with a
warning" - not run. The database effect of the abort is the ABSENCE of everything
those two phases would have written, so an entry point that logged the condition
and carried on would post a batch the frozen system refuses to post.

The exact value matters twice over, which is why nobody may "simplify" it: below
five and `load08.` stops matching, above seven and `load00.` diverts to
`overrewrite.` instead. And `general/general.cbl:L714` clears `WS-Term-Code`
before EVERY dispatch, so no code is ever carried from one phase into the next.

THE PHASE NUMBERING IS NOT THE EXECUTION ORDER
==============================================
The programs label their own phases on screen, and Agent Action Plan section
0.6.4 asks that the labels be preserved "so a maintainer is not misled":

    phase 1  batch check              `gl070`  [general/gl070.cbl:L284]
    phase 2  transaction pre-process  `gl070`  [general/gl070.cbl:L292]
    (sort)                            `gl071`  [general/gl071.cbl:L170]
    phase 4  transaction update       `gl072`  [general/gl072.cbl:L274]
    phase 3  transaction deletion     `gl080`  [general/gl080.cbl:L319]
    phase 5  end of period            `gl080`  [general/gl080.cbl:L336]

So **deletion is labelled phase 3 but executes after phase 4**, and the numbering
is not sequential with execution. Phases 3 and 5 are NOT dispatched from here:
`gl080` is `load09.` [general/general.cbl:L817-L821] and belongs to the sibling
entry point `acas_posting/cli/gl_end_of_cycle.py`.

THE SORT ORDER IS LOAD-BEARING - THE MOST FRAGILE THING IN THE CYCLE
====================================================================
`gl072` locates the nominal-ledger account for each posting with a SEQUENTIAL
read-next rather than an indexed read [general/gl072.cbl:L407-L408], and there is
no error path at all. It finds the right account ONLY because `gl071` has already
emitted the stream in nominal-key order, sorting on
`(sort-batch, sort-ac, sort-pc, sort-post)` [general/gl071.cbl:L172-L176]. Agent
Action Plan section 0.6.4: "Any change in sort stability or key composition
produces silent misposting - no error, no diagnostic, wrong balances."

Two consequences bind this module. The three phases run **in this order, in one
process, strictly sequentially** - never reordered, never parallelised (rule
R-3). And the three phases share ONE work-file container, because `pre-trans` and
`post-trans` [copybooks/wsnames.cob:L15-L16] are how they communicate: `gl070`
writes `pre_trans`, `gl071` sorts it into `post_trans`, `gl072` posts from
`post_trans`. See `_CycleWorkFiles`.

WHAT IS DELIBERATELY NOT HERE
=============================
No screen output of any kind. The menu's own `display-menu` redraw, its
`accept-loop` and its `go to load01 ... depending on z` dispatch table are all
omitted, and each omission is recorded in the traceability footer rather than
left to be noticed (Agent Action Plan section 0.4.3). The programs' phase banners
belong to `acas_posting.programs` and are not duplicated here.

WHAT IS HERE AND USED TO BE OMITTED. `overrewrite`'s persistence of the system
records IS reproduced, on the one arm the frozen `load00.` reaches it from -
`if ws-term-code > 7 / go to overrewrite` [general/general.cbl:L720-L721] - and
once more at the quit, reproducing [general/general.cbl:L595-L596]; the two
guards are mutually exclusive, so a run performs it exactly once. The paragraph
itself lives once, in `acas_posting.cli.args`, and the state it persists is loaded
by the same module before the first dispatch. Its RDB arm
[general/general.cbl:L656-L672] - open key 1, rewrite keys 1, 2 and 4 in that
order, then close - is reproduced in full, so `SYSTEM-REC`, `SYSDEFLT-REC` and
`SYSTOT-REC` are persisted exactly as a menu dispatch persists them. What remains
unreproduced is only the SECOND leg: the same three rewrites against the ISAM
parameter file at [general/general.cbl:L676-L691], which has no counterpart
because the migration has a single store. That residue is carried as
`Q-CLI-OVERREWRITE-SECOND-LEG` rather than described as an omission of the whole
paragraph.

Example:
    Run the cycle for the 21st of September 2025, General Ledger only. This
    WRITES - it posts, and it persists the system records afterwards - so point
    it only at a disposable schema::

        python -m acas_posting.cli.gl_post_cycle \\
            --run-date 21/09/2025 --irs-instead " "

    The exit status is `WS-Term-Code` itself: 0 when all three phases ran, 5 when
    the abort gate fired, and the reported code when a phase failed seriously.
"""

from __future__ import annotations

import argparse
import enum
import logging
from collections.abc import Sequence
from typing import Final, Protocol

from acas_posting.cli import args
from acas_posting.programs import (
    gl070_transaction_pre_process,
    gl071_batch_sort,
    gl072_transaction_update,
)

__all__: Final[tuple[str, ...]] = ("main", "load00", "load08")

#: Diagnostics only.
_LOG: Final[logging.Logger] = logging.getLogger(__name__)

# THE THREE PROGRAM-IDS THE MENU MOVES INTO `WS-Called`, named once each.
_GL070: Final[str] = "gl070"
_GL071: Final[str] = "gl071"
_GL072: Final[str] = "gl072"

#  THIS MODULE CALLS NO `basicConfig` AND DECLARES NO LOG FORMAT.
#  `logging.basicConfig` mutates the root logger, so seven entry points each
#  calling it produced seven formats and a first-caller-wins race. There is now
#  exactly one call, in `acas_posting.__main__.configure_logging`, which owns the
#  single timestamp-free format and the single level policy - see that module's
#  `LOG_FORMAT`. Both process boundaries reach it: the router, and this module's
#  own `if __name__ == "__main__":` guard through `run_entry_point`. `main` asks
#  that one configurator to SET THE LEVEL when the operator supplied
#  `--log-level` - the option every route now shares - and does nothing at all
#  when they did not, which is what the scenario suites need from a library
#  call.


class _Disposition(enum.Enum):
    """What `load00` observed after a dispatch, and therefore what follows it.

    TWO MEMBERS, because `load00.` has exactly two exits and no others: it either
    reaches its own end and returns to whichever paragraph performed it, or it takes `go
    to overrewrite` at [general/general.cbl:L720-L721] and the run unit ends.
    """

    CONTINUE = enum.auto()

    #: `if ws-term-code > 7 / go to overrewrite.`
    #: [general/general.cbl:L720-L721]. Control never comes back in the frozen
    #: program: `overrewrite.` falls through `overclose.`
    #: [general/general.cbl:L693] to `goback` [general/general.cbl:L694] and the
    #: run unit ends. A caller that receives this must not dispatch again.
    #: `load00` has ALREADY performed `args.overrewrite` before returning this,
    #: so a caller has no persistence left to do.
    SERIOUS_ERROR = enum.auto()


class _GlProgram(Protocol):
    """The shape every migrated General Ledger program module presents.

    Structural, not nominal: `gl070_transaction_pre_process`, `gl071_batch_sort` and
    `gl072_transaction_update` are MODULES, and each publishes `__all__ = ("run",)` with
    every paragraph function private.
    """

    def run(
        self,
        ws_calling_data: object,
        system_record: object,
        to_day: str,
        file_defs: object,
        /,
        *,
        work_files: object | None = ...,
    ) -> object:
        """Run the program. Returns the work-file container, or None."""


class _CycleWorkFiles:
    """The ONE work-file container the three phases of the cycle share.

    WHY A HOLDER RATHER THAN A LOCAL. The container has to outlive one dispatch and
    reach the next two, because that is how the phases communicate.

    Attributes:
        container: the cycle's work files once a dispatch has produced them, and None
            before that. Passed to every dispatch as-is.
    """

    __slots__ = ("container",)

    def __init__(self) -> None:
        """Start with no container. The first dispatch produces one."""
        self.container: object | None = None


def load00(
    linkage: args.GlLinkage,
    program: _GlProgram,
    program_id: str,
    *,
    menu_state: args.MenuState,
    work_files: _CycleWorkFiles | None = None,
) -> _Disposition:
    """`load00.` [general/general.cbl:L711-L721] - dispatch one program.

    THE PARAGRAPH ENDS AT L721, AND THAT IS WHY THE ABORT GATE IS REACHABLE.
    `load00-exit.` [general/general.cbl:L723] is a SEPARATE paragraph, so its `go to
    display-menu` [general/general.cbl:L725] is NOT part of the range that `perform
    load00` executes.

    Args:
        linkage: the four `CALL` arguments in COBOL parameter order
            [general/gl070.cbl:L245-L248]. The carrier is immutable.
        program: the callee, as a module publishing `run`.
        program_id: the literal the menu moves into `WS-Called` immediately before
            transferring here - `"gl070"`, `"gl071"` or `"gl072"`
            [general/general.cbl:L808], [general/general.cbl:L812],
            [general/general.cbl:L814]. Written into the record for
            traceability and for any callee that reads it.
        menu_state: the menu shell's own WORKING-STORAGE, as `main` created it
            and as `args.bind_gl_linkage` loaded through it. Required rather than
            optional: `overrewrite` on the `> 7` arm needs it, and a dispatch that
            could not persist would be the very gap this parameter closes.
        work_files: the cycle's shared work-file holder. Keyword-only and NOT a
            linkage parameter - see `_CycleWorkFiles`. Omitting it dispatches the
            program against work files of its own, which is what a single
            standalone dispatch wants and what every program module's own
            `work_files=None` default already means. IT IS THE ONLY KEYWORD THIS
            FUNCTION FORWARDS, AND THE ONLY ONE IT ACCEPTS BEYOND `menu_state`:
            none of the three callees declares any other, so offering one would
            raise `TypeError` before the dispatch. A `transport` parameter was
            declared here once and neither read nor forwarded - no caller supplied
            it and no callee accepts it - so it is gone again (finding F-03, the
            recurrence of B2-F5). The operator's transport declaration reaches the
            handlers through the process-level policy
            `args.install_connection_policy` installs while the linkage is bound,
            not call by call - see the comment at the dispatch.

    Returns:
        `_Disposition.SERIOUS_ERROR` when the callee reported `> 7`, in which case
        `args.overrewrite` has already run - this function reproduces the transfer
        to `overrewrite.` rather than reporting that one is due. Otherwise
        `_Disposition.CONTINUE`, and nothing has been persisted, because the
        frozen paragraph's ordinary exit at [general/general.cbl:L722] persists
        nothing - the quit-time `overrewrite` [general/general.cbl:L595-L596] is
        then still owed, and `main` performs it once. A code of 5 returns
        `CONTINUE`, deliberately: see THE THRESHOLD above.

    Raises:
        Exception: whatever the callee raises is propagated unchanged. Nothing is caught
            here.
    """
    carrier = _CycleWorkFiles() if work_files is None else work_files

    # 714 move zero to ws-term-code. REPRODUCED (rule R-4). First, and once per dispatch
    # - see the docstring on why the placement is load-bearing rather than tidy.
    args.reset_term_code(linkage.calling_data)

    # `move "<prog>" to ws-called.` - the statement each caller of this paragraph
    # executes immediately before transferring here [general/general.cbl:L808],
    # [general/general.cbl:L812], [general/general.cbl:L814].
    args.set_called(linkage.calling_data, program_id)

    _LOG.info("dispatching %s (general/general.cbl:L715-L718)", program_id)

    # 715  call     ws-called using ws-calling-data
    # 716                           system-record
    # 717                           to-day
    # 718                           file-defs
    # 719  end-call
    #      FOUR POSITIONAL ARGUMENTS, IN THE COBOL ORDER. `args.GlLinkage` holds
    #      them in that order, so the splat below and L715-L718 above are the same
    #      list and can be diffed line for line. The ONE keyword is `work_files`,
    #      which is not a COBOL operand at all - see `_CycleWorkFiles`.
    #
    #  THE OPERATOR'S TRANSPORT DECLARATION IS NOT THREADED THROUGH HERE, AND THE
    #  REASON IS A FACT ABOUT THE THREE CALLEES RATHER THAN A PREFERENCE. None of
    #  `gl070.run`, `gl071.run` or `gl072.run` declares a `transport` parameter -
    #  their keyword-only parameters are `work_files` and, for two of them,
    #  `file_access`, `dal_common` and `states` - so offering one would raise
    #  `TypeError` before the dispatch and the phase would never run. It is not a
    #  COBOL operand either: the frozen `CALL` at L715-L718 passes four things and
    #  no fifth, its bridge having no transport policy to pass
    #  [copybooks/mysql-procedures.cpy:L72-L77]. What carries the declaration
    #  instead is the ONE process-level policy `args.install_connection_policy`
    #  installs while the linkage is bound, from the deployment contract alone,
    #  so every handler any phase reaches observes it without being told.
    #  That is the same mechanism the other six routes use; `gl_end_of_cycle.py`
    #  differs only because `gl080.run` DOES declare `dal_options`, and even there
    #  the route leaves it unset for exactly this reason.
    returned = program.run(*linkage, work_files=carrier.container)

    # The one conditional that is a Python-language necessity rather than a test of any
    # value the COBOL tests.
    if returned is not None:
        carrier.container = returned

    # 720  if       ws-term-code > 7
    # 721           go to overrewrite.
    #      GO TO class 4 (sibling re-dispatch). PER-SITE PROOF OF EQUIVALENCE,
    #      required because class 4 is the only class that needs one (Agent Action
    #      Plan section 0.4.2):
    #        COBOL: `go to overrewrite` reaches `overrewrite.`
    #               [general/general.cbl:L656], which persists the system records,
    #               then FALLS THROUGH into `overclose.`
    #               [general/general.cbl:L693] and ends the run unit at `goback`
    #               [general/general.cbl:L694]. Control never comes back to this
    #               paragraph and no further program is called.
    #        Python: perform `args.overrewrite` - the same paragraph, reproduced
    #               once in `args.py` and shared by the routes - then return
    #               `SERIOUS_ERROR`; `load08` returns at once and `main` returns
    #               `args.exit_status_for(ws_term_code)`, so the process ends
    #               carrying the reported code.
    #        PROOF: in both implementations the system records are persisted, then
    #               control never returns to the dispatch paragraph and no further
    #               program is invoked - so the set of programs run and the
    #               database effect are identical.
    #      THE PERSISTENCE IS ON THIS ARM ALONE WITHIN THIS PARAGRAPH, AND THAT IS
    #      THE FROZEN SHAPE. `load00.` has exactly one transfer to `overrewrite`,
    #      guarded by `> 7` [general/general.cbl:L720-L721]; the ordinary exit at
    #      L722 persists NOTHING. This is where the General menu differs from the
    #      Sales and Purchase ones, whose `load000.` performs `overrewrite` on BOTH
    #      arms [sales/sales.cbl:L708-L712], [purchase/purchase.cbl:L701-L704].
    #      Neither `load08.` nor `load09.` adds a persist of its own - `load03`
    #      through `load06` do, and none of those four serves an in-scope program.
    #      The asymmetry is reproduced, not smoothed away (rule R-4).
    #      WHAT PERSISTS ON THE ORDINARY EXIT IS THE MENU QUIT, NOT THIS PARAGRAPH.
    #      `main` performs `args.overrewrite` once when the run completes without a
    #      serious code, reproducing [general/general.cbl:L595-L596] and the
    #      paragraph it transfers to - a different statement of the frozen session,
    #      not a `< 8` arm added to this one. The guard there is this same
    #      predicate, so the two sites cannot both fire.
    #      REPRODUCED (rule R-4): the predicate is the threshold `> 7` the frozen
    #      source writes, evaluated through `args.is_serious_error`, so this route
    #      and the six others share one implementation of it.
    #
    #      THE GENERAL LEDGER SHELL HAS NO `< 8` ARM, and that is a divergence, not
    #      an omission. `load00.` performs the persistence ONLY on this branch
    #      [general/general.cbl:L720-L721], where the Sales and Purchase
    #      `load000.` paragraphs perform it on both arms and therefore after every
    #      dispatch [sales/sales.cbl:L708-L712],
    #      [purchase/purchase.cbl:L701-L704]. Adding a `< 8` arm here would make
    #      the General Ledger route write rows the frozen one leaves alone
    #      (rule R-3), so none is added. Note also that `load00.` is not the only
    #      General Ledger path to the paragraph - `load03.` through `load06.`
    #      perform it explicitly after their own dispatch
    #      [general/general.cbl:L766-L768] - but every one of those routes
    #      dispatches an out-of-scope program, so none of them is this module's.
    if args.is_serious_error(linkage.calling_data.ws_term_code):
        _LOG.error(
            "%s reported a serious error, term code %d "
            "(general/general.cbl:L720-L721)",
            program_id,
            linkage.calling_data.ws_term_code,
        )
        # 721  go to overrewrite.  ->  general/general.cbl:L656-L672
        args.overrewrite(linkage.system_record, menu_state, linkage.file_defs)
        return _Disposition.SERIOUS_ERROR

    return _Disposition.CONTINUE


def load08(linkage: args.GlLinkage, *, menu_state: args.MenuState) -> None:
    """`load08.` [general/general.cbl:L805-L815] - run the posting cycle.

    Three phases, one at a time, with the abort gate between the first and the second.
    Rule R-3 names this function's file for exactly this.

    Args:
        linkage: the four `CALL` arguments in COBOL parameter order
            [general/gl070.cbl:L245-L248], as `main` bound them. `WS-Called` is
            overwritten per dispatch and `WS-Term-Code` is cleared per dispatch,
            exactly as the menu does, so the value the caller arrives with in
            either field is not read.
        menu_state: the menu's own WORKING-STORAGE, built by
            `args.general_menu_state()` and loaded by
            `args.aa010_get_system_recs`, carrying the `SYSTEM-REC` this linkage
            was bound from together with `SYSTOT-REC` and `SYSDEFLT-REC`.
            Threaded into each dispatch so that the `> 7` arm of `load00.` can
            reach `overrewrite.` [general/general.cbl:L720-L721].

    Returns:
        None. The cycle reports through `WS-Term-Code` inside
        `linkage.calling_data` and through nothing else, exactly as the frozen
        menu does - which is why `main` reads that field afterwards rather than a
        return value, both for the exit status and to decide whether the
        quit-time `overrewrite` is still owed. After the gate has fired the field
        holds `args.GL_ABORT_TERM_CODE`; after a clean cycle it holds the zero the
        last dispatch reset it to; and above `args.SERIOUS_ERROR_THRESHOLD` it
        means a phase reported seriously AND `load00` has already persisted.

    Raises:
        Exception: propagated unchanged from a phase. See `load00`.
    """
    work_files = _CycleWorkFiles()

    disposition = load00(
        linkage,
        gl070_transaction_pre_process,
        _GL070,
        menu_state=menu_state,
        work_files=work_files,
    )

    # Not a statement of `load08.`, but the disposition of L720-L721 inside the
    # paragraph just performed.
    if disposition is _Disposition.SERIOUS_ERROR:
        return

    # 810 if ws-term-code = 5 811 go to display-menu. ⭐ THE HARD GATE.
    if linkage.calling_data.ws_term_code == args.GL_ABORT_TERM_CODE:
        _LOG.warning(
            "%s left a batch open and raised term code %d "
            "(general/gl070.cbl:L289); the cycle stops here and %s and %s do NOT "
            "run (general/general.cbl:L810-L811)",
            _GL070,
            args.GL_ABORT_TERM_CODE,
            _GL071,
            _GL072,
        )
        return

    # 812  move     "gl071" to ws-called.
    # 813  perform  load00.
    #      THE SORT. Its output ordering is a hard contract consumed by `gl072`
    #      [general/gl071.cbl:L172-L176].
    #      ⛔ NO GATE OF `load08.`'s OWN FOLLOWS THIS DISPATCH. REPRODUCED
    #      (rule R-4): the frozen source runs straight from L813 into L814 with no
    #      test of any kind [general/general.cbl:L813-L814], and `gl071` never
    #      writes `WS-Term-Code` at all - the string does not occur in
    #      general/gl071.cbl. No `= 5` gate is added here "for symmetry" with L810,
    #      because that would invent a stop the COBOL has not got.
    disposition = load00(
        linkage,
        gl071_batch_sort,
        _GL071,
        menu_state=menu_state,
        work_files=work_files,
    )

    #      ⭐ BUT THE DISPATCH PARAGRAPH'S OWN TRANSFER STILL APPLIES, AND IT IS
    #      NOT A GATE OF THIS PARAGRAPH. `load00.` ends `if ws-term-code > 7 / go
    #      to overrewrite` [general/general.cbl:L720-L721], and that transfer
    #      leaves the dispatch paragraph for `overrewrite.`
    #      [general/general.cbl:L656], falls through into `overclose.`
    #      [general/general.cbl:L693] and ends the run unit at `goback`
    #      [general/general.cbl:L694]. Control never returns to L814, so `gl072`
    #      cannot run. The FIRST dispatch above honours that contract and this one
    #      must honour it identically - which is what returning here does. The
    #      persistence has already happened inside `load00`; nothing is repeated.
    #
    #      LATENT, AND IMPLEMENTED ANYWAY. `gl071` never assigns `WS-Term-Code`,
    #      and L714 clears the field before the `CALL`, so the value read back can
    #      only be the zero just written and this branch cannot be taken by this
    #      callee. It is written because the frozen dispatch paragraph contains the
    #      transfer, exactly as the `> 7` branch inside `load00` is written for
    #      `gl071` although the same reasoning applies there - and because a
    #      neighbour contract that holds for one dispatch and not for its sibling
    #      is wrong even when nothing currently trips it.
    if disposition is _Disposition.SERIOUS_ERROR:
        return

    # 814  move     "gl072" to ws-called.
    # 815  go       to load00.
    #      PHASE 4 (transaction update) - the only phase of the cycle that posts.
    #      GO TO class 4 (sibling re-dispatch), and the class matters here for one
    #      reason only: this is `go to load00`, NOT `perform load00` as L809 and
    #      L813 are. PER-SITE PROOF OF EQUIVALENCE:
    #        COBOL: control transfers into `load00.`, which dispatches `gl072`
    #               and then FALLS THROUGH into `load00-exit.`
    #               [general/general.cbl:L723] and leaves for `display-menu`
    #               [general/general.cbl:L725]. It does not come back to
    #               `load08.`, so nothing after L815 in this paragraph can run -
    #               and indeed L816 is the rule line that ends it.
    #        Python: the call is the last statement of this function, so nothing
    #               after it runs either.
    #        PROOF: identical set of invoked programs and identical database
    #               effect; the difference is only the menu redraw, OMISSION 1.
    #      ⛔ NOTHING MAY BE ADDED AFTER THIS CALL. The distinction between `go
    #      to` and `perform` at this site is real in COBOL and is preserved by
    #      that emptiness, not by a comment alone. The disposition is deliberately
    #      not read: `load08.` has nowhere left to take it, and `main` reads
    #      `WS-Term-Code` itself.
    load00(
        linkage,
        gl072_transaction_update,
        _GL072,
        menu_state=menu_state,
        work_files=work_files,
    )


def _build_parser() -> argparse.ArgumentParser:
    """Build this route's parser by composing the two published fragments.

    COMPOSED, NEVER REDEFINED. Both option groups come from `acas_posting.cli.args`,
    which owns the binding of `01 WS-Calling-Data` [copybooks/wscall.cob:L6-L14], of the
    run date and of the system record.

    Returns:
        A parser requiring `--run-date` and accepting the five calling-data options plus
            the two pinnable system-record fields.
    """
    parser = argparse.ArgumentParser(
        prog="python -m acas_posting.cli.gl_post_cycle",
        description=(
            "Run the General Ledger posting cycle: gl070, then the "
            "ws-term-code = 5 abort gate, then gl071, then gl072. Reproduces "
            "general/general.cbl load08. (L805-L815) through its dispatch "
            "paragraph load00. (L711-L721). Batch and headless: no screen "
            "output, no prompts, and the run date is never taken from the "
            "system clock."
        ),
        epilog=(
            "Exit status is WS-Term-Code itself (copybooks/wscall.cob:L10): 0 "
            "when all three phases ran, "
            f"{args.GL_ABORT_TERM_CODE} when gl070 found a batch left open and "
            "the abort gate stopped the cycle before gl071 and gl072 "
            "(general/general.cbl:L810-L811), and the reported code when a "
            f"phase failed seriously, that is above "
            f"{args.SERIOUS_ERROR_THRESHOLD} "
            "(general/general.cbl:L720-L721)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # `move "general" to ws-caller.` [general/general.cbl:L512] - this route's
    # dispatching menu is the General Ledger one, so that is the default identity.
    args.add_calling_data_arguments(parser, default_caller=args.WS_CALLER_GENERAL)
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
    #  Diagnostics only: no COBOL counterpart, no database effect. Shared with
    #  the other six routes so the level policy has one spelling.
    args.add_log_level_argument(parser)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """The command-line boundary. No COBOL counterpart.

    What the frozen program has here is a menu: `display-menu.`
    [general/general.cbl:L509] draws the screen, `accept-loop.`
    [general/general.cbl:L591] reads a keystroke and
    `go to load01 ... depending on z` [general/general.cbl:L696-L704] dispatches
    the selection. All of that is removed rather than reimplemented (Agent Action
    Plan section 0.3.4) and this function stands in its place: one selection, made
    on the command line, run once, non-interactively.

    THE RUN DATE IS AN ARGUMENT AND NEVER A CLOCK READING (rule R-6). `--run-date`
    is required, has no default, no environment fallback and no test hook, and
    `args.bind_gl_linkage` pins BOTH observables from it - the text `to-day
    pic x(10)` and the binary `Run-Date` [copybooks/wssystem.cob:L67]. The frozen
    call chain holds FOURTEEN ambient date and time reads across six files - the
    census is in `acas_posting/clock.py` and in `cli/args.py` - but every one of
    them is in an out-of-scope menu shell or in the date-service copybook those
    shells COPY, and all three programs dispatched below contain zero clock reads.
    So pinning here is sufficient to make two runs of one scenario byte-identical
    (Agent Action Plan section 0.8.5).

    Args:
        argv: the argument vector, WITHOUT the program name. None reads `sys.argv[1:]`,
            which is what argparse does by default and what a real invocation wants.

    Returns:
        `WS-Term-Code` as the process exit status, through
        `args.exit_status_for`, which is the identity - so a caller reads the code
        the cycle produced rather than a re-encoding of it. Zero when all three
        phases ran; `args.GL_ABORT_TERM_CODE` when the abort gate fired; the
        reported code when a phase failed seriously; and the parameter loader's own
        frozen return code, through `args.report_configuration_failure`, when the
        deployment contract for the database connection is absent or unusable.

    Raises:
        SystemExit: raised by argparse for `--help` and for a usage error, such as
            the required `--run-date` being absent. Deliberately not caught: an
            omitted run date must fail, because the only alternative is an ambient
            one.
        Exception: propagated unchanged from a phase. THIS IS THE LIBRARY
            CONTRACT and it has not changed: a caller that imports this function
            still receives the exception, with its traceback, which is the only
            diagnostic a genuine defect leaves behind. What changed is that the
            PROCESS boundary no longer lets one reach a terminal:
            `acas_posting.__main__.run_entry_point` converts it into one
            sanitised ERROR record and a deterministic exit status, because a
            traceback on stderr prints absolute paths, source lines and whatever
            text the exception carries.
    """
    parser = _build_parser()
    namespace = parser.parse_args(argv)

    #  THE MENU'S OWN WORKING-STORAGE, created once and shared by the load and by
    #  the persist, exactly as one menu program's single `01 File-Access` serves
    #  `aa010-Get-System-Recs` and `overrewrite` both. The General menu is the only
    #  one of the four that carries a defaults record as well as a totals record -
    #  see `args.general_menu_state`.
    menu_state = args.general_menu_state()

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

    #  `move "gl070" to ws-called.` [general/general.cbl:L808] - the first
    #  dispatch of the cycle, so the record is bound with the first callee's
    #  program-id. `load00` sets the field again before each of the three
    #  dispatches, exactly as L808, L812 and L814 do.
    #
    #  BINDING NOW ALSO LOADS - `Open-System.` [general/general.cbl:L385] then
    #  `aa010-Get-System-Recs.` [general/general.cbl:L398-L419]. Passing
    #  `menu_state` makes the binder perform both BEFORE it fills
    #  `WS-Calling-Data`, which is the order the frozen menu establishes its state
    #  in - the load at L385-L419, `move "general" to ws-caller` at L512 - and so
    #  before `display-menu.` and therefore before any `load` paragraph runs. The
    #  records are the menu's own and the linkage carries the same `SystemRecord`,
    #  so what is read there is what `gl070`, `gl071` and `gl072` then see: the
    #  seed's accounting cycle, its account switches, its VAT rates and its
    #  file-system selector, rather than the record layer's declared defaults
    #  (finding CLI-02).
    #
    #  THE KEY ORDER IS 4, THEN 2, THEN 1, and key 2 is the General Ledger menu's
    #  alone [general/general.cbl:L406-L408]; Sales reads keys 4 and 1
    #  [sales/sales.cbl:L355-L360] and Purchase the same
    #  [purchase/purchase.cbl:L350-L354]. `args.general_menu_state` carries all
    #  three records and `args.aa010_get_system_recs` reads a key only when its
    #  record is present, so that asymmetry comes out of one implementation.
    #
    #  A FAILING READ IS NOT REFUSED HERE. The frozen paragraph answers `if
    #  fs-reply not = zero` by running the parameter-file set-up program and
    #  looping back [general/general.cbl:L412-L417] - a GO TO class 1 over an
    #  interactive recovery, whose own comment says the branch "should NOT happen
    #  as done in open-system". `common/sys002.cbl` is out of scope (Agent Action
    #  Plan section 0.2.2) and prompts an operator this process does not have, so
    #  the recovery is not reproduced and the reply is left in `File-Access`
    #  exactly as it is for every other handler failure in the migrated cycle.
    #  Refusing the run instead would be a new validation (rule R-3). Recorded at
    #  `args.aa010_get_system_recs`.
    #
    #  THE EXACT TYPE IS CAUGHT, NOT `ValueError` (finding CLI-09). The deployment
    #  contract for the six connection parameters is resolved inside the binder,
    #  before the store is opened, so a failure here has touched nothing: no
    #  database contacted, no file opened, no program entered. Catching the base
    #  class also swallowed a genuine defect and reported it as a configuration
    #  problem, so only the exact type is caught and everything else keeps its
    #  traceback. `RdbmsParamError` never carries a parameter value, so reporting
    #  it cannot leak a credential.
    try:
        linkage = args.bind_gl_linkage(
            namespace, called=_GL070, menu_state=menu_state
        )
    except args.RdbmsParamError as error:
        return args.report_configuration_failure(
            error, logger=_LOG, subject="General Ledger"
        )

    #  805  load08.
    load08(linkage, menu_state=menu_state)

    #  595  if       menu-reply = "X"
    #  596           go to pre-overrewrite.
    #  634  pre-overrewrite.  ->  656  overrewrite.  ->  693 overclose. 694 goback.
    #  ⭐ THE MENU-QUIT PERSISTENCE, AND PROCESS COMPLETION IS THE MENU QUIT.
    #  This is the one statement of the frozen session that `load08.` itself does
    #  not contain and that a headless one-shot process must still perform, because
    #  the callees MUTATE the caller's `SYSTEM-REC` by reference -
    #  `gl070_transaction_pre_process` writes `Date-Form` at its own L2013 and
    #  L2064 and `gl072_transaction_update` at its L761, reproducing
    #  `zz070-Convert-Date`'s write-back [general/gl070.cbl:L580-L581] - and
    #  nothing else in this route writes those changes to the store.
    #
    #  WHY THIS IS THE FROZEN SHAPE AND NOT AN ADDITION. A frozen SESSION cannot
    #  end any other way: `display-menu.` is a loop, the only exit is the quit key
    #  [general/general.cbl:L595-L596], and that key reaches `overrewrite.` whether
    #  or not a backup script is installed - `go to overrewrite`
    #  [general/general.cbl:L636] when none is, `perform overrewrite`
    #  [general/general.cbl:L649] when one is. So every operator who runs the
    #  posting cycle and then leaves the menu persists the mutated records, exactly
    #  once. A one-shot process runs ONE operation per session, so its ordinary
    #  completion IS that session end, and performing the paragraph once here is
    #  what makes the two runs comparable at all: `harness/run_cobol_scenario.sh`
    #  drives the oracle through the same menu and leaves it with "X", so the
    #  COBOL side of every scenario carries these writes (Agent Action Plan
    #  section 0.8.5's empty ordering-normalised diff).
    #
    #  EXACTLY ONCE, AND THE GUARD IS WHAT MAKES IT SO. `load00.` transfers to
    #  `overrewrite` on its own `> 7` arm [general/general.cbl:L720-L721], and
    #  `load00` above has already performed the paragraph and returned
    #  `SERIOUS_ERROR` on that arm, after which `load08` returns at once. So a term
    #  code above 7 here means the persistence has ALREADY happened and the frozen
    #  `goback` [general/general.cbl:L694] has already ended the run unit - there
    #  is no second `overrewrite` to perform, and performing one would write the
    #  same rows twice. Every other code, INCLUDING the abort code 5, reaches this
    #  line unpersisted: the frozen menu answers a 5 with `go to display-menu`
    #  [general/general.cbl:L810-L811] and persists later, at the quit, which is
    #  here. The predicate is `args.is_serious_error`, the same implementation the
    #  `> 7` arm uses, so the two cannot disagree about the band.
    #
    #  NOT REPRODUCED, and recorded as OMISSION 2 in the footer: the backup
    #  spool-out half of `pre-overrewrite.` - the `string "nohup " ... Run-Backup`
    #  assembly [general/general.cbl:L637-L648] and the `call "SYSTEM" using
    #  Full-Backup-Script` [general/general.cbl:L650] - which Agent Action Plan
    #  section 0.2.2 excludes as a spool-out path and rule R-1 excludes again. It
    #  has no database effect; the persistence beside it has nothing but.
    if not args.is_serious_error(linkage.calling_data.ws_term_code):
        _LOG.info(
            "persisting the system records once, as the menu does at its quit key "
            "(general/general.cbl:L595-L596 -> L656-L672); ws-term-code %d",
            linkage.calling_data.ws_term_code,
        )
        args.overrewrite(linkage.system_record, menu_state, linkage.file_defs)

    return args.exit_status_for(linkage.calling_data.ws_term_code)


if __name__ == "__main__":
    #  `pyproject.toml` declares no `[project.scripts]`, so `python -m
    #  acas_posting` is the packaged route - but the oracle comparison scripts
    #  drive these entry points as modules,
    #  `python -m acas_posting.cli.gl_post_cycle`, so direct execution has to
    #  work. Rule R-1 runs the other way round: those scripts are a sibling of
    #  the shipped package and drive it from OUTSIDE, and nothing here reaches
    #  back towards them.
    #
    #  BOTH ROUTES SHARE ONE PROCESS BOUNDARY. `run_entry_point` configures
    #  logging once and converts a failure into one sanitised ERROR record and a
    #  deterministic exit status, so this module behaves identically whether it
    #  was reached through the router or executed directly. The import is inside
    #  the guard rather than at module scope for two reasons: it is needed only
    #  when this module IS the process, and it keeps the module's import list
    #  free of the router, which imports this module back when the router is the
    #  process. `raise SystemExit(...)` rather than `sys.exit(...)` keeps `sys`
    #  off the import list.
    from acas_posting.__main__ import run_entry_point

    raise SystemExit(run_entry_point(main, command="gl-post-cycle"))


# --- traceability ------------------------------------------------------------
#
# Rule R-5. Every construct of general/general.cbl `load08.` and `load00.` mapped
# to what reproduces it here, every `GO TO` classified, every correction to a
# planning locator stated, and every deliberate omission recorded AS an omission -
# Agent Action Plan section 0.4.3, verbatim on why: "so that a reader comparing
# the two files does not conclude something was lost."
#
# THERE IS NO USER RULES DOCUMENT. `review_rules` reports "No user rules
# provided", so nothing on disk is being complied with here and none has been
# invented. The six binding rules R-1 to R-6 are the Agent Action Plan's own,
# section 0.7.2, and their exact wording is retrievable from the requirements.
# Where they are silent, enterprise-standard best practice applies.
#
# MODULE  <-  COBOL SOURCE
#   acas_posting/cli/gl_post_cycle.py  <-  general/general.cbl  (931 lines,
#   program-id `general` [general/general.cbl:L36], FROZEN). Boundary: the
#   posting-cycle dispatch paragraph `load08.` L805-L815 and the shared dispatch
#   paragraph `load00.` L711-L721 that it performs three times. Everything else in
#   that file is out of scope (Agent Action Plan section 0.2.2) - it is an
#   interactive menu program.
#
# FUNCTION  ->  PARAGRAPH
#   load00              ->  `load00.`  [general/general.cbl:L711-L721]
#                           L714 reset, L715-L718 CALL, L719 end-call,
#                           L720-L721 the `> 7` test.
#   load08              ->  `load08.`  [general/general.cbl:L805-L815]
#                           L808/L812/L814 the three `move ... to ws-called`,
#                           L809/L813 `perform load00`, L810-L811 the `= 5` gate,
#                           L815 `go to load00`.
#   main                ->  THE CLI BOUNDARY. No COBOL counterpart: the menu's
#                           `display-menu.` [general/general.cbl:L509],
#                           `accept-loop.` [general/general.cbl:L591] and
#                           `go to load01 ... depending on z`
#                           [general/general.cbl:L696-L704] are removed, not
#                           reimplemented (Agent Action Plan section 0.3.4).
#   _build_parser       ->  no counterpart. Composes the two option groups that
#                           `cli/args.py` publishes; declares no option of its own.
#   (`_binding_exit_status` was REMOVED. It caught every `ValueError` and mapped
#    it to a status, which swallowed genuine defects alongside the configuration
#    failure it was written for. `args.report_configuration_failure` replaces it
#    for all seven routes, catching the exact `args.RdbmsParamError` and surfacing
#    the same frozen codes [common/acas-get-params.cbl:L37-L42] - finding CLI-09.)
#   _Disposition        ->  the two exits of `load00.` - falling off the end at
#                           L721, and `go to overrewrite` at L720-L721.
#   _GlProgram          ->  `call ws-called using ...`
#                           [general/general.cbl:L715-L718], the dynamic call by
#                           name, resolved by module choice because rule R-1
#                           leaves no COBOL runtime to resolve a name against.
#   _CycleWorkFiles     ->  the FILE SECTIONs over `pre-trans` and `post-trans`
#                           [copybooks/wsnames.cob:L15-L16]; work files, not
#                           tables, and absent from every table dump.
#
# PROGRAM  ->  MODULE  (the three callees; business logic lives only there)
#   gl070  ->  acas_posting/programs/gl070_transaction_pre_process.py
#              linkage [general/gl070.cbl:L245-L248]. THE ONLY ONE OF THE THREE
#              THAT SETS `WS-Term-Code` - to 5, on the abort path
#              [general/gl070.cbl:L289], and nowhere else.
#   gl071  ->  acas_posting/programs/gl071_batch_sort.py
#              linkage [general/gl071.cbl:L161-L164]. Keeps all four parameters
#              although three are unread. Never sets the term code: the string
#              does not occur in the file.
#   gl072  ->  acas_posting/programs/gl072_transaction_update.py
#              linkage [general/gl072.cbl:L262-L265]. Never sets the term code.
#   Only three of the twelve in-scope programs ever set it at all: `gl070` to 5
#   [general/gl070.cbl:L289], `sl055` to 8 [sales/sl055.cbl:L344] and `pl055` to 8
#   [purchase/pl055.cbl:L286].
#
# `GO TO` CLASSES  (the four-class taxonomy, Agent Action Plan section 0.4.2)
#   Every transfer reachable from these two paragraphs is CLASS 4, sibling
#   re-dispatch - the only class that requires per-site proof of equivalence. All
#   three proofs are written at their sites; they are indexed here.
#     L720-L721  `go to overrewrite`     ->  args.overrewrite(...) then return
#                                            _Disposition.SERIOUS_ERROR
#                proof at the `> 7` site in `load00`. The transfer is reproduced
#                in full: the paragraph runs, then control does not come back.
#     L810-L811  `go to display-menu`    ->  return from `load08`
#                proof at the gate site in `load08`. THE HARD GATE.
#     L815       `go to load00`          ->  the last statement of `load08`
#                proof at the third dispatch site in `load08`. This is a `go to`
#                where L809 and L813 are `perform`, and the difference is
#                preserved by nothing following the call.
#   Not reachable by `perform load00`, and therefore not translated: L725
#   `go to display-menu` in `load00-exit.` [general/general.cbl:L723-L725].
#   Its unreachability under `perform` IS the structural fact that makes the gate
#   at L810 reachable, and it is recorded in `load00`'s docstring for that reason.
#   Classes 1, 2 and 3 do not occur here: neither paragraph loops, neither has a
#   forward terminator and neither has an exit label of its own.
#
# `PERFORM ... THRU`
#   None in either paragraph. The construct occurs only seven times across the
#   whole in-scope set, none of them here.
#
# CORRECTIONS TO PLANNING LOCATORS  (each verified by reading the frozen source)
#   1. THE `gl070` RAISE IS AT L289, NOT L288. The Agent Action Plan and the
#      folder brief both cite [general/gl070.cbl:L288] as the raising site. L288
#      is `perform gl060a`. The raise is `move 5 to ws-term-code` at
#      [general/gl070.cbl:L289], inside the conditional
#      [general/gl070.cbl:L287-L290]. Related, and also worth stating so the two
#      are not confused with a raiser: [general/gl070.cbl:L312-L313] is the CYCLE
#      FILTER, `if bcycle not = scycle go to loop`, and
#      [general/gl070.cbl:L314-L315] is the OPEN-BATCH DETECTOR,
#      `if status-open move 1 to a`. Do not "fix" any of this back.
#   2. `gl072`'s PHASE 4 BANNER IS AT L274, NOT L277. The plan cites
#      [general/gl072.cbl:L277]; the `display "Phase - 4.  Transaction Update"`
#      is at [general/gl072.cbl:L274].
#   3. `gl072`'s SEQUENTIAL NOMINAL READ IS AT L407-L408, NOT L410-L412. The plan
#      cites [general/gl072.cbl:L410-L412], which is
#      `move zero to tot-dr tot-cr`; the read itself is
#      `if read-ledger not = "R" / perform GL-Nominal-Read-Next` at
#      [general/gl072.cbl:L407-L408]. The sort-order dependency the plan draws
#      from it is unaffected and is reproduced.
#   4. `gl080`'s PHASE 5 BANNER IS AT L336, NOT L330. The plan cites
#      [general/gl080.cbl:L330]. Phase 3 at [general/gl080.cbl:L319] is as cited.
#      That program is dispatched from the sibling entry point, not from here.
#
# ANOMALIES REPRODUCED, NEVER FIXED  (rule R-4; each has a comment at its site
# citing its locator, as Agent Action Plan section 0.7.4 C-4 requires)
#   1. THE GATE PREDICATE IS AN EQUALITY, `= 5`
#      [general/general.cbl:L810-L811] - not `>= 5`, not `> 4`, not
#      `not = zero`. The Sales route tests `not = zero`
#      [sales/sales.cbl:L761-L762], [sales/sales.cbl:L765-L766] and the Purchase
#      route has no paragraph-level gate at all, its lines commented out in the
#      frozen source [purchase/purchase.cbl:L755-L758]. THE THREE FORMS STAY
#      DIFFERENT. Harmonising them would be a behaviour change and therefore a
#      failure.
#   2. NO GATE OF `load08.`'s OWN AFTER `gl071` [general/general.cbl:L813-L814].
#      L813 runs straight into L814 with no `= 5` test of any kind, and none is
#      added "for symmetry" with L810. What DOES still apply after that dispatch is
#      the dispatch paragraph's own `if ws-term-code > 7 / go to overrewrite`
#      [general/general.cbl:L720-L721], which leaves `load00.` for `overrewrite.`
#      and ends the run unit at `goback` [general/general.cbl:L694] - so control
#      never reaches L814 and `gl072` cannot run. `load08` honours that after ALL
#      THREE dispatches, not just the first: the returned disposition is read after
#      `gl071` as well. Latent, because `gl071` never assigns `WS-Term-Code` - the
#      string does not occur in general/gl071.cbl - and implemented anyway, because
#      the transfer belongs to the paragraph being reproduced.
#   3. `move zero to ws-term-code` BEFORE EVERY CALL
#      [general/general.cbl:L714] - per dispatch, not once per run, so no code is
#      ever carried from one phase into the next.
#   4. THE THRESHOLD IS `> 7` [general/general.cbl:L720-L721], evaluated through
#      `args.is_serious_error` so that all seven entry points share one
#      implementation of the frozen predicate.
#   5. AND THE TWO INTERACT: because L714 has just cleared the field, a `gl070`
#      code of 5 is NOT `> 7`, so `load00.` does NOT take the `overrewrite` exit.
#      The stop is purely the paragraph gate at L810-L811, whose disposition is
#      RETURN TO THE MENU and not program exit. That is the whole reason the
#      General Ledger route differs from Sales and Purchase, whose own dispatch
#      paragraphs add a `goback` to the `> 7` branch
#      [sales/sales.cbl:L710-L712], [purchase/purchase.cbl:L703-L704] and whose
#      abort code, 8, IS greater than 7. No Sales or Purchase reasoning is
#      imported into this file.
#
# OMISSIONS  (deliberate; recorded so nothing looks lost)
#   1. `display-menu.` [general/general.cbl:L509] and all menu screen I/O, the
#      `accept-loop.` [general/general.cbl:L591] keystroke loop, and the
#      `go to load01 load02 ... depending on z` dispatch table
#      [general/general.cbl:L696-L704] with its `loader.` catch-all
#      [general/general.cbl:L706-L709]. Screen output with no database effect is
#      dropped (Agent Action Plan section 0.3.4); `main` replaces the selection
#      with one command line.
#   2. NOT OMITTED AT ALL, AND THE SECOND HALF OF THIS ENTRY WAS REVISED -
#      `overrewrite.` [general/general.cbl:L656] is reproduced by
#      `args.overrewrite`, and it is now performed from TWO places, which is what
#      the frozen session does:
#        * from the `> 7` arm of `load00`, reproducing `go to overrewrite`
#          [general/general.cbl:L720-L721]; and
#        * ONCE from `main`, on ordinary completion, reproducing the quit-time
#          transfer `if menu-reply = "X" / go to pre-overrewrite`
#          [general/general.cbl:L595-L596] and the `go to overrewrite` /
#          `perform overrewrite` inside that paragraph
#          [general/general.cbl:L636], [general/general.cbl:L649].
#      It persists three records - `System-Record` at File-Key-No 1,
#      `Default-Record` at 2 and `WS-System-Record-4` at 4 - and the matching load
#      is performed by `args.aa010_get_system_recs` through the binder before the
#      first dispatch. The two sites are mutually exclusive: `main` guards on
#      `args.is_serious_error`, so the arm that has already persisted does not
#      persist again.
#      WHY THE EARLIER READING - that the quit-time rewrite has "no counterpart in
#      a single-operation process" - WAS WRONG, stated so it is not restored. A
#      frozen SESSION cannot end any other way: `display-menu.` loops and the quit
#      key is its only exit, so every operator who runs `load08.` and then leaves
#      the menu persists the mutated records exactly once. The callees DO mutate
#      them - `gl070` and `gl072` write `Date-Form` back through
#      `zz070-Convert-Date` [general/gl070.cbl:L580-L581] - and
#      `harness/run_cobol_scenario.sh` leaves the oracle's menu with "X", so the
#      COBOL side of every scenario carries those writes. Skipping them here would
#      make Agent Action Plan section 0.8.5's empty ordering-normalised diff
#      unreachable. What is NOT relocated is anything conditional: one operation
#      per process, one persist per process.
#      STILL OMITTED, and only this half: the BACKUP SPOOL-OUT of
#      `pre-overrewrite.` - the `string "nohup " ... Run-Backup` assembly
#      [general/general.cbl:L637-L648] and `call "SYSTEM" using
#      Full-Backup-Script` [general/general.cbl:L650] - excluded by rule R-1 and by
#      Agent Action Plan section 0.2.2's spool-out exclusion. It has no database
#      effect. Also still omitted from `overrewrite.` itself is its COBOL-FILE arm
#      [general/general.cbl:L674-L691]: the migration has no ISAM store, so only
#      the RDB arm has a counterpart - recorded in `acas_posting/cli/args.py`, at
#      `RDBMS_STORE_SELECTOR_DIGIT`. `overclose.` [general/general.cbl:L693] and
#      its `goback` [general/general.cbl:L694] are the return from `main`, not a
#      statement of their own.
#   3. `load12.` [general/general.cbl:L835-L855], which dispatches `gl100` then
#      `gl105` and contains a SECOND `ws-term-code = 5` gate at
#      [general/general.cbl:L844-L845] - whose target is `accept-loop`, NOT
#      `display-menu` - plus a `= 4` branch at
#      [general/general.cbl:L846-L853]. Report programs, out of scope (Agent
#      Action Plan section 0.2.2). NOT ROUTED FROM HERE, and the existence of a
#      second gate with a different disposition is exactly why this one is
#      written out in full rather than shared.
#   4. `load07.` [general/general.cbl:L799-L803] (`gl060`) and `load10.`
#      [general/general.cbl:L823-L827] (`gl090`) - out of scope, not routed. So
#      too `load11.` [general/general.cbl:L829-L833] (`gl120`).
#   5. `load000.` [general/general.cbl:L727-L737]. It looks like the General
#      Ledger shape with one more parameter, but its third argument is
#      `default-record` [general/general.cbl:L733] and it serves `gl020` and
#      `gl050`. NO in-scope General Ledger program uses it, and it is not the
#      Sales and Purchase five-parameter shape either.
#   6. `gl051`'s control-total gate has NO entry point in this package - Agent
#      Action Plan section 0.4.1.1 lists none - so it is not routed from here.
#      The frozen menu reaches the whole interactive `gl051` through `load06.`
#      [general/general.cbl:L790-L797], of which only the `end-batch` block
#      [general/gl051.cbl:L1096-L1133] is in scope, reachable as a library
#      function in `acas_posting.programs.gl051_batch_control_check`.
#   7. `gl080` is not dispatched from here. It is `load09.`
#      [general/general.cbl:L817-L821] and belongs to the sibling entry point
#      `acas_posting/cli/gl_end_of_cycle.py`; phases 3 and 5 live there.
#   8. `general/gl072.cbl:L134-L155`'s `Dummies-4-Unused-ACAS-FH-Calls` block -
#      facade stubs declared only so the linker resolves the copybook's full verb
#      set - is a `programs/` concern and is not translated anywhere. Noted here
#      only so a reviewer knows it was seen.
#
# AMBIGUITY
#   Q-CLI-EXITSTATUS - the COBOL disposition for term code 5 is "return to
#   display-menu", which has no process-status analogue in a single-operation
#   CLI. Locators [general/general.cbl:L810-L811] and
#   [general/general.cbl:L720-L721]; state of the question and the ground the
#   identity mapping rests on are at the `return` in `main`, and the full
#   argument is recorded by `args.exit_status_for`. To be carried into
#   docs/migration/ambiguity-resolutions.md.
#
# THE FREEZE
#   Nothing under common/, copybooks/, general/, sales/, purchase/, irs/, stock/
#   or mysql/ is touched by this file, not even to reformat a line. Every locator
#   above was verified by reading those files, and reading is all this migration
#   does to them.
