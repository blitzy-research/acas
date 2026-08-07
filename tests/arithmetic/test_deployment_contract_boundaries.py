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
import dataclasses
import importlib
import inspect
import re
from pathlib import Path

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
