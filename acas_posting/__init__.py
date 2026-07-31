"""ACAS batch posting cycle - the Python 3.12 migration of the COBOL original.

`acas_posting` is the behaviourally exact Python 3.12 clone of the batch
posting cycle of ACAS, the Applewood Computers Accounting System. The cycle
carries entered transaction batches through four stages, in this order:

    1. validation;
    2. batch-control checking - the control-total gate that decides whether a
       batch may be posted at all;
    3. posting to the Sales, Purchase and General ledgers, including the
       IRS-module postings the cycle reaches;
    4. period-total and control-account updates.

It is a CLONE, not an improvement. Agent Action Plan section 0.1.1 states the
objective as "a Python 3.12 implementation of the ACAS batch posting cycle that
is a behaviorally exact clone of the compiled COBOL - not an improvement on
it". The COBOL is not deleted, ported in place or wrapped: it stays in this
repository exactly as its maintainer left it, "serving simultaneously as the
specification and as the comparison oracle".

WHAT "EXACT" MEANS  (the one acceptance condition)
==================================================
"Exact" is not a matter of judgement here; it is defined operationally, and
Agent Action Plan section 0.1.1 gives the definition verbatim:

    "the ordering-normalized diff of affected database tables after a Python
    run versus a COBOL run against an identical seed must be empty"

So the question this package must answer is never "does this look right?" but
"is the diff empty?". Seed a scenario, run the compiled cycle, dump the
affected tables ordering-normalised, reset, run this cycle against the same
seed, dump again - and the two dumps must be identical. A non-empty diff is
always a real behavioural difference, because the dump is deterministic by
construction: every one of the 22 in-scope tables in the frozen schema has a
single-column primary key and no secondary index, and none carries a
TIMESTAMP column, an AUTO_INCREMENT column or a column-level DEFAULT.

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!  READ THIS BEFORE YOU READ ANY OTHER MODULE  (rule R-4)                 !!
!!                                                                         !!
!!  THE LEGACY DEFECTS IN THIS PACKAGE ARE REPRODUCED ON PURPOSE.          !!
!!                                                                         !!
!!  Agent Action Plan section 0.8.2, preserved verbatim from the user's    !!
!!  own requirements:                                                      !!
!!                                                                         !!
!!      "There is no test suite: compiled COBOL execution is the           !!
!!      behavioral specification, defects included. A defect reproduced    !!
!!      is correct; a defect fixed is a failure."                          !!
!!                                                                         !!
!!  That sentence inverts normal engineering judgement for this whole      !!
!!  package. If you find a rounding oddity, a half-posted double entry, a  !!
!!  lost update, an unbounded array subscript, a silently dropped record   !!
!!  or three copies of one idiom that disagree with each other, you have   !!
!!  found the specification, not a bug to fix. Twenty-two such anomalies   !!
!!  are catalogued in docs/migration/anomaly-log.md with the COBOL locator !!
!!  and the reproducing module for each, and fourteen of them are locked   !!
!!  in place by dedicated tests precisely so that a well-meaning           !!
!!  correction fails the suite instead of passing unnoticed.               !!
!!                                                                         !!
!!  Improving this code is the one way to break it.                        !!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

NO COBOL AT RUNTIME  (rule R-1)
===============================
COBOL is the specification for this migration, not a runtime dependency of the
result. This package contains no COBOL and makes no out-of-process call: it
never launches a child process, never loads a foreign library, and never
reaches the sibling compiled-oracle tree. The shipped artifact must run on a
host with no COBOL compiler and no COBOL runtime present, and it does.

Every COBOL construct is reimplemented natively rather than delegated. Picture
clauses, the six numeric storage classes, the arithmetic verbs and their store
semantics, MOVE between unlike pictures, 88-level condition names and the SORT
verb's key ordering all live in `acas_posting.cobol`; each numbered file
handler and its generated MySQL bridge becomes a module in `acas_posting.dal`
issuing SQL against the frozen schema; and `acas_posting.dates` reimplements
common/maps04.cbl in full, including its 1600-12-31 ordinal epoch, rather than
calling it.

The compiled comparison oracle lives in a top-level sibling tree, never inside
this package, and pyproject.toml packages `acas_posting*` and nothing else.
That is what makes rule R-1 structural rather than a matter of discipline:
there is no import path from the shipped package to the oracle.

WHAT THIS MODULE EXPORTS - AND WHY THAT IS ALL
==============================================
Agent Action Plan section 0.4.1.1 gives this file's entire mandate in one line:
"Package marker; exports the version and the dictionary path constant". So it
exports a version string and the paths of the generated data dictionary, and
does nothing else whatsoever.

In particular this module is NOT a convenience-import hub. It contains no
`acas_posting` import of any kind, and that is deliberate rather than
minimalist:

  * Agent Action Plan section 0.4.3 fixes a strict acyclic layering -
    `records/*.py` may import `cobol.field` and `dictionary.loader` only,
    "this keeps the record layer a leaf", and `cobol/*.py` may import
    `dictionary.loader` only. Eager re-exports here would execute those
    imports whenever anything in the package is imported, manufacturing the
    very cycles that layering forbids.
  * Agent Action Plan section 0.4.3 also promises that the arithmetic test
    tier "imports only `cobol` and `records` and touches no database, so it
    runs anywhere". If importing this package pulled in `dal`, then importing
    `acas_posting.cobol.arithmetic` would pull in a database driver and that
    promise would be broken on any host without MariaDB.

Importing this module therefore binds the six public names listed in `__all__`
and has no other observable effect. It opens no file and reads no data, opens
no connection, configures no logging, starts no thread, no event loop and no
process pool, touches no clock and no entropy source, and cannot fail for an
environmental reason. Argument handling belongs to `acas_posting.cli`; the
documented invocation route is `python -m acas_posting`, and pyproject.toml
deliberately declares no console entry point.

PACKAGE LAYOUT AND THE LAYERING CONTRACT
========================================
The tree in Agent Action Plan section 0.3.1 is exhaustive - "Every file is
named explicitly below; nothing is left to inference" - and the direct children
of this package are closed at five modules and six subpackages:

    __init__.py     this file: the package marker, the version and the
                    generated data dictionary's paths
    __main__.py     the `python -m acas_posting` router, from common/ACAS.cbl's
                    system-selection menu, minus all screen I/O
    clock.py        the controlled clock, which pins both run-date observables
    dates.py        the date module, from common/maps04.cbl
    workfiles.py    pretrans.tmp and postrans.tmp as ordered in-process
                    sequences, from copybooks/wsnames.cob L14-L17

    cli/            the batch entry points and the linkage-parameter binding
    programs/       one module per migrated COBOL program - the only place
                    business logic lives
    records/        one dataclass module per record copybook; a leaf layer
    cobol/          the COBOL-language semantics runtime
    dal/            the data-access layer: one module per file handler
    dictionary/     the data dictionary's model, generator and runtime loader

Agent Action Plan section 0.3.1 states the layering contract that keeps the
arithmetic parity suite possible, verbatim:

    "`cobol/` contains no business logic and `programs/` contains no numeric
    primitives."

Business logic lives ONLY in `programs/`. Every picture-clause, packed-decimal,
truncation and MOVE rule lives in `cobol/`, where it can be proved in
isolation against values captured from the compiled programs, with no database
and no scenario setup; the program modules then read as accounting logic, so
any parity failure localises immediately to one layer or the other.

NUMERIC POLICY  (rule R-2)
==========================
No accounting value may pass through a binary floating-point type at any
point - not in computation, not in storage, not in transport. Money and
quantity values are `decimal.Decimal` carrying the precision and scale of the
COBOL field that receives them, truncating toward zero on store exactly as an
un-ROUNDED COBOL store does; the BINARY-CHAR, BINARY-SHORT and BINARY-LONG
fields are native Python `int`, so their truncation on divide is integer
truncation as the compiled program's is. The frozen schema itself declares no
FLOAT, DOUBLE or REAL column anywhere, and pandas and numpy are excluded from
the dependency set outright for this reason. The version below is a string,
not a number, for the same discipline.

DETERMINISM  (rule R-6)
=======================
Compiled behaviour is the tie-breaker for every semantic question that reading
the source cannot settle, and two runs of one scenario under the same pinned
clock must produce byte-identical dumps. That is affordable because every
in-scope posting program contains zero clock reads and receives the run date
purely through linkage, so `clock.py` pins exactly two observables - the text
date `to-day pic x(10)` and the binary `Run-Date` (copybooks/wssystem.cob
L67) - at the CLI boundary, and nothing downstream reads a clock. Nothing in
this package consults an entropy source or the process environment either, and
the version below is a hard-coded literal for precisely that reason.

SEQUENTIAL EXECUTION, NO NEW BEHAVIOUR  (rule R-3)
==================================================
Execution is strictly sequential, matching the single-threaded COBOL: no
thread, no event loop, no process pool, no connection pool. The migration adds
no validation, no field and no schema change - mysql/ACASDB.sql is untouched,
no DDL is ever emitted, and the record modules mirror their copybooks field for
field with nothing added, misnamings included.

TRACEABILITY AND THE MANDATED DELIVERABLES  (rule R-5)
======================================================
Every program maps to a module, every paragraph to a function and every field
to a data-dictionary entry, and those mappings are recorded as documents rather
than left implicit in the code:

    data_dictionary/acas_posting_dictionary.json
        the machine-readable data dictionary - the field-level authority for
        this migration; its paths are exported below
    data_dictionary/acas_posting_dictionary.schema.json
        the JSON Schema the dictionary is validated against
    docs/migration/traceability.md
        program-to-module, paragraph-to-function and field-to-dictionary-entry
    docs/migration/anomaly-log.md
        the register of the legacy defects this migration reproduces
    docs/migration/ambiguity-resolutions.md
        each semantic question and the compiled-behaviour arbitration that
        settled it
    docs/migration/scenario-diff-evidence.md
        the empty-diff evidence, per mandated scenario
    README-python-migration.md
        how to build the comparison oracle, seed it, run both cycles and diff
        the resulting table state

THE FREEZE
==========
Nothing in this package may cause a diff to common/, copybooks/, general/,
sales/, purchase/, irs/, stock/ or mysql/ACASDB.sql. Those trees are read
exhaustively as specification and are never modified, reformatted, commented,
relocated or built from here. Agent Action Plan section 0.8.1, verbatim: "Any
diff touching `common/*.cbl`, `common/*.scb`, `copybooks/*.cob`,
`general/*.cbl`, `sales/*.cbl`, `purchase/*.cbl`, `irs/*.cbl` or
`mysql/ACASDB.sql` is a defect in the migration, regardless of how harmless it
appears."

THE MAINTAINER'S OWN RECORD IS LEFT ALONE
=========================================
The COBOL system's own release state is the maintainer's to record, and he
records it in two files this migration does not touch:

    README.TXT   entry dated 2025-09-21 - all source updated to "v3.3
                 pre-final release", with the caveat that General has not been
                 worked on since it moved to the COBOL 3.2 compiler. That
                 caveat is why expected values for General Ledger scenarios
                 come only from the compiled oracle, never from documentation
                 and never from reasoning about intent.
    Changelog    entry dated 2025-09-20 - "3.3.00 Version update and builds
                 reset."

Neither file is edited, appended to or repurposed: they document the COBOL
system and its version history, and modifying them would misrepresent the
maintainer's record (Agent Action Plan section 0.2.1.4). This package's own
documentation is a new file, README-python-migration.md, which cross-references
them instead.
"""

from pathlib import Path
from typing import Final

# ---------------------------------------------------------------------------
#  THE VERSION OF THIS MIGRATION PACKAGE  (rules R-2 and R-6)
# ---------------------------------------------------------------------------
#  This versions the PYTHON MIGRATION PACKAGE, and nothing else. It
#  deliberately does not impersonate the COBOL system's own release, which is
#  v3.3 pre-final and which its maintainer records in README.TXT (entry dated
#  2025-09-21) and Changelog (2025-09-20, "3.3.00 Version update and builds
#  reset."). Both of those files are his record and neither is modified by
#  this migration, so a Python constant must not claim to speak for them.
#
#  PIN-PARITY CONTRACT: pyproject.toml declares the distribution version, and
#  it declares "0.1.0". This constant and that manifest must agree, and a
#  divergence between them is a defect in the migration rather than a cosmetic
#  mismatch - the two are the only places a version is written down.
#
#  It is a STRING LITERAL, and both halves of that matter.
#
#    * A string, never a number. Rule R-2 keeps binary floating point out of
#      this package altogether, so a bare decimal-looking numeric constant has
#      no business appearing in it - not even here, where it could never reach
#      an accounting value. One rule applied without exception is far easier to
#      hold than one rule with a carve-out.
#
#    * A literal, never a lookup. Reading the version back out of installed
#      distribution metadata would raise when the package is used straight
#      from a source checkout without being installed - which is exactly how
#      the oracle scripts and the test suites invoke it - and it would make
#      the value vary with the environment it happens to be running in. Rule
#      R-6 requires two runs of one scenario under the same pinned clock to be
#      byte-identical; an environment-derived constant in the one module every
#      other module sits under is not the place to start eroding that.
# ---------------------------------------------------------------------------
__version__: Final[str] = "0.1.0"

# ---------------------------------------------------------------------------
#  WHERE THE GENERATED DATA DICTIONARY LIVES  (rule R-5)
# ---------------------------------------------------------------------------
#  WHY THESE CONSTANTS EXIST
#  Rule R-5 requires that every field map to a data-dictionary entry and that
#  the mapping be recorded rather than left implicit in the code. These
#  constants are what makes that mechanical instead of manual:
#  `acas_posting.dictionary.loader` lets every record field cite its dictionary
#  key at run time, and the loader has to be able to find the artifact. Agent
#  Action Plan section 0.8.1 makes the ordering a directive rather than a
#  preference - "Data dictionary first. The dictionary is generated from the
#  bridge before record definitions are written, and every Python field
#  definition cites its entry. This ordering is a directive, not a
#  preference - it is what prevents fields being transcribed by eye."
#
#  WHOSE AUTHORITY THE DICTIONARY CARRIES
#  Not the copybooks'. The user's own requirement, preserved verbatim in Agent
#  Action Plan section 0.8.2 and byte-identical to the `meta.authority` string
#  inside the generated artifact itself:
#
#      The maintainer's one-way COBOL-to-MySQL bridge defines the
#      authoritative record-layout ↔ table mapping - it is the data dictionary
#      for this migration.
#
#  The codebase proves why that is non-negotiable rather than stylistic. The
#  internal IRS posting table carries three columns - POST4-DAY, POST4-MONTH
#  and POST4-YEAR - that have NO counterpart in any copybook. They exist only
#  because the bridge derives them from a date string under a guarded
#  substring rule [common/irspostingMT.cbl:L982-L987], and when that guard
#  fails they are left at zero while the raw date text is still stored, so the
#  row written is internally inconsistent. Agent Action Plan section 0.1.1: "A
#  migration driven from the copybooks alone would silently omit three columns
#  of a posting table." All three duly appear in the dictionary as one-sided
#  entries - present in the bridge and in the column, absent from any
#  copybook - which is exactly the class of fact a hand-transcribed field list
#  loses.
#
#  WHY THE PATHS POINT *OUT* OF THIS PACKAGE
#  The dictionary is a top-level repository sibling of `acas_posting`, NOT
#  package data. Agent Action Plan section 0.3.1 places data_dictionary/ beside
#  the package rather than inside it, and pyproject.toml enforces that: its
#  package discovery includes "acas_posting*" and names "data_dictionary*" in
#  its exclude list, then states the division of labour outright - "The
#  generated data dictionary lives in the sibling data_dictionary/ tree and is
#  therefore NOT package data. Nothing here relocates it; the runtime path
#  constant that points at it belongs to acas_posting/__init__.py."
#
#  So the derivation below walks UP out of the package and back down into the
#  sibling directory. Nothing here relocates, copies, vendors or symlinks the
#  artifact into the package, and nothing here declares it as package data.
#
#  `Path(__file__).resolve()` rather than a bare `Path(__file__)`: resolving
#  makes every constant absolute and symlink-free, so its value is stable no
#  matter how the interpreter was invoked, what the working directory is, or
#  whether a relative entry on the module search path is what put this package
#  within reach. Rule R-6 wants a value that does not move under its own
#  caller; resolving once, here, is the cheapest way to get one. Nothing in
#  this module alters the search path either - not by insertion, not by
#  reordering, not at all.
#
#  To be exact about what resolving costs, since this module claims to be
#  inert: `resolve()` asks the operating system to canonicalise the path,
#  which follows symbolic links, but it opens nothing, reads no file content
#  and - defaulting to `strict=False` - cannot raise for a path that is not
#  there. That is a canonicalisation, not a validation, and it is the reason
#  a checkout reached through a symbolic link still yields the real tree.
#
#  THE PACKAGING CAVEAT, STATED HONESTLY
#  Because data_dictionary/ is excluded from packaging, DATA_DICTIONARY_PATH
#  will NOT exist inside an installed wheel. That is intended and not an
#  oversight: the dictionary is repository data, consumed from a source
#  checkout, which is how the oracle scripts and the test suites run.
#  Resolving that absence - reporting it, or declining to start - is
#  `acas_posting.dictionary.loader`'s responsibility, not this module's.
#
#  THIS MODULE MUST NOT VALIDATE  (rule R-3)
#  What follows are paths, not open files. Nothing below reads, opens, parses
#  or even asks the filesystem whether the artifact is there, and nothing
#  below raises if it is missing. Import stays a pure namespace definition: a
#  package marker able to fail because of its surroundings would be a new
#  validation this migration is not permitted to add, and it would take every
#  module that sits under it down with it.
# ---------------------------------------------------------------------------

#: This package's own directory, absolute and symlink-free.
PACKAGE_ROOT: Final[Path] = Path(__file__).resolve().parent

#: The repository checkout root - the parent of this package, and the tree that
#: also holds the frozen COBOL specification sources, the frozen MySQL schema,
#: the generated data dictionary, the migration documents and the compiled
#: comparison oracle. Every one of those is a SIBLING of this package, never a
#: child of it.
REPOSITORY_ROOT: Final[Path] = PACKAGE_ROOT.parent

#: The generated data dictionary's directory: a top-level repository sibling,
#: deliberately excluded from packaging (see THE PACKAGING CAVEAT above).
DATA_DICTIONARY_DIR: Final[Path] = REPOSITORY_ROOT / "data_dictionary"

#: The machine-readable data dictionary itself - the field-level authority for
#: this migration, generated from the authoritative triple of the copybook
#: picture clause, the bridge host-variable declaration and the CREATE TABLE
#: column definition. Its root members are `meta`, `sources`, `tables`,
#: `entries` and `coverage`; an entry is keyed `<TABLE-NAME>.<COLUMN-NAME>`
#: where a column backs it and `<COPYBOOK-RECORD>.<FIELD-NAME>` where the field
#: is copybook-only. Read it through `acas_posting.dictionary.loader`; never
#: from here.
DATA_DICTIONARY_PATH: Final[Path] = DATA_DICTIONARY_DIR / "acas_posting_dictionary.json"

#: The JSON Schema the dictionary above is validated against. The dictionary's
#: own `meta.schema_ref` names it relatively, and this constant is that
#: reference resolved against DATA_DICTIONARY_DIR - the same directory, by
#: construction, so the two can never drift apart.
DATA_DICTIONARY_SCHEMA_PATH: Final[Path] = (
    DATA_DICTIONARY_DIR / "acas_posting_dictionary.schema.json"
)

# The complete public surface of this module: the version and the generated
# data dictionary's paths, which is precisely the mandate Agent Action Plan
# section 0.4.1.1 gives this file. Nothing else belongs here - no re-exported
# submodule, no lazy `__getattr__` shim, no helper.
#
# Sorted, and a tuple rather than a list: sorted so the order is a mechanical
# consequence of the names instead of an editorial choice, and a tuple so the
# surface cannot be reordered, extended or mutated in place at run time. Both
# are small determinism guarantees in the spirit of rule R-6.
__all__: Final[tuple[str, ...]] = (
    "DATA_DICTIONARY_DIR",
    "DATA_DICTIONARY_PATH",
    "DATA_DICTIONARY_SCHEMA_PATH",
    "PACKAGE_ROOT",
    "REPOSITORY_ROOT",
    "__version__",
)
