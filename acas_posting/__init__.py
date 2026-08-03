"""The ACAS batch posting cycle, migrated from COBOL to Python 3.12.

This package is the Python side of a behaviour-preserving migration of the
Applewood Computers Accounting System posting cycle. The COBOL tree stays in
the repository, unmodified, as both the specification and the comparison
oracle; nothing here executes, embeds or shells out to it (rule R-1).

Scope of the migration: the cycle that carries entered transaction batches
through validation, batch-control checking, posting to the Sales, Purchase and
General ledgers together with the IRS postings the cycle reaches, and the
period-total and control-account updates.

Layout
    clock.py        the controlled clock - pins the text date and Run-Date
    dates.py        the date module, from common/maps04.cbl
    workfiles.py    pretrans.tmp / postrans.tmp as ordered sequences
    cli/            argument binding and the batch entry points
    programs/       one module per migrated COBOL program
    records/        one dataclass module per record copybook
    cobol/          COBOL language semantics; no business logic
    dal/            data access against the frozen MySQL schema
    dictionary/     the data dictionary model, generator and loader

The layers below `acas_posting` are populated progressively, and every one of
them listed above is now complete: `clock.py`, `dates.py`, `workfiles.py`, all
nine `cli/` modules, all twelve `programs/` modules, `records/`, `cobol/`, all
twenty-one `dal/` modules and `dictionary/`. What remains outstanding is outside
this package: the migration documents under `docs/migration/`, the test suites
under `tests/`, the scenario definitions under `harness/scenarios/` and
`README-python-migration.md`. Nothing in this module depends on any of them.

What this module publishes
    __version__                     the package version
    PACKAGE_ROOT                    this package's directory
    REPOSITORY_ROOT                 the checkout root, its parent
    DATA_DICTIONARY_DIR             the sibling data_dictionary/ tree, and
    REPOSITORY_DATA_DICTIONARY_DIR  that same tree named explicitly
    DATA_DICTIONARY_PATH            the generated dictionary artifact
    DATA_DICTIONARY_SCHEMA_PATH     the JSON Schema that validates it
    PACKAGE_DATA_DICTIONARY_DIR     the copy inside an installed distribution,
    PACKAGED_DATA_DICTIONARY_DIR    that same copy named explicitly, with
    PACKAGED_DATA_DICTIONARY_PATH   the two artifacts inside it
    PACKAGED_DATA_DICTIONARY_SCHEMA_PATH
    DATA_DICTIONARY_SEARCH_PATH     the two directories, in the order to try

The dictionary is the field-level authority for the migration, generated from
the copybook picture clause, the bridge host-variable declaration and the
CREATE TABLE column definition. The user's requirement, preserved in Agent
Action Plan section 0.8.2, is that the maintainer's one-way COBOL-to-MySQL
bridge - not the copybooks - defines the authoritative record-layout to table
mapping. `IRSPOSTING-REC` proves the point: `POST4-DAY`, `POST4-MONTH` and
`POST4-YEAR` have no counterpart in any copybook and exist only because the
bridge derives them under a guarded substring rule
[common/irspostingMT.cbl:L982-L987].

The dictionary is COMMITTED as a repository sibling of this package and SHIPPED
inside it: pyproject.toml names the `acas_posting` packages one by one and maps
the committed data_dictionary/ tree in as `acas_posting.data_dictionary`, so an
installed distribution carries a copy at `acas_posting/data_dictionary/`. That
is not a convenience - the record modules resolve their field metadata while
they are being imported, so a distribution that could not reach the artifact
could not import its own record layer. The constants below therefore name BOTH
locations, and either may legitimately be absent: a source checkout has only
the sibling, a wheel only the packaged copy. Choosing between them, and
reporting the case where neither is readable, is
`acas_posting.dictionary.loader`'s job, not this module's.

Import is a pure namespace definition. Nothing here opens a file, validates a
path or raises if the artifact is missing - a package marker able to fail
because of its surroundings would be a new validation the migration is not
permitted to add (rule R-3), and it would take every module beneath it down
with it.
"""

from pathlib import Path
from typing import Final

# The version of this migration package, and nothing else. It deliberately
# does not impersonate the COBOL system's own release, which its maintainer
# records in README.TXT and Changelog - neither of which this migration
# modifies. pyproject.toml declares the same value; a divergence between the
# two is a defect, since they are the only places a version is written down.
# A string literal rather than a lookup of installed distribution metadata,
# which would raise when the package runs straight from a source checkout and
# would make the value vary with the environment (rule R-6).
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
#  WHERE THE DICTIONARY LIVES, AND WHY THERE ARE TWO PLACES TO LOOK
#  The dictionary is COMMITTED as a top-level repository sibling of
#  `acas_posting` - Agent Action Plan section 0.3.1 places data_dictionary/
#  beside the package, section 0.4.1.6 fixes the file name, and
#  `acas_posting.dictionary.generate` writes exactly that path. Nothing here
#  relocates it. It is also SHIPPED, because twenty-five record modules and two
#  of the COBOL semantics modules resolve their field metadata at import time, so
#  an installed wheel that could not reach it would fail on
#  `import acas_posting.records.gl_posting` with a DictionaryNotFoundError rather
#  than merely lack a convenience. pyproject.toml reconciles the two by mapping
#  the one committed directory into the wheel as
#  `acas_posting/data_dictionary/` - one source of truth, copied at build time,
#  never edited in two places.
#
#  So this module publishes both locations as plain paths, plus the order to try
#  them in:
#      DATA_DICTIONARY_*            the repository sibling; the path a source
#                                   checkout reads and the generator writes
#      PACKAGE_DATA_DICTIONARY_DIR  the copy inside an installed distribution
#      PACKAGED_DATA_DICTIONARY_*   that same copy under its second published
#                                   spelling, and the two artifacts in it
#      DATA_DICTIONARY_SEARCH_PATH  the two directories, in the order to try
#  Nothing here chooses between them, because choosing means asking the
#  filesystem which one exists, and this module does not touch the filesystem
#  (see below). `acas_posting.dictionary.loader` makes that choice: it walks the
#  search path, preferring the packaged copy through `importlib.resources` and
#  falling back to the repository copy - which is the only one present in a
#  checkout, where the mapped directory does not exist. The singular
#  DATA_DICTIONARY_* constants continue to name the REPOSITORY location, which is
#  what the generator's `--output` default and every regeneration and comparison
#  workflow need: those write the source of truth, never a copy.
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
#  WHICH CONSTANT EXISTS WHERE, STATED PLAINLY
#  In a source checkout DATA_DICTIONARY_PATH exists and the packaged copy does
#  not: the build-time mapping has not run, so the package holds no
#  data_dictionary/ subdirectory. In an installed distribution it is the other
#  way round - the packaged copy exists, and REPOSITORY_ROOT is site-packages,
#  which holds no data_dictionary/ tree. An editable install can present both.
#  All three are ordinary and none is an error, so BOTH are paths that may
#  legitimately be absent and NEITHER is validated here. Deciding which to read,
#  and reporting the case where neither is readable, is
#  `acas_posting.dictionary.loader`'s responsibility, not this module's.
#
#  THIS MODULE MUST NOT VALIDATE  (rule R-3)
#  What follows are paths, not open files. Nothing below reads, opens, parses
#  or even asks the filesystem whether either artifact is there, and nothing
#  below raises if both are missing - which is precisely why the search order
#  is published as a tuple to be walked elsewhere rather than resolved to a
#  single winner here, since choosing a winner would mean probing the disk.
#  Import stays a pure namespace definition: a package marker able to fail
#  because of its surroundings would be a new validation this migration is not
#  permitted to add, and it would take every module that sits under it down
#  with it.
# ---------------------------------------------------------------------------

#: The directory name the artifact lives in, under BOTH candidate roots, and
#: the artifact's own filename. Written once so the two published locations
#: cannot drift apart, and so every path below spells them the same way.
_DICTIONARY_DIR_NAME: Final[str] = "data_dictionary"
_DICTIONARY_FILE_NAME: Final[str] = "acas_posting_dictionary.json"
#: This package's own directory, absolute and symlink-free.
PACKAGE_ROOT: Final[Path] = Path(__file__).resolve().parent

#: The repository checkout root - the parent of this package, and the tree that
#: also holds the frozen COBOL specification sources, the frozen MySQL schema,
#: the generated data dictionary, the migration documents and the compiled
#: comparison oracle. Every one of those is a SIBLING of this package, never a
#: child of it.
REPOSITORY_ROOT: Final[Path] = PACKAGE_ROOT.parent

#: The generated data dictionary's directory: a top-level repository sibling,
#: and the SOURCE OF TRUTH the Agent Action Plan places there (sections 0.3.1
#: and 0.4.1.6). This is what the generator writes and what `--check` compares.
DATA_DICTIONARY_DIR: Final[Path] = REPOSITORY_ROOT / _DICTIONARY_DIR_NAME

#: The same two artifacts as they appear INSIDE an installed distribution, put
#: there by the `package-dir` mapping in pyproject.toml that makes the
#: repository-root data_dictionary/ tree this package's data directory. Present
#: in a wheel, absent from a plain source checkout. Nothing in this repository
#: writes here; the build step does.
PACKAGE_DATA_DICTIONARY_DIR: Final[Path] = PACKAGE_ROOT / _DICTIONARY_DIR_NAME

#: The machine-readable data dictionary itself - the field-level authority for
#: this migration, generated from the authoritative triple of the copybook
#: picture clause, the bridge host-variable declaration and the CREATE TABLE
#: column definition. Its root members are `meta`, `sources`, `tables`,
#: `entries` and `coverage`; an entry is keyed `<TABLE-NAME>.<COLUMN-NAME>`
#: where a column backs it and `<COPYBOOK-RECORD>.<FIELD-NAME>` where the field
#: is copybook-only, `<PROGRAM-RECORD>.<FIELD-NAME>` where the field is
#: declared inline in a program's FILE or SORT SECTION. Read it through
#: `acas_posting.dictionary.loader`; never from here.
DATA_DICTIONARY_PATH: Final[Path] = DATA_DICTIONARY_DIR / _DICTIONARY_FILE_NAME

#: The JSON Schema the dictionary above is validated against. The dictionary's
#: own `meta.schema_ref` names it relatively, and this constant is that
#: reference resolved against DATA_DICTIONARY_DIR - the same directory, by
#: construction, so the two can never drift apart.
DATA_DICTIONARY_SCHEMA_PATH: Final[Path] = (
    DATA_DICTIONARY_DIR / "acas_posting_dictionary.schema.json"
)

#: The two directories a reader may legitimately find the dictionary in, IN THE
#: ORDER TO TRY THEM: the packaged copy first, the repository sibling second.
#:
#: Packaged first because that ordering is the one that cannot mislead. An
#: installed wheel has no repository above site-packages, so its only copy is
#: the packaged one; a source checkout has no packaged copy, so its only copy is
#: the sibling; and an editable install can present both, where the packaged
#: copy is the one the distribution actually declares. Trying the repository
#: first would, in that last case, read a file the installed distribution does
#: not vouch for.
#:
#: A tuple, not a list, and resolved nowhere in this module: which entry exists
#: is a question about the filesystem, and this module does not ask the
#: filesystem anything (see THIS MODULE MUST NOT VALIDATE above).
#: `acas_posting.dictionary.loader` walks it, prefers the first entry that is
#: there, and reports the absence of both.
DATA_DICTIONARY_SEARCH_PATH: Final[tuple[Path, ...]] = (
    PACKAGE_DATA_DICTIONARY_DIR,
    DATA_DICTIONARY_DIR,
)

#: The packaged directory under its SECOND PUBLISHED SPELLING, and the two
#: artifacts inside it. `PACKAGE_DATA_DICTIONARY_DIR` above and
#: `PACKAGED_DATA_DICTIONARY_DIR` here are ONE directory under two names, not
#: two directories, and this constant is defined by ASSIGNMENT from the first
#: rather than by repeating its expression, which is what makes it impossible
#: for the two to drift apart.
#:
#: The shorter spelling is the one the lookup consumes:
#: DATA_DICTIONARY_SEARCH_PATH is built from it and
#: `acas_posting.dictionary.loader` resolves the shipped copy against it
#: through `importlib.resources`. The longer spelling is published for callers
#: and tooling outside this package that name the shipped FILES rather than the
#: directory - a packaging check, or a test asserting a wheel carries them -
#: which is why the two file paths below exist at all.
PACKAGED_DATA_DICTIONARY_DIR: Final[Path] = PACKAGE_DATA_DICTIONARY_DIR

#: The repository sibling under its SECOND PUBLISHED SPELLING, the mirror of
#: the pair above. `DATA_DICTIONARY_DIR` and `REPOSITORY_DATA_DICTIONARY_DIR`
#: are ONE directory under two names, defined by assignment so they cannot
#: drift. The explicit spelling exists so a caller naming both candidates -
#: a diagnostic, or a packaging check - can say "repository" and "packaged"
#: rather than relying on the unqualified name meaning the repository one.
REPOSITORY_DATA_DICTIONARY_DIR: Final[Path] = DATA_DICTIONARY_DIR

#: The shipped copy of the machine-readable data dictionary. Same bytes as
#: DATA_DICTIONARY_PATH by construction: the build copies the committed file
#: rather than regenerating it, so there is one source of truth and no way for
#: the two to disagree.
PACKAGED_DATA_DICTIONARY_PATH: Final[Path] = (
    PACKAGED_DATA_DICTIONARY_DIR / "acas_posting_dictionary.json"
)

#: The shipped copy of the JSON Schema. It travels with the dictionary because
#: `meta.schema_ref` names it relatively; shipping one without the other would
#: leave that reference dangling.
PACKAGED_DATA_DICTIONARY_SCHEMA_PATH: Final[Path] = (
    PACKAGED_DATA_DICTIONARY_DIR / "acas_posting_dictionary.schema.json"
)

# The complete public surface of this module: the version and the generated
# data dictionary's paths. Sorted, and a tuple, so the surface cannot be
# reordered, extended or mutated in place at run time (rule R-6).
__all__: Final[tuple[str, ...]] = (
    "DATA_DICTIONARY_DIR",
    "DATA_DICTIONARY_PATH",
    "DATA_DICTIONARY_SCHEMA_PATH",
    "DATA_DICTIONARY_SEARCH_PATH",
    "PACKAGED_DATA_DICTIONARY_DIR",
    "PACKAGED_DATA_DICTIONARY_PATH",
    "PACKAGED_DATA_DICTIONARY_SCHEMA_PATH",
    "PACKAGE_DATA_DICTIONARY_DIR",
    "PACKAGE_ROOT",
    "REPOSITORY_DATA_DICTIONARY_DIR",
    "REPOSITORY_ROOT",
    "__version__",
)
