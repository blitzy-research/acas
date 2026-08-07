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
#  MJ-20 - THE DECLARED RUNTIME DEPENDENCIES ARE THE IMPORTED ONES
#
#  `pyproject.toml` declared `SQLAlchemy`, `greenlet` and `typing_extensions` as runtime
#  dependencies, SQLAlchemy described as "CORE LEVEL ONLY: text() statements on an
#  explicit Connection", and `requirements.txt` pinned all three with hashes, and the
#  README documented the boundary as active. No module under `acas_posting/` imported any
#  of them. The same file that declared them also stated, correctly, that the package
#  imports "exactly one third-party top-level module, `mysql`".
#
#  The individual package is not the point. The point is that nothing checked, so the
#  architecture the artifacts describe and the architecture that executes were free to
#  disagree - and they did, across three artifacts at once. This holds them together in
#  BOTH directions: a declared package that nothing imports is as much a defect as an
#  imported package that nothing declares, the first because it makes the shipped
#  execution path unauditable from the manifest, the second because an install
#  reproduced from the manifest would fail at import.
_PACKAGE_ROOT = "acas_posting"

#: Distribution name -> the top-level module it provides, for the runtime set. A
#: distribution whose import name differs from its package name needs an entry here.
_DISTRIBUTION_MODULES: Mapping[str, str] = MappingProxyType(
    {
        "mysql-connector-python": "mysql",
        # ⭐ MAPPED BUT NOT DECLARED, DELIBERATELY. These three are the packages MJ-20
        # was raised about. Keeping their import names here means that re-declaring one
        # is reported as "declared and never imported" -- the actual defect, naming the
        # package -- rather than as "this census cannot say", which is a true but much
        # less useful refusal. Presence in this mapping is not an endorsement: it is
        # what lets the assertion below be specific about them.
        "sqlalchemy": "sqlalchemy",
        "greenlet": "greenlet",
        "typing_extensions": "typing_extensions",
        "typing-extensions": "typing_extensions",
    }
)


def _declared_runtime_distributions() -> list[str]:
    """Return `pyproject.toml`'s `[project].dependencies`, names only.

    Returns:
        The distribution names, lower-cased, in declaration order.
    """
    root = Path(__file__).resolve().parents[2]
    manifest = root / "pyproject.toml"
    assert manifest.is_file(), f"the manifest is absent: {manifest}"
    parsed = tomllib.loads(manifest.read_text(encoding="utf-8"))
    declared = parsed["project"]["dependencies"]
    return [re.split(r"[=<>!~\[;]", entry, maxsplit=1)[0].strip().lower() for entry in declared]


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


def test_every_declared_runtime_dependency_is_actually_imported() -> None:
    """No runtime dependency is declared that the package does not import (MJ-20)."""
    declared = _declared_runtime_distributions()
    imported = _imported_third_party_modules()

    unmapped = sorted(name for name in declared if name not in _DISTRIBUTION_MODULES)
    assert not unmapped, (
        "these runtime dependencies have no entry in _DISTRIBUTION_MODULES, so this "
        f"census cannot say whether they are imported: {', '.join(unmapped)}. Add the "
        "distribution-to-module mapping rather than removing the assertion."
    )

    unused = sorted(
        name for name in declared if _DISTRIBUTION_MODULES[name] not in imported
    )
    assert not unused, (
        "these packages are declared as RUNTIME dependencies of acas_posting and no "
        f"module in the package imports them: {', '.join(unused)}.\n"
        "  A manifest that advertises an execution path the code does not take makes "
        "the shipped architecture unauditable from the artifact (MJ-20). Either use "
        "the package or stop declaring it -- and if it belongs to the harness or the "
        "test tooling, declare it in the matching optional-dependency group instead."
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
    """`requirements.txt` pins exactly the runtime set, with no orphan (MJ-20).

    The lock file is what the container and the parity protocol install from, so a pin
    surviving there after leaving `pyproject.toml` would keep the unused package in
    every environment that matters while the manifest looked clean.
    """
    root = Path(__file__).resolve().parents[2]
    lock = (root / "requirements.txt").read_text(encoding="utf-8")

    pinned = {
        match.group(1).lower()
        for match in re.finditer(r"^([A-Za-z][A-Za-z0-9_.-]*)==", lock, re.MULTILINE)
    }
    for name in _declared_runtime_distributions():
        assert name in pinned, (
            f"{name} is a declared runtime dependency and requirements.txt does not "
            "pin it, so a hashed install would not provide it."
        )

    # The three MJ-20 packages must be gone from BOTH artifacts, not just one.
    for stale in ("sqlalchemy", "greenlet", "typing_extensions"):
        assert stale not in pinned, (
            f"requirements.txt still pins {stale}, which nothing in acas_posting "
            "imports. A hashed install would place it in the container and the parity "
            "environment while pyproject.toml no longer declares it (MJ-20)."
        )


def test_no_document_claims_an_unused_data_access_boundary() -> None:
    """No artifact describes SQLAlchemy Core as the active boundary (MJ-20).

    Text rather than imports, because the defect was three documents describing an
    execution path the code did not take, and no import census can see prose. A
    sentence RECORDING that the boundary was considered and not taken is the decision
    record and is exempt; a sentence asserting it is active is not.
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
    # And a sentence that names the finding is the record of the decision, not a claim.
    exempt = ("mj-20", "deliberately absent", "is absent from")
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
