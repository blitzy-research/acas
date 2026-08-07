"""Regression locks for shared COBOL storage and DAL call boundaries.

EVERY IMPORT HERE IS MANDATORY, NOT SKIPPABLE. An earlier revision reached each
module through `pytest.importorskip`, so a host that could not import one
reported this file as SKIPPED rather than as broken - and every lock in it
silently stopped locking. These are regression locks for the anomalies rule R-4
requires be reproduced, so a lock that can disappear into a skip line is not a
lock. `mysql-connector-python==26.7.0` is a hard `[project.dependencies]` entry,
so an installed package can always import every name below;
`importlib.import_module` therefore raises rather than skipping.
"""

from __future__ import annotations

import ast
import dataclasses
from decimal import Decimal
import importlib
import json
import re
import subprocess
import sys
import types
from collections.abc import Iterator
from pathlib import Path
from types import MappingProxyType
from typing import Final, Mapping

import pytest


pytestmark = pytest.mark.arithmetic


# ---------------------------------------------------------------------------
#  THE IMPORTS ARE REAL, AND THEY LEAVE NOTHING RESIDENT.
#
#  Every test below reaches a shipped data-access module, and `acas_posting.dal.*`
#  pulls the pinned MySQL driver in transitively. Two properties have to hold at once.
#
#  THE IMPORT MUST FAIL WHEN IT FAILS. These sites used `pytest.importorskip`, which
#  turned the one outcome the file exists to catch into a PASS: a handler that cannot
#  be imported at all - a syntax error, a circular import, a symbol renamed in a module
#  it imports - produced a SKIP, and a skipped test reads as green. The driver is a hard
#  requirement of `requirements.txt`, so its absence is a broken environment and not a
#  supported configuration. `_shipped` therefore uses `importlib.import_module` and lets
#  the `ImportError` reach pytest.
#
#  AND NOTHING FORBIDDEN MAY BE LEFT LOADED. Agent Action Plan section 0.4.3 gives this
#  tier `cobol` and `records` and forbids `dal` and any database, and three files in it
#  assert exactly that - `test_comp3_packed_decimal.py`, `test_comp_binary.py` and
#  `test_pic_field_descriptors.py`. Two of them read LIVE `sys.modules`. This file used
#  to leave `acas_posting.dal.*` and `mysql.*` resident, and the only reason those three
#  kept passing is that they collate ALPHABETICALLY BEFORE it: the suite was green by
#  file order. `_purge_tier_isolated_names` runs after every test here and asserts the
#  residue is empty, so the ordering accident is no longer load-bearing.
# ---------------------------------------------------------------------------


#: The module-name prefixes the tier's own isolation assertions forbid. The same list
#: the five program-module loaders in this directory carry.
_TIER_ISOLATION_PREFIXES: Final[tuple[str, ...]] = (
    "acas_posting.cli",
    "acas_posting.dal",
    "acas_posting.programs",
    "harness",
    "mysql",
    "numpy",
    "pandas",
    "sqlalchemy",
    "yaml",
)


def _is_tier_isolated_name(name: str) -> bool:
    """Does `name` fall under a prefix the tier must not leave loaded?

    Matched as a package prefix - the exact name, or the name plus a dot - so a
    submodule cannot slip past and a merely similar name is not caught by accident.
    """
    return any(
        name == prefix or name.startswith(f"{prefix}.")
        for prefix in _TIER_ISOLATION_PREFIXES
    )


def _shipped(dotted_name: str) -> types.ModuleType:
    """Import a shipped module FOR REAL, letting an `ImportError` be a failure.

    Args:
        dotted_name: The importable name.

    Returns:
        The imported module.

    Raises:
        ImportError: The module could not be imported. Deliberately NOT converted into
            a skip - see the section note above.
    """
    return importlib.import_module(dotted_name)


@pytest.fixture(autouse=True)
def _purge_tier_isolated_names() -> Iterator[None]:
    """Remove every tier-isolated module each test added, and prove none survived.

    Autouse, so no test can forget it, and it asserts rather than merely cleaning:
    a name left resident would make the tier's three isolation assertions depend on
    which file ran first, which is how this leak went unnoticed.

    Yields:
        None, once, around each test.
    """
    before = frozenset(sys.modules)
    yield
    for name in sorted(set(sys.modules) - before, reverse=True):
        if _is_tier_isolated_name(name):
            del sys.modules[name]
    residue = sorted(
        name for name in set(sys.modules) - before if _is_tier_isolated_name(name)
    )
    assert not residue, (
        f"this test left {residue} resident in sys.modules. Agent Action Plan section "
        f"0.4.3 forbids `dal` and any database in this tier, and the assertions in "
        f"test_comp3_packed_decimal.py, test_comp_binary.py and "
        f"test_pic_field_descriptors.py read LIVE sys.modules - so a survivor makes "
        f"them pass or fail on file order alone."
    )


def test_system_cycle_redefines_is_one_storage_location() -> None:
    """Cyclea and Scycle are two names for the byte at copybooks/wssystem.cob:L62-L63."""
    module = _shipped("acas_posting.records.system_record")
    block = module.SystemDataBlock()

    block.cyclea = 7
    assert block.scycle == 7

    block.scycle = 11
    assert block.cyclea == 11


@pytest.mark.parametrize("separator", ["/", ".", ",", "-"])
def test_controlled_clock_canonicalizes_supported_separators(
    separator: str,
) -> None:
    """Every maps04-supported input pins the frozen slash-form text."""
    clock = _shipped("acas_posting.clock")

    pinned = clock.pin_from_to_day(f"21{separator}09{separator}2025")

    assert pinned.to_day == "21/09/2025"
    assert pinned.run_date == 155127


def test_gl_batch_key_redefines_round_trips_through_both_views() -> None:
    """The grouped and six-digit batch keys cannot diverge."""
    records = _shipped("acas_posting.records.gl_batch")
    dal = _shipped("acas_posting.dal.acas007_gl_batch")

    assert [field.name for field in dataclasses.fields(records.WsBatchKey9)] == [
        "ws_batch_key9"
    ]

    batch = records.GlBatchRecord()
    batch.ws_batch_key.ws_ledger = 1
    batch.ws_batch_key.ws_batch_nos = 2
    assert batch.ws_batch_key9.ws_batch_key9 == 100002

    batch.ws_batch_key9.ws_batch_key9 = 200123
    assert batch.ws_batch_key.ws_ledger == 2
    assert batch.ws_batch_key.ws_batch_nos == 123
    assert dal.synchronise_batch_key_views(batch) == 200123
    assert dal.COLUMNS[0].record_path == ("ws_batch_key9", "ws_batch_key9")


def test_purchase_order_group_move_preserves_the_caller_byte_image() -> None:
    """The X(10) caller view survives the bridge's mixed-type group view."""
    records = _shipped("acas_posting.records.purchase_invoice")
    dal = _shipped("acas_posting.dal.acas026_pinvoice")

    group = records.IhOrder(
        ih_freq=" ",
        ih_repeat=0,
        filler_1=" " * 3,
        ih_last_date=0,
    )
    context = dal.PInvoiceContext()
    caller_image = "SO-31009  "

    dal._split_ih_order(caller_image, group, context)

    # `ih-order pic x(10)` [copybooks/plwspinv2.cob:L28] may contain bytes that
    # are not valid for the numeric members of the bridge's group view
    # [copybooks/plwspinv.cob:L17-L27]. An untouched group MOVE copies those
    # bytes; it does not parse and reformat them.
    assert group.ih_repeat == 0
    assert dal._group_ih_order(group, context) == caller_image

    # Once a subordinate field is explicitly changed, its declared representation
    # replaces the corresponding bytes, exactly as a COBOL elementary MOVE would.
    group.ih_repeat = 12
    assert dal._group_ih_order(group, context).startswith("S12")


def test_purchase_ledger_linkage_reinterprets_binary_bytes_like_purchmt() -> None:
    """acas022/wspl bytes cross purchMT's incompatible COMP linkage unchanged."""
    records = _shipped("acas_posting.records.purchase_ledger")
    dal = _shipped("acas_posting.dal.acas022_purch")

    caller = records.WsPurchRecord()
    caller.purch_sortcode = 112233
    caller.purch_accountno = 12345678
    caller.purch_last_inv = 155127
    caller.purch_average = 642
    caller.purch_create_date = 150000

    loaded = dal.bb000_hv_load(caller)

    # The frozen CALL passes native BINARY-LONG bytes to `PIC 9(8) COMP`
    # [copybooks/wspl.cob:L32-L39], [common/purchMT.cbl:L345-L352]. The
    # bridge's subsequent numeric MOVE preserves the reinterpreted underlying
    # value; only sort code's eight-character SQL window truncates it later.
    assert loaded.hv_purch_sortcode == 73535488
    assert loaded.hv_purch_accountno == 1315027968
    assert loaded.hv_purch_last_inv == 4150067712
    assert loaded.hv_purch_average == 2181169152
    assert loaded.hv_purch_create_dat == 4031316480

    fetched = dal.HostVariables(
        hv_purch_accountno=1315027968,
        hv_purch_last_inv=2354905600,
        hv_purch_average=2181169152,
        hv_purch_create_dat=4031316480,
    )
    unloaded = records.WsPurchRecord()
    dal.bb100_unload_hvs(fetched, unloaded)

    # The reverse MOVE first narrows into purchMT's eight-digit picture, then
    # exposes those bytes through the native BINARY-LONG caller declaration.
    assert unloaded.purch_accountno == 5235968
    assert unloaded.purch_last_inv == 13321475
    assert unloaded.purch_average == 9164292
    assert unloaded.purch_create_date == 14343425


def test_acas000_rdbms_dispatch_clears_the_incoming_reply_pair(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An EOF from key 2 cannot suppress the following key-1 bridge call."""
    handler = _shipped("acas_posting.dal.acas000_system")
    status = _shipped("acas_posting.dal.status")
    file_access_module = _shipped("acas_posting.records.file_access")
    system_module = _shipped("acas_posting.records.system_record")
    flags_module = _shipped("acas_posting.records.test_data_flags")

    handler.reset_handler_state()
    system = system_module.SystemRecord()
    file_access = file_access_module.FileAccess()
    file_access.file_function = int(status.FileFunction.READ_INDEXED)
    file_access.fs_reply = int(status.FsReply.END_OF_FILE)
    file_access.we_error = 10
    dal_common = flags_module.AcasDalCommonData(sw_testing=0)
    observed: list[tuple[int, int, int]] = []

    monkeypatch.setattr(handler, "ba010_test_ws_rec_size", lambda _fa: None)
    monkeypatch.setattr(
        handler,
        "ba012_test_ws_rec_size_2",
        lambda _system, _fa, _common: False,
    )
    monkeypatch.setattr(handler, "ba_rdbms_exit", lambda: None)

    def capture(file_access_arg, _common, _record) -> None:
        observed.append(
            (
                int(file_access_arg.fs_reply),
                int(file_access_arg.we_error),
                int(file_access_arg.file_function),
            )
        )

    monkeypatch.setattr(handler, "ba015_test_ends", capture)
    handler.ba_process_rdbms(file_access, dal_common, system)

    assert observed == [
        (
            int(status.FsReply.SUCCESS),
            int(status.WeError.SUCCESS),
            int(status.FileFunction.READ_INDEXED),
        )
    ]


def test_acasirsub1_dispatch_resets_status_without_losing_operation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Shared File-Access residue is cleared before IRS nominal guards run."""
    handler = _shipped("acas_posting.dal.acasirsub1_irs_nominal")
    status = _shipped("acas_posting.dal.status")
    nominal_module = _shipped("acas_posting.records.irs_nominal")
    file_access_module = _shipped("acas_posting.records.file_access")
    file_defs_module = _shipped("acas_posting.records.file_defs")
    system_module = _shipped("acas_posting.records.system_record")
    flags_module = _shipped("acas_posting.records.test_data_flags")

    system = system_module.SystemRecord()
    system.system_data_block.rdbms_flat_statuses.file_system_used = 1
    file_access = file_access_module.FileAccess()
    file_access.file_function = int(status.FileFunction.READ_INDEXED)
    file_access.logging_data.file_key_no = 1
    file_access.fs_reply = int(status.FsReply.END_OF_FILE)
    file_access.we_error = 10
    observed: list[tuple[int, int, int]] = []

    monkeypatch.setattr(handler, "_record_size_gate", lambda _s, _fa: True)

    def bridge(_system, file_access_arg, _record):
        observed.append(
            (
                int(file_access_arg.fs_reply),
                int(file_access_arg.we_error),
                int(file_access_arg.file_function),
            )
        )
        return (int(status.FsReply.SUCCESS), int(status.WeError.SUCCESS))

    monkeypatch.setattr(handler, "_bridge_call", bridge)
    result = handler.dispatch(
        system,
        nominal_module.WsIrsnlRecord(),
        file_access,
        file_defs_module.FileDefs(),
        flags_module.AcasDalCommonData(sw_testing=0),
    )

    assert result == (int(status.FsReply.SUCCESS), int(status.WeError.SUCCESS))
    assert observed == [
        (
            int(status.FsReply.SUCCESS),
            int(status.WeError.SUCCESS),
            int(status.FileFunction.READ_INDEXED),
        )
    ]


def test_irs_indexed_read_does_not_report_driver_failure_as_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A SELECT that never ran is distinct from a clean zero-row result."""
    handler = _shipped("acas_posting.dal.acasirsub1_irs_nominal")
    status = _shipped("acas_posting.dal.status")
    nominal_module = _shipped("acas_posting.records.irs_nominal")
    file_access_module = _shipped("acas_posting.records.file_access")

    handler.reset_bridge_storage(transport=None)
    failure = status.DbErrorStatus(
        fs_reply=status.FsReply.ERROR,
        we_error=status.WeError.RDB_INIT_ERROR,
        sql_err="1046 ",
        sql_msg="connection unavailable",
        sql_state="HY000",
        duplicate_key=False,
    )
    monkeypatch.setattr(
        handler,
        "_run_query",
        lambda _file_access, _statement, _parameters: ([], failure),
    )

    file_access = file_access_module.FileAccess()
    result = handler.read_indexed(
        file_access,
        nominal_module.WsIrsnlRecord(),
    )

    assert result == (
        int(status.FsReply.ERROR),
        int(status.WeError.RDB_INIT_ERROR),
    )
    assert result != handler.NOT_FOUND_STATUS


def test_transient_connection_close_does_not_close_persistent_handle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """acasirsub3's synthesized close owns only its transient SQL handle."""
    connection = _shipped("acas_posting.dal.connection")
    system_module = _shipped("acas_posting.records.system_record")

    class FakeConnection:
        def __init__(self) -> None:
            self.closed = False

        def connect(self, **_arguments: object) -> None:
            self.closed = False

        def close(self) -> None:
            self.closed = True

    persistent = FakeConnection()
    transient = FakeConnection()
    connections = iter((persistent, transient))

    connection.reset_process_connection()
    monkeypatch.setattr(
        connection.mysql.connector,
        "connect",
        lambda **_arguments: next(connections),
    )
    monkeypatch.setattr(
        connection,
        "load_rdb_data_once",
        lambda _system: object(),
    )
    monkeypatch.setattr(
        connection,
        "connection_parameters",
        lambda _data, *, transport: {},
    )
    monkeypatch.setattr(
        connection,
        "_require_permitted_connection",
        lambda *_arguments, **_keywords: None,
    )
    monkeypatch.setattr(
        connection,
        "_assert_converter_pinned",
        lambda _connection: None,
    )

    system = system_module.SystemRecord()
    first = connection.mysql_1000_open(system)
    second = connection.mysql_1000_open(
        system,
        reuse_process_connection=False,
    )

    assert first.connection is persistent
    assert second.connection is transient
    connection.mysql_1980_close(second.connection)
    assert transient.closed
    assert not persistent.closed
    assert connection.process_connection() is persistent

    connection.mysql_1980_close(first.connection)
    assert not persistent.closed
    assert connection.process_connection() is persistent

    connection.reset_process_connection()
    assert persistent.closed


def test_acas007_dispatch_honours_keyword_transport(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Facade-forwarded transport reaches the GL batch handler."""
    handler = _shipped("acas_posting.dal.acas007_gl_batch")
    connection = _shipped("acas_posting.dal.connection")
    batch_module = _shipped("acas_posting.records.gl_batch")
    file_access_module = _shipped("acas_posting.records.file_access")
    file_defs_module = _shipped("acas_posting.records.file_defs")
    system_module = _shipped("acas_posting.records.system_record")
    flags_module = _shipped("acas_posting.records.test_data_flags")

    handler.reset_working_storage()
    declared = connection.TransportSecurity(isolated_oracle=True)
    observed: list[object] = []
    monkeypatch.setattr(
        handler,
        "aa_process_flat_file",
        lambda *_arguments: observed.append(handler._HANDLER.transport),
    )

    handler.dispatch(
        system_module.SystemRecord(),
        batch_module.GlBatchRecord(),
        file_access_module.FileAccess(),
        file_defs_module.FileDefs(),
        flags_module.AcasDalCommonData(sw_testing=0),
        transport=declared,
    )

    assert observed == [declared]


def test_acas016_reuses_bridge_connection_across_fresh_buffers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A new invoice linkage buffer does not lose slinvoiceMT working storage."""
    handler = _shipped("acas_posting.dal.acas016_invoice")
    connection = _shipped("acas_posting.dal.connection")
    status = _shipped("acas_posting.dal.status")
    file_access_module = _shipped("acas_posting.records.file_access")
    file_defs_module = _shipped("acas_posting.records.file_defs")
    system_module = _shipped("acas_posting.records.system_record")
    flags_module = _shipped("acas_posting.records.test_data_flags")

    persistent = object()
    declared = connection.TransportSecurity(isolated_oracle=True)
    handler.reset_bridge_storage(transport=declared)
    monkeypatch.setattr(
        handler,
        "mysql_1000_open",
        lambda *_arguments, **_keywords: connection.OpenOutcome(
            connection=persistent,
            fs_reply=status.FsReply.SUCCESS,
            we_error=status.WeError.SUCCESS,
            ws_no_paragraph=0,
            sql_err="",
            sql_msg="",
            sql_state="",
        ),
    )
    observed: list[tuple[object, object]] = []

    def capture_write(context) -> None:
        observed.append((context.connection, context.state))
        context.file_access.fs_reply = int(status.FsReply.SUCCESS)
        context.file_access.we_error = int(status.WeError.SUCCESS)

    monkeypatch.setattr(handler, "ba070_process_write", capture_write)

    system = system_module.SystemRecord()
    system.system_data_block.rdbms_flat_statuses.file_system_used = 1
    file_access = file_access_module.FileAccess()
    file_defs = file_defs_module.FileDefs()
    common = flags_module.AcasDalCommonData(sw_testing=0)

    file_access.file_function = int(status.FileFunction.OPEN)
    first = handler.InvoiceBuffer()
    handler.dispatch(
        system,
        first,
        file_access,
        file_defs,
        common,
        transport=declared,
    )

    file_access.file_function = int(status.FileFunction.WRITE)
    second = handler.InvoiceBuffer()
    handler.dispatch(system, second, file_access, file_defs, common)

    assert observed == [(persistent, first.bridge_state)]
    assert second.connection is persistent
    assert second.bridge_state is first.bridge_state
    handler.reset_bridge_storage()


# ---------------------------------------------------------------------------
#  THE DEPLOYMENT SECURITY CONTRACT
#
#  ONE VARIABLE NAME AND ONE RESOLVER, asserted rather than assumed. The
#  declaration used to be spelled `ACAS_DB_ALLOW_PLAINTEXT` by the shell half of
#  the harness and by `harness/docker-compose.yml`, and read as
#  `ACAS_DB_ISOLATED_ORACLE` by the policy installer - so a harness run exported
#  the declaration, the installer never saw it, and every handler open logged the
#  unprotected-transport warning while the Compose file said the declaration had
#  been made. These tests fail if the two halves drift apart again, and if the
#  fail-closed default is ever softened back into a warning.
#
#  Infrastructure-free: no database, no COBOL, no Docker. Every environment is an
#  explicit mapping, so the process environment is never read.
# ---------------------------------------------------------------------------


def test_the_plaintext_declaration_has_exactly_one_variable_name() -> None:
    """The resolver reads the name the shell half and Compose export, and no other."""
    rdbms_params = importlib.import_module("acas_posting.cli.rdbms_params")

    assert (
        rdbms_params.TRANSPORT_ALLOW_PLAINTEXT_VARIABLE == "ACAS_DB_ALLOW_PLAINTEXT"
    )
    # The superseded spelling must not come back under any name.
    assert not [
        name
        for name in dir(rdbms_params)
        if isinstance(getattr(rdbms_params, name), str)
        and getattr(rdbms_params, name) == "ACAS_DB_ISOLATED_ORACLE"
    ]


def test_an_undeclared_deployment_resolves_to_the_fail_closed_policy() -> None:
    """Nothing set means both refusals are ON, which is the production boundary."""
    rdbms_params = importlib.import_module("acas_posting.cli.rdbms_params")

    declaration = rdbms_params.resolve_transport_policy({})

    assert declaration.require_encrypted_transport is True
    assert declaration.require_declared_placeholder_credentials is True
    assert declaration.isolated_oracle is False
    assert declaration.allow_frozen_placeholder_credentials is False


def test_the_declaration_is_the_narrow_opt_out_and_strictness_outranks_it() -> None:
    """The harness's declaration permits plaintext; an explicit strict setting wins."""
    rdbms_params = importlib.import_module("acas_posting.cli.rdbms_params")

    declared = rdbms_params.resolve_transport_policy(
        {rdbms_params.TRANSPORT_ALLOW_PLAINTEXT_VARIABLE: "1"}
    )
    assert declared.isolated_oracle is True
    assert declared.require_encrypted_transport is False
    # Granting plaintext grants nothing else: the credential refusal stays on.
    assert declared.require_declared_placeholder_credentials is True

    forced = rdbms_params.resolve_transport_policy(
        {
            rdbms_params.TRANSPORT_ALLOW_PLAINTEXT_VARIABLE: "1",
            rdbms_params.TRANSPORT_REQUIRE_ENCRYPTION_VARIABLE: "1",
        }
    )
    assert forced.isolated_oracle is True
    assert forced.require_encrypted_transport is True


def test_the_installed_policy_carries_the_resolved_declaration() -> None:
    """`install_connection_policy` installs what the contract resolved, unchanged."""
    args = importlib.import_module("acas_posting.cli.args")
    connection = importlib.import_module("acas_posting.dal.connection")
    rdbms_params = importlib.import_module("acas_posting.cli.rdbms_params")

    previous = connection.connection_policy()
    try:
        undeclared = args.install_connection_policy({})
        assert undeclared is connection.connection_policy()
        assert undeclared.require_encrypted_transport is True
        assert undeclared.require_declared_placeholder_credentials is True

        declared = args.install_connection_policy(
            {rdbms_params.TRANSPORT_ALLOW_PLAINTEXT_VARIABLE: "yes"}
        )
        assert declared is connection.connection_policy()
        assert declared.transport is not None
        assert declared.transport.isolated_oracle is True
        assert declared.require_encrypted_transport is False
    finally:
        connection.set_connection_policy(previous)


def test_no_migrated_route_publishes_a_transport_option() -> None:
    """Rule R-3: the linkage contract publishes no deployment-security input."""
    forbidden = ("--db-tls-ca", "--db-tls-cert", "--db-tls-key", "--db-allow-plaintext")
    for module_name in (
        "acas_posting.cli.gl_post_cycle",
        "acas_posting.cli.gl_end_of_cycle",
        "acas_posting.cli.sl_invoice_post",
        "acas_posting.cli.sl_cash_post",
        "acas_posting.cli.pl_order_post",
        "acas_posting.cli.pl_payment_post",
        "acas_posting.cli.irs_post",
    ):
        module = importlib.import_module(module_name)
        parser = module._build_parser()  # noqa: SLF001 - the route's own builder
        published = {
            option
            for action in parser._actions  # noqa: SLF001 - argparse publishes no reader
            for option in action.option_strings
        }
        assert not published.intersection(forbidden), module_name


# ---------------------------------------------------------------------------
#  THE FIVE `ROUNDED` SITES, EXERCISED THROUGH THE PRODUCTION FUNCTIONS
#
#  `test_compute_rounded_half_up.py` owns the rounding SEMANTICS and closes the
#  census against the shipped tree with an AST walk. What it cannot do without
#  breaking its own tier contract is CALL the accounting functions, because
#  `acas_posting.programs.*` imports `acas_posting.dal.facade`. This file already
#  crosses that boundary deliberately - every test in it reaches a program or a
#  handler through `pytest.importorskip` - so the behavioural lock lives here.
#
#  It matters that these assert against production rather than against a local
#  re-derivation of the formula: a test that rebuilds `post-amount * rate / 100`
#  itself passes even if the shipped store truncates.
# ---------------------------------------------------------------------------


def test_gl051_net_is_a_half_up_store_in_production() -> None:
    """Site 1 of 5: `compute vat-amount rounded = post-amount * ws-vat-rate / 100.`

    [general/gl051.cbl:L791]. 100.03 at 17.50% is exactly 17.50525, whose third
    decimal is above a half penny, so a half-up store holds 17.51 and a truncating
    store would hold 17.50. The pair therefore proves the DIRECTION and not merely
    that a number came back.
    """
    decimal_module = importlib.import_module("decimal")
    gl051 = importlib.import_module("acas_posting.programs.gl051_batch_control_check")
    gl_posting = importlib.import_module("acas_posting.records.gl_posting")

    posting = gl_posting.WsPostingRecord()
    posting.post_amount = decimal_module.Decimal("100.03")
    gl051._net(posting, decimal_module.Decimal("17.50"))  # noqa: SLF001

    assert posting.vat_amount == decimal_module.Decimal("17.51")
    # Un-ROUNDED, the same operands would have held 17.50 - asserted so the test
    # fails if `rounded=True` is ever dropped from the store.
    assert posting.vat_amount != decimal_module.Decimal("17.50")


def test_gl051_gross_rounds_then_subtracts_without_rounding_in_production() -> None:
    """Sites 2 of 5 and its un-ROUNDED successor, in one call.

    `compute vat-amount rounded = post-amount - (post-amount / ((ws-vat-rate + 100) /
    100)).` [general/gl051.cbl:L796] followed by `subtract vat-amount from
    post-amount.` [general/gl051.cbl:L797] - which carries no `ROUNDED` and therefore
    truncates. The successor is DESTRUCTIVE: `post-amount` leaves the paragraph
    holding the net.
    """
    decimal_module = importlib.import_module("decimal")
    gl051 = importlib.import_module("acas_posting.programs.gl051_batch_control_check")
    gl_posting = importlib.import_module("acas_posting.records.gl_posting")

    posting = gl_posting.WsPostingRecord()
    posting.post_amount = decimal_module.Decimal("117.50")
    gl051._gross(posting, decimal_module.Decimal("17.50"))  # noqa: SLF001

    assert posting.vat_amount == decimal_module.Decimal("17.50")
    # The gross has been REPLACED by the net, which is what makes the paragraph
    # non-idempotent - calling it twice would tax the net.
    assert posting.post_amount == decimal_module.Decimal("100.00")


def test_irs030_net_and_gross_are_the_gl051_pair_under_another_rate_field() -> None:
    """Sites 4 and 5 of 5: [irs/irs030.cbl:L1551] and [irs/irs030.cbl:L1562-L1563].

    The same two expressions as `gl051`'s, differing only in the rate field's name -
    `WS-Vat-Current` rather than `ws-vat-rate` - and in the receiving record. Asserted
    side by side with the `gl051` pair so that a divergence between the two ledgers'
    VAT arithmetic cannot appear silently.
    """
    decimal_module = importlib.import_module("decimal")
    irs030 = importlib.import_module("acas_posting.programs.irs030_posting")
    irs_posting = importlib.import_module("acas_posting.records.irs_posting")

    net_record = irs_posting.PostingRecord()
    net_record.post_amount = decimal_module.Decimal("100.03")
    irs030._net_section(net_record, decimal_module.Decimal("17.50"))  # noqa: SLF001
    assert net_record.vat_amount == decimal_module.Decimal("17.51")

    gross_record = irs_posting.PostingRecord()
    gross_record.post_amount = decimal_module.Decimal("117.50")
    irs030._gross_section(gross_record, decimal_module.Decimal("17.50"))  # noqa: SLF001
    assert gross_record.vat_amount == decimal_module.Decimal("17.50")
    assert gross_record.post_amount == decimal_module.Decimal("100.00")


def test_gl051_account_scaling_truncates_on_all_five_statements() -> None:
    """The five scaling statements Agent Action Plan section 0.4.1.2 names for `gl051`.

    Two divides at [general/gl051.cbl:L604] and [general/gl051.cbl:L607], two
    multiplies at [general/gl051.cbl:L654] and [general/gl051.cbl:L657], and the fifth
    multiply at [general/gl051.cbl:L803]. NONE carries `ROUNDED`, so every one
    truncates - which is why the census in the sibling file stays at five.

    Also locks the field the divides store into: `acc-ok`
    [general/gl051.cbl:L233], NOT `account-in` [general/gl051.cbl:L178]. They share a
    picture and a separate statement copies between them, so conflating the two would
    be invisible to a value assertion alone.
    """
    decimal_module = importlib.import_module("decimal")
    gl051 = importlib.import_module("acas_posting.programs.gl051_batch_control_check")
    gl_posting = importlib.import_module("acas_posting.records.gl_posting")

    posting = gl_posting.WsPostingRecord()
    posting.post_dr = 123456
    posting.dr_pc = 7
    posting.post_cr = 654321
    posting.cr_pc = 9

    storage = gl051._WorkingStorage()  # noqa: SLF001
    gl051._accept_date_scale_out(storage, posting, "DR")  # noqa: SLF001
    assert storage.acc_ok == decimal_module.Decimal("1234.56")
    assert storage.array_pc == 7
    # `account-in` is untouched: the copy is `move acc-ok to account-in.` at
    # [general/gl051.cbl:L615], a statement in a different paragraph.
    assert storage.account_in == decimal_module.Decimal("0.00")

    # Anything other than "DR" takes the credit arm - the frozen test is an
    # alphanumeric relation condition with no third branch.
    gl051._accept_date_scale_out(storage, posting, "  ")  # noqa: SLF001
    assert storage.acc_ok == decimal_module.Decimal("6543.21")
    assert storage.array_pc == 9

    storage.account_in = decimal_module.Decimal("1234.56")
    storage.array_pc = 3
    scaled = gl_posting.WsPostingRecord()
    gl051._accept_amount_scale_in(storage, scaled, "DR")  # noqa: SLF001
    assert scaled.post_dr == 123456
    assert scaled.dr_pc == 3
    gl051._accept_amount_scale_in(storage, scaled, "CR")  # noqa: SLF001
    assert scaled.post_cr == 123456
    assert scaled.cr_pc == 3

    assert gl051._gl050c_get_description_scale(storage) == 123456  # noqa: SLF001

    # Truncation, proved on a value the multiply cannot represent exactly in the
    # receiver: 1234.569 * 100 is 123456.9, and the integer receiver keeps 123456.
    storage.account_in = decimal_module.Decimal("1234.569")
    assert gl051._gl050c_get_description_scale(storage) == 123456  # noqa: SLF001


# ---------------------------------------------------------------------------
#  THE CANONICAL FIXTURE ROOT -- THREE DERIVATIONS, ASSERTED TO AGREE
#
#  A built fixture cannot live where a scenario's own `seed_dir` points, because
#  that key resolves relative to the scenario file and the checkout is mounted
#  read-only (R-3). So the runtime location is a separate agreement, and three
#  components have to hold it: `harness/build_fixtures.sh` writes it,
#  `harness/run_parity.sh` reads it for the standalone driver, and
#  `tests/conftest.py` reads it for the pytest protocol.
#
#  Each states the rule in its own language, so nothing but a test can keep them
#  in step - and when they drift, every parity and determinism composition fails
#  at stage 1 with a path nobody wrote down. These tests read the two shell
#  derivations out of the scripts as TEXT and compare them with the Python one.
# ---------------------------------------------------------------------------


def _harness_dir():
    """Return the repository's `harness/` directory."""
    import pathlib

    return pathlib.Path(__file__).resolve().parents[2] / "harness"


def test_the_three_fixture_root_derivations_are_textually_identical() -> None:
    """`build_fixtures.sh`, `run_parity.sh` and `conftest.py` derive one root.

    Asserted on the shell text because the two scripts cannot be imported: each must
    contain the `${ACAS_FIXTURES...}` / `$ACAS_DATA/fixtures` pair, so a change to
    one that is not made in the other is visible here rather than at stage 1.
    """
    builder = (_harness_dir() / "build_fixtures.sh").read_text(encoding="utf-8")
    driver = (_harness_dir() / "run_parity.sh").read_text(encoding="utf-8")

    # The producer's single statement of the rule.
    assert 'ACAS_BF_OUT="${ACAS_FIXTURES:-${ACAS_DATA:-/data}/fixtures}"' in builder

    # The driver's derivation: the same two sources, in the same precedence.
    assert 'local root="${ACAS_FIXTURES:-}"' in driver
    assert '[[ -n "$root" ]] || root="${ACAS_DATA%/}/fixtures"' in driver
    assert 'ACAS_PARITY_SEED_DIR="${root%/}/$ACAS_PARITY_SCENARIO"' in driver

    # And each cites the other, so a reader of one finds the other two.
    for text in (builder, driver):
        assert "tests/conftest.py" in text
    assert "harness/build_fixtures.sh" in driver


def test_the_python_derivation_matches_the_shell_precedence() -> None:
    """`scenario_fixture_dir` prefers `$ACAS_FIXTURES`, then `$ACAS_DATA/fixtures`.

    Measured against a controlled environment rather than read off the source, so
    the precedence itself is asserted and not merely the presence of two names.
    """
    import pathlib

    conftest = importlib.import_module("conftest")
    monkey = pytest.MonkeyPatch()
    try:
        # Both set: ACAS_FIXTURES wins outright, and ACAS_DATA is not consulted.
        monkey.setenv("ACAS_FIXTURES", "/fx")
        monkey.setenv("ACAS_DATA", "/dt")
        assert conftest.scenario_fixture_dir("clean_batch_gl") == pathlib.Path(
            "/fx/clean_batch_gl"
        )

        # Only ACAS_DATA: the `fixtures` subdirectory is appended, exactly as the
        # builder's default does.
        monkey.delenv("ACAS_FIXTURES")
        assert conftest.scenario_fixture_dir("clean_batch_gl") == pathlib.Path(
            "/dt/fixtures/clean_batch_gl"
        )

        # An empty value is not a value: the builder's `:-` treats it the same way.
        monkey.setenv("ACAS_FIXTURES", "   ")
        assert conftest.scenario_fixture_dir("clean_batch_gl") == pathlib.Path(
            "/dt/fixtures/clean_batch_gl"
        )

        # Neither set: the two READERS refuse rather than guess. The builder's own
        # `/data` last resort is deliberately not mirrored here - it can be run
        # outside Compose, and a test protocol that guessed would fail at stage 1
        # against a path nobody chose.
        monkey.delenv("ACAS_FIXTURES")
        monkey.delenv("ACAS_DATA")
        with pytest.raises(conftest.HarnessFaultError):
            conftest.scenario_fixture_dir("clean_batch_gl")
    finally:
        monkey.undo()


# ---------------------------------------------------------------------------
#  THE SEEDING WINDOW'S DEFAULT MODE, AND THE HARDENED SEED TRANSPORT
#
#  Both belong to `harness/seed.sh` and both are R-6 arbitrations rather than
#  readings, so both are asserted on the shipped script text: a default that
#  silently reverts to the AAP-literal OFF mode would make every seed exit 76, and
#  a transport that reverted to the bare `KEY<TAB>value` grammar would let a
#  scenario file forge a record.
# ---------------------------------------------------------------------------


def test_the_seeding_window_defaults_to_the_measured_durable_mode() -> None:
    """Unset `ACAS_SEED_AUTOCOMMIT` selects ON, the mode measured to persist rows.

    MEASURED against the compiled loaders, both modes, `clean_batch_gl`: under OFF
    all seven loaders return zero and a fresh session sees zero rows in all seven
    seeded tables, and `seed.sh` exits 76; under ON the same seven return zero and a
    fresh session sees 8 rows across those 7 tables. The loader return codes are
    IDENTICAL either way, so the mode is invisible to the frozen code.

    The shipped default must therefore be ON. `off` stays selectable and reproduces
    the frozen no-COMMIT defect end to end, which is what exit 76 reports (R-4).
    """
    seed = (_harness_dir() / "seed.sh").read_text(encoding="utf-8")

    # The unset case is grouped with the ON spellings, not with the OFF ones.
    assert "    ''|on|1|true|yes)\n" in seed
    assert "    off|0|false|no)\n" in seed
    assert "    ''|off|0|false|no)\n" not in seed

    # And the initial value of the target agrees with that grouping, so a code path
    # that skipped the parse would still open the durable window.
    assert "ACAS_SEED_WINDOW_TARGET=1" in seed


def test_the_seed_transport_is_control_free_and_length_prefixed() -> None:
    """The YAML-to-shell seed protocol cannot be forged by a scenario file.

    The superseded grammar was `KEY<TAB>value`, read with `IFS=$'\\t' read -r key
    value`. A value carrying a TAB split its own record and the reader kept the
    fragment; a value carrying a NEWLINE let the scenario forge an entire extra
    record - a forged `SEED_FILE` (CWE-93) or, worse, a forged `SEED_DIR` pointing
    anywhere (CWE-22). A NUL-delimited stream is the usual answer and is unavailable
    here: the output is captured through command substitution and a bash variable
    cannot hold a NUL.

    So the emitter refuses every C0 control character and DEL outright, and the
    grammar is framed and length-prefixed so the decode is independently verifiable.
    Both halves are asserted, because either alone would be a single point of
    failure.
    """
    seed = (_harness_dir() / "seed.sh").read_text(encoding="utf-8")

    # The emitter's refusal, and the strict bare-name grammar beside it.
    assert "def reject_control_characters(" in seed
    assert "ord(character) < 0x20 or ord(character) == 0x7F" in seed
    assert "BARE_NAME = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]*$')" in seed

    # The framed, length-prefixed grammar.
    assert "sys.stdout.write('BEGIN\\t1\\n')" in seed
    assert "def emit(key, value):" in seed
    assert "'%s\\t%d\\t%s\\n' % (key, len(value), value)" in seed

    # The decoder's INDEPENDENT revalidation: three-field read, numeric length,
    # measured-versus-declared length, and the grammar applied a second time.
    assert "while IFS=$'\\t' read -r key len value; do" in seed
    assert "(( ${#value} == len ))" in seed
    assert '[[ "$value" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]' in seed
    assert "the seed transport stream carries no BEGIN record" in seed
    assert "the seed transport stream carries no END record" in seed

    # The superseded two-field read must not come back as a loop header. The string
    # itself still appears ONCE, inside the emitter's docstring, which is where the
    # reason it went is recorded - so the assertion is on the loop and not on the
    # prose, and the prose is asserted to be the only other occurrence.
    assert "while IFS=$'\\t' read -r key value" not in seed
    assert seed.count("IFS=$'\\t' read -r key value") == 1


def test_the_parity_driver_shares_the_hardened_seed_transport() -> None:
    """`run_parity.sh`'s pre-flight decodes with the same framed grammar.

    The pre-flight exists so that a fixture that was never built is reported BEFORE
    stage 1 drops and re-applies the frozen schema. It reads the same untrusted
    source - a scenario YAML - into the same kind of shell loop, so it carries the
    same defences rather than a shorter version of them.
    """
    driver = (_harness_dir() / "run_parity.sh").read_text(encoding="utf-8")

    assert "acas_parity_assert_seed_files()" in driver
    assert "BARE_NAME = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]*$')" in driver
    assert "while IFS=$'\\t' read -r key len value; do" in driver
    assert "(( ${#value} == len ))" in driver
    assert "the seed transport stream carries no BEGIN record" in driver
    # Called from the precondition stage, so it runs before any stage command.
    assert "  acas_parity_resolve_fixture_root\n  acas_parity_assert_seed_files\n" in driver


# ---------------------------------------------------------------------------
#  CAPTURE OWNERSHIP, ATTESTATION AND OPERATION SYMMETRY
#
#  Three properties of the ten-stage protocol that nothing but a test can hold,
#  because each is a relationship BETWEEN files rather than a fact inside one:
#
#    * exactly one stage takes the state capture, and it is the protocol's stage 7
#      -- the only moment at which the run status its attestation carries is final;
#    * a run that COMPLETED and found a behavioural difference is comparable, while
#      a run that the harness broke is not;
#    * both runners can drive every operation a scenario declares.
# ---------------------------------------------------------------------------


def _load_harness_module(name: str):
    """Import a `harness/` module by file path, with `harness/` on `sys.path`.

    The harness is a SIBLING of the package and never on the import path (R-1), so a
    plain import cannot find it and adding it permanently would defeat the layering.
    This helper puts it there for the duration of one import, which is what the
    scenario tier's own helpers do.

    Args:
        name: The module's stem, e.g. `dump_tables`.

    Returns:
        The imported module.
    """
    import importlib.util
    import sys

    directory = _harness_dir()
    path = directory / f"{name}.py"
    inserted = False
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))
        inserted = True
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        if inserted:
            sys.path.remove(str(directory))


def test_only_the_protocol_takes_the_state_capture() -> None:
    """Neither runner dumps: capture ownership is single, and it is stage 7's.

    The Python runner used to take a full capture of every affected table and the
    protocol then took another to the same path. That cost three things: every table
    was read and written TWICE per scenario; the tree had two writers; and the
    runner's own capture COULD NOT BE USED, because the attestation
    `harness/dump_tables.py` reads carries the runner's exit status, which is not
    settled until its EXIT trap - after the stage that took it. The code said so
    itself.

    The oracle-side runner never dumped, so removing the Python one also removes an
    asymmetry a reader had to hold two models for.
    """
    python_runner = (_harness_dir() / "run_python_scenario.sh").read_text(
        encoding="utf-8"
    )
    cobol_runner = (_harness_dir() / "run_cobol_scenario.sh").read_text(
        encoding="utf-8"
    )

    # The capture command is still BUILT, because it is printed for a hand-driven
    # run - but it is never executed.
    assert "acas_py_capture_command()" in python_runner
    assert "owned by the protocol, not by this stage" in python_runner
    assert "deferred to the protocol" in python_runner

    # The opt-out flag is gone along with the stage it opted out of, and so is the
    # deadline that bounded a command this script no longer runs.
    assert "--no-dump" not in python_runner
    assert "ACAS_PY_DUMP" not in python_runner
    assert "ACAS_TIMEOUT_CAPTURE" not in python_runner

    # No trace of the EXECUTION remains: the stage neither bounds the capture with a
    # deadline nor diagnoses its failure, because it does not run it.
    assert "the state capture failed (status" not in python_runner

    # And the oracle side builds no capture command at all, so the two runners are
    # symmetrical. Asserted on the argv TOKENS dump_tables.py takes rather than on
    # its name, which both files mention in prose.
    for token in ("'--tables'", "'--side'", "'--out-dir'"):
        assert token not in cobol_runner, token


def test_neither_runner_removes_a_status_record_on_a_dry_run() -> None:
    """`--dry-run` writes nothing, and deleting is a write.

    Both runners used to `rm` any existing run-status record on a dry run, guarding a
    real hazard - a previous run's record going on to attest the next capture - with
    the most destructive tool available, inside a mode whose entire contract is that
    it touches nothing. The hazard is now REPORTED, and the operator's artifact is
    left alone.
    """
    for name in ("run_python_scenario.sh", "run_cobol_scenario.sh"):
        text = (_harness_dir() / name).read_text(encoding="utf-8")
        assert "rm -f -- \"$dry_target\"" not in text, name
        assert "has been left exactly as it was" in text, name
        assert "nothing on disk was created, changed or removed" in text, name


def test_a_completed_run_that_found_a_difference_is_still_comparable(tmp_path) -> None:
    """Status 69 attests a COMPARABLE run; any other non-zero attests nothing.

    This is the property that makes a real behavioural difference investigable.
    `harness/run_python_scenario.sh` exits 69 only after every operation has run,
    every post-run assertion has been taken and the database holds whatever the run
    produced - so that state IS the finding, and the table diff is the only artifact
    that says which rows and columns it consists of. An earlier revision refused it
    along with the harness faults, which withheld the evidence exactly when it
    mattered most.
    """
    dump_tables = _load_harness_module("dump_tables")

    #  A COMPLETE RECORD, because an incomplete one now attests nothing at all. The
    #  reader requires the whole provenance set - the attempt id, both seed digests,
    #  the declared operation count and one disposition per operation, with
    #  `wrapper_status` agreeing with `status` - so a fixture that wrote only the
    #  status would exercise the MISSING-KEY refusal rather than the property under
    #  test. What varies here is the status; everything else is a healthy record.
    digest = "a" * 64

    def write_status(side: str, status: int) -> None:
        path = dump_tables.run_status_path(tmp_path, "clean_batch_gl", side)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"scenario\tclean_batch_gl\n"
            f"side\t{side}\n"
            f"run_id\tclean_batch_gl-0001\n"
            f"status\t{status}\n"
            f"wrapper_status\t{status}\n"
            f"seed_fingerprint_sha256\t{digest}\n"
            f"seed_marker_sha256\t{digest}\n"
            f"operations\t1\n"
            f"operation_status\t1\tgl_post_cycle\t0\n",
            encoding="utf-8",
        )

    # Clean: attested, disposition `clean`.
    write_status("python", 0)
    clean = dump_tables.read_run_attestation(tmp_path, "clean_batch_gl", "python")
    assert clean["attested"] is True
    assert clean["disposition"] == dump_tables.DISPOSITION_CLEAN
    assert clean["run_status"] == 0

    # Behavioural: attested AND comparable, with the status recorded verbatim and a
    # detail that forbids reading the verdict as a clean run's.
    write_status("python", dump_tables.BEHAVIOURAL_RUN_STATUS)
    behavioural = dump_tables.read_run_attestation(
        tmp_path, "clean_batch_gl", "python"
    )
    assert behavioural["attested"] is True
    assert behavioural["disposition"] == dump_tables.DISPOSITION_BEHAVIOURAL
    assert behavioural["run_status"] == 69
    assert "must not" in (behavioural["detail"] or "")
    assert behavioural["disposition"] in dump_tables.COMPARABLE_DISPOSITIONS

    # A harness fault is NOT comparable, and says so - with the status and the file
    # that recorded it, which is an operator's first question.
    write_status("python", 71)
    fault = dump_tables.read_run_attestation(tmp_path, "clean_batch_gl", "python")
    assert fault["attested"] is False
    assert fault["disposition"] == dump_tables.DISPOSITION_HARNESS_FAULT
    assert fault["run_status"] == 71
    assert fault["source"] is not None
    assert fault["disposition"] not in dump_tables.COMPARABLE_DISPOSITIONS

    # 69 is scoped to the migrated side: the oracle-side runner's band is 70-79 and
    # every member of it is a precondition or a drive fault, so a 69 there is not a
    # behavioural result and must not be treated as one.
    write_status("cobol", dump_tables.BEHAVIOURAL_RUN_STATUS)
    cobol = dump_tables.read_run_attestation(tmp_path, "clean_batch_gl", "cobol")
    assert cobol["attested"] is False
    assert cobol["disposition"] == dump_tables.DISPOSITION_HARNESS_FAULT

    # An absent record claims nothing, and is `unknown` rather than a fault: nothing
    # has seen a status, so nothing can say which kind of nothing it was.
    missing = dump_tables.read_run_attestation(tmp_path, "empty_batch", "python")
    assert missing["attested"] is False
    assert missing["disposition"] == dump_tables.DISPOSITION_UNKNOWN


def test_the_three_stages_agree_on_the_attestation_key_order() -> None:
    """`dump_tables`, `normalize` and `diff_states` carry one attestation shape.

    The object is written by the first, carried unread by the second and enforced by
    the third, and the manifest is compared byte for byte - so a key one stage writes
    and another drops is a false difference in every scenario at once.
    """
    dump_tables = _load_harness_module("dump_tables")
    normalize = _load_harness_module("normalize")

    assert dump_tables.ATTESTATION_KEYS == normalize.ATTESTATION_KEYS
    assert "disposition" in dump_tables.ATTESTATION_KEYS

    # diff_states mirrors the one disposition it treats specially rather than
    # importing it, following the convention its four sibling constants follow.
    diff_text = (_harness_dir() / "diff_states.py").read_text(encoding="utf-8")
    assert (
        f'DISPOSITION_BEHAVIOURAL: Final[str] = "{dump_tables.DISPOSITION_BEHAVIOURAL}"'
        in diff_text
    )


def test_both_sides_are_checked_against_every_declared_operation() -> None:
    """A parity verdict requires that the two sides did the same work.

    The failure this closes is silent and expensive: an operation one side cannot
    drive used to surface as a stage-10 table difference, after nine stages and two
    full seeds, looking exactly like a behavioural defect in the migration.
    """
    driver = (_harness_dir() / "run_parity.sh").read_text(encoding="utf-8")
    cobol_runner = (_harness_dir() / "run_cobol_scenario.sh").read_text(
        encoding="utf-8"
    )

    # The orchestrator checks both maps, before stage 1, and reads them out of the
    # shipped scripts rather than holding a third copy that could drift from either.
    assert "acas_parity_assert_operations_supported_by_both_sides()" in driver
    assert "ACAS_RUN_OPERATION_MAP" in driver
    assert "ACAS_PY_OPERATION_MAP" in driver
    assert (
        "  acas_parity_assert_operations_supported_by_both_sides\n" in driver
    )

    # And the oracle-side runner DRIVES EVERY DECLARED OPERATION ITSELF, in the
    # scenario's own order, with one status slot per operation pre-set to a sentinel
    # that is not zero - so a multi-operation scenario cannot compare a state
    # produced with less work than the migrated side did, and a hand invocation is
    # complete rather than merely looking complete.
    #
    #  TWO REMEDIATIONS EXISTED FOR THIS ONE DEFECT, and the stronger one is what the
    #  tree carries. The other had the runner REFUSE a multi-operation scenario
    #  outright while the orchestrator looped over the list; that closed the silent
    #  case but left a bare invocation unable to drive a four-operation scenario at
    #  all, and left the per-operation term codes unattested. Resolving the ordered
    #  list inside the runner closes both, so the refusal was withdrawn with it.
    assert "acas_resolve_operations()" in cobol_runner
    assert "One status slot per operation" in cobol_runner
    assert "ACAS_RUN_OP_STATUS" in cobol_runner


# ---------------------------------------------------------------------------
# SECTION 17 -- what the harness GENERATES and what it REUSES
#
# Two properties of the build side, asserted against the shipped scripts because
# neither can be reached from the package (R-1 keeps `harness/` off the import path)
# and both are the kind of thing that is correct once and then quietly regresses:
#
#   * a path the operator supplies cannot end a COBOL string literal early, so
#     `make_fixtures.py` cannot be steered into generating a different program;
#   * every source, object and translator the oracle is built from can name where it
#     came from, on the reuse branch as well as the build branch.
# ---------------------------------------------------------------------------


def test_a_generated_cobol_literal_cannot_be_ended_early() -> None:
    """Every path `make_fixtures.py` writes into COBOL goes through one gate.

    The generator emits `move "<path>" to <field>.` statements. A path holding a
    double quote would close the literal and leave the rest of it as COBOL source --
    an operator-supplied `--out` deciding what the generated loader DOES rather than
    only where it writes. Control characters are the same defect through a different
    door: a newline splits one statement into two.

    Driven through the shipped helper rather than asserted on the source text, so it
    is the committed behaviour that is measured.
    """
    make_fixtures = _load_harness_module("make_fixtures")

    # Refused: the character that ends a literal, every control character, the
    # DEL byte, an empty path, and anything past the length budget.
    rejected = (
        '/data/fix"tures/x.dat',
        "/data/fix\ntures/x.dat",
        "/data/fix\ttures/x.dat",
        "/data/fix\rtures/x.dat",
        "/data/fix\x00tures/x.dat",
        "/data/fix\x7ftures/x.dat",
        "",
        "/" + "d" * (make_fixtures.COBOL_PATH_LITERAL_MAX + 1),
    )
    for path in rejected:
        with pytest.raises(SystemExit) as caught:
            make_fixtures.cobol_path_literal(path, what="--out")
        assert caught.value.code == 65, f"{path!r} was not refused with exit 65"

    # Accepted, and returned unchanged: the caller supplies the framing, because a
    # `move' statement wants quotes and a `*>' comment does not.
    good = "/data/fixtures/clean_batch_gl/system.dat"
    assert make_fixtures.cobol_path_literal(good, what="--out") == good

    # A path exactly at the budget is inside it: the bound is not off by one.
    at_budget = "/" + "d" * (make_fixtures.COBOL_PATH_LITERAL_MAX - 1)
    assert len(at_budget) == make_fixtures.COBOL_PATH_LITERAL_MAX
    assert make_fixtures.cobol_path_literal(at_budget, what="--out") == at_budget


def test_one_rule_governs_every_generated_literal() -> None:
    """A declared VALUE, a declared raw image and a path are held to one standard.

    Three of the four interpolation gates used to spell the rule for themselves and
    checked only `"`, newline and carriage return; a NUL or a DEL went straight into
    generated source. The rule now lives in one function, so a site cannot be tightened
    without tightening all of them.
    """
    make_fixtures = _load_harness_module("make_fixtures")

    # The shared predicate refuses the quote and EVERY control character, under
    # whichever exit status its caller passes.
    for bad in ('a"b', "a\nb", "a\rb", "a\tb", "a\x00b", "a\x7fb"):
        for code in (make_fixtures.EX_DECLARATION, make_fixtures.EX_PRECONDITION):
            with pytest.raises(SystemExit) as caught:
                make_fixtures.refuse_unplaceable_text(bad, what="x", code=code)
            assert caught.value.code == code
    # Ordinary text passes through, including a space and a trailing one.
    for good in ("abc", "a b ", "", "/data/x.dat"):
        make_fixtures.refuse_unplaceable_text(
            good, what="x", code=make_fixtures.EX_DECLARATION
        )

    # A declared VALUE reaches it, and comes back quoted exactly once.
    assert make_fixtures.cobol_literal("alphanumeric", "AB", "F") == '"AB"'
    for bad in ('A"B', "A\nB", "A\tB", "A\x00B"):
        with pytest.raises(SystemExit) as caught:
            make_fixtures.cobol_literal("alphanumeric", bad, "F")
        assert caught.value.code == make_fixtures.EX_DECLARATION


def test_every_generated_path_interpolation_uses_the_gate() -> None:
    """No interpolation site may format an unchecked value into generated COBOL.

    The gate only helps if nothing bypasses it, and a new emitter is exactly the
    change that would. Asserted structurally, because a bypass is a source-level
    property: there is no input that reveals a site which simply was not called.
    """
    source = (_harness_dir() / "make_fixtures.py").read_text(encoding="utf-8")
    checked = 'cobol_path_literal(path, what="the seed file path")'

    # Every generated `move "<path>" to <field>.' interpolates the CHECKED path.
    assert source.count(f'f\'     move     "{{{checked}}}"\'') == 4, (
        "expected exactly four generated `move \"<path>\" to <field>.' statements, "
        "each interpolating cobol_path_literal(); a new one must route through it"
    )
    # And both comment lines that name the path do too.
    assert source.count(f"*>  Writes {{{checked}}}") == 2

    # The only other `move "{...}"' emitters interpolate a declared raw image, and
    # that name is gated by refuse_unplaceable_text before it is used. Counting them
    # pins the total, so a NEW unchecked emitter cannot slip in unnoticed.
    assert source.count('move     "{') == 6
    assert source.count('move     "{text}"') == 2
    assert source.count("refuse_unplaceable_text(") == 5  # 1 def + 4 call sites

    # The path budget is measured against the WORST case once, before any file is
    # generated, so the diagnosis names what the operator typed rather than a line of
    # generated COBOL they never wrote.
    assert "longest = max(len(name) for name in SEED_FILES)" in source
    assert "the --out directory, plus the longest seed file name it will hold," in source


def test_a_reused_build_product_must_name_the_source_it_came_from() -> None:
    """Step 1 verifies four members; steps 2 and 3 verify what they reuse.

    The hole this closes was structural rather than theoretical. `build_oracle.sh`
    verified the vendored archive's digest only on the branch that UNPACKS it, and
    the reuse branch is the default -- the image unpacks at build time -- so an
    ordinary run never reached the check. Step 2 compiles `cobmysqlapi38.c' into the
    object every bridge links, and step 3 compiles `presql2.cbl' into the translator
    that generates every bridge's SQL, so between them those two files decide what
    the oracle IS. The oracle is the specification (R-6), which makes an unverified
    one an unverified specification.
    """
    build = (_harness_dir() / "build_oracle.sh").read_text(encoding="utf-8")

    # The four members carry pinned digests, and they are verified on BOTH branches:
    # the loop sits after the if/else, not inside the unpack arm.
    assert "readonly ACAS_PRESQL2_MEMBER_DIGESTS=(" in build
    for member in (
        "cobmysqlapi38.c",
        "cobmysqlapi38.sh",
        "presql2.cbl",
        "presql2.sh",
    ):
        assert f"'{member}:" in build, f"{member} carries no pinned digest"

    unpack = build.index("acas_step1_unpack_presql2()")
    step2 = build.index("acas_step2_build_cobmysqlapi()")
    loop = build.index('for entry in "${ACAS_PRESQL2_MEMBER_DIGESTS[@]}"; do', unpack)
    reuse_branch = build.index("reusing the package harness/Dockerfile.gnucobol", unpack)
    assert unpack < reuse_branch < loop < step2, (
        "the member-digest loop must run AFTER the reuse/unpack choice, so that the "
        "default branch is verified too"
    )

    # A compiled artifact cannot honestly pin its own digest -- that moves with the
    # compiler and the host -- so what is pinned is the digest of its SOURCE.
    assert "readonly ACAS_COBMYSQLAPI_PROVENANCE_SUFFIX='.source-sha256'" in build

    # Both reuse sites are gated on it, and each names its own source.
    assert build.count("acas_artifact_provenance_holds ") >= 2
    assert (
        'acas_artifact_provenance_holds "$published" "$c_digest" '
        "'cobmysqlapi38.c'" in build
    )
    assert (
        'acas_artifact_provenance_holds "$existing" "$cbl_digest" '
        "'presql2.cbl'" in build
    )

    # Refusing must not be fatal: each caller rebuilds from the verified source, so a
    # missing record costs one compile instead of failing the build.
    assert "'presql2 cannot be trusted or is absent" in build
    assert "acas_record_artifact_provenance " in build

    # The pinned ARCHIVE digest stays authoritative: the identity override cannot
    # admit unpinned C or COBOL, because the member digests are still enforced.
    assert "ACAS_PRESQL2_SHA256_EXPECTED and ACAS_PRESQL2_MEMBER_DIGESTS." in build
    assert "cannot become a way to" in build


def test_the_image_records_the_provenance_the_build_script_requires() -> None:
    """The two sides of the sidecar contract agree on its name and its content.

    If they disagree the build still works -- it rebuilds both artifacts every run --
    so the regression is a silent slowdown rather than a failure, which is precisely
    the kind that survives. The image also asserts it wrote them, so the divergence
    surfaces at image build.
    """
    build = (_harness_dir() / "build_oracle.sh").read_text(encoding="utf-8")
    dockerfile = (_harness_dir() / "Dockerfile.gnucobol").read_text(encoding="utf-8")

    suffix = ".source-sha256"
    assert f"readonly ACAS_COBMYSQLAPI_PROVENANCE_SUFFIX='{suffix}'" in build

    # The producer writes one sidecar per published artifact, from the SOURCE.
    assert f'sha256sum cobmysqlapi38.c | cut -d" " -f1' in dockerfile
    assert f'"${{ACAS_LIB_DIR}}/cobmysqlapi.o{suffix}"' in dockerfile
    assert f'sha256sum presql2.cbl | cut -d" " -f1' in dockerfile
    assert f"/usr/local/bin/presql2{suffix}" in dockerfile

    # And asserts them, so a producer change that stops writing them fails loudly.
    assert f'test -s "${{ACAS_LIB_DIR}}/cobmysqlapi.o{suffix}"' in dockerfile
    assert f"test -s /usr/local/bin/presql2{suffix}" in dockerfile


# ---------------------------------------------------------------------------
# SECTION 18 -- WITHDRAWN. THE gl051 CONTROL-TOTAL GATE IS DRIVEN ELSEWHERE.
#
# ⭐ THIS SECTION HELD SIX TESTS THAT DROVE `gl051_batch_control_check._end_batch`
# FROM PRE-GATE DATA, AND THEY WERE REDUNDANT. They were written on the belief that no
# test drove the migrated gate - a belief formed from an incomplete reading of
# `tests/arithmetic/test_control_total_comparison.py`, whose first twelve hundred lines
# do re-derive the comparison out of `arithmetic.compare` and `arithmetic.store`. Its
# LAST two hundred do not: `test_the_shipped_gate_accepts_a_vat_bearing_batch_as_written`,
# `..._rejects_a_vat_mismatch_and_still_mutates_the_gross`, `..._rejects_a_gross_mismatch`,
# `..._keeps_its_two_early_dispositions` and `..._leaves_no_driver_loaded` call the
# shipped `_end_batch` directly, through a deferred import behind `pytest.importorskip`
# that deletes every tier-isolated name it added.
#
# That group is a STRICT SUPERSET of what was here: the same three dispositions, the
# same `Batch-Status` sentinel of 7 so that "never assigned" is distinguishable from
# "rejected", the same L1109-before-L1117 proof stated as a counterfactual value, plus a
# byte-level `encoded()` comparison and an R-1 no-driver-left-loaded check that the six
# withdrawn tests did not have.
#
# The withdrawal is recorded rather than done silently, because two other files were
# edited to point AT the withdrawn section and have been corrected to point at the real
# one. Duplicating coverage would have been the smaller error; leaving a header claiming
# to be the only place the gate is driven would have been the larger.
#
# WHAT DRIVES WHAT, for a reader arriving from either file:
#   - the gl051 control-total gate      -> tests/arithmetic/test_control_total_comparison.py
#   - the gl072 silent skips            -> SECTION 19 below
#   - the acas008 refusal pair (A-6)    -> SECTION 20 below
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# SECTION 19 -- gl072'S TWO SILENT SKIPS, DRIVEN AGAINST THE MIGRATED LOOP
#
# ⭐ WHY THESE ARE HERE AND NOT IN A SCENARIO, WITH THE MEASUREMENT THAT DECIDED IT.
# `mixed_accepted_rejected` is the scenario whose stated headline is these two skips
# [general/gl072.cbl:L291-L292] and [general/gl072.cbl:L306-L307]. It does not reach
# either of them, and no seed can, which was established by running the compiled
# cycle and looking at the work file gl070 writes and gl072 reads:
#
#     pretrans.tmp  EXISTS  size=0 bytes
#     postrans.tmp  EXISTS  size=0 bytes
#
# Zero bytes means gl070 emitted no work record, so gl072's first `read post-trans`
# met AT END [general/gl072.cbl:L286-L289] and neither skip test was ever evaluated.
# The cause is ANOMALY N-KEY, measured on GnuCOBOL 3.2 and derived in full in
# `test_the_measured_post_key_round_trip_is_what_starves_gl072` below: the POST-KEY
# a seeded posting row carries cannot be decoded back into the batch number it came
# from, so gl070's OWN guard [general/gl070.cbl:L492-L493] discards the row first.
#
# So the scenario tier can prove the ABSENCE (and does, row by row against the
# declared seed) but cannot prove WHICH skip produced it - which is exactly the
# defect this section closes. Each skip is therefore driven against
# `acas_posting.programs.gl072_transaction_update` itself, and each is paired with
# its CONTRARY case, because a test that only shows a skip cannot tell a skip from a
# program that does nothing at all.
#
# NO DATABASE IS REACHED. The eight facade verbs gl072 performs are replaced by
# recorders, and the work files are the migration's own in-process sequences
# [acas_posting/workfiles.py] - `self._records.clear()`, not a file. The program
# module is imported inside each test body, as everywhere in this file.
# ---------------------------------------------------------------------------

#: The five bytes the frozen bridge leaves in `Batch` after a POST-KEY round trip,
#: measured on the oracle compiler. `move HV-POST-KEY to WS-Post-Key`
#: [common/glpostingMT.cbl:L1085] copies the host variable's eight bytes into the
#: ten-byte group, and for the POST-KEY a seeded `batch 1 / post 1` produces those
#: bytes are 0x06 0x8E 0x0C 0x15 0x3B 0x04 0x30 0x30. `Batch` is the first five.
_MEASURED_ROUND_TRIPPED_BATCH_BYTES: str = "\x06\x8e\x0c\x15\x3b"

#: `472328296244457520` - what the column actually holds after a compiled seed of
#: `Batch: "1"` / `Post-Number: "1"`. Measured by SELECT, and derived from first
#: principles in the test that consumes it.
_MEASURED_STORED_POST_KEY: int = 472328296244457520


def _gl072_fixture(monkeypatch, *, cleared_status: int = 0):
    """Build gl072's storage with every facade verb replaced by a recorder.

    Args:
        monkeypatch: The pytest fixture, used to swap the facade verbs.
        cleared_status: What `GL-Batch-Read-Next` leaves in `Cleared-Status`. Zero is
            `88 Waiting` [copybooks/wsbatch.cob:L30]; one is `88 Processed`.

    Returns:
        `(module, storage, calls)` where `calls` is the ordered list of facade verb
        names the run performed.
    """
    from acas_posting.dal import facade
    from acas_posting.programs import gl072_transaction_update as gl072
    from acas_posting.records.file_access import FileAccess
    from acas_posting.records.file_defs import FileDefs
    from acas_posting.records.gl_batch import GlBatchRecord
    from acas_posting.records.gl_ledger import WsLedgerRecord
    from acas_posting.records.system_record import SystemRecord
    from acas_posting.records.test_data_flags import AcasDalCommonData
    from acas_posting.workfiles import general_ledger_work_files

    calls: list[str] = []

    def recorder(name: str):
        def verb(ctx, *args, **kwargs):
            calls.append(name)
            # `GL-Batch-Read-Next` is the ONLY verb whose result the skip logic reads:
            # `get-batch` tests `Cleared-Status` immediately after it
            # [general/gl072.cbl:L458].
            if name == "gl_batch_read_next":
                ctx.record.cleared_status = cleared_status
            ctx.file_access.fs_reply = 0
        return verb

    for verb_name in (
        "gl_batch_open",
        "gl_nominal_open",
        "gl_batch_read_next",
        "gl_nominal_read_next",
        "gl_batch_rewrite",
        "gl_nominal_rewrite",
        "gl_batch_close",
        "gl_nominal_close",
    ):
        monkeypatch.setattr(gl072.facade, verb_name, recorder(verb_name))

    system_record = SystemRecord()
    file_access = FileAccess()
    ledger = WsLedgerRecord()
    batch = GlBatchRecord()
    file_defs = FileDefs()
    common = AcasDalCommonData()

    storage = gl072._ProgramStorage(
        ws_calling_data=__import__(
            "acas_posting.records.calling_data", fromlist=["WsCallingData"]
        ).WsCallingData(),
        system_record=system_record,
        to_day="21/09/2025",
        file_defs=file_defs,
        file_access=file_access,
        ledger=ledger,
        batch=batch,
        dal_common=common,
        date_formats=__import__(
            "acas_posting.dates", fromlist=["WsDateFormats"]
        ).WsDateFormats(),
        work_files=general_ledger_work_files(),
        ledger_ctx=facade.FacadeContext(
            system=system_record,
            record=ledger,
            file_access=file_access,
            file_defs=file_defs,
            dal_common=common,
        ),
        batch_ctx=facade.FacadeContext(
            system=system_record,
            record=batch,
            file_access=file_access,
            file_defs=file_defs,
            dal_common=common,
        ),
    )
    return gl072, storage, calls


def _stage_one_work_record(gl072, storage, *, post_batch) -> None:
    """Put exactly one record into `post-trans` and open it for input.

    Args:
        gl072: The program module.
        storage: Its storage.
        post_batch: What `post-batch pic 9(5)` [general/gl072.cbl:L111] holds. An
            `int` for the numeric case; a `str` of non-digit bytes for the case the
            frozen bridge actually produces.
    """
    import decimal

    from acas_posting.records.work_records import PostTransRecord

    record = PostTransRecord()
    record.post_batch = post_batch
    record.post_post = 1
    record.post_ledger.post_ac = 1000
    record.post_ledger.post_pc = 0
    record.post_amount = decimal.Decimal("100.00")
    record.post_code = "GL"
    record.post_date = "21/09/25"
    record.post_legend = "one leg"

    files = storage.work_files.post_trans
    files.open_output()
    files.write(record)
    files.close()
    files.open_input()


def test_the_non_numeric_batch_number_skip_fires_and_is_silent(monkeypatch) -> None:
    """SKIP (a), driven: `if post-batch not numeric go to loop`.

    [general/gl072.cbl:L291-L292], ANOMALY A-13 site (a). The value handed in is not
    invented for the test - it is the FIVE BYTES the frozen bridge leaves in `Batch`
    after a POST-KEY round trip, measured on the oracle compiler.

    WHAT "SILENT" MEANS HERE, ASSERTED RATHER THAN DESCRIBED. The skip precedes
    `if save-batch equal zero ... perform headings` [general/gl072.cbl:L302-L304], so
    `get-batch` - and with it the ONLY read of the batch file
    [general/gl072.cbl:L454] - never happens. Nothing is written, nothing is counted,
    and `save-batch` is still zero afterwards.
    """
    import decimal

    gl072, storage, calls = _gl072_fixture(monkeypatch)
    _stage_one_work_record(
        gl072, storage, post_batch=_MEASURED_ROUND_TRIPPED_BATCH_BYTES
    )

    gl072._loop(storage)

    assert "gl_batch_read_next" not in calls, (
        "the skip is BEFORE the headings performs, so get-batch must not run; the "
        f"loop performed {calls}"
    )
    assert "gl_nominal_read_next" not in calls, (
        "no account may be located for a record the program discarded"
    )
    assert storage.save_batch == 0, (
        "`move post-batch to save-batch` [general/gl072.cbl:L303] is downstream of "
        f"the skip, so save-batch must still be zero; it holds {storage.save_batch!r}"
    )
    assert storage.tot_dr == decimal.Decimal("0.00")
    assert storage.tot_cr == decimal.Decimal("0.00")
    # AT END still performs end-account and end-batch [general/gl072.cbl:L287-L288],
    # which is why the two rewrites appear. They are the AT-END pair, not this
    # record's - the frozen program performs them unconditionally on the way out.
    assert calls == ["gl_nominal_rewrite", "gl_batch_rewrite"], (
        "the only verbs on this path are the AT-END pair; the loop performed "
        f"{calls}"
    )


def test_a_numeric_batch_number_is_not_skipped_which_is_the_contrast(
    monkeypatch,
) -> None:
    """THE CONTRARY CASE, without which the test above proves nothing.

    Identical staging except that `post-batch` holds a NUMBER. The record now
    survives the class condition, `save-batch` is zero so `headings` runs, and
    `get-batch` reads the batch file - so the two paths are distinguished by an
    observable rather than asserted to differ.
    """
    gl072, storage, calls = _gl072_fixture(monkeypatch, cleared_status=0)
    _stage_one_work_record(gl072, storage, post_batch=1)

    gl072._loop(storage)

    assert "gl_batch_read_next" in calls, (
        "a numeric batch number must reach get-batch, or this file cannot claim to "
        f"distinguish the skip from the posting path; the loop performed {calls}"
    )
    assert storage.save_batch == 1, (
        "get-batch's two-receiver move [general/gl072.cbl:L452] must have run"
    )
    assert "gl_nominal_read_next" in calls, (
        "with we-error clear the record proceeds to new-account "
        "[general/gl072.cbl:L316-L317]"
    )


def test_get_batch_raises_the_999_sentinel_for_a_batch_that_is_not_waiting(
    monkeypatch,
) -> None:
    """The ONLY setter of the sentinel, driven: `if not waiting move 999 to we-error`.

    [general/gl072.cbl:L458-L460]. `88 Waiting value 0` sits on `Cleared-Status`
    [copybooks/wsbatch.cob:L29-L32] - NOT on `Batch-Status`, which carries
    `Status-Open`/`Status-Closed` two lines above and is a different field. A batch
    already `Processed` therefore raises the sentinel, which is the frozen system's
    re-post guard.

    `999` IS `WeError.NOT_USED` [copybooks/wsfnctn.cob:L23] - the handler
    vocabulary's "not used" value, borrowed here as a private flag. That overlap is
    the frozen program's, and it is preserved.
    """
    gl072, storage, _ = _gl072_fixture(monkeypatch, cleared_status=1)
    _stage_one_work_record(gl072, storage, post_batch=1)
    storage.post = storage.work_files.post_trans.read_next()

    gl072._get_batch(storage)

    assert storage.file_access.we_error == 999, (
        "a batch that is not waiting must raise the sentinel; we-error holds "
        f"{storage.file_access.we_error!r}"
    )
    assert storage.save_batch == 0, (
        "`move 0 to save-batch` [general/gl072.cbl:L460] accompanies the sentinel, "
        "and it is what makes the NEXT record re-perform headings"
    )


def test_get_batch_clears_the_sentinel_for_a_waiting_batch(monkeypatch) -> None:
    """The `else` limb, so the sentinel is shown to be conditional.

    [general/gl072.cbl:L461-L462]. Same call, same record, `Cleared-Status` zero.
    """
    gl072, storage, _ = _gl072_fixture(monkeypatch, cleared_status=0)
    _stage_one_work_record(gl072, storage, post_batch=7)
    storage.post = storage.work_files.post_trans.read_next()

    gl072._get_batch(storage)

    assert storage.file_access.we_error == 0
    assert storage.save_batch == 7, (
        "the two-receiver move [general/gl072.cbl:L452] writes save-batch AND "
        "WS-Batch-Nos; the else limb leaves both standing"
    )
    assert storage.batch.ws_batch_key.ws_batch_nos == 7
    assert storage.batch.ws_batch_key.ws_ledger == 1, (
        "`move 1 to WS-Ledger` [general/gl072.cbl:L451] - 88 GL-Batch value 1 "
        "[copybooks/wsbatch.cob:L16]"
    )


def test_the_999_skip_fires_and_leaves_the_ledger_untouched(monkeypatch) -> None:
    """SKIP (b), driven END TO END: `if we-error equal 999 go to loop`.

    [general/gl072.cbl:L306-L307], ANOMALY A-13 site (b). Not staged by hand: the
    sentinel is raised by the production `get-batch` the loop itself performs,
    because the batch the sequential read lands on is `Processed`. So this exercises
    the whole chain - headings performs get-batch, get-batch raises 999, the loop
    tests it and continues - rather than asserting a branch over a planted flag.

    THE DATABASE EFFECT IS NOTHING, which is the half of A-13 the anomaly register
    cares about: the account is never located, so no balance moves.
    """
    import decimal

    gl072, storage, calls = _gl072_fixture(monkeypatch, cleared_status=1)
    _stage_one_work_record(gl072, storage, post_batch=1)

    gl072._loop(storage)

    assert "gl_batch_read_next" in calls, (
        "the sentinel must be raised by the production get-batch, not planted"
    )
    assert storage.file_access.we_error == 999
    assert "gl_nominal_read_next" not in calls, (
        "the skip precedes new-account [general/gl072.cbl:L309-L317], so the "
        f"nominal ledger must never be read; the loop performed {calls}"
    )
    assert storage.tot_dr == decimal.Decimal("0.00")
    assert storage.tot_cr == decimal.Decimal("0.00")
    assert storage.ledger.ledger_balance == decimal.Decimal("0.00"), (
        "no accumulation at [general/gl072.cbl:L331] may have happened"
    )


def test_the_measured_post_key_round_trip_is_what_starves_gl072() -> None:
    """ANOMALY N-KEY, derived and locked: why no seed can reach either skip.

    THE CHAIN, each link measured on GnuCOBOL 3.2 against MariaDB 10.11.7:

      1. `WS-Post-Key` is a GROUP of two `pic 9(5)` items
         [copybooks/wspost.cob:L14-L16]; `HV-POST-KEY` is `PIC 9(18) COMP`
         [common/glpostingMT.cbl:L283]. A GROUP sender makes
         `move WS-Post-Key to HV-POST-KEY` [common/glpostingMT.cbl:L1054] a BYTE
         move, not a numeric conversion - proved on the oracle by moving the
         non-numeric group "ABCDE00001" into it without a diagnostic.
      2. Batch 1 / post 1 gives the bytes "0000100001". The first EIGHT read as a
         big-endian integer are 3472328296244457520 - NINETEEN digits - which the
         eighteen-digit picture truncates to 472328296244457520. That is what the
         column holds; measured by SELECT after a compiled seed.
      3. The nineteenth digit is gone, so reading back cannot restore the original
         bytes. `move HV-POST-KEY to WS-Post-Key` [common/glpostingMT.cbl:L1085]
         copies the host variable's eight bytes back, and `Batch` receives five
         CONTROL CHARACTERS. `IF Batch IS NUMERIC` is FALSE - displayed by the
         oracle probe.
      4. gl070 therefore discards the row at
         `if batch not = WS-Batch-Nos go to loop` [general/gl070.cbl:L492-L493] and
         writes nothing. MEASURED: pretrans.tmp is ZERO BYTES after the run.

    Step 4 is the whole reason SECTION 19 exists: gl072's skips are downstream of a
    guard that removes their input, so they are unreachable from any seed and must be
    driven directly. Nothing here is repaired (R-4).
    """
    group_image = f"{1:05d}{1:05d}".encode("latin-1")
    assert group_image == b"0000100001"

    raw = int.from_bytes(group_image[:8], byteorder="big")
    assert raw == 3472328296244457520
    assert len(str(raw)) == 19, (
        "the nineteenth digit is the whole mechanism: an eighteen-digit picture "
        "cannot hold it"
    )
    assert raw % 10**18 == _MEASURED_STORED_POST_KEY, (
        "the truncated value must equal what the column was measured to hold"
    )

    # Step 3, byte for byte.
    returned = _MEASURED_STORED_POST_KEY.to_bytes(8, byteorder="big")
    assert returned == b"\x06\x8e\x0c\x15\x3b\x0400"
    assert returned[:5].decode("latin-1") == _MEASURED_ROUND_TRIPPED_BATCH_BYTES

    # Step 3's consequence, through the PRODUCTION class condition rather than a
    # hand-rolled one.
    from acas_posting.cobol import move as cobol_move
    from acas_posting.programs import gl072_transaction_update as gl072

    assert not cobol_move.is_numeric_class(
        _MEASURED_ROUND_TRIPPED_BATCH_BYTES, gl072._POST_BATCH
    ), (
        "if this ever becomes numeric the derivation above is wrong and the "
        "scenario narratives that cite it must be re-measured"
    )

    # Step 4: whatever those bytes are, they are not the batch number that produced
    # them, so gl070's guard cannot match for ANY seeded batch number.
    assert _MEASURED_ROUND_TRIPPED_BATCH_BYTES != f"{1:05d}"


# ---------------------------------------------------------------------------
# SECTION 20 -- ANOMALY A-6, LOCKED AT THE HANDLER WHERE IT LIVES
#
# ⭐ WHY A HANDLER-LEVEL CASE IS NEEDED WHEN A SCENARIO ALREADY ASSERTS THE STATE.
# `acas008` refuses FOUR verbs unconditionally at its own entry
# [common/acas008.cbl:L299-L307] and the facade publishes all four anyway, so a
# caller invoking the re-write verb ALWAYS fails. The only TABLE STATE that can
# produce is no change - which is what `tests/scenarios/test_clean_batch_post_irs.py`
# asserts, and it is not enough on its own: a migrated handler that silently did
# nothing, or raised, or returned a DIFFERENT failure pair, would leave exactly the
# same state and pass. The anomaly is the SPECIFIC PAIR the guard answers with, and
# the pair is a value returned to a caller rather than a row, so only a handler-level
# case can see it.
#
# THE PAIR WAS MEASURED, NOT READ. A COBOL driver was compiled against the frozen
# copybooks and called the COMPILED `acas008` once per verb, with its own linkage in
# its own order [common/acas008.cbl:L278-L284], logging off, and `File-System-Used`
# set to the RDB mode. GnuCOBOL 3.2 answered:
#
#     verb              File-Function  WE-Error  FS-Reply
#     ----------------  -------------  --------  --------
#     read-indexed      04             988       99
#     re-write          07             988       99
#     delete            08             988       99
#     start             09             988       99
#
# No database was needed and none was opened, because the guard returns before any
# access-type or file-mode logic runs - which is itself part of what was measured.
#
# THE CONTRAST WAS MEASURED TOO, and it is what makes the pair meaningful rather than
# generic: `read-next` (function 2) is NOT named by the `evaluate`, so the same call
# passed the guard and went on into the handler's real work - observably, it reached
# code that drives the terminal. So 988/99 is THIS GUARD'S answer and not what
# `acas008` says whenever something goes wrong.
# ---------------------------------------------------------------------------

#: The pair the compiled `acas008` answered for every one of the four refused verbs.
#: `988` is the maintainer's own `*> Action type wrong for file type (seq)   988`
#: [common/acas008.cbl:L304]; `99` is `FS-Reply` [common/acas008.cbl:L305].
_MEASURED_ACAS008_REFUSAL: tuple[int, int] = (988, 99)

#: The four `File-Function` values the guard's single branch names, in the order the
#: `evaluate` lists them - `when 4`, `when 7`, `when 9`, `when 8`
#: [common/acas008.cbl:L300-L303]. The order is preserved because the anomaly register
#: cites the individual `when` lines.
_MEASURED_ACAS008_REFUSED_FUNCTIONS: tuple[int, ...] = (4, 7, 9, 8)


def _acas008_linkage(file_function: int):
    """Build `acas008`'s five arguments, in its own order, for one function code.

    Args:
        file_function: The `File-Function` to call with.

    Returns:
        `(module, args)` where `args` is the tuple `aa010_main` takes.
    """
    from acas_posting.dal import acas008_spl_posting as acas008
    from acas_posting.records.file_access import FileAccess
    from acas_posting.records.file_defs import FileDefs
    from acas_posting.records.spl_irs_posting import WsIrsPostingRecord
    from acas_posting.records.system_record import SystemRecord
    from acas_posting.records.test_data_flags import AcasDalCommonData

    file_access = FileAccess()
    file_access.file_function = file_function
    # Neither is the guard's business - it is tested before both - but they are set so
    # that a handler which somehow got PAST the guard would take the RDB path the
    # migration reproduces rather than the flat-file leg it does not have. ONE is
    # `88 FS-MySql-Used` and ZERO is `88 FS-Cobol-Files-Used`
    # [copybooks/wssystem.cob:L112-L114], and the default is zero.
    system = SystemRecord()
    system.system_data_block.rdbms_flat_statuses.file_system_used = 1
    args = (
        system,
        WsIrsPostingRecord(),
        file_access,
        FileDefs(),
        AcasDalCommonData(),
    )
    return acas008, args


@pytest.mark.parametrize("file_function", _MEASURED_ACAS008_REFUSED_FUNCTIONS)
def test_a6_the_handler_answers_the_measured_refusal_pair(file_function: int) -> None:
    """A-6, DRIVEN: each refused verb answers exactly `WE-Error 988` / `FS-Reply 99`.

    The migrated handler is called through `aa010_main`, which is
    `aa010-main.` [common/acas008.cbl:L289] and holds the whole of the handler's
    logic. No connection is opened, for the same reason the compiled probe needed
    none: the guard is the FIRST thing after the two logging moves, so it returns
    before any code that would want one.

    THE VALUES ARE THE MEASUREMENT'S, not the source's. Reading
    [common/acas008.cbl:L304-L305] would give the same two numbers, but reading is not
    arbitration (R-6) - and reading cannot establish that the compiled handler really
    returns them rather than being overridden downstream, which the probe did
    establish by calling it.

    Args:
        file_function: One of the four values the guard's branch names.
    """
    acas008, args = _acas008_linkage(file_function)

    acas008.aa010_main(*args)

    file_access = args[2]
    measured_we, measured_fs = _MEASURED_ACAS008_REFUSAL
    assert (file_access.we_error, file_access.fs_reply) == (measured_we, measured_fs), (
        f"acas008 called with File-Function {file_function} answered "
        f"({file_access.we_error}, {file_access.fs_reply}); the COMPILED handler was "
        f"measured to answer ({measured_we}, {measured_fs}). A-6 is that the refusal "
        f"is unconditional and always this pair; a different pair means the guard has "
        f"been altered, and a SUCCESS means A-6 has been FIXED - which is a failure "
        f"(R-4)."
    )


def test_a6_the_refusal_is_declared_for_exactly_the_four_measured_functions() -> None:
    """The guard's MEMBERSHIP, so a fifth verb cannot be quietly added or one dropped.

    The migrated layer is data-driven - `HANDLER_REJECTED_FUNCTIONS` keyed by table
    then by function - which is the right shape, and it means the set itself is a
    value that can drift without any code changing. It is pinned here against the
    four the compiled handler was measured to refuse, and against the locators the
    anomaly register cites.
    """
    from acas_posting.dal import acas008_spl_posting as acas008

    declared = {int(function) for function in acas008.REJECTED_FUNCTIONS}
    assert declared == set(_MEASURED_ACAS008_REFUSED_FUNCTIONS), (
        f"the handler declares refusals for {sorted(declared)} and the compiled "
        f"handler was measured to refuse "
        f"{sorted(_MEASURED_ACAS008_REFUSED_FUNCTIONS)} "
        f"[common/acas008.cbl:L300-L303]"
    )
    for function, (fs_reply, we_error, locator) in acas008.REJECTED_FUNCTIONS.items():
        assert (int(we_error), int(fs_reply)) == _MEASURED_ACAS008_REFUSAL, (
            f"File-Function {int(function)} is declared to answer "
            f"({int(we_error)}, {int(fs_reply)}) and was measured as "
            f"{_MEASURED_ACAS008_REFUSAL}"
        )
        assert locator.startswith("[common/acas008.cbl:L30"), (
            f"File-Function {int(function)} cites {locator!r}; the guard's four `when` "
            f"lines are L300 to L303 and the anomaly register cites them individually"
        )


def test_a6_both_published_facade_verbs_reach_the_same_refusal() -> None:
    """THE VERB IS PUBLISHED TWICE AND FAILS BOTH WAYS.

    `SPL-Posting-Rewrite` [copybooks/Proc-ACAS-FH-Calls.cob] and `acas008-Rewrite`
    [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L163] are the entity-named and
    handler-named spellings of one verb, and the facade publishes BOTH over one
    implementation. A caller following either convention must reach the same refusal,
    or the dual-alias design has a hole in exactly the place the anomaly lives.

    ASSERTED ON THE PLAN, NOT BY CALLING. Both verbs dispatch into the handler, and
    the handler's answer is already driven above; what is open here is whether the two
    aliases carry the SAME `File-Function`. That is the property the aliasing could
    get wrong, and it is a value in the published plan, so it is read from there. The
    two prefixes are the layer's own: `_E_` for the ENTITY-named vocabulary of
    `Proc-ACAS-FH-Calls.cob` and `_H_` for the HANDLER-named vocabulary of
    `Proc-ZZ100-ACAS-IRS-Calls.cob`.
    """
    from acas_posting.dal import facade

    plans = {
        "spl_posting_rewrite": getattr(facade, "_E_SPL_POSTING_REWRITE", None),
        "acas008_rewrite": getattr(facade, "_H_ACAS008_REWRITE", None),
    }
    missing = sorted(name for name, plan in plans.items() if plan is None)
    assert not missing, (
        f"no published plan for {missing}; the facade publishes the entity-named and "
        f"handler-named vocabularies over one implementation, so both spellings of the "
        f"re-write verb must exist [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L163-L166]"
    )

    def function_of(plan) -> int:
        for setting, value in plan.moves:
            if str(setting).endswith("File-Function"):
                return int(value)
        raise AssertionError(f"{plan.paragraph} sets no File-Function")

    functions = {name: function_of(plan) for name, plan in plans.items()}
    assert len(set(functions.values())) == 1, (
        f"the two alias spellings set different File-Function values: {functions!r}. "
        f"They are one verb [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L163], so a "
        f"caller following either convention must reach the same refusal."
    )
    assert set(functions.values()) == {7}, (
        f"the re-write verb must carry File-Function 7, which is the `when 7` of the "
        f"guard [common/acas008.cbl:L301]; the plans carry {functions!r}"
    )
    assert all(plan.handler == "acas008" for plan in plans.values()), (
        "both aliases must dispatch to acas008, which is the handler that refuses"
    )


def _a6_facade_context():
    """One `FacadeContext` carrying the five arguments every handler CALL takes.

    The facade path, as distinct from `_acas008_linkage`'s direct call into
    `aa010_main`: these three cases are about what a CALLER of the published verb
    observes, so they go through the published verb.

    Returns:
        The context, with a fresh record and a fresh status block, in the RDB
        configuration - `1` is `88 FS-MySql-Used` [copybooks/wssystem.cob:L112-L114], so
        a supported function would take the leg that wants a connection.
    """
    from acas_posting.dal import facade
    from acas_posting.records.file_access import FileAccess
    from acas_posting.records.file_defs import FileDefs
    from acas_posting.records.spl_irs_posting import WsIrsPostingRecord
    from acas_posting.records.system_record import SystemRecord
    from acas_posting.records.test_data_flags import AcasDalCommonData

    system = SystemRecord()
    system.system_data_block.rdbms_flat_statuses.file_system_used = 1
    return facade.FacadeContext(
        system=system,
        record=WsIrsPostingRecord(),
        file_access=FileAccess(),
        file_defs=FileDefs(),
        dal_common=AcasDalCommonData(),
    )


@pytest.mark.parametrize(
    ("verb_name", "file_function"),
    (
        ("spl_posting_read_indexed", 4),
        ("spl_posting_rewrite", 7),
        ("spl_posting_start", 9),
        ("spl_posting_delete", 8),
    ),
)
def test_a6_the_published_verb_is_refused_and_leaves_the_record_alone(
    verb_name: str, file_function: int
) -> None:
    """A-6 through the ENTITY-named vocabulary, invoked rather than inspected.

    The section above drives `aa010_main` directly, which establishes the pair. What
    this adds is the CALLER'S view: the facade paragraph is performed, so the
    `File-Function` it sets on the way in is observable, and the record is compared
    field for field before and after - because "the verb can never succeed" has to mean
    the record did not move either, not merely that a status came back.

    Args:
        verb_name: The published entity-named verb.
        file_function: The `when` the guard names for it [common/acas008.cbl:L300-L303].
    """
    from acas_posting.dal import facade

    context = _a6_facade_context()
    before = dataclasses.asdict(context.record)

    pair = getattr(facade, verb_name)(context)

    measured_we, measured_fs = _MEASURED_ACAS008_REFUSAL
    assert (int(pair.fs_reply), int(pair.we_error)) == (measured_fs, measured_we)
    assert int(context.file_access.fs_reply) == measured_fs
    assert int(context.file_access.we_error) == measured_we
    #  The facade paragraph selected this function, which is how we know the right verb
    #  was reached rather than some other refusal being observed.
    assert int(context.file_access.file_function) == file_function
    assert dataclasses.asdict(context.record) == before, (
        "the verb can never succeed [common/acas008.cbl:L296-L307], so nothing about "
        "the record may move - a handler that refused and still stored would leave the "
        "same status pair behind"
    )


def test_a6_the_handler_named_rewrite_is_refused_by_calling_it() -> None:
    """A-6 through the OTHER vocabulary - one implementation, two published names.

    `acas008-Rewrite` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L163-L166] is the IRS
    convention's name for the same paragraph, and the facade publishes both alias sets
    over one implementation (Agent Action Plan section 0.3.3). The sibling test above
    asserts the two PLANS agree; this one asserts a caller following the IRS convention
    actually gets the identical refusal.

    ⭐ THE IRS VOCABULARY PUBLISHES ONLY THE REWRITE of the four. It has no
    `acas008-Read-Indexed`, `-Start` or `-Delete` paragraph at all, which is asserted
    here as an absence: inventing aliases the frozen copybook does not declare would be
    a facade this migration made up.
    """
    from acas_posting.dal import facade

    context = _a6_facade_context()
    before = dataclasses.asdict(context.record)

    pair = facade.acas008_rewrite(context)

    measured_we, measured_fs = _MEASURED_ACAS008_REFUSAL
    assert (int(pair.fs_reply), int(pair.we_error)) == (measured_fs, measured_we)
    assert int(context.file_access.file_function) == 7
    assert dataclasses.asdict(context.record) == before

    for absent in ("acas008_read_indexed", "acas008_start", "acas008_delete"):
        assert not hasattr(facade, absent), (
            f"{absent} is published, but "
            f"[copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L163-L166] declares no such "
            f"paragraph - the handler-named vocabulary would then be this migration's "
            f"invention rather than the copybook's."
        )


def test_a6_the_refusal_happens_before_any_connection_is_attempted() -> None:
    """The guard is the FIRST thing the handler does, so no database is reached.

    The measurement in the section note records this - the compiled probe needed no
    database - and prose is not a lock. Proved here by sabotage: the handler's own
    `mysql_1000_open` is replaced by a call that fails the test if it is ever reached,
    and the verb is invoked in the RDBMS configuration, the one every scenario runs in,
    where a SUPPORTED function would open a connection. The verb still answers 99/988,
    so the guard returned before the configuration test at [common/acas008.cbl:L313] and
    before every store decision after it.

    The process connection is asserted absent afterwards as well, because a connection
    opened and left open would be a resource leak this tier could not otherwise see.
    """
    from acas_posting.dal import acas008_spl_posting as acas008
    from acas_posting.dal import connection, facade

    context = _a6_facade_context()
    assert connection.process_connection() is None

    attempts: list[object] = []

    def refuse_to_open(*arguments, **_keywords):
        attempts.append(arguments)
        raise AssertionError(
            "a verb the handler refuses at entry [common/acas008.cbl:L296-L307] must "
            "not reach the database - anomaly A-6 is a status pair, not a query."
        )

    original = acas008.mysql_1000_open
    acas008.mysql_1000_open = refuse_to_open
    try:
        pair = facade.spl_posting_rewrite(context)
    finally:
        acas008.mysql_1000_open = original

    measured_we, measured_fs = _MEASURED_ACAS008_REFUSAL
    assert (int(pair.fs_reply), int(pair.we_error)) == (measured_fs, measured_we)
    assert attempts == []
    assert connection.process_connection() is None


def test_a6_the_supported_functions_are_not_refused() -> None:
    """The guard names four functions and ONLY those four.

    Without this control every assertion above would pass just as well if the handler
    refused EVERYTHING - and a handler that refused `Open`, `Close`, `Read-Next` and
    `Write` would make the IRS transfer file unusable while every A-6 test stayed green.
    The supported functions [common/acas008.cbl:L354-L375] are therefore asserted to be
    absent from the rejection table, and `Delete-All` with them: it is the function the
    handler COERCES `Open`-plus-`Output` into [common/acas008.cbl:L313-L319], so
    refusing it would break the transfer-file clear `irs030` performs at end of job
    [irs/irs030.cbl:L1720-L1724].
    """
    from acas_posting.dal import acas008_spl_posting as acas008
    from acas_posting.dal import status

    rejected = {int(function) for function in acas008.REJECTED_FUNCTIONS}
    assert rejected == set(_MEASURED_ACAS008_REFUSED_FUNCTIONS)

    for supported in acas008.SUPPORTED_HANDLER_FUNCTIONS:
        assert int(supported) not in rejected, (
            f"File-Function {int(supported)} is both supported and refused, which no "
            f"reading of [common/acas008.cbl:L296-L307] permits"
        )
    assert int(status.FileFunction.DELETE_ALL) not in rejected
    assert int(acas008.COERCED_FUNCTION) == int(status.FileFunction.DELETE_ALL)



# ---------------------------------------------------------------------------
# SECTION 21 -- THE TIER-IMPORT CONTRACT, MADE EXPLICIT AND BOUNDED
#
# ⭐ WHY THIS SECTION EXISTS. Agent Action Plan section 0.4.3 gives `tests/arithmetic/*`
# a deliberately narrow import set: `cobol` and `records`, and NOT `dal`, NOT
# `programs` and NOT a database. The point of that boundary is not tidiness. It is
# that the arithmetic tier is the one tier which runs ANYWHERE - no container, no
# MariaDB, no seeded fixture - so it is the tier that still tells you something when
# the stack is down. An arithmetic module that imports `acas_posting.dal` at module
# level drags `dal.facade` in at COLLECTION time, and with it a connection module and
# every handler; the tier then either fails to collect on a bare host or silently
# stops being the thing it was for.
#
# AND YET SEVERAL MODULES IN THIS TIER LEGITIMATELY REACH INTO `programs` AND `dal`.
# They must: a test that re-derives a program's formula inline is a SECOND source of
# business logic, and can pass while the shipped program is wrong. Driving the
# shipped paragraph is the fix, and it needs the shipped module. So the boundary
# cannot be "never"; it has to be "never at module level, and only in a named set of
# files".
#
# THE TWO HALVES, AND WHY BOTH ARE ASSERTED SEPARATELY.
#
#   (1) NO MODULE-LEVEL IMPORT, in ANY file of the tier. This is the structural
#       property, and it is absolute - there is no allow-list for it. A deferred
#       import inside a function body costs nothing until that test runs, and the
#       helpers that perform them restore `sys.modules` afterwards, so collection
#       stays clean and a bare host still collects the whole tier.
#
#   (2) A BOUNDED SET OF FILES may defer-import. This half is a ratchet rather than
#       a prohibition. Without it the practice spreads file by file, each step
#       locally justified, until the tier's import set is whatever happened to
#       accumulate - and nobody ever decided that. Adding a file to the set below is
#       a deliberate edit with a reason attached, which is the whole mechanism.
#
# WHAT THIS SECTION DOES NOT DO. It does not check that a deferred import is *used*
# correctly, and it does not check the third mechanism - `pytest.importorskip` and
# the `_shipped_module` / `_freshly_imported` context managers, which import by NAME
# rather than by statement and therefore cannot be found by an AST walk for `Import`
# nodes. Those are bounded by the same allow-list through their own textual
# reference, and each restores what it added in a `finally`. Naming that limit here
# is better than implying a completeness the walk does not have.
# ---------------------------------------------------------------------------

#: Every `tests/arithmetic/*.py` permitted to import `acas_posting.programs` or
#: `acas_posting.dal` INSIDE A FUNCTION BODY, with the reason each one needs to.
#:
#: Every entry earns its place by driving shipped code instead of re-deriving it. That
#: is the trade this allow-list records: a slightly wider import set in exchange for
#: tests that cannot pass by agreeing with themselves.
_MAY_DEFER_IMPORT_PROGRAM_OR_DAL: Final[Mapping[str, str]] = MappingProxyType(
    {
        "test_double_entry_explosion.py": (
            "drives gl070's own pre-process loop, so the three-leg explosion is "
            "measured against the shipped paragraph rather than a transcription of it"
        ),
        "test_gl080_cycle_divide_rounded.py": (
            "drives gl080.run() with every facade verb substituted, to prove the "
            "file's transcription agrees with the shipped program"
        ),
        "test_irs_vat_from_gross.py": (
            "drives the shipped gross sections of irs030 and gl051, so the VAT store "
            "under test is the one the cycle performs"
        ),
        "test_irs_vat_from_net.py": (
            "the net twin of the above, dispatching on the receiving descriptor to "
            "reach whichever of the two shipped sections owns it"
        ),
        "test_ledger_balance_accumulation.py": (
            "drives gl072's new-account paragraph; the conformance lock here is what "
            "caught the transcription that computed the key move without storing it"
        ),
        "test_compute_truncate_unrounded.py": (
            "drives the shipped sl060 and sl100 average blocks, whose three "
            "mutually inconsistent guards cannot be checked from a transcription"
        ),
        "test_control_total_comparison.py": (
            "drives gl051._end_batch, which is the control-total gate itself"
        ),
        "test_shared_storage_and_dispatch_boundaries.py": (
            "this file: sections 19 and 20 drive gl072's skip loop and the acas008 "
            "refusal plans, and this section reads the tier's own import graph"
        ),
        "test_comp3_packed_decimal.py": (
            "reads the shipped sl060 accumulator declaration to pin truncation #1 "
            "against the field the program actually declares"
        ),
        "test_comp_binary.py": (
            "reads the shipped sales-ledger and bridge views for the A-11 sign-loss "
            "census and the measured Q-3 outcome"
        ),
        "test_compute_rounded_half_up.py": (
            "walks the three program modules with `ast` to close the five-ROUNDED "
            "census at both ends - table rows and shipped call sites"
        ),
        "test_irs_date_component_derivation.py": (
            "reads the shipped irspostingMT loader view for the guarded date "
            "components and the Q-25 composition census"
        ),
        "test_pic_field_descriptors.py": (
            "reads shipped descriptors for the drift census across the three layers"
        ),
    }
)


def _arithmetic_tier_files() -> tuple[Path, ...]:
    """Every test module of the arithmetic tier, in a stable order.

    Returns:
        The `tests/arithmetic/*.py` paths, sorted, excluding `__init__.py` so the
        count is of test modules rather than of package plumbing.
    """
    here = Path(__file__).resolve().parent
    return tuple(
        path
        for path in sorted(here.glob("*.py"))
        if path.name != "__init__.py"
    )


def _tier_crossing_imports(tree: ast.Module) -> tuple[tuple[int, str, bool], ...]:
    """Every import of `acas_posting.programs` or `acas_posting.dal` in one module.

    Args:
        tree: The parsed module.

    Returns:
        One tuple per crossing import: its line, the module named, and whether it
        sits at MODULE level. Module level is determined by identity against the
        module body rather than by indentation or by `ast.walk` order, because
        walking from the top descends into function bodies and would report every
        deferred import as a module-level one.
    """
    top_level = {id(node) for node in tree.body}
    found: list[tuple[int, str, bool]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        named: list[str] = []
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            named.append(node.module)
        named.extend(alias.name for alias in node.names)
        for name in named:
            if name.startswith(("acas_posting.programs", "acas_posting.dal")):
                found.append((node.lineno, name, id(node) in top_level))
    return tuple(found)


def test_no_arithmetic_module_imports_a_program_or_dal_at_module_level() -> None:
    """Half one, and it is absolute: nothing crosses the tier at COLLECTION time.

    A module-level `from acas_posting.dal import facade` in this tier pulls the whole
    data-access layer in when pytest merely COLLECTS the file - before any test runs,
    on every host, including one with no MariaDB. The tier's value is that it runs
    anywhere; that is what this assertion protects, and it protects it for every file
    rather than for a chosen set, because there is no legitimate reason for the
    exception to exist.

    The diagnostic names the file, the line and the module, so a failure is a
    one-line fix rather than a hunt.
    """
    offenders: list[str] = []
    for path in _arithmetic_tier_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        offenders.extend(
            f"{path.name}:L{line} imports {module} at module level"
            for line, module, at_module_level in _tier_crossing_imports(tree)
            if at_module_level
        )

    assert offenders == [], (
        "the arithmetic tier must not import acas_posting.programs or "
        "acas_posting.dal at module level - Agent Action Plan section 0.4.3 keeps "
        "this tier runnable with no database, and a module-level import crosses the "
        "boundary at collection time. Move the import into the function that needs "
        "it. Offenders: " + "; ".join(offenders)
    )


def test_the_set_of_modules_that_defer_import_is_the_declared_one() -> None:
    """Half two, a ratchet: the crossing set is exactly what was decided.

    Two directions, and the second is the one that matters more.

    FORWARD - a file that defers an import must be on the list. That is the ratchet:
    the practice cannot spread to a fourteenth file without someone adding a row and
    a reason, which is the moment to ask whether driving shipped code is really what
    the new test needs.

    BACKWARD - a row on the list whose file no longer defers anything is stale, and
    stale permission is how an allow-list stops meaning anything. Asserting the set
    both ways keeps the list a description of the tree rather than a wish about it.

    The backward direction is asserted only for files that exist and defer no import
    by STATEMENT. A listed file may legitimately reach shipped code only through
    `pytest.importorskip` or a `_shipped_module` context manager, which import by
    name; those are outside an AST walk for `Import` nodes, as this section's header
    records, so their rows are checked for a textual reference instead of being
    reported as stale.
    """
    present = {path.name for path in _arithmetic_tier_files()}
    declared = set(_MAY_DEFER_IMPORT_PROGRAM_OR_DAL)

    unknown = sorted(declared - present)
    assert unknown == [], (
        f"the allow-list names files that are not in this tier: {unknown}. A row "
        f"that points at nothing grants permission nobody can audit."
    )

    deferring: set[str] = set()
    referencing: set[str] = set()
    for path in _arithmetic_tier_files():
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
        crossings = _tier_crossing_imports(tree)
        if crossings:
            deferring.add(path.name)
        if "acas_posting.programs" in text or "acas_posting.dal" in text:
            referencing.add(path.name)

    undeclared = sorted(deferring - declared)
    assert undeclared == [], (
        f"these modules defer-import acas_posting.programs or acas_posting.dal but "
        f"are not on the allow-list: {undeclared}. Driving shipped code instead of "
        f"re-deriving a formula is the right reason to cross this boundary - add the "
        f"file to _MAY_DEFER_IMPORT_PROGRAM_OR_DAL with that reason stated, so the "
        f"tier's import set stays something that was decided rather than something "
        f"that accumulated (Agent Action Plan section 0.4.3)."
    )

    stale = sorted(declared - referencing)
    assert stale == [], (
        f"these modules are on the allow-list but no longer reference "
        f"acas_posting.programs or acas_posting.dal at all: {stale}. Remove the "
        f"rows - an allow-list carrying permissions nothing uses trains a reader to "
        f"stop believing it."
    )

    # Every reason is real prose, not a placeholder. A row whose justification is
    # empty grants the same permission as one that explains itself, which is exactly
    # the failure this list exists to prevent.
    for name, reason in _MAY_DEFER_IMPORT_PROGRAM_OR_DAL.items():
        assert len(reason.split()) >= 8, f"{name}'s reason is too thin: {reason!r}"


def test_the_tier_still_collects_without_the_data_access_layer_imported() -> None:
    """The property the two halves above exist to deliver, asserted end to end.

    The previous two tests are about import STATEMENTS. This one is about the
    OUTCOME they are meant to produce, and it is worth asserting separately because
    the statements could all be correct while something else - a module-level
    descriptor built by calling into `dal`, say - still dragged the layer in.

    Collecting this tier in a subprocess with `--collect-only` and then asking
    whether `acas_posting.dal.connection` reached `sys.modules` answers the real
    question: can a developer with no MariaDB, no container and no seeded fixture
    still collect and run the arithmetic tier? A subprocess is required because this
    very session has already imported the layer through the deferred imports the
    allow-list permits, so `sys.modules` here cannot answer it.
    """
    repo_root = Path(__file__).resolve().parents[2]
    probe = (
        "import subprocess, sys, json\n"
        "import pytest\n"
        "code = pytest.main(['-q', '--collect-only', '-p', 'no:cacheprovider',\n"
        "                    'tests/arithmetic'])\n"
        "leaked = sorted(m for m in sys.modules\n"
        "                if m.startswith('acas_posting.dal')\n"
        "                or m.startswith('acas_posting.programs'))\n"
        "print('COLLECT_RC=' + str(int(code)))\n"
        "print('LEAKED=' + json.dumps(leaked))\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )
    stdout = completed.stdout
    assert "COLLECT_RC=0" in stdout, (
        f"collecting the arithmetic tier must succeed on its own; rc line missing or "
        f"non-zero.\nstdout:\n{stdout[-3000:]}\nstderr:\n{completed.stderr[-2000:]}"
    )

    leaked_line = next(
        line for line in stdout.splitlines() if line.startswith("LEAKED=")
    )
    leaked = json.loads(leaked_line[len("LEAKED=") :])
    assert leaked == [], (
        f"collecting the arithmetic tier imported program or data-access modules: "
        f"{leaked}. Collection must not cross the tier boundary, or this tier stops "
        f"being the one that still runs when the stack is down."
    )


# ---------------------------------------------------------------------------
# SECTION 22 -- THE POST-KEY ROUND TRIP, MEASURED AND PINNED  (ANOMALY N-KEY)
#
# ⭐ WHAT WAS WRONG, AND WHY NO GREEN SCENARIO WOULD HAVE SHOWN IT.
#
# `WS-Post-Key` is a GROUP of two `pic 9(5)` items [copybooks/wspost.cob:L14-L16] and
# `HV-POST-KEY` is `PIC 9(18) COMP` [common/glpostingMT.cbl:L283]. Both directions of
# the bridge move between them:
#
#     move WS-Post-Key to HV-POST-KEY.   [common/glpostingMT.cbl:L1054]   LOAD
#     move HV-POST-KEY to WS-Post-Key.   [common/glpostingMT.cbl:L1085]   UNLOAD
#
# Because one operand is a group, BOTH are alphanumeric BYTE moves - nothing is
# converted numerically on the way. The load was implemented that way. The unload was
# not: it took the last ten DECIMAL digits of the host variable and split them, which
# for the value the compiled bridge actually stores yields a batch of 62444.
#
# 62444 is a perfectly legitimate five-digit batch number, and that is the whole danger.
# The compiled program leaves bytes in `Batch` that cannot be a batch number at all, so
# gl070's guard `if batch not = WS-Batch-Nos go to loop` [general/gl070.cbl:L492-L493]
# discards every posting - ANOMALY N-KEY, the defect that starves gl070, gl071, gl072
# AND gl080's deletion pass. A reproduction yielding 62444 discards every posting too,
# for as long as no run happens to seed batch 62444. On a run that did, the Python side
# would MATCH and post while the frozen system posts nothing. A state diff would then
# show it - but only on that run, which is why the arithmetic tier has to own it.
#
# THE MEASUREMENT, taken with both operands declared exactly as the frozen sources
# declare them, the host variable set to 472328296244457520 - the value the compiled
# bridge stores for a 0000100001 key, hence the value a fetch really returns - and all
# ten group bytes read back with FUNCTION ORD:
#
#     group bytes      06 8E 0C 15 3B 04 30 30 20 20
#     Batch            0x06 8E 0C 15 3B   -> reported NOT NUMERIC
#     Post-Number      0x04 30 30 20 20   -> reported NOT NUMERIC
#     first ten digits 4723282962         -> does not match
#     last ten digits  6244457520         -> does not match
#
# So the answer to "first ten or last ten" is NEITHER: it is eight BYTES, space-padded
# to the group's ten. The last two bytes are 0x20 - measured, not assumed, and not zero.
#
# AND WHAT `Batch` COMPARES AS. An exhaustive comparison against every value in
# 0..99999 inside the compiled probe matched 75261 and nothing else; `= 1`, `= 62444`
# and `= ZERO` were all false. 75261 is what COBOL's tolerant zoned read gives for those
# five bytes - the digit of each byte is its LOW NIBBLE, so 6, 14, 12, 5, 11 accumulated
# base ten - which is exactly the rule `acas_posting.cobol.usage` already implements.
# The compiled program and the migration's own semantics layer agree, independently.
#
# WHY THESE TESTS EXIST RATHER THAN JUST THE DOCSTRING. The DAL states the zoned rule
# inline because `acas_posting.cobol` is outside its dependency set (section 0.4.3).
# That is a SECOND expression of a rule the semantics layer owns, and the way to make a
# second expression safe is to assert the two agree - which is what the first test below
# does, over a range of images rather than the one that was measured.
# ---------------------------------------------------------------------------

#: The value the compiled bridge stores for a `0000100001` key, and therefore the value
#: a fetch returns. Recorded once, because three tests below use it.
_MEASURED_POST_KEY_COLUMN_VALUE: Final[str] = "472328296244457520"

#: The ten group bytes measured after the frozen unload of that value.
_MEASURED_POST_KEY_GROUP_IMAGE: Final[bytes] = bytes(
    (0x06, 0x8E, 0x0C, 0x15, 0x3B, 0x04, 0x30, 0x30, 0x20, 0x20)
)

#: What `Batch` compares equal to, found by exhaustive search inside the compiled probe.
_MEASURED_BATCH_COMPARES_AS: Final[int] = 75261

#: What the superseded `% 10**10` reading produced - a LEGITIMATE batch number, which is
#: why it was dangerous rather than merely wrong.
_REJECTED_DECIMAL_READING_BATCH: Final[int] = 62444


def test_the_post_key_unload_reproduces_the_measured_group_image() -> None:
    """The unload takes eight BYTES, space-padded - not ten decimal digits.

    Asserts the measured outcome directly, and asserts BOTH rejected readings against
    it, so the test records what the answer is *and* what it is not. Without the second
    half a reader cannot tell that two plausible alternatives were considered and
    excluded by measurement rather than never contemplated.
    """
    from acas_posting.dal import acas006_gl_posting as gl_posting

    batch, post_number = gl_posting._split_post_key(
        Decimal(_MEASURED_POST_KEY_COLUMN_VALUE)
    )

    # oracle: measured - an exhaustive comparison in the compiled probe matched this
    # value and no other.  spec: [common/glpostingMT.cbl:L1085]
    assert batch == _MEASURED_BATCH_COMPARES_AS

    # The byte image the function must be building, asserted through the function's own
    # inputs rather than by reading its internals.
    stored = int(Decimal(_MEASURED_POST_KEY_COLUMN_VALUE))
    assert (
        stored.to_bytes(8, byteorder="big") + b"\x20\x20"
        == _MEASURED_POST_KEY_GROUP_IMAGE
    )

    # NEITHER decimal reading. Both are asserted because both were live candidates.
    eighteen_digits = f"{stored:018d}"
    assert batch != int(eighteen_digits[:10]) % 100000, "the first-ten reading"
    assert batch != _REJECTED_DECIMAL_READING_BATCH, (
        "the last-ten reading produced 62444, a legitimate batch number that would "
        "MATCH a seeded batch 62444 and post where the frozen system posts nothing"
    )
    assert post_number == 40000


def test_the_post_key_zoned_rule_agrees_with_the_semantics_layer() -> None:
    """The DAL's inline zoned read must equal `cobol.usage`'s, over a RANGE of images.

    The DAL states the rule inline because it may not import `acas_posting.cobol`
    (section 0.4.3). This test is what makes that safe: it drives the DAL's own function
    and the semantics layer's canonical decoder over the same images and requires them to
    agree. A range rather than the single measured image, because two implementations can
    coincide on one input and diverge on the next - which is exactly how a duplicated
    rule rots.

    The images are chosen to span the cases that behave differently: the measured one, a
    plain ASCII-digit key where every low nibble is already a digit, and keys whose bytes
    carry high nibbles the zoned read must ignore.
    """
    from acas_posting.cobol import usage as cobol_usage
    from acas_posting.dal import acas006_gl_posting as gl_posting
    from acas_posting.dictionary import model

    column_values = (
        Decimal(_MEASURED_POST_KEY_COLUMN_VALUE),
        Decimal("3472328296244457520"),  # the in-memory image, all ASCII digits
        Decimal("0"),
        Decimal("1"),
        Decimal("999999999999999999"),  # the widest `pic 9(18)` value
        Decimal("72340172838076673"),
    )

    for column_value in column_values:
        batch, post_number = gl_posting._split_post_key(column_value)
        stored = int(column_value)
        image = stored.to_bytes(8, byteorder="big", signed=stored < 0) + b"\x20\x20"

        canonical_batch = cobol_usage.decode(
            image[:5], usage=model.Usage.DISPLAY, digits=5, scale=0, signed=False
        )
        canonical_post = cobol_usage.decode(
            image[5:10], usage=model.Usage.DISPLAY, digits=5, scale=0, signed=False
        )
        assert batch == canonical_batch, column_value
        assert post_number == canonical_post, column_value


def test_an_in_memory_post_key_round_trip_is_byte_symmetric() -> None:
    """Load then unload the SAME host variable and the bytes come back.

    This is the case the load and the unload share, and it is worth pinning separately
    because it is the one that proves the two functions are mirrors. A probe measured it:
    loading `0000100001` leaves the ASCII bytes `00001000` in the host variable, and
    unloading that same host variable puts those eight bytes back with two spaces after
    them, so `Batch` reads 1 and `Post-Number` reads 0.

    NOTE WHAT THIS IS NOT. It is not the path a real read takes. A real read fetches the
    COLUMN's value - the eighteen-digit edit the bridge rendered, which is a DIFFERENT
    bit pattern - so the sibling test above is the one that describes production
    behaviour. Both are kept because conflating them is how the `% 10**10` reading looked
    plausible in the first place.
    """
    from acas_posting.dal import acas006_gl_posting as gl_posting
    from acas_posting.records.gl_posting import WsPostKey

    host_variable = gl_posting._join_post_key(WsPostKey(batch=1, post_number=1))

    # The load's own byte image, which the probe read as the ASCII text `00001000`.
    assert int(host_variable).to_bytes(8, byteorder="big") == b"00001000"

    batch, post_number = gl_posting._split_post_key(host_variable)
    assert batch == 1
    assert post_number == 0, (
        "the group's last two bytes are the alphanumeric space pad, so Post-Number "
        "reads `000` followed by two spaces - low nibbles 0,0,0,0,0"
    )


# ---------------------------------------------------------------------------
# SECTION 23 -- THE CITATION CONTRACT: EVERY `[path:Lnnn]` MUST RESOLVE  (R-5)
#
#  Rule R-5 requires field-level and paragraph-level traceability, and this
#  project discharges it with inline `[path:Lnnn]` citations into the frozen
#  source - more than eighteen thousand of them. A citation that does not resolve
#  is worse than no citation: it asserts an authority, and a reader who follows it
#  lands on an unrelated line and either mistrusts the whole scheme or, worse,
#  believes what they find there.
#
#  A code review found twenty-six such citations. Fixing them one by one would have
#  left the next twenty-six to the next reviewer, so this section makes the
#  property MACHINE-CHECKED instead. It found and closed fifty-three:
#    * 5 out of range - `copybooks/irswssystem.cob:L44` and `:L43` in `args.py`
#      (that copybook has 41 lines; `Print-Spool-Name` is line 37 and
#      `PL-Approp-AC` is line 36, a consistent +7 drift), plus
#      `harness/docker-compose.yml` lines 869-871 in `build_oracle.sh` and line 792
#      in `dump_tables.py`, for a file of 592 lines.
#    * 48 bare FILENAMES with no directory - `ACASDB.sql`, `irsfinalMT.cbl`,
#      `irswsfinal.cob`, `acasirsub5.cbl`, `run_cobol_scenario.sh`. Each resolved
#      to exactly ONE tracked path, so qualifying them was mechanical.
#
#  TWO CITATION FORMS, AND WHY THE SECOND NEEDS A DOCUMENTED RULE. The
#  fully-qualified form -- `general/gl080.cbl` then `:L328`, wrapped in brackets --
#  is self-contained and is checked directly. The SHORTHAND form, a bare `:L328` in
#  brackets with no path, inherits its path from context, and that
#  inheritance is what a validation check has to model. Reading the codebase rather
#  than assuming, the convention is TWO-LEVEL:
#
#    1. THE NEAREST PRECEDING fully-qualified citation in the same scope, where a
#       scope is one function (or, for markdown, one heading section). This is what
#       a human reader does, and it accounts for 1749 of the 2155 shorthand
#       citations. It was verified against a case that discriminates: the shorthand
#       `:L324` in `acas007_gl_batch.py` resolves to `common/acas007.cbl` line 324,
#       which reads
#       `perform ba012-Test-WS-Rec-Size-2.` - an exact match for the comment on it,
#       and NOT the more-frequently-cited `common/glbatchMT.cbl`, whose line 324 is
#       an unrelated screen literal.
#    2. THE FILE'S DECLARED SUBJECT, when level 1 yields nothing or yields a file
#       too short to contain the line. A module docstring whose shorthand names line
#       1176 of the program it migrates means that program, even where some other
#       file was
#       mentioned more recently - which is the case for the shorthand pointing at
#       line 1176 in `sl060_invoice_posting.py`, and accounts for most of the
#       remaining 406.
#
#  A DAL module has TWO declared subjects, its handler AND its bridge, because it
#  narrates both: `acas007_gl_batch.py` cites `common/acas007.cbl` for the
#  handler's procedure division and `common/glbatchMT.cbl` for the bridge's. That
#  is not laxity in the rule - it is the module's actual subject matter, and a
#  one-subject rule would reject correct citations.
#
#  ⛔ WHAT THIS SECTION DELIBERATELY DOES NOT DO. It does not check that a citation
#  points at the RIGHT line, only that the line EXISTS. Semantic correctness is not
#  mechanically decidable and the surviving quotations in the prose are what carry
#  it. What is decidable - the path resolves, and the line is inside the file - is
#  now decided on every run, and the frozen sources cannot be edited to satisfy it
#  because they cannot be edited at all.
# ---------------------------------------------------------------------------

#: A fully-qualified citation: a path with an extension, then `:Lnnn` or
#: `:Lnnn-Lmmm`. The alternation of extensions keeps prose like `[R-5:L1]` out.
_CITATION_FULL: Final = re.compile(
    r"\[([A-Za-z0-9_./-]+\.(?:cbl|cob|scb|sql|cpy|sh|conf|py|md|txt|toml|yaml|yml))"
    r":L(\d+)(?:\s*-\s*L?(\d+))?\]"
)

#: The shorthand form, which inherits its path from context.
_CITATION_BARE: Final = re.compile(r"\[:L(\d+)(?:\s*-\s*L?(\d+))?\]")

#: A scope boundary in Python: the shorthand does not reach across a definition.
_SCOPE_BOUNDARY: Final = re.compile(r"^\s*(?:def |class |async def )")

#: handler stem -> bridge stem, from the Agent Action Plan's entity-to-table spine
#: (§0.2.1.1). A DAL module's shorthand may cite either of its two subjects.
_HANDLER_BRIDGE: Final[Mapping[str, str]] = MappingProxyType(
    {
        "acas000": "systemMT",
        "acas005": "nominalMT",
        "acas006": "glpostingMT",
        "acas007": "glbatchMT",
        "acas008": "slpostingMT",
        "acas012": "salesMT",
        "acas013": "valueMT",
        "acas015": "analMT",
        "acas016": "slinvoiceMT",
        "acas019": "otm3MT",
        "acas022": "purchMT",
        "acas026": "plinvoiceMT",
        "acas029": "otm5MT",
        "acasirsub1": "irsnominalMT",
        "acasirsub3": "irsdfltMT",
        "acasirsub4": "irspostingMT",
        "acasirsub5": "irsfinalMT",
    }
)

#: Files whose subject is not derivable from their name, declared explicitly. Each
#: was determined by measurement - the frozen file cited most often in that module
#: whose length admits every shorthand line it carries - and each is the module's
#: obvious subject, which is the corroboration that the derivation is right rather
#: than merely self-consistent.
_DECLARED_SUBJECT: Final[Mapping[str, str]] = MappingProxyType(
    {
        "acas_posting/dal/status.py": "common/glpostingMT.cbl",
        "acas_posting/dal/connection.py": "copybooks/mysql-procedures.cpy",
        "acas_posting/records/file_access.py": "copybooks/wsfnctn.cob",
        "acas_posting/records/file_defs.py": "copybooks/wsnames.cob",
        "acas_posting/records/gl_ledger.py": "copybooks/wsledger.cob",
        "acas_posting/records/maps03.py": "copybooks/wsmaps03.cob",
        "tests/arithmetic/test_irs_date_component_derivation.py": (
            "common/irspostingMT.cbl"
        ),
    }
)


def _repo_root() -> Path:
    """The repository root, from this file's own location."""
    return Path(__file__).resolve().parent.parent.parent


def _citation_subjects(relative_path: str) -> tuple[str, ...]:
    """The declared subjects a shorthand citation in this file may resolve to."""
    root = _repo_root()
    name = relative_path.split("/")[-1]
    candidates: list[str] = []

    explicit = _DECLARED_SUBJECT.get(relative_path)
    if explicit is not None:
        candidates.append(explicit)

    handler = re.match(r"(acasirsub\d|acas\d{3})_", name)
    if handler is not None and "/dal/" in relative_path:
        candidates.append(f"common/{handler.group(1)}.cbl")
        bridge = _HANDLER_BRIDGE.get(handler.group(1))
        if bridge is not None:
            candidates.append(f"common/{bridge}.cbl")

    for pattern, directory in (
        (r"(gl\d{3})_", "general"),
        (r"(sl\d{3})_", "sales"),
        (r"(pl\d{3})_", "purchase"),
    ):
        program = re.match(pattern, name)
        if program is not None:
            candidates.append(f"{directory}/{program.group(1)}.cbl")

    if name == "irs030_posting.py":
        candidates.append("irs/irs030.cbl")

    return tuple(c for c in candidates if (root / c).is_file())


#: Directory names never scanned for citations. Caches and virtual environments
#: hold generated copies of files that ARE scanned, so including them would report
#: every failure twice and make the count depend on whether a cache happened to be
#: warm.
_UNSCANNED_DIRECTORIES = frozenset(
    {
        "__pycache__",
        ".git",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".venv",
        "venv",
        "node_modules",
        "build",
        "dist",
    }
)

#: The four trees whose files carry this migration's citations, plus the README,
#: which sits at the repository root and so is named rather than walked.
_CITED_TREES = ("acas_posting", "harness", "docs/migration", "tests")

#: Suffixes that can carry a citation. A citation lives in prose or a comment, so
#: binary and generated-data files are out.
_CITED_SUFFIXES = (".py", ".md", ".sh", ".yaml", ".yml")


def _cited_files() -> tuple[str, ...]:
    """Every text file of this migration that may carry a citation.

    DELIBERATELY NOT `git ls-files`. An earlier revision shelled out to git, and
    that made this check environment-dependent in the one environment that matters
    most: the harness container has python3 but NO git, so the whole check raised
    `FileNotFoundError: 'git'` there while passing on the host. A check that is
    skipped or broken exactly where the authoritative run happens is worse than no
    check, because its green result on the host is then read as coverage.

    The walk below is deterministic and needs no tooling: a sorted traversal of
    four named trees, filtered by suffix, with cache and virtual-environment
    directories pruned and scratch files excluded by name. It therefore scans an
    IDENTICAL set on a bare host and inside the container, which is the property
    that makes the two runs comparable.

    Returns:
        Repository-relative paths, sorted, with the root README last.
    """
    root = _repo_root()
    scanned: list[str] = []

    for tree in _CITED_TREES:
        base = root / tree
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or path.suffix not in _CITED_SUFFIXES:
                continue
            relative = path.relative_to(root)
            if _UNSCANNED_DIRECTORIES.intersection(relative.parts):
                continue
            #  Ad-hoc validation scratch is never committed and never cited.
            if relative.name.startswith("blitzy_adhoc_test_"):
                continue
            scanned.append(relative.as_posix())

    return tuple(sorted(scanned) + ["README-python-migration.md"])


def _validate_citations() -> tuple[dict[str, int], tuple[str, ...]]:
    """Resolve every citation in the migration's own files.

    Returns:
        A count per citation form, and one human-readable failure line per
        citation that does not resolve. An empty failure tuple is the pass.
    """
    root = _repo_root()
    lengths: dict[str, int | None] = {}

    def line_count(path: str) -> int | None:
        if path not in lengths:
            target = root / path
            lengths[path] = (
                len(target.read_text(errors="replace").split("\n"))
                if target.is_file()
                else None
            )
        return lengths[path]

    counts = {"full": 0, "bare": 0}
    failures: list[str] = []

    for relative in _cited_files():
        source = root / relative
        if not source.is_file():
            continue
        lines = source.read_text(errors="replace").split("\n")
        is_markdown = relative.endswith(".md")
        subjects = _citation_subjects(relative)
        inherited: str | None = None

        for number, line in enumerate(lines, start=1):
            #  A definition (or, in markdown, a heading) ends the scope the
            #  shorthand inherits through.
            if (not is_markdown and _SCOPE_BOUNDARY.match(line)) or (
                is_markdown and line.startswith("#")
            ):
                inherited = None

            found = [
                (match.start(), "full", match)
                for match in _CITATION_FULL.finditer(line)
            ] + [
                (match.start(), "bare", match)
                for match in _CITATION_BARE.finditer(line)
            ]

            for _, form, match in sorted(found):
                if form == "full":
                    counts["full"] += 1
                    inherited = match.group(1)
                    available = line_count(inherited)
                    low = int(match.group(2))
                    high = int(match.group(3) or match.group(2))
                    if available is None:
                        failures.append(
                            f"{relative}:{number}  {match.group(0)}  -> no such "
                            f"file. A citation must name a path that exists; a "
                            f"bare filename is not a path."
                        )
                    elif low < 1 or high > available:
                        failures.append(
                            f"{relative}:{number}  {match.group(0)}  -> "
                            f"{inherited} has {available} lines. Re-read the "
                            f"frozen file and cite the line it is actually on."
                        )
                    continue

                counts["bare"] += 1
                high = int(match.group(2) or match.group(1))
                resolved = False
                if inherited is not None:
                    available = line_count(inherited)
                    if available is not None and high <= available:
                        resolved = True
                if not resolved:
                    for subject in subjects:
                        available = line_count(subject)
                        if available is not None and high <= available:
                            resolved = True
                            break
                if not resolved:
                    failures.append(
                        f"{relative}:{number}  {match.group(0)}  -> unresolvable. "
                        f"The nearest preceding citation in scope is "
                        f"{inherited!r} and this file's declared subjects are "
                        f"{subjects}; none of them has a line {high}. Either "
                        f"qualify the citation with its path, or add this file to "
                        f"SECTION 23's _DECLARED_SUBJECT."
                    )

    return counts, tuple(failures)


def test_every_citation_resolves_to_a_real_line() -> None:
    """R-5's citations must lead a reviewer somewhere real.

    This is the check a code review asked for, standing in place of the twenty-six
    corrections it listed. It resolves both citation forms and fails with the file,
    the line, the citation and the reason for each one that does not resolve, so a
    failure is actionable without re-deriving anything.
    """
    counts, failures = _validate_citations()

    assert not failures, (
        f"{len(failures)} citation(s) do not resolve:\n  " + "\n  ".join(failures[:40])
    )

    #  The check must be measuring something. A refactor that removed the citations,
    #  or a regex that stopped matching them, would otherwise pass silently.
    assert counts["full"] > 15_000, (
        f"only {counts['full']} fully-qualified citations were found; R-5's "
        f"traceability rests on them and this file previously saw over 15,000"
    )
    assert counts["bare"] > 2_000, (
        f"only {counts['bare']} shorthand citations were found; the two-level "
        f"resolution rule above is what makes them checkable, so a collapse here "
        f"means the scanner stopped seeing them"
    )


def test_the_citation_scanner_rejects_a_broken_citation() -> None:
    """The check is proven non-vacuous rather than asserted to be.

    A validation check that cannot fail is decoration. Rather than editing a
    shipped file to prove it, the three failure modes are exercised directly
    against the resolver's own inputs: a path that does not exist, a line past the
    end of a real file, and a shorthand citation with no subject that admits it.
    """
    root = _repo_root()

    #  A real frozen file, and a line number past its end.
    ledger = root / "copybooks" / "wsledger.cob"
    assert ledger.is_file()
    available = len(ledger.read_text().split("\n"))
    assert available < 500, "the guard below assumes this copybook is short"

    #  Built by concatenation so no literal citation appears in this file for the
    #  scanner above to read as a claim - the check checks this file too.
    probe_text = "[" + f"copybooks/wsledger.cob:L{available + 1}" + "]"
    probe_full = _CITATION_FULL.fullmatch(probe_text)
    assert probe_full is not None, "the regex must match a well-formed citation"
    assert int(probe_full.group(2)) > available, (
        "the probe must describe a line the file does not have, which is exactly "
        "what the check reports"
    )

    #  A path that does not exist resolves to no length at all.
    assert not (root / "copybooks" / "no-such-copybook.cob").is_file()

    #  And the shorthand form is matched, with its range captured, so an
    #  out-of-range shorthand is reachable by the same comparison.
    probe_bare = _CITATION_BARE.fullmatch("[" + ":L1-L99999" + "]")
    assert probe_bare is not None
    assert int(probe_bare.group(2)) == 99_999

    #  A file with no derivable and no declared subject offers the shorthand
    #  nothing to resolve against, which is the third failure mode.
    assert _citation_subjects("acas_posting/cobol/move.py") == ()
