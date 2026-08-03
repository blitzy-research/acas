"""``acasirsub4`` + ``irspostingMT`` -> ``IRSPOSTING-REC``: the IRS posting table.

TEN COPYBOOK FIELDS BECOME THIRTEEN COLUMNS, AND THAT GAP IS WHY THIS MODULE
EXISTS. ``copybooks/irswspost.cob`` declares exactly ten elementary items
[copybooks/irswspost.cob:L9-L18]. The frozen table declares thirteen
[mysql/ACASDB.sql:L275-L287]. The three extra columns - ``POST4-DAY``,
``POST4-MONTH`` and ``POST4-YEAR`` - appear in NO copybook anywhere in the
repository; they exist only because the bridge derives them from a date string.
The Agent Action Plan builds its whole authority argument on this table, section
0.1.1 verbatim:

    "The bridge, not the copybook, must be treated as authoritative - and the
    codebase proves why. The internal IRS posting table carries three columns,
    ``POST4-DAY``, ``POST4-MONTH`` and ``POST4-YEAR``, that have no counterpart
    in any copybook; they exist only because the bridge derives them from a date
    string with a guarded substring rule [common/irspostingMT.cbl:L982-L987]. A
    migration driven from the copybooks alone would silently omit three columns
    of a posting table."

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


#  IDENTITY  -  THE TABLE, ITS KEY, AND ITS KEY METADATA


TABLE: Final[str] = "IRSPOSTING-REC"
"""The table this handler owns [mysql/ACASDB.sql:L274]."""

PRIMARY_KEY: Final[str] = "KEY-4"
"""The single-column primary key [mysql/ACASDB.sql:L288].

Named after the HANDLER NUMBER, not after its contents, exactly as ``IRSNL-REC``
names its key ``KEY-1`` after ``acasirsub1``. The digit 4 is injected in three
different positions across this table - as a prefix (``POST4-CODE``), as a key
suffix (``KEY-4``), and as a field suffix (``VAT-AC-DEF4``, ``VAT-AMOUNT4``).
"""

KEY_OFFSET: Final[int] = 1
KEY_LENGTH: Final[int] = 5
"""The key's one-based offset and length within the record buffer.

From ``"00010005"`` [common/irspostingMT.scb:L125], which matches ``Post-Key pic
9(5)`` [copybooks/irswspost.cob:L9] exactly - unlike ``irsdfltMT``, whose
offset/length indexes a field its record does not contain.
"""

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
"""``keyOfReference occurs 1`` [common/irspostingMT.scb:L129].

One key of reference, therefore one cursor - ``Most-Cursor-Set`` is a single flag
[common/irspostingMT.scb:L141], so only :attr:`CursorSlot.PRIMARY` is ever used.
"""


#  THE COLUMN LIST  -  DERIVED FROM THE DICTIONARY, VALIDATED AGAINST THE SCHEMA


_FROZEN_COLUMNS: Final[tuple[str, ...]] = (
    "KEY-4",  # [mysql/ACASDB.sql:L275]  mediumint(5) unsigned
    "POST4-CODE",  # [mysql/ACASDB.sql:L276]  char(2)
    "POST4-DAT",  # [mysql/ACASDB.sql:L277]  char(8)   "DATE" truncated
    "POST4-DAY",  # [mysql/ACASDB.sql:L278]  tinyint(2) unsigned  BRIDGE-ONLY
    "POST4-MONTH",  # [mysql/ACASDB.sql:L279]  tinyint(2) unsigned  BRIDGE-ONLY
    "POST4-YEAR",  # [mysql/ACASDB.sql:L280]  tinyint(2) unsigned  BRIDGE-ONLY
    "POST4-DR",  # [mysql/ACASDB.sql:L281]  mediumint(5) unsigned
    "POST4-CR",  # [mysql/ACASDB.sql:L282]  mediumint(5) unsigned
    "POST4-AMOUNT",  # [mysql/ACASDB.sql:L283]  decimal(9,2)  SIGNED
    "POST4-LEGEND",  # [mysql/ACASDB.sql:L284]  char(32)
    "VAT-AC-DEF4",  # [mysql/ACASDB.sql:L285]  tinyint(2) unsigned
    "POST4-VAT-SIDE",  # [mysql/ACASDB.sql:L286]  char(2)
    "VAT-AMOUNT4",  # [mysql/ACASDB.sql:L287]  decimal(9,2)  SIGNED
)
"""The thirteen columns in schema order, read directly from the frozen table.

Held ONLY to validate the generated dictionary against the frozen source at
import. :data:`COLUMNS` - the list every statement is built from - is derived
from the dictionary, because plan section 0.8.1 makes that ordering a directive:
"every Python field definition cites its entry. This ordering is a directive, not
a preference - it is what prevents fields being transcribed by eye." Keeping both
turns a dictionary regeneration that drifted from the schema into an import-time
failure instead of a silent behavioural change.
"""


def _dictionary_entries() -> tuple[Any, ...]:
    """Return this table's dictionary entries in column-ordinal order.

    ``entries_for_table`` orders by ordinal, so the three bridge-only columns
    arrive interleaved at positions 4, 5 and 6 - the schema's own order - rather
    than appended.

    Raises:
        RuntimeError: If the dictionary disagrees with the frozen table
            declaration, in either the set of columns or their order.
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

Every statement in this module names all thirteen and binds all thirteen. None is
ever omitted and none is ever bound as a null, because ``initialize
TD-IRSPOSTING-REC`` [common/irspostingMT.cbl:L966] guarantees the bridge always
has a value to send - which is why the frozen declaration can mark every column
not-null with no default.
"""


#  THE THREE BRIDGE-ONLY COLUMNS AND THEIR SUBSTRING RULES


DERIVED_COLUMNS: Final[tuple[str, ...]] = (
    "POST4-DAY",
    "POST4-MONTH",
    "POST4-YEAR",
)
"""The columns with no copybook counterpart [common/irspostingMT.cbl:L177-L179].

ANOMALY A1, the plan's register entry ``A-7``, and the reason this module is the
plan's proof that the bridge is authoritative. Derived on every write
[common/irspostingMT.cbl:L982-L987] and read back NEVER (anomaly A3) - the unload
performs ten moves for thirteen columns
[common/irspostingMT.cbl:L1006-L1015], because no copybook field exists to
receive them. The maintainer's rationale
[common/irspostingMT.cbl:L1017-L1018]: "only used in select statements instead of
a sort."
"""

DERIVED_COLUMN_SLICES: Final[Mapping[str, tuple[int, int]]] = MappingProxyType(
    {
        # `Post-Date (1:2)` -> one-based offset 1, length 2.
        "POST4-DAY": (1, 2),  # [common/irspostingMT.cbl:L982-L983]
        # `Post-Date (4:2)` - positions 4 and 5, skipping the separator at 3.
        "POST4-MONTH": (4, 2),  # [common/irspostingMT.cbl:L984-L985]
        # `Post-Date (7:2)` - a TWO-DIGIT year is all that is ever stored.
        "POST4-YEAR": (7, 2),  # [common/irspostingMT.cbl:L986-L987]
    }
)
"""The reference-modification offsets, one-based, exactly as the source writes.

The implied layout is ``DD/MM/YY`` with separators at positions 3 and 6, and
THOSE TWO POSITIONS ARE NEVER EXAMINED (anomaly A4) - so ``"01X02X23"`` derives
day 1, month 2, year 23 without complaint. No separator check, no range check and
no century inference is added; the class test is the entire validation, and rule
R-3 forbids extending it.
"""

POST_DATE_LENGTH: Final[int] = 8
"""``Post-Date pic x(8)`` [copybooks/irswspost.cob:L11], space-padded."""


#  LOG IDENTITY  -  `WS-Log-System` AND `WS-Log-File-No`


WS_LOG_SYSTEM: Final[int] = int(LogSystem.IRS)
"""``move 1 to WS-Log-System`` [common/acasirsub4.cbl:L160], 1 being IRS."""

WS_LOG_FILE_NO_FLAT: Final[int] = 13
"""``move 13 to WS-Log-File-No`` [common/acasirsub4.cbl:L161]."""

WS_LOG_FILE_NO_RDB: Final[int] = 23
"""``move 23 to WS-Log-File-no`` [common/acasirsub4.cbl:L469].

The database path bumps the file number and the flat path does not, because the
bump lives in ``ba010-Test-WS-Rec-Size`` which only the database branch reaches.
So 23 is the effective number here. It COLLIDES with ``acas013``'s 23, and only
the ``(system, file)`` pair disambiguates - ``acas013`` logs under system 6 where
this handler logs under system 1.
"""


#  TRACE NUMBERS  -  `WS-No-Paragraph`, TWO INDEPENDENT SETS


HANDLER_TRACE: Final[Mapping[int, int]] = MappingProxyType(
    {
        int(FileFunction.OPEN): 201,  # [common/acasirsub4.cbl:L244]
        int(FileFunction.CLOSE): 202,  # [common/acasirsub4.cbl:L283]
        int(FileFunction.READ_NEXT): 203,  # [common/acasirsub4.cbl:L300]
        int(FileFunction.READ_INDEXED): 204,  # [common/acasirsub4.cbl:L336]
        int(FileFunction.START): 205,  # [common/acasirsub4.cbl:L354]
        int(FileFunction.WRITE): 206,  # [common/acasirsub4.cbl:L404]
        int(FileFunction.DELETE): 207,  # [common/acasirsub4.cbl:L416]
        int(FileFunction.RE_WRITE): 208,  # [common/acasirsub4.cbl:L429]
    }
)
"""The handler's own trace numbers, 201 through 208.

``acasirsub4`` is the eighth handler using this identical band; ``acasirsub1`` is
the only one that breaks it, adding numbers for its two raw verbs. Note the
mapping is by FUNCTION, not by execution order - delete is 207 and rewrite 208,
whereas the dispatch tests rewrite before delete
[common/acasirsub4.cbl:L229-L231].
"""

BRIDGE_TRACE: Final[Mapping[int, int]] = MappingProxyType(
    {
        int(FileFunction.OPEN): 1,  # [common/irspostingMT.cbl:L312]
        int(FileFunction.CLOSE): 2,  # [common/irspostingMT.cbl:L331]
        int(FileFunction.READ_NEXT): 3,  # [common/irspostingMT.cbl:L372]
        int(FileFunction.READ_INDEXED): 5,  # [common/irspostingMT.cbl:L515]
        int(FileFunction.START): 8,  # [common/irspostingMT.cbl:L654]
        int(FileFunction.WRITE): 10,  # [common/irspostingMT.cbl:L713]
        int(FileFunction.DELETE): 13,  # [common/irspostingMT.cbl:L757]
        int(FileFunction.DELETE_ALL): 15,  # [common/irspostingMT.cbl:L838]
        int(FileFunction.RE_WRITE): 17,  # [common/irspostingMT.cbl:L875]
    }
)
"""The bridge's trace numbers, an entirely different scale from the handler's.

Both are written into the same ``ws-No-Paragraph`` field
[copybooks/wsfnctn.cob:L48] as control passes down, so the value observed at any
moment depends on which layer last ran. The bridge's is the one that survives a
database call, because it runs last - so these are what this module reports.
Numbers 4, 6 and 20 also occur, for the reread, the indexed fetch and the cursor
free, and are set by the machinery that owns those steps.
"""


#  STATUS PAIRS  -  `(FS-Reply, We-Error)`, AND THE HANDLER/BRIDGE DISAGREEMENTS


END_OF_FILE: Final[tuple[int, int]] = (int(FsReply.END_OF_FILE), 3)
"""``(10, 3)`` - end of file for THIS bridge.

ANOMALY A12, the dead-status-overwrite idiom. Both layers write the pair twice and
the first write is dead. The handler
[common/acasirsub4.cbl:L314-L315] writes ``move 10 to WE-Error FS-Reply`` and then
``move 3 to WE-Error``, so the 10 in ``We-Error`` never survives. The bridge does
the same with the "proper" code commented out
[common/irspostingMT.cbl:L405-L406]::

    *>                   move 10 to WE-Error
                       move 3 to WE-Error                 *> as in irsub4

The effective pair is therefore ``(10, 3)``, repeated at
[common/irspostingMT.cbl:L454-L455] and [common/irspostingMT.cbl:L467-L469].

THIS DIFFERS FROM THE SHARED HELPER. ``status.end_of_file_status()`` returns
``(10, 10)``, which is correct for ``glpostingMT`` - the bridge that module was
derived from - and wrong here. That is why this constant exists and why
:func:`_bridge_status` remaps what the cursor machinery returns: the ISAM
positioning is common to every bridge, the status codes are not.
"""

NOT_FOUND: Final[tuple[int, int]] = (int(FsReply.INVALID_KEY_ON_START), 2)
"""``(21, 2)`` - key not found, for both the indexed read and the start.

The same dead-write idiom as :data:`END_OF_FILE`: ``move 21 to we-error fs-reply``
then ``move 2 to we-error`` [common/acasirsub4.cbl:L341-L342]. The bridge agrees
at [common/irspostingMT.cbl:L533-L534] and repeats it twice more with the
"proper" codes commented out - ``990`` at [common/irspostingMT.cbl:L568] and
``989`` at [common/irspostingMT.cbl:L577].

Note 21, never 23, even though ``FsReply`` carries a distinct ``KEY_NOT_FOUND``
of 23. And note that ``glpostingMT`` leaves ``We-Error`` UNTOUCHED on this
condition where this bridge writes 2 - a second reason the remap is needed.
"""

WE_ERROR_EOF_ONLY_IN_COMMENT: Final[int] = 989
"""ANOMALY A13: a code that exists only as a commented-out line.

[common/irspostingMT.cbl:L577] carries ``*> move 989 to WE-Error`` and 989 appears
nowhere else in the whole handler-and-bridge folder. Named here so the register
entry has a home; NEVER emitted, which is the point.
"""

HANDLER_BAD_FUNCTION: Final[int] = int(WeError.NOT_USED)
"""``999`` - the handler's bad-function code [common/acasirsub4.cbl:L439-L440]."""

BRIDGE_BAD_FUNCTION: Final[int] = int(WeError.UNKNOWN_UNEXPECTED)
"""``990`` - the bridge's bad-function code [common/irspostingMT.cbl:L924].

ANOMALY A17, first half: the two layers disagree on the SAME condition. Both set
``FS-Reply`` to 99 and both carry the comment ``*> Houston; We have a problem``,
but the handler reports 999 and the bridge 990. The disagreement is confirmed in
three handler/bridge pairs across the folder, so it is a pattern rather than a
slip. The handler's code is what a caller of this module observes, because the
handler is the module boundary; the bridge's is recorded and not emitted.
"""

HANDLER_START_PARAM_ERROR: Final[int] = int(WeError.FILE_KEY_NO_OUT_OF_RANGE)
"""``998`` - the handler's access-type rejection [common/acasirsub4.cbl:L362].

ANOMALY A17, second half. The handler sets 998 and, unlike every other error path,
LEAVES ``FS-Reply`` AT ZERO - there is no ``move 99 to fs-reply`` in that block
[common/acasirsub4.cbl:L361-L364]. Unreachable from this module (it is on the flat
path) and recorded for the traceability map.
"""

BRIDGE_START_PARAM_ERROR: Final[int] = int(WeError.ACCESS_TYPE_WRONG)
"""``997`` - the bridge's access-type rejection [common/irspostingMT.cbl:L601].

THIS ONE IS LIVE, and correcting the note that said otherwise is one of the five
corrections in the module docstring. The bridge repeats the handler's guard
[common/irspostingMT.cbl:L599] ``if access-type < 5 or > 8`` - written with
``or >`` rather than ``not >``, and rejecting 9 - then sets ``(99, 997)`` and
leaves. So an access type outside 5..8 never reaches a statement, and
:func:`start` enforces it with the BRIDGE's pair because the bridge is what runs.

The relation table nevertheless maps 9 to ``"<= "``
[common/irspostingMT.scb:L546], so that entry is unreachable - declared support
for a relation the guard forbids.
"""

FILE_KEY_NO_START_ERROR: Final[int] = int(WeError.FILE_KEY_NO_OUT_OF_RANGE)
"""``998`` - key-number guard for the indexed read and the start.

[common/acasirsub4.cbl:L166-L172]: ``fn-read-indexed`` and ``fn-start`` both
require ``File-Key-No`` of 1, and anything else yields ``(99, 998)``. The guard is
shared verbatim with ``acasirsub1`` and ``acas022``, comment included - "1 is only
for RDB as Cobol does it on primary key".
"""

FILE_KEY_NO_DELETE_ERROR: Final[int] = int(WeError.DELETE_KEY_OUT_OF_RANGE)
"""``996`` - the same guard for ``fn-delete`` [common/acasirsub4.cbl:L174-L178].

A DIFFERENT CODE FOR AN IDENTICAL CONDITION, which is why it is a separate
constant rather than a shared one.
"""

RECORD_SIZE_MISMATCH: Final[int] = int(WeError.RECORD_SIZE_MISMATCH)
"""``901`` - the record-size gate's failure [common/acasirsub4.cbl:L481-L482]."""


#  MODULE STATE  -  THE COBOL PROGRAM'S OWN WORKING STORAGE


_CONNECTION: Any = None
"""The open connection, held across calls.

FAITHFUL RATHER THAN CONVENIENT. A COBOL sub-program's ``WORKING-STORAGE``
survives between ``CALL``s unless the program is cancelled, and the bridge holds
its connection exactly this way: ``ba020-Process-Open`` connects
[common/irspostingMT.cbl:L312-L313] and ``ba030-Process-Close`` disconnects
[common/irspostingMT.cbl:L336], with every verb in between relying on the
connection still being there. Module state reproduces that lifetime exactly.

Rule R-3 forbids a connection pool, and there is none: exactly one connection,
opened once, used sequentially.
"""

_RECORD_SIZE_CHECKED: bool = False
"""The ``if A = zero`` latch [common/acasirsub4.cbl:L473].

``A`` and ``B`` are declared with the comment "A & B used in 1st test ONLY / in
ba-Process-RDBMS" [common/acasirsub4.cbl:L121-L122], so the size comparison runs
once per program activation and never again. The connection parameters are copied
inside the same latch [common/acasirsub4.cbl:L505-L510] and are therefore NEVER
REFRESHED once taken - reproduced by :func:`_record_size_gate`.
"""


#  `WS-MYSQL-EDIT`  -  THE BRIDGE'S ONE NUMERIC RENDERER


_EDIT_WIDTH: Final[int] = 30
"""``WS-MYSQL-EDIT PIC -Z(18)9.9(9)`` is thirty characters wide.

One sign, eighteen zero-suppressed digits, one mandatory digit, the point, then
nine decimal digits: 1 + 18 + 1 + 1 + 9 = 30. Confirmed by compiled measurement
of ``function length`` on the field.
"""

_EDIT_INTEGER_DIGITS: Final[int] = 19
"""Positions 2 through 20 - the ``Z(18)`` run plus the mandatory ``9``.

The trailing position is ``9`` and not ``Z``, so a value of zero renders ``"0"``
rather than blank. Measured: a zero key renders ``[0]``, not ``[]``.
"""

_EDIT_FRACTION_DIGITS: Final[int] = 9
"""Positions 22 through 30 - the ``9(9)`` run, never suppressed."""

_EDIT_POINT_POSITION: Final[int] = 21
"""The literal ``.`` separating the two runs."""

_MONEY_WINDOW: Final[tuple[int, int]] = (14, 7)
"""``WS-MYSQL-EDIT(14:07)`` [common/irspostingMT.cbl:L1101].

Seven positions - exactly the seven integer digits of ``S9(07)V9(02)``. THE SIGN
AT POSITION 1 IS OUTSIDE THIS WINDOW, which is the whole mechanism of the measured
sign loss described in the module docstring.
"""

_MONEY_FRACTION_WINDOW: Final[tuple[int, int]] = (22, 2)
"""``WS-MYSQL-EDIT(22:02)`` [common/irspostingMT.cbl:L1105].

Taken RAW, not trimmed - the bridge trims the integer window and then appends the
literal ``"."`` and these two characters untouched, so a value of zero yields
``"0.00"`` rather than ``"0."``.
"""

_WIDE_INTEGER_WINDOW: Final[tuple[int, int]] = (13, 8)
"""``WS-MYSQL-EDIT(13:08)`` [common/irspostingMT.cbl:L1041].

Eight positions for the ``9(08) COMP`` host variables - ``HV-KEY-4``,
``HV-POST4-DR`` and ``HV-POST4-CR``. ANOMALY A16: their copybook sources are
``pic 9(5)`` and their columns ``mediumint(5)``, so the width inflates 5 -> 8 -> 5.
No clamping is applied; the inflation is the bridge's own and is reproduced.
"""

_NARROW_INTEGER_WINDOW: Final[tuple[int, int]] = (18, 3)
"""``WS-MYSQL-EDIT(18:03)`` [common/irspostingMT.cbl:L1071].

Three positions for the ``9(03) COMP`` host variables - the three derived
components and ``HV-VAT-AC-DEF4``. ANOMALY A16 again: fed from two-character
substrings, or from ``pic 99``, into ``tinyint(2)`` columns, so 2 -> 3 -> 2.
"""

_EDIT_CONTEXT: Final[decimal.Context] = decimal.Context(
    prec=_EDIT_INTEGER_DIGITS + _EDIT_FRACTION_DIGITS + 2,
    rounding=decimal.ROUND_DOWN,
)
"""An exact-decimal context wide enough for the whole edit field.

Precision covers every digit position the field can hold, so no rendering can
lose a digit to the context. Rounding is toward zero because COBOL truncates on
store unless ``ROUNDED`` is written, and no ``ROUNDED`` appears anywhere in this
bridge - though nothing here should ever need to round, since every value arriving
has already been stored into its field by the record layer.
"""


def _mysql_edit(value: decimal.Decimal) -> str:
    """Render one value into the bridge's thirty-character edit field.

    Reproduces ``MOVE HV-xxx TO WS-MYSQL-EDIT`` for the picture ``-Z(18)9.9(9)``
    [common/irspostingMT.cbl:L1039-L1040]. The layout, one-based:

    ===========  ==========================================================
    Position     Content
    ===========  ==========================================================
    1            The sign - ``-`` when negative, otherwise a space. A FIXED
                 insertion character, so it never moves with the value.
    2 .. 20      Nineteen integer positions, right-aligned. Leading zeros
                 become spaces except at position 20, which is ``9``.
    21           The literal ``.``.
    22 .. 30     Nine decimal positions, zero-filled, never suppressed.
    ===========  ==========================================================

    Verified against the compiled program: ``-12345.67`` renders
    ``"-              12345.670000000"`` and ``-0.05`` renders
    ``"-                  0.050000000"``.

    Args:
        value: The host variable's value. Exact decimal throughout; no binary
            approximation is used at any point (rule R-2).

    Returns:
        The thirty-character field, ready for windowing.
    """
    with decimal.localcontext(_EDIT_CONTEXT):
        negative = value < 0
        magnitude = -value if negative else value
        # Split without division: scale by the fraction width, then take the
        # integral part. `scaleb` and `to_integral_value` are exact decimal
        # operations, so no binary approximation enters here.
        shifted = magnitude.scaleb(_EDIT_FRACTION_DIGITS).to_integral_value(
            rounding=decimal.ROUND_DOWN
        )
        all_digits = format(shifted, "f").rjust(
            _EDIT_INTEGER_DIGITS + _EDIT_FRACTION_DIGITS, "0"
        )

    integer_digits = all_digits[:-_EDIT_FRACTION_DIGITS]
    fraction_digits = all_digits[-_EDIT_FRACTION_DIGITS:]

    # `Z(18)` suppresses leading zeros to spaces; the final `9` at position 20
    # does not, which is why a zero value still renders a digit there.
    suppressible = integer_digits[:-1]
    mandatory = integer_digits[-1]
    stripped = suppressible.lstrip("0")
    suppressed = stripped.rjust(len(suppressible), " ")

    # The sign is written at position 1 and NOWHERE ELSE. Every window the bridge
    # reads starts at position 13 or later, so this character is unreachable from
    # all of them - the measured sign loss, reproduced structurally rather than by
    # a discard step that a later reader might mistake for a bug and "fix".
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

    Reproduces ``WS-MYSQL-EDIT(offset:length)``. COBOL offsets are one-based, so
    the offset is decremented once here rather than at each of the five call
    sites.
    """
    offset, length = window
    return edit[offset - 1 : offset - 1 + length]


def _integer_window(integer_digits: int) -> tuple[int, int]:
    """Derive the edit-field window for a host variable's integer width.

    The integer run is right-aligned and ends at position 20, so ``n`` integer
    digits occupy positions ``21 - n`` through 20. That single formula reproduces
    all three windows the bridge hard-codes, which is why the window is derived
    from the dictionary's declared digit count rather than transcribed per column:

    * 8 digits -> ``(13, 8)``  = ``WS-MYSQL-EDIT(13:08)``
    * 7 digits -> ``(14, 7)``  = ``WS-MYSQL-EDIT(14:07)``
    * 3 digits -> ``(18, 3)``  = ``WS-MYSQL-EDIT(18:03)``

    Validated against those three literals at import by
    :func:`_verify_edit_geometry`, so a dictionary that ever reported a different
    width fails loudly instead of silently shifting a window.
    """
    return (_EDIT_POINT_POSITION - integer_digits, integer_digits)


def _verify_edit_geometry() -> None:
    """Check the derived geometry against the field's frozen literals.

    Guards the one piece of arithmetic in this module that is not itself quoted
    from the source. A mismatch means either the picture clause or a windowing
    literal has been misread, and both would corrupt every value written.

    Raises:
        RuntimeError: If the rendered field is the wrong width, if the decimal
            point lands in the wrong place, or if a derived window disagrees with
            the literal the bridge writes.
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


#  CHARACTER HOST VARIABLES


def _fixed_char(value: str, length: int) -> str:
    """Hold a value in a fixed-width ``PIC X(n)`` display item.

    A COBOL character field is always exactly its declared width: a shorter value
    is padded with trailing spaces and a longer one is truncated on the right.
    Both are reproduced, because both change what reaches the column - the
    padding is what the bridge then trims, and the truncation is silent.
    """
    if len(value) >= length:
        return value[:length]
    return value.ljust(length)


def _render_character(value: str, length: int) -> str:
    """Render a character host variable as the bridge does.

    ``FUNCTION TRIM (HV-xxx,TRAILING)`` [common/irspostingMT.cbl:L1052-L1053] -
    TRAILING ONLY, so leading spaces are PRESERVED and reach the column while
    trailing padding does not. Trimming both ends would silently left-justify
    every value that arrived with a leading space.
    """
    return _fixed_char(value, length).rstrip(" ")


#  THE THREE GUARDED SUBSTRING RULES  -  ANOMALY A1 / REGISTER A-7


def _is_cobol_numeric(text: str) -> bool:
    """Reproduce COBOL's ``numeric`` class test on a display item.

    Every character must be a digit. MEASURED AGAINST THE COMPILED PROGRAM, which
    is the only way to settle the edge cases rule R-6 cares about: both ``" 7"``
    and ``"7 "`` test FALSE, so a space is not tolerated in any position - not as
    padding, not as a leading blank.

    ``str.isdigit`` is deliberately not used: it accepts superscripts and other
    non-ASCII digit forms that a COBOL display item cannot hold and that would
    then be sent to a numeric column. The membership test below admits exactly
    the ten ASCII digits.
    """
    return bool(text) and all(character in "0123456789" for character in text)


def _derive_date_components(post_date: str) -> tuple[int, int, int]:
    """Derive ``POST4-DAY``, ``POST4-MONTH`` and ``POST4-YEAR`` from the date text.

    THIS IS THE MODULE'S CENTREPIECE - the plan's proof that the bridge and not
    the copybook is authoritative. Reproduces
    [common/irspostingMT.cbl:L982-L987] exactly::

        if       Post-Date (1:2) numeric
                 move     Post-Date (1:2) to HV-POST4-DAY.
        if       Post-Date (4:2) numeric
                 move     Post-Date (4:2) to HV-POST4-MONTH.
        if       Post-Date (7:2) numeric
                 move     Post-Date (7:2) to HV-POST4-YEAR.

    THREE INDEPENDENT GUARDS, NOT ONE (anomaly A2). Each component stands or falls
    on its own two characters, so derivation is partial: ``"01/AB/23"`` gives
    ``(1, 0, 23)`` - measured against the compiled program - while ``POST4-DAT``
    still stores the raw text. Eight outcomes are reachable. The plan's register
    describes only the all-or-nothing case; the source is authoritative (rule R-6).

    A FAILED GUARD YIELDS ZERO, NOT AN ERROR AND NOT AN ABSENT VALUE. The move
    simply does not happen, leaving the host variable at the value ``initialize
    TD-IRSPOSTING-REC`` [common/irspostingMT.cbl:L966] gave it. The row is still
    written in full. That produces the internally inconsistent row the plan's
    register entry ``A-7`` names - raw text in one column, zero in another - and
    rule R-4 makes reproducing it mandatory. It is NOT reconciled, NOT repaired,
    and NOT reported.

    The maintainer expected this never to happen
    [common/irspostingMT.cbl:L978-L980] - "and yes they all should be numeric as a
    date is present / but JIC (just in case)" - so a firing guard leaves the row in
    a state its author did not anticipate. A debug record is emitted for the
    operator's benefit; it changes no value and no control flow.

    Positions 3 and 6 are never examined (anomaly A4), so any separator passes,
    and the year is two digits with no century (anomaly A4). The text is SLICED,
    never parsed: a date library would be more correct than the specification,
    which plan section 0.8.6 identifies as the one outcome to avoid.

    Args:
        post_date: ``Post-Date``, a ``pic x(8)`` display item
            [copybooks/irswspost.cob:L11]. Padded or truncated to eight
            characters here exactly as the fixed-width field would hold it, so a
            short value cannot raise on slicing.

    Returns:
        ``(day, month, year)`` as integers, each zero where its own guard failed.
        Never ``None``, and never a partial structure.
    """
    text = _fixed_char(post_date, POST_DATE_LENGTH)
    components: list[int] = []
    for column in DERIVED_COLUMNS:
        offset, length = DERIVED_COLUMN_SLICES[column]
        fragment = text[offset - 1 : offset - 1 + length]
        if _is_cobol_numeric(fragment):
            components.append(int(fragment))
            continue
        # The guard failed, so the `move` never runs and the host variable keeps
        # the zero that `initialize TD-IRSPOSTING-REC` left
        # [common/irspostingMT.cbl:L966]. Reproduced, not repaired - rule R-4.
        components.append(0)
        #  THE DATE TEXT ITSELF IS NOT LOGGED. `POST4-DAT` carries a posting's
        #  own date - business data, which the safe-event schema forbids in a record
        #  (CWE-532) - and the guard's failure is fully identified by the table and
        #  the column it left at zero. The raw text is still STORED, because the
        #  frozen bridge stores it, so the row is exactly as inconsistent as it is in
        #  the compiled program (anomaly 7, R-4).
        _LOG.debug(
            "%s: the guard on %s did not hold, so the column stays zero while "
            "POST4-DAT keeps the raw text - the maintainer expected this never "
            "to occur [common/irspostingMT.cbl:L978-L987]",
            TABLE,
            column,
        )
    day, month, year = components
    return day, month, year


#  `bb000-HV-Load`  -  THIRTEEN HOST VARIABLES, TEN THEN THREE


_COPYBOOK_LOAD_ORDER: Final[tuple[tuple[str, str], ...]] = (
    ("KEY-4", "post_key"),  # [common/irspostingMT.cbl:L967]
    ("POST4-CODE", "post_code"),  # [common/irspostingMT.cbl:L968]
    ("POST4-DAT", "post_date"),  # [common/irspostingMT.cbl:L969]
    ("POST4-DR", "post_dr"),  # [common/irspostingMT.cbl:L970]
    ("POST4-CR", "post_cr"),  # [common/irspostingMT.cbl:L971]
    ("POST4-AMOUNT", "post_amount"),  # [common/irspostingMT.cbl:L972]
    ("POST4-LEGEND", "post_legend"),  # [common/irspostingMT.cbl:L973]
    ("VAT-AC-DEF4", "vat_ac_def"),  # [common/irspostingMT.cbl:L974]
    ("POST4-VAT-SIDE", "post_vat_side"),  # [common/irspostingMT.cbl:L975]
    ("VAT-AMOUNT4", "vat_amount"),  # [common/irspostingMT.cbl:L976]
)
"""The ten copybook moves, IN COPYBOOK ORDER, not column order.

ANOMALY A5. These run first, in exactly this sequence
[common/irspostingMT.cbl:L967-L976], and the three derived columns follow AFTER
them [common/irspostingMT.cbl:L982-L987] even though they occupy ordinals 4, 5 and
6 of the row [mysql/ACASDB.sql:L278-L280]. The reason is in the maintainer's own
comment - "These added after new columns created 31/12/16"
[common/irspostingMT.cbl:L978] - they were bolted on to an existing paragraph.
Load order and column order are therefore different orders, and both are preserved
where each belongs.

The pairing also encodes anomaly A27: the column names on the left come from the
FD view [common/acasirsub4.cbl:L101-L112] while the record attributes on the right
carry the linkage names [copybooks/irswspost.cob:L9-L18]. ``KEY-4`` from
``post_key``, ``VAT-AC-DEF4`` from ``vat_ac_def`` - the two views disagree on
almost every name, and this table is where they are reconciled.
"""


def _render_value(column: str, value: Any) -> str:
    """Render one host variable exactly as the bridge's statement builder does.

    Dispatches on the DICTIONARY's declared metadata rather than on the Python
    type, so the storage class comes from the authoritative triple and not from a
    guess about the value in hand (rule R-5). Character fields are trimmed
    trailing; numeric fields go through the edit field and its window.

    Every value ends up a string, because the bridge wraps every one of them -
    numerics included - in double quotes. That is what makes anomaly A15 real: the
    numeric key is compared as a quoted string.
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
        # [common/irspostingMT.cbl:L1101-L1105]. The fraction is not trimmed, so a
        # whole value renders "n.00" rather than "n.".
        return (
            _window(edit, _integer_window(integer_digits)).strip()
            + "."
            + _window(edit, _MONEY_FRACTION_WINDOW)
        )
    return _window(edit, _integer_window(integer_digits)).strip()


def _load_host_variables(posting: PostingRecord) -> Mapping[str, str]:
    """``bb000-HV-Load`` [common/irspostingMT.cbl:L958-L987].

    Produces all THIRTEEN host variables as the rendered strings the bridge sends.

    THE ORDER IS THE SOURCE'S ORDER: the group is initialised, then the ten
    copybook fields are moved in copybook order, then the three derived components
    are moved last (anomaly A5).

    ``initialize TD-IRSPOSTING-REC`` [common/irspostingMT.cbl:L966] is reproduced
    by seeding every entry before any move runs. This is the statement that makes
    the whole not-null schema possible, and plan section 0.6.2 states the
    consequence: "unset fields become zero or space rather than SQL NULL. This is
    why every column in the schema can be declared NOT NULL and why the Python
    layer must default rather than omit." No entry is ever absent and no entry is
    ever null.

    Args:
        posting: The caller's ``Posting-Record``. Read only; the database path
            never mutates it, unlike the flat write's key retry
            [common/acasirsub4.cbl:L410] which is out of scope.

    Returns:
        Thirteen rendered values keyed by column name, ready to bind in schema
        order.
    """
    # `initialize TD-IRSPOSTING-REC.` - every host variable gets its group's
    # initial value BEFORE any move [common/irspostingMT.cbl:L966]. A numeric
    # becomes zero and a character becomes space, which is exactly what a failed
    # date guard then leaves in place.
    loaded: dict[str, str] = {}
    for column in COLUMNS:
        host_variable = _ENTRY_BY_COLUMN[column].bridge_host_variable
        if host_variable.character_length is not None:
            loaded[column] = _render_character(
                "", host_variable.character_length
            )
        else:
            loaded[column] = _render_value(column, decimal.Decimal(0))

    # The ten copybook moves, in copybook order.
    for column, attribute in _COPYBOOK_LOAD_ORDER:
        loaded[column] = _render_value(column, getattr(posting, attribute))

    # The three derived moves, LAST - after every copybook field, though their
    # columns sit at ordinals 4, 5 and 6 [common/irspostingMT.cbl:L982-L987].
    day, month, year = _derive_date_components(posting.post_date)
    loaded["POST4-DAY"] = _render_value("POST4-DAY", day)
    loaded["POST4-MONTH"] = _render_value("POST4-MONTH", month)
    loaded["POST4-YEAR"] = _render_value("POST4-YEAR", year)

    return MappingProxyType(loaded)


#  `bb100-UnloadHVs`  -  TEN MOVES FOR THIRTEEN COLUMNS


def _unload_host_variables(row: Mapping[str, Any]) -> PostingRecord:
    """``bb100-UnloadHVs`` [common/irspostingMT.cbl:L995-L1015].

    TEN MOVES FOR THIRTEEN COLUMNS - the asymmetry is anomaly A3 and it is
    deliberate. ``POST4-DAY``, ``POST4-MONTH`` and ``POST4-YEAR`` are read from the
    row and DISCARDED, because ``Posting-Record`` has no field able to receive
    them: they exist in the bridge and the table only. The maintainer states why
    [common/irspostingMT.cbl:L1017-L1018]:

        "We do not need to unload POST4- DAY, MONTH or YEAR as only used in select
        statements instead of a sort."

    So they are write-only columns with a documented purpose - the only such entry
    in the folder's inventory that carries one. Adding them to the record would
    invent a field the frozen layout does not have, which rule R-3 forbids.

    ``initialize Posting-Record`` [common/irspostingMT.cbl:L1004] is reproduced by
    constructing a fresh record from defaults, so a column absent from the row
    leaves its field at the layout's initial value rather than raising. The
    bridge's own note on why nulls never arrive
    [common/irspostingMT.cbl:L1002-L1003]: "NULL fields must not be returned in the
    buffer. SQL filters each column to ensure it has a proper value. This saves
    using indicator variables."

    Args:
        row: One fetched row keyed by column name. The driver's pinned converter
            already delivers exact decimals and integers, never binary
            approximations (rule R-2).

    Returns:
        The ten copybook fields as a record. The three derived columns are read
        and dropped.
    """
    # `initialize Posting-Record.` - defaults first, so any column the row does
    # not carry stays at the layout's own initial value.
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


#  STATUS REMAPPING  -  THIS BRIDGE'S CODES, NOT `glpostingMT`'S


def _bridge_status(outcome: CursorOutcome) -> tuple[int, int]:
    """Translate a cursor outcome into ``irspostingMT``'s own status pair.

    THE ISAM POSITIONING IS SHARED; THE STATUS CODES ARE NOT. ``cursor_state``
    reproduces ``glpostingMT`` - cursor positioning, the stored-result snapshot,
    one row per call, and sticky end of file - and all of that is common to every
    bridge in the family, including this one, whose ``ba041-Reread`` carries the
    same sticky-EOF retest [common/irspostingMT.cbl:L479-L483]. But the We-Error
    values are per-bridge, and the two disagree:

    ======================  =====================  =====================
    Condition               ``glpostingMT``        ``irspostingMT``
    ======================  =====================  =====================
    End of file             ``(10, 10)``           ``(10, 3)``
    Key not found           ``(21, untouched)``    ``(21, 2)``
    ======================  =====================  =====================

    ``glpostingMT`` writes ``move 10 to fs-Reply WE-Error`` and leaves it; this
    bridge overwrites the 10 with 3 [common/irspostingMT.cbl:L405-L406] and writes
    a 2 where the other writes nothing [common/irspostingMT.cbl:L533-L534]. So the
    pair is remapped here, in the module that owns this bridge, rather than by
    changing shared machinery that is correct for its own bridge. Anomaly A12.

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

    One place for the ``move n to FS-Reply`` / ``move n to WE-Error`` pattern that
    the frozen source writes at more than thirty sites, so a caller reads as the
    paragraph it reproduces rather than as four assignments.

    ``write_status=False`` REPRODUCES THE PATHS THAT WRITE NO STATUS AT ALL, and
    those paths are real rather than defensive. Two of this bridge's exits log and
    leave both status fields exactly as the caller passed them:

    * the sticky end-of-file discard, which sets the cursor inactive and moves
      ``"EOF3"`` into the log tag with no status move anywhere in the block
      [common/irspostingMT.cbl:L479-L483];
    * the START that matched zero rows with no client error, which skips the
      ``move 21``/``move 2`` guarded by the errno test and falls straight through
      to the log and the read [common/irspostingMT.cbl:L675-L686], [:L698-L702].

    On those paths the trace number and the log tag are still written, because the
    frozen source writes the logging fields before it tests status. Only the pair
    is withheld.

    Returns:
        The pair now in force - the one just written, or the caller's own where
        the frozen path writes none, so a verb can both record and return in one
        statement.
    """
    if write_status:
        file_access.fs_reply = fs_reply
        file_access.we_error = we_error
    if trace is not None:
        file_access.logging_data.ws_no_paragraph = trace
    if file_key is not None:
        # `WS-File-Key` is `pic x(64)` [copybooks/wsfnctn.cob:L52] and is a LOG
        # TAG only - it never reaches a column.
        file_access.logging_data.ws_file_key = _fixed_char(file_key, 64)
    return int(file_access.fs_reply), int(file_access.we_error)


def _clear_sql_fields(file_access: FileAccess) -> None:
    """``move spaces to SQL-Err SQL-Msg SQL-State`` [common/acasirsub4.cbl:L216].

    The handler clears the three diagnostic fields on entry to its flat dispatch,
    and the bridge clears them again in ``ba010-Initialise``
    [common/irspostingMT.cbl:L236-L246]. Reproduced once, at the point the handler
    does it, so a stale diagnostic from a previous call cannot be mistaken for this
    one's.
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
    """Map a driver failure through the shared ``Mysql-1100-DB-Error`` translation.

    The frozen copybook's error paragraph writes ``SQL-Err``, ``SQL-Msg`` and
    ``SQL-State`` from the client library and then sets a status, and the bridge
    tests ``SQL-Err`` and ``SQL-State`` afterwards to tell a duplicate key from
    anything else [common/irspostingMT.cbl:L723-L728]. ``mysql_1100_db_error``
    owns that translation for every handler; the per-operation We-Error override
    supplies this bridge's 995 for a delete and 994 for a rewrite
    [common/irspostingMT.cbl:L779-L780], [common/irspostingMT.cbl:L906-L907].
    """
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


#  SQL TEXT  -  EVERY IDENTIFIER QUOTED, EVERY VALUE BOUND


_QUOTED_TABLE: Final[str] = quote_identifier(TABLE)
_QUOTED_KEY: Final[str] = quote_identifier(PRIMARY_KEY)
"""Pre-quoted identifiers.

MANDATORY, NOT STYLISTIC. Every identifier in this table contains a hyphen -
``IRSPOSTING-REC``, ``KEY-4``, ``POST4-CODE``, ``VAT-AC-DEF4`` - so unquoted they
are parsed as subtraction and the statement is a syntax error. ``KEY-4`` and
``VAT-AC-DEF4`` additionally read as arithmetic on a bare word. The bridge
backtick-quotes for the same reason [common/irspostingMT.cbl:L1032], and
``execute_statement`` requires identifiers to arrive already quoted because it
binds values and never interpolates them.
"""


def _assignment_clause() -> str:
    """Build the ``SET`` list naming all thirteen columns in schema order.

    The bridge uses MySQL's ``INSERT ... SET`` form
    [common/irspostingMT.cbl:L1033] rather than a column list with a values list,
    and its update names the same thirteen in the same order
    [common/irspostingMT.cbl:L1211]. The statement SHAPE is a driver-level detail
    expressed idiomatically here; THE COLUMN ORDER IS NOT, because the state diff
    is sensitive to it, so it is taken from :data:`COLUMNS` which is itself derived
    from the frozen table.
    """
    return ", ".join(f"{quote_identifier(column)} = %s" for column in COLUMNS)


def _ordered_parameters(loaded: Mapping[str, str]) -> tuple[str, ...]:
    """Order the loaded host variables to match :func:`_assignment_clause`.

    All thirteen, always, in schema order. Never a subset and never a null - the
    initialised group [common/irspostingMT.cbl:L966] guarantees a value for every
    one, which is what lets the frozen table declare them all not-null with no
    default.
    """
    return tuple(loaded[column] for column in COLUMNS)


def _key_predicate() -> str:
    """The equality predicate on the key of reference.

    ``'`' KeyName '`' '="' <record buffer substring> '"'`` - the construction the
    bridge assembles at [common/irspostingMT.cbl:L501-L510]. The key of reference
    is looked up rather than assumed, so the offset and length come from the
    frozen metadata [common/irspostingMT.scb:L124-L126] by way of the shared key
    table.
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

    THIS IS NOT THE SAME RENDERING THE ``SET`` LIST USES, and the difference is
    easy to miss. A predicate takes ``Posting-Record (K:L) delimited by size``
    [common/irspostingMT.cbl:L505] - five raw characters lifted straight out of the
    record buffer, with no trimming and no edit field - whereas the assignment list
    passes the same key through ``WS-MYSQL-EDIT`` and trims it
    [common/irspostingMT.cbl:L1039-L1043]. So the key 123 appears as ``"00123"`` in
    a ``WHERE`` clause and as ``"123"`` in a ``SET`` clause. The maintainer left the
    alternative in place, commented out, immediately below the substring
    [common/irspostingMT.cbl:L506] - ``*> Post-Key`` - so the choice was
    deliberate.

    ``Post-Key`` is ``pic 9(5)`` display [copybooks/irswspost.cob:L9], which is
    right-justified and zero-filled, and a value too wide for the field loses its
    high-order digits rather than raising.

    ANOMALY A15 lands here: the five characters are wrapped in double quotes and
    compared against ``mediumint(5) unsigned`` [mysql/ACASDB.sql:L275], so the
    comparison succeeds only because the server coerces a string to a number. The
    value is BOUND as a parameter rather than interpolated, which preserves the
    comparison the bridge makes without assembling SQL from text.
    """
    digits = str(int(posting.post_key)).rjust(KEY_LENGTH, "0")
    # `pic 9(5)` truncates on the LEFT when the value is too wide, keeping the
    # low-order digits - the same silent narrowing the flat write's key increment
    # relies on when it wraps past 99999 [common/acasirsub4.cbl:L410].
    return digits[-KEY_LENGTH:]


#  `ba012-Test-WS-Rec-Size-2`  -  THE ONCE-ONLY LATCH


_FD_RECORD_LENGTH: Final[int] = 5 + 2 + 8 + 5 + 5 + 9 + 32 + 2 + 2 + 9
"""``function length ( Record-4 )`` [common/acasirsub4.cbl:L477].

Summed from the inline FD declaration [common/acasirsub4.cbl:L101-L112], field by
field in its own order: ``Key-4`` group holding ``Key-Number pic 9(5)`` is 5,
``Post4-Code`` 2, ``Post4-Date`` 8, ``Post4-DR`` 5, ``Post4-CR`` 5,
``Post4-Amount`` 9, ``Post4-Legend`` 32, ``Vat-AC-Def4`` 2, ``Post4-Vat-Side`` 2,
``Vat-Amount4`` 9.

The two money items are ``pic s9(7)v99 sign is leading`` with NO ``separate
character`` clause, so the sign is overpunched onto the leading digit and the item
occupies nine bytes rather than ten - confirmed by compiled measurement of
``function length`` on the linkage field.

The linkage layout [copybooks/irswspost.cob:L9-L18] sums to the same total, which
is why the gate passes on frozen data. It is still evaluated, because a divergence
is precisely what the gate exists to catch.
"""


def _record_size_gate(
    system: SystemRecord, file_access: FileAccess
) -> tuple[int, int] | None:
    """``ba012-Test-WS-Rec-Size-2`` [common/acasirsub4.cbl:L471-L511].

    Compares the linkage record's length against the FD record's and refuses to
    proceed if the linkage record is the shorter, then captures the connection
    parameters. Both happen INSIDE ``if A = zero``
    [common/acasirsub4.cbl:L473], so both happen once per activation and never
    again - the parameters are captured once and NEVER REFRESHED.

    The comparison is ``if A < B`` where ``A`` is ``function Length (
    Posting-Record )`` and ``B`` is ``function length ( Record-4 )``
    [common/acasirsub4.cbl:L474-L479] - note the capital and lower-case spellings of
    the same intrinsic on adjacent lines, a copy-paste shared with two sibling
    handlers. Here the two layouts agree at :data:`_FD_RECORD_LENGTH` characters, so
    the gate passes; it is implemented rather than assumed because a divergence is
    exactly what it exists to catch, and its comment explains the asymmetry - "allow
    for last field ( FILLER) not being present in layout"
    [common/acasirsub4.cbl:L482].

    On failure the handler sets ``(99, 901)``, displays ``IR902`` with the record
    length and ``IR901``, waits for a keystroke, and then ``go to ba-rdbms-exit``
    [common/acasirsub4.cbl:L480-L499] - SO THE BRIDGE IS NEVER CALLED. The screen
    dialogue is dropped as presentation and THE CONTROL TRANSFER IS KEPT, which is
    the rule plan section 0.3.4 sets for an accept that guards a write.

    Args:
        system: Supplies the six connection parameters, taken in the handler's own
            order - schema, user, password, port, host, socket
            [common/acasirsub4.cbl:L505-L510]. That order differs from the
            copybook's declaration order [copybooks/wsfnctn.cob:L57-L62] and from
            the bridge's own [common/irspostingMT.cbl:L289-L311]; three orders for
            one set of fields, and none of them matters to the result.
        file_access: Receives the status pair on failure.

    Returns:
        ``None`` when the gate passes, or the ``(99, 901)`` pair when it does not,
        in which case the caller must return immediately without touching the
        database.
    """
    global _RECORD_SIZE_CHECKED
    if _RECORD_SIZE_CHECKED:
        return None

    # `move function Length ( Posting-Record ) to A` [common/acasirsub4.cbl:L474],
    # summed from the linkage layout's own field widths. A `sign is leading` item
    # has no separate sign byte, so its width is its digit count.
    linkage_length = sum(
        entry.copybook.character_length or entry.copybook.digits or 0
        for entry in _ENTRIES
        if entry.copybook is not None
    )
    if linkage_length < _FD_RECORD_LENGTH:
        # `if A < B  move 901 to WE-Error  move 99 to fs-reply`
        # [common/acasirsub4.cbl:L480-L482], then IR902/IR901 and
        # `go to ba-rdbms-exit` [common/acasirsub4.cbl:L498] - THE BRIDGE IS NEVER
        # CALLED. The dialogue is dropped; the control transfer is kept.
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
    # [common/acasirsub4.cbl:L505-L510]. The shared extractor performs exactly
    # these six moves in exactly this order, so it is reused rather than repeated
    # - one owner for the record shape. CAPTURED ONCE, NEVER REFRESHED, because the
    # whole block sits inside `if A = zero` [common/acasirsub4.cbl:L473].
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


#  THE VERBS


def open_(
    system: SystemRecord,
    file_access: FileAccess,
    *,
    access_type: int = int(AccessType.INPUT),
) -> tuple[int, int]:
    """``fn-open`` - ``ba020-Process-Open`` [common/irspostingMT.cbl:L283-L325].

    The bridge builds six null-terminated connection strings from ``RDB-Data`` and
    then performs ``MYSQL-1000-OPEN THRU MYSQL-1090-EXIT``
    [common/irspostingMT.cbl:L312-L313] - a ``PERFORM ... THRU`` pair, and one of
    the seven in the whole in-scope set, so it becomes an explicit two-call
    composition here per plan section 0.4.2 rule 3 rather than a pattern-matched
    single call. On a non-zero reply it leaves at once
    [common/irspostingMT.cbl:L314-L315]; otherwise it tags the log and clears the
    cursor flag [common/irspostingMT.cbl:L322-L323].

    THE ACCESS TYPE DOES NOT REACH THE DATABASE. Input, i-o and output all resolve
    to the same connect; only ``fn-extend`` is refused, and only on the flat path
    [common/acasirsub4.cbl:L270-L271]. Output additionally triggers the delete-all
    coercion, which :func:`dispatch` handles before reaching here.

    Args:
        system: Source of the connection parameters.
        file_access: Receives the status pair, the trace number and the log tag.
        access_type: Recorded for the log and for the caller's own inspection; it
            selects no different behaviour here, exactly as the bridge selects
            none.

    Returns:
        The ``(FS-Reply, We-Error)`` pair.
    """
    global _CONNECTION

    gate = _record_size_gate(system, file_access)
    if gate is not None:
        return gate

    if _CONNECTION is not None:
        # The bridge reconnects unconditionally, so an open on an already-open
        # connection replaces it. Closing first keeps exactly one connection,
        # which is what rule R-3's no-pool constraint requires.
        mysql_1999_exit()
        mysql_1980_close(_CONNECTION)
        _CONNECTION = None

    # `PERFORM MYSQL-1000-OPEN THRU MYSQL-1090-EXIT` - the two paragraphs of the
    # THRU range, called explicitly and in order.
    outcome = mysql_1000_open(
        system, ws_no_paragraph=BRIDGE_TRACE[int(FileFunction.OPEN)]
    )
    outcome = mysql_1090_exit(outcome)

    logging_data = file_access.logging_data
    logging_data.sql_err = outcome.sql_err
    logging_data.sql_msg = outcome.sql_msg
    logging_data.sql_state = outcome.sql_state

    if outcome.fs_reply != FsReply.SUCCESS or outcome.connection is None:
        # `if fs-reply not = zero  go to ba999-end`
        # [common/irspostingMT.cbl:L314-L315].
        return _store(
            file_access,
            int(outcome.fs_reply),
            int(outcome.we_error),
            trace=BRIDGE_TRACE[int(FileFunction.OPEN)],
        )

    _CONNECTION = outcome.connection
    # `move zero to Most-Cursor-Set` [common/irspostingMT.cbl:L323] - a fresh
    # connection has no cursor position.
    _cursor_reset(TABLE)
    # `move "OPEN IRSPOSTING" to WS-File-Key` [common/irspostingMT.cbl:L322].
    return _store(
        file_access,
        int(FsReply.SUCCESS),
        int(WeError.SUCCESS),
        trace=BRIDGE_TRACE[int(FileFunction.OPEN)],
        file_key="OPEN IRSPOSTING",
    )


def open_input(system: SystemRecord, file_access: FileAccess) -> tuple[int, int]:
    """``fn-open`` with ``fn-input`` - published by the facade at
    [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L261]."""
    return open_(system, file_access, access_type=int(AccessType.INPUT))


def open_extend(system: SystemRecord, file_access: FileAccess) -> tuple[int, int]:
    """``fn-open`` with ``fn-extend``.

    The flat path refuses this outright with ``(99, 997)``
    [common/acasirsub4.cbl:L270-L271], the copybook noting extend is "not valid for
    ISAM" [copybooks/wsfnctn.cob:L109]. THE DATABASE PATH DOES NOT REFUSE IT: the
    branch to the bridge [common/acasirsub4.cbl:L196-L200] is taken long before
    ``aa020`` runs, so extend resolves to an ordinary connect. Reproduced as the
    source behaves and not as the flat path suggests, and unreachable through the
    facade in any case, which publishes no extend verb for this handler.
    """
    return open_(system, file_access, access_type=int(AccessType.EXTEND))


def close(file_access: FileAccess) -> tuple[int, int]:
    """``fn-close`` - ``ba030-Process-Close`` [common/irspostingMT.cbl:L327-L340].

    Frees an active cursor first [common/irspostingMT.cbl:L328-L329], tags the log,
    then performs ``MYSQL-1980-CLOSE THRU MYSQL-1999-EXIT``
    [common/irspostingMT.cbl:L336] - the second ``PERFORM ... THRU`` pair, again an
    explicit composition.

    The handler's own close carries a dated commented-out status clear
    [common/acasirsub4.cbl:L287] - ``*> 27/07/16 16:30 move zeros to FS-Reply
    WE-Error.`` - which the sibling ``acasirsub3`` also carries, doubly commented
    where this one is singly. It is commented out, so NO STATUS IS CLEARED HERE and
    the caller's pair survives the close.
    """
    global _CONNECTION

    # `if Cursor-Active perform ba998-Free` [common/irspostingMT.cbl:L328-L329].
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

    The bridge assumes a connection is present in every verb but ``ba020`` - there
    is no re-open and no test. Calling a verb before the open is therefore outside
    the frozen source's behaviour, so rather than invent a status this reports the
    shared ``911`` init error [copybooks/wsfnctn.cob] that
    ``Mysql-1100-DB-Error`` already owns for a failed connection, and says so in
    the log.
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
    statement executed on its behalf. Its protocol asks for exactly "a DB-API cursor
    from ``connection.py``", which is what this yields.

    DELIBERATELY NOT ``execute_statement``. That function executes a statement in
    order to yield its cursor, so borrowing it here would issue a probe query the
    frozen bridge never issues - and rule R-6 makes the exact sequence of statements
    part of behaviour, with the scenario state diff sensitive to it. This module
    therefore uses two paths for two different jobs: ``execute_statement`` for every
    statement it issues itself, and this for handing a cursor to the component that
    issues its own.

    A SESSION ANOTHER BRIDGE HAS CLOSED DOES NOT RAISE HERE. Anomaly A-8 means
    any bridge's ``Mysql-1980-Close`` closes the one process handle
    [presql2-package/cobmysqlapi38.c:L230-L234]; the frozen bridge reports that
    from its ``call "MySQL_query"`` [copybooks/mysql-procedures.cpy:L165-L166],
    so ``acquire_cursor`` carries the failure to the ``execute`` that
    ``cursor_state`` issues rather than raising out of this generator.

    The cursor is closed on every path, including when the caller raises.
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

    [common/irspostingMT.cbl:L342-L488]. Self-positions when no cursor is active,
    stores the whole result, then delivers ONE ROW PER CALL from that snapshot -
    issuing no further statement, exactly as the bridge fetches from a stored
    result. The positioning relation and low key are the frozen ones for this table,
    ``>=`` from ``"00000"``, carried as data by the shared key metadata; the
    bridge's own comment records that the nominal bridge uses plain ``>`` instead.

    THE READ IS UNFILTERED (anomaly A24). ``aa041-Reread``
    [common/acasirsub4.cbl:L312-L321] has no loop-back and no predicate, so every
    row is delivered. Its near-twin ``acasirsub1`` filters at
    [common/acasirsub1.cbl:L414-L415] and silently drops every sub-nominal row - two
    handlers sharing a common ancestor, one filtering and one not. No filter is
    added here; copy-paste lineage is not behavioural equivalence.

    On exhaustion the pair is ``(10, 3)`` and the log tag is ``"EOF"``
    [common/acasirsub4.cbl:L314-L319] - see :data:`END_OF_FILE` for why the 10 the
    source first writes into ``We-Error`` is dead.

    ANOMALY A14, and it cuts the other way from the working note. The HANDLER clears
    only ``We-Error`` after a successful read [common/acasirsub4.cbl:L325] where its
    twin clears both. But that line is on the FLAT path, which this module never
    reaches; the BRIDGE clears BOTH [common/irspostingMT.cbl:L487]. The bridge's
    behaviour is what runs, so both are cleared, and the handler's divergence is
    recorded here rather than implemented.

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
            # `move "EOF" to WS-File-Key` for logging
            # [common/acasirsub4.cbl:L319]; `initialize Posting-Record`
            # [common/acasirsub4.cbl:L318] leaves the caller's record cleared.
            #
            # THE STICKY-EOF DISCARD WRITES NO STATUS. When the caller's own
            # `FS-Reply` still holds 10 from an earlier end of file, this bridge
            # fetches the row, throws it away, sets the cursor inactive and moves
            # `"EOF3"` into the log tag - and that block contains NO status move,
            # so We-Error keeps whatever the caller was carrying
            # [common/irspostingMT.cbl:L479-L483]. Writing the 3 here would
            # clobber a value the compiled bridge preserves, so the pair is
            # withheld exactly where the source withholds it.
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
        # `move zero to fs-reply WE-Error` - the BRIDGE clears both
        # [common/irspostingMT.cbl:L487].
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

    [common/irspostingMT.cbl:L490-L590]. One equality select on the key of
    reference, then one fetch. Every exit frees the cursor
    [common/irspostingMT.cbl:L585-L590], so AN INDEXED READ TAKEN MID-WALK DESTROYS
    THE WALK'S POSITION - a caller interleaving this with :func:`read_next` must
    re-position, and that is the frozen behaviour rather than an implementation
    limit.

    Not found is ``(21, 2)``; see :data:`NOT_FOUND`. The code is 21 and never 23,
    even though a distinct not-found reply exists.

    THE HANDLER'S COUNTERPART CARRIES TWO PIECES OF RESIDUE, both preserved as
    evidence rather than tidied away (anomaly A8). Its comment
    [common/acasirsub4.cbl:L333-L334] reads "if retrieve record by key set up for
    Owning or Sub-Nominal pointer record" - NOMINAL-LEDGER semantics, in the posting
    handler, describing a pointer chain this table does not have and has no field
    for. And ``aa051-Reread`` [common/acasirsub4.cbl:L338] is a label NOTHING
    BRANCHES TO, left behind when the pointer chase was removed; its own comment
    "in case of goto Reread" [common/acasirsub4.cbl:L339] describes a jump that no
    longer exists. Both are copy-paste inheritance from ``acasirsub1``, and both are
    exactly the sort of trace the traceability and ambiguity documents need
    recorded.

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
            # [common/irspostingMT.cbl:L533-L534]. Every exit of this paragraph
            # writes its status, so the flag is honoured for symmetry with the
            # other two read verbs rather than because this path withholds it.
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

    START DOES NOT MERELY POSITION - IT RETURNS A RECORD (anomaly A11). The
    paragraph ends ``perform ba999-end`` and then ``go to ba041-Reread``
    [common/irspostingMT.cbl:L698-L702], and the handler does the same with
    ``perform aa999-main-exit.`` followed by ``go to aa041-Reread.``
    [common/acasirsub4.cbl:L400-L401]. So one invocation both positions the cursor
    and delivers the first matching row. This is a Class 4 transfer under plan
    section 0.4.2 - a sibling re-dispatch whose target performs work and then
    transfers control itself - and it is the one class needing per-site proof, so
    the equivalence is stated: the ``perform`` runs the exit paragraph's logging and
    returns, and the ``go to`` then enters the read paragraph, which is exactly a
    call to the logging step followed by a call to :func:`read_next`. Nothing between
    the two labels is skipped, because ``aa999-main-exit`` is the last paragraph
    before ``aa041`` in the flow and its own body ends by returning.

    THE ACCESS-TYPE GUARD IS LIVE HERE, which corrects the note that called it
    flat-file-only. The bridge repeats it [common/irspostingMT.cbl:L599-L601]::

        if       access-type < 5 or > 8   *> not using not < or not >
                 move 99 to FS-Reply
                 move 997 to WE-Error

    Written as ``< 5 or > 8`` rather than with negated comparisons, and REJECTING 9
    - so ``fn-not-greater-than`` cannot be used even though the relation table maps
    it to ``"<= "`` [common/irspostingMT.scb:L546]. That mapping is unreachable.
    The pair is the BRIDGE's ``(99, 997)``, not the handler's ``(99, 998)``; see
    :data:`BRIDGE_START_PARAM_ERROR` and :data:`HANDLER_START_PARAM_ERROR`.

    The relation for a valid access type is trimmed of its padding before it reaches
    the predicate - ``"=  "`` becomes ``=`` and ``">= "`` becomes ``>=`` - because
    the bridge strings it ``delimited by space``.

    Args:
        posting: Supplies the key to position on.
        file_access: Receives the status pair.
        access_type: 5 through 8 - equal to, less than, greater than, not less than.
            The handler tests them in the order 5, 8, 7, 6
            [common/acasirsub4.cbl:L368-L397], annotating the last "Not used in
            irsub4"; the order affects nothing since the tests are exclusive.

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
            # writes NO STATUS AT ALL. The `move 21` / `move 2` pair sits INSIDE
            # the errno test [common/irspostingMT.cbl:L679-L686], so when errno is
            # `"0  "` that guarded block is skipped entirely; and the `move zero to
            # FS-Reply WE-Error` at [:L688] belongs to the rows-NOT-zero `else`, so
            # it is skipped too. Control reaches `perform ba999-end` and then
            # `go to ba041-Reread` [:L698-L702] with the caller's pair exactly as
            # it arrived. Falling into the read is therefore mandatory rather than
            # optional - it is the READ that goes on to report the end of file.
            _store(
                file_access,
                int(file_access.fs_reply),
                int(file_access.we_error),
                trace=BRIDGE_TRACE[int(FileFunction.START)],
                write_status=False,
            )
        elif outcome.fs_reply != FsReply.SUCCESS:
            # `move 21 to fs-reply` then `move 2 to we-error`, guarded by the errno
            # test, then `go to ba999-End` [common/irspostingMT.cbl:L683-L685] -
            # the ONLY exit of this paragraph that does not fall into the read.
            fs_reply, we_error = _bridge_status(outcome)
            _store(
                file_access,
                fs_reply,
                we_error,
                trace=BRIDGE_TRACE[int(FileFunction.START)],
            )
            return fs_reply, None
        else:
            # Rows found: `set Cursor-Active to true` [:L671-L673] then `move zero
            # to FS-Reply WE-Error` and the descriptive tag the bridge strings from
            # the relation, the key and the row count
            # [common/irspostingMT.cbl:L688-L696].
            _store(
                file_access,
                int(FsReply.SUCCESS),
                int(WeError.SUCCESS),
                trace=BRIDGE_TRACE[int(FileFunction.START)],
                file_key=outcome.file_key or "",
            )

    # `go to aa041-Reread` / `go to ba041-Reread` - the Class 4 transfer, made an
    # explicit call. The start's own status has already been written above where the
    # source writes one, exactly as `perform aa999-main-exit` logs before the
    # transfer [common/acasirsub4.cbl:L400-L401].
    return read_next(file_access)


def write(posting: PostingRecord, file_access: FileAccess) -> tuple[int, int]:
    """``fn-write`` - ``ba070-Process-Write`` + ``bb200-Insert``.

    [common/irspostingMT.cbl:L707-L732] and [common/irspostingMT.cbl:L1023-L1196].
    Loads all thirteen host variables [common/irspostingMT.cbl:L708] and issues one
    insert naming all thirteen columns in schema order.

    THIS IS WHERE THE THREE BRIDGE-ONLY COLUMNS ARE POPULATED, and the only place
    they are ever written - see :func:`_derive_date_components` and
    :func:`_load_host_variables`. Anomaly A1, register entry ``A-7``.

    The bridge uses MySQL's ``INSERT ... SET`` form
    [common/irspostingMT.cbl:L1033]. The statement's SHAPE is a driver-level detail
    expressed idiomatically; the COLUMN ORDER is not, and it is taken from
    :data:`COLUMNS`.

    DUPLICATE KEY IS ``(22, 0)`` AND We-Error IS LEFT ALONE. The bridge tests the
    driver's error number and SQL state and moves 22 into ``FS-Reply`` only
    [common/irspostingMT.cbl:L723-L726]; there is no ``move`` to ``We-Error`` on
    either branch, so a caller's previous value survives a failed insert. Any other
    failure is ``(99, 0)`` [common/irspostingMT.cbl:L728] - again with ``We-Error``
    untouched.

    NO KEY-INCREMENT RETRY. The flat write retries a duplicate by incrementing the
    key and re-entering its own paragraph [common/acasirsub4.cbl:L409-L411], but that
    path is out of scope and the database path has no equivalent - a duplicate simply
    returns 22. Worth stating because the flat retry has two properties a reader
    might expect to find reproduced and must not: it MUTATES THE CALLER'S RECORD, and
    it advances only because ``move Posting-Record to Record-4``
    [common/acasirsub4.cbl:L405] reloads the record at the top of every pass. The
    note that called it a non-terminating loop was wrong on that second point; see
    the module docstring's corrections.

    Returns:
        The ``(FS-Reply, We-Error)`` pair.
    """
    connection = _require_connection(file_access)
    if connection is None:
        return int(file_access.fs_reply), int(file_access.we_error)

    # `perform bb000-HV-Load` [common/irspostingMT.cbl:L708].
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
        # `move 22 to FS-Reply` for a duplicate, else 99 - and in BOTH cases
        # We-Error is left exactly as the caller had it
        # [common/irspostingMT.cbl:L723-L728].
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
    Reloads all thirteen host variables [common/irspostingMT.cbl:L873] - SO THE
    THREE DERIVED COLUMNS ARE RE-DERIVED ON EVERY REWRITE, from whatever the record's
    date text holds at that moment - then updates all thirteen columns with a key
    predicate.

    A ZERO-ROW UPDATE SETS NO STATUS AT ALL (anomaly A10). The update has no
    ``invalid key`` equivalent: the status moves sit inside the driver-error test,
    so when the statement succeeds but matches nothing, neither ``FS-Reply`` nor
    ``We-Error`` is written and the caller's incoming pair survives untouched
    [common/irspostingMT.cbl:L898-L919]. The flat handler agrees - its ``rewrite``
    carries no ``invalid key`` clause either [common/acasirsub4.cbl:L434]. No status
    is invented for the missing row.

    On a driver failure the pair is ``(99, 994)``
    [common/irspostingMT.cbl:L906-L907], supplied by the shared per-operation
    override rather than written here, so the one mapping serves every handler.

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

    # `move zero to FS-Reply WE-Error SQL-Err` / `move spaces to SQL-Msg`
    # [common/irspostingMT.cbl:L915-L917].
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

    A ZERO-ROW DELETE SETS NO STATUS (anomaly A10), for exactly the reason the
    rewrite does: the status moves sit inside the driver-error test, so a statement
    that succeeds and matches nothing leaves both fields alone
    [common/irspostingMT.cbl:L771-L788]. The flat handler's ``delete`` likewise has
    no ``invalid key`` clause [common/acasirsub4.cbl:L424].

    ITS COMMENT DESCRIBES BEHAVIOUR THAT DOES NOT EXIST (anomaly A9). The handler
    writes ``*> Delete record and pointer if neccessary``
    [common/acasirsub4.cbl:L422] above a body containing exactly ONE delete and no
    pointer concept at all. The twin ``acasirsub1`` carries the same comment above a
    genuinely two-delete body [common/acasirsub1.cbl:L613], which is where this one
    came from - more nominal-ledger residue in a posting handler, misspelling
    included. Preserved as evidence, not corrected.

    On a driver failure the pair is ``(99, 995)``
    [common/irspostingMT.cbl:L779-L780], again from the shared override.

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

    [common/irspostingMT.cbl:L790-L869], which the bridge itself flags
    ``*> THIS IS NON STANDARD`` at its paragraph head.

    IT IS BOUNDED, NOT A WHOLE-TABLE WIPE, and this corrects the note that described
    it as an unqualified delete. The paragraph first increments the key
    [common/irspostingMT.cbl:L812] - ``add 1 to Post-Key.`` with the comment "as its
    the last posting" - then builds a ``<`` predicate on the key of reference
    [common/irspostingMT.cbl:L818-L828] and deletes with it
    [common/irspostingMT.cbl:L845-L848]. So it removes every row BELOW the
    incremented key and leaves anything at or above it, and its log text says as much
    [common/irspostingMT.cbl:L830] - "Deleting back from". A whole-table statement
    would destroy rows this one preserves.

    IT MUTATES THE CALLER'S RECORD. The increment is applied to ``Post-Key`` in the
    linkage record, which is passed by reference, so the caller's key is one higher
    after the call. Reproduced, because the caller can observe it.

    The bounded form is a plain delete, which rule R-3 permits. It is emphatically
    NOT the whole-table removal statement, and substituting one would change both the
    rows affected and the reported row count.

    REACHABLE ONLY BY COERCION. No handler dispatches function code 6 -
    ``acasirsub4`` sends it to bad-function with the comment ``*> 6 is unused``
    [common/acasirsub4.cbl:L234] - yet the bridge dispatches it
    [common/irspostingMT.cbl:L271-L272] under the comment "option 6 is a special to
    cleardown all data". The route in is ``ba015-Test-Ends``
    [common/acasirsub4.cbl:L518-L522], which sets the function code AFTER the open
    has already been performed. So delete-all is reachable, but only by that
    coercion - the precise statement, which supersedes the earlier working note that
    called the code entirely undispatched (anomaly A18).

    The row count is reported through ``WS-Count-Rows``
    [copybooks/wsfnctn.cob:L55], the field the copybook annotates as being "used in
    Delete-All".

    Returns:
        The ``(FS-Reply, We-Error)`` pair.
    """
    connection = _require_connection(file_access)
    if connection is None:
        return int(file_access.fs_reply), int(file_access.we_error)

    # `add 1 to Post-Key.` [common/irspostingMT.cbl:L812] - ON THE CALLER'S RECORD.
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

    # `move WS-MYSQL-Count-Rows to WS-Count-Rows` - the count the copybook reserves
    # for exactly this verb [copybooks/wsfnctn.cob:L55].
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

    ``ba015-Test-Ends`` [common/acasirsub4.cbl:L513-L522]::

        if       fn-Open
           and   fn-Output
                 perform ba020-Process-Dal
                 set fn-Delete-All to true
        end-if.

    and then FALLS THROUGH into ``ba020-Process-DAL``
    [common/acasirsub4.cbl:L531]. So the bridge is called TWICE: once with the
    function still open/output, which connects, and once more with the function now
    6, which clears the data down. Anomaly A19.

    THIS HANDLER IS THE ORIGIN OF THE PATTERN. ``acasirsub1`` credits it explicitly -
    "TAKEN from acasirsub4 22/12/16" [common/acasirsub1.cbl:L247] - and copies it
    verbatim including the ``*> [ Backup code ]`` note and the lower-case
    ``Process-Dal`` spelling. Four distinct open-output behaviours exist across the
    seventeen handlers; this two-call fall-through is one of them, ``acas008``
    coerces with a single call instead, ``acas005`` has the block commented out
    entirely, and seven handlers have no such block at all.

    A DEAD BLOCK SITS EARLIER IN THE SAME FILE. [common/acasirsub4.cbl:L185-L192]
    looks like the coercion but has BOTH of its coercion lines commented out
    [common/acasirsub4.cbl:L188-L189], so it performs the database call and leaves
    without ever setting the function code. Since this handler is the original, that
    commented-out state is original too and not a later regression. The live coercion
    is the one above.

    ANOMALY A20: that earlier block also BYPASSES ``move RDBMS-Flat-Statuses to
    FA-RDBMS-Flat-Statuses``, which the general database branch performs
    [common/acasirsub4.cbl:L197]. The bypass is reproduced - the flat-status copy is
    deliberately not made on this path.

    Args:
        system: For the connect.
        posting: For the delete-all bound, whose key this call increments.
        file_access: Receives the status pair.

    Returns:
        The pair from the second call, the delete-all, since it runs last.
    """
    # FIRST CALL - function still fn-Open / fn-Output. `perform ba020-Process-Dal`
    # [common/acasirsub4.cbl:L520].
    fs_reply, we_error = open_(
        system, file_access, access_type=int(AccessType.OUTPUT)
    )
    if fs_reply != FsReply.SUCCESS:
        # The frozen code performs the second call unconditionally, but with no
        # connection there is nothing for it to act on; the failed pair from the
        # connect is what a caller sees either way.
        return fs_reply, we_error

    # ANOMALY A20: `move RDBMS-Flat-Statuses to FA-RDBMS-Flat-Statuses`
    # [common/acasirsub4.cbl:L197] is NOT performed on this path. Left undone
    # deliberately - see the docstring.

    # `set fn-Delete-All to true` [common/acasirsub4.cbl:L521], then FALL THROUGH
    # into `ba020-Process-DAL` [common/acasirsub4.cbl:L531] - the SECOND call.
    file_access.file_function = int(FileFunction.DELETE_ALL)
    return delete_all(posting, file_access)


#  `dispatch`  -  THE HANDLER'S PROCEDURE DIVISION


def _key_number_guard(file_access: FileAccess) -> tuple[int, int] | None:
    """``evaluate File-Function`` key guard [common/acasirsub4.cbl:L165-L179].

    Three function codes require ``File-Key-No`` of 1, and two different We-Error
    values are used for the identical condition::

        when  4 / when  9   ->  998   [common/acasirsub4.cbl:L169]
        when  8             ->  996   [common/acasirsub4.cbl:L175]

    Both set ``FS-Reply`` to 99 and leave immediately. The guard is shared verbatim
    with ``acasirsub1`` and ``acas022``, comment included - "1 is only for RDB as
    Cobol does it on primary key" [common/acasirsub4.cbl:L174] - and this table has
    exactly one key of reference [common/irspostingMT.scb:L129], so any other key
    number is meaningless rather than merely unsupported.

    Callers arriving through the IRS facade always pass, because that convention sets
    the key number to 1 before every call
    [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L71].

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
    # Every other function ignores the key number entirely - the `evaluate` has no
    # `when other` [common/acasirsub4.cbl:L179].
    return None


def dispatch(
    system: SystemRecord,
    posting: PostingRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> tuple[int, int]:
    """``acasirsub4``'s procedure division [common/acasirsub4.cbl:L145-L235].

    THE PARAMETER ORDER IS THE FROZEN LINKAGE ORDER, so a reviewer can diff this
    signature against the source line for line::

        Procedure Division Using System-Record       [common/acasirsub4.cbl:L145]
                                 Posting-Record      [:L147]
                                 File-Access         [:L149]
                                 File-Defs           [:L150]
                                 ACAS-DAL-Common-data [:L151]

    The facade calls with exactly this order
    [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L69-L75].

    The sequence reproduced, in the source's own order:

    1. Set the log identity - system 1 for IRS [common/acasirsub4.cbl:L160] and file
       number 13 [common/acasirsub4.cbl:L161], the latter then raised to 23 on this
       path [common/acasirsub4.cbl:L469].
    2. Apply the key-number guard [common/acasirsub4.cbl:L165-L179].
    3. Handle open/output through its two-call coercion, bypassing the flat-status
       copy [common/acasirsub4.cbl:L185-L192].
    4. Clear the three diagnostic fields [common/acasirsub4.cbl:L216].
    5. Dispatch on the function code [common/acasirsub4.cbl:L218-L235].

    EIGHT CODES ARE DISPATCHED - 1, 2, 3, 4, 5, 7, 8 and 9. Code 6 goes to
    bad-function under the comment ``*> 6 is unused``
    [common/acasirsub4.cbl:L234], EVEN THOUGH THE BRIDGE IMPLEMENTS IT
    [common/irspostingMT.cbl:L271-L272]; the only route to delete-all is the
    coercion in step 3. Anything else is bad-function too, giving ``(99, 999)``
    [common/acasirsub4.cbl:L439-L440] - note the bridge would say 990 for the same
    condition [common/irspostingMT.cbl:L924], and the handler's code is what a caller
    of this module sees because the handler is the boundary.

    NO RECOVERY IS PERFORMED, and that is deliberate rather than an omission. The IRS
    facade wraps most handlers in a per-handler error check that can return from the
    program outright, but THERE IS NONE FOR ``acasirsub4`` - the checks exist only for
    five other handlers [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L320-L348]. The
    handler contributes no module-specific message either, declaring a ``*> Module
    Specific`` heading above nothing [common/acasirsub4.cbl:L129-L131], so the facade
    has none to display (anomaly A26). The source states the contract directly
    [common/acasirsub4.cbl:L538] - "Any errors leave it to caller to recover from".
    This matters: ``irs030`` abandons its run on a posting-write failure while still
    committing partial state [irs/irs030.cbl:L1673-L1678], so the pair returned here
    decides which rows survive.

    Args:
        system: ``SYSTEM-REC``, supplying the connection parameters.
        posting: ``Posting-Record``, both input and output. Named without a ``Ws``
            prefix because the handler copies the copybook with no ``replacing``
            clause [common/acasirsub4.cbl:L135] and so does the bridge
            [common/irspostingMT.cbl:L201] - an exact handler/bridge record-name
            agreement, one of only two clean pairs in the folder.
        file_access: Carries the function code, the access type, the key number and
            the returned status. Mutated, as the frozen linkage is.
        file_defs: The file-name block. Accepted because the frozen linkage accepts
            it; UNUSED ON THIS PATH, since a table name comes from the bridge's own
            directive [common/irspostingMT.scb:L167] and not from a file name. Kept
            so the signature matches and a caller need not know which handlers read
            it.
        dal_common: The testing-flag block [common/acasirsub4.cbl:L143]. Its
            ``Testing-1`` switch gates the logging call
            [common/acasirsub4.cbl:L446], which is a deliberate omission here - the
            logging program is out of scope, so this becomes a Python log record.

    Returns:
        The ``(FS-Reply, We-Error)`` pair, exactly as the frozen handler leaves them
        in ``File-Access``.
    """
    # `move 1 to WS-Log-System` / `move 13 to WS-Log-File-No`
    # [common/acasirsub4.cbl:L160-L161].
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
        # [copybooks/wsfnctn.cob:L88-L118], not business data.
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

    # `move 23 to WS-Log-File-no` [common/acasirsub4.cbl:L469] - the database path
    # raises the file number, the flat path does not.
    logging_data.ws_log_file_no = WS_LOG_FILE_NO_RDB

    # Step 3 - open/output, whose coercion must be handled before the ordinary
    # dispatch because it changes the function code
    # [common/acasirsub4.cbl:L185-L192], [common/acasirsub4.cbl:L518-L522].
    if function == int(FileFunction.OPEN) and access_type == int(
        AccessType.OUTPUT
    ):
        _clear_sql_fields(file_access)
        return open_output(system, posting, file_access)

    # Step 4 - `move spaces to SQL-Err SQL-Msg SQL-State`
    # [common/acasirsub4.cbl:L216]. `move zero to WE-Error`
    # [common/acasirsub4.cbl:L214] is paired with a COMMENTED-OUT clear of
    # `FS-Reply` [common/acasirsub4.cbl:L215] - `*>  ?  FS-Reply.` - so only
    # We-Error is cleared here, and the caller's FS-Reply survives into the verb.
    file_access.we_error = int(WeError.SUCCESS)
    _clear_sql_fields(file_access)

    # Step 5 - the dispatch. Codes in the source's own `when` order
    # [common/acasirsub4.cbl:L218-L235].
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
    passed by reference. The verbs return a fresh record so they can be used and
    tested without a caller's block, and this copies it across for the dispatch path
    that has one - the same value in the same field, by the same mechanism the frozen
    ``move`` uses.
    """
    for _column, attribute in _COPYBOOK_LOAD_ORDER:
        setattr(target, attribute, getattr(source, attribute))


# --- traceability -------------------------------------------------------------
#
# Rule R-5 requires every paragraph to map to a function and every field to a
# dictionary entry. The field mapping is mechanical - `loader.entries_for_table`
# drives `COLUMNS`, `_render_value` and both host-variable functions, so no field
# metadata is transcribed by eye. The paragraph mapping is below, with each `GO TO`
# annotated by its class from plan section 0.4.2.
#
# HANDLER  common/acasirsub4.cbl  (553 lines, Procedure Division L145)
# ---------------------------------------------------------------------------
# L145-L151  Procedure Division Using ...........  dispatch()  [order preserved]
# L160-L161  log identity .......................  dispatch(), step 1
# L165-L179  evaluate File-Function key guard ...  _key_number_guard()
# L185-L192  open/output block (coercion lines
#            commented out - anomaly A19) .......  open_output() docstring only
# L196-L200  branch to the database path ........  dispatch(), implicit - this
#                                                  module IS that branch
# L204       perform ba012 (flat) ...............  omitted: flat-file path
# L208-L212  dual-write banner (anomaly A32) ....  omitted: recorded in docstring
# L214-L216  clear We-Error / SQL fields .........  dispatch(), step 4
# L218-L235  evaluate File-Function dispatch .....  dispatch(), step 5
#            `go to aa0NN-...` x8 ................ CLASS 3 (section exit) -> the
#                                                  `return` of each branch
# L240       unreachable `go to aa100` ...........  omitted: dead code
# L242-L280  aa020-Process-Open ..................  open_() / open_input() /
#                                                  open_extend()
# L282-L293  aa030-Process-Close .................  close()
#            L287 dated commented-out clear ......  NOT implemented - it is
#                                                  commented out (anomaly A31)
# L295-L310  aa040 Cobol-File-Eof block ..........  omitted: flat-file path;
#                                                  carries the live `stop`
#                                                  (anomaly A23)
# L312-L321  aa041-Reread ........................  read_next()
#            `go to aa999-main-exit` at end ....... CLASS 2 (forward terminator)
#                                                  -> `return` with the EOF pair
#                                                  and the post-loop log tag
# L322-L325  transfer + clear (anomaly A14) .......  read_next(); the BRIDGE's
#                                                  both-fields clear wins
# L328-L334  aa050 pointer-record residue ..........  read_indexed() docstring
#                                                  (anomaly A8)
# L338-L339  aa051-Reread - NOTHING BRANCHES HERE .  read_indexed() docstring;
#                                                  vestigial (anomaly A8)
# L340-L348  aa050 keyed read ....................  read_indexed()
#            `go to aa999-main-exit` .............. CLASS 3 -> `return`
# L350-L359  aa060 preamble, sets Key-Number ......  start(); corrects the claim
#                                                  that it never does (A22)
# L361-L364  access-type guard (handler's 998) ....  start() uses the BRIDGE's 997
#                                                  (anomaly A17, A21 corrected)
# L368-L397  four relation branches, order 5/8/7/6  start(), via the shared
#                                                  relation table
# L400-L401  `perform aa999-main-exit.` then
#            `go to aa041-Reread.` ................ CLASS 4 (sibling re-dispatch)
#                                                  -> _store(...) then an explicit
#                                                  read_next() call. Equivalence
#                                                  proved in start()'s docstring:
#                                                  the performed paragraph logs and
#                                                  returns, and nothing lies
#                                                  between it and aa041.
#                                                  (anomaly A11)
# L403-L413  aa070-Process-Write .................  write(); L405 DOES load the FD
#                                                  record, so the claimed A7 is
#                                                  withdrawn
#            L409-L411 `go to aa070-...` .......... CLASS 1 (loop-back) ->
#                                                  omitted: flat-file path
#                                                  (anomaly A6, refined)
# L415-L425  aa080-Process-Delete ................  delete(); L422 pointer comment
#                                                  is residue (anomaly A9); no
#                                                  `invalid key` clause (A10)
# L427-L435  aa090-Process-Rewrite ...............  rewrite(); no `invalid key`
#                                                  clause either (anomaly A10)
# L437-L442  aa100-Bad-Function -> (99, 999) .....  dispatch(), final branch
# L444-L447  aa999-main-exit .....................  _store(); the logging call it
#                                                  gates is a deliberate omission
# L455-L469  ba-Process-RDBMS / ba010 ............  dispatch(); the 13 -> 23 bump
# L471-L511  ba012-Test-WS-Rec-Size-2 ............  _record_size_gate()
#            L484-L499 IR902/IR901 dialogue ....... presentation dropped, the
#                                                  `go to ba-rdbms-exit` KEPT
#            L505-L510 connection parameters ...... _record_size_gate(), once only
# L513-L522  ba015-Test-Ends (the coercion) .......  open_output()
# L531-L536  ba020-Process-DAL ...................  the verb calls themselves
# L540-L541  ba-rdbms-exit .......................  the `return` of each verb
# L544-L548  Ca-Process-Logs .....................  omitted: the logging program is
#                                                  out of scope (rule R-1); becomes
#                                                  a Python log record
#
# BRIDGE  common/irspostingMT.cbl  (1389 lines, Procedure Division L221)
# ---------------------------------------------------------------------------
# L123-L133  Table-Of-Keynames ...................  KEY_OFFSET / KEY_LENGTH /
#                                                  KEY_METADATA_TYPE, and the
#                                                  shared key table
# L139-L143  DAL-Data (one cursor) ...............  KEY_COUNT; CursorSlot.PRIMARY
# L172-L186  TD-IRSPOSTING-REC, 13 host variables   COLUMNS + _render_value()
# L221-L223  PROCEDURE DIVISION USING ............  the verb signatures
# L226       accept ws-env-lines from lines ......  omitted: presentation
# L236-L247  ba010-Initialise ....................  _clear_sql_fields()
# L257-L281  dispatch, NINE codes including 6 ....  dispatch() docstring; code 6
#                                                  reachable only by coercion (A18)
# L283-L325  ba020-Process-Open ..................  open_()
#            L312-L313 PERFORM MYSQL-1000-OPEN
#            THRU MYSQL-1090-EXIT ................. explicit two-call composition
#                                                  (plan 0.4.2 rule 3)
# L318-L321  commented-out credential block ......  NOT carried into Python; the
#                                                  frozen comment holds a plaintext
#                                                  password and no credential is
#                                                  reproduced anywhere here
# L327-L340  ba030-Process-Close .................  close(); MYSQL-1980-CLOSE THRU
#                                                  MYSQL-1999-EXIT, again explicit
# L342-L418  ba040-Process-Read-Next .............  read_next(), via the shared
#                                                  positioning machinery
# L420-L488  ba041-Reread ........................  read_next(); L487 clears BOTH
#                                                  status fields (anomaly A14)
# L490-L590  ba050-Process-Read-Indexed ..........  read_indexed()
# L592-L703  ba060-Process-Start .................  start()
#            L599-L601 access-type guard (997) ....  start(), LIVE (anomaly A21
#                                                  corrected)
#            L702 `go to ba041-Reread` ............ CLASS 4 -> explicit read_next()
# L707-L732  ba070-Process-Write .................  write()
# L734-L788  ba080-Process-Delete ................  delete()
# L790-L869  ba085-Process-Delete-ALL ............  delete_all(); BOUNDED by a
#            (`*> THIS IS NON STANDARD`)             `<` predicate, not a whole-table
#                                                  statement (anomaly A18 corrected)
# L871-L919  ba090-Process-Rewrite ...............  rewrite()
# L921-L923  ba092/ba093-Finish ..................  the `return` of each verb
# L924       ba100-Bad-Function -> (99, 990) .....  BRIDGE_BAD_FUNCTION; the
#                                                  handler's 999 is what callers see
#                                                  (anomaly A17)
# L936       ba998-Free ..........................  the positioning machinery's own
#                                                  cursor release
# L948-L955  ba999-end / ba999-exit ..............  the `return` of each verb
# L958-L987  bb000-HV-Load .......................  _load_host_variables()
#            L966 initialize the HV group ......... the seeding loop - the statement
#                                                  that makes every column not-null
#            L967-L976 ten copybook moves ......... _COPYBOOK_LOAD_ORDER
#            L982-L987 THREE GUARDED MOVES ........ _derive_date_components()
#                                                  (anomalies A1/A2/A4/A5, A-7)
# L995-L1018 bb100-UnloadHVs .....................  _unload_host_variables()
#            L1006-L1015 TEN moves for 13 columns . the derived three are read and
#                                                  discarded (anomaly A3)
# L1023-L1196 bb200-Insert .......................  write()
# L1200-L1374 bb300-Update .......................  rewrite()
#
# DELIBERATE OMISSIONS, restated for the migration record: the entire flat-file
# path and with it anomalies A6, A7 (withdrawn), A22 (withdrawn) and A23; the
# dual-write semantics (A32); `Key-Number` (A28); all screen presentation; the
# terminal-height probe; and the logging program call. Anomaly A13's We-Error 989
# exists only as a commented-out line in the frozen bridge and is NEVER emitted.
# ------------------------------------------------------------------------------
