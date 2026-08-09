"""`gl080` - the General Ledger End Of Cycle Processing  [general/gl080.cbl].

The whole program, per Agent Action Plan section 0.2.1.1 - only `gl051` and
`irs030` are partial. So the archiving path `gl080b`/`arc-process`, the
interactive `disk-change` and `compress-post` are all migrated. Eight sections,
38 labels and 36 `GO TO` sites, six paragraphs named `loop.`, seven named
`main-exit.` and three named `end-run.`, which is why every function below is
section-qualified.

Entry point: `run(ws_calling_data, system_record, to_day, file_defs, ...)`, the
four-parameter General Ledger linkage shape.

PHASE LABELS, AND WHY THEY MISLEAD
==================================
    L306  "Phase - 1.  Batch Check"            L319  "Phase - 3.  Transaction Deletion"
    L316  "Phase - 2.  Transaction Archiving"  L637  "Phase - 4.  Posting Contraction "
    L336  "Phase - 5.  End of Period Processing"

Phase 1 and phase 4 each occur in a second program under the same number -
"Batch Check" in `gl070` [general/gl070.cbl:L284] over a DIFFERENT predicate,
and "Transaction Update" in `gl072` [general/gl072.cbl:L274]. Phase 3 is
labelled before phase 4 and runs before it. The labels are preserved because
Agent Action Plan section 0.6.4 asks for them "so a maintainer is not misled";
NOTHING below infers an ordering from a phase number. `archiving` is the
`88`-level over `Arch pic x` [copybooks/wssystem.cob:L164-L165], so archiving
and deletion are mutually exclusive - one `perform` or the other, never both.

`gl080b` AND `gl080c` HAVE IDENTICAL DATABASE EFFECTS
=====================================================
The key fact for reading a table dump of this program. Both walk the batch file
filtered on the cycle, delete every posting of the batch through
`GL-Posting-Delete` - [general/gl080.cbl:L513] archiving,
[general/gl080.cbl:L622] deletion - then stamp the header with the same three
moves, `move 2 to cleared-status` / `move run-date to stored` /
`move zero to batch-start`, and rewrite it [general/gl080.cbl:L430-L433],
[general/gl080.cbl:L585-L589]. The only difference is three rows per posting
written to a FLAT ARCHIVE FILE [general/gl080.cbl:L481], [general/gl080.cbl:L495],
[general/gl080.cbl:L508], which is not a schema table. IN AN
ORDERING-NORMALIZED TABLE-STATE DIFF THE TWO PATHS ARE INDISTINGUISHABLE, so a
scenario meaning to exercise archiving must pin `Arch` and assert on something
other than the tables. `gl072`'s parallel stamping [general/gl072.cbl:L375-L377]
differs in all three moves - 1 not 2, `posted` not `stored`, and `batch-start`
left alone - and that difference is preserved.

ONLY THREE THINGS REACH A TABLE
===============================
    1. `GL-Posting-Delete`, once per posting, on both paths. `gl080` is the only
       in-scope program that performs this verb.
    2. The batch stamping plus `GL-Batch-Rewrite`, once per batch in the cycle.
    3. Phase 5's `GL-Nominal-Rewrite` [general/gl080.cbl:L348], for EVERY
       nominal account the sequential walk reaches - a full-table update of
       `GLLEDGER-REC`.

Everything else - five sections of screen handling, path building and
diagnostics - has no database effect.

`compress-post` IS UNREACHABLE IN BOTH CONFIGURATIONS  (question Q-23)
======================================================================
Two gates stand in front of `loop1` [general/gl080.cbl:L654]. Against MySQL,
`not FS-Cobol-Files-Used` [general/gl080.cbl:L633-L635] is true - two `88`s over
one `pic 9` [copybooks/wssystem.cob:L113], [copybooks/wssystem.cob:L116] - so
the section returns at L634. In the Cobol-files configuration the record-size
test [general/gl080.cbl:L643-L649] is TRUE and `stop run` fires, because the two
lengths MEASURE 103 and 101: `WS-Posting-Record` [copybooks/wspost.cob:L12-L28]
sums to 103 over fifteen DISPLAY items, while `work-file-record` is
`pic x(101)` [general/gl080.cbl:L172] - the maintainer took the slipped "96
bytes" [copybooks/wspost.cob:L7] and added 5 for `WS-Post-rrn`, leaving the work
file two bytes short. `loop1`, `loop1-end`, `loop2`, `file-error` and `loop2-end`
are therefore unreachable either way. All are reproduced in full, and the two
lengths are COMPUTED FROM THE DESCRIPTORS rather than written as literals, so if
the oracle reports otherwise the code follows the dictionary. R-3 forbids
removing the gate and R-4 forbids tidying it.

`file-error.` [general/gl080.cbl:L688-L697] ends with a `display` and NO
transfer, so it FALLS THROUGH into `loop2-end.` [general/gl080.cbl:L699],
skipping `loop1-end`'s own closes [general/gl080.cbl:L670-L671] - it never
reopens the work file for input and never performs `GL-Posting-Open-Output`.
Each of the four `go to file-error` sites [general/gl080.cbl:L661],
[general/gl080.cbl:L664], [general/gl080.cbl:L681], [general/gl080.cbl:L685]
becomes an explicit two-call sequence carrying its own equivalence proof.

THREE PROMPTS PROMOTED TO CLI PARAMETERS  (Agent Action Plan section 0.3.4)
==========================================================================
    `run_confirmed`, default True - the run confirm [general/gl080.cbl:L299-L302].
        A, a or Escape returns BEFORE ANY WRITE OF ANY KIND.
    `disk_change_option`, default 0 - the `disk-change` option
        [general/gl080.cbl:L545-L547]. The clearest database-gating prompt in the
        folder: answering 9 leaves `a = 9`, which [general/gl080.cbl:L408-L409]
        tests to skip the whole archiving walk and [general/gl080.cbl:L324-L326]
        tests to skip the whole of phase 5. One keystroke suppresses the batch
        stamping, every posting delete, the quarter rollover and the cycle
        increment - ON AN ARCHIVING SYSTEM, AND ONLY THERE. `disk-change section.`
        [general/gl080.cbl:L519] is performed from exactly one site, L406 inside
        `gl080b`, which the test at [general/gl080.cbl:L315] reaches only when
        `Archiving` is on; the other arm performs `gl080c`
        [general/gl080.cbl:L318-L320] and never asks. So with archiving off the
        answer is never read, `a` keeps whatever `gl080a` left in it, and 9 and 0
        produce the SAME table state. Measured in both configurations.
    `archive_path_override`, default None - the archive path edit
        [general/gl080.cbl:L555]. Gates WHERE the flat archive file is written,
        so it has no table effect.

The other two `accept`s [general/gl080.cbl:L311-L312], [general/gl080.cbl:L648],
[general/gl080.cbl:L696] only block a terminal and are DROPPED; the control
transfers around them are PRESERVED.

ONE VARIABLE, THREE UNRELATED PURPOSES
======================================
`77 a pic 99` [general/gl080.cbl:L183] is the batch-check detector (zeroed L290,
set L386, tested L308), the `disk-change` abort code (accepted L545, tested L408
and L324) and the quarter subscript (computed L328, subscripted L345). `divide
scycle by period giving a rounded` [general/gl080.cbl:L328] OVERWRITES whatever
`a` held, including the 9 L324 has just tested. An abort of 9 returns at L324
before the clobber; a detector value of 1 fails L324 and IS clobbered. So it is
modelled as ONE field - splitting it into three well-named locals would be a
behaviour change disguised as a readability improvement. `77 y`
[general/gl080.cbl:L182] is the round-trip product, used at L329 and L331 only.

THE DETECTOR IS NOT `gl070`'S, AND NO TERM CODE IS SET
=====================================================
`gl080a` tests `if not status-closed and not processed` [general/gl080.cbl:L384-
L386] over `Cleared-Status` [copybooks/wsbatch.cob:L29-L32]; `gl070` tests
`if status-open` [general/gl070.cbl:L314-L315] over `Batch-Status`
[copybooks/wsbatch.cob:L25-L27]. Different fields, different predicates, not
interchangeable. And `gl080` sets NO term code - it displays and returns
[general/gl080.cbl:L313], [general/gl080.cbl:L366] - which is why the menu's
`load09.` [general/general.cbl:L817-L821] carries no `ws-term-code = 5` test
where `load08.` does [general/general.cbl:L810-L811]. Its aborts are all local:
`goback` L302, three `go to main-end` L313/L326/L332, one `stop run` L649.

TWO FLAT FILES, NEITHER A SCHEMA TABLE NOR A CYCLE WORK FILE
============================================================
`archive` on `file-2` [general/gl080.cbl:L138] and `work-file` on `file-21`
[general/gl080.cbl:L143]. Neither reaches the database, so neither appears in a
table dump; both are declared module-privately rather than added to the
package's work-file layer, for the three reasons in STRUCTURAL NOTES below -
`arc-trans-record` is a ten-field 78-byte layout in a different field order,
`work-file-record` is one unstructured `pic x(101)`, and that layer cannot
express `open extend` [general/gl080.cbl:L411]. `file-21` is `work.tmp`
[copybooks/file21.cob:L1], THE SAME NAME `gl071` GIVES ITS SORT WORK FILE
[general/gl071.cbl:L102] - a genuine collision, harmless only because the two
never run together and R-3 forbids concurrency. Both files declare `fs-reply`
[copybooks/wsfnctn.cob:L25] as their FILE STATUS, the very field the facade and
its handlers write, so a flat-file operation and a facade verb SHARE ONE STATUS
FIELD and each overwrites the other's reply. The sequences below therefore store
their status into the shared `File-Access` record, which is what a FILE STATUS
clause does.

ARITHMETIC, AND THE ONE `ROUNDED` SITE
======================================
`gl080` owns exactly one of the five `ROUNDED` sites in the whole migration, and
its un-`ROUNDED` companion is on the very next line:

    L328  divide   scycle by period giving a rounded    <-- THE ONLY ONE
    L329  multiply a by period giving y                     truncates
    L334  add      1 to scycle                              truncates
    L355  add      1 to current-quarter                     truncates
    L477  add      post-amount vat-amount giving arc-amount truncates
    L489  add      post-amount vat-amount giving arc-amount truncates
    L493  multiply arc-amount by -1 giving arc-amount       truncates
    L506  multiply arc-amount by -1 giving arc-amount       truncates
    L643  function length (...) twice - an integer count, no store

Every store other than L328 truncates toward zero, the COBOL default when
`ROUNDED` is absent. No `ON SIZE ERROR` and no `REMAINDER` phrase anywhere.
Every value is `Decimal` or `int` under the receiving item's descriptor, and per
Agent Action Plan section 0.3.1 no numeric primitive is hand-written here: scale
alignment, truncation, encoding, picture parsing, `MOVE` truncation, `88` tests,
`STRING`, reference modification and comparison all delegate to `cobol/`.

Anomalies reproduced, each annotated at its site: A-2 the unbounded quarter
subscript, A-3 the disagreeing notions of "current quarter", A-21 three
qualified references, and the two archive sign flips [general/gl080.cbl:L493],
[general/gl080.cbl:L506]. NOTHING is added that the frozen source does not do -
no bounds check on the subscript, no guard on `GL-Posting-Open-Output`, no
non-zero test before the L328 divide, no transaction wrapper around the
delete-then-stamp pairs. `compress-post` in particular looks like a hand-rolled
table rebuild begging for one SQL statement; it is not replaced.

IMPORTS AND WHAT IS ABSENT
==========================
Twelve `COPY` statements translate to `records/gl_ledger`, `records/gl_batch`,
`records/gl_posting` (which `gl072` does NOT copy), `records/test_data_flags`,
`records/file_access` plus `dal/status`, `records/calling_data`,
`records/system_record`, `records/file_defs` and `dal/facade`; `envdiv.cob` and
`screenio.cpy` are representation-only omissions and `FileStat-Msgs.cpy` becomes
`_evaluate_message`. Because the file copies `Proc-ACAS-FH-Calls.cob` and not
`Proc-ZZ100-ACAS-IRS-Calls.cob`, THIS PROGRAM USES THE ENTITY-NAMED FACADE
VOCABULARY AND TESTS THE REPLY INLINE - that copybook has no error-check
paragraph, so every `fs-reply` test below is the caller's own. Sixteen distinct
verbs are performed, the largest set of the twelve programs.
`acas_posting/workfiles.py` is NOT imported: `gl080` shares no work file with
`gl070`, `gl071` or `gl072`. No clock is read - `general/gl080.cbl` contains zero
clock reads, and `move run-date to stored` [general/gl080.cbl:L431],
[general/gl080.cbl:L586] writes the pinned `Run-Date binary-long`
[copybooks/wssystem.cob:L67] straight from the system record. There is no
`call "SYSTEM" using Print-Report` and no print file, so unlike `gl072` there is
no spool-out path to omit; the `STRING` in `disk-change`
[general/gl080.cbl:L531-L536] builds a file path and is never a command line.
`gl080` has no `zz050-Validate-Date` and no `zz060-Convert-Date` section, only
`zz070-Convert-Date` [general/gl080.cbl:L719], so anomaly A-22 does not occur
here.

AMBIGUITIES  (rule R-6)
=======================
Six questions, each annotated `AMBIGUITY Q-nn` at the site that raises it and
recorded in full in `docs/migration/ambiguity-resolutions.md`:

    Q-18  whether `move 1 to File-Key-No` [general/gl080.cbl:L288] has any
          observable effect, given the facade re-pins it. Reproduced regardless.
    Q-19  what the compiled program writes when the quarter subscript runs past
          the record - ANSWERED ON THE ORACLE; see A-2 at `_gl080_main_loop`.
    Q-20  whether `GL-Posting-Open-Output` [general/gl080.cbl:L673] truncates
          `GLPOSTING-REC` - SETTLED BY CONSTRUCTION, yes on both stores.
    Q-21  whether this program's six system-record mutations are persisted - the
          caller's side is settled: the menu shell rewrites the record in
          `overrewrite.` [general/general.cbl:L656-L692]. All six are reproduced
          in memory; none is written to a table from here (R-3).
    Q-22  what path the `disk-change` `STRING` builds. The maintainer flagged it
          himself: `*> this lot looks wrong !!!!!` [general/gl080.cbl:L530].
          Measured against the package's record defaults it is
          "archives archive.dat" - a space where a separator belongs.
    Q-23  whether `compress-post` aborts the run in the Cobol-files
          configuration - yes, per the section above.
"""

from __future__ import annotations

import dataclasses
import logging
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Final, Mapping

from acas_posting.dal import facade

from acas_posting.dal.status import FsReply

from acas_posting.cobol import arithmetic, condition_names, move, picture


# The unchecked subscript of [general/gl080.cbl:L345] is the one statement whose
# out-of-range occurrences land in bytes that belong to a `pic x(50)` FILLER
# rather than to a packed item, so its store has to be expressed as the byte
# image the compiled program lays down. `move.subscripted_store` over
# `_LEDGER_RECORD_GROUP` does that, reading every width from the record layer's
# own descriptors, so no storage class is decoded here and this module names no
# `usage` primitive of its own. See `_move_ledger_balance_to_quarter`.

# `descriptors_for_copybook_record` is imported as a BARE NAME rather than
# through its module, because `dataclasses.field` is already bound above and the
# module `acas_posting.cobol.field` would shadow it - or be shadowed by it -
# depending on import order. The two are unrelated and both are needed here, so
# neither is allowed to own the name.
from acas_posting.cobol.field import FieldDescriptor, descriptors_for_copybook_record

# copy "wscall.cob". [general/gl080.cbl:L263] `01 WS-Calling-Data`
# [copybooks/wscall.cob:L7-L14] - the first linkage parameter. `gl080` never reads or
# writes a field of it; see Q-21 and the OMISSIONS list.
from acas_posting.records.calling_data import WsCallingData

from acas_posting.records.file_defs import FileDefs

from acas_posting.records.file_access import FileAccess

from acas_posting.records.gl_batch import GlBatchRecord

# copy "wsledger.cob". [general/gl080.cbl:L188] `LedgerQuarters` is the four NAMED
# quarter fields and `LedgerQuartersTable` is the `occurs 4` view over the same bytes
# [copybooks/wsledger.cob:L31-L36].
from acas_posting.records.gl_ledger import (
    LedgerQuarters,
    LedgerQuartersTable,
    WsLedgerRecord,
)

# copy "wspost.cob". [general/gl080.cbl:L190] `gl080` DOES copy this, unlike `gl072`,
# because it reads the posting table through `acas006` rather than a work file.
from acas_posting.records.gl_posting import WsPostingRecord

from acas_posting.records.system_record import SystemRecord

from acas_posting.records.test_data_flags import AcasDalCommonData

# The house convention for attaching a `FieldDescriptor` to a dataclass attribute,
# borrowed from the package's work-record layouts so that the two module-private layouts
# below carry their provenance the same way every other record layout in the package
# does.
from acas_posting.records.work_records import COBOL_FIELD_METADATA_KEY

from acas_posting.dates import WsDateFormats, zz070_convert_date

#: The whole public surface: the program's single entry point, mirroring its
#: `PROCEDURE DIVISION USING` list [general/gl080.cbl:L269-L272]. Agent Action
#: Plan section 0.3.3, verbatim: "Each `programs/*.py` module exposes a single
#: `run(...)` entry mirroring its COBOL `PROCEDURE DIVISION USING` list, with
#: the paragraph functions private to the module. Callers cannot reach into a
#: program's internals, exactly as a COBOL `CALL` cannot." All 38 paragraph and
#: section functions are therefore private, and a tuple is used so the surface
#: cannot be extended in place at run time.
__all__: Final[tuple[str, ...]] = ("DiskChangeOptionNotAcceptable", "run")

_LOG: Final[logging.Logger] = logging.getLogger(__name__)


# WORKING-STORAGE FIELD DESCRIPTORS [general/gl080.cbl:L182-L187] Four `77`/`01` items
# of this program's own working storage receive a value below, so each needs the
# descriptor of the field that receives it (rule R-2.

# 183 77 a pic 99 value zero. PURPOSES in the module docstring.
_A: Final[FieldDescriptor] = picture.descriptor_for(
    "99 value zero", name="a", source_locator="general/gl080.cbl:L183", level="77"
)

_Y: Final[FieldDescriptor] = picture.descriptor_for(
    "99 value zero", name="y", source_locator="general/gl080.cbl:L182", level="77"
)

_WS_EVAL_MSG: Final[FieldDescriptor] = picture.descriptor_for(
    "x(25) value spaces",
    name="ws-eval-msg",
    source_locator="general/gl080.cbl:L185",
    level="77",
)

# 187 01 Arg-Test pic x(525) value spaces. The receiver of the `disk-change` `STRING`
# [general/gl080.cbl:L531-L536].
_ARG_TEST: Final[FieldDescriptor] = picture.descriptor_for(
    "x(525) value spaces",
    name="Arg-Test",
    source_locator="general/gl080.cbl:L187",
    level="01",
)

_FILE_2: Final[FieldDescriptor] = picture.descriptor_for(
    "x(532)", name="file-2", source_locator="copybooks/file02.cob:L1"
)


# COPYBOOK AND TABLE FIELD DESCRIPTORS - looked up, never transcribed Every field below
# that belongs to a copybook record or a table column takes its descriptor from the
# generated data dictionary, so no picture, scale, sign or usage is retyped here (rule
# R-5.

_SCYCLE: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "System-Record.Scycle"
)

#: `05 Current-Quarter pic 9.` [copybooks/wssystem.cob:L110] The SECOND, INDEPENDENT
#: notion of "current quarter" - anomaly A-3. Receives [general/gl080.cbl:L355] and
#: [general/gl080.cbl:L357].
_CURRENT_QUARTER: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "SYSTEM-REC.CURRENT-QUARTER"
)

#: `05 Date-Form pic 9.` [copybooks/wssystem.cob] THE FIFTH AND LAST SYSTEM-RECORD
#: MUTATION THIS PROGRAM MAKES, and the only one outside `gl080-Main`.
_DATE_FORM: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "SYSTEM-REC.DATE-FORM"
)

_LEDGER_BALANCE: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLLEDGER-REC.LEDGER-BALANCE"
)

_LEDGER_LAST: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLLEDGER-REC.LEDGER-LAST"
)

#: `05 Ledger-Q pic s9(8)v99 comp-3 occurs 4.` [copybooks/wsledger.cob:L36] - a
#: REDEFINES over `Ledger-Q1` through `Ledger-Q4` [copybooks/wsledger.cob:L31-L34].
_LEDGER_Q: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "WS-Ledger-Record.Ledger-Q"
)

#  THE REST OF `01 WS-Ledger-Record.` [copybooks/wsledger.cob:L12-L37]. Phase 5
#  needs the WHOLE record's layout, not only the fields it names, because
#  [general/gl080.cbl:L345] indexes `Ledger-Q` with an unbounded subscript and an
#  unbounded subscript reaches whatever field shares the bytes - see
#  `_LEDGER_RECORD_GROUP` and `_move_ledger_balance_to_quarter`.
_WS_LEDGER_NOS: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "WS-Ledger-Record.WS-Ledger-Nos"
)
_LEDGER_PC: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "WS-Ledger-Record.Ledger-PC"
)
_LEDGER_TYPE: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLLEDGER-REC.LEDGER-TYPE"
)
_LEDGER_PLACE: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLLEDGER-REC.LEDGER-PLACE"
)
_LEDGER_LEVEL: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLLEDGER-REC.LEDGER-LEVEL"
)
#: `03  filler  pic x(5).`  [copybooks/wsledger.cob:L26]
_LEDGER_FILLER_26: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "WS-Ledger-Record.filler#26"
)
_LEDGER_NAME: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLLEDGER-REC.LEDGER-NAME"
)
#: The four NAMED quarters [copybooks/wsledger.cob:L31-L34] - the same bytes the
#: `occurs` view above spans, and the fields the `acas005` handler binds its
#: columns from.
_LEDGER_Q1: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLLEDGER-REC.LEDGER-Q1"
)
_LEDGER_Q2: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLLEDGER-REC.LEDGER-Q2"
)
_LEDGER_Q3: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLLEDGER-REC.LEDGER-Q3"
)
_LEDGER_Q4: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLLEDGER-REC.LEDGER-Q4"
)
#: `03  filler  pic x(50).`  [copybooks/wsledger.cob:L37] - the trailing filler
#: an out-of-range quarter subscript of 5 or more lands in. No column, so no
#: table effect; it is modelled because the measurement showed the bytes DO
#: change and a reader must be able to see that they do.
_LEDGER_FILLER_37: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "WS-Ledger-Record.filler#37"
)

#: `03  Cleared-Status  pic 9.`  [copybooks/wsbatch.cob:L29]
#: Receives the value of `88 Archived value 2.` [copybooks/wsbatch.cob:L32] at
#: [general/gl080.cbl:L430] and [general/gl080.cbl:L585].
_CLEARED_STATUS: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLBATCH-REC.CLEARED-STATUS"
)

#: `05 Stored binary-long.` [copybooks/wsbatch.cob:L39] Receives `Run-Date`
#: [copybooks/wssystem.cob:L67] at [general/gl080.cbl:L431] and [general/gl080.cbl:L586]
#: - a controlled-clock observable written into a table column (rule R-6).
_STORED: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLBATCH-REC.STORED"
)

_BATCH_START: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLBATCH-REC.BATCH-START"
)

_WS_BATCH_NOS: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "WS-Batch-Record.WS-Batch-Nos"
)

#: The fourteen `WS-Posting-Record` fields the archive explosion reads
#: [copybooks/wspost.cob:L14-L28].
_POST_CODE: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLPOSTING-REC.POST-CODE"
)
_POST_DATE: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLPOSTING-REC.POST-DAT"
)
_POST_LEGEND: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLPOSTING-REC.POST-LEGEND"
)
_POST_DR: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLPOSTING-REC.POST-DR"
)
_DR_PC: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLPOSTING-REC.DR-PC"
)
_POST_CR: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLPOSTING-REC.POST-CR"
)
_CR_PC: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLPOSTING-REC.CR-PC"
)
_POST_AMOUNT: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLPOSTING-REC.POST-AMOUNT"
)
_VAT_AC: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLPOSTING-REC.VAT-AC"
)
_VAT_PC: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLPOSTING-REC.VAT-PC"
)
_VAT_AMOUNT: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLPOSTING-REC.VAT-AMOUNT"
)
_POST_NUMBER: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "WS-Posting-Record.Post-Number"
)
_POST_BATCH: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "WS-Posting-Record.Batch"
)

_FILE_KEY_NO: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "File-Access.File-Key-No"
)

#: `05 Lin2 pic 99.` [copybooks/wsfnctn.cob:L33], a redefines of `Curs2 pic 9(4)`
#: [copybooks/wsfnctn.cob:L31]. The receiver of [general/gl080.cbl:L291].
_LIN2: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "File-Access.Lin2"
)


# fd archive. [general/gl080.cbl:L156-L168] TEN fields, SEVENTY-EIGHT characters, and a
# field order that is NOT the order of the cycle's work records.

_ARC_BATCH: Final[FieldDescriptor] = picture.descriptor_for(
    "9(5)", name="arc-batch", source_locator="general/gl080.cbl:L159"
)
_ARC_POST: Final[FieldDescriptor] = picture.descriptor_for(
    "9(5)", name="arc-post", source_locator="general/gl080.cbl:L160"
)
_ARC_CODE: Final[FieldDescriptor] = picture.descriptor_for(
    "xx", name="arc-code", source_locator="general/gl080.cbl:L161"
)
_ARC_DATE: Final[FieldDescriptor] = picture.descriptor_for(
    "x(8)", name="arc-date", source_locator="general/gl080.cbl:L162"
)
_ARC_AC: Final[FieldDescriptor] = picture.descriptor_for(
    "9(6)", name="arc-ac", source_locator="general/gl080.cbl:L163"
)
_ARC_PC: Final[FieldDescriptor] = picture.descriptor_for(
    "99", name="arc-pc", source_locator="general/gl080.cbl:L164"
)
# Signed, scale 2, DISPLAY zoned with a trailing overpunched sign because the
# declaration carries no usage clause and no sign clause.
_ARC_AMOUNT: Final[FieldDescriptor] = picture.descriptor_for(
    "s9(8)v99", name="arc-amount", source_locator="general/gl080.cbl:L165"
)
_ARC_LEGEND: Final[FieldDescriptor] = picture.descriptor_for(
    "x(32)", name="arc-legend", source_locator="general/gl080.cbl:L166"
)
_ARC_C_AC: Final[FieldDescriptor] = picture.descriptor_for(
    "9(6)", name="arc-c-ac", source_locator="general/gl080.cbl:L167"
)
_ARC_C_PC: Final[FieldDescriptor] = picture.descriptor_for(
    "99", name="arc-c-pc", source_locator="general/gl080.cbl:L168"
)

_WORK_FILE_RECORD: Final[FieldDescriptor] = picture.descriptor_for(
    "x(101)",
    name="work-file-record",
    source_locator="general/gl080.cbl:L172",
    level="01",
)


@dataclass(slots=True)
class _ArcTransRecord:
    """`01 arc-trans-record.` - the flat archive row [general/gl080.cbl:L158].

    Attributes:
        arc_batch: `03 arc-batch pic 9(5).` Set once before the posting walk
            [general/gl080.cbl:L449] and then again per posting
            [general/gl080.cbl:L465].
        arc_post: `03 arc-post pic 9(5).` The posting number.
        arc_code: `03 arc-code pic xx.` Filled by a QUALIFIED move, anomaly A-21
            [general/gl080.cbl:L467].
        arc_date: `03 arc-date pic x(8).` EIGHT characters, inherited from `Post-Date
            pic x(8)` [copybooks/wspost.cob:L18]. Not a truncation of the ten-character
            run date, and the century is not restored.
        arc_ac: `03 arc-ac pic 9(6).` The account. SWAPPED with `arc_c_ac` between leg
            one and leg two.
        arc_pc: `03 arc-pc pic 99.` The profit centre, swapped likewise.
        arc_amount: `03 arc-amount pic s9(8)v99.` Signed, scale 2.
        arc_legend: `03 arc-legend pic x(32).` The narrative. DECLARED AFTER the amount,
            which is where this layout parts company with the cycle's work records.
        arc_c_ac: `03 arc-c-ac pic 9(6).` The contra account. No counterpart exists in
            `pre-trans-record`, so leg two's four-field swap has no analogue in
            `gl070`'s explosion.
        arc_c_pc: `03 arc-c-pc pic 99.` The contra profit centre. NOT reset by leg
            three, which leaves leg two's values standing [general/gl080.cbl:L501-L503].
    """

    arc_batch: int = field(default=0, metadata={COBOL_FIELD_METADATA_KEY: _ARC_BATCH})
    arc_post: int = field(default=0, metadata={COBOL_FIELD_METADATA_KEY: _ARC_POST})
    arc_code: str = field(
        default="  ", metadata={COBOL_FIELD_METADATA_KEY: _ARC_CODE}
    )
    arc_date: str = field(
        default=" " * 8, metadata={COBOL_FIELD_METADATA_KEY: _ARC_DATE}
    )
    arc_ac: int = field(default=0, metadata={COBOL_FIELD_METADATA_KEY: _ARC_AC})
    arc_pc: int = field(default=0, metadata={COBOL_FIELD_METADATA_KEY: _ARC_PC})
    arc_amount: Decimal = field(
        default=Decimal("0.00"), metadata={COBOL_FIELD_METADATA_KEY: _ARC_AMOUNT}
    )
    arc_legend: str = field(
        default=" " * 32, metadata={COBOL_FIELD_METADATA_KEY: _ARC_LEGEND}
    )
    arc_c_ac: int = field(default=0, metadata={COBOL_FIELD_METADATA_KEY: _ARC_C_AC})
    arc_c_pc: int = field(default=0, metadata={COBOL_FIELD_METADATA_KEY: _ARC_C_PC})


# THE TWO FLAT SEQUENCES [general/gl080.cbl:L138-L146], [L156-L172] Neither file is a
# schema table and neither is one of the cycle's work files, so neither can be served by
# the package's work-file layer - which publishes only `pre_trans`, `post_trans` and
# `sort_trans`, and whose open modes are deliberately limited to input and output with
# NO extend, while [general/gl080.cbl:L411] needs `open extend`.

#: File status "00" - successful completion.
_FS_OK: Final[int] = int(FsReply.SUCCESS)

_FS_AT_END: Final[int] = int(FsReply.END_OF_FILE)

#: File status "35" - an attempt to open a non-optional file that is not present.
_FS_FILE_NOT_FOUND: Final[int] = 35


class DiskChangeOptionNotAcceptable(ValueError):
    """The promoted disk-change option is neither 0 nor 9, which cannot happen.

    `accept-option.` [general/gl080.cbl:L542-L549] is an input loop with exactly
    two exits: `if a = 9 go to main-exit` [:L546-L547], a class-3 section exit that
    aborts the run, and falling through on zero, which proceeds. `if a not = zero
    go to accept-option` [:L548-L549] returns EVERY OTHER VALUE to the prompt. So
    no other value can reach the statements below the paragraph, and the value 9 is
    read twice more afterwards - at [general/gl080.cbl:L408] to skip the archiving
    walk and at [general/gl080.cbl:L324] to skip the whole of end-of-period
    processing.

    A THIRD VALUE THEREFORE HAS NO FROZEN BEHAVIOUR TO REPRODUCE, only a frozen
    IMPOSSIBILITY to preserve. The interactive re-prompt cannot be reproduced -
    Agent Action Plan section 0.4.2 places interactive retry targets outside the
    migrated surface - and of the two remaining dispositions, proceeding would let
    a value legacy execution can never carry here drive five tables' worth of
    end-of-period work. Refusing is the one that keeps the database effect inside
    the set the frozen program can produce.

    NOT A VALIDATION ADDED TO THE CYCLE (rule R-3): nothing is checked that the
    frozen source does not check, and the check is the frozen source's own
    `if a not = zero`. What changed is only the disposition of its true arm, from a
    re-prompt with no headless equivalent to a refusal.

    `acas_posting/cli/gl_end_of_cycle.py` restricts `--disk-change-option` to
    `{0, 9}`, so a command line reaches an argparse usage error first and this
    exception is the second gate, for a caller that reaches `run` directly.

    Attributes:
        option: the value as `77 a pic 99` [general/gl080.cbl:L183] received it,
            after that field's own truncation.
    """

    def __init__(self, option: int) -> None:
        """Build the refusal from the stored option value.

        Args:
            option: the value in `a` after the store through its descriptor.
        """
        super().__init__(
            f"the disk-change option is {option}, which general/gl080.cbl "
            f"L548-L549 sends back to the prompt: the frozen program can only "
            f"proceed on 0 or abort on 9, so no other value ever reaches the "
            f"archiving walk or end-of-period processing. Pass 0 to proceed or 9 "
            f"to abort."
        )
        self.option: int = option


class _StopRun(RuntimeError):
    """Reproduces `stop run.` [general/gl080.cbl:L649].

    THE ONE PLACE THIS PROGRAM TERMINATES THE RUN UNIT RATHER THAN RETURNING.
    """


class _SequentialFile:
    """One flat sequential file: its record area, its rows and its status.

    The base of the two `fd` entries this program declares.

    Args:
        name: The `assign` clause's file name, carried for diagnostics only.
        file_access: The `01 File-Access` record whose `Fs-Reply`
            [copybooks/wsfnctn.cob:L25] is this file's FILE STATUS.
    """

    __slots__ = ("_file_access", "_name", "_open", "_position", "_present", "_rows")

    def __init__(self, name: str, file_access: FileAccess) -> None:
        self._name = name
        self._file_access = file_access
        self._rows: list[object] = []
        self._position = 0
        self._open = False
        # A sequence that has never been opened for output stands for a file that is not
        # yet on disk, which is the state the archive is in the first time a scenario
        # runs.
        self._present = False

    @property
    def name(self) -> str:
        """The `assign` clause's file name."""
        return self._name

    @property
    def rows(self) -> tuple[object, ...]:
        """Every row written so far, in the order it was written."""
        return tuple(self._rows)

    def _reply(self, status: int) -> None:
        """Store a file status into the shared `Fs-Reply`, as FILE STATUS does."""
        self._file_access.fs_reply = status

    def open_input(self) -> None:
        """`open input <file>` - position at the first row, status 00."""
        self._position = 0
        self._open = True
        self._present = True
        self._reply(_FS_OK)

    def open_output(self) -> None:
        """`open output <file>` - CREATE OR TRUNCATE, then status 00."""
        self._rows.clear()
        self._position = 0
        self._open = True
        self._present = True
        self._reply(_FS_OK)

    def open_extend(self) -> None:
        """`open extend <file>` - append, or report file-not-found."""
        if not self._present:
            self._reply(_FS_FILE_NOT_FOUND)
            return
        self._position = len(self._rows)
        self._open = True
        self._reply(_FS_OK)

    def close(self) -> None:
        """`close <file>` - status 00. A closed file keeps its rows."""
        self._open = False
        self._reply(_FS_OK)


class _ArchiveFile(_SequentialFile):
    """`fd archive.` - the flat archive [general/gl080.cbl:L156-L168].

    `organization line sequential`, `access sequential`, status in `fs-reply`
    [general/gl080.cbl:L138-L141], assigned `file-2` [copybooks/file02.cob:L1]. Written
    only; this program never reads it back.

    Args:
        file_access: The record carrying this file's FILE STATUS.
    """

    __slots__ = ("record",)

    def __init__(self, file_access: FileAccess) -> None:
        super().__init__("archive", file_access)
        self.record = _ArcTransRecord()

    def write(self) -> None:
        """`write arc-trans-record.` - append a SNAPSHOT of the record area.

        Performed three times per posting [general/gl080.cbl:L481],
        [general/gl080.cbl:L495], [general/gl080.cbl:L508] against ONE record area, so
        each write must capture an INDEPENDENT COPY of the fields as they stand.
        """
        self._rows.append(dataclasses.replace(self.record))
        self._reply(_FS_OK)


class _WorkFile(_SequentialFile):
    """`fd work-file.` - the contraction scratch file [general/gl080.cbl:L170].

    Its record `01 work-file-record pic x(101).` [general/gl080.cbl:L172] is ONE
    UNSTRUCTURED ALPHANUMERIC ITEM, so the record area is a string of exactly 101
    characters and both the write and the read below are GROUP MOVES of raw characters
    rather than field-by-field transfers.

    Args:
        file_access: The record carrying this file's FILE STATUS.
    """

    __slots__ = ("posting_image", "record")

    def __init__(self, file_access: FileAccess) -> None:
        super().__init__("work-file", file_access)
        self.record: str = move.move_figurative(move.SPACE, _WORK_FILE_RECORD)
        self.posting_image: WsPostingRecord | None = None

    def write_from(
        self,
        posting: WsPostingRecord,
        *,
        image: str,
        group: FieldDescriptor,
    ) -> None:
        """`write work-file-record from WS-Posting-Record.`

        [general/gl080.cbl:L662]. The FROM phrase performs `MOVE WS-Posting-Record TO
        work-file-record` and then writes, so the move happens first.

        Args:
            posting: The sending group's current field values.
            image: The sending group's byte image, `group`'s width wide.
            group: The sending group's descriptor, so the unlike-picture rule is applied
                rather than guessed.
        """
        self.record = move.move(image, _WORK_FILE_RECORD, sending_field=group)
        self._rows.append((self.record, _copy_posting_record(posting)))
        self._reply(_FS_OK)

    def read(self) -> bool:
        """`read work-file at end ...` [general/gl080.cbl:L678].

        Returns:
            True when a row was read into the record area, False at end of file.
        """
        if self._position >= len(self._rows):
            self._reply(_FS_AT_END)
            return False
        area, snapshot = self._rows[self._position]
        self.record = str(area)
        self.posting_image = snapshot
        self._position = self._position + 1
        self._reply(_FS_OK)
        return True


def _copy_posting_record(posting: WsPostingRecord) -> WsPostingRecord:
    """An independent copy of `01 WS-Posting-Record.` [copybooks/wspost.cob:L12].

    `WRITE` publishes the record area's CURRENT contents, so a row must not alias the
    live record that the next `READ` overwrites - the same trap the archive's three
    writes carry [general/gl080.cbl:L481], [general/gl080.cbl:L495],
    [general/gl080.cbl:L508].

    Args:
        posting: The record area to snapshot.

    Returns:
        A copy that no later read can disturb.
    """
    return dataclasses.replace(
        posting, ws_post_key=dataclasses.replace(posting.ws_post_key)
    )


@dataclass(slots=True)
class _Gl080Storage:
    """This program's linkage, working storage, records and facade contexts.

    COBOL working storage is visible to every paragraph of the program, and eight
    sections here read and write the same handful of fields - `a` alone is touched by
    five of them.

    Attributes:
        ws_calling_data: `01 WS-Calling-Data` [copybooks/wscall.cob:L7-L14]. Accepted
            and never read - `gl080` sets no term code.
        system: `SYSTEM-REC`. Read for `Scycle`, `Period`, `Arch`, `Current-Quarter`,
            `Date-Form`, `Run-Date`, `Usera` and `File-System-Used`; MUTATED at six
            sites, question Q-21.
        to_day: `01 to-day pic x(10).` [general/gl080.cbl:L267], a DD/MM/CCYY text date
            and the only date input.
        file_defs: `01 File-Defs.` [copybooks/wsnames.cob:L13]. Supplies the two
            `assign` names and three of the four `STRING` sources.
        file_access: `01 File-Access` [copybooks/wsfnctn.cob:L22]. Carries `Fs-Reply`,
            which is BOTH the facade's status and both flat files' FILE STATUS.
        dal_common: `01 ACAS-DAL-Common-data.` [copybooks/Test-Data-Flags.cob], the
            logging switch every handler receives as its fifth argument.
        ledger: `WS-Ledger-Record` [copybooks/wsledger.cob], the record `acas005` reads
            and rewrites.
        batch: `WS-Batch-Record` [copybooks/wsbatch.cob], the record `acas007` reads and
            rewrites.
        posting: `WS-Posting-Record` [copybooks/wspost.cob], the record `acas006` reads,
            deletes, writes and rewrites.
        a: `77 a pic 99 value zero.` [general/gl080.cbl:L183]. ONE FIELD, THREE
            UNRELATED PURPOSES; see the module docstring. Modelled as one field because
            the sharing is observable.
        y: `77 y pic 99 value zero.` [general/gl080.cbl:L182].
        ws_eval_msg: `77 ws-eval-msg pic x(25).` [general/gl080.cbl:L185]. Diagnostic
            only; never tested, never stored to a table.
        ws_date_formats: The `01 ws-date-formats` redefines block
            [general/gl080.cbl:L222-L243] that `zz070-Convert-Date` fills.
        archive: `fd archive.` [general/gl080.cbl:L156].
        work_file: `fd work-file.` [general/gl080.cbl:L170].
        run_confirmed: The promoted run-confirm answer [general/gl080.cbl:L299-L302].
        disk_change_option: The promoted `disk-change` option
            [general/gl080.cbl:L545-L547].
        archive_path_override: The promoted archive path edit [general/gl080.cbl:L555],
            or None to keep what `disk-change` computes.
        dal_options: Forwarded verbatim to every handler as `FacadeContext.options`.
            Python plumbing with no COBOL counterpart; see `run`.
    """

    ws_calling_data: WsCallingData
    system: SystemRecord
    to_day: str
    file_defs: FileDefs
    file_access: FileAccess
    dal_common: AcasDalCommonData
    ledger: WsLedgerRecord
    batch: GlBatchRecord
    posting: WsPostingRecord
    a: int
    y: int
    ws_eval_msg: str
    ws_date_formats: WsDateFormats
    archive: _ArchiveFile
    work_file: _WorkFile
    run_confirmed: bool
    disk_change_option: int
    archive_path_override: str | None
    dal_options: Mapping[str, object]

    def nominal_ctx(self) -> facade.FacadeContext:
        """The `acas005` call block: `WS-Ledger-Record` is the record argument.

        `perform acas005.` [copybooks/Proc-ACAS-FH-Calls.cob] issues `call "acas005"
        using System-Record WS-Ledger-Record File-Access File-Defs ACAS-DAL-Common-
        Data`, and this is that parameter list in that order. A fresh context per verb
        is deliberate.
        """
        return facade.FacadeContext(
            system=self.system,
            record=self.ledger,
            file_access=self.file_access,
            file_defs=self.file_defs,
            dal_common=self.dal_common,
            options=self.dal_options,
        )

    def batch_ctx(self) -> facade.FacadeContext:
        """The `acas007` call block: `WS-Batch-Record` is the record argument."""
        return facade.FacadeContext(
            system=self.system,
            record=self.batch,
            file_access=self.file_access,
            file_defs=self.file_defs,
            dal_common=self.dal_common,
            options=self.dal_options,
        )

    def posting_ctx(self) -> facade.FacadeContext:
        """The `acas006` call block: `WS-Posting-Record` is the record argument."""
        return facade.FacadeContext(
            system=self.system,
            record=self.posting,
            file_access=self.file_access,
            file_defs=self.file_defs,
            dal_common=self.dal_common,
            options=self.dal_options,
        )


def _gl080_main(st: _Gl080Storage) -> None:
    """`gl080-Main section.` - setup, the confirm gate and the phase driver.

    Args:
        st: The program's storage. `st.a`, `st.y` and the system record are all mutated
            here.

    Raises:
        _StopRun: By way of `compress-post` [general/gl080.cbl:L649].
        DiskChangeOptionNotAcceptable: by way of `disk-change`
            [general/gl080.cbl:L519] when the disk-change option reaches neither
            exit of `accept-option.` [general/gl080.cbl:L542-L557] - see
            `_disk_change_accept_option`.
    """
    # 283 display prog-name at 0101 ... 284 display "End Of Cycle Processing" at 0130
    # ...
    _LOG.info("gl080 (3.3.00) - End Of Cycle Processing")

    # 285 perform zz070-convert-date. PRESERVED, not dropped with the display that
    # consumes it, because it MUTATES `Date-Form` on the system record when that field
    # is zero [general/gl080.cbl:L729-L730].
    _zz070_convert_date(st)

    # 286  display  ws-date at 0171 ...
    # 287  display  usera at 0301 ...
    #  NEITHER THE DATE NOR THE USER IS RECORDED. [general/gl080.cbl:L286-L287]
    # displays `ws-date` and `usera`: the posting date this run stamps into every record
    # it writes, and the OPERATOR'S USER ID. A date with business meaning and a user
    # identity are both excluded by the safe-event schema (CWE-532), and both are inputs
    # already known wherever the run was started.

    # 288 move 1 to File-Key-No. AMBIGUITY Q-18 - WHETHER THIS MOVE HAS ANY OBSERVABLE
    # EFFECT.
    st.file_access.logging_data.file_key_no = move.move(1, _FILE_KEY_NO)

    st.a = move.move_figurative(move.ZERO, _A)

    # 291 move scycle to lin2. Feeds the three "Cycle - " displays
    # [general/gl080.cbl:L402], [general/gl080.cbl:L566]. The DISPLAYS are dropped.
    st.file_access.curs2_parts.lin2 = move.move(
        st.system.system_data_block.scycle, _LIN2, sending_field=_SCYCLE
    )

    # 295 display GL085 at 0801 ... "Have you taken a backup?" 296 display GL086 at 0901
    # ... 297 display GL087 at 1001 ...
    _LOG.warning(
        "end of cycle processing is about to run - a backup should have been "
        "taken first"
    )

    # 298 move space to keyed-reply. 299 accept keyed-reply at 1065 with update auto.
    if not st.run_confirmed:
        # 302  goback.
        # NO RECORD HERE. [general/gl080.cbl:L299-L304] is `accept keyed-reply` then
        # `goback` - an ACCEPT and a transfer, with no `display` of its own. Agent
        # Action Plan section 0.3.4 makes the accept a CLI parameter, which it is, and
        # the transfer is preserved below; announcing the decision was invented (R-4).
        pass
        return

    _LOG.info("Phase - 1.  Batch Check")

    _gl080a(st)

    if arithmetic.compare(st.a, 1) == 0:
        # 309 display GL088 at 1501 ... "Batches outstanding" 310 display GL012 at 1701
        # ...
        _LOG.warning(
            "batches are outstanding for this cycle - end of cycle processing "
            "cannot run"
        )
        # 313 go to main-end. GO TO class 3 - a transfer to the section's terminal
        # paragraph, whose only statement is `goback.` [general/gl080.cbl:L366].
        _main_end(st)
        return

    # 315 if archiving `88 Archiving value "Y".` [copybooks/wssystem.cob:L165] over
    # `Arch pic x` [copybooks/wssystem.cob:L164].
    if condition_names.evaluate("Archiving", st.system.general_ledger_block.arch):
        _LOG.info("Phase - 2.  Transaction Archiving")
        _gl080b(st)
    else:
        _LOG.info("Phase - 3.  Transaction Deletion")
        _gl080c(st)

    # 322 perform compress-post. Phase 4, and see question Q-23.
    _compress_post(st)

    # 324 if a = 9 325 or scycle < period 326 go to main-end. `a` IN ITS SECOND ROLE:
    # the `disk-change` abort code [general/gl080.cbl:L545].
    if (
        arithmetic.compare(st.a, 9) == 0
        or arithmetic.compare(
            st.system.system_data_block.scycle, st.system.system_data_block.period
        )
        < 0
    ):
        # 326  go to  main-end.
        # GO TO class 3.
        #  NO RECORD HERE. The frozen statement this stood for displays nothing -
        # gl080's thirty-nine `display`s are all accounted for, and none of them is at
        # this site - so the record was invented (R-4). Progress and completion traces
        # of internal phase boundaries are not events the compiled program produces.
        # It also named the cycle and the period, which are business data.
        _main_end(st)
        return

    st.a = arithmetic.divide_by_giving(
        st.system.system_data_block.scycle,
        st.system.system_data_block.period,
        _A,
        rounded=True,
        receiver_value=st.a,
    )

    # 329 multiply a by period giving y.
    st.y = arithmetic.multiply_by_giving(
        st.a, st.system.system_data_block.period, _Y, rounded=False
    )

    # 331 if scycle not = y 332 go to main-end. THE PERIOD-BOUNDARY TEST: round-trip the
    # divide and compare.
    if arithmetic.compare(st.system.system_data_block.scycle, st.y) != 0:
        # 332  go to  main-end.
        # GO TO class 3.
        #  NO RECORD HERE. The frozen statement this stood for displays nothing -
        # gl080's thirty-nine `display`s are all accounted for, and none of them is at
        # this site - so the record was invented (R-4). Progress and completion traces
        # of internal phase boundaries are not events the compiled program produces.
        # It also named the cycle and the period.
        _main_end(st)
        return

    st.system.system_data_block.scycle = arithmetic.add_to(
        1, receiver_value=st.system.system_data_block.scycle, receiving=_SCYCLE
    )

    _LOG.info("Phase - 5.  End of Period Processing")

    facade.gl_nominal_open(st.nominal_ctx())

    # Control now FALLS THROUGH into `loop.` [general/gl080.cbl:L339], which is the next
    # paragraph of this same section.
    _gl080_main_loop(st)

    # 351 loop-end. THE POST-LOOP BLOCK OF THE CLASS-2 TRANSFER AT
    # [general/gl080.cbl:L344]. Agent Action Plan section 0.6.3, verbatim.
    _gl080_main_loop_end(st)

    _main_end(st)


def _gl080_main_loop(st: _Gl080Storage) -> None:
    """`loop.` - phase 5's walk over every nominal account.

    Args:
        st: The program's storage.

    Raises:
        Nothing on account of the quarter subscript. It is emphatically NOT
        validated - see anomaly A-2 at the subscripted move below. The compiled
        program was measured rather than reasoned about (rule R-6): a subscript
        outside 1 through 4 stores into whichever bytes the address computes,
        `Ledger-Last` at 0 and the trailing filler at 5 and 6, and the program
        RUNS ON with no diagnostic and no status. An exception here would replace
        a reproduced anomaly with an invented one (rules R-3, R-4), which is what
        question Q-19 asked and what the oracle answered.
    """
    while True:
        facade.gl_nominal_read_next(st.nominal_ctx())

        if arithmetic.compare(st.file_access.fs_reply, _FS_AT_END) == 0:
            break

        # 345  move     ledger-balance  to  ledger-q (a).
        #
        # ANOMALY A-2 [general/gl080.cbl:L328], [general/gl080.cbl:L345] - the
        # quarter subscript is computed by a `ROUNDED` divide and then used as a
        # table subscript with NO BOUNDS CHECK, against
        # `05 Ledger-Q pic s9(8)v99 comp-3 occurs 4.`
        # [copybooks/wsledger.cob:L36]. `a` is `pic 99`
        # [general/gl080.cbl:L183], so its declared domain is 0 through 99 and
        # only 1 through 4 are valid. An accounting cycle that is not a small
        # multiple of the period length silently indexes past a four-element
        # table. Reproduced deliberately per R-4; DO NOT FIX. No bounds test is
        # added, and none may be.
        #
        # HOW THE OUT-OF-RANGE STORE IS REPRODUCED. COBOL writes past the table
        # into whatever storage follows, silently and with no diagnostic, and in
        # THIS record what follows is declared: `filler pic x(50)`
        # [copybooks/wsledger.cob:L37]. `_move_ledger_balance_to_quarter`
        # therefore resolves the subscript to a BYTE OFFSET and stores into
        # whichever declared item those bytes belong to - the two `Quarters` views
        # for 1..4, the trailing filler for 5..12, the two preceding packed items
        # for 0 and -1 - so nothing is clamped, nothing is validated and control
        # flow continues exactly as the frozen loop's does. Note what is NOT done:
        # `ledger_q[a - 1]` would write QUARTER FOUR when `a` is zero, because
        # Python indexes backwards from the end, and that is a third behaviour
        # belonging to neither language.
        #
        # AMBIGUITY Q-19 - WHAT THE COMPILED PROGRAM WRITES PAST THE RECORD END,
        # NOW MEASURED (rule R-6). From `a = 13` the store runs beyond the 126th
        # byte into WORKING-STORAGE that belongs to no table. Driving GnuCOBOL
        # 3.2.0 with the record transcribed and a sentinel item declared
        # immediately after it put the six packed bytes at offsets 125 through
        # 130 - two in the trailing filler, four in the sentinel - left
        # `Ledger-Q1` through `Ledger-Q4` and `Ledger-Last` UNCHANGED, printed no
        # diagnostic and exited 0. So an overrunning run moves NO compared table,
        # and the reproduction below is complete for every observable: the
        # in-record bytes are written and the overrun is reported as a log line.
        _move_ledger_balance_to_quarter(st)

        # 346 if current-quarter = 4 ANOMALY A-3 [general/gl080.cbl:L345-L357] - TWO
        # DISAGREEING NOTIONS OF "CURRENT QUARTER" in one paragraph pair.
        if arithmetic.compare(st.system.system_data_block.current_quarter, 4) == 0:
            st.ledger.ledger_last = move.move(
                st.ledger.ledger_balance,
                _LEDGER_LAST,
                sending_field=_LEDGER_BALANCE,
            )

        facade.gl_nominal_rewrite(st.nominal_ctx())

        continue


#: `01 WS-Ledger-Record.` [copybooks/wsledger.cob:L12-L37] as the 126 BYTES the
#: compiled program addresses, in declaration order. It exists for exactly one
#: statement - `move ledger-balance to ledger-q (a).`
#: [general/gl080.cbl:L345] - because that statement's subscript is unbounded and
#: an unbounded subscript lands on BYTES, not on an attribute.
#:
#: The `occurs 4` view is spelled as its four occurrences so the layout reads the
#: way the storage is laid out; `Ledger-Q1` through `Ledger-Q4`
#: [copybooks/wsledger.cob:L31-L34] are the SAME bytes under their own names, so
#: they are not listed a second time. `WS-Ledger-Key9`
#: [copybooks/wsledger.cob:L21] and `Ledger-n`/`Ledger-s`
#: [copybooks/wsledger.cob:L17-L18] are likewise REDEFINES and not listed.
#:
#: THE LENGTH IS VERIFIED AGAINST THE COMPILED ORACLE, not asserted: GnuCOBOL
#: 3.2.0 reported `function length (WS-Ledger-Record)` = 126, which is also the
#: figure the maintainer's own change note gives
#: [copybooks/wsledger.cob:L10] ("Resized to 126 bytes").
_LEDGER_RECORD_GROUP: Final[move.StorageGroup] = move.StorageGroup(
    (
        move.GroupItem("WS-Ledger-Nos", _WS_LEDGER_NOS),
        move.GroupItem("Ledger-PC", _LEDGER_PC),
        move.GroupItem("Ledger-Type", _LEDGER_TYPE),
        move.GroupItem("Ledger-Place", _LEDGER_PLACE),
        move.GroupItem("Ledger-Level", _LEDGER_LEVEL),
        move.GroupItem("filler-26", _LEDGER_FILLER_26),
        move.GroupItem("Ledger-Name", _LEDGER_NAME),
        move.GroupItem("Ledger-Balance", _LEDGER_BALANCE),
        move.GroupItem("Ledger-Last", _LEDGER_LAST),
        move.GroupItem("Ledger-Q (1)", _LEDGER_Q1),
        move.GroupItem("Ledger-Q (2)", _LEDGER_Q2),
        move.GroupItem("Ledger-Q (3)", _LEDGER_Q3),
        move.GroupItem("Ledger-Q (4)", _LEDGER_Q4),
        move.GroupItem("filler-37", _LEDGER_FILLER_37),
    ),
    source_locator="copybooks/wsledger.cob:L12-L37",
)

#: Bytes per occurrence of `Ledger-Q`, i.e. the width of one
#: `pic s9(8)v99 comp-3` item [copybooks/wsledger.cob:L36]. Read from the
#: descriptor rather than written as a literal 6.
_LEDGER_Q_ELEMENT_BYTES: Final[int] = _LEDGER_Q1.byte_length

#: The four named quarter attributes of `03 Quarters.`
#: [copybooks/wsledger.cob:L30-L34], in declaration order - which is the order
#: the `occurs` view's occurrences map onto.
_LEDGER_QUARTER_ATTRS: Final[tuple[str, ...]] = tuple(
    f.name for f in dataclasses.fields(LedgerQuarters)
)


def _ledger_record_values(ledger: WsLedgerRecord) -> dict[str, object]:
    """The record's current contents, keyed the way the byte layout names them."""
    key = ledger.ws_ledger_key
    quarters = ledger.quarters
    return {
        "WS-Ledger-Nos": key.ws_ledger_nos,
        "Ledger-PC": key.ledger_pc,
        "Ledger-Type": ledger.ledger_type,
        "Ledger-Place": ledger.ledger_place,
        "Ledger-Level": ledger.ledger_level,
        "filler-26": ledger.filler_l26,
        "Ledger-Name": ledger.ledger_name,
        "Ledger-Balance": ledger.ledger_balance,
        "Ledger-Last": ledger.ledger_last,
        "Ledger-Q (1)": quarters.ledger_q1,
        "Ledger-Q (2)": quarters.ledger_q2,
        "Ledger-Q (3)": quarters.ledger_q3,
        "Ledger-Q (4)": quarters.ledger_q4,
        "filler-37": ledger.filler_l37,
    }


def _move_ledger_balance_to_quarter(st: _Gl080Storage) -> None:
    """`move ledger-balance to ledger-q (a).`  [general/gl080.cbl:L345].

    One COBOL statement with its own function, because of the target rather than
    the statement. In COBOL `Ledger-Q (a)` and `Ledger-Q1` through `Ledger-Q4` ARE
    THE SAME BYTES [copybooks/wsledger.cob:L31-L36]; in Python they are separate
    attributes that do not alias, and `acas_posting/records/gl_ledger.py`
    deliberately declines to synchronise them because keeping a redefines in step
    would be behaviour in a record layout (rule R-3). The consequence is concrete
    and silent: the `acas005` handler binds its columns from the FOUR NAMED
    FIELDS, so a value written into the `occurs` view alone would never reach
    `GLLEDGER-REC` and phase 5's entire table effect would vanish with no
    diagnostic. The COBOL names the `occurs` view, so BOTH views are written.

    For an in-range subscript the move's own semantics are unchanged: the value is
    stored into `Ledger-Q`'s picture, truncating toward zero because L345 carries
    no `ROUNDED`.

    ANOMALY A-2 - THE SUBSCRIPT IS NOT BOUNDS-CHECKED, AND MUST NOT BE
    (rules R-3, R-4). `a` is the `ROUNDED` quotient from
    [general/gl080.cbl:L328], guarded only by `if a = 9 or scycle < period`
    [general/gl080.cbl:L324-L326] and the exact-multiple test
    [general/gl080.cbl:L329-L332], and `77 a pic 99` [general/gl080.cbl:L183]
    admits 0..99. `scycle` is reset only for `period = 3` and `period = 13`
    [general/gl080.cbl:L358-L363]; for any other period - `period = 1` above all -
    nothing resets it and the quotient climbs through the whole domain. So the
    out-of-range case is REACHABLE, not theoretical. Raising would turn a silent
    legacy store into an abort that ends the phase-5 loop and changes the
    disposition of every ledger row after the first overrun. Instead the store is
    EMULATED BY BYTE ADDRESS, and control flow continues in every case. A Python
    `[a - 1]` is NOT used: that would make `a = 0` accumulate into the LAST
    occurrence, which corresponds to nothing the compiled program does.

    THE DESTINATION, BY BYTE OFFSET. `Ledger-Q` is `pic s9(8)v99 comp-3`, six
    bytes, `occurs 4` [copybooks/wsledger.cob:L36], redefining the 24 bytes of
    `Quarters` [copybooks/wsledger.cob:L30-L34]. The neighbouring declarations
    settle where an out-of-range occurrence lands
    [copybooks/wsledger.cob:L28-L37]::

        offset from Quarters   declaration                          reached by
        -12                    03  Ledger-Balance  s9(8)v99 comp-3  a = -1
         -6                    03  Ledger-Last     s9(8)v99 comp-3  a =  0
          0 .. 23              03  Quarters  (Ledger-Q1 .. Q4)      a = 1..4
         24 .. 73              03  filler    pic x(50)              a = 5..12
         74 and beyond         past the 126-byte record             a = 13..99

    `GLLEDGER-REC` has eleven columns and binds NONE of the trailing filler, so
    the four bands differ in observability:

        a = 1..4   the four quarter fields.      OBSERVABLE - LEDGER-Q1..Q4.
        a = 0      `Ledger-Last`, one field earlier in the record. OBSERVABLE -
                   LEDGER-LAST. Unreachable here because L325 forbids
                   `scycle < period`, but resolved rather than special-cased so
                   the emulation carries no bound of its own.
        a = 5..12  wholly inside the fifty-byte filler. NOT OBSERVABLE - all
                   eleven columns unchanged, and the row is still rewritten by
                   [general/gl080.cbl:L348]. This is the band A-2 actually
                   reaches: with `Period = 1` the guard passes for any `Scycle`,
                   L328 gives `a = Scycle` and L331 agrees, so `a` walks 5, 6, 7,
                   8, 10, 11, 12 as the cycles advance - `a = 9` alone is
                   unreachable because the guard tests it.
        a >= 13    at or past the record end. All eleven columns unchanged.

    AMBIGUITY Q-19, ANSWERED ON THE ORACLE (rule R-6). What the compiled
    program writes past the record end is not defined by the layout: GnuCOBOL
    compiled without bounds checking - and no compile line in this repository
    passes such a flag - stores into whatever WORKING-STORAGE follows. Measured
    against this copybook with a `pic x(20)` sentinel declared immediately after
    the record, `move 999.99 to ledger-q (13)` put the six packed bytes
    `00 00 00 99 99 9C` at 1-based offsets 125 through 130 - two in the filler,
    four in the sentinel - left `Ledger-Q1` through `Ledger-Q4` and `Ledger-Last`
    UNCHANGED, printed no diagnostic and exited 0; subscript 14 landed six bytes
    further on, so addressing stays linear rather than wrapping or clamping. An
    overrunning run therefore moves NONE of the 22 compared tables, which makes
    storing the in-record bytes and logging the remainder the whole behaviour.
    The one thing still not derivable is which `01` item receives the overrun
    bytes, and no column binds them either way.

    The occurrence count, the element width and the record's total width all come
    from the record layer's descriptors, so neither the bound, the stride nor the
    record length is a literal here.

    Args:
        st: The program's storage. `st.a` is the subscript and
            `st.ledger.ledger_balance` the sending field.
    """
    #  345  move     ledger-balance  to  ledger-q (a).
    #  The store is performed over the record's BYTES, because that is what
    #  the generated code addresses; `subscripted_store` returns every
    #  elementary item decoded afterwards, so whichever field shared the
    #  window is visible here exactly as the compiled program left it.
    after = move.subscripted_store(
        _LEDGER_RECORD_GROUP,
        _ledger_record_values(st.ledger),
        member="Ledger-Q (1)",
        element_length=_LEDGER_Q_ELEMENT_BYTES,
        subscript=st.a,
        value=move.move(
            st.ledger.ledger_balance, _LEDGER_Q, sending_field=_LEDGER_BALANCE
        ),
        statement="general/gl080.cbl:L345",
    )

    #  Write the whole record back from the image, because an out-of-range
    #  subscript changes a field the statement does not name - `Ledger-Last` for
    #  `a = 0`, the trailing filler for `a = 5` and above. Assigning only the
    #  quarters would silently discard the very effect being reproduced.
    st.ledger.ledger_last = after["Ledger-Last"]
    st.ledger.filler_l37 = after["filler-37"]

    #  The named fields those bytes carry, which is what the handler binds its
    #  columns from - and, in the same statement, the `occurs` view the COBOL
    #  statement itself names.
    quarter_values = tuple(
        after[f"Ledger-Q ({occurrence})"]
        for occurrence in range(1, len(_LEDGER_QUARTER_ATTRS) + 1)
    )
    for attribute, stored in zip(_LEDGER_QUARTER_ATTRS, quarter_values, strict=True):
        setattr(st.ledger.quarters, attribute, stored)
    st.ledger.quarters_table = LedgerQuartersTable(ledger_q=quarter_values)


def _gl080_main_loop_end(st: _Gl080Storage) -> None:
    """`loop-end.` - close the ledger and roll the quarter and the cycle.

    THE TWO CYCLE WRAPS ARE ASYMMETRIC AND BOTH ARE PRESERVED AS WRITTEN. Period 3 wraps
    above 12 and period 13 wraps above 52 - monthly and weekly accounting respectively -
    and no other period value wraps at all.

    Args:
        st: The program's storage. Four system-record fields are mutated here; see
            question Q-21.
    """
    facade.gl_nominal_close(st.nominal_ctx())

    # 355 add 1 to current-quarter. ANOMALY A-3's second notion of "current quarter",
    # rotated here independently of the subscript `a` that actually selected a field
    # [general/gl080.cbl:L345].
    st.system.system_data_block.current_quarter = arithmetic.add_to(
        1,
        receiver_value=st.system.system_data_block.current_quarter,
        receiving=_CURRENT_QUARTER,
    )

    if arithmetic.compare(st.system.system_data_block.current_quarter, 5) == 0:
        st.system.system_data_block.current_quarter = move.move(
            1, _CURRENT_QUARTER
        )

    if (
        arithmetic.compare(st.system.system_data_block.period, 3) == 0
        and arithmetic.compare(st.system.system_data_block.scycle, 12) > 0
    ):
        st.system.system_data_block.scycle = move.move(1, _SCYCLE)

    if (
        arithmetic.compare(st.system.system_data_block.period, 13) == 0
        and arithmetic.compare(st.system.system_data_block.scycle, 52) > 0
    ):
        st.system.system_data_block.scycle = move.move(1, _SCYCLE)


def _main_end(st: _Gl080Storage) -> None:
    """`main-end.` - the `goback` [general/gl080.cbl:L365-L366].

    THE PARAGRAPH'S ENTIRE BODY IS `goback.`, so this function's entire body is a
    `return`. A faithful one-to-one mapping and NOT a stub.

    Args:
        st: The program's storage, unchanged by this paragraph.
    """
    # 366  goback.
    #  NO RECORD HERE. The frozen statement this stood for displays nothing -
    # gl080's thirty-nine `display`s are all accounted for, and none of them is at
    # this site - so the record was invented (R-4). Progress and completion traces
    # of internal phase boundaries are not events the compiled program produces.
    # It also named the cycle and the current quarter - the latter being anomaly
    # A-3's own field, which is documented in `docs/migration/anomaly-log.md`.
    return


def _gl080a(st: _Gl080Storage) -> None:
    """`gl080a section.` - phase 1's detector [general/gl080.cbl:L368-L372].

    Args:
        st: The program's storage. Sets `st.a` when a batch is outstanding.
    """
    _LOG.info("checking batches")

    facade.gl_batch_open_input(st.batch_ctx())

    _gl080a_loop(st)

    _gl080a_end_run(st)

    _gl080a_main_exit(st)


def _gl080a_loop(st: _Gl080Storage) -> None:
    """`loop.` - one pass over the batch file [general/gl080.cbl:L374-L388].

    THE DETECTOR PREDICATE IS NOT `gl070`'S, and the difference is not cosmetic. `gl070`
    tests `if status-open` [general/gl070.cbl:L314] - one condition name over `Batch-
    Status` [copybooks/wsbatch.cob:L25-L27].

    Args:
        st: The program's storage.
    """
    while True:
        facade.gl_batch_read_next(st.batch_ctx())

        if arithmetic.compare(st.file_access.fs_reply, _FS_AT_END) == 0:
            break

        if (
            arithmetic.compare(
                st.batch.bcycle, st.system.system_data_block.scycle
            )
            != 0
        ):
            continue

        # 384 if not status-closed 385 and not processed Both through the condition-name
        # vocabulary: `88 Status-Closed value 1.` [copybooks/wsbatch.cob:L27] and `88
        # Processed value 1.` [copybooks/wsbatch.cob:L31].
        if not condition_names.is_status_closed(
            st.batch.batch_status
        ) and not condition_names.is_processed(st.batch.cleared_status):
            st.a = move.move(1, _A)

        continue


def _gl080a_end_run(st: _Gl080Storage) -> None:
    """`end-run.` - close the batch file [general/gl080.cbl:L390-L393].

    The post-loop block of [general/gl080.cbl:L379]. One statement, and losing it would
    leave the batch file open across the archiving or deletion walk that follows, both
    of which reopen it for update.

    Args:
        st: The program's storage.
    """
    facade.gl_batch_close(st.batch_ctx())


def _gl080a_main_exit(st: _Gl080Storage) -> None:
    """`main-exit. exit section.` [general/gl080.cbl:L395].

    ONE OF SEVEN paragraphs named `main-exit.` in this program - the others are at
    [general/gl080.cbl:L442], [general/gl080.cbl:L516], [general/gl080.cbl:L559],
    [general/gl080.cbl:L597], [general/gl080.cbl:L625] and [general/gl080.cbl:L705] -
    which is why every function in this module is section-qualified.

    Args:
        st: The program's storage, unchanged by this paragraph.
    """
    # 395  exit section.
    #  NO RECORD HERE. The frozen statement this stood for displays nothing -
    # gl080's thirty-nine `display`s are all accounted for, and none of them is at
    # this site - so the record was invented (R-4). Progress and completion traces
    # of internal phase boundaries are not events the compiled program produces.
    return


def _gl080b(st: _Gl080Storage) -> None:
    """`gl080b section.` - the archiving walk [general/gl080.cbl:L398-L415].

    THE EXTEND-THEN-FALLBACK IDIOM [general/gl080.cbl:L411-L414] is the maintainer's
    own, and his comment explains it: try to append, and if the status is non-zero close
    and open for output instead, which creates the file and truncates anything in it.

    Args:
        st: The program's storage.
    """
    # 401  display  "Archiving.      Cycle - " ...
    # 402  display  lin2 at 2330 ...            `lin2` was set at L291
    # 403  display  "/ Batch - " ...
    # 404  display  "/ Item  - " ...
    # Four displays that together build one progress line. One log record.
    #  THE CYCLE NUMBER IS NOT IN THE RECORD. The accounting cycle selects
    # which batches a run touches, so it is business data by the same rule that
    # excludes a batch number; the phase label is what the frozen `display` puts on
    # the screen alongside it and is kept.
    _LOG.info("Archiving.")

    _disk_change(st)

    if arithmetic.compare(st.a, 9) == 0:
        # 409 go to main-exit. GO TO class 3 - a transfer to this section's exit
        # paragraph. THE WHOLE ARCHIVING WALK IS SKIPPED.
        _gl080b_main_exit(st)
        return

    st.archive.open_extend()

    # 412 if fs-reply not = zero *> just in case extend wont create 413 close archive *>
    # a non-existent file 414 open output archive.
    if arithmetic.compare(st.file_access.fs_reply, _FS_OK) != 0:
        st.archive.close()
        st.archive.open_output()

    # 415 perform GL-Batch-Open. *> open i-o batch-file. OPENED FOR UPDATE, not for
    # input as `gl080a` did, because this walk rewrites every batch header it reads.
    facade.gl_batch_open(st.batch_ctx())

    _gl080b_loop(st)

    _gl080b_end_run(st)

    _gl080b_main_exit(st)


def _gl080b_loop(st: _Gl080Storage) -> None:
    """`loop.` - one batch per pass [general/gl080.cbl:L417-L434].

    [general/gl080.cbl:L585-L589], which is what makes the two paths indistinguishable
    in a table dump. It differs from `gl072`'s parallel stamping
    [general/gl072.cbl:L375-L377] in three ways at once.

    Args:
        st: The program's storage.
    """
    while True:
        facade.gl_batch_read_next(st.batch_ctx())

        if arithmetic.compare(st.file_access.fs_reply, _FS_AT_END) == 0:
            break

        if (
            arithmetic.compare(
                st.batch.bcycle, st.system.system_data_block.scycle
            )
            != 0
        ):
            continue

        _arc_process(st)

        facade.gl_posting_close(st.posting_ctx())

        # 430 move 2 to cleared-status. `88 Archived value 2.`
        # [copybooks/wsbatch.cob:L32].
        st.batch.cleared_status = _archived_status()

        # 431 move run-date to stored. (rule R-6). `Run-Date binary-long`
        # [copybooks/wssystem.cob:L67] is read from the system record that arrived
        # through linkage.
        st.batch.dates.stored = move.move(
            st.system.system_data_block.run_date, _STORED
        )

        st.batch.batch_start = move.move_figurative(move.ZERO, _BATCH_START)

        facade.gl_batch_rewrite(st.batch_ctx())

        continue


def _gl080b_end_run(st: _Gl080Storage) -> None:
    """`end-run.` - close the archive and the batch file.

    Args:
        st: The program's storage.
    """
    st.archive.close()

    facade.gl_batch_close(st.batch_ctx())


def _gl080b_main_exit(st: _Gl080Storage) -> None:
    """`main-exit. exit section.` [general/gl080.cbl:L442].

    The second of the seven `main-exit.` paragraphs. Reached two ways: by the class-3
    transfer at [general/gl080.cbl:L409] when the promoted `disk-change` option is 9,
    and by fall-through from `end-run.` [general/gl080.cbl:L440] otherwise.

    Args:
        st: The program's storage, unchanged by this paragraph.
    """
    # 442  exit section.
    #  NO RECORD HERE. The frozen statement this stood for displays nothing -
    # gl080's thirty-nine `display`s are all accounted for, and none of them is at
    # this site - so the record was invented (R-4). Progress and completion traces
    # of internal phase boundaries are not events the compiled program produces.
    return


def _archived_status() -> int:
    """The value of `88 Archived value 2.` [copybooks/wsbatch.cob:L32].

    `move 2 to cleared-status` [general/gl080.cbl:L430] and [general/gl080.cbl:L585]
    both write the literal the `Archived` condition name declares.

    Returns:
        The single declared value of the condition name, stored into `Cleared-Status pic
            9` [copybooks/wsbatch.cob:L29].
    """
    declared = condition_names.values_for("Archived")
    return move.move(declared[0], _CLEARED_STATUS)


def _arc_process(st: _Gl080Storage) -> None:
    """`arc-process section.` - explode, archive and delete one batch's postings.

    Note that `arc-batch` is set here from `WS-Batch-Nos` AND AGAIN inside the loop from
    `batch` [general/gl080.cbl:L465] - the posting record's own batch number, which the
    filter at [general/gl080.cbl:L460] has just proved equal to `WS-Batch-Nos`.

    Args:
        st: The program's storage.
    """
    # 448  display  WS-Batch-Nos at 2345 ...
    #  THE KEY IS NOT IN THE RECORD. The frozen `display` shows the batch or
    # posting number on a curses screen as a moving progress counter; a batch number
    # and a posting number are business keys, which the safe-event schema in
    # `acas_posting/dal/status.py` excludes (CWE-532). The progress display's only
    # purpose was to reassure an operator watching a terminal, and there is no
    # terminal; the rows themselves are what the scenario diff compares.

    st.archive.record.arc_batch = move.move(
        st.batch.ws_batch_key.ws_batch_nos,
        _ARC_BATCH,
        sending_field=_WS_BATCH_NOS,
    )

    facade.gl_posting_open(st.posting_ctx())

    _arc_process_loop(st)


def _post_key_is_zero(st: _Gl080Storage) -> bool:
    """`if WS-Post-Key = zero` - the unset-key filter of both posting passes.

    A GROUP COMPARED WITH `ZERO` IS A BYTE COMPARISON, measured on the compiled oracle
    (GnuCOBOL 3.2.0) with `WS-Post-Key` declared as [copybooks/wspost.cob:L14-L16]
    declares it: a group holding ten SPACES is NOT equal to `ZERO`, while a group holding
    ten `0` characters IS. A group has no numeric reading of its own, so the comparison
    is against the character `0` repeated across its width, which is the concatenation of
    each item's zero image.

    THE ELEMENTARY CASE IS THE OTHER WAY ROUND, which is why this is spelled out rather
    than inferred: `if batch = zero` on an elementary `pic 9(5)` item was measured
    NUMERIC in the same probe - a `Batch` of spaces IS zero - so a comparison of one item
    with `ZERO` stays with `arithmetic.compare`. `gl051` has that form
    [general/gl051.cbl:L1012] and this program has the group form twice.

    Args:
        st: The program's storage.

    Returns:
        True when the ten bytes of the group are all the character `0`.
    """
    key = st.posting.ws_post_key
    return (
        arithmetic.compare_zoned_display_fields(
            key.batch, 0, left_field=_POST_BATCH, right_field=_POST_BATCH
        )
        == 0
        and arithmetic.compare_zoned_display_fields(
            key.post_number, 0, left_field=_POST_NUMBER, right_field=_POST_NUMBER
        )
        == 0
    )


def _batch_is_not_the_one_being_processed(st: _Gl080Storage) -> bool:
    """`batch not = WS-Batch-Nos` - the gate both posting passes turn on.

    TWO SAME-PICTURE DISPLAY FIELDS COMPARE BYTE-WISE, measured on the compiled oracle;
    `arithmetic.compare_zoned_display_fields` carries the measurement and the reason a
    numeric comparison here is wrong. In this program it decides whether a posting is
    archived [general/gl080.cbl:L460] and whether it is deleted
    [general/gl080.cbl:L617]; `Batch` [copybooks/wspost.cob:L15] arrives from the bridge
    holding bytes its picture cannot produce (ANOMALY N-KEY), so for every posting read
    back from the database this is TRUE and neither pass touches the row - which is what
    the compiled program does, measured by statement count on both sides.

    Args:
        st: The program's storage.

    Returns:
        True when the posting belongs to some other batch, and so is passed over.
    """
    return (
        arithmetic.compare_zoned_display_fields(
            st.posting.ws_post_key.batch,
            st.batch.ws_batch_key.ws_batch_nos,
            left_field=_POST_BATCH,
            right_field=_WS_BATCH_NOS,
        )
        != 0
    )


def _arc_process_loop(st: _Gl080Storage) -> None:
    """`loop.` - the three-leg archive explosion, once per posting.

    1. THE TAX-SUPPRESSION TRANSFER GOES SOMEWHERE ELSE, AND IT MATTERS. `gl070` writes
    `go to loop` [general/gl070.cbl:L523], abandoning the record entirely. This section
    writes `go to by-pass` [general/gl080.cbl:L499], AND `by-pass` STILL PERFORMS `GL-
    Posting-Delete` [general/gl080.cbl:L513].

    Args:
        st: The program's storage.
    """
    while True:
        facade.gl_posting_read_next(st.posting_ctx())

        if arithmetic.compare(st.file_access.fs_reply, _FS_AT_END) == 0:
            # 457 go to main-exit. GO TO class 3 - a transfer to this section's exit
            # paragraph, which is `exit section.` [general/gl080.cbl:L516].
            _arc_process_main_exit(st)
            return

        # 459 if WS-Post-Key = zero 460 or batch not = WS-Batch-Nos 461 go to loop.
        # The same two disjuncts as `del-process` [general/gl080.cbl:L616-L618], so the
        # same two storage comparisons: a posting read back through the bridge is
        # archived by neither pass.
        if _post_key_is_zero(st) or _batch_is_not_the_one_being_processed(st):
            # 461 go to loop. GO TO class 1.
            continue

        # 463  display  post-number at 2364 ...
        #  THE KEY IS NOT IN THE RECORD. The frozen `display` shows the batch or
        # posting number on a curses screen as a moving progress counter; a batch number
        # and a posting number are business keys, which the safe-event schema in
        # `acas_posting/dal/status.py` excludes (CWE-532). The progress display's only
        # purpose was to reassure an operator watching a terminal, and there is no
        # terminal; the rows themselves are what the scenario diff compares.

        record = st.archive.record
        record.arc_batch = move.move(
            st.posting.ws_post_key.batch, _ARC_BATCH, sending_field=_POST_BATCH
        )
        record.arc_post = move.move(
            st.posting.ws_post_key.post_number,
            _ARC_POST,
            sending_field=_POST_NUMBER,
        )
        # ANOMALY A-21 [general/gl080.cbl:L467] - a QUALIFIED reference forced by a
        # field-name collision across three posting copybooks.
        record.arc_code = move.move(
            st.posting.post_code, _ARC_CODE, sending_field=_POST_CODE
        )
        record.arc_date = move.move(
            st.posting.post_date, _ARC_DATE, sending_field=_POST_DATE
        )
        record.arc_legend = move.move(
            st.posting.post_legend, _ARC_LEGEND, sending_field=_POST_LEGEND
        )

        record.arc_ac = move.move(
            st.posting.post_dr, _ARC_AC, sending_field=_POST_DR
        )
        record.arc_pc = move.move(
            st.posting.dr_pc, _ARC_PC, sending_field=_DR_PC
        )
        record.arc_c_ac = move.move(
            st.posting.post_cr, _ARC_C_AC, sending_field=_POST_CR
        )
        record.arc_c_pc = move.move(
            st.posting.cr_pc, _ARC_C_PC, sending_field=_CR_PC
        )

        if st.posting.post_vat_side == "CR":
            record.arc_amount = arithmetic.add_giving(
                st.posting.post_amount,
                st.posting.vat_amount,
                receiving=_ARC_AMOUNT,
            )
        else:
            record.arc_amount = move.move(
                st.posting.post_amount, _ARC_AMOUNT, sending_field=_POST_AMOUNT
            )

        st.archive.write()

        record.arc_ac = move.move(
            st.posting.post_cr, _ARC_AC, sending_field=_POST_CR
        )
        record.arc_pc = move.move(
            st.posting.cr_pc, _ARC_PC, sending_field=_CR_PC
        )
        record.arc_c_ac = move.move(
            st.posting.post_dr, _ARC_C_AC, sending_field=_POST_DR
        )
        record.arc_c_pc = move.move(
            st.posting.dr_pc, _ARC_C_PC, sending_field=_DR_PC
        )

        # 488 if post-vat-side = "DR" 489 add post-amount vat-amount giving arc-amount
        # 490 else 491 move post-amount to arc-amount.
        if st.posting.post_vat_side == "DR":
            record.arc_amount = arithmetic.add_giving(
                st.posting.post_amount,
                st.posting.vat_amount,
                receiving=_ARC_AMOUNT,
            )
        else:
            record.arc_amount = move.move(
                st.posting.post_amount, _ARC_AMOUNT, sending_field=_POST_AMOUNT
            )

        # 493 multiply arc-amount by -1 giving arc-amount.
        record.arc_amount = arithmetic.multiply_by_giving(
            record.arc_amount, -1, _ARC_AMOUNT
        )

        st.archive.write()

        # 497 if vat-ac of WS-Posting-Record equal zero 498 or vat-amount = zero 499 go
        # to by-pass.
        if (
            arithmetic.compare(st.posting.vat_ac, 0) == 0
            or arithmetic.compare(st.posting.vat_amount, 0) == 0
        ):
            # 499 go to by-pass. GO TO class 4 - SIBLING RE-DISPATCH, and the
            # equivalence proof matters here because the target is not an exit. PROOF.
            _arc_process_by_pass(st)
            continue

        # 501 move vat-ac of WS-Posting-Record to arc-ac. 502 move vat-pc to arc-pc. 503
        # move vat-amount to arc-amount. LEG THREE, the tax leg.
        record.arc_ac = move.move(
            st.posting.vat_ac, _ARC_AC, sending_field=_VAT_AC
        )
        record.arc_pc = move.move(
            st.posting.vat_pc, _ARC_PC, sending_field=_VAT_PC
        )
        record.arc_amount = move.move(
            st.posting.vat_amount, _ARC_AMOUNT, sending_field=_VAT_AMOUNT
        )

        if st.posting.post_vat_side == "CR":
            record.arc_amount = arithmetic.multiply_by_giving(
                record.arc_amount, -1, _ARC_AMOUNT
            )

        st.archive.write()

        # Control FALLS THROUGH into `by-pass.` [general/gl080.cbl:L510] - the same
        # paragraph the class-4 transfer above jumps to. Called explicitly so the fall-
        # through is visible rather than implied.
        _arc_process_by_pass(st)

        continue


def _arc_process_by_pass(st: _Gl080Storage) -> None:
    """`by-pass.` - delete the posting [general/gl080.cbl:L510-L513].

    THE ONE STATEMENT IN THIS SECTION THAT REACHES A TABLE, and `gl080` is the only in-
    scope program that performs this verb.

    Args:
        st: The program's storage.
    """
    facade.gl_posting_delete(st.posting_ctx())


def _arc_process_main_exit(st: _Gl080Storage) -> None:
    """`main-exit. exit section.` [general/gl080.cbl:L516].

    The third of the seven `main-exit.` paragraphs. Reached ONLY by the class-3 transfer
    at [general/gl080.cbl:L457]; this section has no fall-through path to its exit,
    because `by-pass` always transfers back to the loop head.

    Args:
        st: The program's storage, unchanged by this paragraph.
    """
    # 516  exit section.
    #  NO RECORD HERE. The frozen statement this stood for displays nothing -
    # gl080's thirty-nine `display`s are all accounted for, and none of them is at
    # this site - so the record was invented (R-4). Progress and completion traces
    # of internal phase boundaries are not events the compiled program produces.
    # It also named the batch number.
    return


def _disk_change(st: _Gl080Storage) -> None:
    """`disk-change section.` - build the archive path [general/gl080.cbl:L519].

    `*> this lot looks wrong !!!!!` [general/gl080.cbl:L530]. The same CHARACTER of
    finding as anomaly A-17 [sales/sl060.cbl:L1173], where he marked an unexplained move
    with a question mark, though this is not one of the register's twenty-two entries.

    Args:
        st: The program's storage. `st.a`, `st.file_defs.file_defs_a.file_2` and the
            local `Arg-Test` are written here.
    """
    # 530 move space to Arg-Test. NOT a clear-to-nothing.
    arg_test = move.move_figurative(move.SPACE, _ARG_TEST)

    # 531 string file-24 delimited by space *> spaces 532 "archives" delimited by size
    # 533 file-defs-os-delimiter 534 delimited by size 535 file-2 delimited by space *>
    # archive.dat 536 into Arg-Test.
    arg_test, _pointer = move.string_into(
        arg_test,
        (
            (st.file_defs.file_defs_a.file_24, move.DELIMITED_BY_SPACE),
            ("archives", move.DELIMITED_BY_SIZE),
            (st.file_defs.file_defs_os_delimiter, move.DELIMITED_BY_SIZE),
            (st.file_defs.file_defs_a.file_2, move.DELIMITED_BY_SPACE),
        ),
    )

    st.file_defs.file_defs_a.file_2 = move.move(
        arg_test, _FILE_2, sending_field=_ARG_TEST
    )

    # 539  display  GL085 at 1201 ...
    # 540  display  Gl084 at 1301 ...
    # `GL084` [general/gl080.cbl:L252] and `GL085` [general/gl080.cbl:L253].
    #  THE PATH IS NOT IN THE RECORD. `File-2` is an absolute filesystem path
    # from the deployment's own configuration [copybooks/wsnames.cob], which the
    # safe-event schema excludes (CWE-532) and which differs between environments, so
    # a record naming it could not be identical across two runs of one scenario.

    # Fall-through into `accept-option.` [general/gl080.cbl:L542].
    #
    # THE THIRD ANSWER NEVER GETS BACK HERE. `accept-option.`
    # [general/gl080.cbl:L548-L549] sends any value that is neither 9 nor zero
    # straight back to its own prompt, so the frozen paragraph cannot reach
    # `main-exit` [general/gl080.cbl:L559] on it and NOTHING after `perform
    # disk-change.` [general/gl080.cbl:L406] executes - not the archive open at
    # L411, not the batch walk, not the batch stamps at L426-L430, not
    # `compress-post` at L322 and not phase 5. `_disk_change_accept_option`
    # reproduces that by raising `DiskChangeOptionNotAcceptable` at the point the
    # frozen paragraph refuses to leave, which is why only the two answers the
    # frozen program can proceed on are returned here (CWE-636).
    declined = _disk_change_accept_option(st)

    if declined:
        # 547  go to  main-exit.
        # GO TO class 3, raised inside `accept-option` and carried out here. The
        # option value 9 has already been stored into `a`, which
        # [general/gl080.cbl:L408] and [general/gl080.cbl:L324] both read.
        _disk_change_main_exit(st)
        return

    _disk_change_main_exit(st)


def _disk_change_accept_option(st: _Gl080Storage) -> bool:
    """`accept-option.` - the option and the path edit.

    [general/gl080.cbl:L542-L557].

        542  accept-option.
        545      accept   a at 1369.
        546      if       a = 9
        547               go to  main-exit.
        548      if       a  not = zero
        549               go to  accept-option.
        553      display  "Current path/name is :" at 1401 ...
        554      display  file-2             at 1501 ...
        555      accept   file-2             at 1501 with ... update.
        556      if       file-2 (1:1) = space
        557               go to accept-option.

    TWO PROMPTS, TWO DIFFERENT TREATMENTS, BOTH DECIDED BY WHETHER THEY GATE A
    DATABASE WRITE (Agent Action Plan section 0.3.4).

    [general/gl080.cbl:L545] GATES DATABASE WRITES, and it is the clearest such
    prompt in the General Ledger folder. The value it accepts lands in `a`, and
    the value 9 is then read TWICE - at [general/gl080.cbl:L408], which skips the
    entire archiving walk, and at [general/gl080.cbl:L324], which skips the
    entire end-of-period section. One keystroke therefore suppresses every batch
    stamp, every posting delete, the ledger-quarter rollover and the cycle
    increment. Promoted to the `disk_change_option` parameter with the COBOL's
    proceed answer, zero, as the default.

    [general/gl080.cbl:L555] gates only WHERE THE FLAT ARCHIVE FILE IS WRITTEN.
    That file is not a table, so this prompt has no table effect at all.
    Promoted to `archive_path_override`, defaulting to None, which keeps the
    path [general/gl080.cbl:L537] computed.

    THERE ARE EXACTLY TWO WAYS OUT OF THIS PARAGRAPH, AND EVERY OTHER ANSWER
    LEAVES CONTROL INSIDE IT FOREVER, which is why this function returns a
    THREE-STATE disposition rather than a boolean. Reading the transfers as a
    graph:

        L546-L547   a = 9                              -> main-exit    DECLINED
        L548-L549   a not = zero                       -> accept-option (loop)
        L556-L557   file-2 (1:1) = space               -> accept-option (loop)
        fall-through, i.e. a = 0 AND the path is good  -> main-exit    ACCEPTED

    So an option that is neither 0 nor 9, and a path override whose first
    character is a space, BOTH return the operator to the option prompt. From
    there the only exits are the same two. THE COMPILED PROGRAM CANNOT REACH
    `main-exit` ON EITHER OF THOSE ANSWERS, so it cannot reach anything after
    `perform disk-change.` [general/gl080.cbl:L406] either - not the archive open,
    not the batch walk, not `compress-post` [general/gl080.cbl:L322] and not phase
    5. Warning and then continuing with the computed path reaches a state the frozen
    program has no path to, which is a
    behaviour change and, at CWE-636, a fail-open one: the answer the operator was
    never allowed to give would have authorised a full-table archive, a posting
    delete and the period rollover.

    THE THREE DISPOSITIONS AND THEIR DATABASE EFFECTS, which differ from each
    other and must (Agent Action Plan section 0.6.5):

      ACCEPTED   `a = 0` and the path's first character is not a space. Archiving
                 proceeds: `open extend archive` [general/gl080.cbl:L411], the
                 batch walk, `arc-process`, the batch stamps at
                 [general/gl080.cbl:L426-L430], then `compress-post` and phase 5.
      DECLINED   `a = 9`. `gl080b` reads it at [general/gl080.cbl:L408] and skips
                 the entire archiving walk, and the main section reads THE SAME
                 VALUE at [general/gl080.cbl:L324] and skips the entire
                 end-of-period section. `compress-post` [general/gl080.cbl:L322]
                 still runs. One keystroke, two suppressions.
      REFUSED    any other answer. Control never leaves `accept-option`, so
                 NOTHING after [general/gl080.cbl:L406] runs at all - including
                 the `if a = 9` test itself. The effect is the ABSENCE of
                 everything below, and it is reproduced by raising
                 `DiskChangeOptionNotAcceptable` from here rather than returning:
                 there is no disposition to return, because the frozen paragraph
                 has no exit to take.

    THE RETRY LOOPS THEMSELVES ARE STILL DROPPED, and only they are: a parameter
    cannot be re-prompted, and Agent Action Plan section 0.4.2 puts interactive
    retry targets outside the migrated surface "except where one gates a database
    write, in which case it is treated as Class 4". Both of these gate database
    writes, so both are Class 4: the LOOP goes and the DECISION stays, and the
    decision here is that control does not proceed.

    Args:
        st: The program's storage. Writes `st.a`, and `file-2` when the override is
            accepted.

    Returns:
        `True` when the operator declined archiving (`a = 9`), `False` when the
        run proceeds (`a = 0`). A Python function cannot transfer into its
        caller, so the answer is returned and `_disk_change` carries out the
        transfer.

    Raises:
        DiskChangeOptionNotAcceptable: the option is neither 0 nor 9, which is
            the answer the frozen paragraph re-prompts on for ever.
    """
    # 545 accept a at 1369. `a` IN ITS SECOND ROLE.
    st.a = move.move(st.disk_change_option, _A)

    if arithmetic.compare(st.a, 9) == 0:
        # 547  go to  main-exit.
        # GO TO class 3, carried out by the caller.
        # NO RECORD HERE. [general/gl080.cbl:L543-L546] is `accept a` and two
        # transfers, with no `display` of its own; the ACCEPT is a CLI parameter per
        # Agent Action Plan section 0.3.4 and the transfer is preserved. Announcing the
        # decision was invented (R-4).
        return True

    # 548  if       a  not = zero
    # 549           go to  accept-option.
    # GO TO class 1 over an INTERACTIVE RETRY. The loop is dropped with the
    # prompt; what it guaranteed - THAT CONTROL LEAVES THIS PARAGRAPH ONLY WHEN
    # THE OPTION IS 9 OR ZERO - is preserved by FAILING CLOSED on any other value.
    #
    # FAILING CLOSED RATHER THAN WARNING AND PROCEEDING. Logging a warning and
    # falling through would let a third value carry on into the archiving walk and
    # the whole of end-of-period processing - every batch stamp, every posting
    # delete, the ledger-quarter rollover and the cycle increment.
    # THE FROZEN PROGRAM CANNOT REACH THAT STATE: L548-L549 sends any
    # value that is neither 9 nor zero straight back to L542, so the code below
    # this paragraph only ever runs with `a` at zero. Proceeding on a third value
    # was therefore not permissiveness but ADDED BEHAVIOUR, and behaviour that
    # writes to five tables (rule R-3).
    #
    # This is not a validation added to the cycle either. It is the one disposition
    # the frozen loop leaves for a value that can never leave it: an interactive
    # re-prompt has no parameter equivalent (Agent Action Plan section 0.4.2 puts
    # interactive retry targets outside the migrated surface), and of the two
    # remaining possibilities - proceed, or refuse - only refusing keeps the
    # database effect the frozen program can produce. The entry point restricts
    # the option to {0, 9} as well, so this raise is the second gate for a caller
    # that reaches `run` directly.
    if arithmetic.compare(st.a, 0) != 0:
        raise DiskChangeOptionNotAcceptable(st.a)

    # 553  display  "Current path/name is :" at 1401 ...
    # 554  display  file-2             at 1501 ...
    #  THE PATH IS NOT IN THE RECORD. `File-2` is an absolute filesystem path
    # from the deployment's own configuration [copybooks/wsnames.cob], which the
    # safe-event schema excludes (CWE-532) and which differs between environments, so
    # a record naming it could not be identical across two runs of one scenario.
    _LOG.info("Current path/name is :")

    # 555  accept   file-2             at 1501 with ... update.
    # 556  if       file-2 (1:1) = space
    # 557           go to accept-option.
    #
    # The `with update` phrase means the field is presented holding its current
    # value and the operator edits it, so an operator who simply presses return
    # accepts the computed path - which is why NOT supplying an override is
    # ACCEPTED and not UNRESOLVED. `archive_path_override is None` is that
    # operator.
    #
    # AN OVERRIDE OVERWRITES IN PLACE; IT DOES NOT REPLACE THE FIELD. Question
    # `Q-GL084-ACCEPT-SEMANTICS` asked whether typed text REPLACES the presented
    # content or is INSERTED into it, and the compiled answer is NEITHER: it
    # overwrites from position 1 and leaves everything beyond what was typed
    # exactly as the field already held it. MEASURED (2026-08-08) on the harness
    # image's own `cobc (GnuCOBOL) 3.2.0` over a real 24x80 pty, with the frozen
    # declaration `03 file-2 pic x(532) value "archive.dat"`
    # [copybooks/file02.cob:L1] and the frozen statement form
    # [general/gl080.cbl:L555]: a field presented holding `archives/archive.dat`
    # and given the two keystrokes `XY` followed by Return came back holding
    # `XYchives/archive.dat`, and the same field given a BARE Return came back
    # unchanged. So an override shorter than the computed path leaves the
    # computed path's tail in place, and an EMPTY override is the bare Return.
    #
    # This function used to assign the override as a whole-field `MOVE`, which is
    # a THIRD reading - the operator typing and then clearing the tail - and one
    # no probe could make the compiled accept produce. Reproducing what was
    # measured rather than what was assumed is rule R-6; carrying the whole-field
    # replacement would be added behaviour under rule R-3. The path is a flat
    # file and not a schema table, so no scenario diff can see the difference,
    # which is precisely why it had to be measured rather than inferred from a
    # green run. The register records the reading and its bound.
    if st.archive_path_override is not None and st.archive_path_override != "":
        # 555 accept file-2 ... with update. The typed characters overwrite the
        # leading positions of the field's presented content; the rest stands.
        typed = move.move(
            st.archive_path_override,
            picture.descriptor_for(
                f"x({len(st.archive_path_override)})",
                name="file-2-typed",
                source_locator="general/gl080.cbl:L555",
            ),
        )
        candidate = move.ref_mod_into(
            st.file_defs.file_defs_a.file_2, 1, len(typed), typed
        )
        # 556 if file-2 (1:1) = space ONE-BASED reference modification, delegated. Never
        # a Python slice.
        if move.ref_mod(candidate, 1, 1) == " ":
            # 557  go to accept-option.
            # GO TO class 1 over an interactive retry. The re-prompt is dropped;
            # the REJECTION is kept, and rejecting means the computed path
            # stands. No table is affected either way.
            # NO RECORD HERE. `if file-2 (1:1) = space go to accept-option`
            # [general/gl080.cbl:L556-L557] is a test and a transfer that display
            # nothing, and the record named the path it was keeping (CWE-532). The
            # transfer itself is preserved.
            pass
        else:
            st.file_defs.file_defs_a.file_2 = candidate
            #  THE PATH IS NOT IN THE RECORD. `File-2` is an absolute filesystem path
            # from the deployment's own configuration [copybooks/wsnames.cob], which the
            # safe-event schema excludes (CWE-532) and which differs between environments, so
            # a record naming it could not be identical across two runs of one scenario.

    return False


def _disk_change_main_exit(st: _Gl080Storage) -> None:
    """`main-exit. exit section.` [general/gl080.cbl:L559].

    The fourth of the seven `main-exit.` paragraphs. Reached two ways: by the class-3
    transfer at [general/gl080.cbl:L547] when the option is 9, and by fall-through from
    [general/gl080.cbl:L557] otherwise.

    Args:
        st: The program's storage, unchanged by this paragraph.
    """
    # 559  exit section.
    #  NO RECORD HERE. The frozen statement this stood for displays nothing -
    # gl080's thirty-nine `display`s are all accounted for, and none of them is at
    # this site - so the record was invented (R-4). Progress and completion traces
    # of internal phase boundaries are not events the compiled program produces.
    return


def _gl080c(st: _Gl080Storage) -> None:
    """`gl080c section.` - Phase 3, delete without archiving.

    [general/gl080.cbl:L562-L597]. The `else` branch of the phase driver's `if
    archiving` [general/gl080.cbl:L315-L320]: performed when the system record's archive
    switch is not set, so the cycle's postings are discarded rather than written out
    first.

    Args:
        st: The program's storage.
    """
    # 565  display  "Deleting.       Cycle - " at 2301 ...
    # 566  display  lin2 at 2330 ...            `lin2` was set at L291
    # 567  display  "/ Batch - " at 2334 ...
    # 568  display  "/ Item  - " at 2352 ...
    # Screen furniture with no database effect, so log records (Agent Action
    # Plan section 0.3.4). They must not alter control flow, and they do not.
    #  THE CYCLE NUMBER IS NOT IN THE RECORD. The accounting cycle selects
    # which batches a run touches, so it is business data by the same rule that
    # excludes a batch number; the phase label is what the frozen `display` puts on
    # the screen alongside it and is kept.
    _LOG.info("Deleting.")

    facade.gl_batch_open(st.batch_ctx())

    _gl080c_loop(st)

    _gl080c_end_run(st)

    _gl080c_main_exit(st)


def _gl080c_loop(st: _Gl080Storage) -> None:
    """`loop.` - one batch per pass [general/gl080.cbl:L572-L590].

    Args:
        st: The program's storage.
    """
    while True:
        facade.gl_batch_read_next(st.batch_ctx())

        if arithmetic.compare(st.file_access.fs_reply, _FS_AT_END) == 0:
            # 577 go to end-run. GO TO class 2 - the forward terminator.
            # `_gl080c_end_run` closes the batch file AFTER this loop.
            break

        # 579 if bcycle not = scycle 580 go to loop.
        if (
            arithmetic.compare(
                st.batch.bcycle, st.system.system_data_block.scycle
            )
            != 0
        ):
            continue

        _del_process(st)

        facade.gl_posting_close(st.posting_ctx())

        st.batch.cleared_status = _archived_status()

        # 586 move run-date to stored. A CONTROLLED-CLOCK OBSERVABLE WRITTEN INTO A
        # TABLE COLUMN (rule R-6), read from the system record that arrived through
        # linkage.
        st.batch.dates.stored = move.move(
            st.system.system_data_block.run_date, _STORED
        )

        st.batch.batch_start = move.move_figurative(move.ZERO, _BATCH_START)

        facade.gl_batch_rewrite(st.batch_ctx())

        continue


def _gl080c_end_run(st: _Gl080Storage) -> None:
    """`end-run.` - close the batch file [general/gl080.cbl:L592-L595].

    The third of the three `end-run.` paragraphs. Shorter than `gl080b`'s
    [general/gl080.cbl:L436-L440] by one statement: there is no archive sequence to
    close because this path never opened one.

    Args:
        st: The program's storage.
    """
    facade.gl_batch_close(st.batch_ctx())


def _gl080c_main_exit(st: _Gl080Storage) -> None:
    """`main-exit. exit section.` [general/gl080.cbl:L597].

    The fifth of the seven `main-exit.` paragraphs. Reached only by fall-through from
    `end-run.`; no `GO TO` in this section targets it, because this path has no `disk-
    change` option to abort on.

    Args:
        st: The program's storage, unchanged by this paragraph.
    """
    # 597  exit section.
    #  NO RECORD HERE. The frozen statement this stood for displays nothing -
    # gl080's thirty-nine `display`s are all accounted for, and none of them is at
    # this site - so the record was invented (R-4). Progress and completion traces
    # of internal phase boundaries are not events the compiled program produces.
    return


def _del_process(st: _Gl080Storage) -> None:
    """`del-process section.` - delete every posting of one batch.

    DECLINED. He observes, correctly, that against a relational store the whole walk
    below could be one statement deleting every posting of a batch. Agent Action Plan
    section 0.8.4 forbids taking it up, verbatim.

    Args:
        st: The program's storage.
    """
    # 606  display  WS-Batch-Nos at 2345.
    # Screen furniture. `arc-process` makes the same display at
    # [general/gl080.cbl:L448] and additionally moves the value into the archive
    # header at L449; there is no header here, so the display stands alone.
    #  THE KEY IS NOT IN THE RECORD. The frozen `display` shows the batch or
    # posting number on a curses screen as a moving progress counter; a batch number
    # and a posting number are business keys, which the safe-event schema in
    # `acas_posting/dal/status.py` excludes (CWE-532). The progress display's only
    # purpose was to reassure an operator watching a terminal, and there is no
    # terminal; the rows themselves are what the scenario diff compares.

    facade.gl_posting_open(st.posting_ctx())

    _del_process_loop(st)


def _del_process_loop(st: _Gl080Storage) -> None:
    """`loop.` - one posting per pass [general/gl080.cbl:L609-L623].

    Args:
        st: The program's storage.
    """
    while True:
        facade.gl_posting_read_next(st.posting_ctx())

        if arithmetic.compare(st.file_access.fs_reply, _FS_AT_END) == 0:
            # 614 go to main-exit. GO TO class 3 - a transfer to this section's exit
            # paragraph [general/gl080.cbl:L625].
            _del_process_main_exit(st)
            return

        # 616 if WS-Post-Key = zero 617 or batch not = WS-Batch-Nos 618 go to loop.
        #  BOTH DISJUNCTS COMPARE STORAGE, NOT VALUES, and that is measured rather than
        # chosen - see `_post_key_is_zero` and `_batch_is_not_the_one_being_processed`.
        # For a posting read back through the bridge the second disjunct is TRUE for
        # every batch number there is, so this loop reads every row and deletes none.
        if _post_key_is_zero(st) or _batch_is_not_the_one_being_processed(st):
            continue

        # 620  display  post-number at 2364 ...
        #  THE KEY IS NOT IN THE RECORD. The frozen `display` shows the batch or
        # posting number on a curses screen as a moving progress counter; a batch number
        # and a posting number are business keys, which the safe-event schema in
        # `acas_posting/dal/status.py` excludes (CWE-532). The progress display's only
        # purpose was to reassure an operator watching a terminal, and there is no
        # terminal; the rows themselves are what the scenario diff compares.

        facade.gl_posting_delete(st.posting_ctx())

        continue


def _del_process_main_exit(st: _Gl080Storage) -> None:
    """`main-exit. exit section.` [general/gl080.cbl:L625].

    Args:
        st: The program's storage, unchanged by this paragraph.
    """
    # 625  exit section.
    #  NO RECORD HERE. The frozen statement this stood for displays nothing -
    # gl080's thirty-nine `display`s are all accounted for, and none of them is at
    # this site - so the record was invented (R-4). Progress and completion traces
    # of internal phase boundaries are not events the compiled program produces.
    # It also named the batch number.
    return


def _compress_post(st: _Gl080Storage) -> None:
    """`compress-post section.` - Phase 4, rebuild the posting file.

    on L633 is a RUNTIME condition over a system-record field, so which way it goes is
    decided by the data and not by this migration. Reproducing the section whole is the
    only faithful answer.

    Args:
        st: The program's storage.

    Raises:
        _StopRun: From `Test-Work-File-Size-1` [general/gl080.cbl:L649] when the two
            record lengths disagree.
    """
    # 633 if not FS-Cobol-Files-Used 634 go to main-exit 635 end-if.
    if not condition_names.evaluate(
        "FS-Cobol-Files-Used",
        st.system.system_data_block.rdbms_flat_statuses.file_system_used,
    ):
        # 634  go to main-exit.
        # GO TO class 3 - a transfer to this section's exit paragraph
        # [general/gl080.cbl:L705]. Reproduced as a call to that paragraph
        # followed by a return.
        #  NO RECORD HERE. The frozen statement this stood for displays nothing -
        # gl080's thirty-nine `display`s are all accounted for, and none of them is at
        # this site - so the record was invented (R-4). Progress and completion traces
        # of internal phase boundaries are not events the compiled program produces.
        _compress_post_main_exit(st)
        return

    # 637 display "Phase - 4. Posting Contraction " at 0801 ...
    _LOG.info("Phase - 4.  Posting Contraction")

    _compress_post_test_work_file_size_1(st)

    _compress_post_main_exit(st)


def _compress_post_test_work_file_size_1(st: _Gl080Storage) -> None:
    """`Test-Work-File-Size-1.` - the length gate and the two loops.

    of a group is the sum of its elementary items' storage widths, so the sending side
    is summed over the copybook's own declarations - which is also how the 103 in
    AMBIGUITY Q-23 was measured - and the receiving side is the width its picture
    declares.

    Args:
        st: The program's storage.

    Raises:
        _StopRun: When the two record lengths disagree [general/gl080.cbl:L649].
    """
    # 643 if function length (WS-Posting-Record) not = 644 function length (work-file-
    # record) The sending group's own elementary declarations, summed.
    posting_descriptors = descriptors_for_copybook_record("WS-Posting-Record")
    posting_length = sum(
        descriptor.byte_length
        for descriptor in posting_descriptors
        if not descriptor.is_group
    )
    work_length = _WORK_FILE_RECORD.byte_length

    if arithmetic.compare(posting_length, work_length) != 0:
        _LOG.error(
            "posting record length %s does not match work file record length "
            "%s [general/gl080.cbl:L643-L644]",
            posting_length,
            work_length,
        )


        raise _StopRun(
            "compress-post: function length (WS-Posting-Record) = "
            f"{posting_length} does not equal function length "
            f"(work-file-record) = {work_length} "
            "[general/gl080.cbl:L643-L649]"
        )

    facade.gl_posting_open_input(st.posting_ctx())

    st.work_file.open_output()

    if _compress_post_loop1(st):
        # The class-4 transfer to `file-error.` was taken inside the loop, and `file-
        # error` has already fallen through into `loop2-end.`, so the whole of
        # `loop1-end.`, `loop2.` and the second half of the section is skipped.
        return

    _compress_post_loop1_end(st)

    if _compress_post_loop2(st):
        return

    _compress_post_loop2_end(st)


def _compress_post_loop1(st: _Gl080Storage) -> bool:
    """`loop1.` - copy every posting out to the scratch sequence.

    NOTE THE ORDER OF THE TWO STATUS TESTS AT L658 AND L660. End of file is tested
    FIRST, so status 10 leaves by the class-2 route and only a status that is neither 0
    nor 10 reaches `file-error`.

    Args:
        st: The program's storage.

    Returns:
        True when one of the two class-4 transfers to `file-error.` was taken - in which
            case `file-error.` and the `loop2-end.` it falls into have ALREADY RUN and
            the caller must not continue.
    """
    posting_descriptors = descriptors_for_copybook_record("WS-Posting-Record")
    posting_group = next(
        descriptor
        for descriptor in posting_descriptors
        if descriptor.is_group and descriptor.name.lower() == "ws-posting-record"
    )
    posting_length = sum(
        descriptor.byte_length
        for descriptor in posting_descriptors
        if not descriptor.is_group
    )

    while True:
        facade.gl_posting_read_next(st.posting_ctx())

        if arithmetic.compare(st.file_access.fs_reply, _FS_AT_END) == 0:
            # 659 go to loop1-end. GO TO class 2 - the forward terminator.
            return False

        if arithmetic.compare(st.file_access.fs_reply, _FS_OK) != 0:
            # 661 go to file-error. GO TO CLASS 4, SITE ONE OF FOUR. EQUIVALENCE PROOF.
            _compress_post_file_error(st)
            _compress_post_loop2_end(st)
            return True

        # 662 write work-file-record from WS-Posting-Record. The FROM phrase moves the
        # sending group into the `pic x(101)` record area and then writes.
        st.work_file.write_from(
            st.posting,
            image=move.move_group(
                move.SPACE, posting_group, length=posting_length
            ),
            group=posting_group,
        )

        if arithmetic.compare(st.file_access.fs_reply, _FS_OK) != 0:
            # 664 go to file-error. GO TO CLASS 4, SITE TWO OF FOUR. EQUIVALENCE PROOF.
            _compress_post_file_error(st)
            _compress_post_loop2_end(st)
            return True

        continue


def _compress_post_loop1_end(st: _Gl080Storage) -> None:
    """`loop1-end.` - turn both files around [general/gl080.cbl:L667-L673].

    AMBIGUITY Q-20, SETTLED - THE DANGEROUS LINE IN THIS PROGRAM. L673 performs
    `GL-Posting-Open-Output` [copybooks/Proc-ACAS-FH-Calls.cob:L364], and on a relational
    store an open-for-output DOES mean DELETE EVERY ROW: `acas006` forces `fn-Delete-All`
    after the dispatch [common/acas006.cbl:L637-L644], exactly as the transfer-file
    handler does for the same verb [common/acas008.cbl:L313-L319]. Q-23 keeps the
    statement unreachable, so this is what it would do rather than what it does.

    Args:
        st: The program's storage.
    """
    st.work_file.close()

    facade.gl_posting_close(st.posting_ctx())

    st.work_file.open_input()

    # 673 perform GL-Posting-Open-Output. See AMBIGUITY Q-20 above. Reproduced without a
    # guard.
    facade.gl_posting_open_output(st.posting_ctx())


def _compress_post_loop2(st: _Gl080Storage) -> bool:
    """`loop2.` - write every row back into the posting file.

    NOTE THE ASYMMETRY WITH `loop1`. There the end of file is a STATUS TEST
    [general/gl080.cbl:L658] because the read goes through a facade verb.

    Args:
        st: The program's storage.

    Returns:
        True when one of the two class-4 transfers to `file-error.` was taken - in which
            case `file-error.` and `loop2-end.` have ALREADY RUN.
    """
    posting_descriptors = descriptors_for_copybook_record("WS-Posting-Record")
    posting_group = next(
        descriptor
        for descriptor in posting_descriptors
        if descriptor.is_group and descriptor.name.lower() == "ws-posting-record"
    )
    posting_length = sum(
        descriptor.byte_length
        for descriptor in posting_descriptors
        if not descriptor.is_group
    )

    while True:
        if not st.work_file.read():
            # 679 go to loop2-end. GO TO class 2 - the forward terminator, reached
            # through the AT END phrase rather than a status test.
            return False

        if arithmetic.compare(st.file_access.fs_reply, _FS_OK) != 0:
            # 681 go to file-error. GO TO CLASS 4, SITE THREE OF FOUR. EQUIVALENCE
            # PROOF.
            _compress_post_file_error(st)
            _compress_post_loop2_end(st)
            return True

        # 682  move     work-file-record to WS-Posting-Record.
        # A GROUP MOVE of the 101 raw characters into a group receiver, so no
        # child picture is applied and no numeric conversion happens. Delegated
        # whole; see `_WorkFile.write_from` for how the field values travel.
        # THE RESULT IS NOT BOUND. It was bound only so a log record could report
        # its length and the work file's path, and that record is gone. The MOVE itself
        # stays because it is the frozen statement, and its effect is applied through
        # `posting_group`, the receiver it is given.
        move.move_group(
            st.work_file.record, posting_group, length=posting_length
        )
        # The 101-character sender pads to the group's 103, which is the width
        # disagreement the length gate exists to prevent - and does.
        if st.work_file.posting_image is not None:
            st.posting = st.work_file.posting_image
        #  NO RECORD HERE. The frozen statement this stood for displays nothing -
        # gl080's thirty-nine `display`s are all accounted for, and none of them is at
        # this site - so the record was invented (R-4). Progress and completion traces
        # of internal phase boundaries are not events the compiled program produces.
        # It also named the work file's own path.

        facade.gl_posting_write(st.posting_ctx())

        if arithmetic.compare(st.file_access.fs_reply, _FS_OK) != 0:
            # 685 go to file-error. GO TO CLASS 4, SITE FOUR OF FOUR. EQUIVALENCE PROOF.
            _compress_post_file_error(st)
            _compress_post_loop2_end(st)
            return True

        continue


def _compress_post_file_error(st: _Gl080Storage) -> None:
    """`file-error.` - report, and FALL THROUGH [general/gl080.cbl:L688-L697].

    THE MAJOR FALL-THROUGH OF THIS PROGRAM. L697 is the paragraph's last statement and
    there is NO `GO TO`, no `PERFORM` return and no `EXIT` after it, so control runs
    straight on into `loop2-end.` [general/gl080.cbl:L699].

    Args:
        st: The program's storage. `st.ws_eval_msg` is written by the message lookup
            this paragraph performs.
    """

    # 693 perform evaluate-message. The message-table lookup. Diagnostic only - it sets
    # the text and must not alter control flow, and it does not.
    _evaluate_message(st)

    _LOG.error(
        "posting file error: fs-reply=%s %s [general/gl080.cbl:L691-L694]",
        st.file_access.fs_reply,
        st.ws_eval_msg,
    )


def _compress_post_loop2_end(st: _Gl080Storage) -> None:
    """`loop2-end.` - close both files [general/gl080.cbl:L699-L703].

    REACHED FIVE WAYS: by the class-2 transfer at [general/gl080.cbl:L679], and by fall-
    through from `file-error.` on each of the four class-4 sites.

    Args:
        st: The program's storage.
    """
    st.work_file.close()

    facade.gl_posting_close(st.posting_ctx())


def _compress_post_main_exit(st: _Gl080Storage) -> None:
    """`main-exit.` / `exit section.` [general/gl080.cbl:L705-L708].

    The seventh and last of the seven `main-exit.` paragraphs, and the only one whose
    `exit section.` sits on a line of its own rather than sharing the label's line.
    Reached two ways.

    Args:
        st: The program's storage, unchanged by this paragraph.
    """
    # 708  exit     section.
    #  NO RECORD HERE. The frozen statement this stood for displays nothing -
    # gl080's thirty-nine `display`s are all accounted for, and none of them is at
    # this site - so the record was invented (R-4). Progress and completion traces
    # of internal phase boundaries are not events the compiled program produces.
    return


#: The `EVALUATE STATUS` table that `copy "FileStat-Msgs.cpy" replacing MSG by ws-Eval-
#: Msg STATUS by fs-reply.` [general/gl080.cbl:L713-L714] expands into.
_FILE_STATUS_MESSAGES: Final[Mapping[int, str]] = {
    0: "Success",
    2: "Success Duplicate",
    4: "Success Incomplete",
    5: "Success Optional, Missing",
    6: "Multiple Records LS",
    7: "Success No Unit",
    9: "Success LS Bad Data",
    10: "End Of File",
    14: "Out Of Key Range",
    21: "Key Invalid",
    22: "Key Exists",
    23: "Key Not Exists",
    24: "Key Boundary violation",
    30: "Permanent Error",
    31: "Inconsistent Filename",
    34: "Boundary Violation",
    35: "File Not Found",
    37: "Permission Denied",
    38: "Closed With Lock",
    39: "Conflict Attribute",
    41: "Already Open",
    42: "Not Open",
    43: "Read Not Done",
    44: "Record Overflow",
    46: "Read Error",
    47: "Input Denied",
    48: "Output Denied",
    49: "I/O Denied",
    51: "Record Locked",
    52: "End-Of-Page",
    57: "I/O Linage",
    61: "File Sharing Failure",
    71: "Bad Character LS",
    91: "Feature Not Available",
}

_FILE_STATUS_MESSAGE_OTHER: Final[str] = "Unknown File Status"


def _evaluate_message(st: _Gl080Storage) -> None:
    """`Evaluate-Message Section.` - status to text [general/gl080.cbl:L710].

    `Evaluate-Message`, which is what `pl060` writes too [purchase/pl060.cbl:L1037],
    while `sl060` writes `zz040-Evaluate-Message` [sales/sl060.cbl:L1183] for the same
    idea. Renaming either to match the other would break the paragraph-to-function
    traceability rule R-5 depends on.

    Args:
        st: The program's storage. Reads `Fs-Reply` and writes `ws-eval-msg`.
    """
    # 713 EVALUATE fs-reply ...
    status = int(st.file_access.fs_reply)
    text = _FILE_STATUS_MESSAGES.get(status, _FILE_STATUS_MESSAGE_OTHER)

    # The literal is stored through the receiving field's own descriptor, so the
    # 25-character width and its space padding come from `ws-eval-msg pic x(25)`
    # [general/gl080.cbl:L185] rather than from the length the copybook happens to have
    # typed.
    st.ws_eval_msg = move.move(text, _WS_EVAL_MSG)

    _eval_msg_exit(st)


def _eval_msg_exit(st: _Gl080Storage) -> None:
    """`Eval-Msg-Exit. exit section.` [general/gl080.cbl:L716].

    Args:
        st: The program's storage, unchanged by this paragraph.
    """
    # 716  exit section.
    #  NO RECORD HERE. The frozen statement this stood for displays nothing -
    # gl080's thirty-nine `display`s are all accounted for, and none of them is at
    # this site - so the record was invented (R-4). Progress and completion traces
    # of internal phase boundaries are not events the compiled program produces.
    # The status and its message DO reach a record, once, at the one site the frozen
    # source displays them [general/gl080.cbl:L691-L695].
    return


def _zz070_convert_date(st: _Gl080Storage) -> None:
    """`zz070-Convert-Date section.` - present the run date.

    CARRIES IT. Agent Action Plan section 0.6.3 identifies these repeated date sections
    as the one place consolidation is unambiguously safe, "because the bodies are
    textually equivalent".

    Args:
        st: The program's storage. Reads `to-day`, reads and writes `Date-Form`, and
            fills `ws-date` and its three redefined views.
    """
    # 727-744, as one call.
    effective_form = zz070_convert_date(
        st.ws_date_formats,
        st.to_day,
        st.system.system_data_block.date_form,
    )

    # 729 if Date-Form = zero 730 move 1 to Date-Form. Storing the returned form back is
    # what reproduces the mutation.
    st.system.system_data_block.date_form = move.move(effective_form, _DATE_FORM)

    # 746 zz070-Exit. Reached three ways in the frozen source: the class-3 transfers at
    # [general/gl080.cbl:L732] and [general/gl080.cbl:L737], and fall-through from L744.
    _zz070_exit(st)


def _zz070_exit(st: _Gl080Storage) -> None:
    """`zz070-Exit.` / `exit section.` [general/gl080.cbl:L746-L747].

    Args:
        st: The program's storage, unchanged by this paragraph.
    """
    # 747  exit     section.
    #  NO RECORD HERE. The frozen statement this stood for displays nothing -
    # gl080's thirty-nine `display`s are all accounted for, and none of them is at
    # this site - so the record was invented (R-4). Progress and completion traces
    # of internal phase boundaries are not events the compiled program produces.
    # It also named the run date twice - a date with business meaning (CWE-532).
    return


def run(
    ws_calling_data: WsCallingData,
    system_record: SystemRecord,
    to_day: str,
    file_defs: FileDefs,
    *,
    file_access: FileAccess | None = None,
    dal_common: AcasDalCommonData | None = None,
    run_confirmed: bool = True,
    disk_change_option: int = 0,
    archive_path_override: str | None = None,
    dal_options: Mapping[str, object] | None = None,
) -> None:
    """`gl080` - General Ledger End Of Cycle Processing [general/gl080.cbl].

    The whole program, entered exactly where the COBOL is entered. Its four
    positional parameters are the `PROCEDURE DIVISION USING` list, verbatim and
    in order::

         269  procedure division using ws-calling-data
         270                           system-record
         271                           to-day
         272                           file-defs.

    THE GENERAL LEDGER FOUR-PARAMETER SHAPE, one of the three linkage shapes in
    the migration. The Sales and Purchase families add a fourth system record;
    the IRS program takes neither the calling-data block nor the run date. This
    is the plain General Ledger form and no parameter is added to, removed from or
    reordered within it.

    ITS CALLER, AND WHAT THAT CALLER DOES NOT DO. `general.cbl` dispatches this
    program from `load09.` [general/general.cbl:L817-L821], which moves the
    program name and transfers to the shared `load00.` block
    [general/general.cbl:L711-L722]. That block zeroes the term code, issues the
    `CALL` with these four arguments, and tests `if ws-term-code > 7`. UNLIKE
    `load08`, IT HAS NO `= 5` GATE - and it does not need one, because `gl080`
    NEVER SETS A TERM CODE. Where `gl070` raises 5 to stop the cycle
    [general/gl070.cbl:L289], `gl080` simply returns [general/gl080.cbl:L366].
    So `ws_calling_data` is accepted and never read, which is why it is a
    parameter rather than a return value.

    THE PROMOTED PARAMETERS. Three interactive statements in the frozen source
    decide something a later statement acts on, and Agent Action Plan section
    0.3.4 turns exactly those into parameters "with the COBOL default preserved".
    Every one defaults to the answer that lets the program proceed:

    `run_confirmed`  from [general/gl080.cbl:L299-L302]. The run-confirm prompt;
        Escape or "A" makes the program `goback` before a single write. Default
        True, meaning proceed.
    `disk_change_option`  from [general/gl080.cbl:L545-L547]. THE CLEAREST
        DATABASE-GATING PROMPT IN THE FOLDER: 9 suppresses the archiving walk
        [general/gl080.cbl:L408-L409] AND the whole of end-of-period processing
        [general/gl080.cbl:L324-L326], so it stops every batch stamp, every
        posting delete, the ledger-quarter rollover and the cycle increment.
        Default 0, meaning proceed. ITS DOMAIN IS EXACTLY {0, 9}: `if a not =
        zero go to accept-option` [general/gl080.cbl:L548-L549] returns every
        other value to the prompt, so no other value can reach the statements
        below it. Any other value raises `DiskChangeOptionNotAcceptable` rather
        than proceeding.
    `archive_path_override`  from [general/gl080.cbl:L555]. Edits where the flat
        archive rows are written. NO TABLE EFFECT - the archive is not a schema
        table. Default None, meaning keep the path `disk-change` computes at
        [general/gl080.cbl:L537].

    The acknowledgement pauses at [general/gl080.cbl:L311-L312],
    [general/gl080.cbl:L648] and [general/gl080.cbl:L696] are NOT parameters,
    because their only effect was to hold a terminal. They are dropped and the
    control transfers around them are kept.

    THE OTHER FOUR KEYWORD PARAMETERS ARE NOT PROMOTED PROMPTS. `file_access` and
    `dal_common` are two of the five arguments every handler `CALL` carries
    [copybooks/Proc-ACAS-FH-Calls.cob:L51-L57]; the COBOL program declares them
    in its own working storage rather than receiving them, so they default to
    fresh records and a caller that wants to observe `Fs-Reply` afterwards may
    pass its own. `dal_options` is forwarded verbatim into every
    `FacadeContext.options` and has no COBOL counterpart at all - it is how a
    caller reaches the data-access layer's own knobs without this module knowing
    what they are.

    DETERMINISM (rule R-6). Every date this program uses arrives here: the text
    date in `to_day` and the binary run date in `system_record`. There is no
    ambient clock anywhere in the module and the controlled-clock module is not
    imported - the two batch stamps at [general/gl080.cbl:L431] and
    [general/gl080.cbl:L586] read `Run-Date` [copybooks/wssystem.cob:L67] out of
    the record they were handed. Two runs with the same arguments write the same
    rows.

    Args:
        ws_calling_data: `01 WS-Calling-Data` [copybooks/wscall.cob:L7-L14].
        system_record: `01 System-Record` [copybooks/wssystem.cob]. READ AND MUTATED -
            `Scycle` at [general/gl080.cbl:L334], [general/gl080.cbl:L360] and
            [general/gl080.cbl:L363], `Current-Quarter` at [general/gl080.cbl:L355] and
            [general/gl080.cbl:L357], and `Date-Form` at [general/gl080.cbl:L730].
        to_day: `01 to-day pic x(10).` [general/gl080.cbl:L267], DD/MM/CCYY.
        file_defs: `01 File-Defs.` [copybooks/wsnames.cob:L13].
        file_access: `01 File-Access` [copybooks/wsfnctn.cob:L22]. A fresh record when
            omitted.
        dal_common: `01 ACAS-DAL-Common-data.` [copybooks/Test-Data-Flags.cob]. A fresh
            record when omitted.
        run_confirmed: See above. False reproduces Escape or "A".
        disk_change_option: See above. 0 proceeds and 9 reproduces the abort;
            no third value is accepted.
        archive_path_override: See above.
        dal_options: Forwarded to every handler.

    Raises:
        DiskChangeOptionNotAcceptable: `disk_change_option` is neither 0 nor 9,
            which `accept-option.` [general/gl080.cbl:L542-L549] cannot leave the
            prompt on. Raised before the archiving walk, so nothing is written.
        _StopRun: `stop run.` [general/gl080.cbl:L649], when `compress-post`
            finds the posting record and its work record are different lengths.
            The run unit ends; see AMBIGUITY Q-23 for when this can happen.
    """
    # BOTH FLAT FILES DECLARE `fs-reply` AS THEIR FILE STATUS [general/gl080.cbl:L140],
    # [general/gl080.cbl:L146], and that is the SAME `Fs-Reply pic 99`
    # [copybooks/wsfnctn.cob:L25] the handlers write.
    access = file_access if file_access is not None else FileAccess()

    st = _Gl080Storage(
        ws_calling_data=ws_calling_data,
        system=system_record,
        to_day=to_day,
        file_defs=file_defs,
        file_access=access,
        dal_common=(
            dal_common if dal_common is not None else AcasDalCommonData()
        ),
        ledger=WsLedgerRecord(),
        batch=GlBatchRecord(),
        # `copy "wspost.cob".` [general/gl080.cbl:L190] - a copy `gl072` does NOT make,
        # which is why this program can write and rewrite postings.
        posting=WsPostingRecord(),
        a=0,
        y=0,
        ws_eval_msg=move.move_figurative(move.SPACE, _WS_EVAL_MSG),
        ws_date_formats=WsDateFormats(),
        archive=_ArchiveFile(access),
        work_file=_WorkFile(access),
        run_confirmed=run_confirmed,
        disk_change_option=disk_change_option,
        archive_path_override=archive_path_override,
        dal_options=dal_options if dal_options is not None else {},
    )

    _gl080_main(st)
