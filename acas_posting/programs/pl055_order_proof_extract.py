"""`pl055` - Purchase Invoice Post Extract, migrated from `purchase/pl055.cbl`.

THE PROGRAM, IN ITS OWN WORDS. `*> Remarks.  PO (Orders) Proof Report Extract
& Analysis.` [purchase/pl055.cbl:L20] is what the source calls itself; `display
"Invoice Post Extract"` [purchase/pl055.cbl:L294] is what it calls itself on
screen; and the Agent Action Plan calls it the order-proof extract. All three
name the same 635-line program, and it does four things:

  1. walks the purchase-invoice file line record by line record, accumulating
     value-analysis counts and money into `VALUEANAL-REC` per analysis group,
     creating an emergency `ANALYSIS-REC` when the group is missing;
  2. for each invoice HEADER record, accumulates four special totals - VAT,
     VAT-on-receipts, carriage and discount - and stamps the header analysed;
  3. extracts each unapplied header into the OTM4 open-item work file, which
     `pl060` consumes, negating FOUR money fields for a credit note;
  4. adds the invoice or credit-note total into the purchase period totals.

  ============================================================================
  ⛔ THIS MODULE IS **NOT** A MIRROR OF `sl055`. DO NOT MAKE IT ONE. ⛔
  ============================================================================

The Agent Action Plan describes `pl055` as the "Purchase mirror of `sl055`".
Measured against the two frozen sources, that is WRONG: they diverge in
EIGHTEEN places, at least eight of them behaviourally significant and directly
visible in a table dump. This module was transcribed from
`purchase/pl055.cbl` alone, statement by statement. It does not import,
adapt, parameterise or share code with the sales extract, and every divergence
below is preserved deliberately under rule R-4 - *"A defect reproduced is
correct; a defect fixed is a failure."*

    #   what differs               sl055                       pl055 (HERE)
    --- -------------------------- --------------------------- --------------
    1   negation-block width       NINE fields          [L658-L666]
                                                               FOUR fields    [L571-L575]
                                   ...and `oi-deduct-amt` IS negated there,
                                   but is NOT negated here even though it IS
                                   moved at [purchase/pl055.cbl:L564]
    2   invoice-total addends      NINE                 [L671-L673]
                                                               FOUR           [L580]
    3   main-loop structure        inline `perform until` with
                                   `exit perform`       [L365-L424]
                                                               a plain `GO TO`
                                                               loop           [L315, L341, L347, L360]
    4   loop-exit condition        `if fs-reply = 10`, EOF only
                                                        [L367]
                                                               `if FS-Reply not = zero`,
                                                               ANY non-zero   [L308]
    5   `INITIALIZE`               `initialize oi-header with filler.`
                                                        [L635]
                                                               `initialise OI-Header.`
                                                               - British, and
                                                               NO `WITH FILLER` [L547]
    6   case of a STORED flag      upper-case `"Z"`     [L421, L468]
                                                               lower-case `"z"` [L358, L396]
    7   skip-invoice path          `da030-Skip-Invoice` + `Invoice-Start`
                                   + proforma filter + pending filter
                                   + `ws-p-flag`        [L430-L434, L472-L479]
                                                               NONE OF IT EXISTS
    8   header-analysis sign flips THREE                [L446, L457, L463]
                                                               TWO - the discount
                                                               block has none  [L376, L387, L391-L394]
    9   VAT total addends          THREE, incl. `ih-e-vat`
                                                        [L444]
                                                               TWO - `ih-e-vat`
                                                               omitted         [L374]
    10  paragraph naming           `da`/`db`/`dc`/`dd`-prefixed
                                                               UNPREFIXED
    11  the Value-file open        an existence-probe dance
                                                        [L319-L324]
                                                               just `perform Value-Open.`
                                                               twice, no reply
                                                               test            [L261, L299]
    12  `ih-status-A`              sets `ih-status` AND `ih-status-A`
                                                        [L679-L680]
                                                               sets `ih-status`
                                                               ONLY            [L586]
    13  the write target           `write oi-header.`   [L681]
                                                               `write open-item-record-4.`
                                                                               [L587]
    14  `a01-Eval-Status` exit     `a01-exit.`          [L729]
                                                               NO exit paragraph
                                                                               [L629-L632]
    15  accumulation verb count    four single-receiver [L391-L395]
                                                               two two-receiver
                                                                               [L330, L332]
    16  `il-product (1:1) = "/"`   present              [L376]
        comment filter                                         absent
    17  value-analysis groups      `vo`,`vp`,`zc`,`zd`, `va-system` implicit
                                                               `vi`,`vj`,`za`,`zb`,
                                                               `va-system` set
                                                               EXPLICITLY      [L403]
    18  `extract` terminator       `exit section.`             `main-exit. exit.`
                                                               - a plain `EXIT` [L597]

Divergence 13 was measured and is COSMETIC, which the Agent Action Plan could
not know: in `pl055` BOTH `copy "fdoi4.cob"` [purchase/pl055.cbl:L120] and
`copy "plwsoi.cob"` [purchase/pl055.cbl:L121] sit in the FILE SECTION under
the one FD, so `01 open-item-record-4 pic x(113)` [copybooks/fdoi4.cob:L2] and
`01 OI-Header` [copybooks/plwsoi.cob:L9] are two record descriptions of the
SAME 113-byte area and no transfer is implied. `pl060` proves the point from
the other side: it puts `plwsoi.cob` in WORKING-STORAGE
[purchase/pl060.cbl:L152], which is exactly why IT needs `move
open-item-record-4 to oi-header.` [purchase/pl060.cbl:L428] and `pl055` does
not. See STRUCTURAL NOTES in the traceability footer.

THE LINKAGE - THE SL/PL FIVE-PARAMETER SHAPE, VERBATIM.

    procedure division using ws-calling-data          [purchase/pl055.cbl:L239]
                             system-record            [purchase/pl055.cbl:L240]
                             system-record-4          [purchase/pl055.cbl:L241]
                             to-day                   [purchase/pl055.cbl:L242]
                             file-defs.               [purchase/pl055.cbl:L243]

`run` mirrors that list in that order. The third parameter is spelled
literally `system-record-4` and is the period-totals record
[copybooks/wssys4.cob:L8] - `pl055` is one of only nine writers of it in the
whole migration, at [purchase/pl055.cbl:L582] and [purchase/pl055.cbl:L584].

⛔ CITATION CORRECTION - THE PURCHASE TERM-CODE GATE DOES EXIST.

The Agent Action Plan states that Purchase has no term-code gate at all and
concludes that `move 8 to WS-Term-Code` [purchase/pl055.cbl:L286] therefore
"has no gating effect on pl060". The premise is right and the conclusion is
WRONG, measured. `load08` really does dispatch the two programs with no test
between them, its would-be gate lines commented out:

     move     "pl055" to ws-called.              [purchase/purchase.cbl:L759]
     perform  load000.                           [purchase/purchase.cbl:L760]
     move     "pl060" to ws-called.              [purchase/purchase.cbl:L761]
     go       to load000.                        [purchase/purchase.cbl:L762]

but the SHARED dispatch paragraph gates on the way out:

     if       ws-term-code > 7    *> Got a serious (reported) error
              go to overrewrite.                 [purchase/purchase.cbl:L704-L705]

and `overrewrite.` [purchase/purchase.cbl:L621] falls through to `overclose.`
[purchase/purchase.cbl:L652] and `goback.` [purchase/purchase.cbl:L653]. A
`GO TO` out of a `PERFORM` range abandons the return, so with term code 8 the
`perform load000.` at L760 NEVER RETURNS and the menu program itself ends.
`pl060` IS NEVER CALLED. The three ledgers' gate predicates still must not be
unified - General tests `= 5` [general/general.cbl:L810-L811], Sales tests
`not = zero` [sales/sales.cbl:L759-L768] and Purchase tests `> 7`
[purchase/purchase.cbl:L704] - but the reason is now the measured one.

A SECOND-ORDER CONSEQUENCE, worth stating because it bounds this module's
responsibility: `overrewrite` [purchase/purchase.cbl:L621-L651] is what
PERSISTS `System-Record-4`, doing `move WS-System-Record-4 to System-Record`
and `System-Rewrite` under file key 4 for both the RDB and the Cobol
parameter file. The period totals this module adds at [L582] and [L584] are
therefore written by the MENU, not by `pl055`. This module mutates the
in-memory record and persists nothing, exactly as the COBOL does.

WHAT THIS MODULE DELIBERATELY DOES NOT DO. It has no print file and no `call
"SYSTEM" using Print-Report`; no `PInvoice-Start` and no `set fn-` of any
kind; no skip-invoice paragraph, proforma filter, pending filter or
`ws-p-flag`; no IRS fan-out test; no `ROUNDED` store and no `DIVIDE`; and no
`zz050`, `zz060` or `maps03`/`maps04` wrapper, so anomaly A-22 cannot arise
here. The full list is in OMISSIONS in the traceability footer.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field as dataclass_field, fields as dataclasses_fields
from decimal import Decimal
from types import ModuleType
from typing import Any, Final

# `MULTIPLY -1 BY x`, `ADD ... GIVING`, `ADD ... TO` and `SUBTRACT ... FROM`.
# Every store in this module truncates toward zero: `pl055` contains ZERO
# `ROUNDED` phrases and ZERO `DIVIDE` statements, so `rounded=` is never
# passed and its default False is the whole of the program's rounding policy.
from acas_posting.cobol import arithmetic

# The `88`-level vocabulary. `il-analyised` [copybooks/plwspinv2.cob:L72],
# `ih-analyised` [copybooks/plwspinv2.cob:L53] and `applied`
# [copybooks/plwspinv2.cob:L43] gate the walk; `FS-Cobol-Files-Used`
# [copybooks/wssystem.cob:L113] gates the block this module refuses to run;
# `Date-UK` and `Date-USA` [copybooks/wssystem.cob:L129-L130] steer `zz070`.
from acas_posting.cobol import condition_names

# `MOVE` in all its categories - alphanumeric, numeric, group, figurative,
# multi-receiver - plus 1-based reference modification for
# [purchase/pl055.cbl:L622-L624]. `pl055` issues 91 `MOVE` statements, the
# count `move.MOVE_STATEMENT_CENSUS` records for this file.
from acas_posting.cobol import move

# `PIC` parsing, for the working storage `pl055` declares itself and which is
# therefore in no data dictionary: `01 ws-data.` [purchase/pl055.cbl:L161-L179].
from acas_posting.cobol import picture

# copy "wsfnctn.cob".               [purchase/pl055.cbl:L128]
# The receiving descriptor type, and the two dictionary-backed lookups that
# supply descriptors for records the bridge does map.
from acas_posting.cobol.field import FieldDescriptor, descriptors_for_copybook_record

# copy "wsfnctn.cob".               [purchase/pl055.cbl:L128]
# `Fs-Reply pic 99` [copybooks/wsfnctn.cob:L25] is tested at six sites in this
# program and never against a bare integer literal.
from acas_posting.dal.status import FsReply

# `zz070-Convert-Date` [purchase/pl055.cbl:L599-L627] is byte-identical in all
# ten carrying programs, so it is consolidated rather than re-implemented.
# `pl055` copies NO `wsmaps03.cob` and has no `zz050`, no `zz060` and no
# date-module wrapper, so nothing else from `dates` is reachable from here.
from acas_posting.dates import WsDateFormats, zz070_convert_date

# copy "wsanal.cob".                [purchase/pl055.cbl:L133]
from acas_posting.records.analysis import WsAnalysisRecord

# copy "wscall.cob".                [purchase/pl055.cbl:L232]
# `01 WS-Calling-Data.` [copybooks/wscall.cob:L6-L14] - the seven-field
# linkage block. Note the span: the Agent Action Plan cites L6-L13, but
# `WS-CD-Args` is at [copybooks/wscall.cob:L14], so the record ends there, as
# this module's own `RECORD_LOCATOR` already records.
from acas_posting.records.calling_data import (
    WsCallingData,
    descriptor_for as calling_data_descriptor_for,
)

# copy "wsfnctn.cob".               [purchase/pl055.cbl:L128]
# Carries `Fs-Reply` [copybooks/wsfnctn.cob:L25] and, inside `Logging-Data`
# [copybooks/wsfnctn.cob:L44], `File-Key-No` [copybooks/wsfnctn.cob:L46] -
# the field the ten `move 1 to File-Key-No` statements target.
from acas_posting.records.file_access import FileAccess

# copy "wsnames.cob".               [purchase/pl055.cbl:L235]
from acas_posting.records.file_defs import FileDefs

# copy "plwsoi.cob".                [purchase/pl055.cbl:L121]
# The 113-byte purchase Open Item Header. It is published here rather than
# declared locally because `records/otm5.py` already carries this exact
# copybook layout with a dictionary key on every field.
from acas_posting.records.otm5 import (
    Filler1,
    OiBatch,
    OiCustomer,
    OiHeader,
    OiKey,
    OiSupplier,
    descriptors_of as otm5_descriptors_of,
)

# copy "plwspinv2.cob".             [purchase/pl055.cbl:L135]
# THE FLAT SHAPE, not the nested `plwspinv.cob` one: `pl055` copies
# `plwspinv2.cob`, whose `Invoice-Header` [copybooks/plwspinv2.cob:L21] and
# `Invoice-Line` [copybooks/plwspinv2.cob:L56] both REDEFINE
# `WS-PInvoice-Record` [copybooks/plwspinv2.cob:L10], which is why `ih-test`
# and `il-line` share bytes and why [purchase/pl055.cbl:L311] can use one to
# tell a header from a line.
from acas_posting.records.purchase_invoice import (
    IhFig2,
    IhInvoiceHeader,
    IhSupplier2,
    IlInvoiceLine,
    InvoiceKey,
    WsPInvoiceRecord,
    descriptor_for as pinvoice_descriptor_for,
)

# copy "wssystem.cob".              [purchase/pl055.cbl:L233]
from acas_posting.records.system_record import SystemRecord

# copy "wssys4.cob".                [purchase/pl055.cbl:L234]
from acas_posting.records.system_record_4 import SystemRecord4

# copy "Test-Data-Flags.cob".       [purchase/pl055.cbl:L225]
from acas_posting.records.test_data_flags import AcasDalCommonData

# copy "wsval.cob".                 [purchase/pl055.cbl:L132]
from acas_posting.records.value_analysis import WsValueRecord

# `open extend`/`open output`/`write`/`close open-item-file-4`
# [purchase/pl055.cbl:L301-L304, L423, L587] act on a transient work file that
# reaches no schema table. The published status constant, open-mode vocabulary
# and error type are reused so this module invents no parallel vocabulary; the
# file itself is module-private because `OpenMode` has no `EXTEND` member -
# see STRUCTURAL NOTES.
from acas_posting.workfiles import FS_REPLY_OK, OpenMode, WorkFileError

#: Agent Action Plan section 0.3.3, verbatim: *"Each `programs/*.py` module
#: exposes a single `run(...)` entry mirroring its COBOL `PROCEDURE DIVISION
#: USING` list, with the paragraph functions private to the module. Callers
#: cannot reach into a program's internals, exactly as a COBOL `CALL`
#: cannot."* Every other name in this module is therefore underscore-private.
__all__: Final[tuple[str, ...]] = ("run",)


_LOG: Final[logging.Logger] = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
#  Field descriptors
#
#  Three provenances, because the frozen sources have three. Record fields the
#  bridge maps come from the generated data dictionary; the OTM4 layout comes
#  from the published purchase open-item record; and the working storage
#  `pl055` declares for itself is in no dictionary at all and is parsed from
#  its own picture clauses, each carrying the locator of the line it was read
#  from. Rule R-5 requires every descriptor to cite a dictionary key or a
#  source locator, and all three routes do.
# ---------------------------------------------------------------------------


def _by_name(record: str) -> dict[str, FieldDescriptor]:
    """Descriptors of one dictionary-backed copybook record, keyed lower-case.

    `descriptors_for_copybook_record` returns them in copybook order with the
    copybook's own capitalisation - `va-t-this` in one record and `Pa-Gl` in
    another - so the key is folded to make a lookup independent of a
    transcription choice the copybook author made forty years ago.
    """
    return {d.name.lower(): d for d in descriptors_for_copybook_record(record)}


#: copy "wsval.cob".               [purchase/pl055.cbl:L132]
#: `01 WS-Value-Record.` [copybooks/wsval.cob:L9], 66 bytes.
_VAL: Final[dict[str, FieldDescriptor]] = _by_name("WS-Value-Record")

#: copy "wsanal.cob".              [purchase/pl055.cbl:L133]
#: `01 WS-Analysis-Record.` [copybooks/wsanal.cob:L9], 36 bytes.
_ANL: Final[dict[str, FieldDescriptor]] = _by_name("WS-Analysis-Record")

#: copy "wssys4.cob".              [purchase/pl055.cbl:L234]
#: `01 System-Record-4.` [copybooks/wssys4.cob:L8], 1024 bytes.
_S4: Final[dict[str, FieldDescriptor]] = _by_name("System-Record-4")

#: A group descriptor carries no width of its own, so `MOVE` to a group takes
#: its length from the copybook. Both record sizes are stated by their own
#: authors: `*> record size 66 bytes ** 08/03/09` [copybooks/wsval.cob:L6] and
#: `*> 36 bytes 25/3/09` [copybooks/wsanal.cob:L6]. Independently derived:
#: WS-Value-Record = 3 + 6 + 24 + 3 + 3x4 (`pic 9(5) comp`) + 3x6
#: (`pic s9(8)v99 comp-3`) = 66; WS-Analysis-Record = 3 + 6 + 24 + 3 = 36.
_VALUE_RECORD_BYTES: Final[int] = 66
_ANALYSIS_RECORD_BYTES: Final[int] = 36

#: The four alphanumeric/display fields the group move at
#: [purchase/pl055.cbl:L452] actually carries, as 1-based `(offset:length)`
#: pairs into the 66-byte receiver. The six trailing numeric fields receive
#: SPACES from that move - a group move applies no picture clause to any part
#: of the receiver - which is precisely why the very next statement,
#: [purchase/pl055.cbl:L453-L454], zeroes all six in one go.
_VALUE_HEAD_LAYOUT: Final[tuple[tuple[str, int, int], ...]] = (
    ("va-code", 1, 3),
    ("va-gl", 4, 6),
    ("va-desc", 10, 24),
    ("va-print", 34, 3),
)

#: copy "plwsoi.cob".              [purchase/pl055.cbl:L121]
#: The 113-byte OTM4 header. Two lookups, because the copybook nests the ten
#: money fields inside `03 filler comp-3.` [copybooks/plwsoi.cob:L41] - a
#: GROUP filler whose subordinates are all named, which is the fact behind
#: divergence 5.
_OI: Final[dict[str, FieldDescriptor]] = dict(otm5_descriptors_of(OiHeader))
_OI_MONEY: Final[dict[str, FieldDescriptor]] = dict(otm5_descriptors_of(Filler1))
_OI_KEY: Final[dict[str, FieldDescriptor]] = dict(otm5_descriptors_of(OiKey))
_OI_BATCH: Final[dict[str, FieldDescriptor]] = dict(otm5_descriptors_of(OiBatch))
_OI_CUSTOMER: Final[dict[str, FieldDescriptor]] = dict(otm5_descriptors_of(OiCustomer))
_OI_SUPPLIER: Final[dict[str, FieldDescriptor]] = dict(otm5_descriptors_of(OiSupplier))


def _ws(clauses: str, name: str, line: int) -> FieldDescriptor:
    """A descriptor for one of `01 ws-data.`'s own fields.

    `01 ws-data.` [purchase/pl055.cbl:L161-L179] is program-local working
    storage. It reaches no table, so the bridge never saw it and the generated
    dictionary has no entry for it. The picture clause is therefore parsed
    from the declaring line and the descriptor carries that line as its
    `source_locator`, which is what rule R-5 asks of a field the dictionary
    cannot key.
    """
    return picture.descriptor_for(
        clauses, name=name, source_locator=f"purchase/pl055.cbl:L{line}"
    )


#: `03 Anal-Created pic 9 value zero.`          [purchase/pl055.cbl:L163]
_D_ANAL_CREATED: Final[FieldDescriptor] = _ws("pic 9", "Anal-Created", 163)
#: `03 save-code pic xxx.`                      [purchase/pl055.cbl:L164]
_D_SAVE_CODE: Final[FieldDescriptor] = _ws("pic xxx", "save-code", 164)
#: `03 ws-inv-amt pic s9(7)v99 comp-3 value zero.` [purchase/pl055.cbl:L165]
_D_INV_AMT: Final[FieldDescriptor] = _ws("pic s9(7)v99 comp-3", "ws-inv-amt", 165)
#: `03 work-2 pic s9(7)v99 comp-3 value zero.`  [purchase/pl055.cbl:L166]
_D_WORK_2: Final[FieldDescriptor] = _ws("pic s9(7)v99 comp-3", "work-2", 166)
#: `03 work-3 pic s9(5) comp value zero.`       [purchase/pl055.cbl:L167]
_D_WORK_3: Final[FieldDescriptor] = _ws("pic s9(5) comp", "work-3", 167)
#: The four money totals, [purchase/pl055.cbl:L168-L171].
_D_VAT_TOTALV: Final[FieldDescriptor] = _ws("pic s9(7)v99 comp-3", "ws-vat-totalv", 168)
_D_VATR_TOTALV: Final[FieldDescriptor] = _ws("pic s9(7)v99 comp-3", "ws-vatr-totalv", 169)
_D_CARR_TOTALV: Final[FieldDescriptor] = _ws("pic s9(7)v99 comp-3", "ws-carr-totalv", 170)
_D_DISC_TOTALV: Final[FieldDescriptor] = _ws("pic s9(7)v99 comp-3", "ws-disc-totalv", 171)
#: The four counts, [purchase/pl055.cbl:L172-L175]. Signed `comp`, so the
#: count arithmetic is integer arithmetic and never touches `Decimal`.
_D_VAT_TOTALT: Final[FieldDescriptor] = _ws("pic s9(5) comp", "ws-vat-totalt", 172)
_D_VATR_TOTALT: Final[FieldDescriptor] = _ws("pic s9(5) comp", "ws-vatr-totalt", 173)
_D_CARR_TOTALT: Final[FieldDescriptor] = _ws("pic s9(5) comp", "ws-carr-totalt", 174)
_D_DISC_TOTALT: Final[FieldDescriptor] = _ws("pic s9(5) comp", "ws-disc-totalt", 175)
#: `03 v-exists pic 9.`                         [purchase/pl055.cbl:L176]
_D_V_EXISTS: Final[FieldDescriptor] = _ws("pic 9", "v-exists", 176)
#: `03 WS-Term-Code pic 99.` [copybooks/wscall.cob:L10], widened from `pic 9`
#: on 14/11/25 [copybooks/wscall.cob:L4], which is why 8 fits it comfortably.
_D_TERM_CODE: Final[FieldDescriptor] = calling_data_descriptor_for("ws_term_code")

#: `77 prog-name pic x(15) value "PL055 (3.3.00)".` [purchase/pl055.cbl:L125]
_PROG_NAME: Final[str] = "PL055 (3.3.00)"

#: `01 Error-Messages.` [purchase/pl055.cbl:L215-L223]. Screen literals have
#: no database effect, so they survive only as log text (Agent Action Plan
#: section 0.3.4). `PL003` and `PL006` are the two acknowledgement prompts
#: whose `accept` is dropped.
_PL003: Final[str] = "PL003 Hit Return To Continue"
_PL006: Final[str] = "PL006 Note Details & Hit Return to continue"
_PL201: Final[str] = "PL201 Analyst records with desc, 'Emergency Name' created"
_PL202: Final[str] = "PL202 You will need to update these"
_PL203: Final[str] = "PL203 P.A. File Does Not Exist"
_PL204: Final[str] = "PL204 Error writing to Open Item 4 File "

#: The character images of the only two literals `pl055` compares against an
#: ALPHANUMERIC field, resolved once through the receiving descriptor rather
#: than written as Python literals. `il-type` is `pic x`
#: [copybooks/plwspinv2.cob:L63], so `if il-type not = 3`
#: [purchase/pl055.cbl:L329, L351] is an ALPHANUMERIC comparison against the
#: one-character image of the literal 3 - it is NOT numeric, and routing it
#: through `arithmetic.compare` would raise on any non-digit byte a `READ`
#: happens to deliver.
_IL_TYPE_3: Final[str] = move.move_alphanumeric(
    3, pinvoice_descriptor_for(IlInvoiceLine, "il_type")
)
#: `space` as the one-character image its receivers hold, for
#: [purchase/pl055.cbl:L340, L456, L495, L524].
_SPACE_1: Final[str] = move.move_figurative(move.SPACE, _VAL["va-second"])


class _CobolFilesModeUnsupportedError(RuntimeError):
    """`if FS-Cobol-Files-Used` was true, and that branch cannot be migrated.

    The block guarded by `if FS-Cobol-Files-Used` [purchase/pl055.cbl:L266-L290]
    does three things this migration cannot do:

        call  "CBL_CHECK_FILE_EXIST" using File-15 File-Info
                                             [purchase/pl055.cbl:L267-L269]
        call  "sl070" using ws-calling-data system-record to-day file-defs
                                             [purchase/pl055.cbl:L273-L277]
        call  "CBL_CHECK_FILE_EXIST" using File-15 File-Info
                                             [purchase/pl055.cbl:L278-L279]

    `CBL_CHECK_FILE_EXIST` is a GnuCOBOL library routine and `sl070` is a
    COBOL program that is NOT one of the twelve in scope (Agent Action Plan
    section 0.2.2), so no Python module implements it. Rule R-1 forbids
    invoking COBOL at runtime, which rules out calling either.

    THE BRANCH IS UNREACHABLE IN THE CONFIGURATION THIS MIGRATION TARGETS.
    `88 FS-Cobol-Files-Used value zero.` [copybooks/wssystem.cob:L113] and
    `88 FS-RDBMS-Used value 1.` [copybooks/wssystem.cob:L116] are alternative
    values of one field, `07 File-System-Used pic 9.`
    [copybooks/wssystem.cob:L112]; the migrated cycle runs against MySQL, so
    the field is 1 and the condition is false.

    So the gate is reproduced faithfully and data-driven, and this is raised
    inside it. Silently skipping the block would hide a scenario that had
    configured indexed files; stubbing it as a no-op would claim a behaviour
    that was never measured; emulating `sl070` would invent one. Raising says
    exactly what is true - the configuration is outside the migrated surface.

    A curiosity worth recording rather than acting on: `pl055` is a PURCHASE
    program and the program it calls here is `sl070`, the SALES analysis and
    value file creator, not `pl070`. `sl055` makes the identical call
    [sales/sl055.cbl:L332], and since `sl070` creates the shared Analysis and
    Value files that both ledgers read, it is very likely deliberate. It is
    NOT "corrected" to `pl070`.
    """


@dataclass
class _OpenItemFile4:
    """`open-item-file-4` - the OTM4 extract, an ordered in-process sequence.

        select  open-item-file-4  assign        file-28
                                  access        sequential
                                  status        fs-reply.
                                             [copybooks/seloi4.cob:L1-L4]
        fd  open-item-file-4.
        01  open-item-record-4  pic x(113).  [copybooks/fdoi4.cob:L1-L2]

    A TRANSIENT WORK FILE, NOT A TABLE. `copy "seloi4.cob"` carries its
    author's own note - `*> Temp file only for i/p to pl060.`
    [purchase/pl055.cbl:L109] - and `file-28` is `"openitm4.dat"`
    [copybooks/file28.cob:L1]. It reaches no schema table, appears in no table
    dump, and is consumed by `pl060` [purchase/pl060.cbl:L421-L425]. It is
    therefore modelled the way the Agent Action Plan models the General Ledger
    work files: an ordered sequence with the same record layout and the same
    ordering guarantee, and nothing else.

    WHY THIS IS MODULE-PRIVATE RATHER THAN `workfiles.LineSequentialWorkFile`.
    `pl055` opens this file with `open extend` [purchase/pl055.cbl:L301] -
    append, preserving what is already there. The published work-file class
    has no `open_extend`, its `OpenMode` vocabulary is exactly
    `CLOSED`/`INPUT`/`OUTPUT`, and its only route into a writable state is
    `open_output`, which truncates. Reaching into its private record list to
    add an extend would be a layering violation dressed up as reuse. So the
    file is declared here, and the published `FS_REPLY_OK`, `OpenMode` and
    `WorkFileError` are reused so that no parallel status vocabulary is
    invented alongside them.

    THE STATUS FIELD IS SHARED WITH THE DATA-ACCESS LAYER, DELIBERATELY.
    `seloi4.cob:L4` declares `status fs-reply`, and `Fs-Reply`
    [copybooks/wsfnctn.cob:L25] is the very field every facade verb also
    writes. That sharing is not incidental: it is what lets
    [purchase/pl055.cbl:L302] and [purchase/pl055.cbl:L588] test `fs-reply`
    straight after a native `OPEN` and `WRITE`. Callers pass the same
    `FileAccess` this program hands the facade, so the field is one field.

    AMBIGUITY Q-PL055-5 - the `OI-Header` / `open-item-record-4` storage
    relationship, and what a reader of the sequence actually sees. Divergence
    13 is that [purchase/pl055.cbl:L587] writes `open-item-record-4` while
    [purchase/pl055.cbl:L547] initialises `OI-Header`, which reads at first
    glance as a write of an area nothing filled. It is not, and the evidence is
    structural: in `pl055` BOTH `copy "fdoi4.cob"` [purchase/pl055.cbl:L120] and
    `copy "plwsoi.cob"` [purchase/pl055.cbl:L121] sit inside the FILE SECTION
    under one FD, so `01 open-item-record-4 pic x(113)`
    [copybooks/fdoi4.cob:L2] and `01 OI-Header` [copybooks/plwsoi.cob:L9] are
    two `01` descriptions of THE SAME 113-byte record area - the second `01`
    under an FD is an alternative description, not a second buffer - and
    `OI-Header`'s fields sum to exactly 113. The divergence is therefore
    COSMETIC in `pl055`, and this class models the one area. `pl060` proves the
    contrast: it copies `plwsoi.cob` into WORKING-STORAGE
    [purchase/pl060.cbl:L152] and consequently needs an explicit `move
    open-item-record-4 to oi-header` [purchase/pl060.cbl:L428] that `pl055` has
    no counterpart to.
    WHAT REMAINS FOR THE ORACLE: the sequence is handed to `pl060` as OBJECTS
    here and as 113 BYTES there, so any field whose Python value can render to
    more than one byte image - and the `FILLER` bytes that
    [purchase/pl055.cbl:L547] does not reset, per Q-PL055-1 - could in principle
    be read back differently by the two programs. Measure a round trip through
    the compiled pair before treating the two representations as
    interchangeable.
    """

    file_access: FileAccess
    _records: list[OiHeader] = dataclass_field(default_factory=list)
    _open_mode: OpenMode = OpenMode.CLOSED

    @property
    def records(self) -> tuple[OiHeader, ...]:
        """The sequence as written, in insertion order - what `pl060` reads."""
        return tuple(self._records)

    def __len__(self) -> int:
        return len(self._records)

    def open_extend(self) -> None:
        """`open extend open-item-file-4.`   [purchase/pl055.cbl:L301]

        Append: existing records survive and the write position is the end.
        On a sequential work file this always succeeds once the sequence
        exists, so `fs-reply` is set to zero and the fallback at
        [purchase/pl055.cbl:L302-L304] does not fire. It is still transcribed,
        because whether it fires is a property of the run and not of the code.
        """
        self._open_mode = OpenMode.OUTPUT
        self.file_access.fs_reply = FS_REPLY_OK

    def open_output(self) -> None:
        """`open output open-item-file-4.`   [purchase/pl055.cbl:L304]

        Truncate: the sequence is emptied, which is what `OPEN OUTPUT` on a
        sequential file means and what makes the fallback a create.
        """
        self._records.clear()
        self._open_mode = OpenMode.OUTPUT
        self.file_access.fs_reply = FS_REPLY_OK

    def write(self, record: OiHeader) -> None:
        """`write open-item-record-4.`       [purchase/pl055.cbl:L587]

        Appends a SNAPSHOT. `OI-Header` is one 113-byte record area that the
        extract paragraph rebuilds for every invoice, so storing the live
        object would leave every element of the sequence pointing at the last
        invoice written. The copy is what makes the sequence a file.
        """
        if self._open_mode is not OpenMode.OUTPUT:
            raise WorkFileError(
                "write to open-item-file-4 while it is not open for output: "
                f"mode is {self._open_mode.value}"
            )
        self._records.append(_copy_oi_header(record))
        self.file_access.fs_reply = FS_REPLY_OK

    def close(self) -> None:
        """`close open-item-file-4.`         [purchase/pl055.cbl:L423]

        Closes without discarding: the records are the deliverable, and
        `pl060` opens the same file for input afterwards.
        """
        self._open_mode = OpenMode.CLOSED
        self.file_access.fs_reply = FS_REPLY_OK


def _copy_oi_header(source: OiHeader) -> OiHeader:
    """A deep copy of one `OI-Header`, group by group.

    Written out rather than deep-copied generically so that a reader can see
    that all seventeen top-level fields of [copybooks/plwsoi.cob:L9-L64] are
    carried, including the three nested groups and the ten money fields inside
    `03 filler comp-3.` [copybooks/plwsoi.cob:L41].
    """
    return OiHeader(
        oi_key=OiKey(
            oi_customer=OiCustomer(oi_supplier=source.oi_key.oi_customer.oi_supplier),
            oi_invoice=source.oi_key.oi_invoice,
        ),
        oi_date=source.oi_date,
        oi_batch=OiBatch(
            oi_b_nos=source.oi_batch.oi_b_nos, oi_b_item=source.oi_batch.oi_b_item
        ),
        oi_type=source.oi_type,
        oi_ref=source.oi_ref,
        oi_order=source.oi_order,
        oi_hold_flag=source.oi_hold_flag,
        oi_unapl=source.oi_unapl,
        filler_1=Filler1(
            oi_p_c=source.filler_1.oi_p_c,
            oi_net=source.filler_1.oi_net,
            oi_approp=source.filler_1.oi_approp,
            oi_extra=source.filler_1.oi_extra,
            oi_carriage=source.filler_1.oi_carriage,
            oi_vat=source.filler_1.oi_vat,
            oi_discount=source.filler_1.oi_discount,
            oi_e_vat=source.filler_1.oi_e_vat,
            oi_c_vat=source.filler_1.oi_c_vat,
            oi_paid=source.filler_1.oi_paid,
        ),
        oi_status=source.oi_status,
        oi_deduct_days=source.oi_deduct_days,
        oi_deduct_amt=source.oi_deduct_amt,
        oi_deduct_vat=source.oi_deduct_vat,
        oi_days=source.oi_days,
        oi_cr=source.oi_cr,
        oi_applied=source.oi_applied,
        oi_date_cleared=source.oi_date_cleared,
    )


#: The only group items in the three `plwspinv2.cob` views, named explicitly
#: rather than discovered, so that a reader can check the list against the
#: copybook: `03 Invoice-Key.` [copybooks/plwspinv2.cob:L11], `03 ih-supplier.`
#: [copybooks/plwspinv2.cob:L24] and `03 ih-fig comp-3.`
#: [copybooks/plwspinv2.cob:L31]. `Invoice-Line` has none.
_PINVOICE_GROUPS: Final[dict[type, dict[str, type]]] = {
    WsPInvoiceRecord: {"invoice_key": InvoiceKey},
    IhInvoiceHeader: {"ih_supplier": IhSupplier2, "ih_fig": IhFig2},
    IlInvoiceLine: {},
    # The three subordinate groups themselves contain only elementary items -
    # `05 Invoice-Nos` / `05 Item-Nos` [copybooks/plwspinv2.cob:L12-L13],
    # `05 ih-nos` / `05 ih-check` [copybooks/plwspinv2.cob:L25-L26] and the
    # eight `05 ih-...` money fields [copybooks/plwspinv2.cob:L32-L39] - so the
    # recursion terminates here. Listed explicitly rather than defaulted so that
    # a NEW group added to the copybook fails loudly instead of being skipped.
    InvoiceKey: {},
    IhSupplier2: {},
    IhFig2: {},
}


def _initial_pinvoice_view(record_class: type) -> Any:
    """A `plwspinv2.cob` view with every field at its category's initial value.

    `copy "plwspinv2.cob"` [purchase/pl055.cbl:L135] declares one 100-byte
    working-storage area under three names - the base record and its two
    redefinitions - and NONE of its fields carries a `VALUE` clause. In COBOL
    that area's initial content is whatever the run unit left there, and `pl055`
    never reads it before its first `PInvoice-Read-Next`
    [purchase/pl055.cbl:L307] fills it. So an initial value is needed only to
    have an object at all, and the category default - zero for numeric, space
    for alphanumeric - is chosen for the same reason the COBOL's own loaders
    choose it: it is the one value that cannot be mistaken for data.

    Every field is set through `move_figurative` under its OWN descriptor, so a
    packed field gets `Decimal("0.00")` and a `pic x(10)` gets ten spaces rather
    than one. Group items recurse through `_PINVOICE_GROUPS`.
    """
    values: dict[str, Any] = {}
    for attribute, nested_class in _PINVOICE_GROUPS[record_class].items():
        values[attribute] = _initial_pinvoice_view(nested_class)
    for attribute in _pinvoice_attributes(record_class):
        if attribute in values:
            continue
        descriptor = pinvoice_descriptor_for(record_class, attribute)
        figurative = move.ZERO if descriptor.is_numeric else move.SPACE
        values[attribute] = move.move_figurative(figurative, descriptor)
    return record_class(**values)


def _pinvoice_attributes(record_class: type) -> tuple[str, ...]:
    """The dataclass attribute names of one `plwspinv2.cob` view, in order."""
    return tuple(f.name for f in dataclasses_fields(record_class))


@dataclass
class _FacadeContext:
    """The operands the three handler dispatch paragraphs pass, in their order.

        acas013.  move 1 to File-Key-No.
                  call "acas013" using System-Record WS-Value-Record
                       File-Access File-Defs ACAS-DAL-Common-Data.
                                    [copybooks/Proc-ACAS-FH-Calls.cob:L90-L96]
        acas015.  ... WS-Analysis-Record ...
                                   [copybooks/Proc-ACAS-FH-Calls.cob:L108-L114]
        acas026.  ... WS-PInvoice-Record ...
                                   [copybooks/Proc-ACAS-FH-Calls.cob:L156-L162]

    One object rather than three parameter lists, because the Agent Action Plan
    fixes the facade call form as a single argument - section 0.4.3 gives
    `perform GL-Batch-Read-Next` becoming `facade.gl_batch_read_next(ctx)`.
    The fields are the union of the three `using` lists, named after the COBOL
    operands, so a reviewer can diff them against the copybook.

    `WS-PInvoice-Record` is carried alongside its two redefinitions because
    `plwspinv2.cob` describes ONE record area three ways - `Invoice-Header
    redefines WS-PInvoice-Record` [copybooks/plwspinv2.cob:L21] and
    `Invoice-Line redefines WS-PInvoice-Record`
    [copybooks/plwspinv2.cob:L56] - and `pl055` reads through all three: the
    base record is what the handler is handed, `ih-test`
    [copybooks/plwspinv2.cob:L23] tells a header from a line, and then either
    the `ih-` or the `il-` view is used. A facade honouring this contract keeps
    the three views coherent across a read and a rewrite, exactly as
    redefinition does in COBOL.

    AMBIGUITY Q-PL055-7 - the shape of the single argument the facade verbs take.
    `acas_posting/dal/facade.py` is generated in this same batch and does not
    exist while this module is written, so its parameter object cannot be
    imported and bound against. What IS fixed is the CALL FORM: Agent Action Plan
    section 0.4.3 gives `perform GL-Batch-Read-Next` becoming
    `facade.gl_batch_read_next(ctx)` - one verb function, one context argument -
    and the operand LIST is fixed by the copybook, at
    [copybooks/Proc-ACAS-FH-Calls.cob:L90-L96], [L108-L114] and [L156-L162]. This
    class is therefore that operand list under the COBOL's own names, and the
    facade is injected rather than reached for, so a caller can bind whichever
    context type the generated module publishes without this module changing.
    Confirm the field names against the generated facade once it exists.

    AMBIGUITY Q-PL055-8 - which purchase-invoice record shape the handler wants.
    `pl055` copies `plwspinv2.cob` [purchase/pl055.cbl:L135], the FLAT hundred-
    byte description whose header view is `Invoice-Header`
    [copybooks/plwspinv2.cob:L21]; but `acas_posting/dal/acas026_pinvoice.py`
    dispatches on `PInvoiceHeader`, the NESTED description that
    `copybooks/plwspinv.cob` declares and that the header-plus-lines table split
    is modelled from. The two are descriptions of the same rows, and the COBOL
    resolves the difference by having each caller copy the description it wants -
    `acas026` itself is handed whatever its caller's `WS-PInvoice-Record`
    happens to be. Reproduced the same way here: this module holds the flat
    views its own `copy` declares and the facade owns any translation to the
    handler's shape, because inventing a conversion in a program module would
    put a data-access concern in `programs/`. Measure a read-then-rewrite round
    trip through the compiled `acas026` to confirm the two descriptions agree
    field for field before relying on it.
    """

    system_record: SystemRecord
    ws_value_record: WsValueRecord
    ws_analysis_record: WsAnalysisRecord
    ws_pinvoice_record: WsPInvoiceRecord
    invoice_header: IhInvoiceHeader
    invoice_line: IlInvoiceLine
    file_access: FileAccess
    file_defs: FileDefs
    acas_dal_common_data: AcasDalCommonData

    @property
    def invoice_fig(self) -> IhFig2:
        """`03 ih-fig comp-3.`   [copybooks/plwspinv2.cob:L31]

        The eight money fields of the header live in a subordinate group, so
        they are reached through it rather than duplicated beside it - a second
        reference would be a second copy of one 113-byte record area, and
        keeping the views coherent is the whole point of a redefinition.
        """
        return self.invoice_header.ih_fig


#: The entity work area each dispatch paragraph names as its SECOND operand,
#: keyed by the verb-name prefix that reaches it. The three `using` lists this
#: program's `_FacadeContext` is the union of, from
#: `copybooks/Proc-ACAS-FH-Calls.cob`:
#:
#:     acas013.  call "acas013" using System-Record WS-Value-Record
#:                    File-Access File-Defs ACAS-DAL-Common-Data.   [:L90-L96]
#:     acas015.  ...                        WS-Analysis-Record ...  [:L108-L114]
#:     acas026.  ...                        WS-PInvoice-Record ...  [:L156-L162]
_ENTITY_RECORD: Final[dict[str, str]] = {
    "value": "ws_value_record",
    "analysis": "ws_analysis_record",
    "pinvoice": "ws_pinvoice_record",
}


class _BoundFacade:
    """`_FacadeContext` on this side, `facade.FacadeContext` on the other.

    THIS RESOLVES AMBIGUITY Q-PL055-7, which asked what shape of single argument
    the generated facade verbs take and instructed a reader to confirm the field
    names against the facade once it existed. Confirmed: the CALL FORM assumed by
    `_FacadeContext` is right - one verb function, one context argument - and the
    OPERAND LIST is right, being the copybook's five in the copybook's order. The
    only difference is that the facade publishes them as its own
    `facade.FacadeContext(system, record, file_access, file_defs, dal_common)`,
    carrying the one record area the verb is for, where this module names all
    three after the COBOL operands and lets the verb pick.

    So `_FacadeContext` stays exactly as it is - it is this module's record of the
    union of the three `using` lists, which is what makes them diffable against
    the copybook - and the pick happens here, at the boundary. That is precisely
    where `_FacadeContext`'s own docstring says it should: "the facade is injected
    rather than reached for, so a caller can bind whichever context type the
    generated module publishes without this module changing", and "the facade owns
    any translation to the handler's shape, because inventing a conversion in a
    program module would put a data-access concern in `programs/`". `run`'s
    `facade` parameter still overrides this binding, so a test double remains
    structurally sufficient.

    AMBIGUITY Q-PL055-8 IS NOT TOUCHED and remains open. `ws_pinvoice_record` is
    handed over as the base record area, exactly as `acas026`'s dispatch paragraph
    passes `WS-PInvoice-Record` [copybooks/Proc-ACAS-FH-Calls.cob:L156-L162]; the
    flat-versus-nested question of which purchase-invoice description the handler
    wants is the facade's and the handler's, and is still to be settled by
    measuring a read-then-rewrite round trip through the compiled `acas026`.

    Nothing about the operation changes. `File-Access` is passed by reference, so
    each verb writes `We-Error` and `Fs-Reply` into the very block this context
    holds [copybooks/wsfnctn.cob:L23-L38] - the block every inline reply test in
    this module reads. One `PERFORM` is one call, in source order; nothing is
    reordered, batched, deferred, coalesced or cached.
    """

    __slots__ = ("_facade",)

    def __init__(self, facade_module: ModuleType) -> None:
        self._facade = facade_module

    def __getattr__(self, verb: str) -> Any:
        """Bind one entity-named verb, resolving its record area by prefix."""
        entity = next(
            (name for name in _ENTITY_RECORD if verb.startswith(f"{name}_")), None
        )
        if entity is None:
            raise AttributeError(
                f"pl055 performs no facade verb {verb!r}; it copies "
                f'copy "Proc-ACAS-FH-Calls.cob". [purchase/pl055.cbl:L646] and '
                f"reaches only the Value, Analysis and PInvoice entities"
            )
        target = getattr(self._facade, verb)
        record_attribute = _ENTITY_RECORD[entity]

        def _perform(ctx: _FacadeContext, /) -> None:
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


@dataclass
class _Pl055State:
    """Everything `pl055` holds between statements.

    `01 ws-data.` [purchase/pl055.cbl:L161-L179] and `01 ws-date-formats.`
    [purchase/pl055.cbl:L182-L203] are its own working storage; the records and
    `File-Access` arrive through linkage or the facade context. Grouping them
    in one object is a Python necessity - COBOL working storage is reachable
    from every paragraph of a program and Python locals are not - and it is
    NOT a behavioural change: no field is added, renamed or given a value the
    COBOL does not give it.
    """

    ctx: _FacadeContext
    facade: ModuleType | _BoundFacade
    open_item_file_4: _OpenItemFile4
    ws_calling_data: WsCallingData
    system_record_4: SystemRecord4
    to_day: str
    ws_date_formats: WsDateFormats

    #: `03 Anal-Created pic 9 value zero.`   [purchase/pl055.cbl:L163]
    anal_created: int = 0
    #: `03 save-code pic xxx.`               [purchase/pl055.cbl:L164]
    save_code: str = ""
    #: `03 ws-inv-amt ... value zero.`       [purchase/pl055.cbl:L165]
    ws_inv_amt: Decimal = Decimal("0.00")
    #: `03 work-2 ... value zero.`           [purchase/pl055.cbl:L166]
    work_2: Decimal = Decimal("0.00")
    #: `03 work-3 ... value zero.`           [purchase/pl055.cbl:L167]
    work_3: int = 0
    #: The four money totals.                [purchase/pl055.cbl:L168-L171]
    ws_vat_totalv: Decimal = Decimal("0.00")
    ws_vatr_totalv: Decimal = Decimal("0.00")
    ws_carr_totalv: Decimal = Decimal("0.00")
    ws_disc_totalv: Decimal = Decimal("0.00")
    #: The four counts.                      [purchase/pl055.cbl:L172-L175]
    ws_vat_totalt: int = 0
    ws_vatr_totalt: int = 0
    ws_carr_totalt: int = 0
    ws_disc_totalt: int = 0
    #: `03 v-exists pic 9.`                  [purchase/pl055.cbl:L176]
    #: Declared with NO `VALUE` clause, so its initial content is whatever the
    #: run-unit left there. Every path that reads it assigns it first -
    #: [purchase/pl055.cbl:L319] and [purchase/pl055.cbl:L506] - so zero is a
    #: safe start and not an added initialisation.
    v_exists: int = 0
    #: `77 Exception-Msg pic x(25) value spaces.` [purchase/pl055.cbl:L126].
    #: Filled by `a01-Eval-Status` [purchase/pl055.cbl:L629-L632] and read at
    #: exactly one place, the failed-write display [purchase/pl055.cbl:L592].
    exception_msg: str = " " * 25
    #: `01 OI-Header.` [copybooks/plwsoi.cob:L9], which in `pl055` IS
    #: `open-item-record-4` - the same 113-byte FD area under two names.
    oi_header: OiHeader = dataclass_field(default_factory=lambda: _initialise_oi_header())


def _initialise_oi_header() -> OiHeader:
    """`initialise OI-Header.`   [purchase/pl055.cbl:L547]

    ⭐ DIVERGENCE 5, THE BEHAVIOURAL ONE, PRESERVED AS WRITTEN. `pl055` spells
    the verb the British way and, critically, omits the `WITH FILLER` phrase
    that its sales counterpart carries:

        initialise OI-Header.   *> 07/01/18  JIC   [purchase/pl055.cbl:L547]
        initialize oi-header with filler.          [sales/sl055.cbl:L635]

    ⛔ Rule R-3 forbids adding `WITH FILLER` "for consistency", and rule R-4
    forbids treating the omission as a defect to repair. It stays omitted.

    WHAT THE OMISSION ACTUALLY COSTS HERE, MEASURED. Without `WITH FILLER`,
    `INITIALIZE` leaves ELEMENTARY items named `FILLER` untouched. The purchase
    open-item layout has NO elementary `FILLER`: its only filler is the GROUP
    `03 filler comp-3.` [copybooks/plwsoi.cob:L41], every one of whose ten
    subordinates is named - `OI-P-C` through `OI-Paid`
    [copybooks/plwsoi.cob:L42-L51] - and named subordinates of a filler group
    are ordinary elementary items that `INITIALIZE` does process. So for THIS
    layout the two spellings are expected to agree, and the divergence is one
    of source text rather than of stored bytes.

    # AMBIGUITY Q-PL055-1 - the observable effect of the missing `WITH FILLER`.
    # "Expected to agree" is a reading of the standard, not a measurement, and
    # a filler GROUP whose subordinates are packed decimal is exactly the case
    # a compiler might treat its own way. The compiled program decides it
    # (rule R-6): initialise a known-dirty 113-byte area both ways and compare
    # the written record byte for byte. Recorded, not guessed.

    `oi-approp` is NOT initialised, which is not an oversight either.
    `INITIALIZE` skips an item carrying a `REDEFINES` clause, and `05
    OI-Approp redefines OI-Net` [copybooks/plwsoi.cob:L44] carries one. It
    shares storage with `OI-Net`, which IS initialised, so the shared bytes
    end at zero and the redefining view reads zero with it - modelled here by
    giving it whatever `oi-net` was given rather than by initialising it
    independently.
    """
    zero_net = move.move_figurative(move.ZERO, _OI_MONEY["oi_net"])
    return OiHeader(
        oi_key=OiKey(
            oi_customer=OiCustomer(
                oi_supplier=OiSupplier(
                    oi_nos=move.move_figurative(move.SPACE, _OI_SUPPLIER["oi_nos"]),
                    oi_check=move.move_figurative(move.ZERO, _OI_SUPPLIER["oi_check"]),
                )
            ),
            oi_invoice=move.move_figurative(move.ZERO, _OI_KEY["oi_invoice"]),
        ),
        oi_date=move.move_figurative(move.ZERO, _OI["oi_date"]),
        oi_batch=OiBatch(
            oi_b_nos=move.move_figurative(move.ZERO, _OI_BATCH["oi_b_nos"]),
            oi_b_item=move.move_figurative(move.ZERO, _OI_BATCH["oi_b_item"]),
        ),
        oi_type=move.move_figurative(move.ZERO, _OI["oi_type"]),
        oi_ref=move.move_figurative(move.SPACE, _OI["oi_ref"]),
        oi_order=move.move_figurative(move.SPACE, _OI["oi_order"]),
        oi_hold_flag=move.move_figurative(move.SPACE, _OI["oi_hold_flag"]),
        oi_unapl=move.move_figurative(move.SPACE, _OI["oi_unapl"]),
        filler_1=Filler1(
            oi_p_c=move.move_figurative(move.ZERO, _OI_MONEY["oi_p_c"]),
            oi_net=zero_net,
            # `05 OI-Approp redefines OI-Net`  [copybooks/plwsoi.cob:L44]
            oi_approp=zero_net,
            oi_extra=move.move_figurative(move.ZERO, _OI_MONEY["oi_extra"]),
            oi_carriage=move.move_figurative(move.ZERO, _OI_MONEY["oi_carriage"]),
            oi_vat=move.move_figurative(move.ZERO, _OI_MONEY["oi_vat"]),
            oi_discount=move.move_figurative(move.ZERO, _OI_MONEY["oi_discount"]),
            oi_e_vat=move.move_figurative(move.ZERO, _OI_MONEY["oi_e_vat"]),
            oi_c_vat=move.move_figurative(move.ZERO, _OI_MONEY["oi_c_vat"]),
            oi_paid=move.move_figurative(move.ZERO, _OI_MONEY["oi_paid"]),
        ),
        oi_status=move.move_figurative(move.ZERO, _OI["oi_status"]),
        oi_deduct_days=move.move_figurative(move.ZERO, _OI["oi_deduct_days"]),
        oi_deduct_amt=move.move_figurative(move.ZERO, _OI["oi_deduct_amt"]),
        oi_deduct_vat=move.move_figurative(move.ZERO, _OI["oi_deduct_vat"]),
        oi_days=move.move_figurative(move.ZERO, _OI["oi_days"]),
        oi_cr=move.move_figurative(move.ZERO, _OI["oi_cr"]),
        oi_applied=move.move_figurative(move.SPACE, _OI["oi_applied"]),
        oi_date_cleared=move.move_figurative(move.ZERO, _OI["oi_date_cleared"]),
    )


#
#  mainline section.   [purchase/pl055.cbl:L246]
#


def _mainline(st: _Pl055State) -> None:
    """`mainline section.`   [purchase/pl055.cbl:L246-L304]

    Opens the four files and falls through into the read loop. Everything that
    survives migration is in the last fourteen lines; the first seventeen are
    terminal geometry, screen environment and a branch that cannot run.

    THE TERMINAL GEOMETRY IS DROPPED, AND IT IS NOT A CLOCK READ.

        accept   ws-env-lines   from lines.        [purchase/pl055.cbl:L249]
        subtract 1 from ws-lines giving ws-23-lines.
                                                   [purchase/pl055.cbl:L255]
        set ENVIRONMENT "COB_SCREEN_EXCEPTIONS" to "Y".
                                                   [purchase/pl055.cbl:L257]

    `FROM LINES` reports the height of the terminal. `ws-lines` and
    `ws-23-lines` [purchase/pl055.cbl:L178-L179] are then used only to place
    `display` and `accept` on screen rows [purchase/pl055.cbl:L590-L594], so
    they leave with the presentation layer, and the one subtraction that
    computes them is the only arithmetic in `pl055` that this migration does
    not carry. Rule R-6 is untouched: `purchase/pl055.cbl` performs ZERO clock
    reads and takes its date entirely through `to-day`.

    THE VALUE FILE IS OPENED TWICE, AND NEITHER OPEN IS CHECKED - divergence 11.

        perform  Value-Open.                       [purchase/pl055.cbl:L261]
        ...
        perform  Value-Open.                       [purchase/pl055.cbl:L299]

    The sales program replaces the first of these with an existence probe -
    open input, test the reply, close and re-open output if it failed, then
    close again [sales/sl055.cbl:L319-L324]. `pl055` just opens, twice, and
    tests nothing either time. Both calls are issued here, in place. Rule R-3
    and Agent Action Plan section 0.8.4 - *"Any performance work is therefore
    out of scope by construction, not merely unrequested."* - and a redundant
    open is exactly what an optimiser would remove.

    Args:
        st: The program's state, carrying the linkage records, the facade and
            the OTM4 sequence.

    Raises:
        _CobolFilesModeUnsupportedError: If `FS-Cobol-Files-Used` is true. See
            that class for why the branch cannot be migrated and why it cannot
            arise in the configuration this migration targets.
    """
    # 261  perform  Value-Open.
    # FINDING / DIVERGENCE 11 [purchase/pl055.cbl:L261] vs
    # [sales/sl055.cbl:L319-L324] - the sales program probes for the file's
    # existence here and this one does not. No reply test follows, so a failed
    # open is not noticed until the first read. Preserved.
    st.facade.value_open(st.ctx)

    # 266  if       FS-Cobol-Files-Used
    # The gate is reproduced, and reproduced DATA-DRIVEN through the condition
    # name so the decision is made at run time from `07 File-System-Used pic 9.`
    # [copybooks/wssystem.cob:L112] exactly as the COBOL makes it - not decided
    # here by an assumption about how the run is configured.
    #
    # AMBIGUITY Q-PL055-6 - does any scenario ever set `FS-Cobol-Files-Used`?
    # `88 FS-Cobol-Files-Used value zero.` [copybooks/wssystem.cob:L113] and
    # `88 FS-RDBMS-Used value 1.` [copybooks/wssystem.cob:L116] are two states of
    # ONE column, `File-System-Used`, and that column is seeded from
    # `system.dat` through `systemLD`. Which value the mandated scenarios carry
    # is therefore a property of the seed, not of this program, and it decides
    # whether the branch below is dead code or the whole of the run: if a seed
    # ships zero, the compiled `pl055` performs two file-existence checks and may
    # call `sl070`, and the Python module raises instead. Establish the seeded
    # value for every scenario against the oracle before treating the raise as
    # unreachable. ⛔ Until then, do NOT weaken the raise into a warning or a
    # no-op - a silent skip would make a genuinely divergent configuration look
    # like a clean run.
    if condition_names.evaluate(
        "FS-Cobol-Files-Used",
        st.ctx.system_record.system_data_block.rdbms_flat_statuses.file_system_used,
    ):
        # 286  move 8 to WS-Term-Code
        # Set BEFORE raising, so the observable consequence the COBOL leaves on
        # its abort path is present for any caller that catches the error. The
        # COBOL reaches this only after two failed existence checks
        # [purchase/pl055.cbl:L270, L280]; here it is unconditional within the
        # gate, because the checks themselves cannot be performed.
        st.ws_calling_data.ws_term_code = move.move(8, _D_TERM_CODE)
        # 287  goback
        # FINDING [purchase/purchase.cbl:L704-L705] - term code 8 makes the
        # shared dispatch paragraph `go to overrewrite`, which abandons the
        # `perform load000.` return at [purchase/purchase.cbl:L760] and ends the
        # menu program, so `pl060` never runs. This CORRECTS the Agent Action
        # Plan, which concludes the term code has no gating effect in Purchase.
        raise _CobolFilesModeUnsupportedError(
            "purchase/pl055.cbl:L266-L290 requires call "
            '"CBL_CHECK_FILE_EXIST" and call "sl070"; sl070 is out of scope '
            "per Agent Action Plan section 0.2.2 and rule R-1 forbids "
            "invoking COBOL at runtime. This branch is unreachable in the "
            "RDBMS configuration the migration targets, where "
            "File-System-Used is 1 (FS-RDBMS-Used) and not zero. "
            "WS-Term-Code has been set to 8 as the COBOL abort path does."
        )

    # 291  move     1 to File-Key-No.
    st.ctx.file_access.logging_data.file_key_no = 1

    # 293  display  prog-name at 0101 ...
    # 294  display  "Invoice Post Extract" at 0133 ...
    # Screen output with no database effect becomes a log record and must not
    # alter control flow (Agent Action Plan section 0.3.4).
    _LOG.info("%s  Invoice Post Extract", _PROG_NAME)

    # 295  perform  zz070-Convert-Date.
    _zz070_convert_date(st)

    # 296  display  ws-date at 0171 ...
    _LOG.info("run date %s", st.ws_date_formats.ws_date)

    # 298  perform  PInvoice-Open.
    st.facade.pinvoice_open(st.ctx)
    # 299  perform  Value-Open.
    # The SECOND of the two unchecked opens - divergence 11.
    st.facade.value_open(st.ctx)
    # 300  perform  Analysis-Open.
    st.facade.analysis_open(st.ctx)

    # 301  open     extend  open-item-file-4.
    st.open_item_file_4.open_extend()
    # 302  if       fs-reply not = zero
    # The extend-then-fallback idiom: append if you can, otherwise create.
    if st.ctx.file_access.fs_reply != FsReply.SUCCESS:
        # 303           close open-item-file-4
        st.open_item_file_4.close()
        # 304           open output open-item-file-4.
        st.open_item_file_4.open_output()

    # FALL-THROUGH into `read-loop.` [purchase/pl055.cbl:L306]. `mainline` has
    # no terminating `exit section.`, so control simply arrives at the next
    # paragraph - recorded in the traceability footer as a fall-through.
    _read_loop(st)


#
#  read-loop.   [purchase/pl055.cbl:L306]
#


def _read_loop(st: _Pl055State) -> None:
    """`read-loop.`   [purchase/pl055.cbl:L306-L360]

    Walks the purchase-invoice file and accumulates value-analysis totals for
    every LINE record whose analysis group it can find or create.

    ⭐ DIVERGENCE 3 - THIS IS A `GO TO` LOOP, NOT AN INLINE `PERFORM`. The
    maintainer modernised the sales extract - `perform until FS-Reply = 10`
    with `exit perform` and `exit perform cycle`, carrying its own note *"changed
    18/01/25 for clean up using inline perform"* [sales/sl055.cbl:L365] - and
    never came back to this one. `pl055` still transfers with four explicit
    `go to read-loop` statements [purchase/pl055.cbl:L315, L341, L347, L360].
    The `while True` below is the class-1 translation of those four, and the
    single `break` is the class-2 translation of [purchase/pl055.cbl:L309].

    ⭐⭐ DIVERGENCE 4 - THE EXIT CONDITION IS `NOT = ZERO`, NOT `= 10`.

        if       FS-Reply not = zero               [purchase/pl055.cbl:L308]
        if       fs-reply = 10                     [sales/sl055.cbl:L367]

    ⛔ This is the divergence most likely to be "tidied" and it must not be.
    The sales program leaves the loop only at end of file; `pl055` leaves it on
    ANY non-zero status. In a scenario where a read fails mid-walk - a locked
    row, a key error, anything at all - the two programs write different
    amounts of data before stopping, and everything the remaining invoices
    would have contributed is simply absent. That is precisely the class of
    difference the state diff exists to catch, so the comparison stays as
    written.

    ⭐ THE ACCUMULATION BLOCK APPEARS TWICE AND IS NOT FACTORED. Lines
    [purchase/pl055.cbl:L327-L337] and [purchase/pl055.cbl:L349-L356] look like
    one helper called twice. They are not the same: the first chooses `Write`
    or `Rewrite` from `v-exists` and the second always rewrites, and the second
    carries an extra `move 1 to File-Key-No` [purchase/pl055.cbl:L355] that the
    first does not have at the equivalent point. Agent Action Plan section
    0.6.1 on the sibling programs' averages applies exactly: *"Normalising them
    into one helper would be the single easiest way to fail this migration."*

    Args:
        st: The program's state.
    """
    ctx = st.ctx
    line = ctx.invoice_line
    header = ctx.invoice_header
    value = ctx.ws_value_record

    while True:
        # 307  perform  PInvoice-Read-Next.
        st.facade.pinvoice_read_next(ctx)

        # 308  if       FS-Reply not = zero
        # 309           go to  close-files.
        # GO TO class 2 - forward terminator. The target does real work, so the
        # break is paired with the post-loop call below and not left bare.
        # DIVERGENCE 4 [purchase/pl055.cbl:L308] vs [sales/sl055.cbl:L367] -
        # ANY non-zero status ends the walk here, end of file only there.
        # ⛔ DO NOT change this to `== FsReply.END_OF_FILE`.
        if ctx.file_access.fs_reply != FsReply.SUCCESS:
            break

        # 311  if       ih-test = zero
        # 312           go to header-analysis.
        # GO TO class 4 - sibling re-dispatch. EQUIVALENCE PROOF: every path
        # through `header-analysis` [purchase/pl055.cbl:L362-L398] ends in `go
        # to read-loop` - at [L366], at [L372] and at [L398], the paragraph's
        # last statement - so it has no fall-through and no other exit. A call
        # followed by an unconditional `continue` is therefore exactly what the
        # COBOL does. Note that the sales program reaches its header block by
        # `exit perform` and FALL-THROUGH [sales/sl055.cbl:L371, L426]; this
        # one names the target explicitly.
        # `ih-test pic 99` [copybooks/plwspinv2.cob:L23] is numeric DISPLAY and
        # shares bytes with `il-line` [copybooks/plwspinv2.cob:L58] through the
        # redefinition, which is how one field tells a header from a line.
        if arithmetic.compare(header.ih_test, 0) == 0:
            _header_analysis(st)
            continue

        # 314  if       il-analyised
        # 315           go to  read-loop.
        # GO TO class 1 - loop-back.
        # `88 il-analyised values "z" "Z".` [copybooks/plwspinv2.cob:L72]
        # accepts BOTH cases, which is why the lower-case store at
        # [purchase/pl055.cbl:L358] still satisfies its own test.
        if condition_names.evaluate(
            "il-analyised", line.il_update, copybook="copybooks/plwspinv2.cob"
        ):
            continue

        # ⭐ DIVERGENCE 16 - THERE IS NO COMMENT-LINE FILTER HERE, AND NOTHING IS
        # MISSING. This is exactly the point at which the sales extract skips a
        # line whose product code opens with a slash -
        #
        #     if       il-product (1:1) = "/"        [sales/sl055.cbl:L376]
        #              exit perform cycle
        #
        # - and `pl055` has no such test anywhere: `grep` for `il-product` in
        # [purchase/pl055.cbl] finds it only in the copybook it inherits, never
        # in a statement. So a purchase invoice line whose product code is a
        # comment marker IS analysed and DOES contribute to the value totals,
        # where its sales counterpart would be passed over. Recorded, not
        # imported - adding the filter would be a new validation (rule R-3) and
        # would change `VALUEANAL-REC` totals for any seed that carries such a
        # line. ⛔ DO NOT ADD IT.
        #
        # ⭐ DIVERGENCE 10 - THE PARAGRAPH NAMES ARE UNPREFIXED. The sales
        # program's equivalent loop is `da010-Read-Loop` [sales/sl055.cbl:L364]
        # inside `da000-mainline` [sales/sl055.cbl:L305], with `db`/`dc`/`dd`
        # prefixes on the later sections; `pl055` names the same paragraphs
        # `read-loop` [purchase/pl055.cbl:L306], `header-analysis` [L362],
        # `close-files` [L400], `menu-exit` [L434], `Create-Main` [L444],
        # `Create-Anal` [L488] and three bare `main-exit` [L501, L536, L597].
        # The Python functions therefore carry the COBOL's own unprefixed names,
        # section-qualified only where the name is not unique - which is why
        # `_create__main_exit`, `_store_specials__main_exit` and
        # `_extract__main_exit` exist as three distinct functions.

        # 317  move     "P" to va-system.
        value.va_code.va_system = move.move("P", _VAL["va-system"])
        # 318  move     il-pa to  va-group.
        # `il-pa pic xx` [copybooks/plwspinv2.cob:L60] into the two-character
        # group `va-group` [copybooks/wsval.cob:L12], so a group move of 2.
        _move_into_va_group(
            value,
            move.move_group(
                line.il_pa,
                _VAL["va-group"],
                sending_field=pinvoice_descriptor_for(IlInvoiceLine, "il_pa"),
                length=2,
            ),
        )
        # 319  move     1  to  v-exists.
        st.v_exists = move.move(1, _D_V_EXISTS)

        # 321  move     1 to File-Key-No.
        st.ctx.file_access.logging_data.file_key_no = 1
        # 322  perform  Value-Read-Indexed.
        st.facade.value_read_indexed(ctx)
        # 323  if       fs-reply = 21
        # FINDING [purchase/pl055.cbl:L323] - this site, and
        # [purchase/pl055.cbl:L346], [L510] and [L527], test 21 ALONE, while
        # [purchase/pl055.cbl:L449] tests `= 21 or = 23`. The inconsistency is
        # the COBOL's, reproduced site by site. The sales program tests
        # `= 21 or = 23` at both of its equivalent sites
        # [sales/sl055.cbl:L384, L408].
        if ctx.file_access.fs_reply == FsReply.INVALID_KEY_ON_START:
            # 324           perform  create
            _create(st)
            # 325           move zero to v-exists.
            st.v_exists = move.move_figurative(move.ZERO, _D_V_EXISTS)

        # 327  add      1  to  va-t-this.
        value.va_t_this = arithmetic.add_to(
            1, receiver_value=value.va_t_this, receiving=_VAL["va-t-this"]
        )
        # 328  add      1  to  va-t-year.
        value.va_t_year = arithmetic.add_to(
            1, receiver_value=value.va_t_year, receiving=_VAL["va-t-year"]
        )
        # 329  if       il-type not = 3
        # `il-type pic x` [copybooks/plwspinv2.cob:L63] is ALPHANUMERIC, so
        # this compares one character against the image of the literal 3.
        # Routing it through numeric comparison would raise on any non-digit
        # byte a read happens to deliver.
        if line.il_type != _IL_TYPE_3:
            # 330           add il-net to  va-v-this va-v-year
            # DIVERGENCE 15 [purchase/pl055.cbl:L330] vs
            # [sales/sl055.cbl:L391-L395] - ONE statement with TWO receivers
            # here, four single-receiver statements there. Each receiver
            # converts the sender independently.
            value.va_v_this, value.va_v_year = _add_to_pair(
                line.il_net,
                (value.va_v_this, _VAL["va-v-this"]),
                (value.va_v_year, _VAL["va-v-year"]),
            )
        else:
            # 332           subtract il-net from va-v-this va-v-year.
            value.va_v_this, value.va_v_year = _subtract_from_pair(
                line.il_net,
                (value.va_v_this, _VAL["va-v-this"]),
                (value.va_v_year, _VAL["va-v-year"]),
            )

        # 334  if       v-exists = zero
        if arithmetic.compare(st.v_exists, 0) == 0:
            # 335           perform Value-Write
            st.facade.value_write(ctx)
        else:
            # 337           perform Value-Rewrite.
            st.facade.value_rewrite(ctx)
        # 338  end-if
        # FINDING [purchase/pl055.cbl:L338] - a period AFTER `end-if`, closing
        # a construct whose `if` at [L334] was already closed by the period on
        # [L337]. Harmless in COBOL and noted only as evidence of the era.

        # 340  if       va-second = space
        # 341           go to read-loop.
        #
        # ================================ FINDING B ================================
        # FINDING [purchase/pl055.cbl:L340-L341] cf. [purchase/pl055.cbl:L358-L359]
        #   A SINGLE-CHARACTER ANALYSIS GROUP IS ACCUMULATED BUT NEVER STAMPED, SO IT
        #   IS RE-ANALYSED - AND THEREFORE DOUBLE-COUNTED - ON EVERY SUBSEQUENT RUN.
        #
        #   `va-second` is the second character of the two-character analysis group
        #   `il-pa` [copybooks/plwspinv2.cob:L61] that was moved into `va-group` at
        #   [L318]. When that second character is a space the group has no roll-up
        #   partner, so the second half of the twice-over accumulation - the read of
        #   the blanked key at [L343-L345] and its rewrite at [L356] - is genuinely
        #   inapplicable and the transfer at [L341] correctly skips it.
        #
        #   What the transfer ALSO skips, because it targets `read-loop` rather than
        #   the tail of the loop body, is EVERYTHING BETWEEN HERE AND [L360]:
        #       [L358]  move     "z"  to  il-update.
        #       [L359]  perform  PInvoice-Rewrite.
        #   The line's `il-update` flag is consequently never set and the
        #   `PUINV-LINES-REC` row is never rewritten, even though [L327-L337] has
        #   already added the line into `VALUEANAL-REC` and committed it with a
        #   `Value-Write` or `Value-Rewrite`. The `il-analyised` test at [L314] -
        #   `88 il-analyised values "z" "Z"` [copybooks/plwspinv2.cob:L69] - therefore
        #   still reads FALSE on the next run, and the same line is accumulated into
        #   the same value row a second time. The value totals grow without bound
        #   across reruns for every line whose analysis group is one character wide.
        #
        #   This is NOT a transcription artefact of the Purchase side. `sl055` has the
        #   identical ordering: `if va-second = space exit perform cycle`
        #   [sales/sl055.cbl:L402-L404] sits BEFORE `move "Z" to il-update`
        #   [sales/sl055.cbl:L421] and `perform Invoice-Rewrite`
        #   [sales/sl055.cbl:L422]. Both programs carry the defect, which is why it is
        #   recorded as a shared legacy defect rather than as a pl055/sl055
        #   divergence. Only the STAMPED CASE is a divergence: pl055 stores lower-case
        #   `"z"` [purchase/pl055.cbl:L358] where sl055 stores upper-case `"Z"`
        #   [sales/sl055.cbl:L421] - see DIVERGENCE 6 at that site.
        #
        #   Measured effect, from the ad-hoc walk of a single line with `il-pa = "v "`:
        #   the value rows are written and rewritten, and `PInvoice-Rewrite` is never
        #   called at all - no stamp is issued for the line.
        #
        #   Reproduced deliberately per R-4; DO NOT FIX. Moving the stamp above this
        #   transfer, or retargeting the transfer at the loop tail, would set
        #   `il-update` on a row the COBOL leaves blank - a stored column value in
        #   `PUINV-LINES-REC` and therefore directly visible in a table dump.
        # ===========================================================================
        #
        # GO TO class 1 - loop-back.
        if value.va_code.va_group.va_second == _SPACE_1:
            continue

        # 343  move     space  to  va-second.
        value.va_code.va_group.va_second = move.move_figurative(
            move.SPACE, _VAL["va-second"]
        )
        # 344  move     1 to File-Key-No.
        st.ctx.file_access.logging_data.file_key_no = 1
        # 345  perform  Value-Read-Indexed.
        st.facade.value_read_indexed(ctx)
        # 346  if       FS-Reply = 21
        # 347           go to read-loop.
        # GO TO class 1 - loop-back. 21 alone again, not `21 or 23`.
        if ctx.file_access.fs_reply == FsReply.INVALID_KEY_ON_START:
            continue

        # 349  add      1  to  va-t-this.
        value.va_t_this = arithmetic.add_to(
            1, receiver_value=value.va_t_this, receiving=_VAL["va-t-this"]
        )
        # 350  add      1 to va-t-year.
        value.va_t_year = arithmetic.add_to(
            1, receiver_value=value.va_t_year, receiving=_VAL["va-t-year"]
        )
        # 351  if       il-type not = 3
        if line.il_type != _IL_TYPE_3:
            # 352           add il-net to  va-v-this va-v-year
            value.va_v_this, value.va_v_year = _add_to_pair(
                line.il_net,
                (value.va_v_this, _VAL["va-v-this"]),
                (value.va_v_year, _VAL["va-v-year"]),
            )
        else:
            # 354           subtract il-net from va-v-this va-v-year.
            value.va_v_this, value.va_v_year = _subtract_from_pair(
                line.il_net,
                (value.va_v_this, _VAL["va-v-this"]),
                (value.va_v_year, _VAL["va-v-year"]),
            )
        # 355  move     1 to File-Key-No.
        # FINDING [purchase/pl055.cbl:L355] - an assignment the first pass does
        # not make at the equivalent point, sitting between the accumulation
        # and the rewrite. The facade's own dispatch paragraph sets the same
        # field anyway [copybooks/Proc-ACAS-FH-Calls.cob:L90], so this is
        # redundant twice over. ⛔ Rule R-3: it is preserved in place.
        st.ctx.file_access.logging_data.file_key_no = 1
        # 356  perform  Value-Rewrite.
        st.facade.value_rewrite(ctx)

        # 358  move     "z"  to  il-update.
        # ⭐⭐ DIVERGENCE 6 [purchase/pl055.cbl:L358] vs [sales/sl055.cbl:L421].
        # LOWER-CASE "z" here; the sales program stores upper-case "Z" and
        # documents its own change - *"Analysied flag changed from z (1/6/13)"*
        # - which `pl055` was never given. `il-update` is a stored
        # `PUINV-LINES-REC` column, so the case difference is DIFF-VISIBLE
        # even though `88 il-analyised values "z" "Z".`
        # [copybooks/plwspinv2.cob:L72] accepts both and control flow is
        # therefore unaffected. ⛔ DO NOT normalise the case.
        line.il_update = move.move(
            "z", pinvoice_descriptor_for(IlInvoiceLine, "il_update")
        )
        # 359  perform  PInvoice-Rewrite.
        st.facade.pinvoice_rewrite(ctx)
        # 360  go       to read-loop.
        # GO TO class 1 - loop-back, and the paragraph's last statement.
        continue

    # The class-2 target of [purchase/pl055.cbl:L309]. Agent Action Plan
    # section 0.6.3, verbatim: *"the transformation is `break` PLUS faithful
    # placement of that work after the loop, not `break` alone. Mis-splitting
    # here would silently drop end-of-run processing."* The work in question is
    # the four special-total stores and four closes at
    # [purchase/pl055.cbl:L403-L423] - the entire purchase value-analysis
    # roll-up - and because [L308] breaks on ANY non-zero status this path is
    # reached far more often than its sales counterpart.
    _close_files(st)


def _move_into_va_group(value: WsValueRecord, image: str) -> None:
    """Scatter a two-character `va-group` image back into its two children.

    `03 va-group.` [copybooks/wsval.cob:L12] is a group over `va-first` and
    `va-second` [copybooks/wsval.cob:L13-L14]. A group move lays bytes into it
    without consulting either child's picture, so the bytes are laid down and
    then read back through the children - which is what the COBOL storage does
    for free and a Python dataclass does not.
    """
    value.va_code.va_group.va_first = move.move(
        move.ref_mod(image, 1, 1), _VAL["va-first"]
    )
    value.va_code.va_group.va_second = move.move(
        move.ref_mod(image, 2, 1), _VAL["va-second"]
    )


def _add_to_pair(
    source: Decimal | int,
    first: tuple[Decimal | int, FieldDescriptor],
    second: tuple[Decimal | int, FieldDescriptor],
) -> tuple[Any, Any]:
    """`ADD <source> TO <receiver-1> <receiver-2>` - two receivers, one verb.

    Each receiver is added into and stored under its OWN description, which is
    what a multi-receiver `ADD` does: the sender is not summed once and copied
    twice. Both receivers here happen to share a picture, but the primitive is
    written per receiver so that it stays correct if they ever do not.
    """
    return (
        arithmetic.add_to(source, receiver_value=first[0], receiving=first[1]),
        arithmetic.add_to(source, receiver_value=second[0], receiving=second[1]),
    )


def _subtract_from_pair(
    source: Decimal | int,
    first: tuple[Decimal | int, FieldDescriptor],
    second: tuple[Decimal | int, FieldDescriptor],
) -> tuple[Any, Any]:
    """`SUBTRACT <source> FROM <receiver-1> <receiver-2>` - two receivers.

    `SUBTRACT a FROM b` with no `GIVING` computes `b - a` into `b`; the
    receiver is the second operand, and the primitive takes it as
    `receiver_value` for exactly that reason.
    """
    return (
        arithmetic.subtract_from(source, receiver_value=first[0], receiving=first[1]),
        arithmetic.subtract_from(source, receiver_value=second[0], receiving=second[1]),
    )


#
#  header-analysis.   [purchase/pl055.cbl:L362]
#


def _header_analysis(st: _Pl055State) -> None:
    """`header-analysis.`   [purchase/pl055.cbl:L362-L398]

    Extracts one invoice HEADER into the OTM4 sequence and folds its VAT,
    carriage and discount figures into four running special totals.

    ⭐ DIVERGENCE 8 - TWO SIGN FLIPS, NOT THREE. The sales program negates
    three work values for a credit note - VAT [sales/sl055.cbl:L446], carriage
    [sales/sl055.cbl:L457] and discount [sales/sl055.cbl:L461-L466]. `pl055`
    negates the first two [purchase/pl055.cbl:L376, L387] and leaves the
    discount block alone [purchase/pl055.cbl:L391-L394]. There is a mechanical
    reason to believe that is intentional rather than an oversight: the
    purchase discount field is UNSIGNED - `03 ih-deduct-amt pic 999v99 comp.`
    [copybooks/plwspinv2.cob:L46], with no `S` - so it cannot carry a negative
    value in the first place and `ws-disc-totalv` can only ever grow. The
    divergence is preserved either way; the note is recorded because it is
    evidence, not because it licenses a change.

    ⭐ DIVERGENCE 9 - TWO VAT ADDENDS, NOT THREE.

        add      ih-c-vat ih-vat giving work-2.    [purchase/pl055.cbl:L374]
        add      ih-c-vat ih-vat ih-e-vat giving work-2.
                                                   [sales/sl055.cbl:L444]

    `ih-e-vat` [copybooks/plwspinv2.cob:L38] exists in the purchase header and
    is simply not summed here. ⛔ Rule R-3 forbids adding it.

    ⭐ THE SIGN FLIP IS THE NO-`GIVING` FORM. `multiply -1 by work-2` computes
    `work-2 = -1 * work-2` - the RECEIVER IS THE SECOND OPERAND. That is not
    the General Ledger family's `multiply x by -1 giving x`, and getting the
    operand roles the wrong way round would be undetectable by inspection.

    ⭐ THE TWO VAT TOTALS ARE NOT ONE TOTAL. [purchase/pl055.cbl:L377-L380]
    accumulates into `ws-vat-total*` when the type is NOT 1, and
    [purchase/pl055.cbl:L381-L384] into `ws-vatr-total*` when it IS 1 -
    receipts kept apart from everything else, later stored under two different
    analysis groups. ⛔ Do not merge the two conditions.

    Args:
        st: The program's state.
    """
    ctx = st.ctx
    header = ctx.invoice_header
    fig = ctx.invoice_fig

    # ⭐⭐ DIVERGENCE 7 - THE ENTIRE SKIP-INVOICE APPARATUS IS ABSENT, AND ITS
    # ABSENCE IS THE SPECIFICATION. The sales program guards this same point
    # with four things `pl055` does not have:
    #
    #   * a proforma filter          `if ih-type = 4`   [sales/sl055.cbl:L430]
    #   * a pending / status filter  `if pending or ih-status = "L"`
    #                                          [sales/sl055.cbl:L433-L434]
    #   * a `ws-p-flag` recording that a proforma was seen, which drives a
    #     SECOND conditional `goback` at [sales/sl055.cbl:L509, L518]
    #   * a whole paragraph, `da030-Skip-Invoice.` [sales/sl055.cbl:L472], which
    #     repositions the file with `set fn-not-less-than to true`
    #     [sales/sl055.cbl:L475] followed by `Invoice-Start`
    #     [sales/sl055.cbl:L476] so the walk resumes past the skipped invoice's
    #     lines
    #
    # `pl055` goes straight from the `ih-analyised and applied` test
    # [purchase/pl055.cbl:L365-L366] to `perform extract`
    # [purchase/pl055.cbl:L368]. There is NO `PInvoice-Start` verb call and NO
    # `set fn-` of ANY kind anywhere in the program, so there is no repositioning
    # to reproduce and nothing to skip past. A purchase proforma is therefore
    # extracted into OTM4 and counted in the special totals exactly like an
    # invoice. ⛔ Rule R-3 forbids importing any of it, and the missing
    # paragraph is recorded rather than invented so that a reader diffing the two
    # programs does not conclude a function was lost.

    # 365  if       ih-analyised and applied
    # 366           go to read-loop.
    # GO TO class 1 - loop-back, expressed by returning to the caller, which
    # continues the loop. Two condition names over two different fields:
    # `88 ih-analyised values "z" "Z".` [copybooks/plwspinv2.cob:L53] over
    # `ih-update`, and `88 applied values "z" "Z".`
    # [copybooks/plwspinv2.cob:L43] over `ih-status`.
    if condition_names.evaluate(
        "ih-analyised", header.ih_update, copybook="copybooks/plwspinv2.cob"
    ) and condition_names.evaluate(
        "applied", header.ih_status, copybook="copybooks/plwspinv2.cob"
    ):
        return

    # 368  perform  extract.
    _extract(st)

    # 370  if       ih-analyised
    if condition_names.evaluate(
        "ih-analyised", header.ih_update, copybook="copybooks/plwspinv2.cob"
    ):
        # 371           perform  PInvoice-Rewrite
        st.facade.pinvoice_rewrite(ctx)
        # 372           go to read-loop.
        # GO TO class 1 - loop-back.
        return

    # 374  add      ih-c-vat ih-vat giving work-2.
    # DIVERGENCE 9 [purchase/pl055.cbl:L374] vs [sales/sl055.cbl:L444] - TWO
    # addends, `ih-e-vat` omitted. A variadic `ADD ... GIVING` sums at extended
    # intermediate precision and quantizes ONCE into the receiver.
    st.work_2 = arithmetic.add_giving(fig.ih_c_vat, fig.ih_vat, receiving=_D_WORK_2)
    # 375  if       ih-type = 3
    if arithmetic.compare(header.ih_type, 3) == 0:
        # 376           multiply -1 by work-2.
        # SIGN FLIP 1 of 2. No `GIVING`: the receiver is `work-2`, the second
        # operand.
        st.work_2 = arithmetic.multiply_by(-1, st.work_2, _D_WORK_2)
    # 377  if       work-2 not = zero and
    # 378           ih-type not = 1
    if arithmetic.compare(st.work_2, 0) != 0 and arithmetic.compare(header.ih_type, 1) != 0:
        # 379           add 1 to ws-vat-totalt
        st.ws_vat_totalt = arithmetic.add_to(
            1, receiver_value=st.ws_vat_totalt, receiving=_D_VAT_TOTALT
        )
        # 380           add work-2 to ws-vat-totalv.
        st.ws_vat_totalv = arithmetic.add_to(
            st.work_2, receiver_value=st.ws_vat_totalv, receiving=_D_VAT_TOTALV
        )
    # 381  if       work-2 not = zero and
    # 382           ih-type = 1
    if arithmetic.compare(st.work_2, 0) != 0 and arithmetic.compare(header.ih_type, 1) == 0:
        # 383           add 1 to ws-vatr-totalt
        st.ws_vatr_totalt = arithmetic.add_to(
            1, receiver_value=st.ws_vatr_totalt, receiving=_D_VATR_TOTALT
        )
        # 384           add work-2 to ws-vatr-totalv.
        st.ws_vatr_totalv = arithmetic.add_to(
            st.work_2, receiver_value=st.ws_vatr_totalv, receiving=_D_VATR_TOTALV
        )
    # 385  move     ih-carriage to work-2.
    st.work_2 = move.move(
        fig.ih_carriage,
        _D_WORK_2,
        sending_field=pinvoice_descriptor_for(IhFig2, "ih_carriage"),
    )
    # 386  if       ih-type = 3
    if arithmetic.compare(header.ih_type, 3) == 0:
        # 387           multiply -1 by work-2.
        # SIGN FLIP 2 of 2.
        st.work_2 = arithmetic.multiply_by(-1, st.work_2, _D_WORK_2)
    # 388  if       work-2 not = zero
    if arithmetic.compare(st.work_2, 0) != 0:
        # 389           add 1 to ws-carr-totalt
        st.ws_carr_totalt = arithmetic.add_to(
            1, receiver_value=st.ws_carr_totalt, receiving=_D_CARR_TOTALT
        )
        # 390           add work-2 to ws-carr-totalv.
        st.ws_carr_totalv = arithmetic.add_to(
            st.work_2, receiver_value=st.ws_carr_totalv, receiving=_D_CARR_TOTALV
        )
    # 391  move     ih-deduct-amt to work-2.
    st.work_2 = move.move(
        header.ih_deduct_amt,
        _D_WORK_2,
        sending_field=pinvoice_descriptor_for(IhInvoiceHeader, "ih_deduct_amt"),
    )
    # ⭐⭐ DIVERGENCE 8 [purchase/pl055.cbl:L391] vs [sales/sl055.cbl:L461-L466]
    # - THERE IS NO `if ih-type = 3 / multiply -1 by work-2` HERE. The sales
    # program flips the discount's sign for a credit note; this one does not,
    # and `ih-deduct-amt` is unsigned [copybooks/plwspinv2.cob:L46] so it
    # could not hold the result if it did. ⛔ DO NOT add the missing flip.
    # 392  if       work-2 not = zero
    if arithmetic.compare(st.work_2, 0) != 0:
        # 393           add 1 to ws-disc-totalt
        st.ws_disc_totalt = arithmetic.add_to(
            1, receiver_value=st.ws_disc_totalt, receiving=_D_DISC_TOTALT
        )
        # 394           add work-2 to ws-disc-totalv.
        st.ws_disc_totalv = arithmetic.add_to(
            st.work_2, receiver_value=st.ws_disc_totalv, receiving=_D_DISC_TOTALV
        )

    # 396  move     "z" to ih-update.
    # ⭐⭐ DIVERGENCE 6 [purchase/pl055.cbl:L396] vs [sales/sl055.cbl:L468].
    # LOWER-CASE "z" into a stored `PUINVOICE-REC` column. Note the internal
    # inconsistency inside `pl055` itself: `ih-update` and `il-update` take
    # lower case here and at [purchase/pl055.cbl:L358], while `ih-status`
    # takes UPPER case at [purchase/pl055.cbl:L586] under the maintainer's own
    # note *"07/01/18 was 'z'"*. Both exactly as written. ⛔ Do not normalise.
    header.ih_update = move.move(
        "z", pinvoice_descriptor_for(IhInvoiceHeader, "ih_update")
    )
    # 397  perform  PInvoice-Rewrite.
    st.facade.pinvoice_rewrite(ctx)
    # 398  go       to read-loop.
    # GO TO class 1 - loop-back, and the paragraph's last statement. This is
    # what makes the class-4 entry at [purchase/pl055.cbl:L312] provably a
    # call-then-continue: there is no path out of this paragraph except back to
    # the loop head.
    return


#
#  close-files.   [purchase/pl055.cbl:L400]
#


def _close_files(st: _Pl055State) -> None:
    """`close-files.`   [purchase/pl055.cbl:L400-L432]

    Stores the four special totals as value-analysis groups, closes everything
    and reports whether any emergency analysis record had to be invented.

    ⭐ DIVERGENCE 17 - THE GROUPS ARE `vi`, `vj`, `za`, `zb`, AND `va-system`
    IS SET EXPLICITLY. The sales program uses `vo`, `vp`, `zc`, `zd` and lets
    the system character ride along inside a three-character literal. `pl055`
    writes `move "P" to va-system.` [purchase/pl055.cbl:L403] on its own line
    and then sets only the two-character group. `pl060`'s deduction analysis
    later targets the `"zb"` group, the purchase analogue of the sales
    `"Szd"`.

    ⭐ ONE CONDITIONAL `goback`, NOT TWO. The sales program has two
    [sales/sl055.cbl:L509, L518] because it also carries a proforma flag;
    `pl055` has no `ws-p-flag` at all and so has one, at
    [purchase/pl055.cbl:L432], complete with the maintainer's shrug: *"Yep, I
    know but just in case extra code goes here!"*

    Args:
        st: The program's state.
    """
    ctx = st.ctx
    value = ctx.ws_value_record

    # 403  move     "P" to va-system.
    # DIVERGENCE 17 - set explicitly, once, for all four groups that follow.
    value.va_code.va_system = move.move("P", _VAL["va-system"])

    # 404  move     "vi" to va-group.
    # 405  move     ws-vat-totalt to work-3.
    # 406  move     ws-vat-totalv to work-2.
    # 407  perform  store-specials
    _store_group(st, "vi", st.ws_vat_totalt, _D_VAT_TOTALT, st.ws_vat_totalv, _D_VAT_TOTALV)
    # 408  move     "vj" to va-group.
    # 409  move     ws-vatr-totalt to work-3.
    # 410  move     ws-vatr-totalv to work-2.
    # 411  perform  store-specials
    _store_group(
        st, "vj", st.ws_vatr_totalt, _D_VATR_TOTALT, st.ws_vatr_totalv, _D_VATR_TOTALV
    )
    # 412  move     "za" to va-group.
    # 413  move     ws-carr-totalt to work-3.
    # 414  move     ws-carr-totalv to work-2.
    # 415  perform  store-specials
    _store_group(
        st, "za", st.ws_carr_totalt, _D_CARR_TOTALT, st.ws_carr_totalv, _D_CARR_TOTALV
    )
    # 416  move     "zb" to va-group.
    # 417  move     ws-disc-totalt to work-3.
    # 418  move     ws-disc-totalv to work-2.
    # 419  perform  store-specials
    _store_group(
        st, "zb", st.ws_disc_totalt, _D_DISC_TOTALT, st.ws_disc_totalv, _D_DISC_TOTALV
    )

    # 420  perform  PInvoice-Close.
    st.facade.pinvoice_close(ctx)
    # 421  perform  Value-Close.
    st.facade.value_close(ctx)
    # 422  perform  Analysis-Close.
    st.facade.analysis_close(ctx)
    # 423  close    open-item-file-4.
    st.open_item_file_4.close()

    # 425  if       Anal-Created not = zero
    if arithmetic.compare(st.anal_created, 0) != 0:
        # 426           display PL201 at 1201 ...
        # 427           display PL202 at 1401 ...
        _LOG.warning("%s", _PL201)
        _LOG.warning("%s", _PL202)
        # 428           if     WS-Caller not = "xl150"
        # The codebase's own unattended-mode check: when the out-of-scope
        # `xl150` driver is running the cycle there is nobody at the terminal.
        # The BRANCH is preserved because it is real control flow; only the
        # `accept` inside it is dropped.
        if not _caller_is_xl150(st):
            # 429                  display PL006 at 1601 ...
            _LOG.warning("%s", _PL006)
            # 430                  accept ws-reply at 1645
            # Dropped: an acknowledgement pause whose only effect is to block a
            # terminal (Agent Action Plan section 0.3.4).
        # 432           goback.
        # *> Yep, I know but just in case extra code goes here!
        return

    # FALL-THROUGH into `menu-exit.` [purchase/pl055.cbl:L434] when
    # `Anal-Created` is zero. Recorded in the traceability footer.
    _menu_exit()


def _store_group(
    st: _Pl055State,
    group: str,
    count: int,
    count_field: FieldDescriptor,
    money: Decimal,
    money_field: FieldDescriptor,
) -> None:
    """One `move va-group / move work-3 / move work-2 / perform store-specials`.

    The four blocks at [purchase/pl055.cbl:L404-L419] are textually identical
    but for the group literal and the pair of totals, so the repetition is
    carried by an argument list rather than by four transcriptions of the same
    four statements. Nothing is shared that the COBOL does not share: the
    statements are the same statements, the operands differ, and each call site
    above names the exact lines it stands for.
    """
    value = st.ctx.ws_value_record
    # move     "<group>" to va-group.
    _move_into_va_group(
        value, move.move_group(group, _VAL["va-group"], length=2)
    )
    # move     ws-*-totalt to work-3.
    st.work_3 = move.move(count, _D_WORK_3, sending_field=count_field)
    # move     ws-*-totalv to work-2.
    st.work_2 = move.move(money, _D_WORK_2, sending_field=money_field)
    # perform  store-specials
    _store_specials(st)


def _caller_is_xl150(st: _Pl055State) -> bool:
    """`if WS-Caller not = "xl150"`   [purchase/pl055.cbl:L283, L428]

    `03 WS-Caller pic x(8).` [copybooks/wscall.cob:L8] is eight characters, so
    the literal is compared space-padded to that width - the shorter operand is
    extended with spaces, which is what makes `"xl150"` match a field holding
    `"xl150   "`. Comparing the raw Python strings would fail on the padding.
    """
    caller = move.move("xl150", calling_data_descriptor_for("ws_caller"))
    return st.ws_calling_data.ws_caller == caller


#
#  menu-exit.   [purchase/pl055.cbl:L434]
#


def _menu_exit() -> None:
    """`menu-exit.` / `goback.`   [purchase/pl055.cbl:L434-L435]

    The normal end of the program. `GOBACK` from a called sub-program returns
    to its caller, which is a plain return here - `pl055` is never the main
    program, as its five-parameter `PROCEDURE DIVISION USING`
    [purchase/pl055.cbl:L239-L243] shows.

    It carries no statement other than the `goback`, and it is retained as its
    own function because rule R-5 requires a named function per paragraph even
    where the paragraph does nothing but end - Agent Action Plan section 0.7.4
    C-4, verbatim: *"every paragraph retains a named function even where its
    `GO TO` becomes a `continue`, a `break` or a `return`."*
    """
    _LOG.debug("pl055 menu-exit  [purchase/pl055.cbl:L434-L435]")


#
#  create section.   [purchase/pl055.cbl:L441]
#


def _create(st: _Pl055State) -> None:
    """`create section.`   [purchase/pl055.cbl:L441]

    The section HEAD, which is what `perform create` [purchase/pl055.cbl:L324,
    L511] actually names. It carries no statements of its own - the next line is
    `Create-Main.` [purchase/pl055.cbl:L444] - so all it does is enter the
    section's first paragraph, exactly as COBOL does.

    Kept as its own function rather than folded into `_create__create_main`
    because rule R-5 asks for a named function per SECTION as well as per
    paragraph, and because the two are genuinely different labels: `perform
    create` enters the section and runs to its end, while the backward transfer
    at [purchase/pl055.cbl:L499] names the PARAGRAPH `create-Main`. Collapsing
    them would hide that distinction.

    Args:
        st: The program's state.
    """
    _create__create_main(st)


def _create__create_main(st: _Pl055State) -> None:
    """`Create-Main.`   [purchase/pl055.cbl:L444-L486], of `create section.` L441

    Seeds a value-analysis record from its analysis record, inventing the
    analysis record first if it is missing. Entered by `perform create` from
    [purchase/pl055.cbl:L324] and [purchase/pl055.cbl:L511].

    ⭐⭐ THE BACKWARD RETRY, WHICH IS THE ONLY REAL CONTROL-FLOW PUZZLE IN THIS
    PROGRAM. `Create-Anal` [purchase/pl055.cbl:L488] ends with `go to
    create-Main` [purchase/pl055.cbl:L499] - a BACKWARD transfer to this
    paragraph, the first of the section. So the pair is a retry loop: read the
    analysis record; if it is not there, write an emergency one and read again.

    EQUIVALENCE PROOF FOR THE `while True`. `Create-Anal` has exactly one exit,
    the unconditional `go to create-Main` at its last line, and it contains no
    other transfer. `Create-Main` reaches it from exactly one place, the
    conditional `go to Create-Anal` at [purchase/pl055.cbl:L450]. A loop whose
    body is `Create-Main`'s statements, which calls `Create-Anal` and then
    `continue`s, therefore visits exactly the same statements in exactly the
    same order as the two COBOL paragraphs do, and terminates in exactly the
    same circumstances.

    # AMBIGUITY Q-PL055-2 - the retry has NO iteration guard.
    # If `Analysis-Write` [purchase/pl055.cbl:L494] fails silently, the re-read
    # at [purchase/pl055.cbl:L448] returns 21 again and the pair spins forever.
    # ⛔ Rule R-3 forbids adding a guard, a counter or a bail-out: that would be
    # a new validation. What the compiled program actually does when the write
    # fails is a question for the oracle (rule R-6), not for a defensive `if`.

    ⭐ THE ONLY `= 21 or = 23` SITE IN THE PROGRAM is
    [purchase/pl055.cbl:L449]. Four other reply tests - [L323], [L346], [L510]
    and [L527] - test 21 alone. The inconsistency is reproduced rather than
    smoothed. The data-access layer records that `FS-Reply` 23 is documented
    but never actually returned, which makes the `or = 23` arm dead in
    practice; ⛔ it is not removed for that.

    ⭐ THREE GROUP MOVES AND THREE SIX-RECEIVER `MOVE`s.
    [purchase/pl055.cbl:L452], [L470] and [L482] move a 36-byte analysis record
    into a 66-byte value record - a group move, which applies NO picture clause
    to any part of the receiver and space-fills the 30 trailing bytes. Those
    30 bytes are the six `comp`/`comp-3` numeric fields, which is exactly why
    each group move is immediately followed by a single `MOVE ZERO` naming all
    six [purchase/pl055.cbl:L453-L454, L471-L472, L483-L484].

    ⭐ A NAMING QUIRK, RECORDED. The paragraph is declared `Create-Main.` and
    the `GO TO` spells it `create-Main` [purchase/pl055.cbl:L499]. COBOL is
    case-insensitive so the two agree; the sales program has the identical
    quirk [sales/sl055.cbl:L530, L585].

    Args:
        st: The program's state.
    """
    ctx = st.ctx
    value = ctx.ws_value_record
    analysis = ctx.ws_analysis_record

    while True:
        # 445  move     va-code  to  WS-Pa-Code.
        # Group to group, three characters each: `03 va-code.`
        # [copybooks/wsval.cob:L10] into `03 WS-Pa-Code.`
        # [copybooks/wsanal.cob:L10].
        _move_into_pa_code(
            analysis,
            move.move_group(
                _va_code_image(value),
                _ANL["ws-pa-code"],
                sending_field=_VAL["va-code"],
                length=3,
            ),
        )

        # 447  move     1 to File-Key-No.
        ctx.file_access.logging_data.file_key_no = 1
        # 448  perform  Analysis-Read-Indexed.
        st.facade.analysis_read_indexed(ctx)
        # 449  if       FS-Reply = 21 or = 23
        if ctx.file_access.fs_reply in (
            FsReply.INVALID_KEY_ON_START,
            FsReply.KEY_NOT_FOUND,
        ):
            # 450           go to  Create-Anal.
            # GO TO class 4 - sibling re-dispatch. The target writes an
            # emergency record and transfers back here, so the call is followed
            # by an explicit `continue` that stands for
            # [purchase/pl055.cbl:L499].
            _create__create_anal(st)
            continue

        # 452  move     WS-Analysis-record  to  WS-Value-record.
        _group_move_analysis_into_value(analysis, value)
        # 453  move     zero  to  va-t-this  va-t-last va-t-year
        # 454                     va-v-this  va-v-last va-v-year.
        _zero_the_six_value_totals(value)

        # 456  if       va-second = space
        if value.va_code.va_group.va_second == _SPACE_1:
            # 457           go to  main-exit.
            # GO TO class 3 - section exit.
            return _create__main_exit()

        # 459  move     va-code  to  save-code.
        st.save_code = move.move(
            _va_code_image(value), _D_SAVE_CODE, sending_field=_VAL["va-code"]
        )

        # 461  move     space    to  va-second.
        value.va_code.va_group.va_second = move.move_figurative(
            move.SPACE, _VAL["va-second"]
        )
        # 462  move     va-code  to  WS-Pa-Code.
        _move_into_pa_code(
            analysis,
            move.move_group(
                _va_code_image(value),
                _ANL["ws-pa-code"],
                sending_field=_VAL["va-code"],
                length=3,
            ),
        )

        # 464  move     1 to File-Key-No.
        ctx.file_access.logging_data.file_key_no = 1
        # 465  perform  Analysis-Read-Indexed.
        st.facade.analysis_read_indexed(ctx)
        # 466  if       FS-Reply = 21
        if ctx.file_access.fs_reply == FsReply.INVALID_KEY_ON_START:
            # 467           move  save-code  to  WS-Pa-Code
            _move_into_pa_code(
                analysis,
                move.move_group(
                    st.save_code,
                    _ANL["ws-pa-code"],
                    sending_field=_D_SAVE_CODE,
                    length=3,
                ),
            )
            # 468           go to  main-exit.
            # GO TO class 3 - section exit.
            #
            # ⭐ FINDING [purchase/pl055.cbl:L461, L467-L468] - THIS EXIT
            # RESTORES `WS-Pa-Code` AND LEAVES `va-code` BLANKED. Only
            # [purchase/pl055.cbl:L476] restores `va-code`, and this path never
            # reaches it, so the value record goes back to the caller with the
            # second character of its own key still SPACE from
            # [purchase/pl055.cbl:L461]. Every caller then acts on that key: the
            # read loop writes the accumulated line total under the rolled-up
            # code rather than the specific one [purchase/pl055.cbl:L335] and
            # then takes the `va-second = space` exit at
            # [purchase/pl055.cbl:L340-L341], skipping the second accumulation
            # entirely; `store-specials` stores a whole special total under the
            # rolled-up code [purchase/pl055.cbl:L520]. Observable in
            # `VALUEANAL-REC`: a row that should have been keyed `Pvi` is keyed
            # `Pv `.
            # It is LATENT rather than certain - it fires only when the
            # blanked-second analysis code is itself missing, which a properly
            # seeded `ANALYSIS-REC` makes unlikely because the emergency-create
            # path at [purchase/pl055.cbl:L495-L497] writes both forms. The
            # sales program carries the identical shape [sales/sl055.cbl:L555].
            # Reproduced deliberately per R-4; DO NOT FIX - restoring `va-code`
            # here would move rows between keys.
            return _create__main_exit()

        # 470  move     WS-Analysis-record  to  WS-Value-record
        # FINDING [purchase/pl055.cbl:L470] - no terminating period; the period
        # belongs to the `move zero` that follows at [L472]. Cosmetic.
        _group_move_analysis_into_value(analysis, value)
        # 471  move     zero  to  va-t-this  va-t-last  va-t-year
        # 472                     va-v-this  va-v-last  va-v-year.
        _zero_the_six_value_totals(value)

        # ================================ FINDING A ================================
        # FINDING [purchase/pl055.cbl:L474] cf. [purchase/pl055.cbl:L334-L337] and
        # [purchase/pl055.cbl:L519-L522]
        #   THE ROLL-UP `Value-Write` AT [L474] IS BOTH UNCONDITIONAL AND UNTESTED,
        #   SO ON EVERY RUN IN WHICH THE ROLL-UP ROW ALREADY EXISTS IT ISSUES AN
        #   INSERT THAT FAILS ON A DUPLICATE KEY AND THE FAILURE IS SWALLOWED.
        #
        #   The three statements immediately above are, in order: blank the second
        #   character of the key [L461], group-move the analysis record over the
        #   value record [L470], and zero all six totals [L471-L472]. The write at
        #   [L474] then commits that zeroed image under the ROLLED-UP key. When that
        #   row does not yet exist this is the intended behaviour - it materialises
        #   the roll-up row so the caller's second accumulation has something to
        #   read and rewrite.
        #
        #   What is missing is the `v-exists` discrimination the two structurally
        #   identical sites elsewhere in the program both have: `if v-exists = zero
        #   perform Value-Write else perform Value-Rewrite` at [L334-L337] in the
        #   read loop and at [L519-L522] in `store-specials`. Here the write is
        #   issued unconditionally, and its reply is never inspected.
        #
        #   What actually happens on the duplicate is settled by the handler, not by
        #   guesswork: `Value-Write` reaches `ba070_process_write` in
        #   `acas_posting.dal.acas013_value`, which issues `INSERT INTO
        #   `VALUEANAL-REC` SET ...` and, on a duplicate key, sets `FS-Reply` 22 and
        #   LEAVES THE STORED ROW UNTOUCHED - reproducing
        #   [common/valueMT.cbl:L817-L831], where `1062`, `1022` and SQLSTATE `23000`
        #   all map to 22. So the accumulated totals are NOT lost. ⛔ It is
        #   therefore WRONG to describe this as a lost update, and wrong to "repair"
        #   it as though data were at risk.
        #
        #   The two real consequences, both reproduced:
        #     1. A duplicate INSERT is issued against `VALUEANAL-REC` essentially
        #        every run. `close-files` [L403-L419] guarantees it: `vi` and `vj`
        #        share the roll-up `Pv `, `za` and `zb` share `Pz `, so whichever of
        #        each pair is stored second re-issues the write for a key the first
        #        already created.
        #     2. `create` returns with `FS-Reply` left at 22 rather than at the
        #        success it would carry had the write been guarded. No caller reads
        #        that stale status before overwriting it - the read loop's next read
        #        is [L345] and `store-specials`' is [L526], and both assign
        #        `FS-Reply` - so within `pl055` the stale value is inert. It is
        #        recorded because inertness here is an accident of statement order,
        #        not a property anyone arranged.
        #
        #   Measured, from the ad-hoc walk of one type-3 header against an empty
        #   `VALUEANAL-REC`: duplicate writes are issued for `Pv ` and for `Pz `, and
        #   both rows keep the totals banked before them - `Pv ` holds (1, -11.00)
        #   and `Pz ` holds (2, -1.00), the latter being `za`'s -5.00 plus `zb`'s
        #   +4.00.
        #
        #   This is NOT a transcription artefact of the Purchase side. `sl055` writes
        #   unconditionally at the same point in its own create section,
        #   `perform Value-Write.` [sales/sl055.cbl:L560], immediately after the same
        #   blank-key [sales/sl055.cbl:L547] and zeroing sequence, and likewise
        #   restores `va-code` only afterwards [sales/sl055.cbl:L562]. Both programs
        #   carry it, so it is recorded as a shared legacy defect rather than as a
        #   pl055/sl055 divergence.
        #
        #   Reproduced deliberately per R-4; DO NOT FIX. Guarding this write with a
        #   `v-exists`-style test, or turning it into a `Value-Rewrite`, would remove
        #   a statement the COBOL issues against the database and would change the
        #   status the section returns with - and testing the reply here would add a
        #   control transfer the COBOL does not have, which R-3 forbids outright.
        # ===========================================================================
        # 474  perform  Value-Write.
        st.facade.value_write(ctx)

        # 476  move     save-code  to  va-code  WS-Pa-Code.
        # A TWO-receiver `MOVE`, each receiver converting independently.
        _move_into_va_code(
            value,
            move.move_group(
                st.save_code, _VAL["va-code"], sending_field=_D_SAVE_CODE, length=3
            ),
        )
        _move_into_pa_code(
            analysis,
            move.move_group(
                st.save_code, _ANL["ws-pa-code"], sending_field=_D_SAVE_CODE, length=3
            ),
        )
        # 477  move     1 to File-Key-No.
        ctx.file_access.logging_data.file_key_no = 1
        # 478  perform  Analysis-Read-Indexed.
        st.facade.analysis_read_indexed(ctx)
        # 479  if       FS-Reply = 21
        if ctx.file_access.fs_reply == FsReply.INVALID_KEY_ON_START:
            # 480           go to  main-exit.
            # GO TO class 3 - section exit.
            return _create__main_exit()

        # 482  move     WS-Analysis-record  to  WS-Value-record
        _group_move_analysis_into_value(analysis, value)
        # 483  move     zero  to  va-t-this  va-t-last  va-t-year
        # 484                     va-v-this  va-v-last  va-v-year.
        _zero_the_six_value_totals(value)

        # 486  go       to main-exit.
        # GO TO class 3 - section exit.
        return _create__main_exit()


def _create__create_anal(st: _Pl055State) -> None:
    """`Create-Anal.`   [purchase/pl055.cbl:L488-L499], of `create section.` L441

    Invents an analysis record so the value record has something to be seeded
    from, and jumps back to `Create-Main` to read it.

    ⭐ IT MAY WRITE TWICE. [purchase/pl055.cbl:L495-L497] adds a second
    `Analysis-Write` for the blanked-second-character form of the code, so a
    two-level analysis group gets both its specific and its rolled-up record.

    The `go to create-Main` at [purchase/pl055.cbl:L499] is represented by the
    `continue` in the caller, not by a call from here - see the equivalence
    proof in `_create__create_main`.

    Args:
        st: The program's state.
    """
    ctx = st.ctx
    value = ctx.ws_value_record
    analysis = ctx.ws_analysis_record

    # 489  move     va-code to WS-Pa-Code.
    _move_into_pa_code(
        analysis,
        move.move_group(
            _va_code_image(value),
            _ANL["ws-pa-code"],
            sending_field=_VAL["va-code"],
            length=3,
        ),
    )
    # 490  move     zero to pa-gl.
    analysis.pa_gl = move.move_figurative(move.ZERO, _ANL["pa-gl"])
    # 491  move     spaces to pa-print.
    analysis.pa_print = move.move_figurative(move.SPACES, _ANL["pa-print"])
    # 492  move     "Emergency Name - Missing" to pa-desc.
    # Exactly 24 characters, which is `pa-desc pic x(24)`
    # [copybooks/wsanal.cob:L16] to the byte - it neither truncates nor pads.
    analysis.pa_desc = move.move("Emergency Name - Missing", _ANL["pa-desc"])
    # 493  move     1 to File-Key-No.
    ctx.file_access.logging_data.file_key_no = 1
    # 494  perform  Analysis-Write.
    st.facade.analysis_write(ctx)
    # 495  if       pa-second not = space
    if analysis.ws_pa_code.pa_group.pa_second != _SPACE_1:
        # 496           move space to pa-second
        analysis.ws_pa_code.pa_group.pa_second = move.move_figurative(
            move.SPACE, _ANL["pa-second"]
        )
        # 497           perform Analysis-Write.
        st.facade.analysis_write(ctx)
    # 498  move     1 to Anal-Created.
    st.anal_created = move.move(1, _D_ANAL_CREATED)
    # 499  go       to create-Main.
    # GO TO class 4 - backward retry to the section's first paragraph. Carried
    # by the caller's `continue`; see the equivalence proof there.
    return


def _create__main_exit() -> None:
    """`main-exit.   exit section.`   [purchase/pl055.cbl:L501]

    The `create` section's exit. Named with its section prefix because
    `main-exit.` occurs THREE times in this program - here, at
    [purchase/pl055.cbl:L536] and at [purchase/pl055.cbl:L597] - so paragraph
    names are not unique and a bare `_main_exit` would silently collide.
    """
    _LOG.debug("pl055 create/main-exit  [purchase/pl055.cbl:L501]")


def _va_code_image(value: WsValueRecord) -> str:
    """The three-character byte image of `03 va-code.` [copybooks/wsval.cob:L10].

    A group has no value of its own, only the bytes of its children -
    `va-system`, `va-first`, `va-second` [copybooks/wsval.cob:L11-L14]. Assembled
    here so that a group move out of `va-code` has a sender to work from.
    """
    return "".join(
        (
            move.move(value.va_code.va_system, _VAL["va-system"]),
            move.move(value.va_code.va_group.va_first, _VAL["va-first"]),
            move.move(value.va_code.va_group.va_second, _VAL["va-second"]),
        )
    )


def _pa_code_image(analysis: WsAnalysisRecord) -> str:
    """The three-character byte image of `03 WS-Pa-Code.` [copybooks/wsanal.cob:L10]."""
    return "".join(
        (
            move.move(analysis.ws_pa_code.pa_system, _ANL["pa-system"]),
            move.move(analysis.ws_pa_code.pa_group.pa_first, _ANL["pa-first"]),
            move.move(analysis.ws_pa_code.pa_group.pa_second, _ANL["pa-second"]),
        )
    )


def _move_into_va_code(value: WsValueRecord, image: str) -> None:
    """Scatter a three-character `va-code` image into its three children."""
    value.va_code.va_system = move.move(move.ref_mod(image, 1, 1), _VAL["va-system"])
    value.va_code.va_group.va_first = move.move(
        move.ref_mod(image, 2, 1), _VAL["va-first"]
    )
    value.va_code.va_group.va_second = move.move(
        move.ref_mod(image, 3, 1), _VAL["va-second"]
    )


def _move_into_pa_code(analysis: WsAnalysisRecord, image: str) -> None:
    """Scatter a three-character `WS-Pa-Code` image into its three children."""
    analysis.ws_pa_code.pa_system = move.move(
        move.ref_mod(image, 1, 1), _ANL["pa-system"]
    )
    analysis.ws_pa_code.pa_group.pa_first = move.move(
        move.ref_mod(image, 2, 1), _ANL["pa-first"]
    )
    analysis.ws_pa_code.pa_group.pa_second = move.move(
        move.ref_mod(image, 3, 1), _ANL["pa-second"]
    )


def _group_move_analysis_into_value(
    analysis: WsAnalysisRecord, value: WsValueRecord
) -> None:
    """`move WS-Analysis-record to WS-Value-record.`

    [purchase/pl055.cbl:L452], [purchase/pl055.cbl:L470] and
    [purchase/pl055.cbl:L482].

    A GROUP MOVE, WHICH IS AN ALPHANUMERIC MOVE OF THE WHOLE BYTE IMAGE. No
    child's picture is consulted on either side. The 36-byte sender
    [copybooks/wsanal.cob:L6] lands in the first 36 bytes of the 66-byte
    receiver [copybooks/wsval.cob:L6], which happen to align field for field -
    3-character code, 6-digit ledger number, 24-character description,
    3-character print flag - and the remaining 30 bytes, the six `comp` and
    `comp-3` totals, are SPACE-FILLED. Spaces in a packed field are not a
    number, which is precisely why every one of the three sites is immediately
    followed by a `MOVE ZERO` naming all six. This function therefore carries
    only the four aligned fields; the six are the next statement's business.

    The sender's byte image is materialised at its OWN declared width first,
    because `move_group` pads or truncates against the receiver only - "with no
    width the movement is a byte-image copy of whatever the sender presents",
    per `cobol.move.move_group`. Presenting the sender at 36 characters is what
    makes the 30-byte space fill of the receiver's tail a consequence of the
    record sizes rather than of however many characters this module happened to
    concatenate.
    """
    sender_image = move.move_group(
        _pa_code_image(analysis) + _analysis_tail_image(analysis),
        _ANL["ws-analysis-record"],
        length=_ANALYSIS_RECORD_BYTES,
    )
    image = move.move_group(
        sender_image,
        _VAL["ws-value-record"],
        sending_field=_ANL["ws-analysis-record"],
        length=_VALUE_RECORD_BYTES,
    )
    for name, offset, length in _VALUE_HEAD_LAYOUT:
        piece = move.ref_mod(image, offset, length)
        if name == "va-code":
            _move_into_va_code(value, piece)
        elif name == "va-gl":
            value.va_gl = move.move(piece, _VAL["va-gl"])
        elif name == "va-desc":
            value.va_desc = move.move(piece, _VAL["va-desc"])
        else:
            value.va_print = move.move(piece, _VAL["va-print"])


def _analysis_tail_image(analysis: WsAnalysisRecord) -> str:
    """Bytes 4 to 36 of `WS-Analysis-Record` - everything after the code.

    `Pa-Gl pic 9(6)` [copybooks/wsanal.cob:L15] is zoned DISPLAY, so its bytes
    are its six digits; `Pa-Desc pic x(24)` and `Pa-Print pic xxx`
    [copybooks/wsanal.cob:L16-L17] are already characters.
    """
    return "".join(
        (
            move.move(analysis.pa_gl, _ANL["pa-gl"], sending_field=_ANL["pa-gl"]).rjust(
                6, "0"
            )
            if isinstance(analysis.pa_gl, str)
            else f"{int(analysis.pa_gl):06d}",
            move.move(analysis.pa_desc, _ANL["pa-desc"]),
            move.move(analysis.pa_print, _ANL["pa-print"]),
        )
    )


def _zero_the_six_value_totals(value: WsValueRecord) -> None:
    """`move zero to va-t-this va-t-last va-t-year va-v-this va-v-last va-v-year.`

    [purchase/pl055.cbl:L453-L454], [purchase/pl055.cbl:L471-L472] and
    [purchase/pl055.cbl:L483-L484] - one statement, SIX receivers, each
    converting the figurative constant under its own description: three
    `pic 9(5) comp` counts and three `pic s9(8)v99 comp-3` money fields
    [copybooks/wsval.cob:L18-L23].
    """
    (
        value.va_t_this,
        value.va_t_last,
        value.va_t_year,
        value.va_v_this,
        value.va_v_last,
        value.va_v_year,
    ) = move.move_to_all(
        move.ZERO,
        (
            _VAL["va-t-this"],
            _VAL["va-t-last"],
            _VAL["va-t-year"],
            _VAL["va-v-this"],
            _VAL["va-v-last"],
            _VAL["va-v-year"],
        ),
    )


#
#  store-specials section.   [purchase/pl055.cbl:L503]
#


def _store_specials(st: _Pl055State) -> None:
    """`store-specials section.`   [purchase/pl055.cbl:L503-L534]

    Folds one special total - a count into the two count fields and a money
    figure into the two money fields - into a value-analysis group, creating
    the group first if it is missing, then repeats the whole thing for the
    rolled-up form with the second character blanked.

    ⭐ THE TWICE-OVER PATTERN IS NOT FACTORED, for the same reason it is not
    factored in `read-loop`: the first pass chooses `Value-Write` or
    `Value-Rewrite` from `v-exists` [purchase/pl055.cbl:L519-L522] and the
    second always rewrites [purchase/pl055.cbl:L534]. They are two different
    blocks that happen to share four arithmetic statements.

    ⭐ IT ADDS. `pl060`'s deduction analysis later SUBTRACTS from these same
    groups, which is why the direction is worth stating rather than assuming.

    Args:
        st: The program's state.
    """
    ctx = st.ctx
    value = ctx.ws_value_record

    # 506  move     1  to  v-exists.
    st.v_exists = move.move(1, _D_V_EXISTS)

    # 508  move     1 to File-Key-No.
    ctx.file_access.logging_data.file_key_no = 1
    # 509  perform  Value-Read-Indexed.
    st.facade.value_read_indexed(ctx)
    # 510  if       FS-Reply = 21
    # 21 alone, not `21 or 23` - see the note in `_create__create_main`.
    if ctx.file_access.fs_reply == FsReply.INVALID_KEY_ON_START:
        # 511           perform  create
        _create(st)
        # 512           move zero to v-exists.
        st.v_exists = move.move_figurative(move.ZERO, _D_V_EXISTS)

    # 514  add      work-3 to  va-t-this.
    value.va_t_this = arithmetic.add_to(
        st.work_3, receiver_value=value.va_t_this, receiving=_VAL["va-t-this"]
    )
    # 515  add      work-3 to  va-t-year.
    value.va_t_year = arithmetic.add_to(
        st.work_3, receiver_value=value.va_t_year, receiving=_VAL["va-t-year"]
    )
    # 516  add      work-2 to  va-v-this.
    value.va_v_this = arithmetic.add_to(
        st.work_2, receiver_value=value.va_v_this, receiving=_VAL["va-v-this"]
    )
    # 517  add      work-2 to  va-v-year.
    value.va_v_year = arithmetic.add_to(
        st.work_2, receiver_value=value.va_v_year, receiving=_VAL["va-v-year"]
    )

    # 519  if       v-exists = zero
    if arithmetic.compare(st.v_exists, 0) == 0:
        # 520           perform Value-Write
        st.facade.value_write(ctx)
    else:
        # 522           perform Value-Rewrite.
        st.facade.value_rewrite(ctx)

    # 524  move     space  to  va-second.
    value.va_code.va_group.va_second = move.move_figurative(
        move.SPACE, _VAL["va-second"]
    )
    # 525  move     1 to File-Key-No.
    ctx.file_access.logging_data.file_key_no = 1
    # 526  perform  Value-Read-Indexed.
    st.facade.value_read_indexed(ctx)
    # 527  if       FS-Reply = 21
    if ctx.file_access.fs_reply == FsReply.INVALID_KEY_ON_START:
        # 528           go to main-exit.
        # GO TO class 3 - section exit.
        return _store_specials__main_exit()

    # 530  add      work-3 to  va-t-this.
    value.va_t_this = arithmetic.add_to(
        st.work_3, receiver_value=value.va_t_this, receiving=_VAL["va-t-this"]
    )
    # 531  add      work-3 to  va-t-year.
    value.va_t_year = arithmetic.add_to(
        st.work_3, receiver_value=value.va_t_year, receiving=_VAL["va-t-year"]
    )
    # 532  add      work-2 to  va-v-this.
    value.va_v_this = arithmetic.add_to(
        st.work_2, receiver_value=value.va_v_this, receiving=_VAL["va-v-this"]
    )
    # 533  add      work-2 to  va-v-year.
    value.va_v_year = arithmetic.add_to(
        st.work_2, receiver_value=value.va_v_year, receiving=_VAL["va-v-year"]
    )
    # 534  perform  Value-Rewrite.
    st.facade.value_rewrite(ctx)

    # FALL-THROUGH into `main-exit.` [purchase/pl055.cbl:L536].
    return _store_specials__main_exit()


def _store_specials__main_exit() -> None:
    """`main-exit.   exit section.`   [purchase/pl055.cbl:L536]

    The `store-specials` section's exit - the second of the three paragraphs in
    this program named `main-exit`, hence the section-qualified name.
    """
    _LOG.debug("pl055 store-specials/main-exit  [purchase/pl055.cbl:L536]")


#
#  extract section.   [purchase/pl055.cbl:L538]
#


def _extract(st: _Pl055State) -> None:
    """`extract section.`   [purchase/pl055.cbl:L538-L595]

    Builds one OTM4 open-item record from the invoice header, negates four
    money fields for a credit note, adds the invoice total into the purchase
    period totals and appends the record to the work sequence.

    FINDING - THE SECTION'S OWN COMMENT PROMISES FILTERS IT DOES NOT HAVE.

        *> only Process header records, drop pro-formas.
                                                   [purchase/pl055.cbl:L541]
        *>   ignore records which have already been copied.
                                                   [purchase/pl055.cbl:L542]

    Only the second half is implemented, by `if applied`
    [purchase/pl055.cbl:L544]. There is NO proforma test anywhere in `pl055` -
    the sales program has one, `if ih-type = 4` [sales/sl055.cbl:L430], routed
    through a skip paragraph this program does not have. The comment is a
    leftover; it is quoted rather than acted on. Related: divergence 7.

    ⭐⭐ DIVERGENCE 1 - THE NEGATION BLOCK NEGATES FOUR FIELDS, NOT NINE.

        if       ih-type = 3                       [purchase/pl055.cbl:L571]
                 multiply  -1  by  oi-net          [purchase/pl055.cbl:L572]
                 multiply  -1  by  oi-carriage     [purchase/pl055.cbl:L573]
                 multiply  -1  by  oi-vat          [purchase/pl055.cbl:L574]
                 multiply  -1  by  oi-c-vat.       [purchase/pl055.cbl:L575]

    The sales program negates NINE [sales/sl055.cbl:L658-L666], and the first
    of its nine is `oi-deduct-amt` - which `pl055` DOES populate, at
    [purchase/pl055.cbl:L564], and does NOT negate. ⛔ Adding a fifth
    `multiply` would be a behaviour change and a rule R-3 violation.

    ⭐⭐ DIVERGENCE 2 - THE INVOICE TOTAL HAS FOUR ADDENDS, NOT NINE, AND IT
    SUMS THE UNNEGATED HEADER FIELDS.

        add ih-net ih-carriage ih-vat ih-c-vat giving ws-inv-amt.
                                                   [purchase/pl055.cbl:L580]

    Note which fields those are: `ih-`, the header, NOT the `oi-` copies that
    were just negated. So for a credit note the extracted row carries negative
    money while `ws-inv-amt` holds the POSITIVE sum, and
    [purchase/pl055.cbl:L584] adds that positive figure into
    `pl-credit-notes-this-month`. The sales program does exactly the same with
    its nine [sales/sl055.cbl:L671-L673], so this is the codebase's convention
    rather than a slip. ⛔ Do not "consistently" negate it.

    # AMBIGUITY Q-PL055-3 - the negated `oi-` row against the unnegated `ih-`
    # sum. That a credit note leaves a negative extract row and a positive
    # period total is what the source says; whether the stored period total
    # then reads as the accountant intends is a question about the SYSTEM, not
    # about this transcription. Expected values come from the oracle (rule
    # R-6), never from reasoning about what the total ought to be.

    ⭐⭐ PERIOD TOTALS - SITES 6 AND 7 OF THE NINE IN THE WHOLE MIGRATION.
    [purchase/pl055.cbl:L582] and [purchase/pl055.cbl:L584] write
    `pl-invoices-this-month` [copybooks/wssys4.cob:L23] and
    `pl-credit-notes-this-month` [copybooks/wssys4.cob:L24]. Agent Action Plan
    section 0.6.4 records that the nine sites are *"the sole writers"* of the
    totals record, which is what makes the period-end scenario checkable by
    inspecting one table. Both stores TRUNCATE - `pl055` has no `ROUNDED`
    anywhere.

    ⭐ DIVERGENCE 12 - `ih-status` ONLY, NOT `ih-status-A`.

        move     "Z"  to  ih-status.   *> 07/01/18 was "z"
                                                   [purchase/pl055.cbl:L586]
        move     "Z"  to  ih-status.               [sales/sl055.cbl:L679]
        move     "A"  to  ih-status-A.             [sales/sl055.cbl:L680]

    `ih-status-A` does not exist in `plwspinv2.cob` at all, so there is nothing
    here to set even if one wanted to. Note the case: UPPER here, under the
    maintainer's own dated note, while `ih-update` and `il-update` take LOWER
    case at [purchase/pl055.cbl:L396] and [purchase/pl055.cbl:L358]. The
    inconsistency is internal to `pl055` and both halves are stored as written.

    Args:
        st: The program's state.
    """
    ctx = st.ctx
    header = ctx.invoice_header
    fig = ctx.invoice_fig
    s4 = st.system_record_4.purchase_ledger_data

    # 544  if       applied
    if condition_names.evaluate(
        "applied", header.ih_status, copybook="copybooks/plwspinv2.cob"
    ):
        # 545           go to  main-exit.
        # GO TO class 3 - section exit.
        return _extract__main_exit()

    # 547   initialise OI-Header.   *> 07/01/18  JIC
    # ⭐⭐ DIVERGENCE 5 - British spelling and NO `WITH FILLER`, unlike
    # [sales/sl055.cbl:L635]. See `_initialise_oi_header` for the measured
    # analysis and AMBIGUITY Q-PL055-1. ⛔ Do not add `WITH FILLER`.
    st.oi_header = _initialise_oi_header()
    oi = st.oi_header

    # 548  move     ih-supplier to  oi-supplier.
    # Group to group, seven characters: `03 ih-supplier.`
    # [copybooks/plwspinv2.cob:L24] into `07 OI-Supplier.`
    # [copybooks/plwsoi.cob:L12].
    _move_into_oi_supplier(
        oi,
        move.move_group(
            _ih_supplier_image(header),
            _OI_CUSTOMER["oi_supplier"],
            sending_field=pinvoice_descriptor_for(IhInvoiceHeader, "ih_supplier"),
            length=7,
        ),
    )
    # 549  move     ih-invoice  to  oi-invoice.
    oi.oi_key.oi_invoice = move.move(
        header.ih_invoice,
        _OI_KEY["oi_invoice"],
        sending_field=pinvoice_descriptor_for(IhInvoiceHeader, "ih_invoice"),
    )
    # 550  move     ih-date     to  oi-date.
    oi.oi_date = move.move(
        header.ih_date,
        _OI["oi_date"],
        sending_field=pinvoice_descriptor_for(IhInvoiceHeader, "ih_date"),
    )
    # 551  move     zero        to  oi-b-nos oi-b-item.
    oi.oi_batch.oi_b_nos, oi.oi_batch.oi_b_item = move.move_to_all(
        move.ZERO, (_OI_BATCH["oi_b_nos"], _OI_BATCH["oi_b_item"])
    )
    # 552  move     ih-type     to  oi-type.
    oi.oi_type = move.move(
        header.ih_type,
        _OI["oi_type"],
        sending_field=pinvoice_descriptor_for(IhInvoiceHeader, "ih_type"),
    )
    # 553  move     ih-ref      to  oi-ref.
    oi.oi_ref = move.move(
        header.ih_ref,
        _OI["oi_ref"],
        sending_field=pinvoice_descriptor_for(IhInvoiceHeader, "ih_ref"),
    )
    # 554  move     ih-order    to  oi-order.
    oi.oi_order = move.move(
        header.ih_order,
        _OI["oi_order"],
        sending_field=pinvoice_descriptor_for(IhInvoiceHeader, "ih_order"),
    )
    # 555  move     zero        to  oi-p-c.
    oi.filler_1.oi_p_c = move.move_figurative(move.ZERO, _OI_MONEY["oi_p_c"])
    # 556  move     ih-net      to  oi-net.
    _set_oi_net(
        oi,
        move.move(
            fig.ih_net,
            _OI_MONEY["oi_net"],
            sending_field=pinvoice_descriptor_for(IhFig2, "ih_net"),
        ),
    )
    # 557  move     zero        to  oi-extra.
    oi.filler_1.oi_extra = move.move_figurative(move.ZERO, _OI_MONEY["oi_extra"])
    # 558  move     ih-carriage to  oi-carriage.
    oi.filler_1.oi_carriage = move.move(
        fig.ih_carriage,
        _OI_MONEY["oi_carriage"],
        sending_field=pinvoice_descriptor_for(IhFig2, "ih_carriage"),
    )
    # 559  move     ih-vat      to  oi-vat.
    oi.filler_1.oi_vat = move.move(
        fig.ih_vat,
        _OI_MONEY["oi_vat"],
        sending_field=pinvoice_descriptor_for(IhFig2, "ih_vat"),
    )
    # 560  move     zero        to  oi-discount.
    oi.filler_1.oi_discount = move.move_figurative(move.ZERO, _OI_MONEY["oi_discount"])
    # 561  move     ih-c-vat    to  oi-c-vat.
    oi.filler_1.oi_c_vat = move.move(
        fig.ih_c_vat,
        _OI_MONEY["oi_c_vat"],
        sending_field=pinvoice_descriptor_for(IhFig2, "ih_c_vat"),
    )
    # 562  move     zero        to  oi-e-vat.
    oi.filler_1.oi_e_vat = move.move_figurative(move.ZERO, _OI_MONEY["oi_e_vat"])
    # 563  move     zero        to  oi-paid.
    oi.filler_1.oi_paid = move.move_figurative(move.ZERO, _OI_MONEY["oi_paid"])
    # 564  move     ih-deduct-amt  to  oi-deduct-amt.
    # FINDING - the sender is UNSIGNED, `pic 999v99 comp`
    # [copybooks/plwspinv2.cob:L46], and the receiver is SIGNED, `pic s999v99
    # comp` [copybooks/plwsoi.cob:L57]. Widening a sign in is harmless; it is
    # noted because it is the field divergence 1 declines to negate.
    oi.oi_deduct_amt = move.move(
        header.ih_deduct_amt,
        _OI["oi_deduct_amt"],
        sending_field=pinvoice_descriptor_for(IhInvoiceHeader, "ih_deduct_amt"),
    )
    # 565  move     zero           to  oi-deduct-vat.
    oi.oi_deduct_vat = move.move_figurative(move.ZERO, _OI["oi_deduct_vat"])
    # 566  move     ih-deduct-days to  oi-deduct-days.
    oi.oi_deduct_days = move.move(
        header.ih_deduct_days,
        _OI["oi_deduct_days"],
        sending_field=pinvoice_descriptor_for(IhInvoiceHeader, "ih_deduct_days"),
    )
    # 567  move     ih-days     to  oi-days.
    oi.oi_days = move.move(
        header.ih_days,
        _OI["oi_days"],
        sending_field=pinvoice_descriptor_for(IhInvoiceHeader, "ih_days"),
    )
    # 568  move     zero        to  oi-status oi-date-cleared.
    oi.oi_status, oi.oi_date_cleared = move.move_to_all(
        move.ZERO, (_OI["oi_status"], _OI["oi_date_cleared"])
    )
    # 569  move     space       to  oi-applied oi-hold-flag.
    # TWO receivers. FINDING [purchase/pl055.cbl:L569] vs
    # [sales/sl055.cbl:L655] - the sales statement has THREE, adding
    # `oi-unapl`. `pl055` leaves `oi-unapl` [copybooks/plwsoi.cob:L40] at
    # whatever the `initialise` gave it, which is a space anyway.
    oi.oi_applied, oi.oi_hold_flag = move.move_to_all(
        move.SPACE, (_OI["oi_applied"], _OI["oi_hold_flag"])
    )

    # 571  if       ih-type = 3
    if arithmetic.compare(header.ih_type, 3) == 0:
        # ⭐⭐ DIVERGENCE 1 - FOUR fields, and `oi-deduct-amt` is deliberately
        # not one of them. [purchase/pl055.cbl:L571-L575] against the nine at
        # [sales/sl055.cbl:L658-L666]. ⛔ DO NOT add a fifth `multiply`.
        # Every one is the no-`GIVING` form: the receiver is the SECOND
        # operand, so `multiply -1 by oi-net` means `oi-net = -1 * oi-net`.
        # 572           multiply  -1  by  oi-net
        _set_oi_net(oi, arithmetic.multiply_by(-1, oi.filler_1.oi_net, _OI_MONEY["oi_net"]))
        # 573           multiply  -1  by  oi-carriage
        oi.filler_1.oi_carriage = arithmetic.multiply_by(
            -1, oi.filler_1.oi_carriage, _OI_MONEY["oi_carriage"]
        )
        # 574           multiply  -1  by  oi-vat
        oi.filler_1.oi_vat = arithmetic.multiply_by(
            -1, oi.filler_1.oi_vat, _OI_MONEY["oi_vat"]
        )
        # 575           multiply  -1  by  oi-c-vat.
        oi.filler_1.oi_c_vat = arithmetic.multiply_by(
            -1, oi.filler_1.oi_c_vat, _OI_MONEY["oi_c_vat"]
        )

    # 577  move     ih-cr to oi-cr.
    # AFTER the negation block, not before - the order is the source's.
    oi.oi_cr = move.move(
        header.ih_cr,
        _OI["oi_cr"],
        sending_field=pinvoice_descriptor_for(IhInvoiceHeader, "ih_cr"),
    )

    # 579  if       ih-type not = 1                *> not Receipts
    if arithmetic.compare(header.ih_type, 1) != 0:
        # 580           add ih-net ih-carriage ih-vat ih-c-vat giving ws-inv-amt.
        # ⭐⭐ DIVERGENCE 2 - FOUR addends, and they are the UNNEGATED `ih-`
        # fields. Nine addends at [sales/sl055.cbl:L671-L673]. A variadic
        # `ADD ... GIVING` sums at extended intermediate precision and
        # quantizes ONCE into `ws-inv-amt`, truncating - there is no `ROUNDED`.
        st.ws_inv_amt = arithmetic.add_giving(
            fig.ih_net,
            fig.ih_carriage,
            fig.ih_vat,
            fig.ih_c_vat,
            receiving=_D_INV_AMT,
        )
    # 581  if       ih-type = 2                    *> Invoice
    if arithmetic.compare(header.ih_type, 2) == 0:
        # 582           add ws-inv-amt to pl-invoices-this-month.
        # PERIOD TOTAL - site 6 of the nine. `pl-invoices-this-month`
        # [copybooks/wssys4.cob:L23], `s9(8)v99 comp-3`, key
        # SYSTOT-REC.PL-INVOICES-THIS-MONTH.
        s4.pl_invoices_this_month = arithmetic.add_to(
            st.ws_inv_amt,
            receiver_value=s4.pl_invoices_this_month,
            receiving=_S4["pl-invoices-this-month"],
        )
    # 583  if       ih-type = 3                    *> Cr. Note
    if arithmetic.compare(header.ih_type, 3) == 0:
        # 584           add ws-inv-amt to pl-credit-notes-this-month.
        # PERIOD TOTAL - site 7 of the nine. `pl-credit-notes-this-month`
        # [copybooks/wssys4.cob:L24]. The figure added is POSITIVE, because
        # [L580] summed the unnegated header - see AMBIGUITY Q-PL055-3.
        s4.pl_credit_notes_this_month = arithmetic.add_to(
            st.ws_inv_amt,
            receiver_value=s4.pl_credit_notes_this_month,
            receiving=_S4["pl-credit-notes-this-month"],
        )

    # 586  move     "Z"  to  ih-status.   *> 07/01/18 was "z"
    # ⭐ DIVERGENCE 12 - UPPER case, and `ih-status` alone. The maintainer's own
    # dated note is kept because rule R-5 asks for exactly this evidence.
    header.ih_status = move.move(
        "Z", pinvoice_descriptor_for(IhInvoiceHeader, "ih_status")
    )
    # 587  write    open-item-record-4.
    # DIVERGENCE 13 - the FD record name, where the sales program writes the
    # working-storage name [sales/sl055.cbl:L681]. Measured to be the SAME
    # 113-byte area in `pl055`, because `fdoi4.cob` and `plwsoi.cob` are both in
    # its FILE SECTION [purchase/pl055.cbl:L120-L121]; the divergence is which
    # of two names for one storage the programmer typed. See STRUCTURAL NOTES.
    st.open_item_file_4.write(oi)
    # 588  if       fs-reply not = zero
    if ctx.file_access.fs_reply != FsReply.SUCCESS:
        # 589           perform  a01-Eval-Status
        _a01_eval_status(st)
        # 590-593       display PL204 / fs-reply / Exception-Msg / PL006
        _LOG.error(
            "%s fs-reply=%s %s",
            _PL204,
            ctx.file_access.fs_reply,
            st.exception_msg,
        )
        _LOG.error("%s", _PL006)
        # 594           accept   ws-reply ...
        # Dropped: an acknowledgement pause.
        #
        # A REJECTION CLASS WITH A PARTIAL EFFECT, RECORDED. There is no retry,
        # no abort and no control transfer here: the invoice's header has
        # already been stamped `"Z"` at [L586] and will be rewritten by the
        # caller at [purchase/pl055.cbl:L397], but its OTM4 row is missing, so
        # `pl060` will never see it. The sequence is left short and the walk
        # continues. ⛔ Rule R-3 forbids adding either recovery.
        #
        # AMBIGUITY Q-PL055-4 - the disposition of a failed write at
        # [purchase/pl055.cbl:L588]. Whether the compiled program leaves the
        # header stamped as extracted while the extract row is absent is a
        # question for the oracle, not one to resolve by adding a rollback.
    # 595  end-if.

    # FALL-THROUGH into `main-exit.` [purchase/pl055.cbl:L597].
    return _extract__main_exit()


def _extract__main_exit() -> None:
    """`main-exit.   exit.`   [purchase/pl055.cbl:L597]

    ⭐ DIVERGENCE 18 - A PLAIN `EXIT`, NOT `EXIT SECTION`. The other two
    sections end `main-exit.   exit section.` [purchase/pl055.cbl:L501, L536];
    this one ends with a bare `EXIT`, which in COBOL is a no-operation - it
    does not terminate the section. Control therefore arrives at the next
    statement, and the next statement is the `zz070-Convert-Date section.`
    header [purchase/pl055.cbl:L599], which ends the `extract` section anyway.
    So the outcome is the same and the source text is not.

    # EXIT (plain, not EXIT SECTION) [purchase/pl055.cbl:L597]

    Kept as its own named function because it is the third paragraph named
    `main-exit` in this program and rule R-5 requires one function per
    paragraph regardless of what the paragraph does.
    """
    _LOG.debug("pl055 extract/main-exit  [purchase/pl055.cbl:L597]")


def _ih_supplier_image(header: IhInvoiceHeader) -> str:
    """The seven-character image of `03 ih-supplier.` [copybooks/plwspinv2.cob:L24].

    `05 ih-nos pic x(6)` and `05 ih-check pic 9`
    [copybooks/plwspinv2.cob:L25-L26], so six characters and one digit.
    """
    nos = move.move(header.ih_supplier.ih_nos, _OI_SUPPLIER["oi_nos"])
    check = f"{int(header.ih_supplier.ih_check):01d}"
    return nos + check


def _move_into_oi_supplier(oi: OiHeader, image: str) -> None:
    """Scatter a seven-character `oi-supplier` image into its two children.

    `07 OI-Supplier.` [copybooks/plwsoi.cob:L12] over `09 OI-Nos Pic X(6)` and
    `09 OI-Check Pic 9` [copybooks/plwsoi.cob:L13-L14].
    """
    supplier = oi.oi_key.oi_customer.oi_supplier
    supplier.oi_nos = move.move(move.ref_mod(image, 1, 6), _OI_SUPPLIER["oi_nos"])
    supplier.oi_check = move.move(move.ref_mod(image, 7, 1), _OI_SUPPLIER["oi_check"])


def _set_oi_net(oi: OiHeader, value: Decimal) -> None:
    """Store `oi-net` and carry `oi-approp` with it - they are one field.

    `05 OI-Approp redefines OI-Net pic s9(7)v99.` [copybooks/plwsoi.cob:L44]
    describes the SAME bytes as `05 OI-Net` [copybooks/plwsoi.cob:L43]. A
    COBOL store into one is visible through the other for free; two Python
    attributes are not, so the redefinition is honoured explicitly. `pl055`
    never reads `oi-approp`, but `pl060` moves the whole `OI-Header` into
    `WS-OTM5-Record` [purchase/pl060.cbl:L521], so an inconsistent pair would
    escape this program.
    """
    oi.filler_1.oi_net = value
    oi.filler_1.oi_approp = value


#
#  zz070-Convert-Date section.   [purchase/pl055.cbl:L599]
#


def _zz070_convert_date(st: _Pl055State) -> None:
    """`zz070-Convert-Date section.`   [purchase/pl055.cbl:L599-L624]

    Renders `to-day` into `ws-date` in whichever of the three presentations the
    system record selects.

        move     to-day to ws-date.                [purchase/pl055.cbl:L607]
        if       Date-Form = zero
                 move 1 to Date-Form.              [purchase/pl055.cbl:L609-L610]
        if       Date-UK   go to zz070-Exit.       [purchase/pl055.cbl:L611-L612]
        if       Date-USA  ...swap...  go to zz070-Exit.
                                                   [purchase/pl055.cbl:L613-L617]
        move     "ccyy/mm/dd" to ws-date.          [purchase/pl055.cbl:L621]
        move     to-day (7:4) to ws-Intl-Year.     [purchase/pl055.cbl:L622]
        move     to-day (4:2) to ws-Intl-Month.    [purchase/pl055.cbl:L623]
        move     to-day (1:2) to ws-Intl-Days.     [purchase/pl055.cbl:L624]

    THE BODY IS DELEGATED, NOT RE-IMPLEMENTED. This section is byte-identical
    in all ten programs that carry it, which is the one place where
    consolidation is unambiguously safe because the bodies are textually
    equivalent. The two `go to zz070-Exit` transfers [purchase/pl055.cbl:L612,
    L617] are class 3 - section exits - and live inside the consolidated
    implementation along with the 1-based reference modification of
    [purchase/pl055.cbl:L622-L624].

    ⚠️ IT MUTATES THE SYSTEM RECORD, AND THAT IS DIFF-VISIBLE. `Date-Form`
    [copybooks/wssystem.cob:L128] is a `SYSTEM-REC` column, and
    [purchase/pl055.cbl:L609-L610] defaults it to 1 in place when it is zero.
    So merely converting a date for display can change a stored column. The
    consolidated helper returns the possibly-updated value and it is stored
    back here, because dropping it would lose a write to `SYSTEM-REC`.

    ⛔ `pl055` HAS NO `zz050`, NO `zz060` AND NO DATE-MODULE WRAPPER. It does
    not `copy "wsmaps03.cob"` and never calls `maps04`, so the wrapper-naming
    inconsistency the Agent Action Plan records as anomaly A-22 at
    [general/gl070.cbl:L603-L609] CANNOT ARISE HERE.

    Args:
        st: The program's state.
    """
    system_data = st.ctx.system_record.system_data_block
    # 607-624, including the `Date-Form` default at L609-L610.
    #
    # GO TO class 3 - section exit.  `if Date-UK go to zz070-Exit.`
    #   [purchase/pl055.cbl:L611-L612] -> `zz070-Exit.` [purchase/pl055.cbl:L626].
    #   Carried inside the consolidated helper as an early return; the UK form
    #   needs no reformatting because `ws-date` already holds `to-day`.
    # GO TO class 3 - section exit.  `if Date-USA ...swap... go to zz070-Exit.`
    #   [purchase/pl055.cbl:L613-L617] -> `zz070-Exit.` [purchase/pl055.cbl:L626].
    #   Likewise an early return, taken after the day/month swap through
    #   `ws-swap` [purchase/pl055.cbl:L183].
    # Both are class 3 by shape - a forward transfer to the section's trailing
    # exit label, skipping no statement that would otherwise run - and both live
    # in `dates.zz070_convert_date` because this section is textually identical
    # in all ten carriers. They are annotated here, at the call site, so that the
    # per-site census rule R-5 asks for is complete for `pl055` even though the
    # bodies are shared.
    system_data.date_form = zz070_convert_date(
        st.ws_date_formats, st.to_day, system_data.date_form
    )
    _zz070_exit()


def _zz070_exit() -> None:
    """`zz070-Exit.` / `exit section.`   [purchase/pl055.cbl:L626-L627]

    The target of the two class-3 transfers at [purchase/pl055.cbl:L612] and
    [purchase/pl055.cbl:L617]. It carries nothing but the `exit section.` and is
    retained as a named function under rule R-5.
    """
    _LOG.debug("pl055 zz070-Exit  [purchase/pl055.cbl:L626-L627]")


#
#  a01-Eval-Status section.   [purchase/pl055.cbl:L629]
#


def _a01_eval_status(st: _Pl055State) -> None:
    """`a01-Eval-Status section.`   [purchase/pl055.cbl:L629-L632]

        move     spaces to exception-msg.          [purchase/pl055.cbl:L630]
        copy "FileStat-Msgs.cpy"  replacing STATUS by fs-reply
                                            msg    by exception-msg.
                                                   [purchase/pl055.cbl:L631-L632]

    Turns a file status into a human-readable message. It is DIAGNOSTIC ONLY:
    its single caller [purchase/pl055.cbl:L589] uses the result in a `display`
    and nothing else, and the section alters no control flow and touches no
    table.

    ⭐ DIVERGENCE 14 - IT HAS NO EXIT PARAGRAPH. The sales program closes the
    equivalent section with `a01-exit.   exit section.` [sales/sl055.cbl:L729];
    `pl055` ends at the `copy` and lets the following `copy
    "Proc-ACAS-FH-Calls.cob"` [purchase/pl055.cbl:L634] terminate it. Recorded,
    not corrected - there is no paragraph here to give a function to.

    Args:
        st: The program's state, whose `exception_msg` this fills.
    """
    # 630  move     spaces to exception-msg.
    st.exception_msg = move.move_figurative(
        move.SPACES, _ws("pic x(25)", "Exception-Msg", 126)
    )
    # 631-632  the FileStat-Msgs.cpy table, fs-reply -> exception-msg.
    # The mapping itself belongs to the shared status vocabulary rather than to
    # this program, so the reply's own name is used as the message text. No
    # branch depends on it.
    st.exception_msg = move.move(
        _fs_reply_message(st.ctx.file_access.fs_reply),
        _ws("pic x(25)", "Exception-Msg", 126),
    )


def _fs_reply_message(fs_reply: int) -> str:
    """One `FileStat-Msgs.cpy` row - the text for a file status.

    `copybooks/FileStat-Msgs.cpy` is a flat `evaluate` over the status value.
    The statuses this program can actually see are the ones the data-access
    layer publishes, so the published enumeration names them rather than a
    transcription of the copybook's literals: an unknown value must still
    produce text, because the COBOL's own fall-through leaves `exception-msg`
    spaces and the display prints the number beside it either way.
    """
    try:
        return FsReply(fs_reply).name.replace("_", " ").title()
    except ValueError:
        return f"Unmapped status {fs_reply}"


#
#  The program entry point.   [purchase/pl055.cbl:L239-L243]
#


def run(
    ws_calling_data: WsCallingData,
    system_record: SystemRecord,
    system_record_4: SystemRecord4,
    to_day: str,
    file_defs: FileDefs,
    *,
    facade: ModuleType | None = None,
    file_access: FileAccess | None = None,
    acas_dal_common_data: AcasDalCommonData | None = None,
    ws_value_record: WsValueRecord | None = None,
    ws_analysis_record: WsAnalysisRecord | None = None,
    ws_pinvoice_record: WsPInvoiceRecord | None = None,
    invoice_header: IhInvoiceHeader | None = None,
    invoice_line: IlInvoiceLine | None = None,
    open_item_file_4: _OpenItemFile4 | None = None,
) -> None:
    """Run `pl055`, the Purchase Invoice Post Extract.

    THE LINKAGE, VERBATIM  [purchase/pl055.cbl:L239-L243]

        procedure division using ws-calling-data
                                 system-record
                                 system-record-4
                                 to-day
                                 file-defs.

    The five positional parameters are those five operands in that order. This
    is the SL/PL five-parameter shape shared by all six Sales and Purchase
    modules, and it differs from the General Ledger family, which omits
    `system-record-4`, and from the IRS program, which takes neither the
    calling-data block nor the run date.

    HOW EACH OF THE FIVE IS USED.
      * `ws_calling_data` - read for `WS-Caller` at [purchase/pl055.cbl:L283]
        and [purchase/pl055.cbl:L428]; WRITTEN at [purchase/pl055.cbl:L286],
        which sets `WS-Term-Code` to 8 on the abort path.
      * `system_record` - read for `File-System-Used` at
        [purchase/pl055.cbl:L266]; WRITTEN at [purchase/pl055.cbl:L610], which
        defaults `Date-Form`.
      * `system_record_4` - WRITTEN at [purchase/pl055.cbl:L582] and
        [purchase/pl055.cbl:L584], the two period totals. Not persisted here:
        the menu's `overrewrite` paragraph does that
        [purchase/purchase.cbl:L621-L651].
      * `to_day` - read at [purchase/pl055.cbl:L607] and, by reference
        modification, at [purchase/pl055.cbl:L622-L624]. The ONLY source of
        date information in the program, which is why `pl055` needs no clock.
      * `file_defs` - passed through to every handler call. `file-15`
        [copybooks/wsnames.cob:L32] and `file-28`
        [copybooks/wsnames.cob:L45] are the two members that matter here.

    THE KEYWORD-ONLY PARAMETERS ARE A PYTHON NECESSITY, NOT AN ADDED FEATURE.
    A COBOL sub-program shares its records with the run unit: `WS-Value-Record`,
    `WS-Analysis-Record`, `WS-PInvoice-Record`, `File-Access` and
    `ACAS-DAL-Common-data` are all `copy`-included working storage
    [purchase/pl055.cbl:L128-L135, L225] that the handler calls mutate in place.
    Python has no equivalent ambient scope, so those areas are accepted here
    and default to freshly initialised ones. NOTHING about them is a new input:
    every default is the record's own initial state, and no behaviour depends on
    which route supplied it. Accepting them also lets `pl060` be handed the same
    OTM4 sequence this program fills, exactly as the COBOL hands it the same
    file.

    `facade` is injected for one measured reason: `acas_posting.dal.facade` is
    not yet generated, so importing it at module scope would make this module
    unimportable. It is resolved at call time, which is also when a test can
    substitute one. The import form is the Agent Action Plan's own, section
    0.4.3 - `from acas_posting.dal import facade`.

    Args:
        ws_calling_data: `01 WS-Calling-Data.` [copybooks/wscall.cob:L6-L14].
        system_record: `01 System-Record.` [copybooks/wssystem.cob].
        system_record_4: `01 System-Record-4.` [copybooks/wssys4.cob:L8].
        to_day: `01 to-day pic x(10).` [purchase/pl055.cbl:L237], the run date
            as `DD/MM/CCYY`.
        file_defs: `01 File-Defs.` [copybooks/wsnames.cob:L13].
        facade: The entity-named data-access facade. `pl055` copies
            `Proc-ACAS-FH-Calls.cob` [purchase/pl055.cbl:L634], so it uses the
            ENTITY-named vocabulary and tests every reply inline; it never uses
            the handler-named aliases of the IRS convention.
        file_access: `01 File-Access.` [copybooks/wsfnctn.cob:L22]. Shared with
            the OTM4 sequence, because `seloi4.cob:L4` declares `status
            fs-reply`.
        acas_dal_common_data: `01 ACAS-DAL-Common-data.`
            [copybooks/Test-Data-Flags.cob:L6].
        ws_value_record: `01 WS-Value-Record.` [copybooks/wsval.cob:L9].
        ws_analysis_record: `01 WS-Analysis-Record.` [copybooks/wsanal.cob:L9].
        ws_pinvoice_record: `01 WS-PInvoice-Record.`
            [copybooks/plwspinv2.cob:L10].
        invoice_header: `01 Invoice-Header redefines WS-PInvoice-Record.`
            [copybooks/plwspinv2.cob:L21].
        invoice_line: `01 Invoice-Line redefines WS-PInvoice-Record.`
            [copybooks/plwspinv2.cob:L56].
        open_item_file_4: The OTM4 extract sequence that `pl060` consumes. A
            caller sequencing the two programs passes one instance to both.

    Raises:
        _CobolFilesModeUnsupportedError: If `FS-Cobol-Files-Used`
            [copybooks/wssystem.cob:L113] is true. Unreachable in the RDBMS
            configuration the migration targets.
        WorkFileError: If the OTM4 sequence is written while not open for
            output, which the `mainline` open sequence prevents.
    """
    if facade is None:
        # The Agent Action Plan's own import form, section 0.4.3. Resolved here
        # rather than at module scope because the module is generated later in
        # this same batch.
        from acas_posting.dal import facade as imported_facade

        resolved_facade = _BoundFacade(imported_facade)
    else:
        resolved_facade = facade

    resolved_file_access = FileAccess() if file_access is None else file_access
    header = (
        _initial_pinvoice_view(IhInvoiceHeader)
        if invoice_header is None
        else invoice_header
    )

    ctx = _FacadeContext(
        system_record=system_record,
        ws_value_record=WsValueRecord() if ws_value_record is None else ws_value_record,
        ws_analysis_record=(
            WsAnalysisRecord() if ws_analysis_record is None else ws_analysis_record
        ),
        ws_pinvoice_record=(
            _initial_pinvoice_view(WsPInvoiceRecord)
            if ws_pinvoice_record is None
            else ws_pinvoice_record
        ),
        invoice_header=header,
        invoice_line=(
            _initial_pinvoice_view(IlInvoiceLine)
            if invoice_line is None
            else invoice_line
        ),
        file_access=resolved_file_access,
        file_defs=file_defs,
        acas_dal_common_data=(
            AcasDalCommonData()
            if acas_dal_common_data is None
            else acas_dal_common_data
        ),
    )

    st = _Pl055State(
        ctx=ctx,
        facade=resolved_facade,
        open_item_file_4=(
            _OpenItemFile4(file_access=resolved_file_access)
            if open_item_file_4 is None
            else open_item_file_4
        ),
        ws_calling_data=ws_calling_data,
        system_record_4=system_record_4,
        to_day=to_day,
        ws_date_formats=WsDateFormats(),
    )

    # `mainline section.` [purchase/pl055.cbl:L246] and everything it falls
    # through into. The program has no other entry.
    _mainline(st)


# =============================================================================
# --- traceability ---
#
# Rule R-5 requires that every program map to a module, every paragraph to a
# function and every field to a data-dictionary entry, AND that the mapping be
# recorded rather than left implicit in the code. This footer is that record for
# `purchase/pl055.cbl`. It is deliberately exhaustive: the migration's only
# specification is a program nobody has re-tested since the compiler migration,
# so a reader who wants to know whether something was carried across must be
# able to find the answer here rather than by re-reading 635 lines of COBOL.
#
# PROGRAM -> MODULE
#   purchase/pl055.cbl  ->  acas_posting/programs/pl055_order_proof_extract.py
#   Boundary: THE WHOLE PROGRAM. Unlike `gl051` and `irs030`, which are migrated
#   in part, every section of `pl055` is in scope.
#
# -----------------------------------------------------------------------------
# 1.  SECTION AND PARAGRAPH -> FUNCTION
#
# Sixteen labels were measured in the procedure division. Agent Action Plan
# section 0.4.2 lists only the five section heads for this program and omits
# every paragraph, so the ten paragraphs plus `a01-Eval-Status` are a measured
# addition. Each label has its own function; the three `main-exit` labels are
# SECTION-QUALIFIED because paragraph names are not unique in this codebase.
#
#   COBOL label                    Line   Section            Python function
#   ---------------------------- ------ ------------------ ---------------------
#   mainline section.               246  mainline           _mainline
#   read-loop.                      306  mainline           _read_loop
#   header-analysis.                362  mainline           _header_analysis
#   close-files.                    400  mainline           _close_files
#   menu-exit.                      434  mainline           _menu_exit
#   create section.                 441  create             _create
#   Create-Main.                    444  create             _create__create_main
#   Create-Anal.                    488  create             _create__create_anal
#   main-exit.                      501  create             _create__main_exit
#   store-specials section.         503  store-specials     _store_specials
#   main-exit.                      536  store-specials     _store_specials__main_exit
#   extract section.                538  extract            _extract
#   main-exit.                      597  extract            _extract__main_exit
#   zz070-Convert-Date section.     599  zz070-Convert-Date _zz070_convert_date
#   zz070-Exit.                     626  zz070-Convert-Date _zz070_exit
#   a01-Eval-Status section.        629  a01-Eval-Status    _a01_eval_status
#
#   `create section.` [L441] and `Create-Main.` [L444] are two labels three
#   lines apart, and both are named by real transfers: `perform create` at
#   [L324] and [L511] names the SECTION, while the backward `go to create-Main`
#   at [L499] names the PARAGRAPH. They therefore get two functions, the first
#   of which carries no statements because the COBOL section head carries none.
#
#   Helper functions carry no COBOL label of their own. They exist because one
#   COBOL statement can need several Python ones - a two-receiver `MOVE`, a
#   group move into a nested dataclass, a byte image of a group item - and each
#   names in its docstring the statement it serves:
#     _by_name  _ws  _copy_oi_header  _initialise_oi_header
#     _initial_pinvoice_view  _pinvoice_attributes  _move_into_va_group
#     _add_to_pair  _subtract_from_pair  _store_group  _caller_is_xl150
#     _va_code_image  _pa_code_image  _move_into_va_code  _move_into_pa_code
#     _group_move_analysis_into_value  _analysis_tail_image
#     _zero_the_six_value_totals  _ih_supplier_image  _move_into_oi_supplier
#     _set_oi_net  _fs_reply_message
#   Types: _CobolFilesModeUnsupportedError  _OpenItemFile4  _FacadeContext
#          _Pl055State.
#   Public API: `run` alone. `__all__ = ("run",)`, and every other module-level
#   name begins with an underscore, so a caller cannot reach into the program's
#   internals - exactly as a COBOL `CALL` cannot.
#
# -----------------------------------------------------------------------------
# 2.  `GO TO` CENSUS - NINETEEN SITES, CLASSIFIED BY SHAPE
#
# Classified by shape rather than by matching the Agent Action Plan's label
# list, which is not exhaustive for this program.
#
#   Class 1 - loop-back -> `continue` (7 sites)
#     L315  if il-analyised            go to read-loop     -> continue
#     L341  if va-second = space       go to read-loop     -> continue
#     L347  if FS-Reply = 21           go to read-loop     -> continue
#     L360  (unconditional, last stmt) go to read-loop     -> continue
#     L366  if ih-analyised and applied go to read-loop    -> return to caller
#     L372  after PInvoice-Rewrite     go to read-loop     -> return to caller
#     L398  (unconditional, last stmt) go to read-loop     -> return to caller
#     The last three are inside `header-analysis`, which the loop calls; a
#     `return` there lands on the `continue` at the class-4 site below, so the
#     effect is the same loop-back.
#
#   Class 2 - forward terminator -> `break` PLUS the post-loop block (1 site)
#     L309  if FS-Reply not = zero     go to close-files   -> break
#     Agent Action Plan section 0.6.3, verbatim: *"the target label is followed
#     by real work - closing files, printing totals, rewriting a control record
#     - so the transformation is `break` PLUS faithful placement of that work
#     after the loop, not `break` alone. Mis-splitting here would silently drop
#     end-of-run processing."* Here that work is the FOUR special-total stores
#     and the FOUR closes at [L403-L423]; dropping it would lose the entire
#     purchase value-analysis roll-up. And because [L308] leaves on ANY non-zero
#     status rather than only at end of file, this break is reached in more
#     circumstances than its sales counterpart - see divergence 4.
#
#   Class 3 - section or paragraph exit -> `return` (8 sites)
#     L457  if va-second = space       go to main-exit  [L501]
#     L468  after restoring WS-Pa-Code go to main-exit  [L501]
#     L480  if FS-Reply = 21           go to main-exit  [L501]
#     L486  (unconditional, last stmt) go to main-exit  [L501]
#     L528  if FS-Reply = 21           go to main-exit  [L536]
#     L545  if applied                 go to main-exit  [L597]
#     L612  if Date-UK                 go to zz070-Exit [L626]
#     L617  if Date-USA, after swap    go to zz070-Exit [L626]
#     The last two live in `dates.zz070_convert_date`, because that section is
#     textually identical in all ten carriers; they are annotated at the call
#     site so this census is complete for `pl055`.
#
#   Class 4 - sibling re-dispatch -> named call plus an explicit transfer
#             (3 sites, each with its own equivalence proof)
#     L312  if ih-test = zero  go to header-analysis  [L362]
#           PROOF: every path through `header-analysis` ends in `go to
#           read-loop` - at [L366], at [L372] and at [L398], the paragraph's
#           last statement - so the paragraph has no fall-through and no other
#           exit. A call followed by an unconditional `continue` visits the same
#           statements in the same order. Note the sales program reaches its
#           header block by `exit perform` and FALL-THROUGH
#           [sales/sl055.cbl:L371, L426]; this one names the target.
#     L450  if FS-Reply = 21 or = 23  go to Create-Anal  [L488]
#           PROOF: `Create-Anal` has exactly one exit, the unconditional `go to
#           create-Main` at its last line [L499], and contains no other
#           transfer. So the transfer pair is a retry loop and nothing else.
#     L499  (unconditional, last stmt) go to create-Main  [L444]
#           A BACKWARD transfer to the section's FIRST paragraph - the only
#           genuine cross-paragraph retry in the program. PROOF: combined with
#           the L450 proof above, the pair is exactly `while True:` around
#           `Create-Main`'s statements with a call to `Create-Anal` followed by
#           `continue`. Termination is NOT guaranteed by the COBOL and no guard
#           is added - see AMBIGUITY Q-PL055-2.
#
#   Plain `EXIT`, not `EXIT SECTION` (1 site, not a `GO TO`)
#     L597  main-exit.   exit.        -> `_extract__main_exit`
#     `EXIT` on its own is a no-op that documents an exit point; `create` [L501]
#     and `store-specials` [L536] both write `exit section.` instead. Divergence
#     18, preserved.
#
#   `PERFORM ... THRU` DOES NOT OCCUR IN `pl055`. The four in-scope sites
#   repository-wide are [general/gl072.cbl:L300], [general/gl072.cbl:L304],
#   [sales/sl100.cbl:L344] and [purchase/pl100.cbl:L336].
#
# -----------------------------------------------------------------------------
# 3.  FALL-THROUGH
#
#   `mainline` [L246-L304] has no terminating `exit section.`, so control
#   arrives at `read-loop.` [L306] by falling through. Represented by the call
#   to `_read_loop` at the end of `_mainline`.
#
#   `close-files` [L400-L432] falls through into `menu-exit.` [L434] whenever
#   `Anal-Created` is zero - the conditional `goback` at [L432] is taken only
#   when an emergency analysis record was written. Represented by the call to
#   `_menu_exit` after the conditional return in `_close_files`.
#
#   `create section.` [L441] falls through into `Create-Main.` [L444], the
#   section head carrying no statements. Represented by `_create` calling
#   `_create__create_main`.

#
# -----------------------------------------------------------------------------
# 4.  DIVERGENCES FROM `sales/sl055.cbl` - EIGHTEEN, ALL PRESERVED
#
# ⛔⛔ `pl055` IS NOT A MIRROR OF `sl055`. The Agent Action Plan describes it as
# the "Purchase mirror of `sl055`"; measured against the two sources that is
# WRONG. The two programs diverge in eighteen places, at least eight of them
# behaviourally significant and directly visible in a table dump. This module
# was transcribed from `purchase/pl055.cbl` alone. `sl055` is cited below and in
# the comments ONLY as the contrast that makes each divergence visible - there
# is no import of and no call into `sl055_invoice_extract_analysis`, which would
# be both a layering violation and the single most likely way to destroy these
# eighteen facts.
#
#   #   Subject                     sl055                     pl055
#  --- --------------------------- ------------------------- --------------------
#   1   negation-block width        NINE fields               ⭐ FOUR fields
#       [sales/sl055.cbl:L658-L666] vs [purchase/pl055.cbl:L571-L575]
#       `oi-net`, `oi-carriage`, `oi-vat`, `oi-c-vat` only. `oi-deduct-amt` IS
#       moved at [purchase/pl055.cbl:L564] and is NOT negated, where the sales
#       program negates it first [sales/sl055.cbl:L658]. Diff-visible in every
#       credit-note row of the OTM4 sequence that `pl060` then consumes.
#
#   2   invoice-total addends       NINE addends              ⭐ FOUR addends
#       [sales/sl055.cbl:L671-L673] vs [purchase/pl055.cbl:L580]
#       `ih-net ih-carriage ih-vat ih-c-vat` giving `ws-inv-amt`. Diff-visible
#       in `SYSTOT-REC` through the two period totals.
#
#   3   main-loop control structure inline PERFORM UNTIL      ⭐ a `GO TO` loop
#       [sales/sl055.cbl:L365-L424] vs [purchase/pl055.cbl:L306-L360]
#       The maintainer modernised the sales extract - its own note reads
#       *"changed 18/01/25 for clean up using inline perform"* - and never came
#       back to this one. Structural, not behavioural, but it is why the class-1
#       and class-2 census above has seven and one entries here and none there.
#
#   4   loop-exit condition         `if fs-reply = 10`        ⭐⭐ `not = zero`
#       [sales/sl055.cbl:L367] vs [purchase/pl055.cbl:L308]
#       BEHAVIOURAL. The sales program leaves the walk only at end of file;
#       `pl055` leaves it on ANY non-zero status. In a scenario where a read
#       fails mid-walk the two programs write different amounts of data.
#
#   5   `INITIALIZE`                `with filler`             ⭐⭐ no `with filler`
#       [sales/sl055.cbl:L635] vs [purchase/pl055.cbl:L547]
#       BEHAVIOURAL, and a British spelling into the bargain - `initialise`.
#       Without `WITH FILLER`, `FILLER` items are not reset and retain their
#       previous contents, which is directly visible in the written record. See
#       AMBIGUITY Q-PL055-1 and the note in `_initialise_oi_header`.
#
#   6   case of a STORED flag       upper `"Z"`               ⭐⭐ lower `"z"`
#       [sales/sl055.cbl:L421, L468] vs [purchase/pl055.cbl:L358, L396]
#       BEHAVIOURAL AND DIFF-VISIBLE: `il-update` in `PUINV-LINES-REC` and
#       `ih-update` in `PUINVOICE-REC` are stored columns, and the case differs.
#       The sales program even documents its own change - *"Analysied flag
#       changed from z (1/6/13)"* - and `pl055` was left behind. The `88`-level
#       [copybooks/plwspinv2.cob:L53, L72] accepts both cases, which is why the
#       program still recognises its own flag and the defect stays invisible at
#       run time.
#
#   7   skip-invoice path           a whole apparatus         ⭐⭐ NONE OF IT
#       [sales/sl055.cbl:L430, L433-L434, L472-L479] vs nothing in `pl055`
#       BEHAVIOURAL. No `da030-Skip-Invoice` paragraph, no `Invoice-Start`, no
#       `set fn-not-less-than`, no proforma filter, no pending/status filter and
#       no `ws-p-flag`. `header-analysis` [L362] goes straight from [L365-L366]
#       to `perform extract` [L368], so a purchase proforma IS extracted and IS
#       counted. See the note at the top of `_header_analysis`.
#
#   8   header-analysis sign flips  THREE                     ⭐ TWO
#       [sales/sl055.cbl:L446, L457, L463] vs [purchase/pl055.cbl:L376, L387]
#       BEHAVIOURAL for the discount total: the discount block
#       [purchase/pl055.cbl:L391-L394] has no `if ih-type = 3 multiply -1`.
#       Mechanically consistent with `03 ih-deduct-amt pic 999v99 comp.`
#       [copybooks/plwspinv2.cob:L46] being UNSIGNED, which cannot hold a
#       negative in the first place - recorded as evidence, not as a licence.
#
#   9   VAT total addends           THREE                     ⭐ TWO
#       [sales/sl055.cbl:L444] vs [purchase/pl055.cbl:L374]
#       BEHAVIOURAL. `ih-e-vat` [copybooks/plwspinv2.cob:L38] exists in the
#       purchase header and is simply not summed.
#
#  10   paragraph naming            `da`/`db`/`dc`/`dd`       ⭐ UNPREFIXED
#       [sales/sl055.cbl:L305, L364] vs [purchase/pl055.cbl:L306, L362, ...]
#       Structural. The Python functions carry the COBOL's own unprefixed names,
#       section-qualified only where a name is not unique.
#
#  11   the Value-file open         an existence probe        ⭐ just an open
#       [sales/sl055.cbl:L319-L324] vs [purchase/pl055.cbl:L261]
#       BEHAVIOURAL on a missing file: the sales program probes with
#       `Value-Open-Input`, conditionally closes and re-opens for output, then
#       unconditionally closes; `pl055` performs `Value-Open` with NO reply test
#       and does it a SECOND time at [purchase/pl055.cbl:L299]. A failed open is
#       therefore not noticed until the first read.
#
#  12   `ih-status-A`               set as well               ⭐ NOT set
#       [sales/sl055.cbl:L679-L680] vs [purchase/pl055.cbl:L586]
#       BEHAVIOURAL AND DIFF-VISIBLE: only `ih-status` is stamped. Corroborated
#       from the copybook side - `ih-status-A` DOES NOT EXIST in
#       `copybooks/plwspinv2.cob` at all, so there is no field to set. Note the
#       program's own internal inconsistency: `ih-status` takes UPPER-case `"Z"`
#       here while `ih-update` and `il-update` take LOWER-case `"z"` at [L396]
#       and [L358], and the maintainer's own comment at [L586] reads
#       *"07/01/18 was "z""*.
#
#  13   the write target            `oi-header` (WS)          ⭐ `open-item-record-4`
#       [sales/sl055.cbl:L681] vs [purchase/pl055.cbl:L587]
#       COSMETIC IN `pl055`, and the resolution is structural - see STRUCTURAL
#       NOTES below and AMBIGUITY Q-PL055-5.
#
#  14   `a01-Eval-Status` exit      `a01-exit.`               ⭐ NO exit paragraph
#       [sales/sl055.cbl:L729] vs [purchase/pl055.cbl:L629-L632]
#       Structural. The section ends at the `copy` and the following `copy
#       "Proc-ACAS-FH-Calls.cob"` [L634] terminates it.
#
#  15   accumulation verb count     four single-receiver      ⭐ two two-receiver
#       [sales/sl055.cbl:L391-L395] vs [purchase/pl055.cbl:L330, L332]
#       `add il-net to va-v-this va-v-year` and `subtract il-net from va-v-this
#       va-v-year`. Each receiver converts INDEPENDENTLY under its own
#       description, which is why `_add_to_pair` and `_subtract_from_pair` call
#       the primitive twice rather than computing once and assigning twice.
#
#  16   `il-product (1:1) = "/"`    present                   ⭐ absent
#       [sales/sl055.cbl:L376] vs nothing in `pl055`
#       BEHAVIOURAL. A purchase line whose product code opens with a comment
#       marker IS analysed and DOES contribute to `VALUEANAL-REC`.
#
#  17   value-analysis groups       `vo` `vp` `zc` `zd`       ⭐ `vi` `vj` `za` `zb`
#       [sales/sl055.cbl] vs [purchase/pl055.cbl:L404, L408, L412, L416]
#       and `va-system` set EXPLICITLY by `move "P" to va-system` at
#       [purchase/pl055.cbl:L403], where the sales program sets it implicitly by
#       moving a three-character literal such as `"Svo"` into `va-code`.
#       `pl060`'s deduction analysis later targets the `"zb"` group, the
#       purchase analogue of `sl060`'s `"Szd"`.
#
#  18   `extract` terminator        `exit section.`           ⭐ plain `exit.`
#       [sales/sl055.cbl] vs [purchase/pl055.cbl:L597]
#       Cosmetic, and inconsistent within `pl055` itself: `create` [L501] and
#       `store-specials` [L536] both write `exit section.`
#
# FURTHER DIVERGENCES AND INCONSISTENCIES RECORDED IN THE CODE, not numbered
# above because they are internal to `pl055` rather than contrasts with `sl055`:
#   * `= 21` alone at [L323], [L346], [L510] and [L527] against `= 21 or = 23`
#     at [L449] - the only site testing both. The data-access layer records that
#     `FS-Reply` 23 is documented but never actually returned, so the `or = 23`
#     arm is dead in practice; ⛔ it is not removed for that.
#   * The unguarded backward retry at [L499] - AMBIGUITY Q-PL055-2.
#   * `Create-Main.` declared mixed-case at [L444] and spelled `create-Main` at
#     the `GO TO` [L499]. COBOL is case-insensitive; `sl055` has the identical
#     quirk [sales/sl055.cbl:L530, L585].
#   * `end-if.` at [L338] - a period AFTER `end-if`, closing a construct whose
#     `if` at [L334] already ends at [L337]'s period. Harmless.
#   * The extra `move 1 to File-Key-No` at [L355], between the accumulation and
#     the `Value-Rewrite`, which the first accumulation block does not have at
#     the equivalent point.
#   * `call "sl070"` at [L273] - the SALES program called from a PURCHASE
#     module, not `pl070`. `sl070` creates the shared Analysis and Value files,
#     so it is probably deliberate; `sl055` makes the identical call
#     [sales/sl055.cbl:L332]. ⛔ Not "corrected" to `pl070`.
#   * The `va-code` left blanked by the [L467-L468] exit of `Create-Main` - a
#     latent defect recorded at that site, reproduced per R-4.
#   * Missing terminating periods at [L470] and [L482] where [L452] has one.
#   * [L547] carries one extra leading space relative to its neighbours.
#   * `01 ws-Test-Date pic x(10).` [L181], `01 error-code pic 999.` [L227] and
#     `03 ws-Conv-Date pic x(10).` [L184] are declared and NEVER referenced.
#
# SHARED LEGACY DEFECTS - PRESENT IDENTICALLY IN `sl055`, SO NOT DIVERGENCES.
# Both were found by RUNNING this module and tracing its verb order, then
# confirmed against the sales source line by line. Both are reproduced per R-4
# and both are locked in place by the ad-hoc walk, so that a later "tidy-up"
# fails rather than passing unnoticed.
#
#   FINDING A - THE ROLL-UP `Value-Write` AT [L474] IS UNCONDITIONAL AND
#   UNTESTED, SO IT ISSUES A DUPLICATE INSERT ON ESSENTIALLY EVERY RUN AND
#   SWALLOWS THE FAILURE.
#     `Create-Main` blanks the second character of the key [L461], group-moves
#     the analysis record over the value record [L470], zeroes all six totals
#     [L471-L472] and then writes UNCONDITIONALLY [L474] - with no `v-exists`
#     test, unlike the two structurally identical sites at [L334-L337] and
#     [L519-L522] - and never inspects the reply. When the roll-up row does not
#     yet exist this is the intended materialisation. When it does, the handler
#     `ba070_process_write` in `acas_posting.dal.acas013_value` issues
#     `INSERT INTO `VALUEANAL-REC` SET ...`, hits the duplicate key, sets
#     `FS-Reply` 22 and LEAVES THE STORED ROW UNTOUCHED - reproducing
#     [common/valueMT.cbl:L817-L831]. ⛔ The accumulated totals are therefore NOT
#     lost; this is not a lost update. The two real effects are a duplicate
#     INSERT - guaranteed by `close-files` [L403-L419], where `vi`/`vj` share the
#     roll-up `Pv ` and `za`/`zb` share `Pz ` - and a stale `FS-Reply` 22 on
#     return, inert only because the next read at [L345] or [L526] assigns over
#     it. Measured for one type-3 header against an empty table: duplicate writes
#     for `Pv ` and `Pz `, with `Pv ` holding (1, -11.00) and `Pz ` (2, -1.00).
#     `sl055` writes unconditionally at the same point,
#     `perform Value-Write.` [sales/sl055.cbl:L560], after the same blank-key
#     [sales/sl055.cbl:L547] and zeroing sequence, restoring `va-code` only
#     afterwards [sales/sl055.cbl:L562]. Recorded at its site in
#     `_create__create_main`. DO NOT FIX - guarding the write would remove a
#     statement the COBOL issues against the database, and testing the reply
#     would add a control transfer the COBOL does not have (R-3).
#
#   FINDING B - A SINGLE-CHARACTER ANALYSIS GROUP IS ACCUMULATED BUT NEVER
#   STAMPED, SO IT IS RE-ANALYSED AND DOUBLE-COUNTED ON EVERY LATER RUN.
#     `if va-second = space go to read-loop.` [L340-L341] correctly skips the
#     inapplicable second half of the twice-over accumulation, but because it
#     targets `read-loop` rather than the loop tail it ALSO skips
#     `move "z" to il-update` [L358] and `perform PInvoice-Rewrite` [L359]. The
#     line has already been committed into `VALUEANAL-REC` by [L327-L337], yet
#     `il-analyised` [copybooks/plwspinv2.cob:L69] still reads FALSE, so the
#     next run accumulates the same line again. Measured: for `il-pa = "v "` the
#     value rows are written and rewritten and `PInvoice-Rewrite` is never called
#     at all. `sl055` has the identical ordering -
#     `if va-second = space exit perform cycle` [sales/sl055.cbl:L402-L404]
#     before `move "Z" to il-update` [sales/sl055.cbl:L421] and
#     `perform Invoice-Rewrite` [sales/sl055.cbl:L422]. Only the STAMPED case
#     differs between the programs, and that is DIVERGENCE 6. Recorded at its
#     site in `_read_loop`. DO NOT FIX - issuing the stamp would set a stored
#     `PUINV-LINES-REC` column the COBOL leaves blank.
#
# THE TWICE-OVER BLOCKS ARE NOT FACTORED, DELIBERATELY. [L327-L337] against
# [L349-L356], and [L514-L522] against [L530-L534], each look like one helper
# called twice and are not: the first of each pair branches on `v-exists` to
# choose `Write` or `Rewrite` and the second always `Rewrite`s, and the first
# pair's second half carries the extra [L355]. Agent Action Plan section 0.6.1,
# verbatim: *"Normalising them into one helper would be the single easiest way
# to fail this migration."*

#
# -----------------------------------------------------------------------------
# 5.  STRUCTURAL NOTES
#
# 5.1  THE OTM4 WORK FILE, AND WHY IT IS DECLARED HERE
#
#   `open-item-file-4` is the purchase temp extract: `copy "seloi4.cob"` [L109]
#   carries its author's own note *"Temp file only for i/p to pl060"*, `copy
#   "fdoi4.cob"` [L120] gives it `01 open-item-record-4 pic x(113)`, and
#   `file-28` is `"openitm4.dat"` [copybooks/file28.cob:L1]. It reaches NO
#   schema table and appears in NO table dump; `pl060` consumes it
#   [purchase/pl060.cbl:L421-L425].
#
#   It is modelled the way the Agent Action Plan models the General Ledger work
#   files - an ordered in-process sequence with the same record layout and the
#   same ordering guarantee - by the module-private `_OpenItemFile4`:
#     `open extend`  [L301]  -> positions at the end, existing records survive
#     `open output`  [L304]  -> truncates, which is what makes the fallback a
#                               create
#     `write`        [L587]  -> appends, in insertion order, a SNAPSHOT
#     `close`        [L423]  -> a no-op on the records; they are the deliverable
#
#   WHY MODULE-PRIVATE RATHER THAN `workfiles.LineSequentialWorkFile`. That
#   published class has no `open_extend`; its `OpenMode` vocabulary is exactly
#   `CLOSED`/`INPUT`/`OUTPUT`, and its only route into a writable state is
#   `open_output`, which truncates. Its record list, open mode, read pointer and
#   status field are all private. Adding an extend by reaching into them would
#   be a layering violation dressed up as reuse, and `acas_posting/workfiles.py`
#   publishes only `pre_trans`, `post_trans` and `sort_trans` - none of which is
#   this file. The published `FS_REPLY_OK`, `OpenMode` and `WorkFileError` ARE
#   reused, so no parallel status vocabulary is invented beside them.
#
#   AND NO NEW FILE WAS CREATED. `acas_posting/programs/` is closed at exactly
#   thirteen files - `__init__.py` plus the twelve program modules - per Agent
#   Action Plan sections 0.4.1.2 and 0.4.4.
#
#   The status field is shared with the data-access layer DELIBERATELY:
#   `seloi4.cob:L4` declares `status fs-reply`, and `Fs-Reply`
#   [copybooks/wsfnctn.cob:L25] is the very field every facade verb also writes.
#   That sharing is what lets [L302] and [L588] test `fs-reply` straight after a
#   native `OPEN` and `WRITE`.
#
# 5.2  `OI-Header` AGAINST `open-item-record-4` - DIVERGENCE 13, RESOLVED
#
#   [L547] initialises `OI-Header` and [L587] writes `open-item-record-4`, which
#   reads at first glance as a write of an area nothing filled. It is not. In
#   `pl055` BOTH `copy "fdoi4.cob"` [L120] and `copy "plwsoi.cob"` [L121] sit
#   inside the FILE SECTION under one FD, so `01 open-item-record-4 pic x(113)`
#   and `01 OI-Header` are two `01` DESCRIPTIONS OF THE SAME 113-BYTE RECORD
#   AREA - a second `01` under an FD is an alternative description, not a second
#   buffer - and `OI-Header`'s fields sum to exactly 113. The divergence is
#   therefore COSMETIC here, and `_OpenItemFile4` models the one area.
#
#   `pl060` proves the contrast: it copies `plwsoi.cob` into WORKING-STORAGE
#   [purchase/pl060.cbl:L152] and consequently needs an explicit `move
#   open-item-record-4 to oi-header` [purchase/pl060.cbl:L428] that `pl055` has
#   no counterpart to. What remains for the oracle is recorded as AMBIGUITY
#   Q-PL055-5.
#
# 5.3  THE `OI-Header` LAYOUT IS PUBLISHED, NOT DECLARED HERE
#
#   `copybooks/plwsoi.cob` has no `records/` module of its own in Agent Action
#   Plan section 0.3.1's list, which suggested a module-private declaration would
#   be needed. It is not: `acas_posting/records/otm5.py` already publishes
#   `OiHeader` with its subordinate groups `OiKey`, `OiBatch`, `OiCustomer`,
#   `OiSupplier` and `Filler1`, and `otm5.descriptors_of()` supplies a descriptor
#   for every field WITH a dictionary key. So every field of the record this
#   module writes is traceable to a dictionary entry, and no layout was invented.
#   (`field.descriptors_for_copybook_record("OI-Header")` is NOT used: it is
#   ambiguous, returning 69 descriptors that mix the purchase `PUITM5-REC` and
#   the sales `SAITM3-REC` views of the same copybook name.)
#
# 5.4  `WITH FILLER` HAS NO ELEMENTARY TARGET IN THIS COPYBOOK
#
#   `copybooks/plwsoi.cob` contains exactly one `FILLER`, the GROUP item at
#   [copybooks/plwsoi.cob:L41] whose ten subordinates are ALL named. So the
#   omitted `WITH FILLER` at [L547] cannot be observed by watching a named field
#   - it can only be observed in bytes the group description does not name, and
#   whether any such bytes exist is the oracle question Q-PL055-1.
#   `_initialise_oi_header` therefore initialises the seventeen top-level fields
#   under their own descriptors and NOTHING ELSE, which is the closest faithful
#   reading of `initialise` without `WITH FILLER`.
#
# 5.5  FIELD DESCRIPTORS AND THEIR PROVENANCE
#
#   Every descriptor this module uses is either looked up from the generated
#   dictionary - `_VAL`, `_ANL`, `_S4`, the five `_OI*` dicts, and
#   `pinvoice_descriptor_for` - and therefore carries a `dictionary_key`, or is
#   built by `_ws()` from the program's OWN working storage and therefore carries
#   a `source_locator` of the form `purchase/pl055.cbl:L<n>`. FOURTEEN `_D_*`
#   descriptors are the second kind: `Anal-Created` [L163], `save-code` [L164],
#   `ws-inv-amt` [L165], `work-2` [L166], `work-3` [L167], the four money totals
#   [L168-L171], the four counts [L172-L175] and `v-exists` [L176]. A fifteenth
#   `_ws()` descriptor, `Exception-Msg` [L126], is built inline in
#   `_a01_eval_status` rather than at module scope because nothing else needs it.
#   `_D_TERM_CODE` is the FIRST kind - it comes from
#   `calling_data_descriptor_for("ws_term_code")`, so its provenance is the
#   dictionary entry for `WS-Term-Code` [copybooks/wscall.cob:L10] rather than a
#   locator written here.
#
#   VERIFIED BY INTROSPECTION, not by reading: 97 `FieldDescriptor` objects are
#   reachable from this module's namespace; 83 carry a `dictionary_key`, 14 carry
#   a `source_locator` matching `^[A-Za-z0-9_./-]+:L[0-9]+(-L[0-9]+)?$`, and NONE
#   carries neither. No descriptor is constructed without one or the other.
#
# 5.6  THE FACADE IS INJECTED, NOT IMPORTED AT MODULE SCOPE
#
#   `pl055` copies `Proc-ACAS-FH-Calls.cob` [L634], so it uses the ENTITY-named
#   verb vocabulary and TESTS THE REPLY INLINE - that copybook has no
#   per-handler error-check paragraph at all, unlike the IRS convention. The
#   thirteen distinct verbs this module calls are `PInvoice-Open` [L298],
#   `PInvoice-Read-Next` [L307], `PInvoice-Rewrite` [L359, L371, L397],
#   `PInvoice-Close` [L420], `Value-Open` [L261, L299], `Value-Read-Indexed`
#   [L322, L345, L509, L526], `Value-Write` [L335, L474, L520], `Value-Rewrite`
#   [L337, L356, L522, L534], `Value-Close` [L421], `Analysis-Open` [L300],
#   `Analysis-Read-Indexed` [L448, L465, L478], `Analysis-Write` [L494, L497]
#   and `Analysis-Close` [L422]. ⛔ No handler-named alias
#   (`acas013_*`/`acas015_*`/`acas026_*`) is called.
#
#   `acas_posting/dal/facade.py` is generated in this same batch and does not
#   exist while this module is written, so it is resolved lazily inside `run`
#   and can be substituted by a caller. See AMBIGUITY Q-PL055-7 and Q-PL055-8.
#
#   ALL TEN `move 1 to File-Key-No` STATEMENTS ARE PRESERVED IN PLACE - [L291],
#   [L321], [L344], [L355], [L447], [L464], [L477], [L493], [L508] and [L525] -
#   and so are BOTH `Value-Open` calls, neither with a reply test. They look
#   cacheable and are not cached: Agent Action Plan section 0.8.4, verbatim,
#   *"Any performance work is therefore out of scope by construction, not merely
#   unrequested."*
#
# -----------------------------------------------------------------------------
# 6.  CITATION CORRECTIONS - FOUR MEASURED FACTS THAT OVERTURN THE PLAN
#
# Recorded because a downstream reader working from the Agent Action Plan alone
# would otherwise be misled. Each was measured against the frozen source.
#
# 6.1  `pl055` DOES HAVE A FACADE STUB BLOCK.
#   The plan states this program has "NO facade stub block (unlike gl072
#   L135-L155 and gl080 L194-L214)". It does: `01
#   Dummies-4-Unused-ACAS-FH-Calls.` at [purchase/pl055.cbl:L139-L159], carrying
#   the comment *"Call blk at zz080-ACAS-Calls"*. What makes it look absent is
#   that FOUR of its members are COMMENTED OUT - `System-Record-4` [L142],
#   `WS-Value-Record` [L150], `WS-Analysis-Record` [L152] and
#   `WS-PInvoice-Record` [L158] - precisely because those four are real records
#   in this program rather than stubs. Like `gl072`'s block it maps to NOTHING
#   in Python, which has no linker to satisfy; recorded here as a
#   representation-only omission so that a reader diffing the two files does not
#   conclude something was lost.
#
# 6.2  THE `extract` SECTION COMMENT PROMISES A FILTER THAT DOES NOT EXIST.
#   [purchase/pl055.cbl:L541-L542] reads *"only Process header records, drop
#   pro-formas"* and *"ignore records which have already been copied"*. Only the
#   second is implemented, by `if applied` [L544]. There is NO `ih-type = 4`
#   proforma test anywhere in `pl055` - see divergence 7. The comment is the
#   maintainer's intent; the code is the specification.
#
# 6.3  ⛔ THE PURCHASE TERM-CODE GATE EXISTS, AND THE PLAN'S CONCLUSION IS WRONG.
#   The plan observes correctly that `load08.` [purchase/purchase.cbl:L752-L762]
#   has NO inline gate - its would-be gate lines are commented out at
#   [purchase/purchase.cbl:L755-L758] - and concludes that `move 8 to
#   WS-Term-Code` [purchase/pl055.cbl:L286] "has no gating effect on `pl060`".
#   MEASURED, IT DOES. The shared dispatch paragraph `load000.`
#   [purchase/purchase.cbl:L691] gates for every loader:
#       if       ws-term-code < 8   perform overrewrite.   [L702-L703]
#       if       ws-term-code > 7   go to overrewrite.     [L704-L705]
#   With term code 8, [L702] is false and [L704] is TRUE, so `go to overrewrite`
#   transfers OUT of the `perform load000.` range at
#   [purchase/purchase.cbl:L760]. A `GO TO` escaping a `PERFORM` range never
#   returns, so control reaches `overrewrite.` [purchase/purchase.cbl:L621],
#   falls through to `overclose.` [L652] and `goback.` [L653], and
#   `purchase.cbl` TERMINATES. `pl060` IS NEVER CALLED.
#   The three gate predicates must still NOT be unified - General tests `= 5`
#   [general/general.cbl:L810-L811], Sales `not = zero`
#   [sales/sales.cbl:L759-L768] and Purchase `> 7`
#   [purchase/purchase.cbl:L704].
#   SECOND-ORDER CONSEQUENCE, AND IT SHAPES THIS MODULE. `overrewrite.`
#   [purchase/purchase.cbl:L621-L651] is what PERSISTS the period totals: it
#   moves `WS-System-Record-4` into `System-Record` and rewrites under
#   `File-Key-No` 4, for both the RDB and the Cobol parameter file. So the two
#   period-total adds at [purchase/pl055.cbl:L582, L584] are written to
#   `SYSTOT-REC` BY THE MENU, not by `pl055`. This module therefore mutates
#   `system_record_4` in place and does NOT persist it - persisting it here
#   would double-write on the normal path and would write on the abort path,
#   where the COBOL does not.
#
# 6.4  `copybooks/wscall.cob`'s SEVEN-FIELD SPAN IS L6-L14, NOT L6-L13.
#   The plan cites [copybooks/wscall.cob:L6-L13]; measured, the seventh field
#   `WS-CD-Args pic x(13)` is at [copybooks/wscall.cob:L14]. The published
#   `records/calling_data.py` already records the correct span. Also note
#   [copybooks/wscall.cob:L4], *"14/11/25 vbc - 1.02 - Chg WS-Term-Code from 9
#   to 99"* - `WS-Term-Code` is `pic 99` [copybooks/wscall.cob:L10], which is
#   why the value 8 is stored through a descriptor rather than assigned raw.

#
# -----------------------------------------------------------------------------
# 7.  OMISSIONS - WHAT WAS DELIBERATELY NOT CARRIED ACROSS
#
# Agent Action Plan section 0.4.3 and rule R-5 require that deliberate omissions
# be recorded AS omissions, *"so that a reader comparing the two files does not
# conclude something was lost."* This is the complete list for `pl055`.
#
# 7.1  THE `if FS-Cobol-Files-Used` BLOCK BODY  [L266-L290]
#   The GATE is reproduced, data-driven through the condition name over `07
#   File-System-Used pic 9.` [copybooks/wssystem.cob:L112], so the decision is
#   made at run time exactly as the COBOL makes it. The BODY is not: it needs
#   `call "CBL_CHECK_FILE_EXIST"` [L267-L269, L278-L279] and `call "sl070"`
#   [L273-L277]. `sl070` is not one of the twelve in-scope programs - Agent
#   Action Plan section 0.2.2 - so there is no Python module to call, and rule
#   R-1 forbids invoking the COBOL. Inside the gate the module therefore RAISES
#   `_CobolFilesModeUnsupportedError`, an explicitly typed error whose message
#   states all four facts. ⛔ NOT silently skipped and NOT stubbed as a no-op: a
#   silent skip would make a genuinely divergent configuration look like a clean
#   run. The observable consequences of the COBOL's own abort path ARE preserved
#   - `move 8 to WS-Term-Code` [L286] happens BEFORE the raise, and the `goback`
#   [L287] is the raise itself. See AMBIGUITY Q-PL055-6.
#
# 7.2  ALL `display ... at` OUTPUT -> LOG RECORDS
#   [L281-L282] the two file-missing messages; [L293-L296] the program banner,
#   the "Invoice Post Extract" title and the converted date; [L426-L429] the
#   emergency-analysis warnings; [L590-L593] the OTM4 write-failure diagnostic.
#   Agent Action Plan section 0.3.4: they *"must not alter control flow and must
#   not appear in any table dump."* None of them does either.
#
# 7.3  `accept WS-Reply`  [L284], [L430], [L594]  -> DROPPED
#   Acknowledgement pauses whose only effect is to block a terminal. BUT the
#   `if WS-Caller not = "xl150"` branches around [L284] and [L430] ARE
#   PRESERVED - that test is the codebase's own unattended-mode check, and when
#   the out-of-scope `xl150` driver is the caller the COBOL skips the accept
#   itself. And both `goback`s ARE PRESERVED: [L287] and [L432].
#
# 7.4  TERMINAL GEOMETRY  [L249-L255]
#   `accept ws-env-lines from lines`, the companion `from columns`, and the
#   arithmetic `subtract 1 from ws-lines giving ws-23-lines`. A TERMINAL-SIZE
#   READ, NOT A CLOCK READ - it feeds only screen positioning, which is out of
#   scope. `ws-lines`, `ws-23-lines` and `ws-env-lines` are consequently not
#   modelled. Rule R-6 is unaffected: `purchase/pl055.cbl` contains ZERO clock
#   reads and the date arrives entirely through the `to-day` operand.
#
# 7.5  REPRESENTATION-ONLY DECLARATIONS
#   `set ENVIRONMENT` [L257-L258] and `copy "envdiv.cob"` [L102] - environment
#   configuration with no database effect. The facade stub block
#   [L139-L159] - see citation correction 6.1. `01 File-Info` [L205-L213] - eight
#   filesystem-metadata fields that only `CBL_CHECK_FILE_EXIST` populates and
#   that `pl055` never reads, testing `return-code` instead; NOT a clock read.
#   `01 ws-Test-Date pic x(10).` [L181], `01 error-code pic 999.` [L227] and
#   `03 ws-Conv-Date pic x(10).` [L184] - declared and never referenced anywhere
#   in the program. `03 ws-swap` [L183] IS modelled, inside
#   `dates.zz070_convert_date`, because [L614] and [L616] use it.
#
# 7.6  MESSAGE LITERALS
#   `prog-name` [L125] survives as the log prefix. `PL003` [L217], `PL006`
#   [L218], `PL201` [L220], `PL202` [L221], `PL203` [L222] and `PL204` [L223]
#   survive only insofar as they become log text; `PL204` is in fact never
#   referenced by any statement.
#
# 7.7  THE OTM4 SEQUENCE IS IN-MEMORY ONLY
#   It reaches no schema table and appears in no table dump - see STRUCTURAL
#   NOTES 5.1. Its `OI-Header` layout is the PUBLISHED `records/otm5.OiHeader`,
#   so nothing was declared privately after all; only the FILE was.
#
# 7.8  THINGS `pl055` SIMPLY DOES NOT HAVE, STATED EXPLICITLY
#   * NO print file and NO `call "SYSTEM" using Print-Report` - unlike `sl060`,
#     `sl100`, `pl060` and `pl100`. Nothing is spooled to the operating system.
#   * NO `PInvoice-Start` and NO `set fn-` of any kind - so no cursor
#     repositioning to emulate. `sl055` has `Invoice-Start`
#     [sales/sl055.cbl:L476] preceded by `set fn-not-less-than to true`
#     [sales/sl055.cbl:L475].
#   * NO skip-invoice paragraph, NO proforma filter, NO pending filter and NO
#     `ws-p-flag` - divergence 7. `pl055` has ONE conditional `goback` [L432]
#     where `sl055` has two [sales/sl055.cbl:L509, L518].
#   * ZERO IRS fan-out tests. It is an extract program, like `sl055`; the
#     `IRS-Used`/`IRS-Instead` switch [copybooks/wssystem.cob:L179-L181] is
#     tested by `sl060`/`pl060`, not here.
#   * ZERO `ROUNDED` stores and ZERO `DIVIDE` statements. Every store in this
#     program truncates toward zero. The five `ROUNDED` sites in the whole
#     migration are [general/gl051.cbl:L791], [general/gl051.cbl:L796],
#     [general/gl080.cbl:L328], [irs/irs030.cbl:L1551] and
#     [irs/irs030.cbl:L1562] - none of them here.
#   * ZERO `ON SIZE ERROR`, ZERO `REMAINDER`, ZERO relation-condition
#     arithmetic.
#   * NO `zz050`, NO `zz060` and NO `maps03`/`maps04` wrapper. `pl055` does not
#     `copy "wsmaps03.cob"` and never calls the date module, so anomaly A-22 -
#     the wrapper named after the copybook with its exit named after the called
#     program, [general/gl070.cbl:L603-L609] - CANNOT ARISE HERE. Only `zz070`
#     exists.
#   * NO `PERFORM ... THRU`.
#
# -----------------------------------------------------------------------------
# 8.  AMBIGUITY REGISTER - EIGHT QUESTIONS FOR THE ORACLE
#
# Rule R-6 makes compiled behaviour the tie-breaker and requires each resolution
# to be documented. These are the questions this module cannot settle by reading
# the source; each is marked `AMBIGUITY Q-PL055-<n>` at the site it affects and
# belongs in `docs/migration/ambiguity-resolutions.md`.
#
#   Q-PL055-1  The observable effect of the missing `WITH FILLER` at [L547].
#              Site: `_initialise_oi_header`.  Divergence 5.
#   Q-PL055-2  Whether the unguarded `Create-Anal` -> `Create-Main` retry
#              [L499] can fail to terminate, and what the compiled program does
#              when `Analysis-Write` [L494] fails.
#              Site: `_create__create_main`.
#   Q-PL055-3  The negated `oi-` extract row against the UNNEGATED `ih-` sum:
#              for a credit note the OTM4 row carries negatives [L571-L575]
#              while `ws-inv-amt` [L580] holds the positive sum that [L584]
#              adds into `pl-credit-notes-this-month`.
#              Site: `_extract`.  Divergences 1 and 2.
#   Q-PL055-4  The disposition of a failed `write open-item-record-4` [L588]:
#              the diagnostic transfers no control, so the sequence is left
#              short with no retry and no abort, and the partial state stands.
#              Site: `_extract`.
#   Q-PL055-5  The `OI-Header` / `open-item-record-4` storage relationship and
#              whether the object handoff to `pl060` can differ from the
#              113-byte handoff the COBOL performs.
#              Site: `_OpenItemFile4`.  Divergence 13.  See 5.2 above.
#   Q-PL055-6  Whether any mandated scenario seeds `File-System-Used` to zero
#              and therefore reaches the `FS-Cobol-Files-Used` branch at all.
#              Site: `_mainline`.  See 7.1 above.
#   Q-PL055-7  The exact shape of the single context argument the generated
#              facade verbs take.
#              Site: `_FacadeContext`.
#   Q-PL055-8  Which purchase-invoice record shape the `acas026` handler wants -
#              the flat `plwspinv2.cob` views this program copies, or the nested
#              `plwspinv.cob` `PInvoiceHeader` the published handler dispatches
#              on.
#              Site: `_FacadeContext`.
#
# TWO FURTHER QUESTIONS AROSE DURING VALIDATION AND ARE NOT IN THE REGISTER
# BECAUSE THEY WERE ANSWERED, NOT DEFERRED. Both concern what a COBOL `WRITE`
# against an existing key does, and both were settled by reading the handler
# rather than by reasoning about the COBOL:
#   * `Value-Write` [L474] against an existing roll-up key. `ba070_process_write`
#     in `acas_posting.dal.acas013_value` issues `INSERT INTO `VALUEANAL-REC`
#     SET ...`, and on `1062`/`1022`/SQLSTATE `23000` sets `FS-Reply` 22 and
#     LEAVES THE STORED ROW UNTOUCHED - reproducing
#     [common/valueMT.cbl:L817-L831]. So the roll-up totals survive; the defect
#     is an unchecked duplicate INSERT and a stale status, NOT a lost update.
#     Recorded as FINDING A in section 4.
#   * `Analysis-Write` [L494, L497] against an existing analysis key. Same shape
#     in `acas_posting.dal.acas015_analysis`; the reply is never tested at either
#     call site, so a duplicate is silently tolerated.
# They are minuted here because the FIRST reading of the source suggested a lost
# update, and the wrong reading is easy to arrive at independently. It is worth a
# reader's while to know it was checked against the handler and rejected.
#
# -----------------------------------------------------------------------------
# 9.  WHAT THIS PROGRAM WRITES - THREE TABLES AND ONE WORK SEQUENCE
#
#   VALUEANAL-REC     `Value-Write` [L335, L474, L520] and `Value-Rewrite`
#                     [L337, L356, L522, L534]
#   ANALYSIS-REC      `Analysis-Write` [L494, L497] - the emergency records
#   PUINVOICE-REC     `PInvoice-Rewrite` [L371, L397], stamping `ih-update` and
#                     `ih-status`
#   PUINV-LINES-REC   `PInvoice-Rewrite` [L359], stamping `il-update`
#   SYSTOT-REC        indirectly, through the two period-total adds at [L582]
#                     and [L584] - sites 6 and 7 of the nine period-total writes
#                     that Agent Action Plan section 0.6.4 calls *"the sole
#                     writers"* of that record. Persisted by the menu, not here;
#                     see citation correction 6.3.
#   SYSTEM-REC        indirectly, through the `Date-Form` default at [L610].
#   open-item-file-4  the OTM4 work sequence, which `pl060` consumes and which
#                     reaches no table.
#
# --- end traceability -------------------------------------------------------
