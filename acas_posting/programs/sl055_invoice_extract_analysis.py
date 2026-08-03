"""`sl055` - Sales invoice post extract and analysis-total build [sales/sl055.cbl].

The whole program: it walks the invoice file, extracts the postings the Sales
posting run needs and builds the analysis totals.

Credit notes are carried by flipping signs rather than by a separate path
[sales/sl055.cbl:L446], [sales/sl055.cbl:L457], [sales/sl055.cbl:L463], and the
credit-note branch negates nine fields in one block
[sales/sl055.cbl:L658-L666]. Every flip is reproduced field by field; folding
them into one helper would lose the field set the COBOL actually negates.

Two of the cycle's nine period-total writes are here - sales invoices
[sales/sl055.cbl:L675] and sales credit notes [sales/sl055.cbl:L677]. Those nine
sites are the only writers of the totals record, which is what makes the
period-end totals observable in one table.

THE FIRST SALES/PURCHASE MODULE, AND IT IS NOT A GENERAL LEDGER MODULE
"""

from __future__ import annotations

import enum
import logging
from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from types import MappingProxyType
from typing import Final, Protocol

# copy "wsfnctn.cob". [sales/sl055.cbl:L155] `01 File-Access.`
# [copybooks/wsfnctn.cob:L22] - `We-Error`, `Rrn`, `Fs-Reply`, `FS-Action`, the
# `Logging-Data` block that carries `File-Key-No` [copybooks/wsfnctn.cob:L46] and the
# `RDB-Data` connection block.
from acas_posting.records.file_access import FileAccess, LoggingData

from acas_posting.records.value_analysis import VaCode, VaGroup, WsValueRecord

from acas_posting.records.analysis import PaGroup, WsAnalysisRecord, WsPaCode

# copy "slwsinv2.cob". [sales/sl055.cbl:L158] The invoice record and its two REDEFINES
# views - `01 Invoice-Record.` [copybooks/slwsinv2.cob:L27], `01 Invoice-Header
# redefines Invoice-Record.` [copybooks/slwsinv2.cob:L38] and `01 Invoice-Line redefines
# Invoice-Record.` [copybooks/slwsinv2.cob:L91].
from acas_posting.records.sales_invoice import (
    IhInvoiceHeader,
    IhFig,
    IhPrime,
    IhSubPrime,
    IlInvoiceLine,
    InvoiceKey,
)
from acas_posting.records.sales_invoice import descriptor_for as _invoice_descriptor

from acas_posting.records.test_data_flags import AcasDalCommonData

from acas_posting.records.file_defs import FileDefs

# copy "wscall.cob". [sales/sl055.cbl:L267] `01 WS-Calling-Data`
# [copybooks/wscall.cob:L6-L14] - the first linkage parameter. `WS-Caller` is read three
# times, at [sales/sl055.cbl:L341], [sales/sl055.cbl:L505] and [sales/sl055.cbl:L514].
from acas_posting.records.calling_data import WsCallingData
from acas_posting.records.calling_data import descriptor_for as _calling_descriptor

from acas_posting.records.system_record import (
    RdbmsFlatStatuses,
    SystemDataBlock,
    SystemRecord,
)

from acas_posting.records.system_record_4 import SalesLedgerData, SystemRecord4

# copy "slwsoi.cob". [sales/sl055.cbl:L145] `01 OI-Header.` [copybooks/slwsoi.cob:L8] -
# the 118-byte OTM2 record this program builds and writes.
from acas_posting.records.otm3 import Filler1, Filler2, OiBatch, OiCustomer, OiHeader, OiKey
from acas_posting.records.otm3 import descriptor_for as _otm2_descriptor

# The COBOL-language semantics layer. Every arithmetic statement, every `MOVE`, every
# `88`-level test and every reference modification in this program routes through one of
# these four modules.
from acas_posting.cobol import arithmetic, condition_names, move, picture
from acas_posting.cobol.field import FieldDescriptor

from acas_posting.dal.status import AccessType, FsReply


from acas_posting import dates
from acas_posting.workfiles import (
    OPEN_ITEM_2_NAME,
    OpenItemWorkFile,
    open_item_work_file,
)

# `select open-item-file-2 assign file-18 access sequential status fs-reply.`
# [copybooks/seloi2.cob:L2-L4] is copied by BOTH this program and `sl060`
# [sales/sl060.cbl:L178], because both open the same transient extract file - this
# one to append headers, `sl060` to walk them. Section 0.4.3 forbids one
# `programs/` module from importing another, and section 0.3.1 assigns this
# species of file - "ordered in-process sequences", reaching no schema table - to
# `acas_posting.workfiles`, which both ends ARE permitted to import. Both ends
# therefore take the SAME carrier type from there - `OpenItemWorkFile`, keyed by
# the name `file-18` assigns - and the CALLER hands one instance to both, which
# is what makes the handoff a handoff: `cli/sl_invoice_post` creates it once per
# route invocation, because the file outlives the first `CALL` and is read by the
# second. See `open_item_file_2` in `run`.

#: The whole public surface: this program's single entry point, mirroring its `PROCEDURE
#: DIVISION USING` list [sales/sl055.cbl:L271-L275]. Agent Action Plan section 0.3.3,
#: verbatim.
__all__: Final[tuple[str, ...]] = ("run",)

#: Every `display` in this program is a diagnostic with no database effect, and section
#: 0.3.4 makes such a display "a log record at a severity matching the original's
#: intent" that "must not alter control flow and must not appear in any table dump".
_LOG: Final[logging.Logger] = logging.getLogger(__name__)


_D_WS_P_FLAG: Final[FieldDescriptor] = picture.descriptor_for(
    "pic 9 value zero", name="ws-p-flag", source_locator="sales/sl055.cbl:L200"
)
_D_WS_ANAL_FLAG: Final[FieldDescriptor] = picture.descriptor_for(
    "pic 9 value zero", name="ws-Anal-Flag", source_locator="sales/sl055.cbl:L201"
)
_D_SAVE_CODE: Final[FieldDescriptor] = picture.descriptor_for(
    "pic xxx", name="save-code", source_locator="sales/sl055.cbl:L202"
)
_D_V_EXISTS: Final[FieldDescriptor] = picture.descriptor_for(
    "pic 9", name="v-exists", source_locator="sales/sl055.cbl:L203"
)
_D_WS_INV_AMT: Final[FieldDescriptor] = picture.descriptor_for(
    "pic s9(7)v99 comp-3 value zero",
    name="ws-inv-amt",
    source_locator="sales/sl055.cbl:L204",
)
_D_WORK_2: Final[FieldDescriptor] = picture.descriptor_for(
    "pic s9(7)v99 comp-3 value zero", name="work-2", source_locator="sales/sl055.cbl:L205"
)
_D_WS_VAT_TOTALV: Final[FieldDescriptor] = picture.descriptor_for(
    "pic s9(7)v99 comp-3 value zero",
    name="ws-vat-totalv",
    source_locator="sales/sl055.cbl:L206",
)
_D_WS_VATR_TOTALV: Final[FieldDescriptor] = picture.descriptor_for(
    "pic s9(7)v99 comp-3 value zero",
    name="ws-vatr-totalv",
    source_locator="sales/sl055.cbl:L207",
)
_D_WS_CARR_TOTALV: Final[FieldDescriptor] = picture.descriptor_for(
    "pic s9(7)v99 comp-3 value zero",
    name="ws-carr-totalv",
    source_locator="sales/sl055.cbl:L208",
)
_D_WS_DISC_TOTALV: Final[FieldDescriptor] = picture.descriptor_for(
    "pic s9(7)v99 comp-3 value zero",
    name="ws-disc-totalv",
    source_locator="sales/sl055.cbl:L209",
)
_D_WORK_3: Final[FieldDescriptor] = picture.descriptor_for(
    "pic s9(5) comp value zero", name="work-3", source_locator="sales/sl055.cbl:L210"
)
_D_WS_VAT_TOTALT: Final[FieldDescriptor] = picture.descriptor_for(
    "pic s9(5) comp value zero", name="ws-vat-totalt", source_locator="sales/sl055.cbl:L211"
)
_D_WS_VATR_TOTALT: Final[FieldDescriptor] = picture.descriptor_for(
    "pic s9(5) comp value zero", name="ws-vatr-totalt", source_locator="sales/sl055.cbl:L212"
)
_D_WS_CARR_TOTALT: Final[FieldDescriptor] = picture.descriptor_for(
    "pic s9(5) comp value zero", name="ws-carr-totalt", source_locator="sales/sl055.cbl:L213"
)
_D_WS_DISC_TOTALT: Final[FieldDescriptor] = picture.descriptor_for(
    "pic s9(5) comp value zero", name="ws-disc-totalt", source_locator="sales/sl055.cbl:L214"
)

_D_EXCEPTION_MSG: Final[FieldDescriptor] = picture.descriptor_for(
    "pic x(25) value spaces", name="Exception-Msg", source_locator="sales/sl055.cbl:L153"
)

#  THE MESSAGE LITERALS  [sales/sl055.cbl:L247-L257]
#
# `01 Error-Messages.` Presentation only: each becomes the text of a log record
# and never reaches a column. `SL124` is DECLARED [sales/sl055.cbl:L255] and
# never referenced anywhere in the program - recorded in the OMISSIONS list
# rather than dropped silently.
#
# `SL002` IS DECLARED HERE AND DELIBERATELY NEVER REFERENCED. The frozen program
# displays it at [sales/sl055.cbl:L340, L506, L515, L687], always immediately
# before an `accept ws-reply`, and the literal itself - "Note error and hit
# return" - is nothing but the instruction to press that key. Section 0.3.4 drops
# such a prompt entirely, so no log record carries it. The DECLARATION stays
# because rule R-5 maps the whole `01 Error-Messages` group, and dropping the
# member would make the group look shorter than the frozen source's.
_SL002: Final[str] = "SL002 Note error and hit return"
_SL121: Final[str] = "SL121 Error writing to Open Item 2 File "
_SL122: Final[str] = "SL122 Unprinted Invoices Exist. Correct & Run Again"
_SL123: Final[str] = "SL123 Analyst records with desc, 'Emergency Name' created"
_SL125: Final[str] = "SL125 Analysis File Does Not Exist"
_SL126: Final[str] = "SL126 You will need to update this"

_PROG_NAME: Final[str] = "SL055 (3.3.00)"

_TITLE: Final[str] = "Invoice Post Extract"

#: `"Emergency Name - Missing"` [sales/sl055.cbl:L578] - the description `db010-Create-
#: Anal` writes into the analysis record it invents.
_EMERGENCY_NAME: Final[str] = "Emergency Name - Missing"

_TERM_CODE_ANALYSIS_FILE_MISSING: Final[int] = 8

#: `if WS-Caller not = "xl150"` [sales/sl055.cbl:L341], [sales/sl055.cbl:L505],
#: [sales/sl055.cbl:L514] - the codebase's OWN unattended-mode check. `xl150` is the
#: end-of-cycle driver, out of scope per section 0.2.2.
_XL150: Final[str] = move.move_alphanumeric("xl150", _calling_descriptor("ws_caller"))


# `select open-item-file-2 assign file-18 access sequential status fs-reply.`
# [copybooks/seloi2.cob] - the OTM2 file's FILE STATUS field IS `Fs-Reply`
# [copybooks/wsfnctn.cob:L25], the very field the data-access layer uses. One
# field, two producers. So `open extend` [sales/sl055.cbl:L359] and
# `write oi-header` [sales/sl055.cbl:L681] write the same `Fs-Reply` that
# `Invoice-Read-Next` does, and this program's two tests of it -
# [sales/sl055.cbl:L360] and [sales/sl055.cbl:L682] - are both `not = zero`,
# which is why the exact non-zero value never changes a decision here.
#
# The RAW COBOL FILE STATUSES this file reports are deliberately NOT `FsReply`
# members: `Fs-Reply pic 99` holds whatever the file system returns, and the six
# `FsReply` values are the data-access layer's own vocabulary. They are declared
# ONCE, beside the carrier that reports them, as
# `acas_posting.workfiles.FS_REPLY_OPEN_NOT_FOUND` (35, the status that makes the
# fallback at [sales/sl055.cbl:L360-L362] the normal first-run path, since
# `copybooks/seloi2.cob` declares no `OPTIONAL`) and `FS_REPLY_WRITE_NOT_OPEN`
# (48). This program only ever tests them as `not = zero`
# [sales/sl055.cbl:L360], [sales/sl055.cbl:L682], so the exact non-zero value
# never changes a decision here.


def _field_of(fields: tuple[FieldDescriptor, ...], cobol_name: str) -> FieldDescriptor:
    """Pick one published descriptor out of a record class's `FIELDS` tuple.

    `records.value_analysis`, `records.analysis` and `records.system_record_4` publish
    their field metadata as a `FIELDS` class variable rather than through an accessor
    function, so this is the accessor. It looks the descriptor UP.

    Args:
        fields: A record class's published `FIELDS` tuple.
        cobol_name: The field's COBOL name, in any case.

    Returns:
        The matching descriptor, with its dictionary key and locator intact.

    Raises:
        KeyError: No field of that name is published. A PROGRAMMER error: it can only
            fire on a name retyped wrongly here, never on record content.
    """
    wanted = cobol_name.casefold()
    for descriptor in fields:
        if descriptor.name.casefold() == wanted:
            return descriptor
    raise KeyError(f"no published field named {cobol_name!r} in this record")


# `01 WS-Value-Record.` [copybooks/wsval.cob:L9] NOTE THE SIGNEDNESS SPLIT, which is
# load-bearing for the accumulations below.
_D_VA_CODE: Final[FieldDescriptor] = _field_of(WsValueRecord.FIELDS, "va-code")
_D_VA_SYSTEM: Final[FieldDescriptor] = _field_of(VaCode.FIELDS, "va-system")
_D_VA_GROUP: Final[FieldDescriptor] = _field_of(VaCode.FIELDS, "va-group")
_D_VA_FIRST: Final[FieldDescriptor] = _field_of(VaGroup.FIELDS, "va-first")
_D_VA_SECOND: Final[FieldDescriptor] = _field_of(VaGroup.FIELDS, "va-second")
_D_VA_GL: Final[FieldDescriptor] = _field_of(WsValueRecord.FIELDS, "va-gl")
_D_VA_DESC: Final[FieldDescriptor] = _field_of(WsValueRecord.FIELDS, "va-desc")
_D_VA_PRINT: Final[FieldDescriptor] = _field_of(WsValueRecord.FIELDS, "va-print")
_D_VA_T_THIS: Final[FieldDescriptor] = _field_of(WsValueRecord.FIELDS, "va-t-this")
_D_VA_T_LAST: Final[FieldDescriptor] = _field_of(WsValueRecord.FIELDS, "va-t-last")
_D_VA_T_YEAR: Final[FieldDescriptor] = _field_of(WsValueRecord.FIELDS, "va-t-year")
_D_VA_V_THIS: Final[FieldDescriptor] = _field_of(WsValueRecord.FIELDS, "va-v-this")
_D_VA_V_LAST: Final[FieldDescriptor] = _field_of(WsValueRecord.FIELDS, "va-v-last")
_D_VA_V_YEAR: Final[FieldDescriptor] = _field_of(WsValueRecord.FIELDS, "va-v-year")

#: The six fields `move zero to VA-T-This va-t-last VA-T-Year VA-V-This va-v-last VA-V-
#: Year` [sales/sl055.cbl:L539-L540] names, IN THE ORDER IT NAMES THEM.
_VALUE_TOTALS_CLEARED_BY_DB000: Final[tuple[FieldDescriptor, ...]] = (
    _D_VA_T_THIS,
    _D_VA_T_LAST,
    _D_VA_T_YEAR,
    _D_VA_V_THIS,
    _D_VA_V_LAST,
    _D_VA_V_YEAR,
)

_D_WS_PA_CODE: Final[FieldDescriptor] = _field_of(WsAnalysisRecord.FIELDS, "WS-Pa-Code")
_D_PA_SYSTEM: Final[FieldDescriptor] = _field_of(WsPaCode.FIELDS, "Pa-System")
_D_PA_GROUP: Final[FieldDescriptor] = _field_of(WsPaCode.FIELDS, "Pa-Group")
_D_PA_FIRST: Final[FieldDescriptor] = _field_of(PaGroup.FIELDS, "Pa-First")
_D_PA_SECOND: Final[FieldDescriptor] = _field_of(PaGroup.FIELDS, "Pa-Second")
_D_PA_GL: Final[FieldDescriptor] = _field_of(WsAnalysisRecord.FIELDS, "Pa-Gl")
_D_PA_DESC: Final[FieldDescriptor] = _field_of(WsAnalysisRecord.FIELDS, "Pa-Desc")
_D_PA_PRINT: Final[FieldDescriptor] = _field_of(WsAnalysisRecord.FIELDS, "Pa-Print")

_D_SL_INVOICES_THIS_MONTH: Final[FieldDescriptor] = _field_of(
    SalesLedgerData.FIELDS, "sl-invoices-this-month"
)
_D_SL_CREDIT_NOTES_THIS_MONTH: Final[FieldDescriptor] = _field_of(
    SalesLedgerData.FIELDS, "sl-credit-notes-this-month"
)

_D_INVOICE_NOS: Final[FieldDescriptor] = _invoice_descriptor(InvoiceKey, "invoice_nos")
_D_ITEM_NOS: Final[FieldDescriptor] = _invoice_descriptor(InvoiceKey, "item_nos")

_D_IH_TEST: Final[FieldDescriptor] = _invoice_descriptor(IhPrime, "ih_test")
_D_IH_INVOICE: Final[FieldDescriptor] = _invoice_descriptor(IhPrime, "ih_invoice")
_D_IH_CUSTOMER: Final[FieldDescriptor] = _invoice_descriptor(IhPrime, "ih_customer")
_D_IH_DATE: Final[FieldDescriptor] = _invoice_descriptor(IhPrime, "ih_date")
_D_IH_ORDER: Final[FieldDescriptor] = _invoice_descriptor(IhPrime, "ih_order")
_D_IH_TYPE: Final[FieldDescriptor] = _invoice_descriptor(IhPrime, "ih_type")

_D_IH_P_C: Final[FieldDescriptor] = _invoice_descriptor(IhFig, "ih_p_c")
_D_IH_NET: Final[FieldDescriptor] = _invoice_descriptor(IhFig, "ih_net")
_D_IH_EXTRA: Final[FieldDescriptor] = _invoice_descriptor(IhFig, "ih_extra")
_D_IH_CARRIAGE: Final[FieldDescriptor] = _invoice_descriptor(IhFig, "ih_carriage")
_D_IH_VAT: Final[FieldDescriptor] = _invoice_descriptor(IhFig, "ih_vat")
_D_IH_DISCOUNT: Final[FieldDescriptor] = _invoice_descriptor(IhFig, "ih_discount")
_D_IH_E_VAT: Final[FieldDescriptor] = _invoice_descriptor(IhFig, "ih_e_vat")
_D_IH_C_VAT: Final[FieldDescriptor] = _invoice_descriptor(IhFig, "ih_c_vat")

_D_IH_STATUS: Final[FieldDescriptor] = _invoice_descriptor(IhSubPrime, "ih_status")
_D_IH_STATUS_A: Final[FieldDescriptor] = _invoice_descriptor(IhSubPrime, "ih_status_a")
_D_IH_STATUS_L: Final[FieldDescriptor] = _invoice_descriptor(IhSubPrime, "ih_status_l")
_D_IH_DEDUCT_DAYS: Final[FieldDescriptor] = _invoice_descriptor(IhSubPrime, "ih_deduct_days")
_D_IH_CR: Final[FieldDescriptor] = _invoice_descriptor(IhSubPrime, "ih_cr")
_D_IH_UPDATE: Final[FieldDescriptor] = _invoice_descriptor(IhSubPrime, "ih_update")

#: `ih-deduct-amt pic 999v99 comp` [copybooks/slwsinv2.cob:L82] and `ih-deduct-vat pic
#: 999v99 comp` [copybooks/slwsinv2.cob:L83] are UNSIGNED, whereas their OTM2 receivers
#: `OI-Deduct-Amt`/`OI-Deduct-Vat pic s999v99 comp` [copybooks/slwsoi.cob:L51-L52] are
#: SIGNED.
_D_IH_DEDUCT_AMT: Final[FieldDescriptor] = _invoice_descriptor(IhSubPrime, "ih_deduct_amt")
_D_IH_DEDUCT_VAT: Final[FieldDescriptor] = _invoice_descriptor(IhSubPrime, "ih_deduct_vat")

_D_IL_PRODUCT: Final[FieldDescriptor] = _invoice_descriptor(IlInvoiceLine, "il_product")
_D_IL_PA: Final[FieldDescriptor] = _invoice_descriptor(IlInvoiceLine, "il_pa")
_D_IL_TYPE: Final[FieldDescriptor] = _invoice_descriptor(IlInvoiceLine, "il_type")
_D_IL_NET: Final[FieldDescriptor] = _invoice_descriptor(IlInvoiceLine, "il_net")
_D_IL_UPDATE: Final[FieldDescriptor] = _invoice_descriptor(IlInvoiceLine, "il_update")

# `01 OI-Header.` - THE OTM2 RECORD [copybooks/slwsoi.cob:L8] All twenty-eight leaves,
# because `initialize oi-header with filler.` [sales/sl055.cbl:L635] touches every one
# of them.
_D_OI_NOS: Final[FieldDescriptor] = _otm2_descriptor(OiCustomer, "oi_nos")
_D_OI_CHECK: Final[FieldDescriptor] = _otm2_descriptor(OiCustomer, "oi_check")
_D_OI_INVOICE: Final[FieldDescriptor] = _otm2_descriptor(OiKey, "oi_invoice")
_D_OI_CUSTOMER: Final[FieldDescriptor] = _otm2_descriptor(OiKey, "oi_customer")
_D_OI_DATE: Final[FieldDescriptor] = _otm2_descriptor(Filler1, "oi_date")
_D_OI_B_NOS: Final[FieldDescriptor] = _otm2_descriptor(OiBatch, "oi_b_nos")
_D_OI_B_ITEM: Final[FieldDescriptor] = _otm2_descriptor(OiBatch, "oi_b_item")
_D_OI_TYPE: Final[FieldDescriptor] = _otm2_descriptor(Filler1, "oi_type")
_D_OI_DESCRIPTION: Final[FieldDescriptor] = _otm2_descriptor(Filler1, "oi_description")
_D_OI_HOLD_FLAG: Final[FieldDescriptor] = _otm2_descriptor(Filler1, "oi_hold_flag")
_D_OI_UNAPL: Final[FieldDescriptor] = _otm2_descriptor(Filler1, "oi_unapl")
_D_OI_P_C: Final[FieldDescriptor] = _otm2_descriptor(Filler2, "oi_p_c")
_D_OI_NET: Final[FieldDescriptor] = _otm2_descriptor(Filler2, "oi_net")
_D_OI_APPROP: Final[FieldDescriptor] = _otm2_descriptor(Filler2, "oi_approp")
_D_OI_EXTRA: Final[FieldDescriptor] = _otm2_descriptor(Filler2, "oi_extra")
_D_OI_CARRIAGE: Final[FieldDescriptor] = _otm2_descriptor(Filler2, "oi_carriage")
_D_OI_VAT: Final[FieldDescriptor] = _otm2_descriptor(Filler2, "oi_vat")
_D_OI_DISCOUNT: Final[FieldDescriptor] = _otm2_descriptor(Filler2, "oi_discount")
_D_OI_E_VAT: Final[FieldDescriptor] = _otm2_descriptor(Filler2, "oi_e_vat")
_D_OI_C_VAT: Final[FieldDescriptor] = _otm2_descriptor(Filler2, "oi_c_vat")
_D_OI_PAID: Final[FieldDescriptor] = _otm2_descriptor(Filler2, "oi_paid")
_D_OI_STATUS: Final[FieldDescriptor] = _otm2_descriptor(Filler1, "oi_status")
_D_OI_DEDUCT_DAYS: Final[FieldDescriptor] = _otm2_descriptor(Filler1, "oi_deduct_days")
_D_OI_DEDUCT_AMT: Final[FieldDescriptor] = _otm2_descriptor(Filler1, "oi_deduct_amt")
_D_OI_DEDUCT_VAT: Final[FieldDescriptor] = _otm2_descriptor(Filler1, "oi_deduct_vat")
_D_OI_DAYS: Final[FieldDescriptor] = _otm2_descriptor(Filler1, "oi_days")
_D_OI_CR: Final[FieldDescriptor] = _otm2_descriptor(Filler1, "oi_cr")
_D_OI_APPLIED: Final[FieldDescriptor] = _otm2_descriptor(Filler1, "oi_applied")
_D_OI_DATE_CLEARED: Final[FieldDescriptor] = _otm2_descriptor(Filler1, "oi_date_cleared")

#: The NUMERIC leaves of `OI-Header`, which `INITIALIZE` sets to the value zero.
_OI_HEADER_NUMERIC_LEAVES: Final[tuple[FieldDescriptor, ...]] = (
    _D_OI_CHECK,
    _D_OI_INVOICE,
    _D_OI_DATE,
    _D_OI_B_NOS,
    _D_OI_B_ITEM,
    _D_OI_TYPE,
    _D_OI_P_C,
    _D_OI_NET,
    _D_OI_APPROP,
    _D_OI_EXTRA,
    _D_OI_CARRIAGE,
    _D_OI_VAT,
    _D_OI_DISCOUNT,
    _D_OI_E_VAT,
    _D_OI_C_VAT,
    _D_OI_PAID,
    _D_OI_STATUS,
    _D_OI_DEDUCT_DAYS,
    _D_OI_DEDUCT_AMT,
    _D_OI_DEDUCT_VAT,
    _D_OI_DAYS,
    _D_OI_CR,
    _D_OI_DATE_CLEARED,
)

_OI_HEADER_ALPHANUMERIC_LEAVES: Final[tuple[FieldDescriptor, ...]] = (
    _D_OI_NOS,
    _D_OI_DESCRIPTION,
    _D_OI_HOLD_FLAG,
    _D_OI_UNAPL,
    _D_OI_APPLIED,
)


# THE CONDITION NAMES THIS PROGRAM TESTS (rule R-2: no `88`-level test is written here;
# each one resolves to the published vocabulary) copybooks/slwsinv2.cob:L72 88 pending
# value "P".
_IS_PENDING: Final = condition_names.is_pending_slwsinv2
_IS_APPLIED: Final = condition_names.is_applied_slwsinv2
_IS_IH_ANALYISED: Final = condition_names.is_ih_analyised_slwsinv2
_IS_IL_ANALYISED: Final = condition_names.is_il_analyised_slwsinv2

#: `88 FS-Cobol-Files-Used value zero.` [copybooks/wssystem.cob:L113], declared on
#: `File-System-Used`, with `88 FS-RDBMS-Used value 1.` [copybooks/wssystem.cob:L116] as
#: its sibling.
_IS_FS_COBOL_FILES_USED: Final = condition_names.predicate_for(
    "FS-Cobol-Files-Used", copybook="copybooks/wssystem.cob"
)

_D_FILE_KEY_NO: Final[FieldDescriptor] = _field_of(LoggingData.FIELDS, "File-Key-No")

#: `03 Date-Form pic 9.` [copybooks/wssystem.cob] - read AND written by `zz070-Convert-
#: Date` [sales/sl055.cbl:L704-L705].
_D_DATE_FORM: Final[FieldDescriptor] = _field_of(SystemDataBlock.FIELDS, "Date-Form")

#: `05 File-System-Used pic 9.` [copybooks/wssystem.cob:L112] - the conditional variable
#: that `88 FS-Cobol-Files-Used value zero.` [copybooks/wssystem.cob:L113] and `88 FS-
#: RDBMS-Used value 1.` [copybooks/wssystem.cob:L116] are declared on.
_D_FILE_SYSTEM_USED: Final[FieldDescriptor] = _field_of(
    RdbmsFlatStatuses.FIELDS, "File-System-Used"
)


class CobolFileSystemPathUnavailable(RuntimeError):
    """`if FS-Cobol-Files-Used` was TRUE, and that path needs COBOL (rule R-1).

    Raised from `_da000_mainline` when the system record selects the INDEXED (COBOL)
    file system rather than the RDBMS one, because the block that branch guards cannot
    be reproduced in Python.
    """


class InvoiceRecordAreaNotLoaded(RuntimeError):
    """The invoice record area does not hold the view the program is reading.

    A PROGRAMMER error, and specifically a violation of the facade's contract - never
    something record CONTENT can cause.
    """


class _Label(enum.Enum):
    """The paragraph labels this program's `GO TO` statements transfer to.

    Rule R-5 requires a named function per paragraph AND a class annotation at every
    transfer site, and section 0.7.4 conflict C-4 resolves the tension between
    traceability and restructuring by "[k]eeping the function boundary fixed at the
    paragraph boundary and varying only the TRANSFER MECHANISM".
    """

    DA010_READ_LOOP = "da010-Read-Loop"
    #: `da020-Header-Analysis.` [sales/sl055.cbl:L426] - reached only by fall-through,
    #: never by a `GO TO`.
    DA020_HEADER_ANALYSIS = "da020-Header-Analysis"
    DA030_SKIP_INVOICE = "da030-Skip-Invoice"
    DA040_CLOSE_FILES = "da040-Close-Files"
    DA999_MENU_EXIT = "da999-Menu-Exit"
    GOBACK = "goback"
    #: `DB000-Create-Main.` [sales/sl055.cbl:L530] - the class-4 target of
    #: [sales/sl055.cbl:L585], a BACKWARD transfer from the paragraph below it.
    DB000_CREATE_MAIN = "DB000-Create-Main"
    DB010_CREATE_ANAL = "db010-Create-Anal"
    DB999_MAIN_EXIT = "db999-Main-Exit"


class _FacadeVerbs(Protocol):
    """The sixteen ENTITY-named facade verbs this program performs.

    `sl055` copies `Proc-ACAS-FH-Calls.cob` [sales/sl055.cbl:L731] and not the
    IRS convention's `Proc-ZZ100-ACAS-IRS-Calls.cob`, so it performs
    entity-named paragraphs - `Value-Read-Indexed`, `Analysis-Write`,
    `Invoice-Rewrite` - and TESTS `Fs-Reply` INLINE after each one. That copybook
    declares no error-check paragraph at all, which is a behavioural difference
    from the IRS convention and not merely a naming one, so nothing below calls a
    handler-named alias and nothing below expects the facade to raise on a
    non-zero reply.

    THE CALL SHAPE IS SECTION 0.4.3's, VERBATIM: `perform GL-Batch-Read-Next`
    becomes `facade.gl_batch_read_next(ctx)` - one context argument carrying the
    blocks the dispatch paragraph names. Here that is `_Sl055Context`. Declared
    as a Protocol so the sixteen verbs are named explicitly and a test double is
    structurally sufficient, and the real binding is resolved at first use by
    `_resolve_facade`. AMBIGUITY Q-57 covers whether the verb shape assumed here
    is the one `acas_posting.dal.facade` publishes.

    Each verb SETS `File-Function` and `Access-Type` and then dispatches to its
    handler, so each one writes `ctx.file_access.fs_reply` and returns nothing.
    The paragraph locators are `copybooks/Proc-ACAS-FH-Calls.cob`: `Value-Open`
    L711, `Value-Open-Input` L716, `Value-Open-Output` L721, `Value-Close` L726,
    `Value-Read-Indexed` L753, `Value-Write` L759, `Value-Rewrite` L764,
    `Analysis-Open` L831, `Analysis-Close` L846, `Analysis-Read-Indexed` L867,
    `Analysis-Write` L873, `Invoice-Open` L885, `Invoice-Close` L900,
    `Invoice-Start` L917, `Invoice-Read-Next` L922, `Invoice-Rewrite` L943.
    """

    def value_open(self, ctx: _Sl055Context, /) -> None:
        """`Value-Open.` [copybooks/Proc-ACAS-FH-Calls.cob:L711] - open I-O."""

    def value_open_input(self, ctx: _Sl055Context, /) -> None:
        """`Value-Open-Input.` [copybooks/Proc-ACAS-FH-Calls.cob:L716]."""

    def value_open_output(self, ctx: _Sl055Context, /) -> None:
        """`Value-Open-Output.` [copybooks/Proc-ACAS-FH-Calls.cob:L721]."""

    def value_close(self, ctx: _Sl055Context, /) -> None:
        """`Value-Close.` [copybooks/Proc-ACAS-FH-Calls.cob:L726]."""

    def value_read_indexed(self, ctx: _Sl055Context, /) -> None:
        """`Value-Read-Indexed.` [copybooks/Proc-ACAS-FH-Calls.cob:L753]."""

    def value_write(self, ctx: _Sl055Context, /) -> None:
        """`Value-Write.` [copybooks/Proc-ACAS-FH-Calls.cob:L759]."""

    def value_rewrite(self, ctx: _Sl055Context, /) -> None:
        """`Value-Rewrite.` [copybooks/Proc-ACAS-FH-Calls.cob:L764]."""

    def analysis_open(self, ctx: _Sl055Context, /) -> None:
        """`Analysis-Open.` [copybooks/Proc-ACAS-FH-Calls.cob:L831]."""

    def analysis_close(self, ctx: _Sl055Context, /) -> None:
        """`Analysis-Close.` [copybooks/Proc-ACAS-FH-Calls.cob:L846]."""

    def analysis_read_indexed(self, ctx: _Sl055Context, /) -> None:
        """`Analysis-Read-Indexed.` [copybooks/Proc-ACAS-FH-Calls.cob:L867]."""

    def analysis_write(self, ctx: _Sl055Context, /) -> None:
        """`Analysis-Write.` [copybooks/Proc-ACAS-FH-Calls.cob:L873]."""

    def invoice_open(self, ctx: _Sl055Context, /) -> None:
        """`Invoice-Open.` [copybooks/Proc-ACAS-FH-Calls.cob:L885]."""

    def invoice_close(self, ctx: _Sl055Context, /) -> None:
        """`Invoice-Close.` [copybooks/Proc-ACAS-FH-Calls.cob:L900]."""

    def invoice_start(self, ctx: _Sl055Context, /) -> None:
        """`Invoice-Start.` [copybooks/Proc-ACAS-FH-Calls.cob:L917]."""

    def invoice_read_next(self, ctx: _Sl055Context, /) -> None:
        """`Invoice-Read-Next.` [copybooks/Proc-ACAS-FH-Calls.cob:L922]."""

    def invoice_rewrite(self, ctx: _Sl055Context, /) -> None:
        """`Invoice-Rewrite.` [copybooks/Proc-ACAS-FH-Calls.cob:L943]."""


def _resolve_facade() -> _FacadeVerbs:
    """Bind the entity-named facade, at first use rather than at import.

    Returns:
        The facade module, which structurally satisfies `_FacadeVerbs`.

    Raises:
        ModuleNotFoundError: `acas_posting.dal.facade` cannot be imported. The message
            is Python's own; `run`'s `facade` parameter is the documented way to supply
            an alternative.
    """
    from acas_posting.dal import facade

    return _BoundFacade(facade)


_ENTITY_RECORD: Final[dict[str, str]] = {
    "value": "ws_value_record",
    "analysis": "ws_analysis_record",
    "invoice": "ws_invoice_record",
}


class _BoundFacade:
    """`_Sl055Context` on this side, `facade.FacadeContext` on the other.

    THIS RESOLVES AMBIGUITY Q-57. The question `_FacadeVerbs` records is what shape of
    single argument the generated facade would publish; the answer is that it publishes
    `verb(ctx.
    """

    __slots__ = ("_facade",)

    def __init__(self, facade_module: object) -> None:
        self._facade = facade_module

    def __getattr__(self, verb: str) -> object:
        """Bind one entity-named verb, resolving its record area by prefix."""
        entity = next(
            (name for name in _ENTITY_RECORD if verb.startswith(f"{name}_")), None
        )
        if entity is None:
            raise AttributeError(
                f"sl055 performs no facade verb {verb!r}; it copies "
                f'copy "Proc-ACAS-FH-Calls.cob". [sales/sl055.cbl:L731] and '
                f"reaches only the Value, Analysis and Invoice entities"
            )
        target = getattr(self._facade, verb)
        record_attribute = _ENTITY_RECORD[entity]

        def _perform(ctx: _Sl055Context, /) -> None:
            target(
                self._facade.FacadeContext(
                    ctx.system_record,
                    getattr(ctx, record_attribute),
                    ctx.file_access,
                    ctx.file_defs,
                    ctx.acas_dal_common_data,
                )
            )

        return _perform


@dataclass(slots=True)
class _InvoiceRecordArea:
    """`01 Invoice-Record.` and its two `REDEFINES` views - one 137-byte area.

    which is why `ih-test = zero` [sales/sl055.cbl:L370] discriminates a header from a
    line - a header carries item number zero - and why writing `invoice-nos`/`item-nos`
    through the GENERIC view at [sales/sl055.cbl:L473-L474] positions the `Invoice-
    Start` that follows.
    """

    invoice_nos: int = 0
    item_nos: int = 0
    invoice_header: IhInvoiceHeader | None = None
    invoice_line: IlInvoiceLine | None = None

    @property
    def ih_test(self) -> int:
        """`ih-test pic 99` [copybooks/slwsinv2.cob:L41] - bytes 9-10."""
        return self.item_nos

    @property
    def header(self) -> IhInvoiceHeader:
        """The header view, for the paragraphs that only ever see headers.

        Raises:
            InvoiceRecordAreaNotLoaded: No header view is loaded.
        """
        if self.invoice_header is None:
            raise InvoiceRecordAreaNotLoaded(
                "the invoice record area holds no `01 Invoice-Header` view "
                "[copybooks/slwsinv2.cob:L38]; a facade read verb must load one "
                "before `da020-Header-Analysis` [sales/sl055.cbl:L426] or "
                "`dd000-Extract` [sales/sl055.cbl:L626] reads it"
            )
        return self.invoice_header

    @property
    def line(self) -> IlInvoiceLine:
        """The line view, for the inner loop's value-analysis accumulation.

        Raises:
            InvoiceRecordAreaNotLoaded: No line view is loaded.
        """
        if self.invoice_line is None:
            raise InvoiceRecordAreaNotLoaded(
                "the invoice record area holds no `01 Invoice-Line` view "
                "[copybooks/slwsinv2.cob:L91]; a facade read verb must load one "
                "before `da010-Read-Loop` [sales/sl055.cbl:L364] reads it"
            )
        return self.invoice_line


def _initialize_oi_header_with_filler() -> OiHeader:
    """`initialize oi-header with filler.` [sales/sl055.cbl:L635].

    The `INITIALIZE` verb sets every elementary item of the group to its CATEGORY
    DEFAULT - numeric items to the value zero, alphanumeric items to spaces - and the
    `WITH FILLER` phrase extends that to `FILLER` items, which are otherwise left alone.

    Returns:
        An `OI-Header` with all twenty-eight leaves at their category defaults.
    """
    (
        oi_check,
        oi_invoice,
        oi_date,
        oi_b_nos,
        oi_b_item,
        oi_type,
        oi_p_c,
        oi_net,
        oi_approp,
        oi_extra,
        oi_carriage,
        oi_vat,
        oi_discount,
        oi_e_vat,
        oi_c_vat,
        oi_paid,
        oi_status,
        oi_deduct_days,
        oi_deduct_amt,
        oi_deduct_vat,
        oi_days,
        oi_cr,
        oi_date_cleared,
    ) = move.move_to_all(move.ZERO, _OI_HEADER_NUMERIC_LEAVES)
    (
        oi_nos,
        oi_description,
        oi_hold_flag,
        oi_unapl,
        oi_applied,
    ) = move.move_to_all(move.SPACE, _OI_HEADER_ALPHANUMERIC_LEAVES)

    return OiHeader(
        oi_key=OiKey(
            oi_customer=OiCustomer(oi_nos=str(oi_nos), oi_check=int(oi_check)),
            oi_invoice=int(oi_invoice),
        ),
        filler_1=Filler1(
            oi_date=int(oi_date),
            oi_batch=OiBatch(oi_b_nos=int(oi_b_nos), oi_b_item=int(oi_b_item)),
            oi_type=int(oi_type),
            oi_description=str(oi_description),
            oi_hold_flag=str(oi_hold_flag),
            oi_unapl=str(oi_unapl),
            filler_2=Filler2(
                oi_p_c=Decimal(oi_p_c),
                oi_net=Decimal(oi_net),
                oi_approp=Decimal(oi_approp),
                oi_extra=Decimal(oi_extra),
                oi_carriage=Decimal(oi_carriage),
                oi_vat=Decimal(oi_vat),
                oi_discount=Decimal(oi_discount),
                oi_e_vat=Decimal(oi_e_vat),
                oi_c_vat=Decimal(oi_c_vat),
                oi_paid=Decimal(oi_paid),
            ),
            oi_status=int(oi_status),
            oi_deduct_days=int(oi_deduct_days),
            oi_deduct_amt=Decimal(oi_deduct_amt),
            oi_deduct_vat=Decimal(oi_deduct_vat),
            oi_days=int(oi_days),
            oi_cr=int(oi_cr),
            oi_applied=str(oi_applied),
            oi_date_cleared=int(oi_date_cleared),
        ),
    )


@dataclass(slots=True)
class _Sl055Context:
    """`sl055`'s state - its linkage, its working storage and its record areas.

    Note that the dispatch paragraph sets `File-Key-No` ITSELF, and so does `Value-Read-
    Indexed` [copybooks/Proc-ACAS-FH-Calls.cob:L753-L757] - which makes this program's
    nine explicit `move 1 to File-Key-No` statements triply redundant. All nine are
    preserved regardless (rule R-3, AMBIGUITY Q-55).
    """


    ws_calling_data: WsCallingData
    system_record: SystemRecord
    system_record_4: SystemRecord4
    to_day: str
    file_defs: FileDefs


    file_access: FileAccess = field(default_factory=FileAccess)
    ws_value_record: WsValueRecord = field(default_factory=WsValueRecord)
    ws_analysis_record: WsAnalysisRecord = field(default_factory=WsAnalysisRecord)
    ws_invoice_record: _InvoiceRecordArea = field(default_factory=_InvoiceRecordArea)
    acas_dal_common_data: AcasDalCommonData = field(default_factory=AcasDalCommonData)


    ws_p_flag: int = 0
    ws_anal_flag: int = 0
    save_code: str = "   "
    v_exists: int = 0
    ws_inv_amt: Decimal = Decimal("0.00")
    work_2: Decimal = Decimal("0.00")
    ws_vat_totalv: Decimal = Decimal("0.00")
    ws_vatr_totalv: Decimal = Decimal("0.00")
    ws_carr_totalv: Decimal = Decimal("0.00")
    ws_disc_totalv: Decimal = Decimal("0.00")
    work_3: int = 0
    ws_vat_totalt: int = 0
    ws_vatr_totalt: int = 0
    ws_carr_totalt: int = 0
    ws_disc_totalt: int = 0
    exception_msg: str = " " * 25


    oi_header: OiHeader = field(default_factory=_initialize_oi_header_with_filler)
    #: `open-item-file-2` [copybooks/seloi2.cob] - the OTM2 work file, and the
    #: CHANNEL to `sl060`. The SHARED carrier `acas_posting.workfiles` publishes,
    #: not a module-private one: the producer and the consumer must hold the SAME
    #: object or nothing this program writes can be read, which is exactly what
    #: naming the same `assign file-18` achieves in COBOL.
    open_item_file_2: OpenItemWorkFile[OiHeader] = field(
        default_factory=lambda: open_item_work_file(OPEN_ITEM_2_NAME, OiHeader)
    )


    #: The `ws-date` work area `zz070-Convert-Date` [sales/sl055.cbl:L694] fills,
    #: consolidated in `acas_posting.dates` because its body is byte-identical in all
    #: ten programs that carry it.
    date_formats: dates.WsDateFormats = field(default_factory=dates.WsDateFormats)
    facade: _FacadeVerbs | None = None

    @property
    def fs_reply(self) -> int:
        """`03 Fs-Reply pic 99.` [copybooks/wsfnctn.cob:L25].

        ONE FIELD, TWO PRODUCERS. Every facade verb writes it, and so does every `open-
        item-file-2` operation, because [copybooks/seloi2.cob] declares `status fs-
        reply` - the same field.
        """
        return self.file_access.fs_reply

    @property
    def verbs(self) -> _FacadeVerbs:
        """The facade, resolved.

        Raises:
            RuntimeError: `run` did not bind one. A PROGRAMMER error: the only entry
                point sets it before performing any paragraph.
        """
        if self.facade is None:
            raise RuntimeError(
                "no facade is bound; `sl055` reaches every file through "
                "`copy \"Proc-ACAS-FH-Calls.cob\".` [sales/sl055.cbl:L731] and "
                "`run` binds it before performing `da000-mainline`"
            )
        return self.facade


# Each one is normalised THROUGH the `MOVE` primitive against the field it is moved into
# or compared with, rather than written as a bare Python string, because a COBOL
# relation condition compares operands at the RECEIVING FIELD'S WIDTH.

_VALUE_SYSTEM_SALES: Final[str] = move.move_alphanumeric("S", _D_VA_SYSTEM)

_COMMENT_LINE_MARKER: Final[str] = "/"

#: `if il-type not = 3` [sales/sl055.cbl:L390], [sales/sl055.cbl:L413], commented "Cr.
#: notes". AMBIGUITY Q-53.
_IL_TYPE_CREDIT_NOTE: Final[str] = move.move_alphanumeric(3, _D_IL_TYPE)

_IL_UPDATE_ANALYSED: Final[str] = move.move_alphanumeric("Z", _D_IL_UPDATE)

_IH_UPDATE_ANALYSED: Final[str] = move.move_alphanumeric("Z", _D_IH_UPDATE)

_IH_STATUS_APPLIED: Final[str] = move.move_alphanumeric("Z", _D_IH_STATUS)

_IH_STATUS_A_APPLIED: Final[str] = move.move_alphanumeric("A", _D_IH_STATUS_A)

_IH_STATUS_L_PRINTED: Final[str] = move.move_alphanumeric("L", _D_IH_STATUS_L)

#: `move space to va-second` [sales/sl055.cbl:L405], [sales/sl055.cbl:L547] and the
#: comparand of `if va-second = space` [sales/sl055.cbl:L402], [sales/sl055.cbl:L542],
#: [sales/sl055.cbl:L611].
_VA_SECOND_SPACE: Final[str] = str(move.move_figurative(move.SPACE, _D_VA_SECOND))

_PA_SECOND_SPACE: Final[str] = str(move.move_figurative(move.SPACE, _D_PA_SECOND))

#: `move "Svo" to va-code.` [sales/sl055.cbl:L482] - the FIRST of the four special-total
#: keys, and the only one that sets `va-system` as well.
_SPECIAL_TOTAL_VAT_CODE: Final[str] = "Svo"
_SPECIAL_TOTAL_VATR_GROUP: Final[str] = "vp"
_SPECIAL_TOTAL_CARRIAGE_GROUP: Final[str] = "zc"
_SPECIAL_TOTAL_DISCOUNT_GROUP: Final[str] = "zd"

#: `ih-type` values, from the type table `copybooks/slwsoi.cob:L20-L31`: 1 = Receipt, 2
#: = Account (invoice), 3 = Cr. Note, 4 = Proforma.
_IH_TYPE_RECEIPT: Final[int] = 1
_IH_TYPE_INVOICE: Final[int] = 2
_IH_TYPE_CREDIT_NOTE: Final[int] = 3
_IH_TYPE_PROFORMA: Final[int] = 4

#: `multiply -1 by ...` - the multiplier of all twelve sign flips
#: [sales/sl055.cbl:L446], [sales/sl055.cbl:L457], [sales/sl055.cbl:L463] and
#: [sales/sl055.cbl:L658-L666]. NO `GIVING`, so the RECEIVER IS THE SECOND OPERAND.
_NEGATE: Final[int] = -1


# THE THREE-BYTE GROUP KEYS - `va-code` AND `WS-PA-Code` `03 va-code.`
# [copybooks/wsval.cob:L10] and `03 WS-Pa-Code.` [copybooks/wsanal.cob:L10] are GROUP
# items of three one-character children.


def _three_byte_group_image(first: str, second: str, third: str) -> str:
    """The byte image of a three-one-character-children group item.

    Args:
        first: The first child's image - `va-system` or `Pa-System`.
        second: The second child's image - `va-first` or `Pa-First`.
        third: The third child's image - `va-second` or `Pa-Second`.

    Returns:
        The group's three-character byte image.
    """
    return f"{first}{second}{third}"


def _place_va_code(record: WsValueRecord, image: str) -> None:
    """Distribute a three-byte image over `va-code`'s three children.

    Args:
        record: The value record whose key is being set.
        image: The three-character image a `move_group` produced.
    """
    # Reference modification is ONE-BASED, and `acas_posting.cobol.move.ref_mod` is the
    # primitive for it: never Python slicing, whose bounds differ by one.
    record.va_code.va_system = move.ref_mod(image, 1, 1)
    record.va_code.va_group.va_first = move.ref_mod(image, 2, 1)
    record.va_code.va_group.va_second = move.ref_mod(image, 3, 1)


def _place_va_group(record: WsValueRecord, image: str) -> None:
    """Distribute a two-byte image over `va-group`'s two children.

    Args:
        record: The value record whose group is being set.
        image: The two-character image a `move_group` produced.
    """
    record.va_code.va_group.va_first = move.ref_mod(image, 1, 1)
    record.va_code.va_group.va_second = move.ref_mod(image, 2, 1)


def _place_pa_code(record: WsAnalysisRecord, image: str) -> None:
    """Distribute a three-byte image over `WS-PA-Code`'s three children.

    Args:
        record: The analysis record whose key is being set.
        image: The three-character image a `move_group` produced.
    """
    record.ws_pa_code.pa_system = move.ref_mod(image, 1, 1)
    record.ws_pa_code.pa_group.pa_first = move.ref_mod(image, 2, 1)
    record.ws_pa_code.pa_group.pa_second = move.ref_mod(image, 3, 1)


def _da000_mainline(ctx: _Sl055Context) -> None:
    """`da000-mainline section.` - open everything, then fall into the loop.

    Read as a normal open this looks redundant, and it is not: it is an existence probe.
    Try to open for input.

    Args:
        ctx: The program's state. Its `system_record` is read for `File-System-Used`;
            its `file_access`, `ws_value_record` and `open_item_file_2` are all written.

    Raises:
        CobolFileSystemPathUnavailable: `FS-Cobol-Files-Used` was true.
    """
    # 308  accept   ws-env-lines   from lines.
    # 309-313  if ws-env-lines < 24 / move 24 to ws-env-lines ws-lines / else ...
    # 314  subtract 1 from ws-lines giving ws-23-lines.
    #
    # OMITTED. `accept ... from lines` reads the TERMINAL'S HEIGHT, not a clock -
    # rule R-6 is about reproducibility of the run date and this is neither a date
    # nor a source of non-determinism in any table. `ws-lines` and `ws-23-lines`
    # are used only as screen row numbers in the `display ... at line` statements
    # [L504, L506, L684-L687], whose positions this module drops whether the
    # display becomes a log record or is dropped outright, so with the positions
    # gone the geometry has no remaining consumer. The `subtract` is therefore also
    # omitted, which is why the arithmetic census in the module docstring marks it
    # as the one statement not transcribed.
    #
    # 316  set      ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".
    # 317  set      ENVIRONMENT "COB_SCREEN_ESC" to "Y".
    #
    # OMITTED. These configure the curses screen handler to report Esc, PgUp,
    # PgDown and PrtSC as exceptions. There is no screen here.

    ctx.verbs.value_open_input(ctx)
    if arithmetic.compare(ctx.fs_reply, FsReply.SUCCESS) != 0:
        ctx.verbs.value_close(ctx)
        ctx.verbs.value_open_output(ctx)
    ctx.verbs.value_close(ctx)

    if _IS_FS_COBOL_FILES_USED(
        ctx.system_record.system_data_block.rdbms_flat_statuses.file_system_used
    ):
        # 339 display SL125 at 2301 Emitted before raising, because it is the message
        # the compiled program produces on the only path out of this block that has an
        # observable effect.
        _LOG.error("%s", _SL125)
        # 344 move 8 to WS-Term-Code PRESERVED, and set BEFORE the raise.
        ctx.ws_calling_data.ws_term_code = int(
            move.move_numeric(
                _TERM_CODE_ANALYSIS_FILE_MISSING,
                _calling_descriptor("ws_term_code"),
            )
        )
        # 345 goback The compiled program returns here. This module cannot simply
        # return, because the three sub-outcomes of the block are not distinguishable
        # without `CBL_CHECK_FILE_EXIST`.
        raise CobolFileSystemPathUnavailable(
            "sl055 [sales/sl055.cbl:L326-L348] requires the GnuCOBOL built-in "
            '`CBL_CHECK_FILE_EXIST` and the COBOL program `sl070`; `sl070` is out '
            "of scope for this migration (Agent Action Plan section 0.2.2) and "
            "rule R-1 forbids invoking COBOL at run time. This branch is "
            "unreachable in the RDBMS configuration the migration targets: "
            "`88 FS-Cobol-Files-Used value zero.` [copybooks/wssystem.cob:L113] "
            "against `88 FS-RDBMS-Used value 1.` [copybooks/wssystem.cob:L116]. "
            "`WS-Term-Code` has been set to "
            f"{_TERM_CODE_ANALYSIS_FILE_MISSING} per [sales/sl055.cbl:L344]."
        )

    # 349 move 1 to File-Key-No. The first of NINE.
    ctx.file_access.logging_data.file_key_no = int(move.move_numeric(1, _D_FILE_KEY_NO))

    _LOG.info("%s", _PROG_NAME)
    _LOG.info("%s", _TITLE)

    _zz070_convert_date(ctx)
    _zz070_exit()

    # 354  display  ws-date at 0171 with foreground-color 2.
    #
    #  THE RUN DATE IS NOT IN A RECORD, and the display therefore has no log
    #  counterpart at all. `ws-date` is the posting date this run stamps into
    #  every record it writes - a date with business meaning, which the
    #  safe-event schema in `acas_posting/dal/status.py` excludes (CWE-532).
    #  The date is an INPUT the caller supplied through the `to-day` operand, so
    #  it is already known wherever the run was started, and `clock.py` pins it,
    #  so no record is needed to reconstruct it. The SAME omission is made in
    #  `gl070`, `gl080`, `sl060`, `sl100`, `pl055`, `pl060` and `pl100`, whose
    #  banners each show the same converted date.

    ctx.verbs.invoice_open(ctx)
    ctx.verbs.value_open(ctx)
    ctx.verbs.analysis_open(ctx)

    # 359 open extend open-item-file-2. 360 if fs-reply not = zero 361 close open-item-
    # file-2 362 open output open-item-file-2.
    ctx.open_item_file_2.open_extend(ctx.file_access)
    if arithmetic.compare(ctx.fs_reply, FsReply.SUCCESS) != 0:
        ctx.open_item_file_2.close(ctx.file_access)
        ctx.open_item_file_2.open_output(ctx.file_access)

    # FALL-THROUGH 1 OF 2: control leaves this section here and enters `da010-Read-
    # Loop.` [sales/sl055.cbl:L364] with no transfer statement.


def _da010_read_loop(ctx: _Sl055Context) -> _Label:
    """`da010-Read-Loop.` - the item-level loop, and the value-analysis build.

    Why the `UNTIL` and the explicit L367 test are both reproduced is set out in the
    module docstring: `Fs-Reply` is one shared field with several producers, so the two
    tests can see different values and lead to different places.

    Args:
        ctx: The program's state.

    Returns:
        `_Label.DA040_CLOSE_FILES` when the read hit end of file - the class-2 transfer
            - or `_Label.DA020_HEADER_ANALYSIS` when the loop ended by `exit perform` or
            by its own `UNTIL`, both of which FALL THROUGH.
    """
    while arithmetic.compare(ctx.fs_reply, FsReply.END_OF_FILE) != 0:
        ctx.verbs.invoice_read_next(ctx)

        if arithmetic.compare(ctx.fs_reply, FsReply.END_OF_FILE) == 0:
            # 368 go to da040-Close-Files GO TO class 2 - a forward terminator OUT OF
            # the inline perform, which GnuCOBOL permits and `-Wno-goto-section` stops
            # it warning about.
            return _Label.DA040_CLOSE_FILES

        if arithmetic.compare(ctx.ws_invoice_record.ih_test, 0) == 0:
            break

        line = ctx.ws_invoice_record.line

        if _IS_IL_ANALYISED(line.il_update):
            continue

        # 376 if il-product (1:1) = "/" *> comment only REFERENCE MODIFICATION IS ONE-
        # BASED. `move.ref_mod` is the primitive.
        if move.ref_mod(line.il_product, 1, 1) == _COMMENT_LINE_MARKER:
            continue

        value = ctx.ws_value_record

        value.va_code.va_system = _VALUE_SYSTEM_SALES
        _place_va_group(
            value, move.move_group(line.il_pa, _D_VA_GROUP, sending_field=_D_IL_PA, length=2)
        )
        ctx.v_exists = int(move.move_numeric(1, _D_V_EXISTS))
        ctx.file_access.logging_data.file_key_no = int(move.move_numeric(1, _D_FILE_KEY_NO))
        ctx.verbs.value_read_indexed(ctx)

        if (
            arithmetic.compare(ctx.fs_reply, FsReply.INVALID_KEY_ON_START) == 0
            or arithmetic.compare(ctx.fs_reply, FsReply.KEY_NOT_FOUND) == 0
        ):
            _db000_create(ctx)
            ctx.v_exists = int(move.move_figurative(move.ZERO, _D_V_EXISTS))


        value.va_t_this = int(
            arithmetic.add_to(1, receiver_value=value.va_t_this, receiving=_D_VA_T_THIS)
        )
        value.va_t_year = int(
            arithmetic.add_to(1, receiver_value=value.va_t_year, receiving=_D_VA_T_YEAR)
        )
        if line.il_type != _IL_TYPE_CREDIT_NOTE:
            value.va_v_this = Decimal(
                arithmetic.add_to(
                    line.il_net, receiver_value=value.va_v_this, receiving=_D_VA_V_THIS
                )
            )
            value.va_v_year = Decimal(
                arithmetic.add_to(
                    line.il_net, receiver_value=value.va_v_year, receiving=_D_VA_V_YEAR
                )
            )
        else:
            # 394 subtract il-net from VA-V-This `SUBTRACT a FROM b` with no `GIVING` is
            # `b = b - a`, so the RECEIVER is the field named after `FROM`.
            value.va_v_this = Decimal(
                arithmetic.subtract_from(
                    line.il_net, receiver_value=value.va_v_this, receiving=_D_VA_V_THIS
                )
            )
            value.va_v_year = Decimal(
                arithmetic.subtract_from(
                    line.il_net, receiver_value=value.va_v_year, receiving=_D_VA_V_YEAR
                )
            )

        if arithmetic.compare(ctx.v_exists, 0) == 0:
            ctx.verbs.value_write(ctx)
        else:
            ctx.verbs.value_rewrite(ctx)

        if value.va_code.va_group.va_second == _VA_SECOND_SPACE:
            # 403 exit perform cycle EXIT PERFORM CYCLE [sales/sl055.cbl:L403] -
            # iterate.
            continue

        value.va_code.va_group.va_second = str(
            move.move_figurative(move.SPACE, _D_VA_SECOND)
        )
        ctx.file_access.logging_data.file_key_no = int(move.move_numeric(1, _D_FILE_KEY_NO))
        ctx.verbs.value_read_indexed(ctx)
        if (
            arithmetic.compare(ctx.fs_reply, FsReply.INVALID_KEY_ON_START) == 0
            or arithmetic.compare(ctx.fs_reply, FsReply.KEY_NOT_FOUND) == 0
        ):
            # 409 exit perform cycle EXIT PERFORM CYCLE [sales/sl055.cbl:L409] -
            # iterate. THE PARENT GROUP IS NOT CREATED HERE, unlike the specific group
            # at L385.
            continue

        # The identical four statements as L388-L396, deliberately written out again
        # rather than shared with them. See the docstring.

        value.va_t_this = int(
            arithmetic.add_to(1, receiver_value=value.va_t_this, receiving=_D_VA_T_THIS)
        )
        value.va_t_year = int(
            arithmetic.add_to(1, receiver_value=value.va_t_year, receiving=_D_VA_T_YEAR)
        )
        if line.il_type != _IL_TYPE_CREDIT_NOTE:
            value.va_v_this = Decimal(
                arithmetic.add_to(
                    line.il_net, receiver_value=value.va_v_this, receiving=_D_VA_V_THIS
                )
            )
            value.va_v_year = Decimal(
                arithmetic.add_to(
                    line.il_net, receiver_value=value.va_v_year, receiving=_D_VA_V_YEAR
                )
            )
        else:
            value.va_v_this = Decimal(
                arithmetic.subtract_from(
                    line.il_net, receiver_value=value.va_v_this, receiving=_D_VA_V_THIS
                )
            )
            value.va_v_year = Decimal(
                arithmetic.subtract_from(
                    line.il_net, receiver_value=value.va_v_year, receiving=_D_VA_V_YEAR
                )
            )

        # 420  perform  Value-Rewrite      <- ALWAYS a rewrite, never a write
        ctx.verbs.value_rewrite(ctx)
        line.il_update = _IL_UPDATE_ANALYSED
        ctx.verbs.invoice_rewrite(ctx)
        # 423 exit perform cycle EXIT PERFORM CYCLE [sales/sl055.cbl:L423] - iterate.
        # The last statement of the loop body, so it is the one departure that changes
        # nothing.
        continue

    return _Label.DA020_HEADER_ANALYSIS


def _da020_header_analysis(ctx: _Sl055Context) -> _Label:
    """`da020-Header-Analysis.` - the header-level processing and four totals.

    Reached only by FALL-THROUGH out of `da010-Read-Loop.`, never by a transfer, and
    ending in `go to da010-Read-Loop.` [sales/sl055.cbl:L470] - which is what makes this
    paragraph the body of the OUTER loop. Its trailing source comment reads "Headers
    only".

    Args:
        ctx: The program's state. The invoice header view is read and its `ih-update`
            written; the four special-total pairs are accumulated.

    Returns:
        `_Label.DA010_READ_LOOP` for the three class-1 back-edges at L428, L442 and
            L470, or `_Label.DA030_SKIP_INVOICE` for the two class-4 transfers at L431
            and L436.
    """
    header = ctx.ws_invoice_record.header
    prime = header.ih_prime
    sub = header.ih_sub_prime
    fig = sub.ih_fig

    if _IS_IH_ANALYISED(sub.ih_update) and _IS_APPLIED(sub.ih_status):
        return _Label.DA010_READ_LOOP

    if arithmetic.compare(prime.ih_type, _IH_TYPE_PROFORMA) == 0:
        # 431 go to da030-Skip-Invoice. GO TO class 4 - SITE 1 OF 4.
        return _Label.DA030_SKIP_INVOICE

    if _IS_PENDING(sub.ih_status) or sub.ih_status_l != _IH_STATUS_L_PRINTED:
        ctx.ws_p_flag = int(move.move_numeric(1, _D_WS_P_FLAG))
        return _Label.DA030_SKIP_INVOICE

    _dd000_extract(ctx)

    # 440 if ih-analyised RE-TESTED, because `dd000-Extract` may have set it - no, it
    # sets `ih-status` and `ih-status-A` [sales/sl055.cbl:L679-L680] and leaves `ih-
    # update` alone.
    if _IS_IH_ANALYISED(sub.ih_update):
        ctx.verbs.invoice_rewrite(ctx)
        return _Label.DA010_READ_LOOP


    # 444 add ih-c-vat ih-vat ih-e-vat giving work-2. A THREE-ADDEND VARIADIC `ADD ...
    # GIVING`.
    ctx.work_2 = Decimal(
        arithmetic.add_giving(
            fig.ih_c_vat, fig.ih_vat, fig.ih_e_vat, receiving=_D_WORK_2
        )
    )
    if arithmetic.compare(prime.ih_type, _IH_TYPE_CREDIT_NOTE) == 0:
        ctx.work_2 = Decimal(
            arithmetic.multiply_by(_NEGATE, ctx.work_2, _D_WORK_2)
        )
    if (
        arithmetic.compare(ctx.work_2, 0) != 0
        and arithmetic.compare(prime.ih_type, _IH_TYPE_RECEIPT) != 0
    ):
        ctx.ws_vat_totalt = int(
            arithmetic.add_to(1, receiver_value=ctx.ws_vat_totalt, receiving=_D_WS_VAT_TOTALT)
        )
        ctx.ws_vat_totalv = Decimal(
            arithmetic.add_to(
                ctx.work_2, receiver_value=ctx.ws_vat_totalv, receiving=_D_WS_VAT_TOTALV
            )
        )
    if (
        arithmetic.compare(ctx.work_2, 0) != 0
        and arithmetic.compare(prime.ih_type, _IH_TYPE_RECEIPT) == 0
    ):
        ctx.ws_vatr_totalt = int(
            arithmetic.add_to(
                1, receiver_value=ctx.ws_vatr_totalt, receiving=_D_WS_VATR_TOTALT
            )
        )
        ctx.ws_vatr_totalv = Decimal(
            arithmetic.add_to(
                ctx.work_2, receiver_value=ctx.ws_vatr_totalv, receiving=_D_WS_VATR_TOTALV
            )
        )


    ctx.work_2 = Decimal(
        move.move_numeric(fig.ih_carriage, _D_WORK_2, sending_field=_D_IH_CARRIAGE)
    )
    if arithmetic.compare(prime.ih_type, _IH_TYPE_CREDIT_NOTE) == 0:
        ctx.work_2 = Decimal(
            arithmetic.multiply_by(_NEGATE, ctx.work_2, _D_WORK_2)
        )
    if arithmetic.compare(ctx.work_2, 0) != 0:
        ctx.ws_carr_totalt = int(
            arithmetic.add_to(
                1, receiver_value=ctx.ws_carr_totalt, receiving=_D_WS_CARR_TOTALT
            )
        )
        ctx.ws_carr_totalv = Decimal(
            arithmetic.add_to(
                ctx.work_2, receiver_value=ctx.ws_carr_totalv, receiving=_D_WS_CARR_TOTALV
            )
        )


    # 461 move ih-deduct-amt to work-2. AN UNSIGNED SENDER INTO A SIGNED RECEIVER. `ih-
    # deduct-amt pic 999v99 comp` [copybooks/slwsinv2.cob:L82] cannot hold a negative.
    ctx.work_2 = Decimal(
        move.move_numeric(sub.ih_deduct_amt, _D_WORK_2, sending_field=_D_IH_DEDUCT_AMT)
    )
    if arithmetic.compare(prime.ih_type, _IH_TYPE_CREDIT_NOTE) == 0:
        ctx.work_2 = Decimal(
            arithmetic.multiply_by(_NEGATE, ctx.work_2, _D_WORK_2)
        )
    if arithmetic.compare(ctx.work_2, 0) != 0:
        ctx.ws_disc_totalt = int(
            arithmetic.add_to(
                1, receiver_value=ctx.ws_disc_totalt, receiving=_D_WS_DISC_TOTALT
            )
        )
        ctx.ws_disc_totalv = Decimal(
            arithmetic.add_to(
                ctx.work_2, receiver_value=ctx.ws_disc_totalv, receiving=_D_WS_DISC_TOTALV
            )
        )

    sub.ih_update = _IH_UPDATE_ANALYSED
    ctx.verbs.invoice_rewrite(ctx)
    # 470 go to da010-Read-Loop. GO TO class 1 - THE OUTER LOOP'S PRINCIPAL BACK-EDGE.
    return _Label.DA010_READ_LOOP


def _da030_skip_invoice(ctx: _Sl055Context) -> _Label:
    """`da030-Skip-Invoice.` - reposition past this invoice's remaining items.

    THE CLASS-4 EQUIVALENCE PROOF, for both call sites [sales/sl055.cbl:L431] and
    [sales/sl055.cbl:L436].

    Args:
        ctx: The program's state. The invoice area's key is rewritten and `Access-Type`
            is set.

    Returns:
        `_Label.DA040_CLOSE_FILES` for the class-2 transfer at L478, or
            `_Label.DA010_READ_LOOP` for the class-1 loop-back at L479.
    """
    area = ctx.ws_invoice_record

    area.invoice_nos = int(
        arithmetic.add_to(1, receiver_value=area.invoice_nos, receiving=_D_INVOICE_NOS)
    )
    # 474 move zeros to item-nos. `ZEROS`, one of the figurative constant's three
    # spellings.
    area.item_nos = int(move.move_figurative(move.ZERO, _D_ITEM_NOS))
    # 475 set fn-not-less-than to true. THE ISAM `START` RELATION, SET THROUGH THE
    # ACCESS-TYPE VOCABULARY. `88 fn-not-less-than value 8.`
    # [copybooks/wsfnctn.cob:L115] is declared on `Access-Type`, and `SET ...
    ctx.file_access.access_type = int(AccessType.NOT_LESS_THAN)
    ctx.verbs.invoice_start(ctx)
    if (
        arithmetic.compare(ctx.fs_reply, FsReply.INVALID_KEY_ON_START) == 0
        or arithmetic.compare(ctx.fs_reply, FsReply.KEY_NOT_FOUND) == 0
    ):
        # 478 go to da040-Close-Files.
        return _Label.DA040_CLOSE_FILES
    return _Label.DA010_READ_LOOP


def _da040_close_files(ctx: _Sl055Context) -> _Label:
    """`da040-Close-Files.` - the four special totals, the four closes, the exits.

    "the target label is followed by real work - closing files, printing totals,
    rewriting a control record - so the transformation is `break` PLUS faithful
    placement of that work after the loop, not `break` alone.

    Args:
        ctx: The program's state. The value record's key and totals are set, the four
            files are closed, and the two exit flags are tested.

    Returns:
        `_Label.GOBACK` for either early exit at L509 or L518, or
            `_Label.DA999_MENU_EXIT` for the fall-through into `da999-Menu-Exit.`.
    """
    value = ctx.ws_value_record


    _place_va_code(
        value, move.move_group(_SPECIAL_TOTAL_VAT_CODE, _D_VA_CODE, length=3)
    )
    ctx.work_3 = int(
        move.move_numeric(ctx.ws_vat_totalt, _D_WORK_3, sending_field=_D_WS_VAT_TOTALT)
    )
    ctx.work_2 = Decimal(
        move.move_numeric(ctx.ws_vat_totalv, _D_WORK_2, sending_field=_D_WS_VAT_TOTALV)
    )
    _dc000_store_specials(ctx)


    _place_va_group(
        value, move.move_group(_SPECIAL_TOTAL_VATR_GROUP, _D_VA_GROUP, length=2)
    )
    ctx.work_3 = int(
        move.move_numeric(ctx.ws_vatr_totalt, _D_WORK_3, sending_field=_D_WS_VATR_TOTALT)
    )
    ctx.work_2 = Decimal(
        move.move_numeric(ctx.ws_vatr_totalv, _D_WORK_2, sending_field=_D_WS_VATR_TOTALV)
    )
    _dc000_store_specials(ctx)


    _place_va_group(
        value, move.move_group(_SPECIAL_TOTAL_CARRIAGE_GROUP, _D_VA_GROUP, length=2)
    )
    ctx.work_3 = int(
        move.move_numeric(ctx.ws_carr_totalt, _D_WORK_3, sending_field=_D_WS_CARR_TOTALT)
    )
    ctx.work_2 = Decimal(
        move.move_numeric(ctx.ws_carr_totalv, _D_WORK_2, sending_field=_D_WS_CARR_TOTALV)
    )
    _dc000_store_specials(ctx)


    _place_va_group(
        value, move.move_group(_SPECIAL_TOTAL_DISCOUNT_GROUP, _D_VA_GROUP, length=2)
    )
    ctx.work_3 = int(
        move.move_numeric(ctx.ws_disc_totalt, _D_WORK_3, sending_field=_D_WS_DISC_TOTALT)
    )
    ctx.work_2 = Decimal(
        move.move_numeric(ctx.ws_disc_totalv, _D_WORK_2, sending_field=_D_WS_DISC_TOTALV)
    )
    _dc000_store_specials(ctx)


    ctx.verbs.invoice_close(ctx)
    ctx.verbs.value_close(ctx)
    ctx.verbs.analysis_close(ctx)
    ctx.open_item_file_2.close(ctx.file_access)


    if arithmetic.compare(ctx.ws_p_flag, 0) != 0:
        _LOG.warning(_SL122)
        # 505 if WS-Caller not = "xl150" THE CODEBASE'S OWN UNATTENDED-MODE CHECK.
        # `xl150` is the end-of-cycle driver, out of scope per section 0.2.2.
        if ctx.ws_calling_data.ws_caller != _XL150:
            # 506  display SL002        at line ws-lines    col 1
            # 507  accept  ws-reply     at line ws-lines    col 33
            #
            # BOTH OMITTED. `SL002` is "SL002 Note error and hit return"
            # [sales/sl055.cbl:L250] - the whole literal is the instruction to
            # press a key, and its `accept` on the next line is the key press.
            # Section 0.3.4 drops a prompt whose only effect is to block a
            # terminal; a headless run has no operator to instruct, and the
            # substantive diagnostic is the `SL122` record above. The BRANCH
            # itself survives - it is the codebase's own unattended-mode test
            # and evidence that headless operation was designed for.
            pass
        # 509  goback.               *> Yep, I know but just in case extra code goes here!
        #
        # The maintainer's own comment, kept: he is noting that the `goback` is
        # redundant here because the next paragraph is `da999-Menu-Exit.`, and
        # that he wrote it anyway to leave room.
        #
        # ANOMALY [sales/sl055.cbl:L503-L509] - THIS PATH RETURNS WITHOUT SETTING
        # `WS-Term-Code`. It stays at whatever the caller passed, which for a
        # normal dispatch is zero - so `sales/sales.cbl`'s gate
        # `if ws-term-code not = zero` [sales/sales.cbl:L765] PASSES and `sl060`
        # runs anyway, even though this program has just reported that unprinted
        # invoices exist and abandoned its own run part-way. The
        # `move 8 to WS-Term-Code` [sales/sl055.cbl:L344] that the missing-file
        # path performs is exactly what this path lacks.
        # Reproduced deliberately per R-4; DO NOT FIX. A `move` added here would
        # suppress `sl060` and change which tables the cycle writes.
        return _Label.GOBACK

    if arithmetic.compare(ctx.ws_anal_flag, 0) != 0:
        _LOG.warning(_SL123)
        _LOG.warning(_SL126)
        if ctx.ws_calling_data.ws_caller != _XL150:
            # 515  display SL002 at 1601 with foreground-color 2
            # 516  accept ws-reply at 1633
            #
            # BOTH OMITTED, exactly as at [sales/sl055.cbl:L506-L507] above: the
            # literal IS the key-press instruction and the `accept` IS the key
            # press. The substantive diagnostics are the `SL123` and `SL126`
            # records above. The BRANCH survives.
            pass
        # 518  goback.   *> Yep, I know but just in case extra code goes here!
        #
        # The same missing `WS-Term-Code` as L509, and with the same consequence.
        # Reproduced deliberately per R-4; DO NOT FIX.
        return _Label.GOBACK

    # FALL-THROUGH 2 OF 2 [sales/sl055.cbl:L518 -> sales/sl055.cbl:L520] With neither
    # flag set there is no transfer statement at the bottom of `da040-Close-Files.`, so
    # control falls into `da999-Menu-Exit.` and its `goback.`.
    return _Label.DA999_MENU_EXIT


def _da999_menu_exit() -> None:
    """`da999-Menu-Exit.` - the normal end of the program.

    `GOBACK` returns to the caller - `sales/sales.cbl`'s `load000.`
    [sales/sales.cbl:L698], which then tests `WS-Term-Code`. Reached only by fall-
    through from `da040-Close-Files.`; nothing transfers to it.
    """
    return None


def _group_move_analysis_record_to_value_record(ctx: _Sl055Context) -> None:
    """`move WS-Analysis-Record to WS-Value-Record` - the byte-image copy alone.

    Live at [sales/sl055.cbl:L538], [sales/sl055.cbl:L556] and [sales/sl055.cbl:L568],
    and at every one of those three sites the very next statement zeroes the six totals.
    This helper performs ONLY the move.

    Args:
        ctx: The program's state. `WS-Value-Record`'s first four fields are overwritten
            from `WS-Analysis-Record`; its six totals are left for the caller's next
            statement to zero.
    """
    analysis = ctx.ws_analysis_record
    value = ctx.ws_value_record

    # The thirty-six-byte span, copied field-for-field because the two layouts are
    # picture-identical across it.
    _place_va_code(
        value,
        move.move_group(
            _three_byte_group_image(
                analysis.ws_pa_code.pa_system,
                analysis.ws_pa_code.pa_group.pa_first,
                analysis.ws_pa_code.pa_group.pa_second,
            ),
            _D_VA_CODE,
            length=3,
        ),
    )
    value.va_gl = int(
        move.move_numeric(analysis.pa_gl, _D_VA_GL, sending_field=_D_PA_GL)
    )
    value.va_desc = move.move_alphanumeric(
        analysis.pa_desc, _D_VA_DESC, sending_field=_D_PA_DESC
    )
    value.va_print = move.move_alphanumeric(
        analysis.pa_print, _D_VA_PRINT, sending_field=_D_PA_PRINT
    )


def _move_va_code_to_ws_pa_code(ctx: _Sl055Context) -> None:
    """`move va-code to WS-PA-Code.` - the key handed from value to analysis.

    Live at [sales/sl055.cbl:L531], [sales/sl055.cbl:L548] and [sales/sl055.cbl:L575].
    Both operands are three-byte group items whose three children are `pic x` apiece, so
    the move is a straight three-byte copy with no padding and no truncation.

    Args:
        ctx: The program's state. `WS-PA-Code`'s three children are overwritten from
            `va-code`'s.
    """
    value = ctx.ws_value_record
    _place_pa_code(
        ctx.ws_analysis_record,
        move.move_group(
            _three_byte_group_image(
                value.va_code.va_system,
                value.va_code.va_group.va_first,
                value.va_code.va_group.va_second,
            ),
            _D_WS_PA_CODE,
            length=3,
        ),
    )


def _db000_create(ctx: _Sl055Context) -> None:
    """`db000-Create section.` - find the analysis record, or invent one.

    THE SECTION, AS A WHOLE. Performed from two places - [sales/sl055.cbl:L385] inside
    the item loop and [sales/sl055.cbl:L598] inside `dc000-Store-Specials` - both times
    because a `Value-Read-Indexed` found no row for the key.

    Args:
        ctx: The program's state. `WS-Value-Record` is seeded from `WS-Analysis-Record`;
            `save-code`, `ws-Anal-Flag` and `File-Key-No` are written; `ANALYSIS-REC`
            rows may be created and a `VALUEANAL-REC` row may be written.
    """
    while True:
        label = _db000_create_main(ctx)
        if label is _Label.DB999_MAIN_EXIT:
            _db999_main_exit()
            return
        # GO TO class 4 - SITE 3 OF 4 [sales/sl055.cbl:L536]. The named call, then the
        # explicit transfer on what `db010-Create-Anal` itself decides.
        _db010_create_anal(ctx)
        continue


def _db000_create_main(ctx: _Sl055Context) -> _Label:
    """`DB000-Create-Main.` - seed the value record from the analysis record.

    Declared in MIXED CASE at [sales/sl055.cbl:L530] and spelled entirely in lower case
    by the `GO TO` that targets it at [sales/sl055.cbl:L585]. COBOL folds case in user-
    defined words, so the two spell one label.

    Args:
        ctx: The program's state.

    Returns:
        `_Label.DB010_CREATE_ANAL` for the class-4 transfer at L536, or
            `_Label.DB999_MAIN_EXIT` for the class-3 transfers at L543, L554, L566 and
            L572.
    """
    value = ctx.ws_value_record
    analysis = ctx.ws_analysis_record


    _move_va_code_to_ws_pa_code(ctx)
    ctx.file_access.logging_data.file_key_no = int(
        move.move_numeric(1, _D_FILE_KEY_NO)
    )
    ctx.verbs.analysis_read_indexed(ctx)
    if (
        arithmetic.compare(ctx.fs_reply, FsReply.INVALID_KEY_ON_START) == 0
        or arithmetic.compare(ctx.fs_reply, FsReply.KEY_NOT_FOUND) == 0
    ):
        return _Label.DB010_CREATE_ANAL

    _group_move_analysis_record_to_value_record(ctx)
    (
        value.va_t_this,
        value.va_t_last,
        value.va_t_year,
        value.va_v_this,
        value.va_v_last,
        value.va_v_year,
    ) = move.move_to_all(move.ZERO, _VALUE_TOTALS_CLEARED_BY_DB000)

    if value.va_code.va_group.va_second == _VA_SECOND_SPACE:
        # 543 go to db999-Main-Exit. GO TO class 3 - the key IS the group-level key, so
        # passes 2 and 3 would re-read the same record.
        return _Label.DB999_MAIN_EXIT


    # 545 move va-code to save-code. `save-code pic xxx` [sales/sl055.cbl:L202] holds
    # the SPECIFIC key across the group-level read, so that pass 3 can restore it.
    ctx.save_code = move.move_group(
        _three_byte_group_image(
            value.va_code.va_system,
            value.va_code.va_group.va_first,
            value.va_code.va_group.va_second,
        ),
        _D_SAVE_CODE,
        length=3,
    )
    value.va_code.va_group.va_second = str(
        move.move_figurative(move.SPACE, _D_VA_SECOND)
    )
    _move_va_code_to_ws_pa_code(ctx)
    ctx.file_access.logging_data.file_key_no = int(
        move.move_numeric(1, _D_FILE_KEY_NO)
    )
    ctx.verbs.analysis_read_indexed(ctx)
    if arithmetic.compare(ctx.fs_reply, FsReply.INVALID_KEY_ON_START) == 0:
        # 553 move save-code to WS-PA-Code The analysis key is restored, but `va-code`
        # is NOT - it is left with `va-second` blanked from L547.
        _place_pa_code(
            analysis, move.move_group(ctx.save_code, _D_WS_PA_CODE, length=3)
        )
        return _Label.DB999_MAIN_EXIT

    _group_move_analysis_record_to_value_record(ctx)
    (
        value.va_t_this,
        value.va_t_last,
        value.va_t_year,
        value.va_v_this,
        value.va_v_last,
        value.va_v_year,
    ) = move.move_to_all(move.ZERO, _VALUE_TOTALS_CLEARED_BY_DB000)

    ctx.verbs.value_write(ctx)


    va_code_image, pa_code_image = move.move_to_all(
        ctx.save_code, (_D_VA_CODE, _D_WS_PA_CODE)
    )
    _place_va_code(value, str(va_code_image))
    _place_pa_code(analysis, str(pa_code_image))
    ctx.file_access.logging_data.file_key_no = int(
        move.move_numeric(1, _D_FILE_KEY_NO)
    )
    ctx.verbs.analysis_read_indexed(ctx)
    # 565 if FS-Reply = 21 ONLY 21, again. And note what it means.
    if arithmetic.compare(ctx.fs_reply, FsReply.INVALID_KEY_ON_START) == 0:
        return _Label.DB999_MAIN_EXIT

    _group_move_analysis_record_to_value_record(ctx)
    (
        value.va_t_this,
        value.va_t_last,
        value.va_t_year,
        value.va_v_this,
        value.va_v_last,
        value.va_v_year,
    ) = move.move_to_all(move.ZERO, _VALUE_TOTALS_CLEARED_BY_DB000)

    # 572 go to db999-Main-Exit.
    return _Label.DB999_MAIN_EXIT


def _db010_create_anal(ctx: _Sl055Context) -> _Label:
    """`db010-Create-Anal.` - invent the missing analysis record, then retry.

    TWO ROWS MAY BE WRITTEN, NOT ONE. The specific code is written first; then, if the
    code has a second character, `pa-second` is blanked and the SAME record is written
    AGAIN under the group-level key.

    Args:
        ctx: The program's state. `WS-Analysis-Record` is overwritten, one or two
            `ANALYSIS-REC` rows are written, and `ws-Anal-Flag` is set.

    Returns:
        `_Label.DB000_CREATE_MAIN` always - the unconditional class-4 back-edge at L585.
    """
    analysis = ctx.ws_analysis_record

    _move_va_code_to_ws_pa_code(ctx)
    analysis.pa_gl = int(move.move_figurative(move.ZERO, _D_PA_GL))
    analysis.pa_print = str(move.move_figurative(move.SPACE, _D_PA_PRINT))
    analysis.pa_desc = move.move_alphanumeric(_EMERGENCY_NAME, _D_PA_DESC)
    ctx.file_access.logging_data.file_key_no = int(
        move.move_numeric(1, _D_FILE_KEY_NO)
    )
    ctx.verbs.analysis_write(ctx)
    if analysis.ws_pa_code.pa_group.pa_second != _PA_SECOND_SPACE:
        analysis.ws_pa_code.pa_group.pa_second = str(
            move.move_figurative(move.SPACE, _D_PA_SECOND)
        )
        ctx.verbs.analysis_write(ctx)
    ctx.ws_anal_flag = int(move.move_numeric(1, _D_WS_ANAL_FLAG))
    # 585 go to db000-Create-Main. GO TO class 4 - SITE 4 OF 4, and the only BACKWARD
    # transfer in the program. Proof in `_db000_create`'s docstring.
    return _Label.DB000_CREATE_MAIN


def _db999_main_exit() -> None:
    """`db999-Main-Exit.` - `exit section.` [sales/sl055.cbl:L588].

    The class-3 target of [sales/sl055.cbl:L543], [sales/sl055.cbl:L554],
    [sales/sl055.cbl:L566] and [sales/sl055.cbl:L572]. `EXIT SECTION` returns to
    whichever `PERFORM db000-Create` entered the section - [sales/sl055.cbl:L385] or
    [sales/sl055.cbl:L598].
    """
    return None


def _dc000_store_specials(ctx: _Sl055Context) -> None:
    """`dc000-Store-Specials section.` - add one special total into the value file.

    THE SECTION HEAD CARRIES THE BODY. There is no paragraph label between `dc000-Store-
    Specials section.` [sales/sl055.cbl:L590] and its first statement at
    [sales/sl055.cbl:L593], so the statements belong to the SECTION itself and only the
    exit is a separate paragraph.

    Args:
        ctx: The program's state. `v-exists` and `File-Key-No` are written, and one or
            two `VALUEANAL-REC` rows are written or rewritten.
    """
    value = ctx.ws_value_record

    ctx.v_exists = int(move.move_numeric(1, _D_V_EXISTS))

    ctx.file_access.logging_data.file_key_no = int(
        move.move_numeric(1, _D_FILE_KEY_NO)
    )
    ctx.verbs.value_read_indexed(ctx)
    if arithmetic.compare(ctx.fs_reply, FsReply.INVALID_KEY_ON_START) == 0:
        # 598 perform db000-Create The second of the section's two call sites.
        _db000_create(ctx)
        ctx.v_exists = int(move.move_figurative(move.ZERO, _D_V_EXISTS))


    value.va_t_this = int(
        arithmetic.add_to(
            ctx.work_3, receiver_value=value.va_t_this, receiving=_D_VA_T_THIS
        )
    )
    value.va_t_year = int(
        arithmetic.add_to(
            ctx.work_3, receiver_value=value.va_t_year, receiving=_D_VA_T_YEAR
        )
    )
    value.va_v_this = Decimal(
        arithmetic.add_to(
            ctx.work_2, receiver_value=value.va_v_this, receiving=_D_VA_V_THIS
        )
    )
    value.va_v_year = Decimal(
        arithmetic.add_to(
            ctx.work_2, receiver_value=value.va_v_year, receiving=_D_VA_V_YEAR
        )
    )

    if arithmetic.compare(ctx.v_exists, 0) == 0:
        ctx.verbs.value_write(ctx)
    else:
        ctx.verbs.value_rewrite(ctx)


    # 611 move space to va-second.
    value.va_code.va_group.va_second = str(
        move.move_figurative(move.SPACE, _D_VA_SECOND)
    )
    ctx.file_access.logging_data.file_key_no = int(
        move.move_numeric(1, _D_FILE_KEY_NO)
    )
    ctx.verbs.value_read_indexed(ctx)
    # 614 if FS-Reply = 21 ONLY 21 again - and note the asymmetry with the block above.
    if arithmetic.compare(ctx.fs_reply, FsReply.INVALID_KEY_ON_START) == 0:
        _dc999_main_exit()
        return

    # 617 add work-3 to VA-T-This. THE SAME FOUR ADDS, DELIBERATELY DUPLICATED. See the
    # docstring.
    value.va_t_this = int(
        arithmetic.add_to(
            ctx.work_3, receiver_value=value.va_t_this, receiving=_D_VA_T_THIS
        )
    )
    value.va_t_year = int(
        arithmetic.add_to(
            ctx.work_3, receiver_value=value.va_t_year, receiving=_D_VA_T_YEAR
        )
    )
    value.va_v_this = Decimal(
        arithmetic.add_to(
            ctx.work_2, receiver_value=value.va_v_this, receiving=_D_VA_V_THIS
        )
    )
    value.va_v_year = Decimal(
        arithmetic.add_to(
            ctx.work_2, receiver_value=value.va_v_year, receiving=_D_VA_V_YEAR
        )
    )
    # 621 perform Value-Rewrite.
    ctx.verbs.value_rewrite(ctx)

    _dc999_main_exit()


def _dc999_main_exit() -> None:
    """`dc999-Main-Exit.` - `exit section.` [sales/sl055.cbl:L624]."""
    return None


def _dd000_extract(ctx: _Sl055Context) -> None:
    """`dd000-Extract section.` - build one OTM2 row and the period totals.

    Four names against nine, and the four are a SUBSET of the nine - so the purchase
    extract leaves the two deduction fields, the extra, the VAT-on-extra and the
    discount POSITIVE on a credit note where the sales extract makes them negative.

    Args:
        ctx: The program's state. `oi-header` is rebuilt and appended to the OTM2
            sequence.
    """
    header = ctx.ws_invoice_record.header
    prime = header.ih_prime
    sub = header.ih_sub_prime
    fig = sub.ih_fig
    totals = ctx.system_record_4.sales_ledger_data

    # 632 if applied `applied` [copybooks/slwsinv2.cob:L74] is a condition name on `ih-
    # status`, value "Z" - the header has already been extracted by an earlier run, so
    # extracting it again would duplicate the OTM2 row and double the period total.
    if _IS_APPLIED(sub.ih_status):
        _dd999_main_ex()
        return

    # 635 initialize oi-header with filler. Every elementary item to its category
    # default, FILLER included - which here means twenty-three of the twenty-eight
    # leaves.
    ctx.oi_header = _initialize_oi_header_with_filler()
    oi = ctx.oi_header
    oi_key = oi.oi_key
    oi_filler = oi.filler_1
    oi_money = oi_filler.filler_2

    oi_money.oi_p_c = Decimal(
        move.move_numeric(fig.ih_p_c, _D_OI_P_C, sending_field=_D_IH_P_C)
    )
    oi_key.oi_invoice = int(
        move.move_numeric(prime.ih_invoice, _D_OI_INVOICE, sending_field=_D_IH_INVOICE)
    )
    # 638 move ih-customer to oi-customer.
    oi_key.oi_customer.oi_nos = move.move_alphanumeric(
        prime.ih_customer.ih_nos, _D_OI_NOS
    )
    oi_key.oi_customer.oi_check = int(
        move.move_numeric(prime.ih_customer.ih_check, _D_OI_CHECK)
    )
    oi_filler.oi_date = int(
        move.move_numeric(prime.ih_date, _D_OI_DATE, sending_field=_D_IH_DATE)
    )
    (
        oi_filler.oi_batch.oi_b_nos,
        oi_filler.oi_batch.oi_b_item,
    ) = (
        int(value)
        for value in move.move_to_all(move.ZERO, (_D_OI_B_NOS, _D_OI_B_ITEM))
    )
    oi_filler.oi_description = move.move_alphanumeric(
        prime.ih_order, _D_OI_DESCRIPTION, sending_field=_D_IH_ORDER
    )
    # 642 move ih-net to oi-net. `OI-Approp redefines OI-Net`
    # [copybooks/slwsoi.cob:L38-L39], so the two attribute names are ONE storage
    # location and must never diverge.
    oi_money.oi_net = Decimal(
        move.move_numeric(fig.ih_net, _D_OI_NET, sending_field=_D_IH_NET)
    )
    oi_money.oi_approp = oi_money.oi_net
    oi_money.oi_extra = Decimal(
        move.move_numeric(fig.ih_extra, _D_OI_EXTRA, sending_field=_D_IH_EXTRA)
    )
    oi_money.oi_carriage = Decimal(
        move.move_numeric(fig.ih_carriage, _D_OI_CARRIAGE, sending_field=_D_IH_CARRIAGE)
    )
    oi_money.oi_vat = Decimal(
        move.move_numeric(fig.ih_vat, _D_OI_VAT, sending_field=_D_IH_VAT)
    )
    oi_money.oi_c_vat = Decimal(
        move.move_numeric(fig.ih_c_vat, _D_OI_C_VAT, sending_field=_D_IH_C_VAT)
    )
    oi_money.oi_e_vat = Decimal(
        move.move_numeric(fig.ih_e_vat, _D_OI_E_VAT, sending_field=_D_IH_E_VAT)
    )
    oi_money.oi_discount = Decimal(
        move.move_numeric(fig.ih_discount, _D_OI_DISCOUNT, sending_field=_D_IH_DISCOUNT)
    )
    oi_money.oi_paid = Decimal(move.move_figurative(move.ZERO, _D_OI_PAID))
    # 650 move ih-deduct-amt to oi-deduct-amt. AN UNSIGNED SENDER INTO A SIGNED
    # RECEIVER.
    oi_filler.oi_deduct_amt = Decimal(
        move.move_numeric(
            sub.ih_deduct_amt, _D_OI_DEDUCT_AMT, sending_field=_D_IH_DEDUCT_AMT
        )
    )
    oi_filler.oi_deduct_vat = Decimal(
        move.move_numeric(
            sub.ih_deduct_vat, _D_OI_DEDUCT_VAT, sending_field=_D_IH_DEDUCT_VAT
        )
    )
    oi_filler.oi_deduct_days = int(
        move.move_numeric(
            sub.ih_deduct_days, _D_OI_DEDUCT_DAYS, sending_field=_D_IH_DEDUCT_DAYS
        )
    )
    # 653 move zero to oi-status oi-date-cleared oi-days. *> hmm, initialised, not
    # needed but acts as a note ONE statement, THREE receivers.
    (
        oi_filler.oi_status,
        oi_filler.oi_date_cleared,
        oi_filler.oi_days,
    ) = (
        int(value)
        for value in move.move_to_all(
            move.ZERO, (_D_OI_STATUS, _D_OI_DATE_CLEARED, _D_OI_DAYS)
        )
    )
    oi_filler.oi_type = int(
        move.move_numeric(prime.ih_type, _D_OI_TYPE, sending_field=_D_IH_TYPE)
    )
    (
        oi_filler.oi_applied,
        oi_filler.oi_unapl,
        oi_filler.oi_hold_flag,
    ) = (
        str(value)
        for value in move.move_to_all(
            move.SPACE, (_D_OI_APPLIED, _D_OI_UNAPL, _D_OI_HOLD_FLAG)
        )
    )

    # ANOMALY [sales/sl055.cbl:L657-L666] vs [purchase/pl055.cbl:L572-L575] - NINE
    # fields here, FOUR in the purchase counterpart, and the four are a subset of the
    # nine.

    if arithmetic.compare(prime.ih_type, _IH_TYPE_CREDIT_NOTE) == 0:
        # 658 multiply -1 by oi-deduct-amt `MULTIPLY -1 BY x` with NO `GIVING`: the
        # receiver is the SECOND operand.
        oi_filler.oi_deduct_amt = Decimal(
            arithmetic.multiply_by(
                _NEGATE, oi_filler.oi_deduct_amt, _D_OI_DEDUCT_AMT
            )
        )
        oi_filler.oi_deduct_vat = Decimal(
            arithmetic.multiply_by(
                _NEGATE, oi_filler.oi_deduct_vat, _D_OI_DEDUCT_VAT
            )
        )
        oi_money.oi_net = Decimal(
            arithmetic.multiply_by(_NEGATE, oi_money.oi_net, _D_OI_NET)
        )
        oi_money.oi_approp = oi_money.oi_net
        oi_money.oi_extra = Decimal(
            arithmetic.multiply_by(_NEGATE, oi_money.oi_extra, _D_OI_EXTRA)
        )
        oi_money.oi_carriage = Decimal(
            arithmetic.multiply_by(_NEGATE, oi_money.oi_carriage, _D_OI_CARRIAGE)
        )
        oi_money.oi_vat = Decimal(
            arithmetic.multiply_by(_NEGATE, oi_money.oi_vat, _D_OI_VAT)
        )
        oi_money.oi_c_vat = Decimal(
            arithmetic.multiply_by(_NEGATE, oi_money.oi_c_vat, _D_OI_C_VAT)
        )
        oi_money.oi_e_vat = Decimal(
            arithmetic.multiply_by(_NEGATE, oi_money.oi_e_vat, _D_OI_E_VAT)
        )
        oi_money.oi_discount = Decimal(
            arithmetic.multiply_by(_NEGATE, oi_money.oi_discount, _D_OI_DISCOUNT)
        )

    # 668 move ih-cr to oi-cr. AFTER the negation block, not before, and outside it - so
    # the credit-terms flag is carried across unflipped for every type.
    oi_filler.oi_cr = int(
        move.move_numeric(sub.ih_cr, _D_OI_CR, sending_field=_D_IH_CR)
    )


    if arithmetic.compare(prime.ih_type, _IH_TYPE_RECEIPT) != 0:
        # 671 add ih-net ih-extra ih-carriage ih-discount ih-vat 672 ih-c-vat ih-e-vat
        # ih-deduct-amt ih-deduct-vat 673 giving ws-inv-amt.
        ctx.ws_inv_amt = Decimal(
            arithmetic.add_giving(
                fig.ih_net,
                fig.ih_extra,
                fig.ih_carriage,
                fig.ih_discount,
                fig.ih_vat,
                fig.ih_c_vat,
                fig.ih_e_vat,
                sub.ih_deduct_amt,
                sub.ih_deduct_vat,
                receiving=_D_WS_INV_AMT,
            )
        )
    if arithmetic.compare(prime.ih_type, _IH_TYPE_INVOICE) == 0:
        # 675 add ws-inv-amt to sl-invoices-this-month. PERIOD TOTAL 1 OF 2, and site 1
        # of the nine in section 0.6.4.
        totals.sl_invoices_this_month = Decimal(
            arithmetic.add_to(
                ctx.ws_inv_amt,
                receiver_value=totals.sl_invoices_this_month,
                receiving=_D_SL_INVOICES_THIS_MONTH,
            )
        )
    if arithmetic.compare(prime.ih_type, _IH_TYPE_CREDIT_NOTE) == 0:
        totals.sl_credit_notes_this_month = Decimal(
            arithmetic.add_to(
                ctx.ws_inv_amt,
                receiver_value=totals.sl_credit_notes_this_month,
                receiving=_D_SL_CREDIT_NOTES_THIS_MONTH,
            )
        )


    sub.ih_status = _IH_STATUS_APPLIED
    sub.ih_status_a = _IH_STATUS_A_APPLIED
    ctx.open_item_file_2.write(ctx.oi_header, ctx.file_access)
    if arithmetic.compare(ctx.fs_reply, FsReply.SUCCESS) != 0:
        _a01_eval_status(ctx)
        _LOG.error("%s%s %s", _SL121, ctx.fs_reply, ctx.exception_msg)
        # 687  display  SL002         at line ws-lines col 01
        # 688  accept   ws-reply      at line ws-lines col 33
        #
        # BOTH OMITTED - the key-press instruction and the key press. The
        # substantive diagnostic is the record above.
        #
        # ANOMALY [sales/sl055.cbl:L682-L689] - THIS PATH PERFORMS NO CONTROL
        # TRANSFER. There is no `go to`, no retry, no abort and no flag: the section
        # simply ends, the caller stamps `ih-update` and rewrites the invoice as
        # ANALYSED, and the run continues with the OTM2 sequence one record short.
        # The invoice is therefore marked extracted while its open item does not
        # exist, and `sl060` will never see it. A rejection with a PARTIAL database
        # effect, in section 0.6.5's terms.
        # Reproduced deliberately per R-4; DO NOT FIX - no retry and no abort have
        # been added.
        #
        # AMBIGUITY Q-52 [sales/sl055.cbl:L682-L689] - the disposition of a failed
        # OTM2 write. Only the oracle can establish whether the sequential write can
        # fail at all once the file is open, and if it can, what the caller's
        # subsequent `Invoice-Rewrite` leaves in `SAINVOICE-REC`.
        # 689  end-if.

    _dd999_main_ex()


def _dd999_main_ex() -> None:
    """`dd999-Main-Ex.` - `exit section.` [sales/sl055.cbl:L692]."""
    return None


def _zz070_convert_date(ctx: _Sl055Context) -> None:
    """`zz070-Convert-Date section.` - render the run date in the configured form.

    `Date-Form` [copybooks/wssystem.cob:L128] is a persisted column, not working
    storage, so defaulting it to 1 (UK) is a DIFF-VISIBLE side effect of merely
    formatting a date - and the caller's `overrewrite.` in `sales/sales.cbl` is what
    commits it.

    Args:
        ctx: The program's state. `ctx.date_formats.ws_date` receives the rendered date
            and `System-Record.Date-Form` may be defaulted from zero to 1.
    """
    # 702 move to-day to ws-date. 704 if Date-Form = zero 705 move 1 to Date-Form. 706
    # if Date-UK 707 go to zz070-Exit.
    effective_date_form = dates.zz070_convert_date(
        ctx.date_formats,
        ctx.to_day,
        ctx.system_record.system_data_block.date_form,
    )
    # The write-back of L705's default. Routed through `cobol.move` rather than
    # assigned, so the receiver's own `pic 9` governs the store.
    ctx.system_record.system_data_block.date_form = int(
        move.move_numeric(effective_date_form, _D_DATE_FORM)
    )


def _zz070_exit() -> None:
    """`zz070-Exit.` - `exit section.` [sales/sl055.cbl:L722]."""
    return None


#: `copy "FileStat-Msgs.cpy" replacing STATUS by fs-reply msg by exception-msg.`
#: [sales/sl055.cbl:L726-L727], expanded.
_FILE_STATUS_MESSAGES: Final[Mapping[int, str]] = MappingProxyType(
    {
        0: "Success                  ",
        2: "Success Duplicate        ",
        4: "Success Incomplete       ",
        5: "Success Optional, Missing",
        6: "Multiple Records LS      ",
        7: "Success No Unit          ",
        9: "Success LS Bad Data      ",
        10: "End Of File              ",
        14: "Out Of Key Range         ",
        21: "Key Invalid              ",
        22: "Key Exists               ",
        23: "Key Not Exists           ",
        24: "Key Boundary violation   ",
        30: "Permanent Error          ",
        31: "Inconsistent Filename    ",
        34: "Boundary Violation       ",
        35: "File Not Found           ",
        37: "Permission Denied        ",
        38: "Closed With Lock         ",
        39: "Conflict Attribute       ",
        41: "Already Open             ",
        42: "Not Open                 ",
        43: "Read Not Done            ",
        44: "Record Overflow          ",
        46: "Read Error               ",
        47: "Input Denied             ",
        48: "Output Denied            ",
        49: "I/O Denied               ",
        51: "Record Locked            ",
        52: "End-Of-Page              ",
        57: "I/O Linage               ",
        61: "File Sharing Failure     ",
        71: "Bad Character LS         ",
        91: "Feature Not Available    ",
    }
)

_FILE_STATUS_UNKNOWN: Final[str] = "Unknown File Status      "


def _a01_eval_status(ctx: _Sl055Context) -> None:
    """`a01-Eval-Status section.` - turn `fs-reply` into readable text.

    DIAGNOSTIC ONLY. It writes nothing but `exception-msg`, a working-storage field, and
    it is performed from exactly one place - the failed OTM2 write at
    [sales/sl055.cbl:L683].

    Args:
        ctx: The program's state. `exception-msg` is overwritten from `fs-reply`.
    """
    ctx.exception_msg = str(move.move_figurative(move.SPACE, _D_EXCEPTION_MSG))
    ctx.exception_msg = move.move_alphanumeric(
        _FILE_STATUS_MESSAGES.get(ctx.fs_reply, _FILE_STATUS_UNKNOWN),
        _D_EXCEPTION_MSG,
    )
    _a01_exit()


def _a01_exit() -> None:
    """`a01-exit.` - `exit section.` [sales/sl055.cbl:L729].

    Declared on the SAME SOURCE LINE as its `exit section.`, which is why section
    0.4.2's inventory misses it - it is `a01-exit. exit section.`, one line rather than
    two. Reached only by fall-through; nothing transfers to it.
    """
    return None


def run(
    ws_calling_data: WsCallingData,
    system_record: SystemRecord,
    system_record_4: SystemRecord4,
    to_day: str,
    file_defs: FileDefs,
    *,
    facade: _FacadeVerbs | None = None,
    open_item_file_2: OpenItemWorkFile[OiHeader] | None = None,
) -> OpenItemWorkFile[OiHeader]:
    """Run `sl055` - the Sales Invoice Post Extract and analysis-total build.

    `da000-mainline` falls through into `da010-Read-Loop`, whose inline `perform until
    FS-Reply = 10` is the ITEM-level loop over invoice LINES.

    Args:
        ws_calling_data: `01 WS-Calling-Data.` [copybooks/wscall.cob:L6] - `WS-Called`,
            `WS-Caller`, `WS-Del-Link`, `WS-Term-Code`, `WS-Process-Func`, `WS-Sub-
            Function` and `WS-CD-Args`.
        system_record: `01 System-Record.` [copybooks/wssystem.cob] - read for `File-
            System-Used` (the `FS-Cobol-Files-Used` gate) and MUTATED at `Date-Form`
            when `zz070-Convert-Date` defaults it.
        system_record_4: `01 System-Record-4.` [copybooks/wssys4.cob] - `SYSTOT-REC`.
            `sl-invoices-this-month` and `sl-credit-notes-this-month` are accumulated in
            `dd000-Extract`.
        to_day: `01 to-day pic x(10).` [sales/sl055.cbl:L264] - the run date, in
            DD/MM/CCYY. THE PROGRAM'S ONLY SOURCE OF THE DATE; it contains no clock
            read of any kind, so pinning this argument pins the run (rule R-6).
        file_defs: `01 File-Defs.` [copybooks/wsnames.cob] - the file and
            work-file names the facade opens by.
        facade: The entity-named data-access facade -
            `copy "Proc-ACAS-FH-Calls.cob".` [sales/sl055.cbl:L731]. Defaults to
            `acas_posting.dal.facade`, imported at this moment rather than at
            module import so that the arithmetic parity suite can exercise the
            program with no data-access layer present. A COBOL `CALL` resolves its
            target when it executes, which is the same timing.
        open_item_file_2: The OTM2 extract file
            [copybooks/seloi2.cob], [copybooks/fdoi2.cob]. Defaults to a fresh
            `workfiles.OpenItemWorkFile` under the name `file-18` assigns, which
            is what a caller driving this program alone wants. THE HANDOFF TO
            `sl060` NEEDS THE CALLER: the route creates one carrier and passes
            the same object to both programs, so `sl060` walks exactly what this
            program appended. On the first run of a given name the file does not
            yet exist, so the `open extend` at [sales/sl055.cbl:L359] fails and the
            `open output` fallback at [sales/sl055.cbl:L362] creates it - the
            compiled program's own first-run path. Passing an explicit object is
            supported for tests that want an isolated file.

    Raises:
        CobolFileSystemPathUnavailable: `System-Record.File-System-Used` selects
            the indexed-file configuration, in which [sales/sl055.cbl:L326-L348]
            calls `sl070` and `CBL_CHECK_FILE_EXIST`. Neither is reachable - the
            first is out of scope per section 0.2.2 and rule R-1 forbids invoking
            COBOL at runtime - and the branch is unreachable in the RDBMS
            configuration this migration targets.
        ModuleNotFoundError: `facade` was not supplied and
            `acas_posting.dal.facade` is not yet on the import path.

    Returns:
        The OTM2 work file this program wrote - the one it was given, or the one
        it declared when given None. RETURNED because it is the handoff: in COBOL
        the file survives the run unit and `sl060` reaches it by naming the same
        `assign file-18`, so the migrated equivalent has to hand the object back
        for the route to pass on. Nothing about the posting is communicated this
        way; the five linkage records carry that, by reference, as COBOL does.
    """
    # THE CONTEXT IS THIS PROGRAM'S WORKING-STORAGE, NOT AN ADDED ABSTRACTION. Every
    # field on it is a `01`/`03` item declared between [sales/sl055.cbl:L145] and
    # [sales/sl055.cbl:L259].
    ctx = _Sl055Context(
        ws_calling_data=ws_calling_data,
        system_record=system_record,
        system_record_4=system_record_4,
        to_day=to_day,
        file_defs=file_defs,
        facade=_resolve_facade() if facade is None else facade,
        #  THE CHANNEL TO `sl060`. Declared here only when the caller passed
        #  none, and RETURNED either way, so the route can hand the very object
        #  this program wrote to the program that reads it - the same pattern
        #  `gl070.run` uses for the General Ledger work files.
        open_item_file_2=(
            open_item_work_file(OPEN_ITEM_2_NAME, OiHeader)
            if open_item_file_2 is None
            else open_item_file_2
        ),
    )

    _da000_mainline(ctx)

    label = _Label.DA010_READ_LOOP

    while True:
        match label:
            case _Label.DA010_READ_LOOP:
                label = _da010_read_loop(ctx)
                continue
            case _Label.DA020_HEADER_ANALYSIS:
                label = _da020_header_analysis(ctx)
                continue
            case _Label.DA030_SKIP_INVOICE:
                # GO TO class 4 - SITES 1 AND 2 OF 4 land here. THE PER-SITE EQUIVALENCE
                # PROOF, restated at the dispatch point.
                label = _da030_skip_invoice(ctx)
                continue
            case _:
                # GO TO class 2 - `DA040_CLOSE_FILES`, from either
                # [sales/sl055.cbl:L368] or [sales/sl055.cbl:L478]. The `break` leaves
                # the loop.
                break

    label = _da040_close_files(ctx)

    # `goback.` at [sales/sl055.cbl:L509] or [sales/sl055.cbl:L518] returns WITHOUT
    # reaching `da999-Menu-Exit.`, so the two dispositions are kept distinct even though
    # both end the program.
    if label is _Label.GOBACK:
        #  THE CHANNEL IS RETURNED ON BOTH DISPOSITIONS. `sl060` reads what this
        #  program wrote whichever `goback` ended it, because in COBOL the file
        #  survives the run unit either way.
        return ctx.open_item_file_2

    _da999_menu_exit()
    return ctx.open_item_file_2



# --- traceability ----------------------------------------------------------
#
# Rule R-5 requires that every program map to a module, every paragraph to a
# function and every field to a data-dictionary entry, and that the mapping be
# RECORDED rather than left implicit. This footer is that record for
# `sales/sl055.cbl`, and `docs/migration/traceability.md` aggregates it.
#
# PROGRAM -> MODULE
#   sales/sl055.cbl  ->  acas_posting/programs/sl055_invoice_extract_analysis.py
#   Boundary: THE WHOLE PROGRAM. Unlike `gl051` and `irs030`, which are migrated
#   only in part, every section and paragraph of `sl055` is in scope.
#   Public API: `run` only. `__all__ = ("run",)`, and every other module-level
#   name begins with `_`, so a caller cannot reach into a program's internals -
#   exactly as a COBOL `CALL` cannot (section 0.3.3).
#
# PARAGRAPH -> FUNCTION   (all eighteen labels, in source order)
#   da000-mainline section.         L305  -> _da000_mainline
#   da010-Read-Loop.                L364  -> _da010_read_loop
#   da020-Header-Analysis.          L426  -> _da020_header_analysis
#   da030-Skip-Invoice.             L472  -> _da030_skip_invoice
#   da040-Close-Files.              L481  -> _da040_close_files
#   da999-Menu-Exit.                L520  -> _da999_menu_exit
#   db000-Create section.           L527  -> _db000_create
#   DB000-Create-Main.              L530  -> _db000_create_main
#   db010-Create-Anal.              L574  -> _db010_create_anal
#   db999-Main-Exit.                L587  -> _db999_main_exit
#   dc000-Store-Specials  section.  L590  -> _dc000_store_specials
#   dc999-Main-Exit.                L623  -> _dc999_main_exit
#   dd000-Extract section.          L626  -> _dd000_extract
#   dd999-Main-Ex.                  L691  -> _dd999_main_ex
#   zz070-Convert-Date        section. L694 -> _zz070_convert_date
#   zz070-Exit.                     L721  -> _zz070_exit
#   a01-Eval-Status section.        L724  -> _a01_eval_status
#   a01-exit.                       L729  -> _a01_exit
#
#   Three of the four sections carry statements DIRECTLY under the section
#   header, with no paragraph label between - `dc000-Store-Specials` L590,
#   `dd000-Extract` L626 and `zz070-Convert-Date` L694 - so the section function
#   holds the body and only the trailing `-Exit`/`-Ex` paragraph is separate.
#   `db000-Create` L527 is the exception: its first statement is inside
#   `DB000-Create-Main.` L530, so `_db000_create` holds only the retry loop.
#
#   Section 0.4.2's inventory for `sl055` is INCOMPLETE and the list above
#   supersedes it: it omits `dc000-Store-Specials section.` L590 (citing only
#   that section's exit paragraph) and `a01-exit.` L729 (which is declared on the
#   same source line as its `exit section.`, and so reads as one line rather than
#   two).
#
# STATEMENT -> CALL SITE
#   perform Value-Open-Input     L319  -> ctx.verbs.value_open_input
#   perform Value-Close          L321, L324, L499
#                                      -> ctx.verbs.value_close
#   perform Value-Open-Output    L322  -> ctx.verbs.value_open_output
#   perform Invoice-Open         L356  -> ctx.verbs.invoice_open
#   perform Value-Open           L357  -> ctx.verbs.value_open
#   perform Analysis-Open        L358  -> ctx.verbs.analysis_open
#   open extend  open-item-file-2 L359 -> ctx.open_item_file_2.open_extend
#   close        open-item-file-2 L361, L501
#                                      -> ctx.open_item_file_2.close
#   open output  open-item-file-2 L362 -> ctx.open_item_file_2.open_output
#   perform Invoice-Read-Next    L366  -> ctx.verbs.invoice_read_next
#   perform Value-Read-Indexed   L383, L407, L596, L613
#                                      -> ctx.verbs.value_read_indexed
#   perform db000-Create         L385, L598
#                                      -> _db000_create
#   perform Value-Write          L398, L560, L607
#                                      -> ctx.verbs.value_write
#   perform Value-Rewrite        L400, L420, L609, L621
#                                      -> ctx.verbs.value_rewrite
#   perform Invoice-Rewrite      L422, L441, L469
#                                      -> ctx.verbs.invoice_rewrite
#   perform dd000-Extract        L438  -> _dd000_extract
#   perform Invoice-Start        L476  -> ctx.verbs.invoice_start
#   perform dc000-Store-Specials L485, L489, L493, L497
#                                      -> _dc000_store_specials
#   perform Invoice-Close        L498  -> ctx.verbs.invoice_close
#   perform Analysis-Close       L500  -> ctx.verbs.analysis_close
#   perform Analysis-Read-Indexed L534, L551, L564
#                                      -> ctx.verbs.analysis_read_indexed
#   perform Analysis-Write       L580, L583
#                                      -> ctx.verbs.analysis_write
#   write   oi-header            L681  -> ctx.open_item_file_2.write
#   perform a01-Eval-Status      L683  -> _a01_eval_status
#   perform zz070-Convert-Date   L353  -> _zz070_convert_date
#                                         (body: dates.zz070_convert_date)
#
#   SIXTEEN DISTINCT FACADE VERBS, all from the ENTITY-named vocabulary, because
#   `sl055` copies `Proc-ACAS-FH-Calls.cob` [sales/sl055.cbl:L731] and not
#   `Proc-ZZ100-ACAS-IRS-Calls.cob`. That copybook has NO per-handler error-check
#   paragraph, so every reply is tested INLINE by the caller - which is what the
#   `if fs-reply ...` tests transcribed throughout this module are. No
#   handler-named alias (`acas008_*`, `acas012_*`, `acas013_*`, `acas015_*`,
#   `acas016_*`) is called anywhere in this module.
#
#   `move 1 to File-Key-No` is preserved at ALL NINE sites - L349, L382, L406,
#   L533, L550, L563, L579, L595, L612 - in place, un-hoisted and un-cached
#   (rule R-3, section 0.8.4, AMBIGUITY Q-55).
#
# `GO TO`   - eighteen sites, classified by SHAPE, not by matching a label list
#   class 1  loop-back to `da010-Read-Loop.` L364, transformed to a dispatcher
#            `continue`:
#              L428  da020 -> da010   (already analysed AND applied)
#              L442  da020 -> da010   (analysed, rewritten, totals skipped)
#              L470  da020 -> da010   (the principal back-edge)
#              L479  da030 -> da010   (repositioned, resume reading)
#   class 2  forward terminator to `da040-Close-Files.` L481, transformed to a
#            dispatcher `break` PLUS the post-loop block:
#              L368  inside the inline perform -> da040
#              L478  da030 -> da040   (START found no further invoice)
#            Section 0.6.3: the transformation is "`break` PLUS faithful
#            placement of that work after the loop, not `break` alone.
#            Mis-splitting here would silently drop end-of-run processing." The
#            work is the four special-total stores L482-L497 and the four closes
#            L498-L501.
#   class 3  section or paragraph exit, transformed to a `return`:
#              L543, L554, L566, L572  -> db999-Main-Exit. L587
#              L615                    -> dc999-Main-Exit. L623
#              L633                    -> dd999-Main-Ex.   L691
#              L707, L712              -> zz070-Exit.      L721
#                                         (inside the delegated `dates` body)
#   class 4  sibling re-dispatch - a named call followed by an explicit transfer
#            on the callee's own outcome. PER-SITE PROOF REQUIRED, and given:
#              L431  -> da030-Skip-Invoice. L472   (proof 1 of 4)
#              L436  -> da030-Skip-Invoice. L472   (proof 2 of 4)
#              L536  -> db010-Create-Anal.  L574   (proof 3 of 4)
#              L585  -> DB000-Create-Main.  L530   (proof 4 of 4, BACKWARD)
#
#   THE FOUR CLASS-4 EQUIVALENCE PROOFS, one per site:
#     1. L431. The transfer is the ENTIRE body of `if ih-type = 4`, so no
#        statement of `da020-Header-Analysis` is skipped by taking it, and
#        `da030-Skip-Invoice` is not reachable by fall-through because L470
#        transfers away first. Therefore "transfer to L472" == "run L473-L476,
#        then transfer where L477-L479 decide". `_da020_header_analysis` returns
#        `DA030_SKIP_INVOICE`; `run`'s dispatcher calls `_da030_skip_invoice` and
#        threads its returned label. Equivalent.
#     2. L436. Its `if` body is `move 1 to ws-p-flag` and then the transfer, and
#        the `move` is performed BEFORE the label is returned, so the flag is set
#        exactly once and exactly as early. Otherwise identical to proof 1. The
#        two sites are proven separately because the property being proven is
#        about each SITE's trailing statements, not about the shared target.
#        Equivalent.
#     3. L536. The transfer is the entire body of `if FS-Reply = 21 or = 23`;
#        every statement after it in `DB000-Create-Main` is reachable only when
#        that `if` was false, and `db010-Create-Anal` is unreachable by
#        fall-through because L572 transfers away. Therefore "transfer to L574" ==
#        "run L575-L584, then transfer where L585 says". Equivalent.
#     4. L585. UNCONDITIONAL, and the LAST statement of its paragraph, so nothing
#        follows it that a loop back-edge would skip. The cycle
#        `DB000-Create-Main -> db010-Create-Anal -> DB000-Create-Main` therefore
#        has exactly one entry point (`DB000-Create-Main`'s first statement),
#        exactly one back-edge, and no work after the back-edge - which is the
#        definition of a `while` loop over the entry point. `_db000_create`'s
#        `while True:` is that loop. It has NO iteration guard, matching the
#        source (AMBIGUITY Q-51). Equivalent.
#
# `EXIT PERFORM` / `EXIT PERFORM CYCLE` - six sites, NOT `GO TO`s
#   These exist because `da010-Read-Loop.` L364 contains an INLINE
#   `perform until FS-Reply = 10` L365-L424, which the maintainer introduced
#   deliberately - his own comment at L365 reads "changed 18/01/25 for clean up
#   using inline perform". The loop is already structured, so it is transcribed
#   as a `while`, not rebuilt as a `GO TO` cycle.
#     L371  exit perform        -> `break`, and then a FALL-THROUGH into
#                                  `da020-Header-Analysis.` L426
#     L374  exit perform cycle  -> `continue`  (line already analysed)
#     L377  exit perform cycle  -> `continue`  (comment line, product "/")
#     L403  exit perform cycle  -> `continue`  (group has no second character)
#     L409  exit perform cycle  -> `continue`  (group-level value row absent)
#     L423  exit perform cycle  -> `continue`  (end of the loop body)
#   The loop's own `UNTIL FS-Reply = 10` AND the explicit `if fs-reply = 10` at
#   L367 are BOTH reproduced. They are not redundant in the migration for the
#   same reason they are not redundant in the source: `fs-reply` is written both
#   by the facade verbs and by `open-item-file-2`, whose SELECT names the same
#   field, and the `UNTIL` is evaluated at the TOP of each iteration while L367
#   is evaluated immediately after the read.
#
# FALL-THROUGHS - two, recorded explicitly so that a reader diffing the two
#   files does not go looking for a `GO TO` that is not there
#     1. `da000-mainline` L362 -> `da010-Read-Loop.` L364. The entry section ends
#        with the OTM2 open and no transfer statement. Modelled by `run` setting
#        its initial label to `DA010_READ_LOOP` immediately after
#        `_da000_mainline` returns.
#     2. `da040-Close-Files` L518 -> `da999-Menu-Exit.` L520. Taken only when
#        NEITHER `ws-p-flag` nor `ws-Anal-Flag` is set; the two early `goback`s at
#        L509 and L518 skip `da999-Menu-Exit` entirely. Modelled by
#        `_da040_close_files` returning `DA999_MENU_EXIT` rather than `GOBACK`.
#   A third, inner fall-through is the `exit perform` at L371 listed above.
#
# `PERFORM ... THRU` - DOES NOT OCCUR in `sl055`. The four in-scope sites
#   repository-wide are `gl072` L300, `gl072` L304, `sl100` L344 and `pl100`
#   L336. Stated so that no later reader hunts for one here.
#

# ANOMALY REGISTER (rule R-4)
#   Section 0.6.7's twenty-two-entry register assigns `sl055` no numbered entry,
#   but it names one divergence explicitly and this file's own reading of the
#   frozen source surfaced six more. Every one is REPRODUCED, and rule R-4 with
#   section 0.7.4 conflict C-4 requires that each carry a comment at its
#   reproduction site citing the COBOL locator - which each does.
#
#   A. THE NINE-VERSUS-FOUR NEGATION DIVERGENCE.
#      `sl055` negates NINE fields for a credit note [sales/sl055.cbl:L657-L666];
#      `pl055` negates FOUR [purchase/pl055.cbl:L571-L575], and the four
#      (`oi-net`, `oi-carriage`, `oi-vat`, `oi-c-vat`) are a SUBSET of the nine.
#      Likewise the invoice sum: nine addends [sales/sl055.cbl:L671-L673] against
#      four [purchase/pl055.cbl:L580]. `pl055` IS NOT A MIRROR of `sl055`.
#      Reproduced in `_dd000_extract`; DO NOT NORMALISE EITHER DIRECTION. The same
#      note is carried in `pl055_order_proof_extract.py`. This is the same CLASS
#      of finding as section 0.6.7's A-1 (`sl060`'s missing terminating period
#      against `pl060`'s present one) and A-10 (three inconsistent
#      moving-average guards), for which section 0.6.1 says verbatim:
#      "Normalising them into one helper would be the single easiest way to fail
#      this migration."
#
#   B. THE NEGATED `oi-` FIELDS VERSUS THE UN-NEGATED `ih-` SUM.
#      [sales/sl055.cbl:L657-L666] flips nine `oi-` fields; [L671-L673] then sums
#      nine `ih-` fields - the header, untouched. So a credit note's OTM2 row
#      carries NEGATIVE money while `ws-inv-amt` carries the POSITIVE sum, and
#      [L677] adds that positive sum into `sl-credit-notes-this-month`.
#      Reproduced in `_dd000_extract`. AMBIGUITY Q-50.
#
#   C. THE `FS-Reply` TEST INCONSISTENCY.
#      `= 21 or = 23` at L384, L408, L477 and L535; only `= 21` at L552, L565,
#      L597 and L614 - the same verb, the same files. Each site is transcribed as
#      written. The data-access layer's finding N2 is that
#      `FsReply.KEY_NOT_FOUND` (23) is DOCUMENTED BUT NEVER ACTUALLY RETURNED, so
#      the `or = 23` arms are dead in practice; they are kept regardless, because
#      removing a test is a behaviour change (rule R-3). Consolidated comment in
#      `_da010_read_loop` at the L384 site; per-site notes at the other seven.
#
#   D. THE UNGUARDED CROSS-PARAGRAPH RETRY.
#      [sales/sl055.cbl:L585] transfers BACKWARD to [sales/sl055.cbl:L530] with no
#      iteration limit, so a failing `Analysis-Write` [L580] spins forever with no
#      message. Reproduced as an unbounded `while True:` in `_db000_create`; NO
#      counter, ceiling or break-out added. AMBIGUITY Q-51.
#
#   E. THE LABEL-CASE INCONSISTENCY.
#      Declared `DB000-Create-Main.` [sales/sl055.cbl:L530], targeted as
#      `db000-Create-Main` [sales/sl055.cbl:L585]. COBOL folds case, so the two
#      are one label; recorded because a reader grepping the exact string finds
#      only one occurrence. Noted in `_db000_create_main`.
#
#   F. THE VALUE FILE IS OPENED, CLOSED, RE-OPENED AND CLOSED AGAIN.
#      [sales/sl055.cbl:L319-L324] is an EXISTENCE PROBE - `Open-Input`, and on
#      failure `Close` then `Open-Output`, then an UNCONDITIONAL `Close` - and
#      [sales/sl055.cbl:L357] reopens the file eight lines later. All four verbs
#      are reproduced in order in `_da000_mainline` and none is collapsed.
#
#   G. THE FAILED OTM2 WRITE PERFORMS NO CONTROL TRANSFER.
#      [sales/sl055.cbl:L682-L689] evaluates the status, displays it, waits for a
#      keypress - and then simply ends the section. No retry, no abort, no flag.
#      The caller stamps `ih-update` and rewrites the invoice as ANALYSED, so the
#      invoice is marked extracted while its open item does not exist and `sl060`
#      will never see it: a rejection with a PARTIAL database effect in section
#      0.6.5's terms. Reproduced in `_dd000_extract`. AMBIGUITY Q-52.
#
#   H. THE TWO EARLY `goback`s DO NOT SET `WS-Term-Code`.
#      [sales/sl055.cbl:L509] and [sales/sl055.cbl:L518] return with the term code
#      left at whatever the caller passed - normally zero - so
#      `sales/sales.cbl`'s gate `if ws-term-code not = zero`
#      [sales/sales.cbl:L765] PASSES and `sl060` runs anyway, even though this
#      program has just reported unprinted invoices or invented emergency
#      analysis names and abandoned its run. Contrast
#      [sales/sl055.cbl:L344], which DOES set 8 on the missing-file path.
#      Reproduced in `_da040_close_files`; no `move` added.
#
#   Also recorded, as findings rather than defects, at their sites: the second
#   `Analysis-Write` [L583] is not preceded by a `move 1 to File-Key-No` while
#   every other indexed operation is; `db000-Create`'s pass-2 failure arm [L553]
#   restores `WS-PA-Code` but NOT `va-code`, so the caller returns holding the
#   group-level key; `ws-inv-amt` [L671] is never re-zeroed between headers; and
#   `dd999-Main-Ex` is spelled `-Ex` where its three sibling exits are spelled
#   `-Exit`.
#
# AMBIGUITY REGISTER (rule R-6) - each becomes an entry in
#   `docs/migration/ambiguity-resolutions.md`, and each is arbitrated by the
#   compiled program, never by reasoning about intent
#     Q-50  the negated `oi-` fields versus the un-negated `ih-` sum, and hence
#           the sign of `sl-credit-notes-this-month`
#     Q-51  the termination of the unguarded `db010-Create-Anal` retry when
#           `Analysis-Write` fails
#     Q-52  the disposition of a failed `write oi-header`, and whether a
#           sequential write can fail at all once the file is open
#     Q-53  `il-type pic x` [copybooks/slwsinv2.cob:L97] compared against the
#           numeric literal 3 [sales/sl055.cbl:L390], where `ih-type` is `pic 9`
#     Q-54  what GnuCOBOL does with the space-filled bytes 37-66 that the group
#           move at [sales/sl055.cbl:L538] leaves before L539-L540 zeroes them
#     Q-55  whether any of the nine `move 1 to File-Key-No` statements has an
#           observable effect, given the handler already defaults it
#     Q-56  whether any scenario sets `FS-Cobol-Files-Used`, which would make
#           [sales/sl055.cbl:L326-L348] reachable
#     Q-57  whether the verb shape assumed here is the one
#           `acas_posting.dal.facade` publishes
#     Q-58  the invoice record area's three `REDEFINES` views and which of them a
#           handler populates on a `Read-Next`
#
# FIELD -> DICTIONARY ENTRY
#   The `_D_*` block between [sales/sl055.cbl:L198] and the OTM2 layout is this
#   module's field-to-dictionary mapping, and it is exhaustive for the fields this
#   program touches - working storage, both invoice views, the value and analysis
#   records, the two `SYSTOT-REC` columns, `File-Key-No`, `Date-Form`,
#   `File-System-Used` and all twenty-eight OTM2 leaves. Every descriptor is built
#   by `acas_posting.cobol.picture` or looked up from a record class's published
#   `FIELDS`, so each carries either a `dictionary_key` (for a field the bridge
#   and schema also declare) or a `source_locator` matching
#   `^[A-Za-z0-9_./-]+:L[0-9]+(-L[0-9]+)?$`, which `FieldDescriptor.__post_init__`
#   enforces. Some descriptors have no conversion call site - `_D_IH_TEST`,
#   `_D_IL_NET`, `_D_IL_PRODUCT`, `_D_VA_FIRST`, `_D_PA_FIRST`, `_D_IH_CUSTOMER`,
#   `_D_OI_CUSTOMER` and `_D_FILE_SYSTEM_USED` among them - because the operation
#   on that field is a comparison against a figurative constant, a reference
#   modification, or a condition-name predicate that takes the VALUE rather than
#   the descriptor. They are retained deliberately: rule R-5 asks for a
#   field-to-dictionary entry for every field the program touches, not only for
#   every field a conversion happens to need.
#
# STRUCTURAL NOTES
#   THE OTM2 WORK FILE. `sl055` opens, writes and closes `open-item-file-2`,
#   declared by `copy "seloi2.cob"` [sales/sl055.cbl:L134] with its FD from
#   `copy "fdoi2.cob"` [sales/sl055.cbl:L144] and its record layout from
#   `copy "slwsoi.cob"` [sales/sl055.cbl:L145]. Two decisions were needed and both
#   are recorded here rather than left to inference:
#
#     1. THE RECORD is NOT declared locally. `copybooks/slwsoi.cob` has no entry
#        of its own in section 0.3.1's `records/` inventory, but
#        `acas_posting.records.otm3` - the module section 0.4.1.3 derives from
#        `copybooks/slwsoi3.cob` - already publishes `OiHeader` with ALL
#        TWENTY-EIGHT leaves and their dictionary keys, because the two layouts
#        are the same open-item header. It is imported and used as published. No
#        new module was created and no layout was re-declared, which keeps
#        `acas_posting/programs/` at exactly the thirteen files sections 0.4.1.2
#        and 0.4.4 allow.
#     2. THE FILE is NOT declared locally either. `acas_posting.workfiles`
#        publishes `OpenItemWorkFile`, the shared carrier for both open-item work
#        files, and `open_item_work_file` declares one. `open extend` appends to
#        what is there, `open output` truncates, `write` appends a deep snapshot
#        in insertion order, `read_next` is what `sl060` uses, and `close` keeps
#        the records. Every verb sets `fs-reply`, because
#        `copybooks/seloi2.cob` declares `status fs-reply` - the very same field
#        the facade verbs write, which is why the doubled loop condition at
#        L365/L367 is not redundant.
#        THIS WAS ONCE A MODULE-PRIVATE CLASS, on the ground that
#        `LineSequentialWorkFile`'s `OpenMode` had no EXTEND. The ground was true
#        and the conclusion was wrong: a work file that the producer and the
#        consumer declare separately is not a channel, so `sl060` could never read
#        what this program wrote. `OpenMode.EXTEND` is now published, and the file
#        is declared ONCE.
#
#   THE EXTEND-THEN-FALLBACK IDIOM. [sales/sl055.cbl:L359-L362] tries
#   `open extend` and, on any non-zero status, closes and `open output`s -
#   creating the file. The same shape appears at `gl080`'s archive open
#   [general/gl080.cbl:L411-L414]. BOTH branches are reproduced, including the
#   `close` that runs even though the `open extend` did not succeed.
#
#   THE FILE REACHES NO SCHEMA TABLE. It is `sl060`'s input - `sl060` copies the
#   same `seloi2`/`fdoi2`/`slwsoi` trio - so it appears in NO table dump, and the
#   handoff is via the sequence object exactly as it is via the file in COBOL.
#   `run` exposes it as the keyword-only `open_item_file_2` so the CLI can pass
#   one object to both programs; this module does NOT import
#   `acas_posting.programs.sl060_invoice_posting`, and must not.
#
#   THE INVOICE RECORD AREA. `01 Invoice-Record.` [copybooks/slwsinv2.cob:L27] is
#   one 137-byte area with two `REDEFINES` views over it, `Invoice-Header` L38 and
#   `Invoice-Line` L91, and `sl055` reads all three: the generic view's
#   `Invoice-Nos`/`Item-Nos` to set the START key [L473-L474], the header view for
#   `ih-*` and the line view for `il-*`. `_InvoiceRecordArea` holds the key and
#   both views side by side and exposes `ih_test` for the L370 discriminator; it is
#   module-private because the aliasing is this program's own reading of the area,
#   not a published record contract. AMBIGUITY Q-58.
#

# OMISSIONS - deliberate, and each one recorded rather than silent
#   Section 0.4.3 and rule R-5 require that omissions be recorded AS omissions
#   "so that a reader comparing the two files does not conclude something was
#   lost". Nothing below is absent by accident.
#
#   1. THE `if FS-Cobol-Files-Used` BLOCK [sales/sl055.cbl:L326-L348].
#      THE GATE ITSELF IS REPRODUCED, through the condition-name vocabulary, so
#      the decision is data-driven at runtime exactly as the COBOL's is. What is
#      omitted is the BODY: `call "CBL_CHECK_FILE_EXIST"` [L327], [L336] and
#      `call "sl070" using ws-calling-data system-record to-day file-defs` [L332].
#      `sl070` is not one of the twelve in-scope programs (section 0.2.2), so no
#      Python module exists to call, and rule R-1 forbids invoking the COBOL at
#      runtime. `_da000_mainline` therefore raises
#      `CobolFileSystemPathUnavailable` inside the gate, with a message naming all
#      four facts: that the block needs `sl070` and `CBL_CHECK_FILE_EXIST`, that
#      `sl070` is out of scope, that R-1 forbids the call, and that the branch is
#      unreachable in the RDBMS configuration this migration targets
#      (`88 FS-Cobol-Files-Used value zero.` [copybooks/wssystem.cob:L113] against
#      `88 FS-RDBMS-Used value 1.` [copybooks/wssystem.cob:L116]). It is NOT
#      silently skipped, NOT stubbed as a no-op and NOT partially emulated. The
#      observable consequences the COBOL has on that path are preserved up to the
#      raise: the `SL125` diagnostic and `move 8 to WS-Term-Code` [L344] happen
#      first. AMBIGUITY Q-56.
#
#   2. `display ... at` OUTPUT -> LOG RECORDS, BUT NOT ALL OF IT. Section 0.3.4
#      converts a DIAGNOSTIC display, which "must not alter control flow and must
#      not appear in any table dump" - and none of these records does either.
#      CONVERTED: L339 (`SL125`, inside omission 1), L351-L352 (banner and title),
#      L504 (`SL122`), L512-L513 (`SL123`, `SL126`) and L684-L686 (`SL121`,
#      `fs-reply`, `Exception-Msg`). Severity matches the original's intent:
#      `warning` for the operator-attention flags, `error` for the failed write and
#      the missing file, `info` for the banner. The screen coordinates,
#      `foreground-color` clauses and `erase eos` are dropped with them.
#
#      NOT CONVERTED, and each for a stated reason:
#        * L340, L506, L515, L687 - `SL002`. A PURE ACKNOWLEDGEMENT PROMPT: every
#          one stands immediately before an `accept ws-reply` and the literal is
#          nothing but the instruction to press that key, so section 0.3.4 drops
#          it with the pause (omission 5). No substantive half remains to keep.
#        * L354 - `display ws-date`. THE POSTING DATE IS BUSINESS DATA, which the
#          safe-event schema in `acas_posting/dal/status.py` excludes from a record
#          (CWE-532). It is a command-line INPUT and `clock.py` pins it, so nothing
#          is lost.
#      `Exception-Msg` IS carried, because `a01-Eval-Status` [L724-L727] fills it
#      only from the static table `copybooks/FileStat-Msgs.cpy` keyed on `fs-reply`:
#      it is a fixed status NAME, not driver text and not a business value.
#
#   3. `accept ws-env-lines from lines` [sales/sl055.cbl:L308] AND THE SCREEN
#      GEOMETRY [L309-L314]. `ws-env-lines`, `ws-lines` and `ws-23-lines` exist
#      only to place `display` output on a terminal of unknown height, and
#      `subtract 1 from ws-lines giving ws-23-lines` [L314] is the only arithmetic
#      in the program that computes nothing financial. NOTE THAT L308 IS A
#      TERMINAL-GEOMETRY READ, NOT A CLOCK READ - `sl055` contains ZERO clock
#      reads of any kind, which is why pinning `to_day` pins the whole run
#      (rule R-6).
#
#   4. `set ENVIRONMENT "COB_SCREEN_EXCEPTIONS"/"COB_SCREEN_ESC" to "Y"`
#      [L316-L317] and `copy "envdiv.cob"` [L129] - curses configuration and an
#      ENVIRONMENT DIVISION shell. Representation only.
#
#   5. `accept ws-reply` [L342], [L507], [L516], [L688] - acknowledgement pauses
#      whose only effect is to block a terminal. DROPPED. BUT: the
#      `if WS-Caller not = "xl150"` branches around L342, L507 and L516 are
#      PRESERVED, and so are the `goback`s at L345, L509 and L518. The
#      `xl150` test is the codebase's OWN unattended-mode check - `xl150` is the
#      end-of-cycle driver - and it is direct evidence that headless operation was
#      designed for rather than bolted on. Only the pause is removed; every
#      control transfer around it survives.
#
#   6. THE VERSION BANNER AND THE MESSAGE LITERALS. `prog-name`
#      [sales/sl055.cbl:L152] and `SL121`, `SL122`, `SL123`, `SL125`, `SL126`
#      [L250-L257] survive as log text. `SL002` [L250] is DECLARED AND
#      DELIBERATELY NEVER REFERENCED - it is the acknowledgement prompt of
#      omission 2 - and `SL124` [sales/sl055.cbl:L255] is DECLARED AND NEVER
#      REFERENCED BY THE FROZEN PROGRAM ITSELF. Both are transcribed as
#      declarations and used nowhere, recorded here so that each absence reads as
#      deliberate: rule R-5 maps the whole `01 Error-Messages.` group, so no member
#      is dropped merely because nothing reads it.
#
#   7. THE COMMENTED-OUT DECLARATIVES BLOCK [sales/sl055.cbl:L280-L303]. A `use
#      after standard error procedure on open-item-file-2` handler, entirely
#      commented out in the frozen source. Not code, so not translated.
#
#   8. THE FACADE STUB BLOCK IS PRESENT IN THE SOURCE BUT MAPS TO NOTHING.
#      `01 Dummies-4-Unused-ACAS-FH-Calls.` [sales/sl055.cbl:L164-L184] declares
#      the record areas the copybook's unused verbs reference, purely so the
#      linker resolves them; four of its entries - `System-Record-4` L167,
#      `WS-Value-Record` L175, `WS-Analysis-Record` L177 and `WS-Invoice-Record`
#      L181 - are themselves commented out because this program supplies them for
#      real. Python has no equivalent need, so the block translates to nothing, as
#      section 0.4.3 prescribes for `gl072`'s counterpart. NOTE THAT THIS
#      CONTRADICTS the assertion that `sl055` has no stub block: it has one, at
#      L164-L184.
#
#   9. `call "SYSTEM" using Print-Report` - DOES NOT OCCUR. `sl055` has no print
#      file, no report writer and no spool-out path at all, so section 0.2.2's
#      exclusion of that path has nothing to exclude here.
#
#  10. IRS FAN-OUT TESTS - ZERO. `sl055` is an EXTRACT program, not a posting
#      program: it never reads `System-Record`'s IRS switch and never branches on
#      it. `sl060`, `sl100`, `pl060` and `pl100` each carry six or seven such
#      tests. Confirmed by reading the whole of the frozen source.
#
#  11. `zz050-Validate-Date`, `zz060-Convert-Date`, the `maps03`/`maps04` wrapper
#      and `copy "wsmaps03.cob"` - NONE OF THEM OCCURS. `sl055` carries only
#      `zz070-Convert-Date`, so it never converts a date to a day number and
#      ANOMALY A-22 (a wrapper section whose name and exit label disagree) DOES
#      NOT ARISE HERE. `acas_posting.records.maps03` is not imported and
#      `dates.zz050_*` / `dates.zz060_*` are not called.
#
# CITATION CORRECTIONS - the frozen files are the authority
#   Recorded because a downstream reader working from the plan alone would look in
#   the wrong place. In each case the frozen source was measured directly.
#
#   * THE SECTION INVENTORY. Section 0.4.2 omits `dc000-Store-Specials section.`
#     [sales/sl055.cbl:L590], citing only that section's exit paragraph, and omits
#     `a01-exit.` [sales/sl055.cbl:L729] entirely. The eighteen-label list in this
#     footer is the measured inventory and supersedes it.
#
#   * THE FACADE STUB BLOCK. The claim that `sl055` has no stub block is wrong:
#     `01 Dummies-4-Unused-ACAS-FH-Calls.` stands at
#     [sales/sl055.cbl:L164-L184]. Its `gl072` counterpart is likewise cited as
#     beginning at L134 when the label is at [general/gl072.cbl:L135].
#
#   * THE CALLER'S GATE. The Sales menu's dispatch is cited as
#     [sales/sales.cbl:L759-L768]; the frozen paragraph is `load07.` at
#     [sales/sales.cbl:L756], with `move "sl055" to ws-called`
#     [sales/sales.cbl:L763], `perform load000.` [sales/sales.cbl:L764], the gate
#     `if ws-term-code not = zero / go to display-menu.`
#     [sales/sales.cbl:L765-L766], then `move "sl060"`
#     [sales/sales.cbl:L767] and `go to load000.` [sales/sales.cbl:L768]. The
#     dispatcher `load000.` itself is at [sales/sales.cbl:L698], its `CALL` at
#     [sales/sales.cbl:L702-L707], and it tests `ws-term-code < 8`
#     [sales/sales.cbl:L708-L709] and `> 7` [sales/sales.cbl:L710-L712].
#
#   * THE THIRD PARAMETER'S SPELLING. `sl055` declares it `system-record-4`
#     [sales/sl055.cbl:L273]; the caller passes `WS-System-Record-4`
#     [sales/sales.cbl:L704]. The caller's `overrewrite.` is what makes this
#     program's `system_record_4` and `Date-Form` mutations diff-visible.
#
#   * `File-Key-No` IS AT [copybooks/wsfnctn.cob:L46], not L45, inside
#     `03 Logging-Data.` [copybooks/wsfnctn.cob:L44]. `Date-Form` is at
#     [copybooks/wssystem.cob:L128], and `File-System-Used` at
#     [copybooks/wssystem.cob:L112] with `88 FS-Cobol-Files-Used value zero.` at
#     [copybooks/wssystem.cob:L113].
#
#   * `pl055`'s NEGATION BLOCK is cited as [purchase/pl055.cbl:L572-L575], which
#     is correct for the four `multiply` statements; the guarding
#     `if ih-type = 3` is at [purchase/pl055.cbl:L571], and the four fields are
#     `oi-net`, `oi-carriage`, `oi-vat` and `oi-c-vat`. Its four-addend sum is the
#     single statement at [purchase/pl055.cbl:L580].
#
# --- end traceability -----------------------------------------------------
