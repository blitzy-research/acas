"""The General Ledger posting cycle - `gl070`, the abort gate, `gl071`, `gl072`.

The migration of `general/general.cbl` `load08.` **L805-L815**, together with the
dispatch paragraph it performs three times, `load00.` **L711-L721**. Those two
paragraphs, verbatim from the frozen source with the `*>` rule lines elided::

    805  load08.
    808      move     "gl070" to ws-called.
    809      perform  load00.
    810      if       ws-term-code = 5
    811               go to display-menu.
    812      move     "gl071" to ws-called.
    813      perform  load00.
    814      move     "gl072" to ws-called.
    815      go       to load00.

    711  load00.
    714      move     zero to ws-term-code.
    715      call     ws-called using ws-calling-data
    716                               system-record
    717                               to-day
    718                               file-defs
    719      end-call
    720      if       ws-term-code > 7
    721               go to overrewrite.
    723  load00-exit.
    725      go       to display-menu.

THE LINKAGE IS THE COMMAND-LINE CONTRACT
========================================
None of the three callees is a main program. Each is a `CALL`ed sub-program with
a fixed parameter list, and all three take the same four-parameter General Ledger
shape [general/gl070.cbl:L245-L248]::

    procedure division using ws-calling-data
                             system-record
                             to-day
                             file-defs.

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
`accept-loop`, its `go to load01 ... depending on z` dispatch table and its
`overrewrite` persistence of the system records are all omitted, and each
omission is recorded in the traceability footer rather than left to be noticed
(Agent Action Plan section 0.4.3). The programs' phase banners belong to
`acas_posting.programs` and are not duplicated here.

Example:
    Run the cycle for the 21st of September 2025, General Ledger only::

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

#: Diagnostics only. Every `display` of the frozen menu that has no database
#: effect becomes a log record (Agent Action Plan section 0.3.4), and a log
#: record must "not alter control flow and must not appear in any table dump".
#: Nothing below branches on a logging call, and nothing below prints.
#: A module-level `getLogger` is not a side effect - it registers a name and
#: performs no input or output. Configuring the root logger IS a side effect, so
#: it happens only inside `main`: importing this module configures nothing, which
#: is what lets a test import it and drive `load08` directly.
_LOG: Final[logging.Logger] = logging.getLogger(__name__)

#  THE THREE PROGRAM-IDS THE MENU MOVES INTO `WS-Called`, named once each.
#  `move "gl070" to ws-called` [general/general.cbl:L808],
#  `move "gl071" to ws-called` [general/general.cbl:L812] and
#  `move "gl072" to ws-called` [general/general.cbl:L814]. They are the literals
#  the frozen source writes, at the width `PIC X(8)` [copybooks/wscall.cob:L7]
#  will hold them - `args.set_called` applies the receiving-field `MOVE`, so a
#  five-character id lands as five characters and three spaces.
_GL070: Final[str] = "gl070"
_GL071: Final[str] = "gl071"
_GL072: Final[str] = "gl072"

#: The format `main` configures the root logger with. Deliberately carries NO
#: timestamp: a wall-clock field in the output would be the one ambient reading
#: in an otherwise clock-free entry point, and rule R-6 is served better by log
#: output that two runs of one scenario can be diffed against each other. The run
#: date reaches this module only through the required `--run-date` option.
_LOG_FORMAT: Final[str] = "%(levelname)s %(name)s: %(message)s"


class _Disposition(enum.Enum):
    """What `load00` observed after a dispatch, and therefore what follows it.

    TWO MEMBERS, because `load00.` has exactly two exits and no others: it either
    reaches its own end and returns to whichever paragraph performed it, or it
    takes `go to overrewrite` at [general/general.cbl:L720-L721] and the run unit
    ends. There is deliberately no member for the abort code 5 - that is NOT a
    `load00.` outcome. `load00.` cannot see it, because its only test is `> 7`
    and 5 is not greater than 7, so the abort is invisible here and is caught one
    level up by `load08.` reading `WS-Term-Code` itself. Adding a third member
    would move the gate into the wrong paragraph and lose exactly the asymmetry
    that makes the General Ledger route differ from the Sales one.

    An enum rather than a bool, so that a call site reads as the COBOL does and
    cannot be misread as "succeeded / failed": `CONTINUE` is silent about whether
    anything went wrong, which is precisely `load00.`'s position after a code of
    5 has been stored.
    """

    #: `load00.` ran to its end and control returned to the performing paragraph.
    #: `WS-Term-Code` may still be non-zero - 5, for instance - and reading it is
    #: the caller's business, exactly as `load08.` L810 reads it.
    CONTINUE = enum.auto()

    #: `if ws-term-code > 7 / go to overrewrite.`
    #: [general/general.cbl:L720-L721]. Control never comes back in the frozen
    #: program: `overrewrite.` falls through `overclose.`
    #: [general/general.cbl:L693] to `goback` [general/general.cbl:L694] and the
    #: run unit ends. A caller that receives this must not dispatch again.
    SERIOUS_ERROR = enum.auto()


class _GlProgram(Protocol):
    """The shape every migrated General Ledger program module presents.

    Structural, not nominal: `gl070_transaction_pre_process`,
    `gl071_batch_sort` and `gl072_transaction_update` are MODULES, and each
    publishes `__all__ = ("run",)` with every paragraph function private. So a
    dispatch reaches a program through exactly one door, which is what
    Agent Action Plan section 0.3.3 requires - "Callers cannot reach into a
    program's internals, exactly as a COBOL `CALL` cannot."

    The four linkage parameters are declared POSITIONAL-ONLY here. Their names
    are documentation of the `PROCEDURE DIVISION USING` order and nothing else,
    because `load00` supplies them by splatting `args.GlLinkage`, exactly as
    `call ws-called using ...` supplies them by position
    [general/general.cbl:L715-L718].

    They are typed `object` rather than by their record classes on purpose: the
    per-directory import table of Agent Action Plan section 0.4.3 lets a `cli`
    module import `programs`, `clock` and `cli.args`, and nothing else - not
    `records`, not `cobol`, not `dal` and not `workfiles`. The linkage carrier
    that `cli.args` publishes is already precisely typed, so the types are
    checked where they are constructed and this protocol only has to name the
    arity and the order.
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

    Not a linkage parameter and not a table. It stands in for what the compiled
    programs use instead - their own FILE SECTIONs over two transient work files
    that persist on the filesystem between phases, `pre-trans.tmp` and
    `post-trans.tmp`, both named in the shared names copybook and both annotated
    by the maintainer as belonging to `gl071` [copybooks/wsnames.cob:L15-L16].
    Nothing about them reaches the database, so nothing about them appears in a
    table dump.

    WHY A HOLDER RATHER THAN A LOCAL. The container has to outlive one dispatch
    and reach the next two, because that is how the phases communicate: `gl070`
    appends the exploded double-entry legs to `pre_trans`, `gl071` sorts those
    into `post_trans` [general/gl071.cbl:L172-L178], and `gl072` posts from
    `post_trans` [general/gl072.cbl:L286]. All three program modules therefore
    accept the same keyword-only `work_files`, and their own docstrings state the
    contract in the same words - "the General Ledger cycle passes ONE container
    through all three phases". Threading it through a holder keeps `load00`
    returning the disposition enum that `load08.` reads, while still letting the
    container the FIRST dispatch creates reach the other two.

    WHY NOT A MODULE-LEVEL DEFAULT. `acas_posting/workfiles.py` deliberately
    builds a fresh set on every request and caches nothing, so that one run's
    records cannot leak into the next; a shared container would break rule R-6's
    byte-identical-reruns guarantee silently. This holder is created per call to
    `load08`, which preserves that property.

    WHO CREATES THE CONTAINER. Not this class. `gl070.run` creates one when it is
    passed None and RETURNS it, so the first dispatch of the cycle both produces
    the container and populates it; `load00` captures the returned value here and
    the remaining two dispatches receive it. That is why this holder starts empty
    and why the type is `object`: the concrete class lives in
    `acas_posting/workfiles.py`, which a `cli` module may not import (Agent
    Action Plan section 0.4.3), and it never needs to - the container is only
    ever carried, never inspected.

    Attributes:
        container: the cycle's work files once a dispatch has produced them, and
            None before that. Passed to every dispatch as-is: a None means "you
            declare them", which is exactly what each program module's own
            `work_files=None` default means.
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
    work_files: _CycleWorkFiles | None = None,
) -> _Disposition:
    """`load00.` [general/general.cbl:L711-L721] - dispatch one program.

    The shared dispatch paragraph of the General Ledger menu, and the reason all
    five General Ledger programs take the identical four-parameter shape. Four
    statements, reproduced in the order the frozen source writes them::

        714      move     zero to ws-term-code.
        715      call     ws-called using ws-calling-data
        716                               system-record
        717                               to-day
        718                               file-defs
        719      end-call
        720      if       ws-term-code > 7
        721               go to overrewrite.

    THE PARAGRAPH ENDS AT L721, AND THAT IS WHY THE ABORT GATE IS REACHABLE.
    `load00-exit.` [general/general.cbl:L723] is a SEPARATE paragraph, so its
    `go to display-menu` [general/general.cbl:L725] is NOT part of the range that
    `perform load00` executes: a `perform` returns after L721 to the paragraph
    that issued it, while `go to load00` falls through into `load00-exit.` and
    ends the dispatch at the menu. `load08.` performs it twice and transfers to it
    once for exactly that reason - had L725 been inside this paragraph, control
    would never reach L810 and the abort gate would be unreachable.

    THE RESET IS FIRST, AND IT IS PER DISPATCH (rule R-4).
    `move zero to ws-term-code` [general/general.cbl:L714] runs before EVERY
    `CALL`, not once per run. `WS-Term-Code` is shared linkage storage, so a code
    a previous phase left behind would still be there for the next test of it -
    and in this cycle that test decides whether the remaining phases run at all
    [general/general.cbl:L810-L811]. Clearing it per dispatch is what makes each
    phase's verdict its own.

    THE THRESHOLD IS `> 7`, NOT `>= 5`. REPRODUCED (rule R-4), and the two
    statements above INTERACT - this is the fifth thing this module reproduces and
    the least obvious. Because L714 has just cleared the field, the only value
    L720 can see is the one the callee just stored, and
    [general/general.cbl:L720-L721] is `> 7`. Five - the General Ledger abort code
    [general/gl070.cbl:L289] - does NOT satisfy it, so an abort leaves this
    paragraph by the ORDINARY exit and is caught one level up by the paragraph
    gate, whose disposition is RETURN TO THE MENU and not program exit. That
    asymmetry is
    the whole reason the General Ledger stop is *return to the menu* while the
    Sales and Purchase stops are *end the program*: their own dispatch paragraphs
    add a `goback` to the `> 7` branch [sales/sales.cbl:L710-L712],
    [purchase/purchase.cbl:L703-L704] and their abort code is 8
    [sales/sl055.cbl:L344], [purchase/pl055.cbl:L286], which IS greater than 7.
    Nothing of that reasoning may be imported into this route.

    Args:
        linkage: the four `CALL` arguments in COBOL parameter order
            [general/gl070.cbl:L245-L248]. The carrier is immutable; the
            `WS-Calling-Data` record inside it is NOT, because COBOL passes a
            group item by reference and `gl070` writes `WS-Term-Code` back into
            the caller's own storage [general/gl070.cbl:L289].
        program: the callee, as a module publishing `run`. Corresponds to
            `call ws-called` [general/general.cbl:L715] - a dynamic call by name
            in the frozen program, resolved here by the caller choosing the
            module, because rule R-1 leaves no COBOL runtime to resolve a name
            against.
        program_id: the literal the menu moves into `WS-Called` immediately
            before transferring here - `"gl070"`, `"gl071"` or `"gl072"`
            [general/general.cbl:L808], [general/general.cbl:L812],
            [general/general.cbl:L814]. Written into the record for
            traceability and for any callee that reads it.
        work_files: the cycle's shared work-file holder. Keyword-only and NOT a
            linkage parameter - see `_CycleWorkFiles`. Omitting it dispatches the
            program against work files of its own, which is what a single
            standalone dispatch wants and what every program module's own
            `work_files=None` default already means.

    Returns:
        `_Disposition.SERIOUS_ERROR` when the callee reported `> 7` and the frozen
        paragraph would have transferred to `overrewrite.`, otherwise
        `_Disposition.CONTINUE`. A code of 5 returns `CONTINUE`, deliberately:
        see THE THRESHOLD above.

    Raises:
        Exception: whatever the callee raises is propagated unchanged. Nothing is
            caught here. The frozen paragraph has no error handler either - it
            reports through `WS-Term-Code` and nothing else - so swallowing an
            exception would invent a disposition the COBOL has not got, and
            losing the traceback would cost a maintainer the only diagnostic a
            genuine defect leaves behind.
    """
    carrier = _CycleWorkFiles() if work_files is None else work_files

    # 714  move     zero to ws-term-code.
    #      REPRODUCED (rule R-4). First, and once per dispatch - see the docstring
    #      on why the placement is load-bearing rather than tidy.
    args.reset_term_code(linkage.calling_data)

    #      `move "<prog>" to ws-called.` - the statement each caller of this
    #      paragraph executes immediately before transferring here
    #      [general/general.cbl:L808], [general/general.cbl:L812],
    #      [general/general.cbl:L814]. Placed inside the dispatch so that the
    #      field and the callee cannot disagree, which in the frozen program they
    #      cannot either: there the field IS the call target.
    args.set_called(linkage.calling_data, program_id)

    #      Diagnostic only, and at INFO. The frozen menu displays nothing at this
    #      point; the phase banners belong to the programs themselves
    #      [general/gl070.cbl:L284], [general/gl070.cbl:L292],
    #      [general/gl071.cbl:L170], [general/gl072.cbl:L274] and are not
    #      duplicated here. No control flow depends on this record.
    _LOG.info("dispatching %s (general/general.cbl:L715-L718)", program_id)

    # 715  call     ws-called using ws-calling-data
    # 716                           system-record
    # 717                           to-day
    # 718                           file-defs
    # 719  end-call
    #      FOUR POSITIONAL ARGUMENTS, IN THE COBOL ORDER. `args.GlLinkage` holds
    #      them in that order, so the splat below and L715-L718 above are the same
    #      list and can be diffed line for line.
    returned = program.run(*linkage, work_files=carrier.container)

    #      The one conditional that is a Python-language necessity rather than a
    #      test of any value the COBOL tests. `gl070.run` returns the work-file
    #      container - the migration's equivalent of naming the same file in the
    #      next program's `SELECT` - while `gl071.run` and `gl072.run` return None
    #      because they have nothing new to hand on. Capturing the first is what
    #      lets `post-trans` reach `gl072` in the order `gl071` left it, which
    #      [general/gl072.cbl:L407-L408] depends on absolutely.
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
    #        Python: return `SERIOUS_ERROR`; `load08` returns at once and `main`
    #               returns `args.exit_status_for(ws_term_code)`, so the process
    #               ends carrying the reported code.
    #        PROOF: in both implementations control never returns to the dispatch
    #               paragraph and no further program is invoked, so the set of
    #               programs run and the database effect are identical. The ONLY
    #               difference is the omitted persistence of the three system
    #               records, recorded as OMISSION 2 in the traceability footer.
    #      REPRODUCED (rule R-4): the predicate is the threshold `> 7` the frozen
    #      source writes, evaluated through `args.is_serious_error`, so this route
    #      and the six others share one implementation of it.
    if args.is_serious_error(linkage.calling_data.ws_term_code):
        _LOG.error(
            "%s reported a serious error, term code %d "
            "(general/general.cbl:L720-L721)",
            program_id,
            linkage.calling_data.ws_term_code,
        )
        return _Disposition.SERIOUS_ERROR

    # 722  *>
    #      Falling off the end of the paragraph is the ordinary exit: `perform
    #      load00` returns to the performing paragraph here, WITHOUT executing
    #      `load00-exit.` [general/general.cbl:L723-L725]. See the docstring.
    return _Disposition.CONTINUE


def load08(linkage: args.GlLinkage) -> None:
    """`load08.` [general/general.cbl:L805-L815] - run the posting cycle.

    Three phases, one at a time, with the abort gate between the first and the
    second. Rule R-3 names this function's file for exactly this: it "runs the
    three phases **one at a time** with the abort gate between them, exactly as
    the menu does".

    STRICTLY SEQUENTIAL, AND THE ORDER IS NOT NEGOTIABLE (rule R-3). There is no
    concurrency of any kind here - no threads, no event loop, no child process,
    no pooling - and the order is `gl070`, then `gl071`, then `gl072`, because
    `gl072` reads each nominal account with a SEQUENTIAL read
    [general/gl072.cbl:L407-L408] and is correct only against the stream `gl071`
    ordered. Reordering or overlapping them produces silent misposting: no error,
    no diagnostic, wrong balances.

    ONE WORK-FILE CONTAINER, CREATED HERE AND SHARED BY ALL THREE. The three
    phases communicate through `pre-trans` and `post-trans`
    [copybooks/wsnames.cob:L15-L16], never through a table. A fresh holder per
    call keeps two runs of one scenario independent, which rule R-6 requires.

    Args:
        linkage: the four `CALL` arguments in COBOL parameter order
            [general/gl070.cbl:L245-L248], as `main` bound them. `WS-Called` is
            overwritten per dispatch and `WS-Term-Code` is cleared per dispatch,
            exactly as the menu does, so the value the caller arrives with in
            either field is not read.

    Returns:
        None. The cycle reports through `WS-Term-Code` inside
        `linkage.calling_data` and through nothing else, exactly as the frozen
        menu does - which is why `main` reads that field afterwards rather than a
        return value. After the gate has fired the field holds
        `args.GL_ABORT_TERM_CODE`; after a clean cycle it holds the zero the last
        dispatch reset it to.

    Raises:
        Exception: propagated unchanged from a phase. See `load00`.
    """
    #      The cycle's own work files. `gl070` declares the container on the first
    #      dispatch and `load00` captures it here - see `_CycleWorkFiles`.
    work_files = _CycleWorkFiles()

    # 808  move     "gl070" to ws-called.
    # 809  perform  load00.
    #      PHASE 1 (batch check) and PHASE 2 (transaction pre-process). `perform`,
    #      not `go to`: control comes back to L810 below, which is what makes the
    #      gate reachable at all.
    disposition = load00(
        linkage, gl070_transaction_pre_process, _GL070, work_files=work_files
    )

    #      Not a statement of `load08.`, but the disposition of L720-L721 inside
    #      the paragraph just performed. GO TO class 4 (sibling re-dispatch), and
    #      the proof is at the `> 7` site in `load00`: the frozen program has
    #      already left for `overrewrite.` and `goback` by this point, so nothing
    #      after it runs. Tested BEFORE the `= 5` gate because that is where the
    #      transfer happens in the frozen source - inside the performed paragraph,
    #      before control could ever reach L810. The two are mutually exclusive
    #      anyway: 5 is not greater than 7.
    if disposition is _Disposition.SERIOUS_ERROR:
        return

    # 810  if       ws-term-code = 5
    # 811           go to display-menu.
    #      ⭐ THE HARD GATE. REPRODUCED (rule R-4), and reproduced as an EQUALITY
    #      test because that is what the frozen source writes - not `>= 5`, not
    #      `> 4`, not `not = zero`. The Sales route tests a different predicate,
    #      `if ws-term-code not = zero` [sales/sales.cbl:L761-L762] and again at
    #      [sales/sales.cbl:L765-L766], and the Purchase route has NO
    #      paragraph-level gate at all - its lines are commented out in the frozen
    #      source [purchase/purchase.cbl:L755-L758]. The three forms must stay
    #      different; harmonising them would be a behaviour change and therefore,
    #      under rule R-4, a failure.
    #
    #      GO TO class 4 (sibling re-dispatch). PER-SITE PROOF OF EQUIVALENCE:
    #        COBOL: `go to display-menu` reaches `display-menu.`
    #               [general/general.cbl:L509], which redraws the menu and waits
    #               for the next selection. `gl071` and `gl072` are never reached.
    #        Python: this function returns immediately; neither `gl071_batch_sort`
    #               nor `gl072_transaction_update` is invoked.
    #        PROOF: the set of programs invoked is identical - `gl070` alone - and
    #               so is the database effect, which is the ABSENCE of everything
    #               phases 4 and 5 would have written. The omitted part is only
    #               the menu redraw, which has no database effect and is dropped
    #               under Agent Action Plan section 0.3.4; OMISSION 1 in the
    #               traceability footer records it.
    if linkage.calling_data.ws_term_code == args.GL_ABORT_TERM_CODE:
        #  A log record, not a warning in the sense the gate is not: the transfer
        #  above is unconditional once the code is 5. This line reports; the
        #  `return` decides.
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
    #      ⛔ NO GATE FOLLOWS THIS DISPATCH. REPRODUCED (rule R-4): the frozen
    #      source runs straight from L813 into L814 with no test of any kind
    #      [general/general.cbl:L813-L814], and `gl071` never writes
    #      `WS-Term-Code` at all - the string does not occur in
    #      general/gl071.cbl. Adding a gate here "for symmetry" with L810 would
    #      invent a stop the COBOL has not got.
    load00(linkage, gl071_batch_sort, _GL071, work_files=work_files)

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
    load00(linkage, gl072_transaction_update, _GL072, work_files=work_files)


def _build_parser() -> argparse.ArgumentParser:
    """Build this route's parser by composing the two published fragments.

    COMPOSED, NEVER REDEFINED. Both option groups come from
    `acas_posting.cli.args`, which owns the binding of `01 WS-Calling-Data`
    [copybooks/wscall.cob:L6-L14], of the run date and of the system record. No
    option is declared here, and in particular this route adds no option of its
    own: an option the COBOL menu does not offer would be an input the frozen
    system has not got.

    Two options the fragments deliberately do NOT offer, because their absence is
    part of the specification: `--ws-called`, since `WS-Called` is set per
    dispatch by `load00` [general/general.cbl:L808]; and `--ws-term-code`, since
    `WS-Term-Code` is an OUTPUT that every dispatch clears first
    [general/general.cbl:L714].

    Returns:
        A parser requiring `--run-date` and accepting the five calling-data
        options plus the two pinnable system-record fields.
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
    #  `move "general" to ws-caller.` [general/general.cbl:L512] - this route's
    #  dispatching menu is the General Ledger one, so that is the default identity.
    args.add_calling_data_arguments(parser, default_caller=args.WS_CALLER_GENERAL)
    #  The REQUIRED `--run-date`, plus the two pinnable `SYSTEM-REC` fields.
    args.add_gl_linkage_arguments(parser)
    return parser


def _binding_exit_status(error: ValueError) -> int:
    """Return the exit status for a linkage-binding failure.

    `args.bind_gl_linkage` resolves the six connection parameters through
    `acas_posting.cli.rdbms_params`, whose `RdbmsParamError` subclasses
    `ValueError` and carries the frozen return code of the parameter loader the
    whole loader family calls - 8 when the contract is absent entirely and 1 when
    it is present but unusable [common/acas-get-params.cbl:L37-L42]. Surfacing
    that code is what lets a caller tell "not configured" from "misconfigured"
    without parsing a message.

    The attribute is read reflectively rather than by importing the exception
    class, because the per-directory import table of Agent Action Plan section
    0.4.3 allows a `cli` entry point `cli.args`, `clock` and `programs`, and
    `rdbms_params` is reached only through `args`, which does not re-export the
    class. Reading the attribute costs nothing and invents nothing; the fallback
    below covers a `ValueError` from anywhere else in the binding.

    Args:
        error: the failure raised while binding the linkage.

    Returns:
        The error's own frozen return code when it carries one, otherwise the
        smallest status the frozen menu would treat as a serious error - derived
        from `args.SERIOUS_ERROR_THRESHOLD` rather than typed, so that the two can
        never disagree [general/general.cbl:L720].
    """
    return_code = getattr(error, "return_code", None)
    if isinstance(return_code, int):
        return return_code
    return args.SERIOUS_ERROR_THRESHOLD + 1


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
    call chain reads a clock exactly once, in the menu shell's date service
    [copybooks/Proc-ACAS-Mapser-RDB.cob:L72-L80], and all three programs
    dispatched below contain zero clock reads, so pinning here is sufficient to
    make two runs of one scenario byte-identical (Agent Action Plan section 0.8.5).

    Args:
        argv: the argument vector, WITHOUT the program name. None reads
            `sys.argv[1:]`, which is what argparse does by default and what a
            real invocation wants; a test passes a list.

    Returns:
        `WS-Term-Code` as the process exit status, through
        `args.exit_status_for`, which is the identity - so a caller reads the code
        the cycle produced rather than a re-encoding of it. Zero when all three
        phases ran; `args.GL_ABORT_TERM_CODE` when the abort gate fired; the
        reported code when a phase failed seriously; and the parameter loader's own
        return code when the linkage could not be bound at all.

    Raises:
        SystemExit: raised by argparse for `--help` and for a usage error, such as
            the required `--run-date` being absent. Deliberately not caught: an
            omitted run date must fail, because the only alternative is an ambient
            one.
        Exception: propagated unchanged from a phase. A failure inside the cycle
            keeps its traceback, which is the only diagnostic a genuine defect
            leaves behind; nothing here converts one into a status.
    """
    #  The one side effect this module performs, and it performs it HERE and
    #  nowhere else: `basicConfig` at import time would configure logging for
    #  every importer, including the test suites that import this module to drive
    #  `load08` directly. It is also a no-op when the root logger already has a
    #  handler, so a caller that configured logging itself keeps its own setup.
    logging.basicConfig(level=logging.INFO, format=_LOG_FORMAT)

    parser = _build_parser()
    namespace = parser.parse_args(argv)

    #  `move "gl070" to ws-called.` [general/general.cbl:L808] - the first
    #  dispatch of the cycle, so the record is bound with the first callee's
    #  program-id. `load00` sets the field again before each of the three
    #  dispatches, exactly as L808, L812 and L814 do.
    try:
        linkage = args.bind_gl_linkage(namespace, called=_GL070)
    except ValueError as error:
        #  The deployment contract for the connection parameters is absent or
        #  unusable. Reported rather than raised because it is a configuration
        #  failure at the process boundary, not a defect in the cycle - and
        #  nothing has been touched yet: the failure is raised while the linkage is
        #  still being bound, before any database is contacted, any file opened or
        #  any program entered. The message never carries a parameter value, so
        #  logging it cannot leak a credential.
        _LOG.error("cannot bind the General Ledger linkage: %s", error)
        return _binding_exit_status(error)

    #  805  load08.
    load08(linkage)

    #  AMBIGUITY Q-CLI-EXITSTATUS: the COBOL disposition for term code 5 is
    #  "return to display-menu", which has no process-status analogue in a
    #  single-operation CLI - resolve against the compiled oracle; record in
    #  docs/migration/ambiguity-resolutions.md. Locators:
    #  [general/general.cbl:L810-L811], [general/general.cbl:L720-L721].
    #  STATE OF THE QUESTION. `args.exit_status_for` records it as settled, and
    #  settled by proving there is no oracle observable to arbitrate against: a
    #  census of the five menus and all twelve in-scope programs finds
    #  `RETURN-CODE` read and never written, every occurrence being the shell-out
    #  test `if Return-Code not = zero` [general/general.cbl:L496], and the
    #  transfers that do end a run end it with a bare `goback` carrying nothing
    #  [general/general.cbl:L694]. The compiled cycle therefore emits no exit
    #  status derived from `WS-Term-Code` in any band. The identity is adopted
    #  because it is total and lossless over `pic 99`
    #  [copybooks/wscall.cob:L10] and because banding would discard the
    #  distinction between the abort code 5 and a serious error above 7 - making
    #  the migrated cycle report LESS than the original. This entry point does not
    #  re-encode the value; it is the code itself.
    return args.exit_status_for(linkage.calling_data.ws_term_code)


if __name__ == "__main__":
    #  `pyproject.toml` declares no `[project.scripts]`, so `python -m
    #  acas_posting` is the packaged route - but the oracle comparison scripts
    #  drive these entry points as modules,
    #  `python -m acas_posting.cli.gl_post_cycle`, so direct execution has to
    #  work. `raise SystemExit(main())` rather than `sys.exit(main())`, which
    #  keeps `sys` off the import list. Rule R-1 runs the other way round: those
    #  scripts are a sibling of the shipped package and drive it from OUTSIDE,
    #  and nothing here reaches back towards them.
    raise SystemExit(main())


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
#   _binding_exit_status->  no menu counterpart. The codes it surfaces ARE frozen:
#                           [common/acas-get-params.cbl:L37-L42].
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
#     L720-L721  `go to overrewrite`     ->  return _Disposition.SERIOUS_ERROR
#                proof at the `> 7` site in `load00`.
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
#   2. NO GATE AFTER `gl071` [general/general.cbl:L813-L814]. L813 runs straight
#      into L814 with no test of any kind. None is added "for symmetry".
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
#   2. `overrewrite.` [general/general.cbl:L656] and its persistence of three
#      records - `System-Record` at File-Key-No 1, `Default-Record` at 2 and
#      `WS-System-Record-4` at 4 - to both the RDB and the Cobol file, falling
#      through `overclose.` [general/general.cbl:L693] to `goback`
#      [general/general.cbl:L694]. Not reproduced: it is the menu's own
#      housekeeping around a dispatch, not part of the posting cycle, and the
#      menu is out of scope as a program. Also omitted, and additionally
#      excluded by rule R-1 and by Agent Action Plan section 0.2.2's spool-out
#      exclusion: `pre-overrewrite.` [general/general.cbl:L634] and its backup
#      `call "SYSTEM" using Full-Backup-Script` [general/general.cbl:L650].
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
