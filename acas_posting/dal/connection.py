"""ACAS relational connection - the native reimplementation of the open path.

WHAT THIS MODULE OWNS
=====================
This module is the single place in ``acas_posting`` that opens a connection to
the frozen MySQL/MariaDB schema, and the single place that decides how a value
coming back is turned into a Python object. Nothing else in the package
connects, and nothing else configures conversion.

Agent Action Plan section 0.4.1.5 states the assignment, summarised rather than
transcribed: build the connection from the ``RDB-Data`` block - schema, user,
password, host, socket and port, cited there as ``copybooks/wsfnctn.cob``
L57-L64 and corrected below to L56 plus L57-L62; use per-statement autocommit
exactly as the COBOL does; use NO connection pool; and pin the converter so
numeric columns arrive as ``Decimal`` or ``int``. Each is discharged below.

WHAT IT REPRODUCES, PARAGRAPH BY PARAGRAPH  (RULE R-5)
======================================================
The COBOL reaches MySQL through a copybook of shared paragraphs that every
generated bridge includes, ``copybooks/mysql-procedures.cpy``. Three of those
paragraphs are the open/close path, and each has a function here named after
it:

===================================== ========================================
COBOL paragraph                       Python function
===================================== ========================================
``Mysql-1000-Open`` [:L63-L85]        :func:`mysql_1000_open`
``Mysql-1090-Exit`` [:L87-L88]        :func:`mysql_1090_exit`
``Mysql-1980-Close`` [:L264-L265]     :func:`mysql_1980_close`
``Mysql-1999-Exit`` [:L267-L268]      :func:`mysql_1999_exit`
===================================== ========================================

``Mysql-1100-Db-Error`` [:L96-L128] is NOT reproduced here: ``dal/status.py``
owns it as :func:`~acas_posting.dal.status.mysql_1100_db_error` and this module
calls it, so the ``(99, 911)`` pair has exactly one implementation.

RULE R-1 - NO COBOL AT RUNTIME
==============================
Rule R-1, verbatim:

    "The Python implementation must not execute, embed, or shell out to the
    COBOL programs. COBOL is the specification for the migration, not a
    runtime dependency of the result. The shipped artifact must run on a host
    with no COBOL compiler and no COBOL runtime present."

``Mysql-1000-Open`` reaches the database through three foreign ``CALL``
statements - ``"MySQL_init"`` [:L66], ``"MySQL_real_connect"`` [:L72] and
``"MySQL_selectdb"`` [:L82] - which resolve into the hand-written C interface
object every bridge, handler and loader links. That object's file name is
deliberately not written anywhere in this file, so a scan of the shipped
package for it returns nothing. The three calls are reimplemented natively with
``mysql-connector-python``: this module starts no process, loads no shared
library of its own and links against no C interface.

RULE R-2 - ZERO BINARY FLOATING POINT: THE PINNED CONVERTER
===========================================================
Rule R-2, verbatim:

    "No accounting value may pass through a binary floating-point type at any
    point - not in computation, not in storage, not in transport."

and, naming THIS FILE by hand:

    "`acas_posting/dal/connection.py` additionally pins the converter
    explicitly rather than relying on the default."

That is why :class:`AcasConverter` exists and is passed to every connection as
``converter_class``. Relying on the driver's default is the named failure mode:
a default that returned a binary floating-point value for one ``DECIMAL``
column would corrupt every posted figure in the state diff while leaving the
arithmetic, record and program layers all demonstrably correct - the hardest
possible place to notice the fault.

Two independent enforcement mechanisms are used, because one a driver upgrade
can silently disable is not enforcement:

1. **The converter itself.** :class:`AcasConverter` overrides every hook the
   frozen schema can reach, and the two it must never reach -
   ``FieldType.FLOAT`` and ``FieldType.DOUBLE`` - raise
   :class:`BinaryFloatingPointError` instead of returning a value.
2. **A connect-time assertion.** :func:`mysql_1000_open` runs
   :data:`CONVERTER_PROBE_STATEMENT` and checks both the returned Python types
   and the converter's own hook table, raising
   :class:`ConverterPinningError` if either has drifted.

The schema makes this tractable. A census of the 22 in-scope tables - 513
columns - finds ``char`` 177, ``decimal`` 128, ``tinyint`` 99, ``int`` 65,
``mediumint`` 21, ``smallint`` 20, ``bigint`` 3, and ZERO ``FLOAT``, ``DOUBLE``
or ``REAL`` anywhere in ``mysql/ACASDB.sql``. So the converter has exactly
three families to serve and any appearance of a fourth is a fault, not a case.

THE CONVERTER GUARDS THE WAY IN; THE WAY OUT IS THE CALLER'S (rules R-2, R-4)
============================================================================
Everything above is about values arriving. Values LEAVING are not this
module's to quantize, and the asymmetry is a trap worth stating plainly here,
because this is the file a handler author reads before writing an ``INSERT``.

Hand the server a ``Decimal`` carrying more places than the column declares
and the server stores it ROUNDED HALF AWAY FROM ZERO. Measured on this
project's own MariaDB 10.11.7 against ``decimal(10,2)``:

    value handed over     server stores      COBOL un-ROUNDED store
    ------------------    -------------      ----------------------
    1.005                 1.01               1.00
    2.675                 2.68               2.67
    -1.005                -1.01              -1.00
    0.125                 0.13               0.12

Every one of those four disagrees, and the disagreement is exactly COBOL's
``ROUNDED`` semantics - ``decimal.ROUND_HALF_UP``, which
``acas_posting.cobol.arithmetic`` reserves for the FIVE sites in the whole
in-scope cycle that write the word (Agent Action Plan section 0.6.1:
``[general/gl080.cbl:L328]``, ``[general/gl051.cbl:L791]``,
``[general/gl051.cbl:L796]``, ``[irs/irs030.cbl:L1551]`` and
``[irs/irs030.cbl:L1562]``). Every other store in the cycle TRUNCATES toward
zero. So a handler that lets the server do the quantizing turns the exception
into the default and silently rounds a figure the COBOL truncates - a defect
FIXED, which rule R-4 counts as a failure, and one that surfaces as a single
wrong penny in a state diff with the arithmetic layer demonstrably correct.

The obligation therefore sits with the caller: every monetary and quantity
value must already be at its column's declared scale, quantized through
``acas_posting.cobol.arithmetic`` against the field's descriptor, BEFORE it is
bound as a statement parameter. This module cannot enforce that - it never
sees which field a parameter belongs to - so it is recorded here rather than
left to be discovered. Nothing in this file rounds, truncates, pads or coerces
an outbound value, by design.

AUTOCOMMIT IS ON, PER STATEMENT, AND THERE IS NO TRANSACTION SCOPE
==================================================================
This is counted from the frozen source, not assumed. A census over all twenty
in-scope bridges - ``systemMT``, ``dfltMT``, ``finalMT``, ``sys4MT``,
``nominalMT``, ``glpostingMT``, ``glbatchMT``, ``slpostingMT``, ``salesMT``,
``valueMT``, ``analMT``, ``slinvoiceMT``, ``otm3MT``, ``purchMT``,
``plinvoiceMT``, ``otm5MT``, ``irsnominalMT``, ``irsdfltMT``,
``irspostingMT`` and ``irsfinalMT`` - counts ZERO occurrences of ``COMMIT``,
``ROLLBACK`` or ``START TRANSACTION`` in every one of them. The corroboration
comes from the other direction: the LOADERS are the only programs in the tree
that even mention commit and rollback, and ``common/glbatchLD.cbl:L9-L12`` asks
the operator to turn autocommit off for them while recording that the server
default is ON. Even there the intention is never carried out - every
``perform aa020-Rollback`` is commented out and ``aa030-Commit`` has no perform
site at all, in any of the 28 loaders - so nothing in the frozen tree ever
reaches a reachable ``COMMIT``.

So the bridges run under the server default and every statement is durable the
moment it succeeds. This module therefore passes ``autocommit=True`` and
publishes no way to start, end or abandon a transaction. That absence is
load-bearing rather than incidental: it is exactly why Agent Action Plan
section 0.6.5 can say of the file-abandoning rejection path, verbatim, "The
partial state is therefore committed, not rolled back."

THERE IS NO CONNECTION POOL - THERE IS EXACTLY ONE HANDLE
=========================================================
The plan forbids threads, event loops, process-level parallelism and any
connection pool; execution is strictly sequential, matching the single-threaded
COBOL. The frozen source agrees structurally: a bridge opens a connection when
asked to open a file [common/glpostingMT.cbl:L389-L419] and closes it when
asked to close one [:L433-L443].

That is NOT the same thing as a connection per bridge, and the difference is
load-bearing. Read on, because the frozen C interface settles it.

ONE PROCESS-GLOBAL HANDLE, SHARED BY EVERY BRIDGE
=================================================
``Mysql-1000-Open`` reaches the server through three foreign ``CALL``s and
``Mysql-1980-Close`` through a fourth. All four land in the hand-written C
interface object that every bridge, handler and loader links, whose source is
vendored in this checkout as ``presql2-package/cobmysqlapi38.c`` inside
``presql2-latest.zip``. Its second declaration is the whole story
[presql2-package/cobmysqlapi38.c:L71]::

    MYSQL            sql, *mysql=&sql;

ONE ``MYSQL`` struct at C file scope, and one pointer that always aims at it.
Every entry point in that file then operates on that one struct and on nothing
else:

=========================================== =================================
C entry point                               What it operates on
=========================================== =================================
``MySQL_init(MYSQL **cid, ...)``    [:L420] ``*cid = mysql``          [:L431]
                                            ``mysql_init(&sql)``      [:L433]
``MySQL_real_connect(host, ...)``   [:L500] ``mysql_real_connect(&sql, ...)``
                                                                      [:L527]
``MySQL_selectdb(dbname)``          [:L534] ``mysql_select_db(mysql,`` [:L539]
``MySQL_close(void)``               [:L230] ``mysql_close(mysql)``     [:L232]
``MySQL_errno`` / ``MySQL_error``   [:L237] ``mysql_errno(mysql)``     [:L240]
=========================================== =================================

Three consequences follow, and each one is an observable this module has to
reproduce:

1. **A bridge does not own a connection.** ``Ws-Mysql-Cid`` is declared
   ``pointer`` [copybooks/mysql-variables.cpy:L65] and ``MySQL_init`` fills it
   with the address of the one struct [:L431], so every bridge's handle holds
   the SAME address. Nothing in the C file ever reads a handle back - not
   ``real_connect``, not ``selectdb``, not ``query``, not ``close`` - so
   ``Ws-Mysql-Cid`` is written and never used. Twenty bridges, one connection.

2. **``Mysql-1980-Close`` closes it for everybody.** The frozen paragraph is
   two lines and takes no argument at all
   [copybooks/mysql-procedures.cpy:L264-L265]::

       Mysql-1980-Close.
           call "MySQL_close".

   so when ``ba030-Process-Close`` in ANY bridge performs it
   [common/glpostingMT.cbl:L443], the connection every other open bridge would
   next use is gone. Their next statement fails, and under anomaly N3 it fails
   as ``(FS-Reply 99, We-Error 911)`` whatever went wrong.

3. **Re-opening revives it for everybody**, because the struct is a static
   that outlives each close: a later ``MySQL_init`` + ``MySQL_real_connect``
   re-establishes a session in that same struct, and every bridge's stale
   handle is aiming at it again.

So this module keeps ONE connection object for the life of the process - see
:data:`_PROCESS_CONNECTION` - and ``mysql_1000_open`` re-establishes the
session ON THAT OBJECT rather than building a second one. Object identity is
the Python analogue of ``&sql``: because every handler ends up holding the same
object, a close by one is a close for all, exactly as above, with no
cooperation required from the twenty-one modules above this one.

THIS IS NOT A POOL, and the distinction is not a quibble. A pool hands out
DIFFERENT connections and takes them back; this hands out THE SAME one and
never reclaims it. There is no borrow, no return, no sizing, no eviction, no
liveness probing and no second connection to hand anybody - which is precisely
why it satisfies rule R-3 while a pool would not.

WHERE THE CREDENTIALS COME FROM, AND WHY ONLY ONCE
==================================================
All six members of ``03 RDB-Data.`` are declared ``value spaces``
[copybooks/wsfnctn.cob:L57-L62], so THERE IS NO CREDENTIAL IN THE FROZEN
SOURCE. The values arrive from the ``SYSTEM-REC`` row, copied field by field by
the file handler at [common/acas008.cbl:L558-L563] - inside a first-call-only
guard, which is anomaly A-1 below. Consequently this module reads NOTHING from
the process environment, no parameter file and no ambient source: rule R-6
requires two runs of one scenario to be byte-identical and an ambient fallback
would let them differ. The only input is the caller's own ``SystemRecord``.

ANOMALIES REPRODUCED, NOT FIXED  (RULE R-4)
===========================================
A-1  **The credentials are loaded exactly once per run and never re-read.**
     The six moves sit inside ``if A = zero`` [common/acas008.cbl:L526], whose
     own comment reads "Test on very first call only  (So do NOT use var A & B
     again)" [:L518] and, at the moves, "Load up the DB settings from the
     system record as its not passed on / hopefully once is enough  :)"
     [:L555-L556]. ``A`` is assigned before the comparison, so from the second
     call onward the whole block - record-length check AND credential load - is
     skipped, and a later change to the ``SYSTEM-REC`` row cannot affect the
     run that read it. Stated in full at :func:`load_rdb_data_once`.

A-2  **Every connect failure is reported as ``(FS-Reply 99, We-Error 911)``,
     whichever step failed.** All three arms of ``Mysql-1000-Open`` funnel into
     the same error paragraph, whose last two statements are unguarded: ``move
     99 to fs-Reply`` [copybooks/mysql-procedures.cpy:L127] and ``move 911 to
     We-Error`` [:L128]. The step is distinguished ONLY by ``ws-No-Paragraph``,
     carrying 101, 102 or 103. Reproduced by :func:`mysql_1000_open` delegating
     to ``status.mysql_1100_db_error``. Note 911's documented meaning, "Rdb
     Error during initializing, possibly can not connect to database"
     [common/glpostingMT.cbl:L143-L144], is accurate on this path - unlike
     everywhere else it is used.

A-3  **The user name travels in a variable named after something else.** The
     ``MySQL_real_connect`` argument list is host, user, password, base, port,
     socket, and its second argument is ``Ws-Mysql-Implementation``
     [copybooks/mysql-procedures.cpy:L73], declared at
     [copybooks/mysql-variables.cpy:L88]. The bridge loads ``DB-UName`` into it
     [common/glpostingMT.cbl:L402-L404], so the variable holds the user name
     and the name is simply wrong. Nothing is renamed; the misnaming is
     recorded so a reviewer diffing argument lists is not misled.

A-4  **A malformed port is not an error - it is a different port.** The C
     interface converts the port characters with a bare ``atoi`` and passes the
     result straight to ``mysql_real_connect``. ``atoi`` cannot fail: it takes
     the leading digits and yields 0 if there are none. So a ``DB-Port`` of
     ``"33o6"`` connects to port 33 and ``"abcde"`` uses the default port. NO
     PORT VALIDATION IS PERFORMED HERE - adding one would be a new validation
     (R-3) and a defect fixed (R-4). Reproduced by :func:`_atoi`.

A-5  **No port above 9999 can be expressed.** ``DB-Port`` is ``pic x(5)``
     [copybooks/wsfnctn.cob:L62] but the working-storage item the bridge
     STRINGs it into is ``pic x(4)`` [copybooks/mysql-variables.cpy:L91], and
     ``STRING`` stops when its receiver is full
     [common/glpostingMT.cbl:L410-L412]. A five-digit port silently loses its
     last digit: ``"13306"`` becomes 1330. Reproduced by
     :func:`connection_parameters`, which narrows before converting.

A-6  **Three literal socket values mean "no socket at all".** Before calling
     ``mysql_real_connect`` the C interface compares the socket item against
     ``"0"``, ``"null"`` and ``"NULL"`` and substitutes a null pointer, so those
     spellings behave like a blank item rather than naming a socket file.
     Reproduced via :data:`_SOCKET_MEANS_NONE`.

A-7  **Multi-statement execution is off, so a stray second statement is a
     syntax error rather than a silent extra execution.** The C interface passes
     a LITERAL ZERO as ``mysql_real_connect``'s client-flag word, so
     CLIENT_MULTI_STATEMENTS is never negotiated. ``mysql-connector-python``
     enables it by default, which would diverge, so :func:`mysql_1000_open`
     unsets it. Here the DRIVER, not the COBOL, carried the surprise, and rule
     R-6 settles it in the compiled program's favour.

A-8  **Closing ONE logical file closes the connection every other open file is
     using.** ``MySQL_close`` takes no argument and closes the single
     file-scope handle [presql2-package/cobmysqlapi38.c:L230-L234], so the
     ``PERFORM MYSQL-1980-CLOSE`` in one bridge's ``ba030-Process-Close``
     [common/glpostingMT.cbl:L443] pulls the connection out from under every
     other bridge in the run. A posting program that holds the batch, posting
     and nominal files open together and closes any one of them leaves the
     other two unusable until something re-opens - and because the failure
     funnels through ``Mysql-1100-Db-Error`` it is reported as the same
     ``(99, 911)`` a genuine connect failure gives, with nothing to
     distinguish the two. Symmetrically, ``Mysql-1000-Open`` re-initialises
     and re-connects THE SAME struct [:L431, :L433, :L527], so opening a
     second file abandons the session the first was using and continues on a
     new one; the switch is invisible because the bridges buffer their result
     sets client-side with ``MySQL_store_result``
     [copybooks/mysql-procedures.cpy:L188]. Reproduced by keeping exactly one
     connection object per process - :data:`_PROCESS_CONNECTION` - and NOT
     fixed: giving each handler its own connection would make a close local,
     which rule R-4 counts as a failure.

     ONE CONSEQUENCE NEEDED HANDLING RATHER THAN REPRODUCING, because it is an
     artefact of this language and not of the frozen one. A bridge can now hold
     a connection another bridge has closed, and ``mysql-connector-python``
     refuses a cursor on it - raising where the frozen bridge, which has no
     acquisition step at all, reports from its ``call "MySQL_query"``
     [copybooks/mysql-procedures.cpy:L165-L166] and so always yields a status
     pair. :func:`acquire_cursor` keeps the two the same by carrying that
     failure to the statement, where every handler already guards it. The
     anomaly is untouched; only the exception that the driver's two-step API
     would have leaked is.

DELIBERATE OMISSIONS, RECORDED AS OMISSIONS  (RULE R-5)
=======================================================
O-1  **The trailing ``x"00"`` on every parameter.** The copybook's own header
     instructs it, verbatim - ``*> The name of your data base followed by hex
     00 needs to be moved into ws-mysql-base-name before execution. example:
     move "MYNAME" & x"00" to ws-mysql-base-name``
     [copybooks/mysql-procedures.cpy:L58-L61] - and each bridge duly appends it
     [common/glpostingMT.cbl:L394-L416]. The NUL is the C-string terminator the
     foreign interface requires; Python strings carry their own length and the
     driver builds the wire protocol itself, so it is dropped as representation
     only, with no observable effect. What those same statements DO carry that
     is observable is the ``delimited by space`` clause, and that is
     reproduced: see :func:`cobol_string_delimited_by_space`.

O-2  **The reset of the two lock-ladder counters.** ``Mysql-1000-Open`` opens
     by clearing ``WS-Mysql-Time-Step`` and ``WS-SQL-Retry``
     [copybooks/mysql-procedures.cpy:L64-L65], the only place either is
     cleared. Both belong exclusively to ``Mysql-1300-DB-Error`` [:L209], the
     backoff ladder ``dal/status.py`` records as anomaly N1: dead code, never
     performed by any in-scope bridge, and declared "NOT YET IN USE AS TESTING
     IS NEEDED" [copybooks/mysql-variables.cpy:L99-L100]. Clearing a counter
     nothing reads has no observable effect, so neither is modelled. For the
     same reason this module adds NO retry of any kind - a retry would be
     anomaly N1 fixed by another route, which rule R-4 forbids.

O-3  **``Mysql-1110-Report-Problem``** [copybooks/mysql-procedures.cpy:L130-
     L137] displays two messages and blocks on ``accept ws-reply``. Per Agent
     Action Plan section 0.3.4 a display with no database effect becomes a log
     record and an acknowledgement pause is dropped. ``dal/status.py`` already
     emits that record; this module adds none of its own.

O-4  **No SQLAlchemy Engine is exposed.** SQLAlchemy is pinned and permitted at
     Core level, but an ``Engine`` owns a connection pool by construction and
     rule R-3 forbids one; naming a pool class to suppress it would still be
     naming a pool class. The connector is therefore the sole path, which Agent
     Action Plan section 0.5.1 also calls "the primary database path". Any
     future Core path must take its connection from :func:`mysql_1000_open` so
     the pinned converter still applies.

LINE-NUMBER CORRECTIONS
=======================
Three citations in the inputs are off by a line or more against the checkout,
and the checkout's own spans are used throughout this file:

============================================ ================= ==============
Citation                                     As given          In checkout
============================================ ================= ==============
``copybooks/wsfnctn.cob`` ``RDB-Data``        L57-L64           L56 + L57-L62
``copybooks/mysql-procedures.cpy`` open       L62-L87           L63-L85
``common/acas008.cbl`` credential moves       L557-L562         L558-L563
============================================ ================= ==============

``copybooks/wsfnctn.cob`` is 117 lines long and L63-L64 are comments, so the
group header is L56 and its six elementary items L57-L62. ``Mysql-1000-Open``
is labelled at L63, its last statement is at L85 and ``Mysql-1090-Exit`` is at
L87. The six credential moves are L558-L563, closed by ``end-if`` at L564.

WHAT THIS MODULE MUST NOT DO
============================
* No DDL and no schema-generating machinery - rule R-3. The harness applies
  ``mysql/ACASDB.sql`` verbatim and nothing here alters it.
* No ORM entity layer, no declarative schema metadata and no reflection - a
  reflected model would make statement text depend on discovered information
  and give this layer a schema it must not own.
* No session-shaping statement the COBOL does not issue; a census of the twenty
  bridges finds none, so none is issued.
* No clock read, no nondeterministic source, no sleep - rule R-6.
* No work at import time: importing this module opens no socket, reads no file
  and configures no logger.
"""

from __future__ import annotations

import decimal
import ipaddress
import logging
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, NoReturn

import mysql.connector
from mysql.connector import FieldType, conversion
from mysql.connector.abstracts import (
    MySQLConnectionAbstract,
    MySQLCursorAbstract,
)
from mysql.connector.constants import ClientFlag

from acas_posting.dal.status import (
    ConnectStep,
    DbErrorStatus,
    FsReply,
    WeError,
    db_error_log_category,
    mysql_1100_db_error,
    redact_for_log,
    sanitise_for_log,
)
from acas_posting.records.file_access import LoggingData, RdbData
from acas_posting.records.system_record import (
    SystemRecord,
    carries_frozen_placeholder_rdbms_credentials,
)

__all__: Final[tuple[str, ...]] = (
    # Ordered isort-style to match `dal/status.py`: the frozen tables and
    # constants first, then the classes, then the behaviour, each group
    # sorted. Neither this ordering nor `status.py`'s is observable.
    "CONVERTER_PROBE_EXPECTED_DECIMAL_TEXT",
    "CONVERTER_PROBE_STATEMENT",
    "IDENTIFIER_QUOTE",
    "LOOPBACK_HOST_NAMES",
    "PINNED_CONVERTER_HOOKS",
    "REJECTED_CONVERTER_HOOKS",
    "SCHEMA_MAX_DECIMAL_PRECISION",
    "SCHEMA_MAX_DECIMAL_SCALE",
    "AcasConverter",
    "BinaryFloatingPointError",
    "ConnectionPolicyError",
    "ConverterPinningError",
    "FrozenPlaceholderCredentialsError",
    "InsecureTransportError",
    "OpenOutcome",
    "TransportSecurity",
    "acquire_cursor",
    "cobol_string_delimited_by_space",
    "connection_parameters",
    "cursor_is_unavailable",
    "execute_statement",
    "load_rdb_data_once",
    "mysql_1000_open",
    "mysql_1090_exit",
    "mysql_1980_close",
    "mysql_1999_exit",
    "process_connection",
    "quote_identifier",
    "rdb_data_from_system_record",
    "rdb_data_is_loaded",
    "reset_process_connection",
    "reset_rdb_data_cache",
    "transport_decimal_context",
)

#: Module logger. A library module attaches no handler and configures no root
#: logger; the application decides where diagnostics go. This mirrors
#: `dal/status.py`, and it is why no logging configuration call appears here.
_LOG: Final[logging.Logger] = logging.getLogger(__name__)


#  THE FROZEN SCHEMA, AS COUNTED  -  THE FACTS THE CONVERTER RESTS ON
#  Counted over the 22 in-scope tables of `mysql/ACASDB.sql`, whose header
#  records the producing server as `MariaDB dump 10.19  Distrib
#  10.11.7-MariaDB` [mysql/ACASDB.sql:L1] for database `ACASDB` [:L3].

#: Widest ``DECIMAL`` precision in any in-scope column. Counted, not chosen:
#: the 128 in-scope ``decimal`` columns use exactly seven distinct forms -
#: ``(4,2)``, ``(5,0)``, ``(5,2)``, ``(6,2)``, ``(9,2)``, ``(10,2)`` and
#: ``(14,2)`` - so 14 significant digits holds any stored value exactly.
#: e.g. `INPUT-GROSS` decimal(14,2) and `LEDGER-BALANCE` decimal(10,2).
SCHEMA_MAX_DECIMAL_PRECISION: Final[int] = 14

#: Widest ``DECIMAL`` scale in any in-scope column. Two, throughout - these
#: are money and quantity fields in a pounds-and-pence accounting system, and
#: the one zero-scale form ``(5,0)`` is narrower still.
SCHEMA_MAX_DECIMAL_SCALE: Final[int] = 2

#: The backtick. MySQL and MariaDB quote identifiers with it, and EVERY ACAS
#: table and column name needs it - see :func:`quote_identifier`.
IDENTIFIER_QUOTE: Final[str] = "`"

#: The driver field types the frozen schema can produce, mapped to the converter hook that
#: must be pinned for each. The hook names are not invented:
#: ``conversion.MySQLConverter.to_python`` builds its dispatch table by lower-casing each
#: ``FieldType`` name and wrapping it as ``_<name>_to_python``, so this table IS the driver's
#: own naming rule made explicit. Coverage, against the module docstring's census: ``DECIMAL``
#: and ``NEWDECIMAL`` for the 128 ``decimal`` columns (MariaDB sends ``NEWDECIMAL`` on the
#: wire; ``DECIMAL`` is the pre-5.0 form, pinned too so no server version can route around the
#: guarantee); ``TINY``, ``SHORT``, ``INT24``, ``LONG``, ``LONGLONG`` for the 99 ``tinyint``,
#: 20 ``smallint``, 21 ``mediumint``, 65 ``int`` and 3 ``bigint`` columns, in that order; and
#: ``STRING`` for the 177 ``char`` columns, with ``VAR_STRING`` pinned as well because the
#: schema holds zero ``varchar`` columns but a ``CAST(... AS CHAR(n))`` reports ``VAR_STRING``
#: and the probe uses one.
PINNED_CONVERTER_HOOKS: Final[Mapping[int, str]] = MappingProxyType(
    {
        FieldType.DECIMAL: "_decimal_to_python",
        FieldType.NEWDECIMAL: "_newdecimal_to_python",
        FieldType.TINY: "_tiny_to_python",
        FieldType.SHORT: "_short_to_python",
        FieldType.INT24: "_int24_to_python",
        FieldType.LONG: "_long_to_python",
        FieldType.LONGLONG: "_longlong_to_python",
        FieldType.STRING: "_string_to_python",
        FieldType.VAR_STRING: "_var_string_to_python",
    }
)

#: The two field types that must never arrive, and the hooks that refuse them.
#: ``mysql/ACASDB.sql`` contains zero ``FLOAT``, ``DOUBLE`` and ``REAL``
#: columns, so either hook firing means the schema has drifted or a caller has
#: written an expression that produces a binary floating-point value. Under
#: rule R-2 neither is recoverable, so both hooks raise.
REJECTED_CONVERTER_HOOKS: Final[Mapping[int, str]] = MappingProxyType(
    {
        FieldType.FLOAT: "_float_to_python",
        FieldType.DOUBLE: "_double_to_python",
    }
)

#: The connect-time probe. Three casts, chosen so the statement depends on no table and
#: therefore cannot be affected by - or affect - any seeded state: ``DECIMAL(10,2)`` is the
#: commonest in-scope decimal form and reports ``NEWDECIMAL``, the type the 128 money columns
#: arrive as; the signed integer cast reports ``LONG``, one of the five integer widths; and
#: the character cast reports ``VAR_STRING``, proving text arrives as ``str`` rather than
#: ``bytes``. The value ``'1.50'`` is deliberate: a driver that returned a binary
#: floating-point value, or a ``Decimal`` normalised to ``1.5``, fails the scale check
#: :func:`_assert_converter_pinned` applies. The literal is quoted as text on both sides so no
#: binary floating-point value is constructed anywhere along the path.
CONVERTER_PROBE_STATEMENT: Final[str] = (
    "SELECT CAST('1.50' AS DECIMAL(10,2)), "
    "CAST(-42 AS SIGNED), "
    "CAST('AB' AS CHAR(4))"
)

#: The exact text the decimal probe value must render as. ``'1.50'`` and not
#: ``'1.5'``: a ``DECIMAL(10,2)`` carries its declared scale, and a converter
#: that discarded the trailing zero would also discard the distinction between
#: a value stored at two decimal places and one stored at one - which the
#: state diff compares.
CONVERTER_PROBE_EXPECTED_DECIMAL_TEXT: Final[str] = "1.50"

#: Width of ``05  DB-Port     pic x(5)`` [copybooks/wsfnctn.cob:L62]. Held as
#: a named constant because the widening from those five CHARACTERS to the
#: integer the driver wants happens in this module and nowhere else - see
#: :func:`connection_parameters`.
_DB_PORT_WIDTH: Final[int] = 5

#: Width of ``Ws-Mysql-Port-Number pic x(4)``
#: [copybooks/mysql-variables.cpy:L91] - the working-storage item the bridge
#: STRINGs ``DB-Port`` into [common/glpostingMT.cbl:L410-L412]. It is ONE
#: CHARACTER NARROWER than ``DB-Port``, so a five-digit port loses its last
#: digit on the way to the driver and no port above 9999 is expressible. That
#: is a limitation of the frozen source, reproduced rather than repaired
#: (rule R-4), and :func:`connection_parameters` applies it.
_WS_MYSQL_PORT_WIDTH: Final[int] = 4

#: The three literal values the C interface reads as "no socket", tested with
#: ``strcmp`` after it has trimmed the item. A ``DB-Socket`` holding any of
#: them behaves exactly like a blank one. Compared case-sensitively, because
#: the C tests exactly these three spellings and not, for example, ``Null``.
_SOCKET_MEANS_NONE: Final[frozenset[str]] = frozenset({"0", "null", "NULL"})


#  RULE R-2 ENFORCEMENT  -  THE TWO FAILURES THAT MUST NOT BE SURVIVABLE


class BinaryFloatingPointError(TypeError):
    """A binary floating-point value reached the transport boundary.

    Raised by :class:`AcasConverter` when a driver field type that produces a
    binary floating-point value is encountered. Rule R-2 is absolute - "No
    accounting value may pass through a binary floating-point type at any
    point - not in computation, not in storage, not in transport" - so there
    is no degraded mode to fall back to and no value worth returning.

    A ``TypeError`` subclass on purpose. ``conversion.MySQLConverter
    .to_python`` catches ``ValueError`` and ``TypeError`` and re-raises a plain
    ``TypeError`` with the offending column name appended, so raising a
    ``TypeError`` gets the column name into the message for free. The cost is
    that the re-raised exception is a plain ``TypeError`` and this class
    survives only as its ``__cause__``; a caller that needs to identify the
    fault programmatically should test ``exc.__cause__``. That is why this
    guard is defence in depth and :func:`_assert_converter_pinned` is the
    primary enforcement: the probe raises out of this module's own code, where
    nothing re-wraps it.
    """


class ConverterPinningError(RuntimeError):
    """The pinned numeric converter is not in force on a live connection.

    Raised by :func:`_assert_converter_pinned`, which runs on every successful
    connect. It means one of:

    * the connection is not using :class:`AcasConverter` at all - the
      ``converter_class`` argument was dropped or overridden;
    * a hook this module pins is no longer overridden, so the driver's default
      would serve that field type;
    * a probe value came back as the wrong Python type; or
    * the decimal probe lost its declared scale.

    Any of those breaks rule R-2 at the transport layer, which Agent Action
    Plan section 0.7.2 singles this file out to prevent. The connection is
    closed before the exception leaves :func:`mysql_1000_open`, so a caller
    cannot accidentally keep using it.

    A ``RuntimeError`` and not a ``TypeError``: nothing about the caller's
    arguments is wrong. The environment has drifted from what the migration
    requires, and the correct response is to stop.
    """


#  THE PINNED CONVERTER  (RULE R-2  -  THIS FILE IS NAMED BY THE RULE)


class AcasConverter(conversion.MySQLConverter):
    """The explicitly pinned type converter for every ACAS connection.

    Rule R-2, of this file, verbatim: "`acas_posting/dal/connection.py`
    additionally pins the converter explicitly rather than relying on the
    default." This class is that pinning. It is passed as ``converter_class``
    to every connection :func:`mysql_1000_open` opens, and it is honoured by
    BOTH driver implementations: ``mysql-connector-python``'s C extension
    detects a custom converter, stops converting in C, and routes every value
    through this class instead, exactly as the pure-Python implementation
    does. So the guarantee does not depend on which implementation is
    installed, and ``use_pure`` is deliberately left unset.

    Every override below returns the same Python type the driver's own default
    returns. That is the point: the behaviour is IDENTICAL and the GUARANTEE is
    not. A default can change in a driver release, be affected by a connection
    argument, or differ between the C and pure implementations; an override
    cannot. :func:`_assert_converter_pinned` then checks at connect time that
    the overrides are still the ones in force, so the guarantee is checked
    rather than assumed.

    Three families and nothing else, per the schema census:

    ============ ================================= ======================
    Family       In-scope columns                  Python type
    ============ ================================= ======================
    decimal      128 ``decimal(p,2)``/``(5,0)``    ``decimal.Decimal``
    integer      99+20+21+65+3 = 208 columns       ``int``
    character    177 ``char(n)``                   ``str``
    ============ ================================= ======================

    plus the two hooks that refuse to return anything at all. No date, time,
    binary or JSON hook is touched: the frozen schema holds zero ``timestamp``,
    ``datetime``, ``blob``, ``text`` and ``varchar`` columns, so overriding
    those would be modelling a case that cannot arise.
    """

    # -- decimal -------------------------------------------------------------
    # Serves the 128 in-scope `decimal` columns. MariaDB sends them as
    # NEWDECIMAL; DECIMAL is the pre-5.0 wire type and is pinned to the same
    # implementation so no server version can route around the guarantee.

    def _decimal_to_python(
        self,
        value: bytes | bytearray | str,
        desc: Any = None,
    ) -> decimal.Decimal:
        """Return a ``DECIMAL`` column as an exact ``decimal.Decimal``.

        The server sends a decimal as its TEXT rendering, so the declared
        scale is present in the bytes and survives if - and only if - the
        ``Decimal`` is built from that text. ``DECIMAL(10,2)`` holding one
        pound fifty arrives as ``b'1.50'`` and becomes ``Decimal("1.50")``,
        whose ``as_tuple().exponent`` is ``-2``. Nothing in this method
        normalises, rounds or re-scales the value.

        The construction is from a ``str`` and never from a binary
        floating-point value - rule R-2 - and there is no intermediate
        numeric type between the wire bytes and the ``Decimal``.

        Arithmetic policy is NOT set here. Precision, truncation direction and
        the five ``ROUNDED`` sites belong to ``cobol/arithmetic.py``, which
        this module does not import and must not (Agent Action Plan section
        0.4.3 does not permit ``dal`` to depend on ``cobol``). This method's
        only job is that the value arrives exact.

        Args:
            value: The column as the driver delivers it - ``bytes`` from the
                wire, or ``str`` if a caller has already decoded it.
            desc: The driver's column description tuple. Unused: the scale is
                carried in the value's own text, so nothing needs to be read
                from the description.

        Returns:
            The value as an exact ``decimal.Decimal`` at its declared scale.
        """
        del desc  # The text carries the scale; the description adds nothing.
        text = (
            value.decode(self.charset)
            if isinstance(value, (bytes, bytearray))
            else str(value)
        )
        return decimal.Decimal(text)

    #: `NEWDECIMAL` is what MariaDB 10.11.7 actually sends for a `decimal`
    #: column. Aliased to the same implementation exactly as the driver's own
    #: base class aliases it, because overriding only one of the pair would
    #: leave the other resolving to the base implementation - the very
    #: "relying on the default" that rule R-2 forbids for this file.
    _newdecimal_to_python = _decimal_to_python

    # -- integer -------------------------------------------------------------
    # Five widths, 208 in-scope columns, one behaviour. Declared as static
    # methods because the driver's base class declares them so and the
    # dispatch table binds whatever it finds; a plain method here would be
    # called with the wrong argument count.
    # `int` and not `Decimal`: these columns hold the COBOL binary family -
    # `binary-long` statistics fields such as `SALES-AVERAGE`
    # [copybooks/wssl.cob:L46-L52] - whose truncation on divide is INTEGER
    # truncation. Widening them to `Decimal` here would quietly repair the
    # double-truncation anomaly the migration is required to reproduce, and
    # rule R-4 makes a defect fixed a failure.

    @staticmethod
    def _tiny_to_python(
        value: bytes | bytearray | str | int,
        desc: Any = None,
    ) -> int:
        """Return a ``TINYINT`` column as ``int`` (99 in-scope columns)."""
        del desc
        return int(value)

    @staticmethod
    def _short_to_python(
        value: bytes | bytearray | str | int,
        desc: Any = None,
    ) -> int:
        """Return a ``SMALLINT`` column as ``int`` (20 in-scope columns)."""
        del desc
        return int(value)

    @staticmethod
    def _int24_to_python(
        value: bytes | bytearray | str | int,
        desc: Any = None,
    ) -> int:
        """Return a ``MEDIUMINT`` column as ``int`` (21 in-scope columns)."""
        del desc
        return int(value)

    @staticmethod
    def _long_to_python(
        value: bytes | bytearray | str | int,
        desc: Any = None,
    ) -> int:
        """Return an ``INT`` column as ``int`` (65 in-scope columns)."""
        del desc
        return int(value)

    @staticmethod
    def _longlong_to_python(
        value: bytes | bytearray | str | int,
        desc: Any = None,
    ) -> int:
        """Return a ``BIGINT`` column as ``int`` (3 in-scope columns)."""
        del desc
        return int(value)

    # -- character -----------------------------------------------------------
    # Serves the 177 in-scope `char(n)` columns, which the driver reports as
    # STRING. VAR_STRING is pinned alongside it: the schema holds zero
    # `varchar` columns, but a `CAST(... AS CHAR(n))` expression reports
    # VAR_STRING and the connect-time probe uses one.
    # TRAILING SPACES ARE NOT STRIPPED. A `char(n)` column is fixed width and
    # its padding is part of the stored value; canonicalising it is the
    # dump normaliser's job, not the transport layer's, and doing it here
    # would hide the copybook-to-column width drift the migration records.

    def _string_to_python(
        self,
        value: bytes | bytearray | str,
        dsc: Any = None,
    ) -> str:
        """Return a ``CHAR`` column as ``str``, padding intact.

        Args:
            value: The column as the driver delivers it.
            dsc: The driver's column description tuple. Unused - the frozen
                schema holds no SET column and no binary-charset column, the
                two cases the driver's own implementation consults it for.

        Returns:
            The value decoded with the connection's character set.
        """
        del dsc
        if isinstance(value, (bytes, bytearray)):
            return value.decode(self.charset)
        return str(value)

    #: `VAR_STRING`, aliased to the same implementation. See the note above.
    _var_string_to_python = _string_to_python

    # -- the two hooks that must never return ---------------------------------

    @staticmethod
    def _float_to_python(value: Any, desc: Any = None) -> NoReturn:
        """Refuse a ``FLOAT`` column - rule R-2.

        ``mysql/ACASDB.sql`` declares zero ``FLOAT`` columns, so reaching this
        method means either the schema has drifted from the frozen file or a
        statement asked the server for a binary floating-point expression.

        Raises:
            BinaryFloatingPointError: Always.
        """
        del value, desc
        raise BinaryFloatingPointError(
            "rule R-2 violated at the transport layer: a FLOAT value reached "
            "acas_posting.dal.connection. No accounting value may pass "
            "through a binary floating-point type at any point - not in "
            "computation, not in storage, not in transport. The frozen schema "
            "mysql/ACASDB.sql declares zero FLOAT, DOUBLE and REAL columns, "
            "so this value cannot have come from an in-scope column."
        )

    @staticmethod
    def _double_to_python(value: Any, desc: Any = None) -> NoReturn:
        """Refuse a ``DOUBLE`` column - rule R-2.

        Raises:
            BinaryFloatingPointError: Always. See
                :meth:`_float_to_python` for the reasoning; ``DOUBLE`` is the
                same fault with a wider mantissa.
        """
        del value, desc
        raise BinaryFloatingPointError(
            "rule R-2 violated at the transport layer: a DOUBLE value reached "
            "acas_posting.dal.connection. No accounting value may pass "
            "through a binary floating-point type at any point - not in "
            "computation, not in storage, not in transport. The frozen schema "
            "mysql/ACASDB.sql declares zero FLOAT, DOUBLE and REAL columns, "
            "so this value cannot have come from an in-scope column."
        )


def transport_decimal_context() -> decimal.Context:
    """Return the decimal context this transport layer is exact under.

    A DELIBERATE context rather than an implicit one, but a narrow one: its
    only job is to guarantee that no value read from - or written to - an
    in-scope column can be rounded or lose a digit merely by being carried.
    Precision is set to twice
    :data:`SCHEMA_MAX_DECIMAL_PRECISION` so that the widest stored form,
    ``decimal(14,2)``, has ample headroom, and every inexact condition is
    trapped so that a silent loss becomes an exception instead.

    ARITHMETIC POLICY DOES NOT LIVE HERE. Truncation on store, the ROUND_DOWN
    default and the five ``ROUNDED`` sites of the in-scope cycle all belong to
    ``cobol/arithmetic.py``. This module does not import it and must not: the
    Agent Action Plan's per-directory import table permits ``dal`` modules to
    reach ``dal.connection``, ``dal.status``, ``dal.cursor_state`` and one
    ``records`` module, and does not permit ``dal`` to reach ``cobol``. A
    caller performing arithmetic should adopt that module's context, not this
    one.

    The context is RETURNED and never installed. Installing a context is a
    process-wide side effect, and this module does no work on import and
    changes no global state.

    Returns:
        A fresh :class:`decimal.Context`, safe for the caller to mutate.

        >>> ctx = transport_decimal_context()
        >>> ctx.prec
        28
        >>> ctx.create_decimal("1.50") + ctx.create_decimal("0.25")
        Decimal('1.75')
    """
    return decimal.Context(
        prec=SCHEMA_MAX_DECIMAL_PRECISION * 2,
        # No rounding mode is nominated as "the" mode, because this context
        # must never round. Trapping Inexact and Rounded turns any loss into
        # an exception rather than a quietly altered figure.
        traps=[
            decimal.Inexact,
            decimal.Rounded,
            decimal.InvalidOperation,
            decimal.DivisionByZero,
            decimal.Overflow,
        ],
    )


#  COBOL TEXT SEMANTICS AT THIS BOUNDARY
#  Two of them, and both are observable, so neither may be approximated.


def cobol_string_delimited_by_space(field: str) -> str:
    """Return a fixed-width field as the COBOL ``STRING`` verb sends it.

    Every bridge loads the driver's parameters out of ``RDB-Data`` with the
    same six-statement idiom, e.g. [common/glpostingMT.cbl:L394-L396]::

        string   DB-Schema      delimited by space
                 X"00"          delimited by size
                                  into WS-MYSQL-BASE-NAME
        end-string.

    ``delimited by space`` means the sending item contributes its characters UP
    TO the first space and stops. Two consequences follow, and both are
    reproduced here rather than approximated by a trailing-space strip:

    * a field that is all spaces contributes NOTHING, so the driver receives an
      empty string - which is how "unset" is expressed. That is what makes a
      spaces-valued ``DB-Host`` or ``DB-Socket`` mean "use the default", and
      :func:`connection_parameters` relies on it.
    * a field with an EMBEDDED space is truncated at that space. A host name of
      ``"db1 db2"`` reaches the driver as ``"db1"``. That is a latent trap in
      the frozen source rather than a defect this migration may repair, so it
      is preserved exactly; a plain right-strip would send ``"db1 db2"`` and
      diverge from the compiled program.

    The ``X"00"`` the same statements append is omission O-1 - a C string
    terminator with no Python analogue. It is not reproduced, and the module
    docstring records the omission.

    Args:
        field: The fixed-width, space-padded field value.

    Returns:
        The characters before the first space, or ``""`` if the field starts
        with one.

        >>> cobol_string_delimited_by_space("ACASDB      ")
        'ACASDB'
        >>> cobol_string_delimited_by_space("            ")
        ''
        >>> cobol_string_delimited_by_space("db1 db2     ")
        'db1'
        >>> cobol_string_delimited_by_space("")
        ''
    """
    return field.partition(" ")[0]


def quote_identifier(name: str) -> str:
    """Return a table or column name wrapped in backticks, ready for SQL.

    THE SINGLE QUOTING HELPER FOR THE WHOLE DATA-ACCESS LAYER. Every ACAS
    table name and every ACAS column name contains a HYPHEN - the schema is
    full of names like ``GLBATCH-REC``, ``BATCH-KEY`` and ``INPUT-GROSS`` -
    and MySQL and MariaDB parse an unquoted hyphen as the subtraction
    operator. So quoting is not a style preference: an unquoted ACAS
    identifier is a SYNTAX ERROR. Centralising it here turns twenty-one
    chances to get it wrong into one.

    That is what the frozen source does too. The generated bridges wrap the
    table name as a literal, ``"`GLPOSTING-REC`"``
    [common/glpostingMT.cbl:L623-L624], and build a column reference by
    stringing a backtick, the key name and a backtick
    [common/glpostingMT.cbl:L602-L604]::

        string   "`"                   delimited by size
                 KeyName (KOR-x1)      delimited by space
                 "`"                   delimited by size

    Note the ``delimited by space`` on the name itself: a COBOL key name is a
    fixed-width, space-padded item, so the bridge quotes only its significant
    characters. This function applies the same rule via
    :func:`cobol_string_delimited_by_space`, which means a caller may pass a
    padded name from a record layout and get the same identifier the bridge
    would emit.

    An embedded backtick is ESCAPED by doubling it, which is MySQL's own rule
    for a quoted identifier. No ACAS identifier contains one - the schema's
    177 character columns and 22 table names are all upper case, digits and
    hyphens - so the branch cannot fire on frozen data. It is implemented
    rather than assumed away because this helper is the layer's only quoting
    path and a silent mis-quote there would be an injection.

    Args:
        name: The identifier, optionally space-padded to a COBOL field width.

    Returns:
        The identifier enclosed in backticks.

    Raises:
        ValueError: If the identifier is empty once the ``delimited by space``
            rule has been applied, or if it contains a NUL. MySQL permits
            neither in an identifier, and both would otherwise produce a
            statement whose meaning is not the caller's.

        >>> quote_identifier("GLBATCH-REC")
        '`GLBATCH-REC`'
        >>> quote_identifier("BATCH-KEY   ")
        '`BATCH-KEY`'
        >>> quote_identifier("INPUT-GROSS")
        '`INPUT-GROSS`'
    """
    significant = cobol_string_delimited_by_space(name)
    if not significant:
        raise ValueError(
            "an ACAS identifier cannot be empty: every table and column name "
            "in mysql/ACASDB.sql is a non-empty upper-case, hyphenated name "
            f"(received {name!r})"
        )
    if "\x00" in significant:
        raise ValueError(
            "an ACAS identifier cannot contain a NUL: MySQL forbids it, and "
            "no name in mysql/ACASDB.sql carries one "
            f"(received {name!r})"
        )
    escaped = significant.replace(IDENTIFIER_QUOTE, IDENTIFIER_QUOTE * 2)
    return f"{IDENTIFIER_QUOTE}{escaped}{IDENTIFIER_QUOTE}"


#  THE CREDENTIAL LOAD  -  `common/acas008.cbl:L558-L563`


def _pic_x(text: str, width: int) -> str:
    """Fit a value to an alphanumeric picture of ``width`` characters.

    COBOL ``MOVE`` into a ``pic x(n)`` item truncates on the right and pads on
    the right with spaces. Reproduced locally, mirroring the same private
    helper in ``dal/status.py``, because this module may not import
    ``cobol/move.py``: the Agent Action Plan's import table does not permit a
    ``dal`` module to reach the ``cobol`` package.

    Args:
        text: The sending value.
        width: The receiving item's declared character count.

    Returns:
        Exactly ``width`` characters.
    """
    return text[:width].ljust(width)


def rdb_data_from_system_record(system_record: SystemRecord) -> RdbData:
    """Copy the connection parameters out of ``SYSTEM-REC`` into ``RDB-Data``.

    Reproduces the six ``MOVE`` statements at [common/acas008.cbl:L558-L563],
    IN THEIR SOURCE ORDER. That order is Schema, UName, UPass, **Port, Host,
    Socket** - which is NOT the declaration order of ``RDB-Data``, where port
    comes last [copybooks/wsfnctn.cob:L57-L62]. Rule R-6 makes statement
    ordering part of behaviour, so the source order is what is reproduced::

        move     RDBMS-DB-Name to DB-Schema        [common/acas008.cbl:L558]
        move     RDBMS-User    to DB-UName         [:L559]
        move     RDBMS-Passwd  to DB-UPass         [:L560]
        move     RDBMS-Port    to DB-Port          [:L561]
        move     RDBMS-Host    to DB-Host          [:L562]
        move     RDBMS-Socket  to DB-Socket        [:L563]

    All six receiving items are declared ``value spaces``
    [copybooks/wsfnctn.cob:L57-L62], so THE FROZEN SOURCE CARRIES NO
    CREDENTIAL and every value a connection ever uses originates in the
    ``SYSTEM-REC`` row. Nothing is read from the process environment or from
    any parameter file: rule R-6 requires two runs of one scenario to be
    byte-identical, and an ambient source would let them differ.

    Each value is fitted to its receiving picture - 12 characters for schema,
    user and password, 32 for host, 64 for socket and 5 for port. The sending
    items happen to be declared at the same widths in
    ``copybooks/wssystem.cob`` (L137, L138, L139, L142, L143, L144), so no
    truncation occurs on frozen data; the fit is applied anyway because a
    ``MOVE`` truncates whatever it is given and a caller may hold a record
    built by hand.

    All six sending items are ``05`` items of ``03 System-Data-Block.``
    [copybooks/wssystem.cob:L52], so they are reached through
    ``system_record.system_data_block``. The frozen ``MOVE`` statements name
    them unqualified because they are unique within the program; the group
    path is spelled out here only because Python requires it.

    Args:
        system_record: The ``SYSTEM-REC`` row the caller already holds. Read
            only; this function mutates nothing.

    Returns:
        A fresh :class:`~acas_posting.records.file_access.RdbData`. The class
        is IMPORTED from the record layer and never redeclared here - one
        record shape, one owner.
    """
    rdb_data = RdbData()

    # All six sending items are `05` items of `03 System-Data-Block.`
    # [copybooks/wssystem.cob:L52], so the record layer exposes them on
    # `SystemRecord.system_data_block` rather than on the record itself. The
    # frozen MOVEs name them UNQUALIFIED - `move RDBMS-DB-Name to DB-Schema` -
    # because a COBOL data name needs qualifying only when it is ambiguous, and
    # these six are unique within the program. Python has no such rule, so the
    # group is named explicitly; the statements themselves are unchanged.
    system_data_block = system_record.system_data_block

    # The six moves, in the frozen source's own order. Each line is one COBOL
    # statement, so a reviewer can diff this block against
    # [common/acas008.cbl:L558-L563] line for line.
    rdb_data.db_schema = _pic_x(system_data_block.rdbms_db_name, 12)
    rdb_data.db_uname = _pic_x(system_data_block.rdbms_user, 12)
    rdb_data.db_upass = _pic_x(system_data_block.rdbms_passwd, 12)
    rdb_data.db_port = _pic_x(system_data_block.rdbms_port, _DB_PORT_WIDTH)
    rdb_data.db_host = _pic_x(system_data_block.rdbms_host, 32)
    rdb_data.db_socket = _pic_x(system_data_block.rdbms_socket, 64)

    return rdb_data


#  ANOMALY A-1  -  THE FIRST-CALL-ONLY GUARD, REPRODUCED AND NOT FIXED

#: The loaded block, or ``None`` before the first load. This one module-level
#: name IS the reproduction of the COBOL's `A` sentinel: `A` starts at zero and
#: is assigned a length on the first call, so a later call finds it non-zero
#: and skips the guarded block. Here `None` is the "not yet called" state and
#: an `RdbData` instance is the "already called" state.
#:
#: NOT guarded by a lock, deliberately. Rule R-3 forbids concurrency outright -
#: no threads, no event loop, no process-level parallelism - and a lock here
#: would imply that concurrent callers exist. Execution is strictly sequential,
#: matching the single-threaded COBOL.
_LOADED_RDB_DATA: RdbData | None = None


def load_rdb_data_once(system_record: SystemRecord) -> RdbData:
    """Load the connection parameters on the first call and never again.

    *** ANOMALY A-1 - REPRODUCED, NOT FIXED (rule R-4) ***

    The credential load in the file handler is wrapped in a first-call-only
    guard [common/acas008.cbl:L526]::

        if       A = zero                        *> so it is being called first time

    whose own comments say what it is for. At the head of the paragraph
    [common/acas008.cbl:L518]::

        *>     Test on very first call only  (So do NOT use var A & B again)

    and immediately above the six moves [common/acas008.cbl:L555-L556]::

        *>  Load up the DB settings from the system record as its not passed on
        *>           hopefully once is enough  :)

    ``A`` is assigned a record length inside the guarded block before any later
    call can test it, and the ``end-if`` [common/acas008.cbl:L564] closes AFTER
    the six moves, so from the second call onward the ENTIRE block - the
    record-length check and the credential load together - is skipped for the
    remainder of the run.

    The observable consequence, which this function reproduces exactly: a
    change to the ``SYSTEM-REC`` row part-way through a run cannot affect that
    run. The second and later callers get the parameters the FIRST caller
    supplied, whatever their own ``SYSTEM-REC`` row carries by then. Re-reading
    would be a defect fixed, and rule R-4 makes a defect fixed a failure.

    Args:
        system_record: The ``SYSTEM-REC`` row. CONSULTED ONLY ON THE FIRST
            CALL; ignored on every later call, exactly as the guard ignores it.

    Returns:
        The one :class:`~acas_posting.records.file_access.RdbData` for this
        run. The same object every time, so a caller cannot be handed a
        different set of parameters than another caller in the same run.
    """
    global _LOADED_RDB_DATA  # noqa: PLW0603 - the `A = zero` sentinel

    if _LOADED_RDB_DATA is None:
        # `if A = zero` [common/acas008.cbl:L526] - the very first call.
        _LOADED_RDB_DATA = rdb_data_from_system_record(system_record)
        _LOG.debug(
            "RDB-Data loaded from SYSTEM-REC "
            "(common/acas008.cbl:L558-L563); "
            "the first-call-only guard at L526 closes it for this run"
        )
    # `end-if` [common/acas008.cbl:L564]. No else branch exists in the frozen
    # source and none is added: a later call simply proceeds with whatever the
    # block already holds.
    return _LOADED_RDB_DATA


def rdb_data_is_loaded() -> bool:
    """Report whether the first-call-only load has already happened.

    The observable form of the COBOL's ``A`` sentinel, published so that a
    test can assert anomaly A-1 rather than infer it.

    Returns:
        ``True`` once :func:`load_rdb_data_once` has run in this process,
        ``False`` before that and after :func:`reset_rdb_data_cache`.
    """
    return _LOADED_RDB_DATA is not None


def reset_rdb_data_cache() -> None:
    """Clear the first-call-only load so the next call reloads.

    THERE IS NO COBOL COUNTERPART, and that is stated plainly rather than
    disguised: nothing in the frozen source clears ``A``. It does not need to,
    because a COBOL run is a process and the sentinel dies with it.

    In Python a test process outlives a "run", and the determinism test a later
    boundary adds has to perform two runs of one scenario IN ONE PROCESS and
    get identical results. Without an
    explicit reset the second run would inherit the first run's parameters and
    the two runs would not be independent - so this function exists to make
    the determinism test able to establish what it claims, not to soften
    anomaly A-1.

    Production callers have no reason to call it: one process is one run, and
    a run loads its parameters once.
    """
    global _LOADED_RDB_DATA  # noqa: PLW0603 - the `A = zero` sentinel

    _LOADED_RDB_DATA = None


#  THE DRIVER PARAMETER SET  -  `common/glpostingMT.cbl:L394-L416`


def _atoi(text: str) -> int:
    """Convert leading digits to an ``int`` the way C's ``atoi`` does.

    *** REPRODUCED, NOT REPAIRED (rules R-3 and R-4) ***

    The C interface the bridges link converts the port with a bare
    ``port = atoi(xport)`` and then hands the result straight to
    ``mysql_real_connect``. ``atoi`` HAS NO FAILURE MODE: it skips leading
    white space, takes an optional sign, consumes as many decimal digits as it
    finds and stops at the first character that is not one, returning 0 if
    there were none at all. So a malformed ``DB-Port`` does not make the
    compiled program report an error - it makes it connect somewhere else, or
    to the default port.

    That is why this module performs NO port validation. Raising on a
    non-numeric port would be a new validation, which rule R-3 forbids, and a
    defect fixed, which rule R-4 makes a failure: a scenario whose
    ``SYSTEM-REC`` held a malformed port would abort under Python and connect
    under the compiled program, and the two runs would then disagree about
    every row.

    The observable consequences, all reproduced:

    * ``"3306"`` -> 3306, the ordinary case.
    * ``""`` -> 0. Zero is what the C then passes as the port argument, and
      the client library reads a zero port as "use your default".
    * ``"33o6"`` -> 33. The digits before the stray letter are kept and the
      rest is discarded silently, so the program connects to port 33.
    * ``"abcde"`` -> 0, i.e. the default port, NOT an error.
    * ``"-330"`` -> -330. The C parameter is an ``unsigned int``, so a
      negative value is reinterpreted as a very large one; either reading is
      refused when the connection is attempted, so the step attribution is
      the same under both.

    Args:
        text: The port characters, already reduced by the ``delimited by
            space`` rule and narrowed to the working-storage item's width.

    Returns:
        The converted value, or 0 when no digits were found.

        >>> _atoi("3306")
        3306
        >>> _atoi("")
        0
        >>> _atoi("33o6")
        33
        >>> _atoi("abcde")
        0
        >>> _atoi("-330")
        -330
        >>> _atoi("+80")
        80
    """
    body = text.lstrip(" \t\n\r\v\f")
    sign = 1
    if body[:1] in {"+", "-"}:
        if body[0] == "-":
            sign = -1
        body = body[1:]
    digits = ""
    for character in body:
        if not character.isdigit() or not character.isascii():
            break
        digits += character
    if not digits:
        return 0
    return sign * int(digits)


# =============================================================================
#  THE TRANSPORT AND CREDENTIAL POLICY  (CWE-798, CWE-295, CWE-319)
# =============================================================================
#  This is the ONE place in the migrated cycle that reaches a real server, so it
#  is the one place where two properties of the frozen source stop being
#  harmless facts about a 1980s accounting package and become live exposures.
#
#  1. THE CREDENTIALS ARE SOURCE LITERALS. `05 RDBMS-User pic x(12) value
#     "ACAS-User"` and `05 RDBMS-Passwd pic x(12) value "PaSsWoRd"`
#     [copybooks/wssystem.cob:L138-L139], each annotated `*> change in setup` by
#     the maintainer. `acas_posting/records/system_record.py` declares them
#     byte-for-byte because `SYSTEM-REC` is a dumped table and its declared
#     defaults are diff-visible (rule R-4), and it publishes them so that this
#     module can RECOGNISE them.
#  2. THE TRANSPORT IS PLAINTEXT. The C interface the bridges link calls
#     `mysql_real_connect(&sql, host, user, passwd, db, port, socket, 0)` with a
#     literal zero client-flag word, so `CLIENT_SSL` is never negotiated and the
#     password crosses the wire in the clear. On a loopback socket that is of no
#     consequence; to a server on another host it is the whole credential and
#     every posted figure, unprotected and unauthenticated.
#
#  WHAT IS NOT DONE ABOUT IT, AND WHY
#  ----------------------------------
#  Reading a credential from the process environment, a dotenv file or a
#  parameter file is NOT an option here, however conventional it would be. Rule
#  R-6 makes two runs of the same scenario byte-identical, and an ambient input
#  is exactly what breaks that; rule R-3 forbids adding anything the frozen
#  source does not have. So the credential keeps arriving where the frozen source
#  puts it - in the `SYSTEM-REC` row this module is handed - and this module never
#  reads its surroundings. A grep of this file for `os.environ`, `getenv` or
#  `dotenv` returns nothing, and it must stay that way.
#
#  WHAT IS DONE INSTEAD: THE CALLER DECLARES, IN CODE, AND THE DEFAULT REFUSES
#  --------------------------------------------------------------------------
#  Both exposures are turned into an EXPLICIT KEYWORD DECLARATION that the
#  caller must make at the call site, and the default value of every one of them
#  refuses. Opening a connection therefore fails closed: a caller that has
#  thought about neither credentials nor transport gets an exception rather than
#  a plaintext connection authenticated by a password published in this
#  repository.
#
#  * A `SYSTEM-REC` still carrying the maintainer's placeholder user or password
#    is refused unless the caller passes
#    `allow_frozen_placeholder_credentials=True`, which is the declaration "I
#    know these are the shipped values and this server is disposable".
#  * A connection to anything other than a loopback address or a Unix socket is
#    refused unless the caller supplies a certificate authority to verify the
#    server against - or declares `isolated_oracle=True`, which is the
#    declaration "this is the parity harness on a private network where the
#    server has no TLS at all", the situation the harness genuinely runs in.
#
#  WHY THIS CHANGES NO BEHAVIOUR THAT IS COMPARED
#  ---------------------------------------------
#  Every refusal RAISES. None of them returns a COBOL status, and that is
#  deliberate: `(FS-Reply 99, We-Error 911)` is what the frozen paragraph
#  produces for a failed connect [copybooks/mysql-procedures.cpy:L127-L128], and
#  manufacturing that pair for a policy refusal would make a refusal
#  indistinguishable from a genuine connect failure - the caller would carry on
#  along the frozen error path as though the server had answered. Raising a type
#  no COBOL path can produce keeps the two apart. It is the same reasoning
#  `_assert_converter_pinned` is given (rule R-2): a broken migration guarantee
#  is not a state the frozen program can be in, so there is nothing to degrade
#  to.
#
#  And once a connection IS permitted, nothing here touches it. The six
#  `RDB-Data` items are marshalled exactly as before, the port still narrows
#  through `pic x(4)`, no value is validated, and the TLS arguments are
#  additional driver keywords that alter the wire and nothing above it. No stored
#  value, no status pair, no statement text and no table dump moves by a
#  character (rules R-3, R-4).
# =============================================================================

#: Host names that name the local machine, compared lower-case.
#:
#: Numeric loopback addresses are NOT listed: they are recognised properly by
#: :func:`ipaddress.ip_address`, which covers the whole of 127.0.0.0/8 and ::1
#: rather than the two spellings someone happened to think of.
LOOPBACK_HOST_NAMES: Final[frozenset[str]] = frozenset(
    {"localhost", "localhost.localdomain"}
)


class ConnectionPolicyError(RuntimeError):
    """A connection was refused by this module's own policy, not by a server.

    Raised, never reported as a COBOL status, for the reason argued in the
    section comment above: a policy refusal must not be mistakable for the
    ``(99, 911)`` the frozen paragraph produces when a server declines.

    ``RuntimeError`` rather than a new hierarchy root, matching
    :class:`ConverterPinningError`, which is raised for the same class of
    reason - a guarantee of the migration itself has not been met.
    """


class FrozenPlaceholderCredentialsError(ConnectionPolicyError):
    """The `SYSTEM-REC` row still carries the maintainer's shipped credentials.

    `05 RDBMS-User pic x(12) value "ACAS-User"` and `05 RDBMS-Passwd pic x(12)
    value "PaSsWoRd"` [copybooks/wssystem.cob:L138-L139] are published in the
    frozen source and in this repository, so a connection authenticated by them
    is a connection anyone reading the source can make. Pass
    ``allow_frozen_placeholder_credentials=True`` to declare that the server is
    disposable and the exposure is intended.
    """


class InsecureTransportError(ConnectionPolicyError):
    """A non-local connection would have crossed the network in the clear.

    Either supply a certificate authority in :class:`TransportSecurity` so the
    server is authenticated and the session encrypted, or declare
    ``isolated_oracle=True`` to state that the target is the parity harness on a
    private network with no TLS available.
    """


@dataclass(frozen=True, slots=True)
class TransportSecurity:
    """The caller's declaration about how the connection may cross the network.

    Frozen and slotted, like every other value object in this layer: a policy is
    a decision the caller has already taken, not something this module edits.

    An instance with every field at its default - which is what
    :func:`mysql_1000_open` uses when the caller passes none - permits a
    loopback or Unix-socket connection and refuses everything else. That is the
    fail-closed default, and it is deliberately the one a caller gets by
    forgetting to think about it.

    Attributes:
        ca_file: Path to the certificate authority bundle the server's
            certificate is verified against. Supplying it turns on TLS with
            BOTH certificate and host-name verification, which is what makes it
            protection rather than decoration (CWE-295): an encrypted session to
            an unverified server defends against nothing, because the server may
            be anyone.
        certificate_file: Path to a client certificate, when the server requires
            one. Must be given together with ``key_file``.
        key_file: Path to the private key for ``certificate_file``.
        isolated_oracle: Declares that the target is the comparison harness on a
            private network whose server has no TLS configured at all - the
            situation the harness genuinely runs in - and that a plaintext
            connection to it is intended. Permits plaintext to a non-local host;
            grants nothing else, and in particular does not admit the frozen
            placeholder credentials, which have their own separate declaration.
    """

    ca_file: str | None = None
    certificate_file: str | None = None
    key_file: str | None = None
    isolated_oracle: bool = False

    def verifies_the_server(self) -> bool:
        """Report whether this policy authenticates and encrypts the session.

        Returns:
            ``True`` when a certificate authority was supplied, which is the
            only configuration this module treats as protected.
        """
        return bool(self.ca_file)

    def driver_arguments(self) -> dict[str, Any]:
        """Render the policy as driver keyword arguments.

        Returns:
            The ``ssl_*`` keywords, or an empty mapping when no certificate
            authority was supplied. The empty case is deliberate: it leaves the
            connect call byte-for-byte as it was before this policy existed, so
            a permitted plaintext connection behaves exactly as the frozen C
            interface's does. Whether the empty case is PERMITTED is decided by
            :func:`_require_permitted_connection`, not here.
        """
        if not self.ca_file:
            return {}
        arguments: dict[str, Any] = {
            "ssl_ca": self.ca_file,
            # Both, always, and never one without the other: `ssl_verify_cert`
            # alone accepts a valid certificate issued to a different name, and
            # `ssl_verify_identity` alone is meaningless without a chain to
            # verify. Together they are what CWE-295 asks for.
            "ssl_verify_cert": True,
            "ssl_verify_identity": True,
            "ssl_disabled": False,
        }
        if self.certificate_file:
            arguments["ssl_cert"] = self.certificate_file
        if self.key_file:
            arguments["ssl_key"] = self.key_file
        return arguments


def _target_is_local(parameters: Mapping[str, Any]) -> bool:
    """Report whether the connect target is on this machine.

    A Unix socket cannot leave the machine, and a loopback address does not
    reach a network, so neither carries the password anywhere an eavesdropper
    can be. Everything else is treated as remote.

    Args:
        parameters: The driver keyword arguments
            :func:`connection_parameters` produced. Only ``unix_socket`` and
            ``host`` are consulted; the TLS keywords are ignored here.

    Returns:
        ``True`` for a socket, an absent host, a loopback host name or any
        loopback IP address; ``False`` otherwise - including for a host name
        that does not resolve to an address here, because this module resolves
        nothing. A name is judged by what it says, never by what a name service
        would say about it, so the verdict cannot change between two runs
        (rule R-6).
    """
    if "unix_socket" in parameters:
        return True

    host = str(parameters.get("host", "")).strip()
    if not host:
        # A blank `DB-Host` omits the key, and the driver's own default is the
        # loopback address 127.0.0.1. `RDBMS-Host` is `value spaces` in the
        # maintainer's defaults [copybooks/wssystem.cob:L143], so this is the
        # ordinary case rather than an edge one.
        return True
    if host.lower() in LOOPBACK_HOST_NAMES:
        return True

    try:
        # `strip("[]")` because a literal IPv6 address is conventionally
        # bracketed in a host field.
        return ipaddress.ip_address(host.strip("[]")).is_loopback
    except ValueError:
        return False


def _require_permitted_connection(
    system_record: SystemRecord,
    parameters: Mapping[str, Any],
    transport: TransportSecurity,
    *,
    allow_frozen_placeholder_credentials: bool,
) -> None:
    """Refuse a connection the caller has not explicitly declared safe.

    The whole of the policy argued in the section comment above, applied in one
    place immediately before the connect call and nowhere else.

    Args:
        system_record: The row the credentials came from.
        parameters: The driver keyword arguments, used to judge locality.
        transport: The caller's transport declaration.
        allow_frozen_placeholder_credentials: The caller's credential
            declaration. ``False`` - the default at every call site - refuses.

    Raises:
        FrozenPlaceholderCredentialsError: The row still carries a shipped
            credential and the caller did not declare that it intends to.
        InsecureTransportError: The target is not local, no certificate
            authority was supplied and no isolated-oracle declaration was made;
            or a client certificate was supplied without its key, or the key
            without the certificate, which cannot authenticate anything.
    """
    if (
        carries_frozen_placeholder_rdbms_credentials(system_record)
        and not allow_frozen_placeholder_credentials
    ):
        raise FrozenPlaceholderCredentialsError(
            "SYSTEM-REC still carries the placeholder RDBMS credentials "
            "declared at [copybooks/wssystem.cob:L138-L139]; supply real "
            "credentials in the row, or pass "
            "allow_frozen_placeholder_credentials=True to declare that this "
            "server is disposable"
        )

    if bool(transport.certificate_file) != bool(transport.key_file):
        raise InsecureTransportError(
            "TransportSecurity needs certificate_file and key_file together: "
            "a client certificate cannot authenticate without its private key"
        )

    if _target_is_local(parameters):
        return

    if transport.verifies_the_server():
        return

    if transport.isolated_oracle:
        # Logged without the host, the account or the schema: this is the one
        # message that says a password is about to cross a network in the clear,
        # and it must not also say to whom (CWE-532).
        _LOG.warning(
            "Mysql-1000-Open: plaintext transport to a non-local server "
            "permitted by the caller's explicit isolated_oracle declaration; "
            "credentials and posted figures are unprotected on this connection"
        )
        return

    raise InsecureTransportError(
        "the connect target is not a loopback address or a Unix socket, so "
        "the credentials from [copybooks/wssystem.cob:L138-L139] and every "
        "posted figure would cross the network in the clear: supply "
        "TransportSecurity(ca_file=...) to verify and encrypt, or declare "
        "TransportSecurity(isolated_oracle=True) for the parity harness"
    )



def connection_parameters(
    rdb_data: RdbData, *, transport: TransportSecurity | None = None
) -> dict[str, Any]:
    """Build the driver's keyword arguments from the ``RDB-Data`` block.

    Reproduces the bridge's own parameter marshalling
    [common/glpostingMT.cbl:L394-L416], which loads the six ``RDB-Data`` items into
    the six working-storage items ``MySQL_real_connect`` is called with. That
    call's argument list is host, USER, password, base, port, socket
    [copybooks/mysql-procedures.cpy:L72-L77], and its second argument is
    ``Ws-Mysql-Implementation`` - anomaly A-3, a variable whose name says nothing
    about the user name it carries [common/glpostingMT.cbl:L402-L404]:

    ============================= ================================ ==========
    ``RDB-Data`` item             COBOL working-storage item       Driver
    ============================= ================================ ==========
    ``DB-Host``     x(32)  [:L60] ``Ws-Mysql-Host-Name``    x(64)  ``host``
    ``DB-UName``    x(12)  [:L58] ``Ws-Mysql-Implementation`` x(64) ``user``
    ``DB-UPass``    x(12)  [:L59] ``Ws-Mysql-Password``     x(64)  ``password``
    ``DB-Schema``   x(12)  [:L57] ``Ws-Mysql-Base-Name``    x(64)  ``database``
    ``DB-Port``     x(5)   [:L62] ``Ws-Mysql-Port-Number``  x(4)   ``port``
    ``DB-Socket``   x(64)  [:L61] ``Ws-Mysql-Socket``       x(64)  ``unix_socket``
    ============================= ================================ ==========

    ``DB-Port`` IS A CHARACTER FIELD, declared ``pic x(5)``
    [copybooks/wsfnctn.cob:L62], and the item it is strung into is narrower still
    at ``pic x(4)`` [copybooks/mysql-variables.cpy:L91], so the port travels
    through the whole COBOL side as text. Two consequences are reproduced:

    * THE NARROWING IS OBSERVABLE. ``STRING`` stops when its receiving item is
      full, so a five-digit port loses its fifth character
      [common/glpostingMT.cbl:L410-L412] and no port above 9999 can be expressed -
      ``"13306"`` reaches the client library as 1330. A limitation of the frozen
      source, not a defect to repair (anomaly A-5).
    * THE CONVERSION CANNOT FAIL. The C interface converts with ``atoi`` and passes
      the result straight on, so a malformed port silently becomes a different port
      or the default. See :func:`_atoi`; NO PORT VALIDATION IS PERFORMED, because a
      new validation is forbidden by R-3 and a defect fixed is a failure under R-4
      (anomaly A-4).

    The widening from characters to the integer the driver wants happens HERE and
    nowhere else, because the C interface takes a numeric fifth argument
    [copybooks/mysql-procedures.cpy:L76] and the Python driver takes an ``int``.
    ``port`` is therefore ALWAYS present in the returned mapping, mirroring the C
    call, which always passes one: a blank ``DB-Port`` yields 0, precisely what the
    C passes and what the client library reads as "use your default port".

    A BLANK TEXT ITEM MEANS UNSET, and omitting its key is how that is expressed.
    The ``delimited by space`` clause on each of the six STRING statements makes an
    all-spaces item contribute nothing, so the C interface receives an empty string
    and its client library reads that as "no value supplied". Two of the six are
    ``value spaces`` in the maintainer's own defaults - ``RDBMS-Host`` and
    ``RDBMS-Socket`` [copybooks/wssystem.cob:L143-L144] - so this is the ordinary
    case, not an edge one. Supplying an empty string instead would ask the driver
    to connect to a host named "".

    THREE SOCKET VALUES ALSO MEAN "NO SOCKET". Before calling
    ``mysql_real_connect`` the C interface compares the socket item against
    ``"0"``, ``"null"`` and ``"NULL"`` and substitutes a null pointer, so those
    spellings behave exactly like a blank item. Reproduced via
    :data:`_SOCKET_MEANS_NONE` (anomaly A-6); without it a ``DB-Socket`` of ``"0"``
    would send the driver looking for a socket file named ``0``.

    THE TRANSPORT KEYWORDS ARE THE ONE ADDITION, AND THEY ARE OPT-IN. The frozen
    C interface passes a literal zero client-flag word, so it negotiates no TLS
    at all; when ``transport`` is omitted this function therefore returns
    precisely the six-item mapping it always did, and the connect call is
    byte-for-byte the frozen one. When a caller supplies a certificate authority,
    its ``ssl_*`` keywords are merged in. They affect the wire and nothing above
    it: no ``RDB-Data`` item is re-read, no value is validated and no stored
    value moves (rules R-3, R-4). Whether a connection without them is PERMITTED
    is decided by :func:`_require_permitted_connection`, not here - this function
    marshals, it does not judge.

    Args:
        rdb_data: The block :func:`load_rdb_data_once` produced.
        transport: The caller's transport declaration, or ``None`` for the
            frozen plaintext behaviour. See :class:`TransportSecurity`.

    Returns:
        The driver keyword arguments: the four text items that are set, plus
        ``port`` always, plus the ``ssl_*`` keywords when ``transport``
        authenticates the server. No pool argument and no session-shaping
        argument appears here; ``autocommit``, ``converter_class`` and the
        client-flag adjustment are added by :func:`mysql_1000_open`, which owns
        them.
    """
    # Each of the six values is extracted exactly as the bridge extracts it -
    # up to the first space - so that a blank item yields "" and an item with
    # an embedded space is truncated where the COBOL truncates it.
    host = cobol_string_delimited_by_space(rdb_data.db_host)
    user = cobol_string_delimited_by_space(rdb_data.db_uname)
    password = cobol_string_delimited_by_space(rdb_data.db_upass)
    database = cobol_string_delimited_by_space(rdb_data.db_schema)
    port_text = cobol_string_delimited_by_space(rdb_data.db_port)
    socket_path = cobol_string_delimited_by_space(rdb_data.db_socket)

    parameters: dict[str, Any] = {}
    if host:
        parameters["host"] = host
    if user:
        parameters["user"] = user
    if password:
        parameters["password"] = password
    if database:
        parameters["database"] = database
    if socket_path and socket_path not in _SOCKET_MEANS_NONE:
        # The C interface substitutes a null pointer for "0", "null" and
        # "NULL", so those three reach the client library as no socket at all.
        parameters["unix_socket"] = socket_path

    # `pic x(5)` -> `pic x(4)` -> int, in that order, because that is the order
    # the frozen source performs it in: the STRING narrows, then `atoi`
    # converts. Doing the conversion first and truncating afterwards would give
    # 13306 where the compiled program gives 1330.
    parameters["port"] = _atoi(port_text[:_WS_MYSQL_PORT_WIDTH])

    # Merged LAST and only when the caller declared a verifying policy, so that
    # the six frozen items are never displaced and the omitted-transport case
    # returns exactly what it returned before this policy existed.
    if transport is not None:
        parameters.update(transport.driver_arguments())

    return parameters


#  THE OPEN OUTCOME  -  WHAT `Mysql-1000-Open` LEAVES BEHIND


@dataclass(frozen=True, slots=True)
class OpenOutcome:
    """Everything ``Mysql-1000-Open`` leaves behind, success or failure.

    Frozen, because an outcome is a fact about something that already
    happened - the same reasoning ``dal/status.py`` gives for
    :class:`~acas_posting.dal.status.DbErrorStatus`.

    The COBOL has no return value: the paragraph writes its results into the
    shared ``File-Access`` record and the caller reads them afterwards. This
    dataclass carries the same set of results so that a Python caller can
    apply them to the record it holds - see :meth:`apply_to_logging_data` -
    without this module having to own the caller's record.
    """

    #: The live connection, or ``None`` if any step failed. The COBOL analogue
    #: is ``Ws-Mysql-Cid``, the handle ``MySQL_init`` populates
    #: [copybooks/mysql-procedures.cpy:L66], declared as a pointer at
    #: [copybooks/mysql-variables.cpy:L65].
    connection: MySQLConnectionAbstract | None

    #: ``Fs-Reply`` [copybooks/wsfnctn.cob:L25]. ``FsReply.SUCCESS`` when all
    #: three steps completed, and ``FsReply.ERROR`` (99) otherwise -
    #: unconditionally, per anomaly A-2
    #: [copybooks/mysql-procedures.cpy:L127].
    fs_reply: FsReply

    #: ``We-Error`` [copybooks/wsfnctn.cob:L23]. On failure this is
    #: ``WeError.RDB_INIT_ERROR`` (911) [copybooks/mysql-procedures.cpy:L128],
    #: whose documented meaning - "Rdb Error during initializing, possibly can
    #: not connect to database" [common/glpostingMT.cbl:L143-L144] - is
    #: accurate on this path. On success it is whatever the caller was already
    #: carrying, because the paragraph writes it only on the error path.
    we_error: int

    #: ``ws-No-Paragraph`` [copybooks/wsfnctn.cob:L48]. On failure, the
    #: :class:`~acas_posting.dal.status.ConnectStep` that failed - 101, 102 or
    #: 103. On success, the value the CALLER was carrying, undisturbed: the
    #: copybook's own changelog records that the three stamps were moved to sit
    #: immediately before the error report precisely so that a successful open
    #: "hides caller para lits if no errors"
    #: [copybooks/mysql-procedures.cpy:L45-L47]. The bridge sets 1 before it
    #: performs the paragraph [common/glpostingMT.cbl:L418], and that 1 is
    #: what survives a clean open.
    ws_no_paragraph: int

    #: ``SQL-Err pic x(5)`` [copybooks/wsfnctn.cob:L49], already fitted to its
    #: picture width by ``status.mysql_1100_db_error``.
    sql_err: str

    #: ``SQL-Msg pic x(512)`` [copybooks/wsfnctn.cob:L50], likewise fitted.
    sql_msg: str

    #: ``SQL-State pic x(5)`` [copybooks/wsfnctn.cob:L51], likewise fitted.
    #: Written by the error paragraph at
    #: [copybooks/mysql-procedures.cpy:L122-L123].
    sql_state: str

    @property
    def opened(self) -> bool:
        """Report whether the connection is usable.

        Returns:
            ``True`` only when a connection was produced AND the reply is
            zero. Both are required: a caller must never treat a non-zero
            ``Fs-Reply`` as usable just because an object is present.

            >>> OpenOutcome(None, FsReply.ERROR, 911, 102, "", "", "").opened
            False
        """
        return self.connection is not None and self.fs_reply == FsReply.SUCCESS

    def apply_to_logging_data(self, logging_data: LoggingData) -> None:
        """Write the diagnostics into the caller's ``Logging-Data`` block.

        Reproduces what the COBOL leaves in the shared record: the three
        diagnostic text fields plus ``ws-No-Paragraph``. ``Fs-Reply`` and
        ``We-Error`` are NOT written here, because they live on ``File-Access``
        itself rather than in this sub-block
        [copybooks/wsfnctn.cob:L23-L25] - the caller sets those on the record
        it already holds, exactly as ``DbErrorStatus.apply_to_logging_data``
        leaves them.

        Args:
            logging_data: The block to update, owned by
                ``records/file_access.py``. Mutated in place, as a COBOL
                ``MOVE`` mutates a record.
        """
        logging_data.ws_no_paragraph = self.ws_no_paragraph
        logging_data.sql_err = self.sql_err
        logging_data.sql_msg = self.sql_msg
        logging_data.sql_state = self.sql_state


# =============================================================================
#  STEP ATTRIBUTION  -  SETTLED BY MEASUREMENT AGAINST THE ORACLE (R-6)
# =============================================================================


def _connect_step_for(errno: int) -> ConnectStep:
    """Decide which COBOL step a single driver failure is attributed to.

    *** ARBITRATED AGAINST COMPILED BEHAVIOUR (R-6). The experiment and every
    measured value are recorded below. ***

    THE QUESTION. ``Mysql-1000-Open`` performs THREE distinct operations and can
    report three distinct step codes: ``MySQL_init`` failing gives 101
    [copybooks/mysql-procedures.cpy:L66-L68], ``MySQL_real_connect`` failing gives
    102 [:L72-L79] and ``MySQL_selectdb`` failing gives 103 [:L82-L84].
    ``mysql-connector-python`` collapses all three into ONE call that initialises,
    connects and selects the schema, and raises ONE exception. So which step code
    does a Python failure carry?

    THE EXPERIMENT. A standalone GnuCOBOL 3.2 program was linked against the
    frozen bridge's own C interface object ``cobmysqlapi.o`` and given the
    connect-field setup the bridges use - every value STRINGed with a trailing
    ``X"00"`` [common/otm5MT.scb:L403-L426], which that C layer requires
    because ``cobapi_trim`` and ``move_to_cob`` size their arguments with
    ``strlen`` while COBOL never NUL-terminates a ``pic x(n)``. It then called
    ``MySQL_init``, ``MySQL_real_connect`` and ``MySQL_selectdb`` in
    ``Mysql-1000-Open``'s own order against MariaDB 10.11.7 on the frozen
    schema, capturing ``return-code`` and ``MySQL_errno`` after each call,
    under nine perturbations.

    THE MEASURED RESULT - perturbation, failing step, server error number and
    the SQLSTATE left behind:

    * nothing perturbed, the control ........ none, errno 0, 00000
    * port with nothing listening ........... 102, errno 2002, HY000
    * wrong password ........................ 102, errno 1045, HY000
    * unknown user .......................... 102, errno 1045, HY000
    * unknown schema, restricted user ....... 102, errno 1044, HY000
    * user with no rights to the schema ..... 102, errno 1044, HY000
    * unknown schema, privileged user ....... 102, errno 1049, HY000
    * selectdb given another name ........... 103, errno 1044, 42000
    * the same, privileged user ............. 103, errno 1049, 42000

    WHAT THAT OVERTURNS. This function previously routed 1049 and 1044 to 103,
    reasoning that they are "precisely the errors ``mysql_select_db``
    produces". The measurement contradicts that twice over:

    * BOTH numbers occur at BOTH steps, so the error number cannot identify
      the step at all. Which of the two appears is decided by the USER'S
      PRIVILEGES - a privileged user is told the schema is unknown (1049), one
      without global visibility is told access is denied (1044) - and not by
      which call failed.
    * They arise at 102 because ``mysql_real_connect`` receives the schema as
      its fourth argument and selects it during the handshake: the bridge's C
      interface passes ``db`` straight through to it
      [presql2-package/cobmysqlapi38.c, ``MySQL_real_connect``]. A schema that
      cannot be selected therefore fails the CONNECT, not the selection.

    WHY 103 IS UNREACHABLE IN THE FROZEN CALL SHAPE. Step 103 failed only when
    ``MySQL_selectdb`` was handed a DIFFERENT name from the one the connect had
    already selected. The bridge never does that: it STRINGs the schema once
    into ``WS-MYSQL-BASE-NAME`` and hands THAT ONE FIELD to both
    ``MySQL_real_connect`` [copybooks/mysql-procedures.cpy:L75] and
    ``MySQL_selectdb`` [:L82]. Re-selecting the schema the handshake already
    selected cannot fail on an unknown-schema or an access ground, so no server
    error number reachable through the bridge attributes to 103.

    THE RESOLUTION ENCODED HERE - two arms, therefore, and not three:

    * **101, ``INIT``** when there is no server error number at all. Measured:
      ``MySQL_init`` returned zero with ``MySQL_errno`` 0 under every one of
      the nine perturbations, because it only allocates and prepares the handle
      and contacts no server. The driver uses a sentinel rather than ``None``,
      so "no server error" is a non-positive ``errno``.
    * **102, ``REAL_CONNECT``** for every positive server error number, 1044
      and 1049 included, because that is where the frozen bridge reports them.

    A MEASURED CONSEQUENCE THE BRIDGE NEVER SEES. After a failed step 102 the
    following ``MySQL_selectdb`` reported 2006 "Server has gone away" in every
    case, there being no connection to select on. ``Mysql-1000-Open`` never
    observes it: it performs the error paragraph and ``go to Mysql-1090-Exit``
    immediately [copybooks/mysql-procedures.cpy:L78-L81], so the number it
    captures is always the true cause and never 2006.

    WHAT IS NOT AMBIGUOUS. The status PAIR is identical whichever step failed,
    ``(FS-Reply 99, We-Error 911)``, because the two statements that set it are
    unguarded [copybooks/mysql-procedures.cpy:L127-L128] - anomaly A-2. So no
    posted figure and no table row can depend on the attribution, which is exactly
    why the question is safe to resolve by documented reasoning while the oracle
    confirms it.

    Args:
        errno: The driver's error number. Non-positive when the driver never
            reached a server.

    Returns:
        The :class:`~acas_posting.dal.status.ConnectStep` to report.

        >>> _connect_step_for(-1)
        <ConnectStep.INIT: 101>
        >>> _connect_step_for(2003)
        <ConnectStep.REAL_CONNECT: 102>
        >>> _connect_step_for(1049)  # measured at 102, never 103
        <ConnectStep.REAL_CONNECT: 102>
        >>> _connect_step_for(1044)  # measured at 102, never 103
        <ConnectStep.REAL_CONNECT: 102>
    """
    if errno <= 0:
        return ConnectStep.INIT
    return ConnectStep.REAL_CONNECT


def _db_error_status(
    *,
    errno: int,
    message: str,
    sql_state: str,
    we_error: int,
) -> DbErrorStatus:
    """Map one connect failure through ``Mysql-1100-Db-Error``.

    Delegates to :func:`~acas_posting.dal.status.mysql_1100_db_error` rather
    than restating the mapping, so ``(99, 911)`` has exactly one
    implementation in the package.

    ``command`` is passed as empty on purpose. That argument feeds ONLY the
    duplicate-key test, which examines ``Ws-Mysql-Command (1:6)``
    [copybooks/mysql-procedures.cpy:L100] and can fire only for error numbers
    1062 and 1022 [:L99]. Neither can arise from opening a connection, and
    ``Mysql-1000-Open`` never writes ``Ws-Mysql-Command`` at all, so the
    duplicate branch is unreachable on this path and there is no statement text
    to report.

    Args:
        errno: The driver's error number.
        message: The driver's error message - the equivalent of
            ``Ws-Mysql-Error-Message`` [copybooks/mysql-variables.cpy:L86].
        sql_state: The driver's SQLSTATE - the equivalent of
            ``WS-Mysql-SqlState`` [copybooks/mysql-variables.cpy:L85].
        we_error: The value ``We-Error`` already held.

    Returns:
        The status the error paragraph would have left behind.
    """
    return mysql_1100_db_error(
        # `call "MySQL_errno" using Ws-Mysql-Error-Number`
        # [copybooks/mysql-procedures.cpy:L97]. Text, because
        # `Ws-Mysql-Error-Number` is `pic x(5)`
        # [copybooks/mysql-variables.cpy:L84] and the duplicate test compares
        # it as characters.
        errno=str(errno) if errno > 0 else "",
        # `call "MySQL_error" using Ws-Mysql-Error-Message` [:L107]
        message=message,
        # `call "MySQL_sqlstate" using WS-MYSQL-SqlState` [:L122]
        sql_state=sql_state,
        command="",
        we_error=we_error,
    )


#  THE CONNECT-TIME ASSERTION  -  RULE R-2 MADE CHECKABLE


def _assert_converter_pinned(connection: MySQLConnectionAbstract) -> None:
    """Verify the pinned converter is really in force on a live connection.

    Rule R-2 names this file for pinning the converter "rather than relying on
    the default". A pinning that is never checked is indistinguishable from a
    default that merely happens to agree, so this function turns the guarantee
    into something that fails loudly the moment it stops holding - on a driver
    upgrade, a changed connection argument, or a caller that replaces the
    converter after connecting.

    Three checks, cheapest first:

    1. **The converter object is an** :class:`AcasConverter`. If the argument
       was dropped, nothing else is worth testing.
    2. **Every pinned hook is still an override.** For each field type the
       schema can produce, the resolved attribute must NOT be the driver base
       class's, and each rejected hook must not be either. This covers all
       five integer widths, both decimal wire types and both string wire types
       without needing a table to read from.
    3. **A live value probe.** :data:`CONVERTER_PROBE_STATEMENT` is executed
       and its three values are checked for exact type and, for the decimal,
       for its declared scale.

    Args:
        connection: A connection that has just been opened.

    Raises:
        ConverterPinningError: On any drift. The caller closes the connection
            before letting this leave :func:`mysql_1000_open`.
    """
    converter = getattr(connection, "converter", None)
    if not isinstance(converter, AcasConverter):
        raise ConverterPinningError(
            "rule R-2: the ACAS numeric converter is not in force - the "
            f"connection is using {type(converter).__name__!r}. Every "
            "connection must be opened with converter_class=AcasConverter so "
            "that no accounting value passes through a binary floating-point "
            "type in transport."
        )

    base = conversion.MySQLConverter
    for field_type, hook in (
        *PINNED_CONVERTER_HOOKS.items(),
        *REJECTED_CONVERTER_HOOKS.items(),
    ):
        if getattr(AcasConverter, hook) is getattr(base, hook):
            raise ConverterPinningError(
                f"rule R-2: converter hook {hook!r} for driver field type "
                f"{FieldType.get_info(field_type)!r} resolves to the driver's "
                "own implementation, so that type would be converted by the "
                "default this file exists to replace."
            )

    with execute_statement(connection, CONVERTER_PROBE_STATEMENT) as cursor:
        probe = cursor.fetchone()

    if probe is None or len(probe) != 3:
        raise ConverterPinningError(
            "rule R-2: the converter probe returned no row, so the pinning "
            f"could not be verified (statement: {CONVERTER_PROBE_STATEMENT})"
        )

    probed_decimal, probed_integer, probed_text = probe

    if not isinstance(probed_decimal, decimal.Decimal):
        raise ConverterPinningError(
            "rule R-2: a DECIMAL(10,2) column arrived as "
            f"{type(probed_decimal).__name__!r} instead of decimal.Decimal. "
            "No accounting value may pass through a binary floating-point "
            "type at any point - not in computation, not in storage, not in "
            "transport - and the 128 in-scope decimal columns all take this "
            "path."
        )
    if str(probed_decimal) != CONVERTER_PROBE_EXPECTED_DECIMAL_TEXT:
        raise ConverterPinningError(
            "rule R-2: a DECIMAL(10,2) column lost its declared scale - "
            f"expected {CONVERTER_PROBE_EXPECTED_DECIMAL_TEXT!r}, got "
            f"{str(probed_decimal)!r}. The scale is part of the stored value "
            "and the state diff compares it."
        )
    # The same fact stated as an exponent rather than as text, because the
    # widest in-scope scale is what a money column carries and a normalised
    # value would silently report a different one.
    if -probed_decimal.as_tuple().exponent != SCHEMA_MAX_DECIMAL_SCALE:
        raise ConverterPinningError(
            "rule R-2: a DECIMAL(10,2) column arrived at exponent "
            f"{probed_decimal.as_tuple().exponent} rather than at the "
            f"{SCHEMA_MAX_DECIMAL_SCALE} decimal places every in-scope money "
            "column declares."
        )
    # `isinstance(x, int)` would accept a bool, which is an int subclass and
    # is not a value any in-scope column can hold, so the type is checked
    # exactly.
    if type(probed_integer) is not int:
        raise ConverterPinningError(
            "rule R-2: a signed integer column arrived as "
            f"{type(probed_integer).__name__!r} instead of int. The 208 "
            "in-scope integer columns carry the COBOL binary family, whose "
            "truncation on divide is integer truncation."
        )
    if type(probed_text) is not str:
        raise ConverterPinningError(
            "rule R-2 support: a character column arrived as "
            f"{type(probed_text).__name__!r} instead of str, so the 177 "
            "in-scope char columns would not compare as text in a state diff."
        )


#  ANOMALY A-8  -  THE ONE PROCESS-GLOBAL HANDLE, REPRODUCED AND NOT FIXED

#: The one connection this process ever has, or ``None`` before the first open.
#: This single module-level name IS the reproduction of the C interface's own
#: single declaration [presql2-package/cobmysqlapi38.c:L71]::
#:
#:     MYSQL            sql, *mysql=&sql;
#:
#: ``sql`` is a file-scope struct, so it exists for the life of the process and
#: survives every close; ``mysql`` always aims at it, so every entry point in
#: that file - ``mysql_init(&sql)`` [:L433], ``mysql_real_connect(&sql, ...)``
#: [:L527], ``mysql_select_db(mysql, ...)`` [:L539], ``mysql_close(mysql)``
#: [:L232], ``mysql_errno(mysql)`` [:L240] - reaches the same connection. The
#: twenty bridges have no way to hold a second one: ``MySQL_init`` copies the
#: address of this struct into whichever ``Ws-Mysql-Cid`` asked
#: [copybooks/mysql-variables.cpy:L65], and no entry point ever reads a handle
#: back, so the pointer a bridge holds is a formality.
#:
#: The Python analogue of "the address of ``sql``" is OBJECT IDENTITY, which is
#: why the object here is reused rather than rebuilt: every handler that has
#: opened holds this exact object, so :func:`mysql_1980_close` closing it is
#: observable to all of them without any of them having to know that.
#:
#: THIS IS NOT A CONNECTION POOL and must never grow into one. A pool holds
#: several connections, hands a caller one it is not otherwise using, and takes
#: it back. This holds exactly one, hands every caller the same one, and takes
#: nothing back. Rule R-3 forbids the former; the frozen C interface requires
#: the latter.
#:
#: NOT guarded by a lock, deliberately, for the reason given at
#: :data:`_LOADED_RDB_DATA`: rule R-3 forbids concurrency outright, so a lock
#: would imply that concurrent callers exist.
_PROCESS_CONNECTION: MySQLConnectionAbstract | None = None


def process_connection() -> MySQLConnectionAbstract | None:
    """Report the one connection this process holds, without touching it.

    The observable form of the C interface's file-scope ``sql`` struct
    [presql2-package/cobmysqlapi38.c:L71], published so that a test can assert
    anomaly A-8 - that twenty bridges share one connection - rather than infer
    it from behaviour.

    Sends nothing to the server and changes nothing: it neither opens, closes,
    reconnects nor pings. A caller wanting the connection to USE must go
    through :func:`mysql_1000_open`, exactly as a bridge must perform
    ``Mysql-1000-Open`` before it can issue a statement.

    Returns:
        The one connection object, live or closed, or ``None`` before the first
        :func:`mysql_1000_open` of the process and after
        :func:`reset_process_connection`.
    """
    return _PROCESS_CONNECTION


def reset_process_connection() -> None:
    """Close the one connection and forget it, so the next open starts clean.

    THERE IS NO COBOL COUNTERPART, and that is stated plainly rather than
    disguised - the same position :func:`reset_rdb_data_cache` is in. Nothing in
    the frozen source discards the ``sql`` struct, because it does not need to:
    a COBOL run is a process, and the struct dies with it.

    In Python a test process outlives a "run". The determinism requirement
    (rule R-6) is that two runs of one scenario IN ONE PROCESS produce identical
    results, and a run that inherited the previous run's live session - possibly
    mid-cursor, possibly already closed by the previous run's last file-close -
    would not be independent of it. So this exists to let a harness or test
    establish a clean starting state, NOT to soften anomaly A-8.

    Production callers have no reason to call it: one process is one run.
    """
    global _PROCESS_CONNECTION  # noqa: PLW0603 - the `MYSQL sql` file-scope struct

    if _PROCESS_CONNECTION is not None:
        _close_quietly(_PROCESS_CONNECTION)
    _PROCESS_CONNECTION = None


def _close_quietly(connection: MySQLConnectionAbstract) -> None:
    """Close one connection the way ``MySQL_close`` closes: without reporting.

    ``MySQL_close`` is declared ``void`` and returns nothing
    [presql2-package/cobmysqlapi38.c:L230-L234], and the frozen paragraph that
    calls it tests nothing afterwards
    [copybooks/mysql-procedures.cpy:L264-L265]. So a close failure cannot
    change control flow in the compiled program, and it must not change it
    here: raising would invent an error path the specification does not have
    (rule R-3, nothing added).

    Args:
        connection: The connection to close. Already-closed is fine - the
            driver tolerates it, and so does ``mysql_close`` on a struct whose
            session has gone.
    """
    try:
        connection.close()
    except Exception as error:  # noqa: BLE001 - `void MySQL_close` reports nothing
        # Redacted for the same reason `_failed_open` redacts: this text is the
        # driver's, so it can name the account and can carry a line feed.
        _LOG.debug(
            "Mysql-1980-Close: driver reported %s on close",
            redact_for_log(str(error)),
        )


#  `Mysql-1000-Open`  -  [copybooks/mysql-procedures.cpy:L63-L85]


def mysql_1000_open(
    system_record: SystemRecord,
    *,
    ws_no_paragraph: int = 0,
    we_error: int = WeError.SUCCESS,
    transport: TransportSecurity | None = None,
    allow_frozen_placeholder_credentials: bool = False,
) -> OpenOutcome:
    """Open the connection, as ``Mysql-1000-Open`` does.

    Reproduces [copybooks/mysql-procedures.cpy:L63-L85] natively. The frozen
    paragraph zeroes two counters [:L64-L65], then makes three foreign calls,
    each guarded by an identical arm that moves a step code to
    ``Ws-No-Paragraph``, performs the error ladder, and leaves::

        call "MySQL_init" using Ws-Mysql-Cid.        [:L66] arm 101 [:L67-L70]
        call "MySQL_real_connect" using Host-Name, Implementation, Password,
             Base-Name, Port-Number, Socket.   [:L72-L77] arm 102 [:L78-L81]
        call "MySQL_selectdb" using Base-Name.       [:L82] arm 103 [:L83-L85]

    Only the third arm omits the ``go to``, because it is already last.

    Five things about it survive the migration:

    * **The one handle.** ``MySQL_init`` does not create a connection - it
      re-points the caller's ``Ws-Mysql-Cid`` at the single file-scope struct
      and re-initialises THAT struct [presql2-package/cobmysqlapi38.c:L431,
      :L433], and ``MySQL_real_connect`` then connects the same struct [:L527].
      So the first open of a process brings :data:`_PROCESS_CONNECTION` into
      being and every later open re-establishes the session IN THAT SAME
      OBJECT, abandoning whatever session it held. Every handler that has
      opened therefore holds one and the same connection - anomaly A-8.
    * The parameter marshalling, including ``Ws-Mysql-Implementation`` in
      the USER slot - anomaly A-3. See :func:`connection_parameters`.
    * The three step codes, imported as
      :class:`~acas_posting.dal.status.ConnectStep`. The driver raises one
      exception for a call doing all three things, so the attribution is a
      recorded ambiguity - see :func:`_connect_step_for`.
    * The unconditional ``(FS-Reply 99, We-Error 911)`` on every failure -
      anomaly A-2 - by delegating to
      :func:`~acas_posting.dal.status.mysql_1100_db_error`.
    * The untouched ``ws-No-Paragraph`` on success, so a clean open "hides
      caller para lits if no errors" [:L45-L47].

    Two do not, both recorded as omissions in the module docstring: the
    ``x"00"`` terminator on each parameter (O-1), and the reset of the two
    dead lock-ladder counters at [:L64-L65] (O-2).

    Two properties are added because the migration requires them, and both
    are argued in the module docstring: ``autocommit`` is enabled, because
    the twenty in-scope bridges contain zero occurrences of COMMIT, ROLLBACK
    and START TRANSACTION and the batch loader's own header records the RDB
    default as ON [common/glbatchLD.cbl:L9-L12]; and the pinned converter is
    installed and then checked. NOTHING IS RETRIED - ``dal/status.py``
    records the backoff ladder as dead code (its anomaly N1), so a failure
    here is final.

    Args:
        system_record: The ``SYSTEM-REC`` row carrying the connection
            parameters. Consulted only on the first call of the run - anomaly
            A-1, see :func:`load_rdb_data_once`.
        ws_no_paragraph: The value the caller already has in
            ``ws-No-Paragraph``. Returned unchanged on success, exactly as the
            frozen paragraph leaves it; the bridge sets 1 before performing the
            paragraph [common/glpostingMT.cbl:L418].
        we_error: The value the caller already has in ``We-Error``. Returned
            unchanged on success, because the paragraph writes that field only
            on the error path.
        transport: How the connection may cross the network. The default -
            ``None``, read as :class:`TransportSecurity` at its own defaults -
            permits a loopback or Unix-socket connection and REFUSES anything
            else, so a caller that has not thought about transport cannot send
            the password across a network in the clear. See the policy section
            of this module.
        allow_frozen_placeholder_credentials: Declares that the caller knows the
            row may still carry `"ACAS-User"` and `"PaSsWoRd"`
            [copybooks/wssystem.cob:L138-L139] and that the target server is
            disposable. The default REFUSES.

    Returns:
        An :class:`OpenOutcome`. On success it carries the live connection -
        THE one process connection, the same object every other caller in this
        process is handed - and ``FsReply.SUCCESS``; on failure no connection,
        the ``(99, 911)`` pair, the step code and the three diagnostic fields.

    Raises:
        FrozenPlaceholderCredentialsError: The row still carries a shipped
            credential and the caller made no declaration. Raised rather than
            reported as ``(99, 911)`` so that a policy refusal can never be
            mistaken for a server declining - see the policy section.
        InsecureTransportError: The connection would have crossed a network
            unprotected, or the transport declaration is internally
            inconsistent. Raised for the same reason.
        ConverterPinningError: If the connection opened but the pinned
            converter is not in force. Not reported as a COBOL status,
            because it is not a condition the frozen program can be in: the
            migration's own transport guarantee has failed and rule R-2
            leaves nothing to degrade to. The connection is closed first.
    """
    global _PROCESS_CONNECTION  # noqa: PLW0603 - the `MYSQL sql` file-scope struct

    declared_transport = (
        TransportSecurity() if transport is None else transport
    )

    rdb_data = load_rdb_data_once(system_record)
    parameters = connection_parameters(rdb_data, transport=declared_transport)

    # BEFORE the connect call, so that a refused connection is never attempted
    # and no credential ever leaves the process. Raises; never returns a status.
    # Evaluated on EVERY call, including the calls that re-use the one process
    # connection: the policy is this caller's declaration about this call, so a
    # caller that declared nothing must be refused even when an earlier caller
    # that declared properly has already opened.
    _require_permitted_connection(
        system_record,
        parameters,
        declared_transport,
        allow_frozen_placeholder_credentials=(
            allow_frozen_placeholder_credentials
        ),
    )

    # THE FULL ARGUMENT SET, ASSEMBLED ONCE AND USED ON EVERY OPEN, because that
    # is what the frozen source does: `ba020-Process-Open` re-STRINGs all six
    # `RDB-Data` items into working storage on every single open
    # [common/glpostingMT.cbl:L394-L416] and `Mysql-1000-Open` hands all six to
    # `MySQL_real_connect` again [copybooks/mysql-procedures.cpy:L72-L77]. So a
    # re-open is re-parameterised, never "resumed with whatever it had".
    driver_arguments: dict[str, Any] = {
        **parameters,
        # AUTOCOMMIT IS ON, AND THE ABSENCE OF A TRANSACTION SCOPE IS
        # DELIBERATE. A census over all twenty in-scope bridges finds zero
        # occurrences of COMMIT, ROLLBACK and START TRANSACTION, so every
        # statement they issue is durable the moment it succeeds. The
        # loaders confirm it from the other side; `common/glbatchLD.cbl`
        # L9-L12 reads, verbatim:
        #
        #     *>  This modules uses commit and rollback so *
        #     *>  you MUST ensure that autocommit is OFF   *
        #     *>   in the rdb settings. It is as default   *
        #     *>   set ON.                                 *
        #
        # i.e. the LOADERS ask for it to be off; the BRIDGES never do, so
        # they run under the ON default. Even the loaders never act on that
        # header - their `perform aa020-Rollback` lines are all commented
        # out and `aa030-Commit` is never performed at all - so the whole
        # frozen tree runs without a reachable COMMIT and the harness
        # database is served with autocommit ON to match
        # [harness/Dockerfile.mariadb]. This module therefore publishes no
        # begin, no commit, no rollback and no transactional context manager -
        # adding any of them would change when rows become visible and so
        # change the state diff. It is also precisely why Agent Action Plan
        # section 0.6.5 can say of the file-abandoning rejection path,
        # verbatim: "The partial state is therefore committed, not rolled
        # back."
        "autocommit": True,
        # RULE R-2, WHICH NAMES THIS FILE. The converter is pinned
        # explicitly rather than left to the driver's default. Honoured by
        # both driver implementations, so `use_pure` is deliberately not
        # passed: the C extension detects a custom converter and hands
        # every value to it instead of converting in C.
        "converter_class": AcasConverter,
        # MULTI-STATEMENT EXECUTION IS TURNED OFF, because the compiled
        # program does not have it. The C interface the bridges link calls
        # `mysql_real_connect(&sql, host, user, passwd, db, port, socket,
        # 0)` - the final argument is the client-flag word and it is a
        # LITERAL ZERO [presql2-package/cobmysqlapi38.c:L527], so
        # CLIENT_MULTI_STATEMENTS is never negotiated and the server rejects
        # a second statement in one query with a syntax error.
        # `mysql-connector-python` sets that flag BY DEFAULT, which would let
        # one `execute` call run two statements; the negative entry unsets it
        # and restores the frozen behaviour. Rule R-6 settles it - the
        # compiled program is the specification - and it is what makes
        # `execute_statement`'s one-statement-per-call guarantee structural
        # rather than a convention.
        "client_flags": [-ClientFlag.MULTI_STATEMENTS],
        # No pool argument of any kind appears here, and none may be added:
        # rule R-3 forbids a connection pool, and the frozen bridges reach one
        # process-global handle rather than borrowing from a set
        # [presql2-package/cobmysqlapi38.c:L71].
    }

    # ANOMALY A-8. `MySQL_init` does not create a connection - it re-points the
    # caller's handle at the ONE file-scope struct and re-initialises THAT
    # struct [presql2-package/cobmysqlapi38.c:L431, :L433]::
    #
    #     *cid = mysql;
    #     rc = mysql_init(&sql) != NULL ? 0 : 1;
    #
    # and `MySQL_real_connect` then connects that same struct [:L527]. So the
    # first open of the process brings the struct into being and every later
    # open RE-ESTABLISHES THE SESSION IN IT, abandoning whatever session it
    # held. `MySQLConnectionAbstract.connect` is the exact analogue: it
    # re-configures and re-connects the object it is called on, in place, so
    # the object's identity - the Python stand-in for `&sql` - is preserved and
    # every handler that has ever opened is still holding the live connection.
    established = _PROCESS_CONNECTION
    try:
        if established is None:
            connection = mysql.connector.connect(**driver_arguments)
        else:
            established.connect(**driver_arguments)
            connection = established
    except mysql.connector.Error as error:
        # A failed re-connect leaves the object in the slot, disconnected -
        # which is what `mysql_init(&sql)` followed by a failing
        # `mysql_real_connect(&sql, ...)` leaves behind: the struct still
        # exists, it simply has no session.
        errno = error.errno if isinstance(error.errno, int) else 0
        return _failed_open(
            step=_connect_step_for(errno),
            errno=errno,
            message=error.msg or str(error),
            sql_state=error.sqlstate or "",
            we_error=we_error,
        )

    # THE STRUCT IS NOW THE LIVE CONNECTION, and it is installed before anything
    # else looks at it because that is the order the C interface establishes:
    # `mysql_init(&sql)` [presql2-package/cobmysqlapi38.c:L433] and
    # `mysql_real_connect(&sql, ...)` [:L527] have already made the one
    # file-scope struct current by the time `Mysql-1000-Open` reaches its next
    # statement. Every handler that opens from here on receives this same
    # object, which is what makes a close by any one of them observable to all
    # of them (anomaly A-8).
    _PROCESS_CONNECTION = connection

    # Checked on EVERY open, exactly as before this slot existed, so the number
    # of probe statements a run issues does not move: each open probed once
    # then and each open probes once now. Rule R-2 admits no conditional
    # enforcement, and the re-open path passes the identical `converter_class`
    # argument, so there is nothing here that would only need checking once.
    try:
        _assert_converter_pinned(connection)
    except BaseException:
        # The connection is unusable under rule R-2, so it is closed rather
        # than leaked. `Mysql-1980-Close` is used so the close path stays
        # single-sourced. No COMMIT precedes it - see that function.
        mysql_1980_close(connection)
        raise

    # A clean open: the paragraph wrote neither `Fs-Reply`, nor `We-Error`, nor
    # `ws-No-Paragraph`, so the caller's own values are handed straight back.
    return mysql_1090_exit(
        OpenOutcome(
            connection=connection,
            fs_reply=FsReply.SUCCESS,
            we_error=we_error,
            ws_no_paragraph=ws_no_paragraph,
            sql_err="",
            sql_msg="",
            sql_state="",
        )
    )


def _failed_open(
    *,
    step: ConnectStep,
    errno: int,
    message: str,
    sql_state: str,
    we_error: int,
) -> OpenOutcome:
    """Assemble the outcome of a failed connect, as the three arms do.

    The three failure arms of ``Mysql-1000-Open`` differ in ONE statement -
    the step code they stamp into ``ws-No-Paragraph``
    [copybooks/mysql-procedures.cpy:L68, :L79, :L84] - and are otherwise
    identical: each performs the same error paragraph, and two of the three
    then jump to the exit while the third simply runs out of statements. So one
    function serves all three, parameterised by the step, and the shared tail
    is written once.

    Args:
        step: Which of the three steps failed.
        errno: The driver's error number, or 0 if the driver never reached a
            server.
        message: The driver's error message.
        sql_state: The driver's SQLSTATE, or ``""`` if it reported none.
        we_error: The value ``We-Error`` already held.

    Returns:
        The failure :class:`OpenOutcome`, carrying no connection.
    """
    status = _db_error_status(
        errno=errno,
        message=message,
        sql_state=sql_state,
        we_error=we_error,
    )
    # The step code, its name and the two ACAS status values are this module's
    # own values and carry nothing sensitive. THE DRIVER'S SQLSTATE AND MESSAGE
    # DO: a failed connect is precisely the failure whose message names the
    # account and the host - "Access denied for user 'ACAS-User'@'localhost'" -
    # and it can carry a carriage return that forges a second log record. Both
    # therefore go through `dal/status.py`'s log-safety functions, and the error
    # number is reported as a stable category instead of raw (CWE-117, CWE-532).
    # The `OpenOutcome` returned below still carries all three diagnostic fields
    # exactly as the driver produced them, so no status, no linkage field and no
    # compared value is affected by the redaction.
    _LOG.error(
        "Mysql-1000-Open failed at step %d (%s): "
        "FS-Reply=%d WE-Error=%d SQLSTATE=%r category=%s %s",
        int(step),
        step.name,
        int(status.fs_reply),
        int(status.we_error),
        sanitise_for_log(status.sql_state.strip(), limit=5),
        db_error_log_category(errno, sql_state),
        redact_for_log(status.sql_msg.strip()),
    )
    return mysql_1090_exit(
        OpenOutcome(
            connection=None,
            fs_reply=status.fs_reply,
            we_error=status.we_error,
            ws_no_paragraph=int(step),
            sql_err=status.sql_err,
            sql_msg=status.sql_msg,
            sql_state=status.sql_state,
        )
    )


def mysql_1090_exit(outcome: OpenOutcome) -> OpenOutcome:
    """The single convergence point of the open paragraph.

    ``Mysql-1090-Exit`` [copybooks/mysql-procedures.cpy:L87-L88] is a label
    followed by ``exit.`` and nothing else. It exists because two of the three
    failure arms transfer to it - ``go to Mysql-1090-Exit`` at [:L70] and
    [:L81] - and because the caller performs the paragraph range
    ``MYSQL-1000-OPEN THRU MYSQL-1090-EXIT``
    [common/glpostingMT.cbl:L419], which needs a named end.

    Both of those ``go to``s are class-3 transfers under the Agent Action
    Plan's taxonomy - a jump to a section's trailing exit label becomes a
    ``return`` - so in Python they are ``return mysql_1090_exit(...)``. Keeping
    the paragraph as a named function preserves the paragraph-to-function
    correspondence rule R-5 requires even where the transfer mechanism has
    changed, and gives the traceability document a target to point at.

    It transforms nothing, because the COBOL label transforms nothing.

    Args:
        outcome: The outcome the arriving arm assembled.

    Returns:
        That same outcome, unchanged.
    """
    return outcome


#  `Mysql-1980-Close`  -  [copybooks/mysql-procedures.cpy:L264-L265]


def mysql_1980_close(connection: MySQLConnectionAbstract | None) -> None:
    """Close the connection, as ``Mysql-1980-Close`` does.

    The frozen block is two lines [copybooks/mysql-procedures.cpy:L264-L265]::

        Mysql-1980-Close.
            call "MySQL_close".

    and the bridge reaches it on a file-close request,
    ``PERFORM MYSQL-1980-CLOSE THRU MYSQL-1999-EXIT``
    [common/glpostingMT.cbl:L443].

    NO COMMIT PRECEDES THE CLOSE, and none is added. Under autocommit there is
    nothing outstanding to make durable, so a COMMIT here would be added
    behaviour with an observable consequence - it would suppress the partial
    state that Agent Action Plan section 0.6.5 requires the file-abandoning
    rejection path to leave behind. Equally there is no ROLLBACK: the frozen
    close discards nothing.

    Closing is idempotent and tolerant, matching ``MySQL_close``, which takes
    no argument and reports no status: the frozen paragraph cannot fail and
    neither can this. A ``None`` connection - the shape a failed open returns -
    is accepted and ignored, so a caller may close unconditionally.

    *** ANOMALY A-8 - REPRODUCED, NOT FIXED (rule R-4) ***

    ``call "MySQL_close"`` PASSES NOTHING
    [copybooks/mysql-procedures.cpy:L264-L265], and the C entry point it
    reaches takes nothing [presql2-package/cobmysqlapi38.c:L230-L234]::

        void MySQL_close(void)
        {
            mysql_close(mysql);
            return;
        }

    so a bridge cannot nominate WHICH connection to close: there is only the
    one file-scope handle [:L71] and closing is closing THAT. This function
    therefore closes :data:`_PROCESS_CONNECTION` and not the argument, and the
    consequence is the anomaly: a posting program holding several files open
    and closing any one of them leaves the rest unusable until something
    re-opens. Honouring the argument instead would make each handler's close
    local, and a defect fixed is a failure.

    The argument is still accepted, and is still the right thing to pass, for
    two reasons. It keeps every call site a faithful transcription of the
    frozen ``PERFORM MYSQL-1980-CLOSE THRU MYSQL-1999-EXIT`` at the point where
    the bridge issues it, and it lets the one caller that is NOT a bridge -
    :func:`mysql_1000_open` discarding a connection whose converter would not
    verify - name the object it means. When the argument is some other object
    than the one in the slot, BOTH are closed, because leaking the argument
    would be worse than closing it and the frozen source has no such case to
    diverge from.

    The object stays in the slot after closing, deliberately: ``sql`` is a
    static struct, so a close empties it without destroying it and a later
    ``mysql_init(&sql)`` [:L433] revives the very same struct. Keeping the
    object is how a later :func:`mysql_1000_open` can re-connect it in place
    and so hand every handler that is still holding it a live connection again.

    Args:
        connection: The connection the calling paragraph believes it is
            closing, or ``None``. Not used to decide WHAT is closed - see
            above.
    """
    global _PROCESS_CONNECTION  # noqa: PLW0603 - the `MYSQL sql` file-scope struct

    # `mysql_close(mysql)` - the one handle, whatever the caller named.
    if _PROCESS_CONNECTION is not None:
        _close_quietly(_PROCESS_CONNECTION)
    if connection is not None and connection is not _PROCESS_CONNECTION:
        # Not the process handle. No frozen counterpart exists, because no
        # bridge can hold a second connection; closing it is the only
        # non-leaking thing to do and it changes nothing a bridge can observe.
        _close_quietly(connection)
    mysql_1999_exit()


def mysql_1999_exit() -> None:
    """The convergence point of the close block.

    ``Mysql-1999-Exit`` [copybooks/mysql-procedures.cpy:L267-L268] is, like
    ``Mysql-1090-Exit``, a label followed by ``exit.``. It is the named end of
    the range the bridge performs [common/glpostingMT.cbl:L443], and it is
    reproduced as a function for the same rule R-5 reason: every paragraph in
    the migrated surface has a correspondingly named function, so the
    traceability document can be generated rather than curated.

    It does nothing, because the COBOL label does nothing.
    """
    return


#  CURSOR ACQUISITION  -  KEEPING A DEAD SESSION ON THE STATEMENT'S ERROR PATH


class _UnavailableCursor:
    """A cursor-shaped stand-in that reports the failure when a statement runs.

    WHY THIS EXISTS, AND WHY IT IS NOT AN INVENTION.

    The frozen bridges issue a statement with ONE foreign call - ``call
    "MySQL_query" using Ws-Mysql-Command`` [copybooks/mysql-procedures.cpy:L148,
    :L165] - and test ONE return code immediately afterwards [:L149, :L166].
    There is no separate "obtain a cursor" step to fail at, so every failure a
    bridge can see, including a session that another bridge has closed
    (anomaly A-8), is reported BY THE STATEMENT and lands on
    ``Mysql-1100-Db-Error``.

    ``mysql-connector-python`` splits that one call in two - ``cursor()`` then
    ``execute()`` - and the split moves the failure: on a closed connection it
    is ``cursor()`` that raises, before any statement text is offered. Every
    handler guards the statement, because that is where the frozen source puts
    the test; none guards cursor acquisition, because the frozen source has
    nothing there to guard. The result would be a Python exception escaping the
    data-access layer on a path where the compiled program reports a status -
    a difference introduced purely by the decomposition.

    This class removes the difference by carrying the driver's own error forward
    to the point the frozen source tests: :meth:`execute` raises exactly the
    exception ``cursor()`` raised, so the handler's existing statement guard
    sees it and maps it through the bridge's own failure arm. Nothing decides
    WHICH status results - that is the handler's and
    ``dal/cursor_state.py``'s already-settled mapping, unchanged.

    It is deliberately inert in every other respect: no statement is issued, no
    row is produced, and closing does nothing.
    """

    __slots__ = ("_error",)

    #: A closed connection has no result set, so there is no row description to
    #: report. Present because callers read it defensively before fetching.
    description: Final[None] = None

    #: ``MySQL_affected_rows`` on a failed statement reports "unknown" rather
    #: than a count [copybooks/mysql-procedures.cpy:L178]; nothing here is ever
    #: read, because :meth:`execute` raises first, and zero is the value the
    #: handlers' own ``getattr(cursor, "rowcount", 0)`` defaults to.
    rowcount: Final[int] = 0

    def __init__(self, error: BaseException) -> None:
        """Capture the failure to re-raise when a statement is attempted.

        Args:
            error: The exception ``connection.cursor()`` raised.
        """
        self._error = error

    def execute(
        self, operation: str, params: Sequence[Any] | None = None
    ) -> NoReturn:
        """Report the captured failure, as ``MySQL_query`` reports its own.

        Args:
            operation: The statement the caller meant to issue. Accepted so
                that the signature matches a real cursor's; never sent.
            params: The parameters the caller meant to bind. Likewise never
                sent.

        Raises:
            BaseException: The error ``connection.cursor()`` raised, unchanged,
                so the caller's own error mapping sees the driver's own errno,
                SQLSTATE and message rather than a substitute.
        """
        raise self._error

    def fetchone(self) -> NoReturn:
        """Report the captured failure.

        Unreachable through any handler, because :meth:`execute` raises first.
        Present so that a caller which fetches without executing cannot silently
        read ``None`` from a dead session and take it for an empty result.

        Raises:
            BaseException: The error ``connection.cursor()`` raised.
        """
        raise self._error

    def fetchall(self) -> NoReturn:
        """Report the captured failure, for the reason :meth:`fetchone` gives.

        Raises:
            BaseException: The error ``connection.cursor()`` raised.
        """
        raise self._error

    def close(self) -> None:
        """Do nothing, because nothing was opened.

        Every caller closes its cursor in a ``finally``, so this must not
        raise - a raise from a ``finally`` would replace the caller's own
        status with a misleading exception, which is the same reasoning
        :func:`execute_statement` gives for swallowing a cursor-close failure.
        """
        return


def acquire_cursor(connection: MySQLConnectionAbstract) -> Any:
    """Obtain a cursor, or a stand-in that fails when the statement runs.

    The single cursor-acquisition point for the handler modules that issue
    their statement themselves rather than through :func:`execute_statement` -
    the positioning verbs, which need the cursor and the statement in the
    caller's hands. Those handlers guard the statement, exactly where the
    frozen source tests ``Return-Code`` [copybooks/mysql-procedures.cpy:L149,
    :L166], and this function makes sure the guard is reached even when the
    session has already gone.

    That case is real rather than theoretical: anomaly A-8 means any bridge's
    ``Mysql-1980-Close`` closes the one process handle
    [presql2-package/cobmysqlapi38.c:L230-L234], so a handler still holding it
    can be asked to read on a connection the driver will refuse a cursor for.
    The compiled program reports that as a failed statement; so does this.

    Nothing is retried and nothing reconnects here. ``dal/status.py`` records
    the lock-retry ladder as dead code, and a silent reconnect would hide
    anomaly A-8 - a defect fixed, which rule R-4 counts as a failure. Reviving
    the connection is ``Mysql-1000-Open``'s job and the caller's decision.

    Args:
        connection: The connection :func:`mysql_1000_open` returned, live or
            not.

    Returns:
        The driver's cursor when one can be obtained; otherwise an inert
        stand-in whose ``execute`` raises the driver's own error, so the
        caller's existing failure arm produces the status.
    """
    try:
        return connection.cursor()
    except Exception as error:  # noqa: BLE001 - the bridge tests a code, not a type
        _LOG.debug(
            "cursor acquisition refused (%s); the failure is carried to the "
            "statement, where the frozen source tests it "
            "[copybooks/mysql-procedures.cpy:L149, :L166]",
            redact_for_log(str(error)),
        )
        return _UnavailableCursor(error)


def cursor_is_unavailable(cursor: object) -> bool:
    """Report whether :func:`acquire_cursor` returned the stand-in.

    Only one caller needs this, and only because it caches: ``acas005``'s
    ``_require_cursor`` keeps one cursor for the life of the open, modelling the
    single result pointer ``TP-GLLEDGER-REC USAGE POINTER``
    [common/nominalMT.cbl:L293]. Caching a stand-in there would make a dead
    session STICK: the failure would outlive the close that caused it and
    survive a later ``Mysql-1000-Open``, whereas the frozen handle is revived in
    place by ``mysql_init(&sql)`` [presql2-package/cobmysqlapi38.c:L433] and
    every holder of it can read again. Anomaly A-8 is symmetric, and this keeps
    the second half of it intact.

    Args:
        cursor: Whatever :func:`acquire_cursor` returned.

    Returns:
        ``True`` when it is the stand-in, so the caller must use it once and
        discard it rather than retain it.
    """
    return isinstance(cursor, _UnavailableCursor)


#  STATEMENT EXECUTION  -  ONE STATEMENT, BOUND PARAMETERS, NO OPTIMISATION


@contextmanager
def execute_statement(
    connection: MySQLConnectionAbstract,
    statement: str,
    parameters: Sequence[Any] = (),
) -> Iterator[MySQLCursorAbstract]:
    """Execute exactly one statement and yield its cursor.

    The shared execution path for every handler module, corresponding to the
    frozen copybook's ``Mysql-1200-Select`` [copybooks/mysql-procedures.cpy:
    L147-L150] and ``Mysql-1210-Command`` [:L164-L178], both of which issue a
    single ``call "MySQL_query"`` and then test the return code. The caller
    fetches from the yielded cursor, mirroring the way a bridge stores the
    result and walks it row by row rather than being handed a materialised
    list.

    IDENTIFIERS MUST ALREADY BE QUOTED. This function binds VALUES and never
    interpolates them, so ``statement`` arrives with its table and column names
    already passed through :func:`quote_identifier` - exactly as a bridge
    assembles ``"SELECT * FROM " "`GLPOSTING-REC`" " WHERE " ...``
    [common/glpostingMT.cbl:L623-L625]. Values travel as ``%s`` placeholders
    and are bound by the driver.

    NO OPTIMISATION IS PERFORMED, AND NONE MAY BE ADDED. Prepared-statement
    caching, multi-statement execution, batching and result prefetch are all
    forbidden here, because the exact sequence of statements is what the
    scenario state diff compares - Agent Action Plan section 0.3.3 objects to
    an ORM on precisely that ground, that it "would obscure the exact statement
    ordering that the state diff is sensitive to" - and section 0.8.4 settles
    the wider question: "Any performance work is therefore out of scope by
    construction, not merely unrequested." So each call creates one cursor,
    issues one statement in the caller's order, and closes that cursor.
    Multi-statement execution is not merely avoided here but DISABLED on the
    connection, so passing two statements is refused by the server.

    Args:
        connection: A connection from :func:`mysql_1000_open`, so the pinned
            converter applies to everything fetched through it.
        statement: One SQL statement, identifiers already backtick-quoted and
            values expressed as ``%s`` placeholders.
        parameters: The values to bind, in the statement's own order. Empty by
            default, for a statement that carries no placeholder.

    Yields:
        The cursor the statement was executed on, positioned before the first
        row. Closed when the block ends, whether or not it raised.
    """
    cursor = connection.cursor()
    try:
        # One `execute` per call, so one statement per call. The guarantee is
        # structural rather than a convention: `mysql_1000_open` unsets
        # CLIENT_MULTI_STATEMENTS, matching the literal-zero client-flag word
        # the C interface passes, so a second statement in this text is a
        # SERVER-SIDE SYNTAX ERROR rather than a silent second execution.
        # Parameters are bound by the driver and never formatted into the text.
        cursor.execute(statement, tuple(parameters))
        yield cursor
    finally:
        # The cursor is closed on every path. Any rows the caller chose not to
        # fetch are discarded first, because the driver refuses to close a
        # cursor whose result is unread and that refusal would otherwise
        # replace the caller's own exception with a misleading one.
        # THIS IS CLEANUP, NOT PREFETCH. It runs only after the caller has
        # finished with the cursor, nothing read here is returned to anyone,
        # and it changes neither which statements are issued nor their order -
        # which is what the state diff compares. `consume_results` is the
        # driver's own name for exactly this operation and is present on both
        # implementations; it is resolved defensively because the abstract base
        # class does not declare it.
        discard_unread = getattr(connection, "consume_results", None)
        if discard_unread is not None:
            try:
                discard_unread()
            except mysql.connector.Error as error:
                _LOG.debug(
                    "execute_statement: discarding the unread result "
                    "reported %s",
                    redact_for_log(str(error)),
                )
        try:
            cursor.close()
        except mysql.connector.Error as error:
            # A cursor that will not close is not a condition the frozen
            # source has an error path for, and raising from a `finally` would
            # hide the caller's own failure. It is recorded and dropped.
            _LOG.debug(
                "execute_statement: cursor close reported %s",
                redact_for_log(str(error)),
            )
