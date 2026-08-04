r"""`acas007` and its bridge `glbatchMT` - the `GLBATCH-REC` batch table.

The data-access module for the GL-Batch entity. It carries the batch header the
whole General Ledger cycle turns on: `gl051` sets its status from the
control-total gate, `gl070` filters on its cycle and its open status, and `gl072`
stamps it cleared with a posting date [general/gl072.cbl:L375-L377].

The record's declared length is disputed in the copybook itself - 96 bytes, then
98, with the maintainer recording that he counts 96 while `function length` says
98 [copybooks/wsbatch.cob:L7-L9]. No length constant is declared here; the
contradiction is recorded rather than resolved.
"""

from __future__ import annotations

import dataclasses
import decimal
import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, NoReturn

from acas_posting.dal import cursor_state
from acas_posting.dal.connection import (
    OpenOutcome,
    TransportSecurity,
    acquire_cursor,
    execute_statement,
    load_rdb_data_once,
    mysql_1000_open,
    mysql_1090_exit,
    mysql_1980_close,
    mysql_1999_exit,
    quote_identifier,
    transport_decimal_context,
)
from acas_posting.dal.status import (
    AccessType,
    DbErrorStatus,
    FileFunction,
    FsReply,
    LogSystem,
    WeError,
    end_of_file_status,
    log_cobol_stop,
    log_file_handler_record,
    log_handler_failure,
    is_duplicate_key_bridge_level,
    mysql_1100_db_error,
    override_we_error_for_operation,
)
from acas_posting.dictionary import loader
from acas_posting.records.file_access import FileAccess, LoggingData
from acas_posting.records.file_defs import FileDefs
from acas_posting.records.gl_batch import (
    BatchAmounts,
    BatchDates,
    GlBatchRecord,
    PostingData,
    WsBatchKey,
    WsBatchKey9,
)
from acas_posting.records.system_record import SystemRecord
from acas_posting.records.test_data_flags import AcasDalCommonData

__all__: Final[tuple[str, ...]] = (
    "AMBIGUITIES",
    "ANOMALIES",
    "BRIDGE",
    "BatchColumn",
    "BatchKeyViewsDisagreeError",
    "BridgeCalledOutsideHandlerError",
    "BridgeNotOpenError",
    "COLUMNS",
    "COLUMN_NAMES",
    "COPYBOOK",
    "DELETE_ALL_HIGH_KEY",
    "DISPATCH_ORDER",
    "ENTITY_FACADE",
    "ERROR_MESSAGE_GL901",
    "ERROR_MESSAGE_GL904",
    "FILE_KEY_NO_REQUIRED",
    "FlatFileStoreNotMigratedError",
    "GUARDED_FUNCTIONS",
    "HANDLER",
    "KEY_OF_REFERENCE",
    "MOST_RELATION_DEFAULT",
    "OMISSIONS",
    "PROG_NAME",
    "RECORD",
    "START_RELATION_BY_ACCESS_TYPE",
    "START_ACCESS_TYPE_RANGE",
    "TABLE",
    "TABLE_OF_KEYNAMES_ROW",
    "WS_LOG_FILE_NO_COBOL_PATH",
    "WS_LOG_FILE_NO_RDB_PATH",
    "WS_LOG_SYSTEM",
    "WS_NO_PARAGRAPH_BRIDGE",
    "WS_NO_PARAGRAPH_COBOL",
    "WS_BATCH_RECORD_LENGTH",
    "WS_BATCH_RECORD_LENGTH_COMMENT_CLAIM",
    "aa010_main",
    "aa020_process_open",
    "aa030_process_close",
    "aa040_process_read_next",
    "aa041_reread",
    "aa050_process_read_indexed",
    "aa051_reread",
    "aa060_process_start",
    "aa070_process_write",
    "aa080_process_delete",
    "aa090_process_rewrite",
    "aa100_bad_function",
    "aa999_main_exit",
    "aa_exit",
    "aa_main_exit",
    "aa_process_flat_file",
    "ba010_test_ws_rec_size",
    "ba012_test_ws_rec_size_2",
    "ba015_test_ends",
    "ba020_process_dal",
    "ba_process_rdbms",
    "ba_rdbms_exit",
    "batch_key_image",
    "bb000_hv_load",
    "bb100_unload_hvs",
    "ca_exit",
    "ca_process_logs",
    "declare_connection_policy",
    "dispatch",
    "glbatch_mt",
    "mt_ba010_initialise",
    "mt_ba020_process_open",
    "mt_ba030_process_close",
    "mt_ba040_process_read_next",
    "mt_ba041_reread",
    "mt_ba050_process_read_indexed",
    "mt_ba060_process_start",
    "mt_ba070_process_write",
    "mt_ba080_process_delete",
    "mt_ba085_process_delete_all",
    "mt_ba090_process_rewrite",
    "mt_ba100_bad_function",
    "mt_ba998_free",
    "mt_ba999_end",
    "mt_ba999_exit",
    "mt_ba_acas_dal_process",
    "mt_bb200_insert",
    "mt_bb300_update",
    "mt_ca_process_logs",
    "reset_working_storage",
    "signed_to_unsigned_host_variable",
    "synchronise_batch_key_views",
)

_LOG: Final[logging.Logger] = logging.getLogger(__name__)


HANDLER: Final[str] = "acas007"

BRIDGE: Final[str] = "glbatchMT"

TABLE: Final[str] = "GLBATCH-REC"

RECORD: Final[str] = "WS-Batch-Record"

ENTITY_FACADE: Final[str] = "GL-Batch"

COPYBOOK: Final[str] = "copybooks/wsbatch.cob"

PROG_NAME: Final[str] = "acas007 (3.3.00)"

WS_LOG_SYSTEM: Final[LogSystem] = LogSystem.GL

WS_LOG_FILE_NO_COBOL_PATH: Final[int] = 13

#: ``move 23 to WS-Log-File-no`` [common/acas007.cbl:L577] - ANOMALY N-log, the
#: relational path's overwrite, spelled with a lower-case ``no`` at that site.
WS_LOG_FILE_NO_RDB_PATH: Final[int] = 23

FILE_KEY_NO_REQUIRED: Final[int] = 1

#: ``function Length (WS-Batch-Record)`` and ``function length (Batch-Record)``, the two
#: values ``ba012-Test-WS-Rec-Size-2`` compares [common/acas007.cbl: L582-L587].
WS_BATCH_RECORD_LENGTH: Final[int] = 96

#: What the maintainer's comment claims instead - ANOMALY A-15, kept on record and NOT
#: reconciled.
WS_BATCH_RECORD_LENGTH_COMMENT_CLAIM: Final[int] = 98

#: ``move 901 to WE-Error`` [common/acas007.cbl:L589] and the value ``ba012-Test-WS-Rec-
#: Size-2`` then tests for at [:L592].
RECORD_SIZE_WE_ERROR: Final[int] = int(WeError.RECORD_SIZE_MISMATCH)

#: ``03 GL901 pic x(31) value "GL901 Note error and hit return".``
#: [common/acas007.cbl:L249]. The second of the two lines the 901 branch displays
#: [:L601].
ERROR_MESSAGE_GL901: Final[str] = "GL901 Note error and hit return"

ERROR_MESSAGE_GL904: Final[str] = "GL904 Program Error: Temp rec = "

_DISPLAY_BLK_WIDTH: Final[int] = 75

#: The four ``start Batch-File key ...`` verbs of ``aa060-Process-Start``, keyed by the
#: ``Access-Type`` that selects each.
_START_VERB_LOCATORS: Final[Mapping[int, str]] = MappingProxyType(
    {
        int(AccessType.EQUAL_TO): "[common/acas007.cbl:L480]",
        int(AccessType.NOT_LESS_THAN): "[common/acas007.cbl:L486]",
        int(AccessType.GREATER_THAN): "[common/acas007.cbl:L492]",
        int(AccessType.LESS_THAN): "[common/acas007.cbl:L499]",
    }
)

_RECORD_LENGTH_PICTURE_DIGITS: Final[int] = 4


# THE KEY GUARD, AS DATA. ANOMALY N-guard: `acas000` guards 4, 5 and 7 instead, and the
# two sets are deliberately not harmonised [common/acas007.cbl:L285- L299]. ANOMALY
# N-996-comment.
GUARDED_FUNCTIONS: Final[Mapping[int, int]] = MappingProxyType(
    {
        int(FileFunction.READ_INDEXED): int(WeError.FILE_KEY_NO_OUT_OF_RANGE),
        int(FileFunction.START): int(WeError.FILE_KEY_NO_OUT_OF_RANGE),
        int(FileFunction.DELETE): int(WeError.DELETE_KEY_OUT_OF_RANGE),
    }
)

DISPATCH_ORDER: Final[tuple[int, ...]] = (
    int(FileFunction.OPEN),
    int(FileFunction.CLOSE),
    int(FileFunction.READ_NEXT),
    int(FileFunction.READ_INDEXED),
    int(FileFunction.WRITE),
    int(FileFunction.RE_WRITE),
    int(FileFunction.DELETE),
    int(FileFunction.START),
)

WS_NO_PARAGRAPH_COBOL: Final[Mapping[str, int]] = MappingProxyType(
    {
        "aa020-Process-Open": 201,
        "aa030-Process-Close": 202,
        "aa040-Process-Read-Next": 203,
        "aa050-Process-Read-Indexed": 204,
        "aa060-Process-Start": 205,
        "aa070-Process-Write": 206,
        "aa080-Process-Delete": 207,
        "aa090-Process-Rewrite": 208,
    }
)

#: ``move N to ws-No-Paragraph`` inside the bridge [common/glbatchMT.cbl:L426, :L445,
#: :L466, :L534, :L616, :L646, :L775, :L824, :L867, :L948, :L985, :L1039].
WS_NO_PARAGRAPH_BRIDGE: Final[Mapping[str, int]] = MappingProxyType(
    {
        "ba020-Process-Open": 1,
        "ba030-Process-Close": 2,
        "ba040-Process-Read-Next": 3,
        "ba041-Reread": 4,
        "ba050-Process-Read-Indexed": 5,
        "ba050-Process-Read-Indexed-fetch": 6,
        "ba060-Process-Start": 8,
        "ba070-Process-Write": 10,
        "ba080-Process-Delete": 13,
        "ba085-Process-Delete-ALL": 15,
        "ba090-Process-Rewrite": 17,
        "ba998-Free": 20,
    }
)

#: ``move 999999 to ws-BATCH-KEY`` [common/glbatchMT.cbl:L922], the high key
#: ``ba085-Process-Delete-ALL`` deletes BELOW. Six characters, because the key of
#: reference is offset 1 length 6. ANOMALY N-deleteall-999999.
DELETE_ALL_HIGH_KEY: Final[str] = "999999"

#: ``move spaces to MOST-Relation`` [common/glbatchMT.scb:L629]. ANOMALY N-relation-
#: nodefault: the ``evaluate`` that follows has no ``when other``, so an out-of-range
#: ``Access-Type`` leaves the relation as spaces.
MOST_RELATION_DEFAULT: Final[str] = "   "

#: ``evaluate Access-Type`` for the START relation, verbatim from
#: [common/glbatchMT.scb:L631-L642]. Transcribed rather than imported so the absence of
#: a ``when other`` is visible here.
START_RELATION_BY_ACCESS_TYPE: Final[Mapping[int, str]] = MappingProxyType(
    {
        int(AccessType.EQUAL_TO): "=  ",
        int(AccessType.LESS_THAN): "<  ",
        int(AccessType.GREATER_THAN): ">  ",
        int(AccessType.NOT_LESS_THAN): ">= ",
        int(AccessType.NOT_GREATER_THAN): "<= ",
    }
)

START_ACCESS_TYPE_RANGE: Final[tuple[int, int]] = (5, 8)

TABLE_OF_KEYNAMES_ROW: Final[Mapping[str, object]] = MappingProxyType(
    {
        "KeyName": "BATCH-KEY",
        "KOR-Offset": 1,
        "KOR-Length": 6,
        "KOR-Type": "STR",
        "occurs": 1,
        "offset-length-literal": "00010006",
        "source": "[common/glbatchMT.scb:L231-L241]",
    }
)

#: The same key as ``dal/cursor_state.py`` already holds it, so the positioning verbs
#: and this module can never disagree about offset, length or column.
KEY_OF_REFERENCE: Final[cursor_state.KeyOfReference] = cursor_state.key_of_reference(
    TABLE, FILE_KEY_NO_REQUIRED
)


@dataclass(frozen=True, slots=True)
class _Note:
    """One registered anomaly, omission or ambiguity.

    Attributes:
        reference: The identifier this module's docstring uses for the defect.
        summary: What the frozen program does, in one sentence.
        locators: Every ``[<path>:L<n>]`` that evidences it.
    """

    reference: str
    summary: str
    locators: tuple[str, ...]


ANOMALIES: Final[tuple[_Note, ...]] = (
    _Note(
        "A-11",
        "Entered, Proofed, Posted and Stored are signed binary-long in the "
        "copybook and unsigned PIC 9(10) COMP in the host-variable group, so a "
        "negative loses its sign at the bridge before any SQL runs.",
        (
            "[copybooks/wsbatch.cob:L36-L39]",
            "[common/glbatchMT.cbl:L287-L290]",
            "[mysql/ACASDB.sql:L86-L89]",
        ),
    ),
    _Note(
        "A-15",
        "The maintainer records the record as 96 bytes, then 98, then says he "
        "counts 96 but function length reports 98; ba012-Test-WS-Rec-Size-2 "
        "compares exactly those two lengths.",
        ("[copybooks/wsbatch.cob:L7-L9]", "[common/acas007.cbl:L579-L591]"),
    ),
    _Note(
        "N-widen",
        "The four control totals are widened from 11 digits to 14 at the host "
        "variable and stay widened at the decimal(14,2) column.",
        (
            "[copybooks/wsbatch.cob:L41-L44]",
            "[common/glbatchMT.cbl:L291-L294]",
            "[mysql/ACASDB.sql:L90-L93]",
        ),
    ),
    _Note(
        "N18b",
        "One Open-plus-Output request calls the bridge twice: first fn-Open "
        "with fn-Output, then fn-Delete-All, because ba015-Test-Ends performs "
        "ba020-Process-Dal and then falls through into it again.",
        (
            "[common/acas007.cbl:L305-L312]",
            "[common/acas007.cbl:L622-L631]",
            "[common/acas007.cbl:L640-L645]",
            "[common/acas005.cbl:L307]",
            "[common/acas008.cbl:L313-L319]",
        ),
    ),
    _Note(
        "N-relation-nodefault",
        "The START relation evaluate has no when other, so an Access-Type "
        "outside 5..9 leaves MOST-Relation as spaces and builds a malformed "
        "predicate; no default is supplied.",
        ("[common/glbatchMT.scb:L631-L642]",),
    ),
    _Note(
        "N-initialize",
        "Two initialisation semantics in one bridge: initialize WS-Batch-Record "
        "with filler on the EOF2 path, and a plain initialize in bb100.",
        ("[common/glbatchMT.cbl:L589]", "[common/glbatchMT.cbl:L1106]"),
    ),
    _Note(
        "N-log",
        "WS-Log-File-No is set to 13 on the indexed path and overwritten to 23 "
        "on the relational path, where the field is also spelled with a "
        "lower-case no.",
        ("[common/acas007.cbl:L281]", "[common/acas007.cbl:L577]"),
    ),
    _Note(
        "N-guard",
        "acas007 guards File-Key-No for functions 4, 9 and 8; acas000 guards 4, "
        "5 and 7 instead. The sets are not harmonised.",
        ("[common/acas007.cbl:L285-L299]",),
    ),
    _Note(
        "N-998",
        "We-Error 998 carries three documented meanings across the codebase: "
        "file seeks key type out of range, invalid calling parameter settings, "
        "and File-Key-No out of range.",
        (
            "[common/acas007.cbl:L289]",
            "[common/acas007.cbl:L473]",
            "[common/glpostingMT.cbl:L141]",
        ),
    ),
    _Note(
        "N-996-comment",
        "The comment on the 996 branch is a copy-paste of the 998 comment and "
        "describes the wrong condition.",
        ("[common/acas007.cbl:L295]", "[common/acas007.cbl:L289]"),
    ),
    _Note(
        "N-name",
        "The camelCase copybook name bDefault is flattened to BDEFAULT at both "
        "the host variable and the column.",
        (
            "[copybooks/wsbatch.cob:L48]",
            "[common/glbatchMT.cbl:L296]",
            "[mysql/ACASDB.sql:L95]",
        ),
    ),
    _Note(
        "N-deleteall-999999",
        "Delete-All is not a bare DELETE: it moves 999999 into the key and "
        "deletes WHERE BATCH-KEY < 999999, so a batch keyed exactly 999999 "
        "survives, and its row-count guard is not > zero rather than not = 1.",
        (
            "[common/glbatchMT.cbl:L900]",
            "[common/glbatchMT.cbl:L922]",
            "[common/glbatchMT.cbl:L928-L938]",
            "[common/glbatchMT.cbl:L962]",
        ),
    ),
    _Note(
        "N-close-double-log",
        "aa030-Process-Close performs aa999-main-exit, whose body logs under "
        "Testing-1, and then performs Ca-Process-Logs unconditionally, so a "
        "close logs twice under Testing-1.",
        ("[common/acas007.cbl:L407-L410]", "[common/acas007.cbl:L551-L554]"),
    ),
    _Note(
        "N-start-code-divergence",
        "The handler's access-type guard writes We-Error 998 and leaves "
        "FS-Reply at the zero it had just moved, so a caller testing only "
        "FS-Reply sees success; the bridge writes (99, 997) for the same "
        "condition and the handler's own header documents 997.",
        (
            "[common/acas007.cbl:L466-L475]",
            "[common/glbatchMT.cbl:L715-L720]",
            "[common/acas007.cbl:L155]",
        ),
    ),
    _Note(
        "N-start-dead-arm",
        "The bridge rejects access-type < 5 or > 8 before the relation "
        "evaluate, so the when 9 arm mapping Access-Type 9 to <= is unreachable "
        "dead code.",
        ("[common/glbatchMT.cbl:L715-L720]", "[common/glbatchMT.scb:L640-L641]"),
    ),
    _Note(
        "N-badfunction-divergence",
        "The handler's bad-function paragraph returns (99, 999); the bridge's "
        "returns (99, 990).",
        ("[common/acas007.cbl:L548-L549]", "[common/glbatchMT.cbl:L1030-L1031]"),
    ),
    _Note(
        "N-nostatus",
        "ba010-Initialise has its status zeroing commented out, and ba080, "
        "ba085 and ba090 transfer to ba999-End from inside the row-count test "
        "but outside the errno test, so a delete or rewrite that matches no row "
        "returns the caller's incoming status unchanged; ba070 differs only in "
        "that it zeroed the status itself, so a write that inserts no row "
        "reports success.",
        (
            "[common/glbatchMT.cbl:L351-L352]",
            "[common/glbatchMT.cbl:L881-L896]",
            "[common/glbatchMT.cbl:L962-L977]",
            "[common/glbatchMT.cbl:L1008-L1020]",
            "[common/glbatchMT.cbl:L821]",
        ),
    ),
    _Note(
        "N-hv-render",
        "Every value is rendered through WS-MYSQL-EDIT PIC -Z(18)9.9(9) and no "
        "slice ever includes position 1, which holds the sign, so the sign "
        "cannot reach the statement even for a field that kept it.",
        ("[common/glbatchMT.cbl:L1150-L1160]", "[common/glbatchMT.cbl:L1262-L1269]"),
    ),
    _Note(
        "N-insert-set-syntax",
        "The insert uses MySQL's INSERT ... SET form rather than a column list "
        "with VALUES, and the update re-SETs all twenty-one columns including "
        "the primary key before appending its WHERE.",
        ("[common/glbatchMT.cbl:L1145-L1148]", "[common/glbatchMT.cbl:L1428-L1697]"),
    ),
    _Note(
        "N-affected-rows-int32",
        "MySQL_affected_rows writes four bytes through an int pointer into the "
        "eight-byte binary-double unsigned Ws-Mysql-Count-Rows, and "
        "mysql_affected_rows returns (my_ulonglong)-1 on failure, so a failed "
        "statement leaves 4294967295 there rather than zero; ba085-Process-"
        "Delete-ALL guards on not > zero instead of not = 1, so that value "
        "takes its else branch and A FAILED DELETE-ALL REPORTS COMPLETE "
        "SUCCESS.",
        (
            "[copybooks/mysql-procedures.cpy:L178]",
            "[copybooks/mysql-variables.cpy:L73]",
            "[common/glbatchMT.cbl:L962]",
            "[common/glbatchMT.cbl:L974-L978]",
        ),
    ),
    _Note(
        "N-open-nomode",
        "An Open whose Access-Type is none of input, i-o, output or extend falls "
        "through all four arms of aa020-Process-Open without touching a file and "
        "still reaches the paragraph's tail, so it is answered with the caller's "
        "own incoming FS-Reply, upgraded to We-Error 999 if that happened to be "
        "non-zero, with no diagnostic of any kind.",
        (
            "[common/acas007.cbl:L365-L393]",
            "[common/acas007.cbl:L394-L398]",
        ),
    ),
    _Note(
        "N-fa-statuses-skipped",
        "The Open-plus-Output special case reaches the bridge from a branch that "
        "precedes the move of RDBMS-Flat-Statuses into FA-RDBMS-Flat-Statuses, "
        "so on that one request - and only that one - File-Access reaches the "
        "bridge with the store selector still at its own default while every "
        "other relational request carries the copied value.",
        (
            "[common/acas007.cbl:L305-L312]",
            "[common/acas007.cbl:L316-L320]",
            "[copybooks/wsfnctn.cob:L72-L83]",
        ),
    ),
    _Note(
        "N-901-unreachable",
        "ba012-Test-WS-Rec-Size-2 compares function Length of WS-Batch-Record "
        "against function length of Batch-Record, but fdbatch.cob declares "
        "field for field the same layout as wsbatch.cob - the only difference "
        "is a REDEFINES, which adds no length - so A equals B always and the "
        "A < B arm can never fire; GnuCOBOL 3.2 measures both at 96.",
        (
            "[common/acas007.cbl:L581-L591]",
            "[copybooks/fdbatch.cob:L11-L49]",
            "[copybooks/wsbatch.cob:L13-L54]",
        ),
    ),
    _Note(
        "N-901-sticky",
        "The 901 display-and-exit branch tests WE-Error, which nothing clears - "
        "the handler's own status zeroing is commented out - so a caller "
        "arriving with a stale 901 takes that branch even though the lengths "
        "agree, is answered with its own incoming FS-Reply because only the "
        "A < B arm writes 99, and closes the first-call guard on the way out so "
        "the credentials are never loaded for the rest of the run.",
        (
            "[common/acas007.cbl:L334-L335]",
            "[common/acas007.cbl:L581-L584]",
            "[common/acas007.cbl:L592]",
            "[common/acas007.cbl:L607]",
            "[common/acas007.cbl:L614-L620]",
        ),
    ),
    _Note(
        "N-countrows-shared",
        "Ws-Mysql-Count-Rows is ONE working-storage field written both by "
        "MYSQL-1210-COMMAND, as an affected-row count, and by "
        "MYSQL-1220-STORE-RESULT, as a selected-row count, so a delete or "
        "rewrite that affected no row leaves zero in it and the NEXT "
        "fn-read-next on a live cursor ends the walk at ba041-Reread's zero "
        "test - silently, with the caller's incoming status unchanged.",
        (
            "[copybooks/mysql-variables.cpy:L73]",
            "[copybooks/mysql-procedures.cpy:L178]",
            "[copybooks/mysql-procedures.cpy:L196]",
            "[common/glbatchMT.cbl:L579-L594]",
            "[general/gl072.cbl:L373-L377]",
        ),
    ),
)

OMISSIONS: Final[tuple[_Note, ...]] = (
    _Note(
        "O-1",
        "The indexed-file store itself. Every aa0NN paragraph is reproduced, "
        "but the physical ISAM verb raises FlatFileStoreNotMigratedError "
        "because the Agent Action Plan's target inventory contains no "
        "indexed-file store.",
        ("[common/acas007.cbl:L362-L542]",),
    ),
    _Note(
        "O-2",
        "call fhlogger, in both programs. Rule R-1 forbids calling a COBOL "
        "program and fhlogger is out of scope, so one structured log record is "
        "emitted under the same gate instead.",
        ("[common/acas007.cbl:L656-L657]", "[common/glbatchMT.cbl:L1708-L1709]"),
    ),
    _Note(
        "O-3",
        "The screen statements: ba012's two displays and its accept, the "
        "stop for testing in aa040, and the bridge's Testing-2 displays. The "
        "pause is dropped and the control transfer preserved; the message text "
        "is still written to SQL-Msg where the COBOL writes it.",
        (
            "[common/acas007.cbl:L600-L606]",
            "[common/acas007.cbl:L426]",
            "[common/glbatchMT.cbl:L864-L866]",
        ),
    ),
    _Note(
        "O-4",
        "ba-ACAS-DAL-Process's terminal geometry and curses environment "
        "settings, which are presentation with no database effect.",
        ("[common/glbatchMT.cbl:L339-L347]",),
    ),
    _Note(
        "O-5",
        "ba012's credential load is delegated to connection.load_rdb_data_once "
        "rather than duplicated, and its record-length comparison is recorded "
        "rather than resolved because it is ambiguity Q-4's own comparison.",
        ("[common/acas007.cbl:L614-L619]",),
    ),
    _Note(
        "O-6",
        "WS-Ledger and WS-Batch-Nos have no host variable and no column: they "
        "survive only inside the concatenated BATCH-KEY, reachable through the "
        "WS-Batch-Key9 redefinition of the same six bytes.",
        ("[copybooks/wsbatch.cob:L15]", "[copybooks/wsbatch.cob:L19]"),
    ),
    _Note(
        "O-7",
        "The group items Dates, Amounts and posting-data are groups and "
        "correctly not columns. Amounts is where comp-3 is declared, and its "
        "four elementary items inherit packed usage from it.",
        (
            "[copybooks/wsbatch.cob:L35]",
            "[copybooks/wsbatch.cob:L40]",
            "[copybooks/wsbatch.cob:L47]",
        ),
    ),
    _Note(
        "O-8",
        "The nine 88-level condition names of WS-Batch-Record are predicates "
        "over the record and belong to records/gl_batch.py; they are neither "
        "re-declared nor imported here.",
        ("[copybooks/wsbatch.cob:L16-L18]", "[copybooks/wsbatch.cob:L26-L32]"),
    ),
)

AMBIGUITIES: Final[tuple[_Note, ...]] = (
    _Note(
        "Q-3",
        "RESOLVED ON THE COMPILED ORACLE. What a negative binary value actually "
        "stores after passing through an unsigned host variable into an unsigned "
        "column. GnuCOBOL 3.2 applies ABSOLUTE-VALUE semantics - the ISO MOVE "
        "reading - and NOT a two's-complement reinterpretation of the source "
        "bytes: moving a signed binary-long into PIC 9(10) COMP measured "
        "-5 to 5, -1 to 1, -99 to 99, -20240101 to 20240101 and -2147483648 to "
        "2147483648, with the receiving field's own digit count then bounding "
        "the magnitude. signed_to_unsigned_host_variable already implemented "
        "exactly that reading, so the measurement confirms the implementation "
        "rather than changing it. The same probe re-confirms N-hv-render: the "
        "WS-MYSQL-EDIT render carries no sign for any of those inputs. The sign "
        "loss itself stays on record as A-11 because it is the defect; only the "
        "resulting value is settled.",
        (
            "[copybooks/wsbatch.cob:L36-L39]",
            "[common/glbatchMT.cbl:L287-L290]",
            "[mysql/ACASDB.sql:L86-L89]",
        ),
    ),
    _Note(
        "Q-4",
        "RESOLVED ON THE COMPILED ORACLE. Whether the declared record length or "
        "the field sum governs, which changes field alignment for the trailing "
        "fields. GnuCOBOL 3.2 measures function length of BOTH WS-Batch-Record "
        "and Batch-Record at 96, matching the field sum exactly with no padding "
        "in any sub-group, so the field sum governs, there is no trailing-field "
        "drift, and the maintainer's 98 does not hold under the target "
        "compiler. The 96-versus-98 contradiction stays on record as A-15 "
        "because the comment is frozen text; only the behaviour is settled.",
        (
            "[copybooks/wsbatch.cob:L7-L9]",
            "[copybooks/fdbatch.cob:L6-L8]",
            "[common/acas007.cbl:L581-L591]",
        ),
    ),
    _Note(
        "Q-5",
        "Where control resumes when the 901 branch's go to ba-rdbms-exit leaves "
        "the range of the perform ba012-Test-WS-Rec-Size-2 issued from "
        "aa010-main. exit section runs off the end of the PROCEDURE DIVISION, "
        "because Ca-Process-Logs and ca-Exit are paragraphs inside "
        "ba-Process-RDBMS section and no section follows, which in a called "
        "subprogram is an implicit exit program. That reading is implemented - "
        "the handler returns to its caller and the flat-file dispatch is "
        "skipped - and recorded here because unwinding a live perform stack is "
        "implementation-specific.",
        (
            "[common/acas007.cbl:L324]",
            "[common/acas007.cbl:L607]",
            "[common/acas007.cbl:L649-L650]",
            "[common/acas007.cbl:L653-L662]",
        ),
    ),
)


# ERRORS. Three named boundaries, each unreachable through `dispatch` on a correctly
# configured caller, each raised rather than silently papered over.


class FlatFileStoreNotMigratedError(RuntimeError):
    """Raised when a request would reach the indexed-file store.

    Fabricating a store would invent behaviour the specification does not have, and
    returning a success status would hide a caller that left ``File-System-Used`` at its
    copybook default of zero [copybooks/wssystem.cob:L112-L113], which is exactly the
    mistake this error exists to make loud.
    """


class BatchKeyViewsDisagreeError(ValueError):
    """Compatibility error retained for callers of the former reconciliation API.

    ``WS-Batch-Key`` [copybooks/wsbatch.cob:L14-L19] and ``WS-Batch-Key9`` [:L20-L21]
    are the SAME SIX BYTES - the second is a ``REDEFINES`` of the first - so in COBOL
    they cannot disagree. The record model now makes that structural, so no production
    path raises this class.
    """


class BridgeCalledOutsideHandlerError(RuntimeError):
    """Raised when the bridge is asked to open with no system record resident.

    :func:`dispatch` therefore records the system record for the duration of the call
    chain and :func:`glbatch_mt` reads it from there, which keeps :func:`glbatch_mt` at
    exactly the three parameters its ``CALL`` declares.
    """


class BridgeNotOpenError(RuntimeError):
    """Raised when a statement verb reaches the bridge with no connection open.

    ``Ws-Mysql-Cid`` is the connection handle ``MYSQL-1000-OPEN`` fills in
    [copybooks/mysql-variables.cpy:L65], and every statement paragraph performs
    ``MYSQL-1210-COMMAND`` with it.
    """


_HV_GROUP: Final[str] = "TD-GLBATCH-REC"

_EDIT_INTEGER_END: Final[int] = 20

_EDIT_FRACTION_START: Final[int] = 22

#: Truncation is a DELIBERATE loss of digits, so it cannot be done inside
#: :func:`~acas_posting.dal.connection.transport_decimal_context`, which traps
#: ``Inexact`` and ``Rounded`` precisely to make accidental loss impossible.
_TRUNCATING: Final[decimal.Context] = decimal.Context(
    prec=64,
    rounding=decimal.ROUND_DOWN,
    traps=[decimal.InvalidOperation, decimal.DivisionByZero, decimal.Overflow],
)


@dataclass(frozen=True, slots=True)
class BatchColumn:
    """One column of ``GLBATCH-REC`` with its whole provenance attached.

    Every member is derived from the generated data dictionary rather than transcribed,
    so a change in the frozen sources reaches this module through
    ``data_dictionary/acas_posting_dictionary.json`` and not through an edit here.

    Attributes:
        ordinal: The column's position in the frozen ``CREATE TABLE``, 1-based.
        column: The MySQL column name, hyphens and all.
        quoted: The same name backtick-quoted through
            :func:`~acas_posting.dal.connection.quote_identifier`.
        host_variable: The bridge's ``HV-`` item that carries it.
        copybook_field: The ``WS-Batch-Record`` item it comes from.
        dictionary_key: The dictionary key, ``GLBATCH-REC.<COLUMN>``.
        citation: ``loader.cite(dictionary_key)`` - the three-way locator.
        storage: ``INT``, ``DECIMAL`` or ``STR``; the carrier rule for R-2.
        hv_digits: Total digits of the host variable, or ``None`` if character.
        hv_integer_digits: Digits left of the implied point, or ``None``.
        hv_scale: Digits right of the implied point, or ``None``.
        hv_character_length: Character width, or ``None`` if numeric.
        hv_signed: Whether the HOST VARIABLE is signed. False for every numeric item of
            this group - there is not one ``S9`` in it.
        copybook_signed: Whether the COPYBOOK item is signed. True for the four
            ``binary-long`` dates, which is the whole of anomaly A-11.
        sql_type: The declared column type, verbatim from the schema.
        is_primary_key: True for ``BATCH-KEY`` alone.
        drift: One sentence per disagreement, from ``loader.drift_for``.
        record_path: The attribute path into :class:`GlBatchRecord`.
        anomaly_refs: Anomaly identifiers the dictionary already attaches.
        ambiguity_refs: Ambiguity identifiers the dictionary already attaches.
        edit_slice: The 1-based ``(offset, length)`` of the integer part in ``WS-MYSQL-
            EDIT``, or ``None`` for a character column.
        edit_fraction_slice: The same for the fraction part, or ``None``.
    """

    ordinal: int
    column: str
    quoted: str
    host_variable: str
    copybook_field: str
    dictionary_key: str
    citation: str
    storage: str
    hv_digits: int | None
    hv_integer_digits: int | None
    hv_scale: int | None
    hv_character_length: int | None
    hv_signed: bool
    copybook_signed: bool
    sql_type: str
    is_primary_key: bool
    drift: tuple[str, ...]
    record_path: tuple[str, ...]
    anomaly_refs: tuple[str, ...]
    ambiguity_refs: tuple[str, ...]
    edit_slice: tuple[int, int] | None
    edit_fraction_slice: tuple[int, int] | None

    @property
    def is_character(self) -> bool:
        """True when the host variable is ``PIC X(n)`` rather than numeric."""
        return self.hv_character_length is not None

    @property
    def is_decimal(self) -> bool:
        """True when the value is carried as :class:`decimal.Decimal`."""
        return self.storage == "DECIMAL"

    @property
    def loses_sign_at_the_bridge(self) -> bool:
        """True for the four date fields of anomaly A-11.

        Signed in the copybook and unsigned in the host variable, so the sign is
        discarded at :func:`bb000_hv_load` and never reaches the statement
        [copybooks/wsbatch.cob:L36-L39], [common/glbatchMT.cbl:L287-L290].
        """
        return self.copybook_signed and not self.hv_signed


def _record_paths() -> Mapping[str, tuple[str, ...]]:
    """Walk :class:`GlBatchRecord` for every field's dictionary key.

    Returns:
        Dictionary key mapped to the attribute path into a :class:`GlBatchRecord`
            instance, e.g. ``GLBATCH-REC.INPUT-GROSS`` to ``("amounts",
            "input_gross")``.
    """
    found: dict[str, tuple[str, ...]] = {}

    def walk(record: type, prefix: tuple[str, ...]) -> None:
        for trace in loader.trace_record(record):
            path = (*prefix, trace.attribute)
            if trace.group_type is not None:
                walk(trace.group_type, path)
            elif trace.dictionary_key is not None:
                found[trace.dictionary_key] = path

    walk(GlBatchRecord, ())
    return MappingProxyType(found)


def _edit_slices(
    integer_digits: int | None, scale: int | None
) -> tuple[tuple[int, int] | None, tuple[int, int] | None]:
    """Derive a host variable's ``WS-MYSQL-EDIT`` slices from its picture.

    The bridge moves each host variable into one edited field and then strings a fixed
    substring of it into the statement, for example ``FUNCTION TRIM (WS-MYSQL-
    EDIT(13:08))`` for a ``9(08) COMP`` item [common/glbatchMT.cbl:L1154]. The offsets
    look arbitrary but are not.

    Args:
        integer_digits: Digits left of the implied decimal point, or ``None`` for a
            character item.
        scale: Digits right of it, or ``None`` for a character item.

    Returns:
        The integer slice and the fraction slice, each as a 1-based ``(offset, length)``
            pair, and ``None`` where the bridge writes none.
    """
    if integer_digits is None:
        return (None, None)
    integer = (_EDIT_INTEGER_END + 1 - integer_digits, integer_digits)
    if not scale:
        return (integer, None)
    return (integer, (_EDIT_FRACTION_START, scale))


def _build_columns() -> tuple[BatchColumn, ...]:
    """Assemble :data:`COLUMNS` from the dictionary, in table ordinal order.

    Raises:
        LookupError: If the dictionary and ``records/gl_batch.py`` disagree about which
            fields exist.
    """
    paths = _record_paths()
    built: list[BatchColumn] = []
    for entry in loader.entries_for_table(TABLE):
        host_variable = entry.bridge_host_variable
        column = entry.column
        copybook = entry.copybook
        if host_variable is None or column is None or copybook is None:
            raise LookupError(
                f"{entry.key} is missing one of its three sides in the "
                f"generated dictionary; every column of {TABLE} must carry a "
                f"copybook field, a host variable and a column, because the "
                f"bridge is the authoritative mapping for this migration."
            )
        path = paths.get(entry.key)
        if path is None:
            raise LookupError(
                f"{entry.key} has no attribute on GlBatchRecord, so the "
                f"record module and the data dictionary disagree about "
                f"{TABLE}. Regenerate data_dictionary/"
                f"acas_posting_dictionary.json before using this module."
            )
        integer_slice, fraction_slice = _edit_slices(
            host_variable.integer_digits, host_variable.scale
        )
        built.append(
            BatchColumn(
                ordinal=column.ordinal,
                column=column.name,
                quoted=quote_identifier(column.name),
                host_variable=host_variable.name,
                copybook_field=copybook.name,
                dictionary_key=entry.key,
                citation=loader.cite(entry.key),
                storage=str(entry.cobol_python_storage),
                hv_digits=host_variable.digits,
                hv_integer_digits=host_variable.integer_digits,
                hv_scale=host_variable.scale,
                hv_character_length=host_variable.character_length,
                hv_signed=bool(host_variable.signed),
                copybook_signed=bool(copybook.signed),
                sql_type=column.sql_type,
                is_primary_key=bool(column.is_primary_key),
                drift=tuple(loader.drift_for(entry.key).details),
                record_path=path,
                anomaly_refs=tuple(entry.anomaly_refs),
                ambiguity_refs=tuple(entry.ambiguity_refs),
                edit_slice=integer_slice,
                edit_fraction_slice=fraction_slice,
            )
        )
    return tuple(built)


COLUMNS: Final[tuple[BatchColumn, ...]] = _build_columns()

COLUMN_NAMES: Final[tuple[str, ...]] = tuple(column.column for column in COLUMNS)

_BY_COLUMN: Final[Mapping[str, BatchColumn]] = MappingProxyType(
    {column.column: column for column in COLUMNS}
)

#: Indexed by host-variable name, because that is how ``bb200-Insert`` and
#: ``bb300-Update`` name their operands - ``MOVE HV-BATCH-KEY TO ...``.
_BY_HOST_VARIABLE: Final[Mapping[str, BatchColumn]] = MappingProxyType(
    {column.host_variable: column for column in COLUMNS}
)

#: ``GLBATCH-REC`` backtick-quoted once, since every statement names it.
_QUOTED_TABLE: Final[str] = quote_identifier(TABLE)

_QUOTED_KEY: Final[str] = quote_identifier(KEY_OF_REFERENCE.column_name)

#: The dictionary key of the primary-key column, DERIVED from the column table rather
#: than written out, so it cannot drift from
#: ``data_dictionary/acas_posting_dictionary.json`` (rule R-5).
_KEY_DICTIONARY_KEY: Final[str] = _BY_COLUMN[KEY_OF_REFERENCE.column_name].dictionary_key

#: The place value of ``WS-Ledger`` inside the six-digit key.
_LEDGER_DIGIT_SCALE: Final[int] = 10**5


def _logging_descriptors() -> Mapping[str, Any]:
    """Index ``Logging-Data``'s field descriptors by their COBOL name.

    ``WS-File-Key`` is ``pic x(64)`` [copybooks/wsfnctn.cob:L52] and every handler
    paragraph moves a literal into it, so those literals must be fitted to sixty-four
    characters exactly as a COBOL ``MOVE`` would - padded on the right with spaces,
    truncated on the right when too long.
    """
    return MappingProxyType({field.name: field for field in LoggingData.FIELDS})


_LOGGING_FIELDS: Final[Mapping[str, Any]] = _logging_descriptors()


def _record_descriptors() -> Mapping[str, Any]:
    """Index every ``WS-Batch-Record`` field descriptor by dictionary key.

    Used by :func:`bb100_unload_hvs` to apply the RECEIVING field's own truncation on
    the way back from the host variables. That truncation is real and not decorative.
    """
    indexed: dict[str, Any] = {}
    for group in (
        WsBatchKey,
        WsBatchKey9,
        GlBatchRecord,
        BatchDates,
        BatchAmounts,
        PostingData,
    ):
        for field in getattr(group, "FIELDS", ()):
            indexed[field.dictionary_key] = field
    return MappingProxyType(indexed)


_RECORD_FIELDS: Final[Mapping[str, Any]] = _record_descriptors()


# WORKING STORAGE. Neither program is declared `IS INITIAL` [common/acas007.cbl:L12],
# [common/glbatchMT.cbl:L10], so WORKING-STORAGE PERSISTS ACROSS CALLS and both keep
# state the caller never sees.


@dataclass(slots=True)
class _HandlerWorkingStorage:
    """The residue ``acas007`` keeps between calls.

    Attributes:
        a: ``77 A pic 9(4)`` [common/acas007.cbl:L240], the caller's record length.
        b: ``77 B pic 9(4)`` [:L241], the handler's own record length.
        display_blk: ``Display-Blk pic x(75)``, the 901 message. Built and copied into
            ``SQL-Msg`` [:L593-L602]; the two ``display``s that follow are omission O-3.
        cobol_file_status: ``Cobol-File-Status pic 9`` with ``88 Cobol-File-Eof value
            1``, the handler's own end-of-file flag.
        linkage_system_record: The ``System-Record`` of the call in progress. Reproduces
            LINKAGE residency, not added state.
        transport: The caller's transport declaration, forwarded to
            :func:`~acas_posting.dal.connection.mysql_1000_open`. Has NO COBOL
            counterpart and is not compared - see :func:`declare_connection_policy`.
        allow_frozen_placeholder_credentials: The caller's declaration about the shipped
            placeholder user and password. Also has no COBOL counterpart - see
            :func:`declare_connection_policy`.
    """

    a: int = 0
    b: int = 0
    display_blk: str = ""
    cobol_file_status: int = 0
    linkage_system_record: SystemRecord | None = None
    transport: TransportSecurity | None = None
    allow_frozen_placeholder_credentials: bool | None = None


@dataclass(slots=True)
class _BridgeWorkingStorage:
    """The residue ``glbatchMT`` keeps between calls.

    Attributes:
        connection: The handle ``MYSQL-1000-OPEN`` leaves behind
            [common/glbatchMT.cbl:L427] and ``MYSQL-1980-CLOSE`` releases [:L451]. One
            connection per file-open, no pool - rule R-3.
        ws_where: ``WS-Where``, the single-predicate clause every positioning and write
            paragraph builds [:L851-L861 and siblings].
        j: ``J pic s9(4) comp-5``, the ``with pointer`` cursor into ``WS-Where``.
        most_relation: ``MOST-Relation pic xxx``. Left as spaces unless the ``evaluate``
            sets it - anomaly N-relation-nodefault.
        host_variables: ``01 TD-GLBATCH-REC`` [:L281-L302], keyed by host variable name.
            ``bb000-HV-Load`` fills it, ``bb200-Insert`` and ``bb300-Update`` read it,
            and a fetch overwrites it.
        dal_data: ``01 DAL-Data`` [common/glbatchMT.scb:L247-L251], the bridge's OWN
            cursor block.
        ws_mysql_count_rows: ``Ws-Mysql-Count-Rows`` [copybooks/mysql-
            variables.cpy:L73], ONE field written by TWO things - ``MYSQL-1210-COMMAND``
            stores the affected-row count of an insert, update or delete, and
            ``MYSQL-1220-STORE-RESULT`` stores the row count of a select.
        ws_mysql_error_number: ``WS-MYSQL-Error-Number``, the three-character field
            compared against the literal ``"0 "`` [:L830].
        ws_mysql_error_message: ``WS-MYSQL-Error-Message``.
        ws_mysql_sqlstate: ``WS-MYSQL-SQLstate``.
    """

    connection: Any = None
    ws_where: str = ""
    j: int = 1
    most_relation: str = MOST_RELATION_DEFAULT
    host_variables: dict[str, int | decimal.Decimal | str] = dataclasses.field(
        default_factory=dict
    )
    dal_data: cursor_state.CursorStateTable = dataclasses.field(
        default_factory=cursor_state.CursorStateTable
    )
    ws_mysql_count_rows: int = 0
    ws_mysql_error_number: str = "0  "
    ws_mysql_error_message: str = ""
    ws_mysql_sqlstate: str = ""


_HANDLER: Final[_HandlerWorkingStorage] = _HandlerWorkingStorage()
_BRIDGE_WS: Final[_BridgeWorkingStorage] = _BridgeWorkingStorage()
_TRANSPORT_NOT_SUPPLIED: Final[object] = object()


def reset_working_storage() -> None:
    """Clear both programs' working storage and this table's cursor state.

    No COBOL counterpart: a compiled run cannot reset a program's WORKING-STORAGE
    without starting a new process.
    """
    if _BRIDGE_WS.connection is not None:
        mysql_1980_close(_BRIDGE_WS.connection)
        mysql_1999_exit()
    _HANDLER.a = 0
    _HANDLER.b = 0
    _HANDLER.display_blk = ""
    _HANDLER.cobol_file_status = 0
    _HANDLER.linkage_system_record = None
    _HANDLER.transport = None
    _HANDLER.allow_frozen_placeholder_credentials = None
    _BRIDGE_WS.connection = None
    _BRIDGE_WS.ws_where = ""
    _BRIDGE_WS.j = 1
    _BRIDGE_WS.most_relation = MOST_RELATION_DEFAULT
    _BRIDGE_WS.host_variables.clear()
    _BRIDGE_WS.ws_mysql_count_rows = 0
    _BRIDGE_WS.ws_mysql_error_number = "0  "
    _BRIDGE_WS.ws_mysql_error_message = ""
    _BRIDGE_WS.ws_mysql_sqlstate = ""
    _BRIDGE_WS.dal_data.reset(TABLE)
    cursor_state.reset(TABLE)


def declare_connection_policy(
    *,
    transport: TransportSecurity | None = None,
    allow_frozen_placeholder_credentials: bool | None = None,
) -> None:
    """Record a per-handler connection-policy declaration for later opens.

    ⛔ NORMALLY THERE IS NOTHING TO CALL HERE. The connection policy of a run is
    ONE object installed once by the deployment -
    :func:`acas_posting.dal.connection.set_connection_policy` - and every open
    that declares nothing resolves to it, this handler's included. This function
    exists only to NARROW that policy for this one table, which no in-scope path
    does; leaving it uncalled is the ordinary case and is what keeps the twenty
    handlers of this package saying the same thing about the same connection.

    NO COBOL COUNTERPART, AND NOTHING COMPARED MOVES BY A CHARACTER.
    ``ba020-Process-Open`` marshals the six ``RDB-Data`` items and performs
    ``MYSQL-1000-OPEN`` [common/glbatchMT.cbl:L402-L427] with no notion of
    transport security at all - the C interface passes a literal zero client-flag
    word and no TLS arguments. A declaration therefore changes what
    :func:`~acas_posting.dal.connection.mysql_1000_open` reports about a
    connection, and in the opt-in strict configurations which connections it
    permits - never a stored value, a status pair, a statement text or a table
    dump (rules R-3, R-4).

    ``glbatch_mt`` still takes exactly the bridge's three positional parameters
    [common/acas007.cbl:L641-L644], and ``dispatch`` keeps the handler's five
    positional parameters [:L265-L271]. The facade may additionally forward the
    caller's keyword-only transport declaration; this function remains the
    process-level declaration route for callers that configure policy once.

    Args:
        transport: The transport declaration. ``None`` - the default - defers to
            the ONE installed policy, which is what every in-scope caller wants.
        allow_frozen_placeholder_credentials: ``True`` declares that the
            maintainer's shipped placeholder user and password in ``SYSTEM-REC``
            are the intended credentials and the server is disposable. ``None`` -
            the default - defers to the installed policy; ``False`` states
            positively that no declaration is made for this table.

    Examples:
        The declaration a deployment makes ONCE, and not here::

            from acas_posting.dal import connection

            connection.set_connection_policy(
                connection.ConnectionPolicy(
                    transport=connection.TransportSecurity(ca_file="/etc/ssl/ca.pem"),
                )
            )
    """
    _HANDLER.transport = transport
    #  NOT coerced with `bool(...)`: `None` is a THIRD state here - "this handler
    #  declares nothing, resolve it from the one installed policy" - and coercing
    #  it to False would turn an absent declaration into a positive refusal to
    #  declare, which is what made this handler's policy path diverge from its
    #  nineteen siblings. See `connection.set_connection_policy`.
    _HANDLER.allow_frozen_placeholder_credentials = (
        allow_frozen_placeholder_credentials
    )
    #  THE POLICY IS REPORTED, NOT THE PATHS IT NAMES. `%r` on a
    #  `TransportSecurity` renders `ca_file`, `certificate_file` and `key_file` -
    #  filesystem paths, one of which is a PRIVATE KEY (CWE-532). What an operator
    #  needs is whether the server will be authenticated and the session encrypted,
    #  and that is one boolean.
    _LOG.debug(
        "connection policy declared for %s: server_verified=%s "
        "placeholder_credentials=%s",
        BRIDGE,
        transport.verifies_the_server(),
        _HANDLER.allow_frozen_placeholder_credentials,
    )


def _store_ws_file_key(logging_data: LoggingData, text: str) -> None:
    """``move <literal> to WS-File-Key`` with the receiving field's own fitting.

    ``WS-File-Key`` is ``pic x(64)`` [copybooks/wsfnctn.cob:L52], so a shorter literal
    is padded on the right with spaces and a longer one is truncated on the right.

    Args:
        logging_data: The caller's ``Logging-Data`` block, mutated in place.
        text: The sending literal or field.
    """
    fitted = _LOGGING_FIELDS["WS-File-Key"].store(text)
    logging_data.ws_file_key = str(fitted)


def _store_sql_msg(logging_data: LoggingData, text: str) -> None:
    """``move <field> to SQL-Msg``, fitted to ``pic x(512)``."""
    logging_data.sql_msg = str(_LOGGING_FIELDS["SQL-Msg"].store(text))


def signed_to_unsigned_host_variable(
    value: int, digits: int, *, dictionary_key: str
) -> int:
    """Move a signed value into an unsigned ``PIC 9(n) COMP`` host variable.

    ANOMALY A-11, AND THE ONLY PLACE THE SIGN IS DISCARDED. ``Entered``, ``Proofed``,
    ``Posted`` and ``Stored`` are ``binary-long`` and therefore signed
    [copybooks/wsbatch.cob:L36-L39]; ``HV-ENTERED`` and its three siblings are ``PIC
    9(10) COMP`` and therefore unsigned [common/glbatchMT.cbl:L287-L290].

    Args:
        value: The signed value from the record, as an ``int``.
        digits: The receiving host variable's digit count, from the dictionary.
        dictionary_key: The field's dictionary key, used only in the log line that makes
            the loss visible to an operator.

    Returns:
        The value the host variable holds after the move: non-negative, and never wider
            than ``digits``.
    """
    magnitude = abs(int(value))
    stored = magnitude % (10**digits)
    if value < 0:
        # ANOMALY A-11 at the moment it happens. Neither raised nor reported,
        # because the compiled program neither refuses it nor reports it, and
        # either would be behaviour the specification does not have.
        #  IT IS SILENT, in both senses. The frozen bridge neither reports nor
        #  refuses the narrowing - its own comment is the only trace it leaves - so a
        #  record here is a diagnostic the compiled program cannot produce (rule
        #  R-4). And the record it used to emit interpolated the VALUE, twice: the
        #  signed figure and the unsigned figure actually stored, which for this
        #  record are batch control totals (CWE-532). The anomaly is reproduced by
        #  the narrowing itself and documented in
        #  `docs/migration/anomaly-log.md`; ambiguity Q-3, resolved against
        #  GnuCOBOL 3.2, is recorded in `docs/migration/ambiguity-resolutions.md`.
        #
        #  The frozen `if` is kept with an empty body so that rule R-5's reader
        #  finds the test and finds that it reports nothing.
        pass
    return stored


def _store_host_variable(
    column: BatchColumn, value: object
) -> int | decimal.Decimal | str:
    """Move one record field into its host variable, with the HV's own rules.

    Args:
        column: The column being loaded, carrying its host variable's metadata.
        value: The record field's current value.

    Returns:
        The value the host variable holds, as ``str``, ``int`` or
            :class:`decimal.Decimal` according to :attr:`BatchColumn.storage`.
    """
    if column.hv_character_length is not None:
        text = "" if value is None else str(value)
        width = column.hv_character_length
        return text[:width].ljust(width)

    digits = column.hv_digits or 0
    scale = column.hv_scale or 0
    integer_digits = column.hv_integer_digits or digits

    if column.is_decimal:
        # `Input-Gross` and its three siblings.
        with decimal.localcontext(transport_decimal_context()):
            carried = value if isinstance(value, decimal.Decimal) else decimal.Decimal(
                str(value)
            )
        quantum = decimal.Decimal(1).scaleb(-scale)
        truncated = _TRUNCATING.quantize(carried, quantum)
        # Unsigned at all three layers for these four, so an absolute value is the
        # faithful move rather than the sign loss of anomaly A-11
        # [common/glbatchMT.cbl:L291-L294], [mysql/ACASDB.sql:L90-L93].
        magnitude = truncated.copy_abs()
        modulus = decimal.Decimal(10) ** integer_digits
        if magnitude >= modulus:
            # High-order digits beyond the host variable's twelve integer positions are
            # discarded, as a COBOL store does without `ON SIZE ERROR`. `remainder` and
            # not `remainder_near`.
            magnitude = _TRUNCATING.remainder(magnitude, modulus)
            magnitude = _TRUNCATING.quantize(magnitude, quantum)
        return magnitude

    integer = 0 if value is None else int(value)
    if column.copybook_signed and not column.hv_signed:
        # The four date fields. ANOMALY A-11, applied here and nowhere else.
        return signed_to_unsigned_host_variable(
            integer, digits, dictionary_key=column.dictionary_key
        )
    return abs(integer) % (10**digits)


def _read_record_field(batch: GlBatchRecord, column: BatchColumn) -> object:
    """Read one field out of the record by its derived attribute path."""
    target: object = batch
    for attribute in column.record_path:
        target = getattr(target, attribute)
    return target


def _write_record_field(
    batch: GlBatchRecord, column: BatchColumn, value: object
) -> None:
    """Write one field into the record, applying the RECEIVING field's rules.

    ``bb100-UnloadHVs`` moves each host variable back into the record, and the receiving
    item is often NARROWER than the sending one - eight digits into six for the key
    [common/glbatchMT.cbl:L1107], eight into five for ``Batch-Start`` [:L1127], three
    into two for ``Items`` [:L1108].
    """
    descriptor = _RECORD_FIELDS[column.dictionary_key]
    stored = descriptor.store(value)
    target: object = batch
    for attribute in column.record_path[:-1]:
        target = getattr(target, attribute)
    setattr(target, column.record_path[-1], stored)


def batch_key_image(batch: GlBatchRecord) -> str:
    """Return the six characters ``WS-Batch-Record (1:6)`` holds.

    Every ``WHERE`` clause in the bridge takes its key value from a RAW CHARACTER
    SUBSTRING of the record buffer rather than from a typed field - ``WS-Batch-Record
    (K:L)`` with ``K`` 1 and ``L`` 6, from the key of reference
    [common/glbatchMT.scb:L231-L241].

    Args:
        batch: The record whose key is wanted. Both readings are reconciled first, so it
            does not matter which one the caller populated.

    Returns:
        Exactly six characters.
    """
    synchronise_batch_key_views(batch)
    return f"{int(batch.ws_batch_key9.ws_batch_key9):06d}"


def synchronise_batch_key_views(batch: GlBatchRecord) -> int:
    """Return the value shared by ``WS-Batch-Key`` and ``WS-Batch-Key9``.

    The record model binds both names to one backing key, so this former
    reconciliation boundary is now an idempotent compatibility function.

    Args:
        batch: The record whose shared six-byte key is read.

    Returns:
        The six-digit key.
    """
    value = int(batch.ws_batch_key9.ws_batch_key9)
    batch.ws_batch_key9.ws_batch_key9 = value
    return value


def bb000_hv_load(batch: GlBatchRecord) -> Mapping[str, int | decimal.Decimal | str]:
    """``bb000-HV-Load Section.`` [common/glbatchMT.cbl:L1060-L1092].

    1. ``initialize TD-GLBATCH-REC`` IS THE FIRST STATEMENT [:L1068], so an unset field
    becomes zero or space and NEVER SQL ``NULL``. Agent Action Plan section 0.6.2,
    verbatim.

    Args:
        batch: The record to load from. Mutated only insofar as
            :func:`synchronise_batch_key_views` brings its two key readings into
            agreement.

    Returns:
        The host-variable group, keyed by host-variable name, with all twenty-one
            entries present.
    """
    # `initialize TD-GLBATCH-REC.` [common/glbatchMT.cbl:L1068]. Cleared rather than
    # replaced so the group keeps its identity across calls, which is what WORKING-
    # STORAGE residency means.
    _BRIDGE_WS.host_variables.clear()

    synchronise_batch_key_views(batch)

    for column in COLUMNS:
        _BRIDGE_WS.host_variables[column.host_variable] = _store_host_variable(
            column, _read_record_field(batch, column)
        )
    return MappingProxyType(dict(_BRIDGE_WS.host_variables))


def bb100_unload_hvs(
    row: Mapping[str, object] | None, batch: GlBatchRecord
) -> None:
    """``bb100-UnloadHVs Section.`` [common/glbatchMT.cbl:L1097-L1131].

    *> Load the data buffer in the interface with data from the host *> variables. (init
    moved lower) *> *> NULL fields must not be returned in the buffer.

    Args:
        row: The fetched row, keyed by column name, or ``None`` for an end-of-result.
        batch: The record to unload into, mutated in place.
    """
    _initialize_ws_batch_record(batch, with_filler=False)
    if row is None:
        return

    for column in COLUMNS:
        if column.column not in row:
            # The bridge's own note says SQL filters every column so it always has a
            # proper value, and every column is `NOT NULL`, so a missing key means the
            # statement was not `SELECT *`.
            continue
        value = row[column.column]
        _BRIDGE_WS.host_variables[column.host_variable] = _store_host_variable(
            column, value
        )
        _write_record_field(batch, column, value)

    # The key's two readings are one storage in COBOL, so the group reading is brought
    # into line with the redefinition the move above wrote
    # [copybooks/wsbatch.cob:L14-L21].
    synchronise_batch_key_views(batch)


def _initialize_ws_batch_record(batch: GlBatchRecord, *, with_filler: bool) -> None:
    """``initialize WS-Batch-Record``, in both of the bridge's two forms.

    ANOMALY N-initialize. The plain form [common/glbatchMT.cbl:L1106] sets every named
    elementary item to its category's zero - numerics to zero, alphanumerics to spaces -
    and LEAVES ``FILLER`` ITEMS ALONE. The ``with filler`` form [:L589] clears the
    ``FILLER`` items too.

    Args:
        batch: The record to initialise, mutated in place.
        with_filler: True for the ``with filler`` form, which is the EOF2 path.
    """
    for column in COLUMNS:
        descriptor = _RECORD_FIELDS[column.dictionary_key]
        blank: object = "" if column.storage == "STR" else 0
        _write_record_field(batch, column, descriptor.store(blank))
    batch.ws_batch_key.ws_ledger = 0
    batch.ws_batch_key.ws_batch_nos = 0
    batch.ws_batch_key9.ws_batch_key9 = 0
    if with_filler:
        # `initialize ... with filler` [common/glbatchMT.cbl:L589]. Nothing
        # further to clear: this record declares no FILLER item, so the two
        # forms coincide here. Recorded, not relied on - see the docstring.
        #  NO RECORD. `initialize ... with filler` displays nothing; that the
        #  with-filler and plain forms coincide for this record - it declares no
        #  FILLER item - is a fact about the layout, recorded in this comment where a
        #  reader of the code will find it, not in a run's log stream (rule R-4).
        #
        #  The frozen `if` is kept with an empty body so that rule R-5's reader
        #  finds the with-filler branch and finds that it has nothing to do.
        pass


# bb200-Insert and bb300-Update - the two statement builders.


def _bound_values() -> tuple[object, ...]:
    """Return the twenty-one host-variable values in column order.

    The bridge renders each of them into statement text through ``WS-MYSQL-EDIT``; this
    module binds the same values as parameters instead, for the reason the module
    docstring gives under VALUES ARE BOUND.
    """
    return tuple(
        _BRIDGE_WS.host_variables[column.host_variable] for column in COLUMNS
    )


def mt_bb200_insert() -> tuple[str, tuple[object, ...]]:
    """``bb200-Insert Section.`` [common/glbatchMT.cbl:L1135-L1414].

    followed by one three-part group per column - the quoted name and an opening double
    quote, the value sliced out of ``WS-MYSQL-EDIT``, then a closing double quote and a
    comma - and finally ``";"`` and a ``X"00"`` terminator [:L1407-L1410].

    Returns:
        The statement with ``%s`` placeholders, and the values to bind.
    """
    assignments = ", ".join(f"{column.quoted}=%s" for column in COLUMNS)
    statement = f"INSERT INTO {_QUOTED_TABLE} SET {assignments};"
    return (statement, _bound_values())


def mt_bb300_update() -> tuple[str, tuple[object, ...]]:
    """``bb300-Update Section.`` [common/glbatchMT.cbl:L1418-L1701].

    ANOMALY N-insert-set-syntax, second half: THE PRIMARY KEY IS AMONG THE COLUMNS IT
    SETS [:L1433-L1441].

    Returns:
        The statement with ``%s`` placeholders, and the values to bind: the twenty-one
            column values followed by the key the ``WHERE`` compares.
    """
    assignments = ", ".join(f"{column.quoted}=%s" for column in COLUMNS)
    statement = (
        f"UPDATE {_QUOTED_TABLE} SET {assignments} WHERE {_BRIDGE_WS.ws_where};"
    )
    return (statement, (*_bound_values(), _BRIDGE_WS.host_variables["HV-BATCH-KEY"]))


def _build_where(relation: str, key_value: str) -> str:
    """Build the single-predicate ``WHERE`` clause every paragraph builds.

    The construction is [common/glbatchMT.scb:L644-L650], quoted in full in the module
    docstring. Three properties are reproduced and one is deliberately changed.

    Args:
        relation: The relation, padded or not.
        key_value: The six-character key image. Recorded on the clause for logging; the
            caller binds it.

    Returns:
        The clause, without a leading ``WHERE``, as ``ba080`` and its siblings leave it
            in ``WS-Where``.
    """
    trimmed = relation.strip()
    clause = f"{_QUOTED_KEY} {trimmed} %s" if trimmed else f"{_QUOTED_KEY} %s"
    _BRIDGE_WS.ws_where = clause
    _BRIDGE_WS.j = len(clause) + 1
    _BRIDGE_WS.most_relation = relation
    #  NEITHER THE CLAUSE NOR THE KEY IS LOGGED. `WS-Where` is the composed SQL
    #  `WHERE` clause and `key_value` is the batch key it was built around, so
    #  together they name the exact batch being operated on (CWE-532). The clause is
    #  still BUILT and still stored, because the bridge stores it and the caller can
    #  read it; it simply does not reach a log record.
    return clause


# THE BRIDGE - glbatchMT `Procedure Division using File-Access ACAS-DAL-Common-data WS-
# Batch-Record.` [common/glbatchMT.cbl:L334-L336], reached only by `call "glbatchMT"`
# from `ba020-Process-DAL` in the handler [common/acas007.cbl:L641-L644].

#: ``01 Ws-Mysql-Error-Number pic x(5)`` [copybooks/mysql-variables.cpy:L84]. The
#: maintainer's own note there records it was "changed to 5 char 18/09/16", which
#: matters.
_WS_MYSQL_ERROR_NUMBER_WIDTH: Final[int] = 5

_WS_MYSQL_SQLSTATE_WIDTH: Final[int] = 5

_WS_MYSQL_ERROR_MESSAGE_WIDTH: Final[int] = 160

_WS_MYSQL_ERROR_NUMBER_ZERO: Final[str] = "0".ljust(_WS_MYSQL_ERROR_NUMBER_WIDTH)

_SQL_ERR_ZERO: Final[str] = "0".ljust(5)


def _pic_x(text: str, width: int) -> str:
    """Fit ``text`` to ``pic x(width)`` - pad right with spaces, truncate right.

    The only COBOL ``MOVE`` rule this module needs that the dictionary's own descriptors
    do not already supply, because these three fields belong to ``mysql-variables.cpy``
    rather than to any record in the data dictionary.
    """
    return text[:width] if len(text) >= width else text.ljust(width)


def _mysql_error_fields(error: BaseException | None) -> tuple[str, str, str]:
    """Stand in for the driver's three error-reporting entry points.

    Those three C functions read the connection's last error, so their Python equivalent
    is the exception the driver raised.

    Args:
        error: The driver's exception, or ``None`` when nothing failed.

    Returns:
        ``(WS-MYSQL-Error-Number, WS-MYSQL-SQLstate, WS-MYSQL-Error-Message)``, each
            fitted to its own picture width.
    """
    if error is None:
        return (_WS_MYSQL_ERROR_NUMBER_ZERO, _pic_x("", _WS_MYSQL_SQLSTATE_WIDTH), "")
    errno = getattr(error, "errno", None)
    sqlstate = getattr(error, "sqlstate", None)
    message = getattr(error, "msg", None)
    # A driver exception with no error number at all still took the failure path, and
    # reporting it as "0" would send it through the errno test's false arm and lose it.
    errno_text = str(int(errno)) if isinstance(errno, int) and errno else "2000"
    return (
        _pic_x(errno_text, _WS_MYSQL_ERROR_NUMBER_WIDTH),
        _pic_x("" if sqlstate is None else str(sqlstate), _WS_MYSQL_SQLSTATE_WIDTH),
        _pic_x(
            str(error) if message is None else str(message),
            _WS_MYSQL_ERROR_MESSAGE_WIDTH,
        ),
    )


def _record_driver_error(error: BaseException | None) -> None:
    """Store the driver's three fields into the bridge's working storage.

    Separated from :func:`_mysql_error_fields` so that the storing and the reading are
    distinct, exactly as the ``call ... using`` statements and the later ``move``s of
    those same fields are distinct in the frozen source.
    """
    (
        _BRIDGE_WS.ws_mysql_error_number,
        _BRIDGE_WS.ws_mysql_sqlstate,
        _BRIDGE_WS.ws_mysql_error_message,
    ) = _mysql_error_fields(error)


def _errno_is_non_zero() -> bool:
    """``if WS-MYSQL-Error-Number not = "0 "`` [common/glbatchMT.cbl:L830].

    The identical test appears at [:L885] in ``ba080``, [:L966] in ``ba085``, [:L1012]
    in ``ba090``, [:L511] in ``ba040`` and [:L584] in ``ba041``.
    """
    return _BRIDGE_WS.ws_mysql_error_number != _WS_MYSQL_ERROR_NUMBER_ZERO


def _bridge_cursor() -> Any:
    """Hand out a cursor on the bridge's own connection.

    The positioning verbs are owned by :mod:`acas_posting.dal.cursor_state`, which
    issues the statement itself and therefore takes a cursor rather than a connection.
    That is the boundary the frozen source draws too.

    Raises:
        BridgeNotOpenError: If ``fn-Open`` has not been performed.
    """
    if _BRIDGE_WS.connection is None:
        raise BridgeNotOpenError(
            f"{BRIDGE} was asked for a statement with Ws-Mysql-Cid still null: "
            f"perform fn-Open (File-Function 1) through "
            f"{HANDLER}.dispatch first"
        )
    return acquire_cursor(_BRIDGE_WS.connection)  # type: ignore[arg-type]


def mt_ba_acas_dal_process(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    batch: GlBatchRecord,
) -> None:
    """``ba-ACAS-DAL-Process section.`` [common/glbatchMT.cbl:L338-L347].

    OMISSION O-4: none of it is reproduced. The Agent Action Plan excludes presentation
    entirely - section 0.3.4 records that the curses screen section "is removed rather
    than reimplemented" - and these four statements have no database effect whatsoever.

    Args:
        file_access: ``File-Access``, the first bridge parameter.
        dal_common: ``ACAS-DAL-Common-data``, the second.
        batch: ``WS-Batch-Record``, the third.
    """
    mt_ba010_initialise(file_access, dal_common, batch)


def mt_ba010_initialise(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    batch: GlBatchRecord,
) -> None:
    """``ba010-Initialise.`` [common/glbatchMT.cbl:L349-L395].

    The consequence is load-bearing and shows up in three paragraphs.

    Args:
        file_access: ``File-Access``.
        dal_common: ``ACAS-DAL-Common-data``.
        batch: ``WS-Batch-Record``.
    """
    logging_data = file_access.logging_data
    # ANOMALY N-nostatus [common/glbatchMT.cbl:L351-L352]: `we_error` and `fs_reply` are
    # DELIBERATELY NOT touched here. Do not add them.
    _BRIDGE_WS.ws_mysql_error_message = ""
    _BRIDGE_WS.ws_mysql_error_number = _pic_x("", _WS_MYSQL_ERROR_NUMBER_WIDTH)
    logging_data.ws_log_where = _LOGGING_FIELDS["WS-Log-Where"].store("")
    logging_data.ws_file_key = _LOGGING_FIELDS["WS-File-Key"].store("")
    logging_data.sql_msg = _LOGGING_FIELDS["SQL-Msg"].store("")
    logging_data.sql_err = _LOGGING_FIELDS["SQL-Err"].store("")
    logging_data.sql_state = _LOGGING_FIELDS["SQL-State"].store("")

    function = int(file_access.file_function)
    if function == FileFunction.OPEN:
        mt_ba020_process_open(file_access, dal_common, batch)
        return
    if function == FileFunction.CLOSE:
        mt_ba030_process_close(file_access, dal_common, batch)
        return
    if function == FileFunction.READ_NEXT:
        mt_ba040_process_read_next(file_access, dal_common, batch)
        return
    if function == FileFunction.READ_INDEXED:
        mt_ba050_process_read_indexed(file_access, dal_common, batch)
        return
    if function == FileFunction.WRITE:
        mt_ba070_process_write(file_access, dal_common, batch)
        return
    # `when 6 *> DELETE-ALL Special` [common/glbatchMT.cbl:L385-L386]. THE HANDLER HAS
    # NO SUCH ARM [common/acas007.cbl:L338-L357].
    if function == FileFunction.DELETE_ALL:
        mt_ba085_process_delete_all(file_access, dal_common, batch)
        return
    if function == FileFunction.RE_WRITE:
        mt_ba090_process_rewrite(file_access, dal_common, batch)
        return
    if function == FileFunction.DELETE:
        mt_ba080_process_delete(file_access, dal_common, batch)
        return
    if function == FileFunction.START:
        mt_ba060_process_start(file_access, dal_common, batch)
        return
    mt_ba100_bad_function(file_access, dal_common, batch)


def mt_ba020_process_open(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    batch: GlBatchRecord,
) -> None:
    """``ba020-Process-Open.`` [common/glbatchMT.cbl:L397-L439].

    THE OPEN MODE IS NOT TESTED HERE. ``fn-Input``, ``fn-I-O`` and ``fn-Output`` all
    arrive as ``File-Function`` 1 and all open a database connection.

    Args:
        file_access: ``File-Access``; receives the status pair and log fields.
        dal_common: ``ACAS-DAL-Common-data``, forwarded to the logger.
        batch: ``WS-Batch-Record``. Untouched by this paragraph.
    """
    logging_data = file_access.logging_data
    system_record = _HANDLER.linkage_system_record
    if system_record is None:
        raise BridgeCalledOutsideHandlerError(
            f"{BRIDGE} was asked to open with no System-Record resident: "
            f"call {HANDLER}.dispatch, which is the only caller "
            f"[common/acas007.cbl:L640-L645]"
        )

    logging_data.ws_no_paragraph = _LOGGING_FIELDS["ws-No-Paragraph"].store(
        WS_NO_PARAGRAPH_BRIDGE["ba020-Process-Open"]
    )
    outcome: OpenOutcome = mysql_1000_open(
        system_record,
        ws_no_paragraph=int(logging_data.ws_no_paragraph),
        we_error=int(file_access.we_error),
        transport=_HANDLER.transport,
        allow_frozen_placeholder_credentials=(
            _HANDLER.allow_frozen_placeholder_credentials
        ),
    )
    mysql_1090_exit(outcome)
    _BRIDGE_WS.connection = outcome.connection
    file_access.fs_reply = int(outcome.fs_reply)
    file_access.we_error = int(outcome.we_error)
    logging_data.ws_no_paragraph = _LOGGING_FIELDS["ws-No-Paragraph"].store(
        outcome.ws_no_paragraph
    )
    logging_data.sql_err = _LOGGING_FIELDS["SQL-Err"].store(outcome.sql_err)
    _store_sql_msg(logging_data, outcome.sql_msg)
    logging_data.sql_state = _LOGGING_FIELDS["SQL-State"].store(outcome.sql_state)

    if int(file_access.fs_reply) != int(FsReply.SUCCESS):
        mt_ba999_end(file_access, dal_common, batch)
        return

    _store_ws_file_key(logging_data, "OPEN GLBATCH")
    cursor_state.reset(TABLE)
    mt_ba999_end(file_access, dal_common, batch)


def mt_ba030_process_close(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    batch: GlBatchRecord,
) -> None:
    """``ba030-Process-Close.`` [common/glbatchMT.cbl:L441-L454].

    ``MYSQL-1980-CLOSE`` is performed WHATEVER the state of the handle, and its status
    is not tested afterwards, so a close always reaches ``ba999-end``.

    Args:
        file_access: ``File-Access``.
        dal_common: ``ACAS-DAL-Common-data``.
        batch: ``WS-Batch-Record``. Untouched.
    """
    logging_data = file_access.logging_data
    mt_ba998_free(file_access, dal_common, batch, only_if_active=True)
    logging_data.ws_no_paragraph = _LOGGING_FIELDS["ws-No-Paragraph"].store(
        WS_NO_PARAGRAPH_BRIDGE["ba030-Process-Close"]
    )
    _store_ws_file_key(logging_data, "CLOSE GLBATCH")
    mysql_1980_close(_BRIDGE_WS.connection)
    mysql_1999_exit()
    _BRIDGE_WS.connection = None
    mt_ba999_end(file_access, dal_common, batch)


def mt_ba040_process_read_next(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    batch: GlBatchRecord,
) -> None:
    """``ba040-Process-Read-Next.`` [common/glbatchMT.cbl:L456-L529].

    The maintainer's own inline ``*> nom uses > ??`` at [:L472] is the record of anomaly
    A9 in :mod:`acas_posting.dal.cursor_state`.

    Args:
        file_access: ``File-Access``; receives the status pair and log fields.
        dal_common: ``ACAS-DAL-Common-data``, forwarded to the logger.
        batch: ``WS-Batch-Record``; a delivered row is unloaded into it.
    """
    logging_data = file_access.logging_data
    state = _BRIDGE_WS.dal_data.state_for(TABLE, cursor_state.CursorSlot.PRIMARY)
    if state.cursor_not_active():
        logging_data.ws_no_paragraph = _LOGGING_FIELDS["ws-No-Paragraph"].store(
            WS_NO_PARAGRAPH_BRIDGE["ba040-Process-Read-Next"]
        )
        _build_where(
            cursor_state.SEQUENTIAL_READ_START[TABLE].relation.padded,
            cursor_state.SEQUENTIAL_READ_START[TABLE].low_key,
        )
    mt_ba041_reread(file_access, dal_common, batch)


def mt_ba041_reread(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    batch: GlBatchRecord,
) -> None:
    """``ba041-Reread.`` [common/glbatchMT.cbl:L531-L605].

    * ``return-code = -1`` - exhausted: ``move 10 to fs-Reply WE-Error``, log tag
    ``"EOF"``, cursor deactivated [:L572-L577]. ONE statement writes BOTH fields, so the
    pair is ``(10, 10)`` and ``We-Error`` is not left at zero.

    Args:
        file_access: ``File-Access``.
        dal_common: ``ACAS-DAL-Common-data``.
        batch: ``WS-Batch-Record``; receives the row on the delivering path.
    """
    logging_data = file_access.logging_data
    state = _BRIDGE_WS.dal_data.state_for(TABLE, cursor_state.CursorSlot.PRIMARY)
    logging_data.ws_log_where = _LOGGING_FIELDS["WS-Log-Where"].store("")
    logging_data.ws_no_paragraph = _LOGGING_FIELDS["ws-No-Paragraph"].store(
        WS_NO_PARAGRAPH_BRIDGE["ba041-Reread"]
    )

    # ANOMALY N-countrows-shared - REPRODUCED, NOT FIXED. `if WS-MYSQL-Count-Rows = zero
    # ... set Cursor-Not-Active to true / go to ba999-End`
    # [common/glbatchMT.cbl:L579-L594].
    if state.cursor_active() and _BRIDGE_WS.ws_mysql_count_rows == 0:
        _record_driver_error(None)
        logging_data.sql_state = _LOGGING_FIELDS["SQL-State"].store(
            _BRIDGE_WS.ws_mysql_sqlstate
        )
        # `if WS-MYSQL-Error-Number not = "0 "` [:L583-L591].
        if _errno_is_non_zero():  # pragma: no cover - stale count, never errno
            eof_fs_reply, eof_we_error = end_of_file_status()
            file_access.fs_reply = int(eof_fs_reply)
            file_access.we_error = int(eof_we_error)
            logging_data.sql_err = _LOGGING_FIELDS["SQL-Err"].store(
                _BRIDGE_WS.ws_mysql_error_number
            )
            _store_sql_msg(logging_data, _BRIDGE_WS.ws_mysql_error_message)
            # ANOMALY N-initialize [common/glbatchMT.cbl:L589]: the WITH FILLER variant,
            # where `bb100-UnloadHVs` uses the plain form [:L1106].
            _initialize_ws_batch_record(batch, with_filler=True)
            _store_ws_file_key(logging_data, "EOF2")
        # `set Cursor-Not-Active to true` [:L592] - a bare deactivation, NOT
        # `ba998-Free`, so the stored result stays allocated.
        state.set_cursor_not_active()
        #  SILENT. [common/glbatchMT.cbl:L579-L594] writes no status and displays
        #  nothing: the caller's incoming pair survives per [:L351-L352], and a walk
        #  that a previous WRITE verb quietly ended looks to the caller exactly like
        #  an empty table. That indistinguishability is the anomaly, and reporting it
        #  would be a diagnostic the compiled program cannot produce (rule R-4).
        # `go to ba999-End` [:L593] - Class 3.
        mt_ba999_end(file_access, dal_common, batch)
        return

    cursor = _bridge_cursor()
    try:
        outcome = cursor_state.read_next(
            cursor,
            TABLE,
            slot=cursor_state.CursorSlot.PRIMARY,
            states=_BRIDGE_WS.dal_data,
            file_access=file_access,
        )
    finally:
        cursor.close()
    _BRIDGE_WS.ws_mysql_count_rows = state.count_rows

    if outcome.row is None:
        mt_ba999_end(file_access, dal_common, batch)
        return

    bb100_unload_hvs(outcome.row, batch)
    mt_ba999_end(file_access, dal_common, batch)


def mt_ba050_process_read_indexed(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    batch: GlBatchRecord,
) -> None:
    """``ba050-Process-Read-Indexed.`` [common/glbatchMT.cbl:L607-L712].

    ``WS-Batch-Record (K:L)``, offset 1 length 6 - and it is compared as a DOUBLE-QUOTED
    STRING against a ``mediumint(6) unsigned`` column, letting the database coerce.
    :func:`batch_key_image` produces exactly those six characters and the value is bound
    rather than pasted.

    Args:
        file_access: ``File-Access``.
        dal_common: ``ACAS-DAL-Common-data``.
        batch: ``WS-Batch-Record``; supplies the key and receives the row.
    """
    logging_data = file_access.logging_data
    synchronise_batch_key_views(batch)
    key_value = batch_key_image(batch)
    logging_data.ws_no_paragraph = _LOGGING_FIELDS["ws-No-Paragraph"].store(
        WS_NO_PARAGRAPH_BRIDGE["ba050-Process-Read-Indexed"]
    )
    _build_where("=  ", key_value)
    cursor = _bridge_cursor()
    try:
        outcome = cursor_state.read_indexed(
            cursor,
            TABLE,
            key_value,
            key_number=FILE_KEY_NO_REQUIRED,
            slot=cursor_state.CursorSlot.PRIMARY,
            states=_BRIDGE_WS.dal_data,
            file_access=file_access,
        )
    finally:
        cursor.close()
    logging_data.ws_no_paragraph = _LOGGING_FIELDS["ws-No-Paragraph"].store(
        WS_NO_PARAGRAPH_BRIDGE["ba050-Process-Read-Indexed-fetch"]
    )
    _BRIDGE_WS.ws_mysql_count_rows = 0 if outcome.row is None else 1

    if outcome.row is not None:
        bb100_unload_hvs(outcome.row, batch)
    # `go to ba998-Free.` [:L712] - Class 3.
    mt_ba998_free(file_access, dal_common, batch, only_if_active=False)
    mt_ba999_end(file_access, dal_common, batch)


def mt_ba060_process_start(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    batch: GlBatchRecord,
) -> None:
    """``ba060-Process-Start.`` [common/glbatchMT.cbl:L714-L817].

    So the caller's access type IS the relation, and it is passed through unmodified.

    Args:
        file_access: ``File-Access``; ``access_type`` carries the relation.
        dal_common: ``ACAS-DAL-Common-data``.
        batch: ``WS-Batch-Record``; supplies the key. NOT written - a start fetches
            nothing.
    """
    logging_data = file_access.logging_data
    access_type = int(file_access.access_type)
    # `if access-type < 5 or > 8 move 99 to FS-Reply / move 997 to WE-Error / go to
    # ba999-end` [common/glbatchMT.cbl:L718-L722] - Class 3.
    lower, upper = START_ACCESS_TYPE_RANGE
    if access_type < lower or access_type > upper:
        file_access.fs_reply = int(FsReply.ERROR)
        file_access.we_error = int(WeError.ACCESS_TYPE_WRONG)
        log_handler_failure(
            _LOG,
            program=BRIDGE,
            paragraph="ba060-Process-Start",
            locator="[common/glbatchMT.cbl:L718-L722]",
            fs_reply=int(FsReply.ERROR),
            we_error=int(WeError.ACCESS_TYPE_WRONG),
            detail="Access-Type %d rejected for %s; the guard admits %d..%d "
            "only, which is why the when 9 arm at [:L747] is dead code"
            % (access_type, TABLE, lower, upper),
        )
        mt_ba999_end(file_access, dal_common, batch)
        return

    synchronise_batch_key_views(batch)
    key_value = batch_key_image(batch)
    relation = START_RELATION_BY_ACCESS_TYPE.get(access_type, MOST_RELATION_DEFAULT)
    _build_where(relation, key_value)
    logging_data.ws_no_paragraph = _LOGGING_FIELDS["ws-No-Paragraph"].store(
        WS_NO_PARAGRAPH_BRIDGE["ba060-Process-Start"]
    )
    cursor = _bridge_cursor()
    try:
        #  The return value is deliberately not bound: `cursor_state.start` applies
        #  the status pair to `file_access` itself, which is where the frozen bridge
        #  leaves it, and nothing downstream in this paragraph reads the outcome
        #  object. It was bound only to be interpolated into a per-row trace that no
        #  longer exists.
        cursor_state.start(
            cursor,
            TABLE,
            key_value,
            access_type,
            key_number=FILE_KEY_NO_REQUIRED,
            slot=cursor_state.CursorSlot.PRIMARY,
            states=_BRIDGE_WS.dal_data,
            file_access=file_access,
        )
    finally:
        cursor.close()
    # `WS-MYSQL-Count-Rows` is left exactly as `MYSQL-1220-STORE-RESULT` set it
    # [common/glbatchMT.cbl:L779-L784]; it is the snapshot's row count, owned by
    # `cursor_state` along with the snapshot itself, and no write-side paragraph
    # reads it across a verb boundary. Shadowing it here would give the count two
    # homes and let them disagree.
    #  NO RECORD FOR A SUCCESSFUL POSITIONING. The frozen paragraph displays
    #  nothing on its success path, and a per-row trace of a batch walk is exactly
    #  the kind of invented event rule R-4 excludes - it would also be the highest
    #  volume record in the whole cycle. The status pair is returned to the caller,
    #  which is where the frozen source leaves it.
    # `go to ba999-end` on every path out of this paragraph - Class 3.
    mt_ba999_end(file_access, dal_common, batch)


#: The value ``Ws-Mysql-Count-Rows`` holds after a FAILED statement.
AFFECTED_ROWS_ON_FAILURE: Final[int] = 0xFFFFFFFF


def _mysql_1210_command(
    file_access: FileAccess,
    statement: str,
    parameters: Sequence[object],
    *,
    file_function: int,
) -> BaseException | None:
    """``PERFORM MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT``.

    1. ``Mysql-1100-Db-Error`` writes ``(99, 911)`` for every non-duplicate failure and
    there is NO ``go to`` after it, so control continues.
    :func:`~acas_posting.dal.status.mysql_1100_db_error` owns that, and
    :func:`~acas_posting.dal.status.override_we_error_for_operation` applies the per-
    verb narrowing that ``ba080`` and ``ba090`` write afterwards. 2.

    Args:
        file_access: ``File-Access``; receives the failure status and text fields,
            exactly as ``Mysql-1100-Db-Error`` writes them.
        statement: The statement, identifiers already backtick-quoted.
        parameters: The values to bind, in the statement's order.
        file_function: The verb, for the ``We-Error`` narrowing.

    Returns:
        ``None`` when the statement succeeded, or the driver's exception when it did not
            - which is what the later ``MySQL_errno`` calls read.
    """
    connection = _BRIDGE_WS.connection
    if connection is None:
        raise BridgeNotOpenError(
            f"{BRIDGE} was asked to issue {statement.split(' ', 1)[0]} with "
            f"Ws-Mysql-Cid still null: perform fn-Open (File-Function 1) "
            f"through {HANDLER}.dispatch first"
        )
    logging_data = file_access.logging_data
    try:
        with execute_statement(connection, statement, parameters) as cursor:
            row_count = cursor.rowcount
        _BRIDGE_WS.ws_mysql_count_rows = (
            AFFECTED_ROWS_ON_FAILURE
            if row_count is None or row_count < 0
            else int(row_count)
        )
        _record_driver_error(None)
        return None
    except Exception as error:
        # `if Return-Code not = zero perform Mysql-1100-Db-Error` [:L166-L177].
        _record_driver_error(error)
        status: DbErrorStatus = mysql_1100_db_error(
            errno=_BRIDGE_WS.ws_mysql_error_number.strip(),
            message=_BRIDGE_WS.ws_mysql_error_message,
            sql_state=_BRIDGE_WS.ws_mysql_sqlstate.strip(),
            command=statement,
            we_error=int(file_access.we_error),
        )
        status = override_we_error_for_operation(status, file_function)
        file_access.fs_reply = int(status.fs_reply)
        file_access.we_error = int(status.we_error)
        logging_data.sql_err = _LOGGING_FIELDS["SQL-Err"].store(status.sql_err)
        _store_sql_msg(logging_data, status.sql_msg)
        logging_data.sql_state = _LOGGING_FIELDS["SQL-State"].store(status.sql_state)
        # ANOMALY N-affected-rows-int32 [copybooks/mysql-procedures.cpy:L178]: the
        # affected-row call happens on this path too, and the C shim's `int *` narrowing
        # of -1 leaves 4294967295 here, NOT zero.
        _BRIDGE_WS.ws_mysql_count_rows = AFFECTED_ROWS_ON_FAILURE
        return error


def mt_ba070_process_write(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    batch: GlBatchRecord,
) -> None:
    """``ba070-Process-Write.`` [common/glbatchMT.cbl:L818-L843].

    THIS IS THE ONE WRITE-SIDE PARAGRAPH THAT ESCAPES ANOMALY N-nostatus, and only
    because it zeroes the status pair ITSELF at [:L821] - the clearing
    ``ba010-Initialise`` would have done is commented out [:L351-L352].

    Args:
        file_access: ``File-Access``.
        dal_common: ``ACAS-DAL-Common-data``.
        batch: ``WS-Batch-Record``; supplies every column. Not modified.
    """
    logging_data = file_access.logging_data
    synchronise_batch_key_views(batch)
    bb000_hv_load(batch)
    _store_ws_file_key(logging_data, batch_key_image(batch))
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    logging_data.sql_state = _LOGGING_FIELDS["SQL-State"].store(_SQL_ERR_ZERO)
    _store_sql_msg(logging_data, "")
    logging_data.sql_err = _LOGGING_FIELDS["SQL-Err"].store(_SQL_ERR_ZERO)
    logging_data.ws_no_paragraph = _LOGGING_FIELDS["ws-No-Paragraph"].store(
        WS_NO_PARAGRAPH_BRIDGE["ba070-Process-Write"]
    )
    statement, parameters = mt_bb200_insert()
    logging_data.ws_log_where = _LOGGING_FIELDS["WS-Log-Where"].store(statement)
    _mysql_1210_command(
        file_access, statement, parameters, file_function=FileFunction.WRITE
    )

    if _BRIDGE_WS.ws_mysql_count_rows != 1:
        logging_data.sql_state = _LOGGING_FIELDS["SQL-State"].store(
            _BRIDGE_WS.ws_mysql_sqlstate
        )
        if _errno_is_non_zero():
            logging_data.sql_err = _LOGGING_FIELDS["SQL-Err"].store(
                _BRIDGE_WS.ws_mysql_error_number
            )
            _store_sql_msg(logging_data, _BRIDGE_WS.ws_mysql_error_message)
            if is_duplicate_key_bridge_level(
                str(logging_data.sql_err), str(logging_data.sql_state)
            ):
                file_access.fs_reply = int(FsReply.DUPLICATE_KEY)
            else:
                file_access.fs_reply = int(FsReply.ERROR)
        else:
            # THE DEFECT: no error and no row, so nothing is written and the
            # status pair stays at the `(0, 0)` of [:L821]. A write that
            # inserted nothing reports success. Reproduced, not fixed (R-4).
            #  SILENT: [common/glbatchMT.cbl:L821-L842] displays nothing, so a
            #  write that inserted nothing reports success and says so to nobody.
            #  Reproduced, not reported (rule R-4).
            pass
    # `go to ba999-End.` [:L843] - Class 3.
    mt_ba999_end(file_access, dal_common, batch)


def mt_ba080_process_delete(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    batch: GlBatchRecord,
) -> None:
    """``ba080-Process-Delete.`` [common/glbatchMT.cbl:L845-L898].

    The ``go to ba999-End`` at [:L892] is INSIDE the row-count test and OUTSIDE the
    error-number test, and ``move zero to FS-Reply WE-Error`` at [:L897] is reachable
    ONLY through the ``else``.

    Args:
        file_access: ``File-Access``.
        dal_common: ``ACAS-DAL-Common-data``.
        batch: ``WS-Batch-Record``; supplies the key. Not modified - a delete leaves the
            caller's record alone.
    """
    logging_data = file_access.logging_data
    synchronise_batch_key_views(batch)
    key_value = batch_key_image(batch)
    clause = _build_where("=  ", key_value)
    _store_ws_file_key(logging_data, key_value)
    logging_data.ws_log_where = _LOGGING_FIELDS["WS-Log-Where"].store(clause)
    logging_data.ws_no_paragraph = _LOGGING_FIELDS["ws-No-Paragraph"].store(
        WS_NO_PARAGRAPH_BRIDGE["ba080-Process-Delete"]
    )
    statement = f"DELETE FROM {_QUOTED_TABLE} WHERE {clause}"
    _mysql_1210_command(
        file_access, statement, (key_value,), file_function=FileFunction.DELETE
    )

    if _BRIDGE_WS.ws_mysql_count_rows != 1:
        logging_data.sql_state = _LOGGING_FIELDS["SQL-State"].store(
            _BRIDGE_WS.ws_mysql_sqlstate
        )
        if _errno_is_non_zero():
            file_access.fs_reply = int(FsReply.ERROR)
            file_access.we_error = int(WeError.DELETE_SQLSTATE_NOT_00000)
            logging_data.sql_err = _LOGGING_FIELDS["SQL-Err"].store(
                _BRIDGE_WS.ws_mysql_error_number
            )
            _store_sql_msg(logging_data, _BRIDGE_WS.ws_mysql_error_message)
        else:
            # ANOMALY N-nostatus [common/glbatchMT.cbl:L892]: the jump is here,
            # inside the count test and outside the errno test, so the pair the
            # caller arrived with survives untouched. Do NOT write a status.
            #  SILENT, for the same reason as `fn-write` above: the count test sits
            #  inside the errno test's shadow and [:L892] writes nothing, so the
            #  caller's incoming pair survives untouched and undiagnosed (rule R-4).
            pass
        # `go to ba999-End` [:L892] - Class 3.
        mt_ba999_end(file_access, dal_common, batch)
        return

    _store_sql_msg(logging_data, "")
    logging_data.sql_err = _LOGGING_FIELDS["SQL-Err"].store(_SQL_ERR_ZERO)
    # `move zero to FS-Reply WE-Error.` [:L897] - reachable only through the `else`,
    # which is the whole of anomaly N-nostatus.
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    mt_ba999_end(file_access, dal_common, batch)


def mt_ba085_process_delete_all(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    batch: GlBatchRecord,
) -> None:
    """``ba085-Process-Delete-ALL.`` [common/glbatchMT.cbl:L900-L979].

    The paragraph the maintainer labelled ``*> THIS IS NON STANDARD`` [:L900], and the
    second of the two bridge invocations anomaly N18b produces.

    Args:
        file_access: ``File-Access``.
        dal_common: ``ACAS-DAL-Common-data``.
        batch: ``WS-Batch-Record``; ITS KEY IS OVERWRITTEN with the high key, exactly as
            [:L922] overwrites it.
    """
    logging_data = file_access.logging_data
    # `move 999999 to ws-BATCH-KEY.` [:L922].
    high_key = int(_RECORD_FIELDS[_KEY_DICTIONARY_KEY].store(int(DELETE_ALL_HIGH_KEY)))
    batch.ws_batch_key9.ws_batch_key9 = high_key
    batch.ws_batch_key.ws_ledger = high_key // _LEDGER_DIGIT_SCALE
    batch.ws_batch_key.ws_batch_nos = high_key % _LEDGER_DIGIT_SCALE
    key_value = batch_key_image(batch)
    clause = _build_where("<  ", key_value)
    _store_ws_file_key(logging_data, f"Deleting back from {key_value}")
    logging_data.ws_log_where = _LOGGING_FIELDS["WS-Log-Where"].store(clause)
    logging_data.ws_no_paragraph = _LOGGING_FIELDS["ws-No-Paragraph"].store(
        WS_NO_PARAGRAPH_BRIDGE["ba085-Process-Delete-ALL"]
    )
    statement = f"DELETE FROM {_QUOTED_TABLE} WHERE {clause}"
    _mysql_1210_command(
        file_access, statement, (key_value,), file_function=FileFunction.DELETE_ALL
    )

    if not _BRIDGE_WS.ws_mysql_count_rows > 0:
        logging_data.sql_state = _LOGGING_FIELDS["SQL-State"].store(
            _BRIDGE_WS.ws_mysql_sqlstate
        )
        if _errno_is_non_zero():
            # `move 99 to fs-reply` / `move 995 to WE-Error` [:L970-L971], written
            # inline because verb 6 has no generic override.
            file_access.fs_reply = int(FsReply.ERROR)
            file_access.we_error = int(WeError.DELETE_SQLSTATE_NOT_00000)
            logging_data.sql_err = _LOGGING_FIELDS["SQL-Err"].store(
                _BRIDGE_WS.ws_mysql_error_number
            )
            _store_sql_msg(logging_data, _BRIDGE_WS.ws_mysql_error_message)
        mt_ba999_end(file_access, dal_common, batch)
        return

    # The `else *> of course there could be no data in table` [:L974-L976] - AND, per
    # anomaly N-affected-rows-int32, the path a FAILED delete-all takes.
    if _errno_is_non_zero():
        #  SILENT, AND THAT IS THE WHOLE OF ANOMALY N-affected-rows-int32: a
        #  delete-all that FAILED at the driver reports success, because
        #  `MySQL_affected_rows` narrowed -1 through an int, the `not > zero` guard
        #  at [common/glbatchMT.cbl:L962] is therefore false, and [:L978] zeroes the
        #  status. Nothing is displayed. A record here would tell an operator what
        #  the compiled program refuses to tell them, which is precisely the defect
        #  rule R-4 requires be reproduced rather than repaired.
        pass
    _store_sql_msg(logging_data, "")
    logging_data.sql_err = _LOGGING_FIELDS["SQL-Err"].store(_SQL_ERR_ZERO)
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    mt_ba999_end(file_access, dal_common, batch)


def mt_ba090_process_rewrite(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    batch: GlBatchRecord,
) -> None:
    """``ba090-Process-Rewrite.`` [common/glbatchMT.cbl:L981-L1024].

    ANOMALY N-nostatus, THIRD HALF. Same shape as ``ba080``: the ``go to ba999-End`` at
    [:L1019] is inside the row-count test and outside the error-number test, so A
    REWRITE THAT CHANGED NOTHING RETURNS THE CALLER'S INCOMING STATUS.

    Args:
        file_access: ``File-Access``.
        dal_common: ``ACAS-DAL-Common-data``.
        batch: ``WS-Batch-Record``; supplies every column and the key.
    """
    logging_data = file_access.logging_data
    synchronise_batch_key_views(batch)
    bb000_hv_load(batch)
    key_value = batch_key_image(batch)
    _store_ws_file_key(logging_data, key_value)
    logging_data.ws_no_paragraph = _LOGGING_FIELDS["ws-No-Paragraph"].store(
        WS_NO_PARAGRAPH_BRIDGE["ba090-Process-Rewrite"]
    )
    clause = _build_where("=  ", key_value)
    logging_data.ws_log_where = _LOGGING_FIELDS["WS-Log-Where"].store(clause)
    statement, parameters = mt_bb300_update()
    _mysql_1210_command(
        file_access, statement, parameters, file_function=FileFunction.RE_WRITE
    )

    if _BRIDGE_WS.ws_mysql_count_rows != 1:
        logging_data.sql_state = _LOGGING_FIELDS["SQL-State"].store(
            _BRIDGE_WS.ws_mysql_sqlstate
        )
        if _errno_is_non_zero():
            file_access.fs_reply = int(FsReply.ERROR)
            file_access.we_error = int(WeError.REWRITE_SQLSTATE_NOT_00000)
            logging_data.sql_err = _LOGGING_FIELDS["SQL-Err"].store(
                _BRIDGE_WS.ws_mysql_error_number
            )
            _store_sql_msg(logging_data, _BRIDGE_WS.ws_mysql_error_message)
        else:
            # ANOMALY N-nostatus [common/glbatchMT.cbl:L1019]. Write NO status.
            #  SILENT, per N-nostatus [common/glbatchMT.cbl:L1019]. The zero also
            #  persists in `Ws-Mysql-Count-Rows` and will end the next sequential
            #  walk, which is the second-order effect the walk's own silent exit
            #  above then hides. Both are reproduced and neither is reported (R-4).
            pass
        # `go to ba999-End` [:L1019] - Class 3.
        mt_ba999_end(file_access, dal_common, batch)
        return

    # [:L1021-L1023], outside the `end-if` rather than in an `else`.
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    logging_data.sql_err = _LOGGING_FIELDS["SQL-Err"].store(_SQL_ERR_ZERO)
    _store_sql_msg(logging_data, "")
    mt_ba999_end(file_access, dal_common, batch)


def mt_ba100_bad_function(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    batch: GlBatchRecord,
) -> None:
    """``ba100-Bad-Function.`` [common/glbatchMT.cbl:L1026-L1032].

    ANOMALY N-badfunction-divergence - RECORDED, NOT RECONCILED. The bridge reports
    ``(99, 990)`` here, while the HANDLER's own ``aa100-Bad-Function`` reports ``(99,
    999)`` [common/acas007.cbl:L544-L549].

    Args:
        file_access: ``File-Access``; receives ``(99, 990)``.
        dal_common: ``ACAS-DAL-Common-data``.
        batch: ``WS-Batch-Record``. Untouched.
    """
    file_access.we_error = int(WeError.UNKNOWN_UNEXPECTED)
    file_access.fs_reply = int(FsReply.ERROR)
    log_handler_failure(
        _LOG,
        program=BRIDGE,
        paragraph="ba100-Bad-Function",
        locator="[common/glbatchMT.cbl:L1030-L1031]",
        fs_reply=int(FsReply.ERROR),
        we_error=int(WeError.UNKNOWN_UNEXPECTED),
        detail="File-Function %d matched no arm; note (99, 990) here is NOT the "
        "(99, 999) the handler's own aa100-Bad-Function reports "
        "[common/acas007.cbl:L548-L549]" % int(file_access.file_function),
    )
    mt_ba999_end(file_access, dal_common, batch)


def mt_ba998_free(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    batch: GlBatchRecord,
    *,
    only_if_active: bool,
) -> None:
    """``ba998-Free.`` [common/glbatchMT.cbl:L1038-L1048].

    Releases the stored result and deactivates the cursor.

    Args:
        file_access: ``File-Access``; receives the paragraph number.
        dal_common: ``ACAS-DAL-Common-data``. Unused here; carried so every paragraph
            function has the bridge's own three parameters.
        batch: ``WS-Batch-Record``. Untouched.
        only_if_active: ``True`` for the two ``if Cursor-Active perform`` callers,
            ``False`` for ``ba050``'s unguarded ``go to``.
    """
    del dal_common, batch
    state = _BRIDGE_WS.dal_data.state_for(TABLE, cursor_state.CursorSlot.PRIMARY)
    if only_if_active and state.cursor_not_active():
        # `if Cursor-Active perform ba998-Free.` [:L442-L443], [:L726-L727] - the guard
        # is the CALLER's, so nothing here runs, not even the paragraph number.
        return
    file_access.logging_data.ws_no_paragraph = _LOGGING_FIELDS[
        "ws-No-Paragraph"
    ].store(WS_NO_PARAGRAPH_BRIDGE["ba998-Free"])
    # `CALL "MySQL_free_result"` [:L1046] then `set Cursor-Not-Active to true.`
    # [:L1048].
    state.free()


def mt_ba999_end(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    batch: GlBatchRecord,
) -> None:
    """``ba999-end.`` [common/glbatchMT.cbl:L1050-L1055].

    Args:
        file_access: ``File-Access``.
        dal_common: ``ACAS-DAL-Common-data``.
        batch: ``WS-Batch-Record``.
    """
    mt_ca_process_logs(file_access, dal_common, batch)
    mt_ba999_exit(file_access, dal_common, batch)


def mt_ba999_exit(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    batch: GlBatchRecord,
) -> None:
    """``ba999-exit.`` [common/glbatchMT.cbl:L1057-L1058].

    Args:
        file_access: ``File-Access``. Untouched.
        dal_common: ``ACAS-DAL-Common-data``. Untouched.
        batch: ``WS-Batch-Record``. Untouched.
    """
    del file_access, dal_common, batch


def mt_ca_process_logs(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    batch: GlBatchRecord,
) -> None:
    """``Ca-Process-Logs.`` [common/glbatchMT.cbl:L1705-L1709].

    THE GATE IS ``Testing-1``, not this function. ``if Testing-1 perform Ca-Process-
    Logs`` [:L1053-L1054] reads ``88 Testing-1 value 1`` [copybooks/Test-Data-
    Flags.cob:L11], declared over ``SW-Testing``, which reaches Python as
    :attr:`~acas_posting.records.test_data_flags.AcasDalCommonData.sw_testing`.

    Args:
        file_access: ``File-Access``; every field the log record reports.
        dal_common: ``ACAS-DAL-Common-data``; supplies the ``Testing-1`` gate.
        batch: ``WS-Batch-Record``. Not logged - the COBOL passes only the two blocks
            above - and carried so this function has the bridge's own three parameters.
    """
    del batch
    # `88 Testing-1 value 1` over `SW-Testing` [copybooks/Test-Data-Flags.cob:L10-L11],
    # tested inline for the reason given above. Equality against one, not truthiness.
    if int(dal_common.sw_testing) != 1:
        return
    logging_data = file_access.logging_data
    #  THE ONE ADAPTER, and three fields fewer than this record used to carry.
    #  `WS-File-Key` is the batch key, `WS-Log-Where` is the `WHERE` clause built
    #  around it and `SQL-Msg` is the driver's free text; `redact_for_log` was
    #  applied to the last two and removed nothing, because its rules recognise
    #  connection-message shapes and not a batch number (CWE-532). The adapter also
    #  advances `Log-File-Rec-Written` modulo one million, which this module used
    #  not to do at all.
    log_file_handler_record(
        _LOG,
        program=BRIDGE,
        paragraph="Ca-Process-Logs",
        log_system=logging_data.ws_log_system,
        log_file_no=logging_data.ws_log_file_no,
        no_paragraph=logging_data.ws_no_paragraph,
        file_function=file_access.file_function,
        access_type=file_access.access_type,
        fs_reply=file_access.fs_reply,
        we_error=file_access.we_error,
        sql_err=str(logging_data.sql_err),
        sql_state=str(logging_data.sql_state),
        dal_common=dal_common,
    )


def glbatch_mt(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    batch: GlBatchRecord,
) -> None:
    """``call "glbatchMT" using File-Access ACAS-DAL-Common-data WS-Batch-Record``.

    Published as part of this module's public API under rule R-5, so that a reader
    following the HANDLER-named calling convention finds a function named for the
    handler - :func:`dispatch` - and a reader following the BRIDGE finds one named for
    the bridge, over one implementation.

    Args:
        file_access: ``File-Access`` [copybooks/wsfnctn.cob:L23-L38]. Carries the verb
            in ``file_function``, the START relation in ``access_type``, and receives
            ``fs_reply``, ``we_error`` and every logging field.
        dal_common: ``ACAS-DAL-Common-data``, the ``Testing-1`` logging gate.
        batch: ``WS-Batch-Record`` [copybooks/wsbatch.cob:L13-L54]. Supplies the key
            and, for a write or rewrite, all twenty-one column values; receives a row on
            a successful read.

    Raises:
        BridgeCalledOutsideHandlerError: On ``fn-Open`` with no resident ``System-
            Record``.
        BridgeNotOpenError: On a statement verb with no connection open.

    Examples:
        Read the batch keyed ledger 1, batch 7, then close::

            #  The deployment installed the one policy already; nothing is
            #  declared per table.
            file_access.file_function = int(FileFunction.OPEN)
            file_access.access_type = int(AccessType.I_O)
            dispatch(system, batch, file_access, file_defs, dal_common)

            batch.ws_batch_key.ws_ledger = 1
            batch.ws_batch_key.ws_batch_nos = 7
            file_access.file_function = int(FileFunction.READ_INDEXED)
            file_access.access_type = 0
            dispatch(system, batch, file_access, file_defs, dal_common)

            file_access.file_function = int(FileFunction.CLOSE)
            dispatch(system, batch, file_access, file_defs, dal_common)
    """
    # `move 23 to WS-Log-File-no` was already done by the handler on the RDB path
    # [common/acas007.cbl:L577] - anomaly N-log.
    mt_ba_acas_dal_process(file_access, dal_common, batch)


# THE HANDLER - `acas007` ITSELF. WHY IT IS BELOW THE BRIDGE. The handler CALLS the
# bridge, so the file reads bottom-up.


def _fs_cobol_files_used(system: SystemRecord) -> bool:
    """``FS-Cobol-Files-Used`` - is the indexed-file store the one in use?

    Evaluated inline rather than imported: ``acas_posting.cobol.condition_names`` owns
    the ``88``-level predicates, and Agent Action Plan section 0.4.3's import table
    forbids ``dal`` importing ``cobol``.

    Args:
        system: ``System-Record``, the handler's first parameter.

    Returns:
        ``True`` when ``File-System-Used`` is zero.
    """
    return int(system.system_data_block.rdbms_flat_statuses.file_system_used) == 0


def _indexed_file_verb(
    verb: str, paragraph: str, locator: str, file_defs: FileDefs
) -> NoReturn:
    """Refuse a physical verb against ``Batch-File`` - OMISSION O-1.

    THAT STORE IS NOT IN THE MIGRATION. MySQL is the store the Agent Action Plan
    targets, ``harness/seed.sh`` seeds MySQL and the scenario diffs compare MySQL
    tables, so these verbs have nothing to act on.

    Args:
        verb: The COBOL verb, spelled as the frozen source spells it.
        paragraph: The paragraph it sits in.
        locator: Its ``[common/acas007.cbl:L<n>]`` locator.
        file_defs: ``File-Defs``, consulted only to name the path in the message.

    Raises:
        FlatFileStoreNotMigratedError: Always.
    """
    raise FlatFileStoreNotMigratedError(
        f"{paragraph} reached `{verb} Batch-File` {locator}, which acts on the "
        f"indexed file {file_defs.file_defs_a.file_7.strip()!r} "
        f"[copybooks/selbatch.cob:L2-L6], [copybooks/file07.cob:L1]. That store "
        f"is omission O-1 and is not migrated. Set "
        f"System-Record.system_data_block.rdbms_flat_statuses.file_system_used "
        f"to 1 (`FS-RDBMS-Used` [copybooks/wssystem.cob:L116]) so the request "
        f"routes to {BRIDGE} [common/acas007.cbl:L316-L320]."
    )


def dispatch(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None | object = _TRANSPORT_NOT_SUPPLIED,
) -> None:
    """``call "acas007" using ...`` - THE HANDLER'S FIVE PARAMETERS, IN ORDER.

    Note what the facade does IMMEDIATELY BEFORE the call: ``move 1 to File-Key-No``.

    Args:
        system: ``System-Record`` [copybooks/wssystem.cob]. Supplies the store selector
            ``File-System-Used`` [:L112] and, on the first call of the run, the six
            ``RDB-Data`` credential items [common/acas007.cbl: L614-L619].
        batch: ``WS-Batch-Record`` [copybooks/wsbatch.cob:L13-L54]. Supplies the key,
            and for a write or rewrite all twenty-one column values; receives a row on a
            successful read.
        file_access: ``File-Access`` [copybooks/wsfnctn.cob:L23-L38].
        file_defs: ``File-Defs`` [copybooks/wsnames.cob]. Read only by the indexed
            store's ``assign`` clause, which is omission O-1.
        dal_common: ``ACAS-DAL-Common-data`` [copybooks/Test-Data-Flags.cob]. Its ``SW-
            Testing`` is the ``Testing-1`` logging gate; the copybook default is 1, so
            logging is ON unless a caller clears it.
        transport: The caller's keyword-only transport declaration. Omission
            preserves a process-level declaration made through
            :func:`declare_connection_policy`; an explicit ``None`` clears it.

    Raises:
        FlatFileStoreNotMigratedError: When the request reaches a physical verb
            against ``Batch-File`` - omission O-1.
        BridgeCalledOutsideHandlerError: Not reachable through this function,
            which is precisely what it exists to guarantee.

    Examples:
        Open the table for input, read the batch keyed ledger 1 batch 7, close::

            #  The deployment installed the one policy already; nothing is
            #  declared per table.
            system.system_data_block.rdbms_flat_statuses.file_system_used = 1

            file_access.file_function = int(FileFunction.OPEN)
            file_access.access_type = int(AccessType.INPUT)
            dispatch(system, batch, file_access, file_defs, dal_common)

            batch.ws_batch_key.ws_ledger = 1
            batch.ws_batch_key.ws_batch_nos = 7
            file_access.logging_data.file_key_no = 1
            file_access.file_function = int(FileFunction.READ_INDEXED)
            dispatch(system, batch, file_access, file_defs, dal_common)
    """
    if transport is not _TRANSPORT_NOT_SUPPLIED:
        if transport is not None and not isinstance(transport, TransportSecurity):
            raise TypeError("transport must be TransportSecurity or None")
        _HANDLER.transport = transport

    # LINKAGE residency, not added state.
    previous_system_record = _HANDLER.linkage_system_record
    _HANDLER.linkage_system_record = system
    try:
        aa_process_flat_file(system, batch, file_access, file_defs, dal_common)
    finally:
        _HANDLER.linkage_system_record = previous_system_record


def aa_process_flat_file(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa-Process-Flat-File Section.`` [common/acas007.cbl:L274-L275].

    Args:
        system: ``System-Record``.
        batch: ``WS-Batch-Record``.
        file_access: ``File-Access``.
        file_defs: ``File-Defs``.
        dal_common: ``ACAS-DAL-Common-data``.
    """
    aa010_main(system, batch, file_access, file_defs, dal_common)


def aa010_main(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa010-main.`` [common/acas007.cbl:L276-L360].

    with the source's own comments naming the whole family, ``1 = IRS, 2=GL, 3=SL, 4=PL,
    5=Stock``, and ``Cobol/RDB, File/Table within sub System``. ANOMALY N-log.

    Args:
        system: ``System-Record``.
        batch: ``WS-Batch-Record``.
        file_access: ``File-Access``.
        file_defs: ``File-Defs``.
        dal_common: ``ACAS-DAL-Common-data``.
    """
    logging_data = file_access.logging_data

    logging_data.ws_log_system = _LOGGING_FIELDS["ws-Log-System"].store(
        int(WS_LOG_SYSTEM)
    )
    # `move 13 to WS-Log-File-No.` [:L281] - ANOMALY N-log, stage one of two.
    logging_data.ws_log_file_no = _LOGGING_FIELDS["WS-Log-File-No"].store(
        WS_LOG_FILE_NO_COBOL_PATH
    )

    # `evaluate File-Function / when 4 / when 9 ... when 8 ...`. Held as data in
    # GUARDED_FUNCTIONS so the guarded SET is visible and cannot drift.
    function = int(file_access.file_function)
    guarded_we_error = GUARDED_FUNCTIONS.get(function)
    if guarded_we_error is not None:
        if int(logging_data.file_key_no) != FILE_KEY_NO_REQUIRED:
            file_access.we_error = guarded_we_error
            file_access.fs_reply = int(FsReply.ERROR)
            aa999_main_exit(system, batch, file_access, file_defs, dal_common)
            return

    # Verbatim, including the two commented-out lines that would have coerced the
    # function - their absence is the whole of the anomaly.
    if (
        function == int(FileFunction.OPEN)
        and int(file_access.access_type) == int(AccessType.OUTPUT)
        and not _fs_cobol_files_used(system)
    ):
        # ANOMALY N-fa-statuses-skipped.
        ba_process_rdbms(system, batch, file_access, file_defs, dal_common)
        # `go to AA-Main-Exit` [:L311] - Class 3. NOTE: `aa-main-exit`, NOT `aa999-main-
        # exit`, so THE RELATIONAL PATH DOES NOT LOG HERE.
        aa_main_exit(system, batch, file_access, file_defs, dal_common)
        return

    if not _fs_cobol_files_used(system):
        # `move RDBMS-Flat-Statuses to FA-RDBMS-Flat-Statuses` [:L317] - a GROUP move of
        # two `pic 9` items [copybooks/wssystem.cob:L111-L124] into
        # [copybooks/wsfnctn.cob:L72-L83].
        source_statuses = system.system_data_block.rdbms_flat_statuses
        target_statuses = file_access.fa_rdbms_flat_statuses
        target_statuses.fa_file_system_used = int(source_statuses.file_system_used)
        target_statuses.fa_file_duplicates_in_use = int(
            source_statuses.file_duplicates_in_use
        )
        ba_process_rdbms(system, batch, file_access, file_defs, dal_common)
        aa_main_exit(system, batch, file_access, file_defs, dal_common)
        return

    # `perform ba012-Test-WS-Rec-Size-2.` [:L324] - a PERFORM of ONE PARAGRAPH in
    # another section, so it does NOT fall through into `ba015-Test-Ends` and the bridge
    # is NOT reached from here.
    if ba012_test_ws_rec_size_2(system, batch, file_access, file_defs, dal_common):
        # AMBIGUITY Q-5. The 901 branch's `go to ba-rdbms-exit` [:L607] left the range
        # of this PERFORM and reached `exit section` [:L650].
        return

    # `move spaces to SQL-Err SQL-Msg SQL-State.` [:L336]. The two lines above it are
    # COMMENTED OUT in the frozen source [:L334-L335].
    logging_data.sql_err = _LOGGING_FIELDS["SQL-Err"].store("")
    _store_sql_msg(logging_data, "")
    logging_data.sql_state = _LOGGING_FIELDS["SQL-State"].store("")

    # `evaluate File-Function` [:L338-L357] - eight `when`s in the order 1, 2, 3, 4, 5,
    # 7, 8, 9, so RE-WRITE PRECEDES DELETE, and no `when 6` because the source's own
    # comment says `*> 6 is unused`.
    if function == int(FileFunction.OPEN):
        aa020_process_open(system, batch, file_access, file_defs, dal_common)
        return
    if function == int(FileFunction.CLOSE):
        aa030_process_close(system, batch, file_access, file_defs, dal_common)
        return
    if function == int(FileFunction.READ_NEXT):
        aa040_process_read_next(system, batch, file_access, file_defs, dal_common)
        return
    if function == int(FileFunction.READ_INDEXED):
        aa050_process_read_indexed(system, batch, file_access, file_defs, dal_common)
        return
    if function == int(FileFunction.WRITE):
        aa070_process_write(system, batch, file_access, file_defs, dal_common)
        return
    if function == int(FileFunction.RE_WRITE):
        aa090_process_rewrite(system, batch, file_access, file_defs, dal_common)
        return
    if function == int(FileFunction.DELETE):
        aa080_process_delete(system, batch, file_access, file_defs, dal_common)
        return
    if function == int(FileFunction.START):
        aa060_process_start(system, batch, file_access, file_defs, dal_common)
        return
    # `when other *> 6 is unused / go to aa100-Bad-Function` [:L355-L356] - Class 4.
    aa100_bad_function(system, batch, file_access, file_defs, dal_common)
    # `go to aa100-Bad-Function.` [:L360], unconditional, under the comment "Should
    # never get here but in case :(".
    return


def aa020_process_open(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa020-Process-Open.`` [common/acas007.cbl:L362-L398].

    move spaces to WS-File-Key. *> for logging move 201 to WS-No-Paragraph.

    Args:
        system: ``System-Record``.
        batch: ``WS-Batch-Record``. Untouched by this paragraph.
        file_access: ``File-Access``. Receives ``ws_no_paragraph``, ``ws_file_key`` and,
            on the ``fn-extend`` arm, the status pair.
        file_defs: ``File-Defs``. Names the indexed path in the O-1 refusal.
        dal_common: ``ACAS-DAL-Common-data``.

    Raises:
        FlatFileStoreNotMigratedError: On ``fn-input``, ``fn-i-o`` or ``fn-output``,
            each of which reaches a real ``open`` - omission O-1.
    """
    logging_data = file_access.logging_data
    _store_ws_file_key(logging_data, "")
    logging_data.ws_no_paragraph = _LOGGING_FIELDS["ws-No-Paragraph"].store(
        WS_NO_PARAGRAPH_COBOL["aa020-Process-Open"]
    )

    access_type = int(file_access.access_type)
    if access_type == int(AccessType.INPUT):
        _indexed_file_verb(
            "open input", "aa020-Process-Open", "[common/acas007.cbl:L366]", file_defs
        )
    elif access_type == int(AccessType.I_O):
        _indexed_file_verb(
            "open i-o", "aa020-Process-Open", "[common/acas007.cbl:L374]", file_defs
        )
    elif access_type == int(AccessType.OUTPUT):
        # `open output Batch-File` [:L383] - omission O-1. Note the source's comment
        # "caller should check fs-reply": no status test follows.
        _indexed_file_verb(
            "open output", "aa020-Process-Open", "[common/acas007.cbl:L383]", file_defs
        )
    elif access_type == int(AccessType.EXTEND):
        # `if fn-extend` [:L385]. The `open extend Batch-File` is COMMENTED OUT [:L386],
        # so this arm touches no file and is reproduced in full.
        file_access.we_error = int(WeError.ACCESS_TYPE_WRONG)
        file_access.fs_reply = int(FsReply.ERROR)
        aa999_main_exit(system, batch, file_access, file_defs, dal_common)
        return
    # `end-if.` x4 [:L390-L393]. ANOMALY N-open-nomode: an Access-Type outside 1..4
    # reaches here having touched nothing, and the tail below still runs.

    _HANDLER.cobol_file_status = 0
    # `move "OPEN GL BATCH file" to WS-File-Key.` [:L395]. Note the spacing: "GL BATCH",
    # two words, where the bridge writes "OPEN GLBATCH" as one
    # [common/glbatchMT.cbl:L437].
    _store_ws_file_key(logging_data, "OPEN GL BATCH file")
    if int(file_access.fs_reply) != int(FsReply.SUCCESS):
        file_access.we_error = int(WeError.NOT_USED)
    aa999_main_exit(system, batch, file_access, file_defs, dal_common)


def aa030_process_close(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa030-Process-Close.`` [common/acas007.cbl:L400-L411].

    ANOMALY N-close-double-log, and it is the only paragraph in either program that logs
    twice. ``perform aa999-main-exit`` [:L407] is a PERFORM, so it runs that paragraph's
    ``if Testing-1 perform Ca-Process-Logs`` and RETURNS here rather than falling
    through to ``aa-main-exit``.

    Args:
        system: ``System-Record``.
        batch: ``WS-Batch-Record``. Untouched.
        file_access: ``File-Access``. Receives ``ws_no_paragraph`` and ``ws_file_key``,
            and has ``file_function`` and ``access_type`` ZEROED between the two log
            records.
        file_defs: ``File-Defs``.
        dal_common: ``ACAS-DAL-Common-data``.

    Raises:
        FlatFileStoreNotMigratedError: Always - ``close Batch-File`` [:L403] is the
            third statement, and everything quoted after it is unreachable for exactly
            that reason. Omission O-1.
    """
    logging_data = file_access.logging_data
    logging_data.ws_no_paragraph = _LOGGING_FIELDS["ws-No-Paragraph"].store(
        WS_NO_PARAGRAPH_COBOL["aa030-Process-Close"]
    )
    _store_ws_file_key(logging_data, "")
    # `close Batch-File.` [:L403] - omission O-1.
    _indexed_file_verb(
        "close", "aa030-Process-Close", "[common/acas007.cbl:L403]", file_defs
    )


def aa040_process_read_next(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa040-Process-Read-Next.`` [common/acas007.cbl:L413-L428].

    THE WHOLE BLOCK IS REPRODUCED, because it touches no file. Three observable effects,
    in this order: the status pair becomes ``(10, 10)``.

    Args:
        system: ``System-Record``.
        batch: ``WS-Batch-Record``. Its key is ZEROED on the EOF branch.
        file_access: ``File-Access``.
        file_defs: ``File-Defs``.
        dal_common: ``ACAS-DAL-Common-data``.

    Raises:
        FlatFileStoreNotMigratedError: On the non-EOF path, raised from
            :func:`aa041_reread` - omission O-1.
    """
    logging_data = file_access.logging_data
    logging_data.ws_no_paragraph = _LOGGING_FIELDS["ws-No-Paragraph"].store(
        WS_NO_PARAGRAPH_COBOL["aa040-Process-Read-Next"]
    )
    if _HANDLER.cobol_file_status == 1:
        eof_fs_reply, eof_we_error = end_of_file_status()
        file_access.fs_reply = int(eof_fs_reply)
        file_access.we_error = int(eof_we_error)
        # `move zeros to WS-Batch-Key9` [:L422]. The REDEFINES makes this one storage,
        # so every reading of the six bytes goes to zero together
        # [copybooks/wsbatch.cob:L14-L21].
        batch.ws_batch_key9.ws_batch_key9 = 0
        batch.ws_batch_key.ws_ledger = 0
        batch.ws_batch_key.ws_batch_nos = 0
        # `move spaces to SQL-Err SQL-Msg` [:L423-L425]. SQL-State is NOT in this list
        # and is deliberately left as the caller had it.
        logging_data.sql_err = _LOGGING_FIELDS["SQL-Err"].store("")
        _store_sql_msg(logging_data, "")
        # `stop "Cobol File EOF"` [:L426] - OMISSION O-3, the pause dropped and
        # the diagnostic kept, per Agent Action Plan section 0.3.4.
        #  ONE ERROR, THROUGH THE ONE REPORTER, at the same level in every handler
        #  that carries this stop. The pause is omission O-3; the transfer to
        #  `aa999-main-exit` below is kept.
        log_cobol_stop(
            _LOG,
            program=HANDLER,
            paragraph="aa040-Process-Read-Next",
            literal="Cobol File EOF",
            locator="[common/acas007.cbl:L426]",
        )
        aa999_main_exit(system, batch, file_access, file_defs, dal_common)
        return
    # `end-if.` [:L428], then FALL-THROUGH into `aa041-Reread` [:L430] - modelled as an
    # explicit call because the frozen source relies on source order here.
    aa041_reread(system, batch, file_access, file_defs, dal_common)


def aa041_reread(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa041-Reread.`` [common/acas007.cbl:L430-L444].

    THE FIRST STATEMENT IS THE READ, so the whole paragraph sits inside omission O-1.
    Four details are recorded here because a reader comparing this module with the
    bridge will look for them.

    Args:
        system: ``System-Record``.
        batch: ``WS-Batch-Record``.
        file_access: ``File-Access``.
        file_defs: ``File-Defs``.
        dal_common: ``ACAS-DAL-Common-data``.

    Raises:
        FlatFileStoreNotMigratedError: Always - omission O-1.
    """
    # `read Batch-File next record at end ... end-read.` [common/acas007.cbl: L431-L438]
    # - omission O-1, and the first statement of the paragraph, so nothing precedes it
    # to reproduce.
    _indexed_file_verb(
        "read next record",
        "aa041-Reread",
        "[common/acas007.cbl:L431]",
        file_defs,
    )


def aa050_process_read_indexed(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa050-Process-Read-Indexed.`` [common/acas007.cbl:L446-L449].

    Both touch no file, so both are reproduced. Control then FALLS THROUGH into
    ``aa051-Reread`` [:L451], which is where the keyed read happens.

    Args:
        system: ``System-Record``.
        batch: ``WS-Batch-Record``.
        file_access: ``File-Access``. Receives ``ws_no_paragraph``.
        file_defs: ``File-Defs``.
        dal_common: ``ACAS-DAL-Common-data``.

    Raises:
        FlatFileStoreNotMigratedError: Raised from :func:`aa051_reread` - omission O-1.
    """
    logging_data = file_access.logging_data
    logging_data.ws_no_paragraph = _LOGGING_FIELDS["ws-No-Paragraph"].store(
        WS_NO_PARAGRAPH_COBOL["aa050-Process-Read-Indexed"]
    )
    _HANDLER.cobol_file_status = 0
    aa051_reread(system, batch, file_access, file_defs, dal_common)


def aa051_reread(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa051-Reread.`` [common/acas007.cbl:L451-L459].

    ``move 21 to we-error fs-reply`` [:L454] writes 21 to BOTH fields. 21 is ``FS-
    Reply``'s "invalid key on START" value and has no entry in the authoritative ``We-
    Error`` table [common/glpostingMT.cbl:L132-L153].

    Args:
        system: ``System-Record``.
        batch: ``WS-Batch-Record``. Supplies the key; would receive the row.
        file_access: ``File-Access``. Receives ``ws_file_key`` BEFORE the read.
        file_defs: ``File-Defs``.
        dal_common: ``ACAS-DAL-Common-data``.

    Raises:
        FlatFileStoreNotMigratedError: Always, at the ``read`` - omission O-1.
    """
    logging_data = file_access.logging_data
    _store_ws_file_key(logging_data, batch_key_image(batch))
    _indexed_file_verb(
        "read", "aa051-Reread", "[common/acas007.cbl:L453]", file_defs
    )


def aa060_process_start(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa060-Process-Start.`` [common/acas007.cbl:L461-L509].

    ANOMALY N-start-code-divergence, and it is the sharpest divergence in this module.

    Args:
        system: ``System-Record``.
        batch: ``WS-Batch-Record``. Supplies the key.
        file_access: ``File-Access``. Receives ``ws_no_paragraph``, ``ws_file_key`` and
            the status pair.
        file_defs: ``File-Defs``.
        dal_common: ``ACAS-DAL-Common-data``.

    Raises:
        FlatFileStoreNotMigratedError: When the access type is in 5..8, each of which
            reaches a real ``start`` - omission O-1.
    """
    logging_data = file_access.logging_data
    logging_data.ws_no_paragraph = _LOGGING_FIELDS["ws-No-Paragraph"].store(
        WS_NO_PARAGRAPH_COBOL["aa060-Process-Start"]
    )
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    _HANDLER.cobol_file_status = 0
    _store_ws_file_key(logging_data, batch_key_image(batch))

    # `if access-type < 5 or > 8` [:L472] - INCLUSIVE bounds, held in
    # START_ACCESS_TYPE_RANGE so this module and the bridge cannot drift.
    access_type = int(file_access.access_type)
    lowest, highest = START_ACCESS_TYPE_RANGE
    if access_type < lowest or access_type > highest:
        # `move 998 to WE-Error` [:L473] - AND NOTHING ELSE. ANOMALY N-start-code-
        # divergence.
        file_access.we_error = int(WeError.FILE_KEY_NO_OUT_OF_RANGE)
        aa999_main_exit(system, batch, file_access, file_defs, dal_common)
        return

    # The four `start` blocks [:L479-L503], in the frozen source's own order: equal-to,
    # not-less-than, greater-than, less-than.
    relation = START_RELATION_BY_ACCESS_TYPE.get(access_type, MOST_RELATION_DEFAULT)
    _indexed_file_verb(
        f"start key {relation.strip()}",
        "aa060-Process-Start",
        _START_VERB_LOCATORS[access_type],
        file_defs,
    )


def aa070_process_write(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa070-Process-Write.`` [common/acas007.cbl:L511-L520].

    ⭐ THE ``invalid key`` PHRASE CONTAINS NOTHING BUT A TRANSFER [:L517-L518].

    Args:
        system: ``System-Record``.
        batch: ``WS-Batch-Record``. Supplies all twenty-one column values.
        file_access: ``File-Access``. Receives ``ws_no_paragraph``, ``ws_file_key`` and
            the cleared status pair.
        file_defs: ``File-Defs``.
        dal_common: ``ACAS-DAL-Common-data``.

    Raises:
        FlatFileStoreNotMigratedError: Always, at the ``write`` - omission O-1.
    """
    logging_data = file_access.logging_data
    logging_data.ws_no_paragraph = _LOGGING_FIELDS["ws-No-Paragraph"].store(
        WS_NO_PARAGRAPH_COBOL["aa070-Process-Write"]
    )
    # `move WS-Batch-Record to Batch-Record.` [:L513] - a group move into the FD record,
    # which is not observable through any parameter.
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    _HANDLER.cobol_file_status = 0
    _store_ws_file_key(logging_data, batch_key_image(batch))
    _indexed_file_verb(
        "write", "aa070-Process-Write", "[common/acas007.cbl:L517]", file_defs
    )


def aa080_process_delete(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa080-Process-Delete.`` [common/acas007.cbl:L522-L532].

    ⭐ THERE IS NO ``invalid key`` PHRASE AT ALL.

    Args:
        system: ``System-Record``.
        batch: ``WS-Batch-Record``. Supplies the key.
        file_access: ``File-Access``. Receives ``ws_no_paragraph``, ``ws_file_key`` and
            the cleared status pair.
        file_defs: ``File-Defs``.
        dal_common: ``ACAS-DAL-Common-data``.

    Raises:
        FlatFileStoreNotMigratedError: Always, at the ``delete`` - omission O-1.
    """
    logging_data = file_access.logging_data
    logging_data.ws_no_paragraph = _LOGGING_FIELDS["ws-No-Paragraph"].store(
        WS_NO_PARAGRAPH_COBOL["aa080-Process-Delete"]
    )
    _store_ws_file_key(logging_data, batch_key_image(batch))
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    _HANDLER.cobol_file_status = 0
    # `delete Batch-File record.` [:L531] - omission O-1, and with NO `invalid key`
    # phrase, so nothing here would have tested its outcome.
    _indexed_file_verb(
        "delete record", "aa080-Process-Delete", "[common/acas007.cbl:L531]", file_defs
    )


def aa090_process_rewrite(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa090-Process-Rewrite.`` [common/acas007.cbl:L534-L542].

    ⭐ NO ``invalid key`` PHRASE, exactly as in ``aa080-Process-Delete``, so a rewrite of
    a record that is not there is answered by the file status alone. The bridge answers
    that condition ``(99, 994)`` [common/glbatchMT.cbl:L1016-L1017].

    Args:
        system: ``System-Record``.
        batch: ``WS-Batch-Record``. Supplies all twenty-one column values.
        file_access: ``File-Access``. Receives ``ws_no_paragraph``, ``ws_file_key`` and
            the cleared status pair.
        file_defs: ``File-Defs``.
        dal_common: ``ACAS-DAL-Common-data``.

    Raises:
        FlatFileStoreNotMigratedError: Always, at the ``rewrite`` - omission O-1.
    """
    logging_data = file_access.logging_data
    logging_data.ws_no_paragraph = _LOGGING_FIELDS["ws-No-Paragraph"].store(
        WS_NO_PARAGRAPH_COBOL["aa090-Process-Rewrite"]
    )
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    _HANDLER.cobol_file_status = 0
    _store_ws_file_key(logging_data, batch_key_image(batch))
    _indexed_file_verb(
        "rewrite", "aa090-Process-Rewrite", "[common/acas007.cbl:L541]", file_defs
    )


def aa100_bad_function(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa100-Bad-Function.`` [common/acas007.cbl:L544-L549].

    ANOMALY N-badfunction-divergence, THREE WAYS. This paragraph answers ``(FS-Reply 99,
    We-Error 999)``. The bridge's equivalent answers ``(99, 990)``
    [common/glbatchMT.cbl:L1030-L1031], writing the two fields in the same order but
    with a different code.

    Args:
        system: ``System-Record``.
        batch: ``WS-Batch-Record``. Untouched.
        file_access: ``File-Access``. Receives the status pair.
        file_defs: ``File-Defs``.
        dal_common: ``ACAS-DAL-Common-data``.
    """
    file_access.we_error = int(WeError.NOT_USED)
    file_access.fs_reply = int(FsReply.ERROR)
    # FALL-THROUGH into `aa999-main-exit` [:L551] - no `go to` here, so the transfer is
    # by source order and is modelled as an explicit call.
    aa999_main_exit(system, batch, file_access, file_defs, dal_common)


def aa999_main_exit(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    *,
    fall_through: bool = True,
) -> None:
    """``aa999-main-exit.`` [common/acas007.cbl:L551-L554].

    WHY ``fall_through`` EXISTS, AND WHY IT IS NOT AN INVENTION. This label is reached
    two different ways in the frozen source, and COBOL treats them differently.

    Args:
        system: ``System-Record``.
        batch: ``WS-Batch-Record``. Untouched.
        file_access: ``File-Access``. Passed to the logger.
        file_defs: ``File-Defs``.
        dal_common: ``ACAS-DAL-Common-data``. Its ``SW-Testing`` is the gate.
        fall_through: ``True`` for the ``go to`` sites, ``False`` for ``aa030-Process-
            Close``'s ``perform`` [:L407].
    """
    if int(dal_common.sw_testing) == 1:
        ca_process_logs(system, batch, file_access, file_defs, dal_common)
    if fall_through:
        aa_main_exit(system, batch, file_access, file_defs, dal_common)


def aa_main_exit(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa-main-exit.`` [common/acas007.cbl:L556-L558].

    It has no statements at all, so its only behaviour is to be a transfer target and
    then fall through into ``aa-Exit`` [:L560].

    Args:
        system: ``System-Record``.
        batch: ``WS-Batch-Record``. Untouched.
        file_access: ``File-Access``. Untouched.
        file_defs: ``File-Defs``. Untouched.
        dal_common: ``ACAS-DAL-Common-data``. Untouched.
    """
    aa_exit(system, batch, file_access, file_defs, dal_common)


def aa_exit(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa-Exit.`` [common/acas007.cbl:L560-L561].

    ``exit program`` returns to the caller of ``acas007``, which in Python is
    :func:`dispatch` returning.

    Args:
        system: ``System-Record``.
        batch: ``WS-Batch-Record``. Untouched.
        file_access: ``File-Access``. Untouched.
        file_defs: ``File-Defs``. Untouched.
        dal_common: ``ACAS-DAL-Common-data``. Untouched.
    """
    # `exit program.` [common/acas007.cbl:L561] - a return to the caller.
    #  NO RECORD. `exit program` [common/acas007.cbl:L561] displays nothing; a
    #  trace of reaching it is an invented event (rule R-4), and the status pair it
    #  reported is already in the caller's own `File-Access` block, which is where
    #  the frozen source leaves it.


def ba_process_rdbms(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``ba-Process-RDBMS section.`` [common/acas007.cbl:L563-L569].

    A SECTION ``PERFORM`` runs from the section's first paragraph to the end of the
    section, so ``perform ba-Process-RDBMS`` [:L310, :L318] executes the whole chain
    ``ba010-Test-WS-Rec-Size`` -> ``ba012-Test-WS-Rec-Size-2`` -> ``ba015-Test-Ends`` ->
    ``ba020-Process-DAL`` -> ``ba-rdbms-exit``, every link of it by FALL-THROUGH.

    Args:
        system: ``System-Record``. Supplies the credentials on the first call.
        batch: ``WS-Batch-Record``.
        file_access: ``File-Access``.
        file_defs: ``File-Defs``. Not read on this path - the relational store has no
            ``assign`` clause.
        dal_common: ``ACAS-DAL-Common-data``.
    """
    ba010_test_ws_rec_size(system, batch, file_access, file_defs, dal_common)


def ba010_test_ws_rec_size(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``ba010-Test-WS-Rec-Size.`` [common/acas007.cbl:L571-L577].

    ANOMALY N-log, STAGE TWO. ``aa010-main`` set ``WS-Log-File-No`` to 13 [:L281]; this
    overwrites it with 23, so EVERY LOG RECORD FROM THE RELATIONAL one handler serving
    one table.

    Args:
        system: ``System-Record``.
        batch: ``WS-Batch-Record``.
        file_access: ``File-Access``. Receives ``ws_log_file_no``.
        file_defs: ``File-Defs``.
        dal_common: ``ACAS-DAL-Common-data``.
    """
    logging_data = file_access.logging_data
    # `move 23 to WS-Log-File-no.` [common/acas007.cbl:L577] - ANOMALY N-log.
    logging_data.ws_log_file_no = _LOGGING_FIELDS["WS-Log-File-No"].store(
        WS_LOG_FILE_NO_RDB_PATH
    )
    if ba012_test_ws_rec_size_2(system, batch, file_access, file_defs, dal_common):
        # `ba012` took its `go to ba-rdbms-exit` [:L607], whose `exit section` [:L650]
        # ends this section, so `ba015-Test-Ends` and therefore the bridge are NOT
        # reached.
        return
    ba015_test_ends(system, batch, file_access, file_defs, dal_common)


def ba012_test_ws_rec_size_2(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> bool:
    """``ba012-Test-WS-Rec-Size-2.`` [common/acas007.cbl:L579-L620].

    FOUR THINGS, and three of them are anomalies.

    Returns:
        ``True`` when the 901 branch took its ``go to ba-rdbms-exit`` [:L607], which
            ends ``ba-Process-RDBMS section`` and so prevents ``ba015-Test-Ends`` and
            the bridge from being reached at all.

    Args:
        system: ``System-Record``. Its six ``RDBMS-`` items are the credentials.
        batch: ``WS-Batch-Record``. Untouched.
        file_access: ``File-Access``. May receive ``sql_msg`` on the 901 branch.
        file_defs: ``File-Defs``. Untouched.
        dal_common: ``ACAS-DAL-Common-data``. Its ``SW-Testing`` gates the log.
    """
    logging_data = file_access.logging_data
    if _HANDLER.a != 0:
        return False

    # `move function Length (WS-Batch-Record) to A` [:L582-L584] and `move function
    # length (Batch-Record) to B` [:L585-L587].
    _HANDLER.a = WS_BATCH_RECORD_LENGTH
    _HANDLER.b = WS_BATCH_RECORD_LENGTH

    # `if A < B` [:L588] - ANOMALY N-901-unreachable, false by construction.
    if _HANDLER.a < _HANDLER.b:  # pragma: no cover - see N-901-unreachable
        file_access.we_error = RECORD_SIZE_WE_ERROR
        file_access.fs_reply = int(FsReply.ERROR)

    # `if WE-Error = 901` [:L592] - ⭐ ANOMALY N-901-STICKY.
    if int(file_access.we_error) == RECORD_SIZE_WE_ERROR:
        # `move spaces to Display-Blk` [:L593], then the STRING [:L594-L599]. Five
        # sending items, all `delimited by size`, so each contributes its FULL declared
        # width.
        assembled = (
            f"{ERROR_MESSAGE_GL904}"
            f"{_HANDLER.a:0{_RECORD_LENGTH_PICTURE_DIGITS}d}"
            f" < "
            f"Batch-Rec = "
            f"{_HANDLER.b:0{_RECORD_LENGTH_PICTURE_DIGITS}d}"
        )
        _HANDLER.display_blk = assembled[:_DISPLAY_BLK_WIDTH].ljust(
            _DISPLAY_BLK_WIDTH
        )
        _LOG.error(
            "%s [common/acas007.cbl:L600] - the caller must stop",
            _HANDLER.display_blk.rstrip(),
        )
        # `move Display-Blk to SQL-Msg` [:L602] - NOT presentation.
        _store_sql_msg(logging_data, _HANDLER.display_blk)
        if int(dal_common.sw_testing) == 1:
            ca_process_logs(system, batch, file_access, file_defs, dal_common)
        # `accept Accept-Reply at 2433` [:L606] - OMISSION O-3.
        ba_rdbms_exit(system, batch, file_access, file_defs, dal_common)
        return True

    # The six credential moves [:L614-L619], under the maintainer's own comments "Not a
    # error comparing the length of records so - -" and "Load up the DB settings from
    # the system record as its not passed on / hopefully once is enough :)".
    load_rdb_data_once(system)
    return False


def ba015_test_ends(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``ba015-Test-Ends.`` [common/acas007.cbl:L622-L631].

    1. ``aa010-main`` sees ``fn-Open and fn-output and not FS-Cobol-Files-Used`` and
    performs this section [:L305-L312] WITHOUT coercing the function - the two lines
    that would have done so are commented out. 2.

    Args:
        system: ``System-Record``.
        batch: ``WS-Batch-Record``.
        file_access: ``File-Access``. Its ``file_function`` IS OVERWRITTEN with ``fn-
            Delete-All`` between the two calls.
        file_defs: ``File-Defs``.
        dal_common: ``ACAS-DAL-Common-data``.
    """
    if int(file_access.file_function) == int(FileFunction.OPEN) and int(
        file_access.access_type
    ) == int(AccessType.OUTPUT):
        # `perform ba020-Process-Dal` [:L629] - BRIDGE CALL ONE, still carrying
        # fn-Open and fn-Output, so the bridge opens the connection.
        #  NO RECORD. The double call of anomaly N18b is reproduced by making the
        #  call twice, which is the behaviour; announcing it is a diagnostic the
        #  frozen source does not have (rule R-4). N18b is documented in
        #  `docs/migration/anomaly-log.md`.
        ba020_process_dal(system, batch, file_access, file_defs, dal_common)
        # `set fn-Delete-All to true` [:L630] - writes 6 into the CALLER's `File-
        # Function` AFTER the open has already happened.
        file_access.file_function = int(FileFunction.DELETE_ALL)
    # `end-if.` [:L631] FALL-THROUGH into `ba020-Process-DAL` [:L640] - the SECOND
    # bridge call on the Open-plus-Output path, and the only call on every other path.
    ba020_process_dal(system, batch, file_access, file_defs, dal_common)


def ba020_process_dal(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``ba020-Process-DAL.`` [common/acas007.cbl:L640-L645].

    ``System-Record`` and ``File-Defs`` are NOT passed. The bridge needs neither: the
    credentials reached it through ``RDB-Data``, which ``ba012-Test-WS-Rec-Size-2``
    loaded on the first call of the run [:L614-L619], and the relational store has no
    ``assign`` clause.

    Args:
        system: ``System-Record``. Not passed to the bridge; carried because every
            paragraph in this module has the handler's five parameters.
        batch: ``WS-Batch-Record``. The bridge's third parameter.
        file_access: ``File-Access``. The bridge's FIRST parameter.
        file_defs: ``File-Defs``. Not passed to the bridge.
        dal_common: ``ACAS-DAL-Common-data``. The bridge's second parameter.
    """
    # `call "glbatchMT" using File-Access ACAS-DAL-Common-data WS-Batch-Record`
    # [common/acas007.cbl:L641-L645] - THE BRIDGE'S OWN ORDER, File-Access first, and
    # `System-Record` and `File-Defs` deliberately NOT among the three.
    glbatch_mt(file_access, dal_common, batch)
    ba_rdbms_exit(system, batch, file_access, file_defs, dal_common)


def ba_rdbms_exit(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``ba-rdbms-exit.`` [common/acas007.cbl:L649-L650].

    IT IS ALSO THE TARGET OF THE 901 BRANCH'S ``go to`` [:L607], and that is AMBIGUITY
    Q-5.

    Args:
        system: ``System-Record``. Untouched.
        batch: ``WS-Batch-Record``. Untouched.
        file_access: ``File-Access``. Untouched.
        file_defs: ``File-Defs``. Untouched.
        dal_common: ``ACAS-DAL-Common-data``. Untouched.
    """
    del system, batch, file_defs, dal_common
    # `exit section.` [common/acas007.cbl:L650] - a return, nothing more.
    #  NO RECORD, for the same reason as `aa999-main-exit`: an exit paragraph that
    #  displays nothing has no diagnostic to reproduce (rule R-4).


def ca_process_logs(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``Ca-Process-Logs.`` [common/acas007.cbl:L653-L657].

    Note also that ``File-Defs``, ``System-Record`` and ``WS-Batch-Record`` are NOT
    passed to ``fhlogger`` - only the two blocks the ``using`` list names - which is why
    nothing about the record or the credentials can reach a log record from here.

    Args:
        system: ``System-Record``. Not logged; not in the ``using`` list.
        batch: ``WS-Batch-Record``. Not logged; not in the ``using`` list.
        file_access: ``File-Access``. Every field the log record reports.
        file_defs: ``File-Defs``. Not logged; not in the ``using`` list.
        dal_common: ``ACAS-DAL-Common-data``. The second ``using`` item.
    """
    # `call "fhlogger" using File-Access ACAS-DAL-Common-data.`
    # [common/acas007.cbl:L656-L657] - OMISSION O-2 under rule R-1. Only the two blocks
    # the `using` list names reach the record.
    logging_data = file_access.logging_data
    # The driver's own text is redacted before it reaches the record: a server
    # message can carry the connection's account, host, key values and a line
    # feed (CWE-117, CWE-532). The ACAS status values are integers from this
    # module's own enumerations and are interpolated as themselves.
    #  THE ONE ADAPTER - see the note on the bridge's own logging paragraph above
    #  for which fields are withheld and why.
    log_file_handler_record(
        _LOG,
        program=HANDLER,
        paragraph="Ca-Process-Logs",
        log_system=logging_data.ws_log_system,
        log_file_no=logging_data.ws_log_file_no,
        no_paragraph=logging_data.ws_no_paragraph,
        file_function=file_access.file_function,
        access_type=file_access.access_type,
        fs_reply=file_access.fs_reply,
        we_error=file_access.we_error,
        sql_err=str(logging_data.sql_err),
        sql_state=str(logging_data.sql_state),
        dal_common=dal_common,
    )
    ca_exit(system, batch, file_access, file_defs, dal_common)


def ca_exit(
    system: SystemRecord,
    batch: GlBatchRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``ca-Exit. exit.`` [common/acas007.cbl:L659].

    The last paragraph of the program, and the last statement before ``end program
    acas007.`` [:L662].

    Args:
        system: ``System-Record``. Untouched.
        batch: ``WS-Batch-Record``. Untouched.
        file_access: ``File-Access``. Untouched.
        file_defs: ``File-Defs``. Untouched.
        dal_common: ``ACAS-DAL-Common-data``. Untouched.
    """
    del system, batch, file_access, file_defs, dal_common
