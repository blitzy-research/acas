"""The ACAS batch posting cycle, migrated from COBOL to Python 3.12.

The Python side of a behaviour-preserving migration of the Applewood Computers
Accounting System posting cycle: batch validation, batch-control checking,
posting to the Sales, Purchase and General ledgers together with the IRS
postings the cycle reaches, and the period-total and control-account updates.
The COBOL tree stays in the repository unmodified as both specification and
comparison oracle; nothing here executes, embeds or shells out to it (R-1).

Layout
    clock.py        pins the run date's two observables
    dates.py        the date module, from common/maps04.cbl
    workfiles.py    pretrans.tmp / postrans.tmp as ordered sequences
    cli/            argument binding and the batch entry points
    programs/       one module per migrated COBOL program
    records/        one dataclass module per record copybook
    cobol/          COBOL language semantics; no business logic
    dal/            data access against the frozen MySQL schema
    dictionary/     the data dictionary model, generator and loader

`docs/migration/traceability.md` is the inventory of what the migration delivers,
inside this package and outside it; nothing in this module depends on any of it,
and import is never conditional on repository state.

The generated data dictionary is the field-level authority for every record
module. It is COMMITTED in exactly ONE place - the repository sibling
`data_dictionary/`, fixed there by Agent Action Plan section 0.3.1, which the
generator writes and nothing relocates - and it is SHIPPED from there as package
data, because a wheel installs this package into `site-packages` with no sibling
beside it and rule R-5 has every record module read the dictionary while it is
being imported. `pyproject.toml` maps the package name
`acas_posting.data_dictionary` onto that committed directory, so the build copies
the same bytes to `acas_posting/data_dictionary/` inside the wheel: one artifact
in the checkout, one artifact in an installed tree, and the two candidates never
coexist in the same tree. Publishing both paths is this module's job; reading
them belongs to `acas_posting.dictionary.loader`. Import is a pure namespace
definition: it opens no file and validates no path, because a marker that could
fail because of its surroundings would take the whole package down with it.
"""

from pathlib import Path
from typing import Final

# The version of this migration package, and nothing else.
__version__: Final[str] = "0.1.0"

# Rule R-5 requires that every field map to a data-dictionary entry and that the mapping
# be recorded rather than left implicit in the code.

#: The directory name the artifact lives in, under BOTH candidate roots, and the
#: artifact's own filename.
_DICTIONARY_DIR_NAME: Final[str] = "data_dictionary"
_DICTIONARY_FILE_NAME: Final[str] = "acas_posting_dictionary.json"
_DICTIONARY_SCHEMA_FILE_NAME: Final[str] = "acas_posting_dictionary.schema.json"
PACKAGE_ROOT: Final[Path] = Path(__file__).resolve().parent

#: The repository checkout root - the parent of this package, and the tree that also
#: holds the frozen COBOL specification sources, the frozen MySQL schema, the generated
#: data dictionary and the compiled comparison oracle.
REPOSITORY_ROOT: Final[Path] = PACKAGE_ROOT.parent

DATA_DICTIONARY_DIR: Final[Path] = REPOSITORY_ROOT / _DICTIONARY_DIR_NAME

#: The machine-readable data dictionary itself - the field-level authority for this
#: migration, generated from the authoritative triple of the copybook picture clause,
#: the bridge host-variable declaration and the CREATE TABLE column definition.
DATA_DICTIONARY_PATH: Final[Path] = DATA_DICTIONARY_DIR / _DICTIONARY_FILE_NAME

#: The JSON Schema the dictionary above is validated against.
DATA_DICTIONARY_SCHEMA_PATH: Final[Path] = (
    DATA_DICTIONARY_DIR / _DICTIONARY_SCHEMA_FILE_NAME
)

#: The dictionary AS SHIPPED INSIDE AN INSTALLED DISTRIBUTION, and the reason there are
#: two candidates rather than one.
#:
#: The COMMITTED artifact is the repository sibling above and there is exactly one of
#: those: Agent Action Plan section 0.3.1 fixes it at `data_dictionary/` beside this
#: package, the generator writes that path and no other, and this repository holds no
#: second copy of it. But a wheel installs THIS PACKAGE into `site-packages` and
#: nothing beside it, so the sibling candidate resolves to `site-packages/
#: data_dictionary/` -- a path no install has ever created. Rule R-5 has every record
#: module read the dictionary WHILE IT IS BEING IMPORTED, so an installed distribution
#: with no reachable artifact fails every CLI route before it parses an argument, which
#: is precisely what was measured before this candidate existed.
#:
#: `pyproject.toml` therefore maps the package name `acas_posting.data_dictionary` onto
#: the committed `data_dictionary/` directory and names its two JSON files as package
#: data, so the build copies them to `acas_posting/data_dictionary/` in the wheel. One
#: file in the checkout, one file in the installed tree, the same bytes in both.
PACKAGED_DATA_DICTIONARY_DIR: Final[Path] = PACKAGE_ROOT / _DICTIONARY_DIR_NAME

#: The directories a reader may legitimately find the dictionary in, IN THE ORDER TO TRY
#: THEM, and the order is deliberate.
#:
#: 1. The COMMITTED REPOSITORY SIBLING, so a source checkout resolves the artifact the
#:    generator writes and a regenerated dictionary takes effect immediately -- exactly
#:    the behaviour that held when this tuple had one entry.
#: 2. The PACKAGED COPY inside this package, which is the only candidate that exists in
#:    an installed distribution.
#:
#: The two are never both present in one tree: a checkout has no
#: `acas_posting/data_dictionary/` because that directory is created by the BUILD, and an
#: installed distribution has no `site-packages/data_dictionary/`. So the order settles a
#: precedence that cannot arise in practice, and it settles it towards the committed
#: file. Published as a tuple because `dictionary/loader.py` iterates it and reports
#: every candidate it tried when the artifact is absent.
DATA_DICTIONARY_SEARCH_PATH: Final[tuple[Path, ...]] = (
    DATA_DICTIONARY_DIR,
    PACKAGED_DATA_DICTIONARY_DIR,
)

#: The repository sibling under its SECOND PUBLISHED SPELLING, for a reader who reaches
#: for the explicit name.
REPOSITORY_DATA_DICTIONARY_DIR: Final[Path] = DATA_DICTIONARY_DIR

# The complete public surface of this module: the version and the generated data
# dictionary's paths.
__all__: Final[tuple[str, ...]] = (
    "DATA_DICTIONARY_DIR",
    "DATA_DICTIONARY_PATH",
    "DATA_DICTIONARY_SCHEMA_PATH",
    "DATA_DICTIONARY_SEARCH_PATH",
    "PACKAGED_DATA_DICTIONARY_DIR",
    "PACKAGE_ROOT",
    "REPOSITORY_DATA_DICTIONARY_DIR",
    "REPOSITORY_ROOT",
    "__version__",
)
