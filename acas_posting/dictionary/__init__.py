"""The ACAS posting-cycle data dictionary: model, generator and runtime loader.

`acas_posting.dictionary` carries the field-level authority of this migration.
It holds the three modules that define, produce and read the mandated
machine-readable data dictionary, and it holds nothing else:

    data_dictionary/acas_posting_dictionary.json
        the generated artifact - one entry per field of every in-scope record,
        committed to the repository rather than built on demand
    data_dictionary/acas_posting_dictionary.schema.json
        the JSON Schema that artifact is validated against

MODULE INVENTORY
================
Agent Action Plan section 0.4.1.6 states each module's role in a single line,
quoted here verbatim so that this marker cannot drift from the plan:

    model.py     "The dictionary schema: copybook field (name, picture,
                 usage, sign, scale), bridge host variable, MySQL column
                 (name, type) - plus derivation notes for bridge-only
                 columns"

    generate.py  "Parses all three sources and emits the JSON dictionary;
                 flags any field present in one source and absent from
                 another"

    loader.py    "Runtime lookup so every record field cites its entry"

The package is closed at those three modules and this marker, and it has no
subpackage. In particular there is no validation module here: the artifact is
checked against its JSON Schema by a test under tests/, which is where a check
that is allowed to fail belongs.

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

WHERE THE ARTIFACT LIVES, AND THE PACKAGING CAVEAT
==================================================
The dictionary is a top-level repository SIBLING of `acas_posting`, and
deliberately not package data. Agent Action Plan section 0.3.1 places
data_dictionary/ beside the package rather than inside it, and pyproject.toml
enforces that: package discovery includes "acas_posting*" and names
"data_dictionary*" - together with "tests*", "docs*" and the compiled oracle's
own tree - in its exclude list.

One consequence follows, and is stated plainly here rather than discovered
later: the artifact is NOT present inside an installed wheel. That is
intended. The dictionary is repository data, consumed from a source checkout,
which is how the oracle scripts and the test suites run.

Nothing here relocates, copies, vendors or symlinks it into the package, and
nothing here re-derives its location. The path constants PACKAGE_ROOT,
REPOSITORY_ROOT, DATA_DICTIONARY_DIR, DATA_DICTIONARY_PATH and
DATA_DICTIONARY_SCHEMA_PATH belong to the parent package and are exported by
it; `loader.py` reuses them and owns the absence case. A second walk up the
tree here would be a second source of truth for one fact.

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

# PROVENANCE
# Every fact this package publishes is derived from the maintainer's own
# one-way COBOL-to-MySQL bridge (common/*MT.scb and common/*MT.cbl), the record
# copybooks under copybooks/, and the frozen schema mysql/ACASDB.sql. Those
# files are the specification for this package and are never modified by it.
# No licence grant is stated here: the COBOL carries the maintainer's own
# notice, which is his to make and not this migration's to copy or replace.

# The public surface of this marker is EMPTY, and the empty tuple is the whole
# statement. Agent Action Plan section 0.4.1.6 gives this file exactly one job,
# "Package marker", and a marker that exports something has quietly taken on a
# second one.
#
# WHY EMPTY, RATHER THAN AN INVENTORY OF THE THREE MODULE NAMES
# Naming the submodules here would not be a harmless convenience. When a
# package's `__all__` names its submodules, the star-import machinery is
# documented to IMPORT them - so one `from ... import *` would pull in
# `generate.py`, the parser of the frozen COBOL tree and the frozen schema, and
# reintroduce by that route the very cost this marker exists to keep away from
# `cobol/field.py` and all twenty-seven record modules. An empty surface closes
# the star-import route as well as the plain-import one, and the three modules
# are still named for a reader in MODULE INVENTORY above, as prose, which
# informs without binding anything.
#
# A tuple rather than a list, so the surface cannot be extended or mutated in
# place at run time; trivially sorted, because it is empty. Both are small
# determinism guarantees in the spirit of rule R-6.
__all__: tuple[str, ...] = ()
