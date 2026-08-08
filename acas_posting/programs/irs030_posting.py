"""`irs030` - IRS nominal ledger posting [irs/irs030.cbl].

A PARTIAL migration: only the `Ledger-Postings-Add` section
[irs/irs030.cbl:L1569-L1730], which walks the SL/PL transfer file and updates the
IRS nominal ledger. The remaining 1,500-odd lines are interactive posting entry
and are out of scope, apart from the two VAT computes the posting path consumes
[irs/irs030.cbl:L1551], [irs/irs030.cbl:L1562] - the only `ROUNDED` sites here.

Three defects are reproduced, not repaired, and each leaves the database in a
state a corrected version would not:

  * Half-posted double entry. The debit account is rewritten BEFORE the credit
    account is even looked up [irs/irs030.cbl:L1635-L1652], so a missing credit
    account leaves a posted debit with no balancing credit and no posting record.
  * Lost update on the two VAT control accounts. They are read into snapshots
    before the loop [irs/irs030.cbl:L1602], [irs/irs030.cbl:L1612] and rewritten
    from those snapshots at end of job [irs/irs030.cbl:L1704-L1708], so any
    in-loop rewrite of the same accounts is overwritten.
  * A failure writing the posting record jumps straight to end of job
    [irs/irs030.cbl:L1673-L1678], which still performs both snapshot rewrites and
    the closes, so the partial state is committed rather than rolled back.

The end-of-job question that clears the transfer file
[irs/irs030.cbl:L1715-L1724] is a parameter of `run`, not a prompt, because its
answer truncates a table: the handler implements open-output as deleting every
row [common/acas008.cbl:L313-L319].

The linkage is the migration's third shape - `IRS-System-Params`,
`WS-System-Record`, `File-Defs` [irs/irs030.cbl:L552-L554] - with no calling-data
block, and this program contains no clock read.
"""

from __future__ import annotations

import dataclasses
import logging
from decimal import Decimal
from typing import Final, Mapping

from acas_posting.cobol import arithmetic, move
from acas_posting.cobol.field import FieldDescriptor, descriptors_for_copybook_record

# copy "Proc-ZZ100-ACAS-IRS-Calls.cob". [irs/irs030.cbl:L1732] The handler-named facade
# convention.
from acas_posting.dal import facade

from acas_posting.dal.status import FileFunction, FsReply, WeError

from acas_posting.records.irs_dflt import WsIrsDefaultRecord

from acas_posting.records.irs_nominal import WsIrsnlRecord

from acas_posting.records.irs_posting import PostingRecord

# copy "irswssystem.cob" replacing system-record by IRS-System-Params.
# [irs/irs030.cbl:L416] - the FIRST linkage parameter.
from acas_posting.records.irs_system import IrsSystemParams

from acas_posting.records.spl_irs_posting import WsIrsPostingRecord

from acas_posting.records.system_record import SystemRecord

from acas_posting.records.test_data_flags import AcasDalCommonData

from acas_posting.records.file_defs import FileDefs

from acas_posting.records.file_access import ALL_FIELDS as _FILE_ACCESS_FIELDS
from acas_posting.records.file_access import FileAccess

#: The program's only public entry point.
__all__: Final[tuple[str, ...]] = ("run",)

_LOG: Final[logging.Logger] = logging.getLogger(__name__)


# Rule R-5 requires that every field descriptor be traceable.


def _index(record_name: str) -> dict[str, FieldDescriptor]:
    """Index one dictionary record's flattened descriptors by field name.

    An `OCCURS` field appears once per occurrence with the same name and the same
    picture, so the first occurrence is the representative descriptor for every element
    of the table.
    """
    indexed: dict[str, FieldDescriptor] = {}
    for descriptor in descriptors_for_copybook_record(record_name):
        indexed.setdefault(descriptor.name, descriptor)
    return indexed


_NL: Final[dict[str, FieldDescriptor]] = _index("NL-Record")
_POST: Final[dict[str, FieldDescriptor]] = _index("Posting-Record")
_XFER: Final[dict[str, FieldDescriptor]] = _index("WS-IRS-Posting-Record")

_NL_OWNING: Final[FieldDescriptor] = _NL["NL-Owning"]
_NL_SUB_NOMINAL: Final[FieldDescriptor] = _NL["NL-Sub-Nominal"]
_NL_TYPE: Final[FieldDescriptor] = _NL["NL-Type"]
_NL_NAME: Final[FieldDescriptor] = _NL["NL-Name"]
_NL_DR: Final[FieldDescriptor] = _NL["NL-DR"]
_NL_CR: Final[FieldDescriptor] = _NL["NL-CR"]
_NL_DR_LAST: Final[FieldDescriptor] = _NL["NL-DR-Last"]
_NL_CR_LAST: Final[FieldDescriptor] = _NL["NL-CR-Last"]
_NL_AC: Final[FieldDescriptor] = _NL["NL-AC"]
_NL_POINTER: Final[FieldDescriptor] = _NL["NL-Pointer"]

_POST_KEY: Final[FieldDescriptor] = _POST["Post-Key"]
_POST_CODE: Final[FieldDescriptor] = _POST["Post-Code"]
_POST_DATE: Final[FieldDescriptor] = _POST["Post-Date"]
_POST_DR: Final[FieldDescriptor] = _POST["Post-DR"]
_POST_CR: Final[FieldDescriptor] = _POST["Post-CR"]
_POST_AMOUNT: Final[FieldDescriptor] = _POST["Post-Amount"]
_POST_LEGEND: Final[FieldDescriptor] = _POST["Post-Legend"]
_VAT_AC_DEF: Final[FieldDescriptor] = _POST["Vat-AC-Def"]
_POST_VAT_SIDE: Final[FieldDescriptor] = _POST["Post-Vat-Side"]
_VAT_AMOUNT: Final[FieldDescriptor] = _POST["Vat-Amount"]

_XFER_AMOUNT: Final[FieldDescriptor] = _XFER["WS-IRS-Post-Amount"]
_XFER_VAT_AMOUNT: Final[FieldDescriptor] = _XFER["WS-IRS-Vat-Amount"]
_XFER_POST_DR: Final[FieldDescriptor] = _XFER["WS-IRS-Post-DR"]
_XFER_POST_CR: Final[FieldDescriptor] = _XFER["WS-IRS-Post-CR"]
_XFER_POST_CODE: Final[FieldDescriptor] = _XFER["WS-IRS-Post-Code"]
_XFER_POST_DATE: Final[FieldDescriptor] = _XFER["WS-IRS-Post-Date"]
_XFER_POST_LEGEND: Final[FieldDescriptor] = _XFER["WS-IRS-Post-Legend"]
_XFER_VAT_AC_DEF: Final[FieldDescriptor] = _XFER["WS-IRS-Vat-AC-Def"]
_XFER_POST_VAT_SIDE: Final[FieldDescriptor] = _XFER["WS-IRS-Post-Vat-Side"]

# `File-Access` [copybooks/wsfnctn.cob] - only the function-code receiver is stored into
# by this module; the status fields are read, never written here.
_FILE_FUNCTION: Final[FieldDescriptor] = next(
    descriptor
    for descriptor in _FILE_ACCESS_FIELDS
    if descriptor.name == "File-Function"
)

# `next-post` [copybooks/irswssystem.cob:L25] - the IRS posting key allocator, a field
# of the FIRST linkage parameter.
_NEXT_POST: Final[FieldDescriptor] = next(
    descriptor
    for descriptor in IrsSystemParams.FIELDS
    if descriptor.name == "next-post"
)

# Four receivers in the in-scope region are declared in `irs030`'s OWN WORKING-STORAGE
# rather than in any copybook, so the generated dictionary - which is built from the
# copybooks, the bridge and the schema - has no entry for them.
_POST_RECORD_CNT: Final[FieldDescriptor] = dataclasses.replace(
    _NL_POINTER,
    name="Post-Record-Cnt",
    dictionary_key=None,
    source_locator="irs/irs030.cbl:L272",
)
_NL31_DR: Final[FieldDescriptor] = dataclasses.replace(
    _NL_DR,
    name="nl31-dr",
    dictionary_key=None,
    source_locator="irs/irs030.cbl:L355",
)
_NL31_CR: Final[FieldDescriptor] = dataclasses.replace(
    _NL_CR,
    name="nl31-cr",
    dictionary_key=None,
    source_locator="irs/irs030.cbl:L356",
)
_NL32_DR: Final[FieldDescriptor] = dataclasses.replace(
    _NL_DR,
    name="nl32-dr",
    dictionary_key=None,
    source_locator="irs/irs030.cbl:L370",
)
_NL32_CR: Final[FieldDescriptor] = dataclasses.replace(
    _NL_CR,
    name="nl32-cr",
    dictionary_key=None,
    source_locator="irs/irs030.cbl:L371",
)

# `we-error = 2` is tested for EQUALITY at [irs/irs030.cbl:L1630] and
# [irs/irs030.cbl:L1648].
_IRS_WE_ERROR_RECORD_NOT_FOUND: Final[int] = 2

# The section's message identifiers, declared in `irs030`'s own WORKING-STORAGE and
# retained ONLY as log text.
_IR031: Final[str] = "IR031 No Ledger Posting file found. Process Aborted"
_IR032: Final[str] = "IR032 Invalid key 1 = "
_IR033: Final[str] = "IR033 Invalid key 2 = "

#: What stands where the frozen program displayed the account number. IR032 and
#: IR033 each end in "= " because the frozen source displays the message and then
#: the account beside it [irs/irs030.cbl:L1631-L1632], [irs/irs030.cbl:L1649-L1650].
#: The message identifier is kept exactly, and a FIXED literal takes the value's
#: place so that a reader sees a value was withheld rather than a log truncated.
#: It is a compile-time constant of this migration, which is what the safe-event
#: schema in `dal/status.py` permits; the account identifier itself it forbids at
#: every level (CWE-532).
#  A redacted-tail rendering ("...45") was also written for this line; total
#  withholding supersedes it, because the safe-event schema bars an account
#  identifier at EVERY level and a tail is still part of one. The value stays in
#  IRSPOSTING-REC and in the dump, so nothing an auditor needs is lost.
_ACCOUNT_WITHHELD: Final[str] = "<withheld: see dal/status.py safe-event schema>"
_IR03A: Final[str] = "IR03A IRSUB1-31 returns "
_IR03B: Final[str] = "IR03B IRSUB1-32 returns "
_IR914: Final[str] = "IR914 Error on irspostingMT processing, FS-Reply = "

# The two VAT control accounts, selected by the SL/PL side that produced the transfer
# record. THE CROSS-PROGRAM CONTRACT.
_VAT_AC_PURCHASE: Final[int] = 31
_VAT_AC_SALES: Final[int] = 32

_DEF_ACS_SUBSCRIPT_31: Final[int] = _VAT_AC_PURCHASE - 1
_DEF_ACS_SUBSCRIPT_32: Final[int] = _VAT_AC_SALES - 1



# The debit and credit legs both test the transfer record's VAT side, and each adds the
# VAT to THE OPPOSITE LEG's accumulator - see the reproduction sites.
_SIDE_CR: Final[str] = "CR"
_SIDE_DR: Final[str] = "DR"


@dataclasses.dataclass(slots=True)
class _NlSnapshot:
    """`nl31-record` / `nl32-record` - hand-declared in `irs030`'s WORKING-STORAGE.

    Two divergences from the copybook are recorded rather than smoothed away, because a
    reader diffing the two declarations will find them.
    """

    owning: int = 0
    sub_nominal: int = 0
    tipe: str = " "
    name: str = " " * 24
    dr: Decimal = Decimal("0.00")
    cr: Decimal = Decimal("0.00")
    dr_last: tuple[Decimal, ...] = (Decimal("0.00"),) * 4
    cr_last: tuple[Decimal, ...] = (Decimal("0.00"),) * 4
    ac: str = " "
    pointer: int = 0


def _move_nl_record_to_snapshot(
    source: WsIrsnlRecord,
    receiver: _NlSnapshot,
) -> None:
    """`move WS-IRSNL-Record to nl31-record.` - the group move, one direction.

    A group MOVE between identically laid-out records is a byte-image copy: with no
    receiving width of its own to truncate against, the group receives exactly what the
    sender presents.
    """
    receiver.owning = move.move(
        source.nl_key.nl_owning, _NL_OWNING, sending_field=_NL_OWNING
    )
    receiver.sub_nominal = move.move(
        source.nl_key.nl_sub_nominal, _NL_SUB_NOMINAL, sending_field=_NL_SUB_NOMINAL
    )
    receiver.tipe = move.move(source.nl_type, _NL_TYPE, sending_field=_NL_TYPE)
    receiver.name = move.move(
        source.nl_data.nl_name, _NL_NAME, sending_field=_NL_NAME
    )
    receiver.dr = move.move(source.nl_data.nl_dr, _NL_DR, sending_field=_NL_DR)
    receiver.cr = move.move(source.nl_data.nl_cr, _NL_CR, sending_field=_NL_CR)
    receiver.dr_last = tuple(
        move.move(element, _NL_DR_LAST, sending_field=_NL_DR_LAST)
        for element in source.nl_data.nl_dr_last
    )
    receiver.cr_last = tuple(
        move.move(element, _NL_CR_LAST, sending_field=_NL_CR_LAST)
        for element in source.nl_data.nl_cr_last
    )
    receiver.ac = move.move(source.nl_data.nl_ac, _NL_AC, sending_field=_NL_AC)
    receiver.pointer = move.move(
        source.nl_pointer_view.nl_pointer, _NL_POINTER, sending_field=_NL_POINTER
    )


def _move_snapshot_to_nl_record(
    source: _NlSnapshot,
    receiver: WsIrsnlRecord,
) -> None:
    """`move nl31-record to WS-IRSNL-Record.` - the group move, other direction.

    The mirror of `_move_nl_record_to_snapshot`, and the mechanism of anomaly A-5.
    """
    receiver.nl_key.nl_owning = move.move(
        source.owning, _NL_OWNING, sending_field=_NL_OWNING
    )
    receiver.nl_key.nl_sub_nominal = move.move(
        source.sub_nominal, _NL_SUB_NOMINAL, sending_field=_NL_SUB_NOMINAL
    )
    receiver.nl_type = move.move(source.tipe, _NL_TYPE, sending_field=_NL_TYPE)
    receiver.nl_data.nl_name = move.move(
        source.name, _NL_NAME, sending_field=_NL_NAME
    )
    receiver.nl_data.nl_dr = move.move(source.dr, _NL_DR, sending_field=_NL_DR)
    receiver.nl_data.nl_cr = move.move(source.cr, _NL_CR, sending_field=_NL_CR)
    receiver.nl_data.nl_dr_last = tuple(
        move.move(element, _NL_DR_LAST, sending_field=_NL_DR_LAST)
        for element in source.dr_last
    )
    receiver.nl_data.nl_cr_last = tuple(
        move.move(element, _NL_CR_LAST, sending_field=_NL_CR_LAST)
        for element in source.cr_last
    )
    receiver.nl_data.nl_ac = move.move(source.ac, _NL_AC, sending_field=_NL_AC)
    receiver.nl_pointer_view.nl_pointer = move.move(
        source.pointer, _NL_POINTER, sending_field=_NL_POINTER
    )


@dataclasses.dataclass(slots=True)
class _WorkingStorage:
    """`irs030`'s WORKING-STORAGE and LINKAGE, as one explicitly passed holder.

    COBOL working storage is visible to every paragraph of the program.
    """

    irs_system_params: IrsSystemParams
    ws_system_record: SystemRecord
    file_defs: FileDefs

    file_access: FileAccess
    dal_common: AcasDalCommonData
    ws_irsnl_record: WsIrsnlRecord
    ws_irs_default_record: WsIrsDefaultRecord
    posting_record: PostingRecord
    ws_irs_posting_record: WsIrsPostingRecord
    nl31_record: _NlSnapshot
    nl32_record: _NlSnapshot
    post_record_cnt: int

    # The answer to the end-of-job question at [irs/irs030.cbl:L1717], supplied as an
    # input because it gates a database write. See `run`.
    clear_posting_file: bool

    # NOT A COBOL FIELD.  The caller's keyword-only handler declarations - chiefly
    # the transport-security policy - forwarded to every facade `PERFORM` this
    # section issues.  There is no COBOL counterpart because the frozen bridge has
    # none: its connect passes six values and no transport policy at all
    # [copybooks/mysql-procedures.cpy:L72-L77], transport being compiled into
    # `cobmysqlapi.c`.
    #
    # An empty mapping is a STATEMENT, not an omission: every handler declares
    # `transport: TransportSecurity | None = None` and
    # `connection._require_permitted_connection` resolves `None` against the
    # INSTALLED PROCESS POLICY, which under the exact-parity default reports an
    # unencrypted non-local hop at WARNING and connects, exactly as the compiled
    # open does (rule R-3).  Carried opaquely - nothing here reads a key of it - and
    # `dal/facade.py` projects it onto whatever extras each handler declares.
    dal_options: Mapping[str, object]


def _net_section(
    posting_record: PostingRecord,
    ws_vat_current: Decimal,
) -> None:
    """`Net section.` - derive VAT from a VAT-EXCLUSIVE amount.

    In scope because the posting path consumes the VAT amount this section produces. Its
    only callers in the frozen program are the interactive VAT-entry paragraph, which is
    out of scope; the computation itself is not.
    """
    # ANOMALY A-19 [irs/irs030.cbl:L1550] - a superseded, commented-out variant of this
    # compute survives adjacent to the live one, referencing a differently named rate
    # field `vat` where the live statement references `WS-Vat-Current`.

    posting_record.vat_amount = arithmetic.compute(
        lambda: posting_record.post_amount * ws_vat_current / 100,
        _VAT_AMOUNT,
        rounded=True,
    )
    _net_main_exita()


def _net_main_exita() -> None:
    """`Main-Exita.` - the `Net` section's exit paragraph.

    FINDING the statement is a plain `EXIT`, not `EXIT SECTION` - a no-op continuation
    whose only purpose is to give the paragraph a body.
    """
    return


def _gross_section(
    posting_record: PostingRecord,
    ws_vat_current: Decimal,
) -> None:
    """`Gross section.` - extract VAT from a VAT-INCLUSIVE amount.

    Two stores, and they differ in rounding: the compute is ROUNDED, the subtraction
    that follows it is not. See Q-18 for why the compound expression is transcribed
    exactly as parenthesised.
    """
    # ANOMALY A-19 [irs/irs030.cbl:L1561] - a superseded, commented-out variant of this
    # compute survives adjacent to the live one, again referencing `vat` where the live
    # statement references `WS-Vat-Current`.

    # 1562 compute vat-amount rounded = 1563 post-amount - (post-amount / ( (WS-Vat-
    # Current + 100) / 100)). ROUNDED store 2 of the 2 this module owns.
    posting_record.vat_amount = arithmetic.compute(
        lambda: posting_record.post_amount
        - (posting_record.post_amount / ((ws_vat_current + 100) / 100)),
        _VAT_AMOUNT,
        rounded=True,
    )

    posting_record.post_amount = arithmetic.subtract_from(
        posting_record.vat_amount,
        receiver_value=posting_record.post_amount,
        receiving=_POST_AMOUNT,
    )
    _gross_main_exitb()


def _gross_main_exitb() -> None:
    """`Main-Exitb.` - the `Gross` section's exit paragraph.

    A plain `EXIT`, as in `Main-Exita`; retained as a named function per R-5.
    """
    return


def _ledger_postings_add(ws: _WorkingStorage) -> None:
    """`Ledger-Postings-Add section.` [irs/irs030.cbl:L1569] - the migrated surface.

    The three `go to main99-exit` sites above are the ABORT-WITH-NOTHING disposition:
    `main99-exit` is `exit section.` [irs/irs030.cbl:L1730], so `EOJ` is bypassed
    entirely and neither VAT-snapshot rewrite nor any close takes place.
    """
    facade.acas008_open_input(
        facade.FacadeContext(
            ws.ws_system_record,
            ws.ws_irs_posting_record,
            ws.file_access,
            ws.file_defs,
            ws.dal_common,
            ws.dal_options,
        ),
    )

    # 1579 if FS-Reply not = zero This site reads FS-Reply. Five later sites read we-
    # error instead.
    if arithmetic.compare(ws.file_access.fs_reply, FsReply.SUCCESS) != 0:
        _LOG.error("%s", _IR031)
        _main99_exit()
        return

    # 1585 move 3 to file-function. The function code is bound to the operation
    # vocabulary's own member rather than written as a bare literal.
    ws.file_access.file_function = move.move(
        int(FileFunction.READ_NEXT), _FILE_FUNCTION
    )

    # 1586 perform acasirsub3. *> call-irsub3.
    facade.acasirsub3(
        facade.FacadeContext(
            ws.ws_system_record,
            ws.ws_irs_default_record,
            ws.file_access,
            ws.file_defs,
            ws.dal_common,
            ws.dal_options,
        ),
    )


    # THE CROSS-PROGRAM CONTRACT: subscript 31 is the account the purchase posting
    # programs nominate [purchase/pl060.cbl:L993], [purchase/pl100.cbl:L640]; subscript
    # 32 is the one the sales invoice poster nominates [sales/sl060.cbl:L1139].

    ws.ws_irsnl_record.nl_key.nl_owning = move.move(
        ws.ws_irs_default_record.def_group[_DEF_ACS_SUBSCRIPT_31].def_acs,
        _NL_OWNING,
    )
    ws.ws_irsnl_record.nl_key.nl_sub_nominal = move.move_figurative(
        move.ZERO, _NL_SUB_NOMINAL
    )
    facade.acasirsub1_read_indexed(
        facade.FacadeContext(
            ws.ws_system_record,
            ws.ws_irsnl_record,
            ws.file_access,
            ws.file_defs,
            ws.dal_common,
            ws.dal_options,
        ),
    )
    # 1597 if we-error not = zero "not = zero" here, where the two in-loop account
    # lookups test for equality with 2.
    if arithmetic.compare(ws.file_access.we_error, WeError.SUCCESS) != 0:
        _LOG.error("%s%s", _IR03A, ws.file_access.we_error)
        # 1600 accept WS-Reply at 2340 An acknowledgement pause with no database effect
        # - dropped. The control transfer that follows it is preserved. 1601 go to
        # main99-exit.
        _main99_exit()
        return

    # 1602 move WS-IRSNL-Record to nl31-record.
    _move_nl_record_to_snapshot(ws.ws_irsnl_record, ws.nl31_record)


    ws.ws_irsnl_record.nl_key.nl_owning = move.move(
        ws.ws_irs_default_record.def_group[_DEF_ACS_SUBSCRIPT_32].def_acs,
        _NL_OWNING,
    )
    # 1605 move zero to nl-sub-nominal.
    ws.ws_irsnl_record.nl_key.nl_sub_nominal = move.move_figurative(
        move.ZERO, _NL_SUB_NOMINAL
    )
    facade.acasirsub1_read_indexed(
        facade.FacadeContext(
            ws.ws_system_record,
            ws.ws_irsnl_record,
            ws.file_access,
            ws.file_defs,
            ws.dal_common,
            ws.dal_options,
        ),
    )
    if arithmetic.compare(ws.file_access.we_error, WeError.SUCCESS) != 0:
        _LOG.error("%s%s", _IR03B, ws.file_access.we_error)
        _main99_exit()
        return

    # 1612 move WS-IRSNL-Record to nl32-record. ANOMALY A-5 [irs/irs030.cbl:L1612] - the
    # sales-side VAT control account, snapshotted before the loop and rewritten from the
    # snapshot at [irs/irs030.cbl:L1708].
    _move_nl_record_to_snapshot(ws.ws_irsnl_record, ws.nl32_record)

    _LOG.info("Updating Nominal Ledger")

    # 1617 perform acasirsub4-Open. *> call-irsub4. FINDING - this open has NEITHER a
    # facade error check nor an inline test.
    facade.acasirsub4_open(
        facade.FacadeContext(
            ws.ws_system_record,
            ws.posting_record,
            ws.file_access,
            ws.file_defs,
            ws.dal_common,
            ws.dal_options,
        ),
    )

    # 1619-1700 Input-Loop. Both of the loop's exits are `go to EOJ`, so the post-loop
    # block below is reached on either.
    _input_loop(ws)

    _eoj(ws)
    _eoj_q1(ws)
    _main99_exit()


def _input_loop(ws: _WorkingStorage) -> None:
    """`Input-Loop.` - the transfer-file walk, and where anomaly A-4 lives.

    FINDING the VAT side is applied ASYMMETRICALLY, and the condition is INVERTED
    relative to the leg it affects.
    """
    while True:
        facade.acas008_read_next(
            facade.FacadeContext(
                ws.ws_system_record,
                ws.ws_irs_posting_record,
                ws.file_access,
                ws.file_defs,
                ws.dal_common,
                ws.dal_options,
            ),
        )

        if arithmetic.compare(ws.file_access.fs_reply, FsReply.END_OF_FILE) == 0:
            # 1622 go to EOJ. GO TO class 2 - loop terminator. The post-loop block is
            # the caller's `_eoj` / `_eoj_q1` / `_main99_exit` sequence.
            break

        # 1623 add 1 to Post-Record-Cnt. A display counter only: it feeds the completion
        # message at [irs/irs030.cbl:L1714] and reaches no table.
        ws.post_record_cnt = arithmetic.add_to(
            1,
            receiver_value=ws.post_record_cnt,
            receiving=_POST_RECORD_CNT,
        )


        ws.ws_irsnl_record.nl_key.nl_owning = move.move(
            ws.ws_irs_posting_record.ws_irs_post_dr,
            _NL_OWNING,
            sending_field=_XFER_POST_DR,
        )
        ws.ws_irsnl_record.nl_key.nl_sub_nominal = move.move_figurative(
            move.ZERO, _NL_SUB_NOMINAL
        )
        facade.acasirsub1_read_indexed(
            facade.FacadeContext(
                ws.ws_system_record,
                ws.ws_irsnl_record,
                ws.file_access,
                ws.file_defs,
                ws.dal_common,
                ws.dal_options,
            ),
        )

        # 1630 if we-error = 2 EQUALITY WITH 2 - deliberately not widened to "not =
        # zero".
        if (
            arithmetic.compare(
                ws.file_access.we_error, _IRS_WE_ERROR_RECORD_NOT_FOUND
            )
            == 0
        ):
            #  THE ACCOUNT NUMBER IS NOT LOGGED, AND ITS ABSENCE IS DELIBERATE.
            #  The frozen program displays IR032 and then `WS-IRS-Post-DR`
            #  [irs/irs030.cbl:L1631-L1632], but a screen a clerk is standing at
            #  is not a log file: `dal/status.py`'s safe-event schema forbids "an
            #  account / batch / posting / invoice / customer / supplier
            #  identifier" at EVERY level (CWE-532), and a posting run's log
            #  outlives the run and travels. The DISPOSITION is unchanged - the
            #  message identifier and the clean skip below are exactly the frozen
            #  ones - and the identifier is recoverable from IRSPOSTING-REC, which
            #  the run leaves in place. Agent Action Plan section 0.3.4 governs:
            #  a diagnostic with no database effect becomes a log record, and this
            #  one alters no control flow and reaches no table.
            _LOG.error("%s%s", _IR032, _ACCOUNT_WITHHELD)
            # 1633 accept WS-Reply at 2340 - pause, dropped 1634 go to Input-Loop. GO TO
            # class 1 - loop back. CLEAN SKIP.
            continue

        # 1635 add WS-IRS-Post-Amount to nl-dr.
        ws.ws_irsnl_record.nl_data.nl_dr = arithmetic.add_to(
            ws.ws_irs_posting_record.ws_irs_post_amount,
            receiver_value=ws.ws_irsnl_record.nl_data.nl_dr,
            receiving=_NL_DR,
        )

        if ws.ws_irs_posting_record.ws_irs_post_vat_side == _SIDE_CR:
            ws.ws_irsnl_record.nl_data.nl_dr = arithmetic.add_to(
                ws.ws_irs_posting_record.ws_irs_vat_amount,
                receiver_value=ws.ws_irsnl_record.nl_data.nl_dr,
                receiving=_NL_DR,
            )

        # 1641 perform acasirsub1-Rewrite. ANOMALY A-4 [irs/irs030.cbl:L1641] - THE
        # DEBIT IS COMMITTED HERE, before the credit account is so much as looked up at
        # [irs/irs030.cbl:L1647].
        facade.acasirsub1_rewrite(
            facade.FacadeContext(
                ws.ws_system_record,
                ws.ws_irsnl_record,
                ws.file_access,
                ws.file_defs,
                ws.dal_common,
                ws.dal_options,
            ),
        )


        ws.ws_irsnl_record.nl_key.nl_owning = move.move(
            ws.ws_irs_posting_record.ws_irs_post_cr,
            _NL_OWNING,
            sending_field=_XFER_POST_CR,
        )
        ws.ws_irsnl_record.nl_key.nl_sub_nominal = move.move_figurative(
            move.ZERO, _NL_SUB_NOMINAL
        )
        facade.acasirsub1_read_indexed(
            facade.FacadeContext(
                ws.ws_system_record,
                ws.ws_irsnl_record,
                ws.file_access,
                ws.file_defs,
                ws.dal_common,
                ws.dal_options,
            ),
        )

        if (
            arithmetic.compare(
                ws.file_access.we_error, _IRS_WE_ERROR_RECORD_NOT_FOUND
            )
            == 0
        ):
            #  As IR032 above: the message identifier only. The frozen display of
            #  `WS-IRS-Post-CR` [irs/irs030.cbl:L1649-L1650] is an account
            #  identifier, which the safe-event schema in `dal/status.py` bars from
            #  a log record at every level (CWE-532). The half-posted double entry
            #  this skip leaves behind - anomaly A-4 - is unaffected: the debit has
            #  already been rewritten and the `continue` below is the frozen
            #  `go to Input-Loop`.
            _LOG.error("%s%s", _IR033, _ACCOUNT_WITHHELD)
            # 1651 accept WS-Reply at 2340 - pause, dropped 1652 go to Input-Loop. GO TO
            # class 1 - loop back.
            continue

        ws.ws_irsnl_record.nl_data.nl_cr = arithmetic.add_to(
            ws.ws_irs_posting_record.ws_irs_post_amount,
            receiver_value=ws.ws_irsnl_record.nl_data.nl_cr,
            receiving=_NL_CR,
        )

        if ws.ws_irs_posting_record.ws_irs_post_vat_side == _SIDE_DR:
            ws.ws_irsnl_record.nl_data.nl_cr = arithmetic.add_to(
                ws.ws_irs_posting_record.ws_irs_vat_amount,
                receiver_value=ws.ws_irsnl_record.nl_data.nl_cr,
                receiving=_NL_CR,
            )

        facade.acasirsub1_rewrite(
            facade.FacadeContext(
                ws.ws_system_record,
                ws.ws_irsnl_record,
                ws.file_access,
                ws.file_defs,
                ws.dal_common,
                ws.dal_options,
            ),
        )


        ws.posting_record.post_code = move.move(
            ws.ws_irs_posting_record.ws_irs_post_code,
            _POST_CODE,
            sending_field=_XFER_POST_CODE,
        )
        # 1662 move WS-IRS-Post-Date to post-date. THE DATE ARRIVES IN THE DATA. This is
        # the only date the section handles and it is carried straight through,
        # unconverted.
        ws.posting_record.post_date = move.move(
            ws.ws_irs_posting_record.ws_irs_post_date,
            _POST_DATE,
            sending_field=_XFER_POST_DATE,
        )
        ws.posting_record.post_cr = move.move(
            ws.ws_irs_posting_record.ws_irs_post_cr,
            _POST_CR,
            sending_field=_XFER_POST_CR,
        )
        ws.posting_record.post_dr = move.move(
            ws.ws_irs_posting_record.ws_irs_post_dr,
            _POST_DR,
            sending_field=_XFER_POST_DR,
        )
        ws.posting_record.post_amount = move.move(
            ws.ws_irs_posting_record.ws_irs_post_amount,
            _POST_AMOUNT,
            sending_field=_XFER_AMOUNT,
        )
        ws.posting_record.post_legend = move.move(
            ws.ws_irs_posting_record.ws_irs_post_legend,
            _POST_LEGEND,
            sending_field=_XFER_POST_LEGEND,
        )
        ws.posting_record.vat_ac_def = move.move(
            ws.ws_irs_posting_record.ws_irs_vat_ac_def,
            _VAT_AC_DEF,
            sending_field=_XFER_VAT_AC_DEF,
        )
        ws.posting_record.post_vat_side = move.move(
            ws.ws_irs_posting_record.ws_irs_post_vat_side,
            _POST_VAT_SIDE,
            sending_field=_XFER_POST_VAT_SIDE,
        )
        ws.posting_record.vat_amount = move.move(
            ws.ws_irs_posting_record.ws_irs_vat_amount,
            _VAT_AMOUNT,
            sending_field=_XFER_VAT_AMOUNT,
        )

        ws.posting_record.post_key = move.move(
            ws.irs_system_params.next_post,
            _POST_KEY,
            sending_field=_NEXT_POST,
        )
        # 1671 add 1 to next-post. THE INCREMENT PRECEDES THE WRITE.
        ws.irs_system_params.next_post = arithmetic.add_to(
            1,
            receiver_value=ws.irs_system_params.next_post,
            receiving=_NEXT_POST,
        )

        facade.acasirsub4_write(
            facade.FacadeContext(
                ws.ws_system_record,
                ws.posting_record,
                ws.file_access,
                ws.file_defs,
                ws.dal_common,
                ws.dal_options,
            ),
        )

        # 1674 if we-error not = zero HANDLER.
        if arithmetic.compare(ws.file_access.we_error, WeError.SUCCESS) != 0:
            _LOG.error("%s%s", _IR914, ws.file_access.we_error)
            # 1677 accept WS-Reply at 2355 - pause, dropped 1678 go to EOJ. GO TO class
            # 2 - loop terminator. THE WRITE-FAILURE JUMP.
            break


        if arithmetic.compare(ws.ws_irs_posting_record.ws_irs_vat_ac_def, 0) == 0:
            # 1683 go to Input-Loop. GO TO class 1 - loop back, skipping the VAT ladder
            # entirely. The guard is preserved.
            continue

        # THE FOUR-WAY VAT LADDER. A NESTED if/else CHAIN, not four sibling `if`s.
        if (
            arithmetic.compare(
                ws.ws_irs_posting_record.ws_irs_vat_ac_def, _VAT_AC_PURCHASE
            )
            == 0
            and ws.ws_irs_posting_record.ws_irs_post_vat_side == _SIDE_CR
        ):
            ws.nl31_record.cr = arithmetic.add_to(
                ws.ws_irs_posting_record.ws_irs_vat_amount,
                receiver_value=ws.nl31_record.cr,
                receiving=_NL31_CR,
            )
        else:
            if (
                arithmetic.compare(
                    ws.ws_irs_posting_record.ws_irs_vat_ac_def, _VAT_AC_PURCHASE
                )
                == 0
                and ws.ws_irs_posting_record.ws_irs_post_vat_side == _SIDE_DR
            ):
                ws.nl31_record.dr = arithmetic.add_to(
                    ws.ws_irs_posting_record.ws_irs_vat_amount,
                    receiver_value=ws.nl31_record.dr,
                    receiving=_NL31_DR,
                )
            else:
                if (
                    arithmetic.compare(
                        ws.ws_irs_posting_record.ws_irs_vat_ac_def, _VAT_AC_SALES
                    )
                    == 0
                    and ws.ws_irs_posting_record.ws_irs_post_vat_side == _SIDE_CR
                ):
                    ws.nl32_record.cr = arithmetic.add_to(
                        ws.ws_irs_posting_record.ws_irs_vat_amount,
                        receiver_value=ws.nl32_record.cr,
                        receiving=_NL32_CR,
                    )
                else:
                    if (
                        arithmetic.compare(
                            ws.ws_irs_posting_record.ws_irs_vat_ac_def,
                            _VAT_AC_SALES,
                        )
                        == 0
                        and ws.ws_irs_posting_record.ws_irs_post_vat_side
                        == _SIDE_DR
                    ):
                        ws.nl32_record.dr = arithmetic.add_to(
                            ws.ws_irs_posting_record.ws_irs_vat_amount,
                            receiver_value=ws.nl32_record.dr,
                            receiving=_NL32_DR,
                        )

        # 1700 go to Input-Loop. GO TO class 1 - loop back.
        continue


def _eoj(ws: _WorkingStorage) -> None:
    """`EOJ.` - the post-loop block, and the site of anomaly A-5's lost update.

    This is the block both class-2 transfers reach and all three class-3 transfers skip.
    Dropping any part of it would lose the section's most important database effects, so
    it is reproduced in full and in order.
    """
    # 1704 move nl31-record to WS-IRSNL-Record. ANOMALY A-5 [irs/irs030.cbl:L1704] - the
    # live nominal-ledger record is OVERWRITTEN from the pre-loop snapshot.
    _move_snapshot_to_nl_record(ws.nl31_record, ws.ws_irsnl_record)

    # 1705 perform acasirsub1-Rewrite. ANOMALY A-5 [irs/irs030.cbl:L1705] - THE LOST
    # UPDATE.
    facade.acasirsub1_rewrite(
        facade.FacadeContext(
            ws.ws_system_record,
            ws.ws_irsnl_record,
            ws.file_access,
            ws.file_defs,
            ws.dal_common,
            ws.dal_options,
        ),
    )

    # 1707 move nl32-record to WS-IRSNL-Record. ANOMALY A-5 [irs/irs030.cbl:L1707] - as
    # above, for account 32. Reproduced deliberately per R-4; DO NOT FIX.
    _move_snapshot_to_nl_record(ws.nl32_record, ws.ws_irsnl_record)

    # 1708 perform acasirsub1-Rewrite. ANOMALY A-5 [irs/irs030.cbl:L1708] - the second
    # half of the lost update. Reproduced deliberately per R-4; DO NOT FIX.
    facade.acasirsub1_rewrite(
        facade.FacadeContext(
            ws.ws_system_record,
            ws.ws_irsnl_record,
            ws.file_access,
            ws.file_defs,
            ws.dal_common,
            ws.dal_options,
        ),
    )


    facade.acasirsub4_close(
        facade.FacadeContext(
            ws.ws_system_record,
            ws.posting_record,
            ws.file_access,
            ws.file_defs,
            ws.dal_common,
            ws.dal_options,
        ),
    )

    facade.acas008_close(
        facade.FacadeContext(
            ws.ws_system_record,
            ws.ws_irs_posting_record,
            ws.file_access,
            ws.file_defs,
            ws.dal_common,
            ws.dal_options,
        ),
    )


    _LOG.info("Processing Complete on %s records", ws.post_record_cnt)


def _eoj_q1(ws: _WorkingStorage) -> None:
    """`EOJ-q1.` - the end-of-job question that decides whether the table is cleared.

    Verbatim [irs/irs030.cbl:L1715-L1727]::

        1715 EOJ-q1.
        1716      display  "Can I clear the Ledgers Posting file? [Y]" at 1401 with erase eol.
        1717      accept   WS-Reply at 1440 with foreground-color 6 UPPER.
        1718      if       WS-Reply not = "Y" and not = "N"
        1719               go to EOJ-q1.
        1720      if       WS-Reply = "Y"
        1721  *>             open output irs-post-file
        1722  *>             close irs-post-file.
        1723               perform acas008-Open-Output    *>         performs a acas008-Delete-All
        1724               perform acas008-Close.
        1725      display  "Note counts and any messages" at 1401 with erase eol.
        1726      accept   WS-Reply at 1430.
        1727      display  space at 1401 with erase eol.

    THIS PROMPT IS AN INPUT, NOT DECORATION.  Answering `"Y"` opens the transfer
    file for output, and for this handler opening for output means DELETING EVERY
    ROW - the maintainer's own comment at [irs/irs030.cbl:L1723] records it as
    `*> performs a acas008-Delete-All`.  The answer therefore changes table
    state, so the presentation-removal rule keeps it as an explicit parameter of
    `run` rather than dropping it.  THE COBOL HAS NO DEFAULT ANSWER, and the
    appearance that it does is a trap: the prompt literal displays `[Y]`
    [irs/irs030.cbl:L1716], but the `accept` on the next line carries NO `WITH
    UPDATE` phrase [irs/irs030.cbl:L1717], so the literal never reaches the field;
    `WS-Reply pic x` [irs/irs030.cbl:L230] is never given the value `"Y"` anywhere
    in this program - the only moves into it are `space` [irs/irs030.cbl:L1512] and
    `spaces` [irs/irs030.cbl:L1521], and the `move "Z"` at [irs/irs030.cbl:L1530]
    is commented out - and L1718-L1719 send any other reply back to the prompt.
    That the missing `WITH UPDATE` is deliberate shows in this same file, which
    uses the phrase at six other accepts: [irs/irs030.cbl:L582], [:L732], [:L829],
    [:L848], [:L883] and [:L1015].  So a bare Enter RE-PROMPTS rather than
    clearing.

    THIS PARAMETER'S OWN DEFAULT OF `True` IS RETAINED DELIBERATELY, and it is a
    signature contract rather than a claim about the COBOL: this module's file
    brief fixes the signature, and every caller in the migration passes the value
    EXPLICITLY, so the default is never consulted.
    `acas_posting/cli/irs_post.py` makes the switch pair `required=True` with no
    default of its own, which is where the absence of a COBOL default is enforced -
    at the boundary an operator actually touches.

    `GO TO` CLASS 4 - PER-SITE PROOF for [irs/irs030.cbl:L1719].
    """

    if ws.clear_posting_file:

        # 1723 perform acas008-Open-Output *> performs a acas008-Delete-All THE
        # TRUNCATION. Opening this handler's file for output deletes every row of the
        # transfer table.
        facade.acas008_open_output(
            facade.FacadeContext(
                ws.ws_system_record,
                ws.ws_irs_posting_record,
                ws.file_access,
                ws.file_defs,
                ws.dal_common,
                ws.dal_options,
            ),
        )
        facade.acas008_close(
            facade.FacadeContext(
                ws.ws_system_record,
                ws.ws_irs_posting_record,
                ws.file_access,
                ws.file_defs,
                ws.dal_common,
                ws.dal_options,
            ),
        )

    # 1725 display "Note counts and any messages" at 1401 with erase eol. 1726 accept
    # WS-Reply at 1430. 1727 display space at 1401 with erase eol.


def _main99_exit() -> None:
    """`main99-exit.` - the section's exit paragraph."""
    return


def run(
    irs_system_params: IrsSystemParams,
    ws_system_record: SystemRecord,
    file_defs: FileDefs,
    *,
    clear_posting_file: bool,
    file_access: FileAccess | None = None,
    dal_common: AcasDalCommonData | None = None,
    dal_options: Mapping[str, object] | None = None,
) -> None:
    """Run `irs030`'s `Ledger-Postings-Add` section.

    calling-data block, because `irs030` does not copy `wscall.cob`, and there is NO RUN
    DATE - the posting date arrives in the data, as `WS-IRS-Post-Date`
    [irs/irs030.cbl:L1662]. A `to_day` parameter is deliberately NOT accepted.

    Args:
        irs_system_params: `IRS-System-Params`, the IRS system record
            [irs/irs030.cbl:L416]. MUTATED: the posting key allocator `next-post`
            advances once per posting written [irs/irs030.cbl:L1670-L1671], which is a
            diff-visible effect.
        ws_system_record: `WS-System-Record`, the ACAS system record
            [irs/irs030.cbl:L419]. Passed through to every handler dispatch, exactly as
            the facade copybook's own CALL list passes it.
        file_defs: `File-Defs`, the file and work-file names [irs/irs030.cbl:L450].
        clear_posting_file: the answer to the end-of-job question at
            [irs/irs030.cbl:L1717].  `True` clears the transfer table by
            reopening it for output, which for this handler deletes every row.
            Defaults to `True` as a SIGNATURE CONTRACT fixed by this module's
            file brief, NOT because the COBOL has that default - it has none. The
            `[Y]` at [irs/irs030.cbl:L1716] is prompt text, the accept at L1717
            carries no `WITH UPDATE`, and L1718-L1719 re-prompt on anything that is
            not `"Y"` or `"N"`. Every caller in the migration passes this
            explicitly, so the default is never consulted, and
            `acas_posting/cli/irs_post.py` requires the answer at the boundary an
            operator touches.
        file_access: the `File-Access` block [irs/irs030.cbl:L285].  Not a
            linkage parameter - it is this program's own WORKING-STORAGE, exposed
            because the connection details the handlers need are loaded into it by
            an out-of-scope initialisation section, so the entry point must be
            able to receive one already populated.  A fresh block is created when
            omitted.
        dal_common: the `ACAS-DAL-Common-data` block
            [copybooks/Test-Data-Flags.cob:L6], copied by this program at
            [irs/irs030.cbl:L298].  Also WORKING-STORAGE rather than linkage, and
            the fifth operand of every handler CALL.  A fresh block is created
            when omitted.
        dal_options: the caller's keyword-only handler declarations, forwarded to
            every facade `PERFORM` this section issues, and the declaration it
            exists for is the transport-security policy.  NOT a linkage operand
            and NOT working storage: the frozen bridge has no transport policy to
            declare, its connect passing six values and nothing else
            [copybooks/mysql-procedures.cpy:L72-L77].  `None` - the default -
            declares nothing, which every handler resolves FAIL-CLOSED: a Unix
            socket or a loopback address is permitted and any other target
            refused.  A run against the containerised parity harness must
            therefore say so explicitly, `dal_options={"transport":
            TransportSecurity(isolated_oracle=True)}`, and a run against a real
            server should be given `TransportSecurity(ca_file=...)`.  It changes
            no status, no statement, no arithmetic and no write order.

    Returns:
        Nothing.  The section communicates entirely through the database, through
        the `File-Access` status block and through the advanced key allocator on
        `irs_system_params`.  Every disposition - clean skip, commit-and-stop,
        abort-with-nothing, and the facade copybook's own `goback`
        [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L364] - is a normal return; the
        frozen program raises no condition and signals no failure to its caller,
        so neither does this entry point.

    THE NOMINAL LEDGER IS OPENED AND CLOSED HERE, not in the section.  The
    section runs against a file its out-of-scope `Initialise-Main` left open for
    INPUT [irs/irs030.cbl:L1481] and which `Main-Loop-Clear` closes when the
    operator leaves the menu [irs/irs030.cbl:L589]; `run` is the only place in
    the migrated surface that corresponds to that program boundary.  The
    bracketing statements and the reason the INPUT mode is correct for the
    section's four rewrites are documented at the call site below.
    """
    # The remaining records are this program's own WORKING-STORAGE, initialised as COBOL
    # initialises WORKING-STORAGE: to the layout's own default values.
    ws = _WorkingStorage(
        irs_system_params=irs_system_params,
        ws_system_record=ws_system_record,
        file_defs=file_defs,
        file_access=FileAccess() if file_access is None else file_access,
        dal_common=AcasDalCommonData() if dal_common is None else dal_common,
        ws_irsnl_record=WsIrsnlRecord(),
        ws_irs_default_record=WsIrsDefaultRecord(),
        posting_record=PostingRecord(),
        ws_irs_posting_record=WsIrsPostingRecord(),
        nl31_record=_NlSnapshot(),
        nl32_record=_NlSnapshot(),
        post_record_cnt=0,
        clear_posting_file=clear_posting_file,
        # `None` and `{}` are the same thing - no declaration - and both leave
        # every handler under the installed process policy.  Copied rather than aliased so
        # the caller's mapping cannot change under a run in progress.
        dal_options=dict(dal_options) if dal_options else {},
    )

    # --- THE PROGRAM-BOUNDARY NOMINAL-LEDGER STATE ---------------------------
    #
    # The migrated section issues NO open of the nominal ledger - it says so
    # itself, in a comment that survives in the frozen source
    # [irs/irs030.cbl:L1590]::
    #
    #     1590  *>    perform  acasirsub1-Open.      *> IT is opened in intialise-main
    #
    # and it then drives that already-open file with four `acasirsub1-Read-
    # Indexed` performs (L1596, L1606, L1629, L1647) and four
    # `acasirsub1-Rewrite` performs (L1641, L1657, L1705, L1708).  The two
    # statements that
    # bracket it are therefore part of this PROGRAM's contract even though they
    # sit outside the migrated SECTION, and the Python entry point is the only
    # place they can live: `run` IS the program boundary here, because
    # `Initialise-Main` and the menu loop that contain them are out of scope per
    # Agent Action Plan section 0.2.1.1 ("Partial - only `Ledger-Postings-Add`").
    #
    # Only the acasirsub1 OPEN/CLOSE pair is reproduced.  Nothing else from
    # `Initialise-Main` is - not the screen work, not the CoA table build, not
    # the VAT-account existence sweep, not the VAT-rate load - and none of it is
    # needed by the section, which reloads both VAT accounts itself at
    # [irs/irs030.cbl:L1594-L1612].
    #
    # THE MODE IS `INPUT`, NOT `I-O`, AND THAT IS NOT A TRANSCRIPTION SLIP.
    # `Initialise-Main` opens I-O first [irs/irs030.cbl:L1437], then closes and
    # RE-OPENS FOR INPUT so it can walk the whole file to build the description
    # search table [irs/irs030.cbl:L1480-L1481]::
    #
    #     1480      perform  acasirsub1-Close.
    #     1481      perform  acasirsub1-Open-Input.
    #
    # and it never reverts to I-O.  `Main-Loop` is entered with the file open for
    # INPUT, and option 66 performs the migrated section from there
    # [irs/irs030.cbl:L603].  So the four rewrites the section issues run
    # against a file opened for input - which succeeds, because the handler
    # tests `access-type` on START ONLY [common/acasirsub1.cbl:L525] and its
    # `aa090-Process-Rewrite` [common/acasirsub1.cbl:L627-L635] issues a bare
    # `rewrite Record-1` with no mode test at all.  Opening I-O here "because a
    # rewrite needs it" would be a fix, not a migration, and rule R-4 forbids it.
    #
    # THE CLOSE IS PER PROGRAM INVOCATION.  The frozen close is
    # [irs/irs030.cbl:L589], inside `Main-Loop-Clear`, guarded by `if w = zero`
    # - the operator pressing Return to leave the menu - and followed by `go to
    # Main-Exit`::
    #
    #      589      perform acasirsub1-Close        *> call-irsub1
    #      590      go to Main-Exit.
    #
    # One `run` call is one complete invocation of this program's posting
    # operation, so the close belongs at the end of `run`.  It is NOT in `EOJ`:
    # the frozen `EOJ` carries the close COMMENTED OUT, with the maintainer's own
    # note saying where it really happens [irs/irs030.cbl:L1710]::
    #
    #     1710  *>    perform  acasirsub1-Close.                    *> Closed at EOJ
    #
    # which is why the migrated `EOJ` issues none and this boundary does.  On the
    # `goback` path below no close happens at all, exactly as the frozen program
    # leaves it - see the note on the `except` clause.
    try:
        # 1481  perform  acasirsub1-Open-Input.
        facade.acasirsub1_open_input(
            facade.FacadeContext(
                ws.ws_system_record,
                ws.ws_irsnl_record,
                ws.file_access,
                ws.file_defs,
                ws.dal_common,
            ),
        )
        #  603  perform Ledger-Postings-Add.
        _ledger_postings_add(ws)
        #  589  perform acasirsub1-Close        *> call-irsub1
        #       Reached only when the open and the section both ran to
        #       completion, because the frozen `goback` below abandons
        #       `Main-Loop` and so never reaches L589 either.  This is why the
        #       close is in the success path and NOT in a `finally`.
        facade.acasirsub1_close(
            facade.FacadeContext(
                ws.ws_system_record,
                ws.ws_irsnl_record,
                ws.file_access,
                ws.file_defs,
                ws.dal_common,
            ),
        )
    except facade.FacadeGoback:
        # THE COPYBOOK'S `goback` DISPOSITION.
        # [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L364] is a `goback` at the
        # end of the shared `Open-Error-Continued` paragraph, and a `goback`
        # returns from the PROGRAM - so in `irs030` it ends `irs030` and hands
        # control back to the IRS menu.  Its Python counterpart is
        # `FacadeGoback`, which must therefore be absorbed HERE, at the program
        # boundary, and turned into the same normal subprogram return.  Letting
        # it escape `run` would propagate a condition the frozen program cannot
        # propagate, and would change the caller's disposition.
        #
        # Exactly three call sites in this program can raise it, being the three
        # whose facade paragraphs perform an error check
        # [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L136-L140, L175-L179,
        # L142-L146]: the `acas008-Open-Input` at the head of the section
        # [irs/irs030.cbl:L1578], the `acasirsub1-Open-Input` above, and the
        # `acas008-Open-Output` that clears the transfer file at end of job
        # [irs/irs030.cbl:L1723].  The read-indexed, rewrite, write and close
        # verbs the section uses carry no check and cannot raise.
        #
        # NO CLOSE IS ADDED ON THIS PATH, and the omission is deliberate: each
        # check paragraph performs its OWN handler close before reaching the
        # shared abort - `perform acasirsub1-Close`
        # [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L337] and `perform
        # acas008-Close` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L330] - so the
        # failing handler is already closed.  A second close here would be a
        # statement the frozen program does not execute.  The nominal ledger is
        # left as the frozen program leaves it, which after an `acas008` abort
        # means still open: `goback` skips L589, and rule R-4 keeps that.
        #
        # Recorded at debug because it is a disposition and not a diagnostic -
        # `Open-Error-Continued` has already logged FS-Reply, WE-Error, SQL-Err
        # and SQL-Msg at error level, and the `goback` itself displays nothing.
        _LOG.debug(
            "irs030: returning to caller via the goback at "
            "[copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L364]; FS-Reply=%s "
            "WE-Error=%s",
            ws.file_access.fs_reply,
            ws.file_access.we_error,
        )
        return


# --- STRUCTURAL NOTES -------------------------------------------------------
#
# S-1  THE FACADE MODULE, NOT ITS SYMBOLS.  `copy "Proc-ZZ100-ACAS-IRS-Calls.cob"`
#      [irs/irs030.cbl:L1732] is a textual inclusion of a whole paragraph set, so
#      its Python counterpart is the module, imported as a module.  Nothing is
#      imported FROM it by name, which also keeps this module's import-time
#      coupling to a single edge.
#
# S-2  THE FACADE ARGUMENT LIST.  Each verb is called with the five operands the
#      copybook's own CALL list supplies, in its order
#      [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L22-L86]:
#
#          CALL "<handler>" USING WS-System-Record <record> File-Access
#                                 File-Defs ACAS-DAL-Common-data
#
#      which is also the argument order of the handler dispatch functions, so the
#      two argument lists can be diffed against each other.  The record
#      operand differs per handler and is the one that handler owns: the transfer
#      record for `acas008`, the nominal-ledger record for `acasirsub1`, the
#      defaults record for `acasirsub3`, the internal posting record for
#      `acasirsub4`.  See AMBIGUITY Q-24.
#
# S-3  RETURN VALUES ARE IGNORED BY DESIGN.  A facade verb in the IRS convention
#      is a PERFORM of a paragraph, and a paragraph returns nothing; the reply
#      reaches the caller only through the `File-Access` block.  Every status test
#      in this module therefore reads `fs_reply` or `we_error` from that block
#      after the call, exactly as the frozen program does, and no verb's return
#      value is inspected.  That is both the faithful reading and the robust one.
#
# S-4  THE TWO GROUP MOVES.  `move WS-IRSNL-Record to nl31-record` and its three
#      siblings are group moves between identically laid-out records, which is a
#      byte-image copy.  The storage-class layer that would build those byte
#      images is outside this module's permitted imports, so the copy is realised
#      field for field through the MOVE verb, each field carrying its own
#      descriptor on both sides.  For identical layouts the two are exactly
#      equivalent: with sender and receiver descriptors equal, no truncation, no
#      padding and no class conversion can occur on any field.
#
# S-5  THE `we-error = 2` CONSTANT IS MODULE-PRIVATE, AND HAS TO BE.  The status
#      layer's error vocabulary deliberately omits the IRS handler's `1+`, `2+`
#      and `3+` codes - they are open-ended ranges local to one handler's prose
#      rather than members of the shared vocabulary, and rule R-3 forbids
#      extending that vocabulary to admit them.  The handler module that does
#      publish the pair is barred by the layering rule.  The value is therefore
#      bound once, here, to its authoritative locator
#      [common/acasirsub1.cbl:L87], and never written as a bare literal at either
#      test site.
#
# S-6  FOUR MODULE-PRIVATE DESCRIPTORS.  `Post-Record-Cnt`, `nl31-dr`, `nl31-cr`,
#      `nl32-dr` and `nl32-cr` are declared in `irs030`'s own WORKING-STORAGE, so
#      the generated data dictionary - built from the copybooks, the bridge and
#      the schema - has no entry for them.  Rule R-5 still requires provenance,
#      so each is DERIVED from the dictionary descriptor of the field it mirrors
#      byte for byte and re-labelled with its own locator inside the frozen
#      program.  Deriving rather than constructing keeps the storage class out of
#      this module entirely, which is what rule R-2 and the layering rule between
#      them require.
#
# S-7  WORKING STORAGE IS PASSED, NOT GLOBAL.  COBOL working storage is visible to
#      every paragraph, so the paragraph functions here take one explicit holder
#      rather than reading module state.  That preserves the sharing the COBOL
#      relies on while leaving the module free of mutable globals - and therefore
#      safely re-entrant - without introducing concurrency of any kind.
#
# S-8  NO PARAGRAPH BOUNDARY WAS INVENTED.  `Input-Loop` is long because the COBOL
#      paragraph is long.  It was deliberately NOT split into helper functions,
#      because every split would move a `GO TO` class annotation away from the
#      statement it transcribes and would create a function with no COBOL label
#      to trace it to.
#
# S-9  RELATION CONDITIONS.  Numeric relations go through the arithmetic layer's
#      comparator, which compares algebraically after decimal-point alignment as
#      a COBOL relation condition does.  The four alphanumeric relations - the
#      VAT-side tests - use a direct equality: both operands are of equal declared
#      width, `pic xx` against a two-character literal, so the COBOL relation
#      reduces to a byte-wise comparison in the collating sequence, and because
#      the stored side always arrives through the MOVE layer at its declared
#      width no padding asymmetry can arise.
#
#
# --- traceability -----------------------------------------------------------
#
# BOUNDARY
# ========
# `irs/irs030.cbl` is 1733 lines.  THE ONLY LINES MIGRATED HERE ARE:
#
#     L1544-L1554   Net section.                  (incl. Main-Exita.  L1553)
#     L1556-L1567   Gross section.                (incl. Main-Exitb.  L1566)
#     L1569-L1730   Ledger-Postings-Add section.  (the migrated surface)
#     L1732         copy "Proc-ZZ100-ACAS-IRS-Calls.cob".  -> an import
#
# 187 lines of 1733, PLUS EXACTLY TWO MORE STATEMENTS, named here so the count
# stays honest and the reason is not buried at the call site:
#
#     L1481         perform  acasirsub1-Open-Input.   -> at the head of `run`
#     L589          perform  acasirsub1-Close         -> at the tail of `run`
#
# 189 lines of 1733.  Those two are the nominal ledger's OPEN and CLOSE, and
# they are the section's stated precondition rather than an extension of it: the
# section drives an already-open file and says so in a surviving comment at
# L1590, then issues four read-indexed and four rewrite performs through it.
# `run` is the only place in the migrated surface that corresponds to the program
# boundary where the frozen statements sit - L1481 inside `Initialise-Main`,
# performed once at L562, and L589 inside `Main-Loop-Clear`, performed when the
# operator leaves the menu.  NOTHING ELSE from either of those out-of-scope
# paragraphs is reproduced.
#
# Everything else in the program is out of scope.  The six
# named out-of-scope sections, with their line numbers, are:
#
#     Init-Main         section  L557    program initialisation and screen setup
#     Input-Headings    section  L1239   screen headings
#     Date-Validate     section  L1285   interactive date validation
#     Initialise-Main   section  L1402   further initialisation
#     Show-Default      section  L1504   default display
#     file-init         section  L1518   file initialisation
#
# together with EVERY screen section, ACCEPT loop, amendment dialog and
# data-entry paragraph in L1-L1543 other than `Net` and `Gross`.
#
#
# PROGRAM -> MODULE, PARAGRAPH -> FUNCTION, STATEMENT -> CALL SITE
# ================================================================
# All three tables live in docs/migration/traceability.md. Locally: all NINE
# in-scope labels have a function - `_net_section`, `_net_main_exita`,
# `_gross_section`, `_gross_main_exitb`, `_ledger_postings_add`, `_input_loop`,
# `_eoj`, `_eoj_q1`, `_main99_exit` - including the two plain-`EXIT` paragraphs
# whose bodies do nothing, per R-5 and the plan's requirement that a paragraph
# keep a named function even where its `GO TO` becomes a `continue`, a `break` or
# a `return`. Two further module-private functions carry no COBOL label and are
# therefore named as statements rather than paragraphs, so that no invented
# paragraph appears above: `_move_nl_record_to_snapshot` and
# `_move_snapshot_to_nl_record`; `_index` transcribes no statement at all.
#
# The facade verbs are HANDLER-NAMED throughout - the entity-named vocabulary is
# never used, because this program copies the IRS convention. Eighteen calls
# across acas008 (open-input, read-next, close, open-output which MEANS
# delete-all, close), acasirsub3 in its bare form, acasirsub1 (four read-indexed,
# four rewrite - L1641 is A-4 and L1705/L1708 are A-5) and acasirsub4 (open,
# write, close).
#
# The in-scope arithmetic census is EIGHT distinct statements at THIRTEEN sites -
# two COMPUTEs, one SUBTRACT and ten ADDs - of which exactly TWO are ROUNDED:
# L1551 and L1562-L1563. Every other store truncates toward zero.
#

# ANOMALY REGISTER (rule R-4)                     - reproduced, never fixed
# ===========================
# Four reproductions, each annotated at its own site with its COBOL locator; the
# register text is in docs/migration/anomaly-log.md.
#   A-4   THE HALF-POSTED DOUBLE ENTRY.  L1641 the debit commits, L1652 the
#         abandon.  The debit is rewritten before the credit account is looked up
#         at L1647, so a missing credit leaves an unbalanced debit, no credit and
#         no internal posting row - the posting write is at L1673, past the
#         abandoned point.  The rewrite stays where it is, no rollback is added
#         and the credit account is not pre-validated.
#   A-5   THE LOST UPDATE ON THE TWO VAT CONTROL ACCOUNTS.  L1602 and L1612 take
#         the snapshots, L1704-L1705 and L1707-L1708 rewrite from them, and the
#         ladder at L1685-L1699 accumulates into the snapshots rather than the
#         live rows - so any in-loop rewrite of account 31 or 32 is silently
#         discarded at end of job.  The accounts are not re-read, the snapshots
#         are not merged and the collision is not detected.
#   A-19  SUPERSEDED COMMENTED-OUT VARIANTS OF BOTH VAT COMPUTES, at L1550 and
#         L1561, referencing a differently named rate field `vat` where the live
#         statements reference `WS-Vat-Current`.  Both dead lines are carried
#         verbatim as comments beside their live translations, with the
#         maintainer's uncertainty note at L1547-L1548.  Carrying them IS the
#         reproduction.
#   THE WRITE-FAILURE JUMP at L1674-L1678 transfers to `EOJ`, not to
#         `Input-Loop`, and `EOJ` still performs both snapshot rewrites and all
#         three closes, so the partial state is COMMITTED.  No rollback, no
#         retry, and none of the end-of-job work is skipped.
# Owned ELSEWHERE but touching this section: A-6, the transfer-file handler's
# four unconditionally rejected verbs - this section calls none of them, which is
# why it works - and A-7, the internal posting bridge's three derived
# date-component columns, whose only input from here is the date move at L1662.
#
#

# FINDING LIST                       - recorded, not acted on
# ============
# Candidate register additions scoped to this program. They are named
# `F-IRS030-<n>` rather than bare `F-<n>`, because a bare number allocated inside
# one module collides with the identifiers other registers allocate - the rule
# docs/migration/anomaly-log.md section 15.1 states after exactly that collision
# happened between two other modules. Nothing outside this file cites them.
#   F-IRS030-1  L1579-L1581 IS UNREACHABLE-WHEN-TRUE.  `acas008-Open-Input` already
#        performs `acas008-Check-4-Errors`, whose predicate is identical
#        [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L136-L140]; on failure that
#        check hard-returns out of the program, so control never arrives at
#        L1579, and on success FS-Reply is zero.  Kept regardless, because rule
#        R-3 forbids removing a predicate the compiled program contains.
#   F-IRS030-2  THERE IS NO `acasirsub4-Check-4-Errors`.  The copybook declares five
#        error-check paragraphs for six dispatched handlers.  That absence is why
#        L1674 must test inline, and why the failed open at L1617 is silently
#        ignored.
#   F-IRS030-3  `acasirsub1-Rewrite` has neither a facade check nor an inline test at
#        any of its four sites, so a failed rewrite is silently ignored.  This
#        compounds A-4.
#   F-IRS030-4  A MIXED STATUS PROTOCOL.  Two sites read FS-Reply, five read we-error.
#        Never unified.
#   F-IRS030-5  THE `we-error = 2` PREDICATE IS AN EQUALITY, not "not = zero", so any
#        other non-zero error falls through into the accumulate.  Not widened.
#   F-IRS030-6  THE VAT SIDE IS APPLIED INVERTED.  L1636-L1637 adds VAT to the DEBIT
#        accumulator when the side is "CR"; L1654-L1655 adds it to the CREDIT
#        accumulator when the side is "DR".  Not corrected.
#   F-IRS030-7  THE LADDER HAS NO FINAL `else`.  A VAT account that is non-zero but
#        neither 31 nor 32 accumulates nowhere and nothing is reported.  No
#        `else` and no diagnostic added.
#   F-IRS030-8  `next-post` IS INCREMENTED BEFORE THE WRITE (L1671 before L1673), so the
#        allocator advances even when the write fails.  Ordering preserved.
#   F-IRS030-9  FIELD-NAME CASE INCONSISTENCY.  The VAT side is spelled
#        `ws-irs-post-vat-side` (L1636), `WS-irs-post-vat-side` (L1654) and
#        `WS-IRS-Post-Vat-Side` (L1686).  COBOL is case-insensitive; recorded, not
#        propagated.
#   F-IRS030-10 `EOJ-q1.` IS WRITTEN AT COLUMN 1 (L1715), unlike every other label in
#        the section, which are indented one column.  A formatting oddity only.
#   F-IRS030-11 `Main-Exita.` AND `Main-Exitb.` ARE PLAIN `EXIT`s, not `EXIT SECTION`,
#        and their `a`/`b` suffixes make them distinct labels - unlike the
#        repeated `main-exit` of the Sales and Purchase programs.  Both retain a
#        named function anyway.
#   F-IRS030-12 THE SNAPSHOT DECLARATIONS DIVERGE FROM THE COPYBOOK in two ways:
#        `nl31-type`/`nl31-ac` are `pic a` where the copybook has `pic x`, and
#        the snapshots carry no `filler redefines NL-Data` and therefore no
#        `NL-Pointer`.  Byte widths are identical, so the group move is still an
#        exact byte copy.  See `_NlSnapshot` and STRUCTURAL NOTE S-4.
#   F-IRS030-13 THE MAINTAINER'S OWN UNCERTAINTY NOTE at L1547-L1548 asks whether the
#        VAT compute needs a non-zero-rate test.  Recorded; no test added.
#   F-IRS030-14 THE CREDIT AND DEBIT MOVES AT L1663-L1664 ARE IN THE OPPOSITE ORDER to
#        the two legs that were posted at L1627-L1657.  Transcribed in source
#        order; harmless, but a reader diffing will notice.
#   F-IRS030-15 THE TRANSFER FILE IS CLOSED AT L1712 AND REOPENED AT L1723 purely so
#        that opening it for output can truncate it, then closed again at L1724.
#        Both calls reproduced, in order.
#   F-IRS030-16 THREE DISTINCT REJECTION DISPOSITIONS coexist in this one section and
#        leave three different database states: CLEAN SKIP (L1634 - nothing
#        written), COMMIT-AND-STOP (L1678 - partial state committed, end-of-job
#        work still performed) and ABORT-WITH-NOTHING (L1581/L1601/L1611 - no
#        rewrite, no close, no truncation).  Implemented separately; a single
#        generic rejection path would not reproduce them.
#   F-IRS030-17 REPEATED WORK LEFT UNOPTIMISED.  The two VAT accounts are fetched by two
#        separate indexed reads with the sub-nominal zeroing written out twice,
#        and `nl-sub-nominal` is re-zeroed before all four lookups.  An optimiser
#        would collapse these; performance work is out of scope by construction.
#   F-IRS030-18 THE FOUR REWRITES RUN THROUGH A FILE OPENED FOR *INPUT*, and the
#        handler lets them.  `Initialise-Main` opens the nominal ledger I-O at
#        L1437, then closes it at L1480 and RE-OPENS IT FOR INPUT at L1481 so it
#        can walk the whole file, and never reverts; `Main-Loop` and therefore
#        this section run from that INPUT state.  It works because
#        `common/acasirsub1.cbl` tests `access-type` on START ONLY
#        [common/acasirsub1.cbl:L525] and `aa090-Process-Rewrite`
#        [common/acasirsub1.cbl:L627-L635] issues a bare `rewrite Record-1` with
#        no mode test whatsoever.  Reproduced as measured: `run` opens INPUT.
#        Opening I-O instead "because a rewrite needs it" would be a fix, and
#        rule R-4 forbids fixes.  Compounds F-IRS030-3, which records that a failed
#        rewrite is never tested for at any of its sites.
#
#
# CITATION CORRECTIONS
# ====================
#   C-1  THE UN-ROUNDED SUBTRACT IS AT L1564, NOT L1565.  The migration plan's
#        arithmetic census cites `subtract vat-amount from post-amount` at L1565;
#        measured against the frozen source it is at L1564, and L1565 is a
#        comment line.
#   C-2  THE SECTION ENDS AT L1730, NOT L1733.  The plan gives the boundary as
#        L1569-L1733.  L1730 is `exit section.`, the last executable line; L1731
#        is a comment, L1732 is the facade `COPY` and L1733 is a comment.
#        L1569-L1730 is the code boundary used throughout this module.
#   C-3  `PERFORM ... THRU` IS OUT OF SCOPE HERE.  The plan counts three such
#        sites in `irs030`, at L813, L831 and L832.  All three lie in
#        interactive code outside this module's stated boundary, so the in-scope
#        region contains ZERO `PERFORM ... THRU` and none is transformed.
#   C-4  THE FIFTH IN-SCOPE `COMPUTE` IS OUT OF SCOPE HERE.  The arithmetic
#        layer's own documentation counts `compute u-bin = u-year * 365` at L1362
#        among the cycle's live COMPUTE statements.  It sits in the out-of-scope
#        `Date-Validate` region and is not reproduced by this module.
#   C-5  THE PLAN'S "FIVE ROUNDED SITES" ARE FOUR ROUNDED COMPUTES PLUS ONE
#        ROUNDED DIVIDE.  Two of the four computes are this module's, at L1551 and
#        L1562-L1563; the other two belong to the batch control-total gate and the
#        fifth site is a divide in the end-of-cycle program.  Stated so that
#        "five ROUNDED COMPUTEs" is not inferred.
#
#
# OMISSIONS               - deliberate, so that nothing looks lost by accident
# =========
#   O-1  THE SIX OUT-OF-SCOPE SECTIONS, BY NAME AND LINE, plus every screen
#        section and ACCEPT loop in L1-L1543 other than `Net` and `Gross`.  See
#        BOUNDARY above for the list.  This is the largest omission in this
#        module and the one most likely to be mistaken for a gap: 1544 of the
#        program's 1733 lines are simply not part of this migration.
#        THE TWO EXCEPTIONS ARE NAMED IN BOUNDARY ABOVE and are the only
#        statements taken from outside the three in-scope sections: the
#        `acasirsub1-Open-Input` at L1481 and the `acasirsub1-Close` at L589.
#        `Initialise-Main`'s screen work, its CoA search-table build, its
#        VAT-account existence sweep, its VAT-rate load and its I-O open at L1437
#        are all still omitted, and none is needed - the section reloads both VAT
#        accounts itself at L1594-L1612.
#   O-2  FURTHER CONSTRUCTS EXCLUDED BY NAME, all outside the boundary and
#        therefore NOT reproduced: the eight sign flips at L947, L963, L1096,
#        L1125, L1127, L1139, L1141 and L1179; the amount scaling at L1074, L1077
#        and L1083; the leap-year divide-then-multiply at L1333-L1334; the
#        day-count computation at L1362; and the three `PERFORM ... THRU` sites
#        at L813, L831 and L832.
#        CONSEQUENCE, stated explicitly so no reader goes hunting: THIS MODULE
#        HAS ZERO IN-SCOPE SIGN FLIPS, ZERO `PERFORM ... THRU`, ZERO PERIOD-TOTAL
#        WRITES and ZERO IRS FAN-OUT TESTS.
#   O-3  `display ... at` STATEMENTS BECOME LOG RECORDS.  They must not alter
#        control flow and must not appear in any table dump, and none does:
#        L1580, L1598-L1599, L1608-L1609, L1616, L1631-L1632, L1649-L1650,
#        L1675-L1676 and L1714.  Two carry no content at all and are dropped
#        rather than logged: L1713 and L1727, both bare screen erases.  L1725 is
#        dropped with its accept - see O-4.
#   O-4  `accept WS-Reply` ACKNOWLEDGEMENT PAUSES ARE DROPPED: L1600, L1610,
#        L1633, L1651, L1677 and L1726.  Their only effect is to block a
#        terminal.  BUT EVERY CONTROL TRANSFER THAT FOLLOWS ONE IS PRESERVED -
#        L1601, L1611, L1634, L1652 and L1678 - because only the pause is
#        presentation; the transfer is behaviour.
#   O-5  `accept WS-Reply` AT L1717 IS NOT DROPPED.  It gates a database write -
#        the transfer-table truncation - so it becomes the explicit
#        `clear_posting_file` parameter of `run`.  IT HAS NO DEFAULT, AND THAT IS
#        DELIBERATE: it is keyword-only and required, so this module cannot be
#        called without an answer.  The file brief gives it a `True` default and the
#        module does not follow the brief here, because there is no COBOL default to
#        reproduce -- the `[Y]` at L1716 is prompt text, the accept at L1717 carries
#        no `WITH UPDATE`, `WS-Reply` is never set to `"Y"` anywhere in the program,
#        and L1718-L1719 re-prompt on anything else, so a bare Enter re-prompts
#        rather than clearing.  A `True` default would have been this migration
#        inventing the DESTRUCTIVE answer, which rule R-3 forbids
#        as much as rule R-4 forbids dropping a real one.
#        acas_posting/cli/irs_post.py likewise requires the answer at its boundary.
#   O-6  `copy "screenio.cpy"` (L344) and `copy "envdiv.cob"` (L197) map to
#        nothing.  Both are representation only: a screen-section vocabulary and
#        an environment division fragment, neither of which has a Python
#        counterpart.  Note the first is spelled `.cpy`, not `.cob`.
#   O-7  THE MESSAGE IDENTIFIERS `IR031`, `IR032`, `IR033`, `IR03A`, `IR03B` and
#        `IR914` ARE RETAINED ONLY AS LOG TEXT, verbatim.  `IR916` and `SY008` are
#        the facade's own and belong to it, not here.
#   O-8  `Post-Record-Cnt` IS MAINTAINED BUT REACHES NO TABLE.  It exists solely
#        to feed the completion message at L1714, and is kept because that log
#        line consumes it.
#   O-9  `WS-Reply` ITSELF IS NOT MODELLED.  Every one of its uses is either a
#        dropped pause or the parameter of O-5.
#   O-10 ABSENCES WORTH STATING POSITIVELY, because a reader familiar with the
#        sibling modules will look for them and find nothing:
#          - NO `call "..."` OF ANY KIND in the in-scope region.  No operating
#            system spool-out, no date-module call, no library routine.  This
#            module therefore needs no runtime escape hatch at all.
#          - NO print file and no report formatting whatsoever.
#          - NO work file.  The General Ledger phases hand data through two
#            scratch files; this section hands on nothing.
#          - NO date conversion.  `irs030` does not copy the date-conversion
#            interface copybook, and the posting date is carried through
#            unconverted at L1662.
#          - NO clock read and NO date parameter.  See the module docstring.
#          - NO facade stub block.  One General Ledger program declares unused
#            facade stubs to satisfy the linker; `irs030` declares none.
#          - NO period-total write.  All nine in the migration belong to the
#            Sales and Purchase programs.
#          - NO IRS fan-out test.  This IS the IRS side of the fan-out.
#          - NO 88-level condition-name test.  Every relation in the region is a
#            direct comparison, which is why the condition-name layer is not
#            imported.
#          - NO anomaly A-22.  The wrapper-section naming inconsistency that
#            anomaly records belongs to a General Ledger program.
#
# --- end traceability -------------------------------------------------------
