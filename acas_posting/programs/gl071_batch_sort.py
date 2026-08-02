"""`gl071` - the General Ledger Batch Transaction Sort  [general/gl071.cbl].

The migration of `general/gl071.cbl` in its entirety. Boundary: THE WHOLE
PROGRAM - unlike `gl051` and `irs030`, nothing here is out of scope, because
there is nothing here but a sort.

    THE ENTIRE PROCEDURE DIVISION, VERBATIM  [general/gl071.cbl:L167-L181]

    167  main.
    170      display  "Sorting.......Please wait            " at 0801
             with foreground-color 2.
    172      sort     sort-trans
    173               on ascending key sort-batch
    174                                sort-ac
    175                                sort-pc
    176                                sort-post
    177               using  pre-trans
    178               giving post-trans.
    180  main-exit.
    181      goback.

Two paragraphs, one screen message, one statement, one `goback`. That is the
whole program, and its minimalism is itself specification: a census over the
comment-stripped source finds ZERO `MOVE`, ZERO `GO TO`, ZERO `IF`, ZERO
`ACCEPT`, ZERO `PERFORM`, ZERO `CALL`, ZERO `OPEN`/`READ`/`WRITE`/`CLOSE`, ZERO
arithmetic statements of any kind and ZERO `ROUNDED`. It is the only one of the
twelve in-scope programs that scores zero on every one of those, the only one
that touches NO database table, and the only one with no date sections. Every
absence below is therefore a REPRODUCTION, not an omission of convenience.

A CONTRACT, NOT A COMPUTATION
=============================
Twelve lines of body, one obligation: emit `post-trans` in
`(batch, account, profit-centre, posting)` ascending order, STABLY. And yet
Agent Action Plan section 0.6.4 ranks that ordering as the single strongest
ordering dependency in the whole migration, verbatim:

    "`gl072` locates the nominal-ledger account for each posting with a
    sequential read-next rather than an indexed read. It finds the correct
    account only because `gl071` has already emitted the stream in nominal-key
    order. Any change in sort stability or key composition produces silent
    misposting - no error, no diagnostic, wrong balances."

There is no defensive check anywhere downstream. Get the key tuple wrong, or
lose stability, and the cycle posts real money to the wrong nominal accounts and
reports success - and the failure surfaces later as what looks like an
arithmetic defect in `gl072`.

THE PRODUCER / CONSUMER CHAIN
=============================
    `gl070` phase 2 writes `pre-trans`      [general/gl070.cbl:L495-L533]
    `gl071` sorts it into `post-trans`      [general/gl071.cbl:L172-L178]
    `gl072` phase 4 reads `post-trans` and locates each nominal account by a
            SEQUENTIAL read                 [general/gl072.cbl:L407-L408]

This module is the middle link, and the third link has no error handling at all.
`gl070`'s three-leg double-entry explosion writes a debit leg
[general/gl070.cbl:L508], a credit leg negated by `multiply pre-amount by -1`
[general/gl070.cbl:L517] and written at [general/gl070.cbl:L519], and a VAT leg
[general/gl070.cbl:L532] emitted only when both the VAT account and the VAT
amount are non-zero [general/gl070.cbl:L521-L523]. The batch and posting numbers
are moved ONCE, before the legs [general/gl070.cbl:L495-L496]; only the account
and profit centre change from leg to leg. So two legs of ONE posting that land
on the same account and profit centre carry an IDENTICAL four-key tuple, and
their relative order is decided by the tie behaviour alone - which is why
stability here is concrete rather than theoretical, and why it is guaranteed
structurally rather than assumed. See question Q-7 below for exactly where that
guarantee is enforced and why it cannot be switched off.

WHY A DEFECT ELSEWHERE IS SURVIVABLE  (rule R-4)
================================================
This program reproduces NO entry from the migration's twenty-two-entry anomaly
register: it has no defect of its own. What it does carry is the ordering
contract that ANOMALY A-14 depends on for its correctness - `gl072` moves the
composite ledger key into `WS-Ledger-Key` [general/gl072.cbl:L405] and then
performs a READ NEXT anyway [general/gl072.cbl:L407-L408], so the key move
positions nothing and selects nothing. A-14 is harmless ONLY because this
program sorted first.

That relationship is stated here because a maintainer reading `gl072` in
isolation would see an obvious bug and "fix" it. Agent Action Plan section 0.8.4
forbids the change outright - the obvious speed-up, an indexed read, is
precisely the forbidden one - and section 0.8.2 is unambiguous about why:
"A defect reproduced is correct; a defect fixed is a failure."

THE ABORT CHAIN MEANS THIS PROGRAM MAY NEVER RUN AT ALL
=======================================================
The General Ledger menu dispatches the posting cycle from one paragraph
[general/general.cbl:L805-L815]:

    load08.
        move     "gl070" to ws-called.
        perform  load00.
        if       ws-term-code = 5
                 go to display-menu.
        move     "gl071" to ws-called.
        perform  load00.
        move     "gl072" to ws-called.
        go       to load00.

`gl070` raises `ws-term-code = 5` on finding a batch left open - its phase-1
batch check sets the flag `a` when a batch reports `status-open`
[general/gl070.cbl:L314-L315], and phase 1's own epilogue then acts on it,
`if a = 1 / perform gl060a / move 5 to ws-term-code / go to main-exit.`
[general/gl070.cbl:L287-L290] - and the menu at L810-L811 then returns to
itself, so `gl071` AND `gl072` are skipped entirely. An empty or
absent `post-trans` after an aborted run is CORRECT BEHAVIOUR, not a failure,
and so is an empty `post-trans` from an empty `pre-trans`: sorting nothing
produces nothing, silently, which is exactly the `test_empty_batch` scenario.
Nothing below checks for either case.

`load00.` itself zeroes `ws-term-code` before the `CALL`
[general/general.cbl:L714] and tests it after [general/general.cbl:L720-L721].
`gl071` contains zero `MOVE` and zero `SET` statements, so it cannot write to
its linkage block: the term code a caller reads back is the zero the caller set.
See question Q-15 in the AMBIGUITIES section below.

NO PHASE NUMBER OF ITS OWN
==========================
The programs label their own phases on screen - "Phase - 1. Batch Check"
[general/gl070.cbl:L284], "Phase - 2. Transaction Pre-process"
[general/gl070.cbl:L292], "Phase - 4. Transaction Update"
[general/gl072.cbl:L274], and both "Phase - 3. Transaction Deletion"
[general/gl080.cbl:L319] and "Phase - 5. End of Period Processing"
[general/gl080.cbl:L336]. `gl071` displays NO phase label; it sits unlabelled
between phase 2 and phase 4. And the numbering is not sequential with execution
- deletion is labelled phase 3 but runs after phase 4 - which is recorded here
so that a maintainer is not misled by it.

WORK FILES ARE SEQUENCES  (Agent Action Plan sections 0.3.1, 0.3.3)
==================================================================
The three files this program declares are `pre-trans`
[general/gl071.cbl:L92-L95], `post-trans` [general/gl071.cbl:L97-L100] and the
sort work description `sort-trans` [general/gl071.cbl:L102]. The first two are
the transient scratch files the maintainer annotates as belonging to `gl071`
[copybooks/wsnames.cob:L15-L16] - "not part of the schema" - and the plan models
all three as ORDERED IN-PROCESS SEQUENCES in `acas_posting.workfiles`. Nothing
about them reaches the database, so nothing about them appears in a table dump,
and this module touches no table at all.

Because the sequences are in-process, the container that holds them stands in
for what the compiled program uses instead: the FILESYSTEM. `gl070` writes
`pretrans.tmp` and closes it; `gl071` opens it, reads it, writes `postrans.tmp`
and closes that; `gl072` opens `postrans.tmp`. In one Python process that
persistence is an object, and `acas_posting.workfiles.GeneralLedgerWorkFiles`
is deliberately NOT a module-level singleton - one run's records would leak into
the next and rule R-6's byte-identical-reruns guarantee would fail silently. So
the container is handed in; see `run` for exactly how, and why that does not
disturb the four-parameter linkage shape.

RULES THIS MODULE IS HELD TO
============================
R-1, no COBOL at runtime. Nothing here starts a process, loads a foreign
library, or reaches the compiled-oracle tree under `harness/`. The `SORT` verb
is reimplemented natively: `acas_posting.workfiles.sort_using_giving` performs
the statement's implicit opens, reads, writes and closes, and delegates the
ordering itself to `acas_posting.cobol.sortverb.sort_records`.

R-2, zero binary floating point. No `float`, no `complex`, no `round`, and
nothing numeric is computed here at all - `gl071` has no arithmetic to have.
`sort-amount pic s9(8)v99` [general/gl071.cbl:L143] is DISPLAY zoned and signed,
carried as a scale-2 `decimal.Decimal` and never coerced, re-quantized or
compared; `gl070` writes negative values into it [general/gl070.cbl:L517], so
signed values are routine in the stream. And per Agent Action Plan section
0.3.1 - "`cobol/` contains no business logic and `programs/` contains no numeric
primitives" - there is no comparator here: no `sorted`, no `list.sort`, no
`key=lambda`, no `cmp_to_key`, no `attrgetter`. This module NAMES the keys and
the direction; the comparison and the stability are COBOL language semantics and
live one layer down, so a parity failure localises to one layer or the other.

R-3, nothing added. `gl071` contains zero conditional statements, so this module
adds none: no empty-input check, no input-versus-output count check, no key-range
check, no duplicate detection, no status inspection. The single `if` expression
below resolves a default that Python cannot express in a signature, and is
labelled as such. No DDL, no ORM, no schema access. No `threading`, `asyncio`,
`multiprocessing` or `concurrent.futures`: a sort is the classic place to reach
for a faster algorithm or a parallel merge, and section 0.8.4 puts performance
work "out of scope by construction, not merely unrequested".

R-4, anomalies reproduced. Nothing to reproduce here, and the A-14 relationship
above is why that is worth stating rather than omitting.

R-5, full traceability. A named function per paragraph, and a footer mapping
every construct - and every deliberate omission - to its frozen locator.

R-6, compiled behaviour is the tie-breaker. No clock is read: `gl071` contains
zero clock reads and does not even use its `to-day` parameter, and clock
injection belongs to the CLI boundary. This module is nonetheless WHERE
DETERMINISM IS WON OR LOST for the whole General Ledger cycle - an unstable sort
is a nondeterminism source indistinguishable, from the outside, from a clock
read, and section 0.6.6 records that the schema contributes "no ordering
nondeterminism from a secondary index", which leaves this sort as the cycle's
only ordering decision.

WHAT THIS MODULE MAY IMPORT, AND WHY THE LIST IS THIS SHORT
===========================================================
`gl071`'s ENTIRE `COPY` list is four lines - `envdiv.cob`
[general/gl071.cbl:L85], `wscall.cob` [general/gl071.cbl:L155], `wssystem.cob`
[general/gl071.cbl:L156] and `wsnames.cob` [general/gl071.cbl:L157] - against a
measured eleven in `gl070`, thirteen in `gl072`, twelve in `gl080` and fifteen
in `gl051`. It copies NEITHER facade copybook and it does not copy
`wsfnctn.cob`. So, uniquely among the twelve program modules, this
one MUST NOT import anything from `acas_posting.dal` - not `dal.facade`, not
`dal.status`, not a handler. Adding a facade import "for consistency" would
invent a dependency the specification does not have. Nor `cobol.arithmetic` (no
arithmetic), `cobol.move` (no `MOVE`), `cobol.condition_names` (no `88`-level is
tested), `acas_posting.dates` (no `zz050`, no `zz060`, no `zz070`, no
date-module wrapper) or `acas_posting.clock`. Nor `cli`, nor a sibling
`programs` module, nor `dictionary.generate`, nor `harness`.

What remains is the three record modules the three linkage `COPY` statements
translate to, and `acas_posting.workfiles`. The dependency direction is
`programs -> workfiles -> cobol.sortverb`, never the reverse.

AMBIGUITIES, ARBITRATED AGAINST COMPILED BEHAVIOUR  (rule R-6)
==============================================================
Rule R-6 makes the compiled program's observed behaviour the tie-breaker for an
ambiguous semantic question and requires each resolution to be documented rather
than settled silently. Two bear on this module, and both are answered.

    Q-7   THE ORDER OF RECORDS WHOSE KEYS ALL COMPARE EQUAL. RESOLVED,
          CONFIRMED - GnuCOBOL 3.2's `SORT` IS STABLE. The statement carries no
          `WITH DUPLICATES IN ORDER` phrase [general/gl071.cbl:L172-L178] -
          verified, the string `duplicates` occurs ZERO times in this file - so
          the COBOL standard leaves the relative order of equal-key records
          UNSPECIFIED, and what the standard leaves open the implementation
          nevertheless decides. It was therefore MEASURED rather than assumed:
          the frozen statement was replicated exactly and driven twice, first
          with three records carrying an identical four-key tuple and
          distinguishable payloads, then with 120 records all tied on all four
          keys. The three came out in written order and the 120-record run
          reported zero out-of-input-order breaks. The experiment and its output
          are recorded in full at question Q-7 of
          `acas_posting.cobol.sortverb`, which owns the number and the answer;
          this module inherits both. Stability is NOT requested here as a flag,
          because there is no flag to pass: `sort_using_giving` publishes no
          `stable` parameter, and the sort it delegates to REJECTS any request
          for an unstable ordering outright - `sort_records` raises
          `SortVerbError` unless `stable is True`. The guarantee is therefore
          structural and unbypassable rather than merely defaulted, which is
          stronger than passing `stable=True` would be: there is no argument,
          no environment variable and no subclass hook by which any caller of
          this module can obtain an unstable ordering. What this call site does
          pass explicitly is the KEY LIST - the half of the contract that can
          actually be got wrong. The tie is genuinely reachable, see THE
          PRODUCER / CONSUMER CHAIN above, so the guarantee is asserted
          behaviourally rather than trusted: a tied group must come out in
          written order.
    Q-15  WHAT A CALLER OBSERVES IN THE LINKAGE BLOCK AFTER THIS PROGRAM
          RETURNS. RESOLVED STATICALLY, AND THE ANSWER IS "NOTHING CHANGED".
          The next free number in the migration's shared register. Three of the
          four linkage parameters are ACCEPTED BUT UNREAD - `ws-calling-data` is
          never tested, `system-record` is never tested, and `to-day` is never
          used - and the fourth, `file-defs`, is used only indirectly, supplying
          the two work-file names through the FILE-CONTROL `assign` clauses
          [general/gl071.cbl:L92], [general/gl071.cbl:L97]. The question a
          caller cares about is whether the compiled program nonetheless writes
          anything back, since `WS-Term-Code` is an OUT parameter for every
          other program in the cycle. It cannot: the program contains zero
          `MOVE`, zero `SET`, zero arithmetic and zero `CALL` statements, so
          there is no statement in it capable of storing into the linkage block.
          No oracle run is needed to settle that, and none was invented to
          decorate it. All four parameters are kept in the signature anyway
          rather than silently narrowing it - the menu passes the same
          four-parameter block to `gl070`, `gl071` and `gl072` alike
          [general/general.cbl:L715-L718] - and this module writes to none of
          them.
"""

from __future__ import annotations

from typing import Final

# copy "wscall.cob".   [general/gl071.cbl:L155]
# The linkage block `01 WS-Calling-Data` [copybooks/wscall.cob:L6-L14]. Imported
# for the first parameter's declaration; nothing below reads or writes a field
# of it, which is question Q-15.
from acas_posting.records.calling_data import WsCallingData

# copy "wsnames.cob".  [general/gl071.cbl:L157]
# `01 File-Defs.` [copybooks/wsnames.cob:L13] - the file-name buffers, including
# `pre-trans-name` and `post-trans-name` [copybooks/wsnames.cob:L15-L16] and
# `file-21` [copybooks/file21.cob:L1], the three names this program's
# FILE-CONTROL entries assign [general/gl071.cbl:L92-L102].
from acas_posting.records.file_defs import FileDefs

# copy "wssystem.cob". [general/gl071.cbl:L156]
# `SYSTEM-REC`, the 169-column system record. Imported for the second
# parameter's declaration; never tested here, which is question Q-15.
from acas_posting.records.system_record import SystemRecord

# The work-file layer: the three sequences, and the `SORT` statement itself.
# `sort_using_giving` reproduces [general/gl071.cbl:L172-L178] whole - the
# implicit `USING` opens/reads/close, the ordering, and the implicit `GIVING`
# open/writes/close - and delegates the comparison and the stability to
# `acas_posting.cobol.sortverb.sort_records`, whose stability cannot be switched
# off. `SORT_TRANS_ASCENDING_KEYS` is that statement's own key list; it is
# passed explicitly below rather than left to default, so the four keys are
# named at the call site.
from acas_posting.workfiles import (
    SORT_TRANS_ASCENDING_KEYS,
    GeneralLedgerWorkFiles,
    general_ledger_work_files,
    sort_using_giving,
)

#: The whole public surface: the program's single entry point, mirroring its
#: `PROCEDURE DIVISION USING` list [general/gl071.cbl:L161-L164]. Agent Action
#: Plan section 0.3.3, verbatim: "Each `programs/*.py` module exposes a single
#: `run(...)` entry mirroring its COBOL `PROCEDURE DIVISION USING` list, with
#: the paragraph functions private to the module. Callers cannot reach into a
#: program's internals, exactly as a COBOL `CALL` cannot." So the two paragraph
#: functions below are private, and a tuple is used rather than a list so the
#: surface cannot be extended in place at run time.
__all__: Final[tuple[str, ...]] = ("run",)


#  main.  [general/gl071.cbl:L167]


def _main(work_files: GeneralLedgerWorkFiles) -> None:
    """`main.` - the screen message and the sort  [general/gl071.cbl:L167-L178].

    The paragraph's whole body is two statements, and both are reproduced here.
    A PARAGRAPH, NOT A SECTION: there is no `SECTION` keyword anywhere in this
    program's procedure division - the four in the file are all in the
    environment and data divisions - so there is no `exit section.` to
    reproduce, and control simply falls through into `main-exit.`
    [general/gl071.cbl:L180], which is what `run` does by calling `_main_exit`
    straight after this. Rule R-5 requires a named function for each paragraph
    regardless of how little it holds.

    STATEMENT 1 - THE SCREEN MESSAGE  [general/gl071.cbl:L170]

        display  "Sorting.......Please wait            " at 0801
                 with foreground-color 2.

    A diagnostic with no database effect. Agent Action Plan section 0.3.4 puts
    it in the first of its three classes: such a display "become[s] [a] log
    record[] at a severity matching the original's intent", must not alter
    control flow, and must not appear in any table dump. It is emitted at INFO -
    the original is a progress notice - as
    `acas_posting.workfiles.SORTING_DIAGNOSTIC`, by the first statement of
    `sort_using_giving`, BEFORE that function reads anything, which is the
    position the display occupies here.

    EMITTED ONCE, WHICH IS WHY THERE IS NO `logger.info` IN THIS FUNCTION. One
    COBOL `display` must produce one log record. Logging it here as well would
    produce two records for one statement and would be LESS faithful, not more,
    so the message is owned by the one function that reproduces the statement it
    precedes, and this module deliberately imports no `logging` at all. The
    screen position `at 0801`, the colour, and the literal's trailing padding
    are presentation and are dropped - the padding clears the rest of the screen
    line and carries no meaning.

    STATEMENT 2 - THE SORT  [general/gl071.cbl:L172-L178]
    Delegated whole, because every part of it is language semantics rather than
    an accounting decision: the implicit `USING` open-read-close, the ordering,
    the implicit `GIVING` open-write-close. This program declares no `OPEN`,
    `READ`, `WRITE` or `CLOSE` of either work file - the `SORT ... USING ...
    GIVING` form performs all of that itself - which is also why
    `77 fs-reply pic xx.` [general/gl071.cbl:L150], declared as the FILE STATUS
    of both work files [general/gl071.cbl:L94], [general/gl071.cbl:L99], is
    never inspected anywhere in the program. No status check is invented here
    (rule R-3).

    Args:
        work_files: The three sequences this program's FILE-CONTROL entries
            declare [general/gl071.cbl:L92-L102] - `pre_trans`, `post_trans` and
            `sort_trans`, in the container that stands in for the filesystem the
            compiled program passes them through. Its `pre_trans` is whatever
            `gl070` phase 2 left there, which may legitimately be empty.

    Raises:
        acas_posting.workfiles.WorkFileError: A record description does not have
            the shape the group move between the three field-identical layouts
            [general/gl071.cbl:L112-L144] requires. A PROGRAMMER error; nothing
            in the content of a record can cause it.
    """
    # 172  sort     sort-trans
    # 173           on ascending key sort-batch
    # 174                            sort-ac
    # 175                            sort-pc
    # 176                            sort-post
    # 177           using  pre-trans
    # 178           giving post-trans.
    #
    # THE KEY ORDER IS NOT THE RECORD'S DECLARATION ORDER, and this is the
    # single easiest thing in the module to get wrong. Both orders, side by
    # side:
    #
    #   sort-trans-record, AS DECLARED   [general/gl071.cbl:L136-L144]
    #     1 sort-batch   pic 9(5)      L137   ->  key 1
    #     2 sort-post    pic 9(5)      L138   ->  key 4
    #     3 sort-code    pic xx        L139       not a key
    #     4 sort-date    pic x(8)      L140       not a key
    #     5 sort-ac      pic 9(6)      L141   ->  key 2
    #     6 sort-pc      pic 99        L142   ->  key 3
    #     7 sort-amount  pic s9(8)v99  L143       not a key
    #     8 sort-legend  pic x(32)     L144       not a key
    #
    #   ON ASCENDING KEY, AS WRITTEN     [general/gl071.cbl:L173-L176]
    #     key 1  sort-batch   L173   (record field 1)
    #     key 2  sort-ac      L174   (record field 5)
    #     key 3  sort-pc      L175   (record field 6)
    #     key 4  sort-post    L176   (record field 2)
    #
    # `sort-post` is declared SECOND and sorts FOURTH; `sort-ac` is declared
    # FIFTH and sorts SECOND. A key list in declaration order would still be
    # four ascending keys and would still look like a sort, and it would order
    # the stream differently with no error at all - which is the silent
    # misposting Agent Action Plan section 0.6.4 warns about, because
    # [general/gl072.cbl:L407-L408] then walks it sequentially. Keys 2 and 3
    # together ARE the nominal ledger key the consumer breaks on: `gl072`
    # declares them as one `03 post-ledger.` group [general/gl072.cbl:L115-L117]
    # and moves the composite whole into `WS-Ledger-Key`
    # [general/gl072.cbl:L405].
    #
    # `SORT_TRANS_ASCENDING_KEYS` is that list, in that order, every key
    # ascending - there is no descending key and no mixed direction anywhere in
    # this program. It is passed EXPLICITLY rather than left to default so the
    # key list is named at this call site, and it is not rebuilt locally: one
    # key list in the package means one place to get it wrong instead of two.
    #
    # The four non-key fields - `sort-code`, `sort-date`, `sort-amount` and
    # `sort-legend` - are carried through untouched. `sort-date` is `pic x(8)`,
    # EIGHT characters in `DD/MM/YY` form with a two-digit year, and is NOT a
    # key: nothing here sorts chronologically. `sort-amount` is signed DISPLAY
    # zoned at scale 2 and is NOT a key either.
    #
    # Direction of flow: `USING pre-trans` in, `GIVING post-trans` out
    # [general/gl071.cbl:L177-L178]. Not the reverse.
    sort_using_giving(
        work_files.sort_trans,
        on_ascending_key=SORT_TRANS_ASCENDING_KEYS,
        using=work_files.pre_trans,
        giving=work_files.post_trans,
    )


#  main-exit.  [general/gl071.cbl:L180]


def _main_exit() -> None:
    """`main-exit.` - the `goback`  [general/gl071.cbl:L180-L181].

        180  main-exit.
        181      goback.

    THE PARAGRAPH'S ENTIRE BODY IS `goback.`, so this function's entire body is a
    `return`. That is a faithful one-to-one mapping and NOT a stub: `goback` in a
    called program returns control to its caller, leaving the linkage block
    exactly as it stands, and there is nothing else in the paragraph to
    reproduce. It is present because rule R-5 requires a named function for
    every paragraph, and Agent Action Plan section 0.7.4 C-4 states the reason
    verbatim: "every paragraph retains a named function even where its `GO TO`
    becomes a `continue`, a `break` or a `return`." Here there is no `GO TO` at
    all - this program contains none - and the rule still requires the function.

    Control reaches here by FALLING THROUGH from `main.`
    [general/gl071.cbl:L167], not by a transfer: `main.` ends on the `SORT`
    statement's terminating period [general/gl071.cbl:L178] with no `GO TO` and
    no `exit section.`, so `run` calls this immediately after `_main` to
    reproduce the fall-through explicitly.

    Nothing is written back. `gl071` has zero `MOVE` and zero `SET` statements,
    so it cannot set `WS-Term-Code` the way every other program in the cycle
    can; the value a caller reads back is the zero `load00.` moved in before the
    `CALL` [general/general.cbl:L714]. See question Q-15.
    """
    # 181  goback.
    # Return to the caller - general/general.cbl `load00.`
    # [general/general.cbl:L711-L722] in a real run - with the linkage block
    # untouched.
    return


#  procedure division using ...  [general/gl071.cbl:L161-L164]


def run(
    ws_calling_data: WsCallingData,
    system_record: SystemRecord,
    to_day: str,
    file_defs: FileDefs,
    *,
    work_files: GeneralLedgerWorkFiles | None = None,
) -> None:
    """Run `gl071` - sort the pre-trans stream into nominal-key order.

    The program's single entry point, and the whole of its procedure division:
    `main.` then `main-exit.`, called in source order, exactly as control flows
    through them [general/gl071.cbl:L167-L181].

    THE LINKAGE, VERBATIM  [general/gl071.cbl:L161-L164]

        procedure division using ws-calling-data
                                 system-record
                                 to-day
                                 file-defs.

    The four positional parameters below are that list, in that order, under
    those names - the four-parameter General Ledger call shape, verified
    character-for-character identical in all five programs that take it:
    `gl051` [general/gl051.cbl:L353-L356], `gl070`
    [general/gl070.cbl:L245-L248], `gl072` [general/gl072.cbl:L262-L265] and
    `gl080` [general/gl080.cbl:L269-L272]. Every one of the five is dispatched
    through the SAME menu paragraph, `load00.` [general/general.cbl:L711-L722],
    whose single `CALL` parameter list is [general/general.cbl:L715-L718] - so
    the uniformity is the caller's contract and not a coincidence. `to-day` is
    `01 to-day pic x(10).` [general/gl071.cbl:L159], a DD/MM/CCYY text date and a
    linkage parameter rather than a column.

    THREE OF THE FOUR ARE ACCEPTED BUT UNREAD, and are kept anyway.
    `ws_calling_data` is never tested, `system_record` is never tested, and
    `to_day` is never used - this program has no date section of any kind, no
    `zz050`, no `zz060`, no `zz070` and no date-module wrapper, unlike every
    other in-scope program. `file_defs` is used only indirectly, supplying the
    work-file names its FILE-CONTROL entries assign
    [general/gl071.cbl:L92-L102]. Narrowing the signature to the parameters the
    body happens to read would break the uniformity the caller depends on and
    would hide a fact worth seeing, so all four are declared and the omission of
    any USE of three of them is recorded instead - question Q-15 above, and the
    OMISSIONS list in the traceability footer.

    Args:
        ws_calling_data: `01 WS-Calling-Data` [copybooks/wscall.cob:L6-L14],
            accepted and unread. Not written back either: `WS-Term-Code` keeps
            whatever the caller put there, which `load00.` sets to zero before
            the `CALL` [general/general.cbl:L714].
        system_record: `SYSTEM-REC`, the 169-column system record, accepted and
            unread. `gl071` tests no system flag, no accounting cycle and no
            `Run-Date`.
        to_day: `to-day pic x(10)` in DD/MM/CCYY form, accepted and UNUSED.
            Declared because the linkage declares it; no clock is read here and
            none is read downstream of here.
        file_defs: `01 File-Defs.` [copybooks/wsnames.cob:L13], the file-name
            buffers. Used indirectly: `pre-trans-name` and `post-trans-name`
            [copybooks/wsnames.cob:L15-L16] and `file-21`
            [copybooks/file21.cob:L1] are what this program's three
            FILE-CONTROL entries assign [general/gl071.cbl:L92-L102].
        work_files: The cycle's three work-file sequences. NOT A LINKAGE
            PARAMETER - it is keyword-only, and it stands in for what the
            compiled program uses instead, its own FILE SECTION over files that
            persist on the filesystem between phases. `gl070` must have written
            `pre_trans` into the same container for this sort to have anything
            to order, and `gl072` must read `post_trans` out of it, so the
            General Ledger cycle passes one container through all three phases.
            Omitting it declares a fresh, empty set - three closed, empty
            sequences - and sorting nothing then produces nothing, silently,
            which is the correct outcome both for an empty batch and after the
            `ws-term-code = 5` abort described in the module docstring.

    Raises:
        acas_posting.workfiles.WorkFileError: A record description does not have
            the shape the group move between the three field-identical layouts
            requires. A PROGRAMMER error; see `_main`.
    """
    # THE ONE CONDITIONAL IN THIS MODULE, AND IT IS A PYTHON-LANGUAGE
    # NECESSITY RATHER THAN A VALIDATION. `gl071` contains ZERO conditional
    # statements, so no test of any value reaching this program is added
    # anywhere below (rule R-3). This expression tests no such value: it
    # resolves a default that a signature cannot hold, because a mutable default
    # argument is evaluated once at definition time and would then be SHARED
    # between calls - one run's records leaking into the next, which is exactly
    # what rule R-6's byte-identical-reruns guarantee forbids and what
    # `general_ledger_work_files` returning a fresh container every call exists
    # to prevent.
    files = general_ledger_work_files() if work_files is None else work_files

    # 167  main.
    _main(files)

    # 180  main-exit.  ->  181  goback.
    # Reached by fall-through, not by a transfer; called explicitly so the
    # fall-through is visible rather than implied.
    _main_exit()


# --- traceability ---------------------------------------------------------
#
# Rule R-5. Every construct of general/gl071.cbl, mapped to what reproduces it
# here, and every deliberate omission recorded AS an omission - Agent Action
# Plan section 0.4.3, verbatim, on why the omissions are listed rather than left
# implicit: "so that a reader comparing the two files does not conclude
# something was lost." This program is small enough that a reader will notice
# every absence, so the list below is exhaustive.
#
# PROGRAM  ->  MODULE
#   general/gl071.cbl  ->  acas_posting/programs/gl071_batch_sort.py
#   program-id gl071 [general/gl071.cbl:L12]; boundary THE WHOLE PROGRAM.
#
# PARAGRAPH  ->  FUNCTION
#   main.       [general/gl071.cbl:L167]       ->  _main
#   main-exit.  [general/gl071.cbl:L180]       ->  _main_exit
#   procedure division using ws-calling-data, system-record, to-day, file-defs
#               [general/gl071.cbl:L161-L164]  ->  run
#
#   Both are PARAGRAPHS, not sections: the four `section` keywords in the file
#   are `input-output` [general/gl071.cbl:L86], `file`
#   [general/gl071.cbl:L107], `working-storage` [general/gl071.cbl:L146] and
#   `linkage` [general/gl071.cbl:L152], all outside the procedure division. So
#   there is no `exit section.` anywhere, and the program ends on `goback.`
#   [general/gl071.cbl:L181].
#
#   NO PARAGRAPH-NAME COLLISIONS. Unlike `gl070`, which has four `loop.` and
#   five `main-exit.` paragraphs across its sections, and `gl072`, this program
#   has exactly two paragraph names and both are unique, so no qualification is
#   needed to say which `main-exit.` is meant.
#
# STATEMENT  ->  CALL SITE
#   display "Sorting.......Please wait            " at 0801 with
#   foreground-color 2   [general/gl071.cbl:L170]
#       ->  the INFO log record `acas_posting.workfiles.SORTING_DIAGNOSTIC`,
#           emitted once, by the first statement of `sort_using_giving` - see
#           `_main` for why it is not logged twice.
#   sort sort-trans on ascending key ... using pre-trans giving post-trans
#                        [general/gl071.cbl:L172-L178]
#       ->  `sort_using_giving(work_files.sort_trans,
#            on_ascending_key=SORT_TRANS_ASCENDING_KEYS,
#            using=work_files.pre_trans, giving=work_files.post_trans)` in
#           `_main`.
#   on ascending key sort-batch, sort-ac, sort-pc, sort-post
#                        [general/gl071.cbl:L173-L176]
#       ->  `acas_posting.workfiles.SORT_TRANS_ASCENDING_KEYS`, four keys, all
#           ascending, MOST SIGNIFICANT FIRST, in the statement's order and NOT
#           the sort description's declaration order
#           [general/gl071.cbl:L136-L144]. Both orders are set out in full in
#           `_main`.
#   goback.              [general/gl071.cbl:L181]  ->  `_main_exit`'s `return`.
#
# `GO TO`
#   `gl071` contains ZERO `GO TO` statements - measured over the
#   comment-stripped source, and the only zero in the twelve-program census.
#   The four-class taxonomy of Agent Action Plan section 0.4.2 therefore HAS NO
#   APPLICATION IN THIS MODULE, and no class is claimed anywhere in it. There is
#   likewise NO `PERFORM ... THRU` and no fall-through to make explicit: measured
#   over the comment-stripped source, `gl071` has zero of them, so there is
#   nothing here to hand-verify. Every one of the plan's in-scope occurrences is
#   in another program - see the census under CITATION CORRECTIONS.
#
# ANOMALY REGISTER  (rule R-4)
#   `gl071` reproduces NO entry from the anomaly register. It does, however,
#   carry the ordering contract that anomaly A-14 - `gl072`'s sequential nominal
#   read - depends on for its correctness; see Agent Action Plan section 0.6.4,
#   ordering dependency 1, and THE PRODUCER / CONSUMER CHAIN and WHY A DEFECT
#   ELSEWHERE IS SURVIVABLE in the module docstring. Nothing in this module
#   suggests, comments on, or prepares for changing that read: section 0.8.4
#   forbids it.
#
# OMISSIONS - deliberate, and each one recorded rather than silent
#   1. `display "Sorting.......Please wait            " at 0801 with
#      foreground-color 2.` [general/gl071.cbl:L170] - reproduced as an INFO log
#      record, ONCE. No database effect, and it never appears in a table dump.
#      The screen position, the colour and the literal's trailing padding are
#      presentation and are dropped.
#   2. `copy "envdiv.cob".` [general/gl071.cbl:L85] - environment-division
#      boilerplate, representation only, with no Python counterpart. Its
#      `SPECIAL-NAMES` paragraph is commented out [copybooks/envdiv.cob:L4-L5],
#      which is what leaves the NATIVE collating sequence governing every
#      character comparison in the sort.
#   3. `select sort-trans assign file-21.` [general/gl071.cbl:L102] and
#      `sd sort-trans.` with `01 sort-trans-record.`
#      [general/gl071.cbl:L134-L144] - the SORT work FILE has no Python
#      counterpart; `acas_posting.cobol.sortverb` orders in memory. The KEY
#      NAMES from that record ARE preserved, as the sort key list; the file is
#      not. `file-21` is `work.tmp` [copybooks/file21.cob:L1].
#   4. `77 prog-name pic x(15) value "gl071 (3.3.00)".`
#      [general/gl071.cbl:L149] - the version banner. Presentation only; `gl071`
#      never displays or writes it, unlike `gl072`, which moves its own into a
#      print line.
#   5. `77 fs-reply pic xx.` [general/gl071.cbl:L150] - declared as the FILE
#      STATUS of BOTH work files [general/gl071.cbl:L94],
#      [general/gl071.cbl:L99] and NEVER INSPECTED, because
#      `SORT ... USING ... GIVING` performs the opens, reads, writes and closes
#      implicitly and this program declares no `OPEN`, `READ`, `WRITE` or
#      `CLOSE` at all. No status check is invented (rule R-3). Note also that
#      this is a LOCAL two-character working-storage field, `pic xx`, and NOT
#      the `Fs-Reply pic 99` of [copybooks/wsfnctn.cob:L25] - a copybook `gl071`
#      does not copy. That picture divergence is registered in
#      `acas_posting.workfiles`, and it is a further reason this module imports
#      nothing from `acas_posting.dal`.
#   6. `access sequential` and `organization line sequential` on both work files
#      [general/gl071.cbl:L93-L95], [general/gl071.cbl:L98-L100] - subsumed by
#      `acas_posting.workfiles`'s ordered-sequence model, which is sequential by
#      construction.
#   7. Three of the four linkage parameters are accepted but UNREAD -
#      `ws-calling-data`, `system-record` and `to-day`. KEPT IN THE SIGNATURE
#      for shape uniformity with `gl070`, `gl072`, `gl080` and `gl051`; recorded
#      here so that the omission of any USE of them is visible. See question
#      Q-15 in the module docstring.
#   8. Stated affirmatively, because each absence is a fact about the frozen
#      source rather than a decision taken here: there is NO
#      `call "SYSTEM" using Print-Report` in `gl071` and no report spool-out
#      path of any kind; NO `accept` statement of any kind, so no interactive
#      prompt is dropped and none becomes a CLI parameter; and NO `GO TO`.
#      There is also no `MOVE`, no arithmetic statement, no `ROUNDED`, no `IF`,
#      no `PERFORM`, no `CALL`, no condition-name test and no clock read - which
#      is why this module imports no `dal`, no `cobol.arithmetic`, no
#      `cobol.move`, no `cobol.condition_names`, no `dates` and no `clock`.
#
# CITATION CORRECTIONS - the frozen files are the authority
#   Several spans cited by the Agent Action Plan do not match the frozen
#   sources. Every locator in this module is the FROZEN line, re-read from the
#   file rather than copied from the plan, and each divergence is recorded here
#   so the wrong span is not propagated by anyone reading this module. The first
#   two agree with the corrections `acas_posting.cobol.sortverb` already
#   records.
#     * THE WORK-FILE NAMES. The plan cites [copybooks/wsnames.cob:L14-L17]; the
#       frozen span is L13-L16 - `01 File-Defs.` at L13, `02 file-defs-a.` at
#       L14, `pre-trans-name` at L15 and `post-trans-name` at L16.
#     * `gl072`'s SEQUENTIAL NOMINAL READ. The plan cites
#       [general/gl072.cbl:L410-L412]; the frozen lines are the key move at
#       L405 and the read at L407-L408, L410-L411 holding the second
#       `if read-ledger not = "R"` and its `move zero to tot-dr tot-cr`.
#     * `main.` IN THIS PROGRAM. The plan places it at L169; the frozen file puts
#       it at [general/gl071.cbl:L167], L168-L169 being the paragraph's underline
#       comment and a blank comment line.
#     * THE MENU'S DISPATCH PARAGRAPHS. The plan cites `load08.` as L806-L816 and
#       the abort test as L800-L814; the frozen paragraph is
#       [general/general.cbl:L805-L815] with the test at L810-L811. `load00.` is
#       cited as L711-L723; the frozen paragraph label is at L711, the zeroing of
#       `ws-term-code` at L714, the `CALL` parameter list at L715-L718 and the
#       serious-error test at L720-L721.
#     * THE `ws-term-code = 5` SITE IN `gl070`. The plan cites L288 and
#       L312-L313; the frozen `move 5 to ws-term-code` is at L289 inside the
#       block [general/gl070.cbl:L287-L290], and L312-L313 is in fact phase 1's
#       ACCOUNTING-CYCLE FILTER, `if bcycle not = scycle / go to loop.`, a
#       different statement entirely.
#     * THE PHASE LABELS. The plan cites [general/gl070.cbl:L283] and
#       [general/gl070.cbl:L291] for phases 1 and 2, [general/gl072.cbl:L277] for
#       phase 4 and [general/gl080.cbl:L330] for phase 5; the frozen `display`
#       statements are at L284, L292, L274 and L336 respectively. Only the
#       phase-3 citation, [general/gl080.cbl:L319], is exact. Recorded also
#       because `gl080` in fact labels FIVE phases of its own - L306, L316, L319,
#       L336 and a "Phase - 4.  Posting Contraction" at L637 - which is a further
#       reason the numbering must not be read as an execution order.
#     * `gl070`'s `COPY` COUNT. The plan describes it as nine; the frozen file
#       carries eleven `copy` statements. `gl051`'s fifteen is exact. Recorded
#       only because this module's own count of FOUR is quoted against them.
#     * THE `PERFORM ... THRU` CENSUS. The plan counts seven in-scope
#       occurrences - "twice in `gl072`, once each in `sl100` and `pl100`, three
#       times in `irs030`". Measured over the comment-stripped sources, the sites
#       are [general/gl072.cbl:L300] and [general/gl072.cbl:L304],
#       [sales/sl100.cbl:L344], [purchase/pl100.cbl:L336],
#       [irs/irs030.cbl:L813], [irs/irs030.cbl:L831] and [irs/irs030.cbl:L832],
#       plus two the plan does not count at [general/gl051.cbl:L504] and
#       [general/gl051.cbl:L955]. The two `gl051` sites and all three `irs030`
#       sites fall OUTSIDE those programs' stated migration boundaries
#       ([general/gl051.cbl:L1096-L1133] and [irs/irs030.cbl:L1569-L1733]), which
#       leaves four inside the in-scope surface rather than seven. The count
#       affects neither this module nor its ordering contract - `gl071` has zero
#       either way - and is recorded so the discrepancy is not rediscovered as a
#       defect.
#
# --- end traceability -----------------------------------------------------
