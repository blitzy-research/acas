"""Record layouts for the migrated ACAS batch posting cycle.

This package holds the 27 record modules of the Python 3.12 migration of the
ACAS (Applewood Computers Accounting System) COBOL batch posting cycle: one
module per in-scope COBOL copybook, plus ``work_records.py`` for the three
General Ledger work-record layouts, which are declared as program file
descriptions rather than in any copybook. Every module defines plain
dataclasses that mirror their copybook field for field.

This file itself is a package marker and nothing more. It declares no type, no
function and no constant, and it imports nothing. That restraint is deliberate
and is explained under "Why this file stays empty" below.

THE FOLDER'S MANDATE
--------------------
From the Agent Action Plan, section 0.4.1.3:

    "Every module is a CREATE from its copybook, translating each 05/03 field
    to a dataclass attribute whose descriptor is looked up in the generated
    dictionary. Oddities in the source are preserved, never corrected."

Its binding shape, from section 0.8.1:

    "Plain modules and dataclasses; no ORM entity layer."

And, folder-specific, from rule R-3:

    "The 27 record modules mirror their copybooks field for field with nothing
    added, preserving even the misnamings - the two spare fields keep their
    Sales prefix inside the Purchase group [copybooks/wssys4.cob]."

The COBOL tree is frozen. It is read as the specification for this migration
and is never modified, reformatted, relocated or commented. Nothing in this
package executes, embeds or shells out to a COBOL program; the migrated cycle
runs on a host with no COBOL compiler and no COBOL runtime present (R-1).

THIS IS A LEAF LAYER
--------------------
The per-directory import contract of section 0.4.3 grants ``records/*.py``
exactly two imports and forbids everything else, for a stated reason -
"this keeps the record layer a leaf":

    permitted:  ``acas_posting.cobol.field``      (the FieldDescriptor type)
                ``acas_posting.dictionary.loader``  (the descriptor lookup)

    forbidden:  ``dal`` (any module), ``programs``, ``cli``, ``clock``,
                ``dates``, ``workfiles``, ``cobol.arithmetic``,
                ``cobol.move``, ``cobol.picture``, ``cobol.usage``,
                ``cobol.condition_names``, ``cobol.sortverb``,
                ``dictionary.generate``, the compiled comparison oracle in
                its sibling tree, and - note this one - **any other module of
                this package**. Record modules never import one another; a
                layout that spans two copybooks restates both locally.

That is not bookkeeping. Section 0.4.3 promises that the arithmetic test tier
"imports only ``cobol`` and ``records`` and touches no database, so it runs
anywhere". A single import reaching into ``dal`` would drag a database driver
into that tier and break the promise for every test in it.

THE DESCRIPTOR CONTRACT - LOOKED UP, NEVER TRANSCRIBED
------------------------------------------------------
No module in this package writes a picture clause, a digit count, a scale, a
sign position or a storage class by hand. Each attribute obtains its storage
metadata from the generated data dictionary, which is built from the
maintainer's one-way COBOL-to-MySQL bridge - "it is the data dictionary for
this migration". Section 0.3.3 states the reason:

    "Field metadata is therefore derived, not transcribed, which eliminates an
    entire class of transcription error across several hundred fields."

Two lookups cover every field in the package:

    ``FieldDescriptor.from_dictionary_key(key)``
        For the 20 table-backed modules, covering the 22 in-scope tables
        (``sales_invoice`` and ``purchase_invoice`` each own a header table
        and a lines table), and for the six linkage and working-storage
        modules whose blocks are declared in a copybook but map to no table.

    ``FieldDescriptor.for_working_storage(name=..., source_locator=...)``
        For ``work_records.py`` alone. Its three layouts belong to no copybook
        and to no table, so there is no dictionary entry to cite; the
        ``source_locator`` carries the program locator instead.

Dictionary keys take one of two forms, and never a bare field name:

    ``<TABLE-NAME>.<COLUMN-NAME>``      for column-mapped entries
    ``<COPYBOOK-RECORD>.<FIELD-NAME>``  for copybook-only entries

The table or record name is part of the key precisely so that two similar
layouts can never merge. The clearest case is the pair of IRS posting
records. ``PSIRSPOST-REC`` (10 columns, from ``copybooks/wspost-irs.cob``,
reached through handler ``acas008``) and ``IRSPOSTING-REC`` (13 columns, from
``copybooks/irswspost.cob``, reached through handler ``acasirsub4``) carry
near-identical field names and are different records. The copybook says so
itself [copybooks/wspost-irs.cob:L6-L7]:

    "This is NOT the same as the internal IRS posting file"

Key by field name alone and those two collapse into one, silently.

``acas_posting.dictionary.loader.cite(key)`` returns the compact
three-locator provenance string - copybook field, bridge host variable, MySQL
column - for any key. Record modules surface that primitive; they never
reimplement it. The full mapping is recorded in
``docs/migration/traceability.md`` (R-5).

TYPE DISCIPLINE (R-2)
---------------------
    money and quantity                   -> ``decimal.Decimal``, at the scale
                                            the copybook declares
    ``binary-char``/``-short``/``-long``  -> ``int``
    ``PIC X(n)``                          -> ``str``

There is no ``float`` anywhere in this package, ever - not in computation, not
in storage, not in transport.

That rule is load-bearing rather than stylistic, and one example shows why.
The seven statistics fields at [copybooks/wssl.cob:L46-L52] are declared
``binary-long``, among them ``Sales-Average`` at L49. Because they are binary
integers, their truncation on divide is *integer* truncation - and section
0.6.1 records that this "is exactly what makes the moving-average defect
reproducible". Typing one of them as ``Decimal`` would carry a remainder the
compiled program discards, silently repairing a defect that R-4 requires be
reproduced. The storage class decides the type; a reading of what the field
"means" never does.

WARNING - ANOMALIES ARE REPRODUCED HERE, NEVER FIXED (R-4)
----------------------------------------------------------
Read this before changing any module in this folder. From the preserved user
requirement, section 0.8.2:

    "There is no test suite: compiled COBOL execution is the behavioral
    specification, defects included.
    A defect reproduced is correct; a defect fixed is a failure."

Several modules here look wrong because the frozen source is wrong, and the
migration's entire value is that the Python cycle posts the same figures as
the compiled one. Four temptations in particular are already known, all
verified in the frozen source, and all of them must be left exactly as they
are:

    * ``sl4-spare3`` and ``sl4-spare4`` sit inside the Purchase group yet
      carry the Sales ``sl4-`` prefix [copybooks/wssys4.cob:L29-L30]. Do not
      rename them.
    * ``Ledger-Name`` is 24 characters in the copybook
      [copybooks/wsledger.cob:L27], 32 in the bridge host variable
      [common/nominalMT.cbl:L299] and 32 in the column
      [mysql/ACASDB.sql:L127]. Do not widen the copybook view to agree.
    * The batch record's declared length contradicts the sum of its fields,
      in the maintainer's own words [copybooks/wsbatch.cob:L7-L9]. Do not
      settle it here.
    * ``IRSPOSTING-REC`` has three date-component columns
      [mysql/ACASDB.sql:L278-L280] that appear in no copybook; the bridge
      derives them under a guard [common/irspostingMT.cbl:L982-L987]. Do not
      add them to the copybook-derived record.

There is deliberately no "resolved", "canonical", "effective",
"authoritative", "corrected", "recommended" or "preferred" type, view, value
or picture anywhere in this system, and none may be introduced. Where the
copybook, the bridge host variable and the MySQL column disagree, the
dictionary records all three views side by side plus an unresolved ``drift``
object, and the disagreement stays unsettled. Reproducing a discrepancy is
the requirement; choosing a winner is the failure.

Each reproduction site in these modules carries a comment citing its COBOL
locator, and the register of every such site is
``docs/migration/anomaly-log.md``.

DETERMINISM (R-6)
-----------------
Dataclass field order follows copybook declaration order, so a reader can set
a module beside its copybook and diff the two by eye. No module in this
package performs import-time I/O: nothing reads the generated dictionary at
import, consults a clock, draws an unpredictable value or inspects the
process environment, and execution is strictly sequential with no concurrency
introduced anywhere. Two imports in two processes produce identical state.

Where a semantic question cannot be settled by reading the source, the
compiled program's observed behaviour settles it, and the arbitration is
written down in ``docs/migration/ambiguity-resolutions.md``.

THE 27 MODULES
--------------
Module, its ``01``-level record, and the copybook it is a CREATE from::

    calling_data.py       WS-Calling-Data        copybooks/wscall.cob
    file_access.py        File-Access            copybooks/wsfnctn.cob
    file_defs.py          File-Defs              copybooks/wsnames.cob
    system_record.py      System-Record          copybooks/wssystem.cob
    system_record_4.py    System-Record-4        copybooks/wssys4.cob
    system_dflt.py        Default-Record         copybooks/wsdflt.cob
    system_final.py       Final-Record           copybooks/wsfinal.cob
    gl_batch.py           WS-Batch-Record        copybooks/wsbatch.cob
    gl_ledger.py          WS-Ledger-Record       copybooks/wsledger.cob
    gl_posting.py         WS-Posting-Record      copybooks/wspost.cob
    spl_irs_posting.py    WS-IRS-Posting-Record  copybooks/wspost-irs.cob
    irs_posting.py        Posting-Record         copybooks/irswspost.cob
    irs_nominal.py        NL-Record              copybooks/irswsnl.cob
    irs_dflt.py           Default-Record         copybooks/irswsdflt.cob
    irs_final.py          Final-Record           copybooks/irswsfinal.cob
    irs_system.py         system-record          copybooks/irswssystem.cob
    sales_ledger.py       WS-Sales-Record        copybooks/wssl.cob
    purchase_ledger.py    WS-Purch-Record        copybooks/wspl.cob
    value_analysis.py     WS-Value-Record        copybooks/wsval.cob
    analysis.py           WS-Analysis-Record     copybooks/wsanal.cob
    sales_invoice.py      SInvoice-Header        copybooks/slwsinv.cob
                          SInvoice-Bodies
                          Invoice-Record         copybooks/slwsinv2.cob
    purchase_invoice.py   PInvoice-Header        copybooks/plwspinv.cob
                          Pinvoice-Bodies
                          WS-PInvoice-Record     copybooks/plwspinv2.cob
    otm3.py               WS-OTM3-Record         copybooks/slwsoi3.cob
                          Open-Item-Record-3
    otm5.py               WS-OTM5-Record         copybooks/plwsoi5B.cob
                          Open-Item-Record-5     copybooks/plwsoi5C.cob
    maps03.py             maps03-ws              copybooks/wsmaps03.cob
    test_data_flags.py    ACAS-DAL-Common-data   copybooks/Test-Data-Flags.cob
    work_records.py       pre-trans-record       general/gl070.cbl:L108
                          post-trans-record      general/gl071.cbl:L124
                          sort-trans-record      general/gl071.cbl:L136

``work_records.py`` is the one module with neither a copybook nor a table
behind it. Its layouts carry data between the General Ledger phases through
the two transient work files named at [copybooks/wsnames.cob:L15-L16], both
annotated by the maintainer as belonging to ``gl071``. Nothing about them
reaches the database, so nothing about them appears in a table dump.

WHY THIS FILE STAYS EMPTY
-------------------------
There are no convenience re-exports here, and their absence is a design
decision with three separate reasons:

1. The import contract of section 0.4.3 has a consumer import one symbol out
   of one module, as a single line reading
   ``from acas_posting.records.gl_batch import GlBatchRecord``. A hub here
   would let one import in ``programs/`` pull in all 27 modules at once,
   dissolving the layering the contract exists to hold.
2. Every record module reaches the dictionary loader while its classes are
   being defined. Eagerly importing all 27 would make a bare
   ``import acas_posting.records`` load and parse the whole data dictionary -
   exactly the import-time cost the loader's lazy design avoids, and exactly
   what would break the infrastructure-free arithmetic test tier.
3. ``acas_posting/__init__.py`` sets the house precedent: no eager
   subpackage imports, no import-time I/O, no logging configuration. This
   file matches it.

For the same reason this file declares no shared base class, mixin,
metaclass, protocol, type variable, validator or helper. R-3 forbids adding
anything the copybooks do not declare, and a shared base in the package root
would become a de-facto ORM root - which section 0.8.1 rules out outright.

The path constants ``PACKAGE_ROOT``, ``REPOSITORY_ROOT``,
``DATA_DICTIONARY_DIR``, ``DATA_DICTIONARY_PATH``,
``DATA_DICTIONARY_SCHEMA_PATH`` and ``__version__`` belong to
``acas_posting/__init__.py``. Import them from there; never re-derive them.
"""

# Provenance. The COBOL system, its bridge programs and its schema are the
# maintainer's work and carry his own notice; this package is a migration of
# the posting cycle's behaviour and restates none of it. The rule identifiers
# R-1 through R-6 cited above are the Agent Action Plan's own (section 0.7.2);
# this project carries no separate rules document, so the plan is where their
# full text lives.

# Deliberately empty: this package publishes no aggregate surface. Import each
# record type from its own module, as the layering contract requires.
__all__: list[str] = []
