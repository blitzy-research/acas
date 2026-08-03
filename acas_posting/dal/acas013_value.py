"""ACAS file handler ``acas013`` and its bridge ``valueMT`` - the Value entity.

WHAT THIS MODULE OWNS
=====================
One handler-and-bridge pair, reimplemented as SQL against the frozen schema:

======================= ==================================================
Entity facade           ``Value``  [copybooks/Proc-ACAS-FH-Calls.cob:L711]
Handler                 ``acas013``            [common/acas013.cbl:L12]
Bridge                  ``valueMT``            [common/valueMT.cbl:L664]
Table                   ``VALUEANAL-REC``  [mysql/ACASDB.sql:L1418-L1431]
Record copybook         ``copybooks/wsval.cob``
Record class            :class:`acas_posting.records.value_analysis.WsValueRecord`
======================= ==================================================

Ten columns, all ``NOT NULL``, single-column primary key ``VA-CODE``
[mysql/ACASDB.sql:L1429], no secondary index. Value analysis is a
sales-and-purchase analysis-code table: a three-character code, the nominal
account it posts to, a description, a print flag, three period transaction
COUNTS and three period transaction VALUES.

Per Agent Action Plan section 0.3.1 the boundary is the HANDLER, not the table -
"One data-access module per handler, not per table ... preserves the dispatch
semantics rather than flattening them." Here handler and table happen to be
one-to-one, but the two dispatch layers are still both reproduced, because they
disagree with each other in three places (see DISAGREEMENTS below).

THE TWO CALL SIGNATURES, BOTH PUBLISHED
=======================================
Rule R-5 requires a Python function per COBOL paragraph and a callable whose
argument list a reviewer can diff against the COBOL. There are two, because
COBOL has two layers here, and both are published.

The handler's linkage is FIVE parameters [common/acas013.cbl:L283-L289]::

    Procedure Division Using System-Record
                             WS-Value-Record
                             File-Access
                             File-Defs
                             ACAS-DAL-Common-data.

reached from the facade's dispatch paragraph, which sets the key number first
[copybooks/Proc-ACAS-FH-Calls.cob:L90-L96]::

    acas013.       *>  Value
        move 1 to File-Key-No.
        call "acas013" using System-Record
                             WS-Value-Record
                             File-Access
                             File-Defs
                             ACAS-DAL-Common-Data.

giving, per Agent Action Plan section 0.4.3::

    TO:    acas013_value.dispatch(system, value, file_access, file_defs, dal_common)

The bridge's linkage is THREE parameters, in a DIFFERENT order - the record
comes last, not second [common/valueMT.cbl:L339-L341], and the handler calls it
that way [common/valueMT.cbl:L664-L668]::

    ba020-Call.
        call     "valueMT" using File-Access
                                 ACAS-DAL-Common-data

                                 WS-Value-Record
        end-call.

giving :func:`value_mt`, which owns every statement issued against
``VALUEANAL-REC``. Both functions take their COBOL parameters POSITIONALLY, in
the COBOL's own order. Each also accepts keyword-only extras - the open
connection, the cursor table, the transport policy - which model the bridge's
own WORKING-STORAGE. A COBOL sub-program retains working storage between
``CALL``s and it never appears in a linkage list, so representing it as
keyword-only arguments keeps the positional contract exactly the COBOL's while
letting a caller supply state the COBOL held implicitly.

THE HANDLER'S VERB SET AND DISPATCH ORDER
=========================================
``evaluate File-Function`` [common/acas013.cbl:L343-L362]. The dispatch order is
NOT the paragraph order - write, rewrite and delete are dispatched out of
sequence - and that order is preserved here:

===== ===================== ====================================
Code  Paragraph             Note
===== ===================== ====================================
1     aa020-Process-Open    Access-Type selects input/i-o/output/extend
2     aa030-Process-Close
3     aa040-Process-Read-Next
4     aa050-Process-Read-Indexed
5     aa070-Process-Write   dispatched fifth, declared seventh
7     aa090-Process-Rewrite dispatched sixth, declared last
8     aa080-Process-Delete  dispatched seventh, declared before rewrite
9     aa060-Process-Start
other aa100-Bad-Function    `*> 6 is spare / unused` [:L361]
===== ===================== ====================================

There is NO function 31 here. ``acas012`` dispatches 31 (read by name); this
handler stops at 9 and sends everything else to ``aa100-Bad-Function``, which is
reached BOTH by ``when other`` [:L361-L362] AND by an unconditional fall-through
one line past the end of the evaluate [:L365] - "Should never get here but in
case :(". Both routes are reproduced.

Function 6 is ``fn-Delete-All``, which the handler's own comment calls spare -
yet the BRIDGE dispatches it to ``ba085-Process-Delete-All``
[common/valueMT.cbl:L385-L386], and the handler itself SETS it, from
``ba015-Test-Ends`` [common/acas013.cbl:L659]. So a function the handler will not
accept from a caller is one the handler generates internally.

THE FACADE PUBLISHES ELEVEN VERBS, NOT TWELVE
=============================================
[copybooks/Proc-ACAS-FH-Calls.cob:L711-L768]: Value-Open, Value-Open-Input,
Value-Open-Output, Value-Close, Value-Delete, Value-Delete-All, Value-Start,
Value-Read-Next, Value-Read-Indexed, Value-Write, Value-Rewrite.

There is no ``Value-Open-Extend``. ``Access-Type 4`` (``fn-extend``) is therefore
unreachable through the facade, yet the handler still implements it, with the
``open extend`` itself commented out and a ``We-Error 997`` in its place
[common/acas013.cbl:L390-L394]. Reproduced as written; recorded as N-noextendverb.

``Value-Start`` [:L743-L747] sets the key number and the function but does NOT
zero ``Access-Type``, unlike its ten siblings - so for a START the access type
IS the relation, 5 to 9. It is passed through unmodified.

THE FIELD DRIFT, TAKEN FROM THE DATA DICTIONARY
===============================================
Agent Action Plan section 0.8.1 makes this a directive rather than a preference:
"Data dictionary first ... every Python field definition cites its entry. This
ordering is a directive, not a preference - it is what prevents fields being
transcribed by eye." Every conversion below comes from
``loader.drift_for(<key>)``; nothing is read off a picture clause.

= =========== ================== ================== ======================= ==================
# Column      Copybook           Bridge host var    MySQL column            Drift
= =========== ================== ================== ======================= ==================
1 VA-CODE     group of 3 x       X(3)        [:L287] char(3) PK    [:L1419] GROUP FLATTENED
2 VA-GL       9(6)   DISPLAY     9(08) COMP  [:L288] mediumint(6) u [:L1420] usage + digits
3 VA-DESC     x(24)              X(24)       [:L289] char(24)       [:L1421] clean
4 VA-PRINT    xxx                X(3)        [:L290] char(3)        [:L1422] clean
5 VA-T-THIS   9(5)   COMP        9(08) COMP  [:L291] mediumint(5) u [:L1423] digits only
6 VA-T-LAST   9(5)   COMP        9(08) COMP  [:L292] mediumint(5) u [:L1424] digits only
7 VA-T-YEAR   9(5)   COMP        9(08) COMP  [:L293] mediumint(5) u [:L1425] digits only
8 VA-V-THIS   s9(8)v99 COMP-3    9(08)V9(02) [:L294] decimal(10,2) u[:L1426] SIGN LOST
9 VA-V-LAST   s9(8)v99 COMP-3    9(08)V9(02) [:L295] decimal(10,2) u[:L1427] SIGN LOST
10 VA-V-YEAR  s9(8)v99 COMP-3    9(08)V9(02) [:L296] decimal(10,2) u[:L1428] SIGN LOST
= =========== ================== ================== ======================= ==================

Copybook locators are ``copybooks/wsval.cob`` L10-L23; bridge locators are
``common/valueMT.cbl``; column locators are ``mysql/ACASDB.sql``. Full citations
are emitted by :func:`column_citations` and come from ``loader.cite``.

A CORRECTION TO THE AGENT ACTION PLAN, SECTION 0.6.2
====================================================
Section 0.6.2 makes a general claim, verbatim:

    "By contrast the monetary fields are declared signed at all three layers and
    pass through cleanly, so the drift is specific rather than systemic and must
    be handled field by field from the dictionary."

THAT CLAIM IS TRUE FOR ``salesMT`` AND ``nominalMT`` AND FALSE HERE. Verified in
this checkout, side by side:

* ``salesMT``    money host variables are ``PIC S9(08)V9(02) COMP`` - SIGNED
  [common/salesMT.cbl:L313-L319] - against signed ``decimal(10,2)`` columns
  [mysql/ACASDB.sql:L974-L980].
* ``nominalMT``  money host variables are ``PIC S9(08)V9(02) COMP`` - SIGNED
  [common/nominalMT.cbl:L300-L305] - against signed ``decimal(10,2)`` columns
  [mysql/ACASDB.sql:L128-L130].
* ``valueMT``    money host variables are ``PIC 9(08)V9(02) COMP`` - NO ``S``
  [common/valueMT.cbl:L294-L296] - against ``decimal(10,2) unsigned`` columns
  [mysql/ACASDB.sql:L1426-L1428], while the copybook declares all three
  ``pic s9(8)v99 comp-3`` - SIGNED [copybooks/wsval.cob:L21-L23].

So three MONETARY fields lose their sign at this bridge, before any SQL runs. A
negative value-analysis total is a credit; here it silently stops being one. The
loss is reproduced, never repaired - see :func:`_hv_unsigned_money`.

This is the strongest available proof of the same section's own rule that the
drift "must be handled field by field from the dictionary": the generated
dictionary, built from the bridge rather than from the copybook, already carries
the correction independently. ``loader.drift_for("VALUEANAL-REC.VA-V-THIS")``
reports ``signedness=True``, the entry carries ``anomaly_refs ('A-11',)`` and
``ambiguity_refs ('Q-3',)``, and its note says the stored value "can only be
measured by running the compiled program". Reading the picture clause by eye
would have concluded the opposite.

TWO INDEPENDENT SIGN-LOSS MECHANISMS, NOT ONE
=============================================
1. THE MOVE. ``bb000-HV-Load`` moves a signed ``COMP-3`` item into an unsigned
   ``COMP`` host variable [common/valueMT.cbl:L1067-L1069]. A receiving item
   with no sign cannot carry one, so the magnitude is stored.
2. THE EDIT PICTURE. ``WS-MYSQL-EDIT`` is ``PIC -Z(18)9.9(9)``
   [common/valueMT.cbl:L225] - thirty characters, the SIGN at character 1,
   nineteen integer digit positions at 2 to 20, the point at 21, nine decimal
   positions at 22 to 30. An 8-integer/2-decimal host variable therefore lands
   its integer digits at 13 to 20 and its decimals at 22 to 23, which is exactly
   what the bridge slices: ``WS-MYSQL-EDIT(13:08)`` and ``WS-MYSQL-EDIT(22:02)``
   [common/valueMT.cbl:L1196-L1203]. CHARACTER 1 IS NEVER REFERENCED ANYWHERE IN
   THE FILE, so the emitted SQL text structurally cannot carry a minus sign even
   if the host variable had one.

Either mechanism alone would lose the sign. Both are reproduced, because the
question of what is finally stored is open (below) and the two mechanisms could
in principle answer it differently.

AN OPEN QUESTION, LEFT OPEN
===========================
Agent Action Plan section 0.6.8 lists among the five questions only compiled
execution can settle: "A negative binary value through an unsigned host variable
into an unsigned column ... what the resulting stored value IS depends on the
conversion the bridge's C interface performs, which must be measured rather than
assumed." Section 0.6.2 scopes that question to statistics fields; the finding
above extends it to these three money fields, and the dictionary agrees, tagging
them ``Q-3``.

:func:`_hv_unsigned_money` therefore implements the reading this module can
defend from the frozen source - GnuCOBOL applies a sign to a receiving item only
when that item has one, so the magnitude survives and the sign is dropped - and
says so at the site. It does NOT raise, clamp to zero, reject the row or take a
mathematical absolute value as an arithmetic step. The exact stored value is
recorded as pending oracle arbitration in
``docs/migration/ambiguity-resolutions.md`` under Q-3. If the oracle later shows
the C interface produces something else, exactly one function changes.

FOUR COPYBOOK FIELDS HAVE NOWHERE TO GO
=======================================
The bridge does NOT ``copy "wsval.cob"``. It re-declares the record inline in
its own Linkage Section, named after the TABLE rather than after the record, and
flattens the key [common/valueMT.cbl:L309-L319]::

    01  VALUEANAL-REC.
        03  WS-Va-Code         pic xxx.
        03  Va-Gl              pic 9(6).
        ...

against the copybook's three-level group [copybooks/wsval.cob:L10-L14]::

    01  WS-Value-Record.
        03  va-code.
            05  va-system      pic x.
            05  va-group.
                07 va-first    pic x.
                07 va-second   pic x.

So ``va-system``, ``va-group``, ``va-first`` and ``va-second`` have NO host
variable and NO column. They survive only inside ``VA-CODE``'s three characters,
and they are recorded as deliberate omissions in
:data:`OMITTED_COPYBOOK_FIELDS` rather than given columns of their own. The
copybook has no ``filler``, so nothing else is dropped.

``valueMT`` is one of five bridges that declare their record inline rather than
by ``COPY`` - the others being ``analMT``, ``purchMT``, ``irsnominalMT`` and,
partially, ``slinvoiceMT`` / ``plinvoiceMT`` - so this is a known family rather
than a one-off. It is, after ``irspostingMT``'s three columns that exist in no
copybook, the clearest proof in the checkout that the bridge and the copybook are
different documents.

THREE PLACES THE TWO LAYERS DISAGREE
====================================
Both dispatch layers are reproduced because they do not agree, and a caller sees
whichever layer answered:

============================ ===================== =====================
Condition                    Handler               Bridge
============================ ===================== =====================
START access type out of     ``998``, and FS-Reply  ``997`` WITH FS-Reply
range (< 5 or > 8)           IS NEVER WRITTEN       ``99``
                             [acas013:L501-L504]    [valueMT:L699-L703]
Bad function                 ``999``, FS-Reply 99   ``990``, FS-Reply 99
                             [acas013:L571-L573]    [valueMT:L1019-L1021]
Read-indexed, no row         ``21`` (ISAM invalid   ``23`` with We-Error
                             key) [acas013:L478]    ZEROED [valueMT:L641]
============================ ===================== =====================

The first is doubly wrong against the handler's own error table, which documents
``997`` for "Access-Type wrong (< 5 or > 8)" and marks ``998`` with the asterisk
meaning "FS-Reply = 99" [common/acas013.cbl:L168-L191]. Reproduced as coded, not
as documented.

The read-indexed row is why this module issues its own SQL for the positioning
verbs instead of delegating to
:mod:`acas_posting.dal.cursor_state`'s ``read_indexed``: that function reproduces
``glpostingMT``, which answers ``21`` and leaves ``We-Error`` alone. This bridge
answers ``23`` and zeroes ``We-Error``. The shared module supplies the
primitives - the cursor state, the relation mapping, the declared key metadata -
and this module supplies the statements and the status writes, which is also what
the assignment requires: ``value_mt`` owns ALL SQL for ``VALUEANAL-REC``.

THE FLAT-FILE BRANCH, AND WHY MOST OF IT IS UNREACHABLE
=======================================================
``acas013`` serves two data paths. The choice is made once, at
[common/acas013.cbl:L321-L325]::

    if       not FS-Cobol-Files-Used
             move RDBMS-Flat-Statuses to FA-RDBMS-Flat-Statuses
             perform  ba-Process-RDBMS
             go to AA-Main-Exit

so when the system record selects a relational store the handler goes straight
to the bridge and RETURNS - the ``aa0NN`` ISAM paragraphs never execute. Only
when ``FS-Cobol-Files-Used`` (``File-System-Used`` zero
[copybooks/wssystem.cob:L111-L116]) does it fall through to the indexed-file
verbs.

This migration targets the relational path: Agent Action Plan section 0.2.1.1
maps the Value entity to ``VALUEANAL-REC`` through ``valueMT``, and section
0.7.2 R-1 requires the handler-and-bridge pair be reimplemented "as SQL against
the frozen schema". There is no indexed-file layer in the target and none is
being built.

The ``aa0NN`` paragraphs are nonetheless present as functions, because R-5 wants
one per paragraph, and each is complete for every statement that is not itself
an indexed-file verb - the guards, the status writes, the ``WS-File-Key``
strings, the record moves, the whole ``fn-extend`` branch (whose ``open extend``
is commented out in the source, so it reproduces exactly). At the one point where
COBOL issues the verb itself, the function raises
:class:`IndexedFilePathNotMigrated`, having first performed every statement
COBOL would have performed before that verb, so the status a caller inspects is
the status COBOL would have left. That boundary is a recorded omission, not a
stub: nothing about it is deferred, and on the migrated path it cannot be
reached.

WHAT IS DELIBERATELY NOT REPRODUCED
===================================
Per Agent Action Plan section 0.3.4, presentation with no database effect is
dropped and only the control transfer survives:

* ``display Display-Blk at 2301`` / ``display AC901 at 2401`` and the
  ``accept Accept-Reply at 2433`` pause in ``ba012-Test-WS-Rec-Size-2``
  [common/acas013.cbl:L619-L631]. The pause is dropped; the transfer to
  ``ba-rdbms-exit`` is preserved, and the two lengths are logged instead.
* ``display Display-Message-1 with erase eos`` under ``Testing-2``
  [common/valueMT.cbl:L619-L621] and its siblings - log records here.
* the ``COB_SCREEN_*`` environment set-up [common/valueMT.cbl:L344-L352].
* ``call "fhlogger"`` [common/acas013.cbl:L679-L680] is a log write, so
  :func:`ca_process_logs` emits a log record carrying the same fields rather
  than invoking the COBOL logger - R-1 forbids reaching a COBOL program.

THE STATEMENT TEXT, AND THE ONE REPRESENTATIONAL DIFFERENCE
===========================================================
The bridge interpolates its values into the statement text as quoted literals.
This module binds them instead, because
:func:`acas_posting.dal.connection.execute_statement` is the shared execution
path for every handler module and its contract is fixed: identifiers arrive
already quoted, values travel as ``%s`` placeholders.

Both forms are therefore built. The COBOL-shaped text - values rendered exactly
as the bridge renders them, ``WS-MYSQL-EDIT`` slices included, trailing-space
artefact included - is what is written to ``WS-Log-Where`` and returned for
inspection, so a reviewer can diff it against the frozen source. The bound form
is what executes. The VALUES are identical in both, because the rendering
happens first and the bound value is the rendered one; only the transport
differs, and no compared artefact - table state, ``WS-Log-Where``,
``WS-File-Key`` - can tell them apart. Interpolating instead would reproduce a
text-assembly detail at the price of an injection surface, which is not a trade
this layer makes.

Every identifier goes through
:func:`acas_posting.dal.connection.quote_identifier`. This is not stylistic:
every table and column name here contains a hyphen, so unquoted each one is a
syntax error.

Because the schema declares all ten columns ``NOT NULL`` and
``bb000-HV-Load`` begins with ``initialize TD-VALUEANAL-REC``
[common/valueMT.cbl:L1059], an unset field becomes zero or space and never SQL
``NULL``. Agent Action Plan section 0.6.2: "This is why every column in the
schema can be declared ``NOT NULL`` and why the Python layer must default rather
than omit." Every insert names all ten columns and nothing is ever bound as
``None``.

ANOMALY REGISTER
================
Reproduced, never repaired - rule R-4, "A defect reproduced is correct; a defect
fixed is a failure." Each entry names its site here and its locator in the frozen
source; :data:`ANOMALIES` carries the machine-readable form, and each belongs in
``docs/migration/anomaly-log.md`` naming this module as the reproducing module.

===================== =========================================================
N-money-signloss      three MONETARY fields lose their sign at the bridge;
                      corrects Agent Action Plan section 0.6.2
N-flatkey             a three-level key group flattened and renamed; four
                      sub-fields have no destination
N-inline-record       the bridge re-declares its record inline, named after
                      the table, rather than copying the copybook
N-logsystem6          a sixth logging subsystem code, meaning "PL & SL",
                      listed out of numeric order in its own comment
N-log                 the log file number is 13 on the indexed path and 23 on
                      the relational path
N-noreread            no reread paragraph of any name, alone among its
                      siblings
N-ba020call           the bridge-call paragraph is ``ba020-Call``, not
                      ``ba020-Process-DAL``
N-hvcase              host-variable names lower-cased in the load paragraph,
                      upper-cased in their declarations
N-initialize          two initialisation semantics in one bridge
N-recsize             the declared record size, and what the field sum makes it
N-guard               the delete key guard's comment is the seek guard's
N-998                 ``998`` carries three different meanings
N-996-comment         copy-pasted comment on the delete guard
N-kortype             a declared key type its own comment says is unused
N-noextendverb        a handled access type the facade cannot produce
N-startguard          the two layers disagree on the START guard's code AND on
                      whether FS-Reply is written
N-badfunc             the two layers disagree on the bad-function code
N-wscountrows         a copybook field annotated for this bridge's Delete-All
                      and never referenced by it
N-filekey-deadstore   a log key written and immediately overwritten with a
                      stale row count
N-deleteall-zzz       "delete all" does not delete all, and mutates the
                      caller's record to do it
N-readnext-lowkey     sequential read silently skips rows below its low key
N-start-nostatus      a fruitless START can leave the caller's previous status
                      untouched
N-reread-staleeof     the fetch tests the caller's incoming FS-Reply after
                      fetching, and can discard a row it retrieved
N-deadcode            two unreachable blocks
N-stopliteral         a debugging ``stop`` literal on the indexed path
N-closelogtwice       close writes two log records
N-writenokey          write never resolves its key, so it logs a stale one
N-casing              four casing inconsistencies
N-varsab              a changelog entry contradicted by the code it describes
N-pointer-offbyone    every statement carries one extra trailing space
N-updates-key         the rewrite assigns the primary key to itself
===================== =========================================================

RULES THIS MODULE IS HELD TO
============================
There is NO user rules document for this project - ``review_rules`` returns
exactly "No user rules provided." The binding rules are R-1 to R-6 of Agent
Action Plan section 0.7.2, and where they are silent this module is held to
enterprise-standard practice rather than to an invented rule.

R-1  no COBOL at runtime - nothing here starts a process, loads a shared
     object, or reaches the COBOL logger, and nothing imports the oracle
     harness. Every COBOL construct is reimplemented natively.
R-2  no binary floating point - the three money columns are ``Decimal`` end to
     end and the four integer columns are ``int``. No value is ever built from
     a binary approximation, and no rounding helper of that kind is used.
R-3  no new validation, field or schema change, and no concurrency - only
     ``SELECT``, ``INSERT``, ``UPDATE`` and ``DELETE``; no schema statement of
     any kind; no entity-mapping layer; strictly sequential, with no thread, no
     event loop, no sub-process and no connection re-use pool.
R-4  anomalies reproduced with an inline locator at each site.
R-5  one function per paragraph, both call signatures published, every field
     citing its dictionary entry, omissions recorded as omissions.
R-6  compiled behaviour arbitrates, and the module reads no clock and draws no
     unpredictable value, so two runs of the same input are identical.
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
    # The two published call signatures.
    "dispatch",
    "value_mt",
    # The handler's paragraphs, in declaration order [common/acas013.cbl].
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
    # The bridge's paragraphs, in declaration order [common/valueMT.cbl].
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
    # Module state, mirroring the bridge's WORKING-STORAGE lifetime.
    "cursor_states",
    "reset_module_state",
)

#: Diagnostics only. No handler is attached and no record is emitted at import,
#: so importing this module performs no input or output of any kind.
_LOG: Final[logging.Logger] = logging.getLogger(__name__)


class IndexedFilePathNotMigrated(RuntimeError):
    """Raised where the frozen handler would issue an indexed-file verb.

    ``acas013`` serves two data paths and picks one at
    [common/acas013.cbl:L321-L325]. This migration implements the relational
    path, because Agent Action Plan section 0.2.1.1 maps the Value entity to
    ``VALUEANAL-REC`` through ``valueMT`` and section 0.7.2 R-1 requires the
    handler-and-bridge pair be reimplemented as SQL against the frozen schema.
    No indexed-file layer exists in the target.

    On the migrated path this is unreachable: the frozen source itself returns
    at [:L325] before any ``aa0NN`` paragraph runs whenever the system record
    selects a relational store. It exists so that the boundary announces itself
    instead of fabricating a success, and so that the ``aa0NN`` functions - which
    R-5 requires to exist - can execute every statement COBOL would have executed
    up to the verb and leave the caller's status exactly as COBOL would have left
    it. It is a recorded scope boundary, not deferred work.
    """


# ---------------------------------------------------------------------------
# Identity and provenance
# ---------------------------------------------------------------------------

#: `Program-Id. acas013.` [common/acas013.cbl:L12]; the frozen version string
#: the program reports for itself is `"acas013 (3.3.00)"` [:L250].
HANDLER: Final[str] = "acas013"

#: `call "valueMT" using ...` [common/acas013.cbl:L664].
BRIDGE: Final[str] = "valueMT"

#: The `/MYSQL VAR\ ... TABLE=VALUEANAL-REC,HV` directive names the table
#: [common/valueMT.cbl:L278-L281], and the frozen schema defines it at
#: [mysql/ACASDB.sql:L1418-L1431].
TABLE_NAME: Final[str] = "VALUEANAL-REC"

#: The facade entity name, from the eleven `Value-*` verbs
#: [copybooks/Proc-ACAS-FH-Calls.cob:L711-L768].
ENTITY_FACADE: Final[str] = "Value"

#: `copy "wsval.cob" replacing VA-Code by WS-VA-Code.` [common/acas013.cbl:L269],
#: which is why the linkage record's key is `WS-VA-Code` while the indexed-file
#: record keeps `VA-Code` [copybooks/fdval.cob:L11].
RECORD_COPYBOOK: Final[str] = "copybooks/wsval.cob"

#: `PRIMARY KEY (`VA-CODE`)` [mysql/ACASDB.sql:L1429]. Taken from the shared
#: declaration table so this module and the cursor emulator cannot drift apart.
TABLE_PRIMARY_KEY: Final[str] = TABLE_PRIMARY_KEYS[TABLE_NAME]

#: N-logsystem6. `move 6 to WS-Log-System.` with the comment
#: `*> 1 = IRS, 2=GL, 3=SL, 4=PL, 6=PL & SL, 5=Stock used in FH logging`
#: [common/acas013.cbl:L298]. Two things are reproduced. First the VALUE: 6 means
#: "PL & SL", a composite subsystem no other handler uses, so
#: :class:`acas_posting.dal.status.LogSystem` - whose census is built from
#: `acas000` and `acas008` and stops at `LogSystem.STOCK` - has no member for it
#: and this is a literal rather than an enum lookup. Second the ORDERING: the
#: comment lists 6 BETWEEN 4 and 5, out of numeric sequence. Recorded, not
#: tidied; the enum is deliberately not extended, because extending a shared
#: vocabulary from one handler would misrepresent the other nineteen.
WS_LOG_SYSTEM: Final[int] = 6

#: N-log, first half. `move 13 to WS-Log-File-No.` [common/acas013.cbl:L299],
#: which is the indexed-file number: `select value-file assign file-13`
#: [copybooks/selval.cob:L2]. It is the value a caller sees on the indexed path,
#: because that path performs `ba012-Test-WS-Rec-Size-2` DIRECTLY [:L329] and so
#: never reaches the paragraph that overwrites it.
WS_LOG_FILE_NO_COBOL: Final[int] = 13

#: N-log, second half. `move 23 to WS-Log-File-no.` [common/acas013.cbl:L602] -
#: the sole statement of `ba010-Test-WS-Rec-Size`, reached only by
#: `perform ba-Process-RDBMS` [:L324]. It is the table number within the
#: subsystem rather than the file number. The declaration spells the field
#: `WS-Log-File-No` [:L299] and this site spells it `WS-Log-File-no`; COBOL is
#: case-insensitive so nothing breaks, and the inconsistency is recorded under
#: N-casing rather than normalised.
WS_LOG_FILE_NO_RDB: Final[int] = 23

#: ``77  prog-name           pic x(17)    value "acas013 (3.3.00)"``
#: [common/acas013.cbl:L250] - the handler's own self-identification, carried so a
#: log line can name the version of the program whose behaviour is reproduced.
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

#: ``move function Length (WS-Value-Record) to A`` [common/acas013.cbl:L607-L609].
#:
#: 66 bytes, as ``copybooks/wsval.cob:L6`` declares and as the field sum confirms:
#: ``va-code`` 3 + ``va-gl`` 6 + ``va-desc`` 24 + ``va-print`` 3 + three
#: ``9(5) comp`` at 4 + three ``s9(8)v99 comp-3`` at 6 = 66. N-recsize records that
#: two of those sizes are compiler-dependent, so the declared comment and the
#: measured length agree only under the settings the maintainer built with - which
#: is exactly the worry [common/acas013.cbl:L600] raises. NOTHING IS RESOLVED.
_WS_VALUE_RECORD_LENGTH: Final[int] = 66

#: ``move function length (Value-Record) to B`` [common/acas013.cbl:L610-L612].
#:
#: Also 66: ``copybooks/fdval.cob`` declares a field-identical layout and repeats the
#: same "record size 66 bytes" comment at its own L6. So ``A < B`` is ``66 < 66`` and
#: THE TEST CAN NEVER FIRE FOR THIS TABLE - the 901 path exists and is unreachable.
_VALUE_RECORD_LENGTH: Final[int] = 66

#: `05  WS-File-Key     pic x(64)` [copybooks/wsfnctn.cob:L52]. Every log key
#: this module writes is truncated to this width and space-padded to it, as a
#: `MOVE` to a fixed alphanumeric item does.
WS_FILE_KEY_WIDTH: Final[int] = 64

#: The receiving width of `WS-Log-Where`, `pic x(231)`
#: [copybooks/wsfnctn.cob:L53].
_WS_LOG_WHERE_WIDTH: Final[int] = 231

#: `01  WS-MYSQL-EDIT  PIC -Z(18)9.9(9).` [common/valueMT.cbl:L225]. Thirty
#: characters: sign at 1, nineteen integer positions at 2 to 20, point at 21,
#: nine decimal positions at 22 to 30. The bridge slices `(13:08)` and `(22:02)`
#: and never touches character 1 - see the module docstring.
_EDIT_WIDTH: Final[int] = 30
_EDIT_INTEGER_POSITIONS: Final[int] = 19
_EDIT_DECIMAL_POSITIONS: Final[int] = 9

#: The two slices the bridge actually takes, as one-based COBOL
#: reference-modification pairs [common/valueMT.cbl:L1196-L1203].
_EDIT_INTEGER_SLICE: Final[tuple[int, int]] = (13, 8)
_EDIT_DECIMAL_SLICE: Final[tuple[int, int]] = (22, 2)

#: The shared logging-subsystem census, read rather than restated, so that
#: N-logsystem6's claim can be checked instead of asserted: this handler's 6 is
#: absent from it. :data:`WS_LOG_SYSTEM` is therefore a literal.
_LOG_SYSTEM_CENSUS: Final[Mapping[str, int]] = MappingProxyType(
    {member.name: int(member.value) for member in LogSystem}
)

#: True exactly while no member of the shared census carries this handler's
#: code, which is the condition N-logsystem6 records.
_LOG_SYSTEM_IS_UNCENSUSED: Final[bool] = WS_LOG_SYSTEM not in set(
    _LOG_SYSTEM_CENSUS.values()
)


# ---------------------------------------------------------------------------
# N-flatkey: the copybook fields with no host variable and no column
# ---------------------------------------------------------------------------

#: The four copybook fields that have NO host variable and NO column, recorded as
#: deliberate omissions per R-5 ("Deliberate omissions are recorded as
#: omissions") rather than given columns of their own.
#:
#: The copybook declares a three-level key group [copybooks/wsval.cob:L10-L14];
#: the bridge re-declares the record inline and flattens that group to a single
#: `WS-Va-Code pic xxx` [common/valueMT.cbl:L309-L310]. All four survive only
#: inside `VA-CODE`'s three characters, which is why
#: :func:`bb100_unload_hvs` reconstitutes the group from those characters rather
#: than reading four columns that do not exist. The copybook contains no
#: `filler`, so these four are the complete omission set.
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


# ---------------------------------------------------------------------------
# The anomaly register, in machine-readable form (R-4)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Anomaly:
    """One reproduced legacy defect, with where it is and where it came from.

    Rule R-4 and Agent Action Plan section 0.7.4 C-4 together require an inline
    comment citing the COBOL locator at each reproduction site; this record makes
    the same information available to a reader and to
    ``docs/migration/anomaly-log.md``, which names this module as the reproducing
    module for every entry.
    """

    #: Stable identifier, matching the module docstring's register.
    name: str
    #: One-line statement of the defect, in this module's own words.
    summary: str
    #: Every frozen-source locator that evidences it.
    locators: tuple[str, ...]
    #: The function or data name in this module that reproduces it.
    reproduced_at: str


#: The complete register for this handler-and-bridge pair. Thirty-one entries:
#: the fourteen the assignment names, and seventeen more found by reading the two
#: frozen programs end to end. Every one is reproduced, none is repaired.
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


# ---------------------------------------------------------------------------
# The ten columns, derived from the data dictionary (R-5, "dictionary first")
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ColumnBinding:
    """One column of ``VALUEANAL-REC``, with the whole authoritative triple.

    Every field of this record is DERIVED - from ``loader.get_entry``,
    ``loader.drift_for`` and ``loader.cite`` - and none is transcribed from a
    picture clause. Agent Action Plan section 0.8.1 makes that a directive, and
    this table is the reason the directive pays: reading
    [common/valueMT.cbl:L294] by eye and seeing a money field would have produced
    a signed host variable, and the three money columns would have been wrong in
    exactly the way section 0.6.2 predicted could not happen.
    """

    #: The MySQL column name, hyphens and all - so it must be quoted.
    name: str
    #: ``ORDINAL_POSITION`` in the frozen table, 1 to 10.
    ordinal: int
    #: The dictionary key, e.g. ``VALUEANAL-REC.VA-V-THIS``.
    dictionary_key: str
    #: ``loader.cite(dictionary_key)`` - copybook, bridge and column locators.
    citation: str
    #: Attribute of :class:`WsValueRecord` this column is carried in. The key is
    #: a group in the record and three characters in the bridge, so the
    #: conversion is not symmetric - see :func:`bb000_hv_load`.
    record_attribute: str
    #: Attribute of :class:`TdValueanalRec` holding the host variable.
    host_attribute: str
    #: ``DECIMAL``, ``INT``, ``STR`` or ``NONE`` (the group key), from the
    #: dictionary's own storage classification.
    storage: str
    #: Total and integer digit counts of the BRIDGE HOST VARIABLE, which is the
    #: receiving field the value is actually truncated into.
    host_digits: int
    host_integer_digits: int
    #: Decimal places of the host variable: 2 for money, 0 otherwise.
    host_scale: int
    #: Character length of the host variable, for the alphanumeric columns.
    host_length: int
    #: Whether the host variable is signed. ``False`` for all ten here, which for
    #: the three money columns is the anomaly.
    host_signed: bool
    #: Whether the COPYBOOK field is signed. ``True`` for the three money fields,
    #: which is where the sign is lost from.
    copybook_signed: bool
    #: Whether the column is ``unsigned``.
    column_unsigned: bool
    #: Whether this column is the primary key.
    primary_key: bool
    #: The dictionary's own drift prose, verbatim, so the reason is never
    #: paraphrased away.
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

        True exactly when the copybook declares the field signed and the bridge
        host variable does not, which is the condition
        [copybooks/wsval.cob:L21-L23] against [common/valueMT.cbl:L294-L296]
        creates. It is derived rather than listed, so a field cannot be missed.
        """
        return self.copybook_signed and not self.host_signed


#: Which :class:`WsValueRecord` attribute carries each column, and which
#: :class:`TdValueanalRec` attribute is its host variable. Ordered as the frozen
#: table orders its columns, which is also the order
#: ``bb000-HV-Load`` moves them in [common/valueMT.cbl:L1060-L1069] - unlike
#: ``nominalMT`` and ``glpostingMT``, whose load order inverts against the
#: column order, this bridge's load order IS the column order.
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

    ``loader.entries_for_table`` returns the entries in COLUMN-ORDINAL order,
    which is the order every statement in this module names its columns in, so no
    sorting is applied and none is needed. The result is deterministic: the
    dictionary is a committed JSON artefact read in file order, there is no set
    iteration anywhere in this path, and two processes therefore build a
    byte-identical list - which rule R-6 requires.

    Raises:
        RuntimeError: If the dictionary and this module disagree about the table.
            That is a traceability defect under R-5 rather than a runtime
            condition to tolerate, so it is refused at import rather than
            papered over: a wrong locator or a missing field would silently
            produce wrong SQL.
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


#: The ten columns of ``VALUEANAL-REC`` in column-ordinal order, every field
#: derived from the data dictionary. This is the single source every statement in
#: this module draws its column list from, so an insert cannot name nine columns
#: and an update cannot name eleven.
COLUMNS: Final[tuple[ColumnBinding, ...]] = _build_columns()

#: Column lookup by name, for the fetch path.
_COLUMNS_BY_NAME: Final[Mapping[str, ColumnBinding]] = MappingProxyType(
    {binding.name: binding for binding in COLUMNS}
)

#: The three money columns, identified by the dictionary rather than by a hard
#: coded list - see :attr:`ColumnBinding.loses_its_sign_at_the_bridge`.
_SIGN_LOSING_COLUMNS: Final[tuple[ColumnBinding, ...]] = tuple(
    binding for binding in COLUMNS if binding.loses_its_sign_at_the_bridge
)


def column_citations() -> tuple[str, ...]:
    """Return one dictionary citation per column, in column-ordinal order.

    Each line names the copybook field, the bridge host variable and the MySQL
    column that together define one field, which is the triple R-5 requires every
    field to be traceable through. Provided as a function rather than a constant
    so that ``docs/migration/traceability.md`` can be regenerated from the
    running module rather than kept in step by hand.
    """
    return tuple(binding.citation for binding in COLUMNS)


# ---------------------------------------------------------------------------
# The key declaration table, for START and READ NEXT
# ---------------------------------------------------------------------------

#: Every ``keyOfReference`` slot this bridge declares. There is exactly ONE,
#: transcribed from [common/valueMT.cbl:L237-L247]::
#:
#:     01  Table-Of-Keynames.
#:         03  filler  pic x(30) value 'VA-CODE                       '.
#:         03  filler  pic x(8)  value '00010003'.   *> offset/length
#:         03  filler  pic x(3)  value 'STR'.        *> data type
#:     01  filler redefines Table-Of-Keynames.
#:         03  keyOfReference occurs 1    indexed by KOR-x1.
#:             05  keyname    pic x(30).
#:             05  KOR-offset pic 9(4).
#:             05  KOR-length pic 9(4).
#:             05  KOR-Type   pic XXX.               *> Not used currently
#:
#: Offset 1, length 3 - BYTES OF THE WORKING-STORAGE RECORD, which is how the
#: bridge slices the key value straight out of it as ``VALUEANAL-REC (K:L)``
#: [common/valueMT.cbl:L613-L616]. Because the bridge flattened the key group
#: (N-flatkey) those three bytes are the whole of ``WS-Va-Code``.
#:
#: ONE key, despite ``aa045-Eval-Keys`` existing to discriminate a key number
#: [common/acas013.cbl:L452-L468]: that paragraph's inner ``evaluate File-Key-No``
#: has a single arm, ``when 1``, and its ``when other`` clears the log key. So the
#: paragraph that would discriminate a second key finds there is none.
#:
#: N-kortype: the declared type ``'STR'`` is carried by a field whose own comment
#: says it is not used currently [common/valueMT.cbl:L247], and it differs per
#: bridge - ``slpostingMT`` declares ``'BNT'``. Data that varies and is read by
#: nothing. It is preserved on the record rather than dropped.
#:
#: Read from the shared declaration table rather than restated, so this module and
#: the cursor emulator cannot describe the same key differently.
KEY_OF_REFERENCE: Final[KeyOfReference] = TABLE_OF_KEYNAMES[TABLE_NAME][0]

#: The sequential-read starting position, `>= "000"`
#: [common/valueMT.cbl:L476-L477]. N-readnext-lowkey: the low key is a VALUE and
#: not a floor, so a row whose three-character code sorts below ``"000"`` - a
#: space-leading code, for instance - is silently never returned by a sequential
#: walk. The sibling ``analMT``, with an identically shaped three-byte key, uses
#: ``>`` where this one uses ``>=``, so even the relation is not a house rule.
_SEQUENTIAL_READ: Final = SEQUENTIAL_READ_START[TABLE_NAME]

#: `" >= "` as the bridge writes it [common/valueMT.cbl:L476].
SEQUENTIAL_READ_RELATION: Final[str] = _SEQUENTIAL_READ.relation.token

#: The low key itself, ``000``. The bridge writes it as the COBOL literal
#: `'"000"'` [common/valueMT.cbl:L477] - a literal that carries the statement's
#: own double quotes inside it - so the quoting is applied where the clause is
#: assembled and this constant holds only the three key characters.
SEQUENTIAL_READ_LOW_KEY: Final[str] = str(_SEQUENTIAL_READ.low_key)

#: The single cursor slot this bridge uses. ``Most-Cursor-Set`` is one digit with
#: two condition names, ``Cursor-Not-Active`` and ``Cursor-Active``
#: [common/valueMT.cbl:L255-L258], so there is one cursor and it is either live or
#: it is not.
_CURSOR_SLOT: Final[CursorSlot] = CursorSlot.PRIMARY


# ---------------------------------------------------------------------------
# COBOL storage and edit semantics, reproduced for this table only
# ---------------------------------------------------------------------------


def _pic_x(value: object, length: int) -> str:
    """Store ``value`` into a ``PIC X(length)`` item, as ``MOVE`` would.

    Alphanumeric ``MOVE`` is left-justified: a shorter sending item is padded on
    the right with spaces, a longer one is truncated on the right. Applied to
    ``HV-VA-CODE`` X(3), ``HV-VA-DESC`` X(24) and ``HV-VA-PRINT`` X(3)
    [common/valueMT.cbl:L287-L290], and to ``WS-File-Key`` x(64)
    [copybooks/wsfnctn.cob:L52].
    """
    text = "" if value is None else str(value)
    return text[:length].ljust(length)


def _cobol_trim_trailing(text: str) -> str:
    """``FUNCTION TRIM (item, TRAILING)`` - trailing spaces only.

    The bridge trims the three alphanumeric host variables this way, and only
    this way, before quoting them into a statement
    [common/valueMT.cbl:L1119, :L1140, :L1149] on the insert path and
    [:L1268, :L1289, :L1298] on the update path. LEADING SPACES SURVIVE, so a
    value-analysis code of ``" 1"`` is stored with its leading space intact and is
    a different key from ``"1 "``. Reproduced exactly: stripping both ends would
    silently merge keys the frozen system keeps apart.
    """
    return text.rstrip(" ")


def _cobol_trim(text: str) -> str:
    """``FUNCTION TRIM (item)`` with no direction - both ends.

    Used on the numeric edit slices [common/valueMT.cbl:L1130 and its nine
    siblings] and on the rewrite's where clause [:L1392]. On an edit slice the
    leading spaces are what zero suppression produced, so trimming both ends is
    what turns ``"    1234"`` into ``"1234"``.
    """
    return text.strip(" ")


def _ws_mysql_edit(value: Decimal) -> str:
    """Render into ``WS-MYSQL-EDIT``, ``PIC -Z(18)9.9(9)``.

    Thirty characters [common/valueMT.cbl:L225]: the sign at character 1,
    nineteen integer digit positions at 2 to 20, the decimal point at 21, nine
    decimal positions at 22 to 30. Zero suppression blanks leading zeros in the
    ``Z`` positions 2 to 19; position 20 is a hard ``9`` and always holds a digit,
    which is why zero renders as ``"0"`` and not as spaces.

    THE SIGN IS RENDERED HERE AND NEVER READ. The bridge only ever slices
    ``(13:08)`` and ``(22:02)``, so character 1 is dead - the second of the two
    sign-loss mechanisms described in the module docstring. It is still rendered,
    because reproducing the field means reproducing the field; a reader diffing
    this against [common/valueMT.cbl:L225] should find all thirty characters.

    Args:
        value: The host variable's value. Always non-negative by the time it
            arrives, because every host variable here is unsigned and
            :func:`_hv_unsigned_money` and :func:`_hv_unsigned_integer` have
            already applied that. A negative value would render with the sign in
            character 1, where nothing reads it.

    Returns:
        Exactly thirty characters.
    """
    sign = "-" if value < 0 else " "
    magnitude = value.copy_abs()
    integer_part = int(magnitude)
    # The nine decimal positions, as digits, taken by scaling rather than by
    # text surgery so that a value carrying fewer than nine places pads with
    # zeros exactly as the picture does.
    fraction = magnitude - Decimal(integer_part)
    decimals = int(
        (fraction * (10**_EDIT_DECIMAL_POSITIONS)).quantize(
            Decimal(1), rounding=ROUND_DOWN
        )
    )
    integer_digits = str(integer_part)[-_EDIT_INTEGER_POSITIONS:]
    # Zero suppression: the 18 Z positions blank, position 19 of the integer run
    # (character 20) is a hard 9 and keeps its digit.
    suppressed = integer_digits.rjust(_EDIT_INTEGER_POSITIONS)
    rendered = f"{sign}{suppressed}.{decimals:0{_EDIT_DECIMAL_POSITIONS}d}"
    return _pic_x(rendered, _EDIT_WIDTH)


def _edit_slice(edited: str, start: int, length: int) -> str:
    """Take a one-based COBOL reference modification out of an edited item.

    ``WS-MYSQL-EDIT(13:08)`` is characters 13 to 20 inclusive; Python's slice
    bounds are shifted by one. Isolated so that the two magic pairs appear once
    each, next to their locator, instead of at ten call sites.
    """
    return edited[start - 1 : start - 1 + length]


def _require_exact_numeric(value: object, what: str) -> None:
    """Refuse any numeric value that is not exactly representable.

    ⭐ THIS IS THE ENFORCEMENT POINT FOR THE ZERO-BINARY-FLOATING-POINT RULE
    (Agent Action Plan section 0.7.2, R-2), which forbids an accounting value
    passing through a binary floating-point type "at any point - not in
    computation, not in storage, not in transport".

    A whitelist, not a blacklist: only ``Decimal`` and ``int`` are admitted.
    Written that way on purpose, because a blacklist would have to be revisited
    every time a caller reached for a new inexact type, and because it also turns
    away the near misses - a numeric string, a rational built from an inexact
    quotient, a third-party numeric scalar - each of which would otherwise be
    silently coerced into something plausible. ``bool`` passes as a subclass of
    ``int``, which is harmless: a ``MOVE`` of ``1`` into ``PIC 9(08) COMP`` stores
    ``1``.

    Why a guard is needed at all, when every annotation already says ``Decimal``:
    :class:`TdValueanalRec` and :func:`bb100_unload_hvs` are part of the published
    surface, so a caller CAN hand this module an inexact value, and annotations do
    not execute. Without the guard the inexact value would be quantized into a
    tidy-looking exact one - ``0.1 + 0.2`` becoming ``0.30`` - and the binary
    artefact would be laundered rather than caught. That is the single failure mode
    R-2 exists to prevent, so it is refused loudly instead.

    This is NOT a business validation, and so is not the kind of addition
    forbidden by R-3: it adds no accounting rule the COBOL lacks and can never
    change a posted figure. It only asserts the storage class that COBOL's own
    ``COMP-3`` and ``COMP`` items guarantee by construction, which
    :mod:`acas_posting.dal.connection` asserts on the driver side by pinning its
    converters rather than trusting the default.

    Args:
        value: The candidate, straight from a record or host-variable field.
        what: The field being stored, for a diagnosis that names the culprit.

    Raises:
        TypeError: If the value is neither ``Decimal`` nor ``int``.

        >>> _require_exact_numeric(Decimal("1.23"), "VA-V-THIS")
        >>> _require_exact_numeric(7, "VA-GL")
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

    THE ONE HELPER for all three money fields, applied in :func:`bb000_hv_load`
    before any statement text exists, because that is where COBOL applies it:
    ``move va-v-this to HV-va-v-this`` [common/valueMT.cbl:L1067-L1069] moves a
    ``pic s9(8)v99 comp-3`` item [copybooks/wsval.cob:L21-L23] into a
    ``PIC 9(08)V9(02) COMP`` item [common/valueMT.cbl:L294-L296] whose column is
    ``decimal(10,2) unsigned`` [mysql/ACASDB.sql:L1426-L1428].

    Two things happen, in this order, both of them the receiving field's doing:

    1. THE SIGN IS DROPPED. A receiving item with no sign cannot carry one, so the
       magnitude is what is stored. Expressed with ``Decimal.copy_abs``, the
       decimal module's sign-clearing operation - which is a storage operation on
       the representation, not the arithmetic absolute value that repairing this
       defect would require, and which handles a negative zero correctly.
    2. THE MAGNITUDE IS FITTED. Eight integer digits and two decimal places, so a
       larger magnitude loses its high-order digits and a longer fraction is
       truncated toward zero - COBOL truncates on store unless ``ROUNDED`` is
       written, and this ``MOVE`` is not a ``COMPUTE`` and carries no ``ROUNDED``.
       The copybook is itself 8.2 so the fit is normally a no-op; it is applied
       anyway because the record class is deliberately not frozen - ``sl055`` and
       ``pl055`` accumulate into these fields in place - so a value wider than the
       host variable can genuinely arrive.

    WHAT THIS DELIBERATELY DOES NOT DO: it does not raise, does not clamp a
    negative to zero, does not reject the row, and does not let the driver refuse
    it. Each of those would be a repair, and R-4 is explicit that "A defect
    reproduced is correct; a defect fixed is a failure."

    THE EXACT STORED VALUE IS AN OPEN QUESTION. Agent Action Plan section 0.6.8
    lists "A negative binary value through an unsigned host variable into an
    unsigned column" among the five questions only compiled execution can settle,
    and the data dictionary independently tags all three of these fields ``Q-3``
    for the same reason. The reading implemented here is the one defensible from
    the frozen source - a sign is applied to a receiving item only when that item
    has one - and it is recorded as pending arbitration in
    ``docs/migration/ambiguity-resolutions.md``. If the oracle shows the bridge's
    C interface produces something else, this function is the only thing that
    changes.

    Args:
        value: The record's value, signed as the copybook declares it.
        binding: The column, for its host-variable digits and scale. Passed
            rather than assumed so the shape comes from the dictionary.

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
        # High-order truncation, as a MOVE into a narrower numeric item does.
        fitted = (fitted % modulus).quantize(scale, rounding=ROUND_DOWN)
    return fitted


def _hv_unsigned_integer(value: int, binding: ColumnBinding) -> int:
    """Store into an unsigned integer host variable, ``PIC 9(08) COMP``.

    Covers ``HV-VA-GL`` and the three ``HV-VA-T-*`` counters
    [common/valueMT.cbl:L288, :L291-L293]. Unlike the money fields these lose
    NOTHING at the bridge, and the difference is worth stating because it is what
    makes the money case an anomaly rather than a pattern: their copybook
    declarations are ``pic 9(6)`` and ``pic 9(5) comp``
    [copybooks/wsval.cob:L15, :L18-L20] - already unsigned - so there is no sign
    to lose. The dictionary records digits drift only (6 or 5 widening to 8, then
    narrowing again at a ``mediumint(6)`` or ``mediumint(5)`` column) and, for
    ``VA-GL``, a storage-class change from ``DISPLAY`` to ``COMP``.

    The host variable's eight digits are the fitting width, because the host
    variable is the receiving field. A magnitude wider than that loses its
    high-order digits, as a numeric ``MOVE`` does.

    Raises:
        TypeError: If the value is not an exact numeric type. See
            :func:`_require_exact_numeric`.
    """
    _require_exact_numeric(value, f"{binding.name} (record value)")
    value = int(value)
    magnitude = -value if value < 0 else value
    modulus = 10**binding.host_integer_digits
    return magnitude % modulus


# ---------------------------------------------------------------------------
# TD-VALUEANAL-REC, the host-variable group
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class TdValueanalRec:
    """``01 TD-VALUEANAL-REC.`` - the bridge's host-variable group.

    Field for field from [common/valueMT.cbl:L285-L297]::

        01  TP-VALUEANAL-REC                      USAGE POINTER.
        01  TD-VALUEANAL-REC.
            05  HV-VA-CODE                        PIC X(3).
            05  HV-VA-GL                          PIC  9(08) COMP.
            05  HV-VA-DESC                        PIC X(24).
            05  HV-VA-PRINT                       PIC X(3).
            05  HV-VA-T-THIS                      PIC  9(08) COMP.
            05  HV-VA-T-LAST                      PIC  9(08) COMP.
            05  HV-VA-T-YEAR                      PIC  9(08) COMP.
            05  HV-VA-V-THIS                      PIC  9(08)V9(02) COMP.
            05  HV-VA-V-LAST                      PIC  9(08)V9(02) COMP.
            05  HV-VA-V-YEAR                      PIC  9(08)V9(02) COMP.

    generated from the ``/MYSQL VAR\\ ... TABLE=VALUEANAL-REC,HV`` directive
    [common/valueMT.cbl:L278-L281].

    THE LAST THREE CARRY NO ``S``. That is N-money-signloss, and it is the whole
    reason this class exists as its own type rather than as a dictionary of
    values: the group is the boundary where the sign is lost, so making it a real
    object with real declared widths puts the loss somewhere a reader can see it.

    ``TP-VALUEANAL-REC`` is the result-set pointer the fetch call is handed
    [common/valueMT.cbl:L285, :L545-L546]. It is a C-side handle with no Python
    counterpart - the cursor state in :mod:`acas_posting.dal.cursor_state` plays
    its role - and is recorded as a representation-only omission.

    Mutable, unlike most records in this layer, because the group is
    working storage that the bridge initialises and refills on every call. It is
    not shared between calls and never escapes the function that built it.
    """

    #: `PIC X(3)` [:L287] - the FLATTENED key. The record's three-level group
    #: [copybooks/wsval.cob:L10-L14] has no counterpart here; see N-flatkey.
    hv_va_code: str = "   "
    #: `PIC 9(08) COMP` [:L288], from a `pic 9(6)` DISPLAY field.
    hv_va_gl: int = 0
    #: `PIC X(24)` [:L289].
    hv_va_desc: str = " " * 24
    #: `PIC X(3)` [:L290].
    hv_va_print: str = "   "
    #: `PIC 9(08) COMP` [:L291-L293], from `pic 9(5) comp` counters.
    hv_va_t_this: int = 0
    hv_va_t_last: int = 0
    hv_va_t_year: int = 0
    #: `PIC 9(08)V9(02) COMP` [:L294-L296] - UNSIGNED, from signed
    #: `pic s9(8)v99 comp-3` money fields. N-money-signloss.
    hv_va_v_this: Decimal = field(default_factory=lambda: Decimal("0.00"))
    hv_va_v_last: Decimal = field(default_factory=lambda: Decimal("0.00"))
    hv_va_v_year: Decimal = field(default_factory=lambda: Decimal("0.00"))

    def initialize(self) -> None:
        """``initialize TD-VALUEANAL-REC.`` [common/valueMT.cbl:L1059].

        The FIRST statement of the load paragraph, and the reason every column of
        this table can be declared ``NOT NULL``: an unset field becomes zero or
        space, never SQL ``NULL``. Agent Action Plan section 0.6.2 states the
        consequence for this layer - "the Python layer must default rather than
        omit".

        Plain ``INITIALIZE`` without ``ALL`` or ``WITH FILLER`` sets numeric items
        to zero and alphanumeric items to spaces, which is what these defaults
        are. Contrast the ``initialize ... with filler`` at [:L582] - N-initialize.
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
    """The three characters of ``WS-Va-Code``, as the bridge sees the key.

    The record holds a three-level group [copybooks/wsval.cob:L10-L14]; the bridge
    holds three flat characters [common/valueMT.cbl:L310]. Assembling them in
    declaration order - ``va-system``, then ``va-group``'s ``va-first`` and
    ``va-second`` - is exactly what the group occupies in storage, and it is what
    ``VALUEANAL-REC (K:L)`` slices out with the declared offset 1 and length 3
    [common/valueMT.cbl:L613-L616]. N-flatkey.
    """
    code = value.va_code
    return _pic_x(
        f"{code.va_system}{code.va_group.va_first}{code.va_group.va_second}",
        KEY_OF_REFERENCE.kor_length,
    )


def bb000_hv_load(value: WsValueRecord) -> TdValueanalRec:
    """``bb000-HV-Load Section.`` [common/valueMT.cbl:L1051].

    Moves the record's fields into the host-variable group, ready for an insert or
    an update. Transcribed statement for statement from
    [common/valueMT.cbl:L1059-L1069]::

        initialize TD-VALUEANAL-REC.
        move     WS-VA-Code            to HV-VA-Code
        move     va-gl                 to HV-va-gl
        move     va-desc               to HV-va-desc
        move     va-print              to HV-va-print
        move     va-t-this             to HV-va-t-this
        move     va-t-last             to HV-va-t-last
        move     va-t-year             to HV-va-t-year
        move     va-v-this             to HV-va-v-this
        move     va-v-last             to HV-va-v-last
        move     va-v-year             to HV-va-v-year.

    Four facts about that block, each preserved rather than tidied:

    * THE LOAD ORDER IS THE COLUMN ORDER. Ten moves, matching ordinals 1 to 10 of
      the frozen table. ``nominalMT`` and ``glpostingMT`` are the bridges whose
      load order inverts against their column order; this one does not, so
      :data:`COLUMNS` can drive both the moves and the statement.
    * THE KEY IS LOADED. [:L1060] moves it, unlike ``glpostingMT``, which leaves
      ``HV-POST-RRN`` unloaded because the row number is the database's to assign.
    * N-hvcase. The declarations are upper case [:L288-L296]; nine of the ten
      moves write the host-variable name lower-cased after the ``HV-`` prefix
      [:L1061-L1069] and the key move alone writes it upper [:L1060]. COBOL is
      case-insensitive, so nothing breaks and nothing is normalised.
    * ONLY THE LAST MOVE CARRIES A TERMINATING PERIOD [:L1069] - the same style as
      ``nominalMT``, and unlike ``slpostingMT``, where every move has one. A
      formatting fact with no behavioural consequence, recorded so a reader
      diffing the two is not surprised.

    The maintainer's own closing comment [common/valueMT.cbl:L1071-L1072] explains
    why the paragraph is where it is, verbatim: "Loading HVs implies a non-Fetch
    action. RGs are handled separately for all such actions so they must not be
    loaded here."

    THIS IS WHERE THE SIGN IS LOST. The three money moves go through
    :func:`_hv_unsigned_money` because their receiving items are unsigned, and
    they do so HERE - before any statement text exists - because that is where
    COBOL does it. Building the statement first and converting later would put the
    loss on the wrong side of the boundary and would misrepresent which layer is
    responsible.

    Args:
        value: The caller's ``WS-Value-Record``. Not modified.

    Returns:
        A freshly initialised host-variable group holding the converted values.
    """
    host = TdValueanalRec()
    host.initialize()  # [:L1059] - first, so nothing can reach a column as NULL.

    # [:L1060] `move WS-VA-Code to HV-VA-Code` - the flattened three characters.
    host.hv_va_code = _pic_x(_flat_key_of(value), _COLUMNS_BY_NAME["VA-CODE"].host_length)
    # [:L1061] `move va-gl to HV-va-gl` - pic 9(6) DISPLAY into PIC 9(08) COMP.
    host.hv_va_gl = _hv_unsigned_integer(value.va_gl, _COLUMNS_BY_NAME["VA-GL"])
    # [:L1062] `move va-desc to HV-va-desc`.
    host.hv_va_desc = _pic_x(value.va_desc, _COLUMNS_BY_NAME["VA-DESC"].host_length)
    # [:L1063] `move va-print to HV-va-print`.
    host.hv_va_print = _pic_x(value.va_print, _COLUMNS_BY_NAME["VA-PRINT"].host_length)
    # [:L1064-L1066] the three counters. Unsigned in the copybook already, so
    # nothing is lost here - which is what makes the money case below an anomaly.
    host.hv_va_t_this = _hv_unsigned_integer(
        value.va_t_this, _COLUMNS_BY_NAME["VA-T-THIS"]
    )
    host.hv_va_t_last = _hv_unsigned_integer(
        value.va_t_last, _COLUMNS_BY_NAME["VA-T-LAST"]
    )
    host.hv_va_t_year = _hv_unsigned_integer(
        value.va_t_year, _COLUMNS_BY_NAME["VA-T-YEAR"]
    )
    # [:L1067-L1069] the three money fields. N-money-signloss: signed
    # `pic s9(8)v99 comp-3` [copybooks/wsval.cob:L21-L23] into unsigned
    # `PIC 9(08)V9(02) COMP` [common/valueMT.cbl:L294-L296], column
    # `decimal(10,2) unsigned` [mysql/ACASDB.sql:L1426-L1428]. A credit balance
    # stops being one here, before any SQL runs. Reproduced, not repaired.
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

    Moves the host variables back into the caller's record after a fetch.
    Transcribed from [common/valueMT.cbl:L1086-L1097]::

        initialize VALUEANAL-REC.

        move     HV-VA-Code          to WS-VA-Code
        move     HV-va-gl            to va-gl
        move     HV-va-desc          to va-desc
        move     HV-va-print         to va-print
        move     HV-va-t-this        to va-t-this
        move     HV-va-t-last        to va-t-last
        move     HV-va-t-year        to va-t-year
        move     HV-va-v-this        to va-v-this
        move     HV-va-v-last        to va-v-last
        move     HV-va-v-year        to va-v-year.

    N-initialize: the initialisation at [:L1086] is PLAIN, while the error path at
    [:L582] writes ``initialize VALUEANAL-REC with filler``. Two initialisation
    semantics in one bridge, as in ``glbatchMT``, ``slpostingMT`` and ``salesMT``.
    Each is reproduced at its own site and neither is harmonised: ``WITH FILLER``
    additionally clears filler items, and although this record declares no filler
    - so here the two happen to coincide - the distinction is the bridge's and not
    this module's to collapse.

    The maintainer's comment above it [common/valueMT.cbl:L1080-L1084] records the
    contract the initialisation supports: "NULL fields must not be returned in the
    buffer. SQL filters each column to ensure it has a proper value. This saves
    using indicator variables." And the parenthetical "(init moved lower)" [:L1081]
    is why the ``initialize`` sits nine lines below the comment that describes it.

    THE SIGN IS NOT RESTORED. The host variables are unsigned, the columns are
    unsigned, and a fetch therefore returns a magnitude. This function does not
    re-derive a sign, because there is nothing to re-derive it from: the
    information left the system on the way in. So a credit total written as -12.34
    reads back as 12.34, and the record's signed descriptors then carry a positive
    value quite legitimately.

    N-hvcase applies here too: [:L1088] writes the key host variable upper-cased
    and [:L1089-L1097] write the other nine lower-cased.

    THE KEY IS REBUILT, NOT COPIED. The record's key is a three-level group and
    the host variable is three flat characters, so the group is reconstituted
    character by character - the inverse of :func:`_flat_key_of`. The four
    sub-field names still have no column; they are being repopulated from the
    three characters that are all the bridge ever carried. N-flatkey.

    Args:
        host: The group just filled by a fetch.
        value: The caller's record, MUTATED in place - which is what a COBOL
            ``MOVE`` into a linkage item does, and why
            :class:`WsValueRecord` is deliberately not frozen.
    """
    # [:L1086] `initialize VALUEANAL-REC.` - plain, not `with filler`.
    # Reproduced by writing every field below, which is what INITIALIZE followed
    # by ten unconditional moves amounts to: no field survives from the previous
    # call, so a fetch cannot leak the last row's value into an unfilled item.
    code = _pic_x(host.hv_va_code, KEY_OF_REFERENCE.kor_length)
    # [:L1088] `move HV-VA-Code to WS-VA-Code` - three characters back into the
    # three-level group the bridge flattened away. N-flatkey.
    value.va_code = VaCode(
        va_system=code[0],
        va_group=VaGroup(va_first=code[1], va_second=code[2]),
    )
    # Every numeric field is checked for exactness before it is read out, so that
    # an inexact value reaching the published host-variable group is refused rather
    # than quantized into a tidy-looking exact one (R-2, see
    # :func:`_require_exact_numeric`).
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
    # [:L1089-L1091] the display and alphanumeric fields.
    value.va_gl = int(host.hv_va_gl)
    value.va_desc = _pic_x(host.hv_va_desc, _COLUMNS_BY_NAME["VA-DESC"].host_length)
    value.va_print = _pic_x(host.hv_va_print, _COLUMNS_BY_NAME["VA-PRINT"].host_length)
    # [:L1092-L1094] the three counters.
    value.va_t_this = int(host.hv_va_t_this)
    value.va_t_last = int(host.hv_va_t_last)
    value.va_t_year = int(host.hv_va_t_year)
    # [:L1095-L1097] the three money fields, arriving as magnitudes because the
    # column and the host variable are both unsigned. N-money-signloss: the sign
    # was lost on the way in and is not recoverable here.
    scale = Decimal(1).scaleb(-_COLUMNS_BY_NAME["VA-V-THIS"].host_scale)
    value.va_v_this = Decimal(host.hv_va_v_this).quantize(scale, rounding=ROUND_DOWN)
    value.va_v_last = Decimal(host.hv_va_v_last).quantize(scale, rounding=ROUND_DOWN)
    value.va_v_year = Decimal(host.hv_va_v_year).quantize(scale, rounding=ROUND_DOWN)


# ---------------------------------------------------------------------------
# Statement assembly - the COBOL-shaped text, and the bound form that executes
# ---------------------------------------------------------------------------

#: The table name, quoted once. The bridge writes the literal
#: ``"`VALUEANAL-REC`"`` with its backticks already in it
#: [common/valueMT.cbl:L497, :L633, :L858, :L1106], because every ACAS identifier
#: contains a hyphen and would otherwise be a syntax error.
_QUOTED_TABLE: Final[str] = quote_identifier(TABLE_NAME)

#: The primary-key column, quoted, as the bridge writes it: a backtick, then
#: ``KeyName (KOR-x1) delimited by space``, then a backtick
#: [common/valueMT.cbl:L479-L481]. ``delimited by space`` is what turns the
#: thirty-character declared key name into ``VA-CODE``, and it is reproduced with
#: the shared helper rather than by a local strip so that every handler module
#: means the same thing by it.
_QUOTED_KEY: Final[str] = quote_identifier(
    cobol_string_delimited_by_space(KEY_OF_REFERENCE.key_name)
)


@dataclass(frozen=True, slots=True)
class _Statement:
    """One statement in both of its forms, plus what the bridge would log.

    ``text`` is the statement as the BRIDGE assembles it, values interpolated as
    quoted literals, so it can be diffed against the frozen source.
    ``bound``/``parameters`` are what actually executes, because
    :func:`acas_posting.dal.connection.execute_statement` binds values and never
    interpolates them. The values are the same in both: every parameter is
    derived from the rendered text, so the two cannot disagree.

    TWO DELIBERATE DIFFERENCES BETWEEN THE FORMS, both recorded because R-5 requires
    omissions be visible:

    * ``bound`` OMITS THE TRAILING ``";"`` that ``text`` carries wherever the bridge
      writes one. A statement terminator is meaningful only to a client parsing a
      script; the driver is handed exactly one statement and multi-statement
      execution is disabled server-side, so the semicolon has no addressee. ``text``
      keeps it, so a comparison against the frozen bridge's ``WS-MYSQL-COMMAND``
      still matches character for character.
    * ``bound`` carries ``%s`` where ``text`` carries a quoted literal. This is not
      a stylistic choice: the frozen bridge interpolates values into statement text,
      which is safe there only because every value has already passed through a
      fixed-width COBOL picture. Reproducing the interpolation in Python would
      reproduce an injection surface instead of a behaviour, so the value travels
      as a parameter and the interpolated form survives only as the compared
      artefact. The bytes MySQL receives for each value are the same either way.
    """

    #: The COBOL-shaped statement, values rendered. Goes to ``WS-Log-Where``.
    text: str
    #: The same statement with ``%s`` placeholders.
    bound: str
    #: The values, in the placeholders' own order.
    parameters: tuple[object, ...]


def _where_with_pointer(*parts: str) -> str:
    """Assemble a where clause the way the bridge does, artefact included.

    Every clause in this bridge is built as::

        move     spaces to WS-Where
        move     1   to J
        string   ... into WS-Where with pointer J
        end-string

    and then consumed as ``WS-Where (1:J)``
    [common/valueMT.cbl:L477-L487, :L609-L618, :L735-L749, :L845-L852,
    :L911-L920]. ``STRING`` leaves the pointer ONE PAST the last character
    transferred, so ``(1:J)`` reads one character further than was written - and
    because the field was cleared to spaces first, that character is a space.

    N-pointer-offbyone: EVERY statement this bridge emits, and every clause it
    logs, therefore carries exactly one extra trailing space. MySQL is indifferent
    to it, but ``WS-Log-Where`` is not, and the rewrite's where clause is the only
    one the bridge trims [:L1392], so it alone escapes. The space is appended here
    rather than at five call sites so that the one place it comes from is the one
    place it is explained.
    """
    return "".join(parts) + " "


def _quoted_literal(text: str) -> str:
    """A value as the bridge quotes it into statement text: double quotes.

    The bridge writes ``'="'`` then the value then ``'"'``
    [common/valueMT.cbl:L612-L616]. MySQL accepts double-quoted strings, which is
    why this works at all. Only ever used to build the COBOL-shaped ``text``; the
    executed form binds instead, so this never carries a value to the server.
    """
    return f'"{text}"'


def _rendered_value(binding: ColumnBinding, host: TdValueanalRec) -> tuple[str, object]:
    """Render one host variable as the bridge renders it, and bind the same value.

    Three renderings, one per storage class, each transcribed from the insert
    paragraph [common/valueMT.cbl:L1102-L1249] - the update paragraph
    [:L1251-L1402] repeats them identically:

    * ALPHANUMERIC - ``FUNCTION TRIM (HV-VA-CODE,TRAILING)`` and its two siblings
      [:L1119, :L1140, :L1149]. Trailing spaces only, so a leading space survives
      into the key.
    * UNSIGNED INTEGER - ``MOVE HV-VA-GL TO WS-MYSQL-EDIT`` then
      ``FUNCTION TRIM (WS-MYSQL-EDIT(13:08))`` [:L1127-L1132]. The trim here has no
      direction, so it removes the blanks zero suppression left.
    * UNSIGNED MONEY - the same integer slice, then ``"."``, then
      ``WS-MYSQL-EDIT(22:02)`` UNTRIMMED [:L1196-L1203]. The decimal slice is
      always two digits, so there is nothing to trim, and zero renders ``"0.00"``.

    The bound value is parsed back out of the rendered text rather than taken from
    the host variable, so the value that executes is provably the value the bridge
    would have written - the two forms cannot drift.

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
    # Alphanumeric, including the flattened key, whose storage the dictionary
    # classifies as NONE because the copybook side of it is a group.
    rendered = _cobol_trim_trailing(_pic_x(raw, binding.host_length))
    return rendered, rendered


def _assignment_list(host: TdValueanalRec) -> tuple[str, str, tuple[object, ...]]:
    """The ten ``column="value"`` assignments, comma-separated, in ordinal order.

    Shared by the insert [common/valueMT.cbl:L1102-L1249] and the update
    [:L1251-L1402], which assemble an identical list - the update merely puts a
    where clause after it. The separator is the bridge's own ``', '``
    [:L1123-L1124]: comma then space.

    ALL TEN COLUMNS ARE ALWAYS NAMED, and nothing is ever bound as ``None``.
    Every column of this table is ``NOT NULL`` [mysql/ACASDB.sql:L1419-L1428] and
    the host-variable group was initialised before it was loaded
    [common/valueMT.cbl:L1059], so an unset field is a zero or a space and there
    is no such thing here as an omitted column.

    N-updates-key: the list includes ``VA-CODE``, so the update assigns the primary
    key to itself on every rewrite while the same value also appears in the where
    clause. Preserved.
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

    Builds ``INSERT INTO `VALUEANAL-REC` SET ...;`` - the ``SET`` form rather than
    the column-list-and-``VALUES`` form, exactly as the bridge writes it
    [:L1107-L1110]::

        STRING 'INSERT INTO '
                 '`VALUEANAL-REC` SET '

    then the ten assignments, then ``";"`` [:L1238] and the null terminator
    [:L1240], and finally ``PERFORM MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT``
    [:L1243]. The null terminator is a C-string convention of the frozen
    interface, not part of the SQL, so it has no Python counterpart and is a
    recorded representation-only omission.

    The single space after ``SET`` comes from the literal at [:L1108], which ends
    with one; the first assignment adds none of its own. Preserved, because the
    text is a compared artefact.
    """
    text_list, bound_list, parameters = _assignment_list(host)
    return _Statement(
        text=f"INSERT INTO {_QUOTED_TABLE} SET {text_list};",
        bound=f"INSERT INTO {_QUOTED_TABLE} SET {bound_list}",
        parameters=parameters,
    )


def bb300_update(host: TdValueanalRec, where: _Statement) -> _Statement:
    """``bb300-Update Section.`` [common/valueMT.cbl:L1251].

    Builds ``UPDATE `VALUEANAL-REC` SET ... WHERE ...;`` [:L1256-L1259,
    :L1388-L1399]. The assignment list is byte for byte the insert's, and the
    where clause is appended as ``" WHERE "`` then
    ``FUNCTION TRIM (WS-Where (1:J))`` [:L1392].

    THAT TRIM IS THE ONE EXCEPTION TO N-pointer-offbyone. Every other statement in
    this bridge carries the pointer's extra trailing space; the rewrite trims its
    clause and so does not. Reproduced rather than harmonised - harmonising it
    either way would change a compared artefact.

    Args:
        host: The loaded host-variable group.
        where: The clause built by :func:`_ba090_where`, still carrying its
            trailing space, which this function trims exactly as [:L1392] does.
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


# ---------------------------------------------------------------------------
# The five where clauses, one per bridge paragraph that builds one
# ---------------------------------------------------------------------------


def _key_equals_where(key_value: str) -> _Statement:
    """`` `VA-CODE`="<key>" `` - the clause read-indexed, delete and rewrite share.

    Assembled identically in all three [common/valueMT.cbl:L609-L618 read-indexed,
    :L845-L852 delete, :L980-L989 rewrite]::

        string   "`"                   delimited by size
                 KeyName (KOR-x1)      delimited by space
                 "`"                   delimited by size
                 '="'                  delimited by size
                 VALUEANAL-REC (K:L)   delimited by size
                 '"'                   delimited by size
                         into WS-Where
                           with pointer J

    ``VALUEANAL-REC (K:L)`` is the record sliced with the DECLARED offset and
    length, 1 and 3 [common/valueMT.cbl:L239] - which after N-flatkey is the whole
    of ``WS-Va-Code``. ``delimited by size`` and not ``by space``, so the three
    characters go in as they stand, trailing spaces included; a two-character code
    is matched as ``"AB "`` and not as ``"AB"``. That matters against a ``char(3)``
    column, where MySQL's own comparison ignores trailing spaces but the emitted
    text does not, and it is the reason nothing is trimmed here.
    """
    return _Statement(
        text=_where_with_pointer(_QUOTED_KEY, "=", _quoted_literal(key_value)),
        bound=_where_with_pointer(_QUOTED_KEY, "=", "%s"),
        parameters=(key_value,),
    )


def _ba040_where() -> _Statement:
    """The sequential-read clause [common/valueMT.cbl:L477-L487].

    ``\u0060VA-CODE\u0060 >= "000" ORDER BY \u0060VA-CODE\u0060 ASC``, built once
    per cursor and only ``if Cursor-Not-Active`` [:L465]::

        string   "`" KeyName (KOR-x1) "`"
                 " >= "
                 '"000"'
                 ' ORDER BY '
                 "`" keyname (KOR-x1) "`"
                   ' ASC'

    Three facts, all preserved:

    * N-readnext-lowkey. The low key is a VALUE, not a floor derived from the data,
      so a row whose code sorts below ``"000"`` is silently never returned by a
      sequential walk. There is no diagnostic and no counter.
    * THE ADJACENT COMMENT IS WRONG TWICE. [:L498] reads
      ``*> WS-VA-Code > "000" ORDER BY VALUEANAL-REC ASC`` - the code emits ``>=``,
      not ``>``, and orders by the KEY column, not by the table name. The comment
      is not reproduced because a comment has no behaviour; it is recorded because
      a reader comparing the two will meet it.
    * ``' ASC'`` HERE, ``' ASC  '`` IN START. This clause's literal has no trailing
      space [:L485] while the START clause's has two [:L746]. Both are reproduced
      as written.

    The relation and the low key are read from the shared declaration data rather
    than restated, so this module and the cursor emulator cannot disagree about
    where a sequential walk begins.
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

    NO ``ORDER BY`` and NO ``LIMIT`` - the bridge asks for every row matching the
    key and then fetches one [:L633-L637, :L662]. Against a primary key that is at
    most one row, so the absence is harmless here; it is noted because it is a real
    difference from the two clauses that do order, and because "it happens to be
    unique" is the only thing making it safe.
    """
    return _key_equals_where(key_value)


def _ba060_where(relation: MostRelation, key_value: str) -> _Statement:
    """The START clause [common/valueMT.cbl:L735-L749].

    ``\u0060VA-CODE\u0060 <rel> "<key>" ORDER BY \u0060VA-CODE\u0060 ASC``::

        string   "`" KeyName (KOR-x1) "`"
                 MOST-relation         delimited by space
                 '"' VALUEANAL-REC (K:L) '"'
                 ' ORDER BY '
                 "`" keyname (KOR-x1) "`"
                   ' ASC  '

    Two things are load-bearing:

    * ``MOST-relation delimited by space`` [:L738]. The relation is held in a
      ``pic xxx`` item [:L256] and the padded form is trimmed at its first space,
      so ``">= "`` becomes ``">="`` in the text while ``"=  "`` becomes ``"="``.
      Reproduced with the shared helper.
    * ``ASC`` IS EMITTED FOR EVERY RELATION, INCLUDING ``<`` AND ``<=``
      [:L746]. So a backwards START orders its result set FORWARDS and the first
      row fetched is the LOWEST qualifying key, not the highest - which is not what
      indexed ``START ... KEY <`` means. A row is still returned, so nothing fails
      loudly; the row is simply the wrong end of the range. Reproduced exactly, and
      not corrected: correcting it would change which row a caller reads.

    The literal carries TWO trailing spaces [:L746], where the sequential clause's
    carries none, and the pointer artefact then adds a third.
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

    `` `VA-CODE`<"ZZZ" `` - a strict less-than against the sentinel the paragraph
    has just written into the caller's own record [:L913].

    N-deleteall-zzz: a row keyed exactly ``"ZZZ"``, or anything sorting above it,
    SURVIVES A DELETE-ALL. The verb's name promises otherwise and its own comment
    calls the sentinel "as its the last rec", which it is not - ``"ZZZ"`` is the
    last three-character code only if nothing above it exists. Reproduced, because
    a delete-all that actually deleted everything would leave a different table
    state than the frozen system leaves.
    """
    return _Statement(
        text=_where_with_pointer(_QUOTED_KEY, "<", _quoted_literal(key_value)),
        bound=_where_with_pointer(_QUOTED_KEY, "<", "%s"),
        parameters=(key_value,),
    )


def _ba090_where(key_value: str) -> _Statement:
    """The rewrite clause [common/valueMT.cbl:L980-L989] - the shared key equality.

    Passed on to :func:`bb300_update`, which trims it - the sole escape from
    N-pointer-offbyone.
    """
    return _key_equals_where(key_value)


def _select(where: _Statement) -> _Statement:
    """``SELECT * FROM `VALUEANAL-REC` WHERE <clause>;``.

    Assembled at [common/valueMT.cbl:L495-L499] for the sequential read, [:L633-L637]
    for read-indexed and [:L757-L761] for START - the same four literals in each::

        STRING "SELECT * FROM "
          "`VALUEANAL-REC`"
          " WHERE "
          ws-Where (1:J)
         ";"  X"00" INTO WS-MYSQL-COMMAND

    ``SELECT *`` and not a column list, which is why :func:`bb100_unload_hvs` can
    read the row back by column name and why the fetch depends on the frozen
    table's column set rather than on a list this module maintains.
    """
    return _Statement(
        text=f"SELECT * FROM {_QUOTED_TABLE} WHERE {where.text};",
        bound=f"SELECT * FROM {_QUOTED_TABLE} WHERE {where.bound}",
        parameters=where.parameters,
    )


def _delete(where: _Statement) -> _Statement:
    """``DELETE FROM `VALUEANAL-REC` WHERE <clause>`` - WITH NO SEMICOLON.

    [common/valueMT.cbl:L858-L862] and [:L926-L930]::

        STRING "DELETE FROM "
          "`VALUEANAL-REC`"
          " WHERE "
          WS-Where (1:J)
          X"00" INTO WS-MYSQL-COMMAND

    Both delete paragraphs go straight from the clause to the null terminator,
    where every ``SELECT``, the ``INSERT`` and the ``UPDATE`` all interpose a
    ``";"``. The client library does not require one, so nothing breaks; the
    inconsistency is reproduced because the statement text is a compared artefact.
    """
    return _Statement(
        text=f"DELETE FROM {_QUOTED_TABLE} WHERE {where.text}",
        bound=f"DELETE FROM {_QUOTED_TABLE} WHERE {where.bound}",
        parameters=where.parameters,
    )


# ---------------------------------------------------------------------------
# Module state - the bridge's WORKING-STORAGE, which outlives one CALL
# ---------------------------------------------------------------------------

#: ``Most-Cursor-Set`` and the stored result set [common/valueMT.cbl:L255-L258,
#: :L285]. A COBOL sub-program's working storage survives between ``CALL``s, which
#: is exactly what makes ``Cursor-Active`` mean anything across a sequential walk:
#: the caller performs ``Value-Start`` once and ``Value-Read-Next`` many times, and
#: the cursor has to still be there. Module-level state is therefore the faithful
#: model, not a convenience.
#:
#: Strictly sequential, matching the single-threaded COBOL (R-3): one cursor, one
#: statement at a time, no re-entrancy and no sharing.
_CURSOR_STATES: CursorStateTable = CursorStateTable()

#: The open connection, standing in for the client-library handle the frozen
#: bridge keeps in ``WS-MYSQL-*`` working storage. ``ba020-Process-Open`` sets it,
#: ``ba030-Process-Close`` clears it, and every other paragraph expects it.
_CONNECTION: MySQLConnectionAbstract | None = None

#: The system record most recently seen by ``ba012-Test-WS-Rec-Size-2``, which is
#: the paragraph where the credentials cross from ``System-Record`` into
#: ``File-Access``'s ``RDB-Data`` group [common/acas013.cbl:L633-L643].
#:
#: It is held because the two layers disagree about who knows the credentials. In
#: COBOL the bridge reads them from ``File-Access``, which the handler filled; in
#: Python :func:`acas_posting.dal.connection.mysql_1000_open` is keyed on the
#: system record, because it owns the pinned converter and the transport policy
#: that every handler module must share and that only the system record describes.
#: Keeping the record here preserves the COBOL data flow - the handler still
#: supplies the credentials, still by way of ``ba012`` - without widening the
#: bridge's three-parameter linkage. A caller invoking :func:`value_mt` directly
#: can pass ``system=`` instead.
_SYSTEM_FOR_OPEN: SystemRecord | None = None

#: ``if A = zero`` [common/acas013.cbl:L606] - the record-size test and the
#: credential load run on the FIRST call only, because ``A`` is working storage
#: initialised to zero and left non-zero afterwards.
_RECORD_SIZE_TESTED: bool = False

#: ``77 ws-temp-ed pic 9(10)`` [common/valueMT.cbl:L229], rendered as the ten
#: zero-padded digits a numeric-display item holds.
#:
#: IT IS BRIDGE WORKING STORAGE, NOT CURSOR STATE, and that distinction is the
#: whole of N-filekey-deadstore. Only two paragraphs ever write it - the successful
#: cursor open at [common/valueMT.cbl:L526] and the successful START at [:L791] -
#: while a third, :func:`ba050_process_read_indexed`, READS it at [:L691] without
#: ever writing it. Because working storage survives between ``CALL``s, what that
#: read observes is whatever count one of the other two left behind, from an
#: entirely unrelated earlier call, or ten zeroes if neither has run since the
#: module was loaded. Modelling it at module scope rather than per cursor is what
#: makes the stale value stale.
_WS_TEMP_ED: str = "0" * 10


def cursor_states() -> CursorStateTable:
    """The live cursor state for this table, for inspection and for tests."""
    return _CURSOR_STATES


def reset_module_state() -> None:
    """Discard the cursor, the connection handle and the first-call latch.

    Equivalent to a fresh load of the sub-program: COBOL working storage is
    re-initialised when the module is loaded again, and there is no other way to
    clear ``Most-Cursor-Set`` from outside. Provided so a scenario can start from a
    known state without a process boundary, which the determinism requirement of
    R-6 needs - two runs must be identical, and a cursor surviving from the first
    would make them differ.

    Does NOT close the connection: :func:`ba030_process_close` is the paragraph
    that closes, and calling it from here would invent a close the COBOL never
    performs.
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


# ---------------------------------------------------------------------------
# Status and logging helpers, fitted to their picture widths
# ---------------------------------------------------------------------------


def _set_file_key(logging_data: LoggingData, text: str) -> None:
    """``move <literal> to WS-File-Key`` - ``pic x(64)``.

    [copybooks/wsfnctn.cob:L52]. Truncated at 64 and space-padded to 64, as a
    ``MOVE`` into a fixed alphanumeric item does, so a longer literal loses its
    tail rather than raising.
    """
    logging_data.ws_file_key = _pic_x(text, WS_FILE_KEY_WIDTH)


def _set_log_where(logging_data: LoggingData, text: str) -> None:
    """``move WS-Where (1:J) to WS-Log-Where`` - ``pic x(231)``.

    [copybooks/wsfnctn.cob:L53]. The bridge writes this at every clause site for
    test logging, e.g. [common/valueMT.cbl:L487, :L618, :L750, :L853, :L925]. The
    text arrives already carrying N-pointer-offbyone's extra space, because that is
    what ``(1:J)`` yields.
    """
    logging_data.ws_log_where = _pic_x(text, _WS_LOG_WHERE_WIDTH)


@dataclass(frozen=True, slots=True)
class _DriverResult:
    """What the frozen bridge learns after a statement, and nothing more.

    The bridge issues a statement and then interrogates the client library through
    three foreign calls - ``MySQL_errno``, ``MySQL_sqlstate`` and ``MySQL_error``
    [common/valueMT.cbl:L505-L513 and its many siblings] - plus the stored row
    count ``WS-MYSQL-Count-Rows``. This record is those four answers. Nothing is
    called out of process to obtain them (R-1); the driver's exception carries the
    same information and is translated here.
    """

    #: The rows a ``SELECT`` stored, keyed by column name.
    rows: tuple[Mapping[str, object], ...]
    #: ``WS-MYSQL-Count-Rows`` - stored rows for a select, affected rows otherwise.
    row_count: int
    #: ``WS-MYSQL-Error-Number`` AS TEXT, because the field is alphanumeric and the
    #: bridge compares it as text. ``"0"`` when the statement succeeded.
    errno: str
    #: ``WS-MYSQL-SqlState``.
    sql_state: str
    #: ``WS-MYSQL-Error-Message``.
    message: str

    @property
    def driver_reported_error(self) -> bool:
        """``if WS-MYSQL-Error-Number (1:1) not = "0"``.

        The bridge's own test, at [common/valueMT.cbl:L515, :L577, :L646, :L771,
        :L820, :L871, :L941, :L995] - eight sites, all identical. It inspects ONE
        CHARACTER of a five-character field, so it is really asking "does the
        errno's first digit differ from zero", and a clean statement leaves ``"0"``
        there. Reproduced as the one-character test it is rather than as an
        equality against zero, because that is what decides the branch.
        """
        return _pic_x(self.errno, 5)[:1] != "0"


def _mysql_1210_command(
    connection: MySQLConnectionAbstract,
    statement: _Statement,
    *,
    store_result: bool,
) -> _DriverResult:
    """``PERFORM MYSQL-1210-COMMAND`` and, for a select, ``MYSQL-1220-STORE-RESULT``.

    One statement per call, in the caller's order, through the shared execution
    path [copybooks/mysql-procedures.cpy:L164-L178]. No batching, no statement
    cache and no prefetch: Agent Action Plan section 0.3.3 objects to an
    entity-mapping layer precisely because it "would obscure the exact statement
    ordering that the state diff is sensitive to", and the same reasoning forbids
    reordering here.

    A failure raises in Python where it sets an errno in COBOL, so the exception is
    translated into the four answers the bridge would have interrogated and control
    returns normally - the caller then branches on
    :attr:`_DriverResult.driver_reported_error` exactly as the COBOL branches on
    its one-character test.

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

    Every failure path in this bridge does the same three things before it decides
    a status: ``call "MySQL_errno"``, ``call "MySQL_sqlstate"`` and
    ``move WS-MYSQL-SqlState to SQL-State``, and then, only if the one-character
    test says there was an error, ``call "MySQL_error"`` and the two stores into
    ``SQL-Err`` and ``SQL-Msg`` - for instance [common/valueMT.cbl:L505-L521].

    NOTE THE ASYMMETRY, WHICH IS PRESERVED: ``SQL-State`` is written
    UNCONDITIONALLY, before the test, while ``SQL-Err`` and ``SQL-Msg`` are written
    only inside it. So a statement that returned no rows without failing still
    overwrites the caller's ``SQL-State`` - with the driver's success state - while
    leaving the other two alone.
    """
    logging_data = file_access.logging_data
    # `move WS-MYSQL-SqlState to SQL-State` - unconditional.
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
    # `move WS-MYSQL-Error-Number to SQL-Err` and `... Error-Message to SQL-Msg`.
    # Only these two: the status pair is decided by the CALLING paragraph, each of
    # which writes its own values, so nothing here touches FS-Reply or We-Error.
    logging_data.sql_err = status.sql_err
    logging_data.sql_msg = status.sql_msg


# ---------------------------------------------------------------------------
# The bridge: valueMT, one function per paragraph [common/valueMT.cbl]
# ---------------------------------------------------------------------------


def ba010_initialise(file_access: FileAccess) -> None:
    """``ba010-Initialise.`` [common/valueMT.cbl:L354].

    Clears the diagnostic fields at the top of every bridge call
    [common/valueMT.cbl:L358-L365]::

        move     spaces to WS-MYSQL-Error-Message, WS-MYSQL-Error-Number,
                           WS-Log-Where, WS-File-Key,
                           SQL-Msg, SQL-Err, SQL-State.

    IT DOES NOT CLEAR THE STATUS PAIR, and that is deliberate in the source: the
    two statements that would have are present and COMMENTED OUT
    [common/valueMT.cbl:L356-L357]. So ``We-Error`` and ``Fs-Reply`` arrive from the
    caller and survive until some paragraph writes them - which is the mechanism
    behind two anomalies. N-reread-staleeof reads the caller's incoming ``Fs-Reply``
    after a successful fetch and abandons the row if it happens to be 10, and
    N-start-nostatus lets a fruitless START return with the caller's previous status
    still in place.

    Preserved exactly: clearing the pair here would repair both defects at once,
    and R-4 makes that a failure.
    """
    logging_data = file_access.logging_data
    logging_data.sql_msg = _pic_x("", 512)
    logging_data.sql_err = _pic_x("", 5)
    logging_data.sql_state = _pic_x("", 5)
    _set_file_key(logging_data, "")
    _set_log_where(logging_data, "")
    # We-Error and Fs-Reply are NOT cleared - [common/valueMT.cbl:L356-L357] are
    # commented out in the frozen source. See the note above.


def ba020_process_open(
    file_access: FileAccess,
    *,
    system: SystemRecord,
    dal_common: AcasDalCommonData,
    transport: TransportSecurity | None = None,
) -> OpenOutcome:
    """``ba020-Process-Open.`` [common/valueMT.cbl:L401].

    Six ``STRING`` statements marshal the ``RDB-Data`` block into the client
    library's parameters, each ``delimited by space`` and each terminated with
    ``X"00"`` because the library takes C strings [common/valueMT.cbl:L406-L429]::

        string   DB-Schema      delimited by space
                 X"00"          delimited by size
                                  into WS-MYSQL-BASE-NAME

    and so on for ``DB-Host``, ``DB-UName``, ``DB-UPass``, ``DB-Port`` and
    ``DB-Socket``. Then ``move 1 to ws-No-Paragraph`` [:L431] and
    ``PERFORM MYSQL-1000-OPEN THRU MYSQL-1090-EXIT`` [:L432].

    On failure, ``if fs-reply not = zero / go to ba999-end`` [:L433-L434] - AAP
    section 0.4.2 Class 3, a transfer to the section's exit, so a ``return``. On
    success, ``move "OPEN Value" to WS-File-Key`` [:L441] and
    ``move zero to Most-Cursor-Set`` [:L442]: an open always leaves the cursor
    inactive, so a caller that opens mid-walk loses its position silently.

    The marshalling is DELEGATED rather than repeated.
    :func:`acas_posting.dal.connection.mysql_1000_open` performs the same six-field
    marshalling for all twenty handler modules, and it additionally owns the pinned
    numeric converter that keeps every value arriving as ``Decimal`` or ``int``
    rather than as a binary approximation (R-2) and the transport policy. Repeating
    it here would fork both. The ``delimited by space`` trims are still applied
    below, to the values recorded for traceability, so that what this module says
    it sent is what the COBOL would have sent.

    Args:
        file_access: Status and logging destination; its ``RDB-Data`` group is the
            credential source the COBOL reads.
        system: The system record :func:`ba012_test_ws_rec_size_2` loaded the
            credentials from - see :data:`_SYSTEM_FOR_OPEN` for why it is needed.
        transport: Transport policy, passed straight through.

    Returns:
        The open outcome, so a caller can inspect it; the status is also applied to
        ``file_access``, which is where the COBOL leaves it.
    """
    global _CONNECTION
    logging_data = file_access.logging_data
    # `RDB-Data` [copybooks/wsfnctn.cob:L56-L63] - the six credentials that
    # `ba012-Test-WS-Rec-Size-2` moved in from the system record [:L638-L643].
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
    # [:L431] `move 1 to ws-No-Paragraph.`
    logging_data.ws_no_paragraph = 1
    # [:L432] `PERFORM MYSQL-1000-OPEN THRU MYSQL-1090-EXIT.`
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
    # [:L433-L434] `if fs-reply not = zero / go to ba999-end.` - Class 3.
    if int(outcome.fs_reply) != FsReply.SUCCESS:
        ba999_end(file_access, dal_common=dal_common)
        return outcome
    _CONNECTION = outcome.connection
    # [:L441] `move "OPEN Value" to WS-File-Key`.
    _set_file_key(logging_data, "OPEN Value")
    # [:L442] `move zero to Most-Cursor-Set` - an open discards any position.
    _state().set_cursor_not_active()
    ba999_end(file_access, dal_common=dal_common)
    return outcome


def ba030_process_close(
    file_access: FileAccess, *, dal_common: AcasDalCommonData
) -> None:
    """``ba030-Process-Close.`` [common/valueMT.cbl:L445].

    [common/valueMT.cbl:L449-L457]::

        if       Cursor-Active
                 perform  ba998-Free
        end-if
        move     2 to ws-No-Paragraph
        move    "CLOSE Value" to WS-File-Key
        PERFORM  MYSQL-1980-CLOSE THRU MYSQL-1999-EXIT
        go       to ba999-end.

    The cursor is freed first and only ``if Cursor-Active``, so closing without an
    active cursor frees nothing - which matters because ``ba998-Free`` also writes
    ``ws-No-Paragraph`` and would otherwise overwrite the 2 written here.
    """
    global _CONNECTION
    logging_data = file_access.logging_data
    # [:L449-L451] `if Cursor-Active perform ba998-Free end-if`.
    # A PERFORM of a paragraph runs THAT PARAGRAPH ONLY and returns - it does not
    # continue into the paragraph that physically follows. So this does NOT reach
    # ba999-end, whereas ba050's `go to ba998-Free` does. See :func:`ba998_free`.
    if _state().cursor_active():
        ba998_free(file_access)
    # [:L453-L454].
    logging_data.ws_no_paragraph = 2
    _set_file_key(logging_data, "CLOSE Value")
    # [:L455] `PERFORM MYSQL-1980-CLOSE THRU MYSQL-1999-EXIT.` - both paragraphs of
    # the range, in order, because that is what THRU executes.
    mysql_1980_close(_CONNECTION)
    mysql_1999_exit()
    _CONNECTION = None
    # [:L456] `go to ba999-end.` - AAP section 0.4.2 Class 3.
    ba999_end(file_access, dal_common=dal_common)


def ba040_process_read_next(
    file_access: FileAccess,
    value: WsValueRecord,
    connection: MySQLConnectionAbstract,
    dal_common: AcasDalCommonData,
) -> None:
    """``ba040-Process-Read-Next.`` [common/valueMT.cbl:L460].

    A sequential walk in two halves. THIS paragraph opens the cursor, once, and
    only ``if Cursor-Not-Active`` [:L465]; then it FALLS THROUGH into
    :func:`ba041_reread`, which fetches one row - and every subsequent read-next
    call re-enters here, finds the cursor active, skips the whole block and falls
    through to the fetch again. That fall-through is the loop, and it is
    unconditional: there is no ``go to`` between [:L532] and [:L535].

    Opening the cursor [:L466-L502]: build the clause, log it, ``move 3 to
    ws-No-Paragraph``, select, store the result, and ``move "000" to WS-File-Key``.

    No rows [:L505-L523]: capture the driver's answers, then ``move 10 to fs-reply``
    and ``move 10 to WE-Error`` and ``move "No Data" to WS-File-Key``, then
    ``go to ba999-End`` - AAP section 0.4.2 Class 3.

    Rows [:L525-L532]: ``set Cursor-Active to true``, build the count into the log
    key, and ``perform ba999-End`` - a PERFORM, not a jump, whose comment is simply
    "log it" [:L531]. So a successful cursor open writes a log record of its own and
    THEN the fetch writes a second one. Preserved: two records, not one.

    N-readnext-lowkey lives in the clause this paragraph builds - see
    :func:`_ba040_where`.
    """
    global _WS_TEMP_ED
    logging_data = file_access.logging_data
    state = _state()
    # [:L465] `if Cursor-Not-Active` - the whole block is the cursor open.
    if state.cursor_not_active():
        where = _ba040_where()
        # [:L487] `move ws-Where (1:J) to WS-Log-Where` - for test logging.
        _set_log_where(logging_data, where.text)
        # [:L488] `move 3 to ws-No-Paragraph`.
        logging_data.ws_no_paragraph = 3
        statement = _select(where)
        result = _mysql_1210_command(connection, statement, store_result=True)
        state.store_result(result.rows)
        # [:L503] `move "000" to WS-File-Key` - the low key, before the row test.
        _set_file_key(logging_data, SEQUENTIAL_READ_LOW_KEY)
        # [:L505-L523] `if WS-MYSQL-Count-Rows = zero`.
        if result.row_count == 0:
            _capture_driver_error(file_access, result, statement)
            # [:L520-L522] 10 to both, unconditionally - not only on a real error.
            # So an empty table and a broken statement are the same answer here.
            file_access.fs_reply = int(FsReply.END_OF_FILE)  # [:L520]
            # [:L521] `move 10 to WE-Error`. TEN IS NOT A We-Error VALUE: the
            # handler's own vocabulary [common/acas013.cbl:L168-L191] runs
            # 0, 901, 910, 911 and 988..999, and 10 is an FS-Reply value being
            # reused in the other field. The source says as much where it repeats
            # the trick - `*> EOF equivilent !!` [:L578]. Written as the literal it
            # is, because WeError has no member to name it and inventing one would
            # imply the vocabulary contains it.
            file_access.we_error = 10
            _set_file_key(logging_data, "No Data")
            state.set_cursor_not_active()
            ba999_end(file_access, dal_common=dal_common)
            return
        # [:L525] `set Cursor-Active to true`.
        state.set_cursor_active()
        # [:L526] `move WS-MYSQL-Count-Rows to WS-Temp-Ed` - one of only two writes
        # to that field anywhere in the bridge; see :data:`_WS_TEMP_ED`.
        _WS_TEMP_ED = f"{result.row_count:010d}"
        # [:L527-L531] `string "> 0 got cnt=" WS-Temp-ED " recs" into WS-File-Key`.
        # WS-Temp-ED is `pic 9(10)` [:L229] and is NOT `delimited by space`, so all
        # ten zero-padded digits land in the key.
        _set_file_key(logging_data, f"> 0 got cnt={_WS_TEMP_ED} recs")
        # [:L531] `perform ba999-End` - a PERFORM, so the walk continues into the
        # fetch below and this paragraph's log record is written first.
        ba999_end(file_access, dal_common=dal_common)
    # [:L535] Unconditional fall-through into ba041-Reread. AAP section 0.4.2 has
    # no class for a fall-through because it is not a GO TO at all; it is the
    # absence of one, and reproducing it means an unconditional call here.
    ba041_reread(file_access, value, dal_common=dal_common)


def ba041_reread(
    file_access: FileAccess,
    value: WsValueRecord,
    *,
    dal_common: AcasDalCommonData,
) -> None:
    """``ba041-Reread.`` [common/valueMT.cbl:L535].

    Fetches one row from the open cursor into the host variables
    [common/valueMT.cbl:L545-L560] and then decides, in this order:

    1. ``if return-code = -1`` [:L565] - no more data. ``move 10 to fs-Reply
       WE-Error``, ``move "EOF" to WS-File-Key``, free the cursor, exit.
    2. ``if WS-MYSQL-Count-Rows = zero`` [:L572] - capture the driver's answers,
       and ONLY IF it reported an error [:L576] write ``10``/``10``, the message
       fields, ``initialize VALUEANAL-REC with filler`` [:L582] and
       ``"EOF2"`` [:L583]. Then, OUTSIDE that inner test, free the cursor and exit
       [:L585-L586]. So a zero count with a clean errno writes NO STATUS AT ALL and
       still returns - the caller keeps whatever it arrived with.
    3. ``if fs-reply = 10`` [:L589] - N-reread-staleeof. THE ROW HAS ALREADY BEEN
       FETCHED SUCCESSFULLY at this point, and this tests the value the CALLER
       brought in, because ``ba010-Initialise`` deliberately does not clear it. A
       caller that arrives with an end-of-file status therefore loses a row that
       was there: the cursor is freed, ``"EOF3"`` is logged, and the fetched row is
       discarded unread. Reproduced exactly.
    4. Otherwise [:L595-L597]: ``perform bb100-UnloadHVs``, then
       ``move HV-VA-Code to WS-File-Key``, then ``move zero to fs-reply WE-Error``.

    ``initialize VALUEANAL-REC with filler`` at [:L582] is the ``WITH FILLER`` half
    of N-initialize; :func:`bb100_unload_hvs` carries the plain half.

    THE FETCH ITSELF is ``call "MySQL_fetch_record"`` with all ten host variables
    [:L546-L558], and NO TRIM IS APPLIED ON THIS PATH. All twenty-one
    ``FUNCTION TRIM`` sites in the bridge are on the insert and update paths; the
    fetch fills fixed-width items directly, so a ``char(3)`` code comes back
    space-padded to three and a ``char(24)`` description to twenty-four. Trim on the
    way in, pad on the way out - reproduced by :func:`_pic_x` in the unload.
    """
    logging_data = file_access.logging_data
    state = _state()
    # [:L537] `move spaces to WS-Log-Where` and [:L538] `move 4 to ws-No-Paragraph`.
    _set_log_where(logging_data, "")
    logging_data.ws_no_paragraph = 4
    # [:L545-L560] the fetch. `return-code = -1` is "no more rows".
    row = state.fetch_record()
    # 1. [:L565-L570].
    if row is None:
        # [:L566] `move 10 to fs-Reply WE-Error` - ONE statement writing BOTH
        # fields, so the We-Error 10 here is not even a separate decision. See the
        # note in :func:`ba040_process_read_next` on why 10 is written as a literal.
        file_access.fs_reply = int(FsReply.END_OF_FILE)
        file_access.we_error = 10
        _set_file_key(logging_data, "EOF")
        state.set_cursor_not_active()
        ba999_end(file_access, dal_common=dal_common)
        return
    # 2. [:L572-L587]. The count is the STORED count, so it can only be zero here
    # if the cursor was opened empty - which case 1 already caught. Reproduced
    # anyway, because the frozen source tests it and a caller reading the code
    # would expect the branch to exist.
    if state.count_rows == 0:
        result = _DriverResult((), 0, "0", "00000", "")
        _capture_driver_error(file_access, result, _select(_ba040_where()))
        if result.driver_reported_error:  # [:L576] the one-character test
            # [:L578] `move 10 to fs-reply  *> EOF equivilent !!` and [:L579]
            # `move 10 to WE-Error` - two statements here, one at [:L566].
            file_access.fs_reply = int(FsReply.END_OF_FILE)
            file_access.we_error = 10
            # [:L582] `initialize VALUEANAL-REC with filler` - N-initialize, the
            # WITH FILLER half. This record declares no filler, so here the two
            # forms coincide; the distinction is the bridge's, not this module's.
            bb100_unload_hvs(TdValueanalRec(), value)
            _set_file_key(logging_data, "EOF2")
        # [:L585-L586] OUTSIDE the inner test - so a clean zero count writes
        # nothing and still returns.
        state.set_cursor_not_active()
        ba999_end(file_access, dal_common=dal_common)
        return
    # 3. [:L589-L593] N-reread-staleeof. The caller's incoming FS-Reply, tested
    # AFTER a successful fetch, discards a row that was actually retrieved.
    if int(file_access.fs_reply) == FsReply.END_OF_FILE:
        state.set_cursor_not_active()
        _set_file_key(logging_data, "EOF3")
        ba999_end(file_access, dal_common=dal_common)
        return
    # 4. [:L595-L597].
    host = _row_to_host(row)
    bb100_unload_hvs(host, value)
    _set_file_key(logging_data, host.hv_va_code)
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    ba999_end(file_access, dal_common=dal_common)


def _row_to_host(row: Mapping[str, object]) -> TdValueanalRec:
    """Fill the host-variable group from a fetched row.

    Stands in for ``call "MySQL_fetch_record" USING WS-MYSQL-RESULT`` and its ten
    host-variable arguments [common/valueMT.cbl:L546-L558]. The C interface writes
    each column into its declared item, so each value is fitted to that item's
    picture here - a ``char(24)`` description into ``X(24)``, a ``decimal(10,2)``
    into ``9(08)V9(02)``.

    The columns are read by NAME, from :data:`COLUMNS`, in ordinal order, which is
    the order ``SELECT *`` returns them and the order the fetch call lists them.
    Reading by name rather than by position means a row can be handed in by any
    caller - including a test - without depending on tuple order.

    Every value is a ``Decimal``, an ``int`` or a ``str``. The driver's converter is
    pinned by :mod:`acas_posting.dal.connection` so a ``decimal(10,2)`` column
    arrives as a ``Decimal``; the conversions below are the picture fitting, not a
    numeric type change (R-2). The exactness of each numeric column is asserted here
    as well, rather than assumed from that pinning, because this is the boundary at
    which a value crosses from the driver into the migrated code - and an inexact
    value quantized at this point would be indistinguishable afterwards from an
    exact one.

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

    A single-row read by primary key. Builds ``=``-form clause [:L611-L619], logs
    it [:L620], ``move 5 to ws-No-Paragraph`` [:L624], selects and stores
    [:L630-L638], then:

    * ``if WS-MYSQL-Count-Rows = zero`` [:L641] - ``move 23 to fs-Reply`` [:L642]
      with the comment "could also be 21 or 14", ``move zero to WE-Error`` [:L643],
      ``go to ba998-Free`` [:L644].
    * ``move 6 to ws-No-Paragraph`` [:L646], fetch [:L652-L666].
    * ``if WS-MYSQL-Count-Rows not > zero`` [:L668] - a SECOND row-count test, on
      the same unchanged count the first test already passed. Unreachable, and both
      of its arms are written out in full: the error arm gives ``23``/``990``
      [:L673-L674] and the clean arm ``23``/``989`` [:L681-L682]. Reproduced
      because R-5 requires every paragraph's structure, and because the two
      ``WeError`` values are the only place ``989`` is ever written.
    * Success [:L689-L693]: unload, then the two file-key writes and
      ``move zero to FS-Reply WE-Error``, then ``go to ba998-Free``.

    ⭐ A MISSING ROW REPORTS 23 WITH ``We-Error`` ZEROED. The 23 is
    :attr:`~acas_posting.dal.status.FsReply.KEY_NOT_FOUND` and is apt; the ``move
    zero to WE-Error`` beside it [:L643] is what matters, because it means a caller
    testing ``We-Error`` alone cannot distinguish a missing row from a successful
    read - only ``FS-Reply`` carries the difference. The source is visibly unsure
    of the value: its own comment reads ``*> could also be 21 or 14``.

    This is why :func:`acas_posting.dal.cursor_state.read_indexed` CANNOT be
    borrowed here. That helper returns 21, the shape ``glpostingMT`` uses, and 21
    is a different answer with a different ``We-Error``. Each bridge's status
    protocol is its own, and R-4 makes the difference the specification rather than
    an inconsistency to smooth over, so only the key-extraction and cursor
    primitives of that module are used.

    ⭐ N-filekey-deadstore is at [:L690-L691]. ``move HV-VA-Code to WS-File-Key``
    is immediately overwritten by ``move ws-temp-ed to WS-File-Key``, and THIS
    PARAGRAPH NEVER SETS ``ws-temp-ed`` - only :func:`ba040_process_read_next` and
    :func:`ba060_process_start` do. So the log line for a successful indexed read
    carries a stale row count left behind by whichever of those ran last, or ten
    zeroes if neither has. Both stores are reproduced, in order.
    """
    logging_data = file_access.logging_data
    state = _state()
    key_value = _flat_key_of(value)
    where = _ba050_where(key_value)
    # [:L620] `move WS-Where (1:J) to WS-Log-Where.`
    _set_log_where(logging_data, where.text)
    # [:L624] `move 5 to ws-No-Paragraph.`
    logging_data.ws_no_paragraph = 5
    statement = _select(where)
    result = _mysql_1210_command(connection, statement, store_result=True)
    state.store_result(result.rows)
    # [:L641-L645] the first row-count test.
    if result.row_count == 0:
        # [:L642] 23, with the source's own "could also be 21 or 14" beside it, and
        # [:L643] zero to WE-Error - so nothing distinguishes this from success
        # except FS-Reply. Preserved.
        file_access.fs_reply = int(FsReply.KEY_NOT_FOUND)  # [:L642] 23
        file_access.we_error = int(WeError.SUCCESS)
        # [:L644] `go to ba998-Free` - AAP section 0.4.2 Class 4: a jump into a
        # sibling that does work and then falls through, so the call is followed by
        # the fall-through target explicitly and then a return.
        ba998_free(file_access)
        ba999_end(file_access, dal_common=dal_common)
        return
    # [:L646] `move 6 to ws-No-Paragraph.`
    logging_data.ws_no_paragraph = 6
    # [:L652-L666] the fetch.
    row = state.fetch_record()
    # [:L668-L688] the second, unreachable row-count test. The count cannot have
    # changed since [:L641], so `not > zero` cannot be true. Both arms preserved.
    if state.count_rows <= 0:  # pragma: no cover - unreachable in the frozen source
        _capture_driver_error(file_access, result, statement)
        if result.driver_reported_error:
            file_access.fs_reply = int(FsReply.KEY_NOT_FOUND)  # [:L673] 23
            file_access.we_error = int(WeError.UNKNOWN_UNEXPECTED)  # [:L674] 990
            _set_file_key(logging_data, "")  # [:L678]
        else:
            file_access.fs_reply = int(FsReply.KEY_NOT_FOUND)  # [:L681] 23
            file_access.we_error = int(WeError.READ_INDEXED_UNEXPECTED)  # [:L682] 989
            # [:L683] `move zero to SQL-Err` into `pic x(5)`: an alphanumeric
            # receiving item takes the figurative constant as the character "0",
            # left-justified and space-padded - "0" then four spaces, not "00000".
            logging_data.sql_err = _pic_x("0", 5)
            logging_data.sql_msg = _pic_x("", 512)  # [:L684]
            _set_file_key(logging_data, "")  # [:L685]
        ba998_free(file_access)
        ba999_end(file_access, dal_common=dal_common)
        return
    # [:L689] `perform bb100-UnloadHVs`.
    host = _row_to_host(row) if row is not None else TdValueanalRec()
    bb100_unload_hvs(host, value)
    # [:L690] then [:L691] - N-filekey-deadstore. The first store is overwritten by
    # the second, which reads a field this paragraph never wrote.
    _set_file_key(logging_data, host.hv_va_code)
    _set_file_key(logging_data, _WS_TEMP_ED)
    # [:L692] `move zero to FS-Reply WE-Error.`
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    # [:L693] `go to ba998-Free.` - Class 4, as above.
    ba998_free(file_access)
    ba999_end(file_access, dal_common=dal_common)


def ba060_process_start(
    file_access: FileAccess,
    value: WsValueRecord,
    connection: MySQLConnectionAbstract,
    dal_common: AcasDalCommonData,
) -> None:
    """``ba060-Process-Start.`` [common/valueMT.cbl:L695].

    Positions the cursor for a subsequent sequential walk. In order:

    1. ``if access-type < 5 or > 8`` [:L699] - the bridge-level guard, with the
       source's own note "not using not < or not >". ``move 99 to FS-Reply``
       [:L700] and ``move 997 to WE-Error`` [:L701], then ``go to ba999-end``
       [:L702]. AAP section 0.4.2 Class 3.
    2. ``if Cursor-Active perform ba998-Free.`` [:L709-L710] - a PERFORM, so it
       frees and returns here rather than falling into the exit.
    3. ``evaluate Access-Type`` [:L721-L732] mapping 5..9 onto ``MOST-Relation``.
       ⭐ ``when 9`` [:L730-L731] IS DEAD: step 1 already rejected 9, and the
       source says so beside it - "not currently used in ACAS". Reproduced, and
       recorded as N-deadcode.
       ⭐ THERE IS NO ``when other`` [:L732 closes the evaluate directly], so an
       unmatched value would leave ``MOST-Relation`` as the spaces written at
       [:L719]. Unreachable behind step 1, and preserved: the module does not add
       the ``when other`` the source declines to write.
    4. The clause [:L735-L749], with ``' ASC  '`` [:L746] - TWO trailing spaces
       where :func:`_ba040_where` has none. ``ASC`` is emitted for EVERY relation,
       including ``<`` and ``<=``, so a backwards START orders the result set
       forwards. See :func:`_ba060_where`.
    5. ``move VALUEANAL-REC (K:L) to WS-File-Key`` [:L751].
    6. ``move 8 to ws-No-Paragraph`` [:L756], select and store [:L762-L770].
    7. ``if WS-MYSQL-Count-Rows not zero / set Cursor-Active to true`` [:L773-L775].
    8. ``if WS-MYSQL-Count-Rows = zero`` [:L777]: capture, and ONLY IF the driver
       reported an error [:L781] write ``21``/``zero`` [:L785-L786] and
       ``go to ba999-End`` [:L787].
       ⭐ N-start-nostatus: a START THAT MATCHES NOTHING WITHOUT A DRIVER ERROR -
       the ordinary "positioned past the end" case - FALLS OUT OF THE ``if`` HAVING
       WRITTEN NO STATUS AT ALL, reaches [:L800] and returns with whatever
       ``FS-Reply`` and ``We-Error`` the caller brought in. ``ba010-Initialise``
       deliberately does not clear them [:L356-L357], so a caller that arrives
       clean reads success from a START that found nothing. Reproduced exactly:
       nothing is written on that path.
       ``else`` [:L789-L798] - rows found: ``move zero to FS-Reply WE-Error`` and
       the count string into the file key.
    9. ``go to ba999-end.`` [:L800].

    [:L804] ``go to ba041-Reread.`` sits after that unconditional jump and is
    therefore unreachable - N-deadcode's second site. It is not translated, and the
    omission is recorded rather than silent (R-5).
    """
    global _WS_TEMP_ED
    logging_data = file_access.logging_data
    state = _state()
    access_type = int(file_access.access_type)
    # 1. [:L699-L703]. The predicate is `< 5 or > 8`; `start_access_type_is_valid`
    # expresses exactly that inclusive range (see `dal.status`, whose
    # START_ACCESS_TYPE_RANGE holds the frozen bounds the predicate reads).
    if not start_access_type_is_valid(access_type):
        file_access.fs_reply = int(FsReply.ERROR)  # [:L700] 99
        file_access.we_error = int(WeError.ACCESS_TYPE_WRONG)  # [:L701] 997
        ba999_end(file_access, dal_common=dal_common)
        return
    # 2. [:L709-L710] a PERFORM, not a jump - no fall-through.
    if state.cursor_active():
        ba998_free(file_access)
    # 3. [:L719-L732]. ACCESS_TYPE_TO_RELATION carries the same five spellings,
    # each already padded to the three characters of `MOST-Relation pic xxx`
    # [:L256], and there is no default entry because the source writes no
    # `when other`.
    relation = MostRelation(
        ACCESS_TYPE_TO_RELATION.get(AccessType(access_type), "   ")
    )
    state.most_relation = relation.padded
    key_value = _flat_key_of(value)
    # 4. [:L735-L749].
    where = _ba060_where(relation, key_value)
    _set_log_where(logging_data, where.text)  # [:L750]
    # 5. [:L751] - overwritten on the success path at [:L797], preserved in order.
    _set_file_key(logging_data, key_value)
    # 6. [:L756].
    logging_data.ws_no_paragraph = 8
    statement = _select(where)
    result = _mysql_1210_command(connection, statement, store_result=True)
    state.store_result(result.rows)
    state.position_at(key_value)
    # 7. [:L773-L775].
    if result.row_count != 0:
        state.set_cursor_active()
    # 8. [:L777-L799].
    if result.row_count == 0:
        _capture_driver_error(file_access, result, statement)
        if result.driver_reported_error:  # [:L781]
            file_access.fs_reply = int(FsReply.INVALID_KEY_ON_START)  # [:L785] 21
            file_access.we_error = int(WeError.SUCCESS)  # [:L786] zero
            ba999_end(file_access, dal_common=dal_common)
            return
        # N-start-nostatus - no status write on this path. Deliberate: see above.
    else:
        file_access.fs_reply = int(FsReply.SUCCESS)  # [:L790]
        file_access.we_error = int(WeError.SUCCESS)
        _WS_TEMP_ED = f"{result.row_count:010d}"  # [:L791]
        # [:L792-L798] `MOST-relation` is NOT `delimited by space` here, unlike in
        # the clause at [:L738], so all three characters including the padding land
        # in the key: ">= " and not ">=".
        _set_file_key(
            logging_data,
            f"{relation.padded}{key_value} got ={_WS_TEMP_ED} recs",
        )
    # 9. [:L800].
    ba999_end(file_access, dal_common=dal_common)


def ba070_process_write(
    file_access: FileAccess,
    value: WsValueRecord,
    connection: MySQLConnectionAbstract,
    dal_common: AcasDalCommonData,
) -> None:
    """``ba070-Process-Write.`` [common/valueMT.cbl:L809].

    [:L810-L816] in order: ``perform bb000-HV-Load`` - "move VALUEANAL-REC fields
    to HV fields", which is where the three money fields lose their sign;
    ``move WS-VA-Code to WS-File-Key``; ``move zero to FS-Reply WE-Error
    SQL-State``; ``move spaces to SQL-Msg``; ``move zero to SQL-Err``;
    ``move 10 to ws-No-Paragraph``; ``perform bb200-Insert``.

    ⭐ THE STATUS IS CLEARED TO SUCCESS BEFORE THE INSERT IS ISSUED [:L812], so
    every path out of this paragraph that does not explicitly write a failure
    reports success - including one where the insert affected no rows but the
    driver reported nothing.

    ``if WS-MYSQL-COUNT-ROWS not = 1`` [:L817] and then, only inside the
    one-character errno test [:L821], the duplicate-key discrimination
    [:L825-L831]::

        if    SQL-Err (1:4) = "1062"
                         or = "1022"   *> Dup key (rec already present)
            or Sql-State = "23000"  *> Dup key (rec already present)
              move 22 to fs-reply
        else
              move 99 to fs-reply
        end-if

    ⭐ ``We-Error`` IS NEVER WRITTEN ON THE FAILURE PATH. It stays at the zero from
    [:L812], so a failed write reports ``FS-Reply`` 99 with ``We-Error`` 0 - the
    handler's ``994``/``995`` pattern is absent here. Preserved.

    ⭐ The duplicate test reads ``SQL-Err (1:4)``, four characters of a
    five-character field, which is why
    :func:`acas_posting.dal.status.is_duplicate_key_bridge_level` compares on the
    text rather than on a number. ``1062`` and ``1022`` both mean a duplicate key;
    the ``23000`` state is an independent third way of saying it.
    """
    logging_data = file_access.logging_data
    # [:L810].
    host = bb000_hv_load(value)
    # [:L811].
    _set_file_key(logging_data, _flat_key_of(value))
    # [:L812-L814].
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    logging_data.sql_state = _pic_x("0", 5)
    logging_data.sql_msg = _pic_x("", 512)
    logging_data.sql_err = _pic_x("0", 5)
    # [:L815].
    logging_data.ws_no_paragraph = 10
    # [:L816] `perform bb200-Insert.`
    statement = bb200_insert(host)
    result = _mysql_1210_command(connection, statement, store_result=False)
    # [:L817].
    if result.row_count != 1:
        _capture_driver_error(file_access, result, statement)
        if result.driver_reported_error:  # [:L821]
            if is_duplicate_key_bridge_level(
                logging_data.sql_err, logging_data.sql_state
            ):
                file_access.fs_reply = int(FsReply.DUPLICATE_KEY)  # [:L828] 22
            else:
                file_access.fs_reply = int(FsReply.ERROR)  # [:L830] 99
            # No We-Error write: see the note above.
    # [:L834] `go to ba999-End.` - Class 3.
    ba999_end(file_access, dal_common=dal_common)


def ba080_process_delete(
    file_access: FileAccess,
    value: WsValueRecord,
    connection: MySQLConnectionAbstract,
    dal_common: AcasDalCommonData,
) -> None:
    """``ba080-Process-Delete.`` [common/valueMT.cbl:L836].

    Clause [:L844-L852], file key [:L853], log where [:L854],
    ``move 13 to ws-No-Paragraph`` [:L858], then the delete [:L864-L870].

    ⭐ THE DELETE CARRIES NO SEMICOLON. [:L869] terminates with ``X"00"`` alone,
    where every ``SELECT``, ``INSERT`` and ``UPDATE`` in this bridge appends
    ``";"`` first [:L499, :L635, :L767, :L1245, :L1398]. Reproduced by
    :func:`_delete`, which is why its text ends in the pointer artefact's space
    rather than a semicolon.

    ``if WS-MYSQL-COUNT-ROWS not = 1`` [:L872]; inside the errno test,
    ``99``/``995`` [:L880-L881]; then ``go to ba999-End`` [:L883] - WHICH IS
    OUTSIDE the errno test, so a delete that affected some other number of rows
    without a driver error also returns here, having written nothing. The
    ``else`` [:L884-L886] clears the two message fields, and [:L888] then writes
    ``zero to FS-Reply WE-Error`` - reached ONLY from the else, because the if-arm
    jumped past it.
    """
    logging_data = file_access.logging_data
    key_value = _flat_key_of(value)
    where = _ba080_where(key_value)
    _set_file_key(logging_data, key_value)  # [:L853]
    _set_log_where(logging_data, where.text)  # [:L854]
    logging_data.ws_no_paragraph = 13  # [:L858]
    statement = _delete(where)
    result = _mysql_1210_command(connection, statement, store_result=False)
    # [:L872-L887].
    if result.row_count != 1:
        _capture_driver_error(file_access, result, statement)
        if result.driver_reported_error:  # [:L876]
            file_access.fs_reply = int(FsReply.ERROR)  # [:L880] 99
            file_access.we_error = int(WeError.DELETE_SQLSTATE_NOT_00000)  # [:L881] 995
        # [:L883] `go to ba999-End` - outside the errno test, and it SKIPS the
        # `move zero to FS-Reply WE-Error` at [:L888]. Class 3.
        ba999_end(file_access, dal_common=dal_common)
        return
    # [:L885-L886] the else arm.
    logging_data.sql_msg = _pic_x("", 512)
    logging_data.sql_err = _pic_x("0", 5)
    # [:L888] reached only from the else.
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    # [:L889].
    ba999_end(file_access, dal_common=dal_common)


def ba085_process_delete_all(
    file_access: FileAccess,
    value: WsValueRecord,
    connection: MySQLConnectionAbstract,
    dal_common: AcasDalCommonData,
) -> None:
    """``ba085-Process-Delete-All.`` [common/valueMT.cbl:L891].

    The source's own header calls it ``*> THIS IS NON STANDARD`` [:L891], and it is:
    it is the only verb that mutates the caller's record before doing its work.

    ⭐ N-deleteall-zzz. [:L913] ``move "ZZZ" to WS-VA-Code.  *> as its the last rec``
    OVERWRITES THE CALLER'S KEY FIELD IN PLACE, and the clause is then built from
    that mutated record with ``<`` [:L921-L929], giving ``` `VA-CODE`<"ZZZ" ```. Two
    consequences, both reproduced:

    * A ROW KEYED ``"ZZZ"`` OR HIGHER SURVIVES A DELETE-ALL. The comparison is
      strictly less-than against a literal that is not the maximum of a
      three-character column - ``"ZZ~"`` and ``"zzz"`` both sort above it under the
      table's ``utf8mb3_general_ci`` collation [mysql/ACASDB.sql:L1430].
    * THE CALLER'S RECORD IS LEFT HOLDING ``"ZZZ"``. The record is a linkage
      parameter, passed by reference, so the mutation is visible to the caller
      after the call returns. That is why :data:`_flat_key_of` is not used to
      snapshot the key first: the write must land on the caller's object.

    Guard [:L953]: ``if WS-MYSQL-COUNT-ROWS = zero``, with the source's own
    ``*> Diferent from modal`` [sic] beside it - every sibling verb tests
    ``not = 1``. Deleting exactly one row is therefore a success here and so is
    deleting nine hundred; deleting none is the failure, which is reasonable for
    this verb and inconsistent with the rest of the bridge.
    """
    logging_data = file_access.logging_data
    # [:L913] the in-place mutation of the caller's record. It writes the whole
    # three characters of `WS-VA-Code`, which the copybook declares as the group
    # `va-code` [copybooks/wsval.cob:L10-L14] - so the three sub-fields the bridge
    # flattened away (N-flatkey) receive "Z", "Z" and "Z" respectively.
    value.va_code.va_system = "Z"
    value.va_code.va_group.va_first = "Z"
    value.va_code.va_group.va_second = "Z"
    key_value = _flat_key_of(value)
    where = _ba085_where(key_value)  # [:L921-L929]
    # [:L930-L934] `move spaces to WS-File-Key` then the string into it.
    _set_file_key(logging_data, f"Deleting back from {key_value}")
    _set_log_where(logging_data, where.text)  # [:L935]
    logging_data.ws_no_paragraph = 15  # [:L939]
    statement = _delete(where)
    result = _mysql_1210_command(connection, statement, store_result=False)
    # [:L953-L968].
    if result.row_count == 0:
        _capture_driver_error(file_access, result, statement)
        if result.driver_reported_error:  # [:L957]
            file_access.fs_reply = int(FsReply.ERROR)  # [:L961] 99
            file_access.we_error = int(WeError.DELETE_SQLSTATE_NOT_00000)  # [:L962] 995
        # [:L964] outside the errno test, skipping [:L969]. Class 3.
        ba999_end(file_access, dal_common=dal_common)
        return
    logging_data.sql_msg = _pic_x("", 512)  # [:L966]
    logging_data.sql_err = _pic_x("0", 5)  # [:L967]
    file_access.fs_reply = int(FsReply.SUCCESS)  # [:L969]
    file_access.we_error = int(WeError.SUCCESS)
    ba999_end(file_access, dal_common=dal_common)  # [:L970]


def ba090_process_rewrite(
    file_access: FileAccess,
    value: WsValueRecord,
    connection: MySQLConnectionAbstract,
    dal_common: AcasDalCommonData,
) -> None:
    """``ba090-Process-Rewrite.`` [common/valueMT.cbl:L972].

    [:L974-L993]: ``perform bb000-HV-Load`` - so the sign loss happens on a rewrite
    exactly as on a write; ``move 17 to ws-No-Paragraph``; ``move WS-VA-Code to
    WS-File-Key``; the ``=``-form clause; the log where; ``perform bb300-Update``.

    ⭐ N-updates-key. :func:`bb300_update` assigns ALL TEN COLUMNS INCLUDING
    ``VA-CODE``, and the ``WHERE`` then matches on that same key - so the primary
    key is rewritten to the value it already holds. Harmless against this schema
    and preserved: removing the assignment would change the statement text, which
    is observable in ``WS-Log-Where``'s neighbour fields and in any statement-level
    comparison against the oracle.

    ``if WS-MYSQL-COUNT-ROWS not = 1`` [:L999]; inside the errno test,
    ``99``/``994`` [:L1007-L1008] - the ``994`` that exists nowhere else in this
    bridge; then ``go to ba999-end`` [:L1010], again outside the errno test.
    Success [:L1012-L1014] clears ``FS-Reply``, ``WE-Error``, ``SQL-State``,
    ``SQL-Err`` and ``SQL-Msg``.

    ⚠ A rewrite whose ``WHERE`` matched a row but changed nothing reports
    ``WS-MYSQL-COUNT-ROWS`` of zero under the driver's default affected-rows
    accounting, and therefore takes the failure branch with no driver error and no
    status write - leaving the caller's incoming status intact. That is the frozen
    behaviour of a no-change rewrite and it is not corrected here; the exact count
    the C interface reports is one of the things only the compiled oracle can
    settle (Agent Action Plan section 0.6.8).
    """
    logging_data = file_access.logging_data
    host = bb000_hv_load(value)  # [:L974]
    logging_data.ws_no_paragraph = 17  # [:L975]
    key_value = _flat_key_of(value)
    _set_file_key(logging_data, key_value)  # [:L976]
    where = _ba090_where(key_value)  # [:L983-L991]
    _set_log_where(logging_data, where.text)  # [:L992]
    # [:L993] `perform bb300-Update.`
    statement = bb300_update(host, where)
    result = _mysql_1210_command(connection, statement, store_result=False)
    # [:L999-L1011].
    if result.row_count != 1:
        _capture_driver_error(file_access, result, statement)
        if result.driver_reported_error:  # [:L1003]
            file_access.fs_reply = int(FsReply.ERROR)  # [:L1007] 99
            file_access.we_error = int(WeError.REWRITE_SQLSTATE_NOT_00000)  # [:L1008] 994
        # [:L1010] outside the errno test. Class 3.
        ba999_end(file_access, dal_common=dal_common)
        return
    # [:L1012-L1014].
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    logging_data.sql_state = _pic_x("0", 5)
    logging_data.sql_err = _pic_x("0", 5)
    logging_data.sql_msg = _pic_x("", 512)
    ba999_end(file_access, dal_common=dal_common)  # [:L1015]


def ba100_bad_function(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``ba100-Bad-Function.`` [common/valueMT.cbl:L1017].

    [:L1021-L1023]::

        move     990 to WE-Error.
        move     99 to Fs-Reply.
        go       to ba999-end.

    Reached from the bridge's ``when other`` for a ``File-Function`` outside 1..9
    and 6. It is NOT the handler's :func:`aa100_bad_function`, which writes
    ``999``/``99`` [common/acas013.cbl:L571-L572] - the two layers disagree about
    what an unrecognised function is called, and only the layer the caller reached
    decides. Both are reproduced separately, which is N-badfunc.
    """
    file_access.we_error = int(WeError.UNKNOWN_UNEXPECTED)  # [:L1021] 990
    file_access.fs_reply = int(FsReply.ERROR)  # [:L1022] 99
    ba999_end(file_access, dal_common=dal_common)  # [:L1023]


def ba998_free(file_access: FileAccess) -> None:
    """``ba998-Free.`` [common/valueMT.cbl:L1029].

    [:L1030-L1039]::

        move     20 to ws-No-Paragraph.
        ...
              MOVE TP-VALUEANAL-REC TO WS-MYSQL-RESULT
              CALL "MySQL_free_result" USING WS-MYSQL-RESULT end-call
        ...
        set      Cursor-Not-Active to true.

    ⭐ IT DOES NOT END WITH A ``GO TO``, so control falls through into
    :func:`ba999_end` - but only when control ARRIVED here by ``go to``, as it does
    from :func:`ba050_process_read_indexed` [:L644, :L679, :L686, :L693]. Where it
    arrived by ``perform`` - from :func:`ba030_process_close` [:L450] and
    :func:`ba060_process_start` [:L710] - the PERFORM returns at the paragraph
    boundary and ``ba999-end`` DOES NOT RUN, so no log record is written.

    That distinction is why this function does not call ``ba999_end`` itself. Each
    caller reproduces its own arrival mode: the ``go to`` callers call this and then
    ``ba999_end`` explicitly (AAP section 0.4.2 Class 4), and the ``perform``
    callers call only this. Folding the call in here would emit log records the
    frozen bridge does not emit.
    """
    logging_data = file_access.logging_data
    logging_data.ws_no_paragraph = 20  # [:L1030]
    # [:L1036-L1037] `MySQL_free_result` - the stored result set is discarded.
    _state().free_result()
    # [:L1039] `set Cursor-Not-Active to true.`
    _state().set_cursor_not_active()


def ba999_end(
    file_access: FileAccess, *, dal_common: AcasDalCommonData | None
) -> None:
    """``ba999-end.`` [common/valueMT.cbl:L1041] and ``ba999-exit.`` [:L1048].

    [:L1044-L1046]::

        if       Testing-1
                 perform Ca-Process-Logs
        end-if.

    then falls through to ``ba999-exit. exit program.`` [:L1048-L1049].

    So EVERY exit from the bridge passes through one conditional log write, and the
    condition is the compile-time switch ``sw-testing`` carried in
    ``ACAS-DAL-Common-data`` [copybooks/Test-Data-Flags.cob].

    ``Testing-1`` is the ``88``-level ``sw-testing value 1``. The predicate
    functions for the ``88``-levels live in ``acas_posting/cobol/condition_names``,
    which this layer may not import - AAP section 0.4.3 confines ``dal`` modules to
    ``dal.connection``, ``dal.status``, ``dal.cursor_state`` and one ``records``
    module - so the comparison is written out here against the field the record
    exposes. It is the same test, evaluated at the same point.

    Args:
        file_access: The status the log record describes.
        dal_common: The testing switch. ``None`` where a caller has none to give,
            in which case no record is written - the same outcome as
            ``sw-testing`` being zero, which the copybook's own comment describes
            as the way to "stop logging" [common/valueMT.cbl:L307].
    """
    if dal_common is not None and dal_common.sw_testing == 1:  # [:L1044] Testing-1
        ca_process_logs(file_access, dal_common)  # [:L1045]
    # [:L1048-L1049] `ba999-exit. exit program.` - the return itself.


def value_mt(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    value: WsValueRecord,
    *,
    system: SystemRecord | None = None,
    transport: TransportSecurity | None = None,
) -> None:
    """``call "valueMT"`` - THE BRIDGE'S OWN THREE-PARAMETER ENTRY POINT.

    [common/valueMT.cbl:L339-L341], verbatim::

        PROCEDURE DIVISION   using File-Access
                                   ACAS-DAL-Common-data
                                   VALUEANAL-REC.   *>  Ws record

    and the call site that supplies them, [common/acas013.cbl:L663-L668]::

        ba020-Call.
            call     "valueMT" using File-Access
                                      ACAS-DAL-Common-data
                                       WS-Value-Record
            end-call.

    THREE PARAMETERS, IN THIS ORDER. Both signatures are published because R-5
    requires it: a reader following the handler finds :func:`dispatch` with its five
    parameters, and a reader following the bridge finds this with its three. Neither
    is a wrapper for the other's convenience - they are the two real entry points of
    the two real programs, and the bridge can be called directly, as
    ``ba020-Call`` proves.

    ⭐ THE THIRD PARAMETER IS THE TABLE-NAMED RECORD, NOT THE COPYBOOK-NAMED ONE.
    The handler passes ``WS-Value-Record``; the bridge receives it as
    ``VALUEANAL-REC`` because it declares its own inline layout under the table's
    name [:L309-L319] instead of copying ``copybooks/wsval.cob``. The two layouts
    are field-compatible, so the ``CALL`` works, but they are DIFFERENT DECLARATIONS
    and one of them flattens the key. That is N-inline-record and N-flatkey, and it
    is why the record class this module accepts is the copybook's ``WsValueRecord``
    while the host-variable group it builds is :class:`TdValueanalRec`.

    THE SECTION HEADER'S WORK IS NOT REPRODUCED. [:L344-L352] reads the terminal
    height into ``ws-env-lines`` and sets two curses environment variables so that
    Escape and the paging keys are detectable. It is presentation setup with no
    database effect, which AAP section 0.1.1 excludes from the migration, and it is
    recorded here as an omission rather than left to be noticed as a gap (R-5).

    ⭐ THE DISPATCH IS PHYSICALLY INSIDE ``ba010-Initialise``. There is no paragraph
    header between the clearing at [:L359-L365] and the ``evaluate`` at
    [:L375-L399]; both belong to the same paragraph. :func:`ba010_initialise`
    carries the clearing and the ``evaluate`` is written here, which is a
    presentational split of one paragraph and changes no order: the clearing still
    happens first, and nothing runs between them.

    Every arm is ``go to`` rather than ``perform`` [:L377-L398], so no arm returns
    to the ``evaluate`` - AAP section 0.4.2 Class 4, a named call followed by an
    explicit return. The verb-to-paragraph map, in the source's own order::

        1 -> ba020-Process-Open        2 -> ba030-Process-Close
        3 -> ba040-Process-Read-Next   4 -> ba050-Process-Read-Indexed
        5 -> ba070-Process-Write       6 -> ba085-Process-Delete-All
        7 -> ba090-Process-Rewrite     8 -> ba080-Process-Delete
        9 -> ba060-Process-Start       other -> ba100-Bad-Function

    ⭐ FUNCTION 6 IS DISPATCHED HERE AND NOWHERE ELSE. The handler's own
    ``evaluate`` [common/acas013.cbl:L343-L362] has no ``when 6`` - its comment says
    ``*> 6 is spare / unused`` - so a caller that sets function 6 and goes through
    the handler lands in :func:`aa100_bad_function`, while the same caller reaching
    the bridge directly deletes every row. The two layers disagree about whether the
    verb exists. Both are reproduced; see N-badfunc.

    Args:
        file_access: Status, logging and credentials - the same object throughout,
            because COBOL passes it by reference and the caller reads the status out
            of it afterwards.
        dal_common: The testing switch that gates every log write.
        value: The record, read for a write or rewrite and written for a read. It is
            MUTATED IN PLACE, as the ``CALL`` mutates its argument - including by
            :func:`ba085_process_delete_all`, which overwrites the key with
            ``"ZZZ"``.
        system: Needed only by the open verb, and only because
            :func:`ba020_process_open` delegates to the shared connection module.
            Defaults to the record :func:`ba012_test_ws_rec_size_2` last saw.
        transport: Transport policy for the open verb.

    Raises:
        AcasFileHandlerFatalError: If a verb other than open is reached with no
            connection. The frozen bridge would pass a stale handle to the client
            library and get an undefined result; failing loudly is the one place
            this module declines to reproduce undefined behaviour, because there is
            no defined behaviour to reproduce.
    """
    # [:L344-L352] the section header's screen setup - omitted, see the docstring.
    # [:L354-L365] `ba010-Initialise.` - the clearing half.
    ba010_initialise(file_access)
    function = int(file_access.file_function)
    # [:L375-L399] the `evaluate File-Function`, physically the same paragraph.
    if function == FileFunction.OPEN:  # [:L376-L377] when 1
        ba020_process_open(
            file_access,
            system=_system_for_open(system),
            dal_common=dal_common,
            transport=transport,
        )
        return
    if function == FileFunction.CLOSE:  # [:L378-L379] when 2
        ba030_process_close(file_access, dal_common=dal_common)
        return
    connection = _require_connection(file_access, function)
    if function == FileFunction.READ_NEXT:  # [:L380-L381] when 3
        ba040_process_read_next(file_access, value, connection, dal_common)
        return
    if function == FileFunction.READ_INDEXED:  # [:L382-L383] when 4
        ba050_process_read_indexed(file_access, value, connection, dal_common)
        return
    if function == FileFunction.WRITE:  # [:L384-L385] when 5
        ba070_process_write(file_access, value, connection, dal_common)
        return
    # [:L389-L390] when 6 - "a special to cleardown all data", the source's words.
    if function == FileFunction.DELETE_ALL:
        ba085_process_delete_all(file_access, value, connection, dal_common)
        return
    if function == FileFunction.RE_WRITE:  # [:L391-L392] when 7
        ba090_process_rewrite(file_access, value, connection, dal_common)
        return
    if function == FileFunction.DELETE:  # [:L393-L394] when 8
        ba080_process_delete(file_access, value, connection, dal_common)
        return
    if function == FileFunction.START:  # [:L395-L396] when 9
        ba060_process_start(file_access, value, connection, dal_common)
        return
    # [:L397-L398] when other.
    ba100_bad_function(file_access, dal_common)


def _system_for_open(system: SystemRecord | None) -> SystemRecord:
    """The system record the open verb needs, and why it is not a linkage parameter.

    ``ba020-Process-Open`` reads its credentials from ``File-Access``'s ``RDB-Data``
    group [common/valueMT.cbl:L406-L429], which
    :func:`ba012_test_ws_rec_size_2` filled from the system record
    [common/acas013.cbl:L638-L643]. The Python connection module is keyed on the
    system record instead, because it owns the pinned numeric converter and the
    transport policy that every handler must share. Both routes carry the same six
    values; this returns whichever record supplied them.
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
    checks it: a verb issued before an open passes a null handle to the library,
    whose result is undefined. There is no behaviour there to reproduce - undefined
    is not a specification - so this reports the ``911`` that
    ``ba012-Test-WS-Rec-Size-2``'s own vocabulary reserves for a failed RDB
    initialisation [common/acas013.cbl:L184] and stops, rather than inventing a
    success or a silent no-op.
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


# ---------------------------------------------------------------------------
# The handler: acas013, one function per paragraph [common/acas013.cbl]
#
# `aa-Process-Flat-File Section.` [common/acas013.cbl:L292] - note the capital S,
# against the lower-case s of `ba-Process-RDBMS section.` [:L588]. Recorded under
# N-casing; COBOL is case-insensitive, so nothing depends on it.
#
# EVERY PARAGRAPH IN THIS SECTION DRIVES THE INDEXED FILE, and the indexed file is
# not part of this migration - see :class:`IndexedFilePathNotMigrated`. Each function
# below therefore performs every statement its paragraph performs UP TO the ISAM
# verb, in order, writing the same paragraph numbers, log keys and statuses, and
# then announces the boundary. That is what makes them useful: a caller that reaches
# one has its `File-Access` in exactly the state the COBOL would have left it in
# before the verb, and R-5's paragraph-to-function mapping is complete rather than
# selectively populated.
# ---------------------------------------------------------------------------


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

    Six things, in this order:

    1. THE LOG IDENTITY [:L298-L299]. ``move 6 to WS-Log-System`` and
       ``move 13 to WS-Log-File-No``. See :data:`WS_LOG_SYSTEM` for N-logsystem6 and
       :data:`WS_LOG_FILE_NO_COBOL` for N-log.
    2. THE KEY GUARD [:L303-L317] - :func:`_aa010_key_guard`.
    3. THE STORE SELECTION [:L321-L325]::

           if       not FS-Cobol-Files-Used
                    move RDBMS-Flat-Statuses to FA-RDBMS-Flat-Statuses
                    perform ba-Process-RDBMS
                    go to AA-Main-Exit
           end-if.

       ⭐ THIS IS THE MIGRATED PATH AND IT RETURNS HERE. Everything after [:L325] is
       indexed-file work that a relational installation never reaches. ``perform`` of
       a SECTION runs the whole section - ``ba010``, ``ba012``, ``ba015``,
       ``ba020-Call`` - and then ``go to AA-Main-Exit`` skips the flat-file
       processing entirely.
    4. ⭐ ``perform ba012-Test-WS-Rec-Size-2.`` [:L329] - THE SECOND HALF OF N-log.
       The flat path performs ``ba012`` DIRECTLY, jumping over ``ba010``, and
       ``ba010``'s only statement is the ``move 23 to WS-Log-File-no`` [:L602]. So
       the flat path logs against file 13 and the relational path against 23, from
       one program, decided purely by which paragraph the ``perform`` names.
    5. ``move spaces to SQL-Err SQL-Msg SQL-State.`` [:L341]. The two statements
       that would also have cleared ``WE-Error`` and ``FS-Reply`` are present and
       COMMENTED OUT [:L339-L340], each carrying the maintainer's own ``?``.
    6. THE FUNCTION DISPATCH [:L343-L362], every arm a ``go to`` - AAP section 0.4.2
       Class 4 - and then ``go to aa100-Bad-Function.`` [:L365] UNCONDITIONALLY,
       under the comment "Should never get here but in case :(". Both routes into
       :func:`aa100_bad_function` are reproduced: the ``when other`` arm and the
       fall-through. The fall-through is unreachable because every arm jumps, and
       it is written anyway because the source writes it.

    ⭐ THERE IS NO ``when 6``. The comment at [:L360] says ``*> 6 is spare / unused``,
    so ``File-Function`` 6 reaches ``aa100-Bad-Function`` here - while the SAME verb
    reaching :func:`value_mt` deletes every row [common/valueMT.cbl:L389-L390]. That
    disagreement between the two layers is N-badfunc.

    Args:
        system: ``System-Record`` - parameter 1, the credential source and the store
            selector.
        value: ``WS-Value-Record`` - parameter 2, read or written in place.
        file_access: ``File-Access`` - parameter 3, status and logging.
        file_defs: ``File-Defs`` - parameter 4. Carries the indexed file's path,
            which only the unmigrated flat path uses; it is accepted because the
            linkage list has it and R-5 requires the parameter order preserved.
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
    # 2. [:L303-L317].
    if _aa010_key_guard(file_access):
        aa999_main_exit(file_access, dal_common)  # [:L309, :L315] Class 3
        return
    # 3. [:L321-L325] the store selection.
    if not _fs_cobol_files_used(system):
        # [:L322] `move RDBMS-Flat-Statuses to FA-RDBMS-Flat-Statuses`, with the
        # source's own "needed for DAL? not JC/dbpre versions" beside it. The group
        # move copies both fields of the group.
        source = system.system_data_block.rdbms_flat_statuses
        target = file_access.fa_rdbms_flat_statuses
        target.fa_file_system_used = source.file_system_used
        target.fa_file_duplicates_in_use = source.file_duplicates_in_use
        # [:L323] `perform ba-Process-RDBMS` - the whole section.
        ba_process_rdbms(
            system, value, file_access, dal_common, transport=transport
        )
        # [:L324] `go to AA-Main-Exit` - Class 3.
        aa_main_exit(file_access)
        return
    # 4. [:L329] `perform ba012-Test-WS-Rec-Size-2.` - ba010 is skipped, so
    # WS-Log-File-No keeps the 13 from step 1. N-log.
    if ba012_test_ws_rec_size_2(system, file_access, dal_common):
        ba_rdbms_exit(file_access)
        return
    # 5. [:L341]. `move spaces to SQL-Err` puts a space in the first character of a
    # `pic x(5)`, not a zero - unlike [common/valueMT.cbl:L683]'s `move zero`.
    logging_data.sql_err = _pic_x("", 5)
    logging_data.sql_msg = _pic_x("", 512)
    logging_data.sql_state = _pic_x("", 5)
    # 6. [:L343-L362] the dispatch. No `when 6`.
    function = int(file_access.file_function)
    if function == FileFunction.OPEN:  # [:L344-L345]
        aa020_process_open(file_access, file_defs, dal_common)
        return
    if function == FileFunction.CLOSE:  # [:L346-L347]
        aa030_process_close(file_access, dal_common)
        return
    if function == FileFunction.READ_NEXT:  # [:L348-L349]
        aa040_process_read_next(file_access, value, dal_common)
        return
    if function == FileFunction.READ_INDEXED:  # [:L350-L351]
        aa050_process_read_indexed(file_access, value, dal_common)
        return
    if function == FileFunction.WRITE:  # [:L352-L353]
        aa070_process_write(file_access, value, dal_common)
        return
    if function == FileFunction.RE_WRITE:  # [:L354-L355]
        aa090_process_rewrite(file_access, value, dal_common)
        return
    if function == FileFunction.DELETE:  # [:L356-L357]
        aa080_process_delete(file_access, value, dal_common)
        return
    if function == FileFunction.START:  # [:L358-L359]
        aa060_process_start(file_access, value, dal_common)
        return
    # [:L360-L361] `when other  *> 6 is spare / unused`.
    aa100_bad_function(file_access, dal_common)
    # [:L365] `go to aa100-Bad-Function.` unconditionally - "Should never get here
    # but in case :(". Unreachable, because every arm above returns, and reproduced
    # because the source writes it. Were an arm ever to fall through, this would
    # overwrite its status with 999/99.
    return


def _aa010_key_guard(file_access: FileAccess) -> bool:
    """The key guard of ``aa010-main`` [common/acas013.cbl:L303-L317], verbatim::

        evaluate File-Function
                 when  4   *> fn-read-indexed
                 when  9   *> fn-start
                   if     File-Key-No not = 1
                          move 998 to WE-Error       *> file seeks key type out of range        998
                          move 99 to fs-reply
                          go   to aa999-main-exit
                   end-if
                 when     8  *> fn-delete
                   if     File-Key-No not = 1        *> 1  is only for RDB as Cobol does it on primary key
                          move 996 to WE-Error       *> file seeks key type out of range        996
                          move 99 to fs-reply
                          go   to aa999-main-exit
                   end-if
        end-evaluate.

    THREE FUNCTIONS ARE GUARDED, IN TWO GROUPS. Read-indexed (4) and start (9) share
    one arm and yield ``998``; delete (8) has its own and yields ``996``. Every other
    function passes unguarded - including write (5) and rewrite (7), which also carry
    a key.

    ⭐ N-guard. THIS SET IS NOT THE FAMILY'S SET. ``acas000`` guards 4, 5 and 7,
    because it dispatches four tables by key number and the key number means
    something different there. Harmonising the two would change which calls this
    handler rejects, so they stay different.

    ⭐ N-996-comment. [:L313]'s comment is a VERBATIM COPY of [:L307]'s - "file seeks
    key type out of range" with the number changed - even though the header's own
    vocabulary gives ``996`` a different meaning: "File Delete key out of range (not
    1)" [:L172]. The comment describes the wrong error. Recorded, not corrected;
    comments are not behaviour, and this one is evidence of how the paragraph was
    written.

    ⭐ The literal is ``not = 1``, and the only valid key number for this table is 1
    because its key table declares exactly one key of reference
    [common/valueMT.cbl:L237-L247]. So the guard is really "reject any key but the
    primary", and the facade never sets anything else - it writes
    ``move 1 to File-Key-No`` before every dispatch
    [copybooks/Proc-ACAS-FH-Calls.cob:L91]. Unreachable through the facade, reachable
    by a direct call, and reproduced either way.

    Returns:
        True if the call was rejected and the caller must transfer to
        ``aa999-main-exit``; False to continue. The status is already written.
    """
    function = int(file_access.file_function)
    key_no = int(file_access.logging_data.file_key_no)
    # [:L304-L305] the shared arm: read-indexed and start.
    if function in (FileFunction.READ_INDEXED, FileFunction.START):
        if key_no != 1:  # [:L306]
            file_access.we_error = int(WeError.FILE_KEY_NO_OUT_OF_RANGE)  # [:L307]
            file_access.fs_reply = int(FsReply.ERROR)  # [:L308]
            return True
        return False
    # [:L311] the delete arm, with its own value.
    if function == FileFunction.DELETE:
        if key_no != 1:  # [:L312]
            file_access.we_error = int(WeError.DELETE_KEY_OUT_OF_RANGE)  # [:L313]
            file_access.fs_reply = int(FsReply.ERROR)  # [:L314]
            return True
    return False


def _fs_cobol_files_used(system: SystemRecord) -> bool:
    """``FS-Cobol-Files-Used`` - the ``88``-level tested at [common/acas013.cbl:L321].

    ``88 FS-Cobol-Files-Used value zero`` over ``File-System-Used``
    [copybooks/wssystem.cob:L112-L116]; ``88 FS-MySql-Used value 1`` is its
    companion. The handler tests the NEGATIVE - ``if not FS-Cobol-Files-Used`` - so
    ANY non-zero value selects the relational path, not only 1.

    Written out here rather than imported: the ``88``-level predicates live in
    ``acas_posting/cobol/condition_names``, which AAP section 0.4.3 excludes from
    this layer's imports.
    """
    return int(system.system_data_block.rdbms_flat_statuses.file_system_used) == 0


def aa020_process_open(
    file_access: FileAccess, file_defs: FileDefs, dal_common: AcasDalCommonData
) -> None:
    """``aa020-Process-Open.`` [common/acas013.cbl:L367].

    ``move spaces to WS-File-Key`` [:L368] "for logging", ``move 201 to
    WS-No-Paragraph`` [:L369], then a four-deep nest on ``Access-Type``
    [:L370-L398]:

    * ``fn-input`` [:L370] - ``open input``; on failure ``move 35 to fs-Reply``
      [:L373] and exit. ⭐ 35 IS A COBOL FILE STATUS, not an ``FS-Reply`` value from
      this system's vocabulary - it is "file not found" as the runtime reports it,
      passed through unmapped. And ⭐ THE CLOSE IS COMMENTED OUT [:L374], so a failed
      open input leaves the file in whatever state the runtime left it.
    * ``fn-i-o`` [:L378] - ``open i-o``; on failure the create dance
      [:L381-L384]: close, ``open output`` with the note "Doesnt create in i-o",
      close, ``open i-o`` again. ⭐ THE SECOND ``open i-o``'S STATUS IS NEVER TESTED,
      so a genuinely broken file reports whatever [:L402] finds.
    * ``fn-output`` [:L387] - ``open output``, with "caller should check fs-reply".
      No test at all.
    * ``fn-extend`` [:L390] - ⭐ ``open extend`` IS COMMENTED OUT [:L391] under
      "Must not be used for ISAM files", and the verb reports ``997``/``99``
      [:L392-L393] instead. THE EXTEND VERB IS REFUSED, NOT PERFORMED. This is
      N-noextendverb's other half: the facade publishes ELEVEN Value verbs
      [copybooks/Proc-ACAS-FH-Calls.cob:L711-L768] and ``Value-Open-Extend`` is not
      among them - the twelve-verb vocabulary AAP section 0.1.1 describes is
      eleven here - yet the handler still carries the refusal for a verb no facade
      paragraph can request.

    Then [:L400-L404]: ``move zero to Cobol-File-Status``, ``move "OPEN VALUE File"
    to WS-File-Key``, and

    ⭐ [:L402-L403]::

        if       fs-reply not = zero
                 move 999 to WE-Error.
        go       to aa999-main-exit.

    THE PERIOD ON [:L403] TERMINATES THE ``if``, so [:L404]'s ``go to`` is
    unconditional - which is what was meant. Compare AAP anomaly 1, where a MISSING
    period nests a statement that was meant to be outside. Here the period is
    present and the structure is right. ``999`` is the value the header calls
    "undefined" [:L169].

    ⭐ The file key is written TWICE - spaces at [:L368] and the literal at [:L401] -
    and the literal is ``"OPEN VALUE File"`` with VALUE upper-cased, against the
    bridge's ``"OPEN Value"`` [common/valueMT.cbl:L441]. Two layers, two spellings,
    both reproduced; N-casing.

    Raises:
        IndexedFilePathNotMigrated: For every access type but extend, which is
            refused before any verb is issued.
    """
    logging_data = file_access.logging_data
    _set_file_key(logging_data, "")  # [:L368]
    logging_data.ws_no_paragraph = 201  # [:L369]
    access_type = int(file_access.access_type)
    # [:L390-L395] the extend arm reports and returns WITHOUT touching the file, so
    # it is the one arm that is fully implementable here.
    if access_type == AccessType.EXTEND:
        file_access.we_error = int(WeError.ACCESS_TYPE_WRONG)  # [:L392] 997
        file_access.fs_reply = int(FsReply.ERROR)  # [:L393] 99
        aa999_main_exit(file_access, dal_common)  # [:L394] Class 3
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

    [:L407-L417], every statement::

        move     202 to WS-No-Paragraph.
        move     spaces to WS-File-Key.     *> for logging
        close    Value-File.
        move     zero to Cobol-File-Status.
        move    "CLOSE VALUE File" to WS-File-Key
        perform  aa999-main-exit.
        move     zero to  File-Function
                          Access-Type.              *> close log file
        perform  Ca-Process-Logs.
        go       to aa-main-exit.

    ⭐ N-closelogtwice. TWO LOG RECORDS ARE WRITTEN FOR ONE CLOSE, and only the first
    is conditional:

    1. ``perform aa999-main-exit`` [:L413] runs ``if Testing-1 perform
       Ca-Process-Logs`` - a log record IF the switch is set.
    2. ``perform Ca-Process-Logs`` [:L416] runs it AGAIN, UNCONDITIONALLY. The
       switch is not consulted. So a close always emits at least one record even
       with logging "off", and emits two with it on.

    And the second record differs from the first: [:L414-L415] zero
    ``File-Function`` and ``Access-Type`` in between, under the comment "close log
    file". So record one names the close verb and record two names function 0 -
    which is what the logger reads as its end-of-file marker. The zeroing is a
    SIGNAL, not a tidy-up, and it is visible in the caller's ``File-Access``
    afterwards because the record is passed by reference.

    ⭐ ``perform aa999-main-exit`` is a PERFORM of a paragraph, so it does NOT
    continue into ``aa-main-exit``; control returns to [:L414]. Only [:L417]'s
    ``go to`` leaves.

    Raises:
        IndexedFilePathNotMigrated: At the ``close`` of [:L409].
    """
    logging_data = file_access.logging_data
    logging_data.ws_no_paragraph = 202  # [:L407]
    _set_file_key(logging_data, "")  # [:L408]
    # [:L409] `close Value-File.` - the indexed-file verb.
    raise _indexed_file_verb("CLOSE", file_access)


def aa040_process_read_next(
    file_access: FileAccess, value: WsValueRecord, dal_common: AcasDalCommonData
) -> None:
    """``aa040-Process-Read-Next.`` [common/acas013.cbl:L419].

    ``move 203 to WS-No-Paragraph`` [:L424], then the end-of-file gate
    [:L425-L433]::

        if       Cobol-File-Eof
                 move 10 to FS-Reply
                            WE-Error
                 move spaces to VA-Code
                                SQL-Err
                                SQL-Msg
                 stop "Cobol File EOF"               *> for testing
                 go to aa999-main-exit
        end-if

    ⭐ N-stopliteral. ``stop "Cobol File EOF"`` IS AN OPERATOR PAUSE, not a program
    termination: the obsolete ``STOP`` literal form displays its literal and
    suspends until the operator resumes. Left in production code under the comment
    "for testing", it means a second read-next after end-of-file HANGS A BATCH RUN
    waiting for a keystroke. Per AAP section 0.3.4 the pause is dropped - it has no
    database effect and blocks a terminal - while the control transfer at [:L432] is
    preserved, and the drop is recorded here rather than left silent (R-5).

    ⭐ ``move spaces to VA-Code`` [:L428] writes the BRIDGE-SIDE record's key, not
    ``WS-VA-Code``. The copybook is included with a rename -
    ``copy "wsval.cob" replacing VA-Code by WS-VA-Code.`` [:L269] - so ``VA-Code``
    here is the ISAM ``FD`` record's key from ``copybooks/fdval.cob``, an entirely
    different item that happens to share the original name. Two records, two keys,
    one name; N-flatkey's cousin.

    Then the read [:L435-L442], whose ``at end`` writes ``10`` to both fields, sets
    the end-of-file flag, ``move 1 to Cobol-File-Status`` under "JIC above dont work
    :)", blanks the record and logs ``"EOF"``. Then [:L443-L448]: the status test,
    the record move, ``move VA-Code to WS-File-Key``, ``move zeros to WE-Error`` -
    ⭐ ``WE-Error`` ONLY, LEAVING ``FS-Reply`` UNCLEARED, which is safe only because
    [:L443] already proved it zero.

    Raises:
        IndexedFilePathNotMigrated: At the ``read`` of [:L435], or at the end-of-file
            gate, which is equally indexed-file state.
    """
    logging_data = file_access.logging_data
    logging_data.ws_no_paragraph = 203  # [:L424]
    # [:L425] `if Cobol-File-Eof` reads the indexed file's own end-of-file flag,
    # which exists only on the unmigrated path, as does the `read` at [:L435].
    raise _indexed_file_verb("READ NEXT", file_access)


def aa045_eval_keys(file_access: FileAccess, value: WsValueRecord) -> None:
    """``aa045-Eval-Keys.`` [common/acas013.cbl:L452].

    Preceded by the maintainer's own doubt [:L450]: "The next block will never get
    executed unless performed so is it needed ?" - which is accurate. It sits
    between :func:`aa040_process_read_next` and
    :func:`aa050_process_read_indexed`, both of which are entered by ``go to``, so
    nothing falls into it.

    [:L453-L468], verbatim::

        evaluate File-Function      *> Set up keys just for logging
                 when  4             *> fn-read-indexed
                 when  5             *> fn-write
                 when  7             *> fn-re-write
                 when  8             *> fn-delete    For delete can ignore Desc key
                 when  9             *> fn-start
                       evaluate  File-Key-No
                                 when   1
                                        move   WS-VA-Code       to WS-File-Key
                                                                     VA-Code
                                 when   other
                                        move   spaces             to WS-File-Key
                       end-evaluate
                 when  other
                       move   spaces             to WS-File-Key
        end-evaluate.

    ⭐⭐ N-noreread. ``acas013`` IS THE ONLY HANDLER WITH AN EVAL-KEYS PARAGRAPH AND
    NO REREAD PARAGRAPH. The full census, verified across the frozen sources - the
    Agent Action Plan's four-handler comparison, extended by a fifth::

        acas005  aa041-Reread L433  +  aa047-Eval-Keys L451
        acas006  aa041-Reread L436  +  aa051-Reread    L461
        acas007  aa041-Reread L430  +  aa051-Reread    L451
        acas008  neither - aa040 L435 stands alone
        acas012  aa041-Reread L429  +  aa045-Eval-Keys L447
        acas013  aa045-Eval-Keys L452 ONLY

    Six handlers, six shapes. There is no handler template to code against, which is
    why every one is read rather than pattern-matched. No reread function is
    invented here.

    ⭐⭐ N-writenokey. FIVE FUNCTIONS ARE LISTED AND ONLY ONE EVER ARRIVES.
    :func:`aa050_process_read_indexed` performs this at [:L475] - the ``when 4``
    arm. Nothing performs it for write (5), rewrite (7), delete (8) or start (9), so
    four of the five arms are dead and those four verbs log whatever key the
    previous call left in ``WS-File-Key``. Every arm is reproduced; the callers are
    reproduced as they are.

    ⭐ ``move WS-VA-Code to WS-File-Key, VA-Code`` writes TWO destinations from one
    statement, and the second is the ISAM record's key - the copy-with-rename at
    [:L269] again. So this paragraph is not "just for logging" as its comment
    claims: it is also how the read-indexed verb gets its search key into the file
    record. The comment understates what the paragraph does.
    """
    logging_data = file_access.logging_data
    function = int(file_access.file_function)
    key_no = int(file_access.logging_data.file_key_no)
    # [:L454-L458] the five shared arms.
    if function in (
        FileFunction.READ_INDEXED,
        FileFunction.WRITE,
        FileFunction.RE_WRITE,
        FileFunction.DELETE,
        FileFunction.START,
    ):
        if key_no == 1:  # [:L460]
            # [:L461-L462] one statement, two destinations. Only the WS-File-Key
            # half is representable here: `VA-Code` is the indexed-file record's
            # key, and no indexed-file record exists on the migrated path.
            _set_file_key(logging_data, _flat_key_of(value))
        else:  # [:L463-L464]
            _set_file_key(logging_data, "")
        return
    # [:L466-L467] the outer `when other`.
    _set_file_key(logging_data, "")


def aa050_process_read_indexed(
    file_access: FileAccess, value: WsValueRecord, dal_common: AcasDalCommonData
) -> None:
    """``aa050-Process-Read-Indexed.`` [common/acas013.cbl:L470].

    ``move 204 to WS-No-Paragraph`` [:L474], ``perform aa045-Eval-keys`` [:L475] -
    ⭐ SPELT WITH A LOWER-CASE ``k`` where the paragraph itself is ``aa045-Eval-Keys``
    [:L452]; COBOL does not care and N-casing records it - then ``move zero to
    Cobol-File-Status`` [:L476].

    [:L477-L487]::

        if       File-Key-No = 1
                 read     Value-File key VA-Code       invalid key
                          move 21 to we-error fs-reply
                 end-read
                 if       fs-Reply = zero
                          move     Value-Record to  WS-Value-Record
                 else
                          move     spaces     to  WS-Value-Record
                 end-if
                 go       to aa999-main-exit
        end-if.

    ⭐ ``move 21 to we-error fs-reply`` puts 21 IN BOTH FIELDS. Twenty-one is an
    ``FS-Reply`` value; the handler's ``We-Error`` vocabulary [:L168-L191] has no 21
    at all, so this writes a meaningless code into the field a caller inspects for
    the reason. The bridge's answer to the same situation is ``23`` with ``We-Error``
    ZEROED [common/valueMT.cbl:L642-L643] - a third disagreement between the layers,
    after the bad-function codes and the start guard.

    ⭐ A FAILED READ BLANKS THE CALLER'S RECORD [:L484]. ``move spaces to
    WS-Value-Record`` over a group containing ``comp`` and ``comp-3`` fields writes
    the space character into their storage, leaving them holding whatever the space
    bit pattern means as a number. The caller's record is not merely unchanged on
    failure - it is corrupted. Reproduced by the relational path only in that a
    failed read there leaves the record alone, which is the bridge's behaviour
    [common/valueMT.cbl:L641-L645]; the flat path's blanking belongs to the
    unmigrated verb.

    Then [:L488-L490]: ``998``/``99`` for any other key number, under "should never
    get here" - which duplicates the guard :func:`_aa010_key_guard` already applied
    at [:L306]. Two rejections of the same condition, in the same program, with the
    same code.

    Raises:
        IndexedFilePathNotMigrated: At the ``read`` of [:L478].
    """
    logging_data = file_access.logging_data
    logging_data.ws_no_paragraph = 204  # [:L474]
    # [:L475] `perform aa045-Eval-keys.` - the one live caller of that paragraph.
    aa045_eval_keys(file_access, value)
    key_no = int(logging_data.file_key_no)
    # [:L488-L490] the fall-through arm, reachable without touching the file.
    if key_no != 1:
        file_access.we_error = int(WeError.FILE_KEY_NO_OUT_OF_RANGE)  # [:L488] 998
        file_access.fs_reply = int(FsReply.ERROR)  # [:L489] 99
        aa999_main_exit(file_access, dal_common)  # [:L490] Class 3
        return
    # [:L478] `read Value-File key VA-Code invalid key`.
    raise _indexed_file_verb("READ INDEXED", file_access)


def aa060_process_start(
    file_access: FileAccess, value: WsValueRecord, dal_common: AcasDalCommonData
) -> None:
    """``aa060-Process-Start.`` [common/acas013.cbl:L492].

    Its own header warns "Not logging starts" [:L494]. ``move 205 to
    WS-No-Paragraph`` [:L496], ``move zeros to fs-reply WE-Error`` [:L497-L498],
    ``move zero to Cobol-File-Status`` [:L499].

    ⭐⭐ N-startguard, THE THIRD MEANING OF 998 AND A MISSING STATUS
    [:L501-L504]::

        if       access-type < 5 or > 8                   *> NOT using 'not >'
                 move 998 to WE-Error                     *> 998 Invalid calling parameter settings
                 go to aa999-main-exit
        end-if

    Three separate defects in four lines, all reproduced:

    1. ``998`` MEANS SOMETHING ELSE. The header assigns ``998`` to "File-Key-No out
       of range" and ``997`` to "Access-Type wrong (< 5 or > 8)" [:L170-L171] - and
       this is precisely the Access-Type test, so it should be ``997``. The comment
       beside it even paraphrases ``997``'s definition while writing ``998``. This
       handler therefore uses ``998`` for THREE distinct conditions: the key guard
       at [:L307], the unreachable key arm at [:L488], and this.
    2. ``FS-Reply`` IS NEVER WRITTEN. The header's own convention marks ``998`` with
       an asterisk meaning "``FS-Reply`` = 99" [:L191], and [:L307] and [:L488] both
       honour it. Here the ``move 99 to fs-reply`` is simply absent, and [:L497] has
       just zeroed the field - so an invalid access type returns ``FS-Reply`` 0,
       WHICH READS AS SUCCESS, alongside a non-zero ``We-Error``. A caller checking
       only ``FS-Reply`` proceeds as though the start had worked.
    3. THE BRIDGE DISAGREES. Its guard writes ``99``/``997``
       [common/valueMT.cbl:L700-L701] - both values different from this one's.

    Then four separate ``if File-Key-No = 1 and fn-<relation>`` blocks
    [:L508-L535], one per relation, each with its own ``start ... invalid key /
    move 21 to Fs-Reply`` - ⭐ ``Fs-Reply`` ALONE here, not both fields as
    :func:`aa050_process_read_indexed` writes.

    ⭐ THERE IS NO ARM FOR ``fn-not-greater-than`` (access type 9). The guard admits
    5..8 only, so 9 could not reach one anyway; the bridge, by contrast, carries a
    ``when 9`` in its relation ``evaluate`` [common/valueMT.cbl:L730-L731] that its
    own guard makes dead. Both halves of that mismatch are preserved.

    A start that matches nothing falls to [:L536] with the zeroes from [:L497-L498]
    intact - success. Compare the bridge's N-start-nostatus, which reaches the same
    outcome by a different route: there nothing is written; here zeroes are written
    first and then nothing overwrites them.

    Raises:
        IndexedFilePathNotMigrated: At the first ``start`` of [:L510].
    """
    logging_data = file_access.logging_data
    logging_data.ws_no_paragraph = 205  # [:L496]
    file_access.fs_reply = int(FsReply.SUCCESS)  # [:L497]
    file_access.we_error = int(WeError.SUCCESS)  # [:L498]
    access_type = int(file_access.access_type)
    # [:L501-L504] the guard. Note what is NOT here: no FS-Reply write.
    if not start_access_type_is_valid(access_type):
        file_access.we_error = int(WeError.FILE_KEY_NO_OUT_OF_RANGE)  # [:L502] 998
        # No `move 99 to fs-reply` - see the docstring. FS-Reply stays at the zero
        # written by [:L497], so this rejection reports success in that field.
        aa999_main_exit(file_access, dal_common)  # [:L503] Class 3
        return
    key_no = int(logging_data.file_key_no)
    if key_no != 1:
        # None of the four relation blocks matches, so control reaches [:L536] with
        # the zeroes intact - a start that did nothing and reported success.
        aa999_main_exit(file_access, dal_common)  # [:L536]
        return
    # [:L510, :L517, :L524, :L531] the four `start` verbs.
    relation = ACCESS_TYPE_TO_RELATION.get(AccessType(access_type), "   ")
    raise _indexed_file_verb(f"START (key {relation.strip()})", file_access)


def aa070_process_write(
    file_access: FileAccess, value: WsValueRecord, dal_common: AcasDalCommonData
) -> None:
    """``aa070-Process-Write.`` [common/acas013.cbl:L538].

    [:L539-L546]::

        move     206 to WS-No-Paragraph.
        move      WS-Value-Record to Value-Record.
        move     zeros to FS-Reply  WE-Error.
        move     zero to Cobol-File-Status
        write    Value-Record invalid key
                 move 22 to FS-Reply
        end-write.
        go       to aa999-main-exit.

    ⭐ N-writenokey. IT NEVER PERFORMS ``aa045-Eval-Keys``, even though that
    paragraph lists ``when 5 *> fn-write`` among its arms [:L455]. So a write logs
    whatever ``WS-File-Key`` the previous call happened to leave behind - the key of
    some earlier record, or spaces. The bridge does its own key logging
    [common/valueMT.cbl:L811] and is unaffected, which is why this only shows up in
    a log comparison and never in table state.

    ⭐ ``move 22 to FS-Reply`` writes ``FS-Reply`` only, leaving ``We-Error`` at the
    zero from [:L541] - so a duplicate-key write reports 22 with no ``We-Error``,
    which is exactly what the bridge does too [common/valueMT.cbl:L828]. The two
    layers agree here, and it is worth saying so: they disagree on bad-function, on
    the start guard and on read-indexed, and agreement is the exception.

    Raises:
        IndexedFilePathNotMigrated: At the ``write`` of [:L543].
    """
    logging_data = file_access.logging_data
    logging_data.ws_no_paragraph = 206  # [:L539]
    # [:L540] `move WS-Value-Record to Value-Record.` - into the indexed-file
    # record, which does not exist here. No aa045 call: see the docstring.
    file_access.fs_reply = int(FsReply.SUCCESS)  # [:L541]
    file_access.we_error = int(WeError.SUCCESS)
    # [:L543] `write Value-Record invalid key`.
    raise _indexed_file_verb("WRITE", file_access)


def aa080_process_delete(
    file_access: FileAccess, value: WsValueRecord, dal_common: AcasDalCommonData
) -> None:
    """``aa080-Process-Delete.`` [common/acas013.cbl:L548].

    [:L549-L556] - the same five statements as :func:`aa070_process_write` with
    ``207`` [:L549], ``delete Value-File record invalid key`` [:L553] and ``move 21
    to FS-Reply`` [:L554].

    ⭐ 21 FOR A FAILED DELETE, where the write reports 22 and the bridge reports
    ``99``/``995`` [common/valueMT.cbl:L880-L881]. As with the write, ``We-Error``
    is left at the zero from [:L551].

    ⭐ It does not perform ``aa045-Eval-Keys`` either, though ``when 8 *> fn-delete``
    is one of its arms [:L457] - carrying the note "For delete can ignore Desc key",
    which refers to a description key this table does not have. The arm was written
    for a table with more than one key of reference; this one declares exactly one
    [common/valueMT.cbl:L237-L247].

    Raises:
        IndexedFilePathNotMigrated: At the ``delete`` of [:L553].
    """
    logging_data = file_access.logging_data
    logging_data.ws_no_paragraph = 207  # [:L549]
    # [:L550] `move WS-Value-Record to Value-Record.`
    file_access.fs_reply = int(FsReply.SUCCESS)  # [:L551]
    file_access.we_error = int(WeError.SUCCESS)
    # [:L553] `delete Value-File record invalid key`.
    raise _indexed_file_verb("DELETE", file_access)


def aa090_process_rewrite(
    file_access: FileAccess, value: WsValueRecord, dal_common: AcasDalCommonData
) -> None:
    """``aa090-Process-Rewrite.`` [common/acas013.cbl:L558].

    [:L560-L567], with ``208`` [:L560], ``rewrite Value-Record invalid key``
    [:L564] and ``move 21 to FS-Reply`` [:L565] - the same 21 as the delete.

    ⭐ [:L566]'s ``end-rewrite`` CARRIES NO PERIOD, unlike the ``end-write.`` of
    [:L545] and the ``end-delete.`` of [:L555]. It is harmless - [:L567]'s ``go to``
    supplies the sentence-ending period - and it is the kind of inconsistency that
    matters here only because AAP anomaly 1 is a missing period that is NOT
    harmless: there, the absence nests a statement inside a conditional and stops
    the General Ledger posting close from ever running
    [sales/sl060.cbl:L1172-L1178]. Same omission, different consequence, which is
    why each one is checked rather than assumed. Recorded under N-casing's
    neighbourhood as a formatting divergence with no behavioural effect.

    Raises:
        IndexedFilePathNotMigrated: At the ``rewrite`` of [:L564].
    """
    logging_data = file_access.logging_data
    logging_data.ws_no_paragraph = 208  # [:L560]
    # [:L561] `move WS-Value-Record to Value-Record.`
    file_access.fs_reply = int(FsReply.SUCCESS)  # [:L562]
    file_access.we_error = int(WeError.SUCCESS)
    # [:L564] `rewrite Value-Record invalid key`.
    raise _indexed_file_verb("REWRITE", file_access)


def aa100_bad_function(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa100-Bad-Function.`` [common/acas013.cbl:L569].

    Under the maintainer's "Houston; We have a problem" [:L571], two statements
    [:L573-L574]::

        move     999 to WE-Error.                         *> 999
        move     99  to fs-reply.

    ⭐ IT ENDS WITHOUT A ``GO TO``, so control FALLS THROUGH into
    ``aa999-main-exit`` [:L576] and the log record is written. Reproduced as an
    explicit call, because the fall-through is the only way the log happens.

    ⭐ N-badfunc. ``999`` is the value the header's own vocabulary calls
    "undefined" [:L169] - the handler reports an unrecognised function by writing
    the code that means "no code assigned". The bridge writes ``990`` for the same
    condition [common/valueMT.cbl:L1021], which at least has a definition
    ("unknown/unexpected"), and :class:`~acas_posting.dal.status.WeError` carries a
    ``992`` named ``INVALID_FUNCTION`` that NEITHER LAYER EVER USES. Three codes for
    one condition, two of them wrong, none of them corrected here.
    """
    file_access.we_error = int(WeError.NOT_USED)  # [:L573] 999
    file_access.fs_reply = int(FsReply.ERROR)  # [:L574] 99
    # No `go to` - falls through to aa999-main-exit [:L576].
    aa999_main_exit(file_access, dal_common)


def aa999_main_exit(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa999-main-exit.`` [common/acas013.cbl:L576].

    [:L577-L579]::

        if       Testing-1
                 perform Ca-Process-Logs
        end-if.

    then falls through to ``aa-main-exit`` [:L581] and ``aa-Exit`` [:L585].

    Identical in form to the bridge's :func:`ba999_end`, and reached from every
    ``go to aa999-main-exit`` in the flat-file section - eleven sites - plus the
    fall-through from :func:`aa100_bad_function` and the single ``perform`` from
    :func:`aa030_process_close`. That ``perform`` is why this cannot itself continue
    into ``aa-main-exit``: a PERFORM must return.
    """
    if dal_common is not None and dal_common.sw_testing == 1:  # [:L577]
        ca_process_logs(file_access, dal_common)  # [:L578]


def aa_main_exit(file_access: FileAccess) -> None:
    """``aa-main-exit.`` [common/acas013.cbl:L581].

    AN EMPTY PARAGRAPH. It holds only the maintainer's note - "Now have processed
    cobol flat file, so .." [:L583] - and exists to be a ``go to`` target, from
    [:L324] on the relational path and [:L417] on the close path. Control falls
    straight through into :func:`aa_exit`.

    Reproduced as a function because R-5 requires one function per paragraph and
    because an empty paragraph is a fact about the program: a reader looking for
    where the relational path rejoins the flat path finds that it does not - it
    lands here, and here does nothing.
    """
    # [:L581-L583] no statements. Falls through to aa-Exit [:L585].
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

    Note the lower-case ``section`` against ``aa-Process-Flat-File Section.``
    [:L292]; N-casing.

    Its header states the intent [:L591-L594]: "Here we call the relevent RDBMS
    module for this table / which will include processing any other joined tables as
    needed". This table has no joins - it is ten columns with a single-column primary
    key [mysql/ACASDB.sql:L1418-L1431] - so the second clause is aspirational here
    and describes the invoice handlers instead.

    ``perform ba-Process-RDBMS`` from [:L323] runs THE WHOLE SECTION, so all four
    paragraphs execute in order and fall through one into the next:

    * :func:`ba010_test_ws_rec_size` [:L596] - one statement, ``move 23 to
      WS-Log-File-no``.
    * :func:`ba012_test_ws_rec_size_2` [:L604] - the first-call record-size check
      and credential load.
    * :func:`ba015_test_ends` [:L646] - the Open-Output special case.
    * :func:`ba020_call` [:L663] - the bridge call.

    then ``ba-rdbms-exit. exit section.`` [:L672-L673].
    """
    # [:L596-L602].
    ba010_test_ws_rec_size(file_access)
    # [:L604-L644]. Returns True when it took the 901 path and jumped to the exit.
    if ba012_test_ws_rec_size_2(system, file_access, dal_common):
        ba_rdbms_exit(file_access)
        return
    # [:L646-L661] and its fall-through into [:L663-L668].
    ba015_test_ends(
        file_access, value, dal_common, system=system, transport=transport
    )
    # [:L672-L673] `ba-rdbms-exit. exit section.`
    ba_rdbms_exit(file_access)


def ba010_test_ws_rec_size(file_access: FileAccess) -> None:
    """``ba010-Test-WS-Rec-Size.`` [common/acas013.cbl:L596].

    Its comment block promises the record-size test [:L598-L600] - "Test on very
    first call only (So do NOT use var A & B again) / Lets test that Data-record
    size is = or > than declared Rec in DAL / as we cant adjust at compile/run time
    due to ALL Cobol compilers ?" - but ⭐ THE PARAGRAPH CONTAINS EXACTLY ONE
    STATEMENT, and it is not that test [:L602]::

        move     23 to WS-Log-File-no.        *> for FHlogger

    The test itself is in the NEXT paragraph. This one only renumbers the log file.

    ⭐⭐ N-log, THE MECHANISM. ``13`` was written at [:L299] for every call; ``23``
    is written here, on the relational path only, because the flat path performs
    ``ba012`` directly at [:L329] and jumps over this paragraph entirely. One
    program, one table, two log file numbers, chosen by which paragraph name a
    ``perform`` mentions. There is no comment anywhere explaining why the relational
    path deserves a different number.

    ⭐ Note ``WS-Log-File-no`` here against ``WS-Log-File-No`` at [:L299] - the same
    field, two capitalisations, four lines apart in the same source. N-casing.
    """
    # [:L602] the paragraph's only statement.
    file_access.logging_data.ws_log_file_no = WS_LOG_FILE_NO_RDB


def ba012_test_ws_rec_size_2(
    system: SystemRecord, file_access: FileAccess, dal_common: AcasDalCommonData
) -> bool:
    """``ba012-Test-WS-Rec-Size-2.`` [common/acas013.cbl:L604].

    The whole body is one ``if A = zero`` [:L606], so EVERYTHING HERE HAPPENS ONCE
    PER PROGRAM LOAD. ``A`` and ``B`` are working storage initialised to zero
    [:L254-L255] and left non-zero afterwards, which the comment at [:L598] spells
    out: "So do NOT use var A & B again".

    First the size test [:L607-L616]: ``A`` takes the length of ``WS-Value-Record``,
    ``B`` the length of ``Value-Record``, and ``if A < B`` reports
    ``901``/``99`` - the caller's record being smaller than the file's would mean a
    write reads past the end of it.

    ⭐ THE TEST CAN NEVER FIRE FOR THIS TABLE. Both records are 66 bytes:
    ``copybooks/wsval.cob`` and ``copybooks/fdval.cob`` declare field-identical
    layouts, and ``3 + 6 + 24 + 3 + 3x4 + 3x6 = 66``. ``A < B`` is ``66 < 66``.

    ⭐ N-recsize. AND YET ``copybooks/wsval.cob:L6`` DECLARES "record size 66 bytes"
    IN A COMMENT WHOSE ARITHMETIC DEPENDS ON THE COMP AND COMP-3 STORAGE SIZES BEING
    WHAT THE FIELD SUM ASSUMES - four bytes for each ``9(5) comp`` and six for each
    ``s9(8)v99 comp-3``. Those sizes are compiler-dependent, which is exactly the
    concern [:L600] raises ("as we cant adjust at compile/run time due to ALL Cobol
    compilers ?"). Under a different ``binary-size`` setting the two records would
    still match each other while both differing from 66, so the declared comment
    could be wrong without the test noticing. NOTHING IS RESOLVED HERE: the number
    is recorded, the arithmetic is recorded, and the question of what the compiled
    program actually measures is left to the oracle, as AAP section 0.6.8 requires
    for the sibling contradiction in ``wsbatch.cob`` (AAP anomaly 15).

    Then the 901 report [:L617-L632]: build the diagnostic, display it at 2301 and
    2401, log it if testing, ``accept Accept-Reply at 2433`` [:L630] and
    ``go to ba-rdbms-exit`` [:L631].

    ⭐ THE ``accept`` IS DROPPED AND THE TRANSFER IS KEPT, per AAP section 0.3.4: a
    prompt that only pauses for acknowledgement after an error display has no
    database effect, so the pause goes and the control transfer stays. The two
    ``display``s become one log record at error severity. ⭐ AND NOTE THE 901 PATH
    LOGS UNCONDITIONALLY-ISH: [:L627-L629] performs ``Ca-Process-Logs`` under
    ``Testing-1``, which contradicts the comment on ``Ca-Process-Logs`` itself -
    "Not called on DAL access as it does it already" [:L676]. It is called on DAL
    access, here. Recorded.

    Finally the credential load [:L638-L643], six moves from the system record into
    ``RDB-Data``::

        move     RDBMS-DB-Name to DB-Schema
        move     RDBMS-User    to DB-UName
        move     RDBMS-Passwd  to DB-UPass
        move     RDBMS-Port    to DB-Port
        move     RDBMS-Host    to DB-Host
        move     RDBMS-Socket  to DB-Socket

    under the comment "Load up the DB settings from the system record as its not
    passed on / hopefully once is enough :)" [:L635-L636]. THE ORDER IS NOT THE
    ORDER THE BRIDGE THEN SENDS THEM IN - schema, user, password, port, host, socket
    here; schema, host, user, password, port, socket at
    [common/valueMT.cbl:L406-L429]. Both orders are preserved in their own place; it
    is unobservable, and unobservable differences are still differences.

    THE LOAD IS DELEGATED to
    :func:`acas_posting.dal.connection.load_rdb_data_once`, whose name records the
    same "once is enough" contract and which owns the caching so that all twenty
    handler modules share one interpretation of it. ⛔ It is NOT duplicated here.

    Returns:
        True if the 901 path was taken and the caller must transfer to
        ``ba-rdbms-exit``; False to continue into ``ba015-Test-Ends``.
    """
    global _RECORD_SIZE_TESTED, _SYSTEM_FOR_OPEN
    # [:L606] `if A = zero` - the whole paragraph body, first call only.
    if _RECORD_SIZE_TESTED:
        return False
    _RECORD_SIZE_TESTED = True
    # [:L607-L609] `move function Length (WS-Value-Record) to A`.
    a = _WS_VALUE_RECORD_LENGTH
    # [:L610-L612] `move function length (Value-Record) to B`. Note the lower-case
    # `length` against the upper-case `Length` three lines above - N-casing again.
    b = _VALUE_RECORD_LENGTH
    # [:L613-L616] `if A < B` -> 901/99, under the source's own aside "COULD LET
    # caller module deal with these errors !!!!!!!". Unreachable for this table
    # (66 < 66), written out because the frozen source writes it and because the
    # 901 disposition needs a home should the two constants ever disagree.
    if a < b:  # pragma: no cover - 66 < 66 is false; see N-recsize
        file_access.we_error = int(WeError.RECORD_SIZE_MISMATCH)  # [:L614] 901
        file_access.fs_reply = int(FsReply.ERROR)  # [:L615] 99
    # [:L617-L632] `if WE-Error = 901`. IT RE-TESTS THE FIELD rather than using the
    # branch above, so a caller that arrived ALREADY CARRYING 901 takes this path
    # even though the size test passed - nothing clears We-Error on the way in, the
    # statements that would have being commented out at [:L339-L340]. Preserved as
    # the separate test it is.
    if int(file_access.we_error) == WeError.RECORD_SIZE_MISMATCH:
        # [:L618-L624] the diagnostic, built into `Display-Blk pic x(75)` [:L256]
        # and therefore truncated at seventy-five characters. `A` and `B` are
        # `pic 9(4)` [:L254-L255], so each renders as four zero-padded digits -
        # which is what the commented-out template at [:L265] shows as "yyy" and
        # "zzz", three characters, from before N-varsAB changed their width.
        display_blk = _pic_x(f"{_AC902}{a:04d} < Value-Rec = {b:04d}", 75)
        # [:L625-L626] two `display ... with erase eol` at 2301 and 2401. Screen
        # output with no database effect, so AAP section 0.3.4 makes them log records
        # at the severity the original intends - an error the operator must notice.
        # They must not alter control flow, and they do not.
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
        # [:L630] `accept Accept-Reply at 2433` - DROPPED. Its only effect is to
        # block a terminal until a key is pressed, and no database state depends on
        # it. [:L631] `go to ba-rdbms-exit` - PRESERVED, as this return value.
        return True
    # [:L638-L643] the six credential moves - schema, user, password, port, host,
    # socket - delegated to the shared loader so that all twenty handler modules
    # share one reading of "hopefully once is enough  :)" [:L636]. NOT duplicated
    # here, and the password never reaches a log or a diagnostic field.
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

    Its comment block records a design intention never carried out [:L649-L651]:
    "HERE we need a CDF [Compiler Directive] to select the correct DAL based on the
    pre SQL compiler e.g., JCs or dbpre or Prima conversions <<<< ? >>>>> / Do this
    after system testing and pre code release." No directive exists; the JC bridge
    is called unconditionally [:L653].

    The body [:L656-L661], verbatim::

        if       fn-open
          and    fn-output
                 perform  ba020-Call           *> open access
                 set fn-Delete-All to true
                 move zero to Access-Type
        end-if.                                *> full through for call to delete

    then FALLS THROUGH into ``ba020-Call`` [:L663]. So an open-output makes TWO
    bridge calls: the first opens, the second - with ``File-Function`` now 6 -
    deletes every row. That is how "open output" acquires its COBOL meaning of
    "truncate", and it is the same mechanism AAP section 0.6.5 describes for the IRS
    transfer file.

    The fall-through is AAP section 0.4.2 Class 2: a forward path whose post-block
    work must be placed faithfully, not merely jumped over. Here the "post-loop
    work" is the second call itself.

    ⭐ ``*> full through for call to delete`` [:L661] - "full" for "fall". Recorded
    verbatim because comments are evidence.

    ⭐⭐ FOUR VARIANTS OF THIS PARAGRAPH EXIST ACROSS THE FAMILY, not the three the
    Agent Action Plan's own table lists. Verified in each handler's
    ``ba015-Test-Ends``::

        acas005 L644  the whole block COMMENTED OUT [:L649-L653], "[ Backup code ]"
                      -> no clear-down at all
        acas006 L635  live two-call pattern [:L640-L644]
        acas007 L622  live two-call pattern [:L627-L631]
        acas008 L566  `set fn-Delete-All` WITHOUT the first call [:L571-L574]
                      -> ONE coerced call; the open never happens
        acas012 L648  NO open-output block whatsoever
                      -> fn-Output reaches the bridge unaltered, table never cleared
        acas013 L646  the two-call pattern PLUS `move zero to Access-Type` [:L660]

    ⭐ ``acas013`` IS THE ONLY ONE THAT ZEROES ``Access-Type``. No sibling does. The
    SQL is unaffected - the bridge dispatches on ``File-Function`` alone and
    :func:`ba085_process_delete_all` never reads ``Access-Type`` - but the value
    reaches ``fhlogger`` through ``File-Access``, so it is observable in a log
    comparison, and it is left in the caller's record afterwards. Reproduced, and
    the divergence recorded rather than harmonised.
    """
    # [:L656-L657] `if fn-open and fn-output`.
    is_open = int(file_access.file_function) == FileFunction.OPEN
    is_output = int(file_access.access_type) == AccessType.OUTPUT
    if is_open and is_output:
        # [:L658] `perform ba020-Call  *> open access` - the FIRST call.
        ba020_call(
            file_access, value, dal_common, system=system, transport=transport
        )
        # [:L659] `set fn-Delete-All to true` - File-Function becomes 6, the verb
        # the handler's own dispatch calls "spare / unused" [:L360].
        file_access.file_function = int(FileFunction.DELETE_ALL)
        # [:L660] `move zero to Access-Type` - unique to this handler.
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

    [:L664-L668], verbatim::

        ba020-Call.
            call     "valueMT" using File-Access
                                      ACAS-DAL-Common-data
                                       WS-Value-Record
            end-call.

    followed by "Any errors leave it to caller to recover from" [:L670] - which is
    the whole of this paragraph's error handling. No status is inspected, nothing is
    retried, nothing is logged here.

    ⭐⭐ N-ba020call. THE PARAGRAPH IS NAMED ``ba020-Call``, AND ONLY IN THIS
    HANDLER. The verified census across the family - which CORRECTS the three-way
    split the Agent Action Plan's own notes describe::

        ba020-Process-DAL declared      acas005 L662, acas006 L653, acas007 L640
        no ba020 paragraph, CALL inline
                          inside ba015  acas008 (CALL L583), acas012 (CALL L658)
        ba020-Call                      acas013 L663 ONLY

    So ``acas012`` does NOT declare ``ba020-Process-DAL``; it calls inline, as
    ``acas008`` does. Three shapes, not two, and this handler is alone in the third.
    R-5 requires the function be named after THIS handler's paragraph, so it is
    :func:`ba020_call` and not ``ba020_process_dal``. Naming it after the family
    would break the one mapping traceability exists to provide.

    ⭐ The three arguments are the bridge's own linkage, in the bridge's order -
    ``File-Access`` first, the record LAST - which is the reverse emphasis of the
    handler's five-parameter list, where ``System-Record`` leads and ``File-Access``
    is third. Both orders are published verbatim; see :func:`value_mt`.
    """
    # [:L664-L668].
    value_mt(
        file_access, dal_common, value, system=system, transport=transport
    )
    # [:L670] "Any errors leave it to caller to recover from" - deliberately no
    # status inspection, no retry, no log. Reproduced as the absence it is.


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

    TEXTUALLY IDENTICAL IN BOTH PROGRAMS [common/acas013.cbl:L679-L680]::

        call     "fhlogger" using File-Access
                                  ACAS-DAL-Common-data.

    followed by ``ca-Exit.     exit.`` [:L682] and [common/valueMT.cbl:L1410]. One
    function serves both paragraphs because they are the same two lines with the
    same two arguments; the two ``ca-Exit`` paragraphs are likewise one
    :func:`ca_exit`.

    ⭐ The handler's copy carries a comment the bridge's does not [:L676]: "Not
    called on DAL access as it does it already". IT IS CALLED ON DAL ACCESS - by
    ``ba012-Test-WS-Rec-Size-2``'s 901 path at [:L628], which is squarely on the
    relational route. The comment is wrong about the program it annotates, and it is
    recorded rather than corrected.

    ⭐ ``fhlogger`` IS NOT MIGRATED. AAP section 0.2.2 places ``common/fhlogger.cbl``
    among the non-posting utilities that are explicitly out of scope, and R-1 forbids
    calling the COBOL program. The record it would write is emitted as a log line
    carrying the same fields - the log system, the file number, the paragraph number,
    the status pair and the file key - so that a comparison has something to compare,
    while the file the COBOL writes has no counterpart. Recorded as a deliberate
    omission (R-5).

    ⭐ NO CREDENTIAL REACHES THE LOG. ``File-Access`` contains ``DB-UPass``, and
    ``fhlogger`` receives the whole group; this writes named fields only, and the
    password is not among them. That is a deliberate departure, taken because rule
    V.S1 forbids emitting a credential and because no database state depends on it.
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
    because R-5 requires a function per paragraph and because ``exit.`` is the
    marker that ``Ca-Process-Logs`` ends here rather than falling into whatever
    follows.
    """
    return


# ---------------------------------------------------------------------------
# The published handler entry point
# ---------------------------------------------------------------------------


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

    [common/acas013.cbl:L283-L289], verbatim including its blank lines::

        Procedure Division Using System-Record

                                 WS-Value-Record

                                 File-Access
                                 File-Defs
                                 ACAS-DAL-Common-data.

    FIVE PARAMETERS, IN THIS ORDER, exactly as AAP section 0.4.3 specifies the
    contract for this file::

        FROM:  call "acas013" using System-Record WS-Value-Record File-Access
                                    File-Defs ACAS-DAL-Common-data
        TO:    acas013_value.dispatch(system, value, file_access, file_defs, dal_common)

    THE CALLER IS THE FACADE, and it does one thing first
    [copybooks/Proc-ACAS-FH-Calls.cob:L90-L97]::

        acas013.
            move 1 to File-Key-No.
            call "acas013" using System-Record
                                 WS-Value-Record
                                 File-Access
                                 File-Defs
                                 ACAS-DAL-Common-data
            end-call.

    ``move 1 to File-Key-No`` precedes every dispatch, which is why the key guard of
    :func:`_aa010_key_guard` never fires through the facade and why it is
    nevertheless reproduced: a direct caller can set anything.

    ⭐ ELEVEN VERBS, NOT TWELVE. The facade publishes ``Value-Open``,
    ``Value-Open-Input``, ``Value-Open-Output``, ``Value-Close``, ``Value-Delete``,
    ``Value-Delete-All``, ``Value-Start``, ``Value-Read-Next``,
    ``Value-Read-Indexed``, ``Value-Write`` and ``Value-Rewrite``
    [copybooks/Proc-ACAS-FH-Calls.cob:L711-L768]. There is NO
    ``Value-Open-Extend``, against the twelve-verb vocabulary AAP section 0.1.1
    describes - and yet :func:`aa020_process_open` still carries the extend refusal
    for a verb no facade paragraph can request. N-noextendverb.

    ⭐ ``Value-Start`` DOES NOT ZERO ``Access-Type``
    [copybooks/Proc-ACAS-FH-Calls.cob:L743], deliberately, so 5..9 arrives intact
    and IS the START relation. This module passes it through unmodified to
    :func:`ba060_process_start`; anything else would break positioning.

    THIS IS NOT A WRAPPER AROUND :func:`value_mt`. It is the handler, which is a
    different program with a different linkage, a different function dispatch, a
    different bad-function code and a different key guard. Both are published
    because R-5 requires that a reader following either COBOL convention find a
    correspondingly named Python function.

    Args:
        system: ``System-Record``. Selects the store at
            [common/acas013.cbl:L321] and supplies the credentials at [:L638-L643].
        value: ``WS-Value-Record``. MUTATED IN PLACE, as a COBOL ``CALL`` mutates
            its argument.
        file_access: ``File-Access``. Carries the request in and the status out;
            read it after the call, as the COBOL callers do.
        file_defs: ``File-Defs``. The indexed file's path, used only by the
            unmigrated flat path, and accepted because the linkage list has it.
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

    Example:
        The Value facade's read-indexed verb, end to end::

            file_access.logging_data.file_key_no = 1     # the facade's own move
            file_access.file_function = int(FileFunction.OPEN)
            file_access.access_type = int(AccessType.INPUT)
            dispatch(system, value, file_access, file_defs, dal_common)

            file_access.file_function = int(FileFunction.READ_INDEXED)
            value.va_code.va_system = "S"
            value.va_code.va_group.va_first = "A"
            value.va_code.va_group.va_second = "1"
            dispatch(system, value, file_access, file_defs, dal_common)
            # file_access.fs_reply is 0 and `value` holds the row, or 23 and it does
            # not - see ba050_process_read_indexed on why 23 and not 21.
    """
    # [:L292] `aa-Process-Flat-File Section.` then [:L294] `aa010-main.` - control
    # enters at the first paragraph of the first section, so this is the whole of it.
    aa010_main(
        system, value, file_access, file_defs, dal_common, transport=transport
    )


# ---------------------------------------------------------------------------
# R-5: the paragraph-to-function map, as data
# ---------------------------------------------------------------------------

#: Every COBOL paragraph of both programs, mapped to the Python function that
#: reproduces it, with the paragraph's own line number.
#:
#: R-5 requires that "every program must map to a module, every paragraph to a
#: function". This is that mapping in machine-readable form, so
#: ``docs/migration/traceability.md`` can be built from the code rather than
#: maintained alongside it and drift between them cannot go unnoticed. The tuple
#: values are ``(source locator, Python function name)``.
#:
#: THE COVERAGE IS TOTAL AND CHECKED. Both source programs' paragraph inventories are
#: listed, in declaration order, and :func:`paragraph_coverage` verifies at call time
#: that every named function actually exists in this module - so a rename cannot
#: silently break the mapping.
#:
#: Two entries deserve note because they are where this handler diverges from its
#: siblings, and R-5 makes divergence the thing traceability must capture:
#:
#: * ``ba020-Call`` maps to :func:`ba020_call`, NOT ``ba020_process_dal``. Only this
#:   handler names the paragraph that way - N-ba020call.
#: * THERE IS NO REREAD ENTRY on the handler side. ``acas013`` has ``aa045-Eval-Keys``
#:   and no reread paragraph of any name, alone among six siblings - N-noreread. The
#:   bridge does have one, ``ba041-Reread``, and it is listed under the bridge.
PARAGRAPH_FUNCTIONS: Final[Mapping[str, tuple[str, str]]] = MappingProxyType(
    {
        # --- common/acas013.cbl, the handler ------------------------------------
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
        # --- common/valueMT.cbl, the bridge -------------------------------------
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

#: The paragraphs deliberately NOT given a function, each with the reason. R-5
#: requires that "deliberate omissions are recorded as omissions", so they are named
#: here rather than left as gaps in :data:`PARAGRAPH_FUNCTIONS` for a reader to
#: notice and wonder about.
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
        The paragraph keys whose named function is missing - empty when the mapping
        is sound, which is the only acceptable state.
    """
    namespace = globals()
    return tuple(
        paragraph
        for paragraph, (_locator, function_name) in PARAGRAPH_FUNCTIONS.items()
        if not callable(namespace.get(function_name))
    )
