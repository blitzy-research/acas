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

Every layer listed above is complete, and so is everything outside this package
that the migration owes. Inside: `clock.py`, `dates.py`, `workfiles.py`, the ten
`cli/` modules (`__init__`, `args`, `rdbms_params` and the seven route entry
points), the thirteen `programs/` modules (`__init__` and the twelve migrated
programs), the twenty-eight `records/` modules, the eight `cobol/` modules, the
twenty-two `dal/` modules and the four `dictionary/` modules. Outside: the four
migration documents under `docs/migration/` - `traceability.md`,
`anomaly-log.md`, `ambiguity-resolutions.md` and `scenario-diff-evidence.md` -
the thirty files under `tests/` across the arithmetic, scenario and
determinism tiers, the nine scenario definitions under `harness/scenarios/`,
and `README-python-migration.md` at the repository root. Nothing in this module
depends on any of them, which is why this list is a statement of repository
state and never a precondition of import.

The generated data dictionary is the field-level authority for every record
module, and it lives in two places: a committed repository sibling and a copy
packaged inside an installed distribution. Either may legitimately be absent -
a source checkout has only the first, a wheel only the second - so both are
named here and choosing between them belongs to
`acas_posting.dictionary.loader`. Import is a pure namespace definition: it
opens no file and validates no path, because a marker that could fail because
of its surroundings would take the whole package down with it.
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
PACKAGE_ROOT: Final[Path] = Path(__file__).resolve().parent

#: The repository checkout root - the parent of this package, and the tree that also
#: holds the frozen COBOL specification sources, the frozen MySQL schema, the generated
#: data dictionary and the compiled comparison oracle.
REPOSITORY_ROOT: Final[Path] = PACKAGE_ROOT.parent

DATA_DICTIONARY_DIR: Final[Path] = REPOSITORY_ROOT / _DICTIONARY_DIR_NAME

PACKAGE_DATA_DICTIONARY_DIR: Final[Path] = PACKAGE_ROOT / _DICTIONARY_DIR_NAME

#: The machine-readable data dictionary itself - the field-level authority for this
#: migration, generated from the authoritative triple of the copybook picture clause,
#: the bridge host-variable declaration and the CREATE TABLE column definition.
DATA_DICTIONARY_PATH: Final[Path] = DATA_DICTIONARY_DIR / _DICTIONARY_FILE_NAME

#: The JSON Schema the dictionary above is validated against.
DATA_DICTIONARY_SCHEMA_PATH: Final[Path] = (
    DATA_DICTIONARY_DIR / "acas_posting_dictionary.schema.json"
)

#: The two directories a reader may legitimately find the dictionary in, IN THE ORDER TO
#: TRY THEM: the packaged copy first, the repository sibling second.
DATA_DICTIONARY_SEARCH_PATH: Final[tuple[Path, ...]] = (
    PACKAGE_DATA_DICTIONARY_DIR,
    DATA_DICTIONARY_DIR,
)

#: The packaged directory under its SECOND PUBLISHED SPELLING, and the two artifacts
#: inside it.
PACKAGED_DATA_DICTIONARY_DIR: Final[Path] = PACKAGE_DATA_DICTIONARY_DIR

#: The repository sibling under its SECOND PUBLISHED SPELLING, the mirror of the pair
#: above.
REPOSITORY_DATA_DICTIONARY_DIR: Final[Path] = DATA_DICTIONARY_DIR

#: The shipped copy of the machine-readable data dictionary. Same bytes as
#: DATA_DICTIONARY_PATH by construction.
PACKAGED_DATA_DICTIONARY_PATH: Final[Path] = (
    PACKAGED_DATA_DICTIONARY_DIR / "acas_posting_dictionary.json"
)

#: The shipped copy of the JSON Schema. It travels with the dictionary because
#: `meta.schema_ref` names it relatively.
PACKAGED_DATA_DICTIONARY_SCHEMA_PATH: Final[Path] = (
    PACKAGED_DATA_DICTIONARY_DIR / "acas_posting_dictionary.schema.json"
)

# The complete public surface of this module: the version and the generated data
# dictionary's paths.
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
