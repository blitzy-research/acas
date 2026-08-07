"""Regression locks for the deployment contract and the IRS bind boundary.

WHY THIS FILE IS IN THE `arithmetic` TIER, WHICH IS OTHERWISE ABOUT PICTURE
CLAUSES. That tier's defining property is not its subject but its dependencies:
it needs no database, no COBOL and no Docker, so it runs anywhere. Every
assertion below reads a declaration or calls a pure function, so it belongs to
that tier and NOT to `tests/scenarios/`, whose fixtures require the Compose
stack. `tests/arithmetic/test_shared_storage_and_dispatch_boundaries.py` set the
precedent for a stack-free structural lock living here.

WHAT IS LOCKED, AND WHICH DEFECT EACH LOCK CLOSES:

  * F-07 - ONE transport environment contract. There were two: this package
    declared four flag variables that nothing in the shipped stack set, while
    `acas_posting/cli/args.py` read a fifth with a DIFFERENT rule for what counts
    as an affirmative value. The tests here assert that every row of
    `rdbms_params.TRANSPORT_CONTRACT` has a consumer (a field of
    `TransportPolicyParams`, which `install_connection_policy` turns into the
    installed `ConnectionPolicy`), that the row the harness provides is the one
    `harness/docker-compose.yml` actually sets, and that a command-line
    declaration can no longer annul the contract's refusal switches.

  * F-05 - the three driver deadlines are finite, and the two layers that name
    their defaults agree. `dal/connection.py` may not import the entry-point
    layer, so the defaults are declared twice by necessity; this is what stops
    them drifting.

  * F-01 - the IRS route binds once. `bind_irs_route` publishes the snapshot its
    single `zz090` pass captured, and `bind_irs_linkage` delegates to it rather
    than repeating the bind.

  * F-42 - cross-file references into the harness scripts name a SYMBOL and not a
    line number. 91 distinct line-number locators had accumulated across the nine
    scenario YAMLs, the migration documents and the scenario tests, and they were
    stale by construction: they point into files this project edits, so every edit
    moves them, and the stale reference then reads as present evidence for
    whatever happens to sit at that line. The four tests at the end of this file
    assert that no such locator has come back -- into a harness script or into a
    scenario definition -- and that every symbol and every quoted section heading
    named actually exists in the file named. Locators into the FROZEN tree -- the
    `.cbl`, `.cob`, `.sql` and `.sh` files under `common/`, `copybooks/`,
    `general/`, `sales/`, `purchase/`, `irs/`, `stock/`, `mysql/` -- are exempt and
    deliberately so: those files cannot change (AAP 0.8.1), so a line number in
    them is permanently valid and is the most precise reference available.

EVERY SHIPPED MODULE HERE IS IMPORTED WITH `importlib.import_module` AND NOT WITH
`pytest.importorskip`. That is deliberate and it matches the discipline the rest of
this tier states at length: `acas_posting.cli.args`, `acas_posting.cli.rdbms_params`,
`acas_posting.cli.gl_post_cycle` and `acas_posting.dal.connection` are all part of the
shipped package, and `mysql-connector-python` is a hard `[project.dependencies]` entry
and a hard `requirements.txt` pin -- so a module that cannot be imported at all is a
BROKEN ENVIRONMENT or a broken module, never a supported configuration. An
`importorskip` here reported exactly that condition as a PASS, which is the one outcome
a regression lock must not have; `importlib.import_module` lets the `ImportError` reach
pytest as the failure it is. The same argument, at greater length, is in
`tests/arithmetic/test_compute_truncate_unrounded.py`'s `_shipped_module`.
"""

from __future__ import annotations

import argparse
import ast
import builtins
import dataclasses
import importlib.util
import inspect
import re
import symtable
import sys
import textwrap
import tomllib
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Any

import pytest


pytestmark = pytest.mark.arithmetic


#: A complete six-parameter connection contract, with values that reach nothing.
#: `_bind_system_record` refuses an environment carrying none of the six rather
#: than binding the copybook's placeholder literals, so a binder test has to state
#: them; these are obviously synthetic and no connection is opened by any test in
#: this file.
_FAKE_CONTRACT: dict[str, str] = {
    "ACAS_DB_HOST": "127.0.0.1",
    "ACAS_DB_PORT": "3306",
    "ACAS_DB_NAME": "ACASDB",
    "ACAS_DB_USER": "unit-test",
    "ACAS_DB_PASSWORD": "unit-test",
    "ACAS_DB_SOCKET": "",
}


_COMPOSE = (
    Path(__file__).resolve().parents[2] / "harness" / "docker-compose.yml"
)


def _compose_environment_names() -> frozenset[str]:
    """Return every `ACAS_DB_*` variable the compose file sets in an env block.

    Read with a line regex rather than a YAML parser: the assertion is about the
    literal names a reader of the file sees being set, and the tier is the one
    that must import with nothing installed but pytest.

    Returns:
        The set of variable names assigned in the file, without values - so a
        credential in the file could never reach a failure message.
    """
    text = _COMPOSE.read_text(encoding="utf-8")
    return frozenset(
        match.group(1)
        for match in re.finditer(
            r"^\s{6}(ACAS_DB_[A-Z0-9_]+):", text, flags=re.MULTILINE
        )
    )


def test_every_transport_contract_row_has_a_consumer() -> None:
    """No declared knob may be unread: each names a TransportPolicyParams field."""
    rdbms_params = importlib.import_module("acas_posting.cli.rdbms_params")

    fields = {
        field.name
        for field in dataclasses.fields(rdbms_params.TransportPolicyParams)
    }
    assert fields, "TransportPolicyParams declares no fields"

    for entry in rdbms_params.TRANSPORT_CONTRACT:
        assert entry.field in fields, (
            f"{entry.variable} resolves into {entry.field!r}, which is not a "
            f"field of TransportPolicyParams; a knob nothing reads is a knob "
            f"that lies about what it does (finding F-07)"
        )


def test_every_transport_policy_field_has_a_provider() -> None:
    """No field may be unreachable: each is named by at least one contract row."""
    rdbms_params = importlib.import_module("acas_posting.cli.rdbms_params")

    declared = {entry.field for entry in rdbms_params.TRANSPORT_CONTRACT}
    for field in dataclasses.fields(rdbms_params.TransportPolicyParams):
        assert field.name in declared, (
            f"TransportPolicyParams.{field.name} is resolved from no declared "
            f"variable, so a deployment cannot set it (finding F-07)"
        )


def test_contract_variable_names_are_unique_and_alias_targets_exist() -> None:
    """One name means one thing, and an alias names a row that is really there."""
    rdbms_params = importlib.import_module("acas_posting.cli.rdbms_params")

    names = [entry.variable for entry in rdbms_params.TRANSPORT_CONTRACT]
    assert len(names) == len(set(names)), f"duplicate contract variable: {names}"

    canonical = {
        entry.variable
        for entry in rdbms_params.TRANSPORT_CONTRACT
        if entry.alias_of is None
    }
    for entry in rdbms_params.TRANSPORT_CONTRACT:
        if entry.alias_of is not None:
            assert entry.alias_of in canonical, (
                f"{entry.variable} is declared an alias of {entry.alias_of!r}, "
                f"which is not a canonical row of the contract"
            )


def test_the_harness_provides_exactly_the_rows_marked_provided() -> None:
    """`provided_by_harness` is a claim about docker-compose.yml, so check it."""
    rdbms_params = importlib.import_module("acas_posting.cli.rdbms_params")

    if not _COMPOSE.is_file():  # pragma: no cover - the file is committed
        pytest.skip(f"{_COMPOSE} is absent, so its claims cannot be checked")

    supplied = _compose_environment_names()
    for entry in rdbms_params.TRANSPORT_CONTRACT:
        if entry.provided_by_harness:
            assert entry.variable in supplied, (
                f"{entry.variable} is marked provided_by_harness but "
                f"harness/docker-compose.yml does not set it (finding F-07)"
            )


def test_the_canonical_isolated_oracle_name_is_the_harness_spelling() -> None:
    """The Python and shell halves must read ONE variable, and only that one.

    The defect was two spellings for one decision - the harness exported
    `ACAS_DB_ALLOW_PLAINTEXT` while this module also read `ACAS_DB_ISOLATED_ORACLE`,
    so a deployment could set the one nothing read and believe it had declared
    something. Reading the second name as an ALIAS closes the silent case; reading
    ONE NAME closes it and leaves nothing to explain, which is what the contract
    does now.
    """
    rdbms_params = importlib.import_module("acas_posting.cli.rdbms_params")

    assert (
        rdbms_params.TRANSPORT_ALLOW_PLAINTEXT_VARIABLE
        == "ACAS_DB_ALLOW_PLAINTEXT"
    )

    #  Exactly one contract row resolves the grant, and it is that name.
    rows = [
        entry
        for entry in rdbms_params.TRANSPORT_CONTRACT
        if entry.field == "isolated_oracle"
    ]
    assert [entry.variable for entry in rows] == ["ACAS_DB_ALLOW_PLAINTEXT"]
    assert rows[0].alias_of is None


def test_the_superseded_spelling_is_not_read_at_all() -> None:
    """The second name declares NOTHING, and no row or attribute names it.

    A deployment that exports only the superseded spelling gets no grant - which is
    the fail-closed answer, because the value governs whether a credential and every
    posted figure may cross a network in the clear. Asserted three ways so the name
    cannot creep back as a row, as a constant, or as a reader.
    """
    rdbms_params = importlib.import_module("acas_posting.cli.rdbms_params")

    superseded = "ACAS_DB_ISOLATED_ORACLE"

    from_superseded = rdbms_params.resolve_transport_policy({superseded: "1"})
    assert from_superseded.isolated_oracle is False

    both = rdbms_params.resolve_transport_policy(
        {"ACAS_DB_ALLOW_PLAINTEXT": "0", superseded: "1"}
    )
    assert both.isolated_oracle is False

    assert superseded not in {
        entry.variable for entry in rdbms_params.TRANSPORT_CONTRACT
    }
    assert superseded not in {
        entry.alias_of for entry in rdbms_params.TRANSPORT_CONTRACT
    }
    assert not [
        name
        for name in dir(rdbms_params)
        if getattr(rdbms_params, name, None) == superseded
    ]


def test_affirmative_spellings_match_the_shell_scripts_closed_set() -> None:
    """`false` must not mean yes, and a spelling in NEITHER set stops the run.

    THE SET IS CLOSED AT BOTH ENDS, and that is the whole of the remediation. Reading
    an unrecognised value as "no" was the original defect in reverse: `false` read as
    yes, `maybe` read as no, and either way the operator who typed it was never told.
    `harness/seed.sh acas_plaintext_declared` matches `1|true|yes|on` and
    `''|0|false|no|off` case-insensitively and DIES on anything else; this module's
    `read_declared_flag` raises on anything else. `Y` is in neither set, in either
    half, so it is refused rather than guessed at.
    """
    rdbms_params = importlib.import_module("acas_posting.cli.rdbms_params")

    assert rdbms_params.AFFIRMATIVE_SPELLINGS == frozenset({"1", "true", "yes", "on"})
    assert rdbms_params.NEGATIVE_SPELLINGS == frozenset({"", "0", "false", "no", "off"})

    #  Case and surrounding space are normalised, and nothing else is.
    for spelling in ("1", "true", "yes", "on", " TRUE ", "On", "YES"):
        assert rdbms_params.resolve_transport_policy(
            {"ACAS_DB_ALLOW_PLAINTEXT": spelling}
        ).isolated_oracle, spelling

    for spelling in ("", "  ", "0", "false", "no", "off", "FALSE"):
        assert not rdbms_params.resolve_transport_policy(
            {"ACAS_DB_ALLOW_PLAINTEXT": spelling}
        ).isolated_oracle, spelling

    for spelling in ("Y", "N", "maybe", "2", "true-ish"):
        with pytest.raises(rdbms_params.RdbmsParamError):
            rdbms_params.resolve_transport_policy(
                {"ACAS_DB_ALLOW_PLAINTEXT": spelling}
            )


def test_driver_deadlines_are_finite_and_agree_across_the_two_layers() -> None:
    """The DAL may not import the CLI, so the two default sets must be equal."""
    rdbms_params = importlib.import_module("acas_posting.cli.rdbms_params")
    connection = importlib.import_module("acas_posting.dal.connection")

    assert (
        rdbms_params.CONNECT_TIMEOUT_DEFAULT
        == connection.DEFAULT_CONNECT_TIMEOUT_SECONDS
    )
    assert (
        rdbms_params.READ_TIMEOUT_DEFAULT
        == connection.DEFAULT_READ_TIMEOUT_SECONDS
    )
    assert (
        rdbms_params.WRITE_TIMEOUT_DEFAULT
        == connection.DEFAULT_WRITE_TIMEOUT_SECONDS
    )

    deadlines = connection.ConnectionPolicy().driver_deadlines()
    assert set(deadlines) == {
        "connection_timeout",
        "read_timeout",
        "write_timeout",
    }
    assert all(isinstance(value, int) and value > 0 for value in deadlines.values())


def test_a_configured_deadline_reaches_the_policy() -> None:
    """A deployment that asks for a different budget gets it."""
    rdbms_params = importlib.import_module("acas_posting.cli.rdbms_params")

    resolved = rdbms_params.resolve_transport_policy(
        {
            "ACAS_DB_CONNECT_TIMEOUT": "5",
            "ACAS_DB_READ_TIMEOUT": "60",
            "ACAS_DB_WRITE_TIMEOUT": "90",
        }
    )
    assert resolved.connect_timeout_seconds == 5
    assert resolved.read_timeout_seconds == 60
    assert resolved.write_timeout_seconds == 90


@pytest.mark.parametrize("value", ["0", "-1", "abc", "86401", "1.5"])
def test_a_malformed_deadline_is_refused_rather_than_replaced(value: str) -> None:
    """An unbounded or unreadable budget is a refusal, not a silent default."""
    rdbms_params = importlib.import_module("acas_posting.cli.rdbms_params")

    with pytest.raises(rdbms_params.RdbmsParamError):
        rdbms_params.resolve_transport_policy({"ACAS_DB_READ_TIMEOUT": value})


def test_a_command_line_declaration_cannot_annul_the_contract() -> None:
    """There is no command line to annul it WITH: the option surface is withdrawn.

    TWO REMEDIATIONS, AND THE TREE CARRIES THE STRONGER. Publishing
    `--db-tls-ca/-cert/-key` and `--db-allow-plaintext` and then returning
    `ConnectionPolicy(transport=stated)` the moment one was typed SILENTLY DROPPED the
    refusal-and-allowance knobs and the three driver deadlines. Merging the typed
    declaration over the contract field by field fixes that. WITHDRAWING the options
    fixes it and removes the surface as well: a program input and two refusal outcomes
    the compiled program has not got are themselves a behaviour change (rule R-3),
    and a certificate path on a command line is a process-listing leak
    [common/acas-get-params.cbl:L30].

    So the property this test defends is now stated positively: the contract is read
    ONCE, every field of it survives, and there is no argv path into the policy at
    all - asserted on the absent binder, the absent parameter and the absent option
    strings, because any one of those returning is the overlay coming back.
    """
    args = importlib.import_module("acas_posting.cli.args")
    connection = importlib.import_module("acas_posting.dal.connection")

    assert not hasattr(args, "add_transport_security_arguments")
    assert not hasattr(args, "bind_transport_security")
    assert "namespace" not in inspect.signature(
        args.install_connection_policy
    ).parameters

    #  No route publishes a transport option either, which is what makes the
    #  paragraph above true of the shipped CLI rather than of one function.
    cli_dir = Path(args.__file__).resolve().parent
    for module in sorted(cli_dir.glob("*.py")):
        text = module.read_text(encoding="utf-8")
        for option in ("--db-tls-ca", "--db-tls-cert", "--db-tls-key"):
            assert f'"{option}"' not in text, f"{module.name} publishes {option}"

    try:
        policy = args.install_connection_policy(
            {
                "ACAS_DB_ALLOW_PLAINTEXT": "1",
                "ACAS_DB_REQUIRE_TLS": "1",
                "ACAS_DB_REQUIRE_DECLARED_CREDENTIALS": "1",
                "ACAS_DB_READ_TIMEOUT": "45",
            }
        )

        #  THE WHOLE CONTRACT SURVIVES: the transport material, both refusal knobs
        #  and the deadline. This is the assertion the overlay defect broke.
        assert policy.transport is not None
        assert policy.transport.isolated_oracle is True
        assert policy.require_encrypted_transport is True
        assert policy.require_declared_placeholder_credentials is True
        assert policy.read_timeout_seconds == 45
    finally:
        connection.reset_connection_policy()


def test_the_contract_alone_installs_the_same_transport_declaration() -> None:
    """The contract is the only source, and it is honoured on its own."""
    args = importlib.import_module("acas_posting.cli.args")
    connection = importlib.import_module("acas_posting.dal.connection")

    try:
        policy = args.install_connection_policy({"ACAS_DB_ALLOW_PLAINTEXT": "1"})
        assert policy.transport is not None
        assert policy.transport.isolated_oracle is True
        assert policy.require_encrypted_transport is False
    finally:
        connection.reset_connection_policy()


def test_bind_irs_route_publishes_the_snapshot_of_its_single_zz090_pass() -> None:
    """F-01: one bind, one key-1 load, one remap, and the snapshot comes back."""
    args = importlib.import_module("acas_posting.cli.args")

    parser = argparse.ArgumentParser()
    args.add_irs_linkage_arguments(parser)
    namespace = parser.parse_args(["--run-date", "21/09/2025"])

    binding = args.bind_irs_route(namespace, env=_FAKE_CONTRACT)

    assert isinstance(binding, args.IrsRouteBinding)
    assert isinstance(binding.linkage, args.IrsLinkage)
    #  No `menu_state`, so `zz090` is not performed at all - exactly as a caller
    #  that never reaches [irs/irs.cbl:L556] leaves it.
    assert binding.pre_dispatch_snapshot is None
    assert binding.linkage.irs_system_params.run_date == "21/09/25"
    assert binding.linkage.ws_system_record.system_data_block.run_date == 155127


def test_bind_irs_linkage_delegates_to_bind_irs_route() -> None:
    """Two entry points, ONE implementation, so they cannot drift (F-01)."""
    args = importlib.import_module("acas_posting.cli.args")

    parser = argparse.ArgumentParser()
    args.add_irs_linkage_arguments(parser)
    namespace = parser.parse_args(["--run-date", "21/09/2025"])

    linkage = args.bind_irs_linkage(namespace, env=_FAKE_CONTRACT)
    route = args.bind_irs_route(namespace, env=_FAKE_CONTRACT)

    assert type(linkage) is type(route.linkage)
    assert linkage.irs_system_params.run_date == route.linkage.irs_system_params.run_date
    assert (
        linkage.ws_system_record.system_data_block.run_date
        == route.linkage.ws_system_record.system_data_block.run_date
    )


def test_load00_publishes_no_transport_parameter() -> None:
    """F-03: the unused keyword-only parameter must stay removed."""
    import inspect

    gl_post_cycle = importlib.import_module("acas_posting.cli.gl_post_cycle")

    parameters = inspect.signature(gl_post_cycle.load00).parameters
    assert "transport" not in parameters
    assert list(parameters) == [
        "linkage",
        "program",
        "program_id",
        "menu_state",
        "work_files",
    ]


# ---------------------------------------------------------------------------
# F-42 -- cross-file references into the harness scripts
# ---------------------------------------------------------------------------

#: The FROZEN tree, verbatim from AAP 0.8.1 plus the maintainer's own documents. A
#: line number into any of these is permanently valid, because the file cannot
#: change, and is therefore the most precise reference available. Everything else in
#: the repository is written by this migration and moves.
_FROZEN_PREFIXES: tuple[str, ...] = (
    "common/",
    "copybooks/",
    "general/",
    "sales/",
    "purchase/",
    "irs/",
    "stock/",
    "mysql/",
    "etc/",
    "payroll/",
    "Basic-Code/",
    "ACAS-Manuals/",
    "home/",
    "presql2-package/",
)

#: Individual frozen files at the repository root.
_FROZEN_FILES: frozenset[str] = frozenset(
    {
        "README.TXT",
        "README",
        "README.SVN",
        "README.nightly",
        "Changelog",
        "comp-all.sh",
        "comp-all-noflags.sh",
    }
)

#: The harness files whose line numbers move whenever this project edits them, and
#: which are therefore referenced by symbol. `harness/scenario_stream.py` and
#: `harness/parity_stages.sh` are included even though nothing references them by
#: line today, so that a first such reference is caught rather than admitted.
_EDITABLE_HARNESS_FILES: tuple[str, ...] = (
    "run_cobol_scenario.sh",
    "run_python_scenario.sh",
    "seed.sh",
    "reset_db.sh",
    "build_oracle.sh",
    "build_fixtures.sh",
    "run_parity.sh",
    "parity_stages.sh",
    "dump_tables.py",
    "normalize.py",
    "diff_states.py",
    "make_fixtures.py",
    "scenario_stream.py",
)

#: Where cross-file references are written: the scenario definitions, the four
#: migration documents and the test suites. Not the harness scripts themselves --
#: a script referring to its own neighbour by line is a separate matter and none
#: does.
_REFERENCE_SOURCES: tuple[str, ...] = (
    "harness/scenarios/*.yaml",
    "docs/migration/*.md",
    "tests/arithmetic/*.py",
    "tests/scenarios/*.py",
    "tests/determinism/*.py",
    "tests/*.py",
)

_LINE_LOCATOR = re.compile(
    r"harness/(" + "|".join(re.escape(name) for name in _EDITABLE_HARNESS_FILES)
    + r"):L\d+"
)

#: `[harness/<file> <symbol>]` -- the shape every converted reference takes. The
#: SQUARE BRACKETS are part of the pattern and must stay: without them this also
#: matches ordinary prose such as "harness/seed.sh reproduces the loader contract",
#: where the following word is English rather than a symbol name.
_SYMBOL_REFERENCE = re.compile(
    r"\[harness/(" + "|".join(re.escape(name) for name in _EDITABLE_HARNESS_FILES)
    + r")\s+([A-Za-z_][A-Za-z0-9_]*)\]"
)

#: The same idea for a `.py` module of this project, referenced either bracketed or
#: in backticks: `[acas_posting/cobol/usage.py byte_length]` and
#: `` `tests/conftest.py REPO_ROOT` ``. The delimiter is again what keeps prose out:
#: "acas_posting/cobol/usage.py states the rule" must not be read as a symbol.
_MODULE_SYMBOL_REFERENCE = re.compile(
    r"[\[`]((?:acas_posting|tests|harness)/[A-Za-z0-9_./\-]+\.py)"
    r"\s+([A-Za-z_][A-Za-z0-9_]*)[\]`]"
)

_SHELL_FUNCTION = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*\(\)")
_SHELL_VARIABLE = re.compile(
    r"^\s*(?:readonly\s+)?(?:declare\s+)?(?:-a\s+|-i\s+|-r\s+)?"
    r"([A-Z_][A-Z0-9_]*)="
)
_PYTHON_DEF = re.compile(r"^(?:async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)")
_PYTHON_CLASS = re.compile(r"^class\s+([A-Za-z_][A-Za-z0-9_]*)")
_PYTHON_CONSTANT = re.compile(r"^([A-Z_][A-Z0-9_]*)\s*(?::|=)")


def _reference_source_files() -> list[Path]:
    """Every file in which a cross-file reference may legitimately appear."""
    root = Path(__file__).resolve().parents[2]
    found: list[Path] = []
    for pattern in _REFERENCE_SOURCES:
        found.extend(sorted(root.glob(pattern)))
    return found


_PYTHON_METHOD = re.compile(r"^\s{4}(?:async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)")


def _symbols_in(relative_path: str) -> frozenset[str]:
    """Return every symbol the file at `relative_path` defines.

    Shell functions, upper-case shell variables, Python defs, classes, module-level
    constants and four-space-indented methods -- the six shapes a reference can
    legitimately name. Deliberately a line scan rather than an `ast` parse: the shell
    files are half the corpus, and a reference is checked against what a reader of
    the file sees declared.

    Args:
        relative_path: repository-relative path, e.g. `harness/seed.sh`.

    Returns:
        The names that file declares, empty when the file does not exist.
    """
    path = Path(__file__).resolve().parents[2] / relative_path
    if not path.is_file():
        return frozenset()
    names: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        for pattern in (
            _SHELL_FUNCTION,
            _SHELL_VARIABLE,
            _PYTHON_DEF,
            _PYTHON_CLASS,
            _PYTHON_CONSTANT,
            _PYTHON_METHOD,
        ):
            match = pattern.match(line)
            if match:
                names.add(match.group(1))
    return frozenset(names)


def _defined_symbols(harness_file: str) -> frozenset[str]:
    """Return every top-level symbol `harness/<harness_file>` defines.

    Args:
        harness_file: bare file name under `harness/`.

    Returns:
        The names defined at the top level of that file.
    """
    return _symbols_in(f"harness/{harness_file}")


#: `[harness/scenarios/<file>.yaml "SOME HEADING"]` -- the same idea for a file that
#: has no symbols. A scenario definition is prose under keys, so the durable handle
#: is a section heading, quoted verbatim. The heading may wrap across source lines,
#: so the match is taken over the whole file text rather than line by line.
_YAML_HEADING_REFERENCE = re.compile(
    r"\[harness/scenarios/([a-z_0-9]+\.yaml)\s*\n?\s*\"([^\"]{8,})\"\]"
)


#: `<some/path.ext>:L<n>` in any shape this repository writes.
_ANY_LINE_LOCATOR = re.compile(
    r"\b((?:[A-Za-z0-9_.\-]+/)*[A-Za-z0-9_.\-]+"
    r"\.(?:py|sh|yml|yaml|toml|json|md|cbl|cob|sql|scb|txt|conf))"
    r":L\d+"
)


def _is_frozen(path_text: str) -> bool:
    """True when `path_text` names a file the migration may not modify.

    Args:
        path_text: a repository-relative path as it appears inside a locator.

    Returns:
        Whether the path is under a frozen directory or is a frozen root file.
    """
    return path_text.startswith(_FROZEN_PREFIXES) or path_text in _FROZEN_FILES


def test_no_reference_names_a_line_in_a_file_this_migration_writes() -> None:
    """The general form of F-42, so the defect cannot come back somewhere new.

    A line number is a perfectly good reference into the FROZEN tree, where the file
    cannot change. Into a file this migration writes it is stale at the next edit --
    and the stale reference then reads as present evidence for whatever now sits at
    that line, which is how `period_end_totals.yaml` came to cite a `trap` statement
    as the operation/subsystem cross-check and how a locator into
    `acas_posting/dal/connection.py` came to be cited as where `autocommit` is set
    while pointing three paragraphs of docstring away from the assignment.

    Name a symbol, or quote a section heading for a file that has none. Both forms
    are then verified by the tests that follow.
    """
    offenders: list[str] = []
    for path in _reference_source_files():
        for number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            for match in _ANY_LINE_LOCATOR.finditer(line):
                if _is_frozen(match.group(1)):
                    continue
                offenders.append(f"{path.name}:{number}: {match.group(0)}")
    assert not offenders, (
        "these references name a line in a file this migration writes, so each will "
        "be stale at the next edit of that file. Name the function, class, variable "
        "or constant instead, or quote a section heading for a file with no "
        "symbols:\n  " + "\n  ".join(offenders)
    )


def test_every_scenario_heading_reference_resolves() -> None:
    """A quoted heading must appear, verbatim, in the definition it names."""
    root = Path(__file__).resolve().parents[2]
    unresolved: list[str] = []
    checked = 0
    for path in _reference_source_files():
        text = path.read_text(encoding="utf-8")
        for match in _YAML_HEADING_REFERENCE.finditer(text):
            scenario_file, heading = match.group(1), match.group(2)
            checked += 1
            target = root / "harness" / "scenarios" / scenario_file
            # The reference itself may be wrapped, so the heading is re-joined on
            # single spaces before the search, and the target is collapsed the same
            # way. Nothing else about either text is altered.
            wanted = " ".join(heading.split())
            haystack = " ".join(target.read_text(encoding="utf-8").split())
            if not target.is_file() or wanted not in haystack:
                unresolved.append(f"{path.name}: {scenario_file} has no {wanted!r}")
    assert checked, (
        "no `[harness/scenarios/<file>.yaml \"HEADING\"]` reference was found, so "
        "this test is asserting nothing."
    )
    assert not unresolved, (
        "these references quote a heading their scenario definition does not "
        "carry:\n  " + "\n  ".join(unresolved)
    )


def test_no_reference_names_a_harness_script_line_number() -> None:
    """A line number into an editable harness script is stale by construction.

    It moves with every edit of that script, and the moved reference then reads as
    present evidence for whatever now sits at that line -- which is how
    `period_end_totals.yaml` came to cite a `trap` statement as the operation and
    subsystem cross-check. Symbols are used instead.
    """
    offenders: list[str] = []
    for path in _reference_source_files():
        text = path.read_text(encoding="utf-8")
        for number, line in enumerate(text.splitlines(), start=1):
            for match in _LINE_LOCATOR.finditer(line):
                offenders.append(f"{path.name}:{number}: {match.group(0)}")
    assert not offenders, (
        "these references name a line in a harness script this project edits, so "
        "they will be stale at the next edit of that script. Name the function, "
        "variable or constant instead:\n  " + "\n  ".join(offenders)
    )


def test_every_harness_symbol_reference_resolves() -> None:
    """A symbol reference is only better than a line number if it is checked.

    An unresolvable name is a louder failure than a moved line number, which is
    the point: renaming a function breaks the reference here rather than leaving
    the prose quietly describing something that no longer exists.
    """
    unresolved: list[str] = []
    checked = 0
    for path in _reference_source_files():
        text = path.read_text(encoding="utf-8")
        for number, line in enumerate(text.splitlines(), start=1):
            for match in _SYMBOL_REFERENCE.finditer(line):
                harness_file, symbol = match.group(1), match.group(2)
                checked += 1
                if symbol not in _defined_symbols(harness_file):
                    unresolved.append(
                        f"{path.name}:{number}: harness/{harness_file} "
                        f"defines no {symbol!r}"
                    )
    assert checked, (
        "no `harness/<file> <symbol>` reference was found at all, so this test is "
        "asserting nothing. The 129 references converted for F-42 should be here."
    )
    assert not unresolved, (
        "these cross-file references name a symbol their target does not "
        "define:\n  " + "\n  ".join(unresolved)
    )


#: `<number word> ... under|of `<directory>`` -- how the migration documents state an
#: inventory count. The word is checked against the tree, so a document cannot claim
#: fifteen files where sixteen exist. Three documents held three DIFFERENT numbers for
#: `tests/arithmetic/` before F-47.
_NUMBER_WORDS: dict[str, int] = {
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "twenty-one": 21,
    "twenty-two": 22,
    "twenty-eight": 28,
}

#: directory -> (glob, whether `__init__.py` is counted). A package directory is
#: quoted BOTH ways in the documents -- `acas_posting/programs/` as "thirteen
#: modules", counting the package marker, and `acas_posting/cobol/` as "the seven",
#: not counting it -- so both readings are accepted and only a number matching
#: NEITHER fails.
_INVENTORY_DIRECTORIES: dict[str, str] = {
    "tests/arithmetic": "test_*.py",
    "tests/scenarios": "test_*.py",
    "harness/scenarios": "*.yaml",
    "docs/migration": "*.md",
    "data_dictionary": "*.json",
    "acas_posting/programs": "*.py",
    "acas_posting/dal": "*.py",
    "acas_posting/cli": "*.py",
    "acas_posting/cobol": "*.py",
    "acas_posting/records": "*.py",
    "acas_posting/dictionary": "*.py",
}

_INVENTORY_CLAIM = re.compile(
    r"\b(" + "|".join(sorted(_NUMBER_WORDS, key=len, reverse=True)) + r")\b"
    r"((?:\s+[a-z]+){0,4}?\s+(?:under|of)\s+)`([A-Za-z_0-9/.]+?)/?`"
)


def _inventory_documents() -> list[Path]:
    """The documents that state inventory counts."""
    root = Path(__file__).resolve().parents[2]
    return sorted(root.glob("docs/migration/*.md")) + sorted(
        root.glob("README-python-migration.md")
    )


def test_documented_inventory_counts_match_the_tree() -> None:
    """A stated count must be what the directory holds.

    F-47's defect was documents preserving the counts they were authored with. The
    numbers are small and written as English words, which is exactly why nobody
    noticed three documents disagreeing about one directory. This reads the tree.
    """
    root = Path(__file__).resolve().parents[2]
    wrong: list[str] = []
    checked = 0
    for document in _inventory_documents():
        # Collapsed to one line, because a claim WRAPS: "the sixteen test\nfiles
        # under `tests/arithmetic/`" is one claim and a line-by-line scan would
        # silently skip it -- which is how a wrapped claim stayed wrong while the
        # unwrapped one beside it was corrected.
        text = " ".join(document.read_text(encoding="utf-8").split())
        for match in _INVENTORY_CLAIM.finditer(text):
            word, _, directory = match.groups()
            glob = _INVENTORY_DIRECTORIES.get(directory)
            if glob is None:
                continue
            checked += 1
            present = list((root / directory).glob(glob))
            actual = len(present)
            without_marker = len(
                [path for path in present if path.name != "__init__.py"]
            )
            claimed = _NUMBER_WORDS[word]
            if claimed not in (actual, without_marker):
                wrong.append(
                    f"{document.name}: claims {word} ({claimed}) "
                    f"for {directory}/, which holds {actual} "
                    f"({without_marker} excluding __init__.py)"
                )
    assert checked, (
        "no inventory claim was matched, so this test is asserting nothing. The "
        "documents state counts as English words followed by `of` or `under` and a "
        "backtick-quoted directory."
    )
    assert not wrong, (
        "these documented inventory counts do not match the checkout:\n  "
        + "\n  ".join(wrong)
    )


def test_every_module_symbol_reference_resolves() -> None:
    """The same guarantee for references into this project's own `.py` modules.

    These carried the same defect and one of them proved it: a locator cited as the
    place `autocommit` is set pointed at a docstring paragraph three screens away,
    and three references into sibling test modules pointed at a blank line, a closing
    parenthesis and an unrelated `for` statement.
    """
    unresolved: list[str] = []
    checked = 0
    for path in _reference_source_files():
        for number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            for match in _MODULE_SYMBOL_REFERENCE.finditer(line):
                module, symbol = match.group(1), match.group(2)
                checked += 1
                if symbol not in _symbols_in(module):
                    unresolved.append(
                        f"{path.name}:{number}: {module} defines no {symbol!r}"
                    )
    assert checked, (
        "no `<module>.py <symbol>` reference was found at all, so this test is "
        "asserting nothing."
    )
    assert not unresolved, (
        "these references name a symbol their module does not define:\n  "
        + "\n  ".join(unresolved)
    )


# ---------------------------------------------------------------------------
#  CR-02 - NO FUNCTION MAY READ A NAME NOTHING DEFINES
#
#  `tests/conftest.py`'s ten-stage helper referenced two names that existed only in
#  its CALLER's scope: `cache_key`, read on the success path of every run, and
#  `requested_operations`, read on the operation-mismatch branch. Python resolves an
#  unqualified name inside a function against the function's locals and then the
#  MODULE globals, never the caller's frame, so each read raised `NameError` - and it
#  did so AFTER an otherwise complete ten-stage protocol, so the crash landed on the
#  ordinary consumer of a successful parity run. The mismatch branch was worse: the
#  `NameError` replaced the harness-fault diagnosis with a second, unrelated failure.
#
#  Neither defect is visible to a test that never reaches the branch, and every
#  scenario module reaches the first one, which is precisely why this is a STATIC gate
#  rather than a runtime one. It costs nothing, needs no database, and it catches the
#  whole class rather than the two instances.
#
#  WHY `symtable` AND NOT A LINTER. The check has to run in this suite, on this
#  interpreter, with no tool outside `[project.optional-dependencies].test` - and
#  `symtable` is the compiler's own scope analysis, so it agrees with what the
#  interpreter will do by construction rather than by imitation. A name is reported
#  only when the compiler classified it as global AND the module binds no such name
#  AND it is not a builtin, which is exactly the condition that raises at run time.
_SCOPE_CHECKED_SOURCES: tuple[str, ...] = (
    "tests/conftest.py",
    "tests/arithmetic/*.py",
    "tests/scenarios/*.py",
    "tests/determinism/*.py",
    "harness/dump_tables.py",
    "harness/normalize.py",
    "harness/diff_states.py",
    "harness/make_fixtures.py",
    "harness/scenario_stream.py",
    "harness/table_digest.py",
)

#: The names every module has without writing them down. The import system binds
#: these before the first statement runs, so a function reading one is reading a
#: real binding even though `symtable` sees no assignment for it.
_IMPLICIT_MODULE_NAMES: frozenset[str] = frozenset(
    {
        "__annotations__",
        "__builtins__",
        "__cached__",
        "__debug__",
        "__dict__",
        "__doc__",
        "__file__",
        "__loader__",
        "__name__",
        "__package__",
        "__path__",
        "__spec__",
    }
)


def _unresolved_global_reads(path: Path) -> list[str]:
    """Return every `<scope>: <name>` a function reads but nothing can bind.

    Args:
        path: The module to analyse.

    Returns:
        One entry per offending read, empty when the module is clean.
    """
    source = path.read_text(encoding="utf-8")
    table = symtable.symtable(source, str(path), "exec")
    module_names = set(table.get_identifiers())
    builtin_names = set(dir(builtins))
    offenders: list[str] = []

    def visit(scope: symtable.SymbolTable, trail: str) -> None:
        for child in scope.get_children():
            here = f"{trail}.{child.get_name()}" if trail else child.get_name()
            if child.get_type() == "function":
                for symbol in child.get_symbols():
                    name = symbol.get_name()
                    if (
                        symbol.is_global()
                        and not symbol.is_assigned()
                        and name not in module_names
                        and name not in builtin_names
                        and name not in _IMPLICIT_MODULE_NAMES
                    ):
                        offenders.append(f"{here}: {name}")
            visit(child, here)

    visit(table, "")
    return offenders


def test_no_function_reads_a_name_nothing_defines() -> None:
    """Every global read in the harness and test seam resolves to a binding.

    THE REGRESSION THIS CLOSES is `tests/conftest.py`'s
    `_run_scenario_parity_stages`, which read `cache_key` and `requested_operations`
    from its caller's scope. Both are now parameters. A future edit that moves a
    stage out of one function and into another without carrying its inputs across
    fails here instead of at the end of a ten-stage run.
    """
    root = Path(__file__).resolve().parents[2]
    files: list[Path] = []
    for pattern in _SCOPE_CHECKED_SOURCES:
        files.extend(sorted(root.glob(pattern)))
    assert files, (
        "no module was analysed at all, so this test is asserting nothing. "
        f"Patterns: {_SCOPE_CHECKED_SOURCES!r}"
    )

    offenders: list[str] = []
    for path in files:
        for entry in _unresolved_global_reads(path):
            offenders.append(f"{path.relative_to(root)}  {entry}")

    assert not offenders, (
        "these functions read a name that neither their own scope nor their "
        "module's binds, so the read raises `NameError` the moment the line "
        "executes:\n  " + "\n  ".join(offenders) + "\n\n"
        "  A name read inside a function resolves against that function's locals "
        "and then its MODULE globals - never against the frame that called it. If "
        "the value belongs to the caller, pass it as a parameter."
    )


# ---------------------------------------------------------------------------
#  MJ-01 - THE ADMITTED-STATUS BAND IS DECLARED TWICE AND MUST AGREE
#
#  A status the Python runner admits as a DISPOSITION becomes evidence: the wrapper
#  exits 69, harness/run_parity.sh continues past stage 6 so the capture can
#  corroborate it, harness/dump_tables.py attests that capture as comparable, and
#  tests/conftest.py bands it as a behavioural difference rather than a broken rig.
#  Every one of those steps is downstream of one question - "is this status a
#  disposition at all" - and that question is answered by a table in the shell runner
#  and a table in the test seam. The two are necessarily separate: a shell script
#  cannot import a Python `Final`, and tests/conftest.py must not be imported at
#  module scope by this tier. So they are held together here.
#
#  THE AUTHORITY IS THE FROZEN SOURCE, and it is short: `move 5 to ws-term-code`
#  [general/gl070.cbl:L289], `move 8 to ws-term-code` [sales/sl055.cbl:L344] and
#  [purchase/pl055.cbl:L286]. Three sites, three codes, four operations that set none.
_CONFTEXT_TERM_CODES_NAME = "TERM_CODES"
_SHELL_TERM_CODE_MAP = re.compile(
    r"^\s*'(?P<operation>[a-z_]+)\|(?P<codes>[0-9 ]*)'\s*$"
)


def _declared_term_codes_from_conftest() -> dict[str, tuple[int, ...]]:
    """Parse `TERM_CODES` out of `tests/conftest.py` without importing it.

    Returns:
        The operation-to-term-codes mapping the test seam declares.
    """
    root = Path(__file__).resolve().parents[2]
    tree = ast.parse((root / "tests" / "conftest.py").read_text(encoding="utf-8"))
    for node in tree.body:
        target = None
        if isinstance(node, ast.AnnAssign):
            target = node.target
        elif isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
        if (
            isinstance(target, ast.Name)
            and target.id == _CONFTEXT_TERM_CODES_NAME
            and node.value is not None
        ):
            return {
                str(ast.literal_eval(key)): tuple(ast.literal_eval(value))
                for key, value in zip(node.value.keys, node.value.values)
            }
    raise AssertionError(
        f"tests/conftest.py declares no module-level {_CONFTEXT_TERM_CODES_NAME}"
    )


def _declared_term_codes_from_runner() -> dict[str, tuple[int, ...]]:
    """Parse `ACAS_PY_TERM_CODE_MAP` out of the Python runner.

    Returns:
        The operation-to-term-codes mapping the runner declares.
    """
    root = Path(__file__).resolve().parents[2]
    lines = (
        (root / "harness" / "run_python_scenario.sh")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    try:
        start = next(
            index
            for index, line in enumerate(lines)
            if line.startswith("readonly -a ACAS_PY_TERM_CODE_MAP=(")
        )
    except StopIteration as absent:  # pragma: no cover - asserted below
        raise AssertionError(
            "harness/run_python_scenario.sh declares no ACAS_PY_TERM_CODE_MAP"
        ) from absent
    declared: dict[str, tuple[int, ...]] = {}
    for line in lines[start + 1 :]:
        if line.strip() == ")":
            break
        match = _SHELL_TERM_CODE_MAP.match(line)
        assert match, f"unreadable ACAS_PY_TERM_CODE_MAP entry: {line!r}"
        declared[match.group("operation")] = tuple(
            int(code) for code in match.group("codes").split()
        )
    return declared


def test_term_codes_match_the_runner_table() -> None:
    """The runner and the test seam admit exactly the same statuses.

    A code in one table and not the other is the drift this lock exists for: an
    operation the runner admits but the seam bands as a fault reports a real
    behavioural difference as a broken rig, and an operation the seam admits but the
    runner refuses can never reach it at all.
    """
    from_conftest = _declared_term_codes_from_conftest()
    from_runner = _declared_term_codes_from_runner()

    assert from_runner, "the runner's term-code table parsed as empty"
    assert set(from_runner) == set(from_conftest), (
        "the two tables name different operations:\n"
        f"  harness/run_python_scenario.sh: {sorted(from_runner)}\n"
        f"  tests/conftest.py            : {sorted(from_conftest)}"
    )
    disagreements = {
        operation: (from_runner[operation], from_conftest[operation])
        for operation in sorted(from_runner)
        if tuple(sorted(from_runner[operation]))
        != tuple(sorted(from_conftest[operation]))
    }
    assert not disagreements, (
        "these operations admit different statuses on the two sides "
        "(runner, conftest):\n  "
        + "\n  ".join(f"{name}: {pair}" for name, pair in disagreements.items())
    )


def test_only_three_term_codes_exist_and_they_are_the_frozen_ones() -> None:
    """The whole admitted set is `{5, 8}`, held by three frozen `MOVE` statements.

    Stated as its own assertion so that ADDING a term code is a deliberate act with a
    frozen citation behind it, rather than a table entry nobody reviews. `gl070` sets
    5; `sl055` and `pl055` each set 8; the other four operations set none.
    """
    from_runner = _declared_term_codes_from_runner()
    assert from_runner["gl_post_cycle"] == (5,)
    assert from_runner["sl_invoice_post"] == (8,)
    assert from_runner["pl_order_post"] == (8,)
    for operation in (
        "gl_end_of_cycle",
        "sl_cash_post",
        "pl_payment_post",
        "irs_post",
    ):
        assert from_runner[operation] == (), (
            f"{operation} declares a term code. No frozen program on that route sets "
            f"one, so zero is its only semantic status; admitting another would let a "
            f"fault be attested as a measured difference."
        )
    everything = {code for codes in from_runner.values() for code in codes}
    assert everything == {5, 8}, (
        f"the admitted non-zero set is {sorted(everything)} and the frozen cycle sets "
        f"only 5 and 8 -- [general/gl070.cbl:L289], [sales/sl055.cbl:L344], "
        f"[purchase/pl055.cbl:L286]."
    )


# ---------------------------------------------------------------------------
#  MJ-17 - ONE DUPLICATE-REJECTING SCENARIO PARSER, AND NO OTHER
#
#  `yaml.safe_load` applies last-one-wins to a repeated mapping key, silently. A
#  scenario definition carries the destructive answers (`irs_clear_postings`,
#  `gl080_proceed`, `disk_change_option`), the three-state fan-out switch that decides
#  which tables a run touches, the `affected_tables` list the runners assert against
#  and the `expected_status` that makes a term code a PASS. A shadowed key therefore
#  means one consumer reads the value the file appears to state and another reads a
#  different one, and an empty diff drawn across that pair measures nothing.
#
#  Eight call sites parsed definitions that way. All of them now go through
#  `harness/scenario_yaml.py`, and these tests assert both halves: the loader rejects a
#  duplicate, and no consumer has quietly gone back to `yaml.safe_load`.
_SCENARIO_YAML_CONSUMERS: tuple[str, ...] = (
    "harness/seed.sh",
    "harness/run_parity.sh",
    "harness/dump_tables.py",
    "harness/diff_states.py",
    "harness/scenario_stream.py",
    "harness/make_fixtures.py",
    "tests/conftest.py",
)


def _scenario_yaml_module():
    """Load `harness/scenario_yaml.py` by explicit path (rule R-1).

    Returns:
        The executed module.
    """
    root = Path(__file__).resolve().parents[2]
    path = root / "harness" / "scenario_yaml.py"
    assert path.is_file(), f"the shared scenario parser is absent: {path}"
    spec = importlib.util.spec_from_file_location("acas_scenario_yaml_probe", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_shared_loader_rejects_a_duplicate_key() -> None:
    """A repeated mapping key is a parse failure naming the key.

    The DISCRIMINATING half of this pair: a loader that merely subclassed
    `SafeLoader` without overriding `construct_mapping` would pass every other
    assertion here and still silently drop the shadowed value.
    """
    yaml = pytest.importorskip("yaml")
    module = _scenario_yaml_module()

    good = module.load_scenario_yaml("irs_instead: ' '\nexpected_status:\n  - 0\n")
    assert good == {"irs_instead": " ", "expected_status": [0]}

    with pytest.raises(yaml.YAMLError) as caught:
        module.load_scenario_yaml("irs_clear_postings: 'N'\nirs_clear_postings: 'Y'\n")
    assert "DUPLICATE KEY" in str(caught.value)
    assert "irs_clear_postings" in str(caught.value)

    # A duplicate NESTED inside a mapping is refused too, since the destructive
    # answers and the seed records both live under nested keys.
    with pytest.raises(yaml.YAMLError):
        module.load_scenario_yaml("seed_records:\n  batch.dat: [1]\n  batch.dat: [2]\n")

    # And it is still a SAFE loader: an arbitrary Python tag must not construct.
    with pytest.raises(yaml.YAMLError):
        module.load_scenario_yaml("!!python/object/apply:os.system ['true']\n")


def test_every_committed_scenario_parses_within_the_budgets() -> None:
    """The budgets admit every committed definition unchanged (finding SEC-07).

    Stated FIRST and separately from the refusal test, because this is the half that
    would make the hardening a regression. A budget derived from anything other than the
    measured maxima could reject a real scenario, and the failure would surface as a
    parity run that cannot start rather than as an obviously wrong limit.
    """
    root = Path(__file__).resolve().parents[2]
    module = _scenario_yaml_module()

    definitions = sorted((root / "harness" / "scenarios").glob("*.yaml"))
    assert definitions, "no scenario definition was found; this test would be vacuous"

    widest = 0
    for path in definitions:
        text = path.read_text(encoding="utf-8")
        widest = max(widest, len(text.encode("utf-8")))
        parsed = module.load_scenario_yaml(text)
        assert isinstance(parsed, dict) and parsed, (
            f"{path.name} did not parse to a non-empty mapping under the parse "
            "budgets, so a budget is rejecting a committed definition."
        )

    # Headroom, asserted rather than assumed: a budget that the committed set already
    # sits near is one edit away from rejecting a real file.
    assert widest * 4 <= module.MAX_DOCUMENT_BYTES, (
        f"the largest committed definition is {widest} bytes against a budget of "
        f"{module.MAX_DOCUMENT_BYTES}, which leaves under 4x headroom. Raise the "
        "budget rather than trimming a scenario."
    )


def test_the_shared_loader_refuses_an_over_budget_document() -> None:
    """Each parse budget refuses what it exists for, and an alias is refused outright.

    The DISCRIMINATING half: constants alone prove nothing, since a limit that is never
    consulted reads exactly like one that is. Every budget is driven past its bound here
    and the alias case is a real multiplicative-expansion document, not a token one.
    """
    yaml = pytest.importorskip("yaml")
    module = _scenario_yaml_module()

    # 1. Size, checked BEFORE the parser sees the text.
    oversized = "a: " + "x" * (module.MAX_DOCUMENT_BYTES + 1)
    with pytest.raises(module.ScenarioBudgetError) as size_error:
        module.load_scenario_yaml(oversized)
    assert "parse budget" in str(size_error.value)

    # 2. An alias, which is the multiplicative-expansion class. Refused, not counted.
    laughs = (
        'a: &anchor ["x","x","x","x","x","x","x","x","x"]\n'
        "b: [*anchor,*anchor,*anchor,*anchor,*anchor,*anchor,*anchor,*anchor,*anchor]\n"
        "c: [*anchor,*anchor,*anchor,*anchor,*anchor,*anchor,*anchor,*anchor,*anchor]\n"
    )
    with pytest.raises(module.ScenarioBudgetError) as alias_error:
        module.load_scenario_yaml(laughs)
    assert "ALIAS" in str(alias_error.value)

    # 3. Depth.
    deep = (
        "a:\n"
        + "".join("  " * level + "k:\n" for level in range(1, module.MAX_DEPTH + 4))
        + "  " * (module.MAX_DEPTH + 4)
        + "v"
    )
    with pytest.raises(module.ScenarioBudgetError) as depth_error:
        module.load_scenario_yaml(deep)
    assert "nests deeper" in str(depth_error.value)

    # 4. Node count.
    wide = "root: [" + ",".join(str(n) for n in range(module.MAX_NODES + 10)) + "]"
    with pytest.raises(module.ScenarioBudgetError) as node_error:
        module.load_scenario_yaml(wide)
    assert "nodes" in str(node_error.value)

    # Every budget rejection is a `yaml.YAMLError`, so the eight consumers -- all of
    # which already handle that -- report one with no change of their own.
    assert issubclass(module.ScenarioBudgetError, yaml.YAMLError)


def test_the_dictionary_reader_bounds_what_it_reads() -> None:
    """The dictionary read is bounded in size and depth, and still reads the artifact.

    Both halves in one test because they are one contract: the committed dictionary must
    load exactly as before, and a document that is oversized, deeper than the budget, or
    deep enough to exhaust the interpreter's own recursion limit must be refused as a
    named `DictionaryParseError` rather than crashing the reader (finding SEC-07).
    """
    import json
    import tempfile

    loader = importlib.import_module("acas_posting.dictionary.loader")

    # The real artifact, unchanged.
    document = loader.load_dictionary()
    assert document.entries, "the committed dictionary no longer loads"

    root = Path(__file__).resolve().parents[2]
    artifact = root / "data_dictionary" / "acas_posting_dictionary.json"
    measured = artifact.stat().st_size
    assert measured * 4 <= loader._MAX_DOCUMENT_BYTES, (
        f"the committed dictionary is {measured} bytes against a read budget of "
        f"{loader._MAX_DOCUMENT_BYTES}, which leaves under 4x headroom."
    )

    # The depth helper does not recurse, so it can bound a document too deep to walk
    # recursively. Asserted directly, since that is the property that makes it usable.
    assert not loader._document_depth_exceeds(json.loads(artifact.read_text()), 64)
    assert loader._document_depth_exceeds(json.loads("[" * 200 + "]" * 200), 64)

    with tempfile.TemporaryDirectory() as directory:
        scratch = Path(directory)

        oversized = scratch / "oversized.json"
        oversized.write_bytes(
            b'{"x":"' + b"a" * (loader._MAX_DOCUMENT_BYTES + 16) + b'"}'
        )
        with pytest.raises(loader.DictionaryParseError) as size_error:
            loader.load_dictionary(oversized)
        assert "read budget" in str(size_error.value)

        # Deeper than the budget, but shallow enough that `json.loads` itself succeeds --
        # so this exercises the post-parse bound rather than the recursion guard.
        over_depth = scratch / "deep.json"
        over_depth.write_text('{"a":' * 100 + "1" + "}" * 100, encoding="utf-8")
        with pytest.raises(loader.DictionaryParseError) as depth_error:
            loader.load_dictionary(over_depth)
        assert "nests deeper" in str(depth_error.value)

        # Deep enough that the JSON scanner exhausts the recursion limit. Without the
        # guard this leaves the reader as a bare RecursionError.
        recursive = scratch / "recursive.json"
        recursive.write_text("[" * 100_000 + "]" * 100_000, encoding="utf-8")
        with pytest.raises(loader.DictionaryParseError) as recursion_error:
            loader.load_dictionary(recursive)
        assert "too deeply" in str(recursion_error.value)


def test_no_artifact_recommends_an_unhashed_install() -> None:
    """Install guidance names the hash-verified route, never a bare `pip install` (DEP-02).

    A `pip install <name>==<version>` in remediation text teaches the reader to fetch an
    unverified artifact, which is exactly the route the rest of this project refuses. The
    editable routes are permitted where they are labelled as development conveniences,
    so what is banned is an unqualified install of a PINNED DISTRIBUTION.
    """
    root = Path(__file__).resolve().parents[2]
    checked = (
        "pyproject.toml",
        "requirements.txt",
        "README-python-migration.md",
        "harness/run_cobol_scenario.sh",
        "harness/Dockerfile.gnucobol",
    )

    # `pip install name==version` with no --require-hashes on the same line.
    unhashed = re.compile(r"pip install(?![^\n]*--require-hashes)[^\n]*[A-Za-z0-9_.-]+==")

    offenders: list[str] = []
    for relative in checked:
        path = root / relative
        assert path.is_file(), f"a checked artifact is absent: {path}"
        for number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if unhashed.search(line):
                offenders.append(f"{relative}:{number}: {line.strip()[:96]}")

    assert not offenders, (
        "these lines recommend installing a pinned distribution without hash "
        "verification, which is the DEP-02 defect:\n  " + "\n  ".join(offenders) + "\n"
        "  Point at `pip install --require-hashes -r requirements.txt` instead."
    )


def test_every_scenario_yaml_consumer_uses_the_shared_loader() -> None:
    """No consumer calls `yaml.safe_load` on a scenario definition.

    Read as TEXT rather than by import, because three of the seven consumers are shell
    scripts whose parsing happens inside an embedded Python heredoc, and one is
    `tests/conftest.py`, which this tier must not import at module scope.
    """
    root = Path(__file__).resolve().parents[2]
    offenders: list[str] = []
    missing: list[str] = []
    for relative in _SCENARIO_YAML_CONSUMERS:
        path = root / relative
        assert path.is_file(), f"a declared consumer is absent: {path}"
        text = path.read_text(encoding="utf-8")
        if "load_scenario_yaml" not in text:
            missing.append(relative)
        if relative.endswith(".py"):
            # AST rather than text, so that PROSE naming the defect - a docstring
            # explaining why the shared loader exists - is not itself reported as the
            # defect. Every real use is an attribute access, whether called directly
            # or bound to a name first, so walking Attribute nodes catches both.
            for node in ast.walk(ast.parse(text, filename=str(path))):
                if (
                    isinstance(node, ast.Attribute)
                    and node.attr in ("safe_load", "safe_load_all")
                    and isinstance(node.value, ast.Name)
                    and node.value.id == "yaml"
                ):
                    offenders.append(f"{relative}:{node.lineno}: yaml.{node.attr}")
            continue
        # A shell script has no docstring, and its Python lives in a heredoc the shell
        # never parses, so a text scan is both sufficient and the only option.
        for number, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if "yaml.safe_load" in line:
                offenders.append(f"{relative}:{number}: {stripped}")

    assert not missing, (
        "these scenario-definition consumers do not reference the shared "
        "duplicate-rejecting loader at all:\n  " + "\n  ".join(missing)
    )
    assert not offenders, (
        "these lines call `yaml.safe_load`, whose last-one-wins on a duplicate key "
        "is the defect finding MJ-17 names:\n  " + "\n  ".join(offenders) + "\n\n"
        "  Parse scenario definitions through harness/scenario_yaml.py's "
        "`load_scenario_yaml` instead."
    )


# ---------------------------------------------------------------------------
#  MJ-17, SECOND HALF - A CONSUMER MUST RESOLVE THE SHARED PARSER BY ITSELF
#
#  Wiring every consumer to `harness/scenario_yaml.py` fixed the last-one-wins defect
#  and introduced a quieter one. `scenario_yaml` is a SIBLING FILE, not an installed
#  package, so `import scenario_yaml` resolves only when something has already put
#  `harness/` on `sys.path` - true when the consumer runs as a script from that
#  directory, false when a test loads it by path. The import was therefore
#  ORDER-DEPENDENT, and `diff_states.py` reported the failure as "PyYAML is not
#  importable", which is a different fault with a different remedy, so the refusal that
#  should have followed was never produced.
#
#  What that cost, measured: `pytest tests/scenarios/` on its own failed TWELVE tests
#  while the whole suite passed, because in the whole suite an earlier module both
#  inserted the path and left `scenario_yaml` in `sys.modules` for the bare import to
#  find in cache. A green full suite was therefore not evidence, and these two tests
#  exist so that it is: the first refuses the pattern statically, the second reproduces
#  the exact masking conditions - no `harness/` on the path AND no cached module - and
#  requires a real scenario read to still succeed.
_HARNESS_SIBLING_SELF_RESOLVERS: tuple[str, ...] = (
    "diff_states",
    "dump_tables",
)


def _harness_module_names(root: Path) -> frozenset[str]:
    """Every module name that is resolvable as a `harness/` sibling.

    Args:
        root: The repository root.

    Returns:
        The importable stems of the harness modules.
    """
    return frozenset(path.stem for path in (root / "harness").glob("*.py"))


def test_no_harness_module_resolves_a_sibling_by_name_unguarded() -> None:
    """A by-name sibling import must be guarded by the module's own path insert.

    Two shapes are acceptable and one is not. Resolving the sibling from
    `Path(__file__)` is acceptable and mutates nothing. Importing it by name after
    inserting the module's own directory on `sys.path` is acceptable because the
    guarantee is self-contained. Importing it by name with neither is the
    order-dependent defect, and it passes for as long as some other module happens to
    run first.
    """
    root = Path(__file__).resolve().parents[2]
    siblings = _harness_module_names(root)
    assert {"scenario_yaml", "diff_states", "dump_tables"} <= siblings, (
        "the harness module inventory is not what this test was written against; "
        f"found {sorted(siblings)}"
    )

    unguarded: list[str] = []
    for path in sorted((root / "harness").glob("*.py")):
        text = path.read_text(encoding="utf-8")
        # A guard is a `sys.path` insert derived from THIS module's own location.
        # `__file__` on the same statement is what makes it self-contained; an insert
        # of some other directory would not be.
        guards_itself = any(
            "sys.path.insert" in line and "__file__" in line
            for line in text.splitlines()
        )
        for node in ast.walk(ast.parse(text, filename=str(path))):
            imported: list[str] = []
            if isinstance(node, ast.Import):
                imported = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                imported = [node.module.split(".")[0]]
            for name in imported:
                if name in siblings and name != path.stem and not guards_itself:
                    unguarded.append(
                        f"harness/{path.name}:{node.lineno}: import {name}"
                    )

    assert not unguarded, (
        "these imports resolve a `harness/` sibling BY NAME without the importing "
        "module guaranteeing its own `sys.path`, so whether they resolve depends on "
        "what ran first:\n  " + "\n  ".join(unguarded) + "\n\n"
        "  Resolve the sibling from `Path(__file__).resolve().parent` instead, as "
        "harness/diff_states.py and harness/dump_tables.py do, or insert this "
        "module's own directory on `sys.path` before the import."
    )


@pytest.mark.parametrize("module_name", _HARNESS_SIBLING_SELF_RESOLVERS)
def test_a_scenario_reads_with_harness_off_the_path_and_out_of_cache(
    module_name: str,
) -> None:
    """The DISCRIMINATING half: reproduce both masking conditions, then read.

    The static test above cannot see a resolution that succeeds from the
    `sys.modules` cache, and cache is half of why this hid: a bare `import
    scenario_yaml` finds an already-imported module even with nothing on the path. So
    this test removes `harness/` from `sys.path` AND evicts every cached spelling of
    the parser, which is the state `pytest tests/scenarios/` runs in, and then requires
    a real scenario definition to still parse.

    Args:
        module_name: The harness module under test.
    """
    pytest.importorskip("yaml")
    root = Path(__file__).resolve().parents[2]
    harness = (root / "harness").resolve()
    scenario = harness / "scenarios" / "clean_batch_gl.yaml"
    assert scenario.is_file(), f"the scenario definition is absent: {scenario}"

    saved_path = list(sys.path)
    saved_modules = {
        name: module
        for name, module in sys.modules.items()
        if name == "scenario_yaml" or name.endswith("_scenario_yaml")
    }
    try:
        kept: list[str] = []
        for entry in sys.path:
            try:
                same = Path(entry or ".").resolve() == harness
            except OSError:  # pragma: no cover - unresolvable entry
                same = False
            if not same:
                kept.append(entry)
        sys.path[:] = kept
        for name in saved_modules:
            sys.modules.pop(name, None)

        probe = f"acas_sibling_probe_{module_name}"
        spec = importlib.util.spec_from_file_location(
            probe, harness / f"{module_name}.py"
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[probe] = module
        try:
            spec.loader.exec_module(module)
            tables = module.scenario_tables(scenario)
        finally:
            sys.modules.pop(probe, None)
    finally:
        sys.path[:] = saved_path
        sys.modules.update(saved_modules)

    assert tables, (
        f"harness/{module_name}.py read no tables from {scenario.name} with "
        f"harness/ off sys.path. Before this was fixed the refusal blamed PyYAML, "
        f"which is why the real cause went unnoticed."
    )
    assert "GLBATCH-REC" in tables, (
        f"harness/{module_name}.py parsed {scenario.name} but did not return its "
        f"declared tables; got {tables}"
    )


# ---------------------------------------------------------------------------
#  MJ-19 - EVERY KEYSTROKE A SCENARIO SUPPLIES IS ESCAPED AT THE PLAN BOUNDARY
#
#  The pty driver's `decode_send` expands `\r`, `\n`, `\e`, `\t` and `\\` anywhere in a
#  plan row's send field. That is correct for the terminator the runner appends and
#  wrong for the scenario value it is appended to: a backslash in scenario text would
#  be read as the start of a control sequence, so `run_date_text: 01\r02\r2025` would
#  be typed at the compiled program as three ENTER-terminated fields.
#
#  The parity consequence is the reason this is locked. The migrated leg receives
#  scenario values as argv - no escape layer - so a value the oracle leg reinterpreted
#  and the migrated leg took literally means the two legs were driven with DIFFERENT
#  logical inputs, and the diff measures the escape layer rather than the accounting.
#
#  Every send field that interpolates anything must therefore pass it through
#  `acas_plan_escape_data`. Asserted statically, because the validation that currently
#  keeps these values backslash-free sits hundreds of lines from the send site.
_PLAN_SEND_ARGUMENT = re.compile(r'"\$\{?ACAS_[A-Za-z0-9_]+\}?\\\\[rnet]"')


def test_every_scenario_supplied_keystroke_is_escaped() -> None:
    """No plan send field interpolates a variable without the escaping helper."""
    root = Path(__file__).resolve().parents[2]
    path = root / "harness" / "run_cobol_scenario.sh"
    text = path.read_text(encoding="utf-8")

    assert "acas_plan_escape_data()" in text, (
        "harness/run_cobol_scenario.sh no longer defines acas_plan_escape_data, the "
        "boundary between trusted plan controls and untrusted scenario data (MJ-19)."
    )

    raw: list[str] = []
    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if _PLAN_SEND_ARGUMENT.search(line):
            raw.append(f"{path.name}:{number}: {stripped}")

    assert not raw, (
        "these plan send fields interpolate a variable directly, so a backslash in "
        "the value would be expanded by decode_send into a control sequence and the "
        "two parity legs would receive different bytes (MJ-19):\n  "
        + "\n  ".join(raw)
        + '\n\n  Wrap the value: "$(acas_plan_escape_data "$VAR")\\\\r"'
    )

    # And the escaping is actually REACHED - at least once per scenario-supplied
    # keystroke this runner types. A helper defined and never called would satisfy
    # every assertion above.
    assert text.count('acas_plan_escape_data "') >= 4, (
        "acas_plan_escape_data is defined but reaches fewer send sites than the "
        "runner has scenario-supplied keystrokes (date text, two payment "
        "confirmations, the IRS clear answer)."
    )


def test_the_escape_boundary_round_trips_every_byte() -> None:
    """`acas_plan_escape_data` then `decode_send` is the identity on the data.

    The DISCRIMINATING half: it reimplements both halves of the boundary from the
    shell and the driver source respectively and asserts the composition returns the
    input unchanged, with the appended terminator as the ONLY control byte. Text
    containing `\\r` is the case the old code got wrong.
    """
    root = Path(__file__).resolve().parents[2]
    script = root / "harness" / "run_cobol_scenario.sh"
    text = script.read_text(encoding="utf-8")

    # decode_send, lifted from the driver heredoc so the test cannot drift from it.
    start = text.index("def decode_send(spec):")
    end = text.index("class Rule(object):", start)
    namespace: dict[str, Any] = {}
    exec(compile(textwrap.dedent(text[start:end]), "<decode_send>", "exec"), namespace)
    decode_send = namespace["decode_send"]

    def escape(value: str) -> str:
        """`acas_plan_escape_data`: `${raw//\\/\\\\}`."""
        return value.replace("\\", "\\\\")

    for data in (
        "21/09/2025",
        "2025/09/21",
        "Y",
        "N",
        "YES",
        "NO",
        "",
        r"01\r02\r2025",
        r"a\\b",
        r"\e[1m",
        r"\t\n",
        "\\",
    ):
        got = decode_send(escape(data) + "\\r")
        assert got == data.encode("utf-8") + b"\r", (
            f"the escape boundary is not byte-transparent for {data!r}: the compiled "
            f"leg would be typed {got!r} while the migrated leg receives {data!r} as "
            "argv, so the two legs would not share one logical input (MJ-19)."
        )

    # Proof the escaping is what achieves it: unescaped, the CR-bearing case really
    # does become three ENTER-terminated fields.
    unescaped = decode_send(r"01\r02\r2025" + "\\r")
    assert unescaped.count(b"\r") == 3, (
        "this test no longer demonstrates the defect it locks; decode_send's escape "
        "table may have changed."
    )


# ---------------------------------------------------------------------------
#  MN-09 - NO DIAGNOSTIC LOSES ITS TAIL TO A MISSING LINE CONTINUATION
#
#  A multi-line `acas_die` argument list is held together by trailing backslashes. Drop
#  one and the command ENDS there: the remaining quoted lines become a fresh command
#  whose name is the concatenation of those strings. Because `acas_die` exits, that
#  command never runs, so the advice in it is simply never printed - and the sentences
#  most likely to be lost this way are the ones appended last, which is to say the ones
#  telling an operator how to recover.
#
#  `bash -n` does not catch it: the result is syntactically valid. shellcheck does not
#  either, since a bare word command is legal. It is only visible by looking at where
#  an argument list stops relative to what follows it, which is what this does.
_DIAGNOSTIC_COMMAND = re.compile(
    r"^\s*(acas_(?:[a-z_]*_)?(?:die|note|warn|log|ok)|acas_refuse_target)\b"
)


def test_no_diagnostic_argument_list_is_broken_by_a_missing_continuation() -> None:
    """Every multi-line harness diagnostic keeps its whole argument list."""
    root = Path(__file__).resolve().parents[2]
    scripts = sorted((root / "harness").glob("*.sh"))
    assert scripts, "no harness shell scripts were found to check"

    broken: list[str] = []
    for path in scripts:
        lines = path.read_text(encoding="utf-8").splitlines()
        index = 0
        while index < len(lines):
            match = _DIAGNOSTIC_COMMAND.match(lines[index])
            if not (match and lines[index].rstrip().endswith("\\")):
                index += 1
                continue
            # Walk to the last continued line of this argument list.
            last = index
            while last < len(lines) - 1 and lines[last].rstrip().endswith("\\"):
                last += 1
            # The next non-blank line: an indented quoted string there means the list
            # stopped early and the remainder became an unreachable command.
            following = last + 1
            while following < len(lines) and not lines[following].strip():
                following += 1
            if following < len(lines) and re.match(r"^\s{2,}['\"]", lines[following]):
                broken.append(
                    f"{path.name}:{following + 1}: orphaned after "
                    f"{match.group(1)} at line {index + 1}\n"
                    f"      last argument: {lines[last].strip()[:78]}\n"
                    f"      orphaned     : {lines[following].strip()[:78]}"
                )
            index = last + 1

    assert not broken, (
        "these diagnostic argument lists end before the quoted lines that follow "
        "them, so that text becomes an unreachable command and its advice is never "
        "printed (MN-09):\n  " + "\n  ".join(broken) + "\n\n"
        "  Add the missing trailing backslash, or merge the text into the call."
    )


# ---------------------------------------------------------------------------
#  MJ-16 / MJ-10 - THE END-OF-CYCLE DESTRUCTIVE ANSWERS
#
#  MJ-16: `acas_posting/cli/args.py` carries an explicit-intent gate. `require_stated`
#  refuses to run until each destructive answer has been STATED, and
#  `stated_explicitly` decides that by asking whether the option was PRESENT ON THE
#  COMMAND LINE. The Python runner then composed `--run-confirmed` and
#  `--disk-change-option <v>` onto argv unconditionally, sourcing the value from its
#  own default when the scenario omitted it - so an omission arrived at the entry
#  point indistinguishable from a deliberate instruction, and the one component whose
#  job is to refuse un-stated consent was told consent had been given.
#
#  MJ-10: the oracle leg listed `disk_change_option` and `archive_path_override` among
#  its known keys and read NEITHER, hard-coding `0`. A scenario declaring `9` was
#  accepted, honoured by the migrated leg and contradicted by the compiled one.
#
#  Both are locked here as SOURCE properties, because the behaviour they concern is
#  reachable only with a live oracle and the defect is visible without one.
_GL080_RUNNERS = ("harness/run_python_scenario.sh", "harness/run_cobol_scenario.sh")


def test_neither_end_of_cycle_answer_can_be_defaulted() -> None:
    """No runner supplies `gl080_proceed` or `disk_change_option` on the scenario's behalf.

    The DISCRIMINATING assertion is the `_default` one: a runner that read the key
    but fell back to `'Y'` or `'0'` would still pass a mere "is the key mentioned"
    check, and would still launder a silent omission into stated consent.
    """
    root = Path(__file__).resolve().parents[2]
    offenders: list[str] = []
    for relative in _GL080_RUNNERS:
        path = root / relative
        text = path.read_text(encoding="utf-8")
        for number, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            for key in ("gl080_proceed", "disk_change_option"):
                # `<something>_default <key> '<value>'` is the laundering shape.
                if re.search(rf"_default\s+{key}\s+'", line):
                    offenders.append(f"{relative}:{number}: {stripped[:96]}")
    assert not offenders, (
        "these lines default a DESTRUCTIVE end-of-cycle answer, which the runner then "
        "passes as an option and the entry point reads as consent explicitly stated "
        "(MJ-16):\n  " + "\n  ".join(offenders) + "\n\n"
        "  Read the key without a fallback and refuse when it is absent."
    )

    # And the refusal must actually be there - a key read without a fallback and
    # without a refusal would simply run with an empty answer.
    for relative in _GL080_RUNNERS:
        text = (root / relative).read_text(encoding="utf-8")
        for key in ("gl080_proceed", "disk_change_option"):
            assert re.search(rf"does not declare {key}", text), (
                f"{relative} does not refuse a scenario that omits {key}; without "
                "the refusal, removing the default just substitutes an empty answer "
                "for an invented one (MJ-16)."
            )


def test_the_oracle_leg_reads_the_disk_change_answer_it_types() -> None:
    """The compiled leg drives the declared option rather than a hard-coded one (MJ-10)."""
    root = Path(__file__).resolve().parents[2]
    text = (root / "harness" / "run_cobol_scenario.sh").read_text(encoding="utf-8")

    assert re.search(r"ACAS_RUN_DISK_CHANGE=\"\$\(acas_scenario_scalar disk_change_option\)\"", text), (
        "harness/run_cobol_scenario.sh does not READ disk_change_option. It listed the "
        "key among those it accepts while ignoring it, so a scenario declaring 9 was "
        "driven as 0 on this leg and as 9 on the other (MJ-10)."
    )
    # The GL084 step must send the READ value, not a literal.
    assert not re.search(r"'gl080-archive' react 'GL084' '0", text), (
        "the GL084 plan step still hard-codes 0, so the two legs can be driven with "
        "different disk-change answers (MJ-10)."
    )
    assert re.search(r"'gl080-archive' react 'GL084'", text) and re.search(
        r'acas_plan_escape_data "\$ACAS_RUN_DISK_CHANGE"', text
    ), "the GL084 step no longer sends the declared value through the escape boundary."

    # The second prompt - which this plan had no step for at all - must be answered.
    assert "'gl080-archive-path'" in text and "Current path/name is" in text, (
        "the plan has no step for the archive-path accept at "
        "[general/gl080.cbl:L555]. Answering GL084 falls through to it, so without a "
        "step the run would stall there and report a pty timeout rather than the "
        "missing step it actually is (MJ-10)."
    )


def test_inputs_with_no_oracle_counterpart_are_refused_by_both_legs() -> None:
    """Neither leg accepts an input the other cannot reproduce (MJ-10).

    Asymmetry here is the whole defect: one leg honouring an input the other cannot
    means the two were driven differently, and the diff then measures the harness.
    """
    root = Path(__file__).resolve().parents[2]
    for relative in _GL080_RUNNERS:
        text = (root / relative).read_text(encoding="utf-8")
        assert "cannot be driven through this leg provably" in text or (
            "has no oracle counterpart" in text
        ), f"{relative} does not refuse the unsupported end-of-cycle inputs (MJ-10)."
        assert "archive_path_override" in text and re.search(
            r"archive_path_override (cannot be driven|has no oracle counterpart)", text
        ), f"{relative} still accepts archive_path_override (MJ-10)."
        # The open question must be NAMED, not gestured at, so the refusal is findable.
        assert "Q-GL084-ACCEPT-SEMANTICS" in text, (
            f"{relative} refuses these inputs without naming the open question that "
            "records why, so a reader cannot find the arbitration (R-5, R-6)."
        )

    register = (root / "docs" / "migration" / "ambiguity-resolutions.md").read_text(
        encoding="utf-8"
    )
    assert "Q-GL084-ACCEPT-SEMANTICS" in register, (
        "both runners cite Q-GL084-ACCEPT-SEMANTICS and the register does not carry "
        "it, so the citation dangles."
    )
    assert '<a id="q-gl084-accept-semantics"></a>' in register, (
        "the entry has no anchor, so a fragment citation to it cannot resolve."
    )


def test_no_scenario_declares_an_input_its_runners_refuse() -> None:
    """Every committed scenario is still runnable after the MJ-10/MJ-16 tightening."""
    yaml = pytest.importorskip("yaml")
    root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location(
        "acas_scenario_yaml_probe2", root / "harness" / "scenario_yaml.py"
    )
    assert spec is not None and spec.loader is not None
    loader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loader)

    scenarios = sorted((root / "harness" / "scenarios").glob("*.yaml"))
    assert scenarios, "no scenario definitions were found"

    problems: list[str] = []
    for path in scenarios:
        try:
            declared = loader.load_scenario_yaml(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:  # a duplicate key is MJ-17's business
            problems.append(f"{path.name}: does not parse: {exc}")
            continue
        operations = declared.get("operations") or []
        if isinstance(operations, str):
            operations = [operations]
        selects = "gl_end_of_cycle" in operations or (
            declared.get("operation") == "gl_end_of_cycle"
        )
        if declared.get("archive_path_override"):
            problems.append(
                f"{path.name}: declares archive_path_override, which both runners refuse"
            )
        if str(declared.get("disk_change_option") or "") == "9":
            problems.append(
                f"{path.name}: declares disk_change_option 9, which both runners refuse"
            )
        if selects:
            for key in ("gl080_proceed", "disk_change_option"):
                if not declared.get(key):
                    problems.append(
                        f"{path.name}: selects gl_end_of_cycle without declaring {key}, "
                        "which both runners now require"
                    )
    assert not problems, (
        "these committed scenarios can no longer be run by their own runners:\n  "
        + "\n  ".join(problems)
    )


# ---------------------------------------------------------------------------
#  DEP-01 / MJ-20 - THE DECLARED CLOSURE IS THE PLAN'S, AND THE IMPORTED SET IS
#  EXACTLY THE DRIVER
#
#  This section has been wrong in BOTH directions, and it now locks both.
#
#  MJ-20 was the first direction. `pyproject.toml` declared `SQLAlchemy`, `greenlet` and
#  `typing_extensions` as runtime dependencies, SQLAlchemy described as "CORE LEVEL ONLY:
#  text() statements on an explicit Connection"; `requirements.txt` pinned all three with
#  hashes; and the README documented that boundary as ACTIVE. No module under
#  `acas_posting/` imported any of them. The same file that declared them also stated,
#  correctly, that the package imports "exactly one third-party top-level module,
#  `mysql`". Three artifacts described an execution path the code did not take.
#
#  DEP-01 was the correction over-shooting. The response to MJ-20 deleted the three pins
#  from both manifests so that declared and imported coincided. That made the artifacts
#  self-consistent and made them NARROWER THAN THE FROZEN PLAN: AAP section 0.5.1 states
#  the runtime inventory as four names at exact versions -- mysql-connector-python
#  26.7.0, SQLAlchemy 2.0.51, and in its own words "Pulls `greenlet` 3.5.4 as a
#  transitive dependency", with typing_extensions travelling with it. The plan is the
#  agreed contract for what this distribution DECLARES and is not editable by the
#  implementation, so a manifest that drops one of its names diverges from it.
#
#  WHAT IS LOCKED, THEREFORE, IS THE PAIR AND NOT EITHER HALF:
#    * the DECLARED runtime closure is EXACTLY the plan's four names - no wider, so a
#      package cannot be smuggled into the shipped graph, and no narrower, so the plan
#      cannot be quietly re-written by deletion;
#    * the IMPORTED third-party set under `acas_posting/` is EXACTLY {mysql}, so the
#      execution path stays auditable from the source;
#    * the DIFFERENCE between them is exactly the three names the plan declares as the
#      alternative Core-level boundary, so a fourth declared-and-unimported package
#      cannot join them unnoticed;
#    * `requirements.txt` pins exactly the union of the manifest's sets, so the hashed
#      route the container and the parity protocol use installs neither more nor less;
#    * and no artifact describes the Core boundary as ACTIVE, which is the MJ-20 defect
#      itself and is a property of prose that no import census can see.
#
#  Declaring more than is imported is therefore permitted HERE AND ONLY HERE, only for
#  the names the plan itself declares, and only while every artifact says so in as many
#  words. That is what makes it an auditable decision rather than the drift MJ-20 found.
_PACKAGE_ROOT = "acas_posting"

#: Distribution name -> the top-level module it provides, for the runtime set. A
#: distribution whose import name differs from its package name needs an entry here.
_DISTRIBUTION_MODULES: Mapping[str, str] = MappingProxyType(
    {
        "mysql-connector-python": "mysql",
        "sqlalchemy": "sqlalchemy",
        "greenlet": "greenlet",
        "typing_extensions": "typing_extensions",
        "typing-extensions": "typing_extensions",
    }
)

#: The runtime closure AAP section 0.5.1 fixes, canonicalised the way pip canonicalises
#: a distribution name (lower-case, `_` and `.` folded to `-`). Changing this set means
#: claiming the plan says something different, so it is spelled out here rather than
#: derived from the manifest it is used to check.
_PLAN_RUNTIME_CLOSURE: Mapping[str, str] = MappingProxyType(
    {
        "mysql-connector-python": "26.7.0",
        "sqlalchemy": "2.0.51",
        "greenlet": "3.5.4",
        "typing-extensions": "4.16.0",
    }
)

#: The names the plan declares that the code deliberately does not import. Their
#: presence in the manifest is an auditable decision; a FOURTH name in this position
#: would be drift, so the tests pin the set rather than merely tolerating a non-empty
#: difference.
_DECLARED_AND_NOT_IMPORTED: frozenset[str] = frozenset(
    {"sqlalchemy", "greenlet", "typing-extensions"}
)

#: The one third-party top-level module the shipped package may import.
_IMPORTED_THIRD_PARTY_SET: frozenset[str] = frozenset({"mysql"})


def _canonical_distribution(name: str) -> str:
    """Canonicalise a distribution name the way pip does.

    Args:
        name: A distribution name as written in a manifest or a lock file.

    Returns:
        The name lower-cased with runs of `-`, `_` and `.` folded to a single `-`.
    """
    return re.sub(r"[-_.]+", "-", name.strip().lower())


def _declared_runtime_distributions() -> list[str]:
    """Return `pyproject.toml`'s `[project].dependencies`, names only.

    Returns:
        The canonicalised distribution names, in declaration order.
    """
    parsed = _parsed_manifest()
    declared = parsed["project"]["dependencies"]
    return [
        _canonical_distribution(re.split(r"[=<>!~\[;]", entry, maxsplit=1)[0])
        for entry in declared
    ]


def _parsed_manifest() -> dict[str, Any]:
    """Return `pyproject.toml`, parsed.

    Returns:
        The parsed manifest.
    """
    root = Path(__file__).resolve().parents[2]
    manifest = root / "pyproject.toml"
    assert manifest.is_file(), f"the manifest is absent: {manifest}"
    return tomllib.loads(manifest.read_text(encoding="utf-8"))


def _declared_runtime_pins() -> dict[str, str]:
    """Return `pyproject.toml`'s `[project].dependencies` as name -> pinned version.

    Returns:
        Canonical distribution name -> the exact version it is pinned to. An entry that
        is not pinned with `==` maps to the empty string, which the caller reports.
    """
    parsed = _parsed_manifest()
    pins: dict[str, str] = {}
    for entry in parsed["project"]["dependencies"]:
        name, separator, remainder = entry.partition("==")
        pins[_canonical_distribution(name)] = remainder.strip() if separator else ""
    return pins


def _imported_third_party_modules() -> dict[str, set[str]]:
    """Return the third-party top-level modules `acas_posting/` imports.

    Walks every module with `ast` rather than importing them, so the census is a
    property of the source rather than of what a particular run happened to load, and
    so a deferred import inside a function body is counted exactly like a top-level one.

    Returns:
        Top-level module name -> the files that import it.
    """
    root = Path(__file__).resolve().parents[2] / _PACKAGE_ROOT
    standard = set(sys.stdlib_module_names)
    found: dict[str, set[str]] = {}
    for path in sorted(root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module]
            else:
                continue
            for name in names:
                top = name.split(".")[0]
                if top in standard or top == _PACKAGE_ROOT:
                    continue
                found.setdefault(top, set()).add(path.name)
    return found


def test_the_declared_runtime_closure_is_exactly_the_plans_closure() -> None:
    """`[project].dependencies` is the plan's four names at the plan's versions (DEP-01).

    Both directions matter and for different reasons. A name the plan does not declare
    would put a package into the shipped dependency graph on no authority. A plan name
    that is missing would narrow the frozen closure by deletion, which is the defect
    DEP-01 records -- the response to MJ-20 removed three of these four.
    """
    declared = _declared_runtime_pins()

    extra = sorted(set(declared) - set(_PLAN_RUNTIME_CLOSURE))
    assert not extra, (
        "pyproject.toml declares these RUNTIME dependencies and AAP section 0.5.1's "
        f"dependency inventory does not name them: {', '.join(extra)}.\n"
        "  The plan fixes the runtime closure at "
        f"{', '.join(sorted(_PLAN_RUNTIME_CLOSURE))}. A package outside it belongs in "
        "an optional-dependency group, or nowhere."
    )

    missing = sorted(set(_PLAN_RUNTIME_CLOSURE) - set(declared))
    assert not missing, (
        "AAP section 0.5.1 declares these in the runtime dependency inventory and "
        f"pyproject.toml no longer does: {', '.join(missing)}.\n"
        "  This is finding DEP-01. The plan is FROZEN: aligning the manifest to it is "
        "the standing rule, and a name may not be dropped because nothing imports it. "
        "Declaring a name the code does not import is permitted for exactly "
        f"{', '.join(sorted(_DECLARED_AND_NOT_IMPORTED))} and is stated as such in "
        "pyproject.toml, requirements.txt and README-python-migration.md."
    )

    wrong = sorted(
        f"{name}: manifest {declared[name] or '(not pinned with ==)'}, "
        f"plan {_PLAN_RUNTIME_CLOSURE[name]}"
        for name in sorted(_PLAN_RUNTIME_CLOSURE)
        if name in declared and declared[name] != _PLAN_RUNTIME_CLOSURE[name]
    )
    assert not wrong, (
        "these runtime dependencies are not pinned to the version AAP section 0.5.1 "
        "states:\n  " + "\n  ".join(wrong) + "\n"
        "  Every version in section 0.5.1 was resolved rather than recalled, and a "
        "driver or runtime change can move a stored penny (R-6)."
    )


def test_the_imported_third_party_set_is_exactly_the_driver() -> None:
    """`acas_posting/` imports exactly one third-party module, `mysql` (MJ-20).

    This is the half MJ-20 was raised about, expressed positively. The manifest declares
    four names; the source may reach for only one of them, so that the execution path
    stays auditable from the source rather than inferred from the manifest.
    """
    imported = _imported_third_party_modules()
    observed = frozenset(imported)

    unexpected = sorted(
        f"{module} (imported by {', '.join(sorted(imported[module]))})"
        for module in observed - _IMPORTED_THIRD_PARTY_SET
    )
    assert not unexpected, (
        "acas_posting imports third-party modules beyond the one driver:\n  "
        + "\n  ".join(unexpected)
        + "\n  The shipped package's third-party surface is exactly "
        f"{{{', '.join(sorted(_IMPORTED_THIRD_PARTY_SET))}}}. In particular an "
        "`import sqlalchemy` here would take the Core-level data-access path the "
        "project deliberately does not take: acas_posting/dal/connection.py reproduces "
        "the frozen bridges' connection ownership, which an Engine is built to own "
        "instead, and re-routing it would change which physical session a statement "
        "runs on (R-4, R-6)."
    )

    absent = sorted(_IMPORTED_THIRD_PARTY_SET - observed)
    assert not absent, (
        f"acas_posting no longer imports {', '.join(absent)}. The database driver is "
        "the package's one third-party import; if it has genuinely gone, this census "
        "and every document describing it need re-stating, not this assertion relaxing."
    )


def test_the_declared_but_unimported_set_is_exactly_the_three_the_plan_declares() -> None:
    """Declaring-without-importing is confined to the plan's three names (DEP-01/MJ-20).

    The difference between the declared closure and the imported set is where MJ-20's
    drift lived. Leaving it merely "allowed to be non-empty" would let a fourth package
    settle there unnoticed, which is the same defect with a different name in it, so the
    set is pinned exactly.
    """
    declared = set(_declared_runtime_distributions())
    imported = _imported_third_party_modules()

    unmapped = sorted(name for name in declared if name not in _DISTRIBUTION_MODULES)
    assert not unmapped, (
        "these runtime dependencies have no entry in _DISTRIBUTION_MODULES, so this "
        f"census cannot say whether they are imported: {', '.join(unmapped)}. Add the "
        "distribution-to-module mapping rather than removing the assertion."
    )

    unused = {name for name in declared if _DISTRIBUTION_MODULES[name] not in imported}

    joined = sorted(unused - _DECLARED_AND_NOT_IMPORTED)
    assert not joined, (
        "these packages are declared as RUNTIME dependencies of acas_posting, no module "
        f"in the package imports them, and the plan does not declare them either: "
        f"{', '.join(joined)}.\n"
        "  A manifest that advertises an execution path the code does not take makes "
        "the shipped architecture unauditable from the artifact (MJ-20). Either use the "
        "package or stop declaring it -- and if it belongs to the harness or the test "
        "tooling, declare it in the matching optional-dependency group instead."
    )

    started_being_imported = sorted(_DECLARED_AND_NOT_IMPORTED - unused)
    assert not started_being_imported, (
        "these packages are recorded across pyproject.toml, requirements.txt, "
        "README-python-migration.md and harness/Dockerfile.gnucobol as DECLARED AND NOT "
        f"IMPORTED, and acas_posting now imports them: {', '.join(started_being_imported)}"
        ".\n  If that is intended it is a change of data-access architecture, not a "
        "test to relax: those four artifacts state the opposite, and "
        "test_no_document_claims_an_unused_data_access_boundary forbids describing the "
        "Core boundary as active while it is not taken."
    )


def test_every_imported_third_party_module_is_declared() -> None:
    """The package imports nothing it does not declare (MJ-20, the other direction).

    Without this half, satisfying the first would be as easy as deleting a needed pin:
    an install reproduced from the manifest would then fail at import instead.
    """
    declared = _declared_runtime_distributions()
    provided = {
        _DISTRIBUTION_MODULES[name]
        for name in declared
        if name in _DISTRIBUTION_MODULES
    }
    imported = _imported_third_party_modules()

    undeclared = sorted(
        f"{module} (imported by {', '.join(sorted(files))})"
        for module, files in imported.items()
        if module not in provided
    )
    assert not undeclared, (
        "acas_posting imports these third-party modules and pyproject.toml's "
        f"[project].dependencies declares none of them:\n  {chr(10).join(undeclared)}\n"
        "  An environment built from the manifest would fail at import (MJ-20)."
    )


def test_the_manifests_agree_on_the_runtime_set() -> None:
    """`requirements.txt` pins exactly the manifest's names, with no orphan (MJ-20).

    The lock file is what the container and the parity protocol install from, so it is
    the artifact that decides what actually lands in every environment that matters. A
    name pinned there and not declared in `pyproject.toml` would install silently; a name
    declared and not pinned would be missing from the one route that is hash-verified.
    Both are asserted, over the WHOLE manifest -- runtime, harness, dev and the build
    backend -- because a hashed install of this file installs all of them at once.
    """
    root = Path(__file__).resolve().parents[2]
    lock = (root / "requirements.txt").read_text(encoding="utf-8")

    pinned = {
        _canonical_distribution(match.group(1)): match.group(2)
        for match in re.finditer(
            r"^([A-Za-z][A-Za-z0-9_.-]*)==([^\s\\]+)", lock, re.MULTILINE
        )
    }

    parsed = _parsed_manifest()
    manifest_entries: list[str] = list(parsed["project"]["dependencies"])
    for group, entries in parsed["project"]["optional-dependencies"].items():
        for entry in entries:
            # The `test` group is defined BY REFERENCE (`acas-posting[dev,harness]`) so
            # the two sets can never drift apart; it names no distribution of its own.
            if _canonical_distribution(
                re.split(r"[=<>!~\[;]", entry, maxsplit=1)[0]
            ) == _canonical_distribution(parsed["project"]["name"]):
                continue
            manifest_entries.append(entry)
    manifest_entries.extend(parsed["build-system"]["requires"])

    declared_pins: dict[str, str] = {}
    for entry in manifest_entries:
        name, separator, remainder = entry.partition("==")
        declared_pins[_canonical_distribution(name)] = (
            remainder.strip() if separator else ""
        )

    missing = sorted(set(declared_pins) - set(pinned))
    assert not missing, (
        f"pyproject.toml declares {', '.join(missing)} and requirements.txt does not "
        "pin them, so the hash-verified route -- the one the container and the parity "
        "protocol use -- would not provide them."
    )

    orphans = sorted(set(pinned) - set(declared_pins))
    assert not orphans, (
        f"requirements.txt pins {', '.join(orphans)} and no group of pyproject.toml "
        "declares them. A hashed install would place them in the container and the "
        "parity environment while the manifest looked clean, which is how MJ-20's "
        "divergence survived in the first place."
    )

    disagreements = sorted(
        f"{name}: pyproject {declared_pins[name] or '(not pinned with ==)'}, "
        f"requirements.txt {pinned[name]}"
        for name in sorted(declared_pins)
        if declared_pins[name] != pinned[name]
    )
    assert not disagreements, (
        "these names are pinned to different versions in the two dependency "
        "artifacts:\n  " + "\n  ".join(disagreements) + "\n"
        "  A version that differs between them is a defect, not a variation: the two "
        "install routes would then produce different environments and only one of them "
        "could be the one parity evidence was taken on (R-6)."
    )


def test_every_pin_in_the_lock_is_hash_verified() -> None:
    """Every `requirements.txt` pin carries at least one `--hash`, so nothing floats.

    `pip install --require-hashes` refuses the whole file if ANY requirement lacks a
    hash, so a missing one does not weaken the install quietly -- it breaks the
    documented route outright, including the image build in
    `harness/Dockerfile.gnucobol`. Asserting it here names the offending pin instead.
    """
    root = Path(__file__).resolve().parents[2]
    text = (root / "requirements.txt").read_text(encoding="utf-8")

    # A requirement is its `name==version` line plus the continuation lines it joins
    # with a trailing backslash. Splitting on that keeps each pin with its own hashes.
    logical = re.sub(r"\\\n\s*", " ", text)
    unhashed = [
        match.group(1)
        for match in re.finditer(
            r"^([A-Za-z][A-Za-z0-9_.-]*==[^\s]+)([^\n]*)$", logical, re.MULTILINE
        )
        if "--hash=sha256:" not in match.group(2)
    ]
    assert not unhashed, (
        "these requirements.txt pins carry no --hash, which makes "
        "`pip install --require-hashes -r requirements.txt` refuse the entire file:\n  "
        + "\n  ".join(unhashed)
    )


def test_the_documented_pin_and_hash_counts_match_the_lock() -> None:
    """README section 7 quotes the pin and hash counts; both must be measured, not stale.

    This is the third symptom of DEP-01 specifically: when three pins were removed the
    documented figure was left behind, so the README described a 13-pin lock that had
    become a 10-pin lock. A count in prose is a claim about the tree, and this ties it
    to the tree so the next pin change cannot leave it behind again.
    """
    root = Path(__file__).resolve().parents[2]
    lock = (root / "requirements.txt").read_text(encoding="utf-8")
    readme_text = (root / "README-python-migration.md").read_text(encoding="utf-8")
    # The claim wraps across source lines, so compare against unwrapped text.
    readme = " ".join(readme_text.split())

    pins = len(set(re.findall(r"^([A-Za-z][A-Za-z0-9_.-]*)==", lock, re.MULTILINE)))
    hashes = lock.count("--hash=sha256:")

    quoted = re.search(r"\*\*(\d+) hashes across (\d+) pins\*\*", readme)
    assert quoted, (
        "README section 7 no longer states the pin and hash counts in the form "
        "'**<N> hashes across <M> pins**'. Restore the claim or update this test -- the "
        "install section is where a reader checks the lock is complete."
    )

    documented_hashes, documented_pins = int(quoted.group(1)), int(quoted.group(2))
    assert (documented_hashes, documented_pins) == (hashes, pins), (
        f"README section 7 documents {documented_hashes} hashes across "
        f"{documented_pins} pins; requirements.txt actually carries {hashes} hashes "
        f"across {pins} pins.\n"
        "  A stale count here is how DEP-01 presented: the prose kept describing the "
        "closure the lock used to have."
    )

    # The prose also spells the pin count as a word ("all thirteen pinned
    # distributions"), and a spelled count drifts just as silently as a digit.
    spelled = [
        word
        for word, value in _NUMBER_WORDS.items()
        if f"all {word} pinned distributions" in readme.lower() and value != pins
    ]
    assert not spelled, (
        f"README section 7 spells the pin count as {', '.join(spelled)} while "
        f"requirements.txt pins {pins} distributions."
    )


def test_no_document_claims_an_unused_data_access_boundary() -> None:
    """No artifact describes SQLAlchemy Core as the active boundary (MJ-20).

    Text rather than imports, because the defect was three documents describing an
    execution path the code did not take, and no import census can see prose. This
    survives DEP-01 unchanged in substance: restoring the pins restored what the
    manifests DECLARE, not what the code executes, so a document may say the name is
    declared and may quote what the plan contemplates -- and may not say the boundary is
    live. A sentence recording the decision is exempt; a sentence asserting the boundary
    is active is not.
    """
    root = Path(__file__).resolve().parents[2]
    # The ASSERTIVE forms only. A decision record has to be able to quote what the
    # plan says - AAP section 0.1.2's diagram label "SQLAlchemy Core / connector" is
    # itself an either/or and was never a claim in these files - so the patterns match
    # the shapes that actually asserted the boundary was live, not every mention of it.
    claims = (
        "sqlalchemy is used at",
        "used at core level only",
        "used at **core level only**",
        "used at CORE level only",
        "| **core level only**",
        "sqlalchemy core is",
    )
    # And a sentence that names a finding, or that states the declared-not-imported pair
    # in as many words, is the record of the decision rather than a claim.
    exempt = (
        "mj-20",
        "dep-01",
        "deliberately absent",
        "is absent from",
        "not imported",
        "does not take",
    )
    offenders: list[str] = []
    for relative in (
        "pyproject.toml",
        "requirements.txt",
        "README-python-migration.md",
    ):
        path = root / relative
        assert path.is_file(), f"a declared artifact is absent: {path}"
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            lowered = line.lower()
            if any(word in lowered for word in exempt):
                continue
            for claim in claims:
                if claim in lowered:
                    offenders.append(f"{relative}:{number}: {line.strip()[:96]}")
    assert not offenders, (
        "these lines describe a SQLAlchemy Core boundary as active, while no module in "
        "acas_posting imports SQLAlchemy at all (MJ-20):\n  " + "\n  ".join(offenders)
    )


def test_the_declared_and_unimported_decision_is_stated_in_every_artifact() -> None:
    """Every artifact that carries the three pins also says they are not imported.

    Declaring a package the code does not import is only auditable if the artifact says
    so. MJ-20 was exactly this omission: three artifacts carried the pins and none
    recorded that nothing imported them, so a reader could not tell the difference
    between a decision and a mistake. Restoring the pins under DEP-01 therefore restores
    the obligation to state the pair, and this test holds the two together.
    """
    root = Path(__file__).resolve().parents[2]
    # Each artifact must contain a phrase asserting the DECLARED / NOT IMPORTED pair. The
    # alternatives per file are wording variants of one statement, not different claims.
    required: Mapping[str, tuple[str, ...]] = MappingProxyType(
        {
            "pyproject.toml": ("declared here and is not imported",),
            "requirements.txt": ("declared is not the same as imported",),
            "README-python-migration.md": ("declared and is not imported",),
            "harness/Dockerfile.gnucobol": ("declared is not imported",),
        }
    )
    missing: list[str] = []
    for relative, phrases in required.items():
        path = root / relative
        assert path.is_file(), f"a declared artifact is absent: {path}"
        lowered = path.read_text(encoding="utf-8").lower()
        if not any(phrase in lowered for phrase in phrases):
            missing.append(f"{relative} (expected one of: {', '.join(phrases)})")
    assert not missing, (
        "these artifacts carry the SQLAlchemy pin, or assert on it, and none of them "
        "states that nothing imports it:\n  " + "\n  ".join(missing) + "\n"
        "  A declared-and-unimported dependency is an auditable decision only while "
        "every artifact says so; unstated, it is the MJ-20 drift again."
    )


# ---------------------------------------------------------------------------
#  SEC-04 - THE DATABASE SUPERUSER CREDENTIAL REACHES TWO STAGES OF TEN
#
#  `harness/docker-compose.yml` must declare ACAS_DB_ADMIN_USER / ACAS_DB_ADMIN_PASSWORD
#  at service level, because `run_parity.sh` drives all ten protocol stages from one
#  invocation and stages 1 and 5 - both `reset_db.sh` - drop and re-apply the frozen
#  schema. A service-level variable is inherited by every descendant, so that put the
#  superuser password into the environment of the GnuCOBOL compiler, the preSQL
#  translator, every bridge and menu binary, the migrated Python cycle and pytest.
#
#  Three independent mechanisms now remove it everywhere it is not needed, and the
#  tests below assert each one plus the CENSUS that makes all three safe.
# ---------------------------------------------------------------------------

#: The two names. Spelled here rather than imported, so the test would notice a rename
#: in either direction instead of following it silently.
_ADMIN_CREDENTIAL_NAMES: tuple[str, ...] = (
    "ACAS_DB_ADMIN_USER",
    "ACAS_DB_ADMIN_PASSWORD",
)

#: The harness scripts that perform NO schema administration. Each must drop the pair
#: at entry, so a direct invocation is scoped just as a driven one is.
_NON_ADMINISTRATIVE_SCRIPTS: tuple[str, ...] = (
    "harness/build_oracle.sh",
    "harness/build_fixtures.sh",
    "harness/run_cobol_scenario.sh",
    "harness/run_python_scenario.sh",
)

#: The only two scripts that legitimately consume the credential.
_ADMINISTRATIVE_SCRIPTS: tuple[str, ...] = ("harness/reset_db.sh", "harness/seed.sh")


def test_only_the_administrative_scripts_consume_the_credential() -> None:
    """THE CENSUS THAT MAKES THE SCRUB SAFE, and that would notice it stopping to be.

    Removing a variable from a child's environment is only correct while no child needs
    it. So rather than trusting that, this counts actual references: the pair may be
    consumed by the two schema-administration scripts and named in documentation
    anywhere, but a NON-administrative script that started reading it would mean the
    scrub had begun breaking something - and this test is how that surfaces, instead of
    as a confusing authentication failure inside a stage.
    """
    root = Path(__file__).resolve().parents[2]

    for relative in _ADMINISTRATIVE_SCRIPTS:
        text = (root / relative).read_text(encoding="utf-8")
        assert any(name in text for name in _ADMIN_CREDENTIAL_NAMES), (
            f"{relative} no longer references the administrative credential at all. "
            "If schema administration has moved elsewhere, the scrub lists in this "
            "module and in run_parity.sh have to move with it."
        )

    offenders: list[str] = []
    for relative in _NON_ADMINISTRATIVE_SCRIPTS:
        path = root / relative
        assert path.is_file(), f"a declared script is absent: {path}"
        for number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            stripped = line.strip()
            # A comment may name it - the scrub block itself does - and the `unset`
            # is the point of this whole exercise.
            if stripped.startswith("#") or stripped.startswith("unset "):
                continue
            if any(name in line for name in _ADMIN_CREDENTIAL_NAMES):
                offenders.append(f"{relative}:{number}: {stripped[:80]}")

    assert not offenders, (
        "these scripts are declared non-administrative and drop the superuser "
        "credential at entry, yet they now READ it, so they cannot work:\n  "
        + "\n  ".join(offenders)
        + "\n  Either the reference is wrong, or the script has become administrative "
        "and must be moved out of the scrub list deliberately."
    )


def test_every_non_administrative_script_drops_the_credential_at_entry() -> None:
    """Mechanism 2: the pair is gone before the script's first child exists.

    Asserted as ordering, not just presence: an `unset` placed after the first
    subprocess would leave exactly the exposure it is meant to close. `set -Eeuo
    pipefail` is used as the marker for "the script has started", and the `unset` must
    come within the header rather than somewhere down in a function.
    """
    root = Path(__file__).resolve().parents[2]
    problems: list[str] = []

    for relative in _NON_ADMINISTRATIVE_SCRIPTS:
        lines = (root / relative).read_text(encoding="utf-8").splitlines()
        unset_at = next(
            (
                number
                for number, line in enumerate(lines, start=1)
                if line.strip().startswith("unset ")
                and all(name in line for name in _ADMIN_CREDENTIAL_NAMES)
            ),
            None,
        )
        if unset_at is None:
            problems.append(
                f"{relative}: never unsets {' and '.join(_ADMIN_CREDENTIAL_NAMES)}"
            )
            continue
        # It must be in the script's header, before any function body or command that
        # could spawn something.
        first_function = next(
            (
                number
                for number, line in enumerate(lines, start=1)
                if re.match(r"^[A-Za-z_][A-Za-z0-9_]*\(\)\s*\{", line)
            ),
            len(lines),
        )
        if unset_at > first_function:
            problems.append(
                f"{relative}: unsets the pair at line {unset_at}, AFTER the first "
                f"function at line {first_function} - too late to be a guarantee"
            )

    assert not problems, (
        "the administrative credential is not dropped early enough to be a guarantee "
        "(finding SEC-04):\n  " + "\n  ".join(problems)
    )


def test_the_parity_driver_scopes_the_credential_to_the_reset_stages() -> None:
    """Mechanism 1: only stages 1 and 5 keep the pair; the other eight run without it."""
    root = Path(__file__).resolve().parents[2]
    driver = (root / "harness" / "run_parity.sh").read_text(encoding="utf-8")

    expected = "env -u ACAS_DB_ADMIN_USER -u ACAS_DB_ADMIN_PASSWORD"
    assert expected in driver, (
        "harness/run_parity.sh no longer strips the administrative credential from a "
        f"stage's environment; expected the scrub {expected!r}. Without it every stage "
        "inherits the database superuser password from the service environment."
    )
    assert "1|5)" in driver, (
        "harness/run_parity.sh no longer distinguishes the two administrative stages, "
        "so either every stage now gets the credential or the two resets have lost it."
    )
    # And it must be applied where the stage is actually executed, not merely defined.
    assert '"${scrub[@]}" "${ACAS_PARITY_ARGV[@]}"' in driver, (
        "the scrub is declared but is not applied at the point the stage runs, which "
        "would leave it inert."
    )


def test_the_test_protocol_scrubs_the_credential_by_default() -> None:
    """Mechanism 3: `_run_script` withholds the pair unless a caller asks for it.

    The POLARITY is what is asserted. A helper that scrubbed only when asked would put
    the burden on every future call site to remember; scrubbing by default means a new
    stage is least-privileged unless someone deliberately says otherwise.
    """
    conftest = importlib.import_module("conftest")

    signature = inspect.signature(conftest._run_script)
    administrative = signature.parameters.get("administrative")
    assert administrative is not None, (
        "tests/conftest.py::_run_script no longer takes `administrative`, so every "
        "stage it runs receives the database superuser password again (SEC-04)."
    )
    assert administrative.default is False, (
        f"`administrative` defaults to {administrative.default!r}; it must default to "
        "False so a stage is least-privileged unless it deliberately opts in."
    )

    # The helper itself, exercised rather than read.
    scrubbed = conftest.without_admin_credentials(
        {
            "ACAS_DB_ADMIN_USER": "root",
            "ACAS_DB_ADMIN_PASSWORD": "SENTINEL-SUPERUSER-SECRET",
            "ACAS_DB_USER": "acas",
            "ACAS_DB_PASSWORD": "app-secret",
        }
    )
    for name in _ADMIN_CREDENTIAL_NAMES:
        assert name not in scrubbed, f"{name} survived the scrub"
    assert "SENTINEL-SUPERUSER-SECRET" not in scrubbed.values(), (
        "the superuser password survived the scrub under some other name"
    )
    # Application access must be untouched, or every scrubbed stage loses the database.
    assert scrubbed["ACAS_DB_USER"] == "acas"
    assert scrubbed["ACAS_DB_PASSWORD"] == "app-secret"

    # Exactly the schema-administration stages opt in: the seed and the two resets.
    source = (Path(conftest.__file__).read_text(encoding="utf-8"))
    assert source.count("administrative=True") == 3, (
        f"{source.count('administrative=True')} call site(s) request the "
        "administrative credential; exactly three should - the seed and the two "
        "resets. A fourth means some other stage has been handed the superuser."
    )


# ---------------------------------------------------------------------------
#  SEC-05 - NO ACCOUNTING VALUE REACHES AN ASSERTION MESSAGE
#
#  `harness/diff_states.py` ships two renderers and only one of them is safe to put in
#  a failure message:
#
#    render(tree)     every differing value AND every primary key. Its purpose is the
#                     on-disk report, where that detail belongs.
#    summarise(tree)  table, column name and ordinal, counts. No value, no key.
#
#  The scenario and determinism tiers interpolated `render` into assertion messages, so
#  a failing parity run printed real ledger balances, VAT amounts and account
#  identifiers into pytest output and from there into any log that collects it. The
#  route is now `ParityRun.diagnose()`, `DeterminismRun.diagnose()` and the `withheld`
#  fixture, all defined once in `tests/conftest.py`.
#
#  This is a STATIC test on purpose. The tier it polices is stack-bound - without the
#  Compose stack those tests skip - so the messages themselves are not exercised by an
#  ordinary run, and a regression here would otherwise be invisible until the day a
#  parity run actually failed. Reading the source needs no stack.
# ---------------------------------------------------------------------------

#: The tiers whose assertion messages describe a comparison of real table state.
_STATE_ASSERTING_TIERS: tuple[str, ...] = ("tests/scenarios", "tests/determinism")


def _assertion_message_interpolations(path: Path) -> list[tuple[int, str]]:
    """Every expression interpolated into an `assert` MESSAGE in one module.

    The message is what reaches a log. An expression in the assert CONDITION is not
    printed by pytest unless it is also in the message, so only the message is read.

    Args:
        path: The module to read.

    Returns:
        `(line number, source of the interpolated expression)` for each one.
    """
    found: list[tuple[int, str]] = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"), filename=str(path))):
        if isinstance(node, ast.Assert) and node.msg is not None:
            for inner in ast.walk(node.msg):
                if isinstance(inner, ast.FormattedValue):
                    found.append((inner.lineno, ast.unparse(inner.value)))
    return found


def test_no_assertion_message_renders_a_value_bearing_report() -> None:
    """No `diff_states.render` reaches an assertion message (finding SEC-05).

    `render` is not banned outright, because it is the right function for writing the
    report and for asserting that an EMPTY comparison renders to nothing. What is
    banned is putting its output where pytest will print it.
    """
    root = Path(__file__).resolve().parents[2]
    offenders: list[str] = []

    for tier in _STATE_ASSERTING_TIERS:
        directory = root / tier
        assert directory.is_dir(), f"a declared tier is absent: {directory}"
        modules = sorted(directory.glob("test_*.py"))
        assert modules, f"{tier} holds no test module; this test would be vacuous"
        for module in modules:
            for line, expression in _assertion_message_interpolations(module):
                if re.search(r"(^|\.)_?render\s*\(", expression):
                    offenders.append(f"{tier}/{module.name}:{line}: {expression[:74]}")

    assert not offenders, (
        "these assertion messages interpolate the value-bearing report, which copies "
        "real accounting figures and account identifiers into pytest output:\n  "
        + "\n  ".join(offenders)
        + "\n  Use `parity.diagnose()` / `run.diagnose()` instead - the same comparison, "
        "summarised without values, naming the report and its digest so the figures are "
        "still reachable by anyone who should see them."
    )


def test_the_value_free_route_exists_and_actually_withholds() -> None:
    """The DISCRIMINATING half: `summarise` and `withheld` withhold what they promise.

    A test that only banned `render` would pass just as well against a `diagnose()`
    that had been quietly repointed back at the value-bearing renderer. So sentinel
    values and a sentinel key are pushed through both value-free routes and the output
    is searched for them. `render` is checked too, in the same breath, because the ban
    above is only worth having while the two really do differ.
    """
    root = Path(__file__).resolve().parents[2]
    # Loaded by explicit path, like `_scenario_yaml_module` above, so this tier keeps
    # importing no harness module by package path (rule R-1).
    path = root / "harness" / "diff_states.py"
    assert path.is_file(), f"the comparison module is absent: {path}"
    module_name = "acas_diff_states_probe"
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    diff_states = importlib.util.module_from_spec(spec)
    # Registered BEFORE execution, and removed again on failure, exactly as
    # `tests/conftest.py` does it: the module's records are `@dataclass(slots=True)`,
    # and that decorator resolves `cls.__module__` through `sys.modules` while the
    # class is being built, so an unregistered module fails to execute at all.
    sys.modules[module_name] = diff_states
    try:
        spec.loader.exec_module(diff_states)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise

    value_difference = diff_states.ValueDifference(
        column="LEDGER-BALANCE", ordinal=7,
        cobol="SENTINEL-COBOL-VALUE", python="SENTINEL-PYTHON-VALUE",
    )
    tree = diff_states.TreeDiff(
        tables=(
            diff_states.TableDiff(
                table="GLLEDGER-REC", primary_key="LEDGER-KEY",
                in_cobol=True, in_python=True,
                cobol_columns=("LEDGER-KEY", "LEDGER-BALANCE"),
                python_columns=("LEDGER-KEY", "LEDGER-BALANCE"),
                cobol_row_count=1, python_row_count=1,
                missing_in_python=("SENTINEL-MISSING-KEY",), missing_in_cobol=(),
                value_differences=(
                    diff_states.RowDifference(
                        key="SENTINEL-ROW-KEY", values=(value_difference,)
                    ),
                ),
                rows_compared=1,
                cobol_key_types=("str",), python_key_types=("str",),
            ),
        ),
        cobol_dir=None, python_dir=None,
    )
    sentinels = (
        "SENTINEL-COBOL-VALUE", "SENTINEL-PYTHON-VALUE",
        "SENTINEL-ROW-KEY", "SENTINEL-MISSING-KEY",
    )

    summary = diff_states.summarise(tree, report_path=None)
    leaked = [sentinel for sentinel in sentinels if sentinel in summary]
    assert not leaked, (
        f"`summarise` disclosed {leaked}, so the route the scenario tier now relies on "
        "is no longer value-free and finding SEC-05 is reopened."
    )
    # It must still be a USEFUL diagnosis: naming the table and column is the whole
    # point of summarising rather than saying nothing.
    assert "GLLEDGER-REC" in summary and "LEDGER-BALANCE" in summary, (
        "`summarise` withheld the values AND the table and column names, which leaves a "
        f"failure message that cannot be acted on at all: {summary!r}"
    )

    # And the ban above is only meaningful while `render` really does disclose them.
    rendered = diff_states.render(tree)
    assert all(sentinel in rendered for sentinel in sentinels), (
        "`render` no longer discloses values or keys, so the two renderers no longer "
        "differ and this test pair has stopped measuring anything. Re-derive the "
        "SEC-05 policy against what the module now does."
    )


def test_the_withheld_helper_handles_every_shape_the_tier_passes_it() -> None:
    """`withheld` is exercised here because a failure message is not exercised anywhere.

    An assertion message is only formatted WHEN THE ASSERTION FAILS, and the tier that
    calls `withheld` is stack-bound, so on a green run these expressions are never
    evaluated - not locally, and not inside the harness image either. A `TypeError`
    raised while formatting a failure message would therefore stay hidden until the one
    moment it destroys a real diagnosis.

    So every argument SHAPE the call sites actually pass is driven through the helper
    here: a scalar string, an integer, a mapping (one dumped row), a sequence of rows, a
    set of keys, and a tuple of projected cells. Each is checked to render and to
    withhold.
    """
    conftest = importlib.import_module("conftest")
    withheld = conftest._withheld

    sentinel = "SENTINEL-9876.54"
    shapes: tuple[tuple[str, Any], ...] = (
        ("scalar string", sentinel),
        ("integer", 4242),
        ("one dumped row", {"LEDGER-KEY": sentinel, "LEDGER-BALANCE": sentinel}),
        ("a sequence of rows", [{"k": sentinel}, {"k": sentinel}]),
        ("a set of keys", {sentinel, sentinel + "-B"}),
        ("a tuple of cells", (sentinel, 1, None)),
        ("None", None),
    )

    for label, value in shapes:
        rendered = withheld(value, column="LEDGER-BALANCE", artifact="/out/x.json")
        assert isinstance(rendered, str) and rendered.startswith("<") and rendered.endswith(">"), (
            f"withheld({label}) produced {rendered!r}, which is not the bracketed "
            "stand-in every call site interpolates."
        )
        assert sentinel not in rendered, (
            f"withheld({label}) disclosed the value it exists to withhold: {rendered!r}"
        )
        assert "LEDGER-BALANCE" in rendered, (
            f"withheld({label}) dropped the column name, which is the part of the "
            f"message a reader acts on: {rendered!r}"
        )

    # Called the way most sites call it - no column, no artifact - it must still render.
    assert withheld(sentinel).startswith("<"), "withheld() needs its optional arguments"


# ---------------------------------------------------------------------------
#  ADV-01 - THE ADVISORY REGISTER STAYS TRUE TO WHAT THE TREE ACTUALLY DOES
#
#  README section 7.1 records an advisory review of every pinned component. A review is
#  a point-in-time record and no offline test can re-run the queries, so what IS tested
#  here is the two claims the register makes ABOUT THIS REPOSITORY -- the parts that can
#  silently stop being true:
#
#    1. every pinned distribution was actually reviewed, so adding a pin without
#       reviewing it is a failure rather than an omission nobody notices; and
#    2. none of the standard-library modules named by the ten applicable CPython
#       advisories is imported anywhere, which is the register's stated reason those
#       advisories are unreachable rather than merely accepted.
#
#  Neither test asserts a vulnerability verdict. They assert that the register cannot
#  drift away from the tree it describes.
# ---------------------------------------------------------------------------

#: The standard-library modules named by the ten CPython advisories that apply to the
#: pinned interpreter. Recorded as top-level module names because that is the
#: granularity an import census can decide.
_ADVISORY_NAMED_STDLIB: Mapping[str, str] = MappingProxyType(
    {
        "plistlib": "CVE-2025-13837",
        "xml": "CVE-2025-12084, CVE-2026-7210",
        "base64": "CVE-2025-12781",
        "tarfile": "CVE-2025-13462",
        "http": "CVE-2026-3644, CVE-2026-6019",
        "html": "CVE-2026-15308",
        "webbrowser": "CVE-2026-4519",
    }
)

#: Named separately because it is a CALL, not an import: `shutil` is entirely fine.
_ADVISORY_NAMED_CALL = "unpack_archive"

_CENSUS_ROOTS: tuple[str, ...] = ("acas_posting", "harness", "tests")


def test_every_pinned_distribution_appears_in_the_advisory_register() -> None:
    """A pin nobody reviewed is the ADV-01 gap reopening.

    The register in README section 7.1 lists the distributions it reviewed. If a pin is
    added to the lock and the register is not extended, the project is carrying a
    component whose advisory status was never examined -- which is precisely the state
    the finding was raised about. Asserted against the lock rather than against
    `pyproject.toml` because the lock is what every environment installs from.
    """
    root = Path(__file__).resolve().parents[2]
    register = (root / "README-python-migration.md").read_text(encoding="utf-8").lower()
    lock = (root / "requirements.txt").read_text(encoding="utf-8")

    pinned = sorted(
        {
            _canonical_distribution(match.group(1))
            for match in re.finditer(
                r"^([A-Za-z][A-Za-z0-9_.-]*)==", lock, re.MULTILINE
            )
        }
    )
    assert pinned, "no pin was parsed from requirements.txt; the census is vacuous"

    unreviewed = [
        name
        for name in pinned
        # The register may spell a name either way round, as PyPI itself does.
        if name not in register and name.replace("-", "_") not in register
    ]
    assert not unreviewed, (
        "requirements.txt pins these distributions and README section 7.1 does not "
        f"name them, so their advisory status is unrecorded: {', '.join(unreviewed)}\n"
        "  Re-run the two queries the register documents and extend it; do not edit "
        "the verdict by hand."
    )


def test_no_advisory_named_stdlib_module_is_imported() -> None:
    """The register calls ten CPython advisories unreachable. This is why.

    Every one of them lives in a module this migration does not use -- consistent with
    the plan's own list of load-bearing standard-library modules (`decimal`, `datetime`,
    `dataclasses`, `argparse`, `pathlib`, `csv`, `json`). Importing one does not create a
    vulnerability by itself, but it DOES falsify the register's stated basis, so the
    correct response to this test failing is to re-review and rewrite section 7.1 --
    not to work around the assertion.
    """
    root = Path(__file__).resolve().parents[2]
    offenders: list[str] = []

    for relative in _CENSUS_ROOTS:
        for path in sorted((root / relative).rglob("*.py")):
            text = path.read_text(encoding="utf-8")
            shown = path.relative_to(root)
            if f".{_ADVISORY_NAMED_CALL}(" in text or f" {_ADVISORY_NAMED_CALL}(" in text:
                offenders.append(f"{shown}: calls {_ADVISORY_NAMED_CALL} (CVE-2026-3087)")
            for node in ast.walk(ast.parse(text, filename=str(path))):
                imported: list[str] = []
                if isinstance(node, ast.Import):
                    imported = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    imported = [node.module]
                for name in imported:
                    top = name.split(".")[0]
                    if top in _ADVISORY_NAMED_STDLIB:
                        offenders.append(
                            f"{shown}:{node.lineno}: imports {name} "
                            f"({_ADVISORY_NAMED_STDLIB[top]})"
                        )

    assert not offenders, (
        "README section 7.1 records that no module named by an applicable CPython "
        "advisory is imported, and that is the register's basis for calling those "
        "advisories unreachable. These imports contradict it:\n  "
        + "\n  ".join(offenders)
        + "\n  Re-review the affected advisories and rewrite section 7.1 to say what is "
        "actually true."
    )


# ---------------------------------------------------------------------------
#  MJ-13 - ONE GLOBAL RESOLUTION STATE FOR EVERY R-6 QUESTION
#
#  `docs/migration/ambiguity-resolutions.md` is the SINGLE place a question's status is
#  declared. Its consumers - the test headers, the traceability document, the anomaly
#  log and the evidence register - then DESCRIBE that status in prose, and prose does
#  not follow a status when it changes. The measured result was a register declaring
#  `Q-2`, `Q-3`, `Q-4`, `Q-5.1`, `Q-5.2` and `Q-SORT-TIE-ORDER` `RESOLVED BY ORACLE`
#  while consumers still called them "pending", "unmeasured", "still open" and, in one
#  case, `PENDING - AWAITING ORACLE EXECUTION` verbatim. Under R-6 that is not a
#  cosmetic drift: a reader cannot tell which statement is current, so the project's
#  arbitration state stops being knowable, and the register's own §17 self-audit was
#  counting statuses that its consumers contradicted.
#
#  The invariant this locks is deliberately POSITIVE rather than a blacklist of stale
#  phrases, because a blacklist has to anticipate the wording and this does not: IF a
#  consumer describes a question in open language AT ALL, the register's own resolution
#  must appear beside it. Historical narrative therefore passes by construction - "was a
#  question for the oracle, and the oracle has ANSWERED it" carries the resolution in the
#  same breath - while a bare "Q-4 is pending" cannot pass however it is phrased.
_REGISTER_RELATIVE: Final[str] = "docs/migration/ambiguity-resolutions.md"

#: Wording that presents a question as NOT YET measured.
_OPEN_LANGUAGE: Final[re.Pattern[str]] = re.compile(
    r"\bstill open\b|\bstill pending\b|\bremains open\b|\bis pending\b|\bare pending\b"
    r"|\bawaiting oracle\b|\bAWAITING ORACLE EXECUTION\b|\bpending measurement\b"
    r"|\bunmeasured\b|\bnobody has measured\b|\bopen question\b|\bopen half\b"
    r"|\bnot (?:yet )?(?:been )?(?:resolved|settled|measured|arbitrated)\b"
    r"|\bonly execution shows\b|\bis a question for the oracle\b|\bnever resolved\b",
    re.IGNORECASE,
)

#: Wording that names the register's resolution, so openness is never stated alone.
_RESOLUTION_LANGUAGE: Final[re.Pattern[str]] = re.compile(
    r"\bRESOLVED\b|\bMEASURED\b|\bANSWERED\b|\bsettled by the language\b"
    r"|\bsettled by\b|\bsettled BY\b",
    re.IGNORECASE,
)


def _register_statuses(root: Path) -> dict[str, str]:
    """Read every question's DECLARED status out of the register.

    Args:
        root: The repository root.

    Returns:
        Question identifier to the status text the register declares for it.
    """
    lines = (root / _REGISTER_RELATIVE).read_text(encoding="utf-8").splitlines()
    heading = re.compile(r"^#{3,4}\s+`(Q-[A-Za-z0-9._-]+)`")
    status = re.compile(r"\*\*Status:\s*(.+?)\*\*", re.S)
    declared: dict[str, str] = {}
    for index, line in enumerate(lines):
        match = heading.match(line)
        if match is None:
            continue
        # The status sits on the heading's own line or within the next few, after the
        # blank line the register's house style puts between them.
        found = status.search("\n".join(lines[index : index + 8]))
        declared[match.group(1)] = found.group(1).strip() if found else ""
    return declared


def test_the_register_declares_a_status_for_every_question_it_enters() -> None:
    """Every `Q-` heading carries a parseable `**Status:**`.

    The precondition for the lock below: a question whose status cannot be read cannot
    be checked against its consumers, and would pass silently.
    """
    root = Path(__file__).resolve().parents[2]
    declared = _register_statuses(root)
    assert len(declared) >= 22, (
        f"the register entered {len(declared)} questions; it carried 22 when this lock "
        f"was written, and entries are never removed."
    )
    unstated = sorted(qid for qid, text in declared.items() if not text)
    assert not unstated, (
        "these register entries have no parseable `**Status:**` line, so their "
        "resolution state cannot be compared with what consumers say about them:\n  "
        + "\n  ".join(unstated)
    )
    # The three statuses that PERMIT open language must still be distinguishable from
    # the ones that do not, or the lock below would vacuously pass everything.
    permits = {
        qid
        for qid, text in declared.items()
        if "PENDING" in text.upper()
        or "PARTIALLY" in text.upper()
        or "different statuses" in text
    }
    assert permits, (
        "no register entry has a status that permits open language, which means the "
        "classification below cannot be discriminating. Q-9 is PARTIALLY RESOLVED and "
        "Q-GL084-ACCEPT-SEMANTICS is PENDING; if both are gone, re-derive this lock."
    )


def test_no_consumer_describes_a_resolved_question_as_open() -> None:
    """A consumer may state openness only alongside the register's resolution.

    Read as TEXT across the test suite and the three sibling migration documents,
    because the statements at issue are docstrings, block comments, assertion messages
    and Markdown prose in roughly equal measure - there is no single syntactic node to
    walk. The register itself is excluded: it is the source of truth, and it
    deliberately preserves the readings it has rejected as evidence.
    """
    root = Path(__file__).resolve().parents[2]
    declared = _register_statuses(root)
    # Only questions the register declares FULLY resolved are governed. A `PENDING` or
    # `PARTIALLY RESOLVED` question is entitled to be described as open, because it is.
    governed = {
        qid: text
        for qid, text in declared.items()
        if "PENDING" not in text.upper()
        and "PARTIALLY" not in text.upper()
        and "different statuses" not in text
    }
    assert governed, "no fully resolved question was found; re-derive this lock."

    # A boundary on the right, so `Q-5` does not match inside `Q-5.1` and `Q-2` does not
    # match inside `Q-20`.
    patterns = {
        qid: re.compile(re.escape(qid) + r"(?![0-9A-Za-z._-])") for qid in governed
    }

    consumers = sorted(root.joinpath("tests").rglob("*.py"))
    consumers += [
        path
        for path in sorted(root.joinpath("docs", "migration").glob("*.md"))
        if path.name != Path(_REGISTER_RELATIVE).name
    ]

    violations: list[str] = []
    for path in consumers:
        lines = path.read_text(encoding="utf-8").splitlines()
        for index, line in enumerate(lines):
            hits = [qid for qid, pattern in patterns.items() if pattern.search(line)]
            if not hits:
                continue
            window = "\n".join(lines[max(0, index - 5) : index + 7])
            if _OPEN_LANGUAGE.search(window) is None:
                continue
            if _RESOLUTION_LANGUAGE.search(window) is not None:
                continue
            relative = path.relative_to(root)
            violations.append(
                f"{relative}:{index + 1}: {', '.join(sorted(hits))} described as open "
                f"with no resolution named nearby: {line.strip()[:80]}"
            )

    assert not violations, (
        "these consumers describe a question the register declares RESOLVED using "
        "open language, without naming the resolution anywhere nearby, so the "
        "project's R-6 arbitration state reads differently depending on which file "
        "you open (MJ-13):\n  " + "\n  ".join(violations) + "\n\n"
        "  Either state the register's declared status beside the open language - "
        "which is what a historical account does - or remove the open language. The "
        "register at "
        + _REGISTER_RELATIVE
        + " is the single place a status is declared."
    )


def _repo_root() -> Path:
    """The repository root, by this module's own convention."""
    return Path(__file__).resolve().parents[2]


def _harness_dir() -> Path:
    """The harness tree, which is a SIBLING of the package (rule R-1)."""
    return _repo_root() / "harness"


def _tests_dir() -> Path:
    """The test tree, which owns the tier-availability probe."""
    return _repo_root() / "tests"


# ---------------------------------------------------------------------------
#  THE ORACLE'S PROVENANCE IS THE IDENTITY OF THE SPECIFICATION (finding SEC-02)
#
#  Under R-6 the compiled COBOL *is* the behavioural specification, so "which bytes
#  were compiled" is not an operational detail -- it decides what the migration is
#  being measured against. A build that repairs IF scope, connection lifetime,
#  credential propagation and stale reply pairs has repaired the specification, and
#  an empty diff against it shows agreement with a PATCHED system.
#
#  The defect these close is a quiet one. The transformations were applied
#  unconditionally, so no frozen build was reachable at all, and `run_parity.sh`
#  merely WARNED about the result before printing `identical`. A reader taking the
#  verdict at face value would have read a parity claim that nothing established.
# ---------------------------------------------------------------------------


def test_the_frozen_oracle_is_the_default_and_transformation_is_opt_in() -> None:
    """A build with no flags applies no source transformation.

    The catalogue of available transformations must not be the register of applied
    ones: the attestation's `oracle-source-is-frozen` is derived from what was
    APPLIED, so a build that applies nothing can answer `yes`. When the two were the
    same array, and that array was a non-empty `readonly`, the answer could only ever
    be `no`.
    """
    build = (_harness_dir() / "build_oracle.sh").read_text(encoding="utf-8")

    # The default is frozen, and the opt-in is a distinct, explicit request. The
    # check is ^-anchored to the DECLARATION: `--frozen-oracle` also assigns 0, but
    # indented, and an unanchored substring test is satisfied by that assignment even
    # when the declaration itself has been flipped to 1.
    declaration = re.search(
        r"^ACAS_ALLOW_SOURCE_TRANSFORMS=(\d+)", build, re.MULTILINE
    )
    assert declaration is not None, "build_oracle.sh declares no transform switch"
    assert declaration.group(1) == "0", (
        "the shipped default applies source transformations, so no frozen oracle is "
        f"reachable and `oracle-source-is-frozen=yes` is unattainable; got "
        f"{declaration.group(1)!r}"
    )
    assert "--transformed-oracle" in build
    assert "--frozen-oracle" in build

    # The APPLIED register exists and is what the attestation is derived from.
    assert "ACAS_SOURCE_TRANSFORMS_APPLIED" in build
    assert "if (( ACAS_ALLOW_SOURCE_TRANSFORMS )); then" in build

    # `source_is_frozen` must be computed from the APPLIED register. Deriving it
    # from the available catalogue is the original defect: that catalogue is a
    # non-empty `readonly` array, so `yes` was unreachable by construction. The
    # assertion is on the ASSIGNMENT's own line so a comment cannot satisfy it.
    derivations = [
        line.strip()
        for line in build.splitlines()
        if "source_is_frozen=" in line and not line.strip().startswith("#")
    ]
    assert derivations, "nothing assigns source_is_frozen"
    assert any("ACAS_SOURCE_TRANSFORMS_APPLIED" in line for line in derivations), (
        "source_is_frozen is not derived from the APPLIED transform register: "
        f"{derivations!r}. Deriving it from the available catalogue makes `yes` "
        "unreachable, which is how a transformed oracle passed as frozen."
    )
    assert not any(
        "ACAS_SOURCE_TRANSFORMS[@]" in line
        and "APPLIED" not in line
        for line in derivations
    ), f"source_is_frozen still reads the available catalogue: {derivations!r}"


def test_the_parity_driver_refuses_a_transformed_oracle_as_evidence() -> None:
    """A non-frozen oracle ends the run, and not with a difference status.

    The distinction is the point. `69`/`1` mean the two states disagree, which is a
    finding ABOUT the migration. `77` means nothing was compared, which is a finding
    about the harness's inputs. Collapsing them would let "we could not measure" be
    read as "we measured and it matched", or as a behavioural defect that does not
    exist.
    """
    parity = (_harness_dir() / "run_parity.sh").read_text(encoding="utf-8")

    assert "EX_EVIDENCE_UNAVAILABLE=77" in parity
    # Distinct from every other status the driver uses.
    for other in ("EX_OK=0", "EX_USAGE=70", "EX_PRECONDITION=71"):
        assert other in parity, f"{other} is missing, so 77's distinctness is unproven"
        assert not other.endswith("=77")

    # The refusal is a die, not a warn.
    assert 'acas_parity_die "$EX_EVIDENCE_UNAVAILABLE"' in parity

    # An ABSENT attestation is the same class of answer, because the commonest reason
    # for one on this checkout is that the default frozen build failed.
    absent_gate = parity.split("$ACAS_PARITY_ATTESTATION_BASENAME")[1][:1500]
    assert "EX_EVIDENCE_UNAVAILABLE" in absent_gate, (
        "an absent attestation is still reported as a precondition rather than as "
        "evidence-unavailable, so a failed frozen build reads as operator error"
    )

    # The escape hatch exists, is explicit, and taints the verdict rather than
    # silently restoring it.
    assert "--accept-transformed-oracle" in parity
    assert "ACAS_PARITY_ORACLE_IS_DIAGNOSTIC" in parity
    assert "identical-against-diagnostic-oracle" in parity
    assert "NO PARITY CLAIM" in parity


def test_the_test_tier_skips_rather_than_asserting_parity_on_a_stale_oracle() -> None:
    """The scenario tier reports itself unavailable against a transformed oracle.

    A tier that PASSED here would publish a parity claim nobody had measured, and a
    passing test is far less visible than a skip. The judgement must match
    `run_parity.sh`'s so the two cannot disagree about what counts as evidence.
    """
    conftest = (_tests_dir() / "conftest.py").read_text(encoding="utf-8")

    assert "_probe_oracle_is_frozen" in conftest
    assert "oracle-source-is-frozen" in conftest
    assert "oracle:not-frozen" in conftest
    # Wired into the probe that decides tier availability, not merely defined.
    assert "_probe_oracle_is_frozen(build_root, missing, detail)" in conftest
    # The diagnosis opt-in mirrors the driver's flag.
    assert "ACAS_ACCEPT_TRANSFORMED_ORACLE" in conftest
    # And the skip reason must carry the measured cause, not a vague pointer.
    assert "exit 74" in conftest
    assert "ACAS-SQLstate-error-list.cob" in conftest


def test_the_missing_member_is_never_written_into_the_frozen_tree() -> None:
    """The absent copybook is not fabricated, and the shim stays comment-only.

    Inventing a frozen source file would breach R-3 (no new validations) and R-4
    (reproduce, never fix). The shim exists only under the writable build copy, and
    its being comment-only is what makes it behaviour-neutral -- measured: the
    generated C is byte-identical with the shim, with a zero-byte member, and with
    different comment text.
    """
    repo = _harness_dir().parent
    assert not (repo / "copybooks" / "ACAS-SQLstate-error-list.cob").exists(), (
        "the missing archive member has been written into the FROZEN tree; R-3 and "
        "R-4 forbid inventing it, and it must be supplied by the maintainer"
    )

    shim = _harness_dir() / "copybook-shims" / "ACAS-SQLstate-error-list.cob"
    assert shim.is_file(), "the build-copy shim is absent"
    for number, line in enumerate(shim.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        if not stripped:
            continue
        assert stripped.startswith("*>"), (
            f"{shim} line {number} is not a comment: {stripped!r}. Executable text "
            f"here would make the shim a behavioural change rather than a "
            f"compatibility include"
        )


# ---------------------------------------------------------------------------
#  THE EVIDENCE VOLUME HAS A STATED LIFETIME (finding PRIV-01, CWE-459)
#
#  THE DEFECT THIS CLOSES. The harness publishes every parity run into a named
#  volume and said nothing about how long it is kept, what protects it, or how it is
#  disposed of. Measured on this clone: 1410 files, 11.5 MB, nine scenario trees, and
#  the captures are `SELECT *` over the in-scope tables -- so they carry monetary
#  amounts and the primary keys identifying the accounts, customers and suppliers
#  those amounts belong to. An accumulating store of accounting data with no
#  documented disposal is the finding, and the fix is a contract a reader can follow.
#
#  WHY THE DISPOSAL COMMAND'S SHAPE IS ASSERTED, NOT JUST ITS PRESENCE. Sibling
#  clones each own an `acas-harness-<CLONE_INDEX>-out` volume in the same daemon, so
#  `docker volume prune` -- the command an operator reaches for by reflex -- destroys
#  other runs' evidence. Documenting a guarded command and leaving an unguarded one
#  in the same file would defeat the point, so the unguarded forms are asserted
#  ABSENT outside a prohibition.
# ---------------------------------------------------------------------------

#: Every document that must carry the retention and disposal contract.
_RETENTION_DOCUMENTS: tuple[str, ...] = (
    "README-python-migration.md",
    "docs/migration/scenario-diff-evidence.md",
    "harness/docker-compose.yml",
)

#: Commands that reach volumes this clone does not own. Each may appear only as a
#: prohibition -- on a line that also warns against it.
_UNGUARDED_DISPOSAL: tuple[str, ...] = (
    "docker volume prune",
    "docker volume rm $(docker volume ls -q)",
)


@pytest.mark.parametrize("relative_path", _RETENTION_DOCUMENTS)
def test_the_evidence_retention_and_disposal_contract_is_stated(
    relative_path: str,
) -> None:
    """Retention, protection and disposal are documented where an operator looks.

    All three of these files are read by someone deciding what to do with a finished
    run: the README is the narrative, the evidence register is what cites the
    artifacts, and the Compose file is where the volume is declared. A contract
    stated in only one of them is a contract most readers never see.
    """
    text = (_repo_root() / relative_path).read_text(encoding="utf-8")
    lowered = text.lower()

    assert "retention" in lowered or "retain" in lowered, (
        f"{relative_path} says nothing about how long evidence is kept"
    )
    assert "dispos" in lowered, (
        f"{relative_path} says nothing about how evidence is disposed of"
    )
    # The guarded, clone-scoped command, which is the whole mechanism.
    assert "acas-harness-${CLONE_INDEX}-out" in text, (
        f"{relative_path} does not name the clone-scoped volume, so a reader has no "
        f"target-guarded command to copy"
    )


@pytest.mark.parametrize("relative_path", _RETENTION_DOCUMENTS)
def test_no_document_offers_an_unguarded_disposal_command(
    relative_path: str,
) -> None:
    """A broad delete may appear only as a prohibition, never as instruction.

    `docker volume prune` reaches every sibling clone's evidence in the same daemon.
    Naming it is useful -- an operator who has been told not to run it is better
    informed than one who has not -- so the test allows the mention and requires the
    warning on the same line.
    """
    text = (_repo_root() / relative_path).read_text(encoding="utf-8")
    for number, line in enumerate(text.splitlines(), start=1):
        for command in _UNGUARDED_DISPOSAL:
            if command not in line:
                continue
            assert "never" in line.lower() or "not" in line.lower(), (
                f"{relative_path} line {number} offers `{command}` without warning "
                f"against it. It reaches every sibling clone's evidence volume in "
                f"this daemon: {line.strip()!r}"
            )


def test_the_evidence_volume_cannot_default_to_a_sibling_clone() -> None:
    """`CLONE_INDEX` is required for the evidence volume, not defaulted.

    This is what makes the documented disposal command safe: the volume cannot
    silently resolve to a name another run owns, so `docker volume rm
    "acas-harness-${CLONE_INDEX}-out"` either names this clone's volume or fails.
    A `${CLONE_INDEX:-000}` style default would reintroduce the hazard.
    """
    compose = (_harness_dir() / "docker-compose.yml").read_text(encoding="utf-8")
    out_declaration = [
        line for line in compose.splitlines() if "-out" in line and "name:" in line
    ]
    assert out_declaration, "the evidence volume declares no name"
    for line in out_declaration:
        assert "${CLONE_INDEX:?" in line, (
            f"the evidence volume's name does not REQUIRE CLONE_INDEX, so it can "
            f"resolve to a sibling clone's volume: {line.strip()!r}"
        )
        assert "${CLONE_INDEX:-" not in line, (
            f"the evidence volume's name DEFAULTS CLONE_INDEX, which is the hazard "
            f"the required form exists to prevent: {line.strip()!r}"
        )
