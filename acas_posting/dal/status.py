"""ACAS file-handler status protocol and operation vocabulary.

WHAT THIS MODULE OWNS
=====================
Two things, for the whole migrated cycle:

* the **status protocol** - the ``FS-Reply`` value set, the ``We-Error`` code
  set, the SQLSTATE vocabulary, and the mapping from a driver error to that
  pair; and
* the **operation vocabulary** - the ``File-Function`` codes and the
  ``Access-Type`` codes, plus the START relation those access types double as.

It is the deepest module of ``acas_posting.dal``: it imports nothing from
``dal`` and nothing from ``cobol``, so every other data-access module can
depend on it with no possibility of a cycle.

WHY IT EXISTS AT ALL: THE TWO-WAY SPLIT OF ONE COPYBOOK
=======================================================
One COBOL copybook, ``copybooks/wsfnctn.cob``, mixes a record layout with an
operation vocabulary, so a single ``COPY`` becomes two imports. Agent Action
Plan section 0.4.3 gives the contract verbatim::

    FROM:  copy "wsfnctn.cob".
    TO:    from acas_posting.records.file_access import FileAccess, RdbData, LoggingData
           from acas_posting.dal.status import FsReply, FileFunction, AccessType

So the division of labour is fixed and total: ``records/file_access.py`` owns
the record SHAPE (``FileAccess``, ``LoggingData``, ``RdbData``,
``FaRdbmsFlatStatuses``, ``CursParts``, ``Curs2Parts``),
``cobol/condition_names.py`` owns the ``88``-level PREDICATES (``is_fn_open``
and its fourteen siblings), and THIS module owns the VALUES those names stand
for plus the behaviour that turns a driver error into an ACAS status pair.
Neither of the other two is ever redeclared here.

PROVENANCE, AND A CORRECTION TO THE CITED SPANS
===============================================
Every locator below is traced to this checkout rather than copied forward,
because rule R-5 makes a wrong locator a traceability defect.

* ``copybooks/wsfnctn.cob`` is **117 lines**. The Agent Action Plan cites
  ``L23-L38``, ``L57-L64`` and ``L88-L118``; all three are approximate and the
  last runs one line past end of file. The spans in this checkout are
  ``L22-L26`` (status fields), ``L44-L55`` (``Logging-Data``), ``L56-L62``
  (``RDB-Data``), ``L88-L105`` (``File-Function`` and its fifteen ``88``
  levels) and ``L107-L116`` (``Access-Type`` and its nine).
* The authoritative status table is the module-usage block of the generated
  bridge, ``common/glpostingMT.cbl:L125-L158`` - prose in a comment, not code.
  Neither ``Fs-Reply`` nor ``We-Error`` carries a single ``88``-level condition
  name anywhere in the frozen source, so every symbolic name here is OURS,
  derived from that prose; there are none to look up.
* Two copybooks the Agent Action Plan does not cite are the real specification
  for the error path: ``copybooks/mysql-procedures.cpy`` and
  ``copybooks/mysql-variables.cpy``, ``COPY``d by twenty of the twenty
  in-scope bridges and holding the code that actually sets the status pair.
  Their line numbers in the briefing material run one to two lines out; the
  numbers below are read from the checkout.

A MISSING BUILD INPUT, RECORDED AND NOT INVENTED
================================================
``common/glpostingMT.cbl:L160`` carries an **uncommented** directive::

     copy "ACAS-SQLstate-error-list.cob".

That copybook **does not exist anywhere in the checkout** - a search of the
whole tree returns zero hits - so the twenty-two bridges that reference it
cannot be compiled as they stand. It is a second missing build input alongside
the bridge's C interface object, which Agent Action Plan section 0.5.2 records
as having no build rule. Whatever SQLSTATE-to-status detail it holds is
therefore **unavailable** and none of it is invented here: this module
reproduces only the SQLSTATE behaviour present in the frozen source, namely
the duplicate tests of section "DUPLICATE KEY" below.

THE ANOMALIES REPRODUCED HERE (RULE R-4)
========================================
Agent Action Plan section 0.8.2, verbatim, is the whole engagement in one
sentence:

    "There is no test suite: compiled COBOL execution is the behavioral
    specification, defects included. A defect reproduced is correct; a defect
    fixed is a failure."

Six anomalies live in this module's remit. Each is reproduced, never
corrected, and each is stated IN FULL - with every locator - in a comment at
the site that reproduces it, per Agent Action Plan section 0.7.4 conflict C-4.
This is the index; the sites are authoritative. Every one is also destined for
the migration anomaly log, which a later boundary creates.

N1  The lock-retry backoff ladder is dead code, so ``We-Error 910`` is
    unreachable and a table lock is misreported. See ``LOCK_RETRY_LADDER``.
N2  ``FS-Reply 23`` is documented by every bridge and produced by only seven
    of the twenty. See ``FsReply.KEY_NOT_FOUND``.
N3  ``We-Error 911`` is a catch-all, not the connect failure it is documented
    as. See ``mysql_1100_db_error``.
N4  The documented SQLSTATE map was never implemented. See
    ``DOCUMENTED_SQLSTATE_MAPPINGS``.
N5  The ``Access-Type 9`` relation arm is unreachable behind the START guard.
    See ``START_RELATION_BY_ACCESS_TYPE``.
N6  ``We-Error 992`` has no producer anywhere in the frozen tree. See
    ``DOCUMENTATION_ONLY_WE_ERRORS``.

DELIBERATE OMISSIONS (RULE R-5)
===============================
Rule R-5 requires omissions to be recorded rather than discovered as gaps.

1. **No import of ``acas_posting.cobol``.** ``cobol/condition_names.py``
   offers ``values_for`` and ``specs_for_variable``, which would spare this
   module transcribing the fifteen out-of-order function codes again.
   Declined: the per-directory import table of Agent Action Plan section 0.4.3
   grants no ``dal`` to ``cobol`` edge. The literal values are assigned here
   and the two modules are cross-checked by test.
2. **The interactive tail of ``Mysql-1110-Report-Problem`` is dropped.** That
   paragraph (``copybooks/mysql-procedures.cpy:L130-L137``) displays two
   messages then blocks on ``accept ws-reply`` at ``:L136``. Per Agent Action
   Plan section 0.3.4 the display becomes one log record and the pause - which
   has no database effect - is dropped; control flow is untouched.
3. **One maintainer note is paraphrased rather than quoted.** The bracketed
   note against SQLSTATE ``0200n`` at
   ``copybooks/mysql-procedures.cpy:L112`` proposes deciding between 23 and 10
   by an entropy source. Quoting it would name that entropy source inside a
   module rule R-6 requires to be free of one, and it was never implemented.

RULES R-6, R-2 AND R-1
======================
No clock read, no entropy source, no environment read, no host lookup and no
sleep call appears below - not even in the dead ladder of N1, whose rung
durations are integer data rather than performed waits. Import is side-effect
free and the one dependency on another package is type-checking-only. Every
collection published is an immutable tuple, frozenset or mapping proxy, so
member order is fixed and two runs observe it identically (R-6). Every status
code is an ``int`` and the N1 rung durations are integer nanoseconds and
seconds exactly as the COBOL writes them; no binary floating-point type
appears in any role (R-2). The COBOL error path reaches its driver through
``call "MySQL_errno"``, ``call "MySQL_error"`` and ``call "MySQL_sqlstate"``;
those are reimplemented natively here from what a Python driver exception
already carries, none is invoked, and this module runs on a host with no COBOL
compiler and no COBOL runtime present (R-1).
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
    # `LoggingData` is the record sub-block this module's error results are
    # written into: `SQL-Err`, `SQL-Msg` and `SQL-State` are its fields
    # [copybooks/wsfnctn.cob:L49-L51]. The import is guarded because
    # `records/file_access.py` resolves its field metadata from the generated
    # data dictionary at import time, which reads a file; keeping the import
    # to type-checking time is what lets THIS module stay side-effect free on
    # import (rule R-6). `from __future__ import annotations` makes every
    # annotation below a string, so nothing needs the symbol at runtime.
    from acas_posting.records.file_access import LoggingData

__all__: Final[tuple[str, ...]] = (
    # Ordered isort-style - the SCREAMING_CASE tables, then the classes, then
    # the functions - each group sorted. Note this differs from the plain
    # `sorted()` order used by `records/file_access.py`; that module documents
    # its own choice at its `__all__`, and neither ordering is observable
    # behaviour.
    # The frozen tables derived from the frozen source.
    "DOCUMENTATION_ONLY_WE_ERRORS",
    "DOCUMENTED_SQLSTATE_MAPPINGS",
    "DUPLICATE_KEY_COMMAND_PREFIXES",
    "DUPLICATE_KEY_ERRNOS",
    "DUPLICATE_KEY_SQLSTATE",
    "END_OF_FILE_WE_ERROR",
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
    # The two exceptions, raised only where the COBOL itself transfers
    # control; the four status/vocabulary enumerations; the two
    # `Logging-Data` vocabularies; and the three value objects.
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
    # The behaviour.
    "db_error_log_category",
    "end_of_file_status",
    "implies_fs_reply_error",
    "is_duplicate_key_bridge_level",
    "is_duplicate_key_driver_level",
    "is_lock_errno",
    "is_ok",
    "mysql_1100_db_error",
    "mysql_1300_db_error",
    "override_we_error_for_operation",
    "raise_for_status",
    "redact_for_log",
    "sanitise_for_log",
    "start_access_type_is_valid",
    "start_relation_for",
)

#: Module logger. A library module attaches no handler and configures no root
#: logger; the application decides where diagnostics go. The COBOL equivalent
#: is `Mysql-1110-Report-Problem` [copybooks/mysql-procedures.cpy:L130-L137],
#: which only displays - see "DELIBERATE OMISSIONS" item 2 above.
_LOG: Final[logging.Logger] = logging.getLogger(__name__)

#: The copybook that ``common/glpostingMT.cbl:L160`` copies and that is ABSENT
#: from the checkout. Published as a plain name so that the anomaly log and
#: the traceability document can cite the same string this module does, and so
#: that a future checkout which DOES ship it can be detected by searching for
#: this constant rather than by re-deriving the finding.
#:
#: Its contents are unknown and are deliberately not modelled. See "A MISSING
#: BUILD INPUT, RECORDED AND NOT INVENTED" in the module docstring.
MISSING_SQLSTATE_COPYBOOK: Final[str] = "ACAS-SQLstate-error-list.cob"


#  FS-REPLY - THE FILE-HANDLER REPLY CODE
#  `03  Fs-Reply        pic 99.`              [copybooks/wsfnctn.cob:L25]
#  Two digits, unsigned, and carrying ZERO `88`-level condition names in the
#  frozen source - `cobol/condition_names.py` independently reports a count of
#  0 for this variable. Every name below is therefore OURS, derived from the
#  prose table at [common/glpostingMT.cbl:L125-L131]. There is no COBOL
#  condition name to look up.


class FsReply(enum.IntEnum):
    """The ``FS-Reply`` value set, as the bridges' own prose table defines it.

    ``IntEnum`` and not ``Enum``: ``FileAccess.fs_reply`` is a plain ``int``
    attribute, so a member must compare equal to the raw value a handler
    stores there. ``FsReply.SUCCESS == 0`` has to be true for the record layer
    and this layer to agree without either one converting.

    The six members are exactly the set the Agent Action Plan section 0.4.1.5
    mandates for this module - 0, 10, 21, 22, 23, 99 - and no more. Other
    handlers document values outside it (``common/acas008.cbl:L159`` documents
    ``35 = File not found``), and those are recorded as comments below rather
    than added as members: rule R-3 is that validation and vocabulary are
    copied, never extended, and the mandated set is the one the migrated cycle
    tests against.

        >>> FsReply.SUCCESS == 0
        True
        >>> [int(member) for member in FsReply]
        [0, 10, 21, 22, 23, 99]
    """

    #: `0  = Operation completed successfully` [common/glpostingMT.cbl:L126]
    SUCCESS = 0

    #: `10 = End of (Cobol) File returned to calling module only.`
    #: [common/glpostingMT.cbl:L127]
    #:
    #: ANOMALY-ADJACENT FACT, not a defect but easy to get wrong: at end of
    #: file the bridge sets `We-Error` to 10 as well, rather than leaving it
    #: at zero. `move 10 to fs-Reply WE-Error` is a single statement over both
    #: fields [common/glpostingMT.cbl:L557], and the two-statement form
    #: appears twice more [:L508-L509] and [:L569-L570]. Use
    #: `end_of_file_status()` so the pair is never set half-way.
    END_OF_FILE = 10

    #: `21 = Invalid key on START OR key not found`
    #: [common/glpostingMT.cbl:L128]
    #:
    #: Produced on the START parameter guard together with `We-Error 997`
    #: [common/glpostingMT.cbl:L695-L698], and - see `KEY_NOT_FOUND` below -
    #: ALSO produced by the read-indexed path of seven of the twenty in-scope
    #: bridges where the prose table promises 23, paired there with
    #: `We-Error 990` [:L668-L669] or `We-Error 989` [:L676-L677].
    INVALID_KEY_ON_START = 21

    #: `22 - Attempt to duplicate a key value.`
    #: [common/glpostingMT.cbl:L129] - the dash instead of `=` is the
    #: maintainer's own; the table uses `=` on every other line.
    #:
    #: The only status in the set with two independent producers: the driver
    #: level [copybooks/mysql-procedures.cpy:L99-L105] and the bridge level
    #: [common/glpostingMT.cbl:L818-L824]. They do not agree on their tests -
    #: see `is_duplicate_key_driver_level` and
    #: `is_duplicate_key_bridge_level`.
    DUPLICATE_KEY = 22

    #: `23 = Key not found.     from read indexed` [common/glpostingMT.cbl:L130] *** ANOMALY
    #: N2 - REPRODUCED, NOT FIXED (rule R-4) *** Retained precisely BECAUSE the reference
    #: bridge never produces it: `glpostingMT` has zero `move 23 to fs-reply` sites and
    #: returns 21, the change recorded at both sites - `move 21 to fs-reply *> from 23` with
    #: 990 [common/glpostingMT.cbl:L668-L669] and with 989 [:L676-L677]. The anomaly is that
    #: it reached only SOME bridges. Census of the twenty in-scope bridges: seven return 21
    #: (nominalMT, glpostingMT, glbatchMT, slpostingMT, analMT, irsnominalMT, irspostingMT),
    #: seven return 23 (salesMT, valueMT, slinvoiceMT, otm3MT, purchMT, plinvoiceMT, otm5MT),
    #: six have no keyed read (systemMT, dfltMT, finalMT, sys4MT, irsdfltMT, irsfinalMT). So
    #: one condition answers 21 from a GL or IRS table and 23 from a Sales or Purchase one
    #: while every prose table documents 23.
    KEY_NOT_FOUND = 23

    #: `99 = Indicates an error see WE-Error, SQL-ERR/MSG for more info`
    #: [common/glpostingMT.cbl:L131]
    ERROR = 99


#: The `We-Error` value that accompanies `FsReply.END_OF_FILE`, which is 10
#: and NOT zero - see the note on that member. Named separately because it is
#: the one place in the protocol where a `We-Error` code deliberately collides
#: numerically with an `FS-Reply` code, and a reader meeting a bare `10` in a
#: `We-Error` field is entitled to think it a bug.
#: [common/glpostingMT.cbl:L557]
END_OF_FILE_WE_ERROR: Final[int] = 10


def end_of_file_status() -> tuple[FsReply, int]:
    """Return the end-of-file status pair, ``(10, 10)``.

    Reproduces ``move 10 to fs-Reply WE-Error``
    [common/glpostingMT.cbl:L557] - one statement writing BOTH fields, which
    is why this helper exists rather than two assignments at each call site.
    The same pair is written in two statements at
    [common/glpostingMT.cbl:L508-L509] and again at
    [common/glpostingMT.cbl:L569-L570], so all three sites agree: at end of
    file ``We-Error`` is 10, not zero.

    Returns:
        The ``(FS-Reply, We-Error)`` pair to store into ``FileAccess``.

        >>> end_of_file_status()
        (<FsReply.END_OF_FILE: 10>, 10)
    """
    return FsReply.END_OF_FILE, END_OF_FILE_WE_ERROR


#  FILE-FUNCTION - THE OPERATION CODE. `03  File-Function   pic 99.`
#  [copybooks/wsfnctn.cob:L88] with fifteen `88`-level condition names [:L89-L105]. Two
#  digits, and the values are NOT monotonic with declaration order: 1 through 9, then 15
#  BEFORE 13, then 31 through 34. That ordering is the frozen source's own, so the members
#  below are in DECLARATION order, not value order. The out-of-sequence pair has a documented
#  cause - the changelog widens the wrong field on 07/12/16 and corrects itself on 22/12/16,
#  verbatim `*> Oops, previous chg should have been for File-Function. / next-read-raw changed
#  to 13.` [copybooks/wsfnctn.cob:L14-L15] - so 15 was allocated first and 13 assigned
#  afterwards. The gaps 10, 11, 12, 14 and 16 through 30 are unallocated in the frozen source
#  and are NOT filled here.


class FileFunction(enum.IntEnum):
    """The ``File-Function`` operation codes, in copybook declaration order.

    Fifteen members, values assigned literally. ``enum.auto`` is unusable here
    twice over: the values are not consecutive, and they are not even
    increasing.

        >>> [int(member) for member in FileFunction]
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 15, 13, 31, 32, 33, 34]
        >>> FileFunction.WRITE_RAW > FileFunction.READ_NEXT_RAW
        True

    The names are the ``88``-level names with the ``fn-`` prefix dropped and
    the hyphens made underscores, so the correspondence to the frozen source
    is mechanical in both directions: ``fn-read-next`` becomes ``READ_NEXT``
    and back. ``cobol/condition_names.py`` publishes the matching predicates
    (``is_fn_read_next`` and its siblings) over the same fifteen names; the
    two modules are kept in step by test rather than by import, for the
    layering reason recorded in the module docstring.
    """

    #: `88  fn-open            value 1.`      [copybooks/wsfnctn.cob:L89]
    OPEN = 1

    #: `88  fn-close           value 2.`      [copybooks/wsfnctn.cob:L90]
    CLOSE = 2

    #: `88  fn-read-next       value 3.`      [copybooks/wsfnctn.cob:L91]
    READ_NEXT = 3

    #: `88  fn-read-indexed    value 4.`      [copybooks/wsfnctn.cob:L92]
    #:
    #: One of the four verbs the sequential-file handler rejects outright at
    #: entry [common/acas008.cbl:L299-L307].
    READ_INDEXED = 4

    #: `88  fn-write           value 5.`      [copybooks/wsfnctn.cob:L93]
    WRITE = 5

    #: `88  fn-Delete-All      value 6.       *> 10/10/16 - Delete all records.`
    #: [copybooks/wsfnctn.cob:L94]
    #:
    #: This is how "open for output" is implemented against a relational
    #: store: the sequential-file handler turns `fn-Open` plus `fn-output`
    #: into this verb and deletes every row [common/acas008.cbl:L313-L319].
    DELETE_ALL = 6

    #: `88  fn-re-write        value 7.`      [copybooks/wsfnctn.cob:L95]
    #:
    #: Published by the facade for every entity, but permanently rejected by
    #: the sequential-file handler [common/acas008.cbl:L299-L307], so the
    #: `SPL-Posting-Rewrite` verb can never succeed. Agent Action Plan
    #: section 0.6.7 anomaly 6.
    RE_WRITE = 7

    #: `88  fn-delete          value 8.`      [copybooks/wsfnctn.cob:L96]
    DELETE = 8

    #: `88  fn-start           value 9.`      [copybooks/wsfnctn.cob:L97]
    #:
    #: The one verb whose facade paragraph deliberately does NOT zero
    #: `Access-Type` - see `START_RELATION_BY_ACCESS_TYPE` below.
    START = 9

    # ---- Declaration order diverges from value order from here. ----------

    #: `88  fn-Write-Raw       value 15.`     [copybooks/wsfnctn.cob:L99]
    #:
    #: Declared BEFORE value 13 and higher than it. Preserved as written.
    WRITE_RAW = 15

    #: `88  fn-Read-Next-Raw   value 13.       *> 14/11/16 - Special 4 LD.`
    #: [copybooks/wsfnctn.cob:L100]
    #:
    #: "LD" is the load-program family, `common/*LD.cbl` - the seeding path.
    #: Value 13 was assigned after 15 by the 22/12/16 changelog correction.
    READ_NEXT_RAW = 13

    #: `88  fn-Read-By-Name    value 31.       *> 15/01/17 for Salesled
    #: (SL160), could be used for GL ledger?` [copybooks/wsfnctn.cob:L102]
    #:
    #: The trailing question mark is the maintainer's own; the speculation was
    #: never acted on.
    READ_BY_NAME = 31

    #: `88  fn-Read-By-Batch   value 32.       *> 08/02/17 for OTM3/5
    #: (sl095/pl095)` [copybooks/wsfnctn.cob:L103]
    READ_BY_BATCH = 32

    #: `88  fn-Read-By-Cust    value 33.       *> 09/02/17 for OTM3 (sl110,
    #: 120, 190)` [copybooks/wsfnctn.cob:L104]
    READ_BY_CUST = 33

    #: `88  fn-Read-Next-Header value 34.      *> 18/04/17 for Invoice (sl020,
    #: 50, 140, 820)` [copybooks/wsfnctn.cob:L105]
    READ_NEXT_HEADER = 34


#  ACCESS-TYPE - THE OPEN MODE, AND (FOR START) THE RELATION. `03  Access-Type     pic 9.`
#  [copybooks/wsfnctn.cob:L107] with nine `88`-level condition names [:L108-L116]. ONE digit,
#  not two: the changelog announces widening it to 99 "for extra adhoc functions such as
#  select x ORDER BY etc. / Not used yet." [copybooks/wsfnctn.cob:L11-L13] and then withdraws
#  the announcement two entries later, `*> Oops, previous chg should have been for
#  File-Function.` [:L14-L15], and the field was never in fact widened. The `pic 9` at L107 is
#  the state of the frozen source, so one digit is modelled. Since the nine values are 1
#  through 9 the distinction never truncates a legal value - but there is no room for a tenth,
#  which is the fact a future reader needs.


class AccessType(enum.IntEnum):
    """The ``Access-Type`` codes: values 1-4 are open modes, 5-9 relations.

    The split down the middle is not a convention this migration invented; it
    is how the frozen source uses the field. Values 1 through 4 answer "in
    what mode is this file being opened", and values 5 through 9 answer "with
    what relation is this START positioning the cursor". One field, two
    meanings, disambiguated by which ``File-Function`` accompanies it.

        >>> [int(member) for member in AccessType]
        [1, 2, 3, 4, 5, 6, 7, 8, 9]
        >>> AccessType.NOT_LESS_THAN.name
        'NOT_LESS_THAN'
    """

    # ---- 1 to 4: open modes. ---------------------------------------------

    #: `88  fn-input           value 1.`      [copybooks/wsfnctn.cob:L108]
    INPUT = 1

    #: `88  fn-i-o             value 2.`      [copybooks/wsfnctn.cob:L109]
    I_O = 2

    #: `88  fn-output          value 3.`      [copybooks/wsfnctn.cob:L110]
    #:
    #: Against a relational store this means DELETE EVERY ROW, not "create an
    #: empty file": the sequential-file handler rewrites `fn-Open` plus
    #: `fn-output` into `fn-Delete-All` [common/acas008.cbl:L313-L319].
    OUTPUT = 3

    #: `88  fn-extend          value 4.       *> not valid for ISAM`
    #: [copybooks/wsfnctn.cob:L111]
    EXTEND = 4

    # ---- 5 to 9: START relations. ----------------------------------------

    #: `88  fn-equal-to        value 5.`      [copybooks/wsfnctn.cob:L112]
    EQUAL_TO = 5

    #: `88  fn-less-than       value 6.`      [copybooks/wsfnctn.cob:L113]
    LESS_THAN = 6

    #: `88  fn-greater-than    value 7.`      [copybooks/wsfnctn.cob:L114]
    GREATER_THAN = 7

    #: `88  fn-not-less-than   value 8.`      [copybooks/wsfnctn.cob:L115]
    NOT_LESS_THAN = 8

    #: `88  fn-not-greater-than value 9.`     [copybooks/wsfnctn.cob:L116]
    #:
    #: The changelog says this one was switched on -
    #: `*> 06/08/23 vbc - Activated fn-not-greater-than (for Stock file).`
    #: [copybooks/wsfnctn.cob:L20] - but the START guard still rejects it. See
    #: anomaly N5 on `START_RELATION_BY_ACCESS_TYPE`.
    NOT_GREATER_THAN = 9


#  ACCESS-TYPE 5-9 AS THE START RELATION. Why the caller's `Access-Type` survives into a START
#  at all: every facade verb begins by clearing the field, EXCEPT the `-Start` verbs. The
#  facade copybook's changelog states the exemption in as many words, verbatim `*> 14/08/23
#  vbc - 1.08 - Remove 'move zero to access-type for Start, it is set !!!`
#  [copybooks/Proc-ACAS-FH-Calls.cob:L18], and the general rule it is an exemption FROM is
#  `move zero to Access-Type to keep logging clean.` [:L15]. Counted over the copybook: none
#  of the twenty `-Start` paragraphs clears the field (`GL-Nominal-Start` :L330,
#  `GL-Posting-Start` :L393, `GL-Batch-Start` :L456, `Sales-Start` :L680 and the rest), 146 of
#  the other 215 do (`GL-Batch-Read-Next` :L461, `-Read-Indexed` :L466, `-Write` :L471,
#  `-Rewrite` :L476), and the 69 that do not are the `-Open` family, which SETS the field to
#  the open mode instead (:L194, :L201, :L208). So on a START the caller's access type IS the
#  relation.

#: Width of the `MOST-Relation` field the bridge stores a relation into:
#: `05  MOST-Relation   pic xxx.                  *> valid are >=, <=, <, >, =`
#: [common/glpostingMT.scb:L248]. Three characters, so every relation is
#: SPACE-PADDED to three on the way in.
_MOST_RELATION_WIDTH: Final[int] = 3

#: `Access-Type` -> the relation exactly as the bridge stores it, padded to the three
#: characters of `MOST-Relation pic xxx`. Reproduces `evaluate Access-Type`
#: [common/glpostingMT.cbl:L715-L726], whose five arms move `"=  "`, `"<  "`, `">  "`, `">= "`
#: and `"<= "` - padding included - after `move spaces to MOST-Relation` at [:L713]. ***
#: ANOMALY N5 - REPRODUCED, NOT FIXED (rule R-4) *** The `when 9` arm is UNREACHABLE:
#: `ba060-Process-Start` guards with `if access-type < 5 or > 8` and answers `(99, 997)`
#: [common/glpostingMT.cbl:L695-L698], so 9 never reaches the arm that would give it `"<= "` -
#: labelled `*> [ not currently used in ACAS ]` at [:L724] while [copybooks/wsfnctn.cob:L20]
#: records it "Activated". The arm stays because the frozen `evaluate` declares it and the
#: guard stays as `START_ACCESS_TYPE_RANGE` because the frozen `if` does. Callers apply
#: `start_access_type_is_valid()` first; then the dead arm stays dead as in COBOL.
START_RELATION_BY_ACCESS_TYPE: Final[Mapping[AccessType, str]] = MappingProxyType(
    {
        # when  5   *> fn-equal-to [also in sub4]          [:L716-L717]
        AccessType.EQUAL_TO: "=  ",
        # when  6   *> fn-less-than  [NOT in sub4]         [:L718-L719]
        AccessType.LESS_THAN: "<  ",
        # when  7   *> fn-greater-than [also in sub4]      [:L720-L721]
        AccessType.GREATER_THAN: ">  ",
        # when  8   *> fn-not-less-than [also in sub4]     [:L722-L723]
        AccessType.NOT_LESS_THAN: ">= ",
        # when  9   *> fn-not-greater-than [ not currently used in ACAS ]
        # UNREACHABLE behind the L695 guard - anomaly N5.  [:L724-L725]
        AccessType.NOT_GREATER_THAN: "<= ",
    }
)

#: The same five relations with the padding stripped, which is the form that
#: reaches the SQL text.
#:
#: Both forms are published because the frozen source uses both. The bridge
#: STORES the padded literal into `MOST-Relation pic xxx`
#: [common/glpostingMT.cbl:L713-L726], then builds its WHERE clause with
#: `MOST-relation delimited by space` [common/glpostingMT.cbl:L732], and
#: `delimited by space` stops at the first space - so the SQL sees `">="` and
#: never `">= "`. A module that published only one form would force every
#: caller to guess which one it had.
START_RELATION_TOKEN_BY_ACCESS_TYPE: Final[Mapping[AccessType, str]] = (
    MappingProxyType(
        {
            access_type: relation.strip()
            for access_type, relation in START_RELATION_BY_ACCESS_TYPE.items()
        }
    )
)

#: The inclusive bounds the START parameter guard actually enforces, as the
#: frozen `if access-type < 5 or > 8` writes them
#: [common/glpostingMT.cbl:L695]. Note the upper bound is 8, NOT 9 - see
#: anomaly N5 above. Published as data so the anomaly log and the
#: anomaly-locking tests can assert on the discrepancy between this range and
#: the five keys of `START_RELATION_BY_ACCESS_TYPE`.
START_ACCESS_TYPE_RANGE: Final[tuple[int, int]] = (5, 8)


def start_access_type_is_valid(access_type: int) -> bool:
    """Report whether a START would pass the bridge's parameter guard.

    Reproduces ``if access-type < 5 or > 8`` exactly
    [common/glpostingMT.cbl:L695], upper bound of 8 included - see anomaly N5
    on :data:`START_RELATION_BY_ACCESS_TYPE`. A caller that gets ``False``
    must set the pair ``(FsReply.ERROR, WeError.ACCESS_TYPE_WRONG)`` and
    abandon the START, which is what
    [common/glpostingMT.cbl:L696-L698] does.

    Args:
        access_type: The ``Access-Type`` value the caller set before the
            ``fn-start`` call. Accepts a plain ``int`` because that is what
            ``FileAccess.access_type`` holds.

    Returns:
        ``True`` if the value lies within the guard's inclusive 5-8 range.

        >>> start_access_type_is_valid(AccessType.NOT_LESS_THAN)
        True
        >>> start_access_type_is_valid(AccessType.NOT_GREATER_THAN)  # N5
        False
        >>> start_access_type_is_valid(AccessType.INPUT)
        False
    """
    lower, upper = START_ACCESS_TYPE_RANGE
    return lower <= int(access_type) <= upper


def start_relation_for(access_type: int, *, padded: bool = False) -> str:
    """Return the START relation for an access type.

    Reproduces the relation table at [common/glpostingMT.cbl:L715-L726]. The
    dead ``when 9`` arm is served like any other, because the COBOL
    ``evaluate`` declares it; reaching it requires having skipped the guard,
    exactly as it would in COBOL. Use :func:`start_access_type_is_valid`
    first.

    Args:
        access_type: An ``Access-Type`` value in the 5-9 relation band.
        padded: ``True`` for the three-character form the bridge stores into
            ``MOST-Relation pic xxx``; ``False`` (the default) for the trimmed
            token that reaches the SQL text through ``delimited by space``
            [common/glpostingMT.cbl:L732].

    Returns:
        The relation as a string.

    Raises:
        KeyError: If the value is outside the 5-9 relation band. The COBOL has
            no equivalent - its ``evaluate`` has no ``when other``, so an
            out-of-band value simply leaves ``MOST-Relation`` at the spaces
            moved in at [common/glpostingMT.cbl:L713]. That silent fall-through
            is unreachable in practice because the L695 guard rejects 1-4 and
            anything above 9 before the table is consulted, so this raise
            covers only a programming error in the Python caller, never a
            COBOL-reachable state. Callers reproducing the fall-through
            deliberately should read the mapping directly.

        >>> start_relation_for(AccessType.NOT_LESS_THAN)
        '>='
        >>> start_relation_for(AccessType.NOT_LESS_THAN, padded=True)
        '>= '
        >>> len(start_relation_for(AccessType.EQUAL_TO, padded=True))
        3
    """
    key = AccessType(int(access_type))
    if padded:
        return START_RELATION_BY_ACCESS_TYPE[key]
    return START_RELATION_TOKEN_BY_ACCESS_TYPE[key]


#  WE-ERROR - THE DETAIL CODE BEHIND FS-REPLY 99. `03  We-Error        pic 999.`
#  [copybooks/wsfnctn.cob:L23] - three digits, widened from two while chasing a missing-data
#  bug in the period-totals table [copybooks/wsfnctn.cob:L8-L9]. Like `Fs-Reply` it carries no
#  `88`-level condition names, so every name below is ours, derived from the prose table at
#  [common/glpostingMT.cbl:L132-L155] plus the two handler-only codes. The table's own
#  footnote ties each code to `Fs-Reply`, verbatim `*> * = FS-Reply = 99.`
#  [common/glpostingMT.cbl:L158] - an asterisk against a code means that code arrives with
#  FS-Reply 99. `implies_fs_reply_error()` implements the footnote; see the discrepancy
#  recorded on `RECORD_SIZE_MISMATCH`.


class WeError(enum.IntEnum):
    """The ``We-Error`` detail codes, with the frozen prose for each.

    Fourteen members: the twelve of the bridge's own table plus the two that
    exist only in handler source. The set is closed - other handlers document
    codes outside it, and those are recorded in comments rather than added,
    because rule R-3 is that vocabulary is copied and never extended.

    Recorded but deliberately NOT members:

    * ``1+``, ``2+``, ``3+`` - "Failure to open IRS file", "Indexed IRS record
      not found", "IRS EOF reached" [common/acas008.cbl:L162-L164]. Open-ended
      ranges rather than codes, local to one handler's prose.

        >>> [int(member) for member in WeError]
        [0, 999, 998, 997, 996, 995, 994, 992, 990, 989, 988, 911, 910, 901]
        >>> WeError.SUCCESS == 0
        True
    """

    #: `WE-Error   0    = Operation completed successfully`
    #: [common/glpostingMT.cbl:L132]
    SUCCESS = 0

    #: `999  = Not used here - Yet.` [common/glpostingMT.cbl:L134]
    #:
    #: "Not used HERE" is precise: no bridge sets it, but every numbered
    #: handler does - it is the handlers' unknown-function code. So unlike 992
    #: it does have producers, just not in the layer whose table documents it.
    NOT_USED = 999

    #: `998* = File-Key-No Out Of Range not 1, 2 or 3.` [common/glpostingMT.cbl:L135] THREE
    #: different wordings exist for this one code and they disagree about the permitted range:
    #: "File-Key-No Out Of Range not 1, 2 or 3." [common/glpostingMT.cbl:L135], "file seeks
    #: key type out of range" [common/acas000.cbl:L336] and "File-Key-No Out Of Range not 1."
    #: [common/acas008.cbl:L166]. The code that actually enforces it permits FIVE values - `if
    #: File-Key-No < 1 or > 5     *> Chg 14/10/25 to support PY` [common/acas000.cbl:L335].
    #: See `FILE_KEY_NO_DOCUMENTED_RANGE` and `FILE_KEY_NO_GUARD_RANGE`, which publish the
    #: documentation and the implementation side by side without reconciling them.
    FILE_KEY_NO_OUT_OF_RANGE = 998

    #: `997* = Access-Type wrong (< 5 or > 8)` [common/glpostingMT.cbl:L136]
    #:
    #: The parenthesis is the guard verbatim, and its upper bound of 8 is the
    #: whole of anomaly N5. Set with FS-Reply 99 at
    #: [common/glpostingMT.cbl:L696-L697].
    ACCESS_TYPE_WRONG = 997

    #: `996* = File Delete key out of range (not = 1 or 2)`
    #: [common/glpostingMT.cbl:L136 continued at :L137]
    #:
    #: The sequential-file handler documents a narrower range for the same
    #: code - `996* = File Delete key out of range (not 1)`
    #: [common/acas008.cbl:L168].
    DELETE_KEY_OUT_OF_RANGE = 996

    #: `995* = During Delete SQLSTATE not '00000' investigate using MSG-Err/Msg`
    #: [common/glpostingMT.cbl:L138]
    #:
    #: One of the two per-operation narrowings of the 911 catch-all: set AFTER
    #: the generic handler has already returned `(99, 911)` -
    #: `move 99 to fs-reply` / `move 995 to WE-Error`
    #: [common/glpostingMT.cbl:L874-L875], in `ba080-Process-Delete`. See
    #: anomaly N3 and `mysql_1100_db_error`.
    DELETE_SQLSTATE_NOT_00000 = 995

    #: `994* = During Rewrite,                     ^^ see above ^^`
    #: [common/glpostingMT.cbl:L139] - the caret run means "as 995, but for
    #: rewrite".
    #:
    #: The other per-operation narrowing:
    #: `move 99 to fs-reply    *> this may need changing for val in WE-Error!!`
    #: / `move 994 to WE-Error` [common/glpostingMT.cbl:L1001-L1002], in
    #: `ba090-Process-Rewrite`.
    REWRITE_SQLSTATE_NOT_00000 = 994

    #: `992* = Invalid Function requested in File-Function` [common/glpostingMT.cbl:L140] ***
    #: ANOMALY N6 - REPRODUCED, NOT FIXED (rule R-4) *** This code has NO PRODUCER. An
    #: exhaustive search of `common/` and `copybooks/` finds not one statement that sets 992 -
    #: every occurrence in the tree is inside a comment, in the prose table each bridge
    #: carries a copy of. An invalid `File-Function` is in fact answered with 999 by the
    #: handlers, never with 992. The member is retained because the authoritative table
    #: declares it, and deleting an unproduced-but-documented code would hide the anomaly -
    #: the same reasoning that keeps `FsReply.KEY_NOT_FOUND`. Listed in
    #: `DOCUMENTATION_ONLY_WE_ERRORS`.
    INVALID_FUNCTION = 992

    #: `990* = Unknown and unexpected error, again ^^ see above ^^`
    #: [common/glpostingMT.cbl:L141]
    #:
    #: Paired with FS-Reply 21 - not 23 - on the read-indexed error branch:
    #: `move 21 to fs-reply    *> from 23` / `move 990 to WE-Error`
    #: [common/glpostingMT.cbl:L668-L669]. Anomaly N2.
    UNKNOWN_UNEXPECTED = 990

    #: `989* = Unexpected error on Read-Indexed, investigate as above.`
    #: [common/glpostingMT.cbl:L142]
    #:
    #: Paired with FS-Reply 21 - again not 23 - on the read-indexed
    #: no-such-row branch: `move 21   to fs-reply    *> from 23` /
    #: `move 989  to WE-Error` [common/glpostingMT.cbl:L676-L677]. Anomaly N2.
    READ_INDEXED_UNEXPECTED = 989

    #: `988* = File Action wrong for file type.` [common/acas008.cbl:L173], the site's own
    #: wording being `*> Action type wrong for file type (seq)   988`
    #: [common/acas008.cbl:L304]. A handler-only code: it appears in NO bridge's table, and
    #: the single statement that sets it anywhere in the tree is [common/acas008.cbl:L304],
    #: paired with `move 99 to fs-reply` at [:L305]. It is the rejection the sequential-file
    #: handler applies to `fn-read-indexed`, `fn-re-write`, `fn-start` and `fn-delete`
    #: unconditionally at entry [common/acas008.cbl:L299-L307], which is why the facade's
    #: `SPL-Posting-Rewrite` verb can never succeed.
    ACTION_TYPE_WRONG_FOR_SEQ = 988

    #: `911* = Rdb Error during initializing, possibly can not connect to database / Check
    #: connect data and see SQL-Err & SQL-MSG / Produced by Mysql-1100-Db-Error in copy module
    #: mysql-procedure.` [common/glpostingMT.cbl:L143-L148] *** ANOMALY N3 - REPRODUCED, NOT
    #: FIXED (rule R-4) *** The documentation says "during initializing"; the code says
    #: "always". The last two statements of `Mysql-1100-Db-Error` are unconditional - `move 99
    #: to fs-Reply.` then `move 911 to We-Error.` [copybooks/mysql-procedures.cpy:L127-L128] -
    #: no `if` guards them, and the only path that skips them is the duplicate-key early exit.
    #: So EVERY non-duplicate failure of EVERY operation is reported as 911: a syntax error, a
    #: missing table, a constraint violation, a lost connection, and - because the retry
    #: ladder is dead - a table lock too. Reproduced in `mysql_1100_db_error`, which returns
    #: 911 unconditionally; callers narrow it afterwards, as the bridges do for delete and
    #: rewrite.
    RDB_INIT_ERROR = 911

    #: `910* = Table locked > 5 seconds` [common/glpostingMT.cbl:L149] *** ANOMALY N1 -
    #: REPRODUCED, NOT FIXED (rule R-4) *** UNREACHABLE AT RUNTIME. The only statement in the
    #: tree that sets 910 is [copybooks/mysql-procedures.cpy:L245], inside
    #: `Mysql-1300-DB-Error`, and the only `perform` of that paragraph is commented out at
    #: [:L167]. No live path reaches it, so no caller can ever see this code; a locked table
    #: is reported as 911 instead. The prose is also arithmetically wrong about its own ladder
    #: - the four rungs wait 1/4 + 1/2 + 1 + 5 seconds, so 910 would be raised after 6.75
    #: seconds, not 5. See `LOCK_RETRY_LADDER` and `mysql_1300_db_error`.
    TABLE_LOCKED = 910

    #: `901  = File Def Record size not =< than ws record size / Module needs ws definition
    #: changing to correct size / FATAL, Stop using system, fix source code and recompile
    #: before using system again.` [common/glpostingMT.cbl:L150-L153] FATAL in the frozen
    #: source's own capitals: the compiled record layout and the table row disagree in length,
    #: so the run cannot continue - the handler displays, accepts and stops
    #: [common/acas008.cbl:L537-L540]. DISCREPANCY, recorded and not resolved: 901 is the one
    #: starred-worthy code the table prints WITHOUT an asterisk [:L150], which by its own
    #: footnote [:L158] would mean it does not arrive with FS-Reply 99. The code disagrees -
    #: `move 901 to WE-Error` is immediately followed by `move 99 to fs-reply`
    #: [common/acas008.cbl:L534-L535]. Both facts are published: 901 IS in
    #: `WE_ERRORS_IMPLYING_FS_REPLY_ERROR` because that is what executes, and the missing
    #: asterisk is recorded because that is what is written.
    RECORD_SIZE_MISMATCH = 901


#: The `We-Error` codes that arrive with `FsReply.ERROR`, i.e. the codes the authoritative
#: table marks with an asterisk, per its own footnote `*> * = FS-Reply = 99.`
#: [common/glpostingMT.cbl:L158]. Starred in the table [:L135-L149]: 998, 997, 996, 995, 994,
#: 992, 990, 989, 911, 910. Unstarred: 0 [:L132], 999 [:L134] and 901 [:L150]. 901 is
#: nonetheless INCLUDED, and 988 - which the table does not list at all - is included too,
#: because both are paired with `move 99 to fs-reply` in handler code:
#: [common/acas008.cbl:L534-L535] for 901 and [:L304-L305] for 988. Where the prose and the
#: executing code disagree, rule R-6 makes the code the tie-breaker; the disagreement itself
#: is recorded on `WeError.RECORD_SIZE_MISMATCH` rather than smoothed over.
WE_ERRORS_IMPLYING_FS_REPLY_ERROR: Final[frozenset[WeError]] = frozenset(
    {
        WeError.FILE_KEY_NO_OUT_OF_RANGE,  # 998* [:L135]
        WeError.ACCESS_TYPE_WRONG,  # 997* [:L136]
        WeError.DELETE_KEY_OUT_OF_RANGE,  # 996* [:L137]
        WeError.DELETE_SQLSTATE_NOT_00000,  # 995* [:L138]
        WeError.REWRITE_SQLSTATE_NOT_00000,  # 994* [:L139]
        WeError.INVALID_FUNCTION,  # 992* [:L140]
        WeError.UNKNOWN_UNEXPECTED,  # 990* [:L141]
        WeError.READ_INDEXED_UNEXPECTED,  # 989* [:L142]
        WeError.ACTION_TYPE_WRONG_FOR_SEQ,  # 988  [common/acas008.cbl:L304-L305]
        WeError.RDB_INIT_ERROR,  # 911* [:L143]
        WeError.TABLE_LOCKED,  # 910* [:L149] - unreachable, N1
        WeError.RECORD_SIZE_MISMATCH,  # 901  unstarred yet paired with 99
    }
)

#: The `We-Error` codes with NO producer anywhere in the frozen tree - present in the
#: authoritative prose table, set by no statement. 992 is anomaly N6: exhaustive search finds
#: no assignment and an invalid `File-Function` yields 999 instead
#: [common/glpostingMT.cbl:L140]. 910 is anomaly N1: assigned only inside the dead paragraph
#: at [copybooks/mysql-procedures.cpy:L245], whose sole `perform` is commented out at [:L167].
#: 999 is deliberately NOT here - its prose says "Not used HERE - Yet"
#: [common/glpostingMT.cbl:L134] and that is accurate: no bridge sets it, but every numbered
#: handler does, so it has producers, just not in the layer that documents it. Published so
#: the anomaly-locking tests can assert these two stay unproduced, which makes a future
#: well-meaning activation of either fail rather than pass unnoticed.
DOCUMENTATION_ONLY_WE_ERRORS: Final[frozenset[WeError]] = frozenset(
    {WeError.INVALID_FUNCTION, WeError.TABLE_LOCKED}
)


def implies_fs_reply_error(we_error: int) -> bool:
    """Report whether a ``We-Error`` code arrives with ``FS-Reply 99``.

    Implements the authoritative table's own footnote, verbatim
    [common/glpostingMT.cbl:L158]::

        *>                                     * = FS-Reply = 99.

    This is a reporting predicate over :data:`WE_ERRORS_IMPLYING_FS_REPLY_ERROR`,
    not a validation: it never rejects anything, and no caller is obliged to
    consult it. Rule R-3 forbids adding validation the COBOL lacks, and the
    COBOL sets the two fields independently at every site rather than deriving
    one from the other.

    Args:
        we_error: A ``We-Error`` value; a plain ``int`` is accepted because
            that is what ``FileAccess.we_error`` holds.

    Returns:
        ``True`` if the code is one that the frozen source pairs with
        ``FS-Reply 99``. Unknown values - the table's own
        `Other = any other rdbms errors` [:L154-L155] - return ``False``,
        because nothing in the frozen source pairs them with anything.

        >>> implies_fs_reply_error(WeError.RDB_INIT_ERROR)
        True
        >>> implies_fs_reply_error(WeError.RECORD_SIZE_MISMATCH)   # unstarred
        True
        >>> implies_fs_reply_error(WeError.SUCCESS)
        False
        >>> implies_fs_reply_error(WeError.NOT_USED)
        False
        >>> implies_fs_reply_error(12345)
        False
    """
    try:
        member = WeError(int(we_error))
    except ValueError:
        # `Other = any other rdbms errors see specific (Rdbms) manual`
        # [common/glpostingMT.cbl:L154-L155]. Not an error condition here.
        return False
    return member in WE_ERRORS_IMPLYING_FS_REPLY_ERROR


#  FILE-KEY-NO - A DOCUMENTED RANGE THAT CONTRADICTS THE ENFORCED ONE
#  `05  File-Key-No     pic 9.` [copybooks/wsfnctn.cob:L46], selects which key
#  of a table a keyed read uses. Two sources describe its legal values and
#  they do not agree, so both are published and neither is resolved.

#: The range the copybook DOCUMENTS, immediately above the `Logging-Data`
#: block, verbatim [copybooks/wsfnctn.cob:L42-L43]::
#:
#:     *> current range 1 thru 3
#:     *>     1 = Stock-Key (or only key), 2 = Stock-Abrev-Key, 3 = Stock-Desc
#:
#: Note the meanings are Stock-specific, in a copybook shared by every
#: subsystem - which is itself the clue that the comment was written for one
#: caller and never generalised.
FILE_KEY_NO_DOCUMENTED_RANGE: Final[tuple[int, int]] = (1, 3)

#: The range a handler actually ENFORCES, verbatim `if     File-Key-No < 1 or > 5     *> Chg
#: 14/10/25 to support PY` [common/acas000.cbl:L335], with its own meanings for the values and
#: no mention of Stock - `*>    1 = params rec, 2 = default rec, / *>    3 = final rec & 4 =
#: system totals rec.` [common/acas000.cbl:L328-L329]. Three disagreements with the copybook
#: comment: the upper bound is 5 and not 3; the meanings are system-record types and not Stock
#: keys; and value 5 is admitted by the guard while given no meaning at all by either source -
#: the trailing note says the widening was made "to support PY", the payroll subsystem, which
#: this migration does not reach. Violating the guard yields `(99, 998)`
#: [common/acas000.cbl:L336-L337]. The system handler module a later boundary adds will
#: reproduce the guard; this module only records the contradiction. Rule R-4 forbids resolving
#: it and rule R-3 forbids
#: validating against either range here.
FILE_KEY_NO_GUARD_RANGE: Final[tuple[int, int]] = (1, 5)


#  SQLSTATE - THE VOCABULARY, AND THE MAP THAT WAS NEVER WIRED UP
#  `05  SQL-State       pic x(5).` [copybooks/wsfnctn.cob:L51]


class SqlState(enum.StrEnum):
    """The five-character SQLSTATE values the frozen source names.

    Two kinds of value in one vocabulary, and the distinction matters:

    * ``NO_DATA`` and ``DUPLICATE_KEY`` are real ANSI SQLSTATE values that
      arrive from the driver.
    * the five ``99xxx`` values are **not SQLSTATEs at all**. They are
      internal codes the bridge layer invented for its own cursor-state
      failures, occupying the SQLSTATE field because that is where a caller
      would look. No database will ever return one.

    ``StrEnum`` so a member compares equal to the raw five-character string
    ``LoggingData.sql_state`` holds, matching the ``IntEnum`` choice made for
    the numeric codes.

    Only ``DUPLICATE_KEY`` is consulted at runtime anywhere in the frozen
    source - see :data:`DOCUMENTED_SQLSTATE_MAPPINGS` and anomaly N4.

        >>> SqlState.DUPLICATE_KEY == "23000"
        True
        >>> len(SqlState.READ_NEXT_WITH_NO_POSITION)
        5
    """

    #: `0200n  no data found one way or another` [copybooks/mysql-procedures.cpy:L112] The
    #: frozen comment writes the value as `0200n` with a trailing placeholder letter, i.e. a
    #: family rather than one code; `"02000"` is the member of that family the commented-out
    #: test at [copybooks/mysql-procedures.cpy:L124] names, and it is the value used here. The
    #: rest of the family is not modelled because the frozen source never names another member
    #: of it. The same line carries the maintainer's bracketed note on what to do with it - a
    #: proposal to choose between 23 and 10 by an entropy source. It is paraphrased rather
    #: than quoted; see "DELIBERATE OMISSIONS" item 3
    #: in the module docstring. It was never implemented.
    NO_DATA = "02000"

    #: `23000  Dup primary key on insert same as fs-reply = 22.`
    #: [copybooks/mysql-procedures.cpy:L114]
    #:
    #: THE ONLY SQLSTATE ANY LIVE CODE PATH TESTS. Used at the bridge level
    #: only, as one of three alternatives in the write path's duplicate test
    #: [common/glpostingMT.cbl:L818-L820]. The driver-level test in the same
    #: call chain does not look at SQLSTATE at all - it tests the numeric
    #: errno instead [copybooks/mysql-procedures.cpy:L99].
    DUPLICATE_KEY = "23000"

    #: `'99NKS'   internal error = invalid key # used.`
    #: [copybooks/mysql-procedures.cpy:L115]
    INVALID_KEY_NUMBER = "99NKS"

    #: `'99NKU'   internal error = No valid key used.`
    #: [copybooks/mysql-procedures.cpy:L116]
    NO_VALID_KEY = "99NKU"

    #: `'99NKD'   internal error - no valid key used for delete`
    #: [copybooks/mysql-procedures.cpy:L117] - the dash instead of `=` is the
    #: maintainer's own, on this line only.
    NO_VALID_KEY_FOR_DELETE = "99NKD"

    #: `'99RNP'   internal error = read next with no position (no start 1st)`
    #: [copybooks/mysql-procedures.cpy:L118]
    #:
    #: The cursor-state failure `dal/cursor_state.py` exists to detect: a
    #: `fn-read-next` issued without a preceding `fn-start` to position the
    #: cursor.
    READ_NEXT_WITH_NO_POSITION = "99RNP"

    #: `'99GNS'   internal error = Could not generate a start.`
    #: [copybooks/mysql-procedures.cpy:L119]
    COULD_NOT_GENERATE_START = "99GNS"


@dataclass(frozen=True, slots=True)
class SqlStateMapping:
    """One line of the SQLSTATE dispositions block, with its wiring status.

    A record of what the frozen source SAYS a SQLSTATE should mean, paired
    with whether any code actually acts on it. The ``implemented`` marker is
    the point of the type: without it a reader would take the block for a
    specification of live behaviour, which is exactly the mistake anomaly N4
    is about.
    """

    #: The SQLSTATE this line describes.
    sql_state: SqlState

    #: The disposition the frozen comment proposes, in this migration's words
    #: rather than the maintainer's where the original wording cannot be
    #: reproduced here - see the note on ``SqlState.NO_DATA``.
    proposed_disposition: str

    #: Locator of the line in the frozen source.
    locator: str

    #: ``True`` only if some live code path actually tests this SQLSTATE.
    #: Exactly one of the seven is ``True``.
    implemented: bool


#: The SQLSTATE dispositions block, entry by entry, with its wiring status. *** ANOMALY N4 -
#: REPRODUCED, NOT FIXED (rule R-4) *** The whole block at
#: [copybooks/mysql-procedures.cpy:L109-L119] is COMMENT, opening by admitting it is
#: unfinished - `*> Next blk new, 30/12/16 and is under test- just have to work out any IF
#: tests.` [:L109] - and those tests never were. Live code only fetches and stores the value
#: [:L122-L123]; the test that would read it is commented out at [:L124], and the
#: unconditional `(99, 911)` at [:L127-L128] follows. So six of seven dispositions are dead
#: letters; `"23000"` is live only because a BRIDGE tests it in the duplicate check
#: [common/glpostingMT.cbl:L818-L820], the only `True` here. Turning any `False` into logic
#: would add behaviour the compiled program lacks: R-4 forbids it and R-3 forbids it again.
#: Order is the frozen block's own line order, and the tuple is immutable, so
#: iteration is deterministic (rule R-6).
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


#  DUPLICATE KEY - TWO TESTS AT TWO LAYERS, DELIBERATELY NOT MERGED
#  The same condition is detected twice in one call chain, by two tests that
#  do not agree. Both are reproduced, each named after the site it comes from,
#  because merging them would change which failures are reported as duplicates.

#: The driver error numbers that mean "duplicate", as the driver-level test writes them,
#: verbatim `if       Ws-Mysql-Error-Number = "1062" or = "1022"   *> Duplicate entry/Write
#: dup key` [copybooks/mysql-procedures.cpy:L99]. STRINGS, not integers, and deliberately so:
#: `Ws-Mysql-Error-Number` is a character field, so COBOL compares text. The distinction shows
#: - text comparison makes `"1062"`, `" 1062"` and `"01062"` three different values where
#: integer comparison would make the first two equal. Converting to `int` here would be a
#: silent semantic change, so the strings stay strings and callers hand over whatever text
#: they have.
#:
#: 1062 is MySQL's ER_DUP_ENTRY; 1022 is ER_DUP_KEY.
DUPLICATE_KEY_ERRNOS: Final[frozenset[str]] = frozenset({"1062", "1022"})

#: The two statement-text prefixes the driver-level test accepts, from the
#: `evaluate` arms at [copybooks/mysql-procedures.cpy:L100-L102]::
#:
#:     evaluate Ws-Mysql-Command (1:6)
#:           when "INSERT"
#:           when "insert"
#:
#: Two spellings, six characters, CASE-SENSITIVE, and tested against the raw
#: statement text rather than against a parsed statement type. A statement
#: beginning `Insert` or ` INSERT` matches neither arm. That is the frozen
#: behaviour and it is preserved literally - see
#: `is_duplicate_key_driver_level` for what happens when it does not match.
DUPLICATE_KEY_COMMAND_PREFIXES: Final[tuple[str, ...]] = ("INSERT", "insert")

#: Length of the reference modification `Ws-Mysql-Command (1:6)`
#: [copybooks/mysql-procedures.cpy:L100] - six characters from position one.
_DUPLICATE_KEY_COMMAND_PREFIX_LENGTH: Final[int] = 6

#: The SQLSTATE the BRIDGE-level test accepts as a duplicate
#: [common/glpostingMT.cbl:L820]. The driver-level test never looks at
#: SQLSTATE; this is the one place it is consulted. Same value as
#: `SqlState.DUPLICATE_KEY`, named separately here so the bridge-level test
#: reads as the frozen source reads.
DUPLICATE_KEY_SQLSTATE: Final[str] = SqlState.DUPLICATE_KEY

#: Length of the reference modification `SQL-Err (1:4)`
#: [common/glpostingMT.cbl:L818] - four characters of a `pic x(5)` field
#: [copybooks/wsfnctn.cob:L49], so the fifth character is NOT compared.
_SQL_ERR_COMPARE_LENGTH: Final[int] = 4


def is_duplicate_key_driver_level(errno: str, command: str) -> bool:
    """Driver-level duplicate test, from ``Mysql-1100-Db-Error``.

    Reproduces [copybooks/mysql-procedures.cpy:L99-L105], verbatim::

        if       Ws-Mysql-Error-Number = "1062" or = "1022"   *> Duplicate entry/Write dup key
                 evaluate Ws-Mysql-Command (1:6)
                       when "INSERT"
                       when "insert"
                       move 22 to fs-Reply
                       go to Mysql-1190-Exit
        end-if

    Two structural details of that fragment are load-bearing and are both
    reproduced:

    1. **The ``evaluate`` has no ``when other``**, and no ``end-evaluate``
       either - it is closed implicitly by the ``end-if`` at ``:L105``. So a
       duplicate errno raised by a statement that is NOT an ``INSERT`` matches
       neither arm, falls out of the ``evaluate``, falls out of the ``if``,
       and continues into the generic error path at ``:L107`` onwards - ending
       at the unconditional ``(99, 911)`` of anomaly N3. It is NOT reported as
       a duplicate. An ``UPDATE`` that violates a unique constraint therefore
       returns 99/911, not 22.
    2. **Both tests must pass.** The errno test alone is not sufficient, which
       is why this function takes the statement text as well.

    Args:
        errno: The driver's error number AS TEXT, because
            ``Ws-Mysql-Error-Number`` is a character field and COBOL compares
            it as text. Callers holding an integer should render it without
            padding, e.g. ``str(exc.errno)``.
        command: The statement text, unparsed and untrimmed - the equivalent
            of ``Ws-Mysql-Command``. Only its first six characters are looked
            at, and they are compared case-sensitively.

    Returns:
        ``True`` only if BOTH tests pass, meaning the caller should set
        ``FS-Reply 22`` and exit early WITHOUT touching ``We-Error``. The
        early exit is ``go to Mysql-1190-Exit`` at ``:L104``, which jumps past
        both moves of anomaly N3 - so on a duplicate, ``We-Error`` keeps
        whatever value it already had. ``mysql_1100_db_error`` reproduces
        that.

        >>> is_duplicate_key_driver_level("1062", "INSERT INTO `GLPOSTING-REC`")
        True
        >>> is_duplicate_key_driver_level("1022", "insert into x values (1)")
        True
        >>> is_duplicate_key_driver_level("1062", "UPDATE x SET y = 1")  # falls through
        False
        >>> is_duplicate_key_driver_level("1062", "Insert into x")  # case-sensitive
        False
        >>> is_duplicate_key_driver_level("1146", "INSERT INTO x")
        False
    """
    # `if Ws-Mysql-Error-Number = "1062" or = "1022"` [:L99]. Text comparison,
    # as the field is `pic x`; see DUPLICATE_KEY_ERRNOS.
    if errno not in DUPLICATE_KEY_ERRNOS:
        return False

    # `evaluate Ws-Mysql-Command (1:6)` [:L100] with arms `when "INSERT"` and
    # `when "insert"` [:L101-L102]. Reference modification is a fixed-length
    # slice, so a statement shorter than six characters yields a short string
    # that matches neither arm - the same outcome COBOL reaches, by a
    # different route, since its field is space-filled to its declared length.
    prefix = command[:_DUPLICATE_KEY_COMMAND_PREFIX_LENGTH]

    # No `when other` and no `end-evaluate` [:L105]: a non-INSERT duplicate
    # falls through to the generic path rather than being reported as 22.
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
    not = "0"`` [:L814]. Those belong to the GL posting handler's write path,
    which a later boundary adds; this function is only the innermost test.

    Args:
        sql_err: The ``SQL-Err`` field's contents. Only the first four
            characters are compared.
        sql_state: The ``SQL-State`` field's contents, compared in full.

    Returns:
        ``True`` for ``FS-Reply 22``, ``False`` for ``FS-Reply 99``.

        >>> is_duplicate_key_bridge_level("1062", "HY000")
        True
        >>> is_duplicate_key_bridge_level("1022", "HY000")
        True
        >>> is_duplicate_key_bridge_level("1451", "23000")  # SQLSTATE alone
        True
        >>> is_duplicate_key_bridge_level("10629", "HY000")  # only (1:4) compared
        True
        >>> is_duplicate_key_bridge_level("1146", "42S02")
        False
    """
    # `SQL-Err (1:4) = "1062" or = "1022"` [:L818-L819]. The `or = "1022"`
    # continuation line is easy to miss when the fragment is quoted without
    # it; both codes are tested here, exactly as at the driver level.
    if sql_err[:_SQL_ERR_COMPARE_LENGTH] in DUPLICATE_KEY_ERRNOS:
        return True

    # `or Sql-State = "23000"` [:L820] - the only runtime use of SQLSTATE
    # anywhere in the frozen error path. Anomaly N4.
    return sql_state == DUPLICATE_KEY_SQLSTATE


#  THE DIAGNOSTIC FIELDS, AND A LOCAL PICTURE-CLAUSE HELPER. Three `Logging-Data` fields carry
#  the driver's own account of a failure - `SQL-Err pic x(5)` [copybooks/wsfnctn.cob:L49],
#  `SQL-Msg pic x(512) value spaces` [:L50] and `SQL-State pic x(5)` [:L51] - and the
#  authoritative table says when they are meaningful: `*>  SQL-Err  = Error code from RDBMS is
#  set if above 2 are non zero / *>  SQL-Msg  = Non space providing more info if SQL-Err non
#  '00000'` [common/glpostingMT.cbl:L156-L157]. The truncate-and-pad is implemented LOCALLY
#  rather than delegated to the module that owns `MOVE`, because the per-directory import
#  table of Agent Action Plan section 0.4.3 grants no `dal` to `cobol` edge. All three fields
#  are `pic x(n)` - no sign, no scale, no numeric editing - so the local helper is complete
#  for its stated domain. Anything beyond alphanumeric fields must NOT be added here; it
#  belongs in the `MOVE` module, reached from a permitted layer.

#: `pic x(5)` [copybooks/wsfnctn.cob:L49].
SQL_ERR_WIDTH: Final[int] = 5

#: `pic x(512)` [copybooks/wsfnctn.cob:L50].
SQL_MSG_WIDTH: Final[int] = 512

#: `pic x(5)` [copybooks/wsfnctn.cob:L51].
SQL_STATE_WIDTH: Final[int] = 5


def _pic_x(text: str, width: int) -> str:
    """Store ``text`` into an alphanumeric field of ``width`` characters.

    The receiving-field rule for a ``MOVE`` to ``pic x(n)``: the sending item
    is aligned to the LEFT of the receiving item, excess characters on the
    RIGHT are truncated, and any unused character positions on the right are
    filled with spaces. Result length is always exactly ``width``, which is
    what makes a fixed-length record fixed.

    Local to this module for the layering reason given in the section comment
    above, and restricted to alphanumeric fields by design.
    """
    return text[:width].ljust(width)


# =============================================================================
#  LOG-SAFE DIAGNOSTIC TEXT  (CWE-117 log injection, CWE-532 secret exposure)
# =============================================================================
#  The three fields above carry the DRIVER'S OWN account of a failure, and two
#  things are true of that text at once: it is the most useful thing an operator
#  has, and it is the least trustworthy string in the process. It is assembled
#  by the server and the client library out of material that includes the
#  connection's user name, the host, the socket path, the schema name and, for a
#  statement failure, key values taken from the data.
#
#  Two consequences, and one non-consequence.
#
#  * A log record built by interpolating that text can be FORGED. A message
#    carrying a carriage return and a line feed writes what looks like a second
#    log record, of the sender's choosing, into the same stream; one carrying an
#    ANSI escape can rewrite what a terminal shows. So control characters are
#    replaced by their own `\xNN` spelling before the text is logged - escaped
#    rather than dropped, so the evidence that they were there survives.
#  * The text LEAKS. "Access denied for user 'ACAS-User'@'localhost' (using
#    password: YES)" names the account; "Can't connect to MySQL server on
#    'db.internal:3306'" names the host. Neither belongs in a log file that is
#    read, shipped or attached to a ticket by people with no business knowing
#    either. So the quoted identity runs are replaced by a fixed marker.
#  * NON-CONSEQUENCE, and the reason this is safe: none of it touches a STORED
#    value. `SQL-Err`, `SQL-Msg` and `SQL-State` are linkage fields, and
#    `DbErrorStatus` keeps carrying them exactly as the driver produced them,
#    fitted only to their picture widths. FS-Reply, WE-Error and SQLSTATE are
#    likewise untouched, and so is every branch that reads them. Redaction
#    applies to the log RENDERING and nowhere else, so no compared value, no
#    disposition and no table dump moves by a character (rules R-3, R-4).
#
#  The three functions are published because three modules need the identical
#  treatment - this one, `dal/connection.py` and `dal/cursor_state.py` - and
#  three copies of a redaction rule is three chances for one to be the weak one.
# =============================================================================

#: The fixed marker that stands in for a removed identity or secret. A constant
#: rather than a literal at each site, so a log reader can grep for it and a
#: reviewer can see at a glance that a field was removed rather than absent.
LOG_REDACTION: Final[str] = "[redacted]"

#: Appended when a diagnostic is cut short by :data:`LOG_FIELD_MAX_CHARS`.
LOG_ELISION: Final[str] = "[...]"

#: The rendered length one diagnostic field may occupy in a log record.
#:
#: `SQL-Msg` is `pic x(512)` [copybooks/wsfnctn.cob:L50] and the driver's own
#: strings are unbounded before they are fitted to it, so an unbounded log line
#: is a denial-of-service surface: a failure that repeats a thousand times fills
#: a disk with padding. 200 characters is comfortably more than every driver
#: message this cycle can provoke and still bounds the record. The STORED field
#: is unaffected and stays at its full 512.
LOG_FIELD_MAX_CHARS: Final[int] = 200

#: The category reported for an error number this module does not recognise.
LOG_CATEGORY_UNCLASSIFIED: Final[str] = "unclassified"

#: Codepoints replaced by their own escape spelling before text is logged.
#:
#: The C0 range covers carriage return, line feed and ESC - the three that make
#: forgery possible - and DELETE plus the C1 range cover the terminal-control
#: codes some emulators still honour. U+2028 and U+2029 are included because
#: they are line breaks to a reader that splits on Unicode line boundaries even
#: though they are not C0.
_CONTROL_CODEPOINTS: Final[tuple[int, ...]] = (
    *range(0x00, 0x20),
    0x7F,
    *range(0x80, 0xA0),
    0x2028,
    0x2029,
)


def _control_character_escapes() -> Mapping[int, str]:
    """Build the translation table :func:`sanitise_for_log` applies.

    Returns:
        A read-only mapping from each codepoint of :data:`_CONTROL_CODEPOINTS`
        to the text `\\xNN` or `\\uNNNN`, so that the escape a reader sees is
        the codepoint that was actually present.
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

#: The identity and secret shapes removed from driver text, in application
#: order. Each is keyed to a message the MySQL client library actually produces,
#: and the surrounding words are KEPT: an operator needs to know that the
#: failure was an access denial, and needs not to know which account it was.
_REDACTION_RULES: Final[tuple[tuple[re.Pattern[str], str], ...]] = (
    # "Access denied for user 'ACAS-User'@'localhost' (using password: YES)"
    (
        re.compile(r"(?i)\bfor user\s+'[^']*'(?:@'[^']*')?"),
        "for user " + LOG_REDACTION,
    ),
    # The bare 'user'@'host' pair, wherever else it appears.
    (re.compile(r"'[^']*'@'[^']*'"), LOG_REDACTION),
    # The driver's own report of whether a password was sent. Deliberately
    # `[A-Za-z]+` rather than `\S+`: the driver writes YES or NO and the word is
    # followed by a closing parenthesis that belongs to the message, not to the
    # value, and swallowing it would leave the rendering unbalanced.
    (
        re.compile(r"(?i)\busing password:\s*[A-Za-z]+"),
        "using password: " + LOG_REDACTION,
    ),
    # Any explicit password assignment, however spelled. Two exclusions keep it
    # from damaging what the rules above have already produced: the value may not
    # itself be the redaction marker, and it stops at a closing parenthesis,
    # which belongs to the surrounding message rather than to the value.
    (
        re.compile(
            r"(?i)\b(pass(?:wd|word|phrase))\s*[=:]\s*"
            r"(?!" + re.escape(LOG_REDACTION) + r")[^\s)]+"
        ),
        "\\g<1>=" + LOG_REDACTION,
    ),
    # "Can't connect to MySQL server on 'db.internal:3306' (111)", "Can't
    # connect to local MySQL server through socket '/run/mysqld/x.sock' (2)",
    # "Unknown database 'ACASDB'".
    (
        re.compile(
            r"(?i)\b(server|host|socket|database|schema)"
            r"\s+(?:on\s+|through\s+)?'[^']*'"
        ),
        "\\g<1> " + LOG_REDACTION,
    ),
)

#: Stable low-cardinality categories for the error numbers this cycle can meet.
#:
#: NOTHING BRANCHES ON THIS TABLE. It exists so that a log record carries a
#: token an operator can grep and alert on without the redacted message text,
#: and it must never be consulted by code that decides an FS-Reply, a WE-Error
#: or a control transfer - those come from the frozen source alone, and adding a
#: second opinion here would be behaviour the compiled program does not have.
#: Growing the table changes no disposition; it only makes a log line more
#: legible.
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
    """Render ``text`` so that it cannot forge or distort a log record.

    Control characters become their own escape spelling and the result is cut to
    ``limit`` characters. Nothing else changes: this is a rendering, and the
    caller's own copy of the text is untouched.

    Args:
        text: the text to render. Driver-supplied text is the expected case.
        limit: the rendered length allowed before the tail is elided.

    Returns:
        A single-line rendering, at most ``limit`` characters plus
        :data:`LOG_ELISION`.

        >>> sanitise_for_log("first\\r\\nWARNING forged second")
        'first\\\\x0d\\\\x0aWARNING forged second'
        >>> sanitise_for_log("abcdef", limit=3)
        'abc[...]'
    """
    escaped = text.translate(_CONTROL_CHARACTER_ESCAPES)
    if len(escaped) <= limit:
        return escaped
    return escaped[:limit] + LOG_ELISION


def redact_for_log(text: str, *, limit: int = LOG_FIELD_MAX_CHARS) -> str:
    """Remove identities and secrets from ``text``, then render it log-safe.

    The rules are applied in the order of :data:`_REDACTION_RULES` and the
    result is passed through :func:`sanitise_for_log`, so one call is enough at
    a log site. USE THIS, not :func:`sanitise_for_log`, for anything the
    database driver produced.

    Args:
        text: the driver-supplied text.
        limit: as :func:`sanitise_for_log`.

    Returns:
        The redacted, sanitised rendering.

        >>> redact_for_log(
        ...     "Access denied for user 'ACAS-User'@'localhost' "
        ...     "(using password: YES)"
        ... )
        'Access denied for user [redacted] (using password: [redacted])'
        >>> redact_for_log("Unknown database 'ACASDB'")
        'Unknown database [redacted]'
    """
    redacted = text
    for pattern, replacement in _REDACTION_RULES:
        redacted = pattern.sub(replacement, redacted)
    return sanitise_for_log(redacted, limit=limit)


def db_error_log_category(errno: int | str, sql_state: str = "") -> str:
    """Classify a driver failure into a stable token safe to log and alert on.

    Derived from the error number and the SQLSTATE ONLY - never from the
    message - so the result carries no host name, no account and no data value,
    and is identical for every occurrence of the same fault. That stability is
    the point: an operator can alert on ``access-denied`` without the redacted
    message text being parseable at all.

    NOT A DISPOSITION. The FS-Reply and WE-Error a failure produces come from
    `mysql_1100_db_error` and `mysql_1300_db_error`, which read the frozen
    source; this function is consulted by log sites and by nothing else.

    Args:
        errno: the driver's error number, as text or as an integer.
        sql_state: the driver's SQLSTATE, used only for the duplicate-key case
            the bridge itself recognises [copybooks/mysql-procedures.cpy:L99].

    Returns:
        One of the tokens of :data:`_LOG_CATEGORY_BY_ERRNO`, or
        ``"duplicate-key"``, ``"lock"`` or :data:`LOG_CATEGORY_UNCLASSIFIED`.

        >>> db_error_log_category(1045)
        'access-denied'
        >>> db_error_log_category("1062")
        'duplicate-key'
        >>> db_error_log_category("1036")
        'lock'
        >>> db_error_log_category(0)
        'unclassified'
    """
    number = str(errno).strip()
    if number in DUPLICATE_KEY_ERRNOS or sql_state.strip() == DUPLICATE_KEY_SQLSTATE:
        return "duplicate-key"
    if number in LOCK_ERRNOS:
        return "lock"
    return _LOG_CATEGORY_BY_ERRNO.get(number, LOG_CATEGORY_UNCLASSIFIED)




@dataclass(frozen=True, slots=True)
class DbErrorStatus:
    """The outcome of mapping one driver failure onto the ACAS status protocol.

    Frozen, because a status is a fact about something that already happened.
    Callers that need it in a record apply it with
    :meth:`apply_to_logging_data`.

    The three text fields arrive already truncated and space-padded to their
    picture widths, so applying them to a record cannot change a field's
    length.
    """

    #: `Fs-Reply` [copybooks/wsfnctn.cob:L25]. Either
    #: `FsReply.DUPLICATE_KEY` from [copybooks/mysql-procedures.cpy:L103] or
    #: `FsReply.ERROR` from [copybooks/mysql-procedures.cpy:L127].
    fs_reply: FsReply

    #: `We-Error` [copybooks/wsfnctn.cob:L23]. `WeError.RDB_INIT_ERROR` on the
    #: generic path [copybooks/mysql-procedures.cpy:L128] - anomaly N3 - or
    #: whatever the field already held, untouched, on the duplicate path,
    #: whose `go to Mysql-1190-Exit` [:L104] jumps past that statement.
    #:
    #: Typed `int` rather than `WeError` because a caller may legitimately be
    #: carrying a code outside the closed set: the table's own
    #: `Other = any other rdbms errors` [common/glpostingMT.cbl:L154-L155].
    we_error: int

    #: `SQL-Err pic x(5)` [copybooks/wsfnctn.cob:L49]. Written by the BRIDGE,
    #: e.g. `move WS-MYSQL-Error-Number to SQL-Err`
    #: [common/glpostingMT.cbl:L816], not by the driver paragraph.
    sql_err: str

    #: `SQL-Msg pic x(512)` [copybooks/wsfnctn.cob:L50]. Also written by the
    #: bridge, e.g. [common/glpostingMT.cbl:L817].
    sql_msg: str

    #: `SQL-State pic x(5)` [copybooks/wsfnctn.cob:L51]. Written by the driver
    #: paragraph at [copybooks/mysql-procedures.cpy:L123] on the generic path
    #: ONLY - see `duplicate_key` below - and independently by each bridge,
    #: e.g. [common/glpostingMT.cbl:L813].
    sql_state: str

    #: ``True`` if the duplicate-key early exit was taken, i.e. if `go to Mysql-1190-Exit`
    #: [copybooks/mysql-procedures.cpy:L104] fired. Published because that jump skips real
    #: work, and a caller reproducing the DRIVER PARAGRAPH in isolation needs to know it
    #: happened: the statements at [:L107] (fetch message) and [:L122-L123] (fetch and store
    #: SQLSTATE) are all bypassed, so the paragraph leaves `SQL-State` untouched on this path.
    #: The values reported in the three text fields above are what the BRIDGE-level write path
    #: leaves in the record, since each bridge stores all three itself before testing
    #: [common/glpostingMT.cbl:L813-L817]. A caller that must reproduce the paragraph's skip
    #: exactly should test this flag and decline to apply the text fields.
    duplicate_key: bool

    def apply_to_logging_data(self, logging_data: LoggingData) -> None:
        """Write the three diagnostic fields into a ``Logging-Data`` block.

        Reproduces what the bridge-level error path leaves in the record:
        ``SQL-Err``, ``SQL-Msg`` and ``SQL-State`` all populated
        [common/glpostingMT.cbl:L813-L817]. The status pair is deliberately
        NOT written here, because ``Fs-Reply`` and ``We-Error`` live on
        ``File-Access`` itself rather than in this sub-block
        [copybooks/wsfnctn.cob:L23-L25] - the caller sets those on the record
        it already holds.

        Args:
            logging_data: The ``LoggingData`` instance to update, owned by
                ``records/file_access.py``. Mutated in place, as the COBOL
                ``MOVE`` statements mutate the record.
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

    Reproduces [copybooks/mysql-procedures.cpy:L96-L128], the paragraph every one
    of the twenty in-scope bridges reaches for on any failed statement -
    ``Mysql-1210-Command`` performs it at [:L176], and ``Mysql-1200-Select``,
    ``Mysql-1220-Store-Result``, ``Mysql-1240-Switch-Db`` and ``Mysql-1000-Open``
    all do the same. It has exactly two outcomes, in this order.

    **1. The duplicate-key early exit.** If :func:`is_duplicate_key_driver_level`
    holds, ``move 22 to fs-Reply`` [:L103] and ``go to Mysql-1190-Exit`` [:L104].
    ``We-Error`` is NOT touched, so it keeps whatever it held; the jump also skips
    the message fetch at [:L107] and the SQLSTATE fetch and store at [:L122-L123].

    **2. Everything else.** ``(99, 911)``, unconditionally.

    *** ANOMALY N3 - REPRODUCED, NOT FIXED (rule R-4) ***

    The last two statements of the paragraph are not guarded by anything::

        L127     move     99 to fs-Reply.
        L128     move     911 to We-Error.

    [copybooks/mysql-procedures.cpy:L127-L128]. So a missing table, a syntax
    error, a constraint violation, a dropped connection and - because the retry
    ladder of anomaly N1 is dead - a locked table are ALL reported as
    ``We-Error 911``, which the authoritative table documents as ``Rdb Error
    during initializing, possibly can not connect to database``
    [common/glpostingMT.cbl:L143-L144]. Returning anything more accurate would be
    a defect fix, which rule R-4 makes a failure. Callers narrow the code
    AFTERWARDS, the bridges' own idiom - see
    :data:`WE_ERROR_OVERRIDE_BY_FILE_FUNCTION` and
    :func:`override_we_error_for_operation`.

    On the diagnostic side this reproduces the native equivalent of three foreign
    calls - ``call "MySQL_errno"`` [:L97], ``call "MySQL_error"`` [:L107] and
    ``call "MySQL_sqlstate"`` [:L122] - by taking their results as arguments.
    Nothing is called out of process (rule R-1). A log record stands in for
    ``Mysql-1110-Report-Problem`` [:L130-L137], whose two displays become the
    record and whose ``accept ws-reply`` [:L136] pause is dropped per Agent Action
    Plan section 0.3.4; it changes no control flow and reaches no table.

    Args:
        errno: The driver's error number AS TEXT - see
            :data:`DUPLICATE_KEY_ERRNOS` for why text and not an integer.
        message: The driver's error message, the equivalent of
            ``Ws-Mysql-Error-Message``. Truncated to 512 characters on the way
            into ``SQL-Msg``.
        sql_state: The driver's SQLSTATE, the equivalent of ``WS-MYSQL-SqlState``.
        command: The statement text that failed. Consulted ONLY by the duplicate
            test, and only its first six characters.
        we_error: The value ``We-Error`` already holds. Returned unchanged on the
            duplicate path, because the COBOL jump skips the statement that would
            overwrite it. Defaults to ``WeError.SUCCESS``, the value a handler
            starts an operation with.

    Returns:
        A :class:`DbErrorStatus` with the fields already fitted to their picture
        widths.

        >>> status = mysql_1100_db_error(
        ...     errno="1062",
        ...     message="Duplicate entry '1' for key 'PRIMARY'",
        ...     sql_state="23000",
        ...     command="INSERT INTO `GLPOSTING-REC` VALUES (1)",
        ... )
        >>> status.fs_reply
        <FsReply.DUPLICATE_KEY: 22>
        >>> status.duplicate_key
        True
        >>> int(status.we_error)                      # untouched by the jump
        0

        >>> generic = mysql_1100_db_error(
        ...     errno="1146",
        ...     message="Table 'ACASDB.GLPOSTING-REC' doesn't exist",
        ...     sql_state="42S02",
        ...     command="SELECT * FROM `GLPOSTING-REC`",
        ... )
        >>> generic.fs_reply, generic.we_error       # anomaly N3
        (<FsReply.ERROR: 99>, <WeError.RDB_INIT_ERROR: 911>)
        >>> len(generic.sql_err), len(generic.sql_state), len(generic.sql_msg)
        (5, 5, 512)
        >>> generic.sql_err
        '1146 '
    """
    # `move WS-MYSQL-Error-Number to SQL-Err` / `... Error-Message to SQL-Msg`
    # / `... SqlState to SQL-State` - the bridge's own stores, e.g.
    # [common/glpostingMT.cbl:L813], [:L816] and [:L817]. Fitted to the
    # picture widths at [copybooks/wsfnctn.cob:L49-L51].
    fitted_err = _pic_x(errno, SQL_ERR_WIDTH)
    fitted_msg = _pic_x(message, SQL_MSG_WIDTH)
    fitted_state = _pic_x(sql_state, SQL_STATE_WIDTH)

    # OUTCOME 1: `if Ws-Mysql-Error-Number = "1062" or = "1022"` with the
    # INSERT-only `evaluate` [copybooks/mysql-procedures.cpy:L99-L105], then
    # `move 22 to fs-Reply` [:L103] and `go to Mysql-1190-Exit` [:L104]. The
    # jump is why `we_error` is passed straight through rather than replaced:
    # it never reaches the `move 911` at [:L128].
    if is_duplicate_key_driver_level(errno, command):
        return DbErrorStatus(
            fs_reply=FsReply.DUPLICATE_KEY,
            we_error=we_error,
            sql_err=fitted_err,
            sql_msg=fitted_msg,
            sql_state=fitted_state,
            duplicate_key=True,
        )

    # OUTCOME 2: the fall-through. Note what does NOT happen between the
    # duplicate test and the two moves below: the SQLSTATE dispositions block
    # at [copybooks/mysql-procedures.cpy:L109-L119] is comment, and the one
    # test that would have read the value it describes is commented out at
    # [:L124]. So `SQL-State` is stored and then never consulted - anomaly N4.
    # Six of the seven entries of DOCUMENTED_SQLSTATE_MAPPINGS record that.
    # *** ANOMALY N3 *** - unconditional, for EVERY non-duplicate error:
    #     L127   move     99 to fs-Reply.
    #     L128   move     911 to We-Error.
    # [copybooks/mysql-procedures.cpy:L127-L128]
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
    # The two ACAS status values are interpolated as themselves: they are
    # integers drawn from this module's own enumerations, so neither can carry a
    # control character or an identity. The driver's SQLSTATE, error number and
    # message cannot make that claim, so each goes through the log-safety
    # functions above, and the number is additionally reported as a stable
    # category an operator can alert on (CWE-117, CWE-532). The status object
    # returned below still carries all three driver fields exactly as the driver
    # produced them, fitted only to their picture widths - the redaction is a
    # property of this log record and of nothing else.
    _LOG.error(
        "ACAS file handler: FS-Reply=%d WE-Error=%d SQLSTATE=%s errno=%s "
        "category=%s: %s "
        "[reproduces the unconditional (99, 911) of "
        "copybooks/mysql-procedures.cpy:L127-L128 - WE-Error 911 is a "
        "catch-all here, not evidence of a connect failure]",
        int(status.fs_reply),
        int(status.we_error),
        sanitise_for_log(sql_state, limit=SQL_STATE_WIDTH),
        sanitise_for_log(errno, limit=SQL_ERR_WIDTH),
        db_error_log_category(errno, sql_state),
        redact_for_log(message),
    )
    return status


#: The per-operation narrowings of the 911 catch-all - the SECOND stage of anomaly N3. Two of
#: the bridge's operations refuse to leave 911 in place: each performs the generic paragraph,
#: lets it set `(99, 911)`, then overwrites the detail code with something specific -
#: `ba080-Process-Delete` moves 99 to fs-reply and 995 to WE-Error
#: [common/glpostingMT.cbl:L874-L875], `ba090-Process-Rewrite` moves 99 and 994
#: [:L1001-L1002]. Both re-state `move 99 to fs-reply` even though the generic paragraph has
#: already set it - harmless, and preserved as written by `override_we_error_for_operation`,
#: which likewise returns FS-Reply 99. The others do not narrow: the write path leaves
#: `We-Error` entirely alone [:L818-L824] and read-indexed sets its own pair from scratch
#: [:L668-L669], [:L676-L677]. So this mapping has exactly two entries and must not grow.
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
    everything; delete and rewrite then replace it with 995 and 994
    respectively, AFTER the generic paragraph has returned
    [common/glpostingMT.cbl:L874-L875] and [:L1001-L1002].

    Two-stage rather than one because that is the shape of the COBOL: the
    generic paragraph cannot know which verb invoked it, so the verb corrects
    the record afterwards. Reproducing it as a single mapper that already knew
    the verb would collapse a distinction the frozen source makes, and would
    lose the fact that any verb WITHOUT an override silently keeps 911.

    Only the duplicate-key case is exempt: on that path the bridges do not
    reach an override at all, so a status carrying ``duplicate_key`` is
    returned untouched.

    Args:
        status: The result of :func:`mysql_1100_db_error`.
        file_function: The ``File-Function`` value of the operation that
            failed.

    Returns:
        A new :class:`DbErrorStatus` with the narrowed code, or ``status``
        itself when the verb has no override. The three text fields are
        carried over unchanged - neither override site touches them.

        >>> failure = mysql_1100_db_error(
        ...     errno="1451", message="constraint fails", sql_state="23000",
        ...     command="DELETE FROM `GLPOSTING-REC` WHERE 1=1",
        ... )
        >>> failure.we_error
        <WeError.RDB_INIT_ERROR: 911>
        >>> override_we_error_for_operation(failure, FileFunction.DELETE).we_error
        <WeError.DELETE_SQLSTATE_NOT_00000: 995>
        >>> override_we_error_for_operation(failure, FileFunction.RE_WRITE).we_error
        <WeError.REWRITE_SQLSTATE_NOT_00000: 994>
        >>> override_we_error_for_operation(failure, FileFunction.WRITE).we_error
        <WeError.RDB_INIT_ERROR: 911>
    """
    if status.duplicate_key:
        return status
    try:
        verb = FileFunction(int(file_function))
    except ValueError:
        # An unrecognised verb gets no override, which leaves 911 standing -
        # the same outcome as any verb the two override sites do not cover.
        return status
    narrowed = WE_ERROR_OVERRIDE_BY_FILE_FUNCTION.get(verb)
    if narrowed is None:
        return status
    # Both sites also re-state `move 99 to fs-reply`, so FS-Reply stays 99.
    return DbErrorStatus(
        fs_reply=FsReply.ERROR,
        we_error=narrowed,
        sql_err=status.sql_err,
        sql_msg=status.sql_msg,
        sql_state=status.sql_state,
        duplicate_key=False,
    )


#  ANOMALY N1 - THE LOCK-RETRY BACKOFF LADDER THAT IS DEAD CODE. `Mysql-1300-DB-Error`
#  [copybooks/mysql-procedures.cpy:L209-L255] is a working four-rung backoff over three lock
#  errnos that is never called: its ONLY `perform` is commented out at [:L167], with the 910
#  test at [:L168] and the retry test at [:L171-L174], while the live `perform` at [:L176]
#  reaches the generic paragraph. Hence, each by grep: 910 unreachable (set only at [:L245]);
#  nothing retried (`WS-SQL-Retry` [copybooks/mysql-variables.cpy:L104] set to 1 only at
#  [:L254]); ratchet frozen (`WS-Mysql-Time-Step` [:L105] advanced only there, zeroed at
#  [copybooks/mysql-procedures.cpy:L64-L65]); a lock misreported `(99, 911)`; the exit advice
#  at [:L180] unsatisfiable; all twenty bridges carry it unreachable. The prose errs too - 910
#  is documented as a 5-second lock [common/glpostingMT.cbl:L149] against rungs waiting 6.75s.
#  It stays uncalled and waitless; wiring it up would add resilience the COBOL cycle lacks,
#  which rule R-4 forbids.

#: The three MySQL error numbers the dead ladder would have treated as recoverable locks, with
#: the frozen source's own comments `not = "1027"  *> HY000 - Locked against change`, `not =
#: "1036"  *> HY000 - Table Read Only`, `not = "1099"  *> HY000 - Locked with Read lock`,
#: falling through to `go to Mysql-1390-Exit.  *> Not interested as it's not a LOCK problem.`
#: [copybooks/mysql-procedures.cpy:L218-L220]. Strings for the same reason as
#: `DUPLICATE_KEY_ERRNOS`: the COBOL field is alphanumeric and the comparison is textual. All
#: three share SQLSTATE `HY000`, which is one more reason the SQLSTATE map of anomaly N4 could
#: not have distinguished them even if it had been wired up.
LOCK_ERRNOS: Final[frozenset[str]] = frozenset({"1027", "1036", "1099"})


@dataclass(frozen=True, slots=True)
class LockRetryRung:
    """One rung of the dead lock-retry ladder of anomaly N1.

    A description of a wait, NOT a wait. Nothing in this class or in
    :func:`mysql_1300_db_error` blocks: the duration is data the caller may
    inspect, and rule R-6 forbids this module from depending on wall-clock
    time. A dead function that would have slept must not be reproduced as a
    live function that does.
    """

    #: The `WS-Mysql-Time-Step` value this rung fires on.
    time_step_before: int

    #: The value it ratchets the step to. Never reset by this paragraph - only
    #: `Mysql-1000-Open` clears it
    #: [copybooks/mysql-procedures.cpy:L64-L65] - so a run climbs the ladder
    #: once and stays at the top.
    time_step_after: int

    #: The wait in INTEGER NANOSECONDS, or ``None`` when the frozen source
    #: expresses this rung in whole seconds instead.
    #:
    #: Integers because rule R-2 admits no binary floating-point value
    #: anywhere in this module, and because they are exactly the literals the
    #: frozen source writes - `250000000` and `500000000`, not a fraction of a
    #: second.
    nanoseconds: int | None

    #: The wait in INTEGER SECONDS, or ``None`` when the rung is expressed in
    #: nanoseconds.
    seconds: int | None

    #: The foreign routine the rung would have called. Recorded for
    #: traceability and NEVER invoked - rule R-1 admits no out-of-process call
    #: from this package.
    routine: str

    #: The blinking status line the rung would have displayed, or ``None`` for
    #: the first rung, which displays nothing. Per Agent Action Plan section
    #: 0.3.4 these are diagnostics with no database effect, so they are
    #: recorded rather than rendered.
    display: str | None

    #: Locator of the rung in the frozen source.
    locator: str


#: The four rungs, in the order the nested ``if`` chain tests them
#: [copybooks/mysql-procedures.cpy:L223-L242].
#:
#: The ratchet runs 0 -> 1 -> 2 -> 4 -> 8, doubling after the first step, and
#: is never reset by this paragraph. A fifth failure finds the step at 8,
#: matches no rung, and falls into the ``else`` at [:L244-L248] which sets the
#: unreachable ``(99, 910)``.
#:
#: Published as inspectable data precisely so that the migration anomaly log
#: and the anomaly-locking tests a later boundary adds can assert on the
#: ladder's shape WITHOUT calling :func:`mysql_1300_db_error` - because
#: calling it is the one thing that must never happen.
LOCK_RETRY_LADDER: Final[tuple[LockRetryRung, ...]] = (
    # L223   if       WS-Mysql-Time-Step = zero
    # L224            move 1 to WS-Mysql-Time-Step
    # L225            call "CBL_OC_NANOSLEEP" using 250000000    *> 1/4 sec
    LockRetryRung(
        time_step_before=0,
        time_step_after=1,
        nanoseconds=250000000,
        seconds=None,
        routine="CBL_OC_NANOSLEEP",
        display=None,
        locator="[copybooks/mysql-procedures.cpy:L223-L225]",
    ),
    # L227    if      WS-Mysql-Time-Step = 1
    # L228            move 2 to WS-Mysql-Time-Step
    # L229            display "Waiting < sec " at line ws-lines col 1 blink
    # L230            call "CBL_OC_NANOSLEEP" using 500000000    *> 1/2 sec
    LockRetryRung(
        time_step_before=1,
        time_step_after=2,
        nanoseconds=500000000,
        seconds=None,
        routine="CBL_OC_NANOSLEEP",
        display="Waiting < sec ",
        locator="[copybooks/mysql-procedures.cpy:L227-L230]",
    ),
    # L233     if     WS-Mysql-Time-Step = 2
    # L234            move 4 to WS-Mysql-Time-Step
    # L235            display "Waiting 1 sec " at line ws-lines col 1 blink
    # L236            call "C$SLEEP" using 1    *> 1 sec
    LockRetryRung(
        time_step_before=2,
        time_step_after=4,
        nanoseconds=None,
        seconds=1,
        routine="C$SLEEP",
        display="Waiting 1 sec ",
        locator="[copybooks/mysql-procedures.cpy:L233-L236]",
    ),
    # L239      if    WS-Mysql-Time-Step = 4
    # L240            move 8 to WS-Mysql-Time-Step
    # L241            display "Waiting 5 secs" at line ws-lines col 1 blink
    # L242            call "C$SLEEP" using 5    *> 5 sec
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

    The predicate exists to make anomaly N1 assertable, not to change any
    behaviour. A ``True`` answer changes NOTHING about the status a caller
    reports: :func:`mysql_1100_db_error` maps a lock to ``(99, 911)`` like any
    other non-duplicate error, with no wait and no retry, because the ladder
    that would have handled it is unreachable.

    That follows from the frozen control flow - the ladder's only ``perform``
    is commented out [copybooks/mysql-procedures.cpy:L167], so a lock reaches
    ``Mysql-1100-Db-Error`` and nothing else - and it must be preserved.
    Using this predicate to trigger a wait, a retry, or a
    ``We-Error`` of 910 would give the Python cycle a resilience the COBOL
    cycle does not have, and rule R-4 makes a defect fixed a failure.

    Args:
        errno: The driver's error number as text.

    Returns:
        ``True`` for ``"1027"``, ``"1036"`` or ``"1099"``
        [copybooks/mysql-procedures.cpy:L218-L220].

        >>> is_lock_errno("1027")
        True
        >>> is_lock_errno("1146")
        False

        And the live path is unmoved by it - no wait, no retry, 911:

        >>> locked = mysql_1100_db_error(
        ...     errno="1099", message="Table 'x' was locked with a READ lock",
        ...     sql_state="HY000", command="UPDATE `GLLEDGER-REC` SET x = 1",
        ... )
        >>> locked.fs_reply, locked.we_error
        (<FsReply.ERROR: 99>, <WeError.RDB_INIT_ERROR: 911>)
    """
    return errno in LOCK_ERRNOS


def mysql_1300_db_error(
    errno: str, time_step: int
) -> tuple[int, LockRetryRung | None, tuple[FsReply, WeError] | None]:
    """DEAD CODE, reproduced unreachable: see [copybooks/mysql-procedures.cpy:L167].

    Reproduces ``Mysql-1300-DB-Error`` [copybooks/mysql-procedures.cpy:L209-L255].
    **It must never be called.** The only ``perform`` of that paragraph anywhere in
    the repository is commented out at [:L167], so no live COBOL path reaches it,
    and reproducing this defect means keeping the Python equivalent equally
    unreached: it has zero call sites in ``acas_posting`` and must keep zero.
    Wiring it up would give the migrated cycle a lock-retry behaviour the compiled
    cycle does not have, which rule R-4 makes a failure rather than an improvement.

    It exists at all for two reasons: rule R-5 asks that every paragraph
    reproduced keep a function named after it, so a reader following the COBOL
    finds a counterpart; and the anomaly log needs something concrete to point at
    when it claims the ladder was fully written before being abandoned.

    **It performs no wait.** Rule R-6 forbids this module any dependence on
    wall-clock time, and a dead function that would have slept must not become a
    live one that does. The rung it selects is RETURNED as data, its duration an
    integer count of nanoseconds or seconds; the two foreign sleep routines named
    at [:L225], [:L230], [:L236] and [:L242] are recorded on the rung and never
    invoked, which rule R-1 requires in any case.

    The logic reproduced, faithfully:

    1. ``move zero to WS-SQL-Retry`` [:L215] - the retry flag is cleared on entry,
       which is why it can only ever hold zero anywhere else.
    2. If the errno is not one of the three lock codes, ``go to Mysql-1390-Exit``
       [:L218-L221], having changed nothing.
    3. Otherwise walk the nested ``if`` chain [:L223-L242] for the rung matching
       the current ``WS-Mysql-Time-Step``, ratchet the step, and (in COBOL) wait.
    4. If no rung matches - the step has already reached 8 - set the unreachable
       pair ``(99, 910)`` [:L245-L246] and exit [:L248].
    5. On any rung that did match, ``move 1 to WS-SQL-Retry`` [:L254] and exit
       [:L255], asking the caller to retry the statement.

    THE RATCHET IS NOT RESET HERE, deliberately: step 1 clears the retry flag but
    never the step, so the ladder climbs monotonically for the life of the
    connection and only ``Mysql-1000-Open`` zeroes it [:L64-L65]. A caller must
    thread the step through successive calls, which is why it is a parameter and a
    return value rather than module state - module state would also break the
    determinism rule R-6 requires.

    Args:
        errno: The driver's error number as text, standing in for the result of
            ``call "MySQL_errno"`` at [:L217].
        time_step: The current ``WS-Mysql-Time-Step``
            [copybooks/mysql-variables.cpy:L105]. Zero on a fresh connection.

    Returns:
        A triple ``(next_time_step, rung, exhausted_status)``:

        * ``next_time_step`` - the ratcheted step to carry to the next call,
          unchanged when nothing matched;
        * ``rung`` - the :class:`LockRetryRung` that fired, or ``None``. A rung
          means the COBOL would have waited and then set ``WS-SQL-Retry`` to 1 at
          [:L254], i.e. asked for a retry;
        * ``exhausted_status`` - ``(99, 910)`` when the ladder is exhausted
          [:L245-L246], else ``None``. That pair is the unreachable
          ``WeError.TABLE_LOCKED``, which no live path can produce.

    ILLUSTRATION, DELIBERATELY NOT A DOCTEST
        A non-executable literal block rather than ``>>>`` examples, because a
        doctest is a call site: it would make this paragraph run, and reproducing
        anomaly N1 means it never runs. The assertable surface is
        :data:`LOCK_RETRY_LADDER`, which is plain data and needs no call. Walking
        the ladder from a fresh connection would give::

            step = 0                     ->  (1, rung 250000000 ns, None)
            step = 1                     ->  (2, rung 500000000 ns, None)
            step = 2                     ->  (4, rung 1 s,          None)
            step = 4                     ->  (8, rung 5 s,          None)
            step = 8   ladder exhausted  ->  (8, None, (99, 910))
            errno "1146", any step       ->  (step, None, None)

        The fifth line is the pair no caller can reach in the frozen source, and
        the sixth is `go to Mysql-1390-Exit` [:L218-L221] leaving everything alone.
    """
    # L215: `move zero to WS-SQL-Retry.` The flag is cleared on entry. Because
    # this paragraph is unreachable, that clearing is also the reason the flag
    # holds zero everywhere else in the system.
    # L217-L221: `call "MySQL_errno" ...` then, if the code is none of the
    # three locks, `go to Mysql-1390-Exit  *> Not interested as it's not a
    # LOCK problem.` Nothing is changed on the way out.
    if not is_lock_errno(errno):
        return time_step, None, None

    # L223-L242: the nested `if` chain over WS-Mysql-Time-Step. Expressed as a
    # search of LOCK_RETRY_LADDER so that the rung table is the single
    # definition of the ladder's shape and cannot drift from the chain.
    for rung in LOCK_RETRY_LADDER:
        if time_step == rung.time_step_before:
            # In COBOL: ratchet the step, display the blinking status line,
            # and call the sleep routine named on the rung. Here: ratchet, and
            # return the rung so its duration and display can be inspected.
            # NO WAIT IS PERFORMED - see this function's docstring.
            # L254: `move 1 to WS-SQL-Retry.` - a matched rung means "retry
            # the statement", which the returned rung signals to the caller.
            # L255: `go to Mysql-1390-Exit.`
            return rung.time_step_after, rung, None

    # L244-L248: `else  *> well after 5 secs it should be released so error.`
    #     move 910 to WE-Error / move 99 to FS-Reply
    #     call "MySQL_error" using Ws-Mysql-Error-Message
    #     go to Mysql-1390-Exit.     *>  Test for, after exit
    # `WeError.TABLE_LOCKED` is produced HERE AND NOWHERE ELSE in the entire
    # frozen tree, which is exactly why no caller can ever see it. The step is
    # returned unchanged: the chain has no arm for a step of 8, so nothing
    # ratchets it further.
    return time_step, None, (FsReply.ERROR, WeError.TABLE_LOCKED)


#  TESTING A STATUS
#  A caution that governs this whole section: THE COBOL DOES NOT RAISE. Every
#  handler returns a status pair in the record and every caller tests it
#  inline, then decides. There is no exception mechanism to reproduce, so a
#  Python module that raised on a non-zero reply would be inventing control
#  flow the compiled program does not have - and control flow is behaviour.
#  `is_ok` is therefore the normal way to test a reply, and
#  `raise_for_status` is the exception, for the two places where the frozen
#  source itself stops.


class AcasFileHandlerError(Exception):
    """A file-handler status the frozen source treats as unrecoverable.

    Raised ONLY by :func:`raise_for_status`, and so only at the sites where
    the COBOL itself transfers control out of the program. The archetype is
    the IRS calling convention's shared error tail: each of its per-handler
    checks tests ``if fs-reply not = zero``, reports, closes the handler and
    jumps to a common paragraph that gives up outright
    [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L327-L332] and the rest::

        Open-Error-Continued.   *> If here we cannot continue as its a major failure
            ... displays ...
            accept   Accept-Reply     at 1335.
            goback.

    - ``goback`` at [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L364] returns
    from the program, which is the closest thing in the frozen source to a
    raised exception.

    Note the asymmetry this preserves, recorded in Agent Action Plan section
    0.6.5: the IRS convention has these per-handler checks and this hard exit,
    while the General/Sales/Purchase convention
    [copybooks/Proc-ACAS-FH-Calls.cob] has NO equivalent paragraph at all -
    its callers test the reply inline and carry on. So this exception belongs
    to one calling convention and not the other, and a General Ledger caller
    that raised it would be adding behaviour.
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
            operation: Optional description of the verb being attempted, for
                the message only.
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

    A subclass rather than a separate type because the frozen source treats it
    as a more severe case of the same thing, and a caller that wants to catch
    either can catch the base.

    ``901`` means the compiled record layout and the table row disagree in
    length. The authoritative table's wording is unusually emphatic
    [common/glpostingMT.cbl:L150-L153]::

        901  = File Def Record size not =< than ws record size
               Module needs ws definition changing to correct size
               FATAL, Stop using system, fix source code
               and recompile before using system again.

    and the handler acts on it, displaying the two lengths and then stopping
    rather than returning [common/acas008.cbl:L533-L540].
    """


def is_ok(fs_reply: int) -> bool:
    """Report whether a reply means the operation completed successfully.

    True for zero and nothing else, per
    ``0  = Operation completed successfully``
    [common/glpostingMT.cbl:L126].

    In particular ``FsReply.END_OF_FILE`` is NOT ok - end of file is a normal
    terminator but it is not a success, and a read loop must distinguish the
    two. Nor is ``FsReply.DUPLICATE_KEY``, which several posting paths handle
    as an expected outcome without it being a success.

    This is the normal way to test a reply, and it returns rather than raises
    because that is what the COBOL does at every one of its several hundred
    test sites.

    Args:
        fs_reply: An ``FS-Reply`` value; a plain ``int`` is accepted because
            that is what ``FileAccess.fs_reply`` holds.

    Returns:
        ``True`` only if the value is zero.

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

    **Ordinary non-zero replies are RETURNED, never raised.** The COBOL has no
    exception mechanism: every handler leaves its status in the record and
    every caller tests it inline with :func:`is_ok` and decides for itself.
    Calling this function IS the opt-in, and it must be called only where the
    frozen source itself stops or returns early. Sprinkling it over ordinary
    reply tests would replace a tested branch with a thrown exception, which
    changes control flow - and control flow is behaviour under rule R-4.

    The two sanctioned sites:

    1. **The IRS convention's per-handler error checks.** Each is literally
       ``if fs-reply not = zero`` followed by a report, a close and a jump to
       ``Open-Error-Continued``, which ends in ``goback``
       [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L327-L332] for ``acas008``,
       and identically at [:L334-L339], [:L341-L346] and [:L348-L353] for
       ``acasirsub1``, ``acasirsub3`` and ``acasirsub5``; the shared tail is
       at [:L355-L364]. Note the test is ANY non-zero value, end of file
       included - these checks run after an open, where end of file should not
       arise, but the test as written does not exclude it, and this function
       does not exclude it either.
    2. **The ``We-Error 901`` fatal disposition**, where the handler displays
       and stops [common/acas008.cbl:L533-L540].

    Args:
        fs_reply: The ``FS-Reply`` value to test.
        we_error: The accompanying ``We-Error``. A value of 901 selects
            :class:`AcasFileHandlerFatalError`.
        operation: Optional verb description, carried into the message.
        table: Optional table name, carried into the message.

    Returns:
        ``None``, when the reply is zero.

    Raises:
        AcasFileHandlerFatalError: If ``we_error`` is
            ``WeError.RECORD_SIZE_MISMATCH`` (901), whatever the reply -
            because the handler that sets 901 stops the run on the strength of
            the detail code alone, testing ``if WE-Error = 901``
            [common/acas008.cbl:L537].
        AcasFileHandlerError: If the reply is any other non-zero value,
            reproducing ``if fs-reply not = zero`` followed by ``goback``.

        >>> raise_for_status(FsReply.SUCCESS) is None
        True
        >>> raise_for_status(FsReply.ERROR, WeError.RDB_INIT_ERROR)
        Traceback (most recent call last):
            ...
        acas_posting.dal.status.AcasFileHandlerError: ACAS file handler failed: FS-Reply=99 WE-Error=911
        >>> raise_for_status(0, WeError.RECORD_SIZE_MISMATCH)
        Traceback (most recent call last):
            ...
        acas_posting.dal.status.AcasFileHandlerFatalError: ACAS file handler failed: FS-Reply=0 WE-Error=901
    """
    # `if WE-Error = 901` [common/acas008.cbl:L537] - tested on the detail
    # code alone, before and independently of the reply, because a length
    # mismatch is a programming error that no reply value can excuse.
    if int(we_error) == WeError.RECORD_SIZE_MISMATCH:
        raise AcasFileHandlerFatalError(
            fs_reply, we_error, operation=operation, table=table
        )

    # `if fs-reply not = zero` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L328]
    # and its three siblings, each ending at the `goback` of [:L364].
    if not is_ok(fs_reply):
        raise AcasFileHandlerError(
            fs_reply, we_error, operation=operation, table=table
        )


#  LOGGING-DATA VOCABULARY
#  `03  Logging-Data.` [copybooks/wsfnctn.cob:L44-L55]. Two of its fields
#  carry small closed vocabularies that are documented only in handler
#  comments, so they are collected here rather than left to be rediscovered.
#  The block's other fields are plain data and belong to
#  `records/file_access.py`.


class LogSystem(enum.IntEnum):
    """``ws-Log-System`` values - which subsystem is logging.

    `05  ws-Log-System   pic 9      value zero.       *> loaded by caller of FHlogger`
    [copybooks/wsfnctn.cob:L47]

    The vocabulary appears only as handler comments, and the two that spell it
    out do not quite agree. Verbatim:

        move     0      to WS-Log-System.   *> 0 = Params, 1 = IRS, 2=GL, 3=SL, 4=PL, 5=Stock, 4 FH logging
        [common/acas000.cbl:L324]

        move     1      to WS-Log-System.   *> 1 = IRS, 2=GL, 3=SL, 4=PL, 5=Stock - used in FH logging
        [common/acas008.cbl:L293]

    The first lists a value 0 for the parameter files and ends with a trailing
    ``4 FH logging`` that duplicates the number already assigned to Purchase;
    the second omits 0 altogether and starts at 1. The six members below are
    the union, and the stray trailing fragment is recorded here rather than
    modelled, because it names no distinct subsystem.

    Note that logging cannot in fact be switched off in this checkout: the
    frozen ``copybooks/Test-Data-Flags.cob`` hardcodes the testing switch on,
    so a run appends to the file-handler log regardless. That is a property of
    the frozen source, not something this module can or should change.

        >>> [int(member) for member in LogSystem]
        [0, 1, 2, 3, 4, 5]
    """

    #: `0 = Params` [common/acas000.cbl:L324] - the system parameter files,
    #: which is why `acas000` sets it.
    PARAMS = 0

    #: `1 = IRS` [common/acas000.cbl:L324], [common/acas008.cbl:L293].
    IRS = 1

    #: `2=GL` - General Ledger.
    GL = 2

    #: `3=SL` - Sales Ledger.
    SL = 3

    #: `4=PL` - Purchase Ledger.
    PL = 4

    #: `5=Stock` - present in both vocabularies, though the stock subsystem is
    #: outside this migration's scope.
    STOCK = 5


class ConnectStep(enum.IntEnum):
    """``ws-No-Paragraph`` values for the three steps of opening a connection.

    `05  ws-No-Paragraph pic 999.` [copybooks/wsfnctn.cob:L48]

    ``Mysql-1000-Open`` calls three driver routines in sequence and stamps a
    different identifier before each failure report, so that a connect failure
    can be attributed to the step that produced it. The changelog records why
    the stamping sits where it does, verbatim
    [copybooks/mysql-procedures.cpy:L45-L47]::

        *> version 008 -- Moved 'move 101,102,103..' to just before
        *>                'perform DB-Error..' in mysql-1000-open.
        *>                as it hides caller para lits if no errors

    i.e. the value is set immediately before the error report rather than at
    the top of each step, so that a successful open leaves the caller's own
    paragraph number in the field undisturbed.

    ``dal/connection.py`` sets these while opening a connection.

        >>> [int(member) for member in ConnectStep]
        [101, 102, 103]
    """

    #: `MySQL_init` failed - `move 101 to Ws-No-Paragraph`
    #: [copybooks/mysql-procedures.cpy:L68], guarded by the return-code test
    #: at [:L67]. The driver could not be initialised at all.
    INIT = 101

    #: `MySQL_real_connect` failed - `move 102 to Ws-No-Paragraph`
    #: [copybooks/mysql-procedures.cpy:L79], guarded by [:L78]. Host, user,
    #: password, port or socket is wrong, or the server is unreachable. The
    #: parameters come from the `RDB-Data` block
    #: [copybooks/wsfnctn.cob:L56-L62].
    REAL_CONNECT = 102

    #: `MySQL_selectdb` failed - `move 103 to Ws-No-Paragraph`
    #: [copybooks/mysql-procedures.cpy:L84], guarded by [:L83]. Connected, but
    #: the schema named in `DB-Schema` could not be selected.
    #:
    #: Unlike the first two, this failure does NOT jump to the exit: the
    #: `perform` at [:L85] ends the paragraph, so control falls through to
    #: `Mysql-1090-Exit` [:L87] either way. The distinction is immaterial
    #: here and is recorded only so that a reader comparing the three arms
    #: does not conclude a `go to` is missing.
    SELECT_DB = 103
