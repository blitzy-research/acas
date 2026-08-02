"""`gl051` - the General Ledger batch control-total gate  [general/gl051.cbl].

A **PARTIAL** migration, and one of only two in the whole engagement. Agent
Action Plan section 0.8.7, verbatim:

    "Two of the twelve in-scope programs are migrated only in part, and the
    boundaries are narrow: one contributes only its control-total gate
    [general/gl051.cbl:L1096-L1133] and the other only its ledger-posting
    section [irs/irs030.cbl:L1569-L1733]. Both files are otherwise dominated by
    interactive code that is out of scope, so an agent working from the file
    rather than from the stated boundary would migrate several hundred lines
    that must not be migrated."

`general/gl051.cbl` is 1,282 lines of interactive batch proof-and-amendment
screen program. Roughly 170 of them are here. The BOUNDARY table in the
traceability footer names every section on both sides of the line, and it is the
single most important part of that footer: it is what shows the boundary was
respected rather than merely intended.

THE BOUNDARY
============
IN SCOPE - `batch-print section.` in its ENTIRETY  [general/gl051.cbl:L999-L1166]

    batch-print       section.  L999   entry: headings, then WS-Ledger
    loop.                       L1005  the posting read loop AND the accumulation
    get-a-batch.                L1067  the indexed batch-header read
    headings.                   L1074  print headings; performs `zz060`
    end-batch.                  L1096  THE CONTROL-TOTAL GATE
    get-description.            L1136  the DR/CR existence check that rejects
    main-exit.   exit section.  L1166

The plan cites `[general/gl051.cbl:L1096-L1133]`, which is the `end-batch`
paragraph ALONE. Measured, the section runs L999 to L1166 and `end-batch` is the
fourth of its six paragraphs; section 0.2.1.1's phrasing - "only `batch-print`
section 999 and its `end-batch` paragraph" - is the reading reproduced here, so
the section is migrated whole. Two things the cited range cannot show are the
reason it has to be:

  * `get-description.` [general/gl051.cbl:L1136] IS THE ENTIRE REJECTION
    MECHANISM. It is the only in-scope writer of `trutht`, and `end-batch` reads
    `trutht` at [general/gl051.cbl:L1101] before it compares anything. Omit the
    paragraph and the gate can only ever accept.
  * `add post-amount to actual-gross` [general/gl051.cbl:L1063] and
    `add vat-amount to actual-vat` [general/gl051.cbl:L1064] ARE THE ENTIRE
    ACCUMULATION. Omit them and the gate compares the operator's control totals
    against zero and rejects every batch that has any value in it.

ALSO IN SCOPE, because plan section 0.4.1.2 names them explicitly - arithmetic
fragments that produce the gate's inputs, drawn from otherwise out-of-scope
interactive paragraphs. Each carries a `# BOUNDARY` comment at its definition:

    net.                        L788   the first `ROUNDED` compute  L791
    gross.                      L793   the second `ROUNDED` compute L796,
                                       plus its un-`ROUNDED` companion L797
    the five account-scaling statements  L604, L607, L654, L657, L803

ALSO IN SCOPE as thin delegations, because `batch-print` performs `zz060` twice
(at [general/gl051.cbl:L1020] and [general/gl051.cbl:L1082]) and `zz060` reaches
the date-module wrapper:

    zz050-Validate-Date  section.  L1169
    zz060-Convert-Date   section.  L1208
    zz070-Convert-Date   section.  L1243
    maps03               section.  L1273   ANOMALY A-22, OCCURRENCE 2

OUT OF SCOPE - not one line of any of these is translated:

    gl051-Main       section.  L359
    proof-all        section.  L474
    gl050c           section.  L496   incl. accept-amount. L650, h-o-data. L782,
                                      get-description. L799, main-exit. L816
    batch-amendment  section.  L825   incl. batch-outline. L838, b-o-loop2. L845,
                                      b-o-data. L855, cycle-in. L868,
                                      items-in. L889, gross-in. L901,
                                      vat-in. L912, desc-in. L926,
                                      detail-query. L939
    gl050d           section.  L961   incl. disp-head-skip. L978,
                                      main-exit. L985, end-routine. L993

plus every screen section, every `accept` loop and every amendment dialog.

THE MODULE MUTATES NO TABLE
===========================
`batch-print` performs exactly THREE file-handler verbs, and all three are
READS: `GL-Posting-Read-Next` [general/gl051.cbl:L1008],
`GL-Batch-Read-Indexed` [general/gl051.cbl:L1070] and
`GL-Nominal-Read-Indexed` [general/gl051.cbl:L1142] and
[general/gl051.cbl:L1156]. There is no write, no rewrite, no delete, no open and
no close anywhere inside the boundary. The opens are `gl050d`'s
[general/gl051.cbl:L980-L981] and so are the closes
[general/gl051.cbl:L989-L990].

So the whole deliverable of this module is a VALUE: `Batch-Status` on the
in-memory batch record, plus the `trutht` flag that decides it. The two
`GL-Batch-Rewrite` calls that persist `Batch-Status` are at
[general/gl051.cbl:L415] and [general/gl051.cbl:L491], both outside the
boundary, so persistence belongs to the caller - question Q-1.

THE GATE, AND THE ONE ORDERING FACT THAT MATTERS MOST
=====================================================
`end-batch.` [general/gl051.cbl:L1096], the part the plan cites:

    1099      if       z = 99
    1100               go to  main-exit.
    1101      if       not truet
    1102               move  0  to  batch-status
    1103               go to  main-exit.
    1105      subtract input-vat  from  input-gross  giving  l9-amount.
    1106      move     input-vat    to  l9-vat.
    1107      move     actual-gross to  l10-amount.
    1108      move     actual-vat   to  l10-vat.
    1109      add      actual-vat   to  actual-gross.
    1111      if       line-cnt > Page-Lines - 12
    1112               perform headings.
    1113      write    print-record  from  line-8 after 3.
    1114      write    print-record  from  line-9 after 2.
    1115      write    print-record  from  line-10 after 2.
    1117      if       input-gross = actual-gross
    1118        and    input-vat   = actual-vat
    1119               move  1  to  batch-status
    1120      else
    1121               move  0  to  batch-status.

[general/gl051.cbl:L1109] adds the accumulated VAT INTO the accumulated gross,
and it does so BEFORE the equality test at [general/gl051.cbl:L1117-L1121]. Plan
section 0.6.4, verbatim: "the entered figure is VAT-inclusive. Reversing these
two steps would reject every batch that carries VAT." That is the single most
important ordering fact in this module, it is an in-place mutation rather than a
fresh total, and `_end_batch` performs it exactly where the COBOL does.

The gate itself is a TWO-condition AND: both `input-gross = actual-gross` and
`input-vat = actual-vat` must hold. All four are `pic 9(9)v99 comp-3`
[copybooks/wsbatch.cob:L41-L44], so the comparison is algebraic and goes through
`acas_posting.cobol.arithmetic.compare`, never a Python `==` on raw attributes
and never a text comparison.

THIS MODULE IS LINK ZERO OF THE FOUR-LINK ABORT CHAIN
=====================================================
`Batch-Status` is `03 Batch-Status pic 9.` with `88 Status-Open value 0.` and
`88 Status-Closed value 1.` [copybooks/wsbatch.cob:L25-L27]. So
`move 1 to batch-status` means `Status-Closed` and `move 0` means `Status-Open` -
and leaving a batch OPEN is precisely what the next phase looks for. Measured
end to end:

    link 0  this module rejects        ->  Batch-Status = 0 = `Status-Open`
    link 1  gl071a. sees it                `if status-open move 1 to a`
                                           [general/gl070.cbl:L314-L315]
    link 2  gl070 raises the code          `move 5 to ws-term-code`
                                           [general/gl070.cbl:L289], reached by
                                           `if a = 1` [general/gl070.cbl:L287]
    link 3  the menu returns               `if ws-term-code = 5 go to
                                           display-menu` in `load08.`
                                           [general/general.cbl:L810-L811],
                                           the paragraph beginning at
                                           [general/general.cbl:L805]

and the consequence is that `gl071` and `gl072` NEVER RUN. Plan section 0.6.5
classes that as a "run-aborting rejection", whose database effect is THE ABSENCE
of everything the later phases would have written. Plan section 0.6.4 adds that
the control-total mismatch scenario is General-Ledger-specific, because "Sales
and Purchase batches balance by construction".

THE REJECTION MECHANISM
=======================
`get-description.` [general/gl051.cbl:L1136] does two independent indexed
nominal reads - the debit account [general/gl051.cbl:L1139-L1142] then the credit
account [general/gl051.cbl:L1153-L1156] - each preceded by `move zero to
we-error` and each testing `fs-reply = 21`. On failure it writes a print marker
AND clears `trutht` [general/gl051.cbl:L1150] and
[general/gl051.cbl:L1164]. Those two statements are the ONLY in-scope writers of
`trutht`, and they only ever clear it. Combined with `move 1 to trutht`
[general/gl051.cbl:L967], set by `gl050d` outside the boundary, the semantics
are: the batch is valid UNLESS some posting references a nominal account that
does not exist. `end-batch` [general/gl051.cbl:L1101] then rejects it before
comparing anything, so a missing account rejects the batch whether or not its
totals agree.

`we-error` is used here as a LOCAL 0-or-1 FLAG - literal `1` at
[general/gl051.cbl:L1144] and [general/gl051.cbl:L1158], zero at
[general/gl051.cbl:L1138] and [general/gl051.cbl:L1152]. It is the same
`We-Error pic 999` field the file handlers use [copybooks/wsfnctn.cob:L23-L38],
but NOT the handler's code vocabulary: a reader arriving from `gl072` will
expect the 999 sentinel and there is none here. `_batch_print_get_description`
says so at the site.

ROUNDING
========
`gl051` owns TWO of the FIVE `ROUNDED` sites in the entire migration -
[general/gl051.cbl:L791] and [general/gl051.cbl:L796]. The other three are
[general/gl080.cbl:L328], [irs/irs030.cbl:L1551] and [irs/irs030.cbl:L1562].
EVERY OTHER STORE IN THIS PROGRAM TRUNCATES, so truncation is the default at
every call below and the `rounded` flag is set true at exactly two call sites.
The adjacency at [general/gl051.cbl:L796-L797] is why rounding has to be a
per-call argument and can never be a module-wide mode: a half-up store is
followed IMMEDIATELY by a truncating one.

ANOMALIES REPRODUCED  (rule R-4)
================================
Plan section 0.8.2, verbatim: "There is no test suite: compiled COBOL execution
is the behavioral specification, defects included. A defect reproduced is
correct; a defect fixed is a failure." Section 0.7.4 C-4 prescribes a comment at
each reproduction site citing the COBOL locator, and that is how engineering
quality is expressed here rather than through correction.

  A-22, OCCURRENCE 2  `maps03 section.` [general/gl051.cbl:L1273] carries the
      exit label `maps04-exit.` [general/gl051.cbl:L1278] - the section named
      after the interface copybook, its exit named after the called program. The
      plan records this defect for `gl070` only ([general/gl070.cbl:L603] and
      [general/gl070.cbl:L608]); `gl051` has it identically and this is its
      second occurrence. Reproduced by `_maps03`.
  A-21  Field-name collisions across three posting copybooks force qualified
      references. Three in-scope sites, in BOTH spellings: `post-code in
      WS-Posting-Record` [general/gl051.cbl:L1033] uses `in`, while `vat-ac of
      WS-Posting-Record` [general/gl051.cbl:L1044] and
      [general/gl051.cbl:L1047] use `of`. In Python the collision disappears, so
      the reproduction is the comment plus record-qualified attribute access.
  A-15  (context, not a reproduction site) The batch record's declared length
      contradicts the sum of its fields - [copybooks/wsbatch.cob:L7-L9] says
      "96 bytes ... 98 bytes ... (no, dont understand as I count 96) but
      function length (Batch-record) says 98?". `gl051` reads and compares those
      very fields, so the contradiction bears on this module directly. It is an
      OPEN ORACLE QUESTION - question Q-9 - and this module takes the layout as
      `acas_posting/records/gl_batch.py` publishes it.

FINDINGS NOT IN THE TWENTY-TWO-ENTRY REGISTER, recorded for the log
==================================================================
  F-1 `03 trutht pic 9.` [general/gl051.cbl:L175] is a transposition typo of
      "truth" or "true", and its condition names are spelled differently again -
      `88 falset value zero.` [general/gl051.cbl:L176] and `88 truet value 1.`
      [general/gl051.cbl:L177]. `falset` is DECLARED BUT NEVER TESTED anywhere
      in the 1,282 lines; only `truet` is, at [general/gl051.cbl:L507] (out of
      scope) and [general/gl051.cbl:L1101] (in scope). Same character of finding
      as the register's A-20.
  F-2 The plan's own section 0.4.1.2 says `gl051` "Accumulates actual DR/CR/VAT".
      That is factually wrong: there is no `actual-DR` and no `actual-CR`
      anywhere in the program. `03 Amounts comp-3.` has exactly four money
      fields - `Input-Gross`, `Input-Vat`, `Actual-Gross`, `Actual-Vat`
      [copybooks/wsbatch.cob:L41-L44]. What is accumulated is gross and VAT.
  F-3 The two page-break constants DIFFER: `Page-Lines - 6`
      [general/gl051.cbl:L1060] against `Page-Lines - 12`
      [general/gl051.cbl:L1111]. Deliberate, not a typo - the second is about to
      write three multi-line blocks - and both are reproduced as written.
  F-4 The unsigned accumulators receive signed addends. `Actual-Gross` and
      `Actual-Vat` are `pic 9(9)v99` UNSIGNED [copybooks/wsbatch.cob:L43-L44],
      while `Post-Amount` and `Vat-Amount` are `pic s9(8)v99` SIGNED
      [copybooks/wspost.cob:L23] and [copybooks/wspost.cob:L28]. So
      [general/gl051.cbl:L1063-L1064] can add a negative value into a field that
      cannot hold one. Question Q-3.
  F-5 The file holds TWO `get-description.` paragraphs that disagree on their
      own sentinel: the out-of-scope one moves `255` to `we-error`
      [general/gl051.cbl:L808], the in-scope one moves `1`
      [general/gl051.cbl:L1144]. Both are read back with the same
      `if we-error = zero` test, so neither value is wrong - but they were
      plainly written at different times.
  F-6 `gl051` DOES have a linker-satisfying stub block -
      `01 Dummies-4-Unused-ACAS-FH-Calls.` [general/gl051.cbl:L136-L156], with
      its own comment "Call blk at zz080-ACAS-Calls" - exactly like `gl072`
      [general/gl072.cbl:L134-L153] and `gl080`. It maps to nothing in Python
      and is recorded in the OMISSIONS list as representation-only.
  F-7 In the `z = 99` "all batches" mode, `get-a-batch`
      [general/gl051.cbl:L1018] re-reads the batch header on every batch change,
      which OVERWRITES `Actual-Gross` and `Actual-Vat` with the stored values
      mid-run, and [general/gl051.cbl:L1063-L1064] then accumulates on top of
      them. It is harmless only because [general/gl051.cbl:L1099-L1100]
      short-circuits the gate in that very mode, so the clobbered accumulators
      are never compared. In the `z not = 99` mode that DOES reach the gate,
      `get-a-batch` is never performed from the loop at all. Reproduced as
      written; see `_loop`.

QUESTIONS FOR THE COMPILED ORACLE  (rule R-6)
=============================================
Rule R-6 makes observed compiled behaviour the tie-breaker, and section 0.6.8
requires each question be recorded with its experiment. Nothing below is guessed
in code: each is marked `# AMBIGUITY Q-n` at the site it bears on.

  Q-1 Is persisting `Batch-Status` the caller's job? The two `GL-Batch-Rewrite`
      calls are at [general/gl051.cbl:L415] and [general/gl051.cbl:L491], both
      outside the boundary, and `batch-print` performs no write of any kind.
      `run` therefore SETS the field and returns. Experiment: proof one batch
      through the compiled program and observe whether `GLBATCH-REC` changes
      before the amendment screen is left.
  Q-2 The compound VAT expression's intermediate precision
      [general/gl051.cbl:L796]. Section 0.6.8 names this as "the one place a
      precision difference could change a stored penny": there is no `-std=`
      dialect flag and no `>>SET ARITHMETIC` directive anywhere in the
      repository, so the compiler's default governs. The expected value must be
      CAPTURED from the compiled program, never derived by reading. Experiment:
      drive `gross.` over a rate and amount grid and record every result.
  Q-3 What does an unsigned `pic 9(9)v99 comp-3` receiver hold after a negative
      addend at [general/gl051.cbl:L1063-L1064] or
      [general/gl051.cbl:L1109]? `acas_posting.cobol.arithmetic` models the sign
      being dropped; the compiled value must confirm it. Experiment: post a
      credit-heavy batch whose signed `Post-Amount` is negative and dump
      `GLBATCH-REC`.
  Q-4 The three promoted preconditions - `move 1 to trutht`
      [general/gl051.cbl:L967] and `move zero to actual-gross actual-vat`
      [general/gl051.cbl:L982] - plus the batch-selection value `z`. All are set
      by `gl050d` immediately before `perform batch-print`
      [general/gl051.cbl:L983], so they are inputs to this boundary rather than
      behaviour of it. Defaulted below to the COBOL's own values. Experiment:
      confirm no other path reaches `batch-print` with different ones.
  Q-5 `z` has no `VALUE` clause [general/gl051.cbl:L172] and is set only in
      out-of-scope interactive code, yet it is tested in scope four times -
      [general/gl051.cbl:L1015], [general/gl051.cbl:L1026],
      [general/gl051.cbl:L1088] and [general/gl051.cbl:L1099]. The default here
      is zero, the "single selected batch" mode, because that is the only mode
      that reaches the gate. Experiment: observe the value on entry for each
      menu path.
  Q-6 The file-handler facade's Python call shape. Plan section 0.4.3 writes it
      as `facade.gl_batch_read_next(ctx)`, but no `ctx` type is defined
      anywhere, whereas the frozen copybook forwards five arguments -
      `call "acas007" using System-Record WS-Batch-Record File-Access File-Defs
      ACAS-DAL-Common-Data` [copybooks/Proc-ACAS-FH-Calls.cob:L51-L57] - and
      every already-written handler in this tree reproduces exactly that
      five-argument order. This module binds to the frozen copybook and the real
      code rather than to the prose, through one private adapter per verb, so
      there is a single place to reconcile if the facade lands with a context
      object instead.
  Q-7 `Date-Form` is MUTATED when it is zero - `if Date-Form = zero move 1 to
      Date-Form` at [general/gl051.cbl:L1183-L1184], and again inside `zz060`
      [general/gl051.cbl:L1223-L1224] and `zz070`
      [general/gl051.cbl:L1253-L1254]. It is a `SYSTEM-REC` column, so the
      mutation is visible in a table dump. `_headings` performs `zz060` and
      writes the returned value back for that reason. Experiment: dump
      `SYSTEM-REC` before and after a proof run started with `Date-Form` zero.
  Q-8 `line-cnt` [general/gl051.cbl:L166] counts print lines and is therefore
      presentation - but it is TESTED at [general/gl051.cbl:L1060] and
      [general/gl051.cbl:L1111], and a true test performs `headings`, which
      performs `zz060`, which can mutate `Date-Form`. So the counter arithmetic
      is reproduced even though the printing is not, because dropping it would
      change how many times a diff-visible column is written. Experiment: as
      Q-7, with a page-length small enough to force a break.
  Q-9 A-15's record-length contradiction [copybooks/wsbatch.cob:L7-L9]. Section
      0.6.8, verbatim: "Whether the declared length or the field sum governs the
      record actually read affects field alignment for the trailing fields, and
      only execution shows which." This module reads `Input-Gross`, `Input-Vat`,
      `Actual-Gross` and `Actual-Vat`, which sit mid-record, and takes the
      layout as `acas_posting/records/gl_batch.py` publishes it.

WHAT THIS MODULE DELIBERATELY DOES NOT DO
=========================================
Rule R-1: it never invokes the compiled program. `perform maps03`
[general/gl051.cbl:L1276] becomes a call into `acas_posting.dates`, never a
`call "maps04"`. Rule R-2: no binary floating point reaches an accounting value;
there is not one numeric primitive in this file, because section 0.3.1 puts them
all in `cobol/` - "`cobol/` contains no business logic and `programs/` contains
no numeric primitives." Rule R-3: not one conditional here is absent from the
COBOL, and there is no concurrency of any kind - section 0.8.4, verbatim: "Any
performance work is therefore out of scope by construction, not merely
unrequested." Two indexed nominal reads per posting look like an obvious
candidate for caching, and nothing is cached. Rule R-6: there is no ambient
clock; the date arrives through `to_day` and through `system_record`, and
`acas_posting/clock.py` is not imported.

NOTE ON THE RULES DOCUMENT: this project has NO user rules document -
`review_rules` reports that none was provided. The six binding rules R-1 to R-6
are the Agent Action Plan's own, section 0.7.2, and are cited above by name and
number. None has been invented, and where the plan is silent this module holds
to ordinary enterprise practice.
"""

from __future__ import annotations

import decimal
import logging
from dataclasses import dataclass, field
from typing import Final

# copy "Proc-ACAS-FH-Calls.cob".   [general/gl051.cbl:L1281]
# The 21-entity, 12-verb file-handler facade. Because `gl051` copies THIS
# copybook rather than the IRS one, it uses the ENTITY-named vocabulary -
# `GL-Posting-Read-Next` and its siblings - and it TESTS THE REPLY INLINE: this
# copybook has no per-handler error-check paragraph, unlike
# [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob]. The handler-named aliases are
# therefore never called from here. See question Q-6 for the call shape.
from acas_posting.dal import facade

# copy "wsfnctn.cob".   [general/gl051.cbl:L129] - the operation vocabulary half.
# The single COBOL copybook mixes record layout with operation vocabulary, and
# the Python layering separates them, so one `COPY` becomes two imports.
from acas_posting.dal.status import FsReply

# The date sections. `zz050`, `zz060`, `zz070` and the date-module wrapper are
# repeated near-identically in nine of the in-scope programs, and `dates.py` is
# where they consolidate - the one place consolidation is unambiguously safe
# because the bodies are textually equivalent. TWO facts decide which entry
# points this module calls, and both are `gl051`-specific:
#   * `zz050_validate_date_gl051` is `gl051`'s OWN variant. Its three `inspect
#     ... replacing all` statements [general/gl051.cbl:L1178-L1180] are absent
#     from `sl060`, `sl100`, `pl060` and `pl100`, which is why two variants are
#     published rather than one.
#   * `maps03` and `maps04` are the SAME wrapper under both names. `gl051` and
#     `gl070` perform one named `maps03` [general/gl051.cbl:L1273]; the Sales
#     and Purchase carriers perform one named `maps04`. This module passes
#     `maps03`.
from acas_posting.dates import (
    WsDateFormats,
    maps03 as _dates_maps03,
    zz050_validate_date_gl051,
    zz060_convert_date,
    zz070_convert_date,
)

# copy "wsfnctn.cob".   [general/gl051.cbl:L129] - the record-layout half.
# `01 File-Access.` [copybooks/wsfnctn.cob:L23-L38], carrying `We-Error pic 999`
# and `Fs-Reply pic 99`. Both are read and written inside the boundary.
# `ALL_FIELDS` is the flattened descriptor set for the whole copybook, which is
# where `We-Error`'s descriptor comes from: it is nested under `01 File-Access.`
# rather than published on the dataclass's own `FIELDS`.
from acas_posting.records.file_access import (
    ALL_FIELDS as _FILE_ACCESS_FIELDS,
    FileAccess,
)

# copy "wsnames.cob".   [general/gl051.cbl:L349]
# `01 File-Defs.` - the file-name buffers. Forwarded to every handler call
# exactly as the facade copybook forwards it; no field of it is read here.
from acas_posting.records.file_defs import FileDefs

# copy "wsbatch.cob".   [general/gl051.cbl:L131]
# The batch header. `WsBatchKey` carries `WS-Ledger` with its three condition
# names and `WS-Batch-Nos`; `BatchAmounts` carries the four money fields the
# gate compares.
from acas_posting.records.gl_batch import (
    BatchAmounts,
    BatchDates,
    GlBatchRecord,
    WsBatchKey,
)

# copy "wsledger.cob".   [general/gl051.cbl:L130]
# The nominal account. Only its KEY is written here - `WS-Ledger-Nos` and
# `Ledger-PC` - and only the reply is read back; `get-description` never looks
# at `Ledger-Name`, unlike its out-of-scope namesake at
# [general/gl051.cbl:L811].
from acas_posting.records.gl_ledger import WsLedgerKey, WsLedgerRecord

# copy "wspost.cob".   [general/gl051.cbl:L132]
# The posting being proofed. `Post-Amount` and `Vat-Amount` are `pic s9(8)v99`
# SIGNED [copybooks/wspost.cob:L23] and [copybooks/wspost.cob:L28] - finding
# F-4 and question Q-3.
from acas_posting.records.gl_posting import WsPostingRecord

# copy "wsmaps03.cob".   [general/gl051.cbl:L128]
# `01 maps03-ws.` - the two-field interface block passed to the date module:
# `u-date` text in and out, `u-bin` the binary day number.
from acas_posting.records.maps03 import Maps03Ws

# copy "wscall.cob".   [general/gl051.cbl:L347]
# `01 WS-Calling-Data.` [copybooks/wscall.cob:L6-L13] - the linkage block. The
# first parameter's declaration; no field of it is read or written inside the
# boundary, which is recorded in the OMISSIONS list.
from acas_posting.records.calling_data import WsCallingData

# copy "wssystem.cob".   [general/gl051.cbl:L348]
# `SYSTEM-REC`, the 169-column system record. Two of its columns are used here:
# `Page-Lines`, tested at [general/gl051.cbl:L1060] and
# [general/gl051.cbl:L1111], and `Date-Form`, which the date sections MUTATE
# when it is zero - question Q-7.
from acas_posting.records.system_record import SystemRecord

# copy "Test-Data-Flags.cob".   [general/gl051.cbl:L158]
# `01 ACAS-DAL-Common-Data.` - the compile-time logging switch, whose own
# comment reads "set sw-testing to zero to stop logging". Forwarded to every
# handler call as the facade copybook's fifth argument.
from acas_posting.records.test_data_flags import AcasDalCommonData

# The COBOL-language semantics. Section 0.3.1, verbatim: "`cobol/` contains no
# business logic and `programs/` contains no numeric primitives." Every store,
# every comparison and every `MOVE` below therefore delegates: there is no
# hand-written scale alignment, no hand-written truncation, no picture parsing
# and no comparator in this file.
from acas_posting.cobol import arithmetic, move
from acas_posting.cobol.condition_names import is_status_closed, values_for
from acas_posting.cobol.field import FieldDescriptor
from acas_posting.cobol.picture import descriptor_for

#: The whole public surface: this program's single entry point, mirroring its
#: `PROCEDURE DIVISION USING` list [general/gl051.cbl:L353-L356]. Agent Action
#: Plan section 0.3.3, verbatim: "Each `programs/*.py` module exposes a single
#: `run(...)` entry mirroring its COBOL `PROCEDURE DIVISION USING` list, with
#: the paragraph functions private to the module. Callers cannot reach into a
#: program's internals, exactly as a COBOL `CALL` cannot." Every other
#: module-level name below is therefore prefixed with an underscore, and a tuple
#: is used rather than a list so the surface cannot be extended at run time.
__all__: Final[tuple[str, ...]] = ("run",)

_LOG: Final[logging.Logger] = logging.getLogger(__name__)


def _from_record(
    fields: tuple[FieldDescriptor, ...], cobol_name: str
) -> FieldDescriptor:
    """Resolve one copybook field's descriptor from its record class's `FIELDS`.

    Rule R-5 requires every descriptor to carry provenance, and
    `FieldDescriptor.__post_init__` enforces it. The record modules already
    publish descriptors carrying BOTH a `dictionary_key` and a `source_locator`,
    generated from the authoritative triple - copybook picture clause, bridge
    host variable and `CREATE TABLE` column - so resolving from `FIELDS` is
    strictly better than restating the metadata here: it cannot drift from the
    generated dictionary, and section 0.3.3's "Dictionary as single source of
    truth" is honoured by derivation rather than by transcription.

    Args:
        fields: The `FIELDS` tuple published by a record dataclass.
        cobol_name: The field's name exactly as its copybook spells it.

    Returns:
        The published descriptor for that field.

    Raises:
        KeyError: If the record class publishes no such field. That can only
            mean this module named a field the frozen copybook does not declare,
            which rule R-3 forbids, so it fails loudly rather than inventing a
            descriptor.
    """
    for descriptor in fields:
        if descriptor.name == cobol_name:
            return descriptor
    raise KeyError(
        f"{cobol_name!r} is not published by this record layout. Adding a field "
        f"the frozen copybooks do not declare is forbidden by rule R-3. "
        f"Published names: {tuple(d.name for d in fields)!r}"
    )


# ---------------------------------------------------------------------------
#  Field descriptors - the copybook fields, resolved from the record layer
# ---------------------------------------------------------------------------

#: `05  WS-Ledger  pic 9.`  [copybooks/wsbatch.cob:L15]
_WS_LEDGER: Final = _from_record(WsBatchKey.FIELDS, "WS-Ledger")
#: `05  WS-Batch-Nos  pic 9(5).`  [copybooks/wsbatch.cob:L19]
_WS_BATCH_NOS: Final = _from_record(WsBatchKey.FIELDS, "WS-Batch-Nos")
#: `03  Batch-Status  pic 9.`  [copybooks/wsbatch.cob:L25]
_BATCH_STATUS: Final = _from_record(GlBatchRecord.FIELDS, "Batch-Status")

#: The four money fields of `03 Amounts comp-3.`
#: [copybooks/wsbatch.cob:L41-L44]. All are `pic 9(9)v99` and ALL FOUR ARE
#: UNSIGNED - finding F-4 and question Q-3.
_INPUT_GROSS: Final = _from_record(BatchAmounts.FIELDS, "Input-Gross")
_INPUT_VAT: Final = _from_record(BatchAmounts.FIELDS, "Input-Vat")
_ACTUAL_GROSS: Final = _from_record(BatchAmounts.FIELDS, "Actual-Gross")
_ACTUAL_VAT: Final = _from_record(BatchAmounts.FIELDS, "Actual-Vat")

#: The posting fields the boundary reads. `Post-Amount`
#: [copybooks/wspost.cob:L23] and `Vat-Amount` [copybooks/wspost.cob:L28] are
#: `pic s9(8)v99` SIGNED, which is the whole of finding F-4.
_POST_DR: Final = _from_record(WsPostingRecord.FIELDS, "Post-DR")
_POST_CR: Final = _from_record(WsPostingRecord.FIELDS, "Post-CR")
_DR_PC: Final = _from_record(WsPostingRecord.FIELDS, "DR-PC")
_CR_PC: Final = _from_record(WsPostingRecord.FIELDS, "CR-PC")
_POST_AMOUNT: Final = _from_record(WsPostingRecord.FIELDS, "Post-Amount")
_VAT_AMOUNT: Final = _from_record(WsPostingRecord.FIELDS, "Vat-Amount")
#: `03  Vat-AC  pic 9(6).` [copybooks/wspost.cob:L25] is read twice inside the
#: boundary - [general/gl051.cbl:L1044] and [general/gl051.cbl:L1047], both
#: qualified references and both anomaly A-21 sites - but neither statement needs
#: a SENDING descriptor: the first is a `DIVIDE ... GIVING` whose only descriptor
#: is its receiver, and the second is a relation condition against the figurative
#: zero. No constant is declared for it rather than declaring one that nothing
#: uses; the locator is cited at each of the two sites instead.

#: The nominal key `get-description` writes before each indexed read.
#: [copybooks/wsledger.cob:L14] and [copybooks/wsledger.cob:L20].
_WS_LEDGER_NOS: Final = _from_record(WsLedgerKey.FIELDS, "WS-Ledger-Nos")
_LEDGER_PC: Final = _from_record(WsLedgerKey.FIELDS, "Ledger-PC")

#: `03  u-bin  binary-long.`  [copybooks/wsmaps03.cob:L30] - the receiver of the
#: `MOVE` at [general/gl051.cbl:L1019] and [general/gl051.cbl:L1081]. Resolved
#: from the record layer for the same reason as every other copybook field.
_U_BIN: Final = _from_record(Maps03Ws.FIELDS, "u-bin")

#: `05  Entered  binary-long.`  [copybooks/wsbatch.cob:L36] - the sending field
#: of those two `MOVE` statements. Binary to binary, so no scale conversion, but
#: the `MOVE` still goes through `cobol/move.py` rather than a bare assignment.
_ENTERED: Final = _from_record(BatchDates.FIELDS, "Entered")

#: `03  We-Error  pic 999.`  [copybooks/wsfnctn.cob:L23]. THREE digits, because
#: the file handlers store codes up to 999 in it - and `get-description` uses it
#: as a plain 0-or-1 flag anyway. The descriptor is the handler's; the USE is
#: local. See `_batch_print_get_description`.
_WE_ERROR: Final = _from_record(_FILE_ACCESS_FIELDS, "We-Error")

#: `move  1  to  we-error.`  [general/gl051.cbl:L1144] and
#: [general/gl051.cbl:L1158]. A BARE LITERAL ONE in the source, not a member of
#: the handler's code vocabulary: it is emphatically NOT `WeError.NOT_USED`,
#: whose value is 999 and which is `gl072`'s sentinel
#: [general/gl072.cbl:L303-L304]. Named here so the call sites read as the flag
#: they are, and so nobody substitutes an enum member that would change the
#: stored value. Finding F-5 records that the out-of-scope `get-description.`
#: [general/gl051.cbl:L799] uses 255 for the identical purpose
#: [general/gl051.cbl:L808].
_WE_ERROR_LOCAL_FAILURE: Final[int] = 1


# ---------------------------------------------------------------------------
#  Field descriptors - `gl051`'s own WORKING-STORAGE
# ---------------------------------------------------------------------------
# These fields never reach a table, so the generated dictionary does not cover
# them and their `source_locator` is the only traceability they will ever have
# (rule R-5). `descriptor_for` is `cobol/picture.py`'s published entry point for
# exactly this case, so the picture grammar stays in `cobol/` - section 0.3.1.

#: `03  line-cnt  binary-char  value zero.`  [general/gl051.cbl:L166]. A binary
#: field, so Python `int`; question Q-8 records why a print-line counter is
#: reproduced at all.
_LINE_CNT: Final = descriptor_for(
    "binary-char value zero", name="line-cnt", source_locator="general/gl051.cbl:L166"
)
#: `03  page-nos  binary-char  value zero.`  [general/gl051.cbl:L167]
_PAGE_NOS: Final = descriptor_for(
    "binary-char value zero", name="page-nos", source_locator="general/gl051.cbl:L167"
)
#: `03  z  pic 99.`  [general/gl051.cbl:L172] - NO `VALUE` clause. Question Q-5.
_Z: Final = descriptor_for("pic 99", name="z", source_locator="general/gl051.cbl:L172")
#: `03  save-batch  pic 9(5)  comp  value zero.`  [general/gl051.cbl:L174] - a
#: BINARY field, and one of the three receivers of the `MOVE` at
#: [general/gl051.cbl:L1017], each of which converts independently.
_SAVE_BATCH: Final = descriptor_for(
    "pic 9(5) comp value zero",
    name="save-batch",
    source_locator="general/gl051.cbl:L174",
)
#: `03  trutht  pic 9.`  [general/gl051.cbl:L175] - the batch-valid flag, and
#: finding F-1's transposition typo.
_TRUTHT: Final = descriptor_for(
    "pic 9", name="trutht", source_locator="general/gl051.cbl:L175"
)
#: `03  account-in  pic 9(4)v99.`  [general/gl051.cbl:L178] - the operator's
#: account number in `nnnn.ss` form, scaled by the `MULTIPLY` statements.
_ACCOUNT_IN: Final = descriptor_for(
    "pic 9(4)v99", name="account-in", source_locator="general/gl051.cbl:L178"
)
#: `03  array-pc  pic 99.`  [general/gl051.cbl:L179]
_ARRAY_PC: Final = descriptor_for(
    "pic 99", name="array-pc", source_locator="general/gl051.cbl:L179"
)
#: `03  ws-vat-rate  pic 99v99  comp  value zero.`  [general/gl051.cbl:L183] -
#: the rate both `ROUNDED` computes divide by.
_WS_VAT_RATE: Final = descriptor_for(
    "pic 99v99 comp value zero",
    name="ws-vat-rate",
    source_locator="general/gl051.cbl:L183",
)
#: `03  acc-ok  pic 9(4)v99.`  [general/gl051.cbl:L233], reached through the
#: `redefines` of `ws-account-work` [general/gl051.cbl:L232]. The receiver of
#: the two scaling `DIVIDE` statements.
_ACC_OK: Final = descriptor_for(
    "pic 9(4)v99", name="acc-ok", source_locator="general/gl051.cbl:L233"
)

#: `03  l4-batch  pic z(4)9.`  [general/gl051.cbl:L289] - a print field, and the
#: FIRST receiver of the three-receiver `MOVE` at [general/gl051.cbl:L1017]. It
#: is the one edited picture in this program that `cobol/move.py` renders, so it
#: is the one whose rendering is reproduced rather than omitted.
_L4_BATCH: Final = descriptor_for(
    "pic z(4)9", name="l4-batch", source_locator="general/gl051.cbl:L289"
)
#: `03  l7-dr  pic zzz9.99b.`  [general/gl051.cbl:L308]
_L7_DR: Final = descriptor_for(
    "pic zzz9.99b", name="l7-dr", source_locator="general/gl051.cbl:L308"
)
#: `03  l7-cr  pic zzz9.99b.`  [general/gl051.cbl:L310]
_L7_CR: Final = descriptor_for(
    "pic zzz9.99b", name="l7-cr", source_locator="general/gl051.cbl:L310"
)
#: `03  l7-vat-ac  pic zzz9.99  blank when zero.`  [general/gl051.cbl:L314]
_L7_VAT_AC: Final = descriptor_for(
    "pic zzz9.99 blank when zero",
    name="l7-vat-ac",
    source_locator="general/gl051.cbl:L314",
)
#: `03  dr-error  pic x(12).`  [general/gl051.cbl:L321] and
#: `03  cr-error  pic x(12).`  [general/gl051.cbl:L322]. These two look like
#: pure print markers and are NOT: [general/gl051.cbl:L1056-L1059] reads them
#: back to decide whether to write an extra line and advance `line-cnt`, which
#: feeds the page-break test - question Q-8.
_DR_ERROR: Final = descriptor_for(
    "pic x(12)", name="dr-error", source_locator="general/gl051.cbl:L321"
)
_CR_ERROR: Final = descriptor_for(
    "pic x(12)", name="cr-error", source_locator="general/gl051.cbl:L322"
)
#: `03  l9-amount  pic z(9)9.99bb.`  [general/gl051.cbl:L331] - the receiver of
#: the `SUBTRACT ... GIVING` at [general/gl051.cbl:L1105].
_L9_AMOUNT: Final = descriptor_for(
    "pic z(9)9.99bb", name="l9-amount", source_locator="general/gl051.cbl:L331"
)


# ---------------------------------------------------------------------------
#  Literals the boundary tests and stores
# ---------------------------------------------------------------------------

#: `88  truet  value 1.`  [general/gl051.cbl:L177]. `gl051` declares this
#: condition name on its OWN working storage rather than in a copybook, so
#: `cobol/condition_names.py` does not hold it - that registry transcribes the
#: frozen copybooks only, and asking it for `truet` raises rather than
#: inventing an entry, which is rule R-3 working as intended. The VALUE is
#: therefore restated here from the declaration, and the TEST still goes through
#: `arithmetic.compare` so the comparator itself stays in `cobol/`.
_TRUET_VALUE: Final[int] = 1

#: `88  falset  value zero.`  [general/gl051.cbl:L176]. FINDING F-1: declared
#: and NEVER TESTED - not once in 1,282 lines. It is named here because rule R-5
#: asks for the declaration to be traceable, and it is deliberately not turned
#: into a predicate, because doing so would imply a test the COBOL never makes.
_FALSET_VALUE: Final[int] = 0

#: `move 99999 to WS-Batch-Nos.`  [general/gl051.cbl:L1072] - the sentinel
#: `get-a-batch` plants when the batch header cannot be found. Every subsequent
#: comparison at [general/gl051.cbl:L1029] then fails, silently skipping the
#: rest of that batch.
_BATCH_NOT_FOUND_SENTINEL: Final[int] = 99999

#: `if z = 99` - the "all batches" proof mode, tested four times inside the
#: boundary: [general/gl051.cbl:L1015], [general/gl051.cbl:L1026],
#: [general/gl051.cbl:L1088] and [general/gl051.cbl:L1099]. Question Q-5.
_Z_ALL_BATCHES: Final[int] = 99

#: `Page-Lines - 6` [general/gl051.cbl:L1060] against `Page-Lines - 12`
#: [general/gl051.cbl:L1111]. FINDING F-3: the two constants DIFFER, deliberately
#: - the second guards three multi-line blocks about to be written - and both are
#: reproduced as written rather than reconciled.
_PAGE_BREAK_MARGIN_DETAIL: Final[int] = 6
_PAGE_BREAK_MARGIN_TOTALS: Final[int] = 12

#: `move 6 to line-cnt.`  [general/gl051.cbl:L1087] - the number of lines a page
#: of headings has already consumed when `headings` returns. It shares the VALUE
#: of `_PAGE_BREAK_MARGIN_DETAIL` and NOT its meaning, so it is a separate name:
#: one is a count of lines written, the other is a margin subtracted from the
#: page depth. Conflating them would invite a future reader to "unify" two
#: constants the COBOL keeps apart by accident of value alone.
_HEADING_LINE_COUNT: Final[int] = 6

#: `move "^^^^^^^^^^" to dr-error` [general/gl051.cbl:L1149] and to `cr-error`
#: [general/gl051.cbl:L1163] - ten carets, into a `pic x(12)` field.
_ACCOUNT_ERROR_MARKER: Final[str] = "^^^^^^^^^^"

#: The divisor and multiplier of every account-scaling statement in this
#: program: [general/gl051.cbl:L604], [general/gl051.cbl:L607],
#: [general/gl051.cbl:L654], [general/gl051.cbl:L657] and
#: [general/gl051.cbl:L803]. An account is held as `nnnnss` and shown as
#: `nnnn.ss`, so the scale factor is a hundred - the same literal the two print
#: divides [general/gl051.cbl:L1035] and [general/gl051.cbl:L1037] use.
_ACCOUNT_SCALE: Final[int] = 100

#: `compute vat-amount rounded = post-amount * ws-vat-rate / 100`
#: [general/gl051.cbl:L791]. The percentage base, and the same literal inside
#: the compound expression at [general/gl051.cbl:L796].
_PERCENT: Final[int] = 100


# ---------------------------------------------------------------------------
#  `gl051`'s WORKING-STORAGE, as the boundary sees it
# ---------------------------------------------------------------------------


@dataclass
class _WorkingStorage:
    """The `gl051` working-storage items the six in-scope paragraphs SHARE.

    COBOL's paragraphs all see one working storage, and this is that storage -
    nothing more. It exists because the alternative, passing eight mutable
    values by hand through eight function signatures, would obscure what the
    COBOL makes plain: `get-description` clears a flag that `end-batch` reads,
    and `loop` advances a counter that `headings` resets. Every field below is a
    declared `gl051` working-storage item at the locator given; not one is
    invented, and none is a convenience aggregate.

    Only the fields the boundary actually reads or writes are here. The other
    thirty-odd working-storage items of `general/gl051.cbl` belong to the
    interactive sections and are recorded in the OMISSIONS list.

    EVERY DEFAULT IS PRODUCED BY `cobol/move.py`, NOT WRITTEN AS A PYTHON
    LITERAL. Three of these items carry `value zero` in their declaration -
    `save-batch` [general/gl051.cbl:L174], `line-cnt`
    [general/gl051.cbl:L166] and `page-nos` [general/gl051.cbl:L167], with
    `ws-vat-rate` [general/gl051.cbl:L183] a fourth - and the rest carry no
    `VALUE` clause at all, which GnuCOBOL initialises to the picture's own
    default: zero for a numeric item, spaces for an alphanumeric one. Moving the
    figurative constant into the descriptor reproduces both cases with the
    receiver's picture applied, so `account-in` starts as a two-place decimal
    zero and `dr-error` starts as twelve spaces rather than an empty string. A
    hand-written literal would have to guess the scale and the width.
    """

    #: `03  z  pic 99.`  [general/gl051.cbl:L172]. The batch-selection mode: 99
    #: means proof every batch, anything else means proof the one batch whose
    #: number is already in `WS-Batch-Nos`. Set only in out-of-scope interactive
    #: code, tested four times in scope. Question Q-5.
    z: int = field(default_factory=lambda: move.move(move.Figurative.ZERO, _Z))

    #: `03  save-batch  pic 9(5)  comp  value zero.`
    #: [general/gl051.cbl:L174]. Remembers the batch last printed, so the `z = 99`
    #: path emits one sub-heading per batch instead of one per posting.
    save_batch: int = field(
        default_factory=lambda: move.move(move.Figurative.ZERO, _SAVE_BATCH)
    )

    #: `03  trutht  pic 9.`  [general/gl051.cbl:L175]. The batch-valid flag.
    #: `gl050d` sets it to one before entry [general/gl051.cbl:L967]; inside the
    #: boundary it is only ever CLEARED, at [general/gl051.cbl:L1150] and
    #: [general/gl051.cbl:L1164]; and `end-batch` reads it at
    #: [general/gl051.cbl:L1101]. Defaulted to the promoted precondition's value
    #: so an instance is meaningful on its own - question Q-4.
    trutht: int = field(default_factory=lambda: move.move(_TRUET_VALUE, _TRUTHT))

    #: `03  line-cnt  binary-char  value zero.`  [general/gl051.cbl:L166].
    #: Question Q-8: presentation, and yet load-bearing, because the two tests it
    #: feeds can perform `headings`, which performs `zz060`, which can mutate a
    #: `SYSTEM-REC` column.
    line_cnt: int = field(
        default_factory=lambda: move.move(move.Figurative.ZERO, _LINE_CNT)
    )

    #: `03  page-nos  binary-char  value zero.`  [general/gl051.cbl:L167].
    #: `gl050d` zeroes it at [general/gl051.cbl:L966] and `headings` increments it
    #: at [general/gl051.cbl:L1077].
    page_nos: int = field(
        default_factory=lambda: move.move(move.Figurative.ZERO, _PAGE_NOS)
    )

    #: `03  l4-batch  pic z(4)9.`  [general/gl051.cbl:L289]. Written by the
    #: three-receiver `MOVE` [general/gl051.cbl:L1017] and again by `headings`
    #: [general/gl051.cbl:L1079], so it outlives a single paragraph.
    l4_batch: str = field(
        default_factory=lambda: move.move(move.Figurative.ZERO, _L4_BATCH)
    )

    #: `03  dr-error  pic x(12).`  [general/gl051.cbl:L321] and
    #: `03  cr-error  pic x(12).`  [general/gl051.cbl:L322]. Set by
    #: `get-description` and READ BACK by `loop`
    #: [general/gl051.cbl:L1056-L1057], which is why they are state and not
    #: locals.
    dr_error: str = field(
        default_factory=lambda: move.move(move.Figurative.SPACE, _DR_ERROR)
    )
    cr_error: str = field(
        default_factory=lambda: move.move(move.Figurative.SPACE, _CR_ERROR)
    )

    #: `01  ws-date-formats.`  [general/gl051.cbl:L196-L217] - `ws-swap`,
    #: `ws-conv-date`, `ws-date` and the UK, USA and International `redefines`
    #: over `ws-date`, plus `01 ws-Test-Date pic x(10).`
    #: [general/gl051.cbl:L195]. Owned by `acas_posting.dates`, which is where the
    #: `redefines` overlays and the `INSPECT` statements live.
    ws_date_formats: WsDateFormats = field(default_factory=WsDateFormats)

    #: `01  maps03-ws.` from `copy "wsmaps03.cob"` [general/gl051.cbl:L128] - the
    #: interface block the date module is called with.
    maps03_ws: Maps03Ws = field(default_factory=Maps03Ws)

    #: `03  account-in  pic 9(4)v99.`  [general/gl051.cbl:L178] and
    #: `03  array-pc  pic 99.`  [general/gl051.cbl:L179]. Inputs to the five
    #: account-scaling statements section 0.4.1.2 names. They reach this boundary
    #: only through those statements; the `accept` that fills them is out of
    #: scope.
    account_in: decimal.Decimal = field(
        default_factory=lambda: move.move(move.Figurative.ZERO, _ACCOUNT_IN)
    )
    array_pc: int = field(
        default_factory=lambda: move.move(move.Figurative.ZERO, _ARRAY_PC)
    )

    #: `03  ws-vat-rate  pic 99v99  comp  value zero.`
    #: [general/gl051.cbl:L183]. The rate both `ROUNDED` computes use.
    ws_vat_rate: decimal.Decimal = field(
        default_factory=lambda: move.move(move.Figurative.ZERO, _WS_VAT_RATE)
    )


@dataclass(frozen=True)
class _HandlerLinkage:
    """The five arguments every file-handler call in the facade copybook takes.

    `copy "Proc-ACAS-FH-Calls.cob"` [general/gl051.cbl:L1281] resolves each of
    its twelve verbs onto a dispatch paragraph, and every one of those paragraphs
    issues the SAME five-argument `CALL`
    [copybooks/Proc-ACAS-FH-Calls.cob:L51-L57], verbatim:

        call     "acas007" using System-Record
                                 WS-Batch-Record
                                 File-Access
                                 File-Defs
                                 ACAS-DAL-Common-Data.

    Two of the five are this program's LINKAGE - `System-Record`
    [general/gl051.cbl:L348] and `File-Defs` [general/gl051.cbl:L349] - and three
    are its WORKING-STORAGE: `File-Access` from `copy "wsfnctn.cob"`
    [general/gl051.cbl:L129], `ACAS-DAL-Common-Data` from
    `copy "Test-Data-Flags.cob"` [general/gl051.cbl:L158], and the record buffer,
    which differs per entity. All three record buffers are held together here
    because the COBOL holds them together: they are simply three more
    working-storage items, and which one a verb uses is decided by the verb, not
    by the caller.

    Frozen because the CONTAINER never changes during a run - the records it
    points at are mutated in place, exactly as COBOL mutates its working storage.
    """

    #: `copy "wssystem.cob".`  [general/gl051.cbl:L348] - linkage parameter two.
    system_record: SystemRecord
    #: `copy "wspost.cob".`  [general/gl051.cbl:L132] - the read target of
    #: `GL-Posting-Read-Next` [general/gl051.cbl:L1008].
    posting: WsPostingRecord
    #: `copy "wsbatch.cob".`  [general/gl051.cbl:L131] - the read target of
    #: `GL-Batch-Read-Indexed` [general/gl051.cbl:L1070], the source of the
    #: control totals, AND the destination of `Batch-Status`.
    batch: GlBatchRecord
    #: `copy "wsledger.cob".`  [general/gl051.cbl:L130] - the read target of both
    #: `GL-Nominal-Read-Indexed` calls, [general/gl051.cbl:L1142] and
    #: [general/gl051.cbl:L1156].
    ledger: WsLedgerRecord
    #: `01 File-Access.`  [copybooks/wsfnctn.cob:L23-L38] - carries `Fs-Reply`,
    #: which every verb below tests, and `We-Error`, which `get-description` uses
    #: as a local flag.
    file_access: FileAccess
    #: `copy "wsnames.cob".`  [general/gl051.cbl:L349] - linkage parameter four.
    file_defs: FileDefs
    #: `01 ACAS-DAL-Common-Data.`  [copybooks/Test-Data-Flags.cob] - the logging
    #: switch.
    dal_common: AcasDalCommonData


# ---------------------------------------------------------------------------
#  The three file-handler verbs the boundary performs - ALL READS
# ---------------------------------------------------------------------------
# `batch-print` performs exactly three verbs and every one of them is a read.
# There is no write, no rewrite, no delete, no open and no close inside the
# boundary; the opens are `gl050d`'s [general/gl051.cbl:L980-L981] and so are the
# closes [general/gl051.cbl:L989-L990]. Each verb gets its own adapter so that
# question Q-6 - the facade's Python call shape - has exactly three places to
# reconcile rather than four scattered call sites.


def _gl_posting_read_next(linkage: _HandlerLinkage) -> None:
    """`perform GL-Posting-Read-Next.`  [general/gl051.cbl:L1008].

    The facade paragraph, verbatim
    [copybooks/Proc-ACAS-FH-Calls.cob:L397-L400]:

         GL-Posting-Read-Next.
             move     zero to Access-Type.
             set      fn-Read-Next to true.
             perform  acas006.

    Setting the access type and the function code belongs to the facade, not to
    a caller, so this adapter forwards and nothing more. The COBOL's own comment
    on the call site reads "read posting-file next record at end", and the reply
    is tested INLINE by `loop` immediately afterwards - `gl051` copies
    [copybooks/Proc-ACAS-FH-Calls.cob], which has no error-check paragraph.
    """
    facade.gl_posting_read_next(
        facade.FacadeContext(
            linkage.system_record,
            linkage.posting,
            linkage.file_access,
            linkage.file_defs,
            linkage.dal_common,
        ),
    )


def _gl_batch_read_indexed(linkage: _HandlerLinkage) -> None:
    """`perform GL-Batch-Read-Indexed.`  [general/gl051.cbl:L1070].

    The facade paragraph, verbatim
    [copybooks/Proc-ACAS-FH-Calls.cob:L465-L469]:

         GL-Batch-Read-Indexed.
             move     zero to Access-Type.
             set      fn-Read-Indexed to true.
             perform  acas007.

    Reads the header of whichever batch `WS-Batch-Nos` currently names; the
    caller, `get-a-batch`, has just put the posting's own batch number there.
    """
    facade.gl_batch_read_indexed(
        facade.FacadeContext(
            linkage.system_record,
            linkage.batch,
            linkage.file_access,
            linkage.file_defs,
            linkage.dal_common,
        ),
    )


def _gl_nominal_read_indexed(linkage: _HandlerLinkage) -> None:
    """`perform GL-Nominal-Read-Indexed.`  [general/gl051.cbl:L1142] and L1156.

    The facade paragraph, verbatim
    [copybooks/Proc-ACAS-FH-Calls.cob:L339-L342]:

         GL-Nominal-Read-Indexed.
             move     zero to Access-Type.
             set      fn-Read-Indexed to true.
             perform  acas005.

    Performed TWICE per posting by `get-description` - once for the debit account
    and once for the credit - and that is not an accident to be optimised away.
    Section 0.8.4, verbatim: "Any performance work is therefore out of scope by
    construction, not merely unrequested." Nothing here caches the result, even
    though consecutive postings in a proofed batch very often name the same
    accounts.
    """
    facade.gl_nominal_read_indexed(
        facade.FacadeContext(
            linkage.system_record,
            linkage.ledger,
            linkage.file_access,
            linkage.file_defs,
            linkage.dal_common,
        ),
    )


#  net.  [general/gl051.cbl:L788]
#  # BOUNDARY: this paragraph sits inside `gl050c section.`
#  [general/gl051.cbl:L496], which is OUT OF SCOPE in its entirety. It is
#  migrated because Agent Action Plan section 0.4.1.2 names its compute
#  explicitly, and because that compute produces `Vat-Amount` - one of the two
#  values the gate accumulates. Nothing else from `gl050c` is here.


def _net(storage: _WorkingStorage, posting: WsPostingRecord) -> decimal.Decimal | int:
    """`net.` - VAT computed FROM a net amount  [general/gl051.cbl:L788-L791].

        788  net.
        791      compute  vat-amount rounded = post-amount * ws-vat-rate / 100.

    ONE OF THE FIVE `ROUNDED` SITES IN THE WHOLE MIGRATION, and one of the two
    this program owns; the others are [general/gl051.cbl:L796],
    [general/gl080.cbl:L328], [irs/irs030.cbl:L1551] and
    [irs/irs030.cbl:L1562]. `ROUNDED` on a COBOL store means round half away from
    zero, where the default - every other store in this program - truncates
    toward zero, so the flag is passed explicitly here and left at its default
    everywhere else. Getting that backwards would corrupt essentially every
    posted figure.

    THE WHOLE EXPRESSION IS ONE STORE. `post-amount * ws-vat-rate / 100` is
    evaluated at extended intermediate precision and the result is stored ONCE,
    into `Vat-Amount`'s two decimal places. Splitting it into a multiply
    followed by a divide would store twice and could lose a penny on the
    intermediate, which is why the expression is handed to `compute` as a
    callable rather than pre-computed.

    FINDING: a superseded commented-out variant of this compute sits directly
    above it at [general/gl051.cbl:L790], referring to a differently named rate
    field. It is the same character of leftover the plan records as anomaly 19
    for `irs030` [irs/irs030.cbl:L1550]. Not reproduced - a comment has no
    behaviour - but recorded.

    Args:
        storage: Supplies `ws-vat-rate` [general/gl051.cbl:L183].
        posting: Supplies `Post-Amount` and RECEIVES `Vat-Amount`
            [copybooks/wspost.cob:L23] and [copybooks/wspost.cob:L28].

    Returns:
        The stored `Vat-Amount`, which is also written back onto `posting`.
    """
    # 791  compute  vat-amount rounded = post-amount * ws-vat-rate / 100.
    posting.vat_amount = arithmetic.compute(
        lambda: arithmetic.intermediate(posting.post_amount)
        * arithmetic.intermediate(storage.ws_vat_rate)
        / arithmetic.intermediate(_PERCENT),
        receiving=_VAT_AMOUNT,
        rounded=True,
    )
    return posting.vat_amount


#  gross.  [general/gl051.cbl:L793]
#  # BOUNDARY: as `net.` above - inside the OUT-OF-SCOPE `gl050c section.`
#  [general/gl051.cbl:L496], migrated only because section 0.4.1.2 names its two
#  statements.


def _gross(storage: _WorkingStorage, posting: WsPostingRecord) -> decimal.Decimal | int:
    """`gross.` - VAT extracted FROM a gross amount  [general/gl051.cbl:L793-L797].

        793  gross.
        796      compute  vat-amount rounded =
                          post-amount - (post-amount / ((ws-vat-rate + 100) / 100)).
        797      subtract vat-amount  from  post-amount.

    TWO STORES, AND THEY DISAGREE ON ROUNDING. The first is the second of this
    program's two `ROUNDED` sites; the second, one line later, is un-`ROUNDED`
    and therefore truncates. That adjacency is the reason rounding is a per-call
    argument in `acas_posting.cobol.arithmetic` and can never be a module-wide
    mode - and it is not unique to `gl051`: three of the migration's five
    `ROUNDED` sites are followed immediately by a truncating store, the others
    being [general/gl080.cbl:L329] and [irs/irs030.cbl:L1564].

    AMBIGUITY Q-2 - THE COMPOUND EXPRESSION. Section 0.6.8 singles this
    statement out, verbatim: "the compound VAT expression, which is the one place
    a precision difference could change a stored penny." There is no `-std=`
    dialect selection and no `>>SET ARITHMETIC` directive anywhere in the
    repository, so the compiler's DEFAULT intermediate precision governs the
    nested division. The expected value for any given rate and amount must
    therefore be CAPTURED from the compiled program and never derived by reading
    this expression. What is reproduced structurally is what can be read with
    certainty: the parenthesisation exactly as written, one single store, and
    extended precision throughout the intermediate.

    `SUBTRACT a FROM b` with no `GIVING` stores into b, so
    [general/gl051.cbl:L797] leaves `Post-Amount` holding the net amount - the
    gross it arrived with, less the VAT just extracted. The order matters: the
    subtract reads the `Vat-Amount` the compute has just stored, so it consumes
    the ROUNDED value, not the exact one.

    Args:
        storage: Supplies `ws-vat-rate` [general/gl051.cbl:L183].
        posting: Supplies and RECEIVES both `Post-Amount` and `Vat-Amount`.

    Returns:
        The stored `Vat-Amount`. `posting.post_amount` is reduced in place.
    """
    # 796  compute  vat-amount rounded =
    #               post-amount - (post-amount / ((ws-vat-rate + 100) / 100)).
    # AMBIGUITY Q-2: default intermediate precision governs the nested divide;
    # the expected value comes from the compiled program, not from this reading.
    posting.vat_amount = arithmetic.compute(
        lambda: arithmetic.intermediate(posting.post_amount)
        - (
            arithmetic.intermediate(posting.post_amount)
            / (
                (
                    arithmetic.intermediate(storage.ws_vat_rate)
                    + arithmetic.intermediate(_PERCENT)
                )
                / arithmetic.intermediate(_PERCENT)
            )
        ),
        receiving=_VAT_AMOUNT,
        rounded=True,
    )

    # 797  subtract vat-amount  from  post-amount.
    # No `GIVING`, so the receiver is `post-amount` itself; and NO `ROUNDED`, so
    # this store truncates one line after the one above rounded.
    posting.post_amount = arithmetic.subtract_from(
        posting.vat_amount,
        receiver_value=posting.post_amount,
        receiving=_POST_AMOUNT,
        rounded=False,
    )
    return posting.vat_amount


# ---------------------------------------------------------------------------
#  The five account-scaling statements
# ---------------------------------------------------------------------------
# # BOUNDARY: not one of these five lives inside `batch-print`. Agent Action Plan
# section 0.4.1.2 names them individually - "the account scaling multiplies and
# divides by 100 at [general/gl051.cbl:L604], [general/gl051.cbl:L607],
# [general/gl051.cbl:L654], [general/gl051.cbl:L657], [general/gl051.cbl:L803]" -
# so each is reproduced as its own named helper, and each says which OUT-OF-SCOPE
# paragraph it was taken from. All five are un-`ROUNDED`, so all five truncate.
#
# The two directions are inverses: an account number is STORED as `nnnnss` in a
# `pic 9(6)` field and SHOWN to the operator as `nnnn.ss` in a `pic 9(4)v99` one.
# `DIVIDE a BY b GIVING c` means `c = a / b`; `MULTIPLY a BY b GIVING c` means
# `c = a * b`.


def _scale_acc_ok_from_post_dr(posting: WsPostingRecord) -> decimal.Decimal | int:
    """`divide post-dr by 100 giving acc-ok`  [general/gl051.cbl:L604].

    # BOUNDARY: the `if convention = "DR"` true branch
    [general/gl051.cbl:L603-L605], inside the OUT-OF-SCOPE `gl050c section.`
    [general/gl051.cbl:L496]. Unpacks the stored debit account into the
    operator's `nnnn.ss` display form. Un-`ROUNDED`, therefore truncating.
    """
    # 604  divide post-dr by 100 giving acc-ok
    return arithmetic.divide_by_giving(
        posting.post_dr, _ACCOUNT_SCALE, _ACC_OK, rounded=False
    )


def _scale_acc_ok_from_post_cr(posting: WsPostingRecord) -> decimal.Decimal | int:
    """`divide post-cr by 100 giving acc-ok`  [general/gl051.cbl:L607].

    # BOUNDARY: the `else` branch of the same statement
    [general/gl051.cbl:L606-L608], inside the OUT-OF-SCOPE `gl050c section.`
    The credit-side twin of `_scale_acc_ok_from_post_dr`; the pair differ only in
    which account they unpack and which profit centre they carry across.
    Un-`ROUNDED`, therefore truncating.
    """
    # 607  divide post-cr by 100 giving acc-ok
    return arithmetic.divide_by_giving(
        posting.post_cr, _ACCOUNT_SCALE, _ACC_OK, rounded=False
    )


def _scale_post_dr_from_account(storage: _WorkingStorage) -> decimal.Decimal | int:
    """`multiply account-in by 100 giving post-dr`  [general/gl051.cbl:L654].

    # BOUNDARY: `accept-amount.` [general/gl051.cbl:L650], inside the
    OUT-OF-SCOPE `gl050c section.` [general/gl051.cbl:L496]. The inverse of
    `_scale_acc_ok_from_post_dr`: packs the operator's `nnnn.ss` back into the
    stored `pic 9(6)` debit account. Un-`ROUNDED`, therefore truncating - so a
    third decimal place typed by the operator is discarded rather than rounded
    up.
    """
    # 654  multiply account-in by 100 giving post-dr
    return arithmetic.multiply_by_giving(
        storage.account_in, _ACCOUNT_SCALE, _POST_DR, rounded=False
    )


def _scale_post_cr_from_account(storage: _WorkingStorage) -> decimal.Decimal | int:
    """`multiply account-in by 100 giving post-cr`  [general/gl051.cbl:L657].

    # BOUNDARY: the `else` branch of the same statement
    [general/gl051.cbl:L656-L658] in `accept-amount.`
    [general/gl051.cbl:L650], inside the OUT-OF-SCOPE `gl050c section.`
    Un-`ROUNDED`, therefore truncating.
    """
    # 657  multiply account-in by 100 giving post-cr
    return arithmetic.multiply_by_giving(
        storage.account_in, _ACCOUNT_SCALE, _POST_CR, rounded=False
    )


def _scale_ledger_nos_from_account(storage: _WorkingStorage) -> decimal.Decimal | int:
    """`multiply account-in by 100 giving WS-Ledger-Nos`  [general/gl051.cbl:L803].

    # BOUNDARY - AND READ THIS ONE CAREFULLY. This statement lives inside the
    OUT-OF-SCOPE `get-description.` at [general/gl051.cbl:L799], NOT inside the
    in-scope `get-description.` at [general/gl051.cbl:L1136]. The two paragraphs
    share a name and do a similar job, and they are NOT the same code:

        L799  builds the key from `account-in` and `array-pc`, then displays
              `ledger-name` on success and moves 255 to `we-error` on failure
              [general/gl051.cbl:L808]
        L1136 builds the key from `post-dr`/`dr-pc` and then `post-cr`/`cr-pc`,
              twice, and moves 1 to `we-error` on failure
              [general/gl051.cbl:L1144]

    Finding F-5 records the two disagreeing sentinels. This helper reproduces the
    L803 statement only, because section 0.4.1.2 names it; the rest of L799's
    paragraph is out of scope, and `_batch_print_get_description` below is the
    in-scope one. Un-`ROUNDED`, therefore truncating.
    """
    # 803  multiply account-in by 100 giving WS-Ledger-Nos.
    return arithmetic.multiply_by_giving(
        storage.account_in, _ACCOUNT_SCALE, _WS_LEDGER_NOS, rounded=False
    )


# ---------------------------------------------------------------------------
#  The four date sections - thin delegations to `acas_posting.dates`
# ---------------------------------------------------------------------------


#  maps03  section.  [general/gl051.cbl:L1273]


def _maps03(maps03_ws: Maps03Ws) -> None:
    """`maps03 section.` - the date-module wrapper  [general/gl051.cbl:L1273-L1279].

        1273  maps03       section.
        1276      call     "maps04"  using  maps03-ws.
        1278  maps04-exit.
        1279      exit     section.

    # ANOMALY A-22, OCCURRENCE 2  [general/gl051.cbl:L1273] and
    # [general/gl051.cbl:L1278] - the section is named after the INTERFACE
    # COPYBOOK it passes (`wsmaps03.cob` [general/gl051.cbl:L128]) while its exit
    # label is named after the PROGRAM it calls (`maps04`
    # [general/gl051.cbl:L1276]). One three-line section, two different naming
    # conventions.
    # Reproduced deliberately per R-4; DO NOT FIX. The Agent Action Plan records
    # this defect for `gl070` ALONE - `[general/gl070.cbl:L603-L609]`, where the
    # section is `maps03` and the exit is `maps04-exit` - and `gl051` carries it
    # IDENTICALLY. This is therefore a SECOND OCCURRENCE of A-22 and belongs in
    # the anomaly log as such. The reproduction is the naming itself: this
    # function is `_maps03`, after the section, and its exit label `maps04-exit`
    # is recorded here and in the traceability footer, because Python has no
    # separate exit label to misname.

    RULE R-1. `call "maps04"` becomes a call into `acas_posting.dates`, which
    reimplements `common/maps04.cbl` in full - the 1600-12-31 ordinal epoch, the
    six-part reject test [common/maps04.cbl:L140-L146] and the reject behaviour of
    leaving the output field UNTOUCHED [common/maps04.cbl:L146]. Nothing here
    executes COBOL, spawns a process or loads a shared object.

    Args:
        maps03_ws: `01 maps03-ws.` - `u-date` and `u-bin`, converted in place in
            whichever direction the caller has primed.
    """
    # 1276  call     "maps04"  using  maps03-ws.
    _dates_maps03(maps03_ws)
    # 1278  maps04-exit.
    # 1279      exit     section.   ->  fall out of the function.


#  zz050-Validate-Date  section.  [general/gl051.cbl:L1169]


def _zz050_validate_date(storage: _WorkingStorage, date_form: int) -> int:
    """`zz050-Validate-Date section.`  [general/gl051.cbl:L1169-L1206].

    Validates `ws-test-date` and converts it to UK form, leaving `u-bin` non-zero
    when the date is good. Three paragraphs - the section body, `zz050-test-date.`
    [general/gl051.cbl:L1200] and `zz050-exit.` [general/gl051.cbl:L1205] - and
    both `GO TO` statements in it, [general/gl051.cbl:L1186] and
    [general/gl051.cbl:L1191], are class 3 exits onto `zz050-test-date`, all of
    which `acas_posting.dates` owns.

    THIS SECTION IS NOT THE SAME AS THE OTHER CARRIERS' AND MUST NOT BE
    CONSOLIDATED WITH THEM. `gl051` carries three statements the Sales and
    Purchase carriers do not have at all, verbatim
    [general/gl051.cbl:L1178-L1180]:

        1178      inspect  ws-test-date replacing all "." by "/".
        1179      inspect  ws-test-date replacing all "," by "/".
        1180      inspect  ws-test-date replacing all "-" by "/".

    `sl060`, `sl100`, `pl060` and `pl100` omit them entirely, so their `zz050`
    accepts only slash-separated input while this one silently normalises three
    other separators. That is exactly why `acas_posting.dates` publishes TWO
    variants, and why this module calls the `gl051` one. Passing the other would
    make well-formed operator input invalid.

    `INSPECT ... REPLACING ALL` is `acas_posting.dates`' responsibility, not this
    module's and not `cobol/move.py`'s - section 0.3.1 puts every
    language-semantics primitive in `cobol/` and the shared date logic in
    `dates.py`, and this function does not implement one character of it.

    AMBIGUITY Q-7. `if Date-Form = zero move 1 to Date-Form`
    [general/gl051.cbl:L1183-L1184] MUTATES a `SYSTEM-REC` column, so the change
    is visible in a table dump. The mutated value is returned rather than
    swallowed, and the caller writes it back.

    Args:
        storage: Supplies `ws-test-date` and receives `ws-date`, plus the
            `maps03-ws` block the wrapper is called with.
        date_form: `Date-Form` as it stands on the system record.

    Returns:
        `Date-Form`, possibly changed from zero to one - question Q-7.
    """
    return zz050_validate_date_gl051(
        storage.ws_date_formats,
        storage.maps03_ws,
        date_form,
        # The wrapper this program performs is the one named `maps03`
        # [general/gl051.cbl:L1273], NOT the `maps04`-named wrapper the Sales and
        # Purchase carriers perform. Same implementation, and the name is what
        # carries anomaly A-22.
        wrapper=_maps03,
    )


#  zz060-Convert-Date  section.  [general/gl051.cbl:L1208]


def _zz060_convert_date(storage: _WorkingStorage, date_form: int) -> int:
    """`zz060-Convert-Date section.`  [general/gl051.cbl:L1208-L1241].

    Converts a BINARY day number in `u-bin` into `ws-date` in whichever of the
    UK, USA or International presentations `Date-Form` selects. Its three `GO TO`
    statements - [general/gl051.cbl:L1220], [general/gl051.cbl:L1226] and
    [general/gl051.cbl:L1231] - are all class 3 exits onto `zz060-Exit.`
    [general/gl051.cbl:L1240], and `acas_posting.dates` owns them.

    THE ONLY SECTION `batch-print` REACHES, and it reaches it twice: from `loop`
    at [general/gl051.cbl:L1020] and from `headings` at
    [general/gl051.cbl:L1082]. Both call sites first prime `u-bin` with the batch
    header's `Entered` date [general/gl051.cbl:L1019] and
    [general/gl051.cbl:L1081], which is `binary-long`
    [copybooks/wsbatch.cob:L36].

    IT IS PRESERVED EVEN THOUGH ITS OUTPUT IS A PRINT FIELD, for two reasons.
    First it performs `maps03` [general/gl051.cbl:L1217], which reaches the date
    module. Second, and decisively, it MUTATES `Date-Form` when that column is
    zero - `if Date-Form = zero move 1 to Date-Form`
    [general/gl051.cbl:L1223-L1224] - and `Date-Form` is a `SYSTEM-REC` column,
    so the mutation is diff-visible. Dropping the call because "the result is
    only printed" would lose a database effect. Question Q-7.

    `zz060` is byte-identical across all six carriers EXCEPT for one token: the
    name of the wrapper it performs. `gl051` and `gl070` perform `maps03`; the
    Sales and Purchase carriers perform `maps04`. The `maps03` alias is passed
    here for that reason.

    Args:
        storage: Supplies the primed `maps03-ws` and receives `ws-date`.
        date_form: `Date-Form` as it stands on the system record.

    Returns:
        `Date-Form`, possibly changed from zero to one - question Q-7.
    """
    return zz060_convert_date(
        storage.ws_date_formats,
        storage.maps03_ws,
        date_form,
        wrapper=_maps03,
    )


#  zz070-Convert-Date  section.  [general/gl051.cbl:L1243]


def _zz070_convert_date(storage: _WorkingStorage, to_day: str, date_form: int) -> int:
    """`zz070-Convert-Date section.`  [general/gl051.cbl:L1243-L1271].

    Converts the run date `to-day` [general/gl051.cbl:L351] into `ws-date` in the
    presentation `Date-Form` selects. Its two `GO TO` statements -
    [general/gl051.cbl:L1256] and [general/gl051.cbl:L1261] - are class 3 exits
    onto `zz070-Exit.` [general/gl051.cbl:L1270].

    This section is BYTE-IDENTICAL in all ten carriers, so the consolidated
    `acas_posting.dates` entry point is called with no variant selection. It
    takes no wrapper argument because it performs no wrapper: it reformats the
    text date it is given and never calls the date module.

    NOT REACHED FROM INSIDE THE BOUNDARY. The only `perform` of it in this program
    is at [general/gl051.cbl:L973], in the OUT-OF-SCOPE `gl050d section.`
    [general/gl051.cbl:L961]. It is present because rule R-5 asks for a named
    function per in-scope section and section 0.4.1.2 counts all four date
    sections as in scope, and because a caller standing where `gl050d` stands
    needs it. It also mutates `Date-Form` when that column is zero
    [general/gl051.cbl:L1253-L1254] - question Q-7 again.

    Args:
        storage: Receives `ws-date`.
        to_day: `01 to-day pic x(10).` [general/gl051.cbl:L351] - linkage
            parameter three, a DD/MM/CCYY text date.
        date_form: `Date-Form` as it stands on the system record.

    Returns:
        `Date-Form`, possibly changed from zero to one - question Q-7.
    """
    return zz070_convert_date(storage.ws_date_formats, to_day, date_form)



# ---------------------------------------------------------------------------
#  batch-print  section.   [general/gl051.cbl:L999-L1166]
# ---------------------------------------------------------------------------


#  batch-print  section.  - the section's own entry statements
#  [general/gl051.cbl:L999-L1003]


def _batch_print(storage: _WorkingStorage, linkage: _HandlerLinkage) -> None:
    """`batch-print section.` - the section entry and its three-part body.

         999  batch-print                 section.
        1002      perform  headings.
        1003      move     1 to WS-Ledger.

    Two statements of its own, and then it falls straight through into `loop.`
    [general/gl051.cbl:L1005].

    THIS FUNCTION IS WHERE THE CLASS 2 `GO TO` IS MADE GOOD, and that is its
    most important job. `loop` leaves itself at [general/gl051.cbl:L1010] with
    `go to end-batch`, and section 0.6.3 is explicit about what that must become,
    verbatim: "the target label is followed by real work - closing files,
    printing totals, rewriting a control record - so the transformation is
    `break` PLUS faithful placement of that work after the loop, not `break`
    alone. Mis-splitting here would silently drop end-of-run processing." Here
    the "real work" IS THE ENTIRE CONTROL-TOTAL GATE, so the split is: `_loop`
    returns when the posting file is exhausted, and `_end_batch` is then called
    from HERE, unconditionally, exactly as control arrives at
    [general/gl051.cbl:L1096]. Calling `_end_batch` from inside `_loop` would put
    the gate inside the iteration; leaving it out would delete the gate.

    `main-exit.` [general/gl051.cbl:L1166] then always runs, because it is the
    section's terminator: all three of `end-batch`'s exits go to it and the
    section cannot end any other way.

    `move 1 to WS-Ledger` [general/gl051.cbl:L1003] SELECTS THE GENERAL LEDGER.
    One is `88 GL-Batch value 1.` [copybooks/wsbatch.cob:L16], sibling to
    `PL-Batch` and `SL-Batch`, and it is the first half of the batch key that
    every `GL-Batch-Read-Indexed` below reads on. The value comes from the
    condition-name registry rather than from a bare literal so that the
    declaration, not this file, remains its source of truth.

    ORDER IS NOT NEGOTIABLE: `headings` runs BEFORE the ledger is selected, and
    `headings` itself performs a date conversion [general/gl051.cbl:L1082] that
    can mutate `Date-Form` on the system record. Reordering the two statements
    would be harmless today and is still not done, because "harmless today" is
    not the standard this migration is held to.

    Args:
        storage: The section's shared working storage.
        linkage: The five handler arguments plus the records the section reads
            and the batch record whose `Batch-Status` it sets.
    """
    # 1002  perform  headings.
    _headings(storage, linkage)

    # 1003  move     1 to WS-Ledger.       *> `88 GL-Batch value 1.`
    linkage.batch.ws_batch_key.ws_ledger = move.move(
        values_for("GL-Batch")[0], _WS_LEDGER
    )

    # 1005  loop.   - the posting read loop, which leaves itself two ways:
    #                 `go to loop` (class 1, inside `_loop`) and
    #                 `go to end-batch` (class 2, which returns to here).
    _loop(storage, linkage)

    # 1096  end-batch.   - THE CLASS 2 TARGET. The whole gate, placed after the
    #                      loop rather than inside it.
    _end_batch(storage, linkage)

    # 1166  main-exit.   exit section.
    _batch_print_main_exit()


#  loop.  [general/gl051.cbl:L1005]


def _loop(storage: _WorkingStorage, linkage: _HandlerLinkage) -> None:
    """`loop.` - the read loop AND THE ACCUMULATION  [general/gl051.cbl:L1005-L1065].

    Sixty-one lines of which two matter more than all the rest:

        1063      add      post-amount  to  actual-gross.
        1064      add      vat-amount   to  actual-vat.

    THOSE TWO STATEMENTS ARE THE ACCUMULATION, AND THE AGENT ACTION PLAN NEVER
    CITES THEM. Without them the gate at [general/gl051.cbl:L1117-L1121] compares
    the operator's entered totals against zero and rejects every batch that has
    any value in it at all. They sit at the very end of each iteration, after the
    print line has been built and after `get-description` has checked the
    accounts, and they are unconditional: every posting that reaches
    [general/gl051.cbl:L1032] is counted, including one whose accounts were just
    found missing.

    THE ACCUMULATORS ARE UNSIGNED AND THE ADDENDS ARE SIGNED. `Actual-Gross` and
    `Actual-Vat` are `pic 9(9)v99 comp-3` with no `S`
    [copybooks/wsbatch.cob:L43-L44]; `Post-Amount` and `Vat-Amount` are
    `pic s9(8)v99` [copybooks/wspost.cob:L23] and [copybooks/wspost.cob:L28].
    A negative posting therefore adds its MAGNITUDE - question Q-3. Nothing here
    guards against it, because a guard would be a new validation under rule R-3.

    THE READ AND ITS TWO EXITS.

        1008      perform  GL-Posting-Read-Next.
        1009      if       fs-reply = 10
        1010               go to  end-batch.       *> GO TO class 2
        1012      if       batch = zero
        1013               go to  loop.             *> GO TO class 1

    End of file leaves the loop for good and hands control to the gate; a zero
    batch number is skipped with no message, no counter and no trace.

    THE BATCH-SELECTION BLOCK IS A NESTED THREE-WAY, not the two-way the plan's
    summary suggests [general/gl051.cbl:L1015-L1030]:

        1015      if       z = 99
        1016        and    save-batch not = batch
                           ... new-batch sub-heading ...
        1025      else
        1026       if      z = 99
        1027               then next sentence
        1028       else
        1029         if    batch not = WS-Batch-Nos
        1030               go to  loop.

    Read as three arms: in all-batches mode with a batch number that has changed,
    emit a sub-heading and read that batch's header; in all-batches mode with the
    same batch number, do nothing and carry on - `then next sentence` is COBOL's
    explicit no-op, and it is written out below as one, because omitting the arm
    would collapse the three-way into a two-way with different behaviour; in
    single-batch mode, skip every posting that is not the batch being proofed.

    THE THREE-RECEIVER `MOVE` AT [general/gl051.cbl:L1017] moves one sending
    field into three receivers of three different pictures - an edited print
    field, a `comp` binary and a display numeric - so each conversion is
    performed independently against its own receiver. One conversion assigned
    three times would be a different statement.

    EVERYTHING FROM [general/gl051.cbl:L1032] TO [general/gl051.cbl:L1050] IS
    PRINT-LINE CONSTRUCTION with no database effect, and is recorded in the
    OMISSIONS list. Three of those statements are nonetheless reproduced as
    arithmetic because section 0.4.1.2's census names them -
    [general/gl051.cbl:L1035], [general/gl051.cbl:L1037] and
    [general/gl051.cbl:L1044] - so their truncation into an edited receiver is
    modelled even though the rendering is not; see question Q-14.

    `line-cnt` IS PRESENTATION AND STILL LOAD-BEARING - question Q-8. The
    increments at [general/gl051.cbl:L1024], [general/gl051.cbl:L1053] and
    [general/gl051.cbl:L1059] feed the page-break test at
    [general/gl051.cbl:L1060], which can perform `headings`, which performs
    `zz060`, which can mutate `Date-Form` on `SYSTEM-REC`. Dropping the counter
    because "it only drives printing" would drop a database effect.

    Args:
        storage: The section's shared working storage - `z`, `save-batch`,
            `line-cnt`, the error markers and the date buffers.
        linkage: Supplies the posting the read fills; receives the accumulated
            totals on the batch record.
    """
    while True:
        # 1008  perform  GL-Posting-Read-Next.   *> read posting-file next at end
        _gl_posting_read_next(linkage)

        # 1009  if       fs-reply = 10
        # 1010           go to  end-batch.
        # GO TO class 2 - forward terminator. `break`, PLUS the whole `end-batch`
        # body placed after the loop by `_batch_print`. Ten is
        # `FsReply.END_OF_FILE`; the literal never appears.
        if linkage.file_access.fs_reply == FsReply.END_OF_FILE:
            return

        # 1012  if       batch = zero
        # 1013           go to  loop.
        # GO TO class 1 - loop-back. A SILENT SKIP: no message, no counter, no
        # trace, and rule R-3 forbids adding one.
        if arithmetic.compare(linkage.posting.ws_post_key.batch, 0) == 0:
            continue

        # --- the batch-selection three-way  [general/gl051.cbl:L1015-L1030] ---

        # 1015  if       z = 99
        # 1016    and    save-batch not = batch
        if (
            arithmetic.compare(storage.z, _Z_ALL_BATCHES) == 0
            and arithmetic.compare(
                storage.save_batch, linkage.posting.ws_post_key.batch
            )
            != 0
        ):
            # 1017  move   batch  to  l4-batch save-batch WS-Batch-Nos
            # ONE sending field, THREE receivers, THREE pictures: `l4-batch pic
            # z(4)9` [general/gl051.cbl:L289], `save-batch pic 9(5) comp`
            # [general/gl051.cbl:L174] and `WS-Batch-Nos pic 9(5)`
            # [copybooks/wsbatch.cob:L19]. Converted once per receiver.
            (
                storage.l4_batch,
                storage.save_batch,
                linkage.batch.ws_batch_key.ws_batch_nos,
            ) = move.move_to_all(
                linkage.posting.ws_post_key.batch,
                (_L4_BATCH, _SAVE_BATCH, _WS_BATCH_NOS),
            )

            # 1018  perform get-a-batch
            # Reads the header of the batch just named. It replaces EVERY field
            # of the batch record, `Actual-Gross` and `Actual-Vat` among them -
            # finding F-7. Harmless only because `end-batch` short-circuits in
            # this very mode [general/gl051.cbl:L1099].
            _get_a_batch(storage, linkage)

            # 1019  move  entered  to  u-bin
            storage.maps03_ws.u_bin = move.move(
                linkage.batch.dates.entered, _U_BIN, sending_field=_ENTERED
            )

            # 1020  perform zz060-Convert-Date
            # AMBIGUITY Q-7: the conversion can mutate `Date-Form`, a
            # `SYSTEM-REC` column, so the returned value is written back.
            linkage.system_record.system_data_block.date_form = _zz060_convert_date(
                storage, linkage.system_record.system_data_block.date_form
            )

            # 1021  move ws-date  to  l4-date        *> presentation only - omitted
            # 1022  move description to l4-desc      *> presentation only - omitted
            # 1023  write  print-record  from  line-4  after  2   *> omitted
            # 1024  add 2 to line-cnt
            storage.line_cnt = arithmetic.add_to(
                2, receiver_value=storage.line_cnt, receiving=_LINE_CNT, rounded=False
            )

        # 1025  else
        # 1026   if      z = 99
        # 1027           then next sentence
        elif arithmetic.compare(storage.z, _Z_ALL_BATCHES) == 0:
            # COBOL's explicit no-op. Written out rather than folded away,
            # because folding it turns a three-way into a two-way: without this
            # arm, an all-batches run whose batch number has NOT changed would
            # fall into the `batch not = WS-Batch-Nos` test below and could skip
            # the posting entirely.
            pass

        # 1028   else
        # 1029     if    batch not = WS-Batch-Nos
        # 1030           go to  loop.
        # GO TO class 1 - loop-back. In single-batch mode every posting outside
        # the batch being proofed is passed over. FINDING F-9: this test is often
        # said to be what the `get-a-batch` sentinel
        # [general/gl051.cbl:L1072] weaponises, and it is NOT - this arm is
        # reachable only when `z not = 99`, and `get-a-batch` is performed only
        # when `z = 99`, so the sentinel never reaches this comparison. See
        # `_get_a_batch`.
        elif (
            arithmetic.compare(
                linkage.posting.ws_post_key.batch,
                linkage.batch.ws_batch_key.ws_batch_nos,
            )
            != 0
        ):
            continue

        # --- the print line  [general/gl051.cbl:L1032-L1052] - PRESENTATION ---
        #
        # 1032  move     post-number  to  l7-number.          *> omitted
        #
        # ANOMALY A-21 [general/gl051.cbl:L1033] - a reference qualified with
        # `in` because `Post-Code` collides across three posting copybooks:
        # `move post-code in WS-Posting-Record to l7-code.` Note the spelling:
        # this site uses `in`, while [general/gl051.cbl:L1044] and
        # [general/gl051.cbl:L1047] use the synonym `of`. In Python the collision
        # cannot arise, so the reproduction is this comment plus record-qualified
        # attribute access wherever such a field IS read - never a bare local.
        # Reproduced deliberately per R-4; DO NOT FIX.
        #
        # 1033  move     post-code in WS-Posting-Record  to  l7-code.   *> omitted
        # 1034  move     post-date    to  l7-date.                      *> omitted

        # 1035  divide   post-dr  by  100  giving  l7-dr.
        # Presentation only: an account held as `nnnnss` shown as `nnnn.ss`. The
        # DIVIDE is reproduced because section 0.4.1.2's census names it, so the
        # truncation into the edited receiver is modelled; the RENDERING is
        # omitted - `cobol/move.py` declines the `zzz9.99b` picture because no
        # database write reaches it and no oracle experiment can observe it
        # (question Q-14). `DIVIDE a BY b GIVING c` means `c = a / b`.
        l7_dr = arithmetic.divide_by_giving(
            linkage.posting.post_dr, _ACCOUNT_SCALE, _L7_DR, rounded=False
        )
        # 1036  move     dr-pc        to  l7-dr-pc.           *> omitted

        # 1037  divide   post-cr  by  100  giving  l7-cr.     *> presentation only
        l7_cr = arithmetic.divide_by_giving(
            linkage.posting.post_cr, _ACCOUNT_SCALE, _L7_CR, rounded=False
        )
        # 1038  move     cr-pc        to  l7-cr-pc.           *> omitted
        # 1039  move     post-amount  to  l7-amount.          *> omitted
        # 1040  move     vat-amount   to  l7-vat.             *> omitted
        # 1041  move     zero         to  l7-vat-ac  l7-vat-pc      *> omitted
        # 1042  move     spaces       to  l7-side.            *> omitted

        # ANOMALY A-21 [general/gl051.cbl:L1044] - the same collision, qualified
        # with `of` this time: `divide vat-ac of WS-Posting-Record by 100 giving
        # l7-vat-ac.` Reproduced deliberately per R-4; DO NOT FIX.
        # 1044  divide   vat-ac of WS-Posting-Record by 100 giving l7-vat-ac.
        l7_vat_ac = arithmetic.divide_by_giving(
            linkage.posting.vat_ac, _ACCOUNT_SCALE, _L7_VAT_AC, rounded=False
        )
        # 1045  move     vat-pc  to  l7-vat-pc.               *> omitted

        # ANOMALY A-21 [general/gl051.cbl:L1047] - the third qualified reference,
        # again with `of`, in a relation condition this time:
        # `if vat-ac of WS-Posting-Record not equal zero move post-vat-side to
        # l7-side.` Its only consequence [general/gl051.cbl:L1048] writes a print
        # field, so the conditional carries no database effect and is recorded in
        # the OMISSIONS list rather than reproduced as an empty `if`.
        # Reproduced deliberately per R-4; DO NOT FIX.
        # 1047  if       vat-ac of WS-Posting-Record not equal  zero
        # 1048           move    post-vat-side  to  l7-side.          *> omitted
        # 1050  move     post-legend  to  l7-legend.                  *> omitted
        # 1052  write    print-record  from  line-7 after 1.          *> omitted
        _LOG.debug(
            "gl051 loop: batch %s posting %s dr %s cr %s vat a/c %s "
            "[general/gl051.cbl:L1032-L1052]",
            linkage.posting.ws_post_key.batch,
            linkage.posting.ws_post_key.post_number,
            l7_dr,
            l7_cr,
            l7_vat_ac,
        )

        # 1053  add      1 to line-cnt.
        storage.line_cnt = arithmetic.add_to(
            1, receiver_value=storage.line_cnt, receiving=_LINE_CNT, rounded=False
        )

        # 1054  perform  get-description.
        # RESOLVES TO [general/gl051.cbl:L1136], the paragraph inside THIS
        # section, and never to the namesake at [general/gl051.cbl:L799] inside
        # the out-of-scope `gl050c section.` - COBOL resolves an unqualified
        # `perform` to the paragraph in the referencing section when one exists
        # there. That resolution is the difference between a two-lookup account
        # check that can reject the batch and an interactive account prompt.
        _batch_print_get_description(storage, linkage)

        # 1056  if       cr-error not = spaces
        # 1057    or     dr-error not = spaces
        # 1058           write print-record from line-error after 1
        # 1059           add 1 to line-cnt.
        # The markers `get-description` has just set are READ BACK here, which is
        # why they are working storage and not locals. The `write` is omitted; the
        # counter increment is not, because `line-cnt` feeds the next test.
        # Both operands are `pic x(12)` and the comparison is alphanumeric, so
        # each is compared against the all-spaces value of its own field as
        # `cobol/move.py` renders it - never against a hand-written literal.
        if storage.cr_error != move.move(
            move.Figurative.SPACE, _CR_ERROR
        ) or storage.dr_error != move.move(move.Figurative.SPACE, _DR_ERROR):
            storage.line_cnt = arithmetic.add_to(
                1, receiver_value=storage.line_cnt, receiving=_LINE_CNT, rounded=False
            )

        # 1060  if       line-cnt > Page-Lines - 6
        # 1061           perform  headings.
        # Arithmetic INSIDE a relation condition: there is no receiving field, so
        # there is nothing to truncate to, and `intermediate` deliberately does
        # not quantize. FINDING F-3: the constant is SIX here and TWELVE at
        # [general/gl051.cbl:L1111] - a deliberate difference, reproduced rather
        # than reconciled.
        page_lines = linkage.system_record.system_data_block.page_lines
        if (
            arithmetic.compare(
                storage.line_cnt,
                arithmetic.intermediate(
                    lambda: page_lines - _PAGE_BREAK_MARGIN_DETAIL
                ),
            )
            > 0
        ):
            _headings(storage, linkage)

        # --- THE ACCUMULATION  [general/gl051.cbl:L1063-L1064] ---
        # The two statements the whole gate depends on. Unconditional, and last.

        # 1063  add      post-amount  to  actual-gross.
        linkage.batch.amounts.actual_gross = arithmetic.add_to(
            linkage.posting.post_amount,
            receiver_value=linkage.batch.amounts.actual_gross,
            receiving=_ACTUAL_GROSS,
            rounded=False,
        )

        # 1064  add      vat-amount   to  actual-vat.
        linkage.batch.amounts.actual_vat = arithmetic.add_to(
            linkage.posting.vat_amount,
            receiver_value=linkage.batch.amounts.actual_vat,
            receiving=_ACTUAL_VAT,
            rounded=False,
        )

        # 1065  go       to loop.
        # GO TO class 1 - loop-back. Unconditional, which is why control never
        # falls out of this paragraph into `get-a-batch.`
        # [general/gl051.cbl:L1067] the way the source's textual order suggests.
        continue


#  get-a-batch.  [general/gl051.cbl:L1067]


def _get_a_batch(storage: _WorkingStorage, linkage: _HandlerLinkage) -> None:
    """`get-a-batch.` - the indexed batch-header read  [general/gl051.cbl:L1067-L1072].

        1067  get-a-batch.
        1070      perform  GL-Batch-Read-Indexed.
        1071      if       fs-reply = 21
        1072               move 99999 to WS-Batch-Nos.

    Three statements, and the third is a trap worth naming. `21` is
    `FsReply.INVALID_KEY_ON_START` - the value this codebase actually returns for
    an indexed read that finds nothing. `FsReply` also defines `KEY_NOT_FOUND`
    at 23, which the data-access analysis records as DOCUMENTED BUT NEVER
    RETURNED, so testing 23 here would test a condition that cannot arise.

    FINDING F-9 - THE SENTINEL IS UNREACHABLE AS A SKIP MECHANISM, and the plan
    and the received wisdom both overstate it. The usual reading is that planting
    99999 in `WS-Batch-Nos` makes the comparison at [general/gl051.cbl:L1029]
    fail for every remaining posting, silently skipping the rest of the batch.
    MEASURED, IT CANNOT: `perform get-a-batch` occurs EXACTLY ONCE in all 1,282
    lines, at [general/gl051.cbl:L1018], inside the arm that requires
    `z = 99` [general/gl051.cbl:L1015] - and in that mode L1029 is never reached,
    because the middle arm [general/gl051.cbl:L1026-L1027] short-circuits with
    `then next sentence`. In the other mode, `z not = 99`, this paragraph is never
    performed at all, so `WS-Batch-Nos` keeps whatever the caller put there. The
    sentinel's only observable effect is therefore the batch number `headings`
    prints [general/gl051.cbl:L1079]. Both facts are reproduced exactly as
    written; neither is corrected, and the reachability finding is recorded rather
    than acted on. There is no `else`, so on success `WS-Batch-Nos` keeps the
    batch number the caller just moved in.

    REACHED ONLY FROM THE `z = 99` BRANCH [general/gl051.cbl:L1018], which is also
    why finding F-7's accumulator clobber is harmless: this read replaces every
    field of the batch record including `Actual-Gross` and `Actual-Vat`, but the
    mode that performs it is the mode `end-batch` short-circuits.

    NO `else`, NO ERROR PATH, NO DIAGNOSTIC. Adding any of the three would be a
    new validation, which rule R-3 forbids.

    Args:
        storage: Unused by this paragraph's three statements; accepted so every
            in-scope paragraph has one shape. Its `save_batch` was set by the
            caller's `MOVE` at [general/gl051.cbl:L1017].
        linkage: Supplies the batch record the read fills and the reply it sets.
    """
    # 1070  perform  GL-Batch-Read-Indexed.   *> read batch-file invalid key
    _gl_batch_read_indexed(linkage)

    # 1071  if       fs-reply = 21
    if linkage.file_access.fs_reply == FsReply.INVALID_KEY_ON_START:
        # 1072  move 99999 to WS-Batch-Nos.
        linkage.batch.ws_batch_key.ws_batch_nos = move.move(
            _BATCH_NOT_FOUND_SENTINEL, _WS_BATCH_NOS
        )
        _LOG.debug(
            "gl051 get-a-batch: batch header not found, WS-Batch-Nos set to the "
            "%s sentinel [general/gl051.cbl:L1072]; the remaining postings of "
            "this batch are skipped silently",
            _BATCH_NOT_FOUND_SENTINEL,
        )
    _ = storage


#  headings.  [general/gl051.cbl:L1074]


def _headings(storage: _WorkingStorage, linkage: _HandlerLinkage) -> None:
    """`headings.` - the page headings  [general/gl051.cbl:L1074-L1094].

        1077      add      1          to  page-nos.
        1078      move     page-nos   to  l1-page.
        1079      move     WS-Batch-Nos  to  l4-batch.
        1080      move     description  to  l4-desc.
        1081      move     entered  to  u-bin.
        1082      perform  zz060-Convert-Date.
        1083      move     ws-date  to  l4-date.
        1085      write    print-record  from  line-1 after 1.
        1086      write    print-record  from  line-3 after 1.
        1087      move     6 to line-cnt.
        1088      if       z not = 99
        1089               write  print-record  from  line-4 after 2
        1090               add 2 to line-cnt.
        1091      write    print-record  from  line-5 after 2.
        1092      write    print-record  from  line-6 after 1.
        1093      move     spaces  to  print-record.
        1094      write    print-record after 1.

    PRESENTATION FROM END TO END, AND YET THREE OF ITS EFFECTS SURVIVE THE
    MIGRATION:

      * [general/gl051.cbl:L1082] performs `zz060`, which reaches the date module
        AND can mutate `Date-Form` on the system record - question Q-7. Dropping
        the call because its output is only printed would lose a database effect.
      * [general/gl051.cbl:L1087] RESETS `line-cnt` to six and
        [general/gl051.cbl:L1090] adds two more when `z not = 99`. The counter
        feeds the page-break tests at [general/gl051.cbl:L1060] and
        [general/gl051.cbl:L1111], each of which can perform this paragraph
        again - question Q-8. Note the reset is a `MOVE`, not an addition, so
        this is where the count starts over.
      * [general/gl051.cbl:L1077] advances `page-nos`, which nothing else writes.

    Everything else - the seven `write print-record` statements, the print-line
    fields they are built from, and `l1-page`, `l4-desc` and `l4-date` - is
    report formatting with no database effect, out of scope by section 0.2.2 and
    recorded in the OMISSIONS list. `l4-batch` [general/gl051.cbl:L1079] IS
    reproduced, because it is also a receiver of the three-receiver `MOVE` in
    `loop` and so outlives this paragraph.

    Args:
        storage: Receives `page-nos`, `line-cnt`, `l4-batch` and the converted
            date; supplies `z`.
        linkage: Supplies `WS-Batch-Nos` and the batch header's `Entered` date,
            and carries the system record whose `Date-Form` may be mutated.
    """
    # 1077  add      1          to  page-nos.
    storage.page_nos = arithmetic.add_to(
        1, receiver_value=storage.page_nos, receiving=_PAGE_NOS, rounded=False
    )

    # 1078  move     page-nos   to  l1-page.        *> presentation only - omitted
    # 1079  move     WS-Batch-Nos  to  l4-batch.
    storage.l4_batch = move.move(
        linkage.batch.ws_batch_key.ws_batch_nos,
        _L4_BATCH,
        sending_field=_WS_BATCH_NOS,
    )
    # 1080  move     description  to  l4-desc.      *> presentation only - omitted

    # 1081  move     entered  to  u-bin.
    storage.maps03_ws.u_bin = move.move(
        linkage.batch.dates.entered, _U_BIN, sending_field=_ENTERED
    )

    # 1082  perform  zz060-Convert-Date.
    # AMBIGUITY Q-7: `zz060` mutates `Date-Form` when it is zero, and `Date-Form`
    # is a `SYSTEM-REC` column, so the returned value is written back rather than
    # discarded.
    linkage.system_record.system_data_block.date_form = _zz060_convert_date(
        storage, linkage.system_record.system_data_block.date_form
    )

    # 1083  move     ws-date  to  l4-date.          *> presentation only - omitted
    # 1085  write    print-record  from  line-1 after 1.
    # 1086  write    print-record  from  line-3 after 1.
    _LOG.debug(
        "gl051 headings: page %s, batch %s [general/gl051.cbl:L1074-L1094]",
        storage.page_nos,
        storage.l4_batch,
    )

    # 1087  move     6 to line-cnt.
    storage.line_cnt = move.move(_HEADING_LINE_COUNT, _LINE_CNT)

    # 1088  if       z not = 99
    if arithmetic.compare(storage.z, _Z_ALL_BATCHES) != 0:
        # 1089  write  print-record  from  line-4 after 2   *> presentation only
        # 1090  add 2 to line-cnt.
        storage.line_cnt = arithmetic.add_to(
            2, receiver_value=storage.line_cnt, receiving=_LINE_CNT, rounded=False
        )

    # 1091-1094  four more `write print-record` statements  *> presentation only


#  end-batch.  [general/gl051.cbl:L1096]
#  ***  THE CONTROL-TOTAL GATE  ***
#  The reason this module exists, and the reason the Agent Action Plan's cited
#  boundary [general/gl051.cbl:L1096-L1133] points here and nowhere else.


def _end_batch(storage: _WorkingStorage, linkage: _HandlerLinkage) -> None:
    """`end-batch.` - THE CONTROL-TOTAL GATE  [general/gl051.cbl:L1096-L1134].

        1099      if       z = 99
        1100               go to  main-exit.
        1101      if       not truet
        1102               move  0  to  batch-status
        1103               go to  main-exit.
        1105      subtract input-vat  from  input-gross  giving  l9-amount.
        1106      move     input-vat    to  l9-vat.
        1107      move     actual-gross to  l10-amount.
        1108      move     actual-vat   to  l10-vat.
        1109      add      actual-vat   to  actual-gross.
        1111      if       line-cnt > Page-Lines - 12
        1112               perform headings.
        1113      write    print-record  from  line-8 after 3.
        1114      write    print-record  from  line-9 after 2.
        1115      write    print-record  from  line-10 after 2.
        1117      if       input-gross = actual-gross
        1118        and    input-vat   = actual-vat
        1119               move  1  to  batch-status
        1120      else
        1121               move  0  to  batch-status.
        1123      move     "*********************"  to  l11-status.
        1124      write    print-record  from  line-11 after 3.
        1126      if       batch-status = 1
        1127               move  "* Batch Verified Ok *"  to  l11-status
        1128      else
        1129               move  "*  Batch In ERROR   *"  to  l11-status.
        1131      write    print-record  from  line-11 after 1.
        1132      move     "*********************"  to  l11-status.
        1133      write    print-record  from  line-11 after 1.
        1134      go       to main-exit.

    VAT ENTERS THE TOTAL BEFORE THE COMPARISON, AND THAT IS THE SINGLE MOST
    IMPORTANT ORDERING FACT IN THIS MODULE. [general/gl051.cbl:L1109] mutates
    `actual-gross` in place, and only then does [general/gl051.cbl:L1117] test it
    against `input-gross`. Section 0.6.4, verbatim: "the entered figure is
    VAT-inclusive. Reversing these two steps would reject every batch that
    carries VAT."

    THREE WAYS OUT, ALL CLASS 3, AND THEY DIFFER IN THEIR DATABASE EFFECT - which
    is exactly the distinction section 0.6.5 requires be preserved:

      * [general/gl051.cbl:L1100], reached when `z = 99`. `Batch-Status` IS NEVER
        TOUCHED. A clean rejection with NO database effect: in all-batches proof
        mode the report is produced and no batch is accepted or rejected. This is
        also why the accumulator clobber at [general/gl051.cbl:L1018] is harmless
        - finding F-7.
      * [general/gl051.cbl:L1103], reached when `trutht` has been cleared. Sets
        `Batch-Status` to zero and returns BEFORE COMPARING ANYTHING. A rejection
        WITH a database effect, and the only path by which a batch whose figures
        agree perfectly is still rejected: `get-description`
        [general/gl051.cbl:L1150] and [general/gl051.cbl:L1164] found a posting
        naming a nominal account that does not exist.
      * [general/gl051.cbl:L1134], the normal end, after the comparison has set
        the status one way or the other.

    THE GATE IS A TWO-CONDITION `AND`. Gross AND VAT must both agree; either
    alone is not enough. All four operands are `pic 9(9)v99 comp-3` and UNSIGNED
    [copybooks/wsbatch.cob:L41-L44], and COBOL compares numerics ALGEBRAICALLY,
    so a two-place value equals a numerically equal value held at any other
    scale. The comparison therefore goes through `cobol/arithmetic.py`; a
    `Decimal.__eq__` on raw attributes, or worse a string comparison, would be a
    different test.

    `Batch-Status` SEMANTICS ARE INVERTED FROM WHAT THE LITERALS SUGGEST.
    `03 Batch-Status pic 9.` carries `88 Status-Open value 0.`
    [copybooks/wsbatch.cob:L26] and `88 Status-Closed value 1.`
    [copybooks/wsbatch.cob:L27]. So `move 1` means CLOSED, hence accepted, and
    `move 0` means OPEN, hence rejected - and leaving a batch OPEN is precisely
    what the next program in the cycle looks for.

    THIS PARAGRAPH IS LINK ZERO OF THE FOUR-LINK ABORT CHAIN. A rejection here
    leaves `Status-Open`; `gl070`'s batch check finds it - `if status-open move 1
    to a.` [general/gl070.cbl:L314-L315] - and raises the terminate code,
    `move 5 to ws-term-code` [general/gl070.cbl:L289]; the menu tests that code,
    `if ws-term-code = 5 go to display-menu.` [general/general.cbl:L810-L811];
    and so `gl071` [general/general.cbl:L812] and `gl072`
    [general/general.cbl:L814] NEVER RUN. The expected database state for a
    control-total mismatch is therefore the ABSENCE of everything the later
    phases would have written - section 0.6.5's "run-aborting rejection" class.
    Section 0.6.4 adds that this scenario is General-Ledger-specific: "Sales and
    Purchase batches balance by construction."

    NOTHING HERE PERSISTS THE STATUS. `Batch-Status` is set on the in-memory
    batch record and that is all: the two `GL-Batch-Rewrite` calls that write it
    back are at [general/gl051.cbl:L415] and [general/gl051.cbl:L491], both
    outside the boundary. Question Q-1.

    FINDING F-3: the page-break margin is TWELVE here [general/gl051.cbl:L1111]
    and SIX in `loop` [general/gl051.cbl:L1060]. Twelve guards the three
    multi-line total blocks about to be written. Both are reproduced as written.

    Everything from [general/gl051.cbl:L1105] to [general/gl051.cbl:L1108], and
    [general/gl051.cbl:L1113] to [general/gl051.cbl:L1133] except the gate
    itself, is report formatting with no database effect and is recorded in the
    OMISSIONS list. The `SUBTRACT ... GIVING` at [general/gl051.cbl:L1105] is
    reproduced anyway because section 0.4.1.2's census names it.

    Args:
        storage: Supplies `z`, `trutht` and `line-cnt`.
        linkage: Supplies the four control-total fields and `Page-Lines`;
            receives `Batch-Status` and the mutated `Actual-Gross`.
    """
    amounts: BatchAmounts = linkage.batch.amounts

    # 1099  if       z = 99
    # 1100           go to  main-exit.
    # GO TO class 3 - section exit. `Batch-Status` IS DELIBERATELY NOT SET: a
    # clean rejection with no database effect. There is no `else`.
    if arithmetic.compare(storage.z, _Z_ALL_BATCHES) == 0:
        _LOG.debug(
            "gl051 end-batch: all-batches proof mode, the gate is skipped and "
            "Batch-Status is left untouched [general/gl051.cbl:L1099-L1100]"
        )
        return

    # 1101  if       not truet
    # 1102           move  0  to  batch-status
    # 1103           go to  main-exit.
    # THE ACCOUNT-EXISTENCE REJECTION, and it happens BEFORE any total is
    # compared. `88 truet value 1.` [general/gl051.cbl:L177] is declared on
    # `gl051`'s own working storage rather than in a copybook, so its value comes
    # from `_TRUET_VALUE` and the comparison from `cobol/arithmetic.py`. Zero is
    # `88 Status-Open value 0.` - rejected.
    # GO TO class 3 - section exit.
    if arithmetic.compare(storage.trutht, _TRUET_VALUE) != 0:
        linkage.batch.batch_status = move.move(
            values_for("Status-Open")[0], _BATCH_STATUS
        )
        _LOG.info(
            "gl051 end-batch: batch %s REJECTED because a posting named a "
            "nominal account that does not exist - Batch-Status left "
            "Status-Open, no total compared [general/gl051.cbl:L1101-L1103]",
            linkage.batch.ws_batch_key.ws_batch_nos,
        )
        return

    # 1105  subtract input-vat  from  input-gross  giving  l9-amount.
    # `SUBTRACT a FROM b GIVING c` means `c = b - a`, so this is the net of VAT
    # the operator entered. Presentation only; reproduced because the census
    # names it, rendering omitted (question Q-14).
    l9_amount = arithmetic.subtract_giving(
        amounts.input_vat,
        minuend=amounts.input_gross,
        receiving=_L9_AMOUNT,
        rounded=False,
    )
    # 1106  move     input-vat    to  l9-vat.        *> presentation only - omitted
    # 1107  move     actual-gross to  l10-amount.    *> presentation only - omitted
    # 1108  move     actual-vat   to  l10-vat.       *> presentation only - omitted
    # The three moves above are why [general/gl051.cbl:L1109] can mutate
    # `actual-gross` without disturbing the report: the printed figures were
    # captured first.

    # 1109  add      actual-vat   to  actual-gross.
    # ***  VAT ENTERS THE CONTROL TOTAL, AND IT DOES SO BEFORE THE TEST.  ***
    # Section 0.6.4, verbatim: "the entered figure is VAT-inclusive. Reversing
    # these two steps would reject every batch that carries VAT." An in-place
    # mutation of an UNSIGNED `pic 9(9)v99 comp-3` receiver, un-`ROUNDED` and so
    # truncating.
    amounts.actual_gross = arithmetic.add_to(
        amounts.actual_vat,
        receiver_value=amounts.actual_gross,
        receiving=_ACTUAL_GROSS,
        rounded=False,
    )

    # 1111  if       line-cnt > Page-Lines - 12
    # 1112           perform headings.
    # FINDING F-3: TWELVE here against SIX at [general/gl051.cbl:L1060]. No
    # receiving field, so `intermediate` does not quantize.
    page_lines = linkage.system_record.system_data_block.page_lines
    if (
        arithmetic.compare(
            storage.line_cnt,
            arithmetic.intermediate(lambda: page_lines - _PAGE_BREAK_MARGIN_TOTALS),
        )
        > 0
    ):
        _headings(storage, linkage)

    # 1113  write    print-record  from  line-8 after 3.    *> omitted
    # 1114  write    print-record  from  line-9 after 2.    *> omitted
    # 1115  write    print-record  from  line-10 after 2.   *> omitted
    _LOG.debug(
        "gl051 end-batch: entered gross %s vat %s net %s, actual gross %s "
        "vat %s [general/gl051.cbl:L1105-L1115]",
        amounts.input_gross,
        amounts.input_vat,
        l9_amount,
        amounts.actual_gross,
        amounts.actual_vat,
    )

    # 1117  if       input-gross = actual-gross
    # 1118    and    input-vat   = actual-vat
    # 1119           move  1  to  batch-status
    # 1120  else
    # 1121           move  0  to  batch-status.
    # ***  THE GATE.  ***  Two conditions, both required. One is
    # `88 Status-Closed value 1.` - accepted; zero is `88 Status-Open value 0.` -
    # rejected, and an open batch is what aborts the rest of the posting cycle.
    if (
        arithmetic.compare(amounts.input_gross, amounts.actual_gross) == 0
        and arithmetic.compare(amounts.input_vat, amounts.actual_vat) == 0
    ):
        linkage.batch.batch_status = move.move(
            values_for("Status-Closed")[0], _BATCH_STATUS
        )
    else:
        linkage.batch.batch_status = move.move(
            values_for("Status-Open")[0], _BATCH_STATUS
        )
        _LOG.info(
            "gl051 end-batch: batch %s REJECTED on control totals - %s %s "
            "against %s %s, and %s %s against %s %s "
            "[general/gl051.cbl:L1117-L1121]",
            linkage.batch.ws_batch_key.ws_batch_nos,
            _INPUT_GROSS.name,
            amounts.input_gross,
            _ACTUAL_GROSS.name,
            amounts.actual_gross,
            _INPUT_VAT.name,
            amounts.input_vat,
            _ACTUAL_VAT.name,
            amounts.actual_vat,
        )

    # 1123  move     "*********************"  to  l11-status.   *> omitted
    # 1124  write    print-record  from  line-11 after 3.        *> omitted

    # 1126  if       batch-status = 1
    # 1127           move  "* Batch Verified Ok *"  to  l11-status
    # 1128  else
    # 1129           move  "*  Batch In ERROR   *"  to  l11-status.
    # The status is READ BACK to choose the banner - print only, and worth keeping
    # as a log record because it is the operator-visible verdict. `= 1` is
    # `88 Status-Closed`, so the test goes through the condition-name vocabulary.
    if is_status_closed(linkage.batch.batch_status):
        _LOG.info(
            "gl051 end-batch: batch %s verified ok, Batch-Status Status-Closed "
            "[general/gl051.cbl:L1126-L1127]",
            linkage.batch.ws_batch_key.ws_batch_nos,
        )
    else:
        _LOG.info(
            "gl051 end-batch: batch %s in error, Batch-Status Status-Open "
            "[general/gl051.cbl:L1128-L1129]",
            linkage.batch.ws_batch_key.ws_batch_nos,
        )

    # 1131  write    print-record  from  line-11 after 1.        *> omitted
    # 1132  move     "*********************"  to  l11-status.    *> omitted
    # 1133  write    print-record  from  line-11 after 1.        *> omitted

    # 1134  go       to main-exit.
    # GO TO class 3 - section exit. The third and last of this paragraph's exits.
    return


#  get-description.  [general/gl051.cbl:L1136]
#  SECTION-QUALIFIED. `general/gl051.cbl` declares TWO paragraphs named
#  `get-description.` - one at [general/gl051.cbl:L799], inside the OUT-OF-SCOPE
#  `gl050c section.`, and this one at [general/gl051.cbl:L1136], inside
#  `batch-print`. COBOL resolves a `perform` to the paragraph in the SAME section
#  as the reference when one exists there, so `perform get-description` at
#  [general/gl051.cbl:L1054] reaches THIS paragraph and never the L799 one. The
#  name carries the section prefix so that no reader has to reconstruct that rule.


def _batch_print_get_description(
    storage: _WorkingStorage, linkage: _HandlerLinkage
) -> None:
    """`get-description.` - the DR/CR existence check  [general/gl051.cbl:L1136-L1164].

        1138      move     zero         to  we-error.
        1139      move     post-dr      to  WS-Ledger-Nos.
        1140      move     dr-pc        to  ledger-pc.
        1142      perform  GL-Nominal-Read-Indexed.
        1143      if       fs-reply = 21
        1144               move  1  to  we-error.
        1146      if       we-error = zero
        1147               move  spaces  to  dr-error
        1148      else
        1149               move  "^^^^^^^^^^"  to  dr-error
        1150               move  0  to  trutht.
        1152      move     zero         to  we-error.
        1153      move     post-cr      to  WS-Ledger-Nos.
        1154      move     cr-pc        to  ledger-pc.
        1156      perform  GL-Nominal-Read-Indexed.
        1157      if       fs-reply = 21
        1158               move  1  to  we-error.
        1160      if       we-error = zero
        1161               move  spaces  to  cr-error
        1162      else
        1163               move  "^^^^^^^^^^"  to  cr-error
        1164               move  0  to  trutht.

    THIS PARAGRAPH IS THE WHOLE REJECTION PATH, and it is invisible from the line
    range the Agent Action Plan cites. Two independent indexed lookups - the
    debit account, then the credit - each preceded by its own
    `move zero to we-error` and each testing `fs-reply = 21`. On either failure it
    writes a print marker AND clears `trutht`. Those two `move 0 to trutht`
    statements, [general/gl051.cbl:L1150] and [general/gl051.cbl:L1164], are the
    ONLY in-scope writers of that flag and they only ever clear it. Together with
    `move 1 to trutht` [general/gl051.cbl:L967] outside the boundary the meaning
    is: the batch is valid unless some posting names a nominal account that does
    not exist. `end-batch` [general/gl051.cbl:L1101] then rejects it BEFORE
    comparing any total, so a bad account rejects a batch whose figures agree
    perfectly.

    SYMMETRY IS EXACT AND DELIBERATE. The credit half is the debit half with
    `post-cr`/`cr-pc`/`cr-error` substituted. It is written out twice rather than
    folded into a loop because the two halves are two separate statement
    sequences in the source and because `we-error` is re-zeroed between them -
    which is what makes them independent: a debit failure does not mask a credit
    success, and neither can un-clear `trutht`.

    `we-error` IS A LOCAL FLAG HERE, NOT A HANDLER CODE. It is the same
    `We-Error pic 999` field [copybooks/wsfnctn.cob:L23-L38] the file handlers
    write their diagnostics into, but this paragraph uses it as plain 0-or-1:
    literal `1` at [general/gl051.cbl:L1144] and [general/gl051.cbl:L1158], zero
    at [general/gl051.cbl:L1138] and [general/gl051.cbl:L1152]. A reader arriving
    from `gl072` will expect the handler vocabulary - in particular the 999
    sentinel `gl072` tests at [general/gl072.cbl:L303-L304] - and NONE OF IT
    APPLIES HERE. Nothing below compares `we-error` against a handler code.
    Finding F-5 records that the out-of-scope namesake at
    [general/gl051.cbl:L799] uses 255 for the same purpose.

    THE PRINT MARKERS ARE NOT PURELY PRESENTATION. `dr-error` and `cr-error` look
    like report decoration and are read back by `loop`
    [general/gl051.cbl:L1056-L1057] to decide whether to write an extra line and
    advance `line-cnt`, which feeds the page-break test. So both are reproduced -
    question Q-8.

    NO DIAGNOSTIC BEYOND THE MARKER. The out-of-scope namesake displays "Invalid
    A/C number" on the screen [general/gl051.cbl:L814]; this one displays nothing
    at all. Adding a message would be new behaviour under rule R-3.

    FALL-THROUGH. The paragraph ends at [general/gl051.cbl:L1164] with NO `GO TO`,
    and the next label in the file is `main-exit.   exit section.`
    [general/gl051.cbl:L1166]. Control never actually falls there, because the
    paragraph is only ever reached by `perform` from [general/gl051.cbl:L1054] and
    a `PERFORM` of a paragraph returns at that paragraph's end - so this function
    returns to `_loop`. Both facts are stated because the textual adjacency is
    what a reader sees first.

    Args:
        storage: Receives `dr-error`, `cr-error` and `trutht`.
        linkage: Supplies the posting's four account fields, receives the nominal
            key, and carries the `File-Access` block whose `We-Error` and
            `Fs-Reply` this paragraph writes and tests.
    """
    posting = linkage.posting
    ledger_key: WsLedgerKey = linkage.ledger.ws_ledger_key

    # --- the debit account  [general/gl051.cbl:L1138-L1150] ---

    # 1138  move     zero         to  we-error.
    # A LOCAL 0-or-1 FLAG, not a handler code - see the docstring. Deliberately
    # NOT compared against any `WeError` member anywhere below.
    linkage.file_access.we_error = move.move(move.Figurative.ZERO, _WE_ERROR)

    # 1139  move     post-dr      to  WS-Ledger-Nos.
    ledger_key.ws_ledger_nos = move.move(
        posting.post_dr, _WS_LEDGER_NOS, sending_field=_POST_DR
    )
    # 1140  move     dr-pc        to  ledger-pc.
    ledger_key.ledger_pc = move.move(posting.dr_pc, _LEDGER_PC, sending_field=_DR_PC)

    # 1142  perform  GL-Nominal-Read-Indexed.   *> read ledger-file invalid key
    _gl_nominal_read_indexed(linkage)

    # 1143  if       fs-reply = 21
    if linkage.file_access.fs_reply == FsReply.INVALID_KEY_ON_START:
        # 1144  move  1  to  we-error.
        linkage.file_access.we_error = move.move(_WE_ERROR_LOCAL_FAILURE, _WE_ERROR)

    # 1146  if       we-error = zero
    if arithmetic.compare(linkage.file_access.we_error, 0) == 0:
        # 1147  move  spaces  to  dr-error
        storage.dr_error = move.move(move.Figurative.SPACE, _DR_ERROR)
    else:
        # 1149  move  "^^^^^^^^^^"  to  dr-error
        storage.dr_error = move.move(_ACCOUNT_ERROR_MARKER, _DR_ERROR)
        # 1150  move  0  to  trutht.
        # ONE OF THE TWO IN-SCOPE WRITERS OF `trutht`, AND IT ONLY CLEARS.
        # `end-batch` [general/gl051.cbl:L1101] rejects the batch on this.
        storage.trutht = move.move(_FALSET_VALUE, _TRUTHT)
        _LOG.debug(
            "gl051 get-description: debit account %s pc %s not on the nominal "
            "ledger, trutht cleared [general/gl051.cbl:L1149-L1150]",
            ledger_key.ws_ledger_nos,
            ledger_key.ledger_pc,
        )

    # --- the credit account  [general/gl051.cbl:L1152-L1164] ---

    # 1152  move     zero         to  we-error.
    # Re-zeroed, which is what makes the two halves independent.
    linkage.file_access.we_error = move.move(move.Figurative.ZERO, _WE_ERROR)

    # 1153  move     post-cr      to  WS-Ledger-Nos.
    ledger_key.ws_ledger_nos = move.move(
        posting.post_cr, _WS_LEDGER_NOS, sending_field=_POST_CR
    )
    # 1154  move     cr-pc        to  ledger-pc.
    ledger_key.ledger_pc = move.move(posting.cr_pc, _LEDGER_PC, sending_field=_CR_PC)

    # 1156  perform  GL-Nominal-Read-Indexed.   *> read ledger-file invalid key
    _gl_nominal_read_indexed(linkage)

    # 1157  if       fs-reply = 21
    if linkage.file_access.fs_reply == FsReply.INVALID_KEY_ON_START:
        # 1158  move  1  to  we-error.
        linkage.file_access.we_error = move.move(_WE_ERROR_LOCAL_FAILURE, _WE_ERROR)

    # 1160  if       we-error = zero
    if arithmetic.compare(linkage.file_access.we_error, 0) == 0:
        # 1161  move  spaces  to  cr-error
        storage.cr_error = move.move(move.Figurative.SPACE, _CR_ERROR)
    else:
        # 1163  move  "^^^^^^^^^^"  to  cr-error
        storage.cr_error = move.move(_ACCOUNT_ERROR_MARKER, _CR_ERROR)
        # 1164  move  0  to  trutht.
        # THE SECOND AND LAST IN-SCOPE WRITER OF `trutht`, and it also only
        # clears. There is no path in the boundary that sets it back to one.
        storage.trutht = move.move(_FALSET_VALUE, _TRUTHT)
        _LOG.debug(
            "gl051 get-description: credit account %s pc %s not on the nominal "
            "ledger, trutht cleared [general/gl051.cbl:L1163-L1164]",
            ledger_key.ws_ledger_nos,
            ledger_key.ledger_pc,
        )

    # 1164 is the paragraph's last statement and there is no `GO TO`; the
    # `perform` at [general/gl051.cbl:L1054] returns here. See the docstring on
    # the textual fall-through into `main-exit.` [general/gl051.cbl:L1166].


#  main-exit.  [general/gl051.cbl:L1166]
#  SECTION-QUALIFIED. `general/gl051.cbl` declares THREE paragraphs named
#  `main-exit.` - [general/gl051.cbl:L816] in the out-of-scope `gl050c section.`,
#  [general/gl051.cbl:L985] in the out-of-scope `gl050d section.`, and this one at
#  [general/gl051.cbl:L1166] in `batch-print`. Only the third is in scope, and
#  only the third is a bare terminator: the `gl050d` namesake closes the print
#  file and both ledger files [general/gl051.cbl:L988-L990] and spools the report
#  [general/gl051.cbl:L991]. Confusing them would smuggle three file closes and a
#  `call "SYSTEM"` into the boundary.


def _batch_print_main_exit() -> None:
    """`main-exit.` - the section terminator  [general/gl051.cbl:L1166].

        1166  main-exit.   exit section.

    ONE STATEMENT, AND IT IS `exit section.` - nothing is closed, nothing is
    written, nothing is computed. It exists as a function because rule R-5 asks
    for a named function per paragraph and section 0.7.4 C-4 is explicit,
    verbatim: "every paragraph retains a named function even where its `GO TO`
    becomes a `continue`, a `break` or a `return`." Three `GO TO`s target it -
    [general/gl051.cbl:L1100], [general/gl051.cbl:L1103] and
    [general/gl051.cbl:L1134], all class 3 - and `_end_batch` reproduces each as
    a `return`, so by the time this runs the transfers have already happened.
    `_batch_print` calls it unconditionally, because a COBOL section cannot end
    any other way.

    It takes no arguments because the COBOL paragraph reads nothing.
    """
    _LOG.debug("gl051 batch-print: exit section [general/gl051.cbl:L1166]")


# ---------------------------------------------------------------------------
#  The program entry point
# ---------------------------------------------------------------------------


def run(
    ws_calling_data: WsCallingData,
    system_record: SystemRecord,
    to_day: str,
    file_defs: FileDefs,
    *,
    posting: WsPostingRecord | None = None,
    batch: GlBatchRecord | None = None,
    ledger: WsLedgerRecord | None = None,
    file_access: FileAccess | None = None,
    dal_common: AcasDalCommonData | None = None,
    z: int = 0,
    trutht: int = _TRUET_VALUE,
    actual_gross: decimal.Decimal | int = 0,
    actual_vat: decimal.Decimal | int = 0,
) -> None:
    """Run `gl051`'s batch control-total gate - `batch-print section.` and nothing else.

    THE LINKAGE, VERBATIM  [general/gl051.cbl:L353-L356]:

        procedure division using ws-calling-data
                                 system-record
                                 to-day
                                 file-defs.

    Four positional parameters in that order - the General Ledger shape, shared
    with `gl070`, `gl071`, `gl072` and `gl080`, and distinct both from the Sales
    and Purchase shape, which adds a fourth system record, and from the IRS
    shape, which drops the calling-data block and the run date entirely.

    WHAT THIS FUNCTION DELIVERS IS ONE FIELD: `Batch-Status` on the batch record
    passed in. `batch-print` performs exactly three file-handler verbs and every
    one of them is a READ - `GL-Posting-Read-Next` [general/gl051.cbl:L1008],
    `GL-Batch-Read-Indexed` [general/gl051.cbl:L1070] and
    `GL-Nominal-Read-Indexed` [general/gl051.cbl:L1142] and
    [general/gl051.cbl:L1156]. There is no write, no rewrite, no delete, no open
    and no close inside the boundary, so THE IN-SCOPE MODULE PERFORMS ZERO
    DATABASE MUTATIONS. Persisting the status is the caller's, through the two
    `GL-Batch-Rewrite` calls at [general/gl051.cbl:L415] and
    [general/gl051.cbl:L491] - question Q-1.

    THE KEYWORD-ONLY PARAMETERS ARE NOT AN INVENTION; THEY ARE THE BOUNDARY MADE
    HONEST. `batch-print` is performed from `gl050d`
    [general/gl051.cbl:L983], and `gl050d` sets up four things first that the
    gate is meaningless without. Each is promoted to a parameter defaulting to
    the value the COBOL gives it, and each is an oracle question:

      * `trutht` - `move 1 to trutht.` [general/gl051.cbl:L967]. The batch starts
        VALID. Inside the boundary the flag is only ever cleared, so without this
        one the account-existence rejection could never fire. Question Q-4.
      * `actual_gross`, `actual_vat` - `move zero to actual-gross actual-vat.`
        [general/gl051.cbl:L982]. Both accumulators start at ZERO. Without this
        the gate compares against whatever the batch header happened to hold.
        Question Q-4.
      * `z` - `03 z pic 99.` [general/gl051.cbl:L172], written only by
        out-of-scope interactive code and tested four times in scope, at
        [general/gl051.cbl:L1015], [general/gl051.cbl:L1026],
        [general/gl051.cbl:L1088] and [general/gl051.cbl:L1099]. Defaulted to
        zero - single-batch mode, the mode in which the gate actually runs -
        because 99 short-circuits it. Question Q-5.
      * The five handler-call records default to freshly constructed instances so
        a caller that has no state to carry in need not build them, exactly as
        COBOL's `VALUE` clauses initialise working storage at load time.

    THE FILES ARE ALREADY OPEN ON ENTRY. `perform GL-Nominal-Open-Input.`
    [general/gl051.cbl:L980] and `perform GL-Posting-Open-Input.`
    [general/gl051.cbl:L981] are `gl050d`'s, immediately before the `perform` -
    and so are the closes [general/gl051.cbl:L989-L990]. They are documented
    preconditions and postconditions, not code, because reproducing them here
    would add two opens and two closes the boundary does not contain.

    WHAT IS NOT MIGRATED. `general/gl051.cbl` is 1,282 lines and this module
    covers roughly 170 of them. `gl051-Main section.` [general/gl051.cbl:L359],
    `proof-all section.` [general/gl051.cbl:L474], `gl050c section.`
    [general/gl051.cbl:L496], `batch-amendment section.` [general/gl051.cbl:L825]
    and `gl050d section.` [general/gl051.cbl:L961] are OUT OF SCOPE in their
    entirety, along with every screen section, every `accept` loop and every
    amendment dialog. The traceability footer names each one. Section 0.8.7,
    verbatim: "an agent working from the file rather than from the stated
    boundary would migrate several hundred lines that must not be migrated."

    DETERMINISM. Nothing here reads a clock. `general/gl051.cbl` contains ZERO
    clock reads: the date arrives through `to_day` [general/gl051.cbl:L351] and
    through `Run-Date` on the system record [copybooks/wssystem.cob:L67], both
    supplied by the caller. The controlled-clock module `acas_posting/clock.py`
    is deliberately NOT imported, because a program that cannot reach a clock
    cannot be made non-deterministic by one.

    Args:
        ws_calling_data: `01 WS-Calling-Data.` [copybooks/wscall.cob:L6-L13],
            linkage parameter one. No field of it is read or written inside the
            boundary - the term code that aborts the cycle is `gl070`'s
            [general/gl070.cbl:L289], not this program's - and it is accepted
            because the `PROCEDURE DIVISION USING` list declares it.
        system_record: `SYSTEM-REC` [general/gl051.cbl:L348], linkage parameter
            two. Supplies `Page-Lines` for the two page-break tests and
            `Date-Form`, which the date sections MUTATE when it is zero -
            question Q-7. Forwarded to every handler call as its first argument.
        to_day: `01 to-day pic x(10).` [general/gl051.cbl:L351], linkage
            parameter three - the run date in DD/MM/CCYY form. `batch-print`
            itself never reads it; `zz070-Convert-Date`
            [general/gl051.cbl:L1251] does, and that section is in scope as a
            delegation, so the parameter is bound and passed on rather than
            ignored.
        file_defs: `01 File-Defs.` [general/gl051.cbl:L349], linkage parameter
            four. Forwarded to every handler call unread, exactly as the facade
            copybook forwards it.
        posting: `01 WS-Posting-Record.` [general/gl051.cbl:L132] - the buffer
            `GL-Posting-Read-Next` fills.
        batch: `01 WS-Batch-Record.` [general/gl051.cbl:L131] - the source of the
            control totals AND the destination of `Batch-Status`. THE OUTPUT OF
            THIS FUNCTION IS A FIELD OF THIS RECORD.
        ledger: `01 WS-Ledger-Record.` [general/gl051.cbl:L130] - the buffer both
            `GL-Nominal-Read-Indexed` calls fill.
        file_access: `01 File-Access.` [copybooks/wsfnctn.cob:L23-L38] - carries
            `Fs-Reply`, tested after every verb, and `We-Error`, used by
            `get-description` as a local 0-or-1 flag.
        dal_common: `01 ACAS-DAL-Common-Data.` from `copy "Test-Data-Flags.cob"`
            [general/gl051.cbl:L158] - the logging switch, the fifth argument of
            every handler call.
        z: `03 z pic 99.` [general/gl051.cbl:L172]. Promoted out-of-boundary
            precondition; question Q-5.
        trutht: `03 trutht pic 9.` [general/gl051.cbl:L175]. Promoted
            out-of-boundary precondition, `move 1 to trutht.`
            [general/gl051.cbl:L967]; question Q-4.
        actual_gross: `05 Actual-Gross pic 9(9)v99.`
            [copybooks/wsbatch.cob:L43]. Promoted out-of-boundary precondition,
            `move zero to actual-gross actual-vat.` [general/gl051.cbl:L982];
            question Q-4.
        actual_vat: `05 Actual-Vat pic 9(9)v99.` [copybooks/wsbatch.cob:L44].
            The other half of the same precondition.

    Returns:
        Nothing. COBOL sub-programs return through `goback` and communicate by
        mutating the records passed to them, and so does this: read
        `batch.batch_status` afterwards - `88 Status-Closed value 1.` means the
        batch was accepted, `88 Status-Open value 0.` means it was rejected, and
        an untouched value means the all-batches proof mode short-circuited the
        gate [general/gl051.cbl:L1099-L1100].
    """
    # The five handler-call records. Defaulted rather than required so a caller
    # holding no prior state need not build them; COBOL's own working storage is
    # initialised the same way, by `VALUE` clauses at load time.
    posting = WsPostingRecord() if posting is None else posting
    batch = GlBatchRecord() if batch is None else batch
    ledger = WsLedgerRecord() if ledger is None else ledger
    file_access = FileAccess() if file_access is None else file_access
    dal_common = AcasDalCommonData() if dal_common is None else dal_common

    # BOUNDARY PRECONDITION  [general/gl051.cbl:L982]
    # `move zero to actual-gross actual-vat.` - set by `gl050d`, immediately
    # before `perform batch-print` [general/gl051.cbl:L983]. A two-receiver
    # `MOVE` of the figurative zero, so each receiver is converted against its
    # own `pic 9(9)v99 comp-3` picture. AMBIGUITY Q-4: promoted to a parameter
    # because the statement is outside the boundary, and defaulted to the value
    # the COBOL gives it.
    batch.amounts.actual_gross = move.move(actual_gross, _ACTUAL_GROSS)
    batch.amounts.actual_vat = move.move(actual_vat, _ACTUAL_VAT)

    # BOUNDARY PRECONDITION  [general/gl051.cbl:L967] and [general/gl051.cbl:L172]
    # `move 1 to trutht.` - `gl050d` again. And `z`, which only out-of-scope
    # interactive code writes. AMBIGUITY Q-4 and Q-5.
    storage = _WorkingStorage(
        z=move.move(z, _Z),
        trutht=move.move(trutht, _TRUTHT),
    )

    # BOUNDARY PRECONDITION  [general/gl051.cbl:L980-L981]
    # `perform GL-Nominal-Open-Input.` and `perform GL-Posting-Open-Input.` are
    # `gl050d`'s and are NOT reproduced: the boundary contains no open and no
    # close. Both files are assumed open on entry, and the matching closes
    # [general/gl051.cbl:L989-L990] are assumed to follow the return.
    # AMBIGUITY Q-2.
    linkage = _HandlerLinkage(
        system_record=system_record,
        posting=posting,
        batch=batch,
        ledger=ledger,
        file_access=file_access,
        file_defs=file_defs,
        dal_common=dal_common,
    )

    _LOG.debug(
        "gl051 batch-print: entering with z=%s trutht=%s actual-gross=%s "
        "actual-vat=%s, run date %r [general/gl051.cbl:L999]",
        storage.z,
        storage.trutht,
        batch.amounts.actual_gross,
        batch.amounts.actual_vat,
        to_day,
    )

    # 999  batch-print  section.
    _batch_print(storage, linkage)

    # `ws-calling-data` and `to-day` are declared by the `PROCEDURE DIVISION
    # USING` list and are not read by the boundary's own statements: the term
    # code that aborts the posting cycle is set by `gl070`
    # [general/gl070.cbl:L289] and the run date is consumed by
    # `zz070-Convert-Date` [general/gl051.cbl:L1251], which `batch-print` never
    # performs. Both are bound so the linkage shape is exact, and both are named
    # here so that no reader concludes a parameter was dropped.
    _ = (ws_calling_data, to_day)


# --- traceability ---------------------------------------------------------
#
# Rule R-5. Every in-scope construct of general/gl051.cbl mapped to what
# reproduces it here, every `GO TO` classified at its site, and every deliberate
# omission recorded AS an omission - Agent Action Plan section 0.4.3, verbatim,
# on why: "so that a reader comparing the two files does not conclude something
# was lost."
#
# THIS FOOTER'S MOST IMPORTANT SECTION IS `BOUNDARY`, NOT `PARAGRAPH -> FUNCTION`.
# `general/gl051.cbl` is 1,282 lines and this module covers roughly 170 of them.
# What proves the PARTIAL boundary was respected is the list of what is absent,
# so that list is exhaustive and comes first among the omissions.
#
# PROGRAM  ->  MODULE
#   general/gl051.cbl  ->  acas_posting/programs/gl051_batch_control_check.py
#   program-id gl051; boundary PARTIAL - `batch-print section.`
#   [general/gl051.cbl:L999-L1166] in its entirety, plus the arithmetic fragments
#   Agent Action Plan section 0.4.1.2 names by locator, plus the four date
#   sections as thin delegations. NOTHING ELSE.
#
# BOUNDARY  -  what is IN, measured
#   batch-print               section.  [general/gl051.cbl:L999-L1166]   IN, whole
#     loop.                             [general/gl051.cbl:L1005]        IN
#     get-a-batch.                      [general/gl051.cbl:L1067]        IN
#     headings.                         [general/gl051.cbl:L1074]        IN
#     end-batch.                        [general/gl051.cbl:L1096]        IN
#     get-description.                  [general/gl051.cbl:L1136]        IN
#     main-exit.                        [general/gl051.cbl:L1166]        IN
#   net.                                [general/gl051.cbl:L788]         IN, fragment
#   gross.                              [general/gl051.cbl:L793]         IN, fragment
#   five account-scaling statements     [general/gl051.cbl:L604], L607,
#                                       L654, L657, L803                 IN, fragments
#   zz050-Validate-Date       section.  [general/gl051.cbl:L1169]        IN, delegation
#     zz050-test-date.                  [general/gl051.cbl:L1200]        IN, delegation
#     zz050-exit.                       [general/gl051.cbl:L1205]        IN, delegation
#   zz060-Convert-Date        section.  [general/gl051.cbl:L1208]        IN, delegation
#     zz060-Exit.                       [general/gl051.cbl:L1240]        IN, delegation
#   zz070-Convert-Date        section.  [general/gl051.cbl:L1243]        IN, delegation
#     zz070-Exit.                       [general/gl051.cbl:L1270]        IN, delegation
#   maps03                    section.  [general/gl051.cbl:L1273]        IN, delegation
#     maps04-exit.                      [general/gl051.cbl:L1278]      IN, ANOMALY A-22
#
#   THE PLAN'S CITED RANGE IS NARROWER THAN THE SECTION. Section 0.4.1.2 cites
#   [general/gl051.cbl:L1096-L1133], which is the `end-batch` paragraph ALONE -
#   the fourth of the section's six paragraphs. Section 0.2.1.1's table is the
#   correct reading: "only `batch-print` section 999 and its `end-batch`
#   paragraph", i.e. THE SECTION, INCLUDING `end-batch`. Measured, the section
#   runs L999 to L1166. Two of its paragraphs are entirely absent from the plan
#   and are load-bearing: `get-description.` [general/gl051.cbl:L1136], which is
#   the whole rejection path, and the accumulation at
#   [general/gl051.cbl:L1063-L1064], without which the gate compares against zero.
#
# BOUNDARY  -  what is OUT, named section by section
#   gl051-Main           section.  [general/gl051.cbl:L359]   OUT, whole
#   proof-all            section.  [general/gl051.cbl:L474]   OUT, whole
#   gl050c               section.  [general/gl051.cbl:L496]   OUT, whole, except
#       the `net.`/`gross.` computes and the four scaling statements above
#     accept-amount.               [general/gl051.cbl:L650]   OUT, except L654/L657
#     h-o-data.                    [general/gl051.cbl:L782]   OUT
#     get-description.             [general/gl051.cbl:L799]   OUT, except L803
#     main-exit.                   [general/gl051.cbl:L816]   OUT
#     end-routine.                 [general/gl051.cbl:L822]   OUT
#   batch-amendment      section.  [general/gl051.cbl:L825]   OUT, whole
#     batch-outline.               [general/gl051.cbl:L838]   OUT
#     b-o-loop2.                   [general/gl051.cbl:L845]   OUT
#     b-o-data.                    [general/gl051.cbl:L855]   OUT
#     cycle-in.                    [general/gl051.cbl:L868]   OUT
#     items-in.                    [general/gl051.cbl:L889]   OUT
#     gross-in.                    [general/gl051.cbl:L901]   OUT
#     vat-in.                      [general/gl051.cbl:L912]   OUT
#     desc-in.                     [general/gl051.cbl:L926]   OUT
#     detail-query.                [general/gl051.cbl:L939]   OUT
#   gl050d               section.  [general/gl051.cbl:L961]   OUT, whole
#     disp-head-skip.              [general/gl051.cbl:L978]   OUT
#     main-exit.                   [general/gl051.cbl:L985]   OUT
#     end-routine.                 [general/gl051.cbl:L993]   OUT
#   Every screen section, every `accept` loop and every amendment dialog: OUT.
#
# PARAGRAPH  ->  FUNCTION
#   procedure division using ws-calling-data, system-record, to-day, file-defs
#                     [general/gl051.cbl:L353-L356]  ->  run
#   batch-print  section. entry statements
#                     [general/gl051.cbl:L999-L1003] ->  _batch_print
#   loop.             [general/gl051.cbl:L1005]      ->  _loop
#   get-a-batch.      [general/gl051.cbl:L1067]      ->  _get_a_batch
#   headings.         [general/gl051.cbl:L1074]      ->  _headings
#   end-batch.        [general/gl051.cbl:L1096]      ->  _end_batch
#   get-description.  [general/gl051.cbl:L1136]      ->  _batch_print_get_description
#   main-exit.        [general/gl051.cbl:L1166]      ->  _batch_print_main_exit
#   net.              [general/gl051.cbl:L788]       ->  _net
#   gross.            [general/gl051.cbl:L793]       ->  _gross
#   zz050-Validate-Date section. + zz050-test-date. + zz050-exit.
#                     [general/gl051.cbl:L1169, L1200, L1205]
#                                                   ->  _zz050_validate_date
#   zz060-Convert-Date section. + zz060-Exit.
#                     [general/gl051.cbl:L1208, L1240]
#                                                   ->  _zz060_convert_date
#   zz070-Convert-Date section. + zz070-Exit.
#                     [general/gl051.cbl:L1243, L1270]
#                                                   ->  _zz070_convert_date
#   maps03 section. + maps04-exit.
#                     [general/gl051.cbl:L1273, L1278]
#                                                   ->  _maps03
#
#   TWO NAMES ARE SECTION-QUALIFIED BECAUSE THE FILE REUSES THEM.
#     * `main-exit.` occurs THREE times - [general/gl051.cbl:L816] in `gl050c`,
#       [general/gl051.cbl:L985] in `gl050d` and [general/gl051.cbl:L1166] in
#       `batch-print`. Only the third is in scope and only the third is a bare
#       terminator; the `gl050d` namesake closes three files and spools a report.
#       Hence `_batch_print_main_exit`.
#     * `get-description.` occurs TWICE - [general/gl051.cbl:L799] in `gl050c`
#       and [general/gl051.cbl:L1136] in `batch-print`. COBOL resolves the
#       unqualified `perform get-description` at [general/gl051.cbl:L1054] to the
#       paragraph in the SAME section, so it reaches L1136 and never L799. Hence
#       `_batch_print_get_description`.
#
#   FUNCTIONS THAT ARE NOT PARAGRAPHS, and why each exists:
#     _from_record                     resolves a copybook field's descriptor
#                                      from the record layer, so no picture is
#                                      re-transcribed here
#     _gl_posting_read_next            `perform GL-Posting-Read-Next.` L1008
#     _gl_batch_read_indexed           `perform GL-Batch-Read-Indexed.` L1070
#     _gl_nominal_read_indexed         `perform GL-Nominal-Read-Indexed.`
#                                      L1142 and L1156
#     _scale_acc_ok_from_post_dr       [general/gl051.cbl:L604]
#     _scale_acc_ok_from_post_cr       [general/gl051.cbl:L607]
#     _scale_post_dr_from_account      [general/gl051.cbl:L654]
#     _scale_post_cr_from_account      [general/gl051.cbl:L657]
#     _scale_ledger_nos_from_account   [general/gl051.cbl:L803]
#     _WorkingStorage                  the working-storage items the six in-scope
#                                      paragraphs share
#     _HandlerLinkage                  the five arguments every handler `CALL`
#                                      takes [copybooks/Proc-ACAS-FH-Calls.cob:L51-L57]
#
# STATEMENT  ->  CALL SITE   -  the complete arithmetic census of the in-scope
# and plan-named set. SEVENTEEN statements. Two are `ROUNDED` and fifteen are
# not, so truncation is the default path and rounding the annotated exception.
#   604   divide post-dr by 100 giving acc-ok
#             ->  arithmetic.divide_by_giving(..., _ACC_OK, rounded=False)
#                 in `_scale_acc_ok_from_post_dr`
#   607   divide post-cr by 100 giving acc-ok
#             ->  arithmetic.divide_by_giving(..., _ACC_OK, rounded=False)
#                 in `_scale_acc_ok_from_post_cr`
#   654   multiply account-in by 100 giving post-dr
#             ->  arithmetic.multiply_by_giving(..., _POST_DR, rounded=False)
#                 in `_scale_post_dr_from_account`
#   657   multiply account-in by 100 giving post-cr
#             ->  arithmetic.multiply_by_giving(..., _POST_CR, rounded=False)
#                 in `_scale_post_cr_from_account`
#   791   compute vat-amount ROUNDED = post-amount * ws-vat-rate / 100
#             ->  arithmetic.compute into _VAT_AMOUNT with the rounding flag
#                 SET, in `_net`
#                 ***  ROUNDED site 1 of 2  ***
#   796   compute vat-amount ROUNDED =
#             post-amount - (post-amount / ((ws-vat-rate + 100) / 100))
#             ->  arithmetic.compute into _VAT_AMOUNT with the rounding flag
#                 SET, in `_gross`
#                 ***  ROUNDED site 2 of 2  ***   question Q-9
#   797   subtract vat-amount from post-amount
#             ->  arithmetic.subtract_from(..., _POST_AMOUNT, rounded=False)
#                 in `_gross`. UN-`ROUNDED`, IMMEDIATELY AFTER A `ROUNDED` STORE -
#                 which is why rounding is a per-call argument and never a mode.
#   803   multiply account-in by 100 giving WS-Ledger-Nos
#             ->  arithmetic.multiply_by_giving(..., _WS_LEDGER_NOS, rounded=False)
#                 in `_scale_ledger_nos_from_account`. NOTE: this statement is in
#                 the OUT-OF-SCOPE `get-description.` [general/gl051.cbl:L799].
#   1035  divide post-dr by 100 giving l7-dr
#             ->  arithmetic.divide_by_giving(..., _L7_DR, rounded=False) in
#                 `_loop`. Presentation only; rendering omitted, question Q-14.
#   1037  divide post-cr by 100 giving l7-cr
#             ->  arithmetic.divide_by_giving(..., _L7_CR, rounded=False) in
#                 `_loop`. Presentation only.
#   1044  divide vat-ac of WS-Posting-Record by 100 giving l7-vat-ac
#             ->  arithmetic.divide_by_giving(..., _L7_VAT_AC, rounded=False) in
#                 `_loop`. Presentation only. ANOMALY A-21.
#   1060  Page-Lines - 6   (inside a relation condition, NO receiving field)
#             ->  arithmetic.compare(line_cnt, arithmetic.intermediate(
#                   lambda: page_lines - _PAGE_BREAK_MARGIN_DETAIL)) in `_loop`.
#                 `intermediate` deliberately does not quantize.
#   1063  add post-amount to actual-gross
#             ->  arithmetic.add_to(..., _ACTUAL_GROSS, rounded=False) in `_loop`
#                 ***  THE ACCUMULATION - cited nowhere in the plan  ***
#   1064  add vat-amount to actual-vat
#             ->  arithmetic.add_to(..., _ACTUAL_VAT, rounded=False) in `_loop`
#                 ***  THE ACCUMULATION  ***
#   1105  subtract input-vat from input-gross giving l9-amount
#             ->  arithmetic.subtract_giving(..., minuend=..., _L9_AMOUNT,
#                 rounded=False) in `_end_batch`. Presentation only. THIRD
#                 arithmetic form in this module: `c = b - a`.
#   1109  add actual-vat to actual-gross
#             ->  arithmetic.add_to(..., _ACTUAL_GROSS, rounded=False) in
#                 `_end_batch`
#                 ***  VAT ENTERS THE TOTAL BEFORE THE TEST AT L1117  ***
#   1111  Page-Lines - 12  (inside a relation condition, NO receiving field)
#             ->  arithmetic.compare(line_cnt, arithmetic.intermediate(
#                   lambda: page_lines - _PAGE_BREAK_MARGIN_TOTALS)) in
#                 `_end_batch`. FINDING F-3: TWELVE here, SIX at L1060.
#
#   FORM CONVENTIONS, stated because three different ones appear above:
#     `DIVIDE a BY b GIVING c`     means  c = a / b
#     `MULTIPLY a BY b GIVING c`   means  c = a * b
#     `SUBTRACT a FROM b GIVING c` means  c = b - a
#     `SUBTRACT a FROM b`          means  b = b - a
#   ZERO `ON SIZE ERROR` and ZERO `REMAINDER` clauses occur anywhere in `gl051`,
#   so no size-error path and no remainder receiver is reproduced.
#
# NON-ARITHMETIC STATEMENT  ->  CALL SITE
#   1003  move 1 to WS-Ledger
#             ->  move.move(values_for("GL-Batch")[0], _WS_LEDGER). One is
#                 `88 GL-Batch value 1.` [copybooks/wsbatch.cob:L16]; the value
#                 comes from the condition-name registry, not a bare literal.
#   1017  move batch to l4-batch save-batch WS-Batch-Nos
#             ->  move.move_to_all(batch, (_L4_BATCH, _SAVE_BATCH, _WS_BATCH_NOS))
#                 THREE receivers, THREE pictures, converted INDEPENDENTLY.
#   1019, 1081  move entered to u-bin
#             ->  move.move(..., _U_BIN, sending_field=_ENTERED)
#   1072  move 99999 to WS-Batch-Nos
#             ->  move.move(_BATCH_NOT_FOUND_SENTINEL, _WS_BATCH_NOS)
#   1087  move 6 to line-cnt
#             ->  move.move(_HEADING_LINE_COUNT, _LINE_CNT). A separate constant
#                 from `_PAGE_BREAK_MARGIN_DETAIL` despite the shared value: a
#                 count of lines written is not a margin.
#   1102, 1121  move 0 to batch-status
#             ->  move.move(values_for("Status-Open")[0], _BATCH_STATUS)
#   1119  move 1 to batch-status
#             ->  move.move(values_for("Status-Closed")[0], _BATCH_STATUS)
#   1126  if batch-status = 1
#             ->  is_status_closed(batch.batch_status)
#   1138, 1152  move zero to we-error
#             ->  move.move(move.Figurative.ZERO, _WE_ERROR)
#   1144, 1158  move 1 to we-error
#             ->  move.move(_WE_ERROR_LOCAL_FAILURE, _WE_ERROR). A LOCAL 0-or-1
#                 FLAG, NOT a handler code: emphatically not `WeError.NOT_USED`,
#                 value 999, which is `gl072`'s sentinel
#                 [general/gl072.cbl:L303-L304].
#   1139, 1153  move post-dr / post-cr to WS-Ledger-Nos
#             ->  move.move(..., _WS_LEDGER_NOS, sending_field=_POST_DR/_POST_CR)
#   1140, 1154  move dr-pc / cr-pc to ledger-pc
#             ->  move.move(..., _LEDGER_PC, sending_field=_DR_PC/_CR_PC)
#   1147, 1161  move spaces to dr-error / cr-error
#             ->  move.move(move.Figurative.SPACE, _DR_ERROR/_CR_ERROR)
#   1149, 1163  move "^^^^^^^^^^" to dr-error / cr-error
#             ->  move.move(_ACCOUNT_ERROR_MARKER, _DR_ERROR/_CR_ERROR)
#   1150, 1164  move 0 to trutht
#             ->  move.move(_FALSET_VALUE, _TRUTHT). THE ONLY TWO IN-SCOPE
#                 WRITERS OF `trutht`, and both only ever CLEAR it.
#   1056-1057  if cr-error not = spaces or dr-error not = spaces
#             ->  compared against `move.move(move.Figurative.SPACE, ...)` of the
#                 same field, so the operand width is the field's and not a
#                 hand-written literal's. An alphanumeric relation, so it does not
#                 go through `arithmetic.compare`, which is the NUMERIC comparator.
#   1082, 1020  perform zz060-Convert-Date
#             ->  _zz060_convert_date(...), whose return value is written BACK to
#                 `Date-Form` on the system record - question Q-7.
#   1276  call "maps04" using maps03-ws
#             ->  `acas_posting.dates.maps03(...)` via `_maps03`. Rule R-1: a
#                 native call, never a COBOL one.
#
# FILE-HANDLER VERBS  -  exactly three, ALL READS
#   1008  perform GL-Posting-Read-Next    ->  _gl_posting_read_next
#   1070  perform GL-Batch-Read-Indexed   ->  _gl_batch_read_indexed
#   1142  perform GL-Nominal-Read-Indexed ->  _gl_nominal_read_indexed  (DR)
#   1156  perform GL-Nominal-Read-Indexed ->  _gl_nominal_read_indexed  (CR)
#   NO write, NO rewrite, NO delete, NO open, NO close. The in-scope module
#   performs ZERO DATABASE MUTATIONS; its whole deliverable is `Batch-Status` on
#   the in-memory batch record - question Q-1.
#   `fs-reply` values go through `FsReply`: 10 is `END_OF_FILE`
#   [general/gl051.cbl:L1009] and 21 is `INVALID_KEY_ON_START`
#   [general/gl051.cbl:L1071], [general/gl051.cbl:L1143] and
#   [general/gl051.cbl:L1157]. `FsReply.KEY_NOT_FOUND`, value 23, is documented
#   but never returned, so it is not tested here. No bare 10 or 21 appears.
#   `gl051` copies [copybooks/Proc-ACAS-FH-Calls.cob] at
#   [general/gl051.cbl:L1281], which has NO per-handler error-check paragraph, so
#   every reply is tested INLINE - never through the IRS convention's
#   handler-named aliases [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob].
#
# `GO TO`  -  every in-scope transfer site, classified BY SHAPE
#   1010  go to end-batch    ->  CLASS 2, forward terminator.
#         `return` from `_loop`, PLUS the whole `end-batch` body placed after the
#         loop by `_batch_print`. Section 0.6.3, verbatim: "the transformation is
#         `break` plus faithful placement of that work after the loop, not
#         `break` alone. Mis-splitting here would silently drop end-of-run
#         processing." HERE THE "REAL WORK" IS THE ENTIRE CONTROL-TOTAL GATE.
#   1013  go to loop         ->  CLASS 1, loop-back.  `continue` in `_loop`.
#   1030  go to loop         ->  CLASS 1, loop-back.  `continue` in `_loop`.
#   1065  go to loop         ->  CLASS 1, loop-back.  `continue` in `_loop`,
#                                unconditional, which is why control never falls
#                                textually into `get-a-batch.` L1067.
#   1100  go to main-exit    ->  CLASS 3, section exit.  `return` from
#                                `_end_batch`, `Batch-Status` UNTOUCHED.
#   1103  go to main-exit    ->  CLASS 3, section exit.  `return` from
#                                `_end_batch` after setting `Status-Open`.
#   1134  go to main-exit    ->  CLASS 3, section exit.  `return` from
#                                `_end_batch`.
#   THE DATE SECTIONS' OWN TRANSFERS are measured here for completeness and are
#   classified BY `acas_posting/dates.py`, which owns their bodies - this module
#   holds four thin delegations and no date logic:
#     1186, 1191  go to zz050-test-date  ->  forward transfer to a sibling
#                 paragraph [general/gl051.cbl:L1200] that does real work and then
#                 falls into `zz050-exit.` [general/gl051.cbl:L1205]
#     1220, 1226, 1231  go to zz060-Exit  ->  CLASS 3, section exit
#     1256, 1261        go to zz070-Exit  ->  CLASS 3, section exit
#   `maps03 section.` [general/gl051.cbl:L1273] contains no `GO TO` at all - one
#   `call` and an exit label.
#   CLASS 4 - sibling re-dispatch - DOES NOT OCCUR inside this boundary. Every
#   one of the eight sites above is class 1, 2 or 3, so no per-site equivalence
#   proof is owed. The classification is by SHAPE and not by matching the plan's
#   label list, which section 0.4.2 does not claim to be exhaustive.
#
# `PERFORM ... THRU`  -  DOES NOT OCCUR inside this boundary. `gl051` has exactly
#   two, at [general/gl051.cbl:L504] and [general/gl051.cbl:L955], and BOTH are
#   out of scope - the first in `proof-all`, the second in `batch-amendment`.
#   Nothing here needed hand-verification for fall-through semantics.
#
# FALL-THROUGH made explicit
#   [general/gl051.cbl:L1003] -> [general/gl051.cbl:L1005]: the section's entry
#     statements fall into `loop.`; `_batch_print` calls `_loop` in sequence.
#   [general/gl051.cbl:L1024] and the `then next sentence` at
#     [general/gl051.cbl:L1027] both fall to [general/gl051.cbl:L1032]; the
#     `if`/`elif` chain in `_loop` falls to the print-line block the same way, and
#     the no-op arm is written out as `pass` rather than folded away.
#   [general/gl051.cbl:L1164] -> [general/gl051.cbl:L1166]: `get-description.`
#     ends with no `GO TO` and `main-exit.` is textually next. Control does not
#     actually go there, because the paragraph is only ever `perform`ed from
#     [general/gl051.cbl:L1054] and a `PERFORM` returns at the paragraph's end.
#     Both facts are stated in `_batch_print_get_description`.
#
# PROMOTED PRECONDITIONS  -  out-of-boundary statements turned into parameters
# `batch-print` is performed from `gl050d` [general/gl051.cbl:L983], and `gl050d`
# sets up FOUR things first that the gate is meaningless without. Each is an
# out-of-boundary precondition promoted to a keyword-only parameter of `run`,
# defaulting to the value the COBOL gives it:
#   trutht=1        `move 1 to trutht.`  [general/gl051.cbl:L967]
#                   The batch starts VALID. In scope the flag is only ever
#                   cleared, so without this the account rejection cannot fire.
#   actual_gross=0  `move zero to actual-gross actual-vat.`
#   actual_vat=0    [general/gl051.cbl:L982]. Both accumulators start at ZERO.
#   z=0             `03 z pic 99.` [general/gl051.cbl:L172], written only by
#                   out-of-scope interactive code, tested in scope at
#                   [general/gl051.cbl:L1015], [general/gl051.cbl:L1026],
#                   [general/gl051.cbl:L1088] and [general/gl051.cbl:L1099].
#                   Defaulted to single-batch mode, the mode in which the gate
#                   actually runs; 99 short-circuits it.
# A FOURTH `gl050d` STATEMENT THE PLAN DOES NOT MENTION is `move zero to
# page-nos.` [general/gl051.cbl:L966]. It is NOT promoted, because `page-nos`
# feeds nothing but the page number on a report this module does not print; it is
# modelled by `_WorkingStorage`'s own default, which routes the same figurative
# zero through the field's picture.
# ALSO OUTSIDE THE BOUNDARY, and NOT reproduced: `perform GL-Nominal-Open-Input.`
# [general/gl051.cbl:L980] and `perform GL-Posting-Open-Input.`
# [general/gl051.cbl:L981]. Both files are documented as already open on entry -
# question Q-2.
#
# OMISSIONS  -  recorded AS omissions, per section 0.4.3 and rule R-5
#   1.  THE ENTIRE OUT-OF-SCOPE SURFACE, named section by section and paragraph
#       by paragraph in the `BOUNDARY - what is OUT` table above: `gl051-Main`
#       section 359, `proof-all` section 474, `gl050c` section 496 with
#       `accept-amount.` L650, `h-o-data.` L782, `get-description.` L799,
#       `main-exit.` L816 and `end-routine.` L822; `batch-amendment` section 825
#       with `batch-outline.` L838, `b-o-loop2.` L845, `b-o-data.` L855,
#       `cycle-in.` L868, `items-in.` L889, `gross-in.` L901, `vat-in.` L912,
#       `desc-in.` L926 and `detail-query.` L939; and `gl050d` section 961 with
#       `disp-head-skip.` L978, `main-exit.` L985 and `end-routine.` L993. THIS
#       IS THE MOST IMPORTANT ENTRY IN THE LIST: it is what proves the PARTIAL
#       boundary was respected rather than quietly widened.
#   2.  The out-of-boundary preconditions and postconditions: the two opens
#       [general/gl051.cbl:L980-L981], `move 1 to trutht.`
#       [general/gl051.cbl:L967], the accumulator zeroing
#       [general/gl051.cbl:L982], `move zero to page-nos.`
#       [general/gl051.cbl:L966], `open output print-file`
#       [general/gl051.cbl:L965], and the closes `close print-file`
#       [general/gl051.cbl:L988] plus [general/gl051.cbl:L989-L990]. The first
#       three are promoted to parameters; the rest are context only.
#   3.  `call "SYSTEM" using Print-Report.` [general/gl051.cbl:L991] - the
#       report spool-out. Out of scope by section 0.2.2, and independently
#       forbidden by rule R-1: this module shells out to nothing.
#   4.  The two `GL-Batch-Rewrite` calls at [general/gl051.cbl:L415] and
#       [general/gl051.cbl:L491]. THE PERSISTENCE OF `Batch-Status` LIES OUTSIDE
#       THE BOUNDARY - question Q-1. This module sets the field and returns.
#   5.  The entire print file: `copy "selprint.cob"` [general/gl051.cbl:L112],
#       `copy "fdprint.cob"` [general/gl051.cbl:L122] and
#       `copy "print-spool-command.cob"` [general/gl051.cbl:L127]; every
#       `write print-record` inside the boundary - [general/gl051.cbl:L1023],
#       [general/gl051.cbl:L1052], [general/gl051.cbl:L1058],
#       [general/gl051.cbl:L1085-L1086], [general/gl051.cbl:L1091-L1094],
#       [general/gl051.cbl:L1113-L1115], [general/gl051.cbl:L1124],
#       [general/gl051.cbl:L1131] and [general/gl051.cbl:L1133]; and the print
#       line groups `line-1`, `line-3`, `line-4`, `line-5`, `line-6`, `line-7`,
#       `line-error`, `line-8`, `line-9`, `line-10` and `line-11` with their
#       `l1-*`, `l3-*`, `l4-*`, `l7-*`, `l9-*`, `l10-*` and `l11-*` fields,
#       `page-nos`' printed rendering, `display-vat` and `display-amt`.
#       Three of the print fields ARE modelled because statements the census
#       names receive into them - `_L7_DR`, `_L7_CR`, `_L7_VAT_AC` and
#       `_L9_AMOUNT` - and a fourth, `_L4_BATCH`, because it is a receiver of the
#       three-receiver `MOVE`. Their RENDERING is still omitted: `cobol/move.py`
#       implements the Z-then-9 edited shape only and deliberately declines
#       `zzz9.99b`, `z(9)9.99bb` and `zzz9.99 blank when zero` because no
#       database write reaches such a picture and no oracle experiment can
#       observe it - question Q-14.
#   6.  `dr-error` and `cr-error`'s printed appearance, though NOT their values:
#       [general/gl051.cbl:L1056-L1057] reads them back to decide whether to
#       advance `line-cnt`, so both are reproduced as state - question Q-8.
#   7.  Every `display ... at` statement inside the boundary becomes a log
#       record. Section 0.3.4: they "must not alter control flow and must not
#       appear in any table dump." Not one log call below changes a branch.
#   8.  `copy "envdiv.cob"` [general/gl051.cbl:L102] and `copy "screenio.cpy"`
#       [general/gl051.cbl:L161] - representation only; there is no environment
#       division and no screen section in Python.
#   9.  `01 Dummies-4-Unused-ACAS-FH-Calls.` [general/gl051.cbl:L136-L156] - a
#       seventeen-entry block of `03 ... pic x` facade stubs, declared purely so
#       the linker resolves the copybook's full verb set. Representation only,
#       exactly like `gl072`'s [general/gl072.cbl:L134-L153]. See CITATION
#       CORRECTIONS: the plan states `gl051` has no such block, and it does.
#  10.  `l7-vat-pc`, `l7-side`, `l7-legend`, `l7-number`, `l7-code`, `l7-date`,
#       `l7-dr-pc`, `l7-cr-pc`, `l7-amount`, `l7-vat`, `l4-date`, `l4-desc`,
#       `l9-vat`, `l10-amount`, `l10-vat` and `l11-status` - the print receivers
#       of [general/gl051.cbl:L1032-L1050], [general/gl051.cbl:L1106-L1108],
#       [general/gl051.cbl:L1123] and [general/gl051.cbl:L1126-L1132], none of
#       which reaches a table.
#  11.  [general/gl051.cbl:L1047-L1048]'s conditional. `if vat-ac ... not equal
#       zero move post-vat-side to l7-side.` Its only consequence writes a print
#       field, so reproducing the `if` would leave an empty branch; the statement
#       is recorded here and its anomaly A-21 qualification is commented at the
#       site.
#  12.  THERE IS NO `accept` STATEMENT INSIDE THE BOUNDARY. Section 0.3.4's
#       second and third cases - an accept that gates a database write, and an
#       accept that merely pauses - therefore do not arise for this module. Every
#       `accept` in `general/gl051.cbl` is in an out-of-scope interactive section.
#
# ANOMALIES REPRODUCED  -  rule R-4, "a defect reproduced is correct; a defect
# fixed is a failure"
#   A-22, OCCURRENCE 2.  The wrapper naming inconsistency. `maps03 section.`
#       [general/gl051.cbl:L1273] carries the exit label `maps04-exit.`
#       [general/gl051.cbl:L1278]: the section is named after the interface
#       copybook while its exit is named after the called program. The plan
#       records this defect for `gl070` alone [general/gl070.cbl:L603] and
#       [general/gl070.cbl:L608]; `gl051` HAS THE IDENTICAL DEFECT and this is its
#       second occurrence. Reproduced by `_maps03`, whose traceability records the
#       mismatched exit label.
#   A-21, three in-scope sites.  Qualified references forced by field-name
#       collisions across three posting copybooks: `post-code in
#       WS-Posting-Record` [general/gl051.cbl:L1033] using `in`, and `vat-ac of
#       WS-Posting-Record` [general/gl051.cbl:L1044] and
#       [general/gl051.cbl:L1047] using the synonym `of`. BOTH SPELLINGS OCCUR.
#       In Python the collision cannot arise, so the reproduction is the comment
#       at each site plus record-qualified attribute access wherever such a field
#       is read - never a bare local.
#   A-15, context rather than a reproduction site.  The batch record's declared
#       length contradicts the sum of its fields, and the copybook says so in the
#       maintainer's own words at [copybooks/wsbatch.cob:L7-L9]: 96 bytes, then 98
#       bytes, then "no, dont understand as I count 96 / but function length
#       (Batch-record) says 98?". `gl051` is the program that reads and writes
#       those very fields. Whether the declared length or the field sum governs
#       the record actually read affects alignment for the TRAILING fields, and
#       section 0.6.8 records that only execution shows which - question Q-10.
#       This module takes the layout exactly as `acas_posting/records/gl_batch.py`
#       publishes it and does not attempt to reconcile the contradiction.
#
# FINDINGS  -  not in the plan's twenty-two-entry register, recorded for the
# anomaly and ambiguity logs
#   F-1  `trutht` / `truet` / `falset`. The data item is `03 trutht pic 9.`
#        [general/gl051.cbl:L175] - a TRANSPOSITION TYPO of "truth"/"true" - while
#        its condition names are `88 falset value zero.`
#        [general/gl051.cbl:L176] and `88 truet value 1.`
#        [general/gl051.cbl:L177]. AND `falset` IS DECLARED BUT NEVER TESTED,
#        not once in 1,282 lines; only `truet` is, at [general/gl051.cbl:L507]
#        out of scope and [general/gl051.cbl:L1101] in scope. Same character of
#        finding as the plan's A-20, the spare fields misnamed with the Sales
#        prefix inside the Purchase group. `_FALSET_VALUE` is therefore declared
#        as a value and deliberately NOT turned into a predicate, which would
#        imply a test the COBOL never makes.
#   F-2  THE PLAN'S DESCRIPTION OF THIS PROGRAM IS FACTUALLY WRONG. Section
#        0.4.1.2 says `gl051` "Accumulates actual DR/CR/VAT". There is no
#        `actual-DR` and no `actual-CR` anywhere in `general/gl051.cbl`:
#        [copybooks/wsbatch.cob:L40-L44] declares `03 Amounts comp-3.` with
#        EXACTLY FOUR money fields - `Input-Gross`, `Input-Vat`, `Actual-Gross`
#        and `Actual-Vat`, all `pic 9(9)v99` and all UNSIGNED. What the program
#        accumulates is gross and VAT, at [general/gl051.cbl:L1063-L1064].
#   F-3  The two page-break constants DIFFER: `Page-Lines - 6`
#        [general/gl051.cbl:L1060] against `Page-Lines - 12`
#        [general/gl051.cbl:L1111]. Deliberate - twelve guards three multi-line
#        total blocks about to be written - and reproduced as written.
#   F-4  SIGNEDNESS ASYMMETRY AT THE ACCUMULATION. `Post-Amount`
#        [copybooks/wspost.cob:L23] and `Vat-Amount` [copybooks/wspost.cob:L28]
#        are `pic s9(8)v99`, SIGNED; the receivers `Actual-Gross` and `Actual-Vat`
#        [copybooks/wsbatch.cob:L43-L44] are `pic 9(9)v99`, UNSIGNED. A negative
#        addend therefore contributes its MAGNITUDE - question Q-3. Nothing
#        guards it, because a guard would be a new validation under rule R-3.
#   F-5  TWO DISAGREEING SENTINELS FOR THE SAME IDEA IN ONE FILE. The
#        out-of-scope `get-description.` [general/gl051.cbl:L799] moves 255 to
#        `we-error` on a failed nominal read [general/gl051.cbl:L808]; the
#        in-scope one at [general/gl051.cbl:L1136] moves 1
#        [general/gl051.cbl:L1144] and [general/gl051.cbl:L1158]. Neither is a
#        member of the handler's own code vocabulary.
#   F-6  `line-cnt` IS PRESENTATION AND STILL LOAD-BEARING. Its increments feed
#        the two page-break tests, which perform `headings`, which performs
#        `zz060`, which can mutate `Date-Form` - a `SYSTEM-REC` column, therefore
#        diff-visible. So the counter is reproduced although the printing is not -
#        question Q-8.
#   F-7  THE ACCUMULATOR CLOBBER. `perform get-a-batch`
#        [general/gl051.cbl:L1018] reads a batch header, which replaces EVERY
#        field of `WS-Batch-Record` including `Actual-Gross` and `Actual-Vat`.
#        Harmless only because the branch that performs it requires `z = 99`
#        [general/gl051.cbl:L1015] and `end-batch` short-circuits in exactly that
#        mode [general/gl051.cbl:L1099]. Reproduced as written.
#   F-8  THE NESTED THREE-WAY. [general/gl051.cbl:L1015-L1030] is a three-armed
#        conditional whose middle arm is COBOL's explicit `then next sentence`
#        no-op [general/gl051.cbl:L1027], not the two-way a summary reading
#        suggests. Folding the no-op away would change behaviour: without it, an
#        all-batches run whose batch number had not changed would fall into the
#        `batch not = WS-Batch-Nos` test and could skip the posting.
#   F-9  THE 99999 SENTINEL IS UNREACHABLE AS A SKIP MECHANISM. `get-a-batch`
#        plants it in `WS-Batch-Nos` [general/gl051.cbl:L1072] when a batch header
#        cannot be found, and the sentinel is universally described as making the
#        comparison at [general/gl051.cbl:L1029] fail so the rest of the batch is
#        silently skipped. Measured, `perform get-a-batch` occurs EXACTLY ONCE in
#        the whole file, at [general/gl051.cbl:L1018], inside the arm requiring
#        `z = 99`; in that mode L1029 is never reached because the middle arm
#        [general/gl051.cbl:L1026-L1027] short-circuits, and in the other mode
#        the paragraph is never performed. So the sentinel's only observable
#        effect is the batch number printed by `headings`
#        [general/gl051.cbl:L1079]. Reproduced exactly as written; the
#        reachability is recorded, not corrected. Confirmed by execution during
#        validation, which is what turned the received reading into a finding.
#
# CITATION CORRECTIONS  -  measured against the sources, recorded so the
# discrepancies are not rediscovered as defects
#   * THE PLAN STATES `gl051` HAS NO FACADE STUB BLOCK. It has one:
#     `01 Dummies-4-Unused-ACAS-FH-Calls.` [general/gl051.cbl:L136-L156],
#     seventeen `03 ... pic x` entries with the comment "Call blk at
#     zz080-ACAS-Calls". The plan attributes such a block to `gl072`
#     [general/gl072.cbl:L134-L153] and `gl080` only.
#   * The plan's boundary citation [general/gl051.cbl:L1096-L1133] is the
#     `end-batch` paragraph, not the section; the section is L999-L1166. Section
#     0.2.1.1's own table - "`batch-print` section 999 and its `end-batch`
#     paragraph" - is the correct reading.
#   * `gl070`'s cycle filter is at [general/gl070.cbl:L312-L313], not L309-L310
#     as section 0.6.4 cites; its open-batch test is [general/gl070.cbl:L314-L315]
#     and the terminate code is set at [general/gl070.cbl:L289].
#   * `general/general.cbl`'s posting-cycle dispatch is `load08.` at
#     [general/general.cbl:L805], with the abort gate at
#     [general/general.cbl:L810-L811] and the `gl071`/`gl072` calls at
#     [general/general.cbl:L812] and [general/general.cbl:L814]; section 0.4.1.1
#     cites L806-L816.
#   * `01 to-day pic x(10).` is declared at [general/gl051.cbl:L351], inside the
#     linkage section after the three copybooks, not among the working storage.
#   * `general/gl051.cbl` carries FIFTEEN `copy` statements, the most of any
#     in-scope program, at L102, L112, L122, L127, L128, L129, L130, L131, L132,
#     L158, L161, L347, L348, L349 and L1281.
#
# AMBIGUITIES FOR THE ORACLE  -  rule R-6, "compiled behavior is the tie-breaker".
# Every one is marked `# AMBIGUITY Q-n` at its site and belongs in
# docs/migration/ambiguity-resolutions.md.
#   Q-1  Is `Batch-Status` persistence the caller's? The boundary contains no
#        rewrite; the two `GL-Batch-Rewrite` calls are at
#        [general/gl051.cbl:L415] and [general/gl051.cbl:L491].
#   Q-2  Are `GL-Nominal` and `GL-Posting` open on entry, and does the caller
#        close them? [general/gl051.cbl:L980-L981] and
#        [general/gl051.cbl:L989-L990] say `gl050d` does both.
#   Q-3  What does an UNSIGNED `pic 9(9)v99 comp-3` accumulator store when a
#        SIGNED negative addend is added to it - [general/gl051.cbl:L1063-L1064]
#        and [general/gl051.cbl:L1109]?
#   Q-4  The three promoted preconditions - `trutht`, `actual-gross`,
#        `actual-vat`. Does any caller other than `gl050d` reach `batch-print`
#        with different values?
#   Q-5  `z`'s value on entry. Only out-of-scope interactive code writes it, and
#        99 short-circuits the entire gate [general/gl051.cbl:L1099].
#   Q-6  The file-handler facade's Python call shape. Section 0.4.3 writes it as
#        `facade.gl_batch_read_next(ctx)`, but no `ctx` type is defined anywhere
#        in the tree, while every handler's own `dispatch` takes the five
#        arguments of the COBOL `CALL`
#        [copybooks/Proc-ACAS-FH-Calls.cob:L51-L57]. This module forwards those
#        five, in COBOL order, through three named adapters so there is a single
#        place to reconcile.
#   Q-7  `Date-Form` is MUTATED from zero to one at [general/gl051.cbl:L1184],
#        [general/gl051.cbl:L1224] and [general/gl051.cbl:L1254]. It is a
#        `SYSTEM-REC` column and therefore diff-visible, so the converted value
#        is written back rather than discarded.
#   Q-8  Does `line-cnt`'s exact value matter to the database? Only through the
#        page-break tests reaching `zz060` and hence Q-7 - but that is enough for
#        the counter to be reproduced.
#   Q-9  The compound VAT expression's intermediate precision
#        [general/gl051.cbl:L796]. Section 0.6.8, verbatim: "the compound VAT
#        expression, which is the one place a precision difference could change a
#        stored penny." The expected value must be CAPTURED FROM THE COMPILED
#        ORACLE, never derived by reading the COBOL.
#  Q-10  A-15's batch-record length contradiction
#        [copybooks/wsbatch.cob:L7-L9]: declared length or field sum?
#  Q-14  The unobservable edited pictures. `cobol/move.py` declines `zzz9.99b`,
#        `z(9)9.99bb` and `zzz9.99 blank when zero` on the ground that no
#        in-scope database write reaches such a picture, so no oracle experiment
#        can observe the rendering. The DIVIDEs and the SUBTRACT that receive into
#        them are reproduced; the rendering is not.
#
# RULES  -  there is NO user rules document for this project. `review_rules`
# returns "No user rules provided." The six binding rules live in Agent Action
# Plan section 0.7.2 and are honoured here as follows:
#   R-1  No COBOL at runtime. No subprocess, no foreign-function interface, no
#        reference to the harness. `perform maps03` [general/gl051.cbl:L1203] and
#        [general/gl051.cbl:L1217] become calls into `acas_posting.dates`, and
#        `call "maps04"` [general/gl051.cbl:L1276] becomes a native Python call.
#        `call "SYSTEM" using Print-Report.` [general/gl051.cbl:L991] is out of
#        scope and omitted.
#   R-2  Zero binary floating point. Every value is `decimal.Decimal` or `int`;
#        every store, comparison and `MOVE` delegates to `cobol/arithmetic.py`
#        and `cobol/move.py`. Section 0.3.1, verbatim: "`cobol/` contains no
#        business logic and `programs/` contains no numeric primitives." This
#        module therefore contains no quantize, no rounding mode, no scale
#        alignment, no picture parse and no comparator of its own. Two `ROUNDED`
#        stores exist, at [general/gl051.cbl:L791] and [general/gl051.cbl:L796];
#        every other store truncates.
#   R-3  No new validations, fields or schema changes, and no concurrency. Every
#        conditional in this module maps to a numbered COBOL line; not one is
#        added. No DDL and no ORM. No concurrent execution of any kind: no
#        threads, no event loop, no process pool, no connection pool -
#        execution is strictly sequential, matching the single-threaded COBOL.
#        And no line outside the boundary is migrated.
#   R-4  Legacy anomalies reproduced, never fixed. See ANOMALIES above; each site
#        carries its locator and a DO NOT FIX note.
#   R-5  Full traceability. Program to module, paragraph to function, statement
#        to call site, `GO TO` class per site, and every field descriptor resolved
#        from `acas_posting/records/*` or built by `cobol/picture.py` with a
#        `source_locator`.
#   R-6  Compiled behavior is the tie-breaker. See AMBIGUITIES above. Nothing
#        here reads a clock: `general/gl051.cbl` has ZERO clock reads, the date
#        arrives through `to-day` [general/gl051.cbl:L351] and `Run-Date`
#        [copybooks/wssystem.cob:L67], and the controlled-clock module
#        `acas_posting/clock.py` is deliberately NOT imported.
#
# --- end traceability -----------------------------------------------------
