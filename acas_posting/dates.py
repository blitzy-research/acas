"""Date validation and conversion - the Python migration of common/maps04.cbl.

This module is the whole of the ACAS date logic that the batch posting cycle
reaches. It is a REIMPLEMENTATION of the COBOL, never a call into it, and it
carries two distinct bodies of code that the COBOL keeps in two places:

  1. `common/maps04.cbl` itself - 189 lines, a CALLed sub-program that converts
     a 10-character UK date text to and from a binary day number. Reproduced
     here statement for statement as `maps04` plus `ws_unpack`.

  2. The four date SECTIONS that the in-scope posting programs each carry a
     private copy of - `zz050-Validate-Date`, `zz060-Convert-Date`,
     `zz070-Convert-Date` and the thin wrapper section around the `CALL`.

NO COBOL AT RUNTIME  (rule R-1)
===============================
Agent Action Plan section 0.7.2 R-1 names this module explicitly and
prescriptively: `acas_posting/dates.py` "reimplements the date module in full -
including its 1600-12-31 ordinal epoch, verified to round-trip correctly -
INSTEAD OF CALLING IT" (common/maps04.cbl:L122, sales/sl060.cbl:L1295).

So this module launches no process, loads no foreign library and reaches no
compiled artifact. It also uses NO third-party date library, and that exclusion
is deliberate rather than incidental - Agent Action Plan section 0.5.1: "the
date semantics being reproduced are those of a specific COBOL program with a
non-standard epoch and idiosyncratic rejection behavior. A general-purpose date
library would be more correct than the specification, which is the one outcome
to avoid." Three COBOL intrinsics are therefore reimplemented natively:
`FUNCTION integer-of-date`, `FUNCTION date-of-integer` and
`FUNCTION Test-Date-YYYYMMDD`.

Imports are standard library only. Agent Action Plan section 0.4.3 fixes the
layering; nothing in `acas_posting` is imported from here, which keeps this
module usable by `programs/*.py` without dragging in the record, DAL or CLI
layers.

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!  THE DEFECTS IN THIS MODULE ARE REPRODUCED ON PURPOSE  (rule R-4)       !!
!!                                                                         !!
!!  Agent Action Plan section 0.8.2, verbatim from the user's own           !!
!!  requirements:                                                          !!
!!                                                                         !!
!!      "There is no test suite: compiled COBOL execution is the           !!
!!      behavioral specification, defects included. A defect reproduced    !!
!!      is correct; a defect fixed is a failure."                          !!
!!                                                                         !!
!!  This module is the primary carrier of ANOMALY #16: on rejection        !!
!!  `maps04` leaves its binary output field COMPLETELY UNTOUCHED - not     !!
!!  zeroed, not set to a sentinel, not raised as an exception - even        !!
!!  though its own remarks at common/maps04.cbl:L163 claim that "Date      !!
!!  errors returned as A-Bin equal zero". That documented contract holds   !!
!!  only because the callers pre-zero the field themselves                 !!
!!  (copybooks/Proc-ACAS-Mapser-RDB.cob:L78 and the `zz050-test-date`      !!
!!  paragraph below). Zeroing it here would be the single easiest way to   !!
!!  "fix" a defect and fail this migration.                                !!
!!                                                                         !!
!!  Every reproduction site below carries an inline [path:Lnnn] comment.   !!
!!  See docs/migration/anomaly-log.md and                                  !!
!!  docs/migration/ambiguity-resolutions.md.                               !!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

THE EPOCH, AND THE MAINTAINER'S OWN WARNING ABOUT IT
====================================================
`FUNCTION integer-of-date` counts days from 1600-12-31, so 1601-01-01 is day 1
(common/maps04.cbl:L167). In Python that epoch is `date(1600, 12, 31)`, whose
proleptic Gregorian ordinal is 584388; `COBOL_DATE_EPOCH_ORDINAL` below derives
it rather than hard-coding it.

The maintainer flags the consequence himself at common/maps04.cbl:L39-L41 -
this "uses binary Dates from 31/12/1600 so is NOT usable within IRS as is, but
in any event uses Dates with CC e.g., dd/mm/ccYY where as IRS uses dd/mm/YY."
That is why the IRS posting path does not route through this module, and why
irs/irs030.cbl's own `Date-Validate` section is out of scope.

WHICH PROGRAM CARRIES WHICH SECTION
===================================
Verified by grepping the frozen source for section headers. Agent Action Plan
section 0.6.3 describes these sections as repeated in "nine of the in-scope
programs"; the measured census is more precise, and NOT uniform:

    program   zz050   zz060   zz070   wrapper section
    -------   -----   -----   -----   -------------------------------
    gl051     L1169   L1208   L1243   maps03  L1273   (anomaly #22)
    gl070      -      L538    L573    maps03  L603    (anomaly #22)
    gl071      -       -       -       -   (a pure sort; no date logic at all)
    gl072      -       -      L467     -
    gl080      -       -      L719     -
    sl055      -       -      L694     -
    sl060     L1192   L1227   L1262   maps04  L1292
    sl100     L708    L743    L778    maps04  L808
    pl055      -       -      L599     -
    pl060     L1046   L1081   L1116   maps04  L1146
    pl100     L689    L724    L759    maps04  L789
    irs030     -       -       -      Date-Validate L1285 - OUT OF SCOPE

`gl070` has no `zz050` at all; four programs carry `zz070` only; `gl071` carries
none. Do not assume uniformity.

WHAT MAY BE CONSOLIDATED, AND WHAT MAY NOT
==========================================
Agent Action Plan section 0.6.3 claims these section bodies are "textually
equivalent" and so may be consolidated. That claim was MEASURED here by
normalised diff across every carrier, and it is only partly true:

  * `zz070-Convert-Date` - byte-identical in all TEN carriers. Consolidated
    into one function, safely.
  * `zz060-Convert-Date` - identical in all SIX carriers except for the single
    token naming the wrapper it performs (`maps03` in gl051/gl070, `maps04` in
    the other four). Consolidated, with the wrapper passed in explicitly.
  * `zz050-Validate-Date` - NOT EQUIVALENT. `gl051` alone carries three extra
    `inspect ws-test-date replacing all` statements at general/gl051.cbl:
    L1178-L1180, which mutate the caller's own text field. It is therefore
    published here as TWO separate functions, and the mutating variant is not
    reachable by accident or by a defaulted argument. Agent Action Plan
    section 0.6.1's warning about three disagreeing copies of one idiom applies
    directly: "Normalising them into one helper would be the single easiest way
    to fail this migration."

COMPILED BEHAVIOUR SETTLED THE OPEN QUESTIONS  (rule R-6)
=========================================================
Agent Action Plan section 0.6.8 lists this module's reject contract as an
ambiguity requiring oracle arbitration, and reading the source cannot settle
three further points. All were resolved by compiling the frozen
`common/maps04.cbl` with GnuCOBOL 3.2 and observing it, exactly as rule R-6
requires; each result is recorded at its reproduction site below and in
docs/migration/ambiguity-resolutions.md:

  * The reject contract. Confirmed: with the binary field pre-set to a sentinel
    and a bad date supplied, the field still holds the sentinel afterwards, on
    BOTH the six-part-test path and the calendar-check path.
  * A non-numeric year. `A-Year` is never tested for numeric, and the compiled
    program does NOT reject such a date - it ACCEPTS it and produces a
    different year. See `_zoned_decimal_value` below, which reproduces the
    measured rule.
  * `FUNCTION Test-Date-YYYYMMDD`'s domain. Measured as exactly 1601-01-01
    through 9999-12-31; it rejects 1600-12-31, which `datetime.date` accepts.
  * An out-of-domain binary day number on the unpack path. The compiled program
    does not fail - it yields "00/00/0000".

NO AMBIENT NONDETERMINISM  (rule R-6)
=====================================
This module converts dates it is GIVEN. It never asks the system what day it
is: there is no clock read, no entropy source and no environment lookup
anywhere below. Pinning the run date is `acas_posting.clock`'s job, and even
that takes an injected value. The single clock read in the entire COBOL call
chain lives in the menu shell's date-service copybook
(copybooks/Proc-ACAS-Mapser-RDB.cob:L72), not in any in-scope program.

NUMERIC POLICY  (rule R-2)
==========================
Every value here is a `str` (the 10-character date text and its fixed-width
sub-fields) or an `int` (the binary day number, the digit groups, and `Z` the
separator tally). This module holds no binary floating-point value and no
fixed-point decimal at all: nothing here is monetary, and `A-Bin` is declared
`binary-long`, a signed 32-bit integer, so it is a Python `int`. The ordinal
arithmetic is integer subtraction, which is exact.

NO ADDED VALIDATION  (rule R-3)
===============================
Agent Action Plan section 0.7.2 R-3, verbatim: "Validation is copied, never
extended: the date module's six-part reject test is reproduced EXACTLY AS
WRITTEN (common/maps04.cbl:L140-L146)." So the test below has exactly six
parts, in exactly the written order, with exactly the written operands - and it
does NOT test `A-Year` for numeric, because the COBOL does not. That gap is
load-bearing, it is measurable in the compiled program's output, and it is not
an oversight to be corrected here.

Nothing in this module raises for a bad date, either. The COBOL never raises;
it falls through and leaves the output field alone, and the rejection signal is
precisely "the binary field was not written". There is deliberately no
exception hierarchy for rejected dates.

TRACEABILITY  (rule R-5)
========================
Every COBOL paragraph and section reproduced here has a correspondingly named
function, and every `GO TO` site carries a comment naming its class from the
four-class taxonomy of Agent Action Plan section 0.4.2: Class 1 loop-back
becomes `continue`; Class 2 forward terminator becomes `break` plus the
post-loop work; Class 3 section or paragraph exit becomes `return`; Class 4
sibling re-dispatch becomes a named call followed by an explicit
`continue`/`return`. Only classes 3 and 4 occur in this module - there is no
loop in any of it.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from typing import Final

# ---------------------------------------------------------------------------
#  THE EPOCH  [common/maps04.cbl:L167]
# ---------------------------------------------------------------------------
#  `FUNCTION integer-of-date` returns 1 for 1601-01-01, so day zero is
#  1600-12-31. DERIVED, not hard-coded, so that the relationship to the
#  Gregorian calendar is stated once and cannot drift: the value is 584388.
#
#  Verified against the compiled intrinsic (rule R-6):
#      integer-of-date(16010101) = 1
#      integer-of-date(20250921) = 155127
#      integer-of-date(99991231) = 3067671
#
#  The maintainer's own caveat on this epoch is at [common/maps04.cbl:L39-L41]:
#  it "is NOT usable within IRS as is", because IRS dates carry no century.
# ---------------------------------------------------------------------------
COBOL_DATE_EPOCH_ORDINAL: Final[int] = date(1600, 12, 31).toordinal()

# ---------------------------------------------------------------------------
#  THE DOMAIN OF THE DATE INTRINSICS  (measured, rule R-6)
# ---------------------------------------------------------------------------
#  `FUNCTION Test-Date-YYYYMMDD` returns zero for a valid date and non-zero
#  otherwise. Its accepted range was measured on the compiled oracle:
#
#      Test-Date-YYYYMMDD(16001231) = 1   <- INVALID
#      Test-Date-YYYYMMDD(16010101) = 0   <- valid
#      Test-Date-YYYYMMDD(99991231) = 0   <- valid
#      Test-Date-YYYYMMDD(00000000) = 1   <- INVALID
#
#  This matters: `datetime.date` happily accepts 1600-12-31, and any
#  implementation that gated only on `date(...)` constructing successfully
#  would accept a date the specification rejects.
# ---------------------------------------------------------------------------
COBOL_MIN_DATE_YEAR: Final[int] = 1601
COBOL_MAX_DATE_YEAR: Final[int] = 9999

#  The corresponding binary day numbers, derived from the year bounds above so
#  the two can never disagree: 1 for 1601-01-01, 3067671 for 9999-12-31.
COBOL_MIN_DATE_INTEGER: Final[int] = (
    date(COBOL_MIN_DATE_YEAR, 1, 1).toordinal() - COBOL_DATE_EPOCH_ORDINAL
)
COBOL_MAX_DATE_INTEGER: Final[int] = (
    date(COBOL_MAX_DATE_YEAR, 12, 31).toordinal() - COBOL_DATE_EPOCH_ORDINAL
)

# ---------------------------------------------------------------------------
#  FIXED WIDTHS  [common/maps04.cbl:L110, L92-L100]
# ---------------------------------------------------------------------------
#  `A-Date pic x(10)` is the date text; `Test-Date` is the 8-byte CCYYMMDD
#  working-storage group that `Test-Date9 redefines ... pic 9(8)` reads as a
#  single number.
# ---------------------------------------------------------------------------
DATE_TEXT_LENGTH: Final[int] = 10
TEST_DATE_LENGTH: Final[int] = 8

# ---------------------------------------------------------------------------
#  THE THREE LOAD-BEARING STRING LITERALS
# ---------------------------------------------------------------------------
#  Each of these is moved into a 10-character field purely so that the SEPARATOR
#  characters land in fixed positions; the surrounding letters and zeros are
#  then overwritten by reference-modified moves. Reproducing the literals - and
#  the positional overwrites - rather than formatting a clean string is what
#  makes the observable output come out right for free.
#
#  MEASURED REFINEMENT (rule R-6): with a spaces source, the compiled code
#  produces "    /  /  " and "  /  /    " respectively - so the LETTERS never
#  survive into the output, because COBOL reference modification always yields
#  exactly the requested length and fully overwrites its target. What genuinely
#  survives from each literal is the "/" separators. That is their whole job.
# ---------------------------------------------------------------------------

#  [common/maps04.cbl:L182] - the unpack seed. Its "/" at positions 3 and 6 are
#  never overwritten, because the three moves that follow write only offsets
#  7-10, 4-5 and 1-2. THIS is why the unpacked form is DD/MM/CCYY.
UNPACK_SEED: Final[str] = "00/00/0000"

#  [general/gl070.cbl:L595] - used by zz060 and zz070, which convert UK order
#  INTO International. Its "/" land at positions 5 and 8, giving CCYY/MM/DD.
UK_TO_INTL_SEED: Final[str] = "ccyy/mm/dd"

#  [general/gl051.cbl:L1195] - used by zz050, which converts International order
#  INTO UK. A DIFFERENT literal from the one above, with "/" at positions 3 and
#  6, giving DD/MM/CCYY. The two directions read their source at different
#  offsets as well, so the two must never be copy-pasted into each other. The
#  names of these two constants state the direction for exactly that reason.
INTL_TO_UK_SEED: Final[str] = "dd/mm/ccyy"

# ---------------------------------------------------------------------------
#  THE PRESENTATION-FORMAT SWITCH  [copybooks/wssystem.cob:L128-L132]
# ---------------------------------------------------------------------------
#      05  Date-Form       pic 9.
#          88  Date-UK             value 1.   *> dd/mm/yyyy
#          88  Date-USA            value 2.   *> mm/dd/yyyy
#          88  Date-Intl           value 3.   *> yyyy/mm/dd
#          88  Date-Valid-Formats  values 1 2 3.
#
#  ANOMALY, reproduced: `Date-Valid-Formats` is declared but NEVER TESTED by
#  any of the date sections. They test `Date-Form = zero` and default to 1
#  instead, which means a Date-Form of 4 or 9 falls through every branch and is
#  treated as International. The unused condition name is therefore not
#  published as a predicate below - publishing it would invite a caller to use
#  the test the COBOL declines to make.
# ---------------------------------------------------------------------------
DATE_FORM_UNSET: Final[int] = 0
DATE_FORM_UK: Final[int] = 1
DATE_FORM_USA: Final[int] = 2
DATE_FORM_INTL: Final[int] = 3

#  The characters a PIC 9 DISPLAY field accepts as numeric. Spelled out rather
#  than delegated to `str.isdigit()`, which is True for superscripts and other
#  Unicode digit forms that a zoned-decimal COBOL field would reject.
_ASCII_DIGITS: Final[str] = "0123456789"


# ===========================================================================
#  COBOL FIXED-WIDTH STORAGE SEMANTICS
# ===========================================================================
#  A COBOL PIC X(n) field is n bytes wide at all times. That single fact is
#  what makes the seed literals above work, so these three helpers exist to
#  keep it true here as well rather than letting Python's variable-length
#  strings quietly change the observable result.
#
#  These are storage mechanics only - no business rule lives in them.
# ===========================================================================


def _alphanumeric_move(source: str, width: int) -> str:
    """Reproduce a COBOL `MOVE` into an alphanumeric `PIC X(width)` field.

    An alphanumeric move is left-justified: a short sending field is padded on
    the right with spaces, and a long one is truncated on the right. The
    receiving field is always exactly `width` characters afterwards.
    """
    if len(source) >= width:
        return source[:width]
    return source + " " * (width - len(source))


def _ref_mod(field_text: str, offset: int, length: int) -> str:
    """Reproduce COBOL reference modification `field (offset:length)`.

    `offset` is 1-based, as COBOL writes it. The declared field is materialised
    at its full width first, so that reading past the end of a short Python
    string yields the spaces a real COBOL field would hold there rather than a
    short slice. The result is always exactly `length` characters.
    """
    required_width = max(len(field_text), offset - 1 + length)
    materialised = _alphanumeric_move(field_text, required_width)
    return materialised[offset - 1 : offset - 1 + length]


def _poke(base_text: str, offset: int, length: int, value: str, width: int) -> str:
    """Reproduce a COBOL `MOVE` into a `REDEFINES` sub-field of a group.

    Writes `value` into the `length` characters at 1-based `offset` of a
    `width`-character group, leaving every other character of the group exactly
    as it was. That is precisely how the seed literals keep their separators:
    the moves overwrite the digit positions and never touch positions 3 and 6
    (or 5 and 8).
    """
    materialised = _alphanumeric_move(base_text, width)
    stored = _alphanumeric_move(value, length)
    return materialised[: offset - 1] + stored + materialised[offset - 1 + length :]


def _is_numeric(field_text: str) -> bool:
    """Reproduce the COBOL `NUMERIC` class condition for a `PIC 9(n)` DISPLAY field.

    A zoned-decimal DISPLAY field is numeric only when every character is an
    ASCII decimal digit. A space, a "/", a letter or a sign character all fail,
    which is why `"2 "` at the century position is rejected by the six-part
    test while `"20"` is accepted.
    """
    return len(field_text) > 0 and all(
        character in _ASCII_DIGITS for character in field_text
    )


def _zoned_decimal_value(digits_text: str) -> int:
    """Read a `PIC 9(n)` DISPLAY field as a number the way the compiled program does.

    ANOMALY, reproduced - and the resolution of an open question that the
    Agent Action Plan expected to be settled by the oracle rather than by
    reading the source (section 0.6.8; see docs/migration/ambiguity-resolutions.md).

    `Test-Date9` is `PIC 9(8)` DISPLAY, and the six-part test at
    [common/maps04.cbl:L140-L145] never checks `A-Year` for numeric, so
    non-digit characters CAN reach it. Reading the source alone suggests such a
    date would then fail the validity check and be rejected. IT IS NOT. The
    compiled program accepts it and posts a DIFFERENT YEAR.

    A zoned-decimal read takes the low nibble of each byte as its digit, and
    the digits are then positionally weighted with carry. Measured on the
    compiled oracle for the year characters that can appear here:

        year  low nibbles   Test-Date9   date         A-Bin observed
        ----  -----------   ----------   ----------   --------------
        "ab"  1, 2          20120921     2012-09-21   150379
        "a0"  1, 0          20100921     2010-09-21   149648
        "zz"  10, 10        21100921     2110-09-21   186172   <- carries
        "  "  0, 0          20000921     2000-09-21   145996

    All four match this implementation exactly. Note the third row: a low
    nibble of 10 is not a decimal digit at all, and it CARRIES into the next
    position - which is why this is written as an accumulate-and-carry loop
    rather than a digit-by-digit string substitution.

    Only `A-Year` can be non-numeric here: the century, month and day are all
    proved numeric by the six-part test before this is reached, so at most two
    of the eight bytes are ever anomalous. When they carry far enough to push
    the year past `COBOL_MAX_DATE_YEAR` the date is rejected by the validity
    check, with the binary field left untouched as always.
    """
    value = 0
    for character in digits_text:
        #  byte & 0x0F is the zoned-decimal digit: "0"-"9" are 0x30-0x39, so
        #  the low nibble is the digit; "a" is 0x61, so its low nibble is 1.
        value = value * 10 + (ord(character) & 0x0F)
    return value


# ===========================================================================
#  THE LINKAGE RECORD
#  [copybooks/wsmaps03.cob:L6-L30]  and  [common/maps04.cbl:L109-L120]
# ===========================================================================
#  ONE record, TWO vocabularies. The callers all pass `maps03-ws` from
#  copybooks/wsmaps03.cob, whose fields are named u-date / u-days / u-month /
#  u-year / u-cc / u-yy / u-bin, and which additionally declares USA and
#  International redefines. The called program declares the same 14 bytes as
#  `Mapa03-WS` with the names A-Date / A-Days / A-Month / A-CCYY / A-CC /
#  A-Year / A-Bin, and sees NEITHER of those extra redefines. Note also that
#  the record `maps04` declares is named after maps0*3* while the program
#  itself is maps04.
#
#  The caller's names are used for the attributes here, because the caller's
#  copybook is the one every in-scope program actually copies; the called
#  program's names appear in the comments at each site.
#
#  Byte layout of the 10-character text, 1-based, all three views at once:
#
#      offset  1  2  3  4  5  6  7  8  9  10
#      UK      d  d  /  m  m  /  c  c  y  y
#      USA     m  m  /  d  d  /  -  -  -  -
#      Intl    c  c  y  y  /  m  m  /  d  d
#
#  MUTABLE BY DESIGN, and this is not a style preference. A COBOL linkage
#  record is passed by reference, and the entire point of anomaly #16 is that
#  `maps04` selectively DOES NOT WRITE one of these fields on the reject path.
#  A frozen dataclass, or an entry point that returned a new object, would
#  erase the anomaly by making every field appear freshly assigned. So this is
#  a plain mutable dataclass, `maps04` returns None, and callers observe both
#  the writes and - crucially - the absences.
#
#  There is deliberately no validating `__post_init__` (rule R-3): this record
#  must be able to hold exactly the malformed text the COBOL can hold.
# ===========================================================================


@dataclass
class Maps03Ws:
    """The `maps03-ws` / `Mapa03-WS` linkage record: 10 characters plus a binary long.

    Attributes:
        u_date: `u-date pic x(10)` / `A-Date pic x(10)`. The date text. Held at
            its declared 10-character width by the accessors below; assign to
            it directly and the sub-field accessors will still read the field
            as COBOL would.
        u_bin: `u-bin binary-long` / `A-Bin binary-long`. The binary day number,
            counted from `COBOL_DATE_EPOCH_ORDINAL`. A signed 32-bit integer in
            COBOL, so a Python `int` here and never a binary floating-point
            value (rule R-2).

    The sub-field properties correspond one-for-one to the `REDEFINES` entries
    of the two copybooks. Reading one materialises the 10-character field first,
    so a short or empty `u_date` reads as the spaces a real COBOL field would
    hold. Writing one overwrites only its own bytes and leaves the separators
    alone, exactly as a `MOVE` into a `REDEFINES` sub-field does.
    """

    u_date: str = field(default=" " * DATE_TEXT_LENGTH)
    u_bin: int = 0

    # -- the UK view: `u-UK redefines u-date` -------------------------------
    #    [copybooks/wsmaps03.cob:L8-L15] / [common/maps04.cbl:L111-L119]

    @property
    def u_days(self) -> str:
        """`u-days pic 99` / `A-Days pic 99` - offset 1, length 2."""
        return _ref_mod(self.u_date, 1, 2)

    @u_days.setter
    def u_days(self, value: str) -> None:
        self.u_date = _poke(self.u_date, 1, 2, value, DATE_TEXT_LENGTH)

    @property
    def u_month(self) -> str:
        """`u-month pic 99` / `A-Month pic 99` - offset 4, length 2."""
        return _ref_mod(self.u_date, 4, 2)

    @u_month.setter
    def u_month(self, value: str) -> None:
        self.u_date = _poke(self.u_date, 4, 2, value, DATE_TEXT_LENGTH)

    @property
    def u_year(self) -> str:
        """`u-year` group / `A-CCYY pic 9(4)` - offset 7, length 4."""
        return _ref_mod(self.u_date, 7, 4)

    @u_year.setter
    def u_year(self, value: str) -> None:
        self.u_date = _poke(self.u_date, 7, 4, value, DATE_TEXT_LENGTH)

    @property
    def u_cc(self) -> str:
        """`u-cc pic 99` / `A-CC pic 99` - the century, offset 7, length 2."""
        return _ref_mod(self.u_date, 7, 2)

    @u_cc.setter
    def u_cc(self, value: str) -> None:
        self.u_date = _poke(self.u_date, 7, 2, value, DATE_TEXT_LENGTH)

    @property
    def u_yy(self) -> str:
        """`u-yy pic 99` / `A-Year pic 99` - year within century, offset 9, len 2.

        This is the field the six-part reject test never checks. See
        `_zoned_decimal_value`.
        """
        return _ref_mod(self.u_date, 9, 2)

    @u_yy.setter
    def u_yy(self, value: str) -> None:
        self.u_date = _poke(self.u_date, 9, 2, value, DATE_TEXT_LENGTH)

    # -- the USA view: `u-USA redefines u-date` -----------------------------
    #    [copybooks/wsmaps03.cob:L16-L21]. Declared by the CALLER's copybook
    #    only; `maps04` itself has no such redefines and never uses it.

    @property
    def u_usa_month(self) -> str:
        """`u-usa-month pic 99` - offset 1, length 2."""
        return _ref_mod(self.u_date, 1, 2)

    @u_usa_month.setter
    def u_usa_month(self, value: str) -> None:
        self.u_date = _poke(self.u_date, 1, 2, value, DATE_TEXT_LENGTH)

    @property
    def u_usa_days(self) -> str:
        """`u-usa-days pic 99` - offset 4, length 2."""
        return _ref_mod(self.u_date, 4, 2)

    @u_usa_days.setter
    def u_usa_days(self, value: str) -> None:
        self.u_date = _poke(self.u_date, 4, 2, value, DATE_TEXT_LENGTH)

    # -- the International view: `u-Intl redefines u-date` ------------------
    #    [copybooks/wsmaps03.cob:L22-L29]. Caller's copybook only, as above.

    @property
    def u_intl_year(self) -> str:
        """`u-intl-year` group - offset 1, length 4."""
        return _ref_mod(self.u_date, 1, 4)

    @u_intl_year.setter
    def u_intl_year(self, value: str) -> None:
        self.u_date = _poke(self.u_date, 1, 4, value, DATE_TEXT_LENGTH)

    @property
    def u_intl_cc(self) -> str:
        """`u-intl-cc pic 99` - offset 1, length 2."""
        return _ref_mod(self.u_date, 1, 2)

    @u_intl_cc.setter
    def u_intl_cc(self, value: str) -> None:
        self.u_date = _poke(self.u_date, 1, 2, value, DATE_TEXT_LENGTH)

    @property
    def u_intl_yy(self) -> str:
        """`u-intl-yy pic 99` - offset 3, length 2."""
        return _ref_mod(self.u_date, 3, 2)

    @u_intl_yy.setter
    def u_intl_yy(self, value: str) -> None:
        self.u_date = _poke(self.u_date, 3, 2, value, DATE_TEXT_LENGTH)

    @property
    def u_intl_month(self) -> str:
        """`u-intl-month pic 99` - offset 6, length 2."""
        return _ref_mod(self.u_date, 6, 2)

    @u_intl_month.setter
    def u_intl_month(self, value: str) -> None:
        self.u_date = _poke(self.u_date, 6, 2, value, DATE_TEXT_LENGTH)

    @property
    def u_intl_days(self) -> str:
        """`u-intl-days pic 99` - offset 9, length 2."""
        return _ref_mod(self.u_date, 9, 2)

    @u_intl_days.setter
    def u_intl_days(self, value: str) -> None:
        self.u_date = _poke(self.u_date, 9, 2, value, DATE_TEXT_LENGTH)


# ===========================================================================
#  THE THREE COBOL INTRINSIC FUNCTIONS, REIMPLEMENTED  (rule R-1)
# ===========================================================================
#  `common/maps04.cbl` delegates the real work to three intrinsics, a choice
#  its own change log dates to 2009 and explains: the migration to GnuCOBOL
#  used "intrinsic FUNCTIONs to do most of the work ... to help reduce risk of
#  format change problems in old programs" [common/maps04.cbl:L35-L37].
#
#  Rule R-1 forbids reaching the COBOL runtime for them, so all three are
#  reimplemented natively below. Each was checked against the compiled
#  intrinsic rather than against its documentation.
# ===========================================================================


def _is_leap_year(year: int) -> bool:
    """Apply the Gregorian leap rule, spelled out rather than delegated.

    Divisible by 4, except centuries, except every fourth century. Written
    explicitly because this is the rule that decides whether 29 February is
    accepted, and the compiled program's own comment at
    [common/maps04.cbl:L137-L138] identifies exactly this as the check the
    six-part test deliberately leaves to the intrinsic: the earlier tests are
    "Very basic Testing here as FUNCTION Test-Date checks for February and leap
    years".
    """
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def _days_in_month(year: int, month: int) -> int:
    """Return the day count for a Gregorian month, February by the leap rule."""
    if month == 2:
        return 29 if _is_leap_year(year) else 28
    if month in (4, 6, 9, 11):
        return 30
    return 31


def test_date_yyyymmdd(yyyymmdd: int) -> int:
    """Reimplement `FUNCTION Test-Date-YYYYMMDD` [common/maps04.cbl:L153].

    Returns ZERO for a valid date and non-zero for an invalid one. That polarity
    is the COBOL intrinsic's, not a Python convention, and the call site tests
    it exactly as the COBOL does - `not = zero` means "bad date".

    The accepted domain was MEASURED on the compiled intrinsic rather than
    assumed (rule R-6), and it is tighter than `datetime.date`'s:

        Test-Date-YYYYMMDD(16001231) = 1   <- rejected, though a valid Gregorian
                                              date and this module's own epoch
        Test-Date-YYYYMMDD(16010101) = 0
        Test-Date-YYYYMMDD(20250921) = 0
        Test-Date-YYYYMMDD(21100921) = 0
        Test-Date-YYYYMMDD(99991231) = 0
        Test-Date-YYYYMMDD(00000000) = 1

    An implementation that merely tried `date(y, m, d)` inside a `ValueError`
    guard would therefore ACCEPT 1600-12-31 and diverge from the specification
    on that date, which is why the year bounds are tested explicitly.

    The non-zero return is 1, matching the observed value, so that a caller
    which compares the result against something other than zero still agrees
    with the compiled program.

    NOTE FOR TEST AUTHORS: this function's name is taken from the COBOL
    intrinsic `FUNCTION Test-Date-YYYYMMDD` for traceability (rule R-5), and it
    consequently matches the `python_functions = ["test_*"]` pattern that
    pyproject.toml configures for pytest. Importing it into a test module's
    namespace by its own name makes pytest try to COLLECT IT AS A TEST, which
    fails with "fixture 'yyyymmdd' not found". Import it under an alias in test
    modules - for example
    `from acas_posting.dates import test_date_yyyymmdd as cobol_test_date` -
    or reference it through the module. Renaming it here to dodge the collision
    would break the one-to-one correspondence with the intrinsic it replaces.
    """
    year, remainder = divmod(yyyymmdd, 10_000)
    month, day = divmod(remainder, 100)
    if year < COBOL_MIN_DATE_YEAR or year > COBOL_MAX_DATE_YEAR:
        return 1
    if month < 1 or month > 12:
        return 1
    if day < 1 or day > _days_in_month(year, month):
        return 1
    return 0


def integer_of_date(year: int, month: int, day: int) -> int:
    """Reimplement `FUNCTION integer-of-date` [common/maps04.cbl:L167].

    Returns the binary day number counted from `COBOL_DATE_EPOCH_ORDINAL`,
    1600-12-31, so that 1601-01-01 is day 1. Verified against the compiled
    intrinsic: 1601-01-01 gives 1, 2025-09-21 gives 155127 and 9999-12-31 gives
    3067671, the maximum.

    The subtraction is integer arithmetic and therefore exact (rule R-2); no
    floating point is involved at any point.

    As in COBOL, validating the argument is the caller's job and no validation
    is added here (rule R-3): `maps04` only ever reaches this after
    `test_date_yyyymmdd` has returned zero, so the date is always a real one by
    then.
    """
    return date(year, month, day).toordinal() - COBOL_DATE_EPOCH_ORDINAL


def date_of_integer(day_number: int) -> date:
    """Reimplement `FUNCTION Date-of-integer` [common/maps04.cbl:L183].

    The inverse of `integer_of_date`: day 1 is 1601-01-01. Returns a
    `datetime.date`, which the unpack path below then renders as CCYYMMDD text.

    The COBOL intrinsic returns zero rather than failing for a day number
    outside 1 through 3067671 - measured, see `ws_unpack`, which reproduces that
    behaviour at the one place it is observable. This function models the
    in-domain conversion only, so the out-of-domain result stays visible at the
    site where the COBOL's zero actually shows up in the output.
    """
    return date.fromordinal(day_number + COBOL_DATE_EPOCH_ORDINAL)


# ===========================================================================
#  maps04 - THE PROGRAM  [common/maps04.cbl:L122-L189]
# ===========================================================================
#  `procedure division using Mapa03-WS.` - one parameter, passed by reference,
#  and no return value. The COBOL has a single exit point, `Main-Exit.` at
#  [common/maps04.cbl:L188-L189], whose only statement is `exit program.`;
#  every `go to Main-Exit` in the program is therefore a Class 3 transfer and
#  becomes a bare `return` here. `Main-Exit` is not given a function of its own
#  because it holds no work - that single-return convention IS its
#  reproduction, and each of the three transfer sites is annotated below.
# ===========================================================================


def maps04(ws: Maps03Ws) -> None:
    """Validate and convert a date, in place, exactly as `common/maps04.cbl` does.

    Two directions in one entry point, selected by `u_bin`:

      * `u_bin > 0` - UNPACK. The binary day number is converted to DD/MM/CCYY
        text in `u_date`.
      * otherwise - VALIDATE AND PACK. The text in `u_date` is normalised,
        checked, and on success converted to a binary day number in `u_bin`.

    Mutates `ws` and returns None, because the COBOL mutates its linkage record
    and returns nothing. THE ABSENCE of a write is as significant as a write
    here - see the reject paths below.

    ANOMALY #16, reproduced [common/maps04.cbl:L146, L154, L163]: on EITHER
    reject path the binary field `u_bin` is left COMPLETELY UNTOUCHED. It is not
    zeroed, not set to a sentinel and no exception is raised, even though the
    program's own remarks at L163 claim "Date errors returned as A-Bin equal
    zero". That documented contract holds only because the callers zero the
    field themselves before calling - `copybooks/Proc-ACAS-Mapser-RDB.cob:L78`
    and the `zz050-test-date` paragraph reproduced further down this module both
    do exactly that. Callers that do not pre-zero observe whatever was in the
    field before.

    Confirmed on the compiled program rather than inferred (rule R-6): with
    `u_bin` pre-set to -999 and the text "xx/yy/zzzz", `u_bin` still held -999
    afterwards; likewise with "31-02-2025", which passes the six-part test and
    fails only the calendar check. See docs/migration/ambiguity-resolutions.md.
    """
    # -----------------------------------------------------------------------
    #  [common/maps04.cbl:L128-L129]
    #      if       A-Bin  >  zero
    #               go to  WS-Unpack.
    #
    #  Class 4 sibling re-dispatch: the named paragraph is called and control
    #  then leaves the program, so it is a call followed by an explicit return.
    #
    #  STRICTLY GREATER THAN ZERO, and that is not interchangeable with "not
    #  zero". The program's own comment two lines above, at
    #  [common/maps04.cbl:L125-L126], describes the switch as "if entry A-Bin
    #  not zero then convert to dd/mm/ccyy" - but the code tests `> zero`, so a
    #  NEGATIVE binary value takes the forward TEXT path, not the unpack path.
    #  That is a second place where this program's comments overstate its code,
    #  independently of anomaly #16, and it is reproduced literally.
    #  Confirmed on the compiled program: u_bin = -1 with valid text took the
    #  forward path and produced 155127.
    # -----------------------------------------------------------------------
    if ws.u_bin > 0:
        ws_unpack(ws)
        return  # Class 3 -> Main-Exit [common/maps04.cbl:L188]

    #  [common/maps04.cbl:L131]  move zero to Z.
    #  `Z pic 99 binary` [common/maps04.cbl:L93] is the separator tally.
    separator_tally = 0

    # -----------------------------------------------------------------------
    #  [common/maps04.cbl:L132-L134]
    #      inspect  A-Date replacing all "." by "/".
    #      inspect  A-Date replacing all "," by "/".
    #      inspect  A-Date replacing all "-" by "/".
    #
    #  ANOMALY, reproduced: these three statements rewrite the CALLER'S OWN
    #  10-character field in place, and they run BEFORE the reject test. So a
    #  date that is subsequently REJECTED still comes back to the caller with
    #  its separators normalised - a caller-visible side effect on the failure
    #  path. Measured on the compiled program: given "31-02-2025" the call is
    #  REJECTED (31 February is not a real date, so the calendar check at L153
    #  fails) and yet the caller's field afterwards reads "31/02/2025", with the
    #  hyphens replaced. The same holds for "31.02.2025" and "31,02,2025".
    #
    #  Three separate statements, applied in the written order "." then ","
    #  then "-", each assigning back to the linkage field. This is also why
    #  this function must never be memoised: it mutates its argument (rule R-3
    #  forbids caching here for exactly that reason).
    #
    #  The first statement materialises the field at its declared 10-character
    #  width, because a COBOL PIC X(10) field is always 10 bytes wide and the
    #  positional tests below depend on that. That is storage mechanics, not a
    #  behaviour change.
    # -----------------------------------------------------------------------
    ws.u_date = _alphanumeric_move(ws.u_date, DATE_TEXT_LENGTH).replace(".", "/")
    ws.u_date = ws.u_date.replace(",", "/")
    ws.u_date = ws.u_date.replace("-", "/")

    # -----------------------------------------------------------------------
    #  [common/maps04.cbl:L135]  inspect A-Date tallying Z for all "/".
    #
    #  The tally counts "/" across the WHOLE ten characters, not just positions
    #  3 and 6. Two consequences, both reproduced: a text carrying three or
    #  more "/" is rejected by part one of the test below, while a text with
    #  exactly two "/" in the WRONG positions passes the tally and is then
    #  judged only by the positional numeric tests.
    # -----------------------------------------------------------------------
    separator_tally = ws.u_date.count("/")

    # -----------------------------------------------------------------------
    #  [common/maps04.cbl:L140-L146]  THE SIX-PART REJECT TEST
    #
    #      if       Z not = 2 or
    #               A-Days not numeric or
    #               A-Month not numeric or
    #               A-CC   not numeric or
    #               A-Days < 01 or > 31 or
    #               A-Month < 01 or > 12
    #               go to Main-Exit.
    #
    #  EXACTLY SIX PARTS, in exactly this order, with exactly these operands.
    #  Agent Action Plan section 0.7.2 R-3 requires it reproduced "exactly as
    #  written", and no part may be added, removed, reordered or strengthened.
    #
    #  *** A-Year IS NOT TESTED FOR NUMERIC ANYWHERE IN THIS LIST. ***
    #  The century (`A-CC`) is checked; the year within the century
    #  (`A-Year`, offset 9) is not. That gap is NOT an oversight to be
    #  corrected: it is observable in the compiled program's output, which
    #  ACCEPTS a date with a non-numeric year and posts a different year for it.
    #  See `_zoned_decimal_value` for the measured rule and the four cases it
    #  was verified against. Adding a year check here - or letting a regex, an
    #  int() conversion or a try/except reject such a value - would silently
    #  reject dates the specification accepts.
    #
    #  Parts five and six reproduce COBOL's abbreviated combined relations,
    #  `A-Days < 01 or > 31` meaning `A-Days < 1 OR A-Days > 31`; each is
    #  bracketed so that this remains six top-level operands rather than eight.
    #  Their int() conversions cannot fail: Python evaluates `or` left to right,
    #  so part five is only reached once part two has proved the days numeric,
    #  and part six only once part three has proved the month numeric.
    # -----------------------------------------------------------------------
    days_text = ws.u_days
    month_text = ws.u_month
    if (
        separator_tally != 2  # part 1  [L140]
        or not _is_numeric(days_text)  # part 2  [L141]
        or not _is_numeric(month_text)  # part 3  [L142]
        or not _is_numeric(ws.u_cc)  # part 4  [L143]
        or (int(days_text) < 1 or int(days_text) > 31)  # part 5  [L144]
        or (int(month_text) < 1 or int(month_text) > 12)  # part 6  [L145]
    ):
        #  Class 3 -> Main-Exit [common/maps04.cbl:L146].
        #  ANOMALY #16: u_bin is NOT written. Returning here leaves whatever the
        #  caller put there, and that is the entire rejection signal.
        return

    # -----------------------------------------------------------------------
    #  [common/maps04.cbl:L148-L151]  assemble Test-Date as CCYYMMDD
    #
    #      move     A-CC    to TD-CC.
    #      move     A-Year  to TD-YY.
    #      move     A-Month to TD-MM.
    #      move     A-Days  to TD-DD.
    #
    #  `Test-Date` [common/maps04.cbl:L94-L99] is an 8-byte group laid out as
    #  TD-CC(1:2) TD-YY(3:2) TD-MM(5:2) TD-DD(7:2), and
    #  `Test-Date9 redefines Test-Date pic 9(8)` [L100] reads all eight bytes as
    #  one number. All four moves are performed in the written order; every byte
    #  of the group is written, so its previous working-storage content cannot
    #  leak through.
    #
    #  Note that A-Year arrives here WITHOUT having been proved numeric, by the
    #  gap documented above. Its characters are carried through as-is, exactly
    #  as the compiled program carries them.
    # -----------------------------------------------------------------------
    test_date = " " * TEST_DATE_LENGTH
    test_date = _poke(test_date, 1, 2, ws.u_cc, TEST_DATE_LENGTH)  # [L148]
    test_date = _poke(test_date, 3, 2, ws.u_yy, TEST_DATE_LENGTH)  # [L149]
    test_date = _poke(test_date, 5, 2, month_text, TEST_DATE_LENGTH)  # [L150]
    test_date = _poke(test_date, 7, 2, days_text, TEST_DATE_LENGTH)  # [L151]

    #  Reading the 8-byte group as `Test-Date9 pic 9(8)`. This is where a
    #  non-numeric year becomes a number - see `_zoned_decimal_value`.
    test_date9 = _zoned_decimal_value(test_date)

    # -----------------------------------------------------------------------
    #  [common/maps04.cbl:L153-L154]
    #      if       FUNCTION Test-Date-YYYYMMDD (Test-Date9) not = zero
    #               go to Main-Exit.
    #
    #  The calendar check - the one that catches February and leap years, and
    #  the reason the six tests above are described in the source itself as
    #  "Very basic Testing".
    # -----------------------------------------------------------------------
    if test_date_yyyymmdd(test_date9) != 0:
        #  Class 3 -> Main-Exit [common/maps04.cbl:L154].
        #  ANOMALY #16 again, on the second and independent reject path: u_bin
        #  is NOT written here either. "31/02/2025" reaches exactly this point.
        return

    # -----------------------------------------------------------------------
    #  [common/maps04.cbl:L167]
    #      move     FUNCTION integer-of-Date (Test-Date9) to A-Bin.
    #
    #  The single successful write to the binary field in the whole forward
    #  path. `Test-Date9` is a validated CCYYMMDD number by now, so splitting it
    #  into year, month and day cannot fail.
    # -----------------------------------------------------------------------
    year, remainder = divmod(test_date9, 10_000)
    month, day = divmod(remainder, 100)
    ws.u_bin = integer_of_date(year, month, day)

    #  [common/maps04.cbl:L168]  go to Main-Exit.
    #  Class 3 -> Main-Exit. Explicit rather than implicit, because the COBOL
    #  writes the transfer explicitly and a reader comparing the two should find
    #  it here.
    return


def ws_unpack(ws: Maps03Ws) -> None:
    """Reproduce the `WS-Unpack` paragraph [common/maps04.cbl:L181-L186].

    Converts the binary day number in `u_bin` to DD/MM/CCYY text in `u_date`.
    Reached only from the `u_bin > 0` switch at the head of `maps04`, and it
    validates NOTHING: `FUNCTION Date-of-integer` is applied to whatever
    positive integer arrived.

    That raises a question `datetime` cannot answer, because
    `date.fromordinal` fails for an out-of-range ordinal while the COBOL does
    not fail at all. MEASURED on the compiled program (rule R-6):

        Date-of-integer(3067671)  = 99991231   <- the last valid day
        Date-of-integer(3067672)  = 0
        Date-of-integer(99999999) = 0

    and through this paragraph:

        u_bin = 1        -> "01/01/1601"
        u_bin = 3067671  -> "31/12/9999"
        u_bin = 3067672  -> "00/00/0000"
        u_bin = 99999999 -> "00/00/0000"

    So an out-of-domain day number yields "00/00/0000": the intrinsic's zero
    flows into the 8-byte group as "00000000", and the three moves below then
    write zeros over the seed's zeros, leaving the seed's separators standing.
    That is reproduced below rather than allowed to raise - not as an invented
    fallback, but because it is what the compiled program was observed to do.
    See docs/migration/ambiguity-resolutions.md.
    """
    # -----------------------------------------------------------------------
    #  [common/maps04.cbl:L182]  move "00/00/0000" to A-Date.
    #
    #  THE SEED. This literal is the sole source of the separators in the
    #  unpacked date: positions 3 and 6 hold "/" and are never overwritten,
    #  because the three moves below write only offsets 7-10, 4-5 and 1-2.
    #  That, and nothing else, is why the unpacked form is DD/MM/CCYY.
    # -----------------------------------------------------------------------
    ws.u_date = UNPACK_SEED

    # -----------------------------------------------------------------------
    #  [common/maps04.cbl:L183]
    #      move FUNCTION Date-of-integer (A-Bin) to Test-Date.  *> CCYYMMDD
    # -----------------------------------------------------------------------
    if COBOL_MIN_DATE_INTEGER <= ws.u_bin <= COBOL_MAX_DATE_INTEGER:
        converted = date_of_integer(ws.u_bin)
        test_date = f"{converted.year:04d}{converted.month:02d}{converted.day:02d}"
    else:
        #  The measured out-of-domain result: the intrinsic returns zero, so the
        #  8-byte group reads "00000000".
        test_date = "0" * TEST_DATE_LENGTH

    # -----------------------------------------------------------------------
    #  [common/maps04.cbl:L184-L186]
    #      move     TD-CCYY to A-CCYY.      *> 4 chars at offset 7
    #      move     TD-MM   to A-Month.     *> 2 chars at offset 4
    #      move     TD-DD   to A-Days.      *> 2 chars at offset 1
    #
    #  In the written order, which is CCYY then MM then DD - the maintainer's
    #  own comment on the last of the three reads "Now UK Date".
    # -----------------------------------------------------------------------
    ws.u_year = _ref_mod(test_date, 1, 4)  # TD-CCYY  [L184]
    ws.u_month = _ref_mod(test_date, 5, 2)  # TD-MM    [L185]
    ws.u_days = _ref_mod(test_date, 7, 2)  # TD-DD    [L186]

    #  Falls straight through to `Main-Exit` in the COBOL; the caller's return
    #  statement stands in for that Class 3 transfer.


# ===========================================================================
#  THE WRAPPER SECTION - ONE IMPLEMENTATION, TWO PUBLISHED NAMES
# ===========================================================================
#  Six programs wrap the `CALL` in a section of their own, and the body is the
#  same single statement in every one of them:
#
#      call     "maps04"  using  maps03-ws.
#
#  ANOMALY #22, reproduced - and it occurs in TWO programs, not one. Agent
#  Action Plan section 0.6.7 entry 22 cites only gl070; gl051 carries the
#  identical defect. In both, the SECTION is named after the interface copybook
#  (maps03) while its EXIT LABEL is named after the called program
#  (maps04-exit):
#
#      program   section name   exit label      agree?
#      -------   ------------   -------------   ------
#      gl051     maps03 L1273   maps04-exit L1278   NO   <- anomaly #22
#      gl070     maps03 L603    maps04-exit L608    NO   <- anomaly #22
#      sl060     maps04 L1292   maps04-exit L1297   yes
#      sl100     maps04 L808    maps04-exit L813    yes
#      pl060     maps04 L1146   maps04-exit L1151   yes
#      pl100     maps04 L789    maps04-exit L794    yes
#
#  Both names are published here over ONE implementation, on the same reasoning
#  Agent Action Plan section 0.3.3 gives for the dual-aliased data-access
#  facade: "traceability demands that a reader following either COBOL convention
#  find a correspondingly named Python function, while sane engineering demands
#  the logic exist once."
# ===========================================================================


def maps03(ws: Maps03Ws) -> None:
    """Reproduce the wrapper section named `maps03`, carried by gl070 and gl051.

    Locators: [general/gl070.cbl:L603-L609] and [general/gl051.cbl:L1273-L1278].

    ANOMALY #22: the section is named after the interface copybook while its
    exit label is `maps04-exit`, named after the program it calls. Its body is
    the single statement `call "maps04" using maps03-ws.`, so it is exactly
    `maps04` under a second name, and it delegates rather than duplicating.

    Published so that a reader following the General Ledger convention finds a
    correspondingly named function; the four Sales and Purchase carriers name
    the same section `maps04` and should call that instead.
    """
    maps04(ws)


# ===========================================================================
#  THE PRESENTATION-FORMAT CONDITION NAMES
#  [copybooks/wssystem.cob:L128-L132]
# ===========================================================================
#  Agent Action Plan section 0.1.2 rule 12 maps an 88-level condition name to
#  "a predicate function over the record", so the three the date sections
#  actually test become the three predicates below.
#
#  `Date-Valid-Formats` (values 1 2 3) is deliberately NOT published. It is
#  declared in the copybook and never tested by any date section - they test
#  `Date-Form = zero` and default to 1 instead. Publishing a predicate for the
#  test the COBOL declines to make would invite a caller to make it, which
#  would be a new validation (rule R-3). A Date-Form of 4 or 9 consequently
#  falls through every branch and is treated as International, and that is the
#  specified behaviour.
# ===========================================================================


def date_form_is_uk(date_form: int) -> bool:
    """`88 Date-UK value 1` - dd/mm/yyyy [copybooks/wssystem.cob:L129]."""
    return date_form == DATE_FORM_UK


def date_form_is_usa(date_form: int) -> bool:
    """`88 Date-USA value 2` - mm/dd/yyyy [copybooks/wssystem.cob:L130]."""
    return date_form == DATE_FORM_USA


def date_form_is_intl(date_form: int) -> bool:
    """`88 Date-Intl value 3` - yyyy/mm/dd [copybooks/wssystem.cob:L131].

    Published for completeness and for callers that need the test, but note that
    NONE of the four date sections uses it: each reaches its International
    branch by FALLING THROUGH the UK and USA tests, never by testing this
    condition. That is why a Date-Form of 4 or 9 is treated as International.
    """
    return date_form == DATE_FORM_INTL


# ===========================================================================
#  THE SECTIONS' WORKING STORAGE  [general/gl070.cbl:L172-L194]
# ===========================================================================
#      01  ws-Test-Date            pic x(10).
#      01  ws-date-formats.
#          03  ws-swap             pic xx.
#          03  ws-Conv-Date        pic x(10).
#          03  ws-date             pic x(10).
#          03  ws-UK   redefines ws-date.  ws-days xx / ws-month xx / ws-year x(4)
#          03  ws-USA  redefines ws-date.  ws-usa-month xx / ws-usa-days xx
#          03  ws-Intl redefines ws-date.  ws-intl-year x(4) / -month xx / -days xx
#
#  The redefines are `pic xx` and `pic x(4)` - ALPHANUMERIC, not numeric - so
#  the USA swap below moves CHARACTERS and never a number. That distinction
#  matters: an alphanumeric move neither strips a sign nor zero-fills.
#
#  `ws-Test-Date` is a separate `01` item in the COBOL, declared immediately
#  above the group. It is bundled into the same dataclass here because the
#  `zz050` sections read and (in one program) WRITE it alongside the group, and
#  because keeping the two together is what lets the gl051 variant's in-place
#  mutation of it stay visible to the caller. Bundling changes no behaviour: the
#  fields are independent and no COBOL redefines spans them.
#
#  `ws-Conv-Date` is declared in the group and is not touched by any of the four
#  date sections; it is modelled so the group is complete and so a reader
#  diffing this against the copybook finds every field.
#
#  Mutable, for the same reason `Maps03Ws` is: these sections communicate by
#  writing their caller's working storage in place.
# ===========================================================================


@dataclass
class WsDateFormats:
    """`ws-Test-Date` plus the `ws-date-formats` group [general/gl070.cbl:L172-L194].

    Attributes:
        ws_test_date: `ws-Test-Date pic x(10)` - the input text of `zz050`.
        ws_swap: `ws-swap pic xx` - the two-character scratch the USA branch
            swaps days and month through.
        ws_conv_date: `ws-Conv-Date pic x(10)` - declared in the group, unused
            by all four date sections.
        ws_date: `ws-date pic x(10)` - the output text of all four sections.
    """

    ws_test_date: str = field(default=" " * DATE_TEXT_LENGTH)
    ws_swap: str = field(default="  ")
    ws_conv_date: str = field(default=" " * DATE_TEXT_LENGTH)
    ws_date: str = field(default=" " * DATE_TEXT_LENGTH)

    # -- `ws-UK redefines ws-date` -----------------------------------------

    @property
    def ws_days(self) -> str:
        """`ws-days pic xx` - offset 1, length 2."""
        return _ref_mod(self.ws_date, 1, 2)

    @ws_days.setter
    def ws_days(self, value: str) -> None:
        self.ws_date = _poke(self.ws_date, 1, 2, value, DATE_TEXT_LENGTH)

    @property
    def ws_month(self) -> str:
        """`ws-month pic xx` - offset 4, length 2."""
        return _ref_mod(self.ws_date, 4, 2)

    @ws_month.setter
    def ws_month(self, value: str) -> None:
        self.ws_date = _poke(self.ws_date, 4, 2, value, DATE_TEXT_LENGTH)

    @property
    def ws_year(self) -> str:
        """`ws-year pic x(4)` - offset 7, length 4."""
        return _ref_mod(self.ws_date, 7, 4)

    @ws_year.setter
    def ws_year(self, value: str) -> None:
        self.ws_date = _poke(self.ws_date, 7, 4, value, DATE_TEXT_LENGTH)

    # -- `ws-USA redefines ws-date` ----------------------------------------

    @property
    def ws_usa_month(self) -> str:
        """`ws-usa-month pic xx` - offset 1, length 2."""
        return _ref_mod(self.ws_date, 1, 2)

    @ws_usa_month.setter
    def ws_usa_month(self, value: str) -> None:
        self.ws_date = _poke(self.ws_date, 1, 2, value, DATE_TEXT_LENGTH)

    @property
    def ws_usa_days(self) -> str:
        """`ws-usa-days pic xx` - offset 4, length 2."""
        return _ref_mod(self.ws_date, 4, 2)

    @ws_usa_days.setter
    def ws_usa_days(self, value: str) -> None:
        self.ws_date = _poke(self.ws_date, 4, 2, value, DATE_TEXT_LENGTH)

    # -- `ws-Intl redefines ws-date` ---------------------------------------

    @property
    def ws_intl_year(self) -> str:
        """`ws-intl-year pic x(4)` - offset 1, length 4."""
        return _ref_mod(self.ws_date, 1, 4)

    @ws_intl_year.setter
    def ws_intl_year(self, value: str) -> None:
        self.ws_date = _poke(self.ws_date, 1, 4, value, DATE_TEXT_LENGTH)

    @property
    def ws_intl_month(self) -> str:
        """`ws-intl-month pic xx` - offset 6, length 2."""
        return _ref_mod(self.ws_date, 6, 2)

    @ws_intl_month.setter
    def ws_intl_month(self, value: str) -> None:
        self.ws_date = _poke(self.ws_date, 6, 2, value, DATE_TEXT_LENGTH)

    @property
    def ws_intl_days(self) -> str:
        """`ws-intl-days pic xx` - offset 9, length 2."""
        return _ref_mod(self.ws_date, 9, 2)

    @ws_intl_days.setter
    def ws_intl_days(self, value: str) -> None:
        self.ws_date = _poke(self.ws_date, 9, 2, value, DATE_TEXT_LENGTH)


def _swap_days_and_month(ws: WsDateFormats) -> None:
    """Swap days and month through the `ws-swap` scratch field (USA branch).

        move ws-days to ws-swap
        move ws-month to ws-days
        move ws-swap to ws-month

    Byte-identical in all three sections that carry it, so it is written once:
    [general/gl070.cbl:L588-L590] in zz070, [general/gl070.cbl:L558-L560] in
    zz060, [general/gl051.cbl:L1188-L1190] in zz050, and at the corresponding
    lines of every other carrier.

    Note what it does NOT touch: the separators. Only the two-character day and
    month windows are exchanged, so DD/MM/CCYY becomes MM/DD/CCYY with the "/"
    at positions 3 and 6 left exactly where they were. Confirmed on the compiled
    program: "21/09/2025" becomes "09/21/2025".

    The scratch field is left holding the original day characters afterwards,
    exactly as the COBOL leaves it, because the third statement reads it rather
    than clearing it.
    """
    ws.ws_swap = _alphanumeric_move(ws.ws_days, 2)
    ws.ws_days = ws.ws_month
    ws.ws_month = ws.ws_swap


# ===========================================================================
#  zz070-Convert-Date  -  CONSOLIDATED, VERIFIED BYTE-IDENTICAL IN 10 CARRIERS
# ===========================================================================
#  Reference body: [general/gl070.cbl:L573-L601]. Every carrier was extracted
#  and compared by normalised diff; all ten are the same body:
#
#      gl051 L1243  gl070 L573  gl072 L467  gl080 L719  sl055 L694
#      sl060 L1262  sl100 L778  pl055 L599  pl060 L1116  pl100 L759
#
#  Agent Action Plan section 0.6.3 permits this consolidation, and here the
#  permission is backed by measurement rather than taken on trust.
# ===========================================================================


def zz070_convert_date(ws: WsDateFormats, to_day: str, date_form: int) -> int:
    """`zz070-Convert-Date`: reformat the run date into the configured form.

    Input is `to-day pic x(10)`, the run date the menu passes down through
    linkage; output is `ws.ws_date`, written in place.

    Args:
        ws: the section's working storage. `ws.ws_date` is overwritten.
        to_day: `to-day pic x(10)` - the run date text, DD/MM/CCYY.
        date_form: `System-Record.Date-Form` on entry.

    Returns:
        The EFFECTIVE `Date-Form`. The COBOL writes a defaulted value straight
        back into the system record, so a caller MUST store this return value
        back into `System-Record.Date-Form` for the migration to stay faithful -
        see the note at the default site below.

    This function does not read a clock (rule R-6): the run date arrives as an
    argument, which is exactly how every in-scope COBOL program receives it.
    """
    #  [general/gl070.cbl:L581]  move to-day to ws-date.
    ws.ws_date = _alphanumeric_move(to_day, DATE_TEXT_LENGTH)

    # -----------------------------------------------------------------------
    #  [general/gl070.cbl:L583-L584]
    #      if       Date-Form = zero
    #               move 1 to Date-Form.
    #
    #  THIS WRITES BACK INTO THE SYSTEM RECORD, and the system record is a table
    #  row (`SYSTEM-REC`), so the write is observable in a state diff and not
    #  merely in memory. It is reproduced by returning the effective value for
    #  the caller to store.
    #
    #  Note that the test is `= zero` and the default is 1: the declared
    #  condition name `Date-Valid-Formats` (values 1 2 3) is NOT used here, so
    #  an out-of-range Date-Form such as 4 is neither defaulted nor rejected -
    #  it simply falls through to the International branch below.
    # -----------------------------------------------------------------------
    if date_form == DATE_FORM_UNSET:
        date_form = DATE_FORM_UK

    #  [general/gl070.cbl:L585-L586]  if Date-UK go to zz070-Exit.
    #  Class 3 section exit -> `zz070-Exit. exit section.` [L600-L601].
    #  The UK form is what `to-day` already holds, so there is nothing to do.
    if date_form_is_uk(date_form):
        return date_form

    # -----------------------------------------------------------------------
    #  [general/gl070.cbl:L587-L591]  if Date-USA ... go to zz070-Exit.
    #  Class 3 section exit.
    # -----------------------------------------------------------------------
    if date_form_is_usa(date_form):
        _swap_days_and_month(ws)  # [L588-L590]
        return date_form

    # -----------------------------------------------------------------------
    #  [general/gl070.cbl:L593-L598]  the International branch, reached by
    #  FALL-THROUGH rather than by testing `Date-Intl`. The source's own comment
    #  is "So its International date format".
    #
    #      move     "ccyy/mm/dd" to ws-date.  *> swap Intl to UK form
    #      move     to-day (7:4) to ws-Intl-Year.
    #      move     to-day (4:2) to ws-Intl-Month.
    #      move     to-day (1:2) to ws-Intl-Days.
    #
    #  The seed literal at [general/gl070.cbl:L595] is moved in purely so that
    #  its "/" characters land at positions 5 and 8; the three reference-modified
    #  moves then overwrite offsets 1-4, 6-7 and 9-10, leaving those two
    #  separators standing. Building the string this way is what makes the
    #  CCYY/MM/DD shape fall out for free.
    #
    #  MEASURED (rule R-6): with `to-day` all spaces the compiled code yields
    #  "    /  /  " - so the literal's LETTERS never survive into the output,
    #  because reference modification always yields exactly the requested length
    #  and fully overwrites its target. Only the separators survive. The
    #  maintainer's inline comment "swap Intl to UK form" describes the opposite
    #  direction from what the code does here, which is UK into International;
    #  the comment is wrong and the code is the specification.
    # -----------------------------------------------------------------------
    ws.ws_date = UK_TO_INTL_SEED  # [L595]
    ws.ws_intl_year = _ref_mod(to_day, 7, 4)  # [L596]
    ws.ws_intl_month = _ref_mod(to_day, 4, 2)  # [L597]
    ws.ws_intl_days = _ref_mod(to_day, 1, 2)  # [L598]

    #  Falls through to `zz070-Exit. exit section.` [L600-L601].
    return date_form


# ===========================================================================
#  zz060-Convert-Date  -  CONSOLIDATED, IDENTICAL IN 6 CARRIERS BUT FOR ONE
#                          TOKEN
# ===========================================================================
#  Reference body: [general/gl070.cbl:L538-L571]. Normalised diff across all six
#  carriers - gl051 L1208, gl070 L538, sl060 L1227, sl100 L743, pl060 L1081,
#  pl100 L724 - shows exactly ONE difference between them:
#
#      -  perform maps03.        <- gl051 and gl070
#      +  perform maps04.        <- sl060, sl100, pl060 and pl100
#
#  Since both wrapper sections have the identical single-statement body, the two
#  spellings invoke the same code and the section is safely consolidated. The
#  wrapper is nonetheless taken as an EXPLICIT, NON-DEFAULTED argument so the
#  calling program states which convention it follows, keeping the distinction
#  visible for traceability (rule R-5).
# ===========================================================================


def zz060_convert_date(
    ws: WsDateFormats,
    maps03_ws: Maps03Ws,
    date_form: int,
    *,
    wrapper: Callable[[Maps03Ws], None],
) -> int:
    """`zz060-Convert-Date`: unpack a binary date, then reformat it for presentation.

    This is `zz070` with a conversion in front of it: input is `u-bin`, not a
    text date, so the wrapper is performed first to turn the binary day number
    into text and only then is the presentation format applied.

    Args:
        ws: the section's working storage. `ws.ws_date` is overwritten.
        maps03_ws: the shared linkage record. `u_bin` is the input; the wrapper
            writes `u_date` in place.
        date_form: `System-Record.Date-Form` on entry.
        wrapper: the wrapper section this program performs - pass `maps03` from
            gl051 or gl070, `maps04` from sl060, sl100, pl060 or pl100. Required
            and never defaulted, so the caller states its own convention.

    Returns:
        The effective `Date-Form`, to be stored back into the system record as
        described in `zz070_convert_date`.

    The section's own header comment at [general/gl070.cbl:L543-L545] claims
    "u-date & ws-Date = spaces if invalid date". That is not quite what happens:
    `ws_unpack` always writes the "00/00/0000" seed first, so a `u_bin` that was
    greater than zero can never come back as spaces. The spaces guard can
    therefore only fire when the caller left `u_date` as spaces AND `u_bin` was
    not greater than zero - in which case `maps04` took its forward text path and
    rejected the empty text. The guard is reproduced as written and the
    misleading comment is left uncorrected; see docs/migration/anomaly-log.md.
    """
    #  [general/gl070.cbl:L547]  perform maps03.  (or maps04 - see above)
    wrapper(maps03_ws)

    # -----------------------------------------------------------------------
    #  [general/gl070.cbl:L548-L550]
    #      if       u-date = spaces
    #               move spaces to ws-Date
    #               go to zz060-Exit.
    #
    #  Class 3 section exit. Compared against figurative SPACES across the whole
    #  declared 10-byte field, so the field is materialised at its full width
    #  before the comparison.
    # -----------------------------------------------------------------------
    if _alphanumeric_move(maps03_ws.u_date, DATE_TEXT_LENGTH) == " " * DATE_TEXT_LENGTH:
        ws.ws_date = " " * DATE_TEXT_LENGTH
        return date_form

    #  [general/gl070.cbl:L551]  move u-date to ws-date.
    ws.ws_date = _alphanumeric_move(maps03_ws.u_date, DATE_TEXT_LENGTH)

    #  [general/gl070.cbl:L553-L554]  the same write-back into the system record
    #  as zz070's; see the note there.
    if date_form == DATE_FORM_UNSET:
        date_form = DATE_FORM_UK

    #  [general/gl070.cbl:L555-L556]  if Date-UK go to zz060-Exit.  Class 3.
    if date_form_is_uk(date_form):
        return date_form

    #  [general/gl070.cbl:L557-L561]  if Date-USA ... go to zz060-Exit.  Class 3.
    if date_form_is_usa(date_form):
        _swap_days_and_month(ws)  # [L558-L560]
        return date_form

    # -----------------------------------------------------------------------
    #  [general/gl070.cbl:L563-L568]  the International branch, again by
    #  fall-through. Identical to zz070's except that it reads the unpacked
    #  `u-date` rather than `to-day`, and it uses the SAME seed literal and the
    #  SAME offsets - (7:4), (4:2), (1:2). Contrast zz050, which uses a
    #  different literal and different offsets because it converts in the
    #  opposite direction.
    # -----------------------------------------------------------------------
    ws.ws_date = UK_TO_INTL_SEED  # [L565]
    ws.ws_intl_year = _ref_mod(maps03_ws.u_date, 7, 4)  # [L566]
    ws.ws_intl_month = _ref_mod(maps03_ws.u_date, 4, 2)  # [L567]
    ws.ws_intl_days = _ref_mod(maps03_ws.u_date, 1, 2)  # [L568]

    #  Falls through to `zz060-Exit. exit section.` [L570-L571].
    return date_form


# ===========================================================================
#  zz050-Validate-Date  -  ⛔ NOT EQUIVALENT ACROSS CARRIERS.
#                             PUBLISHED AS TWO SEPARATE FUNCTIONS.
# ===========================================================================
#  Agent Action Plan section 0.6.3 asserts that these section bodies are
#  "textually equivalent" and so may be consolidated. FOR zz050 THAT IS
#  MEASURABLY FALSE, and consolidating it would lose a caller-visible side
#  effect in one program.
#
#  Normalised diff across all five carriers - gl051 L1169, sl060 L1192,
#  sl100 L708, pl060 L1046, pl100 L689 - puts them in two groups:
#
#    * gl051 ALONE carries three extra statements at
#      [general/gl051.cbl:L1178-L1180], which rewrite the caller's own
#      `ws-test-date` field in place before anything else happens.
#    * sl060, sl100, pl060 and pl100 are byte-identical to one another and have
#      no such statements.
#
#  Two functions therefore, and the mutating variant is NOT reachable through a
#  defaulted argument - a caller has to name it. Agent Action Plan section 0.6.1,
#  on the three disagreeing copies of the moving-average idiom, states the
#  principle this follows: "Normalising them into one helper would be the single
#  easiest way to fail this migration."
#
#  Both variants share the `zz050-test-date` paragraph, which is genuinely
#  common to all five and is reproduced once below.
# ===========================================================================


def zz050_test_date(
    ws: WsDateFormats,
    maps03_ws: Maps03Ws,
    *,
    wrapper: Callable[[Maps03Ws], None],
) -> None:
    """Reproduce the `zz050-test-date` paragraph [general/gl051.cbl:L1200-L1203].

        move     ws-date to u-date.
        move     zero to u-bin.
        perform  maps03.            (or maps04)

    Common to all five carriers of `zz050`. Reached from the UK and USA branches
    by a Class 4 sibling re-dispatch, and by fall-through from the International
    branch.

    ⭐ THE CALLER PRE-ZERO. `move zero to u-bin` is one of the only two places
    in the whole call chain that zeroes the binary field before calling
    `maps04`, and it is the reason `maps04`'s documented "Date errors returned
    as A-Bin equal zero" contract [common/maps04.cbl:L163] appears to hold. It
    does not hold in `maps04` itself - see anomaly #16 there. The other
    pre-zeroing caller is [copybooks/Proc-ACAS-Mapser-RDB.cob:L78].

    Agent Action Plan section 0.6.8 records that "not every in-scope caller has
    been proven to" pre-zero, so this is preserved exactly where the COBOL puts
    it - in the CALLER - rather than being pushed down into `maps04` where it
    would mask the anomaly for every caller at once.

    After this returns, `maps03_ws.u_bin` is non-zero if and only if the date
    was valid. That is the section's entire output contract, per its own header
    comment "u-bin not zero if valid date".
    """
    #  [general/gl051.cbl:L1201]  move ws-date to u-date.
    maps03_ws.u_date = _alphanumeric_move(ws.ws_date, DATE_TEXT_LENGTH)

    #  [general/gl051.cbl:L1202]  move zero to u-bin.   <- the caller pre-zero
    maps03_ws.u_bin = 0

    #  [general/gl051.cbl:L1203]  perform maps03.  (maps04 in the other four)
    wrapper(maps03_ws)

    #  Falls through to `zz050-exit. exit section.` [general/gl051.cbl:L1205-L1206].


def _zz050_validate_date_body(
    ws: WsDateFormats,
    maps03_ws: Maps03Ws,
    date_form: int,
    wrapper: Callable[[Maps03Ws], None],
) -> int:
    """Run the part of `zz050-Validate-Date` that all five carriers share.

    Covers [general/gl051.cbl:L1182-L1203] - everything from `move ws-test-date
    to ws-date` onwards. The three `inspect` statements that precede it in
    gl051 only are NOT here; they belong to `zz050_validate_date_gl051` alone,
    which is the whole point of the split.
    """
    #  [general/gl051.cbl:L1182]  move ws-test-date to ws-date.
    ws.ws_date = _alphanumeric_move(ws.ws_test_date, DATE_TEXT_LENGTH)

    #  [general/gl051.cbl:L1183-L1184]  the same system-record write-back as
    #  zz060 and zz070; see the note in `zz070_convert_date`.
    if date_form == DATE_FORM_UNSET:
        date_form = DATE_FORM_UK

    # -----------------------------------------------------------------------
    #  [general/gl051.cbl:L1185-L1186]  if Date-UK go to zz050-test-date.
    #
    #  Class 4 sibling re-dispatch: the target is a peer PARAGRAPH that performs
    #  work and then itself transfers control to the section exit. So it becomes
    #  a named call followed by an explicit return, not a bare return.
    # -----------------------------------------------------------------------
    if date_form_is_uk(date_form):
        zz050_test_date(ws, maps03_ws, wrapper=wrapper)
        return date_form

    #  [general/gl051.cbl:L1187-L1191]  if Date-USA ... go to zz050-test-date.
    #  Class 4, as above.
    if date_form_is_usa(date_form):
        _swap_days_and_month(ws)  # [L1188-L1190]
        zz050_test_date(ws, maps03_ws, wrapper=wrapper)
        return date_form

    # -----------------------------------------------------------------------
    #  [general/gl051.cbl:L1193-L1198]  the International branch, by
    #  fall-through.
    #
    #      move     "dd/mm/ccyy" to ws-date.  *> swap Intl to UK form
    #      move     ws-test-date (1:4) to ws-Year.
    #      move     ws-test-date (6:2) to ws-Month.
    #      move     ws-test-date (9:2) to ws-Days.
    #
    #  ⚠ THIS IS THE OPPOSITE DIRECTION FROM zz060 AND zz070, and it differs
    #  from them in BOTH details:
    #
    #    * the seed literal is "dd/mm/ccyy", not "ccyy/mm/dd", so the separators
    #      land at positions 3 and 6 rather than 5 and 8;
    #    * the source is read at (1:4), (6:2) and (9:2) - International order -
    #      and stored into the UK-ordered targets ws-Year, ws-Month and ws-Days.
    #
    #  zz060 and zz070 convert UK INTO International; this converts
    #  International INTO UK, because `zz050`'s job is to normalise operator
    #  input for processing. Copy-pasting between the two would silently produce
    #  a wrong date. Confirmed on the compiled logic: "2025/09/21" here yields
    #  "21/09/2025".
    # -----------------------------------------------------------------------
    ws.ws_date = INTL_TO_UK_SEED  # [L1195]
    ws.ws_year = _ref_mod(ws.ws_test_date, 1, 4)  # [L1196]
    ws.ws_month = _ref_mod(ws.ws_test_date, 6, 2)  # [L1197]
    ws.ws_days = _ref_mod(ws.ws_test_date, 9, 2)  # [L1198]

    #  Falls through into the `zz050-test-date` paragraph [L1200].
    zz050_test_date(ws, maps03_ws, wrapper=wrapper)
    return date_form


def zz050_validate_date(
    ws: WsDateFormats,
    maps03_ws: Maps03Ws,
    date_form: int,
    *,
    wrapper: Callable[[Maps03Ws], None],
) -> int:
    """`zz050-Validate-Date` AS CARRIED BY sl060, sl100, pl060 AND pl100.

    Carriers, verified byte-identical to one another:
        sales/sl060.cbl:L1192-L1225
        sales/sl100.cbl:L708-L741
        purchase/pl060.cbl:L1046-L1079
        purchase/pl100.cbl:L689-L722

    Converts operator input in `ws.ws_test_date` from the configured
    presentation format into UK order, then validates it through `maps04`.

    THIS VARIANT DOES NOT MUTATE `ws.ws_test_date`. It has no separator
    normalisation of any kind, so an input using "." or "-" as its separator
    reaches `maps04` unchanged - where `maps04`'s own three `inspect` statements
    then normalise it, but in `maps03_ws.u_date` rather than here. gl051's
    variant additionally normalises the input field itself; use
    `zz050_validate_date_gl051` for that program and only that program.

    Args:
        ws: the section's working storage. `ws.ws_date` is overwritten;
            `ws.ws_test_date` is READ ONLY here.
        maps03_ws: the shared linkage record, written by `zz050_test_date`.
            On return `u_bin` is non-zero if and only if the date was valid.
        date_form: `System-Record.Date-Form` on entry.
        wrapper: `maps04` for all four of this variant's carriers. Required and
            never defaulted.

    Returns:
        The effective `Date-Form`, to be stored back into the system record.
    """
    return _zz050_validate_date_body(ws, maps03_ws, date_form, wrapper)


def zz050_validate_date_gl051(
    ws: WsDateFormats,
    maps03_ws: Maps03Ws,
    date_form: int,
    *,
    wrapper: Callable[[Maps03Ws], None],
) -> int:
    """`zz050-Validate-Date` AS CARRIED BY gl051 ONLY - the divergent variant.

    Carrier: general/gl051.cbl:L1169-L1206.

    Identical to `zz050_validate_date` EXCEPT that it opens with three
    `inspect ... replacing all` statements at [general/gl051.cbl:L1178-L1180]
    which none of the other four carriers has:

        inspect  ws-test-date replacing all "." by "/".
        inspect  ws-test-date replacing all "," by "/".
        inspect  ws-test-date replacing all "-" by "/".

    These rewrite the CALLER'S OWN `ws-test-date` field in place, so gl051's
    working storage is observably different after the call than the other four
    programs' would be for the same input. That divergence is deliberate here,
    not tidied away: this is published as its own named function precisely so
    that it cannot be reached by accident or through a defaulted argument, and
    so that a reader of gl051 finds a function that matches gl051.

    Args:
        ws: the section's working storage. BOTH `ws.ws_test_date` AND
            `ws.ws_date` are overwritten.
        maps03_ws: the shared linkage record, written by `zz050_test_date`.
        date_form: `System-Record.Date-Form` on entry.
        wrapper: `maps03` for gl051 - the anomaly #22 spelling. Required and
            never defaulted.

    Returns:
        The effective `Date-Form`, to be stored back into the system record.
    """
    # -----------------------------------------------------------------------
    #  [general/gl051.cbl:L1178-L1180]  THE THREE STATEMENTS gl051 ALONE HAS.
    #
    #  Applied in the written order "." then "," then "-", each assigning back
    #  to the caller's field. The field is materialised at its declared
    #  10-character width by the first of them, as `maps04` does with its own.
    #
    #  Note that this duplicates work `maps04` will do anyway on `u_date`
    #  [common/maps04.cbl:L132-L134]; the difference, and the only reason this
    #  variant exists, is WHICH FIELD ends up normalised. Here it is gl051's own
    #  `ws-test-date` as well.
    # -----------------------------------------------------------------------
    ws.ws_test_date = _alphanumeric_move(ws.ws_test_date, DATE_TEXT_LENGTH)
    ws.ws_test_date = ws.ws_test_date.replace(".", "/")
    ws.ws_test_date = ws.ws_test_date.replace(",", "/")
    ws.ws_test_date = ws.ws_test_date.replace("-", "/")

    return _zz050_validate_date_body(ws, maps03_ws, date_form, wrapper)


# ===========================================================================
#  THE PUBLIC SURFACE
# ===========================================================================
#  Grouped as the COBOL groups it, so that a reader coming from the source finds
#  what they are looking for where they expect it. The two `zz050` variants are
#  BOTH exported and neither is the "default" one; the storage helpers and
#  `_zz050_validate_date_body` stay private because they are mechanics rather
#  than migrated paragraphs.
# ===========================================================================
#  Sorted alphabetically so that this module conforms to the same lint
#  configuration as every other module in the package (ruff RUF022). The
#  COBOL-source-ordered inventory - which program and paragraph each name
#  reproduces - is in the module docstring above and at each definition site;
#  the export list is not where rule R-5 traceability is recorded.
#  Ordered constants-then-classes-then-functions, each group alphabetical, so
#  that this module satisfies the same lint gate as every other module in the
#  package. The COBOL-source-ordered inventory - which program and which
#  paragraph each name reproduces - is in the module docstring above and at
#  every definition site. The export list is not where rule R-5 traceability
#  is recorded, so its ordering carries no meaning.
__all__: Final[tuple[str, ...]] = (
    "COBOL_DATE_EPOCH_ORDINAL",
    "COBOL_MAX_DATE_INTEGER",
    "COBOL_MAX_DATE_YEAR",
    "COBOL_MIN_DATE_INTEGER",
    "COBOL_MIN_DATE_YEAR",
    "DATE_FORM_INTL",
    "DATE_FORM_UK",
    "DATE_FORM_UNSET",
    "DATE_FORM_USA",
    "DATE_TEXT_LENGTH",
    "INTL_TO_UK_SEED",
    "TEST_DATE_LENGTH",
    "UK_TO_INTL_SEED",
    "UNPACK_SEED",
    "Maps03Ws",
    "WsDateFormats",
    "date_form_is_intl",
    "date_form_is_uk",
    "date_form_is_usa",
    "date_of_integer",
    "integer_of_date",
    "maps03",
    "maps04",
    "test_date_yyyymmdd",
    "ws_unpack",
    "zz050_test_date",
    "zz050_validate_date",
    "zz050_validate_date_gl051",
    "zz060_convert_date",
    "zz070_convert_date",
)
