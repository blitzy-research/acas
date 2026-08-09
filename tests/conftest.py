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

THE SIX BINDING RULES R-1 to R-6 live in Agent Action Plan section 0.7.2, and their
exact wording is retrievable from the requirements via `review_prompt`. Summarised, in
this module's own words, and each named at the site that honours it:

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
import re
import subprocess
import sys
import uuid
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
# where R-1 stops being a promise and becomes a fact, and pyproject.toml turns
# package discovery OFF, listing the eight packages that ship one line each -
# the seven code packages plus the data-only `acas_posting.data_dictionary` that
# carries the generated dictionary into the wheel. `harness*`, `tests*` and
# `docs*` are absent because they are not listed, so they cannot reach a
# distribution at all.
HARNESS_DIR: Final[Path] = REPO_ROOT / "harness"

# The scenario definitions - the eight Agent Action Plan section 0.4.1.7 mandates, and
# exactly those (see SCENARIOS). Created by
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
# (rule R-6). Named so that a failure message or a reader can find them.
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

#: THERE IS NO SEPARATE PROTOCOL DRIVER, and no script runs the ten stages from one
#: invocation. The tests COMPOSE the ten stages themselves - see
#: `_run_scenario_parity_stages` - so that each stage's status is available individually.
#: The three gates a single driver would own live in the stages whose state they protect: the oracle-provenance gate and the
#: seed-file pre-flight in `harness/reset_db.sh` (which is where a refusal happens before
#: a table is dropped), and the cross-side operations check in
#: `harness/run_cobol_scenario.sh` (before the first operation produces state). A
#: hand-driven operator therefore runs the four scripts above and the three Python tools
#: directly, in the order `README-python-migration.md` section 8 sets out, and is guarded
#: at each stage by that stage itself rather than by a wrapper.

#: The module that OWNS the canonical stage registry. The rows
#: were a shell file of its own; they are now `PARITY_STAGES` in `harness/normalize.py`,
#: published to shell through `--print-stage-shell` and to everything else through
#: `--print-stages`. Read through that published interface rather than parsed, so this
#: module depends on the interface and not on the owner's syntax.
STAGE_REGISTRY_SCRIPT: Final[Path] = HARNESS_DIR / "normalize.py"

# ---------------------------------------------------------------------------
#  SECTION 2  -  THE ENVIRONMENT CONTRACT
#
#  Names only. The VALUES are resolved and validated by
#  harness/dump_tables.py's `connection_settings`, which is the single authority
#  and raises `ConnectionConfigError` with the authoritative message; this module
#  never re-implements that validation (R-4).
#
#  The database half derives from `03 RDB-Data.` [copybooks/wsfnctn.cob:L56-L62]:
#  05  DB-Schema   pic x(12)     05  DB-Host     pic x(32)
#  05  DB-UName    pic x(12)     05  DB-Socket   pic x(64)
#  05  DB-UPass    pic x(12)     05  DB-Port     pic x(5)
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
ENV_FIXTURES: Final[str] = "ACAS_FIXTURES"
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

# THE ONE RUN ID EVERY STAGE OF ONE PROTOCOL RUN CARRIES.
#
# ONE id is minted and exported before stage 1, which is how all ten stages come to
# agree - by this module for the composed protocol and by the operator for a
# hand-driven one; both runners read it, and
# `harness/dump_tables.py` records it into each capture's provenance. When it is
# ABSENT each runner derives its own `local-<hex>` id instead - so a protocol composed
# stage by stage, as `run_scenario_parity` composes it, gave the two sides two
# DIFFERENT ids and `harness/diff_states.py` then refused the pair outright, because
# PROVENANCE_MUST_MATCH names `run_id' and two captures of different runs are not two
# sides of one comparison. `harness/reset_db.sh` publishes the seed identity under the
# same id and `acas_read_seed_identity` DISCARDS a record staged by another attempt,
# so an unbound protocol also loses the seed marker the two sides must share.
# Binding it here is therefore not a convenience: it is what makes the composed
# protocol and a hand-driven one the same protocol.
ENV_PARITY_RUN_ID: Final[str] = "ACAS_PARITY_RUN_ID"

# The prefix this module mints under. A hand-driven run exports its own id - `parity-`
# is the documented convention, README section 8 - and a runner invoked with none
# derives `local-`, so a third prefix keeps the composed protocol
# distinguishable in a retained artifact without any tool having to special-case it:
# nothing validates the prefix, only the shape `^[A-Za-z0-9._-]{1,64}$`.
RUN_ID_PREFIX: Final[str] = "pytest-"
# THE ACCEPTANCE MODE. Set it to any of the affirmative spellings below and an
# unusable stack becomes a FAILURE instead of a skip, so that an acceptance run
# cannot report green having skipped the entire oracle tier. UNSET, the default,
# keeps the skip, which is what lets `pytest -m arithmetic` succeed on a host with
# no Docker, no MariaDB and no GnuCOBOL - the direct test of the three-tier design.
#
# It changes only the DISPOSITION of a missing precondition and never what counts as
# one: the enumerated list in `_probe_stack` is the same either way.
ENV_REQUIRE_ORACLE: Final[str] = "ACAS_REQUIRE_ORACLE"

#: The spellings `ENV_REQUIRE_ORACLE` accepts as "yes". Anything else, including an
#: empty value, leaves the default skip in place.
_AFFIRMATIVE: Final[frozenset[str]] = frozenset({"1", "true", "yes", "on"})

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
#  THE SINGLE MOST IMPORTANT MECHANICAL FACT IN THIS FILE: nothing the SHIPPED
#  package imports can reach harness/. That is enforced by pyproject.toml's
#  `[tool.setuptools] packages = [...]` list, which enumerates the eight packages
#  that ship - the seven code packages and the data-only
#  `acas_posting.data_dictionary` - with include-package-data = false and no
#  discovery scan at all; `harness*`, `tests*` and `docs*` are absent because
#  nothing names them, so harness is absent by construction rather than filtered
#  out. There is therefore DELIBERATELY no import path from the shipped
#  package to the compiled oracle (R-1).
#
#  ONE ARGUMENT IS DELIBERATELY NOT MADE HERE, BECAUSE IT IS FALSE. An earlier
#  revision of this comment said a package-style import "FAILS AT COLLECTION ...
#  because the directory is not a package". It does not fail. PEP 420 makes a
#  directory without __init__.py an implicit NAMESPACE package, and the documented
#  run command is `python -m pytest`, which puts the invocation directory on
#  sys.path[0] -- so `import harness.normalize` resolves from the repository root
#  and returns harness/normalize.py. That was measured in this checkout, not
#  assumed. The absence of __init__.py is consequently NOT the enforcement
#  mechanism; the allow-list above is.
#
#  A PACKAGE-STYLE IMPORT IS NEVERTHELESS NOT USED, and the reason is positive
#  rather than a claim about what cannot work. Loading BY EXPLICIT FILE PATH is
#  independent of sys.path, of the invocation directory and of whether the
#  repository root happens to be importable, so the fixtures behave identically
#  under `python -m pytest`, under a bare `pytest`, and from any cwd. It also lets
#  each module be registered under a NAMESPACED sys.modules key (see below), which
#  a namespace import cannot do. That is the only mechanism this module uses.
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

# The harness Python modules this suite loads, by file name without the extension:
# the three state tools a test drives.
#
# THERE IS NO FOURTH ENTRY ANY MORE. The one duplicate-rejecting scenario
# parser was `harness/normalize.py`, a path the Agent Action Plan section 0.3.1
# harness inventory does not name. It now lives in `harness/normalize.py` beside the
# other definitions every consumer must agree on, so loading `normalize` loads the
# parser too and there is no separate module left to keep in step.
HARNESS_MODULE_NAMES: Final[tuple[str, ...]] = (
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
        ValueError: `name` is not one of the loadable harness modules.
        FileNotFoundError: The file is absent. The message carries the full
            expected path and says plainly that the harness tree has not been
            created, because that is the whole diagnosis.
        ImportError: The file exists but could not be turned into a module.
    """
    if name not in HARNESS_MODULE_NAMES:
        raise ValueError(
            f"{name!r} is not a harness Python module. The loadable ones are "
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
    """The `harness/diff_states.py` module - protocol stage 10 (rule R-1).

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

    The three that implement stages 3, 4, 7, 8 and 10 of the ten-stage parity protocol
    the canonical recipe in harness/docker-compose.yml publishes. Each is loaded by
    explicit file path, never imported as a package.

    Frozen because a fixture that could be re-pointed at a different module would
    let two tests in one session compare against two different definitions of the
    protocol.

    Attributes:
        dump_tables: `harness/dump_tables.py` - stages 3 and 7.
        normalize: `harness/normalize.py` - stage 4.
        diff_states: `harness/diff_states.py` - stage 10.
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
#  purely through linkage. That zero, and not any claim about how many reads the
#  system holds, is what makes two observables sufficient. The reads themselves are
#  MANY and all outside the migrated surface: the menu shells' shared date-service
#  copybook [copybooks/Proc-ACAS-Mapser-RDB.cob:L72-L80] holds one, each of the four
#  menu shells holds one of its own - [general/general.cbl:L371],
#  [sales/sales.cbl:L323], [purchase/purchase.cbl:L318], [irs/irs.cbl:L480] - and
#  `tests/determinism/test_two_runs_byte_identical.py` carries the full fourteen-site
#  census, `accept ... from date` and `from time` included.
#  So the controlled clock pins exactly these and nothing deeper:
#
#  1. THE TEXT DATE, `to-day pic x(10)` in DD/MM/CCYY form. It is the 3rd
#  parameter of the General-Ledger linkage shape and the 4th of the
#  Sales/Purchase shape. The IRS shape takes NEITHER `to-day` NOR the
#  calling-data block: [irs/irs030.cbl:L552-L554] is
#  `using IRS-System-Params, WS-System-Record, File-Defs`.
#  2. THE BINARY RUN DATE, declared `05  Run-Date        binary-long.` at
#  [copybooks/wssystem.cob:L67]. It is a real SYSTEM-REC column
#  (`RUN-DAT int(8) unsigned`), and it reaches the EVIDENCE by four independent
#  routes: SYSTEM-REC is itself one of the 22 dumped tables, so the column is
#  compared by value; every date column the cycle stamps in the other tables derives
#  from it (`GLBATCH-REC.POSTED` [general/gl072.cbl:L376], `GLPOSTING-REC.POST-DAT`,
#  `PSIRSPOST-REC.IRS-POST-DAT`); both runners read the column back after the run
#  and refuse a value other than the pin; and both fingerprint SYSTEM-REC before
#  and after. A drifting clock therefore cannot pass unseen.
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
    [copybooks/Proc-ACAS-Mapser-RDB.cob:L78]. That is ANOMALY A-16, and
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
    reproduces [copybooks/Proc-ACAS-Mapser-RDB.cob:L72-L80] with that copybook's
    clock read replaced by this argument. It is the date service's read, not the
    system's only one - see SECTION 5's note.

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
#  $ACAS_OUT/<scenario>/<side>/<TABLE>.json                side: cobol | python
#  $ACAS_OUT/<scenario>/<side>.normalized/<TABLE>.json
#  $ACAS_OUT/<scenario>/diff.txt
#  $ACAS_OUT/run-logs/<scenario>/{cobol.log,python.log,...}
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

# The pre-run and post-run state fingerprints, written INSIDE `run-logs/` and
# therefore outside every compared tree.
#
# ONE LINE PER AFFECTED TABLE, IN THE SCENARIO'S DECLARED ORDER, AND THREE FIELDS:
#
#  <TABLE>\t<row count>\t<sha256 of the canonical dump>
#
# THE DIGEST IS THE THIRD FIELD AND IT IS WHAT MAKES THE RECORD MEAN ANYTHING. A row
# count alone cannot tell two different seeds apart: swap one balance, alter one
# status, load a different fixture with the same shape, and the counts agree while the
# starting states do not - and then every downstream difference, or its absence, is
# unattributable. The digest is taken by `harness/dump_tables.py --table-digest` over the canonical
# text `harness/dump_tables.py` itself writes, so it covers EVERY BOUNDED TABLE AND
# EVERY ROW at the declared scale, and BOTH SIDES COMPUTE IT WITH THE SAME PROGRAM -
# which is the only way two independently produced digests can be compared byte for
# byte at all.
#
# Both runners write the pre-run record immediately before dispatch and the post-run
# record immediately after it. The pre-run pair proves the two cycles were handed the
# same starting state (`assert_seed_fingerprints_agree`); the pre-run against post-run
# comparison proves a run CHANGED something, which is what stops two no-ops passing a
# determinism or an empty-batch claim (`assert_tables_unchanged_by_run`).
SEED_FINGERPRINT_PYTHON: Final[str] = "python.seed-fingerprint"
SEED_FINGERPRINT_COBOL: Final[str] = "cobol.seed-fingerprint"
#  THE MENU-PERSISTED PARAMETER ROW. `overrewrite' rewrites SYSTEM-REC key 1 on
#  all four subsystems - [general/general.cbl:L656-L672], [sales/sales.cbl:L628-L641],
#  [purchase/purchase.cbl:L621-L634], [irs/irs.cbl:L759-L774] - and the migrated
#  command line REPRODUCES that paragraph [acas_posting/cli/args.py]. Both cycles
#  therefore write it on every route.
#
#  IT IS ON EVERY SCENARIO'S AFFECTED-TABLE LIST AND IN EVERY CAPTURE, and the one
#  problem a dump does have is solved where it arises rather than by dropping the table.
#  The row carries `RDBMS-PASSWD char(12)' [copybooks/wssystem.cob:L139] and `PASS-WORD',
#  and a capture is committed evidence, so `harness/dump_tables.py' withholds exactly
#  those two cells through `REDACTED_COLUMNS' inside `render_value' - keyed by
#  (table, column), applied identically on both sides, and therefore incapable of
#  producing a difference of its own. The other 167 columns are compared by value.
#  Bounding the whole table out instead would have taken those 167 with it, and a bound
#  drawn that way cannot reveal a difference in what it excludes.
#
#  The second-order worry was MEASURED rather than assumed: the row's content depends on
#  what the route DID - the run-date stamp, the IRS allocator, the one-shot latches, and
#  `Date-Form', itself a SYSTEM-REC column [copybooks/wssystem.cob:L127] that the frozen
#  date sections write back - so declaring it could in principle tie a scenario's effect
#  claim to fields it does not reason about. It does not: the digest moves on exactly the
#  five scenarios declaring `changed' and holds on the four declaring `unchanged'.
#
#  So both runners ALSO FINGERPRINT it, appended after the declared order, and this
#  module compares the two sides' records. That is a second, independent parity check over
#  all 169 columns, credentials included, with nothing to leak: a sha256 of the canonical
#  dump is not the dump, so even the two withheld cells are compared.
#  `assert_system_record_parity` is the assertion; `assert_tables_unchanged_by_run`
#  reads the same records for the mutation witness.
PARAMETER_TABLE: Final[str] = "SYSTEM-REC"
POST_FINGERPRINT_PYTHON: Final[str] = "python.post-fingerprint"
POST_FINGERPRINT_COBOL: Final[str] = "cobol.post-fingerprint"

#: The three tab-separated fields of one fingerprint line.
FINGERPRINT_FIELDS: Final[int] = 3

#: What a fingerprint field holds when the table could not be read at all. A hyphen
#: and never a zero: "this table could not be counted" is a different fact from "this
#: table is empty", and both runners spell the unreadable case this way.
FINGERPRINT_UNREADABLE: Final[str] = "-"

#: The length of a SHA-256 in lower-case hexadecimal.
DIGEST_LENGTH: Final[int] = 64


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
            f"defaulted: the ten-stage protocol's output IS the evidence, and "
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


#: The four compiled menu executables the COBOL side drives, each built by the
#: maintainer's own per-directory script and living at `$ACAS_BUILD/<name>/<name>`.
#: The runner asserts the same four [harness/run_cobol_scenario.sh, check 5/8]; this
#: is the same list, checked BEFORE a scenario destroys the database rather than in
#: the middle of one.
ORACLE_MENUS: Final[tuple[str, ...]] = ("general", "sales", "purchase", "irs")

#: One dynamically loadable handler module per in-scope table family. `cobc -m`
#: produces `<name>.so`, and the menus `CALL` them by name through `$COB_LIBRARY_PATH`,
#: so a menu that exists without these loads and then fails at the first read. Four
#: representative handlers rather than all seventeen: they span the four families the
#: posting cycle reaches (system, general ledger, sales/purchase, IRS), so any of them
#: missing means the handler build did not complete.
ORACLE_HANDLER_MODULES: Final[tuple[str, ...]] = (
    "acas000",
    "acas006",
    "acas012",
    "acasirsub1",
)

#: The compatibility include supplying the copybook the frozen archive does not carry,
#: as it is named INSIDE THE BUILD COPY. It is not a repository file:
#: `harness/build_oracle.sh` GENERATE it at build time into `$ACAS_BUILD/copybooks`,
#: because a committed copy is a file a reader can mistake for archive material and
#: writing the member into `copybooks/` would be a fabricated frozen source (R-3, R-4,
#: AAP section 0.8.1). Its absence therefore no longer has a repository path to probe -
#: what the tier checks instead is the build's own provenance attestation, which records
#: this include as a registered source transformation, so a build carrying it reports
#: `oracle-source-is-frozen no` and the tier declines to call any result parity.
SQLSTATE_SHIM_BUILD_PATH: Final[str] = "copybooks/ACAS-SQLstate-error-list.cob"

#: `harness/build_oracle.sh`'s completion marker. Its presence says the build tree is
#: the one that script produced rather than a directory that happens to exist.
ORACLE_BUILD_MARKER: Final[str] = ".acas-build-oracle-tree"

#: `harness/seed.sh --build-fixtures`'s publish-last manifest. It is written LAST, so its
#: presence is what distinguishes a complete fixture from a partial one - which is
#: exactly why `harness/seed.sh` requires it too.
FIXTURE_MANIFEST: Final[str] = ".acas-fixture-manifest"


def _probe_compiled_oracle(
    missing: list[str], detail: list[str]
) -> None:
    """Check that the compiled COBOL oracle exists, appending any faults.

    Rule R-6 makes the compiled program the behavioural specification, so a scenario
    tier with no compiled program has nothing to compare against. Every fault is
    appended rather than raised, matching `_probe_stack`'s collect-everything
    contract: one skip message must tell the operator everything that is missing.

    Args:
        missing: The machine-readable fault list, appended to in place.
        detail: The human-readable lines, appended to in place.
    """
    build_root_name = (os.environ.get(ENV_BUILD) or "").strip()
    if not build_root_name:
        missing.append(f"env:{ENV_BUILD}")
        detail.append(
            f"  {ENV_BUILD} is unset or blank, so the compiled oracle cannot be "
            f"located. It names the build tree harness/build_oracle.sh writes and "
            f"harness/docker-compose.yml mounts"
        )
        return

    build_root = Path(build_root_name)
    if not build_root.is_dir():
        missing.append(f"dir:{ENV_BUILD}")
        detail.append(
            f"  {ENV_BUILD} names {build_root}, which is not a directory: the "
            f"oracle has never been built here. Run "
            f"`harness/build_oracle.sh` inside the gnucobol service"
        )
        return

    # The build script's own marker. Its absence does not by itself prove the
    # artifacts are missing, so it is reported as detail alongside whatever else is
    # found rather than short-circuiting the rest of the probe.
    if not (build_root / ORACLE_BUILD_MARKER).exists():
        missing.append("oracle:build-marker")
        detail.append(
            f"  {build_root / ORACLE_BUILD_MARKER} is absent, so this tree was not "
            f"published by harness/build_oracle.sh. Even if artifacts are present "
            f"they cannot be attributed to a completed build"
        )

    absent_menus: list[str] = []
    not_executable: list[str] = []
    for name in ORACLE_MENUS:
        candidate = build_root / name / name
        if not candidate.exists():
            absent_menus.append(str(candidate))
        elif not os.access(candidate, os.X_OK):
            not_executable.append(str(candidate))
    if absent_menus:
        missing.append("oracle:menus")
        detail.append(
            f"  {len(absent_menus)} of {len(ORACLE_MENUS)} compiled menu "
            f"executable(s) are absent: {', '.join(absent_menus)}. Every in-scope "
            f"posting program is a CALLed sub-program with group-item linkage and "
            f"cannot be invoked from a shell, so the menus ARE the oracle's "
            f"entry points (Agent Action Plan section 0.1.1)"
        )
    if not_executable:
        missing.append("oracle:menus-not-executable")
        detail.append(
            f"  compiled menu(s) present but not executable: "
            f"{', '.join(not_executable)}"
        )

    # The handler modules. `cobc -m` writes `<name>.so`; the menus resolve them by
    # name at run time, so a missing module is a failure at the first table read
    # rather than at start-up - which is why it is checked here.
    absent_modules = [
        name
        for name in ORACLE_HANDLER_MODULES
        if not _find_oracle_module(build_root, name)
    ]
    if absent_modules:
        missing.append("oracle:handler-modules")
        detail.append(
            f"  {len(absent_modules)} representative handler module(s) could not "
            f"be found under {build_root}: "
            f"{', '.join(f'{name}.so' for name in absent_modules)}. The menus CALL "
            f"these by name through $COB_LIBRARY_PATH, so without them the oracle "
            f"starts and then fails at its first table read"
        )

    # THERE IS NO SHIM FILE TO PROBE, AND THAT IS THE POINT.
    # `harness/build_oracle.sh` generates the comment-only compatibility include into
    # $ACAS_BUILD/copybooks/ACAS-SQLstate-error-list.cob at build time, so it cannot be
    # missing from a build that ran, and it is not a repository file that could be
    # deleted from the checkout. The condition that actually matters is the one the
    # provenance probe below reports: a build that generated it is a TRANSFORMED build,
    # `oracle-source-is-frozen no`, and therefore not the specification R-6 names.

    # THE ORACLE MUST BE THE FROZEN SPECIFICATION, NOT A REPAIRED ONE.
    #
    # Everything above establishes that an oracle EXISTS. None of it establishes that
    # the oracle is the thing R-6 makes the specification: the frozen checkout. A
    # build carrying source transformations has repaired executable logic - IF scope,
    # connection lifetime, credential propagation, stale reply pairs - so agreement
    # with it cannot show that the migrated cycle reproduces the frozen system. A
    # scenario tier that PASSED against such a build would publish a parity claim
    # nobody had measured, which is worse than a skip because a skip is visible.
    #
    # So the tier reports itself UNAVAILABLE, with the reason, and the reason names
    # the measured cause rather than a hypothesis. `harness/reset_db.sh` refuses
    # the same condition with exit 77 - before it drops a table - and this is the same
    # judgement at the tier boundary, so the two cannot disagree.
    _probe_oracle_is_frozen(build_root, missing, detail)


def _probe_oracle_is_frozen(
    build_root: Path, missing: list[str], detail: list[str]
) -> None:
    """Check the oracle was compiled from the frozen checkout, appending any faults.

    Reads `oracle-source-is-frozen` from the provenance attestation
    `harness/build_oracle.sh` publishes. Absent, unreadable or `no` all make the
    oracle tiers unavailable, because none of them supports a claim about the frozen
    specification.

    Set `ACAS_ACCEPT_TRANSFORMED_ORACLE=1` to run the tiers against a transformed
    build for diagnosis. That mirrors `harness/reset_db.sh
    --accept-transformed-oracle`, and like it, results obtained that way are not
    parity claims.

    Args:
        build_root: The oracle build tree, already known to be a directory.
        missing: The machine-readable fault list, appended to in place.
        detail: The human-readable lines, appended to in place.
    """
    if os.environ.get("ACAS_ACCEPT_TRANSFORMED_ORACLE", "").strip() == "1":
        return

    attestation = build_root / "oracle-attestation.txt"
    remedy = (
        "    A frozen build is the DEFAULT: run `harness/build_oracle.sh` with no "
        "flags.\n"
        "    ON THIS CHECKOUT THAT BUILD FAILS, measured: exit 74, because 22 frozen "
        "common/*MT.cbl\n"
        "    bridges COPY ACAS-SQLstate-error-list.cob and that member is absent from "
        "the checkout\n"
        "    and from presql2-latest.zip alike. It carries the SQLSTATE list the "
        "bridges document and\n"
        "    cannot be fabricated (R-3, R-4); it must be supplied by the maintainer. "
        "See\n"
        "    README-python-migration.md section 8.7 and "
        "docs/migration/scenario-diff-evidence.md section 0.\n"
        "    To run these tiers anyway, for DIAGNOSIS ONLY and with no parity claim, "
        "set\n"
        "    ACAS_ACCEPT_TRANSFORMED_ORACLE=1."
    )

    if not attestation.is_file():
        missing.append("oracle:attestation")
        detail.append(
            f"  {attestation} is absent, so nothing attests which bytes were "
            f"compiled. Under R-6 the compiled program IS the specification, so an "
            f"oracle of unrecorded provenance cannot support a parity claim.\n"
            f"{remedy}"
        )
        return

    frozen = ""
    transforms = ""
    try:
        for line in attestation.read_text(encoding="utf-8").splitlines():
            key, _, value = line.partition("\t")
            if key == "oracle-source-is-frozen":
                frozen = value.strip()
            elif key == "source-transforms":
                transforms = value.strip()
    except OSError as error:
        missing.append("oracle:attestation-unreadable")
        detail.append(
            f"  {attestation} could not be read ({error}), so the oracle's "
            f"provenance is unestablished.\n{remedy}"
        )
        return

    if frozen != "yes":
        missing.append("oracle:not-frozen")
        detail.append(
            f"  {attestation} records oracle-source-is-frozen="
            f"{frozen or '<absent>'}"
            + (f" with {transforms} transformed source path(s)" if transforms else "")
            + ". The oracle was NOT compiled from the frozen checkout, so an empty "
            "diff against it would show agreement with a partly REPAIRED "
            "specification rather than with the frozen one. That is not the "
            "question these tiers exist to answer, so they do not run.\n"
            f"{remedy}"
        )


def _find_oracle_module(build_root: Path, name: str) -> Path | None:
    """Locate one dynamically loadable handler module under the build tree.

    `harness/build_oracle.sh` follows the maintainer's own per-directory layout, so a
    module may sit at the tree root or under the directory its source came from. Both
    are accepted: this probe establishes that the module was BUILT, and the runner and
    `$COB_LIBRARY_PATH` own where it is looked up from.

    Args:
        build_root: `$ACAS_BUILD`.
        name: The module's program-id, for example `acas006`.

    Returns:
        The path found, or None.
    """
    candidates = [build_root / f"{name}.so", build_root / "common" / f"{name}.so"]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    # A single non-recursive sweep of the immediate subdirectories, so an unexpected
    # but legitimate layout is accepted without walking an arbitrarily deep tree.
    try:
        for entry in sorted(build_root.iterdir()):
            if entry.is_dir():
                candidate = entry / f"{name}.so"
                if candidate.is_file():
                    return candidate
    except OSError:
        return None
    return None


def _probe_built_fixtures(
    missing: list[str], detail: list[str]
) -> None:
    """Check that every scenario's fixture has been built, appending any faults.

    Stages 1 and 5 pass `--seed-dir` into `harness/reset_db.sh`, which drops and
    re-applies the frozen schema before it discovers the fixture is not there. So an
    unbuilt fixture destroys the database and then fails - and it fails identically
    for every scenario, which makes the whole tier look broken. Checked once, here.

    Args:
        missing: The machine-readable fault list, appended to in place.
        detail: The human-readable lines, appended to in place.
    """
    try:
        roots = {scenario: scenario_fixture_dir(scenario) for scenario in SCENARIOS}
    except HarnessFaultError as exc:
        missing.append("fixtures:root")
        detail.append(f"  {exc}")
        return

    unbuilt = sorted(
        scenario for scenario, root in roots.items() if not root.is_dir()
    )
    incomplete = sorted(
        scenario
        for scenario, root in roots.items()
        if root.is_dir() and not (root / FIXTURE_MANIFEST).is_file()
    )
    if unbuilt:
        missing.append("fixtures:unbuilt")
        detail.append(
            f"  {len(unbuilt)} of {len(SCENARIOS)} scenario fixture(s) have not "
            f"been built: {', '.join(unbuilt)}. Build them with "
            f"`harness/seed.sh --build-fixtures` (all scenarios) or "
            f"`harness/seed.sh --build-fixtures <scenario>`"
        )
    if incomplete:
        missing.append("fixtures:incomplete")
        detail.append(
            f"  {len(incomplete)} fixture director(ies) exist but carry no "
            f"{FIXTURE_MANIFEST}: {', '.join(incomplete)}. The manifest is written "
            f"LAST, so its absence means the build did not finish and the contents "
            f"cannot be trusted - harness/seed.sh refuses them for the same reason"
        )


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
    #  is most likely to hit: harness/run_python_scenario.sh is a planned
    #  deliverable (Agent Action Plan section 0.4.1.7) that arrives with the
    #  Python cycle it drives, and harness/docker-compose.yml says so in the
    #  canonical recipe itself.
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
            f"  {SCENARIO_DIR} is absent, so no scenario can be read; a scenario "
            f"definition is what bounds every comparison"
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
    #  ACAS_LEDGERS and ACAS_BIN must be NON-BLANK or every one of them displays a
    #  message, waits on an ACCEPT and stops
    #  [copybooks/Proc-Get-Env-Set-Files.cob:L20-L28] - operator trap 3, which
    #  looks exactly like a hung harness.
    for name in (ENV_REPO, ENV_DATA, ENV_BIN, ENV_LEDGERS):
        if not (os.environ.get(name) or "").strip():
            missing.append(f"env:{name}")
            detail.append(f"  {name} is unset or blank")

    # 5. harness/reset_db.sh's three destructive gates. NOT FABRICATED HERE - see
    #  ENV_RESET_CONSENT. The expected token is quoted in the message so the
    #  operator can copy it, which is the whole point of a target-scoped gate.
    #
    #  THE PAIR IS NOT IN THE SERVICE ENVIRONMENT, BY DESIGN, so an absent value
    #  here is the NORMAL state of any invocation that did not ask for it rather
    #  than a misconfigured stack. It used to be declared on the `gnucobol`
    #  service, where PID 1 and every `exec` session carried it; it is now passed
    #  per invocation to the two stages that administer the schema. The message
    #  therefore names the `-e` form to add rather than a variable to export,
    #  because exporting it in the wrong place is exactly what was removed.
    for name in (ENV_DB_ADMIN_USER, ENV_DB_ADMIN_PASSWORD):
        if not (os.environ.get(name) or "").strip():
            missing.append(f"env:{name}")
            detail.append(
                f"  {name} is unset; harness/reset_db.sh GATE 1 requires an "
                f"administrative account distinct from {ENV_DB_USER}. It is "
                f"deliberately absent from the gnucobol service environment, so "
                f"add `-e {ENV_DB_ADMIN_USER} -e {ENV_DB_ADMIN_PASSWORD}` to the "
                f"`docker compose run` that carries this pytest invocation, with "
                f"both exported in the invoking shell"
            )

    # 6. The database environment, resolved by the single authority.
    #
    #  ONLY THE ENUMERATED EXTERNAL-UNAVAILABILITY CONDITIONS ARE SKIPS, and the
    #  narrowing is the whole point. A blanket `except Exception` here turned every
    #  repository defect into a skip: a signature change in
    #  `connection_settings`, a `TypeError` from a renamed keyword, an `ImportError`
    #  from a broken harness module, a parser defect - each one made the WHOLE R-6
    #  tier green-with-skips, which is indistinguishable from a bare host and is the
    #  most expensive failure mode a test suite has. So `dump_tables`'s own
    #  `ConnectionConfigError` - which is what an absent or malformed `ACAS_DB_*`
    #  environment raises, and which carries the authoritative message - is a skip,
    #  an absent script is a skip, and EVERYTHING ELSE PROPAGATES. Raised out of
    #  `_probe_stack` it surfaces as a pytest ERROR from the fixture, which is what
    #  a defect in this repository must look like.
    settings = None
    dump_tables_module = None
    try:
        dump_tables_module = harness_dump_tables()
    except FileNotFoundError as exc:
        missing.append("script:dump_tables.py")
        detail.append(f"  {exc}")

    if dump_tables_module is not None:
        try:
            settings = dump_tables_module.connection_settings(os.environ)
        except dump_tables_module.ConnectionConfigError as exc:
            # The single authority's own diagnosis of an unusable environment. Its
            # message names the variable and what it wanted, so nothing is added.
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

        # 7. The server itself, and the RUNTIME autocommit mode - ON, per the
        #  settled half of docs/migration/ambiguity-resolutions.md#q-10; the
        #  OFF window belongs to harness/seed.sh and to nothing else. One
        #  connection, opened once per session (rule R-3: no pool, no thread).
        #
        #  AGAIN ENUMERATED, AND FOR THE SAME REASON. The four conditions below
        #  are the ways an EXTERNAL server can be unavailable to this process, and
        #  each is a legitimate skip. `AssertionError` is deliberately NOT among
        #  them: `assert_runtime_autocommit_on` failing means the server is
        #  reachable but configured in a way the protocol cannot use, which is a
        #  stack DEFECT rather than a stack absence, and it must be seen. Anything
        #  unlisted - a TypeError from a changed signature, an AttributeError from a
        #  renamed constant - propagates and becomes a pytest ERROR.
        try:
            with dump_tables_module.connect(settings) as connection:
                assert_runtime_autocommit_on(connection)
        except (
            dump_tables_module.ConnectionConfigError,
            dump_tables_module.InsecureTransportError,
            dump_tables_module.DriverUnavailableError,
            dump_tables_module.DumpTimeoutError,
            dump_tables_module.DumpError,
            OSError,
        ) as exc:
            missing.append("database")
            detail.append(f"  {type(exc).__name__}: {exc}")

    # 8. THE COMPILED ORACLE ITSELF.
    #
    #  THE DEFECT THIS CLOSES. Everything above establishes that the harness can
    #  REACH its inputs; none of it established that the thing being compared
    #  against exists. Against a checkout whose oracle had never been built, every
    #  check above passed, the tier declared itself available, and the failure
    #  surfaced as harness/run_cobol_scenario.sh exiting 74 in the middle of a test
    #  that had already reset and re-seeded the database. That is the worst place to
    #  discover it: the diagnosis is buried in a subprocess transcript and the
    #  database has been destroyed for nothing. A missing oracle is a precondition,
    #  so it is reported as one - with the command that builds it.
    _probe_compiled_oracle(missing, detail)

    # 9. THE BUILT FIXTURES. Same argument: stages 1 and 5 pass --seed-dir into the
    #  reset script, and a fixture root that was never built makes the FIRST
    #  destructive stage fail. Checked here, before anything is dropped.
    _probe_built_fixtures(missing, detail)

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


def oracle_is_required() -> bool:
    """Is this an ACCEPTANCE run, in which a skipped oracle tier is a failure?

    Returns:
        True when `ACAS_REQUIRE_ORACLE` carries an affirmative spelling.
    """
    return (os.environ.get(ENV_REQUIRE_ORACLE) or "").strip().lower() in _AFFIRMATIVE


def requires_stack() -> None:
    """Skip - or, in acceptance mode, FAIL - unless the harness stack is usable.

    A SKIP AND NOT A HARD FAILURE BY DEFAULT, deliberately: it is what lets
    `pytest -m arithmetic` succeed on a host with no Docker, no MariaDB and no
    GnuCOBOL, which is the direct test of the three-tier design. The reason names
    every missing precondition, so an operator is not told one thing at a time.

    AND AN ACCEPTANCE MODE, because "green with 63 skips" and "green having
    proved the parity claim" must not look alike to whoever reads the run. With
    `ACAS_REQUIRE_ORACLE` set, an unusable stack FAILS with the same reason text, so
    a run that was supposed to exercise the oracle cannot silently decline to. The
    two dispositions differ; the enumerated conditions in `_probe_stack` do not.

    Raises:
        Skipped: pytest's own skip exception, when a precondition is missing and the
            acceptance mode is off.
        AssertionError: When a precondition is missing and `ACAS_REQUIRE_ORACLE` is
            set.
    """
    status = stack_status()
    if status.available:
        return
    reason = status.reason or "the harness Compose stack is not usable"
    if oracle_is_required():
        raise AssertionError(
            f"{ENV_REQUIRE_ORACLE} is set, so the oracle tier may not be skipped, "
            f"and it cannot run:\n{reason}"
        )
    pytest.skip(reason)


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
# harness/scenarios/<name>.yaml. Agent Action Plan section 0.8.5 mandates exactly
# these eight, expanding "clean batch post per ledger" into four cases because the four
# ledgers exercise materially different code paths.
#
# `control_total_mismatch` IS GENERAL-LEDGER-SPECIFIC. Agent Action Plan section
# 0.6.4: Sales and Purchase batches "balance by construction ... there is no
# meaningful way to construct an unbalanced sales batch". There is deliberately no
# SL or PL variant, and no helper here implies one is possible.
#
# THERE IS NO NINTH SCENARIO, AND `gl080` HAS NO SCENARIO OF ITS OWN. The Agent Action
# Plan's inventory names eight scenario definitions and eight scenario tests, and this
# tree is held to that inventory, so no committed scenario drives `gl080` through the
# real `gl_end_of_cycle` route. What that costs is stated rather than glossed: `gl080` no longer has a TABLE-STATE
# comparison behind it, so posting deletion, batch stamping, the nominal-ledger quarter
# rollover and the cycle advance are covered at unit level only. What it does not cost:
# anomaly A-2 (the unbounded quarter subscript) and anomaly A-3 (the second, independent
# rotating quarter counter) stay locked in the arithmetic tier - `test_a2_...` and
# `test_a3_current_quarter_rotates_independently_of_a` in
# tests/arithmetic/test_gl080_cycle_divide_rounded.py - and the three questions that
# once waited on this scenario were each resolved by STANDALONE compiled probes rather
# than by it (`Q-GL080-DIVIDE-BY-ZERO`, `Q-QUARTER-SUBSCRIPT`, and `Q-2`'s fifth
# `ROUNDED` site at [general/gl080.cbl:L328]). The retained measurement is kept as
# history in docs/migration/scenario-diff-evidence.md rather than deleted.
#
# The `gl_end_of_cycle` OPERATION below is unaffected: it is one of the seven planned
# CLI routes, and both runners still drive it. No committed scenario selects it.
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
    "irs_post": ("irs", "4", "irs030-dispatch", "irs/irs.cbl:L666-L672"),
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
#  gl070 -> 5   [general/gl070.cbl:L289]     an open batch aborts the cycle
#  sl055 -> 8   [sales/sl055.cbl:L344]       the extract file is missing
#  pl055 -> 8   [purchase/pl055.cbl:L286]    the same, on the Purchase side
# and `acas_posting/cli/args.py`'s `exit_status_for(term_code)` returns 0 for 0 and
# THE TERM CODE ITSELF otherwise. So a GL open-batch abort surfaces as exit 5 and
# an SL or PL missing-extract-file abort as exit 8. `irs_post` has no
# `WS-Term-Code` at all and returns 0.
#
# The abort GATES that consume those codes are three different shapes, and the
# asymmetry is the specification, not an oversight to harmonise:
#  General   `if ws-term-code = 5 / go to display-menu`
#  [general/general.cbl:L810-L811]      - gl071 and gl072 never run
#  Sales     `if ws-term-code not = zero`, TWICE
#  [sales/sales.cbl:L761-L762, L765-L766]
#  Purchase  NONE - the gate is commented out
#  [purchase/purchase.cbl:L755-L758]
#  IRS       NONE, and no dispatch wrapper at all  [irs/irs.cbl:L666-L672]
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

# The Python runner's OWN band, transcribed from harness/run_python_scenario.sh's
# `readonly EX_*` block the same way the three above were. Listed for the SAME reason
# they are: a status in this band is the script diagnosing its own preconditions - a
# missing module, an unusable database, an option a module does not publish, a seed
# fingerprint disagreement - and is never a term code.
#
# 69 IS DELIBERATELY NOT IN THIS SET.
#
# harness/run_python_scenario.sh declares 69 as `EX_BEHAVIOUR`: the runner drove the
# cycle to completion and found that an operation's OBSERVED disposition contradicted
# the one the scenario declared. That is the single most important finding the whole
# protocol can produce - a real behavioural difference between the migrated cycle and
# its specification - and it was being classified as a HARNESS FAULT, which reads as
# "the test rig is broken" and is reported as an error rather than a failure. A
# migration defect was therefore indistinguishable from a missing environment
# variable. 69 now classifies as `DISPOSITION_BEHAVIOURAL` and reaches the test body,
# where it FAILS.
#
# AND 69 MEANS A TERM CODE, BECAUSE THE PRODUCER SAYS SO. Admitting
# 69 as data is only sound while the runner cannot mint it from a fault. It could:
# every child status other than 2 became 69, so an uncaught exception, an import
# failure, a signal or an arbitrary tool exit was attested as a completed semantic
# difference. harness/run_python_scenario.sh now admits only 0 and the operation's own
# frozen term codes -- `ACAS_PY_TERM_CODE_MAP', whose contents are the same mapping
# `TERM_CODES` below declares for this side -- and exits EX_ASSERT=77 otherwise, which
# is in the set below and therefore lands as a harness fault. The two layers agree by
# construction rather than by coincidence, and a drift between the two tables is
# caught by `test_term_codes_match_the_runner_table`.
RUN_PYTHON_FAULT_CODES: Final[frozenset[int]] = frozenset(
    {70, 71, 72, 73, 74, 75, 76, 77, 78}
)

#: `EX_BEHAVIOUR` from harness/run_python_scenario.sh. The wrapper completed; an
#: operation's observed status contradicted its declared one. Never a harness fault.
RUN_PYTHON_BEHAVIOURAL_EXIT: Final[int] = 69

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
#  run_date_text         the pinned date, exactly as typed, e.g. 21/09/2025
#  run_date_binary       the expected SYSTEM-REC.RUN-DAT after Date Entry
#  date_form             1 UK dd/mm/yyyy, 2 USA mm/dd/yyyy, 3 yyyy/mm/dd
#  irs_instead           the three-state fan-out switch - see IRS_INSTEAD_* below
#  operation             one of the seven; `subsystem` is derived from it
#  affected_tables       the list that BOUNDS the comparison
#  seed_files            the flat files harness/seed.sh stages; system.dat MUST be
#  among them, because the frozen order seeds the system
#  block first and unconditionally
#  [common/masterLD.sh:L50-L88] and it is what carries
#  Run-Date [copybooks/wssystem.cob:L67] and the fan-out
#  switch [copybooks/wssystem.cob:L179-L181]
#  irs_clear_postings    "Y" or "N"; REQUIRED for irs_post - see below
#  gl080_proceed         "Y" proceeds, "A" aborts; default "Y"
#  payment_post_confirm  "YES" or "NO"; required for sl_cash_post and
#  pl_payment_post, neither of whose prompts has a default
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
#  179       05  IRS-Instead     pic x.
#  180           88  IRS-Used                   value "Y".
#  181           88  IRS-Both-Used              value "B".   *> 26/11/16
# Column `IRS-INSTEAD char(1)`. THREE states, and the third has NO CONDITION NAME AT
# ALL - both predicates are simply False for a space, which is General Ledger only.
# Agent Action Plan section 0.6.4: "leaving it at a default would make the
# affected-table list ambiguous", so every scenario pins it explicitly. A YAML space
# or empty value reaches the CLI as the LITERAL SPACE `--irs-instead ' '`: the option
# takes ONE character and publishes no `N`, so the space is what is passed and what
# the column stores, and normalize.py's job 1 trims that to the empty string on BOTH
# sides - correct, because it is applied identically.
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
# `fn-delete-all` [common/acas008.cbl:L313-L319], which the bridge issues as a delete
# BOUNDED to keys strictly below the key text `9999999999`
# [common/slpostingMT.cbl:L850-L891] - measured to reach no bridge-written key, so the
# table is not emptied; see the key-bound note under A-NEW-8 in
# docs/migration/anomaly-log.md. So the answer decides whether the statement is issued
# at all, and any IRS scenario must both pin it and list PSIRSPOST-REC among its
# affected tables. The trailing accept at
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


def scenario_fixture_dir(scenario: str) -> Path:
    """Return the builder's canonical fixture directory for one scenario.

    `harness/seed.sh --build-fixtures` writes one directory per scenario under
    `$ACAS_FIXTURES`, falling back to `$ACAS_DATA/fixtures`. The scenario YAML is
    mounted read-only inside the harness container, so its relative `seed_dir`
    cannot be the runtime location. Stages 1 and 5 therefore pass this directory
    explicitly through `--seed-dir`; the scenario's `seed_files` list remains the
    authority for *which* files are accepted.

    THE RULE IS STATED ONCE, BY THE PRODUCER, and derived identically in three
    places: `harness/seed.sh --build-fixtures`'s `ACAS_BF_OUT` default owns it,
    `harness/reset_db.sh` derives it for a hand-driven stage 1 or 5, and this function
    derives it for the pytest protocol.
    `test_comp_binary.py` measures all three against one
    environment and fails if any pair disagrees, because a comment would not keep
    them in step. The one deliberate difference: the builder falls back to `/data`
    as a last resort because it can be run outside Compose, while both readers
    would rather refuse than guess - hence the `HarnessFaultError` below.

    Args:
        scenario: The scenario name.

    Returns:
        `$ACAS_FIXTURES/<scenario>` or `$ACAS_DATA/fixtures/<scenario>`.

    Raises:
        HarnessFaultError: Neither fixture-root environment is available. The
            message includes the exact build command rather than allowing
            `seed.sh` to fail later against a path derived from an empty value.
    """
    assert_scenario_name(scenario)
    configured = os.environ.get(ENV_FIXTURES, "").strip()
    if configured:
        return Path(configured) / scenario

    data_dir = os.environ.get(ENV_DATA, "").strip()
    if data_dir:
        return Path(data_dir) / "fixtures" / scenario

    raise HarnessFaultError(
        f"cannot locate the built fixture for {scenario!r}: neither "
        f"${ENV_FIXTURES} nor ${ENV_DATA} is set. Build the fixtures with "
        f"`harness/seed.sh --build-fixtures {scenario}` and expose its output through "
        f"{ENV_FIXTURES}, or set {ENV_DATA} so the canonical "
        f"`$ACAS_DATA/fixtures/{scenario}` location is available."
    )


def scenario_staged_data_dir(scenario: str) -> Path:
    """Return the scenario-owned data directory created by `seed.sh`.

    The fixture builder's immutable input lives under `fixtures/<scenario>`.
    `seed.sh` copies only the declared files into a fresh sibling directory
    `$ACAS_DATA/<scenario>` and points the frozen loaders at that staging area.
    The runner subprocesses are separate processes, so the loader's exported
    `ACAS_LEDGERS` cannot leak into them; this helper reconstructs that exact
    directory for stages 2 and 6 instead of falling back to the ambient
    `$ACAS_DATA`, where `system.dat` does not live.
    """
    assert_scenario_name(scenario)
    data_dir = os.environ.get(ENV_DATA, "").strip()
    if not data_dir:
        raise HarnessFaultError(
            f"cannot locate the staged data for {scenario!r}: ${ENV_DATA} is "
            f"unset. Stage 1 writes `$ACAS_DATA/{scenario}` and both run stages "
            f"must use that same scenario-owned directory."
        )
    return Path(data_dir) / scenario


#: The administrative pair. Only `harness/reset_db.sh` and the `harness/seed.sh` it
#: delegates to hold any reference to either name - a census across the whole harness
#: finds none in the cycle runners, the oracle build, the dump, the normalisation or
#: the comparison. So every other child runs without them.
_ADMIN_ENV_NAMES: Final[tuple[str, ...]] = (ENV_DB_ADMIN_USER, ENV_DB_ADMIN_PASSWORD)


def without_admin_credentials(env: Mapping[str, str]) -> dict[str, str]:
    """Copy an environment with the database superuser credential removed.

    `harness/docker-compose.yml` sets the administrative pair on the whole `gnucobol`
    service, because protocol stages 1 and 5 need DDL rights to drop and re-apply the
    frozen schema. A service-wide variable is inherited by every descendant, so without
    this the superuser password reached the GnuCOBOL compiler, the preSQL translator,
    every bridge and menu binary, the migrated Python cycle and pytest itself.

    Removed rather than left unused, so a child cannot reach the credential even by
    accident. Application access is untouched: `ACAS_DB_USER` and `ACAS_DB_PASSWORD`
    remain, and that account holds only DML on the one schema.

    Args:
        env: The environment to copy.

    Returns:
        A new mapping without the administrative pair.
    """
    return {
        name: value for name, value in env.items() if name not in _ADMIN_ENV_NAMES
    }


def scenario_runtime_environment(scenario: str) -> dict[str, str]:
    """Build the environment shared by the COBOL and Python run stages.

    Copied from `os.environ`, so a run id bound by `bound_run_id` reaches both
    runners without either helper having to know about it - MINUS the administrative
    credential, which neither run stage uses and neither should be able to.
    """
    staged = str(scenario_staged_data_dir(scenario))
    environment = without_admin_credentials(os.environ)
    environment[ENV_DATA] = staged
    environment[ENV_LEDGERS] = staged
    return environment


def mint_run_id() -> str:
    """Mint one run id for one protocol run.

    Shaped to satisfy the runners' own validation, `^[A-Za-z0-9._-]{1,64}$`, so an
    artifact published under it is indistinguishable in form from one published by a
    hand-driven stage.

    Returns:
        A fresh id, for example `pytest-3f9c1a04b7e24d61`.
    """
    return f"{RUN_ID_PREFIX}{uuid.uuid4().hex[:16]}"


@contextlib.contextmanager
def bound_run_id(run_id: str | None = None) -> Iterator[str]:
    """Bind one run id into the environment for the duration of a protocol run.

    THE STAGES ARE SEPARATE PROCESSES, and each of them derives its own identity when
    none is supplied. That is correct for a hand invocation and wrong for a protocol:
    the two sides must be provably two halves of ONE attempt before a verdict may be
    rendered on them. A hand-driven run achieves this by
    exporting `ACAS_PARITY_RUN_ID` once before stage 1 (README section 8); this does the
    same for the protocol
    composed in this module, and every stage helper inherits `os.environ`, so no helper
    signature changes and a test that drives a single stage is unaffected.

    RESTORED ON EXIT, including on an exception, so one test can never leak its run id
    into the next. A pre-existing value is honoured rather than overwritten when
    `run_id` is None, which is what lets an outer driver own the id.

    Args:
        run_id: The id to bind. A fresh one is minted when None, unless the
            environment already carries one, which is then reused.

    Yields:
        The id that is bound for the duration.
    """
    if run_id is None:
        run_id = os.environ.get(ENV_PARITY_RUN_ID) or mint_run_id()
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,64}", run_id):
        raise ValueError(
            f"a run id must match ^[A-Za-z0-9._-]{{1,64}}$ - the shape both runners "
            f"validate before they will accept one - and {run_id!r} does not. An id "
            f"the runners reject would abort stage 2 rather than binding anything."
        )

    previous = os.environ.get(ENV_PARITY_RUN_ID)
    os.environ[ENV_PARITY_RUN_ID] = run_id
    try:
        yield run_id
    finally:
        if previous is None:
            os.environ.pop(ENV_PARITY_RUN_ID, None)
        else:
            os.environ[ENV_PARITY_RUN_ID] = previous


def scenario_definition(scenario: str) -> Mapping[str, Any]:
    """Load one scenario definition (Agent Action Plan section 0.4.1.7).

    Read through `harness/normalize.py`'s duplicate-rejecting loader, which is a
    `yaml.SafeLoader` subclass - so the loader still cannot construct arbitrary Python
    objects from a data file, AND a repeated mapping key is a hard parse failure rather
    than PyYAML's silent last-one-wins. Every consumer of a scenario
    definition in this project uses that one loader, and none of them falls back to
    PyYAML's own safe loader entry point.

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
    #  Both lazy, so the arithmetic tier imports this module without PyYAML present.
    #  `normalize` is loaded by explicit file path for the same reason the other two
    #  harness modules are: harness/ is deliberately not a Python package (rule R-1),
    #  and adding an __init__.py is not the fix. It OWNS the parser.
    import yaml  # noqa: PLC0415, F401 - re-exported exception type

    parser_module = _load_harness_module("normalize")

    path = scenario_file(scenario)
    if not path.is_file():
        raise FileNotFoundError(
            f"the scenario definition {scenario!r} was expected at {path} and is "
            f"not there. The {len(SCENARIOS)} definitions - {', '.join(SCENARIOS)} - "
            f"are an "
            f"Agent Action Plan section 0.4.1.7 deliverable, and every comparison "
            f"is bounded by one: an unbounded dump is refused rather than "
            f"defaulted."
        )

    parsed = parser_module.load_scenario_yaml(path.read_text(encoding="utf-8"))
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
    """One scenario's DECLARED EFFECT, in the order it declares them.

    THIS IS NOT HOW THE COMPARISON IS BOUNDED. It is the list the runners assert
    changed or unchanged against `expected_table_effect`. The capture and the diff
    are bounded by ALL 22 in-scope tables - `in_scope_tables()`, passed as
    `--all-in-scope` by `dump` and `diff` - because a bound drawn from what a
    scenario EXPECTS to move cannot show a difference in anything it did not expect
    to move, and an empty diff is the single pass condition (Agent Action Plan
    section 0.8.5).

    Four facts about the two sides shape the declared lists, and none of them is a
    migration defect:

      1. The menu shell's exit path runs `overrewrite`, persisting SYSTEM-REC
         (key 1), SYSDEFLT-REC (key 2) and SYSTOT-REC (key 4)
         [general/general.cbl:L656-L691], and `load000` does it on EVERY call.
         `acas_posting/cli/args.py`'s `overrewrite` is its migrated counterpart and
         every one of the seven routes calls it, so KEY 1 IS WRITTEN ON BOTH SIDES.
         Key 2 is General-only; SL/PL write keys 1 and 4; IRS writes key 1 alone.
         The asymmetry that once justified a narrower bound therefore no longer
         exists.
      2. SYSTEM-REC is dumped and compared like every other in-scope table, and its
         TWO CREDENTIAL COLUMNS are rendered as a constant rather than captured -
         `harness/dump_tables.py`'s `REDACTED_COLUMNS`, applied in the one funnel
         every captured cell passes through and keyed by `(table, column)` so it is
         identical on both sides. A capture is `SELECT *` and a capture is evidence a
         human reads, and `RDBMS-PASSWD char(12)` [copybooks/wssystem.cob:L139] and
         `PASS-WORD char(4)` have no business in it. Bounding the whole row out would
         have removed the leak by removing 168 columns the two cycles genuinely
         write - the run-date stamp, the IRS allocator, the one-shot latches,
         `Date-Form`, itself a SYSTEM-REC column [copybooks/wssystem.cob:L127] the
         frozen date sections write back - from every diff.
      3. The row is ALSO fingerprinted, before and after each run and on both sides,
         so a change is witnessed even where the diff is empty:
         `assert_system_record_parity` compares the two post-run digests and
         `assert_tables_unchanged_by_run` reads the same records for the mutation
         witness. MEASURED, so the fragility objection is on record rather than
         asserted: the digest moves on exactly the scenarios declaring `changed` and
         holds on those declaring `unchanged`, so counting the row toward
         `expected_table_effect` falsifies no claim today.
      4. sl830 runs only on the COBOL side [sales/sales.cbl:L759], so the four
         autogen tables are never seeded and never listed; the scenarios that could
         reach it pin `sl_autogen` so it cannot, which is an input decision rather
         than a bound, and both runners assert after the run that all four are still
         empty.

    THERE IS STILL NO IGNORING, ONLY BOUNDING: no ignore-list, no tolerance-list and
    no "known difference" allowance exists anywhere in the diff path, and the one
    value substitution is a REDACTION applied to both sides of the same comparison.
    Note that SYSTOT-REC IS genuinely in scope for `period_end_totals` - Agent Action
    Plan section 0.6.4 names nine period-total write sites, "the sole writers of the
    totals record" - so it is never blanket excluded.

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
#  1. Its own header says so - [common/masterLD.sh:L4-L5]: "THIS SCRIPT HAS NOT
#  YET BEEN TESTED".
#  2. It cannot execute at all. All 24 loader lines
#  [common/masterLD.sh:L93-L116] omit the `;` before `fi`, so `bash -n` rejects
#  it at line 124. It is FROZEN and is NOT fixed (Agent Action Plan section
#  0.8.1, rules R-3 and R-4).
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
#
# THE NUMBERING IS THE CANONICAL ONE. The protocol has TEN
# stages, defined once in `PARITY_STAGES` in harness/normalize.py and published by
# `harness/normalize.py --print-stages`. These names previously numbered the second
# normalisation `7b` and the comparison `8`, which described an EIGHT-stage protocol
# that had not been the one driven for some time - so a stage number in a test failure
# named a different stage from the same number in a driver transcript. They now agree,
# and `parity_stage_registry` reads the registry so a test can prove they still do.
STAGE_SEED: Final[str] = "1-seed"
STAGE_RUN_COBOL: Final[str] = "2-run-cobol"
STAGE_DUMP_COBOL: Final[str] = "3-dump-cobol"
STAGE_NORMALIZE_COBOL: Final[str] = "4-normalize-cobol"
STAGE_RESET: Final[str] = "5-reset"
STAGE_RUN_PYTHON: Final[str] = "6-run-python"
STAGE_DUMP_PYTHON: Final[str] = "7-dump-python"
STAGE_NORMALIZE_PYTHON: Final[str] = "8-normalize-python"
STAGE_VERIFY_PUBLISHED: Final[str] = "9-verify-published"
STAGE_DIFF: Final[str] = "10-diff"

#: Every stage name above, in protocol order, so a consumer can iterate the sequence
#: without re-listing it.
STAGE_NAMES: Final[tuple[str, ...]] = (
    STAGE_SEED,
    STAGE_RUN_COBOL,
    STAGE_DUMP_COBOL,
    STAGE_NORMALIZE_COBOL,
    STAGE_RESET,
    STAGE_RUN_PYTHON,
    STAGE_DUMP_PYTHON,
    STAGE_NORMALIZE_PYTHON,
    STAGE_VERIFY_PUBLISHED,
    STAGE_DIFF,
)


_STAGE_REGISTRY: list[tuple[int, str]] | None = None


def parity_stage_registry() -> tuple[tuple[int, str], ...]:
    """Return the canonical stage registry, `(number, label)` in protocol order.

    THE ONE PLACE THE PROTOCOL'S SHAPE IS DEFINED is
    `PARITY_STAGES` in harness/normalize.py, and `harness/normalize.py --print-stages`
    is how it is published. Reading it here rather than restating it is what stops this
    module's prose drifting from the protocol it composes - which is exactly what had
    happened: this file described EIGHT stages while the driver drove ten.

    Memoised per session: it is a subprocess, and the answer cannot change mid-run.

    Returns:
        The registry rows. Empty when the registry could not be read, which a caller
        treats as "cannot check" rather than as a failure - `pytest -m arithmetic`
        must succeed on a host with no harness at all.
    """
    global _STAGE_REGISTRY
    if _STAGE_REGISTRY is not None:
        return tuple(_STAGE_REGISTRY)

    rows: list[tuple[int, str]] = []
    if STAGE_REGISTRY_SCRIPT.is_file() and os.access(STAGE_REGISTRY_SCRIPT, os.X_OK):
        try:
            completed = subprocess.run(  # noqa: S603 - a fixed, repo-local path
                [str(STAGE_REGISTRY_SCRIPT), "--print-stages"],
                capture_output=True,
                text=True,
                timeout=60,
                stdin=subprocess.DEVNULL,
                check=False,
                cwd=REPO_ROOT,
                # A read-only listing of the stage registry: no credential of any kind
                # is needed, so the administrative pair is not handed over.
                env=without_admin_credentials(os.environ),
            )
        except (OSError, subprocess.SubprocessError):
            completed = None
        if completed is not None and completed.returncode == 0:
            for line in completed.stdout.splitlines():
                if not line.strip():
                    continue
                number, _, label = line.partition("\t")
                try:
                    rows.append((int(number, 10), label))
                except ValueError:
                    # A row this module cannot parse is reported by the test that
                    # checks the registry, not swallowed into a partial answer.
                    rows = []
                    break

    _STAGE_REGISTRY = rows
    return tuple(rows)


def stage_number(stage: str) -> int:
    """Return the protocol stage number encoded in one stage name.

    Args:
        stage: One of `STAGE_NAMES`, for example `"6-run-python"`.

    Returns:
        The number, for example 6.

    Raises:
        ValueError: The name does not begin with a number, which would mean a stage
            constant had been written in a shape nothing can place in the sequence.
    """
    number, _, _ = stage.partition("-")
    try:
        return int(number, 10)
    except ValueError as exc:
        raise ValueError(
            f"the stage name {stage!r} does not begin with its protocol stage "
            f"number, so a reader cannot place it in the sequence."
        ) from exc


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
        returncode: The harness stage process's exit status VERBATIM. Never
            normalised or clamped. Run stages expose their child operation statuses
            separately because a successful wrapper exits zero after verifying an
            expected non-zero term code.
        stdout: Everything the stage wrote to stdout.
        stderr: Everything it wrote to stderr.
        operation_statuses: Ordered `(operation, status)` records emitted by a run
            stage. Empty for non-run stages and for a run-stage harness failure.
    """

    stage: str
    argv: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str
    operation_statuses: tuple[tuple[str, int], ...] = ()

    @property
    def ok(self) -> bool:
        """Whether the stage exited zero."""
        return self.returncode == 0

    def operation_status(self, operation: str) -> int:
        """Return one driven operation's observed term/process status.

        The COBOL menu process itself returns to its menu after `ws-term-code = 5`
        [general/general.cbl:L810-L811], while the migrated CLI child exits 5.
        Both harness wrappers then exit zero when that observed behaviour matches the
        scenario. The machine-readable `OPERATION_STATUS` record preserves the
        behavioural value without conflating it with wrapper health.

        Args:
            operation: One of the seven shared operation names.

        Returns:
            The status recorded for that operation.

        Raises:
            HarnessFaultError: The stage recorded none or more than one status for
                the requested operation.
        """
        matches = [
            status
            for recorded_operation, status in self.operation_statuses
            if recorded_operation == operation
        ]
        if len(matches) != 1:
            raise HarnessFaultError(
                f"stage {self.stage} recorded {len(matches)} OPERATION_STATUS "
                f"entries for {operation!r}; expected exactly one. Recorded: "
                f"{self.operation_statuses!r}.\n{self.describe()}"
            )
        return matches[0]

    def describe(self) -> str:
        """A multi-line description, for a failure message.

        Returns:
            The stage, its command line, its status and both streams.
        """
        behavioural = (
            "\n  operation statuses: "
            + ", ".join(
                f"{operation}={status}"
                for operation, status in self.operation_statuses
            )
            if self.operation_statuses
            else ""
        )
        return (
            f"stage {self.stage} exited {self.returncode}\n"
            f"  command: {' '.join(self.argv)}\n"
            f"  stdout:\n{_indent(self.stdout)}\n"
            f"  stderr:\n{_indent(self.stderr)}"
            f"{behavioural}"
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
    administrative: bool = False,
) -> StageResult:
    """Run one harness shell script as a subprocess, non-interactively.

    Args:
        script: The script to run.
        argv: Its arguments, already stringified.
        stage: The `STAGE_*` name, recorded in the result.
        timeout: The wall-clock ceiling for THIS wait.
        env: The environment; the current one when omitted. Everything the scripts read
            is passed through - `ACAS_*`, `ACAS_SEED_STRICT` and the rest - because this
            module has no business deciding what they see. The ONE exception is the
            administrative credential, below.
        administrative: Whether this stage performs schema administration and therefore
            needs `ACAS_DB_ADMIN_USER` / `ACAS_DB_ADMIN_PASSWORD`. FALSE BY DEFAULT, and
            the default is the point: the database superuser password
            is removed from the child's environment unless the stage is one of the two
            that drops and re-applies the schema. Exactly three call sites pass True -
            the seed and the two resets - and every other child, including both cycle
            runners, runs without the credential rather than merely not using it.

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
    source: Mapping[str, str] = os.environ if env is None else env
    child_env = dict(source) if administrative else without_admin_credentials(source)
    try:
        completed = subprocess.run(  # noqa: S603 - a fixed, repository-owned script
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
            stdin=subprocess.DEVNULL,
            cwd=str(REPO_ROOT),
            env=child_env,
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


_OPERATION_STATUS_PREFIX: Final[str] = "OPERATION_STATUS\t"


def _requested_operations(
    scenario: str,
    override: str | None,
    *,
    all_declared: bool,
) -> tuple[str, ...]:
    """Resolve the operations one run-stage invocation drives.

    BOTH runners drive the whole ordered `operations` list in ONE invocation, and both
    take a REPEATABLE `--operation`. Each run stage is therefore a single
    argv carrying one `--operation` per declared operation, in the
    declared order, and each runner publishes one disposition record per operation. THE
    ORACLE RUNNER DOES NOT DRIVE "one menu operation per invocation, using the scalar
    `operation` key" - `harness/run_cobol_scenario.sh --help` states the contract as
    "REPEATABLE, and driven in the order given".

    An explicit override still narrows either side to exactly one operation.
    """
    if override is not None:
        return (override,)

    definition = scenario_definition(scenario)
    declared = definition.get("operations") if all_declared else None
    if (
        all_declared
        and isinstance(declared, Sequence)
        and not isinstance(declared, (str, bytes))
    ):
        return tuple(str(item) for item in declared)
    return (str(definition[SCENARIO_KEY_OPERATION]),)


#: The per-operation status artifact each runner publishes beside its transcript,
#: named `<side>.operation-status`. THE AUTHORITY for what each driven operation
#: actually did: the transcript line is a diagnostic that a `--quiet`
#: mode or a redirected stream can lose, whereas this file is published atomically at
#: mode 0600 and carries the run id, so it can be attributed to an attempt.
OPERATION_STATUS_SUFFIX: Final[str] = ".operation-status"

#: The status field's sentinel for an operation that was declared and never driven.
#: `ACAS_PY_OP_NOT_RUN` in harness/run_python_scenario.sh and `ACAS_RUN_OP_NOT_RUN` in
#: harness/run_cobol_scenario.sh, and deliberately not zero: zero is a real term code,
#: so a slot defaulting to it would attest a clean disposition for work never done.
OPERATION_STATUS_NOT_RUN: Final[str] = "not-run"


def read_operation_status_artifact(
    scenario: str,
    side: str,
    *,
    out_dir: Path | str | None = None,
) -> tuple[tuple[str, int], ...] | None:
    """Read one side's published per-operation statuses, in declared order.

    THE RECORD SHAPE, published by both runners:

        scenario<TAB><name>
        side<TAB>cobol|python
        run_id<TAB><id>
        operations<TAB><count>
        operation<TAB><index><TAB><name><TAB><status>     x count

    THE STATUS FIELD IS A NUMBER *OR* THE SENTINEL `not-run`. Both runners declare
    `not-run` for an operation they never reached - `ACAS_PY_OP_NOT_RUN` and
    `ACAS_RUN_OP_NOT_RUN` - deliberately, because zero is a real term code and a slot
    defaulting to zero would attest a clean disposition for work that never happened.
    This reader used to `int()` the field unconditionally and raise a harness fault on
    the sentinel, so an artifact the runner wrote CORRECTLY was rejected as malformed
    and the diagnosis a partial run had published was replaced by a parse error. A
    `not-run` row is now read, kept out of the returned dispositions - it has none -
    and counted for the completeness check, which is about the record being whole
    rather than about the work being done.

    Args:
        scenario: The scenario name.
        side: `cobol` or `python`.
        out_dir: The output root; `$ACAS_OUT` when omitted.

    Returns:
        The ordered `(operation, status)` pairs for the operations that RAN, or None
        when the file is absent - which is not by itself a fault, because a
        hand-driven run legitimately has none and the caller decides whether it
        needed one.

    Raises:
        HarnessFaultError: The file exists but is malformed, or its rows are not a
            complete ordered set. A published artifact that cannot be read is worse
            than an absent one: it looks like evidence.
    """
    assert_scenario_name(scenario)
    assert_side(side)
    paths = scenario_paths(scenario, out_root=out_dir)
    path = paths.run_logs / f"{side}{OPERATION_STATUS_SUFFIX}"
    if not path.is_file():
        return None

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise HarnessFaultError(
            f"the {side} operation-status artifact {path} exists but could not be "
            f"read: {exc}. It is what says what each driven operation actually did, "
            f"so a capture cannot be attributed without it."
        ) from exc

    declared: int | None = None
    rows: list[tuple[int, str, int | None]] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        fields = line.split("\t")
        key = fields[0]
        if key == "operations" and len(fields) == 2:
            try:
                declared = int(fields[1], 10)
            except ValueError as exc:
                raise HarnessFaultError(
                    f"{path}:{number}: the operation count {fields[1]!r} is not an "
                    f"integer."
                ) from exc
        elif key == "operation":
            if len(fields) != 4:
                raise HarnessFaultError(
                    f"{path}:{number}: an operation record must carry index, name "
                    f"and status; got {line!r}."
                )
            try:
                index = int(fields[1], 10)
            except ValueError as exc:
                raise HarnessFaultError(
                    f"{path}:{number}: a non-integer operation index in {line!r}."
                ) from exc
            if fields[3] == OPERATION_STATUS_NOT_RUN:
                rows.append((index, fields[2], None))
                continue
            try:
                rows.append((index, fields[2], int(fields[3], 10)))
            except ValueError as exc:
                raise HarnessFaultError(
                    f"{path}:{number}: the status field is neither an integer nor "
                    f"the sentinel {OPERATION_STATUS_NOT_RUN!r} in {line!r}."
                ) from exc

    if declared is None:
        raise HarnessFaultError(
            f"{path} declares no operation count, so there is no way to tell a "
            f"complete record from a truncated one."
        )
    if len(rows) != declared:
        raise HarnessFaultError(
            f"{path} declares {declared} operation(s) but carries {len(rows)} "
            f"record(s). A partial set cannot establish the dispositions this "
            f"capture belongs to."
        )
    if [index for index, _, _ in rows] != list(range(1, declared + 1)):
        raise HarnessFaultError(
            f"{path} carries operation indices "
            f"{[index for index, _, _ in rows]!r}; expected 1..{declared} in order. "
            f"The order is the order they were driven in, and it matters."
        )
    #  ONLY THE OPERATIONS THAT RAN CARRY A DISPOSITION. A `not-run` row is
    #  information - it says the record is complete and that this slot was never
    #  driven - and it is deliberately not turned into a status, because there is no
    #  number that means "did not happen".
    return tuple(
        (name, status) for _, name, status in rows if status is not None
    )


def _attach_operation_statuses(
    result: StageResult,
    operations: Sequence[str],
    *,
    scenario: str | None = None,
    side: str | None = None,
    out_dir: Path | str | None = None,
) -> StageResult:
    """Attach machine-readable child-operation statuses to a run stage.

    THE STRUCTURED ARTIFACT IS THE AUTHORITY. Each runner publishes
    `<side>.operation-status` carrying one row per declared operation; the transcript
    also carries an `OPERATION_STATUS<TAB>operation<TAB>status` line per operation, and
    when both are present they must AGREE - a disagreement means one of the two was
    written by a different run and is a fault, not something to pick a winner from.

    A NON-ZERO WRAPPER MUST NOT SKIP THIS. Returning immediately, on the reasoning that
    the wrapper's own status is the diagnosis, is most wrong at exactly the status where
    the detail matters most - `EX_BEHAVIOUR` (69), where the wrapper is saying an
    operation's observed disposition contradicted its declared one and the per-operation
    statuses are precisely what identify WHICH operation and WHAT it did. An early return
    would discard them at the only moment they mattered.

    Args:
        result: The run stage's result.
        operations: The operations that were requested, in order.
        scenario: The scenario, so the published artifact can be located. When None
            the transcript is the only source, which is the pre-artifact behaviour.
        side: `cobol` or `python`, for the same reason.
        out_dir: The output root; `$ACAS_OUT` when omitted.

    Returns:
        The result with `operation_statuses` populated.

    Raises:
        HarnessFaultError: The records are malformed, incomplete, out of order, or
            the artifact and the transcript disagree.
    """
    published: tuple[tuple[str, int], ...] | None = None
    if scenario is not None and side is not None:
        published = read_operation_status_artifact(
            scenario, side, out_dir=out_dir
        )

    observed: list[tuple[str, int]] = []
    for line in result.stdout.splitlines():
        record = line.lstrip()
        if not record.startswith(_OPERATION_STATUS_PREFIX):
            continue
        fields = record.split("\t")
        if len(fields) != 3 or fields[0] != "OPERATION_STATUS":
            raise HarnessFaultError(
                f"stage {result.stage} emitted a malformed operation-status record: "
                f"{line!r}.\n{result.describe()}"
            )
        try:
            status = int(fields[2], 10)
        except ValueError as exc:
            raise HarnessFaultError(
                f"stage {result.stage} emitted a non-integer operation status in "
                f"{line!r}.\n{result.describe()}"
            ) from exc
        observed.append((fields[1], status))

    expected_names = tuple(operations)

    # THE TWO SOURCES MUST AGREE. When they do not, one of them belongs to another
    # run, and choosing either would attribute this capture to a disposition it may
    # not have had.
    if published is not None and observed and tuple(published) != tuple(observed):
        raise HarnessFaultError(
            f"stage {result.stage} published operation statuses {published!r} but "
            f"its transcript records {tuple(observed)!r}. The two disagree, so one "
            f"of them was written by a different run and neither can be trusted to "
            f"describe this capture.\n{result.describe()}"
        )

    resolved: tuple[tuple[str, int], ...] = published or tuple(observed)
    resolved_names = tuple(operation for operation, _ in resolved)

    # A WRAPPER THAT SUCCEEDED MUST ACCOUNT FOR EVERY OPERATION. A wrapper that
    # failed need not: it may have stopped partway, and the artifact then records
    # `not-run` for the operations it never reached - which is information, not a
    # fault. So completeness is required only of a clean run.
    if result.returncode == 0 and resolved_names != expected_names:
        raise HarnessFaultError(
            f"stage {result.stage} exited zero but accounted for operations "
            f"{resolved_names!r}; expected {expected_names!r} in that order. A run "
            f"without a complete behavioural disposition cannot attest a capture.\n"
            f"{result.describe()}"
        )

    return StageResult(
        stage=result.stage,
        argv=result.argv,
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
        operation_statuses=resolved,
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

    AUTOCOMMIT IS OFF FOR THE SEEDING WINDOW, AND ONLY THERE.
    `harness/seed.sh` owns that window - it opens it immediately before the first
    frozen load program, verifies it from a fresh session, restores the runtime
    mode from its exit trap on every path, and exits 73 if it cannot - citing the
    banner every one of the 28 frozen loaders carries at
    [common/glbatchLD.cbl:L9-L13]: "This modules uses commit and rollback so you
    MUST ensure that autocommit is OFF in the rdb settings." Nothing here sets the
    mode, and every connection OUTSIDE the window is runtime access with the mode
    ON: see docs/migration/ambiguity-resolutions.md#q-10 for the scoping.

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
    argv += ["--seed-dir", str(scenario_fixture_dir(scenario))]
    if only:
        argv += ["--only", ",".join(only)]
    if dry_run:
        argv.append("--dry-run")
    argv.append(str(scenario_file(scenario)))
    # administrative: seeding opens the autocommit window with SET GLOBAL, which the
    # application account may not do [harness/seed.sh].
    return _run_script(
        SEED_SCRIPT, argv, stage=STAGE_SEED, timeout=STAGE_TIMEOUT_SEED,
        administrative=True,
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
    else:
        argv += ["--seed-dir", str(scenario_fixture_dir(scenario))]
    if dry_run:
        argv.append("--dry-run")
    argv += _transformed_oracle_waiver()
    argv.append(str(scenario_file(scenario)))
    # administrative: this drops and re-applies the frozen schema.
    return _run_script(
        RESET_SCRIPT, argv, stage=STAGE_RESET, timeout=STAGE_TIMEOUT_RESET,
        administrative=True,
    )


def _transformed_oracle_waiver() -> list[str]:
    """`--accept-transformed-oracle` when, and only when, the operator asked for it.

    THE TWO ACKNOWLEDGEMENTS ARE ONE DECISION AND MUST BE PASSED TOGETHER. There is no
    ten-stage driver; the oracle-provenance gate lives in
    `harness/reset_db.sh`, where it fires before the first `DROP` - which is a
    strictly better place for it, because it guards a hand-driven stage 1 as well
    as a protocol-bound one. The consequence, MEASURED rather than reasoned, is that
    this module's own diagnostic switch stopped being sufficient on its own: setting
    `ACAS_ACCEPT_TRANSFORMED_ORACLE=1` un-skipped the stack-bound tiers and every one
    of them then ERRORED at stage 1 with `reset_db.sh` exit 77, because the script's
    gate wants its own flag. Two acknowledgements for one decision, and only one of
    them given, is a broken diagnostic route rather than a stricter one.

    So the env var - which is the operator saying "run these tiers against a
    transformed build, for diagnosis, with no parity claim" - is translated into the
    script flag that says exactly the same thing. Neither is inferred from the other's
    absence: with the variable unset the tiers SKIP and the flag is never passed, so a
    hand-driven or an unacknowledged run still meets exit 77.

    Returns:
        `["--accept-transformed-oracle"]` when the variable is set to `1`, else `[]`.
    """
    if os.environ.get("ACAS_ACCEPT_TRANSFORMED_ORACLE", "").strip() == "1":
        return ["--accept-transformed-oracle"]
    return []


def prepare_scenario(scenario: str) -> StageResult:
    """STAGE 1 - reset the frozen schema and seed the scenario from scratch.

    The canonical driver uses `reset_db.sh` for both stage 1 and stage 5. A bare
    `seed.sh` at stage 1 leaves rows from whichever scenario ran previously, so
    duplicate-key rewrites can create a different starting state from stage 5.
    This wrapper uses the same command and the same built fixture directory as
    :func:`reset`, but records it under the stage-1 name.
    """
    argv = [
        "--seed-dir",
        str(scenario_fixture_dir(scenario)),
        *_transformed_oracle_waiver(),
        str(scenario_file(scenario)),
    ]
    # administrative: this drops and re-applies the frozen schema, then seeds.
    return _run_script(
        RESET_SCRIPT, argv, stage=STAGE_SEED, timeout=STAGE_TIMEOUT_RESET,
        administrative=True,
    )


def run_cobol(
    scenario: str,
    *,
    operation: str | None = None,
    log_path: Path | str | None = None,
    dry_run: bool = False,
    out_dir: Path | str | None = None,
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
        log_path: Optional transcript path. Multi-operation scenarios use one path per
            menu drive so later operations cannot overwrite earlier oracle evidence.
        dry_run: `--dry-run` - resolve and print the keystroke plan, run every
            precondition, spawn no menu.
        out_dir: The output root, so the runner's published per-operation status
            artifact can be read; `$ACAS_OUT` when omitted.

    Returns:
        The captured result. Codes 70 to 79 are the script's own diagnoses; 74 in
        particular means a compiled artifact is missing and `harness/build_oracle.sh`
        has not completed.

    Raises:
        ValueError: `operation` is given and is not one of the seven.
    """
    # BOTH SIDES DRIVE THE SAME ORDERED LIST, which `all_declared=True` is what secures:
    # asking the oracle runner for ONE operation while asking the Python runner for every
    # operation the scenario declares would drive four operations on one side of
    # `period_end_totals` and one on the other, comparing two different amounts of work.
    # The runner accepts a repeated `--operation` and drives them in order in a single
    # invocation, so the
    # list is simply passed through.
    requested = _requested_operations(
        scenario, operation, all_declared=operation is None
    )
    argv: list[str] = []
    for name in requested:
        argv += ["--operation", name]
    if log_path is not None:
        argv += ["--log", str(log_path)]
    if dry_run:
        argv.append("--dry-run")
    argv.append(str(scenario_file(scenario)))
    result = _run_script(
        RUN_COBOL_SCRIPT,
        argv,
        stage=STAGE_RUN_COBOL,
        timeout=STAGE_TIMEOUT_RUN,
        env=scenario_runtime_environment(scenario),
    )
    if dry_run:
        return result
    return _attach_operation_statuses(
        result,
        requested,
        scenario=scenario,
        side=SIDE_COBOL,
        out_dir=out_dir,
    )


# `run_cobol_sequence` WAS HERE, AND IS GONE.
#
# It existed because harness/run_cobol_scenario.sh read only the SINGULAR `operation:`
# key, so a scenario declaring several - `period_end_totals` spans Sales and Purchase
# and declares four - could not be driven in one invocation. This helper drove the
# runner once per operation and then COPIED the first drive's seed fingerprint and
# run-status attestation back over the last one's, so that the Python side would be
# compared against the state before operation one. The cost was that operations two
# onward had NO ATTESTED DISPOSITION at all: their statuses were concatenated into a
# synthetic result, and the published run-status record described only operation one.
#
# The runner now accepts a repeated `--operation`, resolves the ordered list itself
# (repeated flags, then the `operations:` list, then the singular key), drives them one
# at a time in a single invocation against one seeded state, and publishes an ordered
# per-operation status row for every one of them. So `run_cobol` passes the whole list
# through and there is nothing left to work around: no second transcript path, no
# fingerprint restoration, and no copy-back.


def run_python(
    scenario: str,
    *,
    operation: str | None = None,
    dry_run: bool = False,
    out_dir: Path | str | None = None,
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
        out_dir: The output root, so the runner's published per-operation status
            artifact can be read; `$ACAS_OUT` when omitted.

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
    result = _run_script(
        RUN_PYTHON_SCRIPT,
        argv,
        stage=STAGE_RUN_PYTHON,
        timeout=STAGE_TIMEOUT_RUN,
        env=scenario_runtime_environment(scenario),
    )
    if dry_run:
        return result
    return _attach_operation_statuses(
        result,
        _requested_operations(scenario, operation, all_declared=operation is None),
        scenario=scenario,
        side=SIDE_PYTHON,
        out_dir=out_dir,
    )


def classify_run(result: StageResult, *, operation: str) -> str:
    """Classify a run stage and one observed operation into three dispositions.

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

    # The wrapper status describes whether the harness completed and verified its
    # own work. It is deliberately separate from the driven operation's status.
    wrapper_code = result.returncode
    if wrapper_code != 0:
        # A bad command line is THIS MODULE'S fault and never behavioural data.
        if wrapper_code == ARGPARSE_USAGE_EXIT:
            return DISPOSITION_HARNESS_FAULT
        # EX_BEHAVIOUR IS A BEHAVIOURAL FINDING, NOT A BROKEN RIG.
        # The wrapper ran the cycle and measured a contradiction; that is data. It is
        # classified before the fault bands so a future edit to those bands cannot
        # silently reabsorb it.
        if (
            result.stage == STAGE_RUN_PYTHON
            and wrapper_code == RUN_PYTHON_BEHAVIOURAL_EXIT
        ):
            return DISPOSITION_BEHAVIOURAL
        if result.stage == STAGE_RUN_COBOL and wrapper_code in RUN_COBOL_FAULT_CODES:
            return DISPOSITION_HARNESS_FAULT
        if result.stage == STAGE_RUN_PYTHON and wrapper_code in RUN_PYTHON_FAULT_CODES:
            return DISPOSITION_HARNESS_FAULT
        return DISPOSITION_HARNESS_FAULT

    code = result.operation_status(operation)
    if code == 0:
        return DISPOSITION_SUCCESS
    if code in TERM_CODES[operation]:
        return DISPOSITION_BEHAVIOURAL

    return DISPOSITION_HARNESS_FAULT


def assert_wrapper_completed(result: StageResult, *, label: str | None = None) -> None:
    """Assert a run stage's WRAPPER completed, and diagnose 69 as behavioural.

    WHY THIS IS NOT `assert result.returncode == 0` WITH A MESSAGE.
    Every non-zero wrapper status means the runner did not finish its drive and its
    self-checks, so a test that needs a complete run must refuse them all. But they do
    not all mean the same thing, and exactly one of them is the most valuable finding
    the protocol can produce: `EX_BEHAVIOUR` = 69 means the cycle RAN and an operation's
    observed disposition CONTRADICTED the one its scenario declares. Reporting that as
    "a harness fault" tells an operator to go and look at their environment when what
    they should be looking at is the migrated code.

    So the refusal is the same and the DIAGNOSIS differs, and it differs by reading
    :func:`classify_run` rather than by a second transcription of the bands.

    69 STILL FAILS HERE, and must. This helper is called from test BODIES, so the
    behavioural difference is reported as a pytest FAILURE attributable to the cycle -
    which is the whole point of keeping 69 out of `RUN_PYTHON_FAULT_CODES` and out of
    the fixtures' `raise_for_status` path.

    Args:
        result: A `run_cobol` or `run_python` stage result.
        label: How to name the side in the message. Defaults to the stage name.

    Raises:
        AssertionError: The wrapper exited non-zero, with the diagnosis its status
            earns.
        ValueError: `result` is not a run stage.
    """
    if result.stage not in {STAGE_RUN_COBOL, STAGE_RUN_PYTHON}:
        raise ValueError(
            f"assert_wrapper_completed describes a run stage; got {result.stage!r}."
        )
    if result.returncode == 0:
        return

    named = label or result.stage
    if (
        result.stage == STAGE_RUN_PYTHON
        and result.returncode == RUN_PYTHON_BEHAVIOURAL_EXIT
    ):
        raise AssertionError(
            f"{named} exited {RUN_PYTHON_BEHAVIOURAL_EXIT} (EX_BEHAVIOUR), which is A "
            f"BEHAVIOURAL DIFFERENCE and NOT a harness fault: the runner drove the "
            f"cycle to completion and found that an operation's observed disposition "
            f"contradicted the one the scenario declares. The capture was still taken, "
            f"so the diff stage can corroborate. Read the per-operation statuses in "
            f"the run-status artifact - the migrated cycle is what to examine here, "
            f"not the environment.\n{result.describe()}"
        )
    if result.returncode == ARGPARSE_USAGE_EXIT:
        raise AssertionError(
            f"{named} exited {ARGPARSE_USAGE_EXIT}, which in this family means THE "
            f"RUNNER BUILT A BAD COMMAND LINE. Nothing about the posting cycle was "
            f"measured.\n{result.describe()}"
        )
    band = (
        RUN_COBOL_FAULT_CODES
        if result.stage == STAGE_RUN_COBOL
        else RUN_PYTHON_FAULT_CODES
    )
    placement = (
        "That status is in the script's own documented precondition band"
        if result.returncode in band
        else (
            "That status is not a documented status of that runner at all - its band "
            f"is {sorted(band)} - so it is a fault by exclusion"
        )
    )
    raise AssertionError(
        f"{named}'s harness wrapper exited {result.returncode}, so it did not complete "
        f"its drive and self-checks. {placement}, which makes this a "
        f"{DISPOSITION_HARNESS_FAULT} and not an operation disposition: nothing about "
        f"the posting cycle was measured.\n{result.describe()}"
    )



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
#  * NORMALISATION DOES EXACTLY THREE THINGS AND THERE IS NO FOURTH, and none of
#  them is reproduced here: trailing spaces in fixed-character columns
#  (`rstrip(" ")`, TRAILING ONLY, because a COBOL alphanumeric MOVE is
#  left-justified so LEADING spaces are content); decimal scale rendering to the
#  column's DECLARED scale, which is NOT uniformly 2 and where a value implying
#  more places RAISES rather than rounds, because rounding there would hide a
#  real finding; and the two- versus four-digit date text forms, under an
#  explicit five-column allow-list. `normalize_dump` is a PURE function and this
#  wrapper keeps it that way - no logging inside it, no timestamp, no
#  environment read.
#  * THE DIFF IS EXACT: `==` after a type check, and nothing else. There is no
#  tolerance, no epsilon, no closeness helper from the standard library, no
#  approximate-equality helper from the test runner, no case- or
#  whitespace-insensitive comparison and no numeric coercion - a type mismatch,
#  `1` against `"1"`, IS a difference. Rows are aligned by primary-key VALUE,
#  never by position, and the two labels are `cobol` and `python`, never left
#  and right.
#  * THERE IS NO IGNORE-LIST, NO TOLERANCE-LIST AND NO "KNOWN DIFFERENCE"
#  ALLOWANCE anywhere below. Bounding is done by the 22 in-scope tables, which is
#  the protocol; a scenario's affected-table list is its DECLARED EFFECT, asserted
#  against separately, and is never a way to overlook a difference.
#  * NOTHING HERE CORRECTS OBSERVED BEHAVIOUR (rule R-4). No null is coalesced, no
#  missing row is defaulted, no row or column is re-ordered for legibility, and
#  nothing is trimmed beyond harness/normalize.py's own job 1. A helper that
#  tidied a result would be a defect, not a kindness: the whole value of this
#  migration is that the Python cycle can replace the COBOL cycle without changing
#  a single posted figure, and a tidied comparison cannot demonstrate that.
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

    THE SELECTION IS ALWAYS BOUNDED, AND THE BOUND IS ALL 22 IN-SCOPE TABLES.
    `harness/dump_tables.py` REFUSES an unbounded run rather than defaulting, and this
    wrapper passes `--all-in-scope`, which is the protocol. It is NOT the scenario's
    `affected_tables`: both cycles perform the menu's own `overrewrite.`
    [general/general.cbl:L656-L672] - SYSTEM-REC under key 1, SYSDEFLT-REC under key 2
    and SYSTOT-REC under key 4, reproduced by `acas_posting/cli/args.py::overrewrite` -
    so a capture bounded by what a scenario EXPECTS to move could report an empty diff
    while the run date, the allocators, the flags, the defaults or the period totals
    differed. An empty diff is the single pass condition (Agent Action Plan section
    0.8.5), so its scope has to be everything the cycle can persist. Pass `tables` only
    to narrow one table by hand while debugging.

    THE SCENARIO DEFINITION IS NAMED ON EVERY CAPTURE, as provenance and not as a
    selector, because `scenario_file_sha256` is one of the three provenance fields
    stage 9 requires to be present and equal on both sides.

    Args:
        scenario: The scenario name, which also composes the output path.
        side: `cobol` or `python`. Recorded in the PATH, never in a file.
        tables: An explicit `--tables` list, for narrowing one table by hand. When
            omitted all 22 in-scope tables are captured, which is the protocol.
        out_dir: `--out-dir`; `$ACAS_OUT` when omitted.

    Returns:
        The captured result. `EX_OK` is 0; 80 to 87 are the module's documented
        diagnoses.

    Raises:
        ValueError: `side` is not one of the two, or `scenario` is not a plain name.
    """
    assert_side(side)
    assert_scenario_name(scenario)

    argv: list[str] = ["--scenario", scenario, "--side", side, "--quiet"]
    if out_dir is not None:
        argv += ["--out-dir", str(out_dir)]
    if tables is None:
        argv.append("--all-in-scope")
    else:
        argv += ["--tables", ",".join(tables)]
    #  AND THE DEFINITION IS NAMED WHATEVER THE BOUND IS. `--scenario-file` is
    #  provenance here rather than a selector: its digest becomes
    #  `scenario_file_sha256`, one of the three fields `harness/diff_states.py`
    #  requires to be present and EQUAL on both sides before it compares a row.
    #  Omitting it left the field empty on both sides, and stage 9 refused the pair -
    #  which is exactly right, since the definition carries the fan-out switch that
    #  decides which tables the run touches. A hand-driven run passes it at the same
    #  three stages for the same reason - README section 8 spells each one out.
    argv += ["--scenario-file", str(scenario_file(scenario))]

    stage = STAGE_DUMP_COBOL if side == SIDE_COBOL else STAGE_DUMP_PYTHON
    return _drive_harness_main(harness_dump_tables(), argv, stage=stage)


def verify_published(
    scenario: str,
    *,
    out_dir: Path | str | None = None,
) -> StageResult:
    """STAGE 9 - assert both normalised captures declare themselves complete.

    THE STAGE THAT STOPS TWO PARTIAL CAPTURES PASSING. Two trees missing the same
    tables produce an EMPTY DIFF over the tables they both happen to hold, and an empty
    diff is the one pass condition the protocol has (Agent Action Plan section 0.8.5).
    `harness/normalize.py` writes its manifest LAST, so the manifest's presence is what
    says the stage finished; `harness/diff_states.py`'s `verify_trees` additionally
    requires the two manifests to agree on scenario, on side, on run identity and on
    the exact seeded bytes.

    Performed here as its own recorded stage rather than left implicit inside the
    comparison, so a test can see that it ran and a failure names stage 9 rather than
    arriving as a comparison error. A hand-driven run gets the same
    guarantee from stage 10 itself: `harness/diff_states.py` calls this same
    `verify_trees` before it compares a single row and exits 2 rather than 0, so the
    check is never skipped - only reported differently.

    Args:
        scenario: The scenario name.
        out_dir: The output root; `$ACAS_OUT` when omitted.

    Returns:
        The stage result: `returncode` 0 when both captures verify, 2 with the
        diagnosis on `stderr` when they do not. The status is RETURNED rather than
        raised so a caller may inspect it; `run_scenario_parity` calls
        `raise_for_status` on it, because a comparison over unverified captures is not
        evidence.
    """
    assert_scenario_name(scenario)
    paths = scenario_paths(scenario, out_root=out_dir)
    left = paths.normalized_dir(SIDE_COBOL)
    right = paths.normalized_dir(SIDE_PYTHON)
    argv = (
        "tests/conftest.py:verify_published",
        f"--cobol={left}",
        f"--python={right}",
    )
    diff_states = harness_diff_states()
    try:
        manifests = diff_states.verify_trees(left, right)
    except Exception as exc:  # noqa: BLE001 - every refusal is reported identically
        return StageResult(
            stage=STAGE_VERIFY_PUBLISHED,
            argv=argv,
            returncode=diff_states.EX_ERROR,
            stdout="",
            stderr=f"{type(exc).__name__}: {exc}\n",
        )
    return StageResult(
        stage=STAGE_VERIFY_PUBLISHED,
        argv=argv,
        returncode=0,
        stdout=(
            f"both captures are published and agree: scenario "
            f"{manifests[0].get('scenario')!r}, "
            f"{len(diff_states.manifest_tables(manifests[0]))} table(s) declared on "
            f"the {SIDE_COBOL} side and "
            f"{len(diff_states.manifest_tables(manifests[1]))} on the "
            f"{SIDE_PYTHON} side\n"
        ),
        stderr="",
    )


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


# ---------------------------------------------------------------------------
#  THE VALUE-FREE DIAGNOSTIC ROUTE
#
#  A scenario test compares two database states. When it fails, the useful question is
#  WHICH table and WHICH column disagreed - not what the figures were. The two are
#  easily conflated because `harness/diff_states.py` ships both renderers:
#
#  render(tree)     every differing value AND every primary key. Its purpose is the
#  on-disk report, where that detail belongs.
#  summarise(tree)  table, column name and ordinal, and counts. No value, no key.
#
#  The tier used to interpolate `render` into assertion messages, which put real ledger
#  balances, VAT amounts and account identifiers into pytest output. The figures are not
#  lost by withholding them: they are in the report, and the digest below ties a message
#  to the exact file. So this route costs a reader one `cat` and costs a log scraper
#  everything.
#
#  Reached as `ParityRun.diagnose()`, `DeterminismRun.diagnose()`, and the `withheld`
#  fixture for a bare row value. `tests/arithmetic/` has a static test that refuses a
#  new `render(` in this tier, so the route cannot quietly be abandoned again.
# ---------------------------------------------------------------------------


def _report_digest(report: Path | None) -> str | None:
    """Digest one report file, so a message can be tied to the artifact it describes.

    Args:
        report: The report's path, or None when the run produced none.

    Returns:
        The report's SHA-256, or None if there is no readable file at `report`.
    """
    if report is None:
        return None
    try:
        import hashlib

        return hashlib.sha256(Path(report).read_bytes()).hexdigest()
    except OSError:
        # A message about a missing report must still be printable.
        return None


def _diagnose_tree(tree: Any, *, report: Path | None) -> str:
    """Summarise a comparison for a failure message, withholding every value.

    Args:
        tree: The `TreeDiff` to summarise.
        report: Where the full report - values included - was written.

    Returns:
        `harness/diff_states.py`'s own value-free summary. The empty string when the
        trees are identical, matching the zero-byte report a passing run writes.
    """
    return str(
        harness_diff_states().summarise(
            tree, report_path=report, report_digest=_report_digest(report)
        )
    )


def _withheld(value: Any, *, column: str | None = None, artifact: Any = None) -> str:
    """Describe a row value's SHAPE for a failure message, never its content.

    The stand-in for interpolating a dumped row, a row collection or one column's
    value. What a failure needs is that something differed, how much of it, and where
    the detail is; what it does not need is the figure itself.

    Args:
        value: Whatever would have been interpolated - a scalar, a sequence of rows, a
            set of keys or a mapping.
        column: The column the value came from, if it is one column's.
        artifact: The dump or report the content can be read from, if there is one.

    Returns:
        A bracketed value-free description, safe to place in any message.
    """
    if isinstance(value, Mapping):
        shape = f"{len(value)} column(s)"
    elif isinstance(value, (str, bytes)) or not isinstance(value, Sequence | set | frozenset):
        shape = "1 value"
    else:
        shape = f"{len(value)} value(s)"

    parts = [shape]
    if column is not None:
        parts.append(f"of {column}")
    parts.append("withheld")
    if artifact is not None:
        parts.append(f"- see {artifact}")
    return f"<{' '.join(parts)}>"


@pytest.fixture
def withheld() -> Callable[..., str]:
    """A value-free stand-in for a dumped row value, for assertion messages.

    Returns:
        `_withheld`, callable as `withheld(value, column=..., artifact=...)`.
    """
    return _withheld


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
    """STAGE 10 - compare the two normalised trees. AN EMPTY DIFF IS THE PASS.

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
        tables: An explicit table list, in report order, for narrowing one table by
            hand. By default all 22 in-scope tables are compared - `--all-in-scope`,
            which is the protocol - and the scenario file is passed alongside it so the
            declared-effect gate that refuses an all-empty comparison still applies.
            The scenario's own `affected_tables` is NOT the comparison bound: both
            cycles perform `overrewrite.` [general/general.cbl:L656-L672], so a
            comparison narrowed to a scenario's expected effect could report an empty
            diff while a system row differed.
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
        #  `--all-in-scope` OUTRANKS the scenario's own list and bounds the
        #  comparison at 22 tables; the scenario file is still passed because
        #  `diff_states.py` reads it for the gate that refuses an all-empty
        #  comparison against a scenario that declares a changed effect.
        argv += ["--all-in-scope", "--scenario-file", str(path)]
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
        tuple(tables)
        if tables is not None
        else tuple(diff_states.IN_SCOPE_TABLES)
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


# ---------------------------------------------------------------------------
#  THE THREE-WAY EXIT CONTRACT OF STAGE 8, IN ONE PLACE
#
#  A TEST THAT TREATED "COULD NOT COMPARE" AS "NO DIFFERENCES" IS THE SINGLE WORST
#  BUG AVAILABLE IN THIS TREE, and rule R-6 makes an empty diff the pass condition
#  ONLY when a comparison actually happened. Every scenario file therefore wants to
#  assert the contract - and four of them used to do it by asserting module constants
#  and building their own dataclasses, which passes whatever the comparison does.
#
#  So the contract is exercised HERE, ONCE, against the SHIPPED comparison: trees are
#  published through the dump stage's own writer, canonicalised by the real
#  normalisation stage and compared by `harness/diff_states.py` itself. It needs no
#  Compose stack, no oracle and no database - stages 4 and 8 are file-to-file
#  transformations driven in process - so every scenario file can call it on a bare
#  host.
#
#  IT ASSERTS NOTHING WHATEVER ABOUT THE MIGRATION, and none is claimed: the trees
#  are synthetic, built from the frozen schema's own column lists. It is the
#  COMPARISON that is under test, not either cycle.
#
#  Agent Action Plan section 0.4.3 puts it here rather than in a shared test helper:
#  "tests/conftest.py provides the pinned-clock fixture and the seed/dump/normalize/
#  diff helpers so that no test reimplements the comparison protocol", and this file
#  is the only shared surface the tree is permitted.
# ---------------------------------------------------------------------------


def assert_diff_exit_contract(
    scenario: str,
    *,
    out_dir: Path | str,
    harness: HarnessModules,
    schema: Mapping[str, Mapping[str, Any]],
    vocabulary: Vocabulary,
    readouterr: Callable[[], Any],
) -> None:
    """Exercise stage 8's THREE-WAY exit contract against the real comparison.

        0  the trees are identical, and stdout is EMPTY - zero bytes, not a banner
           and not "no differences found"                                 -> PASS
        1  a real behavioural difference, with a deterministic report   -> FAILURE
        2  THE COMPARISON COULD NOT BE PERFORMED - an unattested capture, a capture
           taken after a failed run, or a missing tree                     -> ERROR

    Every case is driven end to end: two synthetic sides are published with
    `harness/dump_tables.py`'s own writer, normalised by `harness/normalize.py` and
    compared by `harness/diff_states.py`. The two refusals are driven through
    `diff_states.main` directly, because the `diff` helper maps exit 2 to a harness
    fault by design and here a refusal is the expected outcome.

    Args:
        scenario: The scenario the synthetic trees are published under. The trees
            themselves cover ALL 22 IN-SCOPE TABLES, because that is the bound the
            comparison is given; see the note at `tables` below.
        out_dir: A private output root - a test's `tmp_path` - so `$ACAS_OUT` is
            neither read nor needed and nothing is written into a compared tree.
        harness: The three harness modules (rule R-1).
        schema: The parsed `mysql/ACASDB.sql`, READ AND NEVER WRITTEN. It supplies
            every column name and declared type, so nothing is invented.
        vocabulary: The stack-free bundle, for the side labels, the scenario file and
            the normalise and diff stages.
        readouterr: `capsys.readouterr`, so the two refusals' streams can be read
            where they are written.

    Raises:
        AssertionError: An exit status, a stdout stream or a verdict did not match the
            contract.
    """
    assert_scenario_name(scenario)
    root = Path(out_dir)
    dump_tables = harness.dump_tables
    normalize_module = harness.normalize
    diff_states = harness.diff_states

    #  ALL 22 IN-SCOPE TABLES, because that is the bound the diff stage is GIVEN:
    #  `vocabulary.diff` drives `harness/diff_states.py --all-in-scope`. Fabricating
    #  only the scenario's declared effect would make the two synthetic captures and the
    #  comparison disagree about their scope, and the comparison REFUSES that with exit
    #  2 - correctly, since two partial captures can be trivially equal over whatever
    #  they both happen to hold. The declared effect is asserted elsewhere; what this
    #  helper exercises is the exit contract under the real bound.
    tables = tuple(dump_tables.IN_SCOPE)
    paths = vocabulary.paths(scenario, out_root=root)

    #  THE DECLARED OPERATIONS, read from the scenario's own definition, because the
    #  record carries ONE disposition per operation and a record that named a different
    #  number would be refused before any comparison happened.
    operations = tuple(vocabulary.definition(scenario)["operations"])
    #  A syntactically valid digest, so the two provenance fields are present and
    #  well-formed. Its VALUE means nothing here: these are synthetic sides, and what is
    #  being exercised is the exit contract rather than a seed identity.
    synthetic_digest = "0" * 64

    def attest(side: str, *, status: int = 0) -> None:
        """Write the run-status record the dump stage reads its attestation from.

        A capture carries what its RUN stage claimed, and the comparison stage refuses
        a pair that claims nothing: two captures taken after failed runs are trivially
        equal, and equality is the pass condition, so the harness would otherwise
        certify parity having compared nothing. Written through the tool's own path
        helper rather than a hand-built path, so the two cannot drift.

        EVERY REQUIRED KEY IS WRITTEN, and the set is asserted against
        `harness/dump_tables.py`'s own `RUN_STATUS_REQUIRED_KEYS` rather than
        transcribed: the record must carry the run identity, the wrapper's own status,
        both seed digests and one `operation_status` row per declared operation, or the
        comparison refuses it for the WRONG reason and the case below would pass while
        measuring nothing.

        Args:
            side: `cobol` or `python`.
            status: The status the run stage claimed for this side.
        """
        fields = {
            "scenario": scenario,
            "side": side,
            "run_id": f"{scenario}-0001",
            "status": str(status),
            "wrapper_status": str(status),
            "seed_fingerprint_sha256": synthetic_digest,
            "seed_marker_sha256": synthetic_digest,
            "operations": str(len(operations)),
        }
        missing = sorted(dump_tables.RUN_STATUS_REQUIRED_KEYS - fields.keys())
        assert not missing, (
            f"the synthetic run-status record omits {missing}, which "
            f"harness/dump_tables.py requires - the comparison would refuse it for a "
            f"reason this contract is not about."
        )
        lines = [f"{key}\t{value}" for key, value in fields.items()]
        lines += [
            f"operation_status\t{index}\t{operation}\t{status}"
            for index, operation in enumerate(operations, start=1)
        ]
        target = dump_tables.run_status_path(root, scenario, side)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def publish(side: str, *, bend: bool, identify: bool = True) -> None:
        """Publish one synthetic side, then canonicalise it through stage 4.

        Args:
            side: `cobol` or `python`.
            bend: Alter exactly one non-key value of the first table, so the two sides
                differ in exactly one column of exactly one row.
            identify: Record the run id in the manifest's provenance. False models a
                dump taken by hand, out of order, with no attempt to belong to - which
                is what the first case below is about. The comparison has a DIFFERENT
                refusal for each: a capture carrying an identity but no attestation is
                refused by the attestation gate, and one carrying neither is refused by
                the identity gate first. Both are exit 2; the case that asserts the
                attestation wording therefore withholds the identity.
        """
        dumps: dict[str, dict[str, Any]] = {}
        for table in tables:
            columns = normalize_module.schema_columns(schema, table)
            specification = dump_tables.IN_SCOPE[table]
            row: list[Any] = []
            for column in columns:
                declared = normalize_module.column_type(schema, table, column)
                if declared.kind == normalize_module.KIND_INTEGER:
                    row.append(0)
                elif declared.kind == normalize_module.KIND_DECIMAL:
                    # A DECIMAL reaches a dump as a canonical JSON STRING at the
                    # column's declared scale, never as a JSON number (rule R-2).
                    row.append("0")
                else:
                    row.append("")
            key_index = list(columns).index(specification.primary_key)
            row[key_index] = 1 if isinstance(row[key_index], int) else "1"
            if bend and table == tables[0]:
                victims = [
                    index for index in range(len(columns)) if index != key_index
                ]
                assert victims, (
                    f"{table} has only its primary-key column, so no non-key value "
                    f"can be altered to produce a difference."
                )
                victim = victims[0]
                row[victim] = 7 if isinstance(row[victim], int) else "7"
            # Built from the dump stage's OWN key vocabulary, in its own fixed order,
            # so the five-key shape is never transcribed by hand.
            dumps[table] = dict(
                zip(
                    dump_tables.DUMP_KEYS,
                    (table, specification.primary_key, list(columns), 1, [row]),
                    strict=True,
                )
            )
        dump_tables.publish_dumps(
            dumps,
            root,
            scenario=scenario,
            side=side,
            selector=dump_tables.SELECTOR_ALL_IN_SCOPE,
            #  THE RUN IDENTITY REACHES THE MANIFEST, or the comparison refuses the pair
            #  for want of one: a verdict that cannot state which attempt
            #  it is about is a verdict about an unidentified pair of captures. The id is
            #  the one `attest` wrote, so the record and the manifest agree.
            provenance=dump_tables.build_provenance(
                run_id=f"{scenario}-0001" if identify else None,
                scenario_file=vocabulary.scenario_file(scenario),
                repository=REPO_ROOT,
                command=["assert_diff_exit_contract", scenario, side],
            ),
            # Read through the tool's own reader, so what lands in the manifest is
            # what a real run would put there rather than a literal about its shape.
            attestation=dump_tables.read_run_attestation(root, scenario, side),
        )
        vocabulary.normalize(scenario, side, out_dir=root).raise_for_status()

    cobol_side, python_side = vocabulary.sides[0], vocabulary.sides[1]

    # ---- EXIT 2: NEITHER SIDE ATTESTS A RUN -- refused before any compare ----
    # Asserted BEFORE the attestations are written, so the refusal is measured on
    # captures that never claimed anything - the state a dump taken out of order
    # actually leaves behind.
    publish(cobol_side, bend=False, identify=False)
    publish(python_side, bend=False, identify=False)
    refusal_argv = [
        "--scenario",
        scenario,
        "--quiet",
        "--out-dir",
        str(root),
        "--scenario-file",
        str(vocabulary.scenario_file(scenario)),
    ]
    readouterr()
    unattested_status = diff_states.main(refusal_argv)
    unattested_streams = readouterr()
    assert unattested_status == diff_states.EX_ERROR, (
        f"a capture whose run stage attests nothing must be REFUSED with "
        f"{diff_states.EX_ERROR}, never compared: two captures taken after failed "
        f"runs are trivially equal, and equality is the pass condition. It exited "
        f"{unattested_status}."
    )
    assert unattested_streams.out == "", (
        f"a refusal writes its diagnosis to stderr and leaves stdout EMPTY, so an "
        f"empty stdout can never be read as a pass on its own. It wrote "
        f"{unattested_streams.out!r}."
    )
    assert "attest" in unattested_streams.err.lower(), (
        f"the refusal must say WHY, naming the missing attestation. stderr was "
        f"{unattested_streams.err!r}."
    )

    # ---- EXIT 2: A RUN NOBODY MAY CONCLUDE FROM IS NOT A RUN --------------
    #  THE STATUS HERE IS A HARNESS FAULT, NOT MERELY NON-ZERO, and the distinction
    #  is the whole of it. `BEHAVIOURAL_RUN_STATUS` - 69 - is a REPRODUCED
    #  abort, which is comparable BY DESIGN: the term-code-5 chain is correct compiled
    #  behaviour and the state it leaves is exactly what must be diffed. So a case built
    #  on 69 would assert the opposite of the contract. What is refused is a status the
    #  harness cannot vouch for, and the fault status is taken from the vocabulary's own
    #  classification rather than written as a literal.
    fault_status = 71
    #  Asserted against the comparison's OWN disposition model, so the choice of status
    #  is evidenced rather than assumed.
    assert (
        dump_tables.DISPOSITION_BEHAVIOURAL in dump_tables.COMPARABLE_DISPOSITIONS
    ), "a reproduced abort is comparable, which is why it is not the status used here"
    assert (
        dump_tables.DISPOSITION_HARNESS_FAULT
        not in dump_tables.COMPARABLE_DISPOSITIONS
    )
    attest(cobol_side, status=0)
    attest(python_side, status=fault_status)
    fault_attestation = dump_tables.read_run_attestation(root, scenario, python_side)
    assert fault_attestation["disposition"] == dump_tables.DISPOSITION_HARNESS_FAULT, (
        f"status {fault_status} must read back as a harness fault for this case to be "
        f"about an uncomparable capture at all; it read "
        f"{fault_attestation['disposition']!r}."
    )
    publish(cobol_side, bend=False)
    publish(python_side, bend=False)
    readouterr()
    failed_run_status = diff_states.main(refusal_argv)
    failed_run_streams = readouterr()
    assert failed_run_status == diff_states.EX_ERROR, (
        f"a capture taken after a run the harness cannot vouch for must be REFUSED "
        f"with {diff_states.EX_ERROR}. It exited {failed_run_status}."
    )
    assert failed_run_streams.out == "", (
        f"a refusal writes its diagnosis to stderr and leaves stdout EMPTY. It wrote "
        f"{failed_run_streams.out!r}."
    )
    assert paths.python_normalized.name in failed_run_streams.err, (
        f"the refusal must name the capture it refused, so an operator is not left "
        f"guessing which side failed. stderr was {failed_run_streams.err!r}."
    )
    #  AND THE STATUS IS RECORDED VERBATIM IN THE CAPTURE, which is the substantive
    #  half of this case: the run stage's own number survives into the manifest, so the
    #  refusal is traceable to what actually happened rather than to a generic fault.
    #  Asserted on the manifest rather than on the refusal's wording, because a
    #  harness-fault attestation deliberately carries NO seed identity and no run id -
    #  `read_run_attestation` withholds both - so the comparison refuses at the seed-
    #  identity gate before it reaches the status. Both gates are exit 2, and which one
    #  speaks first is the comparison's business, not this contract's.
    refused_manifest = diff_states.read_manifest(paths.python_normalized)
    assert refused_manifest is not None
    refused_attestation = refused_manifest["attestation"]
    assert refused_attestation["attested"] is False
    assert refused_attestation["run_status"] == fault_status
    assert refused_attestation["disposition"] == dump_tables.DISPOSITION_HARNESS_FAULT

    # ---- EXIT 0: identical, and NOT ONE BYTE on stdout -------------------
    attest(cobol_side)
    attest(python_side)
    publish(cobol_side, bend=False)
    publish(python_side, bend=False)
    identical = vocabulary.diff(scenario, out_dir=root)
    assert identical.result.returncode == diff_states.EX_IDENTICAL
    assert identical.is_empty is True
    assert identical.result.stdout == "", (
        f"an identical comparison must write ZERO BYTES to stdout - not a banner, "
        f'not "no differences found" - because the empty stream is itself the pass '
        f"signal. It wrote {identical.result.stdout!r}."
    )
    # A PASSING RUN WRITES A ZERO-BYTE REPORT, deliberately: the evidence document
    # must distinguish "compared, and identical" from "never compared", and an
    # existing empty file says the first while an absent file says nothing at all.
    assert identical.report.is_file()
    assert identical.report.stat().st_size == 0

    # ---- EXIT 1: one differing value is a real behavioural difference -----
    publish(python_side, bend=True)
    different = vocabulary.diff(scenario, out_dir=root)
    assert different.result.returncode == diff_states.EX_DIFFERENT
    assert different.is_empty is False
    assert different.tree.total_differences == 1
    # Stdout carries a value-free summary; the values themselves go to the 0600
    # report. Either way the stream is NOT empty, so exit 1 can never be mistaken
    # for exit 0.
    assert different.result.stdout != ""
    report = diff_states.render(different.tree)
    assert tables[0] in report
    # The two labels are `cobol` and `python`, never left and right.
    assert diff_states.LABEL_COBOL in report
    assert diff_states.LABEL_PYTHON in report

    # ---- EXIT 2: the comparison could not be performed -> RAISED ----------
    # An absent tree is the most dangerous input the comparison can be given, because
    # "nothing to compare" and "nothing differs" are one keystroke apart.
    for member in sorted(paths.python_normalized.iterdir()):
        member.unlink()
    paths.python_normalized.rmdir()
    with pytest.raises(vocabulary.fault) as raised:
        vocabulary.diff(scenario, out_dir=root)
    assert str(diff_states.EX_ERROR) in str(raised.value)
    # AND THE STALE ZERO-BYTE REPORT IS GONE. The comparison invalidates the accepted
    # output the moment the path is known and before a single dump is read, so a
    # report surviving an error path can never be mistaken for proof that this run
    # passed.
    assert not paths.diff_report.exists()


def assert_runtime_autocommit_on(connection: Any) -> None:
    """Assert the RUNTIME autocommit mode is ON, globally and for this session.

    THE MODE IS SCOPED, NOT PINNED, and the scope is the settled half of
    [docs/migration/ambiguity-resolutions.md#q-10]. The Agent Action Plan requires
    autocommit OFF and cites the same frozen banner three times - §0.2.1.1 "the batch
    loader turns autocommit off", §0.5.2 "autocommit must be off DURING SEEDING", and
    §0.4.1.7 on `harness/Dockerfile.mariadb` "autocommit off to match the loaders" -
    and all three provisions name the SEEDING stage in their own words. Every
    connection this protocol opens outside that window - the compiled posting run, the
    Python cycle, the reset and the two dumps - is RUNTIME APPLICATION ACCESS and runs
    with the mode ON.

    WHY THE WIDER READING CANNOT BE THE ONE MEANT: the frozen loaders and bridges
    reach no COMMIT, so under a server-wide OFF pin nothing either cycle writes
    survives its own session, every capture is empty, and an empty diff is the
    protocol's only pass condition (AAP §0.8.5). The wider reading makes the AAP's own
    validation criteria unsatisfiable. The frozen sources say the same thing:
    [common/glbatchLD.cbl:L9-L13] is a four-line COMMENT BANNER addressed to the
    operator, the vendored `cobmysqlapi38.c` exposes `MySQL_commit` and
    `MySQL_rollback` but NOT `MySQL_autocommit`, and every `perform aa020-Rollback`
    in all 28 `common/*LD.cbl` loaders is commented out with the single
    `perform aa030-Commit` anywhere commented out too.

    THE MODE IS ASSERTED AND NEVER SET, exactly as before - only the asserted value
    changed. `harness/Dockerfile.mariadb` is the single authority for the runtime
    mode: it declares `autocommit=1` in `/etc/mysql/conf.d/99-acas-oracle.cnf`.
    `harness/seed.sh` is the ONLY place the mode is ever changed - it opens a seeding
    window immediately before the first frozen load program, verifies the mode from a
    fresh session, and restores the runtime mode from its exit trap on every path,
    exiting 73 if it cannot. WHICH mode that window runs follows the Agent Action
    Plan: `@@GLOBAL.autocommit = 0` is its default, per AAP sections 0.2.1.1, 0.4.1.7
    and 0.5.2, and under it seven loaders report success, the tables read empty and
    `seed.sh` exits 76 - the frozen no-COMMIT defect, reproduced and refused rather
    than papered over. `ACAS_SEED_AUTOCOMMIT=on` selects `1`, the only mode MEASURED
    to leave a durable row, as an explicitly declared deviation. The loader return
    codes are identical under both, so the mode is invisible to the frozen code,
    which is why the deviation is available at all - not why it could be silent. Either way the window is closed before this assertion is ever reached. `harness/reset_db.sh` (83)
    and `harness/run_cobol_scenario.sh` (73) assert this same runtime mode. A fixture
    that quietly issued `SET autocommit` would put the test runner in charge of a
    setting the harness owns.

    ONLY `@@GLOBAL` IS ASSERTED HERE, AND THAT IS DELIBERATE - the server-level value
    is the one the harness owns and the one Q-10 settles. `@@SESSION` is reported but
    not required, because on THIS connection it is a property of the Python driver
    rather than of the server: `mysql-connector-python` defaults `autocommit` to
    False and issues `SET autocommit = 0` for its own session, so a correctly
    configured server measures `global=1, session=0` here while the `mariadb` client
    used by `harness/reset_db.sh` and `harness/run_cobol_scenario.sh` inherits the
    global and measures `1/1`. Requiring 1 for the session would therefore refuse
    every correctly configured server. It is safe to leave unrequired for the same
    reason `harness/dump_tables.py` gives for setting no session state at all: this
    connection is SELECT-only and is released with `rollback()`, so its autocommit
    value cannot affect what it reads. The two sides that DO write pin their own mode
    - the compiled cycle inherits the asserted server mode, and the migrated cycle
    sets `autocommit: True` explicitly at `acas_posting/dal/connection.py mysql_1000_open`,
    per-statement as the COBOL does, which is why `harness/run_python_scenario.sh`
    OBSERVES the mode and never refuses on it.

    A REPRODUCED DEFECT WORTH KNOWING WHILE READING A RESULT (rule R-4): the frozen
    loaders reach no COMMIT, so under the AAP-literal OFF window a table reads EMPTY
    after a seed that reported success. Nothing here issues the missing COMMIT - a
    defect fixed is a failure; `harness/seed.sh` instead refuses fail-closed (76) when
    a seed reports success and leaves the tables empty, whichever mode was selected.

    Args:
        connection: An open DB-API connection.

    Raises:
        AssertionError: `@@GLOBAL.autocommit` is not 1.
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
    assert global_setting == 1, (
        f"the server's RUNTIME autocommit mode is OFF (global={global_setting}, "
        f"session={session_setting} on this driver's own connection); the protocol "
        f"is REFUSED. Every connection this protocol opens outside the seeding "
        f"window is RUNTIME APPLICATION ACCESS, and the Agent Action Plan scopes "
        f"its autocommit-OFF requirement to seeding in all three of its provisions "
        f"- sections 0.2.1.1, 0.5.2 and 0.4.1.7 - as recorded in "
        f"docs/migration/ambiguity-resolutions.md#q-10. Finding the global mode OFF "
        f"means either that the server is pinned to the seeding mode server-wide, "
        f"which leaves the frozen COBOL unable to persist a single row because it "
        f"never reaches a COMMIT, so every capture is empty and an empty diff is "
        f"the protocol's only pass condition; or that a seed was interrupted before "
        f"its exit trap could restore the runtime mode. This assertion never sets "
        f"the mode: harness/Dockerfile.mariadb declares autocommit=1 for runtime "
        f"access and harness/seed.sh is the only place it is ever changed. Start "
        f"the harness MariaDB service built from that Dockerfile, or restore the "
        f"runtime mode with: set global autocommit = 1"
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
#  THE TEN STAGES, IN THE EXACT ORDER. The order and the numbering are NOT restated
#  here as fact - they are DEFINED in `PARITY_STAGES` in harness/normalize.py and published
#  by `harness/normalize.py --print-stages`, which `parity_stage_registry` reads and a
#  test asserts these constants against. Each side is normalised as its
#  own stage, and the second normalisation is NOT numbered `7b` to keep the protocol
#  eight-stage: that would make a stage number in a test message name a different stage
#  from the same number in a driver transcript:
#
#  1  harness/reset_db.sh             "$S"  (schema + seed)
#  2  harness/run_cobol_scenario.sh   "$S"  (every declared operation, in order)
#  3  harness/dump_tables.py  --scenario N --side cobol  --all-in-scope --scenario-file "$S"
#  4  harness/normalize.py    --scenario N --side cobol
#  5  harness/reset_db.sh             "$S"  (the SAME fixture bytes)
#  6  harness/run_python_scenario.sh  "$S"
#  7  harness/dump_tables.py  --scenario N --side python --all-in-scope --scenario-file "$S"
#  8  harness/normalize.py    --scenario N --side python
#  9  both captures declare themselves complete   (an in-driver check)
#  10  harness/diff_states.py  --scenario N --all-in-scope --scenario-file "$S"
#
#  THE TWO OPTIONS ON STAGES 3, 7 AND 10 ARE NOT ALTERNATIVES. `--all-in-scope' is the
#  BOUND -- all 22 in-scope tables, for the `overrewrite.' reason stated above
#  `capture_state' -- and `--scenario-file' is the PROVENANCE, whose sha256 becomes the
#  `scenario_file_sha256' stage 10 requires present and EQUAL on both sides. Passing
#  only the second NARROWS the bound to the scenario's declared effect, which is the
#  debugging mode; passing only the first leaves the provenance field empty and stage 10
#  refuses the pair. So both are passed together, here and in the hand-driven recipe
#  (README section 11.1a). Only `--tables' and `--all-in-scope' are mutually exclusive.
#
#  The Agent Action Plan's EIGHT logical stages (section 0.3.2) become these ten by
#  numbering both normalisations and the publication check instead of folding them in,
#  so where older prose in this repository says "stage 8" of the protocol it means
#  today's stage 10. Separately, the runners print their own `Check n/8' headings;
#  those are each script's internal preflight checks and are NOT protocol stages.
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
#
#  ONE MULTI-OPERATION PROTOCOL, SYMMETRIC ON BOTH SIDES. Stages 2 and 6 drive the
#  scenario's OWN ordered `operations` list - not its scalar `operation` key - so the
#  two sides do the same work in the same order. `period_end_totals` is the one
#  committed example, with four operations:
#
#  * NO RESET BETWEEN OPERATIONS. The claim is cumulative: operation 2 rewrites the
#  ledger rows operation 1 created, and re-seeding in between would measure four
#  unrelated runs instead of one journey.
#  * ONE STATUS PER OPERATION. Each side emits an `OPERATION_STATUS` record per
#  operation and `_attach_operation_statuses` refuses a wrapper that exits zero
#  without the complete ordered set, so no capture can be attributed to an
#  operation whose disposition was never established.
#  * ONE DUMP PER SIDE, after the last operation. Stages 3 and 7 run once.
#  * THE ORACLE SIDE SPANS SEVERAL MENU PROCESSES because one compiled menu drives
#  one subsystem, and `period_end_totals` reaches two of them. That is handled
#  INSIDE one runner invocation, not by invoking the runner once per operation:
#  `harness/run_cobol_scenario.sh` takes a repeatable `--operation`, selects the
#  menu for each in turn, and publishes one disposition per operation. The
#  alternative - one invocation per operation, with operation one's records copied
#  back over the last one's - would leave operations 2..n with no attested
#  disposition at all; the pre-run fingerprint is taken
#  ONCE before operation one and the post-run fingerprint ONCE after the last,
#  which is exactly the span the journey covers.
#  * AND THE SYMMETRY IS ASSERTED, not assumed: after stage 6 the two recorded
#  operation lists are compared, and a disagreement is a harness fault.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ParityRun:
    """One scenario's complete parity run: every stage, and the verdict.

    Attributes:
        scenario: The scenario name.
        tables: The list the comparison was bounded by: ALL 22 in-scope tables,
            not the scenario's declared `affected_tables`. Both cycles perform
            `overrewrite.` [general/general.cbl:L656-L672], so a comparison
            narrowed to a scenario's expected effect could report an empty diff
            while a system row differed.
        stages: Every stage result in execution order, including the two run stages
            whose non-zero status is behavioural data rather than an error.
        cobol_run: The oracle run's result, for a test asserting on its status.
        python_run: The migrated cycle's run result.
        outcome: The stage-10 verdict.
        paths: Where every artifact of this run lives.
        run_id: The one id bound through all ten stages. Every artifact
            this run published records it, and stage 10 refused the pair unless both
            captures carried this exact value - so it is the handle a reader uses to
            find this run's evidence and to prove the two captures are one attempt.
    """

    scenario: str
    tables: tuple[str, ...]
    stages: tuple[StageResult, ...]
    cobol_run: StageResult
    python_run: StageResult
    outcome: DiffOutcome
    paths: ScenarioPaths
    run_id: str = ""

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

    def diagnose(self) -> str:
        """What differed, WITHOUT any differing value. For a failure message.

        THE VALUE-FREE ROUTE. Use this and never
        `harness/diff_states.py`'s `render`: `render` exists to write the on-disk
        report and it prints every differing value AND every primary key, so
        interpolating it into an assertion message copies real accounting figures and
        real account identifiers into pytest output and from there into any log that
        collects it.

        Nothing is lost by withholding them, because they are not discarded - they are
        in the report this names, and the digest ties this message to that exact file.
        A reader who needs the figures opens the artifact; a log that scrapes stdout
        does not get them.

        Returns:
            The table, column and count summary, with the report's path and digest.
            The empty string when the two trees are identical.
        """
        return _diagnose_tree(self.tree, report=self.outcome.report)


#: One completed :class:`ParityRun` per distinct request, for the lifetime of the
#: session. The key is `(scenario, operation, out_dir-as-text, max_differences)` - every
#: argument that changes what the protocol does. See the long comment inside
#: :func:`run_scenario_parity` for why sharing one run per request is a coherence
#: requirement of the scenario tier rather than a performance optimisation.
_PARITY_RUN_CACHE: dict[
    tuple[str, str | None, str | None, int | None], "ParityRun"
] = {}


def run_scenario_parity(
    scenario: str,
    *,
    operation: str | None = None,
    out_dir: Path | str | None = None,
    max_differences: int | None = None,
) -> ParityRun:
    """Run all ten protocol stages for one scenario and return the verdict.

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
        max_differences: Passed to stage 10. It truncates the report only and never
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

    #  THE ORDERED OPERATION LIST THIS REQUEST STANDS FOR, resolved HERE so that the
    #  stage helper can name it in a diagnostic without re-deriving it. `operation is
    #  None` means "every operation the scenario declares, in its declared order",
    #  which is the same rule both runners apply, so the tuple below is what stage 2
    #  and stage 6 are each expected to report having driven.
    requested_operations = _requested_operations(
        scenario, operation, all_declared=operation is None
    )

    # ONE RUN PER DISTINCT REQUEST, FOR THE WHOLE SESSION. Keyed on every argument
    # that changes what the protocol does, so two callers asking different questions
    # still get their own runs and two callers asking the SAME question get the SAME
    # answer. `out_dir` is normalised to a string because a caller may pass either a
    # `Path` or a `str` for the same directory.
    #
    # WHY THIS IS A CORRECTNESS FIX AND NOT A SPEED ONE, which matters because Agent
    # Action Plan section 0.8.4 sets no performance target and forbids optimising for
    # one. A scenario module's assertions are each a claim about ONE run: "the diff is
    # empty", "this batch was not stamped in that run", "the report the verdict came
    # from says so". A file that re-ran the protocol per test let nine tests reason
    # about nine different runs and then report agreement between them, which is a
    # quiet incoherence rather than nine independent confirmations - and if two of
    # those runs ever disagreed, the file would still be green. Sharing one run is what
    # makes the file's own narrative true. Most of the scenario modules already
    # memoised in module-level state to get this; doing it HERE means all eight get it,
    # and no future module has to remember.
    #
    # NOTHING READS THE LIVE DATABASE THROUGH A CACHED RUN. Every artifact of a
    # completed run is on disk - both dumps, both normalised trees, the diff report -
    # and that is what the assertions read. The one fixture that does go back to the
    # database, `seed_baseline`, resets it deliberately and is itself memoised.
    # tests/determinism/ does not come through here at all: it drives `reset`,
    # `run_python`, `dump` and `normalize` directly, precisely because it needs two
    # runs, so this cache cannot collapse the two runs a determinism claim compares.
    #
    # STRICTLY SEQUENTIAL still (R-3): this is a plain dict on one thread, with no lock
    # because there is nothing to race.
    cache_key = (
        scenario,
        operation,
        None if out_dir is None else str(out_dir),
        max_differences,
    )
    cached = _PARITY_RUN_CACHE.get(cache_key)
    if cached is not None:
        return cached

    #  THE COMPARISON BOUND IS ALL 22 IN-SCOPE TABLES, not the scenario's declared
    #  `affected_tables`. The declared list remains the runners' own
    #  changed/unchanged assertion; it is not the evidence bound, because a bound
    #  drawn from what a scenario EXPECTS to move cannot show a difference in
    #  anything it did not expect to move.
    tables = in_scope_tables()
    paths = scenario_paths(scenario, out_root=out_dir)
    stages: list[StageResult] = []

    # ONE RUN ID, BOUND BEFORE STAGE 1 AND HELD TO STAGE 10.
    #
    # This is what makes the composed protocol the SAME protocol as the driven one.
    # Without it every stage is a separate process that mints its own identity, the
    # two sides end up carrying two different ids, and stage 10 refuses the pair -
    # correctly, because PROVENANCE_MUST_MATCH names `run_id' and an empty diff
    # between two captures of different runs says nothing about the migration. It is
    # bound around stage 1 rather than stage 2 because `harness/reset_db.sh` publishes
    # the seed identity under this id and `acas_read_seed_identity` DISCARDS a record
    # staged by a different attempt, which would strand the seed marker that the
    # requires to be present and equal on both sides.
    with bound_run_id() as run_id:
        return _run_scenario_parity_stages(
            scenario,
            operation=operation,
            out_dir=out_dir,
            max_differences=max_differences,
            tables=tables,
            paths=paths,
            stages=stages,
            run_id=run_id,
            cache_key=cache_key,
            requested_operations=requested_operations,
        )


def _run_scenario_parity_stages(
    scenario: str,
    *,
    operation: str | None,
    out_dir: Path | str | None,
    max_differences: int | None,
    tables: tuple[str, ...],
    paths: ScenarioPaths,
    stages: list[StageResult],
    run_id: str,
    cache_key: tuple[object, ...],
    requested_operations: tuple[str, ...],
) -> ParityRun:
    """Drive the ten stages with one run id already bound.

    Split out of `run_scenario_parity` so the binding is a single `with` around the
    whole protocol rather than an indent of every stage, which keeps each stage
    comment where a reader expects it.

    Args:
        scenario: The scenario name, already validated.
        operation: `--operation` for both runners, or None for every declared one.
        out_dir: The output root, or None for `$ACAS_OUT`.
        max_differences: Passed to stage 10; truncates the report only.
        tables: The scenario's affected-table list.
        paths: The resolved artifact paths.
        stages: The list to append each stage result to.
        run_id: The bound run id, recorded on the returned run.
        cache_key: The caller's memo key for this request. Passed in rather than
            recomputed so that the entry this function writes and the entry the
            caller looked up cannot be two different keys - the whole value of the
            memo is that a second caller asking the same question gets the same
            `ParityRun`, and a key derived twice from two scopes is exactly how that
            guarantee is lost.
        requested_operations: The ordered operations this request stands for, already
            resolved by the caller. Used only in the operation-mismatch diagnostic,
            where it is the third term a reader needs: what was asked for, beside
            what each side reported driving.

    Returns:
        The complete run.

    Raises:
        HarnessFaultError: A stage whose failure destroys the evidence failed.
    """
    # STAGE 1. Start from a clean schema, then seed. Using seed.sh alone here
    # would preserve rows from a prior scenario and make stage 1 differ from the
    # identical reset-and-seed command at stage 5.
    stages.append(prepare_scenario(scenario).raise_for_status())

    # STAGE 2. THE STATUS IS RECORDED, NOT ENFORCED - see the section comment.
    #
    # ONE INVOCATION, WHATEVER THE COUNT. `operation` is passed through
    # unchanged - None means "every operation the scenario declares" - and the runner
    # resolves the ordered list itself. `period_end_totals` spans two menu executables
    # and the runner drives all four of its operations one at a time against one
    # seeded state, publishing an ordered status row for each.
    cobol_run = run_cobol(scenario, operation=operation, out_dir=out_dir)
    stages.append(cobol_run)

    # STAGES 3 and 4. Taken WHATEVER stage 2 returned: absence is evidence.
    stages.append(dump(scenario, SIDE_COBOL, out_dir=out_dir).raise_for_status())
    stages.append(
        normalize(scenario, SIDE_COBOL, out_dir=out_dir).raise_for_status()
    )

    # STAGE 5. Both cycles must start from byte-for-byte the same seeded state.
    stages.append(reset(scenario).raise_for_status())

    # STAGE 6. Same treatment as stage 2: exit 5 and exit 8 are term codes.
    python_run = run_python(scenario, operation=operation, out_dir=out_dir)
    stages.append(python_run)

    # THE TWO SIDES MUST HAVE DRIVEN THE SAME WORK, IN THE SAME ORDER - asserted
    # from what each run stage RECORDED rather than from what this function asked for.
    # The one multi-operation scenario is driven as one Python invocation over its
    # declared list and as a series of oracle invocations over the same list, and the
    # two shapes are only comparable if the ordered set of operations they actually
    # reported is identical. When it is not - a runner that derived its own list from
    # the scalar `operation` key, a sequence that stopped early, a declared list read
    # in a different order - the two captures describe DIFFERENT WORK, and a diff
    # between them is meaningless whichever way it comes out. That is a HARNESS FAULT
    # and it is raised here, before stages 7 and 8 can turn it into a verdict.
    #
    # Only successful wrappers are compared: a non-zero wrapper status is already a
    # diagnosis of its own, and a run that stopped at the first contradicted status
    # legitimately reports fewer operations than it was given.
    if cobol_run.returncode == 0 and python_run.returncode == 0:
        cobol_ops = tuple(name for name, _ in cobol_run.operation_statuses)
        python_ops = tuple(name for name, _ in python_run.operation_statuses)
        if cobol_ops != python_ops:
            raise HarnessFaultError(
                f"{scenario}: THE TWO SIDES DID NOT DRIVE THE SAME OPERATIONS. The "
                f"oracle reported {cobol_ops!r} and the migrated cycle reported "
                f"{python_ops!r}; the scenario declares "
                f"{tuple(requested_operations)!r}. A comparison of two states "
                f"produced by different work measures nothing - and an EMPTY diff "
                f"from it is the most misleading outcome available, because it looks "
                f"exactly like parity. Both sides take the scenario's own ordered "
                f"`operations` list, with no reset between operations and one dump "
                f"per side.\n{cobol_run.describe()}\n{python_run.describe()}"
            )

    # STAGES 7 and 8.
    stages.append(dump(scenario, SIDE_PYTHON, out_dir=out_dir).raise_for_status())
    stages.append(
        normalize(scenario, SIDE_PYTHON, out_dir=out_dir).raise_for_status()
    )

    # STAGE 9. BOTH CAPTURES MUST DECLARE THEMSELVES COMPLETE before a single row is
    # compared, which the driver performs as an in-script check and this helper
    # performs in process (the composed protocol has the same ten stages
    # as the driven one, or a stage number here means something else than it does
    # there). It is recorded as its own stage so that a test can see it ran.
    stages.append(verify_published(scenario, out_dir=out_dir).raise_for_status())

    # STAGE 10. Exit 2 raises inside `diff`; exit 1 returns a non-empty TreeDiff.
    outcome = diff(scenario, out_dir=out_dir, max_differences=max_differences)
    stages.append(outcome.result)

    completed = ParityRun(
        scenario=scenario,
        tables=tables,
        stages=tuple(stages),
        cobol_run=cobol_run,
        python_run=python_run,
        outcome=outcome,
        paths=paths,
        run_id=run_id,
    )
    _PARITY_RUN_CACHE[cache_key] = completed
    return completed


# ---------------------------------------------------------------------------
#  THE THREE NON-VACUITY GUARDS, IN ONE PLACE
#
#  AN EMPTY DIFF IS THE PASS CONDITION ONLY WHEN A COMPARISON ACTUALLY HAPPENED
#  (rule R-6). Three conditions make an empty verdict worthless, and none of them is
#  visible in the verdict itself:
#
#  1. NOTHING WAS THERE TO COMPARE. Two dumps of zero rows are identical, so a seed
#  that never landed, a `system.file_system_used` of zero sending every handler
#  to the COBOL indexed-file path [copybooks/wssystem.cob:L112-L114], or a
#  loader returning 16 under the frozen `-gt 63` tolerance
#  [common/masterLD.sh:L56] all produce a clean, meaningless pass.
#  2. THE TWO SIDES STARTED FROM DIFFERENT STATE. Then the differences - or their
#  absence - belong to the seed and not to the cycles.
#  3. A RUN DID NOT REACH ITS DECLARED DISPOSITION. A runner that refused a
#  precondition, or aborted where the scenario expected success, leaves both
#  sides equally unwritten and the diff equally empty.
#
#  tests/determinism/test_two_runs_byte_identical.py already defends the first with
#  its layer 2 (`assert first.total_rows > 0`) and the second with its layer 4
#  (a byte comparison of the two fingerprints). The three helpers below are those
#  arguments, generalised so every scenario makes them from ONE definition instead of
#  each file re-deriving them - which is what Agent Action Plan section 0.4.3 asks of
#  this module: "no test reimplements the comparison protocol".
#
#  THEY BELONG IN A FIXTURE, NOT A TEST BODY. Every one of them fails for a reason
#  that means the question was never asked, so raised from a fixture they surface as
#  a pytest ERROR and stay separable from the FAILURE a real behavioural difference
#  produces.
# ---------------------------------------------------------------------------


def assert_parity_non_vacuous(
    run: ParityRun,
    *,
    tables_requiring_rows: Sequence[str] = (),
    tables_requiring_empty: Sequence[str] = (),
) -> None:
    """Assert a completed comparison actually compared something.

    FOUR CLAIMS, in the order a failure is most usefully reported:

      1. Every table the scenario bounds the comparison by was dumped ON BOTH SIDES.
         A table present in one tree and absent from the other has had nothing
         measured about it, which must never read as agreement.
      2. The comparison saw at least one row somewhere. Zero rows across every
         bounded table on both sides is the signature of a seed that never landed or
         of a run that never reached MySQL.
      3. Each table the caller names as seeded came back WITH ROWS on both sides.
      4. Each table the caller names as legitimately empty came back EMPTY on both
         sides - `empty_batch`'s `GLPOSTING-REC` is the case that exists, and it is
         why "non-empty" cannot simply be demanded of everything.

    NOTHING HERE JUDGES A VALUE. It counts rows and checks presence, so it can never
    substitute this module's opinion for the compiled oracle's (rule R-6), and it adds
    no validation the cycle does not have (rule R-3): the assertions are about the
    EVIDENCE, not about the accounting.

    Args:
        run: The completed `ParityRun`.
        tables_requiring_rows: Tables the scenario's seed fills, which must therefore
            come back with at least one row on each side.
        tables_requiring_empty: Tables that must be empty on both sides - either
            because the scenario seeds nothing into them or because the route
            legitimately empties them.

    Raises:
        AssertionError: A claim above does not hold, or a named table is not among
            the bounded tables at all - a typo there would silently assert nothing.
    """
    bounded = tuple(run.tables)
    by_table = {entry.table: entry for entry in run.tree.tables}

    for name, requested in (
        ("tables_requiring_rows", tables_requiring_rows),
        ("tables_requiring_empty", tables_requiring_empty),
    ):
        unknown = [table for table in requested if table not in bounded]
        assert not unknown, (
            f"{run.scenario}: {name} names {unknown!r}, which the scenario does not "
            f"bound the comparison by - it bounds it by {list(bounded)}. A table "
            f"named here but not compared would make this guard assert NOTHING, "
            f"which is precisely the false pass it exists to prevent."
        )

    overlap = sorted(set(tables_requiring_rows) & set(tables_requiring_empty))
    assert not overlap, (
        f"{run.scenario}: {overlap!r} is required both to hold rows and to be "
        f"empty. One of the two claims is wrong and neither can be checked."
    )

    missing = sorted(table for table in bounded if table not in by_table)
    assert not missing, (
        f"{run.scenario}: the completed comparison holds no entry for {missing!r} "
        f"although the scenario bounds it by {list(bounded)}. The bound and the "
        f"report disagree, so nothing was measured about those tables."
    )

    for table in bounded:
        entry = by_table[table]
        assert entry.in_cobol and entry.in_python, (
            f"{run.scenario}: {table} was dumped on only one side "
            f"(cobol={entry.in_cobol}, python={entry.in_python}). A MISSING DUMP IS "
            f"NOT AN EMPTY DIFF - the capture could not be taken for that side, so "
            f"the comparison for this table did not happen.\n{run.describe()}"
        )

    counts = {
        table: (
            int(by_table[table].cobol_row_count),
            int(by_table[table].python_row_count),
        )
        for table in bounded
    }
    total = sum(cobol + python for cobol, python in counts.values())
    assert total > 0, (
        f"{run.scenario}: EVERY BOUNDED TABLE CAME BACK EMPTY ON BOTH SIDES, so the "
        f"empty diff proves nothing. Row counts (cobol, python): {counts!r}.\n"
        f"  This is exactly what a seed that never landed, a run that never reached "
        f"MySQL, or `system.file_system_used: 0` "
        f"[copybooks/wssystem.cob:L112-L114] produces - and all three are silent in "
        f"the verdict. Check the seed fingerprints under {run.paths.run_logs} and "
        f"the two dumps under {run.paths.out_root} before reading any verdict.\n"
        f"{run.describe()}"
    )

    for table in tables_requiring_rows:
        cobol_rows, python_rows = counts[table]
        assert cobol_rows > 0 and python_rows > 0, (
            f"{run.scenario}: {table} is seeded by this scenario yet came back "
            f"EMPTY on at least one side (cobol={cobol_rows}, python={python_rows}). "
            f"AN EMPTY DIFF OVER AN EMPTY TABLE PROVES NOTHING. All bounded counts "
            f"(cobol, python): {counts!r}. Check the seed fingerprints under "
            f"{run.paths.run_logs}.\n{run.describe()}"
        )

    for table in tables_requiring_empty:
        cobol_rows, python_rows = counts[table]
        assert cobol_rows == 0 and python_rows == 0, (
            f"{run.scenario}: {table} must be EMPTY on both sides and holds "
            f"cobol={cobol_rows}, python={python_rows}. Either the seed carried rows "
            f"the scenario does not declare, or the route wrote a table it must not "
            f"touch.\n{run.describe()}"
        )


@dataclass(frozen=True)
class TableFingerprint:
    """One table's recorded state: how many rows, and a digest of every one of them.

    Attributes:
        table: The table name, as the scenario declared it.
        row_count: The row count, or None when the table could not be read.
        digest: The lower-case hex SHA-256 of the canonical dump
            `harness/dump_tables.py` writes for that table, or None when the table
            could not be read. `harness/dump_tables.py --table-digest` is the sole producer, and
            both sides invoke it, so two digests are comparable by construction.
    """

    table: str
    row_count: int | None
    digest: str | None

    @property
    def readable(self) -> bool:
        """Was the table readable when the record was taken?"""
        return self.row_count is not None and self.digest is not None


def read_fingerprint(path: Path | str) -> tuple[TableFingerprint, ...]:
    """Parse one fingerprint file into its per-table records.

    THE FORMAT IS A CONTRACT, because the two sides compare these files byte for
    byte: one `<TABLE>\\t<count>\\t<digest>` line per fingerprinted table - the
    scenario's bounded tables in its declared order, then `SYSTEM-REC` - with no
    header and no trailing blank line. A table that could not be read carries `-`
    in both value fields.

    THE PARSE IS STRUCTURAL ONLY. It reads the three fields and checks their shape;
    it draws no conclusion from a count or a digest, which is the caller's business
    (rule R-3).

    Args:
        path: The fingerprint file.

    Returns:
        One record per line, in file order.

    Raises:
        AssertionError: A line does not carry exactly three fields, or a value field
            is neither the unreadable marker nor a well-formed count/digest.
        OSError: The file could not be read.
    """
    target = Path(path)
    records: list[TableFingerprint] = []
    for number, line in enumerate(
        target.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        fields = line.split("\t")
        assert len(fields) == FINGERPRINT_FIELDS, (
            f"{target}:{number} carries {len(fields)} tab-separated field(s) where "
            f"the contract is {FINGERPRINT_FIELDS} - "
            f"`<TABLE>\\t<count>\\t<digest>`:\n"
            f"{_indent(line)}\n"
            f"  A two-field line is the SUPERSEDED counts-only form. A count alone "
            f"cannot tell two different seeds apart, so a record without its digest "
            f"establishes nothing about the starting state and must not be read as "
            f"though it did."
        )
        table, count_field, digest_field = (field.strip() for field in fields)
        if count_field == FINGERPRINT_UNREADABLE:
            assert digest_field == FINGERPRINT_UNREADABLE, (
                f"{target}:{number} marks {table!r} unreadable in its count field "
                f"but carries {digest_field!r} as its digest. A table that could not "
                f"be read has neither, and the two fields must agree about it."
            )
            records.append(TableFingerprint(table=table, row_count=None, digest=None))
            continue
        assert count_field.isdigit(), (
            f"{target}:{number} records {count_field!r} as {table!r}'s row count; a "
            f"count is a whole number of rows, or `{FINGERPRINT_UNREADABLE}` when "
            f"the table could not be read."
        )
        assert len(digest_field) == DIGEST_LENGTH and all(
            character in "0123456789abcdef" for character in digest_field
        ), (
            f"{target}:{number} records {digest_field!r} as {table!r}'s digest; a "
            f"digest is {DIGEST_LENGTH} lower-case hexadecimal characters - the "
            f"SHA-256 harness/dump_tables.py --table-digest takes over the canonical dump - or "
            f"`{FINGERPRINT_UNREADABLE}`."
        )
        records.append(
            TableFingerprint(
                table=table, row_count=int(count_field, 10), digest=digest_field
            )
        )
    return tuple(records)


@dataclass(frozen=True)
class SeedFingerprints:
    """The two sides' pre-run state fingerprints, and what they established.

    Attributes:
        python_path: `run-logs/<scenario>/python.seed-fingerprint`, which
            `harness/run_python_scenario.sh` writes at its stage 6a.
        cobol_path: The oracle-side counterpart, written by
            `harness/run_cobol_scenario.sh` immediately before it drives the menu.
        tables: The table names the fingerprint carried, in the order it carried
            them - which must be the scenario's declared order.
        records: The Python side's per-table records, digests included.
        cross_checked: True when both files were present and byte-identical. It can
            no longer be False on a returned value: the cross-check is required, and
            a missing counterpart fails instead of being reported as weaker.
    """

    python_path: Path
    cobol_path: Path
    tables: tuple[str, ...]
    records: tuple[TableFingerprint, ...]
    cross_checked: bool


def fingerprinted_tables(run: ParityRun) -> tuple[str, ...]:
    """The table order both runners write into their state records.

    The scenario's own bounded tables, in the scenario's declared order, then
    `SYSTEM-REC` when the scenario does not already bound it - which is the order
    `acas_resolve_fingerprint_tables` and `acas_py_resolve_fingerprint_tables` build,
    and it is appended rather than sorted in so that the declared order stays exactly
    as the scenario wrote it and the two sides' records stay byte-comparable.

    READ FROM THE SCENARIO, NOT FROM `run.tables`. Those are two different lists in
    this protocol and conflating them fails every scenario: `run.tables` is the
    22-table COMPARISON bound the capture and the diff cover, while the runners
    fingerprint the scenario's own `affected_tables` - the DECLARED effect - because
    that is the list whose seeded state the two sides cross-check.

    Args:
        run: The completed `ParityRun`, for its scenario name.

    Returns:
        The expected record order.
    """
    declared = scenario_affected_tables(run.scenario)
    if PARAMETER_TABLE in declared:
        return declared
    return (*declared, PARAMETER_TABLE)


def assert_seed_fingerprints_agree(
    run: ParityRun, *, require_cross_check: bool = True
) -> SeedFingerprints:
    """Assert BOTH sides recorded the same starting state, rows and values included.

    Each runner records, immediately before it dispatches, one
    `<TABLE>\\t<count>\\t<digest>` line per affected table IN THE SCENARIO'S DECLARED
    ORDER, and the Python runner refuses to proceed when the oracle-side record
    disagrees. This helper asserts everything those two records establish:

      * BOTH exist, and neither is empty. The oracle side is required, not optional:
        a comparison whose starting state was recorded on one side only has not had
        its starting state established at all, and every verdict taken from it - most
        dangerously an EMPTY one - is unattributable.
      * each carries exactly one line per FINGERPRINTED table, in that order - the
        scenario's declared tables, which include `SYSTEM-REC`, the parameter row the
        menu exit persists on every route, with that row appended after the declared
        order only on the fallback path where a scenario omits it - with all three
        fields well formed. The order is part of the contract because the
        two sides are compared byte for byte, so a reordering on one side alone would
        read as a starting-state disagreement.
      * EVERY BOUNDED TABLE CARRIES A DIGEST OVER EVERY ONE OF ITS ROWS. This is the
        claim a row count cannot make. Two seeds that differ in one balance, one
        status byte or one date have identical counts, and the diff that follows -
        or the empty diff that follows - belongs to the seed rather than to either
        cycle. The digest is taken by `harness/dump_tables.py --table-digest` over the canonical
        text `harness/dump_tables.py` writes, by the same program on both sides.
      * the two files are BYTE-IDENTICAL.

    THE COUNTS AND DIGESTS ARE NOT INTERPRETED (rule R-3). Whether a count is
    plausible is not this module's business; `assert_parity_non_vacuous` takes that
    corroboration from the dumps, and `assert_tables_unchanged_by_run` compares the
    pre-run record against the post-run one.

    Args:
        run: The completed `ParityRun`.
        require_cross_check: Kept in the signature, and defaulted to True, so that
            the requirement is visible at every call site rather than implied. Passing
            False asks for the Python-side record to be validated on its own, which is
            a strictly weaker claim and is never what a parity test wants; it exists
            for a caller diagnosing a half-completed run.

    Returns:
        What the two files established.

    Raises:
        AssertionError: Either record is absent, empty, of the wrong length, in the
            wrong order or missing a digest; or the two sides disagree.
    """
    run_logs = run.paths.run_logs
    python_path = run_logs / SEED_FINGERPRINT_PYTHON
    cobol_path = run_logs / SEED_FINGERPRINT_COBOL

    assert python_path.is_file(), (
        f"{run.scenario}: no seed fingerprint at {python_path}. "
        f"harness/run_python_scenario.sh records it at stage 6a and exits with a "
        f"precondition status if it cannot, so a completed run without one means THE "
        f"STARTING STATE OF THE COMPARISON WAS NEVER ESTABLISHED and no verdict from "
        f"it is attributable.\n{run.describe()}"
    )

    recorded = python_path.read_bytes()
    assert recorded, (
        f"{run.scenario}: the seed fingerprint at {python_path} is EMPTY. It carries "
        f"one line per affected table, so an empty file means no table was recorded."
    )

    expected_order = fingerprinted_tables(run)
    records = read_fingerprint(python_path)
    assert len(records) == len(expected_order), (
        f"{run.scenario}: the seed fingerprint at {python_path} carries "
        f"{len(records)} line(s) for {len(expected_order)} fingerprinted table(s) "
        f"{list(expected_order)}:\n"
        f"{_indent(recorded.decode('utf-8'))}\n"
        f"  One line per table is the contract - the scenario's bounded tables in "
        f"declared order, then {PARAMETER_TABLE}, the parameter row the menu exit "
        f"persists - and both sides compare these files byte for byte."
    )

    named: list[str] = []
    for record, table in zip(records, expected_order, strict=True):
        assert record.table == table, (
            f"{run.scenario}: the seed fingerprint at {python_path} names "
            f"{record.table!r} where the fingerprinted order has "
            f"{table!r} in that position:\n"
            f"{_indent(recorded.decode('utf-8'))}\n"
            f"  THE DECLARED ORDER IS PART OF THE CONTRACT: the two sides compare "
            f"these files byte for byte, so a reordering on one side alone would be "
            f"reported as a starting-state disagreement."
        )
        assert record.readable, (
            f"{run.scenario}: the seed fingerprint at {python_path} could not record "
            f"{table!r} at all - it carries the unreadable marker "
            f"{FINGERPRINT_UNREADABLE!r}. A fingerprinted table that cannot be read "
            f"before the run has had nothing established about its starting state, "
            f"and an empty diff over it would mean nothing."
        )
        named.append(record.table)

    if not require_cross_check:
        return SeedFingerprints(
            python_path=python_path,
            cobol_path=cobol_path,
            tables=tuple(named),
            records=records,
            cross_checked=False,
        )

    assert cobol_path.is_file() and cobol_path.stat().st_size > 0, (
        f"{run.scenario}: there is no oracle-side seed fingerprint at "
        f"{cobol_path}, so THE TWO STARTING STATES ARE UNVERIFIED and the comparison "
        f"cannot be attributed to either cycle. harness/run_cobol_scenario.sh writes "
        f"it immediately before it drives the compiled menu, in the same format and "
        f"the same declared order as the Python side's - "
        f"`<TABLE>\\t<count>\\t<digest>` per table - and both digests come from "
        f"harness/dump_tables.py --table-digest. An absent or empty file means the oracle run did "
        f"not reach the stage that records it, which is a HARNESS FAULT and never a "
        f"behavioural difference.\n{run.describe()}"
    )

    assert recorded == cobol_path.read_bytes(), (
        f"{run.scenario}: THE TWO SIDES DID NOT START FROM THE SAME SEEDED "
        f"STATE - a HARNESS FAULT and never a behavioural difference, and the "
        f"distinction matters because the two look identical in a table diff.\n"
        f"  python ({python_path}):\n"
        f"{_indent(recorded.decode('utf-8'))}\n"
        f"  cobol  ({cobol_path}):\n"
        f"{_indent(cobol_path.read_text(encoding='utf-8'))}\n"
        f"  A DIFFERING DIGEST WITH EQUAL COUNTS IS THE CASE THIS RECORD EXISTS FOR: "
        f"the same number of rows carrying different values. Nothing about either "
        f"cycle's behaviour has been measured - they were never given the same "
        f"starting state. Autocommit must be OFF while seeding "
        f"[common/glbatchLD.cbl:L9-L13]."
    )
    return SeedFingerprints(
        python_path=python_path,
        cobol_path=cobol_path,
        tables=tuple(named),
        records=records,
        cross_checked=True,
    )


def assert_system_record_parity(run: ParityRun) -> tuple[TableFingerprint, TableFingerprint]:
    """Assert the two cycles left `SYSTEM-REC` in the SAME state after their runs.

    THIS IS THE SECOND OF TWO BOUNDS ON THE PARAMETER ROW, and it is the one the table
    diff cannot make on its own. `overrewrite` rewrites key 1 on all four subsystems and
    the migrated command line reproduces it, so both cycles write the row on every route;
    the IRS route additionally copies its advanced posting allocator into it before
    persisting. A regression in any of that once produced an EMPTY diff, because the
    table was outside every bound.

    The FIRST bound is the dump: `SYSTEM-REC` is one of the 22 in-scope tables and is on
    every scenario's declared list, so 167 of its 169 columns are compared by value. The
    two it does not compare by value are credentials - `harness/dump_tables.py`'s
    `REDACTED_COLUMNS` withholds `RDBMS-PASSWD` and `PASS-WORD` inside `render_value`,
    identically on both sides, because a dump is `SELECT *` and a capture is committed
    evidence.

    THIS is the second bound, and it reaches the two the dump withholds: comparing the two
    sides' post-run digests covers all 169 columns, credentials included, and leaks
    nothing, because a sha256 of the canonical dump is not the dump. The credential
    columns are filled from the environment by the builder and are identical for both
    sides of one run, so they cannot manufacture a difference; anything that does differ
    is a difference in what the two cycles wrote.

    Args:
        run: The completed `ParityRun`.

    Returns:
        The oracle-side and Python-side post-run records for the parameter row, in
        that order, so a caller can state what it observed.

    Raises:
        AssertionError: A record is missing or unreadable, or the two sides disagree.
    """
    run_logs = run.paths.run_logs
    sides: dict[str, TableFingerprint] = {}
    for side, name in (
        (SIDE_COBOL, POST_FINGERPRINT_COBOL),
        (SIDE_PYTHON, POST_FINGERPRINT_PYTHON),
    ):
        path = run_logs / name
        assert path.is_file() and path.stat().st_size > 0, (
            f"{run.scenario}: the {side} side wrote no post-run state record at "
            f"{path}. Both runners write one immediately after their dispatch, so an "
            f"absent record means the run did not reach that stage - a HARNESS FAULT. "
            f"Without it the parameter row keeps only the bound the dump gives it, and "
            f"the two withheld credential cells are compared by nothing at all.\n"
            f"{run.describe()}"
        )
        found = {record.table: record for record in read_fingerprint(path)}
        record = found.get(PARAMETER_TABLE)
        assert record is not None, (
            f"{run.scenario}: {PARAMETER_TABLE} is absent from the {side} side's "
            f"post-run record at {path}. Both runners record it on every scenario, "
            f"whether the scenario declares it or not, precisely because the digest is "
            f"the only thing that compares its two withheld credential cells."
        )
        assert record.readable, (
            f"{run.scenario}: {PARAMETER_TABLE} could not be read on the {side} side "
            f"after its run, so nothing has been established about the parameter row "
            f"the menu exit persists."
        )
        sides[side] = record

    cobol_record, python_record = sides[SIDE_COBOL], sides[SIDE_PYTHON]
    assert (cobol_record.row_count, cobol_record.digest) == (
        python_record.row_count,
        python_record.digest,
    ), (
        f"{run.scenario}: THE TWO CYCLES LEFT {PARAMETER_TABLE} IN DIFFERENT STATES.\n"
        f"  cobol : {cobol_record.row_count} row(s), digest {cobol_record.digest}\n"
        f"  python: {python_record.row_count} row(s), digest {python_record.digest}\n"
        f"  Both sides persist key 1 on this route - `overrewrite` in the menu shell "
        f"and the paragraph the command line reproduces - so this is a BEHAVIOURAL "
        f"DIFFERENCE in what they wrote, not a harness artefact. The likeliest "
        f"causes are the key order (1, then 2, then 4 - the reverse of the load's), "
        f"the close issued against key 4 rather than key 1, the write-back into "
        f"`Date-Form` the frozen date sections perform, and on the IRS route the "
        f"advanced posting allocator. The digest covers all 169 columns, so the "
        f"difference is somewhere in the row; dump the table by hand to locate it - "
        f"the capture deliberately does not carry it, because the row holds a "
        f"credential.\n{run.describe()}"
    )
    return cobol_record, python_record


def assert_tables_unchanged_by_run(
    run: ParityRun,
    *,
    unchanged: Sequence[str] = (),
    changed: Sequence[str] = (),
) -> None:
    """Compare each side's PRE-run record against its POST-run record, per table.

    THE QUESTION THIS ANSWERS IS "DID THE RUN DO ANYTHING?", and no table diff can
    answer it. A diff compares the two SIDES to each other; two runs that did nothing
    at all agree perfectly. So each runner records the same canonical digest again
    immediately after its dispatch, and the two records together say, per table,
    whether that table's rows changed - on each side independently.

    Both sides are asserted, and separately, because a claim that holds on one side
    only is not the claim: "byte-identical to the seed" and "this run mutated
    something" are properties of a CYCLE, and there are two cycles.

    Args:
        run: The completed `ParityRun`.
        unchanged: Tables whose rows must be identical before and after the run, on
            both sides. Use it for the read-only tables of a route: the claim is that
            the run did not touch them, which is stronger and more useful than the
            claim that the two sides agree about them.
        changed: Tables at least one of which must differ before and after the run,
            on both sides - a MUTATION WITNESS. Passing several names asserts that at
            least one of them changed, which is what a route with several possible
            landing places needs; passing one asserts that one changed.

    Raises:
        AssertionError: A record is missing, unreadable, or contradicts the claim.
        OSError: A fingerprint file could not be read.
    """
    if not unchanged and not changed:
        raise ValueError(
            "assert_tables_unchanged_by_run needs at least one table to assert "
            "about; a call that claims nothing would read as evidence."
        )

    run_logs = run.paths.run_logs
    for side, before_name, after_name in (
        (SIDE_COBOL, SEED_FINGERPRINT_COBOL, POST_FINGERPRINT_COBOL),
        (SIDE_PYTHON, SEED_FINGERPRINT_PYTHON, POST_FINGERPRINT_PYTHON),
    ):
        before_path = run_logs / before_name
        after_path = run_logs / after_name
        for path in (before_path, after_path):
            assert path.is_file() and path.stat().st_size > 0, (
                f"{run.scenario}: the {side} side has no state record at {path}. "
                f"Both runners write one immediately before their dispatch and one "
                f"immediately after it, so an absent record means the run did not "
                f"reach the stage that writes it - a HARNESS FAULT. Without both, "
                f"whether the run changed anything cannot be established at all.\n"
                f"{run.describe()}"
            )

        before = {record.table: record for record in read_fingerprint(before_path)}
        after = {record.table: record for record in read_fingerprint(after_path)}

        for table in unchanged:
            first, second = before.get(table), after.get(table)
            assert first is not None and second is not None, (
                f"{run.scenario}: {table} is absent from the {side} side's "
                f"{'pre' if first is None else 'post'}-run record, so nothing about "
                f"whether this run changed it has been established.\n"
                f"  WHAT THE RECORD COVERS, which is what a caller must pass: the "
                f"scenario's own declared `affected_tables` plus the menu-persisted "
                f"parameter row, and nothing else. Both runners fingerprint exactly "
                f"that set.\n"
                f"  IT IS NOT `run.tables`. That is the 22-table COMPARISON bound, "
                f"which is asserted side-to-side by the diff; asking the pre/post "
                f"record about a table it never fingerprinted reports this missing "
                f"record rather than an unchanged table. Pass "
                f"`scenario_definition(scenario)['affected_tables']`, as "
                f"tests/scenarios/test_empty_batch.py and "
                f"test_mixed_accepted_rejected_batch.py do.\n"
                f"  record: {before_path if first is None else after_path}"
            )
            assert first.readable and second.readable, (
                f"{run.scenario}: {table} could not be read on the {side} side "
                f"either before or after the run, so nothing about it has been "
                f"established."
            )
            assert (first.row_count, first.digest) == (
                second.row_count,
                second.digest,
            ), (
                f"{run.scenario}: {table} CHANGED on the {side} side, and this "
                f"route must not touch it.\n"
                f"  before: {first.row_count} row(s), digest {first.digest}\n"
                f"  after:  {second.row_count} row(s), digest {second.digest}\n"
                f"  The digest covers every row at its declared scale, so this is a "
                f"real change of stored values and not a representation artefact. A "
                f"row count that did not move does not exonerate the table: an "
                f"in-place rewrite leaves the count alone.\n{run.describe()}"
            )

        if changed:
            witnesses = []
            for table in changed:
                first, second = before.get(table), after.get(table)
                assert first is not None and second is not None, (
                    f"{run.scenario}: {table} is absent from the {side} side's "
                    f"{'pre' if first is None else 'post'}-run record, so it cannot "
                    f"witness that the run did anything."
                )
                assert first.readable and second.readable, (
                    f"{run.scenario}: {table} could not be read on the {side} side, "
                    f"so it cannot witness that the run did anything."
                )
                if (first.row_count, first.digest) != (
                    second.row_count,
                    second.digest,
                ):
                    witnesses.append(table)
            assert witnesses, (
                f"{run.scenario}: THE {side.upper()} RUN CHANGED NOTHING. None of "
                f"{list(changed)} differs between the pre-run and post-run records, "
                f"so the run was a no-op over every table that was supposed to move. "
                f"TWO NO-OPS ARE BYTE-IDENTICAL AND SO ARE THEIR DUMPS: without this "
                f"witness an empty diff, or two byte-identical determinism runs, "
                f"would prove only that neither side did anything. The likeliest "
                f"causes are a seed that never landed, a route that returned through "
                f"a gate, or `system.file_system_used` not selecting the RDB path "
                f"[copybooks/wssystem.cob:L111-L114].\n"
                f"  pre-run record:  {before_path}\n"
                f"  post-run record: {after_path}\n{run.describe()}"
            )


def expected_exit_status(declared: Sequence[int] | int | None) -> int:
    """The aggregate behavioural status declared per operation.

    A scenario declares `expected_status` PER OPERATION. For concise diagnostics this
    helper reduces the ordered list to its first non-zero value, or zero when every
    operation succeeds. The harness wrapper's own process status is not involved:
    wrappers exit zero after verifying an expected non-zero child term code.

    Only two non-zero statuses exist anywhere in the in-scope set: 5, from
    [general/gl070.cbl:L289] via the gate at [general/general.cbl:L810-L811], and 8,
    from [sales/sl055.cbl:L344] and [purchase/pl055.cbl:L286].

    Args:
        declared: The scenario's `expected_status` - a list, a bare integer, or None
            when the scenario declares none.

    Returns:
        The implied process exit status; 0 when nothing non-zero is declared.

    Raises:
        ValueError: A declared entry is not an integer.
    """
    if declared is None:
        return 0
    values = [declared] if isinstance(declared, int) else list(declared)
    for value in values:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(
                f"a declared expected_status entry must be an integer; got "
                f"{value!r}. The vocabulary is 0, 5 and 8 and nothing else."
            )
        if value != 0:
            return value
    return 0


def observed_exit_status(result: StageResult, operations: Sequence[str]) -> int:
    """Reduce a run stage's recorded operation statuses in declared order.

    This is the observed counterpart of :func:`expected_exit_status`. It never reads
    the wrapper process status: `StageResult.returncode` describes harness health,
    while `operation_statuses` carries the behavioural data whose database effect is
    still dumped under Agent Action Plan section 0.6.5.
    """
    for operation in operations:
        status = result.operation_status(operation)
        if status != 0:
            return status
    return 0


def assert_operations_driven(
    run: ParityRun,
    *,
    operations: Sequence[str],
) -> None:
    """Assert BOTH sides drove exactly these operations, in exactly this order.

    THE TWO-SIDED CLAIM, ASSERTED WHERE A READER LOOKS FOR IT. The
    protocol compares one COBOL run against one Python run, and that comparison means
    nothing unless the two runs drove THE SAME ORDERED LIST. One scenario -
    `period_end_totals` - declares four operations spanning two menu executables, so
    driving the oracle side one operation at a time while the Python side runs all four
    would diff a one-operation state against a four-operation state, and the verdict would
    be meaningless in either direction.

    Both runners resolve the ordered list from the scenario itself and publish one
    status row per operation, in order, so the claim is CHECKABLE - and this asserts it
    rather than leaving it to be implied by `StageResult.operation_status` raising deep
    inside another helper.

    THE ORDER IS PART OF THE CLAIM, not decoration: `period_end_totals`' operation 3
    sets flags operation 4 reads [purchase/pl060.cbl:L373-L375], and there is exactly
    one dump per side, so the dump attributes the CUMULATIVE effect of the sequence.

    Args:
        run: The completed `ParityRun`.
        operations: The operations the scenario declares, in declared order.

    Raises:
        AssertionError: Either side recorded a different set, a different order, or a
            different count.
        ValueError: An operation is not one of the seven.
    """
    expected = tuple(operations)
    for operation in expected:
        assert_operation(operation)

    for side, stage in (
        (SIDE_COBOL, run.cobol_run),
        (SIDE_PYTHON, run.python_run),
    ):
        recorded = tuple(name for name, _status in stage.operation_statuses)
        assert recorded == expected, (
            f"{run.scenario}: the {side} run recorded operation statuses for "
            f"{list(recorded)} where the scenario declares {list(expected)}. THE TWO "
            f"SIDES MUST DRIVE THE SAME ORDERED LIST or the comparison is between two "
            f"different amounts of work and its verdict means nothing in either "
            f"direction - an empty diff most of all. A short list means the runner "
            f"drove fewer operations than the scenario declares; a reordered one means "
            f"a later operation ran before the state it reads was written.\n"
            f"{stage.describe()}"
        )


def assert_declared_run_statuses(
    run: ParityRun,
    *,
    operations: Sequence[str],
    declared: Sequence[int] | int | None,
    reference_only: bool = False,
) -> tuple[str, str]:
    """Assert the run stages reached the disposition the scenario declared.

    THE THIRD WAY AN EMPTY DIFF MEANS NOTHING. A runner that refused a precondition,
    or aborted where the scenario expected success, leaves both sides equally
    unwritten - and the diff equally empty. So the two ACTUAL statuses are read, not
    the YAML's declaration compared with a local restatement of itself.

    BOTH SIDES ARE ALSO CLASSIFIED, because the three dispositions must stay distinct:
    a reproduced abort is a BEHAVIOURAL result whose database effect is still
    evidence, whereas a runner handed a bad command line - `argparse` exit 2 - or one
    reporting its own precondition band leaves no evidence at all. A harness fault
    here is refused outright rather than being read as agreement.

    WHICH SIDES THE STATUS EQUALITY COVERS IS A DELIBERATE CHOICE, and it decides
    whether a wrong status is reported as an ERROR or as a FAILURE. Called from a
    FIXTURE with `reference_only=True`, this asserts only that THE ORACLE reached the
    declared disposition - the scenario was set up as declared and there is something
    to compare - and leaves "the Python side reproduced it" to a test BODY, where a
    divergence is a behavioural FAILURE attributable to the migrated code rather than
    a setup error attributable to the environment. Called with the default, it covers
    both sides, which is right only where no body owns the behavioural claim.

    Args:
        run: The completed `ParityRun`.
        operations: The operations the run drove, in order. Each is classified, which
            is what makes a status admissible for one operation and a fault for
            another.
        declared: The scenario's `expected_status`.
        reference_only: Restrict the status equality to the oracle side. The
            harness-fault refusal always covers BOTH sides regardless, because a
            runner that never ran is an environment fault on either side.

    Returns:
        The two dispositions, `(cobol, python)`.

    Raises:
        AssertionError: An in-scope actual status differs from the declared one, or
            either side classified as a harness fault.
        ValueError: An operation is not one of the seven.
    """
    for operation in operations:
        assert_operation(operation)

    dispositions: list[str] = []
    for side, stage in (
        (SIDE_COBOL, run.cobol_run),
        (SIDE_PYTHON, run.python_run),
    ):
        seen = {
            classify_run(stage, operation=operation) for operation in operations
        }
        assert DISPOSITION_HARNESS_FAULT not in seen, (
            f"{run.scenario}: the {side} run stage classified as a HARNESS FAULT "
            f"rather than a disposition of the cycle. `argparse` exit "
            f"{ARGPARSE_USAGE_EXIT} means the command line was wrong; a code in a "
            f"runner's own band means the script diagnosed itself. Either way the "
            f"question was never asked and no verdict from this run is "
            f"attributable.\n{stage.describe()}"
        )
        # One disposition per side. A single status can classify differently across
        # operations ONLY by being a term code for one and not for another - and "not
        # for another" is exactly `DISPOSITION_HARNESS_FAULT`, which the assertion
        # above has just refused. So the set is a singleton here whatever
        # `reference_only` was, and this does not depend on the status equality.
        assert len(seen) == 1, (
            f"{run.scenario}: the {side} run stage's status "
            f"{stage.returncode} classifies as {sorted(seen)} across operations "
            f"{list(operations)}. A single status must reach ONE disposition for a "
            f"run to have a disposition at all.\n{stage.describe()}"
        )
        dispositions.append(sorted(seen)[0])

    expected = expected_exit_status(declared)
    checked_stages: tuple[tuple[str, StageResult], ...] = (
        ((SIDE_COBOL, run.cobol_run),)
        if reference_only
        else (
            (SIDE_COBOL, run.cobol_run),
            (SIDE_PYTHON, run.python_run),
        )
    )
    for side, stage in checked_stages:
        observed = observed_exit_status(stage, operations)
        assert observed == expected, (
            f"{run.scenario}: the {side} run observed operation status {observed} "
            f"where the scenario declares {declared!r}, whose aggregate status is "
            f"{expected}. The harness wrapper itself exited {stage.returncode}.\n"
            f"  A behavioural status that is not the declared one means the run did "
            f"not reach the disposition this comparison is about, so both sides may "
            f"be equally unwritten and the diff equally empty. Operations driven: "
            f"{list(operations)}.\n{run.describe()}"
        )

    return (dispositions[0], dispositions[1])


def assert_python_reproduced_disposition(
    run: ParityRun,
    *,
    operations: Sequence[str],
    declared: Sequence[int] | int | None,
) -> str:
    """Assert the migrated cycle reached the SAME disposition the oracle reached.

    THE BEHAVIOURAL HALF of the status question, and it belongs in a test BODY. The
    oracle's status is the specification (rule R-6): whatever it exited with is
    correct by definition, so a Python side that exits differently is a behavioural
    divergence of the migrated code and must be reported as a FAILURE. Asserting it
    during setup instead would report a real regression in the posting cycle as an
    ERROR, making it indistinguishable from a broken environment - which is the exact
    confusion the fixture/body split exists to prevent.

    The declared status is passed in rather than read here so that the caller states
    what it expects, and it is checked against the oracle too: agreement between the
    two sides is necessary but not sufficient, since two sides that both failed to
    abort would agree perfectly and prove nothing.

    Args:
        run: The completed `ParityRun`.
        operations: The operations the run drove, in order.
        declared: The scenario's `expected_status`, as the caller understands it.

    Returns:
        The disposition both sides reached.

    Raises:
        AssertionError: The two sides' statuses differ, or agree on something other
            than the declared status.
        ValueError: An operation is not one of the seven.
    """
    for operation in operations:
        assert_operation(operation)

    expected = expected_exit_status(declared)
    cobol_code = observed_exit_status(run.cobol_run, operations)
    python_code = observed_exit_status(run.python_run, operations)

    assert python_code == cobol_code, (
        f"{run.scenario}: BEHAVIOURAL DIVERGENCE - the compiled oracle observed "
        f"status {cobol_code} and the migrated Python cycle observed {python_code} for "
        f"operations {list(operations)}.\n"
        f"  The oracle's disposition is the specification (rule R-6), so this is a "
        f"difference in the migrated code, not in the environment. Reproduce the "
        f"oracle's status - do not adjust the scenario's declaration to match the "
        f"Python side.\n{run.describe()}"
    )
    assert cobol_code == expected, (
        f"{run.scenario}: both sides observed {cobol_code}, agreeing with each other "
        f"but not with the declared {declared!r} (implied status {expected}). Two "
        f"sides that equally failed to reach this scenario's disposition agree "
        f"perfectly and prove nothing.\n{run.describe()}"
    )

    disposition = classify_run(run.python_run, operation=operations[0])
    return disposition


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

    Composed from the individual stages - RESET-AND-SEED, run, dump, normalize, then
    RESET-AND-SEED, run, dump, normalize, compare - WITHOUT the COBOL side, which is
    the composition tests/determinism/ needs. The reset is what makes the two runs
    comparable, and it happens before BOTH of them by the same command; see the loop
    below. Both runs use the same scenario, so both receive the same pinned run date
    through linkage; that pin is returned so a test can assert it rather than assume
    it.

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

    #  As the parity driver: two runs of one scenario are compared over ALL 22
    #  in-scope tables, so a determinism claim covers everything the cycle can
    #  persist rather than only the tables the scenario expected to move.
    tables = in_scope_tables()
    definition = scenario_definition(scenario)

    # The scenario's own declared run date, so the pin returned is the pin the runs
    # actually used. `pinned_clock_from` does not validate the text - `maps04` alone
    # judges it - and a rejected date arrives as run_date 0 (anomaly A-16).
    declared_text = definition.get(SCENARIO_KEY_RUN_DATE_TEXT)
    pin = pinned_clock_from(
        PINNED_RUN_DATE_TEXT if declared_text is None else str(declared_text)
    )

    root = output_root() if out_dir is None else Path(out_dir).resolve()
    first_root = root / DETERMINISM_SUBDIR / DETERMINISM_LABELS[0]
    second_root = root / DETERMINISM_SUBDIR / DETERMINISM_LABELS[1]

    stages: list[StageResult] = []
    runs: list[StageResult] = []
    for side_root in (first_root, second_root):
        # THE SAME COMMAND BEFORE BOTH LEGS, AND BEFORE THE FIRST.
        # This used to `seed` the first leg and `reset` the second, and the two are NOT
        # the same starting state: a bare seed leaves behind whatever the previously
        # executed scenario wrote and relies on duplicate-key rewrites, while a reset
        # re-applies the frozen schema verbatim first. So leg one could begin from rows
        # leg two never saw, and a difference between the legs would then belong to the
        # seeding and not to the cycle - in a helper whose entire purpose is to prove
        # the cycle is deterministic. Worse, the two legs could AGREE because a
        # duplicate-key rewrite happened to converge. Both legs now reset and re-seed
        # from the one built fixture, which is also exactly what stages 1 and 5 of the
        # parity protocol do, and `prepare_scenario` is `reset_db.sh` under the stage-1
        # name - the identical command `reset` issues - so the two starting states are
        # produced by one code path rather than two.
        #
        # THIS IS THE ISOLATION, AND IT IS WHY NO FINAL CLEANUP FOLLOWS. Every run of
        # this helper and of `run_scenario_parity` begins by dropping the schema,
        # re-applying `mysql/ACASDB.sql` verbatim and re-seeding the scenario's own
        # fixture, so nothing a previous run left can reach a later one. A trailing
        # teardown would delete the very artifacts an operator reads after a failure
        # and would still not be a substitute for resetting at the start (rule R-3
        # keeps this sequential, so there is no concurrent writer to guard against).
        stages.append(reset(scenario).raise_for_status())

        # EVERY ARTIFACT OF THIS LEG LIVES IN THIS LEG'S ROOT. The
        # dump and the normalisation were already per-leg, but the RUN published its
        # transcript, its run-status record and its per-operation statuses into the
        # canonical run-logs root - so leg two overwrote leg one's attestation, and the
        # dump of leg one was attested by the run of leg two. Passing the leg's own
        # root keeps the attestation with the capture it belongs to.
        run = run_python(scenario, operation=operation, out_dir=side_root)
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

    # NEITHER LEG MAY BE UNATTESTED. `diff_trees_directly` compares
    # two directories and asks nothing of them, which is right for its own purpose and
    # wrong here: two captures taken after runs that never happened are trivially
    # equal, and equality is what this helper reports as determinism. So each leg's
    # published manifest is required to exist and to ATTEST its run before the
    # comparison, using the comparison tool's own reader rather than a check invented
    # here. The manifests also carry the seed identity, which must be the same digest
    # on both legs - the whole claim is that one seeded state produced two identical
    # results.
    diff_states = harness_diff_states()
    leg_manifests: list[Mapping[str, Any]] = []
    for label, tree_dir in (
        (DETERMINISM_LABELS[0], first_normalized),
        (DETERMINISM_LABELS[1], second_normalized),
    ):
        try:
            manifest = diff_states.read_manifest(tree_dir)
        except Exception as exc:  # noqa: BLE001 - any read failure is a fault
            raise HarnessFaultError(
                f"{scenario}: the {label} leg's normalised capture {tree_dir} could "
                f"not be read for its completeness manifest: {exc}."
            ) from exc
        if manifest is None:
            raise HarnessFaultError(
                f"{scenario}: the {label} leg's normalised capture {tree_dir} carries "
                f"no manifest, so it does not declare itself complete. Two partial "
                f"captures can be identical over the tables they both hold, and this "
                f"helper reports identity as determinism - so it is refused (R-6)."
            )
        attestation = manifest.get("attestation")
        if not isinstance(attestation, Mapping) or attestation.get("attested") is not True:
            detail = (
                attestation.get("detail")
                if isinstance(attestation, Mapping)
                else "no attestation block"
            )
            raise HarnessFaultError(
                f"{scenario}: the {label} leg does not attest a successful run, so "
                f"there is nothing to claim determinism about: "
                f"{detail or 'no reason recorded'}."
            )
        leg_manifests.append(manifest)

    first_seed = leg_manifests[0]["attestation"].get("seed_marker_sha256")
    second_seed = leg_manifests[1]["attestation"].get("seed_marker_sha256")
    if first_seed != second_seed:
        raise HarnessFaultError(
            f"{scenario}: the two determinism legs were seeded from DIFFERENT "
            f"fixtures ({first_seed!r} and {second_seed!r}). Determinism is the claim "
            f"that ONE seeded state produces two identical results, so two different "
            f"seeded states make the comparison meaningless whatever it reports."
        )

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
class Vocabulary:
    """The shared vocabulary and the PURE helpers, with no stack requirement.

    THE OTHER HALF OF "conftest IS REACHED THROUGH FIXTURES". `Protocol` gathers the
    stages, every one of which needs the Compose stack; this gathers what a test can
    legitimately ask for on a bare host - the operation names both runners share, the
    term codes, the three dispositions, the scenario keys, the pinned pair - together
    with the helpers that only read files. Without it a stack-free precondition test
    would have to import this module to reach a constant, which is exactly the
    import-mode fragility the house convention exists to avoid.

    Frozen and derived: every field below is the SAME object the stages themselves
    use, so there is one definition of each and no second authority to drift.

    Attributes:
        scenarios: The scenario names, in `SCENARIOS` order.
        operations: The seven operations both runners accept, each mapping to
            `(subsystem, menu key, menu paragraph, locator)`.
        term_codes: The admissible term codes per operation - only 5 and 8 exist.
        disposition_success: `classify_run`'s verdict for a clean run.
        disposition_behavioural: Its verdict for a reproduced abort.
        disposition_harness_fault: Its verdict for a status nobody may conclude from.
        argparse_usage_exit: 2 - a bad command line, always a harness fault.
        sides: `("cobol", "python")`, in the order the report labels them.
        scenario_keys: The scenario keys the stages read, by name.
        irs_instead_states: The three states of the fan-out switch
            [copybooks/wssystem.cob:L179-L181].
        date_forms: `(UK, USA, International)` as `SYSTEM-REC.DATE-FORM` numbers.
        autogen_tables: The four automatic-generation tables both runners assert
            remain empty.
        parameter_table: `SYSTEM-REC`, the ONE in-scope table BOTH cycles write on
            EVERY route (`args.overrewrite` rewrites key 1 unconditionally) and
            which NO scenario names in `affected_tables`, because a dump is
            `SELECT *` and the record carries `RDBMS-PASSWD char(12)`. It is
            bounded by FINGERPRINT instead - see `assert_system_record_parity`.
            Published on this STACK-FREE bundle as well as on `Protocol` because
            the test that asserts the bounding list's shape takes no stack.
        pinned_run_date_text: The pinned `to-day`, DD/MM/CCYY.
        pinned_run_date_binary: The same date as `Run-Date binary-long`.
        fault: `HarnessFaultError`, so a test can name the class it expects.
        scenario_file: One scenario's definition PATH, for the rare test that
            must build a harness command line itself instead of going through a
            stage helper - a refusal, whose exit 2 the helper maps to a fault.
        affected_tables: One scenario's bounding list, in declared order.
        definition: One scenario's parsed YAML.
        paths: The canonical artifact layout for one scenario.
        read_dump: One dump object, parsed.
        assert_dump_wellformed: The structural contract, asserted.
        diff_trees_directly: A `TreeDiff` between two normalised trees on disk.
        expected_exit_status: The process status a declared list implies.
        classify_run: A run stage's disposition. Pure - it reads a captured result.
        assert_wrapper_completed: A run stage's WRAPPER health, asserted with the
            diagnosis its status earns - 69 reads as a behavioural difference and not
            as a broken rig.
        normalize: STAGE 4, which is a FILE-TO-FILE transformation driven in process
            and needs no database, no COBOL and no Docker. It is published here as
            well as on `Protocol` for exactly one purpose: a test that publishes
            synthetic trees to a `tmp_path` and exercises the three-way exit contract
            end to end must be able to do so ON A BARE HOST.
        assert_diff_exit_contract: STAGE 10's THREE-WAY exit contract, exercised
            against the SHIPPED comparison on synthetic trees the caller publishes
            into its own `tmp_path`. Stack-free, and the ONE definition of the
            contract: four scenario files used to assert it against module constants
            and hand-built dataclasses, which passes whatever the comparison does.
        diff: STAGE 10, in process over two normalised trees on disk, and stack-free
            for the same reason. Its exit-2 mapping to `HarnessFaultError` is part of
            what such a test asserts.
    """

    scenarios: tuple[str, ...]
    operations: Mapping[str, tuple[str, str, str, str]]
    term_codes: Mapping[str, tuple[int, ...]]
    disposition_success: str
    disposition_behavioural: str
    disposition_harness_fault: str
    argparse_usage_exit: int
    sides: tuple[str, str]
    scenario_keys: Mapping[str, Any]
    irs_instead_states: tuple[str, str, str]
    date_forms: tuple[int, int, int]
    autogen_tables: tuple[str, ...]
    parameter_table: str
    pinned_run_date_text: str
    pinned_run_date_binary: int
    fault: type[HarnessFaultError]
    scenario_file: Callable[[str], Path]
    affected_tables: Callable[[str], tuple[str, ...]]
    definition: Callable[[str], Mapping[str, Any]]
    paths: Callable[..., ScenarioPaths]
    read_dump: Callable[..., dict[str, Any]]
    assert_dump_wellformed: Callable[..., None]
    diff_trees_directly: Callable[..., Any]
    expected_exit_status: Callable[..., int]
    classify_run: Callable[..., str]
    assert_wrapper_completed: Callable[..., None]
    normalize: Callable[..., StageResult]
    diff: Callable[..., DiffOutcome]
    assert_diff_exit_contract: Callable[..., None]


def build_vocabulary() -> Vocabulary:
    """Assemble the stack-free vocabulary bundle.

    Returns:
        The bundle, every field pointing at this module's single definition of it.
    """
    return Vocabulary(
        scenarios=SCENARIOS,
        operations=OPERATIONS,
        term_codes=TERM_CODES,
        disposition_success=DISPOSITION_SUCCESS,
        disposition_behavioural=DISPOSITION_BEHAVIOURAL,
        disposition_harness_fault=DISPOSITION_HARNESS_FAULT,
        argparse_usage_exit=ARGPARSE_USAGE_EXIT,
        sides=(SIDE_COBOL, SIDE_PYTHON),
        scenario_keys={
            "run_date_text": SCENARIO_KEY_RUN_DATE_TEXT,
            "run_date_binary": SCENARIO_KEY_RUN_DATE_BINARY,
            "date_form": SCENARIO_KEY_DATE_FORM,
            "irs_instead": SCENARIO_KEY_IRS_INSTEAD,
            "operation": SCENARIO_KEY_OPERATION,
            "subsystem": SCENARIO_KEY_SUBSYSTEM,
            "seed_files": SCENARIO_KEY_SEED_FILES,
            "irs_clear_postings": SCENARIO_KEY_IRS_CLEAR_POSTINGS,
            "affected_tables": SCENARIO_KEY_AFFECTED_TABLES,
        },
        irs_instead_states=IRS_INSTEAD_STATES,
        date_forms=(DATE_FORM_UK, DATE_FORM_USA, DATE_FORM_INTL),
        autogen_tables=AUTOGEN_TABLES,
        parameter_table=PARAMETER_TABLE,
        pinned_run_date_text=PINNED_RUN_DATE_TEXT,
        pinned_run_date_binary=PINNED_RUN_DATE_BINARY,
        fault=HarnessFaultError,
        scenario_file=scenario_file,
        affected_tables=scenario_affected_tables,
        definition=scenario_definition,
        paths=scenario_paths,
        read_dump=read_dump,
        assert_dump_wellformed=assert_dump_wellformed,
        diff_trees_directly=diff_trees_directly,
        expected_exit_status=expected_exit_status,
        classify_run=classify_run,
        assert_wrapper_completed=assert_wrapper_completed,
        normalize=normalize,
        diff=diff,
        assert_diff_exit_contract=assert_diff_exit_contract,
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
        diff: Stage 10; its `DiffOutcome.is_empty` is the pass condition.
        run_scenario_parity: All eight, in order.
        run_determinism_pair: Two Python runs, compared.
        classify_run: Success, behavioural difference or harness fault.
        assert_wrapper_completed: A run stage's wrapper health, asserted from a
            test BODY so that an `EX_BEHAVIOUR` wrapper reads as a behavioural
            FAILURE rather than as a broken rig.
        paths: The canonical layout for one scenario.
        affected_tables: The list a comparison is bounded by.
        definition: One scenario's parsed YAML.
        in_scope_tables: THE CANONICAL COMPARISON BOUND - all 22 in-scope tables,
            ascending. This, not `affected_tables`, is what `dump` and `diff` cover,
            because a bound drawn from what a scenario EXPECTS to move cannot reveal
            a difference in anything it did not expect to move.
        assert_non_vacuous: The guard that refuses an empty verdict over empty
            tables. Called in a FIXTURE, so its failure is a pytest ERROR.
        assert_seed_fingerprints_agree: The guard that establishes the two sides
            started from the same seeded state - rows AND values, cross-checked.
        assert_tables_unchanged_by_run: The guard that establishes whether a run
            changed a table at all, per side, from the pre-run and post-run records.
        assert_system_record_parity: The parity claim no table diff can make - that
            the two cycles left the menu-persisted parameter row in the same state.
            No scenario dumps `SYSTEM-REC`, because the row carries a credential
            column, so this comparison of the two post-run digests is the only bound
            it has.
        fingerprinted_tables: The table order both runners write into their state
            records - the bounded tables as declared, then `SYSTEM-REC`.
        read_fingerprint: One state record, parsed into its per-table digests.
        assert_diff_exit_contract: The three-way exit contract of stage 8, exercised
            against the real comparison on trees the caller publishes. Needs no
            stack.
        assert_declared_statuses: The guard that reads the run stages' ACTUAL
            statuses and classifies them. Called in a FIXTURE with
            `reference_only=True`, so a mis-set-up scenario is a pytest ERROR.
        assert_operations_driven: Both run stages drove the SAME ORDERED operation
            list, which is what makes their comparison mean anything at all
. Called in a FIXTURE: a short or reordered list means the
            runner drove something other than the scenario, a pytest ERROR.
        assert_python_reproduced_disposition: The BEHAVIOURAL half of the same
            question, for a test BODY: the migrated cycle reached the disposition the
            oracle reached. A divergence here is a FAILURE, not an ERROR.
        read_dump: One dump object, parsed.
        assert_dump_wellformed: The structural contract, asserted.
        diff_trees_directly: A `TreeDiff` between two normalised trees, for an
            against-the-seed comparison the ten stages do not perform.
        fault: `HarnessFaultError`, so a test can name the class it expects.
        vocabulary: The stack-free vocabulary bundle, for a stage-backed test that
            also needs a constant.
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
    assert_wrapper_completed: Callable[..., None]
    paths: Callable[..., ScenarioPaths]
    affected_tables: Callable[[str], tuple[str, ...]]
    in_scope_tables: Callable[[], tuple[str, ...]]
    definition: Callable[[str], Mapping[str, Any]]
    assert_non_vacuous: Callable[..., None]
    assert_seed_fingerprints_agree: Callable[..., SeedFingerprints]
    assert_tables_unchanged_by_run: Callable[..., None]
    assert_system_record_parity: Callable[
        ..., tuple[TableFingerprint, TableFingerprint]
    ]
    fingerprinted_tables: Callable[..., tuple[str, ...]]
    read_fingerprint: Callable[..., tuple[TableFingerprint, ...]]
    assert_diff_exit_contract: Callable[..., None]
    assert_declared_statuses: Callable[..., tuple[str, str]]
    assert_operations_driven: Callable[..., None]
    assert_python_reproduced_disposition: Callable[..., str]
    read_dump: Callable[..., dict[str, Any]]
    assert_dump_wellformed: Callable[..., None]
    diff_trees_directly: Callable[..., Any]
    fault: type[HarnessFaultError]
    vocabulary: Vocabulary



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
    DOES NOT RAISE - it arrives as `run_date == 0`, which is anomaly A-16 reproduced,
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

    Skips when the stack is unavailable, and asserts the RUNTIME autocommit mode
    before yielding, so a test never reads a database through a connection whose
    mode says a seeding window is still open (ambiguity-resolutions.md#q-10).

    WHAT THIS IS NOT FOR, AND WHY NO TEST CURRENTLY USES IT. This reads the LIVE
    SHARED database AT THE MOMENT THE TEST RUNS. It is therefore NOT evidence about a
    completed run: `run_scenario_parity` is CACHED, its stage 5 drops, re-applies the
    frozen schema and re-seeds BETWEEN the two sides, and every scenario in the suite
    shares one database - so by the time a test executes, the row it reads may be the
    freshly seeded one, the migrated cycle's, or another scenario's. A test that wants
    a fact about one side of one run must take it from that side's OWN captured stream:
    both runners read the values they can only observe live - the pinned `RUN-DAT`, the
    fan-out switch, the two one-shot posting latches - in their post-run assertion
    stage and print them into their capture, where they are immutable and attributable.
    `tests/scenarios/test_period_end_totals_update.py`'s latch assertion was moved off
    this fixture onto those markers for exactly that reason. This fixture remains
    published for a genuine live-state question, which is a different kind of question
    from "what did that run leave behind".

    Yields:
        The open DB-API connection. Released with `rollback()` and closed on exit,
        because this path only ever reads.
    """
    requires_stack()
    dump_tables = harness_dump_tables()
    with dump_tables.connect() as connection:
        assert_runtime_autocommit_on(connection)
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
        assert_wrapper_completed=assert_wrapper_completed,
        paths=scenario_paths,
        affected_tables=scenario_affected_tables,
        in_scope_tables=in_scope_tables,
        definition=scenario_definition,
        assert_non_vacuous=assert_parity_non_vacuous,
        assert_seed_fingerprints_agree=assert_seed_fingerprints_agree,
        assert_tables_unchanged_by_run=assert_tables_unchanged_by_run,
        assert_system_record_parity=assert_system_record_parity,
        fingerprinted_tables=fingerprinted_tables,
        read_fingerprint=read_fingerprint,
        assert_diff_exit_contract=assert_diff_exit_contract,
        assert_declared_statuses=assert_declared_run_statuses,
        assert_operations_driven=assert_operations_driven,
        assert_python_reproduced_disposition=assert_python_reproduced_disposition,
        read_dump=read_dump,
        assert_dump_wellformed=assert_dump_wellformed,
        diff_trees_directly=diff_trees_directly,
        fault=HarnessFaultError,
        vocabulary=build_vocabulary(),
    )


@pytest.fixture(scope="session")
def vocabulary() -> Vocabulary:
    """The shared vocabulary and the pure helpers. NEEDS NO STACK.

    THE FIXTURE THAT REMOVES THE LAST REASON TO IMPORT THIS MODULE. A stack-free
    precondition test needs the operation names both runners accept, the term codes,
    the scenario keys and the pinned pair; reaching them through an `import conftest`
    binds the whole scenario tier to pytest's default import mode, so collection fails
    outright under `--import-mode=importlib`. Every one of them arrives here instead.

    Session-scoped, because the bundle is frozen and derived - two per-test copies
    would be the same object's contents twice over.

    Returns:
        The bundle.
    """
    return build_vocabulary()


@pytest.fixture(scope="session")
def scenario_loader() -> Callable[[str], Mapping[str, Any]]:
    """A loader for one scenario definition, duplicate-rejecting.

    Needs no stack: a scenario definition is a file on disk. Parsing goes through
    `harness/normalize.py`, so a repeated mapping key is a hard parse failure
    rather than a silent last-one-wins. ONLY THE KEYS THE HELPERS CONSUME ARE
    CHECKED FOR PRESENCE and nothing is interpreted, because judging a scenario's
    declared contents would be the added validation rule R-3 forbids.

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


# ---------------------------------------------------------------------------
#  SESSION TEARDOWN -- THE PER-RUN CREDENTIAL CARRIER DOES NOT OUTLIVE THE SESSION
#
#  The compiled side reads its database account out of the SEEDED SYSTEM record
#  [copybooks/wssystem.cob:L137-L139], so `harness/seed.sh` stages a `system.dat`
#  that carries it and `harness/run_cobol_scenario.sh` check 7/8 REQUIRES that file
#  to still be there when the compiled cycle runs. The carrier therefore cannot be
#  destroyed when seeding ends - it is an input to a later stage - which is why it
#  is destroyed HERE instead, once every stage that needs it has run.
#
#  ONLY THE PER-RUN COPY. The fixture under `$ACAS_FIXTURES` is a build product the
#  next session's stage 1 re-stages from, and `_probe_built_fixtures` skips the whole
#  oracle tier when it is incomplete - so removing it here would silently disarm 114
#  tests. `harness/seed.sh --shred-credentials --include-fixtures` destroys those, as
#  the deliberate "putting the harness away" step.
#
#  IT NEVER FAILS THE SESSION. A cleanup that turns a green run red - or worse, a red
#  run into a differently-red one - hides the outcome the session was for. A failure
#  is REPORTED, with the command to run by hand, and the exit status is left alone.
# ---------------------------------------------------------------------------


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Shred the per-run credential carriers this session's seeds left staged.

    Args:
        session: The finished session, used only to reach the terminal reporter.
        exitstatus: The session's status, neither read nor changed - the cleanup is
            unconditional, because a failed run leaves the same carrier behind as a
            successful one.
    """
    del exitstatus  # The carrier is shredded on both outcomes.

    data_root = (os.environ.get(ENV_DATA) or "").strip()
    if not data_root:
        #  No data root configured means no stage-bound tier ran in this session -
        #  the bare-host case - so there is nothing staged to destroy.
        return
    if not SEED_SCRIPT.is_file() or not Path(data_root).is_dir():
        return

    staged = [
        entry
        for entry in sorted(Path(data_root).iterdir())
        if entry.is_dir() and entry.name != "fixtures"
    ]
    if not staged:
        return

    reporter = session.config.pluginmanager.get_plugin("terminalreporter")

    def note(line: str) -> None:
        """Put one line where the operator will see it, or on stderr if headless."""
        if reporter is not None:
            reporter.write_line(line)
        else:  # pragma: no cover - only when the terminal plugin is disabled
            print(line, file=sys.stderr)

    try:
        completed = subprocess.run(  # noqa: S603 - a fixed, repository-owned script
            (str(SEED_SCRIPT), "--shred-credentials", "--data-dir", data_root),
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
            stdin=subprocess.DEVNULL,
            cwd=str(REPO_ROOT),
            #  Least privilege on the way out as on the way in: this destroys files
            #  and administers no schema.
            env=without_admin_credentials(os.environ),
        )
    except (OSError, subprocess.SubprocessError) as exc:
        note(
            f"credential cleanup could not run: {exc}. Destroy the staged carriers "
            f"by hand: harness/seed.sh --shred-credentials --data-dir {data_root}"
        )
        return

    if completed.returncode != 0:
        note(
            f"credential cleanup exited {completed.returncode}; the staged "
            f"system.dat files may still hold the database account. Run "
            f"harness/seed.sh --shred-credentials --data-dir {data_root} by hand."
        )
        for line in (completed.stderr or "").splitlines()[:5]:
            note(f"  {line}")
        return

    for line in (completed.stdout or "").splitlines():
        if "shredded" in line or "destroyed" in line:
            note(line)
