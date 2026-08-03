"""`DISPLAY` with `SIGN LEADING` - the sixth COBOL numeric storage class.

File 4 of 14 in the arithmetic parity tier. Four things are established here, and
they are the four things a migration of this cycle can silently get wrong:

  1. BOTH SPELLINGS SURVIVE VERBATIM. The frozen copybooks write the same clause two
     ways - `sign leading` at [copybooks/wspost-irs.cob:L21] and [:L25], and
     `sign is leading` at [copybooks/irswspost.cob:L14] and [:L18].
     The declared text is preserved exactly as written while the SEMANTICS are unified
     onto one `SignPosition` member. Normalising one spelling into the other would
     erase evidence about the frozen source; unifying the semantics is what lets one
     encoder serve both.
  2. THE TWO NEAR-IDENTICALLY-NAMED POSTING RECORDS ARE TWO DISTINCT ENTRIES.
     [copybooks/wspost-irs.cob:L6-L7] says so in the source itself: "This is NOT the
     same as the internal IRS posting file". `PSIRSPOST-REC` is the transfer file the
     Sales and Purchase programs write - ten columns, handler `acas008`, bridge
     `slpostingMT`. `IRSPOSTING-REC` is the internal IRS posting file - thirteen
     columns, handler `acasirsub4`, bridge `irspostingMT`. Their field names are
     near-identical, so a dictionary keyed by field name alone would merge them; this
     module proves the dictionary refuses an unqualified key outright.
  3. THE LEADING-SIGN BYTE LENGTH IS NOT SETTLED. See Q-5.2 below. The width test is
     `xfail(strict=True)` against that id and asserts no width as fact.
  4. THE TRAILING-SIGN BYTE LENGTH *IS* SETTLED, from the maintainer's own running
     byte offsets, and is asserted as a plain fact.

THERE IS NO USER RULES DOCUMENT FOR THIS PROJECT. `review_rules` reports that none was
provided, so there is no on-disk rules file and no reader should look for one. The six
binding rules R-1 to R-6 live in the Agent Action Plan section 0.7.2 and their exact
wording is retrievable from the requirements via `review_prompt`. Summarised in this
module's own words, each named at the site that honours it:

    R-1  No COBOL at runtime. This module runs on a bare host: no Docker, no MariaDB,
         no GnuCOBOL, no `cobc`, no `cobcrun`, no subprocess and no FFI. Its only
         file-system prerequisite is data_dictionary/acas_posting_dictionary.json,
         which `FieldDescriptor.from_dictionary_key` reads. Nothing under harness/ is
         imported or referenced.
    R-2  Zero binary floating point. Every value here is a `decimal.Decimal`, an `int`,
         a `str` or `bytes`. There is no float literal, no binary-float constructor, no
         tolerance, no epsilon and no approximate comparison, and the ambient `decimal`
         context is neither read nor mutated - the descriptor carries its own scale, and
         `encode` takes its rounding direction as an explicit argument at the call site.
         Comparison is always exact equality.
    R-3  No new validations, fields or schema changes; no concurrency. This module
         asserts, it does not repair: where a field's storage class differs between the
         copybook, the bridge host variable and the column, that difference is reported
         as it stands rather than reconciled into one answer. Nothing here emits DDL or
         adds a check the COBOL lacks. Execution is strictly sequential and no parallel
         runner is used.
    R-4  Legacy anomalies are reproduced, never fixed. Every expected value below is
         accompanied by the COBOL locator it came from. A test that asserted tidy
         accounting instead of the declared behaviour would itself be the defect.
    R-5  Full traceability. Every descriptor is obtained from a dictionary key or from
         `picture.parse_entry` with an explicit `source_locator`; not one field's
         metadata is hand-written. Coverage is evidence, never a gate.
    R-6  Compiled behaviour is the tie-breaker, AND THIS IS THE PRIMARY R-6 SITE IN
         THE FOLDER. Where the frozen sources support two readings and no oracle
         measurement is on record, the test is written and marked
         `xfail(strict=True)` against a named `Q-` id rather than guessed at or
         skipped.

THE TWO `Q-` IDS THIS MODULE TOUCHES, both named by acas_posting/cobol/usage.py:

    Q-5.2  THE WIDTH OF A LEADING-SIGN DISPLAY ITEM, named at
           acas_posting/cobol/usage.py:L415. The frozen sources support two readings
           and they disagree by exactly one byte:

             Reading A - the maintainer's own byte accounting, verbatim from
             [copybooks/wspost.cob:L6-L7]:
                 *> 98 bytes 26/03/09
                 *> 96 bytes 20/12/11 (leading sign removed)
             Dropping the clause from TWO fields saved TWO bytes, i.e. one byte per
             field, i.e. the leading sign occupied a byte of its own. Width = digits+1,
             so 10 bytes for `pic s9(7)v99 sign leading`.

             Reading B - the ISO overpunch reading. `SIGN LEADING` written WITHOUT
             `SEPARATE` is overpunched into the leading digit and costs no byte.
             Width = digits, so 9 bytes. This is what usage.byte_length implements.

             Reading C, which is why A is genuinely puzzling rather than obviously
             right: in the SAME copybook the TRAILING sign is provably overpunched.
             [copybooks/wspost.cob:L22-L23] runs 36 -> 46 and
             [copybooks/wspost.cob:L27-L28] runs 86 -> 96, both ten bytes for a ten
             digit `pic s9(8)v99`. So an included sign costs nothing there.

           Nothing in the tree records an oracle measurement for the leading case:
           `FieldDescriptor.ambiguity_refs()` is empty for all four leading-sign
           fields. The width is therefore left open here, exposed and unarbitrated.

    Q-5.3  THE ZONED OVERPUNCH BYTE VALUES - `usage.ZONED_POSITIVE_BASE` and
           `usage.ZONED_NEGATIVE_BASE`, named at acas_posting/cobol/usage.py:L94. This
           module deliberately asserts NO specific overpunch byte and no literal byte
           string. The sign is observed instead through WHICH BYTE POSITION CHANGES
           between a value and its negation, which distinguishes a leading sign from a
           trailing one without depending on the byte's value at all.

THE SIGN-CLAUSE CENSUS, measured over the frozen tree and over the generated
dictionary, and recorded here so a reader knows why two `SignPosition` members are
modelled but never exercised:

    copybooks/ tree
        `sign leading`     4 - [copybooks/wspost-irs.cob:L21] and [:L25], plus
                               [copybooks/fdpost-irs.cob:L20] and [:L24], the
                               file-description twin of the transfer record, which
                               sits outside the in-scope copybook closure
        `sign is leading`  2 - [copybooks/irswspost.cob:L14] and [:L18]
        `sign trailing`    0
        `separate`         0
        `justified`        0
        `blank when zero`  0
        `binary-double` and `comp-5` never appear as an in-scope RECORD-LAYOUT
        field; their only occurrences are in copybooks/mysql-variables.cpy, the
        bridge row-count scaffolding, which declares no record at all.

    data_dictionary/acas_posting_dictionary.json - 1061 entries, 22 tables
        LEADING_INCLUDED   4 - the two amount fields of each of the two IRS
                               posting records
        TRAILING_INCLUDED  2 - GLPOSTING-REC.POST-AMOUNT and GLPOSTING-REC.VAT-AMOUNT
        LEADING_SEPARATE   0
        TRAILING_SEPARATE  0

    So `LEADING_SEPARATE` and `TRAILING_SEPARATE` exist in the model - they are part of
    the COBOL vocabulary and `usage.byte_length` prices them - and no in-scope field
    uses either. Both halves of that statement are asserted below.

TWO LOCATOR DISCREPANCIES, noted so a reader is not misled by the plan text. The Agent
Action Plan body cites [copybooks/irswspost.cob:L19] for the second `sign is leading`
field; L19 is a `*>` comment line and the declaration is on L14's sibling L18, which is
also the locator the generated dictionary records for `IRSPOSTING-REC.VAT-AMOUNT4`. The
plan likewise cites mysql/ACASDB.sql:L282 for `POST4-AMOUNT`; L282 is `POST4-CR` and the
`POST4-AMOUNT decimal(9,2)` column is on L283. Both frozen files are read here as
specification and neither is modified.
"""

from __future__ import annotations

from decimal import ROUND_DOWN, Decimal

import pytest

from acas_posting.cobol import field as cobol_field
from acas_posting.cobol import picture as cobol_picture
from acas_posting.cobol import usage as cobol_usage
from acas_posting.dictionary import loader, model

pytestmark = pytest.mark.arithmetic


# ---------------------------------------------------------------------------
#  SECTION 1  -  THE TWO RECORDS, AND THE KEYS THAT REACH THEM
#
#  Named once, with their provenance, so that no test hand-writes a key and every
#  assertion below can be traced back to a frozen line (R-5).
# ---------------------------------------------------------------------------

# The SPL/IRS TRANSFER file. Written by the Sales and Purchase posting programs on the
# IRS fan-out, read by irs030. Ten columns [mysql/ACASDB.sql:L366-L377], handler
# acas008, bridge slpostingMT, record layout [copybooks/wspost-irs.cob].
SPL_TRANSFER_TABLE: str = "PSIRSPOST-REC"
SPL_TRANSFER_COLUMN_COUNT: int = 10
SPL_TRANSFER_BRIDGE: str = "slpostingMT"
SPL_TRANSFER_HANDLER: str = "acas008"

# The INTERNAL IRS posting file. Thirteen columns [mysql/ACASDB.sql:L274-L288] - three
# of them, POST4-DAY / POST4-MONTH / POST4-YEAR, exist only because the bridge derives
# them - handler acasirsub4, bridge irspostingMT, record layout
# [copybooks/irswspost.cob].
IRS_INTERNAL_TABLE: str = "IRSPOSTING-REC"
IRS_INTERNAL_COLUMN_COUNT: int = 13
IRS_INTERNAL_BRIDGE: str = "irspostingMT"
IRS_INTERNAL_HANDLER: str = "acasirsub4"

# The General Ledger posting file, whose sign is TRAILING and whose width is proven.
GL_POSTING_TABLE: str = "GLPOSTING-REC"

# `sign leading` fields - [copybooks/wspost-irs.cob:L21] and [:L25].
SPL_POST_AMOUNT_KEY: str = "PSIRSPOST-REC.IRS-POST-AMOUNT"
SPL_VAT_AMOUNT_KEY: str = "PSIRSPOST-REC.IRS-VAT-AMOUNT"

# `sign is leading` fields - [copybooks/irswspost.cob:L14] and [:L18].
IRS_POST_AMOUNT_KEY: str = "IRSPOSTING-REC.POST4-AMOUNT"
IRS_VAT_AMOUNT_KEY: str = "IRSPOSTING-REC.VAT-AMOUNT4"

# The two fields that declare NO sign clause at all, so they take COBOL's default
# trailing included sign - [copybooks/wspost.cob:L23] and [copybooks/wspost.cob:L28].
GL_POST_AMOUNT_KEY: str = "GLPOSTING-REC.POST-AMOUNT"
GL_VAT_AMOUNT_KEY: str = "GLPOSTING-REC.VAT-AMOUNT"

# All four leading-sign fields in the whole in-scope dictionary, paired with the exact
# clause text their copybook writes and the locator it writes it on.
LEADING_SIGN_FIELDS: tuple[tuple[str, str, str], ...] = (
    (SPL_POST_AMOUNT_KEY, "sign leading", "copybooks/wspost-irs.cob:L21"),
    (SPL_VAT_AMOUNT_KEY, "sign leading", "copybooks/wspost-irs.cob:L25"),
    (IRS_POST_AMOUNT_KEY, "sign is leading", "copybooks/irswspost.cob:L14"),
    (IRS_VAT_AMOUNT_KEY, "sign is leading", "copybooks/irswspost.cob:L18"),
)

# Both leading-sign records declare their money as `pic s9(7)v99`: nine digits, seven
# of them integral, scale two. [copybooks/wspost-irs.cob:L21],
# [copybooks/irswspost.cob:L14].
LEADING_SIGN_PICTURE: str = "s9(7)v99"
LEADING_SIGN_DIGITS: int = 9
LEADING_SIGN_INTEGER_DIGITS: int = 7
LEADING_SIGN_SCALE: int = 2

# The General Ledger posting record declares `pic s9(8)v99` [copybooks/wspost.cob:L23].
TRAILING_SIGN_PICTURE: str = "s9(8)v99"
TRAILING_SIGN_DIGITS: int = 10
TRAILING_SIGN_INTEGER_DIGITS: int = 8
TRAILING_SIGN_SCALE: int = 2

# Evidence C, and the ONE byte width in this module that is a fact rather than a
# reading. [copybooks/wspost.cob:L22-L23] runs the record offset 36 -> 46 across
# `Post-Amount pic s9(8)v99`, and [copybooks/wspost.cob:L27-L28] runs it 86 -> 96
# across `Vat-Amount pic s9(8)v99`: 46 - 36 == 10 and 96 - 86 == 10, ten bytes for ten
# declared digits, so the included TRAILING sign is overpunched and costs nothing.
TRAILING_SIGN_PROVEN_BYTES: int = 10
TRAILING_OFFSET_BEFORE_POST_AMOUNT: int = 36
TRAILING_OFFSET_AFTER_POST_AMOUNT: int = 46
TRAILING_OFFSET_BEFORE_VAT_AMOUNT: int = 86
TRAILING_OFFSET_AFTER_VAT_AMOUNT: int = 96

# The scale both records declare, expressed as the quantum a store must land on.
MONEY_QUANTUM: Decimal = Decimal("0.01")

# The value set the zoned round-trip is exercised over. Every entry is a Decimal string
# and there is not a float in sight (R-2). Zero is included because it is the value at
# which a leading overpunch is least visible; the two full-width entries are included
# because they occupy every one of the nine declared digits, which is where a
# mis-modelled width shows up first. 9999999.99 is the true maximum of `s9(7)v99`;
# 1234567.89 is a full-width value with a distinct digit in every position, which makes
# a transposed digit visible in the encoding.
ZONED_ROUND_TRIP_MAGNITUDES: tuple[str, ...] = (
    "0.00",
    "0.01",
    "1.23",
    "1234567.89",
    "9999999.99",
)

# The subset with a non-zero magnitude. Only these can show a sign at all: COBOL has no
# negative zero and Python's `decimal` agrees, so a negated `Decimal("0.00")` is zero
# and its encoding is byte-identical to the positive one.
SIGNED_MAGNITUDES: tuple[str, ...] = tuple(
    text for text in ZONED_ROUND_TRIP_MAGNITUDES if Decimal(text) != 0
)


# ---------------------------------------------------------------------------
#  SECTION 2  -  A DEFENSIVE, FILE-LOCAL KEY RESOLVER
#
#  Every descriptor in this module comes from the generated dictionary, never from a
#  hand-written picture clause (R-5). Resolution is defensive for one concrete reason:
#  the two posting records carry near-identical field names, so a key that is right for
#  one is a plausible near miss for the other - `PSIRSPOST-REC.POST-AMOUNT` looks
#  correct and does not exist, because that table's column is `IRS-POST-AMOUNT`. The
#  loader raises `DictionaryKeyError`, a `KeyError` subclass, with the nearest keys
#  listed; this resolver turns that into a test failure that names the table's real
#  keys, so a wrong key can never be mistaken for a missing field.
#
#  No helper module is created for this: the resolver is local to this file, as the
#  tier contract requires.
# ---------------------------------------------------------------------------


def _entry(key: str) -> model.DictionaryEntry:
    """Return the dictionary entry for `key`, or fail naming the table's real keys.

    Two failure modes are distinguished, because they mean different things. A key whose
    TABLE half is known but whose column half is wrong is the near miss this section
    exists for, and the real keys of that table are listed so the mistake is obvious. A
    key whose table half is unknown too is a different error, and the loader's own
    diagnostic is the better one to surface. The fallback lookup is itself guarded, so
    this helper can never raise a second exception out of its own handler.
    """
    try:
        return loader.get_entry(key)
    except loader.DictionaryKeyError as exc:  # KeyError subclass; see loader.__all__
        table, separator, _column = key.partition(".")
        siblings: tuple[str, ...] = ()
        if separator:
            try:
                siblings = tuple(
                    sibling.key for sibling in loader.entries_for_table(table)
                )
            except loader.DictionaryLookupError:
                # The table half is unknown as well, so there are no sibling keys to
                # show; the loader's message below already says so.
                siblings = ()
        qualification = (
            f"Keys present for table {table!r}: {siblings}."
            if separator
            else f"{key!r} is unqualified: a bare field name is never a key."
        )
        raise AssertionError(
            f"the data dictionary has no entry keyed {key!r}. "
            f"Keys are <TABLE-NAME>.<COLUMN-NAME>, exact and case-sensitive. "
            f"{qualification} "
            f"Loader detail: {exc}"
        ) from exc


def _descriptor(key: str) -> cobol_field.FieldDescriptor:
    """Return the `FieldDescriptor` for `key`, looked up through the dictionary only.

    `_entry` is called first so that a bad key fails with the dictionary's own
    near-miss diagnostics rather than with a bare `KeyError` from the descriptor
    factory.
    """
    _entry(key)
    return cobol_field.FieldDescriptor.from_dictionary_key(key)


def _encode(descriptor: cobol_field.FieldDescriptor, value: Decimal) -> bytes:
    """Encode `value` into `descriptor`'s zoned representation.

    Every storage keyword is taken from the descriptor, so the encoding under test is
    driven by the field's dictionary entry and by nothing restated here (R-5). The
    rounding direction is passed explicitly rather than left to a default, because the
    direction of a store is the single decision that decides whether a penny moves
    (R-2): an un-`ROUNDED` COBOL store truncates toward zero, and `ROUND_DOWN` is that
    behaviour. Nothing here reads or mutates the ambient decimal context.
    """
    return cobol_usage.encode(
        value,
        usage=descriptor.usage,
        digits=descriptor.digits,
        scale=descriptor.scale,
        signed=descriptor.signed,
        unsigned=descriptor.unsigned,
        sign_position=descriptor.sign_position,
        rounding=ROUND_DOWN,
    )


def _decode(descriptor: cobol_field.FieldDescriptor, raw: bytes) -> Decimal:
    """Decode `raw` back out of `descriptor`'s zoned representation.

    The `Decimal` check is not decoration: the field is declared money, so a decode that
    handed back an `int` or a `str` would silently drop the scale and every downstream
    equality would still look plausible.
    """
    decoded = cobol_usage.decode(
        raw,
        usage=descriptor.usage,
        digits=descriptor.digits,
        scale=descriptor.scale,
        signed=descriptor.signed,
        unsigned=descriptor.unsigned,
        sign_position=descriptor.sign_position,
    )
    assert isinstance(decoded, Decimal), (
        f"{descriptor.dictionary_key} is declared "
        f"{descriptor.python_storage.value}, so decode must yield a Decimal and not "
        f"{type(decoded).__name__}"
    )
    return decoded


def _sign_carrying_index(raw: bytes, descriptor: cobol_field.FieldDescriptor) -> int:
    """Which byte of `raw` an INCLUDED sign is overpunched into.

    Derived from the encoded width actually produced rather than from
    `descriptor.byte_length`, so that this helper stays independent of the unarbitrated
    Q-5.2 width.
    """
    if descriptor.sign_position is model.SignPosition.LEADING_INCLUDED:
        return 0
    if descriptor.sign_position is model.SignPosition.TRAILING_INCLUDED:
        return len(raw) - 1
    raise AssertionError(
        f"{descriptor.dictionary_key} declares "
        f"{descriptor.sign_position.value}, which is not one of the two INCLUDED "
        f"positions this module exercises"
    )


# ---------------------------------------------------------------------------
#  SECTION 3  -  THE TWO SPELLINGS, PRESERVED VERBATIM
#
#  The declared TEXT is kept exactly as the copybook writes it; the SEMANTICS collapse
#  onto one `SignPosition` member. Preserve the spelling, unify the meaning.
# ---------------------------------------------------------------------------


def test_sign_leading_spellings_are_the_two_the_frozen_sources_use() -> None:
    """`usage.SIGN_LEADING_SPELLINGS` is exactly the two forms that occur.

    Provenance: `sign leading` at [copybooks/wspost-irs.cob:L21] and
    [copybooks/wspost-irs.cob:L25]; `sign is leading` at [copybooks/irswspost.cob:L14]
    and [copybooks/irswspost.cob:L18]. Order matters and is asserted: the tuple is
    declared `Final` in acas_posting/cobol/usage.py:L82 and a reordering would silently
    change any membership test written against an index.
    """
    assert cobol_usage.SIGN_LEADING_SPELLINGS == ("sign leading", "sign is leading")


def test_spl_transfer_amount_keeps_the_two_word_spelling_verbatim() -> None:
    """`PSIRSPOST-REC.IRS-POST-AMOUNT` reports `sign leading`, unaltered.

    Provenance: [copybooks/wspost-irs.cob:L21], verbatim -
        `03  WS-IRS-Post-Amount     pic s9(7)v99   sign leading.`
    Exact string, no case folding, no whitespace rewriting, and specifically NOT
    rewritten into the `sign is leading` form the other posting record uses.
    """
    descriptor = _descriptor(SPL_POST_AMOUNT_KEY)

    assert descriptor.sign_clause_text == "sign leading"
    assert descriptor.source_locator == "copybooks/wspost-irs.cob:L21"


def test_irs_internal_amount_keeps_the_three_word_spelling_verbatim() -> None:
    """`IRSPOSTING-REC.POST4-AMOUNT` reports `sign is leading`, unaltered.

    Provenance: [copybooks/irswspost.cob:L14], verbatim -
        `03  Post-Amount     pic s9(7)v99  sign is leading.`
    The Agent Action Plan body cites L19 for this record's second such field; L19 is a
    `*>` comment line and the declaration is on L18. Both L14 and L18 are asserted, and
    both are the locators the generated dictionary itself records.
    """
    descriptor = _descriptor(IRS_POST_AMOUNT_KEY)

    assert descriptor.sign_clause_text == "sign is leading"
    assert descriptor.source_locator == "copybooks/irswspost.cob:L14"

    vat_descriptor = _descriptor(IRS_VAT_AMOUNT_KEY)
    assert vat_descriptor.sign_clause_text == "sign is leading"
    assert vat_descriptor.source_locator == "copybooks/irswspost.cob:L18"


def test_spl_transfer_vat_amount_keeps_the_two_word_spelling_verbatim() -> None:
    """The transfer record's second leading-sign field, on its own locator.

    Provenance: [copybooks/wspost-irs.cob:L25], verbatim -
        `03  WS-IRS-Vat-Amount      pic s9(7)v99   sign leading.`
    Asserted separately from L21 because a generator that read only the first field of a
    record would still pass a single-field test.
    """
    descriptor = _descriptor(SPL_VAT_AMOUNT_KEY)

    assert descriptor.sign_clause_text == "sign leading"
    assert descriptor.source_locator == "copybooks/wspost-irs.cob:L25"


@pytest.mark.parametrize(
    ("key", "clause_text", "locator"),
    LEADING_SIGN_FIELDS,
    ids=[key for key, _clause, _locator in LEADING_SIGN_FIELDS],
)
def test_every_leading_sign_field_reports_its_clause_and_locator(
    key: str, clause_text: str, locator: str
) -> None:
    """All four leading-sign fields, each with its own clause text and locator.

    Provenance: the four declarations at [copybooks/wspost-irs.cob:L21],
    [copybooks/wspost-irs.cob:L25], [copybooks/irswspost.cob:L14] and
    [copybooks/irswspost.cob:L18]. The clause text is whichever of the two spellings its
    own copybook writes, and every one of them is a member of the published tuple - so
    the vocabulary is complete and nothing outside it has crept in.
    """
    descriptor = _descriptor(key)

    assert descriptor.sign_clause_text == clause_text
    assert descriptor.source_locator == locator
    assert descriptor.sign_clause_text in cobol_usage.SIGN_LEADING_SPELLINGS


@pytest.mark.parametrize(
    "key",
    [key for key, _clause, _locator in LEADING_SIGN_FIELDS],
)
def test_leading_sign_fields_share_one_storage_description(key: str) -> None:
    """Two spellings, ONE storage description - the whole point of preserving both.

    Provenance: both records declare `pic s9(7)v99` - [copybooks/wspost-irs.cob:L21],
    [copybooks/wspost-irs.cob:L25], [copybooks/irswspost.cob:L14],
    [copybooks/irswspost.cob:L18] - with no `usage` clause, so the item is `DISPLAY`,
    which is zoned decimal. Nine declared digits, seven of them integral, scale two;
    signed, so the sign is real and not decoration; carried in Python as
    `decimal.Decimal` because it is money (R-2), never as a float. Its quantum is
    therefore 0.01, which is the value a store must land on exactly.
    """
    descriptor = _descriptor(key)

    assert descriptor.usage is model.Usage.DISPLAY
    assert descriptor.sign_position is model.SignPosition.LEADING_INCLUDED
    assert descriptor.is_zoned_display is True
    assert cobol_usage.is_zoned_display(descriptor.usage) is True
    assert descriptor.picture == LEADING_SIGN_PICTURE
    assert descriptor.digits == LEADING_SIGN_DIGITS
    assert descriptor.integer_digits == LEADING_SIGN_INTEGER_DIGITS
    assert descriptor.scale == LEADING_SIGN_SCALE
    assert descriptor.signed is True
    assert descriptor.unsigned is False
    assert descriptor.python_storage is model.CobolPythonStorage.DECIMAL
    assert descriptor.quantum == MONEY_QUANTUM


def test_both_spellings_parse_to_different_text_and_the_same_position() -> None:
    """The picture parser preserves the spelling and unifies the semantics.

    Provenance: the two declarations parsed here are the frozen lines themselves,
    [copybooks/irswspost.cob:L14] and [copybooks/wspost-irs.cob:L21], each passed with
    its own `source_locator` so the parse is traceable (R-5).

    This is the contract in one assertion pair: the two `sign_clause_text` values DIFFER
    - neither spelling is rewritten into the other - while the two `sign_position`
    values are IDENTICAL, so one encoder serves both. Collapsing the text would destroy
    evidence about the frozen source; splitting the position would duplicate the
    encoder.
    """
    three_word = cobol_picture.parse_entry(
        "03  Post-Amount     pic s9(7)v99  sign is leading.",
        source_locator="copybooks/irswspost.cob:L14",
    )
    two_word = cobol_picture.parse_entry(
        "03  WS-IRS-Post-Amount     pic s9(7)v99   sign leading.",
        source_locator="copybooks/wspost-irs.cob:L21",
    )

    assert three_word.sign_clause_text == "sign is leading"
    assert two_word.sign_clause_text == "sign leading"
    assert three_word.sign_clause_text != two_word.sign_clause_text

    assert three_word.sign_position is model.SignPosition.LEADING_INCLUDED
    assert two_word.sign_position is model.SignPosition.LEADING_INCLUDED
    assert three_word.sign_position is two_word.sign_position

    # And the rest of the two descriptions agree exactly, which is what makes the
    # differing text purely a record of how the maintainer typed it.
    for parsed in (three_word, two_word):
        assert parsed.picture is not None
        assert parsed.picture.text == LEADING_SIGN_PICTURE
        assert parsed.picture.digits == LEADING_SIGN_DIGITS
        assert parsed.picture.integer_digits == LEADING_SIGN_INTEGER_DIGITS
        assert parsed.picture.scale == LEADING_SIGN_SCALE
        assert parsed.picture.signed is True
        assert parsed.usage is model.Usage.DISPLAY
        assert parsed.sign_clause_text in cobol_usage.SIGN_LEADING_SPELLINGS


def test_parsed_entry_and_dictionary_entry_agree_on_the_clause_text() -> None:
    """Parsing the frozen line yields the same clause text the dictionary recorded.

    Provenance: [copybooks/irswspost.cob:L14] and [copybooks/wspost-irs.cob:L21]. Two
    independent routes to the same field - `picture.parse_entry` reading the declaration
    text, and `dictionary.loader` reading the generated artifact - must report the same
    spelling and the same position, or one of them is normalising.
    """
    parsed_three_word = cobol_picture.parse_entry(
        "03  Post-Amount     pic s9(7)v99  sign is leading.",
        source_locator="copybooks/irswspost.cob:L14",
    )
    parsed_two_word = cobol_picture.parse_entry(
        "03  WS-IRS-Post-Amount     pic s9(7)v99   sign leading.",
        source_locator="copybooks/wspost-irs.cob:L21",
    )

    for parsed, key in (
        (parsed_three_word, IRS_POST_AMOUNT_KEY),
        (parsed_two_word, SPL_POST_AMOUNT_KEY),
    ):
        descriptor = _descriptor(key)
        assert parsed.name == descriptor.name
        assert parsed.sign_clause_text == descriptor.sign_clause_text
        assert parsed.sign_position is descriptor.sign_position
        assert parsed.source_locator == descriptor.source_locator


# ---------------------------------------------------------------------------
#  SECTION 4  -  THE TWO RECORDS ARE DISTINCT ENTRIES, AND NEVER MERGED
#
#  [copybooks/wspost-irs.cob:L6-L7] states it in the source, verbatim:
#      *> This is NOT the same as the internal IRS *
#      *>   posting file                           *
#  The two records carry near-identical field names on purpose - one is the transfer
#  file the Sales and Purchase programs write on the IRS fan-out, the other is the
#  internal IRS posting file irs030 maintains - so any lookup that is not
#  table-qualified would silently return the wrong record's metadata. These tests fail
#  if the dictionary were ever keyed by field name alone.
# ---------------------------------------------------------------------------


def test_the_two_posting_records_are_separate_dictionary_entries() -> None:
    """The two amount fields resolve to two different keys and two different entries.

    Provenance: [copybooks/wspost-irs.cob:L6-L7] - "This is NOT the same as the internal
    IRS posting file"; [copybooks/wspost-irs.cob:L21] against
    [copybooks/irswspost.cob:L14]; [mysql/ACASDB.sql:L366] against
    [mysql/ACASDB.sql:L274].
    """
    transfer = _entry(SPL_POST_AMOUNT_KEY)
    internal = _entry(IRS_POST_AMOUNT_KEY)

    assert transfer.key != internal.key
    assert transfer.table == SPL_TRANSFER_TABLE
    assert internal.table == IRS_INTERNAL_TABLE
    assert transfer.table != internal.table
    assert transfer is not internal


def test_the_two_descriptors_are_not_equal() -> None:
    """`FieldDescriptor` distinguishes them, so no code path can substitute one.

    `FieldDescriptor` is a frozen dataclass with value equality, which is exactly why
    this has to be asserted: two fields that shared every attribute WOULD compare equal
    and could be interchanged. They do not, because their names, their pictures' owners
    and their dictionary keys differ - [copybooks/wspost-irs.cob:L21] declares
    `WS-IRS-Post-Amount`, [copybooks/irswspost.cob:L14] declares `Post-Amount`.

    Same key twice must still compare equal, or the inequality above would prove nothing
    about identity and everything about a broken `__eq__`.
    """
    transfer = _descriptor(SPL_POST_AMOUNT_KEY)
    internal = _descriptor(IRS_POST_AMOUNT_KEY)

    assert transfer != internal
    assert transfer.dictionary_key != internal.dictionary_key
    assert transfer.name != internal.name
    assert transfer.source_locator != internal.source_locator

    assert transfer == _descriptor(SPL_POST_AMOUNT_KEY)
    assert internal == _descriptor(IRS_POST_AMOUNT_KEY)


def test_the_two_records_have_ten_and_thirteen_column_mapped_entries() -> None:
    """Ten columns against thirteen - the count itself distinguishes them.

    Provenance: [mysql/ACASDB.sql:L366-L377] declares `PSIRSPOST-REC` with ten columns;
    [mysql/ACASDB.sql:L274-L288] declares `IRSPOSTING-REC` with thirteen. The extra
    three are POST4-DAY, POST4-MONTH and POST4-YEAR, which have no counterpart in any
    copybook and exist only because the bridge derives them from a date string
    [common/irspostingMT.cbl:L982-L987]. Every entry of both tables is mapped to a
    column, which is asserted rather than assumed so that a copybook-only entry could
    not pad either count.
    """
    transfer_entries = loader.entries_for_table(SPL_TRANSFER_TABLE)
    internal_entries = loader.entries_for_table(IRS_INTERNAL_TABLE)

    assert len(transfer_entries) == SPL_TRANSFER_COLUMN_COUNT
    assert len(internal_entries) == IRS_INTERNAL_COLUMN_COUNT

    assert all(entry.column is not None for entry in transfer_entries)
    assert all(entry.column is not None for entry in internal_entries)

    # And the table records agree with the entry counts, so the two views of the same
    # frozen DDL cannot drift apart.
    assert (
        loader.table_for(SPL_TRANSFER_TABLE).column_count == SPL_TRANSFER_COLUMN_COUNT
    )
    assert (
        loader.table_for(IRS_INTERNAL_TABLE).column_count == IRS_INTERNAL_COLUMN_COUNT
    )


def test_the_two_records_route_through_different_bridges_and_handlers() -> None:
    """Different bridge, different handler - the call chains never meet.

    Provenance: the transfer file is reached through handler `acas008` and bridge
    `slpostingMT` [common/slpostingMT.cbl:L271 declares its amount host variable]; the
    internal IRS posting file is reached through handler `acasirsub4` and bridge
    `irspostingMT` [common/irspostingMT.cbl:L182]. Agent Action Plan section 0.2.1.1
    entity-to-table spine.
    """
    transfer = _entry(SPL_POST_AMOUNT_KEY)
    internal = _entry(IRS_POST_AMOUNT_KEY)

    assert transfer.bridge == SPL_TRANSFER_BRIDGE
    assert transfer.handler == SPL_TRANSFER_HANDLER
    assert internal.bridge == IRS_INTERNAL_BRIDGE
    assert internal.handler == IRS_INTERNAL_HANDLER

    assert transfer.bridge != internal.bridge
    assert transfer.handler != internal.handler

    # Each handler owns exactly its own table, so a handler lookup cannot reach across.
    assert tuple(
        record.name for record in loader.tables_for_handler(SPL_TRANSFER_HANDLER)
    ) == (SPL_TRANSFER_TABLE,)
    assert tuple(
        record.name for record in loader.tables_for_handler(IRS_INTERNAL_HANDLER)
    ) == (IRS_INTERNAL_TABLE,)


def test_no_entry_is_reachable_by_bare_field_name() -> None:
    """A field name alone is NOT a key, and must never become one.

    `POST-AMOUNT` is a column name in `GLPOSTING-REC` and, unqualified, is also the
    obvious short name for the amount field of both IRS posting records. If the
    dictionary were keyed by field name the three would collide and a caller would get
    whichever the generator happened to write last. `find_entry` returns `None` for the
    bare name, which is the observable that proves the key space is qualified.

    `POST-AMOUNT`, `IRS-POST-AMOUNT`, `POST4-AMOUNT` and `Post-Amount` are all checked:
    the column names of the three records and the copybook field name that two of them
    share [copybooks/wspost.cob:L23], [copybooks/irswspost.cob:L14].
    """
    for bare_name in (
        "POST-AMOUNT",
        "IRS-POST-AMOUNT",
        "POST4-AMOUNT",
        "VAT-AMOUNT4",
        "Post-Amount",
    ):
        assert loader.find_entry(bare_name) is None, (
            f"{bare_name!r} was accepted as a key; the key space must stay "
            f"table-qualified so the two posting records cannot be conflated"
        )

    # Every key in the dictionary is qualified, so the property holds globally and not
    # merely for the names spelled out above.
    assert all("." in key for key in loader.entry_keys())


def test_a_plausible_but_wrong_qualified_key_is_rejected() -> None:
    """The near miss that motivates the whole section is rejected, not silently mapped.

    `PSIRSPOST-REC.POST-AMOUNT` reads as if it must be right - the record's copybook
    field is `WS-IRS-Post-Amount` and the sibling General Ledger table does have a
    `POST-AMOUNT` column. It is wrong: that table's column is `IRS-POST-AMOUNT`
    [mysql/ACASDB.sql:L372]. `find_entry` returns `None` and `get_entry` raises
    `DictionaryKeyError`, which is a `KeyError` subclass, so a caller that has not
    thought about the distinction cannot get a plausible-looking wrong answer.

    The file-local resolver converts that into a failure that lists the table's real
    keys, which is asserted here so the diagnostic itself is covered.
    """
    assert loader.find_entry("PSIRSPOST-REC.POST-AMOUNT") is None

    with pytest.raises(loader.DictionaryKeyError):
        loader.get_entry("PSIRSPOST-REC.POST-AMOUNT")

    assert issubclass(loader.DictionaryKeyError, KeyError)

    with pytest.raises(AssertionError) as failure:
        _entry("PSIRSPOST-REC.POST-AMOUNT")

    message = str(failure.value)
    assert "PSIRSPOST-REC.POST-AMOUNT" in message
    assert SPL_POST_AMOUNT_KEY in message


# ---------------------------------------------------------------------------
#  SECTION 5  -  Q-5.2, THE WIDTH OF A LEADING-SIGN DISPLAY ITEM
#
#  The frozen sources support two readings and they differ by exactly one byte.
#
#  READING A - the maintainer's own byte accounting. [copybooks/wspost.cob:L6-L7],
#  verbatim:
#      *> 98 bytes 26/03/09
#      *> 96 bytes 20/12/11 (leading sign removed)
#  The clause was dropped from TWO fields and the record shrank by TWO bytes. One byte
#  per field. On that reading the leading sign occupied a byte of its own and the width
#  is digits + 1, i.e. 10 for `pic s9(7)v99 sign leading`.
#
#  READING B - the ISO overpunch reading. `SIGN LEADING` written WITHOUT `SEPARATE` is
#  overpunched into the leading digit and costs nothing, so the width is digits, i.e. 9.
#  This is the reading acas_posting/cobol/usage.py:L414-L421 implements, and the line
#  that names the id is L415.
#
#  READING C - and this is why A is genuinely puzzling rather than obviously right. In
#  the SAME copybook the TRAILING sign is provably overpunched: the running offsets go
#  36 -> 46 across `Post-Amount pic s9(8)v99` [copybooks/wspost.cob:L22-L23] and
#  86 -> 96 across `Vat-Amount pic s9(8)v99` [copybooks/wspost.cob:L27-L28]. Ten bytes
#  for ten digits, twice. An included sign costs nothing there, which makes the
#  one-byte-per-field history of the LEADING case a real question and not a typo.
#
#  Under R-6 an expected value comes from the compiled oracle, never from reading the
#  COBOL and reasoning about what it ought to produce. No such measurement is on record
#  for the leading case anywhere in this tree: `FieldDescriptor.ambiguity_refs()` is
#  empty for all four leading-sign fields, and docs/migration/ambiguity-resolutions.md
#  carries no entry this test could cite. acas_posting/cobol/usage.py:L415 labels the
#  question and picks Reading B to have something to run with; that choice is a working
#  position, not an oracle measurement, so this module refuses to assert EITHER width as
#  fact. What it asserts instead is what can be asserted without arbitrating: the shape
#  of the disagreement, and the fact that the descriptor and the storage module agree
#  with each other about whatever width is in force.
# ---------------------------------------------------------------------------


def test_the_two_readings_of_q_5_2_differ_by_exactly_one_byte() -> None:
    """Reading A and Reading B are one byte apart - the shape of the disagreement.

    This is the substance of Q-5.2 stated WITHOUT naming a width: an item whose sign is
    SEPARATE is priced one byte wider than the otherwise identical item whose sign is
    INCLUDED, so the two readings of `sign leading` can differ by one byte and by no
    more. Asserted for both the leading and the trailing SEPARATE forms, and for both
    in-scope digit counts - nine for `pic s9(7)v99` [copybooks/wspost-irs.cob:L21] and
    ten for `pic s9(8)v99` [copybooks/wspost.cob:L23].

    Nothing here decides which reading holds. Because the assertion is a RELATIONSHIP
    rather than a value, it stays true whichever way Q-5.2 is eventually arbitrated.
    """
    for digits, scale in (
        (LEADING_SIGN_DIGITS, LEADING_SIGN_SCALE),
        (TRAILING_SIGN_DIGITS, TRAILING_SIGN_SCALE),
    ):
        included_leading = cobol_usage.byte_length(
            model.Usage.DISPLAY,
            digits=digits,
            scale=scale,
            sign_position=model.SignPosition.LEADING_INCLUDED,
        )
        separate_leading = cobol_usage.byte_length(
            model.Usage.DISPLAY,
            digits=digits,
            scale=scale,
            sign_position=model.SignPosition.LEADING_SEPARATE,
        )
        included_trailing = cobol_usage.byte_length(
            model.Usage.DISPLAY,
            digits=digits,
            scale=scale,
            sign_position=model.SignPosition.TRAILING_INCLUDED,
        )
        separate_trailing = cobol_usage.byte_length(
            model.Usage.DISPLAY,
            digits=digits,
            scale=scale,
            sign_position=model.SignPosition.TRAILING_SEPARATE,
        )

        assert separate_leading == included_leading + 1
        assert separate_trailing == included_trailing + 1

        # An implied decimal point occupies no byte, so the scale never enters the
        # width. `pic s9(7)v99` and `pic s9(9)` are the same nine bytes.
        assert included_leading == cobol_usage.byte_length(
            model.Usage.DISPLAY,
            digits=digits,
            scale=0,
            sign_position=model.SignPosition.LEADING_INCLUDED,
        )


def test_descriptor_width_delegates_to_the_storage_module() -> None:
    """The descriptor and `usage.byte_length` agree, whatever width is in force.

    Two layers price the same field: `FieldDescriptor.byte_length` and
    `usage.byte_length`. If they ever disagreed, one of them would be carrying a second,
    private answer to Q-5.2 - and a second definition of one vocabulary is exactly the
    divergence R-4 forbids.

    No width is named. This test cannot be made to pass or fail by arbitrating Q-5.2 in
    either direction; it only pins the two layers together. Asserted across all four
    leading-sign fields [copybooks/wspost-irs.cob:L21], [copybooks/wspost-irs.cob:L25],
    [copybooks/irswspost.cob:L14], [copybooks/irswspost.cob:L18] and both trailing-sign
    fields [copybooks/wspost.cob:L23], [copybooks/wspost.cob:L28].
    """
    keys = [key for key, _clause, _locator in LEADING_SIGN_FIELDS] + [
        GL_POST_AMOUNT_KEY,
        GL_VAT_AMOUNT_KEY,
    ]
    for key in keys:
        descriptor = _descriptor(key)
        assert descriptor.byte_length == cobol_usage.byte_length(
            descriptor.usage,
            digits=descriptor.digits,
            scale=descriptor.scale,
            sign_position=descriptor.sign_position,
            unsigned=descriptor.unsigned,
        )


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Q-5.2 - the width of a leading-sign DISPLAY item is not arbitrated. "
        "Reading A, the maintainer's own byte accounting at "
        '[copybooks/wspost.cob:L6-L7] ("98 bytes 26/03/09" then "96 bytes 20/12/11 '
        '(leading sign removed)": two fields, two bytes, one byte each), gives '
        "digits + 1 = 10 bytes for pic s9(7)v99 sign leading. Reading B, the ISO "
        "overpunch reading implemented at acas_posting/cobol/usage.py:L414-L421 and "
        "named at L415, gives digits = 9. R-6 requires the compiled oracle to decide, "
        "and no measurement for the leading case is on record: "
        "FieldDescriptor.ambiguity_refs() is empty for all four leading-sign fields. "
        "This test asserts Reading A, so it fails while Reading B is in force. "
        "strict=True is deliberate and must not be softened to strict=False or to "
        "raises=: when the oracle settles Q-5.2 in favour of Reading A the test will "
        "XPASS and fail the suite, which is the signal to delete this marker and "
        "promote the width to a fact."
    ),
)
def test_leading_sign_byte_length_is_unarbitrated_q_5_2() -> None:
    """Q-5.2: assert Reading A, which does not hold while Reading B is implemented.

    Two assertions, in this order and for a reason.

    The FIRST records the width actually in force without hard-coding it, by asserting
    that the descriptor and `usage.byte_length` agree. That holds today and would still
    hold after an arbitration, so it never masks the second assertion - which is the
    whole point of writing it as a delegation rather than as a literal 9.

    The SECOND is the claim Q-5.2 has to settle: Reading A's width of digits + 1, from
    [copybooks/wspost.cob:L6-L7]. It fails today, so this test xfails and the suite
    stays green while the question is open. If `usage.byte_length` is ever changed to
    price a leading INCLUDED sign at digits + 1, both assertions hold, the test XPASSes
    and `strict=True` fails the suite - forcing whoever made the change to record the
    arbitration and turn this into a plain assertion.

    Neither 9 nor 10 is asserted as fact anywhere outside this xfail.
    """
    descriptors = [
        _descriptor(key) for key, _clause, _locator in LEADING_SIGN_FIELDS
    ]

    # Reading B, as currently in force - stated through the delegation so that no width
    # is written down here.
    for descriptor in descriptors:
        assert descriptor.sign_position is model.SignPosition.LEADING_INCLUDED
        assert descriptor.byte_length == cobol_usage.byte_length(
            descriptor.usage,
            digits=descriptor.digits,
            scale=descriptor.scale,
            sign_position=descriptor.sign_position,
            unsigned=descriptor.unsigned,
        )

    # Reading A - one byte for the sign, from the maintainer's own byte accounting.
    for descriptor in descriptors:
        assert descriptor.byte_length == descriptor.digits + 1


# ---------------------------------------------------------------------------
#  SECTION 6  -  THE TRAILING SIGN'S WIDTH, WHICH *IS* A FACT
#
#  Not an xfail. [copybooks/wspost.cob] carries running byte offsets in its own
#  end-of-line comments, and they settle the trailing case twice over.
# ---------------------------------------------------------------------------


def test_trailing_sign_width_is_ten_bytes_for_ten_digits() -> None:
    """`GLPOSTING-REC.POST-AMOUNT` is ten bytes for ten digits - proven, not read.

    Provenance, verbatim from [copybooks/wspost.cob:L22-L23]:
        03  CR-PC           pic 99.      *> 36
        03  Post-Amount     pic s9(8)v99.  *> 46
    and again from [copybooks/wspost.cob:L27-L28]:
        03  Post-Vat-Side   pic xx.        *> 86
        03  Vat-Amount      pic s9(8)v99.  *> 96

    The arithmetic: 46 - 36 == 10 and 96 - 86 == 10. Both fields declare
    `pic s9(8)v99`, which is ten digits, and both occupy ten bytes. So the sign of a
    trailing-sign DISPLAY item is overpunched into its last digit and costs no byte -
    twice, independently, in the maintainer's own bookkeeping. That is why this width is
    asserted as fact while the leading case in Section 5 is not.
    """
    # The two offset differences the copybook records, asserted as arithmetic rather
    # than restated as a bare 10, so the provenance is executable.
    assert (
        TRAILING_OFFSET_AFTER_POST_AMOUNT - TRAILING_OFFSET_BEFORE_POST_AMOUNT
        == TRAILING_SIGN_PROVEN_BYTES
    )
    assert (
        TRAILING_OFFSET_AFTER_VAT_AMOUNT - TRAILING_OFFSET_BEFORE_VAT_AMOUNT
        == TRAILING_SIGN_PROVEN_BYTES
    )

    for key, locator in (
        (GL_POST_AMOUNT_KEY, "copybooks/wspost.cob:L23"),
        (GL_VAT_AMOUNT_KEY, "copybooks/wspost.cob:L28"),
    ):
        descriptor = _descriptor(key)

        # A third record, and a third table: the width proven here belongs to the
        # General Ledger posting file, not to either of the two IRS posting records.
        assert _entry(key).table == GL_POSTING_TABLE
        assert descriptor.source_locator == locator
        assert descriptor.usage is model.Usage.DISPLAY
        assert descriptor.is_zoned_display is True
        assert descriptor.sign_position is model.SignPosition.TRAILING_INCLUDED
        assert descriptor.picture == TRAILING_SIGN_PICTURE
        assert descriptor.digits == TRAILING_SIGN_DIGITS
        assert descriptor.integer_digits == TRAILING_SIGN_INTEGER_DIGITS
        assert descriptor.scale == TRAILING_SIGN_SCALE
        assert descriptor.signed is True
        assert descriptor.python_storage is model.CobolPythonStorage.DECIMAL
        assert descriptor.quantum == MONEY_QUANTUM

        # The fact itself: ten bytes, and ten digits, so the included sign is free.
        assert descriptor.byte_length == TRAILING_SIGN_PROVEN_BYTES
        assert descriptor.byte_length == descriptor.digits


def test_the_trailing_sign_fields_declare_no_sign_clause_at_all() -> None:
    """The trailing case is the DEFAULT, which is why it has no clause text.

    Provenance: [copybooks/wspost.cob:L23] and [copybooks/wspost.cob:L28] write
    `pic s9(8)v99.` and stop - no `sign` clause of any kind. COBOL's default for a
    signed DISPLAY item is a trailing included sign, so `sign_clause_text` is `None`
    here while
    it is one of the two spellings on the four leading-sign fields. That asymmetry is
    real and is preserved: a clause text is recorded only where the copybook wrote one.
    """
    for key in (GL_POST_AMOUNT_KEY, GL_VAT_AMOUNT_KEY):
        descriptor = _descriptor(key)
        assert descriptor.sign_clause_text is None
        assert descriptor.sign_position is model.SignPosition.TRAILING_INCLUDED

    for key, _clause, _locator in LEADING_SIGN_FIELDS:
        descriptor = _descriptor(key)
        assert descriptor.sign_clause_text is not None


# ---------------------------------------------------------------------------
#  SECTION 7  -  ZONED ENCODING: ROUND TRIP, CONSTANT WIDTH, AND WHICH BYTE MOVES
#
#  Q-5.3 covers the overpunch BYTE VALUES - `usage.ZONED_POSITIVE_BASE` and
#  `usage.ZONED_NEGATIVE_BASE`, named at acas_posting/cobol/usage.py:L94. This section
#  asserts NO specific overpunch byte and no literal byte string anywhere: under R-6 a
#  byte value would have to come from the compiled oracle, and none is on record here.
#
#  What can be asserted without one is everything that actually matters to the
#  migration, because each of these follows from the storage module's own contract
#  rather than from a measured byte:
#    * the encoding round-trips exactly, at full declared scale, with no float in the
#      path (R-2);
#    * the width is CONSTANT for a given field - a leading sign does not widen it;
#    * the sign is recoverable; and
#    * a value and its negation differ in EXACTLY ONE byte position, and it is the
#      LEADING byte for a `sign leading` field and the TRAILING byte for the General
#      Ledger record. That position is the observable that tells the two apart, and it
#      needs no knowledge of what the byte contains.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "key",
    [key for key, _clause, _locator in LEADING_SIGN_FIELDS]
    + [GL_POST_AMOUNT_KEY, GL_VAT_AMOUNT_KEY],
)
@pytest.mark.parametrize("magnitude", ZONED_ROUND_TRIP_MAGNITUDES)
def test_zoned_encoding_round_trips_exactly(key: str, magnitude: str) -> None:
    """`decode(encode(v)) == v`, positive and negative, at full declared scale.

    Provenance of the value set: `pic s9(7)v99` [copybooks/wspost-irs.cob:L21],
    [copybooks/irswspost.cob:L14] holds nine digits with scale two, so 9999999.99 is its
    maximum and 1234567.89 fills every one of the nine digit positions with a distinct
    digit - a transposition would show up in the encoding. 0.01 is the smallest non-zero
    value the scale admits and 0.00 is the value at which an overpunch is least visible.
    `pic s9(8)v99` [copybooks/wspost.cob:L23] is two digits wider, so the same set fits
    it too.

    Every value is built from a `Decimal` STRING, positive and negative alike, and that
    is deliberate rather than incidental: `Decimal.__neg__` is a CONTEXT operation, so
    `-Decimal("9999999.99")` is rounded to the ambient precision and at a reduced
    `prec` would hand this test a different number than the one it means to encode.
    Prefixing the string instead makes the operand exact whatever the ambient context
    holds. Nothing here reads or mutates that context: the scale comes from the
    descriptor and the rounding direction is passed explicitly, and there is no float in
    this path at any point (R-2).
    """
    descriptor = _descriptor(key)
    for value in (Decimal(magnitude), Decimal("-" + magnitude)):
        raw = _encode(descriptor, value)
        decoded = _decode(descriptor, raw)

        assert decoded == value
        # Exact, not merely numerically equal: the decoded value carries the field's own
        # scale, so a two-place money field never comes back as an integer.
        assert decoded.as_tuple().exponent == -descriptor.scale
        # The same property against the descriptor's own quantum, compared by EXPONENT
        # rather than by `decoded.quantize(descriptor.quantum)`. `Decimal.quantize` is a
        # context operation and raises `InvalidOperation` when the result needs more
        # digits than the ambient `prec` allows, so the quantize form asserts nothing
        # about this layer under a narrowed context - it only reports the context. An
        # exponent comparison is a property of the two values alone (R-2).
        assert decoded.as_tuple().exponent == descriptor.quantum.as_tuple().exponent


@pytest.mark.parametrize(
    "key",
    [key for key, _clause, _locator in LEADING_SIGN_FIELDS]
    + [GL_POST_AMOUNT_KEY, GL_VAT_AMOUNT_KEY],
)
def test_zoned_width_is_constant_across_every_value_of_a_field(key: str) -> None:
    """One field, one encoded width - positive, negative, zero and full width alike.

    A sign, wherever it sits, does not widen a zoned item: the encoded length is a
    property of the DECLARATION, not of the value. This is asserted as a single-element
    set of observed lengths rather than against a number, so it holds whichever way
    Q-5.2 is arbitrated. The width is separately asserted to agree with the descriptor,
    which is what ties the encoder to the field's dictionary entry.

    Provenance: the six fields parametrised here are the four `pic s9(7)v99`
    leading-sign declarations at [copybooks/wspost-irs.cob:L21],
    [copybooks/wspost-irs.cob:L25], [copybooks/irswspost.cob:L14] and
    [copybooks/irswspost.cob:L18], plus the two `pic s9(8)v99` trailing-sign
    declarations at [copybooks/wspost.cob:L23] and [copybooks/wspost.cob:L28].
    """
    descriptor = _descriptor(key)

    # Both signs are formed with `copy_negate()` rather than by multiplying by -1 or
    # by writing `-value`. Multiplication and unary minus are both CONTEXT operations
    # and round to the ambient `prec`, so either form would hand the encoder a
    # narrowed magnitude and the widths measured below would be the caller's
    # context's, not the field's. `copy_negate` touches the sign and nothing else: no
    # rounding, no signal, no context (R-2).
    widths = {
        len(_encode(descriptor, value))
        for magnitude in ZONED_ROUND_TRIP_MAGNITUDES
        for value in (Decimal(magnitude), Decimal(magnitude).copy_negate())
    }

    assert len(widths) == 1
    assert widths == {descriptor.byte_length}


@pytest.mark.parametrize(
    ("key", "expected_position"),
    [
        (SPL_POST_AMOUNT_KEY, model.SignPosition.LEADING_INCLUDED),
        (SPL_VAT_AMOUNT_KEY, model.SignPosition.LEADING_INCLUDED),
        (IRS_POST_AMOUNT_KEY, model.SignPosition.LEADING_INCLUDED),
        (IRS_VAT_AMOUNT_KEY, model.SignPosition.LEADING_INCLUDED),
        (GL_POST_AMOUNT_KEY, model.SignPosition.TRAILING_INCLUDED),
        (GL_VAT_AMOUNT_KEY, model.SignPosition.TRAILING_INCLUDED),
    ],
)
def test_exactly_one_byte_moves_and_it_is_the_declared_sign_position(
    key: str, expected_position: model.SignPosition
) -> None:
    """A value and its negation differ in ONE byte, at the DECLARED sign position.

    This is the observable that distinguishes a leading sign from a trailing one without
    depending on any overpunch byte value, which is Q-5.3 territory and deliberately
    untouched. For the four `sign leading` fields
    [copybooks/wspost-irs.cob:L21], [copybooks/wspost-irs.cob:L25],
    [copybooks/irswspost.cob:L14], [copybooks/irswspost.cob:L18] the moving byte is
    index 0. For the two General Ledger fields [copybooks/wspost.cob:L23],
    [copybooks/wspost.cob:L28], whose sign is the COBOL default trailing form, it is the
    last byte.

    Zero is excluded: COBOL has no negative zero and Python's `decimal` agrees, so a
    negated zero encodes identically and would show no moving byte at all. That is
    correct behaviour, and it is asserted separately below rather than swept into this
    loop.
    """
    descriptor = _descriptor(key)
    assert descriptor.sign_position is expected_position

    for magnitude in SIGNED_MAGNITUDES:
        # Both operands are built from strings. `Decimal.__neg__` is a context
        # operation, so negating a nine-digit magnitude under a reduced ambient `prec`
        # would silently round it and this test would then be comparing the encodings
        # of two DIFFERENT numbers. A string prefix is exact under any context.
        positive = _encode(descriptor, Decimal(magnitude))
        negative = _encode(descriptor, Decimal("-" + magnitude))

        assert len(positive) == len(negative)
        moved = tuple(
            index
            for index, (left, right) in enumerate(zip(positive, negative))
            if left != right
        )

        assert moved == (_sign_carrying_index(positive, descriptor),)

        # The sign really is recoverable, and it is the only thing that changed: every
        # other byte is untouched, and both decode back to the value that produced them.
        assert _decode(descriptor, negative) < 0
        assert _decode(descriptor, positive) > 0
        # Compared against the string-built negative rather than against
        # `-_decode(...)`, for the same reason: the unary minus would be evaluated in
        # the ambient context. The two are the same assertion when the context is
        # wide, and only this one is true when it is not.
        assert _decode(descriptor, negative) == Decimal("-" + magnitude)
        assert _decode(descriptor, positive) == Decimal(magnitude)


@pytest.mark.parametrize(
    "key",
    [key for key, _clause, _locator in LEADING_SIGN_FIELDS]
    + [GL_POST_AMOUNT_KEY, GL_VAT_AMOUNT_KEY],
)
def test_zero_has_no_sign_and_encodes_identically_either_way(key: str) -> None:
    """Negated zero is zero, so its encoding is byte-identical to positive zero.

    COBOL has no negative zero and Python's `decimal` gives `-Decimal("0.00")` back as
    `Decimal("0.00")`, so there is nothing for an overpunch to record. Asserted because
    it is the one value at which "exactly one byte moves" does NOT hold, and a reader
    who met the previous test first would otherwise be entitled to expect it to.

    Provenance: the same six declarations - [copybooks/wspost-irs.cob:L21] and [:L25],
    [copybooks/irswspost.cob:L14] and [:L18], [copybooks/wspost.cob:L23] and [:L28].
    """
    descriptor = _descriptor(key)

    positive_zero = _encode(descriptor, Decimal("0.00"))
    negated_zero = _encode(descriptor, -Decimal("0.00"))

    assert positive_zero == negated_zero
    assert _decode(descriptor, positive_zero) == Decimal("0.00")


def test_the_overpunch_tables_are_digit_indexed_and_disjoint() -> None:
    """The two overpunch tables are structurally sound - values NOT asserted.

    `usage.ZONED_POSITIVE_BASE` and `usage.ZONED_NEGATIVE_BASE` are the Q-5.3 tables
    named at acas_posting/cobol/usage.py:L94. What is asserted here is only structure,
    which the module's own contract fixes: one entry per decimal digit, each a single
    byte, the positive and negative families disjoint so a sign can be read back, and
    each entry's low nibble equal to the digit it stands for. Not one specific byte
    value is asserted, because under R-6 that value would have to come from the
    compiled oracle and no measurement is on record.
    """
    assert len(cobol_usage.ZONED_POSITIVE_BASE) == 10
    assert len(cobol_usage.ZONED_NEGATIVE_BASE) == 10

    for table in (cobol_usage.ZONED_POSITIVE_BASE, cobol_usage.ZONED_NEGATIVE_BASE):
        for digit, byte_value in enumerate(table):
            assert 0 <= byte_value <= 0xFF
            # A zoned digit's low nibble IS the digit; only the zone nibble carries the
            # sign. That relationship is the contract, independent of the zone's value.
            assert byte_value & 0x0F == digit

    assert not set(cobol_usage.ZONED_POSITIVE_BASE) & set(
        cobol_usage.ZONED_NEGATIVE_BASE
    )


# ---------------------------------------------------------------------------
#  SECTION 8  -  THE SAME VALUE, THREE STORAGE CLASSES, ONE BRIDGE CROSSING
#
#  The logical value has three representations on its way to the database, and they are
#  not the same storage class. Verbatim:
#      copybooks/irswspost.cob:L14      03  Post-Amount  pic s9(7)v99  sign is leading.
#      common/irspostingMT.cbl:L182         05  HV-POST4-AMOUNT  PIC S9(07)V9(02) COMP.
#      mysql/ACASDB.sql:L283                `POST4-AMOUNT` decimal(9,2) NOT NULL
#  Zoned DISPLAY with a leading sign, then signed binary COMP, then a DECIMAL column.
#  That is a USAGE drift, and it is reported exactly as it stands - not reconciled, not
#  smoothed, not treated as a defect. The signedness, by contrast, does NOT drift: the
#  item is signed at all three layers, which is why this field's value survives the
#  crossing intact where the Sales statistics fields' signs do not.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("key", "copybook_locator", "bridge_locator", "column_locator"),
    [
        (
            IRS_POST_AMOUNT_KEY,
            "copybooks/irswspost.cob:L14",
            "common/irspostingMT.cbl:L182",
            "mysql/ACASDB.sql:L283",
        ),
        (
            SPL_POST_AMOUNT_KEY,
            "copybooks/wspost-irs.cob:L21",
            "common/slpostingMT.cbl:L271",
            "mysql/ACASDB.sql:L372",
        ),
    ],
)
def test_usage_drifts_at_the_bridge_while_signedness_does_not(
    key: str, copybook_locator: str, bridge_locator: str, column_locator: str
) -> None:
    """`drift().usage is True` and `drift().signedness is False`, with the locators.

    The three declarations are cited above the section. This test pins both halves of
    the finding: the storage CLASS changes at the bridge, and the SIGNEDNESS does not.
    Both are stated as they stand; neither is arbitrated here.
    """
    descriptor = _descriptor(key)
    drift = descriptor.drift()

    assert drift.usage is True
    assert drift.signedness is False

    # And the digits and scale are stable across the crossing, so the usage change is
    # the only thing that moves in the numeric description.
    assert drift.digits is False
    assert drift.scale is False

    entry = _entry(key)

    # Layer 1 - the copybook: zoned DISPLAY, signed, leading sign.
    assert entry.copybook is not None
    assert entry.copybook.source == copybook_locator
    assert entry.copybook.usage is model.Usage.DISPLAY
    assert entry.copybook.signed is True
    assert entry.copybook.sign_position is model.SignPosition.LEADING_INCLUDED

    # Layer 2 - the bridge host variable: binary COMP, still signed.
    assert entry.bridge_host_variable is not None
    assert entry.bridge_host_variable.source == bridge_locator
    assert entry.bridge_host_variable.usage is model.Usage.COMP
    assert entry.bridge_host_variable.signed is True
    assert entry.bridge_host_variable.digits == LEADING_SIGN_DIGITS
    assert entry.bridge_host_variable.scale == LEADING_SIGN_SCALE

    # Layer 3 - the column: DECIMAL, and NOT unsigned, so the sign survives to storage.
    assert entry.column is not None
    assert entry.column.source == column_locator
    assert entry.column.base_type is model.SqlBaseType.DECIMAL
    assert entry.column.unsigned is False
    assert entry.column.scale == LEADING_SIGN_SCALE
    assert entry.column.nullable is False

    # The drift is reported in prose too, and the prose names all three layers.
    assert any("bridge" in detail for detail in drift.details)

    # The citation is the traceability artifact R-5 asks for: one string carrying all
    # three locators.
    citation = descriptor.cite()
    assert copybook_locator in citation
    assert bridge_locator in citation
    assert column_locator in citation


# ---------------------------------------------------------------------------
#  SECTION 9  -  THE ABSENCE CENSUS: `sign trailing` AND `separate` NEVER OCCUR
#
#  `LEADING_SEPARATE` and `TRAILING_SEPARATE` are part of the COBOL vocabulary and
#  `usage.byte_length` prices them, so they are modelled. No in-scope field uses either.
#  Both halves of that are asserted: the first without the second would look like
#  dead code and the second without the first would look like a gap.
# ---------------------------------------------------------------------------


def test_sign_position_models_the_separate_forms_it_never_meets() -> None:
    """The model defines all six positions, including the two that never occur.

    The full vocabulary is asserted as an exact tuple in declaration order: adding a
    seventh position or renaming one would change what every dictionary entry means, so
    it is worth pinning. Nothing in the frozen copybooks writes `separate` - the census
    in this module's docstring records zero occurrences of the keyword - yet the two
    SEPARATE forms are still priced by `usage.byte_length`, which is what makes them
    modelled rather than merely named.

    Provenance: the only sign clauses the frozen copybooks write are the four
    `sign leading` declarations at [copybooks/wspost-irs.cob:L21],
    [copybooks/wspost-irs.cob:L25], [copybooks/fdpost-irs.cob:L20] and
    [copybooks/fdpost-irs.cob:L24], and the two `sign is leading` declarations at
    [copybooks/irswspost.cob:L14] and [copybooks/irswspost.cob:L18]. Not one of the six
    carries `separate`.
    """
    assert tuple(member.name for member in model.SignPosition) == (
        "NONE",
        "TRAILING_INCLUDED",
        "LEADING_INCLUDED",
        "LEADING_SEPARATE",
        "TRAILING_SEPARATE",
        "IMPLICIT_BINARY",
    )

    for member in (
        model.SignPosition.LEADING_SEPARATE,
        model.SignPosition.TRAILING_SEPARATE,
    ):
        # Priced, not merely enumerated. The width is the INCLUDED width plus the one
        # byte the separate sign character occupies; asserted as that relationship in
        # Section 5 rather than as a literal here.
        assert isinstance(
            cobol_usage.byte_length(
                model.Usage.DISPLAY,
                digits=LEADING_SIGN_DIGITS,
                scale=LEADING_SIGN_SCALE,
                sign_position=member,
            ),
            int,
        )


def test_no_in_scope_field_declares_a_separate_sign() -> None:
    """Every dictionary entry scanned: zero SEPARATE signs, four leading, two trailing.

    Measured over all of data_dictionary/acas_posting_dictionary.json. The four
    LEADING_INCLUDED fields are the two amount fields of each of the two IRS posting
    records; the two TRAILING_INCLUDED fields are the General Ledger posting record's
    amounts [copybooks/wspost.cob:L23], [copybooks/wspost.cob:L28]. Both sets are
    asserted by exact key, so a fifth leading-sign field appearing anywhere - or one of
    these four losing its clause - fails here rather than in a scenario diff.
    """
    leading_separate: list[str] = []
    trailing_separate: list[str] = []
    leading_included: list[str] = []
    trailing_included: list[str] = []

    for entry in loader.entries():
        copybook = entry.copybook
        if copybook is None:
            # Bridge-only or column-only entries have no copybook declaration to carry a
            # sign clause - the three derived IRS date components are the notable case
            # [common/irspostingMT.cbl:L982-L987].
            continue
        position = copybook.sign_position
        if position is model.SignPosition.LEADING_SEPARATE:
            leading_separate.append(entry.key)
        elif position is model.SignPosition.TRAILING_SEPARATE:
            trailing_separate.append(entry.key)
        elif position is model.SignPosition.LEADING_INCLUDED:
            leading_included.append(entry.key)
        elif position is model.SignPosition.TRAILING_INCLUDED:
            trailing_included.append(entry.key)

    assert leading_separate == []
    assert trailing_separate == []

    assert sorted(leading_included) == sorted(
        key for key, _clause, _locator in LEADING_SIGN_FIELDS
    )
    assert sorted(trailing_included) == sorted(
        (GL_POST_AMOUNT_KEY, GL_VAT_AMOUNT_KEY)
    )


def test_the_only_sign_clause_texts_in_the_dictionary_are_the_two_spellings() -> None:
    """Two spellings, two fields each - and no third spelling anywhere.

    Measured over every entry: `sign leading` appears on
    [copybooks/wspost-irs.cob:L21] and [copybooks/wspost-irs.cob:L25]; `sign is leading`
    on [copybooks/irswspost.cob:L14] and [copybooks/irswspost.cob:L18]. Every recorded
    clause text is a member of `usage.SIGN_LEADING_SPELLINGS`, so no `sign trailing`, no
    `separate` and no re-spelling has crept into the generated dictionary.

    The frozen tree carries two further `sign leading` declarations, at
    [copybooks/fdpost-irs.cob:L20] and [copybooks/fdpost-irs.cob:L24]. That is the
    file-description twin of the transfer record and sits outside the in-scope copybook
    closure, which is why the dictionary records two of each spelling rather than four
    and two.
    """
    counted: dict[str, int] = {}
    for entry in loader.entries():
        copybook = entry.copybook
        if copybook is None or copybook.sign_clause_text is None:
            continue
        counted[copybook.sign_clause_text] = (
            counted.get(copybook.sign_clause_text, 0) + 1
        )

    assert counted == {"sign leading": 2, "sign is leading": 2}
    assert set(counted) <= set(cobol_usage.SIGN_LEADING_SPELLINGS)
