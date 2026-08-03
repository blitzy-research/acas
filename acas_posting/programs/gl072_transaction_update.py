"""`gl072` - General Ledger phase 4, transaction update [general/gl072.cbl].

The whole program: it walks the sorted post-transaction stream and posts each
transaction into the nominal ledger, accumulating into the ledger balance.

The nominal account is located by a SEQUENTIAL read
[general/gl072.cbl:L408], guarded at L407, so correctness depends entirely on the
upstream sort order; L410-L411 then reset the running totals. Account numbers are
scaled by dividing by 100 [general/gl072.cbl:L386], [general/gl072.cbl:L413].

Order of the two closing steps is load-bearing: `end-account` runs before
`end-batch` [general/gl072.cbl:L297-L298], and it is `end-batch` that stamps the
batch cleared and records the posting date [general/gl072.cbl:L375-L377].
Inverting them would leave a batch marked posted with an unclosed final account.

Two rejections are entirely silent and stay that way - a non-numeric batch number
[general/gl072.cbl:L291-L292] and a handler error of 999
[general/gl072.cbl:L306-L307]. Neither produces a message, a counter or a trace,
so adding one would be an added behaviour.

Two `PERFORM ... THROUGH` sites [general/gl072.cbl:L300],
[general/gl072.cbl:L304] become explicit sequential calls; they are two of the
four such sites in the whole migrated cycle, the others being
[sales/sl100.cbl:L344] and [purchase/pl100.cbl:L336].

Deliberately not translated: the block of unused facade stubs the program
declares only so the linker resolves the copybook's full verb set
[general/gl072.cbl:L135-L153]. Python needs no such declaration, and the omission
is recorded here so a reader comparing the two files does not conclude something
was lost.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Final

from acas_posting.dal import facade

# copy "wsfnctn.cob". [general/gl072.cbl:L129] - the operation vocabulary half. `We-
# Error` is `pic 999` [copybooks/wsfnctn.cob:L23]; `WeError.NOT_USED` is its `999`, the
# sentinel `get-batch` borrows.
from acas_posting.dal.status import WeError

from acas_posting.cobol import arithmetic, condition_names, move, picture
from acas_posting.cobol.field import FieldDescriptor
from acas_posting.cobol.move import Figurative

from acas_posting.dates import WsDateFormats, zz070_convert_date

from acas_posting.records.calling_data import WsCallingData

from acas_posting.records.file_access import FileAccess

from acas_posting.records.file_defs import FileDefs

from acas_posting.records.gl_batch import GlBatchRecord

from acas_posting.records.gl_ledger import WsLedgerRecord

from acas_posting.records.system_record import SystemRecord

from acas_posting.records.test_data_flags import AcasDalCommonData

from acas_posting.records.work_records import PostTransRecord

# The work-file layer. `post-trans` is the output of `gl071` [general/gl071.cbl:L178],
# modelled as an ordered in-process sequence.
from acas_posting.workfiles import (
    GeneralLedgerWorkFiles,
    general_ledger_work_files,
)

logger: Final[logging.Logger] = logging.getLogger(__name__)

#: The whole public surface: the program's single entry point, mirroring its `PROCEDURE
#: DIVISION USING` list [general/gl072.cbl:L262-L265]. Agent Action Plan section 0.3.3,
#: verbatim.
__all__: Final[tuple[str, ...]] = ("run",)


#: `display "Phase - 4. Transaction Update" at 0801 with foreground-color 2.`
#: [general/gl072.cbl:L274].
_PHASE_4_DIAGNOSTIC: Final[str] = "Phase - 4.  Transaction Update"

#: The one-character flag value the page-overflow path stores [general/gl072.cbl:L338]
#: and the three guards test [general/gl072.cbl:L407], [general/gl072.cbl:L410],
#: [general/gl072.cbl:L421].
_READ_LEDGER_SUPPRESSED: Final[str] = "R"

#: The divisor of `divide WS-Ledger-Nos by 100 giving l6-account`
#: [general/gl072.cbl:L386], [general/gl072.cbl:L413].
_ACCOUNT_NUMBER_DIVISOR: Final[int] = 100

#: The two character positions of `WS-Ledger-Key`'s children inside the eight-byte group
#: image, ONE-BASED as COBOL reference modification is.
_WS_LEDGER_NOS_POSITION: Final[tuple[int, int]] = (1, 6)
_LEDGER_PC_POSITION: Final[tuple[int, int]] = (7, 2)

_LINE_CNT_AFTER_HEADINGS: Final[int] = 5

#: The scale-2 zero the two `value zero` clauses on the unsigned money accumulators
#: declare [general/gl072.cbl:L165-L166].
_MONEY_ZERO: Final[Decimal] = Decimal("0.00")


# Field descriptors (rule R-5: every field cites its dictionary entry) Two provenances,
# and the choice between them is not a preference.

_POST_BATCH: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "post-trans-record.post-batch#111"
)
_POST_LEDGER: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "post-trans-record.post-ledger"
)
_POST_AC: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "post-trans-record.post-ac#116"
)
_POST_PC: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "post-trans-record.post-pc#117"
)
# `03 post-amount pic s9(8)v99.` [general/gl072.cbl:L118] is NOT modelled as a
# descriptor here, and its absence is deliberate rather than an oversight.

_WS_LEDGER_KEY: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "WS-Ledger-Record.WS-Ledger-Key"
)
_WS_LEDGER_NOS: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "WS-Ledger-Record.WS-Ledger-Nos"
)
_LEDGER_PC: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "WS-Ledger-Record.Ledger-PC"
)
_LEDGER_BALANCE: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLLEDGER-REC.LEDGER-BALANCE"
)

_WS_LEDGER: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "WS-Batch-Record.WS-Ledger"
)
_WS_BATCH_NOS: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "WS-Batch-Record.WS-Batch-Nos"
)
_CLEARED_STATUS: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLBATCH-REC.CLEARED-STATUS"
)
_POSTED: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLBATCH-REC.POSTED"
)

# copy "wssystem.cob". [general/gl072.cbl:L257] `03 Run-Date binary-long.`
# [copybooks/wssystem.cob:L67] - one of exactly two observables the controlled clock
# pins, the other being the `to-day pic x(10)` text date.
_RUN_DATE: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "SYSTEM-REC.RUN-DAT"
)
#: `03 Date-Form pic 9.` [copybooks/wssystem.cob:L128], with `88 Date-UK value 1.` `88
#: Date-USA value 2.` and `88 Date-Intl value 3.` following it. READ AND WRITTEN.
_DATE_FORM: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "SYSTEM-REC.DATE-FORM"
)

_WE_ERROR: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "File-Access.We-Error"
)
_FILE_KEY_NO: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "File-Access.File-Key-No"
)
#: `03 Fs-Reply pic 99.` [copybooks/wsfnctn.cob:L25].
_FS_REPLY: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "File-Access.Fs-Reply"
)

_SAVE_BATCH: Final[FieldDescriptor] = picture.descriptor_for(
    "pic 9(5) value zero",
    name="save-batch",
    source_locator="general/gl072.cbl:L160",
)
_SAVE_LEDGER: Final[FieldDescriptor] = picture.descriptor_for(
    "pic 9(8) value zero",
    name="save-ledger",
    source_locator="general/gl072.cbl:L161",
)
_READ_LEDGER: Final[FieldDescriptor] = picture.descriptor_for(
    "pic x value space",
    name="read-ledger",
    source_locator="general/gl072.cbl:L162",
)
#: `03 line-cnt binary-char value zero.` [general/gl072.cbl:L163] - SIGNED, because no
#: `unsigned` follows `binary-char`, unlike the six page-geometry fields immediately
#: below it [general/gl072.cbl:L169-L174] which all carry it.
_LINE_CNT: Final[FieldDescriptor] = picture.descriptor_for(
    "binary-char value zero",
    name="line-cnt",
    source_locator="general/gl072.cbl:L163",
)
_Y: Final[FieldDescriptor] = picture.descriptor_for(
    "pic 99 value zero",
    name="y",
    source_locator="general/gl072.cbl:L164",
)
_TOT_DR: Final[FieldDescriptor] = picture.descriptor_for(
    "pic 9(8)v99 value zero",
    name="tot-dr",
    source_locator="general/gl072.cbl:L165",
)
_TOT_CR: Final[FieldDescriptor] = picture.descriptor_for(
    "pic 9(8)v99 value zero",
    name="tot-cr",
    source_locator="general/gl072.cbl:L166",
)

_L6_ACCOUNT: Final[FieldDescriptor] = picture.descriptor_for(
    "pic 9999.99 blank when zero",
    name="l6-account",
    source_locator="general/gl072.cbl:L233",
)


@dataclass(slots=True)
class _ProgramStorage:
    """`gl072`'s LINKAGE and WORKING-STORAGE sections, in one place.

    COBOL paragraphs do not take arguments: every paragraph of a program sees the whole
    of its working-storage and the whole of its linkage.
    """

    ws_calling_data: WsCallingData
    system_record: SystemRecord
    to_day: str
    file_defs: FileDefs

    file_access: FileAccess
    ledger: WsLedgerRecord
    batch: GlBatchRecord
    dal_common: AcasDalCommonData
    date_formats: WsDateFormats

    work_files: GeneralLedgerWorkFiles
    ledger_ctx: facade.FacadeContext
    batch_ctx: facade.FacadeContext

    save_batch: int = 0
    save_ledger: int = 0
    read_ledger: str = " "
    line_cnt: int = 0
    y: int = 0
    tot_dr: Decimal = _MONEY_ZERO
    tot_cr: Decimal = _MONEY_ZERO

    #: `03 l6-account pic 9999.99 blank when zero.` [general/gl072.cbl:L233] - the
    #: receiver of both divides, [general/gl072.cbl:L386] and [general/gl072.cbl:L413].
    #: Print-only.
    l6_account: Decimal = _MONEY_ZERO

    post: PostTransRecord = field(default_factory=PostTransRecord)


def _post_ledger_group_image(post: PostTransRecord) -> str:
    """The eight-character byte image of `03 post-ledger.`.

    `post-ledger` [general/gl072.cbl:L115-L117] is a GROUP item over `post-ac pic 9(6)`
    and `post-pc pic 99`, and COBOL lets a group be used as an alphanumeric item of the
    concatenated width of its children - which is what makes `move post-ledger to WS-
    Ledger-Key` [general/gl072.cbl:L405] and `move post-ledger to save-ledger`
    [general/gl072.cbl:L317] legal, and what makes `if post-ledger not = save-ledger`
    [general/gl072.cbl:L309] a comparison rather than a type error.

    Args:
        post: The `01 post-trans-record.` area whose `post-ledger` group is wanted. Both
            children are read; nothing is written.

    Returns:
        Exactly eight characters - six digits of account number followed by two of
            profit centre.
    """
    return move.move_group(
        post.post_ledger.post_ac, _POST_LEDGER, sending_field=_POST_AC
    ) + move.move_group(
        post.post_ledger.post_pc, _POST_LEDGER, sending_field=_POST_PC
    )


def _gl072_main(st: _ProgramStorage) -> None:
    """`gl072-Main section.` - the opens and the break-detector reset.

    Control FALLS THROUGH from here into `loop.` [general/gl072.cbl:L283]; the section
    header carries no `exit section.` and there is no transfer at the end of L281.

    Args:
        st: The program's storage. `file_access.logging_data.file_key_no`, `save_batch`
            and `save_ledger` are written; the two facade contexts and the work-file
            container are used.
    """
    # 271 move Print-Spool-Name to PSN. OMITTED - the report spool-out path.

    # 272 move 1 to File-Key-No. AMBIGUITY Q-18. Reproduced although it is almost
    # certainly inert.
    st.file_access.logging_data.file_key_no = move.move(1, _FILE_KEY_NO)

    logger.info(_PHASE_4_DIAGNOSTIC)


    facade.gl_batch_open(st.batch_ctx)

    facade.gl_nominal_open(st.ledger_ctx)

    # 278 open input post-trans. The work sequence `gl071` wrote
    # [general/gl071.cbl:L178]. Opened INPUT.
    st.work_files.post_trans.open_input()
    # `select post-trans ...
    st.file_access.fs_reply = move.move(
        st.work_files.post_trans.fs_reply, _FS_REPLY
    )


    # 281 move zero to save-batch save-ledger. A TWO-RECEIVER `MOVE` of the figurative
    # constant.
    st.save_batch, st.save_ledger = move.move_to_all(
        Figurative.ZERO, [_SAVE_BATCH, _SAVE_LEDGER]
    )


def _loop(st: _ProgramStorage) -> None:
    """`loop.` - the main read loop, and the one statement that posts.

    Every exit from this paragraph is a `GO TO`: three of them return to `loop.` itself
    [general/gl072.cbl:L292], [general/gl072.cbl:L307], [general/gl072.cbl:L341] and one
    leaves for `end-run.` [general/gl072.cbl:L289].

    Args:
        st: The program's storage.
    """
    while True:
        record = st.work_files.post_trans.read_next()
        st.file_access.fs_reply = move.move(
            st.work_files.post_trans.fs_reply, _FS_REPLY
        )
        if record is None:
            _end_account(st)
            _end_batch(st)
            break
        st.post = record

        # 291 if post-batch not numeric 292 go to loop. ANOMALY A-13
        # [general/gl072.cbl:L291-L292] - site (a).
        if not move.is_numeric_class(st.post.post_batch, _POST_BATCH):
            continue

        # 294 if post-batch not = save-batch 295 and save-batch not = zero 296 and we-
        # error not = 999 297 perform end-account 298 perform end-batch 299 move zero to
        # save-ledger 300 perform headings through headings-end.
        if (
            arithmetic.compare(st.post.post_batch, st.save_batch) != 0
            and arithmetic.compare(st.save_batch, 0) != 0
            and arithmetic.compare(st.file_access.we_error, WeError.NOT_USED)
            != 0
        ):
            _end_account(st)
            _end_batch(st)
            st.save_ledger = move.move(Figurative.ZERO, _SAVE_LEDGER)
            # PERFORM THRU [general/gl072.cbl:L300] - hand-verified: spans headings
            # (L343) through headings-end (L369), which has an empty body.
            _headings(st)
            _headings_end()

        if arithmetic.compare(st.save_batch, 0) == 0:
            st.save_batch = move.move(
                st.post.post_batch, _SAVE_BATCH, sending_field=_POST_BATCH
            )
            # PERFORM THRU [general/gl072.cbl:L304] - hand-verified: spans headings
            # (L343) through headings-end (L369), which has an empty body.
            _headings(st)
            _headings_end()

        # 306 if we-error equal 999 307 go to loop. ANOMALY A-13
        # [general/gl072.cbl:L306-L307] - site (b).
        if arithmetic.compare(st.file_access.we_error, WeError.NOT_USED) == 0:
            continue

        # 309 if post-ledger not = save-ledger 310 and save-ledger not = zero 311
        # perform end-account 312 perform new-account. THE COMPOSITE LEDGER KEY, ONCE.
        post_ledger_value = move.move(
            _post_ledger_group_image(st.post),
            _SAVE_LEDGER,
            sending_field=_POST_LEDGER,
        )
        if (
            arithmetic.compare(post_ledger_value, st.save_ledger) != 0
            and arithmetic.compare(st.save_ledger, 0) != 0
        ):
            _end_account(st)
            _new_account(st)

        # 314 if save-ledger equal zero 315 perform new-account. A SEPARATE `if`, not an
        # `else` of the one above.
        if arithmetic.compare(st.save_ledger, 0) == 0:
            _new_account(st)

        st.save_ledger = post_ledger_value


        # 321 if post-amount > zero 322 move post-amount to l6-debit 323 add post-amount
        # to tot-dr 324 move zero to l6-credit 325 else 326 move post-amount to
        # l6-credit 327 subtract post-amount from tot-cr 328 move zero to l6-debit.
        if arithmetic.compare(st.post.post_amount, 0) > 0:
            # 323 add post-amount to tot-dr No `ROUNDED`, so the store truncates toward
            # zero.
            st.tot_dr = arithmetic.add_to(
                st.post.post_amount,
                receiver_value=st.tot_dr,
                receiving=_TOT_DR,
                rounded=False,
            )
        else:
            st.tot_cr = arithmetic.subtract_from(
                st.post.post_amount,
                receiver_value=st.tot_cr,
                receiving=_TOT_CR,
                rounded=False,
            )


        st.ledger.ledger_balance = arithmetic.add_to(
            st.post.post_amount,
            receiver_value=st.ledger.ledger_balance,
            receiving=_LEDGER_BALANCE,
            rounded=False,
        )


        st.line_cnt = arithmetic.add_to(
            1, receiver_value=st.line_cnt, receiving=_LINE_CNT, rounded=False
        )

        # 335 if line-cnt > Page-Lines 336 perform end-account 337 perform headings 338
        # move "R" to read-ledger 339 perform new-account.
        if arithmetic.compare(
            st.line_cnt, st.system_record.system_data_block.page_lines
        ) > 0:
            _end_account(st)
            # 337 perform headings THE BARE FORM - `perform headings`, with NO `through
            # headings-end`.
            _headings(st)
            st.read_ledger = move.move(_READ_LEDGER_SUPPRESSED, _READ_LEDGER)
            _new_account(st)

        # 341 go to loop. GO TO class 1 - loop-back to [general/gl072.cbl:L283].
        continue


def _headings(st: _ProgramStorage) -> None:
    """`headings.` - a page of headings, and the batch read that gates the run.

    `perform get-batch` issues a `GL-Batch-Read-Next` and, through it, sets `We-Error`,
    `save-batch` and the batch record area that `end-batch` later stamps and rewrites.

    Args:
        st: The program's storage. `y` and `line_cnt` are written here; `file_access`,
            `save_batch`, the batch record area and `date_formats` are written by the
            two paragraphs performed.
    """
    # 346 perform get-batch. THE DATABASE READ. Preserved even though every other line
    # of this paragraph is print construction.
    _get_batch(st)

    # 348 if we-error equal 999 349 go to headings-end. GO TO class 3 - paragraph exit.
    # CLASSIFIED BY SHAPE, NOT BY NAME.
    if arithmetic.compare(st.file_access.we_error, WeError.NOT_USED) == 0:
        return

    _zz070_convert_date(st)


    st.y = arithmetic.add_to(
        1, receiver_value=st.y, receiving=_Y, rounded=False
    )


    # 357 if y not = 1 358 write print-record from line-1 after page 359 write print-
    # record from line-3 after 1 360 move spaces to print-record 361 write print-record
    # after 1 362 else 363 write print-record from line-1 before 1 364 write print-
    # record from line-3 before 1.

    st.line_cnt = move.move(_LINE_CNT_AFTER_HEADINGS, _LINE_CNT)


def _headings_end() -> None:
    """`headings-end.` - the `PERFORM ... THRU` range terminator; EMPTY.

    THIS IS NOT A STUB, AND ITS EMPTY BODY IS NOT A PLACEHOLDER. There is nothing
    deferred, nothing unimplemented and nothing to add: an empty COBOL paragraph
    reproduced faithfully is an empty function.
    """
    # The paragraph's body, in full: nothing. Its docstring is its implementation,
    # because there is no statement between [general/gl072.cbl:L369] and
    # [general/gl072.cbl:L372] to reproduce.


def _end_batch(st: _ProgramStorage) -> None:
    """`end-batch.` - stamp the batch cleared and posted, and rewrite it.

    DECLARED BEFORE `end-account.` [general/gl072.cbl:L379] AND CALLED AFTER IT. Both
    call sites - the at-end clause [general/gl072.cbl:L287-L288] and the batch break
    [general/gl072.cbl:L297-L298] - perform `end-account` first.

    Args:
        st: The program's storage. `batch.cleared_status` and `batch.dates.posted` are
            written, then the row is rewritten through the batch facade context.
            `system_record` is read for the run date.
    """
    # 375 move 1 to cleared-status. DATABASE EFFECT. `1` is the `88 Processed` condition
    # name on `03 Cleared-Status pic 9.` [copybooks/wsbatch.cob:L29-L31].
    st.batch.cleared_status = move.move(
        condition_names.values_for("Processed")[0], _CLEARED_STATUS
    )

    st.batch.dates.posted = move.move(
        st.system_record.system_data_block.run_date,
        _POSTED,
        sending_field=_RUN_DATE,
    )

    # 377 perform GL-Batch-Rewrite. *> rewrite batch-record. [copybooks/Proc-ACAS-FH-
    # Calls.cob:L475-L478]. Its reply is NOT tested.
    facade.gl_batch_rewrite(st.batch_ctx)


def _end_account(st: _ProgramStorage) -> None:
    """`end-account.` - rewrite the nominal account, then print its totals.

    THE REWRITE COMES FIRST, BEFORE ANY PRINT WORK, and that ordering is preserved: it
    is the statement that persists the balance [general/gl072.cbl:L331] accumulated
    into.

    Args:
        st: The program's storage. The nominal row is rewritten through the ledger
            facade context; `line_cnt` and `l6_account` are written.
    """
    # 382 perform GL-Nominal-Rewrite. *> rewrite ledger-record. The `UPDATE` of
    # `GLLEDGER-REC` [copybooks/Proc-ACAS-FH-Calls.cob:L349-L352] that persists the
    # balance accumulated by [general/gl072.cbl:L331].
    facade.gl_nominal_rewrite(st.ledger_ctx)


    st.line_cnt = arithmetic.add_to(
        1, receiver_value=st.line_cnt, receiving=_LINE_CNT, rounded=False
    )

    # 386 divide WS-Ledger-Nos by 100 giving l6-account.
    st.l6_account = arithmetic.divide_by_giving(
        st.ledger.ws_ledger_key.ws_ledger_nos,
        _ACCOUNT_NUMBER_DIVISOR,
        _L6_ACCOUNT,
        rounded=False,
    )


    st.line_cnt = arithmetic.add_to(
        3, receiver_value=st.line_cnt, receiving=_LINE_CNT, rounded=False
    )


def _new_account(st: _ProgramStorage) -> None:
    """`new-account.` - position on the next account, print its brought forward.

    WHERE ANOMALY A-14 LIVES. See the comment at L405-L408 below.

    Args:
        st: The program's storage. `ledger.ws_ledger_key`, `tot_dr`, `tot_cr`,
            `l6_account`, `line_cnt`, `read_ledger`, `date_formats` and - through the
            read - the whole ledger record area are written.
    """
    # 405 move post-ledger to WS-Ledger-Key.
    ws_ledger_key_image = move.move_group(
        _post_ledger_group_image(st.post),
        _WS_LEDGER_KEY,
        sending_field=_POST_LEDGER,
    )
    st.ledger.ws_ledger_key.ws_ledger_nos = move.move_numeric(
        move.ref_mod(ws_ledger_key_image, *_WS_LEDGER_NOS_POSITION),
        _WS_LEDGER_NOS,
    )
    st.ledger.ws_ledger_key.ledger_pc = move.move_numeric(
        move.ref_mod(ws_ledger_key_image, *_LEDGER_PC_POSITION),
        _LEDGER_PC,
    )

    # 407 if read-ledger not = "R" 408 perform GL-Nominal-Read-Next. *> read ledger-file
    # record. GUARD ONE OF THREE. THE SEQUENTIAL READ - see the A-14 comment above.
    if st.read_ledger != _READ_LEDGER_SUPPRESSED:
        facade.gl_nominal_read_next(st.ledger_ctx)

    # 410 if read-ledger not = "R" 411 move zero to tot-dr tot-cr. GUARD TWO OF THREE, a
    # SEPARATE `if` with the same condition.
    if st.read_ledger != _READ_LEDGER_SUPPRESSED:
        st.tot_dr, st.tot_cr = move.move_to_all(
            Figurative.ZERO, [_TOT_DR, _TOT_CR]
        )

    # 413 divide WS-Ledger-Nos by 100 giving l6-account. UNCONDITIONAL - it sits between
    # guard two and guard three. Presentation only, exactly as at
    # [general/gl072.cbl:L386].
    st.l6_account = arithmetic.divide_by_giving(
        st.ledger.ws_ledger_key.ws_ledger_nos,
        _ACCOUNT_NUMBER_DIVISOR,
        _L6_ACCOUNT,
        rounded=False,
    )


    # 418 perform zz070-convert-date. UNCONDITIONAL, AND NOT PRINT-ONLY IN EFFECT.
    _zz070_convert_date(st)


    # 421 if read-ledger not = "R" 422 if ledger-balance > zero 423 move ledger-balance
    # to l6-debit 424 add ledger-balance to tot-dr 425 else 426 move ledger-balance to
    # l6-credit 427 add ledger-balance to tot-cr.
    if st.read_ledger != _READ_LEDGER_SUPPRESSED:
        if arithmetic.compare(st.ledger.ledger_balance, 0) > 0:
            st.tot_dr = arithmetic.add_to(
                st.ledger.ledger_balance,
                receiver_value=st.tot_dr,
                receiving=_TOT_DR,
                rounded=False,
            )
        else:
            # 427 add ledger-balance to tot-cr AMBIGUITY Q-19, second of its two sites.
            st.tot_cr = arithmetic.add_to(
                st.ledger.ledger_balance,
                receiver_value=st.tot_cr,
                receiving=_TOT_CR,
                rounded=False,
            )


    # 431 move space to read-ledger. THE RESET, and it is unconditional.
    st.read_ledger = move.move(Figurative.SPACE, _READ_LEDGER)


    st.line_cnt = arithmetic.add_to(
        2, receiver_value=st.line_cnt, receiving=_LINE_CNT, rounded=False
    )


def _end_run(st: _ProgramStorage) -> None:
    """`end-run.` - the closes. The class-2 post-loop block.

    REACHED ONLY BY `go to end-run` FROM THE AT-END CLAUSE [general/gl072.cbl:L289] -
    there is no other path to it and no fall-through into it, because `loop.` always
    transfers.

    Args:
        st: The program's storage. The work sequence is closed and both facade files are
            closed; `file_access.fs_reply` is written by the close.
    """
    # 440 close post-trans print-file. The work sequence's close.
    st.work_files.post_trans.close()
    st.file_access.fs_reply = move.move(
        st.work_files.post_trans.fs_reply, _FS_REPLY
    )

    facade.gl_batch_close(st.batch_ctx)

    facade.gl_nominal_close(st.ledger_ctx)

    # 443 call "SYSTEM" using Print-Report. OMITTED, DELIBERATELY, AND FOR TWO
    # INDEPENDENT REASONS.


def _gl072_main_main_exit() -> None:
    """`main-exit.` of `gl072-Main section.` - the `goback`.

    `goback` in a called program returns control to its caller, leaving the linkage
    block as it stands. `gl072` never writes `WS-Term-Code`, so the value the menu reads
    back is the zero `load00.` moved in before the `CALL` [general/general.cbl:L714].
    """
    return


def _get_batch(st: _ProgramStorage) -> None:
    """`get-batch section.` - read the batch header and set or clear the sentinel.

    THE ONLY SETTER OF THE `999` SENTINEL, AND THE ONLY READER OF THE BATCH FILE.
    Performed from exactly one place, `headings.` [general/gl072.cbl:L346]. Everything
    the rest of the program does with `We-Error` follows from the four lines at
    L458-L462.

    Args:
        st: The program's storage. `batch.ws_batch_key`, `save_batch` and
            `file_access.we_error` are written; the whole batch record area is replaced
            by the read.
    """
    # 451 move 1 to WS-Ledger.
    st.batch.ws_batch_key.ws_ledger = move.move(
        condition_names.values_for("GL-Batch")[0], _WS_LEDGER
    )

    # 452 move post-batch to save-batch WS-Batch-Nos. A TWO-RECEIVER `MOVE` ACROSS
    # DIFFERENT PICTURES - `save-batch pic 9(5)` [general/gl072.cbl:L160] and `WS-Batch-
    # Nos pic 9(5)` [copybooks/wsbatch.cob:L19].
    st.save_batch, st.batch.ws_batch_key.ws_batch_nos = move.move_to_all(
        st.post.post_batch,
        [_SAVE_BATCH, _WS_BATCH_NOS],
        sending_field=_POST_BATCH,
    )

    # 454 perform GL-Batch-Read-Next. *> read batch-file record. [copybooks/Proc-ACAS-
    # FH-Calls.cob:L460-L463]. SEQUENTIAL.
    facade.gl_batch_read_next(st.batch_ctx)

    # 456 move description of WS-Batch-Record to l3-desc. OMITTED - print-line receiver
    # [general/gl072.cbl:L219].

    # 458 if not waiting 459 move 999 to we-error 460 move 0 to save-batch 461 else 462
    # move 0 to we-error.
    if not condition_names.is_waiting(st.batch.cleared_status):
        # 459 move 999 to we-error `999` IS `WeError.NOT_USED`
        # [copybooks/wsfnctn.cob:L23] - the handler vocabulary's "not used" sentinel,
        # borrowed here as a private flag.
        st.file_access.we_error = move.move(WeError.NOT_USED, _WE_ERROR)
        st.save_batch = move.move(0, _SAVE_BATCH)
    else:
        # 462 move 0 to we-error Clears the sentinel for an accepted batch.
        st.file_access.we_error = move.move(0, _WE_ERROR)

    _get_batch_main_exit()


def _get_batch_main_exit() -> None:
    """`main-exit.` of `get-batch section.` - a plain `EXIT`, a no-operation.

    A PLAIN `EXIT`, NOT `exit section.` COBOL's `EXIT` statement is a NO-OPERATION whose
    only purpose is to give a series of procedures a common end point; it transfers
    nothing.
    """
    return


def _zz070_convert_date(st: _ProgramStorage) -> None:
    """`zz070-Convert-Date section.` - reformat `to-day` into the configured form.

    NO CLOCK IS READ (rule R-6).

    Args:
        st: The program's storage. `date_formats.ws_date` and `system_record`'s `Date-
            Form` are written; `to_day` is read.
    """
    # 475 move to-day to ws-date. ... through ... 492 move to-day (1:2) to ws-Intl-Days.
    # The whole section body, delegated.
    effective_date_form = zz070_convert_date(
        st.date_formats,
        st.to_day,
        st.system_record.system_data_block.date_form,
    )

    # 478 move 1 to Date-Form. The defaulted value stored back into the system record,
    # which is where the COBOL puts it.
    st.system_record.system_data_block.date_form = move.move(
        effective_date_form, _DATE_FORM
    )

    _zz070_exit()


def _zz070_exit() -> None:
    """`zz070-Exit.` - `exit section.`, the real one.

    The function is present because rule R-5 requires a named function for every
    paragraph, and because the contrast with the plain `EXIT` thirty lines earlier is
    worth being able to point at.
    """
    return


def run(
    ws_calling_data: WsCallingData,
    system_record: SystemRecord,
    to_day: str,
    file_defs: FileDefs,
    *,
    work_files: GeneralLedgerWorkFiles | None = None,
    dal_common: AcasDalCommonData | None = None,
) -> None:
    """Run `gl072` - post the sorted transaction stream to the nominal ledger.

    The four positional parameters below are that list, in that order, under those names
    - the four-parameter General Ledger call shape, shared character-for-character by
    `gl051` [general/gl051.cbl:L353-L356], `gl070` [general/gl070.cbl:L245-L248],
    `gl071` [general/gl071.cbl:L161-L164], this program and `gl080`
    [general/gl080.cbl:L269-L272], because all five are dispatched through the SAME menu
    paragraph `load00.` [general/general.cbl:L711-L722] with one `CALL` parameter list
    [general/general.cbl:L715-L718].

    Args:
        ws_calling_data: `01 WS-Calling-Data` [copybooks/wscall.cob:L6-L14]. ACCEPTED
            AND UNREAD, and not written back either.
        system_record: `SYSTEM-REC`, the 169-column system record. READ for `Run-Date`
            [copybooks/wssystem.cob:L67], `Page-Lines` [copybooks/wssystem.cob:L65],
            `Date-Form` [copybooks/wssystem.cob:L128] and `Scycle`
            [copybooks/wssystem.cob:L63]; WRITTEN at `Date-Form`.
        to_day: `to-day pic x(10)` in DD/MM/CCYY form. The controlled clock's text
            observable; no clock is read here or downstream of here.
        file_defs: `01 File-Defs.` [copybooks/wsnames.cob:L13], the file-name buffers.
            Supplies `post-trans-name` [copybooks/wsnames.cob:L16] to the FILE-CONTROL
            entry [general/gl072.cbl:L95], and is the fourth argument of every handler
            `CALL`.
        work_files: The General Ledger cycle's work-file sequences. NOT A LINKAGE
            PARAMETER - keyword-only, and it stands in for what the compiled program
            uses instead.
        dal_common: `ACAS-DAL-Common-Data` [copybooks/Test-Data-Flags.cob], the fifth
            argument of every handler `CALL`. KEYWORD-ONLY AND NOT A LINKAGE PARAMETER.

    Raises:
        acas_posting.workfiles.WorkFileError: The work sequence was handed a record
            description it cannot carry, or was read in a mode that does not permit it.
            A PROGRAMMER error.
        acas_posting.dal.facade.FacadeError: A facade verb reached a boundary the
            migration states rather than crosses. Not raised by any of the eight verbs
            this program performs.
    """
    # NOT VALIDATION - two default resolutions Python signatures cannot express (rule
    # R-3). Neither tests a value that reaches an accounting decision.
    files = general_ledger_work_files() if work_files is None else work_files
    common = AcasDalCommonData() if dal_common is None else dal_common

    # working-storage section.
    file_access = FileAccess()
    ledger = WsLedgerRecord()
    batch = GlBatchRecord()
    date_formats = WsDateFormats()

    # TWO FACADE LINKAGES OVER ONE STATUS FIELD.
    ledger_ctx = facade.FacadeContext(
        system=system_record,
        record=ledger,
        file_access=file_access,
        file_defs=file_defs,
        dal_common=common,
    )
    batch_ctx = facade.FacadeContext(
        system=system_record,
        record=batch,
        file_access=file_access,
        file_defs=file_defs,
        dal_common=common,
    )

    st = _ProgramStorage(
        ws_calling_data=ws_calling_data,
        system_record=system_record,
        to_day=to_day,
        file_defs=file_defs,
        file_access=file_access,
        ledger=ledger,
        batch=batch,
        dal_common=common,
        date_formats=date_formats,
        work_files=files,
        ledger_ctx=ledger_ctx,
        batch_ctx=batch_ctx,
    )

    _gl072_main(st)

    _loop(st)

    _end_run(st)

    _gl072_main_main_exit()
