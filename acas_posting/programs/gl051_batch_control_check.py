"""`gl051` - the General Ledger batch control-total gate [general/gl051.cbl].

A PARTIAL migration: only the control-total gate, the `end-batch` paragraph of
the `batch-print` section [general/gl051.cbl:L1096-L1133]. The rest of the file
is a proof-and-amendment screen program and is out of scope, so this module holds
no screen, no accept loop and no amendment dialogue.

The gate accumulates the batch's actual debit, credit and VAT totals and then
decides acceptance. Order of operations is load-bearing: actual VAT is added into
the actual gross BEFORE the equality test against the entered gross
[general/gl051.cbl:L1109-L1118], because the entered figure is VAT-inclusive.
Reversing the two steps would reject every batch that carries VAT.

Rejection is not a no-op: it leaves the batch open, which gl070 then detects
[general/gl070.cbl:L314-L315] and answers with terminate code 5
[general/gl070.cbl:L289], so the later phases never run at all. The database
effect of the rejection is the absence of everything they would have written.

THE BOUNDARY
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
=======
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

DELIBERATELY NOT IN SCOPE - seven arithmetic fragments and two date sections
that a reader of plan section 0.4.1.2's summary column might expect to find here.
`net.` L788, `gross.` L793, the five account-scaling statements at L604, L607,
L654, L657 and L803, `zz050-Validate-Date` L1169 and `zz070-Convert-Date` L1243
all live in paragraphs section 0.2.1.1's boundary excludes - `gl050c` section 496
and `gl050d` section 961 - and a census of every `perform` between L999 and L1166
proves that not one of them is reachable from inside the boundary. They are named
individually in the footer's OMISSIONS list, entry 1a, together with the reason
and with where each pattern still lives (`acas_posting.cobol.arithmetic` and
`acas_posting.dates`). Section 0.8.7 is the governing warning: "an agent working
from the file rather than from the stated boundary would migrate several hundred
lines that must not be migrated."

IN SCOPE as thin delegations, because `batch-print` performs `zz060` twice
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
no close anywhere inside the REPORT SECTION. The opens are `gl050d`'s
[general/gl051.cbl:L980-L981] and so are the closes
[general/gl051.cbl:L989-L990].

The section's own deliverable is therefore a VALUE: `Batch-Status` on the batch
record, plus the `trutht` flag that decides it. ⭐ AND `run` WRITES THAT VALUE TO
THE ROW. Both frozen callers of the gate perform `GL-Batch-Rewrite`
UNCONDITIONALLY immediately after it - [general/gl051.cbl:L415] in `gl051-Main`
and [general/gl051.cbl:L491] in `proof-all` - and both callers are out of scope,
while section 0.4.1.1 gives the migration no CLI route that dispatches `gl051`.
So `run` performs it, once, at the position the source gives it. Question Q-1 is
RESOLVED FROM THE SOURCE, not left to the oracle: no path exists in either caller
on which the gate runs and the rewrite does not follow. See `_gl_batch_rewrite`.

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

  Q-1 RESOLVED FROM THE SOURCE - no oracle experiment needed. The question was
      whether persisting `Batch-Status` is the caller's job. It is the caller's
      STATEMENT but not a caller's DECISION: both callers issue
      `GL-Batch-Rewrite` UNCONDITIONALLY on every path that reaches the gate -
      [general/gl051.cbl:L415] in `gl051-Main` and [general/gl051.cbl:L491] in
      `proof-all` - so the field ALWAYS reaches `GLBATCH-REC`. Since both callers
      are out of scope and section 0.4.1.1 gives the migration no route that
      dispatches `gl051`, `run` performs the rewrite itself at that position. Not
      doing so would leave the gate with no observable effect at all.
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
from dataclasses import dataclass, field
from typing import Final

# copy "Proc-ACAS-FH-Calls.cob". [general/gl051.cbl:L1281] The 21-entity, 12-verb file-
# handler facade.
from acas_posting.dal import facade

from acas_posting.dal.status import FsReply

# The date sections. `zz050`, `zz060`, `zz070` and the date-module wrapper are
# repeated near-identically in nine of the in-scope programs, and `dates.py` is
# where they consolidate - the one place consolidation is unambiguously safe
# because the bodies are textually equivalent.
#
# ONLY TWO OF THE FOUR ARE IMPORTED, because only two are reachable from this
# module's boundary. A census of every `perform` between
# [general/gl051.cbl:L999] and [general/gl051.cbl:L1166] names
# `zz060-Convert-Date` and nothing else of the four; `zz060` in turn performs
# `maps03` [general/gl051.cbl:L1217]. `zz050-Validate-Date` is performed only
# from `gl050c` [general/gl051.cbl:L496] and `zz070-Convert-Date` only from
# `gl050d` [general/gl051.cbl:L961], both of which
# [general/gl051.cbl] declares out of scope in their entirety, so
# `zz050_validate_date_gl051` and `zz070_convert_date` are not imported here at
# all. They remain published by `acas_posting.dates` for the carriers that do
# reach them.
#
# `maps03` and `maps04` are the SAME wrapper under both names. `gl051` and
# `gl070` perform one named `maps03` [general/gl051.cbl:L1273]; the Sales and
# Purchase carriers perform one named `maps04`. This module passes `maps03`.
from acas_posting.dates import (
    WsDateFormats,
    maps03 as _dates_maps03,
    zz060_convert_date,
)

# copy "wsfnctn.cob". [general/gl051.cbl:L129] - the record-layout half. `01 File-
# Access.` [copybooks/wsfnctn.cob:L23-L38], carrying `We-Error pic 999` and `Fs-Reply
# pic 99`. Both are read and written inside the boundary.
from acas_posting.records.file_access import (
    ALL_FIELDS as _FILE_ACCESS_FIELDS,
    FileAccess,
)

from acas_posting.records.file_defs import FileDefs

from acas_posting.records.gl_batch import (
    BatchAmounts,
    BatchDates,
    GlBatchRecord,
    WsBatchKey,
)

# copy "wsledger.cob". [general/gl051.cbl:L130] The nominal account. Only its KEY is
# written here - `WS-Ledger-Nos` and `Ledger-PC` - and only the reply is read back.
from acas_posting.records.gl_ledger import WsLedgerKey, WsLedgerRecord

from acas_posting.records.gl_posting import WsPostingRecord

from acas_posting.records.maps03 import Maps03Ws

from acas_posting.records.calling_data import WsCallingData

from acas_posting.records.system_record import SystemRecord

from acas_posting.records.test_data_flags import AcasDalCommonData

from acas_posting.cobol import arithmetic, move
from acas_posting.cobol.condition_names import is_status_closed, values_for
from acas_posting.cobol.field import FieldDescriptor
from acas_posting.cobol.picture import descriptor_for

#: The whole public surface: this program's single entry point, mirroring its `PROCEDURE
#: DIVISION USING` list [general/gl051.cbl:L353-L356]. Agent Action Plan section 0.3.3,
#: verbatim.
__all__: Final[tuple[str, ...]] = ("run",)

#  THIS MODULE HAS NO LOGGER, DELIBERATELY.
#
# A census of the in-scope span - `batch-print section.` through its `main-exit.`
# [general/gl051.cbl:L999-L1170] - finds ZERO `display` statements and FIFTEEN
# `write print-record` statements. Agent Action Plan section 0.3.4 makes a
# DISPLAY with no database effect a log record, and there are none to convert;
# section 0.2.2 puts "report formatting beyond database effects" out of scope, and
# that is all fifteen of the writes. A module-level logger existed only to carry
# thirteen records that were, without exception, either an invented narration of
# frozen control flow (R-4) or the report's own content - batch numbers, nominal
# account numbers and control totals - re-emitted to a different destination
# (CWE-532).
#
# The gate's entire observable outcome is `Batch-Status` in `GLBATCH-REC`, which is
# what `harness/diff_states.py` compares for the control-total-mismatch scenario.


def _from_record(
    fields: tuple[FieldDescriptor, ...], cobol_name: str
) -> FieldDescriptor:
    """Resolve one copybook field's descriptor from its record class's `FIELDS`.

    Rule R-5 requires every descriptor to carry provenance, and
    `FieldDescriptor.__post_init__` enforces it.

    Args:
        fields: The `FIELDS` tuple published by a record dataclass.
        cobol_name: The field's name exactly as its copybook spells it.

    Returns:
        The published descriptor for that field.

    Raises:
        KeyError: If the record class publishes no such field.
    """
    for descriptor in fields:
        if descriptor.name == cobol_name:
            return descriptor
    raise KeyError(
        f"{cobol_name!r} is not published by this record layout. Adding a field "
        f"the frozen copybooks do not declare is forbidden by rule R-3. "
        f"Published names: {tuple(d.name for d in fields)!r}"
    )


_WS_LEDGER: Final = _from_record(WsBatchKey.FIELDS, "WS-Ledger")
_WS_BATCH_NOS: Final = _from_record(WsBatchKey.FIELDS, "WS-Batch-Nos")
_BATCH_STATUS: Final = _from_record(GlBatchRecord.FIELDS, "Batch-Status")

_INPUT_GROSS: Final = _from_record(BatchAmounts.FIELDS, "Input-Gross")
_INPUT_VAT: Final = _from_record(BatchAmounts.FIELDS, "Input-Vat")
_ACTUAL_GROSS: Final = _from_record(BatchAmounts.FIELDS, "Actual-Gross")
_ACTUAL_VAT: Final = _from_record(BatchAmounts.FIELDS, "Actual-Vat")

_POST_DR: Final = _from_record(WsPostingRecord.FIELDS, "Post-DR")
_POST_CR: Final = _from_record(WsPostingRecord.FIELDS, "Post-CR")
_DR_PC: Final = _from_record(WsPostingRecord.FIELDS, "DR-PC")
_CR_PC: Final = _from_record(WsPostingRecord.FIELDS, "CR-PC")
#: `03  Vat-AC  pic 9(6).` [copybooks/wspost.cob:L25] is read twice inside the
#: boundary - [general/gl051.cbl:L1044] and [general/gl051.cbl:L1047], both
#: qualified references and both anomaly A-21 sites - but neither statement needs
#: a SENDING descriptor: the first is a `DIVIDE ... GIVING` whose only descriptor
#: is its receiver, and the second is a relation condition against the figurative
#: zero. No constant is declared for it rather than declaring one that nothing
#: uses; the locator is cited at each of the two sites instead.

_WS_LEDGER_NOS: Final = _from_record(WsLedgerKey.FIELDS, "WS-Ledger-Nos")
_LEDGER_PC: Final = _from_record(WsLedgerKey.FIELDS, "Ledger-PC")

_U_BIN: Final = _from_record(Maps03Ws.FIELDS, "u-bin")

#: `05 Entered binary-long.` [copybooks/wsbatch.cob:L36] - the sending field of those
#: two `MOVE` statements.
_ENTERED: Final = _from_record(BatchDates.FIELDS, "Entered")

#: `03 We-Error pic 999.` [copybooks/wsfnctn.cob:L23].
_WE_ERROR: Final = _from_record(_FILE_ACCESS_FIELDS, "We-Error")

#: `move  1  to  we-error.`  [general/gl051.cbl:L1144] and
#: [general/gl051.cbl:L1158]. A BARE LITERAL ONE in the source, not a member of
#: the handler's code vocabulary: it is emphatically NOT `WeError.NOT_USED`,
#: whose value is 999 and which is `gl072`'s sentinel
#: [general/gl072.cbl:L306-L307]. (The anomaly register cites that sentinel as
#: [general/gl072.cbl:L303-L304]; in the frozen checkout the two statements read
#: at L306-L307, and the frozen file is the authority.) Named here so the call
#: sites read as the flag
#: they are, and so nobody substitutes an enum member that would change the
#: stored value. Finding F-5 records that the out-of-scope `get-description.`
#: [general/gl051.cbl:L799] uses 255 for the identical purpose
#: [general/gl051.cbl:L808].
_WE_ERROR_LOCAL_FAILURE: Final[int] = 1


# Field descriptors - `gl051`'s own WORKING-STORAGE These fields never reach a table, so
# the generated dictionary does not cover them and their `source_locator` is the only
# traceability they will ever have (rule R-5).

#: `03 line-cnt binary-char value zero.` [general/gl051.cbl:L166]. A binary field, so
#: Python `int`; question Q-8 records why a print-line counter is reproduced at all.
_LINE_CNT: Final = descriptor_for(
    "binary-char value zero", name="line-cnt", source_locator="general/gl051.cbl:L166"
)
_PAGE_NOS: Final = descriptor_for(
    "binary-char value zero", name="page-nos", source_locator="general/gl051.cbl:L167"
)
_Z: Final = descriptor_for("pic 99", name="z", source_locator="general/gl051.cbl:L172")
_SAVE_BATCH: Final = descriptor_for(
    "pic 9(5) comp value zero",
    name="save-batch",
    source_locator="general/gl051.cbl:L174",
)
_TRUTHT: Final = descriptor_for(
    "pic 9", name="trutht", source_locator="general/gl051.cbl:L175"
)
_ACCOUNT_IN: Final = descriptor_for(
    "pic 9(4)v99", name="account-in", source_locator="general/gl051.cbl:L178"
)
_ARRAY_PC: Final = descriptor_for(
    "pic 99", name="array-pc", source_locator="general/gl051.cbl:L179"
)
_WS_VAT_RATE: Final = descriptor_for(
    "pic 99v99 comp value zero",
    name="ws-vat-rate",
    source_locator="general/gl051.cbl:L183",
)

#: `03 l4-batch pic z(4)9.` [general/gl051.cbl:L289] - a print field, and the FIRST
#: receiver of the three-receiver `MOVE` at [general/gl051.cbl:L1017].
_L4_BATCH: Final = descriptor_for(
    "pic z(4)9", name="l4-batch", source_locator="general/gl051.cbl:L289"
)
_L7_DR: Final = descriptor_for(
    "pic zzz9.99b", name="l7-dr", source_locator="general/gl051.cbl:L308"
)
_L7_CR: Final = descriptor_for(
    "pic zzz9.99b", name="l7-cr", source_locator="general/gl051.cbl:L310"
)
_L7_VAT_AC: Final = descriptor_for(
    "pic zzz9.99 blank when zero",
    name="l7-vat-ac",
    source_locator="general/gl051.cbl:L314",
)
_DR_ERROR: Final = descriptor_for(
    "pic x(12)", name="dr-error", source_locator="general/gl051.cbl:L321"
)
_CR_ERROR: Final = descriptor_for(
    "pic x(12)", name="cr-error", source_locator="general/gl051.cbl:L322"
)
_L9_AMOUNT: Final = descriptor_for(
    "pic z(9)9.99bb", name="l9-amount", source_locator="general/gl051.cbl:L331"
)


#: `88 truet value 1.` [general/gl051.cbl:L177].
_TRUET_VALUE: Final[int] = 1

#: `88 falset value zero.` [general/gl051.cbl:L176]. FINDING F-1: declared and NEVER
#: TESTED - not once in 1,282 lines.
_FALSET_VALUE: Final[int] = 0

#: `move 99999 to WS-Batch-Nos.` [general/gl051.cbl:L1072] - the sentinel `get-a-batch`
#: plants when the batch header cannot be found.
_BATCH_NOT_FOUND_SENTINEL: Final[int] = 99999

_Z_ALL_BATCHES: Final[int] = 99

#: `Page-Lines - 6` [general/gl051.cbl:L1060] against `Page-Lines - 12`
#: [general/gl051.cbl:L1111]. FINDING F-3.
_PAGE_BREAK_MARGIN_DETAIL: Final[int] = 6
_PAGE_BREAK_MARGIN_TOTALS: Final[int] = 12

#: `move 6 to line-cnt.` [general/gl051.cbl:L1087] - the number of lines a page of
#: headings has already consumed when `headings` returns.
_HEADING_LINE_COUNT: Final[int] = 6

_ACCOUNT_ERROR_MARKER: Final[str] = "^^^^^^^^^^"

#: The divisor of the three account-scaling `DIVIDE` statements INSIDE the
#: boundary - [general/gl051.cbl:L1035], [general/gl051.cbl:L1037] and
#: [general/gl051.cbl:L1044]. An account is held as `nnnnss` and shown as
#: `nnnn.ss`, so the scale factor is a hundred. The five scaling statements the
#: rest of the program has - [general/gl051.cbl:L604], [general/gl051.cbl:L607],
#: [general/gl051.cbl:L654], [general/gl051.cbl:L657] and
#: [general/gl051.cbl:L803] - are outside the boundary and are recorded in the
#: footer's OMISSIONS list rather than reproduced.
_ACCOUNT_SCALE: Final[int] = 100


@dataclass
class _WorkingStorage:
    """The `gl051` working-storage items the six in-scope paragraphs SHARE.

    COBOL's paragraphs all see one working storage, and this is that storage - nothing
    more. It exists because the alternative, passing eight mutable values by hand
    through eight function signatures, would obscure what the COBOL makes plain.
    """

    z: int = field(default_factory=lambda: move.move(move.Figurative.ZERO, _Z))

    #: `03 save-batch pic 9(5) comp value zero.` [general/gl051.cbl:L174].
    save_batch: int = field(
        default_factory=lambda: move.move(move.Figurative.ZERO, _SAVE_BATCH)
    )

    trutht: int = field(default_factory=lambda: move.move(_TRUET_VALUE, _TRUTHT))

    #: `03 line-cnt binary-char value zero.` [general/gl051.cbl:L166]. Question Q-8.
    line_cnt: int = field(
        default_factory=lambda: move.move(move.Figurative.ZERO, _LINE_CNT)
    )

    page_nos: int = field(
        default_factory=lambda: move.move(move.Figurative.ZERO, _PAGE_NOS)
    )

    l4_batch: str = field(
        default_factory=lambda: move.move(move.Figurative.ZERO, _L4_BATCH)
    )

    #: `03 dr-error pic x(12).` [general/gl051.cbl:L321] and `03 cr-error pic x(12).`
    #: [general/gl051.cbl:L322].
    dr_error: str = field(
        default_factory=lambda: move.move(move.Figurative.SPACE, _DR_ERROR)
    )
    cr_error: str = field(
        default_factory=lambda: move.move(move.Figurative.SPACE, _CR_ERROR)
    )

    ws_date_formats: WsDateFormats = field(default_factory=WsDateFormats)

    maps03_ws: Maps03Ws = field(default_factory=Maps03Ws)

    account_in: decimal.Decimal = field(
        default_factory=lambda: move.move(move.Figurative.ZERO, _ACCOUNT_IN)
    )
    array_pc: int = field(
        default_factory=lambda: move.move(move.Figurative.ZERO, _ARRAY_PC)
    )

    ws_vat_rate: decimal.Decimal = field(
        default_factory=lambda: move.move(move.Figurative.ZERO, _WS_VAT_RATE)
    )


@dataclass(frozen=True)
class _HandlerLinkage:
    """The five arguments every file-handler call in the facade copybook takes.

    Two of the five are this program's LINKAGE - `System-Record`
    [general/gl051.cbl:L348] and `File-Defs` [general/gl051.cbl:L349] - and three are
    its WORKING-STORAGE: `File-Access` from `copy "wsfnctn.cob"`
    [general/gl051.cbl:L129], `ACAS-DAL-Common-Data` from `copy "Test-Data-Flags.cob"`
    [general/gl051.cbl:L158], and the record buffer, which differs per entity.
    """

    system_record: SystemRecord
    posting: WsPostingRecord
    batch: GlBatchRecord
    ledger: WsLedgerRecord
    file_access: FileAccess
    file_defs: FileDefs
    dal_common: AcasDalCommonData


# ---------------------------------------------------------------------------
#  The four file-handler verbs this module performs - THREE READS AND THE REWRITE
# ---------------------------------------------------------------------------
# `batch-print` itself performs exactly three verbs and every one of them is a
# read: there is no write, no delete, no open and no close inside the report
# section; the opens are `gl050d`'s [general/gl051.cbl:L980-L981] and so are the
# closes [general/gl051.cbl:L989-L990].
#
# ⭐ THE FOURTH VERB IS `GL-Batch-Rewrite`, AND IT IS NOT OPTIONAL. The gate's one
# deliverable is `Batch-Status` on `GLBATCH-REC`, and a status that is only set in
# memory is not a database effect at all. In the frozen program the rewrite that
# persists it is UNCONDITIONAL in both of the gate's callers:
#
#     L415  perform  GL-Batch-Rewrite.       *> rewrite  batch-record..
#           - `gl051-Main` [general/gl051.cbl:L415], reached on EVERY path out of
#             its menu dispatch, including the `ws-menu = 3` path
#             [general/gl051.cbl:L400-L401] that performs `gl050d` and so reaches
#             `batch-print` and `end-batch`. There is NO path in `gl051-Main` on
#             which the gate runs and the rewrite does not follow it.
#     L491  perform  GL-Batch-Rewrite.       *> rewrite  batch-record..
#           - `proof-all` [general/gl051.cbl:L491], likewise unconditional for
#             every batch it proofs.
#
# Both callers are out of scope (Agent Action Plan section 0.4.2 puts `gl051-Main`
# §359 and `proof-all` §474 outside the boundary), and section 0.4.1.1 gives the
# migration no CLI entry point that dispatches `gl051` - the seven routes are the
# posting-cycle ones. So there is NO in-scope caller anywhere in the migration for
# the rewrite to live in, and omitting it would mean the migrated cycle NEVER
# records an accepted or rejected batch in the one table that decides whether the
# posting phases run at all. The control-total-mismatch scenario that section
# 0.8.5 mandates would then diff EMPTY ON BOTH SIDES FOR THE WRONG REASON: not
# because the two implementations agree, but because neither wrote anything.
#
# It is therefore performed HERE, by `run`, immediately after the section - which
# is exactly where both frozen callers perform it, and unconditionally, as both
# frozen callers do. This is the boundary being honest in the same way the four
# promoted preconditions are: the statement is out-of-boundary, so it is named,
# located, and reproduced at the position the source gives it, rather than
# silently dropped. AMBIGUITY Q-1 is thereby RESOLVED FROM THE SOURCE and no
# longer open: the question was where the rewrite belongs, and the answer is that
# every caller issues it unconditionally, so the gate's status ALWAYS reaches the
# row.
#
# Each verb gets its own adapter so that question Q-6 - the facade's Python call
# shape - has exactly four places to reconcile rather than five scattered call
# sites.


def _gl_posting_read_next(linkage: _HandlerLinkage) -> None:
    """`perform GL-Posting-Read-Next.` [general/gl051.cbl:L1008]."""
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
    """`perform GL-Batch-Read-Indexed.` [general/gl051.cbl:L1070]."""
    facade.gl_batch_read_indexed(
        facade.FacadeContext(
            linkage.system_record,
            linkage.batch,
            linkage.file_access,
            linkage.file_defs,
            linkage.dal_common,
        ),
    )


def _gl_batch_rewrite(linkage: _HandlerLinkage) -> None:
    """`perform GL-Batch-Rewrite.`  [general/gl051.cbl:L415] and L491.

    The facade paragraph, verbatim [copybooks/Proc-ACAS-FH-Calls.cob:L475-L478]:

         GL-Batch-Rewrite.
             move     zero to Access-Type.
             set      fn-Re-write to true.
             perform  acas007.

    ⭐ THE ONE DATABASE MUTATION OF THE WHOLE `gl051` BOUNDARY, and the statement
    that turns the control-total gate from an in-memory calculation into an
    observable effect on `GLBATCH-REC`. It writes back the batch record the gate
    just mutated, carrying `Batch-Status` - `88 Status-Closed value 1.`
    [copybooks/wsbatch.cob:L27] for an accepted batch, `88 Status-Open value 0.`
    [copybooks/wsbatch.cob:L26] for a rejected one.

    WHAT DEPENDS ON IT. `gl070`'s batch check reads this very field -
    `if status-open move 1 to a.` [general/gl070.cbl:L314-L315] - and on finding
    an open batch raises the terminate code [general/gl070.cbl:L289], which the
    posting-cycle route then honours as a hard gate so that `gl071` and `gl072`
    never run. Without this rewrite `gl070` would read whatever status the seed
    left, and the gate's verdict would change nothing anywhere.

    IT IS UNCONDITIONAL, exactly as both frozen callers are. The `z = 99`
    all-batches path leaves `Batch-Status` UNTOUCHED
    [general/gl051.cbl:L1099-L1100], so on that path this rewrite writes the row
    back with the value it already held - which is what the compiled program does
    too, since [general/gl051.cbl:L415] is not guarded. A rewrite of unchanged
    values leaves the row identical, so the state diff sees nothing, and section
    0.6.5's "clean rejection, no database effect" class is preserved.

    The reply is TESTED INLINE by the caller, because `gl051` copies
    [copybooks/Proc-ACAS-FH-Calls.cob], which declares no error-check paragraph -
    the same convention every other verb in this module follows.
    """
    facade.gl_batch_rewrite(
        facade.FacadeContext(
            linkage.system_record,
            linkage.batch,
            linkage.file_access,
            linkage.file_defs,
            linkage.dal_common,
        ),
    )


def _gl_nominal_read_indexed(linkage: _HandlerLinkage) -> None:
    """`perform GL-Nominal-Read-Indexed.` [general/gl051.cbl:L1142] and L1156."""
    facade.gl_nominal_read_indexed(
        facade.FacadeContext(
            linkage.system_record,
            linkage.ledger,
            linkage.file_access,
            linkage.file_defs,
            linkage.dal_common,
        ),
    )


# ---------------------------------------------------------------------------
#  The two date sections `batch-print` reaches - thin delegations to
#  `acas_posting.dates`
# ---------------------------------------------------------------------------
# EXACTLY TWO, and the count is a measurement rather than a choice. A census of
# every `perform` between [general/gl051.cbl:L999] and [general/gl051.cbl:L1166]
# - the whole of the in-scope boundary - returns nine statements and only nine:
# `GL-Posting-Read-Next`, `GL-Batch-Read-Indexed`, `GL-Nominal-Read-Indexed`
# twice, `headings` three times, `get-a-batch`, `get-description` and
# `zz060-Convert-Date` twice. So of the program's four date sections only
# `zz060-Convert-Date` is reachable from inside the boundary, and it reaches
# `maps03` [general/gl051.cbl:L1217]. Those two are here; `zz050-Validate-Date`
# [general/gl051.cbl:L1169] and `zz070-Convert-Date` [general/gl051.cbl:L1243]
# are not, and the OMISSIONS list in the footer records why.


#  maps03  section.  [general/gl051.cbl:L1273]


def _maps03(maps03_ws: Maps03Ws) -> None:
    """`maps03 section.` - the date-module wrapper [general/gl051.cbl:L1273-L1279].

    # ANOMALY A-22, OCCURRENCE 2 [general/gl051.cbl:L1273] and #
    [general/gl051.cbl:L1278] - the section is named after the INTERFACE # COPYBOOK it
    passes (`wsmaps03.cob` [general/gl051.cbl:L128]) while its exit # label is named
    after the PROGRAM it calls (`maps04` # [general/gl051.cbl:L1276]).

    Args:
        maps03_ws: `01 maps03-ws.` - `u-date` and `u-bin`, converted in place in
            whichever direction the caller has primed.
    """
    _dates_maps03(maps03_ws)
    # 1278  maps04-exit.
    # 1279      exit     section.   ->  fall out of the function.


#  zz060-Convert-Date  section.  [general/gl051.cbl:L1208]


def _zz060_convert_date(storage: _WorkingStorage, date_form: int) -> int:
    """`zz060-Convert-Date section.` [general/gl051.cbl:L1208-L1241].

    IT IS PRESERVED EVEN THOUGH ITS OUTPUT IS A PRINT FIELD, for two reasons. First it
    performs `maps03` [general/gl051.cbl:L1217], which reaches the date module.

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


# ---------------------------------------------------------------------------
#  batch-print  section.   [general/gl051.cbl:L999-L1166]
# ---------------------------------------------------------------------------


#  batch-print  section.  - the section's own entry statements
#  [general/gl051.cbl:L999-L1003]


def _batch_print(storage: _WorkingStorage, linkage: _HandlerLinkage) -> None:
    """`batch-print section.` - the section entry and its three-part body.

    THIS FUNCTION IS WHERE THE CLASS 2 `GO TO` IS MADE GOOD, and that is its most
    important job. `loop` leaves itself at [general/gl051.cbl:L1010] with `go to end-
    batch`, and section 0.6.3 is explicit about what that must become, verbatim.

    Args:
        storage: The section's shared working storage.
        linkage: The five handler arguments plus the records the section reads and the
            batch record whose `Batch-Status` it sets.
    """
    _headings(storage, linkage)

    linkage.batch.ws_batch_key.ws_ledger = move.move(
        values_for("GL-Batch")[0], _WS_LEDGER
    )

    _loop(storage, linkage)

    # 1096 end-batch. - THE CLASS 2 TARGET. The whole gate, placed after the loop rather
    # than inside it.
    _end_batch(storage, linkage)

    _batch_print_main_exit()


def _loop(storage: _WorkingStorage, linkage: _HandlerLinkage) -> None:
    """`loop.` - the read loop AND THE ACCUMULATION [general/gl051.cbl:L1005-L1065].

    CITES THEM. Without them the gate at [general/gl051.cbl:L1117-L1121] compares the
    operator's entered totals against zero and rejects every batch that has any value in
    it at all.

    Args:
        storage: The section's shared working storage - `z`, `save-batch`, `line-cnt`,
            the error markers and the date buffers.
        linkage: Supplies the posting the read fills; receives the accumulated totals on
            the batch record.
    """
    while True:
        _gl_posting_read_next(linkage)

        # 1009 if fs-reply = 10 1010 go to end-batch. GO TO class 2 - forward
        # terminator.
        if linkage.file_access.fs_reply == FsReply.END_OF_FILE:
            return

        # 1012 if batch = zero 1013 go to loop. GO TO class 1 - loop-back. A SILENT
        # SKIP.
        if arithmetic.compare(linkage.posting.ws_post_key.batch, 0) == 0:
            continue


        if (
            arithmetic.compare(storage.z, _Z_ALL_BATCHES) == 0
            and arithmetic.compare(
                storage.save_batch, linkage.posting.ws_post_key.batch
            )
            != 0
        ):
            (
                storage.l4_batch,
                storage.save_batch,
                linkage.batch.ws_batch_key.ws_batch_nos,
            ) = move.move_to_all(
                linkage.posting.ws_post_key.batch,
                (_L4_BATCH, _SAVE_BATCH, _WS_BATCH_NOS),
            )

            # 1018 perform get-a-batch Reads the header of the batch just named.
            _get_a_batch(storage, linkage)

            storage.maps03_ws.u_bin = move.move(
                linkage.batch.dates.entered, _U_BIN, sending_field=_ENTERED
            )

            # 1020 perform zz060-Convert-Date AMBIGUITY Q-7: the conversion can mutate
            # `Date-Form`, a `SYSTEM-REC` column, so the returned value is written back.
            linkage.system_record.system_data_block.date_form = _zz060_convert_date(
                storage, linkage.system_record.system_data_block.date_form
            )

            storage.line_cnt = arithmetic.add_to(
                2, receiver_value=storage.line_cnt, receiving=_LINE_CNT, rounded=False
            )

        elif arithmetic.compare(storage.z, _Z_ALL_BATCHES) == 0:
            # COBOL's explicit no-op. Written out rather than folded away, because
            # folding it turns a three-way into a two-way.
            pass

        # 1028 else 1029 if batch not = WS-Batch-Nos 1030 go to loop. GO TO class 1 -
        # loop-back.
        elif (
            arithmetic.compare(
                linkage.posting.ws_post_key.batch,
                linkage.batch.ws_batch_key.ws_batch_nos,
            )
            != 0
        ):
            continue

        # 1032 move post-number to l7-number. *> omitted ANOMALY A-21
        # [general/gl051.cbl:L1033] - a reference qualified with `in` because `Post-
        # Code` collides across three posting copybooks.

        # 1035  divide   post-dr  by  100  giving  l7-dr.
        # Presentation only: an account held as `nnnnss` shown as `nnnn.ss`. The
        # DIVIDE is reproduced because section 0.4.1.2's census names it, so the
        # truncation into the edited receiver is modelled; the RENDERING is
        # omitted - `cobol/move.py` declines the `zzz9.99b` picture because no
        # database write reaches it and no oracle experiment can observe it
        # (question Q-14). `DIVIDE a BY b GIVING c` means `c = a / b`.
        # The RESULT IS NOT BOUND. It was bound only so a log record could render
        # it, and that record is gone - it was report content naming three accounts.
        # The DIVIDE itself stays, because the census names it and because
        # `divide_by_giving` is where the truncation into the edited receiver is
        # modelled; discarding the value is what the frozen program does with it too,
        # since `l7-dr` is a print field nothing else reads.
        arithmetic.divide_by_giving(
            linkage.posting.post_dr, _ACCOUNT_SCALE, _L7_DR, rounded=False
        )

        # 1037  divide   post-cr  by  100  giving  l7-cr.     *> presentation only
        arithmetic.divide_by_giving(
            linkage.posting.post_cr, _ACCOUNT_SCALE, _L7_CR, rounded=False
        )

        # ANOMALY A-21 [general/gl051.cbl:L1044] - the same collision, qualified
        # with `of` this time: `divide vat-ac of WS-Posting-Record by 100 giving
        # l7-vat-ac.` Reproduced deliberately per R-4; DO NOT FIX.
        # 1044  divide   vat-ac of WS-Posting-Record by 100 giving l7-vat-ac.
        arithmetic.divide_by_giving(
            linkage.posting.vat_ac, _ACCOUNT_SCALE, _L7_VAT_AC, rounded=False
        )

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
        #  NO RECORD HERE. The three lines above are `write print-record`, and
        #  report formatting beyond a database effect is OUT OF SCOPE by Agent Action
        #  Plan section 0.2.2 - the migrated cycle produces no report at all, so
        #  turning the report BODY into log lines re-created, at a different
        #  destination, precisely the output the plan excludes. The record also named
        #  the batch number, the posting number and the debit, credit and VAT
        #  accounts, none of which the safe-event schema admits (CWE-532).

        storage.line_cnt = arithmetic.add_to(
            1, receiver_value=storage.line_cnt, receiving=_LINE_CNT, rounded=False
        )

        # 1054 perform get-description.
        _batch_print_get_description(storage, linkage)

        # 1056 if cr-error not = spaces 1057 or dr-error not = spaces 1058 write print-
        # record from line-error after 1 1059 add 1 to line-cnt.
        if storage.cr_error != move.move(
            move.Figurative.SPACE, _CR_ERROR
        ) or storage.dr_error != move.move(move.Figurative.SPACE, _DR_ERROR):
            storage.line_cnt = arithmetic.add_to(
                1, receiver_value=storage.line_cnt, receiving=_LINE_CNT, rounded=False
            )

        # 1060 if line-cnt > Page-Lines - 6 1061 perform headings. Arithmetic INSIDE a
        # relation condition.
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


        linkage.batch.amounts.actual_gross = arithmetic.add_to(
            linkage.posting.post_amount,
            receiver_value=linkage.batch.amounts.actual_gross,
            receiving=_ACTUAL_GROSS,
            rounded=False,
        )

        linkage.batch.amounts.actual_vat = arithmetic.add_to(
            linkage.posting.vat_amount,
            receiver_value=linkage.batch.amounts.actual_vat,
            receiving=_ACTUAL_VAT,
            rounded=False,
        )

        # 1065 go to loop. GO TO class 1 - loop-back.
        continue


def _get_a_batch(storage: _WorkingStorage, linkage: _HandlerLinkage) -> None:
    """`get-a-batch.` - the indexed batch-header read [general/gl051.cbl:L1067-L1072].

    Three statements, and the third is a trap worth naming. `21` is
    `FsReply.INVALID_KEY_ON_START` - the value this codebase actually returns for an
    indexed read that finds nothing.

    Args:
        storage: Unused by this paragraph's three statements; accepted so every in-scope
            paragraph has one shape. Its `save_batch` was set by the caller's `MOVE` at
            [general/gl051.cbl:L1017].
        linkage: Supplies the batch record the read fills and the reply it sets.
    """
    _gl_batch_read_indexed(linkage)

    if linkage.file_access.fs_reply == FsReply.INVALID_KEY_ON_START:
        linkage.batch.ws_batch_key.ws_batch_nos = move.move(
            _BATCH_NOT_FOUND_SENTINEL, _WS_BATCH_NOS
        )
        #  NO RECORD HERE. `move 99999 to WS-Batch-Nos.` [general/gl051.cbl:L1072]
        #  is one statement and it displays nothing: the whole in-scope span
        #  [general/gl051.cbl:L999-L1170] contains ZERO `display` statements, verified
        #  by census, so every record in this module was invented (R-4). That the rest
        #  of the batch is then skipped SILENTLY is the frozen behaviour, and
        #  announcing it would be the fix rule R-4 forbids.
    _ = storage


def _headings(storage: _WorkingStorage, linkage: _HandlerLinkage) -> None:
    """`headings.` - the page headings [general/gl051.cbl:L1074-L1094].

    * [general/gl051.cbl:L1082] performs `zz060`, which reaches the date module AND can
    mutate `Date-Form` on the system record - question Q-7. Dropping the call because
    its output is only printed would lose a database effect.

    Args:
        storage: Receives `page-nos`, `line-cnt`, `l4-batch` and the converted date;
            supplies `z`.
        linkage: Supplies `WS-Batch-Nos` and the batch header's `Entered` date, and
            carries the system record whose `Date-Form` may be mutated.
    """
    storage.page_nos = arithmetic.add_to(
        1, receiver_value=storage.page_nos, receiving=_PAGE_NOS, rounded=False
    )

    storage.l4_batch = move.move(
        linkage.batch.ws_batch_key.ws_batch_nos,
        _L4_BATCH,
        sending_field=_WS_BATCH_NOS,
    )

    storage.maps03_ws.u_bin = move.move(
        linkage.batch.dates.entered, _U_BIN, sending_field=_ENTERED
    )

    # 1082 perform zz060-Convert-Date. AMBIGUITY Q-7.
    linkage.system_record.system_data_block.date_form = _zz060_convert_date(
        storage, linkage.system_record.system_data_block.date_form
    )

    # 1083  move     ws-date  to  l4-date.          *> presentation only - omitted
    # 1085  write    print-record  from  line-1 after 1.
    # 1086  write    print-record  from  line-3 after 1.
    #  NO RECORD HERE. The two lines above are `write print-record` - page
    #  furniture - and report formatting beyond a database effect is out of scope
    #  (Agent Action Plan section 0.2.2). The record also named the batch number.

    storage.line_cnt = move.move(_HEADING_LINE_COUNT, _LINE_CNT)

    if arithmetic.compare(storage.z, _Z_ALL_BATCHES) != 0:
        storage.line_cnt = arithmetic.add_to(
            2, receiver_value=storage.line_cnt, receiving=_LINE_CNT, rounded=False
        )


def _end_batch(storage: _WorkingStorage, linkage: _HandlerLinkage) -> None:
    """`end-batch.` - THE CONTROL-TOTAL GATE [general/gl051.cbl:L1096-L1134].

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

    THIS PARAGRAPH SETS THE STATUS; `run` PERSISTS IT. `end-batch` writes
    `Batch-Status` on the in-memory batch record and performs no file verb at all,
    exactly as the frozen paragraph does. The `GL-Batch-Rewrite` that carries the
    field to `GLBATCH-REC` is at [general/gl051.cbl:L415] in `gl051-Main` and
    [general/gl051.cbl:L491] in `proof-all` - both UNCONDITIONAL, both immediately
    after the gate, and both out of scope - so `run` performs it once, at the same
    position, and `_gl_batch_rewrite` carries the argument. Question Q-1 is
    RESOLVED FROM THE SOURCE: there is no path in either caller on which the gate
    runs and the rewrite does not follow.

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
        linkage: Supplies the four control-total fields and `Page-Lines`; receives
            `Batch-Status` and the mutated `Actual-Gross`.
    """
    amounts: BatchAmounts = linkage.batch.amounts

    # 1099 if z = 99 1100 go to main-exit. GO TO class 3 - section exit. `Batch-Status`
    # IS DELIBERATELY NOT SET.
    if arithmetic.compare(storage.z, _Z_ALL_BATCHES) == 0:
        #  NO RECORD HERE. `if z = 99 go to main-exit.` is a test and a
        #  transfer; it displays nothing and writes nothing. This is one of the five
        #  rejection classes of Agent Action Plan section 0.6.5 - a CLEAN rejection
        #  with no database effect - and its whole observable content is that
        #  `Batch-Status` is left as it stood.
        return

    # 1101 if not truet 1102 move 0 to batch-status 1103 go to main-exit. THE ACCOUNT-
    # EXISTENCE REJECTION, and it happens BEFORE any total is compared.
    if arithmetic.compare(storage.trutht, _TRUET_VALUE) != 0:
        linkage.batch.batch_status = move.move(
            values_for("Status-Open")[0], _BATCH_STATUS
        )
        #  NO RECORD HERE. `move 0 to batch-status` then `go to main-exit`
        #  [general/gl051.cbl:L1102-L1103] carry no `display`. The rejection IS the
        #  `Batch-Status` this writes, which the caller and the database both see; a
        #  log line adds nothing to it and, at INFO, announced a rejection the frozen
        #  program announces only through the batch record - and it named the batch
        #  number (CWE-532).
        return

    # 1105  subtract input-vat  from  input-gross  giving  l9-amount.
    # `SUBTRACT a FROM b GIVING c` means `c = b - a`, so this is the net of VAT
    # the operator entered. Presentation only; reproduced because the census
    # names it, rendering omitted (question Q-14).
    # The RESULT IS NOT BOUND, for the reason the three DIVIDEs above give: it was
    # bound only so a log record could render it, and that record reproduced the proof
    # report's total lines. `l9-amount` is a print field nothing else reads, and the
    # SUBTRACT stays because the census names it and because `subtract_giving` is
    # where the truncation into the receiver is modelled.
    arithmetic.subtract_giving(
        amounts.input_vat,
        minuend=amounts.input_gross,
        receiving=_L9_AMOUNT,
        rounded=False,
    )
    # 1106 move input-vat to l9-vat. *> presentation only - omitted 1107 move actual-
    # gross to l10-amount. *> presentation only - omitted 1108 move actual-vat to
    # l10-vat.

    # 1109 add actual-vat to actual-gross. Section 0.6.4, verbatim: "the entered figure
    # is VAT-inclusive.
    amounts.actual_gross = arithmetic.add_to(
        amounts.actual_vat,
        receiver_value=amounts.actual_gross,
        receiving=_ACTUAL_GROSS,
        rounded=False,
    )

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
    #  NO RECORD HERE. The three lines above are `write print-record` - the
    #  proof report's own total lines - and the record reproduced their CONTENT: five
    #  monetary values, which the safe-event schema forbids outright (CWE-532). Report
    #  formatting beyond a database effect is out of scope (section 0.2.2), and the
    #  figures themselves are verifiable where they belong, in the table dump the
    #  scenario diff compares.

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
        #  NO RECORD HERE. THE GATE'S OUTCOME IS `Batch-Status`, and nothing
        #  else. [general/gl051.cbl:L1117-L1121] is an `if`, two `move`s and no
        #  `display`; the record announced the rejection at INFO and, to do it, named
        #  the batch number and all four control totals - four monetary values and a
        #  business key (CWE-532). The rejection is fully observable where the frozen
        #  program leaves it, in `GLBATCH-REC`, which is what the scenario diff for
        #  the control-total-mismatch case reads.


    # 1126  if       batch-status = 1
    # 1127           move  "* Batch Verified Ok *"  to  l11-status
    # 1128  else
    # 1129           move  "*  Batch In ERROR   *"  to  l11-status.
    # The status is READ BACK to choose the banner - print only, and worth keeping
    # as a log record because it is the operator-visible verdict. `= 1` is
    # `88 Status-Closed`, so the test goes through the condition-name vocabulary.
    #  NO RECORDS HERE, AND THE READ-BACK IS STILL REPRODUCED. The frozen
    #  `if batch-status = 1` [general/gl051.cbl:L1126] chooses between two
    #  twenty-one-character BANNER LITERALS and moves the chosen one into `l11-status`,
    #  a print field written by [:L1131]. That is report furniture, out of scope by
    #  section 0.2.2, and the two records that replaced it announced the verdict at
    #  INFO while naming the batch number (CWE-532). The condition itself is preserved
    #  because it is a frozen test, and `is_status_closed` keeps it going through the
    #  `88`-level vocabulary; it now selects between two banners that are not
    #  rendered, exactly as the surrounding `*> omitted` lines record.
    if is_status_closed(linkage.batch.batch_status):
        pass


    return


# get-description. [general/gl051.cbl:L1136] SECTION-QUALIFIED. `general/gl051.cbl`
# declares TWO paragraphs named `get-description.` - one at [general/gl051.cbl:L799],
# inside the OUT-OF-SCOPE `gl050c section.`, and this one at [general/gl051.cbl:L1136],
# inside `batch-print`.


def _batch_print_get_description(
    storage: _WorkingStorage, linkage: _HandlerLinkage
) -> None:
    """`get-description.` - the DR/CR existence check [general/gl051.cbl:L1136-L1164].

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
    sentinel `gl072` tests at [general/gl072.cbl:L306-L307], cited by the anomaly
    register as [general/gl072.cbl:L303-L304] - and NONE OF IT
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
        linkage: Supplies the posting's four account fields, receives the nominal key,
            and carries the `File-Access` block whose `We-Error` and `Fs-Reply` this
            paragraph writes and tests.
    """
    posting = linkage.posting
    ledger_key: WsLedgerKey = linkage.ledger.ws_ledger_key


    # 1138 move zero to we-error. A LOCAL 0-or-1 FLAG, not a handler code - see the
    # docstring. Deliberately NOT compared against any `WeError` member anywhere below.
    linkage.file_access.we_error = move.move(move.Figurative.ZERO, _WE_ERROR)

    ledger_key.ws_ledger_nos = move.move(
        posting.post_dr, _WS_LEDGER_NOS, sending_field=_POST_DR
    )
    ledger_key.ledger_pc = move.move(posting.dr_pc, _LEDGER_PC, sending_field=_DR_PC)

    _gl_nominal_read_indexed(linkage)

    if linkage.file_access.fs_reply == FsReply.INVALID_KEY_ON_START:
        linkage.file_access.we_error = move.move(_WE_ERROR_LOCAL_FAILURE, _WE_ERROR)

    if arithmetic.compare(linkage.file_access.we_error, 0) == 0:
        storage.dr_error = move.move(move.Figurative.SPACE, _DR_ERROR)
    else:
        storage.dr_error = move.move(_ACCOUNT_ERROR_MARKER, _DR_ERROR)
        storage.trutht = move.move(_FALSET_VALUE, _TRUTHT)
        #  NO RECORD HERE. `move "^^^^^^^^^^" to dr-error` writes a PRINT
        #  FIELD - the report's own not-found marker - and `move 0 to trutht` sets the
        #  flag `end-batch` rejects on. Neither displays anything. The record named
        #  the nominal account number and its profit-centre code (CWE-532), and the
        #  rejection it foreshadows is observable as `Batch-Status` in the table.


    linkage.file_access.we_error = move.move(move.Figurative.ZERO, _WE_ERROR)

    ledger_key.ws_ledger_nos = move.move(
        posting.post_cr, _WS_LEDGER_NOS, sending_field=_POST_CR
    )
    ledger_key.ledger_pc = move.move(posting.cr_pc, _LEDGER_PC, sending_field=_CR_PC)

    _gl_nominal_read_indexed(linkage)

    if linkage.file_access.fs_reply == FsReply.INVALID_KEY_ON_START:
        linkage.file_access.we_error = move.move(_WE_ERROR_LOCAL_FAILURE, _WE_ERROR)

    if arithmetic.compare(linkage.file_access.we_error, 0) == 0:
        storage.cr_error = move.move(move.Figurative.SPACE, _CR_ERROR)
    else:
        storage.cr_error = move.move(_ACCOUNT_ERROR_MARKER, _CR_ERROR)
        storage.trutht = move.move(_FALSET_VALUE, _TRUTHT)
        #  NO RECORD HERE, for the reason the debit half gives above: a print
        #  field and a flag, no `display`, and the record named the account.


# main-exit. [general/gl051.cbl:L1166] SECTION-QUALIFIED.


def _batch_print_main_exit() -> None:
    """`main-exit.` - the section terminator [general/gl051.cbl:L1166].

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

    It takes no arguments because the COBOL paragraph reads nothing, and it emits
    nothing: ``exit section`` is one statement that displays nothing, so a record
    announcing it was invented (R-4).
    """
    return


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

    WHAT THIS FUNCTION DELIVERS IS ONE FIELD, AND IT WRITES IT TO THE ROW:
    `Batch-Status` on `GLBATCH-REC`. `batch-print` itself performs exactly three
    file-handler verbs and every one of them is a READ - `GL-Posting-Read-Next`
    [general/gl051.cbl:L1008], `GL-Batch-Read-Indexed` [general/gl051.cbl:L1070]
    and `GL-Nominal-Read-Indexed` [general/gl051.cbl:L1142] and
    [general/gl051.cbl:L1156] - so the report section performs no mutation of its
    own.

    ⭐ `run` THEN PERFORMS `GL-Batch-Rewrite`, unconditionally, exactly where both
    frozen callers of the gate perform it: [general/gl051.cbl:L415] in
    `gl051-Main`, reached on every path out of its menu dispatch, and
    [general/gl051.cbl:L491] in `proof-all`. Both callers are out of scope
    (section 0.4.2) and section 0.4.1.1 gives the migration no CLI route that
    dispatches `gl051`, so there is nowhere else for it: omit it and the gate
    computes a verdict that no table records and no later phase can read, which
    would make the mandated control-total-mismatch scenario (section 0.8.5) diff
    empty on both sides for the wrong reason. `_gl_batch_rewrite` sets out the
    argument in full. Question Q-1 RESOLVED.

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
        ws_calling_data: `01 WS-Calling-Data.` [copybooks/wscall.cob:L6-L13], linkage
            parameter one.
        system_record: `SYSTEM-REC` [general/gl051.cbl:L348], linkage parameter two.
            Supplies `Page-Lines` for the two page-break tests and `Date-Form`, which
            the date sections MUTATE when it is zero - question Q-7.
        to_day: `01 to-day pic x(10).` [general/gl051.cbl:L351], linkage parameter three
            - the run date in DD/MM/CCYY form. `batch-print` itself never reads it.
        file_defs: `01 File-Defs.` [general/gl051.cbl:L349], linkage parameter four.
            Forwarded to every handler call unread, exactly as the facade copybook
            forwards it.
        posting: `01 WS-Posting-Record.` [general/gl051.cbl:L132] - the buffer `GL-
            Posting-Read-Next` fills.
        batch: `01 WS-Batch-Record.` [general/gl051.cbl:L131] - the source of the
            control totals AND the destination of `Batch-Status`. THE OUTPUT OF THIS
            FUNCTION IS A FIELD OF THIS RECORD.
        ledger: `01 WS-Ledger-Record.` [general/gl051.cbl:L130] - the buffer both `GL-
            Nominal-Read-Indexed` calls fill.
        file_access: `01 File-Access.` [copybooks/wsfnctn.cob:L23-L38] - carries `Fs-
            Reply`, tested after every verb, and `We-Error`, used by `get-description`
            as a local 0-or-1 flag.
        dal_common: `01 ACAS-DAL-Common-Data.` from `copy "Test-Data-Flags.cob"`
            [general/gl051.cbl:L158] - the logging switch, the fifth argument of every
            handler call.
        z: `03 z pic 99.` [general/gl051.cbl:L172]. Promoted out-of-boundary
            precondition; question Q-5.
        trutht: `03 trutht pic 9.` [general/gl051.cbl:L175]. Promoted out-of-boundary
            precondition, `move 1 to trutht.` [general/gl051.cbl:L967]; question Q-4.
        actual_gross: `05 Actual-Gross pic 9(9)v99.` [copybooks/wsbatch.cob:L43].
            Promoted out-of-boundary precondition, `move zero to actual-gross actual-
            vat.` [general/gl051.cbl:L982]; question Q-4.
        actual_vat: `05 Actual-Vat pic 9(9)v99.` [copybooks/wsbatch.cob:L44]. The other
            half of the same precondition.

    Returns:
        Nothing. COBOL sub-programs return through `goback` and communicate by mutating
            the records passed to them, and so does this.
    """
    # The five handler-call records. Defaulted rather than required so a caller holding
    # no prior state need not build them.
    posting = WsPostingRecord() if posting is None else posting
    batch = GlBatchRecord() if batch is None else batch
    ledger = WsLedgerRecord() if ledger is None else ledger
    file_access = FileAccess() if file_access is None else file_access
    dal_common = AcasDalCommonData() if dal_common is None else dal_common

    # BOUNDARY PRECONDITION [general/gl051.cbl:L982] `move zero to actual-gross actual-
    # vat.` - set by `gl050d`, immediately before `perform batch-print`
    # [general/gl051.cbl:L983].
    batch.amounts.actual_gross = move.move(actual_gross, _ACTUAL_GROSS)
    batch.amounts.actual_vat = move.move(actual_vat, _ACTUAL_VAT)

    storage = _WorkingStorage(
        z=move.move(z, _Z),
        trutht=move.move(trutht, _TRUTHT),
    )

    # BOUNDARY PRECONDITION [general/gl051.cbl:L980-L981] `perform GL-Nominal-Open-
    # Input.` and `perform GL-Posting-Open-Input.` are `gl050d`'s and are NOT
    # reproduced: the boundary contains no open and no close.
    linkage = _HandlerLinkage(
        system_record=system_record,
        posting=posting,
        batch=batch,
        ledger=ledger,
        file_access=file_access,
        file_defs=file_defs,
        dal_common=dal_common,
    )

    #  NO ENTRY TRACE. `batch-print section.` [general/gl051.cbl:L999] displays
    #  nothing, and the record named the two running control totals and the run date -
    #  accounting values and a date with business meaning, both forbidden (CWE-532).
    #  THE WHOLE OF THIS MODULE NOW EMITS NOTHING, and that is correct: a census of
    #  the in-scope span [general/gl051.cbl:L999-L1170] finds ZERO `display`
    #  statements and FIFTEEN `write print-record`, so every diagnostic this module
    #  used to emit was either invented (R-4) or a reproduction of report content that
    #  Agent Action Plan section 0.2.2 puts out of scope. The gate's outcome reaches
    #  the caller and the database through `Batch-Status`, which is where the frozen
    #  program puts it and what the scenario diff reads.

    _batch_print(storage, linkage)

    # 415  perform  GL-Batch-Rewrite.               *> rewrite  batch-record..
    # ⭐ THE GATE'S VERDICT REACHES THE ROW. Both frozen callers of the gate issue
    # this UNCONDITIONALLY immediately after it - `gl051-Main`
    # [general/gl051.cbl:L415] and `proof-all` [general/gl051.cbl:L491] - and both
    # are out of scope, so there is no other place in the migration for it. See
    # `_gl_batch_rewrite` for the full argument and for what `gl070` does with the
    # field. Without it, M-01: the gate would compute a verdict that no table ever
    # records and no later phase could ever read.
    _gl_batch_rewrite(linkage)

    # The reply is NOT tested after the rewrite, and nothing is reported. The
    # frozen caller tests nothing either [general/gl051.cbl:L415-L416]: it
    # proceeds straight to `GL-Batch-Close`, so a branch here would be a control
    # flow the source has not got. Nor is the outcome logged: the in-scope span
    # [general/gl051.cbl:L999-L1170] contains ZERO `display` statements, and a
    # record naming the batch key, the reply and `Batch-Status` would put an
    # accounting value into a diagnostic the frozen program never emits (R-4,
    # CWE-532). The verdict's observable is the row itself, which is what the
    # scenario diff reads.

    # BOUNDARY POSTCONDITION  [general/gl051.cbl:L416]
    # `perform GL-Batch-Close.` follows the rewrite in `gl051-Main`. NOT
    # reproduced, for the same reason the opens at [general/gl051.cbl:L980-L981]
    # are not: the file lifecycle is the caller's throughout, and this module
    # neither opens nor closes anything. The rewrite is different in kind - it is
    # a ROW MUTATION, the gate's own deliverable, and the only statement without
    # which the boundary produces no observable effect at all. AMBIGUITY Q-2.

    # `ws-calling-data` and `to-day` are declared by the `PROCEDURE DIVISION
    # USING` list and are not read by the boundary's own statements: the term
    # code that aborts the posting cycle is set by `gl070`
    # [general/gl070.cbl:L289] and the run date is consumed by
    # `zz070-Convert-Date` [general/gl051.cbl:L1251], which `batch-print` never
    # performs. Both are bound so the linkage shape is exact, and both are named
    # here so that no reader concludes a parameter was dropped.
    #
    # ⭐ `move u-bin to proofed.` [general/gl051.cbl:L413-L414] IS NOT REPRODUCED,
    # and the omission is deliberate rather than an oversight. It stamps the batch
    # header's proofed date from the run date and is carried by the SAME rewrite
    # above, so it looks at first like a companion effect that belongs here. It
    # does not: the statement is `gl051-Main`'s, it is guarded on `ws-menu not = 1`
    # - and `ws-menu` is written ONLY by out-of-scope interactive code - and
    # `end-batch` never touches `Proofed` on any path. Reproducing it would mean
    # inventing a `ws_menu` parameter and writing a field the in-scope paragraph
    # does not write, which rule R-3 forbids. Recorded in the OMISSIONS list.
    _ = (ws_calling_data, to_day)
