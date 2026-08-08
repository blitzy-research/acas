"""`MOVE` receiving-field semantics - parity file 5 of 14 in ``tests/arithmetic/``.

WHAT THIS FILE PROVES. A COBOL ``MOVE`` is not an assignment: the RECEIVING field
decides everything about the value that lands. This file pins the five rules the
migrated cycle depends on, one test group each:

* **Alphanumeric moves are left-justified**, padded on the RIGHT with spaces and
  truncated on the RIGHT. A LEADING space is content; only TRAILING spaces are padding.
* **Numeric moves align on the implied decimal point** and then truncate or zero-pad at
  BOTH ends independently - low-order digits are discarded, high-order digits are
  discarded, and the low-order end is zero-filled when the sender is shorter.
* **Multiple receivers each apply their own rules**, independently, in receiver order.
* **Reference modification is 1-BASED on both the sending and the receiving side.**
* **The figurative constants** behave as the frozen sources require, and only the two
  families that actually occur are recognised.

It also LOCKS anomaly **A-13** - see the A-13 section below - by proving that the
numeric class condition is a plain predicate that never raises.

------------------------------------------------------------------------------------
PROVENANCE OF THE RULES
------------------------------------------------------------------------------------
The six binding rules **R-1 ... R-6** live in the Technical Specification section 0.7.2
and are restated below as they bear on this file; where the specification is silent,
enterprise-standard best practice applies.

**R-1 - no COBOL at runtime.** ``tests/arithmetic/*`` touch neither COBOL nor a
database. This file imports only ``acas_posting.cobol`` and ``acas_posting.dictionary``,
starts no process, opens no socket and reads no file other than the generated data
dictionary. It passes on a host with no Docker, no MariaDB and no GnuCOBOL. The compiled
oracle lives only under ``harness/`` and is consumed only by ``tests/scenarios/*`` and
``tests/determinism/*``.

**R-2 - zero binary floating point.** Every value here is a ``decimal.Decimal``, an
``int`` or a ``str``. There is no binary floating-point carrier anywhere - no such
literal, no approximate-equality helper, no closeness helper and no tolerance of any
kind: an accounting value is either exactly right or it is wrong, and every comparison
below is exact equality. The ambient ``decimal`` context is never read and never mutated
- the descriptors carry their own precision, and ``acas_posting.cobol.arithmetic``
supplies its own context - so nothing here can perturb another test.

 EVERY ``Decimal`` BELOW IS CONSTRUCTED FROM A STRING, uniformly and on purpose,
as the migrated modules themselves do. A linter will offer to shorten the
integer-valued ones to a bare numeric literal; do not accept it. The value of the
convention is that it
holds with no exceptions: once a bare literal is acceptable, the day somebody writes a
fractional one it is a binary ``float`` that has already lost precision before
``Decimal`` ever sees it, and R-2 is breached silently. Quoting every literal makes that
entire class of error unwritable.

**R-3 - no new validations.** ``move.is_numeric_class`` returns a plain boolean and
never raises on data; ``move`` itself truncates SILENTLY at both ends. ``ON SIZE ERROR``
occurs ZERO times across the twelve in-scope programs, so there is no diagnostic to
reproduce and this file asserts none. Execution is strictly sequential - no parallel
test runner, no threads.

**R-4 - legacy anomalies are reproduced, never fixed.** "A defect reproduced is
correct; a defect fixed is a failure", and each reproduction site names its COBOL
locator so that "a future well-intentioned correction fails the suite rather than
passing unnoticed". Two consequences are visible below: A-13 is locked by its own test,
and the two ``STRING`` shapes are tested SEPARATELY with a comment forbidding their
unification.

**R-5 - full traceability.** Every descriptor arrives either by a data-dictionary key or
by a ``source_locator`` that was read from the frozen source and verified to declare
exactly that picture. Every assertion carries the ``[path:Lnnn]`` it came from.
``pytest-cov`` is evidence, never a gate - this file sets no coverage threshold.

**R-6 - compiled behaviour is the tie-breaker.** Expected values come from the audited
semantics layer, which in turn records what was measured against the compiled oracle.
Where a question has no compiled answer the assertion is marked
``xfail(strict=True)`` against a NAMED question id, so the suite stays green while the
question is open and turns RED the moment somebody makes the un-arbitrated reading come
true. Every question this file names IS measured, so the policy is recorded here rather
than exercised: what stands in its place is an assertion of the reading the compiler
produced, plus an assertion AGAINST the one it refuted.

Section 0.8.4 also binds: there is no timing assertion and no performance measurement
anywhere in this file.

------------------------------------------------------------------------------------
THE FOUR QUESTION IDS THIS FILE OWNS, ALL FOUR NOW MEASURED
------------------------------------------------------------------------------------
Each id is the one ``acas_posting.cobol.move`` itself publishes, not a new label. All
four are MEASURED on GnuCOBOL 3.2.0, and in every case the measurement REFUTED the naive
reading - what an engineer would guess before consulting the compiler - so each test
asserts the measurement and the refutation rather than the guess. There is no ``xfail``
in this file, and a change back towards a naive reading fails by name rather than passing
unnoticed. That is the same R-4/R-6 lock, working from the answer rather than from the
question.

* **Q-9  - ``MOVE SPACE`` into a numeric receiver.** INEXPRESSIBLE: measured as a
  GnuCOBOL 3.2 compile error, so the statement cannot exist in the compiled system and
  there is no resulting representation to reproduce. Naive reading: the receiver ends up
  holding spaces.
* **Q-10 - reference modification past the end of the item.** UNREPRODUCIBLE: a literal
  out-of-range range does not compile, and a computed one reads ADJACENT STORAGE, which
  a Python ``str`` does not have. Naive reading: the range is clamped to what fits.
* **Q-11 - a ``STRING`` pointer beyond the receiver.** Measured as a silent no-op:
  nothing is written AND the pointer does not advance. Naive reading: the pointer
  advances by the source length even though nothing was written.
* **Q-14 - an edited picture outside the Z-then-9 shape.** UNOBSERVABLE: the only
  observable this migration has is table state, and every other edited picture in the
  frozen sources receives into a print line. Naive reading: it renders anyway.

One value that IS produced, and is therefore asserted UNCONDITIONALLY rather than
xfailed, is the ``z(7)9`` rendering of ZERO - seven suppressed positions then the
always-printing final ``9``. See the A-4.7 section for why that one reaches a real
column and why the assertion is itself the lock.

------------------------------------------------------------------------------------
ANOMALY A-13 - THE TWO ENTIRELY SILENT SKIPS
------------------------------------------------------------------------------------
``general/gl072.cbl`` abandons a record in two places with no message, no counter and no
trace whatsoever. Verbatim from the frozen source::

    general/gl072.cbl:L291-L292     if       post-batch  not numeric
                                    go to  loop.

    general/gl072.cbl:L306-L307     if       we-error  equal  999
                                    go to  loop.

The first turns on the numeric CLASS CONDITION, which is why
``move.is_numeric_class`` must be a predicate and never an exception: if it raised on a
non-numeric batch number the record would abort the run instead of being skipped, which
is a behaviour change. Adding a warning would be an added behaviour too, and is equally
forbidden (R-3, R-4).

LOCATOR NOTE, recorded rather than silently reconciled: the anomaly register in section
0.6.7 cites ``L289-L290`` and ``L303-L304``. Those lines were read and they hold
``go to end-run.`` and ``move post-batch to save-batch`` - the register's figures point
one statement either side. The locators quoted above are the verbatim statements, read
from the frozen file, and ``acas_posting/cobol/move.py`` cites the same ``L291-L292``.

------------------------------------------------------------------------------------
CENSUSES - so a reader knows every absence below is deliberate
------------------------------------------------------------------------------------
``MOVE`` LINES per in-scope program, as ``move.MOVE_CENSUS`` publishes them and as
``test_move_census_is_internally_consistent`` re-checks: gl051 157 - gl070 66 -
**gl071 0, because it is a pure sort** - gl072 59 - gl080 48 - sl055 92 - sl060 177 -
sl100 124 - pl055 91 - pl060 165 - pl100 122 - irs030 190, totalling **1291** lines.
``move.MOVE_STATEMENT_CENSUS`` counts only the statements the compiler executes,
excluding commented-out and continuation lines, and totals **1250**. Section 0.4.1
quotes 1290 with sl055 at 91; a line count of ``sales/sl055.cbl`` returns 92, which is
the figure the audited module carries and the figure asserted here.

Reference-modification ``(offset:length)`` pairs, most frequent first, totalling **83**
live uses: ``(7:4)`` x16 - ``(4:2)`` x16 - ``(1:2)`` x16 - ``(9:2)`` x9 - ``(1:6)`` x8 -
``(6:2)`` x5 - ``(1:4)`` x5 - ``(7:2)`` x4 - ``(1:1)`` x3 - ``(1:22)`` x1.

Figurative constants: only ``ZERO``/``ZEROS``/``ZEROES`` and ``SPACE``/``SPACES`` occur,
at 532 / 12 / 0 / 64 / 138 uses respectively. **Zero occurrences, and therefore neither
implemented nor asserted:** ``HIGH-VALUES``, ``LOW-VALUES``, ``ALL "x"`` as a sending
operand, ``QUOTES``, ``MOVE CORRESPONDING``, ``JUSTIFIED``, ``UNSTRING`` and
``ON OVERFLOW``. ``test_forms_that_never_occur_are_not_implemented`` asserts that census
so the absence is machine-checked rather than merely claimed.

Edited pictures: ``move.EDIT_SYMBOLS_IMPLEMENTED`` is ``('Z', '9')`` and nothing else,
because a grep for edit characters inside ``pic`` clauses across all of
``copybooks/*.cob`` returns ZERO matches - no edited value reaches a column except
through the single ``sales/sl060.cbl`` path exercised in the A-4.7 group below.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from acas_posting.cobol import field as cobol_field
from acas_posting.cobol import move, picture
from acas_posting.cobol import usage as cobol_usage
from acas_posting.dictionary import loader, model

pytestmark = pytest.mark.arithmetic


# ---------------------------------------------------------------------------
#  DESCRIPTOR RESOLUTION
# ---------------------------------------------------------------------------
#
# Two routes, and which one a field takes is not a matter of taste (R-5):
#
#  * A field the generated dictionary catalogues arrives by its DICTIONARY KEY, so the
#  assertion is traceable to the copybook declaration, the bridge host variable and
#  the MySQL column all three - `loader.cite` prints that triple.
#  * A field that never reaches a table - program-local working storage and print-line
#  items - has no dictionary key, so it arrives through the picture parser carrying a
#  SOURCE LOCATOR. `FieldDescriptor.__post_init__` rejects a descriptor with neither,
#  which is the invariant that makes an untraceable assertion impossible to write.
#
# Every locator below was read from the frozen file and verified to declare exactly the
# picture it is cited for. Nothing under common/, copybooks/, general/, sales/,
# purchase/, irs/, stock/ or mysql/ is read at runtime, modified, or touched in any way.


def _from_dictionary(key: str) -> cobol_field.FieldDescriptor:
    """Resolve a dictionary key defensively, tolerating case and column-name drift.

    `FieldDescriptor.from_dictionary_key` raises `loader.DictionaryKeyError` - a
    `KeyError` subclass - on any near miss, and there are two near misses worth
    surviving here. Lookup is exact and case-sensitive, so a key written in the wrong
    case fails; and a key's field half is the COLUMN name, which does not always match
    the copybook's own field name. `GLPOSTING-REC.POST-DAT` is the live example: the
    copybook declares `03  Post-Date       pic x(8).`
    [copybooks/wspost.cob:L18] while the column shortens it to `POST-DAT`. That is the
    same bridge-boundary drift section 0.6.2 documents, and it is a fact about the
    frozen system rather than a defect to correct.

    So on a miss, scan the table's own entries and match either half.

    This is deliberately local to this file: it is test-side robustness, not a new
    lookup rule for the migration. Relaxing `loader` itself would be a new validation
    rule and is forbidden (R-3).

    Args:
        key: The `TABLE-REC.FIELD-NAME` dictionary key, by column or copybook name.

    Returns:
        The catalogued descriptor.

    Raises:
        loader.DictionaryKeyError: No entry of that table matches under either name.
    """
    try:
        return cobol_field.FieldDescriptor.from_dictionary_key(key)
    except loader.DictionaryKeyError:
        table, _, wanted = key.partition(".")
        target = wanted.casefold()
        for entry in loader.entries_for_table(table):
            candidates = {entry.key.rpartition(".")[2].casefold()}
            if entry.copybook is not None:
                candidates.add(entry.copybook.name.casefold())
            if target in candidates:
                return cobol_field.FieldDescriptor.from_dictionary_key(entry.key)
        raise


def _working_storage(
    clauses: str, *, name: str, source_locator: str
) -> cobol_field.FieldDescriptor:
    """Describe a program-local item from the clauses its own declaration writes.

    Args:
        clauses: The picture and usage clauses, exactly as the frozen line writes them.
        name: The field name, verbatim from that line.
        source_locator: `<path>:L<n>`, the line that declares it.

    Returns:
        The descriptor, carrying the locator as its only provenance.
    """
    return picture.descriptor_for(
        clauses, name=name, source_locator=source_locator
    )


# --- Catalogued fields: real columns, reached by dictionary key -------------

#: `03  Post-Legend     pic x(32).` - a REAL COLUMN, and the receiver of the only
#: edited value that ever reaches the database. [copybooks/wspost.cob:L24]
POST_LEGEND = _from_dictionary("GLPOSTING-REC.POST-LEGEND")

#: `03  Post-Amount     pic s9(8)v99.` - the signed money field every GL posting
#: writes. [copybooks/wspost.cob:L23]
POST_AMOUNT = _from_dictionary("GLPOSTING-REC.POST-AMOUNT")

#: `03  Post-Date       pic x(8).` - the eight-character receiver of the two-statement
#: reference-modification pair. [copybooks/wspost.cob:L18] Keyed by the COLUMN name,
#: which the bridge shortens to `POST-DAT`; the defensive resolver above accepts either
#: spelling, and `test_post_date_is_keyed_by_its_column_name` pins the drift.
POST_DATE = _from_dictionary("GLPOSTING-REC.POST-DAT")

#: `05  Input-Gross     pic 9(9)v99.` under `03  Amounts  comp-3.` - UNSIGNED, so a
#: negative sender loses its sign on store. [copybooks/wsbatch.cob:L40-L41]
INPUT_GROSS = _from_dictionary("GLBATCH-REC.INPUT-GROSS")

#: `05  Entered         binary-long.` - SIGNED with scale zero, which is what makes
#: truncation toward zero observable on a negative value. [copybooks/wsbatch.cob:L36]
ENTERED = _from_dictionary("GLBATCH-REC.ENTERED")


# --- Program-local items: no column, so a locator is their only provenance --

#: `05  ws-year         pic x(4).` [general/gl070.cbl:L182]
WS_YEAR = _working_storage(
    "pic x(4)", name="ws-year", source_locator="general/gl070.cbl:L182"
)

#: `05  WS-Batch-Nos       pic 9(5).` - the third receiver of the three-receiver MOVE.
#: [copybooks/wsbatch.cob:L19]
WS_BATCH_NOS = _working_storage(
    "pic 9(5)", name="WS-Batch-Nos", source_locator="copybooks/wsbatch.cob:L19"
)

#: `03  l4-batch            pic z(4)9.` - an EDITED print field, and the first receiver
#: of that same statement. [general/gl051.cbl:L289]
L4_BATCH = _working_storage(
    "pic z(4)9", name="l4-batch", source_locator="general/gl051.cbl:L289"
)

#: `03  save-batch          pic 9(5)   comp  value zero.` - the second receiver: a plain
#: working-storage binary item. [general/gl051.cbl:L174]
SAVE_BATCH = _working_storage(
    "pic 9(5) comp", name="save-batch", source_locator="general/gl051.cbl:L174"
)

#: `03  account-in          pic 9(4)v99.` - four integer digits, so a six-figure sender
#: loses its high-order digits silently. [general/gl051.cbl:L178]
ACCOUNT_IN = _working_storage(
    "pic 9(4)v99", name="account-in", source_locator="general/gl051.cbl:L178"
)

#: `03  ws-vat-rate         pic 99v99  comp   value zero.` - only TWO integer digits.
#: [general/gl051.cbl:L183]
WS_VAT_RATE = _working_storage(
    "pic 99v99 comp", name="ws-vat-rate", source_locator="general/gl051.cbl:L183"
)

#: `03  tot-dr          pic 9(8)v99     value zero.` [general/gl072.cbl:L165]
TOT_DR = _working_storage(
    "pic 9(8)v99", name="tot-dr", source_locator="general/gl072.cbl:L165"
)

#: `03  tot-cr          pic 9(8)v99     value zero.` [general/gl072.cbl:L166]
TOT_CR = _working_storage(
    "pic 9(8)v99", name="tot-cr", source_locator="general/gl072.cbl:L166"
)

#: `03  ws-env-lines    pic 999       value zero.` - a deliberately NARROW receiver,
#: used only to show that swapping one receiver changes only its own element.
#: [general/gl072.cbl:L168]
WS_ENV_LINES = _working_storage(
    "pic 999", name="ws-env-lines", source_locator="general/gl072.cbl:L168"
)

#: `03  l6-legend           pic x(32).` - the print-line legend that receives
#: "Brought Forward". [general/gl072.cbl:L245]
L6_LEGEND = _working_storage(
    "pic x(32)", name="l6-legend", source_locator="general/gl072.cbl:L245"
)

#: `03  l6-balance          pic z(7)9.99cr blank when zero.` - an edited picture OUTSIDE
#: the Z-then-9 shape, and the concrete subject of question Q-14.
#: [general/gl072.cbl:L237]
L6_BALANCE = _working_storage(
    "pic z(7)9.99cr", name="l6-balance", source_locator="general/gl072.cbl:L237"
)

#: `03  m               pic z(7)9.` - the edited work field whose rendering reaches
#: Post-Legend, hence the database. [sales/sl060.cbl:L213]
M_EDITED = _working_storage(
    "pic z(7)9", name="m", source_locator="sales/sl060.cbl:L213"
)

#: `03  b               binary-char           value zero.` - the INSPECT tally item.
#: Signed with scale zero. [sales/sl060.cbl:L214]
B_TALLY = _working_storage(
    "binary-char", name="b", source_locator="sales/sl060.cbl:L214"
)

#: `03  k               pic 9(5).` - a numeric DISPLAY sender, whose byte image is what
#: a STRING contributes. [sales/sl060.cbl:L212]
K_ITEM = _working_storage(
    "pic 9(5)", name="k", source_locator="sales/sl060.cbl:L212"
)

#: `03  u-date          pic x(10).` - the ten-character UK date that both
#: reference-modification statements read. [copybooks/wsmaps03.cob:L7]
U_DATE = _working_storage(
    "pic x(10)", name="u-date", source_locator="copybooks/wsmaps03.cob:L7"
)

#: The pinned run date every assertion below uses, in the DD/MM/CCYY form
#: `01  to-day              pic x(10).` carries [general/gl070.cbl:L243]. A literal
#: rather than a clock read: this tier takes no clock at all (R-6).
RUN_DATE_TEXT = "21/09/2025"


# ---------------------------------------------------------------------------
#  4.1  ALPHANUMERIC MOVE - left-justified, padded and truncated on the RIGHT
# ---------------------------------------------------------------------------


class TestAlphanumericMoveTruncatesAndPadsOnTheRight:
    """A sender longer than the receiver loses its TAIL; a shorter one gains spaces.

    The direction is the whole point. Getting it backwards would corrupt every legend,
    description and date text the cycle writes, and would do so silently, because
    `ON SIZE ERROR` occurs ZERO times across the twelve in-scope programs (R-3).
    """

    def test_sender_longer_than_receiver_loses_its_tail(self) -> None:
        # `05  ws-year         pic x(4).` [general/gl070.cbl:L182] - a ten-character
        # sender keeps its FIRST four characters, not its last four.
        assert move.move("ABCDEFGHIJ", WS_YEAR) == "ABCD"

    def test_sender_shorter_than_receiver_is_padded_on_the_right(self) -> None:
        # Two characters into `pic x(4)` [general/gl070.cbl:L182]: the padding goes to
        # the RIGHT, so the receiver is "AB  " and never "  AB".
        assert move.move("AB", WS_YEAR) == "AB  "
        assert move.move("AB", WS_YEAR) != "  AB"

    def test_a_leading_space_is_content_and_only_trailing_spaces_are_padding(
        self,
    ) -> None:
        # This is the distinction the whole INSPECT TALLYING FOR LEADING SPACE idiom at
        # [sales/sl060.cbl:L1087] depends on: a leading space occupies a character
        # position exactly as a letter does, and is counted, so it cannot be treated as
        # padding to be stripped on the way in.
        assert move.move(" AB", WS_YEAR) == " AB "

    def test_a_forty_character_legend_keeps_its_first_thirty_two_silently(self) -> None:
        # `03  Post-Legend     pic x(32).` [copybooks/wspost.cob:L24] is a REAL COLUMN,
        # so this truncation is visible in a table dump. It must happen, and it must
        # happen without a diagnostic (R-3).
        legend = "Sales Invoice 12345 : Dykegrove Limited*"
        assert len(legend) == 40
        stored = move.move(legend, POST_LEGEND)
        assert stored == legend[:32]
        assert len(stored) == 32
        # The receiver's own width, not the sender's, decides the result.
        assert POST_LEGEND.character_length == 32

    def test_brought_forward_is_padded_out_to_the_full_legend_width(self) -> None:
        # `move     "Brought Forward"  to  l6-legend.` [general/gl072.cbl:L429] into
        # `03  l6-legend           pic x(32).` [general/gl072.cbl:L245].
        stored = move.move("Brought Forward", L6_LEGEND)
        assert stored == "Brought Forward" + " " * 17
        assert len(stored) == 32

    def test_an_alphanumeric_receiver_carries_str(self) -> None:
        # `03  Post-Legend     pic x(32).` [copybooks/wspost.cob:L24] and
        # `03  l6-legend           pic x(32).` [general/gl072.cbl:L245].
        # `usage.python_storage_for` is the single rule that decides the carrier, and
        # for an alphanumeric item it is `str` - never bytes, never a number.
        assert POST_LEGEND.python_storage is model.CobolPythonStorage.STR
        assert (
            cobol_usage.python_storage_for(model.Usage.ALPHANUMERIC, None)
            is model.CobolPythonStorage.STR
        )
        assert isinstance(move.move("Brought Forward", L6_LEGEND), str)

    def test_every_catalogued_field_here_cites_its_full_provenance(self) -> None:
        # R-5 made mechanical: a catalogued field's citation names the copybook
        # declaration, the bridge host variable and the MySQL column all three, so an
        # assertion about it is traceable without reading this file's comments.
        citation = loader.cite("GLPOSTING-REC.POST-LEGEND")
        assert "copybooks/wspost.cob:L24" in citation
        assert POST_LEGEND.dictionary_key == "GLPOSTING-REC.POST-LEGEND"
        # A program-local item has no key, so its locator is its only provenance - and
        # the descriptor layer refuses to exist without one.
        assert L6_LEGEND.dictionary_key is None
        assert L6_LEGEND.source_locator == "general/gl072.cbl:L245"


# ---------------------------------------------------------------------------
#  4.2  NUMERIC MOVE - aligns on the implied decimal point, then truncates or
#  zero-pads at BOTH ends
# ---------------------------------------------------------------------------


class TestNumericMoveAlignsOnTheImpliedDecimalPoint:
    """The two ends are independent, and BOTH are silent.

    A numeric `MOVE` lines the sender's implied decimal point up with the receiver's and
    then fills the receiver's digit positions. Positions the sender cannot reach are
    zero-filled; sender digits the receiver has no room for are DISCARDED -
    low-order and high-order alike, with no diagnostic either way.
    """

    def test_low_order_digits_are_truncated_not_rounded(self) -> None:
        # `03  Post-Amount     pic s9(8)v99.` [copybooks/wspost.cob:L23] has two decimal
        # places, so the third is dropped. 123.456 becomes 123.45 - NOT 123.46. COBOL
        # truncates toward zero on store unless ROUNDED is written, and there are
        # exactly
        # five ROUNDED sites in the whole in-scope cycle, none of them here.
        assert move.move(Decimal("123.456"), POST_AMOUNT) == Decimal("123.45")
        assert move.move(Decimal("123.456"), POST_AMOUNT) != Decimal("123.46")
        assert cobol_field.TRUNCATING_STORE == "ROUND_DOWN"

    def test_the_low_order_end_is_zero_padded_when_the_sender_is_shorter(self) -> None:
        # An integer 7 into `pic s9(8)v99` [copybooks/wspost.cob:L23] acquires the two
        # decimal positions the receiver declares: the scale is the RECEIVER's.
        stored = move.move(Decimal("7"), POST_AMOUNT)
        assert stored == Decimal("7.00")
        # The exponent, not merely the numeric value, matches the receiver's scale -
        # this
        # is what makes a dumped column compare equal without a normalisation step.
        assert stored.as_tuple().exponent == -2

    def test_high_order_digits_are_truncated_silently(self) -> None:
        # `03  account-in          pic 9(4)v99.` [general/gl051.cbl:L178] declares FOUR
        # integer digits. A six-figure sender loses its two most significant digits and
        # nothing is reported: ON SIZE ERROR occurs ZERO times across the twelve
        # in-scope
        # programs, so there is no diagnostic path to reproduce (R-3).
        assert move.move(Decimal("123456.78"), ACCOUNT_IN) == Decimal("3456.78")
        # `03  ws-vat-rate         pic 99v99  comp   value zero.`
        # [general/gl051.cbl:L183] declares only TWO, and loses four.
        assert move.move(Decimal("123456.78"), WS_VAT_RATE) == Decimal("56.78")
        # `03  tot-dr          pic 9(8)v99     value zero.` [general/gl072.cbl:L165]
        # declares eight, and loses one.
        assert move.move(Decimal("123456789.99"), TOT_DR) == Decimal("23456789.99")

    def test_high_order_truncation_raises_nothing_at_all(self) -> None:
        # `03  ws-vat-rate         pic 99v99  comp   value zero.`
        # [general/gl051.cbl:L183], the field that feeds gl051's two ROUNDED VAT
        # computes.
        # Stated as its own assertion because it is the R-3 guarantee, not a side
        # effect:
        # the value is simply wrong-and-stored, exactly as the compiled program leaves
        # it. `pytest.raises` is deliberately absent - a passing call IS the assertion.
        assert move.move(Decimal("999999999.99"), WS_VAT_RATE) == Decimal("99.99")
        assert move.move(Decimal("0.001"), WS_VAT_RATE) == Decimal("0.00")

    def test_a_negative_sender_loses_its_sign_in_an_unsigned_receiver(self) -> None:
        # `05  Input-Gross     pic 9(9)v99.` under `03  Amounts  comp-3.`
        # [copybooks/wsbatch.cob:L40-L41] is UNSIGNED, so the magnitude survives and the
        # sign does not. The batch control totals are all declared this way, which is
        # why
        # the gate compares magnitudes.
        assert INPUT_GROSS.signed is False
        assert move.move(Decimal("-5.00"), INPUT_GROSS) == Decimal("5.00")

    def test_a_signed_receiver_keeps_the_sign(self) -> None:
        # The contrast that proves the previous test is about the RECEIVER and not about
        # `move`: `pic s9(8)v99` [copybooks/wspost.cob:L23] is signed, so -5.00 stays
        # negative. Monetary fields are signed at all three layers and pass through
        # cleanly; the narrowing is specific rather than systemic.
        assert POST_AMOUNT.signed is True
        assert move.move(Decimal("-5.00"), POST_AMOUNT) == Decimal("-5.00")

    def test_truncation_is_toward_zero_for_a_negative_value(self) -> None:
        # The single most important sign in the file. `05  Entered  binary-long.`
        # [copybooks/wsbatch.cob:L36] has scale zero, so -1.5 stores as -1 and NEVER as
        # -2: COBOL truncates toward zero, it does not floor. Flooring would move a
        # penny
        # on every negated credit leg in the cycle.
        assert move.move(Decimal("-1.5"), ENTERED) == -1
        assert move.move(Decimal("-1.5"), ENTERED) != -2
        assert move.move(Decimal("1.5"), ENTERED) == 1
        # -0.9 collapses to zero rather than to -1, for the same reason.
        assert move.move(Decimal("-0.9"), ENTERED) == 0

    def test_the_carrier_is_decimal_for_a_scaled_field_and_int_otherwise(self) -> None:
        # `03  Post-Amount     pic s9(8)v99.` [copybooks/wspost.cob:L23] against
        # `05  Entered         binary-long.` [copybooks/wsbatch.cob:L36] - a scaled
        # field
        # and a binary one, declared five copybook lines apart in the same cycle.
        # One rule decides this for every field in the migration -
        # `usage.python_storage_for(usage, scale)` - so the carrier is derived from the
        # declaration rather than chosen per field.
        assert (
            cobol_usage.python_storage_for(model.Usage.DISPLAY, 2)
            is model.CobolPythonStorage.DECIMAL
        )
        assert (
            cobol_usage.python_storage_for(model.Usage.DISPLAY, 0)
            is model.CobolPythonStorage.INT
        )
        assert (
            cobol_usage.python_storage_for(model.Usage.BINARY_LONG, 0)
            is model.CobolPythonStorage.INT
        )
        # And the descriptors agree with it.
        assert POST_AMOUNT.python_storage is model.CobolPythonStorage.DECIMAL
        assert ENTERED.python_storage is model.CobolPythonStorage.INT
        # The binary family is `int` because its width is a byte count, not a digit
        # count - which is precisely what makes integer truncation reproducible.
        assert cobol_usage.BINARY_WIDTH_BYTES[model.Usage.BINARY_LONG] == 4
        assert cobol_usage.BINARY_WIDTH_BYTES[model.Usage.BINARY_CHAR] == 1

    @pytest.mark.parametrize(
        ("sender", "receiver", "expected_type"),
        [
            (Decimal("123.45"), POST_AMOUNT, Decimal),
            (Decimal("1.00"), INPUT_GROSS, Decimal),
            (Decimal("1.5"), ENTERED, int),
            (Decimal("1.5"), B_TALLY, int),
            (Decimal("42"), WS_BATCH_NOS, int),
        ],
    )
    def test_no_stored_value_is_ever_a_binary_floating_point_carrier(
        self,
        sender: Decimal,
        receiver: cobol_field.FieldDescriptor,
        expected_type: type,
    ) -> None:
        # Five receivers spanning five storage classes: [copybooks/wspost.cob:L23],
        # [copybooks/wsbatch.cob:L41], [copybooks/wsbatch.cob:L36],
        # [sales/sl060.cbl:L214] and [copybooks/wsbatch.cob:L19].
        # R-2 as an executable assertion rather than a code-review promise. `bool` is
        # excluded explicitly because it is an `int` subclass and would otherwise slip
        # through the `int` check.
        stored = move.move(sender, receiver)
        assert type(stored) is expected_type
        assert not isinstance(stored, bool)



# ---------------------------------------------------------------------------
#  4.3  MULTIPLE RECEIVERS - each applies its OWN rules, independently
# ---------------------------------------------------------------------------


class TestMultipleReceiversEachApplyTheirOwnRules:
    """One sender, several receivers, and no receiver influences another.

    Verbatim, [general/gl051.cbl:L1017]::

        move   batch  to  l4-batch save-batch WS-Batch-Nos

    Three receivers with three DIFFERENT pictures in one statement, which is why
    `move_to_all` converts once per receiver rather than converting once and copying:

      * `03  l4-batch            pic z(4)9.`                [general/gl051.cbl:L289]
        - an EDITED print field, so it yields characters.
      * `03  save-batch          pic 9(5)   comp  value zero.`
                                                            [general/gl051.cbl:L174]
        - a plain working-storage binary item, so it yields an int.
      * `05  WS-Batch-Nos       pic 9(5).`                   [copybooks/wsbatch.cob:L19]
        - a numeric DISPLAY item, so it also yields an int, but by a different usage.

    The other verified multiple-receiver sites in the in-scope set, which share this one
    mechanism and so need no separate test: [general/gl051.cbl:L982],
    [general/gl051.cbl:L1041], [general/gl070.cbl:L400], [general/gl072.cbl:L281],
    [general/gl072.cbl:L411], [general/gl072.cbl:L452], [sales/sl055.cbl:L539],
    [sales/sl055.cbl:L653], [sales/sl055.cbl:L655], [sales/sl060.cbl:L477],
    [sales/sl060.cbl:L489], [sales/sl060.cbl:L546] and [sales/sl060.cbl:L941].
    """

    def test_results_come_back_as_a_tuple_in_receiver_order(self) -> None:
        # [general/gl051.cbl:L1017]. The order is the statement's order, so a reader
        # can diff the two argument lists position by position.
        stored = move.move_to_all(
            Decimal("42"), (L4_BATCH, SAVE_BATCH, WS_BATCH_NOS)
        )
        assert isinstance(stored, tuple)
        assert len(stored) == 3
        assert stored == ("   42", 42, 42)

    def test_each_element_reflects_only_its_own_picture(self) -> None:
        # The edited receiver renders characters at its own width while the two numeric
        # receivers carry ints - from ONE sending value, in ONE statement.
        edited, binary_item, display_item = move.move_to_all(
            Decimal("42"), (L4_BATCH, SAVE_BATCH, WS_BATCH_NOS)
        )
        # `pic z(4)9` is five positions: four suppressible, one always printing.
        assert isinstance(edited, str)
        assert edited == "   42"
        assert len(edited) == 5
        assert type(binary_item) is int
        assert type(display_item) is int
        assert L4_BATCH.is_edited is True
        assert SAVE_BATCH.usage is model.Usage.COMP
        assert WS_BATCH_NOS.usage is model.Usage.DISPLAY

    def test_changing_one_receivers_picture_changes_only_that_element(self) -> None:
        # Independence, demonstrated rather than asserted in the abstract. Swap the
        # third
        # receiver for the deliberately narrow
        # `03  ws-env-lines    pic 999       value zero.` [general/gl072.cbl:L168] and
        # only the third element moves; the other two are byte-identical.
        sender = Decimal("1234")
        baseline = move.move_to_all(sender, (L4_BATCH, SAVE_BATCH, WS_BATCH_NOS))
        variant = move.move_to_all(sender, (L4_BATCH, SAVE_BATCH, WS_ENV_LINES))
        assert baseline == (" 1234", 1234, 1234)
        assert variant == (" 1234", 1234, 234)
        assert variant[0] == baseline[0]
        assert variant[1] == baseline[1]
        assert variant[2] != baseline[2]

    def test_a_figurative_constant_reaches_every_receiver(self) -> None:
        # Verbatim, [general/gl072.cbl:L411]::
        #
        #  move  zero   to  tot-dr  tot-cr.
        #
        # Multiple receivers combined with a figurative sender. Both receivers are
        # `pic 9(8)v99` [general/gl072.cbl:L165-L166] - note they are UNSIGNED DISPLAY
        # rather than the packed shape the plan's prose suggests, which the descriptors
        # above carry verbatim from the declaration.
        assert move.move_to_all(move.ZERO, (TOT_DR, TOT_CR)) == (
            Decimal("0.00"),
            Decimal("0.00"),
        )
        # The scale comes from each receiver, so the zero is a two-place zero.
        cleared_dr, cleared_cr = move.move_to_all(move.ZERO, (TOT_DR, TOT_CR))
        assert cleared_dr.as_tuple().exponent == -2
        assert cleared_cr.as_tuple().exponent == -2
        # And the same statement shape against a SIGNED packed money field still yields
        # a
        # two-place zero, so the result does not depend on the storage class.
        assert move.move(move.ZERO, POST_AMOUNT) == Decimal("0.00")

    def test_a_single_receiver_list_still_returns_a_tuple(self) -> None:
        # `move zero to save-batch save-ledger.` [general/gl072.cbl:L281] and the
        # one-receiver form share the same entry point, so the shape of the result must
        # not depend on the count. An edge case worth pinning because a caller unpacks
        # positionally.
        assert move.move_to_all(Decimal("7"), (WS_BATCH_NOS,)) == (7,)
        assert move.move_to_all(Decimal("7"), ()) == ()


# ---------------------------------------------------------------------------
#  4.4  REFERENCE MODIFICATION - 1-BASED on BOTH sides, 83 live uses
# ---------------------------------------------------------------------------


class TestReferenceModificationIsOneBasedOnBothSides:
    """`item (offset:length)` counts from ONE, as a sender and as a receiver.

    Verbatim, [sales/sl060.cbl:L1071-L1072]::

        move     u-date (1:6) to post-date (1:6).
        move     u-date (9:2) to post-date (7:2).

    Two statements that between them build an eight-character date out of a
    ten-character one by dropping the century. `03  u-date          pic x(10).`
    [copybooks/wsmaps03.cob:L7] sends; `03  Post-Date       pic x(8).`
    [copybooks/wspost.cob:L18] receives, and it is A REAL COLUMN, so an off-by-one here
    is visible in a table dump.

    Frequency across the in-scope programs, 83 live uses in total: `(7:4)` x16,
    `(4:2)` x16, `(1:2)` x16, `(9:2)` x9, `(1:6)` x8, `(6:2)` x5, `(1:4)` x5,
    `(7:2)` x4, `(1:1)` x3, `(1:22)` x1.
    """

    def test_offset_one_is_the_first_character_not_the_second(self) -> None:
        # The explicit 1-based-not-0-based assertion. Under 0-based indexing `(1:2)`
        # would return "1/" - the SECOND and third characters - so this single line
        # distinguishes the two conventions.
        assert move.ref_mod(RUN_DATE_TEXT, 1, 2) == "21"
        assert move.ref_mod(RUN_DATE_TEXT, 1, 2) != "1/"
        # And there is no valid offset zero: see the Q-10 test below, which pins that
        # `ref_mod` refuses it rather than treating it as the first character.

    @pytest.mark.parametrize(
        ("offset", "length", "expected", "locator"),
        [
            # `move     to-day (7:4) to ws-Intl-Year.`   [general/gl070.cbl:L596]
            (7, 4, "2025", "general/gl070.cbl:L596"),
            # `move     to-day (4:2) to ws-Intl-Month.`  [general/gl070.cbl:L597]
            (4, 2, "09", "general/gl070.cbl:L597"),
            # `move     to-day (1:2) to ws-Intl-Days.`   [general/gl070.cbl:L598]
            (1, 2, "21", "general/gl070.cbl:L598"),
            # The two-digit year the posting date keeps. [sales/sl060.cbl:L1072]
            (9, 2, "25", "sales/sl060.cbl:L1072"),
            # Day, separator, month, separator - the first six characters.
            # [sales/sl060.cbl:L1071]
            (1, 6, "21/09/", "sales/sl060.cbl:L1071"),
        ],
    )
    def test_the_verified_one_based_reads(
        self, offset: int, length: int, expected: str, locator: str
    ) -> None:
        # `01  to-day              pic x(10).` [general/gl070.cbl:L243] and `u-date`
        # [copybooks/wsmaps03.cob:L7] are both ten characters in DD/MM/CCYY order, so
        # every range above is wholly inside its item.
        assert len(RUN_DATE_TEXT) == 10
        assert move.ref_mod(RUN_DATE_TEXT, offset, length) == expected, locator

    def test_the_two_statement_pair_builds_the_eight_character_posting_date(
        self,
    ) -> None:
        # [sales/sl060.cbl:L1071-L1072], applied in source order. The receiver starts at
        # its declared width of eight spaces, which is what every record layout
        # initialises it to, and each statement overwrites only its own range.
        post_date = " " * 8
        assert POST_DATE.character_length == 8

        # Statement one: `move u-date (1:6) to post-date (1:6).`
        post_date = move.ref_mod_into(
            post_date, 1, 6, move.ref_mod(RUN_DATE_TEXT, 1, 6)
        )
        # Positions 7 and 8 are untouched, so they are still spaces.
        assert post_date == "21/09/  "

        # Statement two: `move u-date (9:2) to post-date (7:2).` - note the ASYMMETRY,
        # source offset 9 into receiver offset 7. That is the century being dropped.
        post_date = move.ref_mod_into(
            post_date, 7, 2, move.ref_mod(RUN_DATE_TEXT, 9, 2)
        )
        assert post_date == "21/09/25"
        assert len(post_date) == 8

    def test_positions_outside_the_range_are_left_exactly_as_they_were(self) -> None:
        # A partial overwrite is a partial overwrite: `ref_mod_into` is not an
        # assignment to the whole item. If it cleared the rest, statement two of the
        # pair
        # above would wipe out the day and month statement one had just written.
        receiver = "ABCDEFGH"
        assert move.ref_mod_into(receiver, 7, 2, "25") == "ABCDEF25"
        assert move.ref_mod_into(receiver, 1, 2, "21") == "21CDEFGH"
        assert move.ref_mod_into(receiver, 4, 2, "09") == "ABC09FGH"

    def test_a_short_value_is_padded_inside_its_range_only(self) -> None:
        # The range is a receiving item in its own right, so it pads on the RIGHT within
        # its own span and does not spill into the neighbouring positions.
        assert move.ref_mod_into("ABCDEFGH", 3, 4, "XY") == "ABXY  GH"

    #  Q-10 IS MEASURED, AND THE MEASUREMENT CONFIRMS THE REFUSAL.
    #
    #  It was recorded as unreproducible on the reasoning that a computed out-of-range
    #  range "reads ADJACENT STORAGE, which a Python str does not have". A focused probe
    #  now shows that is exactly what happens. GnuCOBOL 3.2.0, `cobc -x -free`, default
    #  flags (so no `-fec=bound-ref-mod` runtime check), with a sentinel placed
    #  immediately after the item in the SAME group so the adjacency is known:
    #
    #  01 the-group.
    #  05 src-text  pic x(10) value "ABCDEFGHIJ".
    #  05 sentinel  pic x(10) value "##########".
    #
    #  src-text(8:5)  -> H I J # #     <- two bytes of the SENTINEL
    #  src-text(9:4)  -> I J # #       <- two bytes of the SENTINEL
    #  src-text(11:2) -> # #           <- entirely inside the SENTINEL
    #  src-text(0:3)  -> NUL A B       <- one byte BEFORE the item
    #
    #  So the value is whatever the program's storage layout happens to place next to the
    #  item - not a clamp, not spaces, and not an error. It is unreproducible in a Python
    #  `str` for the reason the refusal states, and it is unreproducible in any
    #  representation that does not model the whole record's neighbours. A LITERAL
    #  out-of-range range does not even compile ("error: length of ... out of bounds"),
    #  so the frozen programs cannot contain one.
    #
    #  `move.ref_mod` therefore continues to REFUSE, and these two tests assert the
    #  refusal - which is the reproduction - instead of asserting a value. Rule R-6 is
    #  satisfied by the measurement being on record; rule R-4 by nothing being invented.
    #
    #  ASSERTED AS A REFUSAL RATHER THAN MARKED XFAIL, and the difference matters. A
    #  strict xfail over `== "25"` could never do anything but fail: the outcome is
    #  settled, so the marker promised an alarm that could not ring while reporting a
    #  settled contract as a pending question. Asserting the refusal locks the contract
    #  instead - the day someone introduces clamping, these tests FAIL, which is the
    #  alarm the marker was reaching for.

    def test_a_range_past_the_end_reads_neighbours_and_is_refused_q10(self) -> None:
        """`(9:4)` on a ten-character item is refused, because its value is adjacency.

        The clamped reading would be "25" and the compiler does not clamp: it hands back
        the two characters that exist followed by two bytes of whatever sits next in
        storage. See the measurement above.
        """
        with pytest.raises(move.ReferenceModificationOutOfRange) as raised:
            move.ref_mod(RUN_DATE_TEXT, 9, 4)

        # The refusal names its question, so a traceback is self-explaining (rule R-5).
        assert "Q-10" in str(raised.value)
        # And it names what it refused, rather than reporting a generic range error.
        assert "(9:4)" in str(raised.value)
        # The clamped answer is nowhere in the message: nothing suggests a value.
        assert "25" not in str(raised.value).split("Q-10")[0]

        # NOT clamped, which is the specific alternative the measurement rules out.
        assert RUN_DATE_TEXT[8:] == "25"
        # And the in-range range at the same end IS available, so the refusal is about
        # the overrun and not about the position.
        assert move.ref_mod(RUN_DATE_TEXT, 9, 2) == "25"

    def test_offset_zero_reads_before_the_item_and_is_refused_q10(self) -> None:
        """Offset zero is refused: it names the byte BEFORE the item, not the first.

        Reference modification is 1-BASED, so zero is not a position in the item at all.
        The measurement above shows `src-text(0:3)` returning a NUL followed by the
        item's first two characters - the byte before the field, read as data. The naive
        reading - that zero means the first character, as a 0-based language would have
        it, giving "21" - has no compiled counterpart.
        """
        with pytest.raises(move.ReferenceModificationOutOfRange) as raised:
            move.ref_mod(RUN_DATE_TEXT, 0, 2)

        assert "Q-10" in str(raised.value)
        assert "(0:2)" in str(raised.value)

        # Offset ONE is the first character, which is what zero is not.
        assert move.ref_mod(RUN_DATE_TEXT, 1, 2) == "21"

    def test_an_out_of_range_range_names_the_question_it_ran_into(self) -> None:
        # Asserted unconditionally, because the FAMILY is contract even where the value
        # is not: the whole family shares one base so a program module can catch it in
        # one place, and each subclass names its own question in the traceback.
        assert issubclass(
            move.ReferenceModificationOutOfRange, move.MovementWithNoCompiledAnswer
        )
        assert issubclass(move.MovementWithNoCompiledAnswer, ValueError)



# ---------------------------------------------------------------------------
#  4.5  FIGURATIVE CONSTANTS - only ZERO and SPACE families occur
# ---------------------------------------------------------------------------


class TestFigurativeConstants:
    """A constant with no sending item, so the receiver alone decides the result.

    Only two families occur anywhere in the frozen sources, at 532 `zero`, 12 `zeros`,
    0 `zeroes`, 64 `space` and 138 `spaces` uses. The variant spellings are
    accepted even where they never occur, because refusing a spelling COBOL accepts
    would be a new
    validation (R-3).
    """

    def test_zero_fills_an_alphanumeric_receiver_with_the_character_zero(self) -> None:
        # Into `pic x(4)` [general/gl070.cbl:L182] the figurative constant becomes four
        # ZERO CHARACTERS, not a number: the receiver is a character item.
        assert move.move(move.ZERO, WS_YEAR) == "0000"
        assert isinstance(move.move(move.ZERO, WS_YEAR), str)

    def test_space_fills_an_alphanumeric_receiver_with_spaces(self) -> None:
        # `05  ws-year         pic x(4).` [general/gl070.cbl:L182].
        assert move.move(move.SPACE, WS_YEAR) == "    "
        # And at the full legend width of `03  Post-Legend     pic x(32).`
        # [copybooks/wspost.cob:L24], which is how a record is cleared before a write.
        assert move.move(move.SPACE, POST_LEGEND) == " " * 32

    def test_zero_into_a_numeric_receiver_takes_the_receivers_scale(self) -> None:
        # `move  zero   to  tot-dr  tot-cr.` [general/gl072.cbl:L411] and the same
        # constant into the signed money field [copybooks/wspost.cob:L23].
        assert move.move(move.ZERO, POST_AMOUNT) == Decimal("0.00")
        assert move.move(move.ZERO, TOT_DR) == Decimal("0.00")
        # A zero-scale receiver gets an int rather than a Decimal, by the one carrier
        # rule that governs every field.
        assert move.move(move.ZERO, WS_BATCH_NOS) == 0
        assert type(move.move(move.ZERO, WS_BATCH_NOS)) is int

    def test_the_variant_spellings_are_the_same_two_constants(self) -> None:
        # `move  zero   to  tot-dr  tot-cr.` [general/gl072.cbl:L411] writes the
        # singular;
        # other sites write the plural. `ZEROS` occurs 12 times and `ZEROES` zero times,
        # but all three spell one constant, and `SPACES` (138 uses) spells the same
        # constant as `SPACE` (64).
        assert move.ZEROS is move.ZERO
        assert move.ZEROES is move.ZERO
        assert move.SPACES is move.SPACE
        assert move.ZERO is not move.SPACE
        # The parser accepts the words as text too, which is how a record layout written
        # from a `VALUE ZEROS` clause resolves.
        assert move.Figurative("zeros") is move.ZERO
        assert move.Figurative("spaces") is move.SPACE

    def test_the_published_spelling_census_matches_the_frozen_sources(self) -> None:
        # Counted across the twelve in-scope programs, `general/gl071.cbl:L172` included
        # -
        # the file whose single `sort     sort-trans` statement is its whole body.
        # Machine-checked rather than asserted in a comment: exactly five spellings, and
        # `zeroes` is carried at zero occurrences precisely so that a reader can see it
        # was considered and found absent.
        spellings = {
            word: (member, count)
            for word, (member, count) in move.FIGURATIVE_SPELLINGS.items()
        }
        assert set(spellings) == {"zero", "zeros", "zeroes", "space", "spaces"}
        assert spellings["zero"] == (move.Figurative.ZERO, 532)
        assert spellings["zeros"] == (move.Figurative.ZERO, 12)
        assert spellings["zeroes"] == (move.Figurative.ZERO, 0)
        assert spellings["space"] == (move.Figurative.SPACE, 64)
        assert spellings["spaces"] == (move.Figurative.SPACE, 138)
        # And the fill characters are the two the constants name.
        assert move.FIGURATIVE_FILL_CHARACTER[move.Figurative.ZERO] == "0"
        assert move.FIGURATIVE_FILL_CHARACTER[move.Figurative.SPACE] == " "

    def test_forms_that_never_occur_are_not_implemented(self) -> None:
        # Counted over the same twelve programs that DO use the two families - for
        # instance [general/gl072.cbl:L411] and [general/gl072.cbl:L281] - so the census
        # is over a corpus that was demonstrably read rather than over an empty set.
        # The zero-occurrence census, asserted so the absence is deliberate and provable
        # rather than an oversight. Implementing any of these would be adding a facility
        # the migrated cycle has no use for, which section 0.2.2 puts out of scope.
        absent = dict(move.ZERO_OCCURRENCE_FORMS)
        for form in (
            'ALL "x" as a MOVE sending operand',
            "HIGH-VALUES",
            "JUSTIFIED",
            "LOW-VALUES",
            "MOVE CORRESPONDING",
            "ON OVERFLOW",
            "QUOTES",
            "UNSTRING",
        ):
            assert absent[form] == 0, form
        # No public name in `move` offers any of them.
        for banned in (
            "HIGH_VALUES",
            "LOW_VALUES",
            "QUOTES",
            "move_corresponding",
            "unstring",
        ):
            assert not hasattr(move, banned), banned

    def test_space_into_a_numeric_display_receiver_is_refused_q9(self) -> None:
        """Q-9 is SETTLED BY THE COMPILER: the statement cannot be compiled at all.

        MEASURED. GnuCOBOL 3.2.0 was given the statement directly:

            01 num-disp pic 9(5) value 12345.
            ...
            move spaces to num-disp.

        and refused it -

            error: MOVE of figurative constant SPACE to numeric item used
            cobc exit=1

        - with default flags AND with `-frelax-syntax-checks`, so there is no flag
        combination under which the ACAS build could produce such a program. The
        statement therefore cannot exist in the compiled system, and there is no
        runtime representation to reproduce: the compiler diagnostic IS the arbitration
        rule R-6 asks for. The naive reading - that the receiver ends up holding five
        spaces - has no compiled counterpart at all.

        `move.move` accordingly RAISES rather than inventing a representation, and this
        test asserts that refusal - which is the faithful reproduction of a statement
        that does not compile.

        ASSERTED AS A REFUSAL RATHER THAN MARKED XFAIL. The compiler's rejection is a
        SETTLED fact, not a pending oracle question, so a strict xfail over `== "     "`
        could only ever fail and its promised alarm could never ring. The refusal is the
        contract; asserting it means that inventing a representation later turns this
        test RED, which is what the marker was reaching for.
        """
        # `05  WS-Batch-Nos       pic 9(5).` [copybooks/wsbatch.cob:L19] is numeric
        # DISPLAY, which is exactly the shape anomaly A-13's class condition tests.
        with pytest.raises(move.FigurativeSpaceIntoNumeric) as raised:
            move.move(move.SPACE, WS_BATCH_NOS)

        # The refusal names the receiver and quotes the compiler, so the traceback
        # carries its own evidence (rule R-5).
        assert "WS-Batch-Nos" in str(raised.value)
        assert "GnuCOBOL 3.2" in str(raised.value)
        # It belongs to the family a program module can catch in one place.
        assert isinstance(raised.value, move.MovementWithNoCompiledAnswer)

        # ZERO into the same receiver is legal and IS reproduced, so the refusal above
        # is specific to SPACE and not a refusal of figurative constants in general.
        # The receiver's carrier is `int`, so the reproduced value is the integer 0 and
        # not a five-character string - which is the point: SPACE has no such value.
        assert move.move(move.ZERO, WS_BATCH_NOS) == 0

    def test_spaces_in_a_numeric_item_fail_the_class_test_without_raising(self) -> None:
        # THIS PART IS CONTRACT, NOT AMBIGUITY, so it is asserted unconditionally.
        # Whatever route puts spaces into a numeric DISPLAY item, the class condition
        # must report False and must not raise - that is what keeps anomaly A-13's skip
        # at [general/gl072.cbl:L291-L292] a skip rather than an abort.
        assert move.is_numeric_class(" " * 5, WS_BATCH_NOS) is False
        # The figurative constant itself answers the class question directly too: ZERO
        # is
        # numeric, SPACE is not.
        assert move.is_numeric_class(move.ZERO, WS_BATCH_NOS) is True
        assert move.is_numeric_class(move.SPACE, WS_BATCH_NOS) is False


# ---------------------------------------------------------------------------
#  4.6  ANOMALY A-13 - `is_numeric_class` NEVER RAISES
# ---------------------------------------------------------------------------


class TestNumericClassConditionNeverRaises:
    """ANOMALY A-13, REPRODUCED AND LOCKED - the two entirely silent skips.

    Verbatim from the frozen source, the two places `general/gl072.cbl` abandons a
    record with no message, no counter and no trace::

        general/gl072.cbl:L291-L292     if       post-batch  not numeric
                                        go to  loop.

        general/gl072.cbl:L306-L307     if       we-error  equal  999
                                        go to  loop.

    The first is a NUMERIC CLASS CONDITION, and everything in this class follows from
    it. If `is_numeric_class` raised on a non-numeric batch number the record would
    abort the run instead of being skipped, and the run would end where the compiled
    program quietly carries on. If it logged a warning the run would report something
    the compiled program does not report. Both are behaviour changes, and both are
    forbidden:
    "a defect reproduced is correct; a defect fixed is a failure" (R-4), and no new
    validation may be added (R-3). THE COBOL IS SILENT, SO THIS IS SILENT.

    `pytest.raises` appears NOWHERE in this class. That is deliberate: there is no
    exception in the specification, so there is none to assert.

    LOCATOR NOTE: the register in section 0.6.7 cites L289-L290 and L303-L304; those
    lines hold `go to end-run.` and `move post-batch to save-batch`. The locators above
    are the verbatim statements as read from the frozen file, and are the same ones
    `acas_posting/cobol/move.py` cites.
    """

    def test_the_three_readings_the_anomaly_turns_on(self) -> None:
        # A batch number of spaces - the untouched state of a numeric DISPLAY item that
        # was never populated - is NOT numeric, so gl072 skips the record.
        assert move.is_numeric_class("  ", WS_BATCH_NOS) is False
        # A properly zero-filled batch number IS numeric, so the record is posted.
        assert move.is_numeric_class("00012", WS_BATCH_NOS) is True
        # A batch number with a letter in it is NOT numeric - the corruption the skip
        # exists to survive.
        assert move.is_numeric_class("00A12", WS_BATCH_NOS) is False

    def test_an_exact_numeric_carrier_is_always_of_the_numeric_class(self) -> None:
        # A value that already arrived as a Decimal cannot be non-numeric: it is not a
        # byte image with a zone to inspect. `pic s9(8)v99` [copybooks/wspost.cob:L23].
        assert move.is_numeric_class(Decimal("12.34"), POST_AMOUNT) is True
        assert move.is_numeric_class(Decimal("-12.34"), POST_AMOUNT) is True
        assert move.is_numeric_class(Decimal("0"), POST_AMOUNT) is True
        assert move.is_numeric_class(0, WS_BATCH_NOS) is True

    @pytest.mark.parametrize(
        ("value", "why"),
        [
            ("", "an empty item"),
            (" ", "one space"),
            ("     ", "all spaces, the width of the field"),
            ("                    ", "more spaces than the field is wide"),
            ("00A12", "an embedded letter"),
            ("ABCDE", "nothing but letters"),
            ("+1234", "an embedded plus"),
            ("-1234", "an embedded minus"),
            ("12.34", "an embedded decimal point"),
            ("1,234", "an embedded comma"),
            (" 1234", "a leading space before the digits"),
            ("1234 ", "a trailing space after the digits"),
            ("12345678901234567890", "far more digits than the field declares"),
            ("0" * 40, "an absurdly long run of digits"),
            ("\x00\x00", "control characters"),
            ("１２３", "non-ASCII digits, which COBOL does not accept"),
            ("½", "a non-ASCII numeric character"),
            ("１", "a single non-ASCII digit"),
            ("00012", "the one well-formed reading, for contrast"),
        ],
    )
    def test_every_pathological_reading_returns_a_bool_and_none_raises(
        self, value: str, why: str
    ) -> None:
        # The A-13 guarantee itself. Whatever the item holds - and a COBOL numeric
        # DISPLAY item can hold literally any byte pattern, because nothing validates it
        # on the way in - the class condition answers with a plain boolean. No
        # exception,
        # no warning, no counter, no trace.
        #
        # Note `str.isdigit()` alone would accept the non-ASCII digits above, which
        # COBOL
        # does not; the audited predicate requires ASCII, so those read False.
        verdict = move.is_numeric_class(value, WS_BATCH_NOS)
        assert type(verdict) is bool, why
        assert verdict in (True, False), why

    @pytest.mark.parametrize(
        "receiver",
        [WS_BATCH_NOS, POST_AMOUNT, INPUT_GROSS, ENTERED, SAVE_BATCH, TOT_DR],
        ids=[
            "display",
            "signed-money",
            "packed-unsigned",
            "binary-long",
            "comp",
            "display-scaled",
        ],
    )
    def test_the_guarantee_holds_across_every_storage_class(
        self, receiver: cobol_field.FieldDescriptor
    ) -> None:
        # A-13's skip must be silent whatever the item's storage class, because the same
        # predicate serves the whole cycle. Six classes, one contract.
        for value in ("", "  ", "00A12", "00012", "-1", Decimal("1.00"), 1):
            assert type(move.is_numeric_class(value, receiver)) is bool

    def test_the_skip_is_reachable_from_a_move_of_spaces(self) -> None:
        # The end-to-end shape of the anomaly, without a database: clear a legend to
        # spaces, read those spaces as if they were a batch number, and observe the
        # class condition report False so that gl072's `go to loop` is taken. No part of
        # this path reports anything.
        cleared = move.move(move.SPACE, WS_YEAR)
        assert cleared == "    "
        assert move.is_numeric_class(cleared, WS_BATCH_NOS) is False



# ---------------------------------------------------------------------------
#  4.7  THE ONE PATH WHERE AN EDITED VALUE REACHES THE DATABASE
# ---------------------------------------------------------------------------


class TestEditedValueReachingARealColumn:
    """An edited picture normally feeds a print line. Exactly once, it feeds a column.

    A grep for edit characters - `z`, `cr`, `db`, `*`, `$`, `,` - inside `pic` clauses
    across ALL of `copybooks/*.cob` returns ZERO matches, so no record layout
    declares an edited field and no edited value can reach a table by the ordinary
    route. One path
    gets there anyway, and this class walks it end to end. Verbatim,
    [sales/sl060.cbl:L1085-L1094]::

        move     oi-invoice to m.
        move     zero to b.
        inspect  m tallying b for leading space.
        subtract b from 8 giving c.
        add      1 to b.

        string   m (b:c)     delimited by size
                 " : "       delimited by size
                 sales-name  delimited by size
                 into Post-Legend pointer  xx.

    `03  m               pic z(7)9.` [sales/sl060.cbl:L213] is the edited item;
    `03  Post-Legend     pic x(32).` [copybooks/wspost.cob:L24] is A REAL COLUMN. So the
    rendering of an edited picture is observable in a table dump, which is the only
    observable this migration has, and it therefore has to be exact.

    WHAT THE IDIOM IS DOING. `z(7)9` right-justifies the number in eight positions and
    blanks the leading zeros. The INSPECT counts how many of those positions came out
    blank; the arithmetic turns that count into a start offset and a length; and the
    reference-modified `m (b:c)` is therefore the number with its leading blanks
    removed. It is a hand-rolled left-trim, built out of an edited picture.

    NOTE ON `SUBTRACT ... GIVING`: `SUBTRACT a FROM b GIVING c` means **c = b - a**, so
    `subtract b from 8 giving c` at [sales/sl060.cbl:L1088] is `c = 8 - b` and NOT
    `b - 8`. The tests below compute it that way round explicitly.
    """

    def test_the_edited_picture_right_justifies_and_blanks_leading_zeros(self) -> None:
        # `pic z(7)9` [sales/sl060.cbl:L213] is eight positions: seven suppressible `Z`
        # and one always-printing `9`.
        assert move.move_to_edited(Decimal("12345"), M_EDITED) == "   12345"
        assert len(move.move_to_edited(Decimal("12345"), M_EDITED)) == 8
        assert move.move_to_edited(Decimal("7"), M_EDITED) == "       7"
        assert move.move_to_edited(Decimal("12345678"), M_EDITED) == "12345678"
        # Only `Z` and `9` are implemented, because only they occur on this path.
        assert move.EDIT_SYMBOLS_IMPLEMENTED == ("Z", "9")

    def test_inspect_tallying_leading_accumulates_into_the_tally(self) -> None:
        # `inspect  m tallying b for leading space.` [sales/sl060.cbl:L1087] ADDS to the
        # tally item rather than replacing it. That is exactly why the line before it,
        # `move     zero to b.` [sales/sl060.cbl:L1086], exists at all - and reproducing
        # the accumulation is what makes that reset meaningful instead of redundant.
        edited = move.move_to_edited(Decimal("12345"), M_EDITED)
        assert edited == "   12345"

        first = move.inspect_tallying_leading(edited, move.SPACE, 0)
        assert first == 3

        # Called again WITHOUT the reset, the count accumulates - 3 added to 3.
        second = move.inspect_tallying_leading(edited, move.SPACE, first)
        assert second == 6
        assert second == first + 3

        # And starting from a non-zero tally proves the same thing directly.
        assert move.inspect_tallying_leading(edited, move.SPACE, 10) == 13
        # A run is LEADING only: the spaces inside "12345 : name" do not count.
        assert move.inspect_tallying_leading("12345 : x", move.SPACE, 0) == 0

    def test_the_full_chain_from_edited_number_to_a_real_column(self) -> None:
        # [sales/sl060.cbl:L1085-L1094] executed in source order for invoice 12345.
        invoice_number = Decimal("12345")

        # `move     oi-invoice to m.`                        [sales/sl060.cbl:L1085]
        edited = move.move_to_edited(invoice_number, M_EDITED)
        assert edited == "   12345"

        # `move     zero to b.`                              [sales/sl060.cbl:L1086]
        tally = move.move(move.ZERO, B_TALLY)
        assert tally == 0

        # `inspect  m tallying b for leading space.`          [sales/sl060.cbl:L1087]
        tally = move.inspect_tallying_leading(edited, move.SPACE, tally)
        assert tally == 3

        # `subtract b from 8 giving c.`  =>  c = 8 - b        [sales/sl060.cbl:L1088]
        length = 8 - tally
        assert length == 5

        # `add      1 to b.`                                 [sales/sl060.cbl:L1089]
        tally = tally + 1
        assert tally == 4

        # `m (b:c)` is therefore the number with its blanks trimmed - and the offset is
        # 1-BASED, which is the only reason `add 1 to b` is there.
        trimmed = move.ref_mod(edited, tally, length)
        assert trimmed == "12345"

        # `string ... into Post-Legend pointer xx.` with `move 1 to xx.`
        # [sales/sl060.cbl:L1078] setting the pointer.  [sales/sl060.cbl:L1091-L1094]
        legend, pointer = move.string_into(
            " " * 32,
            (trimmed, " : ", "Dykegrove Limited"),
            pointer=1,
            delimited_by="size",
        )
        assert legend == "12345 : Dykegrove Limited       "
        assert len(legend) == 32
        # The pointer ends one past the last character written: 5 + 3 + 17 = 25, so 26.
        assert pointer == 26

        # And what lands in the column is what a table dump will show.
        assert move.move(legend, POST_LEGEND) == legend

    def test_the_chain_is_a_left_trim_for_every_invoice_width(self) -> None:
        # The idiom has to work at every width or the legend would be misaligned for
        # some
        # invoices. Walk the widths and confirm the trim is exact each time.
        for invoice, expected in (
            (Decimal("1"), "1"),
            (Decimal("42"), "42"),
            (Decimal("12345"), "12345"),
            (Decimal("1234567"), "1234567"),
            (Decimal("12345678"), "12345678"),
        ):
            edited = move.move_to_edited(invoice, M_EDITED)
            tally = move.inspect_tallying_leading(edited, move.SPACE, 0)
            length = 8 - tally
            assert move.ref_mod(edited, tally + 1, length) == expected

    def test_the_edited_rendering_of_zero_is_seven_blanks_then_a_zero(self) -> None:
        # ASSERTED UNCONDITIONALLY, and here is why rather than xfailed. The folder
        # requirement flags the exact `z(7)9` output for a ZERO value as "a genuine
        # database question", and it is genuine: this rendering reaches
        # `Post-Legend pic x(32)` [copybooks/wspost.cob:L24], a real column, so it is
        # observable in a dump. But it is not UNRESOLVED - the audited `move_to_edited`
        # path renders it deterministically as seven suppressed positions followed by
        # the
        # always-printing final `9`, which is what `z(7)9` means. Marking a produced
        # value
        # xfail(strict=True) would XPASS and turn the suite red, so the assertion IS the
        # lock: change the rendering and this test fails (R-4).
        assert move.move_to_edited(Decimal("0"), M_EDITED) == "       0"
        assert move.move_to_edited(Decimal("0"), M_EDITED) == " " * 7 + "0"
        # It is NOT eight blanks. `BLANK WHEN ZERO` would do that, and `m` does not
        # declare it - `03  m               pic z(7)9.` [sales/sl060.cbl:L213] carries
        # no
        # such clause, unlike `l6-balance` [general/gl072.cbl:L237] which does.
        assert move.move_to_edited(Decimal("0"), M_EDITED) != " " * 8
        # The figurative constant takes the same route as the value zero.
        assert move.move_to_edited(move.ZERO, M_EDITED) == "       0"

    def test_a_zero_invoice_number_still_yields_one_character_through_the_chain(
        self,
    ) -> None:
        # The consequence of the previous test for the column, which is what makes the
        # rendering matter: seven blanks means the trim keeps exactly one character.
        edited = move.move_to_edited(Decimal("0"), M_EDITED)
        tally = move.inspect_tallying_leading(edited, move.SPACE, 0)
        assert tally == 7
        length = 8 - tally
        assert length == 1
        assert move.ref_mod(edited, tally + 1, length) == "0"
        legend, _ = move.string_into(
            " " * 32, ("0", " : ", "Dykegrove Limited"), pointer=1, delimited_by="size"
        )
        assert legend == "0 : Dykegrove Limited           "

    def test_an_edited_picture_outside_z_then_9_is_measured_and_refused_q14(
        self,
    ) -> None:
        """Q-14 is MEASURED, and the rendering is DELIBERATELY not implemented.

        Two statements, and they must not be conflated.

        FIRST, THE MEASUREMENT. Q-14 was recorded as unobservable on the
        reasoning that the only observable this migration has is table state and every
        such picture receives into a print line. That is true of the SCENARIO tier but
        not of the compiler: a focused probe can render the picture and print the
        characters. GnuCOBOL 3.2.0, `cobc -x -free`, default flags, on the exact frozen
        declaration `03 l6-balance pic z(7)9.99cr blank when zero.`
        [general/gl072.cbl:L237]:

            function length(l6-balance) -> 13
             123.45 -> "     123.45  "   (two spaces where CR would go)
            -123.45 -> "     123.45CR"
               0.00 -> "             "   (thirteen spaces, BLANK WHEN ZERO)

        So the rendering is known, and it is exactly the string this test used to assert
        as the "naive reading" - the naive reading was right.

        SECOND, IT IS STILL NOT IMPLEMENTED, AND MUST NOT BE. `l6-balance` is a print
        line item and reaches no column of any in-scope table, and Agent Action Plan
        section 0.2.2 puts "report formatting beyond database effects" out of scope. So
        `move.move_to_edited` continues to REFUSE the shape, and this test asserts the
        refusal. The reason for the refusal has changed - from "nobody knows" to "we
        know, and it is out of scope" - and that distinction is what is recorded here.

        EITHER WAY THE STRICT XFAIL WAS THE WRONG INSTRUMENT. A marker promises an alarm
        when an oracle answers; while the question was thought unobservable no oracle
        ever could answer, so it was a permanent failure describing a settled decision.
        The REFUSAL is the decision, and asserting it means inventing a rendering later
        turns this test RED.

        A SEPARATE SHAPE IS REFUSED BY THE COMPILER ITSELF, which is worth recording
        beside this one: `pic z9z9`, a Z after a 9 before the decimal point, does not
        compile at all ("error: a Z or * which is before the decimal point cannot follow
        9"), so that particular malformation cannot exist in the frozen tree.
        """
        assert L6_BALANCE.is_edited is True

        with pytest.raises(move.UnobservableEditedPicture) as raised:
            move.move_to_edited(Decimal("123.45"), L6_BALANCE)

        # The refusal names the receiver, quotes the picture it will not render, and
        # names the shape it does implement - so the traceback says what to do next.
        assert "l6-balance" in str(raised.value)
        assert "z(7)9.99cr" in str(raised.value)
        assert isinstance(raised.value, move.MovementWithNoCompiledAnswer)

        # The Z-then-9 shape the layer DOES implement still renders, so the refusal is
        # specific to the shapes outside it rather than a blanket refusal of editing.
        assert move.move_to_edited(Decimal("42"), L4_BATCH) == "   42"
        # And the one edited picture that does reach a column still renders too.
        assert move.move_to_edited(Decimal("0"), M_EDITED) == "       0"

    def test_the_ordinary_dispatch_also_routes_an_edited_receiver(self) -> None:
        # Asserted unconditionally because the ROUTING is contract even where the
        # rendering is not: `move` recognises an edited receiver before it considers the
        # numeric or alphanumeric cases, so a program module never has to pick the entry
        # point by hand.
        assert move.move(Decimal("42"), L4_BATCH) == "   42"
        assert move.move(Decimal("42"), L4_BATCH) == move.move_to_edited(
            Decimal("42"), L4_BATCH
        )


# ---------------------------------------------------------------------------
#  4.8  STRING - two shapes, and they must NOT be unified
# ---------------------------------------------------------------------------


class TestStringShapesAreNotUnified:
    """Two ways of building the same 32-character legend, kept apart on purpose.

    DO NOT UNIFY THESE INTO ONE HELPER. The frozen sources build `Post-Legend` two
    different ways, and the maintainer knew: [sales/sl100.cbl:L618] carries his own
    comment, verbatim::

        *> THIS DOES NOT APPEAR THE SAME as SL060 and PL060/PL100

    That is a legacy divergence, so it is reproduced rather than normalised - "a defect
    reproduced is correct; a defect fixed is a failure" (R-4). Collapsing the two into a
    single helper would silently pick one shape's behaviour for both.

    * **Shape 1 - ONE statement, THREE sources.** [sales/sl060.cbl:L1091-L1094], with
      mirrors at [purchase/pl060.cbl:L954] and [purchase/pl100.cbl:L608].
    * **Shape 2 - FIVE separate statements sharing ONE pointer.**
      [sales/sl100.cbl:L622], [sales/sl100.cbl:L624], [sales/sl100.cbl:L626],
      [sales/sl100.cbl:L627] and [sales/sl100.cbl:L628], each `into post-legend pointer
      xx`, with `move 1 to xx.` at [sales/sl100.cbl:L620] starting it.
    """

    def test_shape_one_writes_three_sources_in_a_single_statement(self) -> None:
        # [sales/sl060.cbl:L1091-L1094]. One call, three operands, one pointer advance
        # covering all three.
        legend, pointer = move.string_into(
            " " * 32,
            ("12345", " : ", "Dykegrove Limited"),
            pointer=1,
            delimited_by="size",
        )
        assert legend == "12345 : Dykegrove Limited       "
        assert pointer == 26

    def test_shape_two_chains_one_pointer_across_five_statements(self) -> None:
        # [sales/sl100.cbl:L622-L628]. Five INDEPENDENT calls; each is handed the
        # pointer
        # the previous one returned, which is what `pointer xx` does in the COBOL. The
        # numeric operands are handed their descriptors so the byte image is what a
        # numeric DISPLAY item actually presents - `pic 9(5)` holding 42 is "00042", not
        # "42". `03  k               pic 9(5).` [sales/sl060.cbl:L212].
        legend, pointer = " " * 32, 1

        # `string   batch delimited by size into post-legend pointer xx.`     L622
        legend, pointer = move.string_into(
            legend, ((Decimal("42"), None, K_ITEM),), pointer=pointer
        )
        assert legend == "00042" + " " * 27
        assert pointer == 6

        # `string   "/" delimited by size into post-legend pointer xx.`       L624
        legend, pointer = move.string_into(legend, ("/",), pointer=pointer)
        assert legend == "00042/" + " " * 26
        assert pointer == 7

        # `string   k delimited by size into post-legend pointer xx.`         L626
        legend, pointer = move.string_into(
            legend, ((Decimal("7"), None, K_ITEM),), pointer=pointer
        )
        assert legend == "00042/00007" + " " * 21
        assert pointer == 12

        # `string   "  :  "   delimited  by size into post-legend pointer xx.` L627
        legend, pointer = move.string_into(legend, ("  :  ",), pointer=pointer)
        assert legend == "00042/00007  :  " + " " * 16
        assert pointer == 17

        # `string   sales-name delimited by size into post-legend pointer xx.` L628
        legend, pointer = move.string_into(legend, ("Dykegrove Ltd",), pointer=pointer)
        assert legend == "00042/00007  :  Dykegrove Ltd   "
        assert pointer == 30
        assert len(legend) == 32

    def test_the_two_shapes_reach_genuinely_different_results(self) -> None:
        # The concrete reason unification would be a defect rather than a tidy-up: given
        # comparable inputs the two shapes lay the legend out differently, because shape
        # two writes the zero-filled DISPLAY byte images and a five-character separator
        # while shape one writes a trimmed number and a three-character one.
        shape_one, _ = move.string_into(
            " " * 32,
            ("12345", " : ", "Dykegrove Ltd"),
            pointer=1,
            delimited_by="size",
        )
        shape_two, pointer = " " * 32, 1
        for source in (
            (Decimal("42"), None, K_ITEM),
            "/",
            (Decimal("7"), None, K_ITEM),
            "  :  ",
            "Dykegrove Ltd",
        ):
            shape_two, pointer = move.string_into(
                shape_two, (source,), pointer=pointer
            )
        assert shape_one != shape_two
        assert shape_one.startswith("12345 : ")
        assert shape_two.startswith("00042/00007")

    def test_string_overwrites_rather_than_clearing_the_receiver(self) -> None:
        # Shape two only works because each statement leaves the earlier statements'
        # work
        # alone. If `STRING` cleared the receiver first, statement L624 would erase what
        # L622 wrote and the legend would be "/" and nothing else.
        legend, pointer = move.string_into("X" * 32, ("AB",), pointer=1)
        assert legend == "AB" + "X" * 30
        assert pointer == 3
        legend, pointer = move.string_into(legend, ("CD",), pointer=pointer)
        assert legend == "ABCD" + "X" * 28

    def test_delimited_by_space_trims_at_the_first_space_and_by_size_does_not(
        self,
    ) -> None:
        # `DELIMITED BY SPACE` occurs at [general/gl080.cbl:L531] and
        # [irs/irs030.cbl:L1424]; every other in-scope operand is `DELIMITED BY SIZE`.
        # The difference is not cosmetic - it changes how many characters are written
        # and
        # therefore where the pointer lands for the next statement.
        by_size, size_pointer = move.string_into(
            " " * 20, ("AB CD",), pointer=1, delimited_by="size"
        )
        assert by_size == "AB CD" + " " * 15
        assert size_pointer == 6

        by_space, space_pointer = move.string_into(
            " " * 20, ("AB CD",), pointer=1, delimited_by="space"
        )
        assert by_space == "AB" + " " * 18
        assert space_pointer == 3

        # The two delimiters are the only ones the frozen sources use.
        assert move.DELIMITED_BY_SIZE is move.Delimiter.SIZE
        assert move.DELIMITED_BY_SPACE is move.Delimiter.SPACE

    def test_a_per_operand_delimiter_overrides_the_statement_default(self) -> None:
        # A `STRING` carries a delimiter per operand rather than one for the statement,
        # and [general/gl080.cbl:L530-L536] mixes them in a single statement. The tuple
        # form is how one operand names its own.
        mixed, pointer = move.string_into(
            " " * 20,
            (("AB CD", move.Delimiter.SPACE, None), "-", "EF GH"),
            pointer=1,
            delimited_by="size",
        )
        assert mixed == "AB-EF GH" + " " * 12
        assert pointer == 9

    def test_a_source_longer_than_the_receiver_is_truncated_silently(self) -> None:
        # `ON OVERFLOW` occurs ZERO times in the in-scope set, so a source that runs off
        # the end is simply cut and nothing is reported (R-3).
        legend, pointer = move.string_into(" " * 8, ("ABCDEFGHIJKL",), pointer=1)
        assert legend == "ABCDEFGH"
        assert pointer == 9

    def test_the_pointer_beyond_the_receiver_is_a_silent_no_op(self) -> None:
        # Q-11 as MEASURED, asserted unconditionally so the measurement is locked:
        # nothing is written AND the pointer does not advance. Both halves matter,
        # because shape two hands the pointer straight to the next statement.
        legend, pointer = move.string_into(" " * 32, ("XY",), pointer=33)
        assert legend == " " * 32
        assert pointer == 33
        # The same at the other end of the range.
        legend, pointer = move.string_into(" " * 32, ("XY",), pointer=0)
        assert legend == " " * 32
        assert pointer == 0

    def test_a_pointer_beyond_the_receiver_leaves_it_unchanged_q11(self) -> None:
        """Q-11 is MEASURED: a STRING past the receiver is a complete no-op.

        The question was whether the pointer still ADVANCES by the source length when
        nothing could be written - which is what an implementation that advanced before
        range-checking would do - or whether the whole statement is inert. It matters
        because the pointer feeds the next STRING statement, so an advancing pointer
        would shift everything after it.

        THE MEASUREMENT. GnuCOBOL 3.2.0, `cobc -x -free`, default flags,
        `01 recv pic x(5)` pre-filled with `-----`:

            move 9 to ptr;  string "XY" ... into recv with pointer ptr
                -> overflow RAISED, recv = "-----" (untouched), ptr = 9 (UNCHANGED)

            move 1 to ptr;  string "AB" ... into recv with pointer ptr
                -> no overflow, recv = "AB---", ptr = 3

            move 5 to ptr;  string "PQ" ... into recv with pointer ptr
                -> overflow RAISED, recv = "AB--P" (ONE character written), ptr = 6

        So a pointer entirely beyond the receiver writes NOTHING and leaves the pointer
        exactly where it was; a partial fit writes what fits and advances by that much.
        Both are what `move.string_into` implements, so the measurement confirms it.

        This test used to assert the REJECTED reading - the pointer advancing to 35 -
        under `xfail(strict=True)`. Since Q-11 is measured the outcome is settled, so
        that marker could only ever fail, and the alarm it promised - "if the pointer
        ever starts advancing, this XPASSes" - is delivered better by a plain assertion,
        which goes RED on exactly the same change and says what is wrong. So the
        measured behaviour is asserted, and the rejected value is asserted NOT to hold
        so a regression in that direction still fails here by name.
        """
        receiver, pointer = move.string_into(" " * 32, ("XY",), pointer=33)

        # Entirely beyond the receiver: nothing written, pointer UNCHANGED.
        assert receiver == " " * 32
        assert pointer == 33, (
            f"a STRING whose pointer is beyond the receiver left the pointer at "
            f"{pointer}. GnuCOBOL 3.2.0 leaves it exactly where it was - the whole "
            f"statement is inert - because it range-checks before it advances."
        )
        # NOT the advance-before-checking reading, which would give 33 + 2. Derived from
        # the source's own length rather than written as a literal.
        assert pointer != 33 + len("XY")
        assert pointer != 35

        # A PARTIAL fit writes what fits and advances by that much, which is what makes
        # the no-op above a distinct behaviour rather than a special case of clamping.
        partial, partial_pointer = move.string_into(" " * 5, ("PQ",), pointer=5)
        assert partial == "    P"
        assert partial_pointer == 6


# ---------------------------------------------------------------------------
#  THE FOUR CATEGORY PRIMITIVES BEHIND THE SINGLE DISPATCH
# ---------------------------------------------------------------------------


class TestTheCategoryPrimitivesBehindTheDispatch:
    """`move` picks a primitive by receiver category; each primitive is testable alone.

    A program module calls `move` and never picks the primitive itself, which is what
    makes the dispatch auditable in one place. But the four primitives are published
    separately and each owns one category's rule, so each is pinned here directly and
    then shown to agree with what `move` routes to. If the dispatch order ever changed,
    these agreements would break rather than the behaviour silently shifting.

    The order `move` tries is: group, then EDITED, then numeric, then alphanumeric.
    Edited comes before numeric deliberately - an edited receiver is numeric-edited, so
    testing `is_numeric` first would send it down the wrong path and store a number
    where the picture wants characters.
    """

    def test_move_alphanumeric_owns_the_character_categories(self) -> None:
        # `pic x(4)` [general/gl070.cbl:L182]: truncate right, pad right.
        assert move.move_alphanumeric("ABCDEFGHIJ", WS_YEAR) == "ABCD"
        assert move.move_alphanumeric("AB", WS_YEAR) == "AB  "
        # And `move` routes an alphanumeric receiver here.
        assert move.move("ABCDEFGHIJ", WS_YEAR) == move.move_alphanumeric(
            "ABCDEFGHIJ", WS_YEAR
        )

    def test_a_numeric_display_sender_is_a_character_item(self) -> None:
        # The rule that makes `sending_field` matter, and it is easy to get wrong. In
        # COBOL a numeric DISPLAY item IS a character item: `03  k               pic
        # 9(5).`
        # [sales/sl060.cbl:L212] holding 42 occupies the five bytes "00042", and THAT is
        # what moves into a character receiver. So `pic 9(5)` into `pic x(4)` yields
        # "0004" - the first four bytes of the image, zeros included - and NOT "42" or
        # "  42".
        assert (
            move.move_alphanumeric(Decimal("42"), WS_YEAR, sending_field=K_ITEM)
            == "0004"
        )
        # Without the sending descriptor there is no byte image to take, so the digits
        # move as digits. The two answers differ, which is exactly why the parameter is
        # not optional in spirit even though it is in signature.
        assert move.move_alphanumeric(Decimal("42"), WS_YEAR) != "0004"

    def test_move_numeric_owns_the_numeric_categories(self) -> None:
        # `05  WS-Batch-Nos       pic 9(5).` [copybooks/wsbatch.cob:L19] and
        # `03  Post-Amount     pic s9(8)v99.` [copybooks/wspost.cob:L23].
        # A byte image arriving as text is read as the value it represents - the other
        # direction of the same rule, and how a DISPLAY column read back becomes a
        # number.
        assert move.move_numeric("00042", WS_BATCH_NOS) == 42
        assert type(move.move_numeric("00042", WS_BATCH_NOS)) is int
        # And an exact carrier is stored under the receiver's picture.
        assert move.move_numeric(Decimal("123.456"), POST_AMOUNT) == Decimal("123.45")
        assert move.move(Decimal("123.456"), POST_AMOUNT) == move.move_numeric(
            Decimal("123.456"), POST_AMOUNT
        )

    def test_move_figurative_owns_the_constant_category(self) -> None:
        # `move  zero   to  tot-dr  tot-cr.` [general/gl072.cbl:L411] is the shape, and
        # `05  ws-year         pic x(4).` [general/gl070.cbl:L182] the character
        # receiver.
        # A constant has no sending item, so only the receiver speaks.
        assert move.move_figurative(move.ZERO, WS_YEAR) == "0000"
        assert move.move_figurative(move.SPACE, WS_YEAR) == "    "
        assert move.move_figurative(move.ZERO, POST_AMOUNT) == Decimal("0.00")
        # Any accepted spelling resolves to the same constant, including as plain text.
        assert move.move_figurative("zeros", POST_AMOUNT) == Decimal("0.00")
        assert move.move_figurative("zeroes", POST_AMOUNT) == Decimal("0.00")
        assert move.move_figurative("spaces", WS_YEAR) == "    "
        # `move` routes a figurative sender to the same place.
        assert move.move(move.ZERO, WS_YEAR) == move.move_figurative(
            move.ZERO, WS_YEAR
        )

    def test_move_group_moves_the_whole_byte_image_unconverted(self) -> None:
        # `03  WS-Batch-Key.` [copybooks/wsbatch.cob:L14] is a GROUP over
        # `05  WS-Ledger          pic 9.` [copybooks/wsbatch.cob:L15] and
        # `05  WS-Batch-Nos       pic 9(5).` [copybooks/wsbatch.cob:L19]. A group move
        # is
        # a byte copy: no field is interpreted, no digit is aligned, no sign is applied.
        # That is why a group receiver is tried FIRST - interpreting it would corrupt
        # it.
        batch_key = picture.descriptor_for(
            "",
            name="WS-Batch-Key",
            source_locator="copybooks/wsbatch.cob:L14",
            is_group=True,
        )
        assert batch_key.is_group is True
        assert batch_key.usage is model.Usage.GROUP
        assert move.move_group("001234", batch_key) == "001234"
        assert move.move("001234", batch_key) == "001234"
        # A figurative constant into a group fills it, which is how a record is cleared.
        assert move.move_group(move.SPACE, batch_key, length=6) == "      "

    def test_an_explicit_length_overrides_the_declared_width(self) -> None:
        # The `length` parameter exists for a reference-modified receiver, where the
        # range
        # rather than the item decides the width. `pic x(4)` [general/gl070.cbl:L182]
        # restricted to two positions truncates at two.
        assert move.move_alphanumeric("ABCD", WS_YEAR, length=2) == "AB"
        assert move.move("ABCD", WS_YEAR, length=2) == "AB"
        # Consistent with `ref_mod_into`, which is the other way of saying the same
        # thing.
        assert move.ref_mod_into("ABCD", 1, 2, "XY") == "XYCD"



# ---------------------------------------------------------------------------
#  4.9  THE CENSUSES - so the docstring's claims are machine-checked
# ---------------------------------------------------------------------------


class TestCensusesMatchTheFrozenSources:
    """The module docstring quotes numbers; these tests stop them going stale."""

    def test_move_census_is_internally_consistent(self) -> None:
        # Twelve in-scope programs, and `general/gl071.cbl` contributes ZERO because it
        # is a pure sort: its single statement of substance is `sort     sort-trans` at
        # [general/gl071.cbl:L172]. A fact worth pinning, since a sort program with MOVE
        # statements in it would mean the sort had acquired logic - and gl072 finds the
        # right nominal account only because gl071's ordering is untouched.
        census = dict(move.MOVE_CENSUS)
        assert len(census) == 12
        assert census["general/gl071.cbl"] == 0
        assert dict(move.MOVE_STATEMENT_CENSUS)["general/gl071.cbl"] == 0
        # Line counts total 1291; live statement counts total 1250. Section 0.4.1 quotes
        # 1290 with sl055 at 91, and a line count of that file returns 92 - the figure
        # the audited module carries.
        assert sum(census.values()) == 1291
        assert sum(count for _, count in move.MOVE_STATEMENT_CENSUS) == 1250
        assert census["sales/sl055.cbl"] == 92
        # Live statements can never exceed lines mentioning the verb.
        statements = dict(move.MOVE_STATEMENT_CENSUS)
        assert set(statements) == set(census)
        for program, lines in census.items():
            assert statements[program] <= lines, program

    def test_the_reference_modification_census_totals_eighty_three(self) -> None:
        # 83 live uses, the most frequent being `to-day (7:4)` at
        # [general/gl070.cbl:L596]
        # with 16 occurrences. Every pair this file exercises appears in the census,
        # which
        # is how the tests are shown to cover the real shapes rather than invented ones.
        census = {
            (offset, length): count
            for offset, length, count in move.REFERENCE_MODIFICATION_CENSUS
        }
        assert sum(census.values()) == 83
        assert census[(7, 4)] == 16
        assert census[(4, 2)] == 16
        assert census[(1, 2)] == 16
        assert census[(9, 2)] == 9
        assert census[(1, 6)] == 8
        assert census[(6, 2)] == 5
        assert census[(1, 4)] == 5
        assert census[(7, 2)] == 4
        assert census[(1, 1)] == 3
        assert census[(1, 22)] == 1
        # Every pair the two-statement pair uses is a real, counted shape.
        for pair in ((1, 6), (9, 2), (7, 2)):
            assert census[pair] >= 1
        # And the census is ordered most frequent first, so a reader can trust the
        # order.
        counts = [count for _, _, count in move.REFERENCE_MODIFICATION_CENSUS]
        assert counts == sorted(counts, reverse=True)

    def test_the_published_tables_cannot_be_mutated_by_a_caller(self) -> None:
        # NO COBOL LOCATOR, deliberately, and said out loud so the absence is not
        # mistaken
        # for an oversight: this asserts a property of the PUBLISHED TABLES themselves -
        # the determinism guarantee R-6 requires of them - and not the behaviour of any
        # statement in the frozen source. A test that reordered or edited a published
        # table would change what a later test observes, and the whole point of the
        # arithmetic tier is that two runs agree. Every table is a tuple or a read-only
        # mapping, so no caller can.
        assert isinstance(move.MOVE_CENSUS, tuple)
        assert isinstance(move.REFERENCE_MODIFICATION_CENSUS, tuple)
        assert isinstance(move.EDIT_SYMBOLS_IMPLEMENTED, tuple)
        with pytest.raises(TypeError):
            move.FIGURATIVE_FILL_CHARACTER[  # type: ignore[index]
                move.Figurative.ZERO
            ] = "9"
