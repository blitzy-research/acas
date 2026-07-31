"""The controlled clock: the one boundary at which a run date enters the cycle.

Agent Action Plan section 0.4.1.6 gives this module its entire mandate:

    acas_posting/clock.py | CREATE | copybooks/Proc-ACAS-Mapser-RDB.cob |
    "Pins both observables - the text date and the binary run date - from a
    single injected value; the source of truth is the one clock read in the
    menu shell [copybooks/Proc-ACAS-Mapser-RDB.cob:L72-L80]".

It is a rule-forced deliverable. Agent Action Plan section 0.7.3 lists this file
as forced into scope by rule R-6, compiled behaviour is the tie-breaker, and not
by any feature description. Its job is to make two runs of the same scenario
byte-identical, and it is proven by tests/determinism/test_two_runs_byte_identical.py.

THIS MODULE NEVER READS A CLOCK  (rule R-6)
===========================================
The date is INJECTED. Every function here takes it as an argument, and there is
no default that resolves to "now" - not a convenience one, not one behind a
flag, not one in a test hook. A caller who wants today's date must obtain it
OUTSIDE this package and pass it in, because the whole determinism argument
rests on that being the only route in.

So this module reads no system clock, no elapsed-time counter, no environment
variable, no host name, no user name and no entropy source. Its output for a
given input is byte-identical across runs and across processes.

Those absences are mechanically checkable, and they are meant to be checked: a
grep of this file for any ambient-time or entropy call returns nothing at all,
because even the prose above is worded to avoid the names it disclaims. Keep it
that way when editing - a docstring that trips the check makes the check
useless to whoever runs it next.

WHAT IS PINNED - EXACTLY TWO OBSERVABLES
========================================
Agent Action Plan section 0.1.1 is emphatic that this is smaller than it sounds:

    "The controlled-clock requirement is structurally easier than it appears,
    and must not be over-engineered. Every one of the in-scope posting programs
    contains zero clock reads; the date arrives purely through linkage. ...
    Consequently the controlled clock needs to pin exactly two observables -
    the text date `to-day pic x(10)` in DD/MM/CCYY form, and the binary
    `Run-Date` [copybooks/wssystem.cob:L67] - and inject them at the CLI
    boundary. No clock abstraction is needed inside the migrated programs at
    all."

  * `to-day pic x(10)` - the text date, DD/MM/CCYY. A LINKAGE parameter, not a
    column: declared `01 to-day pic x(10).` at [general/general.cbl:L357], at
    [general/gl070.cbl:L243] and at [irs/irs.cbl:L405]. It is the third
    argument of the General Ledger call shape [general/gl070.cbl:L245-L248] and
    the fourth of the Sales and Purchase shape [sales/sl060.cbl:L395-L399].

  * `Run-Date binary-long` [copybooks/wssystem.cob:L67] - the binary day
    number, a signed 32-bit integer of scale zero, so a Python `int` here and
    never a binary floating-point value (rule R-2).

    Unlike the text date this one IS a column, and therefore DIFF-VISIBLE. The
    authoritative bridge triple is: the copybook field above, SIGNED; the host
    variable `HV-RUN-DAT PIC 9(10) COMP` [common/systemMT.cbl:L336], UNSIGNED,
    loaded at [common/systemMT.cbl:L1082] and unloaded at
    [common/systemMT.cbl:L1268]; and the column `SYSTEM-REC`.`RUN-DAT`,
    `int(8) unsigned NOT NULL` in the frozen schema. Its data-dictionary entry
    is keyed `SYSTEM-REC.RUN-DAT`. Note the column name is RUN-DAT, not
    RUN-DATE. Note also that the signed copybook field becomes an unsigned host
    variable and an unsigned column: reproducing THAT conversion is
    acas_posting/dal/acas000_system.py's job, at the bridge boundary where it
    actually happens, and deliberately not this module's - a pinned day number
    is handed over exactly as the COBOL computed it.

    Getting the epoch wrong would surface as a one-column diff in every single
    scenario, which is precisely the failure the determinism test exists to
    catch.

THE EPOCH  [common/maps04.cbl:L167]
===================================
The binary day number counts from 1600-12-31, so day 1 is 1601-01-01 and
2025-09-21 is 155127. It is NOT a Unix timestamp and NOT a Python ordinal. The
maintainer flags the epoch himself, in the remarks of the program that defines
it: "THIS uses binary Dates from 31/12/1600 so is NOT usable within IRS as is"
[common/maps04.cbl:L39-L41]. The conversion is not reimplemented here - it lives
in exactly one place, acas_posting.dates, which reproduces common/maps04.cbl in
full (rules R-1 and R-5).

BOTH DIRECTIONS ARE REAL
========================
A one-directional clock module would fail one of its two callers.

  * FORWARD, text to binary [copybooks/Proc-ACAS-Mapser-RDB.cob:L72-L80]. The
    text is assembled from date components and `maps04` derives the binary day
    number from it. Reproduced by `pin_from_calendar_date` and, from
    caller-supplied text, by `pin_from_to_day`.

  * REVERSE, binary to text [general/general.cbl:L465-L467]. In normal menu
    operation the BINARY is authoritative - it is read from the system record -
    and the text is DERIVED from it through `maps04`'s unpack path. Verified:
    L467 is the only write to `to-day` anywhere in that shell, and `run-date`
    is never written there at all. Reproduced by `pin_from_run_date`.

A REJECTED DATE YIELDS Run-Date = 0, NOT AN EXCEPTION  (rules R-3 and R-4)
=========================================================================
`maps04` leaves its binary field COMPLETELY UNTOUCHED on either of its two
reject paths [common/maps04.cbl:L146, L154], even though its own remarks claim
"Date errors returned as A-Bin equal zero" [common/maps04.cbl:L163]. That is
anomaly #16, and the documented contract holds only because CALLERS zero the
field first. [copybooks/Proc-ACAS-Mapser-RDB.cob:L78] is one of the two sites
that do so, and the pre-zero is reproduced at each forward site below with the
locator on it, because it is the MASKING MECHANISM of a legacy defect and not
boilerplate. Measured, not assumed: with the field pre-set to -999 and a
rejected date, `maps04` leaves -999 standing; with the pre-zero, 0.

Consequently a rejected injected date comes back as `run_date = 0` and no
exception is raised. [copybooks/Proc-ACAS-Mapser-RDB.cob:L80] stores the result
UNCONDITIONALLY, without inspecting it, and 0 is exactly what the COBOL stores.
Raising instead - or validating the text before converting it - would be a new
validation, which rule R-3 forbids outright.

THE CLOCK-READ CENSUS, CORRECTED
================================
Agent Action Plan sections 0.1.1 and 0.7.2 describe
[copybooks/Proc-ACAS-Mapser-RDB.cob:L72-L80] as "the single read in the whole
call chain". A future reader who greps will find more than one, so the verified
census is recorded here rather than left to surprise them. There are FOURTEEN
ambient date and time reads, across six files:

    FUNCTION CURRENT-DATE, six sites
        common/ACAS.cbl:L353                     general/general.cbl:L371
        sales/sales.cbl:L323                     purchase/purchase.cbl:L318
        irs/irs.cbl:L480                         copybooks/Proc-ACAS-Mapser-RDB.cob:L72
    ACCEPT ... FROM DATE, four sites
        common/ACAS.cbl:L478                     general/general.cbl:L559
        sales/sales.cbl:L528                     purchase/purchase.cbl:L522
    ACCEPT ... FROM TIME, four sites
        common/ACAS.cbl:L470                     general/general.cbl:L551
        sales/sales.cbl:L520                     purchase/purchase.cbl:L514

The plan's CONCLUSION nevertheless holds exactly, and it is the conclusion that
matters: every one of those fourteen sites is in an out-of-scope menu shell or
in the shared date-service copybook the shells COPY, and ALL TWELVE in-scope
posting programs contain ZERO clock reads - gl051, gl070, gl071, gl072, gl080,
sl055, sl060, sl100, pl055, pl060, pl100 and irs030, each verified
individually. The eight `ACCEPT ... FROM DATE` and `... FROM TIME` reads feed
the menu's screen banner only: in the General Ledger shell they run at L551 and
L559, after L467 has already copied `to-day`, and neither observable is written
from them. Pinning the two observables at the CLI boundary is therefore
genuinely sufficient, and no clock abstraction is needed downstream.

WHAT IS DELIBERATELY NOT HERE
=============================
Agent Action Plan section 0.1.1 warns that this "must not be over-engineered",
so the absences are as deliberate as the contents. There is no `Clock` protocol
or abstract base class, no production-versus-test implementation pair, no
freezegun-style monkeypatch hook, no time-provider registry, no global mutable
"current clock" singleton, no time-zone model and no notion of time of day - no
in-scope field has one. Two constructors, one value object and one diagnostic
check is the whole module.

Nor does it switch presentation format. `Date-Form` and its condition names
`Date-UK`, `Date-USA` and `Date-Intl` [copybooks/wssystem.cob:L128-L132] are
handled by the `zz050`, `zz060` and `zz070` reformatters in acas_posting.dates.
This module produces the canonical DD/MM/CCYY `to-day` and nothing else.

Nor does it parse argv: binding arguments is acas_posting.cli.args's job, so
there is no argparse here. `pin_from_to_day` is the plain function a
`--run-date` option calls.

CONTROL FLOW  (rule R-5)
========================
Both reproduced blocks are straight-line MOVE and CALL sequences containing no
GO TO whatsoever, so no class of the four-class GO TO taxonomy in Agent Action
Plan section 0.4.2 applies anywhere in this module. The transfers that do exist
inside `maps04` - its `A-Bin > zero` re-dispatch and its three exits to
`Main-Exit` - are classified and reproduced in acas_posting.dates, where that
program lives.

The two blocks are also unnamed inline fragments rather than named paragraphs -
the forward one sits inside `ba010-Capture-Data`
[copybooks/Proc-ACAS-Mapser-RDB.cob:L49], a paragraph that also accepts and
verifies the company name - so there is no paragraph name for these functions
to inherit. Their names are therefore descriptive, and traceability is carried
by the locator cited in each docstring and at each reproduced statement.

LAYERING  (Agent Action Plan section 0.4.3)
===========================================
`cli/*.py` may import this module. This module imports the standard library and
acas_posting.dates, and nothing else: not `records`, not `dal`, not `programs`,
not `cli`, not `cobol`, not `dictionary`, and never the compiled oracle tree,
which is a top-level sibling of this package and is reachable only
out-of-process, from the scenario and determinism suites (rule R-1).
"""

from dataclasses import dataclass
from datetime import date
from typing import Final

from acas_posting import dates

__all__: Final[tuple[str, ...]] = (
    "TO_DAY_SEED",
    "PinnedRunDate",
    "pin_from_calendar_date",
    "pin_from_run_date",
    "pin_from_to_day",
    "verify_pin",
)


# ===========================================================================
#  THE SEED  [copybooks/Proc-ACAS-Mapser-RDB.cob:L73]
# ===========================================================================
#      move     "00/00/0000" to u-date.
#
#  THIS LITERAL IS WHERE THE SEPARATORS COME FROM, and that is the whole
#  reason it is a named constant rather than an f-string.
#
#  `u-date pic x(10)` carries a UK redefine [copybooks/wsmaps03.cob:L8-L15]:
#  `u-days` at 1:2, a filler "/" at 3, `u-month` at 4:2, a filler "/" at 6 and
#  `u-year` at 7:4. The three moves that follow the seed
#  [copybooks/Proc-ACAS-Mapser-RDB.cob:L74-L76] overwrite offsets 7-10, 4-5
#  and 1-2 only, so positions 3 and 6 keep the "/" the seed put there. THAT,
#  and nothing else, is why `to-day` comes out as DD/MM/CCYY.
#
#  It is textually identical to `maps04`'s own unpack seed
#  [common/maps04.cbl:L182], which acas_posting.dates publishes as
#  `UNPACK_SEED`, but it is a SEPARATE COBOL literal at a separate site in a
#  separate file. It is declared here rather than aliased from there so that a
#  reader tracing the DD/MM/CCYY form of `to-day` lands on L73, which is the
#  statement that actually produces it.
# ===========================================================================

#: The `"00/00/0000"` literal of [copybooks/Proc-ACAS-Mapser-RDB.cob:L73] - the
#: sole source of the two "/" separators in a pinned `to-day`.
TO_DAY_SEED: Final[str] = "00/00/0000"


# ===========================================================================
#  COBOL FIXED-WIDTH STORAGE SEMANTICS
# ===========================================================================
#  One helper, three lines, no business rule. `to-day` and `u-date` are both
#  PIC X(10) [general/general.cbl:L357], [copybooks/wsmaps03.cob:L7], and a
#  COBOL alphanumeric field is exactly its declared width at all times.
#
#  acas_posting.dates has an equivalent, but it is private there and reaching
#  into another module's private surface would be worse than restating three
#  lines of storage mechanics. The WIDTH is taken from that module's public
#  `DATE_TEXT_LENGTH` so the two cannot drift apart.
# ===========================================================================


def _move_to_date_text(source: str) -> str:
    """Reproduce a COBOL `MOVE` into a `PIC X(10)` date field.

    An alphanumeric move is left-justified: a short sending field is padded on
    the right with spaces and a long one is truncated on the right. The
    receiving field is always exactly `dates.DATE_TEXT_LENGTH` characters
    afterwards, because a COBOL `PIC X(10)` field always is.

    This is storage mechanics, not validation: nothing here inspects, rejects
    or normalises the characters it is given (rule R-3).
    """
    if len(source) >= dates.DATE_TEXT_LENGTH:
        return source[: dates.DATE_TEXT_LENGTH]
    return source + " " * (dates.DATE_TEXT_LENGTH - len(source))


# ===========================================================================
#  THE PINNED PAIR
# ===========================================================================


@dataclass(frozen=True)
class PinnedRunDate:
    """The two pinned observables, as one immutable value.

    Frozen because a pinned clock that could be edited after the fact would
    defeat the point of pinning it: once a run date has been fixed at the CLI
    boundary, nothing downstream may move it. Freezing also closes the pair at
    two fields, since assigning an undeclared attribute raises as well.

    DELIBERATELY NOT `slots=True`, and this should not be "tidied" back in.
    Measured on the target interpreter, CPython 3.12.13: with `frozen=True` and
    `slots=True` together, assigning an attribute that is NOT a declared field
    raises `TypeError: super(type, obj): obj must be an instance or subtype of
    type` instead of `FrozenInstanceError`, because `slots=True` rebuilds the
    class while the generated `__setattr__` still closes over the original one.
    The assignment fails either way, so immutability is not at stake - but the
    diagnostic a maintainer would meet after a simple typo becomes actively
    misleading. Frozen alone raises `FrozenInstanceError` for any name, declared
    or not, and the memory a slot layout would save is irrelevant for a value
    object built once per run.

    Attributes:
        to_day: `to-day pic x(10)` - the text date, DD/MM/CCYY. A linkage
            parameter [general/general.cbl:L357], never a column.
        run_date: `Run-Date binary-long` [copybooks/wssystem.cob:L67] - the
            binary day number counted from 1600-12-31, so day 1 is 1601-01-01.
            An `int`, never a binary floating-point value (rule R-2). This one IS
            a column, `SYSTEM-REC`.`RUN-DAT`, dictionary entry
            `SYSTEM-REC.RUN-DAT`, and therefore appears in every table dump the
            scenario diff compares.

    Serving the three linkage shapes. The COBOL call shapes do not agree on
    what a posting program receives, so a consumer takes only the fields its
    own shape declares:

        General Ledger, four parameters - `to-day` is the THIRD argument
            [general/general.cbl:L711-L721], [general/gl070.cbl:L245-L248].
            Takes `to_day`; `run_date` reaches the program inside the system
            record.
        Sales and Purchase, five parameters - `to-day` is the FOURTH argument
            [sales/sl060.cbl:L395-L399]. Same as above.
        IRS, three parameters - `call "irs030" using IRS-System-Params,
            WS-System-Record, file-defs` [irs/irs.cbl:L668-L672],
            [irs/irs030.cbl:L552-L554]. There is NO `to-day` parameter and no
            calling-data block either, so acas_posting.cli.irs_post reads
            `run_date` alone and never touches `to_day`. Nothing here invents a
            text date the COBOL does not pass.

    Constructed directly, this class validates nothing and holds whatever pair
    it is given, exactly as the two COBOL fields do (rule R-3). Use the three
    `pin_from_*` constructors to get a pair the specification itself derived.

    """

    to_day: str
    run_date: int

    @property
    def calendar_date(self) -> date | None:
        """The pinned day number as a `datetime.date`, or None if there is not one.

        A convenience for Python callers, derived from `run_date` rather than
        by parsing `to_day`, so that no text parsing and therefore no new
        validation enters this module (rule R-3).

        None when `run_date` falls outside the day-number domain of
        `FUNCTION Date-of-integer`, 1 through 3067671 - which is exactly the
        case a rejected date leaves behind, `run_date = 0`. None rather than a
        date, because `dates.date_of_integer(0)` would return 1600-12-31 and
        that would be a fabrication: the specification's own calendar check
        rejects 16001231 [common/maps04.cbl:L153], as
        `dates.test_date_yyyymmdd` records from the compiled intrinsic. A
        rejected date has no calendar date, and saying so is more honest than
        inventing the epoch's eve.
        """
        in_domain = (
            dates.COBOL_MIN_DATE_INTEGER
            <= self.run_date
            <= dates.COBOL_MAX_DATE_INTEGER
        )
        if in_domain:
            return dates.date_of_integer(self.run_date)
        return None


# ===========================================================================
#  FORWARD - TEXT TO BINARY  [copybooks/Proc-ACAS-Mapser-RDB.cob:L72-L80]
# ===========================================================================
#  The block being reproduced, verbatim:
#
#      72      move     function current-date to wse-date-block.
#      73      move     "00/00/0000" to u-date.
#      74      move     wse-year  to u-year.
#      75      move     wse-month to u-month.
#      76      move     wse-days  to u-days.
#      77      move     u-date    to to-day.
#      78      move     zero      to u-bin.
#      79      call     "maps04" using maps03-ws.
#      80      move     u-bin  to run-date.
#
#  L72 is THE CLOCK READ, and it is the one statement of the nine that is NOT
#  reproduced: it is replaced by the injected argument, which is the entire
#  point of this module (rule R-6). `wse-date-block` [copybooks/wstime.cob:
#  L18-L22] receives `FUNCTION CURRENT-DATE` and exposes `wse-year pic 9(4)`,
#  `wse-month pic 99` and `wse-days pic 99`, so L74-L76 move zero-padded
#  fixed-width digit strings of four, two and two characters. That is what the
#  three writes below reproduce.
#
#  Straight-line: eight MOVEs and one CALL, no GO TO, no taxonomy class (R-5).
# ===========================================================================


def pin_from_calendar_date(calendar_date: date) -> PinnedRunDate:
    """Pin both observables from an injected calendar date.

    Reproduces [copybooks/Proc-ACAS-Mapser-RDB.cob:L72-L80] with its L72 clock
    read replaced by `calendar_date`. This is the primary entry point: a
    scenario pins its run date once, here, and every migrated program then
    receives it through linkage exactly as the COBOL does.

    Args:
        calendar_date: the run date to pin. INJECTED - there is no default and
            no fallback to the system clock (rule R-6).

    Returns:
        The pinned pair. `run_date` is 0 if the specification rejects the date,
        which happens for any year before 1601: `FUNCTION Test-Date-YYYYMMDD`
        rejects 16001231 and everything earlier [common/maps04.cbl:L153], as
        `dates.test_date_yyyymmdd` records. No exception is raised in that case
        - see the module docstring and the pre-zero comment below.

    Example:
        >>> pin_from_calendar_date(date(2025, 9, 21))
        PinnedRunDate(to_day='21/09/2025', run_date=155127)

    """
    #  `maps03-ws` [copybooks/wsmaps03.cob:L6-L30] is WORKING-STORAGE in the
    #  COBOL and is passed to `maps04` by reference. A fresh record per call is
    #  the deliberate choice: a module-level one would be shared mutable state,
    #  which rule R-3 forbids and rule R-6 would make dangerous, since the
    #  result of one call could then depend on a previous one.
    work = dates.Maps03Ws()

    #  [L73] move "00/00/0000" to u-date.  THE SEED - the separators come from
    #  here and from nowhere else. See TO_DAY_SEED above.
    work.u_date = TO_DAY_SEED

    #  [L74-L76] the three component writes, IN THE COBOL'S OWN ORDER: year,
    #  then month, then days. The order has no effect on the result - each
    #  write lands on its own bytes - but it is reproduced as written for
    #  traceability (rule R-5). Each value is rendered at the width of the
    #  sending field: `wse-year pic 9(4)`, `wse-month pic 99`, `wse-days
    #  pic 99` [copybooks/wstime.cob:L20-L22], which is what gives 2025-01-05
    #  its two-digit day and month.
    work.u_year = f"{calendar_date.year:04d}"  # [L74] -> offset 7, length 4
    work.u_month = f"{calendar_date.month:02d}"  # [L75] -> offset 4, length 2
    work.u_days = f"{calendar_date.day:02d}"  # [L76] -> offset 1, length 2

    #  [L77] move u-date to to-day.  A COPY, not an alias: from here on the two
    #  ten-character values are independent, and this one is taken BEFORE
    #  `maps04` runs at L79 - which matters, because `maps04` rewrites the
    #  caller's text in place [common/maps04.cbl:L132-L134].
    to_day = work.u_date

    # -----------------------------------------------------------------------
    #  [copybooks/Proc-ACAS-Mapser-RDB.cob:L78]  move zero to u-bin.
    #
    #  ANOMALY #16, ITS MASKING MECHANISM REPRODUCED (rule R-4). This is NOT
    #  defensive initialisation and it must not be removed on the grounds that
    #  the date about to be converted is obviously valid.
    #
    #  `maps04` leaves its binary field COMPLETELY UNTOUCHED on both of its
    #  reject paths [common/maps04.cbl:L146] and [common/maps04.cbl:L154],
    #  while its own remarks claim "Date errors returned as A-Bin equal zero"
    #  [common/maps04.cbl:L163]. The documented contract therefore holds ONLY
    #  because callers zero the field first, and this statement is one of the
    #  two sites in the whole system that do so. Delete it and a rejected date
    #  would return whatever happened to be in the field - which is exactly
    #  what the compiled program was measured doing when the field was pre-set
    #  to -999.
    # -----------------------------------------------------------------------
    work.u_bin = 0

    #  [L79] call "maps04" using maps03-ws.  The conversion lives in exactly
    #  one place, acas_posting.dates, which reproduces common/maps04.cbl in
    #  full - including the epoch. The ordinal is never computed here
    #  (rules R-1 and R-5).
    dates.maps04(work)

    #  [L80] move u-bin to run-date.  UNCONDITIONAL. The COBOL does not test
    #  the result before storing it, so neither does this: a rejected date
    #  stores the 0 the pre-zero left behind, and raising instead would be a
    #  new validation (rule R-3).
    return PinnedRunDate(to_day=to_day, run_date=work.u_bin)


def pin_from_to_day(to_day: str) -> PinnedRunDate:
    """Pin both observables from caller-supplied `to-day` text.

    The same forward conversion as `pin_from_calendar_date`
    [copybooks/Proc-ACAS-Mapser-RDB.cob:L73-L80], entered from text instead of
    from date components: the analogue of a COBOL `move <text> to u-date`
    ahead of L77. This is the function a CLI `--run-date` option calls;
    argument binding itself belongs to acas_posting.cli.args, so there is no
    argparse here.

    THE TEXT IS NOT PRE-VALIDATED (rule R-3). Nothing here inspects it, and no
    regex, `int()` conversion, `strptime` or try/except decides its fate:
    `maps04` alone judges it, with its own six-part test
    [common/maps04.cbl:L140-L146] and its own calendar check
    [common/maps04.cbl:L153]. Validating first would reject dates the
    specification accepts, because that six-part test is looser than it looks -
    it never checks the year within the century for NUMERIC at all.

    Args:
        to_day: the date text, canonically DD/MM/CCYY. Stored at the declared
            `PIC X(10)` width, so shorter text is padded with spaces on the
            right and longer text is truncated. Separators may also be ".", ","
            or "-": `maps04` normalises those to "/" itself
            [common/maps04.cbl:L132-L134], which is why `run_date` is derived
            correctly from "21-09-2025".

    Returns:
        The pinned pair, with `run_date = 0` if `maps04` rejects the text. Never
        raises: "31/02/2025" passes the six-part test, fails the calendar check
        and yields 0; "rubbish" fails the six-part test and yields 0 too.

        `to_day` is the text AS SUPPLIED, padded to ten characters - NOT the
        normalised form. That is faithful rather than convenient: L77 copies
        `u-date` into `to-day` BEFORE L79 calls `maps04`, so the copy predates
        the separator rewrite. Pin from "21-09-2025" and the pair is
        ('21-09-2025', 155127), with the hyphens preserved in the text and the
        binary derived from the normalised form - exactly the pair the COBOL
        block produces from that input.

    Example:
        >>> pin_from_to_day("21/09/2025")
        PinnedRunDate(to_day='21/09/2025', run_date=155127)
        >>> pin_from_to_day("31/02/2025").run_date
        0

    """
    work = dates.Maps03Ws()

    #  `move <text> to u-date` - an alphanumeric move into a PIC X(10) field.
    #  The seed at L73 is not used on this path: the caller's text supplies all
    #  ten characters, separators included.
    work.u_date = _move_to_date_text(to_day)

    #  [L77] move u-date to to-day.  Before the conversion, as above.
    pinned_to_day = work.u_date

    #  [L78] move zero to u-bin.  ANOMALY #16's masking mechanism again, and
    #  load-bearing here in a way it is not on the calendar-date path, because
    #  this is the path that actually receives rejectable text. Without it a
    #  rejected date would return the field's previous content
    #  [common/maps04.cbl:L146], [common/maps04.cbl:L154]; with it, 0 - which
    #  is what [copybooks/Proc-ACAS-Mapser-RDB.cob:L78] guarantees and what
    #  [common/maps04.cbl:L163] merely claims (rule R-4).
    work.u_bin = 0

    #  [L79] call "maps04" using maps03-ws.
    dates.maps04(work)

    #  [L80] move u-bin to run-date.  Unconditional, as the COBOL stores it.
    return PinnedRunDate(to_day=pinned_to_day, run_date=work.u_bin)


# ===========================================================================
#  REVERSE - BINARY TO TEXT  [general/general.cbl:L465-L467]
# ===========================================================================
#  The block being reproduced, verbatim:
#
#     465      move     run-date to u-bin.
#     466      call     "maps04" using maps03-ws.
#     467      move     u-date   to to-day.
#
#  This is the direction normal menu operation actually uses, and it is the
#  mirror image of the forward block: the BINARY is authoritative, having been
#  read from the system record, and the TEXT is derived from it by `maps04`'s
#  unpack path [common/maps04.cbl:L181-L186]. Verified against the shell: L467
#  is the ONLY write to `to-day` anywhere in general.cbl, and `run-date` is
#  never written there at all.
#
#  There is no pre-zero on this path, and none is invented: `maps04` writes
#  `u-date` unconditionally on the unpack path, seeding it from its own
#  "00/00/0000" literal [common/maps04.cbl:L182] before filling CCYY, MM and
#  DD - which is why the reverse direction also yields DD/MM/CCYY.
#
#  Straight-line: two MOVEs and one CALL, no GO TO, no taxonomy class (R-5).
# ===========================================================================


def pin_from_run_date(run_date: int) -> PinnedRunDate:
    """Pin both observables from an injected binary `Run-Date`.

    Reproduces [general/general.cbl:L465-L467]. Use this when the day number is
    the authoritative value - which is the normal case, because `Run-Date` is a
    column of the system record and arrives from the database.

    Args:
        run_date: the binary day number, counted from 1600-12-31 so that day 1
            is 1601-01-01. INJECTED, like every input to this module (R-6).

    Returns:
        The pinned pair, with `to_day` derived through `maps04`'s unpack path.

    THE `> zero` SWITCH, AND THE BOUNDARY IT CREATES. `maps04` selects its
    direction with `if A-Bin > zero` [common/maps04.cbl:L128-L129] - strictly
    greater, not "not equal" - even though its own comment two lines earlier
    describes the test as "not zero" [common/maps04.cbl:L125-L126]. So:

        run_date > 0
            The unpack path runs and `to_day` is the converted text. An
            out-of-domain day number does not raise: the compiled intrinsic
            returns zero for anything past 3067671, so the text comes back as
            the seed's own "00/00/0000", which acas_posting.dates reproduces
            from measurement.
        run_date <= 0
            The FORWARD path runs instead, on a date field the shell has not
            filled, so the text is rejected and `run_date` is returned
            unchanged - 0 stays 0 and a negative stays negative, since there is
            no pre-zero on this path to mask it. `to_day` is then whatever that
            field held, and this function models a freshly initialised
            `maps03-ws`, whose `u-date` is ten spaces. That modelling choice is
            stated rather than hidden, and it is unreachable in practice: the
            menu only reaches L465 once a seeded system record has supplied a
            positive day number, having branched away entirely when the cycle
            is zero [general/general.cbl:L462-L463].

    Example:
        >>> pin_from_run_date(155127)
        PinnedRunDate(to_day='21/09/2025', run_date=155127)

    """
    #  A fresh record per call, for the same reason as on the forward path: no
    #  shared mutable state, so no call can be influenced by a previous one.
    work = dates.Maps03Ws()

    #  [L465] move run-date to u-bin.
    work.u_bin = run_date

    #  [L466] call "maps04" using maps03-ws.  Takes the unpack path for a
    #  positive day number and the forward path otherwise, per the switch
    #  documented above.
    dates.maps04(work)

    #  [L467] move u-date to to-day.  The text is the DERIVED value here, and
    #  `u_bin` is carried through unchanged: the unpack path never writes it.
    return PinnedRunDate(to_day=work.u_date, run_date=work.u_bin)


# ===========================================================================
#  THE CONSISTENCY CHECK - A DIAGNOSTIC, NOT A REPRODUCTION
# ===========================================================================
#  Nothing below corresponds to any COBOL statement. No COBOL site checks that
#  the two observables agree - [copybooks/Proc-ACAS-Mapser-RDB.cob:L80] stores
#  the conversion result without inspecting it - so this function is a
#  verification aid for the determinism and scenario suites, and it is kept
#  clearly separate from the reproductions above for exactly that reason.
#
#  Being a diagnostic and not a migrated path, it is permitted to raise. Rule
#  R-3's prohibition on new validation binds the reproductions; it does not
#  require a test helper to stay silent about an inconsistent pair.
# ===========================================================================


def verify_pin(pin: PinnedRunDate) -> None:
    """Check that a pinned pair's text and binary agree. DIAGNOSTIC ONLY.

    Reproduces no COBOL path - see the section comment above. Provided for
    tests/determinism/test_two_runs_byte_identical.py and the scenario suites,
    which need to assert that a pin handed to a run is internally consistent
    before trusting a diff taken after it.

    Both directions are exercised, and each is judged by `maps04` itself rather
    than by re-implemented rules here:

        1. FORWARD - the text is converted the way
           [copybooks/Proc-ACAS-Mapser-RDB.cob:L73-L80] converts it, pre-zero
           included, and the resulting day number must equal `run_date`.
        2. REVERSE - `run_date` is unpacked the way
           [general/general.cbl:L465-L467] unpacks it, and the resulting text
           must equal the text the forward step produced.

    Step 2 compares against the text as `maps04` NORMALISED it in step 1, not
    against `pin.to_day` directly. That is deliberate: `maps04` rewrites ".",
    "," and "-" separators to "/" in place [common/maps04.cbl:L132-L134], so a
    pin legitimately built from "21-09-2025" is consistent even though the
    unpacked form is "21/09/2025". Taking the comparison text from step 1 lets
    the specification's own normalisation settle that, instead of this function
    re-inventing it.

    Args:
        pin: the pair to check.

    Raises:
        ValueError: if the text does not convert to `run_date`; if `run_date` is
            not a day number the unpack path can convert, which is the case for
            the 0 a rejected date leaves behind; or if unpacking `run_date` does
            not reproduce the text.

    """
    #  Step 1 - the forward conversion, pre-zero included so that a rejected
    #  text yields 0 here exactly as it does in the constructors.
    forward = dates.Maps03Ws()
    forward.u_date = _move_to_date_text(pin.to_day)
    forward.u_bin = 0
    dates.maps04(forward)

    if forward.u_bin != pin.run_date:
        raise ValueError(
            f"pinned pair is inconsistent: to_day {pin.to_day!r} converts to "
            f"run_date {forward.u_bin} through maps04, but the pin carries "
            f"{pin.run_date}"
        )

    #  `maps04` selects the unpack path on `> zero` only
    #  [common/maps04.cbl:L128-L129], so a non-positive day number cannot be
    #  converted back to text and the pair is not round-trippable. Nought is
    #  the value a date the specification rejected leaves behind, once the
    #  pre-zero has masked anomaly #16, so this is the branch an unusable pin
    #  arrives at.
    if pin.run_date <= 0:
        raise ValueError(
            f"pinned pair is not usable as a controlled clock: run_date "
            f"{pin.run_date} is not a day number maps04 can unpack, so the "
            f"specification rejected to_day {pin.to_day!r} (a rejected date "
            f"leaves run_date at 0 - see anomaly #16)"
        )

    #  Step 2 - the reverse conversion, compared against step 1's normalised
    #  text for the reason given in the docstring.
    reverse = dates.Maps03Ws()
    reverse.u_bin = pin.run_date
    dates.maps04(reverse)

    if reverse.u_date != forward.u_date:
        raise ValueError(
            f"pinned pair is inconsistent: run_date {pin.run_date} unpacks to "
            f"{reverse.u_date!r}, but to_day {pin.to_day!r} normalises to "
            f"{forward.u_date!r}"
        )
