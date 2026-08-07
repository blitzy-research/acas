#!/usr/bin/env python3
# Executable in its own right, like the three state tools beside it: both run
# stages invoke it by path, and without this line the kernel refuses the exec and
# bash treats the plain-text lines of this docstring as commands.
"""The canonical state fingerprint: one digest per table, over every one of its rows.

WHY THIS EXISTS. Both run stages of the parity protocol record what state they were
handed and what state they left, and until now they recorded a ROW COUNT. A row count
cannot tell two different starting states apart: swap one balance, alter one status
byte, load a different fixture of the same shape, and the counts agree while the
states do not - and then every downstream difference, or its ABSENCE, belongs to the
seed rather than to either cycle. That is the most expensive failure a parity harness
has, because an empty diff over two differently-seeded databases looks exactly like
parity.

So each side records, per bounded table:

    <TABLE><TAB><row count><TAB><sha256 of the canonical dump>

and a table that cannot be read at all carries a single hyphen in both value fields -
a hyphen and never a zero, because "this table could not be read" is a different fact
from "this table is empty" and the far side must be able to tell them apart.

⭐ THE DIGEST IS TAKEN OVER `harness/dump_tables.py`'s OWN CANONICAL TEXT, through its
published `serialise_dump`. That is deliberate and it is the whole design:

  * it covers EVERY BOUNDED TABLE AND EVERY ROW, at each column's declared scale, in
    primary-key order - the same bytes stage 3 and stage 7 write and stage 8 compares;
  * it inherits, for free, every invariant the dump stage already enforces: the
    single-column primary-key ordering, the structural assertion against
    `information_schema`, the rule R-2 float refusal and the null refusal;
  * and BOTH SIDES COMPUTE IT WITH THIS ONE PROGRAM. Two digests are comparable only
    if one implementation produced them. A digest computed by the mysql client on one
    side and by the driver on the other would differ on formatting alone and would
    report a starting-state disagreement on every single run.

WHAT IT IS NOT. It is not a stage of the protocol and it writes nothing into a
compared tree: the runners put its output under `run-logs/`, outside every tree the
comparison reads, so a fingerprint can never be diffed as though it were posted data
(rule R-6). It issues `SELECT` only and emits no DDL (rule R-3). It reaches no COBOL
(rule R-1): the compiled oracle's side of the protocol invokes this Python program the
same way it invokes the dump stage, out of process and by path.

USAGE

    harness/table_digest.py TABLE [TABLE ...]
    harness/table_digest.py --scenario-file harness/scenarios/clean_batch_gl.yaml

The connection comes from the same `ACAS_DB_*` contract `harness/dump_tables.py`
resolves - one authority, never re-implemented here - which derives from
`03 RDB-Data.` [copybooks/wsfnctn.cob:L56-L62].

EXIT STATUS
    0  every requested table was digested
    1  at least one table could not be read; its line carries the hyphen markers and
       the reason is on stderr. The record is still complete and still comparable, so
       the caller decides what an unreadable table means to it.
    2  the command line was wrong - a table that is not one of the 22 in scope, or
       neither a table list nor a scenario file
    3  the environment or the server is unusable, so no record could be taken at all
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import os
import sys
from collections.abc import Sequence
from pathlib import Path
from types import ModuleType
from typing import Any, Final

#: Where this file lives, so its sibling is found without a `sys.path` change.
HARNESS_DIR: Final[Path] = Path(__file__).resolve().parent

#: The three exit statuses that are not "everything worked".
EX_UNREADABLE: Final[int] = 1
EX_USAGE: Final[int] = 2
EX_ENVIRONMENT: Final[int] = 3

#: What a value field holds when the table could not be read. Both runners and
#: `tests/conftest.py` spell the unreadable case this way.
UNREADABLE: Final[str] = "-"

#: The parameter row the menu exit persists on every route. Every scenario declares it,
#: so a scenario-file table list already covers it; it is appended only on the fallback
#: path where one does not - see `_resolve_tables`. It is dumped like any other table,
#: with its two credential cells withheld by `harness/dump_tables.py`, and digested here
#: as well, because a digest compares even those two. Named here once, and spelled the
#: same way in
#: `harness/run_cobol_scenario.sh`, `harness/run_python_scenario.sh` and
#: `tests/conftest.py`.
PARAMETER_TABLE: Final[str] = "SYSTEM-REC"


def _load_dump_tables() -> ModuleType:
    """Load `harness/dump_tables.py` BY PATH, because `harness/` is not a package.

    `pyproject.toml` excludes `harness*` from packaging and there is deliberately no
    `__init__.py` here: that absence is the structural enforcement of rule R-1, so
    `import dump_tables` is not available and must not be made available. The explicit
    loader is the same mechanism `tests/conftest.py` uses for the same reason.

    Returns:
        The loaded module.

    Raises:
        FileNotFoundError: The sibling is absent.
        ImportError: It is present but could not be executed.
    """
    target = HARNESS_DIR / "dump_tables.py"
    if not target.is_file():
        raise FileNotFoundError(
            f"{target} is absent, so no canonical dump can be taken and no digest "
            f"can be computed. It is the single definition of the capture this "
            f"fingerprint digests."
        )
    module_name = "acas_harness_dump_tables"
    specification = importlib.util.spec_from_file_location(module_name, target)
    if specification is None or specification.loader is None:
        raise ImportError(f"{target} could not be prepared for import.")
    module = importlib.util.module_from_spec(specification)
    # REGISTERED BEFORE EXECUTION, and removed again if execution fails. Not
    # optional: `dump_tables.py` declares `@dataclass(frozen=True, slots=True)`
    # classes, and `slots=True` rebuilds the class, which makes `dataclasses` look
    # the defining module up in `sys.modules` - so an unregistered module fails with
    # an AttributeError from inside the standard library. `tests/conftest.py`'s
    # loader registers for the same reason.
    sys.modules[module_name] = module
    try:
        specification.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise
    return module


def digest_of(dump_tables: ModuleType, dump: Any) -> str:
    """Return the SHA-256 of one table's canonical dump text.

    Args:
        dump_tables: The loaded dump module, for its published `serialise_dump`.
        dump: A dump object, as `dump_table` returns.

    Returns:
        The digest, 64 lower-case hexadecimal characters.

    Raises:
        ValueError: The dump object's shape is wrong - raised by `serialise_dump`,
            which is the one definition of that check.
    """
    return hashlib.sha256(
        dump_tables.serialise_dump(dump).encode("utf-8")
    ).hexdigest()


def _resolve_tables(
    dump_tables: ModuleType, named: Sequence[str], scenario_file: str | None
) -> tuple[str, ...]:
    """Resolve the table list, from an explicit list or a scenario file - never both.

    Args:
        dump_tables: The loaded dump module, for `scenario_tables` and `IN_SCOPE`.
        named: Table names given on the command line.
        scenario_file: A scenario definition whose `affected_tables` bounds the record.

    Returns:
        The tables, in the order the caller asked for them - which for a scenario file
        is the scenario's own DECLARED order, with `SYSTEM-REC` appended only when that
        order omits it, because the order is part of the fingerprint contract: the two
        sides compare these records byte for byte. An explicit list is taken exactly as
        given, so a caller that wants only some of them can say so.

    Raises:
        SystemExit: With `EX_USAGE`, when neither or both were given, or when a name is
            not one of the 22 tables in scope.
    """
    if bool(named) == bool(scenario_file):
        raise SystemExit(
            _fail(
                "give either a table list or --scenario-file, and exactly one of "
                "them. They are alternative ways of choosing the same list HERE, "
                "because this tool has no provenance field to put a scenario file "
                "in. Note that harness/dump_tables.py is DIFFERENT: it accepts "
                "--scenario-file alongside a selector and records it as provenance "
                "(scenario_file_sha256), refusing only --tables with "
                "--all-in-scope. This message previously claimed dump_tables "
                "refused the same combination, which is no longer true.",
                EX_USAGE,
            )
        )
    if named:
        tables = tuple(named)
    else:
        #  ⭐ THE SCENARIO-FILE FORM APPENDS THE MENU-PERSISTED PARAMETER ROW, because
        #  that is the order both run stages record. `overrewrite' rewrites SYSTEM-REC
        #  key 1 on all four subsystems - [general/general.cbl:L656-L672],
        #  [sales/sales.cbl:L628-L641], [purchase/purchase.cbl:L621-L634],
        #  [irs/irs.cbl:L759-L774] - and the migrated command line reproduces that
        #  paragraph, so both cycles write the row on every route. No scenario DUMPS
        #  it: the row carries `RDBMS-PASSWD char(12)'
        #  [copybooks/wssystem.cob:L139] and a dump is `SELECT *', and counting it in
        #  a scenario's declared table effect would tie that claim to fields no
        #  scenario reasons about -- `Date-Form', another of its columns
        #  [copybooks/wssystem.cob:L127], among them. A digest carries no value, so
        #  the row can be bounded here and nowhere else. Appended rather than sorted
        #  in, so the scenario's declared order is left exactly as written and the two
        #  sides' records stay byte-comparable.
        declared = tuple(dump_tables.scenario_tables(scenario_file))
        tables = (
            declared
            if PARAMETER_TABLE in declared
            else (*declared, PARAMETER_TABLE)
        )
    for table in tables:
        if table not in dump_tables.IN_SCOPE:
            raise SystemExit(
                _fail(
                    f"{table!r} is not one of the {len(dump_tables.IN_SCOPE)} "
                    f"in-scope tables harness/dump_tables.py declares. The inventory "
                    f"has exactly one definition in this repository.",
                    EX_USAGE,
                )
            )
    return tables


def _fail(message: str, status: int) -> int:
    """Report `message` on stderr and return `status`, for a `SystemExit`."""
    sys.stderr.write(f"harness/table_digest.py: {message}\n")
    return status


def main(argv: Sequence[str] | None = None) -> int:
    """Print one `<TABLE>\\t<count>\\t<digest>` line per requested table.

    RETURNS an exit code and never calls `sys.exit`, so a caller can drive it in
    process - the contract the three state tools beside it already carry.

    Args:
        argv: The argument vector, `sys.argv[1:]` when omitted.

    Returns:
        0, `EX_UNREADABLE`, `EX_USAGE` or `EX_ENVIRONMENT` as the module docstring
        describes.
    """
    parser = argparse.ArgumentParser(
        prog="harness/table_digest.py",
        description=(
            "One canonical state digest per table, for the pre-run and post-run "
            "fingerprints both run stages record."
        ),
    )
    parser.add_argument(
        "tables",
        nargs="*",
        metavar="TABLE",
        help="the tables to digest, in the order to record them",
    )
    parser.add_argument(
        "--scenario-file",
        default=None,
        help=(
            "a scenario definition whose affected_tables list bounds the record, "
            "read in the scenario's own declared order, with SYSTEM-REC - the parameter "
            "row the menu exit persists - appended if that list omits it"
        ),
    )
    try:
        namespace = parser.parse_args(list(argv) if argv is not None else None)
    except SystemExit as exit_request:
        # argparse's own usage failure is EX_USAGE by construction; returned rather
        # than allowed to escape, so this function keeps its no-`sys.exit` contract.
        return int(exit_request.code or EX_USAGE)

    try:
        dump_tables = _load_dump_tables()
    except (FileNotFoundError, ImportError) as exc:
        return _fail(str(exc), EX_ENVIRONMENT)

    try:
        tables = _resolve_tables(
            dump_tables, namespace.tables, namespace.scenario_file
        )
    except SystemExit as exit_request:
        return int(exit_request.code or EX_USAGE)
    except dump_tables.ScenarioFileError as exc:
        return _fail(str(exc), EX_USAGE)

    try:
        settings = dump_tables.connection_settings(os.environ)
    except dump_tables.ConnectionConfigError as exc:
        return _fail(str(exc), EX_ENVIRONMENT)

    status = 0
    lines: list[str] = []
    try:
        with dump_tables.connect(settings) as connection:
            for table in tables:
                try:
                    dump = dump_tables.dump_table(connection, table)
                except dump_tables.DumpError as exc:
                    # A table that cannot be read is REPORTED, not fatal: the record
                    # stays complete and comparable, and the far side can tell an
                    # unreadable table from an empty one. The reason goes to stderr,
                    # never into the record.
                    lines.append(f"{table}\t{UNREADABLE}\t{UNREADABLE}")
                    sys.stderr.write(
                        f"harness/table_digest.py: {table} could not be digested: "
                        f"{type(exc).__name__}: {exc}\n"
                    )
                    status = EX_UNREADABLE
                    continue
                lines.append(
                    f"{table}\t{int(dump['row_count'])}\t"
                    f"{digest_of(dump_tables, dump)}"
                )
    except (
        dump_tables.ConnectionConfigError,
        dump_tables.InsecureTransportError,
        dump_tables.DriverUnavailableError,
        dump_tables.DumpTimeoutError,
        dump_tables.DumpError,
        OSError,
    ) as exc:
        return _fail(f"{type(exc).__name__}: {exc}", EX_ENVIRONMENT)

    # One write, so a partial record cannot reach a caller that reads line by line.
    sys.stdout.write("".join(f"{line}\n" for line in lines))
    return status


if __name__ == "__main__":  # pragma: no cover - the command-line entry point
    raise SystemExit(main())
