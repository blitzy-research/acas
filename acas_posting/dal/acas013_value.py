"""`acas013` and its bridge `valueMT` - the `VALUEANAL-REC` value-analysis table.

The data-access module for the Value entity, ten columns, primary key `VA-CODE`.

Three money fields are signed in the copybook and unsigned at both the bridge
host variable and the column, so a negative value loses its sign at the bridge,
before any SQL executes; the conversion is performed here rather than left to the
database.

The table's layout is near-identical to the Analysis table's, which is why the two
are kept strictly apart: a lookup that reached the wrong copybook would produce a
record that still looked right.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import ROUND_DOWN, Decimal
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from acas_posting.dal.connection import (
    OpenOutcome,
    TransportSecurity,
    cobol_string_delimited_by_space,
    execute_statement,
    load_rdb_data_once,
    mysql_1000_open,
    mysql_1090_exit,
    mysql_1980_close,
    mysql_1999_exit,
    quote_identifier,
    transport_category,
)
from acas_posting.dal.cursor_state import (
    ACCESS_TYPE_TO_RELATION,
    SEQUENTIAL_READ_START,
    TABLE_OF_KEYNAMES,
    TABLE_PRIMARY_KEYS,
    CursorSlot,
    CursorState,
    CursorStateTable,
    KeyOfReference,
    MostRelation,
)
from acas_posting.dal.status import (
    AccessType,
    AcasFileHandlerFatalError,
    FileFunction,
    FsReply,
    LogSystem,
    WeError,
    is_duplicate_key_bridge_level,
    log_file_handler_record,
    log_handler_failure,
    mysql_1100_db_error,
    start_access_type_is_valid,
)
from acas_posting.dictionary import loader
from acas_posting.records.file_access import FileAccess, LoggingData, RdbData
from acas_posting.records.file_defs import FileDefs
from acas_posting.records.system_record import SystemRecord
from acas_posting.records.test_data_flags import AcasDalCommonData
from acas_posting.records.value_analysis import VaCode, VaGroup, WsValueRecord

if TYPE_CHECKING:  # pragma: no cover - typing only, never imported at runtime
    from mysql.connector.abstracts import MySQLConnectionAbstract

__all__: Final[tuple[str, ...]] = (
    # Identity, provenance and the machine-readable traceability data (R-5).
    "ANOMALIES",
    "BRIDGE",
    "COLUMNS",
    "ENTITY_FACADE",
    "HANDLER",
    "KEY_OF_REFERENCE",
    "OMITTED_COPYBOOK_FIELDS",
    "OMITTED_PARAGRAPHS",
    "PARAGRAPH_FUNCTIONS",
    "PROG_NAME",
    "RECORD_COPYBOOK",
    "SEQUENTIAL_READ_LOW_KEY",
    "SEQUENTIAL_READ_RELATION",
    "TABLE_NAME",
    "TABLE_PRIMARY_KEY",
    "WS_FILE_KEY_WIDTH",
    "WS_LOG_FILE_NO_COBOL",
    "WS_LOG_FILE_NO_RDB",
    "WS_LOG_SYSTEM",
    "Anomaly",
    "ColumnBinding",
    "IndexedFilePathNotMigrated",
    "TdValueanalRec",
    "column_citations",
    "paragraph_coverage",
    "dispatch",
    "value_mt",
    "aa010_main",
    "aa020_process_open",
    "aa030_process_close",
    "aa040_process_read_next",
    "aa045_eval_keys",
    "aa050_process_read_indexed",
    "aa060_process_start",
    "aa070_process_write",
    "aa080_process_delete",
    "aa090_process_rewrite",
    "aa100_bad_function",
    "aa999_main_exit",
    "aa_main_exit",
    "aa_exit",
    "ba_process_rdbms",
    "ba010_test_ws_rec_size",
    "ba012_test_ws_rec_size_2",
    "ba015_test_ends",
    "ba020_call",
    "ba_rdbms_exit",
    "ca_process_logs",
    "ca_exit",
    "ba010_initialise",
    "ba020_process_open",
    "ba030_process_close",
    "ba040_process_read_next",
    "ba041_reread",
    "ba050_process_read_indexed",
    "ba060_process_start",
    "ba070_process_write",
    "ba080_process_delete",
    "ba085_process_delete_all",
    "ba090_process_rewrite",
    "ba100_bad_function",
    "ba998_free",
    "ba999_end",
    "bb000_hv_load",
    "bb100_unload_hvs",
    "bb200_insert",
    "bb300_update",
    "cursor_states",
    "reset_module_state",
)

_LOG: Final[logging.Logger] = logging.getLogger(__name__)


class IndexedFilePathNotMigrated(RuntimeError):
    """Raised where the frozen handler would issue an indexed-file verb.

    ``acas013`` serves two data paths and picks one at [common/acas013.cbl:L321-L325].
    """


HANDLER: Final[str] = "acas013"

BRIDGE: Final[str] = "valueMT"

TABLE_NAME: Final[str] = "VALUEANAL-REC"

ENTITY_FACADE: Final[str] = "Value"

#: `copy "wsval.cob" replacing VA-Code by WS-VA-Code.` [common/acas013.cbl:L269], which
#: is why the linkage record's key is `WS-VA-Code` while the indexed-file record keeps
#: `VA-Code` [copybooks/fdval.cob:L11].
RECORD_COPYBOOK: Final[str] = "copybooks/wsval.cob"

#: `PRIMARY KEY (`VA-CODE`)` [mysql/ACASDB.sql:L1429]. Taken from the shared declaration
#: table so this module and the cursor emulator cannot drift apart.
TABLE_PRIMARY_KEY: Final[str] = TABLE_PRIMARY_KEYS[TABLE_NAME]

#: N-logsystem6. `move 6 to WS-Log-System.` with the comment `*> 1 = IRS, 2=GL, 3=SL,
#: 4=PL, 6=PL & SL, 5=Stock used in FH logging` [common/acas013.cbl:L298].
WS_LOG_SYSTEM: Final[int] = 6

#: N-log, first half. `move 13 to WS-Log-File-No.` [common/acas013.cbl:L299], which is
#: the indexed-file number: `select value-file assign file-13`
#: [copybooks/selval.cob:L2].
WS_LOG_FILE_NO_COBOL: Final[int] = 13

#: N-log, second half. `move 23 to WS-Log-File-no.` [common/acas013.cbl:L602] - the sole
#: statement of `ba010-Test-WS-Rec-Size`, reached only by `perform ba-Process-RDBMS`
#: [:L324].
WS_LOG_FILE_NO_RDB: Final[int] = 23

#: ``77 prog-name pic x(17) value "acas013 (3.3.00)"`` [common/acas013.cbl:L250] - the
#: handler's own self-identification, carried so a log line can name the version of the
#: program whose behaviour is reproduced.
PROG_NAME: Final[str] = "acas013 (3.3.00)"

#: ``03  AC901  pic x(31)`` [common/acas013.cbl:L263] and ``03  AC902  pic x(32)``
#: [common/acas013.cbl:L264] - the two operator messages of the 901 record-size
#: path.
#:
#: ``_AC901`` IS DECLARED AND DELIBERATELY UNREFERENCED. The declaration is a fact
#: about the program's ``Error-Messages`` group and R-5 keeps it, but its text is
#: purely the acknowledgement half - it asks the operator to "hit return", which is
#: the ``accept`` AAP section 0.3.4 drops - so no log record quotes it. Only
#: ``_AC902``, which names the error, reaches a record.
_AC901: Final[str] = "AC901 Note error and hit return"
_AC902: Final[str] = "AC902 Program Error: Temp rec = "

#: ``move function Length (WS-Value-Record) to A`` [common/acas013.cbl:L607-L609]. 66
#: bytes, as ``copybooks/wsval.cob:L6`` declares and as the field sum confirms.
_WS_VALUE_RECORD_LENGTH: Final[int] = 66

#: ``move function length (Value-Record) to B`` [common/acas013.cbl:L610-L612]. Also 66.
_VALUE_RECORD_LENGTH: Final[int] = 66

WS_FILE_KEY_WIDTH: Final[int] = 64

_WS_LOG_WHERE_WIDTH: Final[int] = 231

#: `01 WS-MYSQL-EDIT PIC -Z(18)9.9(9).` [common/valueMT.cbl:L225]. Thirty characters.
_EDIT_WIDTH: Final[int] = 30
_EDIT_INTEGER_POSITIONS: Final[int] = 19
_EDIT_DECIMAL_POSITIONS: Final[int] = 9

_EDIT_INTEGER_SLICE: Final[tuple[int, int]] = (13, 8)
_EDIT_DECIMAL_SLICE: Final[tuple[int, int]] = (22, 2)

#: The shared logging-subsystem census, read rather than restated, so that
#: N-logsystem6's claim can be checked instead of asserted: this handler's 6 is absent
#: from it.
_LOG_SYSTEM_CENSUS: Final[Mapping[str, int]] = MappingProxyType(
    {member.name: int(member.value) for member in LogSystem}
)

_LOG_SYSTEM_IS_UNCENSUSED: Final[bool] = WS_LOG_SYSTEM not in set(
    _LOG_SYSTEM_CENSUS.values()
)


#: The four copybook fields that have NO host variable and NO column, recorded as
#: deliberate omissions per R-5 ("Deliberate omissions are recorded as omissions")
#: rather than given columns of their own.
OMITTED_COPYBOOK_FIELDS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "va-system": (
            "[copybooks/wsval.cob:L11] pic x - character 1 of VA-CODE; "
            "flattened away by [common/valueMT.cbl:L310]"
        ),
        "va-group": (
            "[copybooks/wsval.cob:L12] group of two x - characters 2 to 3 of "
            "VA-CODE; flattened away by [common/valueMT.cbl:L310]"
        ),
        "va-first": (
            "[copybooks/wsval.cob:L13] pic x - character 2 of VA-CODE; "
            "flattened away by [common/valueMT.cbl:L310]"
        ),
        "va-second": (
            "[copybooks/wsval.cob:L14] pic x - character 3 of VA-CODE; "
            "flattened away by [common/valueMT.cbl:L310]"
        ),
    }
)


# The anomaly register, in machine-readable form (R-4).


@dataclass(frozen=True, slots=True)
class Anomaly:
    """One reproduced legacy defect, with where it is and where it came from."""

    #: Stable identifier, matching the module docstring's register.
    name: str
    #: One-line statement of the defect, in this module's own words.
    summary: str
    locators: tuple[str, ...]
    #: The function or data name in this module that reproduces it.
    reproduced_at: str


#: The complete register for this handler-and-bridge pair. Thirty-one entries.
ANOMALIES: Final[Mapping[str, Anomaly]] = MappingProxyType(
    {
        anomaly.name: anomaly
        for anomaly in (
            Anomaly(
                "N-money-signloss",
                "Three MONETARY fields are signed in the copybook, unsigned in "
                "the bridge host variable and unsigned in the column, so a "
                "negative value analysis total loses its sign before any SQL "
                "runs. Corrects Agent Action Plan section 0.6.2, which is true "
                "for salesMT and nominalMT and false here.",
                (
                    "[copybooks/wsval.cob:L21-L23]",
                    "[common/valueMT.cbl:L294-L296]",
                    "[mysql/ACASDB.sql:L1426-L1428]",
                    "[common/salesMT.cbl:L313-L319]",
                    "[common/nominalMT.cbl:L300-L305]",
                ),
                "_hv_unsigned_money",
            ),
            Anomaly(
                "N-flatkey",
                "A three-level key group is flattened and renamed in the "
                "bridge's inline record, leaving four copybook sub-fields with "
                "no host variable and no column.",
                (
                    "[copybooks/wsval.cob:L10-L14]",
                    "[common/valueMT.cbl:L309-L310]",
                ),
                "OMITTED_COPYBOOK_FIELDS",
            ),
            Anomaly(
                "N-inline-record",
                "The bridge does not copy its copybook. It re-declares the "
                "record inline in its Linkage Section, named after the TABLE "
                "rather than after the record. One of five bridges that do "
                "this, with analMT, purchMT, irsnominalMT and, partially, "
                "slinvoiceMT and plinvoiceMT.",
                ("[common/valueMT.cbl:L309-L319]",),
                "TdValueanalRec",
            ),
            Anomaly(
                "N-logsystem6",
                "A sixth logging subsystem code, 6, meaning 'PL & SL' - a "
                "composite no other handler uses - and its own comment lists it "
                "between 4 and 5, out of numeric order.",
                ("[common/acas013.cbl:L298]",),
                "WS_LOG_SYSTEM",
            ),
            Anomaly(
                "N-log",
                "The log file number is 13 on the indexed path and 23 on the "
                "relational path, because the indexed path performs the second "
                "size-test paragraph directly and so skips the paragraph whose "
                "only statement is the overwrite.",
                (
                    "[common/acas013.cbl:L299]",
                    "[common/acas013.cbl:L329]",
                    "[common/acas013.cbl:L602]",
                ),
                "ba010_test_ws_rec_size",
            ),
            Anomaly(
                "N-noreread",
                "No reread paragraph of any name. Five sibling handlers, five "
                "different shapes: acas005 has aa041 plus aa047-Eval-Keys, "
                "acas006 and acas007 have aa041 plus aa051, acas012 has aa041 "
                "plus aa045-Eval-Keys, acas008 has neither, and acas013 has "
                "aa045-Eval-Keys alone. There is no handler template.",
                (
                    "[common/acas013.cbl:L452]",
                    "[common/acas005.cbl:L433]",
                    "[common/acas006.cbl:L436]",
                    "[common/acas007.cbl:L430]",
                    "[common/acas012.cbl:L429]",
                ),
                "aa045_eval_keys",
            ),
            Anomaly(
                "N-ba020call",
                "The bridge-call paragraph is named ba020-Call, not "
                "ba020-Process-DAL. Verified census: three handlers declare "
                "ba020-Process-DAL (acas005 L662, acas006 L653, acas007 L640), "
                "two have no such paragraph and call inline from ba015-Test-Ends "
                "(acas008 L583, acas012 L658), and acas013 alone uses "
                "ba020-Call. This corrects the assignment brief, which places "
                "acas012 in the first group.",
                (
                    "[common/acas013.cbl:L663]",
                    "[common/acas005.cbl:L662]",
                    "[common/acas012.cbl:L658]",
                ),
                "ba020_call",
            ),
            Anomaly(
                "N-hvcase",
                "Host-variable names are lower-cased after the HV- prefix in "
                "both transfer paragraphs while their declarations are upper "
                "case, and the key move alone is upper case in each.",
                (
                    "[common/valueMT.cbl:L288-L296]",
                    "[common/valueMT.cbl:L1060-L1069]",
                    "[common/valueMT.cbl:L1088-L1097]",
                ),
                "bb000_hv_load",
            ),
            Anomaly(
                "N-initialize",
                "Two initialisation semantics in one bridge: "
                "`initialize VALUEANAL-REC with filler` on one error path and "
                "plain `initialize VALUEANAL-REC` in the unload paragraph.",
                (
                    "[common/valueMT.cbl:L582]",
                    "[common/valueMT.cbl:L1086]",
                ),
                "bb100_unload_hvs",
            ),
            Anomaly(
                "N-recsize",
                "The copybook and the file description both declare 66 bytes. "
                "The field sum is 3 + 6 + 24 + 3 + three 4-byte COMP + three "
                "6-byte COMP-3 = 66, so under the compiler's default binary "
                "sizing the declaration agrees - unlike wsbatch.cob's 96 versus "
                "98. The agreement is compiler-configuration dependent and the "
                "arithmetic is recorded rather than the question resolved.",
                (
                    "[copybooks/wsval.cob:L6]",
                    "[copybooks/fdval.cob:L6]",
                    "[common/acas013.cbl:L604-L618]",
                ),
                "ba012_test_ws_rec_size_2",
            ),
            Anomaly(
                "N-guard",
                "The delete key guard rejects any key number other than 1 with "
                "996, its comment explaining that 1 is only meaningful for the "
                "relational store because the indexed store deletes on the "
                "primary key.",
                ("[common/acas013.cbl:L311-L316]",),
                "_aa010_key_guard",
            ),
            Anomaly(
                "N-998",
                "998 carries three different meanings in one program: the key "
                "guard's 'key type out of range', read-indexed's 'should never "
                "get here', and START's access type out of range - for which "
                "the program's own error table documents 997, not 998.",
                (
                    "[common/acas013.cbl:L168-L191]",
                    "[common/acas013.cbl:L307]",
                    "[common/acas013.cbl:L488]",
                    "[common/acas013.cbl:L502]",
                ),
                "_aa010_key_guard",
            ),
            Anomaly(
                "N-996-comment",
                "The delete guard's comment is a copy of the seek guard's - "
                "'file seeks key type out of range' with only the number "
                "changed - contradicting the program's own error table, which "
                "reads 'File Delete key out of range (not 1)'.",
                (
                    "[common/acas013.cbl:L307]",
                    "[common/acas013.cbl:L313]",
                    "[common/acas013.cbl:L172]",
                ),
                "_aa010_key_guard",
            ),
            Anomaly(
                "N-kortype",
                "The key declaration table carries a key type, 'STR', whose own "
                "declaration comment says it is not used currently. It differs "
                "per bridge - 'BNT' in slpostingMT - which makes it data that "
                "varies and is read by nothing.",
                (
                    "[common/valueMT.cbl:L240]",
                    "[common/valueMT.cbl:L247]",
                ),
                "KEY_OF_REFERENCE",
            ),
            Anomaly(
                "N-noextendverb",
                "The facade publishes eleven Value verbs and no "
                "Value-Open-Extend, so Access-Type 4 cannot reach the handler "
                "through it - yet the handler still implements that access "
                "type, with the open extend commented out and a We-Error 997 in "
                "its place.",
                (
                    "[copybooks/Proc-ACAS-FH-Calls.cob:L711-L768]",
                    "[common/acas013.cbl:L390-L394]",
                ),
                "aa020_process_open",
            ),
            Anomaly(
                "N-startguard",
                "The two layers disagree on the START guard twice over: the "
                "handler writes We-Error 998 and never writes FS-Reply, the "
                "bridge writes We-Error 997 and FS-Reply 99, for the identical "
                "test. Both are reproduced at their own site.",
                (
                    "[common/acas013.cbl:L501-L504]",
                    "[common/valueMT.cbl:L699-L703]",
                ),
                "aa060_process_start",
            ),
            Anomaly(
                "N-badfunc",
                "The two layers disagree on the bad-function code: the handler "
                "writes 999, the bridge writes 990.",
                (
                    "[common/acas013.cbl:L571-L573]",
                    "[common/valueMT.cbl:L1019-L1021]",
                ),
                "ba100_bad_function",
            ),
            Anomaly(
                "N-wscountrows",
                "A copybook field, WS-Count-Rows, is annotated 'used in "
                "Delete-All in valueMT' and is referenced nowhere in valueMT, "
                "which uses WS-MYSQL-Count-Rows throughout.",
                (
                    "[copybooks/wsfnctn.cob:L55]",
                    "[common/valueMT.cbl:L940-L944]",
                ),
                "ba085_process_delete_all",
            ),
            Anomaly(
                "N-filekey-deadstore",
                "Read-indexed writes the fetched key to the log key and "
                "immediately overwrites it with an edited row count the "
                "paragraph never sets - so the logged key is a stale count from "
                "an earlier operation.",
                ("[common/valueMT.cbl:L690-L691]",),
                "ba050_process_read_indexed",
            ),
            Anomaly(
                "N-deleteall-zzz",
                "Delete-All moves 'ZZZ' into the CALLER'S record key and then "
                "deletes strictly less than it, so a row keyed 'ZZZ' or higher "
                "survives a delete-all, and the caller's record is mutated to "
                "achieve that.",
                (
                    "[common/valueMT.cbl:L913]",
                    "[common/valueMT.cbl:L919-L924]",
                ),
                "ba085_process_delete_all",
            ),
            Anomaly(
                "N-readnext-lowkey",
                "Sequential read positions with a low key of '000' and the "
                "relation >=, so any row sorting below '000' is silently never "
                "returned; the adjacent comment claims > and an order by the "
                "table name, and both are wrong.",
                (
                    "[common/valueMT.cbl:L473-L485]",
                    "[common/valueMT.cbl:L498]",
                ),
                "ba040_process_read_next",
            ),
            Anomaly(
                "N-start-nostatus",
                "When START matches no row and the driver reports no error, "
                "neither FS-Reply nor We-Error is written, so a fruitless START "
                "leaves the caller's previous status in place and can look like "
                "success.",
                ("[common/valueMT.cbl:L771-L788]",),
                "ba060_process_start",
            ),
            Anomaly(
                "N-reread-staleeof",
                "The fetch tests the CALLER'S incoming FS-Reply for 10 AFTER "
                "fetching, so a row that was successfully retrieved is "
                "discarded when the caller happened to arrive with an "
                "end-of-file status.",
                ("[common/valueMT.cbl:L589-L594]",),
                "ba041_reread",
            ),
            Anomaly(
                "N-deadcode",
                "Two unreachable blocks: a jump back into the fetch paragraph "
                "placed after START's own unconditional jump, and the START "
                "relation arm for access type 9, which the guard above it "
                "already rejects.",
                (
                    "[common/valueMT.cbl:L802-L804]",
                    "[common/valueMT.cbl:L699-L703]",
                    "[common/valueMT.cbl:L730-L731]",
                ),
                "ba060_process_start",
            ),
            Anomaly(
                "N-stopliteral",
                "A debugging `stop \"Cobol File EOF\"` with the comment 'for "
                "testing' halts the run on the indexed read-next path.",
                ("[common/acas013.cbl:L431]",),
                "aa040_process_read_next",
            ),
            Anomaly(
                "N-closelogtwice",
                "Close writes two log records: one through the shared exit "
                "paragraph with the real function code, then a second after "
                "zeroing both the function and the access type.",
                ("[common/acas013.cbl:L406-L417]",),
                "aa030_process_close",
            ),
            Anomaly(
                "N-writenokey",
                "Write never performs the key-resolving paragraph, although "
                "that paragraph explicitly handles function 5, so the write is "
                "logged against whatever key an earlier operation left.",
                (
                    "[common/acas013.cbl:L538-L546]",
                    "[common/acas013.cbl:L452-L468]",
                ),
                "aa070_process_write",
            ),
            Anomaly(
                "N-casing",
                "Four casing inconsistencies, all harmless in a "
                "case-insensitive language and none normalised: the log file "
                "field spelled -No then -no, the key paragraph performed as "
                "Eval-keys and declared as Eval-Keys, one section header "
                "written 'section' in lower case among 'Section' siblings, and "
                "the host-variable case split recorded under N-hvcase.",
                (
                    "[common/acas013.cbl:L299]",
                    "[common/acas013.cbl:L475]",
                    "[common/acas013.cbl:L588]",
                    "[common/acas013.cbl:L602]",
                ),
                "ba_process_rdbms",
            ),
            Anomaly(
                "N-varsab",
                "The changelog announces 'Chgd Vars A & B to pic 999' and the "
                "code declares them pic 9(4) - a changelog entry contradicted "
                "by the code it describes.",
                (
                    "[common/acas013.cbl:L144]",
                    "[common/acas013.cbl:L254-L255]",
                ),
                "ba012_test_ws_rec_size_2",
            ),
            Anomaly(
                "N-pointer-offbyone",
                "Every where clause is built with a string pointer starting at "
                "1 and then consumed as (1:J), J having advanced one past the "
                "last character - so every emitted statement and every logged "
                "clause carries exactly one extra trailing space. The rewrite's "
                "where clause is the only one trimmed, so it alone escapes.",
                (
                    "[common/valueMT.cbl:L479-L487]",
                    "[common/valueMT.cbl:L495-L499]",
                    "[common/valueMT.cbl:L1392]",
                ),
                "_where_with_pointer",
            ),
            Anomaly(
                "N-updates-key",
                "The rewrite assigns all ten columns including the primary key, "
                "so VA-CODE is set to itself in every update, and the same "
                "value appears in the where clause.",
                (
                    "[common/valueMT.cbl:L1265-L1271]",
                    "[common/valueMT.cbl:L1388-L1396]",
                ),
                "bb300_update",
            ),
        )
    }
)


# The ten columns, derived from the data dictionary (R-5, "dictionary first").


@dataclass(frozen=True, slots=True)
class ColumnBinding:
    """One column of ``VALUEANAL-REC``, with the whole authoritative triple.

    Every field of this record is DERIVED - from ``loader.get_entry``,
    ``loader.drift_for`` and ``loader.cite`` - and none is transcribed from a picture
    clause.
    """

    name: str
    ordinal: int
    dictionary_key: str
    citation: str
    #: Attribute of :class:`WsValueRecord` this column is carried in.
    record_attribute: str
    host_attribute: str
    storage: str
    host_digits: int
    host_integer_digits: int
    #: Decimal places of the host variable: 2 for money, 0 otherwise.
    host_scale: int
    host_length: int
    #: Whether the host variable is signed. ``False`` for all ten here, which for the
    #: three money columns is the anomaly.
    host_signed: bool
    copybook_signed: bool
    column_unsigned: bool
    primary_key: bool
    #: The dictionary's own drift prose, verbatim, so the reason is never paraphrased
    #: away.
    drift_details: tuple[str, ...]
    #: Anomaly and ambiguity identifiers the dictionary attached to this field.
    anomaly_refs: tuple[str, ...]
    ambiguity_refs: tuple[str, ...]

    @property
    def quoted(self) -> str:
        """The column name, backtick-quoted, ready for a statement."""
        return quote_identifier(self.name)

    @property
    def loses_its_sign_at_the_bridge(self) -> bool:
        """N-money-signloss, expressed as a predicate over dictionary facts.

        True exactly when the copybook declares the field signed and the bridge host
        variable does not, which is the condition [copybooks/wsval.cob:L21-L23] against
        [common/valueMT.cbl:L294-L296] creates. It is derived rather than listed, so a
        field cannot be missed.
        """
        return self.copybook_signed and not self.host_signed


_RECORD_ATTRIBUTES: Final[Mapping[str, tuple[str, str]]] = MappingProxyType(
    {
        "VA-CODE": ("va_code", "hv_va_code"),
        "VA-GL": ("va_gl", "hv_va_gl"),
        "VA-DESC": ("va_desc", "hv_va_desc"),
        "VA-PRINT": ("va_print", "hv_va_print"),
        "VA-T-THIS": ("va_t_this", "hv_va_t_this"),
        "VA-T-LAST": ("va_t_last", "hv_va_t_last"),
        "VA-T-YEAR": ("va_t_year", "hv_va_t_year"),
        "VA-V-THIS": ("va_v_this", "hv_va_v_this"),
        "VA-V-LAST": ("va_v_last", "hv_va_v_last"),
        "VA-V-YEAR": ("va_v_year", "hv_va_v_year"),
    }
)


def _build_columns() -> tuple[ColumnBinding, ...]:
    """Derive the ten column bindings from the generated data dictionary.

    ``loader.entries_for_table`` returns the entries in COLUMN-ORDINAL order, which is
    the order every statement in this module names its columns in, so no sorting is
    applied and none is needed. The result is deterministic.

    Raises:
        RuntimeError: If the dictionary and this module disagree about the table.
    """
    entries = loader.entries_for_table(TABLE_NAME)
    expected = tuple(_RECORD_ATTRIBUTES)
    found = tuple(entry.column.name for entry in entries)
    if found != expected:
        raise RuntimeError(
            f"data dictionary and {HANDLER} disagree about {TABLE_NAME}: "
            f"dictionary lists {found!r}, module expects {expected!r}"
        )

    bindings: list[ColumnBinding] = []
    for ordinal, entry in enumerate(entries, start=1):
        column = entry.column
        if column.ordinal != ordinal:
            raise RuntimeError(
                f"data dictionary returned {TABLE_NAME}.{column.name} at "
                f"position {ordinal} with ordinal {column.ordinal}; "
                "entries_for_table must be in column-ordinal order"
            )
        record_attribute, host_attribute = _RECORD_ATTRIBUTES[column.name]
        host = entry.bridge_host_variable
        drift = loader.drift_for(entry.key)
        bindings.append(
            ColumnBinding(
                name=column.name,
                ordinal=column.ordinal,
                dictionary_key=entry.key,
                citation=loader.cite(entry.key),
                record_attribute=record_attribute,
                host_attribute=host_attribute,
                storage=str(entry.cobol_python_storage.value),
                host_digits=int(host.digits or 0),
                host_integer_digits=int(host.integer_digits or 0),
                host_scale=int(host.scale or 0),
                host_length=int(host.character_length or 0),
                host_signed=bool(host.signed),
                copybook_signed=bool(entry.copybook.signed),
                column_unsigned=bool(column.unsigned),
                primary_key=bool(column.is_primary_key),
                drift_details=tuple(drift.details),
                anomaly_refs=tuple(entry.anomaly_refs),
                ambiguity_refs=tuple(entry.ambiguity_refs),
            )
        )
    return tuple(bindings)


#: The ten columns of ``VALUEANAL-REC`` in column-ordinal order, every field derived
#: from the data dictionary.
COLUMNS: Final[tuple[ColumnBinding, ...]] = _build_columns()

_COLUMNS_BY_NAME: Final[Mapping[str, ColumnBinding]] = MappingProxyType(
    {binding.name: binding for binding in COLUMNS}
)

#: The three money columns, identified by the dictionary rather than by a hard coded
#: list - see :attr:`ColumnBinding.loses_its_sign_at_the_bridge`.
_SIGN_LOSING_COLUMNS: Final[tuple[ColumnBinding, ...]] = tuple(
    binding for binding in COLUMNS if binding.loses_its_sign_at_the_bridge
)


def column_citations() -> tuple[str, ...]:
    """Return one dictionary citation per column, in column-ordinal order."""
    return tuple(binding.citation for binding in COLUMNS)


KEY_OF_REFERENCE: Final[KeyOfReference] = TABLE_OF_KEYNAMES[TABLE_NAME][0]

#: The sequential-read starting position, `>= "000"` [common/valueMT.cbl:L476-L477].
#: N-readnext-lowkey.
_SEQUENTIAL_READ: Final = SEQUENTIAL_READ_START[TABLE_NAME]

SEQUENTIAL_READ_RELATION: Final[str] = _SEQUENTIAL_READ.relation.token

#: The low key itself, ``000``.
SEQUENTIAL_READ_LOW_KEY: Final[str] = str(_SEQUENTIAL_READ.low_key)

_CURSOR_SLOT: Final[CursorSlot] = CursorSlot.PRIMARY


# COBOL storage and edit semantics, reproduced for this table only.


def _pic_x(value: object, length: int) -> str:
    """Store ``value`` into a ``PIC X(length)`` item, as ``MOVE`` would."""
    text = "" if value is None else str(value)
    return text[:length].ljust(length)


def _cobol_trim_trailing(text: str) -> str:
    """``FUNCTION TRIM (item, TRAILING)`` - trailing spaces only.

    The bridge trims the three alphanumeric host variables this way, and only this way,
    before quoting them into a statement [common/valueMT.cbl:L1119, :L1140, :L1149] on
    the insert path and [:L1268, :L1289, :L1298] on the update path.
    """
    return text.rstrip(" ")


def _cobol_trim(text: str) -> str:
    """``FUNCTION TRIM (item)`` with no direction - both ends."""
    return text.strip(" ")


def _ws_mysql_edit(value: Decimal) -> str:
    """Render into ``WS-MYSQL-EDIT``, ``PIC -Z(18)9.9(9)``.

    Thirty characters [common/valueMT.cbl:L225]: the sign at character 1, nineteen
    integer digit positions at 2 to 20, the decimal point at 21, nine decimal positions
    at 22 to 30.

    Args:
        value: The host variable's value, always non-negative by the time it arrives
            because every host variable here is unsigned and
            :func:`_hv_unsigned_money` and :func:`_hv_unsigned_integer` have already
            applied that.

    Returns:
        Exactly thirty characters.
    """
    sign = "-" if value < 0 else " "
    magnitude = value.copy_abs()
    integer_part = int(magnitude)
    # The nine decimal positions, as digits, taken by scaling rather than by text
    # surgery so that a value carrying fewer than nine places pads with zeros exactly as
    # the picture does.
    fraction = magnitude - Decimal(integer_part)
    decimals = int(
        (fraction * (10**_EDIT_DECIMAL_POSITIONS)).quantize(
            Decimal(1), rounding=ROUND_DOWN
        )
    )
    integer_digits = str(integer_part)[-_EDIT_INTEGER_POSITIONS:]
    suppressed = integer_digits.rjust(_EDIT_INTEGER_POSITIONS)
    rendered = f"{sign}{suppressed}.{decimals:0{_EDIT_DECIMAL_POSITIONS}d}"
    return _pic_x(rendered, _EDIT_WIDTH)


def _edit_slice(edited: str, start: int, length: int) -> str:
    """Take a one-based COBOL reference modification out of an edited item.

    ``WS-MYSQL-EDIT(13:08)`` is characters 13 to 20 inclusive; Python's slice bounds are
    shifted by one. Isolated so that the two magic pairs appear once each, next to their
    locator, instead of at ten call sites.
    """
    return edited[start - 1 : start - 1 + length]


def _require_exact_numeric(value: object, what: str) -> None:
    """Refuse any numeric value that is not exactly representable.

    (Agent Action Plan section 0.7.2, R-2), which forbids an accounting value passing
    through a binary floating-point type "at any point - not in computation, not in
    storage, not in transport".

    Args:
        value: The candidate, straight from a record or host-variable field.
        what: The field being stored, for a diagnosis that names the culprit.

    Raises:
        TypeError: If the value is neither ``Decimal`` nor ``int``. >>>
            _require_exact_numeric(Decimal("1.23"), "VA-V-THIS") >>>
            _require_exact_numeric(7, "VA-GL").
    """
    if not isinstance(value, (Decimal, int)):
        raise TypeError(
            f"{HANDLER}/{BRIDGE}: {what} must be an exact numeric value "
            f"(Decimal or int), not {type(value).__name__}. Rule R-2 forbids an "
            f"accounting value passing through a binary floating-point type at "
            f"any point; quantizing one here would launder the artefact instead "
            f"of catching it."
        )


def _hv_unsigned_money(value: Decimal, binding: ColumnBinding) -> Decimal:
    """N-money-signloss. Store into an UNSIGNED money host variable.

    THE ONE HELPER for all three money fields, applied in :func:`bb000_hv_load` before
    any statement text exists, because that is where COBOL applies it.

    Args:
        value: The record's value, signed as the copybook declares it.
        binding: The column, for its host-variable digits and scale. Passed rather than
            assumed so the shape comes from the dictionary.

    Returns:
        The magnitude, fitted to the host variable, at the host variable's scale.

    Raises:
        TypeError: If the value is not an exact numeric type. See
            :func:`_require_exact_numeric`.
    """
    _require_exact_numeric(value, f"{binding.name} (record value)")
    magnitude = Decimal(value).copy_abs()
    scale = Decimal(1).scaleb(-binding.host_scale)
    fitted = magnitude.quantize(scale, rounding=ROUND_DOWN)
    modulus = Decimal(10) ** binding.host_integer_digits
    if fitted >= modulus:
        fitted = (fitted % modulus).quantize(scale, rounding=ROUND_DOWN)
    return fitted


def _hv_unsigned_integer(value: int, binding: ColumnBinding) -> int:
    """Store into an unsigned integer host variable, ``PIC 9(08) COMP``.

    Covers ``HV-VA-GL`` and the three ``HV-VA-T-*`` counters [common/valueMT.cbl:L288,
    :L291-L293]. Unlike the money fields these lose NOTHING at the bridge, and the
    difference is worth stating because it is what makes the money case an anomaly
    rather than a pattern.

    Raises:
        TypeError: If the value is not an exact numeric type. See
            :func:`_require_exact_numeric`.
    """
    _require_exact_numeric(value, f"{binding.name} (record value)")
    value = int(value)
    magnitude = -value if value < 0 else value
    modulus = 10**binding.host_integer_digits
    return magnitude % modulus


@dataclass(slots=True)
class TdValueanalRec:
    """``01 TD-VALUEANAL-REC.`` - the bridge's host-variable group.

    THE LAST THREE CARRY NO ``S``. That is N-money-signloss, and it is the whole reason
    this class exists as its own type rather than as a dictionary of values.
    """

    hv_va_code: str = "   "
    hv_va_gl: int = 0
    hv_va_desc: str = " " * 24
    hv_va_print: str = "   "
    hv_va_t_this: int = 0
    hv_va_t_last: int = 0
    hv_va_t_year: int = 0
    hv_va_v_this: Decimal = field(default_factory=lambda: Decimal("0.00"))
    hv_va_v_last: Decimal = field(default_factory=lambda: Decimal("0.00"))
    hv_va_v_year: Decimal = field(default_factory=lambda: Decimal("0.00"))

    def initialize(self) -> None:
        """``initialize TD-VALUEANAL-REC.`` [common/valueMT.cbl:L1059].

        The FIRST statement of the load paragraph, and the reason every column of this
        table can be declared ``NOT NULL``: an unset field becomes zero or space, never
        SQL ``NULL``.
        """
        self.hv_va_code = "   "
        self.hv_va_gl = 0
        self.hv_va_desc = " " * 24
        self.hv_va_print = "   "
        self.hv_va_t_this = 0
        self.hv_va_t_last = 0
        self.hv_va_t_year = 0
        self.hv_va_v_this = Decimal("0.00")
        self.hv_va_v_last = Decimal("0.00")
        self.hv_va_v_year = Decimal("0.00")


def _flat_key_of(value: WsValueRecord) -> str:
    """The three characters of ``WS-Va-Code``, as the bridge sees the key."""
    code = value.va_code
    return _pic_x(
        f"{code.va_system}{code.va_group.va_first}{code.va_group.va_second}",
        KEY_OF_REFERENCE.kor_length,
    )


def bb000_hv_load(value: WsValueRecord) -> TdValueanalRec:
    """``bb000-HV-Load Section.`` [common/valueMT.cbl:L1051].

    Four facts about that block, each preserved rather than tidied.

    Args:
        value: The caller's ``WS-Value-Record``. Not modified.

    Returns:
        A freshly initialised host-variable group holding the converted values.
    """
    host = TdValueanalRec()
    host.initialize()

    host.hv_va_code = _pic_x(_flat_key_of(value), _COLUMNS_BY_NAME["VA-CODE"].host_length)
    host.hv_va_gl = _hv_unsigned_integer(value.va_gl, _COLUMNS_BY_NAME["VA-GL"])
    host.hv_va_desc = _pic_x(value.va_desc, _COLUMNS_BY_NAME["VA-DESC"].host_length)
    host.hv_va_print = _pic_x(value.va_print, _COLUMNS_BY_NAME["VA-PRINT"].host_length)
    # [:L1064-L1066] the three counters. Unsigned in the copybook already, so nothing is
    # lost here - which is what makes the money case below an anomaly.
    host.hv_va_t_this = _hv_unsigned_integer(
        value.va_t_this, _COLUMNS_BY_NAME["VA-T-THIS"]
    )
    host.hv_va_t_last = _hv_unsigned_integer(
        value.va_t_last, _COLUMNS_BY_NAME["VA-T-LAST"]
    )
    host.hv_va_t_year = _hv_unsigned_integer(
        value.va_t_year, _COLUMNS_BY_NAME["VA-T-YEAR"]
    )
    # [:L1067-L1069] the three money fields. N-money-signloss: signed `pic s9(8)v99
    # comp-3` [copybooks/wsval.cob:L21-L23] into unsigned `PIC 9(08)V9(02) COMP`
    # [common/valueMT.cbl:L294-L296], column `decimal(10,2) unsigned`
    # [mysql/ACASDB.sql:L1426-L1428].
    host.hv_va_v_this = _hv_unsigned_money(
        value.va_v_this, _COLUMNS_BY_NAME["VA-V-THIS"]
    )
    host.hv_va_v_last = _hv_unsigned_money(
        value.va_v_last, _COLUMNS_BY_NAME["VA-V-LAST"]
    )
    host.hv_va_v_year = _hv_unsigned_money(
        value.va_v_year, _COLUMNS_BY_NAME["VA-V-YEAR"]
    )
    return host


def bb100_unload_hvs(host: TdValueanalRec, value: WsValueRecord) -> None:
    """``bb100-UnloadHVs Section.`` [common/valueMT.cbl:L1077].

    N-initialize: the initialisation at [:L1086] is PLAIN, while the error path at
    [:L582] writes ``initialize VALUEANAL-REC with filler``. Two initialisation
    semantics in one bridge, as in ``glbatchMT``, ``slpostingMT`` and ``salesMT``.

    Args:
        host: The group just filled by a fetch.
        value: The caller's record, MUTATED in place - which is what a COBOL ``MOVE``
            into a linkage item does, and why :class:`WsValueRecord` is deliberately not
            frozen.
    """
    # [:L1086] `initialize VALUEANAL-REC.` - plain, not `with filler`. Reproduced by
    # writing every field below, which is what INITIALIZE followed by ten unconditional
    # moves amounts to.
    code = _pic_x(host.hv_va_code, KEY_OF_REFERENCE.kor_length)
    value.va_code = VaCode(
        va_system=code[0],
        va_group=VaGroup(va_first=code[1], va_second=code[2]),
    )
    # Every numeric field is checked for exactness before it is read out, so that an
    # inexact value reaching the published host-variable group is refused rather than
    # quantized into a tidy-looking exact one (R-2, see :func:`_require_exact_numeric`).
    for _column, _raw in (
        ("VA-GL", host.hv_va_gl),
        ("VA-T-THIS", host.hv_va_t_this),
        ("VA-T-LAST", host.hv_va_t_last),
        ("VA-T-YEAR", host.hv_va_t_year),
        ("VA-V-THIS", host.hv_va_v_this),
        ("VA-V-LAST", host.hv_va_v_last),
        ("VA-V-YEAR", host.hv_va_v_year),
    ):
        _require_exact_numeric(_raw, f"{_column} (host variable)")
    value.va_gl = int(host.hv_va_gl)
    value.va_desc = _pic_x(host.hv_va_desc, _COLUMNS_BY_NAME["VA-DESC"].host_length)
    value.va_print = _pic_x(host.hv_va_print, _COLUMNS_BY_NAME["VA-PRINT"].host_length)
    value.va_t_this = int(host.hv_va_t_this)
    value.va_t_last = int(host.hv_va_t_last)
    value.va_t_year = int(host.hv_va_t_year)
    # [:L1095-L1097] the three money fields, arriving as magnitudes because the column
    # and the host variable are both unsigned. N-money-signloss.
    scale = Decimal(1).scaleb(-_COLUMNS_BY_NAME["VA-V-THIS"].host_scale)
    value.va_v_this = Decimal(host.hv_va_v_this).quantize(scale, rounding=ROUND_DOWN)
    value.va_v_last = Decimal(host.hv_va_v_last).quantize(scale, rounding=ROUND_DOWN)
    value.va_v_year = Decimal(host.hv_va_v_year).quantize(scale, rounding=ROUND_DOWN)


#: The table name, quoted once.
_QUOTED_TABLE: Final[str] = quote_identifier(TABLE_NAME)

#: The primary-key column, quoted, as the bridge writes it: a backtick, then ``KeyName
#: (KOR-x1) delimited by space``, then a backtick [common/valueMT.cbl:L479-L481].
_QUOTED_KEY: Final[str] = quote_identifier(
    cobol_string_delimited_by_space(KEY_OF_REFERENCE.key_name)
)


@dataclass(frozen=True, slots=True)
class _Statement:
    """One statement in both of its forms, plus what the bridge would log.

    ``text`` is the statement as the BRIDGE assembles it, values interpolated as quoted
    literals, so it can be diffed against the frozen source. ``bound``/``parameters``
    are what actually executes, because
    :func:`acas_posting.dal.connection.execute_statement` binds values and never
    interpolates them.
    """

    text: str
    bound: str
    parameters: tuple[object, ...]


def _where_with_pointer(*parts: str) -> str:
    """Assemble a where clause the way the bridge does, artefact included.

    and then consumed as ``WS-Where (1:J)`` [common/valueMT.cbl:L477-L487, :L609-L618,
    :L735-L749, :L845-L852, :L911-L920].
    """
    return "".join(parts) + " "


def _quoted_literal(text: str) -> str:
    """A value as the bridge quotes it into statement text: double quotes.

    The bridge writes ``'="'`` then the value then ``'"'``
    [common/valueMT.cbl:L612-L616]. MySQL accepts double-quoted strings, which is why
    this works at all. Only ever used to build the COBOL-shaped ``text``.
    """
    return f'"{text}"'


def _rendered_value(binding: ColumnBinding, host: TdValueanalRec) -> tuple[str, object]:
    """Render one host variable as the bridge renders it, and bind the same value.

    * ALPHANUMERIC - ``FUNCTION TRIM (HV-VA-CODE,TRAILING)`` and its two siblings
    [:L1119, :L1140, :L1149]. Trailing spaces only, so a leading space survives into the
    key. ``FUNCTION TRIM (WS-MYSQL-EDIT(13:08))`` [:L1127-L1132].

    Returns:
        The rendered text, and the value to bind for it.
    """
    raw = getattr(host, binding.host_attribute)
    if binding.storage == "DECIMAL":
        edited = _ws_mysql_edit(Decimal(raw))
        integer_text = _cobol_trim(_edit_slice(edited, *_EDIT_INTEGER_SLICE))
        decimal_text = _edit_slice(edited, *_EDIT_DECIMAL_SLICE)
        rendered = f"{integer_text}.{decimal_text}"
        return rendered, Decimal(rendered)
    if binding.storage == "INT":
        edited = _ws_mysql_edit(Decimal(int(raw)))
        rendered = _cobol_trim(_edit_slice(edited, *_EDIT_INTEGER_SLICE))
        return rendered, int(rendered)
    # Alphanumeric, including the flattened key, whose storage the dictionary classifies
    # as NONE because the copybook side of it is a group.
    rendered = _cobol_trim_trailing(_pic_x(raw, binding.host_length))
    return rendered, rendered


def _assignment_list(host: TdValueanalRec) -> tuple[str, str, tuple[object, ...]]:
    """The ten ``column="value"`` assignments, comma-separated, in ordinal order.

    N-updates-key: the list includes ``VA-CODE``, so the update assigns the primary key
    to itself on every rewrite while the same value also appears in the where clause.
    Preserved.
    """
    texts: list[str] = []
    bounds: list[str] = []
    parameters: list[object] = []
    for binding in COLUMNS:
        rendered, bound_value = _rendered_value(binding, host)
        texts.append(f"{binding.quoted}={_quoted_literal(rendered)}")
        bounds.append(f"{binding.quoted}=%s")
        parameters.append(bound_value)
    return ", ".join(texts), ", ".join(bounds), tuple(parameters)


def bb200_insert(host: TdValueanalRec) -> _Statement:
    """``bb200-Insert Section.`` [common/valueMT.cbl:L1102].

    The single space after ``SET`` comes from the literal at [:L1108], which ends with
    one; the first assignment adds none of its own. Preserved, because the text is a
    compared artefact.
    """
    text_list, bound_list, parameters = _assignment_list(host)
    return _Statement(
        text=f"INSERT INTO {_QUOTED_TABLE} SET {text_list};",
        bound=f"INSERT INTO {_QUOTED_TABLE} SET {bound_list}",
        parameters=parameters,
    )


def bb300_update(host: TdValueanalRec, where: _Statement) -> _Statement:
    """``bb300-Update Section.`` [common/valueMT.cbl:L1251].

    THAT TRIM IS THE ONE EXCEPTION TO N-pointer-offbyone. Every other statement in this
    bridge carries the pointer's extra trailing space; the rewrite trims its clause and
    so does not.

    Args:
        host: The loaded host-variable group.
        where: The clause built by :func:`_ba090_where`, still carrying its trailing
            space, which this function trims exactly as [:L1392] does.
    """
    text_list, bound_list, parameters = _assignment_list(host)
    return _Statement(
        text=f"UPDATE {_QUOTED_TABLE} SET {text_list} WHERE {_cobol_trim(where.text)};",
        bound=(
            f"UPDATE {_QUOTED_TABLE} SET {bound_list} "
            f"WHERE {_cobol_trim(where.bound)}"
        ),
        parameters=parameters + where.parameters,
    )


def _key_equals_where(key_value: str) -> _Statement:
    """`` `VA-CODE`="<key>" `` - the clause read-indexed, delete and rewrite share.

    ``VALUEANAL-REC (K:L)`` is the record sliced with the DECLARED offset and length, 1
    and 3 [common/valueMT.cbl:L239] - which after N-flatkey is the whole of ``WS-Va-
    Code``.
    """
    return _Statement(
        text=_where_with_pointer(_QUOTED_KEY, "=", _quoted_literal(key_value)),
        bound=_where_with_pointer(_QUOTED_KEY, "=", "%s"),
        parameters=(key_value,),
    )


def _ba040_where() -> _Statement:
    """The sequential-read clause [common/valueMT.cbl:L477-L487].

    Three facts, all preserved.
    """
    return _Statement(
        text=_where_with_pointer(
            _QUOTED_KEY,
            f" {SEQUENTIAL_READ_RELATION} ",
            _quoted_literal(SEQUENTIAL_READ_LOW_KEY),
            " ORDER BY ",
            _QUOTED_KEY,
            " ASC",
        ),
        bound=_where_with_pointer(
            _QUOTED_KEY,
            f" {SEQUENTIAL_READ_RELATION} ",
            "%s",
            " ORDER BY ",
            _QUOTED_KEY,
            " ASC",
        ),
        parameters=(SEQUENTIAL_READ_LOW_KEY,),
    )


def _ba050_where(key_value: str) -> _Statement:
    """The read-indexed clause [common/valueMT.cbl:L609-L618].

    NO ``ORDER BY`` and NO ``LIMIT`` - the bridge asks for every row matching the key
    and then fetches one [:L633-L637, :L662]. Against a primary key that is at most one
    row, so the absence is harmless here.
    """
    return _key_equals_where(key_value)


def _ba060_where(relation: MostRelation, key_value: str) -> _Statement:
    """The START clause [common/valueMT.cbl:L735-L749].

    * ``MOST-relation delimited by space`` [:L738]. The relation is held in a ``pic
    xxx`` item [:L256] and the padded form is trimmed at its first space, so ``">= "``
    becomes ``">="`` in the text while ``"= "`` becomes ``"="``.
    """
    token = cobol_string_delimited_by_space(relation.padded)
    return _Statement(
        text=_where_with_pointer(
            _QUOTED_KEY,
            token,
            _quoted_literal(key_value),
            " ORDER BY ",
            _QUOTED_KEY,
            " ASC  ",
        ),
        bound=_where_with_pointer(
            _QUOTED_KEY,
            token,
            "%s",
            " ORDER BY ",
            _QUOTED_KEY,
            " ASC  ",
        ),
        parameters=(key_value,),
    )


def _ba080_where(key_value: str) -> _Statement:
    """The delete clause [common/valueMT.cbl:L845-L852] - the shared key equality."""
    return _key_equals_where(key_value)


def _ba085_where(key_value: str) -> _Statement:
    """The delete-all clause [common/valueMT.cbl:L911-L920].

    N-deleteall-zzz: a row keyed exactly ``"ZZZ"``, or anything sorting above it,
    SURVIVES A DELETE-ALL.
    """
    return _Statement(
        text=_where_with_pointer(_QUOTED_KEY, "<", _quoted_literal(key_value)),
        bound=_where_with_pointer(_QUOTED_KEY, "<", "%s"),
        parameters=(key_value,),
    )


def _ba090_where(key_value: str) -> _Statement:
    """The rewrite clause [common/valueMT.cbl:L980-L989] - the shared key equality."""
    return _key_equals_where(key_value)


def _select(where: _Statement) -> _Statement:
    """``SELECT * FROM `VALUEANAL-REC` WHERE <clause>;``.

    ``SELECT *`` and not a column list, which is why :func:`bb100_unload_hvs` can read
    the row back by column name and why the fetch depends on the frozen table's column
    set rather than on a list this module maintains.
    """
    return _Statement(
        text=f"SELECT * FROM {_QUOTED_TABLE} WHERE {where.text};",
        bound=f"SELECT * FROM {_QUOTED_TABLE} WHERE {where.bound}",
        parameters=where.parameters,
    )


def _delete(where: _Statement) -> _Statement:
    """``DELETE FROM `VALUEANAL-REC` WHERE <clause>`` - WITH NO SEMICOLON.

    Both delete paragraphs go straight from the clause to the null terminator, where
    every ``SELECT``, the ``INSERT`` and the ``UPDATE`` all interpose a ``";"``. The
    client library does not require one, so nothing breaks.
    """
    return _Statement(
        text=f"DELETE FROM {_QUOTED_TABLE} WHERE {where.text}",
        bound=f"DELETE FROM {_QUOTED_TABLE} WHERE {where.bound}",
        parameters=where.parameters,
    )


#: ``Most-Cursor-Set`` and the stored result set [common/valueMT.cbl:L255-L258, :L285].
_CURSOR_STATES: CursorStateTable = CursorStateTable()

_CONNECTION: MySQLConnectionAbstract | None = None

#: The system record most recently seen by ``ba012-Test-WS-Rec-Size-2``, which is the
#: paragraph where the credentials cross from ``System-Record`` into ``File-Access``'s
#: ``RDB-Data`` group [common/acas013.cbl:L633-L643].
_SYSTEM_FOR_OPEN: SystemRecord | None = None

#: ``if A = zero`` [common/acas013.cbl:L606] - the record-size test and the credential
#: load run on the FIRST call only, because ``A`` is working storage initialised to zero
#: and left non-zero afterwards.
_RECORD_SIZE_TESTED: bool = False

#: ``77 ws-temp-ed pic 9(10)`` [common/valueMT.cbl:L229], rendered as the ten zero-
#: padded digits a numeric-display item holds.
_WS_TEMP_ED: str = "0" * 10


def cursor_states() -> CursorStateTable:
    """The live cursor state for this table, for inspection and for tests."""
    return _CURSOR_STATES


def reset_module_state() -> None:
    """Discard the cursor, the connection handle and the first-call latch.

    Equivalent to a fresh load of the sub-program: COBOL working storage is re-
    initialised when the module is loaded again, and there is no other way to clear
    ``Most-Cursor-Set`` from outside.
    """
    global _CONNECTION, _SYSTEM_FOR_OPEN, _RECORD_SIZE_TESTED, _WS_TEMP_ED
    _CURSOR_STATES.reset(TABLE_NAME)
    _CONNECTION = None
    _SYSTEM_FOR_OPEN = None
    _RECORD_SIZE_TESTED = False
    _WS_TEMP_ED = "0" * 10


def _state() -> CursorState:
    """The one cursor state slot for this table [common/valueMT.cbl:L255-L258]."""
    return _CURSOR_STATES.state_for(TABLE_NAME, _CURSOR_SLOT)


def _set_file_key(logging_data: LoggingData, text: str) -> None:
    """``move <literal> to WS-File-Key`` - ``pic x(64)``.

    [copybooks/wsfnctn.cob:L52]. Truncated at 64 and space-padded to 64, as a ``MOVE``
    into a fixed alphanumeric item does, so a longer literal loses its tail rather than
    raising.
    """
    logging_data.ws_file_key = _pic_x(text, WS_FILE_KEY_WIDTH)


def _set_log_where(logging_data: LoggingData, text: str) -> None:
    """``move WS-Where (1:J) to WS-Log-Where`` - ``pic x(231)``.

    [copybooks/wsfnctn.cob:L53]. The bridge writes this at every clause site for test
    logging, e.g. [common/valueMT.cbl:L487, :L618, :L750, :L853, :L925]. The text
    arrives already carrying N-pointer-offbyone's extra space, because that is what
    ``(1:J)`` yields.
    """
    logging_data.ws_log_where = _pic_x(text, _WS_LOG_WHERE_WIDTH)


@dataclass(frozen=True, slots=True)
class _DriverResult:
    """What the frozen bridge learns after a statement, and nothing more.

    The bridge issues a statement and then interrogates the client library through three
    foreign calls - ``MySQL_errno``, ``MySQL_sqlstate`` and ``MySQL_error``
    [common/valueMT.cbl:L505-L513 and its many siblings] - plus the stored row count
    ``WS-MYSQL-Count-Rows``. This record is those four answers.
    """

    rows: tuple[Mapping[str, object], ...]
    #: ``WS-MYSQL-Count-Rows`` - stored rows for a select, affected rows otherwise.
    row_count: int
    #: ``WS-MYSQL-Error-Number`` AS TEXT, because the field is alphanumeric and the
    #: bridge compares it as text. ``"0"`` when the statement succeeded.
    errno: str
    sql_state: str
    message: str

    @property
    def driver_reported_error(self) -> bool:
        """``if WS-MYSQL-Error-Number (1:1) not = "0"``.

        The bridge's own test, at [common/valueMT.cbl:L515, :L577, :L646, :L771, :L820,
        :L871, :L941, :L995] - eight sites, all identical.
        """
        return _pic_x(self.errno, 5)[:1] != "0"


def _mysql_1210_command(
    connection: MySQLConnectionAbstract,
    statement: _Statement,
    *,
    store_result: bool,
) -> _DriverResult:
    """``PERFORM MYSQL-1210-COMMAND`` and, for a select, ``MYSQL-1220-STORE-RESULT``.

    One statement per call, in the caller's order, through the shared execution path
    [copybooks/mysql-procedures.cpy:L164-L178]. No batching, no statement cache and no
    prefetch.

    Args:
        connection: The open connection from :func:`ba020_process_open`.
        statement: Built by this module, identifiers already quoted.
        store_result: True for a select, where the row count is the number of rows
            stored; False for a command, where it is the number affected.

    Returns:
        The row set and the four status answers. Never raises for a database-level
            failure; a failure is data here, as it is in the frozen bridge.
    """
    try:
        with execute_statement(connection, statement.bound, statement.parameters) as cur:
            if store_result:
                description = cur.description or ()
                names = tuple(str(column[0]) for column in description)
                fetched = cur.fetchall() or ()
                rows = tuple(dict(zip(names, tuple(row), strict=False)) for row in fetched)
                return _DriverResult(rows, len(rows), "0", "00000", "")
            affected = cur.rowcount
            return _DriverResult((), max(int(affected), 0), "0", "00000", "")
    except Exception as exc:  # noqa: BLE001 - the driver's failure is data here
        errno = str(getattr(exc, "errno", "") or "").strip() or "9999"
        sql_state = str(getattr(exc, "sqlstate", "") or "").strip() or "HY000"
        message = str(getattr(exc, "msg", None) or exc)
        #  ONE ERROR per failure, and TYPED ONLY. The driver's message is no
        #  longer logged: for this table it renders the statement and its bound
        #  values - the analysis code, its description and the accumulated
        #  amounts - and `sanitise_for_log` could not make that safe, because it
        #  escapes control characters rather than removing content (CWE-117 was
        #  addressed, CWE-532 was not). The errno, the SQLSTATE and the category
        #  derived from them are what an operator acts on.
        #  `message` is still RETURNED. `SQL-Msg` is a status field the frozen
        #  bridge interrogates [copybooks/mysql-procedures.cpy:L130-L137], so
        #  withholding it from the LOG must not withhold it from the CALLER;
        #  R-3 forbids the disposition changing.
        log_handler_failure(
            _LOG,
            program=BRIDGE,
            paragraph="MYSQL-1210-COMMAND",
            locator="[copybooks/mysql-procedures.cpy:L164-L178]",
            sql_err=errno,
            sql_state=sql_state,
            detail="the statement failed; the caller branches on the status "
            "returned here, exactly as the frozen bridge branches on its own "
            "one-character test",
        )
        return _DriverResult((), 0, errno, sql_state, message)


def _capture_driver_error(
    file_access: FileAccess, result: _DriverResult, statement: _Statement
) -> None:
    """The bridge's shared three-call error capture, without the foreign calls.

    NOTE THE ASYMMETRY, WHICH IS PRESERVED: ``SQL-State`` is written UNCONDITIONALLY,
    before the test, while ``SQL-Err`` and ``SQL-Msg`` are written only inside it.
    """
    logging_data = file_access.logging_data
    logging_data.sql_state = _pic_x(result.sql_state, 5)
    if not result.driver_reported_error:
        return
    status = mysql_1100_db_error(
        errno=result.errno,
        message=result.message,
        sql_state=result.sql_state,
        command=statement.text,
        we_error=int(file_access.we_error),
    )
    logging_data.sql_err = status.sql_err
    logging_data.sql_msg = status.sql_msg


def ba010_initialise(file_access: FileAccess) -> None:
    """``ba010-Initialise.`` [common/valueMT.cbl:L354].

    IT DOES NOT CLEAR THE STATUS PAIR, and that is deliberate in the source: the two
    statements that would have are present and COMMENTED OUT
    [common/valueMT.cbl:L356-L357].
    """
    logging_data = file_access.logging_data
    logging_data.sql_msg = _pic_x("", 512)
    logging_data.sql_err = _pic_x("", 5)
    logging_data.sql_state = _pic_x("", 5)
    _set_file_key(logging_data, "")
    _set_log_where(logging_data, "")


def ba020_process_open(
    file_access: FileAccess,
    *,
    system: SystemRecord,
    dal_common: AcasDalCommonData,
    transport: TransportSecurity | None = None,
) -> OpenOutcome:
    """``ba020-Process-Open.`` [common/valueMT.cbl:L401].

    On failure, ``if fs-reply not = zero / go to ba999-end`` [:L433-L434] - AAP section
    0.4.2 Class 3, a transfer to the section's exit, so a ``return``.

    Args:
        file_access: Status and logging destination; its ``RDB-Data`` group is the
            credential source the COBOL reads.
        system: The system record :func:`ba012_test_ws_rec_size_2` loaded the
            credentials from - see :data:`_SYSTEM_FOR_OPEN` for why it is needed.
        dal_common: The handler-common block ``ba999_end`` reports through.
        transport: Transport policy, passed straight through.

    Returns:
        The open outcome, so a caller can inspect it; the status is also applied to
            ``file_access``, which is where the COBOL leaves it.
    """
    global _CONNECTION
    logging_data = file_access.logging_data
    rdb: RdbData = file_access.rdb_data
    # [:L406-L429] the six `delimited by space` marshalled values are built by the
    # shared opener rather than repeated here; only their CLASS is recorded.
    #  THE ENDPOINT IS CLASSIFIED, NOT NAMED. This record used to carry the
    #  schema, the host, the user, the port and the socket path - the deployment's
    #  own identity, useful to an attacker and useless to an operator, and
    #  identical on every run only by accident (CWE-532). `transport_category`
    #  answers the one question a log has to answer about a connect target - can
    #  the credentials and the posted figures be read off the wire - with one of
    #  five fixed tokens. The password was never among the logged fields and
    #  still is not (rule V.S1).
    _LOG.debug(
        "%s/%s open: transport=%s",
        HANDLER,
        BRIDGE,
        transport_category(
            {
                "host": cobol_string_delimited_by_space(rdb.db_host),
                "unix_socket": cobol_string_delimited_by_space(rdb.db_socket),
            }
            if cobol_string_delimited_by_space(rdb.db_socket)
            else {"host": cobol_string_delimited_by_space(rdb.db_host)},
            transport,
        ),
    )
    logging_data.ws_no_paragraph = 1
    outcome = mysql_1090_exit(
        mysql_1000_open(
            system,
            ws_no_paragraph=logging_data.ws_no_paragraph,
            we_error=int(file_access.we_error),
            transport=transport,
        )
    )
    outcome.apply_to_logging_data(logging_data)
    file_access.fs_reply = int(outcome.fs_reply)
    file_access.we_error = int(outcome.we_error)
    if int(outcome.fs_reply) != FsReply.SUCCESS:
        ba999_end(file_access, dal_common=dal_common)
        return outcome
    _CONNECTION = outcome.connection
    _set_file_key(logging_data, "OPEN Value")
    _state().set_cursor_not_active()
    ba999_end(file_access, dal_common=dal_common)
    return outcome


def ba030_process_close(
    file_access: FileAccess, *, dal_common: AcasDalCommonData
) -> None:
    """``ba030-Process-Close.`` [common/valueMT.cbl:L445].

    The cursor is freed first and only ``if Cursor-Active``, so closing without an
    active cursor frees nothing - which matters because ``ba998-Free`` also writes ``ws-
    No-Paragraph`` and would otherwise overwrite the 2 written here.
    """
    global _CONNECTION
    logging_data = file_access.logging_data
    if _state().cursor_active():
        ba998_free(file_access)
    logging_data.ws_no_paragraph = 2
    _set_file_key(logging_data, "CLOSE Value")
    # [:L455] `PERFORM MYSQL-1980-CLOSE THRU MYSQL-1999-EXIT.` - both paragraphs of the
    # range, in order, because that is what THRU executes.
    mysql_1980_close(_CONNECTION)
    mysql_1999_exit()
    _CONNECTION = None
    ba999_end(file_access, dal_common=dal_common)


def ba040_process_read_next(
    file_access: FileAccess,
    value: WsValueRecord,
    connection: MySQLConnectionAbstract,
    dal_common: AcasDalCommonData,
) -> None:
    """``ba040-Process-Read-Next.`` [common/valueMT.cbl:L460].

    Rows [:L525-L532]: ``set Cursor-Active to true``, build the count into the log key,
    and ``perform ba999-End`` - a PERFORM, not a jump, whose comment is simply "log it"
    [:L531].
    """
    global _WS_TEMP_ED
    logging_data = file_access.logging_data
    state = _state()
    if state.cursor_not_active():
        where = _ba040_where()
        _set_log_where(logging_data, where.text)
        logging_data.ws_no_paragraph = 3
        statement = _select(where)
        result = _mysql_1210_command(connection, statement, store_result=True)
        state.store_result(result.rows)
        _set_file_key(logging_data, SEQUENTIAL_READ_LOW_KEY)
        if result.row_count == 0:
            _capture_driver_error(file_access, result, statement)
            file_access.fs_reply = int(FsReply.END_OF_FILE)
            # [:L521] `move 10 to WE-Error`. TEN IS NOT A We-Error VALUE.
            file_access.we_error = 10
            _set_file_key(logging_data, "No Data")
            state.set_cursor_not_active()
            ba999_end(file_access, dal_common=dal_common)
            return
        state.set_cursor_active()
        _WS_TEMP_ED = f"{result.row_count:010d}"
        _set_file_key(logging_data, f"> 0 got cnt={_WS_TEMP_ED} recs")
        # [:L531] `perform ba999-End` - a PERFORM, so the walk continues into the fetch
        # below and this paragraph's log record is written first.
        ba999_end(file_access, dal_common=dal_common)
    # [:L535] Unconditional fall-through into ba041-Reread. AAP section 0.4.2 has no
    # class for a fall-through because it is not a GO TO at all.
    ba041_reread(file_access, value, dal_common=dal_common)


def ba041_reread(
    file_access: FileAccess,
    value: WsValueRecord,
    *,
    dal_common: AcasDalCommonData,
) -> None:
    """``ba041-Reread.`` [common/valueMT.cbl:L535].

    1. ``if return-code = -1`` [:L565] - no more data. ``move 10 to fs-Reply WE-Error``,
    ``move "EOF" to WS-File-Key``, free the cursor, exit. 2.
    """
    logging_data = file_access.logging_data
    state = _state()
    _set_log_where(logging_data, "")
    logging_data.ws_no_paragraph = 4
    row = state.fetch_record()
    if row is None:
        # [:L566] `move 10 to fs-Reply WE-Error` - ONE statement writing BOTH fields, so
        # the We-Error 10 here is not even a separate decision.
        file_access.fs_reply = int(FsReply.END_OF_FILE)
        file_access.we_error = 10
        _set_file_key(logging_data, "EOF")
        state.set_cursor_not_active()
        ba999_end(file_access, dal_common=dal_common)
        return
    # 2. [:L572-L587].
    if state.count_rows == 0:
        result = _DriverResult((), 0, "0", "00000", "")
        _capture_driver_error(file_access, result, _select(_ba040_where()))
        if result.driver_reported_error:
            file_access.fs_reply = int(FsReply.END_OF_FILE)
            file_access.we_error = 10
            bb100_unload_hvs(TdValueanalRec(), value)
            _set_file_key(logging_data, "EOF2")
        # [:L585-L586] OUTSIDE the inner test - so a clean zero count writes nothing and
        # still returns.
        state.set_cursor_not_active()
        ba999_end(file_access, dal_common=dal_common)
        return
    if int(file_access.fs_reply) == FsReply.END_OF_FILE:
        state.set_cursor_not_active()
        _set_file_key(logging_data, "EOF3")
        ba999_end(file_access, dal_common=dal_common)
        return
    host = _row_to_host(row)
    bb100_unload_hvs(host, value)
    _set_file_key(logging_data, host.hv_va_code)
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    ba999_end(file_access, dal_common=dal_common)


def _row_to_host(row: Mapping[str, object]) -> TdValueanalRec:
    """Fill the host-variable group from a fetched row.

    The columns are read by NAME, from :data:`COLUMNS`, in ordinal order, which is the
    order ``SELECT *`` returns them and the order the fetch call lists them.

    Raises:
        TypeError: If a numeric column arrives as an inexact type. See
            :func:`_require_exact_numeric`.
    """
    host = TdValueanalRec()
    host.initialize()
    for binding in COLUMNS:
        raw = row.get(binding.name)
        if binding.storage in {"DECIMAL", "INT"} and raw is not None:
            _require_exact_numeric(raw, f"{binding.name} (fetched column)")
        if binding.storage == "DECIMAL":
            scale = Decimal(1).scaleb(-binding.host_scale)
            fitted: object = Decimal(str(raw if raw is not None else "0")).quantize(
                scale, rounding=ROUND_DOWN
            )
        elif binding.storage == "INT":
            fitted = _hv_unsigned_integer(int(raw or 0), binding)
        else:
            fitted = _pic_x(raw, binding.host_length)
        setattr(host, binding.host_attribute, fitted)
    return host


def ba050_process_read_indexed(
    file_access: FileAccess,
    value: WsValueRecord,
    connection: MySQLConnectionAbstract,
    dal_common: AcasDalCommonData,
) -> None:
    """``ba050-Process-Read-Indexed.`` [common/valueMT.cbl:L600].

    * ``if WS-MYSQL-Count-Rows = zero`` [:L641] - ``move 23 to fs-Reply`` [:L642] with
    the comment "could also be 21 or 14", ``move zero to WE-Error`` [:L643], ``go to
    ba998-Free`` [:L644]. * ``move 6 to ws-No-Paragraph`` [:L646], fetch [:L652-L666].
    """
    logging_data = file_access.logging_data
    state = _state()
    key_value = _flat_key_of(value)
    where = _ba050_where(key_value)
    _set_log_where(logging_data, where.text)
    logging_data.ws_no_paragraph = 5
    statement = _select(where)
    result = _mysql_1210_command(connection, statement, store_result=True)
    state.store_result(result.rows)
    if result.row_count == 0:
        # [:L642] 23, with the source's own "could also be 21 or 14" beside it, and
        # [:L643] zero to WE-Error - so nothing distinguishes this from success except
        # FS-Reply.
        file_access.fs_reply = int(FsReply.KEY_NOT_FOUND)
        file_access.we_error = int(WeError.SUCCESS)
        # [:L644] `go to ba998-Free` - AAP section 0.4.2 Class 4.
        ba998_free(file_access)
        ba999_end(file_access, dal_common=dal_common)
        return
    logging_data.ws_no_paragraph = 6
    row = state.fetch_record()
    # [:L668-L688] the second, unreachable row-count test. The count cannot have changed
    # since [:L641], so `not > zero` cannot be true. Both arms preserved.
    if state.count_rows <= 0:  # pragma: no cover - unreachable in the frozen source
        _capture_driver_error(file_access, result, statement)
        if result.driver_reported_error:
            file_access.fs_reply = int(FsReply.KEY_NOT_FOUND)
            file_access.we_error = int(WeError.UNKNOWN_UNEXPECTED)
            _set_file_key(logging_data, "")
        else:
            file_access.fs_reply = int(FsReply.KEY_NOT_FOUND)
            file_access.we_error = int(WeError.READ_INDEXED_UNEXPECTED)
            logging_data.sql_err = _pic_x("0", 5)
            logging_data.sql_msg = _pic_x("", 512)
            _set_file_key(logging_data, "")
        ba998_free(file_access)
        ba999_end(file_access, dal_common=dal_common)
        return
    host = _row_to_host(row) if row is not None else TdValueanalRec()
    bb100_unload_hvs(host, value)
    # [:L690] then [:L691] - N-filekey-deadstore. The first store is overwritten by the
    # second, which reads a field this paragraph never wrote.
    _set_file_key(logging_data, host.hv_va_code)
    _set_file_key(logging_data, _WS_TEMP_ED)
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    ba998_free(file_access)
    ba999_end(file_access, dal_common=dal_common)


def ba060_process_start(
    file_access: FileAccess,
    value: WsValueRecord,
    connection: MySQLConnectionAbstract,
    dal_common: AcasDalCommonData,
) -> None:
    """``ba060-Process-Start.`` [common/valueMT.cbl:L695].

    1. ``if access-type < 5 or > 8`` [:L699] - the bridge-level guard, with the source's
    own note "not using not < or not >".
    """
    global _WS_TEMP_ED
    logging_data = file_access.logging_data
    state = _state()
    access_type = int(file_access.access_type)
    if not start_access_type_is_valid(access_type):
        file_access.fs_reply = int(FsReply.ERROR)
        file_access.we_error = int(WeError.ACCESS_TYPE_WRONG)
        ba999_end(file_access, dal_common=dal_common)
        return
    if state.cursor_active():
        ba998_free(file_access)
    # 3. [:L719-L732].
    relation = MostRelation(
        ACCESS_TYPE_TO_RELATION.get(AccessType(access_type), "   ")
    )
    state.most_relation = relation.padded
    key_value = _flat_key_of(value)
    where = _ba060_where(relation, key_value)
    _set_log_where(logging_data, where.text)
    # 5. [:L751] - overwritten on the success path at [:L797], preserved in order.
    _set_file_key(logging_data, key_value)
    logging_data.ws_no_paragraph = 8
    statement = _select(where)
    result = _mysql_1210_command(connection, statement, store_result=True)
    state.store_result(result.rows)
    state.position_at(key_value)
    if result.row_count != 0:
        state.set_cursor_active()
    if result.row_count == 0:
        _capture_driver_error(file_access, result, statement)
        if result.driver_reported_error:
            file_access.fs_reply = int(FsReply.INVALID_KEY_ON_START)
            file_access.we_error = int(WeError.SUCCESS)
            ba999_end(file_access, dal_common=dal_common)
            return
        # N-start-nostatus - no status write on this path. Deliberate: see above.
    else:
        file_access.fs_reply = int(FsReply.SUCCESS)
        file_access.we_error = int(WeError.SUCCESS)
        _WS_TEMP_ED = f"{result.row_count:010d}"
        _set_file_key(
            logging_data,
            f"{relation.padded}{key_value} got ={_WS_TEMP_ED} recs",
        )
    ba999_end(file_access, dal_common=dal_common)


def ba070_process_write(
    file_access: FileAccess,
    value: WsValueRecord,
    connection: MySQLConnectionAbstract,
    dal_common: AcasDalCommonData,
) -> None:
    """``ba070-Process-Write.`` [common/valueMT.cbl:L809].

    ⭐ ``We-Error`` IS NEVER WRITTEN ON THE FAILURE PATH. It stays at the zero from
    [:L812], so a failed write reports ``FS-Reply`` 99 with ``We-Error`` 0 - the
    handler's ``994``/``995`` pattern is absent here. Preserved.
    """
    logging_data = file_access.logging_data
    host = bb000_hv_load(value)
    _set_file_key(logging_data, _flat_key_of(value))
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    logging_data.sql_state = _pic_x("0", 5)
    logging_data.sql_msg = _pic_x("", 512)
    logging_data.sql_err = _pic_x("0", 5)
    logging_data.ws_no_paragraph = 10
    statement = bb200_insert(host)
    result = _mysql_1210_command(connection, statement, store_result=False)
    if result.row_count != 1:
        _capture_driver_error(file_access, result, statement)
        if result.driver_reported_error:
            if is_duplicate_key_bridge_level(
                logging_data.sql_err, logging_data.sql_state
            ):
                file_access.fs_reply = int(FsReply.DUPLICATE_KEY)
            else:
                file_access.fs_reply = int(FsReply.ERROR)
    ba999_end(file_access, dal_common=dal_common)


def ba080_process_delete(
    file_access: FileAccess,
    value: WsValueRecord,
    connection: MySQLConnectionAbstract,
    dal_common: AcasDalCommonData,
) -> None:
    """``ba080-Process-Delete.`` [common/valueMT.cbl:L836].

    ⭐ THE DELETE CARRIES NO SEMICOLON. [:L869] terminates with ``X"00"`` alone, where
    every ``SELECT``, ``INSERT`` and ``UPDATE`` in this bridge appends ``";"`` first
    [:L499, :L635, :L767, :L1245, :L1398].
    """
    logging_data = file_access.logging_data
    key_value = _flat_key_of(value)
    where = _ba080_where(key_value)
    _set_file_key(logging_data, key_value)
    _set_log_where(logging_data, where.text)
    logging_data.ws_no_paragraph = 13
    statement = _delete(where)
    result = _mysql_1210_command(connection, statement, store_result=False)
    if result.row_count != 1:
        _capture_driver_error(file_access, result, statement)
        if result.driver_reported_error:
            file_access.fs_reply = int(FsReply.ERROR)
            file_access.we_error = int(WeError.DELETE_SQLSTATE_NOT_00000)
        ba999_end(file_access, dal_common=dal_common)
        return
    logging_data.sql_msg = _pic_x("", 512)
    logging_data.sql_err = _pic_x("0", 5)
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    ba999_end(file_access, dal_common=dal_common)


def ba085_process_delete_all(
    file_access: FileAccess,
    value: WsValueRecord,
    connection: MySQLConnectionAbstract,
    dal_common: AcasDalCommonData,
) -> None:
    """``ba085-Process-Delete-All.`` [common/valueMT.cbl:L891].

    ⭐ N-deleteall-zzz. [:L913] ``move "ZZZ" to WS-VA-Code. *> as its the last rec``
    OVERWRITES THE CALLER'S KEY FIELD IN PLACE, and the clause is then built from that
    mutated record with ``<`` [:L921-L929], giving ``` `VA-CODE`<"ZZZ" ```.
    """
    logging_data = file_access.logging_data
    # [:L913] the in-place mutation of the caller's record.
    value.va_code.va_system = "Z"
    value.va_code.va_group.va_first = "Z"
    value.va_code.va_group.va_second = "Z"
    key_value = _flat_key_of(value)
    where = _ba085_where(key_value)
    _set_file_key(logging_data, f"Deleting back from {key_value}")
    _set_log_where(logging_data, where.text)
    logging_data.ws_no_paragraph = 15
    statement = _delete(where)
    result = _mysql_1210_command(connection, statement, store_result=False)
    if result.row_count == 0:
        _capture_driver_error(file_access, result, statement)
        if result.driver_reported_error:
            file_access.fs_reply = int(FsReply.ERROR)
            file_access.we_error = int(WeError.DELETE_SQLSTATE_NOT_00000)
        ba999_end(file_access, dal_common=dal_common)
        return
    logging_data.sql_msg = _pic_x("", 512)
    logging_data.sql_err = _pic_x("0", 5)
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    ba999_end(file_access, dal_common=dal_common)


def ba090_process_rewrite(
    file_access: FileAccess,
    value: WsValueRecord,
    connection: MySQLConnectionAbstract,
    dal_common: AcasDalCommonData,
) -> None:
    """``ba090-Process-Rewrite.`` [common/valueMT.cbl:L972].

    [:L974-L993]: ``perform bb000-HV-Load`` - so the sign loss happens on a rewrite
    exactly as on a write; ``move 17 to ws-No-Paragraph``; ``move WS-VA-Code to WS-File-
    Key``; the ``=``-form clause; the log where; ``perform bb300-Update``.
    """
    logging_data = file_access.logging_data
    host = bb000_hv_load(value)
    logging_data.ws_no_paragraph = 17
    key_value = _flat_key_of(value)
    _set_file_key(logging_data, key_value)
    where = _ba090_where(key_value)
    _set_log_where(logging_data, where.text)
    statement = bb300_update(host, where)
    result = _mysql_1210_command(connection, statement, store_result=False)
    if result.row_count != 1:
        _capture_driver_error(file_access, result, statement)
        if result.driver_reported_error:
            file_access.fs_reply = int(FsReply.ERROR)
            file_access.we_error = int(WeError.REWRITE_SQLSTATE_NOT_00000)
        ba999_end(file_access, dal_common=dal_common)
        return
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    logging_data.sql_state = _pic_x("0", 5)
    logging_data.sql_err = _pic_x("0", 5)
    logging_data.sql_msg = _pic_x("", 512)
    ba999_end(file_access, dal_common=dal_common)


def ba100_bad_function(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``ba100-Bad-Function.`` [common/valueMT.cbl:L1017].

    Reached from the bridge's ``when other`` for a ``File-Function`` outside 1..9 and 6.
    """
    file_access.we_error = int(WeError.UNKNOWN_UNEXPECTED)
    file_access.fs_reply = int(FsReply.ERROR)
    ba999_end(file_access, dal_common=dal_common)


def ba998_free(file_access: FileAccess) -> None:
    """``ba998-Free.`` [common/valueMT.cbl:L1029].

    That distinction is why this function does not call ``ba999_end`` itself. Each
    caller reproduces its own arrival mode.
    """
    logging_data = file_access.logging_data
    logging_data.ws_no_paragraph = 20
    _state().free_result()
    _state().set_cursor_not_active()


def ba999_end(
    file_access: FileAccess, *, dal_common: AcasDalCommonData | None
) -> None:
    """``ba999-end.`` [common/valueMT.cbl:L1041] and ``ba999-exit.`` [:L1048].

    ``Testing-1`` is the ``88``-level ``sw-testing value 1``.

    Args:
        file_access: The status the log record describes.
        dal_common: The testing switch.
    """
    if dal_common is not None and dal_common.sw_testing == 1:
        ca_process_logs(file_access, dal_common)


def value_mt(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    value: WsValueRecord,
    *,
    system: SystemRecord | None = None,
    transport: TransportSecurity | None = None,
) -> None:
    """``call "valueMT"`` - THE BRIDGE'S OWN THREE-PARAMETER ENTRY POINT.

    THREE PARAMETERS, IN THIS ORDER. Both signatures are published because R-5 requires
    it: a reader following the handler finds :func:`dispatch` with its five parameters,
    and a reader following the bridge finds this with its three.

    Args:
        file_access: Status, logging and credentials - the same object throughout,
            because COBOL passes it by reference and the caller reads the status out of
            it afterwards.
        dal_common: The testing switch that gates every log write.
        value: The record, read for a write or rewrite and written for a read.
        system: Needed only by the open verb, and only because
            :func:`ba020_process_open` delegates to the shared connection module.
            Defaults to the record :func:`ba012_test_ws_rec_size_2` last saw.
        transport: Transport policy for the open verb.

    Raises:
        AcasFileHandlerFatalError: If a verb other than open is reached with no
            connection.
    """
    ba010_initialise(file_access)
    function = int(file_access.file_function)
    if function == FileFunction.OPEN:
        ba020_process_open(
            file_access,
            system=_system_for_open(system),
            dal_common=dal_common,
            transport=transport,
        )
        return
    if function == FileFunction.CLOSE:
        ba030_process_close(file_access, dal_common=dal_common)
        return
    connection = _require_connection(file_access, function)
    if function == FileFunction.READ_NEXT:
        ba040_process_read_next(file_access, value, connection, dal_common)
        return
    if function == FileFunction.READ_INDEXED:
        ba050_process_read_indexed(file_access, value, connection, dal_common)
        return
    if function == FileFunction.WRITE:
        ba070_process_write(file_access, value, connection, dal_common)
        return
    if function == FileFunction.DELETE_ALL:
        ba085_process_delete_all(file_access, value, connection, dal_common)
        return
    if function == FileFunction.RE_WRITE:
        ba090_process_rewrite(file_access, value, connection, dal_common)
        return
    if function == FileFunction.DELETE:
        ba080_process_delete(file_access, value, connection, dal_common)
        return
    if function == FileFunction.START:
        ba060_process_start(file_access, value, connection, dal_common)
        return
    ba100_bad_function(file_access, dal_common)


def _system_for_open(system: SystemRecord | None) -> SystemRecord:
    """The system record the open verb needs, and why it is not a linkage parameter.

    ``ba020-Process-Open`` reads its credentials from ``File-Access``'s ``RDB-Data``
    group [common/valueMT.cbl:L406-L429], which :func:`ba012_test_ws_rec_size_2` filled
    from the system record [common/acas013.cbl:L638-L643].
    """
    if system is not None:
        return system
    if _SYSTEM_FOR_OPEN is not None:
        return _SYSTEM_FOR_OPEN
    raise AcasFileHandlerFatalError(
        int(FsReply.ERROR),
        WeError.RDB_INIT_ERROR,
        operation="Open",
        table=TABLE_NAME,
    )


def _require_connection(
    file_access: FileAccess, function: int
) -> MySQLConnectionAbstract:
    """The open connection, or a fatal status if the caller never opened.

    The frozen bridge keeps the client-library handle in working storage and never
    checks it: a verb issued before an open passes a null handle to the library, whose
    result is undefined.
    """
    if _CONNECTION is None:
        file_access.fs_reply = int(FsReply.ERROR)
        file_access.we_error = int(WeError.RDB_INIT_ERROR)
        raise AcasFileHandlerFatalError(
            int(FsReply.ERROR),
            WeError.RDB_INIT_ERROR,
            operation=f"File-Function {function}",
            table=TABLE_NAME,
        )
    return _CONNECTION


# The handler: acas013, one function per paragraph [common/acas013.cbl] `aa-Process-
# Flat-File Section.` [common/acas013.cbl:L292] - note the capital S, against the lower-
# case s of `ba-Process-RDBMS section.` [:L588].


def _indexed_file_verb(verb: str, file_access: FileAccess) -> IndexedFilePathNotMigrated:
    """Build the boundary report for an indexed-file verb.

    Not raised here - returned, so that each paragraph raises at the line its own
    ``READ``/``WRITE``/``START`` occupies and the traceback points at the paragraph
    rather than at a shared helper.
    """
    logging_data = file_access.logging_data
    return IndexedFilePathNotMigrated(
        f"{HANDLER}: {verb} on the indexed file Value-File is outside the migrated "
        f"scope. The relational path through {BRIDGE} implements this verb; reach it "
        f"by setting FS-RDBMS-Used in the system record, which is what "
        f"[common/acas013.cbl:L321-L325] tests. "
        f"WS-No-Paragraph={logging_data.ws_no_paragraph}."
    )
    # `WS-File-Key` is deliberately NOT interpolated into the message: for this
    # table it is the analysis code, a business key, and an exception message can
    # be logged by whatever catches it (CWE-532). The paragraph number is enough
    # to name the verb that was refused.


def aa010_main(
    system: SystemRecord,
    value: WsValueRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None = None,
) -> None:
    """``aa010-main.`` [common/acas013.cbl:L294] - the handler's mainline.

    ⭐ THIS IS THE MIGRATED PATH AND IT RETURNS HERE. Everything after [:L325] is
    indexed-file work that a relational installation never reaches.

    Args:
        system: ``System-Record`` - parameter 1, the credential source and the store
            selector.
        value: ``WS-Value-Record`` - parameter 2, read or written in place.
        file_access: ``File-Access`` - parameter 3, status and logging.
        file_defs: ``File-Defs`` - parameter 4. Carries the indexed file's path, which
            only the unmigrated flat path uses.
        dal_common: ``ACAS-DAL-Common-data`` - parameter 5, the testing switch.
        transport: Transport policy for the open verb. Not a COBOL parameter; see
            :func:`dispatch`.

    Raises:
        IndexedFilePathNotMigrated: If the system record selects the indexed store.
    """
    logging_data = file_access.logging_data
    # 1. [:L298-L299] the log identity. Written on EVERY call, before anything else,
    # including before the key guard - so even a rejected call is attributed.
    logging_data.ws_log_system = WS_LOG_SYSTEM
    logging_data.ws_log_file_no = WS_LOG_FILE_NO_COBOL
    if _aa010_key_guard(file_access):
        aa999_main_exit(file_access, dal_common)
        return
    if not _fs_cobol_files_used(system):
        source = system.system_data_block.rdbms_flat_statuses
        target = file_access.fa_rdbms_flat_statuses
        target.fa_file_system_used = source.file_system_used
        target.fa_file_duplicates_in_use = source.file_duplicates_in_use
        ba_process_rdbms(
            system, value, file_access, dal_common, transport=transport
        )
        aa_main_exit(file_access)
        return
    if ba012_test_ws_rec_size_2(system, file_access, dal_common):
        ba_rdbms_exit(file_access)
        return
    logging_data.sql_err = _pic_x("", 5)
    logging_data.sql_msg = _pic_x("", 512)
    logging_data.sql_state = _pic_x("", 5)
    function = int(file_access.file_function)
    if function == FileFunction.OPEN:
        aa020_process_open(file_access, file_defs, dal_common)
        return
    if function == FileFunction.CLOSE:
        aa030_process_close(file_access, dal_common)
        return
    if function == FileFunction.READ_NEXT:
        aa040_process_read_next(file_access, value, dal_common)
        return
    if function == FileFunction.READ_INDEXED:
        aa050_process_read_indexed(file_access, value, dal_common)
        return
    if function == FileFunction.WRITE:
        aa070_process_write(file_access, value, dal_common)
        return
    if function == FileFunction.RE_WRITE:
        aa090_process_rewrite(file_access, value, dal_common)
        return
    if function == FileFunction.DELETE:
        aa080_process_delete(file_access, value, dal_common)
        return
    if function == FileFunction.START:
        aa060_process_start(file_access, value, dal_common)
        return
    aa100_bad_function(file_access, dal_common)
    # [:L365] `go to aa100-Bad-Function.` unconditionally - "Should never get here but
    # in case :(".
    return


def _aa010_key_guard(file_access: FileAccess) -> bool:
    """The key guard of ``aa010-main`` [common/acas013.cbl:L303-L317], verbatim::

    THREE FUNCTIONS ARE GUARDED, IN TWO GROUPS. Read-indexed (4) and start (9) share one
    arm and yield ``998``; delete (8) has its own and yields ``996``.

    Returns:
        True if the call was rejected and the caller must transfer to ``aa999-main-
            exit``; False to continue. The status is already written.
    """
    function = int(file_access.file_function)
    key_no = int(file_access.logging_data.file_key_no)
    if function in (FileFunction.READ_INDEXED, FileFunction.START):
        if key_no != 1:
            file_access.we_error = int(WeError.FILE_KEY_NO_OUT_OF_RANGE)
            file_access.fs_reply = int(FsReply.ERROR)
            return True
        return False
    if function == FileFunction.DELETE:
        if key_no != 1:
            file_access.we_error = int(WeError.DELETE_KEY_OUT_OF_RANGE)
            file_access.fs_reply = int(FsReply.ERROR)
            return True
    return False


def _fs_cobol_files_used(system: SystemRecord) -> bool:
    """``FS-Cobol-Files-Used`` - the ``88``-level tested at [common/acas013.cbl:L321].

    Written out here rather than imported: the ``88``-level predicates live in
    ``acas_posting/cobol/condition_names``, which AAP section 0.4.3 excludes from this
    layer's imports.
    """
    return int(system.system_data_block.rdbms_flat_statuses.file_system_used) == 0


def aa020_process_open(
    file_access: FileAccess, file_defs: FileDefs, dal_common: AcasDalCommonData
) -> None:
    """``aa020-Process-Open.`` [common/acas013.cbl:L367].

    * ``fn-input`` [:L370] - ``open input``; on failure ``move 35 to fs-Reply`` [:L373]
    and exit.

    Raises:
        IndexedFilePathNotMigrated: For every access type but extend, which is refused
            before any verb is issued.
    """
    logging_data = file_access.logging_data
    _set_file_key(logging_data, "")
    logging_data.ws_no_paragraph = 201
    access_type = int(file_access.access_type)
    if access_type == AccessType.EXTEND:
        file_access.we_error = int(WeError.ACCESS_TYPE_WRONG)
        file_access.fs_reply = int(FsReply.ERROR)
        aa999_main_exit(file_access, dal_common)
        return
    # [:L370-L388] every other arm issues an indexed-file OPEN. The path it would
    # open comes from File-Defs [copybooks/wsnames.cob], which is why parameter 4
    # is still threaded this far even though nothing here reads it.
    #  NO RECORD HERE. The frozen arms display nothing - each is an `open`, a
    #  status test and a `go to` - so a record would be invented (R-4), and the
    #  one it replaced named `File-13`, an absolute filesystem path from the
    #  deployment's own configuration (CWE-532). The refusal is already reported
    #  to the caller, by the exception raised on the next line.
    raise _indexed_file_verb(f"OPEN (access type {access_type})", file_access)


def aa030_process_close(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa030-Process-Close.`` [common/acas013.cbl:L406].

    1. ``perform aa999-main-exit`` [:L413] runs ``if Testing-1 perform Ca-Process-Logs``
    - a log record IF the switch is set. 2. ``perform Ca-Process-Logs`` [:L416] runs it
    AGAIN, UNCONDITIONALLY. The switch is not consulted.

    Raises:
        IndexedFilePathNotMigrated: At the ``close`` of [:L409].
    """
    logging_data = file_access.logging_data
    logging_data.ws_no_paragraph = 202
    _set_file_key(logging_data, "")
    raise _indexed_file_verb("CLOSE", file_access)


def aa040_process_read_next(
    file_access: FileAccess, value: WsValueRecord, dal_common: AcasDalCommonData
) -> None:
    """``aa040-Process-Read-Next.`` [common/acas013.cbl:L419].

    ⭐ N-stopliteral. ``stop "Cobol File EOF"`` IS AN OPERATOR PAUSE, not a program
    termination: the obsolete ``STOP`` literal form displays its literal and suspends
    until the operator resumes.

    Raises:
        IndexedFilePathNotMigrated: At the ``read`` of [:L435], or at the end-of-file
            gate, which is equally indexed-file state.
    """
    logging_data = file_access.logging_data
    logging_data.ws_no_paragraph = 203
    raise _indexed_file_verb("READ NEXT", file_access)


def aa045_eval_keys(file_access: FileAccess, value: WsValueRecord) -> None:
    """``aa045-Eval-Keys.`` [common/acas013.cbl:L452].

    Preceded by the maintainer's own doubt [:L450]: "The next block will never get
    executed unless performed so is it needed ?" - which is accurate.
    """
    logging_data = file_access.logging_data
    function = int(file_access.file_function)
    key_no = int(file_access.logging_data.file_key_no)
    if function in (
        FileFunction.READ_INDEXED,
        FileFunction.WRITE,
        FileFunction.RE_WRITE,
        FileFunction.DELETE,
        FileFunction.START,
    ):
        if key_no == 1:
            _set_file_key(logging_data, _flat_key_of(value))
        else:
            _set_file_key(logging_data, "")
        return
    _set_file_key(logging_data, "")


def aa050_process_read_indexed(
    file_access: FileAccess, value: WsValueRecord, dal_common: AcasDalCommonData
) -> None:
    """``aa050-Process-Read-Indexed.`` [common/acas013.cbl:L470].

    ⭐ ``move 21 to we-error fs-reply`` puts 21 IN BOTH FIELDS. Twenty-one is an ``FS-
    Reply`` value.

    Raises:
        IndexedFilePathNotMigrated: At the ``read`` of [:L478].
    """
    logging_data = file_access.logging_data
    logging_data.ws_no_paragraph = 204
    aa045_eval_keys(file_access, value)
    key_no = int(logging_data.file_key_no)
    if key_no != 1:
        file_access.we_error = int(WeError.FILE_KEY_NO_OUT_OF_RANGE)
        file_access.fs_reply = int(FsReply.ERROR)
        aa999_main_exit(file_access, dal_common)
        return
    raise _indexed_file_verb("READ INDEXED", file_access)


def aa060_process_start(
    file_access: FileAccess, value: WsValueRecord, dal_common: AcasDalCommonData
) -> None:
    """``aa060-Process-Start.`` [common/acas013.cbl:L492].

    Three separate defects in four lines, all reproduced.

    Raises:
        IndexedFilePathNotMigrated: At the first ``start`` of [:L510].
    """
    logging_data = file_access.logging_data
    logging_data.ws_no_paragraph = 205
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    access_type = int(file_access.access_type)
    # [:L501-L504] the guard. Note what is NOT here: no FS-Reply write.
    if not start_access_type_is_valid(access_type):
        file_access.we_error = int(WeError.FILE_KEY_NO_OUT_OF_RANGE)
        aa999_main_exit(file_access, dal_common)
        return
    key_no = int(logging_data.file_key_no)
    if key_no != 1:
        aa999_main_exit(file_access, dal_common)
        return
    relation = ACCESS_TYPE_TO_RELATION.get(AccessType(access_type), "   ")
    raise _indexed_file_verb(f"START (key {relation.strip()})", file_access)


def aa070_process_write(
    file_access: FileAccess, value: WsValueRecord, dal_common: AcasDalCommonData
) -> None:
    """``aa070-Process-Write.`` [common/acas013.cbl:L538].

    ⭐ N-writenokey. IT NEVER PERFORMS ``aa045-Eval-Keys``, even though that paragraph
    lists ``when 5 *> fn-write`` among its arms [:L455].

    Raises:
        IndexedFilePathNotMigrated: At the ``write`` of [:L543].
    """
    logging_data = file_access.logging_data
    logging_data.ws_no_paragraph = 206
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    raise _indexed_file_verb("WRITE", file_access)


def aa080_process_delete(
    file_access: FileAccess, value: WsValueRecord, dal_common: AcasDalCommonData
) -> None:
    """``aa080-Process-Delete.`` [common/acas013.cbl:L548].

    Raises:
        IndexedFilePathNotMigrated: At the ``delete`` of [:L553].
    """
    logging_data = file_access.logging_data
    logging_data.ws_no_paragraph = 207
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    raise _indexed_file_verb("DELETE", file_access)


def aa090_process_rewrite(
    file_access: FileAccess, value: WsValueRecord, dal_common: AcasDalCommonData
) -> None:
    """``aa090-Process-Rewrite.`` [common/acas013.cbl:L558].

    ⭐ [:L566]'s ``end-rewrite`` CARRIES NO PERIOD, unlike the ``end-write.`` of [:L545]
    and the ``end-delete.`` of [:L555].

    Raises:
        IndexedFilePathNotMigrated: At the ``rewrite`` of [:L564].
    """
    logging_data = file_access.logging_data
    logging_data.ws_no_paragraph = 208
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    raise _indexed_file_verb("REWRITE", file_access)


def aa100_bad_function(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa100-Bad-Function.`` [common/acas013.cbl:L569].

    ⭐ IT ENDS WITHOUT A ``GO TO``, so control FALLS THROUGH into ``aa999-main-exit``
    [:L576] and the log record is written. Reproduced as an explicit call, because the
    fall-through is the only way the log happens.
    """
    file_access.we_error = int(WeError.NOT_USED)
    file_access.fs_reply = int(FsReply.ERROR)
    aa999_main_exit(file_access, dal_common)


def aa999_main_exit(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa999-main-exit.`` [common/acas013.cbl:L576].

    Identical in form to the bridge's :func:`ba999_end`, and reached from every ``go to
    aa999-main-exit`` in the flat-file section - eleven sites - plus the fall-through
    from :func:`aa100_bad_function` and the single ``perform`` from
    :func:`aa030_process_close`.
    """
    if dal_common is not None and dal_common.sw_testing == 1:
        ca_process_logs(file_access, dal_common)


def aa_main_exit(file_access: FileAccess) -> None:
    """``aa-main-exit.`` [common/acas013.cbl:L581].

    Reproduced as a function because R-5 requires one function per paragraph and because
    an empty paragraph is a fact about the program.
    """
    aa_exit(file_access)


def aa_exit(file_access: FileAccess) -> None:
    """``aa-Exit.`` [common/acas013.cbl:L585].

    ``exit program.`` [:L586] - the return to the caller, with ``File-Access``
    carrying the status. Nothing is cleared on the way out; whatever the last
    paragraph wrote is what the caller reads.

     NO RECORD HERE. ``exit program.`` is one statement and it displays
    nothing, so a per-return trace was invented (R-4) - and it would have been the
    highest-volume record in the module, one per handler call, drowning the
    failures an operator is watching for. The status pair it announced is the
    caller's to read from ``File-Access``, which is where the COBOL leaves it.
    """
    return


def ba_process_rdbms(
    system: SystemRecord,
    value: WsValueRecord,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None = None,
) -> None:
    """``ba-Process-RDBMS section.`` [common/acas013.cbl:L588] - THE MIGRATED PATH.

    Its header states the intent [:L591-L594]: "Here we call the relevent RDBMS module
    for this table / which will include processing any other joined tables as needed".
    """
    ba010_test_ws_rec_size(file_access)
    if ba012_test_ws_rec_size_2(system, file_access, dal_common):
        ba_rdbms_exit(file_access)
        return
    ba015_test_ends(
        file_access, value, dal_common, system=system, transport=transport
    )
    ba_rdbms_exit(file_access)


def ba010_test_ws_rec_size(file_access: FileAccess) -> None:
    """``ba010-Test-WS-Rec-Size.`` [common/acas013.cbl:L596].

    ⭐⭐ N-log, THE MECHANISM. ``13`` was written at [:L299] for every call; ``23`` is
    written here, on the relational path only, because the flat path performs ``ba012``
    directly at [:L329] and jumps over this paragraph entirely.
    """
    file_access.logging_data.ws_log_file_no = WS_LOG_FILE_NO_RDB


def ba012_test_ws_rec_size_2(
    system: SystemRecord, file_access: FileAccess, dal_common: AcasDalCommonData
) -> bool:
    """``ba012-Test-WS-Rec-Size-2.`` [common/acas013.cbl:L604].

    First the size test [:L607-L616].

    Returns:
        True if the 901 path was taken and the caller must transfer to ``ba-rdbms-
            exit``; False to continue into ``ba015-Test-Ends``.
    """
    global _RECORD_SIZE_TESTED, _SYSTEM_FOR_OPEN
    if _RECORD_SIZE_TESTED:
        return False
    _RECORD_SIZE_TESTED = True
    a = _WS_VALUE_RECORD_LENGTH
    b = _VALUE_RECORD_LENGTH
    # [:L613-L616] `if A < B` -> 901/99, under the source's own aside "COULD LET caller
    # module deal with these errors !!!!!!!".
    if a < b:  # pragma: no cover - 66 < 66 is false; see N-recsize
        file_access.we_error = int(WeError.RECORD_SIZE_MISMATCH)
        file_access.fs_reply = int(FsReply.ERROR)
    # [:L617-L632] `if WE-Error = 901`.
    if int(file_access.we_error) == WeError.RECORD_SIZE_MISMATCH:
        display_blk = _pic_x(f"{_AC902}{a:04d} < Value-Rec = {b:04d}", 75)
        # [:L625-L626] two `display ... with erase eol` at 2301 and 2401.
        _LOG.error("%s: %s", PROG_NAME, display_blk.rstrip())
        #  THE SECOND DISPLAY IS NOT A RECORD. [:L626] displays `AC901`,
        #  declared at [:L263] - an instruction to
        #  the operator standing at the terminal, paired with the `accept` on the
        #  next frozen line. AAP section 0.3.4 drops an acknowledgement pause
        #  entirely, and quoting its text in a log line is still emitting it. The
        #  substantive half, AC902 above, carries the whole diagnostic; the
        #  control transfer at [:L631] is preserved as this function's return.
        # [:L627-L629] `if Testing-1 perform Ca-Process-Logs` - and see the
        # docstring on why this contradicts [:L676]'s own comment.
        if dal_common is not None and dal_common.sw_testing == 1:
            ca_process_logs(file_access, dal_common)
        # [:L630] `accept Accept-Reply at 2433` - DROPPED.
        return True
    # [:L638-L643] the six credential moves - schema, user, password, port, host, socket
    # - delegated to the shared loader so that all twenty handler modules share one
    # reading of "hopefully once is enough :)" [:L636].
    load_rdb_data_once(system)
    _SYSTEM_FOR_OPEN = system
    return False


def ba015_test_ends(
    file_access: FileAccess,
    value: WsValueRecord,
    dal_common: AcasDalCommonData,
    *,
    system: SystemRecord | None = None,
    transport: TransportSecurity | None = None,
) -> None:
    """``ba015-Test-Ends.`` [common/acas013.cbl:L646] - THE OPEN-OUTPUT SPECIAL CASE.

    Its comment block records a design intention never carried out [:L649-L651]: "HERE
    we need a CDF [Compiler Directive] to select the correct DAL based on the pre SQL
    compiler e.g., JCs or dbpre or Prima conversions <<<< ?
    """
    is_open = int(file_access.file_function) == FileFunction.OPEN
    is_output = int(file_access.access_type) == AccessType.OUTPUT
    if is_open and is_output:
        ba020_call(
            file_access, value, dal_common, system=system, transport=transport
        )
        file_access.file_function = int(FileFunction.DELETE_ALL)
        file_access.access_type = 0
    # [:L661-L663] the fall-through into ba020-Call - the SECOND call when the block
    # ran, the ONLY call otherwise. Class 2: the post-block work placed explicitly.
    ba020_call(file_access, value, dal_common, system=system, transport=transport)


def ba020_call(
    file_access: FileAccess,
    value: WsValueRecord,
    dal_common: AcasDalCommonData,
    *,
    system: SystemRecord | None = None,
    transport: TransportSecurity | None = None,
) -> None:
    """``ba020-Call.`` [common/acas013.cbl:L663] - the bridge call.

    So ``acas012`` does NOT declare ``ba020-Process-DAL``; it calls inline, as
    ``acas008`` does. Three shapes, not two, and this handler is alone in the third.
    """
    value_mt(
        file_access, dal_common, value, system=system, transport=transport
    )
    # [:L670] "Any errors leave it to caller to recover from" - deliberately no status
    # inspection, no retry, no log. Reproduced as the absence it is.


def ba_rdbms_exit(file_access: FileAccess) -> None:
    """``ba-rdbms-exit.`` [common/acas013.cbl:L672].

    ``exit section.`` [:L673] - returns from ``ba-Process-RDBMS`` to the ``perform``
    at [:L323] or, on the 901 path, from the ``go to`` at [:L631]. It writes
    nothing, which is why the 901 status set at [:L614-L615] survives all the way
    back to the caller.

     NO RECORD HERE. ``exit section.`` writes nothing and displays nothing,
    so the position trace this paragraph used to emit was invented (R-4). That the
    901 status survives is a fact about the ABSENCE of statements, and a record
    announcing the absence would be the one statement the paragraph does not have.
    """
    return


def ca_process_logs(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``Ca-Process-Logs.`` [common/acas013.cbl:L676] and [common/valueMT.cbl:L1404].

    followed by ``ca-Exit. exit.`` [:L682] and [common/valueMT.cbl:L1410]. One function
    serves both paragraphs because they are the same two lines with the same two
    arguments; the two ``ca-Exit`` paragraphs are likewise one :func:`ca_exit`.
    """
    logging_data = file_access.logging_data
    #  ONE ADAPTER FOR ALL TWENTY HANDLERS.
    # :func:`acas_posting.dal.status.log_file_handler_record` is the single
    # stand-in for `call "fhlogger"`; before it existed each handler wrote its own
    # field list at its own level, so the one legacy log this cycle produces was
    # unreadable as a whole. It advances `Log-File-Rec-Written` modulo one million,
    # the range of the frozen `pic 9(6)` [copybooks/Test-Data-Flags.cob:L20], which
    # this paragraph did not advance at all.
    # `WS-File-Key` is WITHHELD: for this table it is the analysis code, a business
    # key (CWE-532). So are `WS-Log-Where` and `SQL-Msg`. The password was never
    # written and still is not.
    log_file_handler_record(
        _LOG,
        program=HANDLER,
        paragraph="Ca-Process-Logs",
        log_system=logging_data.ws_log_system,
        log_file_no=logging_data.ws_log_file_no,
        no_paragraph=logging_data.ws_no_paragraph,
        file_function=int(file_access.file_function),
        access_type=int(file_access.access_type),
        fs_reply=int(file_access.fs_reply),
        we_error=int(file_access.we_error),
        sql_err=logging_data.sql_err,
        sql_state=logging_data.sql_state,
        dal_common=dal_common,
    )
    ca_exit()


def ca_exit() -> None:
    """``ca-Exit.`` [common/acas013.cbl:L682] and [common/valueMT.cbl:L1410].

    ``exit.`` in both - a paragraph-level exit with no statements of its own. Present
    because R-5 requires a function per paragraph and because ``exit.`` is the marker
    that ``Ca-Process-Logs`` ends here rather than falling into whatever follows.
    """
    return


def dispatch(
    system: SystemRecord,
    value: WsValueRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
    *,
    transport: TransportSecurity | None = None,
) -> None:
    """``call "acas013"`` - THE HANDLER'S FIVE-PARAMETER ENTRY POINT.

    ``move 1 to File-Key-No`` precedes every dispatch, which is why the key guard of
    :func:`_aa010_key_guard` never fires through the facade and why it is nevertheless
    reproduced: a direct caller can set anything.

    Args:
        system: ``System-Record``. Selects the store at [common/acas013.cbl:L321] and
            supplies the credentials at [:L638-L643].
        value: ``WS-Value-Record``. MUTATED IN PLACE, as a COBOL ``CALL`` mutates its
            argument.
        file_access: ``File-Access``. Carries the request in and the status out; read it
            after the call, as the COBOL callers do.
        file_defs: ``File-Defs``. The indexed file's path, used only by the unmigrated
            flat path, and accepted because the linkage list has it.
        dal_common: ``ACAS-DAL-Common-data``. The ``sw-testing`` switch.
        transport: Transport policy for the open verb. NOT A COBOL PARAMETER - the
            frozen bridge has no transport concept at all - and ``None``, the
            default, defers to the ONE policy the deployment installed with
            :func:`acas_posting.dal.connection.set_connection_policy`, which
            reports an unprotected link rather than refusing it. Keyword-only, so
            the five positional parameters remain exactly the COBOL's five.

    Raises:
        IndexedFilePathNotMigrated: If the system record selects the indexed store.
        AcasFileHandlerFatalError: On the ``911`` dispositions of
            :func:`_require_connection` and :func:`_system_for_open`.
    """
    aa010_main(
        system, value, file_access, file_defs, dal_common, transport=transport
    )


# R-5: the paragraph-to-function map, as data.

PARAGRAPH_FUNCTIONS: Final[Mapping[str, tuple[str, str]]] = MappingProxyType(
    {
        "acas013:Procedure Division": ("[common/acas013.cbl:L283]", "dispatch"),
        "acas013:aa-Process-Flat-File Section": (
            "[common/acas013.cbl:L292]",
            "aa010_main",
        ),
        "acas013:aa010-main": ("[common/acas013.cbl:L294]", "aa010_main"),
        "acas013:aa020-Process-Open": (
            "[common/acas013.cbl:L367]",
            "aa020_process_open",
        ),
        "acas013:aa030-Process-Close": (
            "[common/acas013.cbl:L406]",
            "aa030_process_close",
        ),
        "acas013:aa040-Process-Read-Next": (
            "[common/acas013.cbl:L419]",
            "aa040_process_read_next",
        ),
        "acas013:aa045-Eval-Keys": ("[common/acas013.cbl:L452]", "aa045_eval_keys"),
        "acas013:aa050-Process-Read-Indexed": (
            "[common/acas013.cbl:L470]",
            "aa050_process_read_indexed",
        ),
        "acas013:aa060-Process-Start": (
            "[common/acas013.cbl:L492]",
            "aa060_process_start",
        ),
        "acas013:aa070-Process-Write": (
            "[common/acas013.cbl:L538]",
            "aa070_process_write",
        ),
        "acas013:aa080-Process-Delete": (
            "[common/acas013.cbl:L548]",
            "aa080_process_delete",
        ),
        "acas013:aa090-Process-Rewrite": (
            "[common/acas013.cbl:L558]",
            "aa090_process_rewrite",
        ),
        "acas013:aa100-Bad-Function": (
            "[common/acas013.cbl:L569]",
            "aa100_bad_function",
        ),
        "acas013:aa999-main-exit": ("[common/acas013.cbl:L576]", "aa999_main_exit"),
        "acas013:aa-main-exit": ("[common/acas013.cbl:L581]", "aa_main_exit"),
        "acas013:aa-Exit": ("[common/acas013.cbl:L585]", "aa_exit"),
        "acas013:ba-Process-RDBMS section": (
            "[common/acas013.cbl:L588]",
            "ba_process_rdbms",
        ),
        "acas013:ba010-Test-WS-Rec-Size": (
            "[common/acas013.cbl:L596]",
            "ba010_test_ws_rec_size",
        ),
        "acas013:ba012-Test-WS-Rec-Size-2": (
            "[common/acas013.cbl:L604]",
            "ba012_test_ws_rec_size_2",
        ),
        "acas013:ba015-Test-Ends": ("[common/acas013.cbl:L646]", "ba015_test_ends"),
        "acas013:ba020-Call": ("[common/acas013.cbl:L663]", "ba020_call"),
        "acas013:ba-rdbms-exit": ("[common/acas013.cbl:L672]", "ba_rdbms_exit"),
        "acas013:Ca-Process-Logs": (
            "[common/acas013.cbl:L676]",
            "ca_process_logs",
        ),
        "acas013:ca-Exit": ("[common/acas013.cbl:L682]", "ca_exit"),
        "valueMT:PROCEDURE DIVISION": ("[common/valueMT.cbl:L339]", "value_mt"),
        "valueMT:ba-ACAS-DAL-Process section": (
            "[common/valueMT.cbl:L343]",
            "value_mt",
        ),
        "valueMT:ba010-Initialise": (
            "[common/valueMT.cbl:L354]",
            "ba010_initialise",
        ),
        "valueMT:ba020-Process-Open": (
            "[common/valueMT.cbl:L401]",
            "ba020_process_open",
        ),
        "valueMT:ba030-Process-Close": (
            "[common/valueMT.cbl:L445]",
            "ba030_process_close",
        ),
        "valueMT:ba040-Process-Read-Next": (
            "[common/valueMT.cbl:L460]",
            "ba040_process_read_next",
        ),
        "valueMT:ba041-Reread": ("[common/valueMT.cbl:L535]", "ba041_reread"),
        "valueMT:ba050-Process-Read-Indexed": (
            "[common/valueMT.cbl:L600]",
            "ba050_process_read_indexed",
        ),
        "valueMT:ba060-Process-Start": (
            "[common/valueMT.cbl:L695]",
            "ba060_process_start",
        ),
        "valueMT:ba070-Process-Write": (
            "[common/valueMT.cbl:L809]",
            "ba070_process_write",
        ),
        "valueMT:ba080-Process-Delete": (
            "[common/valueMT.cbl:L836]",
            "ba080_process_delete",
        ),
        "valueMT:ba085-Process-Delete-All": (
            "[common/valueMT.cbl:L891]",
            "ba085_process_delete_all",
        ),
        "valueMT:ba090-Process-Rewrite": (
            "[common/valueMT.cbl:L972]",
            "ba090_process_rewrite",
        ),
        "valueMT:ba100-Bad-Function": (
            "[common/valueMT.cbl:L1017]",
            "ba100_bad_function",
        ),
        "valueMT:ba998-Free": ("[common/valueMT.cbl:L1029]", "ba998_free"),
        "valueMT:ba999-end": ("[common/valueMT.cbl:L1041]", "ba999_end"),
        "valueMT:ba999-exit": ("[common/valueMT.cbl:L1048]", "ba999_end"),
        "valueMT:bb000-HV-Load Section": (
            "[common/valueMT.cbl:L1051]",
            "bb000_hv_load",
        ),
        "valueMT:bb000-Exit": ("[common/valueMT.cbl:L1074]", "bb000_hv_load"),
        "valueMT:bb100-UnloadHVs Section": (
            "[common/valueMT.cbl:L1077]",
            "bb100_unload_hvs",
        ),
        "valueMT:bb100-Exit": ("[common/valueMT.cbl:L1099]", "bb100_unload_hvs"),
        "valueMT:bb200-Insert Section": (
            "[common/valueMT.cbl:L1102]",
            "bb200_insert",
        ),
        "valueMT:bb200-Exit": ("[common/valueMT.cbl:L1248]", "bb200_insert"),
        "valueMT:bb300-Update Section": (
            "[common/valueMT.cbl:L1251]",
            "bb300_update",
        ),
        "valueMT:bb300-Exit": ("[common/valueMT.cbl:L1401]", "bb300_update"),
        "valueMT:Ca-Process-Logs": (
            "[common/valueMT.cbl:L1404]",
            "ca_process_logs",
        ),
        "valueMT:ca-Exit": ("[common/valueMT.cbl:L1410]", "ca_exit"),
    }
)

#: The paragraphs deliberately NOT given a function, each with the reason.
OMITTED_PARAGRAPHS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "valueMT:ba-ACAS-DAL-Process section header statements": (
            "[common/valueMT.cbl:L344-L352] reads the terminal height into "
            "ws-env-lines and sets COB_SCREEN_EXCEPTIONS and COB_SCREEN_ESC. "
            "Presentation setup with no database effect, excluded by AAP section "
            "0.1.1."
        ),
        "valueMT:dead go to ba041-Reread": (
            "[common/valueMT.cbl:L804] sits after the unconditional go to at "
            "[:L800] and is unreachable. N-deadcode; not translated."
        ),
        "acas013:Value-File / Value-Record indexed-file verbs": (
            "The aa0NN paragraphs' READ, WRITE, REWRITE, DELETE, START, OPEN and "
            "CLOSE statements address the ISAM file selected at "
            "[copybooks/selval.cob:L2]. The migrated path returns at "
            "[common/acas013.cbl:L325] before reaching them; see "
            "IndexedFilePathNotMigrated."
        ),
        "common/fhlogger.cbl": (
            "Called by both Ca-Process-Logs paragraphs. AAP section 0.2.2 places it "
            "among the out-of-scope non-posting utilities and R-1 forbids calling "
            "the COBOL program, so its record is emitted as a log line instead - "
            "see ca_process_logs."
        ),
    }
)


def paragraph_coverage() -> tuple[str, ...]:
    """Verify that every function :data:`PARAGRAPH_FUNCTIONS` names really exists.

    R-5's paragraph-to-function mapping is only worth having if it is true, and a
    mapping held as strings can rot the moment a function is renamed. This resolves
    every name against this module's own namespace.

    Returns:
        The paragraph keys whose named function is missing - empty when the mapping is
            sound, which is the only acceptable state.
    """
    namespace = globals()
    return tuple(
        paragraph
        for paragraph, (_locator, function_name) in PARAGRAPH_FUNCTIONS.items()
        if not callable(namespace.get(function_name))
    )
