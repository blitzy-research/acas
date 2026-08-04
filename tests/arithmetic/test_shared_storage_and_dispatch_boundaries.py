"""Regression locks for shared COBOL storage and DAL call boundaries."""

from __future__ import annotations

import dataclasses

import pytest


pytestmark = pytest.mark.arithmetic


def test_system_cycle_redefines_is_one_storage_location() -> None:
    """Cyclea and Scycle are two names for the byte at wssystem.cob:L62-L63."""
    module = pytest.importorskip("acas_posting.records.system_record")
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
    clock = pytest.importorskip("acas_posting.clock")

    pinned = clock.pin_from_to_day(f"21{separator}09{separator}2025")

    assert pinned.to_day == "21/09/2025"
    assert pinned.run_date == 155127


def test_gl_batch_key_redefines_round_trips_through_both_views() -> None:
    """The grouped and six-digit batch keys cannot diverge."""
    records = pytest.importorskip("acas_posting.records.gl_batch")
    dal = pytest.importorskip("acas_posting.dal.acas007_gl_batch")

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
    records = pytest.importorskip("acas_posting.records.purchase_invoice")
    dal = pytest.importorskip("acas_posting.dal.acas026_pinvoice")

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
    records = pytest.importorskip("acas_posting.records.purchase_ledger")
    dal = pytest.importorskip("acas_posting.dal.acas022_purch")

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
    handler = pytest.importorskip("acas_posting.dal.acas000_system")
    status = pytest.importorskip("acas_posting.dal.status")
    file_access_module = pytest.importorskip(
        "acas_posting.records.file_access"
    )
    system_module = pytest.importorskip(
        "acas_posting.records.system_record"
    )
    flags_module = pytest.importorskip(
        "acas_posting.records.test_data_flags"
    )

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
    handler = pytest.importorskip(
        "acas_posting.dal.acasirsub1_irs_nominal"
    )
    status = pytest.importorskip("acas_posting.dal.status")
    nominal_module = pytest.importorskip(
        "acas_posting.records.irs_nominal"
    )
    file_access_module = pytest.importorskip(
        "acas_posting.records.file_access"
    )
    file_defs_module = pytest.importorskip(
        "acas_posting.records.file_defs"
    )
    system_module = pytest.importorskip(
        "acas_posting.records.system_record"
    )
    flags_module = pytest.importorskip(
        "acas_posting.records.test_data_flags"
    )

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
    handler = pytest.importorskip(
        "acas_posting.dal.acasirsub1_irs_nominal"
    )
    status = pytest.importorskip("acas_posting.dal.status")
    nominal_module = pytest.importorskip(
        "acas_posting.records.irs_nominal"
    )
    file_access_module = pytest.importorskip(
        "acas_posting.records.file_access"
    )

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
    connection = pytest.importorskip("acas_posting.dal.connection")
    system_module = pytest.importorskip(
        "acas_posting.records.system_record"
    )

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
    handler = pytest.importorskip("acas_posting.dal.acas007_gl_batch")
    connection = pytest.importorskip("acas_posting.dal.connection")
    batch_module = pytest.importorskip("acas_posting.records.gl_batch")
    file_access_module = pytest.importorskip(
        "acas_posting.records.file_access"
    )
    file_defs_module = pytest.importorskip(
        "acas_posting.records.file_defs"
    )
    system_module = pytest.importorskip(
        "acas_posting.records.system_record"
    )
    flags_module = pytest.importorskip(
        "acas_posting.records.test_data_flags"
    )

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
    handler = pytest.importorskip("acas_posting.dal.acas016_invoice")
    connection = pytest.importorskip("acas_posting.dal.connection")
    status = pytest.importorskip("acas_posting.dal.status")
    file_access_module = pytest.importorskip(
        "acas_posting.records.file_access"
    )
    file_defs_module = pytest.importorskip(
        "acas_posting.records.file_defs"
    )
    system_module = pytest.importorskip(
        "acas_posting.records.system_record"
    )
    flags_module = pytest.importorskip(
        "acas_posting.records.test_data_flags"
    )

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
