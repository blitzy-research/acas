"""argv to `WS-Calling-Data`: the one place the CLI binds the COBOL linkage.

`acas_posting.cli.args` owns exactly two things and nothing else:

  1. the binding of command-line arguments to `01 WS-Calling-Data`
     [copybooks/wscall.cob:L6-L14] and to the system records that the three
     COBOL call shapes pass alongside it; and
  2. the controlled-clock injection point - the one boundary at which a run
     date enters the migrated cycle (rule R-6).

Agent Action Plan section 0.4.1.1 gives this module its whole mandate, source
`copybooks/wscall.cob`:

    "Binds argv to `WS-Calling-Data` - `WS-Called`, `WS-Caller`, `WS-Del-Link`,
    `WS-Term-Code`, `WS-Process-Func`, `WS-Sub-Function`, `WS-CD-Args` - plus
    `to-day` and the system records; the block was designed for unattended
    invocation, so this is a faithful binding rather than an invention."

That closing clause is the point. `WS-CD-Args` carries the maintainer's own
explanation at [copybooks/wscall.cob:L1-L3]: it exists "for passing extra info
to called process that will help in a cron call by time via menu program.
picked by position within WS-Args." The unattended-invocation contract is
therefore already written into the copybook; nothing here invents a CLI.

Every sibling entry point of this package imports these definitions and none
re-implements them. `acas_posting/__main__.py` in particular reuses the shared
option definitions from here and does not redefine the `WS-Calling-Data`
binding.

THE SOURCE LAYOUT, VERIFIED AGAINST THE FROZEN COPYBOOK
=======================================================
`copybooks/wscall.cob` is 16 lines long. Its whole record is::

    L6      01  WS-Calling-Data.
    L7          03  WS-Called       pic x(8).
    L8          03  WS-Caller       pic x(8).
    L9          03  WS-Del-Link     pic x(8).
    L10         03  WS-Term-Code    pic 99.
    L11     *>                                 new 18/5/13
    L12         03  WS-Process-Func pic 9.
    L13         03  WS-Sub-Function pic 9.
    L14         03  WS-CD-Args      pic x(13).    *> Changed / Added 14/03/18

Seven fields, 41 bytes. The record layer models them as
`acas_posting.records.calling_data.WsCallingData`; this module only fills it.

`WS-Term-Code` IS `pic 99` - AN UNSIGNED TWO-DIGIT INTEGER
==========================================================
[copybooks/wscall.cob:L10], widened from `pic 9` by the maintainer's own change
note at [copybooks/wscall.cob:L4]: "14/11/25 vbc - 1.02 - Chg WS-Term-Code from
9 to 99." Its domain is therefore 0 through 99 inclusive, and that single fact
is load-bearing for every entry point in this package:

  * the two predicates the menus test, `ws-term-code < 8` (e.g.
    [sales/sales.cbl:L686], [sales/sales.cbl:L708]) and `ws-term-code > 7`
    (e.g. [general/general.cbl:L720]), are EXHAUSTIVE and MUTUALLY EXCLUSIVE
    over that whole domain. There is no third band, no negative case and no
    "unset" case to handle, so `is_serious_error` below is a total predicate
    and its complement needs no separate helper; and
  * every value it can hold is already a legal process exit status, because 99
    is well inside the 0-255 range a POSIX wait status carries. That is why
    `exit_status_for` can be the identity rather than a lossy mapping.

THE THREE LINKAGE SHAPES - THREE ARGUMENT SHAPES, NOT ONE
=========================================================
Agent Action Plan section 0.1.1: "The CLI contract is already written, in the
LINKAGE SECTIONs." None of the twelve migrated programs is a main program; each
is a `CALL`ed sub-program with a fixed parameter list, and there are exactly
three distinct shapes. The carriers below hold them in COBOL parameter order so
that a reviewer can diff the argument lists side by side:

  Shape 1 - General Ledger, FOUR parameters -> `GlLinkage`
      ws-calling-data, system-record, to-day, file-defs
      dispatched by general/general.cbl `load00.` L711-L723, whose `CALL` runs
      L715-L719 (parameter list L715-L718, `end-call` at L719); callee
      signature [general/gl070.cbl:L245-L248].

  Shape 2 - Sales and Purchase, FIVE parameters -> `SlPlLinkage`
      ws-calling-data, System-Record, WS-System-Record-4, to-day, file-defs
      dispatched by sales/sales.cbl `load000.` L698-L714 (`CALL` at
      L702-L707) and purchase/purchase.cbl `load000.` L691-L706 (`CALL` at
      L695-L700); callee signature [sales/sl060.cbl:L395-L399], which names its
      third parameter `system-record-4`. FIVE, not four - see CORRECTION 3 in
      the footer.

  Shape 3 - IRS, THREE parameters -> `IrsLinkage`
      IRS-System-Params, WS-System-Record, file-defs
      dispatched inline from irs/irs.cbl `Main-Loop.` at L666-L671 (`CALL` at
      L668-L671, the second argument carrying the maintainer's own comment
      `*> ACAS system rec.` at L669); callee signature
      [irs/irs030.cbl:L552-L554]. Materially different from the other two: NO
      calling-data block and NO `to-day`. See section "THE IRS ROUTE" below.

THE CONTROLLED CLOCK STOPS HERE  (rule R-6)
===========================================
Agent Action Plan section 0.1.1, verbatim:

    "the controlled clock needs to pin exactly two observables - the text date
    `to-day pic x(10)` in DD/MM/CCYY form, and the binary `Run-Date`
    [copybooks/wssystem.cob:L67] - and inject them at the CLI boundary. No
    clock abstraction is needed inside the migrated programs at all."

All twelve in-scope posting programs contain zero clock reads; the date reaches
them purely through linkage. The one clock read in the entire call chain lives
in the menu shells' date-service copybook at
[copybooks/Proc-ACAS-Mapser-RDB.cob:L72-L80]::

    L72   move     function current-date to wse-date-block.
    L73   move     "00/00/0000" to u-date.
    L74   move     wse-year  to u-year.
    L75   move     wse-month to u-month.
    L76   move     wse-days  to u-days.
    L77   move     u-date    to to-day.        <- observable 1, pic x(10)
    L78   move     zero      to u-bin.         <- the caller pre-zero
    L79   call     "maps04" using maps03-ws.
    L80   move     u-bin  to run-date.         <- observable 2, binary-long

This module plus `acas_posting/clock.py` are therefore the sole injection
point, and the injection is by ARGUMENT: `--run-date` is REQUIRED on every
route that needs a date, with no default of any kind. Nothing here reads a
system clock, an elapsed-time counter, a process environment variable, a host
name or an entropy source, so two runs of one scenario are byte-identical -
which is what Agent Action Plan section 0.8.5 demands.

A MALFORMED `--run-date` IS NOT REJECTED HERE  (rules R-3 and R-4)
==================================================================
`resolve_clock` hands the text straight to `acas_posting.clock`, which hands it
to the migrated `maps04`. That program judges it with its own six-part test
[common/maps04.cbl:L140-L146] and its own calendar check
[common/maps04.cbl:L153], and on rejection falls through leaving its output
field untouched [common/maps04.cbl:L146], [common/maps04.cbl:L154] - so the
caller pre-zero at [copybooks/Proc-ACAS-Mapser-RDB.cob:L78] is what makes a
rejected date come back as `Run-Date = 0` rather than as stale content. That is
anomaly 16 of the register, reproduced rather than corrected.

So "31/02/2025" yields a pinned pair whose `run_date` is 0 and DOES NOT RAISE.
Validating the text here would add a validation the COBOL does not perform
(forbidden by R-3) and would correct legacy behaviour (forbidden by R-4).

THE IRS ROUTE - WHY IT TAKES `--run-date` AND NO CALLING-DATA OPTIONS
====================================================================
Shape 3 has no calling-data block and no `to-day` parameter, so
`add_irs_linkage_arguments` adds NONE of the calling-data options and
`bind_irs_linkage` builds a carrier of exactly three members. But the route
still needs the pinned clock, for two fields that are unambiguously present:

  1. `WS-System-Record.Run-Date` - `binary-long`
     [copybooks/wssystem.cob:L67]. The ACAS system record IS the second
     linkage argument [irs/irs.cbl:L669], so this field must be pinned. Not
     ambiguous.
  2. `IRS-System-Params.Run-Date` - `pic x(8)`
     [copybooks/irswssystem.cob:L14]. irs/irs.cbl always populates it through
     `zz090-Proc-Run-Date.` [irs/irs.cbl:L972-L978] before any menu option
     runs, and [irs/irs.cbl:L636] carries the maintainer's note that the "menu
     uses the irs param file dates". `irs_run_date_x8` reproduces that
     conversion. Whether irs030 observes the field at all is the open question
     recorded as Q-CLI-IRS-RUNDATE.

Without `--run-date` this module would have to read a live clock (forbidden by
R-6) or leave both fields unpinned (a behaviour change, forbidden by R-3 and
R-4). Requiring it is the only compliant option.

WHAT THIS MODULE MAY AND MAY NOT IMPORT
=======================================
MAY, and does: the standard library, `acas_posting.clock`, and the five record
modules whose dataclasses the three shapes are built from. This is the ONE
module of `acas_posting/cli/` permitted to import the record layer, precisely
because section 0.4.1.1 assigns it the job of binding "the system records"; the
other eight modules of this package construct their linkage through here.

MAY NOT, and does not: the program layer, the data-access layer including its
facade, the COBOL-semantics package, the dictionary package and the work-file
module. Two consequences worth stating because they look like omissions:

  * `MOVE` receiving-field truncation, space padding and justification are NOT
    performed here. They belong to `acas_posting/cobol/move.py`, which this
    layer may not reach, so a value is assigned as supplied and the record
    layer's own declared field semantics govern it. Recorded as an omission in
    the footer.
  * the system records are built at their DECLARED DEFAULTS with only the
    three pinnable fields set, because loading them from the store would need
    the data-access layer. Recorded as Q-CLI-SYSREC-LOAD.

NO IMPORT-TIME SIDE EFFECTS
===========================
Importing this module binds names and evaluates a handful of pure in-memory
dataclass constructions, and has no other observable effect. It builds no
parser, configures no logging, opens no file, connection or directory, reads
nothing from its surroundings, starts nothing, and cannot fail for an
environmental reason. That is a hard requirement rather than a preference: the
scenario test suites import this package, and a module that did work at import
would make their arithmetic tier's "runs anywhere" promise untrue.

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
    to configure and no option that would create one.
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
from typing import Final, NamedTuple

from acas_posting import clock
from acas_posting.records.calling_data import WsCallingData
from acas_posting.records.file_defs import FileDefs
from acas_posting.records.irs_system import IrsSystemParams
from acas_posting.records.system_record import SystemRecord
from acas_posting.records.system_record_4 import SystemRecord4

__all__: Final[tuple[str, ...]] = (
    # ---- the documented argument form -------------------------------------
    "RUN_DATE_FORMAT",
    # ---- verified COBOL defaults, one per menu shell -----------------------
    "WS_CALLER_GENERAL",
    "WS_CALLER_SALES",
    "WS_CALLER_PURCHASE",
    "WS_CALLER_ACAS",
    "WS_DEL_LINK_DEFAULT",
    "WS_PROCESS_FUNC_DEFAULT",
    "WS_SUB_FUNCTION_DEFAULT",
    "WS_CD_ARGS_DEFAULT",
    "WS_TERM_CODE_DEFAULT",
    # ---- behavioural constants the seven entry points share ---------------
    "GL_ABORT_TERM_CODE",
    "EXTRACT_MISSING_FILE_TERM_CODE",
    "SERIOUS_ERROR_THRESHOLD",
    # ---- the three linkage shapes, in COBOL parameter order ---------------
    "GlLinkage",
    "SlPlLinkage",
    "IrsLinkage",
    # ---- argparse fragments, one per route shape --------------------------
    "add_calling_data_arguments",
    "add_gl_linkage_arguments",
    "add_slpl_linkage_arguments",
    "add_irs_linkage_arguments",
    # ---- binders ----------------------------------------------------------
    "bind_calling_data",
    "bind_gl_linkage",
    "bind_slpl_linkage",
    "bind_irs_linkage",
    "resolve_clock",
    # ---- faithful one-statement helpers -----------------------------------
    "reset_term_code",
    "set_called",
    "is_serious_error",
    "exit_status_for",
    "irs_run_date_x8",
)


# =============================================================================
#  DEFAULTS THAT ARE READ FROM THE RECORD LAYER, NEVER TRANSCRIBED BY EYE
# =============================================================================
#  Agent Action Plan section 0.8.1 makes "data dictionary first" a directive
#  rather than a preference: "every Python field definition cites its entry.
#  This ordering is a directive, not a preference - it is what prevents fields
#  being transcribed by eye." A hand-typed `" " * 8` would be exactly that
#  transcription, and it would silently rot if a picture clause ever moved.
#
#  So the space-filled and zero defaults below are READ OUT of the record
#  layer's own declared defaults, which the record modules in turn derive from
#  the generated data dictionary. The helpers construct a throwaway record and
#  read one attribute from it: pure in-memory work, no file, no connection, no
#  environment, so importing this module stays free of side effects.


def _declared_calling_data() -> WsCallingData:
    """Return a fresh `WS-Calling-Data` holding only its declared defaults.

    A brand-new instance each call, so nothing in this module holds shared
    mutable state at module scope and no later mutation can reach the constants
    derived below. Attribute access on the result is typed by the record's own
    annotations, which is why the constants need no cast.

    Returns:
        A `WsCallingData` whose seven fields carry exactly what the record layer
        declares: space-filled at each alphanumeric field's own `PIC X(n)` width
        and zero for the three numeric ones - which is precisely the state the
        menu shells establish before a dispatch.
    """
    return WsCallingData()


def _declared_system_record() -> SystemRecord:
    """Return a fresh `SYSTEM-REC` holding only its declared defaults.

    Same reasoning as `_declared_calling_data`. Constructing the 169-column
    record is pure in-memory work - a nest of dataclass default factories, no
    file, no connection and nothing read from the surroundings - so it is safe
    to do at import and costs nothing worth optimising.

    Returns:
        A `SystemRecord` at its declared defaults. Nothing is loaded from the
        store: see Q-CLI-SYSREC-LOAD.
    """
    return SystemRecord()


# =============================================================================
#  CONSTANTS  (section 8.1 of this module's brief)
# =============================================================================

#  The documented form of the `--run-date` argument. `to-day` is declared
#  `01 to-day pic x(10).` in each menu shell - [general/general.cbl:L357],
#  [sales/sales.cbl:L309], [purchase/purchase.cbl:L304], [irs/irs.cbl:L405] -
#  and the date-service copybook seeds it "00/00/0000" before filling in the
#  year, month and day [copybooks/Proc-ACAS-Mapser-RDB.cob:L73-L76], which is
#  what fixes the field order as day, month, century-year.
#
#  Separators other than "/" are accepted, because the migrated `maps04`
#  normalises ".", "," and "-" to "/" itself [common/maps04.cbl:L132-L134].
#  That is legacy tolerance faithfully carried over, not a convenience added
#  here, and it is why this constant names the CANONICAL form rather than the
#  only accepted one.
RUN_DATE_FORMAT: Final[str] = "DD/MM/CCYY"

#  `WS-Caller` - the dispatching menu's own identity. One constant per menu
#  shell, each the literal the shell moves into the field.
WS_CALLER_GENERAL: Final[str] = "general"  # general/general.cbl:L512
WS_CALLER_SALES: Final[str] = "sales"  # sales/sales.cbl:L481, also L465
WS_CALLER_PURCHASE: Final[str] = "purchase"  # purchase/purchase.cbl:L475, also L459
#  The top-level system-selection menu, which dispatches the four ledger menus
#  rather than any posting program. Published because the package's own router
#  mirrors that menu (Agent Action Plan section 0.4.1.1), and deliberately NOT
#  mapped to by `_menu_caller_for` below: no in-scope posting program is ever
#  called with this caller.
WS_CALLER_ACAS: Final[str] = "ACAS"  # common/ACAS.cbl:L431

#  `WS-Del-Link pic x(8)` [copybooks/wscall.cob:L9] - spaces. Every menu shell
#  clears it in the same statement that clears `WS-Called`:
#  `move spaces to ws-called ws-del-link menu-reply` at
#  [general/general.cbl:L513], [sales/sales.cbl:L482],
#  [purchase/purchase.cbl:L476] and [common/ACAS.cbl:L432]; and the Sales and
#  Purchase pre-run blocks clear it on its own at [sales/sales.cbl:L467] and
#  [purchase/purchase.cbl:L461].
WS_DEL_LINK_DEFAULT: Final[str] = _declared_calling_data().ws_del_link

#  `WS-Process-Func pic 9` [copybooks/wscall.cob:L12] and
#  `WS-Sub-Function pic 9` [copybooks/wscall.cob:L13] - both zero, cleared
#  together in one statement immediately before the menu is drawn:
#  `move zeros to ws-Process-Func ws-Sub-Function` at
#  [general/general.cbl:L505], [sales/sales.cbl:L474] and
#  [purchase/purchase.cbl:L468]; and set individually in the pre-run blocks at
#  [sales/sales.cbl:L468-L469] and [purchase/purchase.cbl:L462-L463].
WS_PROCESS_FUNC_DEFAULT: Final[int] = _declared_calling_data().ws_process_func
WS_SUB_FUNCTION_DEFAULT: Final[int] = _declared_calling_data().ws_sub_function

#  ANOMALY, REPRODUCED  (rule R-4)
#  `WS-CD-Args pic x(13)` [copybooks/wscall.cob:L14] - spaces, because NO menu
#  shell ever assigns it. A census of all four ledger menus and the top-level
#  menu finds only READS of the field, never a write: the Sales and Purchase
#  shells test `WS-CD-Args (1:5) = "xl150"` to decide whether to run the
#  end-of-cycle driver before the menu appears [sales/sales.cbl:L463],
#  [purchase/purchase.cbl:L457]. So the maintainer designed the field for a
#  cron caller to fill in [copybooks/wscall.cob:L1-L3] and then left every
#  in-repository caller passing spaces, which means the pre-run branch is dead
#  code under menu dispatch. Spaces is faithful; inventing a value or deriving
#  one would not be.
WS_CD_ARGS_DEFAULT: Final[str] = _declared_calling_data().ws_cd_args

#  REPRODUCED  (rule R-4)
#  `WS-Term-Code pic 99` [copybooks/wscall.cob:L10] - zero, and RESET
#  IMMEDIATELY BEFORE EVERY `CALL`, not once per run:
#  [general/general.cbl:L714] and [general/general.cbl:L730],
#  [sales/sales.cbl:L680] and [sales/sales.cbl:L701],
#  [purchase/purchase.cbl:L673] and [purchase/purchase.cbl:L694],
#  [common/ACAS.cbl:L576]. `reset_term_code` is the helper that reproduces it.
WS_TERM_CODE_DEFAULT: Final[int] = _declared_calling_data().ws_term_code

#  The General Ledger abort code. `gl070` raises it when Phase 1 finds a batch
#  left open - the conditional is [general/gl070.cbl:L287-L290] and the raise
#  itself is `move 5 to ws-term-code` at [general/gl070.cbl:L289] - and the
#  menu tests it at [general/general.cbl:L810-L811], returning to the menu
#  instead of continuing. The effect is that `gl071` and `gl072` NEVER RUN AT
#  ALL, so the posting-cycle entry point must treat this as a HARD GATE between
#  phases and never as a warning (Agent Action Plan section 0.6.4).
#
#  See CORRECTION 2 in the footer: the raise is at L289, not L288.
GL_ABORT_TERM_CODE: Final[int] = 5

#  Raised by the two extract programs when a file they need is missing, each
#  followed immediately by `goback`: [sales/sl055.cbl:L344-L345] and
#  [purchase/pl055.cbl:L286-L287]. Being 8 it is `> 7`, so it is also a serious
#  error by the predicate below - which is exactly why the Sales `load000.`
#  path performs `overrewrite` and then `goback` [sales/sales.cbl:L710-L712]
#  rather than merely returning to the menu.
EXTRACT_MISSING_FILE_TERM_CODE: Final[int] = 8

#  REPRODUCED  (rule R-4)
#  The `> 7` boundary - "Got a serious (reported) error", in the maintainer's
#  own words at [sales/sales.cbl:L691]. Tested at [general/general.cbl:L720],
#  [general/general.cbl:L735], [sales/sales.cbl:L691] and
#  [sales/sales.cbl:L710], [purchase/purchase.cbl:L684] and
#  [purchase/purchase.cbl:L703], and [common/ACAS.cbl:L578].
#
#  Expressed as the threshold rather than as `>= 8` so that the source reads
#  the way the COBOL does; because `WS-Term-Code` is `pic 99` the two are the
#  same predicate over the whole domain.
SERIOUS_ERROR_THRESHOLD: Final[int] = 7

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
#  `88 Date-Intl value 3` [copybooks/wssystem.cob:L131]. The copybook also
#  declares `88 Date-Valid-Formats values 1 2 3` at
#  [copybooks/wssystem.cob:L132], which is the source of these three choices.
_DATE_FORM_CHOICES: Final[tuple[int, ...]] = (1, 2, 3)

#  The record's OWN declared default, read rather than typed. It is zero, and
#  zero is deliberately absent from `_DATE_FORM_CHOICES` above: the COBOL field
#  can hold zero and `Date-Valid-Formats` is then simply false, so admitting
#  zero as a fourth command-line value would invent an accepted input, while
#  refusing zero as the default would invent a validation - both forbidden by
#  R-3. argparse checks `choices` only against a value actually supplied on the
#  command line, never against the default, so the two coexist exactly as the
#  copybook has them.
_DATE_FORM_DEFAULT: Final[int] = _declared_system_record().system_data_block.date_form

#  The IRS fan-out switch: `05 IRS-Instead pic x.`
#  [copybooks/wssystem.cob:L179] with `88 IRS-Used value "Y"`
#  [copybooks/wssystem.cob:L180] and `88 IRS-Both-Used value "B"`
#  [copybooks/wssystem.cob:L181] - "IRS instead of" and "IRS as well as". "N"
#  is the third state: not a condition name, just any value that satisfies
#  neither, which is what the field holds when the fan-out is off.
_IRS_INSTEAD_CHOICES: Final[tuple[str, ...]] = ("N", "Y", "B")

#  Again the record's own declared default, a single space - the same "neither"
#  state as "N" and, like `_DATE_FORM_DEFAULT`, deliberately outside the
#  choices for the same R-3 reason.
_IRS_INSTEAD_DEFAULT: Final[str] = (
    _declared_system_record().general_ledger_block.irs_instead
)


# =============================================================================
#  THE THREE LINKAGE CARRIERS  (section 8.2 of this module's brief)
# =============================================================================
#  Each carrier holds one COBOL call shape's arguments IN THE COBOL PARAMETER
#  ORDER, so that a call site reads the way a `CALL ... USING` reads and a
#  reviewer can diff the two argument lists line by line::
#
#      link = args.bind_gl_linkage(ns, called="gl070")
#      gl070_transaction_pre_process.run(*link)
#
#  WHY `NamedTuple` AND NOT A FROZEN DATACLASS
#  -------------------------------------------
#  This module's brief allows either. `NamedTuple` is chosen because it gives
#  all three properties the shape needs at once and adds nothing:
#
#    * IMMUTABLE by construction, so a bound shape cannot be re-pointed at a
#      different record halfway through a run;
#    * SPLATS NATIVELY with `*link`, so the parameter order is enforced by the
#      call itself rather than by a convention a caller has to remember, and an
#      arity mistake is a `TypeError` at the call site;
#    * HOLDS ITS MEMBERS BY REFERENCE, which is what COBOL linkage is.
#
#  THE CARRIER IS FROZEN; THE RECORD INSIDE IT IS NOT  (rule R-4)
#  --------------------------------------------------------------
#  COBOL passes a group item BY REFERENCE, so a called program writes into the
#  CALLER's storage. `WS-Term-Code` is the case that matters and it is
#  load-bearing: `gl070` SETS it to 5 on finding a batch left open
#  [general/gl070.cbl:L289], the menu READS it [general/general.cbl:L810-L811],
#  and the consequence is that `gl071` and `gl072` never run at all.
#
#  So `calling_data` is deliberately a MUTABLE `WsCallingData` instance held
#  inside an immutable carrier. Freezing the record instead would force the
#  callee to hand back a replacement, which is not what the COBOL does and
#  would leave the caller's copy stale - the write-back would be lost and the
#  abort gate would silently stop working. The same reasoning applies to
#  `system_record`, `system_record_4` and `irs_system_params`: the menus expect
#  a callee to have updated them, which is exactly why they persist them
#  afterwards in `overrewrite`.


class GlLinkage(NamedTuple):
    """Shape 1 - the General Ledger call shape, FOUR parameters.

    `procedure division using ws-calling-data, system-record, to-day,
    file-defs` [general/gl070.cbl:L245-L248], dispatched by
    general/general.cbl `load00.` L711-L723 whose `CALL` parameter list is
    L715-L718. Serves `gl070`, `gl071`, `gl072` and `gl080`.

    Attributes:
        calling_data: `01 WS-Calling-Data` [copybooks/wscall.cob:L6-L14].
            MUTABLE ON PURPOSE - the callee writes `WS-Term-Code` back into it.
        system_record: `SYSTEM-REC`, the 169-column system record, carrying the
            pinned `Run-Date` [copybooks/wssystem.cob:L67].
        to_day: `to-day pic x(10)` in DD/MM/CCYY form - the THIRD argument, and
            a linkage parameter rather than a column.
        file_defs: `01 File-Defs.` [copybooks/wsnames.cob:L13], the file-name
            buffers, including the two `gl071` work-file names at
            [copybooks/wsnames.cob:L15-L16].
    """

    calling_data: WsCallingData
    system_record: SystemRecord
    to_day: str
    file_defs: FileDefs


class SlPlLinkage(NamedTuple):
    """Shape 2 - the Sales and Purchase call shape, FIVE parameters.

    `procedure division using ws-calling-data, system-record, system-record-4,
    to-day, file-defs` [sales/sl060.cbl:L395-L399], dispatched by
    sales/sales.cbl `load000.` (`CALL` at L702-L707) and purchase/purchase.cbl
    `load000.` (`CALL` at L695-L700). Serves `sl055`, `sl060`, `sl100`,
    `pl055`, `pl060` and `pl100`.

    FIVE, not four. What this shape adds to Shape 1 is exactly the fourth
    system record, `WS-System-Record-4` - the period-totals record that the
    nine period-total writes of the Sales and Purchase programs are the sole
    writers of. See CORRECTION 3 in the footer.

    Attributes:
        calling_data: as `GlLinkage.calling_data`, and mutable for the same
            reason.
        system_record: `SYSTEM-REC`, as `GlLinkage.system_record`.
        system_record_4: `SYSTOT-REC` [copybooks/wssys4.cob] - the period
            totals. The caller spells it `WS-System-Record-4`; the callee spells
            its own parameter `system-record-4` [sales/sl060.cbl:L397]. Same
            record, two spellings, and both spellings are preserved in the
            traceability document rather than reconciled.
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

    `procedure division using IRS-System-Params, WS-System-Record, File-Defs`
    [irs/irs030.cbl:L552-L554], dispatched inline from irs/irs.cbl `Main-Loop.`
    at L668-L671. Serves `irs030` alone.

    Materially different from the other two shapes, and the difference is not
    cosmetic: there is NO calling-data block and NO `to-day`. Two consequences
    follow, and both are honoured rather than smoothed away:

      * there is no `WS-Term-Code` on this route, so the abort gate and the
        serious-error test simply do not apply to it - `irs030` reports through
        its own screen paths, which are out of scope; and
      * the run date reaches the program only inside the two system records,
        never as text, so this carrier has no `to_day` member at all.

    Attributes:
        irs_system_params: `01 system-record.`
            [copybooks/irswssystem.cob:L13], renamed to `IRS-System-Params` by
            the `COPY ... REPLACING` at [irs/irs.cbl:L392]. Its
            `03 run-date pic x(8)` [copybooks/irswssystem.cob:L14] is the
            eight-character form `irs_run_date_x8` produces.
        ws_system_record: `SYSTEM-REC` - the ACAS system record, carrying the
            maintainer's own comment `*> ACAS system rec.` at the call site
            [irs/irs.cbl:L669]. Carries the pinned binary `Run-Date`.
        file_defs: `01 File-Defs.` [copybooks/wsnames.cob:L13].
    """

    irs_system_params: IrsSystemParams
    ws_system_record: SystemRecord
    file_defs: FileDefs


# =============================================================================
#  ARGPARSE FRAGMENTS  (section 8.3 of this module's brief)
# =============================================================================
#  Four fragments, one per call shape plus the calling-data group, so that a
#  route composes exactly the options its COBOL shape has and the router needs
#  no conditionals:
#
#      GL route     add_calling_data_arguments(p, default_caller=...)
#                   add_gl_linkage_arguments(p)
#      SL/PL route  add_calling_data_arguments(p, default_caller=...)
#                   add_slpl_linkage_arguments(p)
#      IRS route    add_irs_linkage_arguments(p)          <- and nothing else
#
#  Each fragment MUTATES the parser it is given and returns None, which is the
#  argparse idiom and keeps a route's `build_parser` a flat sequence of calls.
#  No parser is constructed at module scope: importing this module must do no
#  work (see the module docstring).


def _add_run_date_argument(parser: argparse.ArgumentParser) -> None:
    """Add the REQUIRED `--run-date` option - the controlled clock's only input.

    `required=True` is the whole point and is not negotiable (rule R-6). There
    is no default, no fallback to the current day, no environment lookup and no
    test hook: the run date is an explicit argument on every route that needs
    one, because that is what makes two runs of one scenario byte-identical
    (Agent Action Plan section 0.8.5). Omitting the option is an argparse usage
    error and exits non-zero, which is the mechanically checkable proof that no
    ambient default exists.

    The text is NOT validated here (rules R-3 and R-4) - see `resolve_clock`.

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

    Only two fields of the 169-column system record are settable from the
    command line, and the list is closed: extending it would add a field-level
    input the COBOL menus do not offer, which R-3 forbids. The third pinned
    field, `Run-Date`, comes from the clock and never from argv.

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
            "yyyy/mm/dd. Governs date PRESENTATION only and has no effect on "
            "any posted figure. Defaults to the record's own declared value."
        ),
    )
    parser.add_argument(
        "--irs-instead",
        choices=_IRS_INSTEAD_CHOICES,
        default=_IRS_INSTEAD_DEFAULT,
        help=(
            "SYSTEM-REC IRS-Instead, the IRS fan-out switch "
            "(copybooks/wssystem.cob:L179-L181): Y = IRS instead of the "
            "General Ledger, B = IRS as well as it, N = neither. PIN THIS "
            "EXPLICITLY for every scenario: its state changes WHICH TABLES a "
            "run touches, so leaving it at a default makes the affected-table "
            "list ambiguous. Defaults to the record's own declared value."
        ),
    )


def add_calling_data_arguments(
    parser: argparse.ArgumentParser, *, default_caller: str
) -> None:
    """Add the `WS-Calling-Data` option group - five of the seven fields.

    The five that a caller may legitimately set. The other two are deliberately
    absent, and their absence is part of the specification:

      * `--ws-called` is NOT offered, because `WS-Called` is set per dispatch to
        the callee's own program-id: `move "gl070" to ws-called`
        [general/general.cbl:L808], then `move "gl071" to ws-called`
        [general/general.cbl:L812], and so on down the chain. It is the
        dispatch vehicle, not an operator input, so `set_called` fills it.
      * `--ws-term-code` is NOT offered, because `WS-Term-Code` is an OUTPUT.
        Every menu resets it to zero immediately before every `CALL`
        [general/general.cbl:L714] and reads it immediately after
        [general/general.cbl:L720-L721]. Letting argv seed it would invent an
        input the COBOL does not have.

    Not added to the IRS route: Shape 3 carries no calling-data block at all
    [irs/irs030.cbl:L552-L554].

    Args:
        parser: the parser to add the options to. Mutated in place.
        default_caller: the dispatching menu's own identity, to default
            `--ws-caller` to. Pass `WS_CALLER_GENERAL` for the General Ledger
            routes, `WS_CALLER_SALES` for the Sales routes and
            `WS_CALLER_PURCHASE` for the Purchase routes - the literals the
            menus themselves move into the field.
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

    Composed with `add_calling_data_arguments` by every General Ledger route,
    which is why the calling-data group is not repeated here. `file-defs` needs
    no options at all: `01 File-Defs.` is entirely `VALUE`-initialised in the
    copybook [copybooks/wsnames.cob:L13-L16 and on], so the record layer's
    declared defaults already are the COBOL state.

    Args:
        parser: the parser to add the options to. Mutated in place.
    """
    _add_run_date_argument(parser)
    _add_system_record_arguments(parser)


def add_slpl_linkage_arguments(parser: argparse.ArgumentParser) -> None:
    """Add the options Shape 2 needs: the required `--run-date`, plus `SYSTEM-REC`.

    The same option set as Shape 1, and deliberately a SEPARATE function rather
    than an alias: the router composes per route with no conditionals, and the
    two names document which shape a route is building even where the options
    coincide. Should the shapes ever be read differently, the divergence has a
    place to live.

    What Shape 2 adds over Shape 1 is the `WS-System-Record-4` instance, and
    that needs NO extra options: `SYSTOT-REC` is a period-totals accumulator
    that the Sales and Purchase programs write, never an operator input.

    Args:
        parser: the parser to add the options to. Mutated in place.
    """
    _add_run_date_argument(parser)
    _add_system_record_arguments(parser)


def add_irs_linkage_arguments(parser: argparse.ArgumentParser) -> None:
    """Add the options Shape 3 needs: the required `--run-date`, and nothing else.

    NONE of the calling-data options are added - not `--ws-caller`, not
    `--ws-del-link`, not `--ws-process-func`, not `--ws-sub-function` and not
    `--ws-cd-args` - because Shape 3 carries no calling-data block
    [irs/irs030.cbl:L552-L554], and the IRS entry point passes exactly three
    arguments.

    The two `SYSTEM-REC` presentation and fan-out options are not added either.
    `Date-Form` governs presentation, which this route has none of; and the
    fan-out switch selects whether the SALES and PURCHASE programs also post to
    IRS - it is read at three sites in each of those four programs, and never by
    `irs030`, which IS the IRS posting program. `bind_irs_linkage` still honours
    both if a composing parser happens to supply them, and otherwise leaves them
    at the record's declared defaults.

    `--run-date` IS added, and is required. Shape 3 has no `to-day` parameter,
    but two fields still need the pinned clock: the binary
    `WS-System-Record.Run-Date` [copybooks/wssystem.cob:L67], which is
    unambiguous because the ACAS system record is the second linkage argument
    [irs/irs.cbl:L669]; and the eight-character `IRS-System-Params.Run-Date`
    [copybooks/irswssystem.cob:L14], which irs/irs.cbl always populates through
    `zz090-Proc-Run-Date.` [irs/irs.cbl:L972-L978]. See the module docstring.

    Args:
        parser: the parser to add the option to. Mutated in place.
    """
    _add_run_date_argument(parser)


# =============================================================================
#  THE CONTROLLED CLOCK  (section 8.4 of this module's brief, rule R-6)
# =============================================================================


def resolve_clock(run_date_text: str) -> clock.PinnedRunDate:
    """Pin both date observables from the `--run-date` text. One delegation.

    The whole of the clock contract in one call. `acas_posting.clock` reproduces
    [copybooks/Proc-ACAS-Mapser-RDB.cob:L73-L80] - the caller pre-zero at L78,
    the `maps04` call at L79 and the store at L80 - so there is deliberately no
    date arithmetic, no separator handling, no calendar test and no parsing of
    any kind in this module.

    THE TEXT IS NOT VALIDATED (rules R-3 and R-4). A date the legacy module
    rejects comes back with `run_date` 0 and NO exception, which reproduces
    `maps04` falling through without touching its output field
    [common/maps04.cbl:L146], [common/maps04.cbl:L154] together with the caller
    pre-zero that turns "untouched" into zero
    [copybooks/Proc-ACAS-Mapser-RDB.cob:L78]. That is anomaly 16 of the
    register. Raising instead would both add a validation and correct a defect,
    and the migration is required to do neither.

    Args:
        run_date_text: the date text as supplied on the command line,
            canonically DD/MM/CCYY. Whatever a caller typed, verbatim: shorter
            text is space-padded and longer text truncated to the declared
            `PIC X(10)` width by the clock module, and separator normalisation
            happens inside `maps04`, after the text form has already been
            captured.

    Returns:
        The pinned pair. `to_day` is the text as supplied at the declared width -
        NOT a normalised form, because L77 copies it before L79 converts it -
        and `run_date` is the binary day number counted from 1600-12-31, or 0 if
        the date was rejected.

    Example:
        >>> resolve_clock("21/09/2025")
        PinnedRunDate(to_day='21/09/2025', run_date=155127)
        >>> resolve_clock("31/02/2025").run_date
        0
    """
    return clock.pin_from_to_day(run_date_text)


# =============================================================================
#  BINDERS  (section 8.4 of this module's brief)
# =============================================================================
#  A binder turns a parsed namespace into one linkage shape. Two conventions run
#  through all four of them:
#
#  1. START FROM THE RECORD'S DECLARED DEFAULTS, THEN OVERWRITE. Constructing
#     `WsCallingData()` already reproduces the state each menu establishes
#     before a dispatch - `move spaces to ws-called ws-del-link`
#     [general/general.cbl:L513], `move zeros to ws-Process-Func
#     ws-Sub-Function` [general/general.cbl:L505], `move zero to ws-term-code`
#     [general/general.cbl:L714] and `WS-CD-Args` never assigned at all - so a
#     binder only has to apply what argv actually says.
#
#  2. READ THE NAMESPACE TOLERANTLY, EXCEPT FOR THE RUN DATE. An option group is
#     added per route, so a namespace legitimately lacks the attributes of a
#     group its route did not compose; each read therefore falls back to the
#     same COBOL default the fragment would have supplied, which makes the two
#     paths indistinguishable in the resulting record. `run_date` is the ONE
#     exception and is read directly: it has no defensible default, so a missing
#     one must surface as an error rather than be invented. That direct read is
#     itself part of the proof that no ambient date can enter here.


def _menu_caller_for(program_id: str) -> str:
    """Return the menu identity that dispatches one posting program.

    Which menu shell owns which program is a fact of the frozen source, not a
    choice: general/general.cbl dispatches the `gl` programs, sales/sales.cbl
    the `sl` programs and purchase/purchase.cbl the `pl` programs. So the caller
    is derivable from the callee, which is what lets `bind_slpl_linkage` serve
    both the Sales and the Purchase routes from one signature.

    Used only as the FALLBACK behind `--ws-caller`; an explicit option always
    wins, exactly as the Sales pre-run block overrides the caller for a
    different callee at [sales/sales.cbl:L464-L465].

    Args:
        program_id: the callee's program-id, as `"gl070"` or `"pl100"`.

    Returns:
        The dispatching menu's literal identity, or `WS-Caller`'s own declared
        default - spaces at its `PIC X(8)` width [copybooks/wscall.cob:L8] - for
        a program-id that no in-scope menu dispatches. Spaces rather than an
        exception, because "not assigned" is a state the field genuinely has and
        rejecting the name would be a validation this migration may not add
        (rule R-3). `WS_CALLER_ACAS` is deliberately unreachable from here: the
        top-level menu dispatches the four ledger menus, never a posting
        program.
    """
    prefix = program_id.strip().lower()[:2]
    if prefix == "gl":
        return WS_CALLER_GENERAL  # general/general.cbl:L512
    if prefix == "sl":
        return WS_CALLER_SALES  # sales/sales.cbl:L481
    if prefix == "pl":
        return WS_CALLER_PURCHASE  # purchase/purchase.cbl:L475
    return _declared_calling_data().ws_caller


def _bind_system_record(
    ns: argparse.Namespace, pinned: clock.PinnedRunDate
) -> SystemRecord:
    """Build `SYSTEM-REC` at its declared defaults with the three fields pinned.

    Exactly three of the 169 columns are set here and the list is closed:
    `Run-Date` from the clock, and `Date-Form` and `IRS-Instead` from argv when
    the route offered them. Everything else keeps the record layer's declared
    default.

    Args:
        ns: the parsed namespace. `date_form` and `irs_instead` are read
            tolerantly, so a route that did not add them is served identically.
        pinned: the pinned pair from `resolve_clock`. Only `run_date` is used;
            the text observable travels as its own linkage parameter in Shapes 1
            and 2 and does not exist in Shape 3.

    Returns:
        The system record for this run.
    """
    system_record = _declared_system_record()

    #  [copybooks/wssystem.cob:L67] `05 Run-Date binary-long.` - an `int`, never
    #  a binary-radix numeric type (rule R-2), and from the pinned clock only:
    #  never from argv directly and never from an ambient source (rule R-6).
    #  This is the DIFF-VISIBLE observable of the pair - it is the column
    #  SYSTEM-REC.RUN-DAT and so appears in every table dump the scenario
    #  comparison inspects.
    system_record.system_data_block.run_date = pinned.run_date

    #  [copybooks/wssystem.cob:L128-L131] presentation only.
    system_record.system_data_block.date_form = getattr(
        ns, "date_form", _DATE_FORM_DEFAULT
    )

    #  [copybooks/wssystem.cob:L179-L181] the fan-out switch, which changes
    #  WHICH TABLES a run touches - hence pinnable, per Agent Action Plan
    #  section 0.6.4.
    system_record.general_ledger_block.irs_instead = getattr(
        ns, "irs_instead", _IRS_INSTEAD_DEFAULT
    )

    # AMBIGUITY Q-CLI-SYSREC-LOAD: in the COBOL the MENU SHELL loads SYSTEM-REC
    # and SYSTOT-REC from the store before the CALL and rewrites them afterwards
    # in `overrewrite` [general/general.cbl:L656], [sales/sales.cbl:L628],
    # [purchase/purchase.cbl:L621]; the menus are out of scope and this layer may
    # not reach the data-access layer, so the records are built at their declared
    # defaults with only the three fields above pinned - should the Python cycle
    # instead load them through the program layer? — resolve against
    # the compiled oracle; record in docs/migration/ambiguity-resolutions.md
    return system_record


def bind_calling_data(
    ns: argparse.Namespace, *, called: str, caller: str
) -> WsCallingData:
    """Bind argv to `01 WS-Calling-Data` [copybooks/wscall.cob:L6-L14].

    Reproduces, in order, the state a menu shell establishes immediately before
    a dispatch. The returned record is MUTABLE by design: the callee writes
    `WS-Term-Code` back into it [general/gl070.cbl:L289] and the entry point
    reads it afterwards [general/general.cbl:L720-L721].

    Field widths are NOT applied here. A `MOVE` into a `PIC X(8)` field pads or
    truncates to eight characters, but that is `MOVE` semantics and belongs to
    `acas_posting/cobol/move.py`, which this layer may not import; each value is
    therefore assigned as supplied and the record layer's own field semantics
    govern it. Recorded as an omission in the footer.

    Args:
        ns: the parsed namespace. All five calling-data attributes are read
            tolerantly, each falling back to the COBOL default that
            `add_calling_data_arguments` would have supplied.
        called: the callee's program-id, for `WS-Called`. Set per dispatch, as
            `move "gl070" to ws-called` [general/general.cbl:L808].
        caller: the dispatching menu's identity, used for `WS-Caller` only when
            the namespace carries no `--ws-caller`. An explicitly supplied
            option always wins.

    Returns:
        The bound record, with `WS-Term-Code` at zero ready for the dispatch.
    """
    calling_data = _declared_calling_data()

    #  [general/general.cbl:L808] `move "gl070" to ws-called` - per dispatch.
    set_called(calling_data, called)

    #  [general/general.cbl:L512] `move "general" to ws-caller`. `is None`
    #  rather than a truth test, because a deliberately space-filled caller is a
    #  legitimate value and must not be mistaken for "absent".
    supplied_caller = getattr(ns, "ws_caller", None)
    calling_data.ws_caller = caller if supplied_caller is None else supplied_caller

    #  [general/general.cbl:L513] `move spaces to ws-called ws-del-link ...`
    calling_data.ws_del_link = getattr(ns, "ws_del_link", WS_DEL_LINK_DEFAULT)

    #  [general/general.cbl:L505] `move zeros to ws-Process-Func ws-Sub-Function`
    calling_data.ws_process_func = getattr(
        ns, "ws_process_func", WS_PROCESS_FUNC_DEFAULT
    )
    calling_data.ws_sub_function = getattr(
        ns, "ws_sub_function", WS_SUB_FUNCTION_DEFAULT
    )

    #  ANOMALY, REPRODUCED (rule R-4): no menu shell ever assigns `WS-CD-Args`
    #  [copybooks/wscall.cob:L14] - the shells only read it, at
    #  [sales/sales.cbl:L463] and [purchase/purchase.cbl:L457] - so its default
    #  is spaces and the pre-run branch those reads guard is dead under menu
    #  dispatch. The option exists because the maintainer designed the field for
    #  exactly this unattended case [copybooks/wscall.cob:L1-L3].
    calling_data.ws_cd_args = getattr(ns, "ws_cd_args", WS_CD_ARGS_DEFAULT)

    #  [general/general.cbl:L714] `move zero to ws-term-code` - LAST, immediately
    #  before the dispatch, exactly where the COBOL puts it.
    reset_term_code(calling_data)

    return calling_data


def bind_gl_linkage(ns: argparse.Namespace, *, called: str) -> GlLinkage:
    """Bind Shape 1 - the four-parameter General Ledger shape.

    Args:
        ns: the parsed namespace of a route that composed
            `add_calling_data_arguments` and `add_gl_linkage_arguments`.
        called: the callee's program-id - `"gl070"`, `"gl071"`, `"gl072"` or
            `"gl080"`, the literals general/general.cbl moves into `WS-Called`
            at L808, L812, L814 and L820.

    Returns:
        The four arguments in COBOL parameter order
        [general/gl070.cbl:L245-L248], ready to splat into the program's `run`.

    Raises:
        AttributeError: the namespace carries no `run_date`, meaning the route
            failed to add the required option. Deliberately not caught and
            deliberately not defaulted: a missing run date must be an error,
            because the alternative is an ambient one (rule R-6).
    """
    pinned = resolve_clock(ns.run_date)
    return GlLinkage(
        calling_data=bind_calling_data(
            ns, called=called, caller=_menu_caller_for(called)
        ),
        system_record=_bind_system_record(ns, pinned),
        to_day=pinned.to_day,
        file_defs=FileDefs(),
    )


def bind_slpl_linkage(ns: argparse.Namespace, *, called: str) -> SlPlLinkage:
    """Bind Shape 2 - the five-parameter Sales and Purchase shape.

    Serves both ledgers from one signature: the dispatching menu is derived from
    the callee's program-id, so `"sl060"` binds a Sales caller and `"pl060"` a
    Purchase one, and `--ws-caller` overrides either.

    Args:
        ns: the parsed namespace of a route that composed
            `add_calling_data_arguments` and `add_slpl_linkage_arguments`.
        called: the callee's program-id - `"sl055"`, `"sl060"`, `"sl100"`,
            `"pl055"`, `"pl060"` or `"pl100"`.

    Returns:
        The five arguments in COBOL parameter order
        [sales/sl060.cbl:L395-L399]. `system_record_4` is a fresh `SYSTOT-REC`
        at its declared defaults - see Q-CLI-SYSREC-LOAD, which covers it on the
        same footing as `SYSTEM-REC`.

    Raises:
        AttributeError: as `bind_gl_linkage`.
    """
    pinned = resolve_clock(ns.run_date)
    return SlPlLinkage(
        calling_data=bind_calling_data(
            ns, called=called, caller=_menu_caller_for(called)
        ),
        system_record=_bind_system_record(ns, pinned),
        system_record_4=SystemRecord4(),
        to_day=pinned.to_day,
        file_defs=FileDefs(),
    )


def bind_irs_linkage(ns: argparse.Namespace) -> IrsLinkage:
    """Bind Shape 3 - the three-parameter IRS shape.

    No `called` keyword, because there is no `WS-Called` to fill: Shape 3 has no
    calling-data block [irs/irs030.cbl:L552-L554], and irs/irs.cbl names its
    callee as a `CALL` literal rather than through the field
    [irs/irs.cbl:L668].

    Args:
        ns: the parsed namespace of a route that composed
            `add_irs_linkage_arguments`. Only `run_date` is required.

    Returns:
        The three arguments in COBOL parameter order [irs/irs.cbl:L668-L671].

    Raises:
        AttributeError: as `bind_gl_linkage`.
    """
    pinned = resolve_clock(ns.run_date)

    irs_system_params = IrsSystemParams()

    #  [irs/irs.cbl:L972-L978] `zz090-Proc-Run-Date.` - the eight-character IRS
    #  form, century dropped.
    #
    # AMBIGUITY Q-CLI-IRS-RUNDATE: irs/irs.cbl always populates
    # IRS-System-Params.Run-Date [copybooks/irswssystem.cob:L14] before any menu
    # option runs and notes at [irs/irs.cbl:L636] that the "menu uses the irs
    # param file dates", yet the posting record's own date comes from the data -
    # `move WS-IRS-Post-Date to post-date` [irs/irs030.cbl:L1662] - so does
    # irs030 observe this field at all, and does pinning it change any stored
    # value? — resolve against
    # the compiled oracle; record in docs/migration/ambiguity-resolutions.md
    irs_system_params.run_date = irs_run_date_x8(pinned.to_day)

    return IrsLinkage(
        irs_system_params=irs_system_params,
        #  The binary Run-Date on this route is NOT ambiguous: the ACAS system
        #  record is the second linkage argument, with the maintainer's own
        #  comment `*> ACAS system rec.` at [irs/irs.cbl:L669].
        ws_system_record=_bind_system_record(ns, pinned),
        file_defs=FileDefs(),
    )


# =============================================================================
#  FAITHFUL HELPERS  (section 8.6 of this module's brief)
# =============================================================================
#  Each of the five reproduces ONE COBOL statement or ONE COBOL predicate, and
#  nothing more. They are named functions rather than inline expressions for two
#  reasons that both matter: the traceability document maps each one to its
#  COBOL statement (rule R-5), and the seven entry points then share one
#  implementation instead of seven copies that could drift apart.


def reset_term_code(calling_data: WsCallingData) -> None:
    """`move zero to ws-term-code.` - reproduced exactly.

    CALL THIS IMMEDIATELY BEFORE EVERY DISPATCH, not once per run. That is where
    the COBOL puts it, and it puts it there once per `CALL` site:
    [general/general.cbl:L714] and [general/general.cbl:L730],
    [sales/sales.cbl:L680] and [sales/sales.cbl:L701],
    [purchase/purchase.cbl:L673] and [purchase/purchase.cbl:L694], and
    [common/ACAS.cbl:L576].

    The placement is load-bearing rather than tidy. `WS-Term-Code` is shared
    linkage storage, so a code a previous callee left behind would still be
    there for the next test of it - and in the posting cycle that test decides
    whether the remaining phases run at all [general/general.cbl:L810-L811].
    Clearing it per dispatch is what makes each phase's verdict its own.

    Args:
        calling_data: the record to clear. Mutated in place, exactly as COBOL
            writes into the caller's own storage.
    """
    calling_data.ws_term_code = WS_TERM_CODE_DEFAULT


def set_called(calling_data: WsCallingData, program_id: str) -> None:
    """`move "<prog>" to ws-called.` - reproduced exactly.

    The menus set the field once per dispatch and then transfer to the shared
    dispatch paragraph: `move "gl070" to ws-called`
    [general/general.cbl:L808], `move "gl071" to ws-called`
    [general/general.cbl:L812], `move "gl072" to ws-called`
    [general/general.cbl:L814], `move "gl080" to ws-called`
    [general/general.cbl:L820]. In the COBOL the field is also the CALL TARGET -
    `call ws-called using ...` [general/general.cbl:L715] is a dynamic call by
    name - whereas here the entry point invokes the migrated module directly and
    the field is carried for traceability and for any callee that reads it.

    Receiving-field width is NOT applied: `WS-Called` is `PIC X(8)`
    [copybooks/wscall.cob:L7] and a COBOL `MOVE` would pad a five-character
    program-id to eight, but `MOVE` semantics belong to
    `acas_posting/cobol/move.py` and this layer may not import it. Recorded as
    an omission in the footer.

    Args:
        calling_data: the record to write into. Mutated in place.
        program_id: the callee's program-id, as `"gl070"`.
    """
    calling_data.ws_called = program_id


def is_serious_error(term_code: int) -> bool:
    """`if ws-term-code > 7` - the serious-error predicate.

    "Got a serious (reported) error", in the maintainer's own words at
    [sales/sales.cbl:L691]. Tested at [general/general.cbl:L720] and
    [general/general.cbl:L735], [sales/sales.cbl:L691] and
    [sales/sales.cbl:L710], [purchase/purchase.cbl:L684] and
    [purchase/purchase.cbl:L703], and [common/ACAS.cbl:L578].

    A TOTAL predicate, and its complement needs no second helper: `WS-Term-Code`
    is `pic 99` [copybooks/wscall.cob:L10] so its domain is 0 through 99, over
    which the COBOL's own two tests - `> 7` and the `< 8` at
    [sales/sales.cbl:L686] and [sales/sales.cbl:L708] - are exhaustive and
    mutually exclusive. `not is_serious_error(code)` IS `ws-term-code < 8`.

    Note what this predicate does NOT single out. `GL_ABORT_TERM_CODE` is 5,
    which is `< 8`, so a General Ledger abort is NOT a serious error by this
    test: the menu handles it with its own equality test
    [general/general.cbl:L810-L811] and returns to the menu, leaving the later
    phases unrun. `EXTRACT_MISSING_FILE_TERM_CODE` is 8 and therefore IS one.
    Both facts are reproduced, not reconciled (rule R-4).

    Args:
        term_code: the value of `WS-Term-Code` after a dispatch.

    Returns:
        True when the callee reported a serious error.
    """
    return term_code > SERIOUS_ERROR_THRESHOLD


def exit_status_for(term_code: int) -> int:
    """Map `WS-Term-Code` to a process exit status.

    The identity, and the identity is total: `WS-Term-Code` is `pic 99`
    [copybooks/wscall.cob:L10] so every value it can hold is 0 through 99, well
    inside the 0-255 range a POSIX wait status carries. Zero therefore maps to
    zero, which is success, and every non-zero code is surfaced unchanged so
    that a caller of the migrated cycle sees the code the COBOL produced rather
    than a lossy re-encoding of it.

    Where the COBOL keeps this information, for reference: it never exits with
    it. A menu tests the code and either returns to its own display loop
    [general/general.cbl:L720-L721] or, on the Sales five-parameter path,
    performs `overrewrite` and then `goback` [sales/sales.cbl:L710-L712]; the
    top-level menu does the same [common/ACAS.cbl:L578-L579]. There is no
    process-status equivalent in the original because the original is an
    interactive menu, which is precisely why the mapping is an open question
    rather than a transcription.

    Args:
        term_code: the value of `WS-Term-Code` after the last dispatch.

    Returns:
        The exit status to leave the process with.
    """
    # AMBIGUITY Q-CLI-EXITSTATUS: the COBOL menus never exit with WS-Term-Code -
    # they return to a display loop [general/general.cbl:L720-L721] or `goback`
    # [sales/sales.cbl:L710-L712], [purchase/purchase.cbl:L703-L704],
    # [common/ACAS.cbl:L578-L579] - so what process exit status should each band
    # of the pic 99 domain produce, 0, 1..7 and 8..99? — resolve against
    # the compiled oracle; record in docs/migration/ambiguity-resolutions.md
    return term_code


def irs_run_date_x8(to_day: str) -> str:
    """`zz090-Proc-Run-Date.` [irs/irs.cbl:L972-L978] - reproduced exactly.

    The statement being reproduced, verbatim from the frozen source::

        L972  zz090-Proc-Run-Date.
        L973      move     ACAS-Run-Date to u-bin.
        L974      perform  maps04.  *> now have x(10) & dd/mm/ccyy
        L975      string   u-date (1:6)  delimited by size
        L976               u-date (9:2)  delimited by size  *> Only grab YY and not CC
        L977                      into Run-Date             *> As IRS uses dd/mm/yy
        L978      end-string.

    The maintainer's own comments at [irs/irs.cbl:L968-L971] explain the intent:
    "convert the binary run, start & end date from binary days to x(8) by
    ignoring the cc subfield (century) as not used in IRS".

    L973 and L974 are already done by the time this function is called - the
    pinned pair carries the `x(10)` text - so what remains is the `STRING` of
    L975-L977, which is pure text assembly. COBOL reference modification is
    one-based and `(start:length)`, so `u-date (1:6)` is characters 1 to 6 and
    `u-date (9:2)` is characters 9 to 10, giving `to_day[0:6] + to_day[8:10]`:
    "dd/mm/" followed by "yy". No date module, no calendar and no arithmetic of
    any kind is involved, and none is used here.

    Args:
        to_day: the pinned `to-day`, DD/MM/CCYY. In the COBOL `u-date` is
            `PIC X(10)` and therefore always exactly ten characters, so both
            slices are always in range; `resolve_clock` guarantees the same
            width here, which is why no length check is needed - and adding one
            would be a validation the COBOL does not perform (rule R-3).

    Returns:
        The eight-character `dd/mm/yy` form that
        `IRS-System-Params.Run-Date pic x(8)`
        [copybooks/irswssystem.cob:L14] holds.

    Example:
        >>> irs_run_date_x8("21/09/2025")
        '21/09/25'
    """
    #  [L975] u-date (1:6)  ->  "dd/mm/"      [L976] u-date (9:2)  ->  "yy"
    return to_day[0:6] + to_day[8:10]


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
# CORRECTIONS  -  each verified against the frozen source with a line read. DO
# NOT "fix" these back to the values the planning documents carry.
#
#   1. WS-CD-Args is at copybooks/wscall.cob:L14, NOT L13, so the record block
#      is L6-L14 and not L6-L13 as Agent Action Plan section 0.4.1.1 cites. L13
#      is WS-Sub-Function and L11 is a comment line between L10 and L12. Every
#      citation in this module uses L6-L14.
#
#   2. The General Ledger abort is raised at general/gl070.cbl:L289
#      (`move 5 to ws-term-code`), inside the conditional at L287-L290
#      (`if a = 1` / `perform gl060a` / the raise / `go to main-exit.`). The
#      Agent Action Plan and the folder brief both cite L288, which is
#      `perform gl060a` - a display of the batch-status report, not the raise.
#      Two neighbouring lines are also commonly mis-cited: L312-L313 is the
#      CYCLE FILTER (`if bcycle not = scycle` / `go to loop.`) and L314-L315 is
#      the OPEN-BATCH DETECTOR (`if status-open` / `move 1 to a.`); neither
#      raises anything.
#
#   3. The Sales and Purchase linkage shape has FIVE parameters, not four. Agent
#      Action Plan section 0.4.1.1 calls it "the four-parameter SL/PL linkage
#      shape", which is a slip; section 0.1.1 has it right - "The Sales and
#      Purchase families add the fourth system record" - and so does the source:
#      sales/sales.cbl:L702-L706 and purchase/purchase.cbl:L695-L699 both pass
#      five arguments, and the callee declares five at
#      sales/sl060.cbl:L395-L399. `SlPlLinkage` has five members.
#
# OMISSIONS  -  recorded as omissions so that a reader comparing the two trees
# does not conclude something was lost (Agent Action Plan section 0.4.3).
#
#   * ALL MENU SCREEN I/O. The `display-menu` paragraph and every `DISPLAY ... AT`
#     / `ACCEPT ... AT` around the dispatch - general/general.cbl:L511 onwards,
#     sales/sales.cbl:L479 onwards, purchase/purchase.cbl:L473 onwards,
#     common/ACAS.cbl:L429 onwards - has no database effect and is excluded by
#     Agent Action Plan sections 0.2.2 and 0.3.4. An `ACCEPT` that merely pauses
#     for acknowledgement is dropped; one that would gate a database write
#     becomes an explicit parameter of the individual entry point, never of this
#     module.
#
#   * THE `go to load01 ... depending on z` DISPATCH TABLES. general/general.cbl
#     L696-L704 and common/ACAS.cbl L558-L566. Menu-reply decoding, replaced by
#     one entry point per route rather than by a computed transfer.
#
#   * `overrewrite`'s SYSTEM-RECORD PERSISTENCE and `pre-overrewrite`'s BACKUP
#     SPOOL-OUT. The menus rewrite SYSTEM-REC and SYSTOT-REC after a dispatch
#     (general/general.cbl:L656, sales/sales.cbl:L628,
#     purchase/purchase.cbl:L621) and hand a backup script to the operating
#     system with `call "SYSTEM"` (general/general.cbl:L650, sales/sales.cbl:L625,
#     purchase/purchase.cbl:L618). The first needs the data-access layer, which
#     this layer may not reach - see Q-CLI-SYSREC-LOAD. The second is excluded
#     twice over: by the spool-out exclusion of Agent Action Plan section 0.2.2
#     and by rule R-1.
#
#   * `Default-Record`. general/general.cbl `load000.` L727-L737 looks like the
#     five-parameter shape but its THIRD argument is `default-record`
#     (L731-L732), not `WS-System-Record-4`. That paragraph serves gl020 and
#     gl050, both out of scope, so NO in-scope General Ledger route uses it and
#     this module deliberately binds no such record. `SlPlLinkage` is the only
#     five-member shape here, and its third member is `SYSTOT-REC`.
#
#   * `SYSTEM-REC` FIELDS BEYOND THE THREE PINNED. The record has 169 columns
#     and exactly three are settable here - Run-Date, Date-Form and IRS-Instead.
#     Every other field keeps the record layer's declared default. Adding an
#     option for any of them would add an input the COBOL menus do not offer
#     (rule R-3).
#
#   * `MOVE` RECEIVING-FIELD SEMANTICS. Truncation, space padding and
#     justification for `WS-Called`, `WS-Caller` and `WS-Del-Link` at `PIC X(8)`
#     and `WS-CD-Args` at `PIC X(13)` are NOT applied here. They are `MOVE`
#     semantics and belong to `acas_posting/cobol/move.py`, which this layer may
#     not import; values are assigned as supplied and the record layer's own
#     field semantics govern them. The declared defaults this module starts from
#     are already at their full declared widths.
#
#   * THE FIVE PROMOTED CALLEE PARAMETERS. gl080's run-confirm, disk-change and
#     archive-path; gl051's control-total inputs; sl100's post-confirm; pl100's
#     run-confirm; irs030's clear-transfer-file decision. Each is an `ACCEPT`
#     that gates a database write and each becomes an option on its OWN entry
#     point, because each belongs to one route only. None is a linkage parameter
#     and none is bound here.
#
# AMBIGUITIES RAISED BY THIS MODULE  (rule R-6)  -  three, each marked in place
# at the code it governs and each to be settled against the compiled oracle and
# recorded in docs/migration/ambiguity-resolutions.md:
#   Q-CLI-EXITSTATUS   in exit_status_for
#   Q-CLI-IRS-RUNDATE  in bind_irs_linkage
#   Q-CLI-SYSREC-LOAD  in _bind_system_record
#
# RULES  (no user rules document exists for this project; these are the Agent
# Action Plan's own six, section 0.7.2)
#   R-1  satisfied structurally: the imports of this module are argparse, typing
#        and six modules of this package. No child process, no foreign-function
#        interface, no toolchain lookup, and no option that reaches the compiled
#        comparison oracle.
#   R-2  satisfied by type: WS-Term-Code and Run-Date are `int`, to-day and the
#        IRS run-date are `str`. No binary-radix numeric type appears in any
#        signature, option type or expression.
#   R-3  satisfied by omission: no run-date validation, no added record field, no
#        SQL, no schema access, and no concurrency of any kind. The only option
#        domains declared are the fields' own - `pic 9` gives 0-9 and
#        `88 Date-Valid-Formats` gives 1, 2, 3.
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
