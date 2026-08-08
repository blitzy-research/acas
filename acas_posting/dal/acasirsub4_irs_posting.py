"""`acasirsub4` and its bridge `irspostingMT` - the `IRSPOSTING-REC` posting table.

The data-access module for the IRS posting entity, and the clearest single
argument for the bridge being the authoritative record-layout-to-table mapping.

THREE COLUMNS EXIST HERE THAT APPEAR IN NO COPYBOOK. `POST4-DAY`, `POST4-MONTH`
and `POST4-YEAR` are derived by the bridge from the posting date's text under a
guard [common/irspostingMT.cbl:L982-L987]. A migration driven from the copybooks
alone would silently omit three columns of a posting table, so the derivation is
reproduced here - INCLUDING ITS FAILURE MODE: when the guard fails the three
components stay zero while the raw date text is still stored, producing a row that
is internally inconsistent. That row is written as the frozen bridge writes it.

So the column list here is DERIVED FROM THE GENERATED DATA DICTIONARY rather than
transcribed from a record layout, and validated at import against the frozen
table declaration. Anomaly ``A-7`` in the plan's register is this module's
headline, and a dedicated parity test locks it in place.

THE THREE RECORD VIEWS, AND WHICH ONE NAMES THE COLUMNS
=======================================================

Three different COBOL declarations describe the same row, and they disagree.

=========================  =========================  =========================
Linkage view               FD view                    Bridge host variable
[copybooks/irswspost.cob]  [common/acasirsub4.cbl]    [common/irspostingMT.cbl]
=========================  =========================  =========================
``Post-Key``     pic 9(5)  ``Key-4`` group      L102  ``HV-KEY-4``    9(08) L174
``Post-Code``    pic xx    ``Post4-Code``       L104  ``X(2)``              L175
``Post-Date``    pic x(8)  ``Post4-Date``       L105  ``X(8)``              L176
-- absent --               -- absent --               ``HV-POST4-DAY``      L177
-- absent --               -- absent --               ``HV-POST4-MONTH``    L178
-- absent --               -- absent --               ``HV-POST4-YEAR``     L179
``Post-DR``      pic 9(5)  ``Post4-DR``         L106  ``9(08) COMP``        L180
``Post-CR``      pic 9(5)  ``Post4-CR``         L107  ``9(08) COMP``        L181
``Post-Amount``  signed    ``Post4-Amount``     L108  ``S9(07)V9(02)``      L182
``Post-Legend``  pic x(32) ``Post4-Legend``     L109  ``X(32)``             L183
``Vat-AC-Def``   pic 99    ``Vat-AC-Def4``      L110  ``9(03) COMP``        L184
``Post-Vat-Side`` pic xx   ``Post4-Vat-Side``   L111  ``X(2)``              L185
``Vat-Amount``   signed    ``Vat-Amount4``      L112  ``9(07)V9(02)``       L186
=========================  =========================  =========================

THE COLUMN NAMES COME FROM THE FD VIEW, NOT THE LINKAGE VIEW (anomaly A27). The
inline ``01 Record-4`` at [common/acasirsub4.cbl:L101-L112] supplies ``KEY-4``,
``POST4-CODE``, ``POST4-DR``, ``VAT-AC-DEF4`` and ``VAT-AMOUNT4`` verbatim; the
linkage names (``Post-Key``, ``Post-Code``, ``Post-DR``, ``Vat-AC-Def``,
``Vat-Amount``) match no column at all. Only ``POST4-DAT`` is a genuine
bridge-side rename, "DATE" truncated to dodge the reserved word. The same holds
for ``IRSNL-REC``, whose names come from ``copybooks/irsfdwsnl.cob`` - so across
both IRS record tables the schema follows the FD view. Anyone resolving field
metadata from the linkage copybook gets most of thirteen names wrong, which is
why every lookup below goes through ``dictionary.loader`` (rule R-5, and the plan
section 0.8.1 directive "Data dictionary first ... This ordering is a directive,
not a preference").

``Key-Number`` [common/acasirsub4.cbl:L103], the elementary item inside the
``Key-4`` group, has NO column and NO host variable - the column is named after
its parent group. Recorded as a deliberate omission (anomaly A28).

THE THREE DERIVED COLUMNS
=========================

``bb000-HV-Load`` [common/irspostingMT.cbl:L958] ends with three INDEPENDENT
guarded moves [common/irspostingMT.cbl:L982-L987]::

    if       Post-Date (1:2) numeric
             move     Post-Date (1:2) to HV-POST4-DAY.
    if       Post-Date (4:2) numeric
             move     Post-Date (4:2) to HV-POST4-MONTH.
    if       Post-Date (7:2) numeric
             move     Post-Date (7:2) to HV-POST4-YEAR.

THREE GUARDS, NOT ONE (anomaly A2). The plan's register describes a single rule,
but the source tests each component separately, so derivation is PARTIAL: a date
of ``"01/AB/23"`` yields day 1, month 0, year 23 while ``POST4-DAT`` still holds
the raw text. Eight outcomes are reachable, not two. Verified against the
compiled oracle, which returned day ``1`` and month ``0`` for exactly that input.

``initialize TD-IRSPOSTING-REC`` [common/irspostingMT.cbl:L966] is the
load-bearing statement, not the moves: a failed guard leaves its host variable at
the initialised value, ZERO - never SQL null. That single line is why all
thirteen columns can be declared not-null with no default, and it is the general
mechanism behind plan section 0.6.2's "the Python layer must default rather than
omit". Every statement below binds all thirteen columns and never omits one.

The maintainer expected these guards never to fire
[common/irspostingMT.cbl:L978-L980] - "and yes they all should be numeric as a
date is present / but JIC (just in case)." So a firing guard produces a row in a
state its author did not anticipate: internally inconsistent, and reproduced as
such rather than repaired (rule R-4, "A defect reproduced is correct; a defect
fixed is a failure").

Separator positions 3 and 6 are NEVER examined (anomaly A4), so ``"01X02X23"``
derives cleanly, and only a two-digit year is ever stored. The components are
sliced, never parsed - a general-purpose date routine "would be more correct than
the specification, which is the one outcome to avoid" (plan section 0.8.6).

LOAD ORDER IS NOT COLUMN ORDER (anomaly A5). The three derived columns sit at
ordinals 4, 5 and 6 [mysql/ACASDB.sql:L278-L280] but are loaded LAST, after all
ten copybook fields, because they were bolted on - "These added after new columns
created 31/12/16" [common/irspostingMT.cbl:L978]. Both orders are reproduced
where each belongs: load order in :func:`_load_host_variables`, column order in
every statement.

THEY ARE WRITE-ONLY (anomaly A3). ``bb100-UnloadHVs``
[common/irspostingMT.cbl:L995] performs TEN moves for THIRTEEN columns
[common/irspostingMT.cbl:L1006-L1015] - it cannot do otherwise, since no
copybook field exists to receive them. The maintainer states the purpose
[common/irspostingMT.cbl:L1017-L1018]: "We do not need to unload POST4- DAY,
MONTH or YEAR as only used in select statements instead of a sort." This is the
only entry in the folder's write-only-host-variable inventory carrying a
documented rationale.

CORRECTIONS ESTABLISHED AGAINST THE FROZEN SOURCE
=================================================

Five claims inherited from the working notes were checked against the source and
found wrong. Rule R-6 makes observed behaviour the tie-breaker, so the source
wins and the corrections are recorded here rather than propagated:

* The flat-file write DOES load its FD record - [common/acasirsub4.cbl:L405] is
  ``move Posting-Record to Record-4.``, identical to the rewrite at
  [common/acasirsub4.cbl:L430]. There is no write/rewrite asymmetry and no stale
  record. (Corrects the claimed anomaly A7, which is withdrawn.)
* The duplicate-key retry [common/acasirsub4.cbl:L409-L411] is therefore NOT a
  guaranteed non-terminating loop: because ``Record-4`` is reloaded at the top of
  the paragraph on every pass and ``add 1 to Post-Key`` mutates the CALLER's
  linkage record, the retry advances and stops at the first free key. The real
  defect is the silent unbounded mutation of the caller's key, which wraps at
  99999. (Refines anomaly A6.)
* ``Post-Key`` IS moved into ``Key-Number`` before the flat start -
  [common/acasirsub4.cbl:L358-L359] is one ``move`` with two targets.
  (Corrects the claimed anomaly A22, which is withdrawn.)
* The access-type guard IS LIVE on this path. The bridge repeats it at
  [common/irspostingMT.cbl:L599-L601] with a different status pair, so it is
  implemented here - see :data:`BRIDGE_START_PARAM_ERROR`. (Corrects anomaly A21,
  which claimed the guard was reachable only from the flat path.)
* Delete-all is BOUNDED, not a whole-table wipe. ``ba085-Process-Delete-ALL``
  increments the key [common/irspostingMT.cbl:L812] and builds a ``WHERE``
  predicate [common/irspostingMT.cbl:L818-L828] before issuing its statement
  [common/irspostingMT.cbl:L845-L848]. (Corrects anomaly A18.)

The guard line numbers are ``L982-L987``, matching both the plan's own citation
and the generated dictionary; the working notes were consistently one line high.

THE MEASURED SIGN LOSS
======================

``POST4-AMOUNT`` and ``VAT-AMOUNT4`` are signed at all three declarations -
``sign is leading`` [copybooks/irswspost.cob:L14], ``S9(07)V9(02) COMP``
[common/irspostingMT.cbl:L182], and a column with no unsigned qualifier
[mysql/ACASDB.sql:L283]. The sign nevertheless DOES NOT REACH THE DATABASE, and
this was measured rather than assumed.

The bridge renders every value through one edit field, ``WS-MYSQL-EDIT PIC
-Z(18)9.9(9)``, and extracts a fixed window from it
[common/irspostingMT.cbl:L1101-L1105]. That field is thirty characters wide and
its ``-`` is a FIXED insertion character at position 1, because a floating sign
needs at least two occurrences. The money window begins at position 14, so the
sign is outside every window the bridge reads. Compiled measurement:

    ``-12345.67`` -> ``[-              12345.670000000]`` -> window ``12345.67``
    ``+12345.67`` -> window ``12345.67``          <- IDENTICAL

Plan section 0.6.2 requires "the Python data-access layer must reproduce the
bridge's conversion, not merely write the computed value and let MySQL
complain", so :func:`_mysql_edit` reproduces the edit field and the windowing,
and the sign is lost exactly where the bridge loses it. That it is lost HERE and
not at the column is confirmed by measurement, not assumed: the column is
``decimal(9,2)`` with no ``unsigned`` [mysql/ACASDB.sql:L279] and keeps a negative
value when one is sent. See ambiguity Q-B below.

WHAT THIS MODULE DELIBERATELY DOES NOT DO
=========================================

Recorded as omissions per plan section 0.5.3, "Deliberate omissions are recorded
as omissions":

* THE WHOLE FLAT-FILE PATH. Dispatch reaches the database branch at
  [common/acasirsub4.cbl:L196-L200] and never returns, so ``aa020`` through
  ``aa100`` are specification only. With it go: the duplicate-key retry (A6), the
  flat start's reliance on ``Key-Number`` (A22), and the live ``stop "Cobol File
  EOF"`` in a block whose own comment says it "should NOT occur"
  [common/acasirsub4.cbl:L301-L308] (A23) - never translated to a
  process-terminating call.
* DUAL-WRITE SEMANTICS (A32). The banner at [common/acasirsub4.cbl:L208-L212]
  documents writing to both stores when both are configured, a flat read being
  "overwritten by rdb processing if set". Only the database path is in scope.
* ``Key-Number`` (A28), which has neither column nor host variable.
* ALL PRESENTATION. The record-size failure's ``display``/``accept`` dialogue
  [common/acasirsub4.cbl:L484-L499] keeps its control transfer and loses its
  screen I/O; the bridge's terminal-height probe
  [common/irspostingMT.scb:L207-L211] is dropped entirely.
* THE FH LOGGING CALL at [common/acasirsub4.cbl:L544-L548]. That program is out
  of scope per plan section 0.2.2, so ``Ca-Process-Logs`` becomes a Python log
  record (rule R-1).

REPRESENTATION-ONLY ODDITIES, CARRIED AS EVIDENCE
=================================================

These change no behaviour, so there is nothing to reproduce - but each is a fact
about the frozen source that a later reader would otherwise have to rediscover,
and rule R-4 wants them recorded rather than silently dropped.

* A25 - A REREAD PARAGRAPH INSIDE A BRIDGE. ``ba041-Reread``
  [common/irspostingMT.cbl:L420] is the only such paragraph in any of the twenty
  in-scope bridges; the others fetch inline. It exists because this bridge's START
  ends by jumping to it [common/irspostingMT.cbl:L702], which is the same
  start-then-read shape the handler has, pushed down a layer. It is why
  :func:`start` ends with a call to :func:`read_next` rather than returning a
  position.
* A29 - TWO SPELLINGS OF ``initialize`` FOR THE SAME RECORD, in one bridge. The
  read path uses ``initialize Posting-Record with filler``
  [common/irspostingMT.cbl:L472] while the unload uses the plain form
  [common/irspostingMT.cbl:L1004]. Only the plain form is on the path this module
  takes, so :func:`_unload_host_variables` reproduces that one; the ``with
  filler`` variant sits on the errno branch of the fetch. The unload is also
  preceded by a stale ``*> (init moved lower)``
  [common/irspostingMT.cbl:L999] whose ``initialize`` is in fact five lines BELOW
  it, not lower still - the same stale note ``irsnominalMT`` carries.
* A30 - A REPEATING-GROUP NOTE IN A BRIDGE WITH NO REPEATING GROUP. "RGs are
  handled separately for all such actions so they must not be loaded here"
  [common/irspostingMT.cbl:L989-L990] follows the load paragraph, but
  ``IRSPOSTING-REC`` has no repeating group and no ``occurs`` anywhere - the same
  copy-paste ``purchMT`` and ``irsnominalMT`` carry. And the linkage copybook's
  own change note opens with a DOUBLED comment marker, ``*>> Chg 16/01/09 money to
  9M`` [copybooks/irswspost.cob:L6], where every sibling line uses ``*>``.

HOW THIS MODULE IS REACHED
==========================

Through the IRS facade convention [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L69],
which sets ``File-Key-No`` to 1 and calls with the linkage order preserved here.
That convention wraps most handlers in a per-handler error check - but there is
NONE for ``acasirsub4``; checks exist only for ``acas000``, ``acas008``,
``irsub1``, ``irsub3`` and ``irsub5`` at [:L320], [:L327], [:L334], [:L341] and
[:L348]. Consistently, the handler declares a ``*> Module Specific`` heading and
then no module-specific message at all [common/acasirsub4.cbl:L129-L131] (A26).
SO :func:`dispatch` PERFORMS NO RECOVERY: it returns the status pair and leaves
recovery to the caller, exactly as [common/acasirsub4.cbl:L538] directs - "Any
errors leave it to caller to recover from". This matters because ``irs030``
abandons its run on a posting-write failure [irs/irs030.cbl:L1673-L1678] while
still committing partial state, so the pair returned here decides which rows
survive.

The verb surface narrows at each layer: the facade publishes SIX verbs
[copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L256-L281], the handler dispatches
EIGHT function codes [common/acasirsub4.cbl:L218-L235], and the bridge dispatches
NINE [common/irspostingMT.cbl:L257-L281] - the extra being code 6, delete-all,
reachable only by the coercion in ``ba015-Test-Ends``.

AMBIGUITIES, RESOLVED BY MEASUREMENT  (rule R-6, plan section 0.6.8)
====================================================================
Three conversions could not be asserted from the source alone. All three are now
measured against **MariaDB 10.11.7** - the server version the frozen schema
records as its producer [mysql/ACASDB.sql:L1, :L5] - with the frozen
``ENGINE=InnoDB`` and the server's default ``sql_mode``
(``STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION``),
which is what the bridge's C interface gets. The dump's own
``SQL_MODE='NO_AUTO_VALUE_ON_ZERO'`` [mysql/ACASDB.sql:L21] does not change that:
it is SESSION-scoped, leaves ``@@global.sql_mode`` untouched (measured) and is
restored at [:L1451], so it governs only the schema load - and is inert even there,
the schema's only ``AUTO_INCREMENT`` column belonging to the out-of-scope
``STOCKAUDIT-REC`` [mysql/ACASDB.sql:L1107]. None of the three results changes a
line of code, and that is what measuring rather than guessing was for.

    Q-A  THE WIDTH INFLATIONS. ``9(5)`` sources travel through ``9(08)`` host
         variables into ``mediumint(5) unsigned`` columns, and two-character
         substrings through ``9(03)`` into ``tinyint(2) unsigned``. THE PREMISE
         THAT THE HOST VARIABLE IS WIDER THAN THE COLUMN IS WRONG: ``(5)`` and
         ``(2)`` ARE DISPLAY WIDTHS, NOT CONSTRAINTS. Measured, ``mediumint
         unsigned`` holds 0..16777215 - so ``POST4-DR`` accepted both ``99999``
         and ``16777215``, i.e. all five source digits and three more - and
         ``tinyint unsigned`` holds 0..255. Past those the server REFUSES rather
         than clamps: ``16777216`` into ``POST4-DR`` and into ``KEY-4``, and
         ``256`` into ``POST4-DAY``, each raise ERROR 1264, SQLSTATE 22003, "Out
         of range value", and the row is NOT written. So the inflation is harmless
         over the whole source domain, and beyond it the refusal is the server's -
         which is where the frozen bridge meets it too, so no check is added here
         (rule R-3).

    Q-B  THE MONEY PATH AT THE COLUMN'S PRECISION LIMIT. ``POST4-AMOUNT`` and
         ``VAT-AMOUNT4`` are ``decimal(9,2)`` with **no** ``unsigned``
         [mysql/ACASDB.sql:L279, :L282], so the column itself would keep a sign;
         measured, ``-12345.67`` stores as ``-12345.67``. The sign is therefore
         lost STRICTLY EARLIER, at the edit window described above, and that is a
         COBOL fact this module already reproduces rather than a column effect.
         At the precision limit: ``9999999.99`` (seven integer digits, the most
         ``decimal(9,2)`` holds) stores exactly, and ``10000000.00`` raises ERROR
         1264 / 22003 with nothing written. Note the contrast, also measured -
         SCALE overflow ROUNDS instead of failing: ``1.005`` stores ``1.01`` and
         ``1.004`` stores ``1.00``. Precision and scale have different
         dispositions, and only precision can abort a statement.

    Q-C  THE KEY PREDICATE, ANOMALY A15. The key metadata declares ``"STR"``
         [common/irspostingMT.scb:L126] for a ``mediumint(5) unsigned`` key
         [mysql/ACASDB.sql:L275], so the bridge quotes the value and the
         comparison works only by server coercion. IT COERCES TO A NUMBER, proved
         with a probe whose two readings disagree: against a numeric column
         holding 9 and 10, ``k > "10"`` returned NO rows and ``k < "10"`` returned
         9 - the opposite of the lexical answer - and ``9 > "10"`` evaluates 0
         while ``"9" > "10"`` evaluates 1. Measured on this shape:
         ``KEY-4 = "1"`` returned 1, ``KEY-4 > "1"`` returned 2, and
         ``KEY-4 > "000"`` returned both. The same holds for ``IRSNL-REC``, whose
         ``bigint(10) unsigned`` key matched a zero-filled ten-character image.
         So the quoted literal is reproduced exactly as the bridge emits it, and
         binding an integer "because the column is numeric" would be a different
         statement for no gain.
"""

from __future__ import annotations

import decimal
import logging
from contextlib import contextmanager
from types import MappingProxyType
from typing import Any, Final, Iterator, Mapping

from acas_posting.dal.connection import (
    acquire_cursor,
    execute_statement,
    mysql_1000_open,
    mysql_1090_exit,
    mysql_1980_close,
    mysql_1999_exit,
    quote_identifier,
    rdb_data_from_system_record,
)
from acas_posting.dal.cursor_state import (
    CursorOutcome,
    CursorSlot,
    key_of_reference,
)
from acas_posting.dal.cursor_state import read_indexed as _cursor_read_indexed
from acas_posting.dal.cursor_state import read_next as _cursor_read_next
from acas_posting.dal.cursor_state import reset as _cursor_reset
from acas_posting.dal.cursor_state import start as _cursor_start
from acas_posting.dal.status import (
    AccessType,
    FileFunction,
    FsReply,
    LogSystem,
    WeError,
    log_handler_failure,
    mysql_1100_db_error,
    override_we_error_for_operation,
)
from acas_posting.dictionary import loader
from acas_posting.records.file_access import FileAccess
from acas_posting.records.file_defs import FileDefs
from acas_posting.records.irs_posting import PostingRecord
from acas_posting.records.system_record import SystemRecord
from acas_posting.records.test_data_flags import AcasDalCommonData

__all__ = (
    "COLUMNS",
    "DERIVED_COLUMNS",
    "KEY_LENGTH",
    "KEY_METADATA_TYPE",
    "KEY_OFFSET",
    "PRIMARY_KEY",
    "TABLE",
    "close",
    "delete",
    "delete_all",
    "dispatch",
    "open_",
    "open_extend",
    "open_input",
    "open_output",
    "read_indexed",
    "read_next",
    "rewrite",
    "start",
    "write",
)

_LOG = logging.getLogger(__name__)


TABLE: Final[str] = "IRSPOSTING-REC"
"""The table this handler owns [mysql/ACASDB.sql:L274]."""

PRIMARY_KEY: Final[str] = "KEY-4"
"""The single-column primary key [mysql/ACASDB.sql:L288]."""

KEY_OFFSET: Final[int] = 1
KEY_LENGTH: Final[int] = 5
"""The key's one-based offset and length within the record buffer."""

KEY_METADATA_TYPE: Final[str] = "STR"
"""``*> key is string`` [common/irspostingMT.scb:L126].

ANOMALY A15: the key metadata declares a string type for ``KEY-4``, which is
``mediumint(5) unsigned`` [mysql/ACASDB.sql:L275] - a number. The predicate the
bridge builds wraps the value in double quotes regardless, so it compares a
quoted string to a numeric column and works only because the server coerces.
Both IRS record tables share the contradiction. Reproduced, not corrected; the
coercion is NUMERIC, measured on MariaDB 10.11.7 - see ambiguity Q-C in the module
docstring - so the quoted literal returns the same rows an integer bind would.
"""

KEY_COUNT: Final[int] = 1
"""``keyOfReference occurs 1`` [common/irspostingMT.scb:L129]."""


_FROZEN_COLUMNS: Final[tuple[str, ...]] = (
    "KEY-4",
    "POST4-CODE",
    "POST4-DAT",
    "POST4-DAY",
    "POST4-MONTH",
    "POST4-YEAR",
    "POST4-DR",
    "POST4-CR",
    "POST4-AMOUNT",
    "POST4-LEGEND",
    "VAT-AC-DEF4",
    "POST4-VAT-SIDE",
    "VAT-AMOUNT4",
)
"""The thirteen columns in schema order, read directly from the frozen table.

Held ONLY to validate the generated dictionary against the frozen source at import.
:data:`COLUMNS` - the list every statement is built from - is derived from the
dictionary, because plan section 0.8.1 makes that ordering a directive.
"""


def _dictionary_entries() -> tuple[Any, ...]:
    """Return this table's dictionary entries in column-ordinal order.

    ``entries_for_table`` orders by ordinal, so the three bridge-only columns arrive
    interleaved at positions 4, 5 and 6 - the schema's own order - rather than appended.

    Raises:
        RuntimeError: If the dictionary disagrees with the frozen table declaration, in
            either the set of columns or their order.
    """
    entries = loader.entries_for_table(TABLE)
    derived_order = tuple(entry.column.name for entry in entries)
    if derived_order != _FROZEN_COLUMNS:
        raise RuntimeError(
            "the generated data dictionary no longer matches the frozen table "
            f"declaration for {TABLE} [mysql/ACASDB.sql:L274-L287]; dictionary "
            f"reports {derived_order!r}. Regenerate the dictionary rather than "
            "editing this module - the frozen schema is authoritative."
        )
    return entries


_ENTRIES: Final[tuple[Any, ...]] = _dictionary_entries()

_ENTRY_BY_COLUMN: Final[Mapping[str, Any]] = MappingProxyType(
    {entry.column.name: entry for entry in _ENTRIES}
)

COLUMNS: Final[tuple[str, ...]] = tuple(
    entry.column.name for entry in _ENTRIES
)
"""The thirteen columns, in schema order, derived from the data dictionary.

Every statement in this module names all thirteen and binds all thirteen.
"""


DERIVED_COLUMNS: Final[tuple[str, ...]] = (
    "POST4-DAY",
    "POST4-MONTH",
    "POST4-YEAR",
)
"""The columns with no copybook counterpart [common/irspostingMT.cbl:L177-L179].

ANOMALY A1, the plan's register entry ``A-7``, and the reason this module is the plan's
proof that the bridge is authoritative.
"""

DERIVED_COLUMN_SLICES: Final[Mapping[str, tuple[int, int]]] = MappingProxyType(
    {
        "POST4-DAY": (1, 2),
        "POST4-MONTH": (4, 2),
        "POST4-YEAR": (7, 2),
    }
)
"""The reference-modification offsets, one-based, exactly as the source writes.

The implied layout is ``DD/MM/YY`` with separators at positions 3 and 6, and THOSE TWO
POSITIONS ARE NEVER EXAMINED (anomaly A4) - so ``"01X02X23"`` derives day 1, month 2,
year 23 without complaint.
"""

POST_DATE_LENGTH: Final[int] = 8
"""``Post-Date pic x(8)`` [copybooks/irswspost.cob:L11], space-padded."""


WS_LOG_SYSTEM: Final[int] = int(LogSystem.IRS)
"""``move 1 to WS-Log-System`` [common/acasirsub4.cbl:L160], 1 being IRS."""

WS_LOG_FILE_NO_FLAT: Final[int] = 13
"""``move 13 to WS-Log-File-No`` [common/acasirsub4.cbl:L161]."""

WS_LOG_FILE_NO_RDB: Final[int] = 23
"""``move 23 to WS-Log-File-no`` [common/acasirsub4.cbl:L469].

The database path bumps the file number and the flat path does not, because the bump
lives in ``ba010-Test-WS-Rec-Size`` which only the database branch reaches. So 23 is the
effective number here.
"""


HANDLER_TRACE: Final[Mapping[int, int]] = MappingProxyType(
    {
        int(FileFunction.OPEN): 201,
        int(FileFunction.CLOSE): 202,
        int(FileFunction.READ_NEXT): 203,
        int(FileFunction.READ_INDEXED): 204,
        int(FileFunction.START): 205,
        int(FileFunction.WRITE): 206,
        int(FileFunction.DELETE): 207,
        int(FileFunction.RE_WRITE): 208,
    }
)
"""The handler's own trace numbers, 201 through 208."""

BRIDGE_TRACE: Final[Mapping[int, int]] = MappingProxyType(
    {
        int(FileFunction.OPEN): 1,
        int(FileFunction.CLOSE): 2,
        int(FileFunction.READ_NEXT): 3,
        int(FileFunction.READ_INDEXED): 5,
        int(FileFunction.START): 8,
        int(FileFunction.WRITE): 10,
        int(FileFunction.DELETE): 13,
        int(FileFunction.DELETE_ALL): 15,
        int(FileFunction.RE_WRITE): 17,
    }
)
"""The bridge's trace numbers, an entirely different scale from the handler's.

Both are written into the same ``ws-No-Paragraph`` field [copybooks/wsfnctn.cob:L48] as
control passes down, so the value observed at any moment depends on which layer last
ran.
"""


END_OF_FILE: Final[tuple[int, int]] = (int(FsReply.END_OF_FILE), 3)
"""``(10, 3)`` - end of file for THIS bridge.

THIS DIFFERS FROM THE SHARED HELPER. ``status.end_of_file_status()`` returns ``(10,
10)``, which is correct for ``glpostingMT`` - the bridge that module was derived from -
and wrong here.
"""

NOT_FOUND: Final[tuple[int, int]] = (int(FsReply.INVALID_KEY_ON_START), 2)
"""``(21, 2)`` - key not found, for both the indexed read and the start.

Note 21, never 23, even though ``FsReply`` carries a distinct ``KEY_NOT_FOUND`` of 23.
And note that ``glpostingMT`` leaves ``We-Error`` UNTOUCHED on this condition where this
bridge writes 2 - a second reason the remap is needed.
"""

WE_ERROR_EOF_ONLY_IN_COMMENT: Final[int] = 989
"""ANOMALY A13: a code that exists only as a commented-out line.

[common/irspostingMT.cbl:L577] carries ``*> move 989 to WE-Error`` and 989 appears
nowhere else in the whole handler-and-bridge folder. Named here so the register entry
has a home; NEVER emitted, which is the point.
"""

HANDLER_BAD_FUNCTION: Final[int] = int(WeError.NOT_USED)
"""``999`` - the handler's bad-function code [common/acasirsub4.cbl:L439-L440]."""

BRIDGE_BAD_FUNCTION: Final[int] = int(WeError.UNKNOWN_UNEXPECTED)
"""``990`` - the bridge's bad-function code [common/irspostingMT.cbl:L924].

ANOMALY A17, first half: the two layers disagree on the SAME condition. Both set ``FS-
Reply`` to 99 and both carry the comment ``*> Houston; We have a problem``, but the
handler reports 999 and the bridge 990.
"""

HANDLER_START_PARAM_ERROR: Final[int] = int(WeError.FILE_KEY_NO_OUT_OF_RANGE)
"""``998`` - the handler's access-type rejection [common/acasirsub4.cbl:L362].

ANOMALY A17, second half. The handler sets 998 and, unlike every other error path,
LEAVES ``FS-Reply`` AT ZERO - there is no ``move 99 to fs-reply`` in that block
[common/acasirsub4.cbl:L361-L364].
"""

BRIDGE_START_PARAM_ERROR: Final[int] = int(WeError.ACCESS_TYPE_WRONG)
"""``997`` - the bridge's access-type rejection [common/irspostingMT.cbl:L601].

THIS ONE IS LIVE, and correcting the note that said otherwise is one of the five
corrections in the module docstring.
"""

FILE_KEY_NO_START_ERROR: Final[int] = int(WeError.FILE_KEY_NO_OUT_OF_RANGE)
"""``998`` - key-number guard for the indexed read and the start.

[common/acasirsub4.cbl:L166-L172]: ``fn-read-indexed`` and ``fn-start`` both require
``File-Key-No`` of 1, and anything else yields ``(99, 998)``. The guard is shared
verbatim with ``acasirsub1`` and ``acas022``, comment included - "1 is only for RDB as
Cobol does it on primary key".
"""

FILE_KEY_NO_DELETE_ERROR: Final[int] = int(WeError.DELETE_KEY_OUT_OF_RANGE)
"""``996`` - the same guard for ``fn-delete`` [common/acasirsub4.cbl:L174-L178].

A DIFFERENT CODE FOR AN IDENTICAL CONDITION, which is why it is a separate constant
rather than a shared one.
"""

RECORD_SIZE_MISMATCH: Final[int] = int(WeError.RECORD_SIZE_MISMATCH)
"""``901`` - the record-size gate's failure [common/acasirsub4.cbl:L481-L482]."""


_CONNECTION: Any = None
"""The open connection, held across calls.

FAITHFUL RATHER THAN CONVENIENT. A COBOL sub-program's ``WORKING-STORAGE`` survives
between ``CALL``s unless the program is cancelled, and the bridge holds its connection
exactly this way.
"""

_RECORD_SIZE_CHECKED: bool = False
"""The ``if A = zero`` latch [common/acasirsub4.cbl:L473].

``A`` and ``B`` are declared with the comment "A & B used in 1st test ONLY / in ba-
Process-RDBMS" [common/acasirsub4.cbl:L121-L122], so the size comparison runs once per
program activation and never again.
"""


_EDIT_WIDTH: Final[int] = 30
"""``WS-MYSQL-EDIT PIC -Z(18)9.9(9)`` is thirty characters wide."""

_EDIT_INTEGER_DIGITS: Final[int] = 19
"""Positions 2 through 20 - the ``Z(18)`` run plus the mandatory ``9``.

The trailing position is ``9`` and not ``Z``, so a value of zero renders ``"0"`` rather
than blank. Measured: a zero key renders ``[0]``, not ``[]``.
"""

_EDIT_FRACTION_DIGITS: Final[int] = 9
"""Positions 22 through 30 - the ``9(9)`` run, never suppressed."""

_EDIT_POINT_POSITION: Final[int] = 21
"""The literal ``.`` separating the two runs."""

_MONEY_WINDOW: Final[tuple[int, int]] = (14, 7)
"""``WS-MYSQL-EDIT(14:07)`` [common/irspostingMT.cbl:L1101]."""

_MONEY_FRACTION_WINDOW: Final[tuple[int, int]] = (22, 2)
"""``WS-MYSQL-EDIT(22:02)`` [common/irspostingMT.cbl:L1105].

Taken RAW, not trimmed - the bridge trims the integer window and then appends the
literal ``"."`` and these two characters untouched, so a value of zero yields ``"0.00"``
rather than ``"0."``.
"""

_WIDE_INTEGER_WINDOW: Final[tuple[int, int]] = (13, 8)
"""``WS-MYSQL-EDIT(13:08)`` [common/irspostingMT.cbl:L1041].

Eight positions for the ``9(08) COMP`` host variables - ``HV-KEY-4``, ``HV-POST4-DR``
and ``HV-POST4-CR``. ANOMALY A16: their copybook sources are ``pic 9(5)`` and their
columns ``mediumint(5)``, so the width inflates 5 -> 8 -> 5. No clamping is applied.
"""

_NARROW_INTEGER_WINDOW: Final[tuple[int, int]] = (18, 3)
"""``WS-MYSQL-EDIT(18:03)`` [common/irspostingMT.cbl:L1071].

Three positions for the ``9(03) COMP`` host variables - the three derived components and
``HV-VAT-AC-DEF4``. ANOMALY A16 again: fed from two-character substrings, or from ``pic
99``, into ``tinyint(2)`` columns, so 2 -> 3 -> 2.
"""

_EDIT_CONTEXT: Final[decimal.Context] = decimal.Context(
    prec=_EDIT_INTEGER_DIGITS + _EDIT_FRACTION_DIGITS + 2,
    rounding=decimal.ROUND_DOWN,
)
"""An exact-decimal context wide enough for the whole edit field.

Precision covers every digit position the field can hold, so no rendering can lose a
digit to the context.
"""


def _mysql_edit(value: decimal.Decimal) -> str:
    """Render one value into the bridge's thirty-character edit field.

    Reproduces ``MOVE HV-xxx TO WS-MYSQL-EDIT`` for the picture ``-Z(18)9.9(9)``
    [common/irspostingMT.cbl:L1039-L1040]. The layout, one-based.

    Args:
        value: The host variable's value. Exact decimal throughout; no binary
            approximation is used at any point (rule R-2).

    Returns:
        The thirty-character field, ready for windowing.
    """
    with decimal.localcontext(_EDIT_CONTEXT):
        negative = value < 0
        magnitude = -value if negative else value
        shifted = magnitude.scaleb(_EDIT_FRACTION_DIGITS).to_integral_value(
            rounding=decimal.ROUND_DOWN
        )
        all_digits = format(shifted, "f").rjust(
            _EDIT_INTEGER_DIGITS + _EDIT_FRACTION_DIGITS, "0"
        )

    integer_digits = all_digits[:-_EDIT_FRACTION_DIGITS]
    fraction_digits = all_digits[-_EDIT_FRACTION_DIGITS:]

    # `Z(18)` suppresses leading zeros to spaces; the final `9` at position 20 does not,
    # which is why a zero value still renders a digit there.
    suppressible = integer_digits[:-1]
    mandatory = integer_digits[-1]
    stripped = suppressible.lstrip("0")
    suppressed = stripped.rjust(len(suppressible), " ")

    sign_character = "-" if negative else " "
    return (
        sign_character
        + suppressed
        + mandatory
        + "."
        + fraction_digits
    )


def _window(edit: str, window: tuple[int, int]) -> str:
    """Take a one-based reference-modified slice of the edit field.

    Reproduces ``WS-MYSQL-EDIT(offset:length)``. COBOL offsets are one-based, so the
    offset is decremented once here rather than at each of the five call sites.
    """
    offset, length = window
    return edit[offset - 1 : offset - 1 + length]


def _integer_window(integer_digits: int) -> tuple[int, int]:
    """Derive the edit-field window for a host variable's integer width.

    The integer run is right-aligned and ends at position 20, so ``n`` integer digits
    occupy positions ``21 - n`` through 20.
    """
    return (_EDIT_POINT_POSITION - integer_digits, integer_digits)


def _verify_edit_geometry() -> None:
    """Check the derived geometry against the field's frozen literals.

    Guards the one piece of arithmetic in this module that is not itself quoted from the
    source. A mismatch means either the picture clause or a windowing literal has been
    misread, and both would corrupt every value written.

    Raises:
        RuntimeError: If the rendered field is the wrong width, if the decimal point
            lands in the wrong place, or if a derived window disagrees with the literal
            the bridge writes.
    """
    rendered = _mysql_edit(decimal.Decimal(0))
    if len(rendered) != _EDIT_WIDTH:
        raise RuntimeError(
            f"WS-MYSQL-EDIT rendered {len(rendered)} characters, expected "
            f"{_EDIT_WIDTH} for PIC -Z(18)9.9(9) "
            "[common/irspostingMT.cbl:L1039-L1040]"
        )
    if rendered.index(".") + 1 != _EDIT_POINT_POSITION:
        raise RuntimeError(
            "WS-MYSQL-EDIT decimal point is not at position "
            f"{_EDIT_POINT_POSITION}"
        )
    for digits, literal in (
        (8, _WIDE_INTEGER_WINDOW),
        (7, _MONEY_WINDOW),
        (3, _NARROW_INTEGER_WINDOW),
    ):
        if _integer_window(digits) != literal:
            raise RuntimeError(
                f"derived window for {digits} integer digits is "
                f"{_integer_window(digits)}, but the bridge writes {literal}"
            )


_verify_edit_geometry()


def _fixed_char(value: str, length: int) -> str:
    """Hold a value in a fixed-width ``PIC X(n)`` display item.

    A COBOL character field is always exactly its declared width: a shorter value is
    padded with trailing spaces and a longer one is truncated on the right.
    """
    if len(value) >= length:
        return value[:length]
    return value.ljust(length)


def _render_character(value: str, length: int) -> str:
    """Render a character host variable as the bridge does.

    ``FUNCTION TRIM (HV-xxx,TRAILING)`` [common/irspostingMT.cbl:L1052-L1053] - TRAILING
    ONLY, so leading spaces are PRESERVED and reach the column while trailing padding
    does not. Trimming both ends would silently left-justify every value that arrived
    with a leading space.
    """
    return _fixed_char(value, length).rstrip(" ")


def _is_cobol_numeric(text: str) -> bool:
    """Reproduce COBOL's ``numeric`` class test on a display item.

    Every character must be a digit. MEASURED AGAINST THE COMPILED PROGRAM, which is the
    only way to settle the edge cases rule R-6 cares about.
    """
    return bool(text) and all(character in "0123456789" for character in text)


def _derive_date_components(post_date: str) -> tuple[int, int, int]:
    """Derive ``POST4-DAY``, ``POST4-MONTH`` and ``POST4-YEAR`` from the date text.

    THREE INDEPENDENT GUARDS, NOT ONE (anomaly A2). Each component stands or falls on
    its own two characters, so derivation is partial.

    Args:
        post_date: ``Post-Date``, a ``pic x(8)`` display item
            [copybooks/irswspost.cob:L11].

    Returns:
        ``(day, month, year)`` as integers, each zero where its own guard failed. Never
            ``None``, and never a partial structure.
    """
    text = _fixed_char(post_date, POST_DATE_LENGTH)
    components: list[int] = []
    for column in DERIVED_COLUMNS:
        offset, length = DERIVED_COLUMN_SLICES[column]
        fragment = text[offset - 1 : offset - 1 + length]
        if _is_cobol_numeric(fragment):
            components.append(int(fragment))
            continue
        # The guard failed, so the `move` never runs and the host variable keeps the
        # zero that `initialize TD-IRSPOSTING-REC` left [common/irspostingMT.cbl:L966].
        # Reproduced, not repaired - rule R-4.
        components.append(0)
        #  THE DATE TEXT ITSELF IS NOT LOGGED. `POST4-DAT` carries a posting's
        #  own date - business data, which the safe-event schema forbids in a record
        #  (CWE-532) - and the guard's failure is fully identified by the table and
        #  the column it left at zero. The raw text is still STORED, because the
        #  frozen bridge stores it, so the row is exactly as inconsistent as it is in
        #  the compiled program (anomaly A-7, R-4).
        _LOG.debug(
            "%s: the guard on %s did not hold, so the column stays zero while "
            "POST4-DAT keeps the raw text - the maintainer expected this never "
            "to occur [common/irspostingMT.cbl:L978-L987]",
            TABLE,
            column,
        )
    day, month, year = components
    return day, month, year


_COPYBOOK_LOAD_ORDER: Final[tuple[tuple[str, str], ...]] = (
    ("KEY-4", "post_key"),
    ("POST4-CODE", "post_code"),
    ("POST4-DAT", "post_date"),
    ("POST4-DR", "post_dr"),
    ("POST4-CR", "post_cr"),
    ("POST4-AMOUNT", "post_amount"),
    ("POST4-LEGEND", "post_legend"),
    ("VAT-AC-DEF4", "vat_ac_def"),
    ("POST4-VAT-SIDE", "post_vat_side"),
    ("VAT-AMOUNT4", "vat_amount"),
)
"""The ten copybook moves, IN COPYBOOK ORDER, not column order.

ANOMALY A5. These run first, in exactly this sequence
[common/irspostingMT.cbl:L967-L976], and the three derived columns follow AFTER them
[common/irspostingMT.cbl:L982-L987] even though they occupy ordinals 4, 5 and 6 of the
row [mysql/ACASDB.sql:L278-L280].
"""


def _render_value(column: str, value: Any) -> str:
    """Render one host variable exactly as the bridge's statement builder does.

    Dispatches on the DICTIONARY's declared metadata rather than on the Python type, so
    the storage class comes from the authoritative triple and not from a guess about the
    value in hand (rule R-5). Character fields are trimmed trailing.
    """
    entry = _ENTRY_BY_COLUMN[column]
    host_variable = entry.bridge_host_variable

    if host_variable.character_length is not None:
        return _render_character(str(value), host_variable.character_length)

    amount = value if isinstance(value, decimal.Decimal) else decimal.Decimal(value)
    edit = _mysql_edit(amount)
    integer_digits = host_variable.integer_digits or host_variable.digits or 0

    if host_variable.scale:
        # `TRIM(edit(14:07))` then the literal "." then `edit(22:02)` RAW
        # [common/irspostingMT.cbl:L1101-L1105]. The fraction is not trimmed, so a whole
        # value renders "n.00" rather than "n.".
        return (
            _window(edit, _integer_window(integer_digits)).strip()
            + "."
            + _window(edit, _MONEY_FRACTION_WINDOW)
        )
    return _window(edit, _integer_window(integer_digits)).strip()


def _load_host_variables(posting: PostingRecord) -> Mapping[str, str]:
    """``bb000-HV-Load`` [common/irspostingMT.cbl:L958-L987].

    THE ORDER IS THE SOURCE'S ORDER: the group is initialised, then the ten copybook
    fields are moved in copybook order, then the three derived components are moved last
    (anomaly A5).

    Args:
        posting: The caller's ``Posting-Record``. Read only; the database path never
            mutates it, unlike the flat write's key retry [common/acasirsub4.cbl:L410]
            which is out of scope.

    Returns:
        Thirteen rendered values keyed by column name, ready to bind in schema order.
    """
    # `initialize TD-IRSPOSTING-REC.` - every host variable gets its group's initial
    # value BEFORE any move [common/irspostingMT.cbl:L966].
    loaded: dict[str, str] = {}
    for column in COLUMNS:
        host_variable = _ENTRY_BY_COLUMN[column].bridge_host_variable
        if host_variable.character_length is not None:
            loaded[column] = _render_character(
                "", host_variable.character_length
            )
        else:
            loaded[column] = _render_value(column, decimal.Decimal(0))

    for column, attribute in _COPYBOOK_LOAD_ORDER:
        loaded[column] = _render_value(column, getattr(posting, attribute))

    day, month, year = _derive_date_components(posting.post_date)
    loaded["POST4-DAY"] = _render_value("POST4-DAY", day)
    loaded["POST4-MONTH"] = _render_value("POST4-MONTH", month)
    loaded["POST4-YEAR"] = _render_value("POST4-YEAR", year)

    return MappingProxyType(loaded)


def _unload_host_variables(row: Mapping[str, Any]) -> PostingRecord:
    """``bb100-UnloadHVs`` [common/irspostingMT.cbl:L995-L1015].

    TEN MOVES FOR THIRTEEN COLUMNS - the asymmetry is anomaly A3 and it is deliberate.
    ``POST4-DAY``, ``POST4-MONTH`` and ``POST4-YEAR`` are read from the row and
    DISCARDED, because ``Posting-Record`` has no field able to receive them.

    Args:
        row: One fetched row keyed by column name. The driver's pinned converter already
            delivers exact decimals and integers, never binary approximations (rule
            R-2).

    Returns:
        The ten copybook fields as a record. The three derived columns are read and
            dropped.
    """
    posting = PostingRecord()

    for column, attribute in _COPYBOOK_LOAD_ORDER:
        if column not in row:
            continue
        entry = _ENTRY_BY_COLUMN[column]
        raw = row[column]
        current = getattr(posting, attribute)
        if entry.bridge_host_variable.character_length is not None:
            setattr(
                posting,
                attribute,
                _fixed_char(
                    "" if raw is None else str(raw),
                    entry.bridge_host_variable.character_length,
                ),
            )
        elif isinstance(current, decimal.Decimal):
            setattr(
                posting,
                attribute,
                decimal.Decimal(0) if raw is None else decimal.Decimal(raw),
            )
        else:
            setattr(posting, attribute, 0 if raw is None else int(raw))

    # The three derived columns are NOT unloaded. Reading them here and doing
    # nothing with them is the faithful translation of ten moves for thirteen
    # columns [common/irspostingMT.cbl:L1006-L1018]; the read is what makes the
    # omission visible to a reader rather than looking like an oversight.
    #  NO RECORD HERE. `bb100-UnloadHVs` issues ten moves for thirteen columns
    #  [common/irspostingMT.cbl:L1006-L1018]: the three derived columns are simply
    #  not among them, and the bridge displays nothing about it. A record announcing
    #  the absence of a move is a record with no counterpart (R-4), and it fired once
    #  per column per row. The omission is `DERIVED_COLUMNS` itself, and it is
    #  documented there and in `docs/migration/anomaly-log.md`.
    return posting


def _bridge_status(outcome: CursorOutcome) -> tuple[int, int]:
    """Translate a cursor outcome into ``irspostingMT``'s own status pair.

    ``glpostingMT`` writes ``move 10 to fs-Reply WE-Error`` and leaves it; this bridge
    overwrites the 10 with 3 [common/irspostingMT.cbl:L405-L406] and writes a 2 where
    the other writes nothing [common/irspostingMT.cbl:L533-L534].

    Args:
        outcome: What the cursor machinery reported.

    Returns:
        The ``(FS-Reply, We-Error)`` pair this bridge would have written.
    """
    if outcome.fs_reply == FsReply.END_OF_FILE:
        return END_OF_FILE
    if outcome.fs_reply == FsReply.INVALID_KEY_ON_START:
        return NOT_FOUND
    return int(outcome.fs_reply), int(outcome.we_error)


def _store(
    file_access: FileAccess,
    fs_reply: int,
    we_error: int,
    *,
    trace: int | None = None,
    file_key: str | None = None,
    write_status: bool = True,
) -> tuple[int, int]:
    """Write a status pair, and optionally a trace number and log tag.

    One place for the ``move n to FS-Reply`` / ``move n to WE-Error`` pattern that the
    frozen source writes at more than thirty sites, so a caller reads as the paragraph
    it reproduces rather than as four assignments.

    Returns:
        The pair now in force - the one just written, or the caller's own where the
            frozen path writes none, so a verb can both record and return in one
            statement.
    """
    if write_status:
        file_access.fs_reply = fs_reply
        file_access.we_error = we_error
    if trace is not None:
        file_access.logging_data.ws_no_paragraph = trace
    if file_key is not None:
        # `WS-File-Key` is `pic x(64)` [copybooks/wsfnctn.cob:L52] and is a LOG TAG only
        # - it never reaches a column.
        file_access.logging_data.ws_file_key = _fixed_char(file_key, 64)
    return int(file_access.fs_reply), int(file_access.we_error)


def _clear_sql_fields(file_access: FileAccess) -> None:
    """``move spaces to SQL-Err SQL-Msg SQL-State`` [common/acasirsub4.cbl:L216].

    The handler clears the three diagnostic fields on entry to its flat dispatch, and
    the bridge clears them again in ``ba010-Initialise``
    [common/irspostingMT.cbl:L236-L246].
    """
    logging_data = file_access.logging_data
    logging_data.sql_err = ""
    logging_data.sql_msg = ""
    logging_data.sql_state = ""


def _record_driver_error(
    file_access: FileAccess,
    error: Exception,
    *,
    command: str,
    we_error: int = int(WeError.SUCCESS),
    file_function: int | None = None,
) -> tuple[int, int]:
    """Map a driver failure through the shared ``Mysql-1100-DB-Error`` translation."""
    status = mysql_1100_db_error(
        errno=str(getattr(error, "errno", "") or ""),
        message=str(error),
        sql_state=str(getattr(error, "sqlstate", "") or ""),
        command=command,
        we_error=we_error,
    )
    if file_function is not None:
        status = override_we_error_for_operation(status, file_function)
    logging_data = file_access.logging_data
    logging_data.sql_err = status.sql_err
    logging_data.sql_msg = status.sql_msg
    logging_data.sql_state = status.sql_state
    return _store(file_access, int(status.fs_reply), int(status.we_error))


_QUOTED_TABLE: Final[str] = quote_identifier(TABLE)
_QUOTED_KEY: Final[str] = quote_identifier(PRIMARY_KEY)
"""Pre-quoted identifiers.

MANDATORY, NOT STYLISTIC. Every identifier in this table contains a hyphen -
``IRSPOSTING-REC``, ``KEY-4``, ``POST4-CODE``, ``VAT-AC-DEF4`` - so unquoted they are
parsed as subtraction and the statement is a syntax error.
"""


def _assignment_clause() -> str:
    """Build the ``SET`` list naming all thirteen columns in schema order.

    The bridge uses MySQL's ``INSERT ... SET`` form [common/irspostingMT.cbl:L1033]
    rather than a column list with a values list, and its update names the same thirteen
    in the same order [common/irspostingMT.cbl:L1211].
    """
    return ", ".join(f"{quote_identifier(column)} = %s" for column in COLUMNS)


def _ordered_parameters(loaded: Mapping[str, str]) -> tuple[str, ...]:
    """Order the loaded host variables to match :func:`_assignment_clause`.

    All thirteen, always, in schema order. Never a subset and never a null - the
    initialised group [common/irspostingMT.cbl:L966] guarantees a value for every one,
    which is what lets the frozen table declare them all not-null with no default.
    """
    return tuple(loaded[column] for column in COLUMNS)


def _key_predicate() -> str:
    """The equality predicate on the key of reference.

    ``'`' KeyName '`' '="' <record buffer substring> '"'`` - the construction the bridge
    assembles at [common/irspostingMT.cbl:L501-L510].
    """
    key = key_of_reference(TABLE, 1)
    if key.column_name != PRIMARY_KEY:
        raise RuntimeError(
            f"key of reference 1 for {TABLE} is {key.column_name!r}, expected "
            f"{PRIMARY_KEY!r} [common/irspostingMT.scb:L124]"
        )
    return f"{quote_identifier(key.column_name)} = %s"


def _key_value(posting: PostingRecord) -> str:
    """Render the key for a PREDICATE - the raw record buffer, zero-padded.

    THIS IS NOT THE SAME RENDERING THE ``SET`` LIST USES, and the difference is easy to
    miss.
    """
    digits = str(int(posting.post_key)).rjust(KEY_LENGTH, "0")
    # `pic 9(5)` truncates on the LEFT when the value is too wide, keeping the low-order
    # digits - the same silent narrowing the flat write's key increment relies on when
    # it wraps past 99999 [common/acasirsub4.cbl:L410].
    return digits[-KEY_LENGTH:]


_FD_RECORD_LENGTH: Final[int] = 5 + 2 + 8 + 5 + 5 + 9 + 32 + 2 + 2 + 9
"""``function length ( Record-4 )`` [common/acasirsub4.cbl:L477].

The two money items are ``pic s9(7)v99 sign is leading`` with NO ``separate character``
clause, so the sign is overpunched onto the leading digit and the item occupies nine
bytes rather than ten - confirmed by compiled measurement of ``function length`` on the
linkage field.
"""


def _record_size_gate(
    system: SystemRecord, file_access: FileAccess
) -> tuple[int, int] | None:
    """``ba012-Test-WS-Rec-Size-2`` [common/acasirsub4.cbl:L471-L511].

    Compares the linkage record's length against the FD record's and refuses to proceed
    if the linkage record is the shorter, then captures the connection parameters.

    Args:
        system: Supplies the six connection parameters, taken in the handler's own order
            - schema, user, password, port, host, socket
            [common/acasirsub4.cbl:L505-L510].
        file_access: Receives the status pair on failure.

    Returns:
        ``None`` when the gate passes, or the ``(99, 901)`` pair when it does not, in
            which case the caller must return immediately without touching the database.
    """
    global _RECORD_SIZE_CHECKED
    if _RECORD_SIZE_CHECKED:
        return None

    linkage_length = sum(
        entry.copybook.character_length or entry.copybook.digits or 0
        for entry in _ENTRIES
        if entry.copybook is not None
    )
    if linkage_length < _FD_RECORD_LENGTH:
        # `if A < B move 901 to WE-Error move 99 to fs-reply`
        # [common/acasirsub4.cbl:L480-L482], then IR902/IR901 and `go to ba-rdbms-exit`
        # [common/acasirsub4.cbl:L498] - THE BRIDGE IS NEVER CALLED.
        _LOG.error(
            "%s: IR902 record size gate refused the call - the linkage record "
            "measured %d against the file record's %d "
            "[common/acasirsub4.cbl:L474-L482]",
            TABLE,
            linkage_length,
            _FD_RECORD_LENGTH,
        )
        return _store(
            file_access, int(FsReply.ERROR), RECORD_SIZE_MISMATCH
        )

    # `move RDBMS-DB-Name to DB-Schema` and the five that follow
    # [common/acasirsub4.cbl:L505-L510].
    captured = rdb_data_from_system_record(system)
    rdb_data = file_access.rdb_data
    rdb_data.db_schema = captured.db_schema
    rdb_data.db_uname = captured.db_uname
    rdb_data.db_upass = captured.db_upass
    rdb_data.db_port = captured.db_port
    rdb_data.db_host = captured.db_host
    rdb_data.db_socket = captured.db_socket

    _RECORD_SIZE_CHECKED = True
    return None


def open_(
    system: SystemRecord,
    file_access: FileAccess,
    *,
    access_type: int = int(AccessType.INPUT),
) -> tuple[int, int]:
    """``fn-open`` - ``ba020-Process-Open`` [common/irspostingMT.cbl:L283-L325].

    Args:
        system: Source of the connection parameters.
        file_access: Receives the status pair, the trace number and the log tag.
        access_type: Recorded for the log and for the caller's own inspection; it
            selects no different behaviour here, exactly as the bridge selects none.

    Returns:
        The ``(FS-Reply, We-Error)`` pair.
    """
    global _CONNECTION

    gate = _record_size_gate(system, file_access)
    if gate is not None:
        return gate

    if _CONNECTION is not None:
        # The bridge reconnects unconditionally, so an open on an already-open
        # connection replaces it.
        mysql_1999_exit()
        mysql_1980_close(_CONNECTION)
        _CONNECTION = None

    outcome = mysql_1000_open(
        system, ws_no_paragraph=BRIDGE_TRACE[int(FileFunction.OPEN)]
    )
    outcome = mysql_1090_exit(outcome)

    logging_data = file_access.logging_data
    logging_data.sql_err = outcome.sql_err
    logging_data.sql_msg = outcome.sql_msg
    logging_data.sql_state = outcome.sql_state

    if outcome.fs_reply != FsReply.SUCCESS or outcome.connection is None:
        return _store(
            file_access,
            int(outcome.fs_reply),
            int(outcome.we_error),
            trace=BRIDGE_TRACE[int(FileFunction.OPEN)],
        )

    _CONNECTION = outcome.connection
    _cursor_reset(TABLE)
    return _store(
        file_access,
        int(FsReply.SUCCESS),
        int(WeError.SUCCESS),
        trace=BRIDGE_TRACE[int(FileFunction.OPEN)],
        file_key="OPEN IRSPOSTING",
    )


def open_input(system: SystemRecord, file_access: FileAccess) -> tuple[int, int]:
    """``fn-open`` with ``fn-input`` - published by the facade at
    [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L261].
    """
    return open_(system, file_access, access_type=int(AccessType.INPUT))


def open_extend(system: SystemRecord, file_access: FileAccess) -> tuple[int, int]:
    """``fn-open`` with ``fn-extend``.

    The flat path refuses this outright with ``(99, 997)``
    [common/acasirsub4.cbl:L270-L271], the copybook noting extend is "not valid for
    ISAM" [copybooks/wsfnctn.cob:L109]. THE DATABASE PATH DOES NOT REFUSE IT.
    """
    return open_(system, file_access, access_type=int(AccessType.EXTEND))


def close(file_access: FileAccess) -> tuple[int, int]:
    """``fn-close`` - ``ba030-Process-Close`` [common/irspostingMT.cbl:L327-L340]."""
    global _CONNECTION

    _cursor_reset(TABLE)

    if _CONNECTION is not None:
        mysql_1980_close(_CONNECTION)
        _CONNECTION = None
    mysql_1999_exit()

    # `move "CLOSE IRSPOSTING" to WS-File-Key` [common/irspostingMT.cbl:L332]. The
    # status pair is deliberately NOT written - see the docstring.
    logging_data = file_access.logging_data
    logging_data.ws_no_paragraph = BRIDGE_TRACE[int(FileFunction.CLOSE)]
    logging_data.ws_file_key = _fixed_char("CLOSE IRSPOSTING", 64)
    return int(file_access.fs_reply), int(file_access.we_error)


def _require_connection(file_access: FileAccess) -> Any:
    """Return the open connection, or record the bridge's init failure.

    The bridge assumes a connection is present in every verb but ``ba020`` - there is no
    re-open and no test.
    """
    if _CONNECTION is None:
        # ONE ERROR, through the shared reporter, so this failure renders with the
        # same fields in the same order as every other handler's.
        log_handler_failure(
            _LOG,
            program=TABLE,
            paragraph="_require_connection",
            locator="[common/irspostingMT.cbl:L283-L325]",
            fs_reply=int(FsReply.ERROR),
            we_error=int(WeError.RDB_INIT_ERROR),
            detail="a verb was called with no open connection; the frozen bridge "
            "assumes one from ba020-Process-Open onward",
        )
        _store(file_access, int(FsReply.ERROR), int(WeError.RDB_INIT_ERROR))
        return None
    return _CONNECTION


@contextmanager
def _positioning_cursor(connection: Any) -> Iterator[Any]:
    """Yield a bare driver cursor for the positioning machinery to drive.

    ``cursor_state`` issues its OWN statements - the select that positions, and the
    fetches that walk the stored result - so it needs a cursor handle rather than a
    statement executed on its behalf.
    """
    cursor = acquire_cursor(connection)
    try:
        yield cursor
    finally:
        try:
            cursor.close()
        except Exception:  # noqa: BLE001, S110 - driver-specific, see below
            # A cursor that will not close is not a condition the frozen source has
            # an error path for, and raising from a `finally` would hide the caller's
            # own failure. Dropped.
            #  NOTHING IS LOGGED AND NO NAME IS BOUND. The frozen bridge has no
            #  cursor-close step, so a record here was invented (R-4), and the record
            #  it replaced interpolated the driver's exception WITHOUT EVEN
            #  ESCAPING IT - a message carrying a newline could forge a second log
            #  record (CWE-117) and one carrying the statement leaks the posting key
            #  (CWE-532). Binding no name means nothing can leak by accident.
            pass


def read_next(file_access: FileAccess) -> tuple[int, PostingRecord | None]:
    """``fn-read-next`` - ``ba040`` falling into ``ba041-Reread``.

    THE READ IS UNFILTERED (anomaly A24). ``aa041-Reread``
    [common/acasirsub4.cbl:L312-L321] has no loop-back and no predicate, so every row is
    delivered.

    Returns:
        The ``FS-Reply`` and the record, or ``(10, None)`` at end of file.
    """
    connection = _require_connection(file_access)
    if connection is None:
        return int(file_access.fs_reply), None

    with _positioning_cursor(connection) as cursor:
        outcome = _cursor_read_next(
            cursor, TABLE, slot=CursorSlot.PRIMARY, file_access=file_access
        )
        fs_reply, we_error = _bridge_status(outcome)

        if outcome.row is None:
            # `move "EOF" to WS-File-Key` for logging [common/acasirsub4.cbl:L319];
            # `initialize Posting-Record` [common/acasirsub4.cbl:L318] leaves the
            # caller's record cleared. THE STICKY-EOF DISCARD WRITES NO STATUS.
            fs_reply, we_error = _store(
                file_access,
                fs_reply,
                we_error,
                trace=BRIDGE_TRACE[int(FileFunction.READ_NEXT)],
                file_key=outcome.file_key or "EOF",
                write_status=outcome.status_written,
            )
            return fs_reply, None

        posting = _unload_host_variables(outcome.row)
        _store(
            file_access,
            int(FsReply.SUCCESS),
            int(WeError.SUCCESS),
            trace=BRIDGE_TRACE[int(FileFunction.READ_NEXT)],
            file_key=str(posting.post_key),
        )
        return int(FsReply.SUCCESS), posting


def read_indexed(
    posting: PostingRecord, file_access: FileAccess
) -> tuple[int, PostingRecord | None]:
    """``fn-read-indexed`` - ``ba050-Process-Read-Indexed``.

    [common/irspostingMT.cbl:L490-L590]. One equality select on the key of reference,
    then one fetch.

    Returns:
        The ``FS-Reply`` and the record, or ``(21, None)`` when not found.
    """
    connection = _require_connection(file_access)
    if connection is None:
        return int(file_access.fs_reply), None

    with _positioning_cursor(connection) as cursor:
        outcome = _cursor_read_indexed(
            cursor,
            TABLE,
            _key_value(posting),
            key_number=1,
            slot=CursorSlot.PRIMARY,
            file_access=file_access,
        )
        fs_reply, we_error = _bridge_status(outcome)

        if outcome.row is None:
            # `move 21 to fs-reply` then `move 2 to we-error`
            # [common/irspostingMT.cbl:L533-L534].
            fs_reply, we_error = _store(
                file_access,
                fs_reply,
                we_error,
                trace=BRIDGE_TRACE[int(FileFunction.READ_INDEXED)],
                write_status=outcome.status_written,
            )
            return fs_reply, None

        found = _unload_host_variables(outcome.row)
        _store(
            file_access,
            int(FsReply.SUCCESS),
            int(WeError.SUCCESS),
            trace=BRIDGE_TRACE[int(FileFunction.READ_INDEXED)],
            file_key=str(found.post_key),
        )
        return int(FsReply.SUCCESS), found


def start(
    posting: PostingRecord,
    file_access: FileAccess,
    *,
    access_type: int = int(AccessType.EQUAL_TO),
) -> tuple[int, PostingRecord | None]:
    """``fn-start`` - ``ba060-Process-Start`` [common/irspostingMT.cbl:L592-L703].

    START DOES NOT MERELY POSITION - IT RETURNS A RECORD (anomaly A11). The paragraph
    ends ``perform ba999-end`` and then ``go to ba041-Reread``
    [common/irspostingMT.cbl:L698-L702], and the handler does the same with ``perform
    aa999-main-exit.`` followed by ``go to aa041-Reread.``
    [common/acasirsub4.cbl:L400-L401].

    Args:
        posting: Supplies the key to position on.
        file_access: Receives the status pair.
        access_type: 5 through 8 - equal to, less than, greater than, not less than.

    Returns:
        The ``FS-Reply`` and the first matching record, or ``(21, None)``.
    """
    connection = _require_connection(file_access)
    if connection is None:
        return int(file_access.fs_reply), None

    if not 5 <= int(access_type) <= 8:
        # `(99, 997)` and leave, WITHOUT issuing a statement
        # [common/irspostingMT.cbl:L599-L603].
        # ONE ERROR, through the shared reporter. The refusal returns 99 to the
        # caller, so it is a failure and DEBUG put it below the level an operator
        # watches - the same reasoning that took every sibling's verb refusal off
        # DEBUG.
        log_handler_failure(
            _LOG,
            program=TABLE,
            paragraph="ba060-Process-Start",
            locator="[common/irspostingMT.cbl:L599-L601]",
            fs_reply=int(FsReply.ERROR),
            we_error=BRIDGE_START_PARAM_ERROR,
            detail="fn-start refused access type %s: the bridge admits 5 through "
            "8 only and rejects 9" % access_type,
        )
        fs_reply, we_error = _store(
            file_access,
            int(FsReply.ERROR),
            BRIDGE_START_PARAM_ERROR,
            trace=BRIDGE_TRACE[int(FileFunction.START)],
        )
        return fs_reply, None

    with _positioning_cursor(connection) as cursor:
        outcome = _cursor_start(
            cursor,
            TABLE,
            _key_value(posting),
            access_type,
            key_number=1,
            slot=CursorSlot.PRIMARY,
            file_access=file_access,
        )
        if not outcome.status_written:
            # ZERO ROWS WITH NO CLIENT ERROR - the one exit of this paragraph that
            # writes NO STATUS AT ALL.
            _store(
                file_access,
                int(file_access.fs_reply),
                int(file_access.we_error),
                trace=BRIDGE_TRACE[int(FileFunction.START)],
                write_status=False,
            )
        elif outcome.fs_reply != FsReply.SUCCESS:
            # `move 21 to fs-reply` then `move 2 to we-error`, guarded by the errno
            # test, then `go to ba999-End` [common/irspostingMT.cbl:L683-L685] - the
            # ONLY exit of this paragraph that does not fall into the read.
            fs_reply, we_error = _bridge_status(outcome)
            _store(
                file_access,
                fs_reply,
                we_error,
                trace=BRIDGE_TRACE[int(FileFunction.START)],
            )
            return fs_reply, None
        else:
            _store(
                file_access,
                int(FsReply.SUCCESS),
                int(WeError.SUCCESS),
                trace=BRIDGE_TRACE[int(FileFunction.START)],
                file_key=outcome.file_key or "",
            )

    return read_next(file_access)


def write(posting: PostingRecord, file_access: FileAccess) -> tuple[int, int]:
    """``fn-write`` - ``ba070-Process-Write`` + ``bb200-Insert``.

    THIS IS WHERE THE THREE BRIDGE-ONLY COLUMNS ARE POPULATED, and the only place they
    are ever written - see :func:`_derive_date_components` and
    :func:`_load_host_variables`. Anomaly A1, register entry ``A-7``.

    Returns:
        The ``(FS-Reply, We-Error)`` pair.
    """
    connection = _require_connection(file_access)
    if connection is None:
        return int(file_access.fs_reply), int(file_access.we_error)

    loaded = _load_host_variables(posting)
    statement = (
        f"INSERT INTO {_QUOTED_TABLE} SET {_assignment_clause()}"
    )
    parameters = _ordered_parameters(loaded)

    file_access.logging_data.ws_no_paragraph = BRIDGE_TRACE[
        int(FileFunction.WRITE)
    ]
    try:
        with execute_statement(connection, statement, parameters):
            pass
    except Exception as error:
        return _record_driver_error(
            file_access,
            error,
            command=statement,
            we_error=int(file_access.we_error),
        )

    return _store(
        file_access,
        int(FsReply.SUCCESS),
        int(WeError.SUCCESS),
        file_key=str(posting.post_key),
    )


def rewrite(posting: PostingRecord, file_access: FileAccess) -> tuple[int, int]:
    """``fn-re-write`` - ``ba090-Process-Rewrite`` + ``bb300-Update``.

    [common/irspostingMT.cbl:L871-L919] and [common/irspostingMT.cbl:L1200-L1374].

    Returns:
        The ``(FS-Reply, We-Error)`` pair - the caller's own, unchanged, when the
            statement matched no row.
    """
    connection = _require_connection(file_access)
    if connection is None:
        return int(file_access.fs_reply), int(file_access.we_error)

    loaded = _load_host_variables(posting)
    statement = (
        f"UPDATE {_QUOTED_TABLE} SET {_assignment_clause()} "
        f"WHERE {_key_predicate()}"
    )
    parameters = _ordered_parameters(loaded) + (_key_value(posting),)

    file_access.logging_data.ws_no_paragraph = BRIDGE_TRACE[
        int(FileFunction.RE_WRITE)
    ]
    try:
        with execute_statement(connection, statement, parameters) as cursor:
            affected = cursor.rowcount
    except Exception as error:
        return _record_driver_error(
            file_access,
            error,
            command=statement,
            file_function=int(FileFunction.RE_WRITE),
        )

    if affected != 1:
        # ANOMALY A10: no status is written. The caller's pair stands.
        #  NO RECORD HERE. The frozen update has no invalid-key path and writes
        #  NEITHER status field [common/irspostingMT.cbl:L898-L919], nor does it
        #  display anything, so a record was invented (R-4) - and the SILENCE is the
        #  anomaly, recorded in `docs/migration/anomaly-log.md`. The caller's own pair
        #  standing unchanged is what a caller observes, and it observes it exactly as
        #  it would from the compiled bridge.
        return int(file_access.fs_reply), int(file_access.we_error)

    file_access.logging_data.sql_err = ""
    file_access.logging_data.sql_msg = ""
    return _store(
        file_access,
        int(FsReply.SUCCESS),
        int(WeError.SUCCESS),
        file_key=str(posting.post_key),
    )


def delete(posting: PostingRecord, file_access: FileAccess) -> tuple[int, int]:
    """``fn-delete`` - ``ba080-Process-Delete`` [common/irspostingMT.cbl:L734-L788].

    One keyed delete [common/irspostingMT.cbl:L764-L768], issued with NO trailing
    semicolon in the frozen text - a difference from the insert and update, and a
    driver-level detail rather than a behavioural one.

    Returns:
        The ``(FS-Reply, We-Error)`` pair - unchanged when no row matched.
    """
    connection = _require_connection(file_access)
    if connection is None:
        return int(file_access.fs_reply), int(file_access.we_error)

    statement = f"DELETE FROM {_QUOTED_TABLE} WHERE {_key_predicate()}"
    parameters = (_key_value(posting),)

    file_access.logging_data.ws_no_paragraph = BRIDGE_TRACE[
        int(FileFunction.DELETE)
    ]
    try:
        with execute_statement(connection, statement, parameters) as cursor:
            affected = cursor.rowcount
    except Exception as error:
        return _record_driver_error(
            file_access,
            error,
            command=statement,
            file_function=int(FileFunction.DELETE),
        )

    if affected != 1:
        # ANOMALY A10 again - no status for a row that was not there.
        #  NO RECORD HERE, for the reason the rewrite arm gives: the frozen
        #  delete writes neither status field [common/irspostingMT.cbl:L771-L788] and
        #  displays nothing, and the silence is the anomaly.
        return int(file_access.fs_reply), int(file_access.we_error)

    return _store(
        file_access,
        int(FsReply.SUCCESS),
        int(WeError.SUCCESS),
        file_key=str(posting.post_key),
    )


def delete_all(posting: PostingRecord, file_access: FileAccess) -> tuple[int, int]:
    """``fn-Delete-All`` - ``ba085-Process-Delete-ALL``.

    IT IS BOUNDED, NOT A WHOLE-TABLE WIPE, and this corrects the note that described it
    as an unqualified delete.

    Returns:
        The ``(FS-Reply, We-Error)`` pair.
    """
    connection = _require_connection(file_access)
    if connection is None:
        return int(file_access.fs_reply), int(file_access.we_error)

    posting.post_key = posting.post_key + 1

    key = key_of_reference(TABLE, 1)
    statement = (
        f"DELETE FROM {_QUOTED_TABLE} "
        f"WHERE {quote_identifier(key.column_name)} < %s"
    )
    parameters = (_key_value(posting),)

    file_access.logging_data.ws_no_paragraph = BRIDGE_TRACE[
        int(FileFunction.DELETE_ALL)
    ]
    try:
        with execute_statement(connection, statement, parameters) as cursor:
            affected = cursor.rowcount
    except Exception as error:
        return _record_driver_error(
            file_access,
            error,
            command=statement,
            we_error=int(WeError.DELETE_SQLSTATE_NOT_00000),
        )

    file_access.logging_data.ws_count_rows = max(affected, 0)
    _cursor_reset(TABLE)
    return _store(
        file_access,
        int(FsReply.SUCCESS),
        int(WeError.SUCCESS),
        file_key=f"Deleting back from {posting.post_key}",
    )


def open_output(
    system: SystemRecord, posting: PostingRecord, file_access: FileAccess
) -> tuple[int, int]:
    """``fn-open`` with ``fn-output`` - THE TWO-CALL COERCION.

    and then FALLS THROUGH into ``ba020-Process-DAL`` [common/acasirsub4.cbl:L531]. So
    the bridge is called TWICE: once with the function still open/output, which
    connects, and once more with the function now 6, which clears the data down. Anomaly
    A19.

    Args:
        system: For the connect.
        posting: For the delete-all bound, whose key this call increments.
        file_access: Receives the status pair.

    Returns:
        The pair from the second call, the delete-all, since it runs last.
    """
    fs_reply, we_error = open_(
        system, file_access, access_type=int(AccessType.OUTPUT)
    )
    if fs_reply != FsReply.SUCCESS:
        return fs_reply, we_error

    # ANOMALY A20: `move RDBMS-Flat-Statuses to FA-RDBMS-Flat-Statuses`
    # [common/acasirsub4.cbl:L197] is NOT performed on this path. Left undone
    # deliberately - see the docstring.

    file_access.file_function = int(FileFunction.DELETE_ALL)
    return delete_all(posting, file_access)


def _key_number_guard(file_access: FileAccess) -> tuple[int, int] | None:
    """``evaluate File-Function`` key guard [common/acasirsub4.cbl:L165-L179].

    Both set ``FS-Reply`` to 99 and leave immediately.

    Returns:
        ``None`` when the guard passes, otherwise the refusing pair.
    """
    function = int(file_access.file_function)
    key_number = int(file_access.logging_data.file_key_no)
    if key_number == KEY_COUNT:
        return None

    if function in (
        int(FileFunction.READ_INDEXED),
        int(FileFunction.START),
    ):
        return _store(
            file_access, int(FsReply.ERROR), FILE_KEY_NO_START_ERROR
        )
    if function == int(FileFunction.DELETE):
        return _store(
            file_access, int(FsReply.ERROR), FILE_KEY_NO_DELETE_ERROR
        )
    return None


def dispatch(
    system: SystemRecord,
    posting: PostingRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> tuple[int, int]:
    """``acasirsub4``'s procedure division [common/acasirsub4.cbl:L145-L235].

    The sequence reproduced, in the source's own order.

    Args:
        system: ``SYSTEM-REC``, supplying the connection parameters.
        posting: ``Posting-Record``, both input and output.
        file_access: Carries the function code, the access type, the key number and the
            returned status. Mutated, as the frozen linkage is.
        file_defs: The file-name block. Accepted because the frozen linkage accepts it.
        dal_common: The testing-flag block [common/acasirsub4.cbl:L143].

    Returns:
        The ``(FS-Reply, We-Error)`` pair, exactly as the frozen handler leaves them in
            ``File-Access``.
    """
    logging_data = file_access.logging_data
    logging_data.ws_log_system = WS_LOG_SYSTEM
    logging_data.ws_log_file_no = WS_LOG_FILE_NO_FLAT

    function = int(file_access.file_function)
    access_type = int(file_access.access_type)

    # Step 2 - the key-number guard, before anything else can run.
    refusal = _key_number_guard(file_access)
    if refusal is not None:
        # ONE ERROR, through the shared reporter. `File-Function` and `File-Key-No`
        # are operation codes from the frozen vocabulary
        # [copybooks/wsfnctn.cob:L88-L116], not business data.
        log_handler_failure(
            _LOG,
            program=TABLE,
            paragraph="aa000-Main-Process key guard",
            locator="[common/acasirsub4.cbl:L165-L179]",
            fs_reply=int(refusal[0]),
            we_error=int(refusal[1]),
            detail="File-Function %s refused for File-Key-No %s"
            % (function, int(logging_data.file_key_no)),
        )
        return refusal

    logging_data.ws_log_file_no = WS_LOG_FILE_NO_RDB

    # Step 3 - open/output, whose coercion must be handled before the ordinary dispatch
    # because it changes the function code [common/acasirsub4.cbl:L185-L192],
    # [common/acasirsub4.cbl:L518-L522].
    if function == int(FileFunction.OPEN) and access_type == int(
        AccessType.OUTPUT
    ):
        _clear_sql_fields(file_access)
        return open_output(system, posting, file_access)

    file_access.we_error = int(WeError.SUCCESS)
    _clear_sql_fields(file_access)

    if function == int(FileFunction.OPEN):
        if access_type == int(AccessType.EXTEND):
            return open_extend(system, file_access)
        return open_(system, file_access, access_type=access_type)

    if function == int(FileFunction.CLOSE):
        return close(file_access)

    if function == int(FileFunction.READ_NEXT):
        fs_reply, found = read_next(file_access)
        if found is not None:
            _copy_into(posting, found)
        return fs_reply, int(file_access.we_error)

    if function == int(FileFunction.READ_INDEXED):
        fs_reply, found = read_indexed(posting, file_access)
        if found is not None:
            _copy_into(posting, found)
        return fs_reply, int(file_access.we_error)

    if function == int(FileFunction.WRITE):
        return write(posting, file_access)

    if function == int(FileFunction.RE_WRITE):
        return rewrite(posting, file_access)

    if function == int(FileFunction.DELETE):
        return delete(posting, file_access)

    if function == int(FileFunction.START):
        fs_reply, found = start(
            posting, file_access, access_type=access_type
        )
        if found is not None:
            _copy_into(posting, found)
        return fs_reply, int(file_access.we_error)

    # `when other  *> 6 is unused  go to aa100-Bad-Function`
    # [common/acasirsub4.cbl:L234-L235]. Code 6 lands here even though the BRIDGE
    # dispatches it [common/irspostingMT.cbl:L271-L272] - delete-all is reachable
    # only through the open/output coercion in step 3. Anomaly A18.
    #  NO SEPARATE RECORD FOR CODE 6. The frozen `when other` treats it exactly
    #  as it treats any other unhandled code - one arm, one outcome - so a record
    #  distinguishing it announced an anomaly rather than an event (R-4). Anomaly A18
    #  is recorded in this function's docstring and in
    #  `docs/migration/anomaly-log.md`, and the ONE bad-function record below names
    #  the code, so an operator still sees which function was refused.

    # `aa100-Bad-Function` -> `(99, 999)`. `*> Houston; We have a problem`
    # [common/acasirsub4.cbl:L437-L441].
    log_handler_failure(
        _LOG,
        program=TABLE,
        paragraph="aa100-Bad-Function",
        locator="[common/acasirsub4.cbl:L437-L441]",
        fs_reply=int(FsReply.ERROR),
        we_error=HANDLER_BAD_FUNCTION,
        detail="File-Function %s is not dispatched by this handler; code 6 lands "
        "here even though the bridge implements it "
        "[common/irspostingMT.cbl:L271-L272] - anomaly A18" % function,
    )
    return _store(file_access, int(FsReply.ERROR), HANDLER_BAD_FUNCTION)


def _copy_into(target: PostingRecord, source: PostingRecord) -> None:
    """``move Record-4 to Posting-Record`` [common/acasirsub4.cbl:L322].

    A read delivers its row into the CALLER'S record, because the linkage record is
    passed by reference.
    """
    for _column, attribute in _COPYBOOK_LOAD_ORDER:
        setattr(target, attribute, getattr(source, attribute))


# Rule R-5 requires every paragraph to map to a function and every field to a dictionary
# entry.
