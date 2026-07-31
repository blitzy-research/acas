"""ACAS batch posting cycle - data-access layer (DAL). Package marker.

WHAT THIS PACKAGE IS
--------------------
This package is the data-access layer of the Python 3.12 migration of the
ACAS (Applewood Computers Accounting System) COBOL batch posting cycle. It is
the only layer of ``acas_posting`` that speaks SQL, and every statement it
issues runs against the FROZEN MySQL/MariaDB schema ``mysql/ACASDB.sql``.

"Frozen" is literal and load-bearing. ``mysql/ACASDB.sql`` is read as
specification and is never modified: it declares 33 tables, adds no
secondary index and carries no schema-altering DDL, and the 22 tables this
cycle reaches are consumed exactly as they stand. This layer therefore
emits only ``SELECT``, ``INSERT``, ``UPDATE`` and ``DELETE``, and never a
single DDL statement, a migration script, or an ORM mapping that could
generate one.

THE FOUR-HOP CHAIN, AND HOW IT COLLAPSES TO TWO
-----------------------------------------------
In the COBOL system a posting program reaches a table through four hops: a
facade paragraph supplied by a shared copybook, a numbered file-handler
program (``common/acas0NN.cbl``, ``common/acasirsubN.cbl``), a generated
one-way COBOL-to-MySQL bridge program (``common/*MT.scb`` translated by the
vendored JC preSQL translator into ``common/*MT.cbl``), and finally the
literal SQL text the bridge issues.

Agent Action Plan section 0.1.2, verbatim:

    "In Python this becomes two layers rather than four: a facade module
    publishing the verb vocabulary, and one module per handler that owns the
    SQL for its table."

WHY THE MODULE BOUNDARY IS THE HANDLER AND NOT THE TABLE
--------------------------------------------------------
Agent Action Plan section 0.3.1, verbatim:

    "One data-access module per handler, not per table. The COBOL call chain
    routes through handlers, and the handlers are not always one-to-one with
    tables — `acas000` dispatches to four different bridges by key number,
    and both `acas016` and `acas026` own a header table plus a lines table.
    Mirroring the handler boundary rather than the table boundary keeps the
    Python module set in exact correspondence with the COBOL programs that
    the traceability document must map, and preserves the dispatch semantics
    rather than flattening them."

INFRASTRUCTURE MODULES (FIVE)
-----------------------------
``__init__.py``
    This marker. Docstring only; see "WHY THIS MARKER HOLDS NO CODE" below.
``status.py``
    The ``FS-Reply`` value set (0, 10, 21, 22, 23, 99), the ``We-Error``
    codes, the function-code and access-type vocabulary, the SQLSTATE
    mapping for duplicates, and the lock-retry backoff ladder. Derived from
    ``copybooks/wsfnctn.cob`` and ``common/acas008.cbl``.
``connection.py``
    Engine and connection handling built from the ``RDB-Data`` block of
    ``copybooks/wsfnctn.cob`` (schema, user, password, host, socket, port);
    per-statement autocommit exactly as the COBOL does, with NO connection
    pooling; and the numeric-converter policy pinned so that every numeric
    column arrives as ``decimal.Decimal`` or ``int`` and never as a float.
``cursor_state.py``
    Emulation of the ISAM ``START`` / ``READ NEXT`` cursor positioning,
    driven by each bridge's declared key table and relation directive in
    ``common/*MT.scb``.
``facade.py``
    The verb vocabulary. It publishes BOTH COBOL calling conventions over a
    single implementation and is the ONLY module in this package permitted
    to know all seventeen handler modules.

HANDLER MODULES (SEVENTEEN)
---------------------------
Each module owns all SQL for its handler's table or tables, and nothing
else owns any of it. Module -> COBOL handler -> bridge(s) -> table(s):

``acas000_system``
    ``common/acas000.cbl`` -> ``systemMT`` / ``dfltMT`` / ``finalMT`` /
    ``sys4MT`` -> ``SYSTEM-REC`` / ``SYSDEFLT-REC`` / ``SYSFINAL-REC`` /
    ``SYSTOT-REC``, selected by ``File-Key-No`` 1..4.
``acas005_gl_nominal``
    ``common/acas005.cbl`` -> ``nominalMT`` -> ``GLLEDGER-REC``.
``acas006_gl_posting``
    ``common/acas006.cbl`` -> ``glpostingMT`` -> ``GLPOSTING-REC``.
``acas007_gl_batch``
    ``common/acas007.cbl`` -> ``glbatchMT`` -> ``GLBATCH-REC``.
``acas008_spl_posting``
    ``common/acas008.cbl`` -> ``slpostingMT`` -> ``PSIRSPOST-REC``.
``acas012_sales``
    ``common/acas012.cbl`` -> ``salesMT`` -> ``SALEDGER-REC``.
``acas013_value``
    ``common/acas013.cbl`` -> ``valueMT`` -> ``VALUEANAL-REC``.
``acas015_analysis``
    ``common/acas015.cbl`` -> ``analMT`` -> ``ANALYSIS-REC``.
``acas016_invoice``
    ``common/acas016.cbl`` -> ``slinvoiceMT`` -> ``SAINVOICE-REC`` plus
    ``SAINV-LINES-REC`` (header table plus lines table).
``acas019_otm3``
    ``common/acas019.cbl`` -> ``otm3MT`` -> ``SAITM3-REC``.
``acas022_purch``
    ``common/acas022.cbl`` -> ``purchMT`` -> ``PULEDGER-REC``.
``acas026_pinvoice``
    ``common/acas026.cbl`` -> ``plinvoiceMT`` -> ``PUINVOICE-REC`` plus
    ``PUINV-LINES-REC`` (header table plus lines table).
``acas029_otm5``
    ``common/acas029.cbl`` -> ``otm5MT`` -> ``PUITM5-REC``.
``acasirsub1_irs_nominal``
    ``common/acasirsub1.cbl`` -> ``irsnominalMT`` -> ``IRSNL-REC``.
``acasirsub3_irs_dflt``
    ``common/acasirsub3.cbl`` -> ``irsdfltMT`` -> ``IRSDFLT-REC``.
``acasirsub4_irs_posting``
    ``common/acasirsub4.cbl`` -> ``irspostingMT`` -> ``IRSPOSTING-REC``.
``acasirsub5_irs_final``
    ``common/acasirsub5.cbl`` -> ``irsfinalMT`` -> ``IRSFINAL-REC``.

SEVENTEEN MODULES COVER TWENTY BRIDGE PAIRS
-------------------------------------------
The arithmetic is stated here so that a reader who counts bridges and
expects twenty modules is not left believing three are missing.

The migration's in-scope bridge set is twenty ``common/*MT.scb`` and
``common/*MT.cbl`` pairs, yet this package holds seventeen handler modules,
because the mapping from handler to bridge is not one-to-one:

* Sixteen handlers own exactly one bridge each (``acas005``, ``acas006``,
  ``acas007``, ``acas008``, ``acas012``, ``acas013``, ``acas015``,
  ``acas016``, ``acas019``, ``acas022``, ``acas026``, ``acas029``,
  ``acasirsub1``, ``acasirsub3``, ``acasirsub4``, ``acasirsub5``).
* ``acas000`` alone fans out to FOUR bridges. Its ``evaluate File-Key-No``
  block dispatches key 1 to ``systemMT``, key 2 to ``dfltMT``, key 3 to
  ``finalMT`` and key 4 to ``sys4MT``
  [``common/acas000.cbl``:L574-L599]. The same block carries a fifth arm,
  ``when 5``, commented "support for PY may be", which also calls
  ``systemMT``; only keys 1..4 are in scope for the posting cycle.

16 + 4 = 20 bridge pairs, reached through 16 + 1 = 17 handler modules.

Separately, and for the same reason of mirroring COBOL rather than tables,
two of those seventeen modules own two tables each - ``acas016_invoice``
and ``acas026_pinvoice``, each carrying a header table plus a lines table -
so the module count matches neither the bridge count nor the table count,
and is not meant to. It matches the HANDLER count, which is what the
traceability document maps.

WHY THERE IS NO ``acasirsub2`` MODULE
-------------------------------------
The IRS handler series runs ``acasirsub1``, ``acasirsub3``, ``acasirsub4``,
``acasirsub5`` - there is no ``acasirsub2`` and none is missing. The
maintainer records the reason in the header comment of the IRS calling
convention, verbatim [``copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob``:L12-L13,
the note itself on L13]:

    "Note irsub2 is replaced by acas000 with File-Key-No=1"

That is: the IRS system-parameter access that ``irsub2`` used to provide is
served by ``acas000`` with the primary key number, so it is already covered
by ``acas000_system`` above. Consistent with the note, the copybook's own
``acas000`` paragraph moves 1 to ``File-Key-No`` before its ``CALL``, and no
``irsub2`` or ``acasirsub2`` name appears anywhere in the copybook.

THE TWO PUBLISHED VOCABULARIES
------------------------------
The COBOL codebase names the same twelve-verb idea twice, and ``facade.py``
publishes both name sets over one implementation so that a reader following
either convention finds a correspondingly named Python function without the
logic existing twice:

* ENTITY-named, in ``copybooks/Proc-ACAS-FH-Calls.cob`` (1449 lines, 256
  paragraphs in section ``zz080-ACAS-Processes``). It defines 21 entity
  facades - Analysis, DelFolio, DelInvNos, Delivery, GL-Batch, GL-Nominal,
  GL-Posting, Invoice, OTM3, OTM5, PInvoice, PLautogen, Payments, Purch,
  SLautogen, SPL-Posting, Sales, Stock, Stock-Audit, System, Value - each
  exposing the same verb set: ``-Open``, ``-Open-Input``, ``-Open-Output``,
  ``-Open-Extend``, ``-Close``, ``-Start``, ``-Read-Next``,
  ``-Read-Indexed``, ``-Write``, ``-Rewrite``, ``-Delete``,
  ``-Delete-All``. A facade paragraph sets the access type and the function
  code and then performs the handler dispatch
  [``copybooks/Proc-ACAS-FH-Calls.cob``:L465-L469]; the dispatch paragraph
  sets the key number and issues the ``CALL``
  [``copybooks/Proc-ACAS-FH-Calls.cob``:L51-L57]. The Invoice entity
  additionally publishes ``-Read-Next-Header`` and the sorted-read variants
  by name, by batch and by customer, which ``acas016_invoice`` implements.
* HANDLER-named, in ``copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob`` (367 lines,
  55 paragraphs in section ``zz100-ACAS-IRS-Calls``), which names its
  facade paragraphs after the handler rather than the entity -
  ``acas008-Read-Next`` where the entity convention says
  ``SPL-Posting-Read-Next``.

The two conventions differ BEHAVIOURALLY, not merely in naming, and
``facade.py`` must honour the difference rather than alias it away. The
handler-named convention wraps its open calls in a per-handler error check -
``acas000-Check-4-Errors``, ``acas008-Check-4-Errors``,
``irsub1-Check-4-Errors``, ``irsub3-Check-4-Errors``,
``irsub5-Check-4-Errors``
[``copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob``:L320-L353] - each of which, on
a non-zero ``FS-Reply``, displays a handler-specific message identifier
(IR911, IR916, IR912, IR913, IR915 respectively), closes the file and
transfers to ``Open-Error-Continued``, which reports the status and then
returns from the program outright with ``goback``
[``copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob``:L355-L364]. The entity-named
convention has no such paragraph at all - ``Proc-ACAS-FH-Calls.cob``
contains zero ``Check-4-Errors`` paragraphs - and its callers test the reply
inline instead. An unrecoverable open failure therefore aborts the program
under one convention and returns to the caller under the other.

THE LAYERING CONTRACT
---------------------
The dependency graph of this package is acyclic and the direction is fixed.
Stated so that it can be acted on and reviewed:

* ``dal/acas*.py`` MAY import ``dal.connection``, ``dal.status``,
  ``dal.cursor_state``, the ``acas_posting.records`` module or modules for
  the record layouts it owns, and ``acas_posting.dictionary.loader``.
* ``dal/acas*.py`` MUST NOT import ``acas_posting.programs``,
  ``acas_posting.cli``, another ``dal.acas*`` module, or ``harness``.
* ``programs/*.py`` reaches this layer ONLY through ``dal.facade``, never
  through a ``dal.acas*`` module directly.
* ``facade.py`` is the only module permitted to know all seventeen
  handlers, which is precisely why importing anything into this marker
  would be a cycle: ``facade`` imports the handler modules, and the handler
  modules live in this package.

One division of responsibility is worth restating here because it is the
reason this package exists at all. The bridge is not a transparent pipe:
for several fields the copybook declaration, the bridge host variable and
the MySQL column disagree on signedness or width, and the value changes
BEFORE any SQL executes - a signed ``binary-long`` narrowed to an unsigned
host variable and an unsigned column loses its sign at the bridge, not at
the database. Applying those conversions is the job of THIS layer, module
by module and field by field from the generated data dictionary. The
``acas_posting.records`` dataclasses mirror their copybooks field for field
and deliberately do not apply them.

WHY THIS MARKER HOLDS NO CODE
-----------------------------
This module is a docstring and nothing else - no import statement, no
export list, no version constant, no other constant, no function and no
class. That is a deliberate design decision with four independent
justifications, not an omission:

1. A re-export here would be a cycle. ``facade.py`` imports all seventeen
   handler modules, and every one of them lives in this package, so a
   star-import of ``facade`` in this file would make importing the package
   depend on importing a module that depends on the package.
2. A re-export here would break the layering contract above by handing
   ``programs/*.py`` a route into ``dal.acas*`` that the contract forbids.
3. Importing ``acas_posting.dal`` must be free of side effects. The
   migration's determinism guarantee - that two runs of a scenario under
   the same pinned clock produce byte-identical table dumps - rests on
   there being no hidden clock read, no entropy source and no ordering
   nondeterminism anywhere in the package. So this module opens no
   connection, reads no environment variable, configures no logging, sets
   no ``decimal`` context and performs no file or database I/O. Connection
   handling belongs to ``connection.py`` and the numeric-converter policy
   belongs there with it.
4. The version constant belongs to the parent package ``acas_posting``. A
   second one declared here could only drift from it.

BINDING RULES OBSERVED BY THIS FILE
-----------------------------------
The Agent Action Plan records that no separate user rules document exists
for this project; its six numbered rules are the binding ones. Those that
bear on this file:

R-1, no COBOL at runtime
    The COBOL is specification, not a runtime dependency, and the shipped
    artifact must run on a host with no COBOL compiler and no COBOL runtime
    present. This file names COBOL programs only in prose, as citations into
    the frozen source. It launches no external process, executes no
    operating-system command, loads no foreign library, binds to no C
    interface object, and never reaches the compiled comparison oracle: that
    oracle lives under ``harness``, a SIBLING tree of ``acas_posting``
    rather than a sub-package, so no import path runs from the shipped
    package to it.
R-3, no new validations, fields or schema changes, and no concurrency
    Nothing here validates, declares a field, or emits DDL. Execution across
    the package is strictly sequential, matching the single-threaded COBOL:
    no thread, no event loop, no worker process, no connection pool, no ORM
    entity layer and no schema-migration tooling.
R-5, full traceability
    Satisfied by this docstring in prose. Every program maps to a module,
    every paragraph to a function and every field to a data-dictionary
    entry; a reader arriving at ``acas_posting/dal/`` learns the
    handler-to-bridge-to-table mapping, both calling conventions and the
    layering contract from here, without opening another file. The
    authoritative record-layout-to-table mapping is the maintainer's
    one-way COBOL-to-MySQL bridge - ``common/*MT.scb`` with its generated
    ``common/*MT.cbl`` - and not the copybooks, which is why the module
    inventory above cites the bridge for every table.
R-6, compiled behaviour is the tie-breaker
    Where a semantic question is ambiguous, the observed behaviour of the
    compiled program decides it, and this layer reproduces what the
    handler and bridge pair actually does rather than what a reading of the
    copybook suggests it should. Determinism is a requirement of that
    arbitration, which is why import-time silence is enforced above rather
    than merely preferred.

FROZEN PATHS THIS PACKAGE READS AS SPECIFICATION AND NEVER MODIFIES
-------------------------------------------------------------------
``common/*.cbl``, ``common/*.scb``, ``copybooks/*.cob``, ``general/*.cbl``,
``sales/*.cbl``, ``purchase/*.cbl``, ``irs/*.cbl``, ``stock/*.cbl`` and
``mysql/ACASDB.sql``. Any diff touching those paths is a defect in the
migration, regardless of how harmless it appears.
"""
