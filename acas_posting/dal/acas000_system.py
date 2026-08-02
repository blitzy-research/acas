"""``acas000`` - the System file handler and the four bridges it reaches.

WHAT THIS MODULE OWNS
=====================

One COBOL file handler, [common/acas000.cbl], and the four one-way
COBOL-to-MySQL bridge programs it reaches - ``systemMT``, ``dfltMT``,
``finalMT`` and ``sys4MT`` - reimplemented as SQL against the frozen table
definitions in [mysql/ACASDB.sql]. Nothing else. No other handler is reached
from here, no facade is imported, and no program module is touched.

The entity-to-table spine this module is the whole of, from Agent Action Plan
section 0.2.1.1:

===================  ================  ============  ==================  =========================
Entity facade        Handler           Bridge        MySQL table         Record copybook
===================  ================  ============  ==================  =========================
System               ``acas000`` key 1 ``systemMT``  ``SYSTEM-REC``      [copybooks/wssystem.cob]
System defaults      ``acas000`` key 2 ``dfltMT``    ``SYSDEFLT-REC``    [copybooks/wsdflt.cob]
System final         ``acas000`` key 3 ``finalMT``   ``SYSFINAL-REC``    [copybooks/wsfinal.cob]
System totals        ``acas000`` key 4 ``sys4MT``    ``SYSTOT-REC``      [copybooks/wssys4.cob]
===================  ================  ============  ==================  =========================

``acas000`` IS NOT A TABLE HANDLER - IT IS A DISPATCHER
=======================================================

Every other numbered handler owns one table. This one owns four, and three of
its properties contradict what a reader would reasonably assume. Each is
proven by a specific line of the frozen source rather than asserted.

FOUR LINKAGE PARAMETERS, NOT FIVE. The first name in the ``USING`` list is
COMMENTED OUT [common/acas000.cbl:L309-L315], verbatim::

    Procedure Division Using *>      System-Record

                             WS-System-Record   *> with images for the other three record types as same size

                             File-Access
                             File-Defs
                             ACAS-DAL-Common-data.

so the effective list is four items. The facade copybook says the same thing
in the maintainer's own words [copybooks/Proc-ACAS-FH-Calls.cob:L20-L25]::

    acas000.       *> System and dflt, final and system-record-4 NOTE that this FH only has four
    *>                                           parameters (no system-record from FD)
        call     "acas000" using System-Record
                                File-Access
                                File-Defs
                                ACAS-DAL-Common-Data.

:func:`dispatch` therefore takes exactly those four, in that order, so a
reviewer can diff the argument lists side by side.

FIVE DISPATCH BRANCHES, NOT FOUR. Agent Action Plan section 0.4.1.5 describes
this module as "Four-way dispatch by key number to four tables". THE SOURCE
SUPERSEDES THAT DESCRIPTION: ``ba015-Test-Ends`` has five ``when`` arms
[common/acas000.cbl:L574-L600] and the fifth calls the same bridge as the
first [common/acas000.cbl:L595-L599], verbatim::

    when  5          *> support for PY may be
          call     "systemMT" using File-Access
                                    ACAS-DAL-Common-data
                                    WS-System-Record
          end-call

The handler's own changelog records why [common/acas000.cbl:L161]::

    *> 14/10/25 vbc - 3.3.01 Pre-Support for RRN (File-Key-No) = 5 for Payroll if ever used.

Five arms are implemented. Narrowing to four would contradict the source.

ONE BUFFER, FOUR REINTERPRETATIONS - ANOMALY N9. All five arms pass the SAME
``01``-level ``WS-System-Record`` [common/acas000.cbl:L578, :L583, :L588,
:L593, :L598]; only a trailing comment on each names a different layout. The
reason is that the other three record copybooks are NOT DECLARED in this
program at all [common/acas000.cbl:L296-L301], under the maintainer's own
``OOPS``, verbatim::

    *> Here are the other three records held as relative, in the system file
    *>   OOPS, not actually used here or by a call.
    *> copy "wsdflt.cob".
    *> copy "wsfinal.cob".
    *> copy "wssys4.cob".

and the linkage comment states the consequence outright
[common/acas000.cbl:L311]: "with images for the other three record types as
same size". So in the compiled system the four layouts occupy ONE storage
area and each bridge reinterprets those bytes.

THIS MODULE MODELS THAT EXPLICITLY RATHER THAN QUIETLY PRESENTING FOUR
INDEPENDENT RECORDS. :func:`dispatch` takes ONE record parameter whose type is
the union of the four layouts, exactly as the COBOL has one buffer, and
``File-Key-No`` selects which layout that buffer is to be read as. The
handler's own paragraphs say whose job it is to put the right layout there
[common/acas000.cbl:L455 and :L468]: "caller must issue MOVE". A caller that
selects key 2 while the buffer holds a ``SystemRecord`` has made the mistake
the COBOL would answer with reinterpreted bytes; Python has types, so it is
answered with a ``TypeError`` naming N9. That is a representation consequence
of the target language, not an added validation of data (rule R-3).

SEVEN VERBS, AND ONE OF THEM IS SPELLED ODDLY
=============================================

The facade publishes seven System verbs and no more
[copybooks/Proc-ACAS-FH-Calls.cob:L190-L230]: ``System-Open`` (function 1,
access type 2), ``System-Open-Input`` (1, 1), ``System-Open-Output`` (1, 3),
``System-Close`` (2, access type zeroed first), ``System-Read-Indexed``
(``fn-Read-Indexed``), ``System-Write`` (``fn-Write``) and ``System-ReWrite``
(``fn-re-write``).

``System-ReWrite`` CARRIES A CAPITAL W [copybooks/Proc-ACAS-FH-Calls.cob:L227]
where every other entity in that copybook spells the verb ``-Rewrite``. The
spelling is recorded, not normalised.

THERE IS NO ``Read-Next``, NO ``Start`` AND NO ``Delete``. The handler has no
paragraph for any of them - its own dispatch comment says so
[common/acas000.cbl:L384]: "6 is spare / unused, no delete (8) or start (9)" -
so none is implemented here. Adding one would publish a verb the compiled
system does not have.

``acas000`` is also the ONLY dispatch paragraph in the facade copybook with no
``move 1 to File-Key-No`` before its ``call``; ``acas004`` [:L28],
``acas005`` [:L36], ``acas006`` [:L44], ``acas007`` [:L52] and ``acas008``
[:L60] all set it. THE CALLER OWNS THE KEY for this handler.

THE TWO STORES, AND WHY ONLY ONE OF THEM IS MIGRATED
====================================================

The compiled handler supports two stores and picks between them at run time
[common/acas000.cbl:L344-L356], verbatim including the maintainer's emphasis::

    *>   All programming must be directly requested, ONLY.
    *>
    *>  Unique for acas000 ONLY we check for FA-RDBMS status in wsfnctn as the ones in system-record
    *>   can be altered to direct acas000 to process the other processing mode (cobol / RDB)
    *>    as well as the system-record being temporarily over-written by the other record types being
    *>     read or written out
    *>      so a value of 66 in FA-RDBMS means take that value for mode (rdb) instead otherwise it is 00.
    *>
         if       FA-RDBMS-Flat-Statuses = "66"     *> same as Cobol-File-Used = 1 = RDB (wsfnctn)
                  perform ba-Process-RDBMS            *>   MUST CHANGE ALL OTHER MODULES
                  go to AA-Main-Exit
         end-if

Note what that comment is actually describing: the system record's own store
flags cannot be trusted here BECAUSE THE BUFFER GETS OVERWRITTEN BY THE OTHER
RECORD TYPES. The maintainer is documenting anomaly N9 as the reason this one
handler reads its store selector out of ``File-Access`` instead.

The value ``"66"`` is itself undocumented: the two condition names on
``FA-File-System-Used`` are zero and 1 [copybooks/wsfnctn.cob:L73-L81] and
``FA-File-Duplicates-In-Use`` is annotated "NO LONGER USED other than for a
'6' = rdb" [copybooks/wsfnctn.cob:L82]. Six appears in neither ``88``. The
sentinel is reproduced as written and the contradiction recorded.

THE FLAT STORE IS A RELATIVE FILE, AND IT IS A RECORDED OMISSION. Its
``SELECT`` [copybooks/selsys.cob] is verbatim::

    select  system-file     assign        file-0
                            access        dynamic
                            organization  is relative
                            relative key  is rrn
                            status        fs-reply.

so the four records are relative records 1 to 4 of one file whose name comes
from ``File-Defs`` - which is why ``File-Defs`` is a parameter at all. Agent
Action Plan section 0.1.1 maps every indexed-file verb onto "Data-access
module method issuing SQL against the frozen table", section 0.2.1.2 lists no
indexed-file engine among the Python files to be created, and section 0.5.1
adds no dependency that could provide one. The relative-file store is
therefore OUT OF SCOPE, and this module says so out loud: the five flat-file
paragraphs reproduce every field their COBOL sets - status codes, log fields,
``rrn``, ``Cobol-File-Status`` - and then raise
:exc:`RelativeFileStoreNotMigratedError` at the one statement that has no
target in the migration's store. A caller reaches the migrated path the same
way the compiled system does: by putting ``"66"`` in
``FA-RDBMS-Flat-Statuses``, exactly as [common/acas000.cbl:L352] requires.
Silently serving those verbs out of MySQL instead would substitute one store
for another, which is a behaviour change and so a failure under rule R-4.

THE LOG IDENTITY IS PATH-DEPENDENT - ANOMALY N-log
==================================================

``aa010-main`` sets it once [common/acas000.cbl:L324-L325], verbatim::

    move     0      to WS-Log-System.   *> 0 = Params, 1 = IRS, 2=GL, 3=SL, 4=PL, 5=Stock, 4 FH logging
    move     10     to WS-Log-File-No.  *> RDB, File/Table

(the Agent Action Plan cites L327-L328 for these two moves; the correct
locator is L324-L325, and the correction is recorded rather than applied
silently.)

``ba010-Test-WS-Rec-Size`` then overwrites the file number
[common/acas000.cbl:L521]::

    move     20 to WS-Log-File-no.        *> for FHlogger

and that single statement is the WHOLE of ``ba010``, which falls through into
``ba012-Test-WS-Rec-Size-2`` [common/acas000.cbl:L523]. The two paths reach
the section differently and therefore see different values:

* the relative-file path performs the SECOND paragraph only
  [common/acas000.cbl:L359] ``perform ba012-Test-WS-Rec-Size-2.``, entering
  below L521, so ``WS-Log-File-No`` stays 10;
* the RDB path performs the whole SECTION [common/acas000.cbl:L353]
  ``perform ba-Process-RDBMS``, entering at ``ba010``, so it becomes 20.

Both fit, because ``WS-Log-File-No`` is ``pic 99``
[copybooks/wsfnctn.cob:L54]. The sibling handler ``acas008`` does the same
thing with different numbers - 15 then 25 - so the Agent Action Plan's
expectation of "25 as in acas008" does not hold here; the measured value for
``acas000`` is 20, and that is what is reproduced.

THE ANOMALIES THIS MODULE REPRODUCES, NEVER FIXES
=================================================

Rule R-4, quoting Agent Action Plan section 0.8.2 verbatim: "There is no test
suite: compiled COBOL execution is the behavioral specification, defects
included. A defect reproduced is correct; a defect fixed is a failure."
Section 0.7.4 conflict C-4 prescribes how quality is expressed instead - "a
comment at each reproduction site citing the COBOL locator" - so every entry
below is also commented at the line that reproduces it, and every entry
belongs in ``docs/migration/anomaly-log.md``.

N7  THE HANDLER'S OWN ERROR TABLE IS STALE. It still reads
    [common/acas000.cbl:L185] ``998* = File-Key-No Out Of Range not 1, 2 or 3
    or 4.`` although key 5 was added on 14/10/25 [common/acas000.cbl:L161] and
    the guard was widened with it [common/acas000.cbl:L335]. The IMPLEMENTED
    bound is reproduced - ``< 1 or > 5`` - and the contradiction recorded.

N8  THE GUARD'S NARROWNESS IS THE ANOMALY. It fires for three functions only
    [common/acas000.cbl:L331-L340], so an out-of-range ``File-Key-No`` on
    open, close, read-next, start or delete passes SILENTLY - no message, no
    counter, no trace. Not extended, however obviously safer that would be.
    THIRD FACE: what such a key then reaches is ``ba015-Test-Ends``, whose
    ``evaluate`` has no ``when other`` either [common/acas000.cbl:L574-L600],
    so NO bridge is called and NO status is written and the caller reads back
    the values it passed in. Reproduced as a silent return, because Agent
    Action Plan section 0.6.5 requires a clean rejection with no database
    effect to stay "equally silent".

N9  ONE BUFFER, FOUR REINTERPRETATIONS. Stated in full above.

N-log  THE LOG FILE NUMBER IS 10 ON ONE PATH AND 20 ON THE OTHER. Stated in
    full above.

N-key  ``File-Key-No`` IS DOCUMENTED THREE INCOMPATIBLE WAYS.
    [copybooks/wsfnctn.cob:L42-L43] gives range 1 through 3 with Stock-specific
    meanings; [common/acas000.cbl:L330-L332] gives 1 = params, 2 = default,
    3 = final, 4 = system totals; [common/acas000.cbl:L335] permits 1 through
    5. ``dal/status.py`` already publishes both ranges as
    ``FILE_KEY_NO_DOCUMENTED_RANGE`` and ``FILE_KEY_NO_GUARD_RANGE`` and its
    own comment says the handler module "will reproduce the guard; this module
    only records the contradiction". This is that module. All three
    documentations are recorded and none is resolved.

N-sign  THE BRIDGES DROP THE SIGN OF EVERY NEGATIVE VALUE THEY WRITE.
    Measured against the compiled oracle, not inferred. All four bridges build
    their statement text through one edited field
    [common/systemMT.cbl:L260, common/sys4MT.cbl:L250]::

        01  WS-MYSQL-EDIT      PIC -Z(18)9.9(9).

    which is 30 characters with a FIXED sign at position 1, nineteen integer
    digit positions at 2 through 20, the point at 21 and nine fraction digits
    at 22 through 30. The seven substrings the four bridges take -
    ``(11:10)``, ``(13:08)``, ``(16:05)``, ``(17:04)``, ``(18:03)``,
    ``(19:02)`` for the integer part and ``(22:02)`` for the fraction - each
    span exactly the host variable's own integer digits, ending at position
    20. NONE OF THEM INCLUDES POSITION 1. Measured on GnuCOBOL 3.2, a host
    variable ``PIC S9(08)V9(02) COMP`` holding -1234.56 yields text
    ``1234.56``; -99999999.99 yields ``99999999.99``; -0.05 yields ``0.05``;
    and ``PIC S9(05) COMP`` holding -42 yields ``42``. So ``sys4MT``, whose
    twenty host variables are signed [common/sys4MT.cbl:L316-L335] and whose
    twenty columns are signed ``decimal(10,2)``
    [mysql/ACASDB.sql:L1378-L1397], STORES A NEGATIVE LEDGER TOTAL AS ITS
    ABSOLUTE VALUE, and so does ``systemMT`` for its one signed host variable
    ``HV-SL-NEXT-REC`` [common/systemMT.cbl:L465]. Reading keeps the sign;
    only writing and rewriting lose it. Both halves of that asymmetry are
    reproduced.

N-unsigned  A NEGATIVE VALUE MOVED INTO AN UNSIGNED HOST VARIABLE BECOMES ITS
    ABSOLUTE VALUE. Agent Action Plan section 0.6.8 lists this as an ambiguity
    that "must be measured rather than assumed"; measured under the
    repository's default arithmetic - no dialect flag, no arithmetic
    directive, no truncation flag anywhere - ``move -42`` into ``PIC 9(05)
    COMP`` stores 00042 and ``compute 0 - 42`` into ``PIC 9(10) COMP`` stores
    0000000042. That is what the forty-two signedness drifts in ``SYSTEM-REC``
    do to a negative value.

N-hvload  FIVE ``systemMT`` HOST VARIABLES ARE NEITHER LOADED NOR UNLOADED.
    ``HV-COMPANY-EMAIL`` [common/systemMT.cbl:L346],
    ``HV-STATS-DATE-PERIOD`` [:L373], ``HV-PL-AUTOGEN`` [:L418],
    ``HV-PL-NEXT-REC`` [:L419] and ``HV-PL-APPROP-AC6`` [:L490] each appear at
    exactly three kinds of site and nowhere else - their declaration, the
    ``MySQL_fetch_record`` argument list, and the two statement builders.
    Neither ``bb000-HV-Load`` [:L1061-L1240] nor ``bb100-UnloadHVs``
    [:L1245-L1298] mentions any of them. The consequence runs both ways: on a
    write the five carry only what ``initialize TD-SYSTEM-REC`` [:L1069] left
    - zero for a numeric, space for a character - and that is what reaches the
    row, destroying the caller's data; on a read they are fetched and then
    never moved into the record, so the caller never sees them.

N-key1  THE PRIMARY-KEY HOST VARIABLE IS NEVER UNLOADED. In ``systemMT`` the
    move is commented out with its reason [common/systemMT.cbl:L1255]
    ``*>     move     HV-SYSTEM-REC-KEY  not wanted and is always 1``; in
    ``sys4MT`` ``bb100-UnloadHVs`` [common/sys4MT.cbl:L794-L822] simply has no
    such move. A key read back from the database does not reach the caller.

N-occurs33  ``dfltMT`` CANNOT REACH THE LAST ENTRY OF ITS OWN TABLE.
    [copybooks/wsdflt.cob] declares ``occurs 33`` and the record class carries
    33 entries, but every loop in the bridge bounds at 32 - the read
    [common/dfltMT.cbl:L532], the range guard [:L559], the write [:L600] and
    the rewrite [:L643] - and even the paragraph comment says "Getting the 32
    rows" [:L459]. Entry 33 can never be written and can never be read.
    ``finalMT`` bounds at 26 [common/finalMT.cbl:L532], which IS the full
    count for [copybooks/wsfinal.cob], so it loses nothing. The asymmetry is
    preserved.

N-deadcond  A CONDITION THAT CANNOT HOLD. [common/dfltMT.cbl:L551-L552] tests
    ``if return-code = -1 or A > 32 or = zero``; ``A`` starts at 1 and only
    ever increments, so ``= zero`` is unreachable. Carried as written.

N-eofclear  THE READ LOOP'S END-OF-FILE STATUS IS THROWN AWAY. Both
    ``dfltMT`` and ``finalMT`` set ``10`` into ``fs-reply`` and ``WE-Error``
    inside the loop and then zero both unconditionally after it
    [common/dfltMT.cbl:L589, common/finalMT.cbl:L597], so a table holding
    fewer rows than the record has entries reports SUCCESS with a partly
    filled record.

N-fdcreds  THE RDB PATH TAKES ITS CREDENTIALS FROM A FILE BUFFER IT NEVER
    READ. [common/acas000.cbl:L557-L562] loads them from ``System-Record`` -
    the FILE SECTION record, [copybooks/fdsys.cob] - and not from the linkage
    record the caller passed. On the RDB path no relative-file read has
    happened, so that buffer holds whatever it holds. The migration has no
    FILE SECTION, so the only system record available is the linkage one; the
    substitution and its reason are recorded at the reproduction site.

N-ab  THE CHANGELOG DISAGREES WITH THE DECLARATION.
    [common/acas000.cbl:L270-L271] declares ``A`` and ``B`` as ``pic 9(4)``
    while the changelog entry at [common/acas000.cbl:L156] says they were
    changed to ``pic 999``. Recorded; the declaration governs.

THE BRIDGES DIVERGE FROM ONE ANOTHER, AND THAT IS PRESERVED
===========================================================

Four bridges, one shape, thirteen measured differences. Each is carried in
:class:`BridgeProfile` as data with its locator rather than smoothed into a
common path, because Agent Action Plan section 0.3.3 warns that anything else
"would obscure the exact statement ordering that the state diff is sensitive
to".

1.  ``dfltMT`` and ``finalMT`` HAVE NO ``bb000-HV-Load`` AND NO
    ``bb100-UnloadHVs``. Their paragraph inventories contain neither; they
    load and store their host variables with inline moves inside the loop that
    walks their ``OCCURS`` table. ``systemMT`` and ``sys4MT`` have both
    sections. (``irsdfltMT`` and ``irsfinalMT`` are the only other two bridges
    in the whole set with this property, and they belong to other modules.)
2.  THE LOW KEY IS QUOTED IN THREE BRIDGES AND BARE IN THE FOURTH.
    ``systemMT`` writes ``"000" delimited by size``
    [common/systemMT.cbl:L670]; the other three write ``'"000"'``.
3.  THE LOG TAG AFTER POSITIONING IS ``">000"`` IN ``systemMT``
    [common/systemMT.cbl:L697] and ``"000"`` in the other three.
4.  THE ERROR-NUMBER TEST IS ONE CHARACTER WIDE IN ``systemMT``
    [common/systemMT.cbl:L708, :L916, :L954, :L1010] - ``(1:1) not = "0"`` -
    and three characters wide in the other three - ``not = "0  "``.
5.  ONLY ``systemMT`` CAPTURES SQLSTATE. It calls ``MySQL_sqlstate`` and moves
    the result into ``SQL-State`` [common/systemMT.cbl:L706-L707]; the other
    three never populate that field.
6.  ONLY ``systemMT`` TESTS SQLSTATE ON THE DUPLICATE PATH, adding
    ``or Sql-State = "23000"`` [common/systemMT.cbl:L959] to the two error
    numbers the others test.
7.  THE FREE PARAGRAPH REPORTS ITSELF AS 18 IN ``systemMT``
    [common/systemMT.cbl:L1037] and 20 IN THE OTHER THREE.
8.  ONLY ``systemMT`` CLOSES THE LOG ON A CLOSE
    [common/systemMT.cbl:L1052-L1056].
9.  ONLY ``sys4MT`` GUARDS ON AN INCOMING NON-ZERO STATUS, at three sites
    dated 28/09/16 [common/sys4MT.cbl:L538-L541, :L642-L645, :L702-L705].
10. ``dfltMT``'s ENTIRE DUPLICATE-KEY CHECK IS COMMENTED OUT
    [common/dfltMT.cbl:L616-L632] while the same block is live in ``finalMT``
    [common/finalMT.cbl:L616-L628], ``sys4MT`` [common/sys4MT.cbl:L646-L658]
    and ``systemMT`` [common/systemMT.cbl:L950-L965].
11. ``finalMT`` CLEARS THE ERROR AFTER LOGGING IT
    [common/finalMT.cbl:L629-L633, :L685-L689]; ``dfltMT`` does not.
12. THE REWRITE LOOP LEAVES EARLY IN ``dfltMT`` [common/dfltMT.cbl:L699] AND
    RUNS ON IN ``finalMT``; and ``dfltMT`` sets its paragraph number INSIDE
    the loop [common/dfltMT.cbl:L660] where ``finalMT`` sets it BEFORE
    [common/finalMT.cbl:L641].
13. THE OPEN TAG IS SET BEFORE THE OPEN IN ``sys4MT``
    [common/sys4MT.cbl:L456-L459] AND AFTER IT IN THE OTHER THREE
    [common/systemMT.cbl:L623-L634, common/dfltMT.cbl:L429-L440,
    common/finalMT.cbl:L425-L436], so a FAILED open leaves ``"OPEN SYS4"`` in
    the log field for one bridge and spaces for the other three.

Two further divergences are matters of value rather than shape and live in the
profile too: ``sys4MT`` writes its duplicate test as ``or "1022"`` without
repeating the ``=`` [common/sys4MT.cbl:L652] where ``finalMT`` and
``systemMT`` write ``or = "1022"``; and the rewrite predicate names the
``OCCURS`` subscript in ``dfltMT`` and ``finalMT`` but a bare literal ``"1"``
in ``sys4MT`` [common/sys4MT.cbl:L688] and ``systemMT``
[common/systemMT.cbl:L992].

TWO PRIMARY KEYS EXIST ONLY IN THE BRIDGE
=========================================

This module is the clearest local proof of the preserved user requirement in
Agent Action Plan section 0.8.2: "The maintainer's one-way COBOL-to-MySQL
bridge defines the authoritative record-layout to table mapping - it is the
data dictionary for this migration."

``SYSDEFLT-REC`` has four columns against a 33-entry ``OCCURS`` table, and
``SYSFINAL-REC`` has two against a 26-entry one. In both, the primary key is
the ``OCCURS`` SUBSCRIPT MATERIALISED AS A COLUMN - a column no copybook
declares. The bridges derive it on write from the loop variable
[common/dfltMT.cbl:L612, common/finalMT.cbl:L613] and use it on read as the
slot to store into [common/dfltMT.cbl:L579-L581, common/finalMT.cbl:L587],
each with the same trailing comment: ``*> KEY = table position``. The other
two keys are bridge-derived too, from a literal rather than a subscript
[common/systemMT.cbl:L1070, common/sys4MT.cbl:L769].

Field metadata is therefore DERIVED, never transcribed. Every column list in
this module comes from ``loader.entries_for_table`` in the dictionary's own
``COLUMN-ORDINAL`` order, every conversion from ``loader.drift_for`` and
``loader.derivation_for``, and every mapping cites ``loader.cite``. That order
was verified against the source rather than trusted: for ``SYSTEM-REC`` all
169 entries reproduce ``systemMT``'s ``bb200-Insert`` column order, its
``bb300-Update`` column order AND its ``MySQL_fetch_record`` host-variable
order exactly, and the same holds for ``SYSTOT-REC``'s 21. Agent Action Plan
section 0.8.1 makes the ordering a directive: "Data dictionary first ... it is
what prevents fields being transcribed by eye."

Two citation corrections are recorded here rather than applied silently, in
the manner ``dal/cursor_state.py`` records its own: the Agent Action Plan and
this module's brief place the log identity at L327-L328 when it is at
L324-L325, and describe the four tables as carrying "zero column-level
DEFAULT" when ``SYSTEM-REC.PASS-WORD`` carries ``DEFAULT ''``
[mysql/ACASDB.sql:L1219]. Neither changes behaviour: every statement this
module issues names every column, so no default is ever exercised.

WHAT THIS MODULE MAY NOT DO
===========================

* Rule R-1: no COBOL at run time. No child process, no foreign-function
  interface, no COBOL compiler, no C interface object, nothing imported from
  the parity harness. Every bridge is reimplemented as SQL here.
* Rule R-2: no binary floating-point value anywhere. Money is
  :class:`decimal.Decimal`, the binary family is :class:`int`, and no
  ``Decimal`` is ever built out of an inexact value.
* Rule R-3: only ``SELECT``, ``INSERT``, ``UPDATE`` and ``DELETE`` against the
  four in-scope tables. No schema statement of any kind, no migration tool, no
  object-relational mapping layer, no pool, no thread, no coroutine. Execution
  is strictly sequential, matching the single-threaded COBOL. No validation
  the COBOL does not have.
* Rule R-5: one function per COBOL paragraph, named after it, with its
  locator; every column cited to its dictionary entry; every deliberate
  omission recorded as an omission.
* Rule R-6: no clock, no entropy, no unordered iteration reaching statement
  text. Statement order is the COBOL's order.

There is NO user rules document for this project - ``review_rules`` reports
that none was provided - so rules R-1 to R-6 are quoted from Agent Action Plan
section 0.7.2 above, and everything the plan is silent on is held to ordinary
enterprise practice.
"""

from __future__ import annotations

import dataclasses
import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from decimal import ROUND_DOWN, Decimal
from types import MappingProxyType
from typing import Any, Final, Union, cast

from acas_posting.dal.connection import (
    OpenOutcome,
    TransportSecurity,
    acquire_cursor,
    cobol_string_delimited_by_space,
    execute_statement,
    load_rdb_data_once,
    mysql_1000_open,
    mysql_1090_exit,
    mysql_1980_close,
    mysql_1999_exit,
    quote_identifier,
)
from acas_posting.dal.cursor_state import (
    SEQUENTIAL_READ_START,
    CursorOutcome,
    CursorSlot,
    CursorStateTable,
    key_of_reference,
    read_next,
)
from acas_posting.dal.status import (
    FILE_KEY_NO_DOCUMENTED_RANGE,
    FILE_KEY_NO_GUARD_RANGE,
    SQL_ERR_WIDTH,
    SQL_MSG_WIDTH,
    SQL_STATE_WIDTH,
    AccessType,
    DbErrorStatus,
    FileFunction,
    FsReply,
    LogSystem,
    WeError,
    end_of_file_status,
    is_duplicate_key_bridge_level,
    mysql_1100_db_error,
    sanitise_for_log,
)
from acas_posting.dictionary import loader
from acas_posting.records.file_access import FileAccess
from acas_posting.records.file_defs import FileDefs
from acas_posting.records.system_dflt import SysDefaultRecord
from acas_posting.records.system_final import SysFinalRecord
from acas_posting.records.system_record import SystemRecord
from acas_posting.records.system_record_4 import SystemRecord4
from acas_posting.records.test_data_flags import AcasDalCommonData

_LOG: Final = logging.getLogger(__name__)

#: The one buffer of anomaly N9, as a type. In the compiled handler this is a
#: single `01`-level item [common/acas000.cbl:L311] that four bridges each
#: reinterpret; the union names the four readings without pretending the
#: compiled system had four items.
SystemFileRecord = Union[
    SystemRecord,
    SysDefaultRecord,
    SysFinalRecord,
    SystemRecord4,
]


__all__: Final[tuple[str, ...]] = (
    # Sorted deterministically - plain `sorted()` order over the public names,
    # matching every other module in this package.
    "BRIDGES_BY_FILE_KEY_NO",
    "BridgeProfile",
    "ColumnPlan",
    "DFLT_MT",
    "FILE_KEY_NO_RANGES_AS_DOCUMENTED",
    "FINAL_MT",
    "HANDLER_PROGRAM",
    "HandlerState",
    "LOG_FILE_NO_FLAT_FILE_PATH",
    "LOG_FILE_NO_RDB_PATH",
    "NEVER_LOADED_HOST_VARIABLES",
    "NEVER_UNLOADED_HOST_VARIABLES",
    "OCCURS_LOOP_BOUNDS",
    "OCCURS_SUBSCRIPT_PRIMARY_KEYS",
    "PUBLISHED_VERBS",
    "RDBMS_STORE_SELECTOR",
    "RECORD_TYPE_BY_FILE_KEY_NO",
    "RelativeFileStoreNotMigratedError",
    "SYSTEM_MT",
    "SYSTEM_REC_ROUTES",
    "SYS4_MT",
    "SYSTOT_REC_ROUTES",
    "SystemFileRecord",
    "TABLES_BY_FILE_KEY_NO",
    "WS_FILE_KEY_WIDTH",
    "aa010_main",
    "aa020_process_open",
    "aa030_process_close",
    "aa050_process_read_indexed",
    "aa070_process_write",
    "aa090_process_rewrite",
    "aa100_bad_function",
    "aa999_main_exit",
    "aa_exit",
    "aa_main_exit",
    "ba010_test_ws_rec_size",
    "ba012_test_ws_rec_size_2",
    "ba015_test_ends",
    "ba_process_rdbms",
    "ba_rdbms_exit",
    "ca_process_logs",
    "column_plans_for",
    "configure_transport",
    "dflt_mt",
    "dispatch",
    "final_mt",
    "handler_state",
    "key_range_guard_applies",
    "reset_handler_state",
    "sys4_mt",
    "system_mt",
)


#  SECTION 1 - ORIGIN AND IDENTITY


#: `77  prog-name          pic x(17)    value "acas000 (3.3.01)".`
#: [common/acas000.cbl:L266]. The version digits matter: 3.3.01 is the release
#: that added the fifth dispatch arm [common/acas000.cbl:L161].
HANDLER_PROGRAM: Final[str] = "acas000 (3.3.01)"

#: `move 0 to WS-Log-System.` [common/acas000.cbl:L324]. Zero is the
#: parameters subsystem, which `dal/status.py` publishes by name.
LOG_SYSTEM: Final[LogSystem] = LogSystem.PARAMS

#: `move 10 to WS-Log-File-No.` [common/acas000.cbl:L325] - what the
#: relative-file path is left with, because it enters the size-check section
#: BELOW the overwrite. Anomaly N-log.
LOG_FILE_NO_FLAT_FILE_PATH: Final[int] = 10

#: `move 20 to WS-Log-File-no.` [common/acas000.cbl:L521] - what the RDB path
#: is left with, because `perform ba-Process-RDBMS` [common/acas000.cbl:L353]
#: enters the section AT that statement. Anomaly N-log. Not 25: that is the
#: sibling handler `acas008`'s value, and the Agent Action Plan's expectation
#: of 25 here does not match the source.
LOG_FILE_NO_RDB_PATH: Final[int] = 20

#: `if FA-RDBMS-Flat-Statuses = "66"` [common/acas000.cbl:L352]. Two `pic 9`
#: items read as one two-character group [copybooks/wsfnctn.cob:L72-L83].
#: Neither item has a `88` for 6, which is recorded, not corrected.
RDBMS_STORE_SELECTOR: Final[str] = "66"

#: `WS-File-Key pic x(64) value spaces` [copybooks/wsfnctn.cob:L52], whose own
#: comment records that it was "increased to 64-- 30/12/16".
WS_FILE_KEY_WIDTH: Final[int] = 64

#: `05  File-Key-No             pic 9.` [copybooks/wsfnctn.cob:L46] - ONE
#: digit, which is why `string "Read Indexed " File-Key-No` contributes a
#: single character and why 5 is the largest value the field can hold beyond
#: the four the handler documents. Measured on the compiled oracle: the field
#: at 4 produced `Read Indexed 4`.
FILE_KEY_NO_DIGITS: Final[int] = 1

#: The three function codes `aa010-main`'s key-range guard covers, and ONLY
#: these three [common/acas000.cbl:L333-L341]. Anomaly N8: an out-of-range key
#: on open, close, read-next, start or delete passes silently, because the
#: `evaluate` has no `when other`.
KEY_RANGE_GUARDED_FUNCTIONS: Final[frozenset[int]] = frozenset(
    {
        int(FileFunction.READ_INDEXED),
        int(FileFunction.WRITE),
        int(FileFunction.RE_WRITE),
    }
)

#: The three `WS-No-Paragraph` values the relative-file paragraphs report:
#: 201 open [common/acas000.cbl:L392], 202 close [:L437], 204 read indexed
#: [:L460], 206 write [:L469], 208 rewrite [:L479].
PARAGRAPH_NO_OPEN: Final[int] = 201
PARAGRAPH_NO_CLOSE: Final[int] = 202
PARAGRAPH_NO_READ_INDEXED: Final[int] = 204
PARAGRAPH_NO_WRITE: Final[int] = 206
PARAGRAPH_NO_REWRITE: Final[int] = 208

#: The bridges keep their OWN `ws-No-Paragraph` series, unrelated to the
#: handler's. Verified per bridge: 1 open [common/systemMT.cbl:L582,
#: common/dfltMT.cbl:L432, common/finalMT.cbl:L433, common/sys4MT.cbl:L458],
#: 2 close [common/systemMT.cbl:L622, common/sys4MT.cbl:L497], 3 the read
#: positioning [common/systemMT.cbl:L681, common/sys4MT.cbl:L520], 4 the fetch
#: [common/systemMT.cbl:L724, common/finalMT.cbl:L530], 10 write
#: [common/systemMT.cbl:L948, common/dfltMT.cbl:L599, common/sys4MT.cbl:L637]
#: and 17 rewrite [common/systemMT.cbl:L980, common/dfltMT.cbl:L660,
#: common/finalMT.cbl:L639, common/sys4MT.cbl:L671]. The free paragraph's
#: number diverges and is carried on the profile instead.
BRIDGE_PARAGRAPH_NO_OPEN: Final[int] = 1
BRIDGE_PARAGRAPH_NO_CLOSE: Final[int] = 2
BRIDGE_PARAGRAPH_NO_POSITION: Final[int] = 3
BRIDGE_PARAGRAPH_NO_FETCH: Final[int] = 4
BRIDGE_PARAGRAPH_NO_WRITE: Final[int] = 10
BRIDGE_PARAGRAPH_NO_REWRITE: Final[int] = 17

#: Where each table-shaped record keeps its `OCCURS` table. `dfltMT` walks
#: `Def-Group` 33 times [copybooks/wsdflt.cob] and `finalMT` walks `AR1` 26
#: times [copybooks/wsfinal.cob]; the per-column routes in
#: `SYSDEFLT_REC_ROUTES` and `SYSFINAL_REC_ROUTES` are relative to ONE
#: occurrence, so this is the route to the table itself. An empty route means
#: the occurrence IS the value, which is `finalMT`'s shape.
OCCURS_TABLE_ROUTES: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType(
    {
        "SYSDEFLT-REC": ("def_group",),
        "SYSFINAL-REC": ("ar1",),
    }
)

#: `move 941 to WE-Error` / `move 41 to FS-Reply` [common/acas000.cbl:L397-398]
#: for an open on an already-open file. NEITHER VALUE HAS A NAMED MEMBER in
#: `dal/status.py` - its `WeError` has no 941 and its `FsReply` no 41 - so both
#: are carried here as the literals the handler writes, with the locator. The
#: handler's own error table calls 941 "File already opened.  with fs-reply =
#: 41. Should not happen!" [common/acas000.cbl:L192].
WE_ERROR_FILE_ALREADY_OPEN: Final[int] = 941
FS_REPLY_FILE_ALREADY_OPEN: Final[int] = 41

#: `move 10 to WE-Error` on every end-of-data path in all four bridges
#: [common/systemMT.cbl:L905, :L919, common/dfltMT.cbl:L519, :L561, :L577,
#: common/finalMT.cbl:L515, :L549, :L565, common/sys4MT.cbl:L550, :L599,
#: :L613]. 10 is a FILE STATUS value, and `WeError` has no member for it
#: because no error table lists one - the bridges simply copy `FS-Reply`'s 10
#: into `WE-Error` as well. Carried as the literal, with the locators.
#: ANOMALY N-key, as data. ``File-Key-No`` is documented THREE incompatible
#: ways and nothing reconciles them, so all three are recorded and none is
#: resolved: the copybook that DECLARES the field names range 1 thru 3 with
#: Stock-specific meanings [copybooks/wsfnctn.cob:L42-L43] - that is
#: ``FILE_KEY_NO_DOCUMENTED_RANGE``, imported from dal/status so the two
#: modules cannot drift; this handler's own comment names 1=params, 2=default,
#: 3=final, 4=system totals [common/acas000.cbl:L330-L332]; and its error
#: table still says "not 1, 2 or 3 or 4" [common/acas000.cbl:L185] a year
#: after key 5 arrived [common/acas000.cbl:L161]. The code, which is what
#: governs, permits 1 thru 5 [common/acas000.cbl:L335] - that is
#: ``FILE_KEY_NO_GUARD_RANGE``. ANOMALY N7 is precisely this gap.
FILE_KEY_NO_RANGES_AS_DOCUMENTED: Final[Mapping[str, tuple[int, int]]] = (
    MappingProxyType(
        {
            "copybooks/wsfnctn.cob:L42-L43": FILE_KEY_NO_DOCUMENTED_RANGE,
            "common/acas000.cbl:L330-L332": (1, 4),
            "common/acas000.cbl:L185": (1, 4),
            "common/acas000.cbl:L335": FILE_KEY_NO_GUARD_RANGE,
        }
    )
)

#: `move 35 to fs-Reply` [common/acas000.cbl:L405] when an `open input` of the
#: relative file fails. Also unnamed in `dal/status.py`; 35 is the ANSI file
#: status for a non-optional file that is not present.
FS_REPLY_OPEN_INPUT_FAILED: Final[int] = 35

#: `move 1024 ...` is not in the source; this is `function Length` of the one
#: record definition, which [copybooks/wssystem.cob:L7] gives as "File size
#: 1024 with fillers" and [copybooks/fdsys.cob:L8] as "1024 bytes or larger".
#: The number is used only to make the `A = zero` first-call sentinel non-zero
#: [common/acas000.cbl:L525]; the COMPARISON's outcome does not depend on it,
#: because [copybooks/fdsys.cob:L11] copies the SAME copybook `acas000` renames
#: at [common/acas000.cbl:L288], so `A` and `B` are equal by construction and
#: `A < B` can never hold. See :func:`ba012_test_ws_rec_size_2`.
SYSTEM_RECORD_DECLARED_LENGTH: Final[int] = 1024

#: The seven verbs the facade publishes for this entity, in its own order
#: [copybooks/Proc-ACAS-FH-Calls.cob:L190-L230], each with the function code
#: and access type that paragraph sets. `System-ReWrite` keeps its capital W
#: [:L227]; every other entity in that copybook spells it `-Rewrite`.
PUBLISHED_VERBS: Final[Mapping[str, tuple[FileFunction, AccessType | int]]] = (
    MappingProxyType(
        {
            "System-Open": (FileFunction.OPEN, AccessType.I_O),
            "System-Open-Input": (FileFunction.OPEN, AccessType.INPUT),
            "System-Open-Output": (FileFunction.OPEN, AccessType.OUTPUT),
            "System-Close": (FileFunction.CLOSE, 0),
            "System-Read-Indexed": (FileFunction.READ_INDEXED, 0),
            "System-Write": (FileFunction.WRITE, 0),
            "System-ReWrite": (FileFunction.RE_WRITE, 0),
        }
    )
)

#: The three functions the key-range guard covers, and ONLY those three
#: [common/acas000.cbl:L333-L335]. ANOMALY N8: open, close, read-next, start
#: and delete are not covered, so an out-of-range key passes silently on all
#: of them. Not extended.
FILE_KEY_NO_GUARDED_FUNCTIONS: Final[frozenset[FileFunction]] = frozenset(
    {
        FileFunction.READ_INDEXED,  # when 4 [common/acas000.cbl:L334]
        FileFunction.WRITE,  # when 5 [common/acas000.cbl:L334]
        FileFunction.RE_WRITE,  # when 7 [common/acas000.cbl:L334]
    }
)

#: `File-Key-No` to table, from the handler's own comment
#: [common/acas000.cbl:L330-L332] plus the fifth arm
#: [common/acas000.cbl:L595-L599], which aliases the first. Anomaly N7: the
#: error table at [common/acas000.cbl:L185] still says "not 1, 2 or 3 or 4".
TABLES_BY_FILE_KEY_NO: Final[Mapping[int, str]] = MappingProxyType(
    {
        1: "SYSTEM-REC",  # `when 1` [common/acas000.cbl:L575-L579]
        2: "SYSDEFLT-REC",  # `when 2` [common/acas000.cbl:L580-L584]
        3: "SYSFINAL-REC",  # `when 3` [common/acas000.cbl:L585-L589]
        4: "SYSTOT-REC",  # `when 4` [common/acas000.cbl:L590-L594]
        5: "SYSTEM-REC",  # `when 5` [common/acas000.cbl:L595-L599] - alias
    }
)

#: The record layout each arm's buffer is to be read as. Key 5 repeats key 1
#: because it calls the same bridge with the same record.
RECORD_TYPE_BY_FILE_KEY_NO: Final[Mapping[int, type]] = MappingProxyType(
    {
        1: SystemRecord,
        2: SysDefaultRecord,
        3: SysFinalRecord,
        4: SystemRecord4,
        5: SystemRecord,
    }
)

#: The `OCCURS` subscript materialised as a primary key - a column NO COPYBOOK
#: DECLARES. Value is the locator of the bridge move that derives it.
#: [common/dfltMT.cbl:L612] `move A to HV-DEF-REC-KEY` and
#: [common/finalMT.cbl:L613] `move A to HV-FINAL-ACC-REC-KEY` take the loop
#: variable; the other two bridges take a literal instead
#: [common/systemMT.cbl:L1070] and [common/sys4MT.cbl:L769].
OCCURS_SUBSCRIPT_PRIMARY_KEYS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "SYSDEFLT-REC": "[common/dfltMT.cbl:L612]",
        "SYSFINAL-REC": "[common/finalMT.cbl:L613]",
    }
)

#: How far each bridge's own loops actually run. ANOMALY N-occurs33:
#: [copybooks/wsdflt.cob] declares `occurs 33` but `dfltMT` bounds at 32 at
#: every site [common/dfltMT.cbl:L532, :L559, :L600, :L643], so entry 33 can
#: neither be written nor read. `finalMT`'s 26 [common/finalMT.cbl:L532] IS
#: the full count for [copybooks/wsfinal.cob], so it loses nothing.
OCCURS_LOOP_BOUNDS: Final[Mapping[str, int]] = MappingProxyType(
    {
        "SYSDEFLT-REC": 32,
        "SYSFINAL-REC": 26,
    }
)

#: ANOMALY N-hvload. Five `systemMT` host variables that neither
#: `bb000-HV-Load` [common/systemMT.cbl:L1061-L1240] nor `bb100-UnloadHVs`
#: [common/systemMT.cbl:L1245-L1298] mentions. Value is the declaration
#: locator. On a write each carries only what `initialize TD-SYSTEM-REC`
#: [common/systemMT.cbl:L1069] left; on a read none reaches the caller.
NEVER_LOADED_HOST_VARIABLES: Final[Mapping[str, Mapping[str, str]]] = (
    MappingProxyType(
        {
            "SYSTEM-REC": MappingProxyType(
                {
                    "COMPANY-EMAIL": "[common/systemMT.cbl:L346]",
                    "STATS-DATE-PERIOD": "[common/systemMT.cbl:L373]",
                    "PL-AUTOGEN": "[common/systemMT.cbl:L418]",
                    "PL-NEXT-REC": "[common/systemMT.cbl:L419]",
                    "PL-APPROP-AC6": "[common/systemMT.cbl:L490]",
                }
            ),
        }
    )
)

#: ANOMALY N-key1. Columns fetched from the database whose host variable is
#: never moved back into the record. `systemMT` comments the move out and says
#: why [common/systemMT.cbl:L1255] `*>     move     HV-SYSTEM-REC-KEY  not
#: wanted and is always 1`; `sys4MT`'s unload section simply has no such move
#: [common/sys4MT.cbl:L794-L822]. The five of N-hvload are unloaded nowhere
#: either and are listed above rather than repeated here.
NEVER_UNLOADED_HOST_VARIABLES: Final[Mapping[str, Mapping[str, str]]] = (
    MappingProxyType(
        {
            "SYSTEM-REC": MappingProxyType(
                {"SYSTEM-REC-KEY": "[common/systemMT.cbl:L1255]"}
            ),
            "SYSTOT-REC": MappingProxyType(
                {"LEDGER-TOTALS-REC-KEY": "[common/sys4MT.cbl:L794-L822]"}
            ),
        }
    )
)


class RelativeFileStoreNotMigratedError(RuntimeError):
    """The relative-file store the other branch uses is out of scope.

    NOT A PLACEHOLDER AND NOT DEFERRED WORK. The compiled handler supports two
    stores and selects between them at run time [common/acas000.cbl:L352]; only
    the RDBMS selection is within the migration. The relative-file selection
    reads and writes records 1 to 4 of a COBOL relative file
    [copybooks/selsys.cob] whose engine the migration deliberately does not
    have: Agent Action Plan section 0.1.1 maps every indexed-file verb onto a
    "Data-access module method issuing SQL against the frozen table", section
    0.2.1.2's Python inventory contains no indexed-file engine, and section
    0.5.1 adds no dependency that could supply one.

    Serving those verbs out of MySQL instead would substitute one store for
    another - a behaviour change, and so a failure under rule R-4 - and
    returning a success status for a record transfer that did not happen would
    be worse. The paragraphs therefore set every field their COBOL sets and
    then raise this, naming the omission.

    A caller reaches the migrated path exactly as the compiled system requires:
    by putting ``"66"`` in ``FA-RDBMS-Flat-Statuses``
    [common/acas000.cbl:L346-L354], whose own comment insists "All programming
    must be directly requested, ONLY." [common/acas000.cbl:L338].
    """


#  SECTION 2 - THE HANDLER'S WORKING-STORAGE


@dataclass(slots=True)
class HandlerState:
    """``acas000``'s ``WORKING-STORAGE``, which outlives a single ``CALL``.

    A COBOL program without ``IS INITIAL`` keeps its ``WORKING-STORAGE``
    between calls for the life of the run, and this handler depends on that in
    two places: the first-call sentinel ``A`` [common/acas000.cbl:L525] and the
    open/closed flag ``Cobol-File-Status`` [common/acas000.cbl:L273-L274]. A
    module-level instance is the faithful equivalent, and it is the reason
    :func:`reset_handler_state` exists - see its docstring for why that
    function has no COBOL counterpart and why saying so plainly is the point.

    Attributes:
        cobol_file_status: ``77 Cobol-File-Status pic 9 value zero.``
            [common/acas000.cbl:L273], with ``88 Cobol-File-Eof value 1``
            [:L274]. Zero means the relative file is closed, 1 that it is open.
        a: ``77 A pic 9(4) value zero.`` [common/acas000.cbl:L270], the
            first-call sentinel and the length of the linkage record. Anomaly
            N-ab: the changelog at [common/acas000.cbl:L156] claims these
            became ``pic 999``; the declaration says otherwise and governs.
        b: ``77 B pic 9(4) value zero.`` [common/acas000.cbl:L271], the length
            of the FILE SECTION record [copybooks/fdsys.cob].
        connection: The one open database connection. The compiled bridges keep
            theirs in the C interface's own static storage, shared by all four,
            which is why there is one here and not one per bridge - and why
            there is no pool (rule R-3).
        cursors: The stored-result state the four bridges' positioning and
            fetching walk, owned by ``dal/cursor_state.py``.
        transport: The transport policy :func:`configure_transport` last set.
            NO COBOL COUNTERPART: the frozen source has no transport concept at
            all, it just connects. ``dal/connection.py`` refuses to cross a
            network in clear text, so the policy has to arrive from somewhere;
            it arrives here rather than as a fifth parameter on
            :func:`dispatch`, because the linkage list is four items and adding
            to it would break the diff a reviewer needs.
        system_record: The last ``SystemRecord`` a caller passed. NO
            DIRECT COBOL COUNTERPART, and the reason is worth stating.
            ``ba012-Test-WS-Rec-Size-2`` loads the six connection
            parameters from ``RDBMS-DB-Name in System-Record`` and its
            five siblings [common/acas000.cbl:L557-L562] - and
            ``System-Record`` there is the FILE SECTION record
            [copybooks/fdsys.cob], NOT the linkage buffer, as its own
            comment says: "Load up the DB settings from the system
            record from COBOL file as its not passed on"
            [common/acas000.cbl:L554]. Anomaly N-fdcreds. The relative
            file that record is read from is out of scope, so the
            credentials have to come from the linkage buffer on the
            calls where it IS a ``SystemRecord`` - keys 1 and 5 - and be
            latched for the rest of the run, which is exactly the
            first-call-only behaviour ``ba012``'s ``if A = zero`` guard
            [common/acas000.cbl:L525] and
            :func:`load_rdb_data_once`'s anomaly A-1 already have.
        mysql_count_rows: ``WS-MYSQL-Count-Rows``, one per bridge, because
            each bridge gets its own copy of the procedure copybook that
            declares it [copybooks/mysql-procedures.cpy]. It is NOT part
            of any shared block, and it outlives a statement: the frozen
            fetch paragraphs test it long after the command that set it
            [common/systemMT.cbl:L908, common/dfltMT.cbl:L571,
            common/finalMT.cbl:L559, common/sys4MT.cbl:L604], which is
            what makes the EOF2 branch reachable at all - see
            :func:`_ba040_process_read_next` for the analysis.
        allow_frozen_placeholder_credentials: Whether an open may proceed with
            the placeholder credentials the copybook ships as ``VALUE`` clauses
            [copybooks/wssystem.cob:L137-L139]. Also no COBOL counterpart, for
            the same reason.
    """

    cobol_file_status: int = 0
    a: int = 0
    b: int = 0
    connection: Any | None = None
    cursors: CursorStateTable = field(default_factory=CursorStateTable)
    transport: TransportSecurity | None = None
    allow_frozen_placeholder_credentials: bool = False
    mysql_count_rows: dict[str, int] = field(default_factory=dict)
    system_record: SystemRecord | None = None

    @property
    def cobol_file_eof(self) -> bool:
        """``88  Cobol-File-Eof  value 1.`` [common/acas000.cbl:L274].

        The condition name is spelled "Eof" but the paragraph that tests it
        tests whether the file is OPEN [common/acas000.cbl:L395], and the
        paragraph that sets it sets it after a successful open
        [common/acas000.cbl:L431]. The name is carried as the source spells it
        and its meaning is documented here rather than corrected.

        Returns:
            ``True`` when ``Cobol-File-Status`` is 1.
        """
        return self.cobol_file_status == 1


_STATE: Final[HandlerState] = HandlerState()


def handler_state() -> HandlerState:
    """Return this run's ``WORKING-STORAGE``.

    Returns:
        The one :class:`HandlerState` for the process, so that a caller or a
        test can observe ``A``, ``Cobol-File-Status`` and the connection the
        way a COBOL debugger would.
    """
    return _STATE


def reset_handler_state() -> None:
    """Clear the handler's ``WORKING-STORAGE`` back to its ``VALUE`` clauses.

    THERE IS NO COBOL COUNTERPART, and that is stated rather than disguised:
    nothing in [common/acas000.cbl] clears ``A`` or ``Cobol-File-Status``,
    because a COBOL run is a process and both die with it. In Python one
    process performs many runs - the determinism suite performs two runs of one
    scenario in one process - so the boundary a COBOL run gets for free has
    to be drawn explicitly.

    Any open connection is closed first, through the bridges' own close path,
    so a reset cannot leak a socket.
    """
    if _STATE.connection is not None:
        # `PERFORM MYSQL-1980-CLOSE THRU MYSQL-1999-EXIT`, the same pair
        # `ba030-Process-Close` performs [common/systemMT.cbl:L648].
        mysql_1980_close(_STATE.connection)
        mysql_1999_exit()
    _STATE.cobol_file_status = 0
    _STATE.a = 0
    _STATE.b = 0
    _STATE.connection = None
    _STATE.cursors = CursorStateTable()
    _STATE.transport = None
    _STATE.allow_frozen_placeholder_credentials = False
    _LOG.debug("acas000 WORKING-STORAGE reset; A and Cobol-File-Status zeroed")


def configure_transport(
    transport: TransportSecurity | None,
    *,
    allow_frozen_placeholder_credentials: bool = False,
) -> None:
    """Set the transport policy the next open will use.

    NO COBOL COUNTERPART - see :class:`HandlerState`. It is a separate function
    rather than a parameter on :func:`dispatch` because the linkage list is
    four items [common/acas000.cbl:L309-L315] and a reviewer diffing the
    argument lists must find four on both sides.

    Args:
        transport: The policy to hand :func:`~acas_posting.dal.connection
            .mysql_1000_open`, or ``None`` to let it apply its own default.
        allow_frozen_placeholder_credentials: Whether the placeholder
            credentials the copybook ships [copybooks/wssystem.cob:L137-L139]
            may be used to connect.
    """
    _STATE.transport = transport
    _STATE.allow_frozen_placeholder_credentials = (
        allow_frozen_placeholder_credentials
    )



#  SECTION 3 - THE FOUR BRIDGE PROFILES


@dataclass(frozen=True, slots=True)
class BridgeProfile:
    """One bridge program's measured behaviour, as data not as a branch.

    The four bridges share one shape and diverge from each other at thirteen
    measured points, listed in full in the module docstring. Every divergence
    lives here with its locator, so the shared paragraph functions read it
    instead of testing which bridge they are running as. Agent Action Plan
    section 0.3.3 is the reason: anything that smoothed the differences away
    "would obscure the exact statement ordering that the state diff is
    sensitive to".

    Attributes:
        program: The bridge's ``program-id``.
        source: The bridge's path, for locators built at run time.
        table: Its MySQL table.
        file_key_no: The ``File-Key-No`` value that reaches it. Five also
            reaches ``systemMT`` [common/acas000.cbl:L595-L599]; the profile
            records the first arm's number.
        record_type: The layout the shared buffer must hold for this bridge.
        open_tag: `move "OPEN x" to WS-File-Key`.
        close_tag: `move "CLOSE x" to WS-File-Key`.
        open_tag_set_before_open: Divergence 13. ``sys4MT`` sets the tag BEFORE
            the open [common/sys4MT.cbl:L456-L459], so a failed open leaves it
            set; the other three set it after, so a failed open leaves spaces.
        low_key_is_quoted: Divergence 2. ``systemMT`` emits the low key bare
            [common/systemMT.cbl:L670]; the other three quote it.
        positioned_tag: Divergence 3. ``">000"`` for ``systemMT``
            [common/systemMT.cbl:L697], ``"000"`` for the other three.
        errno_test_width: Divergence 4. One character for ``systemMT``
            [common/systemMT.cbl:L708]; three for the other three.
        captures_sqlstate: Divergence 5. Only ``systemMT`` calls
            ``MySQL_sqlstate`` [common/systemMT.cbl:L706-L707].
        duplicate_test_includes_sqlstate: Divergence 6. Only ``systemMT`` adds
            ``or Sql-State = "23000"`` [common/systemMT.cbl:L959].
        free_paragraph_no: Divergence 7. 18 for ``systemMT``
            [common/systemMT.cbl:L1037]; 20 for the other three.
        closes_log_on_close: Divergence 8. Only ``systemMT``
            [common/systemMT.cbl:L1052-L1056].
        guards_on_incoming_status: Divergence 9. Only ``sys4MT``, at three
            sites dated 28/09/16 [common/sys4MT.cbl:L538-L541, :L642-L645,
            :L702-L705].
        duplicate_check_is_live: Divergence 10. Commented out in its entirety
            in ``dfltMT`` [common/dfltMT.cbl:L616-L632].
        clears_error_after_logging: Divergence 11. ``finalMT`` only
            [common/finalMT.cbl:L629-L633, :L685-L689].
        rewrite_loop_exits_on_mismatch: Divergence 12a. ``dfltMT`` only
            [common/dfltMT.cbl:L699].
        rewrite_paragraph_no_inside_loop: Divergence 12b. ``dfltMT`` sets it
            inside [common/dfltMT.cbl:L660]; ``finalMT`` before
            [common/finalMT.cbl:L641].
        rewrite_key_is_literal_one: The rewrite predicate names a bare ``"1"``
            in ``sys4MT`` [common/sys4MT.cbl:L688] and ``systemMT``
            [common/systemMT.cbl:L992], and the ``OCCURS`` subscript in the
            other two.
        has_hv_load_section: Divergence 1. ``dfltMT`` and ``finalMT`` have
            neither ``bb000-HV-Load`` nor ``bb100-UnloadHVs``; they move their
            host variables inline.
        occurs_bound: How far this bridge's loops run, or ``None`` for the two
            that handle a single row. Anomaly N-occurs33 lives here.
        clears_status_after_read_loop: Anomaly N-eofclear. ``dfltMT``
            [common/dfltMT.cbl:L589] and ``finalMT`` [common/finalMT.cbl:L597]
            zero the status unconditionally after the loop, discarding the end
            of file the loop set.
        clears_record_on_end_of_data: Whether the ``return-code = -1``
            branch of ``ba040`` blanks the record before returning.
            ``sys4MT`` does [common/sys4MT.cbl:L601], ``systemMT`` does
            NOT [common/systemMT.cbl:L903-L909] even though both blank
            it on the ``EOF2`` branch a few lines later
            [common/systemMT.cbl:L920, common/sys4MT.cbl:L613].
            DIVERGENCE 18: so a caller that walks ``SYSTEM-REC`` past
            its last row keeps the previous row's data in the record
            alongside the end-of-file status, while the same caller on
            ``SYSTOT-REC`` gets a blank record. Reproduced, not
            reconciled. The two table-shaped bridges blank their record
            unconditionally before the loop instead
            [common/dfltMT.cbl:L530, common/finalMT.cbl:L531], so this
            flag does not apply to them and is ``False``.
        write_exits_via_ba999_end: Whether ``ba070-Process-Write`` and
            ``ba090-Process-Rewrite`` transfer to ``ba999-End``, which
            logs, rather than to ``ba999-Exit``, which does not.
            ``systemMT`` alone does [common/systemMT.cbl:L971, :L1021];
            the other three log themselves inline and skip it
            [common/dfltMT.cbl:L637, common/finalMT.cbl:L634,
            common/sys4MT.cbl:L664]. DIVERGENCE 16.
        hv_group_locator: Where the host-variable group is declared.
    """

    program: str
    source: str
    table: str
    file_key_no: int
    record_type: type
    open_tag: str
    close_tag: str
    open_tag_set_before_open: bool
    low_key_is_quoted: bool
    positioned_tag: str
    errno_test_width: int
    captures_sqlstate: bool
    duplicate_test_includes_sqlstate: bool
    free_paragraph_no: int
    closes_log_on_close: bool
    guards_on_incoming_status: bool
    duplicate_check_is_live: bool
    clears_error_after_logging: bool
    rewrite_loop_exits_on_mismatch: bool
    rewrite_paragraph_no_inside_loop: bool
    rewrite_key_is_literal_one: bool
    has_hv_load_section: bool
    occurs_bound: int | None
    clears_status_after_read_loop: bool
    hv_group_locator: str
    write_exits_via_ba999_end: bool
    clears_record_on_end_of_data: bool

    def at(self, line: str) -> str:
        """Build a locator into this bridge's own source.

        Args:
            line: The line or span, such as ``"L940"`` or ``"L950-L965"``.

        Returns:
            A ``[<path>:<line>]`` locator in the form every other citation in
            this package uses.
        """
        return f"[{self.source}:{line}]"


#: ``systemMT``, the largest bridge in the checkout at 5258 lines, for the
#: 169-column ``SYSTEM-REC``. Host-variable group ``01 TD-SYSTEM-REC.``
#: [common/systemMT.cbl:L323-L492]; table directive ``TABLE=SYSTEM-REC,HV``
#: [common/systemMT.scb:L319]. It carries seven of the thirteen divergences on
#: its own.
SYSTEM_MT: Final[BridgeProfile] = BridgeProfile(
    program="systemMT",
    source="common/systemMT.cbl",
    table="SYSTEM-REC",
    file_key_no=1,
    record_type=SystemRecord,
    open_tag="OPEN SYSTEM",  # [common/systemMT.cbl:L634]
    close_tag="CLOSE SYSTEM",  # [common/systemMT.cbl:L643]
    open_tag_set_before_open=False,  # [common/systemMT.cbl:L623-L634]
    low_key_is_quoted=False,  # [common/systemMT.cbl:L670] - bare
    positioned_tag=">000",  # [common/systemMT.cbl:L697]
    errno_test_width=1,  # [common/systemMT.cbl:L708] - `(1:1)`
    captures_sqlstate=True,  # [common/systemMT.cbl:L706-L707]
    duplicate_test_includes_sqlstate=True,  # [common/systemMT.cbl:L959]
    free_paragraph_no=18,  # [common/systemMT.cbl:L1037]
    closes_log_on_close=True,  # [common/systemMT.cbl:L1052-L1056]
    guards_on_incoming_status=False,
    duplicate_check_is_live=True,  # [common/systemMT.cbl:L950-L965]
    clears_error_after_logging=False,
    rewrite_loop_exits_on_mismatch=False,
    rewrite_paragraph_no_inside_loop=False,  # [common/systemMT.cbl:L980]
    rewrite_key_is_literal_one=True,  # [common/systemMT.cbl:L992]
    has_hv_load_section=True,  # [common/systemMT.cbl:L1061, :L1245]
    occurs_bound=None,  # one row: "really only getting the one and only row"
    clears_status_after_read_loop=False,
    hv_group_locator="[common/systemMT.cbl:L323-L492]",
    clears_record_on_end_of_data=False,
    write_exits_via_ba999_end=True,
)

#: ``dfltMT`` for ``SYSDEFLT-REC``: four columns against a 33-entry ``OCCURS``
#: table, walked 32 at a time. Host-variable group ``01 TD-SYSDEFLT-REC.``
#: [common/dfltMT.cbl:L315-L319]. NO ``bb000-HV-Load`` and NO
#: ``bb100-UnloadHVs``, and its duplicate-key check is commented out entirely.
DFLT_MT: Final[BridgeProfile] = BridgeProfile(
    program="dfltMT",
    source="common/dfltMT.cbl",
    table="SYSDEFLT-REC",
    file_key_no=2,
    record_type=SysDefaultRecord,
    open_tag="OPEN DEFAULT",  # [common/dfltMT.cbl:L440]
    close_tag="CLOSE DEFAULT",  # [common/dfltMT.cbl:L449]
    open_tag_set_before_open=False,  # [common/dfltMT.cbl:L429-L440]
    low_key_is_quoted=True,  # [common/dfltMT.cbl:L476]
    positioned_tag="000",  # [common/dfltMT.cbl:L504]
    errno_test_width=3,  # `not = "0  "`
    captures_sqlstate=False,
    duplicate_test_includes_sqlstate=False,
    free_paragraph_no=20,  # [common/dfltMT.cbl:L724]
    closes_log_on_close=False,
    guards_on_incoming_status=False,
    duplicate_check_is_live=False,  # [common/dfltMT.cbl:L616-L632]
    clears_error_after_logging=False,
    rewrite_loop_exits_on_mismatch=True,  # [common/dfltMT.cbl:L699]
    rewrite_paragraph_no_inside_loop=True,  # [common/dfltMT.cbl:L660]
    rewrite_key_is_literal_one=False,  # [common/dfltMT.cbl:L655-L656]
    has_hv_load_section=False,
    occurs_bound=32,  # ANOMALY N-occurs33 [common/dfltMT.cbl:L532]
    clears_status_after_read_loop=True,  # [common/dfltMT.cbl:L589]
    hv_group_locator="[common/dfltMT.cbl:L315-L319]",
    clears_record_on_end_of_data=False,
    write_exits_via_ba999_end=False,
)

#: ``finalMT`` for ``SYSFINAL-REC``: two columns against a 26-entry ``OCCURS``
#: table, walked 26 at a time - the full count, so nothing is lost. Also has
#: neither host-variable section. Alone in clearing the error after logging it.
FINAL_MT: Final[BridgeProfile] = BridgeProfile(
    program="finalMT",
    source="common/finalMT.cbl",
    table="SYSFINAL-REC",
    file_key_no=3,
    record_type=SysFinalRecord,
    open_tag="OPEN FINAL",  # [common/finalMT.cbl:L436]
    close_tag="CLOSE FINAL",  # [common/finalMT.cbl:L445]
    open_tag_set_before_open=False,  # [common/finalMT.cbl:L425-L436]
    low_key_is_quoted=True,  # [common/finalMT.cbl:L477]
    positioned_tag="000",  # [common/finalMT.cbl:L505]
    errno_test_width=3,
    captures_sqlstate=False,
    duplicate_test_includes_sqlstate=False,
    free_paragraph_no=20,  # [common/finalMT.cbl:L710]
    closes_log_on_close=False,
    guards_on_incoming_status=False,
    duplicate_check_is_live=True,  # [common/finalMT.cbl:L616-L628]
    clears_error_after_logging=True,  # [common/finalMT.cbl:L629-L633]
    rewrite_loop_exits_on_mismatch=False,
    rewrite_paragraph_no_inside_loop=False,  # [common/finalMT.cbl:L641]
    rewrite_key_is_literal_one=False,  # [common/finalMT.cbl:L647-L648]
    has_hv_load_section=False,
    occurs_bound=26,  # [common/finalMT.cbl:L532] - the full count
    clears_status_after_read_loop=True,  # [common/finalMT.cbl:L597]
    hv_group_locator="[common/finalMT.cbl:L313-L315]",
    clears_record_on_end_of_data=False,
    write_exits_via_ba999_end=False,
)

#: ``sys4MT`` for the 21-column ``SYSTOT-REC``. Host-variable group
#: ``01 TD-SYSTOT-REC.`` [common/sys4MT.cbl:L314-L335], whose twenty money
#: items are SIGNED - which is what makes anomaly N-sign visible here. Alone in
#: guarding on an incoming non-zero status and in setting its log tag before
#: the open.
SYS4_MT: Final[BridgeProfile] = BridgeProfile(
    program="sys4MT",
    source="common/sys4MT.cbl",
    table="SYSTOT-REC",
    file_key_no=4,
    record_type=SystemRecord4,
    open_tag="OPEN SYS4",  # [common/sys4MT.cbl:L457]
    close_tag="CLOSE SYS4",  # [common/sys4MT.cbl:L476]
    open_tag_set_before_open=True,  # [common/sys4MT.cbl:L456-L459]
    low_key_is_quoted=True,  # [common/sys4MT.cbl:L503]
    positioned_tag="000",  # [common/sys4MT.cbl:L531]
    errno_test_width=3,
    captures_sqlstate=False,
    duplicate_test_includes_sqlstate=False,
    free_paragraph_no=20,  # [common/sys4MT.cbl:L741]
    closes_log_on_close=False,
    guards_on_incoming_status=True,  # [common/sys4MT.cbl:L538-L541]
    duplicate_check_is_live=True,  # [common/sys4MT.cbl:L646-L658]
    clears_error_after_logging=False,
    rewrite_loop_exits_on_mismatch=False,
    rewrite_paragraph_no_inside_loop=False,  # [common/sys4MT.cbl:L672]
    rewrite_key_is_literal_one=True,  # [common/sys4MT.cbl:L688]
    has_hv_load_section=True,  # [common/sys4MT.cbl:L760, :L794]
    occurs_bound=None,  # one row: "Getting the row for loading into cobol rec"
    clears_status_after_read_loop=False,
    hv_group_locator="[common/sys4MT.cbl:L314-L335]",
    clears_record_on_end_of_data=True,
    write_exits_via_ba999_end=False,
)

#: ``ba015-Test-Ends``'s five arms [common/acas000.cbl:L574-L600]. FIVE
#: ENTRIES,
#: FOUR BRIDGES: arm 5 is the same profile as arm 1
#: [common/acas000.cbl:L595-L599], which is exactly what the source does.
BRIDGES_BY_FILE_KEY_NO: Final[Mapping[int, BridgeProfile]] = MappingProxyType(
    {
        1: SYSTEM_MT,
        2: DFLT_MT,
        3: FINAL_MT,
        4: SYS4_MT,
        5: SYSTEM_MT,
    }
)


#  SECTION 4 - COLUMN PLANS, DERIVED FROM THE DATA DICTIONARY


@dataclass(frozen=True, slots=True)
class ColumnPlan:
    """One column of one table, with everything needed to read and write it.

    Built from the generated dictionary, never transcribed by eye - Agent
    Action Plan section 0.8.1 makes that a directive, not a preference: "Data
    dictionary first. The dictionary is generated from the bridge before record
    definitions are written, and every Python field definition cites its entry
    ... it is what prevents fields being transcribed by eye."

    Attributes:
        key: The dictionary key, in ``<TABLE-NAME>.<COLUMN-NAME>`` form.
        column: The MySQL column name, hyphens and all.
        ordinal: Its 1-based position in the frozen table definition, which is
            also the order the bridge's own statement builders and its
            ``MySQL_fetch_record`` argument list use - verified, not assumed.
        quoted: The column name already backtick-quoted, because every
            identifier in this schema contains a hyphen and an unquoted one is
            a syntax error.
        storage: ``DECIMAL``, ``INT``, ``STR`` or ``NONE`` from the dictionary.
            ``NONE`` for the four columns no copybook declares and for the two
            group concatenations - which is exactly why numeric-ness is decided
            from the HOST VARIABLE's usage below and not from this field.
        hv_usage: The host variable's own usage, ``COMP`` for every numeric
            item in these four groups and ``ALPHANUMERIC`` for every character
            one. THE AUTHORITATIVE ANSWER to "is this column a number", because
            the bridge is the authority on the wire format (Agent Action Plan
            section 0.8.2) and three of the four primary keys have no copybook
            declaration to consult.
        scale: The host variable's declared scale, so a value can be coerced
            into it without consulting anything else.
        integer_digits: The host variable's integer digit count, which is also
            the width of the substring the bridge's statement builder takes.
        character_length: The declared width for a character column.
        host_variable: The host variable's name, for the anomaly registers.
        signed_host_variable: Whether the host variable itself is signed. Note
            that this does NOT mean a negative value survives: anomaly N-sign
            means none does, because the substring excludes the sign position.
        route: The attribute path from the record to the value, or ``None``
            when the bridge derives the column instead of moving it.
        derivation: The dictionary's derivation record, present exactly for the
            columns no copybook declares and for the group and redefines
            alternatives.
        drift_details: The dictionary's own sentences about how the copybook,
            the host variable and the column disagree. Carried so a reader sees
            WHY a conversion is what it is without leaving this file.
        loads_from_record: Whether the bridge moves the record into this host
            variable at all. ``False`` for the five of anomaly N-hvload, whose
            host variables appear ONLY at their declaration, in the fetch
            argument list and in the two statement builders - so a write sends
            the ``INITIALIZE`` value and the record's own content never
            reaches the database.
        unloads_to_record: Whether the bridge moves this host variable back
            into the record after a fetch. ``False`` for anomaly N-key1 and for
            the same five, so the round trip loses data in BOTH directions.
        derivation_guard: The dictionary's record of the condition the bridge
            wraps the move in, or ``None``. Exactly one column in these four
            tables has one - ``SYSDEFLT-REC.DEF-ACS``, guarded by
            ``if Def-Acs (A) numeric`` [common/dfltMT.cbl:L606-L607] - and when
            it does not hold the move is simply not made, so the host variable
            keeps its ``INITIALIZE`` value while the rest of the row is still
            written.
        copybook_signed: Whether the COPYBOOK field is signed, or ``None`` for
            the four columns no copybook declares. This is the receiving side
            of a ``bb100-UnloadHVs`` move, so it - not the host variable - is
            what decides whether a negative value survives a READ.
        copybook_locator: Where the copybook declares the field, or ``None``.
        citation: ``loader.cite`` output - the three sources in one line.
    """

    key: str
    column: str
    ordinal: int
    quoted: str
    storage: str
    hv_usage: str
    scale: int
    integer_digits: int
    character_length: int
    host_variable: str
    signed_host_variable: bool
    route: tuple[str, ...] | None
    derivation: str | None
    drift_details: tuple[str, ...]
    loads_from_record: bool
    unloads_to_record: bool
    derivation_guard: str | None
    copybook_signed: bool | None
    copybook_locator: str | None
    citation: str

    @property
    def is_numeric(self) -> bool:
        """Whether this column carries a number rather than characters.

        Decided from the host variable's usage, not from the dictionary's
        storage class: three of the four primary keys are declared by no
        copybook at all, so their storage class is ``NONE`` while their host
        variables are ``PIC 9(03) COMP``.

        Returns:
            ``True`` when the host variable is a numeric item.
        """
        return self.hv_usage != "ALPHANUMERIC"



#: ``bb000-HV-Load``'s move list for ``SYSTEM-REC``, one entry per COBOL
#: ``move`` [common/systemMT.cbl:L1061-L1243]: the attribute path from a
#: :class:`~acas_posting.records.system_record.SystemRecord` down to the value
#: the bridge loads into the matching host variable. Derived from the generated
#: dictionary's own field routes and frozen here so a reader can audit all 166
#: plain moves without running anything - Agent Action Plan section 0.8.1
#: requires the dictionary to come FIRST, not that the mapping be invisible.
#: Three of the 169 columns are absent because no plain ``move`` from the
#: record loads them; ``SYSTEM_REC_SPECIAL_LOADS`` records what the bridge
#: does instead.
SYSTEM_REC_ROUTES: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType(
    {
        "SYSTEM-RECORD-VERSION-PRIME": (
            "system_data_block",
            "system_record_version_prime",
        ),
        "SYSTEM-RECORD-VERSION-SECONDAR": (
            "system_data_block",
            "system_record_version_secondary",
        ),
        "VAT-RATE-1": ("system_data_block", "vat_rates", "vat_rate_1"),
        "VAT-RATE-2": ("system_data_block", "vat_rates", "vat_rate_2"),
        "VAT-RATE-3": ("system_data_block", "vat_rates", "vat_rate_3"),
        "VAT-RATE-4": ("system_data_block", "vat_rates", "vat_rate_4"),
        "VAT-RATE-5": ("system_data_block", "vat_rates", "vat_rate_5"),
        "CYCLEA": ("system_data_block", "cyclea"),
        "PERIOD": ("system_data_block", "period"),
        "PAGE-LINES": ("system_data_block", "page_lines"),
        "NEXT-INVOICE": ("system_data_block", "next_invoice"),
        "RUN-DAT": ("system_data_block", "run_date"),
        "START-DAT": ("system_data_block", "start_date"),
        "END-DAT": ("system_data_block", "end_date"),
        "USER-CODE": ("system_data_block", "user_code"),
        "ADDRESS-1": ("system_data_block", "address_1"),
        "ADDRESS-2": ("system_data_block", "address_2"),
        "ADDRESS-3": ("system_data_block", "address_3"),
        "ADDRESS-4": ("system_data_block", "address_4"),
        "POST-CODE": ("system_data_block", "post_code"),
        "COMPANY-EMAIL": ("system_data_block", "company_email"),
        "COUNTRY": ("system_data_block", "country"),
        "PRINT-SPOOL-NAME": ("system_data_block", "print_spool_name"),
        "PASS-VALUE": ("system_data_block", "pass_value"),
        "LEVEL-1": ("system_data_block", "level", "level_1"),
        "LEVEL-2": ("system_data_block", "level", "level_2"),
        "LEVEL-3": ("system_data_block", "level", "level_3"),
        "LEVEL-4": ("system_data_block", "level", "level_4"),
        "LEVEL-5": ("system_data_block", "level", "level_5"),
        "LEVEL-6": ("system_data_block", "level", "level_6"),
        "PASS-WORD": ("system_data_block", "pass_word"),
        "HOST": ("system_data_block", "host"),
        "OP-SYSTEM": ("system_data_block", "op_system"),
        "CURRENT-QUARTER": ("system_data_block", "current_quarter"),
        "FILE-SYSTEM-USED": (
            "system_data_block",
            "rdbms_flat_statuses",
            "file_system_used",
        ),
        "FILE-DUPLICATES-IN-USE": (
            "system_data_block",
            "rdbms_flat_statuses",
            "file_duplicates_in_use",
        ),
        "DATE-FORM": ("system_data_block", "date_form"),
        "DATA-CAPTURE-USED": ("system_data_block", "data_capture_used"),
        "RDBMS-DB-NAME": ("system_data_block", "rdbms_db_name"),
        "RDBMS-USER": ("system_data_block", "rdbms_user"),
        "RDBMS-PASSWD": ("system_data_block", "rdbms_passwd"),
        "RDBMS-PORT": ("system_data_block", "rdbms_port"),
        "RDBMS-HOST": ("system_data_block", "rdbms_host"),
        "RDBMS-SOCKET": ("system_data_block", "rdbms_socket"),
        "VAT-REG-NUMBER": ("system_data_block", "vat_reg_number"),
        "PARAM-RESTRICT": ("system_data_block", "param_restrict"),
        "STATS-DATE-PERIOD": ("system_data_block", "stats_date_period"),
        "P-C": ("general_ledger_block", "p_c"),
        "P-C-GROUPED": ("general_ledger_block", "p_c_grouped"),
        "P-C-LEVEL": ("general_ledger_block", "p_c_level"),
        "COMPS": ("general_ledger_block", "comps"),
        "COMPS-ACTIVE": ("general_ledger_block", "comps_active"),
        "M-V": ("general_ledger_block", "m_v"),
        "ARCH": ("general_ledger_block", "arch"),
        "TRANS-PRINT": ("general_ledger_block", "trans_print"),
        "TRANS-PRINTED": ("general_ledger_block", "trans_printed"),
        "HEADER-LEVEL": ("general_ledger_block", "header_level"),
        "SALES-RANGE": ("general_ledger_block", "sales_range"),
        "PURCHASE-RANGE": ("general_ledger_block", "purchase_range"),
        "VAT": ("general_ledger_block", "vat"),
        "BATCH-ID": ("general_ledger_block", "batch_id"),
        "LEDGER-2ND-INDEX": ("general_ledger_block", "ledger_2nd_index"),
        "IRS-INSTEAD": ("general_ledger_block", "irs_instead"),
        "LEDGER-SEC": ("general_ledger_block", "ledger_sec"),
        "UPDATES": ("general_ledger_block", "updates"),
        "POSTINGS": ("general_ledger_block", "postings"),
        "NEXT-BATCH": ("general_ledger_block", "next_batch"),
        "EXTRA-CHARGE-AC": ("general_ledger_block", "extra_charge_ac"),
        "VAT-AC": ("general_ledger_block", "vat_ac"),
        "PRINT-SPOOL-NAME2": ("general_ledger_block", "print_spool_name2"),
        "NEXT-FOLIO": ("purchase_ledger_block", "next_folio"),
        "BL-PAY-AC": ("purchase_ledger_block", "bl_pay_ac"),
        "P-CREDITORS": ("purchase_ledger_block", "p_creditors"),
        "BL-PURCH-AC": ("purchase_ledger_block", "bl_purch_ac"),
        "GL-BL-PAY-AC": ("sales_ledger_block", "gl_bl_pay_ac"),
        "GL-P-CREDITORS": ("sales_ledger_block", "gl_p_creditors"),
        "GL-BL-PURCH-AC": ("sales_ledger_block", "gl_bl_purch_ac"),
        "GL-SL-PAY-AC": ("sales_ledger_block", "gl_sl_pay_ac"),
        "GL-S-DEBTORS": ("sales_ledger_block", "gl_s_debtors"),
        "GL-SL-SALES-AC": ("sales_ledger_block", "gl_sl_sales_ac"),
        "BL-END-CYCLE-DAT": ("purchase_ledger_block", "bl_end_cycle_date"),
        "BL-NEXT-BATCH": ("purchase_ledger_block", "bl_next_batch"),
        "AGE-TO-PAY": ("purchase_ledger_block", "age_to_pay"),
        "PURCHASE-LEDGER": ("purchase_ledger_block", "purchase_ledger"),
        "PL-DELIM": ("purchase_ledger_block", "pl_delim"),
        "ENTRY-LEVEL": ("purchase_ledger_block", "entry_level"),
        "P-FLAG-A": ("purchase_ledger_block", "p_flag_a"),
        "P-FLAG-I": ("purchase_ledger_block", "p_flag_i"),
        "P-FLAG-P": ("purchase_ledger_block", "p_flag_p"),
        "PL-STOCK-LINK": ("purchase_ledger_block", "pl_stock_link"),
        "PRINT-SPOOL-NAME3": ("purchase_ledger_block", "print_spool_name3"),
        "PL-AUTOGEN": ("purchase_ledger_block", "pl_autogen"),
        "PL-NEXT-REC": ("purchase_ledger_block", "pl_next_rec"),
        "SALES-LEDGER": ("sales_ledger_block", "sales_ledger"),
        "SL-DELIM": ("sales_ledger_block", "sl_delim"),
        "OI-3-FLAG": ("sales_ledger_block", "oi_3_flag"),
        "CUST-FLAG": ("sales_ledger_block", "cust_flag"),
        "OI-5-FLAG": ("sales_ledger_block", "oi_5_flag"),
        "S-FLAG-OI-3": ("sales_ledger_block", "s_flag_oi_3"),
        "FULL-INVOICING": ("sales_ledger_block", "full_invoicing"),
        "S-FLAG-A": ("sales_ledger_block", "s_flag_a"),
        "S-FLAG-I": ("sales_ledger_block", "s_flag_i"),
        "S-FLAG-P": ("sales_ledger_block", "s_flag_p"),
        "SL-DUNNING": ("sales_ledger_block", "sl_dunning"),
        "SL-CHARGES": ("sales_ledger_block", "sl_charges"),
        "SL-OWN-NOS": ("sales_ledger_block", "sl_own_nos"),
        "SL-STATS-RUN": ("sales_ledger_block", "sl_stats_run"),
        "SL-DAY-BOOK": ("sales_ledger_block", "sl_day_book"),
        "INVOICER": ("sales_ledger_block", "invoicer"),
        "EXTRA-DESC": ("sales_ledger_block", "extra_desc"),
        "EXTRA-TYPE": ("sales_ledger_block", "extra_type"),
        "EXTRA-PRINT": ("sales_ledger_block", "extra_print"),
        "SL-STOCK-LINK": ("sales_ledger_block", "sl_stock_link"),
        "SL-STOCK-AUDIT": ("sales_ledger_block", "sl_stock_audit"),
        "SL-LATE-PER": ("sales_ledger_block", "sl_late_per"),
        "SL-DISC": ("sales_ledger_block", "sl_disc"),
        "EXTRA-RATE": ("sales_ledger_block", "extra_rate"),
        "SL-DAYS-1": ("sales_ledger_block", "sl_days_1"),
        "SL-DAYS-2": ("sales_ledger_block", "sl_days_2"),
        "SL-DAYS-3": ("sales_ledger_block", "sl_days_3"),
        "SL-CREDIT": ("sales_ledger_block", "sl_credit"),
        "SL-MIN": ("sales_ledger_block", "sl_min"),
        "SL-MAX": ("sales_ledger_block", "sl_max"),
        "PF-RETENTION": ("sales_ledger_block", "pf_retention"),
        "FIRST-SL-BATCH": ("sales_ledger_block", "first_sl_batch"),
        "FIRST-SL-INV": ("sales_ledger_block", "first_sl_inv"),
        "SL-LIMIT": ("sales_ledger_block", "sl_limit"),
        "SL-PAY-AC": ("sales_ledger_block", "sl_pay_ac"),
        "S-DEBTORS": ("sales_ledger_block", "s_debtors"),
        "SL-SALES-AC": ("sales_ledger_block", "sl_sales_ac"),
        "S-END-CYCLE-DAT": ("sales_ledger_block", "s_end_cycle_date"),
        "SL-COMP-HEAD-PICK": ("sales_ledger_block", "sl_comp_head_pick"),
        "SL-COMP-HEAD-INV": ("sales_ledger_block", "sl_comp_head_inv"),
        "SL-COMP-HEAD-STAT": ("sales_ledger_block", "sl_comp_head_stat"),
        "SL-COMP-HEAD-LETS": ("sales_ledger_block", "sl_comp_head_lets"),
        "SL-VAT-PRINTED": ("sales_ledger_block", "sl_vat_printed"),
        "SL-INVOICE-LINES": ("sales_ledger_block", "sl_invoice_lines"),
        "SL-AUTOGEN": ("sales_ledger_block", "sl_autogen"),
        "SL-NEXT-REC": ("sales_ledger_block", "sl_next_rec"),
        "STK-ABREV-REF": ("stock_control_block", "stk_abrev_ref"),
        "STK-DEBUG": ("stock_control_block", "stk_debug"),
        "STK-MANU-USED": ("stock_control_block", "stk_manu_used"),
        "STK-OE-USED": ("stock_control_block", "stk_oe_used"),
        "STK-AUDIT-USED": ("stock_control_block", "stk_audit_used"),
        "STK-MOV-AUDIT": ("stock_control_block", "stk_mov_audit"),
        "STK-PERIOD-CUR": ("stock_control_block", "stk_period_cur"),
        "STK-PERIOD-DAT": ("stock_control_block", "stk_period_dat"),
        "STOCK-CONTROL": ("stock_control_block", "stock_control"),
        "STK-AVERAGING": ("stock_control_block", "stk_averaging"),
        "STK-ACTIVITY-REP-RUN": (
            "stock_control_block",
            "stk_activity_rep_run",
        ),
        "STK-PAGE-LINES": ("stock_control_block", "stk_page_lines"),
        "STK-AUDIT-NO": ("stock_control_block", "stk_audit_no"),
        "CLIENT": ("irs_entry_block", "client"),
        "NEXT-POST": ("irs_entry_block", "next_post"),
        "VAT1": ("irs_entry_block", "vat_rates2", "vat1"),
        "VAT2": ("irs_entry_block", "vat_rates2", "vat2"),
        "VAT3": ("irs_entry_block", "vat_rates2", "vat3"),
        "IRS-PASS-VALUE": ("irs_entry_block", "irs_pass_value"),
        "SAVE-SEQU": ("irs_entry_block", "save_sequ"),
        "SYSTEM-WORK-GROUP": ("irs_entry_block", "system_work_group"),
        "PL-APP-CREATED": ("irs_entry_block", "pl_app_created"),
        "PL-APPROP-AC": ("irs_entry_block", "filler_323", "pl_approp_ac"),
        "1ST-TIME-FLAG": ("irs_entry_block", "first_time_flag"),
        "PL-APPROP-AC6": ("irs_entry_block", "pl_approp_ac6"),
        "SL-BO-FLAG": ("sales_ledger_block", "sl_bo_flag"),
        "STK-BO-ACTIVE": ("stock_control_block", "stk_bo_active"),
    }
)

#: ``bb000-HV-Load``'s move list for ``SYSTOT-REC``
#: [common/sys4MT.cbl:L760-L789]. Twenty plain moves; the key is derived. NOTE
#: that the bridge issues these in RECORD order - the two Sales spare fields
#: sit between the Sales block and the Purchase block in the copybook, but the
#: two Purchase spares come LAST [common/sys4MT.cbl:L788-L789] - whereas the
#: frozen table definition at mysql/ACASDB.sql:L1376 orders them 2..21 with the
#: spares at 10, 11, 20, 21. Both orders are recorded: this mapping is keyed by
#: column, and ``column_plans_for`` returns COLUMN-ORDINAL order.
SYSTOT_REC_ROUTES: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType(
    {
        "SL-OS-BAL-LAST-MONTH": ("sales_ledger_data", "sl_os_bal_last_month"),
        "SL-OS-BAL-THIS-MONTH": ("sales_ledger_data", "sl_os_bal_this_month"),
        "SL-INVOICES-THIS-MONTH": (
            "sales_ledger_data",
            "sl_invoices_this_month",
        ),
        "SL-CREDIT-NOTES-THIS-MONTH": (
            "sales_ledger_data",
            "sl_credit_notes_this_month",
        ),
        "SL-VARIANCE": ("sales_ledger_data", "sl_variance"),
        "SL-CREDIT-DEDUCTIONS": ("sales_ledger_data", "sl_credit_deductions"),
        "SL-CN-UNAPPL-THIS-MONTH": (
            "sales_ledger_data",
            "sl_cn_unappl_this_month",
        ),
        "SL-PAYMENTS": ("sales_ledger_data", "sl_payments"),
        "SL4-SPARE1": ("sales_ledger_data", "sl4_spare1"),
        "SL4-SPARE2": ("sales_ledger_data", "sl4_spare2"),
        "PL-OS-BAL-LAST-MONTH": (
            "purchase_ledger_data",
            "pl_os_bal_last_month",
        ),
        "PL-OS-BAL-THIS-MONTH": (
            "purchase_ledger_data",
            "pl_os_bal_this_month",
        ),
        "PL-INVOICES-THIS-MONTH": (
            "purchase_ledger_data",
            "pl_invoices_this_month",
        ),
        "PL-CREDIT-NOTES-THIS-MONTH": (
            "purchase_ledger_data",
            "pl_credit_notes_this_month",
        ),
        "PL-VARIANCE": ("purchase_ledger_data", "pl_variance"),
        "PL-CREDIT-DEDUCTIONS": (
            "purchase_ledger_data",
            "pl_credit_deductions",
        ),
        "PL-CN-UNAPPL-THIS-MONTH": (
            "purchase_ledger_data",
            "pl_cn_unappl_this_month",
        ),
        "PL-PAYMENTS": ("purchase_ledger_data", "pl_payments"),
        "SL4-SPARE3": ("purchase_ledger_data", "sl4_spare3"),
        "SL4-SPARE4": ("purchase_ledger_data", "sl4_spare4"),
    }
)

#: ``ba070-Process-Write``'s move list for ``SYSDEFLT-REC``
#: [common/dfltMT.cbl:L606-L614]. The paths are relative to ONE
#: :class:`~acas_posting.records.system_dflt.DefGroup` entry, because this
#: bridge walks the 33-entry ``OCCURS`` table and writes one row per entry, so
#: the subscript is not part of the path - it becomes the primary key. NOTE the
#: bridge's own move order is ACS, key, VAT, CODES, which is neither column
#: order nor copybook order; no move has a side effect on another, so binding
#: in column order is observationally identical.
SYSDEFLT_REC_ROUTES: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType(
    {
        "DEF-ACS": ("def_acs",),  # [common/dfltMT.cbl:L606-L610]
        "DEF-CODES": ("def_codes",),  # [common/dfltMT.cbl:L614]
        "DEF-VAT": ("def_vat",),  # [common/dfltMT.cbl:L613]
    }
)

#: ``ba070-Process-Write``'s move list for ``SYSFINAL-REC``
#: [common/finalMT.cbl:L613-L614]. ``AR1`` is a bare 26-entry table of
#: ``pic x(16)`` items with no group below the subscript, so the route is the
#: EMPTY tuple: the value IS the table element. Recorded explicitly rather than
#: omitted, because an empty route and a missing route mean different things
#: here - Agent Action Plan section 0.7.2 R-5: "Deliberate omissions are
#: recorded as omissions."
SYSFINAL_REC_ROUTES: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType(
    {
        "AR1": (),  # [common/finalMT.cbl:L614]
    }
)

#: The four route tables, reachable by table name.
ROUTES_BY_TABLE: Final[Mapping[str, Mapping[str, tuple[str, ...]]]] = (
    MappingProxyType(
        {
            "SYSTEM-REC": SYSTEM_REC_ROUTES,
            "SYSDEFLT-REC": SYSDEFLT_REC_ROUTES,
            "SYSFINAL-REC": SYSFINAL_REC_ROUTES,
            "SYSTOT-REC": SYSTOT_REC_ROUTES,
        }
    )
)

#: The three ``SYSTEM-REC`` columns ``bb000-HV-Load`` does NOT load with a
#: plain move, and what it does instead. Each is a dictionary-recorded
#: derivation, so the reason is auditable rather than folded into code::
#:
#:     move     1                       to HV-SYSTEM-REC-KEY   [:L1070]
#:     move     Suser                   to HV-SUSER            [:L1085]
#:     move     Maps-Ser-xx to  WS-Maps-xx                     [:L1110]
#:     move     Maps-Ser-nn to  WS-Maps-nn                     [:L1111]
#:     move     ws-Maps-Ser-x           to HV-MAPS-SER         [:L1112]
SYSTEM_REC_SPECIAL_LOADS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "SYSTEM-REC-KEY": "common/systemMT.cbl:L1070",
        "SUSER": "common/systemMT.cbl:L1085",
        "MAPS-SER": "common/systemMT.cbl:L1107-L1112",
    }
)

#: ``SUSER`` is a one-item group, so the group move reaches exactly one field.
SUSER_ROUTE: Final[tuple[str, ...]] = ("system_data_block", "suser", "usera")

#: ``MAPS-SER`` is the only two-part conversion in these four bridges. On the
#: way out ``pic xx`` and a ``binary-short`` are packed into a six-character
#: work group; on the way back in the six characters are unpacked again
#: [common/systemMT.cbl:L1294-L1297]. The work group is declared at
#: [common/systemMT.cbl:L252-L254] as ``ws-maps-xx pic xx`` followed by
#: ``ws-maps-nn pic 9(4)``.
MAPS_SER_ROUTE: Final[tuple[str, ...]] = ("system_data_block", "maps_ser")

#: The width of ``ws-maps-nn`` [common/systemMT.cbl:L254], which fixes how many
#: characters of ``HV-MAPS-SER`` carry the numeric half.
MAPS_SER_NN_DIGITS: Final[int] = 4

#: The two columns whose value the bridge invents rather than moves, and the
#: literal it uses. Both are ``move 1``, so a ``SYSTEM-REC`` row and a
#: ``SYSTOT-REC`` row are ALWAYS written at key 1 - which is also why dispatch
#: arm 5 [common/acas000.cbl:L595-L599] is a true alias of arm 1: it cannot
#: reach a different row.
LITERAL_ONE_PRIMARY_KEYS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "SYSTEM-REC": "common/systemMT.cbl:L1070",
        "SYSTOT-REC": "common/sys4MT.cbl:L769",
    }
)

_COLUMN_PLAN_CACHE: dict[str, tuple[ColumnPlan, ...]] = {}


def column_plans_for(table: str) -> tuple[ColumnPlan, ...]:
    """Build (and cache) the column plan for one of the four tables.

    The order is the frozen table definition's own ordinal order, taken from
    ``loader.entries_for_table``. That order was verified against three
    independent orderings in the bridge - its ``MySQL_fetch_record`` argument
    list, its ``bb200-Insert`` column list and its ``bb300-Update`` assignment
    list - and all three agree, which is what licenses driving the whole
    mapping from the dictionary instead of transcribing 169 columns by eye.

    Args:
        table: One of ``SYSTEM-REC``, ``SYSDEFLT-REC``, ``SYSFINAL-REC`` or
            ``SYSTOT-REC``.

    Returns:
        One :class:`ColumnPlan` per column, in ordinal order.

    Raises:
        KeyError: If ``table`` is not one of this handler's four tables, or if
            the dictionary has an entry for it with no bridge host variable -
            which would mean the generated dictionary and this module have
            drifted apart and must be reconciled before anything is written.
    """
    cached = _COLUMN_PLAN_CACHE.get(table)
    if cached is not None:
        return cached
    routes = ROUTES_BY_TABLE[table]
    plans: list[ColumnPlan] = []
    for entry in loader.entries_for_table(table):
        host_variable = entry.bridge_host_variable
        if host_variable is None:
            raise KeyError(
                f"{entry.key}: the dictionary records no bridge host "
                "variable, so this module cannot know how the bridge "
                "converts it. Regenerate the dictionary before writing."
            )
        column = entry.column
        short_name = entry.key.split(".", 1)[1]
        derivation = entry.derivation
        copybook_field = entry.copybook
        plans.append(
            ColumnPlan(
                key=entry.key,
                column=column.name,
                ordinal=column.ordinal,
                quoted=quote_identifier(column.name),
                storage=entry.cobol_python_storage.value,
                hv_usage=host_variable.usage.value,
                scale=host_variable.scale or 0,
                integer_digits=host_variable.integer_digits or 0,
                character_length=host_variable.character_length or 0,
                host_variable=host_variable.name,
                signed_host_variable=bool(host_variable.signed),
                route=routes.get(short_name),
                derivation=(
                    None if derivation is None else derivation.expression
                ),
                drift_details=tuple(entry.drift.details),
                loads_from_record=bool(host_variable.loaded_from_record),
                unloads_to_record=bool(host_variable.unloaded_to_record),
                derivation_guard=(
                    None if derivation is None else derivation.guard
                ),
                copybook_signed=(
                    None
                    if copybook_field is None
                    else bool(copybook_field.signed)
                ),
                copybook_locator=(
                    None if copybook_field is None else copybook_field.source
                ),
                citation=loader.cite(entry.key),
            )
        )
    built = tuple(plans)
    _COLUMN_PLAN_CACHE[table] = built
    return built


def _route_value(record: object, route: Sequence[str]) -> Any:
    """Follow an attribute route from a record down to one value.

    Args:
        record: The record, or the ``OCCURS`` element for the two table-shaped
            layouts.
        route: The attribute names to follow. An empty route means the record
            argument IS the value, which is how ``SYSFINAL-REC.AR1`` reaches
            its ``pic x(16)`` table element.

    Returns:
        The value the COBOL ``move`` would have taken as its sending field.
    """
    value: Any = record
    for attribute in route:
        value = getattr(value, attribute)
    return value


def _assign_route(record: object, route: Sequence[str], value: Any) -> None:
    """Store one value back through an attribute route.

    Reproduces the receiving half of a ``bb100-UnloadHVs`` move. An empty
    route cannot be assigned through - the two table-shaped layouts rebuild
    their tuple instead - so it is rejected loudly rather than silently
    dropped.

    Args:
        record: The record to store into.
        route: The attribute names to follow; the last one is assigned.
        value: The value to store.

    Raises:
        ValueError: If ``route`` is empty.
    """
    if not route:
        raise ValueError(
            "an empty route has no attribute to assign; the caller must "
            "rebuild the OCCURS tuple itself"
        )
    target: Any = record
    for attribute in route[:-1]:
        target = getattr(target, attribute)
    setattr(target, route[-1], value)


#  SECTION 5 - THE CONVERSIONS, MEASURED AGAINST THE COMPILED BRIDGE
#
#  Nothing in this section is business logic and nothing in it is inferred from
#  a picture clause by reasoning. Every rule below was measured on GnuCOBOL 3.2
#  with the repository's own default arithmetic (no `-std=`, no
#  `>>SET ARITHMETIC`, no `binary-truncate` in any compile line), which
#  is what Agent Action Plan section 0.7.2 R-6 demands: "Where a semantic
#  question is ambiguous, the compiled program's observed behavior decides
#  it."


def _blank_like(value: Any) -> Any:
    """Return the ``INITIALIZE ... WITH FILLER`` value for one elementary item.

    ``WITH FILLER`` is what makes this reset FILLER items too, which plain
    ``INITIALIZE`` leaves alone - and every one of these four record layouts
    has at least one FILLER.

    Args:
        value: The current value, which carries the item's declared shape: a
            :class:`str`'s length is its ``pic x(n)``, a :class:`~decimal
            .Decimal`'s exponent is its ``V9(m)``, and an :class:`int` is a
            binary or zoned integer.

    Returns:
        Spaces of the same length for a character item, a zero of the same
        scale for a decimal item, ``0`` for an integer item, and the value
        unchanged for anything this module does not model.
    """
    if isinstance(value, str):
        return " " * len(value)
    if isinstance(value, Decimal):
        return Decimal(0).quantize(value)
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return 0
    return value


def _initialize_with_filler(record: Any) -> None:
    """Reproduce ``INITIALIZE <record> WITH FILLER`` in place.

    The four bridges issue this at five distinct points, and the point matters
    because it decides what a caller sees after a failed read::

        initialize System-Record   with filler   [common/systemMT.cbl:L922]
        initialize System-Record   with filler   [common/systemMT.cbl:L1253]
        initialize Default-Record  with filler   [common/dfltMT.cbl:L530]
        initialize Final-Record    with filler   [common/finalMT.cbl:L531]
        initialize System-Record-4 with filler   [common/sys4MT.cbl:L601]
        initialize System-Record-4 with filler   [common/sys4MT.cbl:L613]
        initialize System-Record-4 with filler   [common/sys4MT.cbl:L802]

    ``dfltMT`` and ``finalMT`` clear BEFORE their read loop, so a partial sweep
    leaves the untouched entries blank rather than stale. ``systemMT`` and
    ``sys4MT`` clear inside ``bb100-UnloadHVs`` and, separately, on their end
    of file paths.

    Args:
        record: A record dataclass, or any nested group or ``OCCURS`` element
            of one. Mutated in place, because the COBOL statement mutates the
            caller's storage and every record class in this package is
            deliberately not frozen so that it can.
    """
    for descriptor in dataclasses.fields(record):
        current = getattr(record, descriptor.name)
        if dataclasses.is_dataclass(current) and not isinstance(current, type):
            _initialize_with_filler(current)
            continue
        if isinstance(current, tuple):
            rebuilt: list[Any] = []
            for element in current:
                if dataclasses.is_dataclass(element) and not isinstance(
                    element, type
                ):
                    _initialize_with_filler(element)
                    rebuilt.append(element)
                else:
                    rebuilt.append(_blank_like(element))
            setattr(record, descriptor.name, tuple(rebuilt))
            continue
        setattr(record, descriptor.name, _blank_like(current))


def _zoned_display_digits(text: str) -> int:
    """Read a ``pic 9(n)`` DISPLAY item's digits the way the runtime does.

    A zoned decimal digit is the low four bits of the byte, so a space (0x20)
    reads as zero and a letter reads as its low nibble. This is not a
    validation and not a guess - it is how the only unpacked numeric item in
    these four bridges, ``ws-maps-nn pic 9(4)``
    [common/systemMT.cbl:L254], behaves when ``HV-MAPS-SER``'s last four
    characters are not digits, which is reachable because the column is
    ``char(6)`` and nothing constrains its contents.

    Args:
        text: The characters occupying the digit positions.

    Returns:
        The integer the runtime would see.
    """
    total = 0
    for character in text:
        total = total * 10 + (ord(character) & 0x0F)
    return total


def _truncate_toward_zero(value: Decimal, scale: int) -> Decimal:
    """Store a value into a field of ``scale`` decimal places, unrounded.

    COBOL truncates toward zero on store unless ``ROUNDED`` is written, and
    none of these four bridges writes ``ROUNDED`` anywhere. Measured:
    ``move 1.005 to PIC 9(04)V9(02)`` stores ``0001.00``.

    Args:
        value: The sending value.
        scale: The receiving field's decimal places.

    Returns:
        The value with its excess decimal places discarded.
    """
    return value.quantize(Decimal(1).scaleb(-scale), rounding=ROUND_DOWN)


def _high_order_truncate(value: Decimal, integer_digits: int) -> Decimal:
    """Discard integer digits that do not fit the receiving field.

    COBOL drops high-order digits silently on an oversized store; there is no
    size error unless ``ON SIZE ERROR`` is written, and none of these bridges
    writes one.

    Args:
        value: The sending value, already at the receiving scale.
        integer_digits: How many integer digit positions the receiver has.

    Returns:
        The value with any excess high-order digits removed, sign preserved.
    """
    if integer_digits <= 0:
        return value
    limit = Decimal(10) ** integer_digits
    magnitude = value.copy_abs()
    if magnitude < limit:
        return value
    kept = magnitude % limit
    return -kept if value.is_signed() else kept


def _as_decimal(value: Any) -> Decimal:
    """Read any modelled record value as an exact decimal.

    Deliberately never accepts a binary approximation of a real number: Agent
    Action Plan section 0.7.2 R-2 forbids one at every point, "not in
    computation, not in storage, not in transport".

    Args:
        value: A :class:`~decimal.Decimal`, an :class:`int`, or the characters
            of a DISPLAY item.

    Returns:
        The exact value.

    Raises:
        TypeError: If the value is of a type this module does not model, which
            can only mean a record field was assigned something the copybook
            does not describe.
    """
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool):
        return Decimal(int(value))
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, str):
        return Decimal(_zoned_display_digits(value.strip() or "0"))
    raise TypeError(
        f"{type(value).__name__} is not a modelled COBOL value; a record "
        "field holds something no copybook declares"
    )


def _host_variable_value(plan: ColumnPlan, value: Any) -> Decimal | int | str:
    """Reproduce one ``move <record field> to HV-<column>``.

    Args:
        plan: The column's plan, which carries the host variable's declared
            picture straight from the generated dictionary. Nothing here is
            inferred from the COBOL type, because signedness and width drift
            in this codebase is specific rather than systemic - Agent Action
            Plan section 0.6.2.
        value: The sending field's value.

    Returns:
        The value as the host variable would hold it: a left-justified,
        space-padded string of the declared width for a character item; an
        :class:`int` for a scale-zero numeric item; a
        :class:`~decimal.Decimal` at the declared scale otherwise.
    """
    if not plan.is_numeric:
        text = value if isinstance(value, str) else str(value)
        width = plan.character_length
        if width <= 0:
            return text
        return text[:width].ljust(width)
    number = _as_decimal(value)
    number = _truncate_toward_zero(number, plan.scale)
    if not plan.signed_host_variable:
        #  MEASURED, not assumed: `move -42 to PIC 9(05) COMP` stores 00042
        #  and `compute 0 - 42` into `PIC 9(10) COMP` stores 0000000042. This
        #  resolves the third ambiguity in Agent Action Plan section 0.6.8.
        number = number.copy_abs()
    number = _high_order_truncate(number, plan.integer_digits)
    if plan.scale == 0:
        return int(number)
    return number


def _bound_parameter(
    plan: ColumnPlan, host_value: Decimal | int | str
) -> Decimal | int | str:
    """Turn a host variable into the value the bridge's statement carries.

    ANOMALY N-sign, reproduced here and nowhere else. The bridges build their
    statement text by MOVEing the host variable into
    ``01 WS-MYSQL-EDIT PIC -Z(18)9.9(9)`` [common/systemMT.cbl:L260,
    common/sys4MT.cbl:L250] and then taking substrings of it. That edited field
    is thirty characters: position 1 is a FIXED sign, 2..20 are nineteen
    integer digit positions, 21 is the point, 22..30 are nine fraction digits.
    The seven substring ranges the four bridges use - ``(11:10)``, ``(13:08)``,
    ``(16:05)``, ``(17:04)``, ``(18:03)``, ``(19:02)`` and ``(22:02)`` - each
    span exactly the host variable's own digit positions, ending at position
    20. NOT ONE OF THEM INCLUDES POSITION 1, so the sign is never emitted.

    Measured, verbatim from the probe: ``-1234.56`` becomes ``1234.56``;
    ``-99999999.99`` becomes ``99999999.99``; ``-0.05`` becomes ``0.05``; and
    ``HV-SL-NEXT-REC`` [common/systemMT.cbl:L465] at ``-42`` becomes ``42``.
    That is twenty signed ``decimal(10,2)`` ledger-total columns
    [mysql/ACASDB.sql:L1378-L1397] which cannot receive a negative number no
    matter what the record holds. Agent Action Plan section 0.8.2: "A defect
    reproduced is correct; a defect fixed is a failure."

    The asymmetry is real and is preserved: a READ keeps the sign, because the
    column is signed and ``MySQL_fetch_record`` puts a negative straight into a
    signed host variable. Only the write direction loses it.

    Args:
        plan: The column's plan.
        host_value: The value the host variable holds.

    Returns:
        The bound parameter. For a numeric column, the ABSOLUTE value, because
        the bridge's own text carries no sign. For a character column, the
        value with trailing spaces removed, which is what
        ``FUNCTION TRIM (HV-x,TRAILING)`` produces - measured to contribute
        ZERO characters when the host variable is entirely spaces, so an
        all-space item is bound as the empty string, not as a space.
    """
    if not plan.is_numeric:
        text = host_value if isinstance(host_value, str) else str(host_value)
        return text.rstrip(" ")
    if isinstance(host_value, str):
        return host_value
    return abs(host_value)


def _move_into(current: Any, value: Any, *, signed: bool | None) -> Any:
    """Reproduce one ``move HV-<column> to <record field>``.

    The receiving field's shape is read from the value already in it, which is
    exact here because every bridge issues ``INITIALIZE ... WITH FILLER``
    before it unloads, so what is in the field at that moment is the declared
    default the record module authored from the copybook.

    Args:
        current: The value in the receiving field, carrying its shape.
        value: The sending value.
        signed: Whether the RECEIVING copybook field is signed, or ``None``
            when no copybook declares it. An unsigned receiver takes the
            absolute value, measured.

    Returns:
        The value as the receiving field would hold it.
    """
    if isinstance(current, str):
        text = value if isinstance(value, str) else str(value)
        width = len(current)
        return text[:width].ljust(width) if width else text
    if isinstance(current, Decimal):
        number = _as_decimal(value)
        if signed is False:
            number = number.copy_abs()
        return number.quantize(current, rounding=ROUND_DOWN)
    if isinstance(current, int) and not isinstance(current, bool):
        number = _truncate_toward_zero(_as_decimal(value), 0)
        if signed is False:
            number = number.copy_abs()
        return int(number)
    return value


def _pack_maps_ser(group: Any) -> str:
    """Pack ``Maps-Ser`` into the six characters ``HV-MAPS-SER`` carries.

    Reproduces the only two-part conversion in these four bridges, verbatim::

        move     Maps-Ser-xx to  WS-Maps-xx        [common/systemMT.cbl:L1110]
        move     Maps-Ser-nn to  WS-Maps-nn        [common/systemMT.cbl:L1111]
        move     ws-Maps-Ser-x           to HV-MAPS-SER
                                                   [common/systemMT.cbl:L1112]

    The work group is ``ws-maps-xx pic xx`` followed by ``ws-maps-nn pic 9(4)``
    [common/systemMT.cbl:L252-L254], so the numeric half is rendered
    zero-padded to four digits and an oversized value loses its high-order
    digits.

    Args:
        group: The record's ``Maps-Ser`` group.

    Returns:
        Exactly six characters.
    """
    prefix = str(group.maps_ser_xx)[:2].ljust(2)
    number = _high_order_truncate(
        _as_decimal(group.maps_ser_nn).copy_abs(), MAPS_SER_NN_DIGITS
    )
    return prefix + str(int(number)).rjust(MAPS_SER_NN_DIGITS, "0")


def _unpack_maps_ser(text: str, group: Any) -> None:
    """Unpack ``HV-MAPS-SER``'s six characters back into ``Maps-Ser``.

    Reproduces the reverse conversion, verbatim::

        move     HV-MAPS-SER  to ws-Maps-Ser-x     [common/systemMT.cbl:L1294]
        move     ws-Maps-xx  to Maps-Ser-xx        [common/systemMT.cbl:L1295]
        move     WS-Maps-nn  to Maps-Ser-nn        [common/systemMT.cbl:L1296]

    Args:
        text: The host variable's six characters.
        group: The record's ``Maps-Ser`` group, mutated in place.
    """
    padded = str(text)[:6].ljust(6)
    group.maps_ser_xx = padded[:2]
    group.maps_ser_nn = _zoned_display_digits(padded[2:6])


def _fa_rdbms_flat_statuses_text(file_access: FileAccess) -> str:
    """Read ``FA-RDBMS-Flat-Statuses`` as the two characters the handler tests.

    The item is a GROUP of two ``pic 9`` elementary items
    [copybooks/wsfnctn.cob:L72-L83]::

         03  FA-RDBMS-Flat-Statuses.
             07  FA-File-System-Used  pic 9.
             07  FA-File-Duplicates-In-Use pic 9.

    and ``aa010-main`` compares the GROUP against the two-character literal
    ``"66"`` [common/acas000.cbl:L352], which is a group comparison and so
    alphanumeric. So the selector is set by putting 6 in BOTH digits.

    ⭐ ANOMALY, recorded not corrected: 6 is not a value either item has an
    ``88`` for. ``FA-File-System-Used``'s condition names cover 0 and 1 and its
    ``FA-FS-Valid-Options`` names "values 0 thru 1"
    [copybooks/wsfnctn.cob:L74-L82], and ``FA-File-Duplicates-In-Use``'s covers
    1 with the comment "NO LONGER USED other than for a '6' = rdb."
    [copybooks/wsfnctn.cob:L83]. The maintainer flagged the arrangement himself
    two lines above the group: "need to change next one if used in the DAL,
    e.g., move \"66\" ..." [copybooks/wsfnctn.cob:L70-L71]. The magic value
    therefore has no name anywhere, and the handler's own comment insists on it
    all the same: "All programming must be directly requested, ONLY."
    [common/acas000.cbl:L344].

    Args:
        file_access: The caller's block.

    Returns:
        The two characters, in the group's declared order.
    """
    group = file_access.fa_rdbms_flat_statuses
    return (
        f"{int(group.fa_file_system_used) % 10}"
        f"{int(group.fa_file_duplicates_in_use) % 10}"
    )


def _ws_file_key_move(text: str) -> str:
    """Reproduce ``move <value> to WS-File-Key``.

    ``WS-File-Key`` is ``pic x(64)`` [copybooks/wsfnctn.cob:L52], and a MOVE
    replaces the whole field: left-justified, space-padded, truncated on the
    right. A numeric sending item is rendered zero-padded to its own digit
    count first - measured: ``move A to WS-File-Key`` with ``A pic 9(4)`` at 7
    gives ``0007``, and ``move WS-Key to WS-File-Key`` with ``WS-Key pic 999``
    [common/dfltMT.cbl:L302, common/finalMT.cbl:L300] gives ``007``.

    Args:
        text: The sending value, already rendered.

    Returns:
        Exactly ``WS_FILE_KEY_WIDTH`` characters.
    """
    return text[:WS_FILE_KEY_WIDTH].ljust(WS_FILE_KEY_WIDTH)


def _string_into_ws_file_key(existing: str, *parts: str) -> str:
    """Reproduce ``string <parts> into WS-File-Key``.

    MEASURED, and it is not the same as a MOVE: ``STRING`` overlays from the
    pointer and leaves whatever the field already held beyond the last
    character it wrote. Running ``string "Read Indexed " 4`` and then
    ``string "Write " 4`` with no intervening clear leaves
    ``Write 4dexed 4``. Every one of the three ``STRING`` sites in this handler
    is preceded by ``move spaces to WS-File-Key``
    [common/acas000.cbl:L462, :L471, :L482], so the residue is not observable
    here - but the primitive is the faithful one and the clear is reproduced
    at each site rather than assumed.

    Args:
        existing: The field's current sixty-four characters.
        *parts: The sending items, each contributing its full size, which is
            what ``STRING`` does when no ``DELIMITED BY`` is written.

    Returns:
        Exactly ``WS_FILE_KEY_WIDTH`` characters.
    """
    overlay = "".join(parts)
    base = existing[:WS_FILE_KEY_WIDTH].ljust(WS_FILE_KEY_WIDTH)
    joined = overlay + base[len(overlay):]
    return joined[:WS_FILE_KEY_WIDTH]


#  SECTION 6 - THE BRIDGE ENGINE: ONE IMPLEMENTATION, FOUR MEASURED PROFILES
#
#  All four bridges have the same nine-paragraph skeleton, so the skeleton is
#  written once and every place they differ is read out of the bridge's own
#  BridgeProfile. That is the opposite of flattening: the divergences are not
#  smoothed away, they are the data the one implementation runs on, each with
#  its own locator. Where a difference changes control flow rather than a
#  value, the branch is written out and cited at the branch.

#: ``WS-Log-Where`` is ``pic x(231)`` [copybooks/wsfnctn.cob:L53]. It carries
#: the ``WHERE`` clause a rewrite built, for the log record only.
WS_LOG_WHERE_WIDTH: Final[int] = 231

#: ``move 990 to WE-Error`` in every bridge's ``ba100-Bad-Function``
#: [common/systemMT.cbl:L1028, common/dfltMT.cbl:L731,
#: common/finalMT.cbl:L717, common/sys4MT.cbl:L748].
WE_ERROR_BRIDGE_BAD_FUNCTION: Final[int] = WeError.UNKNOWN_UNEXPECTED

#: The three ``WS-File-Key`` tags a read loop leaves on its three distinct end
#: conditions. Each is a plain ``move``, so the field is fully replaced.
#: ``EOF`` is the ordinary end [common/finalMT.cbl:L556]; ``EOF3`` is a key
#: outside the ``OCCURS`` bound, and it puts the OFFENDING KEY VALUE into
#: ``We-Error`` rather than an error code [common/finalMT.cbl:L565-L566];
#: ``EOF2`` is a driver failure discovered through a zero row count
#: [common/finalMT.cbl:L578-L585]. ``No Data`` is set earlier, when the
#: positioning statement itself found nothing [common/finalMT.cbl:L521].
READ_END_TAGS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "end_of_table": "EOF",
        "key_out_of_bound": "EOF3",
        "driver_failure": "EOF2",
        "no_rows": "No Data",
    }
)


def ca_process_logs(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``Ca-Process-Logs`` - hand the shared blocks to the logger.

    [common/acas000.cbl:L608-L613], and the identically named paragraph at the
    foot of each of the four bridges [common/systemMT.cbl:L1062 region,
    common/dfltMT.cbl:L889, common/finalMT.cbl:L823, common/sys4MT.cbl:L1583],
    all of which are one statement::

        call     "fhlogger" using File-Access
                                  ACAS-DAL-Common-data.

    ``common/fhlogger.cbl`` is out of scope - Agent Action Plan section 0.2.2
    lists it under "Non-posting utilities" - and it writes to a log FILE, not
    to a table, so it has no database effect. Agent Action Plan section 0.3.4
    therefore governs: "Diagnostic displays with no database effect become log
    records at a severity matching the original's intent. They must not alter
    control flow and must not appear in any table dump." This function does
    exactly that and nothing else.

    RECORDED OMISSION: ``Log-File-Rec-Written``
    [copybooks/Test-Data-Flags.cob] is a counter ``fhlogger`` maintains. Since
    ``fhlogger`` is out of scope, its side effect on that counter is NOT
    invented here. Nothing in the migrated posting cycle reads it.

    Args:
        file_access: The shared ``File-Access`` block, read only.
        dal_common: The shared flags block. ``SW-Testing`` decides whether the
            caller performs this paragraph at all, which is why this function
            does not test it again - the COBOL tests it at each call site.
    """
    logging_data = file_access.logging_data
    _LOG.debug(
        "fhlogger system=%s file=%s para=%s fn=%s at=%s key=%s "
        "reply=%s werr=%s sqlerr=%s sqlstate=%s where=%s msg=%s",
        logging_data.ws_log_system,
        logging_data.ws_log_file_no,
        logging_data.ws_no_paragraph,
        file_access.file_function,
        file_access.access_type,
        sanitise_for_log(logging_data.ws_file_key),
        file_access.fs_reply,
        file_access.we_error,
        sanitise_for_log(logging_data.sql_err),
        sanitise_for_log(logging_data.sql_state),
        sanitise_for_log(logging_data.ws_log_where),
        sanitise_for_log(logging_data.sql_msg),
    )


def _testing_1(dal_common: AcasDalCommonData) -> bool:
    """Evaluate the ``Testing-1`` condition name.

    ``SW-Testing`` is ``pic 9 value 1`` [copybooks/Test-Data-Flags.cob:L10] and
    ``Testing-1`` is its ``88`` for the value 1. The frozen source ships it ON,
    which is preserved by the record module's default rather than quietly
    turned off.

    Args:
        dal_common: The shared flags block.

    Returns:
        Whether file-handler logging is on.
    """
    return dal_common.sw_testing == 1


def _ba010_initialise(
    bridge: BridgeProfile, file_access: FileAccess
) -> None:
    """``ba010-Initialise`` - clear the diagnostics, then dispatch.

    [common/systemMT.cbl:L540-L547], [common/dfltMT.cbl:L346-L352],
    [common/finalMT.cbl:L342-L348], [common/sys4MT.cbl:L373-L379]. Verbatim,
    from ``systemMT``::

        move     spaces to WS-MYSQL-Error-Message
                           WS-MYSQL-Error-Number
                           WS-Log-Where
                           WS-File-Key
                           SQL-Msg
                           SQL-Err
                           SQL-State.

    DIVERGENCE 14: only ``systemMT`` clears ``SQL-State``. The other three stop
    at ``SQL-Err``, which is consistent with ``systemMT`` being the only one of
    the four that ever populates ``SQL-State``
    [common/systemMT.cbl:L706-L707].

    ANOMALY, RECORDED NOT REPRODUCED because it is already dead in the frozen
    source: each bridge carries its OWN key-range guard here, commented out.
    ``systemMT``'s covers read-indexed, start and delete
    [common/systemMT.cbl:L549-L566]; ``sys4MT``'s covers read-indexed only
    [common/sys4MT.cbl:L382-L390]; ``dfltMT`` and ``finalMT`` have only the
    remark "we will skip this". The handler's guard at
    [common/acas000.cbl:L331-L340] is therefore the ONLY key-range check that
    executes anywhere in this chain - which is what makes its narrowness
    (anomaly N8) load-bearing rather than merely untidy.

    ``WS-MYSQL-Error-Message`` and ``WS-MYSQL-Error-Number`` are bridge-local
    working storage with no counterpart in any shared block, so clearing them
    is representation-only and is recorded here rather than modelled.

    Args:
        bridge: The bridge's profile, consulted for divergence 14.
        file_access: The shared block, mutated in place.
    """
    logging_data = file_access.logging_data
    logging_data.ws_log_where = " " * WS_LOG_WHERE_WIDTH
    logging_data.ws_file_key = " " * WS_FILE_KEY_WIDTH
    logging_data.sql_msg = " " * SQL_MSG_WIDTH
    logging_data.sql_err = " " * SQL_ERR_WIDTH
    if bridge.captures_sqlstate:
        logging_data.sql_state = " " * SQL_STATE_WIDTH


def _ba020_process_open(
    bridge: BridgeProfile,
    system: SystemRecord,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
) -> None:
    """``ba020-Process-Open`` - marshal the six parameters, then open.

    [common/systemMT.cbl:L588-L633], [common/dfltMT.cbl:L394-L440],
    [common/finalMT.cbl:L390-L436], [common/sys4MT.cbl:L410-L459]. Each bridge
    builds six NUL-terminated C strings from ``RDB-Data``::

        string   DB-Schema      delimited by space
                 X"00"          delimited by size
                                  into WS-MYSQL-BASE-NAME
        end-string.

    then ``move 1 to ws-No-Paragraph``, then
    ``PERFORM MYSQL-1000-OPEN THRU MYSQL-1090-EXIT``, then
    ``if fs-reply not = zero go to ba999-end``, and only then the tag.

    DIVERGENCE 13, measured: ``sys4MT`` sets its tag BEFORE the open
    [common/sys4MT.cbl:L456-L459], so a FAILED open leaves ``OPEN SYS4`` in
    ``WS-File-Key``; the other three set it after
    [common/systemMT.cbl:L623-L634], so a failed open leaves the spaces
    ``ba010-Initialise`` put there. That difference is visible in a log record
    and is preserved.

    The credentials come from ``File-Access``'s ``RDB-Data`` block, which the
    handler's ``ba012-Test-WS-Rec-Size-2`` filled - see anomaly N-fdcreds in
    the module docstring for where the COBOL actually reads them from and why
    the migrated slice cannot reproduce that source.

    Args:
        bridge: The bridge's profile.
        system: The system record, which is where
            :func:`~acas_posting.dal.connection.load_rdb_data_once` takes the
            connection parameters from - once per run, anomaly A-1.
        file_access: The shared block, mutated in place.
        dal_common: The shared flags block.
    """
    state = handler_state()
    rdb_data = file_access.rdb_data
    #  The six `string ... delimited by space X"00"` marshalling statements,
    #  in the bridge's own order [common/systemMT.cbl:L598-L621].
    marshalled = (
        cobol_string_delimited_by_space(rdb_data.db_schema),
        cobol_string_delimited_by_space(rdb_data.db_host),
        cobol_string_delimited_by_space(rdb_data.db_uname),
        cobol_string_delimited_by_space(rdb_data.db_upass),
        cobol_string_delimited_by_space(rdb_data.db_port),
        cobol_string_delimited_by_space(rdb_data.db_socket),
    )
    _LOG.debug(
        "%s open: base=%s host=%s port=%s socket=%s",
        bridge.program,
        marshalled[0],
        marshalled[1],
        marshalled[4],
        marshalled[5],
    )
    logging_data = file_access.logging_data
    logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NO_OPEN
    if bridge.open_tag_set_before_open:
        #  DIVERGENCE 13 [common/sys4MT.cbl:L457]
        logging_data.ws_file_key = _ws_file_key_move(bridge.open_tag)
    outcome: OpenOutcome = mysql_1000_open(
        system,
        ws_no_paragraph=BRIDGE_PARAGRAPH_NO_OPEN,
        we_error=file_access.we_error,
        transport=state.transport,
        allow_frozen_placeholder_credentials=(
            state.allow_frozen_placeholder_credentials
        ),
    )
    mysql_1090_exit(outcome)
    outcome.apply_to_logging_data(logging_data)
    file_access.fs_reply = outcome.fs_reply
    file_access.we_error = outcome.we_error
    if outcome.fs_reply != FsReply.SUCCESS:
        #  `if fs-reply not = zero go to ba999-end` - GO TO class 3, section
        #  exit [common/systemMT.cbl:L631-L632].
        return
    state.connection = outcome.connection
    if not bridge.open_tag_set_before_open:
        #  [common/systemMT.cbl:L634]
        logging_data.ws_file_key = _ws_file_key_move(bridge.open_tag)
    state.cursors.reset(bridge.table)
    _LOG.info("%s opened %s", bridge.program, bridge.table)
    del dal_common


def _ba030_process_close(
    bridge: BridgeProfile,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
) -> None:
    """``ba030-Process-Close`` - free any cursor, then close.

    [common/systemMT.cbl:L637-L650], [common/dfltMT.cbl:L443-L456],
    [common/finalMT.cbl:L439-L452], [common/sys4MT.cbl:L470-L483]. Verbatim,
    from ``systemMT``::

        if      Cursor-Active         *> this will not occur for the ...
                perform ba998-Free.

        move     2 to ws-No-Paragraph.
        move    "CLOSE SYSTEM" to WS-File-Key.
              PERFORM MYSQL-1980-CLOSE THRU MYSQL-1999-EXIT
        go      to ba999-end.

    Note the statement order: the free comes first, then the paragraph number,
    then the tag, then the close. ``sys4MT`` is the same here - its tag
    divergence is on the OPEN only.

    Args:
        bridge: The bridge's profile.
        file_access: The shared block, mutated in place.
        dal_common: The shared flags block.
    """
    state = handler_state()
    if state.cursors.state_for(bridge.table).cursor_active():
        _ba998_free(bridge, file_access)
    logging_data = file_access.logging_data
    logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NO_CLOSE
    logging_data.ws_file_key = _ws_file_key_move(bridge.close_tag)
    mysql_1980_close(state.connection)
    mysql_1999_exit()
    state.connection = None
    _LOG.info("%s closed %s", bridge.program, bridge.table)
    del dal_common


def _ba100_bad_function(file_access: FileAccess) -> None:
    """``ba100-Bad-Function`` - the bridge's own catch-all.

    [common/systemMT.cbl:L1024-L1030], [common/dfltMT.cbl:L727-L733],
    [common/finalMT.cbl:L713-L719], [common/sys4MT.cbl:L744-L750]. Identical in
    all four, comment included::

        ba100-Bad-Function.
        *>
        *> Houston; We have a problem
        *>
             move     990 to WE-Error.
             move     99 to Fs-Reply.
             go       to ba999-End.

    Unreachable from this handler in practice, because
    ``aa010-main``'s own ``evaluate`` [common/acas000.cbl:L372-L385] has
    already sent every function the bridges do not implement to
    ``aa100-Bad-Function`` and its ``999``. Reproduced anyway: the bridge is
    also callable from the IRS convention, and a paragraph that exists in the
    specification exists here - Agent Action Plan section 0.7.2 R-5 wants one
    function per paragraph, not one function per reachable paragraph.

    Args:
        file_access: The shared block, mutated in place.
    """
    file_access.we_error = WE_ERROR_BRIDGE_BAD_FUNCTION
    file_access.fs_reply = FsReply.ERROR


def _ba998_free(bridge: BridgeProfile, file_access: FileAccess) -> None:
    """``ba998-Free`` - release the result set and forget the cursor.

    [common/systemMT.cbl:L1036-L1046], [common/dfltMT.cbl:L737-L747],
    [common/finalMT.cbl:L723-L733], [common/sys4MT.cbl:L754-L764]::

        move     18 to ws-No-Paragraph.          *> systemMT only
                   MOVE TP-SYSTEM-REC TO WS-MYSQL-RESULT
                   CALL "MySQL_free_result" USING WS-MYSQL-RESULT end-call
        move     zero to Most-Cursor-Set.

    DIVERGENCE 5: ``systemMT`` numbers this paragraph 18
    [common/systemMT.cbl:L1037]; the other three number it 20
    [common/dfltMT.cbl:L738, common/finalMT.cbl:L724,
    common/sys4MT.cbl:L755]. The number reaches the log record, so it is
    carried in the profile rather than hard-coded.

    Args:
        bridge: The bridge's profile, consulted for divergence 5.
        file_access: The shared block, mutated in place.
    """
    file_access.logging_data.ws_no_paragraph = bridge.free_paragraph_no
    handler_state().cursors.reset(bridge.table)


def _ba999_end(
    bridge: BridgeProfile,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
) -> None:
    """``ba999-End`` - log, and for one bridge log a second time.

    [common/systemMT.cbl:L1048-L1058], [common/dfltMT.cbl:L749-L755],
    [common/finalMT.cbl:L721-L727], [common/sys4MT.cbl:L766-L772]. Three of the
    four are just::

        if       Testing-1
                 perform Ca-Process-Logs
        end-if.

    DIVERGENCE 6: ``systemMT`` alone adds a second, unconditional block that
    fires on a close and logs again with the two function fields ZEROED
    [common/systemMT.cbl:L1052-L1056]::

        if       fn-close
                 move zero to File-Function
                              Access-Type              *> close log file
                 perform  Ca-Process-Logs
        end-if.

    Note that the second block is NOT guarded by ``Testing-1``, so a close
    through ``systemMT`` logs even with logging switched off, and it leaves
    ``File-Function`` and ``Access-Type`` at zero in the caller's shared block
    - a side effect on data the caller owns, not merely a log line. Both halves
    are reproduced.

    Args:
        bridge: The bridge's profile, consulted for divergence 6.
        file_access: The shared block, mutated in place.
        dal_common: The shared flags block.
    """
    if _testing_1(dal_common):
        ca_process_logs(file_access, dal_common)
    if bridge.closes_log_on_close and (
        file_access.file_function == FileFunction.CLOSE
    ):
        file_access.file_function = 0
        file_access.access_type = 0
        ca_process_logs(file_access, dal_common)


#: ``WS-MYSQL-Error-Number`` is ``pic x(3)`` and every bridge compares it
#: against the literal ``"0  "`` [common/sys4MT.cbl:L547], except ``systemMT``
#: which tests only its first character [common/systemMT.cbl:L708]. This is the
#: value the comparison sees when the driver reported nothing wrong.
ERRNO_NO_ERROR: Final[str] = "0  "


@dataclass(frozen=True, slots=True)
class _CommandOutcome:
    """What one ``MYSQL-1210-COMMAND`` left for its caller to test.

    The bridges never look at a return value; they test
    ``WS-MYSQL-COUNT-ROWS`` and then, only if it is not 1, ask the driver for
    an error number. This object carries exactly those three observables and
    the statement text, so each caller can reproduce its own test rather than
    inherit one.

    Attributes:
        count_rows: ``WS-MYSQL-Count-Rows`` after the command.
        errno: What ``call "MySQL_errno"`` would return - ``"0  "`` when the
            driver reported nothing.
        message: What ``call "MySQL_error"`` would return, already safe to log.
        sql_state: What ``call "MySQL_sqlstate"`` would return. Only
            ``systemMT`` asks for it.
        statement: The statement text, for the log record.
    """

    count_rows: int
    errno: str
    message: str
    sql_state: str
    statement: str


def _initial_host_variable(plan: ColumnPlan) -> Decimal | int | str:
    """The value ``initialize TD-<TABLE>`` leaves in one host variable.

    ``bb000-HV-Load`` opens with ``initialize TD-SYSTEM-REC.``
    [common/systemMT.cbl:L1069] and ``initialize TD-SYSTOT-REC.``
    [common/sys4MT.cbl:L768]. Agent Action Plan section 0.6.2 states the
    consequence, verbatim: "an unset field becomes zero or space, never SQL
    ``NULL`` ... This is why every column in the schema can be declared
    ``NOT NULL`` and why the Python layer must default rather than omit."

    ``dfltMT`` and ``finalMT`` have no such statement, because they have no
    ``bb000-HV-Load`` at all - divergence 1. It makes no observable difference
    there: every one of their four and two host variables is assigned on every
    iteration that is not skipped by the empty-entry guard.

    Args:
        plan: The column's plan.

    Returns:
        Spaces of the declared width, ``0``, or a zero at the declared scale.
    """
    if not plan.is_numeric:
        return " " * plan.character_length
    if plan.scale == 0:
        return 0
    return Decimal(0).quantize(Decimal(1).scaleb(-plan.scale))


def _bb000_hv_load(
    bridge: BridgeProfile,
    record: Any,
    *,
    subscript: int | None = None,
) -> dict[str, Decimal | int | str]:
    """``bb000-HV-Load`` - move the record into the host variables.

    [common/systemMT.cbl:L1061-L1243] and [common/sys4MT.cbl:L760-L789] for the
    two bridges that have the section; for ``dfltMT`` and ``finalMT`` this
    reproduces the inline moves their write and rewrite paragraphs make instead
    [common/dfltMT.cbl:L606-L614], [common/finalMT.cbl:L613-L614].

    Everything about which record field reaches which column comes from the
    generated dictionary - Agent Action Plan section 0.8.1 makes that ordering
    a directive - and the four departures from a plain move are each named:

    * The two literal keys. ``move 1 to HV-SYSTEM-REC-KEY``
      [common/systemMT.cbl:L1070] and ``move 1 to HV-LEDGER-TOTALS-REC-KEY``
      [common/sys4MT.cbl:L769]. Neither column exists in any copybook, and
      neither bridge can address a row other than 1.
    * The two subscript keys. ``move A to HV-DEF-REC-KEY``
      [common/dfltMT.cbl:L612] and ``move A to HV-FINAL-ACC-REC-KEY``
      [common/finalMT.cbl:L613] - the ``OCCURS`` subscript materialised as a
      column, and the clearest local proof of the preserved user requirement in
      Agent Action Plan section 0.8.2 that the bridge, not the copybook, is the
      data dictionary for this migration.
    * The group move and the two-part conversion, ``SUSER`` and ``MAPS-SER``.
    * ANOMALY N-hvload: the five ``SYSTEM-REC`` host variables no move ever
      reaches, so a write sends their ``INITIALIZE`` value - zero or spaces -
      and whatever the record held is silently discarded. Reproduced by
      honouring the dictionary's own ``loaded_from_record``, so it cannot drift
      from the source.

    Args:
        bridge: The bridge's profile.
        record: The record for the two single-row tables, or one ``OCCURS``
            element for the two table-shaped ones.
        subscript: The one-based ``OCCURS`` subscript, for the two
            table-shaped tables. ``None`` for the other two.

    Returns:
        The host variables keyed by column name, in the frozen definition's
        ordinal order - which is also the order both statement builders and
        the fetch argument list use.

    Raises:
        ValueError: If a subscript is required and absent, or supplied and not
            required. Both would mean the caller and the bridge disagree about
            the shape of the table, which must never be guessed at.
    """
    plans = column_plans_for(bridge.table)
    needs_subscript = bridge.table in OCCURS_SUBSCRIPT_PRIMARY_KEYS
    if needs_subscript and subscript is None:
        raise ValueError(
            f"{bridge.program} writes one row per OCCURS entry, so the "
            "subscript that becomes the primary key is required "
            f"{OCCURS_SUBSCRIPT_PRIMARY_KEYS[bridge.table]}"
        )
    if not needs_subscript and subscript is not None:
        raise ValueError(
            f"{bridge.program} addresses a single row and derives its key "
            "from a literal, so no subscript applies "
            f"[{LITERAL_ONE_PRIMARY_KEYS[bridge.table]}]"
        )
    #  `initialize TD-<TABLE>.` - every host variable first, so an unloaded one
    #  is zero or spaces rather than absent.
    host_variables: dict[str, Decimal | int | str] = {
        plan.column: _initial_host_variable(plan) for plan in plans
    }
    for plan in plans:
        short_name = plan.column
        if not plan.loads_from_record:
            #  ANOMALY N-hvload [common/systemMT.cbl:L346, :L373, :L418,
            #  :L419, :L490]. The INITIALIZE value stands.
            continue
        if bridge.table in LITERAL_ONE_PRIMARY_KEYS and plan.route is None:
            if short_name == "SYSTEM-REC-KEY" or (
                short_name == "LEDGER-TOTALS-REC-KEY"
            ):
                host_variables[short_name] = 1
                continue
        if needs_subscript and plan.route is None:
            host_variables[short_name] = _host_variable_value(
                plan, subscript
            )
            continue
        if short_name == "SUSER":
            #  `move Suser to HV-SUSER` [common/systemMT.cbl:L1085] - a group
            #  move that reaches the group's single `pic x(32)` item.
            host_variables[short_name] = _host_variable_value(
                plan, _route_value(record, SUSER_ROUTE)
            )
            continue
        if short_name == "MAPS-SER":
            #  [common/systemMT.cbl:L1110-L1112]
            host_variables[short_name] = _host_variable_value(
                plan, _pack_maps_ser(_route_value(record, MAPS_SER_ROUTE))
            )
            continue
        route = plan.route
        if route is None:
            raise ValueError(
                f"{plan.key}: no route and no derivation this module knows "
                f"about. {plan.citation}"
            )
        value = _route_value(record, route)
        if plan.derivation_guard is not None and not isinstance(
            value, (int, Decimal)
        ):
            #  The one guarded move in these four bridges:
            #  `if Def-Acs (A) numeric` [common/dfltMT.cbl:L606-L607]. When it
            #  does not hold the move is NOT made, so the host variable keeps
            #  its INITIALIZE value and the rest of the row is still written.
            continue
        host_variables[short_name] = _host_variable_value(plan, value)
    return host_variables


def _bb100_unload_hvs(
    bridge: BridgeProfile,
    record: Any,
    row: Mapping[str, Any],
    *,
    subscript: int | None = None,
) -> None:
    """``bb100-UnloadHVs`` - move the host variables back into the record.

    [common/systemMT.cbl:L1245-L1428] and [common/sys4MT.cbl:L794-L822]. Its
    opening comment states the reason every column can be ``NOT NULL``,
    verbatim: "NULL fields must not be returned in the buffer. SQL filters each
    column to ensure it has a proper value. This saves using indicator
    variables."

    The section starts with ``initialize System-Record with filler``
    [common/systemMT.cbl:L1253], which is why a receiving field's shape can be
    read from the value already in it: at this moment it holds the declared
    default the record module authored from the copybook.

    ANOMALY N-key1 is reproduced here rather than worked around. ``systemMT``
    comments its key move out and says why [common/systemMT.cbl:L1255]::

        *>     move     HV-SYSTEM-REC-KEY  not wanted and is always 1

    and ``sys4MT``'s section simply has no such move
    [common/sys4MT.cbl:L794-L822]. The five host variables of anomaly N-hvload
    are likewise never moved back, so a read-then-write round trip loses their
    content in BOTH directions. All six omissions come from the dictionary's
    own ``unloaded_to_record``, so they cannot drift from the source.

    Args:
        bridge: The bridge's profile.
        record: The record to store into, mutated in place.
        row: The fetched row keyed by column name.
        subscript: For the two table-shaped tables, the ``OCCURS`` position to
            store at - which the bridge takes from the KEY COLUMN's own value,
            not from its loop counter. ``None`` for the other two.
    """
    for plan in column_plans_for(bridge.table):
        if not plan.unloads_to_record:
            #  ANOMALY N-key1 / N-hvload.
            continue
        route = plan.route
        if plan.column == "SUSER":
            #  `move HV-SUSER to Suser` [common/systemMT.cbl:L1271]
            current = _route_value(record, SUSER_ROUTE)
            _assign_route(
                record,
                SUSER_ROUTE,
                _move_into(
                    current,
                    row[plan.column],
                    signed=plan.copybook_signed,
                ),
            )
            continue
        if plan.column == "MAPS-SER":
            #  [common/systemMT.cbl:L1294-L1296]
            _unpack_maps_ser(
                str(row[plan.column]), _route_value(record, MAPS_SER_ROUTE)
            )
            continue
        if route is None:
            #  The four bridge-only primary keys have no copybook counterpart
            #  to move back into: `SYSTEM-REC-KEY` and `LEDGER-TOTALS-REC-KEY`
            #  are the literal 1 the bridge supplies
            #  [common/systemMT.cbl:L1070, common/sys4MT.cbl:L769], and
            #  `DEF-REC-KEY` and `FINAL-ACC-REC-KEY` are the OCCURS subscript
            #  itself [common/dfltMT.cbl:L579, common/finalMT.cbl:L587]. All
            #  four are the clearest proof of Agent Action Plan section 0.8.2:
            #  "the bridge ... is the data dictionary for this migration."
            continue
        if subscript is not None:
            #  The two table-shaped layouts store through the subscript, so
            #  the tuple is rebuilt rather than assigned through.
            _store_occurs_entry(bridge, record, row, subscript, plan)
            continue
        current = _route_value(record, route)
        _assign_route(
            record,
            route,
            _move_into(
                current, row[plan.column], signed=plan.copybook_signed
            ),
        )


def _store_occurs_entry(
    bridge: BridgeProfile,
    record: Any,
    row: Mapping[str, Any],
    subscript: int,
    plan: ColumnPlan,
) -> None:
    """Store one fetched column into one ``OCCURS`` entry.

    Reproduces the two store-backs verbatim, comment included::

        move  HV-DEF-ACS   to Def-Acs   (HV-DEF-REC-KEY)  *> KEY = table pos
                                                 [common/dfltMT.cbl:L579]
        move  HV-AR1       to AR1 (HV-FINAL-ACC-REC-KEY)  *> KEY = table pos
                                                 [common/finalMT.cbl:L587]

    The subscript is the KEY COLUMN's value, so a row whose key does not match
    its arrival order lands where the key says, not where the loop is. That is
    the behaviour, and it is why the two bridges guard the key against their
    ``OCCURS`` bound before storing [common/finalMT.cbl:L564-L566].

    ``SYSFINAL-REC``'s table has no group below the subscript - it is 26 bare
    ``pic x(16)`` items - so its route is the empty tuple and the element
    itself is replaced. ``SYSDEFLT-REC``'s entries are three-field groups and
    are mutated in place.

    Args:
        bridge: The bridge's profile.
        record: The record holding the table, mutated in place.
        row: The fetched row keyed by column name.
        subscript: The one-based position taken from the key column.
        plan: The column being stored.
    """
    table_attribute = (
        "ar1" if bridge.table == "SYSFINAL-REC" else "def_group"
    )
    entries = list(getattr(record, table_attribute))
    index = subscript - 1
    if not 0 <= index < len(entries):
        #  Unreachable from the two bridges, which test the key against their
        #  own bound first [common/finalMT.cbl:L564-L566,
        #  common/dfltMT.cbl:L551-L556]; raised rather than silently ignored
        #  so a caller that reaches it cannot mistake a lost row for success.
        raise IndexError(
            f"{plan.key}: key {subscript} is outside the "
            f"{len(entries)}-entry OCCURS table"
        )
    if plan.route == ():
        entries[index] = _move_into(
            entries[index], row[plan.column], signed=plan.copybook_signed
        )
        setattr(record, table_attribute, tuple(entries))
        return
    entry = entries[index]
    current = _route_value(entry, plan.route or ())
    _assign_route(
        entry,
        plan.route or (),
        _move_into(current, row[plan.column], signed=plan.copybook_signed),
    )


#: ``A`` is ``pic 99 comp`` in the two table-shaped bridges
#: [common/dfltMT.cbl:L301, common/finalMT.cbl:L299], so
#: ``move A to WS-File-Key`` renders TWO digits, and ``WS-Key`` is ``pic 999``
#: [common/dfltMT.cbl:L302, common/finalMT.cbl:L300], so the rewrite predicate
#: carries three. Measured, because a numeric sending item is rendered
#: zero-padded to its own digit count and nothing about the receiving
#: ``pic x(64)`` changes that.
OCCURS_COUNTER_DIGITS: Final[int] = 2

#: ``WS-Key``'s width [common/dfltMT.cbl:L302, common/finalMT.cbl:L300].
REWRITE_KEY_DIGITS: Final[int] = 3


def _zero_filled(width: int) -> str:
    """Reproduce ``move zero to <alphanumeric item>``.

    The figurative constant ``ZERO`` moved to an alphanumeric item fills it
    with the CHARACTER zero, not with spaces. Three bridges clear ``SQL-Err``
    that way [common/systemMT.cbl:L947, common/sys4MT.cbl:L638,
    common/finalMT.cbl:L605] and ``systemMT`` clears ``SQL-State`` that way
    too [common/systemMT.cbl:L945], so the field a caller then reads holds
    ``"00000"`` rather than blanks. That difference is visible in a log record
    and in every subsequent duplicate-key test, which compares
    ``SQL-Err (1:4)`` against text.

    Args:
        width: The item's declared width.

    Returns:
        ``width`` character zeroes.
    """
    return "0" * width


def _numeric_move_text(value: int, digits: int) -> str:
    """Render a numeric sending item for a ``move`` into an alphanumeric item.

    Measured: ``move A to WS-File-Key`` with ``A pic 9(4)`` at 7 produced
    ``0007``, and with ``WS-Key pic 999`` at 7 it produced ``007`` - the
    sending item's own digit count, zero-padded, with no sign position.

    Args:
        value: The sending value.
        digits: The sending item's declared digit count.

    Returns:
        Exactly ``digits`` characters.
    """
    return str(abs(int(value))).rjust(digits, "0")[-digits:]


def _errno_indicates_failure(bridge: BridgeProfile, errno: str) -> bool:
    """Evaluate the bridge's own test of ``WS-MYSQL-Error-Number``.

    DIVERGENCE 3. ``systemMT`` tests only the FIRST character
    [common/systemMT.cbl:L708, :L916, :L954, :L1010]::

        if    WS-MYSQL-Error-Number (1:1) not = "0"

    while the other three compare the whole three-character field
    [common/sys4MT.cbl:L547, common/dfltMT.cbl:L516,
    common/finalMT.cbl:L512]::

        if    WS-MYSQL-Error-Number  not = "0  "

    For every errno the driver actually produces the two agree, but they are
    not the same test and the profile carries which one applies.

    Args:
        bridge: The bridge's profile.
        errno: The error number as the driver reported it.

    Returns:
        Whether the bridge would treat this as a failure worth recording.
    """
    if bridge.errno_test_width == 1:
        return errno[:1] != "0"
    return errno != ERRNO_NO_ERROR


def _insert_statement(bridge: BridgeProfile) -> str:
    """Build ``bb200-Insert``'s statement for one bridge.

    The generated text is MySQL's ``SET`` form of ``INSERT``, assembled column
    by column in ordinal order [common/finalMT.cbl:L736-L765]::

        INSERT INTO `SYSFINAL-REC` SET `FINAL-ACC-REC-KEY`="026", `AR1`="x";

    Two differences from the frozen text, both deliberate and neither
    observable in table state:

    * values are BOUND rather than interpolated, so no data value can alter the
      statement. The bound value is the same one the frozen text would have
      carried, because :func:`_bound_parameter` reproduces the edit-field
      substring exactly, sign loss included; and
    * the ``x"00"`` terminator [common/finalMT.cbl:L764-L765] is a C-string
      artefact of handing the text to the client library and has no meaning
      when a driver is passed a Python string. RECORDED OMISSION.

    Every column of the table appears, always - Agent Action Plan
    section 0.6.2: "the Python layer must default rather than omit."

    Args:
        bridge: The bridge's profile.

    Returns:
        The statement, with one ``%s`` per column in ordinal order.
    """
    plans = column_plans_for(bridge.table)
    assignments = ", ".join(f"{plan.quoted}=%s" for plan in plans)
    return (
        f"INSERT INTO {quote_identifier(bridge.table)} SET "
        f"{assignments};"
    )


def _update_statement(bridge: BridgeProfile, where_clause: str) -> str:
    """Build ``bb300-Update``'s statement for one bridge.

    [common/finalMT.cbl:L774-L815]::

        UPDATE `SYSFINAL-REC` SET `FINAL-ACC-REC-KEY`="026", `AR1`="x"
         WHERE `FINAL-ACC-REC-KEY`="026";

    Note that the primary key is assigned in the ``SET`` list as well as tested
    in the ``WHERE`` - the generated builder emits every column without
    exception, and that includes the key. Preserved.

    Args:
        bridge: The bridge's profile.
        where_clause: The predicate ``ba090-Process-Rewrite`` built, already
            carrying its own ``%s``.

    Returns:
        The statement, with one ``%s`` per column in ordinal order followed by
        the predicate's own placeholder.
    """
    plans = column_plans_for(bridge.table)
    assignments = ", ".join(f"{plan.quoted}=%s" for plan in plans)
    return (
        f"UPDATE {quote_identifier(bridge.table)} SET {assignments}"
        f" WHERE {where_clause};"
    )


def _execute_command(
    bridge: BridgeProfile, statement: str, parameters: Sequence[Any]
) -> _CommandOutcome:
    """``PERFORM MYSQL-1210-COMMAND THRU MYSQL-1219-EXIT``.

    The frozen paragraph hands the assembled text to the client library and
    leaves the row count in ``WS-MYSQL-Count-Rows``; it does not raise, and
    every caller discovers a failure by testing that count and then asking the
    driver for an error number. This reproduces exactly that shape: a driver
    exception becomes ``count_rows`` zero plus the three diagnostic fields,
    which is what the caller's own ``if WS-MYSQL-COUNT-ROWS not = 1`` block
    then reads.

    Args:
        bridge: The bridge's profile, for the log line.
        statement: The statement text.
        parameters: The values to bind, in the statement's own order.

    Returns:
        The outcome, for the caller to test.

    Raises:
        RuntimeError: If no connection is open. NO COBOL COUNTERPART: the
            frozen bridge would hand a null connection handle to the client
            library, whose behaviour is undefined. Refusing loudly is the only
            honest option, because reporting a fabricated error number would
            put a value into ``SQL-Err`` that no driver ever produced - and
            ``SQL-Err`` is observable.
    """
    connection = handler_state().connection
    if connection is None:
        raise RuntimeError(
            f"{bridge.program}: no connection is open. The caller must issue "
            "the System-Open verb before any other, exactly as the compiled "
            "chain does [common/systemMT.cbl:L592-L594]."
        )
    try:
        with execute_statement(connection, statement, parameters) as cursor:
            count_rows = int(cursor.rowcount or 0)
    except Exception as error:  # any driver failure takes this path
        status: DbErrorStatus = mysql_1100_db_error(
            errno=str(getattr(error, "errno", "") or ""),
            message=str(getattr(error, "msg", None) or error),
            sql_state=str(getattr(error, "sqlstate", "") or ""),
            command=statement,
        )
        _LOG.warning(
            "%s: the command failed at the driver; errno=%s sqlstate=%s",
            bridge.program,
            sanitise_for_log(status.sql_err),
            sanitise_for_log(status.sql_state),
        )
        state = handler_state()
        state.mysql_count_rows[bridge.program] = 0
        return _CommandOutcome(
            count_rows=0,
            errno=status.sql_err.strip() or ERRNO_NO_ERROR,
            message=status.sql_msg,
            sql_state=status.sql_state,
            statement=statement,
        )
    handler_state().mysql_count_rows[bridge.program] = count_rows
    return _CommandOutcome(
        count_rows=count_rows,
        errno=ERRNO_NO_ERROR,
        message=" " * SQL_MSG_WIDTH,
        sql_state=" " * SQL_STATE_WIDTH,
        statement=statement,
    )


def _bb200_insert(
    bridge: BridgeProfile, host_variables: Mapping[str, Any]
) -> _CommandOutcome:
    """``bb200-Insert`` - one row, every column, values bound.

    Args:
        bridge: The bridge's profile.
        host_variables: The host variables keyed by column name.

    Returns:
        The command outcome.
    """
    plans = column_plans_for(bridge.table)
    parameters = [
        _bound_parameter(plan, host_variables[plan.column]) for plan in plans
    ]
    return _execute_command(bridge, _insert_statement(bridge), parameters)


def _bb300_update(
    bridge: BridgeProfile,
    host_variables: Mapping[str, Any],
    where_clause: str,
    where_parameter: str,
) -> _CommandOutcome:
    """``bb300-Update`` - one row, every column, plus the predicate.

    Args:
        bridge: The bridge's profile.
        host_variables: The host variables keyed by column name.
        where_clause: The predicate text, carrying its own ``%s``.
        where_parameter: The predicate's bound value - the quoted digit string
            the frozen builder put into the text.

    Returns:
        The command outcome.
    """
    plans = column_plans_for(bridge.table)
    parameters = [
        _bound_parameter(plan, host_variables[plan.column]) for plan in plans
    ]
    parameters.append(where_parameter)
    return _execute_command(
        bridge, _update_statement(bridge, where_clause), parameters
    )


def _rewrite_predicate(
    bridge: BridgeProfile, subscript: int | None
) -> tuple[str, str]:
    """Build ``ba090-Process-Rewrite``'s ``WHERE``, and its logged text.

    Verbatim, from ``systemMT`` [common/systemMT.cbl:L981-L995]::

        set      KOR-x1 to 1
        move     KOR-offset (KOR-x1) to K
        move     KOR-length (KOR-x1) to L
        move     spaces to WS-Where
        move     1   to J
        string   "`"  KeyName (KOR-x1)  "`"  '="'
        *>              System-Record (K:L)       delimited by size
                 "1"                        *> its record 1
                 '"'   into WS-Where with pointer J

    DIVERGENCE 11: ``systemMT`` and ``sys4MT`` name a bare ``"1"``
    [common/systemMT.cbl:L992, common/sys4MT.cbl:L688] while ``dfltMT`` and
    ``finalMT`` name ``WS-Key``, the ``OCCURS`` subscript
    [common/dfltMT.cbl:L664, common/finalMT.cbl:L663]. Both bridges that use
    the subscript have a commented-out alternative naming the record substring
    and another naming the host variable, which is the maintainer recording
    that he tried three sources for the same value.

    ``K`` and ``L`` are loaded from the key table and then NEVER USED on this
    path, because the only surviving alternative is the literal or the
    subscript - the record-substring line that would have used them is
    commented out. RECORDED as a representation-only omission.

    Args:
        bridge: The bridge's profile.
        subscript: The ``OCCURS`` subscript for the two table-shaped bridges.

    Returns:
        The predicate carrying its ``%s``, and the value to bind.

    Raises:
        ValueError: If a subscript is needed and absent.
    """
    key = key_of_reference(bridge.table, 1)
    column = quote_identifier(key.column_name)
    if bridge.rewrite_key_is_literal_one:
        return (f"{column}=%s", "1")
    if subscript is None:
        raise ValueError(
            f"{bridge.program} rewrites by the OCCURS subscript "
            f"{OCCURS_SUBSCRIPT_PRIMARY_KEYS[bridge.table]}, so it is required"
        )
    return (
        f"{column}=%s",
        _numeric_move_text(subscript, REWRITE_KEY_DIGITS),
    )


#: ``ba999-End`` - the label that logs before falling into ``ba999-Exit``
#: [common/systemMT.cbl:L1048, common/dfltMT.cbl:L749,
#: common/finalMT.cbl:L721, common/sys4MT.cbl:L766].
BA999_END: Final[str] = "ba999-End"

#: ``ba999-Exit`` - the label that does NOT log
#: [common/systemMT.cbl:L1060, common/dfltMT.cbl:L757,
#: common/finalMT.cbl:L729, common/sys4MT.cbl:L774]. Reaching this label
#: instead of ``ba999-End`` suppresses the bridge's own log record, which is
#: DIVERGENCE 16: every write and rewrite path in ``dfltMT``, ``finalMT`` and
#: ``sys4MT`` goes here and logs itself inline, while ``systemMT``'s go to
#: ``ba999-End`` and are logged by it.
BA999_EXIT: Final[str] = "ba999-Exit"


def _report_write_failure(
    bridge: BridgeProfile,
    file_access: FileAccess,
    outcome: _CommandOutcome,
) -> None:
    """The ``if WS-MYSQL-COUNT-ROWS not = 1`` block of ``ba070``.

    The frozen shape, from ``finalMT`` [common/finalMT.cbl:L616-L628]::

        if       WS-MYSQL-COUNT-ROWS not = 1
                 call "MySQL_errno" using WS-MYSQL-Error-Number
                 if    WS-MYSQL-Error-Number  not = "0  "
                       call "MySQL_error" using Ws-Mysql-Error-Message
                       move WS-MYSQL-Error-Number  to SQL-Err
                       move WS-MYSQL-Error-Message to SQL-Msg
                       if    SQL-Err (1:4) = "1062" or = "1022"
                             move 22 to fs-reply
                       else
                             move 99 to fs-reply
                       end-if
                 end-if
        end-if

    Four things about it are load-bearing:

    * ``WE-Error`` is NEVER set on this path, in ANY of the four bridges. A
      failed write reports through ``FS-Reply`` alone, so a caller that tests
      only ``WE-Error`` sees a clean write. Reproduced, not corrected -
      Agent Action Plan section 0.8.2: "A defect reproduced is correct".
    * the errno is tested first, and if the driver reports no error the row
      count mismatch is SWALLOWED - no status, no message, no trace. This is
      reachable: an ``INSERT`` that affects no row without erroring leaves the
      count at zero with errno ``"0  "``.
    * ``SQL-Err (1:4)`` reads FOUR of the field's five characters
      [copybooks/wsfnctn.cob:L49], which is why the shared test in
      ``dal/status.py`` slices before comparing; and
    * DIVERGENCE 12: ``dfltMT``'s entire block is COMMENTED OUT
      [common/dfltMT.cbl:L616-L632], so ANOMALY NEW-7 - ``dfltMT``'s write can
      never report a failure at all. The profile carries that as
      ``duplicate_check_is_live`` False and this function returns at once.

    ``systemMT`` alone adds ``or Sql-State = "23000"`` to the duplicate test
    [common/systemMT.cbl:L963] because it is the only one of the four that
    captured a SQLSTATE two lines earlier [common/systemMT.cbl:L957]; the other
    three never call for one, so their ``SQL-State`` still holds whatever
    ``ba010-Initialise`` left. DIVERGENCE 13.

    ``sys4MT`` writes the duplicate test in COBOL's abbreviated combined
    relation form [common/sys4MT.cbl:L651]::

        if    SQL-Err (1:4) = "1062" or "1022"

    which expands to the same two comparisons as ``finalMT``'s explicit form.
    A stylistic divergence with no behavioural difference - recorded here so
    that nobody later reads it as a defect and "fixes" it.

    Args:
        bridge: The bridge's profile.
        file_access: The caller's status block, updated in place.
        outcome: What the command reported.
    """
    if not bridge.duplicate_check_is_live:
        # ANOMALY NEW-7 [common/dfltMT.cbl:L616-L632]: the block is commented
        # out, so the count mismatch is never even looked at. Also recorded in
        # docs/migration/anomaly-log.md.
        return
    if outcome.count_rows == 1:
        return
    logging_data = file_access.logging_data
    if bridge.captures_sqlstate:
        #  `call "MySQL_sqlstate" ... move WS-MYSQL-SqlState to SQL-State`
        #  sits INSIDE the count block but OUTSIDE the errno test
        #  [common/systemMT.cbl:L951-L953], so systemMT records a SQLSTATE even
        #  when the errno test below swallows the mismatch. The other three
        #  never ask for one - DIVERGENCE 13.
        logging_data.sql_state = _move_into(
            logging_data.sql_state, outcome.sql_state, signed=None
        )
    if not _errno_indicates_failure(bridge, outcome.errno):
        # The mismatch is swallowed. Deliberate silence, preserved.
        return
    logging_data.sql_err = _move_into(
        logging_data.sql_err, outcome.errno, signed=None
    )
    logging_data.sql_msg = _move_into(
        logging_data.sql_msg, outcome.message, signed=None
    )
    sql_state = (
        logging_data.sql_state
        if bridge.duplicate_test_includes_sqlstate
        else ""
    )
    if is_duplicate_key_bridge_level(logging_data.sql_err, sql_state):
        file_access.fs_reply = int(FsReply.DUPLICATE_KEY)
    else:
        file_access.fs_reply = int(FsReply.ERROR)


def _report_rewrite_failure(
    bridge: BridgeProfile,
    file_access: FileAccess,
    outcome: _CommandOutcome,
) -> bool:
    """The ``if WS-MYSQL-COUNT-ROWS not = 1`` block of ``ba090``.

    Identical in all four bridges [common/systemMT.cbl:L999-L1008,
    common/dfltMT.cbl:L690-L700, common/finalMT.cbl:L675-L684,
    common/sys4MT.cbl:L723-L733] and simpler than the write's, because a
    rewrite has no duplicate case::

        move 99 to fs-reply
        move 994 to WE-Error

    994 is ``WeError.REWRITE_SQLSTATE_NOT_00000``, whose name records what the
    maintainer's own error table says it means. The errno guard applies here
    too, with the same swallowing consequence.

    Args:
        bridge: The bridge's profile.
        file_access: The caller's status block, updated in place.
        outcome: What the command reported.

    ANOMALY NEW-19, reproduced: a rewrite that matches NO row reports SUCCESS.
    The 99/994 pair is nested inside the errno test, so ``count_rows`` of zero
    with a clean errno - which is exactly what an ``UPDATE`` of a key that is
    not present produces - sets no status at all. ``ba090`` cleared
    ``FS-Reply`` and ``WE-Error`` to zero on entry
    [common/systemMT.cbl:L976, common/sys4MT.cbl:L707-L709], and the two
    ``OCCURS``-shaped bridges clear them again after their loop
    [common/dfltMT.cbl:L706-L708, common/finalMT.cbl:L691-L693], so the caller
    sees a clean rewrite for a row that was never touched. Recorded in
    docs/migration/anomaly-log.md; not corrected.

    Returns:
        Whether the COUNT block was ENTERED - which is ``count_rows`` not 1,
        NOT whether a failure was reported. Every transfer and every log call
        in the four callers hangs off the count test rather than off the errno
        test nested inside it [common/systemMT.cbl:L1004-L1018,
        common/sys4MT.cbl:L705-L722, common/dfltMT.cbl:L685-L700,
        common/finalMT.cbl:L675-L684], so the callers need the outer test's
        answer, not the inner one's.
    """
    if outcome.count_rows == 1:
        return False
    logging_data = file_access.logging_data
    if bridge.captures_sqlstate:
        #  Unconditional inside the count block [common/systemMT.cbl:L1006-
        #  L1008], as in the write. DIVERGENCE 13.
        logging_data.sql_state = _move_into(
            logging_data.sql_state, outcome.sql_state, signed=None
        )
    if not _errno_indicates_failure(bridge, outcome.errno):
        #  ANOMALY NEW-19: the mismatch is swallowed, and the caller still
        #  takes the count block's transfer.
        return True
    logging_data.sql_err = _move_into(
        logging_data.sql_err, outcome.errno, signed=None
    )
    logging_data.sql_msg = _move_into(
        logging_data.sql_msg, outcome.message, signed=None
    )
    file_access.fs_reply = int(FsReply.ERROR)
    file_access.we_error = int(WeError.REWRITE_SQLSTATE_NOT_00000)
    return True


def _occurs_entry_is_empty(bridge: BridgeProfile, entry: Any) -> bool:
    """The two bridges' "do not write out blank data" guards.

    ``dfltMT`` tests all three of its data fields
    [common/dfltMT.cbl:L602-L606]::

        if       Def-Acs (A)   = zero    *> check for empty occurs
            and  Def-Codes (A) = spaces
            and  Def-Vat (A)   = space
                 exit perform cycle
        end-if

    ``finalMT`` has only one data field, so its guard is one line
    [common/finalMT.cbl:L609-L611]::

        if       AR1 (A) = spaces              *> dont write out blank data
                 exit perform cycle
        end-if

    Note what the guard means for table state: an occurrence the operator has
    genuinely cleared is not written, so a row that was present before a write
    of a cleared entry SURVIVES. Neither bridge issues a delete. Preserved.

    The guard is evaluated on the RECORD's fields, not on the host variables,
    which matters because it runs BEFORE the load - so a non-numeric
    ``Def-Acs`` that the load would have turned into zeroes still counts as
    data here [common/dfltMT.cbl:L602-L607].

    Args:
        bridge: The bridge's profile.
        entry: One ``OCCURS`` occurrence - a group for ``dfltMT``, a bare
            character item for ``finalMT``.

    Returns:
        Whether the frozen guard would skip this occurrence.
    """
    for plan in column_plans_for(bridge.table):
        if not plan.loads_from_record or plan.route is None:
            continue
        value = _route_value(entry, plan.route)
        if plan.is_numeric:
            try:
                if _as_decimal(value) != 0:
                    return False
            except ArithmeticError:
                #  A non-numeric zoned field is not zero, so it is data.
                return False
        elif str(value).strip(" ") != "":
            return False
    return True


def _log_where(clause: str, parameter: str) -> str:
    """Reproduce ``move WS-Where (1:J) to WS-Log-Where``.

    ``ba090-Process-Rewrite`` builds its predicate into ``WS-Where`` and then
    copies the used prefix into the log block [common/systemMT.cbl:L996,
    common/dfltMT.cbl:L668, common/finalMT.cbl:L668, common/sys4MT.cbl:L716].
    ``J`` is the ``STRING`` pointer, so the slice is everything written
    plus the position the pointer advanced to - the code slices ``1:J``
    rather than ``1:J - 1``, so the copied text carries ONE TRAILING SPACE.
    Preserved, because ``WS-Log-Where`` reaches the log record.

    The text differs from the frozen one only in that the value is shown where
    the frozen builder interpolated it, since the executed statement binds it.

    Args:
        clause: The predicate carrying its ``%s``.
        parameter: The value that will be bound.

    Returns:
        Exactly ``WS_LOG_WHERE_WIDTH`` characters.
    """
    rendered = clause.replace("%s", f'"{parameter}"') + " "
    return rendered[:WS_LOG_WHERE_WIDTH].ljust(WS_LOG_WHERE_WIDTH)


def _ba070_process_write(
    bridge: BridgeProfile,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    record: Any,
) -> str:
    """``ba070-Process-Write`` - insert, in each bridge's own shape.

    [common/systemMT.cbl:L940-L1022], [common/dfltMT.cbl:L592-L637],
    [common/finalMT.cbl:L600-L634], [common/sys4MT.cbl:L631-L665].

    The two single-row bridges write ONE row and stamp ``WS-File-Key`` with the
    literal 1 [common/systemMT.cbl:L942, common/sys4MT.cbl:L635], because both
    tables only ever hold row 1. The two table-shaped bridges walk their whole
    ``OCCURS`` table and insert every non-empty occurrence, stamping
    ``WS-File-Key`` with the subscript so that a caller reading the log can see
    which occurrence failed [common/dfltMT.cbl:L611, common/finalMT.cbl:L612].

    Statement order is preserved exactly, and it differs between them:
    ``sys4MT`` loads the host variables and stamps the key BEFORE clearing the
    status [common/sys4MT.cbl:L634-L637] while ``systemMT`` clears
    ``SQL-State`` as well [common/systemMT.cbl:L945], which the other three
    never touch here. Agent Action Plan section 0.3.3 is the reason order is
    honoured to this level: anything else "would obscure the exact statement
    ordering that the state diff is sensitive to."

    ANOMALY NEW-11 [common/finalMT.cbl:L621-L634]: ``finalMT`` clears the
    status ONCE, before the loop. A failure on occurrence five therefore
    survives into the caller even though occurrences six through twenty-six
    then succeed, because no success path clears it and there is no clear at
    the exit. With ``Testing-1`` on, the log block wipes it instead - so the
    status a caller sees depends on a testing switch. Both reproduced. Also
    recorded in docs/migration/anomaly-log.md.

    Args:
        bridge: The bridge's profile.
        file_access: The caller's status block, updated in place.
        dal_common: The shared flags block.
        record: The record to write.

    Returns:
        The exit label reached, which decides whether ``ba999-End`` logs.
    """
    logging_data = file_access.logging_data
    if bridge.occurs_bound is None:
        # systemMT [common/systemMT.cbl:L940-L949] and sys4MT
        # [common/sys4MT.cbl:L631-L638], in their own statement order.
        host_variables = _bb000_hv_load(bridge, record)
        logging_data.ws_file_key = _ws_file_key_move("1")
        file_access.fs_reply = int(FsReply.SUCCESS)
        file_access.we_error = int(WeError.SUCCESS)
        if bridge.captures_sqlstate:
            # systemMT alone clears SQL-State here
            # [common/systemMT.cbl:L945]. DIVERGENCE 14.
            logging_data.sql_state = _zero_filled(SQL_STATE_WIDTH)
        logging_data.sql_msg = " " * SQL_MSG_WIDTH
        logging_data.sql_err = _zero_filled(SQL_ERR_WIDTH)
        logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NO_WRITE
        outcome = _bb200_insert(bridge, host_variables)
        if bridge.guards_on_incoming_status and (
            file_access.fs_reply != int(FsReply.SUCCESS)
            or file_access.we_error != int(WeError.SUCCESS)
        ):
            # sys4MT's 28/09/16 guard, placed AFTER the insert
            # [common/sys4MT.cbl:L640-L643]. GO TO class 3 - section exit.
            return BA999_EXIT
        _report_write_failure(bridge, file_access, outcome)
        if not bridge.write_exits_via_ba999_end:
            #  sys4MT logs itself and then transfers
            #  [common/sys4MT.cbl:L660-L664]. DIVERGENCE 16.
            if _testing_1(dal_common):
                ca_process_logs(file_access, dal_common)
            return BA999_EXIT
        #  systemMT has no log of its own here - `go to ba999-End` is the very
        #  next statement after the count block [common/systemMT.cbl:L968], and
        #  ba999-End is what logs.
        return BA999_END

    # dfltMT [common/dfltMT.cbl:L592-L637] and finalMT
    # [common/finalMT.cbl:L600-L634]: clear once, then walk the table.
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    logging_data.sql_msg = " " * SQL_MSG_WIDTH
    logging_data.sql_err = _zero_filled(SQL_ERR_WIDTH)
    logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NO_WRITE
    table = _route_value(record, OCCURS_TABLE_ROUTES[bridge.table])
    for index in range(1, bridge.occurs_bound + 1):
        entry = table[index - 1]
        if _occurs_entry_is_empty(bridge, entry):
            # GO TO class 1 - "exit perform cycle" is the loop's own continue
            # [common/dfltMT.cbl:L605, common/finalMT.cbl:L610].
            continue
        logging_data.ws_file_key = _ws_file_key_move(
            _numeric_move_text(index, OCCURS_COUNTER_DIGITS)
        )
        host_variables = _bb000_hv_load(bridge, entry, subscript=index)
        outcome = _bb200_insert(bridge, host_variables)
        _report_write_failure(bridge, file_access, outcome)
        if _testing_1(dal_common):
            ca_process_logs(file_access, dal_common)
            if bridge.clears_error_after_logging:
                # ANOMALY NEW-10 [common/finalMT.cbl:L631-L633]: logging wipes
                # the failure it just logged, so whether the caller sees the
                # failure depends on the Testing-1 switch. Also recorded in
                # docs/migration/anomaly-log.md.
                file_access.fs_reply = int(FsReply.SUCCESS)
                logging_data.sql_err = _zero_filled(SQL_ERR_WIDTH)
                logging_data.sql_msg = " " * SQL_MSG_WIDTH
    # GO TO class 3 [common/dfltMT.cbl:L637, common/finalMT.cbl:L634].
    return BA999_EXIT


def _ba090_process_rewrite(
    bridge: BridgeProfile,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    record: Any,
) -> str:
    """``ba090-Process-Rewrite`` - update, in each bridge's own shape.

    [common/systemMT.cbl:L977-L1022], [common/dfltMT.cbl:L639-L709],
    [common/finalMT.cbl:L636-L694], [common/sys4MT.cbl:L667-L741].

    ANOMALY NEW-8 and NEW-9: both table-shaped bridges end with an
    UNCONDITIONAL clear of all five status fields
    [common/dfltMT.cbl:L706-L708], [common/finalMT.cbl:L691-L693], which runs
    after the loop and so after the ``exit perform`` a failure took.
    The 99 and the 994 they had just set are wiped, so NEITHER bridge can ever
    report a rewrite failure to its caller. Reproduced exactly. Also recorded
    in docs/migration/anomaly-log.md.

    ANOMALY NEW-12: neither table-shaped bridge clears the status on ENTRY
    [common/dfltMT.cbl:L639-L644], [common/finalMT.cbl:L636-L640], so until the
    post-loop clear runs they operate on whatever the caller left behind - and
    if the ``OCCURS`` table is entirely empty the loop body never runs, so the
    post-loop clear is the ONLY thing that touches the status and an inbound
    non-zero is silently zeroed. Reproduced. Also in the anomaly log.

    DIVERGENCE 10: ``dfltMT`` sets the paragraph number INSIDE its loop
    [common/dfltMT.cbl:L660] while ``finalMT`` sets it once before
    [common/finalMT.cbl:L639]; the number reaches every log record, so the
    difference is observable.

    DIVERGENCE 9: ``dfltMT`` leaves its loop on a failure
    [common/dfltMT.cbl:L702] while ``finalMT`` carries on through all
    twenty-six [common/finalMT.cbl:L685-L690]. So a mid-table failure abandons
    the remaining defaults but not the remaining final-account names.

    Args:
        bridge: The bridge's profile.
        file_access: The caller's status block, updated in place.
        dal_common: The shared flags block.
        record: The record to rewrite.

    Returns:
        The exit label reached.
    """
    logging_data = file_access.logging_data
    if bridge.occurs_bound is None:
        # systemMT [common/systemMT.cbl:L977-L997] and sys4MT
        # [common/sys4MT.cbl:L667-L721].
        host_variables = _bb000_hv_load(bridge, record)
        logging_data.ws_file_key = _ws_file_key_move("1")
        logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NO_REWRITE
        file_access.fs_reply = int(FsReply.SUCCESS)
        file_access.we_error = int(WeError.SUCCESS)
        logging_data.sql_msg = " " * SQL_MSG_WIDTH
        logging_data.sql_err = _zero_filled(SQL_ERR_WIDTH)
        if bridge.captures_sqlstate:
            logging_data.sql_state = _zero_filled(SQL_STATE_WIDTH)
        clause, parameter = _rewrite_predicate(bridge, None)
        logging_data.ws_log_where = _log_where(clause, parameter)
        outcome = _bb300_update(bridge, host_variables, clause, parameter)
        if bridge.guards_on_incoming_status and (
            file_access.fs_reply != int(FsReply.SUCCESS)
            or file_access.we_error != int(WeError.SUCCESS)
        ):
            # sys4MT's guard, again AFTER the command
            # [common/sys4MT.cbl:L718-L721]. GO TO class 3.
            return BA999_EXIT
        if _report_rewrite_failure(bridge, file_access, outcome):
            #  The transfer belongs to the COUNT block, NOT to the errno test
            #  nested inside it [common/systemMT.cbl:L1017,
            #  common/sys4MT.cbl:L722], so it is taken whether or not a status
            #  was set - which is how ANOMALY NEW-19's silent no-op rewrite
            #  ALSO skips the clear-to-zero that follows.
            if not bridge.write_exits_via_ba999_end:
                #  sys4MT logs before its transfer, unconditionally inside the
                #  count block [common/sys4MT.cbl:L718-L720]. DIVERGENCE 16:
                #  systemMT has no log here at all, because its `ba999-End`
                #  does it [common/systemMT.cbl:L1017].
                if _testing_1(dal_common):
                    ca_process_logs(file_access, dal_common)
                return BA999_EXIT
            return BA999_END
        #  The clear runs only when the count WAS 1
        #  [common/systemMT.cbl:L1019-L1022, common/sys4MT.cbl:L723-L726].
        file_access.fs_reply = int(FsReply.SUCCESS)
        file_access.we_error = int(WeError.SUCCESS)
        logging_data.sql_err = _zero_filled(SQL_ERR_WIDTH)
        logging_data.sql_msg = " " * SQL_MSG_WIDTH
        if bridge.captures_sqlstate:
            #  Only systemMT clears SQL-State here [common/systemMT.cbl:L1019];
            #  sys4MT's clear names FS-Reply, WE-Error, SQL-Err and SQL-Msg and
            #  leaves SQL-State alone [common/sys4MT.cbl:L723-L725].
            #  DIVERGENCE 14.
            logging_data.sql_state = _zero_filled(SQL_STATE_WIDTH)
        if bridge.write_exits_via_ba999_end:
            return BA999_END
        return BA999_EXIT

    # dfltMT and finalMT. NO entry clear - ANOMALY NEW-12.
    if not bridge.rewrite_paragraph_no_inside_loop:
        logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NO_REWRITE
    table = _route_value(record, OCCURS_TABLE_ROUTES[bridge.table])
    for index in range(1, bridge.occurs_bound + 1):
        entry = table[index - 1]
        if _occurs_entry_is_empty(bridge, entry):
            continue  # GO TO class 1 - exit perform cycle
        logging_data.ws_file_key = _ws_file_key_move(
            _numeric_move_text(index, OCCURS_COUNTER_DIGITS)
        )
        host_variables = _bb000_hv_load(bridge, entry, subscript=index)
        if bridge.rewrite_paragraph_no_inside_loop:
            logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NO_REWRITE
        clause, parameter = _rewrite_predicate(bridge, index)
        logging_data.ws_log_where = _log_where(clause, parameter)
        outcome = _bb300_update(bridge, host_variables, clause, parameter)
        failed = _report_rewrite_failure(bridge, file_access, outcome)
        if failed and bridge.rewrite_loop_exits_on_mismatch:
            if _testing_1(dal_common):
                ca_process_logs(file_access, dal_common)
            # GO TO class 2 - forward terminator. The post-loop work below
            # STILL RUNS, which is exactly why NEW-8 wipes the status
            # [common/dfltMT.cbl:L702-L708].
            break
        if _testing_1(dal_common):
            ca_process_logs(file_access, dal_common)
            if bridge.clears_error_after_logging:
                #  ANOMALY NEW-10 again, on the rewrite path
                #  [common/finalMT.cbl:L688-L690]: the log block WIPES the
                #  99/994 it has just written out, so what the caller sees
                #  depends on a compile-time testing switch. finalMT only -
                #  DIVERGENCE 11.
                file_access.fs_reply = int(FsReply.SUCCESS)
                logging_data.sql_err = _zero_filled(SQL_ERR_WIDTH)
                logging_data.sql_msg = " " * SQL_MSG_WIDTH
    # ANOMALY NEW-8 / NEW-9 - the unconditional clear.
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    logging_data.sql_err = _zero_filled(SQL_ERR_WIDTH)
    logging_data.sql_msg = " " * SQL_MSG_WIDTH
    return BA999_EXIT


def _positioning_where_text(bridge: BridgeProfile) -> str:
    """Reproduce the text ``ba040``'s positioning stage puts in ``WS-Where``.

    Verbatim, from ``systemMT`` [common/systemMT.cbl:L665-L678]::

        string   "`"                   delimited by size
                 KeyName (KOR-x1)      delimited by space
                 "`"                   delimited by size
                 " > "                 delimited by size
                 "000"                 delimited by size
                 ' ORDER BY '          delimited by size
                 "`"                   delimited by size
                 keyname (KOR-x1)      delimited by space
                 "`"                   delimited by size
                   ' ASC'              delimited by size
                                into ws-Where
                                with pointer J

    DIVERGENCE 2: ``systemMT`` emits the low key UNQUOTED
    [common/systemMT.cbl:L670] while the other three emit ``'"000"'``, quoted
    [common/dfltMT.cbl:L476, common/finalMT.cbl:L477, common/sys4MT.cbl:L503].
    MariaDB coerces an unquoted ``000`` to the number zero and a quoted
    ``"000"`` to the string, and for these key columns the comparison lands the
    same way either side of the coercion - but the two statements are not the
    same text, and the text reaches ``WS-Log-Where`` and so a log record. The
    executed statement comes from :data:`SEQUENTIAL_READ_START`, which
    ``dal/cursor_state.py`` already drives per bridge as its anomaly A9; this
    function reproduces only the LOGGED rendering.

    Args:
        bridge: The bridge's profile.

    Returns:
        The predicate text, as the frozen builder would have left it.
    """
    key = key_of_reference(bridge.table, 1)
    start = SEQUENTIAL_READ_START[bridge.table]
    #  `KeyName (KOR-x1) delimited by space` sends up to the first space, so a
    #  key name padded in the key table contributes only its own characters
    #  [common/systemMT.cbl:L667].
    name = key.key_name.split(" ")[0]
    low = f'"{start.low_key}"' if bridge.low_key_is_quoted else start.low_key
    return (
        f"`{name}` {start.relation.token} {low}"
        f" ORDER BY `{name}` ASC"
    )


def _read_one_row(bridge: BridgeProfile) -> CursorOutcome:
    """Issue one ``ba040`` fetch, positioning first if there is no position.

    Delegates the mechanics to :func:`acas_posting.dal.cursor_state.read_next`,
    which reproduces the identical two-stage shape from a sibling bridge and
    carries its anomalies A1, A9, A11 and A12 with it. ``file_access`` is NOT
    passed, deliberately: that argument exists to enable anomaly A10, the
    sticky end of file that ``ba041-Reread`` implements, and NONE of these four
    bridges has a ``ba041`` paragraph. Two of them do carry the same idea
    inline as their ``if fs-reply = 10`` "belts and braces" test
    [common/systemMT.cbl:L924-L928, common/sys4MT.cbl:L618-L622], which is
    reproduced HERE in :func:`_ba040_process_read_next` rather than delegated,
    because their tag is ``"EOF3"`` and not the sibling's.

    Args:
        bridge: The bridge's profile.

    Returns:
        The outcome, with the row keyed by column name or ``None``.

    Raises:
        RuntimeError: If no connection is open, for the reason
            :func:`_execute_command` documents.
    """
    state = handler_state()
    connection = state.connection
    if connection is None:
        raise RuntimeError(
            f"{bridge.program}: no connection is open. The caller must issue "
            "the System-Open verb first [common/systemMT.cbl:L592-L594]."
        )
    # A dead session - which anomaly A-8 makes reachable, since any bridge's
    # close takes the one process handle down - must arrive as a status pair and
    # not as a raise, because the frozen bridge has no cursor-acquisition step
    # to fail at: its one `call "MySQL_query"` is what reports
    # [copybooks/mysql-procedures.cpy:L165-L166]. `acquire_cursor` defers the
    # failure to the `execute` inside `read_next`, where it is already handled.
    cursor = acquire_cursor(connection)
    try:
        outcome = read_next(
            cursor,
            bridge.table,
            #  `set KOR-x1 to 1  *> 1 = Primary, ...` - all four bridges
            #  hard-code the primary key of reference and none of the four
            #  tables has a second one [common/systemMT.cbl:L664,
            #  common/dfltMT.cbl:L470, common/finalMT.cbl:L471,
            #  common/sys4MT.cbl:L497]. Named rather than defaulted so the
            #  hard-coding is visible - anomaly A12 of dal/cursor_state.
            slot=CursorSlot.PRIMARY,
            states=state.cursors,
        )
    finally:
        cursor.close()
    if outcome.row is None and outcome.file_key == READ_END_TAGS["no_rows"]:
        #  The positioning stage stored nothing, so `WS-MYSQL-Count-Rows` is
        #  zero for the rest of this bridge's life until another command runs.
        state.mysql_count_rows[bridge.program] = 0
    elif outcome.row is not None:
        #  `MYSQL-1220-STORE-RESULT` leaves the stored count, which is at least
        #  one whenever a row was delivered [copybooks/mysql-procedures.cpy].
        state.mysql_count_rows[bridge.program] = max(
            state.mysql_count_rows.get(bridge.program, 0), 1
        )
    return outcome


def _ba040_process_read_next(
    bridge: BridgeProfile,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    record: Any,
) -> str:
    """``ba040-Process-Read-Next`` - the verb function codes 3 AND 4 reach.

    [common/systemMT.cbl:L652-L938], [common/dfltMT.cbl:L459-L590],
    [common/finalMT.cbl:L460-L598], [common/sys4MT.cbl:L486-L628].

    ⭐ THE HANDLER PUBLISHES ``System-Read-Indexed`` AND NOTHING ELSE
    [copybooks/Proc-ACAS-FH-Calls.cob:L190-L230], yet every one of the four
    bridges routes BOTH function code 3 and function code 4 into this
    sequential paragraph [common/systemMT.cbl:L578-L581, and the same two
    ``when`` clauses in the other three]. There is no ``ba050`` and no keyed
    read anywhere in the four. So a caller asking for a keyed read gets a
    sequential walk from a hard-coded low key, and for the two single-row
    tables that lands on row 1 - which is the row it wanted. RECORDED as
    anomaly NEW-15, reproduced exactly, not corrected: adding a keyed read
    would be new behaviour.

    Two shapes, chosen by whether the table is the flat image of one record or
    the flat image of an ``OCCURS`` table:

    * ``systemMT`` and ``sys4MT`` deliver ONE row per call and unload it into
      the record [common/systemMT.cbl:L930-L936, common/sys4MT.cbl:L624-L627];
    * ``dfltMT`` and ``finalMT`` deliver the WHOLE table in one call, walking
      until the ``OCCURS`` bound and storing each row into the occurrence its
      own key column names [common/dfltMT.cbl:L579-L582,
      common/finalMT.cbl:L587].

    THE ANOMALIES ON THIS PATH, all reproduced and all in
    docs/migration/anomaly-log.md:

    * NEW-4 - the two table-shaped bridges end with an UNCONDITIONAL
      ``move zero to fs-reply WE-Error`` after the loop
      [common/dfltMT.cbl:L588-L589, common/finalMT.cbl:L596-L597], which runs
      after every ``exit perform``. The 10 they had just set for end of data,
      and the offending key they had just put in ``WE-Error`` for ``EOF3``, are
      both wiped. NEITHER BRIDGE CAN REPORT END OF FILE for anything except a
      wholly empty table, whose branch escapes to ``ba998-Free`` instead.
    * NEW-13 - ``dfltMT`` walks 1 to 32 and rejects a key of 33 or more as
      ``EOF3`` [common/dfltMT.cbl:L562-L563], but its copybook declares
      THIRTY-THREE occurrences [copybooks/wsdflt.cob]. Occurrence 33 is
      unreachable through the bridge in either direction. Reproduced: the bound
      on the profile is 32, not 33.
    * NEW-16 - the ``EOF3`` branch of the two table-shaped bridges sets
      ``WE-Error`` to the OFFENDING KEY VALUE and never touches ``FS-Reply``
      [common/dfltMT.cbl:L560-L565, common/finalMT.cbl:L548-L553], so
      ``WE-Error`` briefly holds a row number rather than an error code. NEW-4
      then wipes it. Both reproduced.
    * NEW-17 - the loop's own terminator tests ``A > 32 or = zero``
      [common/dfltMT.cbl:L556] and ``A > 26 or = zero``
      [common/finalMT.cbl:L544]. ``A`` starts at 1 and only increments, and the
      ``until`` clause already excludes the over-bound case, so BOTH added
      sub-conditions are dead. Preserved as unreachable branches rather than
      deleted, because deleting them would hide that the maintainer wrote them.
    * NEW-18 - the ``EOF2`` branch is nearly dead. It tests
      ``WS-MYSQL-Count-Rows = zero`` AFTER a fetch, but nothing between the
      positioning and the fetch can change that count, and a zero count was
      already caught by the positioning branch. It becomes reachable only when
      a FAILED write or rewrite runs between two reads on the same bridge and
      leaves the count at zero. That interleaving is modelled - the count lives
      on :class:`HandlerState`, per bridge, exactly as the copybook declares it
      - so the branch is reproduced rather than assumed unreachable.
    * A10, spelled inline - ``systemMT`` and ``sys4MT`` re-test the CALLER's
      ``FS-Reply`` after the fetch and, if it still holds 10, DISCARD the row
      unread and tag ``"EOF3"`` [common/systemMT.cbl:L924-L928,
      common/sys4MT.cbl:L618-L622]. ``ba010-Initialise`` clears the
      diagnostics but NOT ``FS-Reply`` [common/systemMT.cbl:L541-L547], so a
      caller that left 10 there gets no data and no explanation. Reproduced.

    Args:
        bridge: The bridge's profile.
        file_access: The caller's status block, updated in place.
        dal_common: The shared flags block.
        record: The record to unload into.

    Returns:
        The exit label reached.
    """
    state = handler_state()
    logging_data = file_access.logging_data
    cursor_state = state.cursors.state_for(bridge.table)
    pending: CursorOutcome | None = None

    if cursor_state.cursor_not_active():
        #  `if Cursor-Not-Active` [common/systemMT.cbl:L657]. The positioning
        #  branch, in the frozen statement order.
        logging_data.ws_log_where = _log_where_text(
            _positioning_where_text(bridge)
        )
        logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NO_POSITION
        pending = _read_one_row(bridge)
        logging_data.ws_file_key = _ws_file_key_move(bridge.positioned_tag)
        if bridge.guards_on_incoming_status and _status_is_dirty(file_access):
            #  sys4MT's 28/09/16 guard, before the count test
            #  [common/sys4MT.cbl:L538-L541]. GO TO class 4 - it calls
            #  ba998-Free, which falls into ba999-End.
            _ba998_free(bridge, file_access)
            return BA999_END
        if state.mysql_count_rows.get(bridge.program, 0) == 0:
            #  `if WS-MYSQL-Count-Rows = zero` - an empty table
            #  [common/systemMT.cbl:L702-L718].
            if bridge.captures_sqlstate:
                #  systemMT alone asks for a SQLSTATE here, and moves it
                #  OUTSIDE the errno test [common/systemMT.cbl:L705-L707].
                logging_data.sql_state = _move_into(
                    logging_data.sql_state, pending.sql_state, signed=None
                )
            if _errno_indicates_failure(bridge, _outcome_errno(pending)):
                logging_data.sql_err = _move_into(
                    logging_data.sql_err, _outcome_errno(pending), signed=None
                )
                logging_data.sql_msg = _move_into(
                    logging_data.sql_msg,
                    pending.file_key or "",
                    signed=None,
                )
            (file_access.fs_reply, file_access.we_error) = (
                int(end_of_file_status()[0]),
                end_of_file_status()[1],
            )
            logging_data.ws_file_key = _ws_file_key_move(
                READ_END_TAGS["no_rows"]
            )
            #  GO TO class 4 [common/systemMT.cbl:L717].
            _ba998_free(bridge, file_access)
            return BA999_END
        #  `move 1 to Most-Cursor-Set` [common/systemMT.cbl:L719] - already
        #  done by the delivery stage inside `read_next`.

    #  Both shapes then clear the logged predicate and renumber
    #  [common/systemMT.cbl:L724-L725].
    logging_data.ws_log_where = " " * WS_LOG_WHERE_WIDTH
    logging_data.ws_no_paragraph = BRIDGE_PARAGRAPH_NO_FETCH

    if bridge.occurs_bound is None:
        return _ba040_single_row(
            bridge, file_access, dal_common, record, pending
        )
    return _ba040_occurs_table(
        bridge, file_access, dal_common, record, pending
    )


def _status_is_dirty(file_access: FileAccess) -> bool:
    """``if FS-Reply not = zero or WE-Error not = zero`` - ``sys4MT``'s guard.

    Added 28/09/16 and present at FOUR sites, all in ``sys4MT`` and nowhere
    else [common/sys4MT.cbl:L538-L541, :L593-L596, :L640-L643, :L718-L721].
    DIVERGENCE 8. Because ``ba010-Initialise`` clears the diagnostics but not
    these two fields [common/sys4MT.cbl:L374-L379], the guard reads the
    CALLER's incoming values, so a caller that left a status behind makes
    ``sys4MT`` alone abandon the operation.

    Args:
        file_access: The caller's status block.

    Returns:
        Whether either field is non-zero.
    """
    return (
        file_access.fs_reply != int(FsReply.SUCCESS)
        or file_access.we_error != int(WeError.SUCCESS)
    )


def _outcome_errno(outcome: CursorOutcome) -> str:
    """What ``call "MySQL_errno"`` would report after a positioning stage.

    RECORDED OMISSION, precisely bounded. ``dal/cursor_state.py`` reproduces
    anomaly A11 - a failed statement is reported as end of file - and in doing
    so it collapses two distinguishable situations into one outcome: an EMPTY
    table and a FAILED statement both come back with
    :attr:`CursorOutcome.row` ``None``, ``sql_state`` ``"02000"`` and
    ``file_key`` ``"No Data"``. The driver's own error number is not carried
    across that boundary; it is logged at warning level there instead, so it
    is not lost, only not returned.

    In the frozen bridge the two differ in exactly two fields: ``SQL-Err`` and
    ``SQL-Msg`` [common/systemMT.cbl:L708-L712]. Neither reaches a table -
    both are members of ``Logging-Data`` [copybooks/wsfnctn.cob:L44-L56], which
    ``Ca-Process-Logs`` hands to a log FILE - so the omission has NO DATABASE
    EFFECT and cannot change a state diff, which is the acceptance criterion in
    Agent Action Plan section 0.8.5. Reporting the empty-table value is the
    honest choice of the two, because the alternative is to put a number into
    ``SQL-Err`` that no driver produced.

    Args:
        outcome: What the positioning stage returned.

    Returns:
        The three-character error number, ``"0  "``.
    """
    del outcome  # the distinction is not recoverable - see above
    return ERRNO_NO_ERROR


def _ba040_single_row(
    bridge: BridgeProfile,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    record: Any,
    pending: CursorOutcome | None,
) -> str:
    """``ba040``'s fetch for the two bridges that hold ONE row.

    [common/systemMT.cbl:L727-L937] and [common/sys4MT.cbl:L559-L627]. Both
    tables only ever hold the row whose key is 1, so "the next row" and "the
    row" are the same thing - which is why anomaly NEW-15, the absence of any
    keyed read, is harmless for these two and only these two.

    Args:
        bridge: The bridge's profile.
        file_access: The caller's status block, updated in place.
        dal_common: The shared flags block.
        record: The record to unload into.
        pending: The row the positioning stage already delivered, if this call
            positioned; ``None`` when the cursor was already set.

    Returns:
        The exit label reached, always ``ba999-End`` for these two.
    """
    state = handler_state()
    logging_data = file_access.logging_data
    cursor_state = state.cursors.state_for(bridge.table)
    outcome = pending if pending is not None else _read_one_row(bridge)

    if bridge.guards_on_incoming_status and _status_is_dirty(file_access):
        #  sys4MT's second 28/09/16 guard, AFTER the fetch
        #  [common/sys4MT.cbl:L593-L596]. GO TO class 4.
        _ba998_free(bridge, file_access)
        return BA999_END

    if outcome.row is None:
        #  `if return-code = -1` [common/systemMT.cbl:L903-L909],
        #  [common/sys4MT.cbl:L597-L603].
        (file_access.fs_reply, file_access.we_error) = (
            int(end_of_file_status()[0]),
            end_of_file_status()[1],
        )
        logging_data.ws_file_key = _ws_file_key_move(
            READ_END_TAGS["end_of_table"]
        )
        cursor_state.set_cursor_not_active()
        if bridge.clears_record_on_end_of_data:
            #  DIVERGENCE 18 [common/sys4MT.cbl:L601].
            _initialize_with_filler(record)
        #  GO TO class 3 [common/systemMT.cbl:L908].
        return BA999_END

    if state.mysql_count_rows.get(bridge.program, 0) == 0:
        #  `if WS-MYSQL-Count-Rows = zero` AFTER the fetch - the EOF2 branch
        #  [common/systemMT.cbl:L911-L923], [common/sys4MT.cbl:L605-L616].
        #  ANOMALY NEW-18: reachable only when a failed write or rewrite ran
        #  between two reads on this bridge and left the count at zero, because
        #  nothing else changes it and the positioning stage already caught a
        #  zero. Modelled rather than assumed away.
        if bridge.captures_sqlstate:
            logging_data.sql_state = _move_into(
                logging_data.sql_state, outcome.sql_state, signed=None
            )
        if _errno_indicates_failure(bridge, _outcome_errno(outcome)):
            (file_access.fs_reply, file_access.we_error) = (
                int(end_of_file_status()[0]),
                end_of_file_status()[1],
            )
            _initialize_with_filler(record)
            logging_data.ws_file_key = _ws_file_key_move(
                READ_END_TAGS["driver_failure"]
            )
        cursor_state.set_cursor_not_active()
        return BA999_END

    if file_access.fs_reply == int(FsReply.END_OF_FILE):
        #  ANOMALY A10 spelled inline - `if fs-reply = 10  *> belts and braces`
        #  [common/systemMT.cbl:L925-L929], [common/sys4MT.cbl:L619-L623]. The
        #  row that WAS fetched is discarded unread, the cursor is dropped and
        #  the caller keeps its own 10. `ba010-Initialise` does not clear
        #  `FS-Reply` [common/systemMT.cbl:L541-L547], so this is reachable
        #  from any caller that left an end-of-file status behind.
        cursor_state.set_cursor_not_active()
        logging_data.ws_file_key = _ws_file_key_move(
            READ_END_TAGS["key_out_of_bound"]
        )
        return BA999_END

    _bb100_unload_hvs(bridge, record, outcome.row)
    key_plan = _primary_key_plan(bridge)
    logging_data.ws_file_key = _ws_file_key_move(
        _numeric_move_text(
            int(_as_decimal(outcome.row[key_plan.column])),
            key_plan.integer_digits or REWRITE_KEY_DIGITS,
        )
    )
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    del dal_common  # this shape logs only through ba999-End
    return BA999_END


def _primary_key_plan(bridge: BridgeProfile) -> ColumnPlan:
    """The column plan for the table's single-column primary key.

    Every one of the four tables has exactly one, and no secondary index -
    Agent Action Plan section 0.6.6 establishes that for all twenty-two
    in-scope tables, which makes an ordering-normalised dump deterministic.

    Args:
        bridge: The bridge's profile.

    Returns:
        The plan for the key column.

    Raises:
        KeyError: If the dictionary marks no column as the primary key, which
            would mean the frozen table definition had changed.
    """
    for plan in column_plans_for(bridge.table):
        if plan.ordinal == 1:
            return plan
    raise KeyError(f"{bridge.table} has no column at ordinal 1")


def _ba040_occurs_table(
    bridge: BridgeProfile,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    record: Any,
    pending: CursorOutcome | None,
) -> str:
    """``ba040``'s fetch for the two bridges that hold an ``OCCURS`` table.

    [common/dfltMT.cbl:L528-L590] and [common/finalMT.cbl:L529-L598]. One call
    delivers the WHOLE table: the loop runs to the ``OCCURS`` bound and each
    row is stored into the occurrence ITS OWN KEY COLUMN names, not into the
    occurrence the loop counter is on [common/dfltMT.cbl:L579-L581,
    common/finalMT.cbl:L587]. So a table with rows 1, 5 and 9 populates
    occurrences 1, 5 and 9 and leaves the rest blank, and it stops after three
    iterations rather than nine - the loop counter and the subscript are
    independent.

    ``initialize <record> with filler`` runs FIRST [common/dfltMT.cbl:L530,
    common/finalMT.cbl:L531], so every occurrence the table does not supply
    comes back blank rather than stale.

    Args:
        bridge: The bridge's profile.
        file_access: The caller's status block, updated in place.
        dal_common: The shared flags block.
        record: The record to fill.
        pending: The row the positioning stage already delivered, if this call
            positioned; ``None`` when the cursor was already set.

    Returns:
        The exit label reached, always ``ba999-Exit`` for these two.
    """
    state = handler_state()
    logging_data = file_access.logging_data
    cursor_state = state.cursors.state_for(bridge.table)
    #  `occurs_bound` is set for exactly the two table-shaped bridges and the
    #  caller reaches here only for those, so the bound is read from the public
    #  map whose element type is not optional. That avoids narrowing with an
    #  `assert`, which `python -O` strips. The two agree by construction: 32
    #  [common/dfltMT.cbl:L532] and 26 [common/finalMT.cbl:L532].
    bound = OCCURS_LOOP_BOUNDS[bridge.table]
    key_plan = _primary_key_plan(bridge)
    key_digits = key_plan.integer_digits or REWRITE_KEY_DIGITS

    _initialize_with_filler(record)
    #  `HV-DEF-REC-KEY` keeps whatever the last successful fetch left, which is
    #  what the post-loop `move` then reports [common/dfltMT.cbl:L588].
    hv_key = 0
    carried = pending
    for counter in range(1, bound + 1):
        #  ANOMALY NEW-17: the frozen terminator is
        #  `until A > 32 or return-code not = zero` and the first test inside
        #  the loop adds `or A > 32 or = zero` [common/dfltMT.cbl:L554-L556].
        #  `A` starts at 1 and only increments, so `A = zero` is unreachable,
        #  and `A > 32` is already excluded by the `until`. Both sub-conditions
        #  are preserved as dead rather than deleted.
        outcome = carried if carried is not None else _read_one_row(bridge)
        carried = None
        if outcome.row is None:
            #  `if return-code = -1 or A > 32 or = zero`
            #  [common/dfltMT.cbl:L554-L559], [common/finalMT.cbl:L542-L547].
            (file_access.fs_reply, file_access.we_error) = (
                int(end_of_file_status()[0]),
                end_of_file_status()[1],
            )
            logging_data.ws_file_key = _ws_file_key_move(
                READ_END_TAGS["end_of_table"]
            )
            cursor_state.set_cursor_not_active()
            #  GO TO class 2 - the post-loop work below STILL RUNS, which is
            #  precisely how anomaly NEW-4 erases this status.
            break
        hv_key = int(_as_decimal(outcome.row[key_plan.column]))
        if hv_key == 0 or hv_key > bound:
            #  `if return-code = zero and HV-DEF-REC-KEY = zero or > 32`
            #  [common/dfltMT.cbl:L560-L565], [common/finalMT.cbl:L548-L553].
            #  ANOMALY NEW-16: `WE-Error` receives the OFFENDING KEY and
            #  `FS-Reply` is not touched. ANOMALY NEW-13 for dfltMT: the bound
            #  is 32 while the copybook declares 33 occurrences, so occurrence
            #  33 can never be read.
            logging_data.ws_file_key = _ws_file_key_move(
                READ_END_TAGS["key_out_of_bound"]
            )
            file_access.we_error = hv_key
            cursor_state.set_cursor_not_active()
            break  # GO TO class 2
        if state.mysql_count_rows.get(bridge.program, 0) == 0:
            #  The EOF2 branch [common/dfltMT.cbl:L567-L578],
            #  [common/finalMT.cbl:L555-L566]. ANOMALY NEW-18 again.
            if _errno_indicates_failure(bridge, _outcome_errno(outcome)):
                (file_access.fs_reply, file_access.we_error) = (
                    int(end_of_file_status()[0]),
                    end_of_file_status()[1],
                )
                logging_data.ws_file_key = _ws_file_key_move(
                    READ_END_TAGS["driver_failure"]
                )
            cursor_state.set_cursor_not_active()
            break  # GO TO class 2
        #  The three store-backs [common/dfltMT.cbl:L579-L581] / the one
        #  [common/finalMT.cbl:L587]. The key column is never among them - it
        #  IS the subscript - and the unload helper owns that rule so the two
        #  read paths cannot disagree about it.
        _bb100_unload_hvs(bridge, record, outcome.row, subscript=hv_key)
        logging_data.ws_file_key = _ws_file_key_move(
            _numeric_move_text(hv_key, key_digits)
        )
        if _testing_1(dal_common):
            #  `if Testing-1  *> do for each row` [common/dfltMT.cbl:L584].
            ca_process_logs(file_access, dal_common)

    #  The post-loop block, UNCONDITIONAL - ANOMALY NEW-4
    #  [common/dfltMT.cbl:L587-L590], [common/finalMT.cbl:L595-L598].
    logging_data.ws_file_key = _ws_file_key_move(
        _numeric_move_text(hv_key, key_digits)
    )
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    #  GO TO class 3 - `go to ba999-exit.  *> have written logs if testing`
    return BA999_EXIT


def _log_where_text(text: str) -> str:
    """``move ws-Where (1:J) to WS-Log-Where`` for the positioning branch.

    [common/systemMT.cbl:L680, common/dfltMT.cbl:L490,
    common/finalMT.cbl:L491, common/sys4MT.cbl:L513]. Same one-trailing-space
    slice as :func:`_log_where`, for the same reason.

    Args:
        text: The predicate text.

    Returns:
        Exactly ``WS_LOG_WHERE_WIDTH`` characters.
    """
    return (text + " ")[:WS_LOG_WHERE_WIDTH].ljust(WS_LOG_WHERE_WIDTH)


#  SECTION 7 - THE FOUR BRIDGES, AS THE HANDLER CALLS THEM
#
#  Each of the four is `CALL`ed with THREE parameters and `File-Access` FIRST
#  [common/acas000.cbl:L576-L579], which is a different arity and a different
#  order from the handler's own four-parameter linkage [common/acas000.cbl:
#  L309-L315]. Rule R-5 wants a reviewer to be able to diff argument lists, so
#  both shapes are published as written rather than harmonised.


def _run_bridge(
    bridge: BridgeProfile,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    record: Any,
) -> None:
    """One bridge's whole ``PROCEDURE DIVISION``, for one call.

    Every one of the four has the identical top-level shape - clear the
    diagnostics, evaluate ``File-Function``, transfer to one of six paragraphs,
    and end at ``ba999-End`` or ``ba999-Exit``. The ``evaluate`` is textually
    identical in all four [common/systemMT.cbl:L574-L588,
    common/dfltMT.cbl:L380-L394, common/finalMT.cbl:L376-L390,
    common/sys4MT.cbl:L407-L421]::

        evaluate File-Function
           when  1
                 go to ba020-Process-Open
           when  2
                 go to ba030-Process-Close
           when  3        *> cobol is indexed but here its next
           when  4
                 go to ba040-Process-Read-Next
           when  5
                 go to ba070-Process-Write
           when  7
                 go to ba090-Process-Rewrite
           when  other                          *> 6 is spare / unused
                 go to ba100-Bad-Function
        end-evaluate.

    ⭐ Function code 3 and function code 4 share one arm, and the arm is the
    SEQUENTIAL read. The facade publishes ``System-Read-Indexed`` and no
    read-next verb at all [copybooks/Proc-ACAS-FH-Calls.cob:L190-L230], so the
    only way a caller reaches this arm is by asking for a keyed read - and it
    gets a sequential walk. Anomaly NEW-15, reproduced.

    Every ``go to`` in that ``evaluate`` is class 3 of the Agent Action Plan
    section 0.4.2 taxonomy - a transfer to a named paragraph that runs to its
    own exit - so each becomes a call whose returned label decides whether
    ``ba999-End`` runs.

    Args:
        bridge: The bridge's profile.
        file_access: The shared status block, mutated in place.
        dal_common: The shared flags block.
        record: The record to read into or write from.

    Raises:
        RuntimeError: From the paragraphs that need a connection and find none.
    """
    state = handler_state()
    _ba010_initialise(bridge, file_access)
    function = int(file_access.file_function)

    if function == int(FileFunction.OPEN):
        system = state.system_record
        if system is None and isinstance(record, SystemRecord):
            system = record
        if system is None:
            raise RuntimeError(
                f"{bridge.program}: the six connection parameters are loaded "
                "from the FILE SECTION system record "
                "[common/acas000.cbl:L557-L562], whose relative file is out "
                "of scope; open with File-Key-No 1 or 5 first so the "
                "SystemRecord that carries them reaches this handler. See "
                "anomaly N-fdcreds."
            )
        state.system_record = system
        _ba020_process_open(bridge, system, file_access, dal_common)
        label = BA999_END
    elif function == int(FileFunction.CLOSE):
        _ba030_process_close(bridge, file_access, dal_common)
        label = BA999_END
    elif function in {
        int(FileFunction.READ_NEXT),
        int(FileFunction.READ_INDEXED),
    }:
        label = _ba040_process_read_next(
            bridge, file_access, dal_common, record
        )
    elif function == int(FileFunction.WRITE):
        label = _ba070_process_write(bridge, file_access, dal_common, record)
    elif function == int(FileFunction.RE_WRITE):
        label = _ba090_process_rewrite(bridge, file_access, dal_common, record)
    else:
        #  `when other` - 6 is spare, and 8 delete and 9 start never arrive
        #  because the facade publishes no verb for them.
        _ba100_bad_function(file_access)
        label = BA999_END

    if label == BA999_END:
        _ba999_end(bridge, file_access, dal_common)


def system_mt(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    record: SystemRecord,
) -> None:
    """``call "systemMT" using File-Access ACAS-DAL-Common-data ...``.

    [common/acas000.cbl:L576-L579] for ``File-Key-No`` 1 and, identically,
    [common/acas000.cbl:L596-L599] for ``File-Key-No`` 5 - the same program,
    the same three arguments, in the same order::

        when  1
              call     "systemMT" using File-Access
                                        ACAS-DAL-Common-data
                                        WS-System-Record
              end-call

    Serves ``SYSTEM-REC``, 169 columns, primary key ``SYSTEM-REC-KEY``, from
    the largest bridge in the checkout at 5258 lines. Host-variable group
    ``01 TD-SYSTEM-REC`` [common/systemMT.cbl:L323-L492]; the table declared by
    ``/MYSQL VAR\\ BASE=ACASDB TABLE=SYSTEM-REC,HV /MYSQL-END\\``
    [common/systemMT.scb].

    Its row is ALWAYS row 1: ``bb000-HV-Load`` opens with
    ``move 1 to HV-SYSTEM-REC-KEY`` [common/systemMT.cbl:L1070] and the rewrite
    predicate names the literal ``"1"`` [common/systemMT.cbl:L992]. That is the
    deeper reason dispatch arm 5 cannot reach a different row from arm 1: not
    only is it the same program, it is the same ROW.

    Args:
        file_access: The shared status block, mutated in place.
        dal_common: The shared flags block.
        record: The system record, read into or written from.
    """
    _run_bridge(SYSTEM_MT, file_access, dal_common, record)


def dflt_mt(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    record: SysDefaultRecord,
) -> None:
    """``call "dfltMT" using File-Access ACAS-DAL-Common-data ...``.

    [common/acas000.cbl:L581-L584], whose third argument is
    ``WS-System-Record`` with a trailing ``*> Default-Record`` comment - the
    comment is the ONLY thing that says a different layout is intended.
    Anomaly N9.

    Serves ``SYSDEFLT-REC``, FOUR columns, primary key ``DEF-REC-KEY``. The
    table is the flat image of a 33-entry ``OCCURS`` table in
    [copybooks/wsdflt.cob], one row per occurrence, and its primary key is the
    SUBSCRIPT - a column with no copybook counterpart, materialised by
    ``move A to HV-DEF-REC-KEY`` [common/dfltMT.cbl:L612]. Host-variable group
    [common/dfltMT.cbl:L315-L319].

    STRUCTURAL DIVERGENCE 1: this bridge has NO ``bb000-HV-Load`` and NO
    ``bb100-UnloadHVs`` section. It loads its four host variables with inline
    moves inside ``ba070`` and ``ba090`` and stores fetched values back inline
    inside ``ba040``. Only four bridges in the whole checkout are shaped that
    way - this one, ``finalMT``, ``irsdfltMT`` and ``irsfinalMT`` - and the
    absence is recorded rather than papered over: :func:`_bb000_hv_load` and
    :func:`_bb100_unload_hvs` serve all four bridges here, with the two
    sections' absence noted at each.

    Args:
        file_access: The shared status block, mutated in place.
        dal_common: The shared flags block.
        record: The defaults record, whose 33-entry table this fills or writes.
    """
    _run_bridge(DFLT_MT, file_access, dal_common, record)


def final_mt(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    record: SysFinalRecord,
) -> None:
    """``call "finalMT" using File-Access ACAS-DAL-Common-data ...``.

    [common/acas000.cbl:L586-L589], third argument ``WS-System-Record`` with a
    trailing ``*> Final-Record`` comment. Anomaly N9 again.

    Serves ``SYSFINAL-REC``, TWO columns, primary key
    ``FINAL-ACC-REC-KEY`` - again the ``OCCURS`` subscript materialised, by
    ``move A to HV-FINAL-ACC-REC-KEY`` [common/finalMT.cbl:L613], against a
    26-entry table in [copybooks/wsfinal.cob]. Host-variable group
    [common/finalMT.cbl:L313-L315]. Shares STRUCTURAL DIVERGENCE 1 with
    ``dfltMT``.

    ⭐ Two of this handler's four tables therefore have a primary key that
    exists ONLY in the bridge. That is the clearest local proof of the
    preserved user requirement in Agent Action Plan section 0.8.2: "The
    maintainer's one-way COBOL-to-MySQL bridge defines the authoritative
    record-layout to table mapping - it is the data dictionary for this
    migration." A migration driven from the copybooks alone would have no key
    for either table.

    Args:
        file_access: The shared status block, mutated in place.
        dal_common: The shared flags block.
        record: The final-accounts record, whose 26-entry table this fills.
    """
    _run_bridge(FINAL_MT, file_access, dal_common, record)


def sys4_mt(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    record: SystemRecord4,
) -> None:
    """``call "sys4MT" using File-Access ACAS-DAL-Common-data ...``.

    [common/acas000.cbl:L591-L594], third argument ``WS-System-Record`` with a
    trailing ``*> System-Record-4`` comment. Anomaly N9 once more.

    Serves ``SYSTOT-REC``, 21 columns, primary key
    ``LEDGER-TOTALS-REC-KEY``, from a 1589-line bridge. Host-variable group
    [common/sys4MT.cbl:L314-L335]. Like ``systemMT`` it always acts on row 1:
    ``move 1 to HV-LEDGER-TOTALS-REC-KEY`` [common/sys4MT.cbl:L769] and a
    literal ``"1"`` in the rewrite predicate [common/sys4MT.cbl:L688].

    THE PERIOD-TOTALS TABLE. Agent Action Plan section 0.6.4 records that the
    nine sites that write period totals are the SOLE writers of this record,
    all in the Sales and Purchase programs, which is what makes the
    period-end-totals scenario verifiable by inspecting one table. Every one of
    those writes arrives here.

    DIVERGENCE 8: this bridge alone carries the 28/09/16 status guard, at four
    sites [common/sys4MT.cbl:L538-L541, :L593-L596, :L640-L643, :L718-L721],
    and DIVERGENCE 16: its write and rewrite log themselves and skip
    ``ba999-End``.

    ⭐ ARITHMETIC NOTE, measured on the compiled oracle and reproduced in
    :func:`_bound_parameter`: twenty of this table's twenty-one columns are
    signed ``decimal(10,2)``, yet the edit field the bridge renders them
    through, ``WS-MYSQL-EDIT PIC -Z(18)9.9(9)``, is substringed from position
    18 or 21 onward - and the sign occupies position 1. So a NEGATIVE period
    total is stored as its ABSOLUTE VALUE. Anomaly N-sign. A read returns the
    stored sign faithfully; only the write loses it.

    Args:
        file_access: The shared status block, mutated in place.
        dal_common: The shared flags block.
        record: The period-totals record.
    """
    _run_bridge(SYS4_MT, file_access, dal_common, record)


#  SECTION 8 - THE HANDLER'S OWN PARAGRAPHS
#
#  One function per paragraph of `common/acas000.cbl`, in source order, each
#  carrying its locator and each `GO TO` site annotated with its class from the
#  Agent Action Plan section 0.4.2 taxonomy. Rule R-5: "Every program must map
#  to a module, every paragraph to a function."


def aa999_main_exit(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa999-main-exit`` - log if testing, then fall through.

    [common/acas000.cbl:L492-L495], the whole paragraph::

        aa999-main-exit.
             if       Testing-1
                      perform Ca-Process-Logs
             end-if.

    It has no ``go to``, so it FALLS THROUGH into ``aa-main-exit`` and thence
    into ``aa-Exit`` [common/acas000.cbl:L497-L504]. That fall-through is why
    ``aa030-Process-Close`` can ``perform`` this paragraph and then carry on -
    a ``perform`` of a paragraph runs only that paragraph
    [common/acas000.cbl:L448].

    Args:
        file_access: The shared status block.
        dal_common: The shared flags block.
    """
    if _testing_1(dal_common):
        ca_process_logs(file_access, dal_common)


def aa_main_exit() -> None:
    """``aa-main-exit`` - an empty label.

    [common/acas000.cbl:L497-L500]. It carries only the comment "Now have
    processed cobol flat file ." and falls into ``aa-Exit``. Reproduced as a
    function that does nothing, rather than omitted, because rule R-5 asks for
    a function per paragraph and a reader diffing the two files should find it.
    """


def aa_exit() -> None:
    """``aa-Exit`` - ``exit program``.

    [common/acas000.cbl:L503-L504]. Returning to the caller is what a Python
    function does at its end, so this has no body either; it exists for the
    same traceability reason as :func:`aa_main_exit`.
    """


def aa100_bad_function(file_access: FileAccess) -> None:
    """``aa100-Bad-Function`` - 999 and 99, then fall through.

    [common/acas000.cbl:L485-L490], verbatim::

        aa100-Bad-Function.
        *>
        *> Houston; We have a problem
        *>
             move     999 to WE-Error.                         *> 999
             move     99  to fs-reply.

    ⭐ The handler reports 999 where all four bridges report 990 for the same
    condition [common/systemMT.cbl:L1027-L1029]. 999 is
    ``WeError.NOT_USED`` - the value the shared status module names for "not
    used" - so the handler's bad-function code collides with the code meaning
    no error was set. Recorded, reproduced, not reconciled.

    There is no ``go to``: it falls through into ``aa999-main-exit``, so a bad
    function is still logged.

    Args:
        file_access: The shared status block, mutated in place.
    """
    file_access.we_error = int(WeError.NOT_USED)
    file_access.fs_reply = int(FsReply.ERROR)


def aa020_process_open(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa020-Process-Open`` - open the RELATIVE FILE. Out of scope.

    [common/acas000.cbl:L389-L433]. Sets everything its COBOL sets, in the
    frozen order, and then raises, because the store it opens is not part of
    this migration. See :class:`RelativeFileStoreNotMigratedError` for why
    serving these verbs out of MySQL instead would be a rule R-4 failure.

    The status writes that DO happen first, because a caller can observe them:

    * ``move "OPEN SYSTEM File" to WS-File-Key`` then ``move 201 to
      WS-No-Paragraph`` then ``move zero to FS-Reply WE-Error``
      [common/acas000.cbl:L390-L392];
    * if the file is already open, ``941`` and ``41`` with the log key
      ``"Already OPENed SYSTEM File"`` [common/acas000.cbl:L395-L400] - and
      that path is a clean return, so it does NOT raise; and
    * for ``fn-extend``, ``997`` and ``99`` [common/acas000.cbl:L422-L425] -
      the maintainer's own comment being "Must not be used for ISAM files - IT
      ISNT", with the ``open extend`` line commented out above it. Also a clean
      return.

    So two of the four access types are fully reproducible and both are
    rejections; only ``fn-input``, ``fn-i-o`` and ``fn-output`` need the store.

    Args:
        file_access: The shared status block, mutated in place.
        dal_common: The shared flags block.

    Raises:
        RelativeFileStoreNotMigratedError: For the three access types that
            would actually open the file.
    """
    state = handler_state()
    logging_data = file_access.logging_data
    logging_data.ws_file_key = _ws_file_key_move("OPEN SYSTEM File")
    logging_data.ws_no_paragraph = PARAGRAPH_NO_OPEN
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)

    if state.cobol_file_status == 1:
        logging_data.ws_file_key = _ws_file_key_move(
            "Already OPENed SYSTEM File"
        )
        file_access.we_error = WE_ERROR_FILE_ALREADY_OPEN
        file_access.fs_reply = FS_REPLY_FILE_ALREADY_OPEN
        #  GO TO class 3 - section exit [common/acas000.cbl:L399].
        aa999_main_exit(file_access, dal_common)
        return

    access = int(file_access.access_type)
    if access == int(AccessType.EXTEND):
        #  `move 997 to WE-Error` / `move 99 to fs-reply`
        #  [common/acas000.cbl:L423-L424].
        file_access.we_error = int(WeError.ACCESS_TYPE_WRONG)
        file_access.fs_reply = int(FsReply.ERROR)
        #  GO TO class 3 [common/acas000.cbl:L425].
        aa999_main_exit(file_access, dal_common)
        return

    raise RelativeFileStoreNotMigratedError(
        "aa020-Process-Open would issue "
        f"`open {AccessType(access).name.lower()} System-File` on the "
        "relative file [common/acas000.cbl:L402-L421]. Put \"66\" in "
        "FA-RDBMS-Flat-Statuses to reach the migrated RDBMS path "
        "[common/acas000.cbl:L346-L354]. The relative organisation "
        "is declared at [copybooks/selsys.cob] over the file named "
        "at [copybooks/file00.cob]."
    )


def aa030_process_close(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa030-Process-Close`` - close the relative file, and log TWICE.

    [common/acas000.cbl:L436-L451]. This paragraph is fully reproducible: a
    close of a file that was never opened is a no-op in the frozen source too,
    and the branch that would issue the ``close`` is guarded by the same flag
    this module keeps [common/acas000.cbl:L440-L445]::

             if       Cobol-File-Status = 1
                      close    System-File
                      move     "CLOSE SYSTEM File" to WS-File-Key
             else
                      move     "Already CLOSED: SYSTEM File" to WS-File-Key
             end-if

    ⭐ THE DOUBLE LOG. The tail is not a ``go to`` to the exit; it
    PERFORMS the exit paragraph and then keeps going
    [common/acas000.cbl:L448-L451]::

             perform  aa999-main-exit.
             move     zero to  File-Function
                               Access-Type.              *> close log file
             perform  Ca-Process-Logs.
             go       to aa-main-exit.

    So a close writes one log record with the real function code (if
    ``Testing-1``) and then a SECOND, UNCONDITIONAL record with
    ``File-Function`` and ``Access-Type`` ZEROED in the caller's own block. The
    zeroes are the signal to the logger to close its file, and they are left
    behind for the caller. ``systemMT``'s ``ba999-End`` does exactly the same
    thing at the bridge level [common/systemMT.cbl:L1052-L1057], divergence 6 -
    so a close through the RDBMS path zeroes them too.

    Args:
        file_access: The shared status block, mutated in place.
        dal_common: The shared flags block.
    """
    state = handler_state()
    logging_data = file_access.logging_data
    logging_data.ws_no_paragraph = PARAGRAPH_NO_CLOSE
    logging_data.ws_file_key = " " * WS_FILE_KEY_WIDTH
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    if state.cobol_file_status == 1:
        logging_data.ws_file_key = _ws_file_key_move("CLOSE SYSTEM File")
    else:
        logging_data.ws_file_key = _ws_file_key_move(
            "Already CLOSED: SYSTEM File"
        )
    state.cobol_file_status = 0
    aa999_main_exit(file_access, dal_common)
    #  `move zero to File-Function Access-Type.  *> close log file`
    #  [common/acas000.cbl:L449-L450]. Zero is not a member of either
    #  enumeration - it is the logger's close signal - so the literal is
    #  written, and it is left in the CALLER's block.
    file_access.file_function = 0
    file_access.access_type = 0
    ca_process_logs(file_access, dal_common)
    #  GO TO class 3 [common/acas000.cbl:L451].
    aa_main_exit()


def aa050_process_read_indexed(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa050-Process-Read-Indexed`` - read relative record ``File-Key-No``.

    [common/acas000.cbl:L453-L467]. Its own comment states the contract the
    handler relies on and never checks: "Process according to key number
    (1 thru 4) caller must issue MOVE", and below it "Could put in test for
    file open, and likewise for write & rewrite ?  BUT SHOULD NOT BE NEEDED."

    The statement order is preserved exactly, and it is NOT the same order as
    the write's [common/acas000.cbl:L459-L465]::

             move     204 to WS-No-Paragraph.
             move     File-Key-No to rrn.
             move     spaces to WS-File-Key.
             string   "Read Indexed " File-Key-No into WS-File-Key.
             move     zero to FS-Reply WE-Error.
             read     System-File record into WS-System-Record.

    Note that the status clear comes AFTER the ``string``, whereas
    ``aa070-Process-Write`` clears BEFORE it. Rule R-6 keeps both as written.

    ``rrn`` is ``Rrn pic 9(5) comp`` [copybooks/wsfnctn.cob:L26] - the RELATIVE
    RECORD NUMBER. The key IS the record's position in the file, which is why
    the four record types live in records 1 to 4 of one file and why anomaly N9
    is possible at all.

    Args:
        file_access: The shared status block, mutated in place.
        dal_common: The shared flags block.

    Raises:
        RelativeFileStoreNotMigratedError: Always - the read itself needs the
            store.
    """
    logging_data = file_access.logging_data
    logging_data.ws_no_paragraph = PARAGRAPH_NO_READ_INDEXED
    #  `move File-Key-No to rrn.` [common/acas000.cbl:L461] - `Rrn` is
    #  `pic 9(5) comp` at [copybooks/wsfnctn.cob:L26] and lives in the
    #  CALLER's block, so the relative record number is observable.
    file_access.rrn = int(file_access.logging_data.file_key_no)
    rrn = file_access.rrn
    logging_data.ws_file_key = " " * WS_FILE_KEY_WIDTH
    logging_data.ws_file_key = _string_into_ws_file_key(
        logging_data.ws_file_key,
        "Read Indexed ",
        _numeric_move_text(rrn, FILE_KEY_NO_DIGITS),
    )
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    aa999_main_exit(file_access, dal_common)
    raise RelativeFileStoreNotMigratedError(
        f"aa050-Process-Read-Indexed would issue `read System-File record "
        f"into WS-System-Record` at rrn {rrn} [common/acas000.cbl:L465]. Put "
        '"66" in FA-RDBMS-Flat-Statuses to reach the migrated RDBMS path '
        "[common/acas000.cbl:L346-L354]. The relative organisation "
        "is declared at [copybooks/selsys.cob] over the file named "
        "at [copybooks/file00.cob]."
    )


def aa070_process_write(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa070-Process-Write`` - write relative record ``File-Key-No``.

    [common/acas000.cbl:L468-L476], in its own statement order, which puts the
    ``string`` BEFORE the ``move`` to ``rrn`` - the reverse of the rewrite's::

             move     206   to WS-No-Paragraph.
             move     zeros to FS-Reply  WE-Error.
             move     spaces to WS-File-Key.
             string   "Write " File-Key-No into WS-File-Key.
             move     File-Key-No  to rrn.
             write    System-Record from WS-System-Record.

    ⭐ ``write System-Record from WS-System-Record`` writes the FILE SECTION
    record FROM the linkage buffer. The two are the same layout because
    [copybooks/fdsys.cob] and the linkage both ``copy "wssystem.cob"``,
    which is also why the 901 check in ``ba012`` can never fire.

    Args:
        file_access: The shared status block, mutated in place.
        dal_common: The shared flags block.

    Raises:
        RelativeFileStoreNotMigratedError: Always.
    """
    logging_data = file_access.logging_data
    logging_data.ws_no_paragraph = PARAGRAPH_NO_WRITE
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    logging_data.ws_file_key = " " * WS_FILE_KEY_WIDTH
    logging_data.ws_file_key = _string_into_ws_file_key(
        logging_data.ws_file_key,
        "Write ",
        _numeric_move_text(
            int(file_access.logging_data.file_key_no), FILE_KEY_NO_DIGITS
        ),
    )
    #  `move File-Key-No to rrn.` AFTER the string [common/acas000.cbl:L473]
    file_access.rrn = int(file_access.logging_data.file_key_no)
    rrn = file_access.rrn
    aa999_main_exit(file_access, dal_common)
    raise RelativeFileStoreNotMigratedError(
        f"aa070-Process-Write would issue `write System-Record from "
        f"WS-System-Record` at rrn {rrn} [common/acas000.cbl:L474]. Put "
        '"66" in FA-RDBMS-Flat-Statuses to reach the migrated RDBMS path '
        "[common/acas000.cbl:L346-L354]. The relative organisation "
        "is declared at [copybooks/selsys.cob] over the file named "
        "at [copybooks/file00.cob]."
    )


def aa090_process_rewrite(
    file_access: FileAccess, dal_common: AcasDalCommonData
) -> None:
    """``aa090-Process-Rewrite`` - rewrite relative record ``File-Key-No``.

    [common/acas000.cbl:L477-L484]. Statement order again preserved, and here
    the ``move`` to ``rrn`` comes BEFORE the ``string``::

             move     208 to WS-No-Paragraph.
             move     zeros to FS-Reply  WE-Error.
             move     File-Key-No  to rrn.
             move     spaces to WS-File-Key.
             string   "Rewrite " File-Key-No into WS-File-Key.
             rewrite  System-Record from WS-System-Record.

    The paragraph name is spelled ``aa090-Process-Rewrite`` in its own header
    but the ``evaluate`` that reaches it spells the target
    ``aa090-Process-ReWrite`` with a capital W [common/acas000.cbl:L378]. COBOL
    is case-insensitive so both name the same paragraph; the same capital W
    appears in the facade's ``System-ReWrite`` verb
    [copybooks/Proc-ACAS-FH-Calls.cob:L190-L230], where it is the only
    entity of twenty-one spelled that way. Recorded, not normalised.

    Args:
        file_access: The shared status block, mutated in place.
        dal_common: The shared flags block.

    Raises:
        RelativeFileStoreNotMigratedError: Always.
    """
    logging_data = file_access.logging_data
    logging_data.ws_no_paragraph = PARAGRAPH_NO_REWRITE
    file_access.fs_reply = int(FsReply.SUCCESS)
    file_access.we_error = int(WeError.SUCCESS)
    #  `move File-Key-No to rrn.` BEFORE the string
    #  [common/acas000.cbl:L481] - the reverse of aa070's order.
    file_access.rrn = int(file_access.logging_data.file_key_no)
    rrn = file_access.rrn
    logging_data.ws_file_key = " " * WS_FILE_KEY_WIDTH
    logging_data.ws_file_key = _string_into_ws_file_key(
        logging_data.ws_file_key,
        "Rewrite ",
        _numeric_move_text(rrn, FILE_KEY_NO_DIGITS),
    )
    aa999_main_exit(file_access, dal_common)
    raise RelativeFileStoreNotMigratedError(
        f"aa090-Process-Rewrite would issue `rewrite System-Record from "
        f"WS-System-Record` at rrn {rrn} [common/acas000.cbl:L483]. Put "
        '"66" in FA-RDBMS-Flat-Statuses to reach the migrated RDBMS path '
        "[common/acas000.cbl:L346-L354]. The relative organisation "
        "is declared at [copybooks/selsys.cob] over the file named "
        "at [copybooks/file00.cob]."
    )


def ba_rdbms_exit() -> None:
    """``ba-rdbms-exit`` - an empty label ending the RDBMS section.

    [common/acas000.cbl:L604-L606]. It is the target of the one early transfer
    inside the section, the 901 record-length path
    [common/acas000.cbl:L549], and otherwise falls off the end of the section.
    Reproduced as an empty function for the same traceability reason as
    :func:`aa_main_exit`.
    """


def ba010_test_ws_rec_size(file_access: FileAccess) -> None:
    """``ba010-Test-WS-Rec-Size`` - ONE statement, and it is anomaly N-log.

    [common/acas000.cbl:L515-L521]. The whole paragraph, after its comments::

         move     20 to WS-Log-File-no.        *> for FHlogger

    ⭐ ANOMALY N-log. ``aa010-main`` has already put 10 in that field
    [common/acas000.cbl:L328], and the two paths then diverge:

    * the RDBMS path ``perform ba-Process-RDBMS``
      [common/acas000.cbl:L353], which enters the SECTION at its first
      paragraph and therefore executes this statement, so every log record a
      bridge writes carries 20; while
    * the flat path ``perform ba012-Test-WS-Rec-Size-2``
      [common/acas000.cbl:L358] names the SECOND paragraph, skipping this one
      entirely, so every log record the relative-file paragraphs write carries
      10.

    One handler, two log file numbers, decided by which of two ``PERFORM``
    statements ran. Reproduced exactly, and note the value is 20 - NOT the 25
    that the sibling handler ``acas008`` uses [common/acas008.cbl] and that the
    Agent Action Plan expected here. Source governs.

    The paragraph's comments describe a record-length test that lives in the
    NEXT paragraph, which is why the two are separate labels at all.

    Args:
        file_access: The shared status block, mutated in place.
    """
    file_access.logging_data.ws_log_file_no = LOG_FILE_NO_RDB_PATH


def ba012_test_ws_rec_size_2(
    system: SystemRecord,
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
) -> bool:
    """``ba012-Test-WS-Rec-Size-2`` - the first-call-only credential load.

    [common/acas000.cbl:L523-L563]. Two things happen, both inside one
    ``if A = zero`` guard whose ``end-if`` closes after the sixth move
    [common/acas000.cbl:L563]:

    1. a record-length check that CANNOT FAIL. ``A`` becomes
       ``function Length (WS-System-Record)`` and ``B``
       ``function length (System-Record)`` [common/acas000.cbl:L526-L531], and
       ``if A < B`` sets 901 and 99 [common/acas000.cbl:L532-L535]. But the
       linkage record is ``copy "wssystem.cob"`` renamed
       [common/acas000.cbl:L288-L294] and the FILE SECTION record is
       [copybooks/fdsys.cob], which copies the SAME copybook - so the two
       lengths are equal by construction and ``A < B`` can never hold. The
       whole 901 block, including its two screen displays, its conditional log
       and its ``accept``, is DEAD CODE. Recorded, and the branch is
       reproduced so that a reader can see it is reachable only if the two
       copybooks ever diverge.
    2. the credential load [common/acas000.cbl:L557-L562]::

           move     RDBMS-DB-Name in System-Record  to DB-Schema
           move     RDBMS-User    in System-Record  to DB-UName
           move     RDBMS-Passwd  in System-Record  to DB-UPass
           move     RDBMS-Port    in System-Record  to DB-Port
           move     RDBMS-Host    in System-Record  to DB-Host
           move     RDBMS-Socket  in System-Record  to DB-Socket

    ⭐ ANOMALY N-fdcreds: the source of those six values is ``System-Record``,
    the FILE SECTION record, and the comment above them says so - "Load up the
    DB settings from the system record from COBOL file as its not passed on"
    [common/acas000.cbl:L554]. So on the RDBMS path the handler reads
    credentials from a relative file it has not opened, and gets whatever the
    ``VALUE`` clauses in [copybooks/wssystem.cob:L137-L139] left there. That is
    why :func:`configure_transport` exposes
    ``allow_frozen_placeholder_credentials``: it makes the frozen placeholders
    an explicit, refusable choice rather than a silent connection attempt.

    ⭐ ANOMALY A-1, reproduced by :func:`load_rdb_data_once`: because the
    guard is first-call-only and ``A`` is assigned inside it, a change to
    ``SYSTEM-REC`` row part way through a run cannot affect it.

    THE FLAT PATH PERFORMS THIS PARAGRAPH TOO [common/acas000.cbl:L358], which
    is how the relative-file branch gets its record-length check - and it means
    the credentials are loaded even when no database will be opened.

    Args:
        system: The record the six parameters are taken from.
        file_access: The shared status block, mutated in place.
        dal_common: The shared flags block.

    Returns:
        Whether control transferred to ``ba-rdbms-exit``, which happens only on
        the dead 901 path.
    """
    state = handler_state()
    if state.a != 0:
        #  `if A = zero` is false from the second call onward, so the entire
        #  block - check and load together - is skipped [common/acas000.cbl:
        #  L525, :L563].
        return False
    state.a = SYSTEM_RECORD_DECLARED_LENGTH
    state.b = SYSTEM_RECORD_DECLARED_LENGTH
    if state.a < state.b:  # unreachable - see the docstring
        file_access.we_error = int(WeError.RECORD_SIZE_MISMATCH)
        file_access.fs_reply = int(FsReply.ERROR)
    if file_access.we_error == int(WeError.RECORD_SIZE_MISMATCH):
        #  The two `display ... at` statements and the `accept Accept-Reply at
        #  2433` [common/acas000.cbl:L537-L549] are presentation with no
        #  database effect, so Agent Action Plan section 0.3.4 makes them a log
        #  record and drops the pause.
        _LOG.error(
            "AC902 %s < System-Rec = %s; AC901 - the caller must stop "
            "[common/acas000.cbl:L536-L546]",
            state.a,
            state.b,
        )
        if _testing_1(dal_common):
            ca_process_logs(file_access, dal_common)
        #  GO TO class 3 - section exit [common/acas000.cbl:L549].
        return True
    rdb_data = load_rdb_data_once(system)
    #  The six moves land in `RDB-Data` inside the caller's own block
    #  [copybooks/wsfnctn.cob:L57-L64], so they are copied there and not merely
    #  latched inside `dal/connection.py`.
    file_access.rdb_data.db_schema = _move_into(
        file_access.rdb_data.db_schema, rdb_data.db_schema, signed=None
    )
    file_access.rdb_data.db_uname = _move_into(
        file_access.rdb_data.db_uname, rdb_data.db_uname, signed=None
    )
    file_access.rdb_data.db_upass = _move_into(
        file_access.rdb_data.db_upass, rdb_data.db_upass, signed=None
    )
    file_access.rdb_data.db_port = _move_into(
        file_access.rdb_data.db_port, rdb_data.db_port, signed=None
    )
    file_access.rdb_data.db_host = _move_into(
        file_access.rdb_data.db_host, rdb_data.db_host, signed=None
    )
    file_access.rdb_data.db_socket = _move_into(
        file_access.rdb_data.db_socket, rdb_data.db_socket, signed=None
    )
    return False


def ba015_test_ends(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    record: SystemFileRecord,
) -> None:
    """``ba015-Test-Ends`` - ⭐ THE DISPATCH. FIVE branches, one buffer.

    [common/acas000.cbl:L565-L601]. This is the paragraph the whole module
    exists for, and every one of its three surprising properties is proved by a
    specific line:

    * FIVE arms, not four [common/acas000.cbl:L574-L600]. Arm 5 calls the SAME
      program as arm 1, ``systemMT`` [common/acas000.cbl:L595-L599], added by
      the change the header records verbatim at [common/acas000.cbl:L161]:
      "14/10/25 vbc - 3.3.01 Pre-Support for RRN (File-Key-No) = 5 for Payroll
      if ever used." ANOMALY N7 is that the handler's own error table at
      [common/acas000.cbl:L185] still reads "998* = File-Key-No Out Of Range
      not 1, 2 or 3 or 4." - never updated. The Agent Action Plan's own
      "four-way dispatch by key number to four tables" is superseded by the
      same evidence.
    * THREE arguments to each bridge, with ``File-Access`` FIRST - a different
      arity and order from this handler's own four-parameter linkage. Both are
      published as written; see :func:`system_mt` and :func:`dispatch`.
    * ⭐ ANOMALY N9 - ALL FIVE ARMS PASS THE SAME ``01``-LEVEL ITEM,
      ``WS-System-Record`` [common/acas000.cbl:L578, :L583, :L588, :L593,
      :L598]. Only a trailing comment on three of them names a different
      layout. The three other copybooks are COMMENTED OUT
      [common/acas000.cbl:L299-L301] under the maintainer's own note::

          *> Here are the other three records held as relative, in the system file
          *>   OOPS, not actually used here or by a call.
          *> copy "wsdflt.cob".
          *> copy "wsfinal.cob".
          *> copy "wssys4.cob".

      and the linkage comment states the arrangement outright
      [common/acas000.cbl:L311]: "with images for the other three record types
      as same size". So in the compiled handler the four layouts occupy ONE
      storage area and each bridge REINTERPRETS THOSE BYTES; there is no
      conversion step and no discriminated union. This function accepts four
      distinct record objects because Python has no overlay, and the caller
      chooses which one to pass exactly as the compiled caller chooses what to
      ``MOVE`` into the buffer before the ``CALL``. The four objects are a
      MODELLING DECISION, not a claim about the source, and
      :data:`SystemFileRecord` names them as four readings of one item.

    Two commented-out remarks above the ``evaluate`` record what the maintainer
    wanted instead - a compiler directive to select between the JC, dbpre and
    Prima pre-SQL conversions [common/acas000.cbl:L567-L569] - and the one that
    governs: "NOW SET UP FOR JC pre-sql compiler system."
    [common/acas000.cbl:L571]. This module is the JC reading, as the Agent
    Action Plan's bridge inventory requires.

    ANOMALY N8, THIRD FACE - AN UNMATCHED KEY IS A SILENT NO-OP. The frozen
    ``evaluate`` has no ``when other`` [common/acas000.cbl:L574-L600]. A
    ``File-Key-No`` outside 1 to 5 therefore falls straight through to
    ``ba-rdbms-exit`` [common/acas000.cbl:L604] having called NO bridge and
    having set NO status, so the caller reads back whatever ``FS-Reply`` and
    ``WE-Error`` it passed in. This is reachable ONLY for the five function
    codes the guard in :func:`aa010_main` does not cover - open, close,
    read-next, start and delete [common/acas000.cbl:L333-L341] - because for
    read-indexed, write and re-write the guard already reported 998 / 99 and
    exited.

    Rule R-3 forbids adding a validation the COBOL does not have, and Agent
    Action Plan section 0.6.5 classifies exactly this shape as a "clean
    rejection, no database effect" whose reproduction must be "equally silent;
    adding a warning would be an added behavior". This function therefore
    returns having done nothing, and records the fall-through as a log line -
    which Agent Action Plan section 0.3.4 permits because a diagnostic with no
    database effect "must not alter control flow and must not appear in any
    table dump". An earlier draft raised ``KeyError`` here; that was a
    divergence in disposition, since a COBOL caller continues and a Python
    caller would have aborted, and it was removed.

    Args:
        file_access: The shared status block, mutated in place.
        dal_common: The shared flags block.
        record: The one buffer, in whichever of its four readings the caller
            selected with ``File-Key-No``. Nothing is returned and, because
            the frozen ``evaluate`` rejects nothing, nothing is raised.
    """
    file_key_no = int(file_access.logging_data.file_key_no)
    bridge = BRIDGES_BY_FILE_KEY_NO.get(file_key_no)
    if bridge is None:
        #  GO TO class 3 - the `evaluate` simply ends and control reaches
        #  `ba-rdbms-exit` [common/acas000.cbl:L600, :L604]. No bridge call, no
        #  status write, no counter, no trace - anomaly N8's third face.
        _LOG.error(
            "ba015-Test-Ends: File-Key-No %s matches no arm "
            "[common/acas000.cbl:L574-L600], which has no `when other`, so no "
            "bridge is called and no status is reported; the guard at "
            "[common/acas000.cbl:L333-L341] covers only File-Function 4, 5 "
            "and 7 (anomaly N8)",
            file_key_no,
        )
        return
    #  Each arm is a `call`, class 3 of the taxonomy - it runs to the called
    #  program's own `exit program` and returns here.
    if bridge is SYSTEM_MT:
        system_mt(file_access, dal_common, cast(SystemRecord, record))
    elif bridge is DFLT_MT:
        dflt_mt(file_access, dal_common, cast(SysDefaultRecord, record))
    elif bridge is FINAL_MT:
        final_mt(file_access, dal_common, cast(SysFinalRecord, record))
    else:
        sys4_mt(file_access, dal_common, cast(SystemRecord4, record))


def _credential_record(buffer: SystemFileRecord) -> SystemRecord:
    """The ``SystemRecord`` ``ba012``'s six credential moves read from.

    ANOMALY N-fdcreds, restated as a modelling decision. ``ba012`` names
    ``System-Record`` [common/acas000.cbl:L557-L562], the FILE SECTION record
    from [copybooks/fdsys.cob], whose relative file this migration does not
    open. The only ``SystemRecord`` that reaches the migrated path is the
    linkage buffer, and it IS one exactly when ``File-Key-No`` is 1 or 5
    [common/acas000.cbl:L576-L579, :L596-L599].

    So the buffer supplies the credentials when it can, and otherwise the last
    one this handler saw does - which is faithful, because the compiled
    handler's own guard loads them ONCE for the whole run
    [common/acas000.cbl:L525] and every caller must open with key 1 before it
    can reach keys 2, 3 or 4 through an open connection.

    Args:
        buffer: The one buffer, in the caller's chosen reading.

    Returns:
        The record to take the six parameters from.

    Raises:
        RuntimeError: If neither source is available, naming the omission
            rather than connecting with fabricated credentials.
    """
    state = handler_state()
    if isinstance(buffer, SystemRecord):
        state.system_record = buffer
        return buffer
    if state.system_record is not None:
        return state.system_record
    raise RuntimeError(
        "ba012-Test-WS-Rec-Size-2 takes the six connection parameters from "
        "the FILE SECTION system record [common/acas000.cbl:L557-L562], whose "
        "relative file is out of scope. Call this handler with File-Key-No 1 "
        "or 5 at least once so the SystemRecord that carries them arrives. "
        "See anomaly N-fdcreds."
    )


def ba_process_rdbms(
    file_access: FileAccess,
    dal_common: AcasDalCommonData,
    record: SystemFileRecord,
) -> None:
    """``ba-Process-RDBMS section`` - the whole migrated path, in order.

    [common/acas000.cbl:L508-L606]. A ``PERFORM`` of a SECTION runs every
    paragraph in it until the section ends, so the three paragraphs fall
    through one into the next with no transfer between them:
    ``ba010-Test-WS-Rec-Size`` [common/acas000.cbl:L515], then
    ``ba012-Test-WS-Rec-Size-2`` [:L523], then ``ba015-Test-Ends`` [:L565],
    then ``ba-rdbms-exit`` [:L604]. The fall-through is why the log file number
    is 20 for everything the bridges write - anomaly N-log.

    The section's own header comment states its purpose verbatim: "Here we call
    the relevent RDBMS module for each of the tables which will include
    processing any other joined tables as needed internally."
    [common/acas000.cbl:L510-L513].

    Args:
        file_access: The shared status block, mutated in place.
        dal_common: The shared flags block.
        record: The one buffer, in the caller's chosen reading. Its credentials
            are recovered by :func:`_credential_record`.
    """
    ba010_test_ws_rec_size(file_access)
    if ba012_test_ws_rec_size_2(
        _credential_record(record), file_access, dal_common
    ):
        #  GO TO class 3 - the dead 901 path exits the section
        #  [common/acas000.cbl:L549].
        ba_rdbms_exit()
        return
    ba015_test_ends(file_access, dal_common, record)
    ba_rdbms_exit()


def key_range_guard_applies(file_function: int) -> bool:
    """Whether ``aa010-main``'s key-range guard fires for this function code.

    ⭐ ANOMALY N8, and the narrowness IS the behaviour
    [common/acas000.cbl:L333-L341]::

         evaluate File-Function
                  when  4   *> fn-read-indexed
                  when  5   *> fn-write
                  when  7   *> fn-re-write
                    if     File-Key-No < 1 or > 5     *> Chg 14/10/25 to support PY
                           move 998 to WE-Error       *> file seeks key type out of range        998
                           move 99 to fs-reply
                           go   to aa999-main-exit
                    end-if
         end-evaluate.

    The ``evaluate`` has NO ``when other``, so an out-of-range ``File-Key-No``
    on an open, a close, a read-next, a start or a delete is NOT DIAGNOSED - it
    passes silently and reaches :func:`ba015_test_ends`, whose own ``evaluate``
    also has no ``when other`` and therefore calls no bridge and reports no
    status at all. Widening this test would be a defect FIX and therefore a
    failure under rule R-4.

    It is also the ONLY key-range check that executes anywhere in this chain:
    each of the four bridges carries its own, and all four are commented out
    [common/systemMT.cbl:L549-L566, common/sys4MT.cbl:L382-L390, and the bare
    remark "we will skip this" in the other two].

    Args:
        file_function: The requested function code.

    Returns:
        Whether the guard applies.

        >>> key_range_guard_applies(4), key_range_guard_applies(1)
        (True, False)
    """
    return file_function in KEY_RANGE_GUARDED_FUNCTIONS


def aa010_main(
    system: SystemFileRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``aa010-main`` - the handler's entry paragraph, in the frozen order.

    [common/acas000.cbl:L320-L387]. Six things happen, and the order matters
    because a caller can observe every one of them:

    1. the log identity [common/acas000.cbl:L325-L328]::

           move     0      to WS-Log-System.
           move     10     to WS-Log-File-No.

       0 is ``LogSystem.PARAMS``, whose own comment enumerates the set:
       "0 = Params, 1 = IRS, 2=GL, 3=SL, 4=PL, 5=Stock". The 10 survives only
       on the relative-file path - anomaly N-log, see
       :func:`ba010_test_ws_rec_size`.
    2. the key-range guard - anomaly N8, see
       :func:`key_range_guard_applies`. On violation, ``998`` and ``99`` and a
       class 3 transfer to ``aa999-main-exit``
       [common/acas000.cbl:L336-L338].
    3. the store selector [common/acas000.cbl:L346-L354]::

           if       FA-RDBMS-Flat-Statuses = "66"
                    perform ba-Process-RDBMS
                    go to AA-Main-Exit
           end-if

       whose five comment lines above it are the maintainer explaining N9 -
       that this handler alone must read the selector from ``wsfnctn`` rather
       than from the system record, because "the system-record being
       temporarily over-written by the other record types being read or written
       out". Note the RDBMS path goes to ``aa-main-exit`` and NOT through
       ``aa999-main-exit``, so it is not logged by the handler at all; the
       bridges log themselves.

       ⭐ AND NOTE WHERE THE TRANSFER SITS: it is BEFORE the function
       ``evaluate`` of step 6, so on the RDBMS path the handler's own
       seven-verb ``evaluate`` NEVER RUNS. The bridge's six-arm ``evaluate``
       [common/systemMT.cbl:L557-L575] governs instead, and the two disagree:
       the bridge accepts function code 3 and routes it into
       ``ba040-Process-Read-Next`` alongside code 4, where the handler has no
       arm for 3 at all and would report ``999``. So the SAME request reaches a
       sequential read on one store and a bad-function report on the other.
       Anomaly NEW-15's other half, reproduced.
    4. ``perform ba012-Test-WS-Rec-Size-2`` [common/acas000.cbl:L358] on the
       flat path only - the paragraph, not the section, which is what leaves
       the log file number at 10.
    5. ``move spaces to SQL-Err SQL-Msg SQL-State``
       [common/acas000.cbl:L370] - SPACES, not zeroes, unlike the bridges'
       write paragraphs.
    6. the function ``evaluate`` [common/acas000.cbl:L372-L385], which has NO
       arm for function code 3: a read-next on the relative file falls to
       ``aa100-Bad-Function``. That is consistent with the facade publishing
       exactly seven verbs and no read-next
       [copybooks/Proc-ACAS-FH-Calls.cob:L190-L230].

    A final ``go to aa100-Bad-Function`` follows the ``evaluate``
    [common/acas000.cbl:L387] under the comment "Should never get here but in
    case :(" - unreachable, because the ``evaluate``'s ``when other`` already
    goes there. Preserved as unreachable.

    Args:
        system: THE ONE BUFFER of anomaly N9
            [common/acas000.cbl:L311], in whichever of its four readings
            ``File-Key-No`` selects. Named ``system`` because that is what the
            frozen linkage calls it.
        file_access: The shared status block, mutated in place.
        file_defs: The file-name definitions. Named in this handler's linkage
            [common/acas000.cbl:L314] and referenced NOWHERE in its procedure
            division - its only use is the file-control entry
            ``assign file-0`` [copybooks/selsys.cob], whose value is the
            literal ``"system.dat"`` [copybooks/file00.cob]. Since that store
            is out of scope, the parameter is accepted and unused here.
            RECORDED OMISSION, not an oversight.
        dal_common: The shared flags block.

    Raises:
        RelativeFileStoreNotMigratedError: From the relative-file paragraphs.
            An unmatched ``File-Key-No`` raises NOTHING - see
            :func:`ba015_test_ends` for anomaly N8's third face.
    """
    logging_data = file_access.logging_data
    logging_data.ws_log_system = int(LOG_SYSTEM)
    logging_data.ws_log_file_no = LOG_FILE_NO_FLAT_FILE_PATH

    function = int(file_access.file_function)
    if key_range_guard_applies(function):
        low, high = FILE_KEY_NO_GUARD_RANGE
        if not low <= int(file_access.logging_data.file_key_no) <= high:
            file_access.we_error = int(WeError.FILE_KEY_NO_OUT_OF_RANGE)
            file_access.fs_reply = int(FsReply.ERROR)
            #  GO TO class 3 [common/acas000.cbl:L338].
            aa999_main_exit(file_access, dal_common)
            return

    if _fa_rdbms_flat_statuses_text(file_access) == RDBMS_STORE_SELECTOR:
        #  GO TO class 4 - a sibling call followed by an explicit exit
        #  [common/acas000.cbl:L353-L354].
        ba_process_rdbms(file_access, dal_common, system)
        aa_main_exit()
        return

    ba012_test_ws_rec_size_2(
        _credential_record(system), file_access, dal_common
    )
    logging_data.sql_err = " " * SQL_ERR_WIDTH
    logging_data.sql_msg = " " * SQL_MSG_WIDTH
    logging_data.sql_state = " " * SQL_STATE_WIDTH

    if function == int(FileFunction.OPEN):
        aa020_process_open(file_access, dal_common)
    elif function == int(FileFunction.CLOSE):
        aa030_process_close(file_access, dal_common)
    elif function == int(FileFunction.READ_INDEXED):
        aa050_process_read_indexed(file_access, dal_common)
    elif function == int(FileFunction.WRITE):
        aa070_process_write(file_access, dal_common)
    elif function == int(FileFunction.RE_WRITE):
        aa090_process_rewrite(file_access, dal_common)
    else:
        #  `when other  *> 6 is spare / unused, no delete (8) or start (9)`
        #  [common/acas000.cbl:L383-L384], and the unreachable `go to` below it
        #  [common/acas000.cbl:L387] would land in the same place.
        aa100_bad_function(file_access)
        aa999_main_exit(file_access, dal_common)


#  SECTION 9 - THE HANDLER'S PUBLIC ENTRY POINT


def dispatch(
    system: SystemFileRecord,
    file_access: FileAccess,
    file_defs: FileDefs,
    dal_common: AcasDalCommonData,
) -> None:
    """``call "acas000" using ...`` - FOUR parameters, in the frozen order.

    ⭐ THE ARITY IS FOUR, NOT FIVE, and the reason is one commented-out name.
    The frozen linkage, verbatim [common/acas000.cbl:L309-L315]::

        Procedure Division Using *>      System-Record
                                 WS-System-Record   *> with images for the other three record types as same size
                                 File-Access
                                 File-Defs
                                 ACAS-DAL-Common-data.

    The first name is commented out at L309, so four parameters remain. The
    facade copybook corroborates it with the maintainer's own note
    [copybooks/Proc-ACAS-FH-Calls.cob:L20-L25]::

        acas000.       *> System and dflt, final and system-record-4 NOTE that this FH only has four
        *>                                           parameters (no system-record from FD)
            call     "acas000" using System-Record
                                    File-Access
                                    File-Defs
                                    ACAS-DAL-Common-Data.

    So the transformation rule Agent Action Plan section 0.4.3 states is
    satisfied exactly, argument for argument::

        FROM:  call "acas000" using System-Record File-Access File-Defs
                                   ACAS-DAL-Common-data
        TO:    acas000_system.dispatch(system, file_access, file_defs,
                                       dal_common)

    ⭐ AND THE CALLER OWNS THE KEY. ``acas000.`` is the ONLY dispatch
    paragraph in the 1,449-line facade with no ``move 1 to File-Key-No``;
    every
    other entity's has one, and the IRS convention's is explicit about why -
    ``move 1 to File-Key-No.  *> 1 = Primary as only used.``
    [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L24]. Here the caller must set
    ``File-Access.file_key_no`` itself, to 1, 2, 3, 4 or 5, before calling. The
    frozen source says so twice, in the two paragraphs whose comment reads
    "caller must issue MOVE" [common/acas000.cbl:L468, :L477].

    THE SEVEN VERBS, and no more. The facade publishes ``System-Open``,
    ``System-Open-Input``, ``System-Open-Output``, ``System-Close``,
    ``System-Read-Indexed``, ``System-Write`` and ``System-ReWrite``
    [copybooks/Proc-ACAS-FH-Calls.cob:L190-L230] - note the capital W in the
    last, which no other entity of the twenty-one has - and this handler has no
    ``Process-Read-Next``, no ``Process-Start`` and no ``Process-Delete``
    paragraph to serve any other. :data:`PUBLISHED_VERBS` names the seven and
    the function-code and access-type pair each sets.

    THE FUNCTION IS A COMMAND, NOT A QUERY. The compiled handler communicates
    only by writing into the caller's linkage blocks, so this returns ``None``
    and mutates ``file_access`` - and, on a successful read, ``system`` - in
    place. Every record class this module touches is a mutable dataclass for
    that reason.

    WORKED EXAMPLE, the sequence the compiled chain requires::

        #  the store selector is a GROUP of two `pic 9` items, so 6 goes in
        #  BOTH digits to make the group read "66"
        stats = file_access.fa_rdbms_flat_statuses
        stats.fa_file_system_used = 6
        stats.fa_file_duplicates_in_use = 6
        file_access.logging_data.file_key_no = 1   # caller owns the key
        file_access.file_function = int(FileFunction.OPEN)
        file_access.access_type = int(AccessType.I_O)
        dispatch(system_record, file_access, file_defs, dal_common)
        file_access.file_function = int(FileFunction.READ_INDEXED)
        dispatch(system_record, file_access, file_defs, dal_common)
        # -> the SYSTEM-REC row is now in system_record; fs_reply is 0

    Args:
        system: THE ONE BUFFER of anomaly N9 [common/acas000.cbl:L311]. In the
            compiled handler this is a single ``01``-level item that four
            bridges each REINTERPRET; here it is one of the four record classes
            that name those readings, chosen by the caller to match
            ``File-Key-No``. Passing a reading that does not match the key is
            the Python equivalent of the compiled handler's own hazard, and the
            bridge will read the wrong fields exactly as the compiled one would
            read the wrong bytes.
        file_access: The shared status and function block
            [copybooks/wsfnctn.cob:L23-L64], mutated in place. The caller sets
            ``file_function``, ``access_type``, ``file_key_no`` and
            ``fa_rdbms_flat_statuses`` before the call and reads ``fs_reply``,
            ``we_error`` and the ``logging_data`` members after it.
        file_defs: The file-name definitions [copybooks/wsnames.cob]. Accepted
            because the linkage names it [common/acas000.cbl:L314] and
            unused on the migrated path; see :func:`aa010_main` for the
            full record of that omission.
        dal_common: The shared testing and logging flags
            [copybooks/Test-Data-Flags.cob].

    Raises:
        RelativeFileStoreNotMigratedError: If the caller leaves
            ``fa_rdbms_flat_statuses`` at anything other than ``"66"`` and asks
            for a verb that would touch the relative file
            [common/acas000.cbl:L346-L354].
        RuntimeError: If a database verb is issued with no connection open, or
            if the credentials cannot be recovered - see
            :func:`_credential_record`.
    An unmatched ``File-Key-No`` raises nothing: the frozen ``evaluate`` has
    no ``when other``, so :func:`ba015_test_ends` calls no bridge and writes
    no status at all [common/acas000.cbl:L574-L600]. That is anomaly N8's
    third face, reproduced rather than diagnosed.
    """
    aa010_main(system, file_access, file_defs, dal_common)
