"""The controlled clock: the one boundary at which a run date enters the cycle.

Pins both observables - the text date and the binary run date - from a single
injected value. The source of truth is the date read in the menu shell
[copybooks/Proc-ACAS-Mapser-RDB.cob:L72-L80]; this module reproduces that block
with the clock read replaced by an argument, which is what makes two runs of
one scenario byte-identical. Rule R-6 forces the file into scope.

THIS MODULE NEVER READS A CLOCK
The date is INJECTED. Every function takes it as an argument and no default
resolves to "now" - not a convenience one, not one behind a flag, not one in a
test hook. Nothing here consults a system clock, an elapsed-time counter, the
environment, the host or user name, or an entropy source, so the output for a
given input is identical across runs and processes. Those absences are
mechanically greppable, and the prose above is worded to avoid the names it
disclaims so that the grep stays useful.

THE TWO OBSERVABLES, AND ONLY TWO
    to-day pic x(10)   the text date, DD/MM/CCYY. A LINKAGE parameter, not a
        column: `01 to-day pic x(10).` at [general/general.cbl:L357],
        [general/gl070.cbl:L243] and [irs/irs.cbl:L405]. Third argument of the
        General Ledger shape [general/gl070.cbl:L245-L248], fourth of the Sales
        and Purchase shape [sales/sl060.cbl:L395-L399].
    Run-Date binary-long   [copybooks/wssystem.cob:L67] the binary day number,
        signed 32-bit of scale zero, so a Python `int` and never a binary float
        (rule R-2). This one IS a column - `SYSTEM-REC`.`RUN-DAT`,
        `int(8) unsigned NOT NULL`, dictionary key `SYSTEM-REC.RUN-DAT`, note
        RUN-DAT and not RUN-DATE - so it is diff-visible in every scenario.
        The signed-to-unsigned narrowing at the bridge
        [common/systemMT.cbl:L336] belongs to the handler module that owns that
        boundary, not here; a pinned day number is handed over exactly as the
        COBOL computed it.

THE EPOCH  [common/maps04.cbl:L167]
The day number counts from 1600-12-31, so day 1 is 1601-01-01. It is neither a
Unix timestamp nor a Python ordinal. The maintainer flags the epoch himself:
"THIS uses binary Dates from 31/12/1600 so is NOT usable within IRS as is"
[common/maps04.cbl:L39-L41]. The conversion is not reimplemented here - it
lives in exactly one place, `acas_posting.dates`.

BOTH DIRECTIONS ARE REAL
    forward, text to binary [copybooks/Proc-ACAS-Mapser-RDB.cob:L72-L80] -
        `pin_from_calendar_date`, and from caller text `pin_from_to_day`.
    reverse, binary to text [general/general.cbl:L465-L467] - in normal menu
        operation the binary is authoritative, read from the system record, and
        the text is derived from it. L467 is the only write to `to-day` in that
        shell and `run-date` is never written there. `pin_from_run_date`.

A REJECTED DATE YIELDS Run-Date = 0, NOT AN EXCEPTION  (rules R-3 and R-4)
`maps04` leaves its binary field untouched on either reject path
[common/maps04.cbl:L146], [common/maps04.cbl:L154], although its own remarks
claim "Date errors returned as A-Bin equal zero" [common/maps04.cbl:L163]. The
documented contract holds only because callers zero the field first, and
[copybooks/Proc-ACAS-Mapser-RDB.cob:L78] is one of the two sites that do. That
pre-zero is the masking mechanism of a legacy defect, not boilerplate, so it is
reproduced at each forward site with its locator. A rejected injected date
therefore comes back as `run_date = 0` and raises nothing:
[copybooks/Proc-ACAS-Mapser-RDB.cob:L80] stores the result unconditionally
without inspecting it. Raising, or validating the text first, would be a new
validation that rule R-3 forbids.

THE CLOCK-READ CENSUS
The plan describes [copybooks/Proc-ACAS-Mapser-RDB.cob:L72-L80] as the single
read in the whole call chain. A reader who greps finds fourteen ambient date and
time reads across six files - six `FUNCTION CURRENT-DATE`
(common/ACAS.cbl:L353, general/general.cbl:L371, sales/sales.cbl:L323,
purchase/purchase.cbl:L318, irs/irs.cbl:L480,
copybooks/Proc-ACAS-Mapser-RDB.cob:L72), four `ACCEPT ... FROM DATE`
(common/ACAS.cbl:L478, general/general.cbl:L559, sales/sales.cbl:L528,
purchase/purchase.cbl:L522) and four `ACCEPT ... FROM TIME` (common/ACAS.cbl:L470,
general/general.cbl:L551, sales/sales.cbl:L520, purchase/purchase.cbl:L514) - so
the exact census is recorded here rather than left to surprise them. The plan's
conclusion nevertheless holds, and it is the conclusion that matters: every one
of those sites is in an out-of-scope menu shell or in the shared date-service
copybook the shells COPY, and none of the twelve in-scope posting programs reads
a clock at all. The eight `ACCEPT` reads feed the menu's screen banner only - in
the General Ledger shell they run at L551 and L559, after L467 has already
copied `to-day`. Pinning the two observables at the CLI boundary is sufficient.

WHAT IS DELIBERATELY NOT HERE
Two constructors, one value object and one diagnostic check is the whole
module. No `Clock` protocol or abstract base, no production-versus-test
implementation pair, no monkeypatch hook, no time-provider registry, no global
mutable current-clock singleton, no time zone and no time of day - no in-scope
field has one. Presentation format is not switched either: `Date-Form` and its
condition names [copybooks/wssystem.cob:L128-L132] belong to the `zz050`,
`zz060` and `zz070` reformatters in `acas_posting.dates`, and this module
produces the canonical DD/MM/CCYY `to-day` and nothing else. Nor does it parse
`argv`; `pin_from_to_day` is the plain function a `--run-date` option calls.

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
`cli/*.py` may import this module. This module imports the standard library,
`acas_posting.dates` and the ONE record class its COBOL source copies, and
nothing else: not `dal`, not `programs`, not `cli`, not `cobol`, not
`dictionary`, and never the compiled oracle tree, which is a top-level sibling
of this package and is reachable only out-of-process, from the scenario and
determinism suites (rule R-1).

That record class is `Maps03Ws`, and the import is the plan's own mandated
translation of the `COPY` its source carries (Agent Action Plan section 0.4.3):

    FROM:  copy "wsmaps03.cob".
    TO:    from acas_posting.records.maps03 import Maps03Ws

The section this module migrates passes `maps03-ws` to `maps04`
[copybooks/Proc-ACAS-Mapser-RDB.cob:L78-L79], so it copies that copybook and
gets that class - the same one `dates` operates on. There is exactly one Python
class for `maps03-ws` and both modules use it. That record layer is a leaf which
reaches only `cobol.field` and `dictionary.loader`, so the edge drags in nothing
else.
"""

from dataclasses import dataclass
from datetime import date
from typing import Final

from acas_posting import dates
from acas_posting.records.maps03 import Maps03Ws

__all__: Final[tuple[str, ...]] = (
    "TO_DAY_SEED",
    "PinnedRunDate",
    "pin_from_calendar_date",
    "pin_from_run_date",
    "pin_from_to_day",
    "verify_pin",
)


#  THE SEED  [copybooks/Proc-ACAS-Mapser-RDB.cob:L73]  move "00/00/0000" to
#  u-date.  THIS LITERAL IS WHERE THE SEPARATORS COME FROM, which is the whole
#  reason it is a named constant rather than an f-string. `u-date pic x(10)`
#  carries a UK redefine [copybooks/wsmaps03.cob:L8-L15]: `u-days` at 1:2, a
#  filler "/" at 3, `u-month` at 4:2, a filler "/" at 6 and `u-year` at 7:4.
#  The three moves that follow [copybooks/Proc-ACAS-Mapser-RDB.cob:L74-L76]
#  overwrite offsets 7-10, 4-5 and 1-2 only, so positions 3 and 6 keep the "/"
#  the seed put there. That, and nothing else, is why `to-day` is DD/MM/CCYY.
#  It is textually identical to `maps04`'s own unpack seed
#  [common/maps04.cbl:L182] but is a separate literal at a separate site, and is
#  declared here so a reader tracing the form of `to-day` lands on L73.

#: The `"00/00/0000"` literal of [copybooks/Proc-ACAS-Mapser-RDB.cob:L73] - the
#: sole source of the two "/" separators in a pinned `to-day`.
TO_DAY_SEED: Final[str] = "00/00/0000"


#  COBOL FIXED-WIDTH STORAGE SEMANTICS
#  One helper, no business rule. `to-day` and `u-date` are both PIC X(10)
#  [general/general.cbl:L357], [copybooks/wsmaps03.cob:L7], and a COBOL
#  alphanumeric field is exactly its declared width at all times. The width is
#  taken from `dates.DATE_TEXT_LENGTH` so the two cannot drift apart.


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


#  THE PINNED PAIR


@dataclass(frozen=True)
class PinnedRunDate:
    """The two pinned observables, as one immutable value.

    Frozen because a pinned clock that could be edited afterwards would defeat the
    point of pinning it: once a run date is fixed at the CLI boundary nothing
    downstream may move it. Freezing also closes the pair at two fields, since
    assigning an undeclared attribute raises as well.

    DELIBERATELY NOT `slots=True`, and this should not be "tidied" back in. With
    `frozen=True` and `slots=True` together, assigning an attribute that is not a
    declared field raises `TypeError` rather than `FrozenInstanceError`, because
    `slots=True` rebuilds the class while the generated `__setattr__` still closes
    over the original one. The assignment fails either way, so immutability is not
    at stake - but the diagnostic a maintainer meets after a typo becomes
    misleading. Frozen alone raises `FrozenInstanceError` for any name, and the
    memory a slot layout would save is irrelevant for one value object per run.

    Serving the three linkage shapes. The COBOL call shapes disagree on what a
    posting program receives, so a consumer takes only the fields its own shape
    declares. General Ledger passes `to-day` third
    [general/gl070.cbl:L245-L248]; Sales and Purchase pass it fourth
    [sales/sl060.cbl:L395-L399]; the IRS shape has no `to-day` parameter and no
    calling-data block at all [irs/irs030.cbl:L552-L554], so its entry point reads
    `run_date` alone. Nothing here invents a text date the COBOL does not pass. In
    every shape `run_date` reaches the program inside the system record.

    Constructed directly this class validates nothing and holds whatever pair it is
    given, exactly as the two COBOL fields do (rule R-3). The three `pin_from_*`
    constructors return a pair the specification itself derived.

    Attributes:
        to_day: `to-day pic x(10)` - the text date, DD/MM/CCYY. A linkage
            parameter [general/general.cbl:L357], never a column.
        run_date: `Run-Date binary-long` [copybooks/wssystem.cob:L67] - the binary
            day number counted from 1600-12-31, so day 1 is 1601-01-01. An `int`,
            never a binary float (rule R-2). This one IS the column
            `SYSTEM-REC`.`RUN-DAT`, so it appears in every table dump the scenario
            diff compares.
    """

    to_day: str
    run_date: int

    @property
    def calendar_date(self) -> date | None:
        """The pinned day number as a `datetime.date`, or None if there is not one.

        A convenience for Python callers, derived from `run_date` rather than by
        parsing `to_day`, so no text parsing and therefore no new validation enters
        this module (rule R-3).

        None when `run_date` falls outside the day-number domain of
        `FUNCTION Date-of-integer`, 1 through 3067671 - which is exactly what a
        rejected date leaves behind, `run_date = 0`. None rather than a date, because
        `dates.date_of_integer(0)` would return 1600-12-31 and the specification's own
        calendar check rejects 16001231 [common/maps04.cbl:L153]. A rejected date has
        no calendar date, and saying so is more honest than inventing the epoch's eve.
        """
        in_domain = (
            dates.COBOL_MIN_DATE_INTEGER
            <= self.run_date
            <= dates.COBOL_MAX_DATE_INTEGER
        )
        if in_domain:
            return dates.date_of_integer(self.run_date)
        return None


#  FORWARD - TEXT TO BINARY  [copybooks/Proc-ACAS-Mapser-RDB.cob:L72-L80]:
#      72      move     function current-date to wse-date-block.
#      73      move     "00/00/0000" to u-date.
#      74      move     wse-year  to u-year.
#      75      move     wse-month to u-month.
#      76      move     wse-days  to u-days.
#      77      move     u-date    to to-day.
#      78      move     zero      to u-bin.
#      79      call     "maps04" using maps03-ws.
#      80      move     u-bin  to run-date.
#  L72 is THE CLOCK READ and the one statement of the nine NOT reproduced -
#  replaced by the injected argument, which is the whole point of this module.


def pin_from_calendar_date(calendar_date: date) -> PinnedRunDate:
    """Pin both observables from an injected calendar date.

    Reproduces [copybooks/Proc-ACAS-Mapser-RDB.cob:L72-L80] with its L72 clock read
    replaced by `calendar_date`. This is the primary entry point: a scenario pins
    its run date once, here, and every migrated program then receives it through
    linkage exactly as the COBOL does.

    Args:
        calendar_date: the run date to pin. INJECTED - there is no default and no
            fallback to the system clock (rule R-6).

    Returns:
        The pinned pair. `run_date` is 0 if the specification rejects the date,
        which happens for any year before 1601, since
        `FUNCTION Test-Date-YYYYMMDD` rejects 16001231 and everything earlier
        [common/maps04.cbl:L153]. No exception is raised - see the module
        docstring and the pre-zero comment below.

    Example:
        >>> pin_from_calendar_date(date(2025, 9, 21))
        PinnedRunDate(to_day='21/09/2025', run_date=155127)
    """
    #  `maps03-ws` [copybooks/wsmaps03.cob:L6-L30] is WORKING-STORAGE in the
    #  COBOL and is passed to `maps04` by reference. A fresh record per call is
    #  the deliberate choice: a module-level one would be shared mutable state,
    #  which rule R-3 forbids and rule R-6 would make dangerous, since the
    #  result of one call could then depend on a previous one.
    #
    #  THE canonical record - `acas_posting.records.maps03.Maps03Ws`, whose
    #  every field cites a generated dictionary entry (rule R-5). There is one
    #  class of that name in the package; `acas_posting.dates` re-exports this
    #  same object, so `dates.maps04` below receives exactly what it declares.
    work = Maps03Ws()

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
    #
    #  All three receivers are items of `u-UK`, the redefinition of `u-date`
    #  [copybooks/wsmaps03.cob:L8-L15], so they are written through the one
    #  accessor `dates` publishes for that reading rather than through a
    #  second record shape. Their offsets are DERIVED from the generated
    #  dictionary, not spelled here (rule R-5); the comments record what the
    #  derivation yields so this reads against the copybook.
    dates.set_reading_field(work, "u-year", f"{calendar_date.year:04d}")  # [L74] 7:4
    dates.set_reading_field(work, "u-month", f"{calendar_date.month:02d}")  # [L75] 4:2
    dates.set_reading_field(work, "u-days", f"{calendar_date.day:02d}")  # [L76] 1:2

    #  [L77] move u-date to to-day.  A COPY, not an alias: from here on the two
    #  ten-character values are independent, and this one is taken BEFORE
    #  `maps04` runs at L79 - which matters, because `maps04` rewrites the
    #  caller's text in place [common/maps04.cbl:L132-L134].
    to_day = work.u_date

#  [copybooks/Proc-ACAS-Mapser-RDB.cob:L78]  move zero to u-bin.
#  ANOMALY #16, ITS MASKING MECHANISM REPRODUCED (rule R-4). This is NOT
#  defensive initialisation and must not be removed on the grounds that the
#  date about to be converted is obviously valid. `maps04` leaves its binary
#  field untouched on both reject paths [common/maps04.cbl:L146],
#  [common/maps04.cbl:L154], while its own remarks claim "Date errors returned
#  as A-Bin equal zero" [common/maps04.cbl:L163]. The documented contract holds
#  ONLY because callers zero the field first, and this statement is one of the
#  two sites in the whole system that do so.
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
    [copybooks/Proc-ACAS-Mapser-RDB.cob:L73-L80], entered from text instead of from
    date components: the analogue of a COBOL `move <text> to u-date` ahead of L77.
    This is the function a CLI `--run-date` option calls; argument binding itself
    belongs to `acas_posting.cli.args`, so there is no argparse here.

    THE TEXT IS NOT PRE-VALIDATED (rule R-3). Nothing here inspects it, and no
    regex, `int()` conversion, `strptime` or try/except decides its fate: `maps04`
    alone judges it, with its own six-part test [common/maps04.cbl:L140-L146] and
    its own calendar check [common/maps04.cbl:L153]. Validating first would reject
    dates the specification accepts, because that six-part test is looser than it
    looks - it never checks the year within the century for NUMERIC at all.

    Args:
        to_day: the date text, canonically DD/MM/CCYY. Stored at the declared
            `PIC X(10)` width, so shorter text is padded with spaces on the right
            and longer text is truncated. Separators may also be ".", "," or "-":
            `maps04` normalises those to "/" itself [common/maps04.cbl:L132-L134],
            which is why `run_date` is derived correctly from "21-09-2025".

    Returns:
        The pinned pair, with `run_date = 0` if `maps04` rejects the text. Never
        raises: "31/02/2025" passes the six-part test, fails the calendar check and
        yields 0; "rubbish" fails the six-part test and yields 0 too.

        `to_day` is the text AS SUPPLIED, padded to ten characters - NOT the
        normalised form. That is faithful rather than convenient: L77 copies
        `u-date` into `to-day` BEFORE L79 calls `maps04`, so the copy predates the
        separator rewrite. Pin from "21-09-2025" and the pair is
        ('21-09-2025', 155127), which is what the COBOL block produces from that
        input.

    Example:
        >>> pin_from_to_day("21/09/2025")
        PinnedRunDate(to_day='21/09/2025', run_date=155127)
        >>> pin_from_to_day("31/02/2025").run_date
        0
    """
    #  The same canonical record as `pin_from_calendar_date` builds; see the
    #  note there.
    work = Maps03Ws()

    #  `move <text> to u-date` - an alphanumeric move into a PIC X(10) field.
    #  The seed at L73 is not used on this path: the caller's text supplies all
    #  ten characters, separators included.
    work.u_date = _move_to_date_text(to_day)

    #  [L77] move u-date to to-day.  Before the conversion, as above.
    pinned_to_day = work.u_date

#  [L78] move zero to u-bin.  ANOMALY #16's masking mechanism again, and
#  load-bearing here in a way it is not on the calendar-date path, because this
#  is the path that receives rejectable text. Without it a rejected date would
#  return the field's previous content [common/maps04.cbl:L146],
#  [common/maps04.cbl:L154]; with it, 0 - which is what
#  [copybooks/Proc-ACAS-Mapser-RDB.cob:L78] guarantees and what
#  [common/maps04.cbl:L163] merely claims (rule R-4).
    work.u_bin = 0

    #  [L79] call "maps04" using maps03-ws.
    dates.maps04(work)

    #  [L80] move u-bin to run-date.  Unconditional, as the COBOL stores it.
    return PinnedRunDate(to_day=pinned_to_day, run_date=work.u_bin)


#  REVERSE - BINARY TO TEXT  [general/general.cbl:L465-L467], verbatim:
#     465      move     run-date to u-bin.
#     466      call     "maps04" using maps03-ws.
#     467      move     u-date   to to-day.
#  The mirror image of the forward block, and the direction normal menu
#  operation uses: the BINARY is authoritative, read from the system record,
#  and the TEXT is derived from it by `maps04`'s unpack path
#  [common/maps04.cbl:L181-L186]. L467 is the only write to `to-day` anywhere in
#  general.cbl and `run-date` is never written there. No pre-zero on this path,
#  and none is invented: the unpack path writes `u-date` unconditionally,
#  seeding it from its own "00/00/0000" literal [common/maps04.cbl:L182] before
#  filling CCYY, MM and DD - which is why it too yields DD/MM/CCYY.


def pin_from_run_date(run_date: int) -> PinnedRunDate:
    """Pin both observables from an injected binary `Run-Date`.

    Reproduces [general/general.cbl:L465-L467]. Use this when the day number is the
    authoritative value - the normal case, because `Run-Date` is a column of the
    system record and arrives from the database.

    THE `> zero` SWITCH, AND THE BOUNDARY IT CREATES. `maps04` selects its
    direction with `if A-Bin > zero` [common/maps04.cbl:L128-L129] - strictly
    greater, not "not equal" - even though its own comment two lines earlier
    describes the test as "not zero" [common/maps04.cbl:L125-L126]. So a positive
    day number takes the unpack path and `to_day` is the converted text, while a
    non-positive one takes the FORWARD path instead, on a date field the shell has
    not filled: the text is rejected and `run_date` comes back unchanged, since
    there is no pre-zero on this path to mask it. `to_day` is then whatever that
    field held, and this function models a freshly initialised `maps03-ws`, whose
    `u-date` is ten spaces. That modelling choice is stated rather than hidden, and
    it is unreachable in practice - the menu only reaches L465 once a seeded system
    record has supplied a positive day number, having branched away entirely when
    the cycle is zero [general/general.cbl:L462-L463].

    Args:
        run_date: the binary day number, counted from 1600-12-31 so that day 1 is
            1601-01-01. INJECTED, like every input to this module (rule R-6).

    Returns:
        The pinned pair, with `to_day` derived through `maps04`'s unpack path. An
        out-of-domain day number does not raise: the intrinsic yields zero past
        3067671, so the text comes back as the seed's own "00/00/0000".

    Example:
        >>> pin_from_run_date(155127)
        PinnedRunDate(to_day='21/09/2025', run_date=155127)
    """
    #  A fresh record per call, for the same reason as on the forward path: no
    #  shared mutable state, so no call can be influenced by a previous one.
    work = Maps03Ws()

    #  [L465] move run-date to u-bin.
    work.u_bin = run_date

    #  [L466] call "maps04" using maps03-ws.  Takes the unpack path for a
    #  positive day number and the forward path otherwise, per the switch
    #  documented above.
    dates.maps04(work)

    #  [L467] move u-date to to-day.  The text is the DERIVED value here, and
    #  `u_bin` is carried through unchanged: the unpack path never writes it.
    return PinnedRunDate(to_day=work.u_date, run_date=work.u_bin)


#  THE CONSISTENCY CHECK - A DIAGNOSTIC, NOT A REPRODUCTION
#  Nothing below corresponds to any COBOL statement: no COBOL site checks that
#  the two observables agree, since [copybooks/Proc-ACAS-Mapser-RDB.cob:L80]
#  stores the conversion result without inspecting it. Being a diagnostic and
#  not a migrated path it is permitted to raise - rule R-3's prohibition on new
#  validation binds the reproductions, not a helper.


def verify_pin(pin: PinnedRunDate) -> None:
    """Check that a pinned pair's text and binary agree. DIAGNOSTIC ONLY.

    Reproduces no COBOL path - see the section comment above. It exists so that a
    caller about to trust a diff can first assert that the pin handed to the run is
    internally consistent.

    Both directions are exercised, and each is judged by `maps04` itself rather
    than by rules re-implemented here: the text is converted the way
    [copybooks/Proc-ACAS-Mapser-RDB.cob:L73-L80] converts it, pre-zero included,
    and must yield `run_date`; then `run_date` is unpacked the way
    [general/general.cbl:L465-L467] unpacks it, and must yield the same text.

    The second step compares against the text as `maps04` NORMALISED it in the
    first, not against `pin.to_day` directly. That is deliberate: `maps04` rewrites
    ".", "," and "-" separators to "/" in place [common/maps04.cbl:L132-L134], so a
    pin legitimately built from "21-09-2025" is consistent even though the unpacked
    form is "21/09/2025". Taking the comparison text from step one lets the
    specification's own normalisation settle that.

    Args:
        pin: the pair to check.

    Raises:
        ValueError: if the text does not convert to `run_date`; if `run_date` is not
            a day number the unpack path can convert, which is the case for the 0 a
            rejected date leaves behind; or if unpacking `run_date` does not
            reproduce the text.
    """
    #  Step 1 - the forward conversion, pre-zero included so that a rejected
    #  text yields 0 here exactly as it does in the constructors.
    forward = Maps03Ws()
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
#  converted back to text and the pair is not round-trippable. Nought is what a
#  date the specification rejected leaves behind, once the pre-zero has masked
#  anomaly #16, so this is the branch an unusable pin arrives at.
    if pin.run_date <= 0:
        raise ValueError(
            f"pinned pair is not usable as a controlled clock: run_date "
            f"{pin.run_date} is not a day number maps04 can unpack, so the "
            f"specification rejected to_day {pin.to_day!r} (a rejected date "
            f"leaves run_date at 0 - see anomaly #16)"
        )

    #  Step 2 - the reverse conversion, compared against step 1's normalised
    #  text for the reason given in the docstring.
    reverse = Maps03Ws()
    reverse.u_bin = pin.run_date
    dates.maps04(reverse)

    if reverse.u_date != forward.u_date:
        raise ValueError(
            f"pinned pair is inconsistent: run_date {pin.run_date} unpacks to "
            f"{reverse.u_date!r}, but to_day {pin.to_day!r} normalises to "
            f"{forward.u_date!r}"
        )
