"""`sl055` - the Sales Invoice Post Extract and analysis-total build  [sales/sl055.cbl].

The migration of `sales/sl055.cbl` in its entirety. Boundary: THE WHOLE PROGRAM -
unlike `gl051`, whose control-total gate alone is in scope, and `irs030`, whose
`Ledger-Postings-Add` section alone is in scope, nothing here is excluded.

`sl055` walks the sales invoice file once and does four things with it:

  1. Accumulates VALUE-ANALYSIS totals per analysis group from the invoice LINE
     records - a count and a value, this period and this year - creating an
     emergency `ANALYSIS-REC` when a line names a group that does not exist.
  2. Extracts each not-yet-applied invoice HEADER into the OTM2 open-item work
     file, negating every money field for a credit note.
  3. Adds the invoice or credit-note total into the SALES PERIOD TOTALS on
     `SYSTOT-REC` - two of the nine period-total write sites in the whole
     migration, and the only two writers of those two columns.
  4. Stamps the invoice header as analysed and applied, and rolls four special
     totals - VAT, VAT-on-receipts, carriage and discount - into four reserved
     value-analysis groups at end of run.

THE FIRST SALES/PURCHASE MODULE, AND IT IS NOT A GENERAL LEDGER MODULE
======================================================================
Three things differ from the General Ledger family immediately, and each is a
trap for anyone arriving from `gl070`/`gl071`/`gl072`:

  * THE LINKAGE HAS FIVE PARAMETERS, not four, and the third is `SYSTOT-REC`.
    See THE LINKAGE, VERBATIM in `run`.
  * THE SIGN-FLIP VERB FORM IS `MULTIPLY -1 BY x` WITH NO `GIVING`, so the
    RECEIVER IS THE SECOND OPERAND. `gl070` writes
    `multiply pre-amount by -1 giving pre-amount.` - operands reversed AND with
    `GIVING`. Copying the General Ledger form here would multiply the wrong way
    round. All twelve sites are listed in THE ARITHMETIC CENSUS below.
  * THE MAIN LOOP IS A STRUCTURED INLINE `PERFORM UNTIL`, not a `GO TO` cycle.
    See THE CONTROL SHAPE below.

THE CONTROL SHAPE - TWO NESTED LOOPS, AND THE OUTER ONE IS A `GO TO`
====================================================================
This is the single most important thing to understand before reading any
function body, because getting it wrong misplaces every statement in the file.

`da010-Read-Loop.` [sales/sl055.cbl:L364] is a paragraph that contains an
INLINE `PERFORM UNTIL ... END-PERFORM` [sales/sl055.cbl:L365-L424], carrying the
maintainer's own comment "changed 18/01/25 for clean up using inline perform".
That inline perform is the ITEM-LEVEL loop: it reads invoice records and
accumulates value analysis from the LINE records. It leaves in three ways -

    L367-L368   if fs-reply = 10 -> go to da040-Close-Files   (out of the
                inline perform entirely; GnuCOBOL permits it)
    L370-L371   if ih-test = zero -> exit perform, and control then FALLS
                THROUGH to da020-Header-Analysis. [sales/sl055.cbl:L426]
    L365        the `UNTIL FS-Reply = 10` condition itself, evaluated at the top
                of each iteration, which also falls through to L426

- and it iterates through five `exit perform cycle` statements at L374, L377,
L403, L409 and L423.

`da020-Header-Analysis.` [sales/sl055.cbl:L426] is the HEADER-LEVEL processing,
and it ends with `go to da010-Read-Loop.` [sales/sl055.cbl:L470], re-entering
the paragraph and restarting the inline perform. THAT is the outer loop. Three
further transfers return to the same label - L428, L442 and L479 - so the outer
loop has four back-edges and the inner loop has five.

    outer loop  ->  da010-Read-Loop  (paragraph)
                        inner loop   ->  perform until FS-Reply = 10
                                             ... exit perform cycle x5
                                         end-perform
                    da020-Header-Analysis
                    da030-Skip-Invoice
                    back to da010-Read-Loop, or out to da040-Close-Files

The transcription below is a real `while` for the inner loop - it is already a
`while` in the source and is written as one here, not rebuilt as a `GO TO`
cycle - inside a real `while True` for the outer one. Every transfer site
carries a `# GO TO class N` annotation, and every `EXIT PERFORM` site carries
its own, because the six `EXIT PERFORM`s are not `GO TO`s and must not be
counted as any of the four classes.

WHY THE `UNTIL` AND THE L367 TEST ARE BOTH REPRODUCED
=====================================================
The loop tests `FS-Reply = 10` twice: once as its own `UNTIL` condition
[sales/sl055.cbl:L365] and once explicitly immediately after the read
[sales/sl055.cbl:L367]. Belt and braces - but NOT redundant, and the difference
is observable. `Fs-Reply` is a SINGLE SHARED FIELD [copybooks/wsfnctn.cob:L25]
written by every file operation, so the six facade verbs the loop body performs
AFTER the read - `Value-Read-Indexed` twice, `Value-Write`, `Value-Rewrite`
twice and `Invoice-Rewrite` - each overwrite it. The explicit L367 test sees the
READ's status; the `UNTIL` at the top of the next iteration sees whatever the
LAST verb of the previous iteration left. Those are different values, and they
lead to different places: L368 transfers to `da040-Close-Files`, whereas the
`UNTIL` falling false lets control fall through to `da020-Header-Analysis` with
a STALE record in the invoice area. Both paths are reproduced, separately.

THE PRODUCER / CONSUMER CHAIN
=============================
`sl055` is the first half of the sales invoice posting cycle. `sales.cbl`
dispatches it and then `sl060`:

    756  load07.             *> Sales trans posting
    763      move     "sl055" to ws-called.
    764      perform  load000.
    765      if       ws-term-code not = zero
    766               go to display-menu.
    767      move     "sl060" to ws-called.
    768      go       to load000.

THE ABORT GATE IS `not = zero`, WHICH IS NEITHER THE GENERAL LEDGER'S NOR
PURCHASE'S. `general.cbl` gates its posting cycle on `ws-term-code = 5`;
`purchase.cbl` has no gate at all between `pl055` and `pl060`; here ANY non-zero
term code stops the cycle before `sl060` runs. And `sl055`'s own abort value is
EIGHT - `move 8 to WS-Term-Code` [sales/sl055.cbl:L344] - not the General
Ledger's five, which matters because the shared dispatcher `load000.`
[sales/sales.cbl:L698] treats the two bands differently: `if ws-term-code < 8`
[sales/sales.cbl:L708] rewrites the system records, and `if ws-term-code > 7`
[sales/sales.cbl:L710-L712] rewrites them AND `goback`s out of the menu
altogether. Eight therefore terminates the whole sales menu, not just the cycle.

That same dispatcher paragraph is why this program's mutations of its second and
third parameters are DIFF-VISIBLE. `overrewrite.` writes `System-Record` and
`WS-System-Record-4` back after every dispatch, so both the two period totals
this program adds into [sales/sl055.cbl:L675], [sales/sl055.cbl:L677] and the
`Date-Form` default this program sets [sales/sl055.cbl:L704-L705] reach the
database even though `sl055` never rewrites either record itself.

The OTM2 work file this program writes is `sl060`'s input - `sl060` copies the
same `seloi2.cob`, `fdoi2.cob` and `slwsoi.cob` trio. The handoff is through the
work file, exactly as in COBOL, so this module does NOT import `sl060` and
`sl060` does not import this one; the CLI sequences the two calls.

THE ARITHMETIC CENSUS - MEASURED, NOT ESTIMATED
===============================================
Over the comment-stripped source. ZERO `ROUNDED`, ZERO `ON SIZE ERROR`, ZERO
`REMAINDER`, ZERO `DIVIDE`, ZERO `COMPUTE`, ZERO `PERFORM ... THRU` and ZERO IRS
fan-out tests. Every store in this program TRUNCATES toward zero, which is
`acas_posting.cobol.arithmetic`'s default and is why the `rounded` keyword is
never set true anywhere below - it is left at its default at every call.

    L314  subtract 1 from ws-lines giving ws-23-lines        screen geometry, omitted
    L388  add 1 to VA-T-This            L389  add 1 to VA-T-Year
    L391  add il-net to VA-V-This       L392  add il-net to VA-V-Year
    L394  subtract il-net from VA-V-This
    L395  subtract il-net from VA-V-Year
    L411  add 1 to VA-T-This            L412  add 1 to VA-T-Year
    L414  add il-net to VA-V-This       L415  add il-net to VA-V-Year
    L417  subtract il-net from VA-V-This
    L418  subtract il-net from VA-V-Year
    L444  add ih-c-vat ih-vat ih-e-vat giving work-2         3-addend variadic
    L446  multiply -1 by work-2                              SIGN FLIP 1
    L449  add 1 to ws-vat-totalt        L450  add work-2 to ws-vat-totalv
    L453  add 1 to ws-vatr-totalt       L454  add work-2 to ws-vatr-totalv
    L457  multiply -1 by work-2                              SIGN FLIP 2
    L459  add 1 to ws-carr-totalt       L460  add work-2 to ws-carr-totalv
    L463  multiply -1 by work-2                              SIGN FLIP 3
    L465  add 1 to ws-disc-totalt       L466  add work-2 to ws-disc-totalv
    L473  add 1 to invoice-nos
    L601  add work-3 to VA-T-This       L602  add work-3 to VA-T-Year
    L603  add work-2 to VA-V-This       L604  add work-2 to VA-V-Year
    L617  add work-3 to VA-T-This       L618  add work-3 to VA-T-Year
    L619  add work-2 to VA-V-This       L620  add work-2 to VA-V-Year
    L658-L666  nine x  multiply -1 by oi-...                 THE NINE-FIELD BLOCK
    L671-L673  add ih-net ih-extra ih-carriage ih-discount ih-vat ih-c-vat
               ih-e-vat ih-deduct-amt ih-deduct-vat giving ws-inv-amt
                                                             NINE ADDENDS
    L675  add ws-inv-amt to sl-invoices-this-month            PERIOD TOTAL 1
    L677  add ws-inv-amt to sl-credit-notes-this-month        PERIOD TOTAL 2

`SUBTRACT a FROM b` with no `GIVING` is `b = b - a`. `MULTIPLY a BY b` with no
`GIVING` is `b = a * b`. Both directions are easy to invert by accident and both
are asserted at every site below.

`pl055` IS NOT A MIRROR OF THIS PROGRAM  (rule R-4)
===================================================
The Purchase counterpart looks like a translation of this file and is not one.
The differences are arithmetic, not cosmetic, and NEITHER SIDE MAY BE
NORMALISED TOWARD THE OTHER:

    negation block   sl055: NINE fields  [sales/sl055.cbl:L658-L666]
                     pl055: FOUR fields  [purchase/pl055.cbl:L571-L575]
                            (oi-net, oi-carriage, oi-vat, oi-c-vat only)
    invoice sum      sl055: NINE addends [sales/sl055.cbl:L671-L673]
                     pl055: FOUR addends [purchase/pl055.cbl:L579-L580]
                            (ih-net, ih-carriage, ih-vat, ih-c-vat only)
    header stamps    sl055: ih-status AND ih-status-A  [L679-L680]
                     pl055: ih-status only             [purchase/pl055.cbl:L586]
    paragraph names  sl055: da/db/dc/dd PREFIXED, every label unique
                     pl055: BARE - `read-loop.` [purchase/pl055.cbl:L306],
                            `header-analysis.` [L362], `close-files.` [L400],
                            `menu-exit.` [L434], `Create-Main.` [L444],
                            `Create-Anal.` [L488]
    invoice restart  sl055: `set fn-not-less-than` + `Invoice-Start` [L475-L476]
                     pl055: NO `PInvoice-Start` at all
    written record   sl055: `write oi-header.`  [L681]
                     pl055: `write open-item-record-4.` [purchase/pl055.cbl:L587]

Agent Action Plan section 0.6.1, on the three divergent moving-average blocks,
verbatim: "Normalising them into one helper would be the single easiest way to
fail this migration." The same judgement applies here, which is why the nine
negations are written out as nine statements rather than a loop over a field
list that a later reader could "share" with `pl055`.

RULES THIS MODULE IS HELD TO
============================
There is NO user rules document for this project - `review_rules` returns
exactly "No user rules provided." The six binding rules are the Agent Action
Plan's own, section 0.7.2.

R-1  NO COBOL AT RUNTIME. No `subprocess`, no `ctypes`, no `cffi`, no `cobc`,
     no reference to the comparison oracle. The one place this bites is the
     block [sales/sl055.cbl:L326-L348], which calls `CBL_CHECK_FILE_EXIST` and
     `sl070`. `sl070` is not one of the twelve in-scope programs, so there is
     no Python module to call, and R-1 forbids calling the COBOL. The block is
     gated on `if FS-Cobol-Files-Used` [copybooks/wssystem.cob:L113], which is
     FALSE in the RDBMS configuration this migration targets
     [copybooks/wssystem.cob:L116], so the GATE is reproduced faithfully and
     data-driven, and entering it raises `CobolFileSystemPathUnavailable`
     rather than being silently skipped, stubbed as a no-op, or partly
     emulated. Question Q-56.
R-2  ZERO BINARY FLOATING POINT. No `float`, no `complex`, no `round`, no bare
     `/`. Agent Action Plan section 0.3.1, verbatim: "`cobol/` contains no
     business logic and `programs/` contains no numeric primitives." So there
     is no `quantize`, no scale alignment, no packed or zoned encoding, no
     picture parsing beyond naming this program's own working-storage
     descriptors, no `MOVE` truncation, no `INITIALIZE`, no `88`-level test and
     no reference modification written here: every one of those delegates to
     `acas_posting.cobol`. The `rounded` keyword is never set true anywhere in
     this module, because this program has no `ROUNDED` site at all - the five in
     the whole migration are in `gl051`, `gl080` and `irs030`.
R-3  NO NEW VALIDATIONS, FIELDS, SCHEMA CHANGES OR CONCURRENCY. Not one `if`
     is added. Specifically NOT added: an iteration guard on the
     `db010-Create-Anal` -> `DB000-Create-Main` retry [sales/sl055.cbl:L585];
     a retry or abort after the failed `write oi-header`
     [sales/sl055.cbl:L682]; a consistency check between the negated `oi-`
     fields and the un-negated `ih-` sum; a bounds check on
     `il-product (1:1)`. The nine `move 1 to File-Key-No` statements and the
     repeated indexed re-reads are left exactly as many as they are - section
     0.8.4, verbatim: "Any performance work is therefore out of scope by
     construction, not merely unrequested." No threads, no `asyncio`, no
     pooling.
R-4  LEGACY ANOMALIES REPRODUCED, NEVER FIXED. Section 0.8.2, verbatim: "There
     is no test suite: compiled COBOL execution is the behavioral
     specification, defects included. A defect reproduced is correct; a defect
     fixed is a failure." Each reproduction site carries a comment naming the
     defect and its locator, per section 0.7.4 conflict C-4.
R-5  FULL TRACEABILITY. A named function for every one of the EIGHTEEN labels
     in this program's procedure division, including the two the Agent Action
     Plan's section 0.4.2 inventory omits - `dc000-Store-Specials section.`
     [sales/sl055.cbl:L590] and `a01-exit.` [sales/sl055.cbl:L729]. Every one
     of the eighteen `GO TO` sites annotated with its class, every one of the
     six `EXIT PERFORM` sites annotated as such, both fall-throughs recorded,
     and the four class-4 sites each carrying an individual equivalence proof.
     The traceability footer closes the file.
R-6  COMPILED BEHAVIOUR IS THE TIE-BREAKER, AND RUNS MUST BE REPRODUCIBLE. No
     ambient clock: `sales/sl055.cbl` contains ZERO clock reads and the date
     arrives entirely through the `to-day` linkage parameter, so nothing here
     imports `acas_posting.clock`, `datetime`, `time`, `random` or `uuid`.
     `accept ws-env-lines from lines.` [sales/sl055.cbl:L308] is a
     TERMINAL-GEOMETRY read, not a clock read, and is omitted. Open questions
     are numbered `Q-` below and belong in
     `docs/migration/ambiguity-resolutions.md`.

WHAT THIS MODULE MAY IMPORT, AND WHY THE LIST IS THIS SHORT
===========================================================
Section 0.4.3 gives `programs/*.py` a closed import list: `records`,
`dal.facade`, the `cobol` semantics primitives, `dates` and `workfiles`. It may
NOT import `cli`, a `dal.acas*` handler directly, `dal.connection`,
`dal.cursor_state`, `clock`, the oracle, or another program module. Two
consequences worth stating rather than leaving to be discovered:

  * `sl055` copies `Proc-ACAS-FH-Calls.cob` [sales/sl055.cbl:L731] and NOT
    `Proc-ZZ100-ACAS-IRS-Calls.cob`, so it uses the ENTITY-named facade
    vocabulary - `Value-Read-Indexed`, `Analysis-Write`, `Invoice-Rewrite` -
    and TESTS `Fs-Reply` INLINE. That copybook has no error-check paragraph of
    any kind; the handler-named aliases are the IRS convention's and are never
    used here.
  * `sl055` does NOT copy `wsmaps03.cob` and has no `zz050`, no `zz060` and no
    date-module wrapper section - only `zz070`. So nothing here imports
    `records.maps03` or calls `dates.zz050_*`/`dates.zz060_*`/`maps04`, and
    anomaly A-22 - the wrapper section named after the interface copybook while
    its exit is named after the called program - DOES NOT OCCUR in this
    program.

AMBIGUITIES, ARBITRATED AGAINST COMPILED BEHAVIOUR  (rule R-6)
==============================================================
Numbered in the migration-wide register. Every one is recorded rather than
guessed, and the values a test asserts must come from the oracle.

Q-50  THE NEGATED `oi-` FIELDS VERSUS THE UN-NEGATED `ih-` SUM. For a credit
      note the nine `oi-` money fields are negated [sales/sl055.cbl:L657-L666]
      but the sum at [sales/sl055.cbl:L671-L673] adds the `ih-` fields, which
      were never touched. So the OTM2 row carries NEGATIVES while `ws-inv-amt`
      carries the POSITIVE total - and [sales/sl055.cbl:L677] then adds that
      POSITIVE total into `sl-credit-notes-this-month`. Reproduced exactly. The
      oracle must confirm the stored sign of that column.
Q-51  THE UNGUARDED CROSS-PARAGRAPH RETRY. `db010-Create-Anal` writes an
      emergency analysis record and jumps BACKWARD to `DB000-Create-Main`
      [sales/sl055.cbl:L585] to re-read it, with no iteration limit. Termination
      depends entirely on `Analysis-Write` making the record findable. No guard
      is added (rule R-3); the oracle must establish what the compiled program
      does when the write silently fails.
Q-52  THE FAILED `write oi-header`. [sales/sl055.cbl:L682-L689] displays a
      diagnostic and performs NO control transfer, so the loop continues with
      one record missing from OTM2, no retry and no abort - a rejection class
      with a PARTIAL effect. The oracle must establish whether the run is
      allowed to complete.
Q-53  `il-type` IS `pic x`, ALPHANUMERIC [copybooks/slwsinv2.cob:L97], yet
      [sales/sl055.cbl:L390] and [sales/sl055.cbl:L413] compare it to the
      NUMERIC literal 3. `ih-type` by contrast is `pic 9`
      [copybooks/slwsinv2.cob:L58] and its comparisons are ordinary. The
      compiled comparison is reproduced as a comparison against the CHARACTER
      "3"; the oracle must confirm.
Q-54  THE GROUP MOVE'S EFFECT ON BYTES 37 ONWARD.
      `move WS-Analysis-Record to WS-Value-Record` [sales/sl055.cbl:L538] is a
      36-byte sender into a 66-byte group receiver, so it space-fills the
      remainder - including six COMP and COMP-3 fields, which spaces are not
      valid values for. The very next statement
      [sales/sl055.cbl:L539-L540] sets all six to zero with nothing in between,
      and those six are the only columns the bridge stores from that region, so
      the space-fill is UNOBSERVABLE. Reproduced as the six picture-identical
      field copies plus the zeroing; the oracle must confirm no column differs.
Q-55  `File-Key-No` IS SET NINE TIMES AND IS ALREADY SET TWICE OVER.
      `Value-Read-Indexed` [copybooks/Proc-ACAS-FH-Calls.cob:L753-L757] sets it,
      and so does the `acas013.` dispatch paragraph. The nine explicit
      statements are therefore triply redundant. All nine are preserved in
      place (rule R-3); the oracle must confirm none is load-bearing.
Q-56  IS `FS-Cobol-Files-Used` EVER TRUE IN A SCENARIO? If it is, the block
      [sales/sl055.cbl:L326-L348] needs `sl070`, which is out of scope. See
      R-1 above and `CobolFileSystemPathUnavailable`.
Q-57  THE FACADE'S CALL SHAPE. Section 0.4.3 fixes it as `facade.<verb>(ctx)` -
      one context argument - so `_Sl055Context` below publishes the seven blocks the
      `acas013.`/`acas015.`/`acas016.` dispatch paragraphs name, under those
      names. The binding is deferred to first use and is injectable; see
      `_FacadeVerbs` and `run`.
Q-58  THE INVOICE RECORD AREA IS ONE 137-BYTE AREA WITH THREE `REDEFINES`
      VIEWS [copybooks/slwsinv2.cob:L27], [copybooks/slwsinv2.cob:L38],
      [copybooks/slwsinv2.cob:L91]. `_InvoiceRecordArea` holds the shared
      ten-byte key ONCE and the two views beside it, which is the model
      `acas_posting.dal.acas016_invoice` already adopted for the same union. The
      oracle must confirm the discriminator: `ih-test` and `Item-Nos` and
      `il-line` are the same two bytes with the same picture.
"""

from __future__ import annotations

import enum
import logging
from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from types import MappingProxyType
from typing import Final, Protocol

# copy "wsfnctn.cob".  [sales/sl055.cbl:L155]
# `01 File-Access.` [copybooks/wsfnctn.cob:L22] - `We-Error`, `Rrn`, `Fs-Reply`,
# `FS-Action`, the `Logging-Data` block that carries `File-Key-No`
# [copybooks/wsfnctn.cob:L46] and the `RDB-Data` connection block. ONE copybook
# mixes the data layout with the operation vocabulary, so the Python layering
# splits it in two: the record classes here, the status and function-code
# enumerations from `dal.status` below.
from acas_posting.records.file_access import FileAccess, LoggingData

# copy "wsval.cob".    [sales/sl055.cbl:L156]
# `01 WS-Value-Record.` [copybooks/wsval.cob:L9] - `VALUEANAL-REC`, the
# value-analysis record this program accumulates into.
from acas_posting.records.value_analysis import VaCode, VaGroup, WsValueRecord

# copy "wsanal.cob".   [sales/sl055.cbl:L157]
# `01 WS-Analysis-Record.` [copybooks/wsanal.cob:L9] - `ANALYSIS-REC`, the
# analysis-code record `db010-Create-Anal` writes an emergency entry into.
from acas_posting.records.analysis import PaGroup, WsAnalysisRecord, WsPaCode

# copy "slwsinv2.cob". [sales/sl055.cbl:L158]
# The invoice record and its two REDEFINES views - `01 Invoice-Record.`
# [copybooks/slwsinv2.cob:L27], `01 Invoice-Header redefines Invoice-Record.`
# [copybooks/slwsinv2.cob:L38] and `01 Invoice-Line redefines Invoice-Record.`
# [copybooks/slwsinv2.cob:L91]. `descriptor_for` is the module's own
# field-metadata accessor; every descriptor below comes from it rather than from
# a picture clause retyped here.
from acas_posting.records.sales_invoice import (
    IhInvoiceHeader,
    IhFig,
    IhPrime,
    IhSubPrime,
    IlInvoiceLine,
    InvoiceKey,
)
from acas_posting.records.sales_invoice import descriptor_for as _invoice_descriptor

# copy "Test-Data-Flags.cob".  [sales/sl055.cbl:L259]
# `01 ACAS-DAL-Common-Data.` [copybooks/Test-Data-Flags.cob:L6] - the fifth
# argument of every handler CALL, carrying the `SW-Testing` logging switch. Its
# defaults ARE the copybook's `value` clauses; nothing here changes them.
from acas_posting.records.test_data_flags import AcasDalCommonData

# copy "wsnames.cob".  [sales/sl055.cbl:L265]
# `01 File-Defs.` - the file-name buffers, including `file-15` (the analysis
# file, the `CBL_CHECK_FILE_EXIST` target at [sales/sl055.cbl:L327]), `file-16`
# (the invoice file) and `file-18` (`openitm2`, the OTM2 work file this program
# writes, assigned by [copybooks/seloi2.cob]).
from acas_posting.records.file_defs import FileDefs

# copy "wscall.cob".   [sales/sl055.cbl:L267]
# `01 WS-Calling-Data` [copybooks/wscall.cob:L6-L14] - the first linkage
# parameter. `WS-Caller` is read three times, at [sales/sl055.cbl:L341],
# [sales/sl055.cbl:L505] and [sales/sl055.cbl:L514]; `WS-Term-Code` is written
# once, at [sales/sl055.cbl:L344]; `WS-Process-Func` and `WS-Sub-Function` are
# written once, at [sales/sl055.cbl:L331]. `descriptor_for` supplies their
# widths - `WS-Caller` is `pic x(8)`, which is why the literal "xl150" must be
# padded before it is compared.
from acas_posting.records.calling_data import WsCallingData
from acas_posting.records.calling_data import descriptor_for as _calling_descriptor

# copy "wssystem.cob". [sales/sl055.cbl:L268]
# `SYSTEM-REC`, the 169-column system record. Two fields are read and one is
# WRITTEN: `File-System-Used` carries the `FS-Cobol-Files-Used` condition name
# [copybooks/wssystem.cob:L113] tested at [sales/sl055.cbl:L326], and
# `Date-Form` is both read and defaulted at [sales/sl055.cbl:L704-L705].
from acas_posting.records.system_record import (
    RdbmsFlatStatuses,
    SystemDataBlock,
    SystemRecord,
)

# copy "wssys4.cob".   [sales/sl055.cbl:L269]
# `SYSTOT-REC`, the period-totals record - the THIRD linkage parameter, and the
# target of this program's two period-total adds [sales/sl055.cbl:L675],
# [sales/sl055.cbl:L677].
from acas_posting.records.system_record_4 import SalesLedgerData, SystemRecord4

# copy "slwsoi.cob".   [sales/sl055.cbl:L145]
# `01 OI-Header.` [copybooks/slwsoi.cob:L8] - the 118-byte OTM2 record this
# program builds and writes. Published by `records.otm3`, which owns both the
# `slwsoi` layout and the `SAITM3-REC` one; see STRUCTURAL NOTES in the
# traceability footer for why the FILE is modelled here and the RECORD is not.
from acas_posting.records.otm3 import Filler1, Filler2, OiBatch, OiCustomer, OiHeader, OiKey
from acas_posting.records.otm3 import descriptor_for as _otm2_descriptor

# The COBOL-language semantics layer. Every arithmetic statement, every `MOVE`,
# every `88`-level test and every reference modification in this program routes
# through one of these four modules; none of that logic is written here (rule
# R-2, and section 0.3.1's division of labour).
from acas_posting.cobol import arithmetic, condition_names, move, picture
from acas_posting.cobol.field import FieldDescriptor

# The status vocabulary of `copybooks/wsfnctn.cob`, split out of the record
# layout. `FsReply` supplies the values this program tests inline - 0, 10, 21 and
# 23 - and `AccessType.NOT_LESS_THAN` is the `fn-not-less-than` the `Invoice-Start`
# at [sales/sl055.cbl:L475-L476] sets.
from acas_posting.dal.status import AccessType, FsReply

# copy "Proc-ACAS-FH-Calls.cob".  [sales/sl055.cbl:L731]
# The ENTITY-named facade vocabulary - `Value-*`, `Analysis-*`, `Invoice-*`. This
# COPY is the one whose Python translation is NOT a module-level import: the
# contract is stated structurally by the `_FacadeVerbs` Protocol below, and the
# actual `from acas_posting.dal import facade` lives inside `_resolve_facade`,
# which runs at first use rather than at import. Deferring keeps this module
# importable and its arithmetic testable without a data-access layer - which is
# also how a COBOL `CALL` behaves, resolving its target when it executes.
# AMBIGUITY Q-57.

# `01 to-day pic x(10).` [sales/sl055.cbl:L264] is converted for display by
# `zz070-Convert-Date section.` [sales/sl055.cbl:L694], whose body is
# byte-identical in all ten programs that carry it and is therefore consolidated
# in `acas_posting.dates`. No `zz050`, no `zz060` and no `maps04` wrapper: this
# program has none of them.
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

#: The whole public surface: this program's single entry point, mirroring its
#: `PROCEDURE DIVISION USING` list [sales/sl055.cbl:L271-L275]. Agent Action Plan
#: section 0.3.3, verbatim: "Each `programs/*.py` module exposes a single
#: `run(...)` entry mirroring its COBOL `PROCEDURE DIVISION USING` list, with the
#: paragraph functions private to the module. Callers cannot reach into a
#: program's internals, exactly as a COBOL `CALL` cannot." A tuple rather than a
#: list, so the surface cannot be extended in place at run time.
__all__: Final[tuple[str, ...]] = ("run",)

#: Every `display` in this program is a diagnostic with no database effect, and
#: section 0.3.4 makes such a display "a log record at a severity matching the
#: original's intent" that "must not alter control flow and must not appear in
#: any table dump". One COBOL `display` produces one record here, at the
#: original's own severity, with the screen position and colour dropped.
_LOG: Final[logging.Logger] = logging.getLogger(__name__)



#  THIS PROGRAM'S OWN WORKING STORAGE  [sales/sl055.cbl:L198-L221]
#
#     198  01  ws-data.
#     200      03  ws-p-flag       pic 9                value zero.
#     201      03  ws-Anal-Flag    pic 9                value zero. *> 1 = anal rec created
#     202      03  save-code       pic xxx.
#     203      03  v-exists        pic 9.
#     204      03  ws-inv-amt      pic s9(7)v99  comp-3 value zero.
#     205      03  work-2          pic s9(7)v99  comp-3 value zero.
#     206      03  ws-vat-totalv   pic s9(7)v99  comp-3 value zero.
#     207      03  ws-vatr-totalv  pic s9(7)v99  comp-3 value zero.
#     208      03  ws-carr-totalv  pic s9(7)v99  comp-3 value zero.
#     209      03  ws-disc-totalv  pic s9(7)v99  comp-3 value zero.
#     210      03  work-3          pic s9(5)     comp   value zero.
#     211      03  ws-vat-totalt   pic s9(5)     comp   value zero.
#     212      03  ws-vatr-totalt  pic s9(5)     comp   value zero.
#     213      03  ws-carr-totalt  pic s9(5)     comp   value zero.
#     214      03  ws-disc-totalt  pic s9(5)     comp   value zero.
#
# These fields are DECLARED IN THE PROGRAM and not in any copybook, so they have
# no data-dictionary entry and no host variable: they reach no column and appear
# in no table dump. `FieldDescriptor.__post_init__` still demands provenance, so
# each one carries a `source_locator` pointing at the declaring line of the
# frozen program - which is the correct citation for a program-local field, and
# is what makes the store semantics below auditable against the source.
#
# THE TWO STORAGE CLASSES HERE ARE NOT INTERCHANGEABLE. The four value totals
# and the two work fields are `s9(7)v99 comp-3` - signed packed decimal, scale
# two. The four count totals and `work-3` are `s9(5) comp` - signed binary,
# scale ZERO. So `move ws-vat-totalv to work-2` keeps two decimal places while
# `move ws-vat-totalt to work-3` keeps none, and the pair is then added into
# `VA-V-*` (scale two) and `VA-T-*` (scale zero) respectively.

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

#: `77 Exception-Msg pic x(25) value spaces.` [sales/sl055.cbl:L153] - the
#: receiver `a01-Eval-Status` [sales/sl055.cbl:L724-L727] fills from the
#: file-status message table.
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

#: `77 prog-name pic x(15) value "SL055 (3.3.00)".` [sales/sl055.cbl:L152] - the
#: version banner displayed at [sales/sl055.cbl:L351]. Presentation only.
_PROG_NAME: Final[str] = "SL055 (3.3.00)"

#: `display "Invoice Post Extract" at 1201` [sales/sl055.cbl:L352].
_TITLE: Final[str] = "Invoice Post Extract"

#: `"Emergency Name - Missing"` [sales/sl055.cbl:L578] - the description
#: `db010-Create-Anal` writes into the analysis record it invents. Twenty-four
#: characters, exactly the width of `Pa-Desc pic x(24)`
#: [copybooks/wsanal.cob:L16], so the move neither truncates nor pads.
_EMERGENCY_NAME: Final[str] = "Emergency Name - Missing"

#: `move 8 to WS-Term-Code` [sales/sl055.cbl:L344]. EIGHT, not the General
#: Ledger's five: `load000.` [sales/sales.cbl:L710-L712] treats anything above
#: seven as a serious error and `goback`s out of the sales menu entirely.
_TERM_CODE_ANALYSIS_FILE_MISSING: Final[int] = 8

#: `if WS-Caller not = "xl150"` [sales/sl055.cbl:L341], [sales/sl055.cbl:L505],
#: [sales/sl055.cbl:L514] - the codebase's OWN unattended-mode check. `xl150` is
#: the end-of-cycle driver, out of scope per section 0.2.2; when it is the
#: caller, the acknowledgement `accept` is skipped. Direct evidence that headless
#: operation was designed for rather than bolted on. Padded to `WS-Caller`'s
#: `pic x(8)` through the `MOVE` primitive, because comparing an eight-character
#: field against a five-character literal compares padded operands.
_XL150: Final[str] = move.move_alphanumeric("xl150", _calling_descriptor("ws_caller"))


#  THE GnuCOBOL FILE STATUSES THE OTM2 FILE REPORTS
#
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

    `records.value_analysis`, `records.analysis` and `records.system_record_4`
    publish their field metadata as a `FIELDS` class variable rather than through
    an accessor function, so this is the accessor. It looks the descriptor UP; it
    does not build one, and it applies no picture, storage or comparison
    semantics of its own (rule R-2, and section 0.3.1's rule that a program
    module holds no numeric primitives).

    The match is case-insensitive because the two copybooks disagree on case:
    `copybooks/wsval.cob` writes `va-t-this` in lower case while
    `copybooks/wsanal.cob` writes `Pa-Gl` in mixed case, and COBOL treats the
    two alike.

    Args:
        fields: A record class's published `FIELDS` tuple.
        cobol_name: The field's COBOL name, in any case.

    Returns:
        The matching descriptor, with its dictionary key and locator intact.

    Raises:
        KeyError: No field of that name is published. A PROGRAMMER error: it can
            only fire on a name retyped wrongly here, never on record content.
    """
    wanted = cobol_name.casefold()
    for descriptor in fields:
        if descriptor.name.casefold() == wanted:
            return descriptor
    raise KeyError(f"no published field named {cobol_name!r} in this record")


#  `01 WS-Value-Record.`  [copybooks/wsval.cob:L9]
#
# NOTE THE SIGNEDNESS SPLIT, which is load-bearing for the accumulations below:
# the three COUNT fields are `pic 9(5) comp` - UNSIGNED [copybooks/wsval.cob:L18]
# - while the three VALUE fields are `pic s9(8)v99 comp-3` - SIGNED
# [copybooks/wsval.cob:L21]. So `subtract il-net from VA-V-This`
# [sales/sl055.cbl:L394] can legitimately drive a value negative, and the counts
# cannot go negative at all. `work-3`, the sender at [sales/sl055.cbl:L601], IS
# signed, so a negative count would silently lose its sign at the receiver - it
# cannot arise here because the four count totals are only ever incremented by
# one, but the drift is recorded rather than assumed away.
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

#: The six fields `move zero to VA-T-This va-t-last VA-T-Year VA-V-This
#: va-v-last VA-V-Year` [sales/sl055.cbl:L539-L540] names, IN THE ORDER IT NAMES
#: THEM. A single `MOVE` with six receivers, each converted independently against
#: its own picture - which is why the three counts land as integers and the three
#: values as two-place decimals. Repeated verbatim at [sales/sl055.cbl:L557-L558]
#: and [sales/sl055.cbl:L569-L570].
_VALUE_TOTALS_CLEARED_BY_DB000: Final[tuple[FieldDescriptor, ...]] = (
    _D_VA_T_THIS,
    _D_VA_T_LAST,
    _D_VA_T_YEAR,
    _D_VA_V_THIS,
    _D_VA_V_LAST,
    _D_VA_V_YEAR,
)

#  `01 WS-Analysis-Record.`  [copybooks/wsanal.cob:L9]
#
# Its first thirty-six bytes are field-for-field picture-identical to the value
# record's first thirty-six: `Pa-System`/`va-system` and `Pa-First`/`va-first`
# and `Pa-Second`/`va-second` are all `pic x`, `Pa-Gl`/`va-gl` are both
# `pic 9(6)`, `Pa-Desc`/`va-desc` are both `pic x(24)` and
# `Pa-Print`/`va-print` are both `pic xxx`. That identity is what makes the group
# move at [sales/sl055.cbl:L538] a plain byte copy of those six fields - see
# `_db000_create_main` and question Q-54.
_D_WS_PA_CODE: Final[FieldDescriptor] = _field_of(WsAnalysisRecord.FIELDS, "WS-Pa-Code")
_D_PA_SYSTEM: Final[FieldDescriptor] = _field_of(WsPaCode.FIELDS, "Pa-System")
_D_PA_GROUP: Final[FieldDescriptor] = _field_of(WsPaCode.FIELDS, "Pa-Group")
_D_PA_FIRST: Final[FieldDescriptor] = _field_of(PaGroup.FIELDS, "Pa-First")
_D_PA_SECOND: Final[FieldDescriptor] = _field_of(PaGroup.FIELDS, "Pa-Second")
_D_PA_GL: Final[FieldDescriptor] = _field_of(WsAnalysisRecord.FIELDS, "Pa-Gl")
_D_PA_DESC: Final[FieldDescriptor] = _field_of(WsAnalysisRecord.FIELDS, "Pa-Desc")
_D_PA_PRINT: Final[FieldDescriptor] = _field_of(WsAnalysisRecord.FIELDS, "Pa-Print")

#  `SYSTOT-REC` - THE TWO PERIOD-TOTAL COLUMNS  [copybooks/wssys4.cob]
#
# Section 0.6.4 lists NINE period-total write sites across the whole migration
# and these are numbers one and two. They are the ONLY writers of these two
# columns anywhere, which is what makes the period-end-totals scenario verifiable
# by inspecting one table.
_D_SL_INVOICES_THIS_MONTH: Final[FieldDescriptor] = _field_of(
    SalesLedgerData.FIELDS, "sl-invoices-this-month"
)
_D_SL_CREDIT_NOTES_THIS_MONTH: Final[FieldDescriptor] = _field_of(
    SalesLedgerData.FIELDS, "sl-credit-notes-this-month"
)

#  THE INVOICE RECORD  [copybooks/slwsinv2.cob]
#
# One 137-byte area, three REDEFINES views. The generic view supplies the KEY
# this program rewrites at [sales/sl055.cbl:L473-L474]; the header view supplies
# everything `da020-Header-Analysis` and `dd000-Extract` read; the line view
# supplies everything the inner loop reads.
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

#: `ih-deduct-amt pic 999v99 comp` [copybooks/slwsinv2.cob:L82] and
#: `ih-deduct-vat pic 999v99 comp` [copybooks/slwsinv2.cob:L83] are UNSIGNED,
#: whereas their OTM2 receivers `OI-Deduct-Amt`/`OI-Deduct-Vat pic s999v99 comp`
#: [copybooks/slwsoi.cob:L51-L52] are SIGNED. That asymmetry is precisely why the
#: credit-note negation at [sales/sl055.cbl:L658-L659] is expressible at all: it
#: negates the SIGNED copies, never the unsigned originals, and the un-negated
#: originals are what the nine-addend sum at [sales/sl055.cbl:L671-L673] then
#: adds. See question Q-50.
_D_IH_DEDUCT_AMT: Final[FieldDescriptor] = _invoice_descriptor(IhSubPrime, "ih_deduct_amt")
_D_IH_DEDUCT_VAT: Final[FieldDescriptor] = _invoice_descriptor(IhSubPrime, "ih_deduct_vat")

_D_IL_PRODUCT: Final[FieldDescriptor] = _invoice_descriptor(IlInvoiceLine, "il_product")
_D_IL_PA: Final[FieldDescriptor] = _invoice_descriptor(IlInvoiceLine, "il_pa")
_D_IL_TYPE: Final[FieldDescriptor] = _invoice_descriptor(IlInvoiceLine, "il_type")
_D_IL_NET: Final[FieldDescriptor] = _invoice_descriptor(IlInvoiceLine, "il_net")
_D_IL_UPDATE: Final[FieldDescriptor] = _invoice_descriptor(IlInvoiceLine, "il_update")

#  `01 OI-Header.` - THE OTM2 RECORD  [copybooks/slwsoi.cob:L8]
#
# All twenty-eight leaves, because `initialize oi-header with filler.`
# [sales/sl055.cbl:L635] touches every one of them.
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
#: `OI-Approp` [copybooks/slwsoi.cob:L38] carries a `REDEFINES` clause and is
#: therefore NOT itself an `INITIALIZE` target under the standard - but it
#: occupies `OI-Net`'s bytes, so zeroing `OI-Net` necessarily zeroes it, and it is
#: listed here so the Python model of those shared bytes cannot drift apart from
#: itself.
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

#: The ALPHANUMERIC leaves of `OI-Header`, which `INITIALIZE` sets to spaces.
_OI_HEADER_ALPHANUMERIC_LEAVES: Final[tuple[FieldDescriptor, ...]] = (
    _D_OI_NOS,
    _D_OI_DESCRIPTION,
    _D_OI_HOLD_FLAG,
    _D_OI_UNAPL,
    _D_OI_APPLIED,
)


#  THE CONDITION NAMES THIS PROGRAM TESTS  (rule R-2: no `88`-level test is
#  written here; each one resolves to the published vocabulary)
#
#     copybooks/slwsinv2.cob:L72   88  pending        value "P".   on ih-status
#     copybooks/slwsinv2.cob:L74   88  applied        value "Z".   on ih-status
#     copybooks/slwsinv2.cob:L89   88  ih-analyised   value "Z".   on ih-update
#     copybooks/slwsinv2.cob:L105  88  il-analyised   value "Z".   on il-update
#     copybooks/wssystem.cob:L113  88  FS-Cobol-Files-Used value zero.
#
# `pending` and `applied` are declared on `ih-status`; `ih-analyised` on the
# SEPARATE field `ih-update`. So `if ih-analyised and applied`
# [sales/sl055.cbl:L427] tests TWO DIFFERENT FIELDS, which is easy to misread as
# one compound test of one field.
_IS_PENDING: Final = condition_names.is_pending_slwsinv2
_IS_APPLIED: Final = condition_names.is_applied_slwsinv2
_IS_IH_ANALYISED: Final = condition_names.is_ih_analyised_slwsinv2
_IS_IL_ANALYISED: Final = condition_names.is_il_analyised_slwsinv2

#: `88 FS-Cobol-Files-Used value zero.` [copybooks/wssystem.cob:L113], declared
#: on `File-System-Used`, with `88 FS-RDBMS-Used value 1.`
#: [copybooks/wssystem.cob:L116] as its sibling. Resolved through
#: `predicate_for` with the copybook named EXPLICITLY, because the same COBOL
#: condition-name spelling occurs a second time on a different conditional
#: variable at [copybooks/wsfnctn.cob:L95] and an unqualified lookup would be
#: ambiguous.
_IS_FS_COBOL_FILES_USED: Final = condition_names.predicate_for(
    "FS-Cobol-Files-Used", copybook="copybooks/wssystem.cob"
)

#  THE THREE FIELDS OUTSIDE THE FOUR RECORDS ABOVE THAT THIS PROGRAM WRITES
#
#: `05 File-Key-No pic 9.` [copybooks/wsfnctn.cob:L46] - the receiver of the nine
#: `move 1 to File-Key-No` statements at [sales/sl055.cbl:L349],
#: [sales/sl055.cbl:L382], [sales/sl055.cbl:L406], [sales/sl055.cbl:L533],
#: [sales/sl055.cbl:L550], [sales/sl055.cbl:L563], [sales/sl055.cbl:L579],
#: [sales/sl055.cbl:L595] and [sales/sl055.cbl:L612]. AMBIGUITY Q-55.
_D_FILE_KEY_NO: Final[FieldDescriptor] = _field_of(LoggingData.FIELDS, "File-Key-No")

#: `03 Date-Form pic 9.` [copybooks/wssystem.cob] - read AND written by
#: `zz070-Convert-Date` [sales/sl055.cbl:L704-L705]. A `SYSTEM-REC` column, so the
#: default this program applies is DIFF-VISIBLE once the caller's `overrewrite.`
#: paragraph rewrites the record.
_D_DATE_FORM: Final[FieldDescriptor] = _field_of(SystemDataBlock.FIELDS, "Date-Form")

#: `05 File-System-Used pic 9.` [copybooks/wssystem.cob:L112] - the conditional
#: variable that `88 FS-Cobol-Files-Used value zero.`
#: [copybooks/wssystem.cob:L113] and `88 FS-RDBMS-Used value 1.`
#: [copybooks/wssystem.cob:L116] are declared on. Read only, at
#: [sales/sl055.cbl:L326]. Note the SECOND, unrelated declaration of the same
#: condition-name spelling at [copybooks/wsfnctn.cob:L95], on
#: `FA-File-System-Used` - which is why `_IS_FS_COBOL_FILES_USED` above names its
#: copybook explicitly.
_D_FILE_SYSTEM_USED: Final[FieldDescriptor] = _field_of(
    RdbmsFlatStatuses.FIELDS, "File-System-Used"
)




class CobolFileSystemPathUnavailable(RuntimeError):
    """`if FS-Cobol-Files-Used` was TRUE, and that path needs COBOL  (rule R-1).

    Raised from `_da000_mainline` when the system record selects the INDEXED
    (COBOL) file system rather than the RDBMS one, because the block that branch
    guards cannot be reproduced in Python:

        326      if       FS-Cobol-Files-Used
        327               call  "CBL_CHECK_FILE_EXIST" using File-15   *> Analysis
        328                                                  File-Info
        329               if    return-code not = zero
        331                     move 1 to ws-Process-Func ws-Sub-Function
        332                     call "sl070" using ws-calling-data
        333                                        system-record
        334                                        to-day
        335                                        file-defs

    `CBL_CHECK_FILE_EXIST` is a GnuCOBOL built-in system routine and `sl070` is a
    separate COBOL program that creates default entries in the Analysis and Value
    files. `sl070` is NOT one of the twelve in-scope programs - Agent Action Plan
    section 0.2.2 leaves it out - so there is no Python module to call, and rule
    R-1 forbids invoking the COBOL. Section 0.7.4 conflict C-1 confines compiled
    COBOL to the comparison harness, which a program module may not reach.

    THIS IS RAISED RATHER THAN SKIPPED DELIBERATELY. Silently skipping the block
    would change behaviour invisibly: the compiled program either finds the
    analysis file, or has `sl070` create it, or aborts with term code eight
    [sales/sl055.cbl:L344]. A no-op stub would produce a fourth outcome that the
    compiled program never produces. Raising makes the gap loud and attributable.

    The branch is UNREACHABLE in the configuration this migration targets:
    `88 FS-Cobol-Files-Used value zero.` [copybooks/wssystem.cob:L113] against
    `88 FS-RDBMS-Used value 1.` [copybooks/wssystem.cob:L116], and the whole
    data-access layer exists because the RDBMS path is the one in use. Whether
    any scenario ever sets it is question Q-56.
    """


class InvoiceRecordAreaNotLoaded(RuntimeError):
    """The invoice record area does not hold the view the program is reading.

    A PROGRAMMER error, and specifically a violation of the facade's contract -
    never something record CONTENT can cause. In COBOL the three views
    [copybooks/slwsinv2.cob:L27], [copybooks/slwsinv2.cob:L38] and
    [copybooks/slwsinv2.cob:L91] are the SAME 137 bytes, so a view is always
    "present" and reading the wrong one merely reinterprets bytes. Python models
    the union with two typed views beside one shared key, so the absent view is
    representable and is reported rather than silently read as `None`.

    It can only fire if a facade read verb returned success without loading a
    view, or if a caller invoked a paragraph function out of order. No validation
    of any value is added by it (rule R-3): it inspects presence, not content.
    """


class _Label(enum.Enum):
    """The paragraph labels this program's `GO TO` statements transfer to.

    Rule R-5 requires a named function per paragraph AND a class annotation at
    every transfer site, and section 0.7.4 conflict C-4 resolves the tension
    between traceability and restructuring by "[k]eeping the function boundary
    fixed at the paragraph boundary and varying only the TRANSFER MECHANISM".
    This enumeration is that mechanism made explicit: a paragraph function
    returns the label control would flow to, and its caller performs the
    `continue`, `break` or `return` that class 1, 2 or 3 calls for.

    Only labels that are actually `GO TO` TARGETS in the frozen source appear
    here. `da020-Header-Analysis` is included even though nothing transfers to it,
    because control reaches it by FALL-THROUGH from the inline perform's
    `exit perform` [sales/sl055.cbl:L371] and that fall-through has to be
    expressible too.
    """

    #: `da010-Read-Loop.` [sales/sl055.cbl:L364] - the outer loop's head. Four
    #: back-edges: L428, L442, L470, L479.
    DA010_READ_LOOP = "da010-Read-Loop"
    #: `da020-Header-Analysis.` [sales/sl055.cbl:L426] - reached only by
    #: fall-through, never by a `GO TO`.
    DA020_HEADER_ANALYSIS = "da020-Header-Analysis"
    #: `da030-Skip-Invoice.` [sales/sl055.cbl:L472] - the class-4 target of L431
    #: and L436.
    DA030_SKIP_INVOICE = "da030-Skip-Invoice"
    #: `da040-Close-Files.` [sales/sl055.cbl:L481] - the class-2 target of L368
    #: and L478, and the post-loop block.
    DA040_CLOSE_FILES = "da040-Close-Files"
    #: `da999-Menu-Exit.` [sales/sl055.cbl:L520] - reached by fall-through from
    #: the end of `da040-Close-Files`.
    DA999_MENU_EXIT = "da999-Menu-Exit"
    #: `goback.` [sales/sl055.cbl:L509] and [sales/sl055.cbl:L518] - the two early
    #: returns out of `da040-Close-Files`, which skip `da999-Menu-Exit` entirely.
    GOBACK = "goback"
    #: `DB000-Create-Main.` [sales/sl055.cbl:L530] - the class-4 target of
    #: [sales/sl055.cbl:L585], a BACKWARD transfer from the paragraph below it.
    #: Spelled `db000-Create-Main` at that `GO TO` and `DB000-Create-Main.` at its
    #: declaration; COBOL is case-insensitive, so the two are one label.
    DB000_CREATE_MAIN = "DB000-Create-Main"
    #: `db010-Create-Anal.` [sales/sl055.cbl:L574] - the class-4 target of L536.
    DB010_CREATE_ANAL = "db010-Create-Anal"
    #: `db999-Main-Exit.` [sales/sl055.cbl:L587] - the class-3 target of L543,
    #: L554, L566 and L572.
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

    `acas_posting/dal/facade.py` is the module `copy "Proc-ACAS-FH-Calls.cob".`
    [sales/sl055.cbl:L731] translates to under section 0.4.3, and it is the only
    data-access module a program module may import - `dal.acas*`,
    `dal.connection` and `dal.cursor_state` are all out of bounds. It is not yet
    written, and `acas_posting/dal/__init__.py` says so in its own target
    inventory.

    THE IMPORT IS DEFERRED, NOT AVOIDED. A module-level import would make this
    module unimportable until the facade lands, which would in turn make the
    twelve-module program registry unimportable and this program's arithmetic
    untestable - and rule R-2's parity suite is meant to run with no database and
    no data-access layer at all. Deferring the import to the moment a verb is
    actually needed keeps the layering exactly as section 0.4.3 specifies while
    letting the module be imported, compiled and unit-tested today. It is also
    how the compiled program behaves: a COBOL `CALL` resolves its target when it
    executes, not when the program is loaded.

    Returns:
        The facade module, which structurally satisfies `_FacadeVerbs`.

    Raises:
        ModuleNotFoundError: The facade is not yet on the import path. The
            message is Python's own; `run`'s `facade` parameter is the documented
            way to supply an alternative.
    """
    from acas_posting.dal import facade

    return _BoundFacade(facade)


#: The entity work area each dispatch paragraph names as its SECOND operand,
#: keyed by the verb-name prefix that reaches it. Transcribed from
#: `copybooks/Proc-ACAS-FH-Calls.cob`, which passes the same five operands every
#: time and varies only this one:
#:
#:     acas013.  call "acas013" using System-Record WS-Value-Record
#:                    File-Access File-Defs ACAS-DAL-Common-Data.   [:L90-L96]
#:     acas015.  ...                        WS-Analysis-Record ...  [:L108-L114]
#:     acas016.  ...                        WS-Invoice-Record  ...  [:L116-L122]
#:
#: These are the only three entities `sl055` performs against.
_ENTITY_RECORD: Final[dict[str, str]] = {
    "value": "ws_value_record",
    "analysis": "ws_analysis_record",
    "invoice": "ws_invoice_record",
}


class _BoundFacade:
    """`_Sl055Context` on this side, `facade.FacadeContext` on the other.

    THIS RESOLVES AMBIGUITY Q-57. The question `_FacadeVerbs` records is what
    shape of single argument the generated facade would publish; the answer is
    that it publishes `verb(ctx: facade.FacadeContext)` where `FacadeContext`
    carries the dispatch paragraph's five operands positionally, in the
    copybook's own order - `(system, record, file_access, file_defs,
    dal_common)`. The CALL FORM assumed above is therefore correct and unchanged,
    one verb function taking one context argument; only the context TYPE differs,
    because this module names its three record areas after the COBOL operands
    while the facade carries whichever one the verb is for in a single `record`
    slot.

    Translating here rather than at the twenty-nine call sites is deliberate on
    two counts. It is where `_resolve_facade`'s docstring already says the
    binding happens, so `run`'s `facade` parameter still overrides it and a test
    double is still structurally sufficient. And a conversion between a program's
    record areas and a handler's parameter shape is a data-access concern, so
    keeping it at the facade boundary is what the layering in Agent Action Plan
    section 0.4.3 asks for - no paragraph function below learns anything about it.

    Nothing about the operation changes. `File-Access` is passed by reference, so
    each verb writes `Fs-Reply` and `We-Error` into the very block this context
    holds [copybooks/wsfnctn.cob:L23-L38], which is what every inline reply test
    after a `PERFORM` reads - this module tests the block, never a return value,
    exactly as `Proc-ACAS-FH-Calls.cob` requires of a caller that has no
    error-check paragraph to lean on. One `PERFORM` remains one call, in source
    order; nothing is reordered, batched, deferred, coalesced or cached.
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

    THREE NAMES FOR THE SAME BYTES  [copybooks/slwsinv2.cob]

        L27  01  Invoice-Record.                              the generic view
        L38  01  Invoice-Header  redefines Invoice-Record.     the header view
        L91  01  Invoice-Line    redefines Invoice-Record.     the line view

    and the first TEN bytes are the same field under three names in all three:

        Invoice-Nos pic 9(8)  [L29]  ==  ih-invoice pic 9(8)  [L40]  ==  il-invoice  [L92]
        Item-Nos    pic 99    [L30]  ==  ih-test    pic 99    [L41]  ==  il-line     [L93]

    which is why `ih-test = zero` [sales/sl055.cbl:L370] discriminates a header
    from a line - a header carries item number zero - and why writing
    `invoice-nos`/`item-nos` through the GENERIC view at
    [sales/sl055.cbl:L473-L474] positions the `Invoice-Start` that follows.

    THE SHARED KEY IS HELD ONCE. `invoice_nos` and `item_nos` are the ten bytes;
    `ih_test` and `il_line` are read-only aliases onto `item_nos` rather than
    separate attributes, so the three views cannot drift apart the way three
    independent copies could. This is the model
    `acas_posting.dal.acas016_invoice` already adopted for the same union, and it
    is restated here rather than imported because a program module may not import
    a handler (section 0.4.3). AMBIGUITY Q-58.

    The two typed views beside the key are the ones
    `acas_posting.records.sales_invoice` publishes. A read verb loads exactly one
    of them - which one is determined by the record it read - so the other is
    `None`, and reading it reports `InvoiceRecordAreaNotLoaded` rather than
    silently yielding nothing. In COBOL both "views" always exist because both
    are the same bytes; the check is a Python-language consequence of typing the
    union, not a validation of any value (rule R-3).
    """

    #: `Invoice-Nos pic 9(8)` [copybooks/slwsinv2.cob:L29] - bytes 1-8, shared
    #: with `ih-invoice` and `il-invoice`.
    invoice_nos: int = 0
    #: `Item-Nos pic 99` [copybooks/slwsinv2.cob:L30] - bytes 9-10, shared with
    #: `ih-test` and `il-line`. Zero marks a HEADER.
    item_nos: int = 0
    #: `01 Invoice-Header redefines Invoice-Record.`
    #: [copybooks/slwsinv2.cob:L38], loaded when the record read is a header.
    invoice_header: IhInvoiceHeader | None = None
    #: `01 Invoice-Line redefines Invoice-Record.`
    #: [copybooks/slwsinv2.cob:L91], loaded when the record read is a line.
    invoice_line: IlInvoiceLine | None = None

    @property
    def ih_test(self) -> int:
        """`ih-test pic 99` [copybooks/slwsinv2.cob:L41] - bytes 9-10.

        The same two bytes as `Item-Nos`, under the header view's name. Tested at
        [sales/sl055.cbl:L370].
        """
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
    """`initialize oi-header with filler.`  [sales/sl055.cbl:L635].

    The `INITIALIZE` verb sets every elementary item of the group to its
    CATEGORY DEFAULT - numeric items to the value zero, alphanumeric items to
    spaces - and the `WITH FILLER` phrase extends that to `FILLER` items, which
    are otherwise left alone. `OI-Header` has two of them,
    `02 filler.` [copybooks/slwsoi.cob:L14] and
    `03 filler comp-3.` [copybooks/slwsoi.cob:L35], and between them they hold
    twenty-three of the record's twenty-eight leaves - so without `WITH FILLER`
    the statement would clear almost nothing. Dropping the phrase would be one of
    the quietest possible ways to change behaviour.

    THE TWO FIGURATIVE MOVES ARE THE `cobol.move` PRIMITIVE, NOT A LOOP WRITTEN
    HERE. Each leaf is converted independently against its OWN picture, which is
    why `MOVE ZERO` yields `0` for a `pic 9` and `Decimal("0.00")` for a
    `pic s9(7)v99 comp-3`, and why numeric and alphanumeric leaves must be moved
    separately at all: `MOVE SPACE` into a numeric receiver does not compile, and
    `acas_posting.cobol.move` reproduces the compiler's refusal.

    `OI-Approp` [copybooks/slwsoi.cob:L38] carries a `REDEFINES` clause, so the
    standard excludes it from `INITIALIZE` - but it occupies `OI-Net`'s bytes, and
    zeroing `OI-Net` therefore zeroes it. It is set here for exactly that reason:
    the two attribute names are one storage location, and they may not diverge.

    A FRESH RECORD IS RETURNED RATHER THAN ONE MUTATED IN PLACE. `oi-header` is a
    FILE SECTION record area whose only consumer is `write oi-header.`
    [sales/sl055.cbl:L681], and that write appends a deep snapshot - so nothing
    retains a reference to the previous area and replacing it is indistinguishable
    from clearing it. Returning a value also means the record can never be
    half-initialised.

    Returns:
        An `OI-Header` with all twenty-eight leaves at their category defaults.
    """
    # 635  initialize oi-header with filler.
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

    ONE OBJECT PLAYING TWO ROLES, both of which the compiled program also gives
    to the same storage:

      * IT IS THE PROGRAM'S STATE. The `01 ws-data.` block
        [sales/sl055.cbl:L198-L221] is program-local storage that persists across
        every paragraph, which in Python means it has to be threaded through the
        paragraph functions rather than living in module globals - globals would be
        shared between calls and would break rule R-6's guarantee that two runs of
        one scenario produce identical output.
      * IT IS THE FACADE'S CONTEXT. Section 0.4.3 fixes the facade call shape as
        `facade.<verb>(ctx)`, and the seven blocks the `acas013.`, `acas015.` and
        `acas016.` dispatch paragraphs name in their `CALL` statements are
        published below UNDER THOSE NAMES - `system_record`, `ws_value_record`,
        `ws_analysis_record`, `ws_invoice_record`, `file_access`, `file_defs` and
        `acas_dal_common_data`. Question Q-57.

    The dispatch paragraph, verbatim [copybooks/Proc-ACAS-FH-Calls.cob], for the
    Value entity:

        acas013.
            move     1 to File-Key-No.
            call     "acas013" using System-Record
                                     WS-Value-Record
                                     File-Access
                                     File-Defs
                                     ACAS-DAL-Common-data.

    Note that the dispatch paragraph sets `File-Key-No` ITSELF, and so does
    `Value-Read-Indexed` [copybooks/Proc-ACAS-FH-Calls.cob:L753-L757] - which
    makes this program's nine explicit `move 1 to File-Key-No` statements triply
    redundant. All nine are preserved regardless (rule R-3, AMBIGUITY Q-55).
    """

    #  ---- the linkage, in `PROCEDURE DIVISION USING` order  [L271-L275] ----

    #: `ws-calling-data` - `01 WS-Calling-Data` [copybooks/wscall.cob:L6].
    ws_calling_data: WsCallingData
    #: `system-record` - `SYSTEM-REC`. Also the facade context's first block.
    system_record: SystemRecord
    #: `system-record-4` - `SYSTOT-REC`, the period totals. Spelled
    #: `system-record-4` in this program's linkage [sales/sl055.cbl:L273] and
    #: `WS-System-Record-4` by the caller [sales/sales.cbl:L704]; one record, two
    #: names.
    system_record_4: SystemRecord4
    #: `to-day pic x(10)` [sales/sl055.cbl:L264] in DD/MM/CCYY form. The ONLY
    #: source of the run date - this program reads no clock.
    to_day: str
    #: `file-defs` - the file-name buffers.
    file_defs: FileDefs

    #  ---- the facade context's remaining blocks ----

    #: `01 File-Access.` [copybooks/wsfnctn.cob:L22]. Carries `Fs-Reply`, which
    #: every facade verb AND every OTM2 file operation writes, and
    #: `Logging-Data.File-Key-No` [copybooks/wsfnctn.cob:L46].
    file_access: FileAccess = field(default_factory=FileAccess)
    #: `WS-Value-Record` - `01 WS-Value-Record.` [copybooks/wsval.cob:L9].
    ws_value_record: WsValueRecord = field(default_factory=WsValueRecord)
    #: `WS-Analysis-Record` - `01 WS-Analysis-Record.` [copybooks/wsanal.cob:L9].
    ws_analysis_record: WsAnalysisRecord = field(default_factory=WsAnalysisRecord)
    #: `WS-Invoice-Record` - the 137-byte invoice area and its three views.
    #: `01 WS-Invoice-Record redefines Invoice-Record pic x(137).`
    #: [sales/sl055.cbl:L159-L160] is the flat alias the facade's `acas016.`
    #: dispatch paragraph passes; the views are what this program reads.
    ws_invoice_record: _InvoiceRecordArea = field(default_factory=_InvoiceRecordArea)
    #: `ACAS-DAL-Common-Data` [copybooks/Test-Data-Flags.cob:L6]. Its defaults are
    #: the copybook's own `value` clauses, `SW-Testing` included.
    acas_dal_common_data: AcasDalCommonData = field(default_factory=AcasDalCommonData)

    #  ---- `01 ws-data.`  [sales/sl055.cbl:L198-L214] ----

    #: `ws-p-flag pic 9 value zero` [sales/sl055.cbl:L200]. Set to one at
    #: [sales/sl055.cbl:L435] when an invoice is unprinted, and tested at
    #: [sales/sl055.cbl:L503] to decide the first early `goback`.
    ws_p_flag: int = 0
    #: `ws-Anal-Flag pic 9 value zero` [sales/sl055.cbl:L201], commented
    #: "1 = anal rec created". Set at [sales/sl055.cbl:L584], tested at
    #: [sales/sl055.cbl:L511] for the second early `goback`.
    ws_anal_flag: int = 0
    #: `save-code pic xxx` [sales/sl055.cbl:L202] - the analysis code
    #: `db000-Create` parks while it looks up the blanked-second-character group.
    save_code: str = "   "
    #: `v-exists pic 9` [sales/sl055.cbl:L203] - one when the value record was
    #: found, zero when `db000-Create` had to invent it. Chooses `Value-Write`
    #: over `Value-Rewrite`.
    v_exists: int = 0
    #: `ws-inv-amt pic s9(7)v99 comp-3 value zero` [sales/sl055.cbl:L204] - the
    #: nine-addend invoice total [sales/sl055.cbl:L671-L673].
    ws_inv_amt: Decimal = Decimal("0.00")
    #: `work-2 pic s9(7)v99 comp-3 value zero` [sales/sl055.cbl:L205] - the money
    #: work field the three sign flips negate.
    work_2: Decimal = Decimal("0.00")
    #: `ws-vat-totalv` [sales/sl055.cbl:L206] - VAT value, all invoice types
    #: except receipts.
    ws_vat_totalv: Decimal = Decimal("0.00")
    #: `ws-vatr-totalv` [sales/sl055.cbl:L207] - VAT value on RECEIPTS only.
    ws_vatr_totalv: Decimal = Decimal("0.00")
    #: `ws-carr-totalv` [sales/sl055.cbl:L208] - carriage value.
    ws_carr_totalv: Decimal = Decimal("0.00")
    #: `ws-disc-totalv` [sales/sl055.cbl:L209] - discount (deduction) value.
    ws_disc_totalv: Decimal = Decimal("0.00")
    #: `work-3 pic s9(5) comp value zero` [sales/sl055.cbl:L210] - the COUNT work
    #: field. Scale ZERO, unlike `work-2`.
    work_3: int = 0
    #: `ws-vat-totalt` [sales/sl055.cbl:L211] - VAT count.
    ws_vat_totalt: int = 0
    #: `ws-vatr-totalt` [sales/sl055.cbl:L212] - VAT-on-receipts count.
    ws_vatr_totalt: int = 0
    #: `ws-carr-totalt` [sales/sl055.cbl:L213] - carriage count.
    ws_carr_totalt: int = 0
    #: `ws-disc-totalt` [sales/sl055.cbl:L214] - discount count.
    ws_disc_totalt: int = 0
    #: `77 Exception-Msg pic x(25) value spaces.` [sales/sl055.cbl:L153] - filled
    #: by `a01-Eval-Status` [sales/sl055.cbl:L724] and only ever displayed.
    exception_msg: str = " " * 25

    #  ---- the OTM2 file and its record area ----

    #: `01 OI-Header.` [copybooks/slwsoi.cob:L8] - the OTM2 record area, rebuilt
    #: by `INITIALIZE` at the head of every extract.
    oi_header: OiHeader = field(default_factory=_initialize_oi_header_with_filler)
    #: `open-item-file-2` [copybooks/seloi2.cob] - the OTM2 work file, and the
    #: CHANNEL to `sl060`. The SHARED carrier `acas_posting.workfiles` publishes,
    #: not a module-private one: the producer and the consumer must hold the SAME
    #: object or nothing this program writes can be read, which is exactly what
    #: naming the same `assign file-18` achieves in COBOL.
    open_item_file_2: OpenItemWorkFile[OiHeader] = field(
        default_factory=lambda: open_item_work_file(OPEN_ITEM_2_NAME, OiHeader)
    )

    #  ---- the date-format work area and the facade binding ----

    #: The `ws-date` work area `zz070-Convert-Date` [sales/sl055.cbl:L694] fills,
    #: consolidated in `acas_posting.dates` because its body is byte-identical in
    #: all ten programs that carry it.
    date_formats: dates.WsDateFormats = field(default_factory=dates.WsDateFormats)
    #: The entity-named facade, resolved by `run`.
    facade: _FacadeVerbs | None = None

    @property
    def fs_reply(self) -> int:
        """`03 Fs-Reply pic 99.`  [copybooks/wsfnctn.cob:L25].

        ONE FIELD, TWO PRODUCERS. Every facade verb writes it, and so does every
        `open-item-file-2` operation, because [copybooks/seloi2.cob] declares
        `status fs-reply` - the same field. So a test of it sees whichever wrote
        last, which is exactly the belt-and-braces subtlety WHY THE `UNTIL` AND
        THE L367 TEST ARE BOTH REPRODUCED describes in the module docstring.
        """
        return self.file_access.fs_reply

    @property
    def verbs(self) -> _FacadeVerbs:
        """The facade, resolved.

        Raises:
            RuntimeError: `run` did not bind one. A PROGRAMMER error: the only
                entry point sets it before performing any paragraph.
        """
        if self.facade is None:
            raise RuntimeError(
                "no facade is bound; `sl055` reaches every file through "
                "`copy \"Proc-ACAS-FH-Calls.cob\".` [sales/sl055.cbl:L731] and "
                "`run` binds it before performing `da000-mainline`"
            )
        return self.facade



#  THE LITERALS THIS PROGRAM MOVES AND COMPARES
#
# Each one is normalised THROUGH the `MOVE` primitive against the field it is
# moved into or compared with, rather than written as a bare Python string,
# because a COBOL relation condition compares operands at the RECEIVING FIELD'S
# WIDTH: an eight-character `WS-Caller` against the five-character literal
# "xl150" compares `"xl150   "`, not `"xl150"`. Normalising once here means no
# comparison below has to remember to pad.

#: `move "S" to va-system` [sales/sl055.cbl:L379] - the value-analysis system
#: code for Sales. One character, `va-system pic x` [copybooks/wsval.cob:L11].
_VALUE_SYSTEM_SALES: Final[str] = move.move_alphanumeric("S", _D_VA_SYSTEM)

#: `if il-product (1:1) = "/"` [sales/sl055.cbl:L376], whose own comment reads
#: "comment only" - a line whose product code starts with a slash is a comment
#: line and contributes nothing to value analysis. One character against one
#: character, so no padding rule applies to either operand.
_COMMENT_LINE_MARKER: Final[str] = "/"

#: `if il-type not = 3` [sales/sl055.cbl:L390], [sales/sl055.cbl:L413], commented
#: "Cr. notes". AMBIGUITY Q-53: `il-type` is `pic x` - ALPHANUMERIC
#: [copybooks/slwsinv2.cob:L97] - and the literal is NUMERIC, so the comparison
#: is alphanumeric with the integer treated as though moved to a field of the
#: receiver's size. That is what the `MOVE` below computes, and the result is the
#: single character "3". Note the contrast with `ih-type pic 9`
#: [copybooks/slwsinv2.cob:L58], whose comparisons are ordinary numeric ones.
_IL_TYPE_CREDIT_NOTE: Final[str] = move.move_alphanumeric(3, _D_IL_TYPE)

#: `move "Z" to il-update` [sales/sl055.cbl:L421], whose comment records
#: "Analysied flag changed from z (1/6/13)". The same "Z" is the value of
#: `88 il-analyised` [copybooks/slwsinv2.cob:L105], so writing it is what makes
#: the line skip itself on a later run.
_IL_UPDATE_ANALYSED: Final[str] = move.move_alphanumeric("Z", _D_IL_UPDATE)

#: `move "Z" to ih-update` [sales/sl055.cbl:L468] - the header equivalent, and
#: the value of `88 ih-analyised` [copybooks/slwsinv2.cob:L89].
_IH_UPDATE_ANALYSED: Final[str] = move.move_alphanumeric("Z", _D_IH_UPDATE)

#: `move "Z" to ih-status` [sales/sl055.cbl:L679] - the value of
#: `88 applied` [copybooks/slwsinv2.cob:L74].
_IH_STATUS_APPLIED: Final[str] = move.move_alphanumeric("Z", _D_IH_STATUS)

#: `move "A" to ih-status-A` [sales/sl055.cbl:L680]. `ih-status-A` is a SEPARATE
#: one-character field [copybooks/slwsinv2.cob:L78] commented "Invoice Applied to
#: a/c - space or A", not a condition name on `ih-status`. `pl055` writes no
#: equivalent [purchase/pl055.cbl:L586], which is one of the six divergences
#: listed in the module docstring.
_IH_STATUS_A_APPLIED: Final[str] = move.move_alphanumeric("A", _D_IH_STATUS_A)

#: `if ih-status-L not = "L"` [sales/sl055.cbl:L434]. `ih-status-L`
#: [copybooks/slwsinv2.cob:L76] is commented "Invoice Printed - space or L", so
#: anything other than "L" means the invoice has not been printed and must be
#: skipped.
_IH_STATUS_L_PRINTED: Final[str] = move.move_alphanumeric("L", _D_IH_STATUS_L)

#: `move space to va-second` [sales/sl055.cbl:L405], [sales/sl055.cbl:L547] and
#: the comparand of `if va-second = space` [sales/sl055.cbl:L402],
#: [sales/sl055.cbl:L542], [sales/sl055.cbl:L611]. Blanking the second character
#: of the analysis group is how this program rolls a specific group up into its
#: single-character parent group - which is why every accumulation happens TWICE.
_VA_SECOND_SPACE: Final[str] = str(move.move_figurative(move.SPACE, _D_VA_SECOND))

#: `if pa-second not = space` [sales/sl055.cbl:L581] and
#: `move space to pa-second` [sales/sl055.cbl:L582].
_PA_SECOND_SPACE: Final[str] = str(move.move_figurative(move.SPACE, _D_PA_SECOND))

#: `move "Svo" to va-code.` [sales/sl055.cbl:L482] - the FIRST of the four
#: special-total keys, and the only one that sets `va-system` as well. The three
#: that follow move only two characters into `va-group`
#: [sales/sl055.cbl:L486], [sales/sl055.cbl:L490], [sales/sl055.cbl:L494], so the
#: "S" carries over from here. The four groups are therefore `Svo`, `Svp`, `Szc`
#: and `Szd`.
_SPECIAL_TOTAL_VAT_CODE: Final[str] = "Svo"
#: `move "vp" to va-group.` [sales/sl055.cbl:L486] - VAT on receipts.
_SPECIAL_TOTAL_VATR_GROUP: Final[str] = "vp"
#: `move "zc" to va-group.` [sales/sl055.cbl:L490] - carriage.
_SPECIAL_TOTAL_CARRIAGE_GROUP: Final[str] = "zc"
#: `move "zd" to va-group.` [sales/sl055.cbl:L494] - discount.
_SPECIAL_TOTAL_DISCOUNT_GROUP: Final[str] = "zd"

#: `ih-type` values, from the type table `copybooks/slwsoi.cob:L20-L31`:
#: 1 = Receipt, 2 = Account (invoice), 3 = Cr. Note, 4 = Proforma. Named because
#: this program branches on all four and the comments naming them are attached to
#: the OTM2 copybook rather than to the invoice one.
_IH_TYPE_RECEIPT: Final[int] = 1
_IH_TYPE_INVOICE: Final[int] = 2
_IH_TYPE_CREDIT_NOTE: Final[int] = 3
_IH_TYPE_PROFORMA: Final[int] = 4

#: `multiply -1 by ...` - the multiplier of all twelve sign flips
#: [sales/sl055.cbl:L446], [sales/sl055.cbl:L457], [sales/sl055.cbl:L463] and
#: [sales/sl055.cbl:L658-L666]. NO `GIVING`, so the RECEIVER IS THE SECOND
#: OPERAND: `MULTIPLY a BY b` is `b = a * b`. `gl070` writes the General Ledger's
#: opposite form, `multiply pre-amount by -1 giving pre-amount.`, and copying it
#: here would multiply the wrong way round.
_NEGATE: Final[int] = -1


#  THE THREE-BYTE GROUP KEYS  -  `va-code` AND `WS-PA-Code`
#
# `03 va-code.` [copybooks/wsval.cob:L10] and `03 WS-Pa-Code.`
# [copybooks/wsanal.cob:L10] are GROUP items of three one-character children:
#
#     va-code    =  va-system  ||  va-first  ||  va-second     3 bytes
#     WS-Pa-Code =  Pa-System  ||  Pa-First  ||  Pa-Second     3 bytes
#
# and this program moves them AS GROUPS six times - [sales/sl055.cbl:L482],
# [sales/sl055.cbl:L531], [sales/sl055.cbl:L545], [sales/sl055.cbl:L548],
# [sales/sl055.cbl:L562] - as well as moving the two-byte sub-group `va-group`
# three times at [sales/sl055.cbl:L486], [sales/sl055.cbl:L490] and
# [sales/sl055.cbl:L494].
#
# `acas_posting.cobol.move.move_group` performs the MOVE - the byte-image copy,
# the left justification, the padding and the truncation - and, in its own words,
# expects that "a program module transcribing a group move supplies `length` from
# the copybook", because a group descriptor carries no width of its own. The two
# accessors below supply the other half of that contract: a group item's VALUE IS
# the concatenation of its children's images, and placing a group's image back
# means distributing it over those children by position. Neither is a picture
# rule, a storage conversion or an arithmetic operation, so neither belongs in
# the semantics layer; and neither invents a byte, because every child is already
# held at its own declared width.


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
    # Reference modification is ONE-BASED, and `acas_posting.cobol.move.ref_mod`
    # is the primitive for it: never Python slicing, whose bounds differ by one.
    record.va_code.va_system = move.ref_mod(image, 1, 1)
    record.va_code.va_group.va_first = move.ref_mod(image, 2, 1)
    record.va_code.va_group.va_second = move.ref_mod(image, 3, 1)


def _place_va_group(record: WsValueRecord, image: str) -> None:
    """Distribute a two-byte image over `va-group`'s two children.

    `05 va-group.` [copybooks/wsval.cob:L12] is the SUB-group `va-first` ||
    `va-second`, and moving into it leaves `va-system` untouched - which is what
    lets [sales/sl055.cbl:L486], [sales/sl055.cbl:L490] and
    [sales/sl055.cbl:L494] change the group while the "S" set at
    [sales/sl055.cbl:L482] carries over.

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


#  da000-mainline section.  [sales/sl055.cbl:L305]


def _da000_mainline(ctx: _Sl055Context) -> None:
    """`da000-mainline section.` - open everything, then fall into the loop.

    The program's entry section. Control falls out of its bottom straight into
    `da010-Read-Loop.` [sales/sl055.cbl:L364], with no transfer statement between
    them, which is the first of this program's two fall-throughs.

    THE VALUE FILE IS OPENED, CLOSED, RE-OPENED AND CLOSED AGAIN - AN EXISTENCE
    PROBE  [sales/sl055.cbl:L319-L324]

        319      perform  Value-Open-Input.
        320      if       fs-reply not = zero
        321               perform Value-Close
        322               perform Value-Open-Output
        323      end-if
        324      perform Value-Close.

    Read as a normal open this looks redundant, and it is not: it is an
    existence probe. Try to open for input; if that fails the file does not
    exist, so close it and open it for OUTPUT, which creates it; then close it
    UNCONDITIONALLY, whichever branch ran. The file is then re-opened properly
    at [sales/sl055.cbl:L357]. All four verbs are performed in that order here -
    collapsing them, or hoisting the final close into the `if`, would change the
    sequence of statements the data-access layer sees, and section 0.6.6's state
    diff is sensitive to exactly that.

    THE COBOL-FILE-SYSTEM BLOCK  [sales/sl055.cbl:L326-L348]
    Reproduced as a gate and then refused; see `CobolFileSystemPathUnavailable`
    and rule R-1 in the module docstring.

    OMITTED, AND EACH ONE RECORDED IN THE TRACEABILITY FOOTER: the terminal
    geometry read and arithmetic [sales/sl055.cbl:L308-L314], the two
    `set ENVIRONMENT` statements [sales/sl055.cbl:L316-L317], and the screen
    positions and colours of the three displays.

    Args:
        ctx: The program's state. Its `system_record` is read for
            `File-System-Used`; its `file_access`, `ws_value_record` and
            `open_item_file_2` are all written.

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

    # 319  perform  Value-Open-Input.
    ctx.verbs.value_open_input(ctx)
    # 320  if       fs-reply not = zero
    if arithmetic.compare(ctx.fs_reply, FsReply.SUCCESS) != 0:
        # 321  perform Value-Close
        ctx.verbs.value_close(ctx)
        # 322  perform Value-Open-Output
        ctx.verbs.value_open_output(ctx)
    # 323  end-if
    # 324  perform Value-Close.      <- UNCONDITIONAL, outside the `if`
    ctx.verbs.value_close(ctx)

    # 326  if       FS-Cobol-Files-Used
    if _IS_FS_COBOL_FILES_USED(
        ctx.system_record.system_data_block.rdbms_flat_statuses.file_system_used
    ):
        # 339  display  SL125  at 2301
        #
        # Emitted before raising, because it is the message the compiled program
        # produces on the only path out of this block that has an observable
        # effect. `display SL002 at 2401` [sales/sl055.cbl:L340] is the
        # acknowledgement prompt and is dropped with the rest of them.
        _LOG.error("%s", _SL125)
        # 344  move 8 to WS-Term-Code
        #
        # PRESERVED, and set BEFORE the raise. Eight is this program's own abort
        # value - not the General Ledger's five - and `load000.`
        # [sales/sales.cbl:L710-L712] treats anything above seven as a serious
        # error, rewriting the system records and `goback`ing out of the sales
        # menu. Setting it means the caller's linkage block carries the same
        # signal the compiled program would leave there, whatever this module then
        # does about the rest of the block.
        ctx.ws_calling_data.ws_term_code = int(
            move.move_numeric(
                _TERM_CODE_ANALYSIS_FILE_MISSING,
                _calling_descriptor("ws_term_code"),
            )
        )
        # 345  goback
        #
        # The compiled program returns here. This module cannot simply return,
        # because the three sub-outcomes of the block are not distinguishable
        # without `CBL_CHECK_FILE_EXIST`: the analysis file may be present (no
        # observable effect at all), or absent and created by `sl070` (Analysis and
        # Value rows written), or absent and still absent (term code eight and a
        # return). Rule R-1 forbids running either COBOL routine, so the outcome
        # cannot be computed - and picking one silently would be a behaviour
        # change dressed as a migration. AMBIGUITY Q-56: does any scenario set
        # `File-System-Used` to zero?
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
    # 348  end-if

    # 349  move     1 to File-Key-No.
    #
    # The first of NINE. Triply redundant - `Value-Read-Indexed` sets it and the
    # `acas013.` dispatch paragraph sets it again - and preserved regardless
    # (rule R-3, question Q-55). This one is not even followed by an indexed
    # operation: the next file verb is `Invoice-Open` at [sales/sl055.cbl:L356].
    ctx.file_access.logging_data.file_key_no = int(move.move_numeric(1, _D_FILE_KEY_NO))

    # 351  display  prog-name at 0101 with foreground-color 2 erase eos.
    # 352  display  "Invoice Post Extract" at 1201  with foreground-color 2.
    _LOG.info("%s", _PROG_NAME)
    _LOG.info("%s", _TITLE)

    # 353  perform  zz070-Convert-Date.
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

    # 356  perform  Invoice-Open.
    ctx.verbs.invoice_open(ctx)
    # 357  perform  Value-Open.        <- RE-OPENED; L324 closed it
    ctx.verbs.value_open(ctx)
    # 358  perform  Analysis-Open.
    ctx.verbs.analysis_open(ctx)

    # 359  open     extend open-item-file-2.
    # 360  if       fs-reply not = zero
    # 361           close open-item-file-2
    # 362           open output open-item-file-2.
    #
    # THE EXTEND-THEN-FALLBACK IDIOM, the same shape as `gl080`'s archive open.
    # `copybooks/seloi2.cob` declares no `OPTIONAL`, so extending a file that does
    # not exist fails and the fallback creates it. Both branches are reproduced;
    # note that the `close` runs even though the `open extend` did not succeed,
    # which is what the COBOL writes.
    ctx.open_item_file_2.open_extend(ctx.file_access)
    if arithmetic.compare(ctx.fs_reply, FsReply.SUCCESS) != 0:
        ctx.open_item_file_2.close(ctx.file_access)
        ctx.open_item_file_2.open_output(ctx.file_access)

    # FALL-THROUGH 1 OF 2: control leaves this section here and enters
    # `da010-Read-Loop.` [sales/sl055.cbl:L364] with no transfer statement. `run`
    # calls `_da010_read_loop` next, so the fall-through is visible rather than
    # implied.



#  da010-Read-Loop.  [sales/sl055.cbl:L364]


def _da010_read_loop(ctx: _Sl055Context) -> _Label:
    """`da010-Read-Loop.` - the item-level loop, and the value-analysis build.

    THE PARAGRAPH IS ONE STATEMENT: an inline `PERFORM UNTIL ... END-PERFORM`
    spanning [sales/sl055.cbl:L365-L424], carrying the maintainer's own comment
    "changed 18/01/25 for clean up using inline perform". It is ALREADY a
    structured loop in the frozen source and is transcribed as a `while`, not
    rebuilt as a `GO TO` cycle. Only ONE of the four `GO TO` classes applies
    inside it, at [sales/sl055.cbl:L368]; the other five departures are
    `EXIT PERFORM` statements, which are not `GO TO`s.

    THE FOUR WAYS OUT, AND THEY ARE NOT INTERCHANGEABLE

        L368  go to da040-Close-Files    GO TO class 2 - end of file on the READ
        L371  exit perform               falls through to da020-Header-Analysis
        L365  the UNTIL condition        also falls through to da020, but having
                                         seen a status left by one of the SIX
                                         verbs the body performs after the read
        L374/L377/L403/L409/L423         exit perform cycle - iterate

    Why the `UNTIL` and the explicit L367 test are both reproduced is set out in
    the module docstring: `Fs-Reply` is one shared field with several producers,
    so the two tests can see different values and lead to different places.

    THE ACCUMULATION HAPPENS TWICE, AND THE TWO BLOCKS ARE NOT FACTORED TOGETHER.
    [sales/sl055.cbl:L388-L396] accumulates into the SPECIFIC analysis group;
    [sales/sl055.cbl:L405] then blanks `va-second`, re-reads, and
    [sales/sl055.cbl:L411-L419] accumulates the identical four figures into the
    PARENT group. The two blocks differ in what surrounds them - the first
    branches on `v-exists` to choose `Value-Write` over `Value-Rewrite`
    [sales/sl055.cbl:L397-L401], the second always rewrites
    [sales/sl055.cbl:L420] - and section 0.6.1's judgement on the three divergent
    moving-average blocks applies in spirit: "Normalising them into one helper
    would be the single easiest way to fail this migration." They stay separate.

    NOTE WHAT `db000-Create` CAN LEAVE BEHIND. Its path through
    [sales/sl055.cbl:L552-L554] returns with `va-second` ALREADY BLANKED by
    [sales/sl055.cbl:L547] and only `WS-PA-Code` restored - so the accumulation at
    L388 then applies to the blanked group, and the test at L402 finds a space and
    skips the second accumulation entirely. That is not a special case handled
    here; it is what falls out of transcribing both paragraphs faithfully, and it
    is recorded so a reader does not "correct" it.

    Args:
        ctx: The program's state.

    Returns:
        `_Label.DA040_CLOSE_FILES` when the read hit end of file - the class-2
        transfer - or `_Label.DA020_HEADER_ANALYSIS` when the loop ended by
        `exit perform` or by its own `UNTIL`, both of which FALL THROUGH.
    """
    # 365  perform  until FS-Reply = 10
    while arithmetic.compare(ctx.fs_reply, FsReply.END_OF_FILE) != 0:
        # 366  perform  Invoice-Read-Next
        ctx.verbs.invoice_read_next(ctx)

        # 367  if       fs-reply = 10
        if arithmetic.compare(ctx.fs_reply, FsReply.END_OF_FILE) == 0:
            # 368  go to da040-Close-Files
            #
            # GO TO class 2 - a forward terminator OUT OF the inline perform,
            # which GnuCOBOL permits and `-Wno-goto-section` stops it warning
            # about. Section 0.6.3, verbatim: "the target label is followed by
            # real work - closing files, printing totals, rewriting a control
            # record - so the transformation is `break` PLUS faithful placement of
            # that work after the loop, not `break` alone. Mis-splitting here
            # would silently drop end-of-run processing." Here that work is the
            # FOUR special-total stores and the FOUR closes at
            # [sales/sl055.cbl:L482-L501], and dropping it would lose the whole
            # value-analysis roll-up. It is placed in `run`'s post-loop block.
            return _Label.DA040_CLOSE_FILES
        # 369  end-if

        # 370  if       ih-test = zero
        #
        # THE HEADER/LINE DISCRIMINATOR. `ih-test` is bytes 9-10 of the record -
        # the same two bytes as `Item-Nos` and `il-line` - and a header carries
        # item number zero.
        if arithmetic.compare(ctx.ws_invoice_record.ih_test, 0) == 0:
            # 371  exit perform   *> Header-Analysis
            #
            # EXIT PERFORM [sales/sl055.cbl:L371] - not a `GO TO`, and not one of
            # the four classes. It leaves the inline perform, after which control
            # FALLS THROUGH out of the paragraph and into
            # `da020-Header-Analysis.` [sales/sl055.cbl:L426]. That fall-through
            # is the reason the header processing is a separate paragraph at all.
            break
        # 372  end-if

        line = ctx.ws_invoice_record.line

        # 373  if       il-analyised
        if _IS_IL_ANALYISED(line.il_update):
            # 374  exit perform cycle
            #
            # EXIT PERFORM CYCLE [sales/sl055.cbl:L374] - iterate. The line has
            # already been counted by an earlier run.
            continue
        # 375  end-if

        # 376  if       il-product (1:1) = "/"		*> comment only
        #
        # REFERENCE MODIFICATION IS ONE-BASED. `move.ref_mod` is the primitive;
        # Python slicing would be off by one and is never used here.
        if move.ref_mod(line.il_product, 1, 1) == _COMMENT_LINE_MARKER:
            # 377  exit perform cycle
            #
            # EXIT PERFORM CYCLE [sales/sl055.cbl:L377] - iterate.
            continue
        # 378  end-if

        value = ctx.ws_value_record

        # 379  move     "S"   to va-system
        value.va_code.va_system = _VALUE_SYSTEM_SALES
        # 380  move     il-pa to va-group
        #
        # A GROUP MOVE: `il-pa pic xx` [copybooks/slwsinv2.cob:L95] into the
        # two-byte sub-group `va-group` [copybooks/wsval.cob:L12], which leaves
        # `va-system` alone.
        _place_va_group(
            value, move.move_group(line.il_pa, _D_VA_GROUP, sending_field=_D_IL_PA, length=2)
        )
        # 381  move     1     to v-exists
        ctx.v_exists = int(move.move_numeric(1, _D_V_EXISTS))
        # 382  move     1 to File-Key-No
        ctx.file_access.logging_data.file_key_no = int(move.move_numeric(1, _D_FILE_KEY_NO))
        # 383  perform  Value-Read-Indexed
        ctx.verbs.value_read_indexed(ctx)

        # 384  if       fs-reply = 21 or = 23
        #
        # THE ABBREVIATED RELATION FORM, testing BOTH statuses. Four sites in this
        # program write it this way - L384, L408, L477 and L535 - and four write
        # only `= 21`: L552, L565, L597 and L614. That inconsistency is real and
        # each site is reproduced exactly as written. The data-access layer's own
        # finding is that `FsReply.KEY_NOT_FOUND` (23) is documented but never
        # actually returned, which makes the `or = 23` arms DEAD IN PRACTICE -
        # they are kept regardless, because removing a test is a behaviour change
        # (rule R-3) and because a later handler change could revive them.
        if (
            arithmetic.compare(ctx.fs_reply, FsReply.INVALID_KEY_ON_START) == 0
            or arithmetic.compare(ctx.fs_reply, FsReply.KEY_NOT_FOUND) == 0
        ):
            # 385  perform  db000-Create
            _db000_create(ctx)
            # 386  move zero to v-exists
            ctx.v_exists = int(move.move_figurative(move.ZERO, _D_V_EXISTS))
        # 387  end-if

        # ---- ACCUMULATION 1 OF 2: the SPECIFIC analysis group  [L388-L396] ----

        # 388  add      1  to  VA-T-This
        value.va_t_this = int(
            arithmetic.add_to(1, receiver_value=value.va_t_this, receiving=_D_VA_T_THIS)
        )
        # 389  add      1  to  VA-T-Year
        value.va_t_year = int(
            arithmetic.add_to(1, receiver_value=value.va_t_year, receiving=_D_VA_T_YEAR)
        )
        # 390  if       il-type not = 3			*> Cr. notes
        if line.il_type != _IL_TYPE_CREDIT_NOTE:
            # 391  add il-net to  VA-V-This
            value.va_v_this = Decimal(
                arithmetic.add_to(
                    line.il_net, receiver_value=value.va_v_this, receiving=_D_VA_V_THIS
                )
            )
            # 392  add il-net to  VA-V-Year
            value.va_v_year = Decimal(
                arithmetic.add_to(
                    line.il_net, receiver_value=value.va_v_year, receiving=_D_VA_V_YEAR
                )
            )
        # 393  else
        else:
            # 394  subtract il-net from VA-V-This
            #
            # `SUBTRACT a FROM b` with no `GIVING` is `b = b - a`, so the RECEIVER
            # is the field named after `FROM`. Getting the direction wrong here
            # would invert every credit note in the value analysis.
            value.va_v_this = Decimal(
                arithmetic.subtract_from(
                    line.il_net, receiver_value=value.va_v_this, receiving=_D_VA_V_THIS
                )
            )
            # 395  subtract il-net from VA-V-Year
            value.va_v_year = Decimal(
                arithmetic.subtract_from(
                    line.il_net, receiver_value=value.va_v_year, receiving=_D_VA_V_YEAR
                )
            )
        # 396  end-if

        # 397  if       v-exists  = zero
        if arithmetic.compare(ctx.v_exists, 0) == 0:
            # 398  perform  Value-Write
            ctx.verbs.value_write(ctx)
        # 399  else
        else:
            # 400  perform  Value-Rewrite
            ctx.verbs.value_rewrite(ctx)
        # 401  end-if

        # 402  if       va-second  = space
        if value.va_code.va_group.va_second == _VA_SECOND_SPACE:
            # 403  exit perform cycle
            #
            # EXIT PERFORM CYCLE [sales/sl055.cbl:L403] - iterate. The group has
            # no second character, so it IS its own parent and there is nothing to
            # roll up. Note that this is also the path taken when `db000-Create`
            # returned through [sales/sl055.cbl:L554] having blanked `va-second`
            # itself - and in that case the line is never marked analysed, because
            # [sales/sl055.cbl:L421-L422] is below this point.
            continue
        # 404  end-if

        # 405  move     space  to  va-second
        value.va_code.va_group.va_second = str(
            move.move_figurative(move.SPACE, _D_VA_SECOND)
        )
        # 406  move     1 to File-Key-No
        ctx.file_access.logging_data.file_key_no = int(move.move_numeric(1, _D_FILE_KEY_NO))
        # 407  perform  Value-Read-Indexed
        ctx.verbs.value_read_indexed(ctx)
        # 408  if       fs-reply = 21 or = 23
        if (
            arithmetic.compare(ctx.fs_reply, FsReply.INVALID_KEY_ON_START) == 0
            or arithmetic.compare(ctx.fs_reply, FsReply.KEY_NOT_FOUND) == 0
        ):
            # 409  exit perform cycle
            #
            # EXIT PERFORM CYCLE [sales/sl055.cbl:L409] - iterate. THE PARENT
            # GROUP IS NOT CREATED HERE, unlike the specific group at L385: a
            # missing parent is simply skipped, and the line is left unmarked
            # because L421-L422 is below. `db000-Create` is not performed.
            continue
        # 410  end-if

        # ---- ACCUMULATION 2 OF 2: the PARENT group, `va-second` blanked ----
        #
        # The identical four statements as L388-L396, deliberately written out
        # again rather than shared with them. See the docstring.

        # 411  add      1 to VA-T-This
        value.va_t_this = int(
            arithmetic.add_to(1, receiver_value=value.va_t_this, receiving=_D_VA_T_THIS)
        )
        # 412  add      1 to VA-T-Year
        value.va_t_year = int(
            arithmetic.add_to(1, receiver_value=value.va_t_year, receiving=_D_VA_T_YEAR)
        )
        # 413  if       il-type not = 3
        if line.il_type != _IL_TYPE_CREDIT_NOTE:
            # 414  add il-net to  VA-V-This
            value.va_v_this = Decimal(
                arithmetic.add_to(
                    line.il_net, receiver_value=value.va_v_this, receiving=_D_VA_V_THIS
                )
            )
            # 415  add il-net to  VA-V-Year
            value.va_v_year = Decimal(
                arithmetic.add_to(
                    line.il_net, receiver_value=value.va_v_year, receiving=_D_VA_V_YEAR
                )
            )
        # 416  else
        else:
            # 417  subtract il-net from VA-V-This
            value.va_v_this = Decimal(
                arithmetic.subtract_from(
                    line.il_net, receiver_value=value.va_v_this, receiving=_D_VA_V_THIS
                )
            )
            # 418  subtract il-net from VA-V-Year
            value.va_v_year = Decimal(
                arithmetic.subtract_from(
                    line.il_net, receiver_value=value.va_v_year, receiving=_D_VA_V_YEAR
                )
            )
        # 419  end-if

        # 420  perform  Value-Rewrite      <- ALWAYS a rewrite, never a write
        ctx.verbs.value_rewrite(ctx)
        # 421  move     "Z"  to  il-update 	*> Analysied flag changed from z (1/6/13)
        line.il_update = _IL_UPDATE_ANALYSED
        # 422  perform  Invoice-Rewrite
        ctx.verbs.invoice_rewrite(ctx)
        # 423  exit     perform cycle
        #
        # EXIT PERFORM CYCLE [sales/sl055.cbl:L423] - iterate. The last statement
        # of the loop body, so it is the one departure that changes nothing; it is
        # transcribed anyway because rule R-5 annotates every site, and because
        # its presence is what makes the `UNTIL` test at L365 the next thing
        # evaluated.
        continue
    # 424  end-perform.

    # FALL-THROUGH 2 OF 2 REACHED FROM HERE: whether the loop ended by the
    # `exit perform` at L371 or by its own `UNTIL` at L365, control leaves the
    # paragraph and enters `da020-Header-Analysis.` [sales/sl055.cbl:L426] with no
    # transfer statement.
    return _Label.DA020_HEADER_ANALYSIS



#  da020-Header-Analysis.  [sales/sl055.cbl:L426]   *> Headers only


def _da020_header_analysis(ctx: _Sl055Context) -> _Label:
    """`da020-Header-Analysis.` - the header-level processing and four totals.

    Reached only by FALL-THROUGH out of `da010-Read-Loop.`, never by a transfer,
    and ending in `go to da010-Read-Loop.` [sales/sl055.cbl:L470] - which is what
    makes this paragraph the body of the OUTER loop. Its trailing source comment
    reads "Headers only".

    THE THREE SIGN FLIPS  [sales/sl055.cbl:L446], [sales/sl055.cbl:L457],
    [sales/sl055.cbl:L463] are `MULTIPLY -1 BY work-2` with NO `GIVING`, so
    `work-2` is both the multiplicand AND the receiver. This is the Sales/Purchase
    form; the General Ledger's is
    `multiply pre-amount by -1 giving pre-amount.`, operands reversed and with
    `GIVING`. Each site is annotated at the call.

    THE TWO VAT BRANCHES DIFFER ONLY IN ONE OPERATOR AND MUST NOT BE MERGED

        447      if       work-2 not = zero and
        448               ih-type not = 1
        449               add 1 to ws-vat-totalt
        450               add work-2 to ws-vat-totalv.
        451      if       work-2 not = zero and
        452               ih-type = 1
        453               add 1 to ws-vatr-totalt
        454               add work-2 to ws-vatr-totalv.

    `not = 1` against `= 1`, accumulating into DIFFERENT total pairs - `vat` for
    everything that is not a receipt, `vatr` for receipts. Note also the unusual
    continuation style, a trailing `and` at the end of the first line of each
    condition; both remain two-condition `AND`s.

    Args:
        ctx: The program's state. The invoice header view is read and its
            `ih-update` written; the four special-total pairs are accumulated.

    Returns:
        `_Label.DA010_READ_LOOP` for the three class-1 back-edges at L428, L442
        and L470, or `_Label.DA030_SKIP_INVOICE` for the two class-4 transfers at
        L431 and L436.
    """
    header = ctx.ws_invoice_record.header
    prime = header.ih_prime
    sub = header.ih_sub_prime
    fig = sub.ih_fig

    # 427  if       ih-analyised and applied
    #
    # TWO DIFFERENT FIELDS, not one compound test: `ih-analyised`
    # [copybooks/slwsinv2.cob:L89] is a condition name on `ih-update`, and
    # `applied` [copybooks/slwsinv2.cob:L74] is one on `ih-status`. Both happen to
    # test for "Z", which is what makes the statement easy to misread.
    if _IS_IH_ANALYISED(sub.ih_update) and _IS_APPLIED(sub.ih_status):
        # 428  go to da010-Read-Loop.
        #
        # GO TO class 1 - a loop-back to the head of the outer loop. Fully
        # processed by an earlier run; nothing more to do with it.
        return _Label.DA010_READ_LOOP

    # 430  if       ih-type = 4                	*> Proforma's
    if arithmetic.compare(prime.ih_type, _IH_TYPE_PROFORMA) == 0:
        # 431  go to da030-Skip-Invoice.
        #
        # GO TO class 4 - SITE 1 OF 4. See the equivalence proof in
        # `_da030_skip_invoice`'s docstring and at the call site in `run`. A
        # proforma is never posted, so the whole invoice is skipped past.
        return _Label.DA030_SKIP_INVOICE

    # 433  if       pending
    # 434    or     ih-status-L not = "L"
    #
    # An `OR`, not an `AND`: either the invoice is still pending, or it has not
    # been printed. `pending` [copybooks/slwsinv2.cob:L72] is a condition name on
    # `ih-status`; `ih-status-L` [copybooks/slwsinv2.cob:L76] is a separate field.
    if _IS_PENDING(sub.ih_status) or sub.ih_status_l != _IH_STATUS_L_PRINTED:
        # 435  move 1 to ws-p-flag
        #
        # THE FLAG THAT PRODUCES THE FIRST EARLY `goback`. Tested at
        # [sales/sl055.cbl:L503].
        ctx.ws_p_flag = int(move.move_numeric(1, _D_WS_P_FLAG))
        # 436  go to da030-Skip-Invoice.
        #
        # GO TO class 4 - SITE 2 OF 4.
        return _Label.DA030_SKIP_INVOICE

    # 438  perform  dd000-Extract.
    _dd000_extract(ctx)

    # 440  if       ih-analyised
    #
    # RE-TESTED, because `dd000-Extract` may have set it - no, it sets `ih-status`
    # and `ih-status-A` [sales/sl055.cbl:L679-L680] and leaves `ih-update` alone.
    # So this test sees whatever the record arrived with, and is true only for a
    # header that was analysed by an earlier run but not yet applied - which
    # L427's two-field test let through. The invoice is rewritten (persisting the
    # `ih-status`/`ih-status-A` stamps `dd000-Extract` just made) and the four
    # special totals are NOT accumulated for it.
    if _IS_IH_ANALYISED(sub.ih_update):
        # 441  perform  Invoice-Rewrite
        ctx.verbs.invoice_rewrite(ctx)
        # 442  go to da010-Read-Loop.
        #
        # GO TO class 1 - loop-back.
        return _Label.DA010_READ_LOOP

    # ---- SPECIAL TOTAL 1: VAT  [sales/sl055.cbl:L444-L454] ----

    # 444  add      ih-c-vat ih-vat ih-e-vat giving work-2.
    #
    # A THREE-ADDEND VARIADIC `ADD ... GIVING`: the three terms are summed at
    # intermediate precision and the sum is quantized ONCE, into `work-2`. Summing
    # pairwise with a store between each would truncate twice.
    ctx.work_2 = Decimal(
        arithmetic.add_giving(
            fig.ih_c_vat, fig.ih_vat, fig.ih_e_vat, receiving=_D_WORK_2
        )
    )
    # 445  if       ih-type = 3
    if arithmetic.compare(prime.ih_type, _IH_TYPE_CREDIT_NOTE) == 0:
        # 446  multiply -1 by work-2.
        #
        # SIGN FLIP 1 OF 3. `MULTIPLY -1 BY work-2` - no `GIVING`, receiver second.
        ctx.work_2 = Decimal(
            arithmetic.multiply_by(_NEGATE, ctx.work_2, _D_WORK_2)
        )
    # 447  if       work-2 not = zero and
    # 448           ih-type not = 1
    if (
        arithmetic.compare(ctx.work_2, 0) != 0
        and arithmetic.compare(prime.ih_type, _IH_TYPE_RECEIPT) != 0
    ):
        # 449  add 1 to ws-vat-totalt
        ctx.ws_vat_totalt = int(
            arithmetic.add_to(1, receiver_value=ctx.ws_vat_totalt, receiving=_D_WS_VAT_TOTALT)
        )
        # 450  add work-2 to ws-vat-totalv.
        ctx.ws_vat_totalv = Decimal(
            arithmetic.add_to(
                ctx.work_2, receiver_value=ctx.ws_vat_totalv, receiving=_D_WS_VAT_TOTALV
            )
        )
    # 451  if       work-2 not = zero and
    # 452           ih-type = 1
    #
    # THE SAME `work-2`, THE OPPOSITE TYPE TEST, A DIFFERENT TOTAL PAIR. Not an
    # `else` in the source and not written as one here: two independent `if`s, so
    # a `work-2` of zero falls through both.
    if (
        arithmetic.compare(ctx.work_2, 0) != 0
        and arithmetic.compare(prime.ih_type, _IH_TYPE_RECEIPT) == 0
    ):
        # 453  add 1 to ws-vatr-totalt
        ctx.ws_vatr_totalt = int(
            arithmetic.add_to(
                1, receiver_value=ctx.ws_vatr_totalt, receiving=_D_WS_VATR_TOTALT
            )
        )
        # 454  add work-2 to ws-vatr-totalv.
        ctx.ws_vatr_totalv = Decimal(
            arithmetic.add_to(
                ctx.work_2, receiver_value=ctx.ws_vatr_totalv, receiving=_D_WS_VATR_TOTALV
            )
        )

    # ---- SPECIAL TOTAL 2: CARRIAGE  [sales/sl055.cbl:L455-L460] ----

    # 455  move     ih-carriage to work-2.
    ctx.work_2 = Decimal(
        move.move_numeric(fig.ih_carriage, _D_WORK_2, sending_field=_D_IH_CARRIAGE)
    )
    # 456  if       ih-type = 3
    if arithmetic.compare(prime.ih_type, _IH_TYPE_CREDIT_NOTE) == 0:
        # 457  multiply -1 by work-2.
        #
        # SIGN FLIP 2 OF 3.
        ctx.work_2 = Decimal(
            arithmetic.multiply_by(_NEGATE, ctx.work_2, _D_WORK_2)
        )
    # 458  if       work-2 not = zero
    #
    # ONE condition here, not two: carriage is counted for EVERY invoice type,
    # receipts included. The asymmetry against the VAT pair above is in the source.
    if arithmetic.compare(ctx.work_2, 0) != 0:
        # 459  add 1 to ws-carr-totalt
        ctx.ws_carr_totalt = int(
            arithmetic.add_to(
                1, receiver_value=ctx.ws_carr_totalt, receiving=_D_WS_CARR_TOTALT
            )
        )
        # 460  add work-2 to ws-carr-totalv.
        ctx.ws_carr_totalv = Decimal(
            arithmetic.add_to(
                ctx.work_2, receiver_value=ctx.ws_carr_totalv, receiving=_D_WS_CARR_TOTALV
            )
        )

    # ---- SPECIAL TOTAL 3: DISCOUNT (the deduction amount)  [L461-L466] ----

    # 461  move     ih-deduct-amt to work-2.
    #
    # AN UNSIGNED SENDER INTO A SIGNED RECEIVER. `ih-deduct-amt pic 999v99 comp`
    # [copybooks/slwsinv2.cob:L82] cannot hold a negative; `work-2 pic s9(7)v99
    # comp-3` can, which is what lets the flip below have any effect.
    ctx.work_2 = Decimal(
        move.move_numeric(sub.ih_deduct_amt, _D_WORK_2, sending_field=_D_IH_DEDUCT_AMT)
    )
    # 462  if       ih-type = 3
    if arithmetic.compare(prime.ih_type, _IH_TYPE_CREDIT_NOTE) == 0:
        # 463  multiply -1 by work-2.
        #
        # SIGN FLIP 3 OF 3.
        ctx.work_2 = Decimal(
            arithmetic.multiply_by(_NEGATE, ctx.work_2, _D_WORK_2)
        )
    # 464  if       work-2 not = zero
    if arithmetic.compare(ctx.work_2, 0) != 0:
        # 465  add 1 to ws-disc-totalt
        ctx.ws_disc_totalt = int(
            arithmetic.add_to(
                1, receiver_value=ctx.ws_disc_totalt, receiving=_D_WS_DISC_TOTALT
            )
        )
        # 466  add work-2 to ws-disc-totalv.
        ctx.ws_disc_totalv = Decimal(
            arithmetic.add_to(
                ctx.work_2, receiver_value=ctx.ws_disc_totalv, receiving=_D_WS_DISC_TOTALV
            )
        )

    # 468  move     "Z" to ih-update.
    sub.ih_update = _IH_UPDATE_ANALYSED
    # 469  perform  Invoice-Rewrite.
    ctx.verbs.invoice_rewrite(ctx)
    # 470  go       to da010-Read-Loop.
    #
    # GO TO class 1 - THE OUTER LOOP'S PRINCIPAL BACK-EDGE. Re-entering the
    # paragraph `da010-Read-Loop.` restarts the inline perform inside it, which is
    # why the two loops nest the way they do.
    return _Label.DA010_READ_LOOP


#  da030-Skip-Invoice.  [sales/sl055.cbl:L472]


def _da030_skip_invoice(ctx: _Sl055Context) -> _Label:
    """`da030-Skip-Invoice.` - reposition past this invoice's remaining items.

    THE PARAGRAPH, VERBATIM  [sales/sl055.cbl:L472-L479]

        472  da030-Skip-Invoice.
        473      add      1 to invoice-nos.
        474      move     zeros to item-nos.
        475      set      fn-not-less-than to true.
        476      perform  Invoice-Start.
        477      if       fs-reply = 21 or = 23
        478               go to da040-Close-Files.
        479      go       to da010-Read-Loop.

    Bump the invoice number, zero the item number, and START the invoice file at
    the first record whose key is not less than that - which lands on the next
    invoice's header and so skips every remaining line of this one. The key is
    written through the GENERIC view, `Invoice-Nos` and `Item-Nos`
    [copybooks/slwsinv2.cob:L29-L30], which are the same ten bytes as
    `ih-invoice`/`ih-test`.

    THE CLASS-4 EQUIVALENCE PROOF, for both call sites [sales/sl055.cbl:L431] and
    [sales/sl055.cbl:L436]. In the compiled program each of those two `GO TO`s
    transfers control INTO this paragraph, whose own last two statements then
    transfer it onward - to `da040-Close-Files` when the START reported an invalid
    key, and otherwise to `da010-Read-Loop`. Neither call site does anything after
    its `GO TO`, and this paragraph is not reachable by fall-through from
    `da020-Header-Analysis` because L470 transfers away first. So the observable
    behaviour of "transfer to L472" is exactly "execute L473-L476, then transfer
    where L477-L479 say" - which is what a call followed by an explicit transfer
    on this function's returned label performs. The two sites are proven
    INDIVIDUALLY because each must be shown not to have trailing work of its own,
    and neither has: L431 is the whole body of its `if`, and L436's `if` body is
    `move 1 to ws-p-flag` followed immediately by the transfer.

    `pl055` HAS NO EQUIVALENT. It carries no `PInvoice-Start` at all, so its
    header-analysis paragraph cannot reposition and must read forward instead -
    one of the six divergences in the module docstring.

    Args:
        ctx: The program's state. The invoice area's key is rewritten and
            `Access-Type` is set.

    Returns:
        `_Label.DA040_CLOSE_FILES` for the class-2 transfer at L478, or
        `_Label.DA010_READ_LOOP` for the class-1 loop-back at L479.
    """
    area = ctx.ws_invoice_record

    # 473  add      1 to invoice-nos.
    area.invoice_nos = int(
        arithmetic.add_to(1, receiver_value=area.invoice_nos, receiving=_D_INVOICE_NOS)
    )
    # 474  move     zeros to item-nos.
    #
    # `ZEROS`, one of the figurative constant's three spellings. The receiver is
    # numeric, so the VALUE zero is stored - not the character.
    area.item_nos = int(move.move_figurative(move.ZERO, _D_ITEM_NOS))
    # 475  set      fn-not-less-than to true.
    #
    # THE ISAM `START` RELATION, SET THROUGH THE ACCESS-TYPE VOCABULARY.
    # `88 fn-not-less-than value 8.` [copybooks/wsfnctn.cob:L115] is declared on
    # `Access-Type`, and `SET ... TO TRUE` stores the condition's value there.
    # `AccessType.NOT_LESS_THAN` is that vocabulary as `acas_posting.dal.status`
    # publishes it; a raw `8` is never written.
    ctx.file_access.access_type = int(AccessType.NOT_LESS_THAN)
    # 476  perform  Invoice-Start.        *>  start invoice-file key not < invoice-key invalid key
    ctx.verbs.invoice_start(ctx)
    # 477  if       fs-reply = 21 or = 23
    if (
        arithmetic.compare(ctx.fs_reply, FsReply.INVALID_KEY_ON_START) == 0
        or arithmetic.compare(ctx.fs_reply, FsReply.KEY_NOT_FOUND) == 0
    ):
        # 478  go to da040-Close-Files.
        #
        # GO TO class 2 - there is no invoice at or beyond that key, so the file is
        # exhausted and the post-loop block runs.
        return _Label.DA040_CLOSE_FILES
    # 479  go       to da010-Read-Loop.
    #
    # GO TO class 1 - loop-back.
    return _Label.DA010_READ_LOOP



#  da040-Close-Files.  [sales/sl055.cbl:L481]


def _da040_close_files(ctx: _Sl055Context) -> _Label:
    """`da040-Close-Files.` - the four special totals, the four closes, the exits.

    THE POST-LOOP BLOCK. Both class-2 transfers - [sales/sl055.cbl:L368] out of
    the inline perform and [sales/sl055.cbl:L478] out of `da030-Skip-Invoice` -
    land here, and section 0.6.3 is explicit about what that obliges:

        "the target label is followed by real work - closing files, printing
        totals, rewriting a control record - so the transformation is `break`
        PLUS faithful placement of that work after the loop, not `break` alone.
        Mis-splitting here would silently drop end-of-run processing."

    Here that work is the four VALUE-ANALYSIS SPECIAL TOTALS and the four closes.
    Dropping it would lose the entire roll-up: the per-group totals accumulated in
    `da010-Read-Loop` would be written, but the four whole-run totals - VAT,
    VAT-on-receipts, carriage and discount - would never reach `VALUEANAL-REC`.

    THE KEY IS SET ONCE AND THEN AMENDED THREE TIMES  [sales/sl055.cbl:L482-L497]

        482      move     "Svo" to va-code.
        486      move     "vp" to va-group.
        490      move     "zc" to va-group.
        494      move     "zd" to va-group.

    L482 moves three characters into the whole of `va-code`, setting `va-system`
    to "S" and `va-group` to "vo". The three later moves are into `va-group`
    ALONE, two characters each, so the "S" CARRIES OVER and the four keys are
    `Svo`, `Svp`, `Szc` and `Szd`. Re-setting `va-system` here would be an added
    statement; reading the later moves as three-byte ones would corrupt the key.

    THESE ARE NOT THE PERIOD TOTALS. `VALUEANAL-REC` rows keyed `Svo`/`Svp`/
    `Szc`/`Szd` are value-analysis SPECIAL TOTALS. The two period totals this
    program writes are `SYSTOT-REC` columns and are written in `dd000-Extract`,
    once per header, not once per run.

    Args:
        ctx: The program's state. The value record's key and totals are set, the
            four files are closed, and the two exit flags are tested.

    Returns:
        `_Label.GOBACK` for either early exit at L509 or L518, or
        `_Label.DA999_MENU_EXIT` for the fall-through into `da999-Menu-Exit.`.
    """
    value = ctx.ws_value_record

    # ---- SPECIAL TOTAL 1: "Svo" - VAT  [sales/sl055.cbl:L482-L485] ----

    # 482  move     "Svo" to va-code.
    _place_va_code(
        value, move.move_group(_SPECIAL_TOTAL_VAT_CODE, _D_VA_CODE, length=3)
    )
    # 483  move     ws-vat-totalt to work-3.
    #
    # LIKE FOR LIKE. `ws-vat-totalt` [sales/sl055.cbl:L211] and `work-3`
    # [sales/sl055.cbl:L210] are both `pic s9(5) comp`, so this move neither
    # truncates nor changes sign. The sign drift in this chain appears one step
    # LATER, where `dc000-Store-Specials` adds the signed `work-3` into the
    # UNSIGNED `va-t-this pic 9(5) comp` [copybooks/wsval.cob:L18].
    ctx.work_3 = int(
        move.move_numeric(ctx.ws_vat_totalt, _D_WORK_3, sending_field=_D_WS_VAT_TOTALT)
    )
    # 484  move     ws-vat-totalv to work-2.
    ctx.work_2 = Decimal(
        move.move_numeric(ctx.ws_vat_totalv, _D_WORK_2, sending_field=_D_WS_VAT_TOTALV)
    )
    # 485  perform  dc000-Store-Specials
    _dc000_store_specials(ctx)

    # ---- SPECIAL TOTAL 2: "Svp" - VAT on receipts  [L486-L489] ----

    # 486  move     "vp" to va-group.
    #
    # TWO characters, into the SUB-group - `va-system` keeps the "S" from L482.
    _place_va_group(
        value, move.move_group(_SPECIAL_TOTAL_VATR_GROUP, _D_VA_GROUP, length=2)
    )
    # 487  move     ws-vatr-totalt to work-3.
    ctx.work_3 = int(
        move.move_numeric(ctx.ws_vatr_totalt, _D_WORK_3, sending_field=_D_WS_VATR_TOTALT)
    )
    # 488  move     ws-vatr-totalv to work-2.
    ctx.work_2 = Decimal(
        move.move_numeric(ctx.ws_vatr_totalv, _D_WORK_2, sending_field=_D_WS_VATR_TOTALV)
    )
    # 489  perform  dc000-Store-Specials
    _dc000_store_specials(ctx)

    # ---- SPECIAL TOTAL 3: "Szc" - carriage  [L490-L493] ----

    # 490  move     "zc" to va-group.
    _place_va_group(
        value, move.move_group(_SPECIAL_TOTAL_CARRIAGE_GROUP, _D_VA_GROUP, length=2)
    )
    # 491  move     ws-carr-totalt to work-3.
    ctx.work_3 = int(
        move.move_numeric(ctx.ws_carr_totalt, _D_WORK_3, sending_field=_D_WS_CARR_TOTALT)
    )
    # 492  move     ws-carr-totalv to work-2.
    ctx.work_2 = Decimal(
        move.move_numeric(ctx.ws_carr_totalv, _D_WORK_2, sending_field=_D_WS_CARR_TOTALV)
    )
    # 493  perform  dc000-Store-Specials
    _dc000_store_specials(ctx)

    # ---- SPECIAL TOTAL 4: "Szd" - discount  [L494-L497] ----

    # 494  move     "zd" to va-group.
    _place_va_group(
        value, move.move_group(_SPECIAL_TOTAL_DISCOUNT_GROUP, _D_VA_GROUP, length=2)
    )
    # 495  move     ws-disc-totalt to work-3.
    ctx.work_3 = int(
        move.move_numeric(ctx.ws_disc_totalt, _D_WORK_3, sending_field=_D_WS_DISC_TOTALT)
    )
    # 496  move     ws-disc-totalv to work-2.
    ctx.work_2 = Decimal(
        move.move_numeric(ctx.ws_disc_totalv, _D_WORK_2, sending_field=_D_WS_DISC_TOTALV)
    )
    # 497  perform  dc000-Store-Specials
    _dc000_store_specials(ctx)

    # ---- THE FOUR CLOSES  [sales/sl055.cbl:L498-L501] ----

    # 498  perform  Invoice-Close.
    ctx.verbs.invoice_close(ctx)
    # 499  perform  Value-Close.
    ctx.verbs.value_close(ctx)
    # 500  perform  Analysis-Close.
    ctx.verbs.analysis_close(ctx)
    # 501  close    open-item-file-2.
    #
    # The work sequence, not a table. Closing it is a status-setting no-op; the
    # records it accumulated stay in the sequence for `sl060` to read.
    ctx.open_item_file_2.close(ctx.file_access)

    # ---- THE TWO EARLY EXITS  [sales/sl055.cbl:L503-L518] ----

    # 503  if       ws-p-flag not = zero   *> Unprinted invoice are present
    if arithmetic.compare(ctx.ws_p_flag, 0) != 0:
        # 504  display SL122        at line ws-23-lines col 1
        _LOG.warning(_SL122)
        # 505  if     WS-Caller not = "xl150"
        #
        # THE CODEBASE'S OWN UNATTENDED-MODE CHECK. `xl150` is the end-of-cycle
        # driver, out of scope per section 0.2.2; when it is the caller the
        # acknowledgement prompt is skipped. The BRANCH is preserved because it
        # is evidence that headless operation was designed for rather than bolted
        # on; only the `accept` inside it is dropped, per section 0.3.4's rule for
        # prompts that merely pause.
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

    # 511  if       ws-Anal-Flag not = zero
    #
    # Set by `db010-Create-Anal.` [sales/sl055.cbl:L584] when an emergency
    # analysis record had to be invented. A cross-section flag: written in the
    # `db000-Create` section, read here.
    if arithmetic.compare(ctx.ws_anal_flag, 0) != 0:
        # 512  display SL123 at 1201 with foreground-color 2
        _LOG.warning(_SL123)
        # 513  display SL126 at 1401 with foreground-color 2
        _LOG.warning(_SL126)
        # 514  if     WS-Caller not = "xl150"
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

    # FALL-THROUGH 2 OF 2  [sales/sl055.cbl:L518 -> sales/sl055.cbl:L520]
    #
    # With neither flag set there is no transfer statement at the bottom of
    # `da040-Close-Files.`, so control falls into `da999-Menu-Exit.` and its
    # `goback.`. Recorded explicitly because a reader diffing the two files will
    # otherwise look for the `GO TO` that is not there.
    return _Label.DA999_MENU_EXIT


#  da999-Menu-Exit.  [sales/sl055.cbl:L520]


def _da999_menu_exit() -> None:
    """`da999-Menu-Exit.` - the normal end of the program.

    THE PARAGRAPH, VERBATIM  [sales/sl055.cbl:L520-L521]

        520  da999-Menu-Exit.
        521      goback.

    `GOBACK` returns to the caller - `sales/sales.cbl`'s `load000.`
    [sales/sales.cbl:L698], which then tests `WS-Term-Code`. Reached only by
    fall-through from `da040-Close-Files.`; nothing transfers to it. It retains a
    named function of its own even though its whole body is a `return`, because
    rule R-5 requires a function per paragraph and section 0.7.4 C-4 is explicit
    that this holds "even where its `GO TO` becomes a `continue`, a `break` or a
    `return`".
    """
    # 521  goback.
    #
    # Returning from `run` is the `GOBACK`. `WS-Term-Code` is left exactly as the
    # caller set it - this program only ever writes it on the missing-analysis-file
    # path [sales/sl055.cbl:L344].
    return None



def _group_move_analysis_record_to_value_record(ctx: _Sl055Context) -> None:
    """`move WS-Analysis-Record to WS-Value-Record` - the byte-image copy alone.

    Live at [sales/sl055.cbl:L538], [sales/sl055.cbl:L556] and
    [sales/sl055.cbl:L568], and at every one of those three sites the very next
    statement zeroes the six totals. This helper performs ONLY the move; the
    zeroing is written out inline at each of the three sites, so that the three
    statement PAIRS stay three visibly separate pairs in the transcription.

    WHAT A GROUP MOVE ACTUALLY DOES, AND WHY THE ZEROING IS NOT OPTIONAL. A
    `MOVE` whose sender is a group item is an ALPHANUMERIC move: the sender's
    bytes are copied left-justified into the receiver and the receiver's remaining
    bytes are SPACE-FILLED, with no regard for the receiver's subordinate
    pictures. `01 WS-Analysis-Record.` [copybooks/wsanal.cob:L9] is thirty-six
    bytes - `3 + 6 + 24 + 3`, exactly as its own header comment says - while
    `01 WS-Value-Record.` [copybooks/wsval.cob:L9] is sixty-six: the same
    thirty-six, then three `pic 9(5) comp` counts at four bytes each and three
    `pic s9(8)v99 comp-3` values at six bytes each. So the move copies the first
    thirty-six bytes field-for-field - the two layouts are picture-identical over
    that span - and fills the last THIRTY with `X"20"`, leaving three binary
    counts and three packed values holding spaces. Those are not valid numeric
    representations, which is precisely why
    `move zero to VA-T-This va-t-last VA-T-Year VA-V-This va-v-last VA-V-Year`
    follows immediately at every site. The pair is one idea in two statements.

    # AMBIGUITY Q-54 [sales/sl055.cbl:L538-L540] - the space-filled intermediate
    # state is not materialised here, and cannot be: `acas_posting.cobol.move`
    # refuses `MOVE SPACE` into a numeric receiver, reproducing the compiler's own
    # refusal, and a `Decimal` has no "six spaces" value to hold. Because the very
    # next statement overwrites all six fields unconditionally, the intermediate is
    # unobservable - no read, no write and no comparison occurs between the two
    # statements - so eliding it changes nothing that a table dump can see. The
    # oracle must nonetheless confirm that GnuCOBOL does not diagnose or trap the
    # invalid packed data at the moment of the move itself.

    Args:
        ctx: The program's state. `WS-Value-Record`'s first four fields are
            overwritten from `WS-Analysis-Record`; its six totals are left for the
            caller's next statement to zero.
    """
    analysis = ctx.ws_analysis_record
    value = ctx.ws_value_record

    # The thirty-six-byte span, copied field-for-field because the two layouts are
    # picture-identical across it. Each leaf goes through the `cobol.move`
    # primitive against its OWN descriptor, so `va-gl` is converted as a six-digit
    # DISPLAY integer rather than as three characters of text.
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

    Live at [sales/sl055.cbl:L531], [sales/sl055.cbl:L548] and
    [sales/sl055.cbl:L575]. Both operands are three-byte group items whose three
    children are `pic x` apiece, so the move is a straight three-byte copy with no
    padding and no truncation.

    Args:
        ctx: The program's state. `WS-PA-Code`'s three children are overwritten
            from `va-code`'s.
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


#  db000-Create section.  [sales/sl055.cbl:L527]


def _db000_create(ctx: _Sl055Context) -> None:
    """`db000-Create section.` - find the analysis record, or invent one.

    THE SECTION, AS A WHOLE. Performed from two places -
    [sales/sl055.cbl:L385] inside the item loop and [sales/sl055.cbl:L598] inside
    `dc000-Store-Specials` - both times because a `Value-Read-Indexed` found no
    row for the key. Its job is to seed `WS-Value-Record` from the matching
    `ANALYSIS-REC` description so that the caller's `Value-Write` has a name and a
    general-ledger code to write, and, when even the analysis record is missing,
    to WRITE ONE with the description "Emergency Name - Missing" and then retry.

    THE SECTION IS TWO PARAGRAPHS THAT TRANSFER TO EACH OTHER

        530  DB000-Create-Main.        <-- entry, and the target of L585
        536      go to db010-Create-Anal.       (class 4, forward)
        574  db010-Create-Anal.
        585      go       to db000-Create-Main. (class 4, BACKWARD - a retry)
        587  db999-Main-Exit.

    THE CLASS-4 EQUIVALENCE PROOF FOR [sales/sl055.cbl:L536] - SITE 3 OF 4. The
    transfer is the entire body of its `if`, and nothing in `DB000-Create-Main`
    follows it that could be skipped: every statement after L536 is reachable only
    when the `if` was false. `db010-Create-Anal` is not reachable by fall-through
    either, because L572 transfers away first. So "transfer to L574" is exactly
    "execute L575-L584, then transfer where L585 says" - a call followed by the
    explicit transfer this loop performs on the returned label.

    THE CLASS-4 EQUIVALENCE PROOF FOR [sales/sl055.cbl:L585] - SITE 4 OF 4. This
    is the harder one, because the transfer goes BACKWARD to a sibling paragraph
    in the same section, forming a cycle: main -> anal -> main. It is
    unconditional and it is the last statement of its paragraph, so nothing
    follows it in `db010-Create-Anal` and the cycle has exactly one entry point,
    `DB000-Create-Main`'s first statement. A cycle with a single entry, a single
    back-edge and no work after the back-edge is a `while` loop over the entry
    point - which is what the loop below is. On re-entry `Analysis-Read-Indexed`
    is retried against the record `db010-Create-Anal` has just written, so the
    second pass normally takes the `if` at L535 as FALSE and runs on to an exit.

    # AMBIGUITY Q-51 [sales/sl055.cbl:L585] - THE RETRY HAS NO ITERATION GUARD.
    # If `Analysis-Write` [sales/sl055.cbl:L580] fails - a duplicate key, a lock,
    # a closed file - the re-read at L534 fails again, L536 transfers again, and
    # the compiled program spins forever with no message. The loop below spins the
    # same way, deliberately: rule R-3 forbids added validations and section 0.7.4
    # C-3 makes reproduction the whole point, so NO counter, NO ceiling and NO
    # break-out has been added. The oracle must establish what the compiled program
    # actually does when the write fails, since a hang is the one behaviour a
    # state diff cannot capture.

    Args:
        ctx: The program's state. `WS-Value-Record` is seeded from
            `WS-Analysis-Record`; `save-code`, `ws-Anal-Flag` and `File-Key-No`
            are written; `ANALYSIS-REC` rows may be created and a `VALUEANAL-REC`
            row may be written.
    """
    while True:
        label = _db000_create_main(ctx)
        if label is _Label.DB999_MAIN_EXIT:
            # GO TO class 3 - L543, L554, L566 and L572 all transfer to
            # `db999-Main-Exit.`, whose `exit section.` returns to the `PERFORM`
            # that entered this section.
            _db999_main_exit()
            return
        # GO TO class 4 - SITE 3 OF 4 [sales/sl055.cbl:L536]. The named call, then
        # the explicit transfer on what `db010-Create-Anal` itself decides.
        #
        # GO TO class 4 - SITE 4 OF 4 [sales/sl055.cbl:L585]. `db010-Create-Anal`'s
        # last statement is an UNCONDITIONAL transfer back to `DB000-Create-Main`,
        # so `_Label.DB000_CREATE_MAIN` is the only label it can return and the
        # back-edge is taken every time. No test of the returned label is written
        # here, because writing one would be an `if` the compiled program does not
        # have (rule R-3); the label is discarded exactly as COBOL discards the
        # question.
        _db010_create_anal(ctx)
        continue


#  DB000-Create-Main.  [sales/sl055.cbl:L530]


def _db000_create_main(ctx: _Sl055Context) -> _Label:
    """`DB000-Create-Main.` - seed the value record from the analysis record.

    Declared in MIXED CASE at [sales/sl055.cbl:L530] and spelled entirely in
    lower case by the `GO TO` that targets it at [sales/sl055.cbl:L585]. COBOL
    folds case in user-defined words, so the two spell one label; the
    inconsistency is recorded because a reader grepping for the exact string will
    otherwise find only one of the two occurrences.
    Reproduced deliberately per R-4; DO NOT FIX - there is nothing to fix, only
    something to notice.

    THE THREE-PASS SHAPE. The paragraph reads the analysis file up to three times
    for one value key:

    1.  L531-L540, for the key exactly as given. Missing -> `db010-Create-Anal`.
    2.  L547-L558, for the same key with `va-second` BLANKED - the group-level
        description. Present -> a `Value-Write` at L560 creates the group-level
        value row too.
    3.  L562-L570, for the original key again, restored from `save-code`, so that
        the record area the caller returns to carries the SPECIFIC description
        rather than the group one.

    Pass 3 performs no write at all: it exists purely to leave `WS-Value-Record`
    holding the right description for the caller's own `Value-Write` or
    `Value-Rewrite`. Reordering or eliding it would write the group description
    against the specific key.

    THE `FS-Reply` TEST IS NOT THE SAME AT ALL THREE PASSES. L535 tests
    `= 21 or = 23`; L552 and L565 test only `= 21`. Transcribed exactly as
    written at each site - see the module docstring's note on the eight sites and
    DAL finding N2.

    Args:
        ctx: The program's state.

    Returns:
        `_Label.DB010_CREATE_ANAL` for the class-4 transfer at L536, or
        `_Label.DB999_MAIN_EXIT` for the class-3 transfers at L543, L554, L566
        and L572.
    """
    value = ctx.ws_value_record
    analysis = ctx.ws_analysis_record

    # ---- PASS 1: the key as given  [sales/sl055.cbl:L531-L540] ----

    # 531  move     va-code  to  WS-PA-Code.
    _move_va_code_to_ws_pa_code(ctx)
    # 533  move     1 to File-Key-No.
    #
    # Set again for every indexed operation, exactly as the source does. Nine such
    # statements in this program; section 0.8.4 puts removing them out of scope.
    ctx.file_access.logging_data.file_key_no = int(
        move.move_numeric(1, _D_FILE_KEY_NO)
    )
    # 534  perform  Analysis-Read-Indexed.
    ctx.verbs.analysis_read_indexed(ctx)
    # 535  if       FS-Reply = 21 or = 23
    if (
        arithmetic.compare(ctx.fs_reply, FsReply.INVALID_KEY_ON_START) == 0
        or arithmetic.compare(ctx.fs_reply, FsReply.KEY_NOT_FOUND) == 0
    ):
        # 536  go to db010-Create-Anal.
        #
        # GO TO class 4 - SITE 3 OF 4. Proof in `_db000_create`'s docstring.
        return _Label.DB010_CREATE_ANAL

    # 538  move     WS-Analysis-Record  to WS-Value-Record
    _group_move_analysis_record_to_value_record(ctx)
    # 539  move     zero  to  VA-T-This  va-t-last VA-T-Year
    # 540                     VA-V-This  va-v-last VA-V-Year.
    #
    # ONE statement, SIX receivers, each converted independently against its own
    # picture - and the statement that makes the six totals valid numbers again
    # after the group move space-filled them.
    (
        value.va_t_this,
        value.va_t_last,
        value.va_t_year,
        value.va_v_this,
        value.va_v_last,
        value.va_v_year,
    ) = move.move_to_all(move.ZERO, _VALUE_TOTALS_CLEARED_BY_DB000)

    # 542  if       va-second  = space
    if value.va_code.va_group.va_second == _VA_SECOND_SPACE:
        # 543  go to db999-Main-Exit.
        #
        # GO TO class 3 - the key IS the group-level key, so passes 2 and 3 would
        # re-read the same record. Nothing more to do.
        return _Label.DB999_MAIN_EXIT

    # ---- PASS 2: the same key with `va-second` blanked  [L545-L560] ----

    # 545  move     va-code  to  save-code.
    #
    # `save-code pic xxx` [sales/sl055.cbl:L202] holds the SPECIFIC key across the
    # group-level read, so that pass 3 can restore it.
    ctx.save_code = move.move_group(
        _three_byte_group_image(
            value.va_code.va_system,
            value.va_code.va_group.va_first,
            value.va_code.va_group.va_second,
        ),
        _D_SAVE_CODE,
        length=3,
    )
    # 547  move     space    to  va-second.
    value.va_code.va_group.va_second = str(
        move.move_figurative(move.SPACE, _D_VA_SECOND)
    )
    # 548  move     va-code  to  WS-PA-Code.
    _move_va_code_to_ws_pa_code(ctx)
    # 550  move     1 to File-Key-No.
    ctx.file_access.logging_data.file_key_no = int(
        move.move_numeric(1, _D_FILE_KEY_NO)
    )
    # 551  perform  Analysis-Read-Indexed.
    ctx.verbs.analysis_read_indexed(ctx)
    # 552  if       FS-Reply = 21
    #
    # ONLY 21 HERE, where L535 tested `= 21 or = 23`. Transcribed as written.
    if arithmetic.compare(ctx.fs_reply, FsReply.INVALID_KEY_ON_START) == 0:
        # 553  move  save-code  to  WS-PA-Code
        #
        # The analysis key is restored, but `va-code` is NOT - it is left with
        # `va-second` blanked from L547. So the caller returns holding the
        # group-level value key rather than the specific one it arrived with.
        # Recorded as a finding, not corrected.
        _place_pa_code(
            analysis, move.move_group(ctx.save_code, _D_WS_PA_CODE, length=3)
        )
        # 554  go to db999-Main-Exit.
        #
        # GO TO class 3.
        return _Label.DB999_MAIN_EXIT

    # 556  move     WS-Analysis-Record  to WS-Value-Record
    _group_move_analysis_record_to_value_record(ctx)
    # 557  move     zero  to  VA-T-This  va-t-last  VA-T-Year
    # 558                     VA-V-This  va-v-last  VA-V-Year.
    #
    # THE SECOND OF THE THREE IDENTICAL PAIRS, written out rather than shared. The
    # move-then-zero pair is repeated verbatim in the source at three sites and is
    # repeated verbatim here, for the same reason section 0.6.1 gives about the
    # moving averages: a shared helper invites a later reader to "unify" three
    # sites whose surrounding verbs are NOT the same.
    (
        value.va_t_this,
        value.va_t_last,
        value.va_t_year,
        value.va_v_this,
        value.va_v_last,
        value.va_v_year,
    ) = move.move_to_all(move.ZERO, _VALUE_TOTALS_CLEARED_BY_DB000)

    # 560  perform  Value-Write.
    #
    # THE GROUP-LEVEL VALUE ROW IS CREATED HERE, keyed with `va-second` blank, and
    # it is created UNCONDITIONALLY - no read established that it was absent. A
    # duplicate-key failure is neither tested nor reported.
    ctx.verbs.value_write(ctx)

    # ---- PASS 3: the original key, restored  [L562-L570] ----

    # 562  move     save-code  to  va-code  WS-PA-Code.
    #
    # ONE statement, TWO group receivers. Each is converted independently, and
    # both are three bytes wide, so neither pads nor truncates.
    va_code_image, pa_code_image = move.move_to_all(
        ctx.save_code, (_D_VA_CODE, _D_WS_PA_CODE)
    )
    _place_va_code(value, str(va_code_image))
    _place_pa_code(analysis, str(pa_code_image))
    # 563  move     1 to File-Key-No.
    ctx.file_access.logging_data.file_key_no = int(
        move.move_numeric(1, _D_FILE_KEY_NO)
    )
    # 564  perform  Analysis-Read-Indexed.
    ctx.verbs.analysis_read_indexed(ctx)
    # 565  if       FS-Reply = 21
    #
    # ONLY 21, again. And note what it means: the specific analysis record was
    # found at pass 1 and is being re-read here, so a 21 now would mean it
    # vanished between the two reads.
    if arithmetic.compare(ctx.fs_reply, FsReply.INVALID_KEY_ON_START) == 0:
        # 566  go to  db999-Main-Exit.
        #
        # GO TO class 3.
        return _Label.DB999_MAIN_EXIT

    # 568  move     WS-Analysis-Record  to WS-Value-Record
    _group_move_analysis_record_to_value_record(ctx)
    # 569  move     zero  to  VA-T-This  va-t-last  VA-T-Year
    # 570                     VA-V-This  va-v-last  VA-V-Year.
    #
    # THE THIRD OF THE THREE IDENTICAL PAIRS.
    (
        value.va_t_this,
        value.va_t_last,
        value.va_t_year,
        value.va_v_this,
        value.va_v_last,
        value.va_v_year,
    ) = move.move_to_all(move.ZERO, _VALUE_TOTALS_CLEARED_BY_DB000)

    # 572  go       to db999-Main-Exit.
    #
    # GO TO class 3 - the normal end of the paragraph, written as an explicit
    # transfer rather than left to fall through into `db010-Create-Anal.`, which
    # is what makes that paragraph reachable only by the class-4 transfer at L536.
    return _Label.DB999_MAIN_EXIT


#  db010-Create-Anal.  [sales/sl055.cbl:L574]


def _db010_create_anal(ctx: _Sl055Context) -> _Label:
    """`db010-Create-Anal.` - invent the missing analysis record, then retry.

    THE PARAGRAPH, VERBATIM  [sales/sl055.cbl:L574-L585]

        574  db010-Create-Anal.
        575      move     va-code to WS-PA-Code.
        576      move     zero to pa-gl.
        577      move     spaces to pa-print.
        578      move     "Emergency Name - Missing" to pa-desc.
        579      move     1 to File-Key-No.
        580      perform  Analysis-Write.
        581      if       pa-second not = space
        582               move space to pa-second
        583               perform  Analysis-Write.
        584      move     1 to ws-Anal-Flag.
        585      go       to db000-Create-Main.

    TWO ROWS MAY BE WRITTEN, NOT ONE. The specific code is written first; then, if
    the code has a second character, `pa-second` is blanked and the SAME record is
    written AGAIN under the group-level key. Both rows carry the emergency
    description. `Analysis-Write` at L583 is a second, distinct write - not a
    rewrite of the first - so the analysis file gains two rows from one visit.

    THE FLAG IS WHY THE OPERATOR EVER FINDS OUT. `move 1 to ws-Anal-Flag`
    [sales/sl055.cbl:L584] is tested far away, at [sales/sl055.cbl:L511], and
    produces the second early `goback` and the "You will need to update this"
    message. It is the only trace this paragraph leaves behind.

    Args:
        ctx: The program's state. `WS-Analysis-Record` is overwritten, one or two
            `ANALYSIS-REC` rows are written, and `ws-Anal-Flag` is set.

    Returns:
        `_Label.DB000_CREATE_MAIN` always - the unconditional class-4 back-edge at
        L585.
    """
    analysis = ctx.ws_analysis_record

    # 575  move     va-code to WS-PA-Code.
    _move_va_code_to_ws_pa_code(ctx)
    # 576  move     zero to pa-gl.
    analysis.pa_gl = int(move.move_figurative(move.ZERO, _D_PA_GL))
    # 577  move     spaces to pa-print.
    #
    # `SPACES`, the plural spelling of the same figurative constant as `SPACE`.
    analysis.pa_print = str(move.move_figurative(move.SPACE, _D_PA_PRINT))
    # 578  move     "Emergency Name - Missing" to pa-desc.
    #
    # Twenty-four characters into a `pic x(24)` receiver - an exact fit, with
    # neither truncation nor padding. The literal is the operator's only clue that
    # the analysis file was incomplete.
    analysis.pa_desc = move.move_alphanumeric(_EMERGENCY_NAME, _D_PA_DESC)
    # 579  move     1 to File-Key-No.
    ctx.file_access.logging_data.file_key_no = int(
        move.move_numeric(1, _D_FILE_KEY_NO)
    )
    # 580  perform  Analysis-Write.
    ctx.verbs.analysis_write(ctx)
    # 581  if       pa-second not = space
    if analysis.ws_pa_code.pa_group.pa_second != _PA_SECOND_SPACE:
        # 582  move space to pa-second
        analysis.ws_pa_code.pa_group.pa_second = str(
            move.move_figurative(move.SPACE, _D_PA_SECOND)
        )
        # 583  perform  Analysis-Write.
        #
        # A SECOND WRITE of the same record area under the group-level key. Note
        # that `File-Key-No` is NOT re-set before it, unlike every other indexed
        # operation in this program - it carries over from L579. Recorded as a
        # finding; not corrected.
        ctx.verbs.analysis_write(ctx)
    # 584  move     1 to ws-Anal-Flag.
    ctx.ws_anal_flag = int(move.move_numeric(1, _D_WS_ANAL_FLAG))
    # 585  go       to db000-Create-Main.
    #
    # GO TO class 4 - SITE 4 OF 4, and the only BACKWARD transfer in the program.
    # Proof in `_db000_create`'s docstring; the missing iteration guard is
    # question Q-51.
    return _Label.DB000_CREATE_MAIN


#  db999-Main-Exit.  [sales/sl055.cbl:L587]


def _db999_main_exit() -> None:
    """`db999-Main-Exit.` - `exit section.` [sales/sl055.cbl:L588].

    The class-3 target of [sales/sl055.cbl:L543], [sales/sl055.cbl:L554],
    [sales/sl055.cbl:L566] and [sales/sl055.cbl:L572]. `EXIT SECTION` returns to
    whichever `PERFORM db000-Create` entered the section -
    [sales/sl055.cbl:L385] or [sales/sl055.cbl:L598]. It retains a named function
    of its own under rule R-5 even though its body is empty of effect.
    """
    # 588  exit     section.
    return None



#  dc000-Store-Specials  section.  [sales/sl055.cbl:L590]


def _dc000_store_specials(ctx: _Sl055Context) -> None:
    """`dc000-Store-Specials section.` - add one special total into the value file.

    THE SECTION HEAD CARRIES THE BODY. There is no paragraph label between
    `dc000-Store-Specials section.` [sales/sl055.cbl:L590] and its first statement
    at [sales/sl055.cbl:L593], so the statements belong to the SECTION itself and
    only the exit is a separate paragraph. Section 0.4.2's inventory omits this
    section head altogether, citing only its exit paragraph; the measured
    inventory in the module docstring supersedes it.

    Called four times in a row from `da040-Close-Files.`
    [sales/sl055.cbl:L485], [sales/sl055.cbl:L489], [sales/sl055.cbl:L493] and
    [sales/sl055.cbl:L497], each time with a different key in `va-code` and the
    matching count and value already staged in `work-3` and `work-2`.

    THE TWICE-OVER PATTERN, AGAIN AND SEPARATELY. Exactly as in
    `da010-Read-Loop`, the totals are added first against the SPECIFIC key
    [sales/sl055.cbl:L601-L604] and then against the same key with `va-second`
    BLANKED [sales/sl055.cbl:L617-L620]. The two blocks are byte-identical in the
    source and are written out twice here rather than shared, because the verbs
    around them are NOT the same: the first block chooses between `Value-Write`
    and `Value-Rewrite` on `v-exists`, while the second always `Value-Rewrite`s.
    Section 0.6.1's warning about the moving averages is the governing precedent -
    "Normalising them into one helper would be the single easiest way to fail this
    migration."

    THE SIGN DRIFT AT THE COUNT ADDS. `work-3 pic s9(5) comp`
    [sales/sl055.cbl:L210] is SIGNED and `va-t-this pic 9(5) comp`
    [copybooks/wsval.cob:L18] is UNSIGNED, so a negative `work-3` could not be
    represented in the receiver. It never is - `work-3` only ever receives one of
    the four `ws-*-totalt` counts [sales/sl055.cbl:L211-L214], themselves
    `pic s9(5) comp` but only ever incremented - but the widths are transcribed as
    declared rather than as reasoned about, and `acas_posting.cobol.arithmetic`
    applies the receiver's own sign rule.

    Args:
        ctx: The program's state. `v-exists` and `File-Key-No` are written, and
            one or two `VALUEANAL-REC` rows are written or rewritten.
    """
    value = ctx.ws_value_record

    # 593  move     1  to  v-exists.
    ctx.v_exists = int(move.move_numeric(1, _D_V_EXISTS))

    # 595  move     1 to File-Key-No.
    ctx.file_access.logging_data.file_key_no = int(
        move.move_numeric(1, _D_FILE_KEY_NO)
    )
    # 596  perform  Value-Read-Indexed.
    ctx.verbs.value_read_indexed(ctx)
    # 597  if       fs-Reply = 21
    #
    # ONLY 21 HERE. The two reads inside `da010-Read-Loop` at
    # [sales/sl055.cbl:L384] and [sales/sl055.cbl:L408] test
    # `= 21 or = 23` for the very same verb against the very same file. The
    # inconsistency is real and is transcribed at each site as written.
    if arithmetic.compare(ctx.fs_reply, FsReply.INVALID_KEY_ON_START) == 0:
        # 598  perform  db000-Create
        #
        # The second of the section's two call sites. The record area comes back
        # seeded from `ANALYSIS-REC` with all six totals at zero, ready to be
        # written rather than rewritten.
        _db000_create(ctx)
        # 599  move zero to v-exists.
        ctx.v_exists = int(move.move_figurative(move.ZERO, _D_V_EXISTS))

    # ---- ACCUMULATION 1 OF 2: the specific key  [sales/sl055.cbl:L601-L604] ----
    #
    # FOUR SEPARATE `ADD` STATEMENTS, not one statement with four receivers: each
    # has its own terminating period in the source and each stores independently.

    # 601  add      work-3 to  VA-T-This.
    value.va_t_this = int(
        arithmetic.add_to(
            ctx.work_3, receiver_value=value.va_t_this, receiving=_D_VA_T_THIS
        )
    )
    # 602  add      work-3 to  VA-T-Year.
    value.va_t_year = int(
        arithmetic.add_to(
            ctx.work_3, receiver_value=value.va_t_year, receiving=_D_VA_T_YEAR
        )
    )
    # 603  add      work-2 to  VA-V-This.
    value.va_v_this = Decimal(
        arithmetic.add_to(
            ctx.work_2, receiver_value=value.va_v_this, receiving=_D_VA_V_THIS
        )
    )
    # 604  add      work-2 to  VA-V-Year.
    value.va_v_year = Decimal(
        arithmetic.add_to(
            ctx.work_2, receiver_value=value.va_v_year, receiving=_D_VA_V_YEAR
        )
    )

    # 606  if       v-exists  = zero
    if arithmetic.compare(ctx.v_exists, 0) == 0:
        # 607  perform  Value-Write
        ctx.verbs.value_write(ctx)
    else:
        # 608  else
        # 609  perform  Value-Rewrite.
        ctx.verbs.value_rewrite(ctx)

    # ---- ACCUMULATION 2 OF 2: the group-level key  [L611-L621] ----

    # 611  move     space  to  va-second.
    #
    # The key is amended IN PLACE, so the group-level row is the same key with its
    # third byte blanked - which is how every analysis code rolls up into its
    # two-character group.
    value.va_code.va_group.va_second = str(
        move.move_figurative(move.SPACE, _D_VA_SECOND)
    )
    # 612  move     1 to File-Key-No.
    ctx.file_access.logging_data.file_key_no = int(
        move.move_numeric(1, _D_FILE_KEY_NO)
    )
    # 613  perform  Value-Read-Indexed.
    ctx.verbs.value_read_indexed(ctx)
    # 614  if       FS-Reply = 21
    #
    # ONLY 21 again - and note the asymmetry with the block above: a missing
    # SPECIFIC row causes `db000-Create` to invent one, while a missing GROUP-LEVEL
    # row simply ends the section with the group total silently not accumulated.
    if arithmetic.compare(ctx.fs_reply, FsReply.INVALID_KEY_ON_START) == 0:
        # 615  go to dc999-Main-Exit.
        #
        # GO TO class 3 - the section's exit paragraph, then back to the caller.
        _dc999_main_exit()
        return

    # 617  add      work-3 to  VA-T-This.
    #
    # THE SAME FOUR ADDS, DELIBERATELY DUPLICATED. See the docstring.
    value.va_t_this = int(
        arithmetic.add_to(
            ctx.work_3, receiver_value=value.va_t_this, receiving=_D_VA_T_THIS
        )
    )
    # 618  add      work-3 to  VA-T-Year.
    value.va_t_year = int(
        arithmetic.add_to(
            ctx.work_3, receiver_value=value.va_t_year, receiving=_D_VA_T_YEAR
        )
    )
    # 619  add      work-2 to  VA-V-This.
    value.va_v_this = Decimal(
        arithmetic.add_to(
            ctx.work_2, receiver_value=value.va_v_this, receiving=_D_VA_V_THIS
        )
    )
    # 620  add      work-2 to  VA-V-Year.
    value.va_v_year = Decimal(
        arithmetic.add_to(
            ctx.work_2, receiver_value=value.va_v_year, receiving=_D_VA_V_YEAR
        )
    )
    # 621  perform  Value-Rewrite.
    #
    # ALWAYS a rewrite here, never a write - the read at L613 proved the row
    # exists, and a 21 would have transferred away at L615.
    ctx.verbs.value_rewrite(ctx)

    # FALL-THROUGH into `dc999-Main-Exit.` [sales/sl055.cbl:L623] - the section's
    # statements end at L621 with no transfer, so control reaches the exit
    # paragraph and its `exit section.`.
    _dc999_main_exit()


#  dc999-Main-Exit.  [sales/sl055.cbl:L623]


def _dc999_main_exit() -> None:
    """`dc999-Main-Exit.` - `exit section.` [sales/sl055.cbl:L624].

    The class-3 target of [sales/sl055.cbl:L615], and also reached by
    fall-through from the end of the section's own statements. `EXIT SECTION`
    returns to the `PERFORM dc000-Store-Specials` that entered it - one of the four
    at [sales/sl055.cbl:L485], [sales/sl055.cbl:L489], [sales/sl055.cbl:L493] and
    [sales/sl055.cbl:L497].
    """
    # 624  exit     section.
    return None



#  dd000-Extract section.  [sales/sl055.cbl:L626]


def _dd000_extract(ctx: _Sl055Context) -> None:
    """`dd000-Extract section.` - build one OTM2 row and the period totals.

    THE SECTION HEAD CARRIES THE BODY, as with `dc000-Store-Specials`: the
    statements begin at [sales/sl055.cbl:L632] with no intervening paragraph
    label, and only `dd999-Main-Ex.` is separate. The source's own header comment
    states the intent:

        629  *> Only process header records here, drop pro-formas.
        630  *>  ignore records which have already been copied.

    Performed once per accepted header, from [sales/sl055.cbl:L438].

    ============================================================================
    THE NINE-FIELD NEGATION - AND WHY IT MUST NOT BE MADE TO MATCH `pl055`
    ============================================================================

    `sl055` negates NINE fields for a credit note  [sales/sl055.cbl:L657-L666]

        657      if       ih-type  = 3                     *>  Cr. Notes
        658               multiply -1  by  oi-deduct-amt
        659               multiply -1  by  oi-deduct-vat
        660               multiply -1  by  oi-net
        661               multiply -1  by  oi-extra
        662               multiply -1  by  oi-carriage
        663               multiply -1  by  oi-vat
        664               multiply -1  by  oi-c-vat
        665               multiply -1  by  oi-e-vat
        666               multiply -1  by  oi-discount.

    `pl055` negates FOUR  [purchase/pl055.cbl:L571-L575]

        571      if       ih-type = 3
        572               multiply  -1  by  oi-net
        573               multiply  -1  by  oi-carriage
        574               multiply  -1  by  oi-vat
        575               multiply  -1  by  oi-c-vat.

    Four names against nine, and the four are a SUBSET of the nine - so the
    purchase extract leaves the two deduction fields, the extra, the VAT-on-extra
    and the discount POSITIVE on a credit note where the sales extract makes them
    negative. `pl055` IS NOT A MIRROR OF `sl055`.
    Reproduced deliberately per R-4; DO NOT FIX, and DO NOT NORMALISE EITHER
    DIRECTION. Adding five names to `pl055` or removing five from here would
    change the sign of five columns of a posted open-item row. Section 0.6.1's
    ruling on the three divergent moving averages is the governing precedent -
    "Normalising them into one helper would be the single easiest way to fail this
    migration" - and the same reasoning holds for two programs that look like
    mirrors and are not. The same note is carried in
    `pl055_order_proof_extract.py`.

    THE SUM DOES NOT USE THE NEGATED FIELDS  [sales/sl055.cbl:L670-L673]. Nine
    addends, and every one of them is an `ih-*` field - the UNNEGATED header - not
    the `oi-*` field the block above has just flipped. So for a credit note the
    OTM2 row carries NEGATIVE money while `ws-inv-amt` carries the POSITIVE sum,
    and [sales/sl055.cbl:L677] then adds that positive sum into
    `sl-credit-notes-this-month`. A "consistent" version - summing the `oi-*`
    fields, or negating `ws-inv-amt` - would flip the sign of a `SYSTOT-REC`
    column.
    Reproduced deliberately per R-4; DO NOT FIX.

    # AMBIGUITY Q-50 [sales/sl055.cbl:L657-L666] vs [sales/sl055.cbl:L670-L673] -
    # whether `sl-credit-notes-this-month` is INTENDED to accumulate credit notes as
    # positive magnitudes (a separate column that the reader subtracts) or is a
    # defect cannot be settled from the source, and it does not need to be: the
    # compiled program's value is the specification either way. The expected figure
    # for the period-end-totals scenario must come from the oracle, never from
    # reasoning about which sign is "right".

    THE TWO PERIOD TOTALS ARE THIS PROGRAM'S ONLY `SYSTOT-REC` WRITES, and they
    are sites 1 and 2 of the nine that section 0.6.4 enumerates across the whole
    migration. Nothing else in the codebase writes
    `sl-invoices-this-month` or `sl-credit-notes-this-month`, so the period-end
    scenario is verifiable by inspecting those two columns alone.

    Args:
        ctx: The program's state. `oi-header` is rebuilt and appended to the OTM2
            sequence; `ih-status` and `ih-status-A` are stamped on the invoice
            record area for the caller to rewrite; `ws-inv-amt` is computed; and
            one of the two `system_record_4` period totals is accumulated.
    """
    header = ctx.ws_invoice_record.header
    prime = header.ih_prime
    sub = header.ih_sub_prime
    fig = sub.ih_fig
    totals = ctx.system_record_4.sales_ledger_data

    # 632  if       applied
    #
    # `applied` [copybooks/slwsinv2.cob:L74] is a condition name on `ih-status`,
    # value "Z" - the header has already been extracted by an earlier run, so
    # extracting it again would duplicate the OTM2 row and double the period total.
    if _IS_APPLIED(sub.ih_status):
        # 633  go to dd999-Main-Ex.
        #
        # GO TO class 3 - the section's exit paragraph, then back to the caller.
        _dd999_main_ex()
        return

    # 635  initialize oi-header with filler.
    #
    # Every elementary item to its category default, FILLER included - which here
    # means twenty-three of the twenty-eight leaves. See
    # `_initialize_oi_header_with_filler` for why the phrase is load-bearing.
    ctx.oi_header = _initialize_oi_header_with_filler()
    oi = ctx.oi_header
    oi_key = oi.oi_key
    oi_filler = oi.filler_1
    oi_money = oi_filler.filler_2

    # 636  move     ih-p-c      to  oi-p-c.
    #
    # NOT one of the nine negated fields: the payment-on-account column keeps its
    # sign on a credit note.
    oi_money.oi_p_c = Decimal(
        move.move_numeric(fig.ih_p_c, _D_OI_P_C, sending_field=_D_IH_P_C)
    )
    # 637  move     ih-invoice  to  oi-invoice.
    oi_key.oi_invoice = int(
        move.move_numeric(prime.ih_invoice, _D_OI_INVOICE, sending_field=_D_IH_INVOICE)
    )
    # 638  move     ih-customer to  oi-customer.
    #
    # A GROUP MOVE between two seven-byte groups whose children are
    # picture-identical - `ih-nos`/`OI-Nos` are both `pic x(6)` and
    # `ih-check`/`OI-Check` are both `pic 9` - so the byte copy is a field-for-field
    # copy and each child is converted against its own descriptor.
    oi_key.oi_customer.oi_nos = move.move_alphanumeric(
        prime.ih_customer.ih_nos, _D_OI_NOS
    )
    oi_key.oi_customer.oi_check = int(
        move.move_numeric(prime.ih_customer.ih_check, _D_OI_CHECK)
    )
    # 639  move     ih-date     to  oi-date.
    #
    # `binary-long` to `binary-long`: the run-date-derived day number, carried
    # across unchanged. `acas_posting.clock` is not consulted - this value arrives
    # inside the record, exactly as it does in the compiled program.
    oi_filler.oi_date = int(
        move.move_numeric(prime.ih_date, _D_OI_DATE, sending_field=_D_IH_DATE)
    )
    # 640  move     zero        to  oi-b-nos oi-b-item.
    #
    # ONE statement, TWO receivers. The batch number and item are not known at
    # extract time; `sl060` fills them when it posts.
    (
        oi_filler.oi_batch.oi_b_nos,
        oi_filler.oi_batch.oi_b_item,
    ) = (
        int(value)
        for value in move.move_to_all(move.ZERO, (_D_OI_B_NOS, _D_OI_B_ITEM))
    )
    # 641  move     ih-order    to  oi-description.
    #
    # `pic x(10)` into `pic x(25)`: left-justified, SPACE-PADDED to twenty-five.
    # The customer's order reference becomes the open item's description.
    oi_filler.oi_description = move.move_alphanumeric(
        prime.ih_order, _D_OI_DESCRIPTION, sending_field=_D_IH_ORDER
    )
    # 642  move     ih-net      to  oi-net.
    #
    # `OI-Approp redefines OI-Net` [copybooks/slwsoi.cob:L38-L39], so the two
    # attribute names are ONE storage location and must never diverge. Every store
    # into `oi-net` is mirrored into `oi-approp` for that reason, here and at the
    # negation below.
    oi_money.oi_net = Decimal(
        move.move_numeric(fig.ih_net, _D_OI_NET, sending_field=_D_IH_NET)
    )
    oi_money.oi_approp = oi_money.oi_net
    # 643  move     ih-extra    to  oi-extra.
    oi_money.oi_extra = Decimal(
        move.move_numeric(fig.ih_extra, _D_OI_EXTRA, sending_field=_D_IH_EXTRA)
    )
    # 644  move     ih-carriage to  oi-carriage.
    oi_money.oi_carriage = Decimal(
        move.move_numeric(fig.ih_carriage, _D_OI_CARRIAGE, sending_field=_D_IH_CARRIAGE)
    )
    # 645  move     ih-vat      to  oi-vat.
    oi_money.oi_vat = Decimal(
        move.move_numeric(fig.ih_vat, _D_OI_VAT, sending_field=_D_IH_VAT)
    )
    # 646  move     ih-c-vat    to  oi-c-vat.
    oi_money.oi_c_vat = Decimal(
        move.move_numeric(fig.ih_c_vat, _D_OI_C_VAT, sending_field=_D_IH_C_VAT)
    )
    # 647  move     ih-e-vat    to  oi-e-vat.
    oi_money.oi_e_vat = Decimal(
        move.move_numeric(fig.ih_e_vat, _D_OI_E_VAT, sending_field=_D_IH_E_VAT)
    )
    # 648  move     ih-discount to  oi-discount.
    oi_money.oi_discount = Decimal(
        move.move_numeric(fig.ih_discount, _D_OI_DISCOUNT, sending_field=_D_IH_DISCOUNT)
    )
    # 649  move     zero        to  oi-paid.
    #
    # NOT one of the nine negated fields either: nothing has been paid against a
    # freshly extracted item, of any type.
    oi_money.oi_paid = Decimal(move.move_figurative(move.ZERO, _D_OI_PAID))
    # 650  move     ih-deduct-amt  to oi-deduct-amt.
    #
    # AN UNSIGNED SENDER INTO A SIGNED RECEIVER: `ih-deduct-amt pic 999v99 comp`
    # [copybooks/slwsinv2.cob:L82] cannot be negative while
    # `OI-Deduct-Amt pic s999v99 comp` [copybooks/slwsoi.cob:L51] can - which is
    # exactly what lets [sales/sl055.cbl:L658] have an effect.
    oi_filler.oi_deduct_amt = Decimal(
        move.move_numeric(
            sub.ih_deduct_amt, _D_OI_DEDUCT_AMT, sending_field=_D_IH_DEDUCT_AMT
        )
    )
    # 651  move     ih-deduct-vat  to oi-deduct-vat.
    oi_filler.oi_deduct_vat = Decimal(
        move.move_numeric(
            sub.ih_deduct_vat, _D_OI_DEDUCT_VAT, sending_field=_D_IH_DEDUCT_VAT
        )
    )
    # 652  move     ih-deduct-days to oi-deduct-days.
    oi_filler.oi_deduct_days = int(
        move.move_numeric(
            sub.ih_deduct_days, _D_OI_DEDUCT_DAYS, sending_field=_D_IH_DEDUCT_DAYS
        )
    )
    # 653  move     zero        to  oi-status oi-date-cleared oi-days.
    #      *> hmm, initialised, not needed but acts as a note
    #
    # ONE statement, THREE receivers. The maintainer's own trailing comment is kept
    # verbatim above: he is noting that `initialize` at L635 already zeroed all
    # three, and that he wrote the statement anyway as documentation. Rule R-5 asks
    # for exactly this kind of authorial evidence to be preserved.
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
    # 654  move     ih-type     to  oi-type.
    #      *> oi-days is credit terms, status = open
    #
    # The maintainer's comment belongs to the PREVIOUS statement, not this one -
    # it explains what L653's two zeroes mean. Kept where he put it.
    oi_filler.oi_type = int(
        move.move_numeric(prime.ih_type, _D_OI_TYPE, sending_field=_D_IH_TYPE)
    )
    # 655  move     space to oi-applied oi-unapl oi-hold-flag.
    #
    # ONE statement, THREE receivers, all `pic x`. Each is converted independently
    # against its own picture.
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

    # ---- THE NINE-FIELD NEGATION  [sales/sl055.cbl:L657-L666] ----
    #
    # ANOMALY [sales/sl055.cbl:L657-L666] vs [purchase/pl055.cbl:L572-L575] - NINE
    # fields here, FOUR in the purchase counterpart, and the four are a subset of
    # the nine. `pl055` IS NOT A MIRROR of this program.
    # Reproduced deliberately per R-4; DO NOT FIX and DO NOT NORMALISE. Full
    # reasoning in this function's docstring.

    # 657  if       ih-type  = 3                                       *>  Cr. Notes
    if arithmetic.compare(prime.ih_type, _IH_TYPE_CREDIT_NOTE) == 0:
        # 658  multiply -1  by  oi-deduct-amt
        #
        # `MULTIPLY -1 BY x` with NO `GIVING`: the receiver is the SECOND operand.
        # The General Ledger family writes `multiply x by -1 giving x` instead, and
        # copying that form here would read the wrong operand as the receiver.
        oi_filler.oi_deduct_amt = Decimal(
            arithmetic.multiply_by(
                _NEGATE, oi_filler.oi_deduct_amt, _D_OI_DEDUCT_AMT
            )
        )
        # 659  multiply -1  by  oi-deduct-vat
        oi_filler.oi_deduct_vat = Decimal(
            arithmetic.multiply_by(
                _NEGATE, oi_filler.oi_deduct_vat, _D_OI_DEDUCT_VAT
            )
        )
        # 660  multiply -1  by  oi-net
        oi_money.oi_net = Decimal(
            arithmetic.multiply_by(_NEGATE, oi_money.oi_net, _D_OI_NET)
        )
        # `OI-Approp` redefines `OI-Net`, so negating one negates both bytes.
        oi_money.oi_approp = oi_money.oi_net
        # 661  multiply -1  by  oi-extra
        oi_money.oi_extra = Decimal(
            arithmetic.multiply_by(_NEGATE, oi_money.oi_extra, _D_OI_EXTRA)
        )
        # 662  multiply -1  by  oi-carriage
        oi_money.oi_carriage = Decimal(
            arithmetic.multiply_by(_NEGATE, oi_money.oi_carriage, _D_OI_CARRIAGE)
        )
        # 663  multiply -1  by  oi-vat
        oi_money.oi_vat = Decimal(
            arithmetic.multiply_by(_NEGATE, oi_money.oi_vat, _D_OI_VAT)
        )
        # 664  multiply -1  by  oi-c-vat
        oi_money.oi_c_vat = Decimal(
            arithmetic.multiply_by(_NEGATE, oi_money.oi_c_vat, _D_OI_C_VAT)
        )
        # 665  multiply -1  by  oi-e-vat
        oi_money.oi_e_vat = Decimal(
            arithmetic.multiply_by(_NEGATE, oi_money.oi_e_vat, _D_OI_E_VAT)
        )
        # 666  multiply -1  by  oi-discount.
        #
        # NINE, in this order, and no more: `oi-p-c` and `oi-paid` are NOT flipped.
        oi_money.oi_discount = Decimal(
            arithmetic.multiply_by(_NEGATE, oi_money.oi_discount, _D_OI_DISCOUNT)
        )

    # 668  move     ih-cr to oi-cr.
    #
    # AFTER the negation block, not before, and outside it - so the credit-terms
    # flag is carried across unflipped for every type. Its position matters only
    # because a reader re-ordering the statements would sweep it into the `if`.
    oi_filler.oi_cr = int(
        move.move_numeric(sub.ih_cr, _D_OI_CR, sending_field=_D_IH_CR)
    )

    # ---- THE NINE-ADDEND SUM AND THE TWO PERIOD TOTALS  [L670-L677] ----

    # 670  if       ih-type not = 1                                    *> not Receipts
    if arithmetic.compare(prime.ih_type, _IH_TYPE_RECEIPT) != 0:
        # 671  add ih-net ih-extra ih-carriage ih-discount ih-vat
        # 672      ih-c-vat ih-e-vat ih-deduct-amt ih-deduct-vat
        # 673         giving ws-inv-amt.
        #
        # NINE ADDENDS in ONE statement, summed at intermediate precision and
        # quantized ONCE into `ws-inv-amt pic s9(7)v99 comp-3`. Adding pairwise with
        # a store between each would truncate nine times instead of once.
        #
        # EVERY ADDEND IS AN `ih-*` FIELD - the UNNEGATED header - even though the
        # `oi-*` copies were flipped six lines above. `pl055`'s counterpart sums
        # FOUR - `add ih-net ih-carriage ih-vat ih-c-vat giving ws-inv-amt`
        # [purchase/pl055.cbl:L580] - so nine against four here too, preserved.
        # Reproduced deliberately per R-4; DO NOT FIX.
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
    # 674  if       ih-type = 2                                        *> Invoice
    if arithmetic.compare(prime.ih_type, _IH_TYPE_INVOICE) == 0:
        # 675  add ws-inv-amt to sl-invoices-this-month.
        #
        # PERIOD TOTAL 1 OF 2, and site 1 of the nine in section 0.6.4. The receiver
        # is a `SYSTOT-REC` column on `system_record_4`, the THIRD linkage parameter
        # - which is why the caller's `overrewrite.` makes this write diff-visible.
        # Un-`ROUNDED`, so the store truncates toward zero; `rounded=False` is the
        # default and `sl055` has no `ROUNDED` site anywhere.
        totals.sl_invoices_this_month = Decimal(
            arithmetic.add_to(
                ctx.ws_inv_amt,
                receiver_value=totals.sl_invoices_this_month,
                receiving=_D_SL_INVOICES_THIS_MONTH,
            )
        )
    # 676  if       ih-type = 3                                        *> Cr. Note
    if arithmetic.compare(prime.ih_type, _IH_TYPE_CREDIT_NOTE) == 0:
        # 677  add ws-inv-amt to sl-credit-notes-this-month.
        #
        # PERIOD TOTAL 2 OF 2, and site 2 of the nine. `ws-inv-amt` here is the
        # POSITIVE sum of the unnegated header fields, so a credit note ADDS a
        # positive magnitude into this column while its OTM2 row carries negatives.
        # Reproduced deliberately per R-4; DO NOT FIX - see question Q-50.
        #
        # Note also that a header whose type is neither 2 nor 3 - a payment,
        # journal or old payment - computes `ws-inv-amt` at L671 and then adds it
        # NOWHERE, and that `ws-inv-amt` is never re-zeroed, so it keeps its value
        # into the next header. Only these two types read it, so nothing observes
        # the staleness; recorded because it is the kind of thing a later reader
        # would want to "tidy".
        totals.sl_credit_notes_this_month = Decimal(
            arithmetic.add_to(
                ctx.ws_inv_amt,
                receiver_value=totals.sl_credit_notes_this_month,
                receiving=_D_SL_CREDIT_NOTES_THIS_MONTH,
            )
        )

    # ---- THE STAMPS AND THE WRITE  [sales/sl055.cbl:L679-L689] ----

    # 679  move     "Z"  to ih-status.
    #
    # "Z" is `applied` [copybooks/slwsinv2.cob:L74] - the very condition L632 tests
    # to skip a header. Stamped on the RECORD AREA only; it reaches `SAINVOICE-REC`
    # when the caller performs `Invoice-Rewrite` at [sales/sl055.cbl:L441] or
    # [sales/sl055.cbl:L469].
    sub.ih_status = _IH_STATUS_APPLIED
    # 680  move     "A"  to ih-status-A.
    #
    # A SEPARATE FIELD from `ih-status` [copybooks/slwsinv2.cob:L78], "Invoice
    # Applied to a/c".
    sub.ih_status_a = _IH_STATUS_A_APPLIED
    # 681  write    oi-header.    *> OTM2
    #
    # Appended to the work sequence in insertion order. Reaches no schema table, so
    # it appears in no table dump - it is `sl060`'s input.
    ctx.open_item_file_2.write(ctx.oi_header, ctx.file_access)
    # 682  if       fs-reply not = zero
    if arithmetic.compare(ctx.fs_reply, FsReply.SUCCESS) != 0:
        # 683  perform  a01-Eval-Status
        _a01_eval_status(ctx)
        # 684  display  SL121         at line ws-23-lines col 1
        # 685  display  fs-reply      at line ws-23-lines col 41
        # 686  display  Exception-Msg at line ws-23-lines col 44
        #
        # Three displays, one log record: the message, the status and its text.
        # `Exception-Msg` is `pic x(25)` [sales/sl055.cbl:L153] and is filled
        # ONLY by `a01-Eval-Status` above, from the static status table
        # `copybooks/FileStat-Msgs.cpy` keyed on `fs-reply`. It is therefore a
        # fixed status NAME, never driver text and never a business value, so it
        # is inside the safe-event allowlist alongside `FS-Reply` itself.
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

    # FALL-THROUGH into `dd999-Main-Ex.` [sales/sl055.cbl:L691] - the section's
    # statements end at L689 with no transfer.
    _dd999_main_ex()


#  dd999-Main-Ex.  [sales/sl055.cbl:L691]


def _dd999_main_ex() -> None:
    """`dd999-Main-Ex.` - `exit section.` [sales/sl055.cbl:L692].

    The class-3 target of [sales/sl055.cbl:L633], and also reached by fall-through
    from the end of the section's own statements. Note the label's name:
    `dd999-Main-Ex`, not `-Main-Exit` as the sibling sections spell it - one more
    small naming inconsistency in a program full of them.
    """
    # 692  exit     section.
    return None



#  zz070-Convert-Date        section.  [sales/sl055.cbl:L694]


def _zz070_convert_date(ctx: _Sl055Context) -> None:
    """`zz070-Convert-Date section.` - render the run date in the configured form.

    THE SECTION'S OWN HEADER COMMENT  [sales/sl055.cbl:L697-L700]

        697  *>  Converts date in to-day to UK/USA/Intl date format
        700  *> Input:   to-day
        700  *> output:  ws-date as uk/US/Inlt date format

    THE BODY IS DELEGATED, NOT RE-IMPLEMENTED. This section is byte-identical
    across the ten in-scope programs that carry it, and section 0.6.3 names the
    shared date sections as the one place where consolidation is unambiguously
    safe "because the bodies are textually equivalent". `acas_posting.dates`
    holds the single copy; this function is the per-program CALL SITE that rule
    R-5's paragraph-to-function mapping requires, and it carries the two things
    that are genuinely local: which system record supplies `Date-Form`, and where
    the effective form is written back.

    (!) THE SECTION MUTATES A `SYSTEM-REC` COLUMN  [sales/sl055.cbl:L704-L705]

        704      if       Date-Form = zero
        705               move 1 to Date-Form.

    `Date-Form` [copybooks/wssystem.cob:L128] is a persisted column, not working
    storage, so defaulting it to 1 (UK) is a DIFF-VISIBLE side effect of merely
    formatting a date - and the caller's `overrewrite.` in `sales/sales.cbl` is
    what commits it. `dates.zz070_convert_date` returns the effective form
    precisely so that the write-back stays visible at the call site instead of
    being buried; it is performed here.

    `sl055` CARRIES ONLY THIS ONE DATE SECTION. There is no `zz050-Validate-Date`,
    no `zz060-Convert-Date` and no `maps03`/`maps04` wrapper anywhere in the
    program - it never validates or converts a date to a day number, it only
    reformats the text it was handed. Consequently anomaly A-22, the wrapper
    section whose name and exit label disagree, DOES NOT OCCUR HERE.

    The two `GO TO`s in the section, [sales/sl055.cbl:L707] and
    [sales/sl055.cbl:L712], are both class 3 - transfers to `zz070-Exit.` - and
    both live inside the delegated body. They are annotated in the traceability
    footer against the shared implementation rather than duplicated here, because
    duplicating the body to re-annotate them is exactly what consolidation avoids.

    Args:
        ctx: The program's state. `ctx.date_formats.ws_date` receives the rendered
            date and `System-Record.Date-Form` may be defaulted from zero to 1.
    """
    # 702  move     to-day to ws-date.
    # 704  if       Date-Form = zero
    # 705           move 1 to Date-Form.
    # 706  if       Date-UK
    # 707           go to zz070-Exit.
    #
    # GO TO class 3 - a transfer to the section's own exit paragraph, taken inside
    # the delegated body in `acas_posting.dates.zz070_convert_date`, where it is a
    # `return`. Annotated here because this is the call site rule R-5 maps.
    #
    # 708  if       Date-USA                *> swap month and days
    # 709           move ws-days to ws-swap
    # 710           move ws-month to ws-days
    # 711           move ws-swap to ws-month
    # 712           go to zz070-Exit.
    #
    # GO TO class 3 - likewise, and likewise a `return` in the delegated body.
    #
    # 716  move     "ccyy/mm/dd" to ws-date.
    # 717  move     to-day (7:4) to ws-Intl-Year.
    # 718  move     to-day (4:2) to ws-Intl-Month.
    # 719  move     to-day (1:2) to ws-Intl-Days.
    #
    # The three reference modifications are ONE-BASED and are performed by
    # `acas_posting.cobol.move.ref_mod_into` inside the shared body - never by
    # Python slicing, whose bounds differ by one.
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


#  zz070-Exit.  [sales/sl055.cbl:L721]


def _zz070_exit() -> None:
    """`zz070-Exit.` - `exit section.` [sales/sl055.cbl:L722].

    The class-3 target of [sales/sl055.cbl:L707] and [sales/sl055.cbl:L712], and
    also reached by fall-through from L719. `EXIT SECTION` returns to the single
    `perform zz070-Convert-Date` at [sales/sl055.cbl:L353].
    """
    # 722  exit     section.
    return None


#  a01-Eval-Status section.  [sales/sl055.cbl:L724]

#: `copy "FileStat-Msgs.cpy" replacing STATUS by fs-reply msg by exception-msg.`
#: [sales/sl055.cbl:L726-L727], expanded.
#:
#: The copybook is an `EVALUATE` over the two-digit file status with one
#: twenty-five-character message per `WHEN`, and a `WHEN OTHER` catch-all. It is a
#: COPY, so in the compiled program it is part of THIS program's own code - which
#: is why the table is module-private here rather than imported: `dal.status`
#: publishes the `FsReply` vocabulary and the SQLSTATE mappings but no message
#: text, and inventing a shared table would put a message catalogue in a layer
#: that has none.
#:
#: Every literal is transcribed byte for byte from the copybook INCLUDING ITS
#: TRAILING SPACES, because `exception-msg pic x(25)` [sales/sl055.cbl:L153] is
#: exactly twenty-five characters wide and the copybook's literals are already
#: padded to that width. Trimming them would change what a log line renders.
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

#: `WHEN OTHER MOVE "Unknown File Status      " TO MSG` - the copybook's
#: catch-all, which is what an undocumented status renders as.
_FILE_STATUS_UNKNOWN: Final[str] = "Unknown File Status      "


def _a01_eval_status(ctx: _Sl055Context) -> None:
    """`a01-Eval-Status section.` - turn `fs-reply` into readable text.

    THE SECTION, VERBATIM  [sales/sl055.cbl:L724-L729]

        724  a01-Eval-Status section.
        725      move     spaces to exception-msg.
        726  copy "FileStat-Msgs.cpy"  replacing STATUS by fs-reply
        727                                      msg    by exception-msg.
        729  a01-exit.    exit section.

    DIAGNOSTIC ONLY. It writes nothing but `exception-msg`, a working-storage
    field, and it is performed from exactly one place - the failed OTM2 write at
    [sales/sl055.cbl:L683]. It must not alter control flow and it must never
    appear in a table dump, which section 0.3.4 requires of every display-only
    construct. The function is kept under rule R-5 because the section exists and
    the traceability document maps it; its output becomes log text.

    NOTE WHAT THE `MOVE SPACES` IS FOR. The copybook's `WHEN OTHER` arm always
    fires for an unrecognised status, so the field is never actually left blank -
    L725 is belt and braces, exactly like the doubled loop condition in
    `da010-Read-Loop`. Both statements are reproduced.

    Args:
        ctx: The program's state. `exception-msg` is overwritten from `fs-reply`.
    """
    # 725  move     spaces to exception-msg.
    ctx.exception_msg = str(move.move_figurative(move.SPACE, _D_EXCEPTION_MSG))
    # 726  copy "FileStat-Msgs.cpy"  replacing STATUS by fs-reply
    # 727                                      msg    by exception-msg.
    #
    # The expanded `EVALUATE`. `Mapping.get` with the `WHEN OTHER` literal as the
    # default is the same decision tree, and the store goes through `cobol.move` so
    # that the receiver's `pic x(25)` governs padding and truncation - not the
    # length of whichever literal was selected.
    ctx.exception_msg = move.move_alphanumeric(
        _FILE_STATUS_MESSAGES.get(ctx.fs_reply, _FILE_STATUS_UNKNOWN),
        _D_EXCEPTION_MSG,
    )
    _a01_exit()


#  a01-exit.  [sales/sl055.cbl:L729]


def _a01_exit() -> None:
    """`a01-exit.` - `exit section.` [sales/sl055.cbl:L729].

    Declared on the SAME SOURCE LINE as its `exit section.`, which is why section
    0.4.2's inventory misses it - it is `a01-exit.    exit section.`, one line
    rather than two. Reached only by fall-through; nothing transfers to it. It
    retains a named function under rule R-5 all the same.
    """
    # 729  a01-exit.    exit section.
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

    THE LINKAGE, VERBATIM  [sales/sl055.cbl:L271-L275]

         procedure division using ws-calling-data
                                  system-record
                                  system-record-4
                                  to-day
                                  file-defs.

    FIVE PARAMETERS, IN THAT ORDER - the Sales/Purchase shape, shared by all six
    SL/PL modules and distinct from both the General Ledger's four
    (`ws-calling-data`, `system-record`, `to-day`, `file-defs`) and the IRS's
    three (`IRS-System-Params`, `WS-System-Record`, `File-Defs`, with no run date
    at all). The third parameter is spelled `system-record-4` here and
    `WS-System-Record-4` at the call site [sales/sales.cbl:L704]; it is
    `SYSTOT-REC`, and it is the target of this program's two period-total writes.

    Note also the declaration ORDER in the source's LINKAGE SECTION:
    `01 to-day pic x(10).` stands at [sales/sl055.cbl:L264], BEFORE the four
    `COPY` statements that bring in the other records at L265-L269, even though
    `to-day` is the fourth parameter. Declaration order and parameter order are
    independent in COBOL; the parameter order above is the one that matters.

    ========================================================================
    THE CONTROL SHAPE, AND WHY THE OUTER LOOP LIVES HERE
    ========================================================================

    `da000-mainline` falls through into `da010-Read-Loop`, whose inline
    `perform until FS-Reply = 10` is the ITEM-level loop over invoice LINES. When
    that loop's `exit perform` [sales/sl055.cbl:L371] fires, control falls through
    into `da020-Header-Analysis`, which processes the HEADER and then transfers
    back to `da010-Read-Loop` at [sales/sl055.cbl:L470] - restarting the inline
    perform. That back-edge, together with the ones at L428, L442 and L479, is the
    OUTER loop, and it spans three paragraphs, so it cannot live inside any one of
    them. It lives here.

        _da000_mainline           L305   opens, then FALLS THROUGH
              |
              v
        _da010_read_loop          L364   `while` = the inline perform, ITEMS
              |  L371 exit perform -> FALL-THROUGH
              |  L368 GO TO class 2 -----------------------.
              v                                            |
        _da020_header_analysis    L426   HEADERS            |
              |  L428 / L442 / L470  GO TO class 1 --> back to _da010_read_loop
              |  L431 / L436         GO TO class 4          |
              v                                            |
        _da030_skip_invoice       L472                      |
              |  L479 GO TO class 1 --> back to _da010_read_loop
              |  L478 GO TO class 2 ----------------------->|
                                                            v
                                              _da040_close_files   L481
                                                  |  L509 / L518 goback
                                                  v  fall-through
                                              _da999_menu_exit     L520

    THE DISPATCH LOOP BELOW IS THE `GO TO` MECHANISM MADE EXPLICIT, and section
    0.7.4 conflict C-4 is what licenses it: "Keeping the function boundary fixed at
    the paragraph boundary and varying only the TRANSFER MECHANISM satisfies both,
    and has the side benefit that the equivalence argument is reviewable one site
    at a time." Each paragraph function returns the label control would flow to,
    and this loop performs the `continue` or `break` its class calls for. No
    paragraph was merged, none was split, and none of the four transfer classes was
    collapsed into another.

    WHY A DISPATCH LOOP RATHER THAN NESTED `while`s. The three-paragraph cycle has
    TWO entry paths back to `da010-Read-Loop` (from `da020` and from `da030`) and
    TWO exits to `da040-Close-Files` (from inside the inline perform and from
    `da030`), so it is not reducible to a single nested loop without duplicating a
    paragraph body. Threading the label is the transformation that preserves both
    the paragraph boundaries rule R-5 requires and the exact transfer set the
    source has.

    ========================================================================
    WHAT THIS PROGRAM WRITES
    ========================================================================

    Three schema tables and one work sequence:

      * `VALUEANAL-REC`  - `Value-Write` / `Value-Rewrite`, per analysis group in
        `da010-Read-Loop` and per special total in `dc000-Store-Specials`
      * `ANALYSIS-REC`   - `Analysis-Write`, only when `db010-Create-Anal` has to
        invent an emergency description
      * `SAINVOICE-REC`  - `Invoice-Rewrite`, stamping `il-update`, `ih-update`,
        `ih-status` and `ih-status-A`
      * `SYSTOT-REC`     - the two period-total columns, through `system_record_4`
      * OTM2             - the work sequence `sl060` consumes; NO table, so it
        appears in no dump

    Args:
        ws_calling_data: `01 WS-Calling-Data.` [copybooks/wscall.cob:L6] -
            `WS-Called`, `WS-Caller`, `WS-Del-Link`, `WS-Term-Code`,
            `WS-Process-Func`, `WS-Sub-Function` and `WS-CD-Args`. `WS-Caller` is
            read at [sales/sl055.cbl:L505] and [sales/sl055.cbl:L514] to decide
            whether an acknowledgement prompt is due, and `WS-Term-Code` is
            written only on the missing-analysis-file path
            [sales/sl055.cbl:L344].
        system_record: `01 System-Record.` [copybooks/wssystem.cob] - read for
            `File-System-Used` (the `FS-Cobol-Files-Used` gate) and MUTATED at
            `Date-Form` when `zz070-Convert-Date` defaults it.
        system_record_4: `01 System-Record-4.` [copybooks/wssys4.cob] -
            `SYSTOT-REC`. `sl-invoices-this-month` and
            `sl-credit-notes-this-month` are accumulated in `dd000-Extract`.
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
    # THE CONTEXT IS THIS PROGRAM'S WORKING-STORAGE, NOT AN ADDED ABSTRACTION.
    # Every field on it is a `01`/`03` item declared between
    # [sales/sl055.cbl:L145] and [sales/sl055.cbl:L259]; the five linkage records
    # are held by reference, exactly as COBOL passes them BY REFERENCE, so the
    # mutations this program makes to `System-Record.Date-Form` and to
    # `System-Record-4`'s two period totals are visible to the caller.
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

    # `da000-mainline section.` [sales/sl055.cbl:L305] - the entry section. It ends
    # with the OTM2 open at L362 and no transfer statement, so control falls
    # through into the paragraph below it.
    _da000_mainline(ctx)

    # FALL-THROUGH 1 OF 2  [sales/sl055.cbl:L362 -> sales/sl055.cbl:L364]
    label = _Label.DA010_READ_LOOP

    while True:
        match label:
            case _Label.DA010_READ_LOOP:
                # `da010-Read-Loop.` [sales/sl055.cbl:L364] - the inline
                # `perform until FS-Reply = 10` over invoice LINES. Returns
                # `DA020_HEADER_ANALYSIS` for the fall-through at L371, or
                # `DA040_CLOSE_FILES` for the class-2 `GO TO` at L368.
                label = _da010_read_loop(ctx)
                continue
            case _Label.DA020_HEADER_ANALYSIS:
                # `da020-Header-Analysis.` [sales/sl055.cbl:L426] - HEADERS only.
                # Returns `DA010_READ_LOOP` for the class-1 back-edges at L428,
                # L442 and L470, or `DA030_SKIP_INVOICE` for the class-4 transfers
                # at L431 and L436.
                label = _da020_header_analysis(ctx)
                continue
            case _Label.DA030_SKIP_INVOICE:
                # GO TO class 4 - SITES 1 AND 2 OF 4 land here.
                #
                # THE PER-SITE EQUIVALENCE PROOF, restated at the dispatch point.
                # `_da030_skip_invoice`'s docstring proves that L431 and L436 each
                # have NO trailing work of their own: L431 is the entire body of
                # its `if`, and L436's body is `move 1 to ws-p-flag` followed
                # immediately by the transfer, which `_da020_header_analysis`
                # performs BEFORE returning the label. So in both cases
                # "transfer to L472" is exactly "run L473-L476, then transfer where
                # L477-L479 decide" - a named call followed by an explicit transfer
                # on the returned label, which is what this arm performs. The two
                # sites reach the same paragraph but are proven separately, because
                # the proof is about each site's trailing statements, not about the
                # target.
                label = _da030_skip_invoice(ctx)
                continue
            case _:
                # GO TO class 2 - `DA040_CLOSE_FILES`, from either
                # [sales/sl055.cbl:L368] or [sales/sl055.cbl:L478]. The `break`
                # leaves the loop; the post-loop block below is the "real work"
                # section 0.6.3 insists must accompany it - four special-total
                # stores and four closes. Dropping it would silently discard the
                # whole value-analysis roll-up.
                break

    # THE POST-LOOP BLOCK. `da040-Close-Files.` [sales/sl055.cbl:L481].
    label = _da040_close_files(ctx)

    # `goback.` at [sales/sl055.cbl:L509] or [sales/sl055.cbl:L518] returns
    # WITHOUT reaching `da999-Menu-Exit.`, so the two dispositions are kept
    # distinct even though both end the program: the label records which path the
    # run took, and the traceability footer maps both.
    if label is _Label.GOBACK:
        #  THE CHANNEL IS RETURNED ON BOTH DISPOSITIONS. `sl060` reads what this
        #  program wrote whichever `goback` ended it, because in COBOL the file
        #  survives the run unit either way.
        return ctx.open_item_file_2

    # FALL-THROUGH 2 OF 2  [sales/sl055.cbl:L518 -> sales/sl055.cbl:L520]
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
