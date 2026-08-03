"""`pl100` - the Purchase Cash Posting program  [purchase/pl100.cbl].

The migration of `purchase/pl100.cbl` in its entirety - 798 lines, on-screen
title `"Purchase Cash Posting"` [purchase/pl100.cbl:L299]. Boundary: THE WHOLE
PROGRAM. Unlike `gl051` (control-total gate only) and `irs030`
(`Ledger-Postings-Add` only), nothing here is out of scope.

READ THIS FIRST - THE HEADLINE DEFECT, AND IT IS IN NO ANOMALY REGISTER
======================================================================

`bl-open` opens the two posting files with a MUTUALLY EXCLUSIVE `IF ... ELSE`
where every sibling program uses two independent `IF`s, and the condition it
tests omits `IRS-Both-Used`.  Verbatim [purchase/pl100.cbl:L566-L570]::

    566      if       irs-used      *> will open as o/p if not exist
    567               perform SPL-Posting-Open-Extend  *> needed: - bug in OC
    568      else                   *> will open as o/p if not exist
    569               perform GL-Posting-Open          *>  open i-o Posting-file
    570      end-if.

Contrast the correct sibling [purchase/pl060.cbl:L907-L920], which tests both
condition names, keeps the two opens INDEPENDENT, and retries a failed open as
`open output`::

    907      if       irs-used OR IRS-Both-Used
    908               perform SPL-Posting-Open-Extend
    909               if fs-reply not = zero
    910                  perform SPL-Posting-Close
    911                  perform SPL-Posting-Open-Output
    912               end-if
    913      end-if
    914      if       IRS-Both-Used or G-L
    915               perform GL-Posting-Open
    916               if  fs-reply not = zero
    917                   perform GL-Posting-Close
    918                   perform GL-Posting-Open-Output
    919               end-if
    920      end-if

Three separate defects live in those five `pl100` lines, and ALL THREE are
reproduced here:

(a) `[L566]` tests `irs-used` ALONE.  In `"B"` mode (`IRS-Both-Used`) the
    condition is FALSE, so the `else` runs and `SPL-Posting-Open-Extend` is
    NEVER performed - yet `bl-write` `[L629]` writes under
    `irs-used or IRS-Both-Used`, so `SPL-Posting-Write` executes against a file
    that was never opened.
(b) It is an `ELSE`, so the two opens are mutually exclusive.  In `"Y"` mode
    (`irs-used`) `GL-Posting-Open` is never performed - yet `bl-write`
    `[L646-L647]` writes under `IRS-Both-Used or G-L`, so with `G-L` also set
    `GL-Posting-Write` executes against a file that was never opened.
(c) There are NO fallback blocks.  `pl100` calls neither
    `SPL-Posting-Open-Output` nor `GL-Posting-Open-Output` ANYWHERE, so a
    failed open is simply ignored.

Compounding all three, `bl-close` `[L674-L677]` closes BOTH files under the
`pl060`-style predicates - closing files that may never have been opened.  And
the 99-item batch cap `[L653-L655]` re-performs `bl-open`, so every reopen
repeats the whole condition.

Those three defects are reproduced together as ANOMALY **A-NEW-5**, annotated at
the reproduction site in `_bl_open` and registered in the traceability footer
under that identifier.  It is called A-NEW-5 because it appears in NO anomaly
register - not in the plan's 22-entry list and not in any prior document.

One claim that is NOT true, recorded here because it is the obvious thing to
assume and it is wrong: there is no *further* write-without-open path via
`[L316-L317]`.  `BL-Open` is gated on `G-L`, but so is `BL-Write` `[L409-L410]`
and so is `bl-close` `[L454-L455]` - all three gates are `G-L` ALONE and they
agree, so with `G-L` unset none of the three runs and the IRS fan-out inside
`bl-write` never executes at all.  Verified by driving the
`"B"`-mode-with-`G-L`-unset case: zero batch and zero posting verbs are
reached.  Nor is that a `pl100` divergence -
[purchase/pl060.cbl:L405-L406], [purchase/pl060.cbl:L474-L475] and
[purchase/pl060.cbl:L573-L574] gate identically.  See finding F-17.

This is why `pl100` has SIX IRS fan-out sites where `sl060`, `sl100` and
`pl060` each have SEVEN: the seventh site is the second, independent open that
`pl100` does not have.

DO NOT COPY, IMPORT OR PARAMETERISE ITS SIBLINGS
================================================

`pl100` is structurally similar to `pl060` and `sl100` and behaviourally
divergent from both in ways that change stored figures.  Quoting the plan:
"Normalising them into one helper would be the single easiest way to fail this
migration."  This module therefore imports NO other `acas_posting.programs.*`
module, and every shared-looking idiom is written out in full.  The measured
divergences, each reproduced below:

===========================  =========================  =====================
Site                         `pl100`                    the sibling
===========================  =========================  =====================
posting-file opens           one `IF/ELSE`, no          `pl060` L907-L920: two
                             fallback [L566-L570]       `IF`s + two fallbacks
DR / CR sides                `p-creditors`->`post-dr`,  `pl060` L958-L959: the
                             `bl-pay-ac`->`post-cr`     two are SWAPPED
                             [L612-L613]
`vat-ac`                     ZEROED [L617]              `pl060` L966-L967
                                                        COPIES it
VAT accumulation             NONE - a payment carries   `pl060` L973-L976 adds
                             no VAT                     `input-vat`/`actual-vat`
control totals               TWO adds [L623-L624]       `pl060`: FOUR
batch-number field           `bl-next-batch`            `pl060` L885-L887:
                             [L546][L548]               `next-batch`
`post-legend`                ONE `STRING` of three      `sl100` L620-L628: FIVE
                             sources [L608-L610]        separate `STRING`s
moving average               variant (d) - see below    `pl060` L740-L768 has
                                                        variants (a) and (b)
unknown supplier             print name only, NO        `pl060` L436-L440 and
                             `Purch-Write` [L356-L361]  L515-L519 CREATE it
`purch-current` sign flip    `GIVING` form [L387] so    `pl060` L507: no
                             it is not mutated          `GIVING`, so it IS
supplier-read test           `fs-reply = 21` [L356]     `pl060` L433:
                                                        `not = zero`
`l5-date` source             `u-date` [L369]            `pl060` L448: `ws-date`
batch-write accept           unwrapped [L670]           `pl060` L1022-L1025
                                                        wraps it in
                                                        `WS-Caller not=xl150`
status section               `Eval-Status`, exit         `pl060` L1037:
                             `main-exit` [L681][L687]   `evaluate-message`,
                                                        exit `Eval-Msg-Exit`
===========================  =========================  =====================

ANOMALY A-8 DOES *NOT* APPLY TO THIS FILE
=========================================

A-8 is the double truncation of the moving average: a two-decimal money value
entering a zero-scale accumulator, and then an integer divide.  It requires a
two-decimal sending field.  `pl100`'s average has none.  Both accumulators are
integer `binary-long` [purchase/pl100.cbl:L175-L176], and the value entering
them is a DAY COUNT derived by subtracting one binary day number from another
[purchase/pl100.cbl:L494].  There is therefore exactly ONE truncation here -
the integer divide at `[L502]` - not two.  Do not go looking for `work-goods`
or any money field in `compute-purch-pay`; there is none.  The same conclusion
holds for `[sales/sl100.cbl:L497-L516]`.

What `pl100` DOES carry is A-10 variant (d) of four - the fourth mutually
inconsistent spelling of the same moving-average idiom.  Verbatim
[purchase/pl100.cbl:L488-L508]::

    488  compute-purch-pay.
    491      if       oi-date-cleared = zero
    492               go to csp-exit.
    494      subtract oi-date from oi-date-cleared giving work-a.
    495      move     zero to work-b.
    497      if       purch-pay-activety not = zero
    498               multiply purch-pay-activety by purch-pay-average
    498                                                     giving work-b.
    500      add      work-a to work-b.
    501      add      1 to purch-pay-activety.
    502      divide   work-b by purch-pay-activety giving purch-pay-average.
    504      if       work-a > purch-pay-worst
    505               move work-a to purch-pay-worst.
    507  csp-exit.
    508      exit.

Five differences from `pl060`'s two variants, every one preserved:

1. `move zero to work-b` `[L495]` is UNCONDITIONAL and PRECEDES the guard, so
   there is NO `ELSE`.  `pl060` puts the zero move in an `ELSE`.
2. The guard `[L497]` is ONE condition.  `pl060`'s is a two-condition `AND`
   [purchase/pl060.cbl:L743-L744] and [purchase/pl060.cbl:L758-L759].
3. The counter is incremented AFTER the accumulate - `[L500]` then `[L501]`.
   `pl060`'s `purch-comp` increments BEFORE
   [purchase/pl060.cbl:L749-L750].
4. The divide is the `BY` form, so `purch-pay-average = work-b /
   purch-pay-activety`.  `pl060` uses the `INTO` form, which divides the other
   way round.
5. It maintains a worst-case watermark `[L504-L505]` that `pl060` has no
   equivalent of.

Four variants, four separate functions, four separate modules.  There is no
shared helper, no `average()` utility in `cobol/` and no parameter selecting
behaviour.

WHAT THIS PROGRAM DOES, AND WHAT IT WRITES
==========================================

`pl100` walks the OTM5 purchase open-item file sequentially from the top,
updates the purchase ledger for payments (`oi-type = 5`) and credit journals
(`oi-type = 6`), maintains a payment-days moving average and worst-case
watermark, writes the General Ledger batch and posting records plus the IRS
fan-out records, and finally reverses the accumulated deductions out of the
`"Pzb"` value-analysis group that `pl055` created.

Tables and control fields it writes:

* `PULEDGER-REC`   - `Purch-Rewrite` `[L405]`, issued UNCONDITIONALLY, so also
                     for suppliers that were never read (A-NEW-6).
* `PUITM5-REC`     - two distinct `OTM5-Rewrite` paths, `[L339]` (the type-2
                     batch-linkage clear) and `[L413]` (the posted status).
* `GLBATCH-REC`    - `GL-Batch-Write` `[L663]`.
* `GLPOSTING-REC`  - `GL-Posting-Write` `[L649]`.
* `PSIRSPOST-REC`  - `SPL-Posting-Write` `[L644]`.
* `VALUEANAL-REC`  - the `"Pzb"` reversal, `Value-Rewrite` `[L525]` `[L537]`.
* `SYSTOT-REC`     - `pl-payments`, period total 9 of 9 `[L396]`.
* `SYSTEM-REC`     - `bl-next-batch` `[L548]`, `postings` `[L672]`,
                     `oi-5-flag` `[L464]`, `P-Flag-P` `[L465]`.

`SYSTEM-REC` and `SYSTOT-REC` are NOT written by this program through a facade
verb - it mutates the two linkage records in place and the CALLER persists
them.  `[purchase/purchase.cbl:L691-L706]` (`load000`) calls `pl100` with the
five-parameter linkage list and then performs `overrewrite` when
`ws-term-code < 8`.  There is consequently no `System-*` facade verb anywhere
in `pl100`, and this module calls none.

THE `pl055` -> `pl100` DEDUCTION CONTRACT
=========================================

`analise-deductions` `[L513]` moves the literal `"Pzb"` into `va-code`.  That
three-character key is the group `pl055` CREATES: `[purchase/pl055.cbl:L403]`
moves `"P"` to `va-system` and `[purchase/pl055.cbl:L416]` moves `"zb"` to
`va-group`, the discount/deduction special total.  `pl055` ADDS to it
[purchase/pl055.cbl:L514-L517]; `pl100` SUBTRACTS from it.  Break either half
and the value-analysis totals drift with no error reported anywhere.  The
coupling is through the `VALUEANAL-REC` table exactly as in COBOL, so this
module does NOT import `pl055_order_proof_extract`; the CLI sequences the two
calls.

THE TWO WORK VARIABLES ARE DIFFERENT TYPES - THE LOCAL TRAP
===========================================================

`work-1` is `pic s9(7)v99 comp-3` [purchase/pl100.cbl:L174] - MONEY, a
`Decimal` with scale 2.  `work-a` and `work-b` are `binary-long`
[purchase/pl100.cbl:L175-L176] - INTEGER day counts, Python `int`.  `[L383]`
and `[L387]` use `work-1`; `[L494]` through `[L502]` use `work-a`/`work-b`.
Crossing them corrupts either the ledger or the average.

ZERO `ROUNDED` SITES
====================

`pl100` contains no `ROUNDED` phrase anywhere.  All five `ROUNDED` sites in the
whole migration live elsewhere - `gl051` L791 and L796, `gl080` L328, `irs030`
L1551 and L1562.  Every store in this program therefore truncates toward zero,
which is the default of `cobol.arithmetic`, and no call below sets the rounding
flag on any arithmetic helper - a property a reader can check mechanically,
since the flag would have to appear by name in the source to be set.

DETERMINISM
===========

`pl100` performs ZERO clock reads.  The run date arrives entirely through
linkage - the text date as `to-day pic x(10)` and the binary date as
`Run-Date binary-long` on the system record [copybooks/wssystem.cob:L67],
which `[L551]` moves into the batch `entered` field.  This module reads no
clock, imports no clock and holds no ambient state, so two runs against the
same seed and the same pinned linkage produce byte-identical table state.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field as dc_field
from decimal import Decimal
from typing import Final, Mapping

# The COBOL-language semantics runtime.  Per plan section 0.3.1, "`cobol/`
# contains no business logic and `programs/` contains no numeric primitives" -
# every picture-clause store, MOVE truncation, reference modification,
# INSPECT, STRING, edited move, comparison and 88-level test below is
# delegated to these modules.
from acas_posting import dates  # consolidated maps04 + zz050/zz060/zz070
from acas_posting.cobol import arithmetic, condition_names, picture
from acas_posting.cobol import move as movelib
from acas_posting.cobol.field import FieldDescriptor

# copy "Proc-ACAS-FH-Calls.cob".  [purchase/pl100.cbl:L797] - the ENTITY-named
# facade vocabulary, with every reply tested INLINE by the caller.  `pl100`
# does not use the handler-named `Proc-ZZ100-ACAS-IRS-Calls` convention, so no
# handler-named alias is referenced below.
from acas_posting.dal import facade

# copy "wsfnctn.cob".  [purchase/pl100.cbl:L129] - the single COBOL copybook
# splits into the record layout (records.file_access) and the operation
# vocabulary (dal.status), which is why one `copy` becomes two imports.
from acas_posting.dal.status import FsReply
from acas_posting.records.calling_data import WsCallingData  # copy "wscall" L258
from acas_posting.records.file_access import FileAccess  # copy "wsfnctn" L129
from acas_posting.records.file_defs import FileDefs  # copy "wsnames" L261
from acas_posting.records.gl_batch import GlBatchRecord  # copy "wsbatch" L215
from acas_posting.records.gl_posting import WsPostingRecord  # copy "wspost" L217
from acas_posting.records.maps03 import Maps03Ws  # copy "wsmaps03" L128
# copy "plwsoi5C.cob".  [purchase/pl100.cbl:L213] - note the 5C variant;
# `pl060` copies 5B.  The record the program addresses is `OI-Header`, the
# REDEFINES view, not the raw `WS-OTM5-Record` buffer: `[L328]` and `[L338]`
# carry commented-out `move open-item-record-5 to oi-header` statements,
# switched off precisely because the copybook's `replacing` clause
# [copybooks/plwsoi5C.cob:L19-L20] makes `OI-Header` a redefinition of the
# same bytes, so no transfer is needed.  `acas029_otm5.dispatch` takes
# `OiHeader` for the same reason.
from acas_posting.records.otm5 import (
    Filler1,
    OiBatch,
    OiCustomer,
    OiHeader,
    OiKey,
    OiSupplier,
    descriptors_of,
)
from acas_posting.records.purchase_ledger import WsPurchRecord  # copy "wspl" L214
from acas_posting.records.spl_irs_posting import (  # copy "wspost-irs" L218
    WsIrsPostingRecord,
)
from acas_posting.records.system_record import SystemRecord  # copy "wssystem" L259
from acas_posting.records.system_record_4 import SystemRecord4  # copy "wssys4" L260
from acas_posting.records.test_data_flags import (  # copy "Test-Data-Flags" L210
    AcasDalCommonData,
)
from acas_posting.records.value_analysis import WsValueRecord  # copy "wsval" L216

__all__: Final[tuple[str, ...]] = ("run",)

_LOG: Final = logging.getLogger(__name__)

#: The frozen COBOL specification this module reproduces.  Every locator in
#: this file is relative to it unless another path is named explicitly.
_SRC: Final[str] = "purchase/pl100.cbl"

#: ``77  prog-name  pic x(15)  value "PL100 (3.3.01)".``  [purchase/pl100.cbl:L125]
_PROG_NAME: Final[str] = "PL100 (3.3.01)"

#: ``03  PL002  pic x(31) value "PL002 Note error and hit return".``  [L204]
#: DECLARED AND DELIBERATELY NEVER REFERENCED.  Both of its displays - [L291] and
#: [L669] - stand immediately before an `accept ws-reply`, and the literal is
#: nothing but the instruction to press that key, so plan section 0.3.4 drops it
#: with the pause and no log record carries it; the substantive diagnostic on each
#: of those paths is the `PL137`/`PL132` record beside it.  The DECLARATION stays
#: because rule R-5 maps the whole `01 Error-Messages.` group and a shorter group
#: would misreport the frozen source.  See the OMISSIONS list in the footer.
_PL002: Final[str] = "PL002 Note error and hit return"
#: ``03  PL132  pic x(32) value "PL132 Err on Batch file write : ".``  [L207]
_PL132: Final[str] = "PL132 Err on Batch file write : "
#: ``03  PL137  pic x(26) value "PL137 Payments Not Proofed".``  [L208]
_PL137: Final[str] = "PL137 Payments Not Proofed"


# ==========================================================================
# WORKING-STORAGE FIELD DESCRIPTORS  [purchase/pl100.cbl:L125-L176]
# ==========================================================================
# Program-local items have no data-dictionary entry, because they never reach
# a table.  They are therefore described through `cobol.picture`, which is the
# documented path for exactly this case and which requires an explicit
# `source_locator` - the only traceability a program-local field can carry.


def _local(clauses: str, *, name: str, line: int, level: str = "03") -> FieldDescriptor:
    """Describe one program-local working-storage item of `pl100`.

    `clauses` is the item's declaration text with the level and name removed,
    exactly as it appears in the COBOL.  `line` is its line in
    `purchase/pl100.cbl`, which becomes the descriptor's `source_locator` and
    satisfies the traceability requirement that every descriptor carry either a
    `dictionary_key` or a `source_locator`.
    """
    return picture.descriptor_for(
        clauses,
        name=name,
        source_locator=f"{_SRC}:L{line}",
        level=level,
    )


# 77  exception-msg  pic x(25)  value spaces.                             [L126]
_D_EXCEPTION_MSG: Final = _local("pic x(25)", name="exception-msg", line=126, level="77")
# 03  ws-reply       pic x      value space.                             [L156]
_D_WS_REPLY: Final = _local("pic x", name="ws-reply", line=156)
# 03  wx-reply       pic xxx    value spaces.                            [L157]
_D_WX_REPLY: Final = _local("pic xxx", name="wx-reply", line=157)
# 03  xx             pic 99     value zero.   - the STRING pointer        [L158]
_D_XX: Final = _local("pic 99", name="xx", line=158)
# 03  i              pic 99     value zero.   - declared, never referenced [L159]
_D_I: Final = _local("pic 99", name="i", line=159)
# 03  j              pic 99     value zero.   - the page counter          [L160]
_D_J: Final = _local("pic 99", name="j", line=160)
# 03  k              pic 999    value zero.   - declared, never referenced [L161]
_D_K: Final = _local("pic 999", name="k", line=161)
# 03  m              pic z(7)9.               - the EDITED move receiver  [L162]
_D_M: Final = _local("pic z(7)9", name="m", line=162)
# 03  b              binary-char value zero.  - the INSPECT tally         [L163]
_D_B: Final = _local("binary-char", name="b", line=163)
# 03  c              binary-char value zero.  - the ref-mod length        [L164]
_D_C: Final = _local("binary-char", name="c", line=164)
# 03  save-level-1   pic 9      value zero.   - only the commented-out
#     GL-bypass block at [L282-L283]/[L460] ever used it; see FINDINGS.   [L165]
_D_SAVE_LEVEL_1: Final = _local("pic 9", name="save-level-1", line=165)
# 03  line-cnt       binary-char value zero.  - tested at [L422]          [L166]
_D_LINE_CNT: Final = _local("binary-char", name="line-cnt", line=166)
# 03  n-deduct       binary-long value zero.  - a COUNT, not money        [L167]
_D_N_DEDUCT: Final = _local("binary-long", name="n-deduct", line=167)
# 03  t-paid         pic s9(7)v99 comp-3 value zero.                      [L168]
_D_T_PAID: Final = _local("pic s9(7)v99 comp-3", name="t-paid", line=168)
# 03  t-approp       pic s9(7)v99 comp-3 value zero.                      [L169]
_D_T_APPROP: Final = _local("pic s9(7)v99 comp-3", name="t-approp", line=169)
# 03  t-deduct       pic s9(7)v99 comp-3 value zero.  - gates [L449]      [L170]
_D_T_DEDUCT: Final = _local("pic s9(7)v99 comp-3", name="t-deduct", line=170)
# 03  j-paid         pic s9(7)v99 comp-3 value zero.                      [L171]
_D_J_PAID: Final = _local("pic s9(7)v99 comp-3", name="j-paid", line=171)
# 03  j-approp       pic s9(7)v99 comp-3 value zero.                      [L172]
_D_J_APPROP: Final = _local("pic s9(7)v99 comp-3", name="j-approp", line=172)
# 03  j-deduct       pic s9(7)v99 comp-3 value zero.  - merged at [L448]  [L173]
_D_J_DEDUCT: Final = _local("pic s9(7)v99 comp-3", name="j-deduct", line=173)
# 03  work-1         pic s9(7)v99 comp-3 value zero.  - MONEY (Decimal)   [L174]
_D_WORK_1: Final = _local("pic s9(7)v99 comp-3", name="work-1", line=174)
# 03  work-a         binary-long value zero.  - an INTEGER DAY COUNT      [L175]
_D_WORK_A: Final = _local("binary-long", name="work-a", line=175)
# 03  work-b         binary-long value zero.  - an INTEGER accumulator    [L176]
_D_WORK_B: Final = _local("binary-long", name="work-b", line=176)


# ==========================================================================
# RECORD FIELD DESCRIPTORS - every one traced to a data-dictionary entry
# ==========================================================================
# Plan section 0.8.1: the dictionary is generated from the authoritative triple
# (copybook picture clause, bridge host variable, CREATE TABLE column), and
# "every Python field definition cites its entry".  `from_dictionary_key` is
# the only factory, so citing the key IS the traceability.

_K = FieldDescriptor.from_dictionary_key

# --- WS-Purch-Record  copy "wspl.cob"  [purchase/pl100.cbl:L214] ----------
_D_PURCH_KEY: Final = _K("PULEDGER-REC.PURCH-KEY")
_D_PURCH_NAME: Final = _K("PULEDGER-REC.PURCH-NAME")
_D_PURCH_CURRENT: Final = _K("PULEDGER-REC.PURCH-CURRENT")
_D_PURCH_UNAPPLIED: Final = _K("PULEDGER-REC.PURCH-UNAPPLIED")
_D_PURCH_LAST_PAY: Final = _K("PULEDGER-REC.PURCH-LAST-PAY")
# The three payment-statistics fields are all `binary-long` - integers.  That
# is precisely why the A-10 variant (d) divide at [L502] truncates.
_D_PURCH_PAY_ACTIVETY: Final = _K("PULEDGER-REC.PURCH-PAY-ACTIVETY")
_D_PURCH_PAY_AVERAGE: Final = _K("PULEDGER-REC.PURCH-PAY-AVERAGE")
_D_PURCH_PAY_WORST: Final = _K("PULEDGER-REC.PURCH-PAY-WORST")

# --- OI-Header  copy "plwsoi5C.cob"  [purchase/pl100.cbl:L213] ------------
# `OI-Header` is declared by BOTH `copybooks/plwsoi.cob` (purchase) and
# `copybooks/slwsoi.cob` (sales), so a bare dictionary lookup on the record
# name is ambiguous.  `records.otm5.descriptors_of` exists for exactly this
# reason: it returns the PURCHASE descriptors keyed by attribute name.
_OI_HEADER_D: Final = descriptors_of(OiHeader)
_OI_KEY_D: Final = descriptors_of(OiKey)
_OI_SUPPLIER_D: Final = descriptors_of(OiSupplier)
_OI_BATCH_D: Final = descriptors_of(OiBatch)
_OI_MONEY_D: Final = descriptors_of(Filler1)

_D_OI_NOS: Final = _OI_SUPPLIER_D["oi_nos"]
_D_OI_CHECK: Final = _OI_SUPPLIER_D["oi_check"]
_D_OI_INVOICE: Final = _OI_KEY_D["oi_invoice"]
_D_OI_DATE: Final = _OI_HEADER_D["oi_date"]
_D_OI_TYPE: Final = _OI_HEADER_D["oi_type"]
_D_OI_STATUS: Final = _OI_HEADER_D["oi_status"]
_D_OI_B_NOS: Final = _OI_BATCH_D["oi_b_nos"]
_D_OI_B_ITEM: Final = _OI_BATCH_D["oi_b_item"]
_D_OI_CR: Final = _OI_HEADER_D["oi_cr"]
_D_OI_DEDUCT_AMT: Final = _OI_HEADER_D["oi_deduct_amt"]
_D_OI_DATE_CLEARED: Final = _OI_HEADER_D["oi_date_cleared"]
_D_OI_APPROP: Final = _OI_MONEY_D["oi_approp"]
_D_OI_PAID: Final = _OI_MONEY_D["oi_paid"]

# --- WS-Value-Record  copy "wsval.cob"  [purchase/pl100.cbl:L216] ---------
# `records.value_analysis.VaCode` documents that "no method assembles the
# three characters into a key", so `move "Pzb" to va-code` [L513] is
# distributed across the three subordinate items here, in the program, which
# is where COBOL's group MOVE distributes it.
_D_VA_CODE: Final = _K("VALUEANAL-REC.VA-CODE")
_D_VA_SYSTEM: Final = _K("WS-Value-Record.va-system")
_D_VA_FIRST: Final = _K("WS-Value-Record.va-first")
_D_VA_SECOND: Final = _K("WS-Value-Record.va-second")
# The count fields are UNSIGNED `pic 9(5) comp`; the value fields are signed
# `s9(8)v99 comp-3`.  [L519-L522] subtracts a COUNT from the former pair and a
# VALUE from the latter pair - two different accumulators, four subtracts.
_D_VA_T_THIS: Final = _K("VALUEANAL-REC.VA-T-THIS")
_D_VA_T_YEAR: Final = _K("VALUEANAL-REC.VA-T-YEAR")
_D_VA_V_THIS: Final = _K("VALUEANAL-REC.VA-V-THIS")
_D_VA_V_YEAR: Final = _K("VALUEANAL-REC.VA-V-YEAR")

# --- WS-Batch-Record  copy "wsbatch.cob"  [purchase/pl100.cbl:L215] -------
_D_WS_LEDGER: Final = _K("WS-Batch-Record.WS-Ledger")
_D_WS_BATCH_NOS: Final = _K("WS-Batch-Record.WS-Batch-Nos")
_D_ITEMS: Final = _K("GLBATCH-REC.ITEMS")
_D_BATCH_STATUS: Final = _K("GLBATCH-REC.BATCH-STATUS")
_D_CLEARED_STATUS: Final = _K("GLBATCH-REC.CLEARED-STATUS")
_D_BCYCLE: Final = _K("GLBATCH-REC.BCYCLE")
_D_ENTERED: Final = _K("GLBATCH-REC.ENTERED")
_D_INPUT_GROSS: Final = _K("GLBATCH-REC.INPUT-GROSS")
_D_INPUT_VAT: Final = _K("GLBATCH-REC.INPUT-VAT")
_D_ACTUAL_GROSS: Final = _K("GLBATCH-REC.ACTUAL-GROSS")
_D_ACTUAL_VAT: Final = _K("GLBATCH-REC.ACTUAL-VAT")
_D_DESCRIPTION: Final = _K("GLBATCH-REC.DESCRIPTION")
_D_BDEFAULT: Final = _K("GLBATCH-REC.BDEFAULT")
_D_CONVENTION: Final = _K("GLBATCH-REC.CONVENTION")
_D_BATCH_DEF_AC: Final = _K("GLBATCH-REC.BATCH-DEF-AC")
_D_BATCH_DEF_PC: Final = _K("GLBATCH-REC.BATCH-DEF-PC")
_D_BATCH_DEF_CODE: Final = _K("GLBATCH-REC.BATCH-DEF-CODE")
_D_BATCH_DEF_VAT: Final = _K("GLBATCH-REC.BATCH-DEF-VAT")
_D_BATCH_START: Final = _K("GLBATCH-REC.BATCH-START")

# --- WS-Posting-Record  copy "wspost.cob"  [purchase/pl100.cbl:L217] ------
_D_WS_POST_RRN: Final = _K("GLPOSTING-REC.POST-RRN")
_D_POST_BATCH: Final = _K("WS-Posting-Record.Batch")
_D_POST_NUMBER: Final = _K("WS-Posting-Record.Post-Number")
_D_POST_CODE: Final = _K("GLPOSTING-REC.POST-CODE")
_D_POST_DATE: Final = _K("GLPOSTING-REC.POST-DAT")
_D_POST_DR: Final = _K("GLPOSTING-REC.POST-DR")
_D_DR_PC: Final = _K("GLPOSTING-REC.DR-PC")
_D_POST_CR: Final = _K("GLPOSTING-REC.POST-CR")
_D_CR_PC: Final = _K("GLPOSTING-REC.CR-PC")
_D_POST_AMOUNT: Final = _K("GLPOSTING-REC.POST-AMOUNT")
_D_POST_LEGEND: Final = _K("GLPOSTING-REC.POST-LEGEND")
_D_VAT_AC: Final = _K("GLPOSTING-REC.VAT-AC")
_D_VAT_PC: Final = _K("GLPOSTING-REC.VAT-PC")
_D_POST_VAT_SIDE: Final = _K("GLPOSTING-REC.POST-VAT-SIDE")
_D_VAT_AMOUNT: Final = _K("GLPOSTING-REC.VAT-AMOUNT")

# --- WS-IRS-Posting-Record  copy "wspost-irs.cob"  [purchase/pl100.cbl:L218] -
# The DR and CR account numbers NARROW from `9(6)` on the GL side to `9(5)`
# here, so the fan-out moves at [L634]/[L636] are truncating stores.  The two
# amount fields are `SIGN LEADING` display, not COMP-3.
_D_IRS_BATCH: Final = _K("WS-IRS-Posting-Record.WS-IRS-Batch")
_D_IRS_POST_NUMBER: Final = _K("WS-IRS-Posting-Record.WS-IRS-Post-Number")
_D_IRS_POST_CODE: Final = _K("PSIRSPOST-REC.IRS-POST-CODE")
_D_IRS_POST_DATE: Final = _K("PSIRSPOST-REC.IRS-POST-DAT")
_D_IRS_POST_DR: Final = _K("PSIRSPOST-REC.IRS-POST-DR")
_D_IRS_POST_CR: Final = _K("PSIRSPOST-REC.IRS-POST-CR")
_D_IRS_POST_AMOUNT: Final = _K("PSIRSPOST-REC.IRS-POST-AMOUNT")
_D_IRS_POST_LEGEND: Final = _K("PSIRSPOST-REC.IRS-POST-LEGEND")
_D_IRS_VAT_AC_DEF: Final = _K("PSIRSPOST-REC.IRS-VAT-AC-DEF")
_D_IRS_POST_VAT_SIDE: Final = _K("PSIRSPOST-REC.IRS-POST-VAT-SIDE")
_D_IRS_VAT_AMOUNT: Final = _K("PSIRSPOST-REC.IRS-VAT-AMOUNT")

# --- System-Record  copy "wssystem.cob"  [purchase/pl100.cbl:L259] --------
_D_SCYCLE: Final = _K("System-Record.Scycle")
# `Run-Date binary-long` [copybooks/wssystem.cob:L67] - the second of the two
# observables the controlled clock pins.  The bridge spells it `RUN-DAT`.
_D_RUN_DATE: Final = _K("SYSTEM-REC.RUN-DAT")
_D_POSTINGS: Final = _K("SYSTEM-REC.POSTINGS")
_D_BL_NEXT_BATCH: Final = _K("SYSTEM-REC.BL-NEXT-BATCH")
_D_BL_PAY_AC: Final = _K("SYSTEM-REC.BL-PAY-AC")
_D_P_CREDITORS: Final = _K("SYSTEM-REC.P-CREDITORS")
_D_P_FLAG_P: Final = _K("SYSTEM-REC.P-FLAG-P")
_D_OI_5_FLAG: Final = _K("SYSTEM-REC.OI-5-FLAG")

# --- System-Record-4  copy "wssys4.cob"  [purchase/pl100.cbl:L260] --------
# PERIOD TOTAL 9 OF 9.  Plan section 0.6.4 calls the nine sites "the sole
# writers" of `SYSTOT-REC`; this is the ninth.
_D_PL_PAYMENTS: Final = _K("SYSTOT-REC.PL-PAYMENTS")

# --- File-Access  copy "wsfnctn.cob"  [purchase/pl100.cbl:L129] -----------
_D_RRN: Final = _K("File-Access.Rrn")
_D_FILE_KEY_NO: Final = _K("File-Access.File-Key-No")

# --- WS-Calling-Data  copy "wscall.cob"  [purchase/pl100.cbl:L258] --------
# `WS-Caller pic x(8)` [copybooks/wscall.cob:L8].  DECLARED AND DELIBERATELY
# UNUSED: `pl100` - unlike [purchase/pl060.cbl:L1022-L1025] - never tests it for
# the unattended `"xl150"` caller, and the entry log record that once rendered it
# was removed because a caller name is not inside the safe-event schema and its
# eager `move` made a diagnostic into a failure path.  The descriptor stays so the
# field keeps its dictionary citation, which is what rule R-5 asks of the group.
_D_WS_CALLER: Final = _K("WS-Calling-Data.WS-Caller")

# --- maps03-ws  copy "wsmaps03.cob"  [purchase/pl100.cbl:L128] ------------
_D_U_DATE: Final = _K("maps03-ws.u-date")
_D_U_BIN: Final = _K("maps03-ws.u-bin")


def _alpha_eq(value: str, literal: str, descriptor: FieldDescriptor) -> bool:
    """A COBOL alphanumeric relation condition, as a boolean.

    COBOL pads the shorter operand of an alphanumeric comparison with spaces
    to the length of the longer and then compares byte by byte, which is why
    ``if wx-reply = "NO"`` `[L308]` is true for the three-byte field content
    ``"NO "``.  Both operands are moved into the same receiver descriptor by
    `cobol.move`, which performs the padding and the truncation, so what
    remains here is a byte-image equality and not a padding rule.

    `arithmetic.compare` is deliberately not used: it compares numerics
    algebraically and rejects a non-numeric carrier outright.
    """
    return movelib.move(value, descriptor) == movelib.move(literal, descriptor)


# ==========================================================================
# THE OI-HEADER INITIAL IMAGE
# ==========================================================================


def _initial(descriptor: FieldDescriptor) -> Decimal | int | str:
    """The figurative initial content of one elementary item.

    `ZERO` for a numeric item and `SPACE` for an alphanumeric one, produced by
    `cobol.move` so that neither the value nor its width is written by hand.
    """
    figurative = movelib.ZERO if descriptor.is_numeric else movelib.SPACE
    return movelib.move_figurative(figurative, descriptor)


def _fresh_oi_header() -> OiHeader:
    """A zero/space-filled ``OI-Header``, matching program start.

    ``01 OI-Header`` [copybooks/plwsoi.cob:L12] carries NO `VALUE` clause, and
    the buffer it redefines is ``01 WS-OTM5-Record pic x(113)``
    [copybooks/plwsoi5C.cob:L10], which GnuCOBOL space-fills.  `records.otm5`
    therefore refuses to invent defaults and requires every field explicitly -
    a deliberate policy of the record layer, not an omission - so the initial
    image is assembled here.

    The choice is UNOBSERVABLE in `pl100`: the program reads no `OI-Header`
    field before `OTM5-Read-Next` `[L324]` has populated the whole record, and
    on end-of-file `[L325-L326]` it transfers straight to `main-end` without
    touching one.  The image exists only so the object can be constructed.
    """
    money = Filler1(**{name: _initial(d) for name, d in _OI_MONEY_D.items()})
    supplier = OiSupplier(**{name: _initial(d) for name, d in _OI_SUPPLIER_D.items()})
    oi_key = OiKey(
        oi_customer=OiCustomer(oi_supplier=supplier),
        oi_invoice=_initial(_D_OI_INVOICE),
    )
    oi_batch = OiBatch(**{name: _initial(d) for name, d in _OI_BATCH_D.items()})
    # The three group members are supplied above; every remaining attribute of
    # `OI-Header` is elementary and takes its figurative initial content.
    _GROUPS: Final[frozenset[str]] = frozenset({"oi_key", "oi_batch", "filler_1"})
    elementary = {
        name: _initial(d) for name, d in _OI_HEADER_D.items() if name not in _GROUPS
    }
    return OiHeader(
        oi_key=oi_key, oi_batch=oi_batch, filler_1=money, **elementary
    )


# ==========================================================================
# PROGRAM STATE
# ==========================================================================


@dataclass(slots=True)
class _Pl100State:
    """The whole of `pl100`'s addressable storage, in one mutable object.

    COBOL working storage is program-global: every paragraph of `pl100` reads
    and writes the same items, and control transfers between paragraphs carry
    no arguments.  Reproducing that faithfully - and it must be faithful,
    because for example `[L404]` overwrites a field that `[L396]` has already
    consumed - means the paragraph functions share one mutable state object
    rather than passing values.  Nothing here is module-global, so two
    concurrent `run()` calls could not interfere even though the COBOL is
    strictly single-threaded and this module starts no thread.

    The five linkage items are held by reference and MUTATED IN PLACE, exactly
    as `PROCEDURE DIVISION USING` binds them.  That is how `[L464]`,
    `[L465]`, `[L548]`, `[L672]` and `[L396]` reach the database: the caller
    `[purchase/purchase.cbl:L691-L706]` performs `overrewrite` afterwards.
    """

    # ---- linkage section  [purchase/pl100.cbl:L265-L269] -----------------
    ws_calling_data: WsCallingData
    system_record: SystemRecord
    system_record_4: SystemRecord4
    to_day: str
    file_defs: FileDefs

    # ---- the run-confirm answer, from `accept wx-reply` [L306] -----------
    ok_to_post: bool

    # ---- NOT A COBOL FIELD: the caller's keyword-only handler declarations --
    # Chiefly the transport-security policy, forwarded to every facade
    # `PERFORM` this program issues.  No COBOL counterpart: the frozen bridge's
    # connect passes six values and no transport policy at all
    # [copybooks/mysql-procedures.cpy:L72-L77] - transport is compiled into
    # `cobmysqlapi.c`.  An empty mapping is the SAFE answer, not the absent one:
    # every handler declares `transport: TransportSecurity | None = None` and
    # `connection._require_permitted_connection` resolves `None` fail-closed,
    # permitting a Unix socket or a loopback address and refusing every other
    # target.  Carried opaquely; `dal/facade.py` projects it onto whatever extras
    # each handler declares.
    dal_options: Mapping[str, object] = dc_field(default_factory=dict)

    # ---- records the facade reads into and writes from -------------------
    purch: WsPurchRecord = dc_field(default_factory=WsPurchRecord)
    otm5: OiHeader = dc_field(default_factory=_fresh_oi_header)
    batch: GlBatchRecord = dc_field(default_factory=GlBatchRecord)
    value: WsValueRecord = dc_field(default_factory=WsValueRecord)
    posting: WsPostingRecord = dc_field(default_factory=WsPostingRecord)
    irs_posting: WsIrsPostingRecord = dc_field(default_factory=WsIrsPostingRecord)

    # ---- copy "wsfnctn.cob" [L129] and "Test-Data-Flags.cob" [L210] ------
    file_access: FileAccess = dc_field(default_factory=FileAccess)
    dal_common: AcasDalCommonData = dc_field(default_factory=AcasDalCommonData)

    # ---- copy "wsmaps03.cob" [L128] - the date-module linkage block ------
    maps03_ws: Maps03Ws = dc_field(default_factory=Maps03Ws)
    # 01  ws-Test-Date pic x(10). [L178] / 01 ws-date-formats. [L179-L201]
    date_formats: dates.WsDateFormats = dc_field(default_factory=dates.WsDateFormats)

    # ---- 01  ws-data.  [purchase/pl100.cbl:L155-L176] --------------------
    ws_reply: str = " "  # 03 ws-reply     pic x   value space      [L156]
    wx_reply: str = "   "  # 03 wx-reply   pic xxx value spaces     [L157]
    xx: int = 0  # 03 xx           pic 99  value zero               [L158]
    i: int = 0  # 03 i             pic 99  value zero               [L159]
    j: int = 0  # 03 j             pic 99  value zero               [L160]
    k: int = 0  # 03 k             pic 999 value zero               [L161]
    m: str = " " * 8  # 03 m       pic z(7)9                        [L162]
    b: int = 0  # 03 b             binary-char value zero           [L163]
    c: int = 0  # 03 c             binary-char value zero           [L164]
    save_level_1: int = 0  # 03 save-level-1 pic 9 value zero       [L165]
    line_cnt: int = 0  # 03 line-cnt binary-char value zero         [L166]
    n_deduct: int = 0  # 03 n-deduct binary-long value zero         [L167]
    t_paid: Decimal = Decimal("0.00")  # 03 t-paid   s9(7)v99 c-3   [L168]
    t_approp: Decimal = Decimal("0.00")  # 03 t-approp              [L169]
    t_deduct: Decimal = Decimal("0.00")  # 03 t-deduct              [L170]
    j_paid: Decimal = Decimal("0.00")  # 03 j-paid                  [L171]
    j_approp: Decimal = Decimal("0.00")  # 03 j-approp              [L172]
    j_deduct: Decimal = Decimal("0.00")  # 03 j-deduct              [L173]
    work_1: Decimal = Decimal("0.00")  # 03 work-1 s9(7)v99 comp-3  [L174]
    work_a: int = 0  # 03 work-a   binary-long value zero           [L175]
    work_b: int = 0  # 03 work-b   binary-long value zero           [L176]
    # 77  exception-msg  pic x(25)  value spaces.                   [L126]
    exception_msg: str = " " * 25

    # ---- the print-file surrogate ----------------------------------------
    # The print file itself is omitted (see OMISSIONS), but `l5-name` is read
    # back into `post-legend`'s neighbour at [L434]/[L440] and `line-cnt`/`j`
    # are load-bearing because [L422] tests one and [L471] increments the
    # other.  Only the fields with a downstream consumer are modelled.
    l5_name: str = " " * 25

    # ------------------------------------------------------------------
    # Facade contexts - one per entity, because `FacadeContext` binds the
    # record it operates on.  `Proc-ACAS-FH-Calls.cob` reaches each entity's
    # record through its own `01` item in exactly the same way.
    # ------------------------------------------------------------------
    def ctx(self, record: object) -> facade.FacadeContext:
        """Build the facade context for one entity's record.

        Mirrors the handler `CALL` argument list of
        `[copybooks/Proc-ACAS-FH-Calls.cob:L51-L57]` -
        ``call "acas0NN" using System-Record <entity-record> File-Access
        File-Defs ACAS-DAL-Common-Data`` - with the parameter order preserved.
        """
        return facade.FacadeContext(
            system=self.system_record,
            record=record,
            file_access=self.file_access,
            file_defs=self.file_defs,
            dal_common=self.dal_common,
            # Sixth operand, no COBOL counterpart and no accounting value: the
            # caller's keyword-only declarations, transport policy among them.
            # Attached to EVERY context so the policy does not depend on which
            # entity a verb happens to touch.
            options=self.dal_options,
        )

    # ------------------------------------------------------------------
    # Named accessors for the linkage fields the program touches.  These
    # exist so that the nested block paths appear once each rather than at
    # every reference, and so that a reader can find every SYSTEM-REC
    # interaction by searching this block.
    # ------------------------------------------------------------------
    @property
    def _sys(self) -> object:
        return self.system_record.system_data_block

    @property
    def _gl(self) -> object:
        return self.system_record.general_ledger_block

    @property
    def _pl(self) -> object:
        return self.system_record.purchase_ledger_block


def _is_g_l(state: _Pl100State) -> bool:
    """``88  G-L  value 1.``  on ``07 Level-1 pic 9``  [copybooks/wssystem.cob:L85].

    `cobol.condition_names` publishes no `is_g_l` shorthand and `'G-L'` is
    absent from its `PREDICATES` mapping, so the registry is consulted by
    COBOL name.  `'G-L'` is not in `DUPLICATED_COBOL_NAMES`, so the lookup is
    unambiguous.  Tested at `[L316]`, `[L409]`, `[L454]`, `[L647]`, `[L671]`
    and `[L676]`; note that `[L454]` spells it lower-case `g-l`, which COBOL
    treats identically and which is recorded as a FINDING.
    """
    return condition_names.evaluate("G-L", state._sys.level.level_1)


def _is_irs_used(state: _Pl100State) -> bool:
    """``88  IRS-Used  value "Y".``  [copybooks/wssystem.cob:L180]."""
    return condition_names.is_irs_used(state._gl.irs_instead)


def _is_irs_both_used(state: _Pl100State) -> bool:
    """``88  IRS-Both-Used  value "B".``  [copybooks/wssystem.cob:L181]."""
    return condition_names.is_irs_both_used(state._gl.irs_instead)


def _oi_supplier_image(state: _Pl100State) -> str:
    """The seven-byte image of ``03 OI-Supplier`` - a GROUP item.

    A COBOL group MOVE copies a byte image, and a group's image is the
    concatenation of its subordinates' images.  `OI-Supplier` is
    ``09 OI-Nos pic x(6)`` plus ``09 OI-Check pic 9``
    [copybooks/plwsoi.cob], and `records.value_analysis.VaCode` records the
    record layer's deliberate policy that no method assembles a key, so the
    assembly belongs here in the program.

    `cobol.move`'s `STRING` operand form ``(value, delimiter, descriptor)`` is
    documented as the path for obtaining a numeric item's byte image from its
    picture, so it is used purely as that image-assembly primitive.  The COBOL
    statement being reproduced is the group `MOVE` at `[L352]`, not a `STRING`;
    no byte formatting is hand-rolled in this module.
    """
    supplier = state.otm5.oi_key.oi_customer.oi_supplier
    image, _pointer = movelib.string_into(
        " " * (_D_OI_NOS.byte_length + _D_OI_CHECK.byte_length),
        [
            (supplier.oi_nos, movelib.Delimiter.SIZE, _D_OI_NOS),
            (supplier.oi_check, movelib.Delimiter.SIZE, _D_OI_CHECK),
        ],
        pointer=1,
        delimited_by=movelib.Delimiter.SIZE,
    )
    return image


# ==========================================================================
# init01 SECTION  [purchase/pl100.cbl:L272-L508]
# ==========================================================================
# One very large section carrying TEN labels, three of which - `headings`,
# `compute-purch-pay` and `csp-exit` - are reached only by `PERFORM`.  Plan
# section 0.4.2 lists this program's section heads and OMITS every paragraph;
# the inventory reproduced here is measured from the source and is the one the
# traceability footer is built from.
#
# FALL-THROUGH IS MODELLED AS A TAIL CALL.  Where one paragraph runs into the
# next - `[L294]` into `menu-return` and `[L347]` into `cust-update` - the
# predecessor's LAST act is to call the successor, with nothing after it.  A
# Class 3 `return` therefore unwinds the whole chain back to `run()` exactly as
# `exit program.` `[L468]` unwinds the COBOL activation, and no caller resumes
# work that COBOL would not have resumed.


def _init01(state: _Pl100State) -> None:
    """``init01 section.``  [purchase/pl100.cbl:L272-L294] - entry and the latch gate.

    The one-shot proof latch is the whole of the business content here.
    `P-Flag-P` is a `SYSTEM-REC` column, so the refusal survives across runs::

        289      if       p-flag-p not = 2
        290               display PL137   at 2301
        291               display PL002   at 2401
        292               accept ws-reply at 2433
        293               go to menu-exit
        294      end-if.

    and `[L465]` clears it back to zero at the end of a successful run, so a
    second immediate run is refused too.  `sl100` has the same latch on
    `S-Flag-P` [sales/sl100.cbl:L296-L301] and [sales/sl100.cbl:L474], but
    `pl100`'s DISPLAYS AND ACCEPTS BEFORE RETURNING where `sl100`'s does not.
    The latch and its clearing are reproduced.  `PL137` [L290] becomes a log
    record because it is the diagnostic; `PL002` [L291] and the acknowledgement
    `accept` [L292] are dropped together, the literal being nothing but the
    instruction to press that key; and the `go to menu-exit` control transfer at
    [L293] is preserved.
    """
    # [L273-L274]  move prog-name to l1-name.  move Print-Spool-Name to PSN.
    # OMITTED - both receivers are print-file layout items.  `prog-name` is
    # retained as `_PROG_NAME` for the log banner at [L298].
    # [L276-L277]  set ENVIRONMENT "COB_SCREEN_EXCEPTIONS"/"COB_SCREEN_ESC".
    # OMITTED - curses key handling for a screen this migration removes.
    # [L282-L283]  the commented-out GL-bypass that saves and zeroes Level-1;
    # its restore at [L460] is commented out too.  `save-level-1` [L165] is
    # therefore declared and never assigned; see FINDINGS.

    # [L286]  perform zz070-Convert-Date.
    _zz070_convert_date(state)
    # [L287]  move ws-date to l2-date.  OMITTED - print layout item.

    # [L289]  if p-flag-p not = 2
    if arithmetic.compare(state._pl.p_flag_p, 2) != 0:
        # [L290]  display PL137 at 2301.  A DIAGNOSTIC with no database effect
        # becomes a log record (plan section 0.3.4).  THE RECORD IS THE LITERAL
        # AND NOTHING ELSE:
        #   * [L291] `display PL002` and [L292] `accept ws-reply` are DROPPED
        #     together.  "PL002 Note error and hit return" is nothing but the
        #     instruction to press the key the `accept` reads, so there is no
        #     substantive half to keep and a headless run has no operator to
        #     instruct.
        #   * `P-Flag-P` ITSELF IS NOT LOGGED.  The frozen display shows the
        #     literal alone; the flag's value is a SYSTEM-REC host-variable
        #     value, which the safe-event schema in `acas_posting/dal/status.py`
        #     excludes from a record (CWE-532), and narrating it would also state
        #     more than the compiled program does.
        # The TRANSFER below is not dropped.
        _LOG.warning("%s: %s", _PROG_NAME, _PL137)
        # [L293]  go to menu-exit.        # GO TO class 3 -> menu-exit [L467]
        _init01__menu_exit(state)
        return
    # [L294]  end-if.
    # FALL-THROUGH [L294] -> menu-return. [L296]
    _init01__menu_return(state)


def _init01__menu_return(state: _Pl100State) -> None:
    """``menu-return.``  [purchase/pl100.cbl:L296-L301] - the screen banner.

    Reached ONLY by fall-through from `[L294]`; nothing transfers to it.  Every
    statement in it is a `DISPLAY` except the date conversion at `[L300]`,
    which recomputes `ws-date` from `to-day` and is therefore kept: the same
    conversion already ran at `[L286]`, so this is a redundant recomputation
    that is reproduced rather than removed (plan section 0.8.4 - the
    repetitions an optimiser would delete stay).
    """
    # [L298-L299]  display prog-name / "Purchase Cash Posting".
    _LOG.info("%s: Purchase Cash Posting", _PROG_NAME)
    # [L300]  perform zz070-Convert-Date.
    _zz070_convert_date(state)
    # [L301]  display ws-date at 0171.
    # NO LOG COUNTERPART.  `ws-date` is the posting date this run stamps into the
    # records it writes - a date with business meaning, which the safe-event
    # schema in `acas_posting/dal/status.py` excludes (CWE-532).  It is an INPUT
    # the caller supplied through `to-day`, already known wherever the run was
    # started and pinned by `clock.py`.  The conversion above still runs: it is a
    # redundant recomputation that is reproduced, and it can default `Date-Form`
    # in the system record, which IS a table effect.
    # FALL-THROUGH [L301] -> acpt-xrply. [L302]
    _init01__acpt_xrply(state)


def _init01__acpt_xrply(state: _Pl100State) -> None:
    """``acpt-xrply.``  [purchase/pl100.cbl:L302-L321] - the run confirmation and the opens.

        302  acpt-xrply.
        303      display "OK to post payment transactions (YES/NO) ? <   > ..."
        305      move     spaces to wx-reply.
        306      accept   wx-reply at 1256 ... update.
        307      move     function upper-case (wx-reply) to wx-reply.
        308      if       wx-reply = "NO"
        309               go to menu-exit.
        310      if       wx-reply not = "YES"
        311               go to acpt-xrply.

    THIS PROMPT GATES A DATABASE WRITE.  Answering `"NO"` reaches `menu-exit`
    having opened no file and written nothing at all, so per plan section 0.3.4
    - "accept prompts that gate a database write become explicit CLI
    parameters with the COBOL default preserved" - the answer is the `run()`
    parameter `ok_to_post` rather than a dropped accept.

    THE CLASS 4 RE-ASK AT `[L311]`, AND ITS COLLAPSE.  `[L311]` transfers to
    `acpt-xrply` `[L302]`, a paragraph that performs work (a display and an
    accept) and then itself transfers control, which is what makes it Class 4
    rather than a bare Class 1 loop-back.  Per-site proof of equivalence: the
    target is the head of the paragraph the transfer is issued from, the
    paragraph has no entry side effects beyond the display and the accept, and
    every statement between the target and the transfer is re-executed on
    re-entry - so re-executing the body and re-testing is exactly equivalent.
    With the accept replaced by a boolean parameter the derived reply is one of
    the two literals the tests compare against, so the third branch is
    provably unreachable and the loop completes in a single pass.  THAT
    COLLAPSE IS A CONSEQUENCE OF REMOVING THE PRESENTATION LAYER, NOT A CHANGE
    OF BEHAVIOUR: no reply that the COBOL would have acted on is treated
    differently, and the transfer is still written so the site has a target.
    """
    while True:
        # [L303-L304]  display "OK to post payment transactions (YES/NO) ?".
        # NOT LOGGED.  It is the screen text for the `accept wx-reply` at [L306],
        # and plan section 0.3.4 resolves an `accept` that gates a database write
        # into "an explicit CLI parameter with the COBOL default preserved" -
        # which `ok_to_post` is.  The prompt is the dialogue around that
        # parameter, so emitting it as an operator diagnostic would log a question
        # no one can answer, and echoing the answer back would only restate a
        # command-line argument the caller already holds.
        # [L305]  move spaces to wx-reply.
        state.wx_reply = movelib.move_figurative(movelib.SPACE, _D_WX_REPLY)
        # [L306]  accept wx-reply at 1256 with foreground-color 6 update.
        # The accept becomes the `ok_to_post` parameter; the `update` phrase
        # pre-filled the field with the spaces just moved, which is neither
        # literal, so the COBOL re-asked until the operator typed one of them.
        state.wx_reply = movelib.move("YES" if state.ok_to_post else "NO", _D_WX_REPLY)
        # [L307]  move function upper-case (wx-reply) to wx-reply.
        # `FUNCTION UPPER-CASE` is a character intrinsic, not a picture or
        # arithmetic primitive, so `cobol/move.py` publishes no helper for it
        # and `str.upper()` is the faithful equivalent over the ASCII alphabet
        # this three-character reply field can hold.  The intrinsic is
        # IDEMPOTENT on a value derived from a boolean, both literals already
        # being upper case; it is applied anyway so the statement is
        # represented rather than silently dropped.
        state.wx_reply = movelib.move(state.wx_reply.upper(), _D_WX_REPLY)

        # [L308]  if wx-reply = "NO"
        if _alpha_eq(state.wx_reply, "NO", _D_WX_REPLY):
            # [L309]  go to menu-exit.    # GO TO class 3 -> menu-exit [L467]
            # ZERO database writes on this path: no file has been opened.
            _init01__menu_exit(state)
            return
        # [L310]  if wx-reply not = "YES"
        if not _alpha_eq(state.wx_reply, "YES", _D_WX_REPLY):
            # [L311]  go to acpt-xrply.   # GO TO class 4 -> acpt-xrply [L302]
            # Provably unreachable given `ok_to_post: bool`; see the per-site
            # proof in this function's docstring.
            continue
        break

    # [L313]  perform Purch-Open.        *> open i-o open-item-file-5 purchase-file
    facade.purch_open(state.ctx(state.purch))
    # [L314]  perform OTM5-Open.
    facade.otm5_open(state.ctx(state.otm5))

    # [L316]  if G-L
    if _is_g_l(state):
        # [L317]  perform BL-Open.
        _bl_open(state)
    # NOTE (FINDING F-17), and it is the outer frame A-NEW-5 sits inside:
    # `bl-open` runs ONLY under `G-L`, and so do `bl-write` [L409-L410] and
    # `bl-close` [L454-L455].  The three gates AGREE, so with `G-L` unset none
    # of the three runs and the IRS fan-out inside `bl-write` never executes at
    # all - the IRS switch is inert unless the General Ledger is also enabled,
    # even though `bl-write`'s own predicates [L629] and [L646-L647] name
    # `irs-used`/`IRS-Both-Used` as though they were sufficient.  The sibling
    # gates identically ([purchase/pl060.cbl:L405-L406],
    # [purchase/pl060.cbl:L474-L475], [purchase/pl060.cbl:L573-L574]), so this
    # is a family-wide property, not a pl100 divergence.  A-NEW-5 bites when
    # `G-L` IS set and the switch is "Y" or "B".  Not widened - R-3.

    # [L319]  open output print-file.  OMITTED - the print file (see OMISSIONS).
    # [L320]  move zero to j.
    state.j = movelib.move_figurative(movelib.ZERO, _D_J)
    # [L321]  perform headings.
    _init01__headings(state)

    # FALL-THROUGH [L321] -> loop. [L323]
    _init01__loop(state)


def _init01__loop(state: _Pl100State) -> None:
    """``loop.``  [purchase/pl100.cbl:L323-L347] - the OTM5 walk and its filter cascade.

    A purely SEQUENTIAL walk from the top of the file.  `pl100` performs no
    `OTM5-Start` and sets no `fn-*` function code directly, so there is no
    cursor positioning anywhere in the program.

    TWO ABBREVIATED RELATION CONDITIONS live here and both are easy to
    mis-expand:

        330      if       oi-type not = 2 and not = 5 and not = 6

    expands to a CONJUNCTION OF NEGATIONS - `oi-type not= 2` AND
    `oi-type not= 5` AND `oi-type not= 6` - and is written below in that shape,
    the shape COBOL evaluates, rather than as the logically equivalent negated
    disjunction.  And

        346      if       zero = oi-b-nos and oi-b-item

    is REVERSED: the subject is on the LEFT, so it expands to
    `zero = oi-b-nos` AND `zero = oi-b-item`.  Identical to
    [sales/sl100.cbl:L354].

    THE TYPE-2 BRANCH AT `[L333-L340]` HAS A REAL DATABASE EFFECT that never
    reaches the ledger: it runs the payment-days average, clears the three
    batch-linkage fields and rewrites `PUITM5-REC`, then continues.  `[L342-L343]`
    then excludes type 2 from `cust-update` altogether, so a type-2 row is
    never posted - only cleared.
    """
    while True:
        # [L324]  perform OTM5-Read-Next.  *> read open-item-file-5 next record
        facade.otm5_read_next(state.ctx(state.otm5))
        # [L325]  if fs-reply = 10
        if state.file_access.fs_reply == FsReply.END_OF_FILE:
            # [L326]  go to main-end.      # GO TO class 2 -> main-end [L427]
            break

        # [L328]  *> move open-item-record-5 to oi-header.  Commented out in
        # the frozen source because `OI-Header` REDEFINES the same bytes.

        # [L330]  if oi-type not = 2 and not = 5 and not = 6
        if (
            arithmetic.compare(state.otm5.oi_type, 2) != 0
            and arithmetic.compare(state.otm5.oi_type, 5) != 0
            and arithmetic.compare(state.otm5.oi_type, 6) != 0
        ):
            # [L331]  go to loop.          # GO TO class 1 -> loop [L323]
            continue

        # [L333-L335]  if oi-type = 2 and oi-b-nos not = zero
        #                                and oi-b-item not = zero
        if (
            arithmetic.compare(state.otm5.oi_type, 2) == 0
            and arithmetic.compare(state.otm5.oi_batch.oi_b_nos, 0) != 0
            and arithmetic.compare(state.otm5.oi_batch.oi_b_item, 0) != 0
        ):
            # [L336]  perform compute-purch-pay thru csp-exit.
            # PERFORM ... THRU - one of only FOUR in-scope sites in the whole
            # migration ([general/gl072.cbl:L300], [general/gl072.cbl:L304],
            # [sales/sl100.cbl:L344] and this one).  Plan section 0.4.2: "each
            # is transformed by hand into an explicit sequence of calls and
            # verified individually, with no pattern-matching shortcut."
            # The span L488..L508 covers exactly two labels, so the expansion
            # is those two calls in declaration order and nothing else.
            _init01__compute_purch_pay(state)
            _init01__csp_exit(state)
            # [L337]  move zeros to oi-b-nos oi-b-item oi-cr.
            (
                state.otm5.oi_batch.oi_b_nos,
                state.otm5.oi_batch.oi_b_item,
                state.otm5.oi_cr,
            ) = movelib.move_to_all(
                movelib.ZEROS, [_D_OI_B_NOS, _D_OI_B_ITEM, _D_OI_CR]
            )
            # [L338]  *> move oi-header to open-item-record-5.  Commented out.
            # [L339]  perform OTM5-Rewrite.
            facade.otm5_rewrite(state.ctx(state.otm5))
            # [L340]  go to loop.          # GO TO class 1 -> loop [L323]
            continue

        # [L342-L343]  if s-closed or oi-type = 2
        if (
            condition_names.is_s_closed_plwsoi(state.otm5.oi_status)
            or arithmetic.compare(state.otm5.oi_type, 2) == 0
        ):
            # [L344]  go to loop.          # GO TO class 1 -> loop [L323]
            continue

        # [L346]  if zero = oi-b-nos and oi-b-item
        if (
            arithmetic.compare(0, state.otm5.oi_batch.oi_b_nos) == 0
            and arithmetic.compare(0, state.otm5.oi_batch.oi_b_item) == 0
        ):
            # [L347]  go to loop.          # GO TO class 1 -> loop [L323]
            continue

        # FALL-THROUGH [L347] -> cust-update. [L349]
        _init01__cust_update(state)
        # [L425]  go       to loop.      # GO TO class 1 -> loop [L323]
        # Issued at the END of `cust-update`, which is a paragraph of THIS
        # section, so the transfer is executed here on its behalf.
        continue

    # THE CLASS 2 TARGET.  Plan section 0.6.3: the transformation is "`break`
    # PLUS faithful placement of that work after the loop, not `break` alone.
    # Mis-splitting here would silently drop end-of-run processing."  The work
    # at [L430-L465] is the two closes, the [L448] total merge, the ENTIRE
    # deduction reversal, `bl-close`, and TWO `SYSTEM-REC` writes - every one
    # of them a real database effect.
    _init01__main_end(state)


def _init01__cust_update(state: _Pl100State) -> None:
    """``cust-update.``  [purchase/pl100.cbl:L349-L425] - the purchase-ledger update.

    Reached ONLY by fall-through from `[L347]`; nothing transfers to it.
    """
    # [L352]  move oi-supplier to WS-Purch-Key l5-cust.  TWO receivers; the
    # second is a print field and is dropped, the first is the read key.
    (state.purch.ws_purch_key,) = movelib.move_to_all(
        _oi_supplier_image(state), [_D_PURCH_KEY]
    )

    # [L354]  move space to ws-reply.
    state.ws_reply = movelib.move_figurative(movelib.SPACE, _D_WS_REPLY)
    # [L355]  perform Purch-Read-Indexed.  *> read purchase-file invalid key
    facade.purch_read_indexed(state.ctx(state.purch))
    # [L356]  if fs-reply = 21
    # NOTE the test is `= 21` where the sibling tests `not = zero`
    # [purchase/pl060.cbl:L433] - recorded as a FINDING, not normalised.
    if state.file_access.fs_reply == FsReply.INVALID_KEY_ON_START:
        # [L357]  move "X" to ws-reply.
        state.ws_reply = movelib.move("X", _D_WS_REPLY)

    # ANOMALY A-NEW-6 [purchase/pl100.cbl:L356-L361] and [purchase/pl100.cbl:L405]
    # - an unknown supplier is NEVER CREATED.  On `fs-reply = 21` the program
    # sets a flag and writes "Supplier Unknown" into a PRINT field only; there
    # is no `move ... to purch-name`, no `initialize WS-Purch-Record` and no
    # `Purch-Write` anywhere in the program.  Yet `[L405] Purch-Rewrite` is
    # still issued UNCONDITIONALLY, so the arithmetic at [L379-L389] and the
    # date at [L392] are applied to whatever `WS-Purch-Record` last held - the
    # PREVIOUS supplier's row, or the initial image on the first iteration -
    # and rewritten under the key just set at [L352].  The maintainer knew:
    # "Yes for a non existant Purchase rec the rewrite will fail so ignore
    # error." [purchase/pl100.cbl:L407].  Contrast the sibling, which
    # initialises the record and writes it [purchase/pl060.cbl:L436-L440],
    # [purchase/pl060.cbl:L515-L519].
    # Reproduced deliberately per R-4; DO NOT FIX.
    #
    # AMBIGUITY Q-2: what row state does the rewrite of a never-read record
    # produce - does the handler reject it on the key, or does it overwrite the
    # named row with the previous supplier's field values?  The COBOL comment
    # asserts the rewrite "will fail", but that is the ISAM expectation and the
    # program runs against the RDB path.  THE ORACLE DECIDES (R-6); the DAL's
    # own status pair is reproduced as-is below and no exception is invented.
    # [L358-L361]  if ws-reply = "X" move "Supplier Unknown" to l5-name
    #              else move purch-name to l5-name.
    # Both receivers are `l5-name`, a print field.  It is retained ONLY because
    # `main-end` reuses the same item for its total lines; no database effect.
    if _alpha_eq(state.ws_reply, "X", _D_WS_REPLY):
        state.l5_name = movelib.move("Supplier Unknown", _D_PURCH_NAME)
    else:
        state.l5_name = movelib.move(
            state.purch.purch_name, _D_PURCH_NAME, sending_field=_D_PURCH_NAME
        )

    # [L363-L365]  oi-b-nos -> l5-batch, "/" -> l5-sl, oi-b-item -> l5-item.
    # OMITTED - print layout items with no database effect.

    # [L367]  move oi-date to u-bin.
    state.maps03_ws.u_bin = movelib.move(
        state.otm5.oi_date, _D_U_BIN, sending_field=_D_OI_DATE
    )
    # [L368]  perform zz060-Convert-Date.  Binary -> text, for the print line
    # AND for `bl-write`, which reads `u-date` at [L591-L592].
    _zz060_convert_date(state)
    # [L369]  move u-date to l5-date.  OMITTED - print item.  NOTE the source
    # field: `u-date`, where the sibling uses `ws-date`
    # [purchase/pl060.cbl:L448].  A FINDING, preserved by reading `u-date` in
    # `bl-write` below.

    # [L371-L373]  oi-approp/oi-paid/oi-deduct-amt -> l5-approp/l5-paid/
    # l5-deduct.  OMITTED - print layout items.

    # [L375]  if oi-deduct-amt not = zero
    if arithmetic.compare(state.otm5.oi_deduct_amt, 0) != 0:
        # [L376]  add 1 to n-deduct.  A COUNT, and load-bearing: it is what
        # `analise-deductions` subtracts from the `va-t-*` count fields.
        state.n_deduct = arithmetic.add_to(
            1, receiver_value=state.n_deduct, receiving=_D_N_DEDUCT
        )

    # [L378]  subtract purch-unapplied from purch-current giving l5-old-bal.
    # OMITTED - the receiver is a print field and the `GIVING` form mutates
    # neither operand, so the statement has no observable effect at all.

    # [L379]  subtract oi-approp from purch-current.
    # [L380]  subtract oi-deduct-amt from purch-current.
    # TWO separate single-receiver subtracts with no `GIVING`, so each mutates
    # `purch-current` IN PLACE, sequentially.  Not folded into one statement:
    # each store truncates independently into `s9(8)v99 comp-3`.
    state.purch.purch_current = arithmetic.subtract_from(
        state.otm5.filler_1.oi_approp,
        receiver_value=state.purch.purch_current,
        receiving=_D_PURCH_CURRENT,
    )
    state.purch.purch_current = arithmetic.subtract_from(
        state.otm5.oi_deduct_amt,
        receiver_value=state.purch.purch_current,
        receiving=_D_PURCH_CURRENT,
    )

    # [L382]  if oi-paid not = oi-approp
    if arithmetic.compare(state.otm5.filler_1.oi_paid, state.otm5.filler_1.oi_approp) != 0:
        # [L383]  subtract oi-approp from oi-paid giving work-1.
        # `work-1` is MONEY - `s9(7)v99 comp-3` [L174].  Not `work-a`.
        state.work_1 = arithmetic.subtract_giving(
            state.otm5.filler_1.oi_approp,
            minuend=state.otm5.filler_1.oi_paid,
            receiving=_D_WORK_1,
        )
        # [L384]  add work-1 to purch-unapplied.
        state.purch.purch_unapplied = arithmetic.add_to(
            state.work_1,
            receiver_value=state.purch.purch_unapplied,
            receiving=_D_PURCH_UNAPPLIED,
        )

    # [L386]  if purch-current is negative
    if arithmetic.compare(state.purch.purch_current, 0) < 0:
        # [L387]  multiply -1 by purch-current giving work-1.
        # THE `GIVING` FORM, so `purch-current` is NOT mutated by the multiply;
        # the POSITIVE product lands in `work-1` and `purch-current` is zeroed
        # separately at [L389].  The sibling uses the no-`GIVING` form
        # [purchase/pl060.cbl:L507], which DOES mutate its operand before
        # adding it.  The net effect is the same, the intermediate is not, and
        # each program keeps its own form.  [sales/sl100.cbl:L395] also uses
        # `GIVING`.
        state.work_1 = arithmetic.multiply_by_giving(-1, state.purch.purch_current, _D_WORK_1)
        # [L388]  add work-1 to purch-unapplied.
        state.purch.purch_unapplied = arithmetic.add_to(
            state.work_1,
            receiver_value=state.purch.purch_unapplied,
            receiving=_D_PURCH_UNAPPLIED,
        )
        # [L389]  move zero to purch-current.
        state.purch.purch_current = movelib.move_figurative(
            movelib.ZERO, _D_PURCH_CURRENT
        )

    # [L391]  subtract purch-unapplied from purch-current giving l5-new-bal.
    # OMITTED - print field, `GIVING` form, no observable effect.

    # [L392]  move oi-date to purch-last-pay.  A REAL ledger effect.
    state.purch.purch_last_pay = movelib.move(
        state.otm5.oi_date, _D_PURCH_LAST_PAY, sending_field=_D_OI_DATE
    )

    # [L394]  if oi-type = 5
    if arithmetic.compare(state.otm5.oi_type, 5) == 0:
        # [L395]  add oi-approp to t-approp.
        state.t_approp = arithmetic.add_to(
            state.otm5.filler_1.oi_approp,
            receiver_value=state.t_approp,
            receiving=_D_T_APPROP,
        )
        # [L396]  add oi-paid to t-paid pl-payments.
        # PERIOD TOTAL 9 OF 9, and a TWO-RECEIVER `ADD ... TO`.  `t-paid` is a
        # local print total; `pl-payments` is a `SYSTOT-REC` column on
        # `system_record_4`, and plan section 0.6.4 calls the nine sites "the
        # sole writers" of that table.  Exactly mirrors
        # [sales/sl100.cbl:L404] `add oi-paid to t-paid sl-payments`.
        # Each receiver takes its own store, and BOTH read the ORIGINAL
        # `oi-paid` - which is why the overwrite at [L404] must come after.
        # `pl-payments` accrues ONLY for `oi-type = 5`, NEVER for type 6.
        _oi_paid_at_l396 = state.otm5.filler_1.oi_paid
        state.t_paid = arithmetic.add_to(
            _oi_paid_at_l396, receiver_value=state.t_paid, receiving=_D_T_PAID
        )
        state.system_record_4.purchase_ledger_data.pl_payments = arithmetic.add_to(
            _oi_paid_at_l396,
            receiver_value=state.system_record_4.purchase_ledger_data.pl_payments,
            receiving=_D_PL_PAYMENTS,
        )
        # [L397]  add oi-deduct-amt to t-deduct.  Gates the reversal at [L449].
        state.t_deduct = arithmetic.add_to(
            state.otm5.oi_deduct_amt,
            receiver_value=state.t_deduct,
            receiving=_D_T_DEDUCT,
        )
    # [L398]  else
    else:
        # [L399]  if oi-type = 6
        if arithmetic.compare(state.otm5.oi_type, 6) == 0:
            # [L400-L402]  the journal totals.  All three are PRINT-ONLY and
            # reach no table - except `j-deduct`, which [L448] merges into
            # `t-deduct` before the reversal.
            state.j_approp = arithmetic.add_to(
                state.otm5.filler_1.oi_approp,
                receiver_value=state.j_approp,
                receiving=_D_J_APPROP,
            )
            state.j_paid = arithmetic.add_to(
                state.otm5.filler_1.oi_paid,
                receiver_value=state.j_paid,
                receiving=_D_J_PAID,
            )
            state.j_deduct = arithmetic.add_to(
                state.otm5.oi_deduct_amt,
                receiver_value=state.j_deduct,
                receiving=_D_J_DEDUCT,
            )

    # [L404]  move oi-approp to oi-paid.
    # THE ORDERING TRAP.  This OVERWRITES `oi-paid` AFTER [L396] and [L401]
    # have consumed it, so the period total and the journal total both carry
    # the ORIGINAL amount while the `PUITM5-REC` row stores `oi-approp`.
    # `bl-write` [L595] then reads the OVERWRITTEN value into `post-amount`.
    # Inverting these two statements changes the period total AND the stored
    # row AND every posting amount.  R-3: do not reorder.
    state.otm5.filler_1.oi_paid = movelib.move(
        state.otm5.filler_1.oi_approp, _D_OI_PAID, sending_field=_D_OI_APPROP
    )
    # [L405]  perform Purch-Rewrite.  *> rewrite purch-record.
    # UNCONDITIONAL - see ANOMALY A-NEW-6 above.
    facade.purch_rewrite(state.ctx(state.purch))

    # [L409]  if G-L
    if _is_g_l(state):
        # [L410]  perform BL-Write.
        _bl_write(state)
    # [L411]  move 1 to oi-status.  A REAL `PUITM5-REC` effect: the row is
    # marked closed.  `88 S-Closed value 1.` [copybooks/plwsoi.cob:L55],
    # reached through the `replacing` clause at [copybooks/plwsoi5C.cob:L19-L20].
    state.otm5.oi_status = movelib.move(1, _D_OI_STATUS)

    # [L413]  perform OTM5-Rewrite.  *> rewrite open-item-record-5 from oi-header
    facade.otm5_rewrite(state.ctx(state.otm5))

    # [L415-L419]  the "Cr Journal" / "Payment" label moves into `l5-type`.
    # OMITTED - print layout item.
    # [L420]  write print-record from line-5 after 1.  OMITTED - print file.

    # [L421]  add 1 to line-cnt.  RETAINED because [L422] tests it.
    state.line_cnt = arithmetic.add_to(
        1, receiver_value=state.line_cnt, receiving=_D_LINE_CNT
    )
    # [L422]  if line-cnt > Page-Lines
    if arithmetic.compare(state.line_cnt, state._sys.page_lines) > 0:
        # [L423]  perform headings.
        _init01__headings(state)

    # [L425]  go to loop.  The transfer is issued by the caller's loop; see
    # the annotation at the fall-through site in `_init01__loop`.
    return


def _init01__main_end(state: _Pl100State) -> None:
    """``main-end.``  [purchase/pl100.cbl:L427-L465] - closes, the reversal, two SYSTEM-REC writes.

    The Class 2 target of `[L326]`.  Every database effect here is
    diff-visible, so none of it may be dropped.
    """
    # [L430]  perform OTM5-Close.
    facade.otm5_close(state.ctx(state.otm5))
    # [L431]  perform Purch-Close.
    facade.purch_close(state.ctx(state.purch))

    # [L433-L444]  the two total print blocks.  OMITTED AND NOT LOGGED.  Every
    # statement in both is a `move` into the print line followed by `write
    # print-record`; the frozen program DISPLAYS none of it.  Report formatting
    # beyond database effects is out of scope (plan section 0.2.2), and section
    # 0.3.4 converts a DISPLAY, not a report line.  The six operands are
    # MONETARY TOTALS besides, which the safe-event schema in
    # `acas_posting/dal/status.py` excludes from a record at any level (CWE-532).
    # The accumulators themselves are untouched: they are real, and the ones that
    # matter reach SYSTOT-REC, which is where the audit trail lives.
    # [L445]  close print-file.  OMITTED - the print file.
    # [L446]  call "SYSTEM" using Print-Report.  OMITTED - plan section 0.1.1
    # excludes "the `call "SYSTEM" using Print-Report` spool-out path" by name.
    # It is the only non-migratable call in the whole program (R-1).

    # [L448]  add j-deduct to t-deduct.
    # THE MERGE, and it is LOAD-BEARING: the journal deductions join the
    # payment deduction total BEFORE the gate below sees it, so moving this
    # after [L449] would change which reversals happen at all.  R-3.
    state.t_deduct = arithmetic.add_to(
        state.j_deduct, receiver_value=state.t_deduct, receiving=_D_T_DEDUCT
    )
    # [L449]  if t-deduct not = zero
    #
    # ANOMALY A-NEW-7 [purchase/pl100.cbl:L449] - the ENTIRE value-analysis
    # reversal is gated on `t-deduct` ALONE.  `n-deduct`, the deduction COUNT
    # that [L519-L520] and [L533-L534] subtract from `va-t-this`/`va-t-year`,
    # is NOT in the gate.  So a batch whose deduction VALUES net to zero while
    # its deduction COUNT is non-zero - equal and opposite deductions across a
    # payment and a credit journal, which [L448] has just merged into one
    # total - skips the reversal entirely and leaves the count fields
    # permanently overstated.  Reproduced deliberately per R-4; DO NOT FIX.
    #
    # AMBIGUITY Q-3: how far do the `VALUEANAL-REC` counts drift, and what
    # does the UNSIGNED `va-t-this`/`va-t-year` (`pic 9(5) comp`) store when a
    # subtraction would take them below zero?  Both the drift and the unsigned
    # underflow are measured against the compiled program, not reasoned about
    # (R-6).
    if arithmetic.compare(state.t_deduct, 0) != 0:
        # [L450]  perform Value-Open.     *> open i-o value-file
        facade.value_open(state.ctx(state.value))
        # [L451]  perform analise-deductions.
        _analise_deductions(state)
        # [L452]  perform Value-Close.    *> close value-file
        facade.value_close(state.ctx(state.value))

    # [L454]  if g-l
    # Spelled lower case here and upper case at [L316]/[L409]; COBOL is
    # case-insensitive, and the inconsistency is recorded as a FINDING.
    if _is_g_l(state):
        # [L455]  perform bl-close.
        _bl_close(state)

    # [L460]  *> move save-level-1 to level-1.  The commented-out restore of
    # the commented-out GL bypass at [L282-L283]; neither is reproduced,
    # because neither executes.

    # [L464]  move "Y" to oi-5-flag.  A REAL `SYSTEM-REC` write - it signals
    # the downstream `pl115` sort requirement.  Note where the field lives:
    # `OI-5-Flag` is declared in the SALES ledger block of the system record,
    # not the purchase block, even though only purchase programs set it.
    state.system_record.sales_ledger_block.oi_5_flag = movelib.move(
        "Y", _D_OI_5_FLAG
    )
    # [L465]  move zero to P-Flag-P.  A REAL `SYSTEM-REC` write - it clears
    # the one-shot latch that [L289] tests, so a second immediate run is
    # refused.
    state.system_record.purchase_ledger_block.p_flag_p = movelib.move_figurative(
        movelib.ZERO, _D_P_FLAG_P
    )
    # BOTH writes happen AFTER `bl-close`, so they happen even when the batch
    # write inside it failed - [L664-L670] reports the failure and transfers
    # nowhere.

    # FALL-THROUGH [L465] -> menu-exit. [L467]
    _init01__menu_exit(state)


def _init01__menu_exit(state: _Pl100State) -> None:
    """``menu-exit.``  [purchase/pl100.cbl:L467-L468].

        467  menu-exit.
        468      exit     program.

    `exit program.` and NOT `goback.` - a FINDING, since `gl071` and others in
    the family end with `goback`.  Both return control to the caller here
    because `pl100` is only ever `CALL`ed [purchase/purchase.cbl:L696], never
    run as a main program, so the two are equivalent at this site and the
    spelling is recorded rather than normalised.

    Reached by the two Class 3 transfers at `[L293]` and `[L309]` and by
    fall-through from `[L465]`.  In every case the predecessor's last act is
    the call to this function, so returning unwinds to `run()`.
    """
    # NO LOG RECORD.  `menu-exit.` [L467-L468] displays NOTHING - `exit program.`
    # is its only statement - so an "exit program" event would be output the
    # compiled program never produced, which R-4 forbids inventing, and
    # `WS-Term-Code` is a linkage field the caller reads directly.  `state` stays
    # in the signature so every paragraph function in this module has the same
    # shape (R-5) and the three transfer sites pass it as written.
    del state
    return


def _init01__headings(state: _Pl100State) -> None:
    """``headings.``  [purchase/pl100.cbl:L470-L486] - PERFORM-only, and still load-bearing.

    Every `WRITE` in it is omitted with the print file, but the paragraph MUST
    exist (R-5) and TWO of its statements must execute: `[L471]` advances the
    page counter and `[L486]` resets the line counter that `[L422]` tests.
    Dropping either would change how often this paragraph runs, which is
    observable in nothing - but the counters are cheap and the requirement to
    represent every paragraph is not negotiable.
    """
    # [L471]  add 1 to j.
    state.j = arithmetic.add_to(1, receiver_value=state.j, receiving=_D_J)
    # [L472]  move j to l1-page.       OMITTED - print layout item.
    # [L473]  move usera to l2-user.   OMITTED - print layout item.
    # [L475-L485]  the six `write print-record` statements and the page/before
    # /after phrases.  OMITTED - the print file (see OMISSIONS) - AND NOT LOGGED:
    # a page number and a column ruler are report formatting, out of scope per
    # plan section 0.2.2, and this paragraph contains no `display` at all.  The
    # counter statements above and below stay, because [L422] tests the line
    # budget this paragraph resets.
    # [L486]  move 5 to line-cnt.
    state.line_cnt = movelib.move(5, _D_LINE_CNT)


def _init01__compute_purch_pay(state: _Pl100State) -> None:
    """``compute-purch-pay.``  [purchase/pl100.cbl:L488-L505] - A-10 VARIANT (d) OF FOUR.

    A PARAGRAPH inside `init01`, not a section, and the first half of the
    `PERFORM ... THRU` span at `[L336]`.

    ANOMALY A-10 [purchase/pl100.cbl:L495], [purchase/pl100.cbl:L497],
    [purchase/pl100.cbl:L500-L502] - the fourth mutually inconsistent spelling
    of one moving-average idiom.  `move zero to work-b` is UNCONDITIONAL and
    PRECEDES the guard, so there is no `ELSE`; the guard is ONE condition
    where [purchase/pl060.cbl:L743-L744] and [purchase/pl060.cbl:L758-L759]
    use a two-condition `AND`; the activity counter is incremented AFTER the
    accumulate where [purchase/pl060.cbl:L749-L750] increments before; the
    divide is the `BY` form where `pl060` uses `INTO`, which divides the other
    way round; and a worst-case watermark is maintained that `pl060` has no
    equivalent of.  [sales/sl100.cbl:L506] is variant (c) and differs again.
    Reproduced deliberately per R-4; DO NOT FIX - and NOT factored into a
    shared helper with any of the other three.

    ANOMALY A-8 DOES NOT APPLY HERE.  A-8 is a DOUBLE truncation, and it needs
    a two-decimal value entering a zero-scale accumulator.  `work-a` and
    `work-b` are both `binary-long` [purchase/pl100.cbl:L175-L176], and
    `work-a` is a DAY COUNT - the difference of two binary day numbers
    `[L494]`.  There is exactly ONE truncation in this paragraph, the integer
    divide at `[L502]`, and no money field is involved at any point.
    """
    # [L491]  if oi-date-cleared = zero
    if arithmetic.compare(state.otm5.oi_date_cleared, 0) == 0:
        # [L492]  go to csp-exit.        # GO TO class 3 -> csp-exit [L507]
        return

    # [L494]  subtract oi-date from oi-date-cleared giving work-a.
    # An INTEGER DAY COUNT: both operands are `binary-long` day numbers.
    state.work_a = arithmetic.subtract_giving(
        state.otm5.oi_date,
        minuend=state.otm5.oi_date_cleared,
        receiving=_D_WORK_A,
    )
    # ------------------------------------------------------------------
    # ANOMALY A-10 [purchase/pl100.cbl:L495], [purchase/pl100.cbl:L497],
    # [purchase/pl100.cbl:L500-L502] - VARIANT (d) of four mutually
    # inconsistent moving-average idioms, differing from
    # [purchase/pl060.cbl:L743-L751] (a) and [purchase/pl060.cbl:L758-L766] (b)
    # in FIVE ways and from [sales/sl100.cbl:L497-L516] (c) in the guard:
    #   1. `move zero to work-b` [L495] is UNCONDITIONAL and PRECEDES the
    #      guard, so there is no `ELSE` - a stale average is always discarded;
    #   2. the guard [L497] is ONE condition, where pl060's is a two-condition
    #      AND ([purchase/pl060.cbl:L743-L744], [L758-L759]);
    #   3. the counter is incremented AFTER the accumulate ([L500] then
    #      [L501]), where pl060's `purch-comp` increments BEFORE
    #      ([purchase/pl060.cbl:L749-L750]);
    #   4. the divide is the `BY` form [L502] - average = work-b / activety -
    #      where pl060 uses `INTO`, which reverses the operands;
    #   5. it maintains a worst-case watermark [L504-L505] that pl060 has no
    #      equivalent of.
    # The four variants are FOUR separate functions in FOUR separate modules
    # with no shared helper, because plan section 0.6.1 says normalising them
    # "would be the single easiest way to fail this migration".
    # Reproduced deliberately per R-4; DO NOT FIX.
    # ------------------------------------------------------------------
    # [L495]  move zero to work-b.  UNCONDITIONAL, and it PRECEDES the guard.
    state.work_b = movelib.move_figurative(movelib.ZERO, _D_WORK_B)

    # [L497]  if purch-pay-activety not = zero      ONE condition, no `ELSE`.
    if arithmetic.compare(state.purch.purch_pay_activety, 0) != 0:
        # [L498]  multiply purch-pay-activety by purch-pay-average
        #                                                 giving work-b.
        state.work_b = arithmetic.multiply_by_giving(
            state.purch.purch_pay_activety,
            state.purch.purch_pay_average,
            _D_WORK_B,
        )

    # [L500]  add work-a to work-b.
    state.work_b = arithmetic.add_to(
        state.work_a, receiver_value=state.work_b, receiving=_D_WORK_B
    )
    # [L501]  add 1 to purch-pay-activety.   THE COUNTER, AFTER the accumulate.
    state.purch.purch_pay_activety = arithmetic.add_to(
        1,
        receiver_value=state.purch.purch_pay_activety,
        receiving=_D_PURCH_PAY_ACTIVETY,
    )
    # [L502]  divide work-b by purch-pay-activety giving purch-pay-average.
    # THE `BY` FORM: average = work-b / activety.  The receiver is
    # `binary-long`, so the remainder is discarded - the single truncation of
    # this paragraph, and no `ROUNDED` phrase anywhere.
    state.purch.purch_pay_average = arithmetic.divide_by_giving(
        state.work_b, state.purch.purch_pay_activety, _D_PURCH_PAY_AVERAGE
    )
    #
    # AMBIGUITY Q-5: `Purch-Pay-Average` is declared SIGNED `binary-long`
    # [copybooks/wspl.cob:L41] while the bridge and the column narrow the
    # statistics family to unsigned (cf. [common/salesMT.cbl:L305-L312] for the
    # sales mirror, registered as A-11).  What is STORED when the divide yields
    # a negative average - which it can, because `[L494]` subtracts without
    # ordering its operands - is decided by the bridge's C interface and is
    # measured against the compiled oracle, not assumed (R-6).

    # [L504]  if work-a > purch-pay-worst
    if arithmetic.compare(state.work_a, state.purch.purch_pay_worst) > 0:
        # [L505]  move work-a to purch-pay-worst.  The watermark.
        state.purch.purch_pay_worst = movelib.move(
            state.work_a, _D_PURCH_PAY_WORST, sending_field=_D_WORK_A
        )


def _init01__csp_exit(state: _Pl100State) -> None:
    """``csp-exit.``  [purchase/pl100.cbl:L507-L508] - the second half of the THRU span.

        507  csp-exit.
        508      exit.

    A PLAIN `EXIT`, not `exit section.` and not `exit program.`  A bare `EXIT`
    is a documented NO-OP that exists only to give a paragraph a body, so this
    function has no statements - and it must still exist, both because R-5
    requires a function per paragraph and because it is the second label of the
    `PERFORM compute-purch-pay THRU csp-exit` span at `[L336]`, which really
    does execute it.
    """
    return


# ==========================================================================
# analise-deductions SECTION  [purchase/pl100.cbl:L510-L539]
# ==========================================================================


def _analise_deductions(state: _Pl100State) -> None:
    '''``analise-deductions section.``  [purchase/pl100.cbl:L510-L537] - the "Pzb" reversal.

    THE `pl055` -> `pl100` DEDUCTION CONTRACT, and it is invisible unless you
    look for it.  `[L513]` moves the literal `"Pzb"` into `va-code`, which
    distributes across the three subordinate items - `P` to `va-system`, `z` to
    `va-first`, `b` to `va-second`.  That key is the group `pl055` CREATES:
    [purchase/pl055.cbl:L403] moves `"P"` to `va-system` and
    [purchase/pl055.cbl:L416] moves `"zb"` to `va-group`, the
    discount/deduction special total.  `pl055` ADDS to it
    [purchase/pl055.cbl:L514-L517]; THIS SECTION SUBTRACTS from it.  Break
    either half and the value-analysis totals drift with no error reported
    anywhere.  The coupling runs through the `VALUEANAL-REC` table exactly as
    in COBOL, so nothing here imports `pl055`.

    TWO DIFFERENT ACCUMULATORS, FOUR SUBTRACTS, TWICE OVER.  `n-deduct` is a
    COUNT and reduces the `va-t-*` count fields; `t-deduct` is a VALUE and
    reduces the `va-v-*` value fields.  The block then runs a second time
    against the parent key, `va-second` having been blanked at `[L527]` so the
    key becomes `"Pz "`.  The same idiom appears at
    [purchase/pl055.cbl:L506-L534], and the two blocks here are NOT factored
    into one helper: the first carries an extra `File-Key-No` assignment the
    second does not, and the two `go to main-exit` sites are distinct.
    '''
    # [L513]  move "Pzb" to va-code.
    # A group MOVE distributes the literal across the group's subordinates.
    # `records.value_analysis.VaCode` states that "no method assembles the
    # three characters into a key", so the distribution is written here, using
    # 1-based reference modification on the literal - never Python slicing.
    _code = movelib.move_group("Pzb", _D_VA_CODE, length=3)
    state.value.va_code.va_system = movelib.move(
        movelib.ref_mod(_code, 1, 1), _D_VA_SYSTEM
    )
    state.value.va_code.va_group.va_first = movelib.move(
        movelib.ref_mod(_code, 2, 1), _D_VA_FIRST
    )
    state.value.va_code.va_group.va_second = movelib.move(
        movelib.ref_mod(_code, 3, 1), _D_VA_SECOND
    )

    # [L514]  move 1 to File-Key-No.
    # `dal.facade` sets the primary key number itself on every dispatch, so
    # this assignment is redundant - and plan section 0.8.4 puts performance
    # work "out of scope by construction", so it is reproduced, not elided.
    state.file_access.logging_data.file_key_no = movelib.move(1, _D_FILE_KEY_NO)
    # [L515]  perform Value-Read-Indexed.   *> read value-file invalid key
    facade.value_read_indexed(state.ctx(state.value))
    # [L516]  if FS-Reply = 21
    if state.file_access.fs_reply == FsReply.INVALID_KEY_ON_START:
        # [L517]  go to main-exit.       # GO TO class 3 -> main-exit [L539]
        _analise_deductions__main_exit(state)
        return

    # [L519-L522]  the four subtracts - COUNT from the count pair, VALUE from
    # the value pair.  Each is a single-receiver `SUBTRACT ... FROM`, so each
    # mutates its receiver in place.
    state.value.va_t_this = arithmetic.subtract_from(
        state.n_deduct, receiver_value=state.value.va_t_this, receiving=_D_VA_T_THIS
    )
    state.value.va_t_year = arithmetic.subtract_from(
        state.n_deduct, receiver_value=state.value.va_t_year, receiving=_D_VA_T_YEAR
    )
    state.value.va_v_this = arithmetic.subtract_from(
        state.t_deduct, receiver_value=state.value.va_v_this, receiving=_D_VA_V_THIS
    )
    state.value.va_v_year = arithmetic.subtract_from(
        state.t_deduct, receiver_value=state.value.va_v_year, receiving=_D_VA_V_YEAR
    )

    # [L524]  move 1 to File-Key-No.
    state.file_access.logging_data.file_key_no = movelib.move(1, _D_FILE_KEY_NO)
    # [L525]  perform Value-Rewrite.    *> rewrite value-record
    facade.value_rewrite(state.ctx(state.value))

    # [L527]  move space to va-second.  The key becomes "Pz " - the parent
    # group total, which `pl055` maintains alongside the specific one.
    state.value.va_code.va_group.va_second = movelib.move_figurative(
        movelib.SPACE, _D_VA_SECOND
    )
    # [L528]  move 1 to File-Key-No.
    state.file_access.logging_data.file_key_no = movelib.move(1, _D_FILE_KEY_NO)
    # [L529]  perform Value-Read-Indexed.  *> read value-file invalid key
    facade.value_read_indexed(state.ctx(state.value))
    # [L530]  if FS-Reply = 21
    if state.file_access.fs_reply == FsReply.INVALID_KEY_ON_START:
        # [L531]  go to main-exit.       # GO TO class 3 -> main-exit [L539]
        _analise_deductions__main_exit(state)
        return

    # [L533-L536]  the same four subtracts against the parent-group row.
    state.value.va_t_this = arithmetic.subtract_from(
        state.n_deduct, receiver_value=state.value.va_t_this, receiving=_D_VA_T_THIS
    )
    state.value.va_t_year = arithmetic.subtract_from(
        state.n_deduct, receiver_value=state.value.va_t_year, receiving=_D_VA_T_YEAR
    )
    state.value.va_v_this = arithmetic.subtract_from(
        state.t_deduct, receiver_value=state.value.va_v_this, receiving=_D_VA_V_THIS
    )
    state.value.va_v_year = arithmetic.subtract_from(
        state.t_deduct, receiver_value=state.value.va_v_year, receiving=_D_VA_V_YEAR
    )
    # [L537]  perform Value-Rewrite.    *> rewrite value-record
    # FINDING - THE ASYMMETRY: there is NO `move 1 to File-Key-No` before this
    # second rewrite, where [L524] precedes the first.  Reproduced exactly;
    # R-3 forbids adding the missing assignment.
    facade.value_rewrite(state.ctx(state.value))

    # FALL-THROUGH [L537] -> main-exit. [L539]
    _analise_deductions__main_exit(state)


def _analise_deductions__main_exit(state: _Pl100State) -> None:
    """``main-exit.   exit section.``  [purchase/pl100.cbl:L539].

    The FIRST of FIVE paragraphs in this program named `main-exit` - the others
    are at L574, L657, L679 and L687.  Paragraph names are not globally unique
    in this codebase, which is why every function name here is
    section-qualified.
    """
    return


# ==========================================================================
# bl-open SECTION  [purchase/pl100.cbl:L541-L574]
# ==========================================================================
# Declared LOWER CASE - `bl-open      section.` - yet performed as `BL-Open`
# at [L317] and as `bl-open` at [L655].  COBOL is case-insensitive; the
# inconsistency is recorded as a FINDING.


#: ``05 WS-Batch-Nos pic 9(5)`` [copybooks/wsbatch.cob:L19] - the scale at which
#: ``WS-Ledger`` [:L15] contributes to the six digits ``WS-Batch-Key9`` reads.
_BATCH_NOS_SCALE: Final[int] = 10**5


def _restate_ws_batch_key9(batch: GlBatchRecord) -> None:
    """Keep ``WS-Batch-Key9`` in step with the two members it redefines.

    ⭐⭐ ONE STORAGE, TWO READINGS. ``03 WS-Batch-Key.`` holds ``05 WS-Ledger
    pic 9.`` and ``05 WS-Batch-Nos pic 9(5).``, and ``03 WS-Batch-Key9 redefines
    WS-Batch-Key pic 9(6).`` [copybooks/wsbatch.cob:L14-L21] is those SAME six
    bytes read as one number. ``move bl-next-batch to WS-Batch-Nos``
    [purchase/pl100.cbl:L546] and ``move 2 to WS-Ledger`` [:L547] therefore change
    what ``WS-Batch-Key9`` reads, instantly - in COBOL there is nothing to keep in
    step because there is only one storage. Python has no aliasing, so restating it
    is a MODELLING obligation, not a new rule. (Note this program allocates from
    ``BL-Next-Batch`` rather than ``Next-Batch``, the FINDING recorded at the move
    site; the redefinition behaves the same either way.)

    THE ROLLOVER IS WHY THIS IS REACHED TWICE. ``if items = 99 / perform bl-close /
    perform bl-open`` [purchase/pl100.cbl:L653] closes the full batch and opens the
    next, so a hundredth item returns here with a key already in working storage.
    Without the restatement the grouped reading held the NEW batch while the
    redefined reading still held the PREVIOUS one, and ``acas007``'s
    ``synchronise_batch_key_views`` - which deliberately refuses to pick between two
    non-default disagreeing readings, because ``bb000-HV-Load`` reads
    ``WS-BATCH-KEY9`` [common/glbatchMT.cbl:L1069] while ``ba070`` logs
    ``ws-BATCH-KEY`` - raised ``BatchKeyViewsDisagreeError`` and aborted the run.

    ⭐ THE ABORT WAS ALSO A DOUBLE-POST HAZARD IN THIS PROGRAM, as in ``sl100``: it
    struck UPSTREAM of the point at which the posted-item latch is cleared, leaving
    it set on a run that had already written postings. Restoring the rollover to a
    plain key transition lets the latch reach its reset, as the COBOL always did.

    ⛔ DO NOT relax the reconciler instead. Its refusal is the safeguard; the defect
    was here, at the writer. NOT a new validation (rule R-3) and NOT an anomaly
    repair (rule R-4) - nothing is tested, clamped or corrected, and the value
    computed is the one the COBOL's own bytes already carry after [:L546-L547].

    Args:
        batch: ``01 WS-Batch-Record.`` [copybooks/wsbatch.cob:L13], mutated in
            place so both readings of its key agree.
    """
    batch.ws_batch_key9.ws_batch_key9 = (
        int(batch.ws_batch_key.ws_ledger) * _BATCH_NOS_SCALE
        + int(batch.ws_batch_key.ws_batch_nos)
    )


def _bl_open(state: _Pl100State) -> None:
    """``bl-open section.``  [purchase/pl100.cbl:L541-L572] - batch allocation, AND A-NEW-5.

    Allocates the next purchase batch number, stamps the batch header from the
    controlled run date, seeds the posting relative-record number - and then
    opens the posting files through the mutually exclusive `IF ... ELSE` that
    is the headline defect of this program.  See the module docstring for the
    three-part analysis; the reproduction and its annotation are below.
    """
    # [L544]  perform GL-Batch-Open.     *> open i-o batch-file
    facade.gl_batch_open(state.ctx(state.batch))

    # [L546]  move bl-next-batch to WS-Batch-Nos.
    # `BL-Next-Batch` [copybooks/wssystem.cob:L198] is a DIFFERENT FIELD from
    # the `Next-Batch` [copybooks/wssystem.cob:L185] that
    # [purchase/pl060.cbl:L885-L887] uses.  Bound to the field this program
    # actually names; a FINDING, not normalised.
    state.batch.ws_batch_key.ws_batch_nos = movelib.move(
        state._pl.bl_next_batch, _D_WS_BATCH_NOS, sending_field=_D_BL_NEXT_BATCH
    )
    # [L547]  move 2 to WS-Ledger.       Ledger 2 = Purchase.
    # `88 PL-Batch value 2.` [copybooks/wsbatch.cob]
    state.batch.ws_batch_key.ws_ledger = movelib.move(2, _D_WS_LEDGER)
    # ⭐ The two moves above have just changed the bytes ``WS-Batch-Key9`` redefines,
    # so its reading is restated - see `_restate_ws_batch_key9`.
    _restate_ws_batch_key9(state.batch)
    # [L548]  add 1 to bl-next-batch.    A REAL `SYSTEM-REC` write.
    state.system_record.purchase_ledger_block.bl_next_batch = arithmetic.add_to(
        1, receiver_value=state._pl.bl_next_batch, receiving=_D_BL_NEXT_BATCH
    )
    # [L549]  move zero to batch-status cleared-status.
    (state.batch.batch_status, state.batch.cleared_status) = movelib.move_to_all(
        movelib.ZERO, [_D_BATCH_STATUS, _D_CLEARED_STATUS]
    )
    # [L550]  move Scycle to Bcycle.
    state.batch.bcycle = movelib.move(
        state._sys.scycle, _D_BCYCLE, sending_field=_D_SCYCLE
    )
    # [L551]  move run-date to entered.
    # THE CONTROLLED-CLOCK OBSERVABLE.  `Run-Date binary-long`
    # [copybooks/wssystem.cob:L67] arrives on the linkage system record, pinned
    # by the CLI.  No clock is read here or anywhere in this module (R-6).
    state.batch.dates.entered = movelib.move(
        state._sys.run_date, _D_ENTERED, sending_field=_D_RUN_DATE
    )

    # [L553]  move "Purchase Ledger Payments" to description.
    # The sibling's literal differs - "Purchase Ledger Orders" - and both are
    # kept as written.
    state.batch.description = movelib.move("Purchase Ledger Payments", _D_DESCRIPTION)
    # [L554-L559]  move zero to bdefault batch-def-ac batch-def-pc items
    #              input-gross input-vat actual-gross actual-vat.  EIGHT
    #              receivers in one statement.
    (
        state.batch.posting_data.b_default,
        state.batch.posting_data.batch_def_ac,
        state.batch.posting_data.batch_def_pc,
        state.batch.items,
        state.batch.amounts.input_gross,
        state.batch.amounts.input_vat,
        state.batch.amounts.actual_gross,
        state.batch.amounts.actual_vat,
    ) = movelib.move_to_all(
        movelib.ZERO,
        [
            _D_BDEFAULT,
            _D_BATCH_DEF_AC,
            _D_BATCH_DEF_PC,
            _D_ITEMS,
            _D_INPUT_GROSS,
            _D_INPUT_VAT,
            _D_ACTUAL_GROSS,
            _D_ACTUAL_VAT,
        ],
    )

    # [L561]  move "DR" to convention.
    state.batch.posting_data.convention = movelib.move("DR", _D_CONVENTION)
    # [L562]  move "PL" to batch-def-code.
    state.batch.posting_data.batch_def_code = movelib.move("PL", _D_BATCH_DEF_CODE)
    # [L563]  move "I" to batch-def-vat.
    state.batch.posting_data.batch_def_vat = movelib.move("I", _D_BATCH_DEF_VAT)
    # [L564]  add postings 1 giving batch-start.
    # THE A-17 CONSUMER.  `postings` is the `SYSTEM-REC` column that
    # `bl-close` [L672] writes `RRN` back into, so the cycle is
    # [L672] -> [L564] -> [L572].  `add A B giving C` sums both operands and
    # quantizes ONCE into the receiver.
    state.batch.batch_start = arithmetic.add_giving(
        state._gl.postings, 1, receiving=_D_BATCH_START
    )

    # ------------------------------------------------------------------
    # ANOMALY A-NEW-5 [purchase/pl100.cbl:L566-L570] - a mutually exclusive
    # IF/ELSE where every sibling program uses two independent IFs, and
    # `if irs-used` omits IRS-Both-Used.  In "B" mode
    # SPL-Posting-Open-Extend never runs yet [L629] still writes; in "Y" mode
    # GL-Posting-Open never runs yet [L646] still writes.  No open-output
    # fallback exists (cf. [purchase/pl060.cbl:L907-L920], which tests both
    # names, keeps the opens independent, and retries each failed open as
    # `open output`).  Compounding it, `bl-close` [L674-L677] closes BOTH
    # files under the pl060-style predicates - closing files that may never
    # have been opened - and [L316-L317] gates this whole section on `G-L`
    # alone, so in "B" mode with `G-L` unset NOTHING is opened while
    # `bl-write` still writes.  The 99-item cap [L653-L655] re-performs this
    # section, so every reopen repeats all of it.
    # Reproduce deliberately per R-4; DO NOT FIX.
    #
    # AMBIGUITY Q-1: what status pair does the data-access layer return for a
    # write to a table that was never opened, and what row state results - in
    # "Y" mode for `GL-Posting-Write`, in "B" mode for `SPL-Posting-Write`,
    # and with `G-L` unset for both?  `dal.facade` publishes every verb
    # regardless of open state and `[common/acas008.cbl:L299-L307]` carries its
    # own unconditional guard set, so whatever those two layers yield is
    # reproduced verbatim and NO exception is invented here.  THE ORACLE
    # DECIDES (R-6).
    # ------------------------------------------------------------------
    # [L566]  if irs-used                *> will open as o/p if not exist
    if _is_irs_used(state):
        # [L567]  perform SPL-Posting-Open-Extend.  *> needed: - bug in OC
        facade.spl_posting_open_extend(state.ctx(state.irs_posting))
    # [L568]  else                       *> will open as o/p if not exist
    else:
        # [L569]  perform GL-Posting-Open.          *> open i-o Posting-file
        facade.gl_posting_open(state.ctx(state.posting))
    # [L570]  end-if.

    # [L572]  move batch-start to rrn.   Spelled lower case here; the same
    # item is spelled `RRN` at [L648], [L650] and [L672].
    state.file_access.rrn = movelib.move(
        state.batch.batch_start, _D_RRN, sending_field=_D_BATCH_START
    )

    # FALL-THROUGH [L572] -> main-exit. [L574]
    _bl_open__main_exit(state)


def _bl_open__main_exit(state: _Pl100State) -> None:
    """``main-exit.   exit section.``  [purchase/pl100.cbl:L574] - the SECOND of five."""
    return


# ==========================================================================
# bl-write SECTION  [purchase/pl100.cbl:L577-L657]
# ==========================================================================
# The maintainer's banner at [L580-L588] reads, verbatim:
#     "This will write a posting record to GL or IRS for EACH line item in
#      EACH invoice so, to use it, you MUST have set up the GL account number
#      for EVERY analysis code via pl070.  It also assumes that you have
#      followed the convention in IRS that default a/c 31 points to VAT input
#      and default a/c 32 is VAT output tax."
# That convention is the origin of the `move 31` at [L640] - see A-18.


def _bl_write(state: _Pl100State) -> None:
    """``bl-write section.``  [purchase/pl100.cbl:L577-L655] - the GL/IRS posting write.

    Builds one posting record for the payment just applied and fans it out to
    whichever of the two posting files the three-state IRS switch selects.

    A PAYMENT POSTING CARRIES NO VAT, and the absence is reproduced rather
    than filled in: `vat-ac` is ZEROED at [L617] where
    [purchase/pl060.cbl:L966-L967] copies `vat-ac of system-record` into it,
    there is no `add oi-vat oi-c-vat to vat-amount`, and only TWO control
    totals are accumulated at [L623-L624] where
    [purchase/pl060.cbl:L973-L976] accumulates FOUR.  `input-vat` and
    `actual-vat` therefore stay at the zero `bl-open` [L554-L559] left them.
    """
    # ------------------------------------------------------------------
    # [L591-L592]  move u-date (1:6) to post-date (1:6).  *> using UK format
    #              move u-date (9:2) to post-date (7:2).
    # `u-date` is `x(10)` and `post-date` is `x(8)`, so taking (1:6) then
    # (9:2) DROPS THE CENTURY DIGITS: "31/12/2025" becomes "31/12/25".  Both
    # sides are 1-BASED reference modification - never Python slicing.  This
    # is the origin of the "two-digit versus four-digit date text forms" the
    # harness normaliser canonicalises.
    #
    # AND NOTE WHOSE DATE THIS IS.  `u-date` holds the OPEN-ITEM date, not the
    # run date: `[L367-L368]` loaded `oi-date` into `u-bin` and performed
    # `zz060-Convert-Date` to unpack it into `u-date` a few statements before
    # `bl-write` was performed at `[L410]`.  `to-day` never reaches
    # `post-date`, which is why the maintainer's comment at `[L589]` says only
    # "u-date is in uk format".  Confirmed at run time: an `oi-date` of 155000
    # yields `post-date` = "17/05/25" for a run dated 31/12/2025.
    #
    # AMBIGUITY Q-4: the exact `post-date` text this produces for each
    # `Date-Form` presentation, and therefore what lands in
    # `GLPOSTING-REC.POST-DAT` and `PSIRSPOST-REC.IRS-POST-DAT`, depends on
    # what `zz060`/`maps04` left in `u-date` at the time - which for a
    # rejected date is the caller's prior content, because `maps04` leaves its
    # output untouched on reject [common/maps04.cbl:L146].  Under `Date-USA`
    # and `Date-Intl` the presentation differs and the two characters taken
    # from offset 9 are no longer the year, so the stored text is decided by
    # measurement, not reasoning.  THE ORACLE DECIDES (R-6).
    # ------------------------------------------------------------------
    _post_date = movelib.move(state.posting.post_date, _D_POST_DATE)
    _post_date = movelib.ref_mod_into(
        _post_date, 1, 6, movelib.ref_mod(state.maps03_ws.u_date, 1, 6)
    )
    _post_date = movelib.ref_mod_into(
        _post_date, 7, 2, movelib.ref_mod(state.maps03_ws.u_date, 9, 2)
    )
    state.posting.post_date = _post_date

    # [L593]  add 1 to items.
    state.batch.items = arithmetic.add_to(
        1, receiver_value=state.batch.items, receiving=_D_ITEMS
    )
    # [L594]  move items to post-number.
    state.posting.ws_post_key.post_number = movelib.move(
        state.batch.items, _D_POST_NUMBER, sending_field=_D_ITEMS
    )
    # [L595]  move oi-paid to post-amount.
    # `oi-paid`, NOT a net-of-VAT working figure: the payment is posted gross.
    state.posting.post_amount = movelib.move(
        state.otm5.filler_1.oi_paid, _D_POST_AMOUNT, sending_field=_D_OI_PAID
    )

    # [L600]  move WS-Batch-nos to batch.
    # Sequenced AFTER the amount, as written.
    state.posting.ws_post_key.batch = movelib.move(
        state.batch.ws_batch_key.ws_batch_nos, _D_POST_BATCH,
        sending_field=_D_WS_BATCH_NOS,
    )

    # ------------------------------------------------------------------
    # [L597-L610]  the post-legend, built from folio/invoice number plus
    # " : " plus the supplier name "instead of batch/item on posting file for
    # both IRS & GL" (the maintainer's comment).
    # [L601]  move oi-invoice to m.        `m pic z(7)9` - an EDITED move,
    #                                     so the value arrives space-suppressed.
    # [L602]  move zero to b.
    # [L603]  inspect m tallying b for leading space.
    # [L604]  subtract b from 8 giving c.
    # [L605]  add 1 to b.                 b now indexes the first digit.
    # [L606]  move 1 to xx.
    # [L608-L610]  ONE `STRING` statement with THREE sources sharing
    #              `pointer xx`.  [sales/sl100.cbl:L620-L628] builds the same
    #              column with FIVE separate `STRING` statements sharing one
    #              pointer; the two shapes are NOT unified.
    # ------------------------------------------------------------------
    state.m = movelib.move_to_edited(state.otm5.oi_key.oi_invoice, _D_M)
    state.b = movelib.move(movelib.ZERO, _D_B)
    state.b = movelib.inspect_tallying_leading(state.m, movelib.SPACE, state.b)
    state.c = arithmetic.subtract_giving(state.b, minuend=8, receiving=_D_C)
    state.b = arithmetic.add_to(1, receiver_value=state.b, receiving=_D_B)
    state.xx = movelib.move(1, _D_XX)
    _legend, _pointer = movelib.string_into(
        movelib.move(state.posting.post_legend, _D_POST_LEGEND),
        [
            movelib.ref_mod(state.m, int(state.b), int(state.c)),
            " : ",
            movelib.move(state.purch.purch_name, _D_PURCH_NAME),
        ],
        pointer=int(state.xx),
        delimited_by=movelib.Delimiter.SIZE,
    )
    state.posting.post_legend = _legend
    # `STRING ... POINTER` updates the pointer in place; `xx` is not read
    # again before [L606] re-initialises it on the next item, but the update
    # is a real store and is reproduced.
    state.xx = movelib.move(_pointer, _D_XX)

    # ------------------------------------------------------------------
    # [L612-L613]  THE DR/CR SIDES ARE SWAPPED RELATIVE TO `pl060`.
    #   pl100 : p-creditors -> post-dr    bl-pay-ac   -> post-cr
    #   pl060 : bl-purch-ac -> post-dr    p-creditors -> post-cr
    #           [purchase/pl060.cbl:L958-L959]
    # And the account field is `bl-pay-ac`, not `bl-purch-ac`.  A payment
    # debits creditors and credits the bank/payment account, which is the
    # mirror image of an order posting; `sl100` carries the same swap
    # relative to `sl060`.  Reproduced; NOT "corrected".
    # ------------------------------------------------------------------
    state.posting.post_dr = movelib.move(
        state._pl.p_creditors, _D_POST_DR, sending_field=_D_P_CREDITORS
    )
    state.posting.post_cr = movelib.move(
        state._pl.bl_pay_ac, _D_POST_CR, sending_field=_D_BL_PAY_AC
    )

    # ------------------------------------------------------------------
    # ANOMALY A-18 [purchase/pl100.cbl:L615-L616], [purchase/pl100.cbl:L640-L641]
    # - `dr-pc` and `cr-pc` are zeroed here and are never carried into the IRS
    # posting record, the maintainer flagging the concern himself in adjacent
    # comments: "Missing usage of DR-PC for GL MUST be checked in GL ????"
    # [L635] and the same for CR-PC [L637].  [L640-L641] then moves the
    # literal 31 into BOTH `WS-IRS-Vat-AC-Def` AND `Vat-PC`, carrying the
    # maintainer's own "*> IS IT ???".  31 is the IRS default account the
    # [L586-L587] banner says "points to VAT input"; `sl060` moves 32, the
    # output-tax account.  Reproduce deliberately per R-4; DO NOT FIX.
    #
    # ANOMALY A-21 [purchase/pl100.cbl:L617], [purchase/pl100.cbl:L626],
    # [purchase/pl100.cbl:L631] - `vat-ac of WS-Posting-record`,
    # `post-code in WS-Posting-record` and `Post-Code in WS-Posting-Record`
    # are QUALIFIED references, forced by field-name collisions across
    # `wspost.cob`, `wspost-irs.cob` and `wssystem.cob`.  Note the lower-case
    # `record` at [L617]/[L626] against the upper-case `Record` at [L631] -
    # the same item, spelled two ways.  Python attribute access makes the
    # qualification structural, so the anomaly survives only as this note.
    # Reproduce deliberately per R-4; DO NOT FIX.
    # ------------------------------------------------------------------
    # [L615-L619]  move zero to dr-pc cr-pc vat-ac of WS-Posting-record
    #                          vat-pc vat-amount.   FIVE receivers.
    (
        state.posting.dr_pc,
        state.posting.cr_pc,
        state.posting.vat_ac,
        state.posting.vat_pc,
        state.posting.vat_amount,
    ) = movelib.move_to_all(
        movelib.ZERO, [_D_DR_PC, _D_CR_PC, _D_VAT_AC, _D_VAT_PC, _D_VAT_AMOUNT]
    )

    # [L621]  move spaces to post-vat-side.
    # FINDING - AN INERT STORE: [L627] overwrites it with "DR" before any
    # write occurs, so this store is dead.  It is exactly the pattern at
    # [sales/sl100.cbl:L639]/[L645].  Plan section 0.8.4 puts performance work
    # "out of scope by construction", so the dead store is reproduced.
    state.posting.post_vat_side = movelib.move_figurative(
        movelib.SPACES, _D_POST_VAT_SIDE
    )

    # [L623-L624]  the TWO control-total accumulations - gross only.
    state.batch.amounts.input_gross = arithmetic.add_to(
        state.posting.post_amount,
        receiver_value=state.batch.amounts.input_gross,
        receiving=_D_INPUT_GROSS,
    )
    state.batch.amounts.actual_gross = arithmetic.add_to(
        state.posting.post_amount,
        receiver_value=state.batch.amounts.actual_gross,
        receiving=_D_ACTUAL_GROSS,
    )

    # [L626]  move "PL" to post-code in WS-Posting-record.
    state.posting.post_code = movelib.move("PL", _D_POST_CODE)
    # [L627]  move "DR" to post-vat-side.   Overwrites the inert [L621] store.
    state.posting.post_vat_side = movelib.move("DR", _D_POST_VAT_SIDE)

    # ------------------------------------------------------------------
    # [L629-L645]  the IRS fan-out write.  Predicate `irs-used or
    # IRS-Both-Used` - INCONSISTENT with [L566], which tests `irs-used`
    # ALONE, which is defect (a) of A-NEW-5: in "B" mode the file this writes
    # to was never opened.
    # ------------------------------------------------------------------
    if _is_irs_used(state) or _is_irs_both_used(state):
        # [L630]  move WS-Post-key to WS-IRS-Post-key.
        # A GROUP move: the 10-byte image of `Batch` + `Post-Number` is
        # copied wholesale onto `WS-IRS-Batch` + `WS-IRS-Post-Number`.  The
        # image is assembled from the pictures and redistributed, which is
        # what a group MOVE does at the byte level.
        _key_image, _ = movelib.string_into(
            " " * (_D_POST_BATCH.byte_length + _D_POST_NUMBER.byte_length),
            [
                (state.posting.ws_post_key.batch, movelib.Delimiter.SIZE, _D_POST_BATCH),
                (
                    state.posting.ws_post_key.post_number,
                    movelib.Delimiter.SIZE,
                    _D_POST_NUMBER,
                ),
            ],
            pointer=1,
            delimited_by=movelib.Delimiter.SIZE,
        )
        state.irs_posting.ws_irs_post_key.ws_irs_batch = movelib.move(
            movelib.ref_mod(_key_image, 1, _D_IRS_BATCH.byte_length), _D_IRS_BATCH
        )
        state.irs_posting.ws_irs_post_key.ws_irs_post_number = movelib.move(
            movelib.ref_mod(
                _key_image,
                _D_IRS_BATCH.byte_length + 1,
                _D_IRS_POST_NUMBER.byte_length,
            ),
            _D_IRS_POST_NUMBER,
        )
        # [L631-L632]  move Post-Code in WS-Posting-Record to WS-IRS-Post-Code.
        state.irs_posting.ws_irs_post_code = movelib.move(
            state.posting.post_code, _D_IRS_POST_CODE, sending_field=_D_POST_CODE
        )
        # [L633]  move post-date to WS-IRS-post-date.
        state.irs_posting.ws_irs_post_date = movelib.move(
            state.posting.post_date, _D_IRS_POST_DATE, sending_field=_D_POST_DATE
        )
        # [L634]  move Post-DR to WS-IRS-Post-DR.
        # `Post-DR pic 9(6)` into `WS-IRS-Post-DR pic 9(5)` - the receiving
        # field is one digit NARROWER, so a six-digit account number loses its
        # high-order digit.  `move` applies the receiving picture, so the
        # truncation is reproduced rather than guarded.
        state.irs_posting.ws_irs_post_dr = movelib.move(
            state.posting.post_dr, _D_IRS_POST_DR, sending_field=_D_POST_DR
        )
        # [L635]  *> Missing usage of DR-PC for GL MUST be checked in GL ????
        #         `dr-pc` is NOT carried across - A-18.
        # [L636]  move Post-CR to WS-IRS-Post-CR.   Same 9(6) -> 9(5) narrowing.
        state.irs_posting.ws_irs_post_cr = movelib.move(
            state.posting.post_cr, _D_IRS_POST_CR, sending_field=_D_POST_CR
        )
        # [L637]  *> Missing usage of CR-PC for GL MUST be checked in GL ????
        #         `cr-pc` is NOT carried across - A-18.
        # [L638]  move Post-Amount to WS-IRS-Post-Amount.
        # `s9(8)v99` into `s9(7)v99 sign leading` - again one integer digit
        # narrower, and the receiver is DISPLAY with a LEADING sign.
        state.irs_posting.ws_irs_post_amount = movelib.move(
            state.posting.post_amount,
            _D_IRS_POST_AMOUNT,
            sending_field=_D_POST_AMOUNT,
        )
        # [L639]  move Post-Legend to WS-IRS-Post-Legend.
        state.irs_posting.ws_irs_post_legend = movelib.move(
            state.posting.post_legend,
            _D_IRS_POST_LEGEND,
            sending_field=_D_POST_LEGEND,
        )
        # [L640-L641]  move 31 to WS-IRS-vat-ac-def Vat-PC.   *> IS IT ???
        # TWO receivers, and the second is the GL posting record's `Vat-PC`,
        # which [L618] has just zeroed - so this statement re-writes a field
        # of the OTHER record from inside the IRS block.  A-18.
        (
            state.irs_posting.ws_irs_vat_ac_def,
            state.posting.vat_pc,
        ) = movelib.move_to_all(31, [_D_IRS_VAT_AC_DEF, _D_VAT_PC])
        # [L642]  move Post-Vat-Side to WS-IRS-Post-Vat-Side.
        state.irs_posting.ws_irs_post_vat_side = movelib.move(
            state.posting.post_vat_side,
            _D_IRS_POST_VAT_SIDE,
            sending_field=_D_POST_VAT_SIDE,
        )
        # [L643]  move Vat-Amount to WS-IRS-vat-amount.   Always zero here.
        state.irs_posting.ws_irs_vat_amount = movelib.move(
            state.posting.vat_amount,
            _D_IRS_VAT_AMOUNT,
            sending_field=_D_VAT_AMOUNT,
        )
        # [L644]  perform SPL-Posting-Write.   *> write irs-posting-record
        # In "B" mode the table was never opened - A-NEW-5 defect (a),
        # AMBIGUITY Q-1.  `SPL-Posting-Rewrite` is never called anywhere in
        # this program, which is fortunate: [common/acas008.cbl:L299-L307]
        # refuses rewrite, read-indexed, start and delete unconditionally
        # (ANOMALY A-6).
        facade.spl_posting_write(state.ctx(state.irs_posting))
    # [L645]  end-if

    # [L646-L647]  if IRS-Both-Used or G-L   *> (As set in params)
    # Predicate INCONSISTENT with [L566]'s `else` branch, which reaches
    # `GL-Posting-Open` only when `irs-used` is FALSE - so in "Y" mode with
    # `G-L` also set this writes to a table that was never opened.  A-NEW-5
    # defect (b), AMBIGUITY Q-1.
    if _is_irs_both_used(state) or _is_g_l(state):
        # [L648]  move RRN to WS-Post-RRN.
        state.posting.ws_post_rrn = movelib.move(
            state.file_access.rrn, _D_WS_POST_RRN, sending_field=_D_RRN
        )
        # [L649]  perform GL-Posting-Write.   *> write posting-record
        facade.gl_posting_write(state.ctx(state.posting))
        # [L650]  add 1 to RRN.
        state.file_access.rrn = arithmetic.add_to(
            1, receiver_value=state.file_access.rrn, receiving=_D_RRN
        )
    # [L651]  end-if

    # [L653-L655]  if items = 99 perform bl-close perform bl-open.
    # The 99-item batch cap: the batch is closed and a fresh one allocated,
    # which re-runs `bl-open` [L546-L548] for a new batch number - AND
    # re-runs A-NEW-5 in full, so every reopen repeats the
    # write-without-open condition.
    if arithmetic.compare(state.batch.items, 99) == 0:
        _bl_close(state)
        _bl_open(state)

    # FALL-THROUGH [L655] -> main-exit. [L657]
    _bl_write__main_exit(state)


def _bl_write__main_exit(state: _Pl100State) -> None:
    """``main-exit.   exit section.``  [purchase/pl100.cbl:L657] - the THIRD of five."""
    return


# ==========================================================================
# bl-close SECTION  [purchase/pl100.cbl:L660-L679]
# ==========================================================================


def _bl_close(state: _Pl100State) -> None:
    """``bl-close section.``  [purchase/pl100.cbl:L660-L677] - A-17 and the A-1 CONTROL CASE.

    Writes the batch header, then closes the batch file and BOTH posting
    files - under the `pl060`-style predicates, so it can close a file that
    `bl-open`'s mutually exclusive `IF ... ELSE` never opened.  That
    compounding is documented with A-NEW-5 in `_bl_open`.
    """
    # [L663]  perform GL-Batch-Write.    *> write batch-record
    facade.gl_batch_write(state.ctx(state.batch))
    # [L664-L670]  if fs-reply not = zero -> DIAGNOSTICS WITH NO CONTROL
    # TRANSFER.  Every close below still runs; nothing is retried and nothing
    # is rolled back.  R-3 forbids adding a retry.
    if state.file_access.fs_reply != FsReply.SUCCESS:
        # [L665]  display PL132 at 2301
        # [L666]  perform Eval-Status
        _eval_status(state)
        # [L667-L668]  display fs-reply / exception-msg.  Four displays, one
        # record.  `PL002` [L669] IS DROPPED with the `accept` it introduces -
        # the whole literal is the key-press instruction.  `exception-msg` STAYS:
        # it is `pic x(25)` [purchase/pl100.cbl:L126] filled ONLY by
        # `Eval-Status` above from the static status table
        # `copybooks/FileStat-Msgs.cpy` keyed on `fs-reply`, so it is a fixed
        # status NAME - never driver text and never a business value.
        _LOG.error(
            "%s [%s:L665-L668] %s fs-reply=%s we-error=%s %s",
            _PROG_NAME,
            _SRC,
            _PL132,
            state.file_access.fs_reply,
            state.file_access.we_error,
            state.exception_msg,
        )
        # [L670]  accept ws-reply at 2430.
        # FINDING: this `accept` is NOT wrapped in `if WS-Caller not =
        # "xl150"`, unlike [purchase/pl060.cbl:L1022-L1025].  The accept is a
        # bare acknowledgement pause and is dropped either way, but the
        # ABSENCE of the unattended-mode branch is a real structural
        # divergence from the sibling and is recorded, not repaired.

    # ------------------------------------------------------------------
    # ANOMALY A-17 [purchase/pl100.cbl:L672] - `move RRN to postings.` carries
    # the maintainer's own "*> Why ?".  Plan section 0.6.8: "Because the
    # maintainer himself does not know why it is there, its observable effect
    # on the posting record must be measured and then reproduced regardless of
    # whether it makes sense."  IT IS NOT INERT: `postings` is a `SYSTEM-REC`
    # column read back at [L564] `add postings 1 giving batch-start` and
    # seeded into `rrn` at [L572], so the cycle is [L672] -> [L564] -> [L572]
    # and this store determines the relative-record number the NEXT batch
    # starts from.  Occurrence 4 of 4; the others are [sales/sl060.cbl:L1173],
    # [sales/sl100.cbl:L691] and [purchase/pl060.cbl:L1028].
    # Reproduce deliberately per R-4; DO NOT FIX.
    #
    # FINDING: the maintainer's comment at [L671] reads "*> THIS IS IN
    # PURCHASE PL060" - inside pl100, where it names the wrong program
    # entirely.  It appears in four files: [sales/sl060.cbl:L1172],
    # [purchase/pl060.cbl:L1027], [sales/sl100.cbl:L690] and
    # [purchase/pl100.cbl:L671].  A copy-paste artefact.
    # ------------------------------------------------------------------
    # [L671]  if IRS-Both-Used OR G-L      *> THIS IS IN PURCHASE PL060
    if _is_irs_both_used(state) or _is_g_l(state):
        # [L672]  move RRN to postings.    *> Why ?
        state.system_record.general_ledger_block.postings = movelib.move(
            state.file_access.rrn, _D_POSTINGS, sending_field=_D_RRN
        )

    # [L673]  perform GL-Batch-Close.      *> close Batch-file
    facade.gl_batch_close(state.ctx(state.batch))

    # ------------------------------------------------------------------
    # ANOMALY A-1, CONTROL CASE [purchase/pl100.cbl:L675] - THE PERIOD IS
    # PRESENT, AND IT MUST STAY PRESENT.  Because [L675] terminates its
    # sentence, the `if` at [L676] is a SIBLING and `GL-Posting-Close` IS
    # reached in pure-GL mode.  [sales/sl060.cbl:L1176] LACKS the period, so
    # there its second `if` nests inside the first and the GL posting close
    # never executes when only `G-L` is set - that is anomaly A-1.  The three
    # control cases that prove A-1 is an accident rather than an idiom are
    # [purchase/pl060.cbl:L1031], [sales/sl100.cbl:L694] and this site.
    # The anomaly is the DIFFERENCE from `sl060`; do NOT "align" with it.
    # Reproduce deliberately per R-4; DO NOT FIX.
    # ------------------------------------------------------------------
    # [L674]  if IRS-Used OR IRS-Both-Used
    if _is_irs_used(state) or _is_irs_both_used(state):
        # [L675]  perform SPL-Posting-Close.   *> close irs-post-file
        # May close a file `bl-open` never opened - see A-NEW-5.
        facade.spl_posting_close(state.ctx(state.irs_posting))
    # [L676]  if IRS-Both-Used or G-L        <- a SIBLING `if`, not nested
    if _is_irs_both_used(state) or _is_g_l(state):
        # [L677]  perform GL-Posting-Close.   *> close posting-file
        # Likewise may close a file `bl-open` never opened - see A-NEW-5.
        facade.gl_posting_close(state.ctx(state.posting))

    # FALL-THROUGH [L677] -> main-exit. [L679]
    _bl_close__main_exit(state)


def _bl_close__main_exit(state: _Pl100State) -> None:
    """``main-exit.   exit section.``  [purchase/pl100.cbl:L679] - the FOURTH of five."""
    return


# ==========================================================================
# Eval-Status SECTION  [purchase/pl100.cbl:L681-L687]
# ==========================================================================


def _eval_status(state: _Pl100State) -> None:
    '''``Eval-Status section.``  [purchase/pl100.cbl:L681-L685] - the file-status message.

    ``copy "FileStat-Msgs.cpy" replacing STATUS by fs-reply
                                        msg by exception-msg.``  [L684-L685]

    DIAGNOSTIC ONLY - it renders a message and MUST NOT alter control flow.
    Its only caller is [L666], inside `bl-close`'s batch-write failure path,
    which itself performs no control transfer.

    THREE NAMING DIVERGENCES from the siblings, all preserved:
      * the section is named `Eval-Status`, as in [sales/sl100.cbl] section
        700 - not `Evaluate-Message` [purchase/pl060.cbl] section 1037, and
        not `zz040-Evaluate-Message` [sales/sl060.cbl] section 1183;
      * the `REPLACING` order is `STATUS by fs-reply` THEN `msg by
        exception-msg`, with `msg` in LOWER CASE;
      * the receiver is `exception-msg` [L126], where `pl060` uses
        `ws-Eval-Msg`.

    The copybook resolves a status code to text.  `dal.status` already carries
    that mapping for the codes this cycle produces, so the rendering is taken
    from there rather than duplicated: `FsReply` is an enumeration whose
    member name IS the condition, which is what the copybook's text conveys.
    '''
    # `FS-Reply` is `pic 99`, so an unmapped value must still render.
    try:
        _text = FsReply(int(state.file_access.fs_reply)).name.replace("_", " ")
    except ValueError:
        _text = f"UNMAPPED FILE STATUS {int(state.file_access.fs_reply):02d}"
    state.exception_msg = movelib.move(_text, _D_EXCEPTION_MSG)

    # FALL-THROUGH [L685] -> main-exit. [L687]
    _eval_status__main_exit(state)


def _eval_status__main_exit(state: _Pl100State) -> None:
    """``main-exit.   exit section.``  [purchase/pl100.cbl:L687] - the FIFTH and last.

    Note the name: this section's exit is `main-exit`, NOT the `Eval-Msg-Exit`
    that [purchase/pl060.cbl] section 1043 uses.  Preserved as written.
    """
    return


# ==========================================================================
# zz050-Validate-Date SECTION  [purchase/pl100.cbl:L689-L722]
# ==========================================================================
# FINDING - DEAD CODE THAT MUST STILL EXIST.  `grep -c "perform *zz050"` over
# purchase/pl100.cbl returns ZERO: this section is DECLARED but NEVER
# PERFORMED anywhere in the program.  R-5 nonetheless requires a named
# function per section and per paragraph, and plan section 0.7.4 C-4 requires
# that "every paragraph retains a named function", so all three labels are
# represented here.  Nothing calls them, exactly as nothing calls the COBOL.


def _zz050_validate_date(state: _Pl100State) -> None:
    '''``zz050-Validate-Date section.``  [purchase/pl100.cbl:L689-L714].

    Presents `ws-Test-Date` in UK order and validates it through the date
    module.  ⛔ THE PLAIN VARIANT: `gl051`'s carries three extra
    `inspect ... replacing` statements at [general/gl051.cbl:L1178-L1180]
    that this one does NOT, so `dates.zz050_validate_date` is called and NOT
    `dates.zz050_validate_date_gl051`.

    The consolidated implementation reproduces, in order: `move ws-test-date
    to ws-date` [L698]; the `if Date-Form = zero move 1 to Date-Form` default
    [L699-L700]; the UK short-circuit [L701-L702]; the USA day/month swap
    through `ws-swap` [L703-L707]; and the International rebuild that seeds
    `ws-date` with the literal `"dd/mm/ccyy"` [L711] before three
    reference-modified moves off `ws-test-date` [L712-L714].

    Every `zz0xx` helper RETURNS the effective `Date-Form`, because the COBOL
    writes the default back into the `SYSTEM-REC` field; the caller must store
    it back, which is done here.
    '''
    # THE TWO TRANSFER SITES INSIDE THIS SECTION, each classified by shape.
    # Both target `zz050-test-date` [L716], a named paragraph that performs
    # real work (three statements) and then falls through to the section exit,
    # which is what makes them Class 4 rather than Class 3.  Per-site proof: in
    # both cases every statement between the transfer and the target would
    # otherwise be skipped, and the target is entered with `ws-date` already in
    # UK order - which is exactly what the consolidated helper does when it
    # calls `dates.zz050_test_date` after the UK short-circuit and after the
    # USA swap.
    #
    # [L702]  if Date-UK go to zz050-test-date.
    #         # GO TO class 4 at [L702] -> zz050-test-date [L716]
    # [L707]  after the USA day/month swap, go to zz050-test-date.
    #         # GO TO class 4 at [L707] -> zz050-test-date [L716]
    #
    # [L689-L714] + [L716-L719]  the consolidated section, wrapper = maps04.
    state.system_record.system_data_block.date_form = dates.zz050_validate_date(
        state.date_formats,
        state.maps03_ws,
        int(state._sys.date_form),
        wrapper=_maps04_wrapper(state),
    )
    _zz050_exit(state)


def _zz050_test_date(state: _Pl100State) -> None:
    """``zz050-test-date.``  [purchase/pl100.cbl:L716-L719] - the shared validation tail.

    ``move ws-date to u-date.``  [L717]
    ``move zero to u-bin.``      [L718]  <- the caller PRE-ZEROES, which is
                                            the only reason the date module's
                                            documented "errors return zero"
                                            contract appears to hold; the
                                            module itself leaves `u-bin`
                                            UNTOUCHED on reject
                                            [common/maps04.cbl:L146].
    ``perform maps04.``          [L719]
    """
    dates.zz050_test_date(
        state.date_formats, state.maps03_ws, wrapper=_maps04_wrapper(state)
    )
    _zz050_exit(state)


def _zz050_exit(state: _Pl100State) -> None:
    """``zz050-exit.   exit section.``  [purchase/pl100.cbl:L721-L722]."""
    return


# ==========================================================================
# zz060-Convert-Date SECTION  [purchase/pl100.cbl:L724-L757]
# ==========================================================================


def _zz060_convert_date(state: _Pl100State) -> None:
    '''``zz060-Convert-Date section.``  [purchase/pl100.cbl:L724-L754] - binary -> text.

    Unpacks the binary day number in `u-bin` into `u-date` and presents it in
    the configured form.  Its single caller is [L367-L368], which loads
    `oi-date` into `u-bin` first.

    THE ONE-TOKEN DIVERGENCE: `zz060` is identical across all six carrying
    programs EXCEPT for the wrapper it performs - four of them, including this
    one, `perform maps04` [L733], the others `perform maps03`.  The
    `maps04` variant is selected here.

    Reproduces in order: `perform maps04` [L733]; the space guard `if u-date =
    spaces move spaces to ws-Date go to zz060-Exit` [L734-L736]; `move u-date
    to ws-date` [L737]; the `Date-Form` default [L739-L740]; the UK
    short-circuit [L741-L742]; the USA swap [L743-L747]; and the
    International rebuild seeded with `"ccyy/mm/dd"` [L751] plus three
    reference-modified moves off `u-date` [L752-L754].
    '''
    # THE THREE TRANSFER SITES INSIDE THIS SECTION.  All three target the
    # section's own trailing exit label, so all three are Class 3 - a forward
    # transfer to `exit section.` that skips no statement which would otherwise
    # run.  Reproduced as early returns inside `dates.zz060_convert_date`.
    #
    # [L736]  if u-date = spaces move spaces to ws-Date go to zz060-Exit.
    #         # GO TO class 3 at [L736] -> zz060-Exit [L756]
    # [L742]  if Date-UK go to zz060-Exit.
    #         # GO TO class 3 at [L742] -> zz060-Exit [L756]
    # [L747]  after the USA day/month swap, go to zz060-Exit.
    #         # GO TO class 3 at [L747] -> zz060-Exit [L756]
    state.system_record.system_data_block.date_form = dates.zz060_convert_date(
        state.date_formats,
        state.maps03_ws,
        int(state._sys.date_form),
        wrapper=_maps04_wrapper(state),
    )
    _zz060_exit(state)


def _zz060_exit(state: _Pl100State) -> None:
    """``zz060-Exit.   exit section.``  [purchase/pl100.cbl:L756-L757]."""
    return


# ==========================================================================
# zz070-Convert-Date SECTION  [purchase/pl100.cbl:L759-L787]
# ==========================================================================


def _zz070_convert_date(state: _Pl100State) -> None:
    '''``zz070-Convert-Date section.``  [purchase/pl100.cbl:L759-L784] - the run date.

    Presents the linkage run date `to-day` in the configured form, leaving the
    result in `ws-date`.  Performed twice, at [L286] and [L300].

    `zz070` is BYTE-IDENTICAL in all ten carrying programs, so the
    consolidated implementation is called directly.  It reproduces `move
    to-day to ws-date` [L767]; the `Date-Form` default [L769-L770]; the UK
    short-circuit [L771-L772]; the USA swap [L773-L777]; and the
    International rebuild seeded with `"ccyy/mm/dd"` [L781] plus three
    reference-modified moves off `to-day` [L782-L784].

    ⛔ NO CLOCK IS READ.  `to-day` arrives through linkage and `Run-Date`
    arrives on the system record, both pinned by the CLI (R-6).
    '''
    # THE TWO TRANSFER SITES INSIDE THIS SECTION.  Both target the section's
    # own trailing exit label, so both are Class 3.  Note the ABSENCE of a
    # `u-date = spaces` guard here - `zz070` has no counterpart to `zz060`'s
    # [L736], because it converts the linkage `to-day` rather than a value the
    # date module produced.  Reproduced as early returns inside
    # `dates.zz070_convert_date`.
    #
    # [L772]  if Date-UK go to zz070-Exit.
    #         # GO TO class 3 at [L772] -> zz070-Exit [L786]
    # [L777]  after the USA day/month swap, go to zz070-Exit.
    #         # GO TO class 3 at [L777] -> zz070-Exit [L786]
    state.system_record.system_data_block.date_form = dates.zz070_convert_date(
        state.date_formats, state.to_day, int(state._sys.date_form)
    )
    _zz070_exit(state)


def _zz070_exit(state: _Pl100State) -> None:
    """``zz070-Exit.   exit section.``  [purchase/pl100.cbl:L786-L787]."""
    return


# ==========================================================================
# maps04 SECTION  [purchase/pl100.cbl:L789-L795]
# ==========================================================================


def _maps04(state: _Pl100State) -> None:
    '''``maps04 section.``  [purchase/pl100.cbl:L789-L792] - the date-module wrapper.

    ``call "maps04" using maps03-ws.``  [L792]

    R-1 forbids COBOL at runtime, so the called program is reimplemented in
    `acas_posting.dates` rather than invoked.  `dates.maps04` preserves the
    module's reject behaviour of leaving `u-bin` COMPLETELY UNTOUCHED
    [common/maps04.cbl:L146], [common/maps04.cbl:L154] - it does NOT zero it -
    together with the 1600-12-31 ordinal epoch and the six-part reject test.

    ANOMALY A-22 DOES NOT OCCUR HERE: this section is named `maps04` and its
    exit is named `maps04-exit` [L794], and the two AGREE.  A-22's occurrences
    are [general/gl070.cbl:L603-L609] and
    [general/gl051.cbl:L1273]/[general/gl051.cbl:L1278], where a wrapper is
    named after the interface copybook while its exit is named after the
    called program.
    '''
    dates.maps04(state.maps03_ws)
    _maps04_exit(state)


def _maps04_exit(state: _Pl100State) -> None:
    """``maps04-exit.   exit section.``  [purchase/pl100.cbl:L794-L795]."""
    return


def _maps04_wrapper(state: _Pl100State) -> Callable[[Maps03Ws], None]:
    """Bind this program's own `maps04` section as the wrapper the date helpers perform.

    The consolidated `zz050`/`zz060` implementations take the wrapper as a
    parameter precisely because the carrying programs differ in which one they
    perform.  Routing through `_maps04` rather than straight to `dates.maps04`
    keeps the traced section on the call path, so the paragraph-to-function
    mapping R-5 requires is honoured at run time and not merely on paper.
    """

    def _perform(ws: Maps03Ws) -> None:
        # The helpers hand back the same `maps03-ws` instance the state holds;
        # the assertion is a contract check, not an added validation of data.
        if ws is not state.maps03_ws:  # pragma: no cover - contract guard
            raise AssertionError(
                "maps04 wrapper invoked with a foreign maps03-ws instance"
            )
        _maps04(state)

    return _perform


# ==========================================================================
# PUBLIC ENTRY POINT
# ==========================================================================


def run(
    ws_calling_data: WsCallingData,
    system_record: SystemRecord,
    system_record_4: SystemRecord4,
    to_day: str,
    file_defs: FileDefs,
    *,
    ok_to_post: bool,
    dal_options: Mapping[str, object] | None = None,
) -> None:
    '''Run `pl100` - Purchase Ledger Cash/Payment Posting.

    ``procedure division using ws-calling-data
                              system-record
                              system-record-4
                              to-day
                              file-defs.``   [purchase/pl100.cbl:L265-L269]

    The SL/PL five-parameter linkage shape, in the COBOL's own order.  The
    caller is `acas_posting.cli.pl_payment_post`, mirroring
    [purchase/purchase.cbl:L785-L789] (`load12`).  ⭐ PURCHASE HAS NO
    TERM-CODE GATE - [purchase/purchase.cbl:L752-L762] has its gate lines
    commented out - so unlike the General Ledger cycle nothing here sets
    `WS-Term-Code` to abort a downstream phase.

    Both linkage records are MUTATED IN PLACE, and that is the whole point:
    [purchase/purchase.cbl:L691-L706] (`load000`) persists the mutated
    `SYSTEM-REC` and `SYSTOT-REC` with an over-rewrite after the called
    program returns, which is why this program never invokes a System facade
    verb of its own.  The four `SYSTEM-REC` writes - `bl-next-batch` [L548],
    `postings` [L672], `oi-5-flag` [L464] and `P-Flag-P` [L465] - plus the
    `SYSTOT-REC` write `pl-payments` [L396] all reach the database that way.

    Args:
        ws_calling_data: `WS-Calling-Data` [copybooks/wscall.cob:L6-L13].
        system_record: `System-Record` [copybooks/wssystem.cob].  Supplies the
            pinned `Run-Date` [copybooks/wssystem.cob:L67], the `P-Flag-P`
            one-shot latch, the IRS three-state switch and the GL/PL control
            accounts; receives the four writes listed above.
        system_record_4: `System-Record-4` [copybooks/wssys4.cob].  Receives
            period total 9 of 9, `PL-Payments`, at [L396].
        to_day: `to-day pic x(10)` [purchase/pl100.cbl:L263] - the pinned run
            date in the presentation the `Date-Form` selects.  The first of the
            two controlled-clock observables.
        file_defs: `File-Defs` [copybooks/wsnames.cob].
        ok_to_post: The `[L302-L311]` run-confirm, "OK to post payment
            transactions (YES/NO) ?".  Plan section 0.3.4 requires that
            "accept prompts that gate a database write become explicit CLI
            parameters with the COBOL default preserved", and this one gates
            EVERY write the program makes: answering NO transfers to
            `menu-exit` [L309] having opened nothing and written nothing at
            all.  `True` corresponds to the COBOL's `"YES"`, the only reply
            that proceeds.  ⛔ REQUIRED, WITH NO DEFAULT: there is no COBOL
            default for section 0.3.4 to preserve, because `wx-reply` is
            `pic xxx value spaces` [L157], [L305] moves spaces into it again
            immediately before the accept so that [L306]'s `update` pre-fills
            blanks, and [L310-L311] re-asks on a blank.  A keyword default
            would invent an answer the frozen program has not got, and the
            affirmative one writes to the database; an earlier draft defaulted
            this to `True`.  The COBOL upper-cases the reply
            (`function upper-case`, [L307]) and re-asks on anything other than
            `"YES"` or `"NO"` [L310-L311]; with a boolean the re-ask collapses,
            which is a consequence of removing the presentation layer and NOT
            a behaviour change - see the Class 4 proof on
            `_init01__acpt_xrply`.

            ⭐ REQUIRED, WITH NO DEFAULT (M-09, CWE-636).  It defaulted to
            `True`, on the reasoning that `"YES"` is "the only reply that
            proceeds".  That reasoning is sound and it does not yield a
            default, because a default is what the program does when the
            operator supplies NOTHING and this program then does neither.
            `wx-reply` is `pic xxx value spaces` [purchase/pl100.cbl:L157] and
            [L305] re-fills it with spaces immediately before the accept, so
            pressing return leaves it blank, [L310-L311] fires and control
            returns to `acpt-xrply.` [L302] - for ever.  [L313] is
            UNREACHABLE on a blank answer, so inferring `"YES"` from silence
            authorised every `OTM5-Rewrite`, every `Purch-Rewrite`, the GL
            batch family and the `PL-Payments` period total on an answer the
            compiled program never accepts.  Requiring the keyword removes the
            inference rather than replacing it with the opposite one: the
            caller must state the answer, as the operator must type it.  The
            same change is made to the Sales twin `sl100`, whose paragraph is
            character-for-character the same decision.

    Returns:
        None.  `pl100` is a COBOL sub-program; it communicates only through
        the mutated linkage records and the database.
    '''
    state = _Pl100State(
        ws_calling_data=ws_calling_data,
        system_record=system_record,
        system_record_4=system_record_4,
        to_day=to_day,
        file_defs=file_defs,
        ok_to_post=ok_to_post,
        # `None` and `{}` are the same thing - no declaration - and both leave
        # every handler at its fail-closed default.
        dal_options=dict(dal_options) if dal_options else {},
    )
    # NO ENTRY OR EXIT RECORD.  `pl100` is a `CALL`ed sub-program: the COBOL
    # displays nothing on entry and nothing at [L467-L468] on the way out, so
    # both events would be output the compiled program never produced (R-4).
    # Each also carried data the safe-event schema in `acas_posting/dal/status.py`
    # excludes (CWE-532) - the caller name and the run date on the way in, the
    # batch item count and two accumulated deduction amounts on the way out.
    #
    # AND THE ENTRY RECORD WAS A FAILURE PATH THAT LOGGING MUST NOT ADD.  Its
    # `movelib.move(...)` argument was evaluated BEFORE the logging module
    # decided whether the record was wanted, so a value the receiving picture
    # could not hold would have raised from inside a disabled diagnostic.
    # Removing the operand removes the risk outright, which no `isEnabledFor`
    # guard can do.
    #
    # `init01 section.` [L272] is the program's first executable section, so
    # control enters there and reaches every other section by PERFORM or by
    # fall-through.
    _init01(state)


# ==========================================================================
# --- traceability ---
# ==========================================================================
# Required by R-5 (plan section 0.7.2): every program maps to a module, every
# paragraph to a function, every field to a data-dictionary entry.  Plan
# section 0.7.4 C-4 additionally requires that "every paragraph retains a
# named function even where its `GO TO` becomes a `continue`, a `break` or a
# `return`", and that deliberate omissions be "recorded as omissions ... so
# that a reader comparing the two files does not conclude something was lost".
#
# PROGRAM -> MODULE
#   purchase/pl100.cbl  ->  acas_posting/programs/pl100_payment_posting.py
#   Boundary: THE WHOLE PROGRAM (unlike gl051 and irs030, which are partial).
#
# --------------------------------------------------------------------------
# LABEL -> FUNCTION.  29 labels, 29 functions.  `main-exit.` occurs FIVE
# times, so every name is SECTION-QUALIFIED - paragraph names are not
# globally unique in this codebase.
# --------------------------------------------------------------------------
#   L272  init01 section.              -> _init01
#   L296  menu-return.                 -> _init01__menu_return
#   L302  acpt-xrply.                  -> _init01__acpt_xrply
#   L323  loop.                        -> _init01__loop
#   L349  cust-update.                 -> _init01__cust_update
#   L427  main-end.                    -> _init01__main_end
#   L467  menu-exit.                   -> _init01__menu_exit
#   L470  headings.                    -> _init01__headings          (PERFORM-only)
#   L488  compute-purch-pay.           -> _init01__compute_purch_pay (PERFORM-only)
#   L507  csp-exit.                    -> _init01__csp_exit          (PERFORM-only)
#   L510  analise-deductions section.  -> _analise_deductions
#   L539  main-exit.        (1 of 5)    -> _analise_deductions__main_exit
#   L541  bl-open section.             -> _bl_open
#   L574  main-exit.        (2 of 5)    -> _bl_open__main_exit
#   L577  bl-write section.            -> _bl_write
#   L657  main-exit.        (3 of 5)    -> _bl_write__main_exit
#   L660  bl-close section.            -> _bl_close
#   L679  main-exit.        (4 of 5)    -> _bl_close__main_exit
#   L681  Eval-Status section.         -> _eval_status
#   L687  main-exit.        (5 of 5)    -> _eval_status__main_exit
#   L689  zz050-Validate-Date section. -> _zz050_validate_date       (NEVER performed)
#   L716  zz050-test-date.             -> _zz050_test_date           (NEVER performed)
#   L721  zz050-exit.                  -> _zz050_exit                (NEVER performed)
#   L724  zz060-Convert-Date section.  -> _zz060_convert_date
#   L756  zz060-Exit.                  -> _zz060_exit
#   L759  zz070-Convert-Date section.  -> _zz070_convert_date
#   L786  zz070-Exit.                  -> _zz070_exit
#   L789  maps04 section.              -> _maps04
#   L794  maps04-exit.                 -> _maps04_exit
#   -- public entry --                 -> run   (the only exported name)
#   -- support, no COBOL label --      -> _local, _alpha_eq, _initial,
#      _fresh_oi_header, _is_g_l, _is_irs_used, _is_irs_both_used,
#      _oi_supplier_image, _maps04_wrapper, _Pl100State
#
# --------------------------------------------------------------------------
# `GO TO` CLASSIFICATION - 19 SITES, MEASURED.  Classified by SHAPE, per the
# four-class taxonomy of plan section 0.4.2, not by matching a label list.
# --------------------------------------------------------------------------
#   CLASS 1 - loop-back -> `continue` inside `while True:`   (5 sites)
#     L331 -> loop L323   the type filter rejects the record
#     L340 -> loop L323   after the type-2 average + OTM5 rewrite
#     L344 -> loop L323   supplier closed, or type 2
#     L347 -> loop L323   no batch linkage
#     L425 -> loop L323   end of a posted item
#   CLASS 2 - forward terminator -> `break` PLUS the post-loop block  (1 site)
#     L326 -> main-end L427   on `fs-reply = 10` (end of the OTM5 walk).
#     Plan section 0.6.3: the transformation is "`break` PLUS faithful
#     placement of that work after the loop, not `break` alone.  Mis-splitting
#     here would silently drop end-of-run processing."  The post-loop work at
#     [L430-L465] contains BOTH file closes, the [L448] total merge, the
#     ENTIRE deduction reversal, `bl-close`, and TWO `SYSTEM-REC` writes -
#     every one a real database effect.
#   CLASS 3 - section/paragraph exit -> `return`             (9 sites)
#     L293 -> menu-exit L467          the p-flag-p latch refusal
#     L309 -> menu-exit L467          the run-confirm answered NO
#     L492 -> csp-exit L507           oi-date-cleared is zero
#     L517 -> main-exit L539          "Pzb" not found
#     L531 -> main-exit L539          "Pz " not found
#     L736 -> zz060-Exit L756         u-date is spaces
#     L742 -> zz060-Exit L756         Date-UK short-circuit
#     L747 -> zz060-Exit L756         after the USA swap
#     L772 -> zz070-Exit L786         Date-UK short-circuit
#     L777 -> zz070-Exit L786         after the USA swap
#     (L736/L742/L747 and L772/L777 are reproduced inside the consolidated
#      `dates` helpers, which the wrapper sections delegate to.)
#   CLASS 4 - sibling re-dispatch -> named call + explicit transfer  (3 sites)
#     L311 -> acpt-xrply L302   PER-SITE PROOF: the target re-asks the
#       run-confirm, and the confirm GATES EVERY DATABASE WRITE, so the site
#       is inside the migrated surface rather than out of scope.  The COBOL
#       loops until the reply is exactly "YES" or "NO"; the reply becomes the
#       `ok_to_post` parameter, whose domain is already exactly those two
#       outcomes, so the retry has no reachable iteration and collapses.  The
#       collapse is a PRESENTATION-REMOVAL CONSEQUENCE, not a behaviour
#       change: for every input the COBOL could terminate on, the Python takes
#       the same branch, performs the same opens, and writes the same rows.
#       The `while True:` shape is retained in `_init01__acpt_xrply` so the
#       transfer remains visible.
#     L702 -> zz050-test-date L716   Date-UK reaches the shared tail
#     L707 -> zz050-test-date L716   the USA swap reaches the shared tail
#       (both inside the consolidated `dates.zz050_validate_date`, which calls
#        `dates.zz050_test_date` for that tail)
#
# FALL-THROUGHS - reproduced as explicit calls, both recorded because COBOL
# paragraph fall-through is invisible at the call site:
#   [L294] end of the latch gate -> menu-return.  L296
#   [L347] end of the filter cascade -> cust-update.  L349
#   (also, within sections: L537->L539, L572->L574, L655->L657, L677->L679,
#    L685->L687, L465->L467, L505->L507)
#
# `PERFORM ... THRU` - ONE OF ONLY FOUR IN-SCOPE SITES REPO-WIDE.  The others
# are [general/gl072.cbl:L300], [general/gl072.cbl:L304] and
# [sales/sl100.cbl:L344].  (The plan says seven; four is the measured
# in-scope count - gl051 L504/L955 and irs030 L813/L831/L832 fall outside the
# migrated boundaries.)  Plan section 0.4.2: "each is transformed by hand into
# an explicit sequence of calls and verified individually, with no
# pattern-matching shortcut."
#   [L336]  perform compute-purch-pay thru csp-exit
#     span   = [L488] compute-purch-pay.  ->  [L507] csp-exit.
#     labels = exactly two, so the expansion is:
#                  _init01__compute_purch_pay(state)
#                  _init01__csp_exit(state)
#              in that order, with [L492]'s `go to csp-exit` becoming an early
#              `return` from the first (Class 3).  `csp-exit`'s body is
#              [L508] `exit.` - a PLAIN `EXIT`, a no-op statement, NOT
#              `exit section.` - so the second call really does nothing, and
#              that is why it is written as an empty function rather than
#              dropped.
#
# --------------------------------------------------------------------------
# ANOMALIES REPRODUCED (R-4: "a defect reproduced is correct; a defect fixed
# is a failure").  EIGHT sites, each carrying a locator and `DO NOT FIX`.
# --------------------------------------------------------------------------
#   A-NEW-5  [L566-L570]  in _bl_open - a MUTUALLY EXCLUSIVE `IF ... ELSE`
#            where every sibling uses two independent `IF`s, `irs-used` tested
#            WITHOUT `IRS-Both-Used`, and NO open-output fallback.  Writes to
#            unopened tables in BOTH IRS modes.  Control:
#            [purchase/pl060.cbl:L907-L920].  UNREGISTERED - discovered here.
#   A-NEW-6  [L356-L361], [L405]  in _init01__cust_update - no supplier is
#            ever created (no `Purch-Write` exists in the program), yet
#            `Purch-Rewrite` is issued unconditionally.  Control:
#            [purchase/pl060.cbl:L436-L440], [purchase/pl060.cbl:L515-L519].
#   A-NEW-7  [L449]  in _init01__main_end - the whole deduction reversal is
#            gated on `t-deduct` ALONE, so `n-deduct` can drift permanently.
#   A-1      [L675]  in _bl_close - THE CONTROL CASE: the period IS present,
#            so [L676] is a SIBLING `if` and `GL-Posting-Close` IS reached in
#            pure-GL mode.  The defective sibling is [sales/sl060.cbl:L1176].
#   A-10     [L495], [L497], [L500-L502]  in _init01__compute_purch_pay -
#            VARIANT (d) of four mutually inconsistent moving-average idioms.
#            Peers: [purchase/pl060.cbl:L743] (a), [purchase/pl060.cbl:L758]
#            (b), [sales/sl100.cbl:L506] (c).  ⭐ A-8 DOES NOT APPLY HERE.
#   A-17     [L672]  in _bl_close - `move RRN to postings.  *> Why ?`, the
#            maintainer's own question mark.  Occurrence 4 of 4, and
#            LOAD-BEARING via [L564] -> [L572].
#   A-18     [L615-L616], [L640-L641]  in _bl_write - `dr-pc`/`cr-pc` dropped
#            from the IRS record; `31` moved with `*> IS IT ???`.
#   A-21     [L617], [L626], [L631]  in _bl_write - qualified references
#            forced by copybook field-name collisions.
#   NOT PRESENT IN THIS FILE, recorded so a reader does not hunt for them:
#     A-8  (double truncation) - both accumulators here are integer
#          `binary-long` day counts, so there is only ONE truncation.
#     A-22 (wrapper/exit name disagreement) - `maps04` L789 and `maps04-exit`
#          L794 AGREE.  A-22 is at [general/gl070.cbl:L603-L609] and
#          [general/gl051.cbl:L1273]/[general/gl051.cbl:L1278].
#     A-6  (the always-refused rewrite verb, [common/acas008.cbl:L299-L307])
#          is never triggered: `SPL-Posting-Rewrite` is not called here.
#
# --------------------------------------------------------------------------
# FINDINGS - divergences and oddities recorded but not classified as
# registered anomalies.
# --------------------------------------------------------------------------
#   F-1  [L621]  an INERT store: `move spaces to post-vat-side` is overwritten
#        by `"DR"` at [L627] before any write.  Same pattern at
#        [sales/sl100.cbl:L639]/[L645].  Reproduced, not optimised away.
#   F-2  [L537]  ASYMMETRY: no `move 1 to File-Key-No` precedes the second
#        `Value-Rewrite`, where [L524] precedes the first.
#   F-3  [L612-L613]  the DR/CR sides are SWAPPED relative to
#        [purchase/pl060.cbl:L958-L959], and the account is `bl-pay-ac`, not
#        `bl-purch-ac`.
#   F-4  [L617], [L623-L624]  `vat-ac` is ZEROED where
#        [purchase/pl060.cbl:L966-L967] copies it, and only TWO control totals
#        are accumulated where [purchase/pl060.cbl:L973-L976] accumulates
#        FOUR.  A payment posting carries no VAT.
#   F-5  [L546], [L548]  the field is `bl-next-batch`, a DIFFERENT
#        `SYSTEM-REC` column from the `next-batch` that
#        [purchase/pl060.cbl:L885-L887] uses.
#   F-6  §541/§577/§660  the sections are declared LOWER CASE (`bl-open`,
#        `bl-write`, `bl-close`) yet performed as `BL-Open` [L317], `BL-Write`
#        [L410], `bl-close` [L455] and `bl-close`/`bl-open` [L654-L655].
#        COBOL is case-insensitive; the inconsistency is recorded.
#   F-7  [L670]  the `accept` is NOT wrapped in `if WS-Caller not = "xl150"`,
#        unlike [purchase/pl060.cbl:L1022-L1025] - the unattended-mode branch
#        is simply absent.
#   F-8  [L671]  the comment reads `*> THIS IS IN PURCHASE PL060` - inside
#        pl100.  A copy-paste artefact present in four files:
#        [sales/sl060.cbl:L1172], [purchase/pl060.cbl:L1027],
#        [sales/sl100.cbl:L690], [purchase/pl100.cbl:L671].
#   F-9  [L468]  the program ends with `exit program.`, not `goback`.
#   F-10 [L689-L722]  `zz050-Validate-Date` is DECLARED but NEVER PERFORMED -
#        `grep -c "perform *zz050"` returns 0.  Dead code that R-5 still
#        requires a named function for.
#   F-11 [L369]  `move u-date to l5-date` uses `u-date`, where
#        [purchase/pl060.cbl:L448] uses `ws-date`.  Presentation only, but the
#        field choice is reproduced.
#   F-12 [L356]  the unknown-supplier test is `fs-reply = 21`, where
#        [purchase/pl060.cbl:L433] tests `not = zero`.
#   F-13 [L386-L389]  the sign flip uses the `GIVING` form, so `purch-current`
#        is NOT mutated by the multiply and is zeroed separately at [L389];
#        [purchase/pl060.cbl:L507] uses the no-`GIVING` form, which DOES
#        mutate it.  Net effect equal, intermediate not.
#   F-14 [L634], [L636], [L638]  the IRS receivers are one digit NARROWER than
#        the GL senders (`9(6)`->`9(5)`, `s9(8)v99`->`s9(7)v99`), so a
#        six-digit account or a nine-digit amount loses its high-order digit.
#   F-15 [L640-L641]  the second receiver of the `move 31` is `Vat-PC` on the
#        GL POSTING record, written from inside the IRS block, over the zero
#        [L618] had just stored.  So `GLPOSTING-REC.VAT-PC` is 0 in pure-GL
#        mode and 31 in either IRS mode - the IRS switch changes a GL column.
#   F-19 [L591-L592]  `post-date` is built from `u-date`, which holds the
#        OPEN-ITEM date [L367-L368] unpacked from `oi-date` - NOT the run date.
#        `to-day` never reaches the posting record at all.  Verified at run
#        time: oi-date 155000 -> post-date "17/05/25" for a run of 31/12/2025.
#   F-16 [L653-L655]  the 99-item cap re-performs `bl-open`, so every reopen
#        repeats A-NEW-5 in full.
#   F-17 [L316-L317], [L409-L410], [L454-L455]  ALL THREE `bl-*` sections are
#        gated on `G-L` ALONE, consistently, so with `G-L` unset none of them
#        runs and the IRS fan-out inside `bl-write` NEVER EXECUTES - the IRS
#        switch is inert unless the General Ledger is also enabled.  Verified
#        by driving the "B"-mode-with-`G-L`-unset case: zero batch and zero
#        posting verbs are reached.  This is NOT a pl100 divergence:
#        [purchase/pl060.cbl:L405-L406], [purchase/pl060.cbl:L474-L475] and
#        [purchase/pl060.cbl:L573-L574] gate identically, so it is a
#        codebase-wide property of the purchase posting family.  Recorded
#        because the coupling is invisible from `bl-write`'s own predicates,
#        which name `irs-used`/`IRS-Both-Used` as though they were sufficient.
#   F-18 [L671]/[L674]/[L676]  SIX IRS fan-out sites where `sl060`, `sl100`
#        and `pl060` each have SEVEN, and [L566]'s predicate disagrees with
#        [L629]'s.  Not harmonised across programs.
#
# --------------------------------------------------------------------------
# AMBIGUITIES referred to the compiled oracle (R-6).  Five sites, each marked
# `# AMBIGUITY Q-n` at its location.
# --------------------------------------------------------------------------
#   Q-1  _bl_open  - the status pair and row state produced by A-NEW-5's write
#        to an unopened table, in "Y" mode, in "B" mode, and with `G-L` unset.
#   Q-2  _init01__cust_update - the `PULEDGER-REC` state produced by
#        A-NEW-6's rewrite of a record that was never successfully read.
#   Q-3  _init01__main_end - the `VALUEANAL-REC` count drift from A-NEW-7, and
#        whether the unsigned count columns underflow or clamp.
#   Q-4  _bl_write - the exact `post-date` text the century-dropping
#        reference modification at [L591-L592] yields per `Date-Form`.
#   Q-5  _init01__compute_purch_pay - the stored value of `purch-pay-average`
#        if the bridge narrows a signed `binary-long` to an unsigned column.
#
# --------------------------------------------------------------------------
# OMISSIONS - deliberate, and recorded so nothing looks lost.
# --------------------------------------------------------------------------
#   O-1  [L446]  `call "SYSTEM" using Print-Report` - the spool-out path,
#        which plan section 0.1.1 EXPLICITLY excludes.  Omitted entirely.
#        ⭐ This is the ONLY non-migratable `call` in the program: pl100 has
#        NO `call "CBL_*"` library calls and NO `FS-Cobol-Files-Used`-gated
#        library block at all, unlike pl055 (`call "sl070"`), pl060 (four
#        `CBL_*` calls) and sl060.  Do not go looking for one.
#   O-2  The ENTIRE PRINT FILE: `open output print-file` [L319], `close
#        print-file` [L445], every `write print-record` ([L420], [L438],
#        [L444], [L484-L485]), the `line-1`..`line-5` layouts [L221-L256],
#        `j`, `l1-name`, `l1-page`, `l2-date`, `l2-user`, `Print-Spool-Name`,
#        `PSN`, and `copy "selprint"` [L115] / `"fdprint"` [L122] /
#        `"print-spool-command"` [L127].  `headings` [L470] SURVIVES as a
#        named log-only function because R-5 requires it, and `line-cnt` is
#        still maintained because [L422] tests it.
#   O-3  `display ... at` -> A LOG RECORD, BUT NOT ALL OF IT.  Plan section 0.3.4
#        converts a DIAGNOSTIC display, and such records "must not alter control
#        flow and must not appear in any table dump" - none of these does.
#        CONVERTED: [L290] (`PL137`), [L298-L299] (the banner) and [L665-L668]
#        (the batch-write failure with its file status, we-error and the decoded
#        status name).  NOT CONVERTED, each for a stated reason:
#          - [L291] and [L669] - `PL002`.  PURE ACKNOWLEDGEMENT PROMPTS standing
#            immediately before the `accept ws-reply`s of O-4; the whole of the
#            literal is the key-press instruction, so nothing substantive is lost.
#            `P-Flag-P`, which the [L290] record once narrated, is a SYSTEM-REC
#            host-variable value and is excluded by the safe-event schema in
#            `acas_posting/dal/status.py` (CWE-532) - and the frozen display shows
#            the literal alone in any case.
#          - [L301] - `display ws-date`.  THE POSTING DATE IS BUSINESS DATA,
#            excluded by the same schema; it is a command-line INPUT that
#            `clock.py` pins.
#          - [L303-L304] - the run-confirm PROMPT.  It is the screen text for the
#            `accept wx-reply` that O-4 resolves into the `ok_to_post` parameter,
#            so reproducing it would log a question no one can answer, and echoing
#            the answer would restate a command-line argument.
#        Nothing from `01 line-1`..`line-5` is logged either: [L433-L444] (the two
#        total blocks) and [L472-L473] (the page number and the operator identity)
#        are report content, out of scope per plan section 0.2.2, and the amounts
#        and user identity they carry are excluded by the safe-event schema.
#        `run()` emits NO entry or exit record: the COBOL displays nothing on
#        either boundary, so both would be invented output (R-4).
#   O-4  `accept wx-reply` [L306] -> the explicit `ok_to_post` parameter of
#        `run()`, because it GATES A DATABASE WRITE.  That parameter carries NO
#        default: [L157], [L305] and [L310-L311] leave the frozen prompt with
#        none, so section 0.3.4's "with the COBOL default preserved" has nothing
#        to preserve and the answer is required of the caller.  `accept ws-reply` [L292]
#        and [L670] -> DROPPED as acknowledgement pauses; but [L293]'s
#        `go to menu-exit` control transfer IS PRESERVED.
#   O-5  `set ENVIRONMENT` [L276-L277] and `copy "envdiv.cob"` [L108] -
#        representation only.
#   O-6  `01 Dummies-4-Unused-ACAS-FH-Calls.` [L133] - pl100 declares the
#        group but NO facade stub block of the kind [general/gl072.cbl:L135]
#        and [general/gl080.cbl:L194] carry; Python needs no linker
#        satisfaction either way.  Maps to nothing.
#   O-7  The message literals.  `PL132` [L207] and `PL137` [L208] survive as log
#        text.  `PL002` [L204] is DECLARED AND DELIBERATELY NEVER REFERENCED - it
#        is the acknowledgement prompt of O-3 - and stays declared because rule
#        R-5 maps the whole `01 Error-Messages.` group.
#   O-8  The local print totals `t-approp`, `j-approp`, `j-paid` and
#        `j-deduct` are still COMPUTED - [L396] and [L448] consume them - but
#        their print lines are omitted.  `t-paid`, `t-deduct` and `n-deduct`
#        are LOAD-BEARING: `t-paid` receives period total 9 alongside
#        `pl-payments`, and `t-deduct`/`n-deduct` drive [L449] and the whole
#        of `analise-deductions`.
#   O-9  Absent facade verbs, stated so a reader does not expect them: NO
#        `GL-Posting-Open-Output`, NO `SPL-Posting-Open-Output` (that absence
#        IS A-NEW-5 defect (c)), NO `Purch-Write` (that absence IS A-NEW-6),
#        NO `OTM5-Start` and NO `set fn-*` anywhere - the OTM5 walk is purely
#        sequential from the top, with no cursor positioning at all.
#   O-10 NO WORK FILE.  pl100 declares no `seloi4`/`fdoi4` and no
#        `plwsoi`/`plwssoi`, unlike pl055/pl060 which share OTM4.  Nothing
#        imports `acas_posting.workfiles`.
#   O-11 ZERO `ROUNDED` sites.  Every store in this program truncates toward
#        zero.  The migration's five `ROUNDED` sites are
#        [general/gl051.cbl:L791], [general/gl051.cbl:L796],
#        [general/gl080.cbl:L328], [irs/irs030.cbl:L1551] and
#        [irs/irs030.cbl:L1562].
#   O-12 `copy "FileStat-Msgs.cpy"` [L684-L685] - the message text is taken
#        from `dal.status.FsReply` rather than duplicating the copybook's
#        literal table; the rendering is diagnostic and reaches no table.
#
# --------------------------------------------------------------------------
# FIELD -> DICTIONARY ENTRY.  Every `FieldDescriptor` above is built either
# by `FieldDescriptor.from_dictionary_key(...)` - so it carries a
# `dictionary_key` resolved from `data_dictionary/acas_posting_dictionary.json`
# - or by `_local(...)`, which stamps a `source_locator` of the form
# `purchase/pl100.cbl:L<n>` naming the working-storage line it was read from.
# `_OI_*_D` descriptors come from `records.otm5.descriptors_of`, which carries
# the copybook's own dictionary keys.  No descriptor is hand-built.
# --------------------------------------------------------------------------
# --- end traceability ---
