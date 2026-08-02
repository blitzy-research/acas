"""`gl070` - General Ledger phases 1 and 2  [general/gl070.cbl].

The migration of `general/gl070.cbl` in its entirety. Boundary: THE WHOLE
POSTING PATH - there is no partial-file carve-out here, unlike `gl051`
[general/gl051.cbl:L1096-L1133] and `irs030` [irs/irs030.cbl:L1569-L1733].

TWO PHASES, AND THE PROGRAM LABELS THEM ITSELF
==============================================
The `display` statements are the program's own documentation of what it is:

    284  display "Phase - 1.  Batch Check" at 0801  with foreground-color 2.
    292  display "Phase - 2.  Transaction Pre-process" at 0801 with ...

THE PHASE NUMBERING IS NOT AN EXECUTION ORDER, and Agent Action Plan section
0.6.4 asks that the labels be preserved "so a maintainer is not misled". The
General Ledger cycle runs phase 1, phase 2, phase 4 and only then phase 3:

    phase 1  batch check                 gl070  [general/gl070.cbl:L284]
    phase 2  transaction pre-process     gl070  [general/gl070.cbl:L292]
    (sort)                               gl071  [general/gl071.cbl:L172-L178]
    phase 4  transaction update          gl072  [general/gl072.cbl:L274]
    phase 3  transaction deletion        gl080  [general/gl080.cbl:L319]
    phase 5  end of period processing    gl080  [general/gl080.cbl:L336]

WHAT THIS PROGRAM PRODUCES, AND WHAT IT DOES NOT
================================================
`gl070` WRITES NOTHING TO THE DATABASE. Its six data-access verbs are three
opens, three reads and three closes over two tables, and there is no write, no
rewrite and no delete anywhere in the file. Its entire output is the `pre-trans`
work sequence - a transient `organization line sequential` work file
[general/gl070.cbl:L93-L96] named at [copybooks/wsnames.cob:L15], not a table,
and nothing about it appears in a table dump.

THE ORDER THE LEGS ARE APPENDED IN IS LOAD-BEARING. `gl071` sorts `pre-trans`
on `(sort-batch, sort-ac, sort-pc, sort-post)` [general/gl071.cbl:L173-L176],
and TIES IN THAT TUPLE ARE REACHABLE HERE: the debit leg and the credit leg of
one posting differ only in `pre-ac` and `pre-pc`, so a posting whose debit and
credit accounts and profit centres agree produces two records with an identical
key. `gl072` then locates each nominal account by a SEQUENTIAL read
[general/gl072.cbl:L407-L408], with no error path at all, so the sort has to be
stable and the insertion order here is what stability preserves.

THE ABORT IS A FOUR-LINK CHAIN THAT STOPS THE WHOLE CYCLE
=========================================================
This is the single most important thing a caller has to reproduce, and it is
`acas_posting/cli/gl_post_cycle.py`'s contract with this module:

    1. phase 1 sets the detector flag when it meets an OPEN batch in the
       current accounting cycle          [general/gl070.cbl:L314-L315]
    2. `menu-input2.` tests the flag, runs the open-batch report and stores
       `5` into `WS-Term-Code`           [general/gl070.cbl:L287-L290]
    3. `load00.` returns to `load08.` without tripping its own gate, because
       that gate is `if ws-term-code > 7` and 5 is not greater than 7
                                         [general/general.cbl:L720-L721]
    4. `load08.` tests `if ws-term-code = 5 go to display-menu.` and returns
       to the menu                       [general/general.cbl:L810-L811]

THE EFFECT IS THAT `gl071` AND `gl072` NEVER RUN AT ALL. It is a hard gate,
not a warning: the database effect of the abort is the ABSENCE of everything
phases 4 and 5 would have written. A caller that logged the condition and
carried on would post an unproofed batch.

The exact value matters twice over, which is why nobody may "simplify" it: too
small and `load08.` stops matching, above 7 and `load00.` diverts to
`overrewrite.` instead. And note [general/general.cbl:L714] - `load00.` moves
zero into `WS-Term-Code` BEFORE every `CALL`, so `run` must not assume any
incoming value and does not read one.

THE LINKAGE, VERBATIM  [general/gl070.cbl:L245-L248]
====================================================
    procedure division using ws-calling-data
                             system-record
                             to-day
                             file-defs.

with `01  to-day              pic x(10).` at [general/gl070.cbl:L243]. That is
the four-parameter General Ledger call shape, identical in `gl051`
[general/gl051.cbl:L353-L356], `gl071` [general/gl071.cbl:L161-L164], `gl072`
[general/gl072.cbl:L262-L265] and `gl080` [general/gl080.cbl:L269-L272],
because all five are dispatched through the one menu paragraph `load00.` whose
single `CALL` parameter list is [general/general.cbl:L715-L718]. The Sales and
Purchase families add a fourth system record and `irs030` takes neither the
calling-data block nor the run date; neither shape applies here.

NO CLOCK IS READ  (rule R-6)
============================
`general/gl070.cbl` contains ZERO clock reads. The run date arrives entirely
through the `to-day` linkage parameter, and the one `accept` that reads the
environment - `accept ws-env-lines from lines.` [general/gl070.cbl:L254] - asks
for the terminal's height, not the time. So this module reads no clock, holds
no clock and imports no clock: pinning the date is the caller's business, and
`acas_posting/clock.py` is reached only from the command-line boundary.

FOUR `loop.` PARAGRAPHS AND FIVE `main-exit.` PARAGRAPHS
========================================================
Paragraph names are NOT unique in this file, so every function below is
SECTION-QUALIFIED (rule R-5):

    loop.       L305 in `gl071a`   L344 in `gl060a`
                L450 in `gl071b`   L483 in `gl071b-pre-process`
    main-exit.  L295 in `init01`   L323 in `gl071a`   L442 in `gl060a`
                L475 in `gl071b`   L535 in `gl071b-pre-process`
    end-run.    L318 in `gl071a`   L469 in `gl071b`

`_gl071a_loop` and `_gl060a_loop` are different paragraphs that happen to share
a COBOL name, and merging them would merge two passes that exist for opposite
reasons - see THE TWO PASSES ARE NOT THE SAME PASS below.

THE TWO PASSES ARE NOT THE SAME PASS
====================================
Both walk the whole batch file and both filter on the accounting cycle, and
there the resemblance ends:

    `gl071a`  L314-L315   `if status-open move 1 to a.`
              A DETECTOR. It does not skip the batch, does not stop the walk
              and changes no record; it raises a flag that phase 2 never sees
              and that `menu-input2.` turns into the abort.

    `gl071b`  L460-L463   `if status-open or not waiting or not gl-batch
                             go to loop.`
              A REJECTOR. It skips the batch outright, so no posting of that
              batch is exploded into `pre-trans`.

Collapsing them would either abort on a batch phase 2 merely skips, or skip a
batch phase 1 merely counts. They are two functions and they stay two.

ARITHMETIC  (rule R-2)
======================
Four statements, and NOT ONE OF THEM IS `ROUNDED`. Agent Action Plan section
0.6.1 places all five `ROUNDED` sites of the whole in-scope cycle elsewhere -
[general/gl051.cbl:L791], [general/gl051.cbl:L796], [general/gl080.cbl:L328],
[irs/irs030.cbl:L1551] and [irs/irs030.cbl:L1562] - so every store here
truncates toward zero, which is COBOL's default and the plan's warning:
"Getting this backwards would corrupt essentially every posted figure."

    504  add      post-amount  vat-amount  giving  pre-amount
    513  add      post-amount  vat-amount  giving  pre-amount
    517  multiply pre-amount  by  -1  giving  pre-amount.
    530  multiply pre-amount  by  -1 giving pre-amount.

Both `ADD` statements are VARIADIC `ADD ... GIVING`: the receiver contributes
nothing and the two sources are totalled at intermediate precision and stored
once, which `acas_posting.cobol.arithmetic.add_giving` documents against this
very site. There is ZERO `ON SIZE ERROR` and ZERO `REMAINDER` in the program,
so no overflow handler is added (rule R-3). The cursor arithmetic of the
open-batch report - [general/gl070.cbl:L406], [general/gl070.cbl:L409] and
[general/gl070.cbl:L411] - computes screen positions only and is recorded as
omission 6 rather than reproduced.

Every value is `int` or `decimal.Decimal`; nothing accounting-shaped is ever
carried by an inexact binary carrier, and this module contains no numeric
primitive of its own. Agent Action Plan section 0.3.1, verbatim: "`cobol/`
contains no business logic and `programs/` contains no numeric primitives."

AMBIGUITIES  (rule R-6 - each one feeds docs/migration/ambiguity-resolutions.md)
================================================================================
Q-70a  `move 1 to File-Key-No.` [general/gl070.cbl:L272] may be INERT. Every
       entity facade dispatch paragraph sets the key number itself immediately
       before its `CALL` - `move 1 to File-Key-No` at
       [copybooks/Proc-ACAS-FH-Calls.cob:L52] - so the value this program
       stores is overwritten before any handler reads it. Reproduced anyway;
       only the compiled program can show whether any path observes it.
Q-70b  `move WS-Batch-Nos to pre-batch.` [general/gl070.cbl:L480] is
       overwritten by `move batch to pre-batch.` [general/gl070.cbl:L495]
       before the first `write`, on every path that reaches a write. Both
       statements are reproduced and the redundancy is not tidied away. Whether
       any path can reach a `write` without passing L495 - it cannot, by
       inspection - is left for the oracle to confirm.
Q-70c  `if WS-Post-Key = zero` [general/gl070.cbl:L490] is a GROUP comparison
       against the figurative constant, so the compiled program compares ten
       characters against `"0000000000"`. A group holding SPACES therefore
       fails the test and the posting is PROCESSED. The Python record carries
       the two members as `int` [copybooks/wspost.cob:L15-L16] and cannot
       represent a blank key, so the two readings differ only for a row no
       migrated read can produce. See `_gl071b_pre_process_loop`.
Q-70d  `Scycle` REDEFINES `cyclea` [copybooks/wssystem.cob:L62-L63], one
       storage under two names. The Python record carries two independent
       attributes with no synchronisation, so which one a system-record read
       populates decides what this program compares against. `gl070` reads
       `scycle` and this module reads `scycle`; nothing here reconciles them.
Q-70e  The open-batch report's paging prompt [general/gl070.cbl:L416-L427] is
       dropped, and it is worth recording why that is safe rather than assuming
       it: `ws-21-lines` is `binary-char unsigned value zero`
       [general/gl070.cbl:L165] and the statement that would set it,
       `subtract 3 from ws-lines giving ws-21-lines`, IS COMMENTED OUT at
       [general/gl070.cbl:L262]. So it stays zero, `lin` starts at seven
       [general/gl070.cbl:L340] and only grows, and `if lin < ws-21-lines
       go to loop.` [general/gl070.cbl:L413-L414] can never be true - the
       prompt is reached after the FIRST batch line of every run. Both of its
       branches lead back to `loop.` or forward to `end-report.`, and
       `end-report.` is also where the at-end goes, so the sequence of batch
       reads is the same either way. `gl060a` performs no write, so neither
       branch can change a table.

THE FREEZE
==========
`general/gl070.cbl` is read-only specification. Nothing in this migration
edits, reformats, comments or moves it, and the same holds for every copybook
and for `mysql/ACASDB.sql`.
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

#: The single public name. Every other function in this module is private,
#: because Agent Action Plan section 0.3.3 requires that "callers cannot reach
#: into a program's internals, exactly as a COBOL `CALL` cannot".
__all__: Final[tuple[str, ...]] = ("run",)


#: Diagnostics only. Every `display` statement of the frozen program that has no
#: database effect becomes a record here (Agent Action Plan section 0.3.4), and
#: nothing logged can alter control flow or reach a table.
_LOG: Final[logging.Logger] = logging.getLogger(__name__)


#: `77  prog-name  pic x(15)  value "gl070 (3.3.00)".`
#: [general/gl070.cbl:L123]. Presentation - the banner at
#: [general/gl070.cbl:L277] - carried so the log records name the program the
#: way the screen did.
_PROG_NAME: Final[str] = "gl070 (3.3.00)"


#: `move 5 to ws-term-code.` [general/gl070.cbl:L289]. THE abort value; see THE
#: ABORT IS A FOUR-LINK CHAIN in the module docstring for why it is exactly
#: five and neither smaller nor larger.
_WS_TERM_CODE_OPEN_BATCH_FOUND: Final[int] = 5


#: `move 1 to a.` [general/gl070.cbl:L315] and `move zero to a.`
#: [general/gl070.cbl:L283]. The only two values `03  a  pic 9.`
#: [general/gl070.cbl:L157] ever holds.
_DETECTOR_RAISED: Final[int] = 1
_DETECTOR_CLEAR: Final[int] = 0


#: `move 1 to File-Key-No.` [general/gl070.cbl:L272] - see question Q-70a.
_FILE_KEY_NO_PRIMARY: Final[int] = 1


#  DESCRIPTORS - LOOKED UP, NEVER CONSTRUCTED  (rule R-5)

# Not one `FieldDescriptor` is built in this module. Each one below is READ from
# the published surface of the record module that owns the field, so the storage
# description of every sending and receiving field is declared in exactly one
# place and this module cannot drift from it. The provenance invariant that
# `FieldDescriptor` enforces - a `dictionary_key` or a `source_locator` on every
# instance - is therefore satisfied by construction rather than by assertion.


def _pre_trans_descriptors() -> dict[str, FieldDescriptor]:
    """Map each `pre-trans-record` attribute to the descriptor it carries.

    `acas_posting.records.work_records` attaches the descriptor of every field
    of `01  pre-trans-record.` [general/gl070.cbl:L108-L116] to the dataclass
    member's `metadata`, and its module docstring publishes this exact loop as
    the way to read them back. Using it keeps every width, scale, sign and
    usage in one place - the record module - so the moves below cannot describe
    a field differently from the layout that receives them.

    Returns:
        Attribute name to descriptor, for all eight members.
    """
    return {
        member.name: member.metadata[COBOL_FIELD_METADATA_KEY]
        for member in dataclasses.fields(PreTransRecord)
    }


#: The receiving fields of every move in `gl071b-pre-process`, keyed by
#: attribute name: `pre_batch`, `pre_post`, `pre_code`, `pre_date`, `pre_ac`,
#: `pre_pc`, `pre_amount`, `pre_legend`.
_PRE: Final[dict[str, FieldDescriptor]] = _pre_trans_descriptors()

#: The sending fields - `01  WS-Posting-Record.` [copybooks/wspost.cob:L12],
#: keyed by the COBOL name exactly as the copybook spells it.
_POST: Final[dict[str, FieldDescriptor]] = {
    descriptor.name: descriptor for descriptor in WsPostingRecord.FIELDS
}

#: `03  WS-Post-Key.` [copybooks/wspost.cob:L14] - its two `pic 9(5)` members,
#: which the group descriptor in `_POST` does not describe individually.
_POST_KEY: Final[dict[str, FieldDescriptor]] = {
    descriptor.name: descriptor for descriptor in WsPostKey.FIELDS
}

#: `05  File-Key-No  pic 9.` [copybooks/wsfnctn.cob:L46], inside
#: `03  Logging-Data.` rather than beside the status fields.
_FILE_KEY_NO: Final[FieldDescriptor] = next(
    descriptor
    for descriptor in LoggingData.FIELDS
    if descriptor.name == "File-Key-No"
)

#: `05  WS-Batch-Nos  pic 9(5).` [copybooks/wsbatch.cob:L19], the sending field
#: of `move WS-Batch-Nos to pre-batch.` [general/gl070.cbl:L480]. It lives on
#: `03  WS-Batch-Key.` [copybooks/wsbatch.cob:L14] rather than on the record's
#: own field list, the key being a group.
_BATCH_NOS: Final[FieldDescriptor] = next(
    descriptor
    for descriptor in WsBatchKey.FIELDS
    if descriptor.name == "WS-Batch-Nos"
)

#: `03  u-bin  binary-long.` [copybooks/wsmaps03.cob:L30] - the receiving field
#: of the four `move <date> to u-bin` statements of the open-batch report
#: [general/gl070.cbl:L364], [general/gl070.cbl:L369],
#: [general/gl070.cbl:L374], [general/gl070.cbl:L379].
_U_BIN: Final[FieldDescriptor] = next(
    descriptor for descriptor in Maps03Ws.FIELDS if descriptor.name == "u-bin"
)


#: `if post-vat-side = "CR"` [general/gl070.cbl:L503], [general/gl070.cbl:L529]
#: and `if post-vat-side = "DR"` [general/gl070.cbl:L512]. Two-character
#: literals against `03  Post-Vat-Side  pic xx.` [copybooks/wspost.cob:L27], so
#: the operands are the same length and COBOL's space-padding rule for unequal
#: lengths never comes into play. Case-sensitive, as COBOL is.
_VAT_SIDE_CREDIT: Final[str] = "CR"
_VAT_SIDE_DEBIT: Final[str] = "DR"

#: The zero every numeric comparison in this module is made against. A
#: `decimal.Decimal`, so the two-place amounts compare without any coercion.
_ZERO: Final[decimal.Decimal] = decimal.Decimal(0)


#: `move " G/L" to l6-ledger.` [general/gl070.cbl:L355] and its two siblings
#: [general/gl070.cbl:L357], [general/gl070.cbl:L359]. Presentation - the
#: report's ledger column - carried so the log line reads as the screen did.
_LEDGER_LABEL_GL: Final[str] = " G/L"
_LEDGER_LABEL_PL: Final[str] = " P/L"
_LEDGER_LABEL_SL: Final[str] = " S/L"

#: `move "Open" to l6-status.` [general/gl070.cbl:L388] and the three
#: `status-closed` spellings [general/gl070.cbl:L392], [general/gl070.cbl:L395],
#: [general/gl070.cbl:L398]. Presentation, exactly as above.
_STATUS_LABEL_OPEN: Final[str] = "Open"
_STATUS_LABEL_WAITING: Final[str] = "Waiting"
_STATUS_LABEL_PROCESSED: Final[str] = "Processed"
_STATUS_LABEL_ARCHIVED: Final[str] = "Archived"

#: `move 7 to lin.` [general/gl070.cbl:L340] and, after a page clear,
#: [general/gl070.cbl:L432]. The report's first body line, lines three to six
#: having been taken by the headings.
_REPORT_FIRST_BODY_LINE: Final[int] = 7

#: `add 3 to lin.` [general/gl070.cbl:L411]. Each batch occupies two printed
#: lines, `line-6` and `line-7`, plus one blank.
_REPORT_LINES_PER_BATCH: Final[int] = 3


#  WORKING STORAGE  -  PASSED, NEVER HELD AT MODULE SCOPE


@dataclasses.dataclass(slots=True)
class _WorkingStorage:
    """What `gl070`'s WORKING-STORAGE and LINKAGE hold for one run.

    NOT A COBOL CONSTRUCT AND NOT PART OF THE PUBLIC API. COBOL gives a called
    program a working-storage section that persists for the life of the run and
    a linkage section that aliases the caller's data; Python gives a function
    parameters. This carrier is how the paragraph functions below share the one
    set of records the frozen program shares, WITHOUT any module-level mutable
    state - which rule R-6 forbids, because a sequence or a flag surviving from
    one run into the next would break byte-identical reruns silently.

    ONE `File-Access` FOR BOTH TABLES, and that is not an economy. `gl070`
    copies `wsfnctn.cob` ONCE [general/gl070.cbl:L126], so the compiled program
    has exactly one `Fs-Reply` [copybooks/wsfnctn.cob:L25] - the same field
    tested after a batch read at [general/gl070.cbl:L454] and after a posting
    read at [general/gl070.cbl:L487]. Two `File-Access` records would let a
    posting read's at-end hide behind a batch read's success.

    Attributes:
        ws_calling_data: `01  WS-Calling-Data.` [copybooks/wscall.cob:L6], the
            first linkage parameter. Written on the abort path and nowhere else.
        system_record: `SYSTEM-REC`, the second linkage parameter. `Scycle`
            [copybooks/wssystem.cob:L63] is read by both passes; `Date-Form`
            [copybooks/wssystem.cob:L128] is read AND written by the two date
            sections.
        to_day: `01  to-day  pic x(10).` [general/gl070.cbl:L243], the third
            linkage parameter, in DD/MM/CCYY form.
        file_defs: `01  File-Defs.` [copybooks/wsnames.cob:L13], the fourth.
        file_access: `01  File-Access.` [copybooks/wsfnctn.cob:L22], carried in
            WORKING-STORAGE by this program because it copies the copybook
            [general/gl070.cbl:L126].
        dal_common: `01  ACAS-DAL-Common-data.`
            [copybooks/Test-Data-Flags.cob:L6], likewise
            [general/gl070.cbl:L154].
        batch: `01  WS-Batch-Record.` [copybooks/wsbatch.cob:L13], from
            [general/gl070.cbl:L127]. Filled by every batch read.
        posting: `01  WS-Posting-Record.` [copybooks/wspost.cob:L12], from
            [general/gl070.cbl:L128]. Filled by every posting read.
        pre_trans_record: `01  pre-trans-record.` [general/gl070.cbl:L108], the
            FILE SECTION record AREA. ONE area for the whole run, reused and
            overwritten in place between the three writes of the double-entry
            explosion, exactly as the compiled program reuses it.
        maps03_ws: `01  maps03-ws.` [copybooks/wsmaps03.cob:L6], from
            [general/gl070.cbl:L125] - the date module's linkage block.
        ws: `01  ws-date-formats.` [general/gl070.cbl:L173] plus
            `01  ws-Test-Date` [general/gl070.cbl:L172], the working storage the
            two date sections write `ws-date` into.
        detector: `03  a  pic 9.` [general/gl070.cbl:L157]. THE flag phase 1
            raises and `menu-input2.` turns into the abort. Carried as a plain
            `int`: the generated data dictionary describes the file-record
            layouts and the copybooks, not this program's own working storage,
            so there is no descriptor to look up, and the only two values the
            program ever stores are the literals at [general/gl070.cbl:L283]
            and [general/gl070.cbl:L315].
        work_files: the cycle's three work sequences. `pre-trans` is the one
            this program opens, writes and closes.
        batch_ctx: the linkage a `GL-Batch-*` facade verb needs.
        posting_ctx: the linkage a `GL-Posting-*` facade verb needs. A SECOND
            context over the SAME `File-Access`, because a facade verb names one
            entity record and these are two different entities.
        ledger_label: `03  l6-ledger  pic x(4).` [general/gl070.cbl:L221]. A
            PRINT FIELD, retained for one reason only: the three independent
            `if`s that fill it [general/gl070.cbl:L354-L359] can all miss, and
            then it still holds the PREVIOUS batch's label. Modelling it makes
            that carry-over visible instead of silently absent.
        status_label: `03  l6-status  pic x(9).` [general/gl070.cbl:L223].
            Retained for the same carry-over reason
            [general/gl070.cbl:L387-L398].
        lin: `03  Lin  pic 99.` [copybooks/wsfnctn.cob:L29], the report's cursor
            line. Retained because it is one operand of a PRESERVED CONTROL
            TRANSFER [general/gl070.cbl:L413-L414] - the sole exception the
            omissions list grants the cursor state. Its companions `curs`,
            `curs2`, `lin2` and `cole` feed only `display` positions and are
            dropped.
        ws_21_lines: `03  ws-21-lines  binary-char unsigned value zero.`
            [general/gl070.cbl:L165], the other operand of that transfer, and the
            subject of question Q-70e: the statement that would have given it a
            value, [general/gl070.cbl:L262], IS COMMENTED OUT IN THE FROZEN
            SOURCE, so it keeps its `value zero` for the whole run.
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
    [general/gl070.cbl:L454] over it again and [general/gl070.cbl:L487] over the
    posting file. It compares against `FsReply.END_OF_FILE` and never against
    the literal ten, so the value is named where the bridges name it -
    "10 = End of (Cobol) File returned to calling module only."

    THE STATUS IS SET BY THE VERB AND TESTED HERE, in that order, exactly as the
    frozen source does it: the entity-named facade convention of
    [copybooks/Proc-ACAS-FH-Calls.cob] carries NO error-check paragraph, so its
    callers test the reply inline. Nothing raises on a file error and nothing
    checks any status this program does not check (rule R-3).

    Args:
        store: the run's working storage, whose one `File-Access` holds the
            reply the last verb left there.

    Returns:
        True when the last verb reported end of file.
    """
    return store.file_access.fs_reply == FsReply.END_OF_FILE


def _cycle_differs(store: _WorkingStorage) -> bool:
    """`if bcycle not = scycle` - THE ACCOUNTING-CYCLE FILTER.

    Appears three times, once in each pass over the batch file:
    [general/gl070.cbl:L312] in phase 1, [general/gl070.cbl:L351] in the
    open-batch report and [general/gl070.cbl:L457] in phase 2. `03  Bcycle
    pic 99.` [copybooks/wsbatch.cob:L34] is the batch's own cycle; `05  Scycle
    redefines cyclea binary-char` [copybooks/wssystem.cob:L63] is the system's
    - see question Q-70d on the redefinition.

    Both are scale-zero integers, and the comparison is routed through
    `acas_posting.cobol.arithmetic.compare` rather than done here, because this
    module holds no numeric primitives of its own.

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
    """`if WS-Post-Key = zero` - the unset-key filter.

    [general/gl070.cbl:L490]. A filter the Agent Action Plan does not mention,
    and the only one in the program applied to the posting record's key rather
    than to a status or a cycle.

    A GROUP ITEM COMPARED AGAINST A FIGURATIVE CONSTANT. `03  WS-Post-Key.`
    [copybooks/wspost.cob:L14] is a group of two elementary items, `05  Batch
    pic 9(5).` and `05  Post-Number  pic 9(5).`
    [copybooks/wspost.cob:L15-L16], so COBOL treats the comparison as
    ALPHANUMERIC: the ten characters of the group are compared against ten
    `"0"` characters.

    WHY COMPARING THE TWO MEMBERS NUMERICALLY IS THE SAME TEST. Both members are
    unsigned `DISPLAY` integers, and a zoned unsigned integer's characters are
    all `"0"` exactly when its value is zero - there is no sign position to
    perturb it and no alternative encoding of zero. The group's characters are
    the concatenation of the two members' characters, so all ten are `"0"` if and
    only if both members are zero. The numeric form is used because it is the one
    the published primitive offers, and it is proved equivalent here rather than
    assumed.

    Args:
        store: the run's working storage.

    Returns:
        True when the posting record's key is entirely zero, i.e. the record is
        an unused slot and is to be skipped.
    """
    return (
        arithmetic.compare(store.posting.ws_post_key.batch, _ZERO) == 0
        and arithmetic.compare(store.posting.ws_post_key.post_number, _ZERO)
        == 0
    )


#  init01 section.  [general/gl070.cbl:L251]


def _init01(store: _WorkingStorage) -> None:
    """`init01 section.` - the program's entry, minus the terminal.

    [general/gl070.cbl:L251]. Ten statements, of which SEVEN are screen setup
    and are recorded as omissions 2 and 3 rather than reproduced: the terminal
    height read [general/gl070.cbl:L254], the four screen-geometry statements
    [general/gl070.cbl:L255-L261] and the two `set ENVIRONMENT` statements that
    make the escape and paging keys detectable [general/gl070.cbl:L268-L269].
    None has a database effect and none can have one - they size a screen this
    migration does not draw.

    THE TWO THAT SURVIVE, AND WHY. `perform zz070-convert-date`
    [general/gl070.cbl:L270] is kept because the section it performs MUTATES THE
    SYSTEM RECORD: `if Date-Form = zero / move 1 to Date-Form.`
    [general/gl070.cbl:L583-L584] defaults an unset date format to United
    Kingdom, and `Date-Form` is a `SYSTEM-REC` column, so the mutation is
    visible in a table dump. Dropping the call because its TEXT output is a
    print field would lose a real state change. `move 1 to File-Key-No`
    [general/gl070.cbl:L272] is kept for the reason question Q-70a records.

    Args:
        store: the run's working storage.
    """
    # 254  accept   ws-env-lines   from lines.
    # 255-259  if ws-env-lines < 24 move 24 ... else move ws-env-lines ...
    # 260  subtract 1 from ws-lines giving ws-23-lines.
    # 261  subtract 2 from ws-lines giving ws-22-lines.
    # 268  set      ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".
    # 269  set      ENVIRONMENT "COB_SCREEN_ESC" to "Y".
    #      OMITTED - omissions 2 and 3. Terminal geometry and key handling for a
    #      screen this migration does not draw. `accept ... from lines` reads the
    #      TERMINAL HEIGHT, not a clock, so rule R-6 is not in play here.

    # 270  perform  zz070-convert-date.
    _zz070_convert_date(store)

    # 271  move     ws-date to l3-date.
    #      `l3-date` is a print field of `01 line-3.` [general/gl070.cbl:L209] -
    #      presentation, omission 5. The CONVERSION above is not presentation and
    #      is performed; only its destination is dropped.

    # 272  move     1  to File-Key-No.
    #      Question Q-70a: probably inert, because every facade dispatch
    #      paragraph sets the key number itself immediately before its `CALL`
    #      [copybooks/Proc-ACAS-FH-Calls.cob:L52]. Reproduced regardless, through
    #      the receiving field's own descriptor rather than by assignment.
    store.file_access.logging_data.file_key_no = cobol_move.move(
        _FILE_KEY_NO_PRIMARY, _FILE_KEY_NO
    )

    # 274  menu-input.
    #      FALL-THROUGH, not a `perform`. The section's opening statements end at
    #      [general/gl070.cbl:L272] and control simply runs on into the next
    #      paragraph, so the call is written out explicitly - which is what "fall
    #      through becomes explicit function composition that preserves execution
    #      order" asks for.
    _init01_menu_input(store)

    # 281  menu-input2.
    #      Fall-through again.
    _init01_menu_input2(store)

    # 295  main-exit.
    #      And again. The Class-3 `return` at [general/gl070.cbl:L290] also lands
    #      here, by returning from `_init01_menu_input2` above.
    _init01_main_exit(store)


def _init01_menu_input(store: _WorkingStorage) -> None:
    """`menu-input.` - the screen banner, and nothing else.

    [general/gl070.cbl:L274]. Three `display` statements
    [general/gl070.cbl:L277-L279] and no other statement of any kind, so the
    whole paragraph is presentation. It becomes ONE informational log record
    carrying what the three lines carried - the program banner, its title and
    the run date - because Agent Action Plan section 0.3.4 turns a diagnostic
    display with no database effect into a log record at a severity matching the
    original's intent.

    REACHED TWO WAYS, which is why it is a function rather than inlined. Control
    FALLS THROUGH into it from `init01` [general/gl070.cbl:L272-L274], and the
    open-batch report `perform`s it from another section entirely
    [general/gl070.cbl:L328]. So the banner is redrawn when the report starts,
    and the report relies on `erase eos` at [general/gl070.cbl:L277] to clear
    the screen first.

    Args:
        store: the run's working storage; `ws.ws_date` supplies the run date the
            third display shows.
    """
    # 277  display  prog-name at 0101 with foreground-color 2 erase eos.
    # 278  display  "Transaction Posting" at 0132  with foreground-color 2.
    # 279  display  ws-date at 0171 with foreground-color 2.
    #      Screen positions, colours and the `erase eos` clause are dropped;
    #      omission 1.
    _LOG.info(
        "%s  Transaction Posting  %s", _PROG_NAME, store.ws.ws_date
    )


def _init01_menu_input2(store: _WorkingStorage) -> None:
    """`menu-input2.` - THE PHASE DRIVER AND THE ABORT.

    [general/gl070.cbl:L281]. Eight statements, and between them they decide
    whether the General Ledger posting cycle proceeds at all:

        283  move     zero  to  a.
        284  display  "Phase - 1.  Batch Check" at 0801 ...
        285  perform  gl071a.
        287  if       a = 1
        288           perform gl060a
        289           move 5 to ws-term-code
        290           go to  main-exit.
        292  display  "Phase - 2.  Transaction Pre-process" at 0801 ...
        293  perform  gl071b.

    THE ORDER INSIDE THE ABORT BLOCK IS PRESERVED. `perform gl060a` runs BEFORE
    `move 5 to ws-term-code`, and the report it runs performs
    `GL-Batch-Open-Input`, `GL-Batch-Read-Next` and `GL-Batch-Close` - reads
    only, no write of any kind - so the ordering has no database effect. It is
    reproduced in order anyway, because the traceability has to show it and
    because "no effect today" is not a licence to reorder frozen statements.

    THE FLAG IS CLEARED HERE, NOT AT DECLARATION. `03  a  pic 9.`
    [general/gl070.cbl:L157] carries no VALUE clause, and `move zero to a`
    [general/gl070.cbl:L283] is what makes the detector per-run rather than
    per-load. It matters because a dynamically loaded COBOL module keeps its
    working storage between `CALL`s within one run of the menu, so without this
    statement a second posting cycle would inherit the first one's verdict.

    Args:
        store: the run's working storage. `ws_calling_data.ws_term_code` is
            written here on the abort path AND NOWHERE ELSE in this module.
    """
    # 283  move     zero  to  a.
    store.detector = _DETECTOR_CLEAR

    # 284  display  "Phase - 1.  Batch Check" at 0801 with foreground-color 2.
    _LOG.info("Phase - 1.  Batch Check")

    # 285  perform  gl071a.
    _gl071a(store)

    # 287  if       a = 1
    if store.detector == _DETECTOR_RAISED:
        # 288           perform gl060a
        #      BEFORE the term code is set - see the docstring.
        _gl060a(store)

        # 289           move 5 to ws-term-code
        #      THE ABORT. `general/general.cbl` `load08.` tests
        #      `if ws-term-code = 5 go to display-menu.`
        #      [general/general.cbl:L810-L811] and returns to the menu, so
        #      `gl071` and `gl072` never run. A hard gate, not a warning.
        store.ws_calling_data.ws_term_code = _WS_TERM_CODE_OPEN_BATCH_FOUND
        _LOG.info(
            "An open batch was found in cycle %s: WS-Term-Code set to %s, so"
            " gl071 and gl072 will not run.",
            store.system_record.system_data_block.scycle,
            _WS_TERM_CODE_OPEN_BATCH_FOUND,
        )

        # 290           go to  main-exit.
        # GO TO class 3 - a forward transfer to this section's TRAILING exit
        # paragraph `main-exit.` [general/gl070.cbl:L295], which holds only
        # `goback.` So it is a `return`, and `run` calls `_init01_main_exit`
        # immediately afterwards, which is exactly where the transfer lands.
        return

    # 292  display  "Phase - 2.  Transaction Pre-process" at 0801 with ...
    _LOG.info("Phase - 2.  Transaction Pre-process")

    # 293  perform  gl071b.
    _gl071b(store)


def _init01_main_exit(store: _WorkingStorage) -> None:
    """`main-exit.` - `goback.`

    [general/gl070.cbl:L295], whose whole body is `goback.`
    [general/gl070.cbl:L298]. The FIRST of the five paragraphs in this file
    called `main-exit.`, and the only one that ends the PROGRAM rather than a
    section: the other four are `exit section.`

    Reached two ways, both of which land here: by falling through from
    `menu-input2.`'s last statement [general/gl070.cbl:L293-L295], and by the
    Class-3 transfer at [general/gl070.cbl:L290]. Kept as a function because
    rule R-5 requires one per paragraph even where the `GO TO` became a
    `return` - Agent Action Plan section 0.7.4 C-4, verbatim: "every paragraph
    retains a named function even where its `GO TO` becomes a `continue`, a
    `break` or a `return`."

    Args:
        store: the run's working storage. Nothing further is written to it; the
            values a caller reads back are `WS-Term-Code`, whatever the two date
            sections left in `Date-Form`, and the `pre-trans` sequence.
    """
    # 298  goback.
    #      Return to `general/general.cbl` `load00.` [general/general.cbl:L711]
    #      in a real run, which then tests `if ws-term-code > 7`
    #      [general/general.cbl:L720-L721] - a gate five does not trip - before
    #      `load08.` tests for five exactly [general/general.cbl:L810-L811].
    del store
    return


#  gl071a section.  -  PHASE 1, THE DETECTOR PASS  [general/gl070.cbl:L300]


def _gl071a(store: _WorkingStorage) -> None:
    """`gl071a section.` - phase 1, the batch check.

    [general/gl070.cbl:L300]. Walks EVERY batch of the current accounting cycle
    and raises one flag if any of them is still open. It changes no record,
    writes nothing anywhere and does not stop early - it is a survey, and its
    only product is `03  a  pic 9.`

    THIS IS A DETECTOR, NOT A REJECTOR, and that is the whole difference between
    this pass and phase 2's [general/gl070.cbl:L460-L463]. See THE TWO PASSES
    ARE NOT THE SAME PASS in the module docstring for why they may not be
    merged.

    Args:
        store: the run's working storage. `detector` is the only thing this
            section can change.
    """
    # 303  perform  GL-Batch-Open-Input.           *> open input batch-file.
    #      `GL-Batch-Open-Input` [copybooks/Proc-ACAS-FH-Calls.cob:L424-L427]
    #      sets `fn-open` and `fn-input` and performs the `acas007` dispatch. The
    #      reply is NOT tested here, because the frozen program does not test it
    #      here (rule R-3) - the entity-named convention carries no error-check
    #      paragraph at all, so a failed open shows up as the first read
    #      returning end of file.
    facade.gl_batch_open_input(store.batch_ctx)

    # 305  loop.
    _gl071a_loop(store)

    # 323  main-exit.   exit section.
    _gl071a_main_exit(store)


def _gl071a_loop(store: _WorkingStorage) -> None:
    """`loop.` in `gl071a` - read every batch, and raise the flag on an open one.

    [general/gl070.cbl:L305]. The FIRST of four paragraphs in this file named
    `loop.`; the others are [general/gl070.cbl:L344],
    [general/gl070.cbl:L450] and [general/gl070.cbl:L483].

        308      perform  GL-Batch-Read-Next.
        309      if       fs-reply = 10
        310               go to  end-run.
        312      if       bcycle not = scycle
        313               go to  loop.
        314      if       status-open
        315               move  1  to  a.
        316      go       to loop.

    THREE TRANSFERS, TWO CLASSES. The at-end is Class 2 - `end-run.`
    [general/gl070.cbl:L318] is followed by REAL WORK, the close at
    [general/gl070.cbl:L321], so the transformation is a `break` PLUS that work
    placed after the loop, never a `break` alone. The other two are Class 1,
    plain iteration.

    THE DETECTOR DOES NOT SKIP. Note that [general/gl070.cbl:L314-L315] has no
    `go to` of its own: after raising the flag, control reaches the unconditional
    [general/gl070.cbl:L316] and reads on. So the flag can be raised by any
    batch, is never lowered, and the walk always runs to end of file. Nothing
    counts the open batches and nothing records which they were.

    Args:
        store: the run's working storage.
    """
    while True:
        # 308      perform  GL-Batch-Read-Next.
        #      [copybooks/Proc-ACAS-FH-Calls.cob:L460-L463] - clears
        #      `Access-Type`, sets `fn-Read-Next`, performs `acas007`. Fills
        #      `store.batch` on success.
        facade.gl_batch_read_next(store.batch_ctx)

        # 309      if       fs-reply = 10
        # 310               go to  end-run.
        # GO TO class 2 - forward, out of the loop, to a label followed by real
        # work. `break` plus the post-loop block below.
        if _at_end(store):
            break

        # 312      if       bcycle not = scycle
        # 313               go to  loop.
        # GO TO class 1 - backward to this loop's head.
        if _cycle_differs(store):
            continue

        # 314      if       status-open
        # 315               move  1  to  a.
        #      `88  Status-Open  value 0.` on `03  Batch-Status  pic 9.`
        #      [copybooks/wsbatch.cob:L25-L26], tested through the published
        #      predicate and never as a raw comparison against zero.
        if condition_names.is_status_open(store.batch.batch_status):
            store.detector = _DETECTOR_RAISED

        # 316      go       to loop.
        # GO TO class 1, and UNCONDITIONAL. Written out rather than left to the
        # end of the loop body, because rule R-5 wants the transfer visible at
        # the site the frozen source puts it.
        continue

    # 318  end-run.
    _gl071a_end_run(store)


def _gl071a_end_run(store: _WorkingStorage) -> None:
    """`end-run.` in `gl071a` - close the batch file.

    [general/gl070.cbl:L318]. One statement, `perform GL-Batch-Close.`
    [general/gl070.cbl:L321], and it is exactly the "real work" that makes the
    at-end transfer a Class-2 `break` plus a post-loop block rather than a bare
    `break`. Agent Action Plan section 0.6.3, verbatim: "Mis-splitting here would
    silently drop end-of-run processing."

    The FIRST of two paragraphs called `end-run.` in this file; the other is
    phase 2's [general/gl070.cbl:L469], which closes the work file as well.

    Args:
        store: the run's working storage.
    """
    # 321  perform  GL-Batch-Close.              *> close batch-file.
    #      [copybooks/Proc-ACAS-FH-Calls.cob:L439-L442] - moves zero to
    #      `Access-Type`, sets `fn-Close`, performs `acas007`. The reply is not
    #      tested, here or in the frozen source.
    facade.gl_batch_close(store.batch_ctx)


def _gl071a_main_exit(store: _WorkingStorage) -> None:
    """`main-exit.   exit section.` in `gl071a`.

    [general/gl070.cbl:L323]. The SECOND of the five `main-exit.` paragraphs,
    and the first of the four that end a SECTION rather than the program. Its
    whole body is the `exit section.` on the same line, so it has no work to do;
    it exists because rule R-5 requires a named function per paragraph and
    because a reader looking for `gl071a`'s exit should find one.

    Reached only by falling through from `end-run.`
    [general/gl070.cbl:L321-L323]. No `GO TO` in this file targets it - phase
    1's at-end goes to `end-run.` instead.

    Args:
        store: the run's working storage, unchanged here.
    """
    # 323  main-exit.   exit section.
    del store
    return


#  gl060a section.  -  THE OPEN-BATCH REPORT  [general/gl070.cbl:L325]


def _gl060a(store: _WorkingStorage) -> None:
    """`gl060a section.` - the Batch Status Report, shown when phase 1 aborts.

    [general/gl070.cbl:L325]. Performed from exactly one place,
    [general/gl070.cbl:L288], and only when the detector was raised. It re-walks
    the batch file and reports every batch of the current cycle so the operator
    can see which one is open.

    READS ONLY. `GL-Batch-Open-Input` [general/gl070.cbl:L342],
    `GL-Batch-Read-Next` [general/gl070.cbl:L347] and `GL-Batch-Close`
    [general/gl070.cbl:L440] are its only data-access verbs. There is no write,
    no rewrite and no delete, which is what makes dropping its interactive
    paging safe - see question Q-70e - and why the ordering of
    [general/gl070.cbl:L288-L289] has no database effect.

    ITS ONE NON-PRESENTATION EFFECT is the same as `init01`'s: it performs
    `zz070-convert-date` [general/gl070.cbl:L330], which defaults `Date-Form`
    when that column is zero [general/gl070.cbl:L583-L584]. It also performs
    `zz060-Convert-Date` once per reported batch, which defaults `Date-Form` the
    same way [general/gl070.cbl:L553-L554].

    Args:
        store: the run's working storage.
    """
    # 328  perform  menu-input.
    #      A paragraph of ANOTHER SECTION, `init01` [general/gl070.cbl:L274].
    #      Redraws the banner, and its `erase eos` is what clears the screen
    #      before the report is laid out.
    _init01_menu_input(store)

    # 330  perform  zz070-convert-date.
    #      Kept for its `Date-Form` mutation, exactly as in `init01`.
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
    #      omissions 1, 5 and 6 - reproduced as the three heading log records
    #      below. `01 line-4.` [general/gl070.cbl:L211] and `01 line-5.`
    #      [general/gl070.cbl:L215] are column captions whose text is carried
    #      verbatim so a reader can line the log up against the screen.
    _LOG.info(
        "Batch Status Report    Cycle - %s    %s",
        store.system_record.system_data_block.scycle,
        store.ws.ws_date,
    )
    _LOG.info(
        "Ledger  Batch  Status       Last     "
        "---------Batch Controls---------"
    )
    _LOG.info(
        "------  -----  ------     Activity    "
        "Items  ---Gross---- -----VAT----"
    )

    # 340  move     7  to   lin.
    #      RETAINED, not omitted: `lin` is one operand of the preserved control
    #      transfer at [general/gl070.cbl:L413-L414]. Seven is the first body
    #      line, the headings having taken lines three to six.
    store.lin = _REPORT_FIRST_BODY_LINE

    # 341  move     1 to cole.
    #      The cursor column, used only to position a `display`. Omitted.

    # 342  perform  GL-Batch-Open-Input.           *> open input batch-file.
    facade.gl_batch_open_input(store.batch_ctx)

    # 344  loop.
    _gl060a_loop(store)

    # 442  main-exit.   exit section.
    _gl060a_main_exit(store)


def _gl060a_loop(store: _WorkingStorage) -> None:
    """`loop.` in `gl060a` - report one batch per pass.

    [general/gl070.cbl:L344]. The SECOND paragraph in this file named `loop.`

        347      perform  GL-Batch-Read-Next.
        348      if       fs-reply = 10
        349               go to  end-report.
        351      if       bcycle not = scycle
        352               go to  loop.
        354-359  the ledger label, one `if` per `88` of WS-Ledger
        361      move     WS-Batch-Nos     to  l6-batch.
        363-380  the four-way date-precedence chain
        382  next-1.  ... and the rest of the paragraph

    THE DATE-PRECEDENCE CHAIN IS ORDERED, AND THE ORDER IS THE REPORT'S MEANING:
    `stored`, then `posted`, then `proofed`, then `entered`
    [copybooks/wsbatch.cob:L36-L39] - latest lifecycle event first, so the column
    shows the most recent thing that happened to the batch. The first three each
    end in `go to next-1` [general/gl070.cbl:L366], [general/gl070.cbl:L371],
    [general/gl070.cbl:L376]; the fourth simply falls through
    [general/gl070.cbl:L378-L380].

    THOSE THREE TRANSFERS ARE CLASS 4, NOT CLASS 2, and the distinction is not
    academic. `next-1.` [general/gl070.cbl:L382] is a PEER PARAGRAPH INSIDE THIS
    LOOP: it does real work [general/gl070.cbl:L385-L411] and then transfers
    control itself [general/gl070.cbl:L413-L414]. A Class-2 `break` would leave
    the loop, which is the opposite of what the frozen program does. The Class-4
    transformation - a named call followed by the explicit control statement the
    target itself issues - is what appears below.

    PER-SITE PROOF OF EQUIVALENCE, which Class 4 requires. Each of the three
    transfers is the tail of an alternative whose body is `move <date> to u-bin`
    plus `perform zz060-Convert-Date`; the fourth alternative has no transfer and
    `next-1.` is the statement immediately after it, so "jump to next-1" and
    "fall through to next-1" reach the same place with nothing in between. The
    five reachable behaviours are therefore: alternative k in {1,2,3} then
    `next-1`; alternative 4 then `next-1`; or `next-1` alone when all four dates
    are zero. An `if`/`elif` chain over the four tests followed unconditionally
    by the `next-1` call produces exactly those five and no others.
    AND THE CHAIN IS LOAD-BEARING, not tidying: the `go to`s are what make the
    alternatives MUTUALLY EXCLUSIVE. Rendered as four independent `if`s, a batch
    with several non-zero dates would convert several times and the LAST
    conversion would win - reporting the `entered` date where the frozen program
    reports the `stored` one.

    IF ALL FOUR DATES ARE ZERO, NO CONVERSION RUNS AT ALL and `ws-date` keeps
    whatever the last conversion left in it - the run date from
    [general/gl070.cbl:L330] for the first such batch, or the previous batch's
    date afterwards. That carry-over is the frozen behaviour and is reproduced,
    not patched with a default (rule R-3).

    Args:
        store: the run's working storage.
    """
    while True:
        # 347      perform  GL-Batch-Read-Next.
        facade.gl_batch_read_next(store.batch_ctx)

        # 348      if       fs-reply = 10
        # 349               go to  end-report.
        # GO TO class 2 - `end-report.` [general/gl070.cbl:L435] is followed by
        # the close at [general/gl070.cbl:L440], so `break` plus the post-loop
        # block. A textbook Class 2, and the one place in this section where
        # getting the split wrong would drop the close.
        if _at_end(store):
            break

        # 351      if       bcycle not = scycle
        # 352               go to  loop.
        # GO TO class 1 - the accounting-cycle filter, second of its three
        # occurrences.
        if _cycle_differs(store):
            continue

        # 354      if       gl-batch
        # 355               move  " G/L"  to  l6-ledger.
        # 356      if       pl-batch
        # 357               move  " P/L"  to  l6-ledger.
        # 358      if       sl-batch
        # 359               move  " S/L"  to  l6-ledger.
        #      THREE SEPARATE `if` STATEMENTS, not a chain, and none excludes the
        #      others - reproduced as three, because `03  WS-Ledger  pic 9.`
        #      [copybooks/wsbatch.cob:L15] can hold a value outside 1..3 and then
        #      none of the three fires, leaving `l6-ledger` holding the PREVIOUS
        #      batch's label. Collapsing them into an `if/elif/else` with a
        #      fallback would invent a validation the frozen source does not have.
        ledger_label = store.ledger_label
        if condition_names.is_gl_batch(store.batch.ws_batch_key.ws_ledger):
            ledger_label = _LEDGER_LABEL_GL
        if condition_names.is_pl_batch(store.batch.ws_batch_key.ws_ledger):
            ledger_label = _LEDGER_LABEL_PL
        if condition_names.is_sl_batch(store.batch.ws_batch_key.ws_ledger):
            ledger_label = _LEDGER_LABEL_SL
        store.ledger_label = ledger_label

        # 361      move     WS-Batch-Nos     to  l6-batch.
        #      Presentation; the value is logged by `_gl060a_next_1` from the
        #      record itself rather than through an edited `pic z(4)9bb` field.

        # 363      if       stored not = zero
        # 364               move  stored  to  u-bin
        # 365               perform  zz060-Convert-Date
        # 366               go to next-1.            # GO TO class 4
        if arithmetic.compare(store.batch.dates.stored, _ZERO) != 0:
            store.maps03_ws.u_bin = cobol_move.move(
                store.batch.dates.stored, _U_BIN
            )
            _zz060_convert_date(store)
        # 368      if       posted not = zero
        # 369               move  posted  to  u-bin
        # 370               perform  zz060-Convert-Date
        # 371               go to next-1.            # GO TO class 4
        elif arithmetic.compare(store.batch.dates.posted, _ZERO) != 0:
            store.maps03_ws.u_bin = cobol_move.move(
                store.batch.dates.posted, _U_BIN
            )
            _zz060_convert_date(store)
        # 373      if       proofed not = zero
        # 374               move  proofed  to  u-bin
        # 375               perform  zz060-Convert-Date
        # 376               go to next-1.            # GO TO class 4
        elif arithmetic.compare(store.batch.dates.proofed, _ZERO) != 0:
            store.maps03_ws.u_bin = cobol_move.move(
                store.batch.dates.proofed, _U_BIN
            )
            _zz060_convert_date(store)
        # 378      if       entered not = zero
        # 379               move  entered  to  u-bin
        # 380               perform  zz060-Convert-Date.
        #      NO transfer here - the fourth alternative falls through into
        #      `next-1.` on its own, which is why the chain above is an
        #      `if`/`elif` rather than four independent tests.
        elif arithmetic.compare(store.batch.dates.entered, _ZERO) != 0:
            store.maps03_ws.u_bin = cobol_move.move(
                store.batch.dates.entered, _U_BIN
            )
            _zz060_convert_date(store)

        # 382  next-1.
        #      The three Class-2 transfers above and the fall-through all land
        #      here.
        if _gl060a_next_1(store):
            # 413      if       lin  <  ws-21-lines
            # 414               go to  loop.
            # GO TO class 1 - see `_gl060a_next_1` and question Q-70e.
            continue

        # 418  screen-option.
        #      Reached by falling through from the prompt at
        #      [general/gl070.cbl:L416].
        if _gl060a_screen_option(store):
            # 423      if       ws-reply = "X"  or  "x"
            # 424               go to  end-report.
            # GO TO class 2 - out of the loop, to the label whose close follows.
            break

        # 427      go       to  loop.
        # GO TO class 1, reached after `perform screen-clear`
        # [general/gl070.cbl:L426].
        continue

    # 435  end-report.
    #      THE POST-LOOP BLOCK the two Class-2 transfers above break to. Placing
    #      it here rather than inside the loop is what keeps `GL-Batch-Close`
    #      [general/gl070.cbl:L440] reachable on both exits - the mis-split the
    #      Agent Action Plan warns silently drops end-of-run processing.
    _gl060a_end_report(store)


def _gl060a_next_1(store: _WorkingStorage) -> bool:
    """`next-1.` in `gl060a` - print one batch's two report lines.

    [general/gl070.cbl:L382]. Reached four ways: the three Class-2 `go to next-1`
    transfers of the date-precedence chain, and the fall-through when the fourth
    alternative is taken or when all four dates are zero.

    Presentation from beginning to end, with ONE retained value - `lin`
    [general/gl070.cbl:L411] - because it is an operand of the control transfer
    this function reports on.

    THE STATUS COLUMN IS FOUR INDEPENDENT `if`s [general/gl070.cbl:L387-L398],
    not a chain, and they are reproduced as four. `03  Cleared-Status  pic 9.`
    [copybooks/wsbatch.cob:L29] has condition names for only 0, 1 and 2
    [copybooks/wsbatch.cob:L30-L32], so a closed batch carrying any other value
    matches none of them and the column still shows the PREVIOUS batch's status.
    That carry-over is frozen behaviour; adding an `else` would invent the
    validation rule R-3 forbids.

    Returns:
        `True` when the loop is to be re-entered without prompting, i.e. when
        `lin < ws-21-lines` [general/gl070.cbl:L413]; `False` when the report has
        filled the screen and the prompt is reached.

        ANSWERING QUESTION Q-70e: with the frozen source as it stands this is
        ALWAYS `False`. `ws-21-lines` keeps its `value zero`
        [general/gl070.cbl:L165] because the statement that would have set it,
        `subtract 3 from ws-lines giving ws-21-lines`
        [general/gl070.cbl:L262], IS COMMENTED OUT; and `lin` is at least ten by
        the time the test is reached, being seven [general/gl070.cbl:L340] plus
        three [general/gl070.cbl:L411]. Ten is not less than zero. The comparison
        is nonetheless computed rather than hard-coded, so that the proof is
        checkable and so that the behaviour would follow the source if the
        commented-out line were ever restored.

    Args:
        store: the run's working storage.
    """
    # 385      move     ws-date  to  l6-date.
    #      The date the precedence chain converted, or the carried-over one.

    # 387      if       status-open
    # 388               move  "Open"  to  l6-status.
    if condition_names.is_status_open(store.batch.batch_status):
        store.status_label = _STATUS_LABEL_OPEN

    # 390      if       status-closed
    # 391        and    waiting
    # 392               move  "Waiting"  to  l6-status.
    if condition_names.is_status_closed(
        store.batch.batch_status
    ) and condition_names.is_waiting(store.batch.cleared_status):
        store.status_label = _STATUS_LABEL_WAITING

    # 393      if       status-closed
    # 394        and    processed
    # 395               move  "Processed"  to  l6-status.
    if condition_names.is_status_closed(
        store.batch.batch_status
    ) and condition_names.is_processed(store.batch.cleared_status):
        store.status_label = _STATUS_LABEL_PROCESSED

    # 396      if       status-closed
    # 397        and    archived
    # 398               move  "Archived"  to  l6-status.
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
    _LOG.info(
        "%s  %s  %s  %s  %s  %s  %s",
        store.ledger_label,
        store.batch.ws_batch_key.ws_batch_nos,
        store.status_label,
        store.ws.ws_date,
        store.batch.items,
        store.batch.amounts.input_gross,
        store.batch.amounts.input_vat,
    )
    _LOG.info(
        "%s  %s  %s  %s  %s  %s  %s",
        "",
        "",
        "",
        "",
        store.batch.items,
        store.batch.amounts.actual_gross,
        store.batch.amounts.actual_vat,
    )

    # 411      add      3  to  lin.
    #      Two printed lines plus a blank. Plain integer addition on a `pic 99`
    #      screen-position field, not on a posted figure: no `FieldDescriptor`
    #      exists for it because it is not a record field, and it can never
    #      overflow within a report page because the page test bounds it.
    store.lin = store.lin + _REPORT_LINES_PER_BATCH

    # 413      if       lin  <  ws-21-lines
    # 414               go to  loop.
    #      Reported to the caller; the transfer itself is issued there so that
    #      every `GO TO` stays visible at its own loop.
    return arithmetic.compare(store.lin, store.ws_21_lines) < 0


def _gl060a_screen_option(store: _WorkingStorage) -> bool:
    """`screen-option.` in `gl060a` - the paging prompt.

    [general/gl070.cbl:L418]. Reached by falling through from the prompt display
    at [general/gl070.cbl:L416], and re-entered by nothing: `go to loop`
    [general/gl070.cbl:L427] returns to the report loop, not to here.

        421      accept   ws-reply at line ws-22-lines col 46 ...
        423      if       ws-reply = "X"  or  "x"
        424               go to  end-report.
        426      perform  screen-clear.
        427      go       to  loop.

    THE PAUSE IS DROPPED, THE TRANSFER IS PRESERVED. The prompt gates no database
    write - `gl060a` opens the batch file for input, reads it and closes it, and
    performs no write, rewrite or delete anywhere - so the operator's answer
    cannot change table state, and a headless run may take the continue-paging
    branch unconditionally. That is what this function returning `False` means.

    ANSWERING QUESTION Q-70d: an early "X" exit changes nothing a table dump can
    see. Both branches converge on `GL-Batch-Close` [general/gl070.cbl:L440]; the
    only difference is how many batches got logged and how many `zz060`
    conversions ran, and `zz060` can only ever DEFAULT `Date-Form` to one
    [general/gl070.cbl:L553-L554] - a change the very first conversion, in
    `init01` [general/gl070.cbl:L270], has already made before this section is
    reached. Choosing to page on therefore reports MORE, never differently.

    Returns:
        `True` if the report is to stop early, i.e. the operator typed "X";
        `False` to clear the page and carry on. Always `False` headless.

    Args:
        store: the run's working storage.
    """
    # 421      accept   ws-reply at line ws-22-lines col 46 with foreground-color 6.
    #      Omission 4: the terminal read is dropped. The reply keeps the value it
    #      would have had if the operator had asked for the next screen.

    # 423      if       ws-reply = "X"  or  "x"
    # 424               go to  end-report.
    #      Not taken headless, per the reasoning above.

    # 426      perform  screen-clear.
    _gl060a_screen_clear(store)
    return False


def _gl060a_screen_clear(store: _WorkingStorage) -> None:
    """`screen-clear.` in `gl060a` - start a new report page.

    [general/gl070.cbl:L429]. Performed from exactly one place,
    [general/gl070.cbl:L426].

        432      move     7  to  lin.
        433      display  space at curs with erase eos.

    THE CURSOR RESET IS RETAINED, THE ERASE IS NOT. `lin` going back to seven is
    the whole of this paragraph's non-presentation effect, because it is what
    makes the page test at [general/gl070.cbl:L413] able to be true again.

    Note that `y`, the page number moved to `l1-page` at
    [general/gl070.cbl:L334-L335], is NEVER incremented - not here and not
    anywhere else in the program - so every page of this report claims to be
    page one. Presentation only, and therefore recorded rather than corrected
    (rule R-4).

    Args:
        store: the run's working storage.
    """
    # 432      move     7  to  lin.
    store.lin = _REPORT_FIRST_BODY_LINE

    # 433      display  space at curs with erase eos.
    #      Omission 1: a screen erase with no database effect.


def _gl060a_end_report(store: _WorkingStorage) -> None:
    """`end-report.` in `gl060a` - close the batch file.

    [general/gl070.cbl:L435]. The target of both Class-2 transfers in this
    section, [general/gl070.cbl:L349] and [general/gl070.cbl:L424].

        438      display  "Type return to exit." at line ws-22-lines col 01.
        439      accept   ws-reply at line ws-22-lines col 22 ...
        440      perform  GL-Batch-Close.

    Args:
        store: the run's working storage.
    """
    # 438      display  "Type return to exit." at line ws-22-lines col 01.
    # 439      accept   ws-reply at line ws-22-lines col 22 with foreground-color 2.
    #      Omission 4, second half: a pure acknowledgement pause. It transfers
    #      control nowhere and gates nothing, so it is dropped ENTIRELY - not
    #      even logged, since its only purpose was to hold a terminal.

    # 440      perform  GL-Batch-Close.                  *> close    batch-file.
    facade.gl_batch_close(store.batch_ctx)


def _gl060a_main_exit(store: _WorkingStorage) -> None:
    """`main-exit.` in `gl060a` - the section's trailing exit.

    [general/gl070.cbl:L442]. The THIRD paragraph in this file named `main-exit.`
    `exit section.` returns to [general/gl070.cbl:L288], which then raises the
    abort at [general/gl070.cbl:L289].

    Args:
        store: the run's working storage, unused.
    """
    # 442  main-exit.   exit section.
    del store
    return


#  gl071b section.  -  PHASE 2, THE REJECTOR PASS  [general/gl070.cbl:L444]


def _gl071b(store: _WorkingStorage) -> None:
    """`gl071b section.` - phase 2, transaction pre-process.

    [general/gl070.cbl:L444]. Performed from [general/gl070.cbl:L293], which is
    reached only when phase 1 left the detector clear.

    THIS IS NOT PHASE 1 WITH EXTRA CONDITIONS, and the difference is the whole
    reason the two passes exist. Phase 1 used `status-open` as a DETECTOR: it
    read every batch of the cycle, and an open one raised a flag that stopped the
    run. Phase 2 uses `status-open`, `not waiting` and `not gl-batch` as a
    REJECTOR: a batch matching any of them is SKIPPED and the pass carries on
    with the next. Same condition name, opposite purpose. Merging the two would
    either abort on a batch phase 2 means to skip, or silently pre-process a
    batch phase 1 means to abort on.

    ITS OUTPUT IS THE `pre-trans` WORK SEQUENCE AND NOTHING ELSE. `open output`
    [general/gl070.cbl:L447] TRUNCATES that sequence before the first batch, so a
    rerun of the cycle starts from an empty one rather than appending to the
    previous run's rows - which is what lets two runs under the same pinned date
    produce byte-identical output.

    Args:
        store: the run's working storage.
    """
    # 447      open     output  pre-trans.
    #      TRUNCATION, not append. `OPEN OUTPUT` on a sequential file discards
    #      whatever the file held.
    store.work_files.pre_trans.open_output()

    # 448      perform  GL-Batch-Open-Input.            *> open input batch-file.
    facade.gl_batch_open_input(store.batch_ctx)

    # 450  loop.
    _gl071b_loop(store)

    # 475  main-exit.   exit section.
    _gl071b_main_exit(store)


def _gl071b_loop(store: _WorkingStorage) -> None:
    """`loop.` in `gl071b` - pre-process one accepted batch per pass.

    [general/gl070.cbl:L450]. The THIRD paragraph in this file named `loop.`

        453      perform  GL-Batch-Read-Next.
        454      if       fs-reply = 10
        455               go to  end-run.
        457      if       bcycle not = scycle
        458               go to  loop.
        460      if       status-open
        461            or not waiting
        462            or not gl-batch
        463               go to  loop.
        465      perform  gl071b-pre-process.
        466      perform  GL-Posting-Close.
        467      go       to loop.

    THE REJECTOR IS THREE CONDITIONS JOINED BY `OR`, so ANY ONE of them skips the
    batch: it must be closed, it must be waiting rather than already processed or
    archived, and it must belong to the General Ledger rather than to Purchase or
    Sales [copybooks/wsbatch.cob:L16-L18]. Reading it as `AND` would pre-process
    batches from the other two ledgers into the General Ledger's work sequence.

    THE OPEN AND THE CLOSE OF THE POSTING FILE ARE DELIBERATELY ASYMMETRIC.
    `GL-Posting-Open-Input` is performed by the INNER section
    [general/gl070.cbl:L481], once per accepted batch; `GL-Posting-Close` is
    performed HERE, in the OUTER one [general/gl070.cbl:L466], also once per
    accepted batch, but after the inner section has returned. The pairing is
    therefore one open to one close - it just spans two sections. Hoisting the
    open out or pushing the close in would change how many times each verb runs
    on a run where some batches are rejected, because a REJECTED batch reaches
    neither statement.

    Args:
        store: the run's working storage.
    """
    while True:
        # 453      perform  GL-Batch-Read-Next.
        facade.gl_batch_read_next(store.batch_ctx)

        # 454      if       fs-reply = 10
        # 455               go to  end-run.
        # GO TO class 2 - `end-run.` [general/gl070.cbl:L469] is followed by the
        # `close pre-trans` at [general/gl070.cbl:L472] and the batch close at
        # [general/gl070.cbl:L473], so `break` plus the post-loop block. THE
        # WORK SEQUENCE'S CLOSE HANGS OFF THIS SPLIT: get it wrong and the
        # sequence `gl071` sorts is never finalised.
        if _at_end(store):
            break

        # 457      if       bcycle not = scycle
        # 458               go to  loop.
        # GO TO class 1 - the accounting-cycle filter, third and last occurrence.
        if _cycle_differs(store):
            continue

        # 460      if       status-open
        # 461            or not waiting
        # 462            or not gl-batch
        # 463               go to  loop.
        # GO TO class 1 - THE REJECTOR. Any one of the three skips the batch.
        if (
            condition_names.is_status_open(store.batch.batch_status)
            or not condition_names.is_waiting(store.batch.cleared_status)
            or not condition_names.is_gl_batch(
                store.batch.ws_batch_key.ws_ledger
            )
        ):
            continue

        # 465      perform  gl071b-pre-process.
        _gl071b_pre_process(store)

        # 466      perform  GL-Posting-Close.                 *> close posting-file.
        #      The outer half of the asymmetric pair - see this function's
        #      docstring. It is reached once per ACCEPTED batch and never for a
        #      rejected one.
        facade.gl_posting_close(store.posting_ctx)

        # 467      go       to loop.
        # GO TO class 1 - the unconditional loop-back that ends the paragraph.
        continue

    # 469  end-run.
    #      THE POST-LOOP BLOCK. Only one transfer targets it, the at-end break
    #      above, but the two statements it carries are the ones that make the
    #      work sequence usable by the next phase.
    _gl071b_end_run(store)


def _gl071b_end_run(store: _WorkingStorage) -> None:
    """`end-run.` in `gl071b` - close the work sequence and the batch file.

    [general/gl070.cbl:L469]. The SECOND paragraph in this file named `end-run.`

        472      close    pre-trans.                       *> batch-file
        473      perform  GL-Batch-Close.

    The trailing comment on [general/gl070.cbl:L472] reads `*> batch-file`, which
    is a stale annotation - the statement closes `pre-trans`, and the batch file
    is closed by the NEXT line. Recorded rather than tidied: the frozen source is
    read-only, and a reader comparing the two files should be able to see that
    the discrepancy was noticed.

    Args:
        store: the run's working storage.
    """
    # 472      close    pre-trans.
    store.work_files.pre_trans.close()

    # 473      perform  GL-Batch-Close.
    facade.gl_batch_close(store.batch_ctx)


def _gl071b_main_exit(store: _WorkingStorage) -> None:
    """`main-exit.` in `gl071b` - the section's trailing exit.

    [general/gl070.cbl:L475]. The FOURTH paragraph in this file named
    `main-exit.` `exit section.` returns to [general/gl070.cbl:L293], the last
    statement of `menu-input2.`, and the program then falls into
    [general/gl070.cbl:L295] and `goback`.

    Args:
        store: the run's working storage, unused.
    """
    # 475  main-exit.   exit section.
    del store
    return


#  gl071b-pre-process section.  -  THE DOUBLE-ENTRY EXPLOSION
#  [general/gl070.cbl:L477]


def _gl071b_pre_process(store: _WorkingStorage) -> None:
    """`gl071b-pre-process section.` - explode one batch into work records.

    [general/gl070.cbl:L477]. Performed from exactly one place,
    [general/gl070.cbl:L465], once per ACCEPTED batch.

    THIS IS THE HEART OF PHASE 2. Each posting record of the batch becomes TWO OR
    THREE `pre-trans` records: a debit leg, a credit leg, and - only when the
    posting carries VAT - a VAT leg. The legs are what make the General Ledger
    balance, because the credit leg is stored NEGATED
    [general/gl070.cbl:L517] and so the three legs of one posting sum to the VAT
    the posting bore, or to zero when it bore none.

    THE ORDER THE LEGS ARE APPENDED IN IS LOAD-BEARING, and not only because a
    sequence has an order. `gl071` sorts this output on
    `sort-batch, sort-ac, sort-pc, sort-post` [general/gl071.cbl:L173-L176], and
    TWO LEGS OF ONE POSTING CAN PRODUCE AN IDENTICAL KEY - a posting whose debit
    and credit accounts and profit centres are the same, which the frozen program
    does not forbid. The sort must therefore be stable and the insertion order
    here decides which of the tied legs `gl072` sees first.

    Args:
        store: the run's working storage.
    """
    # 480      move     WS-Batch-Nos  to  pre-batch.
    #      QUESTION Q-70b: THIS STORE IS INERT. Every path that reaches a `write`
    #      passes through [general/gl070.cbl:L495], which overwrites `pre-batch`
    #      from the posting record's own `batch` before the first leg is
    #      appended; and no path writes without passing through it. The statement
    #      is reproduced anyway, because "inert" is a conclusion about the code as
    #      it stands and rule R-3 does not permit removing a store on the
    #      strength of it.
    store.pre_trans_record.pre_batch = cobol_move.move(
        store.batch.ws_batch_key.ws_batch_nos,
        _PRE["pre_batch"],
        sending_field=_BATCH_NOS,
    )

    # 481      perform  GL-Posting-Open-Input.            *> open input posting-file.
    #      The INNER half of the asymmetric pair. Its close is at
    #      [general/gl070.cbl:L466], in the calling section.
    facade.gl_posting_open_input(store.posting_ctx)

    # 483  loop.
    _gl071b_pre_process_loop(store)

    # 535  main-exit.   exit section.
    _gl071b_pre_process_main_exit(store)


def _gl071b_pre_process_loop(store: _WorkingStorage) -> None:
    """`loop.` in `gl071b-pre-process` - explode one posting per pass.

    [general/gl070.cbl:L483]. The FOURTH and last paragraph in this file named
    `loop.`

    THE THREE `write pre-trans-record` STATEMENTS - [general/gl070.cbl:L508],
    [general/gl070.cbl:L519] and [general/gl070.cbl:L532] - ALL NAME THE SAME
    RECORD AREA. In COBOL that is unremarkable: `WRITE` copies the record area
    out to the file, so mutating the area and writing again appends a second,
    different row. In Python the same shape is a trap, because appending the same
    mutable object three times would leave the sequence holding three references
    to one record and therefore three copies of whatever the LAST leg left
    behind. It is handled at the verb rather than here: the work-file `write`
    snapshots the record area on the way in, which is exactly the semantics of
    the COBOL statement. This function consequently keeps ONE record area and
    mutates it between writes, as the compiled program does.

    THE HEADER FIELDS ARE SET ONCE AND CARRY OVER.
    [general/gl070.cbl:L495-L499] fill `pre-batch`, `pre-post`, `pre-code`,
    `pre-date` and `pre-legend`. The credit leg [general/gl070.cbl:L510-L515] and
    the VAT leg [general/gl070.cbl:L525-L527] overwrite ONLY `pre-ac`, `pre-pc`
    and `pre-amount`. Re-populating the header for each leg would look tidier and
    would produce identical rows here - but it would be a second place where the
    header is decided, and the moment the frozen program's header and its legs
    disagreed the copy would hide it.

    THE TWO VAT-SIDE TESTS NAME OPPOSITE SIDES. The debit leg absorbs the VAT
    when the VAT sits on the CREDIT side [general/gl070.cbl:L503]; the credit leg
    absorbs it when the VAT sits on the DEBIT side [general/gl070.cbl:L512]. That
    is not a transcription slip in the frozen source and it is not one here: the
    leg that does NOT carry the VAT account must carry the gross, so that the VAT
    leg's own amount completes the entry.

    ONLY THE CREDIT LEG IS UNCONDITIONALLY NEGATED [general/gl070.cbl:L517]. The
    debit leg never is. The VAT leg is negated only when the VAT sits on the
    credit side [general/gl070.cbl:L529-L530].

    Args:
        store: the run's working storage.
    """
    while True:
        # 486      perform  GL-Posting-Read-Next.
        facade.gl_posting_read_next(store.posting_ctx)

        # 487      if       fs-reply = 10
        # 488               go to  main-exit.
        # GO TO class 3 - `return`, NOT `break`. The target
        # [general/gl070.cbl:L535] is this SECTION'S trailing exit label and
        # carries no statement of its own; there is no post-loop work to place
        # after the loop, and the posting file's close happens in the CALLING
        # section [general/gl070.cbl:L466]. Treating this as a Class 2 and
        # inventing a post-loop block would close the posting file twice.
        if _at_end(store):
            return

        # 490      if       WS-Post-Key = zero
        # 491               go to  loop.
        # GO TO class 1 - the unset-key filter.
        if _post_key_is_zero(store):
            continue

        # 492      if       batch  not = WS-Batch-Nos
        # 493               go to  loop.
        # GO TO class 1 - the posting file is walked SEQUENTIALLY from its start
        # for every batch, so every posting of every other batch is read and
        # skipped here. That is the frozen access pattern and it is not to be
        # narrowed into a keyed read; see the note on performance in the module
        # docstring.
        if (
            arithmetic.compare(
                store.posting.ws_post_key.batch,
                store.batch.ws_batch_key.ws_batch_nos,
            )
            != 0
        ):
            continue

        #  ---- THE COMMON HEADER, SET ONCE PER POSTING ----

        # 495      move     batch        to  pre-batch.
        store.pre_trans_record.pre_batch = cobol_move.move(
            store.posting.ws_post_key.batch,
            _PRE["pre_batch"],
            sending_field=_POST_KEY["Batch"],
        )

        # 496      move     post-number  to  pre-post.
        store.pre_trans_record.pre_post = cobol_move.move(
            store.posting.ws_post_key.post_number,
            _PRE["pre_post"],
            sending_field=_POST_KEY["Post-Number"],
        )

        # 497      move     post-code in WS-Posting-Record   to  pre-code.
        # ANOMALY A-21 [general/gl070.cbl:L497] - field-name collision across
        # three posting copybooks forces a QUALIFIED reference. `gl070` copies
        # `wspost.cob` [general/gl070.cbl:L128] alongside the work-record layouts
        # declared in its own FILE SECTION [general/gl070.cbl:L108-L116], and
        # more than one of them offers a `post-code`, so an unqualified reference
        # will not compile. Note the qualifier keyword here is `in`, while the
        # two sites below use `of` - the same anomaly, spelled two ways in one
        # paragraph. Reproduced deliberately per R-4; DO NOT FIX. In Python the
        # collision cannot arise, because each record is its own object; the
        # reproduction is this comment plus the RECORD-QUALIFIED attribute access
        # `store.posting.post_code`, never a bare local of the same name, so a
        # reader can still see which record the field came from.
        store.pre_trans_record.pre_code = cobol_move.move(
            store.posting.post_code,
            _PRE["pre_code"],
            sending_field=_POST["Post-Code"],
        )

        # 498      move     post-date    to  pre-date.
        #      `pic x(8)` to `pic x(8)` [copybooks/wspost.cob:L18],
        #      [general/gl070.cbl:L111] - equal widths, so neither truncation nor
        #      padding applies. NO DATE ARITHMETIC AND NO REFORMATTING: the eight
        #      characters are carried across as they stand, in whatever form the
        #      entry program stored them.
        store.pre_trans_record.pre_date = cobol_move.move(
            store.posting.post_date,
            _PRE["pre_date"],
            sending_field=_POST["Post-Date"],
        )

        # 499      move     post-legend  to  pre-legend.
        store.pre_trans_record.pre_legend = cobol_move.move(
            store.posting.post_legend,
            _PRE["pre_legend"],
            sending_field=_POST["Post-Legend"],
        )

        #  ---- LEG 1 of 3:  THE DEBIT LEG  ----

        # 501      move     post-dr      to  pre-ac.
        store.pre_trans_record.pre_ac = cobol_move.move(
            store.posting.post_dr,
            _PRE["pre_ac"],
            sending_field=_POST["Post-DR"],
        )

        # 502      move     dr-pc        to  pre-pc.
        store.pre_trans_record.pre_pc = cobol_move.move(
            store.posting.dr_pc,
            _PRE["pre_pc"],
            sending_field=_POST["DR-PC"],
        )

        # 503      if       post-vat-side = "CR"
        # 504               add  post-amount  vat-amount  giving  pre-amount
        # 505      else
        # 506               move post-amount  to  pre-amount.
        #      The debit leg carries the GROSS when the VAT is on the credit side.
        #      `ADD ... GIVING` with two sources: summed at intermediate precision
        #      and quantized ONCE into the receiving field, which is what
        #      `add_giving` does and what summing pairwise would not.
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

        # 508      write    pre-trans-record.
        store.work_files.pre_trans.write(store.pre_trans_record)

        #  ---- LEG 2 of 3:  THE CREDIT LEG  ----
        #  NO HEADER MOVE HERE. `pre-batch`, `pre-post`, `pre-code`, `pre-date`
        #  and `pre-legend` carry over from [general/gl070.cbl:L495-L499].

        # 510      move     post-cr      to  pre-ac.
        store.pre_trans_record.pre_ac = cobol_move.move(
            store.posting.post_cr,
            _PRE["pre_ac"],
            sending_field=_POST["Post-CR"],
        )

        # 511      move     cr-pc        to  pre-pc.
        store.pre_trans_record.pre_pc = cobol_move.move(
            store.posting.cr_pc,
            _PRE["pre_pc"],
            sending_field=_POST["CR-PC"],
        )

        # 512      if       post-vat-side = "DR"
        # 513               add  post-amount  vat-amount  giving  pre-amount
        # 514      else
        # 515               move post-amount  to  pre-amount.
        #      THE OPPOSITE SIDE to the debit leg's test at
        #      [general/gl070.cbl:L503]. See the docstring: deliberate, and
        #      reproduced.
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

        # 517      multiply pre-amount  by  -1  giving  pre-amount.
        #      UNCONDITIONAL, and the only unconditional negation in the program.
        #      The receiving field is signed - `pre-amount pic s9(8)v99`
        #      [general/gl070.cbl:L115] - so the sign survives the store. No
        #      `ROUNDED`, hence truncation, which for a sign flip at the field's
        #      own scale changes nothing but is stated by the primitive anyway.
        store.pre_trans_record.pre_amount = arithmetic.multiply_by_giving(
            store.pre_trans_record.pre_amount,
            -1,
            _PRE["pre_amount"],
        )

        # 519      write    pre-trans-record.
        store.work_files.pre_trans.write(store.pre_trans_record)

        #  ---- LEG 3 of 3:  THE VAT LEG, CONDITIONAL  ----

        # 521      if       vat-ac of WS-Posting-Record = zero
        # 522            or vat-amount = zero
        # 523               go to  loop.
        # GO TO class 1 - and note what it skips: not merely the VAT leg but the
        # REST OF THE POSTING'S PROCESSING, there being nothing after the leg but
        # the loop-back at [general/gl070.cbl:L533]. The gate is `OR`, so EITHER
        # a zero VAT account OR a zero VAT amount suppresses the leg; reading it
        # as `AND` would emit a VAT leg against account zero.
        #
        # AND IT CAN LEAVE THE ENTRY UNBALANCED, which is frozen behaviour and
        # not to be corrected. The gate suppresses only THIS leg; the debit and
        # credit legs have already absorbed the VAT through their own tests at
        # [general/gl070.cbl:L503] and [general/gl070.cbl:L512]. So a posting
        # carrying a VAT AMOUNT but no VAT ACCOUNT emits two legs summing to the
        # VAT rather than to zero - measured: side "CR" with 100.00 and 20.00
        # and no VAT account gives 120.00 and -100.00. Reproduced per R-4.
        #
        # ANOMALY A-21 [general/gl070.cbl:L521] - the same collision as at
        # [general/gl070.cbl:L497], here spelled with the `of` qualifier instead
        # of `in`. Reproduced deliberately per R-4; DO NOT FIX.
        if (
            arithmetic.compare(store.posting.vat_ac, _ZERO) == 0
            or arithmetic.compare(store.posting.vat_amount, _ZERO) == 0
        ):
            continue

        # 525      move     vat-ac of WS-Posting-Record  to  pre-ac.
        # ANOMALY A-21 [general/gl070.cbl:L525] - third and last site of the
        # collision, again with the `of` qualifier. Reproduced deliberately per
        # R-4; DO NOT FIX.
        store.pre_trans_record.pre_ac = cobol_move.move(
            store.posting.vat_ac,
            _PRE["pre_ac"],
            sending_field=_POST["Vat-AC"],
        )

        # 526      move     vat-pc           to      pre-pc.
        store.pre_trans_record.pre_pc = cobol_move.move(
            store.posting.vat_pc,
            _PRE["pre_pc"],
            sending_field=_POST["Vat-PC"],
        )

        # 527      move     vat-amount       to      pre-amount.
        store.pre_trans_record.pre_amount = cobol_move.move(
            store.posting.vat_amount,
            _PRE["pre_amount"],
            sending_field=_POST["Vat-Amount"],
        )

        # 529      if       post-vat-side = "CR"
        # 530               multiply  pre-amount  by  -1 giving pre-amount.
        #      CONDITIONAL, unlike the credit leg's flip at
        #      [general/gl070.cbl:L517]: the VAT leg is negated only when the VAT
        #      sits on the credit side, because that is the side it must offset.
        if store.posting.post_vat_side == _VAT_SIDE_CREDIT:
            store.pre_trans_record.pre_amount = arithmetic.multiply_by_giving(
                store.pre_trans_record.pre_amount,
                -1,
                _PRE["pre_amount"],
            )

        # 532      write    pre-trans-record.
        store.work_files.pre_trans.write(store.pre_trans_record)

        # 533      go       to loop.
        # GO TO class 1 - the unconditional loop-back that ends the paragraph.
        continue


def _gl071b_pre_process_main_exit(store: _WorkingStorage) -> None:
    """`main-exit.` in `gl071b-pre-process` - the section's trailing exit.

    [general/gl070.cbl:L535]. The FIFTH and last paragraph in this file named
    `main-exit.` It carries no statement other than `exit section.`, which is
    precisely why [general/gl070.cbl:L487-L488] is a Class-3 `return` and not a
    Class-2 `break`. `exit section.` returns to [general/gl070.cbl:L466], which
    then closes the posting file.

    Args:
        store: the run's working storage, unused.
    """
    # 535  main-exit.   exit section.
    del store
    return


#  THE DATE SECTIONS  -  zz060, zz070 AND THE WRAPPER  [general/gl070.cbl:L538]


def _zz060_convert_date(store: _WorkingStorage) -> None:
    """`zz060-Convert-Date section.` - a binary date, reformatted for the report.

    [general/gl070.cbl:L538]. Performed four times, once per alternative of the
    open-batch report's date-precedence chain: [general/gl070.cbl:L365],
    [general/gl070.cbl:L370], [general/gl070.cbl:L375] and
    [general/gl070.cbl:L380]. Input is `u-bin`, output is `ws-date`.

    THE BODY IS CONSOLIDATED, NOT REWRITTEN. This section is repeated
    near-identically in six of the in-scope programs, and its body differs
    between them by ONE TOKEN: the name of the wrapper it performs. `gl070` and
    `gl051` perform one named `maps03` [general/gl070.cbl:L547]; `sl060`,
    `sl100`, `pl060` and `pl100` perform one named `maps04`. That is why the
    wrapper is a required argument of the consolidated implementation and why
    THIS module passes its own `_maps03` - so the traceability reads back to the
    name this program actually uses.

    IT MUTATES THE SYSTEM RECORD, and that is not presentation. `if Date-Form =
    zero move 1 to Date-Form.` [general/gl070.cbl:L553-L554] defaults a
    `SYSTEM-REC` column [copybooks/wssystem.cob:L128], and `SYSTEM-REC` is a
    table the state diff inspects. The consolidated implementation returns the
    effective form and the store back into the system record happens HERE,
    because the frozen program's own store is here.

    Args:
        store: the run's working storage. `maps03_ws.u_bin` is the input;
            `ws.ws_date` and `system_record`'s `Date-Form` are the outputs.
    """
    # 547      perform  maps03.
    # 548      if       u-date = spaces
    # 549               move spaces to ws-Date
    # 550               go to zz060-Exit.               # GO TO class 3
    # 551      move     u-date to ws-date.
    # 553      if       Date-Form = zero
    # 554               move 1 to Date-Form.
    # 555      if       Date-UK
    # 556               go to zz060-Exit.               # GO TO class 3
    # 557      if       Date-USA
    # 558-560           swap the day and month through ws-swap
    # 561               go to zz060-Exit.               # GO TO class 3
    # 565-568  otherwise rebuild the text in International order
    # 570  zz060-Exit.  exit section.
    #      All four transfers are Class 3 - the section's trailing exit, no work
    #      after it - and all four live inside the consolidated implementation.
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
    linkage parameter [general/gl070.cbl:L243], set by the menu shell from the
    single clock read in the whole call chain, and this migration receives it as
    an argument (rule R-6).

    Args:
        store: the run's working storage. `to_day` is the input; `ws.ws_date` and
            `system_record`'s `Date-Form` are the outputs.
    """
    # 581      move     to-day to ws-date.
    # 583      if       Date-Form = zero
    # 584               move 1 to Date-Form.
    # 585      if       Date-UK
    # 586               go to zz070-Exit.               # GO TO class 3
    # 587      if       Date-USA
    # 588-590           swap the day and month through ws-swap
    # 591               go to zz070-Exit.               # GO TO class 3
    # 595-598  otherwise rebuild the text in International order
    # 600  zz070-Exit.  exit section.
    #      Both transfers are Class 3, and both live inside the consolidated
    #      implementation - which is byte-identical across all ten carriers of
    #      this section, so consolidating it loses nothing.
    store.system_record.system_data_block.date_form = (
        dates_zz070_convert_date(
            store.ws,
            store.to_day,
            store.system_record.system_data_block.date_form,
        )
    )


def _maps03(maps03_ws: Maps03Ws) -> None:
    """`maps03 section.` - the wrapper around the date module.

    [general/gl070.cbl:L603]. Three lines: `call "maps04" using maps03-ws.`
    [general/gl070.cbl:L606], the exit label, and `exit section.`

    ANOMALY A-22 [general/gl070.cbl:L603-L609] - THE WRAPPER IS NAMED AFTER THE
    INTERFACE COPYBOOK WHILE ITS EXIT IS NAMED AFTER THE CALLED PROGRAM. The
    section is `maps03`, taking its name from `wsmaps03.cob`
    [general/gl070.cbl:L125], which declares the linkage record it passes; the
    exit label three lines later is `maps04-exit` [general/gl070.cbl:L608],
    taking its name from `maps04`, the program it calls. Reproduced deliberately
    per R-4; DO NOT FIX. The reproduction is this function's name - `_maps03`,
    after the section - together with the traceability footer's entry for the
    exit label `maps04-exit`, so both halves of the inconsistency survive the
    migration and neither is quietly normalised.

    THE SAME DEFECT OCCURS TWICE IN THE CODEBASE. Its second occurrence is
    `general/gl051.cbl` at L1273 and L1278, which belongs to
    `gl051_batch_control_check.py`; the Agent Action Plan's anomaly register
    cites only the `gl070` one. Recorded here so the second is not mistaken for
    a new finding.

    NO COBOL IS CALLED (rule R-1). `call "maps04"` becomes a call into
    `acas_posting.dates`, which reimplements the date module natively - epoch,
    six-part reject test and all - rather than invoking it.

    Args:
        maps03_ws: `01  maps03-ws.` [copybooks/wsmaps03.cob:L6], mutated in
            place, exactly as a COBOL `CALL ... USING` mutates its argument.
    """
    # 606      call     "maps04"  using  maps03-ws.
    dates_maps03(maps03_ws)

    # 608  maps04-exit.
    # 609      exit     section.


#  THE PUBLIC ENTRY  -  THE `CALL "gl070" USING ...` CONTRACT


def run(
    ws_calling_data: WsCallingData,
    system_record: SystemRecord,
    to_day: str,
    file_defs: FileDefs,
    *,
    work_files: GeneralLedgerWorkFiles | None = None,
    file_access: FileAccess | None = None,
    dal_common: AcasDalCommonData | None = None,
    transport: object = None,
    states: Mapping[str, object] | None = None,
) -> GeneralLedgerWorkFiles:
    """Run `gl070` - General Ledger phase 1 batch check and phase 2 pre-process.

    THE FOUR POSITIONAL PARAMETERS ARE THE COBOL LINKAGE, IN ITS ORDER::

        procedure division using ws-calling-data
                                 system-record
                                 to-day
                                 file-defs.

    [general/gl070.cbl:L245-L248]. This is the General Ledger's four-parameter
    shape - the Sales and Purchase families add a fifth record and the IRS
    program takes a different three - and the order is preserved exactly so that
    a reviewer can diff this signature against those four lines.

    WHAT IT DOES, IN THE ORDER IT DOES IT:

    1. `init01` [general/gl070.cbl:L251] converts the run date, which DEFAULTS
       `System-Record.Date-Form` when that column is zero, and sets
       `File-Key-No`.
    2. Phase 1, `gl071a` [general/gl070.cbl:L300], reads every batch of the
       current cycle looking for one still OPEN.
    3. If it found one, the open-batch report `gl060a`
       [general/gl070.cbl:L325] is produced and `WS-Term-Code` IS SET TO FIVE.
       THE RUN THEN STOPS - see below.
    4. Otherwise phase 2, `gl071b` [general/gl070.cbl:L444], explodes every
       accepted batch into the `pre-trans` work sequence.

    THE ABORT IS THIS FUNCTION'S CONTRACT WITH ITS CALLER, and honouring it is
    not optional. `move 5 to ws-term-code` [general/gl070.cbl:L289] is tested by
    the menu shell at `general/general.cbl` L810-L811, `if ws-term-code = 5 go to
    display-menu.`, which returns to the menu WITHOUT running `gl071` or `gl072`.
    A caller that logs the value and carries on would post a cycle the frozen
    system refuses to post. Two details of the value itself matter and are the
    reason it must not be "simplified": the shell's other gate, at
    `general/general.cbl` L720-L721, is `if ws-term-code > 7`, which FIVE DOES
    NOT SATISFY, so the abort passes that test and is caught only by the `= 5`
    one; and `general/general.cbl` L714 zeroes `WS-Term-Code` before every call,
    so this function may not assume any incoming value and does not read one.

    IT WRITES NOTHING TO THE DATABASE. Six facade verbs are used - the batch
    file's open-input, read-next and close, and the posting file's - and not one
    write, rewrite or delete. The only mutations this program makes anywhere are
    `WS-Term-Code` on the abort path, `System-Record.Date-Form` when it was zero,
    `File-Key-No`, and the `pre-trans` work sequence, which is not a table.

    Args:
        ws_calling_data: `01  WS-Calling-Data.` [copybooks/wscall.cob:L6]. THE
            ABORT IS DELIVERED HERE, in `WS-Term-Code`
            [copybooks/wscall.cob:L10].
        system_record: `SYSTEM-REC`. `Scycle` [copybooks/wssystem.cob:L63] is
            read by all three passes over the batch file; `Date-Form`
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
        transport: the data-access layer's transport policy, forwarded verbatim
            to the posting handler. `None` leaves the handler's own default in
            force. The BATCH handler takes no such argument, so it is not
            offered one.
        states: the data-access layer's cursor states, forwarded verbatim to the
            posting handler on the same terms.

    Returns:
        The work-file set, so that a caller which let the default be created can
        hand the populated `pre-trans` sequence to `gl071`. The frozen program
        returns nothing - `goback` [general/gl070.cbl:L298] - and communicates
        through the file system instead; returning the set is the migration's
        equivalent of naming the same file in the next program's `SELECT`, and it
        adds no behaviour, the sequence being reachable through the argument too
        when one was passed.
    """
    resolved_work_files = (
        general_ledger_work_files() if work_files is None else work_files
    )
    resolved_file_access = FileAccess() if file_access is None else file_access
    resolved_dal_common = (
        AcasDalCommonData() if dal_common is None else dal_common
    )

    # `01  WS-Batch-Record.` and `01  WS-Posting-Record.` are WORKING-STORAGE of
    # the frozen program [general/gl070.cbl:L127-L128], not linkage: they are
    # created per run and are never visible to the caller.
    batch = GlBatchRecord()
    posting = WsPostingRecord()

    #  THE OPTIONS EACH FACADE CONTEXT MAY CARRY ARE NOT THE SAME, and the
    #  difference is the handlers', not this module's: the batch handler
    #  `acas007` accepts exactly the five positional records the facade passes
    #  it, while the posting handler `acas006` additionally accepts a transport
    #  policy and a cursor-state map. Forwarding this program's options to BOTH
    #  contexts would make every batch verb fail on an unexpected argument.
    posting_options: dict[str, object] = {}
    if transport is not None:
        posting_options["transport"] = transport
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
        # ONE record area for the whole run, reused between the three writes of
        # the double-entry explosion exactly as the FILE SECTION record area of
        # the frozen program is [general/gl070.cbl:L108-L116].
        pre_trans_record=PreTransRecord(),
        maps03_ws=Maps03Ws(),
        ws=WsDateFormats(),
        # `move zero to a.` [general/gl070.cbl:L283] resets the detector at the
        # head of the phase driver; it starts clear here so that the reset is a
        # reset and not the only initialisation.
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

    # 251  init01 section.
    #      The frozen program's entry. `goback` [general/gl070.cbl:L298] ends the
    #      run, and there is nothing after it, so `init01` returning is the whole
    #      of the program's control flow at this level.
    _init01(store)

    return store.work_files


# --- traceability ---
#
# gl070_transaction_pre_process.py  <-  general/gl070.cbl  (612 lines, frozen)
#
# The frozen program is READ-ONLY SPECIFICATION. Nothing under general/,
# copybooks/, common/, sales/, purchase/, irs/, stock/ or mysql/ is touched by
# this migration, not even to reformat a line.
#
#
# PROGRAM -> MODULE
# -----------------
# general/gl070.cbl  ->  acas_posting/programs/gl070_transaction_pre_process.py
#     PROGRAM-ID. gl070.               [general/gl070.cbl:L2]
#     AUTHOR.     Vincent B Coen.      [general/gl070.cbl:L3]
#     Phase 1 batch check + phase 2 transaction pre-process, WHOLE posting path.
#
#
# PARAGRAPH -> FUNCTION
# ---------------------
# Names are derived mechanically: lower-cased, hyphens to underscores, and
# SECTION-QUALIFIED because the labels are not unique - `loop.` occurs four
# times and `main-exit.` five.
#
#   COBOL label                     Line   Section              Python function
#   -----------                     ----   -------              ---------------
#   init01 section.                  251   init01               _init01
#   menu-input.                      274   init01               _init01_menu_input
#   menu-input2.                     281   init01               _init01_menu_input2
#   main-exit.                       295   init01               _init01_main_exit
#   gl071a section.                  300   gl071a               _gl071a
#   loop.                            305   gl071a               _gl071a_loop
#   end-run.                         318   gl071a               _gl071a_end_run
#   main-exit.                       323   gl071a               _gl071a_main_exit
#   gl060a section.                  325   gl060a               _gl060a
#   loop.                            344   gl060a               _gl060a_loop
#   next-1.                          382   gl060a               _gl060a_next_1
#   screen-option.                   418   gl060a               _gl060a_screen_option
#   screen-clear.                    429   gl060a               _gl060a_screen_clear
#   end-report.                      435   gl060a               _gl060a_end_report
#   main-exit.                       442   gl060a               _gl060a_main_exit
#   gl071b section.                  444   gl071b               _gl071b
#   loop.                            450   gl071b               _gl071b_loop
#   end-run.                         469   gl071b               _gl071b_end_run
#   main-exit.                       475   gl071b               _gl071b_main_exit
#   gl071b-pre-process section.      477   gl071b-pre-process   _gl071b_pre_process
#   loop.                            483   gl071b-pre-process   _gl071b_pre_process_loop
#   main-exit.                       535   gl071b-pre-process   _gl071b_pre_process_main_exit
#   zz060-Convert-Date section.      538   zz060-Convert-Date   _zz060_convert_date
#   zz060-Exit.                      570   zz060-Convert-Date   (inside acas_posting.dates.zz060_convert_date)
#   zz070-Convert-Date section.      573   zz070-Convert-Date   _zz070_convert_date
#   zz070-Exit.                      600   zz070-Convert-Date   (inside acas_posting.dates.zz070_convert_date)
#   maps03 section.                  603   maps03               _maps03            <- anomaly A-22
#   maps04-exit.                     608   maps03               (the exit of _maps03)  <- anomaly A-22
#
# Every one of the 28 labels above has a counterpart. Nothing was merged.
#
# NOT COBOL PARAGRAPHS, and named so they cannot be mistaken for them:
#   run                             the public entry; the `CALL "gl070" USING`
#                                   contract [general/gl070.cbl:L245-L248]
#   _WorkingStorage                 the run's WORKING-STORAGE and LINKAGE, passed
#                                   rather than held at module scope
#   _at_end                         `if fs-reply = 10`, spelled once for its four
#                                   sites  L309, L348, L454, L487
#   _cycle_differs                  `if bcycle not = scycle`, spelled once for its
#                                   three sites  L312, L351, L457
#   _post_key_is_zero               `if WS-Post-Key = zero`  L490, with the proof
#                                   that the member-wise test is the group test
#   _pre_trans_descriptors          the descriptor lookup; builds no descriptor
#
#
# STATEMENT -> CALL SITE
# ----------------------
# Data access - SIX facade verbs, entity-named because this program copies
# `Proc-ACAS-FH-Calls.cob` [general/gl070.cbl:L611] and therefore tests the
# reply INLINE; that copybook has no error-check paragraph:
#   L303  perform GL-Batch-Open-Input      -> facade.gl_batch_open_input     _gl071a
#   L308  perform GL-Batch-Read-Next       -> facade.gl_batch_read_next      _gl071a_loop
#   L321  perform GL-Batch-Close           -> facade.gl_batch_close          _gl071a_end_run
#   L342  perform GL-Batch-Open-Input      -> facade.gl_batch_open_input     _gl060a
#   L347  perform GL-Batch-Read-Next       -> facade.gl_batch_read_next      _gl060a_loop
#   L440  perform GL-Batch-Close           -> facade.gl_batch_close          _gl060a_end_report
#   L448  perform GL-Batch-Open-Input      -> facade.gl_batch_open_input     _gl071b
#   L453  perform GL-Batch-Read-Next       -> facade.gl_batch_read_next      _gl071b_loop
#   L466  perform GL-Posting-Close         -> facade.gl_posting_close        _gl071b_loop
#   L473  perform GL-Batch-Close           -> facade.gl_batch_close          _gl071b_end_run
#   L481  perform GL-Posting-Open-Input    -> facade.gl_posting_open_input   _gl071b_pre_process
#   L486  perform GL-Posting-Read-Next     -> facade.gl_posting_read_next    _gl071b_pre_process_loop
# NO WRITE, NO REWRITE, NO DELETE, and no handler module is imported. This
# program mutates no database table.
#
# The work sequence - `pre-trans`, which is a scratch file and not a table:
#   L447  open output pre-trans            -> work_files.pre_trans.open_output()  (TRUNCATES)
#   L508  write pre-trans-record           -> work_files.pre_trans.write(...)     leg 1, debit
#   L519  write pre-trans-record           -> work_files.pre_trans.write(...)     leg 2, credit
#   L532  write pre-trans-record           -> work_files.pre_trans.write(...)     leg 3, VAT
#   L472  close pre-trans                  -> work_files.pre_trans.close()
#
# Arithmetic - FOUR statements, and ZERO of them `ROUNDED`. Every store
# truncates, which is COBOL's default and this program's only behaviour:
#   L504  add post-amount vat-amount giving pre-amount
#                                          -> arithmetic.add_giving(...)      leg 1
#   L513  add post-amount vat-amount giving pre-amount
#                                          -> arithmetic.add_giving(...)      leg 2
#   L517  multiply pre-amount by -1 giving pre-amount
#                                          -> arithmetic.multiply_by_giving(...)  leg 2, UNCONDITIONAL
#   L530  multiply pre-amount by -1 giving pre-amount
#                                          -> arithmetic.multiply_by_giving(...)  leg 3, conditional
# Comparisons route through arithmetic.compare: L312, L351, L457 (cycle), L363,
# L368, L373, L378 (the date-precedence chain), L413 (the page test), L490 (the
# key), L492 (the batch), L521 and L522 (the VAT gate).
# The five `ROUNDED` sites of the whole in-scope cycle are elsewhere - gl051
# L791 and L796, gl080 L328, irs030 L1551 and L1562 - and none is here.
#
# Condition names - `88` levels, never a raw literal:
#   status-open      [copybooks/wsbatch.cob:L26]  -> condition_names.is_status_open
#                    L314 (detector), L387 (report), L460 (rejector)
#   status-closed    [copybooks/wsbatch.cob:L27]  -> condition_names.is_status_closed
#                    L390, L393, L396
#   waiting          [copybooks/wsbatch.cob:L30]  -> condition_names.is_waiting    L391, L461
#   processed        [copybooks/wsbatch.cob:L31]  -> condition_names.is_processed  L394
#   archived         [copybooks/wsbatch.cob:L32]  -> condition_names.is_archived   L397
#   gl-batch         [copybooks/wsbatch.cob:L16]  -> condition_names.is_gl_batch   L354, L462
#   pl-batch         [copybooks/wsbatch.cob:L17]  -> condition_names.is_pl_batch   L356
#   sl-batch         [copybooks/wsbatch.cob:L18]  -> condition_names.is_sl_batch   L358
#   Date-UK, Date-USA  [copybooks/wssystem.cob:L129-L130]  -> inside acas_posting.dates
#                    L555, L557, L585, L587
# `fs-reply = 10` is compared against FsReply.END_OF_FILE, never the literal.
#
# Moves - every one through cobol.move with the RECEIVING field's descriptor,
# each descriptor LOOKED UP from the record module that owns it and never
# constructed here:
#   L272  1 -> File-Key-No                 [copybooks/wsfnctn.cob:L46]
#   L364  stored  -> u-bin  }
#   L369  posted  -> u-bin  }              [copybooks/wsmaps03.cob:L30]
#   L374  proofed -> u-bin  }
#   L379  entered -> u-bin  }
#   L480  WS-Batch-Nos -> pre-batch        [general/gl070.cbl:L109]   (inert, Q-70b)
#   L495  batch        -> pre-batch        [general/gl070.cbl:L109]
#   L496  post-number  -> pre-post         [general/gl070.cbl:L110]
#   L497  post-code    -> pre-code         [general/gl070.cbl:L111]   <- anomaly A-21
#   L498  post-date    -> pre-date         [general/gl070.cbl:L112]   x(8) to x(8)
#   L499  post-legend  -> pre-legend       [general/gl070.cbl:L116]
#   L501  post-dr      -> pre-ac           [general/gl070.cbl:L113]
#   L502  dr-pc        -> pre-pc           [general/gl070.cbl:L114]
#   L506  post-amount  -> pre-amount       [general/gl070.cbl:L115]
#   L510  post-cr      -> pre-ac
#   L511  cr-pc        -> pre-pc
#   L515  post-amount  -> pre-amount
#   L525  vat-ac       -> pre-ac                                      <- anomaly A-21
#   L526  vat-pc       -> pre-pc
#   L527  vat-amount   -> pre-amount
#
# Dates - consolidated into acas_posting.dates, which is native Python and calls
# no COBOL:
#   L547  perform maps03                   -> _maps03 -> dates.maps03
#   L606  call "maps04" using maps03-ws    -> dates.maps03  (reimplemented, NOT invoked)
#   L270, L330  perform zz070-convert-date -> _zz070_convert_date
#   L365, L370, L375, L380  perform zz060-Convert-Date -> _zz060_convert_date
# Both sections DEFAULT `System-Record.Date-Form` to 1 when it is zero - L553-L554
# and L583-L584 - and the store back into the system record is made at the call
# site, because that is where the frozen program makes it. `SYSTEM-REC` is a
# table, so this is a diff-visible mutation and not presentation.
# THIS PROGRAM HAS NO `zz050-Validate-Date` SECTION. Only five of the twelve
# in-scope programs carry one; gl070 is not among them, and none was added.
#
#
# GO TO  -  EVERY TRANSFER SITE, CLASSIFIED BY SHAPE
# --------------------------------------------------
# Class 1  backward to a loop head                        -> continue
# Class 2  forward past the loop, to a label with real work-> break + post-loop block
# Class 3  to a trailing exit label                       -> return
# Class 4  to a peer paragraph that itself transfers       -> call + explicit transfer
#
#   Line   Statement                       Target            Class  Python
#   ----   ---------                       ------            -----  ------
#   L290   go to main-exit                 main-exit  L295     3    return          _init01_menu_input2
#   L310   go to end-run                   end-run    L318     2    break           _gl071a_loop
#   L313   go to loop                      loop       L305     1    continue        _gl071a_loop
#   L316   go to loop                      loop       L305     1    continue        _gl071a_loop
#   L349   go to end-report                end-report L435     2    break           _gl060a_loop
#   L352   go to loop                      loop       L344     1    continue        _gl060a_loop
#   L366   go to next-1                    next-1     L382     4    call+continue   _gl060a_loop
#   L371   go to next-1                    next-1     L382     4    call+continue   _gl060a_loop
#   L376   go to next-1                    next-1     L382     4    call+continue   _gl060a_loop
#   L414   go to loop                      loop       L344     1    continue        _gl060a_loop
#   L424   go to end-report                end-report L435     2    break           _gl060a_loop
#   L427   go to loop                      loop       L344     1    continue        _gl060a_loop
#   L455   go to end-run                   end-run    L469     2    break           _gl071b_loop
#   L458   go to loop                      loop       L450     1    continue        _gl071b_loop
#   L463   go to loop                      loop       L450     1    continue        _gl071b_loop
#   L467   go to loop                      loop       L450     1    continue        _gl071b_loop
#   L488   go to main-exit                 main-exit  L535     3    return          _gl071b_pre_process_loop
#   L491   go to loop                      loop       L483     1    continue        _gl071b_pre_process_loop
#   L493   go to loop                      loop       L483     1    continue        _gl071b_pre_process_loop
#   L523   go to loop                      loop       L483     1    continue        _gl071b_pre_process_loop
#   L533   go to loop                      loop       L483     1    continue        _gl071b_pre_process_loop
#   L550   go to zz060-Exit                zz060-Exit L570     3    return          in acas_posting.dates
#   L556   go to zz060-Exit                zz060-Exit L570     3    return          in acas_posting.dates
#   L561   go to zz060-Exit                zz060-Exit L570     3    return          in acas_posting.dates
#   L586   go to zz070-Exit                zz070-Exit L600     3    return          in acas_posting.dates
#   L591   go to zz070-Exit                zz070-Exit L600     3    return          in acas_posting.dates
#
# Tally: class 1 = 12, class 2 = 4, class 3 = 7, class 4 = 3. Total 26.
#
# CLASSIFIED BY SHAPE, NOT BY NAME, and one label proves why the shape test has
# to be applied rather than a list consulted. `end-report` does not appear in the
# Agent Action Plan's Class-2 label list, yet it is Class 2: it sits OUTSIDE the
# loop and is followed by the close. `next-1` is the mirror image - it looks like
# a forward terminator and is NOT one, because it sits INSIDE the loop, does real
# work, and then transfers control itself. It is Class 4.
#
# THE THREE CLASS-4 SITES AND THEIR EQUIVALENCE PROOF. Class 4 is the only class
# needing a per-site argument, so here it is, once, the three sites being
# identical in shape. L366, L371 and L376 are the tails of the first three
# alternatives of the date-precedence chain; each body is `move <date> to u-bin`
# plus `perform zz060-Convert-Date`. The fourth alternative L378-L380 has NO
# transfer, and `next-1.` L382 is the statement immediately after it, so jumping
# to `next-1` and falling into it reach the same place with nothing in between.
# The reachable behaviours are exactly: alternative k in {1,2,3} then `next-1`;
# alternative 4 then `next-1`; `next-1` alone when all four dates are zero. An
# `if`/`elif` chain over the four tests followed unconditionally by the `next-1`
# call yields precisely those and nothing else. `next-1`'s own transfer at
# L413-L414 is then issued by the caller as `continue`, and falling past it into
# `screen-option.` L418 is simply the next statement - so each site is a named
# call followed by the explicit control statement the target itself executes.
# THE CHAIN IS NOT COSMETIC: the three `go to`s are what make the alternatives
# mutually exclusive. Four independent `if`s would convert a multi-dated batch
# several times over and report the `entered` date where the frozen program
# reports `stored`.
#
# THE THREE CLASS-2 SPLITS - FOUR SITES, THREE SPLITS, which is not a discrepancy
# with the tally above. Four Class-2 transfer SITES exist (L310, L349, L424,
# L455) but only THREE distinct post-loop BLOCKS, because L349 and L424 both
# target the same label, `end-report.` L435: two `go to`s reaching one label share
# one `break` target and one post-loop block. Stated explicitly because
# mis-splitting any one of them silently drops end-of-run processing:
#   gl071a  L318-L321  end-run     -> GL-Batch-Close                        after the loop
#   gl060a  L435-L440  end-report  -> the acknowledgement pause, dropped, and
#                                     GL-Batch-Close                        after the loop
#   gl071b  L469-L473  end-run     -> close pre-trans, then GL-Batch-Close  after the loop
# And the one Class-3 that LOOKS like a Class 2 and is not: L488 targets
# `main-exit.` L535, which holds only `exit section.` The posting file's close is
# in the CALLING section at L466, so a post-loop close here would close it twice.
#
# `PERFORM ... THRU` DOES NOT OCCUR IN THIS PROGRAM. Repo-wide the in-scope sites
# are gl072 L300 and L304, sl100 L344 and pl100 L336 - none here, so no
# fall-through span had to be reconstructed.
#
# THE FALL-THROUGHS that are not `GO TO`s, made explicit as function calls so
# execution order is preserved and visible:
#   L272 -> L274   init01's opening statements into menu-input.
#   L279 -> L281   menu-input. into menu-input2.
#   L293 -> L295   menu-input2. into main-exit.
#   L380 -> L382   the fourth date alternative into next-1.
#   L416 -> L418   the prompt display into screen-option.
#   L427 -> L429   screen-clear. is `perform`ed, not fallen into, from L426
#   L433 -> L435   screen-clear. into end-report.  (unreachable in practice: the
#                  only route to screen-clear. is the `perform` at L426, which
#                  returns)
#
#
# ANOMALY REGISTER  -  REPRODUCED, NEVER FIXED  (rule R-4)
# --------------------------------------------------------
# "A defect reproduced is correct; a defect fixed is a failure."
#
# A-21  Field-name collisions across three posting copybooks force QUALIFIED
#       references, and the qualifier is spelled two different ways within one
#       paragraph. Three sites, all in gl071b-pre-process:
#           [general/gl070.cbl:L497]  move post-code IN WS-Posting-Record ...
#           [general/gl070.cbl:L521]  if   vat-ac    OF WS-Posting-Record = zero
#           [general/gl070.cbl:L525]  move vat-ac    OF WS-Posting-Record ...
#       In Python the collision cannot arise - each record is its own object - so
#       the reproduction is the comment at each site plus RECORD-QUALIFIED
#       attribute access, `store.posting.post_code` and `store.posting.vat_ac`,
#       never a bare local of the same name.
#       The Agent Action Plan cites L510 for this anomaly. L510 is
#       `move post-cr to pre-ac.` and carries no qualifier; the three sites above
#       are the measured ones.
#
# A-22  The wrapper section is named after the INTERFACE COPYBOOK while its exit
#       label is named after the CALLED PROGRAM:
#           [general/gl070.cbl:L603]  maps03       section.
#           [general/gl070.cbl:L606]  call "maps04" using maps03-ws.
#           [general/gl070.cbl:L608]  maps04-exit.
#           [general/gl070.cbl:L609]  exit section.
#       Reproduced by naming the function `_maps03`, after the section, and by
#       recording the exit label `maps04-exit` in the paragraph table above, so
#       both halves of the inconsistency survive.
#       THE SAME DEFECT OCCURS TWICE IN THE CODEBASE. Its second occurrence is
#       `general/gl051.cbl` L1273 and L1278, which belongs to
#       gl051_batch_control_check.py. The Agent Action Plan cites only this one.
#
# Two further oddities are recorded here rather than in the register, the plan
# not having listed them, and both are reproduced as they stand:
#   * [general/gl070.cbl:L472] `close pre-trans.` carries the trailing comment
#     `*> batch-file`, which names the wrong file - the batch file is closed by
#     the NEXT statement.
#   * `y`, the report's page number [general/gl070.cbl:L334-L335], is set to one
#     and NEVER incremented, so every page of the open-batch report claims to be
#     page one.
#   * THE VAT GATE CAN LEAVE A POSTING UNBALANCED. The gate at
#     [general/gl070.cbl:L521-L522] suppresses only the VAT leg, while the debit
#     and credit legs have already absorbed the VAT through their own tests at
#     [general/gl070.cbl:L503] and [general/gl070.cbl:L512]. A posting carrying a
#     VAT amount but NO VAT ACCOUNT therefore emits two legs summing to the VAT
#     instead of to zero. Measured, and reproduced.
#
#
# OMISSIONS  -  DELIBERATE, AND RECORDED SO NOTHING LOOKS LOST
# ------------------------------------------------------------
# Agent Action Plan section 0.4.3 and rule R-5: a deliberate omission is
# recorded AS an omission, "so that a reader comparing the two files does not
# conclude something was lost."
#
#  1. ALL `display ... at` SCREEN OUTPUT -> log records, never table state, never
#     control flow. Sites: L277, L278, L279 (the banner), L284 and L292 (the
#     phase labels, also carried in the module docstring so the non-sequential
#     phase numbering is not lost), L332, L336, L337, L338, L339 (the report
#     headings), L408 and L410 (the two body lines), L416 (the paging prompt),
#     L433 (the page erase), L438 (the closing prompt). Screen positions, colours
#     and the `erase eos` clause are dropped with them.
#
#  2. `accept ws-env-lines from lines.` [general/gl070.cbl:L254] and the
#     screen-geometry arithmetic [general/gl070.cbl:L255-L261], together with
#     `ws-lines`, `ws-23-lines`, `ws-22-lines`, `ws-20-lines` and `Body-lines`
#     [general/gl070.cbl:L162-L167]. This reads the TERMINAL HEIGHT, not a clock,
#     so rule R-6 is not engaged by it.
#     `ws-21-lines` is the ONE exception: it is modelled, because it is an
#     operand of a preserved control transfer - see question Q-70e.
#
#  3. `set ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".` and
#     `set ENVIRONMENT "COB_SCREEN_ESC" to "Y".` [general/gl070.cbl:L268-L269] -
#     they make the escape and paging keys detectable by a screen this migration
#     does not draw.
#
#  4. `accept ws-reply ...` twice, treated DIFFERENTLY because they differ:
#       [general/gl070.cbl:L421]  the paging prompt. It gates no database write -
#         gl060a performs no write, rewrite or delete anywhere - so the PAUSE is
#         dropped while the CONTROL TRANSFER is preserved: the headless report
#         takes the continue-paging branch and runs to completion. Question Q-70d
#         records the measured consequence, which is none.
#       [general/gl070.cbl:L438-L439]  the closing acknowledgement. It transfers
#         control nowhere and gates nothing, so it is dropped ENTIRELY.
#
#  5. ALL PRINT-LINE FIELDS - `l1-*`, `l3-*`, `l4-*`, `l5-*`, `l6-*`, `l7-*`
#     [general/gl070.cbl:L199-L234] - and the moves that fill them: L271, L331,
#     L333, L335, L355, L357, L359, L361, L385, L388, L392, L395, L398, L400,
#     L401, L402, L403, L404. `l6-ledger` and `l6-status` are the exception: they
#     are modelled, because the independent `if`s that fill them can all miss and
#     the CARRY-OVER of the previous batch's label is real behaviour.
#
#  6. THE CURSOR STATE - `curs`, `curs2`, `lin2`, `cole`
#     [copybooks/wsfnctn.cob:L27-L34] - and its arithmetic at L341, L406 and
#     L409. `lin` is the exception, modelled because it is an operand of the
#     preserved transfer at L413-L414.
#
#  7. The version banner `prog-name` [general/gl070.cbl:L98] -> the module
#     docstring and one log record.
#
#  8. `copy "screenio.cpy".` [general/gl070.cbl:L170] and
#     `copy "envdiv.cob".` [general/gl070.cbl:L86] - representation only: a
#     screen-handling declaration set and an ENVIRONMENT DIVISION this migration
#     has no analogue for.
#
#  9. `Dummies-4-Unused-ACAS-FH-Calls` [general/gl070.cbl:L132-L152] - the block
#     of unused facade stubs declared purely so the copybook's full verb set
#     resolves at link time. Python has no equivalent need, so it maps to
#     nothing. This is the representation-only omission the Agent Action Plan
#     names for gl072, present here too.
#
# 10. `SW-Testing` [copybooks/Test-Data-Flags.cob] is carried on the common data
#     record and passed to every dispatch, but this program never tests it, so no
#     conditional logging path was invented for it.
#
# 11. THERE IS NO `call "SYSTEM" using Print-Report` IN THIS PROGRAM. Stated
#     explicitly so a reader knows the spool-out path was looked for and is
#     genuinely absent - gl070 produces no report file.
#
#
# CONDITIONAL CENSUS  -  NOT ONE ADDED VALIDATION  (rule R-3)
# -----------------------------------------------------------
# 34 conditionals exist in executable code. TWENTY-NINE of them are one frozen
# COBOL `if`, each mapped here so the rule can be audited rather than trusted:
#
#   L287 a = 1 .......................... the detector test in menu-input2.
#   L309, L348, L454, L487 fs-reply = 10  the four at-end tests, via _at_end
#   L312, L351, L457 bcycle not = scycle  the cycle filter, via _cycle_differs
#   L314 status-open .................... the DETECTOR, phase 1
#   L354, L356, L358 gl/pl/sl-batch ..... the report's three ledger tests
#   L363, L368, L373, L378 date not = 0 . the date-precedence chain
#   L387 status-open .................... the report's status column
#   L390, L393, L396 status-closed and .. its three closed-status variants
#   L413 lin < ws-21-lines .............. the page test, via _gl060a_next_1
#   L423 ws-reply = "X" ................. the paging choice, via
#                                         _gl060a_screen_option
#   L460 status-open or not waiting or not gl-batch  THE REJECTOR, phase 2
#   L490 WS-Post-Key = zero ............. via _post_key_is_zero
#   L492 batch not = WS-Batch-Nos ....... the posting's batch filter
#   L503, L512 post-vat-side ............ the two opposite VAT-side tests
#   L521 vat-ac = zero or vat-amount = zero  the VAT gate
#   L529 post-vat-side = "CR" ........... the VAT leg's conditional negation
# The two remaining frozen conditionals, `if Date-Form = zero` at L553 and L583,
# live inside the consolidated date implementations.
#
# THE OTHER FIVE ARE NOT VALIDATIONS AND ARE DECLARED HERE SO THEY CANNOT BE
# MISTAKEN FOR ONE. All five are in `run`, and all five resolve an OPTIONAL
# KEYWORD ARGUMENT to a freshly constructed record: `work_files is None`,
# `file_access is None`, `dal_common is None`, `transport is not None` and
# `states is not None`. They exist because Python has optional arguments and
# COBOL does not - the frozen program's caller simply owns the corresponding
# WORKING-STORAGE. None of them inspects a record, filters a row, or can change
# which postings are read, which legs are written, or what any leg contains.
# Three further `if`s appear inside generator expressions
# (`if descriptor.name == "File-Key-No"` and its two siblings); those select a
# published FieldDescriptor by name and likewise judge no data.
#
# ZERO `try`, ZERO `assert`, ZERO `raise`, ZERO `with`, ZERO `lambda` - so no
# error path, no guard and no exception translation was invented either. The four
# `while True:` loops are the four `loop.` paragraphs and nothing else.
#
#
# CITATION CORRECTIONS
# --------------------
# Measured against the frozen source. Where the Agent Action Plan and the source
# disagree, the source wins and the correction is recorded.
#   * The CYCLE FILTER is L312-L313, not L309-L310. L309-L310 is the at-end test.
#   * The DETECTOR is L314-L315; the ABORT is L287-L290, with `move 5 to
#     ws-term-code` at L289.
#   * The phase labels are displayed at L284 and L292, not L283 and L291.
#   * Phase 2's two filters are at L457-L458 and L460-L463, not L452-L453 and
#     L455-L459.
#   * A-21's sites are L497, L521 and L525, not L510.
#   * The two passes are NOT "the same pass with extra conditions": phase 1 uses
#     `status-open` as a DETECTOR that stops the run, phase 2 as a REJECTOR that
#     skips the batch.
#
#
# AMBIGUITIES  ->  docs/migration/ambiguity-resolutions.md
# --------------------------------------------------------
# Q-70a  Is `move 1 to File-Key-No` [general/gl070.cbl:L272] inert? Every facade
#        dispatch paragraph sets the key number itself immediately before its
#        `CALL` [copybooks/Proc-ACAS-FH-Calls.cob:L52], which suggests it is.
#        Reproduced regardless; rule R-3 does not permit dropping a store on
#        inference.
# Q-70b  Likewise `move WS-Batch-Nos to pre-batch` [general/gl070.cbl:L480],
#        which L495 overwrites before any write. Reproduced.
# Q-70c  `Scycle` redefines `Cyclea binary-char` [copybooks/wssystem.cob:L62-L63]
#        while `Bcycle` is `pic 99` DISPLAY [copybooks/wsbatch.cob:L34]. The
#        comparison of the two is made numerically; whether the compiled program
#        compares them numerically or by character for every value in range wants
#        confirming against the oracle.
# Q-70d  Does the paging prompt's early "X" exit [general/gl070.cbl:L423-L424]
#        change any table? Measured answer: no. gl060a performs no write of any
#        kind, both branches converge on `GL-Batch-Close`, and the only side
#        effect in the section - `zz060` defaulting `Date-Form` - has already
#        happened in `init01` at L270 before the section is entered.
# Q-70e  `ws-21-lines` NEVER RECEIVES A VALUE. The statement that would have
#        given it one, `subtract 3 from ws-lines giving ws-21-lines`
#        [general/gl070.cbl:L262], IS COMMENTED OUT IN THE FROZEN SOURCE, so it
#        keeps its `value zero` [general/gl070.cbl:L165] and the page test
#        `if lin < ws-21-lines` [general/gl070.cbl:L413] can never be true - `lin`
#        is at least ten when it is reached. The compiled report therefore
#        prompts after the FIRST batch, every time. Reproduced by computing the
#        comparison rather than by hard-coding its answer.
#
# --- end traceability ---
