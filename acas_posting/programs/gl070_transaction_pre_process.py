"""`gl070` - General Ledger phases 1 and 2 [general/gl070.cbl].

The whole program: phase 1 checks the batches and phase 2 pre-processes the
transactions into the pre-transaction work file that gl071 sorts and gl072 posts.

Phase 1 walks the batch file filtering on the accounting cycle
[general/gl070.cbl:L312-L313], and on finding a batch still open
[general/gl070.cbl:L314-L315] answers with terminate code 5
[general/gl070.cbl:L289] and returns. That code is a hard gate: the menu tests it
and returns [general/general.cbl:L810-L811], so gl071 and gl072 never run.

Phase 2 walks the batch file AGAIN, and the second pass adds status conditions
the first does not [general/gl070.cbl:L460-L463]. Collapsing the two passes into
one would change which batches are pre-processed, so both are kept.

Each accepted transaction explodes into up to three legs
[general/gl070.cbl:L495-L533]: the debit leg, the credit leg with its amount
negated by `multiply pre-amount by -1` [general/gl070.cbl:L517], and a VAT leg
written only when both the VAT account and the VAT amount are non-zero
[general/gl070.cbl:L521-L523].

Two representation details are preserved rather than tidied. Field-name
collisions across three posting copybooks force qualified references -
`post-code in WS-Posting-Record` [general/gl070.cbl:L497] and `vat-ac of
WS-Posting-Record` [general/gl070.cbl:L521], [general/gl070.cbl:L525]. And the
wrapper section around the date module is named after the interface copybook
while its exit label is named after the called program
[general/gl070.cbl:L603-L609].

This program contains no clock read; the run date arrives through linkage.
"""

from __future__ import annotations

import dataclasses
import decimal
import logging
from collections.abc import Mapping
from typing import Final

from acas_posting.cobol import arithmetic
from acas_posting.cobol import condition_names
from acas_posting.cobol import move as cobol_move
from acas_posting.cobol.field import FieldDescriptor
from acas_posting.dal import facade
from acas_posting.dal.status import FsReply
from acas_posting.dates import WsDateFormats
from acas_posting.dates import maps03 as dates_maps03
from acas_posting.dates import zz060_convert_date as dates_zz060_convert_date
from acas_posting.dates import zz070_convert_date as dates_zz070_convert_date
from acas_posting.records.calling_data import WsCallingData
from acas_posting.records.file_access import FileAccess
from acas_posting.records.file_access import LoggingData
from acas_posting.records.file_defs import FileDefs
from acas_posting.records.gl_batch import GlBatchRecord
from acas_posting.records.gl_batch import WsBatchKey
from acas_posting.records.gl_posting import WsPostingRecord
from acas_posting.records.gl_posting import WsPostKey
from acas_posting.records.maps03 import Maps03Ws
from acas_posting.records.system_record import SystemRecord
from acas_posting.records.test_data_flags import AcasDalCommonData
from acas_posting.records.work_records import COBOL_FIELD_METADATA_KEY
from acas_posting.records.work_records import PreTransRecord
from acas_posting.workfiles import GeneralLedgerWorkFiles
from acas_posting.workfiles import general_ledger_work_files

#: The single public name.
__all__: Final[tuple[str, ...]] = ("run",)


_LOG: Final[logging.Logger] = logging.getLogger(__name__)


#: `77 prog-name pic x(15) value "gl070 (3.3.00)".` [general/gl070.cbl:L123].
_PROG_NAME: Final[str] = "gl070 (3.3.00)"


#: `move 5 to ws-term-code.` [general/gl070.cbl:L289]. THE abort value.
_WS_TERM_CODE_OPEN_BATCH_FOUND: Final[int] = 5


_DETECTOR_RAISED: Final[int] = 1
_DETECTOR_CLEAR: Final[int] = 0


_FILE_KEY_NO_PRIMARY: Final[int] = 1


# Not one `FieldDescriptor` is built in this module.


def _pre_trans_descriptors() -> dict[str, FieldDescriptor]:
    """Map each `pre-trans-record` attribute to the descriptor it carries.

    `acas_posting.records.work_records` attaches the descriptor of every field of `01
    pre-trans-record.` [general/gl070.cbl:L108-L116] to the dataclass member's
    `metadata`, and its module docstring publishes this exact loop as the way to read
    them back.

    Returns:
        Attribute name to descriptor, for all eight members.
    """
    return {
        member.name: member.metadata[COBOL_FIELD_METADATA_KEY]
        for member in dataclasses.fields(PreTransRecord)
    }


_PRE: Final[dict[str, FieldDescriptor]] = _pre_trans_descriptors()

_POST: Final[dict[str, FieldDescriptor]] = {
    descriptor.name: descriptor for descriptor in WsPostingRecord.FIELDS
}

_POST_KEY: Final[dict[str, FieldDescriptor]] = {
    descriptor.name: descriptor for descriptor in WsPostKey.FIELDS
}

#: `05 File-Key-No pic 9.` [copybooks/wsfnctn.cob:L46], inside `03 Logging-Data.` rather
#: than beside the status fields.
_FILE_KEY_NO: Final[FieldDescriptor] = next(
    descriptor
    for descriptor in LoggingData.FIELDS
    if descriptor.name == "File-Key-No"
)

#: `05 WS-Batch-Nos pic 9(5).` [copybooks/wsbatch.cob:L19], the sending field of `move
#: WS-Batch-Nos to pre-batch.` [general/gl070.cbl:L480].
_BATCH_NOS: Final[FieldDescriptor] = next(
    descriptor
    for descriptor in WsBatchKey.FIELDS
    if descriptor.name == "WS-Batch-Nos"
)

_U_BIN: Final[FieldDescriptor] = next(
    descriptor for descriptor in Maps03Ws.FIELDS if descriptor.name == "u-bin"
)


#: `if post-vat-side = "CR"` [general/gl070.cbl:L503], [general/gl070.cbl:L529] and `if
#: post-vat-side = "DR"` [general/gl070.cbl:L512].
_VAT_SIDE_CREDIT: Final[str] = "CR"
_VAT_SIDE_DEBIT: Final[str] = "DR"

#: The zero every numeric comparison in this module is made against. A
#: `decimal.Decimal`, so the two-place amounts compare without any coercion.
_ZERO: Final[decimal.Decimal] = decimal.Decimal(0)


#: `move " G/L" to l6-ledger.` [general/gl070.cbl:L355] and its two siblings
#: [general/gl070.cbl:L357], [general/gl070.cbl:L359].
_LEDGER_LABEL_GL: Final[str] = " G/L"
_LEDGER_LABEL_PL: Final[str] = " P/L"
_LEDGER_LABEL_SL: Final[str] = " S/L"

_STATUS_LABEL_OPEN: Final[str] = "Open"
_STATUS_LABEL_WAITING: Final[str] = "Waiting"
_STATUS_LABEL_PROCESSED: Final[str] = "Processed"
_STATUS_LABEL_ARCHIVED: Final[str] = "Archived"

_REPORT_FIRST_BODY_LINE: Final[int] = 7

_REPORT_LINES_PER_BATCH: Final[int] = 3


@dataclasses.dataclass(slots=True)
class _WorkingStorage:
    """What `gl070`'s WORKING-STORAGE and LINKAGE hold for one run.

    NOT A COBOL CONSTRUCT AND NOT PART OF THE PUBLIC API. COBOL gives a called program a
    working-storage section that persists for the life of the run and a linkage section
    that aliases the caller's data.

    Attributes:
        ws_calling_data: `01 WS-Calling-Data.` [copybooks/wscall.cob:L6], the first
            linkage parameter. Written on the abort path and nowhere else.
        system_record: `SYSTEM-REC`, the second linkage parameter. `Scycle`
            [copybooks/wssystem.cob:L63] is read by both passes; `Date-Form`
            [copybooks/wssystem.cob:L128] is read AND written by the two date sections.
        to_day: `01 to-day pic x(10).` [general/gl070.cbl:L243], the third linkage
            parameter, in DD/MM/CCYY form.
        file_defs: `01 File-Defs.` [copybooks/wsnames.cob:L13], the fourth.
        file_access: `01 File-Access.` [copybooks/wsfnctn.cob:L22], carried in WORKING-
            STORAGE by this program because it copies the copybook
            [general/gl070.cbl:L126].
        dal_common: `01 ACAS-DAL-Common-data.` [copybooks/Test-Data-Flags.cob:L6],
            likewise [general/gl070.cbl:L154].
        batch: `01 WS-Batch-Record.` [copybooks/wsbatch.cob:L13], from
            [general/gl070.cbl:L127]. Filled by every batch read.
        posting: `01 WS-Posting-Record.` [copybooks/wspost.cob:L12], from
            [general/gl070.cbl:L128]. Filled by every posting read.
        pre_trans_record: `01 pre-trans-record.` [general/gl070.cbl:L108], the FILE
            SECTION record AREA.
        maps03_ws: `01 maps03-ws.` [copybooks/wsmaps03.cob:L6], from
            [general/gl070.cbl:L125] - the date module's linkage block.
        ws: `01 ws-date-formats.` [general/gl070.cbl:L173] plus `01 ws-Test-Date`
            [general/gl070.cbl:L172], the working storage the two date sections write
            `ws-date` into.
        detector: `03 a pic 9.` [general/gl070.cbl:L157]. THE flag phase 1 raises and
            `menu-input2.` turns into the abort. Carried as a plain `int`.
        work_files: the cycle's three work sequences. `pre-trans` is the one this
            program opens, writes and closes.
        batch_ctx: the linkage a `GL-Batch-*` facade verb needs.
        posting_ctx: the linkage a `GL-Posting-*` facade verb needs.
        ledger_label: `03 l6-ledger pic x(4).` [general/gl070.cbl:L221]. A PRINT FIELD,
            retained for one reason only.
        status_label: `03 l6-status pic x(9).` [general/gl070.cbl:L223]. Retained for
            the same carry-over reason [general/gl070.cbl:L387-L398].
        lin: `03 Lin pic 99.` [copybooks/wsfnctn.cob:L29], the report's cursor line.
        ws_21_lines: `03 ws-21-lines binary-char unsigned value zero.`
            [general/gl070.cbl:L165], the other operand of that transfer, and the
            subject of question Q-70e.
    """

    ws_calling_data: WsCallingData
    system_record: SystemRecord
    to_day: str
    file_defs: FileDefs
    file_access: FileAccess
    dal_common: AcasDalCommonData
    batch: GlBatchRecord
    posting: WsPostingRecord
    pre_trans_record: PreTransRecord
    maps03_ws: Maps03Ws
    ws: WsDateFormats
    detector: int
    work_files: GeneralLedgerWorkFiles
    batch_ctx: facade.FacadeContext
    posting_ctx: facade.FacadeContext
    ledger_label: str = ""
    status_label: str = ""
    lin: int = 0
    ws_21_lines: int = 0


def _at_end(store: _WorkingStorage) -> bool:
    """`if fs-reply = 10` - the at-end test, spelled once.

    The identical statement appears four times, once after each read:
    [general/gl070.cbl:L309] and [general/gl070.cbl:L348] over the batch file,
    [general/gl070.cbl:L454] over it again and [general/gl070.cbl:L487] over the posting
    file.

    Args:
        store: the run's working storage, whose one `File-Access` holds the reply the
            last verb left there.

    Returns:
        True when the last verb reported end of file.
    """
    return store.file_access.fs_reply == FsReply.END_OF_FILE


def _cycle_differs(store: _WorkingStorage) -> bool:
    """`if bcycle not = scycle` - THE ACCOUNTING-CYCLE FILTER.

    Both are scale-zero integers, and the comparison is routed through
    `acas_posting.cobol.arithmetic.compare` rather than done here, because this module
    holds no numeric primitives of its own.

    Args:
        store: the run's working storage.

    Returns:
        True when the batch belongs to some other cycle and must be skipped.
    """
    return (
        arithmetic.compare(
            store.batch.bcycle, store.system_record.system_data_block.scycle
        )
        != 0
    )


def _post_key_is_zero(store: _WorkingStorage) -> bool:
    """`if WS-Post-Key = zero` - the unset-key filter [general/gl070.cbl:L490-L491].

    A GROUP COMPARED WITH `ZERO` IS A BYTE COMPARISON, measured on the compiled oracle
    (GnuCOBOL 3.2.0) against `WS-Post-Key` as [copybooks/wspost.cob:L14-L16] declares it:
    a group of ten SPACES is NOT zero, a group of ten `0` characters IS. A group has no
    numeric reading, so the comparison is against the character `0` repeated across its
    width - which is each item's zero image, tested here item by item.

    Args:
        store: the run's working storage.

    Returns:
        True when the posting record's key is entirely the character zero, i.e. the
            record is an unused slot and is to be skipped.
    """
    key = store.posting.ws_post_key
    return (
        arithmetic.compare_zoned_display_fields(
            key.batch,
            _ZERO,
            left_field=_POST_KEY["Batch"],
            right_field=_POST_KEY["Batch"],
        )
        == 0
        and arithmetic.compare_zoned_display_fields(
            key.post_number,
            _ZERO,
            left_field=_POST_KEY["Post-Number"],
            right_field=_POST_KEY["Post-Number"],
        )
        == 0
    )


def _batch_is_not_the_one_being_processed(store: _WorkingStorage) -> bool:
    """`if batch not = WS-Batch-Nos` [general/gl070.cbl:L492-L493] - the batch gate.

    TWO SAME-PICTURE DISPLAY FIELDS COMPARE BYTE-WISE, measured on the compiled oracle;
    `arithmetic.compare_zoned_display_fields` carries the measurement. It matters here
    more than anywhere: `Batch` [copybooks/wspost.cob:L15] arrives from the bridge
    holding bytes its picture cannot produce (ANOMALY N-KEY), and a field sweep inside
    the compiled probe matched NONE of the 100,000 values a `pic 9(5)` batch number can
    take. So this guard discards every posting the database returns, no work record is
    written, and `gl071` and `gl072` receive nothing - which is the frozen behaviour the
    anomaly register records and `pretrans.tmp` being zero bytes measured.

    Args:
        store: the run's working storage.

    Returns:
        True when the posting belongs to some other batch, and so is passed over.
    """
    return (
        arithmetic.compare_zoned_display_fields(
            store.posting.ws_post_key.batch,
            store.batch.ws_batch_key.ws_batch_nos,
            left_field=_POST_KEY["Batch"],
            right_field=_BATCH_NOS,
        )
        != 0
    )


def _init01(store: _WorkingStorage) -> None:
    """`init01 section.` - the program's entry, minus the terminal.

    [general/gl070.cbl:L251]. Ten statements, of which SEVEN are screen setup and are
    recorded as omissions 2 and 3 rather than reproduced.

    Args:
        store: the run's working storage.
    """
    # 254 accept ws-env-lines from lines. 255-259 if ws-env-lines < 24 move 24 ... else
    # move ws-env-lines ... 260 subtract 1 from ws-lines giving ws-23-lines.

    _zz070_convert_date(store)


    # 272 move 1 to File-Key-No. Question Q-70a: probably inert, because every facade
    # dispatch paragraph sets the key number itself immediately before its `CALL`
    # [copybooks/Proc-ACAS-FH-Calls.cob:L52].
    store.file_access.logging_data.file_key_no = cobol_move.move(
        _FILE_KEY_NO_PRIMARY, _FILE_KEY_NO
    )

    # 274 menu-input. FALL-THROUGH, not a `perform`.
    _init01_menu_input(store)

    _init01_menu_input2(store)

    _init01_main_exit(store)


def _init01_menu_input(store: _WorkingStorage) -> None:
    """`menu-input.` - the screen banner, and nothing else.

    [general/gl070.cbl:L274]. Three `display` statements [general/gl070.cbl:L277-L279]
    and no other statement of any kind, so the whole paragraph is presentation.

    Args:
        store: the run's working storage; `ws.ws_date` supplies the run date the third
            display shows.
    """
    # 277  display  prog-name at 0101 with foreground-color 2 erase eos.
    # 278  display  "Transaction Posting" at 0132  with foreground-color 2.
    # 279  display  ws-date at 0171 with foreground-color 2.
    #      Screen positions, colours and the `erase eos` clause are dropped;
    #      omission 1.
    #  THE RUN DATE IS NOT IN THE RECORD. The first two displays are the
    #  program's own identity and the phase label Agent Action Plan section 0.2.1.1
    #  cites as the program labelling its own work, and both are constants. The third
    #  [:L279] shows `ws-date`, which is the posting date this run stamps into every
    #  record it writes - a date with business meaning, which the safe-event schema in
    #  `acas_posting/dal/status.py` excludes (CWE-532). The date is an INPUT the
    #  operator supplied on the command line, so it is already known wherever the run
    #  was started, and `clock.py` pins it so no record is needed to reconstruct it.
    _LOG.info("%s  Transaction Posting", _PROG_NAME)
    del store


def _init01_menu_input2(store: _WorkingStorage) -> None:
    """`menu-input2.` - THE PHASE DRIVER AND THE ABORT.

    [general/gl070.cbl:L157] carries no VALUE clause, and `move zero to a`
    [general/gl070.cbl:L284] is what makes the detector per-run rather than per-load.

    Args:
        store: the run's working storage. `ws_calling_data.ws_term_code` is written here
            on the abort path AND NOWHERE ELSE in this module.
    """
    store.detector = _DETECTOR_CLEAR

    _LOG.info("Phase - 1.  Batch Check")

    _gl071a(store)

    if store.detector == _DETECTOR_RAISED:
        _gl060a(store)

        # 289 move 5 to ws-term-code THE ABORT.
        store.ws_calling_data.ws_term_code = _WS_TERM_CODE_OPEN_BATCH_FOUND
        #  NO LOG RECORD HERE, AND THAT IS DELIBERATE - two reasons, either of
        #  which is sufficient.
        #
        #  1. THE FROZEN SOURCE IS SILENT. `move 5 to ws-term-code` at
        #     [general/gl070.cbl:L288] carries no `display` of any kind; the
        #     assignment and the `go to main-exit` at [:L289] are the whole of it.
        #     A record invented here would be a diagnostic the compiled program
        #     does not produce (rule R-4).
        #  2. THE ABORT IS ALREADY REPORTED, ONCE, AT THE LAYER THAT DECIDES IT.
        #     `acas_posting/cli/gl_post_cycle.py` evaluates the gate the menu
        #     evaluates [general/general.cbl:L810-L811] and reports the whole
        #     consequence there - that `gl071` and `gl072` will not run - which is
        #     more than this paragraph knows. Reporting it in both places produced
        #     two records for one event.
        #
        #  The scycle the open batch was found in is not reported anywhere: it is
        #  business data (Agent Action Plan section 0.6.4's cycle filter), and the
        #  safe-event schema in `dal/status.py` excludes it.

        return

    _LOG.info("Phase - 2.  Transaction Pre-process")

    _gl071b(store)


def _init01_main_exit(store: _WorkingStorage) -> None:
    """`main-exit.` - `goback.`

    [general/gl070.cbl:L295], whose whole body is `goback.` [general/gl070.cbl:L298].
    The FIRST of the five paragraphs in this file called `main-exit.`, and the only one
    that ends the PROGRAM rather than a section: the other four are `exit section.`.

    Args:
        store: the run's working storage. Nothing further is written to it.
    """
    del store
    return


def _gl071a(store: _WorkingStorage) -> None:
    """`gl071a section.` - phase 1, the batch check.

    THIS IS A DETECTOR, NOT A REJECTOR, and that is the whole difference between this
    pass and phase 2's [general/gl070.cbl:L460-L463].

    Args:
        store: the run's working storage. `detector` is the only thing this section can
            change.
    """
    # 303 perform GL-Batch-Open-Input. *> open input batch-file. `GL-Batch-Open-Input`
    # [copybooks/Proc-ACAS-FH-Calls.cob:L424-L427] sets `fn-open` and `fn-input` and
    # performs the `acas007` dispatch.
    facade.gl_batch_open_input(store.batch_ctx)

    _gl071a_loop(store)

    _gl071a_main_exit(store)


def _gl071a_loop(store: _WorkingStorage) -> None:
    """`loop.` in `gl071a` - read every batch, and raise the flag on an open one.

    THREE TRANSFERS, TWO CLASSES. The at-end is Class 2 - `end-run.`
    [general/gl070.cbl:L318] is followed by REAL WORK, the close at
    [general/gl070.cbl:L321], so the transformation is a `break` PLUS that work placed
    after the loop, never a `break` alone.

    Args:
        store: the run's working storage.
    """
    while True:
        facade.gl_batch_read_next(store.batch_ctx)

        if _at_end(store):
            break

        if _cycle_differs(store):
            continue

        # 314 if status-open 315 move 1 to a.
        if condition_names.is_status_open(store.batch.batch_status):
            store.detector = _DETECTOR_RAISED

        # 316 go to loop. GO TO class 1, and UNCONDITIONAL.
        continue

    _gl071a_end_run(store)


def _gl071a_end_run(store: _WorkingStorage) -> None:
    """`end-run.` in `gl071a` - close the batch file.

    [general/gl070.cbl:L318]. One statement, `perform GL-Batch-Close.`
    [general/gl070.cbl:L321], and it is exactly the "real work" that makes the at-end
    transfer a Class-2 `break` plus a post-loop block rather than a bare `break`. Agent
    Action Plan section 0.6.3, verbatim.

    Args:
        store: the run's working storage.
    """
    facade.gl_batch_close(store.batch_ctx)


def _gl071a_main_exit(store: _WorkingStorage) -> None:
    """`main-exit. exit section.` in `gl071a`.

    [general/gl070.cbl:L323]. The SECOND of the five `main-exit.` paragraphs, and the
    first of the four that end a SECTION rather than the program.

    Args:
        store: the run's working storage, unchanged here.
    """
    del store
    return


def _gl060a(store: _WorkingStorage) -> None:
    """`gl060a section.` - the Batch Status Report, shown when phase 1 aborts.

    [general/gl070.cbl:L325]. Performed from exactly one place,
    [general/gl070.cbl:L288], and only when the detector was raised. It re-walks the
    batch file and reports every batch of the current cycle so the operator can see
    which one is open.

    Args:
        store: the run's working storage.
    """
    _init01_menu_input(store)

    _zz070_convert_date(store)

    # 331  move     ws-date to l3-date.
    # 332  display  line-1 at 0301 with foreground-color 2.
    # 333  move     scycle  to  l3-cycle.
    # 334  move     1      to  y.
    # 335  move     y      to  l1-page.
    # 336  display  l3-lit1 at 0301 with foreground-color 2.
    # 337  display  l3-cycle at 0309 with foreground-color 2.
    # 338  display  line-4 at 0501 with foreground-color 2.
    # 339  display  line-5 at 0601 with foreground-color 2.
    #      The report's headings and its page number: presentation throughout -
    #      omissions 1, 5 and 6.
    #  NO RECORDS HERE. These are the BATCH STATUS REPORT'S OWN HEADINGS - a
    #  title line, a page number and two lines of column captions - and Agent Action
    #  Plan section 0.2.2 puts "report formatting beyond database effects" out of
    #  scope. Section 0.3.4 converts a DIAGNOSTIC display into a record; a column
    #  ruler is not a diagnostic, and reproducing it as three log lines re-created the
    #  report at a destination the plan does not ask for. The title line additionally
    #  named the accounting cycle and the run date, neither of which the safe-event
    #  schema admits. The report's DATABASE effect is nil - `gl060a` opens the batch
    #  file for input, reads and closes - so nothing is lost.

    # 340 move 7 to lin. RETAINED, not omitted: `lin` is one operand of the preserved
    # control transfer at [general/gl070.cbl:L413-L414].
    store.lin = _REPORT_FIRST_BODY_LINE


    facade.gl_batch_open_input(store.batch_ctx)

    _gl060a_loop(store)

    _gl060a_main_exit(store)


def _gl060a_loop(store: _WorkingStorage) -> None:
    """`loop.` in `gl060a` - report one batch per pass.

    `stored`, then `posted`, then `proofed`, then `entered`
    [copybooks/wsbatch.cob:L36-L39] - latest lifecycle event first, so the column shows
    the most recent thing that happened to the batch. The first three each end in `go to
    next-1` [general/gl070.cbl:L366], [general/gl070.cbl:L371],
    [general/gl070.cbl:L376].

    Args:
        store: the run's working storage.
    """
    while True:
        facade.gl_batch_read_next(store.batch_ctx)

        # 348 if fs-reply = 10 349 go to end-report.
        if _at_end(store):
            break

        if _cycle_differs(store):
            continue

        # 354 if gl-batch 355 move " G/L" to l6-ledger. 356 if pl-batch 357 move " P/L"
        # to l6-ledger.
        ledger_label = store.ledger_label
        if condition_names.is_gl_batch(store.batch.ws_batch_key.ws_ledger):
            ledger_label = _LEDGER_LABEL_GL
        if condition_names.is_pl_batch(store.batch.ws_batch_key.ws_ledger):
            ledger_label = _LEDGER_LABEL_PL
        if condition_names.is_sl_batch(store.batch.ws_batch_key.ws_ledger):
            ledger_label = _LEDGER_LABEL_SL
        store.ledger_label = ledger_label

        # 361 move WS-Batch-Nos to l6-batch. Presentation; the value is logged by
        # `_gl060a_next_1` from the record itself rather than through an edited `pic
        # z(4)9bb` field.

        if arithmetic.compare(store.batch.dates.stored, _ZERO) != 0:
            store.maps03_ws.u_bin = cobol_move.move(
                store.batch.dates.stored, _U_BIN
            )
            _zz060_convert_date(store)
        elif arithmetic.compare(store.batch.dates.posted, _ZERO) != 0:
            store.maps03_ws.u_bin = cobol_move.move(
                store.batch.dates.posted, _U_BIN
            )
            _zz060_convert_date(store)
        elif arithmetic.compare(store.batch.dates.proofed, _ZERO) != 0:
            store.maps03_ws.u_bin = cobol_move.move(
                store.batch.dates.proofed, _U_BIN
            )
            _zz060_convert_date(store)
        # 378 if entered not = zero 379 move entered to u-bin 380 perform zz060-Convert-
        # Date.
        elif arithmetic.compare(store.batch.dates.entered, _ZERO) != 0:
            store.maps03_ws.u_bin = cobol_move.move(
                store.batch.dates.entered, _U_BIN
            )
            _zz060_convert_date(store)

        if _gl060a_next_1(store):
            continue

        if _gl060a_screen_option(store):
            break

        continue

    # 435 end-report. THE POST-LOOP BLOCK the two Class-2 transfers above break to.
    _gl060a_end_report(store)


def _gl060a_next_1(store: _WorkingStorage) -> bool:
    """`next-1.` in `gl060a` - print one batch's two report lines.

    Presentation from beginning to end, with ONE retained value - `lin`
    [general/gl070.cbl:L411] - because it is an operand of the control transfer this
    function reports on.

    Returns:
        `True` when the loop is to be re-entered without prompting, i.e. when `lin <
            ws-21-lines` [general/gl070.cbl:L413].

    Args:
        store: the run's working storage.
    """

    if condition_names.is_status_open(store.batch.batch_status):
        store.status_label = _STATUS_LABEL_OPEN

    if condition_names.is_status_closed(
        store.batch.batch_status
    ) and condition_names.is_waiting(store.batch.cleared_status):
        store.status_label = _STATUS_LABEL_WAITING

    if condition_names.is_status_closed(
        store.batch.batch_status
    ) and condition_names.is_processed(store.batch.cleared_status):
        store.status_label = _STATUS_LABEL_PROCESSED

    if condition_names.is_status_closed(
        store.batch.batch_status
    ) and condition_names.is_archived(store.batch.cleared_status):
        store.status_label = _STATUS_LABEL_ARCHIVED

    # 400      move     items  to  l6-items l7-items.
    # 401      move     input-gross  to  l6-gross.
    # 402      move     input-vat    to  l6-vat.
    # 403      move     actual-gross  to  l7-gross.
    # 404      move     actual-vat    to  l7-vat.
    # 406      add      0100 curs giving curs2.
    # 408      display  line-6 at curs2 with foreground-color 2.
    # 409      add      1 to lin2.
    # 410      display  line-7 at curs2 with foreground-color 2.
    #      The two printed lines. `line-6` carries the ENTERED controls and
    #      `line-7` the ACTUAL ones [general/gl070.cbl:L219-L234], which is the
    #      whole point of the report: the operator compares the two.
    #      `curs2 = curs + 100` moves the cursor down one line before each, and
    #      the cursor arithmetic is dropped with the rest of the cursor state.
    #  NO RECORDS HERE, AND THE LABEL COMPUTATION ABOVE IS PRESERVED. The two
    #  records that stood for these displays were the report BODY, and between them
    #  they named the ledger label, the BATCH NUMBER, the run date, the item count and
    #  four monetary control totals - business keys and accounting values, which the
    #  safe-event schema forbids outright (CWE-532). Report formatting beyond a
    #  database effect is out of scope (section 0.2.2), and every figure they carried
    #  is in `GLBATCH-REC`, which is what `harness/diff_states.py` compares.
    #  `store.ledger_label` and `store.status_label` are still computed, because the
    #  frozen `move`s that compute them are statements of the program.

    # 411 add 3 to lin. Two printed lines plus a blank. Plain integer addition on a `pic
    # 99` screen-position field, not on a posted figure.
    store.lin = store.lin + _REPORT_LINES_PER_BATCH

    # 413 if lin < ws-21-lines 414 go to loop. Reported to the caller.
    return arithmetic.compare(store.lin, store.ws_21_lines) < 0


def _gl060a_screen_option(store: _WorkingStorage) -> bool:
    """`screen-option.` in `gl060a` - the paging prompt.

    ANSWERING QUESTION Q-70d: an early "X" exit changes nothing a table dump can see.
    Both branches converge on `GL-Batch-Close` [general/gl070.cbl:L440].

    Returns:
        `True` if the report is to stop early, i.e. the operator typed "X"; `False` to
            clear the page and carry on. Always `False` headless.

    Args:
        store: the run's working storage.
    """
    # 421 accept ws-reply at line ws-22-lines col 46 with foreground-color 6. Omission
    # 4: the terminal read is dropped.


    _gl060a_screen_clear(store)
    return False


def _gl060a_screen_clear(store: _WorkingStorage) -> None:
    """`screen-clear.` in `gl060a` - start a new report page.

    THE CURSOR RESET IS RETAINED, THE ERASE IS NOT. `lin` going back to seven is the
    whole of this paragraph's non-presentation effect, because it is what makes the page
    test at [general/gl070.cbl:L413] able to be true again.

    Args:
        store: the run's working storage.
    """
    store.lin = _REPORT_FIRST_BODY_LINE


def _gl060a_end_report(store: _WorkingStorage) -> None:
    """`end-report.` in `gl060a` - close the batch file.

    Args:
        store: the run's working storage.
    """

    facade.gl_batch_close(store.batch_ctx)


def _gl060a_main_exit(store: _WorkingStorage) -> None:
    """`main-exit.` in `gl060a` - the section's trailing exit.

    Args:
        store: the run's working storage, unused.
    """
    del store
    return


def _gl071b(store: _WorkingStorage) -> None:
    """`gl071b section.` - phase 2, transaction pre-process.

    THIS IS NOT PHASE 1 WITH EXTRA CONDITIONS, and the difference is the whole reason
    the two passes exist. Phase 1 used `status-open` as a DETECTOR.

    Args:
        store: the run's working storage.
    """
    store.work_files.pre_trans.open_output()

    facade.gl_batch_open_input(store.batch_ctx)

    _gl071b_loop(store)

    _gl071b_main_exit(store)


def _gl071b_loop(store: _WorkingStorage) -> None:
    """`loop.` in `gl071b` - pre-process one accepted batch per pass.

    THE REJECTOR IS THREE CONDITIONS JOINED BY `OR`, so ANY ONE of them skips the batch.

    Args:
        store: the run's working storage.
    """
    while True:
        facade.gl_batch_read_next(store.batch_ctx)

        # 454 if fs-reply = 10 455 go to end-run.
        if _at_end(store):
            break

        if _cycle_differs(store):
            continue

        if (
            condition_names.is_status_open(store.batch.batch_status)
            or not condition_names.is_waiting(store.batch.cleared_status)
            or not condition_names.is_gl_batch(
                store.batch.ws_batch_key.ws_ledger
            )
        ):
            continue

        _gl071b_pre_process(store)

        # 466 perform GL-Posting-Close. *> close posting-file. The outer half of the
        # asymmetric pair - see this function's docstring.
        facade.gl_posting_close(store.posting_ctx)

        continue

    _gl071b_end_run(store)


def _gl071b_end_run(store: _WorkingStorage) -> None:
    """`end-run.` in `gl071b` - close the work sequence and the batch file.

    The trailing comment on [general/gl070.cbl:L472] reads `*> batch-file`, which is a
    stale annotation - the statement closes `pre-trans`, and the batch file is closed by
    the NEXT line. Recorded rather than tidied.

    Args:
        store: the run's working storage.
    """
    store.work_files.pre_trans.close()

    facade.gl_batch_close(store.batch_ctx)


def _gl071b_main_exit(store: _WorkingStorage) -> None:
    """`main-exit.` in `gl071b` - the section's trailing exit.

    Args:
        store: the run's working storage, unused.
    """
    del store
    return


def _gl071b_pre_process(store: _WorkingStorage) -> None:
    """`gl071b-pre-process section.` - explode one batch into work records.

    THIS IS THE HEART OF PHASE 2. Each posting record of the batch becomes TWO OR THREE
    `pre-trans` records: a debit leg, a credit leg, and - only when the posting carries
    VAT - a VAT leg.

    Args:
        store: the run's working storage.
    """
    # 480 move WS-Batch-Nos to pre-batch. QUESTION Q-70b: THIS STORE IS INERT.
    store.pre_trans_record.pre_batch = cobol_move.move(
        store.batch.ws_batch_key.ws_batch_nos,
        _PRE["pre_batch"],
        sending_field=_BATCH_NOS,
    )

    facade.gl_posting_open_input(store.posting_ctx)

    _gl071b_pre_process_loop(store)

    _gl071b_pre_process_main_exit(store)


def _gl071b_pre_process_loop(store: _WorkingStorage) -> None:
    """`loop.` in `gl071b-pre-process` - explode one posting per pass.

    THE THREE `write pre-trans-record` STATEMENTS - [general/gl070.cbl:L508],
    [general/gl070.cbl:L519] and [general/gl070.cbl:L532] - ALL NAME THE SAME RECORD
    AREA. In COBOL that is unremarkable.

    Args:
        store: the run's working storage.
    """
    while True:
        facade.gl_posting_read_next(store.posting_ctx)

        # 487 if fs-reply = 10 488 go to main-exit. GO TO class 3 - `return`, NOT
        # `break`.
        if _at_end(store):
            return

        if _post_key_is_zero(store):
            continue

        # 492 if batch not = WS-Batch-Nos 493 go to loop. GO TO class 1. A STORAGE
        # comparison, measured - see `_batch_is_not_the_one_being_processed`.
        if _batch_is_not_the_one_being_processed(store):
            continue


        store.pre_trans_record.pre_batch = cobol_move.move(
            store.posting.ws_post_key.batch,
            _PRE["pre_batch"],
            sending_field=_POST_KEY["Batch"],
        )

        store.pre_trans_record.pre_post = cobol_move.move(
            store.posting.ws_post_key.post_number,
            _PRE["pre_post"],
            sending_field=_POST_KEY["Post-Number"],
        )

        # 497 move post-code in WS-Posting-Record to pre-code. ANOMALY A-21
        # [general/gl070.cbl:L497] - field-name collision across three posting copybooks
        # forces a QUALIFIED reference.
        store.pre_trans_record.pre_code = cobol_move.move(
            store.posting.post_code,
            _PRE["pre_code"],
            sending_field=_POST["Post-Code"],
        )

        store.pre_trans_record.pre_date = cobol_move.move(
            store.posting.post_date,
            _PRE["pre_date"],
            sending_field=_POST["Post-Date"],
        )

        store.pre_trans_record.pre_legend = cobol_move.move(
            store.posting.post_legend,
            _PRE["pre_legend"],
            sending_field=_POST["Post-Legend"],
        )


        store.pre_trans_record.pre_ac = cobol_move.move(
            store.posting.post_dr,
            _PRE["pre_ac"],
            sending_field=_POST["Post-DR"],
        )

        store.pre_trans_record.pre_pc = cobol_move.move(
            store.posting.dr_pc,
            _PRE["pre_pc"],
            sending_field=_POST["DR-PC"],
        )

        # 503 if post-vat-side = "CR" 504 add post-amount vat-amount giving pre-amount
        # 505 else 506 move post-amount to pre-amount.
        if store.posting.post_vat_side == _VAT_SIDE_CREDIT:
            store.pre_trans_record.pre_amount = arithmetic.add_giving(
                store.posting.post_amount,
                store.posting.vat_amount,
                receiving=_PRE["pre_amount"],
            )
        else:
            store.pre_trans_record.pre_amount = cobol_move.move(
                store.posting.post_amount,
                _PRE["pre_amount"],
                sending_field=_POST["Post-Amount"],
            )

        store.work_files.pre_trans.write(store.pre_trans_record)


        store.pre_trans_record.pre_ac = cobol_move.move(
            store.posting.post_cr,
            _PRE["pre_ac"],
            sending_field=_POST["Post-CR"],
        )

        store.pre_trans_record.pre_pc = cobol_move.move(
            store.posting.cr_pc,
            _PRE["pre_pc"],
            sending_field=_POST["CR-PC"],
        )

        # 512 if post-vat-side = "DR" 513 add post-amount vat-amount giving pre-amount
        # 514 else 515 move post-amount to pre-amount.
        if store.posting.post_vat_side == _VAT_SIDE_DEBIT:
            store.pre_trans_record.pre_amount = arithmetic.add_giving(
                store.posting.post_amount,
                store.posting.vat_amount,
                receiving=_PRE["pre_amount"],
            )
        else:
            store.pre_trans_record.pre_amount = cobol_move.move(
                store.posting.post_amount,
                _PRE["pre_amount"],
                sending_field=_POST["Post-Amount"],
            )

        # 517 multiply pre-amount by -1 giving pre-amount. UNCONDITIONAL, and the only
        # unconditional negation in the program.
        store.pre_trans_record.pre_amount = arithmetic.multiply_by_giving(
            store.pre_trans_record.pre_amount,
            -1,
            _PRE["pre_amount"],
        )

        store.work_files.pre_trans.write(store.pre_trans_record)


        # 521 if vat-ac of WS-Posting-Record = zero 522 or vat-amount = zero 523 go to
        # loop. GO TO class 1 - and note what it skips.
        if (
            arithmetic.compare(store.posting.vat_ac, _ZERO) == 0
            or arithmetic.compare(store.posting.vat_amount, _ZERO) == 0
        ):
            continue

        # 525 move vat-ac of WS-Posting-Record to pre-ac. ANOMALY A-21
        # [general/gl070.cbl:L525] - third and last site of the collision, again with
        # the `of` qualifier. Reproduced deliberately per.
        store.pre_trans_record.pre_ac = cobol_move.move(
            store.posting.vat_ac,
            _PRE["pre_ac"],
            sending_field=_POST["Vat-AC"],
        )

        store.pre_trans_record.pre_pc = cobol_move.move(
            store.posting.vat_pc,
            _PRE["pre_pc"],
            sending_field=_POST["Vat-PC"],
        )

        store.pre_trans_record.pre_amount = cobol_move.move(
            store.posting.vat_amount,
            _PRE["pre_amount"],
            sending_field=_POST["Vat-Amount"],
        )

        # 529 if post-vat-side = "CR" 530 multiply pre-amount by -1 giving pre-amount.
        # CONDITIONAL, unlike the credit leg's flip at [general/gl070.cbl:L517].
        if store.posting.post_vat_side == _VAT_SIDE_CREDIT:
            store.pre_trans_record.pre_amount = arithmetic.multiply_by_giving(
                store.pre_trans_record.pre_amount,
                -1,
                _PRE["pre_amount"],
            )

        store.work_files.pre_trans.write(store.pre_trans_record)

        continue


def _gl071b_pre_process_main_exit(store: _WorkingStorage) -> None:
    """`main-exit.` in `gl071b-pre-process` - the section's trailing exit.

    [general/gl070.cbl:L535]. The FIFTH and last paragraph in this file named `main-
    exit.` It carries no statement other than `exit section.`, which is precisely why
    [general/gl070.cbl:L487-L488] is a Class-3 `return` and not a Class-2 `break`.

    Args:
        store: the run's working storage, unused.
    """
    del store
    return


def _zz060_convert_date(store: _WorkingStorage) -> None:
    """`zz060-Convert-Date section.` - a binary date, reformatted for the report.

    THE BODY IS CONSOLIDATED, NOT REWRITTEN. This section is repeated near-identically
    in six of the in-scope programs, and its body differs between them by ONE TOKEN: the
    name of the wrapper it performs.

    Args:
        store: the run's working storage. `maps03_ws.u_bin` is the input; `ws.ws_date`
            and `system_record`'s `Date-Form` are the outputs.
    """
    # 547 perform maps03. 548 if u-date = spaces 549 move spaces to ws-Date 550 go to
    # zz060-Exit.
    store.system_record.system_data_block.date_form = (
        dates_zz060_convert_date(
            store.ws,
            store.maps03_ws,
            store.system_record.system_data_block.date_form,
            wrapper=_maps03,
        )
    )


def _zz070_convert_date(store: _WorkingStorage) -> None:
    """`zz070-Convert-Date section.` - the run date, reformatted.

    [general/gl070.cbl:L573]. Performed twice: [general/gl070.cbl:L270] in
    `init01` and [general/gl070.cbl:L330] at the head of the open-batch report.
    Input is `to-day`, output is `ws-date`.

    IT TOO MUTATES `Date-Form` [general/gl070.cbl:L583-L584], and the store back
    into the system record is made here for the same reason as in `zz060`. THIS
    IS WHY [general/gl070.cbl:L270] IS PRESERVED even though the value it
    produces goes only to a print field: the conversion's SIDE EFFECT on
    `SYSTEM-REC` outlives the report line, and it happens on EVERY run of this
    program whose system record still carries a zero `Date-Form`.

    NO CLOCK IS READ, here or anywhere in this program. `to-day` is the third
    linkage parameter [general/gl070.cbl:L243], and the menu shell sets it from
    the STORED `Run-Date` rather than from a clock - `move run-date to u-bin` /
    `call "maps04"` / `move u-date to to-day` [general/general.cbl:L462-L465].
    The frozen call chain does hold FOURTEEN ambient date and time reads, all of
    them in out-of-scope menu shells or in the date-service copybook those shells
    COPY, as the census in `acas_posting/clock.py` records; none is on the path
    that supplies this parameter. This migration receives it as an argument
    (rule R-6).

    Args:
        store: the run's working storage. `to_day` is the input; `ws.ws_date` and
            `system_record`'s `Date-Form` are the outputs.
    """
    # 581 move to-day to ws-date. 583 if Date-Form = zero 584 move 1 to Date-Form. 585
    # if Date-UK 586 go to zz070-Exit.
    store.system_record.system_data_block.date_form = (
        dates_zz070_convert_date(
            store.ws,
            store.to_day,
            store.system_record.system_data_block.date_form,
        )
    )


def _maps03(maps03_ws: Maps03Ws) -> None:
    """`maps03 section.` - the wrapper around the date module.

    ANOMALY A-22 [general/gl070.cbl:L603-L609] - THE WRAPPER IS NAMED AFTER THE section
    is `maps03`, taking its name from `wsmaps03.cob` [general/gl070.cbl:L125], which
    declares the linkage record it passes.

    Args:
        maps03_ws: `01 maps03-ws.` [copybooks/wsmaps03.cob:L6], mutated in place,
            exactly as a COBOL `CALL ... USING` mutates its argument.
    """
    dates_maps03(maps03_ws)


def run(
    ws_calling_data: WsCallingData,
    system_record: SystemRecord,
    to_day: str,
    file_defs: FileDefs,
    *,
    work_files: GeneralLedgerWorkFiles | None = None,
    file_access: FileAccess | None = None,
    dal_common: AcasDalCommonData | None = None,
    states: Mapping[str, object] | None = None,
) -> GeneralLedgerWorkFiles:
    """Run `gl070` - General Ledger phase 1 batch check and phase 2 pre-process.

    [general/gl070.cbl:L245-L248].

    Args:
        ws_calling_data: `01 WS-Calling-Data.` [copybooks/wscall.cob:L6]. THE ABORT IS
            DELIVERED HERE, in `WS-Term-Code` [copybooks/wscall.cob:L10].
        system_record: `SYSTEM-REC`. `Scycle` [copybooks/wssystem.cob:L63] is read by
            all three passes over the batch file; `Date-Form`
            [copybooks/wssystem.cob:L128] is read and, when zero, WRITTEN.
        to_day: `01  to-day  pic x(10).` [general/gl070.cbl:L243] - the run date
            in DD/MM/CCYY form, supplied by the caller. No clock is read.
        file_defs: `01  File-Defs.` [copybooks/wsnames.cob:L13].
        work_files: the cycle's work sequences. Defaults to a fresh set, which is
            what a standalone run of this program wants; a caller running the
            whole cycle passes the same set it will hand to `gl071`, because
            `pre-trans` is how the two programs communicate.
        file_access: `01  File-Access.` [copybooks/wsfnctn.cob:L22]. Defaults to
            a fresh record. ONE record serves both tables, because the frozen
            program copies the copybook once [general/gl070.cbl:L126].
        dal_common: `01  ACAS-DAL-Common-data.`
            [copybooks/Test-Data-Flags.cob:L6], from
            [general/gl070.cbl:L154]. Defaults to a fresh record, whose
            `SW-Testing` carries the copybook's own `value 1`.
        states: the data-access layer's cursor states, forwarded verbatim to the
            posting handler. `None` leaves the handler's own default in force.
            The BATCH handler takes no such argument, so it is not offered one.

    Note:
        THERE IS NO `transport` PARAMETER, AND ITS ABSENCE IS DELIBERATE.
        Accepting one here could only forward it to the POSTING context, because
        `acas007` takes no such argument - so half of this program's two tables
        would run under the caller's declaration and half under whatever the
        data-access layer defaulted to. The connection policy is one deployment
        decision shared by every handler connection, so it belongs
        to the deployment and is installed once at the entry point
        through `acas_posting.dal.connection.set_connection_policy`; every open
        this program causes then resolves to that one policy, both tables alike.
        A program module has no business declaring it: the layering of Agent
        Action Plan section 0.4.3 does not admit `dal.connection` here, and the
        frozen program has no notion of transport at all
        [copybooks/mysql-procedures.cpy:L72-L77].

    Returns:
        The work-file set, so that a caller which let the default be created can hand
            the populated `pre-trans` sequence to `gl071`.
    """
    resolved_work_files = (
        general_ledger_work_files() if work_files is None else work_files
    )
    resolved_file_access = FileAccess() if file_access is None else file_access
    resolved_dal_common = (
        AcasDalCommonData() if dal_common is None else dal_common
    )

    # `01 WS-Batch-Record.` and `01 WS-Posting-Record.` are WORKING-STORAGE of the
    # frozen program [general/gl070.cbl:L127-L128], not linkage: they are created per
    # run and are never visible to the caller.
    batch = GlBatchRecord()
    posting = WsPostingRecord()

    #  THE OPTIONS EACH FACADE CONTEXT MAY CARRY ARE NOT THE SAME, and the
    #  difference is the handlers', not this module's: the batch handler
    #  `acas007` accepts exactly the five positional records the facade passes
    #  it, while the posting handler `acas006` additionally accepts a
    #  cursor-state map. Forwarding this program's options to BOTH contexts would
    #  make every batch verb fail on an unexpected argument.
    #
    #  NOTHING ABOUT THE CONNECTION TRAVELS THIS WAY. The transport policy used
    #  to be forwarded here, to the posting context and therefore to only one of
    #  this program's two tables; it is now installed once at the entry point and
    #  resolved by `connection.mysql_1000_open` for every open alike. See the
    #  note on `run`.
    posting_options: dict[str, object] = {}
    if states is not None:
        posting_options["states"] = states

    store = _WorkingStorage(
        ws_calling_data=ws_calling_data,
        system_record=system_record,
        to_day=to_day,
        file_defs=file_defs,
        file_access=resolved_file_access,
        dal_common=resolved_dal_common,
        batch=batch,
        posting=posting,
        pre_trans_record=PreTransRecord(),
        maps03_ws=Maps03Ws(),
        ws=WsDateFormats(),
        # `move zero to a.` [general/gl070.cbl:L284] resets the detector at the head of
        # the phase driver.
        detector=_DETECTOR_CLEAR,
        work_files=resolved_work_files,
        batch_ctx=facade.FacadeContext(
            system=system_record,
            record=batch,
            file_access=resolved_file_access,
            file_defs=file_defs,
            dal_common=resolved_dal_common,
        ),
        posting_ctx=facade.FacadeContext(
            system=system_record,
            record=posting,
            file_access=resolved_file_access,
            file_defs=file_defs,
            dal_common=resolved_dal_common,
            options=posting_options,
        ),
    )

    _init01(store)

    return store.work_files
