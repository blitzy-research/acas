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
module, and it lives in exactly ONE place: the committed repository sibling
`data_dictionary/`, fixed there by Agent Action Plan section 0.3.1. It is
deliberately NOT relocated into this package and NOT shipped as package data -
`pyproject.toml` names `data_dictionary*` in its packaging exclusion list - so
there is one artifact, one path and no possibility of two copies disagreeing.
Publishing that path is this module's job; reading it belongs to
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

#: The machine-readable data dictionary itself - the field-level authority for this
#: migration, generated from the authoritative triple of the copybook picture clause,
#: the bridge host-variable declaration and the CREATE TABLE column definition.
DATA_DICTIONARY_PATH: Final[Path] = DATA_DICTIONARY_DIR / _DICTIONARY_FILE_NAME

#: The JSON Schema the dictionary above is validated against.
DATA_DICTIONARY_SCHEMA_PATH: Final[Path] = (
    DATA_DICTIONARY_DIR / "acas_posting_dictionary.schema.json"
)

#: The directories a reader may legitimately find the dictionary in, IN THE ORDER TO TRY
#: THEM. There is exactly ONE, and that is the whole point: the artifact is a TOP-LEVEL
#: SIBLING of this package, fixed at data_dictionary/ by Agent Action Plan section
#: 0.3.1, and `pyproject.toml` names `data_dictionary*` in its packaging exclusion list
#: so no second copy is ever created inside an installed distribution. Published as a
#: tuple rather than as the single path because `dictionary/loader.py` iterates it and
#: reports every candidate it tried when the artifact is absent.
DATA_DICTIONARY_SEARCH_PATH: Final[tuple[Path, ...]] = (DATA_DICTIONARY_DIR,)

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
    "PACKAGE_ROOT",
    "REPOSITORY_DATA_DICTIONARY_DIR",
    "REPOSITORY_ROOT",
    "__version__",
)
