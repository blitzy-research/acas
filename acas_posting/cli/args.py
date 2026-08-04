"""argv to `WS-Calling-Data`: the one place the CLI binds the COBOL linkage.

This module owns two things: the binding of command-line arguments to
`01 WS-Calling-Data` [copybooks/wscall.cob:L6-L14] and to the system records the
three linkage shapes carry, and the reading of the termination code afterwards.
It runs no program, opens no file and touches no database.

Three linkage shapes, published as three dataclasses and three argparse
fragments:

    GlLinkage     four parameters - ws-calling-data, system-record, to-day,
                  file-defs [general/gl070.cbl:L245-L248]
    SlPlLinkage   five - the same four plus WS-System-Record-4
                  [sales/sl060.cbl:L395-L399]
    IrsLinkage    three - IRS-System-Params, WS-System-Record, File-Defs, with
                  no calling-data block at all [irs/irs030.cbl:L552-L554]

The run date is an argument and never a clock reading (R-6). `--run-date` has no
default, no environment fallback and no test hook, and binding pins both
observables from it: the text `to-day pic x(10)` and the binary `Run-Date`
[copybooks/wssystem.cob:L67]. None of the twelve migrated posting programs reads
a clock - each receives the date through linkage - so pinning here is enough to
make two runs of one scenario byte-identical.

Receiving-field semantics are applied rather than skipped: a bound value is
truncated and space-padded exactly as a `MOVE` into the declared picture would
be, so a too-long `--ws-caller` loses its tail here as it would in COBOL.

Term codes read back out: `GL_ABORT_TERM_CODE` 5 is the General Ledger abort
[general/general.cbl:L810-L811], `EXTRACT_MISSING_FILE_TERM_CODE` 8 is a missing
extract file [sales/sl055.cbl:L344-L345], and `is_serious_error` is the menus'
own `> 7` test [common/ACAS.cbl:L578]. `exit_status_for` is the identity, so a
caller reads the code the cycle produced rather than a re-encoding of it.

`WS-Term-Code` IS `pic 99` - AN UNSIGNED TWO-DIGIT INTEGER
[copybooks/wscall.cob:L10], widened from `pic 9` by the maintainer's own change
note at [copybooks/wscall.cob:L4]. Its domain is 0 through 99 inclusive, and
that one fact is load-bearing for every entry point in this package: the two
predicates the menus test, `ws-term-code < 8` (e.g. [sales/sales.cbl:L686],
[sales/sales.cbl:L708]) and `ws-term-code > 7` (e.g. [general/general.cbl:L720]),
are EXHAUSTIVE and MUTUALLY EXCLUSIVE over that domain - no third band, no
negative case, no unset case - so `is_serious_error` is a total predicate whose
complement needs no helper; and every value it can hold is already a legal
process exit status, which is why `exit_status_for` is the identity rather than a
lossy mapping.

THE THREE LINKAGE SHAPES - THREE ARGUMENT SHAPES, NOT ONE
None of the twelve migrated programs is a main program; each is a `CALL`ed
sub-program with a fixed parameter list, and there are exactly three shapes. The
carriers below hold them in COBOL parameter order so a reviewer can diff the
argument lists side by side.

  Shape 1 - General Ledger, FOUR parameters -> `GlLinkage`
      ws-calling-data, system-record, to-day, file-defs
      dispatched by general/general.cbl `load00.` L711-L723 (`CALL` parameter
      list L715-L718); callee [general/gl070.cbl:L245-L248].
  Shape 2 - Sales and Purchase, FIVE parameters -> `SlPlLinkage`
      ws-calling-data, System-Record, WS-System-Record-4, to-day, file-defs
      dispatched by sales/sales.cbl `load000.` (`CALL` L702-L707) and
      purchase/purchase.cbl `load000.` (`CALL` L695-L700); callee
      [sales/sl060.cbl:L395-L399]. FIVE, not four - see CORRECTION 3 in the
      footer.
  Shape 3 - IRS, THREE parameters -> `IrsLinkage`
      IRS-System-Params, WS-System-Record, file-defs
      dispatched from irs/irs.cbl `Main-Loop.` (`CALL` L668-L671); callee
      [irs/irs030.cbl:L552-L554]. Materially different: NO calling-data block
      and NO `to-day`.

THE CONTROLLED CLOCK STOPS HERE  (rule R-6)
Agent Action Plan section 0.1.1 requires the clock to pin exactly two
observables - the text date `to-day pic x(10)` in DD/MM/CCYY form and the binary
`Run-Date` [copybooks/wssystem.cob:L67] - and to inject them at the CLI
boundary, no clock abstraction being needed inside the migrated programs at all.
All twelve in-scope posting programs contain zero clock reads; the date reaches
them purely through linkage.

THE CLOCK-READ CENSUS, MEASURED RATHER THAN QUOTED. Agent Action Plan section
0.1.1 calls [copybooks/Proc-ACAS-Mapser-RDB.cob:L72-L80] "the single read in the
whole call chain". A grep census finds FOURTEEN ambient date and time reads
across SIX files - six `move function current-date to wse-date-block`
(common/ACAS.cbl:L353, general/general.cbl:L371, sales/sales.cbl:L323,
purchase/purchase.cbl:L318, irs/irs.cbl:L480 and the copybook's own at L72), four
`accept ... from time` (common/ACAS.cbl:L470, general/general.cbl:L551,
sales/sales.cbl:L520, purchase/purchase.cbl:L514) and four `accept ... from date`
(common/ACAS.cbl:L478, general/general.cbl:L559, sales/sales.cbl:L528,
purchase/purchase.cbl:L522). The exact figure is recorded here, and identically
in `acas_posting/clock.py`, so that a reader who greps is not surprised by it.

THE PLAN'S CONCLUSION HOLDS ALL THE SAME, and it is the conclusion that matters:
every one of the fourteen sites is in an out-of-scope menu shell or in the
date-service copybook those shells COPY, and none of the twelve in-scope posting
programs reads a clock at all. Two further measurements say why the fourteen
cannot reach a posted figure. The eight `accept` reads feed a screen banner only.
And the copybook's block is not the menu's normal path either - it sits inside
`ba010-Capture-Data`, the FIRST-TIME parameter-file capture, where it builds
`to-day` at L77, pre-zeroes `u-bin` at L78, calls `maps04` at L79 and stores
`run-date` at L80; on a normal run the shell instead derives `to-day` FROM THE
STORED `Run-Date` it has just read, `move run-date to u-bin. call "maps04". move
u-date to to-day.` [general/general.cbl:L462-L465]. So the run date the frozen
cycle uses is a STORED value, and pinning the two observables at this boundary is
what replaces it.

This module plus `acas_posting/clock.py` are therefore the sole injection point,
and the
injection is by ARGUMENT: `--run-date` is REQUIRED on every route that needs a
date, with no default of any kind. Nothing here reads a system clock, an
elapsed-time counter, an environment variable, a host name or an entropy source,
so two runs of one scenario are byte-identical (Agent Action Plan 0.8.5).

A MALFORMED `--run-date` IS NOT REJECTED HERE  (rules R-3 and R-4)
`resolve_clock` hands the text straight to `acas_posting.clock`, which hands it
to the migrated `maps04`. That program judges it with its own six-part test
[common/maps04.cbl:L140-L146] and calendar check [common/maps04.cbl:L153], and
on rejection falls through leaving its output field untouched
[common/maps04.cbl:L146], [common/maps04.cbl:L154] - so the caller pre-zero at
[copybooks/Proc-ACAS-Mapser-RDB.cob:L78] is what makes a rejected date come back
as `Run-Date = 0` rather than as stale content. That is anomaly 16, reproduced
rather than corrected: "31/02/2025" yields a pinned pair whose `run_date` is 0
and DOES NOT RAISE, because validating here would add a validation the COBOL
does not perform (R-3) and correct legacy behaviour (R-4).

THE IRS ROUTE - WHY IT TAKES `--run-date` AND NO CALLING-DATA OPTIONS
Shape 3 has no calling-data block and no `to-day`, so
`add_irs_linkage_arguments` adds none of the calling-data options and
`bind_irs_linkage` builds a carrier of exactly three members. The route still
needs the pinned clock for two fields that are unambiguously present:
`WS-System-Record.Run-Date` `binary-long` [copybooks/wssystem.cob:L67], because
the ACAS system record IS the second linkage argument [irs/irs.cbl:L669]; and
`IRS-System-Params.Run-Date` `pic x(8)` [copybooks/irswssystem.cob:L14], which
irs/irs.cbl always populates through `zz090-Proc-Run-Date.`
[irs/irs.cbl:L972-L978] before any menu option runs. `irs_run_date_x8`
reproduces that conversion; whether irs030 reads the field at all is the open
question Q-CLI-IRS-RUNDATE. Without `--run-date` this module would have to read
a live clock (R-6) or leave both fields unpinned (R-3, R-4).

WHAT THIS MODULE MAY AND MAY NOT IMPORT
MAY, and does: the standard library, `acas_posting.clock`, its sibling
`acas_posting.cli.rdbms_params`, the record modules whose dataclasses the three
shapes are built from, the `MOVE` implementation `acas_posting.cobol.move`, and
- see the next section - the data-access FACADE `acas_posting.dal.facade` with
its status vocabulary, plus `acas_posting.dal.connection` for the one
process-level connection policy. Together with that sibling this is the ONLY part
of `acas_posting/cli/` permitted to import the record layer, precisely because
section 0.4.1.1 assigns it the job of binding "the system records"; the seven
entry-point modules of this package construct their linkage through here.

The sibling import is intra-package and acyclic: `rdbms_params` imports one
record module and nothing else of this package, and `acas_posting/cli/__init__.py`
imports no submodule at all, so there is no cycle to create.

`acas_posting.cobol.move` belongs on that list, and an earlier draft of this file
put it on the other one. The import table of section 0.4.3 bars
`acas_posting/cli/` from the data-access handlers - "Must not import:
`dal.acas*`" - and from nothing else in the semantics package, while section
0.1.2, transformation rule 11, requires a `MOVE` between unlike pictures to go
through "Sending-field-to-receiving-field rules, not assignment". argv is the one
place in the migrated cycle where a string of arbitrary length meets a `PIC X(8)`
receiving field, so this is precisely where rule 11 has to be applied. The edge
is acyclic: `acas_posting.cobol.move` reaches only `cobol.arithmetic`,
`cobol.usage`, `cobol.field` and `dictionary.model`, and none of those reaches
`acas_posting.cli`.

MAY NOT, and does not: the program layer, the data-access HANDLERS
`acas_posting.dal.acas*`, the dictionary package and the work-file module. The
import table of section 0.4.3 names exactly one prohibition for this layer -
"Must not import: `dal.acas*` directly" - and the facade exists precisely so
that a caller reaches a handler THROUGH it, which is what
`aa010_get_system_recs` and `overrewrite` below do. One consequence worth
stating because it looks like an omission:

  * `MOVE` receiving-field semantics ARE applied to the seven `WS-Calling-Data`
    fields, through `acas_posting/cobol/move.py`, because argv is the one place
    in the migrated cycle where a string of arbitrary length meets a `PIC X(8)`
    receiving field. What is deliberately NOT re-plumbed is named in the footer.
    `rdbms_params` pads each connection value to its receiving `pic x(n)` width
    with a local helper instead - the same accommodation
    `acas_posting/dal/connection.py` already makes, and for the same layering
    reason.
  * the system records are LOADED FROM THE STORE, field for field, by
    `aa010_get_system_recs` below, reproducing the menu shells' own
    `aa010-Get-System-Recs` paragraph; only the six connection fields and the
    two pinnable clock fields are re-applied afterwards, for the reasons the
    next section and Q-CLI-SYSREC-LOAD give. The declared dataclass defaults
    survive only for a field the loaded row does not carry.

THE SIX CONNECTION FIELDS ARE THE ONE EXCEPTION TO "DECLARED DEFAULTS"
=====================================================================
`RDBMS-DB-Name`, `RDBMS-User`, `RDBMS-Passwd`, `RDBMS-Port`, `RDBMS-Host` and
`RDBMS-Socket` [copybooks/wssystem.cob:L137-L144] are filled from the deployment
contract by `acas_posting/cli/rdbms_params.py`, which reproduces the frozen
`common/acas-get-params.cbl` and the six `MOVE` statements every load program
performs after calling it [common/glbatchLD.cbl:L262-L267].

They cannot be left at their declared defaults, because those defaults are the
copybook's own placeholders - the literal user `"ACAS-User"` and the literal
password `"PaSsWoRd"` - and `SYSTEM-REC` is the ONLY carrier by which a
connection parameter reaches the data-access layer
[common/acas008.cbl:L558-L563]. A run built purely at declared defaults would
therefore not reach the database the operator provisioned.

No CLI option is added for any of the six: the frozen counterpart takes its
values from a source outside the command line, so this one does too. The closed
list of two settable `SYSTEM-REC` options stays closed, and a password never
appears in argv.

RECEIVING-FIELD SEMANTICS ARE APPLIED, NOT SKIPPED
==================================================
Every write into `01 WS-Calling-Data` [copybooks/wscall.cob:L6-L14] is a `MOVE`
through `acas_posting.cobol.move.move`, carrying the RECEIVING FIELD'S OWN
descriptor. The descriptor is fetched by attribute name from
`acas_posting.records.calling_data.descriptor_for`, imported here under the
local alias `calling_data_record`, so the picture comes from the generated data
dictionary and is never transcribed in this file (rule R-5, and the "data
dictionary first" directive of section 0.8.1). The call sites need know nothing
about field categories, because `move` dispatches on the receiver.

What that buys is the behaviour the frozen copybook declares rather than
Python's assignment: `move "gl070" to ws-called` leaves EIGHT characters in a
`PIC X(8)` field, not five; an over-long `--ws-cd-args` loses its tail at
thirteen instead of widening the field; and a value moved into
`WS-Term-Code pic 99` or `WS-Process-Func pic 9` lands at the declared digit
count. Nothing is checked and nothing is reported on the way in (rule R-3): a
`MOVE` pads and truncates silently, and that silence is the whole of what the
COBOL does.

NO IMPORT-TIME SIDE EFFECTS
Importing this module binds names and evaluates a handful of pure in-memory
dataclass constructions, and has no other observable effect. It builds no
parser, configures no logging, opens no file, connection or directory, reads
nothing from its surroundings, starts nothing, and cannot fail for an
environmental reason. That is a hard requirement rather than a preference: the
scenario test suites import this package, and a module that did work at import
would make their arithmetic tier's "runs anywhere" promise untrue.

Stated precisely, because the connection binding above could be read as
contradicting it: the ENVIRONMENT IS READ ONLY WHEN A BINDER IS CALLED, never at
import. `bind_rdbms_connection` is imported here but not invoked here, and it
accepts an explicit `env` mapping, so a test can drive every binder without
touching the real environment. The three public binders CAN therefore now fail
for an environmental reason - deliberately, because a run that cannot reach the
provisioned database must stop before it writes - while importing this module
still cannot.

THE RULES THAT BIND THIS FILE
=============================
`review_rules` reports NO user rules document for this project, so the binding
constraints are the Agent Action Plan's own six (section 0.7.2):

R-1 No COBOL at run time. Nothing here spawns a child process, loads a foreign
    library or reaches the GnuCOBOL toolchain, and there is no import path from
    this package to the compiled comparison oracle. No option selects, invokes
    or compares against that oracle either - the oracle's own scripts drive
    these entry points from outside, never the reverse.
R-2 Zero binary floating point. `WS-Term-Code` is an `int` (from `pic 99`),
    `to-day` is a `str`, `Run-Date` is an `int` and the IRS `run-date` is a
    `str`. No binary-radix numeric type appears anywhere in this module, in a
    signature, an option type or a computation.
R-3 No added validation, no added field, no schema change, no concurrency.
    Nothing here judges a run date, extends a record or reaches a database, and
    execution is strictly sequential - there is no worker, pool or event loop
    to configure and no option that would create one. The six connection fields
    the binders fill already exist in [copybooks/wssystem.cob:L137-L144], so no
    field is added; the width and blank checks that guard them live in
    `rdbms_params` and apply to DEPLOYMENT CONFIGURATION rather than to any
    accounting value, which that module argues at length.
R-4 Legacy behaviour is reproduced, never corrected. Agent Action Plan section
    0.8.2, verbatim: "A defect reproduced is correct; a defect fixed is a
    failure." Each reproduction below carries its COBOL locator in a comment,
    as section 0.7.4 C-4 requires.
R-5 Full traceability - see the mandatory footer.
R-6 Compiled behaviour is the tie-breaker, so the clock is injected and the
    three genuinely open questions are marked in place rather than guessed.
=======
=======================================
MAY, and does: the standard library, `acas_posting.clock`, its sibling
`acas_posting.cli.rdbms_params`, the five record modules whose dataclasses the
three shapes are built from, and the `MOVE` implementation
`acas_posting.cobol.move`. Together with that sibling this is the ONLY part of
`acas_posting/cli/` permitted to import the record layer, precisely because
section 0.4.1.1 assigns it the job of binding "the system records"; the seven
entry-point modules of this package construct their linkage through here.

The sibling import is intra-package and acyclic: `rdbms_params` imports one
record module and nothing else of this package, and `acas_posting/cli/__init__.py`
imports no submodule at all, so there is no cycle to create.

`acas_posting.cobol.move` belongs on that list, and an earlier draft of this file
put it on the other one. The import table of section 0.4.3 bars
`acas_posting/cli/` from the data-access handlers - "Must not import:
`dal.acas*`" - and from nothing else in the semantics package, while section
0.1.2, transformation rule 11, requires a `MOVE` between unlike pictures to go
through "Sending-field-to-receiving-field rules, not assignment". argv is the one
place in the migrated cycle where a string of arbitrary length meets a `PIC X(8)`
receiving field, so this is precisely where rule 11 has to be applied. The edge
is acyclic: `acas_posting.cobol.move` reaches only `cobol.arithmetic`,
`cobol.usage`, `cobol.field` and `dictionary.model`, and none of those reaches
`acas_posting.cli`.

MAY NOT, and does not: the program layer, the data-access layer including its
facade, the dictionary package and the work-file module. One consequence worth
stating because it looks like an omission:

  * `MOVE` receiving-field semantics ARE applied to the seven `WS-Calling-Data`
    fields, through `acas_posting/cobol/move.py`, because argv is the one place
    in the migrated cycle where a string of arbitrary length meets a `PIC X(8)`
    receiving field. What is deliberately NOT re-plumbed is named in the footer.
    `rdbms_params` pads each connection value to its receiving `pic x(n)` width
    with a local helper instead - the same accommodation
    `acas_posting/dal/connection.py` already makes, and for the same layering
    reason.
  * the system records are BOUND here and LOADED elsewhere. This module fills
    the three pinnable fields and the six connection fields; the other 160
    columns of `SYSTEM-REC`, the whole of `SYSTOT-REC` and the whole of
    `IRS-System-Params` come from the store, read by
    `aa010_get_system_recs` below - the migrated menu boundary - and handed to
    the three binders as keyword arguments. Recorded as Q-CLI-SYSREC-LOAD, and
    settled there; a binder called WITHOUT them still builds declared-default
    records, which is what a caller inspecting a linkage shape without a database
    wants.

THE SIX CONNECTION FIELDS ARE THE ONE EXCEPTION TO "DECLARED DEFAULTS"
=====================================================================
`RDBMS-DB-Name`, `RDBMS-User`, `RDBMS-Passwd`, `RDBMS-Port`, `RDBMS-Host` and
`RDBMS-Socket` [copybooks/wssystem.cob:L137-L144] are filled from the deployment
contract by `acas_posting/cli/rdbms_params.py`, which reproduces the frozen
`common/acas-get-params.cbl` and the six `MOVE` statements every load program
performs after calling it [common/glbatchLD.cbl:L262-L267].

They cannot be left at their declared defaults, because those defaults are the
copybook's own placeholders - the literal user `"ACAS-User"` and the literal
password `"PaSsWoRd"` - and `SYSTEM-REC` is the ONLY carrier by which a
connection parameter reaches the data-access layer
[common/acas008.cbl:L558-L563]. A run built purely at declared defaults would
therefore not reach the database the operator provisioned.

No CLI option is added for any of the six: the frozen counterpart takes its
values from a source outside the command line, so this one does too. The closed
list of two settable `SYSTEM-REC` options stays closed, and a password never
appears in argv.

RECEIVING-FIELD SEMANTICS ARE APPLIED, NOT SKIPPED
==================================================
Every write into `01 WS-Calling-Data` [copybooks/wscall.cob:L6-L14] is a `MOVE`
through `acas_posting.cobol.move.move`, carrying the RECEIVING FIELD'S OWN
descriptor. The descriptor is fetched by attribute name from
`acas_posting.records.calling_data.descriptor_for`, imported here under the
local alias `calling_data_record`, so the picture comes from the generated data
dictionary and is never transcribed in this file (rule R-5, and the "data
dictionary first" directive of section 0.8.1). The call sites need know nothing
about field categories, because `move` dispatches on the receiver.

What that buys is the behaviour the frozen copybook declares rather than
Python's assignment: `move "gl070" to ws-called` leaves EIGHT characters in a
`PIC X(8)` field, not five; an over-long `--ws-cd-args` loses its tail at
thirteen instead of widening the field; and a value moved into
`WS-Term-Code pic 99` or `WS-Process-Func pic 9` lands at the declared digit
count. Nothing is checked and nothing is reported on the way in (rule R-3): a
`MOVE` pads and truncates silently, and that silence is the whole of what the
COBOL does.

NO IMPORT-TIME SIDE EFFECTS
Importing this module binds names and evaluates a handful of pure in-memory
dataclass constructions, and has no other observable effect. It builds no
parser, configures no logging, opens no file, connection or directory, reads
nothing from its surroundings, starts nothing, and cannot fail for an
environmental reason. That is a hard requirement rather than a preference: the
scenario test suites import this package, and a module that did work at import
would make their arithmetic tier's "runs anywhere" promise untrue.

Stated precisely, because the connection binding above could be read as
contradicting it: the ENVIRONMENT IS READ ONLY WHEN A BINDER IS CALLED, never at
import. `bind_rdbms_connection` is imported here but not invoked here, and it
accepts an explicit `env` mapping, so a test can drive every binder without
touching the real environment. The three public binders CAN therefore now fail
for an environmental reason - deliberately, because a run that cannot reach the
provisioned database must stop before it writes - while importing this module
still cannot.

THE RULES THAT BIND THIS FILE
=============================
`review_rules` reports NO user rules document for this project, so the binding
constraints are the Agent Action Plan's own six (section 0.7.2):

R-1 No COBOL at run time. Nothing here spawns a child process, loads a foreign
    library or reaches the GnuCOBOL toolchain, and there is no import path from
    this package to the compiled comparison oracle. No option selects, invokes
    or compares against that oracle either - the oracle's own scripts drive
    these entry points from outside, never the reverse.
R-2 Zero binary floating point. `WS-Term-Code` is an `int` (from `pic 99`),
    `to-day` is a `str`, `Run-Date` is an `int` and the IRS `run-date` is a
    `str`. No binary-radix numeric type appears anywhere in this module, in a
    signature, an option type or a computation.
R-3 No added validation, no added field, no schema change, no concurrency.
    Nothing here judges a run date, extends a record or reaches a database, and
    execution is strictly sequential - there is no worker, pool or event loop
    to configure and no option that would create one. The six connection fields
    the binders fill already exist in [copybooks/wssystem.cob:L137-L144], so no
    field is added; the width and blank checks that guard them live in
    `rdbms_params` and apply to DEPLOYMENT CONFIGURATION rather than to any
    accounting value, which that module argues at length.
R-4 Legacy behaviour is reproduced, never corrected. Agent Action Plan section
    0.8.2, verbatim: "A defect reproduced is correct; a defect fixed is a
    failure." Each reproduction below carries its COBOL locator in a comment,
    as section 0.7.4 C-4 requires.
R-5 Full traceability - see the mandatory footer.
R-6 Compiled behaviour is the tie-breaker, so the clock is injected and the
    three genuinely open questions are marked in place rather than guessed.
"""

from __future__ import annotations

import argparse
import logging
import os
from collections.abc import Callable, Mapping
from typing import Final, NamedTuple

from acas_posting import clock, dates
from acas_posting.cli.rdbms_params import (
    RdbmsParamError,
    bind_rdbms_connection,
    resolve_transport_policy,
)
from acas_posting.cobol import move as cobol_move
from acas_posting.cobol.field import FieldDescriptor

#  `dal.facade` IS THE ONE DATA-ACCESS EDGE THIS MODULE HAS, and it is the
#  published seam rather than a handler. Agent Action Plan section 0.4.3 bars
#  `cli/*.py` from importing `dal.acas*` directly; `dal.facade` is what that bar
#  leaves open, and it is the same seam the twelve program modules use. It is
#  needed because the frozen menu shells this module is derived from
#  [general/general.cbl:L398-L419, L656-L692], [sales/sales.cbl:L351-L410,
#  L628-L657], [purchase/purchase.cbl:L346-L363, L621-L650],
#  [irs/irs.cbl:L494-L551, L755-L775] drive `acas000` themselves, before and
#  after every dispatch. Importing it still does no work: it opens no
#  connection, and nothing below runs at import time.
from acas_posting.dal import connection as dal_connection
from acas_posting.dal import facade

#  THE TRANSPORT-SECURITY VALUE OBJECT AND THE POLICY ERROR, from the module that
#  owns both. `TransportSecurity` is a frozen, slotted value object of four
#  optional strings and a bool, and `dal/connection.py` imports no handler, so
#  plan section 0.4.3's bar on a `cli` module reaching `dal.acas*` is not touched.
from acas_posting.dal.connection import ConnectionPolicyError, TransportSecurity

#  `FS-Reply`'s declared value set [copybooks/wsfnctn.cob:L38], from the module
#  that owns it, so that the ONE reply this layer tests - the key-1 read in
#  `aa010_get_system_recs`, which all four frozen menus test - is written against
#  the vocabulary rather than against a bare zero.
from acas_posting.dal.status import FsReply

#  The data-access layer's OWN redactor, imported rather than reimplemented so
#  the CLI and the handlers cannot disagree about what a safe diagnostic is.
from acas_posting.dal.status import redact_for_log
from acas_posting.records import calling_data as calling_data_record
from acas_posting.records.calling_data import WsCallingData
from acas_posting.records.file_access import FileAccess
from acas_posting.records.file_defs import FileDefs
from acas_posting.records.irs_system import IrsSystemParams
from acas_posting.records.maps03 import Maps03Ws
from acas_posting.records.system_dflt import SysDefaultRecord
from acas_posting.records.system_record import (
    GeneralLedgerBlock,
    SystemDataBlock,
    SystemRecord,
    carries_frozen_placeholder_rdbms_credentials,
)
from acas_posting.records.system_record_4 import SystemRecord4
from acas_posting.records.test_data_flags import AcasDalCommonData

__all__: Final[tuple[str, ...]] = (
    "RUN_DATE_FORMAT",
    "WS_CALLER_GENERAL",
    "WS_CALLER_SALES",
    "WS_CALLER_PURCHASE",
    "WS_CALLER_ACAS",
    "WS_DEL_LINK_DEFAULT",
    "WS_PROCESS_FUNC_DEFAULT",
    "WS_SUB_FUNCTION_DEFAULT",
    "WS_CD_ARGS_DEFAULT",
    "WS_TERM_CODE_DEFAULT",
    "GL_ABORT_TERM_CODE",
    "EXTRACT_MISSING_FILE_TERM_CODE",
    "SERIOUS_ERROR_THRESHOLD",
    #  The `acas000` key numbers and the store selector, transcribed from the
    #  menu shells rather than written as bare literals at each call site.
    "SYSTEM_FILE_KEY_PARAMS",
    "SYSTEM_FILE_KEY_DEFAULTS",
    "SYSTEM_FILE_KEY_TOTALS",
    "RDBMS_STORE_SELECTOR_DIGIT",
    # ---- the three linkage shapes, in COBOL parameter order ---------------
    "GlLinkage",
    "SlPlLinkage",
    "IrsLinkage",
    # ---- the menu shell's own WORKING-STORAGE and its acas000 traffic ------
    "MenuState",
    "IrsSystemSnapshot",
    "general_menu_state",
    "slpl_menu_state",
    "irs_menu_state",
    "aa010_get_system_recs",
    "overrewrite",
    "zz090_set_up_irs_system_data",
    "zz095_restore_irs_system_data",
    "eoj_persist_irs_system_data",
    #  The disposition of the key-1 test every menu makes before it dispatches
    #  [general/general.cbl:L412-L418]. Published so a caller driving the load
    #  itself can name the condition, and so the process boundary's report has a
    #  greppable class name.
    "SystemRecordUnavailableError",
    # ---- argparse fragments, one per route shape --------------------------
    "add_calling_data_arguments",
    "add_gl_linkage_arguments",
    "add_slpl_linkage_arguments",
    "add_irs_linkage_arguments",
    #  Shared by all three shapes rather than belonging to one, so it is listed
    #  after them: diagnostic verbosity is not part of any linkage.
    "add_log_level_argument",
    # ---- binders ----------------------------------------------------------
    "bind_calling_data",
    "bind_gl_linkage",
    "bind_slpl_linkage",
    "bind_irs_linkage",
    "bind_rdbms_connection",
    "install_connection_policy",
    "resolve_clock",
    # ---- the one configuration-failure contract, shared by every route ----
    #  A RE-EXPORT and one helper over it, not a second implementation:
    #  `cli/rdbms_params.py` owns the class and its frozen return codes, and this
    #  layer republishes both so that all seven entry points and the package
    #  router can catch the EXACT type without importing the adapter (finding
    #  CLI-09).
    "RdbmsParamError",
    "report_configuration_failure",
    # ---- the menus' database-affecting record paragraphs ------------------
    "FS_MYSQL_USED",
    "RDBMS_STORE_SELECTOR_DIGIT",
    "SYSTEM_FILE_KEY_DEFAULTS",
    "SYSTEM_FILE_KEY_PARAMS",
    "SYSTEM_FILE_KEY_TOTALS",
    "aa010_get_system_recs",
    "overrewrite",
    "zz095_restore_irs_system_data",
    # ---- the credential question, re-exported -----------------------------
    #  A RE-EXPORT, not a second implementation:
    #  `records/system_record.py` owns the four placeholder items and the
    #  predicate over them, and this layer republishes the predicate so that an
    #  entry point can ask the question without importing the data-access layer,
    #  which the per-directory import table of Agent Action Plan section 0.4.3
    #  forbids it to do. See `_bind_system_record` for what the answer means.
    "carries_frozen_placeholder_rdbms_credentials",
    "reset_term_code",
    "set_called",
    "is_serious_error",
    "exit_status_for",
    "irs_run_date_x8",
    # ---- the transport-security declaration, one contract for every route -
    #  No COBOL counterpart: the frozen bridge's connect passes six values and
    #  no transport policy at all [copybooks/mysql-procedures.cpy:L72-L77], so
    #  the migration has to decide it, and the caller is the only party that
    #  knows. See the section headed THE TRANSPORT-SECURITY DECLARATION.
    "TLS_CA_VARIABLE",
    "ALLOW_PLAINTEXT_VARIABLE",
    "add_transport_security_arguments",
    "bind_transport_security",
    "dal_options_for",
    "declare_connection_policy",
    # ---- the boundary: expected failures, and stated destructive intent ----
    #  See the section headed THE BOUNDARY. `ConnectionPolicyError` is re-exported
    #  so a route can name the exception it reports without importing the
    #  data-access layer itself.
    "ConnectionPolicyError",
    "EXPECTED_BOUNDARY_ERRORS",
    "ExplicitBooleanOptionalAction",
    "STATED_ACTION",
    "STATED_OPTIONS_ATTRIBUTE",
    "boundary_exit_status",
    "redact_boundary_error",
    "require_stated",
    "stated_explicitly",
)


# Agent Action Plan section 0.8.1 makes "data dictionary first" a directive rather than
# a preference: "every Python field definition cites its entry.


def _declared_calling_data() -> WsCallingData:
    """Return a fresh `WS-Calling-Data` holding only its declared defaults.

    A fresh instance each call, so nothing in this module holds shared mutable state at
    module scope and no later mutation can reach the constants derived below.

    Returns:
        A `WsCallingData` whose seven fields carry exactly what the record layer
            declares.
    """
    return WsCallingData()


def _declared_system_record() -> SystemRecord:
    """Return a fresh `SYSTEM-REC` holding only its declared defaults.

    Returns:
        A `SystemRecord` at its declared defaults. Nothing is loaded from the
        store HERE - `aa010_get_system_recs` does that and passes the
        result in. See Q-CLI-SYSREC-LOAD.
    """
    return SystemRecord()


#: Module logger. A library module attaches no handler and configures no root
#: logger - the seven entry points call `logging.basicConfig` inside their own
#: `main`, never at import. Every record this module emits is a diagnostic with
#: no database effect and no influence on control flow, which is what Agent
#: Action Plan section 0.3.4 requires of one.
_LOG: Final[logging.Logger] = logging.getLogger(__name__)


#  CONSTANTS  (section 8.1 of this module's brief)

#  The documented form of the `--run-date` argument. `to-day` is declared
#  `01 to-day pic x(10).` in each menu shell - [general/general.cbl:L357],
#  [sales/sales.cbl:L309], [purchase/purchase.cbl:L304], [irs/irs.cbl:L405] -
#  and the date-service copybook seeds it "00/00/0000" before filling in the
#  year, month and day [copybooks/Proc-ACAS-Mapser-RDB.cob:L73-L76], which is
#  what fixes the field order as day, month, century-year.
#  Separators other than "/" are accepted, because the migrated `maps04`
#  normalises ".", "," and "-" to "/" itself [common/maps04.cbl:L132-L134].
#  That is legacy tolerance faithfully carried over, not a convenience added
#  here, and it is why this constant names the CANONICAL form rather than the
#  only accepted one.
RUN_DATE_FORMAT: Final[str] = "DD/MM/CCYY"

WS_CALLER_GENERAL: Final[str] = "general"
WS_CALLER_SALES: Final[str] = "sales"
WS_CALLER_PURCHASE: Final[str] = "purchase"
# The top-level system-selection menu, which dispatches the four ledger menus rather
# than any posting program.
WS_CALLER_ACAS: Final[str] = "ACAS"

WS_DEL_LINK_DEFAULT: Final[str] = _declared_calling_data().ws_del_link

WS_PROCESS_FUNC_DEFAULT: Final[int] = _declared_calling_data().ws_process_func
WS_SUB_FUNCTION_DEFAULT: Final[int] = _declared_calling_data().ws_sub_function

# ANOMALY, REPRODUCED (rule R-4) `WS-CD-Args pic x(13)` [copybooks/wscall.cob:L14] -
# spaces, because NO menu shell ever assigns it.
WS_CD_ARGS_DEFAULT: Final[str] = _declared_calling_data().ws_cd_args

# REPRODUCED (rule R-4) `WS-Term-Code pic 99` [copybooks/wscall.cob:L10] - zero, and
# RESET IMMEDIATELY BEFORE EVERY `CALL`, not once per run.
WS_TERM_CODE_DEFAULT: Final[int] = _declared_calling_data().ws_term_code

GL_ABORT_TERM_CODE: Final[int] = 5

# Raised by the two extract programs when a file they need is missing, each followed
# immediately by `goback`: [sales/sl055.cbl:L344-L345] and
# [purchase/pl055.cbl:L286-L287].
EXTRACT_MISSING_FILE_TERM_CODE: Final[int] = 8

# REPRODUCED (rule R-4) The `> 7` boundary - "Got a serious (reported) error", in the
# maintainer's own words at [sales/sales.cbl:L691].
SERIOUS_ERROR_THRESHOLD: Final[int] = 7

#  THE `acas000` KEY NUMBERS, as the menu shells write them.
#  `acas000` is the ONE handler that dispatches on `File-Key-No`, because its
#  facade paragraph pins no key - `acas000.` [copybooks/Proc-ACAS-FH-Calls.cob:
#  L20-L24] is four operands with no `move ... to File-Key-No`, unlike every
#  other entity's, which pins 1. The caller therefore owns the key, and the
#  menus set it by hand before each verb: `move 4 to File-Key-No`
#  [general/general.cbl:L402], `move 2 to File-Key-No`
#  [general/general.cbl:L406] and `move 1 to File-Key-No`
#  [general/general.cbl:L410]. Named here so that no call site below carries a
#  bare 1, 2 or 4.
SYSTEM_FILE_KEY_PARAMS: Final[int] = 1  # SYSTEM-REC   - the system parameters
SYSTEM_FILE_KEY_DEFAULTS: Final[int] = 2  # SYSDEFLT-REC - the defaults record
SYSTEM_FILE_KEY_TOTALS: Final[int] = 4  # SYSTOT-REC   - the period totals

#  THE STORE SELECTOR, AND THE ONE PLACE THIS MODULE DEPARTS FROM THE MENUS.
#  `FA-RDBMS-Flat-Statuses` [copybooks/wsfnctn.cob:L72-L73] is a GROUP of two
#  `pic 9` items, so a group value of `"66"` means putting 6 in BOTH digits. The
#  handler reaches its RDBMS path only on that value - `if
#  FA-RDBMS-Flat-Statuses = "66"` [common/acas000.cbl:L352] - and the migrated
#  handler reproduces the same gate.
#
#  THE DEPARTURE, STATED PLAINLY. Every menu READ forces `"00"` instead - "Force
#  Cobol proc." [general/general.cbl:L401], [sales/sales.cbl:L353],
#  [purchase/purchase.cbl:L349], [irs/irs.cbl:L497] - because the frozen system
#  bootstraps from an ISAM parameter file on disk and only then uses the
#  credentials it finds there to reach the RDB. The migration has NO ISAM store:
#  Agent Action Plan section 0.2.1.1 maps the System entity to the `SYSTEM-REC`
#  TABLE, section 0.3.1 gives the data-access layer SQL only, and the connection
#  parameters arrive from the deployment contract through
#  `acas_posting/cli/rdbms_params.py` rather than from a file. There is
#  therefore only one store to select, and `"66"` selects it. The menus'
#  Cobol-file arm has no counterpart and is not reproduced; see
#  `aa010_get_system_recs` and `overrewrite`.
RDBMS_STORE_SELECTOR_DIGIT: Final[int] = 6

#  `pic 9` [copybooks/wscall.cob:L12-L13] - a single unsigned digit, so the
#  domain is 0 through 9. `range(0, 10)` materialised as a tuple so that the
#  values appear in `--help` and in an argparse error message in a stable
#  order. NOT a validation added by this module: it is the declared domain of
#  the field, and argparse rejecting a tenth value is the same refusal COBOL
#  makes structurally by having nowhere to put it.
_PIC_9_CHOICES: Final[tuple[int, ...]] = tuple(range(0, 10))

#  `05 Date-Form pic 9.` [copybooks/wssystem.cob:L128] with its three condition
#  names, `88 Date-UK value 1` [copybooks/wssystem.cob:L129],
#  `88 Date-USA value 2` [copybooks/wssystem.cob:L130] and
#  `88 Date-Intl value 3` [copybooks/wssystem.cob:L131], plus
#  `88 Date-Valid-Formats values 1 2 3` [copybooks/wssystem.cob:L132].
#
#  ⭐ M-05.  THE DOMAIN IS THE WHOLE `pic 9`, NOT THE THREE CONDITION-NAME VALUES,
#  and the difference was MEASURED against the frozen conversion section rather
#  than inferred from the condition names. This used to be `(1, 2, 3)` on the
#  reasoning that `Date-Valid-Formats` "is the source of these three choices".
#  Two facts overturn that:
#
#  (1) `Date-Valid-Formats` IS NEVER TESTED. A census of the whole checkout finds
#      it in exactly two places, its own declaration [copybooks/wssystem.cob:L132]
#      and a verbatim copy of that declaration inside an out-of-scope conversion
#      utility [common/acasconvert2.cbl:L190]. NOT ONE of the twelve in-scope
#      programs references it. It is a declared-but-unused condition name, so
#      deriving a command-line restriction from it invents a validation the
#      compiled cycle does not perform (rule R-3).
#
#  (2) `zz070-Convert-Date` ROUTES EVERY VALUE, and one of the values it routes it
#      also WRITES BACK. The section appears near-identically in nine of the twelve
#      programs; taking [general/gl070.cbl:L580-L596] as the reading:
#
#          L580  if       Date-Form = zero
#          L581           move 1 to Date-Form.        *> MUTATES the record
#          L582  if       Date-UK
#          L583           go to zz070-Exit.           *> 1 -> UK, unchanged
#          L584  if       Date-USA
#          L585-L588      ...swap month and days...
#          L589           go to zz070-Exit.           *> 2 -> USA
#          L591  *> So its International date format
#          L592-L595 ...                              *> EVERYTHING ELSE -> Intl
#
#      So zero is routed AND stored back as 1 - an observable write to the
#      `SYSTEM-REC.DATE-FORM` column, not merely a presentation choice - and 4
#      through 9 all fall through the two tests into the International branch.
#      Refusing them at the command line made a reachable state unreachable.
#
#  argparse rejecting a TENTH value is a different matter and stays: `pic 9` has
#  nowhere to put two digits, so that refusal is the field's own and not an
#  addition. Hence the domain published here is exactly `_PIC_9_CHOICES`.
_DATE_FORM_CHOICES: Final[tuple[int, ...]] = _PIC_9_CHOICES

#  The record's OWN declared default, read rather than typed. It is zero - which
#  is now inside `_DATE_FORM_CHOICES` above rather than outside it, so the default
#  and the accepted domain agree instead of coexisting by argparse's rule that
#  `choices` is checked only against a supplied value. Zero is not an
#  "invalid" default: `zz070-Convert-Date` handles it explicitly and turns it
#  into 1 [general/gl070.cbl:L580-L581].
_DATE_FORM_DEFAULT: Final[int] = _declared_system_record().system_data_block.date_form

# The IRS fan-out switch.
_IRS_INSTEAD_DEFAULT: Final[str] = (
    _declared_system_record().general_ledger_block.irs_instead
)


def _field_named(
    fields: tuple[FieldDescriptor, ...], cobol_name: str
) -> FieldDescriptor:
    """Return one descriptor out of a record block's own declared tuple.

    THE PICTURE IS READ, NEVER TRANSCRIBED. Every record module publishes its
    block's descriptors as a `FIELDS` class variable built from the generated
    data dictionary, so looking a field up by its VERBATIM COBOL NAME is how this
    layer obtains a receiving-field descriptor without writing a picture clause
    of its own - the "data dictionary first" directive of Agent Action Plan
    section 0.8.1, and rule R-5's requirement that every field cite its entry.

    Called at import time for a fixed, closed set of names, so a rename in the
    frozen copybook surfaces as an immediate failure rather than as a silently
    wrong width.

    Args:
        fields: the block's `FIELDS` tuple, in copybook declaration order.
        cobol_name: the field's name exactly as the copybook spells it, e.g.
            `"IRS-Instead"`. Compared case-insensitively, because COBOL names
            are case-insensitive and the copybooks are inconsistent about case.

    Returns:
        That field's `FieldDescriptor`.

    Raises:
        KeyError: no field of the block carries the name. A programming error,
            reported as one; nothing is guessed and no descriptor is fabricated.
    """
    wanted = cobol_name.casefold()
    for descriptor in fields:
        if descriptor.name.casefold() == wanted:
            return descriptor
    raise KeyError(
        f"no field named {cobol_name!r} in the record block's declared FIELDS"
    )


#  `05  Date-Form pic 9.` [copybooks/wssystem.cob:L128] - the receiving field of
#  the `--date-form` pin. ONE digit, so the store goes THROUGH the descriptor
#  rather than by assignment: a wider value is truncated by the receiving field
#  exactly as the frozen `MOVE` truncates it, and the library-caller path (a
#  namespace built in code, which argparse never confined to
#  `_DATE_FORM_CHOICES`) lands under the same picture clause as the command line.
_D_DATE_FORM: Final[FieldDescriptor] = _field_named(
    SystemDataBlock.FIELDS, "Date-Form"
)


#  `05  IRS-Instead pic x.` [copybooks/wssystem.cob:L179] - the receiving field
#  of the one `MOVE` `_bind_system_record` performs into `SYSTEM-REC` outside the
#  connection block and the two pinned date observables. ONE character wide, so
#  the `MOVE` is what turns an operator's "YES" into the "Y" the condition names
#  at [:L180] and [:L181] actually test.
_IRS_INSTEAD_FIELD: Final[FieldDescriptor] = _field_named(
    GeneralLedgerBlock.FIELDS, "IRS-Instead"
)


#  THE THREE LINKAGE CARRIERS
#  Each carrier holds one COBOL call shape's arguments IN THE COBOL PARAMETER
#  ORDER, so a call site reads the way a `CALL ... USING` reads and a reviewer can
#  diff the two argument lists line by line. `NamedTuple` rather than a frozen
#  dataclass: immutable by construction, splats natively with `*link` so an arity
#  mistake is a `TypeError` at the call site, and holds its members BY REFERENCE,
#  which is what COBOL linkage is.
#  THE CARRIER IS FROZEN; THE RECORD INSIDE IT IS NOT (rule R-4). COBOL passes a
#  group item by reference, so a callee writes into the CALLER's storage: `gl070`
#  SETS `WS-Term-Code` to 5 on finding a batch left open [general/gl070.cbl:L289]
#  and the menu READS it [general/general.cbl:L810-L811], so freezing the record
#  would lose the write-back and silently disable the abort gate.


class GlLinkage(NamedTuple):
    """Shape 1 - the General Ledger call shape, FOUR parameters.

    Attributes:
        calling_data: `01 WS-Calling-Data` [copybooks/wscall.cob:L6-L14]. MUTABLE ON
            PURPOSE - the callee writes `WS-Term-Code` back into it.
        system_record: `SYSTEM-REC`, the 169-column system record, carrying the pinned
            `Run-Date` [copybooks/wssystem.cob:L67].
        to_day: `to-day pic x(10)` in DD/MM/CCYY form - the THIRD argument, and a
            linkage parameter rather than a column.
        file_defs: `01 File-Defs.` [copybooks/wsnames.cob:L13], the file-name buffers,
            including the two `gl071` work-file names at
            [copybooks/wsnames.cob:L15-L16].
    """

    calling_data: WsCallingData
    system_record: SystemRecord
    to_day: str
    file_defs: FileDefs


class SlPlLinkage(NamedTuple):
    """Shape 2 - the Sales and Purchase call shape, FIVE parameters.

    Attributes:
        calling_data: as `GlLinkage.calling_data`, and mutable for the same reason.
        system_record: `SYSTEM-REC`, as `GlLinkage.system_record`.
        system_record_4: `SYSTOT-REC` [copybooks/wssys4.cob] - the period totals. The
            caller spells it `WS-System-Record-4`; the callee spells its own parameter
            `system-record-4` [sales/sl060.cbl:L397].
        to_day: `to-day pic x(10)` - the FOURTH argument in this shape.
        file_defs: as `GlLinkage.file_defs`.
    """

    calling_data: WsCallingData
    system_record: SystemRecord
    system_record_4: SystemRecord4
    to_day: str
    file_defs: FileDefs


class IrsLinkage(NamedTuple):
    """Shape 3 - the IRS call shape, THREE parameters.

    Materially different from the other two shapes, and the difference is not cosmetic:
    there is NO calling-data block and NO `to-day`. Two consequences follow, and both
    are honoured rather than smoothed away.

    Attributes:
        irs_system_params: `01 system-record.` [copybooks/irswssystem.cob:L13], renamed
            to `IRS-System-Params` by the `COPY ... REPLACING` at [irs/irs.cbl:L392].
            Its `03 run-date pic x(8)` [copybooks/irswssystem.cob:L14] is the eight-
            character form `irs_run_date_x8` produces.
        ws_system_record: `SYSTEM-REC` - the ACAS system record, carrying the
            maintainer's own comment `*> ACAS system rec.` at the call site
            [irs/irs.cbl:L669]. Carries the pinned binary `Run-Date`.
        file_defs: `01 File-Defs.` [copybooks/wsnames.cob:L13].
    """

    irs_system_params: IrsSystemParams
    ws_system_record: SystemRecord
    file_defs: FileDefs


class MenuState(NamedTuple):
    """The menu shell's OWN WORKING-STORAGE for its `acas000` traffic.

    Not linkage. Every one of the four menu shells declares these blocks for
    itself and passes them to `acas000` on each of its own verbs - `File-Access`
    [copybooks/wsfnctn.cob:L23-L64] and `ACAS-DAL-Common-data`
    [copybooks/Test-Data-Flags.cob:L6], the third and fifth operands of the
    facade's `CALL` [copybooks/Proc-ACAS-FH-Calls.cob:L20-L24]. They belong to
    the MENU, not to the posting program: a posting program has its own pair, and
    the two never meet, because a COBOL `CALL` copies no working storage.

    ONE INSTANCE PER ROUTE INVOCATION, created once and reused by the load and by
    the persist, exactly as one menu program's single `01 File-Access` serves both
    `aa010-Get-System-Recs` and `overrewrite`. Sharing it is what carries the open
    connection, the last status and the store selector from one to the other.

    Attributes:
        file_access: `01 File-Access.` The status block AND the vocabulary block:
            `logging_data.file_key_no` is the `File-Key-No` the menus set by
            hand, and `fa_rdbms_flat_statuses` is the store selector. Mutated in
            place by every verb.
        dal_common: `01 ACAS-DAL-Common-data.` The fifth operand. Carries the
            testing switches and nothing this layer reads.
        system_record_4: `WS-System-Record-4` - the period-totals record the
            General, Sales and Purchase menus load with key 4 and rewrite with
            key 4. `None` on the IRS route, whose menu reads key 1 only
            [irs/irs.cbl:L511-L512].
        default_record: `Default-Record` - the defaults record. Loaded and
            rewritten with key 2 by the GENERAL menu ALONE
            [general/general.cbl:L405-L407], [general/general.cbl:L663-L665];
            `None` everywhere else, because neither the Sales nor the Purchase
            menu touches key 2 at all and their `overrewrite` rewrites keys 1 and
            4 only [sales/sales.cbl:L628-L641],
            [purchase/purchase.cbl:L621-L634]. Reproduced as the asymmetry it is.
        handler_named_verbs: WHICH OF THE TWO FACADE VOCABULARIES THIS MENU DRIVES
            `acas000` THROUGH, and a behavioural property rather than a naming
            one. False for the General, Sales and Purchase menus, each of which
            copies [copybooks/Proc-ACAS-FH-Calls.cob] and performs the
            ENTITY-named `System-*` verbs [general/general.cbl:L411]; True for the
            IRS menu, which copies [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob]
            [irs/irs.cbl:L1035] and performs the HANDLER-named `acas000-*` verbs
            [irs/irs.cbl:L499, L512, L514]. See
            `_HANDLER_NAMED_SYSTEM_VERBS` for the three consequences and their
            locators; the decisive one is that the handler-named open family
            carries `acas000-Check-4-Errors` and can therefore end the menu
            program outright, which the entity-named set cannot. It lives on the
            menu state because the vocabulary belongs to the MENU PROGRAM: it is
            fixed for a whole session, and every verb site is already handed this
            block. Set by the three factories below and by nothing else.

    Note:
        `WS-Temp-System-Rec` [general/general.cbl:L359] has NO counterpart here,
        and its absence is a consequence of anomaly N9 rather than an omission.
        The COBOL needs it because `acas000` has ONE record buffer that four
        bridges reinterpret [common/acas000.cbl:L311], so rewriting key 2 or key
        4 requires moving another record ON TOP of `System-Record` and then
        moving the saved copy back. The migrated handler takes the buffer as an
        argument and the caller passes the record class matching the key, so
        nothing is ever overwritten and there is nothing to save or restore. The
        save/restore pair therefore collapses to nothing, which is recorded here
        so that a reader diffing `overrewrite` against the COBOL finds the two
        missing `move`s explained.
    """

    file_access: FileAccess
    dal_common: AcasDalCommonData
    system_record_4: SystemRecord4 | None = None
    default_record: SysDefaultRecord | None = None
    handler_named_verbs: bool = False


class IrsSystemSnapshot(NamedTuple):
    """The seven `WS-` values `zz090` captures and `zz095` compares against.

    Declared in the IRS menu's own WORKING-STORAGE with the maintainer's comment
    "Holds current values from prog. start" [irs/irs.cbl:L353-L359]::

         353      03  WS-Next-Post       pic 9(5) value zero.
         354      03  WS-Pass-Value      pic 9    value zero.
         355      03  WS-Save-Sequ       pic 9    value zero.
         356      03  WS-First-Time-Flag pic 9    value zero.
         357      03  WS-System-Work-Group pic x(18)  value spaces.
         358      03  WS-PL-App-Created  pic x    value space.
         359      03  WS-PL-Approp-AC    pic 9(5) value zero.

    `zz090` fills them from the loaded ACAS record at the same time as it fills
    `IRS-System-Params` [irs/irs.cbl:L953-L966], and `zz095` writes a value back
    into the ACAS record ONLY where the IRS side has since changed
    [irs/irs.cbl:L1011-L1027]. That "only where changed" is the whole point of
    the snapshot and is why it is a value object here: a tuple cannot be mutated
    by accident between the two, so the comparison `zz095` makes is the
    comparison the COBOL makes.
    """

    next_post: int
    pass_value: int
    save_sequ: int
    first_time_flag: int
    system_work_group: str
    pl_app_created: str
    pl_approp_ac: int


#  ARGPARSE FRAGMENTS
#  Four fragments, one per call shape plus the calling-data group, so a route
#  composes exactly the options its COBOL shape has and the router needs no
#  conditionals:
#      GL route     add_calling_data_arguments(p, default_caller=...)
#                   add_gl_linkage_arguments(p)
#      SL/PL route  add_calling_data_arguments(p, default_caller=...)
#                   add_slpl_linkage_arguments(p)
#      IRS route    add_irs_linkage_arguments(p)          <- and nothing else
#  Each fragment MUTATES the parser it is given and returns None, the argparse
#  idiom, which keeps a route's `build_parser` a flat sequence of calls. No
#  parser is constructed at module scope: importing this module must do no work.


def _add_run_date_argument(parser: argparse.ArgumentParser) -> None:
    """Add the REQUIRED `--run-date` option - the controlled clock's only input.

    `required=True` is the whole point and is not negotiable (rule R-6). There is no
    default, no fallback to the current day, no environment lookup and no test hook.

    Args:
        parser: the parser to add the option to. Mutated in place.
    """
    parser.add_argument(
        "--run-date",
        required=True,
        metavar=RUN_DATE_FORMAT,
        help=(
            "REQUIRED. The run date, canonically "
            f"{RUN_DATE_FORMAT} as the menu shells' `to-day pic x(10)` holds it "
            "(copybooks/Proc-ACAS-Mapser-RDB.cob:L77). Separators '.', ',' and "
            "'-' are also accepted, because the legacy date module normalises "
            "them itself. Pins BOTH observables: the text date and the binary "
            "Run-Date (copybooks/wssystem.cob:L67). There is deliberately no "
            "default - a run date is never taken from the system clock, so that "
            "two runs of one scenario are byte-identical. A date the legacy "
            "module rejects is NOT an error here: it yields Run-Date 0, exactly "
            "as the COBOL does."
        ),
    )


def _add_system_record_arguments(parser: argparse.ArgumentParser) -> None:
    """Add the two pinnable `SYSTEM-REC` options, and no others.

    Only two fields of the 169-column system record are settable from the command line,
    and the list is closed: extending it would add a field-level input the COBOL menus
    do not offer, which R-3 forbids.

    Args:
        parser: the parser to add the options to. Mutated in place.
    """
    parser.add_argument(
        "--date-form",
        type=int,
        choices=_DATE_FORM_CHOICES,
        default=_DATE_FORM_DEFAULT,
        help=(
            "SYSTEM-REC Date-Form (copybooks/wssystem.cob:L128-L131): "
            "1 = UK dd/mm/yyyy, 2 = USA mm/dd/yyyy, 3 = International "
            "yyyy/mm/dd. THE FIELD IS `pic 9` AND EVERY DIGIT IS ROUTED, so the "
            "whole 0-9 domain is accepted: zz070-Convert-Date "
            "(general/gl070.cbl:L580-L596) turns 0 into 1 AND WRITES IT BACK to "
            "the record, sends 1 to UK and 2 to USA, and falls 3 through 9 into "
            "the International branch. Governs date PRESENTATION, except for that "
            "one write-back of 0 -> 1, which is visible in the "
            "SYSTEM-REC.DATE-FORM column; no posted figure depends on it. "
            "Defaults to the record's own declared value."
        ),
    )
    parser.add_argument(
        "--irs-instead",
        metavar="CHAR",
        default=None,
        help=(
            "SYSTEM-REC IRS-Instead, the IRS fan-out switch "
            "(copybooks/wssystem.cob:L179-L181). ONE character: 'Y' = IRS "
            "instead of the General Ledger, 'B' = IRS as well as it, and "
            f"anything else - canonically {_IRS_INSTEAD_DEFAULT!r}, the "
            "record's own declared value - = off, General Ledger only. "
            "Those two are the "
            "field's ONLY condition names; there is no third value and in "
            "particular no 'N'. Not validated, because the pic x can hold any "
            "character and refusing one would invent a check the COBOL has not "
            "got. PIN THIS EXPLICITLY for every scenario: its state changes "
            "WHICH TABLES a run touches, so leaving it out makes the "
            "affected-table list ambiguous. Omitted leaves the field at the "
            "record layer's declared value, unwritten."
        ),
    )


def add_calling_data_arguments(
    parser: argparse.ArgumentParser, *, default_caller: str
) -> None:
    """Add the `WS-Calling-Data` option group - five of the seven fields.

    The five that a caller may legitimately set. The other two are deliberately absent,
    and their absence is part of the specification.

    Args:
        parser: the parser to add the options to. Mutated in place.
        default_caller: the dispatching menu's own identity, to default `--ws-caller`
            to.
    """
    parser.add_argument(
        "--ws-caller",
        default=default_caller,
        metavar="NAME",
        help=(
            "WS-Calling-Data WS-Caller pic x(8) (copybooks/wscall.cob:L8) - the "
            "identity of the dispatching menu. The COBOL literals are "
            f"'{WS_CALLER_GENERAL}' (general/general.cbl:L512), "
            f"'{WS_CALLER_SALES}' (sales/sales.cbl:L481) and "
            f"'{WS_CALLER_PURCHASE}' (purchase/purchase.cbl:L475). "
            f"Default for this route: '{default_caller}'."
        ),
    )
    parser.add_argument(
        "--ws-del-link",
        default=WS_DEL_LINK_DEFAULT,
        metavar="NAME",
        help=(
            "WS-Calling-Data WS-Del-Link pic x(8) (copybooks/wscall.cob:L9). "
            "Every menu clears it to spaces before a dispatch "
            "(general/general.cbl:L513), and no in-scope posting program reads "
            "it. Defaults to spaces at the declared width."
        ),
    )
    parser.add_argument(
        "--ws-process-func",
        type=int,
        choices=_PIC_9_CHOICES,
        default=WS_PROCESS_FUNC_DEFAULT,
        help=(
            "WS-Calling-Data WS-Process-Func pic 9 (copybooks/wscall.cob:L12), "
            "so one unsigned digit, 0-9. Cleared to zero with WS-Sub-Function "
            "before every menu draw (general/general.cbl:L505). Default 0."
        ),
    )
    parser.add_argument(
        "--ws-sub-function",
        type=int,
        choices=_PIC_9_CHOICES,
        default=WS_SUB_FUNCTION_DEFAULT,
        help=(
            "WS-Calling-Data WS-Sub-Function pic 9 (copybooks/wscall.cob:L13), "
            "one unsigned digit, 0-9. Cleared with WS-Process-Func in the same "
            "statement (general/general.cbl:L505). Default 0."
        ),
    )
    parser.add_argument(
        "--ws-cd-args",
        default=WS_CD_ARGS_DEFAULT,
        metavar="TEXT",
        help=(
            "WS-Calling-Data WS-CD-Args pic x(13) (copybooks/wscall.cob:L14) - "
            "the maintainer's own unattended-invocation slot, described at "
            "copybooks/wscall.cob:L1-L3 as being 'for passing extra info to "
            "called process that will help in a cron call by time via menu "
            "program. picked by position within WS-Args'. NO menu shell ever "
            "assigns it, so it defaults to spaces at the declared width; the "
            "shells only READ it, testing WS-CD-Args (1:5) = 'xl150' "
            "(sales/sales.cbl:L463)."
        ),
    )


def add_gl_linkage_arguments(parser: argparse.ArgumentParser) -> None:
    """Add the options Shape 1 needs: the required `--run-date`, plus `SYSTEM-REC`.

    Composed with `add_calling_data_arguments` by every General Ledger route, which is
    why the calling-data group is not repeated here. `file-defs` needs no options at
    all.

    Args:
        parser: the parser to add the options to. Mutated in place.
    """
    _add_run_date_argument(parser)
    _add_system_record_arguments(parser)


def add_slpl_linkage_arguments(parser: argparse.ArgumentParser) -> None:
    """Add the options Shape 2 needs: the required `--run-date`, plus `SYSTEM-REC`.

    The same option set as Shape 1, and deliberately a SEPARATE function rather than an
    alias.

    Args:
        parser: the parser to add the options to. Mutated in place.
    """
    _add_run_date_argument(parser)
    _add_system_record_arguments(parser)


def add_log_level_argument(parser: argparse.ArgumentParser) -> None:
    """Add `--log-level`, the one diagnostic-verbosity option all seven routes share.

    NOT A COBOL PARAMETER, AND NOT A GATE. The frozen programs write their
    diagnostics to a curses screen, and Agent Action Plan section 0.3.4 turns
    those into log records "at a severity matching the original's intent". A batch
    entry point therefore needs a severity threshold, and this is it: it has no
    database effect, cannot alter control flow, is never read by any migrated
    program and never reaches a `run` function. Where the six rules are silent,
    enterprise-standard best practice applies, and a batch job whose operator
    cannot choose between quiet and verbose is not production-ready.

    ONE FRAGMENT, SHARED, FOR THE SAME REASON THE LINKAGE BINDING IS SHARED. The
    option began as a private pair of constants inside `gl_end_of_cycle.py`, so it
    existed on exactly one of the seven entry points: `--log-level` worked for
    that route and was a usage error for the other six. That is not a cosmetic
    asymmetry, because `harness/run_python_scenario.sh` invokes the entry points
    DIRECTLY - `python -m acas_posting.cli.<route>` - rather than through the
    router, so six of the seven gave an operator no way to raise the level at all.
    Composing this fragment gives every route the same option with the same
    choices and the same default, and leaves one spelling that cannot drift.

    THE VOCABULARY IS THE ROUTER'S, RE-EXPORTED, NOT RESTATED. `LOG_LEVEL_NAMES`
    and `DEFAULT_LOG_LEVEL` are declared by `acas_posting.__main__`, which also
    owns the single `basicConfig` that consumes them, so a second copy here could
    fall out of step with the configurator that has the last word. The import is
    FUNCTION-LOCAL for the reason the seven `if __name__ == "__main__":` guards
    give: under `python -m acas_posting` the router is running as `__main__`, and
    a module-scope import of `acas_posting.__main__` from a module the router
    itself imports would materialise a second copy of it. Calling this function
    happens while a parser is being built, long after imports have settled.

    Args:
        parser: the parser to add the option to. Mutated in place.
    """
    from acas_posting.__main__ import DEFAULT_LOG_LEVEL, LOG_LEVEL_NAMES

    #  THE DEFAULT IS `None`, NOT A LEVEL NAME, and that is what makes the
    #  precedence between the two boundaries well defined rather than emergent.
    #  `None` means "the operator did not ask", so the entry point leaves the
    #  level alone and whatever the process boundary configured stands - which on
    #  a routed run is the router's own `--log-level`. A level name here would be
    #  indistinguishable from a supplied one, and an entry point reached through
    #  the router would silently reset a routed `--log-level=DEBUG` back down to
    #  INFO. The help text still names the effective default, because that is what
    #  an operator needs to know; `argparse` never shows this `None`.
    parser.add_argument(
        "--log-level",
        choices=LOG_LEVEL_NAMES,
        default=None,
        help=(
            "Severity threshold for the log records that replace the frozen "
            "program's screen output (Agent Action Plan section 0.3.4). "
            "Diagnostic only: it reaches no migrated program, alters no control "
            "flow and appears in no table dump. Logging is configured once, at "
            "the process boundary; supplying this option sets the level, so the "
            "last explicit request wins, and omitting it leaves the level the "
            f"boundary chose. Default {DEFAULT_LOG_LEVEL}."
        ),
    )


def add_irs_linkage_arguments(parser: argparse.ArgumentParser) -> None:
    """Add the options Shape 3 needs: the required `--run-date`, and nothing else.

    NONE of the calling-data options are added - not `--ws-caller`, not `--ws-del-link`,
    not `--ws-process-func`, not `--ws-sub-function` and not `--ws-cd-args` - because
    Shape 3 carries no calling-data block [irs/irs030.cbl:L552-L554], and the IRS entry
    point passes exactly three arguments.

    Args:
        parser: the parser to add the option to. Mutated in place.
    """
    _add_run_date_argument(parser)


#  THE CONTROLLED CLOCK  (section 8.4 of this module's brief, rule R-6)


def resolve_clock(run_date_text: str) -> clock.PinnedRunDate:
    """Pin both date observables from the `--run-date` text. One delegation.

    The whole of the clock contract in one call.

    Args:
        run_date_text: the date text as supplied on the command line, canonically
            DD/MM/CCYY. Whatever a caller typed, verbatim.

    Returns:
        The pinned pair.
    """
    return clock.pin_from_to_day(run_date_text)


# BINDERS A binder turns a parsed namespace into one linkage shape. Two conventions run
# through all four: 1. START FROM THE RECORD'S DECLARED DEFAULTS, THEN OVERWRITE.


def _menu_caller_for(program_id: str) -> str:
    """Return the menu identity that dispatches one posting program.

    Which menu shell owns which program is a fact of the frozen source, not a choice:
    general/general.cbl dispatches the `gl` programs, sales/sales.cbl the `sl` programs
    and purchase/purchase.cbl the `pl` programs.

    Args:
        program_id: the callee's program-id, as `"gl070"` or `"pl100"`.

    Returns:
        The dispatching menu's literal identity, or `WS-Caller`'s own declared default -
            spaces at its `PIC X(8)` width [copybooks/wscall.cob:L8] - for a program-id
            that no in-scope menu dispatches.
    """
    prefix = program_id.strip().lower()[:2]
    if prefix == "gl":
        return WS_CALLER_GENERAL
    if prefix == "sl":
        return WS_CALLER_SALES
    if prefix == "pl":
        return WS_CALLER_PURCHASE
    return _declared_calling_data().ws_caller


# =============================================================================
#  THE MENUS' DATABASE-AFFECTING RECORD PARAGRAPHS
# =============================================================================
#
#  ⭐ WHY A MENU PARAGRAPH IS REPRODUCED HERE AT ALL. The five menu programs are
#  out of scope AS PROGRAMS (Agent Action Plan section 0.2.2) - their screens,
#  their accept loops and their dispatch tables are not migrated. But two of
#  their paragraphs are not presentation: `aa010-Get-System-Recs` READS the
#  system records the twelve posting programs are then called WITH, and
#  `overrewrite` WRITES back what those programs changed. Section 0.8.5 makes an
#  empty ordering-normalised table diff the acceptance condition, so a Python run
#  that skipped either would differ from a COBOL run in two of the twenty-two
#  compared tables - and, worse, would call every program with fabricated
#  accounting state. Section 0.3.4's rule is the one that decides it: a menu
#  statement with no database effect is dropped, a menu statement that gates or
#  performs a database write is preserved. These two perform one.
#
#  WHAT IS *NOT* REPRODUCED, AND IS RECORDED AS AN OMISSION (rule R-5):
#    * THE COBOL FLAT-FILE HALF. Both paragraphs work the indexed store as well
#      as the relational one - `move zeros to File-System-Used` / `move "00" to
#      FA-RDBMS-Flat-Statuses` [sales/sales.cbl:L354-L355, :L644-L646] - and the
#      migration has no flat-file leg at all: every handler's flat path raises
#      "not migrated". Only the RDB half is reproduced. This is the one point
#      where the reading side cannot be literal, and the frozen source explains
#      why it does not matter: the RDB block in `aa010-Get-System-Recs` is
#      commented out under the maintainer's own heading "BY PASS THIS CODE AS THE
#      FILE WILL ALWAYS BE CURRENT" [sales/sales.cbl:L370-L372], i.e. the two
#      stores are held to carry the same content, and `common/masterLD.sh` seeds
#      them from the same flat files [common/masterLD.sh:L44-L115].
#    * `sys002` RECOVERY. Both paragraphs' callers call the setup program when
#      the parameter file is missing [sales/sales.cbl:L344-L348, :L361-L366];
#      `common/sys002.cbl` is out of scope (section 0.2.2, non-posting
#      utilities), so a failing read is REPORTED and the status returned, and no
#      record is invented to stand in for one.
#    * THE SCREEN PATHS: the credential echoes, `display SY011`, the
#      acknowledgement accepts, and the backup-script branch `pre-overrewrite`
#      [sales/sales.cbl:L609-L625] whose only database effect is the
#      `perform overrewrite` reproduced below.
# =============================================================================

#: `88  FS-MySql-Used  value 1.` [copybooks/wssystem.cob:L114] - the value
#: `File-System-Used` [copybooks/wssystem.cob:L112] must hold for a handler to
#: take its relational leg. Every handler tests the same thing, e.g. `int(...
#: file_system_used) == 0` selects the unmigrated indexed leg.
FS_MYSQL_USED: Final[int] = 1


#  THE MENU SHELL PARAGRAPHS THIS MODULE REPRODUCES LIVE FURTHER DOWN, beside
#  `MenuState` and the three factories - `aa010_get_system_recs`, `overrewrite`,
#  `zz090_set_up_irs_system_data`, `zz095_restore_irs_system_data` and
#  `eoj_persist_irs_system_data`. One implementation of each paragraph, reached
#  by all seven routes through the three linkage binders.


def _stated_transport_security(
    namespace: argparse.Namespace | None,
    env: Mapping[str, str] | None,
) -> TransportSecurity | None:
    """Return the operator's own transport declaration, or None if there is none.

    `add_transport_security_arguments` is composed by every route, so a parsed
    namespace normally carries the four options; a caller that built its own
    namespace, or a route that omitted them, carries none. Only a namespace with
    at least one of them stated is treated as a declaration, so an operator who
    said nothing still gets the deployment contract rather than an empty policy
    that would silently outrank it.

    Args:
        namespace: the parsed arguments, or None.
        env: the environment `bind_transport_security` falls back to.

    Returns:
        The declared policy, or None when nothing was declared on the command
        line.
    """
    if namespace is None:
        return None
    stated = any(
        getattr(namespace, name, None) not in (None, False)
        for name in ("db_tls_ca", "db_tls_cert", "db_tls_key", "db_allow_plaintext")
    )
    if not stated:
        return None
    return bind_transport_security(namespace, environ=env)


def install_connection_policy(
    env: Mapping[str, str] | None = None,
    *,
    namespace: argparse.Namespace | None = None,
) -> dal_connection.ConnectionPolicy:
    """Install the ONE connection policy of the run. THE policy boundary.

    ⭐ THIS IS THE ONLY PLACE IN THE SHIPPED PACKAGE THAT DECLARES A CONNECTION
    POLICY, and it is reached by all seven entry points because
    `_bind_system_record` calls it and all three linkage binders go through
    `_bind_system_record`. Every handler in `acas_posting/dal/` opens without a
    declaration of its own, and `dal/connection.py` resolves that omission from
    the policy installed here - so one deployment decision governs all twenty
    handlers, whichever table a route happens to touch.

    NO FROZEN COUNTERPART, AND NOTHING COMPARED MOVES BY A CHARACTER. The
    compiled system's transport is whatever `MySQL_real_connect` negotiates with
    a literal zero client-flag word [copybooks/mysql-procedures.cpy:L72-L77] -
    that is to say plaintext, always - and it applies no check of its own to the
    host or the credential. With nothing set in the deployment contract this
    function therefore installs a policy that declares nothing, the data-access
    layer reports what is exposed and connects, and the migrated cycle behaves
    exactly as the compiled one does (rule R-3). What the deployment CAN ask for -
    TLS with verification, or a refusal instead of a report - it asks for in the
    contract, once, outside the accounting path.

    WHY IT IS NOT AN ARGPARSE OPTION. The same reason the six connection
    parameters are not: the frozen counterpart takes its settings from a source
    outside the command line [common/acas-get-params.cbl:L30], the closed list of
    settable `SYSTEM-REC` options this module publishes stays closed (rule R-3),
    and a certificate path on a command line is a process-listing leak waiting to
    happen. `acas_posting/cli/rdbms_params.py` owns the reading; this function
    owns the installing.

    Idempotent: called once per bound linkage, and installing the same resolved
    policy twice is indistinguishable from installing it once.

    THE OPERATOR MAY STILL DECLARE ONE ON THE COMMAND LINE, and when a route
    published `add_transport_security_arguments` the parsed namespace is passed
    here so that declaration WINS over the deployment contract. Precedence is
    therefore command line, then contract, then nothing - and "nothing" leaves
    the migrated cycle behaving exactly as the compiled one does. Without this
    the published options would be a knob that does nothing, which is worse than
    no knob because it invites the wrong conclusion.

    Args:
        env: The mapping the declaration is resolved from, passed through to
            `rdbms_params.resolve_transport_policy`. The process environment when
            omitted, which is the case in a real run. This module never reaches
            that environment itself - the adapter does, and only when called.
        namespace: The parsed arguments, when the calling route published the
            transport options. `None`, or a namespace carrying none of them,
            leaves the contract as the only source.

    Returns:
        The policy installed, so that a caller can report or assert on it. It is
        also retrievable from `dal.connection.connection_policy()`.

    Raises:
        ValueError: from `bind_transport_security`, when the operator gave
            `--db-tls-cert` without `--db-tls-key` or the reverse.
    """
    stated = _stated_transport_security(namespace, env)
    if stated is not None:
        policy = dal_connection.ConnectionPolicy(transport=stated)
        dal_connection.set_connection_policy(policy)
        return policy

    declaration = resolve_transport_policy(env)

    #  A `TransportSecurity` is built only when the deployment actually declared
    #  something. Passing `None` is not the same as passing an instance at its
    #  defaults would be if this ever gained a third state: `None` means "no
    #  declaration", and `dal/connection.py` documents that reading.
    transport: dal_connection.TransportSecurity | None = None
    if (
        declaration.ca_file
        or declaration.certificate_file
        or declaration.key_file
        or declaration.isolated_oracle
    ):
        transport = dal_connection.TransportSecurity(
            ca_file=declaration.ca_file,
            certificate_file=declaration.certificate_file,
            key_file=declaration.key_file,
            isolated_oracle=declaration.isolated_oracle,
        )

    policy = dal_connection.ConnectionPolicy(
        transport=transport,
        require_encrypted_transport=declaration.require_encrypted_transport,
        require_declared_placeholder_credentials=(
            declaration.require_declared_placeholder_credentials
        ),
        allow_frozen_placeholder_credentials=(
            declaration.allow_frozen_placeholder_credentials
        ),
    )
    dal_connection.set_connection_policy(policy)
    return policy


def _bind_system_record(
    ns: argparse.Namespace,
    pinned: clock.PinnedRunDate,
    *,
    env: Mapping[str, str] | None = None,
    system_record: SystemRecord | None = None,
) -> SystemRecord:
    """Build `SYSTEM-REC` with the three pinned fields and the six RDBMS fields.

    At most nine of the 169 columns are set here and the list is closed. At most
    three come from argv and the clock: `Run-Date` from the clock always, and
    `Date-Form` and `IRS-Instead` from argv when the route offered them AND a
    value was actually supplied. The other six are the connection parameters,
    which come from the deployment contract through
    `acas_posting/cli/rdbms_params.py`. Everything else comes from the record
    handed in - or, when none is, keeps the record layer's declared default. So
    does `IRS-Instead` when the option is omitted: it is left unwritten rather
    than overwritten, because its off state is a space and a space cannot be told
    from "absent" by a truth test.

    THE 160 OTHER COLUMNS BELONG TO THE STORE, NOT TO argv  (finding CLI-02)
    ======================================================================
    The frozen menu shell READS `SYSTEM-REC` before it dispatches anything -
    `aa010-Get-System-Recs.` [general/general.cbl:L385-L460],
    [sales/sales.cbl:L351-L404], [purchase/purchase.cbl:L346-L398],
    [irs/irs.cbl:L507-L552] - so every callee sees the STORED accounting cycle
    `Scycle` [copybooks/wssystem.cob:L63], period, current quarter, ledger levels,
    control accounts, next batch number and the whole IRS entry block. A record
    built purely at declared defaults carries zeroes and spaces in all of them,
    and a posting cycle driven from zeroes posts differently.

    `system_record` is therefore the record the caller has ALREADY LOADED through
    `aa010_get_system_recs`, which is the migrated menu boundary. It is
    mutated in place and returned, exactly as the COBOL keeps writing into the one
    `01 SYSTEM-REC` the shell read. Omitting it keeps the declared-default
    behaviour, which is what a caller that only wants to inspect a bound linkage
    shape wants and what the arithmetic-tier tests use; a REAL run passes one.

    THE SIX CONNECTION FIELDS ARE RE-APPLIED OVER A LOADED RECORD, deliberately.
    The stored row may hold the copybook's own placeholder credentials, and the
    frozen load programs refuse to take these six from the store for exactly that
    reason - `if RDBMS-DB-Name = spaces or FS-Cobol-Files-Used`
    [common/glbatchLD.cbl:L238-L239] - loading them from an external parameter
    source instead [common/glbatchLD.cbl:L262-L267]. `menu_state` captures what
    the store held and restores it before any rewrite, so the six columns of the
    compared table are left exactly as the run found them.

    WHY THE SIX CONNECTION FIELDS ARE FILLED HERE. `SYSTEM-REC` is the ONLY
    carrier by which a connection parameter reaches the data-access layer: that
    layer copies `RDBMS-DB-Name`, `RDBMS-User`, `RDBMS-Passwd`, `RDBMS-Port`,
    `RDBMS-Host` and `RDBMS-Socket` into `RDB-Data`, reproducing
    [common/acas008.cbl:L558-L563], and hands the result to the driver. Left at
    their declared defaults [copybooks/wssystem.cob:L137-L144] those fields are
    the copybook's own placeholders - the literal user `"ACAS-User"`, the literal
    password `"PaSsWoRd"` and a blank host - so a run would not reach the
    database the operator provisioned. The frozen tree solves this the same way
    and in the same place: every `common/*LD.cbl` load program performs six
    `MOVE` statements into these very fields right after building its own system
    record [common/glbatchLD.cbl:L262-L267].

    THE FOUR RDBMS COLUMNS ARE NOT DEPLOYMENT SETTINGS, AND THIS LAYER OFFERS NO
    OPTION FOR THEM. `RDBMS-DB-Name`, `RDBMS-User`, `RDBMS-Passwd` and
    `RDBMS-Port` [copybooks/wssystem.cob:L137-L139, :L142] are `value` literals
    in the frozen copybook, each annotated `*> change in setup` by the
    maintainer, and the record layer therefore reproduces them byte-for-byte -
    `SYSTEM-REC` is one of the 22 tables the scenario comparison dumps, so its
    declared defaults are diff-visible and moving one would move a compared value
    (rule R-4). Three consequences bear directly on how an entry point behaves:

    * NO OPTION IS ADDED FOR THEM. The list above stays closed at three. A
      `--rdbms-user` would be a new input the frozen source does not have (rule
      R-3), and it would put a password on a command line where every process on
      the machine can read it.
    * THIS MODULE ITSELF READS NOTHING FROM THE SURROUNDINGS. It touches no
      environment variable, no dotenv file and no parameter file. The six
      connection fields are resolved by the sibling adapter
      `acas_posting/cli/rdbms_params.py`, which reproduces the frozen
      `common/acas-get-params.cbl` keyword contract, and only when it is called
      from here. The RUN DATE is untouched by that and still arrives only as
      `--run-date` through the pinned clock, so an ambient input can still not
      make two runs of one scenario differ (rule R-6).
    * A RECORD STILL CARRYING THE SHIPPED PLACEHOLDERS IS REPORTED DOWNSTREAM,
      NOT REFUSED. If the deployment contract supplies the copybook's own
      literals, `acas_posting/dal/connection.py` logs the exposure and connects,
      exactly as the compiled program does - it hands the row's values to the
      server and reports what the server says - and it refuses only when the
      deployment installed a `ConnectionPolicy` asking it to. Use the re-exported
      `carries_frozen_placeholder_rdbms_credentials` to find out which situation
      a given record is in; this layer only reports, it does not reject, because
      rejecting would be a validation added to the migrated cycle (rule R-3).

    Args:
        ns: the parsed namespace. `date_form` and `irs_instead` are read
            tolerantly, so a route that did not add them is served identically.
            No connection parameter is read from it - see the note below.
        pinned: the pinned pair from `resolve_clock`. Only `run_date` is used;
            the text observable travels as its own linkage parameter in Shapes 1
            and 2 and does not exist in Shape 3.
        env: the mapping the connection parameters are resolved from, passed
            through to `bind_rdbms_connection`. The process environment when
            omitted, which is the case in a real run. This module never reaches
            that environment itself - the adapter does, and only when called.
        system_record: the `SYSTEM-REC` the caller has already read from the
            store through `aa010_get_system_recs`, mutated in place and
            returned. `None` builds one at its declared defaults, which is the
            shape a caller inspecting a linkage without a database wants.

    Returns:
        The system record for this run, carrying real connection values.

    Raises:
        rdbms_params.RdbmsParamError: the deployment contract is ABSENT - not one
            of the six variables is set. Deliberately not caught: it reproduces
            `move 8 to LK-Return / goback` [common/acas-get-params.cbl:L174-L178],
            whose frozen callers abort on it [common/glbatchLD.cbl:L244-L249], so
            a run that has no contract at all stops before it writes anything.
            NOT raised for a contract that is merely awkward - a blank, spaced or
            over-long value is transformed exactly as the frozen reader transforms
            it (M-06); call `rdbms_params.audit_deployment_contract` to be warned
            about those.
    """
    #  ⭐ THE SUPPLIED RECORD IS THE RECORD, AND REPLACING IT WOULD BREAK COBOL
    #  LINKAGE. A COBOL `CALL ... USING` passes a group item BY REFERENCE: the
    #  callee writes into the CALLER's storage, and the menu shell holds exactly
    #  one `01 SYSTEM-REC` that its load fills, its `CALL` hands over and its
    #  `overrewrite` writes back [general/general.cbl:L411, L715-L718, L662-L663].
    #  Building a second record here and pinning that instead would silently
    #  discard every accounting field the caller had already loaded or seeded, and
    #  would leave the object the caller still holds - and `overrewrite` still
    #  persists - unrelated to the one the callee received. So a supplied instance
    #  is MUTATED IN PLACE and returned; only its absence builds one, which is what
    #  a caller inspecting a linkage shape without a database gets (finding CLI-02).
    if system_record is None:
        system_record = _declared_system_record()
    _apply_cli_pins(system_record, ns, pinned, env=env)
    return system_record


def _apply_cli_pins(
    system_record: SystemRecord,
    ns: argparse.Namespace,
    pinned: clock.PinnedRunDate,
    *,
    env: Mapping[str, str] | None = None,
) -> None:
    """Write the six connection fields and the three pinned fields into a record.

    CALLED TWICE PER ROUTE, and that is the point of it being a function. Once by
    `_bind_system_record` on the freshly declared record, and once by
    `aa010_get_system_recs` on the record just loaded from the store. One
    implementation means the two applications cannot drift apart.

    WHY THE SECOND APPLICATION IS NEEDED, field by field:

    * THE SIX CONNECTION FIELDS. A row read out of the store carries whatever
      the row holds, which for a seeded database is the copybook's own
      placeholder literals [copybooks/wssystem.cob:L137-L144]. The frozen system
      has the same problem and answers it the same way: the load programs REFUSE
      to take these from a record - `if RDBMS-DB-Name = spaces or
      FS-Cobol-Files-Used` [common/glbatchLD.cbl:L238-L239] - and read an
      external parameter file instead. Leaving the row's values in place would
      also break the very next handler call, because `ba010-Initialise` copies
      `RDBMS-*` OUT of this record into `File-Access.RDB-Data`, so the
      placeholders would become the connection.
    * `Run-Date`. The controlled clock's diff-visible observable, mandated by
      Agent Action Plan sections 0.1.1 and 0.8.1 to be injected AT THE CLI
      BOUNDARY. See the AMBIGUITY note in `aa010_get_system_recs` for the frozen
      derivation this supersedes and why.
    * `Date-Form` and `IRS-Instead`. The two settable options the closed list of
      this module publishes. Re-applied so that an option a caller supplied is
      not silently discarded by the load.

    Args:
        system_record: the record to write into, mutated in place.
        ns: the parsed namespace. `date_form` and `irs_instead` are read
            tolerantly, so a route that did not add them is served identically.
        pinned: the pinned pair from `resolve_clock`. Only `run_date` is used.
        env: the mapping the connection parameters are resolved from.

    Raises:
        rdbms_params.RdbmsParamError: the deployment contract is absent or
            unusable. Deliberately not caught.
    """
    #  THE SIX CONNECTION FIELDS, from the deployment contract. Filled FIRST, so
    #  that a MISSING contract fails before any other work is done - "missing"
    #  meaning not one of the six variables is set, which is the counterpart of
    #  `move 8 to LK-Return / goback` [common/acas-get-params.cbl:L174-L178] and
    #  the frozen program's only refusal this transport can express.
    #
    #  ⭐ M-06.  IT NO LONGER FAILS FOR AN *UNUSABLE* CONTRACT, and it used to.
    #  A blank required value, a value containing whitespace and a value longer
    #  than its carrier all raised `RdbmsParamError` from here. The frozen reader
    #  refuses none of the three - it cuts at the first space
    #  [common/acas-get-params.cbl:L193-L199] and truncates at the receiving
    #  carrier [common/acas-get-params.cbl:L204-L221], both silently - so the
    #  adapter now reproduces those transformations and publishes
    #  `rdbms_params.audit_deployment_contract` for a caller that wants the three
    #  concerns as warnings. Nothing on this path calls it.
    #
    #  NOT from argv, and that is deliberate rather than an oversight. The frozen
    #  counterpart takes its values from a source outside the command line -
    #  `common/acas-get-params.cbl` reads a keyword file and its remarks say
    #  "Uses Current directory only." [common/acas-get-params.cbl:L30] - so no
    #  option is added here either. Two consequences follow: the closed list of
    #  two settable SYSTEM-REC options this module publishes stays closed
    #  (rule R-3), and a password never appears in argv, in a process listing or
    #  in a shell history. The RUN DATE is untouched by this and still arrives
    #  ONLY as `--run-date` through the pinned clock (rule R-6).
    bind_rdbms_connection(system_record, env=env)

    #  THE ONE CONNECTION POLICY, INSTALLED HERE AND NOWHERE ELSE. All three
    #  linkage binders funnel through this function, so every one of the seven
    #  entry points establishes the deployment's declaration before any handler
    #  can open anything, and no handler has to be told about it. See
    #  `install_connection_policy` for why it is not an argparse option and why
    #  its empty default leaves the migrated cycle behaving as the compiled one.
    install_connection_policy(env, namespace=ns)

    #  [copybooks/wssystem.cob:L67] `05 Run-Date binary-long.` - an `int`, never
    #  a binary-radix numeric type (rule R-2), and from the pinned clock only:
    #  never from argv directly and never from an ambient source (rule R-6).
    #  This is the DIFF-VISIBLE observable of the pair - it is the column
    #  SYSTEM-REC.RUN-DAT and so appears in every table dump the scenario
    #  comparison inspects.
    system_record.system_data_block.run_date = pinned.run_date

    #  [copybooks/wssystem.cob:L128-L131] presentation only, save for the
    #  write-back of zero that `zz070-Convert-Date` performs inside the callee
    #  [general/gl070.cbl:L580-L581].
    #
    #  ⭐ M-05. STORED THROUGH THE FIELD'S OWN DESCRIPTOR, not assigned. `pic 9`
    #  is one digit, so a value outside that width is truncated by the receiving
    #  field exactly as the frozen `MOVE` truncates it - the semantics belong to
    #  `acas_posting.cobol.move` and are delegated whole rather than restated
    #  here (Agent Action Plan section 0.3.1). argparse already confines the
    #  command line to `_DATE_FORM_CHOICES`, but this function is also called
    #  with namespaces a library caller built, and the descriptor is what makes
    #  the two paths agree.
    system_record.system_data_block.date_form = cobol_move.move(
        getattr(ns, "date_form", _DATE_FORM_DEFAULT), _D_DATE_FORM
    )

    #  [copybooks/wssystem.cob:L179-L181] the fan-out switch, which changes
    #  WHICH TABLES a run touches - hence pinnable, per Agent Action Plan
    #  section 0.6.4.
    #
    #  `is None` rather than a truth test, and for the same reason `WS-Caller`
    #  uses one in `bind_calling_data`: the OFF state of this field is a SPACE,
    #  and an empty or space-filled value is a legitimate pin that must not be
    #  mistaken for "absent". An omitted option leaves the field exactly as the
    #  record layer declared it - unwritten, not overwritten with a default that
    #  happens to equal it.
    #
    #  RECEIVING-FIELD SEMANTICS ARE APPLIED HERE TOO, and their absence was a
    #  defect. `IRS-Instead` is `pic x` [copybooks/wssystem.cob:L179] - ONE
    #  character - so a `MOVE` of "YES" leaves "Y" in it and a `MOVE` of "" or
    #  "  " leaves a single space. A Python assignment left "YES" in the field
    #  instead, and every reader of the switch tests it against a one-character
    #  literal - `88 IRS-Used value "Y"` [:L180] and `88 IRS-Both-Used value "B"`
    #  [:L181], tested at three sites in each of the four Sales and Purchase
    #  posting programs, e.g. [sales/sl060.cbl:L1039] - so "YES" would have
    #  tested FALSE and silently suppressed the whole IRS fan-out, changing which
    #  tables a run touches (Agent Action Plan section 0.6.4).
    #
    #  Nothing is validated and nothing is rejected on the way in (rule R-3):
    #  section 0.1.2's transformation rule 11 requires the sending-field to
    #  receiving-field rules, and a `MOVE` pads and truncates in silence. The
    #  descriptor is the RECORD LAYER'S OWN, found by the field's verbatim COBOL
    #  name in `GeneralLedgerBlock.FIELDS`, so the picture comes from the
    #  generated data dictionary and is never transcribed here (rule R-5, and the
    #  "data dictionary first" directive of section 0.8.1).
    supplied_irs_instead = getattr(ns, "irs_instead", None)
    if supplied_irs_instead is not None:
        system_record.general_ledger_block.irs_instead = cobol_move.move(
            supplied_irs_instead, _IRS_INSTEAD_FIELD
        )

    #  Q-CLI-SYSREC-LOAD, RE-SETTLED AGAINST THE AGENT ACTION PLAN.
    #
    #  THE QUESTION. In the COBOL the MENU SHELL loads SYSTEM-REC and SYSTOT-REC
    #  from the store before the `CALL` and rewrites them afterwards in
    #  `overrewrite` [general/general.cbl:L656-L692], [sales/sales.cbl:L628-L657],
    #  [purchase/purchase.cbl:L621-L650] - each of which opens `acas000`, rewrites
    #  key 1 (SYSTEM-REC) and key 4 (SYSTOT-REC), and closes; the General menu
    #  rewrites key 2 (SYSDEFLT-REC) as well. Should the Python cycle load and
    #  rewrite them too, and if so, where?
    #
    #  THE MEASUREMENT THAT FRAMES IT. Not one of the twelve in-scope posting
    #  programs performs ANY system-record or totals-record I/O. Grepping all
    #  twelve for `System-Read`, `System-Rewrite`, `System-Open`, `System-Close`
    #  and `acas000` returns exactly one line, and it is a dated remark in a
    #  change history [irs/irs030.cbl:L97], not a statement. The nine
    #  period-total writes the Agent Action Plan enumerates in section 0.6.4 are
    #  in-memory arithmetic on the linkage record - `add ws-inv-amt to
    #  sl-invoices-this-month` [sales/sl055.cbl:L675] - and the menu's
    #  `overrewrite` is their SOLE writer to the store, performed after a
    #  successful call as well as after a failed one: `if ws-term-code < 8 /
    #  perform overrewrite` "Update sys4 and system recs in case of changes"
    #  [sales/sales.cbl:L708-L709], [purchase/purchase.cbl:L701-L702]. Adding that
    #  write to a program module would be added behaviour (rule R-3); putting it
    #  at the menu boundary is where the frozen source has it.
    #
    #  THE RESOLUTION: THE CLI LOADS AND PERSISTS. This module publishes
    #  `aa010_get_system_recs` and `overrewrite`, each named after the paragraph
    #  it reproduces, and the seven routes call them around their dispatches. The
    #  Agent Action Plan requires it and leaves no alternative:
    #
    #    * section 0.4.1.1 derives every CLI entry point FROM a menu paragraph -
    #      `gl_post_cycle.py` "from general/general.cbl load08", and so on for all
    #      seven. The menus are excluded as PROGRAMS to migrate wholesale; the
    #      dispatch behaviour the routes are built out of is the plan's own
    #      source for those files, and the load and the persist are part of it;
    #    * section 0.3.4 says exactly what is dropped from a menu, and it is
    #      PRESENTATION: "Diagnostic displays with no database effect become log
    #      records", "Accept prompts that gate a database write become explicit
    #      CLI parameters". A statement WITH a database effect is not on that
    #      list, and `overrewrite` is nothing but database effect;
    #    * section 0.8.5 makes the acceptance test an EMPTY ordering-normalised
    #      diff on the affected tables. SYSTOT-REC is affected - the nine
    #      period-total writes mutate it and `overrewrite` is their only writer -
    #      so a Python run that never rewrites it cannot produce an empty diff
    #      against a COBOL run that does;
    #    * section 0.4.3's import table bars this layer from `dal.acas*`, not
    #      from `dal.facade`. The facade is the published seam and is what the
    #      twelve program modules themselves use, so the load is reachable from
    #      here without touching a handler module.
    #
    #  AND NOT IN THE PROGRAM LAYER. Putting it there instead would violate rule
    #  R-3, because the twelve frozen programs, as measured above, do not read or
    #  write these records at all. The menu does; the menu's counterpart is the
    #  route; so the route does.
    #
    #  AMBIGUITY Q-CLI-SYSREC-PINS. After the load, this function is applied a
    #  SECOND time, so the six connection fields and the three pinned fields
    #  overwrite whatever the loaded row held for them. For the connection fields
    #  that is not in question - see `_apply_cli_pins`, and the frozen loaders'
    #  own refusal to trust a record. For `Run-Date`, `Date-Form` and
    #  `IRS-Instead` it means the CLI wins over the row, and the consequence is
    #  that a scenario must seed those three columns to agree with the options it
    #  passes, or `overrewrite` will write the CLI's value where the COBOL run
    #  wrote the row's. Arbitrate against the compiled oracle and record in
    #  docs/migration/ambiguity-resolutions.md.


class SystemRecordUnavailableError(RuntimeError):
    """The key-1 read failed, so the menu never reaches a dispatch.

    Raised by `aa010_get_system_recs`, and by nothing else. It reproduces the
    DISPOSITION of the four frozen menus' key-1 test, not a validation added
    here. Verbatim, from the General menu [general/general.cbl:L410-L418]::

         410      move     1 to File-Key-No.
         411      perform  System-Read-Indexed.        *> Read Cobol file params
         412      if       fs-reply not = zero          *> should NOT happen as done in
         413               perform System-close          *> open-system
         414               move    "sys002" to ws-called
         415               call    ws-called using ws-calling-data file-defs
         416               perform System-open
         417               go to aa010-Get-System-Recs
         418      end-if.

    ALL FOUR MENUS TEST THIS READ AND NONE OF THEM DISPATCHES UNTIL IT SUCCEEDS.
    [general/general.cbl:L412-L418], [sales/sales.cbl:L361-L367],
    [purchase/purchase.cbl:L355-L361] and [irs/irs.cbl:L513-L519] are the same
    four statements in the same order, differing only in the verb vocabulary. The
    transfer at L417 is a GO TO class 1 loop-back over an interactive recovery, so
    in the frozen system the paragraph cannot be LEFT while the reply is non-zero:
    either `sys002` creates the record and the loop succeeds, or the operator
    never gets a menu at all.

    WHY THE MIGRATION RAISES WHERE THE COBOL LOOPS. `common/sys002.cbl` is out of
    scope by name (Agent Action Plan section 0.2.2) and is an interactive
    record-creation dialog: it asks the operator for every parameter, and this
    process has no operator. With the recovery unreproducible the loop can never
    terminate successfully, so the only reachable frozen outcome is the one this
    exception carries - NO posting program is called and nothing is written. The
    frozen menu reaches the same end itself by a second route: when `sys002`
    reports a serious code, `call-system-setup.` answers `stop run`
    [general/general.cbl:L630-L631].

    ⛔ WHAT MUST NOT HAPPEN INSTEAD, and why this is not a new validation
    (rule R-3). Continuing past a failed key-1 read hands every callee a record at
    its DECLARED DEFAULTS - accounting cycle zero, period zero, current quarter
    zero, spaces in the control accounts and a posting-key allocator at zero - and
    a posting cycle driven from zeroes posts differently. Reproducing the frozen
    non-dispatch is therefore the faithful reading; fabricating a system row would
    be the added behaviour.

    NOTHING IS ROLLED BACK, deliberately. The failure arm performs the frozen
    close [general/general.cbl:L413] and then stops. The load only reads, so
    there is nothing to undo - and Agent Action Plan section 0.6.5 is explicit
    that partial state is committed rather than rolled back in this system.

    NO `return_code` ATTRIBUTE IS CARRIED, and that is a decision rather than an
    omission: the process boundary `acas_posting.__main__.run_entry_point` then
    reports `SERIOUS_ERROR_THRESHOLD + 1`, the smallest status the frozen menu
    treats as serious [general/general.cbl:L720], which is also the band
    [general/general.cbl:L630-L631] answers with `stop run`. Inventing a distinct
    numeric code would publish an observable the compiled program has not got.

    Attributes:
        fs_reply: `FS-Reply` [copybooks/wsfnctn.cob:L38] AS THE KEY-1 READ LEFT
            IT, captured before the failure arm's close could overwrite it. This
            is the decisive status the frozen `if` tests, preserved rather than
            lost.
        we_error: `We-Error` [copybooks/wsfnctn.cob:L23] from the same read. The
            two travel together because the handlers' own documentation ties them
            together.

    Note:
        The two attributes are named exactly as
        `acas_posting.dal.status.AcasFileHandlerError` names its own, because
        `run_entry_point` reads them reflectively when it builds its one sanitised
        record. They are small closed integer vocabularies and carry no row key,
        no account and no credential, so reporting them cannot disclose anything.

    Note:
        NOT a subclass of `acas_posting.dal.status.AcasFileHandlerError`, and the
        reason is behavioural. That exception's own docstring records that it
        "belongs to one calling convention and not the other, and a General Ledger
        caller that raised it would be adding behaviour" - it stands for the IRS
        convention's `Open-Error-Continued` tail
        [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L355-L364]. The key-1 test
        reproduced here is the MENU's own statement in all four shells, so it
        needs its own type. `acas_posting.dal.facade.FacadeGoback` is excluded for
        the same reason.
    """

    def __init__(self, fs_reply: int, we_error: int) -> None:
        """Record the reply pair the key-1 read left behind.

        Args:
            fs_reply: `FS-Reply` as the read left it, before any close.
            we_error: `We-Error` from the same read.
        """
        self.fs_reply = int(fs_reply)
        self.we_error = int(we_error)
        super().__init__(
            "the system parameter record could not be read under File-Key-No "
            f"{SYSTEM_FILE_KEY_PARAMS}: FS-Reply={self.fs_reply} "
            f"WE-Error={self.we_error}. No posting program is called, exactly as "
            "the frozen menus dispatch nothing until this read succeeds "
            "[general/general.cbl:L412-L418]; their recovery is the interactive "
            "sys002, which is out of scope (Agent Action Plan section 0.2.2). "
            "Seed SYSTEM-REC under key 1 before running the cycle."
        )


class _SystemVerbs(NamedTuple):
    """The three `acas000` verbs the menu load issues, in ONE vocabulary.

    Agent Action Plan section 0.3.3 gives the facade "One implementation, two
    published name sets", and section 0.6.5 states that the difference between
    them is behavioural rather than cosmetic: the handler-named open family
    carries a per-handler error check that ends in `goback`, and the entity-named
    one "has NO such paragraph at all - its callers test the reply inline". So the
    load cannot pick a set arbitrarily; it picks the one its own menu uses, and
    this triple is how that choice is expressed once rather than at three call
    sites.

    Attributes:
        open_input: the open. `System-Open-Input`
            [copybooks/Proc-ACAS-FH-Calls.cob:L197-L202] or `acas000-Open-Input`
            [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L98-L102].
        read_indexed: the read. `System-Read-Indexed`
            [copybooks/Proc-ACAS-FH-Calls.cob:L217-L220] or
            `acas000-Read-Indexed`
            [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L114-L117].
        close: the close. `System-Close`
            [copybooks/Proc-ACAS-FH-Calls.cob:L211-L215] or `acas000-Close`
            [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L104-L107].
        paragraphs: the three COBOL paragraph names, for the log record and for
            the traceability document. Data, never a decision.
        copybook: the copybook the three come from, for the same two reasons.
    """

    open_input: Callable[[facade.FacadeContext], facade.StatusPair]
    read_indexed: Callable[[facade.FacadeContext], facade.StatusPair]
    close: Callable[[facade.FacadeContext], facade.StatusPair]
    paragraphs: str
    copybook: str


#: The vocabulary the General, Sales and Purchase menus use. Each of the three
#: copies [copybooks/Proc-ACAS-FH-Calls.cob] and drives the System entity by its
#: ENTITY name - `perform System-Read-Indexed` [general/general.cbl:L411],
#: [sales/sales.cbl:L360], [purchase/purchase.cbl:L354]. None of the twelve verbs
#: in that copybook carries an error check, so a failing reply is left in
#: `File-Access` for the caller to test, which is exactly what those three menus
#: do inline at [general/general.cbl:L412].
_ENTITY_NAMED_SYSTEM_VERBS: Final[_SystemVerbs] = _SystemVerbs(
    facade.system_open_input,
    facade.system_read_indexed,
    facade.system_close,
    "System-Open-Input / System-Read-Indexed / System-Close",
    "copybooks/Proc-ACAS-FH-Calls.cob",
)

#: The vocabulary the IRS menu uses, and using it is not a naming preference.
#: irs/irs.cbl copies [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob] instead
#: [irs/irs.cbl:L1035] and drives the same handler by its HANDLER name -
#: `perform acas000-open-Input` [irs/irs.cbl:L499], `perform
#: acas000-Read-Indexed` [irs/irs.cbl:L512], `perform acas000-close`
#: [irs/irs.cbl:L514]. Three consequences follow, all reproduced by the facade
#: and none of them available from the entity-named set:
#:
#:   * the open family performs `acas000-Check-4-Errors`
#:     [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L320-L325], which on a non-zero
#:     reply closes the handler and transfers to `Open-Error-Continued`
#:     [:L355-L364], whose `goback` the facade raises as `FacadeGoback`. Because
#:     the copybook is textually included in irs/irs.cbl, that `goback` returns
#:     from THE MENU PROGRAM, which is why `acas_posting/cli/irs_post.py` absorbs
#:     it at its own boundary rather than treating it as a condition from
#:     `irs030`;
#:   * `acas000-Open-Input` performs the check BEFORE the dispatch rather than
#:     after [:L98-L102] - alone among all 42 verb paragraphs - so it tests
#:     whatever reply the PREVIOUS operation left and this open's own failure is
#:     never checked. The facade reproduces that as written;
#:   * the dispatch paragraph itself pins `File-Key-No` to 1
#:     [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L22-L29], where the entity-named
#:     one leaves the caller's key alone. Harmless here and impossible to trip
#:     through the published factories: `irs_menu_state` carries neither a totals
#:     record nor a defaults record, so keys 4 and 2 are never read on the one
#:     route that selects this set. Documented rather than guarded - a guard would
#:     be a validation the COBOL does not have (rule R-3).
_HANDLER_NAMED_SYSTEM_VERBS: Final[_SystemVerbs] = _SystemVerbs(
    facade.acas000_open_input,
    facade.acas000_read_indexed,
    facade.acas000_close,
    "acas000-Open-Input / acas000-Read-Indexed / acas000-Close",
    "copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob",
)


#  THE MENU SHELL'S OWN acas000 TRAFFIC
#  Four functions, each named after the paragraph it reproduces, because rule R-5
#  requires paragraph-to-function traceability and these are menu paragraphs:
#      aa010_get_system_recs        general/general.cbl  L398  (+ Open-System L385)
#                                   sales/sales.cbl      L351  (+ Open-System L338)
#                                   purchase/purchase.cbl L346 (+ Open-System L333)
#                                   irs/irs.cbl          L507  (+ aa005-Open-System L494)
#      overrewrite                  general/general.cbl  L656
#                                   sales/sales.cbl      L628
#                                   purchase/purchase.cbl L621
#                                   irs/irs.cbl          L755  (`EOJ.`, the IRS spelling)
#      zz090_set_up_irs_system_data irs/irs.cbl          L907
#      zz095_restore_irs_system_data irs/irs.cbl         L1000
#  All four are COMMANDS: they mutate the records and the `MenuState` they are
#  given and return either None or a value object. None of them returns a status,
#  because a COBOL paragraph cannot; the reply is in `MenuState.file_access`,
#  exactly as it is in the menus.


def general_menu_state() -> MenuState:
    """The General menu's own WORKING-STORAGE - keys 1, 2 AND 4.

    general/general.cbl is the only menu of the four that touches key 2: its load
    reads `Default-Record` [general/general.cbl:L405-L407] and its `overrewrite`
    rewrites it [general/general.cbl:L664-L666]. It also carries
    `WS-System-Record-4`, which it loads and rewrites even though none of the four
    General Ledger programs receives it - Shape 1 has four parameters and the
    totals record is not among them [general/gl070.cbl:L245-L248]. Loaded and
    written back unchanged, exactly as the menu does.

    A FACTORY RATHER THAN A CONSTRUCTOR CALL AT THE ROUTE, and for a structural
    reason: building the block needs `records.file_access`,
    `records.system_dflt`, `records.system_record_4` and
    `records.test_data_flags`, and every `cli/*` entry point states that it names
    no record module - the record dataclasses are this module's business. Keeping
    the construction here keeps that true.

    THE ENTITY-NAMED VOCABULARY, because general/general.cbl copies
    [copybooks/Proc-ACAS-FH-Calls.cob] and performs `System-Read-Indexed`
    [general/general.cbl:L411]. `handler_named_verbs` is therefore left at its
    False default - see `MenuState` and `_ENTITY_NAMED_SYSTEM_VERBS`.
    """
    return MenuState(
        FileAccess(), AcasDalCommonData(), SystemRecord4(), SysDefaultRecord()
    )


def slpl_menu_state() -> MenuState:
    """The Sales and Purchase menus' own WORKING-STORAGE - keys 1 and 4 only.

    Both menus load keys 4 and 1 [sales/sales.cbl:L355-L360],
    [purchase/purchase.cbl:L350-L354] and rewrite keys 1 and 4
    [sales/sales.cbl:L628-L641], [purchase/purchase.cbl:L621-L634]. NEITHER
    mentions key 2 anywhere, so no defaults record is carried and none is read or
    written. One factory serves both because their key sets are identical; their
    DISPATCH gates are not, and those live in the two routes.

    The totals record this returns is the one that matters most on these routes:
    it becomes `SlPlLinkage.system_record_4`, the third linkage argument
    [sales/sl060.cbl:L397] that the nine period-total writes mutate, and it is the
    same object `overrewrite` rewrites under key 4.

    THE ENTITY-NAMED VOCABULARY, as the General menu's: both shells copy
    [copybooks/Proc-ACAS-FH-Calls.cob] and perform `System-Read-Indexed`
    [sales/sales.cbl:L360], [purchase/purchase.cbl:L354]. `handler_named_verbs`
    stays False.
    """
    return MenuState(FileAccess(), AcasDalCommonData(), SystemRecord4())


def irs_menu_state() -> MenuState:
    """The IRS menu's own WORKING-STORAGE - key 1 alone.

    irs/irs.cbl reads key 1 and nothing else [irs/irs.cbl:L511-L512], and its
    `EOJ.` re-reads and rewrites key 1 and nothing else
    [irs/irs.cbl:L759-L774]. So neither a totals record nor a defaults record is
    carried, and `aa010_get_system_recs` reads neither.

    ⭐ AND THE HANDLER-NAMED VOCABULARY, WHICH IS THIS FACTORY'S SECOND JOB.
    irs/irs.cbl copies [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob]
    [irs/irs.cbl:L1035], not the entity-named copybook the other three menus copy,
    and drives the same handler through `acas000-open-Input`
    [irs/irs.cbl:L499], `acas000-Read-Indexed` [irs/irs.cbl:L512] and
    `acas000-close` [irs/irs.cbl:L514]. Agent Action Plan section 0.6.5 records
    why that is not a naming preference: the handler-named open family carries a
    per-handler error check that closes the file and returns from the program,
    while the entity-named convention "has NO such paragraph at all", so "the
    Python facade must therefore behave differently depending on which alias set
    the caller used, which is a behavioral difference and not merely a naming
    one". `handler_named_verbs=True` is what makes `aa010_get_system_recs` select
    it, and it is what lets a startup failure reach the `FacadeGoback` boundary
    `acas_posting/cli/irs_post.py` already holds open. The IRS menu's own
    persistence, `eoj_persist_irs_system_data`, names those verbs directly because
    it serves this one menu and no other.
    """
    return MenuState(FileAccess(), AcasDalCommonData(), handler_named_verbs=True)


def _force_rdbms_store(file_access: FileAccess) -> None:
    """`move "66" to FA-RDBMS-Flat-Statuses.` [general/general.cbl:L659].

    The selector is a GROUP of two `pic 9` items [copybooks/wsfnctn.cob:L72-L73],
    so the group value `"66"` is 6 in each digit. See
    `RDBMS_STORE_SELECTOR_DIGIT` for why the migrated reads use `"66"` where the
    menus force `"00"`.
    """
    statuses = file_access.fa_rdbms_flat_statuses
    statuses.fa_file_system_used = RDBMS_STORE_SELECTOR_DIGIT
    statuses.fa_file_duplicates_in_use = RDBMS_STORE_SELECTOR_DIGIT


def _system_verbs(state: MenuState) -> _SystemVerbs:
    """Return the three `acas000` verbs THIS menu performs.

    The choice is the menu program's own and is fixed for a whole session: three
    shells copy [copybooks/Proc-ACAS-FH-Calls.cob] and perform the entity-named
    `System-*` paragraphs, irs/irs.cbl copies
    [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob] [irs/irs.cbl:L1035] and performs the
    handler-named `acas000-*` ones. Reading it off `MenuState` rather than
    branching at each call site is what keeps `aa010_get_system_recs` ONE
    reproduction of ONE paragraph while still behaving as each shell behaves.

    Args:
        state: the menu's own WORKING-STORAGE, whose `handler_named_verbs` the
            factory that built it set.

    Returns:
        `_HANDLER_NAMED_SYSTEM_VERBS` for the IRS menu, otherwise
        `_ENTITY_NAMED_SYSTEM_VERBS`.
    """
    if state.handler_named_verbs:
        return _HANDLER_NAMED_SYSTEM_VERBS
    return _ENTITY_NAMED_SYSTEM_VERBS


def _select_key(file_access: FileAccess, key: int) -> None:
    """`move n to File-Key-No.` - the caller-owned key `acas000` dispatches on.

    `File-Key-No` lives inside the logging group of `File-Access`
    [copybooks/wsfnctn.cob:L44-L56], which is where the migrated record layer
    puts it too. Written through a named function so that the four call sites
    below read as the menus do and none of them reaches two levels into the
    record by hand.
    """
    file_access.logging_data.file_key_no = key


def _system_context(
    buffer: object, state: MenuState, file_defs: FileDefs
) -> facade.FacadeContext:
    """Build the five-operand linkage one `acas000` verb needs.

    `acas000.` [copybooks/Proc-ACAS-FH-Calls.cob:L20-L24] is the ONE facade
    dispatch paragraph with four operands rather than five, because the system
    record IS the entity buffer - there is no second record to pass. The facade's
    context still carries five slots, so `system` is the buffer and `record` is
    left as the same object: `_dispatch_acas000_entity` forwards `ctx.system` and
    never looks at `ctx.record`.

    Args:
        buffer: the record class matching the current `File-Key-No` - anomaly
            N9's ONE BUFFER [common/acas000.cbl:L311], which four bridges
            reinterpret in the compiled handler and which the migrated handler
            takes as an argument instead.
        state: the menu's own WORKING-STORAGE.
        file_defs: `01 File-Defs.`, the fourth operand.
    """
    return facade.FacadeContext(
        buffer,
        buffer,
        state.file_access,
        file_defs,
        state.dal_common,
    )


def aa010_get_system_recs(
    system_record: SystemRecord,
    state: MenuState,
    file_defs: FileDefs,
    ns: argparse.Namespace,
    pinned: clock.PinnedRunDate,
    *,
    env: Mapping[str, str] | None = None,
) -> None:
    """`Open-System.` then `aa010-Get-System-Recs.` - the menu's state load.

    Verbatim, from the General menu [general/general.cbl:L398-L412]::

         398  aa010-Get-System-Recs.
         399      move     zeros to File-System-Used
         400                        File-Duplicates-In-Use.
         401      move     "00" to  FA-RDBMS-Flat-Statuses.
         402      move     4 to File-Key-No.
         403      perform  System-Read-Indexed.        *> Read Cobol file sys totals
         404      move     System-Record to WS-System-Record-4.
         405      move     2 to File-Key-No.
         406      perform  System-Read-Indexed.        *> Read Cobol file defaults
         407      move     System-Record to Default-Record.
         408      move     1 to File-Key-No.
         409      perform  System-Read-Indexed.        *> Read Cobol file params
         412      if       fs-reply not = zero          *> should NOT happen as
         413               perform System-close          *>  done in open-system
         414               move    "sys002" to ws-called
         415               call    ws-called using ws-calling-data file-defs
         416               perform System-open
         417               go to aa010-Get-System-Recs
         418      end-if.
         460      perform  System-Close.

    THE KEY ORDER IS 4, THEN 2, THEN 1, AND IT IS NOT ARBITRARY. Key 1 is read
    LAST so that the record buffer is left holding the system parameters when the
    paragraph ends, which is the state every later paragraph assumes. The
    migration passes a distinct record per key and so does not depend on that,
    but the order is preserved anyway: rule R-4, and a reader diffing the two
    should find the same sequence of statements.

    KEY 2 IS THE GENERAL MENU'S ALONE. Sales reads keys 4 and 1
    [sales/sales.cbl:L355-L360] and Purchase reads keys 4 and 1
    [purchase/purchase.cbl:L350-L354]; neither mentions key 2. `state` decides:
    a key is read only when its record is present. Reproduced as the asymmetry it
    is, not normalised into a common three-key load.

    THE `move System-Record to ...` LINES HAVE NO COUNTERPART, and their absence
    is anomaly N9's flip side. They exist because `acas000` has one buffer that
    four bridges reinterpret; here each key is given its own record and the
    handler writes straight into it. See `MenuState`'s note.

    ⭐ THE KEY-1 REPLY IS TESTED, AND TESTED BEFORE THE CLOSE. All four menus
    write the same four statements after the key-1 read -
    [general/general.cbl:L412-L418], [sales/sales.cbl:L361-L367],
    [purchase/purchase.cbl:L355-L361], [irs/irs.cbl:L513-L519] - and none of them
    dispatches anything until that read succeeds. Two properties of the frozen
    shape are load-bearing and both are reproduced:

    * THE TEST PRECEDES THE CLOSE. `if fs-reply not = zero` is L412 and `perform
      System-close` is L413, in that order. A close issued first would leave its
      OWN reply in `File-Access` and the decisive one would be gone, so the read's
      pair is captured off the returned `StatusPair` the moment the read returns
      and the test is made on that.
    * ONLY KEY 1 IS TESTED. The key-4 and key-2 reads above are NOT tested by any
      menu, and no test is added to them (rule R-4). The asymmetry is the
      specification: key 1 carries the accounting cycle, the period, the control
      accounts and the allocator that every callee reads.

    A non-zero reply raises `SystemRecordUnavailableError` after the frozen close,
    which is where the frozen paragraph's own recovery - `sys002`, then a loop back
    to the top - cannot be followed, because `common/sys002.cbl` is an interactive
    record-creation dialog and out of scope by name (Agent Action Plan section
    0.2.2). See that exception for the full argument, including why continuing with
    a declared-default record would be the added behaviour rather than this.

    NOT REPRODUCED, and each for a stated reason:

    * `move zeros to File-System-Used File-Duplicates-In-Use` and `move "00" to
      FA-RDBMS-Flat-Statuses`. Both select the ISAM store, which the migration
      does not have - see `RDBMS_STORE_SELECTOR_DIGIT`. `"66"` is forced instead.
    * The `sys002` CALL and the loop-back inside the two recovery arms at
      [general/general.cbl:L391-L396] and [general/general.cbl:L414-L417] - but
      NOT the arms' own guard and not the close. The guard on the key-1 read IS
      reproduced, above; what has no counterpart is `call "sys002"` itself and the
      `go to aa010-Get-System-Recs` that only makes sense after it. The open arm's
      guard at [general/general.cbl:L391] is left untranslated because its whole
      body is that unreproducible recovery and because a failed open makes the
      key-1 read fail too, so the disposition is reached one statement later
      either way.
    * The commented-out RDB cross-load at [general/general.cbl:L419-L459], which
      the maintainer disabled with "BY PASS THIS CODE AS THE FILE WILL ALWAYS BE
      CURRENT."
    * `move run-date to u-bin. call "maps04". move u-date to to-day.`
      [general/general.cbl:L465-L467]. See the AMBIGUITY note below.

    AMBIGUITY Q-CLI-SYSREC-RUNDATE. The frozen menus derive `to-day` FROM THE
    LOADED ROW: `move run-date to u-bin` [general/general.cbl:L465],
    [sales/sales.cbl:L410], [purchase/purchase.cbl:L404], where `run-date` is
    SYSTEM-REC's own column. A census settles where that column comes from -
    general/general.cbl writes `function current-date` into `wse-date-block` and
    displays one field of it on screen [general/general.cbl:L371],
    [general/general.cbl:L519], and NEVER writes `run-date` at all; the only
    writer in the checkout is `move u-bin to run-date`
    [copybooks/Proc-ACAS-Mapser-RDB.cob:L80], which is copied by
    `common/sys002.cbl` alone, the out-of-scope program that CREATES the record.
    So in the frozen system the run date is written once at record-creation time
    and read thereafter. The migration replaces that creator with the controlled
    clock, which Agent Action Plan section 0.1.1 requires to pin BOTH observables
    "at the CLI boundary", and the review confirms the pinning as correct. This
    function therefore keeps `--run-date` authoritative and re-applies it after
    the load; a scenario must seed SYSTEM-REC.RUN-DATE to agree. Arbitrate
    against the compiled oracle and record in
    docs/migration/ambiguity-resolutions.md.

    ⭐ THE VERB VOCABULARY IS THE MENU'S, NOT THIS FUNCTION'S. Three of the four
    shells drive `acas000` by its ENTITY name and the IRS shell drives it by its
    HANDLER name, and Agent Action Plan section 0.6.5 records that the difference
    is behavioural: the handler-named open family performs
    `acas000-Check-4-Errors` and can end the menu program outright, while the
    entity-named convention "has NO such paragraph at all". `state` therefore
    decides here too - `MenuState.handler_named_verbs`, set by `irs_menu_state`
    alone - and the two sets are `_ENTITY_NAMED_SYSTEM_VERBS` and
    `_HANDLER_NAMED_SYSTEM_VERBS`, whose notes carry the three differences and
    their locators. One implementation, two vocabularies, exactly as the facade
    publishes them.

    Args:
        system_record: `SYSTEM-REC`, loaded by the key-1 read. Mutated in place,
            then re-pinned.
        state: the menu's own WORKING-STORAGE. `system_record_4` and
            `default_record` decide which of keys 4 and 2 are read, and
            `handler_named_verbs` decides which facade vocabulary the three verbs
            come from.
        file_defs: `01 File-Defs.`, the fourth operand of every dispatch.
        ns: the parsed namespace, for the re-application of the pins.
        pinned: the pinned pair from `resolve_clock`.
        env: the mapping the six connection parameters are resolved from.

    Raises:
        SystemRecordUnavailableError: the key-1 read left a non-zero `FS-Reply`.
            The frozen menus answer that by running the interactive `sys002` and
            looping until the read succeeds, so no dispatch follows a failure;
            with `sys002` out of scope the only reachable frozen outcome is that
            non-dispatch. Raised AFTER the frozen close
            [general/general.cbl:L413], carrying the reply pair the read left.
        acas_posting.dal.facade.FacadeGoback: on the IRS route only, and from the
            OPEN alone. `acas000-Open-Input` performs `acas000-Check-4-Errors`
            [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L98-L102], which on a
            non-zero reply reaches `Open-Error-Continued` and its `goback`
            [:L355-L364]; because the copybook is textually included in
            irs/irs.cbl, that `goback` returns from THE MENU PROGRAM, and
            `acas_posting/cli/irs_post.py` absorbs it at that boundary. NEVER
            raised for the General, Sales or Purchase menus: their entity-named
            `System-*` verbs carry no error check
            [copybooks/Proc-ACAS-FH-Calls.cob:L190-L230].
        rdbms_params.RdbmsParamError: from the re-application of the pins.
    """
    #       The menu's own vocabulary, chosen once for all three verbs below.
    verbs = _system_verbs(state)

    #  385  Open-System.  /  494  aa005-Open-System.
    #       `perform System-Open-Input` with key 1 - "as Input as I/o may create"
    #       [irs/irs.cbl:L499]. The key is set before the open because `acas000`
    #       dispatches the OPEN on it too.
    _force_rdbms_store(state.file_access)
    _select_key(state.file_access, SYSTEM_FILE_KEY_PARAMS)
    verbs.open_input(_system_context(system_record, state, file_defs))

    #  403  perform  System-Read-Indexed.        *> Read Cobol file sys totals
    #       NOT TESTED, in any menu. Only key 1 is [general/general.cbl:L412].
    if state.system_record_4 is not None:
        _select_key(state.file_access, SYSTEM_FILE_KEY_TOTALS)
        verbs.read_indexed(_system_context(state.system_record_4, state, file_defs))

    #  406  perform  System-Read-Indexed.        *> Read Cobol file defaults
    #       NOT TESTED either, and the General menu is the only one that reads it.
    if state.default_record is not None:
        _select_key(state.file_access, SYSTEM_FILE_KEY_DEFAULTS)
        verbs.read_indexed(_system_context(state.default_record, state, file_defs))

    #  409  perform  System-Read-Indexed.        *> Read Cobol file params
    #       LAST, as the frozen paragraph reads it. THE PAIR IS CAPTURED FROM THE
    #       RETURN VALUE, because the close below - either the failure arm's at
    #       L413 or the success path's at L460 - overwrites `File-Access` with its
    #       own reply, and the reply the frozen `if` tests is THIS one.
    _select_key(state.file_access, SYSTEM_FILE_KEY_PARAMS)
    key_1_status = verbs.read_indexed(
        _system_context(system_record, state, file_defs)
    )

    #  412  if       fs-reply not = zero          *> should NOT happen as done in
    #  413           perform System-close          *> open-system
    #  414           move    "sys002" to ws-called
    #  415           call    ws-called using ws-calling-data file-defs
    #  416           perform System-open
    #  417           go to aa010-Get-System-Recs
    #  418  end-if.
    #       ⭐ THE GATE. Present in all four shells and identical in all four
    #       [general/general.cbl:L412-L418], [sales/sales.cbl:L361-L367],
    #       [purchase/purchase.cbl:L355-L361], [irs/irs.cbl:L513-L519]. L413 IS
    #       reproduced; L414-L417 cannot be, because `common/sys002.cbl` is an
    #       interactive record-creation dialog and out of scope by name (Agent
    #       Action Plan section 0.2.2), and the loop-back at L417 is meaningful
    #       only after it. What survives is the frozen DISPOSITION: the paragraph
    #       is never left with a bad reply, so nothing is dispatched and nothing is
    #       written. See `SystemRecordUnavailableError`.
    if key_1_status.fs_reply != FsReply.SUCCESS:
        #  A diagnostic, at ERROR because the run stops here. The frozen paragraph
        #  displays nothing at this point - `sys002` puts up its own screens - so
        #  this record replaces a program the migration does not call rather than a
        #  display it dropped, and it names the two locators a reader needs.
        _LOG.error(
            "the system parameter record could not be read: File-Key-No %d, "
            "FS-Reply %d, WE-Error %d, through %s [%s]. The frozen menus recover "
            "by calling the interactive sys002 and re-reading "
            "[general/general.cbl:L412-L418]; sys002 is out of scope (Agent "
            "Action Plan section 0.2.2), so no posting program is called. Seed "
            "SYSTEM-REC under key %d.",
            SYSTEM_FILE_KEY_PARAMS,
            key_1_status.fs_reply,
            key_1_status.we_error,
            verbs.paragraphs,
            verbs.copybook,
            SYSTEM_FILE_KEY_PARAMS,
        )
        #  413  perform System-close.
        verbs.close(_system_context(system_record, state, file_defs))
        raise SystemRecordUnavailableError(
            key_1_status.fs_reply, key_1_status.we_error
        )

    #  460  perform  System-Close.
    verbs.close(_system_context(system_record, state, file_defs))

    #  The pins, re-applied over the loaded row. See Q-CLI-SYSREC-PINS in
    #  `_bind_system_record` and the field-by-field reasons in `_apply_cli_pins`.
    _apply_cli_pins(system_record, ns, pinned, env=env)


def overrewrite(
    system_record: SystemRecord, state: MenuState, file_defs: FileDefs
) -> None:
    """`overrewrite.` - the menu's persistence, RDB arm only.

    Verbatim, from the General menu [general/general.cbl:L656-L672]::

         656  overrewrite.                          *> save to RDB or file.
         657      if       File-System-Used NOT = zero   *> Force RDB processing
         658               move     "66" to FA-RDBMS-Flat-Statuses
         659               move     1 to File-Key-No
         660               perform  System-Open
         661               move     1 to File-Key-No
         662               move     System-Record to WS-Temp-System-Rec
         663               perform  System-Rewrite
         664               move     2 to File-Key-No
         665               move     Default-Record to System-Record
         666               perform  System-Rewrite
         667               move     4 to File-Key-No
         668               move     WS-System-Record-4 to System-Record
         669               perform  System-Rewrite
         670               perform  System-Close
         671               move     WS-Temp-System-Rec to System-Record
         672      end-if.

    THE KEY ORDER IS 1, THEN 2, THEN 4 - the reverse of the load's. Preserved as
    written; the two paragraphs disagree and are not reconciled.

    ONLY THE RDB ARM IS REPRODUCED. What follows `end-if` in all three menus is
    the same three rewrites against the ISAM parameter file
    [general/general.cbl:L674-L691], and the migration has no ISAM store - see
    `RDBMS_STORE_SELECTOR_DIGIT`. One consequence is worth naming: because the
    Cobol arm is unconditional and the RDB arm is not, a frozen run with
    `File-System-Used` at zero persists to the file and NOT to the table, whereas
    this function always persists to the table. That is not a choice made here -
    it is what having a single store means.

    THE `File-System-Used NOT = zero` GATE IS NOT REPRODUCED AS A GATE, and the
    reason is measured rather than assumed. `File-System-Used` is a SYSTEM-REC
    column [copybooks/wssystem.cob], so the key-1 read in the load overwrites it
    with the row's value; the menus zero it beforehand
    [general/general.cbl:L399] and never set it again, the block that would have
    at [general/general.cbl:L428-L432] being commented out. Its value at this
    point is therefore whatever the seed stored. Testing it here would make the
    migration's ONLY persistence path conditional on a column that selects
    between two stores where only one exists, so the gate is dropped and the
    rewrites are unconditional. Recorded, not hidden.

    THE TWO `WS-Temp-System-Rec` MOVES have no counterpart - see `MenuState`'s
    note. Nothing is saved because nothing is overwritten.

    Args:
        system_record: `SYSTEM-REC`, rewritten under key 1.
        state: the menu's own WORKING-STORAGE. `default_record` is rewritten under
            key 2 and `system_record_4` under key 4, each only when present, so
            the General menu's three-key set and the Sales and Purchase two-key
            set both come out of one implementation.
        file_defs: `01 File-Defs.`, the fourth operand of every dispatch.
    """
    #  658-660  move "66" ... move 1 to File-Key-No ... perform System-Open.
    #           An I-O open, not input: `System-Open` sets Access-Type 2
    #           [copybooks/Proc-ACAS-FH-Calls.cob:L190-L195].
    _force_rdbms_store(state.file_access)
    _select_key(state.file_access, SYSTEM_FILE_KEY_PARAMS)
    facade.system_open(_system_context(system_record, state, file_defs))

    #  661-663  move 1 to File-Key-No ... perform System-Rewrite.
    #           The key is set a SECOND time, redundantly, immediately after the
    #           open set it. Transcribed rather than tidied away (rule R-4).
    _select_key(state.file_access, SYSTEM_FILE_KEY_PARAMS)
    facade.system_rewrite(_system_context(system_record, state, file_defs))

    #  664-666  move 2 to File-Key-No ... perform System-Rewrite.
    if state.default_record is not None:
        _select_key(state.file_access, SYSTEM_FILE_KEY_DEFAULTS)
        facade.system_rewrite(
            _system_context(state.default_record, state, file_defs)
        )

    #  667-669  move 4 to File-Key-No ... perform System-Rewrite.
    if state.system_record_4 is not None:
        _select_key(state.file_access, SYSTEM_FILE_KEY_TOTALS)
        facade.system_rewrite(
            _system_context(state.system_record_4, state, file_defs)
        )

    #  670  perform  System-Close.
    #       THE KEY IS STILL 4 HERE, and that is the frozen program's, not a slip.
    #       Nothing between L667 and L670 resets `File-Key-No`, so the close is
    #       issued against key 4 - the totals table - and never against key 1.
    #       `acas000` dispatches its CLOSE on the key like every other function
    #       [common/acas000.cbl:L574-L600], so the two are not interchangeable.
    #       The load's close does NOT have this shape: `aa010-Get-System-Recs`
    #       leaves the key at 1 [general/general.cbl:L408] and its close at
    #       [general/general.cbl:L460] therefore closes key 1. The asymmetry is
    #       transcribed, not reconciled (rule R-4). Recorded as FINDING F-A1 in
    #       the footer.
    facade.system_close(_system_context(system_record, state, file_defs))


#  THE IRS RECEIVING FIELDS, from the generated dictionary and never by eye.
#  Same accessor and same key form `records/irs_system.py` uses for its own 28
#  descriptors - `<COPYBOOK-RECORD>.<FIELD-NAME>` with the record half in the
#  copybook's own lower case. Only the THREE fields whose widths differ from
#  their ACAS sources, or which change category on the way in, are needed here;
#  the rest of `zz090`'s moves are same-width same-category and need no
#  descriptor. Naming them is what makes the two TRUNCATIONS visible rather than
#  accidental - see `zz090_set_up_irs_system_data`.
_IRS_SUSER: Final = FieldDescriptor.from_dictionary_key("system-record.suser")
#  The key carries the copybook's OWN capitalisation - `03  Print-Spool-Name`
#  [copybooks/irswssystem.cob:L44] - because dictionary lookup folds no case. Its
#  two neighbours here are lower case in the same copybook, `03  suser`
#  [copybooks/irswssystem.cob:L15] and `03  system-ops`
#  [copybooks/irswssystem.cob:L23], and the inconsistency is the source's.
_IRS_PRINT_SPOOL_NAME: Final = FieldDescriptor.from_dictionary_key(
    "system-record.Print-Spool-Name"
)
_IRS_SYSTEM_OPS: Final = FieldDescriptor.from_dictionary_key(
    "system-record.system-ops"
)


def zz090_set_up_irs_system_data(
    irs_system_params: IrsSystemParams, ws_system_record: SystemRecord
) -> IrsSystemSnapshot:
    """`zz090-Set-Up-IRS-System-Data Section.` [irs/irs.cbl:L907-L997].

    Remaps the loaded ACAS system record into the old IRS system-file layout,
    which is the record every IRS module is passed. The maintainer states the
    precondition himself [irs/irs.cbl:L924-L926]: "At point of running this
    section the ACAS system parameter file must have been read into the (ACAS)
    System-Record", so this runs AFTER `aa010_get_system_recs` and never before -
    which is also where the frozen menu performs it, at [irs/irs.cbl:L556],
    immediately after `aa010-Get-System-Recs` and before `Main-Loop`.

    THE FIELD NAMES DIFFER ON THE TWO SIDES BECAUSE OF A `COPY ... REPLACING`.
    irs/irs.cbl renames 26 items of `wssystem.cob` as it copies it
    [irs/irs.cbl:L361-L389] - `Run-Date` becomes `ACAS-Run-Date`, `suser` becomes
    `ACAS-suser`, `Client` becomes `IRS-Client` - purely to stop them colliding
    with the identically named items of the IRS layout. The Python records carry
    the copybooks' own names, so a reader matching this function against the
    COBOL should read `ACAS-x` as `ws_system_record.…x` and the bare name as
    `irs_system_params.x`.

    TWO MOVES TRUNCATE, and both are real:

    * `move ACAS-Suser to Suser` - `Usera pic x(32)`
      [copybooks/wssystem.cob:L71] into `suser pic x(24)`
      [copybooks/irswssystem.cob:L15]. Eight characters are lost off the right.
    * `move ACAS-Print-Spool-Name to Print-Spool-Name` - `pic x(48)`
      [copybooks/wssystem.cob:L79] into `pic x(32)`
      [copybooks/irswssystem.cob:L44]. Sixteen characters lost.

    Both go through the MOVE layer with the RECEIVING field's own descriptor, so
    the truncation is the COBOL rule's rather than Python's slicing, and a
    shorter source is space-filled on the right exactly as COBOL fills it.

    `move ACAS-Suser to Suser` IS A GROUP-TO-ELEMENTARY MOVE. `Suser` on the ACAS
    side is a group with one subordinate item [copybooks/wssystem.cob:L70-L71],
    so the group's bytes are that item's bytes and the move is the alphanumeric
    one written here. Recorded because the two sides' `suser` are not the same
    kind of item, only the same name.

    `move ACAS-Op-System to System-Ops` CHANGES CATEGORY: `pic 9`
    [copybooks/wssystem.cob:L99] into `pic x` [copybooks/irswssystem.cob:L23].
    One digit into one character, which COBOL performs as the digit's character.

    THE THREE DATES SHARE ONE `maps03-ws`, AND THAT SHARING IS LOAD-BEARING.
    `zz090-Proc-Run-Date`, `-Start-Date` and `-End-Date`
    [irs/irs.cbl:L972-L991] each move a binary column into `u-bin` and `perform
    maps04`, which in irs/irs.cbl is nothing but `call "maps04" using maps03-ws`
    [irs/irs.cbl:L897-L903]. `maps03-ws` is WORKING-STORAGE and persists between
    the three, and `maps04` UNPACKS only when the binary is greater than zero -
    otherwise it takes the validate-and-pack branch over whatever text `u-date`
    already holds, and on rejection leaves `u-date` untouched
    [common/maps04.cbl:L146]. So a zero `Start-Date` yields not a blank but the
    PREVIOUS conversion's text. One `Maps03Ws` is therefore created here and
    reused for all three, in the frozen order, so that carry-over is reproduced
    rather than removed.

    NOT REPRODUCED: `initialise IRS-System-Params with filler`
    [irs/irs.cbl:L933] has no counterpart because the caller passes a freshly
    declared record whose every field already holds the layout's declared
    default, which is what that statement establishes.

    Args:
        irs_system_params: `IRS-System-Params`, mutated in place. Every field
            this section writes is written; nothing else is touched.
        ws_system_record: the ACAS record, ALREADY LOADED. Read only.

    Returns:
        The seven-value snapshot `zz095` compares against - the Python
        counterpart of the seven `WS-` items [irs/irs.cbl:L353-L359], which the
        frozen section fills by naming them as second receivers on the same
        `move` [irs/irs.cbl:L953-L966].
    """
    data = ws_system_record.system_data_block
    irs_block = ws_system_record.irs_entry_block

    #  935  move     ACAS-Pass-Word to Pass-Word.
    irs_system_params.pass_word = data.pass_word
    #  936  move     ACAS-Suser     to Suser.        <- TRUNCATES 32 -> 24
    irs_system_params.suser = cobol_move.move_alphanumeric(
        data.suser.usera, _IRS_SUSER
    )
    #  937-940  move ACAS-Address-1 .. -4 to Address-1 .. -4.
    irs_system_params.address_1 = data.address_1
    irs_system_params.address_2 = data.address_2
    irs_system_params.address_3 = data.address_3
    irs_system_params.address_4 = data.address_4
    #  941  move     Vat-Rate-1     to Vat in IRS-System-Params.
    #  942  move     Vat-Rate-2     to Vat2.
    #  943  move     Vat-Rate-3     to Vat3.
    #       Same picture on both sides, `pic 99v99`
    #       [copybooks/wssystem.cob:L56], [copybooks/irswssystem.cob:L27-L29].
    irs_system_params.vat_rates.vat = data.vat_rates.vat_rate_1
    irs_system_params.vat_rates.vat2 = data.vat_rates.vat_rate_2
    irs_system_params.vat_rates.vat3 = data.vat_rates.vat_rate_3
    #  944  move     ACAS-Print-Spool-Name to Print-Spool-Name.  <- TRUNCATES 48 -> 32
    irs_system_params.print_spool_name = cobol_move.move_alphanumeric(
        data.print_spool_name, _IRS_PRINT_SPOOL_NAME
    )
    #  946  move     ACAS-Op-System to System-Ops.   <- pic 9 into pic x
    irs_system_params.system_ops = cobol_move.move_alphanumeric(
        data.op_system, _IRS_SYSTEM_OPS
    )

    #  951  move     IRS-Client            to Client.
    irs_system_params.client = irs_block.client
    #  952-966  The seven fields with a SECOND receiver each: the `WS-` snapshot.
    irs_system_params.next_post = irs_block.next_post
    irs_system_params.pass_value = irs_block.irs_pass_value
    irs_system_params.save_sequ = irs_block.save_sequ
    irs_system_params.system_work_group = irs_block.system_work_group
    irs_system_params.pl_app_created = irs_block.pl_app_created
    #       `PL-Approp-AC` is the FIVE-digit item inside the redefinition of the
    #       six-digit `PL-Approp-AC6` [copybooks/wssystem.cob:L322-L325] - "loose
    #       leading char for IRS". The IRS side is `pic 9(5)`
    #       [copybooks/irswssystem.cob:L43], so the five-digit reading is the one
    #       that matches and the six-digit one is deliberately not used.
    irs_system_params.pl_approp_ac = irs_block.filler_323.pl_approp_ac
    irs_system_params.first_time_flag = irs_block.first_time_flag

    #  972-991  zz090-Proc-Run-Date / -Start-Date / -End-Date, ONE `maps03-ws`.
    conversion = Maps03Ws()
    conversion.u_bin = data.run_date
    dates.maps04(conversion)
    irs_system_params.run_date = irs_run_date_x8(conversion.u_date)

    #       `zz090-Proc-Start-Date` and `-End-Date` [irs/irs.cbl:L980-L991] are
    #       the SAME two-slice `string` as `-Proc-Run-Date`, character for
    #       character, into two receivers of the same `pic x(8)`
    #       [copybooks/irswssystem.cob:L21-L22]. `irs_run_date_x8` is therefore
    #       the counterpart of all three statements, not of the first alone, and
    #       is reused rather than copied - its result is already eight characters
    #       wide, so no further MOVE is needed to fit the receiver.
    conversion.u_bin = data.start_date
    dates.maps04(conversion)
    irs_system_params.start_date = irs_run_date_x8(conversion.u_date)

    conversion.u_bin = data.end_date
    dates.maps04(conversion)
    irs_system_params.end_date = irs_run_date_x8(conversion.u_date)

    return IrsSystemSnapshot(
        next_post=irs_system_params.next_post,
        pass_value=irs_system_params.pass_value,
        save_sequ=irs_system_params.save_sequ,
        first_time_flag=irs_system_params.first_time_flag,
        system_work_group=irs_system_params.system_work_group,
        pl_app_created=irs_system_params.pl_app_created,
        pl_approp_ac=irs_system_params.pl_approp_ac,
    )


def zz095_restore_irs_system_data(
    snapshot: IrsSystemSnapshot,
    irs_system_params: IrsSystemParams,
    ws_system_record: SystemRecord,
) -> None:
    """`zz095-Restore-IRS-System-Data Section.` [irs/irs.cbl:L1000-L1032].

    Writes an IRS value back into the ACAS record ONLY where the IRS side has
    changed since `zz090` took the snapshot. Verbatim, the first of seven
    [irs/irs.cbl:L1011-L1012]::

        1011      if       WS-Next-Post         not = Next-Post
        1012               move     Next-Post  to IRS-Next-Post.  *> via irs030

    THE `if` IS THE BEHAVIOUR, NOT AN OPTIMISATION. Seven guarded moves and no
    `else` anywhere: a field the IRS side never touched keeps whatever the freshly
    re-read ACAS row holds for it, which on the frozen EOJ path is a value read
    only moments earlier. Written as seven separate `if`s here for the same
    reason - collapsing them into unconditional assignments would give the same
    answer today and a different one the moment the re-read row disagrees with
    the snapshot.

    SIX OF THE SEVEN ARE IN THE SNAPSHOT'S ORDER; ONE IS NOT. The frozen section
    tests `WS-First-Time-Flag` FIFTH [irs/irs.cbl:L1023], before `PL-Approp-AC`
    and `PL-App-Created`, whereas `zz090` fills it LAST
    [irs/irs.cbl:L965-L966]. The two orders disagree and both are preserved: this
    function follows `zz095`'s.

    `next_post` IS THE ONE THAT MATTERS TO THE POSTING CYCLE. `irs030` advances
    it once per posting written [irs/irs030.cbl:L1670-L1671], and the
    maintainer's own comment on this very line says "via irs030". Without this
    section that increment would never reach SYSTEM-REC, and the key allocator
    would restart at the same value on the next run.

    Args:
        snapshot: what `zz090` captured before the dispatch.
        irs_system_params: the IRS record as the dispatch left it. Read only.
        ws_system_record: the ACAS record to write back into, mutated in place.
            On the frozen EOJ path this is a FRESHLY RE-READ row, not the one
            `zz090` read - see `EOJ.` [irs/irs.cbl:L759-L764].
    """
    irs_block = ws_system_record.irs_entry_block

    #  1011  if  WS-Next-Post not = Next-Post / move Next-Post to IRS-Next-Post.
    if snapshot.next_post != irs_system_params.next_post:
        irs_block.next_post = irs_system_params.next_post
    #  1014  if  WS-Pass-Value not = Pass-Value
    if snapshot.pass_value != irs_system_params.pass_value:
        irs_block.irs_pass_value = irs_system_params.pass_value
    #  1017  if  WS-Save-Sequ not = Save-Sequ
    if snapshot.save_sequ != irs_system_params.save_sequ:
        irs_block.save_sequ = irs_system_params.save_sequ
    #  1020  if  WS-System-Work-Group not = System-Work-Group
    if snapshot.system_work_group != irs_system_params.system_work_group:
        irs_block.system_work_group = irs_system_params.system_work_group
    #  1023  if  WS-First-Time-Flag not = First-Time-Flag   <- FIFTH here
    if snapshot.first_time_flag != irs_system_params.first_time_flag:
        irs_block.first_time_flag = irs_system_params.first_time_flag
    #  1026  if  WS-PL-Approp-AC not = PL-Approp-AC
    if snapshot.pl_approp_ac != irs_system_params.pl_approp_ac:
        irs_block.filler_323.pl_approp_ac = irs_system_params.pl_approp_ac
    #  1029  if  WS-PL-App-Created not = PL-App-Created
    if snapshot.pl_app_created != irs_system_params.pl_app_created:
        irs_block.pl_app_created = irs_system_params.pl_app_created


def eoj_persist_irs_system_data(
    snapshot: IrsSystemSnapshot,
    irs_system_params: IrsSystemParams,
    ws_system_record: SystemRecord,
    state: MenuState,
    file_defs: FileDefs,
) -> None:
    """`EOJ.` [irs/irs.cbl:L755-L775] - the IRS menu's persistence.

    The IRS spelling of `overrewrite`, and structurally different from the other
    three menus' in two ways that both matter. Verbatim
    [irs/irs.cbl:L759-L775]::

         759      move     1 to File-Key-No.
         760      perform  acas000-Open.
         761      perform  acas000-Read-Indexed.        *> Read Cobol file
         762      perform  acas000-Close.
         763 *>
         764      perform  zz095-Restore-IRS-System-Data.
         765      move     1 to File-Key-No.             *> now default to file processing
         766      move     "00" to FA-RDBMS-Flat-Statuses.    *> Now do file
         767      perform  acas000-Open.
         768      perform  acas000-Rewrite.         *> In case of any changes
         769      perform  acas000-Close.
         770      if       File-System-Used NOT = zero   *> Force RDB processing
         771               move     "66" to FA-RDBMS-Flat-Statuses
         772               perform  acas000-Open
         773               perform  acas000-Rewrite         *> In case of any changes
         774               perform  acas000-Close
         775      end-if

    DIFFERENCE 1 - IT RE-READS THE ROW FIRST. Keys 2 and 4 are never involved,
    and key 1 is read AGAIN before anything is written, so what gets rewritten is
    the CURRENT row with only the IRS deltas laid over it by `zz095`. That is
    what makes the guarded moves of `zz095` meaningful: a field the IRS side
    never changed keeps the freshly read row's value rather than the value this
    process loaded at start-up. The other three menus rewrite the record they
    have been holding all along.

    DIFFERENCE 2 - IT USES THE HANDLER-NAMED VERBS. `acas000-Open` and its
    siblings come from [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob], not from
    [copybooks/Proc-ACAS-FH-Calls.cob], so two things follow: the key is PINNED to
    1 by the dispatch paragraph itself, which is why the `move 1 to File-Key-No`
    above is redundant; and every OPEN carries `acas000-Check-4-Errors`, which
    ends in the copybook's `goback`. That `goback` is this menu's own
    termination and is absorbed at the route boundary - see
    `acas_posting/cli/irs_post.py`.

    ONE OPEN/REWRITE/CLOSE, NOT TWO. The frozen paragraph does it once for the
    ISAM file and once more for the RDB, gated on `File-System-Used`. The
    migration has one store, so there is one pass - see
    `RDBMS_STORE_SELECTOR_DIGIT` and the same note in `overrewrite`.

    NOT REPRODUCED: the backup-script arm at [irs/irs.cbl:L777-L791], which ends
    in `call "SYSTEM" using Full-Backup-Script`. Agent Action Plan section 0.2.2
    excludes the `call "SYSTEM"` spool-out path wherever it appears.

    Args:
        snapshot: what `zz090_set_up_irs_system_data` captured before the
            dispatch.
        irs_system_params: the IRS record as the dispatch left it - carrying, in
            particular, the `next-post` allocator `irs030` advanced
            [irs/irs030.cbl:L1670-L1671].
        ws_system_record: the ACAS record. OVERWRITTEN by the re-read below, then
            written back.
        state: the menu's own WORKING-STORAGE.
        file_defs: `01 File-Defs.`, the fourth operand of every dispatch.

    Raises:
        acas_posting.dal.facade.FacadeGoback: from either OPEN, whose facade
            paragraph performs `acas000-Check-4-Errors`
            [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L92-L96]. Propagated, not
            caught: it is the menu program's termination and belongs at the menu
            program's boundary.
    """
    context = _system_context(ws_system_record, state, file_defs)

    #  759-762  the re-read. `move 1 to File-Key-No` is written for form; the
    #           handler-named dispatch pins the key itself.
    _force_rdbms_store(state.file_access)
    _select_key(state.file_access, SYSTEM_FILE_KEY_PARAMS)
    facade.acas000_open(context)
    facade.acas000_read_indexed(context)
    facade.acas000_close(context)

    #  764  perform  zz095-Restore-IRS-System-Data.
    zz095_restore_irs_system_data(snapshot, irs_system_params, ws_system_record)

    #  767-769 / 772-774  the write-back, once.
    facade.acas000_open(context)
    facade.acas000_rewrite(context)
    facade.acas000_close(context)


def bind_calling_data(
    ns: argparse.Namespace, *, called: str, caller: str
) -> WsCallingData:
    """Bind argv to `01 WS-Calling-Data` [copybooks/wscall.cob:L6-L14].

    Reproduces, in order, the state a menu shell establishes immediately before a
    dispatch. The returned record is MUTABLE by design: the callee writes `WS-Term-Code`
    back into it [general/gl070.cbl:L289] and the entry point reads it afterwards
    [general/general.cbl:L720-L721].

    Args:
        ns: the parsed namespace. All five calling-data attributes are read tolerantly,
            each falling back to the COBOL default that `add_calling_data_arguments`
            would have supplied.
        called: the callee's program-id, for `WS-Called`. Set per dispatch, as `move
            "gl070" to ws-called` [general/general.cbl:L808].
        caller: the dispatching menu's identity, used for `WS-Caller` only when the
            namespace carries no `--ws-caller`. An explicitly supplied option always
            wins.

    Returns:
        The bound record, with `WS-Term-Code` at zero ready for the dispatch.
    """
    calling_data = _declared_calling_data()

    set_called(calling_data, called)

    # [general/general.cbl:L512] `move "general" to ws-caller`.
    supplied_caller = getattr(ns, "ws_caller", None)
    calling_data.ws_caller = cobol_move.move(
        caller if supplied_caller is None else supplied_caller,
        calling_data_record.descriptor_for("ws_caller"),
    )

    calling_data.ws_del_link = cobol_move.move(
        getattr(ns, "ws_del_link", WS_DEL_LINK_DEFAULT),
        calling_data_record.descriptor_for("ws_del_link"),
    )

    calling_data.ws_process_func = cobol_move.move(
        getattr(ns, "ws_process_func", WS_PROCESS_FUNC_DEFAULT),
        calling_data_record.descriptor_for("ws_process_func"),
    )
    calling_data.ws_sub_function = cobol_move.move(
        getattr(ns, "ws_sub_function", WS_SUB_FUNCTION_DEFAULT),
        calling_data_record.descriptor_for("ws_sub_function"),
    )

    # ANOMALY, REPRODUCED (rule R-4).
    calling_data.ws_cd_args = cobol_move.move(
        getattr(ns, "ws_cd_args", WS_CD_ARGS_DEFAULT),
        calling_data_record.descriptor_for("ws_cd_args"),
    )

    reset_term_code(calling_data)

    return calling_data


def bind_gl_linkage(
    ns: argparse.Namespace,
    *,
    called: str,
    menu_state: MenuState | None = None,
    env: Mapping[str, str] | None = None,
    system_record: SystemRecord | None = None,
) -> GlLinkage:
    """Bind Shape 1 - the four-parameter General Ledger shape.

    Args:
        ns: the parsed namespace of a route that composed
            `add_calling_data_arguments` and `add_gl_linkage_arguments`.
        called: the callee's program-id - `"gl070"`, `"gl071"`, `"gl072"` or
            `"gl080"`, the literals general/general.cbl moves into `WS-Called`
            at L808, L812, L814 and L820.
        menu_state: the menu shell's own WORKING-STORAGE. When supplied, the
            system records are LOADED from the store first, by
            `aa010_get_system_recs`, exactly as the frozen menu loads them before
            its `CALL`; when omitted, they are built at their declared defaults
            and nothing is read. Every one of the seven routes supplies one, so
            the default serves only a caller that has no database - and such a
            caller gets the pre-load behaviour rather than a failure.
        env: the mapping the six connection parameters are resolved from, passed
            through to `_bind_system_record`. The process environment when
            omitted, which is the case in a real run; a caller that wants to
            drive a specific endpoint supplies one explicitly.
        system_record: the `SYSTEM-REC` the caller loaded through
            `aa010_get_system_recs`, reproducing `aa010-Get-System-Recs.`
            [general/general.cbl:L385-L460]. Mutated in place and carried into the
            linkage, exactly as the shell hands its own one record to the `CALL`.
            `None` builds one at its declared defaults - see `_bind_system_record`
            and finding CLI-02.

    Returns:
        The four arguments in COBOL parameter order [general/gl070.cbl:L245-L248], ready
            to splat into the program's `run`.

    Raises:
        AttributeError: the namespace carries no `run_date`, meaning the route
            failed to add the required option. Deliberately not caught and
            deliberately not defaulted: a missing run date must be an error,
            because the alternative is an ambient one (rule R-6).
        rdbms_params.RdbmsParamError: the deployment contract is absent - not one
            of the six variables is set. See `_bind_system_record`.
        SystemRecordUnavailableError: the key-1 read failed inside
            `aa010_get_system_recs`, so this binder returns nothing and no phase
            is dispatched - which is what the frozen menu does
            [general/general.cbl:L412-L418]. Only when a `menu_state` was
            supplied, since only then is anything read.

    Note:
        The returned `system_record` carries the connection parameters the
        deployment contract supplied. Should that contract supply the frozen
        copybook placeholders, `dal/connection.py` reports the exposure and
        connects anyway, because the compiled program applies no such check - see
        `_bind_system_record`.
    """
    pinned = resolve_clock(ns.run_date)
    file_defs = FileDefs()

    #  THE CALLER'S OWN RECORD, CARRIED THROUGH BY REFERENCE. `_bind_system_record`
    #  mutates and returns the instance it is handed and builds one only when
    #  handed None, so a caller that has already loaded or seeded `SYSTEM-REC` gets
    #  that object in the linkage - which is what a COBOL menu's single
    #  `01 SYSTEM-REC` is. See `_bind_system_record`.
    system_record = _bind_system_record(
        ns, pinned, env=env, system_record=system_record
    )

    #  [general/general.cbl:L385-L419] `Open-System.` then
    #  `aa010-Get-System-Recs.` - the menu loads its state BEFORE it fills
    #  `WS-Calling-Data` at L512, so the load happens here, before
    #  `bind_calling_data` below.
    if menu_state is not None:
        aa010_get_system_recs(
            system_record, menu_state, file_defs, ns, pinned, env=env
        )

    return GlLinkage(
        calling_data=bind_calling_data(
            ns, called=called, caller=_menu_caller_for(called)
        ),
        system_record=system_record,
        to_day=pinned.to_day,
        file_defs=file_defs,
    )


def bind_slpl_linkage(
    ns: argparse.Namespace,
    *,
    called: str,
    menu_state: MenuState | None = None,
    env: Mapping[str, str] | None = None,
    system_record: SystemRecord | None = None,
    system_record_4: SystemRecord4 | None = None,
) -> SlPlLinkage:
    """Bind Shape 2 - the five-parameter Sales and Purchase shape.

    Args:
        ns: the parsed namespace of a route that composed `add_calling_data_arguments`
            and `add_slpl_linkage_arguments`.
        called: the callee's program-id - `"sl055"`, `"sl060"`, `"sl100"`, `"pl055"`,
            `"pl060"` or `"pl100"`.
        env: as `bind_gl_linkage`.
        system_record: as `bind_gl_linkage`. The Sales and Purchase shells read it
            under file-key 1 [sales/sales.cbl:L359-L360],
            [purchase/purchase.cbl:L353-L354].
        system_record_4: the `SYSTOT-REC` the caller loaded through
            `aa010_get_system_recs`, which both shells read under file-key 4
            immediately before it - `move 4 to File-Key-No. perform
            System-Read-Indexed. move System-Record to WS-System-Record-4.`
            [sales/sales.cbl:L355-L357], [purchase/purchase.cbl:L350-L352].
            Carried into the linkage as the SAME object, because the nine
            period-total writes mutate it by reference. `None` falls back to
            `menu_state.system_record_4` - the menu's own record, which is what
            every route relies on - and then, when there is no menu state either,
            to a declared default.

    Returns:
        The five arguments in COBOL parameter order
        [sales/sl060.cbl:L395-L399]. `SYSTOT-REC` carries no connection field of
        its own [copybooks/wssys4.cob], so nothing is bound into it here - it is
        carried exactly as it was read, and the nine period-total accumulations of
        section 0.6.4 land in it during the dispatch.

    Raises:
        AttributeError: as `bind_gl_linkage`.
        rdbms_params.RdbmsParamError: as `bind_gl_linkage`.
        SystemRecordUnavailableError: as `bind_gl_linkage`.

    Note:
        As `bind_gl_linkage` - the connection parameters come from the
        deployment contract, and `dal/connection.py` reports the frozen
        placeholder triple rather than refusing it.
    """
    pinned = resolve_clock(ns.run_date)
    pinned_state = menu_state
    file_defs = FileDefs()

    #  THE CALLER'S OWN RECORD, CARRIED THROUGH BY REFERENCE - see
    #  `_bind_system_record` and `bind_gl_linkage`.
    system_record = _bind_system_record(
        ns, pinned, env=env, system_record=system_record
    )

    #  THE TOTALS RECORD MUST BE THE MENU'S OWN OBJECT, not a second one. The
    #  nine period-total writes mutate the record passed as the THIRD linkage
    #  argument [sales/sl060.cbl:L397], and `overrewrite` rewrites
    #  `WS-System-Record-4` - the SAME `01` item, because a COBOL menu has only
    #  one. Handing the linkage a fresh `SystemRecord4` while the persist wrote
    #  `menu_state.system_record_4` would silently discard every period total.
    #
    #  AN EXPLICIT ARGUMENT WINS, AND IT IS FIRST IN THE ORDER FOR THE SAME REASON
    #  THE SYSTEM RECORD IS: it is the caller's `01` item, passed by reference, and
    #  replacing it would drop whatever the caller had seeded into it. The order is
    #  therefore explicit argument, then the menu's own record, then a declared
    #  default. A caller supplying BOTH should supply the SAME object - the linkage
    #  carries what it passed here and `overrewrite` persists
    #  `menu_state.system_record_4`, so two different instances would split the
    #  period totals from the row that gets written, exactly as passing two
    #  different `01` items would in COBOL if a menu had two.
    if system_record_4 is None:
        system_record_4 = (
            SystemRecord4()
            if pinned_state is None or pinned_state.system_record_4 is None
            else pinned_state.system_record_4
        )

    #  [sales/sales.cbl:L338-L360], [purchase/purchase.cbl:L333-L354] - keys 4
    #  and 1 only. Neither menu reads key 2.
    if pinned_state is not None:
        aa010_get_system_recs(
            system_record, pinned_state, file_defs, ns, pinned, env=env
        )

    return SlPlLinkage(
        calling_data=bind_calling_data(
            ns, called=called, caller=_menu_caller_for(called)
        ),
        system_record=system_record,
        system_record_4=system_record_4,
        to_day=pinned.to_day,
        file_defs=file_defs,
    )


def bind_irs_linkage(
    ns: argparse.Namespace,
    *,
    menu_state: MenuState | None = None,
    env: Mapping[str, str] | None = None,
) -> IrsLinkage:
    """Bind Shape 3 - the three-parameter IRS shape.

    No `called` keyword, because there is no `WS-Called` to fill: Shape 3 has no
    calling-data block [irs/irs030.cbl:L552-L554], and irs/irs.cbl names its callee as a
    `CALL` literal rather than through the field [irs/irs.cbl:L668].

    Args:
        ns: the parsed namespace of a route that composed
            `add_irs_linkage_arguments`. Only `run_date` is required.
        menu_state: the IRS menu's own WORKING-STORAGE. When supplied,
            `WS-System-Record` is LOADED with key 1 - the ONLY key this menu reads
            [irs/irs.cbl:L511-L512] - and `zz090_set_up_irs_system_data` is then
            performed, exactly as [irs/irs.cbl:L556] performs it immediately after
            `aa010-Get-System-Recs`. When omitted, the record is built at its
            declared defaults and `IRS-System-Params.Run-Date` is filled from the
            pinned clock alone.
        env: as `bind_gl_linkage`. Shape 3 carries `WS-System-Record` as its
            second argument - the maintainer's own `*> ACAS system rec.` at
            [irs/irs.cbl:L669] - so the connection fields reach the IRS route by
            exactly the same carrier as the other two shapes.
        system_record: as `bind_gl_linkage`. The IRS shell reads it under file-key
            1 and reads NOTHING ELSE - `move 1 to File-Key-No. perform
            acas000-Read-Indexed.` [irs/irs.cbl:L511-L512] - which is the third of
            the three divergent `aa010` shapes.
        irs_system_params: the `IRS-System-Params` the caller has already built by
            `zz090-Set-Up-IRS-System-Data` [irs/irs.cbl:L907-L997] out of that
            loaded record, through `acas_posting.cli.menu_state`. `None` builds one
            at its declared defaults, which carries `Next-Post` zero and would
            allocate posting keys from zero - see finding CLI-04. Either way the
            eight-character run date below is written into it here, because that is
            what `zz090-Proc-Run-Date.` [irs/irs.cbl:L972-L978] does and the pinned
            clock is this layer's business.

    BOTH RECORDS ARE BUILT HERE, NOT PASSED IN. `WS-System-Record` is the ACAS
    system record the IRS shell reads under file-key 1 and NOTHING ELSE - `move 1
    to File-Key-No. perform acas000-Read-Indexed.` [irs/irs.cbl:L511-L512], the
    third of the three divergent `aa010` shapes, driven here by the `menu_state`
    this function is handed. `IRS-System-Params` is built at its declared
    defaults and then filled by `zz090_set_up_irs_system_data`
    [irs/irs.cbl:L907-L997] out of that loaded record; without the load it would
    carry `Next-Post` zero and allocate posting keys from zero - finding CLI-04.
    Either way the eight-character run date is written into it here, because that
    is what `zz090-Proc-Run-Date.` [irs/irs.cbl:L972-L978] does and the pinned
    clock is this layer's business.

    ⭐ BINDING IS NOT THE WHOLE OF SHAPE 3, AND MUST NOT BE MISTAKEN FOR IT.
    What this function returns is the three records at their DECLARED DEFAULTS
    plus whatever argv supplies - which leaves `IRS-System-Params.Next-Post`, the
    POSTING-KEY ALLOCATOR `irs030` numbers each posting from, at ZERO. The frozen
    menu never calls `irs030` with the record in that state: between the bind and
    the dispatch it performs `aa010-Get-System-Recs` [irs/irs.cbl:L507-L551] to
    load the seeded `SYSTEM-REC` row and then `zz090-Set-Up-IRS-System-Data`
    [irs/irs.cbl:L556] to copy the allocator and seventeen other fields across.
    Both are performed for a caller that supplies `menu_state` - which every
    route does - by `aa010_get_system_recs`, whose key set comes from the
    `irs_menu_state()` block and is therefore key 1 alone, and by
    `zz090_set_up_irs_system_data`.  A caller that passes no `menu_state` gets
    neither. A caller that binds Shape 3 and dispatches without
    them allocates posting keys from zero and collides with the seed.

    ⭐ BINDING IS NOT THE WHOLE OF SHAPE 3, AND MUST NOT BE MISTAKEN FOR IT.
    What this function returns is the three records at their DECLARED DEFAULTS
    plus whatever argv supplies - which leaves `IRS-System-Params.Next-Post`, the
    POSTING-KEY ALLOCATOR `irs030` numbers each posting from, at ZERO. The frozen
    menu never calls `irs030` with the record in that state: between the bind and
    the dispatch it performs `aa010-Get-System-Recs` [irs/irs.cbl:L507-L551] to
    load the seeded `SYSTEM-REC` row and then `zz090-Set-Up-IRS-System-Data`
    [irs/irs.cbl:L556] to copy the allocator and seventeen other fields across.
    Both are the ROUTE's work, not argv binding's, so they live in
    `aa010_get_system_recs_irs` and `zz090_set_up_irs_system_data` and are called
    from `cli/irs_post.main`. A caller that binds Shape 3 and dispatches without
    them allocates posting keys from zero and collides with the seed.

    ⭐ BINDING IS NOT THE WHOLE OF SHAPE 3, AND MUST NOT BE MISTAKEN FOR IT.
    What this function returns is the three records at their DECLARED DEFAULTS
    plus whatever argv supplies - which leaves `IRS-System-Params.Next-Post`, the
    POSTING-KEY ALLOCATOR `irs030` numbers each posting from, at ZERO. The frozen
    menu never calls `irs030` with the record in that state: between the bind and
    the dispatch it performs `aa010-Get-System-Recs` [irs/irs.cbl:L507-L551] to
    load the seeded `SYSTEM-REC` row and then `zz090-Set-Up-IRS-System-Data`
    [irs/irs.cbl:L556] to copy the allocator and seventeen other fields across.
    Both are the ROUTE's work, not argv binding's, so they live in
    `aa010_get_system_recs_irs` and `zz090_set_up_irs_system_data` and are called
    from `cli/irs_post.main`. A caller that binds Shape 3 and dispatches without
    them allocates posting keys from zero and collides with the seed.

    Returns:
        The three arguments in COBOL parameter order [irs/irs.cbl:L668-L671], at
        their declared defaults except for what argv and the environment supply.
        NOT yet carrying the seeded system row - see the note above.

    Raises:
        AttributeError: as `bind_gl_linkage`.
        rdbms_params.RdbmsParamError: as `bind_gl_linkage`.
        SystemRecordUnavailableError: as `bind_gl_linkage`, and reached through the
            HANDLER-named vocabulary on this route [irs/irs.cbl:L513-L519].
        acas_posting.dal.facade.FacadeGoback: from the startup OPEN, which on this
            route performs `acas000-Check-4-Errors`
            [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L98-L102] and can therefore
            reach `Open-Error-Continued` and its `goback` [:L355-L364]. That
            `goback` returns from the MENU PROGRAM, and
            `acas_posting/cli/irs_post.py` absorbs it at that boundary - see
            `irs_menu_state`.

    Note:
        As `bind_gl_linkage` - the connection parameters come from the
        deployment contract, and `dal/connection.py` still refuses the frozen
        placeholder triple without a declaration at the call site.

    Note:
        THE SNAPSHOT `zz095` NEEDS IS NOT RETURNED HERE, and deliberately. It is
        not a linkage operand - `IrsLinkage` carries the three the frozen `CALL`
        passes and nothing else - so the route performs
        `zz090_set_up_irs_system_data` itself when it needs the snapshot, which is
        also how irs/irs.cbl reads: `perform zz090-Set-Up-IRS-System-Data.`
        [irs/irs.cbl:L556] is its own statement, with the maintainer's reminder
        "dont forget to run zz095 after".
    """
    pinned = resolve_clock(ns.run_date)
    ws_system_record = _bind_system_record(ns, pinned, env=env)

    #  Shape 3's FIRST argument is not a record the store holds - the menu builds
    #  it from the ACAS row [irs/irs.cbl:L934-L968] - so it starts at its declared
    #  defaults and `zz090` fills it below, after the load, because `zz090` reads
    #  the loaded values (`Next-Post` above all, which `irs030`'s in-scope section
    #  increments once per posting).
    irs_system_params = IrsSystemParams()

    file_defs = FileDefs()

    #  [irs/irs.cbl:L494-L519] `aa005-Open-System.` then
    #  `aa010-Get-System-Recs.` - KEY 1 ONLY on this route, so `menu_state`
    #  carries no totals record and no defaults record and `aa010_get_system_recs`
    #  reads neither.
    #
    #  [irs/irs.cbl:L556] `perform zz090-Set-Up-IRS-System-Data.` - performed
    #  here rather than left to the caller because it is unconditional in the
    #  frozen menu and because it OVERWRITES `IRS-System-Params.Run-Date` from the
    #  loaded row. The value it writes equals the line above: `_apply_cli_pins`
    #  has already re-pinned the binary `Run-Date` from `--run-date`, and
    #  `zz090-Proc-Run-Date` converts that same binary through the same
    #  `irs_run_date_x8`. The two agree by construction rather than by luck, which
    #  is why both are kept - the pre-load line still serves a caller that
    #  supplies no `menu_state`.
    if menu_state is not None:
        aa010_get_system_recs(
            ws_system_record, menu_state, file_defs, ns, pinned, env=env
        )
        zz090_set_up_irs_system_data(irs_system_params, ws_system_record)

    #  [irs/irs.cbl:L972-L978] `zz090-Proc-Run-Date.` - the eight-character IRS
    #  form, century dropped.
    #
    #  AMBIGUITY Q-CLI-IRS-RUNDATE: irs/irs.cbl always populates
    #  `IRS-System-Params.Run-Date` [copybooks/irswssystem.cob:L14] before any
    #  menu option runs and notes at [irs/irs.cbl:L636] that the "menu uses the
    #  irs param file dates", yet the posting record's own date comes from the
    #  data - `move WS-IRS-Post-Date to post-date` [irs/irs030.cbl:L1662] - so
    #  does `irs030` observe this field at all? Left for the compiled oracle to
    #  settle (rule R-6).
    #
    #  ⭐ STATED AFTER THE LOAD, AND IT AGREES WITH `zz090` BY CONSTRUCTION. The
    #  frozen menu derives this field from the loaded `ACAS-Run-Date`
    #  [irs/irs.cbl:L973], and `_apply_cli_pins` has already re-pinned that
    #  binary `Run-Date` from `--run-date`, so `zz090` converts the same value
    #  through the same `irs_run_date_x8` this line uses. Written unconditionally
    #  because a caller that binds the linkage WITHOUT a `menu_state` - a
    #  program-level test - never reaches `zz090` and must still get the run date
    #  the clock pinned (rule R-6).
    irs_system_params.run_date = irs_run_date_x8(pinned.to_day)

    ws_system_record = _bind_system_record(ns, pinned, env=env)
    file_defs = FileDefs()

    #  [irs/irs.cbl:L494-L519] `aa005-Open-System.` then
    #  `aa010-Get-System-Recs.` - KEY 1 ONLY on this route, so `menu_state`
    #  carries no totals record and no defaults record and `aa010_get_system_recs`
    #  reads neither.
    #
    #  [irs/irs.cbl:L556] `perform zz090-Set-Up-IRS-System-Data.` - performed
    #  here rather than left to the caller because it is unconditional in the
    #  frozen menu and because it OVERWRITES `IRS-System-Params.Run-Date` from the
    #  loaded row. The value it writes equals the line above: `_apply_cli_pins`
    #  has already re-pinned the binary `Run-Date` from `--run-date`, and
    #  `zz090-Proc-Run-Date` converts that same binary through the same
    #  `irs_run_date_x8`. The two agree by construction rather than by luck, which
    #  is why both are kept - the pre-load line still serves a caller that
    #  supplies no `menu_state`.
    if menu_state is not None:
        aa010_get_system_recs(
            ws_system_record, menu_state, file_defs, ns, pinned, env=env
        )
        zz090_set_up_irs_system_data(irs_system_params, ws_system_record)

    return IrsLinkage(
        irs_system_params=irs_system_params,
        #  The binary Run-Date on this route is NOT ambiguous: the ACAS system
        #  record is the second linkage argument, with the maintainer's own
        #  comment `*> ACAS system rec.` at [irs/irs.cbl:L669].
        ws_system_record=ws_system_record,
        file_defs=file_defs,
    )


# FAITHFUL HELPERS (section 8.6 of this module's brief) Each of the five reproduces ONE
# COBOL statement or ONE COBOL predicate, and nothing more.


def reset_term_code(calling_data: WsCallingData) -> None:
    """`move zero to ws-term-code.` - reproduced exactly.

    The placement is load-bearing rather than tidy.

    Args:
        calling_data: the record to clear. Mutated in place, exactly as COBOL writes
            into the caller's own storage.
    """
    calling_data.ws_term_code = cobol_move.move(
        WS_TERM_CODE_DEFAULT, calling_data_record.descriptor_for("ws_term_code")
    )


def set_called(calling_data: WsCallingData, program_id: str) -> None:
    """`move "<prog>" to ws-called.` - reproduced exactly.

    RECEIVING-FIELD WIDTH IS APPLIED. `WS-Called` is `PIC X(8)`
    [copybooks/wscall.cob:L7], so the `MOVE` of a five-character program-id leaves eight
    characters - "gl070" followed by three spaces - and a nine-character sender would
    lose its last character.

    Args:
        calling_data: the record to write into. Mutated in place.
        program_id: the callee's program-id, as `"gl070"`. Space-filled or truncated to
            the field's eight characters.
    """
    calling_data.ws_called = cobol_move.move(
        program_id, calling_data_record.descriptor_for("ws_called")
    )


def is_serious_error(term_code: int) -> bool:
    """`if ws-term-code > 7` - the serious-error predicate.

    Note what this predicate does NOT single out. `GL_ABORT_TERM_CODE` is 5, which is `<
    8`, so a General Ledger abort is NOT a serious error by this test.

    Args:
        term_code: the value of `WS-Term-Code` after a dispatch.

    Returns:
        True when the callee reported a serious error.
    """
    return term_code > SERIOUS_ERROR_THRESHOLD


def exit_status_for(term_code: int) -> int:
    """Map `WS-Term-Code` to a process exit status.

    Where the COBOL keeps this information, for reference: it never exits with it.

    Args:
        term_code: the value of `WS-Term-Code` after the last dispatch.

    Returns:
        The exit status to leave the process with.
    """
    # ORACLE OBSERVABLE, which rule R-6 can only be applied to once that is proved
    # rather than asserted.
    return term_code


#  THE ONE CONFIGURATION-FAILURE CONTRACT, SHARED BY ALL SEVEN ROUTES AND THE
#  PACKAGE ROUTER  (finding CLI-09)
#  Before this, one route caught every `ValueError` and mapped it to 1 or 8 while
#  the other six caught nothing and let the same missing deployment contract
#  surface as an uncaught traceback with a generic status. One condition, seven
#  behaviours. The contract is now written down once, here, and every `main`
#  spells it the same way::
#
#      try:
#          state = menu_state.<ledger>_get_system_recs()
#      except args.RdbmsParamError as error:
#          return args.report_configuration_failure(
#              error, logger=_LOG, subject="General Ledger"
#          )
#
#  THE EXACT TYPE, NOT `ValueError`. `RdbmsParamError` subclasses `ValueError`,
#  so catching the base class also swallowed a genuine defect - a bad namespace
#  attribute, a malformed record - and reported it as a configuration problem.
#  Only the exact type is caught now, and everything else keeps its traceback,
#  which is the only diagnostic a real defect leaves behind.


def report_configuration_failure(
    error: RdbmsParamError,
    *,
    logger: logging.Logger,
    subject: str,
) -> int:
    """Report an absent or unusable connection contract, and return its status.

    NO COBOL COUNTERPART, and the reason is worth stating rather than glossing.
    The frozen load programs abandon on exactly this condition by displaying a
    message and issuing a bare `goback` WITHOUT setting a return code
    [common/glbatchLD.cbl:L245-L259], so there is no frozen exit-status vocabulary
    to reproduce. What IS frozen is the parameter loader's own return code -
    `RDB_RETURN_NO_SOURCE` (8) when the contract is absent entirely and
    `RDB_RETURN_MALFORMED` (1) when it is present but cannot work
    [common/acas-get-params.cbl:L37-L42] - and that is what this surfaces, so a
    caller can tell "not configured" from "misconfigured" without parsing text.

    NOTHING HAS BEEN TOUCHED WHEN THIS IS REACHED. The error is raised while the
    six connection fields are still being resolved, before any database is
    contacted, any file opened or any program module entered, so a run that
    reports this has changed no table.

    THE MESSAGE CANNOT LEAK A CREDENTIAL. `RdbmsParamError` never carries a
    parameter value - it names a length and a limit at most - so logging it is
    safe, and no value is added to it here.

    Args:
        error: the failure raised by the binder or by the menu-state loader.
        logger: the calling module's own logger, so the record is attributed to
            the route the operator invoked rather than to this shared helper.
        subject: what could not be prepared, in the operator's terms - e.g.
            `"General Ledger"`, `"Sales"`, `"IRS"`. Appears in the record and
            nowhere else.

    Returns:
        The frozen return code the error carries, which the route returns as its
        process exit status.
    """
    logger.error(
        "%s: the ACAS_DB_* deployment contract for the database connection is "
        "absent or unusable, so nothing was run and no table was touched "
        "[common/acas-get-params.cbl:L37-L42]: %s",
        subject,
        error,
    )
    return error.return_code


def irs_run_date_x8(to_day: str) -> str:
    """`zz090-Proc-Run-Date.` [irs/irs.cbl:L972-L978] - reproduced exactly.

    Args:
        to_day: the pinned `to-day`, DD/MM/CCYY. In the COBOL `u-date` is `PIC X(10)`
            and therefore always exactly ten characters, so both slices are always in
            range.

    Returns:
        The eight-character `dd/mm/yy` form that `IRS-System-Params.Run-Date pic x(8)`
            [copybooks/irswssystem.cob:L14] holds.
    """
    return to_day[0:6] + to_day[8:10]


# =============================================================================
#  THE TRANSPORT-SECURITY DECLARATION  -  one contract, every route
# =============================================================================
#
#  NO COBOL COUNTERPART, AND THAT IS THE WHOLE PROBLEM IT SOLVES.
#  The frozen bridge reaches the server through six values and nothing else:
#
#      call "MySQL_real_connect" using Host-Name, Implementation, Password,
#           Base-Name, Port-Number, Socket   [copybooks/mysql-procedures.cpy:L72-L77]
#
#  - no certificate, no key, no verification mode. Transport is compiled into
#  `cobmysqlapi.c` and is therefore not something the COBOL can be asked about,
#  which means the migration has to decide it somewhere. `dal/connection.py`
#  decides it FAIL-CLOSED: a Unix socket or a loopback address is permitted, and
#  any other target is refused unless the caller supplies a certificate
#  authority or declares that the target is the isolated parity harness.
#
#  ⭐ WHY THE DECLARATION BELONGS HERE, AT THE PROCESS BOUNDARY.
#  The refusal is only useful if a legitimate operator has a way to say what
#  they meant, and there is exactly one place that knows: the person who typed
#  the command. Before this section existed there was no such place, so the
#  knowledge leaked downwards - one handler decided for itself that every
#  connection it opened was an isolated-oracle connection, which silently
#  granted plaintext to WHATEVER host `RDBMS-Host` happened to name while the
#  other nineteen handlers failed closed (CWE-319, CWE-295). The fix is not a
#  better default; it is a single declaration, made once, by the caller, and
#  carried unchanged to every handler that can honour it.
#
#  THE ENVIRONMENT SPELLINGS ARE THE HARNESS'S OWN, NOT NEW ONES.
#  `harness/build_oracle.sh` and `harness/seed.sh` already refuse a non-local
#  target unless `ACAS_DB_TLS_CA` names a readable PEM bundle or
#  `ACAS_DB_ALLOW_PLAINTEXT` is set, and `harness/docker-compose.yml` documents
#  both. Reading the same two variables makes the shell half and the Python half
#  of the harness obey ONE contract rather than two that can disagree; the
#  command line takes precedence over both, so a scenario can always be pinned
#  explicitly.
#
#  R-6 IS NOT AT RISK. A transport policy decides whether a connect is
#  PERMITTED; it never changes a posted figure, a status, a statement or a write
#  order, so it cannot make two runs of one scenario differ in table state. The
#  run date, which can, is still `--run-date` and still has no environment
#  fallback of any kind.
#
#  THE ONE IMPORT OF THE DATA-ACCESS LAYER IN THIS PACKAGE, AND WHY IT IS RIGHT.
#  `TransportSecurity` is a frozen, slotted value object: four optional strings
#  and a bool, no connection, no cursor, no statement, no handler. Agent Action
#  Plan section 0.4.3 forbids a `cli` module to import `dal.acas*` - the handler
#  modules - and this is not one of those; `dal/connection.py` imports no
#  handler either, so the edge introduces no cycle and no handler dependency.
#  The alternative was to invent a second policy type here and translate it in
#  the data-access layer, which would put two spellings of one security decision
#  in the tree and a conversion between them - the shape of defect this whole
#  section exists to remove. Note that this does NOT reopen the credential
#  question settled in `__all__`: `carries_frozen_placeholder_rdbms_credentials`
#  is a predicate over four SYSTEM-REC FIELD VALUES and belongs to the record
#  layer that declares them, which is a different thing from a policy object
#  that has no COBOL field at all.

#: `ACAS_DB_TLS_CA` - the PEM bundle the server certificate must chain to.
#: The spelling is `harness/build_oracle.sh`'s [harness/build_oracle.sh:L1697]
#: and `harness/seed.sh`'s [harness/seed.sh:L1401].
TLS_CA_VARIABLE: Final[str] = "ACAS_DB_TLS_CA"

#: `ACAS_DB_ALLOW_PLAINTEXT` - the harness's explicit isolated-network
#: declaration [harness/build_oracle.sh:L1716-L1719]. Any non-empty value other
#: than `0` declares it, matching the shell scripts' own reading.
ALLOW_PLAINTEXT_VARIABLE: Final[str] = "ACAS_DB_ALLOW_PLAINTEXT"


def add_transport_security_arguments(parser: argparse.ArgumentParser) -> None:
    """Add the four transport-security options every route shares.

    Composed by every entry point, including the ones whose programs reach no
    handler that declares a transport policy: a declaration that is accepted
    everywhere and honoured where it applies is one an operator can make without
    knowing the handler inventory, and `dal/facade.py` projects it onto whatever
    extras each handler actually declares.

    Args:
        parser: the parser to add the options to. Mutated in place.
    """
    parser.add_argument(
        "--db-tls-ca",
        metavar="PEM",
        default=None,
        help=(
            "Certificate-authority bundle the server's certificate is verified "
            "against. Supplying it turns on TLS with BOTH certificate and "
            "host-name verification, which is what makes it protection rather "
            f"than decoration. Falls back to ${TLS_CA_VARIABLE}, the same "
            "variable harness/build_oracle.sh and harness/seed.sh read, so the "
            "shell and Python halves of the harness obey one contract."
        ),
    )
    parser.add_argument(
        "--db-tls-cert",
        metavar="PEM",
        default=None,
        help=(
            "Client certificate, when the server requires one. Must be given "
            "together with --db-tls-key; either alone is refused, because a "
            "certificate cannot authenticate without its private key."
        ),
    )
    parser.add_argument(
        "--db-tls-key",
        metavar="PEM",
        default=None,
        help="Private key for --db-tls-cert. Must be given together with it.",
    )
    parser.add_argument(
        "--db-allow-plaintext",
        action="store_true",
        default=False,
        help=(
            "Declare that the target is the isolated parity harness - a private "
            "container network whose server has no TLS material at all - and "
            "that an unprotected connection to it is intended. WITHOUT this, or "
            "--db-tls-ca, a non-local target is REFUSED: the credentials of "
            "copybooks/wssystem.cob:L138-L139 and every posted figure would "
            "otherwise cross the network in the clear. Grants nothing else, and "
            "in particular does not admit the frozen placeholder credentials, "
            f"which have their own declaration. Falls back to "
            f"${ALLOW_PLAINTEXT_VARIABLE}."
        ),
    )


def bind_transport_security(
    namespace: argparse.Namespace,
    *,
    environ: Mapping[str, str] | None = None,
) -> TransportSecurity:
    """Resolve the operator's transport declaration into one policy object.

    Precedence is command line, then environment, then nothing - and "nothing"
    is the fail-closed policy, never an absent one.

    Args:
        namespace: the parsed arguments. Options this function reads may be
            absent, in which case the environment is consulted; that is what
            lets a route compose only the options it wants to publish.
        environ: the environment to read the two fallbacks from. Defaults to the
            process environment. Injectable so a test pins it, which is also
            what keeps this function free of an implicit ambient input.

    Returns:
        The policy. Every field at its default means loopback and Unix sockets
        only, which is what a caller who said nothing gets.

    Raises:
        ValueError: `--db-tls-cert` was given without `--db-tls-key`, or the
            reverse. Refused here, at the boundary, so the message names the
            option the operator typed rather than the field the data-access
            layer sees. `dal/connection.py` refuses the same combination again
            at the connect, because a policy built by any other caller must be
            checked too.
    """
    source = os.environ if environ is None else environ

    ca_file = getattr(namespace, "db_tls_ca", None) or source.get(
        TLS_CA_VARIABLE
    )
    certificate_file = getattr(namespace, "db_tls_cert", None)
    key_file = getattr(namespace, "db_tls_key", None)

    #  The shell scripts treat any value other than empty and `0` as the
    #  declaration [harness/build_oracle.sh:L1716]; read the same way here so
    #  one exported variable cannot mean two different things.
    declared = source.get(ALLOW_PLAINTEXT_VARIABLE, "").strip()
    allow_plaintext = bool(getattr(namespace, "db_allow_plaintext", False)) or (
        declared not in {"", "0"}
    )

    if bool(certificate_file) != bool(key_file):
        raise ValueError(
            "--db-tls-cert and --db-tls-key must be given together: a client "
            "certificate cannot authenticate without its private key"
        )

    return TransportSecurity(
        ca_file=ca_file or None,
        certificate_file=certificate_file or None,
        key_file=key_file or None,
        isolated_oracle=allow_plaintext,
    )


def dal_options_for(
    namespace: argparse.Namespace,
    *,
    environ: Mapping[str, str] | None = None,
) -> Mapping[str, object]:
    """The keyword-only extras a route hands its program modules.

    One mapping, built once per run, passed to every program the route
    dispatches, and carried by the program to every facade context it builds.
    `dal/facade.py` then projects it onto whatever extras each handler declares,
    so the operator states the policy once and it reaches every handler that can
    honour it - without the route needing to know which those are.

    Args:
        namespace: the parsed arguments.
        environ: as `bind_transport_security`.

    Returns:
        A mapping carrying the transport policy under the key the handlers
        declare it by. Never empty: the policy is always stated, and when the
        operator declared nothing it is the fail-closed one, which is a
        statement rather than an omission.

    Raises:
        ValueError: as `bind_transport_security`.
    """
    return {"transport": bind_transport_security(namespace, environ=environ)}


def declare_connection_policy(
    namespace: argparse.Namespace,
    *,
    environ: Mapping[str, str] | None = None,
) -> TransportSecurity:
    """State the resolved policy to the handlers that take it no other way.

    PUBLISHED, AND NOT ON ANY ROUTE'S CRITICAL PATH. The seventeen handlers split
    three ways: ELEVEN declare a keyword-only `transport` on their `dispatch` and
    are reached by `dal_options_for`, carried on every facade context the program
    builds; TWO - `acas000_system` and `acasirsub1_irs_nominal` - are reached
    only through a module-level
    declaration, which is the equivalent of setting a COBOL sub-program's working
    storage before the first `CALL`, exactly what the frozen tree does with the
    six `RDBMS-*` values [common/acas008.cbl:L558-L563]. `acas007_gl_batch`
    supports both routes for compatibility. This function calls the one door
    `dal/facade.py` publishes over the module-level routes, so a caller that wants
    the declaration set on them directly
    can state it once without knowing which mechanism any handler uses.

    NONE OF THAT IS LOAD-BEARING ANY MORE, AND THE REASON MATTERS. The
    declaration is resolved in ONE place - `dal.connection.mysql_1000_open` reads
    `connection_policy()` on EVERY open and uses the installed policy wherever the
    caller declared nothing - so the policy `install_connection_policy` puts in
    place before the first `fn-Open` governs all seventeen handlers, including the
    five that publish no mechanism at all, without any of them knowing it exists.
    That is why no route calls this function: there is nothing left for it to
    reach. It stays published for an orchestrator that wants the module-level
    declaration made explicitly as well.

    Args:
        namespace: the parsed arguments.
        environ: as `bind_transport_security`.

    Returns:
        The policy that was declared, so the caller can pass the SAME object to
        `dal_options_for`'s consumers rather than resolving it twice and risking
        two answers.

    Raises:
        ValueError: as `bind_transport_security`.
    """
    policy = bind_transport_security(namespace, environ=environ)
    facade.declare_connection_policy(transport=policy)
    return policy


# =============================================================================
#  THE BOUNDARY: EXPECTED FAILURES, AND STATED DESTRUCTIVE INTENT
# =============================================================================
#
#  Two things every entry point needs and none of them should spell for itself.
#
#  1. AN EXPECTED FAILURE IS NOT A DEFECT, AND MUST NOT LOOK LIKE ONE.
#     A missing connection contract, a malformed one, and a transport
#     declaration that cannot be honoured are all CONFIGURATION failures at the
#     process boundary. Letting one escape prints a Python traceback, which
#     tells an operator nothing they can act on and tells anyone else the
#     absolute paths of the installation, the module layout and the internal
#     call chain (CWE-209). A defect INSIDE the cycle is the opposite case and
#     keeps its traceback, because there the traceback is the only diagnostic.
#
#  2. OMISSION IS NOT CONSENT.
#     Several prompts in the frozen source gate a database write, and Agent
#     Action Plan section 0.3.4 turns each into "an explicit CLI parameter with
#     the COBOL default preserved". The default IS preserved - it is what
#     `--help` shows and what the program module still declares - but a COBOL
#     default is the answer a HUMAN AT A TERMINAL gives by pressing Return
#     having just READ the question. An option the operator never typed is not
#     that: nobody was asked. `require_stated` closes exactly that gap - it
#     asks the operator to say which answer they mean, and then the answer they
#     chose is passed onward completely unaltered.
#
#     THIS CHANGES NO PROGRAM BEHAVIOUR AND NO LEGACY DEFAULT (rule R-4). The
#     gate is at the argv boundary, which has no COBOL counterpart at all; the
#     program modules keep their own defaults, and a library or harness caller
#     that invokes them directly is untouched.


#: The exceptions an entry point should REPORT rather than propagate.
#:
#: `ValueError` covers the linkage binders, including
#: `rdbms_params.RdbmsParamError`, which subclasses it and carries the frozen
#: return code of the parameter loader the whole loader family calls
#: [common/acas-get-params.cbl:L37-L42]. `ConnectionPolicyError` covers a
#: transport or credential declaration the data-access layer refuses.
#: `SystemRecordUnavailableError` covers the one condition the frozen menus
#: themselves refuse to dispatch past - a key-1 read that did not succeed
#: [general/general.cbl:L412-L418] - and belongs here because it is a state of the
#: SEEDED DATABASE rather than a defect in this code: the run stops having written
#: nothing, and the operator's remedy is to seed SYSTEM-REC.
#:
#: Deliberately NOT including `Exception`: a failure inside the cycle is a defect
#: and must keep its traceback. Deliberately NOT including `SystemExit` either -
#: argparse raises it for `--help` and for a usage error, and both must be left
#: alone.
EXPECTED_BOUNDARY_ERRORS: Final[tuple[type[Exception], ...]] = (
    ValueError,
    ConnectionPolicyError,
    SystemRecordUnavailableError,
)


def boundary_exit_status(error: Exception) -> int:
    """Return the exit status for an expected boundary failure.

    THE ONE IMPLEMENTATION, shared by all seven routes so they cannot disagree
    about what a configuration failure is worth.

    `rdbms_params.RdbmsParamError` carries the frozen parameter loader's own
    return code - 8 when the contract is absent entirely and 1 when it is present
    but unusable [common/acas-get-params.cbl:L37-L42] - and surfacing that code is
    what lets a caller tell "not configured" from "misconfigured" without parsing
    a message. The attribute is read reflectively rather than by importing the
    class, because `rdbms_params` is reached only through this module and this
    module does not re-export it.

    Args:
        error: the failure raised at the boundary.

    Returns:
        The error's own frozen return code when it carries one, otherwise the
        smallest status the frozen menu treats as a serious error - derived from
        `SERIOUS_ERROR_THRESHOLD` rather than typed, so the two cannot disagree
        [general/general.cbl:L720].
    """
    return_code = getattr(error, "return_code", None)
    if isinstance(return_code, int):
        return return_code
    return SERIOUS_ERROR_THRESHOLD + 1


def redact_boundary_error(error: Exception) -> str:
    """Render a boundary failure as one bounded, single-line, redacted message.

    Uses the data-access layer's own redactor so that the CLI and the handlers
    cannot disagree about what a safe diagnostic looks like: identities and
    secrets are removed, control characters are escaped so the text cannot forge
    a second log record (CWE-117), and the result is length-capped.

    The exception's CLASS NAME is included and its traceback is not. The class
    name is a stable token an operator can grep and an alert can match on; the
    traceback is what would disclose the installation's paths and internals
    (CWE-209).

    Args:
        error: the failure raised at the boundary.

    Returns:
        `"<ClassName>: <redacted message>"`, or just the class name when the
        exception carries no message.
    """
    message = redact_for_log(str(error))
    return f"{type(error).__name__}: {message}" if message else type(error).__name__


#: The namespace attribute `ExplicitBooleanOptionalAction` records against.
#:
#: An implementation detail of this module's own making, named so it cannot
#: collide with an option `dest`: no COBOL field, and therefore no option, is
#: spelled with a leading underscore.
STATED_OPTIONS_ATTRIBUTE: Final[str] = "_stated_options"


class ExplicitBooleanOptionalAction(argparse.BooleanOptionalAction):
    """`BooleanOptionalAction` that also records that the operator stated it.

    Needed because a value cannot answer the question. `--clear-posting-file`
    stores `True` and the COBOL default is `True`, so comparing the parsed value
    against the default cannot tell "the operator asked for the destructive
    answer" from "the operator was never asked". This records the fact of the
    statement alongside the value, leaving the value and the default exactly as
    they were.

    Publishes both spellings from one declaration, as its base class does, so the
    affirmative and the negative cannot drift apart.
    """

    def __call__(  # noqa: D102 - argparse.Action's own contract
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: object,
        option_string: str | None = None,
    ) -> None:
        super().__call__(parser, namespace, values, option_string)
        stated = set(getattr(namespace, STATED_OPTIONS_ATTRIBUTE, ()))
        stated.add(self.dest)
        setattr(namespace, STATED_OPTIONS_ATTRIBUTE, frozenset(stated))


class _StatedAction(argparse.Action):
    """A value-storing action that also records that the operator stated it.

    The non-boolean counterpart of :class:`ExplicitBooleanOptionalAction`, for an
    option whose COBOL answer is a number rather than a yes or a no - the
    disk-change option of [general/gl080.cbl:L542-L549], where 0 proceeds and 9
    aborts.
    """

    def __call__(  # noqa: D102 - argparse.Action's own contract
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: object,
        option_string: str | None = None,
    ) -> None:
        setattr(namespace, self.dest, values)
        stated = set(getattr(namespace, STATED_OPTIONS_ATTRIBUTE, ()))
        stated.add(self.dest)
        setattr(namespace, STATED_OPTIONS_ATTRIBUTE, frozenset(stated))


#: `_StatedAction` under a public name, so an entry point can pass
#: `action=args.STATED_ACTION` without reaching for a private symbol. The class
#: itself stays private because it is an implementation of `argparse.Action` and
#: not something a caller should subclass.
STATED_ACTION: Final[type[argparse.Action]] = _StatedAction


def stated_explicitly(namespace: argparse.Namespace, dest: str) -> bool:
    """Did the operator actually type the option `dest` came from?

    Args:
        namespace: the parsed arguments.
        dest: the option's `dest`.

    Returns:
        `True` only when the option was present on the command line. An option
        declared with an ordinary action is never recorded, so this answers
        `False` for it - which is correct, because such an option carries no
        destructive intent to state.
    """
    return dest in getattr(namespace, STATED_OPTIONS_ATTRIBUTE, frozenset())


def require_stated(
    parser: argparse.ArgumentParser,
    namespace: argparse.Namespace,
    *requirements: tuple[str, str],
) -> None:
    """Refuse to run until the operator has stated every destructive answer.

    Called by an entry point after `parse_args` and BEFORE anything is bound,
    connected or dispatched, so a refusal leaves the database wholly untouched.

    WHAT THIS IS NOT. It is not a confirmation prompt - there is nothing to
    prompt, this is a batch entry point. It is not a change to any COBOL default:
    the parser still carries the frozen answer, `--help` still shows it, and the
    program module still declares it. And it is not a validation of the ANSWER -
    both answers are equally acceptable and neither is rejected, which matters
    because rejecting one would be a check the COBOL has not got (rule R-3).

    Args:
        parser: the parser, used for its `error` so the refusal is spelled the way
            every other usage error on this route is spelled.
        namespace: the parsed arguments.
        *requirements: `(dest, sentence)` pairs. The sentence says what the answer
            decides and is quoted verbatim in the refusal, so the operator is told
            what they are being asked to take responsibility for.

    Returns:
        None when every requirement was stated.

    Raises:
        SystemExit: through `parser.error`, with argparse's usage status 2, when
            one or more were not. Left as `SystemExit` deliberately: an omitted
            destructive answer is a usage error, exactly like an omitted
            `--run-date`, and must be indistinguishable from one to a caller.
    """
    missing = [
        (dest, sentence)
        for dest, sentence in requirements
        if not stated_explicitly(namespace, dest)
    ]
    if not missing:
        return

    lines = [
        "this run would change or destroy database state, and the intent has "
        "not been stated. State each answer below explicitly - the value you "
        "choose is passed to the program unaltered, and the COBOL default shown "
        "in --help is still available by naming it:",
    ]
    lines.extend(f"  * {sentence}" for _, sentence in missing)
    parser.error("\n".join(lines))


# --- traceability ------------------------------------------------------------
#
# MODULE -> COBOL SOURCE  (rule R-5)
#   acas_posting/cli/args.py  <-  copybooks/wscall.cob L6-L14, plus the linkage
#   and dispatch behaviour of copybooks/wssystem.cob, copybooks/wssys4.cob,
#   copybooks/wsnames.cob, copybooks/irswssystem.cob,
#   copybooks/Proc-ACAS-Mapser-RDB.cob, general/general.cbl, sales/sales.cbl,
#   purchase/purchase.cbl, irs/irs.cbl and common/ACAS.cbl. All ten are
#   REFERENCE only - frozen, read as specification. Any diff touching them is a
#   defect in the migration.
#
# FIELD -> COPYBOOK LINE   `01 WS-Calling-Data.` at copybooks/wscall.cob:L6
#   WS-Called        pic x(8)   L7   -> WsCallingData.ws_called
#                                       set by set_called, per dispatch
#   WS-Caller        pic x(8)   L8   -> WsCallingData.ws_caller
#                                       --ws-caller, default _menu_caller_for
#   WS-Del-Link      pic x(8)   L9   -> WsCallingData.ws_del_link
#                                       --ws-del-link, default spaces
#   WS-Term-Code     pic 99     L10  -> WsCallingData.ws_term_code
#                                       NO option; output only; reset per call
#   WS-Process-Func  pic 9      L12  -> WsCallingData.ws_process_func
#                                       --ws-process-func, default 0
#   WS-Sub-Function  pic 9      L13  -> WsCallingData.ws_sub_function
#                                       --ws-sub-function, default 0
#   WS-CD-Args       pic x(13)  L14  -> WsCallingData.ws_cd_args
#                                       --ws-cd-args, default spaces
#   (L11 is the maintainer's `*> new 18/5/13` comment between L10 and L12.)
#
# OTHER FIELD -> LOCATOR
#   to-day           pic x(10)        -> GlLinkage.to_day, SlPlLinkage.to_day
#                                       general/general.cbl:L357,
#                                       sales/sales.cbl:L309,
#                                       purchase/purchase.cbl:L304,
#                                       irs/irs.cbl:L405
#   SYSTEM-REC Run-Date  binary-long  -> _bind_system_record, from the clock
#                                       copybooks/wssystem.cob:L67
#   SYSTEM-REC Date-Form pic 9        -> --date-form
#                                       copybooks/wssystem.cob:L128, condition
#                                       names L129 L130 L131, valid-set L132
#   SYSTEM-REC IRS-Instead pic x      -> --irs-instead
#                                       copybooks/wssystem.cob:L179, condition
#                                       names L180 L181
#   IRS-System-Params run-date x(8)   -> bind_irs_linkage, via irs_run_date_x8
#                                       copybooks/irswssystem.cob:L14 (the 01
#                                       group is L13, renamed at irs/irs.cbl:L392)
#   File-Defs                         -> FileDefs(), declared defaults only
#                                       copybooks/wsnames.cob:L13, group L14,
#                                       the two gl071 work-file names L15-L16
#   SYSTOT-REC                        -> SystemRecord4(), declared defaults only
#                                       copybooks/wssys4.cob
#
# CONSTANT -> LOCATOR
#   RUN_DATE_FORMAT                 general/general.cbl:L357, sales/sales.cbl:L309,
#                                   purchase/purchase.cbl:L304, irs/irs.cbl:L405;
#                                   field order fixed by
#                                   copybooks/Proc-ACAS-Mapser-RDB.cob:L73-L76
#   WS_CALLER_GENERAL   "general"   general/general.cbl:L512
#   WS_CALLER_SALES     "sales"     sales/sales.cbl:L481, also L465
#   WS_CALLER_PURCHASE  "purchase"  purchase/purchase.cbl:L475, also L459
#   WS_CALLER_ACAS      "ACAS"      common/ACAS.cbl:L431
#   WS_DEL_LINK_DEFAULT spaces      general/general.cbl:L513, sales/sales.cbl:L482
#                                   and L467, purchase/purchase.cbl:L476 and L461,
#                                   common/ACAS.cbl:L432
#   WS_PROCESS_FUNC_DEFAULT 0       general/general.cbl:L505, sales/sales.cbl:L474
#                                   and L468, purchase/purchase.cbl:L468 and L462
#   WS_SUB_FUNCTION_DEFAULT 0       the same statements; individually at
#                                   sales/sales.cbl:L469, purchase/purchase.cbl:L463
#   WS_CD_ARGS_DEFAULT  spaces      copybooks/wscall.cob:L14 - NEVER ASSIGNED by
#                                   any menu shell; read only, at
#                                   sales/sales.cbl:L463 and
#                                   purchase/purchase.cbl:L457
#   WS_TERM_CODE_DEFAULT 0          general/general.cbl:L714 and L730,
#                                   sales/sales.cbl:L680 and L701,
#                                   purchase/purchase.cbl:L673 and L694,
#                                   common/ACAS.cbl:L576
#   GL_ABORT_TERM_CODE  5           raised general/gl070.cbl:L289 (conditional
#                                   L287-L290); tested general/general.cbl:L810-L811
#   EXTRACT_MISSING_FILE_TERM_CODE 8  sales/sl055.cbl:L344 and
#                                   purchase/pl055.cbl:L286, each followed
#                                   immediately by `goback` (L345 / L287)
#   SERIOUS_ERROR_THRESHOLD 7       general/general.cbl:L720 and L735,
#                                   sales/sales.cbl:L691 and L710,
#                                   purchase/purchase.cbl:L684 and L703,
#                                   common/ACAS.cbl:L578
#
# CARRIER -> CALL SHAPE
#   GlLinkage     4 members  general/general.cbl `load00.`  L711-L723, CALL
#                            parameter list L715-L718; callee
#                            general/gl070.cbl:L245-L248
#   SlPlLinkage   5 members  sales/sales.cbl `load000.` CALL L702-L707;
#                            purchase/purchase.cbl `load000.` CALL L695-L700;
#                            callee sales/sl060.cbl:L395-L399
#   IrsLinkage    3 members  irs/irs.cbl `Main-Loop.` CALL L668-L671; callee
#                            irs/irs030.cbl:L552-L554
#
# HELPER -> COBOL STATEMENT
#   reset_term_code    `move zero to ws-term-code`      general/general.cbl:L714
#                                                       and L730,
#                                                       sales/sales.cbl:L680 and
#                                                       L701,
#                                                       purchase/purchase.cbl:L673
#                                                       and L694,
#                                                       common/ACAS.cbl:L576
#   set_called         `move "<prog>" to ws-called`     general/general.cbl:L808,
#                                                       L812, L814, L820
#   is_serious_error   `if ws-term-code > 7`            general/general.cbl:L720
#                                                       and L735,
#                                                       sales/sales.cbl:L691 and
#                                                       L710,
#                                                       purchase/purchase.cbl:L684
#                                                       and L703,
#                                                       common/ACAS.cbl:L578
#   exit_status_for    no COBOL equivalent - the menus never exit with the code;
#                                                       see Q-CLI-EXITSTATUS
#   irs_run_date_x8    `zz090-Proc-Run-Date.`           irs/irs.cbl:L972-L978,
#                                                       the STRING at L975-L977,
#                                                       intent at L968-L971
#   resolve_clock      `move zero to u-bin` / `call "maps04"` / `move u-bin to
#                      run-date`                        copybooks/
#                                                       Proc-ACAS-Mapser-RDB.cob:
#                                                       L78-L80
#   _menu_caller_for   `move "general"/"sales"/"purchase" to ws-caller`
#                                                       general/general.cbl:L512,
#                                                       sales/sales.cbl:L481,
#                                                       purchase/purchase.cbl:L475
#
# RE-EXPORT -> COBOL PROGRAM
#   bind_rdbms_connection   the six `MOVE ... to RDBMS-*` statements every load
#                           program performs after `call "acas-get-params"`,
#                           common/glbatchLD.cbl:L262-L267 and identically at
#                           common/nominalLD.cbl:L248-L253 and
#                           common/glpostingLD.cbl:L263-L268. Implemented in
#                           acas_posting/cli/rdbms_params.py, which reproduces
#                           common/acas-get-params.cbl in full and carries its
#                           own traceability footer; re-exported here because
#                           this module is where SYSTEM-REC is bound and where
#                           an orchestrator looks for a binder.
#
# FINDINGS IN THE FROZEN MENUS  -  reproduced, never corrected (rule R-4)
#
#   F-A1  `overrewrite` CLOSES KEY 4, NOT KEY 1. `acas000` dispatches every
#         function on `File-Key-No` [common/acas000.cbl:L574-L600], and nothing
#         between the key-4 rewrite and the close resets the key
#         [general/general.cbl:L667-L670], [sales/sales.cbl:L639-L642],
#         [purchase/purchase.cbl:L632-L635]. So the paragraph opens the system
#         table under key 1 and closes the TOTALS table under key 4. The load's
#         close is different - `aa010-Get-System-Recs` leaves the key at 1 and so
#         closes key 1 [general/general.cbl:L408], [general/general.cbl:L460].
#         Both are transcribed as written.
#   F-A2  THE KEY IS SET TWICE IN A ROW at the head of `overrewrite`: `move 1 to
#         File-Key-No` immediately before `System-Open` and again immediately
#         after it [general/general.cbl:L659-L661]. Redundant, and kept.
#   F-A3  THE LOAD AND THE PERSIST DISAGREE ABOUT KEY ORDER. The load reads 4, 2,
#         1 [general/general.cbl:L402-L410]; the persist writes 1, 2, 4
#         [general/general.cbl:L661-L669]. Neither is changed to match the other.
#   F-A4  THE `File-System-Used NOT = zero` GATE ON THE RDB ARM CAN NEVER BE
#         DECIDED BY THE MENU ITSELF. It is a SYSTEM-REC column, zeroed before the
#         load [general/general.cbl:L399] and then overwritten by the key-1 read;
#         the only code that would have set it deliberately is commented out
#         [general/general.cbl:L428-L432]. Its value at `overrewrite` is whatever
#         the seed stored. See `overrewrite` for why the gate is therefore not
#         reproduced as a gate.
#   F-A5  `zz090` AND `zz095` DISAGREE ABOUT FIELD ORDER. `zz090` fills
#         `WS-First-Time-Flag` last [irs/irs.cbl:L965-L966]; `zz095` tests it
#         fifth of seven [irs/irs.cbl:L1023]. Each function follows its own
#         paragraph's order.
#   F-A6  `zz090`'s THREE DATE CONVERSIONS SHARE ONE `maps03-ws`, so a zero
#         Start-Date or End-Date yields the PREVIOUS conversion's text rather than
#         a blank - `maps04` unpacks only for a positive binary and leaves
#         `u-date` untouched on rejection [common/maps04.cbl:L146]. One
#         `Maps03Ws` is reused for all three so the carry-over survives.
#   F-A7  TWO OF `zz090`'s MOVES TRUNCATE: `Usera pic x(32)` into `suser pic
#         x(24)` and `Print-Spool-Name pic x(48)` into `pic x(32)`. Both go
#         through the MOVE layer with the receiving field's descriptor.
#
# CORRECTIONS  -  each verified against the frozen source with a line read. DO
# NOT "fix" these back to the values the planning documents carry.
#
#   1. WS-CD-Args is at copybooks/wscall.cob:L14, NOT L13, so the record block
#      is L6-L14 and not L6-L13 as Agent Action Plan section 0.4.1.1 cites. L13
#      is WS-Sub-Function and L11 is a comment line between L10 and L12. Every
#      citation in this module uses L6-L14.
#
#   2. The General Ledger abort is raised at general/gl070.cbl:L289
#      (`move 5 to ws-term-code`), inside the conditional at L287-L290. The plan
#      cites L288, which is `perform gl060a` - a report display, not the raise.
#   3. The Sales and Purchase shape has FIVE parameters, not the four section
#      0.4.1.1 calls it: sales/sales.cbl:L702-L706 passes five and the callee
#      declares five at sales/sl060.cbl:L395-L399, as does
#      purchase/purchase.cbl:L695-L699. `SlPlLinkage` has five members.

# OMISSIONS - recorded as omissions so a reader comparing the two trees does not
# conclude something was lost (Agent Action Plan section 0.4.3).
#   * ALL MENU SCREEN I/O, and the `go to load01 ... depending on z` dispatch
#     tables: no database effect, excluded by sections 0.2.2 and 0.3.4. An
#     `ACCEPT` that merely pauses is dropped; one that gates a database write
#     becomes an option on the individual entry point, never on this module.
#   * `pre-overrewrite`'s BACKUP SPOOL-OUT, and the backup arm of the IRS `EOJ.`
#     [irs/irs.cbl:L777-L791]. Both end in `call "SYSTEM"` and are excluded
#     twice, by section 0.2.2's spool-out exclusion and by rule R-1.
#     `overrewrite`'s SYSTEM-RECORD PERSISTENCE IS NO LONGER OMITTED - it is
#     reproduced by `overrewrite` and, on the IRS route, by
#     `eoj_persist_irs_system_data`. See Q-CLI-SYSREC-LOAD for why, and the
#     COBOL-FILE ARM bullet below for the one part of it that still is not.
#   * THE COBOL-FILE ARM OF EVERY LOAD AND EVERY PERSIST. Each menu drives its
#     ISAM parameter file first and the RDB second - the forced `"00"` at
#     [general/general.cbl:L401] and the unconditional block at
#     [general/general.cbl:L674-L691] - and the migration has no ISAM store at
#     all. Only the RDB arm has a counterpart. See
#     `RDBMS_STORE_SELECTOR_DIGIT`.
#   * `Default-Record`. general/general.cbl `load000.` L727-L737 looks like the
#     five-parameter shape but its THIRD argument is `default-record`
#     (L731-L732), not `WS-System-Record-4`. That paragraph serves gl020 and
#     gl050, both out of scope, so NO in-scope General Ledger route uses it and
#     this module deliberately binds no such record. `SlPlLinkage` is the only
#     five-member shape here, and its third member is `SYSTOT-REC`.
#
#   * `SYSTEM-REC` FIELDS BEYOND THE NINE BOUND. The record has 169 columns and
#     exactly nine are set here. Three are settable from argv and the clock -
#     Run-Date, Date-Form and IRS-Instead - and that list is closed: adding an
#     option for any other would add an input the COBOL menus do not offer
#     (rule R-3). Six more are filled from the deployment contract rather than
#     from argv - RDBMS-DB-Name, RDBMS-User, RDBMS-Passwd, RDBMS-Port,
#     RDBMS-Host and RDBMS-Socket [copybooks/wssystem.cob:L137-L144] - because
#     they are the only carrier by which a connection parameter reaches the
#     data-access layer [common/acas008.cbl:L558-L563] and because the frozen
#     load programs fill exactly these six in exactly this place
#     [common/glbatchLD.cbl:L262-L267]. They add no CLI option, so the settable
#     list is still two. Every other field keeps the record layer's declared
#     default.
#
#   * `MOVE` RECEIVING-FIELD SEMANTICS FOR THE ONE FIELD THIS MODULE STILL
#     ASSIGNS DIRECTLY. The seven `WS-Calling-Data` fields go through
#     `acas_posting/cobol/move.py`. `IRS-Instead` at `PIC X` does not - it is a
#     `SYSTEM-REC` field whose value is already confined by argparse `choices` -
#     and it is the one place where the consequence is visible rather than
#     theoretical: passing `--irs-instead ""` stores a zero-length string where a
#     COBOL `MOVE` would leave one space. The two are the same STATE -
#     `is_irs_used` and `is_irs_both_used` are both false for either, so the
#     fan-out reads off - and the sibling harness writes the empty form itself
#     [harness/run_cobol_scenario.sh:L1785-L1787], trimming a supplied space to it
#     [harness/run_cobol_scenario.sh:L1770]. Padding it here would apply `MOVE`
#     semantics to a record this module has declared it binds at its declared
#     defaults.
#
#   * THE FIVE PROMOTED CALLEE PARAMETERS. gl080's run-confirm, disk-change and
#     archive-path; gl051's control-total inputs; sl100's post-confirm; pl100's
#     run-confirm; irs030's clear-transfer-file decision. Each is an `ACCEPT`
#     that gates a database write and each becomes an option on its OWN entry
#     point, because each belongs to one route only. None is a linkage parameter
#     and none is bound here.
#
# `MOVE` RECEIVING-FIELD SEMANTICS  (Agent Action Plan section 0.1.2, rule 11)
# Applied, not omitted. Every one of the seven `WS-Calling-Data` fields is
# written through acas_posting.cobol.move.move with that field's own descriptor,
# taken from records.calling_data.descriptor_for so the picture is the generated
# dictionary's and no width is transcribed here:
#   WS-Called       pic x(8)   set_called
#   WS-Caller       pic x(8)   bind_calling_data
#   WS-Del-Link     pic x(8)   bind_calling_data
#   WS-Process-Func pic 9      bind_calling_data
#   WS-Sub-Function pic 9      bind_calling_data
#   WS-CD-Args      pic x(13)  bind_calling_data
#   WS-Term-Code    pic 99     reset_term_code
#
# The four remaining receiving fields this module writes need no widening, and
# each reason is a fact about the field rather than a judgement:
#   SYSTEM-REC Run-Date binary-long (copybooks/wssystem.cob:L67) takes the
#     pinned clock's `int`, which is a day count and carries no picture width.
#   SYSTEM-REC Date-Form pic 9 (copybooks/wssystem.cob:L128) takes either the
#     record's own declared default or one of the three values of
#     `88 Date-Valid-Formats` (copybooks/wssystem.cob:L132) - a single digit
#     either way, which is the field's whole capacity.
#   SYSTEM-REC IRS-Instead pic x (copybooks/wssystem.cob:L179) likewise takes
#     the declared default or one of "N", "Y", "B" - one character.
#   IRS-System-Params Run-Date pic x(8) (copybooks/irswssystem.cob:L14) is
#     filled by irs_run_date_x8, and the COBOL verb there is STRING, not MOVE
#     (irs/irs.cbl:L975-L978): a STRING overlays the receiver from its pointer
#     and does NOT space-fill the remainder, and the assembled text is exactly
#     6 + 2 = 8 characters, so the field is wholly overlaid.
#
# THE CONFIGURATION-FAILURE CONTRACT  ->  NO COBOL PARAGRAPH  (finding CLI-09)
#   RdbmsParamError               re-exported from cli/rdbms_params.py, so that
#                                 every route main and the package router catch
#                                 the EXACT type rather than `ValueError`.
#   report_configuration_failure  the one message-and-status contract over it.
#                                 The status is the frozen return code of
#                                 common/acas-get-params.cbl:L37-L42 - 8 for an
#                                 absent contract, 1 for an unusable one - because
#                                 the frozen loaders abandon with a bare `goback`
#                                 and no code of their own
#                                 [common/glbatchLD.cbl:L245-L259], so there is
#                                 nothing else to reproduce.
#
# THE PRELOADED-RECORD PARAMETERS  ->  THE MENU'S OWN `aa010` RESULT (CLI-02)
#   _bind_system_record(..., system_record=)      general/general.cbl:L410-L412
#   bind_gl_linkage(..., system_record=)          general/general.cbl:L399-L460
#   bind_slpl_linkage(..., system_record=,
#                          system_record_4=)      sales/sales.cbl:L355-L360,
#                                                 purchase/purchase.cbl:L350-L354
#   bind_irs_linkage(..., system_record=,
#                         irs_system_params=)     irs/irs.cbl:L511-L512 and
#                                                 `zz090` L907-L997
#   Each defaults to None, which keeps the declared-default behaviour, so no
#   existing caller changes meaning and the arithmetic tier still needs no
#   database.
#   A SUPPLIED INSTANCE IS THE INSTANCE (finding F4 of the B2 review). COBOL
#   passes a group item BY REFERENCE, and a menu shell holds exactly ONE
#   `01 SYSTEM-REC` that its load fills [general/general.cbl:L411], its `CALL`
#   hands over [general/general.cbl:L715-L718] and its `overrewrite` writes back
#   [general/general.cbl:L662-L663]. So `_bind_system_record` mutates and returns
#   the record it is handed and builds one only when handed None, and both public
#   binders forward the argument rather than shadowing it. `bind_slpl_linkage`
#   resolves `SYSTOT-REC` in the order explicit argument, then
#   `menu_state.system_record_4`, then a declared default - the menu's own record
#   being what the nine period-total writes mutate and what `overrewrite`
#   rewrites under key 4. `bind_irs_linkage` still builds both of its records, as
#   its own docstring states and as [irs/irs.cbl:L934-L968] does.
#
# THE KEY-1 GATE  ->  THE ONE REPLY EVERY MENU TESTS  (finding F2 of the B2 review)
#   aa010_get_system_recs reproduces `if fs-reply not = zero` and the `perform
#   System-close` beside it, in that order, and captures the reply from the read's
#   own return value so the close cannot overwrite the value the test needs:
#     general/general.cbl:L412-L413    entity-named, keys 4-2-1
#     sales/sales.cbl:L361-L362        entity-named, keys 4-1
#     purchase/purchase.cbl:L355-L356  entity-named, keys 4-1
#     irs/irs.cbl:L513-L514            handler-named, key 1 only
#   NOT reproduced: `call "sys002"` and the `go to aa010-Get-System-Recs` after it
#   [general/general.cbl:L414-L417] - an interactive record-creation dialog, out of
#   scope by name (Agent Action Plan section 0.2.2), so the loop it heads cannot be
#   entered. What IS reproduced is the frozen DISPOSITION: the paragraph is never
#   left with a bad reply, so nothing is dispatched and nothing is written.
#   `SystemRecordUnavailableError` carries it, and the frozen menu reaches the same
#   end by its own second route when `sys002` reports a serious code -
#   `stop run` [general/general.cbl:L630-L631]. Keys 4 and 2 are NOT tested,
#   because no menu tests them (rule R-4).
#
# THE TWO VERB VOCABULARIES  ->  ONE LOAD  (finding F3 of the B2 review)
#   Agent Action Plan section 0.3.3 gives the facade both name sets and section
#   0.6.5 records that the difference is behavioural, so the load selects per menu
#   through `MenuState.handler_named_verbs`:
#     _ENTITY_NAMED_SYSTEM_VERBS   copybooks/Proc-ACAS-FH-Calls.cob
#         System-Open-Input   L197-L202   general/general.cbl:L390
#         System-Read-Indexed L217-L220   general/general.cbl:L403, L407, L411
#         System-Close        L211-L215   general/general.cbl:L413, L460
#         No verb in that copybook carries an error check; its callers test the
#         reply inline, which is what the gate above does.
#     _HANDLER_NAMED_SYSTEM_VERBS  copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob
#         acas000-Open-Input   L98-L102   irs/irs.cbl:L499
#         acas000-Read-Indexed L114-L117  irs/irs.cbl:L512
#         acas000-Close        L104-L107  irs/irs.cbl:L514
#         The open family performs acas000-Check-4-Errors L320-L325, reaching
#         Open-Error-Continued L355-L364 and its `goback`, which the facade raises
#         as FacadeGoback and acas_posting/cli/irs_post.py absorbs at the menu
#         program's boundary. acas000-Open-Input performs that check BEFORE the
#         dispatch - alone among all 42 verb paragraphs - and the facade reproduces
#         the ordering rather than straightening it. The dispatch paragraph also
#         pins File-Key-No to 1 [:L22-L29]; harmless here because the one menu that
#         selects this set reads key 1 alone.
#   `eoj_persist_irs_system_data` names the handler-named verbs directly rather
#   than through the selector, because it reproduces one paragraph of one menu -
#   `EOJ.` [irs/irs.cbl:L755-L775] - and `overrewrite` names the entity-named ones
#   for the same reason.
#
# AMBIGUITIES RAISED BY THIS MODULE  (rule R-6)  -  three, each marked in place
# at the code it governs. TWO ARE NOW SETTLED, and each is settled at its own
# site with the evidence that settles it, because that is where a reader meets
# the decision:
#
#   Q-CLI-SYSREC-LOAD  in _bind_system_record  -  SETTLED, AND SETTLED THE OTHER
#     WAY FROM AN EARLIER READING. The census stands: not one of the twelve
#     in-scope posting programs performs any system-record or totals-record I/O,
#     so the load and the persist belong to the MENU. What changed is where the
#     menu's counterpart lives. Section 0.4.1.1 derives each CLI entry point FROM
#     a menu paragraph, section 0.3.4 drops only PRESENTATION from a menu, and
#     section 0.8.5 makes an empty diff on the affected tables the acceptance
#     test - and SYSTOT-REC is affected, with `overrewrite` as its only writer to
#     the store. So the route is the menu's counterpart and the route loads and
#     persists. Section 0.4.3's import table bars this layer from `dal.acas*`,
#     not from `dal.facade`, so it is reachable from here. Two consequences are
#     recorded rather than hidden: the ISAM arm of both paragraphs has no
#     counterpart (see OMISSIONS), and the pins are re-applied over the loaded
#     row (see Q-CLI-SYSREC-PINS).
#
#   Q-CLI-SYSREC-PINS  in _bind_system_record  -  OPEN. After the load, the six
#     connection fields and the three pinned fields are written over whatever the
#     row held. For the connection fields that is forced - `ba010-Initialise`
#     copies them out of this record into the connection, so the row's
#     placeholders would BECOME the connection. For Run-Date, Date-Form and
#     IRS-Instead it means the CLI wins over the row, so a scenario must seed
#     those three columns to agree with the options it passes.
#
#   Q-CLI-SYSREC-RUNDATE  in aa010_get_system_recs  -  OPEN. The frozen menus
#     derive `to-day` FROM the loaded row [general/general.cbl:L465-L467], and a
#     census shows the row's RUN-DATE is written once, at record-creation time, by
#     the out-of-scope `common/sys002.cbl` through
#     [copybooks/Proc-ACAS-Mapser-RDB.cob:L80] - no menu ever writes it. The
#     controlled clock replaces that creator, as sections 0.1.1 and 0.8.1 require.
#
#   Q-CLI-EXITSTATUS   in exit_status_for  -  SETTLED by establishing that THERE
#     IS NO ORACLE OBSERVABLE. `RETURN-CODE`, the one register GnuCOBOL surfaces
#     as a process status, is READ and never WRITTEN anywhere in the five menus or
#     the twelve posting programs, and each menu ends with a bare `goback`. The
#     identity mapping is therefore a boundary decision under section 0.3.4, taken
#     on the ground that it is total and lossless over the `pic 99` domain.
#
#   Q-CLI-RUNDATE-VS-ROW  in aa010_get_system_recs  -  STILL OPEN. The frozen
#     menus derive the TEXT date from the row they have just read
#     [general/general.cbl:L466-L468] and never write `RUN-DATE` back - the only
#     writes to it anywhere in the five menus are into `u-bin` and into the IRS
#     `pic x(8)` field - so a scenario must pin `--run-date` to the seeded
#     `RUN-DATE` for the two cycles to be comparable at all. Nothing provisional
#     executes: the pinned value is the observable Agent Action Plan section 0.1.1
#     requires, and re-applying it after the read is what keeps the twelve
#     programs on one date.
#
#   Q-CLI-OVERREWRITE-SECOND-LEG  in overrewrite  -  STILL OPEN, with the
#     migration's position stated and its ground given. The omitted Cobol half
#     zeroes `File-System-Used` and never restores it, which under a literal
#     reading puts a second dispatch in the same session on the indexed leg. The
#     migration has no indexed leg and section 0.8.5 mandates a Sales scenario
#     that is two dispatches, so the half is omitted whole and the relational leg
#     persists. Measure which leg the oracle's second dispatch takes.
#
#   Q-CLI-IRS-RUNDATE  in bind_irs_linkage  -  STILL OPEN, and deliberately so.
#     Nothing provisional executes at that site: the statement reproduces
#     `zz090-Proc-Run-Date.` [irs/irs.cbl:L972-L978], which the menu performs
#     before every option whether or not irs030 reads the field, so the open
#     question cannot change it. It remains marked for the record.
#
# RULES  (no user rules document exists for this project; these are the Agent
# Action Plan's own six, section 0.7.2)
#   R-1  satisfied structurally: the imports of this module are argparse, typing
#        and fifteen modules of this package - one of which is `dal.facade`, the
#        data-access layer's published seam and the same one the twelve program
#        modules use. No child process, no foreign-function interface, no
#        toolchain lookup, and no option that reaches the compiled comparison
#        oracle.
#   R-2  satisfied by type: WS-Term-Code and Run-Date are `int`, to-day and the
#        IRS run-date are `str`. No binary-radix numeric type appears in any
#        signature, option type or expression.
#   R-3  satisfied by omission: no run-date validation, no added record field, no
#        DDL, no schema access, and no concurrency of any kind. The only option
#        domains declared are the fields' own - `pic 9` gives 0-9 and
#        `88 Date-Valid-Formats` gives 1, 2, 3. The four acas000 paragraphs this
#        module reproduces DO reach SQL, through `dal.facade` and only through
#        the verbs the frozen paragraphs perform; no statement is issued that a
#        menu paragraph does not issue, and no verb is added. The ONE reply this
#        module tests is the one all four menus test at
#        [general/general.cbl:L412] and its three siblings, so it is a
#        transcription and not an added check - and the alternative, continuing
#        with a declared-default `SYSTEM-REC`, would be the added behaviour.
#   R-4  reproductions, each carrying its locator at the site: WS-CD-Args
#        defaulting to spaces because no menu assigns it
#        (copybooks/wscall.cob:L14); WS-Term-Code cleared before every dispatch
#        (general/general.cbl:L714); the `> 7` and `< 8` bands left as the two
#        disjoint tests the menus make; and a rejected run date yielding
#        Run-Date 0 rather than an exception (common/maps04.cbl:L146 with
#        copybooks/Proc-ACAS-Mapser-RDB.cob:L78).
#   R-5  this footer, plus the per-symbol locators throughout.
#   R-6  the clock is injected and `--run-date` is required on every route that
#        needs a date; the three open questions above are marked, not guessed.
# -----------------------------------------------------------------------------
