"""The controlled clock: the one boundary at which a run date enters the cycle.

Pins both observables the cycle can see - the text date `to-day pic x(10)` in
DD/MM/CCYY form and the binary `Run-Date` [copybooks/wssystem.cob:L67] - from a
single injected value, reproducing the menu shell's date block
[copybooks/Proc-ACAS-Mapser-RDB.cob:L72-L80] with the clock read replaced by an
argument.

Nothing here reads a clock: the date is injected, no default resolves to "now",
and none of the twelve migrated posting programs contains a clock read at all -
each receives the date through linkage. Pinning at this boundary is therefore
sufficient to make two runs of one scenario byte-identical, which is what R-6
requires.

Published: TO_DAY_SEED, PinnedRunDate, pin_from_calendar_date, pin_from_to_day,
pin_from_run_date, verify_pin.
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


# This literal is where the separators of `to-day` come from, and the reason it
# is a named constant: the three moves that follow it
# [copybooks/Proc-ACAS-Mapser-RDB.cob:L74-L76] overwrite offsets 7-10, 4-5 and
# 1-2 only, so positions 3 and 6 keep the "/" the seed put there.

TO_DAY_SEED: Final[str] = "00/00/0000"


# One helper, no business rule.


def _move_to_date_text(source: str) -> str:
    """Reproduce a COBOL `MOVE` into a `PIC X(10)` date field.

    An alphanumeric move is left-justified: a short sending field is padded on the right
    with spaces and a long one is truncated on the right.
    """
    if len(source) >= dates.DATE_TEXT_LENGTH:
        return source[: dates.DATE_TEXT_LENGTH]
    return source + " " * (dates.DATE_TEXT_LENGTH - len(source))


@dataclass(frozen=True)
class PinnedRunDate:
    """The two pinned observables, as one immutable value.

    Frozen because a pinned clock that could be edited afterwards would defeat the point
    of pinning it: once a run date is fixed at the CLI boundary nothing downstream may
    move it.

    Attributes:
        to_day: `to-day pic x(10)` - the text date, DD/MM/CCYY. A linkage parameter
            [general/general.cbl:L357], never a column.
        run_date: `Run-Date binary-long` [copybooks/wssystem.cob:L67] - the binary day
            number counted from 1600-12-31, so day 1 is 1601-01-01. An `int`, never a
            binary float (rule R-2).
    """

    to_day: str
    run_date: int

    @property
    def calendar_date(self) -> date | None:
        """The pinned day number as a `datetime.date`, or None if there is not one.

        A convenience for Python callers, derived from `run_date` rather than by parsing
        `to_day`, so no text parsing and therefore no new validation enters this module
        (rule R-3).
        """
        in_domain = (
            dates.COBOL_MIN_DATE_INTEGER
            <= self.run_date
            <= dates.COBOL_MAX_DATE_INTEGER
        )
        if in_domain:
            return dates.date_of_integer(self.run_date)
        return None


# FORWARD - TEXT TO BINARY [copybooks/Proc-ACAS-Mapser-RDB.cob:L72-L80]: 72 move
# function current-date to wse-date-block. 73 move "00/00/0000" to u-date. 74 move wse-
# year to u-year.


def pin_from_calendar_date(calendar_date: date) -> PinnedRunDate:
    """Pin both observables from an injected calendar date.

    Reproduces [copybooks/Proc-ACAS-Mapser-RDB.cob:L72-L80] with its L72 clock read
    replaced by `calendar_date`. This is the primary entry point: a scenario pins its
    run date once, here, and every migrated program then receives it through linkage
    exactly as the COBOL does.

    Args:
        calendar_date: the run date to pin. INJECTED - there is no default and no
            fallback to the system clock (rule R-6).

    Returns:
        The pinned pair.
    """
    # `maps03-ws` [copybooks/wsmaps03.cob:L6-L30] is WORKING-STORAGE in the COBOL and is
    # passed to `maps04` by reference. A fresh record per call is the deliberate choice.
    work = Maps03Ws()

    work.u_date = TO_DAY_SEED

    # [L74-L76] the three component writes, IN THE COBOL'S OWN ORDER: year, then month,
    # then days.
    dates.set_reading_field(work, "u-year", f"{calendar_date.year:04d}")
    dates.set_reading_field(work, "u-month", f"{calendar_date.month:02d}")
    dates.set_reading_field(work, "u-days", f"{calendar_date.day:02d}")

    # [L77] move u-date to to-day. A COPY, not an alias.
    to_day = work.u_date

# [copybooks/Proc-ACAS-Mapser-RDB.cob:L78] move zero to u-bin. ANOMALY #16, ITS MASKING
# MECHANISM REPRODUCED (rule R-4).
    work.u_bin = 0

    # [L79] call "maps04" using maps03-ws. The conversion lives in exactly one place,
    # acas_posting.dates, which reproduces common/maps04.cbl in full - including the
    # epoch.
    dates.maps04(work)

    # [L80] move u-bin to run-date. UNCONDITIONAL. The COBOL does not test the result
    # before storing it, so neither does this.
    return PinnedRunDate(to_day=to_day, run_date=work.u_bin)


def pin_from_to_day(to_day: str) -> PinnedRunDate:
    """Pin both observables from caller-supplied `to-day` text.

    THE TEXT IS NOT PRE-VALIDATED (rule R-3). Nothing here inspects it, and no regex,
    `int()` conversion, `strptime` or try/except decides its fate: `maps04` alone judges
    it, with its own six-part test [common/maps04.cbl:L140-L146] and its own calendar
    check [common/maps04.cbl:L153].

    Args:
        to_day: the date text, canonically DD/MM/CCYY.

    Returns:
        The pinned pair, with `run_date = 0` if `maps04` rejects the text. Never raises:
            "31/02/2025" passes the six-part test, fails the calendar check and yields
            0.
    """
    work = Maps03Ws()

    work.u_date = _move_to_date_text(to_day)

    pinned_to_day = work.u_date

# [L78] move zero to u-bin.
    work.u_bin = 0

    dates.maps04(work)

    return PinnedRunDate(to_day=pinned_to_day, run_date=work.u_bin)


# REVERSE - BINARY TO TEXT [general/general.cbl:L465-L467], verbatim: 465 move run-date
# to u-bin. 466 call "maps04" using maps03-ws. 467 move u-date to to-day.


def pin_from_run_date(run_date: int) -> PinnedRunDate:
    """Pin both observables from an injected binary `Run-Date`.

    Reproduces [general/general.cbl:L465-L467]. Use this when the day number is the
    authoritative value - the normal case, because `Run-Date` is a column of the system
    record and arrives from the database.

    Args:
        run_date: the binary day number, counted from 1600-12-31 so that day 1 is
            1601-01-01. INJECTED, like every input to this module (rule R-6).

    Returns:
        The pinned pair, with `to_day` derived through `maps04`'s unpack path. An out-
            of-domain day number does not raise.
    """
    work = Maps03Ws()

    work.u_bin = run_date

    # [L466] call "maps04" using maps03-ws. Takes the unpack path for a positive day
    # number and the forward path otherwise, per the switch documented above.
    dates.maps04(work)

    # [L467] move u-date to to-day. The text is the DERIVED value here, and `u_bin` is
    # carried through unchanged: the unpack path never writes it.
    return PinnedRunDate(to_day=work.u_date, run_date=work.u_bin)


# Nothing below corresponds to any COBOL statement: no COBOL site checks that the two
# observables agree, since [copybooks/Proc-ACAS-Mapser-RDB.cob:L80] stores the
# conversion result without inspecting it.


def verify_pin(pin: PinnedRunDate) -> None:
    """Check that a pinned pair's text and binary agree. DIAGNOSTIC ONLY.

    Reproduces no COBOL path - see the section comment above. It exists so that a caller
    about to trust a diff can first assert that the pin handed to the run is internally
    consistent.

    Args:
        pin: the pair to check.

    Raises:
        ValueError: if the text does not convert to `run_date`.
    """
    # Step 1 - the forward conversion, pre-zero included so that a rejected text yields
    # 0 here exactly as it does in the constructors.
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

# `maps04` selects the unpack path on `> zero` only [common/maps04.cbl:L128-L129], so a
# non-positive day number cannot be converted back to text and the pair is not round-
# trippable.
    if pin.run_date <= 0:
        raise ValueError(
            f"pinned pair is not usable as a controlled clock: run_date "
            f"{pin.run_date} is not a day number maps04 can unpack, so the "
            f"specification rejected to_day {pin.to_day!r} (a rejected date "
            f"leaves run_date at 0 - see anomaly #16)"
        )

    reverse = Maps03Ws()
    reverse.u_bin = pin.run_date
    dates.maps04(reverse)

    if reverse.u_date != forward.u_date:
        raise ValueError(
            f"pinned pair is inconsistent: run_date {pin.run_date} unpacks to "
            f"{reverse.u_date!r}, but to_day {pin.to_day!r} normalises to "
            f"{forward.u_date!r}"
        )
