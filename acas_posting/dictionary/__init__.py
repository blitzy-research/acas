"""The machine-readable data dictionary: model, generator and runtime loader.

The dictionary is the field-level authority for this migration. Every entry is
built from an authoritative triple - the copybook field declaration, the bridge
host-variable declaration, and the `CREATE TABLE` column definition - so that
field metadata is derived rather than transcribed by eye (rule R-5).

Modules
    model       the entry schema: the copybook/host-variable/column triple,
                the drift and presence descriptions, and the derivation notes
                for columns that exist only in the bridge
    generate    parses copybooks/*.cob, common/*MT.scb, common/*MT.cbl and
                mysql/ACASDB.sql and emits the JSON artifact, flagging any
                field present in one source and absent from another
    loader      runtime access, so any record field can cite its entry

The artifact and its JSON Schema live in the sibling `data_dictionary/` tree,
which is excluded from packaging; their paths are published by
`acas_posting.__init__`.

Why the bridge and not the copybooks. The user's requirement, preserved in
Agent Action Plan section 0.8.2, designates the maintainer's one-way
COBOL-to-MySQL bridge as the authoritative record-layout to table mapping.
`IRSPOSTING-REC` shows why that is not a stylistic choice: `POST4-DAY`,
`POST4-MONTH` and `POST4-YEAR` appear in no copybook and exist only because
the bridge derives them from a date string under a guarded substring rule
[common/irspostingMT.cbl:L982-L987]. When the guard fails the three components
stay zero while the raw date text is still stored, so the row is internally
inconsistent - and both the derivation and its failure mode are recorded as
dictionary facts rather than discovered later.

Drift is recorded, never reconciled. A field may be signed in the copybook and
unsigned in both the host variable and the column [common/salesMT.cbl:L305-L312],
or 24 characters wide in the copybook and 32 in the host variable and the
column [common/nominalMT.cbl:L299]. The dictionary states all three
declarations so the data-access layer can reproduce the bridge's conversion,
which happens before any SQL executes.

Every bridge load paragraph initialises its host-variable group first, so an
unset field reaches SQL as zero or space rather than `NULL`. That is why every
column in the frozen schema can be declared `NOT NULL`, and why the Python
layer defaults rather than omits.

The frozen sources are read as specification and never modified. The COBOL
carries the maintainer's own notice, which is his to make and not this
migration's to restate.

THE AUTHORITATIVE SOURCE IS THE BRIDGE, NOT THE COPYBOOK
========================================================
This is the fact that justifies the whole package, and it is the user's own
requirement, preserved verbatim in Agent Action Plan section 0.8.2 and
byte-identical to the `meta.authority` string inside the generated artifact:

    "The maintainer's one-way COBOL-to-MySQL bridge defines the authoritative
    record-layout ↔ table mapping - it is the data dictionary for this
    migration."

The copybooks are the obvious place to look for field metadata, and they are
not sufficient - which this codebase proves rather than merely asserts. The
internal IRS posting table carries three columns, POST4-DAY, POST4-MONTH and
POST4-YEAR, that have NO counterpart in any copybook whatsoever:

  * copybooks/irswspost.cob declares the posting record with ten fields and
    none of the three is among them; the names appear nowhere in copybooks/.
  * They are declared only in the bridge - as HV-POST4-DAY, HV-POST4-MONTH
    and HV-POST4-YEAR, each `PIC 9(03) COMP`, inside the host-variable group
    TD-IRSPOSTING-REC [common/irspostingMT.cbl:L177-L179].
  * They exist because the bridge DERIVES them, under a guard, from
    two-character slices of a date string it has already stored whole
    [common/irspostingMT.cbl:L982-L987]. When a guard does not hold the move
    is simply not made, so the component keeps the zero left by the group
    INITIALIZE while the raw date text is written anyway - a row that is
    internally inconsistent.
  * The bridge never moves them back into the record after a read, because
    the record has nowhere to put them.
  * In the frozen schema they are `tinyint(2) unsigned NOT NULL` at ordinals
    4, 5 and 6 of IRSPOSTING-REC - INTERLEAVED between POST4-DAT and
    POST4-DR, not appended after the copybook's own columns, so even a
    positional reading of that table would misalign without them.

Agent Action Plan section 0.1.1 draws the conclusion: "A migration driven from
the copybooks alone would silently omit three columns of a posting table."

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!  READ THIS BEFORE YOU OPEN model.py  (rule R-4)                         !!
!!                                                                         !!
!!  THE THREE VIEWS ARE KEPT SEPARATE ON PURPOSE. DO NOT RESOLVE THEM.     !!
!!                                                                         !!
!!  A DEFECT REPRODUCED IS CORRECT; A DEFECT FIXED IS A FAILURE.           !!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

That last line is the user's own requirement, which Agent Action Plan section
0.8.2 preserves verbatim - reproduced here in full, outside the banner, so it
can be cited exactly rather than read through a gutter:

    "There is no test suite: compiled COBOL execution is the behavioral
    specification, defects included. A defect reproduced is correct; a defect
    fixed is a failure."

An entry therefore records the copybook field, the bridge host variable and
the column as THREE INDEPENDENT VIEWS, plus the drift between them, and it
stops there. It does not adjudicate.

The temptation this warning exists to stop is a single "resolved" or
"effective" type on an entry. Adding one would be a defect and not an
improvement, because the disagreements between the three views are
LOAD-BEARING BEHAVIOUR:

  * a statistics field declared signed in the copybook becomes an unsigned
    host variable and an unsigned column, so the sign is lost AT THE BRIDGE,
    before any SQL runs;
  * a ledger name declared 24 characters wide becomes a 32-character host
    variable and a 32-character column, so the padding a table dump shows is
    not the copybook's padding;
  * the three columns described above have no copybook view at all.

Collapse the three views into one and every one of those facts becomes
unrecoverable. Record the disagreement; never repair it. The register of the
twenty-two anomalies this migration reproduces is
docs/migration/anomaly-log.md.

DATA DICTIONARY FIRST - WHY THIS PACKAGE DEPENDS ON NOTHING
===========================================================
Agent Action Plan section 0.8.1 makes the ordering a directive rather than a
preference, verbatim:

    "Data dictionary first. The dictionary is generated from the bridge
    before record definitions are written, and every Python field definition
    cites its entry. This ordering is a directive, not a preference - it is
    what prevents fields being transcribed by eye."

So this package is FIRST in the layering order of the whole migration, and its
position is expressed in code as an absence: it imports no sibling. Agent
Action Plan section 0.4.3 fixes the shape - `cobol/*.py` may import
`dictionary.loader` and nothing else, and `records/*.py` may import
`cobol.field` and `dictionary.loader` and nothing else, "this keeps the record
layer a leaf". Nothing under this package may reach `cobol`, `records`, `dal`,
`programs`, `cli`, `clock`, `dates`, `workfiles` or the compiled comparison
oracle's sibling tree. Each of those either sits above this layer or is
outside the shipped package altogether, and importing one here would
manufacture the very cycle that layering forbids.

This marker in particular imports nothing at all, and that is a substantive
choice rather than a tidy one. It does NOT re-export its three modules,
because `generate.py` is a build-time tool that parses the frozen COBOL tree
and the frozen schema. Were this marker to bind it eagerly, every consumer of
`loader.py` - `cobol/field.py` and all twenty-seven record modules - would pay
for that parser on import, and Agent Action Plan section 0.4.3's promise that
the arithmetic test tier "imports only `cobol` and `records` and touches no
database, so it runs anywhere" would be false on a bare host. Import the
module you want, by name.

ENTRY KEYS AND FIELD-LEVEL TRACEABILITY  (rule R-5)
===================================================
Rule R-5 requires that every field map to a data-dictionary entry and that the
mapping be recorded rather than left implicit in the code. `generate.py`
mechanises that mapping and `loader.py` lets a record field cite its entry at
run time, so field metadata is DERIVED rather than transcribed - which is what
removes an entire class of transcription error across several hundred fields.

An entry is addressed by a single key, and there are two forms:

    <TABLE-NAME>.<COLUMN-NAME>      where a column backs the field, for
                                    example IRSPOSTING-REC.POST4-DAY
    <COPYBOOK-RECORD>.<FIELD-NAME>  where the field is copybook-only, for
                                    example WS-Analysis-Record.Pa-System

Both halves of a key are the names the frozen sources use themselves,
unaltered and un-normalised: hyphens are not turned into underscores and case
is not folded, so a key can be searched for in the COBOL and in the schema
exactly as it stands. The artifact's root members are `meta`, `sources`,
`tables`, `entries` and `coverage`.

The wider mapping - program to module, paragraph to function, field to
dictionary entry - is recorded in docs/migration/traceability.md.

WHERE THE ARTIFACT LIVES
========================
The dictionary's SOURCE OF TRUTH is a top-level repository SIBLING of
`acas_posting`: Agent Action Plan sections 0.3.1 and 0.4.1.6 place
data_dictionary/ beside the package rather than inside it, and nothing here
relocates it. That is the file the generator writes and its `--check` mode
compares against.

It is nonetheless SHIPPED, and it has to be: every record module builds its
field descriptors from the dictionary during a normal import, so a distribution
that could not reach it would fail on `import acas_posting.records.gl_posting`
rather than merely lack a convenience. pyproject.toml carries a copy into the
built distribution through a `package-dir` mapping that makes the repository's
data_dictionary/ tree the acas_posting package's data directory, so a wheel
holds the two JSON files at acas_posting/data_dictionary/ while the source of
truth stays exactly where the plan puts it. tests/, docs/ and the compiled
oracle's own tree remain unshipped, and no COBOL source, copybook or schema
file enters a distribution in any form.

Nothing here re-derives either location. The path constants PACKAGE_ROOT,
REPOSITORY_ROOT, DATA_DICTIONARY_DIR and its explicit spelling
REPOSITORY_DATA_DICTIONARY_DIR, PACKAGE_DATA_DICTIONARY_DIR and its explicit
spelling PACKAGED_DATA_DICTIONARY_DIR with the two artifacts inside it,
DATA_DICTIONARY_PATH, DATA_DICTIONARY_SCHEMA_PATH and the ordered
DATA_DICTIONARY_SEARCH_PATH belong to the parent package and are exported by
it; `loader.py` walks that order, prefers the packaged copy, and owns the case
where neither is there. A second walk up the tree here would be a second
source of truth for one fact.

DETERMINISM OF THE GENERATED ARTIFACT  (rule R-6)
=================================================
The dictionary is committed, so regenerating it must reproduce it BYTE FOR
BYTE. Otherwise a difference in the file could not be read as a change in what
it records, and the artifact would stop being evidence about the frozen
sources and become noise about the machine that last wrote it. `generate.py`
therefore emits UTF-8 with no byte-order mark, LF line endings, two-space
indentation and exactly one trailing newline, and it orders every member and
every array from the data rather than from the order in which a directory
happened to be walked.

Four classes of content are forbidden in the artifact outright, because each
would differ between two otherwise identical regenerations:

  * timestamps and dates of generation - a date quoted from a comment in a
    frozen source is evidence about that source and is kept verbatim, but a
    date describing when the artifact itself was produced appears nowhere;
  * hostnames and user names;
  * absolute filesystem paths - every locator is a repository-relative path
    followed by a line reference;
  * revision identifiers, branch names and working-copy state of the
    version-control checkout.

Credential values are excluded on the same principle: the connection block is
catalogued as field layouts only, and no schema name, user, password, host,
socket or port value is recorded anywhere.

This marker holds to the same discipline. Importing it consults no clock, no
entropy source, no process environment and no installed distribution
metadata, so two imports in two processes produce identical state.

NO COBOL AT RUNTIME  (rule R-1)
===============================
COBOL is the specification for this migration, not a runtime dependency of
the result: the shipped artifact must run on a host with no COBOL compiler and
no COBOL runtime present. `generate.py` reads the frozen bridge, the frozen
copybooks and the frozen schema as TEXT and nothing more - it parses source
files, it does not build or run them. No module here launches a child process,
loads a foreign library through a foreign-function interface, looks for a
compiler on the path, or reaches the compiled comparison oracle's sibling
tree; there is no import path from this package to it.

Nor does this package add a dependency. The pinned set is
mysql-connector-python, SQLAlchemy used at Core level only, PyYAML, pytest and
pytest-cov, and a JSON Schema validator is deliberately not among them - which
is the second reason the schema check lives in a test rather than in a module
here.

NUMERIC POLICY  (rule R-2)
==========================
No accounting value may pass through a binary floating-point type at any
point - not in computation, not in storage, not in transport. This package
computes no accounting value at all: it records what a field IS, so that
`cobol/field.py` can build a descriptor of it - places, scale, signedness,
usage and sign position - and `cobol/arithmetic.py` can store through that
descriptor in `decimal`, truncating toward zero exactly as an un-ROUNDED COBOL
store does. What is recorded here is picture text, place counts, scales and
SQL type names: integers and strings throughout, never a binary approximation
of a decimal.

NO NEW VALIDATION, NO CONCURRENCY  (rule R-3)
=============================================
Agent Action Plan section 0.7.4 resolves the apparent tension for this
package, verbatim: "R-3 constrains the database, not the repository.
Describing a schema in a committed artifact is orthogonal to altering it." So
this package describes the frozen schema exhaustively and emits no data
definition statement of any kind - no table, column, index, constraint, view
or trigger is added, altered or dropped from here, and no schema-migration
tool is in the dependency set.

It adds no validation either. `generate.py` FLAGS a field present in one
source and absent from another; it does not reject it, repair it or decline to
emit it, because a one-sided entry is the finding and is recorded as such. And
importing this marker validates nothing: it opens no file, reads no data, does
not ask the filesystem whether the artifact is there, configures no logging,
and cannot fail for an environmental reason. A package marker able to fail
because of its surroundings would be a new validation this migration is not
permitted to add, and it would take every module beneath it down with it.

Execution is strictly sequential, matching the single-threaded COBOL: no
thread, no event loop, no process pool, no connection pool, and no
synchronisation primitive anywhere in this package.

THE FREEZE
==========
Nothing in this package may cause a diff to common/, copybooks/, general/,
sales/, purchase/, irs/, stock/ or mysql/ACASDB.sql. Those trees are the
specification: read exhaustively, and never modified, reformatted, commented,
relocated or built from here. `generate.py` reads them and writes only into
data_dictionary/. Agent Action Plan section 0.8.1, verbatim: "Any diff
touching `common/*.cbl`, `common/*.scb`, `copybooks/*.cob`, `general/*.cbl`,
`sales/*.cbl`, `purchase/*.cbl`, `irs/*.cbl` or `mysql/ACASDB.sql` is a defect
in the migration, regardless of how harmless it appears."

FURTHER READING
===============
    docs/migration/traceability.md           program-to-module,
                                             paragraph-to-function and
                                             field-to-dictionary-entry
                                             mappings
    docs/migration/anomaly-log.md            the register of legacy defects
                                             this migration reproduces
    docs/migration/ambiguity-resolutions.md  each semantic question and the
                                             compiled-behaviour arbitration
                                             that settled it
    README-python-migration.md               how to build the comparison
                                             oracle, seed it, run both cycles
                                             and diff the resulting table
                                             state
"""

# Provenance. Every fact this package publishes is derived from the
# maintainer's one-way COBOL-to-MySQL bridge (common/*MT.scb, common/*MT.cbl),
# the record copybooks under copybooks/, and the frozen schema
# mysql/ACASDB.sql. Those files are the specification and are never modified.

# The public surface is deliberately empty: this file is a package marker, and
# a marker that exports something has taken on a second job. Naming the three
# submodules here would be worse than redundant - when a package's `__all__`
# names its submodules the star-import machinery imports them, which would
# pull in `generate`, the parser of the whole frozen tree, for anyone writing
# `from ... import *`. An empty surface closes that route as well as the plain
# one, and the module docstring still names the three for a reader.
__all__: tuple[str, ...] = ()
