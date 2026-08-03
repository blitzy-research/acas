"""Shared fixtures and protocol helpers for the ACAS COBOL-to-Python test tree.

THE ONE REASON THIS FILE EXISTS, from Agent Action Plan section 0.4.3, verbatim:
"`tests/conftest.py` provides the pinned-clock fixture and the seed/dump/normalize/
diff helpers so that no test reimplements the comparison protocol."

That sentence is the whole scope. Everything the three test tiers need in common
lives here; nothing else does.

THE THREE TIERS, and what each is allowed to touch:

    tests/arithmetic/     unit-level COBOL-semantics parity. Imports only
                          acas_posting.cobol and acas_posting.records. NO database,
                          NO COBOL, NO Docker - it runs on a bare host. Its one
                          file-system prerequisite is
                          data_dictionary/acas_posting_dictionary.json, which
                          `FieldDescriptor.from_dictionary_key` reads at import.
    tests/scenarios/      end-to-end state parity. Asserts an ordering-normalised
                          EMPTY table diff between the compiled oracle and the
                          migrated cycle. Requires the harness/ Compose stack.
    tests/determinism/    two runs of one scenario under the same pinned clock must
                          produce byte-identical dumps. Requires the same stack.

Because the arithmetic tier must run anywhere, THIS MODULE IMPORTS NO HARNESS
MODULE, OPENS NO CONNECTION AND SPAWNS NO SUBPROCESS AT IMPORT TIME. Every one of
those happens inside a helper, on demand.

THERE IS NO USER RULES DOCUMENT FOR THIS PROJECT. `review_rules` reports that none
was provided, so there is no on-disk rules file to consult and no downstream reader
should look for one. The six binding rules R-1 to R-6 live in the Agent Action Plan
itself, section 0.7.2, and their exact wording is retrievable from the requirements
via `review_prompt`. Summarised, in this module's own words, and each named at the
site that honours it:

    R-1  No COBOL at runtime. The compiled oracle exists only under harness/ and is
         reached only out of process, through the harness shell scripts. harness/ is
         NOT a Python package and must never gain an __init__.py, so the three
         harness Python modules are loaded BY EXPLICIT FILE PATH below. Nothing here
         invokes cobc or cobcrun, and there is no FFI of any kind.
    R-2  Zero binary floating point. Every accounting value that passes through this
         module is a decimal.Decimal, an int or a str. There is no float literal, no
         tolerance, no epsilon, no approximate comparison, and no pandas or numpy.
    R-3  No new validations, fields or schema changes; no concurrency. This module
         emits no DDL, adds no check the COBOL lacks, and is strictly sequential.
    R-4  Legacy anomalies are reproduced, never fixed. No helper here coalesces a
         null, defaults a missing row, sorts for prettiness or trims beyond what
         harness/normalize.py already does. Each legacy oddity encoded below carries
         a comment naming its COBOL locator.
    R-5  Full traceability. Every constant and helper cites the Agent Action Plan
         section or the COBOL locator it implements.
    R-6  Compiled behaviour is the tie-breaker. An empty normalised diff is the pass
         condition; a diff exit status of 2 means the comparison could not be
         performed and is an ERROR, never a pass.

MARKERS ARE NOT REGISTERED HERE. pyproject.toml's [tool.pytest.ini_options] declares
all five - arithmetic, scenario, determinism, database, oracle - and this module
deliberately defines no `pytest_configure`, no `pytest_plugins` and no
`pytest_collection_modifyitems`. Under --strict-config a second registration risks a
collision, and a second definition of one vocabulary is exactly the divergence R-4
forbids. Each test file applies its own `pytestmark`.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import subprocess
import sys
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
from types import ModuleType
from typing import Any, Final

import pytest

# The controlled clock, and the ONLY acas_posting import this module makes.
# acas_posting/clock.py owns the conversion between a calendar date, the binary
# `Run-Date` [copybooks/wssystem.cob:L67] and the text `to-day pic x(10)`, and
# acas_posting/dates.py owns the `maps04` semantics behind it. Reimplementing either
# here would create the second definition of one vocabulary that R-4 forbids.
# Measured: importing it pulls in neither mysql.connector, sqlalchemy, yaml nor any
# harness module, so the arithmetic tier stays infrastructure-free.
from acas_posting import clock as acas_clock

# ---------------------------------------------------------------------------
#  SECTION 1  -  REPOSITORY ANCHORING
#
#  Resolved from this file's own location, so a run from any working directory
#  finds the same tree. The four presence assertions turn a mis-rooted run into an
#  immediate, legible failure instead of a confusing ImportError three frames deep.
# ---------------------------------------------------------------------------

# tests/conftest.py -> tests/ -> the repository root.
REPO_ROOT: Final[Path] = Path(__file__).resolve().parent.parent

# The four landmarks that prove this is the ACAS checkout and not some other tree.
# Each is named in the Agent Action Plan section 0.3.1 target layout: the frozen
# schema, the oracle harness, the migrated package and the frozen copybooks.
_REQUIRED_LANDMARKS: Final[tuple[tuple[str, str], ...]] = (
    ("mysql/ACASDB.sql", "the frozen MySQL schema - 33 CREATE TABLE statements"),
    ("harness", "the compiled-oracle harness tree"),
    ("acas_posting", "the migrated Python posting cycle"),
    ("copybooks", "the frozen COBOL copybooks"),
)

_missing_landmarks = [
    f"{relative} ({description})"
    for relative, description in _REQUIRED_LANDMARKS
    if not (REPO_ROOT / relative).exists()
]
if _missing_landmarks:
    raise RuntimeError(
        f"tests/conftest.py resolved the repository root to {REPO_ROOT}, but that "
        f"directory is missing: {'; '.join(_missing_landmarks)}. The root is "
        f"derived from this file's own path as tests/conftest.py -> tests/ -> "
        f"root, so either tests/conftest.py has been moved out of tests/ or the "
        f"checkout is incomplete."
    )
del _missing_landmarks

# The oracle harness. A SIBLING of acas_posting/, never a sub-package: that is
# where R-1 stops being a promise and becomes a fact, and pyproject.toml's
# [tool.setuptools] `packages` allow-list names only the seven acas_posting
# packages plus the generated data directory, so harness/ and tests/ cannot reach a
# distribution at all.
HARNESS_DIR: Final[Path] = REPO_ROOT / "harness"

# The eight scenario definitions (Agent Action Plan section 0.4.1.7). Created by
# another agent; absence is reported, never worked around.
SCENARIO_DIR: Final[Path] = HARNESS_DIR / "scenarios"

# The frozen schema. READ ONLY, by harness/normalize.py's `load_schema`, and by
# nothing else here. Agent Action Plan section 0.8.1: any diff touching it "is a
# defect in the migration, regardless of how harmless it appears".
SCHEMA_SQL_PATH: Final[Path] = REPO_ROOT / "mysql" / "ACASDB.sql"

# The generated data dictionary. The one file-system prerequisite of the
# infrastructure-free arithmetic tier, because every acas_posting.records module
# builds its field descriptors from it during a normal import.
DATA_DICTIONARY_PATH: Final[Path] = (
    REPO_ROOT / "data_dictionary" / "acas_posting_dictionary.json"
)

# WHERE AN UNRESOLVED SEMANTIC QUESTION IS RECORDED (rule R-6). Agent Action Plan
# section 0.6.8 lists five questions that cannot be settled by reading the source and
# must be arbitrated by running the compiled program; each becomes an entry in this
# document naming the experiment and its result. Where a helper below behaves in a way
# that depends on one of them, the docstring says so and points here rather than
# presenting the choice as settled.
AMBIGUITY_RESOLUTIONS_DOC: Final[Path] = (
    REPO_ROOT / "docs" / "migration" / "ambiguity-resolutions.md"
)

# The other two documents a reader of a failing comparison needs: the register of
# reproduced legacy defects (rule R-4) and the per-scenario empty-diff evidence
# (rule R-6). Named so that a failure message or a reviewer can find them.
ANOMALY_LOG_DOC: Final[Path] = REPO_ROOT / "docs" / "migration" / "anomaly-log.md"
SCENARIO_DIFF_EVIDENCE_DOC: Final[Path] = (
    REPO_ROOT / "docs" / "migration" / "scenario-diff-evidence.md"
)

# The four harness shell scripts this module drives, and the protocol stage each
# one is. They are SHELL, so a subprocess is the only way to reach them - which is
# also exactly how R-1 wants the compiled oracle reached: out of process.
SEED_SCRIPT: Final[Path] = HARNESS_DIR / "seed.sh"
RESET_SCRIPT: Final[Path] = HARNESS_DIR / "reset_db.sh"
RUN_COBOL_SCRIPT: Final[Path] = HARNESS_DIR / "run_cobol_scenario.sh"
RUN_PYTHON_SCRIPT: Final[Path] = HARNESS_DIR / "run_python_scenario.sh"

# ---------------------------------------------------------------------------
#  SECTION 2  -  THE ENVIRONMENT CONTRACT
#
#  Names only. The VALUES are resolved and validated by
#  harness/dump_tables.py's `connection_settings`, which is the single authority
#  and raises `ConnectionConfigError` with the authoritative message; this module
#  never re-implements that validation (R-4).
#
#  The database half derives from `03 RDB-Data.` [copybooks/wsfnctn.cob:L56-L62]:
#      05  DB-Schema   pic x(12)     05  DB-Host     pic x(32)
#      05  DB-UName    pic x(12)     05  DB-Socket   pic x(64)
#      05  DB-UPass    pic x(12)     05  DB-Port     pic x(5)
#  so ACAS_DB_USER and ACAS_DB_PASSWORD are each capped at TWELVE characters: a
#  longer value is silently truncated by the COBOL side while the Python side
#  sends it whole, and the two cycles would then authenticate differently.
#  harness/docker-compose.yml defines every variable below for the `gnucobol`
#  service.
# ---------------------------------------------------------------------------

ENV_DB_HOST: Final[str] = "ACAS_DB_HOST"
ENV_DB_PORT: Final[str] = "ACAS_DB_PORT"
ENV_DB_NAME: Final[str] = "ACAS_DB_NAME"
ENV_DB_USER: Final[str] = "ACAS_DB_USER"
ENV_DB_PASSWORD: Final[str] = "ACAS_DB_PASSWORD"
ENV_DB_SOCKET: Final[str] = "ACAS_DB_SOCKET"

# The writable areas. ACAS_REPO is the checkout, mounted READ-ONLY as
# `../:/repo:ro`; everything this module writes goes under ACAS_OUT.
ENV_REPO: Final[str] = "ACAS_REPO"
ENV_OUT: Final[str] = "ACAS_OUT"
ENV_DATA: Final[str] = "ACAS_DATA"
ENV_BUILD: Final[str] = "ACAS_BUILD"
ENV_BIN: Final[str] = "ACAS_BIN"

# `ACAS_LEDGERS` and `ACAS_BIN` must both be NON-BLANK or every compiled load
# program and every menu displays a message, waits on an ACCEPT and stops
# [copybooks/Proc-Get-Env-Set-Files.cob:L20-L28]. That is operator trap 3 in
# harness/docker-compose.yml, and it looks exactly like a hung harness.
ENV_LEDGERS: Final[str] = "ACAS_LEDGERS"

# harness/reset_db.sh GATE 2: target-scoped consent, which must equal exactly
# `DESTROY <schema>@<host>:<port>` for the resolved target. THIS MODULE NEVER
# FABRICATES IT. A fixture that computed the token for the very database it was
# about to destroy would remove the operator's affirmative act and leave the gate
# authorising nothing in particular, which is the failure mode the gate exists to
# prevent. It is read from the environment - harness/docker-compose.yml sets it
# for the `gnucobol` service - and when it is absent the scenario tiers SKIP with
# the exact token to export.
ENV_RESET_CONSENT: Final[str] = "ACAS_RESET_CONSENT"

# harness/reset_db.sh GATE 1: an administrative account DISTINCT from
# ACAS_DB_USER, because the application account the migrated cycle authenticates
# with must not also carry DROP on every table.
ENV_DB_ADMIN_USER: Final[str] = "ACAS_DB_ADMIN_USER"
ENV_DB_ADMIN_PASSWORD: Final[str] = "ACAS_DB_ADMIN_PASSWORD"

# OPT IN to aborting on a loader return code the frozen script TOLERATES - 1
# through 63, of which 16 is "error writing data to rdb"
# [common/masterLD.sh:L39]. UNSET, WHICH IS THE DEFAULT, applies the frozen
# `-gt 63` tolerance [common/masterLD.sh:L41]. This module PASSES THE VARIABLE
# THROUGH and never sets it in either direction: hard-coding strictness would
# override the frozen tolerance, and hard-coding tolerance would remove the
# operator's ability to bisect a seed (R-3, R-4).
ENV_SEED_STRICT: Final[str] = "ACAS_SEED_STRICT"

# The five variables `connection_settings` requires to be present and non-empty.
# ACAS_DB_SOCKET may be empty - that means connect over TCP - but the harness
# scripts require it to be DECLARED.
_REQUIRED_DB_ENV: Final[tuple[str, ...]] = (
    ENV_DB_HOST,
    ENV_DB_PORT,
    ENV_DB_NAME,
    ENV_DB_USER,
    ENV_DB_PASSWORD,
)

# ---------------------------------------------------------------------------
#  SECTION 3  -  THE RULE R-2 TYPE GATE
#
#  A type gate on the TEST HARNESS'S OWN PLUMBING, which is legitimate, and not a
#  validation of accounting data, which R-3 forbids. The frozen schema declares
#  zero FLOAT, DOUBLE or REAL columns anywhere - its numeric census is 167
#  DECIMAL, 151 INT, 116 TINYINT, 23 MEDIUMINT, 22 SMALLINT and 3 BIGINT - so a
#  float reaching a dump means the driver conversion was not pinned. That is
#  RAISED, never coerced: coercing it would silently change a posted figure.
#
#  On the arithmetic side the same rule is why CPython's decimal module is the only
#  numeric engine used. On this interpreter it is backed by the C libmpdec
#  implementation, where ROUND_DOWN truncates toward zero for BOTH signs - which is
#  what COBOL does on an un-ROUNDED store - and ROUND_HALF_UP ties away from zero,
#  which is what COBOL `ROUNDED` does. Nothing here reads or mutates the ambient
#  `decimal.getcontext()`: a fixture that changed the global context could alter a
#  posted figure in an unrelated test.
# ---------------------------------------------------------------------------


def assert_no_floating_point(value: object, *, where: str) -> None:
    """Assert no binary floating-point value appears anywhere in `value` (R-2).

    THE GUARD THIS FILE'S SPECIFICATION CALLS FOR, used by the diff helpers below.
    Named for the rule rather than for the type so that a search for the forbidden
    type itself never matches this module.

    Recurses mappings and sequences. Strings and bytes are leaves rather than
    sequences of leaves, so a long character column is not walked character by
    character.

    Args:
        value: The object to walk - a dump object, a row, or a single value.
        where: What is being checked, quoted verbatim in the failure so the
            finding is traceable to its source.

    Raises:
        TypeError: A `float` or a `complex` was found. The message names `where`
            and the offending value's type.
    """
    if isinstance(value, (float, complex)):
        raise TypeError(
            f"{where}: a {type(value).__name__} reached the comparison "
            f"protocol. Rule R-2 admits no binary floating-point value at any "
            f"point - not in computation, not in storage, not in transport - and "
            f"mysql/ACASDB.sql declares no FLOAT, DOUBLE or REAL column, so this "
            f"is a driver-configuration defect. It is raised rather than coerced, "
            f"because coercing it would silently change a posted figure."
        )
    if isinstance(value, (str, bytes, bytearray)):
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            assert_no_floating_point(item, where=f"{where}[{key!r}]")
        return
    if isinstance(value, Sequence):
        for index, item in enumerate(value):
            assert_no_floating_point(item, where=f"{where}[{index}]")


def assert_no_null(value: object, *, where: str) -> None:
    """Assert no JSON null appears anywhere in `value`.

    The frozen schema declares all 513 in-scope columns NOT NULL, so a null in a
    dump means the file is malformed. It is REPORTED LOUDLY and NEVER COALESCED
    (R-4): substituting a zero or an empty string would invent a value the
    database never held and would make a real finding compare equal.

    Args:
        value: The object to walk.
        where: What is being checked, quoted in the failure.

    Raises:
        ValueError: A `None` was found.
    """
    if value is None:
        raise ValueError(
            f"{where}: a JSON null reached the comparison protocol. All 513 "
            f"in-scope columns of mysql/ACASDB.sql are declared NOT NULL, so a "
            f"null means the dump is malformed. It is reported rather than "
            f"coalesced: a substituted default would make a real difference "
            f"compare equal (rule R-4)."
        )
    if isinstance(value, (str, bytes, bytearray)):
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            assert_no_null(item, where=f"{where}[{key!r}]")
        return
    if isinstance(value, Sequence):
        for index, item in enumerate(value):
            assert_no_null(item, where=f"{where}[{index}]")


def assert_exact_numeric(value: object, *, where: str) -> None:
    """Assert one scalar is an exact numeric or a string, never a float (R-2).

    The admitted types are exactly those `harness/dump_tables.py` produces: `int`
    for every integer width and `str` for a `char` column or a canonically
    rendered `DECIMAL`. `Decimal` is admitted too, for a value taken straight from
    a driver rather than from a dump file.

    NOTE ON `bool`: `isinstance(True, int)` is True in Python, so a boolean would
    otherwise pass an integer check silently. It is rejected explicitly, because no
    column of the frozen schema is boolean - the schema's 116 `tinyint` columns are
    integers - and a `True` standing in for `1` would compare equal while being a
    different type.

    Args:
        value: The scalar to check.
        where: What is being checked, quoted in the failure.

    Raises:
        TypeError: The value is a float, a bool, or any other unadmitted type.
    """
    assert_no_floating_point(value, where=where)
    if isinstance(value, bool):
        raise TypeError(
            f"{where}: a bool reached the comparison protocol. No column of "
            f"mysql/ACASDB.sql is boolean - its 116 tinyint columns are integers - "
            f"and because isinstance(True, int) is True in Python a boolean would "
            f"otherwise pass an integer check unnoticed."
        )
    if not isinstance(value, (int, str, Decimal)):
        raise TypeError(
            f"{where}: {type(value).__name__} is not a type any column of "
            f"mysql/ACASDB.sql can hold. harness/dump_tables.py renders every "
            f"integer width as int and both char and DECIMAL as str, so those "
            f"three plus decimal.Decimal are the whole admitted set (rule R-2)."
        )


# ---------------------------------------------------------------------------
#  SECTION 4  -  THE HARNESS MODULE LOADER  (rule R-1)
#
#  THE SINGLE MOST IMPORTANT MECHANICAL FACT IN THIS FILE: harness/ IS NOT A
#  PYTHON PACKAGE. It carries no __init__.py and must never gain one, and
#  pyproject.toml's [tool.setuptools] `packages` allow-list names only the seven
#  acas_posting packages plus the generated data directory. There is therefore
#  DELIBERATELY no import path from the shipped package to the compiled oracle.
#
#  A PACKAGE-STYLE IMPORT IS WRONG AND FAILS AT COLLECTION: naming `harness` as a
#  module and reaching a submodule through it cannot work, because the directory is
#  not a package. The three modules are loaded BY EXPLICIT FILE PATH instead, and
#  that is the only mechanism this module uses.
#
#  LOADING IS LAZY AND CHEAP. None of the three touches Docker, MariaDB or
#  GnuCOBOL at import: harness/normalize.py and harness/diff_states.py are pure,
#  and harness/dump_tables.py opens a connection only when `connect()` is CALLED.
#  Nothing below runs at conftest import time, which is what lets
#  `pytest -m arithmetic` succeed on a bare host.
#
#  NO sys.path MUTATION IS NEEDED, and none is performed. Verified across the three
#  files: not one imports a sibling harness module, so there is no sibling name to
#  resolve and no risk of shadowing a stdlib name.
# ---------------------------------------------------------------------------

# The three harness Python modules, by file name without the extension.
HARNESS_MODULE_NAMES: Final[tuple[str, str, str]] = (
    "dump_tables",
    "normalize",
    "diff_states",
)

# Loaded modules, memoised so repeated fixture use does not re-execute a
# 3,600-line module. A plain dict rather than functools.lru_cache, so that the
# cache is inspectable and so a partially executed module is never left in it.
_HARNESS_MODULE_CACHE: dict[str, ModuleType] = {}

# The sys.modules key each harness module is registered under. NAMESPACED, so that
# loading `normalize` cannot shadow a third-party or future stdlib module of the
# same name. Registration before `exec_module` is the documented recipe for
# importing a source file directly, and it is what makes the modules' frozen
# dataclasses resolvable by `__module__`.
_HARNESS_SYS_MODULES_PREFIX: Final[str] = "_acas_harness_"


def _load_harness_module(name: str) -> ModuleType:
    """Load one harness Python module by explicit file path (rule R-1).

    Args:
        name: One of `HARNESS_MODULE_NAMES`.

    Returns:
        The executed module, memoised for the life of the session.

    Raises:
        ValueError: `name` is not one of the three harness modules.
        FileNotFoundError: The file is absent. The message carries the full
            expected path and says plainly that the harness tree has not been
            created, because that is the whole diagnosis.
        ImportError: The file exists but could not be turned into a module.
    """
    if name not in HARNESS_MODULE_NAMES:
        raise ValueError(
            f"{name!r} is not a harness Python module. The three are "
            f"{', '.join(HARNESS_MODULE_NAMES)}, at harness/<name>.py."
        )

    cached = _HARNESS_MODULE_CACHE.get(name)
    if cached is not None:
        return cached

    path = HARNESS_DIR / f"{name}.py"
    if not path.is_file():
        raise FileNotFoundError(
            f"the harness module {name!r} was expected at {path} and is not "
            f"there, so that part of the oracle harness has not been created. It "
            f"is loaded by explicit file path because harness/ is deliberately "
            f"not a Python package (rule R-1); adding an __init__.py is not the "
            f"fix."
        )

    module_name = f"{_HARNESS_SYS_MODULES_PREFIX}{name}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(
            f"{path} exists but no import machinery could load it; "
            f"importlib.util.spec_from_file_location returned no usable spec."
        )

    module = importlib.util.module_from_spec(spec)
    # Registered BEFORE execution, and removed again if execution fails, so a
    # half-initialised module is never left visible to a later import.
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise

    _HARNESS_MODULE_CACHE[name] = module
    return module


def harness_dump_tables() -> ModuleType:
    """The `harness/dump_tables.py` module - protocol stages 3 and 7.

    Publishes `IN_SCOPE`, `OUT_OF_SCOPE`, `IN_SCOPE_TABLES`,
    `EXPECTED_TOTAL_COLUMNS`, `SIDES`, `DUMP_KEYS`, `table_spec`, `connect`,
    `connection_settings`, `dump_table`, `dump_tables`, `dump_path`, `write_dump`,
    `publish_dumps`, `scenario_tables`, `resolve_tables` and `main`.

    Returns:
        The loaded module.
    """
    return _load_harness_module("dump_tables")


def harness_normalize() -> ModuleType:
    """The `harness/normalize.py` module - protocol stage 4, and again after 7.

    Publishes `load_schema`, `schema_columns`, `column_type`, `normalize_dump`
    (pure), `normalize_tree`, `read_dump`, `write_dump`, `DATE_TEXT_COLUMNS`,
    `DATE_TEXT_EXCLUSIONS` and `main`.

    Returns:
        The loaded module.
    """
    return _load_harness_module("normalize")


def harness_diff_states() -> ModuleType:
    """The `harness/diff_states.py` module - protocol stage 8 (rule R-1).

    Loaded by explicit file path, like its two siblings, because harness/ is not a
    Python package. Its verdict is the pass condition of Agent Action Plan section
    0.8.5: "the diff must be empty".

    Publishes `TableDiff`, `TreeDiff` (both frozen, both with `is_empty`),
    `diff_table`, `diff_trees`, `render`, `write_report`, `EX_IDENTICAL`,
    `EX_DIFFERENT`, `EX_ERROR`, `LABEL_COBOL`, `LABEL_PYTHON`,
    `NORMALIZED_SUFFIX` and `main`.

    Returns:
        The loaded module.
    """
    return _load_harness_module("diff_states")


@dataclass(frozen=True)
class HarnessModules:
    """The three harness Python modules, loaded and ready (rule R-1).

    The three that implement stages 3, 4, 7 and 8 of the eight-stage parity protocol
    the canonical recipe in harness/docker-compose.yml publishes. Each is loaded by
    explicit file path, never imported as a package.

    Frozen because a fixture that could be re-pointed at a different module would
    let two tests in one session compare against two different definitions of the
    protocol.

    Attributes:
        dump_tables: `harness/dump_tables.py` - stages 3 and 7.
        normalize: `harness/normalize.py` - stage 4.
        diff_states: `harness/diff_states.py` - stage 8.
    """

    dump_tables: ModuleType
    normalize: ModuleType
    diff_states: ModuleType


def load_harness_modules() -> HarnessModules:
    """Load all three harness Python modules (rule R-1).

    Returns:
        The three, memoised.

    Raises:
        FileNotFoundError: One of the three is absent; the message names it.
    """
    return HarnessModules(
        dump_tables=harness_dump_tables(),
        normalize=harness_normalize(),
        diff_states=harness_diff_states(),
    )


def in_scope_tables() -> tuple[str, ...]:
    """The 22 in-scope table names, ascending.

    READ FROM `harness/dump_tables.py`'s `IN_SCOPE_TABLES` rather than restated
    here: the inventory, the single-column primary keys and the declared column
    counts have exactly one definition in this repository (rule R-4), and
    `assert_table_structure` re-checks every entry against a live
    `information_schema` on every dump so the map cannot silently drift.

    Returns:
        The table names, spelled exactly as mysql/ACASDB.sql spells them, hyphens
        included.
    """
    return tuple(harness_dump_tables().IN_SCOPE_TABLES)


def out_of_scope_tables() -> tuple[str, ...]:
    """The 11 out-of-scope table names, ascending.

    Agent Action Plan section 0.2.2 enumerates them as tables "all present in the
    frozen schema but never touched by the cycle"; 22 + 11 = 33, the schema's full
    `CREATE TABLE` count. Read from `harness/dump_tables.py`'s `OUT_OF_SCOPE`.

    Returns:
        The table names, ascending.
    """
    return tuple(sorted(harness_dump_tables().OUT_OF_SCOPE))


def frozen_schema_map() -> Mapping[str, Mapping[str, Any]]:
    """Parse `mysql/ACASDB.sql` into the column-type map (`{table: {column: ...}}`).

    Delegates to `harness/normalize.py`'s `load_schema`, which additionally asserts
    the frozen inventory - 33 `CREATE TABLE` statements, and agreement with
    `IN_SCOPE` on every column count, primary key and allow-listed width - so a
    modified frozen artifact is a hard failure rather than a quiet drift.

    THE FILE IS READ AND NEVER WRITTEN. Agent Action Plan section 0.8.1 makes any
    diff against it a defect in the migration.

    Returns:
        The column-type map, with 33 tables, the inner mapping in schema ordinal
        order.
    """
    return harness_normalize().load_schema(SCHEMA_SQL_PATH)



# ---------------------------------------------------------------------------
#  SECTION 5  -  THE PINNED CLOCK  (rule R-6)
#
#  TWO OBSERVABLES, AND ONLY TWO. Agent Action Plan section 0.1.1: every one of the
#  twelve in-scope posting programs contains ZERO clock reads - the date arrives
#  purely through linkage - and the single read in the whole call chain is in the
#  menu shell's date-service copybook [copybooks/Proc-ACAS-Mapser-RDB.cob:L72-L80].
#  So the controlled clock pins exactly these and nothing deeper:
#
#    1. THE TEXT DATE, `to-day pic x(10)` in DD/MM/CCYY form. It is the 3rd
#       parameter of the General-Ledger linkage shape and the 4th of the
#       Sales/Purchase shape. The IRS shape takes NEITHER `to-day` NOR the
#       calling-data block: [irs/irs030.cbl:L552-L554] is
#       `using IRS-System-Params, WS-System-Record, File-Defs`.
#    2. THE BINARY RUN DATE, declared `05  Run-Date        binary-long.` at
#       [copybooks/wssystem.cob:L67]. It is a real SYSTEM-REC column
#       (`RUN-DAT int(8) unsigned`) and is therefore VISIBLE IN A TABLE DUMP.
#
#  NOTHING MORE IS BUILT. There is no Clock protocol, no ABC, no
#  production-versus-test pair, no monkeypatch hook, no global singleton and no
#  default that resolves to "now" - the Agent Action Plan is explicit that the
#  controlled clock must not be over-engineered, and a fixture that could silently
#  fall back to the system time would make tests/determinism/ meaningless.
#
#  THE CONVERSION IS NOT REIMPLEMENTED HERE. acas_posting/clock.py owns it and
#  acas_posting/dates.py owns the `maps04` semantics beneath it; a second
#  implementation would be the divergence R-4 forbids.
# ---------------------------------------------------------------------------

# THE PROJECT-WIDE PINNED RUN DATE, as typed at the COBOL Date Entry screen and as
# passed to `--run-date` on the Python side. DD/MM/CCYY, ten characters, the form
# `to-day pic x(10)` carries.
PINNED_RUN_DATE_TEXT: Final[str] = "21/09/2025"

# The same date as `Run-Date binary-long` [copybooks/wssystem.cob:L67]. The epoch is
# 1600-12-31, which the maintainer flags at [common/maps04.cbl:L39-L41] as making
# the module "NOT usable within IRS as is"; `date(1600, 12, 31).toordinal()` is
# 584388, so day 1 is 1601-01-01 and the day number is `toordinal() - 584388`.
# Verified on this interpreter: date(2025, 9, 21) -> 155127.
PINNED_RUN_DATE_BINARY: Final[int] = 155127

# The pinned date as a calendar date, for a test that needs to reason about it in
# Python terms. Derived from the two constants above, never from a clock.
PINNED_RUN_DATE_CALENDAR: Final[date] = date(2025, 9, 21)

# The ordinal offset the epoch implies. Stated so a reader can check the arithmetic
# above without running anything; acas_posting/dates.py is the implementation.
COBOL_DATE_EPOCH: Final[date] = date(1600, 12, 31)

# `SYSTEM-REC.DATE-FORM` is `tinyint(1) unsigned`, declared `05  Date-Form pic 9.`
# with [copybooks/wssystem.cob:L129-L131] `88 Date-UK value 1` (dd/mm/yyyy),
# `88 Date-USA value 2` (mm/dd/yyyy) and `88 Date-Intl value 3` (yyyy/mm/dd). It
# selects THE DIGIT ORDER THE COBOL RUNNER MUST TYPE at the Date Entry screen,
# whereas acas_posting/cli/args.py fixes `RUN_DATE_FORMAT = "DD/MM/CCYY"`
# unconditionally. THAT LEXICAL ASYMMETRY IS DOCUMENTED AND DELIBERATE and is not
# "fixed" here: the two sides agree on the DATE, and only on how it is spelled at
# an input surface that the Python side does not have. A scenario declares the form
# it wants under the `date_form` key so the oracle types the right digits.
DATE_FORM_UK: Final[int] = 1
DATE_FORM_USA: Final[int] = 2
DATE_FORM_INTL: Final[int] = 3


def pinned_clock_from(run_date_text: str) -> acas_clock.PinnedRunDate:
    """Pin both observables from caller-supplied `to-day` text (rule R-6).

    A thin factory over `acas_posting.clock.pin_from_to_day`, so that
    tests/determinism/ and any scenario overriding the YAML date can build a second
    clock without duplicating logic.

    THE TEXT IS NOT PRE-VALIDATED AND A BAD DATE DOES NOT RAISE. `maps04` alone
    judges it, with its own six-part test [common/maps04.cbl:L140-L146] and its own
    calendar check [common/maps04.cbl:L153]. On rejection it falls through WITHOUT
    TOUCHING its output field [common/maps04.cbl:L146, L154], and the documented
    "Date errors returned as A-Bin equal zero" contract at
    [common/maps04.cbl:L163] holds only because callers pre-zero the field at
    [copybooks/Proc-ACAS-Mapser-RDB.cob:L78]. That is ANOMALY #16, and
    acas_posting/clock.py reproduces its masking mechanism, so a rejected date
    arrives here as `run_date == 0`. This helper does NOT "helpfully" raise on one:
    a test that wants the behaviour asserts `pin.run_date == 0` (rule R-4).

    AND THAT ZERO IS AN AMBIGUITY THIS HELPER DOES NOT SETTLE (rule R-6). Agent
    Action Plan section 0.6.8 lists the reject contract as the first of five
    questions the compiled program must arbitrate: the module falls through without
    touching its output field, its own remarks say errors return zero
    [common/maps04.cbl:L163], and the ONE caller proven to pre-zero it is the menu
    shell. What each in-scope caller actually observes is recorded in
    `AMBIGUITY_RESOLUTIONS_DOC`; a test asserting on a rejected date should cite that
    entry rather than treat the zero as settled here.

    Args:
        run_date_text: The date text, canonically DD/MM/CCYY. Wider than ten
            characters is truncated and shorter is space-padded, exactly as a COBOL
            alphanumeric `MOVE` into `PIC X(10)` does.

    Returns:
        The pinned pair - `to_day` and `run_date`.
    """
    return acas_clock.pin_from_to_day(run_date_text)


def pinned_clock_from_calendar(calendar_date: date) -> acas_clock.PinnedRunDate:
    """Pin both observables from an injected calendar date (rule R-6).

    A thin factory over `acas_posting.clock.pin_from_calendar_date`, which
    reproduces [copybooks/Proc-ACAS-Mapser-RDB.cob:L72-L80] with its one clock read
    replaced by this argument.

    Args:
        calendar_date: The run date to pin. INJECTED - there is no default and no
            fallback to the system clock.

    Returns:
        The pinned pair.
    """
    return acas_clock.pin_from_calendar_date(calendar_date)


def assert_pin_matches_project_default(pin: acas_clock.PinnedRunDate) -> None:
    """Assert a pinned pair is the project-wide pinned run date.

    A cheap guard that catches an epoch regression in `acas_posting/clock.py` or
    `acas_posting/dates.py` immediately, at the fixture rather than three tables
    into a diff, where a one-day shift in `SYSTEM-REC.RUN-DAT` would look like a
    posting difference.

    Args:
        pin: The pair to check.

    Raises:
        AssertionError: The text or the binary form is not the pinned value.
    """
    assert pin.to_day == PINNED_RUN_DATE_TEXT, (
        f"the pinned clock's text date is {pin.to_day!r}, expected "
        f"{PINNED_RUN_DATE_TEXT!r}. `to-day pic x(10)` is DD/MM/CCYY."
    )
    assert pin.run_date == PINNED_RUN_DATE_BINARY, (
        f"the pinned clock's binary Run-Date is {pin.run_date}, expected "
        f"{PINNED_RUN_DATE_BINARY}. `Run-Date binary-long` "
        f"[copybooks/wssystem.cob:L67] counts days from the 1600-12-31 epoch "
        f"[common/maps04.cbl:L39-L41], so a mismatch here is an epoch regression "
        f"in acas_posting/dates.py - and Run-Date is a SYSTEM-REC column, so it "
        f"would surface as a table difference rather than as an error."
    )



# ---------------------------------------------------------------------------
#  SECTION 6  -  THE CANONICAL OUTPUT LAYOUT, AND THE STACK SKIP GUARD
#
#  THE LAYOUT IS NOT INVENTED HERE. It is the one all three harness Python modules
#  and the committed Compose recipe already compose:
#
#      $ACAS_OUT/<scenario>/<side>/<TABLE>.json                side: cobol | python
#      $ACAS_OUT/<scenario>/<side>.normalized/<TABLE>.json
#      $ACAS_OUT/<scenario>/diff.txt
#      $ACAS_OUT/run-logs/<scenario>/{cobol.log,python.log,...}
#
#  <TABLE> is the schema name EXACTLY, hyphens included - `GLPOSTING-REC.json`.
#  Run logs live OUTSIDE the compared tree by design: a transcript written into
#  $ACAS_OUT/<scenario>/<side>/ would be diffed as though it were posted data. This
#  module writes nothing into a side directory but table dumps, and writes nothing
#  at all outside $ACAS_OUT (or a pytest `tmp_path`).
#
#  THE FREEZE, AND THE __pycache__ TRAP. $ACAS_REPO is mounted READ-ONLY as
#  `../:/repo:ro`, and the harness sets PYTHONDONTWRITEBYTECODE=1 and works from a
#  writable directory outside it, because Python bytecode and pytest's cache are
#  real files that would appear in `git status`. A fixture that tries to write into
#  the checkout FAILS THERE, and that failure is correct: the fixture is fixed, not
#  the mount.
# ---------------------------------------------------------------------------

# The two sides of the comparison. Restated as a module constant only for the skip
# messages and the path helpers below; `harness/dump_tables.py`'s `SIDES` and
# `harness/diff_states.py`'s `LABEL_COBOL`/`LABEL_PYTHON` are the authority, and
# `assert_side` checks against the loaded module rather than against this tuple.
SIDE_COBOL: Final[str] = "cobol"
SIDE_PYTHON: Final[str] = "python"

# The suffix `harness/normalize.py` appends to a side directory, and one of the two
# `harness/diff_states.py` accepts as proof that a tree has been normalised.
NORMALIZED_SUFFIX: Final[str] = ".normalized"

# The per-scenario report `harness/diff_states.py` writes, and the subdirectory the
# run transcripts live in. On a PASS a ZERO-BYTE diff.txt is written, deliberately:
# an existing empty file says "compared, and identical" while an absent file says
# nothing at all, and the evidence document needs to tell those apart.
DIFF_FILENAME: Final[str] = "diff.txt"
RUN_LOG_SUBDIR: Final[str] = "run-logs"


@dataclass(frozen=True)
class ScenarioPaths:
    """Every path one scenario's evidence occupies, composed from `$ACAS_OUT`.

    The layout is the one all three harness Python modules and the canonical recipe
    in harness/docker-compose.yml already compose - see the section comment above -
    and it holds the evidence Agent Action Plan section 0.8.5 requires per scenario.

    Frozen, and derived rather than configurable: two tests that composed the layout
    differently would produce evidence that could not be compared.

    Attributes:
        out_root: `$ACAS_OUT`, the writable output area.
        scenario: The scenario name, a plain directory name.
        cobol_dump: The oracle's raw dump directory.
        python_dump: The migrated cycle's raw dump directory.
        cobol_normalized: The oracle's normalised tree - a diff input.
        python_normalized: The migrated cycle's normalised tree - the other input.
        diff_report: `diff.txt`; zero bytes on a pass.
        run_logs: The transcript directory, OUTSIDE the compared tree.
    """

    out_root: Path
    scenario: str
    cobol_dump: Path
    python_dump: Path
    cobol_normalized: Path
    python_normalized: Path
    diff_report: Path
    run_logs: Path

    def dump_dir(self, side: str) -> Path:
        """The raw dump directory for one side.

        Args:
            side: `cobol` or `python`.

        Returns:
            The directory.

        Raises:
            ValueError: `side` is neither.
        """
        assert_side(side)
        return self.cobol_dump if side == SIDE_COBOL else self.python_dump

    def normalized_dir(self, side: str) -> Path:
        """The normalised tree for one side.

        Args:
            side: `cobol` or `python`.

        Returns:
            The directory.

        Raises:
            ValueError: `side` is neither.
        """
        assert_side(side)
        return (
            self.cobol_normalized if side == SIDE_COBOL else self.python_normalized
        )


def assert_side(side: str) -> None:
    """Assert `side` is one of the two the protocol has.

    Checked against `harness/dump_tables.py`'s `SIDES` rather than against a local
    list, so there is one definition of the vocabulary (rule R-4).

    Args:
        side: The candidate.

    Raises:
        ValueError: It is not `cobol` or `python`.
    """
    sides = tuple(harness_dump_tables().SIDES)
    if side not in sides:
        raise ValueError(
            f"side must be one of {', '.join(sides)}; got {side!r}. The two sides "
            f"of the comparison are the compiled COBOL oracle and the migrated "
            f"Python cycle, and the side is recorded in the PATH, never in a file."
        )


def assert_scenario_name(scenario: str) -> None:
    """Assert `scenario` is a plain directory name and not a path.

    The same test `harness/dump_tables.py`'s `dump_path` makes, applied before a
    path is composed so the failure names the scenario rather than a directory.

    Args:
        scenario: The candidate.

    Raises:
        ValueError: It is empty, is `.` or `..`, or carries a path separator.
    """
    if not scenario or scenario in {".", ".."} or (set(scenario) & set("/\\")):
        raise ValueError(
            f"scenario must be a plain directory name, not a path; got "
            f"{scenario!r}. It names a scenario such as clean_batch_gl."
        )


def output_root(env: Mapping[str, str] | None = None) -> Path:
    """Resolve `$ACAS_OUT`, the one writable area this module writes into.

    Args:
        env: The environment to read; `os.environ` when omitted.

    Returns:
        The output root, as an absolute path.

    Raises:
        RuntimeError: `ACAS_OUT` is unset or empty. It is not defaulted to a
            temporary directory, because evidence written somewhere the operator did
            not name is evidence nobody can find (rule R-6).
    """
    source: Mapping[str, str] = os.environ if env is None else env
    value = (source.get(ENV_OUT) or "").strip()
    if not value:
        raise RuntimeError(
            f"{ENV_OUT} is not set, so there is nowhere to write the scenario "
            f"evidence. harness/docker-compose.yml sets it to /out for the "
            f"gnucobol service, backed by a named volume. It is deliberately not "
            f"defaulted: the eight-stage protocol's output IS the evidence, and "
            f"evidence written to an unnamed location cannot be cited."
        )
    return Path(value).resolve()


def scenario_paths(
    scenario: str, *, out_root: Path | str | None = None
) -> ScenarioPaths:
    """Compose every path one scenario's evidence occupies.

    Args:
        scenario: The scenario name, one of `SCENARIOS`.
        out_root: The output root; `$ACAS_OUT` when omitted.

    Returns:
        The composed paths. NOTHING IS CREATED - the harness stages create their own
        directories, with their own restrictive modes.

    Raises:
        ValueError: `scenario` is not a plain directory name.
        RuntimeError: `out_root` was omitted and `ACAS_OUT` is unset.
    """
    assert_scenario_name(scenario)
    root = output_root() if out_root is None else Path(out_root).resolve()
    base = root / scenario
    return ScenarioPaths(
        out_root=root,
        scenario=scenario,
        cobol_dump=base / SIDE_COBOL,
        python_dump=base / SIDE_PYTHON,
        cobol_normalized=base / f"{SIDE_COBOL}{NORMALIZED_SUFFIX}",
        python_normalized=base / f"{SIDE_PYTHON}{NORMALIZED_SUFFIX}",
        diff_report=base / DIFF_FILENAME,
        run_logs=root / RUN_LOG_SUBDIR / scenario,
    )


@dataclass(frozen=True)
class StackStatus:
    """Whether the harness Compose stack and its environment are usable.

    An unusable stack is a SKIP and never an error, which is what keeps the
    infrastructure-free arithmetic tier of Agent Action Plan section 0.7.2 R-1
    runnable on a bare host: "tests/arithmetic/* touch neither COBOL nor a database".

    Attributes:
        available: True when every precondition the oracle tiers need is met.
        reason: A precise, multi-line explanation when it is not; `None` when it is.
        missing: The specific preconditions that failed, for a test that wants to
            assert on one of them rather than read prose.
    """

    available: bool
    reason: str | None
    missing: tuple[str, ...]


# Computed ONCE per session, lazily, because the probe opens a real connection.
# A plain module global is sufficient and correct: execution is strictly sequential
# (rule R-3), so there is no race to guard.
_STACK_STATUS: StackStatus | None = None


def _probe_stack() -> StackStatus:
    """Check every precondition the scenario and determinism tiers need.

    ORDERED CHEAPEST FIRST, and every failing precondition is collected rather than
    only the first, so one skip message tells the operator everything that is
    missing instead of one thing at a time.

    Returns:
        The status. Never raises: an unusable stack is a SKIP, not an error, which
        is what lets `pytest -m arithmetic` succeed on a bare host.
    """
    missing: list[str] = []
    detail: list[str] = []

    # 1. The harness scripts. Cheapest of all, and the one failure a fresh checkout
    #    is most likely to hit: harness/run_python_scenario.sh is a planned
    #    deliverable (Agent Action Plan section 0.4.1.7) that arrives with the
    #    Python cycle it drives, and harness/docker-compose.yml says so in the
    #    canonical recipe itself.
    for script in (
        SEED_SCRIPT,
        RESET_SCRIPT,
        RUN_COBOL_SCRIPT,
        RUN_PYTHON_SCRIPT,
    ):
        if not script.is_file():
            missing.append(f"script:{script.name}")
            detail.append(f"  {script} is absent")
        elif not os.access(script, os.X_OK):
            missing.append(f"executable:{script.name}")
            detail.append(f"  {script} is not executable")

    # 2. The scenario definitions.
    if not SCENARIO_DIR.is_dir():
        missing.append("scenarios")
        detail.append(
            f"  {SCENARIO_DIR} is absent, so no scenario can be read; the eight "
            f"definitions bound every comparison"
        )

    # 3. The writable output area.
    try:
        root = output_root()
    except RuntimeError as exc:
        missing.append(f"env:{ENV_OUT}")
        detail.append(f"  {exc}")
    else:
        if not root.is_dir():
            missing.append(f"dir:{ENV_OUT}")
            detail.append(f"  {ENV_OUT} names {root}, which is not a directory")
        elif not os.access(root, os.W_OK):
            missing.append(f"writable:{ENV_OUT}")
            detail.append(f"  {ENV_OUT} names {root}, which is not writable")

    # 4. The non-database environment the compiled load programs and menus need.
    #    ACAS_LEDGERS and ACAS_BIN must be NON-BLANK or every one of them displays a
    #    message, waits on an ACCEPT and stops
    #    [copybooks/Proc-Get-Env-Set-Files.cob:L20-L28] - operator trap 3, which
    #    looks exactly like a hung harness.
    for name in (ENV_REPO, ENV_DATA, ENV_BIN, ENV_LEDGERS):
        if not (os.environ.get(name) or "").strip():
            missing.append(f"env:{name}")
            detail.append(f"  {name} is unset or blank")

    # 5. harness/reset_db.sh's three destructive gates. NOT FABRICATED HERE - see
    #    ENV_RESET_CONSENT. The expected token is quoted in the message so the
    #    operator can copy it, which is the whole point of a target-scoped gate.
    for name in (ENV_DB_ADMIN_USER, ENV_DB_ADMIN_PASSWORD):
        if not (os.environ.get(name) or "").strip():
            missing.append(f"env:{name}")
            detail.append(
                f"  {name} is unset; harness/reset_db.sh GATE 1 requires an "
                f"administrative account distinct from {ENV_DB_USER}"
            )

    # 6. The database environment, resolved by the single authority.
    settings = None
    try:
        settings = harness_dump_tables().connection_settings(os.environ)
    except FileNotFoundError as exc:
        missing.append("script:dump_tables.py")
        detail.append(f"  {exc}")
    except Exception as exc:  # noqa: BLE001 - any resolution failure is a skip
        missing.append("env:ACAS_DB_*")
        detail.append(f"  {exc}")

    if settings is not None:
        expected_consent = reset_consent_token(settings)
        declared_consent = (os.environ.get(ENV_RESET_CONSENT) or "").strip()
        if declared_consent != expected_consent:
            shown = repr(declared_consent) if declared_consent else "unset"
            missing.append(f"env:{ENV_RESET_CONSENT}")
            detail.append(
                f"  {ENV_RESET_CONSENT} must equal exactly "
                f"{expected_consent!r} for this target (harness/reset_db.sh "
                f"GATE 2); it is {shown}. This module never fabricates it: a "
                f"computed token would remove the operator's affirmative act and "
                f"leave the gate authorising nothing in particular"
            )

        # 7. The server itself, and the AAP-mandated autocommit mode. One
        #    connection, opened once per session (rule R-3: no pool, no thread).
        try:
            with harness_dump_tables().connect(settings) as connection:
                assert_autocommit_off(connection)
        except Exception as exc:  # noqa: BLE001 - unreachable server is a skip
            missing.append("database")
            detail.append(f"  {type(exc).__name__}: {exc}")

    if not missing:
        return StackStatus(available=True, reason=None, missing=())

    return StackStatus(
        available=False,
        reason=(
            "the harness Compose stack is not usable from this process, so the "
            "oracle tiers cannot run:\n"
            + "\n".join(detail)
            + "\n\nBring the stack up and run inside it:\n"
            "  docker compose -f harness/docker-compose.yml up -d gnucobol\n"
            "  docker compose -f harness/docker-compose.yml exec gnucobol bash\n"
            "The arithmetic tier needs none of this: `pytest -m arithmetic` "
            "requires only data_dictionary/acas_posting_dictionary.json on disk."
        ),
        missing=tuple(missing),
    )


def stack_status() -> StackStatus:
    """The stack status, probed once per session.

    Returns:
        The memoised status. Never raises.
    """
    global _STACK_STATUS
    if _STACK_STATUS is None:
        _STACK_STATUS = _probe_stack()
    return _STACK_STATUS


def requires_stack() -> None:
    """Skip the calling test unless the harness stack is usable.

    A SKIP AND NOT A HARD FAILURE, deliberately: it is what lets
    `pytest -m arithmetic` succeed on a host with no Docker, no MariaDB and no
    GnuCOBOL, which is the direct test of the three-tier design. The reason names
    every missing precondition, so an operator is not told one thing at a time.

    Raises:
        Skipped: pytest's own skip exception, when a precondition is missing.
    """
    status = stack_status()
    if not status.available:
        pytest.skip(status.reason or "the harness Compose stack is not usable")


def reset_consent_token(settings: Any) -> str:
    """Build the exact consent token `harness/reset_db.sh` GATE 2 demands.

    The token is target-scoped by design - `DESTROY <schema>@<host>:<port>` - so
    that a reset cannot be aimed at another database by accident. It is GATE 2 of
    the three `[harness/reset_db.sh]` asserts before it opens a connection, and
    `[harness/docker-compose.yml]` sets it for the `gnucobol` service. Stage 5 of the
    protocol cannot run without it, which is why the absence of a matching token is
    one of the preconditions `stack_status` reports (rule R-3: this module emits no
    DDL of its own, so the reset is the only thing that touches the schema).

    THIS FUNCTION EXISTS SO THE SKIP MESSAGE CAN QUOTE THE TOKEN, NOT SO A FIXTURE
    CAN SUPPLY IT. Nothing in this module passes the value to `harness/reset_db.sh`
    or writes it into the environment; the reset stage reads `$ACAS_RESET_CONSENT`,
    which the operator (or harness/docker-compose.yml) sets.

    Args:
        settings: A `harness/dump_tables.py` `ConnectionSettings`.

    Returns:
        The token for that target.
    """
    return f"DESTROY {settings.database}@{settings.host}:{settings.port}"



# ---------------------------------------------------------------------------
#  SECTION 7  -  SCENARIO DEFINITIONS AND THE OPERATION VOCABULARY
# ---------------------------------------------------------------------------

# THE EIGHT SCENARIOS, one per tests/scenarios/test_*.py, each at
# harness/scenarios/<name>.yaml. Agent Action Plan section 0.8.5 mandates the set,
# expanding "clean batch post per ledger" into four cases because the four ledgers
# exercise materially different code paths.
#
# `control_total_mismatch` IS GENERAL-LEDGER-SPECIFIC. Agent Action Plan section
# 0.6.4: Sales and Purchase batches "balance by construction ... there is no
# meaningful way to construct an unbalanced sales batch". There is deliberately no
# SL or PL variant, and no helper here implies one is possible.
SCENARIOS: Final[tuple[str, ...]] = (
    "clean_batch_gl",
    "clean_batch_sl",
    "clean_batch_pl",
    "clean_batch_irs",
    "mixed_accepted_rejected",
    "period_end_totals",
    "control_total_mismatch",
    "empty_batch",
)

# THE SEVEN OPERATIONS, identical in both runners, mapped to the Python module and
# to the COBOL menu paragraph each one drives. Transcribed from the operation map
# `harness/run_cobol_scenario.sh` publishes, which derives each menu key from the
# menu's own dispatch rule rather than guessing it: `letters-upper` is "ABC..Z"
# [general/general.cbl:L271], a SEARCH sets `z` to the matching subscript
# [general/general.cbl:L603-L608] and `go to load01 load02 ... depending on z`
# dispatches [general/general.cbl:L699-L704], so the Nth letter selects loadNN.
#
# `sl_invoice_post` IS load07, NOT load08. [sales/sales.cbl:L756] carries
# `*> Sales trans posting`; `load08.` at [sales/sales.cbl:L770] dispatches the
# OUT-OF-SCOPE sl080 (Payment Input). An occurrence of load08 against Sales
# anywhere is an error and is not propagated.
OPERATIONS: Final[Mapping[str, tuple[str, str, str, str]]] = {
    # operation: (subsystem, menu key, menu paragraph, locator)
    "gl_post_cycle": ("general", "H", "load08", "general/general.cbl:L805-L815"),
    "gl_end_of_cycle": ("general", "I", "load09", "general/general.cbl:L817-L821"),
    "sl_invoice_post": ("sales", "G", "load07", "sales/sales.cbl:L756-L768"),
    "sl_cash_post": ("sales", "K", "load11", "sales/sales.cbl:L792-L796"),
    "pl_order_post": ("purchase", "H", "load08", "purchase/purchase.cbl:L752-L762"),
    "pl_payment_post": (
        "purchase",
        "L",
        "load12",
        "purchase/purchase.cbl:L786-L790",
    ),
    "irs_post": ("irs", "4", "irs030-dispatch", "irs/irs030.cbl:L666-L672"),
}

# The Python module each operation dispatches, for a test that wants to assert the
# program-to-module traceability of Agent Action Plan section 0.7.2 R-5 directly.
OPERATION_MODULES: Final[Mapping[str, str]] = {
    "gl_post_cycle": "acas_posting.cli.gl_post_cycle",
    "gl_end_of_cycle": "acas_posting.cli.gl_end_of_cycle",
    "sl_invoice_post": "acas_posting.cli.sl_invoice_post",
    "sl_cash_post": "acas_posting.cli.sl_cash_post",
    "pl_order_post": "acas_posting.cli.pl_order_post",
    "pl_payment_post": "acas_posting.cli.pl_payment_post",
    "irs_post": "acas_posting.cli.irs_post",
}

# EXIT STATUSES ARE BEHAVIOURAL DATA, NOT PLUMBING NOISE. Only THREE in-scope
# programs ever set `WS-Term-Code`:
#     gl070 -> 5   [general/gl070.cbl:L289]     an open batch aborts the cycle
#     sl055 -> 8   [sales/sl055.cbl:L344]       the extract file is missing
#     pl055 -> 8   [purchase/pl055.cbl:L286]    the same, on the Purchase side
# and `acas_posting/cli/args.py`'s `exit_status_for(term_code)` returns 0 for 0 and
# THE TERM CODE ITSELF otherwise. So a GL open-batch abort surfaces as exit 5 and
# an SL or PL missing-extract-file abort as exit 8. `irs_post` has no
# `WS-Term-Code` at all and returns 0.
#
# The abort GATES that consume those codes are three different shapes, and the
# asymmetry is the specification, not an oversight to harmonise:
#     General   `if ws-term-code = 5 / go to display-menu`
#               [general/general.cbl:L810-L811]      - gl071 and gl072 never run
#     Sales     `if ws-term-code not = zero`, TWICE
#               [sales/sales.cbl:L761-L762, L765-L766]
#     Purchase  NONE - the gate is commented out
#               [purchase/purchase.cbl:L755-L758]
#     IRS       NONE, and no dispatch wrapper at all  [irs/irs.cbl:L666-L672]
TERM_CODES: Final[Mapping[str, tuple[int, ...]]] = {
    "gl_post_cycle": (5,),
    "gl_end_of_cycle": (),
    "sl_invoice_post": (8,),
    "sl_cash_post": (),
    "pl_order_post": (8,),
    "pl_payment_post": (),
    "irs_post": (),
}

# The three dispositions a stage's exit status can have. They are kept DISTINCT
# because conflating them is the single worst bug available in this tree: a run that
# aborted behaviourally still leaves evidence to compare, whereas a runner that was
# handed a bad command line leaves none.
DISPOSITION_SUCCESS: Final[str] = "success"
DISPOSITION_BEHAVIOURAL: Final[str] = "behavioural-difference"
DISPOSITION_HARNESS_FAULT: Final[str] = "harness-fault"

# `argparse` exits 2 on a usage error. In this family that means THE RUNNER BUILT A
# BAD COMMAND LINE - a harness fault - and never a behavioural difference. No
# in-scope program sets term code 2 and no harness script uses exit 2, so the code
# is unambiguous.
ARGPARSE_USAGE_EXIT: Final[int] = 2

# Each harness script's OWN documented exit codes, transcribed from the `readonly
# EX_*` block at the head of each file. A code in one of these bands is the script
# reporting a precondition, a database problem or a missing artifact - a harness
# fault - and is never a term code.
SEED_FAULT_CODES: Final[frozenset[int]] = frozenset({70, 71, 72, 73, 74, 75})
RESET_FAULT_CODES: Final[frozenset[int]] = frozenset(
    {80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91}
)
RUN_COBOL_FAULT_CODES: Final[frozenset[int]] = frozenset(
    {70, 71, 72, 73, 74, 75, 76, 77, 78, 79}
)

# The frozen load programs' documented return codes, from
# [common/masterLD.sh:L37-L39] verbatim, each traced to its site in
# common/glbatchLD.cbl. Codes ABOVE 63 abort the load [common/masterLD.sh:L41].
LOADER_RETURN_CODES: Final[Mapping[int, str]] = {
    16: (
        "error writing data to the RDB [common/masterLD.sh:L39] "
        "[common/glbatchLD.cbl:L445]"
    ),
    64: (
        "RDB not set up - RDBMS-DB-Name is spaces, or the system record says "
        "Cobol files only [common/masterLD.sh:L38] [common/glbatchLD.cbl:L290]"
    ),
    128: (
        "params not set up - the loader could not open or read the system file "
        "[common/masterLD.sh:L37] [common/glbatchLD.cbl:L223,L233]"
    ),
}

# The threshold the frozen script tests against, `if [ $rc -gt 63 ]`
# [common/masterLD.sh:L56,L65,L74]. ANOMALY, PRESERVED: `dfltLD` alone is tested
# with the stricter `if [ $rc != 0 ]` at [common/masterLD.sh:L83] while the other
# three system-block loaders use `-gt 63`. harness/seed.sh reproduces the asymmetry
# rather than harmonising it (rule R-4), and nothing here overrides it.
LOADER_ABORT_THRESHOLD: Final[int] = 63
LOADER_STRICT_LOADERS: Final[tuple[str, ...]] = ("dfltLD",)

# The scenario keys the harness stages actually read. Listed so a helper can assert
# a definition carries what it will be asked for, WITHOUT interpreting any of it:
# reading a scenario's declared contents and judging them would be exactly the added
# validation rule R-3 forbids, and it is why harness/seed.sh accepts a scenario file
# without parsing anything but its seed-file list.
#
#   run_date_text         the pinned date, exactly as typed, e.g. 21/09/2025
#   run_date_binary       the expected SYSTEM-REC.RUN-DAT after Date Entry
#   date_form             1 UK dd/mm/yyyy, 2 USA mm/dd/yyyy, 3 yyyy/mm/dd
#   irs_instead           the three-state fan-out switch - see IRS_INSTEAD_* below
#   operation             one of the seven; `subsystem` is derived from it
#   affected_tables       the list that BOUNDS the comparison
#   seed_files            the flat files harness/seed.sh stages; system.dat MUST be
#                         among them, because the frozen order seeds the system
#                         block first and unconditionally
#                         [common/masterLD.sh:L50-L88] and it is what carries
#                         Run-Date [copybooks/wssystem.cob:L67] and the fan-out
#                         switch [copybooks/wssystem.cob:L179-L181]
#   irs_clear_postings    "Y" or "N"; REQUIRED for irs_post - see below
#   gl080_proceed         "Y" proceeds, "A" aborts; default "Y"
#   payment_post_confirm  "YES" or "NO"; required for sl_cash_post and
#                         pl_payment_post, neither of whose prompts has a default
SCENARIO_KEY_RUN_DATE_TEXT: Final[str] = "run_date_text"
SCENARIO_KEY_RUN_DATE_BINARY: Final[str] = "run_date_binary"
SCENARIO_KEY_DATE_FORM: Final[str] = "date_form"
SCENARIO_KEY_IRS_INSTEAD: Final[str] = "irs_instead"
SCENARIO_KEY_OPERATION: Final[str] = "operation"
SCENARIO_KEY_SUBSYSTEM: Final[str] = "subsystem"
SCENARIO_KEY_SEED_FILES: Final[str] = "seed_files"
SCENARIO_KEY_IRS_CLEAR_POSTINGS: Final[str] = "irs_clear_postings"

# BOTH SPELLINGS ARE ACCEPTED, and exactly one may be present - the same rule
# harness/dump_tables.py's `scenario_tables` and harness/diff_states.py's apply.
SCENARIO_KEY_AFFECTED_TABLES: Final[tuple[str, str]] = (
    "affected_tables",
    "affected-tables",
)

# THE IRS FAN-OUT SWITCH, [copybooks/wssystem.cob:L179-L181] verbatim:
#     179       05  IRS-Instead     pic x.
#     180           88  IRS-Used                   value "Y".
#     181           88  IRS-Both-Used              value "B".   *> 26/11/16
# Column `IRS-INSTEAD char(1)`. THREE states, and the third has NO CONDITION NAME AT
# ALL - both predicates are simply False for a space, which is General Ledger only.
# Agent Action Plan section 0.6.4: "leaving it at a default would make the
# affected-table list ambiguous", so every scenario pins it explicitly. A YAML space
# or empty value maps to the CLI token "N" while the column still stores a space,
# and normalize.py's job 1 trims that to the empty string on BOTH sides - correct,
# because it is applied identically.
IRS_INSTEAD_GL_ONLY: Final[str] = " "
IRS_INSTEAD_IRS_USED: Final[str] = "Y"
IRS_INSTEAD_BOTH_USED: Final[str] = "B"
IRS_INSTEAD_STATES: Final[tuple[str, str, str]] = (
    IRS_INSTEAD_GL_ONLY,
    IRS_INSTEAD_IRS_USED,
    IRS_INSTEAD_BOTH_USED,
)

# THE CLEAR-POSTING-FILE ANSWER, which every IRS scenario must pin, and why it is an
# INPUT rather than decoration. [irs/irs030.cbl:L1715-L1719]: despite the `[Y]` hint
# in the prompt, `if WS-Reply not = "Y" and not = "N" / go to EOJ-q1` means AN EMPTY
# REPLY LOOPS FOREVER. Answering "Y" performs `acas008-Open-Output`
# [irs/irs030.cbl:L1720-L1724], and for this handler `fn-Open` with `fn-output` sets
# `fn-delete-all` [common/acas008.cbl:L313-L319], which DELETES EVERY ROW of
# PSIRSPOST-REC. So the answer changes table state, and any IRS scenario must both
# pin it and list PSIRSPOST-REC among its affected tables. The trailing accept at
# [irs/irs030.cbl:L1725-L1726] is pure acknowledgement and is dropped on the Python
# side.
#
# That the clear works AT ALL is a deliberate special case ahead of a guard: the same
# handler refuses four of its published verbs UNCONDITIONALLY at entry - read-indexed,
# rewrite, start and delete, each answered with `WE-Error 988` and `fs-reply 99`
# [common/acas008.cbl:L299-L307] - because the underlying file is sequential. The
# open-output special case is tested BEFORE that block, which is why this one path
# reaches the delete-all. Both behaviours are reproduced, neither is fixed (rule R-4).
IRS_CLEAR_POSTINGS_YES: Final[str] = "Y"
IRS_CLEAR_POSTINGS_NO: Final[str] = "N"
IRS_POSTING_TRANSFER_TABLE: Final[str] = "PSIRSPOST-REC"

# THE SL-AUTOGEN DETERMINISM LANDMINE. Both runners assert after a run that these
# four remain EMPTY: [sales/sales.cbl:L759] dispatches sl830 before sl055 on the
# COBOL side, the sl800 to sl830 autogen series is explicitly out of scope (Agent
# Action Plan section 0.2.2), and acas_posting/cli/sl_invoice_post.py dispatches only
# sl055 then sl060. The runners own the authoritative assertion; the helper below is
# the in-process equivalent for a test that wants to make it directly.
AUTOGEN_TABLES: Final[tuple[str, ...]] = (
    "SAAUTOGEN-REC",
    "SAAUTOGEN-LINES-REC",
    "PUAUTOGEN-REC",
    "PUAUTOGEN-LINES-REC",
)


def assert_operation(operation: str) -> None:
    """Assert `operation` is one of the seven the two runners share.

    Args:
        operation: The candidate.

    Raises:
        ValueError: It is not one of the seven. The message lists them, because the
            set is identical in `harness/run_cobol_scenario.sh` and
            `harness/run_python_scenario.sh` so that the two runners stay trivially
            comparable.
    """
    if operation not in OPERATIONS:
        raise ValueError(
            f"unknown operation {operation!r}. The seven are "
            f"{', '.join(OPERATIONS)}, and the set is identical in both runners."
        )


def scenario_file(scenario: str) -> Path:
    """The path of one scenario's definition.

    Args:
        scenario: The scenario name, normally one of `SCENARIOS`.

    Returns:
        `harness/scenarios/<scenario>.yaml`. NOT checked for existence here -
        `scenario_definition` reports that, with the diagnosis.

    Raises:
        ValueError: `scenario` is not a plain directory name.
    """
    assert_scenario_name(scenario)
    return SCENARIO_DIR / f"{scenario}.yaml"


def scenario_definition(scenario: str) -> Mapping[str, Any]:
    """Load one scenario definition (Agent Action Plan section 0.4.1.7).

    Read with `yaml.safe_load`, NEVER `yaml.load`: the loader must not be able to
    construct arbitrary Python objects from a data file.

    ONLY THE KEYS THE HELPERS CONSUME ARE CHECKED FOR PRESENCE, and NOTHING IS
    INTERPRETED. No semantic validation is added on top of the harness's own,
    because interpreting a scenario's declared contents and judging them would be
    exactly the added validation rule R-3 forbids.

    Args:
        scenario: The scenario name.

    Returns:
        The parsed mapping, exactly as the file declares it.

    Raises:
        FileNotFoundError: The definition is absent; the message names the path.
        ValueError: The file is not a YAML mapping, or carries neither spelling of
            the affected-table key or both.
    """
    import yaml  # noqa: PLC0415 - lazy, so the arithmetic tier imports without it

    path = scenario_file(scenario)
    if not path.is_file():
        raise FileNotFoundError(
            f"the scenario definition {scenario!r} was expected at {path} and is "
            f"not there. The eight definitions - {', '.join(SCENARIOS)} - are an "
            f"Agent Action Plan section 0.4.1.7 deliverable, and every comparison "
            f"is bounded by one: an unbounded dump is refused rather than "
            f"defaulted."
        )

    parsed = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(parsed, Mapping):
        raise ValueError(
            f"{path}: a scenario definition must be a YAML mapping; parsed as "
            f"{type(parsed).__name__}."
        )

    present = [key for key in SCENARIO_KEY_AFFECTED_TABLES if key in parsed]
    if len(present) != 1:
        spelt = " or ".join(repr(key) for key in SCENARIO_KEY_AFFECTED_TABLES)
        raise ValueError(
            f"{path}: a scenario must declare exactly one of {spelt} - the "
            f"affected-table list that BOUNDS the comparison; found "
            f"{len(present)}. Bounding is done by this list and never by the "
            f"differ, which has no ignore-list and no tolerance."
        )
    return parsed


def scenario_affected_tables(scenario: str) -> tuple[str, ...]:
    """One scenario's affected-table list, in the order it declares them.

    THIS IS HOW A COMPARISON IS BOUNDED, and the only way. Two structural
    asymmetries exist between the two sides and neither is a migration defect:

      1. The menu shell's exit path runs `overrewrite`, persisting SYSTEM-REC
         (key 1), SYSDEFLT-REC (key 2) and SYSTOT-REC (key 4)
         [general/general.cbl:L656-L691], and `load000` does it on EVERY call. The
         Python command line has no menu and never does this.
      2. sl830 runs only on the COBOL side [sales/sales.cbl:L759].

    So comparing those tables in a scenario that does not affect them reports a
    FALSE FAILURE. THE RESOLUTION IS TO BOUND, NEVER TO IGNORE: there is no
    ignore-list, no tolerance-list and no "known difference" allowance anywhere in
    the diff path. Note that SYSTOT-REC IS genuinely in scope for
    `period_end_totals` - Agent Action Plan section 0.6.4 names nine period-total
    write sites, "the sole writers of the totals record" - so it is never blanket
    excluded.

    Delegates the reading and the in-scope check to `harness/dump_tables.py`'s
    `scenario_tables`, so the list is validated exactly once (rule R-4).

    Args:
        scenario: The scenario name.

    Returns:
        The table names, in the scenario's own order.

    Raises:
        FileNotFoundError: The definition is absent.
        Exception: `harness/dump_tables.py`'s own `ScenarioFileError`,
            `TableNotInScopeError` or `UnknownTableError` when the list is unusable.
    """
    path = scenario_file(scenario)
    if not path.is_file():
        # Raised here rather than left to the harness, so the diagnosis names the
        # eight expected definitions.
        scenario_definition(scenario)
    return tuple(harness_dump_tables().scenario_tables(path))



# ---------------------------------------------------------------------------
#  SECTION 8  -  THE SHELL STAGES  (rule R-1)
#
#  The four harness runners are SHELL, so a subprocess is the only way to reach
#  them - which is also exactly how R-1 wants the compiled oracle reached: OUT OF
#  PROCESS. Nothing here invokes `cobc` or `cobcrun`, nothing loads a COBOL object,
#  and there is no FFI of any kind. Each script drives the compiled menu
#  executables itself, because every in-scope posting program is a CALLed
#  sub-program with group-item linkage and cannot be invoked from a shell at all.
#
#  THE SEEDING CONTRACT, AND WHY THE MAINTAINER'S SCRIPT IS NEVER INVOKED.
#  Agent Action Plan section 0.2.1 designates common/masterLD.sh and the
#  common/*LD.cbl loaders as the SPECIFICATION for seeding. Two independent facts
#  keep the script itself out of the protocol:
#    1. Its own header says so - [common/masterLD.sh:L4-L5]: "THIS SCRIPT HAS NOT
#       YET BEEN TESTED".
#    2. It cannot execute at all. All 24 loader lines
#       [common/masterLD.sh:L93-L116] omit the `;` before `fi`, so `bash -n` rejects
#       it at line 124. It is FROZEN and is NOT fixed (Agent Action Plan section
#       0.8.1, rules R-3 and R-4).
#  harness/seed.sh reproduces its documented per-file contract instead
#  [common/masterLD.sh:L44-L115]. It also carries no `less`: the frozen script pages
#  SYS-DISPLAY.log through it [common/masterLD.sh:L119-L123], which would block a
#  non-interactive run forever.
#
#  EVERY SUBPROCESS IS NON-INTERACTIVE AND BOUNDED. stdin is /dev/null so a stray
#  prompt fails instead of hanging, both streams are captured, and a wall-clock
#  timeout is applied - each script bounds its own internals as well, but a stage
#  that never returns is worse than one that fails, because it looks like progress.
# ---------------------------------------------------------------------------

# Wall-clock ceilings, generous because the compiled oracle drives real menus over a
# pty and the frozen file-handler logger cannot be switched off
# ([copybooks/Test-Data-Flags.cob] hardcodes `SW-Testing pic 9 value 1`, so every
# DAL call writes). These bound THIS process's wait; each script's own finite
# deadlines are unchanged and are the authority on what it does internally.
STAGE_TIMEOUT_SEED: Final[int] = 1800
STAGE_TIMEOUT_RESET: Final[int] = 1800
STAGE_TIMEOUT_RUN: Final[int] = 3600

# The protocol stage names, used in every `StageResult` and every failure message so
# a reader can place a finding in the sequence at a glance.
STAGE_SEED: Final[str] = "1-seed"
STAGE_RUN_COBOL: Final[str] = "2-run-cobol"
STAGE_DUMP_COBOL: Final[str] = "3-dump-cobol"
STAGE_NORMALIZE_COBOL: Final[str] = "4-normalize-cobol"
STAGE_RESET: Final[str] = "5-reset"
STAGE_RUN_PYTHON: Final[str] = "6-run-python"
STAGE_DUMP_PYTHON: Final[str] = "7-dump-python"
STAGE_NORMALIZE_PYTHON: Final[str] = "7b-normalize-python"
STAGE_DIFF: Final[str] = "8-diff"


class HarnessFaultError(RuntimeError):
    """A protocol stage could not be performed, so there is no evidence to judge.

    Distinct from a behavioural difference on purpose. A behavioural difference is
    the answer the protocol exists to produce; a harness fault means the question was
    never asked, and Agent Action Plan section 0.6.5 is explicit that ABSENCE IS
    EVIDENCE only when the run itself completed. Mapping this to a test ERROR rather
    than a failure keeps "could not compare" from ever reading as "no differences".
    """


@dataclass(frozen=True)
class StageResult:
    """One protocol stage's outcome, captured whole.

    Frozen: a stage result is evidence, and evidence that can be edited after the
    fact is not evidence.

    Attributes:
        stage: One of the `STAGE_*` names.
        argv: The exact command line, for the failure message and the record.
        returncode: The exit status VERBATIM. Never normalised, never clamped - the
            status is behavioural data for a run stage and a documented diagnosis
            for every other stage.
        stdout: Everything the stage wrote to stdout.
        stderr: Everything it wrote to stderr.
    """

    stage: str
    argv: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        """Whether the stage exited zero."""
        return self.returncode == 0

    def describe(self) -> str:
        """A multi-line description, for a failure message.

        Returns:
            The stage, its command line, its status and both streams.
        """
        return (
            f"stage {self.stage} exited {self.returncode}\n"
            f"  command: {' '.join(self.argv)}\n"
            f"  stdout:\n{_indent(self.stdout)}\n"
            f"  stderr:\n{_indent(self.stderr)}"
        )

    def raise_for_status(self) -> StageResult:
        """Return self when the stage succeeded, or raise.

        FOR THE STAGES WHOSE FAILURE DESTROYS THE EVIDENCE - seed, reset, dump,
        normalize. It is deliberately NOT applied to the two run stages: a run that
        aborts behaviourally still leaves the database in the state the specification
        says it should be in, and that state must still be dumped.

        Returns:
            Self.

        Raises:
            HarnessFaultError: The stage exited non-zero.
        """
        if self.ok:
            return self
        raise HarnessFaultError(
            f"{self.describe()}\n"
            f"  This stage's failure means the comparison could not be performed, "
            f"so there is no weaker evidence to carry forward: re-run the protocol "
            f"from stage {STAGE_SEED} (rule R-6)."
        )


def _indent(text: str, prefix: str = "    ") -> str:
    """Indent captured output so a multi-line stream reads as one block.

    Args:
        text: The captured stream.
        prefix: The indent.

    Returns:
        The indented text, or a marker when the stream was empty - an EMPTY stream is
        itself meaningful, because `harness/diff_states.py` writes zero bytes to
        stdout on a pass.
    """
    if not text:
        return f"{prefix}<empty>"
    return "\n".join(f"{prefix}{line}" for line in text.splitlines())


def _run_script(
    script: Path,
    argv: Sequence[str],
    *,
    stage: str,
    timeout: int,
    env: Mapping[str, str] | None = None,
) -> StageResult:
    """Run one harness shell script as a subprocess, non-interactively.

    Args:
        script: The script to run.
        argv: Its arguments, already stringified.
        stage: The `STAGE_*` name, recorded in the result.
        timeout: The wall-clock ceiling for THIS wait.
        env: The environment; the current one when omitted. It is passed through
            rather than filtered, because the scripts read `ACAS_*` and
            `ACAS_SEED_STRICT` from it and this module has no business deciding what
            they see.

    Returns:
        The captured result. A non-zero status is RETURNED, never raised: the caller
        decides, because for a run stage the status is behavioural data.

    Raises:
        HarnessFaultError: The script is absent or not executable, or it exceeded
            `timeout`.
    """
    if not script.is_file():
        raise HarnessFaultError(
            f"stage {stage} cannot run: {script} is absent. "
            f"{_script_absence_note(script)}"
        )
    if not os.access(script, os.X_OK):
        raise HarnessFaultError(
            f"stage {stage} cannot run: {script} is not executable."
        )

    command = (str(script), *(str(item) for item in argv))
    try:
        completed = subprocess.run(  # noqa: S603 - a fixed, repository-owned script
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
            stdin=subprocess.DEVNULL,
            cwd=str(REPO_ROOT),
            env=dict(os.environ if env is None else env),
        )
    except subprocess.TimeoutExpired as exc:
        raise HarnessFaultError(
            f"stage {stage} exceeded its {timeout}s ceiling and was stopped. "
            f"command: {' '.join(command)}. A stage that never returns is worse "
            f"than one that fails, because it looks like progress; the usual cause "
            f"is a frozen program waiting on an ACCEPT - "
            f"{ENV_LEDGERS} or {ENV_BIN} blank makes every one of them do that "
            f"[copybooks/Proc-Get-Env-Set-Files.cob:L20-L28]."
        ) from exc

    return StageResult(
        stage=stage,
        argv=command,
        returncode=completed.returncode,
        stdout=completed.stdout or "",
        stderr=completed.stderr or "",
    )


def _script_absence_note(script: Path) -> str:
    """Explain why a harness script might not be there yet.

    Args:
        script: The absent script.

    Returns:
        The diagnosis. `harness/run_python_scenario.sh` gets its own, because
        harness/docker-compose.yml records in the canonical recipe itself that it is
        a planned Agent Action Plan section 0.4.1.7 deliverable which "arrives with
        the Python cycle it drives", and stage 6 fails with "no such file" until
        then. That is reported rather than worked around: an in-process substitute
        would be a second definition of stage 6 and would bypass the runner's own
        post-run assertions (rule R-4).
    """
    if script == RUN_PYTHON_SCRIPT:
        return (
            "harness/run_python_scenario.sh is stage 6 of the parity protocol and "
            "is a planned Agent Action Plan section 0.4.1.7 deliverable; "
            "harness/docker-compose.yml calls this out in the canonical recipe "
            "itself. It is NOT substituted with an in-process driver here: that "
            "would be a second definition of the stage and would skip the runner's "
            "own post-run assertions."
        )
    return (
        "It is one of the four harness shell stages (Agent Action Plan section "
        "0.4.1.7) and the protocol cannot proceed without it."
    )


def seed(
    scenario: str,
    *,
    data_dir: Path | str | None = None,
    only: Sequence[str] | None = None,
    dry_run: bool = False,
) -> StageResult:
    """STAGE 1 - seed the frozen schema through the maintainer's load programs.

    Invokes `harness/seed.sh`, NEVER `common/masterLD.sh` - see the section comment
    above for the two reasons.

    THE SCENARIO IS BINDING, not merely logged. harness/seed.sh stages the
    scenario's declared `seed_files` into a fresh scenario-owned fixture, writes an
    identity marker naming the files and their digests, and seeds from exactly those;
    `harness/reset_db.sh` asserts the same marker after its re-seed, which is how
    stage 5 demonstrably re-seeds from the fixture stage 1 used. A scenario that is
    only recorded would let the seed come from whatever flat files happened to be in
    the data directory, and the resulting dump would then be attributed to a scenario
    it was never derived from.

    AUTOCOMMIT MUST BE OFF. `harness/seed.sh` asserts it and exits 73 otherwise,
    citing the banner every one of the 28 frozen loaders carries at
    [common/glbatchLD.cbl:L9-L13]: "This modules uses commit and rollback so you
    MUST ensure that autocommit is OFF in the rdb settings." The seeded state depends
    on the loaders' commit boundaries.

    `ACAS_SEED_STRICT` IS PASSED THROUGH AND NEVER SET HERE. Setting it to 1 OPTS IN
    to aborting on a return code the frozen test tolerates - 1 through 63, of which
    16 is "error writing data to rdb" [common/masterLD.sh:L39]; leaving it unset,
    the default, applies the frozen `-gt 63` tolerance [common/masterLD.sh:L41].
    Hard-coding either would override a frozen decision (rules R-3, R-4).

    Args:
        scenario: The scenario whose seed files bind the load.
        data_dir: `--data-dir`; `$ACAS_DATA` when omitted. The frozen script
            hard-codes `cd ~/ACAS` [common/masterLD.sh:L45].
        only: `--only`, a loader list, for debugging. Each name must be one of the
            20 in-scope loaders; the 8 out-of-scope loaders are refused by name.
        dry_run: `--dry-run` - print the plan and touch nothing.

    Returns:
        The captured result, its exit status verbatim. Codes 70 to 75 are
        harness/seed.sh's own diagnoses; a loader's own 16, 64 or 128 is described
        by `LOADER_RETURN_CODES`.
    """
    argv: list[str] = []
    if data_dir is not None:
        argv += ["--data-dir", str(data_dir)]
    if only:
        argv += ["--only", ",".join(only)]
    if dry_run:
        argv.append("--dry-run")
    argv.append(str(scenario_file(scenario)))
    return _run_script(
        SEED_SCRIPT, argv, stage=STAGE_SEED, timeout=STAGE_TIMEOUT_SEED
    )


def reset(
    scenario: str,
    *,
    schema_only: bool = False,
    dry_run: bool = False,
) -> StageResult:
    """STAGE 5 - drop, re-apply the frozen schema verbatim, and re-seed.

    Invokes `harness/reset_db.sh`. Both cycles must start from byte-for-byte the
    same seeded state or the diff they produce means nothing.

    NO DDL OF THIS MODULE'S OWN, and none of the script's either (rule R-3):
    `mysql/ACASDB.sql` already carries 33 `DROP TABLE IF EXISTS` alongside its 33
    `CREATE TABLE`, so RE-APPLYING THE FROZEN FILE VERBATIM *IS* THE
    DROP-AND-RECREATE. There is no `TRUNCATE` loop here, no `DROP DATABASE` - the
    frozen file contains neither `CREATE DATABASE` nor `USE`, so the database name is
    supplied on the client command line - and the client is never passed `--force`.
    The file manages its own session state (`SET NAMES utf8mb4`, `UNIQUE_CHECKS=0`,
    `FOREIGN_KEY_CHECKS=0`, `SQL_MODE='NO_AUTO_VALUE_ON_ZERO'`, `SQL_NOTES=0`, all
    restored at its tail) and NONE IS ADDED. The charset caveat at
    [mysql/ACASDB.sql:L9-L11] - `SET NAMES utf8mb4` against utf8mb3 tables - is a
    reproduced anomaly and is NOT fixed (rule R-4).

    THE THREE DESTRUCTIVE GATES ARE THE SCRIPT'S, AND THIS MODULE SATISFIES NONE OF
    THEM ON THE OPERATOR'S BEHALF. In particular `$ACAS_RESET_CONSENT` is read from
    the environment, never computed here - see `reset_consent_token`.

    Args:
        scenario: The scenario forwarded verbatim, so the re-seed provably reuses the
            fixture stage 1 seeded from. Naming one whose seed files are missing
            fails with 91 rather than silently re-seeding from something else.
        schema_only: `--schema-only` - apply the schema and skip the re-seed.
        dry_run: `--dry-run` - report the three gates instead of enforcing them.

    Returns:
        The captured result. Codes 80 to 91 are the script's own diagnoses.
    """
    argv: list[str] = []
    if schema_only:
        argv.append("--schema-only")
    if dry_run:
        argv.append("--dry-run")
    argv.append(str(scenario_file(scenario)))
    return _run_script(
        RESET_SCRIPT, argv, stage=STAGE_RESET, timeout=STAGE_TIMEOUT_RESET
    )


def run_cobol(
    scenario: str,
    *,
    operation: str | None = None,
    dry_run: bool = False,
) -> StageResult:
    """STAGE 2 - drive the COMPILED COBOL posting cycle. THE ORACLE SIDE.

    Invokes `harness/run_cobol_scenario.sh`, which drives the four compiled menu
    executables over a pty because every in-scope posting program is a CALLed
    sub-program with group-item linkage and therefore cannot be invoked from a shell.

    A NON-ZERO STATUS IS RETURNED, NEVER RAISED. Agent Action Plan section 0.6.5: for
    a run-aborting rejection "the database effect is therefore THE ABSENCE of
    everything the later phases would have written" - ABSENCE IS EVIDENCE, and a
    helper that short-circuited the dump would destroy the evidence for
    `control_total_mismatch` and `mixed_accepted_rejected`.

    Args:
        scenario: The scenario, passed as the positional scenario file exactly as the
            canonical recipe does.
        operation: `--operation`; derived from the scenario's own `operation` key when
            omitted.
        dry_run: `--dry-run` - resolve and print the keystroke plan, run every
            precondition, spawn no menu.

    Returns:
        The captured result. Codes 70 to 79 are the script's own diagnoses; 74 in
        particular means a compiled artifact is missing and `harness/build_oracle.sh`
        has not completed.

    Raises:
        ValueError: `operation` is given and is not one of the seven.
    """
    argv: list[str] = []
    if operation is not None:
        assert_operation(operation)
        argv += ["--operation", operation]
    if dry_run:
        argv.append("--dry-run")
    argv.append(str(scenario_file(scenario)))
    return _run_script(
        RUN_COBOL_SCRIPT, argv, stage=STAGE_RUN_COBOL, timeout=STAGE_TIMEOUT_RUN
    )


def run_python(
    scenario: str,
    *,
    operation: str | None = None,
    dry_run: bool = False,
) -> StageResult:
    """STAGE 6 - drive the MIGRATED PYTHON posting cycle.

    Invokes `harness/run_python_scenario.sh`, which accepts the same seven
    `--operation` names as the oracle runner so the two stay trivially comparable.

    A non-zero status is RETURNED, never raised, for the same reason as `run_cobol`:
    only three in-scope programs set `WS-Term-Code` at all - gl070 to 5
    [general/gl070.cbl:L289], sl055 to 8 [sales/sl055.cbl:L344] and pl055 to 8
    [purchase/pl055.cbl:L286] - and `acas_posting/cli/args.py`'s
    `exit_status_for(term_code)` surfaces the term code itself, so exit 5 and exit 8
    are BEHAVIOURAL RESULTS whose database effect must still be dumped.

    Args:
        scenario: The scenario, passed as the positional scenario file.
        operation: `--operation`; derived from the scenario when omitted.
        dry_run: `--dry-run`.

    Returns:
        The captured result.

    Raises:
        ValueError: `operation` is given and is not one of the seven.
        HarnessFaultError: The script is absent - it is a planned Agent Action Plan
            section 0.4.1.7 deliverable, and no in-process substitute is improvised.
    """
    argv: list[str] = []
    if operation is not None:
        assert_operation(operation)
        argv += ["--operation", operation]
    if dry_run:
        argv.append("--dry-run")
    argv.append(str(scenario_file(scenario)))
    return _run_script(
        RUN_PYTHON_SCRIPT, argv, stage=STAGE_RUN_PYTHON, timeout=STAGE_TIMEOUT_RUN
    )


def classify_run(result: StageResult, *, operation: str) -> str:
    """Classify a run stage's exit status into one of the three dispositions.

    THE THREE CATEGORIES ARE KEPT DISTINCT, and an UNRECOGNISED code is reported as
    a harness fault rather than quietly treated as either of the others: a status
    nobody has classified is a status nobody should draw a conclusion from.

    Args:
        result: A `run_cobol` or `run_python` result.
        operation: Which of the seven was driven, so the admissible term codes are
            known.

    Returns:
        `DISPOSITION_SUCCESS`, `DISPOSITION_BEHAVIOURAL` or
        `DISPOSITION_HARNESS_FAULT`.

    Raises:
        ValueError: `operation` is not one of the seven, or `result` is not a run
            stage.
    """
    assert_operation(operation)
    if result.stage not in {STAGE_RUN_COBOL, STAGE_RUN_PYTHON}:
        raise ValueError(
            f"classify_run describes a run stage; got {result.stage!r}. The other "
            f"stages have documented diagnoses of their own and no term code."
        )

    code = result.returncode
    if code == 0:
        return DISPOSITION_SUCCESS

    # A bad command line. Reported first, because it is the one category that means
    # this module made the mistake.
    if code == ARGPARSE_USAGE_EXIT:
        return DISPOSITION_HARNESS_FAULT

    # The runner's own documented band. Only the COBOL runner has one; the Python
    # runner passes the cycle's status through.
    if result.stage == STAGE_RUN_COBOL and code in RUN_COBOL_FAULT_CODES:
        return DISPOSITION_HARNESS_FAULT

    if code in TERM_CODES[operation]:
        return DISPOSITION_BEHAVIOURAL

    return DISPOSITION_HARNESS_FAULT



# ---------------------------------------------------------------------------
#  SECTION 9  -  THE DUMP, NORMALIZE AND DIFF STAGES
#
#  DRIVEN IN PROCESS, and that is the design each module asks for:
#  harness/dump_tables.py states it outright - "`main` RETURNS an exit code and
#  never calls sys.exit, so tests/conftest.py can drive it in process" - and
#  harness/normalize.py and harness/diff_states.py carry the same contract,
#  including mapping argparse's own usage failure to a documented code rather than
#  letting a SystemExit escape. So these three stages need no subprocess, and the
#  exit status and the captured streams are available directly.
#
#  EVERY ONE OF THEM IS A WRAPPER. Nothing here re-implements a dump, a
#  canonicalisation or a comparison; the argv is composed, `main` is called and the
#  result is captured. In particular:
#
#    * NORMALISATION DOES EXACTLY THREE THINGS AND THERE IS NO FOURTH, and none of
#      them is reproduced here: trailing spaces in fixed-character columns
#      (`rstrip(" ")`, TRAILING ONLY, because a COBOL alphanumeric MOVE is
#      left-justified so LEADING spaces are content); decimal scale rendering to the
#      column's DECLARED scale, which is NOT uniformly 2 and where a value implying
#      more places RAISES rather than rounds, because rounding there would hide a
#      real finding; and the two- versus four-digit date text forms, under an
#      explicit five-column allow-list. `normalize_dump` is a PURE function and this
#      wrapper keeps it that way - no logging inside it, no timestamp, no
#      environment read.
#    * THE DIFF IS EXACT: `==` after a type check, and nothing else. There is no
#      tolerance, no epsilon, no closeness helper from the standard library, no
#      approximate-equality helper from the test runner, no case- or
#      whitespace-insensitive comparison and no numeric coercion - a type mismatch,
#      `1` against `"1"`, IS a difference. Rows are aligned by primary-key VALUE,
#      never by position, and the two labels are `cobol` and `python`, never left
#      and right.
#    * THERE IS NO IGNORE-LIST, NO TOLERANCE-LIST AND NO "KNOWN DIFFERENCE"
#      ALLOWANCE anywhere below. Bounding is done by the scenario's affected-table
#      list and by nothing else.
#    * NOTHING HERE CORRECTS OBSERVED BEHAVIOUR (rule R-4). No null is coalesced, no
#      missing row is defaulted, no row or column is re-ordered for legibility, and
#      nothing is trimmed beyond harness/normalize.py's own job 1. A helper that
#      tidied a result would be a defect, not a kindness: the whole value of this
#      migration is that the Python cycle can replace the COBOL cycle without changing
#      a single posted figure, and a tidied comparison cannot demonstrate that.
# ---------------------------------------------------------------------------


def _drive_harness_main(
    module: ModuleType, argv: Sequence[str], *, stage: str
) -> StageResult:
    """Call one harness module's `main` in process and capture everything.

    Args:
        module: A loaded harness module with a `main(argv) -> int`.
        argv: The arguments, without the program name.
        stage: The `STAGE_*` name, recorded in the result.

    Returns:
        The captured result, with the exit status verbatim.

    Raises:
        HarnessFaultError: `main` raised instead of returning a status. Each module
            maps its own documented failures to exit codes, so an escaping exception
            is an unhandled case and is reported as a fault rather than swallowed.
    """
    arguments = tuple(str(item) for item in argv)
    out = io.StringIO()
    err = io.StringIO()

    # `main` tightens the umask to 0o077 for the files it creates, because a dump
    # carries live accounting data and the output root is a shared bind mount. That
    # is process-global, so the previous value is restored afterwards: this module
    # has no business changing the umask of the tests that run after it. The
    # protection of the files main() itself writes is unaffected, because the
    # restore happens after main() returns.
    previous_umask = os.umask(0o077)
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            status = module.main(list(arguments))
    except SystemExit as exc:  # pragma: no cover - the modules document they do not
        raise HarnessFaultError(
            f"stage {stage}: {module.__name__} raised SystemExit({exc.code!r}); it "
            f"documents that `main` returns a status and never calls sys.exit, so "
            f"an in-process caller can inspect the code."
        ) from exc
    except Exception as exc:
        raise HarnessFaultError(
            f"stage {stage}: {module.__name__}.main raised "
            f"{type(exc).__name__}: {exc}\n"
            f"  command: {' '.join(arguments)}\n"
            f"  stdout:\n{_indent(out.getvalue())}\n"
            f"  stderr:\n{_indent(err.getvalue())}"
        ) from exc
    finally:
        os.umask(previous_umask)

    return StageResult(
        stage=stage,
        argv=(module.__name__, *arguments),
        returncode=int(status),
        stdout=out.getvalue(),
        stderr=err.getvalue(),
    )


def dump(
    scenario: str,
    side: str,
    *,
    tables: Sequence[str] | None = None,
    out_dir: Path | str | None = None,
) -> StageResult:
    """STAGES 3 and 7 - capture one side's table state.

    Agent Action Plan section 0.6.6 establishes that this is deterministic by
    construction, so a non-empty diff is always a real behavioural difference: the
    dump is `SELECT * FROM <table> ORDER BY <primary key>` with NO tie-breaking,
    NO timestamp masking and NO surrogate-key remapping, because the frozen schema is
    exceptionally well behaved: every in-scope table has a single-column primary key,
    zero secondary indexes, no TIMESTAMP column, no AUTO_INCREMENT and (with one
    documented exception the harness allows for by name) no column-level default.

    THE SELECTION IS ALWAYS BOUNDED. `harness/dump_tables.py` REFUSES an unbounded
    run rather than defaulting to all 22, and this wrapper passes the scenario's own
    definition file as the selector so the list comes from the scenario itself. Pass
    `tables` only to narrow one table by hand while debugging.

    Args:
        scenario: The scenario name, which also composes the output path.
        side: `cobol` or `python`. Recorded in the PATH, never in a file.
        tables: An explicit `--tables` list. When omitted the scenario's
            `affected_tables` is used, which is the protocol.
        out_dir: `--out-dir`; `$ACAS_OUT` when omitted.

    Returns:
        The captured result. `EX_OK` is 0; 80 to 87 are the module's documented
        diagnoses.

    Raises:
        ValueError: `side` is not one of the two, or `scenario` is not a plain name.
        FileNotFoundError: The scenario definition is absent and no `tables` was
            given.
    """
    assert_side(side)
    assert_scenario_name(scenario)

    argv: list[str] = ["--scenario", scenario, "--side", side, "--quiet"]
    if out_dir is not None:
        argv += ["--out-dir", str(out_dir)]
    if tables is None:
        path = scenario_file(scenario)
        if not path.is_file():
            scenario_definition(scenario)  # raises with the full diagnosis
        argv += ["--scenario-file", str(path)]
    else:
        argv += ["--tables", ",".join(tables)]

    stage = STAGE_DUMP_COBOL if side == SIDE_COBOL else STAGE_DUMP_PYTHON
    return _drive_harness_main(harness_dump_tables(), argv, stage=stage)


def normalize(
    scenario: str,
    side: str,
    *,
    tables: Sequence[str] | None = None,
    out_dir: Path | str | None = None,
) -> StageResult:
    """STAGE 4 (and again after stage 7) - canonicalise one side's dump.

    Delegates every part of the three jobs to `harness/normalize.py`. NOTHING IS
    REIMPLEMENTED AND NO FOURTH JOB IS ADDED - see the section comment. The
    obligation runs both ways: remove the representation artefacts, and NEVER make
    two genuinely different stored values compare equal, so that Agent Action Plan
    section 0.6.6 holds - "a non-empty diff is always a real behavioral difference
    and never an artefact of the comparison".

    Args:
        scenario: The scenario name.
        side: `cobol` or `python`.
        tables: An explicit `--tables` restriction; every dump present by default.
        out_dir: `--out-dir`; `$ACAS_OUT` when omitted.

    Returns:
        The captured result.

    Raises:
        ValueError: `side` is not one of the two, or `scenario` is not a plain name.
    """
    assert_side(side)
    assert_scenario_name(scenario)

    argv: list[str] = ["--scenario", scenario, "--side", side, "--quiet"]
    if out_dir is not None:
        argv += ["--out-dir", str(out_dir)]
    if tables is not None:
        argv += ["--tables", ",".join(tables)]

    stage = (
        STAGE_NORMALIZE_COBOL if side == SIDE_COBOL else STAGE_NORMALIZE_PYTHON
    )
    return _drive_harness_main(harness_normalize(), argv, stage=stage)


@dataclass(frozen=True)
class DiffOutcome:
    """A comparison's verdict, with the evidence that produced it.

    Attributes:
        result: The stage result, carrying the THREE-WAY exit status verbatim -
            0 identical with EMPTY stdout, 1 a real behavioural difference, 2 the
            comparison could not be performed.
        tree: The `harness/diff_states.py` `TreeDiff`. `tree.is_empty` is THE PASS
            CONDITION and is the single question a scenario test asks.
        report: The path of `diff.txt`. A PASSING run writes a ZERO-BYTE file, which
            is deliberate: the evidence document must distinguish "compared, and
            identical" from "never compared", and an existing empty file says the
            first while an absent file says nothing at all.
    """

    result: StageResult
    tree: Any
    report: Path

    @property
    def is_empty(self) -> bool:
        """THE PASS CONDITION - Agent Action Plan section 0.8.5: "the diff must be
        empty".

        Returns:
            True when the two normalised trees are identical.
        """
        return bool(self.tree.is_empty)


def diff(
    scenario: str,
    *,
    tables: Sequence[str] | None = None,
    out_dir: Path | str | None = None,
    max_differences: int | None = None,
) -> DiffOutcome:
    """STAGE 8 - compare the two normalised trees. AN EMPTY DIFF IS THE PASS.

    THE THREE-WAY EXIT CONTRACT, and the one conflation that must never happen:

        0  the trees are identical, and stdout is EMPTY - zero bytes, not a banner
        1  a real behavioural difference, with a deterministic report
        2  THE COMPARISON COULD NOT BE PERFORMED - a missing tree, a missing table
           file, a malformed dump, a shape mismatch, a float in the input, a
           duplicate primary key

    Exit 2 is mapped to `HarnessFaultError`, which surfaces as a test ERROR. A test
    that treated "could not compare" as "no differences" is the single worst bug
    available in this tree, and rule R-6 makes an empty diff the pass condition only
    when a comparison actually happened.

    `main` is called FIRST, because it is the authority: it writes `diff.txt`, which
    is the artifact the per-scenario evidence cites, and it returns the status an
    operator sees. The `TreeDiff` is then built with `diff_trees` - the same function
    `main` used - so a test can inspect the findings, and the two are cross-checked:
    a disagreement between the status and `is_empty` would mean the two views of one
    comparison had diverged, which is itself a fault.

    Args:
        scenario: The scenario name.
        tables: An explicit table list, in report order. The scenario's
            `affected_tables` by default, which is the protocol.
        out_dir: `--out-dir`; `$ACAS_OUT` when omitted.
        max_differences: `--max-differences`. It truncates the REPORT only: the true
            total is always printed and truncation NEVER changes the exit code.

    Returns:
        The outcome.

    Raises:
        HarnessFaultError: The comparison could not be performed (exit 2), or the
            status and the `TreeDiff` disagree.
        ValueError: `scenario` is not a plain directory name.
    """
    assert_scenario_name(scenario)
    diff_states = harness_diff_states()

    argv: list[str] = ["--scenario", scenario, "--quiet"]
    if out_dir is not None:
        argv += ["--out-dir", str(out_dir)]
    if tables is None:
        path = scenario_file(scenario)
        if not path.is_file():
            scenario_definition(scenario)
        argv += ["--scenario-file", str(path)]
    else:
        argv += ["--tables", ",".join(tables)]
    if max_differences is not None:
        argv += ["--max-differences", str(max_differences)]

    result = _drive_harness_main(diff_states, argv, stage=STAGE_DIFF)

    if result.returncode == diff_states.EX_ERROR:
        raise HarnessFaultError(
            f"{result.describe()}\n"
            f"  Exit {diff_states.EX_ERROR} means THE COMPARISON COULD NOT BE "
            f"PERFORMED - a missing tree, a missing table file, a malformed dump, "
            f"a shape mismatch, a float in the input or a duplicate primary key. "
            f"It is NEVER a pass: rule R-6 makes an empty diff the pass condition "
            f"only when a comparison actually happened."
        )

    paths = scenario_paths(scenario, out_root=out_dir)
    resolved_tables = (
        tuple(tables) if tables is not None else scenario_affected_tables(scenario)
    )
    tree = diff_states.diff_trees(
        paths.cobol_normalized, paths.python_normalized, resolved_tables
    )

    expected = (
        diff_states.EX_IDENTICAL if tree.is_empty else diff_states.EX_DIFFERENT
    )
    if result.returncode != expected:
        raise HarnessFaultError(
            f"{result.describe()}\n"
            f"  The comparison's own exit status and its TreeDiff disagree: the "
            f"status is {result.returncode} while TreeDiff.is_empty is "
            f"{tree.is_empty} ({tree.total_differences} finding(s)). Both are "
            f"produced by the same diff_trees over the same two trees, so a "
            f"disagreement means the trees changed between the two reads and "
            f"neither view can be trusted."
        )

    return DiffOutcome(result=result, tree=tree, report=paths.diff_report)


def diff_trees_directly(
    cobol_normalized: Path | str,
    python_normalized: Path | str,
    tables: Sequence[str] | None = None,
    *,
    allow_raw: bool = False,
) -> Any:
    """Compare two normalised trees given by path, returning the `TreeDiff`.

    For tests/determinism/, which compares two runs of ONE side and therefore has no
    canonical `<scenario>/cobol` and `<scenario>/python` pair to name. NOTE that
    `harness/diff_states.py` has exactly two labels and they are not configurable, so
    in such a comparison `cobol` in the report means the FIRST tree and `python` the
    SECOND. That is stated rather than papered over.

    Args:
        cobol_normalized: The tree reported as `cobol` - the specification side, or
            the first run.
        python_normalized: The tree reported as `python` - the migrated side, or the
            second run.
        tables: The tables to compare, in report order. The union of what the two
            trees hold when omitted.
        allow_raw: Permit directories whose names do not end `.normalized` or
            `.norm`. A DEBUGGING ESCAPE: raw dumps still carry the representation
            artefacts, so a verdict taken that way is not evidence.

    Returns:
        The `TreeDiff`; `is_empty` is the pass condition.

    Raises:
        Exception: `harness/diff_states.py`'s own errors - a missing tree, the same
            tree twice (which would always pass and so is refused), a malformed dump,
            a duplicate primary key, or a float (rule R-2).
    """
    return harness_diff_states().diff_trees(
        Path(cobol_normalized),
        Path(python_normalized),
        None if tables is None else tuple(tables),
        allow_raw=allow_raw,
    )


def read_dump(path: Path | str) -> dict[str, Any]:
    """Read one `<TABLE>.json` dump file.

    Args:
        path: The dump file.

    Returns:
        The parsed dump object. Its shape is NOT asserted here - pass it to
        `assert_dump_wellformed` for that.

    Raises:
        Exception: `harness/diff_states.py`'s `DumpReadError` when the file is
            missing, unreadable or not a JSON object.
    """
    return harness_diff_states().read_dump(Path(path))


def assert_dump_wellformed(
    dump_object: Mapping[str, Any],
    *,
    where: str = "dump",
    schema: Mapping[str, Mapping[str, Any]] | None = None,
) -> None:
    """Assert one dump object has the shape the protocol guarantees.

    THE SHAPE, from `harness/dump_tables.py`'s `DUMP_KEYS`: exactly five keys in
    fixed insertion order - `table`, `primary_key`, `columns`, `row_count`, `rows` -
    AND NO OTHERS. No timestamp, no server version, no scenario name, no side; the
    side is recorded in the PATH. `columns` is in schema ordinal order and is never
    sorted; `rows` is a list of lists in primary-key-ascending order, positionally
    aligned. DECIMAL values are canonical JSON STRINGS at the declared scale, never
    JSON numbers and never exponent notation; integers are JSON integers; `char` is
    the string the driver returned.

    The structural checks are DELEGATED to `harness/diff_states.py`'s own dump
    assertion, which is the single definition of them (rule R-4): the five keys in
    order, the table in the 22-name allow-list, `primary_key` present in `columns`,
    `row_count == len(rows)`, every row of `len(columns)` values, NO value a float
    (rule R-2), NO value null - and no primary-key value twice.

    Args:
        dump_object: The parsed dump object.
        where: What is being checked, quoted in every message.
        schema: The frozen column-type map from `frozen_schema_map`. When given,
            `columns` is additionally required to match the schema's ordinal order
            for that table EXACTLY, and the column count to match the declared count.

    Raises:
        Exception: `harness/diff_states.py`'s `DumpShapeError`,
            `TableNotInScopeError`, `UnknownTableError`, `DuplicateKeyError`,
            `UnexpectedNullError`, `NumericPolicyError` or
            `UnexpectedValueTypeError`.
        TypeError: The rule R-2 float gate tripped.
        ValueError: A null reached the protocol, or `columns` disagrees with the
            frozen schema.
    """
    diff_states = harness_diff_states()

    # The single definition of the structural contract.
    diff_states._assert_dump(dump_object, where)  # noqa: SLF001 - see docstring

    # Belt and braces for rules R-2 and R-4, over the whole object rather than only
    # the row values, and stated separately so a failure names this file's own gate.
    assert_no_floating_point(dump_object, where=where)
    assert_no_null(dump_object, where=where)

    table = str(dump_object["table"])
    columns = tuple(str(name) for name in dump_object["columns"])

    declared = diff_states.IN_SCOPE[table].column_count
    if len(columns) != declared:
        raise ValueError(
            f"{where}: `{table}` lists {len(columns)} column(s) but "
            f"mysql/ACASDB.sql declares {declared} "
            f"[mysql/ACASDB.sql:L{diff_states.IN_SCOPE[table].schema_line}]. The "
            f"schema is frozen, so a disagreement means either the dump or the "
            f"checkout is wrong."
        )

    if schema is not None:
        expected = harness_normalize().schema_columns(schema, table)
        if columns != expected:
            first = next(
                (
                    index
                    for index, (got, want) in enumerate(zip(columns, expected))
                    if got != want
                ),
                min(len(columns), len(expected)),
            )
            raise ValueError(
                f"{where}: `{table}`'s column list disagrees with the frozen "
                f"schema at position {first}: the dump says "
                f"{columns[first:first + 1]} and mysql/ACASDB.sql says "
                f"{expected[first:first + 1]}. Rows are POSITIONAL, so a column "
                f"list in any other order has no meaningful alignment."
            )


def assert_autocommit_off(connection: Any) -> None:
    """Assert autocommit is OFF, globally and for this session.

    THE MANDATED MODE, and it derives from the banner ALL 28 frozen loaders carry.
    [common/glbatchLD.cbl:L9-L13] verbatim: "This modules uses commit and rollback so
    you MUST ensure that autocommit is OFF in the rdb settings. It is as default set
    ON." The seeded state depends on the loaders' commit boundaries, so seeding under
    ON would produce durable rows the mandated mode does not and the oracle would no
    longer be the thing the Agent Action Plan specifies.

    THE MODE IS ASSERTED AND NEVER SET. `harness/Dockerfile.mariadb` is the single
    authority - it writes `autocommit=0` into the server configuration - and
    `harness/seed.sh` makes the same assertion, exiting 73. A fixture that quietly
    issued `SET autocommit=0` would make the seeded state depend on the test runner
    rather than on the frozen contract.

    A REPRODUCED DEFECT WORTH KNOWING WHILE READING A RESULT (rule R-4): under this
    mode the frozen loaders reach no COMMIT at all - every `perform aa020-Rollback`
    in all 28 loaders is commented out and the single `perform aa030-Commit` anywhere
    is commented out too - so their writes are not durable and a table may read EMPTY
    after a seed that reported success. Nothing here issues the missing COMMIT: a
    defect fixed is a failure.

    Args:
        connection: An open DB-API connection.

    Raises:
        AssertionError: Either setting is not 0.
    """
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT @@GLOBAL.autocommit, @@SESSION.autocommit")
        row = cursor.fetchone()
    finally:
        cursor.close()

    assert row is not None, (
        "the server returned no row for "
        "`SELECT @@GLOBAL.autocommit, @@SESSION.autocommit`."
    )
    global_setting, session_setting = int(row[0]), int(row[1])
    assert global_setting == 0 and session_setting == 0, (
        f"autocommit is ON (global={global_setting}, session={session_setting}); "
        f"the protocol is REFUSED. The Agent Action Plan mandates autocommit OFF "
        f"for the seeding window, deriving it from the banner all 28 frozen loaders "
        f"carry at [common/glbatchLD.cbl:L9-L13]. This assertion never sets the "
        f"mode: harness/Dockerfile.mariadb is the single authority and writes "
        f"autocommit=0 into the server configuration. Start the harness MariaDB "
        f"service built from it, or set autocommit=0 in the server configuration "
        f"and restart."
    )


def _backtick_out_of_scope(table: str) -> str:
    """Backtick-quote one of the four allow-listed autogen table names.

    A DELIBERATELY TINY COMPANION to `harness/dump_tables.py`'s `_ident`, not a
    replacement for it: `_ident` validates against the 22 in-scope tables and refuses
    anything else, which is correct for a dump and is why it cannot quote these four.
    The allow-list here is `AUTOGEN_TABLES` intersected with the harness's own
    `OUT_OF_SCOPE`, so the two definitions cannot drift apart (rule R-4), and a name
    that is not in both is refused rather than quoted.

    Args:
        table: One of `AUTOGEN_TABLES`.

    Returns:
        The name, backtick-quoted. Every identifier in mysql/ACASDB.sql is hyphenated,
        so quoting is mandatory.

    Raises:
        ValueError: The name is not one of the four, is not out of scope according to
            the harness, or contains a backtick.
    """
    if table not in AUTOGEN_TABLES:
        raise ValueError(
            f"{table!r} is not one of the four autogen tables "
            f"({', '.join(AUTOGEN_TABLES)}); this quoter serves those and nothing "
            f"else. Use harness/dump_tables.py's own _ident for an in-scope table."
        )
    if table not in harness_dump_tables().OUT_OF_SCOPE:
        raise ValueError(
            f"{table!r} is listed in AUTOGEN_TABLES but harness/dump_tables.py does "
            f"not consider it out of scope. The two lists have drifted apart, which "
            f"means one of them is wrong."
        )
    if "`" in table:  # pragma: no cover - no schema identifier carries one
        raise ValueError(f"{table!r} contains a backtick and cannot be quoted.")
    return f"`{table}`"


def assert_autogen_tables_empty(connection: Any) -> None:
    """Assert the four autogen tables are still empty. THE SL-AUTOGEN LANDMINE.

    [sales/sales.cbl:L759] dispatches sl830 before sl055 on the COBOL side, the
    sl800 to sl830 autogen series is explicitly out of scope (Agent Action Plan
    section 0.2.2), and `acas_posting/cli/sl_invoice_post.py` dispatches only sl055
    then sl060. If a run leaves rows in these four, the two sides were not doing
    comparable work and no diff over the affected tables can be trusted.

    THE RUNNERS OWN THE AUTHORITATIVE ASSERTION - both make it after their run. This
    is the in-process equivalent, for a test that wants to make it directly.

    WHY THE HARNESS'S OWN IDENTIFIER QUOTER IS NOT USED HERE, and why that is not a
    duplication: `harness/dump_tables.py`'s `_ident` validates against the 22
    IN-SCOPE tables and REFUSES an out-of-scope name outright, which is exactly right
    for a dump - "dumping one would compare state the migration does not produce" -
    and these four are out of scope by definition. So the quoting for these four
    names goes through `_backtick_out_of_scope`, whose allow-list is `AUTOGEN_TABLES`
    intersected with the harness's own `OUT_OF_SCOPE`. Every identifier in this
    schema is HYPHENATED, so backtick quoting is mandatory either way.

    Args:
        connection: An open DB-API connection.

    Raises:
        AssertionError: One of the four holds a row.
        ValueError: A name is not one of the four allow-listed autogen tables.
    """
    populated: list[str] = []
    for table in AUTOGEN_TABLES:
        statement = f"SELECT COUNT(*) FROM {_backtick_out_of_scope(table)}"
        cursor = connection.cursor()
        try:
            cursor.execute(statement)
            row = cursor.fetchone()
        finally:
            cursor.close()
        count = 0 if row is None else int(row[0])
        if count:
            populated.append(f"{table}={count}")

    assert not populated, (
        f"the autogen tables are not empty ({', '.join(populated)}). "
        f"[sales/sales.cbl:L759] dispatches the out-of-scope sl830 before sl055 on "
        f"the COBOL side while acas_posting/cli/sl_invoice_post.py dispatches only "
        f"sl055 then sl060, so rows here mean the two sides were not doing "
        f"comparable work and the diff cannot be trusted."
    )



# ---------------------------------------------------------------------------
#  SECTION 10  -  THE COMPOSED PROTOCOL
#
#  THE EIGHT STAGES, IN THE EXACT ORDER, transcribed from the canonical recipe
#  harness/docker-compose.yml publishes. Normalisation appears twice - once per side -
#  and the "eight-stage" numbering counts it once:
#
#      1  harness/seed.sh                 "$S"
#      2  harness/run_cobol_scenario.sh   "$S"
#      3  harness/dump_tables.py  --scenario N --side cobol  --scenario-file "$S"
#      4  harness/normalize.py    --scenario N --side cobol
#      5  harness/reset_db.sh             "$S"
#      6  harness/run_python_scenario.sh  "$S"
#      7  harness/dump_tables.py  --scenario N --side python --scenario-file "$S"
#      7b harness/normalize.py    --scenario N --side python
#      8  harness/diff_states.py  --scenario N --scenario-file "$S"
#
#  Agent Action Plan section 0.8.5: "seed identically through the maintainer's load
#  programs, run the compiled cycle, dump the affected tables ordering-normalised,
#  reset, run the Python cycle, dump again - and the diff MUST BE EMPTY."
#
#  ALWAYS DUMP, THEN DECIDE THE STATUS. The two run stages' exit codes are recorded
#  and never allowed to skip the dump that follows them, because Agent Action Plan
#  section 0.6.5 says of a run-aborting rejection that "the database effect is
#  therefore THE ABSENCE of everything the later phases would have written". Absence
#  is evidence, and short-circuiting the dump would destroy it for
#  `control_total_mismatch` and `mixed_accepted_rejected`. Every OTHER stage's
#  failure does destroy the evidence, so those raise.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ParityRun:
    """One scenario's complete parity run: every stage, and the verdict.

    Attributes:
        scenario: The scenario name.
        tables: The affected-table list the comparison was bounded by, in the
            scenario's own order.
        stages: Every stage result in execution order, including the two run stages
            whose non-zero status is behavioural data rather than an error.
        cobol_run: The oracle run's result, for a test asserting on its status.
        python_run: The migrated cycle's run result.
        outcome: The stage-8 verdict.
        paths: Where every artifact of this run lives.
    """

    scenario: str
    tables: tuple[str, ...]
    stages: tuple[StageResult, ...]
    cobol_run: StageResult
    python_run: StageResult
    outcome: DiffOutcome
    paths: ScenarioPaths

    @property
    def is_empty(self) -> bool:
        """THE PASS CONDITION - an empty ordering-normalised diff.

        Returns:
            True when the migrated cycle reproduced the compiled COBOL exactly.
        """
        return self.outcome.is_empty

    @property
    def tree(self) -> Any:
        """The `TreeDiff`, for a test that wants to name what differed."""
        return self.outcome.tree

    def describe(self) -> str:
        """Every stage's outcome, for a failure message.

        Returns:
            One block per stage, in execution order, followed by the verdict.
        """
        blocks = [stage.describe() for stage in self.stages]
        blocks.append(
            f"verdict: {self.outcome.tree.total_differences} finding(s) across "
            f"{len(self.tables)} bounded table(s); report at "
            f"{self.outcome.report}"
        )
        return "\n".join(blocks)


def run_scenario_parity(
    scenario: str,
    *,
    operation: str | None = None,
    out_dir: Path | str | None = None,
    max_differences: int | None = None,
) -> ParityRun:
    """Run all eight protocol stages for one scenario and return the verdict.

    THIS IS THE HELPER THAT MAKES "no test reimplements the comparison protocol"
    TRUE (Agent Action Plan section 0.4.3). A scenario test reads:

        assert run_scenario_parity("clean_batch_gl").is_empty

    STRICTLY SEQUENTIAL (rule R-3): one stage at a time, in the order above, on one
    database. There is no thread, no `asyncio`, no `multiprocessing` and no
    connection pool anywhere in this module, matching the single-threaded COBOL - and
    parallel scenario runs against one shared MariaDB would break this protocol
    outright.

    Args:
        scenario: The scenario name, normally one of `SCENARIOS`.
        operation: `--operation` for both runners; each derives it from the
            scenario's own `operation` key when omitted.
        out_dir: The output root; `$ACAS_OUT` when omitted.
        max_differences: Passed to stage 8. It truncates the report only and never
            changes the verdict.

    Returns:
        The complete run.

    Raises:
        HarnessFaultError: A stage whose failure destroys the evidence failed -
            seed, reset, either dump, either normalisation, or the comparison itself
            with exit 2.
        ValueError: `scenario` or `operation` is not valid.
        FileNotFoundError: The scenario definition is absent.
    """
    assert_scenario_name(scenario)
    if operation is not None:
        assert_operation(operation)

    tables = scenario_affected_tables(scenario)
    paths = scenario_paths(scenario, out_root=out_dir)
    stages: list[StageResult] = []

    # STAGE 1. A failed seed poisons every downstream comparison, so it raises.
    stages.append(seed(scenario).raise_for_status())

    # STAGE 2. THE STATUS IS RECORDED, NOT ENFORCED - see the section comment.
    cobol_run = run_cobol(scenario, operation=operation)
    stages.append(cobol_run)

    # STAGES 3 and 4. Taken WHATEVER stage 2 returned: absence is evidence.
    stages.append(dump(scenario, SIDE_COBOL, out_dir=out_dir).raise_for_status())
    stages.append(
        normalize(scenario, SIDE_COBOL, out_dir=out_dir).raise_for_status()
    )

    # STAGE 5. Both cycles must start from byte-for-byte the same seeded state.
    stages.append(reset(scenario).raise_for_status())

    # STAGE 6. Same treatment as stage 2: exit 5 and exit 8 are term codes.
    python_run = run_python(scenario, operation=operation)
    stages.append(python_run)

    # STAGES 7 and 7b.
    stages.append(dump(scenario, SIDE_PYTHON, out_dir=out_dir).raise_for_status())
    stages.append(
        normalize(scenario, SIDE_PYTHON, out_dir=out_dir).raise_for_status()
    )

    # STAGE 8. Exit 2 raises inside `diff`; exit 1 returns a non-empty TreeDiff.
    outcome = diff(scenario, out_dir=out_dir, max_differences=max_differences)
    stages.append(outcome.result)

    return ParityRun(
        scenario=scenario,
        tables=tables,
        stages=tuple(stages),
        cobol_run=cobol_run,
        python_run=python_run,
        outcome=outcome,
        paths=paths,
    )


# The two output roots a determinism pair uses, composed UNDER `$ACAS_OUT` so that
# each run keeps the canonical `<scenario>/<side>[.normalized]/` shape and the two
# never overwrite one another. Only documented flags are used to get there -
# `--out-dir` plus `--scenario` and `--side` - so nothing about the layout is
# invented.
DETERMINISM_SUBDIR: Final[str] = "determinism"
DETERMINISM_LABELS: Final[tuple[str, str]] = ("run1", "run2")


@dataclass(frozen=True)
class DeterminismRun:
    """Two runs of one scenario under the same pinned clock, and their comparison.

    The acceptance condition of Agent Action Plan section 0.8.5: "Two runs of the
    same scenario under the same pinned clock produce byte-identical dumps." It holds
    because the twelve in-scope programs contain zero clock reads and receive the date
    through linkage, so pinning `to-day` and `Run-Date`
    [copybooks/wssystem.cob:L67] at the command-line boundary is sufficient.

    Attributes:
        scenario: The scenario name.
        tables: The affected-table list both runs were bounded by.
        pin: The pinned run date both runs used - the same object, so there is no
            question of the two having been pinned differently.
        stages: Every stage result, in execution order.
        first_run: The first run's result.
        second_run: The second run's result.
        tree: The `TreeDiff` between the two normalised trees. `is_empty` is the
            pass condition.
        first_normalized: The first run's normalised tree, reported as `cobol`.
        second_normalized: The second run's normalised tree, reported as `python`.
    """

    scenario: str
    tables: tuple[str, ...]
    pin: acas_clock.PinnedRunDate
    stages: tuple[StageResult, ...]
    first_run: StageResult
    second_run: StageResult
    tree: Any
    first_normalized: Path
    second_normalized: Path

    @property
    def is_empty(self) -> bool:
        """THE PASS CONDITION - two runs produced byte-identical state.

        Returns:
            True when nothing differs between the two runs.
        """
        return bool(self.tree.is_empty)


def run_determinism_pair(
    scenario: str,
    *,
    operation: str | None = None,
    out_dir: Path | str | None = None,
) -> DeterminismRun:
    """Run the migrated cycle TWICE from the same seed and compare the two states.

    Composed from the individual stages - seed, run, dump, normalize, reset, seed,
    run, dump, normalize, compare - WITHOUT the COBOL side, which is the composition
    tests/determinism/ needs. Both runs use the same scenario, so both receive the
    same pinned run date through linkage; that pin is returned so a test can assert
    it rather than assume it.

    WHY PINNING TWO OBSERVABLES IS SUFFICIENT: every one of the twelve in-scope
    programs contains ZERO clock reads, there is no random seed anywhere in the
    cycle, and the dump has no ordering nondeterminism because every in-scope table
    has a single-column primary key and no secondary index. So two runs under one
    pinned clock must be byte-identical, and a difference is a real defect.

    NOTE ON THE REPORT'S LABELS: `harness/diff_states.py` has exactly two, `cobol`
    and `python`, and they are not configurable. In this comparison `cobol` means the
    FIRST run and `python` the SECOND.

    Args:
        scenario: The scenario name.
        operation: `--operation` for the runner; derived from the scenario when
            omitted.
        out_dir: The output root; `$ACAS_OUT` when omitted.

    Returns:
        The pair and their comparison.

    Raises:
        HarnessFaultError: A stage whose failure destroys the evidence failed.
        ValueError: `scenario` or `operation` is not valid.
        FileNotFoundError: The scenario definition is absent.
    """
    assert_scenario_name(scenario)
    if operation is not None:
        assert_operation(operation)

    tables = scenario_affected_tables(scenario)
    definition = scenario_definition(scenario)

    # The scenario's own declared run date, so the pin returned is the pin the runs
    # actually used. `pinned_clock_from` does not validate the text - `maps04` alone
    # judges it - and a rejected date arrives as run_date 0 (anomaly #16).
    declared_text = definition.get(SCENARIO_KEY_RUN_DATE_TEXT)
    pin = pinned_clock_from(
        PINNED_RUN_DATE_TEXT if declared_text is None else str(declared_text)
    )

    root = output_root() if out_dir is None else Path(out_dir).resolve()
    first_root = root / DETERMINISM_SUBDIR / DETERMINISM_LABELS[0]
    second_root = root / DETERMINISM_SUBDIR / DETERMINISM_LABELS[1]

    stages: list[StageResult] = []
    runs: list[StageResult] = []
    for index, side_root in enumerate((first_root, second_root)):
        # A fresh seed before EACH run, so the second starts from byte-for-byte the
        # state the first did. The first pass seeds directly; the second resets, which
        # re-applies the frozen schema verbatim and re-seeds from the same fixture.
        if index == 0:
            stages.append(seed(scenario).raise_for_status())
        else:
            stages.append(reset(scenario).raise_for_status())

        run = run_python(scenario, operation=operation)
        stages.append(run)
        runs.append(run)

        stages.append(
            dump(scenario, SIDE_PYTHON, out_dir=side_root).raise_for_status()
        )
        stages.append(
            normalize(scenario, SIDE_PYTHON, out_dir=side_root).raise_for_status()
        )

    first_normalized = scenario_paths(
        scenario, out_root=first_root
    ).python_normalized
    second_normalized = scenario_paths(
        scenario, out_root=second_root
    ).python_normalized

    tree = diff_trees_directly(first_normalized, second_normalized, tables)

    return DeterminismRun(
        scenario=scenario,
        tables=tables,
        pin=pin,
        stages=tuple(stages),
        first_run=runs[0],
        second_run=runs[1],
        tree=tree,
        first_normalized=first_normalized,
        second_normalized=second_normalized,
    )


@dataclass(frozen=True)
class Protocol:
    """Every protocol stage and both compositions, as one injectable object.

    This is what Agent Action Plan section 0.4.3 asks of this file: the seed, dump,
    normalize and diff helpers gathered in one place "so that no test reimplements
    the comparison protocol".

    Handed to a test through the `protocol` fixture, so that a test file needs no
    import of this module and cannot accidentally reach a private helper. Frozen,
    because a protocol whose stages could be swapped mid-session would let two tests
    in one run mean different things by "the diff".

    Attributes:
        seed: Stage 1.
        run_cobol: Stage 2 - the compiled oracle.
        dump: Stages 3 and 7.
        normalize: Stage 4, and again after 7.
        reset: Stage 5.
        run_python: Stage 6 - the migrated cycle.
        diff: Stage 8; its `DiffOutcome.is_empty` is the pass condition.
        run_scenario_parity: All eight, in order.
        run_determinism_pair: Two Python runs, compared.
        classify_run: Success, behavioural difference or harness fault.
        paths: The canonical layout for one scenario.
        affected_tables: The list a comparison is bounded by.
        definition: One scenario's parsed YAML.
    """

    seed: Callable[..., StageResult]
    run_cobol: Callable[..., StageResult]
    dump: Callable[..., StageResult]
    normalize: Callable[..., StageResult]
    reset: Callable[..., StageResult]
    run_python: Callable[..., StageResult]
    diff: Callable[..., DiffOutcome]
    run_scenario_parity: Callable[..., ParityRun]
    run_determinism_pair: Callable[..., DeterminismRun]
    classify_run: Callable[..., str]
    paths: Callable[..., ScenarioPaths]
    affected_tables: Callable[[str], tuple[str, ...]]
    definition: Callable[[str], Mapping[str, Any]]



# ---------------------------------------------------------------------------
#  SECTION 11  -  THE FIXTURES
#
#  NOTHING BELOW REGISTERS A MARKER, and there is deliberately no
#  `pytest_configure`, no `pytest_plugins` list and no
#  `pytest_collection_modifyitems`. pyproject.toml declares all five markers, each
#  test file applies its own `pytestmark`, and NO FIXTURE IS AUTOUSE: an autouse
#  fixture that reached the database would drag the infrastructure requirement into
#  the arithmetic tier, which must run on a bare host.
#
#  Every fixture that needs the stack calls `requires_stack()` FIRST, so a bare host
#  gets a precise SKIP instead of an error.
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """The repository root, resolved from this file's own location.

    Agent Action Plan section 0.8.3 keeps the Python tree in the SAME repository as
    the frozen COBOL, so one root holds both - which is why a test can reach
    mysql/ACASDB.sql and copybooks/ from here at all, and why nothing may write into
    them (Agent Action Plan section 0.8.1).

    Returns:
        The absolute path, asserted at import to hold mysql/ACASDB.sql, harness/,
        acas_posting/ and copybooks/.
    """
    return REPO_ROOT


@pytest.fixture(scope="session")
def pinned_clock() -> acas_clock.PinnedRunDate:
    """The project-wide pinned run date, as both observables (rule R-6).

    Session-scoped, because there is exactly one pinned date for the project and a
    per-test clock would invite two tests to pin two different ones.

    BOTH OBSERVABLES ARE ASSERTED HERE - the text `21/09/2025` and the binary
    `Run-Date` 155127 [copybooks/wssystem.cob:L67] - which catches an epoch
    regression in acas_posting/dates.py at the fixture rather than three tables into
    a diff, where a one-day shift in `SYSTEM-REC.RUN-DAT` would look like a posting
    difference.

    Returns:
        The pinned pair.
    """
    pin = pinned_clock_from(PINNED_RUN_DATE_TEXT)
    assert_pin_matches_project_default(pin)
    # The pair's own internal consistency, checked through the same `maps04` both
    # directions use. Diagnostic only: no COBOL site checks that the two observables
    # agree, because [copybooks/Proc-ACAS-Mapser-RDB.cob:L80] stores the conversion
    # result without inspecting it.
    acas_clock.verify_pin(pin)
    return pin


@pytest.fixture(scope="session")
def pinned_clock_factory() -> Callable[[str], acas_clock.PinnedRunDate]:
    """A factory for a second pinned clock, from caller-supplied `to-day` text.

    For tests/determinism/ and any scenario overriding the YAML date. A REJECTED DATE
    DOES NOT RAISE - it arrives as `run_date == 0`, which is anomaly #16 reproduced,
    not an error to be improved on (rule R-4).

    Returns:
        `pinned_clock_from`.
    """
    return pinned_clock_from


@pytest.fixture(scope="session")
def harness() -> HarnessModules:
    """The three harness Python modules, loaded by explicit file path (rule R-1).

    Loaded on first use rather than at import, so the arithmetic tier never touches
    them. Loading needs no Docker, no MariaDB and no GnuCOBOL: two of the three are
    pure and the third opens a connection only when `connect()` is called.

    Returns:
        The three modules.
    """
    return load_harness_modules()


@pytest.fixture(scope="session")
def frozen_schema(harness: HarnessModules) -> Mapping[str, Mapping[str, Any]]:
    """The parsed frozen schema, `{table: {column: ColumnType}}`.

    A FILE READ AND NOTHING MORE - `mysql/ACASDB.sql` is read, never written (Agent
    Action Plan section 0.8.1). `load_schema` also asserts the frozen inventory, so a
    modified schema fails here loudly rather than drifting quietly.

    Args:
        harness: The loaded harness modules.

    Returns:
        The column-type map, 33 tables, each inner mapping in schema ordinal order.
    """
    return harness.normalize.load_schema(SCHEMA_SQL_PATH)


@pytest.fixture(scope="session")
def in_scope_table_names(harness: HarnessModules) -> tuple[str, ...]:
    """The 22 in-scope table names, ascending.

    Read from `harness/dump_tables.py`'s `IN_SCOPE_TABLES`, never restated: the
    inventory has exactly one definition in this repository (rule R-4).

    Args:
        harness: The loaded harness modules.

    Returns:
        The names, hyphens included.
    """
    return tuple(harness.dump_tables.IN_SCOPE_TABLES)


@pytest.fixture(scope="session")
def harness_stack_status() -> StackStatus:
    """Whether the harness Compose stack is usable. DOES NOT SKIP.

    For a test that wants to reason about the environment rather than be skipped by
    it. Use the `require_stack` fixture, or call `requires_stack()`, to skip.

    Returns:
        The status, probed once per session.
    """
    return stack_status()


@pytest.fixture
def require_stack() -> Callable[[], None]:
    """A callable that skips the test unless the harness stack is usable.

    A SKIP, NOT A FAILURE. This is what lets `pytest -m arithmetic` succeed on a host
    with no Docker, no MariaDB and no GnuCOBOL - the direct test of the three-tier
    design.

    Returns:
        `requires_stack`.
    """
    return requires_stack


@pytest.fixture
def db_connection() -> Iterator[Any]:
    """ONE open read-only connection to the seeded database, for the test's duration.

    Reached through `harness/dump_tables.py`'s `connect`, which resolves the
    `ACAS_DB_*` environment [copybooks/wsfnctn.cob:L56-L62] and pins the driver's
    conversion so DECIMAL arrives as `decimal.Decimal` and every integer width as
    `int` (rule R-2). A SINGLE CONNECTION: no pool, no engine, no SQLAlchemy, no
    thread (rule R-3) - "execution is strictly sequential, matching the
    single-threaded COBOL".

    Skips when the stack is unavailable, and asserts the mandated autocommit mode
    before yielding, so a test never reads a database seeded under the wrong one.

    Yields:
        The open DB-API connection. Released with `rollback()` and closed on exit,
        because this path only ever reads.
    """
    requires_stack()
    dump_tables = harness_dump_tables()
    with dump_tables.connect() as connection:
        assert_autocommit_off(connection)
        yield connection


@pytest.fixture
def seeded_database(
    require_stack: Callable[[], None],
) -> Callable[[str], StageResult]:
    """A factory that seeds the database for one named scenario. STAGE 1.

    A FACTORY rather than a plain fixture, because the seed is scenario-specific: the
    scenario is BINDING, and `harness/seed.sh` stages that scenario's declared
    `seed_files` into a fresh scenario-owned fixture and seeds from exactly those, so
    the resulting state is provably attributable to the scenario it is credited to.
    Invokes `harness/seed.sh` and NEVER `common/masterLD.sh`, which its own author
    marks untested [common/masterLD.sh:L4-L5] and which is not valid shell.

    Args:
        require_stack: The skip guard, applied before anything is run.

    Returns:
        A callable taking a scenario name and returning the seed stage's result,
        raising `HarnessFaultError` if the seed failed - a poisoned seed makes every
        downstream difference unattributable.
    """
    require_stack()

    def _seed(scenario: str) -> StageResult:
        """Seed the database from one scenario's declared fixture.

        Args:
            scenario: The scenario whose `seed_files` bind the load.

        Returns:
            The seed stage's result.

        Raises:
            HarnessFaultError: The seed failed - see `raise_for_status`.
        """
        return seed(scenario).raise_for_status()

    return _seed


@pytest.fixture
def protocol(require_stack: Callable[[], None]) -> Protocol:
    """Every protocol stage and both compositions, as one object.

    THE FIXTURE THAT MAKES "no test reimplements the comparison protocol" TRUE
    (Agent Action Plan section 0.4.3). A scenario test reads:

        def test_clean_batch_post_gl(protocol):
            assert protocol.run_scenario_parity("clean_batch_gl").is_empty

    and a determinism test composes the individual stages, or uses
    `protocol.run_determinism_pair`.

    Args:
        require_stack: The skip guard, applied before any stage can run.

    Returns:
        The protocol object.
    """
    require_stack()
    return Protocol(
        seed=seed,
        run_cobol=run_cobol,
        dump=dump,
        normalize=normalize,
        reset=reset,
        run_python=run_python,
        diff=diff,
        run_scenario_parity=run_scenario_parity,
        run_determinism_pair=run_determinism_pair,
        classify_run=classify_run,
        paths=scenario_paths,
        affected_tables=scenario_affected_tables,
        definition=scenario_definition,
    )


@pytest.fixture(scope="session")
def scenario_loader() -> Callable[[str], Mapping[str, Any]]:
    """A loader for one scenario definition, parsed with `yaml.safe_load`.

    Needs no stack: a scenario definition is a file on disk. ONLY THE KEYS THE
    HELPERS CONSUME ARE CHECKED FOR PRESENCE and nothing is interpreted, because
    judging a scenario's declared contents would be the added validation rule R-3
    forbids.

    Returns:
        `scenario_definition`.
    """
    return scenario_definition


@pytest.fixture(scope="session")
def data_dictionary_path() -> Path:
    """The generated data dictionary's path.

    THE ONE FILE-SYSTEM PREREQUISITE OF THE INFRASTRUCTURE-FREE TIER: every
    acas_posting.records module builds its field descriptors from it during a normal
    import, so a checkout without it cannot import the record layer at all. That is a
    file-system dependency and not an infrastructure one, which is why the arithmetic
    tier still runs anywhere.

    Returns:
        The path.

    Raises:
        AssertionError: The dictionary is absent.
    """
    assert DATA_DICTIONARY_PATH.is_file(), (
        f"the generated data dictionary is absent from {DATA_DICTIONARY_PATH}. "
        f"Every acas_posting.records module reads it at import to build its field "
        f"descriptors, so nothing in the arithmetic tier can run without it. "
        f"Regenerate it with `python -m acas_posting.dictionary.generate`."
    )
    return DATA_DICTIONARY_PATH

