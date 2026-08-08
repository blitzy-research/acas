"""ACAS file-handler status protocol and operation vocabulary.

WHAT THIS MODULE OWNS
=====================
Three things, for the whole migrated cycle:

* the **status protocol** - the ``FS-Reply`` value set, the ``We-Error`` code
  set, the SQLSTATE vocabulary, and the mapping from a driver error to that
  pair;
* the **operation vocabulary** - the ``File-Function`` codes and the
  ``Access-Type`` codes, plus the START relation those access types double as;
  and
* the **safe-event schema** - the one allowlist of what a diagnostic record may
  carry, the log-safety renderers that enforce it, the single ``fhlogger``
  adapter, and the single failure and ``STOP``-literal reporters that every
  handler and every program calls instead of composing its own record.

The third belongs here rather than in a module of its own for the same reason
the first two do: Agent Action Plan section 0.4.3 makes ``dal/status.py`` the
import every ``COPY "wsfnctn.cob"`` resolves to, so it is the one module both
``acas_posting.dal`` and ``acas_posting.programs`` already depend on. Adding a
fourth home for it would have meant a new edge in the dependency table that
section 0.4.3 does not grant.

The SQLSTATE mapping and the lock-retry ladder are here too, because a handler
reports a relational failure through the same two fields an indexed-file failure
uses; a caller therefore cannot tell which store answered, which is the point.

The split of that one copybook is therefore two-way and deliberate: the record
LAYOUT lives in `acas_posting.records.file_access`, which is a leaf, and the
operation VOCABULARY lives here, where both the handlers and the programs may
reach it.
"""

from __future__ import annotations

import enum
import logging
import re
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:  # pragma: no cover - imported for annotations only.
    # `LoggingData` is the record sub-block this module's error results are written
    # into: `SQL-Err`, `SQL-Msg` and `SQL-State` are its fields
    # [copybooks/wsfnctn.cob:L49-L51].
    from acas_posting.records.file_access import LoggingData

__all__: Final[tuple[str, ...]] = (
    "DOCUMENTATION_ONLY_WE_ERRORS",
    "DOCUMENTED_SQLSTATE_MAPPINGS",
    "DUPLICATE_KEY_COMMAND_PREFIXES",
    "DUPLICATE_KEY_ERRNOS",
    "DUPLICATE_KEY_SQLSTATE",
    "END_OF_FILE_WE_ERROR",
    "FH_LOG_LEVEL",
    "FH_LOG_REC_MODULUS",
    "FILE_KEY_NO_DOCUMENTED_RANGE",
    "FILE_KEY_NO_GUARD_RANGE",
    "LOCK_ERRNOS",
    "LOCK_RETRY_LADDER",
    "LOG_CATEGORY_UNCLASSIFIED",
    "LOG_ELISION",
    "LOG_FIELD_MAX_CHARS",
    "LOG_REDACTION",
    "MISSING_SQLSTATE_COPYBOOK",
    "SQL_ERR_WIDTH",
    "SQL_MSG_WIDTH",
    "SQL_STATE_WIDTH",
    "START_ACCESS_TYPE_RANGE",
    "START_RELATION_BY_ACCESS_TYPE",
    "START_RELATION_TOKEN_BY_ACCESS_TYPE",
    "WE_ERRORS_IMPLYING_FS_REPLY_ERROR",
    "WE_ERROR_OVERRIDE_BY_FILE_FUNCTION",
    "AcasFileHandlerError",
    "AcasFileHandlerFatalError",
    "AccessType",
    "ConnectStep",
    "DbErrorStatus",
    "FileFunction",
    "FsReply",
    "LockRetryRung",
    "LogSystem",
    "SqlState",
    "SqlStateMapping",
    "WeError",
    "db_error_log_category",
    "end_of_file_status",
    "implies_fs_reply_error",
    "is_duplicate_key_bridge_level",
    "is_duplicate_key_driver_level",
    "is_lock_errno",
    "is_ok",
    "log_cobol_stop",
    "log_file_handler_record",
    "log_handler_failure",
    "mysql_1100_db_error",
    "mysql_1300_db_error",
    "override_we_error_for_operation",
    "raise_for_status",
    "redact_for_log",
    "sanitise_for_log",
    "start_access_type_is_valid",
    "start_relation_for",
)

#: Module logger. A library module attaches no handler and configures no root logger;
#: the application decides where diagnostics go.
_LOG: Final[logging.Logger] = logging.getLogger(__name__)

#: The copybook that ``common/glpostingMT.cbl:L160`` copies and that is ABSENT from the
#: checkout.
MISSING_SQLSTATE_COPYBOOK: Final[str] = "ACAS-SQLstate-error-list.cob"


class FsReply(enum.IntEnum):
    """The ``FS-Reply`` value set, as the bridges' own prose table defines it.

    ``IntEnum`` and not ``Enum``: ``FileAccess.fs_reply`` is a plain ``int`` attribute,
    so a member must compare equal to the raw value a handler stores there.
    """

    SUCCESS = 0

    #: `10 = End of (Cobol) File returned to calling module only.`
    #: [common/glpostingMT.cbl:L127] ANOMALY-ADJACENT FACT, not a defect but easy to get
    #: wrong.
    END_OF_FILE = 10

    #: `21 = Invalid key on START OR key not found` [common/glpostingMT.cbl:L128]
    #: Produced on the START parameter guard together with `We-Error 997`
    #: [common/glpostingMT.cbl:L695-L698], and - see `KEY_NOT_FOUND` below - ALSO
    #: produced by the read-indexed path of seven of the twenty in-scope bridges where
    #: the prose table promises 23, paired there with `We-Error 990` [:L668-L669] or
    #: `We-Error 989` [:L676-L677].
    INVALID_KEY_ON_START = 21

    DUPLICATE_KEY = 22

    #: `23 = Key not found.
    KEY_NOT_FOUND = 23

    ERROR = 99


#: The `We-Error` value that accompanies `FsReply.END_OF_FILE`, which is 10 and NOT zero
#: - see the note on that member.
END_OF_FILE_WE_ERROR: Final[int] = 10


def end_of_file_status() -> tuple[FsReply, int]:
    """Return the end-of-file status pair, ``(10, 10)``.

    Reproduces ``move 10 to fs-Reply WE-Error`` [common/glpostingMT.cbl:L557] - one
    statement writing BOTH fields, which is why this helper exists rather than two
    assignments at each call site.

    Returns:
        The ``(FS-Reply, We-Error)`` pair to store into ``FileAccess``.

    Examples:
        >>> end_of_file_status()
        (<FsReply.END_OF_FILE: 10>, 10)
    """
    return FsReply.END_OF_FILE, END_OF_FILE_WE_ERROR


# FILE-FUNCTION - THE OPERATION CODE. `03 File-Function pic 99.`
# [copybooks/wsfnctn.cob:L88] with fifteen `88`-level condition names [:L89-L105].


class FileFunction(enum.IntEnum):
    """The ``File-Function`` operation codes, in copybook declaration order.

    The names are the ``88``-level names with the ``fn-`` prefix dropped and the hyphens
    made underscores, so the correspondence to the frozen source is mechanical in both
    directions: ``fn-read-next`` becomes ``READ_NEXT`` and back.
    """

    OPEN = 1

    CLOSE = 2

    READ_NEXT = 3

    READ_INDEXED = 4

    WRITE = 5

    DELETE_ALL = 6

    #: `88 fn-re-write value 7.` [copybooks/wsfnctn.cob:L95] Published by the facade for
    #: every entity, but permanently rejected by the sequential-file handler
    #: [common/acas008.cbl:L299-L307], so the `SPL-Posting-Rewrite` verb can never
    #: succeed.
    RE_WRITE = 7

    DELETE = 8

    #: `88 fn-start value 9.` [copybooks/wsfnctn.cob:L97] The one verb whose facade
    #: paragraph deliberately does NOT zero `Access-Type` - see
    #: `START_RELATION_BY_ACCESS_TYPE` below.
    START = 9


    #: `88 fn-Write-Raw value 15.` [copybooks/wsfnctn.cob:L99] Declared BEFORE value 13
    #: and higher than it. Preserved as written.
    WRITE_RAW = 15

    READ_NEXT_RAW = 13

    #: `88 fn-Read-By-Name value 31. *> 15/01/17 for Salesled (SL160), could be used for
    #: GL ledger?` [copybooks/wsfnctn.cob:L102] The trailing question mark is the
    #: maintainer's own.
    READ_BY_NAME = 31

    READ_BY_BATCH = 32

    READ_BY_CUST = 33

    READ_NEXT_HEADER = 34


# ACCESS-TYPE - THE OPEN MODE, AND (FOR START) THE RELATION. `03 Access-Type pic 9.`
# [copybooks/wsfnctn.cob:L107] with nine `88`-level condition names [:L108-L116]. ONE
# digit, not two.


class AccessType(enum.IntEnum):
    """The ``Access-Type`` codes: values 1-4 are open modes, 5-9 relations."""


    INPUT = 1

    I_O = 2

    OUTPUT = 3

    EXTEND = 4


    EQUAL_TO = 5

    LESS_THAN = 6

    GREATER_THAN = 7

    NOT_LESS_THAN = 8

    #: `88 fn-not-greater-than value 9.` [copybooks/wsfnctn.cob:L116] The changelog says
    #: this one was switched on - `*> 06/08/23 vbc - Activated fn-not-greater-than (for
    #: Stock file).` [copybooks/wsfnctn.cob:L20] - but the START guard still rejects it.
    NOT_GREATER_THAN = 9


# ACCESS-TYPE 5-9 AS THE START RELATION. Why the caller's `Access-Type` survives into a
# START at all.

_MOST_RELATION_WIDTH: Final[int] = 3

#: `Access-Type` -> the relation exactly as the bridge stores it, padded to the three
#: characters of `MOST-Relation pic xxx`.
START_RELATION_BY_ACCESS_TYPE: Final[Mapping[AccessType, str]] = MappingProxyType(
    {
        AccessType.EQUAL_TO: "=  ",
        AccessType.LESS_THAN: "<  ",
        AccessType.GREATER_THAN: ">  ",
        AccessType.NOT_LESS_THAN: ">= ",
        # when 9 *> fn-not-greater-than [ not currently used in ACAS ] UNREACHABLE
        # behind the L695 guard - anomaly N5. [:L724-L725].
        AccessType.NOT_GREATER_THAN: "<= ",
    }
)

#: The same five relations with the padding stripped, which is the form that reaches the
#: SQL text.
START_RELATION_TOKEN_BY_ACCESS_TYPE: Final[Mapping[AccessType, str]] = (
    MappingProxyType(
        {
            access_type: relation.strip()
            for access_type, relation in START_RELATION_BY_ACCESS_TYPE.items()
        }
    )
)

#: The inclusive bounds the START parameter guard actually enforces, as the frozen `if
#: access-type < 5 or > 8` writes them [common/glpostingMT.cbl:L695].
START_ACCESS_TYPE_RANGE: Final[tuple[int, int]] = (5, 8)


def start_access_type_is_valid(access_type: int) -> bool:
    """Report whether a START would pass the bridge's parameter guard.

    Reproduces ``if access-type < 5 or > 8`` exactly [common/glpostingMT.cbl:L695],
    upper bound of 8 included - see anomaly N5 on :data:`START_RELATION_BY_ACCESS_TYPE`.

    Args:
        access_type: The ``Access-Type`` value the caller set before the ``fn-start``
            call. Accepts a plain ``int`` because that is what
            ``FileAccess.access_type`` holds.

    Returns:
        ``True`` if the value lies within the guard's inclusive 5-8 range.

    Examples:
        >>> start_access_type_is_valid(AccessType.NOT_LESS_THAN)
        True

        Anomaly N5 in one line: ``NOT_GREATER_THAN`` is 9, so the guard's upper
        bound of 8 REFUSES it - even though
        :data:`START_RELATION_BY_ACCESS_TYPE` still maps it to ``"<= "``, which is
        why that relation is unreachable behind this guard.

        >>> start_access_type_is_valid(AccessType.NOT_GREATER_THAN)
        False
        >>> start_access_type_is_valid(AccessType.INPUT)
        False
    """
    lower, upper = START_ACCESS_TYPE_RANGE
    return lower <= int(access_type) <= upper


def start_relation_for(access_type: int, *, padded: bool = False) -> str:
    """Return the START relation for an access type.

    Reproduces the relation table at [common/glpostingMT.cbl:L715-L726]. The dead ``when
    9`` arm is served like any other, because the COBOL ``evaluate`` declares it;
    reaching it requires having skipped the guard, exactly as it would in COBOL. Use
    :func:`start_access_type_is_valid` first.

    Args:
        access_type: An ``Access-Type`` value in the 5-9 relation band.
        padded: ``True`` for the three-character form the bridge stores into ``MOST-
            Relation pic xxx``.

    Returns:
        The relation as a string.

    Raises:
        KeyError: If the value is outside the 5-9 relation band.
    """
    key = AccessType(int(access_type))
    if padded:
        return START_RELATION_BY_ACCESS_TYPE[key]
    return START_RELATION_TOKEN_BY_ACCESS_TYPE[key]


class WeError(enum.IntEnum):
    """The ``We-Error`` detail codes, with the frozen prose for each.

    Fourteen members: the twelve of the bridge's own table plus the two that exist only
    in handler source.
    """

    SUCCESS = 0

    NOT_USED = 999

    FILE_KEY_NO_OUT_OF_RANGE = 998

    #: `997* = Access-Type wrong (< 5 or > 8)` [common/glpostingMT.cbl:L136] The
    #: parenthesis is the guard verbatim, and its upper bound of 8 is the whole of
    #: anomaly N5.
    ACCESS_TYPE_WRONG = 997

    DELETE_KEY_OUT_OF_RANGE = 996

    #: `995* = During Delete SQLSTATE not '00000' investigate using MSG-Err/Msg`
    #: [common/glpostingMT.cbl:L138] One of the two per-operation narrowings of the 911
    #: catch-all.
    DELETE_SQLSTATE_NOT_00000 = 995

    REWRITE_SQLSTATE_NOT_00000 = 994

    #: ANOMALY N6 - REPRODUCED, NOT FIXED (rule R-4) *** This code has NO PRODUCER.
    INVALID_FUNCTION = 992

    #: `990* = Unknown and unexpected error, again ^^ see above ^^`
    #: [common/glpostingMT.cbl:L141] Paired with FS-Reply 21 - not 23 - on the read-
    #: indexed error branch.
    UNKNOWN_UNEXPECTED = 990

    #: `989* = Unexpected error on Read-Indexed, investigate as above.`
    #: [common/glpostingMT.cbl:L142] Paired with FS-Reply 21 - again not 23 - on the
    #: read-indexed no-such-row branch.
    READ_INDEXED_UNEXPECTED = 989

    #: `988* = File Action wrong for file type.` [common/acas008.cbl:L173], the site's
    #: own wording being `*> Action type wrong for file type (seq) 988`
    #: [common/acas008.cbl:L304].
    ACTION_TYPE_WRONG_FOR_SEQ = 988

    #: `911* = Rdb Error during initializing, possibly can not connect to database /
    #: Check connect data and see SQL-Err & SQL-MSG / Produced by Mysql-1100-Db-Error in
    #: copy module mysql-procedure.` [common/glpostingMT.cbl:L143-L148] *** ANOMALY N3 -
    #: REPRODUCED, NOT FIXED (rule R-4) *** The documentation says "during
    #: initializing".
    RDB_INIT_ERROR = 911

    #: `910* = Table locked > 5 seconds` [common/glpostingMT.cbl:L149] *** ANOMALY N1 -
    #: REPRODUCED, NOT FIXED (rule R-4) *** UNREACHABLE AT RUNTIME.
    TABLE_LOCKED = 910

    #: `901 = File Def Record size not =< than ws record size / Module needs ws
    #: definition changing to correct size / FATAL, Stop using system, fix source code
    #: and recompile before using system again.` [common/glpostingMT.cbl:L150-L153]
    #: FATAL in the frozen source's own capitals.
    RECORD_SIZE_MISMATCH = 901


#: The `We-Error` codes that arrive with `FsReply.ERROR`, i.e.
WE_ERRORS_IMPLYING_FS_REPLY_ERROR: Final[frozenset[WeError]] = frozenset(
    {
        WeError.FILE_KEY_NO_OUT_OF_RANGE,
        WeError.ACCESS_TYPE_WRONG,
        WeError.DELETE_KEY_OUT_OF_RANGE,
        WeError.DELETE_SQLSTATE_NOT_00000,
        WeError.REWRITE_SQLSTATE_NOT_00000,
        WeError.INVALID_FUNCTION,
        WeError.UNKNOWN_UNEXPECTED,
        WeError.READ_INDEXED_UNEXPECTED,
        WeError.ACTION_TYPE_WRONG_FOR_SEQ,
        WeError.RDB_INIT_ERROR,
        WeError.TABLE_LOCKED,
        WeError.RECORD_SIZE_MISMATCH,
    }
)

#: The `We-Error` codes with NO producer anywhere in the frozen tree - present in the
#: authoritative prose table, set by no statement. 992 is anomaly N6.
DOCUMENTATION_ONLY_WE_ERRORS: Final[frozenset[WeError]] = frozenset(
    {WeError.INVALID_FUNCTION, WeError.TABLE_LOCKED}
)


def implies_fs_reply_error(we_error: int) -> bool:
    """Report whether a ``We-Error`` code arrives with ``FS-Reply 99``.

    This is a reporting predicate over :data:`WE_ERRORS_IMPLYING_FS_REPLY_ERROR`, not a
    validation: it never rejects anything, and no caller is obliged to consult it.

    Args:
        we_error: A ``We-Error`` value; a plain ``int`` is accepted because that is what
            ``FileAccess.we_error`` holds.

    Returns:
        ``True`` if the code is one that the frozen source pairs with ``FS-Reply 99``.
    """
    try:
        member = WeError(int(we_error))
    except ValueError:
        return False
    return member in WE_ERRORS_IMPLYING_FS_REPLY_ERROR


#: The range the copybook DOCUMENTS, immediately above the `Logging-Data` block,
#: verbatim [copybooks/wsfnctn.cob:L42-L43].
FILE_KEY_NO_DOCUMENTED_RANGE: Final[tuple[int, int]] = (1, 3)

FILE_KEY_NO_GUARD_RANGE: Final[tuple[int, int]] = (1, 5)


class SqlState(enum.StrEnum):
    """The five-character SQLSTATE values the frozen source names.

    * ``NO_DATA`` and ``DUPLICATE_KEY`` are real ANSI SQLSTATE values that arrive from
    the driver. * the five ``99xxx`` values are **not SQLSTATEs at all**.
    """

    #: `0200n no data found one way or another` [copybooks/mysql-procedures.cpy:L112]
    #: The frozen comment writes the value as `0200n` with a trailing placeholder
    #: letter, i.e.
    NO_DATA = "02000"

    DUPLICATE_KEY = "23000"

    INVALID_KEY_NUMBER = "99NKS"

    NO_VALID_KEY = "99NKU"

    NO_VALID_KEY_FOR_DELETE = "99NKD"

    READ_NEXT_WITH_NO_POSITION = "99RNP"

    COULD_NOT_GENERATE_START = "99GNS"


@dataclass(frozen=True, slots=True)
class SqlStateMapping:
    """One line of the SQLSTATE dispositions block, with its wiring status.

    A record of what the frozen source SAYS a SQLSTATE should mean, paired with whether
    any code actually acts on it. The ``implemented`` marker is the point of the type.
    """

    sql_state: SqlState

    #: The disposition the frozen comment proposes, in this migration's words rather
    #: than the maintainer's where the original wording cannot be reproduced here - see
    #: the note on ``SqlState.NO_DATA``.
    proposed_disposition: str

    locator: str

    implemented: bool


#: The SQLSTATE dispositions block, entry by entry, with its wiring status.
DOCUMENTED_SQLSTATE_MAPPINGS: Final[tuple[SqlStateMapping, ...]] = (
    SqlStateMapping(
        sql_state=SqlState.NO_DATA,
        proposed_disposition=(
            "No data found. The frozen note proposes deciding between "
            "FS-Reply 23 and FS-Reply 10 by an entropy source, and is "
            "paraphrased rather than quoted for the reason given in the "
            "module docstring. Never implemented; the test that would have "
            "read it is commented out at "
            "[copybooks/mysql-procedures.cpy:L124]."
        ),
        locator="[copybooks/mysql-procedures.cpy:L112]",
        implemented=False,
    ),
    SqlStateMapping(
        sql_state=SqlState.DUPLICATE_KEY,
        proposed_disposition=(
            "Duplicate primary key on insert, same as FS-Reply 22. The ONLY "
            "entry of this block that any live path acts on, and it acts on "
            "it at the bridge level rather than here "
            "[common/glpostingMT.cbl:L818-L820]."
        ),
        locator="[copybooks/mysql-procedures.cpy:L114]",
        implemented=True,
    ),
    SqlStateMapping(
        sql_state=SqlState.INVALID_KEY_NUMBER,
        proposed_disposition="Internal error: invalid key number used.",
        locator="[copybooks/mysql-procedures.cpy:L115]",
        implemented=False,
    ),
    SqlStateMapping(
        sql_state=SqlState.NO_VALID_KEY,
        proposed_disposition="Internal error: no valid key used.",
        locator="[copybooks/mysql-procedures.cpy:L116]",
        implemented=False,
    ),
    SqlStateMapping(
        sql_state=SqlState.NO_VALID_KEY_FOR_DELETE,
        proposed_disposition="Internal error: no valid key used for delete.",
        locator="[copybooks/mysql-procedures.cpy:L117]",
        implemented=False,
    ),
    SqlStateMapping(
        sql_state=SqlState.READ_NEXT_WITH_NO_POSITION,
        proposed_disposition=(
            "Internal error: read next with no position, i.e. no START was "
            "issued first."
        ),
        locator="[copybooks/mysql-procedures.cpy:L118]",
        implemented=False,
    ),
    SqlStateMapping(
        sql_state=SqlState.COULD_NOT_GENERATE_START,
        proposed_disposition="Internal error: could not generate a start.",
        locator="[copybooks/mysql-procedures.cpy:L119]",
        implemented=False,
    ),
)


# The same condition is detected twice in one call chain, by two tests that do not
# agree.

#: The driver error numbers that mean "duplicate", as the driver-level test writes them,
#: verbatim `if Ws-Mysql-Error-Number = "1062" or = "1022" *> Duplicate entry/Write dup
#: key` [copybooks/mysql-procedures.cpy:L99].
DUPLICATE_KEY_ERRNOS: Final[frozenset[str]] = frozenset({"1062", "1022"})

#: The two statement-text prefixes the driver-level test accepts, from the `evaluate`
#: arms at [copybooks/mysql-procedures.cpy:L100-L102].
DUPLICATE_KEY_COMMAND_PREFIXES: Final[tuple[str, ...]] = ("INSERT", "insert")

_DUPLICATE_KEY_COMMAND_PREFIX_LENGTH: Final[int] = 6

#: The SQLSTATE the BRIDGE-level test accepts as a duplicate
#: [common/glpostingMT.cbl:L820]. The driver-level test never looks at SQLSTATE; this is
#: the one place it is consulted.
DUPLICATE_KEY_SQLSTATE: Final[str] = SqlState.DUPLICATE_KEY

#: Length of the reference modification `SQL-Err (1:4)` [common/glpostingMT.cbl:L818] -
#: four characters of a `pic x(5)` field [copybooks/wsfnctn.cob:L49], so the fifth
#: character is NOT compared.
_SQL_ERR_COMPARE_LENGTH: Final[int] = 4


def is_duplicate_key_driver_level(errno: str, command: str) -> bool:
    """Driver-level duplicate test, from ``Mysql-1100-Db-Error``.

    Two structural details of that fragment are load-bearing and are both reproduced.

    Args:
        errno: The driver's error number AS TEXT, because ``Ws-Mysql-Error-Number`` is a
            character field and COBOL compares it as text.
        command: The statement text, unparsed and untrimmed - the equivalent of ``Ws-
            Mysql-Command``. Only its first six characters are looked at, and they are
            compared case-sensitively.

    Returns:
        ``True`` only if BOTH tests pass, meaning the caller should set ``FS-Reply 22``
            and exit early WITHOUT touching ``We-Error``.
    """
    if errno not in DUPLICATE_KEY_ERRNOS:
        return False

    # `evaluate Ws-Mysql-Command (1:6)` [:L100] with arms `when "INSERT"` and `when
    # "insert"` [:L101-L102].
    prefix = command[:_DUPLICATE_KEY_COMMAND_PREFIX_LENGTH]

    # No `when other` and no `end-evaluate` [:L105]: a non-INSERT duplicate falls
    # through to the generic path rather than being reported as 22.
    return prefix in DUPLICATE_KEY_COMMAND_PREFIXES


def is_duplicate_key_bridge_level(sql_err: str, sql_state: str) -> bool:
    """Bridge-level duplicate test, from ``ba070-Process-Write``.

    Reproduces [common/glpostingMT.cbl:L818-L824], verbatim::

        if    SQL-Err (1:4) = "1062"
                         or = "1022"   *> Dup key (rec already present)
            or Sql-State = "23000"  *> Dup key (rec already present)
              move 22 to fs-reply
        else
              move 99 to fs-reply                  *> this may need changing for val in WE-Error!!
        end-if

    How this differs from the driver-level test, which is why the two are
    separate functions rather than one:

    * it reads ``SQL-Err``, the field the driver-level path already STORED
      [common/glpostingMT.cbl:L816], rather than calling for the errno again;
    * it compares only the FIRST FOUR characters of a five-character field
      [copybooks/wsfnctn.cob:L49], so the fifth is never examined;
    * it accepts SQLSTATE ``"23000"`` as a third, independent alternative -
      the driver-level test does not look at SQLSTATE at all; and
    * it does NOT test the statement text, so at this layer a duplicate errno
      IS reported as 22 whatever statement raised it. The two layers disagree
      on precisely that point.

    Neither branch touches ``We-Error``, which is the maintainer's own concern
    in the trailing comment at ``:L823``. So a caller reaching the ``else``
    gets ``FS-Reply 99`` beside whatever ``We-Error`` was already there -
    usually the 911 that anomaly N3 left.

    Note that the whole fragment sits inside two guards: ``if
    WS-MYSQL-COUNT-ROWS not = 1`` [:L810] and ``if WS-MYSQL-Error-Number (1:1)
    not = "0"`` [:L814]. Those belong to the GL posting handler's write path
    in ``acas_posting.dal.acas006_gl_posting``; this function is only the
    innermost test.

    Args:
        sql_err: The ``SQL-Err`` field's contents. Only the first four characters are
            compared.
        sql_state: The ``SQL-State`` field's contents, compared in full.

    Returns:
        ``True`` for ``FS-Reply 22``, ``False`` for ``FS-Reply 99``.
    """
    if sql_err[:_SQL_ERR_COMPARE_LENGTH] in DUPLICATE_KEY_ERRNOS:
        return True

    # `or Sql-State = "23000"` [:L820] - the only runtime use of SQLSTATE anywhere in
    # the frozen error path. Anomaly N4.
    return sql_state == DUPLICATE_KEY_SQLSTATE


# THE DIAGNOSTIC FIELDS, AND A LOCAL PICTURE-CLAUSE HELPER.

SQL_ERR_WIDTH: Final[int] = 5

SQL_MSG_WIDTH: Final[int] = 512

SQL_STATE_WIDTH: Final[int] = 5


def _pic_x(text: str, width: int) -> str:
    """Store ``text`` into an alphanumeric field of ``width`` characters."""
    return text[:width].ljust(width)


# LOG-SAFE DIAGNOSTIC TEXT (CWE-117 log injection, CWE-532 secret exposure) The three
# fields above carry the DRIVER'S OWN account of a failure, and two things are true of
# that text at once.

#: The fixed marker that stands in for a removed identity or secret.
LOG_REDACTION: Final[str] = "[redacted]"

LOG_ELISION: Final[str] = "[...]"

#: The rendered length one diagnostic field may occupy in a log record.
LOG_FIELD_MAX_CHARS: Final[int] = 200

LOG_CATEGORY_UNCLASSIFIED: Final[str] = "unclassified"

#: Codepoints replaced by their own escape spelling before text is logged.
_CONTROL_CODEPOINTS: Final[tuple[int, ...]] = (
    *range(0x00, 0x20),
    0x7F,
    *range(0x80, 0xA0),
    0x2028,
    0x2029,
)


def _control_character_escapes() -> Mapping[int, str]:
    r"""Build the translation table :func:`sanitise_for_log` applies.

    Returns:
        A read-only mapping from each codepoint of :data:`_CONTROL_CODEPOINTS` to the
            text `\xNN` or `\uNNNN`, so that the escape a reader sees is the codepoint
            that was actually present.
    """
    escapes: dict[int, str] = {}
    for codepoint in _CONTROL_CODEPOINTS:
        if codepoint < 0x100:
            escapes[codepoint] = "\\x%02x" % codepoint
        else:
            escapes[codepoint] = "\\u%04x" % codepoint
    return MappingProxyType(escapes)


_CONTROL_CHARACTER_ESCAPES: Final[Mapping[int, str]] = (
    _control_character_escapes()
)

_REDACTION_RULES: Final[tuple[tuple[re.Pattern[str], str], ...]] = (
    (
        re.compile(r"(?i)\bfor user\s+'[^']*'(?:@'[^']*')?"),
        "for user " + LOG_REDACTION,
    ),
    (re.compile(r"'[^']*'@'[^']*'"), LOG_REDACTION),
    # The driver's own report of whether a password was sent. Deliberately `[A-Za-z]+`
    # rather than `\S+`.
    (
        re.compile(r"(?i)\busing password:\s*[A-Za-z]+"),
        "using password: " + LOG_REDACTION,
    ),
    # Any explicit password assignment, however spelled. Two exclusions keep it from
    # damaging what the rules above have already produced.
    (
        re.compile(
            r"(?i)\b(pass(?:wd|word|phrase))\s*[=:]\s*"
            r"(?!" + re.escape(LOG_REDACTION) + r")[^\s)]+"
        ),
        "\\g<1>=" + LOG_REDACTION,
    ),
    (
        re.compile(
            r"(?i)\b(server|host|socket|database|schema)"
            r"\s+(?:on\s+|through\s+)?'[^']*'"
        ),
        "\\g<1> " + LOG_REDACTION,
    ),
)

#: Stable low-cardinality categories for the error numbers this cycle can meet. NOTHING
#: BRANCHES ON THIS TABLE.
_LOG_CATEGORY_BY_ERRNO: Final[Mapping[str, str]] = MappingProxyType(
    {
        "1044": "access-denied",
        "1045": "access-denied",
        "1698": "access-denied",
        "1049": "unknown-database",
        "1146": "unknown-table",
        "2002": "connect-failed",
        "2003": "connect-failed",
        "2005": "connect-failed",
        "2006": "connection-lost",
        "2013": "connection-lost",
        "2026": "tls-failed",
        "2055": "connection-lost",
    }
)


def sanitise_for_log(text: str, *, limit: int = LOG_FIELD_MAX_CHARS) -> str:
    r"""Render ``text`` so that it cannot forge or distort a log record.

    Args:
        text: the text to render. Driver-supplied text is the expected case.
        limit: the rendered length allowed before the tail is elided.

    Returns:
        A single-line rendering, at most ``limit`` characters plus :data:`LOG_ELISION`.

    Examples:
        A forged second log record cannot be injected, because the CR and LF are
        escaped rather than emitted:

        >>> sanitise_for_log("first\r\nWARNING forged second")
        'first\\x0d\\x0aWARNING forged second'

        And an over-long rendering is elided rather than truncated silently:

        >>> sanitise_for_log("abcdef", limit=3)
        'abc[...]'
    """
    escaped = text.translate(_CONTROL_CHARACTER_ESCAPES)
    if len(escaped) <= limit:
        return escaped
    return escaped[:limit] + LOG_ELISION


def redact_for_log(text: str, *, limit: int = LOG_FIELD_MAX_CHARS) -> str:
    """Remove identities and secrets from ``text``, then render it log-safe.

    Args:
        text: the driver-supplied text.
        limit: as :func:`sanitise_for_log`.

    Returns:
        The redacted, sanitised rendering: the driver's "Access denied for user
            '<account>'@'<host>' (using password: YES)" becomes "Access denied for user
            [redacted] (using password".
    """
    redacted = text
    for pattern, replacement in _REDACTION_RULES:
        redacted = pattern.sub(replacement, redacted)
    return sanitise_for_log(redacted, limit=limit)


def db_error_log_category(errno: int | str, sql_state: str = "") -> str:
    """Classify a driver failure into a stable token safe to log and alert on.

    Derived from the error number and the SQLSTATE ONLY - never from the message - so
    the result carries no host name, no account and no data value, and is identical for
    every occurrence of the same fault.

    Args:
        errno: the driver's error number, as text or as an integer.
        sql_state: the driver's SQLSTATE, used only for the duplicate-key case the
            bridge itself recognises [copybooks/mysql-procedures.cpy:L99].

    Returns:
        One of the tokens of :data:`_LOG_CATEGORY_BY_ERRNO`, or ``"duplicate-key"``,
        ``"lock"`` or :data:`LOG_CATEGORY_UNCLASSIFIED`.

    Examples:
        The number may arrive as an ``int`` or as text, because the bridge carries it
        as text:

        >>> db_error_log_category(1045)
        'access-denied'
        >>> db_error_log_category("1062")
        'duplicate-key'
        >>> db_error_log_category("1036")
        'lock'

        An unrecognised number is categorised rather than dropped:

        >>> db_error_log_category(0)
        'unclassified'
    """
    number = str(errno).strip()
    if number in DUPLICATE_KEY_ERRNOS or sql_state.strip() == DUPLICATE_KEY_SQLSTATE:
        return "duplicate-key"
    if number in LOCK_ERRNOS:
        return "lock"
    return _LOG_CATEGORY_BY_ERRNO.get(number, LOG_CATEGORY_UNCLASSIFIED)


#  THE SAFE-EVENT SCHEMA
#  =====================
#  ONE allowlist, published once, applied by every diagnostic site in
#  `acas_posting.dal` and `acas_posting.programs`. It exists because the same
#  three mistakes were being made independently at 400-odd sites: business data
#  reaching a log record (CWE-532), driver text reaching one unescaped or
#  unbounded (CWE-117), and the same failure being reported two or three times
#  by successive layers.
#
#  WHAT A RECORD MAY CARRY - and nothing else:
#    * a program-id, bridge name, handler name or paragraph name; all are
#      compile-time constants of this migration;
#    * a frozen-source locator, likewise constant;
#    * `FS-Reply`, `We-Error`, `File-Function`, `Access-Type`,
#      `ws-Log-System`, `WS-Log-File-No` and `ws-No-Paragraph` - small closed
#      integer vocabularies declared in this module;
#    * `SQL-State` and the driver's error number, each control-escaped and cut
#      to its picture width, plus the stable `db_error_log_category` token;
#    * record-layout LENGTH constants and row COUNTS.
#
#  WHAT A RECORD MAY NEVER CARRY: statement text or any fragment of one, a
#  WHERE clause, a host-variable value, `WS-File-Key` or any other record key,
#  an account / batch / posting / invoice / customer / supplier identifier, a
#  name, a monetary or quantity value, `WS-Log-Where`, `SQL-Msg`, any field of
#  `RDB-Data`, a filesystem path, or a Python traceback. DEBUG IS NOT AN
#  EXEMPTION: a level is a routing decision, not a confidentiality boundary,
#  and the frozen `SW-Testing` switch is hardcoded to 1
#  [copybooks/Test-Data-Flags.cob], so the trace level is always on in
#  practice.
#
#  NONE OF THIS IS A DISPOSITION. No function below returns a value, sets a
#  status, or reads one for any purpose other than rendering it. Rule R-3
#  forbids logging from adding behaviour, so every one of them returns `None`,
#  raises nothing, and touches exactly one caller-owned field - the
#  `Log-File-Rec-Written` counter the frozen `fhlogger` owns, and only in the
#  adapter the frozen source calls `fhlogger` from.

#: The modulus that keeps ``Log-File-Rec-Written`` inside its picture.
#:
#: ``03  Log-File-Rec-Written     pic 9(6) value zero.``
#: [copybooks/Test-Data-Flags.cob:L18] - six digits, so the field wraps at a
#: million rather than growing without bound. ``common/fhlogger.cbl`` owns the
#: counter and is out of scope (Agent Action Plan section 0.2.2), so the wrap is
#: reproduced here, in the one adapter that stands in for it, rather than
#: re-derived at each of the twenty call sites.
FH_LOG_REC_MODULUS: Final[int] = 1_000_000

#: The single level every ``fhlogger`` stand-in record is emitted at.
#:
#: ``fhlogger`` appends a trace line for every file operation whether or not it
#: succeeded - the callers guard it with ``if Testing-1`` and nothing else - so
#: it is instrumentation, not a failure report, and one level for all of it is
#: the honest rendering. A failure additionally produces its own ERROR through
#: :func:`log_handler_failure`; the trace never doubles as one.
FH_LOG_LEVEL: Final[int] = logging.DEBUG


def _safe_token(text: str, width: int) -> str:
    """Render one short frozen-vocabulary field for a log record.

    Args:
        text: the field value. May be padded, may be empty.
        width: the field's picture width, used as the elision limit.

    Returns:
        The stripped, control-escaped value, or ``"-"`` when it is blank, so
        that an absent field reads as absent rather than as an empty gap.

        >>> _safe_token(" 1062 ", 5)
        '1062'
        >>> _safe_token("     ", 5)
        '-'
        >>> _safe_token("23\\r\\n000", 20)
        '23\\\\x0d\\\\x0a000'
    """
    stripped = text.strip()
    if not stripped:
        return "-"
    return sanitise_for_log(stripped, limit=width)


def _optional_int(value: int | None) -> str:
    """Render an optional small integer field, or ``"-"`` when it is absent."""
    return "-" if value is None else str(int(value))


def log_file_handler_record(
    logger: logging.Logger,
    *,
    program: str,
    paragraph: str,
    log_system: int | None = None,
    log_file_no: int | None = None,
    no_paragraph: int | None = None,
    file_function: int | None = None,
    access_type: int | None = None,
    fs_reply: int | None = None,
    we_error: int | None = None,
    sql_err: str = "",
    sql_state: str = "",
    dal_common: object | None = None,
) -> None:
    """Stand in for one ``call "fhlogger"``, safely and identically everywhere.

    THE ONE ADAPTER. ``common/fhlogger.cbl`` is out of scope (Agent Action Plan
    section 0.2.2 lists it under non-posting utilities) and rule R-1 forbids
    invoking it, so every handler that reaches ``call "fhlogger" using
    File-Access ACAS-DAL-Common-data`` calls this instead. Routing all twenty
    through one function is what makes the field set, the level and the counter
    arithmetic identical rather than twenty independent readings of the same
    paragraph.

    THE FIELD SET IS THE FROZEN ONE, MINUS THREE. ``Logging-Data``
    [copybooks/wsfnctn.cob:L44-L55] has eleven fields. Eight are reported here.
    Three are deliberately omitted and their omission is the point:

    * ``WS-File-Key pic x(64)`` [:L52] is the RECORD KEY - an account number, a
      batch number, an invoice number or a customer code depending on the
      handler. It identifies a business entity and never reaches a log record.
    * ``WS-Log-Where pic x(231)`` [:L53] is free text the caller composes, so
      its content cannot be reasoned about from here.
    * ``SQL-Msg pic x(512)`` [:L50] is the driver's own message, which can name
      the account and can carry a line feed. The stable
      :func:`db_error_log_category` token and the SQLSTATE carry the
      diagnostic value without either hazard.

    ``Accept-Reply`` [:L45] is not a diagnostic at all - it is the keystroke of
    an acknowledgement pause, and section 0.3.4 drops those - and
    ``WS-Count-Rows`` [:L54] belongs to ``Delete-All`` reporting rather than to
    the trace, so neither appears in the parameter list.

    THE COUNTER. ``Log-File-Rec-Written`` [copybooks/Test-Data-Flags.cob:L18]
    advances by one, modulo :data:`FH_LOG_REC_MODULUS`, exactly once per call -
    that is, once per record the frozen source would have appended. It is
    advanced BEFORE the emit and independently of ``logger``'s effective level,
    because it is a COBOL-semantic field of the caller's record and must hold
    the same value whether or not a Python handler happens to be attached
    (rule R-3). Callers must therefore call this function only where the frozen
    source performs its log paragraph - inside the ``if Testing-1`` guard - and
    never unconditionally.

    Args:
        logger: the calling module's logger, so the record carries that
            module's name rather than this one's.
        program: the handler or bridge program-id, e.g. ``"acas006"``.
        paragraph: the frozen paragraph the trace belongs to.
        log_system: ``ws-Log-System`` [:L47]; see :class:`LogSystem`.
        log_file_no: ``WS-Log-File-No`` [:L54].
        no_paragraph: ``ws-No-Paragraph`` [:L48].
        file_function: ``File-Function``; see :class:`FileFunction`.
        access_type: ``Access-Type``; see :class:`AccessType`.
        fs_reply: ``Fs-Reply`` [copybooks/wsfnctn.cob:L24].
        we_error: ``We-Error`` [:L22].
        sql_err: ``SQL-Err pic x(5)`` [:L49] - the driver's error number.
        sql_state: ``SQL-State pic x(5)`` [:L51].
        dal_common: the ``ACAS-DAL-Common-data`` record whose
            ``log_file_rec_written`` field is advanced. ``None`` skips the
            advance, for the handlers whose frozen call site passes only
            ``File-Access``.

    Returns:
        ``None``. Nothing is raised and no status is touched.
    """
    if dal_common is not None:
        written = getattr(dal_common, "log_file_rec_written", None)
        if written is not None:
            dal_common.log_file_rec_written = (  # type: ignore[attr-defined]
                int(written) + 1
            ) % FH_LOG_REC_MODULUS

    logger.log(
        FH_LOG_LEVEL,
        "fhlogger %s %s: system=%s file=%s para=%s fn=%s access=%s "
        "fs-reply=%s we-error=%s errno=%s sqlstate=%s category=%s",
        program,
        paragraph,
        _optional_int(log_system),
        _optional_int(log_file_no),
        _optional_int(no_paragraph),
        _optional_int(file_function),
        _optional_int(access_type),
        _optional_int(fs_reply),
        _optional_int(we_error),
        _safe_token(sql_err, SQL_ERR_WIDTH),
        _safe_token(sql_state, SQL_STATE_WIDTH),
        db_error_log_category(sql_err.strip(), sql_state.strip()),
    )


def log_handler_failure(
    logger: logging.Logger,
    *,
    program: str,
    paragraph: str,
    locator: str = "",
    fs_reply: int | None = None,
    we_error: int | None = None,
    sql_err: str = "",
    sql_state: str = "",
    detail: str = "",
) -> None:
    """Emit THE one operator record for a file-handler or bridge failure.

    One failure, one record, at ERROR. A failure is a failure at every layer it
    passes through, so the level does not vary with the layer, and the layers
    below the one that reports do not report at all - they return their status
    and stay quiet. That is what keeps a single fault from producing three log
    lines that an operator must correlate.

    NO FREE-FORM TEXT REACHES THE RECORD. ``detail`` is for a caller-side
    CONSTANT - the frozen message identifier, the condition the source names -
    and never for driver text, a statement, a key or a value. The driver's own
    contribution is limited to its error number and SQLSTATE, each escaped and
    cut to its picture width, plus the stable category token.

    Args:
        logger: the calling module's logger.
        program: the handler or bridge program-id.
        paragraph: the frozen paragraph that detected the failure.
        locator: the frozen-source locator, e.g.
            ``"[common/acas006.cbl:L425-L432]"``.
        fs_reply: ``Fs-Reply`` as the handler left it.
        we_error: ``We-Error`` as the handler left it.
        sql_err: the driver's error number, from ``SQL-Err``.
        sql_state: the driver's SQLSTATE, from ``SQL-State``.
        detail: an allowlisted constant clause, or empty.

    Returns:
        ``None``. Control flow is the caller's; this reports and returns.
    """
    logger.error(
        "%s %s failed%s%s: fs-reply=%s we-error=%s errno=%s sqlstate=%s "
        "category=%s",
        program,
        paragraph,
        (" - " + detail) if detail else "",
        (" " + locator) if locator else "",
        _optional_int(fs_reply),
        _optional_int(we_error),
        _safe_token(sql_err, SQL_ERR_WIDTH),
        _safe_token(sql_state, SQL_STATE_WIDTH),
        db_error_log_category(sql_err.strip(), sql_state.strip()),
    )


def log_cobol_stop(
    logger: logging.Logger,
    *,
    program: str,
    paragraph: str,
    literal: str,
    locator: str,
) -> None:
    """Report one reached ``STOP "literal"`` site, uniformly across the cycle.

    Six of the seventeen handlers carry a ``stop "Cobol File EOF"`` on their
    flat-file branch, several marked ``*> for testing`` by the maintainer. A
    ``STOP`` with a literal displays it and BLOCKS until the operator presses a
    key, so it is two things at once: a diagnostic, which section 0.3.4 turns
    into a log record, and an acknowledgement pause, which section 0.3.4 drops.
    The transfer that follows it in the frozen source is the caller's to
    reproduce and is not affected by this call.

    IT IS A FAILURE, SO IT IS AN ERROR - everywhere, once. Reaching a
    debugging stop in a shipped handler is the strongest signal the frozen
    source emits; reporting it at INFO or DEBUG in some handlers and WARNING or
    ERROR in others made the same event unfindable, which is the defect this
    function removes.

    Args:
        logger: the calling module's logger.
        program: the handler program-id.
        paragraph: the frozen paragraph holding the ``STOP``.
        literal: the ``STOP`` literal, verbatim. A frozen constant, never
            interpolated data.
        locator: the frozen-source locator of the ``STOP``.

    Returns:
        ``None``.
    """
    logger.error(
        "%s %s reached STOP %r %s - the diagnostic is recorded, the operator "
        "pause is not reproduced (Agent Action Plan section 0.3.4); the "
        "transfer the frozen source makes next is preserved",
        program,
        paragraph,
        literal,
        locator,
    )


@dataclass(frozen=True, slots=True)
class DbErrorStatus:
    """The outcome of mapping one driver failure onto the ACAS status protocol.

    Frozen, because a status is a fact about something that already happened. Callers
    that need it in a record apply it with :meth:`apply_to_logging_data`.
    """

    fs_reply: FsReply

    #: `We-Error` [copybooks/wsfnctn.cob:L23].
    we_error: int

    sql_err: str

    sql_msg: str

    sql_state: str

    #: ``True`` if the duplicate-key early exit was taken, i.e. if `go to
    #: Mysql-1190-Exit` [copybooks/mysql-procedures.cpy:L104] fired.
    duplicate_key: bool

    def apply_to_logging_data(self, logging_data: LoggingData) -> None:
        """Write the three diagnostic fields into a ``Logging-Data`` block.

        Reproduces what the bridge-level error path leaves in the record: ``SQL-Err``,
        ``SQL-Msg`` and ``SQL-State`` all populated [common/glpostingMT.cbl:L813-L817].

        Args:
            logging_data: The ``LoggingData`` instance to update, owned by
                ``records/file_access.py``. Mutated in place, as the COBOL ``MOVE``
                statements mutate the record.
        """
        logging_data.sql_err = self.sql_err
        logging_data.sql_msg = self.sql_msg
        logging_data.sql_state = self.sql_state


def mysql_1100_db_error(
    *,
    errno: str,
    message: str,
    sql_state: str,
    command: str,
    we_error: int = WeError.SUCCESS,
) -> DbErrorStatus:
    """Map a driver failure to a status pair, as ``Mysql-1100-Db-Error`` does.

    Reproduces [copybooks/mysql-procedures.cpy:L96-L128], the paragraph every one of the
    twenty in-scope bridges reaches for on any failed statement - ``Mysql-1210-Command``
    performs it at [:L176], and ``Mysql-1200-Select``, ``Mysql-1220-Store-Result``,
    ``Mysql-1240-Switch-Db`` and ``Mysql-1000-Open`` all do the same.

    Args:
        errno: The driver's error number AS TEXT - see :data:`DUPLICATE_KEY_ERRNOS` for
            why text and not an integer.
        message: The driver's error message, the equivalent of ``Ws-Mysql-Error-
            Message``. Truncated to 512 characters on the way into ``SQL-Msg``.
        sql_state: The driver's SQLSTATE, the equivalent of ``WS-MYSQL-SqlState``.
        command: The statement text that failed. Consulted ONLY by the duplicate test,
            and only its first six characters.
        we_error: The value ``We-Error`` already holds. Returned unchanged on the
            duplicate path, because the COBOL jump skips the statement that would
            overwrite it.

    Returns:
        A :class:`DbErrorStatus` with the fields already fitted to their picture widths.

    Examples:
        The duplicate path, which is the one the frozen ``evaluate`` narrows to
        ``INSERT``:

        >>> status = mysql_1100_db_error(
        ...     errno="1062",
        ...     message="Duplicate entry '1' for key 'PRIMARY'",
        ...     sql_state="23000",
        ...     command="INSERT INTO GLPOSTING-REC VALUES (1)",
        ... )
        >>> status.fs_reply
        <FsReply.DUPLICATE_KEY: 22>
        >>> status.duplicate_key
        True
    """
    fitted_err = _pic_x(errno, SQL_ERR_WIDTH)
    fitted_msg = _pic_x(message, SQL_MSG_WIDTH)
    fitted_state = _pic_x(sql_state, SQL_STATE_WIDTH)

    # OUTCOME 1: `if Ws-Mysql-Error-Number = "1062" or = "1022"` with the INSERT-only
    # `evaluate` [copybooks/mysql-procedures.cpy:L99-L105], then `move 22 to fs-Reply`
    # [:L103] and `go to Mysql-1190-Exit` [:L104].
    if is_duplicate_key_driver_level(errno, command):
        return DbErrorStatus(
            fs_reply=FsReply.DUPLICATE_KEY,
            we_error=we_error,
            sql_err=fitted_err,
            sql_msg=fitted_msg,
            sql_state=fitted_state,
            duplicate_key=True,
        )

    # OUTCOME 2: the fall-through. Note what does NOT happen between the duplicate test
    # and the two moves below.
    status = DbErrorStatus(
        fs_reply=FsReply.ERROR,
        we_error=WeError.RDB_INIT_ERROR,
        sql_err=fitted_err,
        sql_msg=fitted_msg,
        sql_state=fitted_state,
        duplicate_key=False,
    )

    # Stands in for `Mysql-1110-Report-Problem`
    # [copybooks/mysql-procedures.cpy:L130-L137]: two displays become one log
    # record and the blocking `accept` at [:L136] is dropped. Control flow is
    # untouched - this returns normally either way.
    #
    # THIS IS THE ONE OPERATOR RECORD FOR A DRIVER FAILURE. It sits here, at the
    # layer that turns the driver's error into the ACAS status pair, because that
    # is where the frozen source reports it. The handlers above therefore report
    # NOTHING for the same fault: a caller that logged again would produce two or
    # three lines an operator has to correlate, for one failure.
    #
    # TYPED FIELDS ONLY - NO DRIVER TEXT. The two ACAS status values are
    # interpolated as themselves: they are integers drawn from this module's own
    # enumerations, so neither can carry a control character or an identity. The
    # driver's SQLSTATE and error number are short closed-vocabulary fields and
    # are escaped and cut to their picture widths; the number is additionally
    # reported as the stable `db_error_log_category` token, which is derived from
    # the number and the SQLSTATE alone and is therefore identical for every
    # occurrence of the same fault and greppable as such.
    #
    # `message` IS DELIBERATELY NOT LOGGED. It is `SQL-Msg pic x(512)`
    # [copybooks/wsfnctn.cob:L50] - the driver's own free text, which names the
    # account on an access denial, echoes the failing statement and its literal
    # values on a constraint violation, and can carry a carriage return that
    # forges a second log record (CWE-117, CWE-532). Redacting it was not enough:
    # the rules of `redact_for_log` recognise the connection-message shapes and
    # cannot recognise an arbitrary SQL literal or row key. The category token
    # above carries the diagnostic value without the payload. The `DbErrorStatus`
    # returned below still carries all three driver fields exactly as the driver
    # produced them, fitted only to their picture widths, so the caller's own
    # `SQL-Msg` field is unaffected and nothing about the status changes.
    _LOG.error(
        "ACAS file handler: FS-Reply=%d WE-Error=%d SQLSTATE=%s errno=%s "
        "category=%s "
        "[reproduces the unconditional (99, 911) of "
        "copybooks/mysql-procedures.cpy:L127-L128 - WE-Error 911 is a "
        "catch-all here, not evidence of a connect failure]",
        int(status.fs_reply),
        int(status.we_error),
        sanitise_for_log(sql_state, limit=SQL_STATE_WIDTH),
        sanitise_for_log(errno, limit=SQL_ERR_WIDTH),
        db_error_log_category(errno, sql_state),
    )
    return status


#: The per-operation narrowings of the 911 catch-all - the SECOND stage of anomaly N3.
#: Two of the bridge's operations refuse to leave 911 in place.
WE_ERROR_OVERRIDE_BY_FILE_FUNCTION: Final[Mapping[FileFunction, WeError]] = (
    MappingProxyType(
        {
            FileFunction.DELETE: WeError.DELETE_SQLSTATE_NOT_00000,
            FileFunction.RE_WRITE: WeError.REWRITE_SQLSTATE_NOT_00000,
        }
    )
)


def override_we_error_for_operation(
    status: DbErrorStatus, file_function: int
) -> DbErrorStatus:
    """Apply the per-operation ``We-Error`` narrowing, if the verb has one.

    The second stage of anomaly N3. :func:`mysql_1100_db_error` reports 911 for
    everything; delete and rewrite then replace it with 995 and 994 respectively, AFTER
    the generic paragraph has returned [common/glpostingMT.cbl:L874-L875] and
    [:L1001-L1002].

    Args:
        status: The result of :func:`mysql_1100_db_error`.
        file_function: The ``File-Function`` value of the operation that failed.

    Returns:
        A new :class:`DbErrorStatus` with the narrowed code, or ``status`` itself when
            the verb has no override.
    """
    if status.duplicate_key:
        return status
    try:
        verb = FileFunction(int(file_function))
    except ValueError:
        return status
    narrowed = WE_ERROR_OVERRIDE_BY_FILE_FUNCTION.get(verb)
    if narrowed is None:
        return status
    return DbErrorStatus(
        fs_reply=FsReply.ERROR,
        we_error=narrowed,
        sql_err=status.sql_err,
        sql_msg=status.sql_msg,
        sql_state=status.sql_state,
        duplicate_key=False,
    )


# [copybooks/mysql-procedures.cpy:L209-L255] is a working four-rung backoff over three
# lock errnos that is never called.

#: The three MySQL error numbers the dead ladder would have treated as recoverable
#: locks, with the frozen source's own comments `not = "1027" *> HY000 - Locked against
#: change`, `not = "1036" *> HY000 - Table Read Only`, `not = "1099" *> HY000 - Locked
#: with Read lock`, falling through to `go to Mysql-1390-Exit.
LOCK_ERRNOS: Final[frozenset[str]] = frozenset({"1027", "1036", "1099"})


@dataclass(frozen=True, slots=True)
class LockRetryRung:
    """One rung of the dead lock-retry ladder of anomaly N1.

    A description of a wait, NOT a wait. Nothing in this class or in
    :func:`mysql_1300_db_error` blocks: the duration is data the caller may inspect, and
    rule R-6 forbids this module from depending on wall-clock time.
    """

    time_step_before: int

    #: The value it ratchets the step to.
    time_step_after: int

    #: The wait in INTEGER NANOSECONDS, or ``None`` when the frozen source expresses
    #: this rung in whole seconds instead.
    nanoseconds: int | None

    seconds: int | None

    #: The foreign routine the rung would have called. Recorded for traceability and
    #: NEVER invoked - rule R-1 admits no out-of-process call from this package.
    routine: str

    #: The blinking status line the rung would have displayed, or ``None`` for the first
    #: rung, which displays nothing.
    display: str | None

    locator: str


LOCK_RETRY_LADDER: Final[tuple[LockRetryRung, ...]] = (
    LockRetryRung(
        time_step_before=0,
        time_step_after=1,
        nanoseconds=250000000,
        seconds=None,
        routine="CBL_OC_NANOSLEEP",
        display=None,
        locator="[copybooks/mysql-procedures.cpy:L223-L225]",
    ),
    LockRetryRung(
        time_step_before=1,
        time_step_after=2,
        nanoseconds=500000000,
        seconds=None,
        routine="CBL_OC_NANOSLEEP",
        display="Waiting < sec ",
        locator="[copybooks/mysql-procedures.cpy:L227-L230]",
    ),
    LockRetryRung(
        time_step_before=2,
        time_step_after=4,
        nanoseconds=None,
        seconds=1,
        routine="C$SLEEP",
        display="Waiting 1 sec ",
        locator="[copybooks/mysql-procedures.cpy:L233-L236]",
    ),
    LockRetryRung(
        time_step_before=4,
        time_step_after=8,
        nanoseconds=None,
        seconds=5,
        routine="C$SLEEP",
        display="Waiting 5 secs",
        locator="[copybooks/mysql-procedures.cpy:L239-L242]",
    ),
)


def is_lock_errno(errno: str) -> bool:
    """Report whether an error number is one the dead ladder would have caught.

    The predicate exists to make anomaly N1 assertable, not to change any behaviour. A
    ``True`` answer changes NOTHING about the status a caller reports.

    Args:
        errno: The driver's error number as text.

    Returns:
        ``True`` for ``"1027"``, ``"1036"`` or ``"1099"``
            [copybooks/mysql-procedures.cpy:L218-L220].
    """
    return errno in LOCK_ERRNOS


def mysql_1300_db_error(
    errno: str, time_step: int
) -> tuple[int, LockRetryRung | None, tuple[FsReply, WeError] | None]:
    """DEAD CODE, reproduced unreachable: see [copybooks/mysql-procedures.cpy:L167].

    Reproduces ``Mysql-1300-DB-Error`` [copybooks/mysql-procedures.cpy:L209-L255]. the
    repository is commented out at [:L167], so no live COBOL path reaches it, and
    reproducing this defect means keeping the Python equivalent equally unreached: it
    has zero call sites in ``acas_posting`` and must keep zero.

    Args:
        errno: The driver's error number as text, standing in for the result of ``call
            "MySQL_errno"`` at [:L217].
        time_step: The current ``WS-Mysql-Time-Step``
            [copybooks/mysql-variables.cpy:L105]. Zero on a fresh connection.

    Returns:
        A triple ``(next_time_step, rung, exhausted_status)``: * ``next_time_step`` -
            the ratcheted step to carry to the next call, unchanged when nothing
            matched.
    """
    # L215: `move zero to WS-SQL-Retry.` The flag is cleared on entry.
    if not is_lock_errno(errno):
        return time_step, None, None

    # L223-L242: the nested `if` chain over WS-Mysql-Time-Step.
    for rung in LOCK_RETRY_LADDER:
        if time_step == rung.time_step_before:
            return rung.time_step_after, rung, None

    return time_step, None, (FsReply.ERROR, WeError.TABLE_LOCKED)


# A caution that governs this whole section: THE COBOL DOES NOT RAISE.


class AcasFileHandlerError(Exception):
    """A file-handler status the frozen source treats as unrecoverable.

    Open-Error-Continued. *> If here we cannot continue as its a major failure ...
    displays ... accept Accept-Reply at 1335. goback.
    """

    def __init__(
        self,
        fs_reply: int,
        we_error: int = WeError.SUCCESS,
        *,
        operation: str = "",
        table: str = "",
    ) -> None:
        """Record the status pair and the context it arose in.

        Args:
            fs_reply: The ``FS-Reply`` value that triggered the hard exit.
            we_error: The accompanying ``We-Error`` detail code.
            operation: Optional description of the verb being attempted, for the message
                only.
            table: Optional name of the table involved, for the message only.
        """
        self.fs_reply = int(fs_reply)
        self.we_error = int(we_error)
        self.operation = operation
        self.table = table
        context = "".join(
            (
                f" during {operation}" if operation else "",
                f" on {table}" if table else "",
            )
        )
        super().__init__(
            f"ACAS file handler failed{context}: "
            f"FS-Reply={self.fs_reply} WE-Error={self.we_error}"
        )


class AcasFileHandlerFatalError(AcasFileHandlerError):
    """The ``We-Error 901`` disposition: stop the run, fix the source.

    A subclass rather than a separate type because the frozen source treats it as a more
    severe case of the same thing, and a caller that wants to catch either can catch the
    base.
    """


def is_ok(fs_reply: int) -> bool:
    """Report whether a reply means the operation completed successfully.

    This is the normal way to test a reply, and it returns rather than raises because
    that is what the COBOL does at every one of its several hundred test sites.

    Args:
        fs_reply: An ``FS-Reply`` value; a plain ``int`` is accepted because that is
            what ``FileAccess.fs_reply`` holds.

    Returns:
        ``True`` only if the value is zero.

    Examples:
        >>> is_ok(FsReply.SUCCESS), is_ok(0)
        (True, True)
        >>> is_ok(FsReply.END_OF_FILE), is_ok(FsReply.ERROR)
        (False, False)
    """
    return int(fs_reply) == FsReply.SUCCESS


def raise_for_status(
    fs_reply: int,
    we_error: int = WeError.SUCCESS,
    *,
    operation: str = "",
    table: str = "",
) -> None:
    """Guard for the two places the frozen source hard-exits. OPT-IN ONLY.

    exception mechanism: every handler leaves its status in the record and every caller
    tests it inline with :func:`is_ok` and decides for itself.

    Args:
        fs_reply: The ``FS-Reply`` value to test.
        we_error: The accompanying ``We-Error``. A value of 901 selects
            :class:`AcasFileHandlerFatalError`.
        operation: Optional verb description, carried into the message.
        table: Optional table name, carried into the message.

    Returns:
        ``None``, when the reply is zero.

    Raises:
        AcasFileHandlerFatalError: If ``we_error`` is ``WeError.RECORD_SIZE_MISMATCH``
            (901), whatever the reply - because the handler that sets 901 stops the run
            on the strength of the detail code alone, testing ``if WE-Error = 901``
            [common/acas008.cbl:L537].
        AcasFileHandlerError: If the reply is any other non-zero value, reproducing ``if
            fs-reply not = zero`` followed by ``goback``.

    Examples:
        A zero reply returns, and returns nothing:

        >>> raise_for_status(FsReply.SUCCESS) is None
        True

        A non-zero reply raises, and the message carries both codes:

        >>> raise_for_status(FsReply.ERROR, WeError.RDB_INIT_ERROR)
        Traceback (most recent call last):
        ...
        acas_posting.dal.status.AcasFileHandlerError: ACAS file handler failed: \
FS-Reply=99 WE-Error=911

        And 901 selects the fatal subclass on the strength of the detail code alone,
        even though the reply here is zero:

        >>> raise_for_status(0, WeError.RECORD_SIZE_MISMATCH)
        Traceback (most recent call last):
        ...
        acas_posting.dal.status.AcasFileHandlerFatalError: ACAS file handler failed: \
FS-Reply=0 WE-Error=901
    """
    # `if WE-Error = 901` [common/acas008.cbl:L537] - tested on the detail code alone,
    # before and independently of the reply, because a length mismatch is a programming
    # error that no reply value can excuse.
    if int(we_error) == WeError.RECORD_SIZE_MISMATCH:
        raise AcasFileHandlerFatalError(
            fs_reply, we_error, operation=operation, table=table
        )

    if not is_ok(fs_reply):
        raise AcasFileHandlerError(
            fs_reply, we_error, operation=operation, table=table
        )


# `03 Logging-Data.` [copybooks/wsfnctn.cob:L44-L55].


class LogSystem(enum.IntEnum):
    """``ws-Log-System`` values - which subsystem is logging.

    The first lists a value 0 for the parameter files and ends with a trailing ``4 FH
    logging`` that duplicates the number already assigned to Purchase; the second omits
    0 altogether and starts at 1.
    """

    #: `0 = Params` [common/acas000.cbl:L324] - the system parameter files, which is why
    #: `acas000` sets it.
    PARAMS = 0

    IRS = 1

    GL = 2

    SL = 3

    PL = 4

    STOCK = 5


class ConnectStep(enum.IntEnum):
    """``ws-No-Paragraph`` values for the three steps of opening a connection.

    i.e. the value is set immediately before the error report rather than at the top of
    each step, so that a successful open leaves the caller's own paragraph number in the
    field undisturbed.
    """

    #: `MySQL_init` failed - `move 101 to Ws-No-Paragraph`
    #: [copybooks/mysql-procedures.cpy:L68], guarded by the return-code test at [:L67]. The
    #: driver could not be initialised at all.
    INIT = 101

    #: `MySQL_real_connect` failed - `move 102 to Ws-No-Paragraph`
    #: [copybooks/mysql-procedures.cpy:L79], guarded by [:L78]. Host, user, password, port or
    #: socket is wrong, or the server is unreachable.
    REAL_CONNECT = 102

    #: `MySQL_selectdb` failed - `move 103 to Ws-No-Paragraph`
    #: [copybooks/mysql-procedures.cpy:L84], guarded by [:L83]. Connected, but the schema named
    #: in `DB- Schema` could not be selected.
    SELECT_DB = 103
