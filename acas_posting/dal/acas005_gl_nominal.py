"""``acas005`` and its bridge ``nominalMT`` - the ``GLLEDGER-REC`` nominal ledger.

WHAT THIS MODULE OWNS
=====================
One data-access module per HANDLER, not per table (Agent Action Plan 0.3.1).
This one collapses two COBOL programs into one Python module:

===================================  ==========================================
`common/acas005.cbl`                 the numbered file handler: linkage, log
                                     identity, the key guard, the function
                                     dispatch and the hand-off to the bridge
`common/nominalMT.cbl`               the generated bridge: the host-variable
                                     group, the load/unload pair and every SQL
                                     statement issued against the table
===================================  ==========================================

The spine it serves, from Agent Action Plan 0.2.1.1::

    entity GL-Nominal -> handler acas005 -> bridge nominalMT
      -> table GLLEDGER-REC  [mysql/ACASDB.sql:L122-L135]   11 columns, PK LEDGER-KEY
      -> copybook copybooks/wsledger.cob
      -> record class WsLedgerRecord in acas_posting/records/gl_ledger.py

It owns no business logic. Every accounting decision belongs to the program
modules; this module moves records between :class:`WsLedgerRecord` and the
frozen table and reports the ``(FS-Reply, We-Error)`` pair the compiled system
would have left in the caller's ``File-Access`` block.

THE HEADLINE RISK  -  THIS IS THE SEQUENTIALLY-READ TABLE
=========================================================
Verbatim from Agent Action Plan 0.6.4:

    **The sort feeds a sequential read.** ``gl072`` locates the nominal-ledger
    account for each posting with a sequential read-next rather than an indexed
    read ``[general/gl072.cbl:L410-L412]``. It finds the correct account only
    because ``gl071`` has already emitted the transaction stream in nominal-key
    order. Any change in sort stability or key composition produces **silent
    misposting** - no error, no diagnostic, wrong balances.

The plan's citation is off: in the frozen program the sequential read is the
guarded ``if read-ledger not = "R" / perform GL-Nominal-Read-Next`` at
``[general/gl072.cbl:L407-L408]``; ``[general/gl072.cbl:L410-L412]`` is the
``move zero to tot-dr tot-cr`` that follows it. The sort-order dependency the
finding draws from it is unaffected and is reproduced.

So ``READ NEXT`` here advances in ``LEDGER-KEY`` ASCENDING order and in no
other, driven by :mod:`acas_posting.dal.cursor_state`, which reproduces the
bridge's own ``ORDER BY`` [common/nominalMT.cbl:L466-L472]. There is no
``LIMIT``, no ordering improvised from another column, and no set or dict
iteration anywhere near the statement text. Agent Action Plan 0.8.4 forbids the
obvious optimisation by name: "the migration must not 'optimise' the sequential
nominal read into an indexed one, even though that would obviously be faster
... Any performance work is therefore out of scope by construction, not merely
unrequested."

THE TWO LINKAGE SHAPES, BOTH PUBLISHED
======================================
Rule R-5 asks that a reviewer be able to diff argument lists against the frozen
source, so both levels of the COBOL call chain are published with their own
parameter order rather than one being folded into the other.

The handler, five parameters [common/acas005.cbl:L268-L275]::

    Procedure Division Using System-Record
                             WS-Ledger-Record
                             File-Access
                             File-Defs
                             ACAS-DAL-Common-data.

    call "acas005" using System-Record WS-Ledger-Record File-Access
                         File-Defs ACAS-DAL-Common-data
 -> dispatch(system, ledger, file_access, file_defs, dal_common)

The bridge, THREE parameters with ``File-Access`` FIRST
[common/acas005.cbl:L663-L666]::

    call     "nominalMT" using File-Access
                               ACAS-DAL-Common-data
                               WS-Ledger-Record
 -> nominal_mt(file_access, dal_common, ledger)

The caller is [copybooks/Proc-ACAS-FH-Calls.cob:L35-L41], whose dispatch
paragraph does ``move 1 to File-Key-No`` before the ``CALL``; ``acas005`` is the
CANONICAL five-parameter handler shape that the remaining sixteen vary from.

THE EIGHT VERBS AND THE DISPATCH ORDER
======================================
``1,2,3,4,5,7,8,9`` - re-write (7) is dispatched BEFORE delete (8), in both the
handler [common/acas005.cbl:L341-L360] and the bridge
[common/nominalMT.cbl:L370-L389]. The order is preserved because R-6 makes
statement order part of the specification::

    1 open   2 close   3 read-next   4 read-indexed
    5 write  7 re-write  8 delete    9 start

There is NO ``when 6`` (``fn-Delete-All``) and no arm for 13, 15 or 31..34, so
every one of those reaches ``aa100-Bad-Function`` and returns ``(99, 999)``.
``aa100`` is reached BOTH by ``when other`` [L358-L359] AND by the unconditional
fall-through the maintainer left after the ``evaluate`` [L362-L363]::

    *>  Should never get here but in case :(
    go       to aa100-Bad-Function.

THE FIELD MAP AND ITS DRIFT
===========================
Taken from ``loader.entries_for_table("GLLEDGER-REC")`` in COLUMN-ORDINAL order
and never re-derived from a picture clause - Agent Action Plan 0.8.1 makes that
a directive: "Data dictionary first. ... every Python field definition cites its
entry. This ordering is a directive, not a preference - it is what prevents
fields being transcribed by eye."

===  ==================  =====================  =========================  ====================  =======================================
Ord  Column              Copybook               Bridge host variable       MySQL column          Drift
===  ==================  =====================  =========================  ====================  =======================================
1    ``LEDGER-KEY``      ``WS-Ledger-Key9``     ``9(10) COMP``    [:L295]  ``int(8) unsigned``   8 -> **10** -> 8 digits; HV WIDER THAN
                         ``9(8)`` DISPLAY,                                                      BOTH ENDS; DISPLAY -> COMP -> INT; the
                         a REDEFINES view                                                       name differs in all three views; loaded
                         [wsledger:L21-L22]                                                     from the REDEFINITION, never the group
2    ``LEDGER-TYPE``     ``Ledger-Type`` ``9``  ``9(03) COMP``    [:L296]  ``tinyint(1) uns.``   1 -> **3** -> 1 digit; DISPLAY -> COMP
3    ``LEDGER-PLACE``    ``Ledger-Place`` ``x`` ``X(1)``          [:L297]  ``char(1)``           clean in every aspect
4    ``LEDGER-LEVEL``    ``Ledger-Level`` ``9`` ``9(03) COMP``    [:L298]  ``tinyint(1) uns.``   1 -> **3** -> 1 digit; DISPLAY -> COMP
5    ``LEDGER-NAME``     ``Ledger-Name``        ``X(32)``         [:L299]  ``char(32)``          **24 -> 32 -> 32.  ANOMALY A-12.**
                         ``x(24)``  [:L27]
6    ``LEDGER-BALANCE``  ``Ledger-Balance``     ``S9(08)V9(02)``  [:L300]  ``decimal(10,2)``     signed at all three layers, so the
                         ``s9(8)v99 comp-3``    ``COMP``                                        DECLARED value is clean; usage changes
7    ``LEDGER-LAST``     ``Ledger-Last``        ``S9(08)V9(02)``  [:L301]  ``decimal(10,2)``     packed -> binary at the bridge. BUT SEE
8    ``LEDGER-Q1``       ``Ledger-Q1``          ``S9(08)V9(02)``  [:L302]  ``decimal(10,2)``     ANOMALY N-SIGNLOSS BELOW: the sign is
9    ``LEDGER-Q2``       ``Ledger-Q2``          ``S9(08)V9(02)``  [:L303]  ``decimal(10,2)``     lost in TRANSPORT even though it
10   ``LEDGER-Q3``       ``Ledger-Q3``          ``S9(08)V9(02)``  [:L304]  ``decimal(10,2)``     survives every DECLARATION.
11   ``LEDGER-Q4``       ``Ledger-Q4``          ``S9(08)V9(02)``  [:L305]  ``decimal(10,2)``
===  ==================  =====================  =========================  ====================  =======================================

DELIBERATE OMISSIONS  -  55 FILLER BYTES AND THREE VIEWS THE BRIDGE DROPS
=========================================================================
Rule R-5: "Deliberate omissions are recorded as omissions." These copybook
items have NO host variable and NO column, so this module emits nothing for
them, and that is correct rather than incomplete:

* ``Ledger-n`` ``pic 9(4)`` and ``Ledger-s`` ``pic 9(2)``
  [copybooks/wsledger.cob:L17-L18] - a redefinition of ``WS-Ledger-Nos``, so
  the same six bytes the key already carries.
* ``Ledger-PC`` ``pic 9(2)`` [copybooks/wsledger.cob:L20] - inside the key
  group; reaches the table only through the ``WS-Ledger-Key9`` redefinition,
  as its low-order two digits.
* ``filler pic x(5)`` [copybooks/wsledger.cob:L26] - 5 bytes.
* ``filler pic x(50)`` [copybooks/wsledger.cob:L37] - 50 bytes.
* ``Ledger-Q pic s9(8)v99 comp-3 occurs 4``
  [copybooks/wsledger.cob:L35-L36] - a redefinition of ``Quarters``, the same
  storage as ``Ledger-Q1``..``Q4``, correctly NOT duplicated as four more
  columns.

That is 55 filler bytes the bridge silently drops out of a record the copybook
header calls 126 bytes [copybooks/wsledger.cob:L10].

ANOMALY REGISTER  -  ALL REPRODUCED, NONE FIXED
===============================================
Rule R-4, from Agent Action Plan 0.8.2: "There is no test suite: compiled COBOL
execution is the behavioral specification, defects included. A defect
reproduced is correct; a defect fixed is a failure." Agent Action Plan 0.7.4
C-4 additionally requires a comment at each reproduction site citing the COBOL
locator, and every entry below also belongs in ``docs/migration/anomaly-log.md``
naming THIS module as the reproducing module.

A-12  LEDGER-NAME WIDTH DRIFT 24 -> 32 -> 32.
      [copybooks/wsledger.cob:L27] ``x(24)``, [common/nominalMT.cbl:L299]
      ``X(32)``, [mysql/ACASDB.sql:L127] ``char(32)``. Agent Action Plan 0.6.2:
      "The value is not corrupted, but the padding differs, and padding is
      visible in a table dump." Reproduced in BOTH directions -
      :func:`bb000_hv_load` pads 24 -> 32, :func:`bb100_unload_hvs` truncates
      32 -> 24. The copybook width is not widened and the value is not
      right-stripped on the way in.

N-SIGNLOSS  EVERY NEGATIVE MONEY VALUE IS STORED AS ITS ABSOLUTE VALUE.
      Discovered here and settled against the compiled oracle, which rule R-6
      makes the tie-breaker. ``WS-MYSQL-EDIT`` is ``PIC -Z(18)9.9(9)``
      [common/nominalMT.cbl:L232] - thirty characters with the SIGN AT POSITION
      ONE. The bridge builds each money literal from
      ``TRIM(WS-MYSQL-EDIT(13:08))`` plus ``"."`` plus ``WS-MYSQL-EDIT(22:02)``
      [common/nominalMT.cbl:L1076-L1085] on the INSERT path and
      [:L1255-L1265] on the UPDATE path - positions 13..20 and 22..23, so
      position one is NEVER copied. GnuCOBOL 3.2.0 compiled from the identical
      declarations returns, for ``HV-LEDGER-BALANCE = -1234.56``::

          full=[-               1234.560000000]
          (13:08)=[    1234]  trim=[1234]  (22:02)=[56]
          INSERT INTO `GLLEDGER-REC` SET ... `LEDGER-BALANCE`="1234.56";

      and for ``-0.07`` it returns ``"0.07"``. Both are the absolute value.
      The six money columns are signed in the schema, so the column CAN hold a
      negative; the bridge simply never writes one. INTEGER columns are
      unaffected because their host variables are unsigned - there is no sign
      to lose - and ``(11:10)`` and ``(18:03)`` were verified to extract their
      digits correctly. Agent Action Plan 0.6.2's "the monetary fields ...
      pass through cleanly" is true of the DECLARATIONS and not of the
      transport. Reproduced by :func:`bridge_money_literal`; fixing it would be
      a failure. The bridge cannot be linked to confirm this end to end because
      ``copy "ACAS-SQLstate-error-list.cob"`` [common/nominalMT.cbl:L175] names
      a copybook absent from the frozen archive, so the isolated
      statement-builder is the oracle.

N-LOG  ``WS-Log-File-No`` HAS TWO VALUES AND THE RDB PATH OVERWRITES THE FIRST.
      ``move 11 to WS-Log-File-No`` [common/acas005.cbl:L284] on entry, then
      ``move 21 to WS-Log-File-no`` [common/acas005.cbl:L600] as the first act
      of the RDB section. Note the maintainer's own capitalisation drift, ``-No``
      at L284 against ``-no`` at L600. Both are reproduced: 11 is written on
      entry by :func:`aa010_main` and 21 by :func:`ba010_test_ws_rec_size`, so a
      Cobol-files run ends on 11 and an RDB run ends on 21. The same pair
      appears in ``acas008`` as 15 -> 25.

N-GUARD  THE GUARDED FUNCTION SETS DIFFER PER HANDLER AND ARE NOT HARMONISED.
      ``acas005`` guards read-indexed (4), start (9) and delete (8)
      [common/acas005.cbl:L288-L302] - NOT write (5) and NOT re-write (7).
      ``acas000`` guards 4, 5 and 7 [common/acas000.cbl:L333-L341] and neither
      8 nor 9. Unifying them would be a defect fix. The test is ``not = 1``,
      exact equality rather than a range, and delete yields 996 where the other
      two yield 998.

N-998  ONE CODE, FOUR DOCUMENTED MEANINGS, NONE OF THEM RESOLVED HERE.
      ``[common/acas005.cbl:L292]`` "file seeks key type out of range";
      ``[common/acas005.cbl:L496]`` "998 Invalid calling parameter settings";
      ``[common/glpostingMT.cbl:L141]`` the authoritative table, "File-Key-No
      out of range"; ``[common/acas000.cbl:L336]`` "file seeks key type out of
      range" again. :mod:`acas_posting.dal.status` owns the code; this module
      supplies the sites and resolves nothing.

N-996-COMMENT  THE 996 COMMENT IS A COPY-PASTE OF THE 998 COMMENT.
      ``[common/acas005.cbl:L298]`` reads "file seeks key type out of range
      996" while the authoritative table records 996 as "delete key out of
      range". Recorded, not corrected.

N-DEADCODE  THE OPEN-OUTPUT -> DELETE-ALL COERCION IS COMMENTED OUT HERE AND
      LIVE IN ``acas008``. [common/acas005.cbl:L305-L315], with the
      maintainer's own reason on [:L307]: "special Delete-All instead. -- NOT
      used with GL." The identical block is live twice in ``acas008``, where
      ``Open-Output`` means delete every row
      [common/acas008.cbl:L313-L319]. NOTHING is implemented for it here, and
      the asymmetry is recorded so the traceability document shows it was
      deliberate. The bridge carries a second dead copy of the same idea in
      ``ba015-Test-Ends`` [common/acas005.cbl:L644-L653].

N-LOADORDER  THE LOAD AND UNLOAD PARAGRAPHS MOVE ``Ledger-Name`` BEFORE
      ``Ledger-Level``, CONTRADICTING BOTH THE HOST-VARIABLE GROUP ORDER AND
      THE COLUMN ORDER. ``move Ledger-Name to HV-LEDGER-NAME``
      [common/nominalMT.cbl:L965] precedes ``move Ledger-Level to
      HV-LEDGER-LEVEL`` [:L966], and ``bb100-UnloadHVs`` inverts the same pair
      at [:L993-L994] - yet the group declares ``LEDGER-LEVEL`` at [:L298]
      before ``LEDGER-NAME`` at [:L299] and the table declares
      ``LEDGER-LEVEL`` fourth and ``LEDGER-NAME`` fifth. The STATEMENT order is
      preserved in :data:`HV_LOAD_ORDER` and :data:`HV_UNLOAD_ORDER`; COLUMNS
      are still emitted in table-ordinal order, because ``SELECT *`` and the
      bridge's own ``INSERT`` both follow the table.

N-REWRITE-SILENT and N-DELETE-SILENT  A NO-OP RE-WRITE OR DELETE REPORTS
      NEITHER SUCCESS NOR FAILURE. ``MYSQL-1210-COMMAND`` fills
      ``WS-Mysql-Count-Rows`` from ``MySQL_affected_rows``
      [copybooks/mysql-procedures.cpy:L178], which counts rows CHANGED. Both
      paragraphs test ``if WS-MYSQL-COUNT-ROWS not = 1``
      [common/nominalMT.cbl:L901], [:L857] and, when the driver reports no
      error, fall to ``go to ba999-End`` [:L912], [:L868] - jumping PAST the
      ``move zero to FS-Reply WE-Error`` that would have reported success
      [:L914], [:L873]. So re-writing a row to the values it already holds, or
      deleting a row that is not there, leaves the CALLER'S incoming status
      pair untouched. ``ba070-Process-Write`` does NOT share the defect,
      because it sets ``zero`` BEFORE the insert [:L796] rather than after.
      Modelled by :attr:`CommandOutcome.status_written`.

N-NOTFOUND-DEAD  THE TWO "Not found" DIAGNOSTICS ARE UNREACHABLE.
      ``ba050-Process-Read-Indexed`` exits on ``WS-MYSQL-Count-Rows = zero``
      at [common/nominalMT.cbl:L633-L637] before it fetches, so the later
      ``if WS-MYSQL-Count-Rows not > zero`` [:L661] can never be true and the
      two branches that ``move "Not found 1"``/``"Not found 2" to Ledger-Name``
      [:L672], [:L678] are dead. Nothing is implemented for them, and the
      record's ``Ledger-Name`` is therefore never overwritten with a
      diagnostic string.

N-SECTION-CASE  ``ba-Process-RDBMS section.`` [common/acas005.cbl:L586] spells
      ``section`` in lower case where ``aa-Process-Flat-File Section.``
      [common/acas005.cbl:L277] capitalises it. Recorded; nothing changed.

N-REDEFINES-ALIAS  THE BRIDGE WRITES THE KEY THROUGH ONE VIEW AND THE POSTING
      PROGRAM READS IT THROUGH THE OTHER. ``bb100-UnloadHVs`` stores the key
      with ``move HV-LEDGER-KEY to WS-Ledger-Key9``
      [common/nominalMT.cbl:L990] - the ``pic 9(8)`` REDEFINES view - while
      ``gl072`` reads the SAME EIGHT BYTES through the group,
      ``divide WS-Ledger-Nos by 100 giving l6-account`` and ``move ledger-pc to
      l6-pc`` [general/gl072.cbl:L412-L413]. In COBOL that works because
      REDEFINES shares storage. Separate Python attributes do not alias, and
      ``records/gl_ledger.py`` states that gap deliberately rather than
      papering over it, ending "the ``acas005`` handler module owns the bridge
      boundary". So this module owns it: :func:`align_ledger_key_views`
      reproduces the shared storage in one named place, and every boundary
      crossing goes through it. Writing only the redefine view would leave
      ``gl072`` dividing zero - silent misposting with no error and no
      diagnostic.

WHAT IS NOT MIGRATED, AND WHY
=============================
The COBOL handler serves TWO backends and this module serves one. When
``FS-Cobol-Files-Used`` [copybooks/wssystem.cob:L111-L113] the handler falls
through to the ISAM paragraphs ``aa020``..``aa090``; otherwise it hands
straight to the bridge and returns [common/acas005.cbl:L319-L323]. The
migration targets the MySQL mirror exclusively - Agent Action Plan 0.2.1.1
maps this module to ``GLLEDGER-REC`` and 0.4.1.5 to the bridge - so there is no
ISAM store to read. The ISAM paragraphs are therefore present for R-5
traceability and reproduce every status, logging and record movement they
perform, but where the COBOL issues the ISAM verb itself they report the frozen
source's own "caller must stop, fix the source" disposition,
``(99, 901)`` [common/acas005.cbl:L612-L613], through
:class:`CobolFileAccessNotMigratedError`. Silently reporting success would be a
behaviour change; this is a recorded omission.

Two more omissions, both representation-only:

* ``call "fhlogger"`` [common/acas005.cbl:L678-L679] and [:L1367] writes a
  test-only log file gated on ``SW-Testing`` [copybooks/Test-Data-Flags.cob].
  It has NO database effect, so per Agent Action Plan 0.3.4 it becomes a log
  record - :func:`ca_process_logs` - and never alters control flow.
* The ``accept Accept-Reply`` that pauses after the 901 display
  [common/acas005.cbl:L628] is dropped and the control transfer to
  ``ba-rdbms-exit`` [:L629] is preserved, exactly as Agent Action Plan 0.3.4
  directs for a prompt whose only effect is to block a terminal.

RULE COMPLIANCE
===============
R-1  No COBOL at runtime. No ``subprocess``, ``ctypes``, ``cffi``, ``os.system``
     or ``cobmysqlapi``, and nothing imported from ``harness``. The handler, the
     bridge and every statement they build are reimplemented natively.
R-2  Zero binary floating point. The six money columns are ``Decimal`` end to
     end, the edit mask in :func:`ws_mysql_edit` is exact-decimal arithmetic,
     and no ``Decimal`` is ever constructed from a ``float``.
R-3  ``SELECT``, ``INSERT``, ``UPDATE`` and ``DELETE`` only - no DDL, no ORM,
     no migration tool, no thread, no pool. Validation is copied, never
     extended.
R-4  See the anomaly register above.
R-5  One function per COBOL paragraph, each citing its locator; every column
     cites its dictionary entry; every ``GO TO`` site carries its class from the
     Agent Action Plan 0.4.2 four-class taxonomy.
R-6  Determinism. No clock, no randomness, no ``uuid``, no ``sleep``. Statement
     order is the COBOL's, and every published collection is an immutable tuple
     or :class:`~types.MappingProxyType` built in a fixed order.

There is NO user rules document for this project - ``review_rules`` reports
"No user rules provided." R-1..R-6 above are the requirement-embedded rules
recorded in Agent Action Plan 0.7.2; anything they are silent on is held to
enterprise-standard best practice.

THE GO TO TAXONOMY AS APPLIED HERE
==================================
Agent Action Plan 0.4.2 classes, and where each is used. Class 4 is the only
one needing per-site proof, and both sites are named:

* Class 1, loop-back to ``continue`` in a ``while True:`` - the lock-retry
  ladder in :func:`_execute_command`, reproducing the commented-out
  ``go to Mysql-1210-Command`` [copybooks/mysql-procedures.cpy:L170].
* Class 2, forward terminator to ``break`` plus the post-loop work - the same
  ladder's exhaustion path.
* Class 3, section or paragraph exit to ``return`` - ``go to
  aa999-main-exit``, ``go to aa-main-exit``, ``go to ba999-end``, ``go to
  ba-rdbms-exit``. By far the commonest class in both programs.
* Class 4, sibling re-dispatch to a named call then an explicit ``return`` -
  (a) ``aa040-Process-Read-Next`` falling into ``aa041-Reread``
  [common/acas005.cbl:L433], reproduced as a call to :func:`aa041_reread`
  followed by returning its result; (b) ``ba050`` and ``ba060`` reaching
  ``ba998-Free`` before ``ba999-End`` [common/nominalMT.cbl:L636, :L702],
  reproduced as a call to :func:`ba998_free` followed by the return that
  ``ba999-End`` performs.
"""

from __future__ import annotations

import decimal
import enum
import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from decimal import Decimal
from types import MappingProxyType
from typing import Any, Final

from acas_posting.dal import cursor_state
from acas_posting.dal.connection import (
    TransportSecurity,
    acquire_cursor,
    cobol_string_delimited_by_space,
    cursor_is_unavailable,
    execute_statement,
    load_rdb_data_once,
    mysql_1000_open,
    mysql_1090_exit,
    mysql_1980_close,
    mysql_1999_exit,
    quote_identifier,
    transport_category,
    transport_decimal_context,
)
from acas_posting.dal.cursor_state import (
    CursorOutcome,
    CursorSlot,
    CursorStateTable,
    DatabaseCursor,
    KeyOfReference,
    key_of_reference,
)
from acas_posting.dal.status import (
    START_ACCESS_TYPE_RANGE,
    AccessType,
    AcasFileHandlerError,
    FileFunction,
    FsReply,
    LogSystem,
    WeError,
    log_file_handler_record,
    log_handler_failure,
    mysql_1100_db_error,
)

#  DELIBERATE OMISSION, recorded as an omission per rule R-5.
#
#  `status.mysql_1300_db_error`, `status.LOCK_RETRY_LADDER` and
#  `status.is_lock_errno` are NOT imported and NOT called from this module, and
#  that is the point. The lock-retry ladder is DEAD CODE in the frozen source: its
#  only `perform Mysql-1300-DB-Error thru Mysql-1390-Exit` is COMMENTED OUT inside
#  `Mysql-1210-Command` [copybooks/mysql-procedures.cpy:L167], together with the
#  `WE-Error = 910` test and the `WS-SQL-Retry = 1` retry jump [:L168-L173]. No
#  live COBOL path reaches it, so no live Python path may either - `status.py` says
#  so in terms: "it has zero call sites in `acas_posting` and must keep zero".
#
#  Wiring the ladder up would give the migrated cycle a retry behaviour the
#  compiled cycle does not have. Rule R-4 makes that a defect FIXED, which is a
#  failure, not an improvement - and it would additionally need a wall-clock sleep,
#  which rule R-6 forbids this module outright.
#
#  What IS live in `Mysql-1210-Command` is reproduced by `_mysql_1210_command`
#  below: query, then `Mysql-1100-Db-Error` on a non-zero return code
#  [copybooks/mysql-procedures.cpy:L176], then `MySQL_affected_rows`
#  UNCONDITIONALLY [:L178] - even after an error.
from acas_posting.dictionary import loader
from acas_posting.records.file_access import FileAccess
from acas_posting.records.file_defs import FileDefs
from acas_posting.records.gl_ledger import (
    WsLedgerKey,
    WsLedgerKey9,
    WsLedgerNosParts,
    WsLedgerRecord,
)
from acas_posting.records.system_record import SystemRecord
from acas_posting.records.test_data_flags import AcasDalCommonData

__all__: Final[tuple[str, ...]] = (
    "BRIDGE_NAME",
    "BRIDGE_PARAGRAPH_NUMBERS",
    "COLUMN_BINDINGS",
    "COLUMN_BINDINGS_BY_NAME",
    "COLUMN_NAMES",
    "DELETE_STATEMENT",
    "DISPATCH_ORDER",
    "ENTITY_FACADE",
    "FILE_KEY_NO",
    "FILE_KEY_TAGS",
    "FLAT_FILE_STATUSES",
    "HANDLER_NAME",
    "HV_LOAD_ORDER",
    "HV_UNLOAD_ORDER",
    "INSERT_STATEMENT",
    "KEY_GUARDED_FUNCTIONS",
    "KEY_OF_REFERENCE",
    "LEDGER_RECORD_LENGTH",
    "SET_CLAUSE",
    "TABLE_NAME",
    "UPDATE_STATEMENT",
    "WS_FILE_KEY_WIDTH",
    "WS_LEDGER_RECORD_LENGTH",
    "WS_LOG_FILE_NO_COBOL",
    "WS_LOG_FILE_NO_RDB",
    "WS_LOG_SYSTEM",
    "WS_MYSQL_EDIT_WIDTH",
    "BridgeSession",
    "CobolFileAccessNotMigratedError",
    "ColumnBinding",
    "CommandOutcome",
    "HandlerParagraph",
    "LedgerKeyView",
    "TdGlledgerRec",
    "aa010_main",
    "aa020_process_open",
    "aa030_process_close",
    "aa040_process_read_next",
    "aa041_reread",
    "aa047_eval_keys",
    "aa050_process_read_indexed",
    "aa060_process_start",
    "aa070_process_write",
    "aa080_process_delete",
    "aa090_process_rewrite",
    "aa100_bad_function",
    "aa999_main_exit",
    "aa_exit",
    "aa_main_exit",
    "aa_process_flat_file",
    "align_ledger_key_views",
    "ba010_test_ws_rec_size",
    "ba012_test_ws_rec_size_2",
    "ba015_test_ends",
    "ba020_process_dal",
    "ba020_process_open",
    "ba030_process_close",
    "ba040_process_read_next",
    "ba041_reread",
    "ba050_process_read_indexed",
    "ba060_process_start",
    "ba070_process_write",
    "ba080_process_delete",
    "ba090_process_rewrite",
    "ba100_bad_function",
    "ba998_free",
    "ba999_end",
    "ba_process_rdbms",
    "ba_rdbms_exit",
    "bb000_hv_load",
    "bb100_unload_hvs",
    "bb200_insert",
    "bb300_update",
    "bridge_character_literal",
    "bridge_money_literal",
    "ca_exit",
    "ca_process_logs",
    "dispatch",
    "nominal_mt",
    "ws_ledger_key_bytes",
    "ws_mysql_edit",
)

_LOG: Final[logging.Logger] = logging.getLogger(__name__)


#  IDENTITY  -  THE SPINE THIS MODULE SITS ON

#: The MySQL table, spelled as `mysql/ACASDB.sql:L122` spells it. Every
#: identifier in this module contains a HYPHEN, so every one is routed through
#: `quote_identifier`; unquoted, each is a MySQL syntax error rather than a
#: subtle bug.
TABLE_NAME: Final[str] = "GLLEDGER-REC"

#: The generated bridge program this module reimplements, named in the handler's
#: own `CALL` [common/acas005.cbl:L663].
BRIDGE_NAME: Final[str] = "nominalMT"

#: The numbered file handler this module reimplements [common/acas005.cbl].
HANDLER_NAME: Final[str] = "acas005"

#: The entity name the facade copybook publishes its twelve verbs under -
#: `GL-Nominal-Open`, `GL-Nominal-Read-Next` and the rest
#: [copybooks/Proc-ACAS-FH-Calls.cob]. Recorded so `dal/facade.py` can bind its
#: entity-named vocabulary to this module without restating the mapping.
ENTITY_FACADE: Final[str] = "GL-Nominal"

#: `move 1 to File-Key-No.` - the facade's dispatch paragraph sets it before
#: every `CALL` [copybooks/Proc-ACAS-FH-Calls.cob:L35-L41], and the key guard
#: below rejects anything else. `nominalMT.scb` declares `occurs 1`
#: [common/nominalMT.scb:L250], so one is the only legal value.
FILE_KEY_NO: Final[int] = 1

#: `move 2 to WS-Log-System.` [common/acas005.cbl:L283] - the handler's own
#: comment enumerates the domain, "1 = IRS, 2=GL, 3=SL, 4=PL, 5=Stock".
WS_LOG_SYSTEM: Final[LogSystem] = LogSystem.GL

#: `move 11 to WS-Log-File-No.` [common/acas005.cbl:L284] - written on entry
#: and therefore the value a Cobol-files run ends on. ANOMALY N-LOG.
WS_LOG_FILE_NO_COBOL: Final[int] = 11

#: `move 21 to WS-Log-File-no.` [common/acas005.cbl:L600] - the first act of the
#: RDB section, overwriting the 11 above. ANOMALY N-LOG, and note the
#: maintainer's `-No`/`-no` capitalisation drift between the two lines.
WS_LOG_FILE_NO_RDB: Final[int] = 21

#: `05  WS-File-Key pic x(64) value spaces.` [copybooks/wsfnctn.cob:L52], whose
#: own comment records the widening: "increased to 64-- 30/12/16". Every log tag
#: this module writes is truncated and space-padded to it, as a COBOL `MOVE` to
#: an alphanumeric field would be.
WS_FILE_KEY_WIDTH: Final[int] = 64


class HandlerParagraph(enum.IntEnum):
    """`WS-No-Paragraph` values the HANDLER writes, one per ISAM verb.

    `03  ws-No-Paragraph pic 999.` [copybooks/wsfnctn.cob:L47]. The handler
    stamps one of these before each flat-file verb so that a log line can be
    traced back to a paragraph. Declared as an enum rather than as loose
    integers because the values are a closed set with meanings, and because a
    reader checking [common/acas005.cbl] against this module should find the
    numbers in one place.

    THE BRIDGE USES A DIFFERENT AND OVERLAPPING SET - 1, 2, 3, 4, 5, 6, 8, 10,
    13, 17 and 20 - which is why :data:`BRIDGE_PARAGRAPH_NUMBERS` is separate
    rather than folded in here. The two programs number their own paragraphs and
    the migration does not reconcile them.
    """

    #: `move 201 to WS-No-Paragraph.` [common/acas005.cbl:L367]
    OPEN = 201

    #: `move 202 to WS-No-Paragraph.` [common/acas005.cbl:L404]
    CLOSE = 202

    #: `move 203 to WS-No-Paragraph.` [common/acas005.cbl:L422]
    READ_NEXT = 203

    #: `move 204 to WS-No-Paragraph.` [common/acas005.cbl:L473]
    READ_INDEXED = 204

    #: `move 205 to WS-No-Paragraph.` [common/acas005.cbl:L489]
    START = 205

    #: `move 206 to WS-No-Paragraph.` [common/acas005.cbl:L535]
    WRITE = 206

    #: `move 207 to WS-No-Paragraph.` [common/acas005.cbl:L547]
    DELETE = 207

    #: `move 208 to WS-No-Paragraph.` [common/acas005.cbl:L559]
    RE_WRITE = 208


#: The BRIDGE's own `ws-No-Paragraph` stamps, keyed by the paragraph that writes
#: each one. Kept as a mapping of names rather than an enum because two of the
#: bridge's paragraphs write two different values in sequence -
#: `ba050-Process-Read-Indexed` stamps 5 before the `SELECT`
#: [common/nominalMT.cbl:L616] and 6 before the `FETCH` [:L638] - so the set is
#: not one-value-per-verb and an enum would misrepresent it.
BRIDGE_PARAGRAPH_NUMBERS: Final[Mapping[str, tuple[int, ...]]] = MappingProxyType(
    {
        # `move 1 to ws-No-Paragraph.` [common/nominalMT.cbl:L420]
        "ba020-Process-Open": (1,),
        # `move 2 to ws-No-Paragraph.` [common/nominalMT.cbl:L439]
        "ba030-Process-Close": (2,),
        # `move 3 to ws-No-Paragraph` [common/nominalMT.cbl:L478]
        "ba040-Process-Read-Next": (3,),
        # `move 4 to ws-No-Paragraph.` [common/nominalMT.cbl:L530]
        "ba041-Reread": (4,),
        # 5 before the SELECT [:L616], 6 before the FETCH [:L638].
        "ba050-Process-Read-Indexed": (5, 6),
        # `move 8 to ws-No-Paragraph` [common/nominalMT.cbl:L748]. SEVEN IS
        # NEVER USED by this bridge - recorded because a reader counting the
        # stamps will notice the gap and it is the frozen source's, not a
        # transcription slip.
        "ba060-Process-Start": (8,),
        # `move 10 to ws-No-Paragraph.` [common/nominalMT.cbl:L799]
        "ba070-Process-Write": (10,),
        # `move 13 to ws-No-Paragraph.` [common/nominalMT.cbl:L843]
        "ba080-Process-Delete": (13,),
        # `move 17 to ws-No-Paragraph.` [common/nominalMT.cbl:L878]
        "ba090-Process-Rewrite": (17,),
        # `move 20 to ws-No-Paragraph.` [common/nominalMT.cbl:L932]
        "ba998-Free": (20,),
    }
)


#  THE WS-FILE-KEY LOG TAGS, VERBATIM

#: Every literal this module can write into `WS-File-Key`, keyed by the
#: paragraph and exit that writes it, transcribed CHARACTER FOR CHARACTER from
#: the frozen source. They are the only way to tell apart several otherwise
#: identical status pairs - the bridge's read-next can return `(10, 10)` under
#: three different tags - so they are behaviour, not decoration, and the
#: `(RDB)` suffixes and inner spacing are preserved exactly.
FILE_KEY_TAGS: Final[Mapping[str, str]] = MappingProxyType(
    {
        # -- handler, flat-file paths -------------------------------------
        # `move "OPEN GL NL File" to WS-File-Key` [common/acas005.cbl:L398]
        "handler-open": "OPEN GL NL File",
        # `move "CLOSE GL NL File" to WS-File-Key.` [common/acas005.cbl:L409]
        "handler-close": "CLOSE GL NL File",
        # `move "EOF" to WS-File-Key` [common/acas005.cbl:L439]
        "handler-eof": "EOF",
        # -- bridge, RDB paths --------------------------------------------
        # `move "OPEN GL LEDGER (RDB)" to WS-File-Key` [common/nominalMT.cbl:L431]
        "bridge-open": "OPEN GL LEDGER (RDB)",
        # `move "CLOSE GL LEDGER (RDB)" to WS-File-Key.` [:L440]
        "bridge-close": "CLOSE GL LEDGER (RDB)",
        # `move "> 00000000" to WS-File-Key` [:L494] - the self-positioning tag,
        # written BEFORE the row count is tested.
        "bridge-position": "> 00000000",
        # `move "No Data" to WS-File-Key` [:L512] - an empty table.
        "bridge-no-data": "No Data",
        # `move "EOF" to WS-File-Key` [:L559] - the fetch returned -1.
        "bridge-eof": "EOF",
        # `move "EOF2" to WS-File-Key` [:L575] - a driver error mid-walk.
        "bridge-eof2": "EOF2",
        # `move "EOF3" to WS-File-Key` [:L583] - `fs-reply` was already 10.
        "bridge-eof3": "EOF3",
    }
)


#  THE KEY GUARD  -  THIS HANDLER'S OWN THREE VERBS AND TWO CODES

#: The `File-Key-No` guard, transcribed from [common/acas005.cbl:L288-L302]::
#:
#:     evaluate File-Function
#:              when  4   *> fn-read-indexed
#:              when  9   *> fn-start
#:                if     File-Key-No not = 1
#:                       move 998 to WE-Error
#:                       move 99 to fs-reply
#:                       go   to aa999-main-exit
#:                end-if
#:              when     8  *> fn-delete
#:                if     File-Key-No not = 1
#:                       move 996 to WE-Error
#:                       move 99 to fs-reply
#:                       go   to aa999-main-exit
#:                end-if
#:     end-evaluate.
#:
#: ANOMALY N-GUARD - REPRODUCED, NOT FIXED. Three facts a reader must not
#: "tidy": the set is read-indexed, start and delete and NOT write or re-write;
#: `acas000` guards a DIFFERENT set, 4, 5 and 7 [common/acas000.cbl:L333-L341],
#: and harmonising the two would be a defect fix; and delete yields 996 where
#: the other two yield 998. The test is `not = 1`, exact equality, NOT a range -
#: so `status.FILE_KEY_NO_GUARD_RANGE` is deliberately unused here.
#:
#: ANOMALY N-998 and N-996-COMMENT are both sited here; see the module
#: docstring for all four wordings of 998 and for the copy-pasted 996 comment.
#: The ORDER of this mapping is the `evaluate`'s own arm order, 4 then 9 then 8,
#: which is neither numeric nor the dispatch order.
KEY_GUARDED_FUNCTIONS: Final[Mapping[FileFunction, tuple[FsReply, WeError, str]]] = (
    MappingProxyType(
        {
            FileFunction.READ_INDEXED: (
                FsReply.ERROR,
                WeError.FILE_KEY_NO_OUT_OF_RANGE,
                "[common/acas005.cbl:L289-L295]",
            ),
            FileFunction.START: (
                FsReply.ERROR,
                WeError.FILE_KEY_NO_OUT_OF_RANGE,
                "[common/acas005.cbl:L290-L295]",
            ),
            FileFunction.DELETE: (
                FsReply.ERROR,
                # 996, not 998 - the one place the two codes differ, and the one
                # whose comment was copy-pasted from 998. ANOMALY N-996-COMMENT.
                WeError.DELETE_KEY_OUT_OF_RANGE,
                "[common/acas005.cbl:L296-L301]",
            ),
        }
    )
)

#: The single key of reference, resolved from the shared transcription in
#: :mod:`acas_posting.dal.cursor_state` rather than restated here, so that the
#: offset and length cannot drift between the two modules. That transcription is
#: `KeyName "LEDGER-KEY"`, `KOR-Offset 0001`, `KOR-Length 0008`, `KOR-Type
#: "STR"`, taken from [common/nominalMT.scb:L245-L247] via the `occurs 1`
#: redefinition [:L250-L254].
#:
#: `occurs 1` IS THE WHOLE STORY: this table declares ONE key, the primary, so
#: there is no alternate index to choose and no `File-Key-No` other than 1 to
#: honour. `KOR-Type "STR"` is carried and never branched on because the frozen
#: source never branches on it either - its own comment is "Not used currently"
#: [common/nominalMT.scb:L254].
#:
#: The offset and length address BYTES OF THE WORKING-STORAGE RECORD, not a
#: column ordinal: the bridge slices the key value straight out of the record
#: with them, `WS-Ledger-Record (K:L)` after `move KOR-offset (KOR-x1) to K`
#: [common/nominalMT.cbl:L598-L599, :L607] and again at [:L707-L709, :L732].
KEY_OF_REFERENCE: Final[KeyOfReference] = key_of_reference(TABLE_NAME, FILE_KEY_NO)


#  THE ELEVEN COLUMNS, FROM THE DATA DICTIONARY


@dataclass(frozen=True, slots=True)
class ColumnBinding:
    """One column of ``GLLEDGER-REC``, bound to its record field and host variable.

    Built ONLY from ``loader.entries_for_table("GLLEDGER-REC")`` - never from a
    picture clause read by eye. Agent Action Plan 0.8.1 makes that ordering a
    directive rather than a preference, and Agent Action Plan 0.8.2 records why
    the bridge is the authority: "The maintainer's one-way COBOL-to-MySQL bridge
    defines the authoritative record-layout <-> table mapping - it is the data
    dictionary for this migration."

    Frozen and slotted because the set is fixed at import and rule R-6 requires
    that two processes agree on it byte for byte.
    """

    #: `ordinal` of the column in `mysql/ACASDB.sql`, one-based. The ORDER
    #: statements are emitted in, because `SELECT *` returns columns in it and
    #: the bridge's own `INSERT` follows it.
    ordinal: int

    #: The MySQL column name, hyphens included, UNQUOTED. Quoting happens once,
    #: at statement build time, through `quote_identifier`.
    column_name: str

    #: The dictionary key, `GLLEDGER-REC.<COLUMN>`, so every binding can be
    #: taken back to its entry with `loader.get_entry` (rule R-5).
    dictionary_key: str

    #: The bridge host-variable name, e.g. `HV-LEDGER-KEY`
    #: [common/nominalMT.cbl:L295-L305].
    hv_name: str

    #: The attribute of :class:`TdGlledgerRec` that holds the host variable.
    hv_attribute: str

    #: The host variable's PICTURE, e.g. `S9(08)V9(02)`. Held so the store
    #: semantics below are driven by the bridge's own declaration rather than by
    #: a width written out by hand.
    hv_picture: str

    #: The host variable's USAGE, e.g. `COMP`. Note this is where the money
    #: fields change storage class - `COMP-3` in the copybook
    #: [copybooks/wsledger.cob:L28-L34] becomes `COMP` in the bridge
    #: [common/nominalMT.cbl:L300-L305]. Packed to binary, value unchanged.
    hv_usage: str

    #: Total digits of the host variable, `None` for the alphanumeric ones.
    hv_digits: int | None

    #: Decimal places of the host variable, `None` for the alphanumeric ones.
    hv_scale: int | None

    #: Whether the host variable carries a sign. `True` for the six money
    #: fields, `False` for `KEY`, `TYPE` and `LEVEL` - which is why only the
    #: money fields can suffer ANOMALY N-SIGNLOSS.
    hv_signed: bool

    #: Character length of the host variable, `None` for the numeric ones. This
    #: is the 32 of ANOMALY A-12 for `HV-LEDGER-NAME`
    #: [common/nominalMT.cbl:L299] against the copybook's 24
    #: [copybooks/wsledger.cob:L27].
    hv_character_length: int | None

    #: The copybook field name, e.g. `WS-Ledger-Key9`
    #: [copybooks/wsledger.cob:L21-L22].
    copybook_name: str

    #: Dotted attribute path from a :class:`WsLedgerRecord` to the field this
    #: column is loaded from and unloaded to, e.g. `quarters.ledger_q1`. The
    #: path is needed because `copybooks/wsledger.cob` groups the quarters under
    #: `Quarters` [:L30] and reaches the key through a REDEFINES [:L21-L22], so
    #: the record layer models both as nested dataclasses.
    record_attribute: str

    #: `[copybooks/wsledger.cob:L<n>]` for the declaring line.
    copybook_locator: str

    #: `[common/nominalMT.cbl:L<n>]` for the host-variable declaration.
    hv_locator: str

    #: `[mysql/ACASDB.sql:L<n>]` for the column definition.
    column_locator: str

    #: `[common/nominalMT.cbl:L<n>]` for the `bb000-HV-Load` move that fills the
    #: host variable. These are what make ANOMALY N-LOADORDER visible: the
    #: `LEDGER-NAME` move is at L965 and the `LEDGER-LEVEL` move at L966, the
    #: reverse of both the group order and the column order.
    load_locator: str

    #: `[common/nominalMT.cbl:L<n>]` for the `bb100-UnloadHVs` move.
    unload_locator: str

    #: `INT`, `STR` or `DECIMAL`, from the dictionary's own
    #: `cobol_python_storage`. Never inferred and never `float` - R-2 forbids
    #: binary floating point in any accounting path.
    python_storage: str

    #: Whether the column is `NOT NULL` in the frozen schema. All eleven are,
    #: which is why every `INSERT` names every column and no bind is ever
    #: `None`; see :func:`bb200_insert`.
    not_null: bool

    #: Whether the column is the table's primary key.
    primary_key: bool

    #: The dictionary's own anomaly tags for this column. Non-empty for exactly
    #: one of the eleven, `LEDGER-NAME`, which carries `A-12` - the ledger-name
    #: width drift declared `x(24)` in the copybook [copybooks/wsledger.cob:L27],
    #: widened to `X(32)` at the bridge [common/nominalMT.cbl:L299] and stored
    #: `char(32)` in the frozen schema [mysql/ACASDB.sql:L127].
    anomaly_refs: tuple[str, ...]

    def cite(self) -> str:
        """Return the dictionary citation for this column, for logs and evidence.

        Delegates to :func:`loader.cite` so the wording is the dictionary's and
        cannot drift from it (rule R-5).
        """
        return loader.cite(self.dictionary_key)


#: The column count `mysql/ACASDB.sql:L122-L135` declares, and the count Agent
#: Action Plan 0.6.6 records for this table. Stated so the check in
#: :func:`_column_bindings` compares against the frozen schema rather than
#: against itself.
_DECLARED_COLUMN_COUNT: Final[int] = 11

#: Copybook field name -> dotted attribute path on :class:`WsLedgerRecord`.
#:
#: The dictionary records WHICH copybook field each host variable is loaded from
#: [common/nominalMT.cbl:L961-L972] but, being derived from COBOL, it records the
#: field's NAME rather than a Python path. This table is the one place the two
#: naming schemes are joined, and it is stated rather than computed because two
#: of the eleven are not a simple lower-casing: `WS-Ledger-Key9` is a REDEFINES
#: view [copybooks/wsledger.cob:L21-L22] and the four quarters sit inside the
#: `Quarters` group [:L30-L34].
_RECORD_ATTRIBUTE_BY_COPYBOOK_FIELD: Final[Mapping[str, str]] = MappingProxyType(
    {
        "WS-Ledger-Key9": "ws_ledger_key9.ws_ledger_key9",
        "Ledger-Type": "ledger_type",
        "Ledger-Place": "ledger_place",
        "Ledger-Level": "ledger_level",
        "Ledger-Name": "ledger_name",
        "Ledger-Balance": "ledger_balance",
        "Ledger-Last": "ledger_last",
        "Ledger-Q1": "quarters.ledger_q1",
        "Ledger-Q2": "quarters.ledger_q2",
        "Ledger-Q3": "quarters.ledger_q3",
        "Ledger-Q4": "quarters.ledger_q4",
    }
)


def _column_bindings() -> tuple[ColumnBinding, ...]:
    """Build the eleven bindings from the data dictionary, in column order.

    Runs ONCE at import. Every value is read out of the generated dictionary, so
    a change to the frozen sources reaches this module by regenerating the
    dictionary rather than by editing code - which is what makes the field-level
    half of rule R-5's traceability mechanical.

    ``loader.entries_for_table`` already returns column-ordinal order; the
    explicit ``sorted`` below states the requirement rather than relying on it,
    because ORDER IS THE ONE THING THIS MODULE CANNOT GET WRONG - it decides the
    ``INSERT`` column list, the ``UPDATE`` set list and the order the fetch
    unloads into the record.

    Returns:
        The eleven bindings, ordinal 1 through 11.

    Raises:
        ValueError: If the dictionary does not describe exactly the eleven
            columns `mysql/ACASDB.sql:L122-L135` declares, or describes them
            with ordinals other than 1..11. This asserts that the
            TRANSCRIPTION is intact; it is not new validation of run-time data,
            which rule R-3 forbids, because every input is a committed artifact
            and a failure here is a build error caught at import.
    """
    entries = sorted(loader.entries_for_table(TABLE_NAME), key=lambda e: e.column.ordinal)
    bindings: list[ColumnBinding] = []
    for entry in entries:
        column = entry.column
        host_variable = entry.bridge_host_variable
        copybook = entry.copybook
        bindings.append(
            ColumnBinding(
                ordinal=column.ordinal,
                column_name=column.name,
                dictionary_key=entry.key,
                hv_name=host_variable.name,
                # `HV-LEDGER-KEY` -> `hv_ledger_key`. One mechanical rule, so a
                # reader can map either way without a second table.
                hv_attribute=host_variable.name.lower().replace("-", "_"),
                hv_picture=host_variable.picture,
                hv_usage=str(host_variable.usage),
                hv_digits=host_variable.digits,
                hv_scale=host_variable.scale,
                hv_signed=host_variable.signed,
                hv_character_length=host_variable.character_length,
                copybook_name=copybook.name,
                record_attribute=_RECORD_ATTRIBUTE_BY_COPYBOOK_FIELD[copybook.name],
                copybook_locator=f"[{copybook.source}]",
                hv_locator=f"[{host_variable.source}]",
                column_locator=f"[{column.source}]",
                load_locator=f"[{host_variable.load_source}]",
                unload_locator=f"[{host_variable.unload_source}]",
                python_storage=str(entry.cobol_python_storage),
                not_null=not column.nullable,
                primary_key=column.is_primary_key,
                anomaly_refs=tuple(entry.anomaly_refs),
            )
        )
    expected_ordinals = tuple(range(1, len(bindings) + 1))
    if tuple(b.ordinal for b in bindings) != expected_ordinals:
        raise ValueError(
            f"{TABLE_NAME} column ordinals are not contiguous from 1: "
            f"{tuple(b.ordinal for b in bindings)}"
        )
    if len(bindings) != _DECLARED_COLUMN_COUNT:
        raise ValueError(
            f"{TABLE_NAME} is declared with {_DECLARED_COLUMN_COUNT} columns at "
            f"[mysql/ACASDB.sql:L122-L135]; the dictionary describes "
            f"{len(bindings)}"
        )
    return tuple(bindings)


#: The eleven columns in TABLE-ORDINAL order - the order every statement this
#: module builds uses, and the order `MySQL_fetch_record` receives its host
#: variables in [common/nominalMT.cbl:L540-L551, :L645-L656].
COLUMN_BINDINGS: Final[tuple[ColumnBinding, ...]] = _column_bindings()

#: Just the names, same order. Held separately because the statement builders
#: want names and nothing else, and because a test can compare this tuple across
#: two processes to prove the determinism rule R-6 asks for.
COLUMN_NAMES: Final[tuple[str, ...]] = tuple(b.column_name for b in COLUMN_BINDINGS)

#: The bindings by column name, for the fetch path, which is handed a row keyed
#: by column name and must find the binding without scanning.
COLUMN_BINDINGS_BY_NAME: Final[Mapping[str, ColumnBinding]] = MappingProxyType(
    {binding.column_name: binding for binding in COLUMN_BINDINGS}
)


#  WS-MYSQL-EDIT  -  THE BRIDGE'S NUMERIC EDIT MASK, AND ANOMALY N-SIGNLOSS

#: `01  WS-MYSQL-EDIT       PIC -Z(18)9.9(9).` [common/nominalMT.cbl:L232].
#: Thirty character positions, laid out as::
#:
#:     pos  1       `-`      the SIGN: "-" when negative, " " when not
#:     pos  2..19   Z(18)    integer digits, LEADING ZEROS SUPPRESSED TO SPACES
#:     pos  20      `9`      the units digit, never suppressed
#:     pos  21      `.`      the decimal point
#:     pos  22..30  9(9)     nine decimal digits, zero-filled
#:
#: Confirmed by compiling the identical declaration under GnuCOBOL 3.2.0:
#: `function length(WS-MYSQL-EDIT)` returns 30.
WS_MYSQL_EDIT_WIDTH: Final[int] = 30

#: Total integer digit positions, `Z(18)` plus the trailing `9` - positions
#: 2..20 of the field.
_EDIT_INTEGER_DIGITS: Final[int] = 19

#: Total decimal digit positions, `9(9)` - positions 22..30.
_EDIT_DECIMAL_DIGITS: Final[int] = 9

#: `WS-MYSQL-EDIT(13:08)` - the money reference modifier
#: [common/nominalMT.cbl:L1078]. One-based start, length. Positions 13..20, the
#: eight integer digits of an `S9(08)V9(02)` value - AND NOT POSITION ONE, which
#: is where the sign lives. This single pair of numbers is anomaly N-SIGNLOSS.
_EDIT_MONEY_INTEGER_SLICE: Final[tuple[int, int]] = (13, 8)

#: `WS-MYSQL-EDIT(22:02)` - the money decimal digits
#: [common/nominalMT.cbl:L1083]. Positions 22..23.
_EDIT_MONEY_DECIMAL_SLICE: Final[tuple[int, int]] = (22, 2)

#: `WS-MYSQL-EDIT(11:10)` - the `LEDGER-KEY` reference modifier
#: [common/nominalMT.cbl:L1024]. Positions 11..20, the ten integer digits of the
#: `9(10) COMP` host variable. Unsigned, so nothing is lost.
_EDIT_KEY_SLICE: Final[tuple[int, int]] = (11, 10)

#: `WS-MYSQL-EDIT(18:03)` - the `LEDGER-TYPE` and `LEDGER-LEVEL` reference
#: modifier [common/nominalMT.cbl:L1036, :L1057]. Positions 18..20, the three
#: integer digits of a `9(03) COMP` host variable. Unsigned, so nothing is lost.
_EDIT_SMALL_INT_SLICE: Final[tuple[int, int]] = (18, 3)


def ws_mysql_edit(value: Decimal | int) -> str:
    """Render ``value`` as ``MOVE <value> TO WS-MYSQL-EDIT`` renders it.

    Reproduces the numeric-edited ``MOVE`` the bridge performs before every
    numeric literal it embeds, e.g. ``MOVE HV-LEDGER-BALANCE TO WS-MYSQL-EDIT``
    [common/nominalMT.cbl:L1076]. The receiving field is
    ``PIC -Z(18)9.9(9)`` [common/nominalMT.cbl:L232], so the rules are:

    * align on the DECIMAL POINT, not on either end;
    * put the sign in position one - ``"-"`` for negative, ``" "`` otherwise;
    * suppress leading zeros in positions 2..19 to SPACES, but never in
      position 20, which is a ``9`` and always shows a digit;
    * zero-fill the decimal positions to the right of the value's own scale.

    Exact-decimal throughout, as rule R-2 requires: the value is a
    :class:`~decimal.Decimal` or an :class:`int`, the scaling is done by
    integer arithmetic on the digit string, and no ``float`` appears anywhere.

    Verified against GnuCOBOL 3.2.0 compiled from the same declaration::

        -1234.56     -> "-               1234.560000000"
         1234.56     -> "                1234.560000000"
        -0.07        -> "-                  0.070000000"
         87654321.99 -> "            87654321.990000000"
         1234567     -> "             1234567.000000000"
         0           -> "                   0.000000000"

    Args:
        value: The host variable's value. ``Decimal`` for the money host
            variables, ``int`` for the three integer ones.

    Returns:
        Exactly :data:`WS_MYSQL_EDIT_WIDTH` characters.
    """
    # `decimal.localcontext` with the transport context keeps this arithmetic
    # inside the precision `connection.py` pins for everything crossing the
    # boundary, so an unusual ambient context cannot change a stored penny.
    with decimal.localcontext(transport_decimal_context()):
        amount = Decimal(value) if isinstance(value, int) else Decimal(value)
        negative = amount < 0
        magnitude = -amount if negative else amount
        # The digit string of the magnitude, scaled up to the field's nine
        # decimal places. `int()` on a quantized Decimal is exact.
        scaled = magnitude.scaleb(_EDIT_DECIMAL_DIGITS)
        units = int(scaled.to_integral_value(rounding=decimal.ROUND_DOWN))
        digits = str(units).rjust(_EDIT_INTEGER_DIGITS + _EDIT_DECIMAL_DIGITS, "0")
        integer_part = digits[:_EDIT_INTEGER_DIGITS]
        decimal_part = digits[_EDIT_INTEGER_DIGITS:]
    # Z-suppression: positions 2..19 show a space in place of a leading zero,
    # position 20 always shows its digit. Slicing off the last integer position
    # first is what encodes "never suppress the units digit".
    suppressible, units_digit = integer_part[:-1], integer_part[-1]
    stripped = suppressible.lstrip("0")
    suppressed = stripped.rjust(len(suppressible), " ")
    sign = "-" if negative else " "
    return f"{sign}{suppressed}{units_digit}.{decimal_part}"


def _reference_modifier(edited: str, start: int, length: int) -> str:
    """Return ``edited(start:length)`` with COBOL's one-based indexing.

    A COBOL reference modifier is one-based and inclusive of ``length``
    characters. Doing the conversion in one named place means no statement
    builder below performs index arithmetic of its own, which is the only way to
    keep the four slice constants above checkable against the frozen source.

    Args:
        edited: The thirty-character edited field.
        start: One-based first character position.
        length: Number of characters.

    Returns:
        The ``length`` characters beginning at ``start``.
    """
    return edited[start - 1 : start - 1 + length]


def bridge_money_literal(value: Decimal) -> Decimal:
    """Return the money value the bridge's SQL literal actually DENOTES.

    ANOMALY N-SIGNLOSS - REPRODUCED, NOT FIXED.

    The bridge builds each money literal in three pieces
    [common/nominalMT.cbl:L1076-L1085] on the ``INSERT`` path and
    [:L1255-L1265] on the ``UPDATE`` path::

        MOVE HV-LEDGER-BALANCE TO WS-MYSQL-EDIT
        STRING FUNCTION TRIM (WS-MYSQL-EDIT(13:08)) ...
        STRING "." ...
        STRING WS-MYSQL-EDIT(22:02) ...

    ``(13:08)`` is positions 13..20 and ``(22:02)`` is positions 22..23. The
    SIGN LIVES AT POSITION ONE and is in neither slice, so it is never copied
    into the statement. The literal is therefore always non-negative, and a
    negative balance is stored as its ABSOLUTE VALUE.

    Settled against the compiled oracle, which rule R-6 makes the tie-breaker.
    GnuCOBOL 3.2.0, same declarations, ``HV-LEDGER-BALANCE = -1234.56``::

        INSERT INTO `GLLEDGER-REC` SET ... `LEDGER-BALANCE`="1234.56";

    and ``-0.07`` yields ``"0.07"``. Fixing this - emitting the sign, or
    reaching past the slice for position one - would be a defect fixed, which
    rule R-4 makes a failure. Agent Action Plan 0.6.2's remark that the monetary
    fields "pass through cleanly" is true of the three DECLARATIONS, all of
    which are signed, and not of the transport between them.

    The three INTEGER columns are unaffected: ``HV-LEDGER-KEY`` ``9(10)``,
    ``HV-LEDGER-TYPE`` ``9(03)`` and ``HV-LEDGER-LEVEL`` ``9(03)`` are all
    UNSIGNED [common/nominalMT.cbl:L295-L298], so they have no sign to lose, and
    ``(11:10)`` and ``(18:03)`` were verified to capture all of their digits.

    This returns a :class:`~decimal.Decimal` rather than the literal STRING
    because the value is bound as a parameter rather than interpolated - the
    same trade :mod:`acas_posting.dal.cursor_state` documents for the key,
    where "interpolation is transport, and a bound parameter yields the same
    logical predicate while removing an injection route the frozen source left
    open". What must survive that trade is the value the literal DENOTES, and
    that is what this returns.

    Args:
        value: The host variable's value, already stored into
            ``S9(08)V9(02)`` by :func:`bb000_hv_load`.

    Returns:
        The non-negative two-decimal-place value the bridge's literal denotes.
    """
    edited = ws_mysql_edit(value)
    integer_text = _reference_modifier(edited, *_EDIT_MONEY_INTEGER_SLICE).strip()
    decimal_text = _reference_modifier(edited, *_EDIT_MONEY_DECIMAL_SLICE)
    # `FUNCTION TRIM` on an all-space slice yields the empty string, which the
    # bridge would concatenate as nothing at all. That can only happen for a
    # value whose units digit is outside the slice, which `S9(08)V9(02)` makes
    # impossible - position 20 is always a digit and the slice ends there - so
    # the guard records the reasoning rather than papering over a real path.
    return Decimal(f"{integer_text or '0'}.{decimal_text}")


def _bridge_integer_literal(value: int, slice_spec: tuple[int, int]) -> int:
    """Return the integer a bridge numeric literal denotes, via the edit mask.

    The integer columns take the same route as the money ones -
    ``MOVE HV-LEDGER-KEY TO WS-MYSQL-EDIT`` then
    ``FUNCTION TRIM (WS-MYSQL-EDIT(11:10))`` [common/nominalMT.cbl:L1022-L1026]
    - and are put through it here rather than bound directly, so that the ONE
    transformation the bridge applies is the one this module applies. Their host
    variables are unsigned, so unlike :func:`bridge_money_literal` nothing is
    lost; reproducing the path anyway is what proves that, and it would catch a
    future bridge whose slice did not cover all of its digits.

    Args:
        value: The host variable's value.
        slice_spec: :data:`_EDIT_KEY_SLICE` or :data:`_EDIT_SMALL_INT_SLICE`.

    Returns:
        The integer the literal denotes.
    """
    edited = ws_mysql_edit(value)
    text = _reference_modifier(edited, *slice_spec).strip()
    return int(text or "0")


#  TD-GLLEDGER-REC  -  THE BRIDGE'S HOST-VARIABLE GROUP

#: The record-layer descriptors for the eleven column-mapped copybook fields,
#: keyed by dictionary key.
#:
#: These own COBOL ``MOVE`` semantics AT THE COPYBOOK END - truncation to the
#: copybook's own width, scale and sign - and :func:`bb100_unload_hvs` moves
#: through them, which is what makes ANOMALY A-12 truncate 32 characters back to
#: 24 on the read path [copybooks/wsledger.cob:L27].
#:
#: Typed loosely on purpose. The concrete class lives in ``acas_posting.cobol``,
#: which this layer must not import (Agent Action Plan 0.4.3 confines
#: ``dal/acas*.py`` to ``dal.connection``, ``dal.status``, ``dal.cursor_state``
#: and one ``records`` module), so the descriptors are reached only through the
#: record class that publishes them.
_COPYBOOK_DESCRIPTORS: Final[Mapping[str, Any]] = MappingProxyType(
    {descriptor.dictionary_key: descriptor for descriptor in WsLedgerRecord.COLUMN_MAPPED_FIELDS}
)


def _locator_line(locator: str) -> int:
    """Return the line number out of a ``[file:Lnnn]`` locator.

    Used only to ORDER the load and unload sequences by the line the frozen
    bridge performs each move on, so :data:`HV_LOAD_ORDER` and
    :data:`HV_UNLOAD_ORDER` are derived from the dictionary rather than typed out
    - which is how ANOMALY N-LOADORDER stays visible even if someone later
    re-reads the bridge and disagrees with this module's prose.

    Args:
        locator: A locator of the form ``[common/nominalMT.cbl:L965]``.

    Returns:
        The integer line number, e.g. ``965``.

    Raises:
        ValueError: If the locator has no ``:L<digits>`` part. A build error, not
            run-time validation: every input is a committed artifact.
    """
    _, _, tail = locator.rpartition(":L")
    digits = tail.rstrip("]")
    if not digits.isdigit():
        raise ValueError(f"locator {locator!r} has no ':L<line>' part")
    return int(digits)


#: The eleven columns in the order ``bb000-HV-Load`` MOVES THEM
#: [common/nominalMT.cbl:L962-L972], derived by sorting the bindings on their
#: load locator.
#:
#: ANOMALY N-LOADORDER - REPRODUCED, NOT FIXED. This is NOT the column order:
#: ``Ledger-Name`` is moved at L965 and ``Ledger-Level`` at L966, while both the
#: host-variable group [:L294-L305] and the frozen schema
#: [mysql/ACASDB.sql:L122-L135] declare ``LEDGER-LEVEL`` BEFORE ``LEDGER-NAME``.
#: The statement order is preserved here; the COLUMN order is preserved in
#: :data:`COLUMN_BINDINGS` and is what the statement builders use. Reordering
#: either to match the other would be a defect fixed, which rule R-4 makes a
#: failure.
HV_LOAD_ORDER: Final[tuple[str, ...]] = tuple(
    binding.column_name
    for binding in sorted(COLUMN_BINDINGS, key=lambda b: _locator_line(b.load_locator))
)

#: The eleven columns in the order ``bb100-UnloadHVs`` MOVES THEM
#: [common/nominalMT.cbl:L990-L1000]. The SAME inversion appears here -
#: ``HV-LEDGER-NAME`` at L993 before ``HV-LEDGER-LEVEL`` at L994 - which is what
#: shows N-LOADORDER is a consistent habit of the generator rather than a slip on
#: one line.
HV_UNLOAD_ORDER: Final[tuple[str, ...]] = tuple(
    binding.column_name
    for binding in sorted(COLUMN_BINDINGS, key=lambda b: _locator_line(b.unload_locator))
)


@dataclass(slots=True)
class TdGlledgerRec:
    """``01  TD-GLLEDGER-REC.`` [common/nominalMT.cbl:L294-L305].

    The bridge's host-variable group for ``GLLEDGER-REC``, declared by the
    ``/MYSQL VAR\\ ... TABLE=GLLEDGER-REC,HV ... /MYSQL-END\\`` directive
    [common/nominalMT.cbl:L286-L306] and materialised by the JC preSQL
    translator as an ``01`` record whose ``05`` items are the eleven host
    variables, in COLUMN order::

        05  HV-LEDGER-KEY       PIC  9(10)        COMP     [:L295]
        05  HV-LEDGER-TYPE      PIC  9(03)        COMP     [:L296]
        05  HV-LEDGER-PLACE     PIC X(1)                   [:L297]
        05  HV-LEDGER-LEVEL     PIC  9(03)        COMP     [:L298]
        05  HV-LEDGER-NAME      PIC X(32)                  [:L299]
        05  HV-LEDGER-BALANCE   PIC S9(08)V9(02)  COMP     [:L300]
        05  HV-LEDGER-LAST      PIC S9(08)V9(02)  COMP     [:L301]
        05  HV-LEDGER-Q1        PIC S9(08)V9(02)  COMP     [:L302]
        05  HV-LEDGER-Q2        PIC S9(08)V9(02)  COMP     [:L303]
        05  HV-LEDGER-Q3        PIC S9(08)V9(02)  COMP     [:L304]
        05  HV-LEDGER-Q4        PIC S9(08)V9(02)  COMP     [:L305]

    This group is the MIDDLE of the three-layer mapping, and it is the layer the
    Agent Action Plan makes authoritative: "The maintainer's one-way
    COBOL-to-MySQL bridge defines the authoritative record-layout <-> table
    mapping - it is the data dictionary for this migration" (0.8.2). Three of the
    eleven are WIDER here than at either end - ``KEY`` 8 -> 10 -> 8 digits,
    ``TYPE`` and ``LEVEL`` 1 -> 3 -> 1 - which is invisible for in-range values
    and is precisely the drift 0.6.2 warns must be taken field by field from the
    dictionary rather than inferred. One of the eleven is wider here and STAYS
    wider at the column: ``NAME`` 24 -> 32 -> 32, ANOMALY A-12.

    Mutable and slotted: the COBOL group is working storage that the load and
    unload paragraphs write in place, and slots keep a typo in an attribute name
    an error rather than a silently ignored assignment.

    Field defaults are the state ``INITIALIZE TD-GLLEDGER-REC``
    [common/nominalMT.cbl:L961] produces - zero for numeric, spaces for
    alphanumeric - so a freshly constructed group already satisfies the
    ``NOT NULL`` invariant of Agent Action Plan 0.6.2: "the Python layer must
    default rather than omit".
    """

    #: ``HV-LEDGER-KEY PIC 9(10) COMP`` [common/nominalMT.cbl:L295]. Unsigned,
    #: so it cannot carry the sign loss that N-SIGNLOSS inflicts on the money.
    hv_ledger_key: int = 0

    #: ``HV-LEDGER-TYPE PIC 9(03) COMP`` [common/nominalMT.cbl:L296].
    hv_ledger_type: int = 0

    #: ``HV-LEDGER-PLACE PIC X(1)`` [common/nominalMT.cbl:L297].
    hv_ledger_place: str = " "

    #: ``HV-LEDGER-LEVEL PIC 9(03) COMP`` [common/nominalMT.cbl:L298].
    hv_ledger_level: int = 0

    #: ``HV-LEDGER-NAME PIC X(32)`` [common/nominalMT.cbl:L299]. THIRTY-TWO, not
    #: the copybook's twenty-four [copybooks/wsledger.cob:L27] - ANOMALY A-12.
    hv_ledger_name: str = " " * 32

    #: ``HV-LEDGER-BALANCE PIC S9(08)V9(02) COMP`` [common/nominalMT.cbl:L300].
    hv_ledger_balance: Decimal = Decimal("0.00")

    #: ``HV-LEDGER-LAST PIC S9(08)V9(02) COMP`` [common/nominalMT.cbl:L301].
    hv_ledger_last: Decimal = Decimal("0.00")

    #: ``HV-LEDGER-Q1 PIC S9(08)V9(02) COMP`` [common/nominalMT.cbl:L302].
    hv_ledger_q1: Decimal = Decimal("0.00")

    #: ``HV-LEDGER-Q2 PIC S9(08)V9(02) COMP`` [common/nominalMT.cbl:L303].
    hv_ledger_q2: Decimal = Decimal("0.00")

    #: ``HV-LEDGER-Q3 PIC S9(08)V9(02) COMP`` [common/nominalMT.cbl:L304].
    hv_ledger_q3: Decimal = Decimal("0.00")

    #: ``HV-LEDGER-Q4 PIC S9(08)V9(02) COMP`` [common/nominalMT.cbl:L305].
    hv_ledger_q4: Decimal = Decimal("0.00")

    def initialize(self) -> None:
        """``INITIALIZE TD-GLLEDGER-REC.`` [common/nominalMT.cbl:L961].

        The FIRST statement of ``bb000-HV-Load``, and the reason every column of
        the frozen schema can be ``NOT NULL``. Agent Action Plan 0.6.2, on the
        convention every bridge follows: "each load paragraph begins by
        initialising the host-variable group, so unset fields become zero or
        space rather than SQL ``NULL``. This is why every column in the schema
        can be declared ``NOT NULL`` and why the Python layer must default rather
        than omit."

        Resets numeric items to zero and alphanumeric items to spaces, exactly as
        COBOL's ``INITIALIZE`` does for a group with no ``VALUE`` clauses.
        """
        self.hv_ledger_key = 0
        self.hv_ledger_type = 0
        self.hv_ledger_place = " "
        self.hv_ledger_level = 0
        self.hv_ledger_name = " " * 32
        self.hv_ledger_balance = Decimal("0.00")
        self.hv_ledger_last = Decimal("0.00")
        self.hv_ledger_q1 = Decimal("0.00")
        self.hv_ledger_q2 = Decimal("0.00")
        self.hv_ledger_q3 = Decimal("0.00")
        self.hv_ledger_q4 = Decimal("0.00")


#  REDEFINES ALIASING  -  ANOMALY N-REDEFINES-ALIAS

class LedgerKeyView(enum.Enum):
    """Which declaration of the shared eight key characters was written last.

    ``copybooks/wsledger.cob`` declares the account key TWICE over the SAME eight
    characters::

        03  WS-Ledger-Key.                          [copybooks/wsledger.cob:L13]
            05  WS-Ledger-Nos    pic 9(6).          [:L14]
            05  filler redefines WS-Ledger-Nos.     [:L16]
                07  Ledger-n     pic 9(4).          [:L17]
                07  Ledger-s     pic 9(2).          [:L18]
            05  Ledger-PC        pic 9(2).          [:L20]
        03  WS-Ledger-Key9 redefines WS-Ledger-Key
                             pic 9(8).              [:L21-L22]

    In COBOL these are one storage location seen three ways, so writing any view
    updates all of them for free. Python dataclasses have no such aliasing, and
    the record layer says so explicitly and hands the problem here: "the
    ``acas005`` handler module owns the bridge boundary."

    This enum names the direction an alignment travels, because the two in-scope
    directions have DIFFERENT writers:

    * :attr:`GROUP` - a caller wrote the group view and the bridge must read the
      redefinition. Every in-scope caller does this, e.g.
      ``move post-ledger to WS-Ledger-Key`` [general/gl072.cbl:L405].
    * :attr:`REDEFINES` - the bridge wrote the redefinition and a caller must read
      the group view. ``bb100-UnloadHVs`` does exactly this,
      ``move HV-LEDGER-KEY to WS-Ledger-Key9`` [common/nominalMT.cbl:L990].

    ANOMALY N-REDEFINES-ALIAS. The asymmetry is load-bearing, not cosmetic. The
    bridge writes ONLY the redefinition on the fetch path, while ``gl072`` reads
    ONLY the group view - ``divide WS-Ledger-Nos by 100 giving l6-account`` and
    ``move ledger-pc to l6-pc`` [general/gl072.cbl:L412-L413]. Omit the alignment
    and ``gl072`` divides zero, picks the wrong account and posts to it with no
    error and no diagnostic: the exact silent-misposting failure Agent Action Plan
    0.6.4 identifies as this table's headline risk.

    Aligning is EMULATION of shared storage, not added behaviour: it produces the
    state the frozen program already has, which is why it does not fall foul of
    rule R-3's ban on new validations or new fields.
    """

    #: The group view - ``WS-Ledger-Nos`` plus ``Ledger-PC`` - is authoritative.
    GROUP = "GROUP"

    #: The ``WS-Ledger-Key9`` redefinition is authoritative.
    REDEFINES = "REDEFINES"


#: Decimal scale factor between ``WS-Ledger-Nos`` and the whole eight-digit key:
#: ``Ledger-PC pic 9(2)`` [copybooks/wsledger.cob:L20] occupies the low two
#: digits, so the six digits of ``WS-Ledger-Nos`` sit two places up. This is the
#: same 100 that ``gl072`` divides by [general/gl072.cbl:L412].
_LEDGER_PC_SCALE: Final[int] = 100

#: Decimal scale factor between ``Ledger-n`` and ``WS-Ledger-Nos``:
#: ``Ledger-s pic 9(2)`` [copybooks/wsledger.cob:L18] occupies the low two digits
#: of the six, so ``Ledger-n pic 9(4)`` [:L17] sits two places up.
_LEDGER_S_SCALE: Final[int] = 100

#: Width of the shared key storage in characters - ``9(6)`` plus ``9(2)``, and
#: equally the ``9(8)`` of the redefinition. This is the ``8`` of the bridge's own
#: ``WS-Ledger-Record(1:8)`` reference modifier [common/nominalMT.cbl:L621].
_LEDGER_KEY_WIDTH: Final[int] = 8


def align_ledger_key_views(
    record: WsLedgerRecord, *, source: LedgerKeyView = LedgerKeyView.GROUP
) -> None:
    """Make every view of the shared eight key characters agree.

    ANOMALY N-REDEFINES-ALIAS - the emulation of REDEFINES storage sharing that
    :class:`LedgerKeyView` documents. Mutates ``record`` in place, as the COBOL
    ``MOVE`` it stands for does.

    With ``source=GROUP`` the redefinition is recomputed from the group::

        WS-Ledger-Key9 = WS-Ledger-Nos * 100 + Ledger-PC

    With ``source=REDEFINES`` the group is recomputed from the redefinition, and
    the inner ``Ledger-n`` / ``Ledger-s`` redefinition of ``WS-Ledger-Nos``
    [copybooks/wsledger.cob:L16-L18] is recomputed too - both directions,
    because that inner pair is a second level of sharing over the same six
    digits and ``gl030`` reads it.

    Every value is put through the record layer's own descriptors, so each view
    lands truncated to ITS OWN declared width exactly as a COBOL ``MOVE`` would,
    rather than being assigned raw.

    Args:
        record: The ``WS-Ledger-Record`` whose key views are to be aligned.
        source: Which view was written last. Defaults to
            :attr:`LedgerKeyView.GROUP` because every in-scope caller writes the
            group view; the sole writers of the redefinition are
            [general/gl030.cbl:L1626] and [:L2323], and ``gl030`` is out of scope
            per Agent Action Plan 0.2.2.
    """
    key = record.ws_ledger_key
    if source is LedgerKeyView.GROUP:
        # `WS-Ledger-Nos` is itself shared with `Ledger-n` / `Ledger-s`, so bring
        # that inner pair up first - a caller may have written either level.
        nos = WsLedgerKey.WS_LEDGER_NOS.store(key.ws_ledger_nos)
        key.ws_ledger_nos = nos
        parts = key.ws_ledger_nos_parts
        parts.ledger_n = WsLedgerNosParts.LEDGER_N.store(nos // _LEDGER_S_SCALE)
        parts.ledger_s = WsLedgerNosParts.LEDGER_S.store(nos % _LEDGER_S_SCALE)
        key.ledger_pc = WsLedgerKey.LEDGER_PC.store(key.ledger_pc)
        record.ws_ledger_key9.ws_ledger_key9 = WsLedgerKey9.WS_LEDGER_KEY9.store(
            nos * _LEDGER_PC_SCALE + key.ledger_pc
        )
        return
    # LedgerKeyView.REDEFINES - the fetch path. `bb100-UnloadHVs` has just done
    # `move HV-LEDGER-KEY to WS-Ledger-Key9` [common/nominalMT.cbl:L990] and
    # nothing else; without the rest of this, `gl072` reads zeros.
    key9 = WsLedgerKey9.WS_LEDGER_KEY9.store(record.ws_ledger_key9.ws_ledger_key9)
    record.ws_ledger_key9.ws_ledger_key9 = key9
    nos = WsLedgerKey.WS_LEDGER_NOS.store(key9 // _LEDGER_PC_SCALE)
    key.ws_ledger_nos = nos
    key.ledger_pc = WsLedgerKey.LEDGER_PC.store(key9 % _LEDGER_PC_SCALE)
    parts = key.ws_ledger_nos_parts
    parts.ledger_n = WsLedgerNosParts.LEDGER_N.store(nos // _LEDGER_S_SCALE)
    parts.ledger_s = WsLedgerNosParts.LEDGER_S.store(nos % _LEDGER_S_SCALE)


def ws_ledger_key_bytes(
    record: WsLedgerRecord, *, source: LedgerKeyView = LedgerKeyView.GROUP
) -> str:
    """Return the eight characters of ``WS-Ledger-Record(1:8)``.

    Every ``WHERE`` clause the bridge builds keys off this reference modifier,
    e.g. ``WS-Ledger-Record(1:8)`` at [common/nominalMT.cbl:L621] on the
    read-indexed path and [:L829] on the delete path. Because the key is
    ``DISPLAY`` usage - ``9(6)`` plus ``9(2)`` [copybooks/wsledger.cob:L14, :L20]
    - those eight characters ARE the eight zero-padded decimal digits, so the
    value the modifier yields is a STRING such as ``"01234567"`` and not an
    integer. :mod:`acas_posting.dal.cursor_state` takes it in that form, and
    :data:`cursor_state.SEQUENTIAL_READ_START` states its low key the same way,
    as ``"00000000"``.

    Aligns the views first, so the caller cannot accidentally read a stale
    redefinition; see :func:`align_ledger_key_views`.

    Args:
        record: The ``WS-Ledger-Record`` to take the key from.
        source: Which view was written last, passed through to
            :func:`align_ledger_key_views`.

    Returns:
        Exactly eight decimal digits, zero-padded on the left.
    """
    align_ledger_key_views(record, source=source)
    return f"{record.ws_ledger_key9.ws_ledger_key9:0{_LEDGER_KEY_WIDTH}d}"


def _align_quarter_views(record: WsLedgerRecord) -> None:
    """Refresh ``Ledger-Q occurs 4`` from the four named quarter fields.

    The second REDEFINES in this record::

        03  Quarters.                               [copybooks/wsledger.cob:L30]
            05  Ledger-Q1 ... Ledger-Q4             [:L31-L34]
        03  filler redefines Quarters.              [:L35]
            05  Ledger-Q  pic s9(8)v99 comp-3
                                   occurs 4.        [:L36]

    ``Quarters`` is the storage-allocating declaration and the four named fields
    are what the bridge loads from and unloads to [common/nominalMT.cbl:L969-L972,
    :L997-L1000]; the table is a subscripted view of the same storage, and it is
    the view ``gl080`` indexes when it rotates the quarters. Keeping them in step
    is the same emulation :func:`align_ledger_key_views` performs for the key, for
    the same reason.

    Note the bridge correctly emits NO column for ``Ledger-Q``: it is the same
    storage as ``Q1``..``Q4``, so a column would double-count it. That omission is
    deliberate and is recorded as such in this module's docstring (rule R-5).

    Args:
        record: The ``WS-Ledger-Record`` whose quarter views are to be aligned.
    """
    quarters = record.quarters
    record.quarters_table.ledger_q = (
        quarters.ledger_q1,
        quarters.ledger_q2,
        quarters.ledger_q3,
        quarters.ledger_q4,
    )


#  BB000-HV-LOAD AND BB100-UNLOADHVS  -  THE TWO-PARAGRAPH CONVENTION

def _store_hv(binding: ColumnBinding, value: object) -> int | str | Decimal:
    """Perform the COBOL ``MOVE`` into ``binding``'s host variable.

    The receiving field's geometry comes ENTIRELY from the data dictionary - the
    picture, digits, scale, sign and character length recorded for the bridge's
    own declaration - never from a width read off the source by eye. Agent Action
    Plan 0.8.1 makes that a directive: "every Python field definition cites its
    entry. This ordering is a directive, not a preference - it is what prevents
    fields being transcribed by eye."

    COBOL ``MOVE`` rules applied, by receiving category:

    * Numeric integer - align on the decimal point, so an oversized value loses
      its HIGH-ORDER digits, and an unsigned receiving field stores the absolute
      value. ``HV-LEDGER-KEY`` is ``9(10)`` against a ``9(8)`` source, so the
      widening is loss-free; the truncation is coded because the receiving field's
      width says so, not because a caller is expected to overflow it.
    * Numeric with scale - truncate excess decimals TOWARD ZERO. Agent Action Plan
      0.1.1: "COBOL ``COMPUTE`` truncates toward zero on store unless ``ROUNDED``
      is written", and there is no ``ROUNDED`` anywhere on this path, so
      ``ROUND_DOWN`` is right and rule R-2 keeps it in :class:`~decimal.Decimal`.
    * Alphanumeric - left-justify, pad right with spaces, truncate on the right.
      This is where ANOMALY A-12 happens: a 24-character source
      [copybooks/wsledger.cob:L27] into a 32-character receiving field
      [common/nominalMT.cbl:L299] keeps the value and APPENDS EIGHT SPACES.

    Args:
        binding: The column whose host variable receives the value.
        value: The value moved from the copybook field.

    Returns:
        The value as the host variable would hold it.

    Raises:
        ValueError: If the dictionary describes a storage class this table does
            not use. A build error: the eleven columns are ``INT``, ``STR`` and
            ``DECIMAL`` only.
    """
    storage = binding.python_storage
    if storage == "STR":
        # Alphanumeric MOVE: left-justify, space-pad, truncate right.
        # ANOMALY A-12, WRITE DIRECTION, for `LEDGER-NAME`
        # [copybooks/wsledger.cob:L27] -> [common/nominalMT.cbl:L299]: 24 -> 32
        # keeps the value and appends eight spaces. NOT right-stripped here - the
        # bridge's own `FUNCTION TRIM (...,TRAILING)` does that later, when it
        # builds the literal [common/nominalMT.cbl:L1067], and reproducing the
        # PAD-THEN-TRIM sequence rather than short-circuiting it is what keeps the
        # anomaly visible at its own site.
        width = binding.hv_character_length
        if width is None:
            raise ValueError(f"{binding.hv_name} is STR storage with no character length")
        text = "" if value is None else str(value)
        return text[:width].ljust(width)
    if storage == "INT":
        digits = binding.hv_digits
        if digits is None:
            raise ValueError(f"{binding.hv_name} is INT storage with no digit count")
        number = int(value)  # type: ignore[arg-type]
        # High-order truncation to the receiving field's digit count, then the
        # unsigned receiving field stores the magnitude. All three integer host
        # variables here are unsigned [common/nominalMT.cbl:L295-L298].
        truncated = abs(number) % (10**digits)
        return truncated if not binding.hv_signed else truncated * (1 if number >= 0 else -1)
    if storage == "DECIMAL":
        digits, scale = binding.hv_digits, binding.hv_scale
        if digits is None or scale is None:
            raise ValueError(f"{binding.hv_name} is DECIMAL storage with no digits or scale")
        with decimal.localcontext(transport_decimal_context()):
            amount = Decimal(value)  # type: ignore[arg-type]
            # Excess decimals are discarded toward zero - never rounded.
            quantised = amount.quantize(Decimal(1).scaleb(-scale), rounding=decimal.ROUND_DOWN)
            # High-order truncation: keep the low `digits` digits of the scaled
            # integer, preserving the sign if the field is signed.
            units = int(quantised.scaleb(scale))
            kept = abs(units) % (10**digits)
            if binding.hv_signed and units < 0:
                kept = -kept
            return Decimal(kept).scaleb(-scale)
    raise ValueError(f"{binding.column_name} has unsupported storage {storage!r}")


def bridge_character_literal(value: str) -> str:
    """Return the character value the bridge's SQL literal DENOTES.

    Reproduces ``FUNCTION TRIM (HV-LEDGER-NAME,TRAILING)``
    [common/nominalMT.cbl:L1067] on the ``INSERT`` path and [:L1245] on the
    ``UPDATE`` path, and the same form for ``HV-LEDGER-PLACE`` at [:L1046] and
    [:L1225].

    ``TRAILING`` is explicit in all four places, so LEADING SPACES ARE PRESERVED -
    a distinction that matters because plain ``FUNCTION TRIM`` would strip both
    ends and silently left-shift an indented name. Read out of the frozen bridge
    rather than assumed.

    This is the second half of ANOMALY A-12 and the reason the anomaly is not
    visible in a dump of freshly written rows: :func:`_store_hv` pads a
    24-character name out to 32 [common/nominalMT.cbl:L299], and this trim removes
    exactly those trailing spaces again before the value reaches the column. The
    LIVE half of A-12 is the read direction, where :func:`bb100_unload_hvs` moves a
    32-character column value back into the 24-character copybook field and
    TRUNCATES it - see there.

    Args:
        value: The host variable's character content.

    Returns:
        The value with trailing spaces removed and leading spaces intact.
    """
    return value.rstrip(" ")


def bb000_hv_load(
    ledger: WsLedgerRecord,
    host_variables: TdGlledgerRec | None = None,
    *,
    key_view: LedgerKeyView = LedgerKeyView.GROUP,
) -> TdGlledgerRec:
    """``bb000-HV-Load Section.`` [common/nominalMT.cbl:L953], body [:L961-L972].

    "move WS-Ledger-Record fields to HV fields" - the maintainer's own summary at
    the ``PERFORM`` site [common/nominalMT.cbl:L794]. Performed on the write path
    at [:L794] and on the re-write path at [:L877] ("Load up the HV fields from
    table record in WS"), and on neither read path.

    The maintainer's closing note, verbatim [common/nominalMT.cbl:L974-L975]:
    "Loading HVs implies a non-Fetch action. RGs are handled separately for all
    such actions so they must not be loaded here."

    Statement order is the FROZEN ORDER, which is not the column order::

        initialize TD-GLLEDGER-REC.                                    [:L961]
        move WS-Ledger-Key9  to HV-LEDGER-KEY.                         [:L962]
        move Ledger-Type     to HV-LEDGER-TYPE                         [:L963]
        move Ledger-Place    to HV-LEDGER-PLACE                        [:L964]
        move Ledger-Name     to HV-LEDGER-NAME                         [:L965]  <-- NAME
        move Ledger-Level    to HV-LEDGER-LEVEL                        [:L966]  <-- then LEVEL
        move Ledger-Balance  to HV-LEDGER-BALANCE                      [:L967]
        move Ledger-Last     to HV-LEDGER-LAST                         [:L968]
        move Ledger-Q1 .. Q4 to HV-LEDGER-Q1 .. Q4                     [:L969-L972]

    ANOMALY N-LOADORDER - REPRODUCED, NOT FIXED. ``Ledger-Name`` is moved BEFORE
    ``Ledger-Level`` [common/nominalMT.cbl:L965-L966] although the host-variable
    group [:L298-L299] and the frozen schema [mysql/ACASDB.sql:L125-L127] both
    declare ``LEDGER-LEVEL`` first. The order is preserved by iterating
    :data:`HV_LOAD_ORDER`; the COLUMN order is preserved separately by the
    statement builders, which iterate :data:`COLUMN_BINDINGS`. Reordering either to
    agree with the other would be a defect fixed, which rule R-4 makes a failure.
    Here the divergence is harmless because the moves are independent - but that is
    an observation about this bridge, not a licence to normalise it.

    Args:
        ledger: The ``WS-Ledger-Record`` to load from.
        host_variables: The group to fill. A new one is built when omitted; the
            COBOL reuses a single working-storage group, and passing it in models
            that faithfully for a caller that wants to inspect it afterwards.
        key_view: Which key view the caller wrote last, passed through to
            :func:`align_ledger_key_views`. Defaults to
            :attr:`LedgerKeyView.GROUP` because every in-scope caller writes the
            group view, e.g. [general/gl072.cbl:L405].

    Returns:
        The filled host-variable group.
    """
    group = TdGlledgerRec() if host_variables is None else host_variables
    # `initialize TD-GLLEDGER-REC.` [common/nominalMT.cbl:L961] - FIRST, and the
    # reason no bind is ever NULL. Agent Action Plan 0.6.2: "each load paragraph
    # begins by initialising the host-variable group, so unset fields become zero
    # or space rather than SQL NULL".
    group.initialize()
    # `move WS-Ledger-Key9 to HV-LEDGER-KEY` [:L962] reads the REDEFINES view, so
    # the shared storage must be coherent first; in COBOL it always is.
    # ANOMALY N-REDEFINES-ALIAS - see `align_ledger_key_views`.
    align_ledger_key_views(ledger, source=key_view)
    for column_name in HV_LOAD_ORDER:
        binding = COLUMN_BINDINGS_BY_NAME[column_name]
        setattr(group, binding.hv_attribute, _store_hv(binding, _record_value(ledger, binding)))
    return group


def _record_value(ledger: WsLedgerRecord, binding: ColumnBinding) -> object:
    """Read ``binding``'s copybook field out of ``ledger``.

    Walks the dotted :attr:`ColumnBinding.record_attribute` path, which exists
    because two of the eleven fields are not top-level attributes: the key is
    reached through a REDEFINES [copybooks/wsledger.cob:L21-L22] and the quarters
    sit inside a group [:L30-L34].

    Args:
        ledger: The record to read from.
        binding: The column whose copybook field is wanted.

    Returns:
        The field's current value.
    """
    target: object = ledger
    for attribute in binding.record_attribute.split("."):
        target = getattr(target, attribute)
    return target


def _set_record_value(ledger: WsLedgerRecord, binding: ColumnBinding, value: object) -> None:
    """Write ``value`` into ``binding``'s copybook field on ``ledger``.

    The inverse of :func:`_record_value`, and the point at which the value passes
    through the RECORD LAYER's descriptor - so it lands truncated to the
    COPYBOOK's declared width, which is what makes ANOMALY A-12 truncate on the
    read path.

    Args:
        ledger: The record to write into.
        binding: The column whose copybook field receives the value.
        value: The value moved from the host variable.
    """
    path = binding.record_attribute.split(".")
    target: object = ledger
    for attribute in path[:-1]:
        target = getattr(target, attribute)
    descriptor = _COPYBOOK_DESCRIPTORS[binding.dictionary_key]
    setattr(target, path[-1], descriptor.store(value))


def _initialize_ws_ledger_record(ledger: WsLedgerRecord) -> None:
    """``initialize WS-Ledger-Record.`` [common/nominalMT.cbl:L989].

    The first statement of ``bb100-UnloadHVs``, and it does NOT do what a reader
    might assume. Settled against the compiled oracle, which rule R-6 makes the
    tie-breaker: a 126-byte record pre-filled with ``"X"`` then put through
    ``initialize WS-Ledger-Record`` under GnuCOBOL 3.2.0 comes back with

    * every NAMED item reset - ``WS-Ledger-Nos`` to ``000000``, ``Ledger-PC`` to
      ``00``, ``Ledger-Type`` and ``Ledger-Level`` to ``0``, ``Ledger-Place`` to a
      space, ``Ledger-Name`` to 24 spaces, and every ``COMP-3`` money field to
      ``+00000000.00``;
    * every REDEFINES view reset AS A CONSEQUENCE of shared storage -
      ``WS-Ledger-Key9`` to ``00000000``, ``Ledger-n``/``Ledger-s`` to zeros, and
      ``Ledger-Q(1)`` to ``+00000000.00``;
    * BOTH ``FILLER`` ITEMS UNTOUCHED, still holding ``"X"``. The eight-character
      probe ``WS-Ledger-Record(11:5)`` returned ``"0XXXX"`` - character 11 is
      ``Ledger-Level``, reset to ``"0"``, and characters 12..15 are the
      ``filler pic x(5)`` [copybooks/wsledger.cob:L26], still ``"XXXX"`` - and the
      fifty-character probe over ``filler pic x(50)`` [:L37] returned fifty ``X``.

    That is the COBOL standard's rule - ``INITIALIZE`` excludes ``FILLER`` - and it
    is reproduced rather than tidied. It has no effect on any table dump, because
    neither filler has a column, but it does decide what a caller sees in the 55
    filler bytes after a read, so getting it wrong would be a behaviour change.

    Args:
        ledger: The record to initialize in place.
    """
    key = ledger.ws_ledger_key
    key.ws_ledger_nos = 0
    key.ledger_pc = 0
    key.ws_ledger_nos_parts.ledger_n = 0
    key.ws_ledger_nos_parts.ledger_s = 0
    ledger.ws_ledger_key9.ws_ledger_key9 = 0
    ledger.ledger_type = 0
    ledger.ledger_place = " "
    ledger.ledger_level = 0
    ledger.ledger_name = " " * 24
    ledger.ledger_balance = Decimal("0.00")
    ledger.ledger_last = Decimal("0.00")
    quarters = ledger.quarters
    quarters.ledger_q1 = Decimal("0.00")
    quarters.ledger_q2 = Decimal("0.00")
    quarters.ledger_q3 = Decimal("0.00")
    quarters.ledger_q4 = Decimal("0.00")
    _align_quarter_views(ledger)
    # `filler pic x(5)` [copybooks/wsledger.cob:L26] and `filler pic x(50)` [:L37]
    # are DELIBERATELY NOT reset - see the docstring's oracle evidence.


def bb100_unload_hvs(host_variables: TdGlledgerRec, ledger: WsLedgerRecord) -> None:
    """``bb100-UnloadHVs Section.`` [common/nominalMT.cbl:L980], body [:L989-L1000].

    The fetch half of the two-paragraph convention: host variables back into the
    record. Performed at [common/nominalMT.cbl:L586] on the read-next path and at
    [:L684] on the read-indexed path, and on neither write path.

    The maintainer's note on why no indicator variables are needed, verbatim
    [common/nominalMT.cbl:L986-L987]: "NULL fields must not be returned in the
    buffer. SQL filters each column to ensure it has a proper value. This saves
    using indicator variables."

    Statement order is again the FROZEN ORDER, with the SAME inversion as the load
    - ``HV-LEDGER-NAME`` at [:L993] before ``HV-LEDGER-LEVEL`` at [:L994] - which
    is what shows ANOMALY N-LOADORDER is a consistent habit of the generator rather
    than a slip on one line::

        initialize WS-Ledger-Record.                                   [:L989]
        move HV-LEDGER-KEY   to WS-Ledger-Key9                         [:L990]
        move HV-LEDGER-TYPE  to Ledger-Type                            [:L991]
        move HV-LEDGER-PLACE to Ledger-Place                           [:L992]
        move HV-LEDGER-NAME  to Ledger-Name                            [:L993]  <-- NAME
        move HV-LEDGER-LEVEL to Ledger-Level                           [:L994]  <-- then LEVEL
        move HV-LEDGER-BALANCE .. HV-LEDGER-Q4 to their fields         [:L995-L1000]

    ANOMALY A-12, READ DIRECTION - REPRODUCED, NOT FIXED. ``HV-LEDGER-NAME`` is 32
    characters [common/nominalMT.cbl:L299] and ``Ledger-Name`` is 24
    [copybooks/wsledger.cob:L27], so this move SILENTLY TRUNCATES the last eight.
    The column is ``char(32)`` [mysql/ACASDB.sql:L127], so a row whose name exceeds
    24 characters - which the schema permits and this handler can be handed - loses
    the excess with no error and no diagnostic. This is the LIVE half of A-12: the
    write direction's pad is undone by the bridge's own ``TRIM``
    (see :func:`bridge_character_literal`), but nothing undoes this. Widening
    ``Ledger-Name`` to 32 to "fix" it would change the record layout, which rule
    R-3 forbids, and would be a defect fixed, which rule R-4 makes a failure.

    ANOMALY N-REDEFINES-ALIAS - REPRODUCED. [:L990] writes ONLY
    ``WS-Ledger-Key9``, the REDEFINES view. In COBOL the group view updates for
    free because it is the same storage; in Python it must be aligned explicitly,
    and if it is not then ``gl072`` divides zero
    [general/gl072.cbl:L412-L413] and posts to the wrong account with no
    diagnostic. The alignment below is that emulation.

    Args:
        host_variables: The group just filled by a fetch.
        ledger: The ``WS-Ledger-Record`` to unload into, mutated in place exactly
            as the COBOL ``MOVE`` statements mutate working storage.
    """
    _initialize_ws_ledger_record(ledger)
    for column_name in HV_UNLOAD_ORDER:
        binding = COLUMN_BINDINGS_BY_NAME[column_name]
        _set_record_value(ledger, binding, getattr(host_variables, binding.hv_attribute))
    # [:L990] wrote the redefinition; bring the group view and the inner
    # `Ledger-n` / `Ledger-s` pair up with it. ANOMALY N-REDEFINES-ALIAS.
    align_ledger_key_views(ledger, source=LedgerKeyView.REDEFINES)
    # [:L997-L1000] wrote the four named quarters; bring `Ledger-Q occurs 4` up
    # with them, the second REDEFINES in this record
    # [copybooks/wsledger.cob:L35-L36].
    _align_quarter_views(ledger)


#  COMMAND EXECUTION  -  MYSQL-1210-COMMAND, AND THE SILENT-STATUS ANOMALIES

class CobolFileAccessNotMigratedError(AcasFileHandlerError):
    """Raised when a caller asks for the ISAM path, which is NOT migrated.

    ``acas005`` is two handlers in one program. ``aa-Process-Flat-File Section.``
    [common/acas005.cbl:L277] drives GnuCOBOL indexed (ISAM) files, and
    ``ba-Process-RDBMS section.`` [:L586] drives MySQL through the bridge; the
    choice is made by ``if not FS-Cobol-Files-Used`` [:L316], which routes to the
    RDBMS section and returns [:L318-L319].

    Only the RDBMS path is in scope. Agent Action Plan 0.2.1.1 puts the twenty
    ``*MT`` bridge pairs and the seventeen handlers in scope as the specification
    for SQL against the frozen schema, and 0.2.2 admits no indexed-file store: the
    migration targets "SQL against the frozen schema", and the shipped package has
    no ISAM engine and, per rule R-1, no COBOL runtime to borrow one from.

    So the ``aa0NN`` paragraphs below are reproduced FAITHFULLY for everything they
    decide - the log identity, the key guard, the dispatch order, the status codes,
    the record movement - and raise this where the COBOL would issue the ISAM verb
    itself. The disposition mirrors the frozen source's own reaction to a situation
    it cannot serve: ``move 901 to WE-Error`` with ``FS-Reply`` 99 and a message
    telling the operator to stop and fix the source
    [common/acas005.cbl:L612-L613], reported here as ``(99, 901)``.

    Raising rather than returning a status is deliberate. A silent failure here
    would look exactly like anomaly N-REWRITE-SILENT to a caller, and inventing a
    new silent path would be a behaviour change; an exception cannot be mistaken
    for data.
    """

    def __init__(self, file_function: int, *, access_type: int = 0) -> None:
        """Build the error for a specific verb.

        Args:
            file_function: The ``File-Function`` the caller asked for.
            access_type: The ``Access-Type`` the caller asked for, when relevant.
        """
        super().__init__(
            FsReply.ERROR,
            WeError.RECORD_SIZE_MISMATCH,
            operation=(
                f"File-Function {file_function} Access-Type {access_type} on the "
                f"Cobol indexed-file path of {HANDLER_NAME}, which is not migrated "
                f"[common/acas005.cbl:L277]"
            ),
            table=TABLE_NAME,
        )
        #: The verb asked for, kept so a caller can report it.
        self.file_function = file_function
        #: The access type asked for, kept for the same reason.
        self.access_type = access_type


@dataclass(frozen=True, slots=True)
class CommandOutcome:
    """The result of one SQL command, in the bridge's own terms.

    Carries the ``(FS-Reply, We-Error)`` pair the bridge would leave behind plus
    the row count it read, and - critically - WHETHER IT WROTE THE PAIR AT ALL.

    That last flag is not fastidiousness. Two of this bridge's paragraphs can
    return having written NEITHER status field, leaving whatever the caller passed
    in; see :attr:`status_written` and the two anomalies it records.
    """

    #: ``FS-Reply`` [copybooks/wsfnctn.cob:L36] as the paragraph left it.
    fs_reply: int

    #: ``We-Error`` [copybooks/wsfnctn.cob:L27] as the paragraph left it.
    we_error: int

    #: ``WS-Mysql-Count-Rows``, from ``MySQL_affected_rows``
    #: [copybooks/mysql-procedures.cpy:L178] after a command, or
    #: ``MySQL_num_rows`` [:L191-L192] after a store.
    count_rows: int

    #: The statement text, identifiers already quoted, values as ``%s``
    #: placeholders. Kept for logging and for the traceability evidence.
    statement: str

    #: The bound values, in placeholder order.
    parameters: tuple[object, ...]

    #: ``SQL-State`` [copybooks/wsfnctn.cob:L54] when the driver reported one.
    sql_state: str = ""

    #: ``SQL-Err`` [copybooks/wsfnctn.cob:L53] when the driver reported one.
    sql_err: str = ""

    #: ``SQL-Msg`` [copybooks/wsfnctn.cob:L55] when the driver reported one.
    sql_msg: str = ""

    #: Whether ``FS-Reply`` and ``We-Error`` were actually SET.
    #:
    #: ANOMALY N-REWRITE-SILENT and ANOMALY N-DELETE-SILENT - REPRODUCED, NOT
    #: FIXED. ``ba090-Process-Rewrite`` [common/nominalMT.cbl:L876] and
    #: ``ba080-Process-Delete`` [:L820] both test ``WS-Mysql-Count-Rows not = 1``
    #: and, when the count is wrong but the driver reported NO error, ``go to
    #: ba999-End`` - jumping PAST the ``move zero to FS-Reply WE-Error`` that sits
    #: at the end of each paragraph [:L873, :L914]. The caller's incoming pair is
    #: therefore returned unchanged, so a re-write or delete that matched no row
    #: reports whatever the previous operation reported - success, very often.
    #:
    #: ``ba070-Process-Write`` does NOT share the defect, because it zeroes the
    #: pair BEFORE the insert [:L796] rather than after it. That asymmetry is the
    #: evidence the omission is an accident rather than an idiom, and it is exactly
    #: why this flag exists instead of a comment.
    status_written: bool = True

    def apply_to(self, file_access: FileAccess) -> None:
        """Write this outcome into ``File-Access``, honouring :attr:`status_written`.

        When :attr:`status_written` is false NEITHER ``fs_reply`` NOR ``we_error``
        is copied, which is precisely the silent behaviour of N-REWRITE-SILENT and
        N-DELETE-SILENT. The diagnostic fields are still copied, because the
        paragraphs that skip the status pair do reach the ``move spaces to SQL-Err
        SQL-Msg SQL-State`` in their success tail [common/nominalMT.cbl:L868-L871].

        Args:
            file_access: The block to update in place.
        """
        if self.status_written:
            file_access.fs_reply = self.fs_reply
            file_access.we_error = self.we_error
        logging_data = file_access.logging_data
        logging_data.sql_err = self.sql_err
        logging_data.sql_msg = self.sql_msg
        logging_data.sql_state = self.sql_state
        logging_data.ws_count_rows = self.count_rows


def _mysql_1210_command(
    connection: object,
    statement: str,
    parameters: Sequence[object],
    *,
    we_error: int = WeError.SUCCESS,
    file_function: int = 0,
) -> CommandOutcome:
    """``Mysql-1210-Command.`` [copybooks/mysql-procedures.cpy:L164-L178].

    The one live route every non-fetch statement in this bridge takes. Three
    statements, in this order::

        call "MySQL_query" using WS-Mysql-Command.                     [:L165]
        if Return-Code not = zero
           perform Mysql-1100-Db-Error Thru Mysql-1190-Exit            [:L176]
        end-if
        call "MySQL_affected_rows" using WS-Mysql-Count-Rows.          [:L178]

    Two details of that order are load-bearing and are reproduced exactly:

    * the row count is read UNCONDITIONALLY, AFTER the error handling - so a failed
      statement still updates ``WS-Mysql-Count-Rows``, and the callers that test
      ``not = 1`` are testing a count taken after a failure as readily as after a
      success;
    * everything between [:L167] and [:L175] is commented out - the lock-retry
      ladder - so a lock error takes the SAME path as any other error. See the
      deliberate-omission note in this module's import block.

    ``MySQL_affected_rows`` counts rows CHANGED rather than rows MATCHED, because
    ``dal/connection.py`` does not negotiate ``CLIENT_FOUND_ROWS``. That is the
    driver default the frozen bridge's C interface also gets, so a re-write that
    stores identical values reports zero - which is one way the silent-status
    anomalies above actually fire.

    Args:
        connection: The open connection.
        statement: The statement, identifiers already quoted by
            :func:`quote_identifier`, values as ``%s``.
        parameters: The values to bind, in placeholder order.
        we_error: The ``We-Error`` to carry into the error handler, matching the
            value the calling paragraph had set.
        file_function: The ``File-Function`` in play, so
            :func:`status.override_we_error_for_operation`-style per-verb codes can
            be applied by the caller.

    Returns:
        The outcome, with ``count_rows`` filled whether or not the command failed.
    """
    bound = tuple(parameters)
    #  THE STATEMENT IS NOT LOGGED. It used to be, redacted - and redaction cannot
    #  help here, because what leaks is not an identity shape the rules recognise
    #  but the statement itself: an `UPDATE ... SET` over `GLLEDGER-REC` names every
    #  column of the nominal ledger row, and a `WHERE` clause names the account
    #  being posted to (CWE-532). The bound parameters are not logged for the same
    #  reason. A failed statement is reported once, with typed fields, by
    #  `dal/status.py`'s `mysql_1100_db_error`, which is enough to identify the
    #  fault; the statement text belongs to a debugger, not to an operator log.
    try:
        with execute_statement(connection, statement, bound) as cursor:  # type: ignore[arg-type]
            # `MySQL_affected_rows` [copybooks/mysql-procedures.cpy:L178] - read
            # unconditionally, and read here because the cursor owns it.
            count_rows = int(getattr(cursor, "rowcount", 0) or 0)
    except Exception as error:  # noqa: BLE001 - the bridge tests a return code, not a type
        # `if Return-Code not = zero / perform Mysql-1100-Db-Error` [:L166, :L176].
        errno = str(getattr(error, "errno", "") or "")
        sql_state = str(getattr(error, "sqlstate", "") or "")
        message = str(getattr(error, "msg", None) or error)
        status = mysql_1100_db_error(
            errno=errno,
            message=message,
            sql_state=sql_state,
            command=statement,
            we_error=we_error,
        )
        return CommandOutcome(
            fs_reply=status.fs_reply,
            we_error=status.we_error,
            # The count is still read after an error [:L178]; a failed statement
            # affected no rows, so zero is what the driver reports.
            count_rows=0,
            statement=statement,
            parameters=bound,
            sql_state=status.sql_state,
            sql_err=status.sql_err,
            sql_msg=status.sql_msg,
        )
    return CommandOutcome(
        fs_reply=FsReply.SUCCESS,
        we_error=WeError.SUCCESS,
        count_rows=count_rows,
        statement=statement,
        parameters=bound,
    )


def _bind_value(binding: ColumnBinding, host_variables: TdGlledgerRec) -> object:
    """Return the value ``binding``'s SQL literal denotes, ready to bind.

    Routes every column through the transformation the bridge applies when it
    builds the literal, so what is bound is what the frozen statement would have
    said:

    * money columns through :func:`bridge_money_literal`, which LOSES THE SIGN -
      ANOMALY N-SIGNLOSS;
    * integer columns through the same edit mask, which loses nothing because their
      host variables are unsigned;
    * character columns through :func:`bridge_character_literal`, which strips
      TRAILING spaces only.

    No value is ever ``None``. Every column of ``GLLEDGER-REC`` is ``NOT NULL``
    [mysql/ACASDB.sql:L123-L133] and ``bb000-HV-Load``'s leading ``initialize``
    [common/nominalMT.cbl:L961] guarantees a zero or a space instead. Agent Action
    Plan 0.6.2: "the Python layer must default rather than omit."

    Args:
        binding: The column being bound.
        host_variables: The loaded host-variable group.

    Returns:
        The value to bind - ``int``, ``str`` or :class:`~decimal.Decimal`, never
        ``None`` and never a binary float.
    """
    value = getattr(host_variables, binding.hv_attribute)
    if binding.python_storage == "DECIMAL":
        return bridge_money_literal(value)
    if binding.python_storage == "INT":
        return _bridge_integer_literal(
            value,
            _EDIT_KEY_SLICE if binding.primary_key else _EDIT_SMALL_INT_SLICE,
        )
    return bridge_character_literal(value)


#  BB200-INSERT AND BB300-UPDATE  -  THE TWO STATEMENT BUILDERS

#: The ``WHERE`` clause every keyed statement in this bridge uses, built once.
#:
#: The bridge assembles it into ``WS-Where`` from the key table
#: [common/nominalMT.scb:L244-L262] and then appends
#: ``FUNCTION TRIM (WS-Where (1:J))`` [common/nominalMT.cbl:L1356]. With
#: ``occurs 1`` there is exactly ONE key of reference, the primary
#: [common/nominalMT.scb:L250], so the clause is always this single equality and
#: never a composite.
_WHERE_BY_KEY: Final[str] = f"{quote_identifier(KEY_OF_REFERENCE.column_name)} = %s"


def _set_clause() -> str:
    """Build the ``SET`` list shared by ``bb200-Insert`` and ``bb300-Update``.

    Eleven assignments in TABLE-ORDINAL order, separated by ``', '`` exactly as the
    bridge's ``STRING ', '`` separators produce
    [common/nominalMT.cbl:L1043-L1044 and passim].

    Every identifier goes through :func:`quote_identifier`. That is not optional
    styling: EVERY name in this table contains a HYPHEN - the table itself and all
    eleven columns [mysql/ACASDB.sql:L122-L134] - and MySQL parses an unquoted
    ``LEDGER-KEY`` as ``LEDGER`` minus ``KEY``, so an unquoted statement is a syntax
    error rather than a subtly wrong one. The frozen bridge writes the backticks
    into its own literals [:L1015, :L1020] for the same reason.

    Values are ``%s`` placeholders rather than interpolated literals. The frozen
    bridge interpolates, because ``STRING`` is all it has;
    :mod:`acas_posting.dal.cursor_state` takes the same trade for the same reason,
    on the ground that interpolation is transport and a bound parameter yields the
    same logical predicate while removing an injection route the frozen source left
    open. What must be preserved across that trade is the VALUE the literal denotes,
    and :func:`_bind_value` is what preserves it - including the sign loss.

    Returns:
        The ``SET`` list, e.g. ``` `LEDGER-KEY` = %s, `LEDGER-TYPE` = %s, ... ```.
    """
    return ", ".join(
        f"{quote_identifier(binding.column_name)} = %s" for binding in COLUMN_BINDINGS
    )


#: The ``SET`` list, built once at import so two processes agree on it byte for
#: byte - the determinism rule R-6 asks for, and cheap to assert in a test.
SET_CLAUSE: Final[str] = _set_clause()

#: ``INSERT INTO `GLLEDGER-REC` SET ...`` [common/nominalMT.cbl:L1015-L1017].
#:
#: MySQL's ``INSERT ... SET`` form, not ``INSERT ... VALUES`` - the bridge's own
#: choice, preserved. All ELEVEN columns are named, always, because all eleven are
#: ``NOT NULL`` [mysql/ACASDB.sql:L123-L133] and the bridge's leading
#: ``initialize`` [:L961] means it always has a value for each.
#:
#: The trailing ``";"`` [:L1173] is kept; the trailing ``X"00"`` [:L1175] is not -
#: that is the NUL that terminates a C string for the ``MySQL_query`` interface,
#: framing rather than statement content, and the Python driver frames its own.
INSERT_STATEMENT: Final[str] = (
    f"INSERT INTO {quote_identifier(TABLE_NAME)} SET {SET_CLAUSE};"
)

#: ``UPDATE `GLLEDGER-REC` SET ... WHERE ...`` [common/nominalMT.cbl:L1194-L1196,
#: :L1353-L1357].
#:
#: The ``SET`` list is the SAME eleven columns, INCLUDING THE PRIMARY KEY, which the
#: statement then also matches on. Assigning a key column its own current value is
#: redundant but harmless, and it is what the bridge does; trimming the key out of
#: the ``SET`` list would change the statement and, through
#: ``MySQL_affected_rows``, could change the row count the caller tests.
UPDATE_STATEMENT: Final[str] = (
    f"UPDATE {quote_identifier(TABLE_NAME)} SET {SET_CLAUSE} WHERE {_WHERE_BY_KEY};"
)

#: ``DELETE FROM `GLLEDGER-REC` WHERE ...`` [common/nominalMT.cbl:L843-L849].
#:
#: NOTE THE ABSENCE OF A TRAILING SEMICOLON. ``ba080-Process-Delete`` appends only
#: ``X"00"`` [:L851-L852] where ``bb200-Insert`` [:L1173] and ``bb300-Update``
#: [:L1359] both append ``";"`` first. MySQL accepts either, so the inconsistency
#: has no effect - but it is the frozen text, and reproducing it costs nothing
#: while normalising it would be an unforced edit to behaviour-adjacent output.
DELETE_STATEMENT: Final[str] = f"DELETE FROM {quote_identifier(TABLE_NAME)} WHERE {_WHERE_BY_KEY}"


def bb200_insert(
    connection: object, host_variables: TdGlledgerRec, *, we_error: int = WeError.SUCCESS
) -> CommandOutcome:
    """``bb200-Insert Section.`` [common/nominalMT.cbl:L1005-L1178].

    Emitted from the ``/MYSQL INSERT\\ ... TABLE=GLLEDGER-REC`` directive
    [common/nominalMT.cbl:L1008-L1012]. Builds the eleven-column ``INSERT ... SET``
    and performs ``MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT`` [:L1177].

    Values are bound in TABLE-ORDINAL order, which is the order the bridge emits
    them - ``LEDGER-KEY`` [:L1020], ``LEDGER-TYPE`` [:L1031], ``LEDGER-PLACE``
    [:L1044], ``LEDGER-LEVEL`` [:L1053], ``LEDGER-NAME`` [:L1065],
    ``LEDGER-BALANCE`` [:L1074], ``LEDGER-LAST``, then ``LEDGER-Q1`` through
    ``LEDGER-Q4`` [:L1162]. Note this is NOT the order ``bb000-HV-Load`` filled the
    group in; see ANOMALY N-LOADORDER on :data:`HV_LOAD_ORDER`.

    ANOMALY N-SIGNLOSS applies to all six money columns here, via
    :func:`_bind_value`.

    Args:
        connection: The open connection.
        host_variables: The group filled by :func:`bb000_hv_load`.
        we_error: The ``We-Error`` in force, carried into the error handler.

    Returns:
        The command outcome. ``count_rows`` is 1 on a successful single-row insert;
        the caller compares it against 1 and maps a duplicate key to ``FS-Reply``
        22 - see :func:`ba070_process_write`.
    """
    parameters = tuple(_bind_value(binding, host_variables) for binding in COLUMN_BINDINGS)
    return _mysql_1210_command(
        connection,
        INSERT_STATEMENT,
        parameters,
        we_error=we_error,
        file_function=FileFunction.WRITE,
    )


def bb300_update(
    connection: object,
    host_variables: TdGlledgerRec,
    key_value: str,
    *,
    we_error: int = WeError.SUCCESS,
) -> CommandOutcome:
    """``bb300-Update Section.`` [common/nominalMT.cbl:L1184-L1362].

    Emitted from the ``/MYSQL UPDATE\\ ... TABLE=GLLEDGER-REC`` directive
    [common/nominalMT.cbl:L1187-L1191]. Builds the eleven-column ``SET`` list, then
    appends ``" WHERE "`` and ``FUNCTION TRIM (WS-Where (1:J))``
    [:L1353-L1357], then performs ``MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT``
    [:L1361].

    The ``WHERE`` value is bound LAST, after the eleven ``SET`` values, matching the
    order the placeholders appear in :data:`UPDATE_STATEMENT`.

    Args:
        connection: The open connection.
        host_variables: The group filled by :func:`bb000_hv_load` at
            [common/nominalMT.cbl:L877].
        key_value: The eight-character key from
            :func:`ws_ledger_key_bytes`, which is what ``ba090-Process-Rewrite``
            puts in ``WS-Where``.
        we_error: The ``We-Error`` in force, carried into the error handler.

    Returns:
        The command outcome. ``count_rows`` is the number of rows CHANGED, not
        matched - so a re-write that stores identical values reports zero, which is
        one way ANOMALY N-REWRITE-SILENT fires.
    """
    parameters = (
        *(_bind_value(binding, host_variables) for binding in COLUMN_BINDINGS),
        key_value,
    )
    return _mysql_1210_command(
        connection,
        UPDATE_STATEMENT,
        parameters,
        we_error=we_error,
        file_function=FileFunction.RE_WRITE,
    )


#  THE NOMINALMT BRIDGE  -  BA0NN PARAGRAPHS

@dataclass(slots=True)
class BridgeSession:
    """The bridge's WORKING STORAGE, which persists between calls.

    ``nominalMT`` is a called sub-program whose working storage survives from one
    ``CALL`` to the next: ``ba020-Process-Open`` connects
    [common/nominalMT.cbl:L421], every other paragraph uses that connection, and
    ``ba030-Process-Close`` closes it [:L446]. The result pointer
    ``TP-GLLEDGER-REC USAGE POINTER`` [:L293] and the ``Most-Cursor-Set`` flag
    [common/nominalMT.scb:L262] live there too.

    Modelled as an explicit object with a module-level default rather than as bare
    module globals, which is the pattern :mod:`acas_posting.dal.cursor_state` sets
    for its own ``states``: the default instance gives the single-instance-per-
    process lifetime the COBOL has, and passing one in lets a test drive the bridge
    without touching the shared one. Determinism (rule R-6) is preserved because
    nothing here is derived from a clock, a random source or iteration order.

    NOT a connection pool and NOT thread-safe, deliberately. Agent Action Plan
    0.2.2: "No threads, no ``asyncio``, no ``multiprocessing``, no connection
    pooling. Execution is strictly sequential, matching the single-threaded COBOL."
    """

    #: The open connection, or ``None`` before ``ba020-Process-Open`` and after
    #: ``ba030-Process-Close``.
    connection: object | None = None

    #: The DB-API cursor the ISAM emulation walks. One only - the bridge has one
    #: result pointer, ``TP-GLLEDGER-REC`` [common/nominalMT.cbl:L293].
    cursor: DatabaseCursor | None = None

    #: ``TD-GLLEDGER-REC`` [common/nominalMT.cbl:L294-L305]. One group, reused, as
    #: the COBOL's working storage is.
    host_variables: TdGlledgerRec = field(default_factory=TdGlledgerRec)

    #: The ``Most-Cursor-Set`` state, delegated to
    #: :mod:`acas_posting.dal.cursor_state` so the ``START`` / ``READ NEXT``
    #: protocol lives in one place across all twenty handlers.
    cursor_states: CursorStateTable = field(default_factory=CursorStateTable)

    #: ``ws-No-Paragraph`` [copybooks/wsfnctn.cob:L49], the bridge's own trace of
    #: which paragraph it last entered. Set to the numbers in
    #: :data:`BRIDGE_PARAGRAPH_NUMBERS`.
    ws_no_paragraph: int = 0

    #: ``WS-Where`` as last built, kept because the bridge copies it to
    #: ``WS-Log-Where`` for test logging [common/nominalMT.cbl:L481].
    ws_where: str = ""

    #: ``ACAS-DAL-Common-data``, the bridge's SECOND parameter
    #: [common/acas005.cbl:L664]. Held here so ``ba999-end`` can test ``Testing-1``
    #: [common/nominalMT.cbl:L946] without every paragraph having to thread it.
    dal_common: AcasDalCommonData | None = None

    #: The system record the handler passed down, needed by
    #: :func:`connection.mysql_1000_open`.
    #:
    #: PLUMBING NOTE, not a behaviour change. The COBOL bridge reads its six
    #: credentials from ``RDB-Data`` inside ``File-Access``
    #: [copybooks/wsfnctn.cob:L57-L64], which the HANDLER filled from
    #: ``System-Record`` on the first call [common/acas005.cbl:L637-L642].
    #: ``connection.py`` owns that same load and takes the system record directly,
    #: so the record is carried here rather than the derived six strings. The values
    #: are identical by construction - :func:`connection.load_rdb_data_once` is the
    #: single implementation of the handler's own move sequence - and
    #: :func:`ba020_process_open` still builds the six connection strings from
    #: ``RDB-Data`` exactly as [:L395-L418] does, so the frozen behaviour is
    #: reproduced and merely not re-derived.
    system_record: SystemRecord | None = None

    #: The transport policy handed to :func:`connection.mysql_1000_open`.
    #:
    #: WHY THIS LIVES IN WORKING STORAGE AND NOT IN THE LINKAGE. The COBOL bridge
    #: reaches its server through six strings it builds in its OWN working storage
    #: from ``RDB-Data`` [common/nominalMT.cbl:L395-L418] - the five-parameter handler
    #: linkage [common/acas005.cbl:L268-L274] carries no connection settings at all,
    #: and neither does the three-parameter bridge call [:L663-L666]. So a caller
    #: configures this once, before the first ``fn-Open``, exactly as the installer's
    #: setup step configures ``RDBMS-User`` and friends in the ``SYSTEM-REC`` row.
    #: Putting it in ``dispatch`` instead would add a sixth parameter and break the
    #: linkage contract that rule R-5 requires a reviewer to be able to diff.
    #:
    #: ``None`` IS THE CORRECT DEFAULT AND IS NOT A WEAKENING. ``connection.py`` owns
    #: the transport policy in full: with ``None`` it permits a loopback address or a
    #: Unix socket and refuses anything else, which is what the frozen system's own
    #: default socket connection is. Encrypting or declaring a disposable server is a
    #: deliberate act by the operator, so it is spelled by the operator - this module
    #: adds no policy of its own, per rule R-3's "validation is copied, never
    #: extended", and simply completes the delegation.
    transport: TransportSecurity | None = None


#: The single working-storage instance, matching the one the COBOL sub-program has
#: for the life of the process.
_SESSION: Final[BridgeSession] = BridgeSession()


def _resolve_session(session: BridgeSession | None) -> BridgeSession:
    """Return ``session``, or the module-level default when it is ``None``.

    Args:
        session: A caller-supplied session, or ``None``.

    Returns:
        The session to use.
    """
    return _SESSION if session is None else session


def _set_file_key(file_access: FileAccess, text: str) -> None:
    """``move <literal> to WS-File-Key`` - the bridge's log tag.

    ``WS-File-Key pic x(64)`` [copybooks/wsfnctn.cob:L52], widened by the
    maintainer with the note "increased to 64-- 30/12/16". A COBOL ``MOVE`` into it
    left-justifies, pads with spaces and truncates on the right, so that is what
    happens here - :data:`WS_FILE_KEY_WIDTH` characters, always.

    Args:
        file_access: The block whose ``Logging-Data`` receives the tag.
        text: The literal or built string being moved.
    """
    file_access.logging_data.ws_file_key = text[:WS_FILE_KEY_WIDTH].ljust(WS_FILE_KEY_WIDTH)


def _display_message_1(file_access: FileAccess, dal_common: AcasDalCommonData | None) -> None:
    """``if Testing-2 display Display-Message-1 with erase eos end-if``.

    The bridge's debug screen, declared verbatim [common/nominalMT.cbl:L322-L324]::

        01  Display-Message-1       foreground-color 2.
            03          value "WS-Where="                line 23 col  1.
            03  from WS-Where (1:J)           pic x(69)          col 10.

    So it renders exactly one thing - the WHERE clause the bridge is about to send,
    truncated to 69 characters - onto line 23 in green, having first cleared the rest
    of the screen (``with erase eos``).

    FIVE SITES, gated by ``Testing-2`` and by nothing else
    [common/nominalMT.cbl:L495-L497, :L613-L615, :L744-L746, :L840-L842, :L897-L899]:
    read-next, read-indexed, start, delete and re-write. NOT write - ``ba070`` builds
    no WHERE clause, so there is nothing for it to show.

    Per Agent Action Plan 0.3.4 a "diagnostic display with no database effect becomes
    a log record at a severity matching the original's intent" and "must not alter
    control flow and must not appear in any table dump". This one is a developer trace
    behind a compile-time switch, so ``DEBUG`` is the matching severity, and the
    ``with erase eos`` - a screen effect with no analogue and no database consequence -
    is dropped. ``pic x(69)`` is honoured, because the truncation is what the operator
    actually saw and a longer clause was genuinely invisible to him.

    Args:
        file_access: The block whose ``WS-Log-Where`` carries the clause.
        dal_common: The switch block. ``None`` means no block was passed, in which
            case ``Testing-2`` cannot be true.
    """
    if dal_common is None or dal_common.sw_testing_2 != _TESTING_2:
        return
    # `03 from WS-Where (1:J) pic x(69)` [common/nominalMT.cbl:L324] - the reference
    # modifier takes the clause's used length and the picture then truncates to 69.
    #
    # THE CLAUSE ITSELF IS NOT LOGGED, WHICH IS WHY THIS FUNCTION NOW ONLY GUARDS.
    # `WS-Where` holds the composed SQL `WHERE` clause, with the key value the
    # bridge built it around - an account number, in this table (CWE-532). The
    # frozen `display` writes it to a curses screen that no operator log persists;
    # a log record persists, is aggregated, and is read by people who have no
    # business seeing which account was touched. The guard is kept in place, with
    # its `Testing-2` predicate intact, so that the paragraph still exists for
    # traceability and so that the switch still means what it means - it simply has
    # nothing left to write. Nothing about control flow or status changes: this
    # function returned `None` before and returns `None` now.


#: ``03  from WS-Where (1:J)  pic x(69)`` [common/nominalMT.cbl:L324] - the width of
#: the only field ``Display-Message-1`` renders.
_DISPLAY_WHERE_WIDTH: Final[int] = 69


def _set_log_where(file_access: FileAccess, text: str) -> None:
    """``move WS-Where (1:J) to WS-Log-Where`` - for test logging.

    ``WS-Log-Where pic x(231)`` [copybooks/wsfnctn.cob:L56]. Same ``MOVE``
    semantics as :func:`_set_file_key`.

    Args:
        file_access: The block whose ``Logging-Data`` receives the clause.
        text: The ``WHERE`` clause as built.
    """
    file_access.logging_data.ws_log_where = text[:231].ljust(231)


def ba020_process_open(
    file_access: FileAccess, *, session: BridgeSession | None = None
) -> None:
    """``ba020-Process-Open.`` [common/nominalMT.cbl:L391-L432].

    Builds the six NUL-terminated connection strings from ``RDB-Data``, then
    performs ``MYSQL-1000-OPEN THRU MYSQL-1090-EXIT`` [:L421].

    The string order is the frozen order - Schema, Host, UName, UPass, Port, Socket
    [:L395-L418] - which is NOT the order the handler loaded ``RDB-Data`` in
    [common/acas005.cbl:L637-L642], where it is Schema, UName, UPass, Port, Host,
    Socket. Both orders are preserved where they occur; neither is normalised.

    Every string is assembled with ``delimited by space`` plus a trailing ``X"00"``,
    i.e. the value up to its first space, NUL-terminated for the C interface.
    :func:`connection.cobol_string_delimited_by_space` is that truncation, and the
    NUL is framing the Python driver supplies itself.

    Control flow::

        if fs-reply not = zero  go to ba999-end                        [:L422-L423]
        move "OPEN GL LEDGER (RDB)" to WS-File-Key                     [:L431]
        move zero to Most-Cursor-Set                                   [:L432]
        go to ba999-end                                                [:L433]

    GO TO CLASS 3 (section exit) at [:L423] and [:L433] - both become ``return``,
    with :func:`ba999_end` performed first because the COBOL falls into it.

    Args:
        file_access: The block supplying ``RDB-Data`` and receiving the status.
        session: The bridge working storage; the module default when ``None``.
    """
    state = _resolve_session(session)
    state.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS["ba020-Process-Open"][0]
    rdb_data = file_access.rdb_data
    # [:L395-L418] - built in the frozen order and kept for the trace, exactly as
    # the bridge builds them before it opens.
    #  THE ENDPOINT IS CLASSIFIED, NOT NAMED. `redact_for_log` was applied to these
    #  four fields and could not help: its rules recognise the shapes a client
    #  library's MESSAGE takes - "for user 'x'@'y'", "Unknown database 'z'" - and a
    #  bare host name or schema name matches none of them, so every character went
    #  straight through (CWE-532). `transport_category` answers the only question a
    #  log record has to answer about a connect target - can the credentials and the
    #  posted figures be read off the wire - with one of five fixed tokens, and is
    #  identical on every deployment.
    _LOG.debug(
        "%s connect: transport=%s",
        BRIDGE_NAME,
        transport_category(
            {
                "host": cobol_string_delimited_by_space(rdb_data.db_host),
                "unix_socket": cobol_string_delimited_by_space(
                    rdb_data.db_socket
                ),
            }
            if cobol_string_delimited_by_space(rdb_data.db_socket)
            else {"host": cobol_string_delimited_by_space(rdb_data.db_host)}
        ),
    )
    if state.system_record is None:
        raise CobolFileAccessNotMigratedError(FileFunction.OPEN, access_type=AccessType.INPUT)
    # `move 1 to ws-No-Paragraph.` then `PERFORM MYSQL-1000-OPEN THRU
    # MYSQL-1090-EXIT.` [:L420-L421].
    outcome = mysql_1090_exit(
        mysql_1000_open(
            state.system_record,
            ws_no_paragraph=state.ws_no_paragraph,
            we_error=file_access.we_error,
            # The policy from working storage - see `BridgeSession.transport`. The
            # frozen bridge has no analogue because GnuCOBOL's client library takes
            # its TLS settings from the environment rather than from the program, so
            # this is the one connection concern the COBOL delegates outward too.
            transport=state.transport,
        )
    )
    file_access.fs_reply = outcome.fs_reply
    file_access.we_error = outcome.we_error
    logging_data = file_access.logging_data
    logging_data.ws_no_paragraph = outcome.ws_no_paragraph
    logging_data.sql_err = outcome.sql_err
    logging_data.sql_msg = outcome.sql_msg
    logging_data.sql_state = outcome.sql_state
    if outcome.fs_reply != FsReply.SUCCESS:
        # `if fs-reply not = zero go to ba999-end.` [:L422-L423] - GO TO CLASS 3.
        # Note what is NOT done on this path: no `WS-File-Key` tag and no
        # `Most-Cursor-Set` reset. Both sit after the test [:L431-L432].
        ba999_end(file_access, session=state)
        return
    state.connection = outcome.connection
    state.cursor = None
    _set_file_key(file_access, FILE_KEY_TAGS["bridge-open"])
    # `move zero to Most-Cursor-Set` [:L432] - a fresh connection has no position.
    state.cursor_states.reset(TABLE_NAME)
    ba999_end(file_access, session=state)


def ba030_process_close(
    file_access: FileAccess, *, session: BridgeSession | None = None
) -> None:
    """``ba030-Process-Close.`` [common/nominalMT.cbl:L435-L448].

    Frees any live cursor first, then closes::

        if Cursor-Active  perform ba998-Free                           [:L436-L437]
        move 2 to ws-No-Paragraph                                      [:L439]
        move "CLOSE GL LEDGER (RDB)" to WS-File-Key                    [:L440]
        PERFORM MYSQL-1980-CLOSE THRU MYSQL-1999-EXIT                  [:L445]
        go to ba999-end                                                [:L447]

    The free is a ``PERFORM``, so control returns and the close still happens - it
    is NOT a ``GO TO``. GO TO CLASS 3 at [:L447].

    Args:
        file_access: The block receiving the status.
        session: The bridge working storage; the module default when ``None``.
    """
    state = _resolve_session(session)
    # `if Cursor-Active perform ba998-Free.` [:L436-L437].
    if state.cursor_states.state_for(TABLE_NAME, CursorSlot.PRIMARY).cursor_active():
        ba998_free(session=state)
    state.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS["ba030-Process-Close"][0]
    _set_file_key(file_access, FILE_KEY_TAGS["bridge-close"])
    # `PERFORM MYSQL-1980-CLOSE THRU MYSQL-1999-EXIT` [:L445].
    if state.cursor is not None:
        state.cursor.close()  # type: ignore[attr-defined]
        state.cursor = None
    mysql_1980_close(state.connection)  # type: ignore[arg-type]
    mysql_1999_exit()
    state.connection = None
    file_access.fs_reply = FsReply.SUCCESS
    file_access.we_error = WeError.SUCCESS
    ba999_end(file_access, session=state)


def _require_cursor(state: BridgeSession) -> DatabaseCursor:
    """Return the session's cursor, creating it on first use.

    The bridge holds ONE result pointer, ``TP-GLLEDGER-REC USAGE POINTER``
    [common/nominalMT.cbl:L293], so this holds one cursor. It is created lazily
    because ``ba020-Process-Open`` connects without positioning anything -
    ``move zero to Most-Cursor-Set`` [:L432] - and destroyed by
    :func:`ba030_process_close`.

    Args:
        state: The bridge working storage.

    Returns:
        The cursor for the ISAM emulation to walk.

    Raises:
        AcasFileHandlerError: If no connection is open. The bridge would have
            failed inside ``MySQL_query`` with a null handle; reported as the
            ``(99, 990)`` pair ``ba100-Bad-Function`` uses
            [common/nominalMT.cbl:L919-L923], since there is no more specific code
            in the frozen source for "used before open".
    """
    if state.connection is None:
        raise AcasFileHandlerError(
            FsReply.ERROR,
            WeError.UNKNOWN_UNEXPECTED,
            operation=f"{BRIDGE_NAME} used before ba020-Process-Open",
            table=TABLE_NAME,
        )
    if state.cursor is None:
        # A dead session is reachable without this bridge doing anything wrong:
        # anomaly A-8 means ANY other bridge's `Mysql-1980-Close` takes the one
        # process handle down [presql2-package/cobmysqlapi38.c:L230-L234]. The
        # frozen bridge reports that from its `call "MySQL_query"`
        # [copybooks/mysql-procedures.cpy:L165-L166] and never from a separate
        # acquisition step, so the failure is carried to the statement instead of
        # raised here.
        cursor = acquire_cursor(state.connection)  # type: ignore[arg-type]
        if cursor_is_unavailable(cursor):
            # NOT cached. Caching it would keep failing after another bridge's
            # `Mysql-1000-Open` had revived the handle in place [:L433], which
            # the frozen source cannot do - see :func:`cursor_is_unavailable`.
            return cursor  # type: ignore[return-value]
        state.cursor = cursor  # type: ignore[assignment]
    return state.cursor


def ba040_process_read_next(
    file_access: FileAccess, ledger: WsLedgerRecord, *, session: BridgeSession | None = None
) -> CursorOutcome:
    """``ba040-Process-Read-Next.`` [common/nominalMT.cbl:L450-L523].

    *** THE VERB THIS TABLE'S CORRECTNESS RESTS ON. ***

    Agent Action Plan 0.6.4, verbatim: "The sort feeds a sequential read. ``gl072``
    locates the nominal-ledger account for each posting with a sequential read-next
    rather than an indexed read [general/gl072.cbl:L410-L412]. It finds the correct
    account only because ``gl071`` has already emitted the transaction stream in
    nominal-key order. Any change in sort stability or key composition produces
    SILENT MISPOSTING - no error, no diagnostic, wrong balances."

    The plan's citation is off by a few lines: the sequential read is the guarded
    ``if read-ledger not = "R" / perform GL-Nominal-Read-Next`` at
    ``[general/gl072.cbl:L407-L408]``, and ``[general/gl072.cbl:L410-L412]`` is the
    ``move zero to tot-dr tot-cr`` after it. The requirement is unchanged.

    So the ordering below is a CORRECTNESS REQUIREMENT, not a convenience. It is
    ``ORDER BY `LEDGER-KEY` ASC``, one term, no tie-breaker, no ``LIMIT``, from the
    key of reference [common/nominalMT.cbl:L466-L470] - and the self-positioning
    relation is ``>`` with a low key of ``"00000000"`` [:L466-L467], carrying the
    maintainer's own note "26/12/16 NOT '='". Agent Action Plan 0.8.4 forbids the
    obvious optimisation by name: the migration "must not 'optimise' the sequential
    nominal read into an indexed one, even though that would obviously be faster ...
    Any performance work is therefore out of scope by construction, not merely
    unrequested."

    All of that - the positioning statement, the stored-result snapshot, the
    one-row-per-call fetch and the ``FS-Reply`` protocol - is implemented by
    :func:`cursor_state.read_next`, driven from
    :data:`cursor_state.SEQUENTIAL_READ_START` and
    :data:`cursor_state.TABLE_OF_KEYNAMES` so that the per-bridge relation survives
    as DATA rather than as a copy of this prose. This paragraph supplies the table
    and the record, and unloads the row.

    STRUCTURE. ``ba040`` and ``ba041`` are two stages of ONE verb: the
    ``if Cursor-Not-Active`` block [:L454-L522] positions, ends with
    ``perform ba999-End`` to log [:L521], and then FALLS THROUGH the ``end-if``
    into ``ba041-Reread``. The empty-table branch inside it instead does
    ``go to ba999-End`` [:L512] and does not fall through.

    * GO TO CLASS 3 (section exit) at [:L512] - the empty-table branch returns
      ``(10, 10)`` with the tag ``"No Data"``.
    * GO TO CLASS 4 (sibling re-dispatch) is the FALL-THROUGH at [:L522] into
      ``ba041-Reread``, expressed here as the explicit call to :func:`ba041_reread`
      that :func:`cursor_state.read_next` performs internally.

    Args:
        file_access: The block supplying the caller's ``FS-Reply`` - which matters,
            because end of file is STICKY on this path - and receiving the status.
        ledger: The record to unload a fetched row into.
        session: The bridge working storage; the module default when ``None``.

    Returns:
        The cursor outcome, already applied to ``file_access``.
    """
    state = _resolve_session(session)
    state.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS["ba040-Process-Read-Next"][0]
    _set_log_where(file_access, "")
    # `if Testing-2 display Display-Message-1 with erase eos end-if`
    # [common/nominalMT.cbl:L495-L497] - the debug trace of the clause just logged.
    _display_message_1(file_access, state.dal_common)
    outcome = cursor_state.read_next(
        _require_cursor(state),
        TABLE_NAME,
        slot=CursorSlot.PRIMARY,
        states=state.cursor_states,
        file_access=file_access,
    )
    state.ws_where = outcome.statement
    _set_file_key(file_access, outcome.file_key)
    if outcome.row is not None:
        # `perform bb100-UnloadHVs` [:L588] then `move HV-LEDGER-KEY to
        # WS-File-Key` [:L590]. Reached only when a row was delivered.
        ba041_reread(outcome, ledger, file_access, session=state)
    ba999_end(file_access, session=state)
    return outcome


def ba041_reread(
    outcome: CursorOutcome,
    ledger: WsLedgerRecord,
    file_access: FileAccess,
    *,
    session: BridgeSession | None = None,
) -> None:
    """``ba041-Reread.`` [common/nominalMT.cbl:L525-L592].

    The delivery stage of the read-next verb, and the target of ``ba040``'s
    fall-through. Reached from ``ba040`` [:L522] and, on a positioned cursor, as
    the whole of the verb; ``ba050-Process-Read-Indexed`` does NOT come through
    here - it has its own ``MySQL_fetch_record`` and its own unload [:L638-L684].

    The eleven host variables are fetched in COLUMN order [:L540-L551], which is why
    the fetch is driven from :data:`COLUMN_BINDINGS` and not from
    :data:`HV_LOAD_ORDER`.

    Three end-of-file branches precede the unload, all reproduced by
    :func:`cursor_state.read_next` and distinguishable only by their log tag:

    * ``return-code = -1`` -> ``(10, 10)``, tag ``"EOF"`` [:L556-L562];
    * count zero WITH an errno -> ``(10, 10)``, tag ``"EOF2"``, and
      ``initialize WS-Ledger-Record WITH FILLER`` [:L574-L575]. Note the
      ``WITH FILLER``: this is the OTHER ``INITIALIZE`` form, and it DOES clear the
      55 filler bytes that ``bb100-UnloadHVs``'s plain ``initialize`` [:L989]
      leaves alone. Two forms, same bridge, both preserved - see
      :func:`_initialize_ws_ledger_record`. Count zero with NO errno writes no
      status at all, which is why :attr:`CursorOutcome.status_written` exists;
    * the caller's own ``FS-Reply`` still 10 -> tag ``"EOF3"``, row DISCARDED
      UNREAD [:L582-L586]. End of file is STICKY and nothing in the bridge clears
      it.

    On success::

        perform bb100-UnloadHVs                                        [:L588]
        move HV-LEDGER-KEY to WS-File-Key                              [:L590]
        move zero to fs-reply WE-Error                                 [:L591]
        go to ba999-end                                                [:L592]

    GO TO CLASS 3 at [:L562], [:L580], [:L586] and [:L592] - every one a ``return``.

    Args:
        outcome: The outcome from :func:`cursor_state.read_next`, carrying the row.
        ledger: The record to unload into.
        file_access: The block receiving the log tag and status.
        session: The bridge working storage; the module default when ``None``.
    """
    state = _resolve_session(session)
    state.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS["ba041-Reread"][0]
    if outcome.row is None:
        return
    _fetch_into_host_variables(outcome.row, state.host_variables)
    # `perform bb100-UnloadHVs.` [:L588] - transfer HV vars to record layout.
    bb100_unload_hvs(state.host_variables, ledger)
    # `move HV-LEDGER-KEY to WS-File-Key.` [:L590] - the KEY, not the tag.
    _set_file_key(file_access, str(state.host_variables.hv_ledger_key))


def _fetch_into_host_variables(
    row: Mapping[str, object], host_variables: TdGlledgerRec
) -> None:
    """``CALL "MySQL_fetch_record" USING WS-MYSQL-RESULT HV-...`` - the fetch.

    Reproduces the eleven-argument fetch at [common/nominalMT.cbl:L540-L551] on the
    read-next path and [:L645-L656] on the read-indexed path. The arguments are in
    COLUMN order in both, so the loop walks :data:`COLUMN_BINDINGS`.

    NO TRIM HAPPENS HERE, and that is a deliberate finding rather than an omission.
    The bridge's four ``FUNCTION TRIM`` calls are all on the WRITE paths -
    ``INSERT`` at [:L1046] and [:L1067], ``UPDATE`` at [:L1225] and [:L1245] - and
    the fetch passes host variables straight to the C interface with no trim at all.
    Trailing spaces therefore arrive exactly as ``char(1)`` and ``char(32)``
    deliver them, and it is the RECEIVING FIELD that pads or truncates, which is
    where anomaly A-12 bites; see :func:`bb100_unload_hvs`.

    The maintainer's own note on why no indicator variables are needed
    [common/nominalMT.cbl:L986-L987]: "NULL fields must not be returned in the
    buffer. SQL filters each column to ensure it has a proper value. This saves
    using indicator variables." Every column is ``NOT NULL``
    [mysql/ACASDB.sql:L123-L133], so a ``None`` here would mean the frozen schema
    had changed; it is coerced to the host variable's own zero or space rather than
    propagated, which is what the C interface's fixed-width buffers do.

    Args:
        row: The fetched row, keyed by column name.
        host_variables: The group to fill in place.
    """
    for binding in COLUMN_BINDINGS:
        value = row.get(binding.column_name)
        if value is None:
            # The buffer never holds NULL - see the maintainer's note above. A
            # fixed-width C buffer presented with nothing keeps its initialised
            # zero or space, so that is what is stored.
            value = 0 if binding.python_storage != "STR" else ""
        setattr(host_variables, binding.hv_attribute, _store_hv(binding, value))


def ba050_process_read_indexed(
    file_access: FileAccess, ledger: WsLedgerRecord, *, session: BridgeSession | None = None
) -> CursorOutcome:
    """``ba050-Process-Read-Indexed.`` [common/nominalMT.cbl:L594-L687].

    Reads one row by primary key. Builds ``` `LEDGER-KEY`="<WS-Ledger-Record(1:8)>" ```
    from the key table [:L603-L611], selects, fetches, unloads, and ALWAYS frees the
    cursor on the way out.

    Two behaviours to note:

    * the miss branch is ``move 21 to fs-Reply`` with ``move zero to WE-Error``
      [:L635-L637] - and that second statement is a DIVERGENCE FROM
      ``glpostingMT``, whose equivalent [common/glpostingMT.cbl:L633-L636] does
      NOT clear ``We-Error``. :func:`cursor_state.read_indexed` implements the
      ``glpostingMT`` form, so this paragraph applies the extra statement ITSELF
      rather than changing the shared module that nineteen sibling handlers depend
      on. The maintainer's own comment on the value is "could also be 23 or 14".
    * the ``WS-MYSQL-Count-Rows not > zero`` branch [:L661-L681], with its
      ``990``/``"Not found 1"`` and ``989``/``"Not found 2"`` arms, is DEAD CODE:
      the ``= zero`` test above it has already returned for the only count that
      could satisfy it. ANOMALY N-NOTFOUND-DEAD - reproduced by being equally
      unreachable here, not by being deleted.

    * GO TO CLASS 4 (sibling re-dispatch) at [:L637], [:L676], [:L681] and [:L687]
      - every exit goes to ``ba998-Free`` first, which frees and then falls into
      ``ba999-End``. Expressed as an explicit :func:`ba998_free` call followed by
      :func:`ba999_end`.

    Args:
        file_access: The block receiving the status.
        ledger: The record supplying the key and receiving the row.
        session: The bridge working storage; the module default when ``None``.

    Returns:
        The cursor outcome, already applied to ``file_access``.
    """
    state = _resolve_session(session)
    state.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS["ba050-Process-Read-Indexed"][0]
    key_value = ws_ledger_key_bytes(ledger)
    outcome = cursor_state.read_indexed(
        _require_cursor(state),
        TABLE_NAME,
        key_value,
        key_number=FILE_KEY_NO,
        slot=CursorSlot.PRIMARY,
        states=state.cursor_states,
        file_access=file_access,
    )
    state.ws_where = outcome.statement
    _set_log_where(file_access, outcome.statement)
    # `if Testing-2 display Display-Message-1 with erase eos end-if`
    # [common/nominalMT.cbl:L613-L615] - the debug trace of the clause just logged.
    _display_message_1(file_access, state.dal_common)
    if outcome.row is not None:
        _fetch_into_host_variables(outcome.row, state.host_variables)
        # `perform bb100-UnloadHVs` [:L682] then `move HV-LEDGER-KEY to
        # WS-File-Key` [:L683].
        bb100_unload_hvs(state.host_variables, ledger)
        _set_file_key(file_access, str(state.host_variables.hv_ledger_key))
    elif outcome.fs_reply == FsReply.INVALID_KEY_ON_START:
        # `move zero to WE-Error` [:L635]. THE DIVERGENCE FROM glpostingMT, applied
        # locally so the shared cursor_state module keeps the glpostingMT form that
        # its other callers were written against.
        #
        # THIS TEST IS DELIBERATELY NOT NARROWED, and the frozen source is why.
        # `cursor_state.read_indexed` also reports a DRIVER FAILURE as FS-Reply 21
        # (its anomaly A14), so this arm catches that too and zeroes a `We-Error`
        # of 911. That looks like it should be split, because the frozen
        # `move zero to WE-Error` sits inside the `if WS-MYSQL-Count-Rows = zero`
        # guard [:L633-L637] which a failed statement does not satisfy. It is not
        # split, because the frozen program never arrives at that guard at all:
        # `ba050` performs `MYSQL-1220-STORE-RESULT` [:L629], whose
        # `call "MySQL_num_rows" using Ws-Mysql-Result Ws-Mysql-Count-Rows`
        # [copybooks/mysql-procedures.cpy:L191-L192] is UNCONDITIONAL, and on a
        # failed statement `Ws-Mysql-Result` is null - the COBOL tests for exactly
        # that one line earlier [:L189-L190]. The C then dereferences it,
        # `*rows = mysql_num_rows(*result)`
        # [presql2-package/cobmysqlapi38.c:L484], so the compiled program faults
        # inside the client library before reaching [:L633]. There is therefore NO
        # frozen status pair for a driver failure here, nothing this arm can
        # disagree with, and no scenario in which the choice is observable.
        # Narrowing it would be an unrequested behaviour change on an
        # oracle-unreachable path.
        file_access.we_error = WeError.SUCCESS
    # ANOMALY N-NOTFOUND-DEAD - REPRODUCTION SITE. The frozen paragraph's
    # `WS-MYSQL-Count-Rows not > zero` branch [common/nominalMT.cbl:L661-L681], with
    # its 990/"Not found 1" and 989/"Not found 2" arms, is UNREACHABLE: the `= zero`
    # test above it already returned for the only count that could satisfy it. It is
    # reproduced by being equally unreachable HERE - deliberately not written - which
    # is why no branch below sets 990 or 989. Deleting it would have been a fix.
    # `go to ba998-Free` on EVERY path [:L637, :L676, :L681, :L687] - GO TO CLASS 4.
    ba998_free(session=state)
    ba999_end(file_access, session=state)
    return outcome


def ba060_process_start(
    file_access: FileAccess, ledger: WsLedgerRecord, *, session: BridgeSession | None = None
) -> CursorOutcome:
    """``ba060-Process-Start.`` [common/nominalMT.cbl:L689-L789].

    Positions the cursor for a following ``READ NEXT``, without delivering a row.

    THE PARAMETER GUARD, verbatim [common/nominalMT.cbl:L692-L696]::

        if       access-type < 5 or > 8       *> not using not < or not >
                 move 99 to FS-Reply
                 move 997 to WE-Error         *> Invalid calling parameter settings 997
                 go to ba999-end
        end-if

    Read that range carefully: ``< 5 or > 8`` REJECTS ACCESS TYPE 9. Yet the
    ``evaluate`` twenty lines below has an explicit ``when 9`` arm mapping it to
    ``"<= "`` [:L722-L723], annotated by the maintainer "not currently used in
    ACAS". The arm is therefore UNREACHABLE - the guard has already returned. Both
    the guard's range and the dead arm are reproduced;
    :data:`status.START_ACCESS_TYPE_RANGE` is ``(5, 8)`` for exactly this reason and
    :data:`status.START_RELATION_BY_ACCESS_TYPE` still carries the 9 mapping as data.

    Note also that the guard writes ``FS-Reply`` 99 AND ``We-Error`` 997 here, while
    the HANDLER's own start guard [common/acas005.cbl:L495-L497] writes ``We-Error``
    998 and DOES NOT TOUCH ``FS-Reply`` at all. Two guards, two dispositions, same
    verb - see :func:`aa060_process_start`.

    The relation comes from ``Access-Type`` [:L713-L725] because the facade
    deliberately does not zero it before a ``-Start``; the mapping is
    :data:`status.START_RELATION_BY_ACCESS_TYPE` and it is passed through unmodified.

    ANOMALY N-START-SILENT - REPRODUCED. When the select returns no rows AND the
    driver reports no errno, the paragraph writes NOTHING: the errno test [:L771]
    has no ``else``, and the outer ``else`` [:L780] only runs when the count is
    non-zero. The caller's ``(FS-Reply, We-Error)`` survive untouched. With an
    errno it is ``(21, 0)`` [:L777-L778].

    * GO TO CLASS 3 at [:L696] (guard), [:L779] (errno branch) and [:L789] (tail).

    Args:
        file_access: The block supplying ``Access-Type`` and receiving the status.
        ledger: The record supplying the key.
        session: The bridge working storage; the module default when ``None``.

    Returns:
        The cursor outcome, already applied to ``file_access``.
    """
    state = _resolve_session(session)
    state.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS["ba060-Process-Start"][0]
    key_value = ws_ledger_key_bytes(ledger)
    outcome = cursor_state.start(
        _require_cursor(state),
        TABLE_NAME,
        key_value,
        file_access.access_type,
        key_number=FILE_KEY_NO,
        slot=CursorSlot.PRIMARY,
        states=state.cursor_states,
        file_access=file_access,
    )
    state.ws_where = outcome.statement
    _set_log_where(file_access, outcome.statement)
    # ANOMALY N-START-SILENT - REPRODUCTION SITE. No status is written on the
    # no-rows-without-errno path: the errno test [common/nominalMT.cbl:L771] has no
    # `else`, and the outer `else` [common/nominalMT.cbl:L780] runs only when the
    # count is non-zero, so the caller's (FS-Reply, We-Error) survive UNTOUCHED.
    # Nothing is assigned to `file_access` between the cursor call and the tail for
    # exactly that reason; writing a status here would be a fix, not a migration.
    # `if Testing-2 display Display-Message-1 with erase eos end-if`
    # [common/nominalMT.cbl:L744-L746] - the debug trace of the clause just logged.
    _display_message_1(file_access, state.dal_common)
    # `move WS-Ledger-Key to WS-File-Key.` [:L744] - note the maintainer's own
    # commented-out alternative on the same line, `WS-Ledger-Record (K:L)`, which
    # would have been the same eight characters by a different route.
    _set_file_key(file_access, outcome.file_key or key_value)
    ba999_end(file_access, session=state)
    return outcome


def ba070_process_write(
    file_access: FileAccess, ledger: WsLedgerRecord, *, session: BridgeSession | None = None
) -> CommandOutcome:
    """``ba070-Process-Write.`` [common/nominalMT.cbl:L793-L818].

    Inserts one row. Statement order, exactly as frozen::

        perform bb000-HV-Load                                          [:L794]
        move WS-Ledger-Key to WS-File-Key                              [:L795]
        move zero to FS-Reply WE-Error                                 [:L796]
        move spaces to SQL-Msg                                         [:L797]
        move zero to SQL-Err                                           [:L798]
        move 10 to ws-No-Paragraph                                     [:L799]
        perform bb200-Insert                                           [:L800]

    *** THE STATUS PAIR IS ZEROED BEFORE THE INSERT, NOT AFTER. *** That one
    ordering choice is why write does NOT suffer ANOMALY N-REWRITE-SILENT or
    N-DELETE-SILENT: whatever happens next, the pair has already been written, so a
    count of zero with no errno reports success rather than reporting whatever the
    caller happened to be carrying. ``ba080`` and ``ba090`` zero it AFTER, and jump
    past that statement. The asymmetry is the evidence their omission is an accident
    rather than an idiom - and it is preserved, not harmonised.

    The duplicate-key mapping [:L810-L815]: with a count other than 1 and a non-zero
    errno, ``SQL-Err (1:4)`` of ``"1062"`` or ``"1022"``, or ``Sql-State`` of
    ``"23000"``, gives ``FS-Reply`` 22; anything else gives 99. ``We-Error`` is
    NEVER set on this path - it stays at the zero from [:L796], which is why a
    duplicate arrives as ``(22, 0)``. :func:`status.mysql_1100_db_error` owns the
    errno-to-status mapping.

    * GO TO CLASS 3 at [:L818].

    Args:
        file_access: The block receiving the status.
        ledger: The record to insert.
        session: The bridge working storage; the module default when ``None``.

    Returns:
        The command outcome, already applied to ``file_access``.
    """
    state = _resolve_session(session)
    # `perform bb000-HV-Load.` [:L794].
    bb000_hv_load(ledger, state.host_variables)
    # `move WS-Ledger-Key to WS-File-Key.` [:L795] - the GROUP view, eight digits.
    _set_file_key(file_access, ws_ledger_key_bytes(ledger))
    # `move zero to FS-Reply WE-Error` [:L796] and the two SQL fields [:L797-L798],
    # ALL BEFORE the insert. See the docstring.
    file_access.fs_reply = FsReply.SUCCESS
    file_access.we_error = WeError.SUCCESS
    file_access.logging_data.sql_msg = ""
    file_access.logging_data.sql_err = ""
    state.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS["ba070-Process-Write"][0]
    outcome = bb200_insert(state.connection, state.host_variables, we_error=WeError.SUCCESS)
    if outcome.count_rows != 1:
        # `if WS-MYSQL-COUNT-ROWS not = 1` [:L801] - the status already reflects the
        # driver's own report, mapped by mysql_1100_db_error. With no errno at all
        # nothing further is written, and the zeroes from [:L796] stand.
        outcome.apply_to(file_access)
    else:
        file_access.logging_data.ws_count_rows = outcome.count_rows
    ba999_end(file_access, session=state)
    return outcome


def ba080_process_delete(
    file_access: FileAccess, ledger: WsLedgerRecord, *, session: BridgeSession | None = None
) -> CommandOutcome:
    """``ba080-Process-Delete.`` [common/nominalMT.cbl:L820-L873].

    Deletes one row by primary key. The maintainer's own header note, verbatim
    [:L820]: "IRS does not test for error cond. as in irsub1".

    ANOMALY N-DELETE-SILENT - REPRODUCED, NOT FIXED. The control flow, verbatim
    [:L857-L871]::

        if       WS-MYSQL-COUNT-ROWS not = 1
                 ... if WS-MYSQL-Error-Number not = "0  "
                        move 99 to fs-reply
                        move 995 to WE-Error
                     end-if
                 go to ba999-End                       *> produce log
        else
                 move spaces to SQL-Msg SQL-State
                 move zero   to SQL-Err
        end-if.
        move     zero to FS-Reply WE-Error.
        go       to ba999-End.

    The ``go to ba999-End`` inside the count test is UNCONDITIONAL within that
    branch, so when the count is wrong and the errno is ``"0  "`` the paragraph
    returns having written NEITHER ``FS-Reply`` NOR ``We-Error`` - it has jumped
    past [:L872]. A delete that matched no row therefore reports whatever the
    caller was already carrying, which after a successful read is success. Modelled
    by :attr:`CommandOutcome.status_written`.

    * GO TO CLASS 3 at [:L868] and [:L873].

    Args:
        file_access: The block receiving the status.
        ledger: The record supplying the key.
        session: The bridge working storage; the module default when ``None``.

    Returns:
        The command outcome, already applied to ``file_access`` - honouring
        ``status_written``.
    """
    state = _resolve_session(session)
    key_value = ws_ledger_key_bytes(ledger)
    # `move WS-Ledger-Record (K:L) to WS-File-Key.` [:L836] - note this paragraph
    # uses the reference modifier where ba070 uses `WS-Ledger-Key`; the same eight
    # characters, and the maintainer left the alternative commented out at [:L833].
    _set_file_key(file_access, key_value)
    _set_log_where(file_access, DELETE_STATEMENT)
    # `if Testing-2 display Display-Message-1 with erase eos end-if`
    # [common/nominalMT.cbl:L840-L842] - the debug trace of the clause just logged.
    _display_message_1(file_access, state.dal_common)
    state.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS["ba080-Process-Delete"][0]
    outcome = _mysql_1210_command(
        state.connection,
        DELETE_STATEMENT,
        (key_value,),
        we_error=file_access.we_error,
        file_function=FileFunction.DELETE,
    )
    if outcome.count_rows != 1:
        if outcome.sql_err:
            # `move 99 to fs-reply` / `move 995 to WE-Error` [:L865-L866].
            outcome = replace(
                outcome, fs_reply=FsReply.ERROR, we_error=WeError.DELETE_KEY_OUT_OF_RANGE
            )
        else:
            # ANOMALY N-DELETE-SILENT: the branch jumps to ba999-End [:L868],
            # PAST `move zero to FS-Reply WE-Error` [:L872]. Nothing is written.
            outcome = replace(outcome, status_written=False)
    else:
        # The `else` arm [:L869-L871] clears the diagnostics, then [:L872] zeroes
        # the pair.
        outcome = replace(
            outcome,
            fs_reply=FsReply.SUCCESS,
            we_error=WeError.SUCCESS,
            sql_err="",
            sql_msg="",
            sql_state="",
        )
    outcome.apply_to(file_access)
    ba999_end(file_access, session=state)
    return outcome


def ba090_process_rewrite(
    file_access: FileAccess, ledger: WsLedgerRecord, *, session: BridgeSession | None = None
) -> CommandOutcome:
    """``ba090-Process-Rewrite.`` [common/nominalMT.cbl:L876-L916].

    Updates one row by primary key. Statement order::

        perform bb000-HV-Load                                          [:L877]
        move 17 to ws-No-Paragraph                                     [:L878]
        ... build WS-Where from the key table                          [:L879-L893]
        move WS-Where (1:J) to WS-Log-Where                            [:L894]
        perform bb300-Update                                           [:L895]

    ANOMALY N-REWRITE-SILENT - REPRODUCED, NOT FIXED. Identical in shape to
    N-DELETE-SILENT [:L901-L913]: the ``go to ba999-End`` at [:L912] sits inside the
    ``WS-MYSQL-COUNT-ROWS not = 1`` branch and jumps past ``move zero to FS-Reply
    WE-Error`` at [:L914]. With a wrong count and no errno, NEITHER STATUS FIELD IS
    WRITTEN.

    That combination is not exotic here. ``MySQL_affected_rows`` counts rows CHANGED
    rather than matched - ``dal/connection.py`` does not negotiate
    ``CLIENT_FOUND_ROWS``, matching the C interface the frozen bridge links - so a
    re-write that stores values identical to those already present reports ZERO rows
    with no error at all, and this paragraph then reports nothing. A caller that
    re-writes an unchanged nominal account sees whatever status it was carrying.

    Note also that this paragraph NEVER SETS ``WS-File-Key``, unlike every other
    verb in the bridge. The log record for a re-write therefore carries the tag left
    by the previous operation. Recorded, not corrected.

    With an errno it is ``(99, 994)`` [:L909-L910].

    * GO TO CLASS 3 at [:L912] and [:L916].

    Args:
        file_access: The block receiving the status.
        ledger: The record to write, and the source of the key.
        session: The bridge working storage; the module default when ``None``.

    Returns:
        The command outcome, already applied to ``file_access`` - honouring
        ``status_written``.
    """
    state = _resolve_session(session)
    # `perform bb000-HV-Load.` [:L877] - "Load up the HV fields from table record
    # in WS".
    bb000_hv_load(ledger, state.host_variables)
    state.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS["ba090-Process-Rewrite"][0]
    key_value = ws_ledger_key_bytes(ledger)
    _set_log_where(file_access, UPDATE_STATEMENT)
    # `if Testing-2 display Display-Message-1 with erase eos end-if`
    # [common/nominalMT.cbl:L897-L899] - the debug trace of the clause just logged.
    _display_message_1(file_access, state.dal_common)
    outcome = bb300_update(
        state.connection, state.host_variables, key_value, we_error=file_access.we_error
    )
    if outcome.count_rows != 1:
        if outcome.sql_err:
            # `move 99 to fs-reply` / `move 994 to WE-Error` [:L909-L910]. 994 has
            # no name in `status.WeError`; it is the re-write-specific code and is
            # carried as its literal value, as the frozen source does.
            outcome = replace(outcome, fs_reply=FsReply.ERROR, we_error=994)
        else:
            # ANOMALY N-REWRITE-SILENT: `go to ba999-End` [:L912] jumps past
            # `move zero to FS-Reply WE-Error` [:L914]. Nothing is written.
            outcome = replace(outcome, status_written=False)
    else:
        # [:L914-L915] - zero the pair and clear the diagnostics.
        outcome = replace(
            outcome,
            fs_reply=FsReply.SUCCESS,
            we_error=WeError.SUCCESS,
            sql_err="",
            sql_msg="",
            sql_state="",
        )
    outcome.apply_to(file_access)
    ba999_end(file_access, session=state)
    return outcome


def ba100_bad_function(
    file_access: FileAccess, *, session: BridgeSession | None = None
) -> None:
    """``ba100-Bad-Function.`` [common/nominalMT.cbl:L919-L923].

    The bridge's own catch-all, headed by the maintainer's comment "Houston; We have
    a problem" [:L921]::

        move     990 to WE-Error.                                      [:L922]
        move     99 to Fs-Reply.                                       [:L923]
        go       to ba999-end.                                         [:L924]

    ``We-Error`` FIRST, then ``FS-Reply`` - the reverse of the handler's own
    ``aa100-Bad-Function``, which writes ``FS-Reply`` first
    [common/acas005.cbl:L569-L570]. Statement order is preserved in both because
    rule R-6 asks for the COBOL's order, even where the result is identical.

    * GO TO CLASS 3 at [:L924].

    Args:
        file_access: The block receiving ``(99, 990)``.
        session: The bridge working storage; the module default when ``None``.
    """
    state = _resolve_session(session)
    file_access.we_error = WeError.UNKNOWN_UNEXPECTED
    file_access.fs_reply = FsReply.ERROR
    ba999_end(file_access, session=state)


def ba998_free(*, session: BridgeSession | None = None) -> None:
    """``ba998-Free.`` [common/nominalMT.cbl:L931-L941].

    Releases the stored result and, as its LAST act, marks the cursor inactive::

        move 20 to ws-No-Paragraph                                     [:L932]
        MOVE TP-GLLEDGER-REC TO WS-MYSQL-RESULT                        [:L938]
        CALL "MySQL_free_result" USING WS-MYSQL-RESULT end-call        [:L939]
        set Cursor-Not-Active to true.                                 [:L941]

    It has NO ``GO TO``: it falls straight into ``ba999-end`` [:L943], which is why
    every ``go to ba998-Free`` in the bridge also produces a log record. Delegated to
    :meth:`cursor_state.CursorState.free`, which owns both statements - including
    the frozen behaviour that the end-of-file sites do NOT free and merely set the
    flag, leaving the snapshot allocated for the next positioning read to overwrite.

    Args:
        session: The bridge working storage; the module default when ``None``.
    """
    state = _resolve_session(session)
    state.ws_no_paragraph = BRIDGE_PARAGRAPH_NUMBERS["ba998-Free"][0]
    state.cursor_states.state_for(TABLE_NAME, CursorSlot.PRIMARY).free()


def ba999_end(file_access: FileAccess, *, session: BridgeSession | None = None) -> None:
    """``ba999-end.`` [common/nominalMT.cbl:L943-L948].

    The bridge's single exit, and its only logging site::

        if       Testing-1
                 perform Ca-Process-Logs.                              [:L946-L947]

    ``Testing-1`` is ``SW-Testing = 1`` [copybooks/Test-Data-Flags.cob:L10-L11],
    whose declared ``VALUE`` is 1 - so logging is ON by default, with the
    maintainer's note that "When testing comlete you can set SW-Testing to zero to
    stop the logging file being produced" [:L3-L4]. The typo is his.

    ``ba999-exit`` [:L950-L951] is ``exit program``, i.e. the return to the handler,
    which is the ``return`` at the end of each caller here.

    Args:
        file_access: The block whose ``Logging-Data`` is written out.
        session: The bridge working storage; the module default when ``None``.
    """
    state = _resolve_session(session)
    file_access.logging_data.ws_no_paragraph = state.ws_no_paragraph
    # `if Testing-1 perform Ca-Process-Logs.` [:L946-L947]. `ACAS-DAL-Common-data`
    # is the bridge's own second parameter [common/acas005.cbl:L664], so the switch
    # is reachable here; the gate is reproduced rather than assumed open.
    dal_common = state.dal_common
    if dal_common is not None and dal_common.sw_testing == _TESTING_1:
        ca_process_logs(file_access, dal_common)


#  CA-PROCESS-LOGS  -  THE FH LOGGER

#: ``88 Testing-1 value 1.`` [copybooks/Test-Data-Flags.cob:L11]. The switch's
#: declared ``VALUE`` is 1, so DAL logging is ON by default; the maintainer's note
#: at [:L3-L4] says "When testing comlete you can set SW-Testing to zero to stop the
#: logging file being produced" - his spelling, preserved in the citation.
_TESTING_1: Final[int] = 1

#: ``88 Testing-2 value 1.`` [copybooks/Test-Data-Flags.cob:L17]. Declared ``VALUE``
#: zero, i.e. off, and it gates only ``display Display-Message-1`` diagnostics
#: [common/nominalMT.cbl:L495-L497, :L613-L615, :L744-L746, :L898-L900]. Per Agent
#: Action Plan 0.3.4 a display with no database effect becomes a log record at
#: matching severity, so those sites log at debug and change no control flow.
_TESTING_2: Final[int] = 1


def ca_process_logs(file_access: FileAccess, dal_common: AcasDalCommonData) -> None:
    """``Ca-Process-Logs.`` [common/nominalMT.cbl:L1367-L1372] and
    [common/acas005.cbl:L675-L680].

    Both the bridge and the handler have a paragraph of this name and both do the
    same one thing::

        call     "fhlogger" using File-Access
                                 ACAS-DAL-Common-data.

    ``fhlogger`` is a separate COBOL program [common/fhlogger.cbl] that appends a
    line to a log file, and Agent Action Plan 0.2.2 puts it OUT OF SCOPE by name
    among the "Non-posting utilities". Rule R-1 forbids calling it in any case: "The
    Python implementation must not execute, embed, or shell out to the COBOL
    programs."

    So the CALL becomes a log record on this module's own logger, carrying the same
    fields the logger would have written - the paragraph number, the file key, the
    where-clause and the SQL diagnostics. It has NO database effect and NO effect on
    control flow, which is the treatment Agent Action Plan 0.3.4 prescribes for
    output that does not reach a table.

    ``Log-File-Rec-Written`` [copybooks/Test-Data-Flags.cob:L20] is advanced, because
    the counter lives in ``ACAS-DAL-Common-data`` - shared with the handler, per its
    comment "in both acas0nn and a DAL" - and a caller can read it. It is plain
    accounting of records written, not a clock or a random source, so it does not
    disturb the determinism rule R-6 requires. IT IS ADVANCED MODULO ONE MILLION,
    which this module used not to do: the field is ``pic 9(6)``, so it wraps rather
    than growing, and an unbounded Python integer diverged from the frozen value the
    moment a run wrote a millionth record.

    ONE ADAPTER FOR ALL TWENTY HANDLERS. The record is composed by
    :func:`acas_posting.dal.status.log_file_handler_record`, so this handler's field
    set, level and counter arithmetic are identical to every other handler's rather
    than a local reading of the same one-line paragraph. Three fields are withheld
    and the withholding is the point: ``WS-File-Key`` is the nominal-ledger ACCOUNT
    NUMBER, ``WS-Log-Where`` is the composed ``WHERE`` clause it was built into, and
    ``SQL-Msg`` is the driver's free text. ``redact_for_log`` was applied to all three
    and could not help - its rules recognise connection-message shapes, not account
    numbers - so they are not reported at all (CWE-532). ``WS-Count-Rows`` goes with
    them: it belongs to ``Delete-All`` reporting rather than to the trace.

    Args:
        file_access: The block whose ``Logging-Data`` is written out.
        dal_common: The switch block, whose counter is advanced.
    """
    logging_data = file_access.logging_data
    log_file_handler_record(
        _LOG,
        program=HANDLER_NAME,
        paragraph="ca-Process-Logs",
        log_system=logging_data.ws_log_system,
        log_file_no=logging_data.ws_log_file_no,
        no_paragraph=logging_data.ws_no_paragraph,
        file_function=file_access.file_function,
        access_type=file_access.access_type,
        fs_reply=file_access.fs_reply,
        we_error=file_access.we_error,
        sql_err=logging_data.sql_err,
        sql_state=logging_data.sql_state,
        dal_common=dal_common,
    )


def ca_exit() -> None:
    """``ca-Exit.`` [common/acas005.cbl:L681-L682].

    ``exit section.`` - a structural no-op that exists only to terminate the logging
    section, and the bridge has the mirror-image ``ba999-exit``
    [common/nominalMT.cbl:L950-L951].

    Kept as a function because rule R-5 asks that every paragraph reproduced have a
    correspondingly named counterpart, so a reader walking the COBOL finds one here
    too. It performs nothing because the COBOL performs nothing: the ``return`` at
    the end of each calling function IS the section exit. Recorded as a
    representation-only reproduction, in the same spirit as Agent Action Plan
    0.4.3's treatment of ``gl072``'s unused facade stubs.
    """


#  NOMINAL_MT  -  THE BRIDGE ENTRY POINT, THREE PARAMETERS

def nominal_mt(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    ledger: WsLedgerRecord,
    *,
    system_record: SystemRecord | None = None,
    session: BridgeSession | None = None,
) -> None:
    """``call "nominalMT" using File-Access ACAS-DAL-Common-data WS-Ledger-Record``.

    The bridge-level entry, with the frozen parameter order preserved so a reviewer
    can diff the argument lists. From ``ba020-Process-DAL``
    [common/acas005.cbl:L662-L668], verbatim::

        ba020-Process-DAL.
            call     "nominalMT" using File-Access
                                       ACAS-DAL-Common-data
                                       WS-Ledger-Record
            end-call.

    THREE parameters, and ``File-Access`` FIRST - not the five-parameter,
    ``System-Record``-first shape of the handler :func:`dispatch`. Rule R-5 asks for
    both signatures to be published precisely so the difference is visible.

    Dispatches on ``File-Function`` through the bridge's own ``evaluate``
    [common/nominalMT.cbl:L360-L389], whose arms are 1, 2, 3, 4, 5, 7, 8, 9 in that
    order with ``when other`` falling to ``ba100-Bad-Function`` - the same order and
    the same omissions as the handler's, including no ``when 6``.

    Args:
        file_access: ``File-Access`` [copybooks/wsfnctn.cob:L23-L38], supplying
            ``File-Function``, ``Access-Type`` and ``RDB-Data``, and receiving
            ``FS-Reply``, ``We-Error`` and all ``Logging-Data``.
        dal_common: ``ACAS-DAL-Common-data``
            [copybooks/Test-Data-Flags.cob:L6], the testing switches and the
            log-record counter.
        ledger: ``WS-Ledger-Record`` [copybooks/wsledger.cob:L12], the record buffer
            - read on write and re-write, written on the two read paths.
        system_record: Carried for :func:`connection.mysql_1000_open`; see the
            plumbing note on :attr:`BridgeSession.system_record`. Not a fourth
            COBOL parameter.
        session: The bridge working storage; the module default when ``None``.
    """
    state = _resolve_session(session)
    state.dal_common = dal_common
    if system_record is not None:
        state.system_record = system_record
    function = file_access.file_function
    # `evaluate File-Function` [common/nominalMT.cbl:L360-L389]. Arm order
    # 1,2,3,4,5,7,8,9 - re-write (7) BEFORE delete (8), no `when 6`.
    if function == FileFunction.OPEN:
        ba020_process_open(file_access, session=state)
    elif function == FileFunction.CLOSE:
        ba030_process_close(file_access, session=state)
    elif function == FileFunction.READ_NEXT:
        ba040_process_read_next(file_access, ledger, session=state)
    elif function == FileFunction.READ_INDEXED:
        ba050_process_read_indexed(file_access, ledger, session=state)
    elif function == FileFunction.WRITE:
        ba070_process_write(file_access, ledger, session=state)
    elif function == FileFunction.RE_WRITE:
        ba090_process_rewrite(file_access, ledger, session=state)
    elif function == FileFunction.DELETE:
        ba080_process_delete(file_access, ledger, session=state)
    elif function == FileFunction.START:
        ba060_process_start(file_access, ledger, session=state)
    else:
        # `when other go to ba100-Bad-Function` [:L387-L388], and the unconditional
        # `go to ba100-Bad-Function` that follows the `end-evaluate` [:L388] as the
        # "should never get here but in case" guard.
        ba100_bad_function(file_access, session=state)


def ba020_process_dal(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    ledger: WsLedgerRecord,
    *,
    system_record: SystemRecord | None = None,
    session: BridgeSession | None = None,
) -> None:
    """``ba020-Process-DAL.`` [common/acas005.cbl:L662-L669].

    The HANDLER's paragraph that issues the bridge ``CALL``. It contains nothing
    else - no status handling, no logging - so it is a single delegation to
    :func:`nominal_mt`, kept as its own named function because rule R-5 asks for one
    Python function per COBOL paragraph.

    Note the parameter order it passes is the BRIDGE's, ``File-Access`` first, and
    not the order this handler itself was called with; that re-ordering is the whole
    content of the paragraph.

    Args:
        file_access: ``File-Access``, passed through first.
        dal_common: ``ACAS-DAL-Common-data``, passed through second.
        ledger: ``WS-Ledger-Record``, passed through third.
        system_record: Carried for the connection open; see
            :attr:`BridgeSession.system_record`.
        session: The bridge working storage; the module default when ``None``.
    """
    nominal_mt(
        file_access, dal_common, ledger, system_record=system_record, session=session
    )


#  BA-PROCESS-RDBMS SECTION  -  THE HANDLER'S RDB SIDE

def _ws_ledger_record_length() -> int:
    """Return ``function Length (WS-Ledger-Record)`` [common/acas005.cbl:L605-L607].

    Summed from the record layer's own descriptors rather than written out as a
    literal: every storage-allocating elementary field contributes its width, and
    groups and REDEFINES views contribute nothing because they allocate no storage
    of their own. That yields 126, which is what the maintainer's header records -
    "31/01/18 vbc - Resized to 126 bytes." [copybooks/wsledger.cob:L10] - and what
    GnuCOBOL 3.2.0 reports for the real copybook, measured directly.

    Returns:
        The record length in bytes.
    """
    total = 0
    for descriptor in WsLedgerRecord.FIELDS:
        parent = descriptor.parent_group
        if descriptor.is_group or descriptor.redefines:
            continue
        if parent and str(parent).lower().startswith("filler"):
            # Subordinate to a `filler redefines ...` group, so it shares storage
            # already counted - `Ledger-n`/`Ledger-s` over `WS-Ledger-Nos`
            # [copybooks/wsledger.cob:L16-L18] and `Ledger-Q` over `Quarters`
            # [:L35-L36].
            continue
        total += descriptor.byte_length * (descriptor.occurs or 1)
    return total


#: ``function Length (WS-Ledger-Record)`` - the ``A`` of the record-length guard,
#: computed once. 126 bytes [copybooks/wsledger.cob:L10].
WS_LEDGER_RECORD_LENGTH: Final[int] = _ws_ledger_record_length()

#: ``function length (Ledger-Record)`` - the ``B`` of the guard.
#:
#: ``Ledger-Record`` is the FD record of the indexed file, and the copybook's own
#: header records where it came from: "04/01/17 vbc - Taken from fdledger."
#: [copybooks/wsledger.cob:L8]. The two layouts are therefore the SAME layout, so
#: ``A`` and ``B`` are equal and the guard never fires for this handler. The
#: comparison is reproduced anyway, because the guard is what the frozen source
#: does and because an equal pair is a fact about this table rather than a licence
#: to drop the test.
LEDGER_RECORD_LENGTH: Final[int] = WS_LEDGER_RECORD_LENGTH


def ba010_test_ws_rec_size(file_access: FileAccess) -> None:
    """``ba010-Test-WS-Rec-Size.`` [common/acas005.cbl:L594-L600].

    The whole paragraph is ONE statement [common/acas005.cbl:L600]::

        move     21 to WS-Log-File-no.        *> for FHlogger

    ANOMALY N-LOG - REPRODUCED. ``WS-Log-File-No`` was set to 11 on entry to the
    program [common/acas005.cbl:L284], with the comment "Cobol/RDB, File/Table
    within sub System"; the moment the RDB path is entered it becomes 21. So the
    SAME handler logs under two different file numbers depending on which store it
    used, and only the RDB value can ever reach a DAL log record. 21 is reproduced
    because 21 is what this path is.

    Note also the CAPITALISATION: the declaration and the first move spell
    ``WS-Log-File-No`` [copybooks/wsfnctn.cob, common/acas005.cbl:L284] and this one
    spells ``WS-Log-File-no``. COBOL is case-insensitive so it is the same field;
    recorded because it is the kind of difference that makes a reader doubt a
    transcription. ``acas008`` has the identical two-value pattern with 15 and 25.

    The paragraph has no ``GO TO``: it falls straight into
    :func:`ba012_test_ws_rec_size_2`.

    Args:
        file_access: The block whose ``Logging-Data`` receives the file number.
    """
    file_access.logging_data.ws_log_file_no = WS_LOG_FILE_NO_RDB


def ba012_test_ws_rec_size_2(
    file_access: FileAccess,
    system_record: SystemRecord,
    dal_common: AcasDalCommonData,
) -> bool:
    """``ba012-Test-WS-Rec-Size-2.`` [common/acas005.cbl:L602-L643].

    Two jobs inside ONE first-call-only guard, ``if A = zero`` [:L604], whose
    ``end-if`` closes after BOTH [:L643]:

    1. compare the working-storage record length against the FD record length and,
       if the working-storage one is SHORTER, refuse [:L608-L613];
    2. otherwise load the six connection parameters out of the system record
       [:L637-L642], in the order Schema, UName, UPass, PORT, HOST, Socket - note
       Port before Host, which is NOT the order the bridge later builds its
       connection strings in [common/nominalMT.cbl:L395-L418]. Both orders are
       preserved where they occur.

    The credential half is :func:`connection.load_rdb_data_once`, which owns the
    first-call-only semantics as its own ANOMALY A-1 - a ``SYSTEM-REC`` change
    part-way through a run cannot affect that run - and is therefore CALLED rather
    than duplicated here.

    The refusal path [:L614-L631] displays two messages, logs, and then ``accept
    Accept-Reply at 2433`` before ``go to ba-rdbms-exit``. Per Agent Action Plan
    0.3.4 the ACCEPT is a pause for acknowledgement with no database effect, so it
    is DROPPED, while the CONTROL TRANSFER it guards is preserved - this returns
    ``False`` and the caller goes straight to :func:`ba_rdbms_exit` without ever
    reaching the bridge. The maintainer's own comment on the pair is "record length
    wrong so display error, accept and then stop run." [:L613] and, on the check
    itself, "COULD LET caller module deal with these errors !!!!!!!" [:L608].

    * GO TO CLASS 3 (section exit) at [:L631].

    Args:
        file_access: The block receiving ``RDB-Data`` and, on refusal, ``(99, 901)``.
        system_record: The source of the six connection parameters.
        dal_common: The switch block; ``Testing-1`` gates the log on the refusal
            path [:L626-L628].

    Returns:
        ``True`` to continue to the bridge, ``False`` when the record-length guard
        fired and the section must exit.
    """
    # `if A < B` [:L608] - the working-storage record must be at least as long as
    # the file record, "allow for last field ( FILLER) not being present in layout."
    if WS_LEDGER_RECORD_LENGTH < LEDGER_RECORD_LENGTH:
        # `move 901 to WE-Error` then `move 99 to fs-reply` [:L609-L610].
        file_access.we_error = WeError.RECORD_SIZE_MISMATCH
        file_access.fs_reply = FsReply.ERROR
        # `display Display-Blk at 2301` / `display GL901 at 2401` [:L623-L624] - two
        # screen writes with no database effect, and AAP 0.3.4 treats them
        # DIFFERENTLY, because they say different things.
        #   * `GL902 Program Error: Temp rec = ` [common/acas005.cbl:L253] plus the
        #     two lengths is the substantive diagnostic, and becomes this record.
        #   * `GL901 Note error and hit return` [:L252] is an acknowledgement prompt
        #     and nothing else. It is dropped, with the pause it introduces.
        #   * The transfer that follows is preserved by the `return False` below.
        # The two lengths are record-layout constants of this migration, not data.
        _LOG.error(
            "GL902 Program Error: Temp rec = %s < NL-Rec = %s - programming "
            "error, the caller must stop [common/acas005.cbl:L609]",
            WS_LEDGER_RECORD_LENGTH,
            LEDGER_RECORD_LENGTH,
        )
        if dal_common.sw_testing == _TESTING_1:
            # `if Testing-1 perform Ca-Process-Logs` [:L626-L628].
            ca_process_logs(file_access, dal_common)
        # `accept Accept-Reply at 2433` [:L630] - DROPPED, per AAP 0.3.4.
        # `go to ba-rdbms-exit` [:L631] - PRESERVED, as the False below.
        return False
    # [:L637-L642] - the six moves, owned by connection.py's first-call-only load.
    file_access.rdb_data = load_rdb_data_once(system_record)
    return True


def ba015_test_ends(file_access: FileAccess) -> None:
    """``ba015-Test-Ends.`` [common/acas005.cbl:L644-L660].

    *** THE PARAGRAPH IS ENTIRELY COMMENTED OUT. IMPLEMENT NOTHING. ***

    ANOMALY N-DEADCODE - REPRODUCED BY REMAINING ABSENT. The body, verbatim
    [common/acas005.cbl:L651-L656]::

         *>    if       fn-Open
         *>       and   fn-Output
         *>             perform ba020-Process-Dal
         *>             set fn-Delete-All to true
         *>    end-if.

    under the heading "First check if there is an open output and if so open 1st then
    we need to force a DELETE-ALL call to the DAL. [ Backup code ]." [:L647-L648].

    The SAME block is commented out a second time in ``aa010-main``
    [common/acas005.cbl:L309-L314], there carrying the maintainer's reason in
    capitals of his own: "Special to allow RDB equivilent of Open file as output ...
    special Delete-All instead. -- NOT used with GL." [:L305-L307].

    In ``acas008`` the identical block is LIVE, and there ``Open-Output`` really does
    mean DELETE EVERY ROW [common/acas008.cbl:L313-L319, :L571-L574]. The divergence
    between the two handlers is deliberate on the maintainer's part - "NOT used with
    GL" is the specification - and reproducing it means this handler must NOT
    coerce an open-output into a delete-all, must NOT publish ``fn-Delete-All``, and
    must reach :func:`aa100_bad_function` if asked for function 6.

    What remains live in the paragraph is only its comments, including the note that
    a compiler directive ought to choose between pre-SQL translators [:L657-L659].
    Nothing there has a database effect.

    Args:
        file_access: Unused. Taken so the call sequence in
            :func:`ba_process_rdbms` reads as the COBOL's does, one call per
            paragraph in source order.
    """


def ba_rdbms_exit() -> None:
    """``ba-rdbms-exit.`` [common/acas005.cbl:L671-L672].

    ``exit section.`` - the RDB section's single exit. Reproduced as a named no-op
    for the same reason as :func:`ca_exit`: rule R-5 asks that every paragraph have a
    counterpart, and the ``return`` in each caller IS the section exit.
    """


def ba_process_rdbms(
    file_access: FileAccess,
    system_record: SystemRecord,
    dal_common: AcasDalCommonData,
    ledger: WsLedgerRecord,
    *,
    session: BridgeSession | None = None,
) -> None:
    """``ba-Process-RDBMS section.`` [common/acas005.cbl:L586-L672].

    The RDB half of the handler, headed by the maintainer's own summary: "Here we
    call the relevent RDBMS module for this table which will include processing any
    other joined tables as needed" [:L590-L591].

    Its four paragraphs run in source order with NO conditional between them - each
    falls into the next - so this is a straight sequence::

        ba010-Test-WS-Rec-Size      set the RDB log file number             [:L594]
        ba012-Test-WS-Rec-Size-2    length guard + first-call credentials   [:L602]
        ba015-Test-Ends             entirely commented out                  [:L644]
        ba020-Process-DAL           call "nominalMT"                        [:L662]
        ba-rdbms-exit               exit section                            [:L671]

    ``ba012`` is the only one that can break the sequence, and it does so by
    ``go to ba-rdbms-exit`` [:L631] when the record-length guard fires.

    NOTE WHAT DOES NOT HAPPEN HERE. The handler's own ``Ca-Process-Logs`` is NOT
    performed on this path, and the maintainer says why in the paragraph header:
    "Not called on DAL access as it does it already" [:L675]. The DAL logs from
    ``ba999-end`` [common/nominalMT.cbl:L946-L947] instead, which is why
    :func:`ba999_end` carries the ``Testing-1`` gate and this section does not.

    Also note the asymmetry with the section's own capitalisation: the flat-file
    section is declared ``aa-Process-Flat-File Section.`` with a capital
    [common/acas005.cbl:L277] and this one ``ba-Process-RDBMS section.`` with a
    lower case [:L586]. COBOL does not care; ANOMALY N-SECTION-CASE records it so a
    reader comparing the two files does not think one was mistyped here.

    Args:
        file_access: ``File-Access``, carrying the verb and receiving the status.
        system_record: ``System-Record``, the source of the connection parameters.
        dal_common: ``ACAS-DAL-Common-data``, the switches and the log counter.
        ledger: ``WS-Ledger-Record``, the record buffer.
        session: The bridge working storage; the module default when ``None``.
    """
    state = _resolve_session(session)
    state.system_record = system_record
    state.dal_common = dal_common
    # ANOMALY N-SECTION-CASE - REPRODUCTION SITE (second of the pair). This
    # function is the section header spelled lower-case `ba-Process-RDBMS section.`
    # [common/acas005.cbl:L586], against the capitalised
    # `aa-Process-Flat-File Section.` [common/acas005.cbl:L277]. Both spellings
    # preserved exactly as the frozen source has them.
    ba010_test_ws_rec_size(file_access)
    if not ba012_test_ws_rec_size_2(file_access, system_record, dal_common):
        # `go to ba-rdbms-exit` [:L631] - GO TO CLASS 3.
        ba_rdbms_exit()
        return
    ba015_test_ends(file_access)
    ba020_process_dal(
        file_access, dal_common, ledger, system_record=system_record, session=state
    )
    ba_rdbms_exit()


#  AA-PROCESS-FLAT-FILE SECTION  -  THE HANDLER'S ISAM SIDE

#: ``move 255 to WE-Error`` - the code the flat-file paragraphs pair with
#: ``FS-Reply`` 21 on an invalid key [common/acas005.cbl:L478, :L503, :L510, :L517,
#: :L524]. It has NO name in :class:`status.WeError` because no other handler uses
#: it, and the maintainer annotated three of the five sites with bare question
#: marks - "USED by  GL?" [:L503], "USED ?" [:L517] and again [:L524] - so he did
#: not know either. Carried as its literal value.
_WE_ERROR_INVALID_KEY: Final[int] = 255

#: ``move 35 to fs-Reply`` - the code substituted when ``open input`` fails
#: [common/acas005.cbl:L371]. 35 is the standard file status for "file not found",
#: written over whatever the ``OPEN`` itself reported.
_FS_REPLY_OPEN_INPUT_FAILED: Final[int] = 35


#: THE STATUS DISPOSITIONS OF THE UNMIGRATED ISAM BRANCHES, recorded as data.
#:
#: The flat-file paragraphs below cannot run without a GnuCOBOL indexed-file engine,
#: which rule R-1 forbids this package from carrying, so each raises
#: :class:`CobolFileAccessNotMigratedError`. That is a deliberate omission, and rule
#: R-5 requires deliberate omissions be RECORDED rather than merely left out - so the
#: disposition each branch WOULD have written is captured here, keyed by paragraph,
#: as ``(condition, FS-Reply, We-Error, locator)``. A ``None`` in either status slot
#: means the branch does not touch that field, which for this handler is behaviour
#: rather than absence of behaviour - see :func:`aa060_process_start`.
#:
#: The table is the reviewable half of the omission: it lets the traceability
#: document state exactly what was not migrated and what it would have done, and it
#: gives a future ISAM implementation its acceptance criteria for free.
FLAT_FILE_STATUSES: Final[Mapping[str, tuple[tuple[str, int | None, int | None, str], ...]]] = (
    MappingProxyType(
        {
            "aa020-Process-Open": (
                (
                    "fn-input, open failed",
                    _FS_REPLY_OPEN_INPUT_FAILED,
                    None,
                    "[common/acas005.cbl:L371]",
                ),
                (
                    "fn-extend, always refused",
                    FsReply.ERROR,
                    WeError.ACCESS_TYPE_WRONG,
                    "[common/acas005.cbl:L390-L391]",
                ),
                (
                    "common tail, any non-zero fs-reply",
                    None,
                    WeError.NOT_USED,
                    "[common/acas005.cbl:L397-L399]",
                ),
            ),
            "aa040-Process-Read-Next": (
                (
                    "already at end of file",
                    FsReply.END_OF_FILE,
                    int(FsReply.END_OF_FILE),
                    "[common/acas005.cbl:L424-L425]",
                ),
            ),
            "aa041-Reread": (
                (
                    "at end",
                    FsReply.END_OF_FILE,
                    int(FsReply.END_OF_FILE),
                    "[common/acas005.cbl:L435]",
                ),
                (
                    "success, We-Error only",
                    None,
                    WeError.SUCCESS,
                    "[common/acas005.cbl:L446]",
                ),
            ),
            "aa050-Process-Read-Indexed": (
                (
                    # `move 21 to fs-reply` [:L477] - 21, not 23, and note the enum
                    # name INVALID_KEY_ON_START describes only one of this value's
                    # three users in this handler.
                    "invalid key",
                    FsReply.INVALID_KEY_ON_START,
                    _WE_ERROR_INVALID_KEY,
                    "[common/acas005.cbl:L477-L478]",
                ),
            ),
            "aa060-Process-Start": (
                (
                    "access-type < 5 or > 8, FS-Reply UNTOUCHED",
                    None,
                    WeError.FILE_KEY_NO_OUT_OF_RANGE,
                    "[common/acas005.cbl:L496]",
                ),
                (
                    "invalid key, all four relations",
                    FsReply.INVALID_KEY_ON_START,
                    _WE_ERROR_INVALID_KEY,
                    "[common/acas005.cbl:L502-L503, :L509-L510, :L516-L517, :L523-L524]",
                ),
            ),
            "aa070-Process-Write": (
                (
                    "invalid key, We-Error UNTOUCHED",
                    FsReply.DUPLICATE_KEY,
                    None,
                    "[common/acas005.cbl:L541]",
                ),
            ),
            "aa080-Process-Delete": (
                (
                    # `move 21 to FS-Reply` [:L553] - the DELETE uses 21 where the
                    # WRITE four paragraphs above uses 22. Both are reproduced.
                    "invalid key, We-Error UNTOUCHED",
                    FsReply.INVALID_KEY_ON_START,
                    None,
                    "[common/acas005.cbl:L553]",
                ),
            ),
            "aa090-Process-Rewrite": (
                (
                    "NO invalid-key clause exists, so nothing is written",
                    None,
                    None,
                    "[common/acas005.cbl:L563]",
                ),
            ),
        }
    )
)


def aa020_process_open(
    file_access: FileAccess, dal_common: AcasDalCommonData | None = None
) -> None:
    """``aa020-Process-Open.`` [common/acas005.cbl:L365-L400].

    Opens the indexed file in one of four modes. THE ONLY MODE FULLY REPRODUCIBLE
    WITHOUT AN ISAM ENGINE IS ``fn-extend``, because it is the one that never touches
    a file::

         if   fn-extend                      *> Must not be used for ISAM files
    *>              open extend Ledger-File
              move 997 to WE-Error                                     [:L390]
              move 99  to FS-Reply                                     [:L391]
              go to aa999-main-exit                                    [:L392]
         end-if

    Note that the ``open extend`` itself is COMMENTED OUT [:L389] - the maintainer
    disabled the verb and left the refusal - and note the ORDER, ``We-Error`` 997
    first and then ``FS-Reply`` 99. ``997`` is
    :attr:`status.WeError.ACCESS_TYPE_WRONG`.

    The other three modes issue real ISAM verbs and therefore raise
    :class:`CobolFileAccessNotMigratedError`; their status logic is documented here
    so the reproduction is complete and reviewable:

    * ``fn-input`` [:L368-L375] - ``open input``; on failure ``move 35 to fs-Reply``,
      CLOSE the file again, and exit. The substitution discards whatever the OPEN
      reported.
    * ``fn-i-o`` [:L377-L384] - ``open i-o``; on failure close, ``open output``,
      close, ``open i-o`` again, with the maintainer's reason "Doesnt create in i-o".
      NO status is written by the retry, so a second failure is reported by the OPEN
      itself.
    * ``fn-output`` [:L386-L387] - ``open output``, and "caller should check
      fs-reply". No coercion to a delete-all: see :func:`ba015_test_ends`.

    The common tail [:L395-L399] then runs ``move zero to Cobol-File-Status``,
    ``move "OPEN GL NL File" to WS-File-Key``, and
    ``if fs-reply not = zero move 999 to we-error.`` - so a failed open that reached
    the tail reports ``We-Error`` 999, which is
    :attr:`status.WeError.NOT_USED`.

    * GO TO CLASS 3 at [:L373], [:L392] and [:L399].

    Args:
        file_access: The block supplying ``Access-Type`` and receiving the status.
        dal_common: The handler's fifth linkage parameter, forwarded to
            :func:`aa999_main_exit` for the ``Testing-1`` log gate.

    Raises:
        CobolFileAccessNotMigratedError: For ``fn-input``, ``fn-i-o`` and
            ``fn-output``, which need an ISAM engine this package does not ship.
    """
    # `move spaces to WS-File-Key.` [:L366] then `move 201 to WS-No-Paragraph.`
    # [:L367] - in that order, and the tag is replaced again at [:L396].
    _set_file_key(file_access, "")
    file_access.logging_data.ws_no_paragraph = HandlerParagraph.OPEN
    access_type = file_access.access_type
    if access_type == AccessType.EXTEND:
        # [:L388-L392]. `open extend` is commented out at [:L389]; only the refusal
        # is live. We-Error FIRST, then FS-Reply.
        file_access.we_error = WeError.ACCESS_TYPE_WRONG
        file_access.fs_reply = FsReply.ERROR
        aa999_main_exit(file_access, dal_common)
        return
    raise CobolFileAccessNotMigratedError(FileFunction.OPEN, access_type=access_type)


def aa030_process_close(file_access: FileAccess) -> None:
    """``aa030-Process-Close.`` [common/acas005.cbl:L402-L412].

    Closes the indexed file and logs TWICE::

        move 202 to WS-No-Paragraph                                    [:L403]
        move spaces to WS-File-Key                                     [:L404]
        close Ledger-File                                              [:L405]
        move zero to Cobol-File-Status                                 [:L407]
        move "CLOSE GL NL File" to WS-File-Key                         [:L408]
        perform aa999-main-exit                                        [:L409]
        move zero to File-Function Access-Type   *> close log file      [:L410-L411]
        perform Ca-Process-Logs                                        [:L412]
        go to aa-main-exit                                             [:L413]

    The double log is deliberate: [:L409] is a ``PERFORM``, so it logs the close and
    RETURNS, and then the verb and access type are zeroed and it logs AGAIN. The
    second record - with ``File-Function`` and ``Access-Type`` both zero - is the
    convention that tells ``fhlogger`` to close its own file, which is what the
    comment "close log file" means. Note also that the second call is UNCONDITIONAL
    where the first is gated by ``Testing-1`` inside ``aa999-main-exit``.

    One line is commented out at [:L406]: ``move zeros to FS-Reply WE-Error``, dated
    "27/07/16 16:30". So a close does NOT clear the status pair, and whatever the
    previous verb left stands - reproduced by not writing it.

    * GO TO CLASS 3 at [:L413].

    Args:
        file_access: The block receiving the tag and the log records.

    Raises:
        CobolFileAccessNotMigratedError: The ``close`` is an ISAM verb.
    """
    file_access.logging_data.ws_no_paragraph = HandlerParagraph.CLOSE
    _set_file_key(file_access, "")
    raise CobolFileAccessNotMigratedError(FileFunction.CLOSE)


def aa040_process_read_next(file_access: FileAccess) -> None:
    """``aa040-Process-Read-Next.`` [common/acas005.cbl:L415-L430].

    The positioning guard for the flat-file read, whose own header says it "is
    processed after Start code as its really Start/Read next at point aa041"
    [:L419-L420]::

        move     203 to WS-No-Paragraph.                               [:L422]
        if       Cobol-File-Eof          *> This block should NOT occur [:L423]
                 move 10 to FS-Reply WE-Error                          [:L424-L425]
                 move spaces to WS-Ledger-Key SQL-Err SQL-Msg          [:L426-L428]
                 stop "Cobol File EOF"                                 [:L429]
                 go to aa999-main-exit                                 [:L430]
        end-if.

    Two things to note. The guard's own comment says it "should NOT occur", and the
    ``stop`` literal carries "for testing because it should not have got here !!" -
    a ``STOP`` with a literal HALTS THE RUN until the operator acknowledges, which is
    a behaviour no batch migration can keep; it has no database effect, so per Agent
    Action Plan 0.3.4 it becomes a log record while the control transfer that follows
    it is preserved. And ``move spaces to WS-Ledger-Key`` writes SPACES into a
    ``9(6)``/``9(2)`` numeric group, leaving it non-numeric - which is exactly the
    condition ``gl072`` silently skips on [general/gl072.cbl:L291-L292] - the
    statement the anomaly register cites as [general/gl072.cbl:L289-L290], which in
    the frozen checkout is the ``go to end-run`` of the at-end clause.

    Falls through into :func:`aa041_reread` when not at end of file.

    * GO TO CLASS 3 at [:L430].

    Args:
        file_access: The block receiving the status.

    Raises:
        CobolFileAccessNotMigratedError: The read is an ISAM verb.
    """
    file_access.logging_data.ws_no_paragraph = HandlerParagraph.READ_NEXT
    raise CobolFileAccessNotMigratedError(FileFunction.READ_NEXT)


def aa041_reread(file_access: FileAccess) -> None:
    """``aa041-Reread.`` [common/acas005.cbl:L433-L448].

    The flat-file delivery stage, reached by fall-through from
    :func:`aa040_process_read_next` [:L431] - there is no ``PERFORM`` of it anywhere,
    so fall-through is its ONLY entry::

        read Ledger-File next record at end                            [:L434]
             move 10 to WE-Error FS-Reply                              [:L435]
             set Cobol-File-EoF to true                                [:L436]
             move 1 to Cobol-File-Status   *> JIC above dont work :)    [:L437]
             initialize WS-Ledger-Record                               [:L438]
             move "EOF" to WS-File-Key                                 [:L439]
             go to aa999-main-exit                                     [:L440]
        end-read.
        if   FS-Reply not = zero  go to aa999-main-exit.                [:L442-L443]
        move Ledger-Record to WS-Ledger-Record.                        [:L444]
        move Ledger-Key    to WS-File-Key.                             [:L445]
        move zeros to WE-Error.                                        [:L446]

    Note the ``initialize WS-Ledger-Record`` at [:L438] is the PLAIN form, so it
    leaves the 55 filler bytes alone - see :func:`_initialize_ws_ledger_record` for
    the oracle evidence. The bridge's own EOF2 branch uses ``WITH FILLER`` instead
    [common/nominalMT.cbl:L575]; two forms, two behaviours, both preserved.

    Note too that the success tail zeroes ``We-Error`` ONLY [:L446] and leaves
    ``FS-Reply`` as the ``READ`` set it - whereas the bridge's equivalent zeroes both
    [common/nominalMT.cbl:L591].

    * GO TO CLASS 3 at [:L440], [:L443] and [:L448].

    Args:
        file_access: The block receiving the status.

    Raises:
        CobolFileAccessNotMigratedError: The read is an ISAM verb.
    """
    raise CobolFileAccessNotMigratedError(FileFunction.READ_NEXT)


def aa047_eval_keys(file_access: FileAccess, ledger: WsLedgerRecord) -> None:
    """``aa047-Eval-Keys.`` [common/acas005.cbl:L451-L466].

    Sets the log key, and ONLY the log key - the maintainer's own comment on the
    ``evaluate`` is "Set up keys just for logging" [:L452].

    Its heading, verbatim [:L449]: "The next block will never get executed unless
    performed". That is accurate rather than an admission of dead code: nothing falls
    into it, but it IS performed, twice - from ``aa050-Process-Read-Indexed`` [:L474]
    and from ``aa060-Process-Start`` [:L490]. So it is reached on exactly two of the
    eight verbs, and NOT on write, re-write or delete, despite listing all five of
    ``4``, ``5``, ``7``, ``8`` and ``9`` in its own ``evaluate`` [:L453-L457]. Three
    of those five arms can therefore never be taken. Reproduced by calling it from
    the same two places and no others.

    The inner ``evaluate File-Key-No`` [:L458-L464] moves ``WS-Ledger-Key`` to BOTH
    ``WS-File-Key`` and ``Ledger-Key`` when the key number is 1, and spaces to
    ``WS-File-Key`` otherwise. The second target is the FD key, so on the RDB path
    only the first is meaningful.

    Args:
        file_access: The block whose ``WS-File-Key`` is set.
        ledger: The record supplying ``WS-Ledger-Key``.
    """
    function = file_access.file_function
    guarded = (
        FileFunction.READ_INDEXED,
        FileFunction.WRITE,
        FileFunction.RE_WRITE,
        FileFunction.DELETE,
        FileFunction.START,
    )
    if function in guarded:
        if file_access.logging_data.file_key_no == FILE_KEY_NO:
            # `move WS-Ledger-Key to WS-File-Key Ledger-Key` [:L460-L461].
            _set_file_key(file_access, ws_ledger_key_bytes(ledger))
        else:
            # `when other move spaces to WS-File-Key` [:L462-L463].
            _set_file_key(file_access, "")
        return
    # `when other move spaces to WS-File-Key` [:L464-L465].
    _set_file_key(file_access, "")


def aa050_process_read_indexed(file_access: FileAccess, ledger: WsLedgerRecord) -> None:
    """``aa050-Process-Read-Indexed.`` [common/acas005.cbl:L469-L483].

    ``move 204 to WS-No-Paragraph`` [:L473], ``perform aa047-Eval-keys`` [:L474],
    ``move zero to Cobol-File-Status`` [:L475], then ``read ... invalid key`` giving
    ``move 21 to fs-reply`` and ``move 255 to WE-Error`` [:L477-L479]. On success
    ``move Ledger-Record to WS-Ledger-Record`` and ``move Ledger-Key to WS-File-Key``
    [:L481-L482].

    Note the commented-out ``*>   we-error`` fragment on [:L477] and the odd
    indentation of the ``move 255`` on [:L478] - the maintainer added the second
    statement later. The bridge's equivalent uses ``(21, 0)`` instead
    [common/nominalMT.cbl:L635-L636], so the SAME verb reports a miss with two
    different ``We-Error`` values depending on the store.

    * GO TO CLASS 3 at [:L479] and [:L483].

    Args:
        file_access: The block receiving the status.
        ledger: The record supplying the key.

    Raises:
        CobolFileAccessNotMigratedError: The read is an ISAM verb.
    """
    file_access.logging_data.ws_no_paragraph = HandlerParagraph.READ_INDEXED
    # `perform aa047-Eval-keys.` [:L474] - one of its only two call sites.
    aa047_eval_keys(file_access, ledger)
    raise CobolFileAccessNotMigratedError(FileFunction.READ_INDEXED)


def aa060_process_start(
    file_access: FileAccess,
    ledger: WsLedgerRecord,
    dal_common: AcasDalCommonData | None = None,
) -> None:
    """``aa060-Process-Start.`` [common/acas005.cbl:L485-L531].

    Positions the indexed file. Its header carries a warning of its own: "Check for
    Param error 1st on start   WARNING Not logging starts" [:L487].

    THE GUARD, verbatim [common/acas005.cbl:L495-L499]::

        if       access-type < 5 or > 8                   *> NOT using 'not >'
                 move 998 to WE-Error       *> 998 Invalid calling parameter settings
                 go to aa999-main-exit
        end-if

    Two facts about it are easy to get wrong and both are reproduced:

    * the range REJECTS ACCESS TYPE 9. Only 5, 6, 7 and 8 pass, and the four ``start``
      variants below cover exactly those - equal-to, not-less-than, greater-than and
      less-than. There is no ``fn-not-greater-than`` branch at all.
    * it writes ``We-Error`` 998 and DOES NOT TOUCH ``FS-Reply``. That is not an
      oversight with no effect: ``move zeros to fs-reply WE-Error`` ran four lines
      earlier [:L492-L493], so the caller sees ``(0, 998)`` - a SUCCESS reply
      alongside an error code. The bridge's own guard writes the pair ``(99, 997)``
      instead [common/nominalMT.cbl:L693-L695], so the same rejection has two
      different dispositions depending on the store, and ANOMALY N-998 records that
      998 itself carries four different documented meanings across the codebase.

    Each of the four ``start`` variants reports an invalid key as
    ``(21, 255)`` [:L502-L503, :L509-L510, :L516-L517, :L523-L524].

    * GO TO CLASS 3 at [:L498], [:L504], [:L511], [:L518], [:L525] and [:L531].

    Args:
        file_access: The block supplying ``Access-Type`` and receiving the status.
        ledger: The record supplying the key.
        dal_common: The handler's fifth linkage parameter, forwarded to
            :func:`aa999_main_exit` for the ``Testing-1`` log gate.

    Raises:
        CobolFileAccessNotMigratedError: When the access type passes the guard, since
            the ``start`` itself is an ISAM verb.
    """
    file_access.logging_data.ws_no_paragraph = HandlerParagraph.START
    # `perform aa047-Eval-keys.` [:L490] - its second and last call site.
    aa047_eval_keys(file_access, ledger)
    # `move zeros to fs-reply WE-Error.` [:L492-L493] - BEFORE the guard, which is
    # what makes the guard's disposition (0, 998).
    file_access.fs_reply = FsReply.SUCCESS
    file_access.we_error = WeError.SUCCESS
    low, high = START_ACCESS_TYPE_RANGE
    if file_access.access_type < low or file_access.access_type > high:
        # `move 998 to WE-Error` [:L496] - and FS-Reply deliberately NOT touched.
        file_access.we_error = WeError.FILE_KEY_NO_OUT_OF_RANGE
        aa999_main_exit(file_access, dal_common)
        return
    raise CobolFileAccessNotMigratedError(
        FileFunction.START, access_type=file_access.access_type
    )


def aa070_process_write(file_access: FileAccess, ledger: WsLedgerRecord) -> None:
    """``aa070-Process-Write.`` [common/acas005.cbl:L534-L544].

    ``move 206 to WS-No-Paragraph`` [:L535], ``move WS-Ledger-Record to
    Ledger-Record`` [:L536], ``move zeros to FS-Reply WE-Error`` [:L537], ``move zero
    to Cobol-File-Status`` [:L538], ``move Ledger-Key to WS-File-Key`` [:L539], then
    ``write ... invalid key move 22 to FS-Reply`` [:L540-L542], then ``move
    WS-Ledger-Key to WS-File-Key`` [:L543].

    Note ``WS-File-Key`` is set TWICE, from two different sources - the FD
    ``Ledger-Key`` before the write and the working-storage ``WS-Ledger-Key`` after -
    so the tag that reaches the log is always the second. And note the status pair is
    zeroed BEFORE the write [:L537], the same ordering that keeps the bridge's own
    write clear of the silent-status defect.

    ``22`` is :attr:`status.FsReply.DUPLICATE_KEY`, and no ``We-Error`` accompanies
    it - a duplicate arrives as ``(22, 0)``, matching the bridge
    [common/nominalMT.cbl:L812].

    * GO TO CLASS 3 at [:L544].

    Args:
        file_access: The block receiving the status.
        ledger: The record to write.

    Raises:
        CobolFileAccessNotMigratedError: The ``write`` is an ISAM verb.
    """
    file_access.logging_data.ws_no_paragraph = HandlerParagraph.WRITE
    file_access.fs_reply = FsReply.SUCCESS
    file_access.we_error = WeError.SUCCESS
    _set_file_key(file_access, ws_ledger_key_bytes(ledger))
    raise CobolFileAccessNotMigratedError(FileFunction.WRITE)


def aa080_process_delete(file_access: FileAccess, ledger: WsLedgerRecord) -> None:
    """``aa080-Process-Delete.`` [common/acas005.cbl:L546-L555].

    ``move 207 to WS-No-Paragraph`` [:L547], ``move WS-Ledger-Key to Ledger-Key
    WS-File-Key`` [:L548-L549] - one ``MOVE``, two targets - ``move zeros to FS-Reply
    WE-Error`` [:L550], ``move zero to Cobol-File-Status`` [:L551], then
    ``delete ... invalid key move 21 to FS-Reply`` [:L552-L554].

    ``21`` here where the write uses 22, and again no ``We-Error``.

    * GO TO CLASS 3 at [:L555].

    Args:
        file_access: The block receiving the status.
        ledger: The record supplying the key.

    Raises:
        CobolFileAccessNotMigratedError: The ``delete`` is an ISAM verb.
    """
    file_access.logging_data.ws_no_paragraph = HandlerParagraph.DELETE
    _set_file_key(file_access, ws_ledger_key_bytes(ledger))
    file_access.fs_reply = FsReply.SUCCESS
    file_access.we_error = WeError.SUCCESS
    raise CobolFileAccessNotMigratedError(FileFunction.DELETE)


def aa090_process_rewrite(file_access: FileAccess, ledger: WsLedgerRecord) -> None:
    """``aa090-Process-Rewrite.`` [common/acas005.cbl:L557-L565].

    ``move 208 to WS-No-Paragraph`` [:L559], ``move WS-Ledger-Record to
    Ledger-Record`` [:L560], ``move zeros to FS-Reply WE-Error`` [:L561], ``move zero
    to Cobol-File-Status`` [:L562], then ``rewrite Ledger-Record.`` [:L563] and
    ``move Ledger-Key to WS-File-Key`` [:L564].

    THE ``rewrite`` HAS NO ``invalid key`` CLAUSE - alone among the four write verbs
    in this handler. So a re-write that matches no record reports whatever the
    ``REWRITE`` itself put in the file status and nothing more, and the zeroes from
    [:L561] may stand. That is the flat-file cousin of ANOMALY N-REWRITE-SILENT in
    the bridge [common/nominalMT.cbl:L901-L913]: the same verb, in the same handler,
    silently under-reports a failed re-write on BOTH stores, by two entirely
    different mechanisms. Recorded, not corrected.

    * GO TO CLASS 3 at [:L565].

    Args:
        file_access: The block receiving the status.
        ledger: The record to re-write.

    Raises:
        CobolFileAccessNotMigratedError: The ``rewrite`` is an ISAM verb.
    """
    file_access.logging_data.ws_no_paragraph = HandlerParagraph.RE_WRITE
    file_access.fs_reply = FsReply.SUCCESS
    file_access.we_error = WeError.SUCCESS
    raise CobolFileAccessNotMigratedError(FileFunction.RE_WRITE)


def aa100_bad_function(
    file_access: FileAccess, dal_common: AcasDalCommonData | None = None
) -> None:
    """``aa100-Bad-Function.`` [common/acas005.cbl:L567-L572].

    The handler's catch-all, under the maintainer's heading "Houston; We have a
    problem" [:L569]::

        move     999 to WE-Error.                         *> 999          [:L571]
        move     99  to fs-reply.                                        [:L572]

    ``999`` - NOT the ``990`` its counterpart ``ba100-Bad-Function`` uses
    [common/nominalMT.cbl:L922]. So an unsupported verb is reported as
    :attr:`status.WeError.NOT_USED` by the handler and as
    :attr:`status.WeError.UNKNOWN_UNEXPECTED` by the bridge, and which one the caller
    sees depends on how far down the chain the verb travelled. Both are reproduced at
    their own sites.

    ``We-Error`` is written FIRST, then ``FS-Reply``. It has NO ``GO TO``: it falls
    straight into :func:`aa999_main_exit`.

    THE VERBS THAT ARRIVE HERE. The dispatch ``evaluate`` [:L341-L360] has arms for
    1, 2, 3, 4, 5, 7, 8 and 9 only, so everything else lands here - specifically
    ``fn-Delete-All`` (6), ``fn-Write-Raw`` (15), ``fn-Read-Next-Raw`` (13) and the
    by-name/by-batch/by-customer/next-header reads (31 to 34). That ``6`` is absent
    is the direct consequence of ANOMALY N-DEADCODE: with the open-output coercion
    commented out [:L305-L314, :L651-L656], nothing in this handler ever sets
    ``fn-Delete-All``, so nothing needs to service it. In ``acas008``, where the
    coercion is live, it does.

    Args:
        file_access: The block receiving ``(99, 999)``.
        dal_common: The handler's fifth linkage parameter, forwarded to
            :func:`aa999_main_exit` for the ``Testing-1`` log gate.
    """
    file_access.we_error = WeError.NOT_USED
    file_access.fs_reply = FsReply.ERROR
    aa999_main_exit(file_access, dal_common)


def aa999_main_exit(
    file_access: FileAccess, dal_common: AcasDalCommonData | None = None
) -> None:
    """``aa999-main-exit.`` [common/acas005.cbl:L574-L577].

    The handler's logging gate::

        if       Testing-1
                 perform Ca-Process-Logs
        end-if.

    Reached by every ``go to aa999-main-exit`` in the flat-file section and by
    fall-through from :func:`aa100_bad_function`. It then falls into
    :func:`aa_main_exit`.

    On the RDB path this paragraph is NOT reached: ``aa010-main`` performs
    ``ba-Process-RDBMS`` and jumps to ``AA-Main-Exit`` directly
    [common/acas005.cbl:L318-L319], skipping it - which is consistent with the
    handler's own note that its ``Ca-Process-Logs`` is "Not called on DAL access as it
    does it already" [:L675].

    Args:
        file_access: The block whose ``Logging-Data`` is written out.
        dal_common: The handler's FIFTH linkage parameter
            [common/acas005.cbl:L274], supplying ``SW-Testing``. ``None`` means the
            caller passed no block, in which case ``Testing-1`` cannot be true and
            nothing is logged.
    """
    if dal_common is not None and dal_common.sw_testing == _TESTING_1:
        ca_process_logs(file_access, dal_common)


def aa_main_exit() -> None:
    """``aa-main-exit.`` [common/acas005.cbl:L579-L582].

    A label with no statements, carrying only the comment "Now have processed cobol
    flat file,  so .." [:L581]. It falls into :func:`aa_exit`.

    Reproduced as a named no-op because rule R-5 asks for one function per paragraph,
    and because it IS a real branch target - ``aa010-main`` jumps to it on the RDB
    path [common/acas005.cbl:L319] and ``aa030-Process-Close`` on the close path
    [:L413].
    """


def aa_exit() -> None:
    """``aa-Exit.`` [common/acas005.cbl:L583-L584].

    ``exit program.`` - the return to the caller of ``acas005``. The ``return`` at the
    end of :func:`dispatch` IS this statement; the function exists so a reader
    following the COBOL finds it.
    """


#  AA010-MAIN AND THE HANDLER ENTRY POINT

#: The dispatch table of ``aa010-main``'s ``evaluate File-Function``
#: [common/acas005.cbl:L340-L361], IN THE FROZEN SOURCE'S OWN ARM ORDER.
#:
#: THE ORDER IS 1, 2, 3, 4, 5, 7, 8, 9 - re-write (7) is dispatched BEFORE delete
#: (8), which is neither numeric order nor the order the paragraphs appear in the
#: program [:L365-L566], where delete's ``aa080`` precedes re-write's ``aa090``. Two
#: orderings of the same eight verbs coexist in one program. An ``evaluate`` is
#: order-insensitive when its ``when`` values are distinct, so the arm order has no
#: observable effect - but rule R-6 asks for the COBOL's statement order and this is
#: the cheapest possible way to keep it, so it is kept, and a reader diffing the two
#: files finds the arms where the COBOL puts them.
#:
#: ``6`` (``fn-Delete-All``) IS ABSENT, as are 13, 15 and 31 to 34. Everything absent
#: reaches :func:`aa100_bad_function`. See that function for why 6's absence is a
#: consequence of ANOMALY N-DEADCODE rather than an oversight.
DISPATCH_ORDER: Final[tuple[FileFunction, ...]] = (
    FileFunction.OPEN,  # `when  1  go to aa020-Process-Open`          [:L341-L342]
    FileFunction.CLOSE,  # `when  2  go to aa030-Process-Close`        [:L343-L344]
    FileFunction.READ_NEXT,  # `when  3  go to aa040-...-Read-Next`    [:L345-L346]
    FileFunction.READ_INDEXED,  # `when  4  go to aa050-...-Indexed`   [:L347-L348]
    FileFunction.WRITE,  # `when  5  go to aa070-Process-Write`        [:L349-L350]
    FileFunction.RE_WRITE,  # `when  7  go to aa090-Process-Rewrite`   [:L351-L352]
    FileFunction.DELETE,  # `when  8  go to aa080-Process-Delete`      [:L353-L354]
    FileFunction.START,  # `when  9  go to aa060-Process-Start`        [:L355-L356]
)


def aa_process_flat_file(
    system: SystemRecord,
    ledger: WsLedgerRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa-Process-Flat-File Section.`` [common/acas005.cbl:L277].

    The FIRST section of the procedure division, so entering the program enters this
    section, which falls straight into :func:`aa010_main` at [common/acas005.cbl:L279].
    Reproduced as its own function for the same reason :func:`ba_process_rdbms` is -
    rule R-5 asks for one function per paragraph and a section header is a paragraph
    for that purpose, and because the pair of section headers is where ANOMALY
    N-SECTION-CASE lives.

    ANOMALY N-SECTION-CASE. This header spells ``Section`` with a CAPITAL S
    [common/acas005.cbl:L277] while its sibling spells it ``section`` in lower case
    [common/acas005.cbl:L586]. COBOL is case-insensitive so nothing observable turns
    on it; it is recorded because rule R-4 asks for anomalies to be recorded rather
    than silently normalised, and because the pair is evidence the two sections were
    written at different times.

    THE ``GO TO`` CENSUS FOR THIS PROGRAM, taken over every live (non-commented)
    transfer in [common/acas005.cbl] and confirming the Agent Action Plan 0.4.2
    taxonomy applies with NO residue:

    ===================================  =====  =====================================
    Target                               Sites  Class
    ===================================  =====  =====================================
    ``aa999-main-exit``                     20  3 - paragraph exit
    ``aa100-Bad-Function``                   2  4 - sibling re-dispatch
    ``AA-Main-Exit``                         2  3 - section exit
    ``ba-rdbms-exit``                        1  3 - section exit
    the eight verb paragraphs                8  4 - sibling re-dispatch
    ===================================  =====  =====================================

    CLASS 1 (loop-back) AND CLASS 2 (forward terminator) DO NOT OCCUR - not in this
    program and not in [common/nominalMT.cbl] either. Neither file contains a single
    ``loop``, ``read-loop``, ``main-loop``, ``end-run``, ``end-report``, ``main-end``,
    ``end-loop`` or ``loop2`` label, because a file handler services exactly one verb
    per call and never iterates: the ITERATION lives in the calling program, which
    performs the read-next verb repeatedly. That is why nothing in this module needs a
    ``while True:``, and it is stated here explicitly so a reviewer knows the two
    classes were CHECKED FOR and found absent rather than overlooked.

    Args:
        system: ``System-Record`` [common/acas005.cbl:L268].
        ledger: ``WS-Ledger-Record`` [common/acas005.cbl:L270].
        file_access: ``File-Access`` [common/acas005.cbl:L272].
        file_defs: ``File-Defs`` [common/acas005.cbl:L273].
        dal_common: ``ACAS-DAL-Common-data`` [common/acas005.cbl:L274].
    """
    # ANOMALY N-SECTION-CASE - REPRODUCTION SITE. This function IS the section
    # header, and the header spells `Section` with a CAPITAL S
    # [common/acas005.cbl:L277] while its sibling spells it lower-case `section`
    # [common/acas005.cbl:L586]. Recorded here rather than normalised (rule R-4).
    # Falls into `aa010-main.` [common/acas005.cbl:L279].
    aa010_main(system, ledger, file_access, file_defs, dal_common)


def aa010_main(
    system: SystemRecord,
    ledger: WsLedgerRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa010-main.`` [common/acas005.cbl:L279-L363].

    The handler's body, in the frozen source's statement order. Every step below is
    the COBOL's, in the COBOL's sequence, and the sequence matters because two of the
    steps are SKIPPED on the RDB path by an early jump.

    ::

        move  2  to WS-Log-System.        *> 2=GL                      [:L283]
        move  11 to WS-Log-File-No.       *> Cobol/RDB File/Table       [:L284]
        evaluate File-Function            *> the key guard             [:L288-L302]
        ...
    *>  if fn-Open and fn-output and not FS-Cobol-Files-Used            [:L309-L314]
        if    not FS-Cobol-Files-Used                                  [:L316]
              move RDBMS-Flat-Statuses to FA-RDBMS-Flat-Statuses       [:L317]
              perform ba-Process-RDBMS                                [:L318]
              go to AA-Main-Exit                                      [:L319]
        end-if.
        perform  ba012-Test-WS-Rec-Size-2.                             [:L327]
        move     spaces to SQL-Err SQL-Msg SQL-State.                  [:L339]
        evaluate File-Function            *> the verb dispatch          [:L340-L361]
        go       to aa100-Bad-Function.   *> unconditional fall-through [:L363]

    THREE ORDERING FACTS THAT ARE EASY TO GET WRONG, all reproduced:

    * ``move spaces to SQL-Err SQL-Msg SQL-State`` [:L339] IS ON THE COBOL-FILES PATH
      ONLY. It sits AFTER the RDB early exit [:L319], so on the RDB path it never
      runs and the SQL diagnostics from the PREVIOUS call survive into this one. The
      bridge clears them itself per verb instead [common/nominalMT.cbl:L797-L798],
      which is why nothing visibly breaks.
    * ``perform ba012-Test-WS-Rec-Size-2`` [:L327] is likewise Cobol-path-only, and
      it is called with the SAME paragraph that the RDB path calls
      [common/acas005.cbl:L602] - one paragraph, two callers, and its ``if A = zero``
      first-call guard means whichever path runs FIRST does the credential load for
      the whole run. That is :func:`ba012_test_ws_rec_size_2`'s ANOMALY A-1.
    * the key guard [:L288-L302] runs BEFORE either, so a bad key number is rejected
      identically on both stores.

    AND THE FALL-THROUGH. ``aa100-Bad-Function`` is reached TWICE over - once as the
    ``when other`` arm [:L357-L358] and once by the unconditional ``go to`` on
    [:L363], under the maintainer's comment "Should never get here but in case :(".
    The second is unreachable, because an ``evaluate`` with a ``when other`` always
    takes an arm and every arm jumps away. Reproduced as written - the ``when other``
    branch below returns, and the statement after the dispatch is still there.

    Args:
        system: ``System-Record`` [:L268] - the connection parameters.
        ledger: ``WS-Ledger-Record`` [:L270] - the record being read or written.
        file_access: ``File-Access`` [:L272] - the verb in, the status out.
        file_defs: ``File-Defs`` [:L273] - the file-name block.
        dal_common: ``ACAS-DAL-Common-data`` [:L274] - the testing switches.
    """
    logging_data = file_access.logging_data
    # `move 2 to WS-Log-System.` [common/acas005.cbl:L283] - 2 is GL, per the
    # maintainer's own key on that line, "1 = IRS, 2=GL, 3=SL, 4=PL, 5=Stock".
    logging_data.ws_log_system = WS_LOG_SYSTEM
    # ANOMALY N-LOG, first half. `move 11 to WS-Log-File-No.`
    # [common/acas005.cbl:L284]. The RDB path overwrites this with 21 the moment it
    # is entered [common/acas005.cbl:L600], so 11 survives only on the Cobol path.
    # Both values are written, at their own sites, and neither is reconciled.
    logging_data.ws_log_file_no = WS_LOG_FILE_NO_COBOL

    # THE KEY GUARD [common/acas005.cbl:L288-L302]. Covers read-indexed (4), start
    # (9) and delete (8) - NOT write (5) and NOT re-write (7). `acas000` guards a
    # DIFFERENT set, 4, 5 and 7 [common/acas000.cbl:L333-L341], and ANOMALY N-GUARD
    # records that the two are deliberately not harmonised. The test is `not = 1`,
    # exact equality against a single valid key, never a range.
    # Looked up on the RAW value, deliberately. `File-Function` is `pic 99`
    # [copybooks/wsfnctn.cob:L88], so it can carry any of 0..99, and this guard is an
    # `evaluate` with NO `when other` [common/acas005.cbl:L288-L302] - a value outside
    # 4, 9 and 8 falls straight through it and goes on to the main dispatch, which
    # sends anything unrecognised to `aa100-Bad-Function` and `(99, 999)`
    # [common/acas005.cbl:L357-L358, :L567-L572], exactly as this module's docstring
    # describes. `FileFunction` is an `IntEnum`, so a raw `int` key still matches the
    # three members this mapping holds and an out-of-vocabulary one simply misses,
    # which is the fall-through. Coercing first would instead reject the value BEFORE
    # the guard could decline it, and the COBOL has no such rejection.
    guard = KEY_GUARDED_FUNCTIONS.get(file_access.file_function)
    if guard is not None and logging_data.file_key_no != FILE_KEY_NO:
        fs_reply, we_error, locator = guard
        # The COBOL writes We-Error FIRST then fs-reply, at all three sites -
        # `move 998 to WE-Error` / `move 99 to fs-reply` [:L292-L293] and
        # `move 996 to WE-Error` / `move 99 to fs-reply` [:L298-L299]. Delete gets
        # 996; read-indexed and start get 998. ANOMALY N-996-COMMENT records that
        # [:L298]'s comment is a copy of [:L292]'s and describes the wrong code.
        file_access.we_error = we_error
        file_access.fs_reply = fs_reply
        log_handler_failure(
            _LOG,
            program=HANDLER_NAME,
            paragraph="aa000-Main-Process key guard",
            locator=locator,
            fs_reply=int(fs_reply),
            we_error=int(we_error),
            detail="File-Key-No %d is not %d for %s"
            % (
                logging_data.file_key_no,
                FILE_KEY_NO,
                FileFunction(file_access.file_function).name,
            ),
        )
        # GO TO CLASS 3 - `go to aa999-main-exit` [:L294, :L300].
        aa999_main_exit(file_access, dal_common)
        return

    # ANOMALY N-DEADCODE. The open-output-becomes-delete-all coercion sits here in
    # `acas008` and is LIVE there [common/acas008.cbl:L313-L319]; here the whole
    # block is COMMENTED OUT [common/acas005.cbl:L309-L314] with the maintainer's own
    # reason on [common/acas005.cbl:L307]: "NOT used with GL." Nothing is implemented,
    # and `ba015_test_ends` - the paragraph it would have called - is likewise dead.
    # The asymmetry is deliberate and is recorded rather than smoothed away.

    if not _is_cobol_files_used(system):
        # `move RDBMS-Flat-Statuses to FA-RDBMS-Flat-Statuses.` [:L317], under the
        # maintainer's note "needed for DAL? not JC/dbpre versions" - so he was not
        # certain it was needed either. Copied regardless, as written.
        #
        # This is a GROUP-TO-GROUP move, so BOTH subordinate fields travel: the store
        # selector AND `File-Duplicates-In-Use`, which the copybook marks "No longer
        # in use" [copybooks/wssystem.cob:L123] on one side and "NO LONGER USED other
        # than for a '6' = rdb" [copybooks/wsfnctn.cob:L80] on the other. Two
        # different obsolescence notes for the same byte; it is copied anyway because
        # the group move copies it, and nothing downstream reads it.
        source = system.system_data_block.rdbms_flat_statuses
        target = file_access.fa_rdbms_flat_statuses
        target.fa_file_system_used = source.file_system_used
        target.fa_file_duplicates_in_use = source.file_duplicates_in_use
        # `perform ba-Process-RDBMS.` [:L318], with the comment "Can't hurt".
        ba_process_rdbms(file_access, system, dal_common, ledger)
        # GO TO CLASS 3 - `go to AA-Main-Exit` [:L319]. This is what skips [:L327]
        # and [:L339] on the RDB path.
        aa_main_exit()
        return

    # `perform ba012-Test-WS-Rec-Size-2.` [:L327]. Cobol path only. Shared with the
    # RDB path's own caller [:L602]; its `if A = zero` guard makes it first-call-only,
    # which is ANOMALY A-1 - whichever path runs FIRST does the load for the run.
    if not ba012_test_ws_rec_size_2(file_access, system, dal_common):
        # The record-length guard inside `ba012` ends `go to ba-rdbms-exit` [:L621]
        # having written (99, 901); on this path that lands back here. GO TO CLASS 3.
        aa999_main_exit(file_access, dal_common)
        return

    # `move spaces to SQL-Err SQL-Msg SQL-State.` [:L339]. COBOL PATH ONLY - see the
    # docstring. `SQL-Err pic 9(9)` takes spaces into a numeric field here, exactly as
    # the frozen source does; the field is display-only and never arithmetic.
    logging_data.sql_err = ""
    logging_data.sql_msg = ""
    logging_data.sql_state = ""

    # THE VERB DISPATCH [:L340-L361], arms taken in :data:`DISPATCH_ORDER`.
    function = file_access.file_function
    for arm in DISPATCH_ORDER:
        if function != arm:
            continue
        if arm == FileFunction.OPEN:
            aa020_process_open(file_access, dal_common)  # `go to aa020` [:L342]
        elif arm == FileFunction.CLOSE:
            aa030_process_close(file_access)  # `go to aa030` [:L344]
            # `aa030` ends `go to aa-main-exit` [:L413], not aa999. GO TO CLASS 3.
            aa_main_exit()
        elif arm == FileFunction.READ_NEXT:
            aa040_process_read_next(file_access)  # `go to aa040` [:L346]
        elif arm == FileFunction.READ_INDEXED:
            aa050_process_read_indexed(file_access, ledger)  # `go to aa050` [:L348]
        elif arm == FileFunction.WRITE:
            aa070_process_write(file_access, ledger)  # `go to aa070` [:L350]
        elif arm == FileFunction.RE_WRITE:
            aa090_process_rewrite(file_access, ledger)  # `go to aa090` [:L352]
        elif arm == FileFunction.DELETE:
            aa080_process_delete(file_access, ledger)  # `go to aa080` [:L354]
        else:
            aa060_process_start(file_access, ledger, dal_common)  # `go to aa060` [:L356]
        return

    # `when other go to aa100-Bad-Function.` [:L357-L358].
    aa100_bad_function(file_access, dal_common)
    # `go to aa100-Bad-Function.` [:L363] - the unconditional fall-through under
    # "Should never get here but in case :(" [:L362]. Unreachable in the COBOL for the
    # reason given in the docstring, and unreachable here for the same reason: every
    # arm above returns and the `when other` has just run. Kept as written, and kept
    # unreachable, so the two files still line up statement for statement.
    return


#: ``88  FS-Cobol-Files-Used    value zero.`` [copybooks/wssystem.cob:L113].
#:
#: ZERO, NOT ONE - and the RDBMS is the ``1`` [copybooks/wssystem.cob:L116]. The
#: sense is the opposite way round from the way the names read, so the value is taken
#: from the frozen condition name rather than from the identifier.
_FS_COBOL_FILES_USED: Final[int] = 0


def _is_cobol_files_used(system: SystemRecord) -> bool:
    """``FS-Cobol-Files-Used`` - the store selector [copybooks/wssystem.cob:L111-L118].

    Verbatim::

        05  RDBMS-Flat-Statuses.                                       [:L111]
            07  File-System-Used  pic 9.                               [:L112]
                88  FS-Cobol-Files-Used    value zero.                 [:L113]
                88  FS-MySql-Used          value 1.                    [:L114]
                88  FS-RDBMS-Used          value 1.  *> Was generic     [:L116]

    THREE THINGS THIS PREDICATE EXISTS TO GET RIGHT, each of which is a live trap:

    * IT LIVES IN ``System-Record``, NOT in ``File-Access``. ``File-Access`` has a
      SEPARATE copy, ``FA-RDBMS-Flat-Statuses`` [copybooks/wsfnctn.cob:L72-L82],
      annotated "Comes from System-Record via acas0nn" - and it is THIS handler that
      does the copying, at [common/acas005.cbl:L317]. So at the moment the test on
      [:L316] runs, the ``File-Access`` copy has not been written yet and reading it
      instead would test a stale or zero value.
    * ``FS-Cobol-Files-Used`` IS ZERO. Indexed files are the ``0`` and the RDBMS is
      the ``1``, which is the reverse of what the names suggest and the reverse of
      what a reader assumes from "Cobol files are the original store".
    * ``FS-MySql-Used`` and ``FS-RDBMS-Used`` ARE BOTH ``1`` [:L114, :L116] - two
      condition names over one value, the second annotated "Was generic". They are
      indistinguishable at run time, so no code can tell which store it has beyond
      "not indexed files". Four further options are commented out [:L117-L121].

    The test at [common/acas005.cbl:L316] is NEGATED - ``if not FS-Cobol-Files-Used``
    - so it is true exactly when the RDBMS is in use, which is the path this module
    implements. Expressed as a named predicate because Agent Action Plan 0.1.1 makes
    ``88``-level condition names predicate functions, and because a negated test over
    an inverted value is precisely the shape that gets mis-read when inlined.

    Args:
        system: ``System-Record`` - the handler's FIRST linkage parameter
            [common/acas005.cbl:L268].

    Returns:
        ``True`` when the run is using GnuCOBOL indexed files, ``False`` when it is
        using the RDBMS.
    """
    # `03  System-Data-Block.` [copybooks/wssystem.cob:L52] encloses the `05` group
    # [:L111], so the group name is part of the path - `System-Record` is 169 columns
    # across seven such blocks and the record module keeps every one of them.
    return (
        system.system_data_block.rdbms_flat_statuses.file_system_used
        == _FS_COBOL_FILES_USED
    )


def dispatch(
    system: SystemRecord,
    ledger: WsLedgerRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``call "acas005" using ...`` - THE HANDLER ENTRY POINT.

    The five-parameter linkage, verbatim [common/acas005.cbl:L268-L274]::

        Procedure Division Using System-Record
                                 WS-Ledger-Record
                                 File-Access
                                 File-Defs
                                 ACAS-DAL-Common-data.

    so the Agent Action Plan 0.4.3 call contract is::

        FROM:  call "acas005" using System-Record WS-Ledger-Record File-Access
                                    File-Defs ACAS-DAL-Common-data
        TO:    acas005_gl_nominal.dispatch(system, ledger, file_access, file_defs,
                                           dal_common)

    THIS IS THE CANONICAL FIVE-PARAMETER HANDLER SHAPE. Sixteen sibling handlers
    share it; ``acas005`` is simply the one that carries no per-table peculiarity in
    its linkage, which is why it is the reference.

    THE CALLER. ``copybooks/Proc-ACAS-FH-Calls.cob:L35-L41` issues the ``CALL``, and
    its dispatch paragraph sets ``move 1 to File-Key-No`` [:L51-L57] immediately
    before it - so on the entity-named facade path the key number is ALWAYS 1 and the
    key guard below can never fire. It fires only for a caller that sets the field
    itself, which the IRS-named convention's callers do.

    WHAT THIS FUNCTION DOES NOT DO. It does not open a connection, validate a record,
    or decide anything: it forwards to :func:`aa010_main`, whose steps are the COBOL's.
    The parameters it appears not to use are used - ``system`` by
    :func:`ba012_test_ws_rec_size_2` for the credential load and by
    :func:`ba020_process_open`, ``file_defs`` by nothing at all, which is itself the
    frozen program's behaviour and is recorded as such below.

    ``FILE-DEFS`` IS RECEIVED AND NEVER READ. Searching the whole of
    [common/acas005.cbl] for a reference to any field of ``File-Defs`` finds none: the
    handler takes the block because every handler takes the block, and on the RDB path
    the file name is irrelevant because there is no file. It is accepted here for the
    same reason - the linkage is the contract, and a reviewer diffing the argument
    lists must find five. Recorded as a deliberate no-op rather than dropped, per rule
    R-5's "deliberate omissions are recorded as omissions".

    Args:
        system: ``System-Record`` - supplies ``RDB-Data``'s credentials by way of
            :func:`connection.load_rdb_data_once`.
        ledger: ``WS-Ledger-Record`` - the record read into or written from. Mutated
            in place on every read, exactly as the COBOL's linkage is.
        file_access: ``File-Access`` - carries ``File-Function`` and ``Access-Type``
            in, and ``FS-Reply``, ``We-Error`` and the whole of ``Logging-Data`` out.
            Mutated in place.
        file_defs: ``File-Defs`` - accepted to honour the linkage and never read.
        dal_common: ``ACAS-DAL-Common-data`` - ``SW-Testing`` and ``SW-Testing-2``,
            the two logging switches.

    Raises:
        CobolFileAccessNotMigratedError: When ``RDB-Data`` selects GnuCOBOL indexed
            files rather than the RDBMS and the verb needs a real ISAM engine. Rule
            R-1 forbids this package from carrying one; see
            :data:`FLAT_FILE_STATUSES` for what each such branch would have done.
        AcasFileHandlerError: Propagated from the bridge for a database failure the
            frozen source reports through ``FS-Reply``/``We-Error``.

    Example:
        Reading the nominal account the General Ledger posting cycle needs, through
        the verb vocabulary the facade publishes::

            file_access.file_function = FileFunction.READ_INDEXED
            file_access.access_type = AccessType.EQUAL_TO
            file_access.logging_data.file_key_no = 1
            ledger.ws_ledger_key9.ws_ledger_key9 = 12345678
            dispatch(system, ledger, file_access, file_defs, dal_common)
            if file_access.fs_reply == FsReply.SUCCESS:
                balance = ledger.ledger_balance      # a Decimal, never a float
    """
    # Entry is at the FIRST section of the procedure division,
    # `aa-Process-Flat-File Section.` [common/acas005.cbl:L277], which falls into
    # `aa010-main.` [common/acas005.cbl:L279].
    aa_process_flat_file(system, ledger, file_access, file_defs, dal_common)
    # `aa-Exit.  exit program.` [common/acas005.cbl:L583-L584] - the return to the
    # caller of `acas005`. See :func:`aa_exit`.
    aa_exit()
